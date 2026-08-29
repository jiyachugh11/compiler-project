"""Tests for hashing.pipeline.HashAnalysisPipeline.

Uses a fake AnalysisResult double (not Backend 1's real class) to prove
Backend 2 only depends on the structural interface in hashing.interfaces,
per the "don't assume my internal classes are your interface" boundary.
"""

from dataclasses import dataclass, field
from typing import Dict, List

from hashing.functions import HASH_FUNCTIONS
from hashing.models import HashAnalysisReport
from hashing.pipeline import HashAnalysisPipeline


@dataclass
class FakeWorkloadMetrics:
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
class FakeAnalysisResult:
    identifier_stream: List[str]
    interned_identifiers: Dict[str, int]
    workload_metrics: FakeWorkloadMetrics
    # Deliberately no symbol_table / scopes / source_code -- Backend 2
    # must not require them.


def build_fake_analysis(stream):
    unique = list(dict.fromkeys(stream))
    freq = {ident: stream.count(ident) for ident in unique}
    total = len(stream)
    wm = FakeWorkloadMetrics(
        total_identifiers=total,
        unique_identifiers=len(unique),
        average_identifier_length=(
            sum(len(i) for i in stream) / total if total else 0.0
        ),
        min_identifier_length=min((len(i) for i in stream), default=0),
        max_identifier_length=max((len(i) for i in stream), default=0),
        identifier_frequency=freq,
        repetition_ratio=1 - (len(unique) / total) if total else 0.0,
        uniqueness_ratio=(len(unique) / total) if total else 0.0,
        scope_count=1,
        max_scope_depth=0,
        identifiers_per_scope={0: total},
    )
    return FakeAnalysisResult(
        identifier_stream=stream,
        interned_identifiers={name: i for i, name in enumerate(unique)},
        workload_metrics=wm,
    )


def test_pipeline_end_to_end_with_fake_analysis_result():
    stream = ["count", "i", "count", "total", "i", "count", "sum", "i"]
    analysis = build_fake_analysis(stream)

    pipeline = HashAnalysisPipeline()
    report = pipeline.run(analysis)

    assert isinstance(report, HashAnalysisReport)
    assert len(report.per_function) == len(HASH_FUNCTIONS)
    assert report.recommended_function in HASH_FUNCTIONS
    assert isinstance(report.recommendation_reason, str) and report.recommendation_reason
    assert report.workload_summary["total_identifiers"] == len(stream)
    assert report.workload_summary["unique_identifiers"] == len(set(stream))


def test_pipeline_handles_empty_identifier_stream():
    analysis = build_fake_analysis([])
    pipeline = HashAnalysisPipeline()
    report = pipeline.run(analysis)
    assert len(report.per_function) == len(HASH_FUNCTIONS)
    assert report.workload_summary["total_identifiers"] == 0


def test_pipeline_is_deterministic_across_runs():
    stream = ["a", "b", "a", "c", "b", "a"] * 10
    analysis = build_fake_analysis(stream)
    pipeline = HashAnalysisPipeline()

    report1 = pipeline.run(analysis)
    report2 = pipeline.run(analysis)

    collisions1 = {r.name: r.collisions for r in report1.per_function}
    collisions2 = {r.name: r.collisions for r in report2.per_function}
    assert collisions1 == collisions2
    assert report1.recommended_function == report2.recommended_function
