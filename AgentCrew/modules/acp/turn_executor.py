from __future__ import annotations

from typing import TYPE_CHECKING, Any


from AgentCrew.modules.acp.session_state import AcpSessionState
from AgentCrew.modules.acp.tools.permission_broker import AcpPermissionBroker
from AgentCrew.modules.agents.base import MessageType
from AgentCrew.modules.tools.parallel_executor import (
    execute_tools_in_parallel,
    is_sequential_tool,
)

if TYPE_CHECKING:
    from AgentCrew.modules.acp.client_communication import ClientCommunication
    from AgentCrew.modules.acp.tool_manager import AcpToolManager
    from AgentCrew.modules.agents import LocalAgent
    from acp import Client


class TurnExecutor:
    def __init__(
        self,
        client_comm: ClientCommunication,
        tool_manager: AcpToolManager,
    ):
        self._client_comm = client_comm
        self._tool_manager = tool_manager

    async def run_turn(self, session_id: str, state: AcpSessionState, conn: Any):
        if state.permission_broker is None and conn is not None:
            state.permission_broker = AcpPermissionBroker(
                conn=conn,
                session_id=session_id,
            )
        await self._tool_manager.ensure_tools_for_session(session_id, state)
        agent = self._get_agent(state.agent_name)
        current_response = ""
        thinking_content = ""
        thinking_signature = ""
        tool_uses: list[dict[str, Any]] = []
        token_usage = None

        def process_result(_tool_uses, _token_usage):
            nonlocal tool_uses, token_usage
            tool_uses = _tool_uses
            token_usage = _token_usage

        async for (
            response_message,
            chunk_text,
            thinking_chunk,
        ) in agent.process_messages(
            state.history,
            callback=process_result,
        ):
            if state.cancelled:
                return
            if response_message:
                current_response = response_message
            if chunk_text:
                await self._client_comm.send_agent_message(session_id, chunk_text)
            if thinking_chunk:
                think_text_chunk, signature = thinking_chunk
                if think_text_chunk:
                    thinking_content += think_text_chunk
                    await self._client_comm.send_thought_chunk(
                        session_id, think_text_chunk
                    )
                if signature:
                    thinking_signature += signature

        thinking_data = (
            (thinking_content, thinking_signature) if thinking_content else None
        )
        thinking_message = agent.format_message(
            MessageType.Thinking,
            {"thinking": thinking_data},
        )
        if thinking_message:
            state.history.append(thinking_message)

        assistant_message = agent.format_message(
            MessageType.Assistant,
            {"message": current_response, "tool_uses": tool_uses},
        )
        if assistant_message:
            state.history.append(assistant_message)

        if tool_uses:
            await self.execute_tools(session_id, state, agent, tool_uses)
            if not state.cancelled:
                await self.run_turn(session_id, state, conn)

    async def execute_tools(
        self,
        session_id: str,
        state: AcpSessionState,
        agent: LocalAgent,
        tool_uses: list[dict[str, Any]],
    ):
        parallel_buffer: list[dict[str, Any]] = []

        async def flush_parallel():
            nonlocal parallel_buffer
            if not parallel_buffer:
                return
            for tool_use in parallel_buffer:
                await self._client_comm.send_tool_started(session_id, tool_use)
            results = await execute_tools_in_parallel(
                parallel_buffer, agent.execute_tool_call
            )
            for result in results:
                await self.append_tool_result(
                    session_id,
                    state,
                    agent,
                    result.tool_use,
                    result.result,
                    result.is_error,
                )
            parallel_buffer = []

        for tool_use in tool_uses:
            if state.cancelled:
                return
            if is_sequential_tool(tool_use["name"]):
                await flush_parallel()
                await self._client_comm.send_tool_started(session_id, tool_use)
                if state.permission_broker:
                    permission_outcome = (
                        await state.permission_broker.request_permission(tool_use)
                    )
                    if permission_outcome == "reject":
                        await self.append_tool_result(
                            session_id,
                            state,
                            agent,
                            tool_use,
                            "Tool execution rejected by user.",
                            is_error=True,
                            is_rejected=True,
                        )
                        continue
                try:
                    tool_result = await agent.execute_tool_call(
                        tool_use["name"],
                        tool_use.get("input", {}),
                    )
                    await self.append_tool_result(
                        session_id, state, agent, tool_use, tool_result
                    )
                except Exception as e:
                    await self.append_tool_result(
                        session_id, state, agent, tool_use, str(e), True
                    )
            else:
                permission_result = "allow_once"
                if state.permission_broker:
                    permission_result = (
                        await state.permission_broker.request_permission(tool_use)
                    )
                if permission_result == "reject":
                    await self.append_tool_result(
                        session_id,
                        state,
                        agent,
                        tool_use,
                        "Tool execution rejected by user.",
                        is_error=True,
                        is_rejected=True,
                    )
                else:
                    parallel_buffer.append(tool_use)

        await flush_parallel()

    async def append_tool_result(
        self,
        session_id: str,
        state: AcpSessionState,
        agent: LocalAgent,
        tool_use: dict[str, Any],
        tool_result: Any,
        is_error: bool = False,
        is_rejected: bool = False,
    ):
        result_message = agent.format_message(
            MessageType.ToolResult,
            {
                "tool_use": tool_use,
                "tool_result": tool_result,
                "is_error": is_error,
                "is_rejected": is_rejected,
            },
        )
        if result_message:
            state.history.append(result_message)
        await self._client_comm.send_tool_completed(
            session_id, tool_use, tool_result, is_error
        )

    async def release_active_terminals(
        self, session_id: str, state: AcpSessionState, conn: Client
    ):
        from AgentCrew.modules.acp.tools.terminal import (
            _kill_terminal,
            _release_terminal,
        )
        from .tools.context import AcpSessionContext

        for terminal_id in list(state.tool_state.acp_active_terminals.values()):
            ctx = AcpSessionContext(
                conn=conn,
                session_id=session_id,
                client_capabilities=self._tool_manager.client_capabilities,
                active_terminals=state.tool_state.acp_active_terminals,
            )
            await _release_terminal(ctx, terminal_id)
            await _kill_terminal(ctx, terminal_id)
        state.tool_state.acp_active_terminals.clear()

    def _get_agent(self, agent_name: str) -> Any:
        from AgentCrew.modules.agents import AgentManager

        agent_manager = AgentManager.get_instance()
        agent = agent_manager.get_local_agent(agent_name)
        if agent is None:
            raise ValueError(f"Agent '{agent_name}' not found")
        return agent
