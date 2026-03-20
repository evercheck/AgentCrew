from __future__ import annotations

from a2a.types import (
    DataPart,
    Message,
    Part,
    Role,
    TextPart,
)


class TaskInteractionHandler:
    def __init__(self) -> None:
        pass

    def create_ask_message(self, question: str, guided_answers: list[str]) -> Message:
        ask_data = {
            "type": "ask",
            "question": question,
            "guided_answers": guided_answers,
            "instruction": "Please respond with one of the guided answers or provide a custom response.",
        }
        return Message(
            message_id=f"ask_{hash(question)}",
            role=Role.agent,
            parts=[
                Part(root=TextPart(text=f"❓ {question}")),
                Part(root=DataPart(data=ask_data)),
            ],
        )

    def cleanup(self, task_id: str) -> None:
        pass
