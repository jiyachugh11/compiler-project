"""Adapter: the single place that knows the *shape* of Backend 1's symbol data.

The core Backend 2 contract (interfaces.py) needs only identifier_stream,
interned_identifiers and workload_metrics. The hash-table-backed symbol-table
benchmark additionally needs the ORDERED declaration/reference events and the
scope parent links. Those are read here, duck-typed, and converted into
neutral types owned by Backend 2. If Backend 1 renames anything, only this
file changes.

Attributes read from Backend 1's AnalysisResult:
    analysis.symbol_table.symbols   ordered list; each item has
                                    .name, .scope_id, .role (enum, .name is
                                    "DECLARATION" or "REFERENCE")
    analysis.scopes                 {scope_id: scope}, scope has .parent_id

If any of that is missing, ``extract_symbol_events`` returns None and the
symbol-table benchmark is simply skipped.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class SymbolEvent:
    name: str
    scope_id: int
    is_declaration: bool


def extract_symbol_events(
    analysis: Any,
) -> Optional[Tuple[List[SymbolEvent], Dict[int, Optional[int]]]]:
    """Return (ordered events, {scope_id: parent_id}) or None if unavailable."""
    table = getattr(analysis, "symbol_table", None)
    scopes = getattr(analysis, "scopes", None)
    symbols = getattr(table, "symbols", None)
    if symbols is None or not scopes:
        return None

    try:
        parents = {int(sid): getattr(sc, "parent_id", None) for sid, sc in scopes.items()}
        events = [
            SymbolEvent(
                name=s.name,
                scope_id=int(s.scope_id),
                is_declaration=getattr(getattr(s, "role", None), "name", "") == "DECLARATION",
            )
            for s in symbols
        ]
    except (AttributeError, TypeError, ValueError):
        return None
    return events, parents
