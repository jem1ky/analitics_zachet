from dataclasses import dataclass, field
from datetime import date


@dataclass(slots=True)
class AnalysisFilters:
    start_date: date | None = None
    end_date: date | None = None
    regions: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    products: list[str] = field(default_factory=list)

