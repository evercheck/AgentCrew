from typing import Optional, Dict, Any


class PromptEvolutionSession:
    def __init__(self):
        self._proposal: Optional[Dict[str, Any]] = None

    def start(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        self._proposal = proposal
        return proposal

    def get(self) -> Optional[Dict[str, Any]]:
        return self._proposal

    def has_pending(self) -> bool:
        return self._proposal is not None

    def clear(self) -> None:
        self._proposal = None

    def get_effective_summary(self) -> str:
        proposal = self._require_pending("No pending evolution proposal available.")
        return (
            proposal.get("approved_summary")
            or proposal.get("generated_summary")
            or proposal.get("user_editable_summary", "")
        )

    def update_approved_summary(self, approved_summary: str) -> str:
        proposal = self._require_pending("No pending evolution proposal to edit.")
        normalized_summary = approved_summary.strip()
        if not normalized_summary:
            raise ValueError("Edited evolution summary cannot be empty.")

        proposal["approved_summary"] = normalized_summary
        proposal["user_editable_summary"] = normalized_summary
        return normalized_summary

    def _require_pending(self, error_message: str) -> Dict[str, Any]:
        if not self._proposal:
            raise ValueError(error_message)
        return self._proposal
