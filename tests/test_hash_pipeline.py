"""Tests for hashing.pipeline.HashAnalysisPipeline.

Uses doubles (not Backend 1's classes) to prove Backend 2 depends only on the
structural interface in hashing.interfaces.
"""

import json
from dataclasses import asdict, dataclass
from types import SimpleNamespace
from typing import Dict, List

from hashing.benchmark import BenchmarkRunner
from hashing.definitions import DEFINITIONS
from hashing.functions import HASH_FUNCTIONS
from hashing.models import HashAnalysisReport
from hashing.pipeline import HashAnalysisPipeline


@dataclass
class FakeWM:
    total_identifiers: int
    unique_identifiers: int
    average_identifier_length: float
    min_identifier_length: int
    max_identifier_length: int
    identifier_frequency: Dict[str, int]
    repetition_ratio: float
    uniqueness_ratio: float
    scope_count: int
    max_scope_depth: int
    identifiers_per_scope: Dict[int, int]


@dataclass
class FakeAnalysis:           # core contract only: no symbol_table / scopes / source_code
    identifier_stream: List[str]
    interned_identifiers: Dict[str, int]
    workload_metrics: FakeWM


def build(stream):
    unique = list(dict.fromkeys(stream))
    total = len(stream)
    wm = FakeWM(
        total_identifiers=total, unique_identifiers=len(unique),
        average_identifier_length=sum(map(len, stream)) / total if total else 0.0,
        min_identifier_length=min(map(len, stream), default=0),
        max_identifier_length=max(map(len, stream), default=0),
        identifier_frequency={u: stream.count(u) for u in unique},
        repetition_ratio=1 - len(unique) / total if total else 0.0,
        uniqueness_ratio=len(unique) / total if total else 0.0,
        scope_count=1, max_scope_depth=0, identifiers_per_scope={0: total})
    return FakeAnalysis(stream, {u: i for i, u in enumerate(unique)}, wm)


LIGHT_SECURITY = dict(bits=7, targets=6, structural_samples=3)


def quick():
    return HashAnalysisPipeline(benchmark_runner=BenchmarkRunner(repeats=1),
                                security_options=LIGHT_SECURITY)


STREAM = ["count", "i", "count", "total", "i", "count", "sum", "i"]


def test_core_contract_only_works_and_skips_symbol_table():
    report = quick().run(build(STREAM))
    assert isinstance(report, HashAnalysisReport)
    assert len(report.per_function) == len(HASH_FUNCTIONS) == 11
    assert report.recommended_function in HASH_FUNCTIONS
    assert report.recommendation_reason
    assert all(r.symbol_table is None for r in report.per_function)
    assert report.workload_summary["total_identifiers"] == len(STREAM)


def test_report_carries_security_ranking_definitions_confidence():
    report = quick().run(build(STREAM))
    assert all(r.security is not None for r in report.per_function)
    assert report.security_reference is not None
    assert report.security_reference.structural_second_preimages_found == 0
    assert [k.rank for k in report.ranking] == list(range(1, 12))
    assert abs(sum(report.weights.values()) - 1.0) < 1e-9
    assert report.definitions == DEFINITIONS and "full_hash_collision" in report.definitions
    assert report.confidence == "low"


def test_optional_stages_can_be_disabled():
    p = HashAnalysisPipeline(benchmark_runner=BenchmarkRunner(repeats=1),
                             include_security=False, include_symbol_table=False)
    report = p.run(build(STREAM))
    assert report.security_reference is None
    assert all(r.security is None for r in report.per_function)


def test_symbol_table_stage_runs_when_scope_data_present():
    analysis = build(STREAM)
    role = lambda n: SimpleNamespace(name=n)   # noqa: E731
    analysis.symbol_table = SimpleNamespace(symbols=[
        SimpleNamespace(name="count", scope_id=0, role=role("DECLARATION")),
        SimpleNamespace(name="i", scope_id=1, role=role("DECLARATION")),
        SimpleNamespace(name="count", scope_id=1, role=role("REFERENCE")),
    ])
    analysis.scopes = {0: SimpleNamespace(parent_id=None), 1: SimpleNamespace(parent_id=0)}
    report = quick().run(analysis)
    assert all(r.symbol_table and r.symbol_table.resolutions == 1 for r in report.per_function)
    assert "symtab_time" in report.weights


def test_empty_stream_is_safe():
    report = quick().run(build([]))
    assert len(report.per_function) == 11 and report.workload_summary["total_identifiers"] == 0


def test_report_is_json_serialisable():
    report = quick().run(build(STREAM * 5))
    text = json.dumps(asdict(report))
    back = json.loads(text)
    assert back["recommended_function"] == report.recommended_function
    assert len(back["per_function"]) == 11


def test_deterministic_metrics_across_runs():
    analysis = build(["a", "b", "a", "c", "b", "a"] * 10)
    r1, r2 = quick().run(analysis), quick().run(analysis)
    det = lambda r: {f.name: (f.collisions, f.full_hash_collisions, f.avalanche_quality) for f in r.per_function}  # noqa: E731
    assert det(r1) == det(r2)
