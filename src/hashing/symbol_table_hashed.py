"""A scoped symbol table implemented ON TOP of the generic HashTable.

This is how a real compiler stores symbols: every lexical scope owns a hash
table keyed by identifier name, and scopes are linked to their parent. Name
resolution starts in the current scope and walks outward until a declaration
is found, which gives shadowing for free.

It exists so the hash functions can be judged on the job they are actually
for - declaring and resolving identifiers - rather than only on bulk
insert/lookup of a flat key list. It does NOT replace Backend 1's SymbolTable
(which is the analysis artefact); it is Backend 2's performance model of a
hash-based one, replayed from Backend 1's recorded events.
"""

import math
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from hashing.adapters import SymbolEvent
from hashing.hash_table import HashTable

GLOBAL_SCOPE = 0


class HashedSymbolTable:
    """Per-scope hash tables with parent links and outward name resolution."""

    def __init__(self, hash_fn: Callable[[str], int], default_buckets: int = 16) -> None:
        self.hash_fn = hash_fn
        self.default_buckets = default_buckets
        self._tables: Dict[int, HashTable] = {}
        self._parent: Dict[int, Optional[int]] = {}
        self._stack: List[int] = []
        self._next_id = 0
        self._new_scope(parent=None, buckets=default_buckets)  # global scope
        self._stack.append(GLOBAL_SCOPE)

    # ------------------------------------------------------------- scopes
    def _new_scope(self, parent: Optional[int], buckets: int, scope_id: Optional[int] = None) -> int:
        sid = self._next_id if scope_id is None else scope_id
        self._next_id = max(self._next_id, sid + 1)
        self._tables[sid] = HashTable(max(1, buckets), self.hash_fn)
        self._parent[sid] = parent
        return sid

    def enter_scope(self, buckets: Optional[int] = None) -> int:
        sid = self._new_scope(self._stack[-1], buckets or self.default_buckets)
        self._stack.append(sid)
        return sid

    def exit_scope(self) -> int:
        if len(self._stack) <= 1:
            raise ValueError("cannot exit the global scope")
        return self._stack.pop()

    def add_scope(self, scope_id: int, parent: Optional[int], buckets: int) -> None:
        """Create a scope with an explicit id (used when replaying a recorded program)."""
        self._new_scope(parent, buckets, scope_id=scope_id)

    @property
    def current_scope_id(self) -> int:
        return self._stack[-1]

    # --------------------------------------------------------- operations
    def declare(self, name: str, info: Any = True, scope_id: Optional[int] = None) -> bool:
        """Declare ``name`` in a scope. Returns False if it was already
        declared in that same scope (a redeclaration)."""
        sid = self.current_scope_id if scope_id is None else scope_id
        table = self._tables[sid]
        if table.contains(name):
            return False
        table.insert(name, info)
        return True

    def resolve(self, name: str, scope_id: Optional[int] = None) -> Tuple[Optional[Any], int, int]:
        """Resolve ``name`` from a scope outward.

        Returns (info or None, scopes_visited, key_comparisons).
        """
        sid: Optional[int] = self.current_scope_id if scope_id is None else scope_id
        hops = 0
        comparisons = 0
        while sid is not None:
            hops += 1
            table = self._tables[sid]
            found = table.probes(name)
            if found is not None:
                return table.lookup(name), hops, comparisons + found
            # a miss still costs a walk of the whole chain in that bucket
            comparisons += table.chain_length_for(name)
            sid = self._parent[sid]
        return None, hops, comparisons

    # ------------------------------------------------------------ reporting
    def tables(self) -> Dict[int, HashTable]:
        return self._tables

    def total_collisions(self) -> int:
        return sum(t.collisions for t in self._tables.values())

    def max_chain_length(self) -> int:
        return max(t.max_chain_length() for t in self._tables.values())


# ------------------------------------------------------------------ replay
@dataclass
class SymbolTableBenchResult:
    """Cost of running a recorded program's symbol traffic through a
    hash-based scoped symbol table using one hash function."""

    scopes: int
    declarations: int
    redeclarations: int
    resolutions: int
    unresolved: int            # references with no visible declaration (e.g. library calls)
    avg_scope_hops: float      # scopes visited per resolution
    avg_comparisons: float     # key comparisons per resolution
    bucket_collisions: int     # summed over every scope's table
    max_chain_length: int
    total_time_sec: float      # declare + resolve for the whole program (best of repeats)


def _scope_buckets(events: Sequence[SymbolEvent], scope_ids, target_load: float) -> Dict[int, int]:
    declared: Dict[int, int] = {sid: 0 for sid in scope_ids}
    for e in events:
        if e.is_declaration and e.scope_id in declared:
            declared[e.scope_id] += 1
    return {sid: max(8, math.ceil(n / target_load)) for sid, n in declared.items()}


def replay(
    hash_fn: Callable[[str], int],
    events: Sequence[SymbolEvent],
    parents: Dict[int, Optional[int]],
    target_load: float = 0.75,
    repeats: int = 3,
) -> SymbolTableBenchResult:
    """Replay recorded declare/resolve events, in source order, through a fresh
    HashedSymbolTable. Timing is the best of ``repeats`` runs (least noise)."""
    sizes = _scope_buckets(events, parents.keys(), target_load)

    def build() -> HashedSymbolTable:
        st = HashedSymbolTable(hash_fn)
        # recreate every recorded scope (ids are creation-ordered, parents first)
        for sid in sorted(parents):
            if sid == GLOBAL_SCOPE:
                st._tables[GLOBAL_SCOPE] = HashTable(sizes.get(GLOBAL_SCOPE, 8), hash_fn)
            else:
                st.add_scope(sid, parents[sid], sizes.get(sid, 8))
        return st

    best = math.inf
    stats = None
    for _ in range(max(1, repeats)):
        st = build()
        decl = redecl = res = unres = hops_total = cmp_total = 0
        start = time.perf_counter()
        for e in events:
            if e.scope_id not in parents:
                continue
            if e.is_declaration:
                if st.declare(e.name, scope_id=e.scope_id):
                    decl += 1
                else:
                    redecl += 1
            else:
                info, hops, cmps = st.resolve(e.name, scope_id=e.scope_id)
                res += 1
                hops_total += hops
                cmp_total += cmps
                if info is None:
                    unres += 1
        elapsed = time.perf_counter() - start
        if elapsed < best:
            best = elapsed
            stats = (st, decl, redecl, res, unres, hops_total, cmp_total)

    st, decl, redecl, res, unres, hops_total, cmp_total = stats
    return SymbolTableBenchResult(
        scopes=len(parents),
        declarations=decl,
        redeclarations=redecl,
        resolutions=res,
        unresolved=unres,
        avg_scope_hops=(hops_total / res) if res else 0.0,
        avg_comparisons=(cmp_total / res) if res else 0.0,
        bucket_collisions=st.total_collisions(),
        max_chain_length=st.max_chain_length(),
        total_time_sec=best,
    )
