from __future__ import annotations

import asyncio
from typing import Any, TYPE_CHECKING

from loguru import logger

from AgentCrew.modules.acp.mcp import normalize_acp_mcp_servers
from AgentCrew.modules.acp.session_state import AcpSessionState
from AgentCrew.modules.mcpclient import MCPSessionManager

if TYPE_CHECKING:
    from AgentCrew.modules.mcpclient import MCPService

ACP_MCP_STARTUP_TIMEOUT_SECONDS = 8.0
ACP_MCP_STARTUP_POLL_SECONDS = 0.1


class McpOrchestrator:
    def __init__(self, agent_manager: Any):
        self._agent_manager = agent_manager

    async def setup_session_mcp_servers(
        self,
        session_id: str,
        state: AcpSessionState,
        mcp_servers: list[Any] | None,
    ):
        configs = normalize_acp_mcp_servers(session_id, state.agent_name, mcp_servers)
        if not configs:
            return
        await self.cleanup_session_mcp_servers(state, clear_configs=True)
        state.acp_mcp_server_configs = configs
        await self.start_session_mcp_configs(state)

    async def start_session_mcp_configs(self, state: AcpSessionState):
        mcp_manager = MCPSessionManager.get_instance()
        if not mcp_manager.initialized:
            mcp_manager.initialize()

        service = mcp_manager.mcp_service
        active_configs: list[Any] = []
        active_ids: list[str] = []
        for config in list(state.acp_mcp_server_configs):
            combined_id = service._get_server_id_format(config.name, state.agent_name)
            try:
                service._run_async(
                    service.start_server_connection_management(config, state.agent_name)
                )
                ready = await self.wait_for_mcp_server_ready(
                    service, combined_id, state.agent_name
                )
            except Exception:
                logger.exception(
                    f"ACP MCP server '{config.name}' failed during startup"
                )
                ready = False

            if ready:
                active_configs.append(config)
                active_ids.append(combined_id)
                continue

            logger.warning(
                f"ACP MCP server '{config.name}' did not become ready; continuing without it"
            )
            await self.cleanup_single_mcp_server(
                service, config.name, state.agent_name, combined_id
            )

        state.acp_mcp_server_configs = active_configs
        state.acp_mcp_server_ids = active_ids

    async def wait_for_mcp_server_ready(
        self,
        service: MCPService,
        combined_id: str,
        agent_name: str,
        timeout_seconds: float = ACP_MCP_STARTUP_TIMEOUT_SECONDS,
    ) -> bool:
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout_seconds
        while loop.time() < deadline:
            agent = self._agent_manager.get_local_agent(agent_name)
            if agent:
                if combined_id not in agent.mcps_loading and (
                    service.connected_servers.get(combined_id)
                    or combined_id in service.tools_cache
                ):
                    return True
            elif (
                service.connected_servers.get(combined_id)
                or combined_id in service.tools_cache
            ):
                return True

            task = service._server_connection_tasks.get(combined_id)
            if task and task.done():
                if task.cancelled():
                    return False
                try:
                    exc = task.exception()
                except Exception:
                    return False
                if exc:
                    logger.warning(
                        f"ACP MCP server task failed for '{combined_id}': {exc}"
                    )
                    return False
                if agent:
                    return bool(
                        combined_id not in agent.mcps_loading
                        and (
                            service.connected_servers.get(combined_id)
                            or combined_id in service.tools_cache
                        )
                    )
                return bool(
                    service.connected_servers.get(combined_id)
                    or combined_id in service.tools_cache
                )

            await asyncio.sleep(ACP_MCP_STARTUP_POLL_SECONDS)

        return False

    async def cleanup_single_mcp_server(
        self, service: Any, server_name: str, agent_name: str, combined_id: str
    ):
        try:
            service._run_async(service.deregister_server_tools(server_name, agent_name))
        except Exception:
            logger.exception("Error deregistering failed ACP MCP server tools")

        try:
            service._run_async(service.shutdown_single_server_connection(combined_id))
        except Exception:
            logger.exception("Error stopping failed ACP MCP server")

    async def cleanup_session_mcp_servers(
        self, state: AcpSessionState, clear_configs: bool = False
    ):
        if not state.acp_mcp_server_ids and not state.acp_mcp_server_configs:
            return

        mcp_manager = MCPSessionManager.get_instance()
        service = mcp_manager.mcp_service
        for config in list(state.acp_mcp_server_configs):
            try:
                service._run_async(
                    service.deregister_server_tools(config.name, state.agent_name)
                )
            except Exception:
                logger.exception("Error deregistering ACP MCP server tools")

        for combined_id in list(state.acp_mcp_server_ids):
            try:
                service._run_async(
                    service.shutdown_single_server_connection(combined_id)
                )
            except Exception:
                logger.exception("Error shutting down ACP MCP server")

        state.acp_mcp_server_ids.clear()
        if clear_configs:
            state.acp_mcp_server_configs.clear()
