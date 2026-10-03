from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SourceRow:
    organisation_name: str
    town_city: str
    county: str
    type_and_rating: str
    route: str


@dataclass
class ValidationReport:
    accepted: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)
    raw_row_count: int = 0

    def add_error(self, message: str) -> None:
        self.errors.append(message)
        self.accepted = False
