"""Agent tool contract: turn one hit into citable evidence items for the investigator agent.

``evidence(hit, entries)`` returns a list of ``EvidenceItem`` (id, kind, text, refs). The harness
(TRA-45) redacts names and account numbers before anything reaches the model, and quotes memos as
data, never as instructions. Never call an LLM from here.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EvidenceItem:
    id: str  # e.g. "E1"; the agent cites these
    kind: str  # "rule" | "transactions" | "baseline" | "reference" | "history"
    text: str  # plain sentence, numbers included, no names
    refs: list[str] = field(default_factory=list)  # entry_ids or reference-table keys


def evidence(hit: dict, entries) -> list[EvidenceItem]:
    raise NotImplementedError("example only")
