"""Backend 2 against Backend 1's REAL AnalysisResult.

Skipped automatically when Backend 1's `compiler` package is not importable
(e.g. before both branches share one src/ tree), so Backend 2's suite never
depends on it.
"""

import pytest

from hashing.benchmark import BenchmarkRunner
from hashing.models import HashAnalysisReport
from hashing.pipeline import HashAnalysisPipeline

compiler_pipeline = pytest.importorskip("compiler.pipeline")

SOURCE = """
int add(int a, int b) {
    int result = a + b;
    return result;
}

int main() {
    int x = 5;
    int y = 10;
    int total = add(x, y);
    for (int i = 0; i < total; i++) {
        int temp = i * 2;
    }
    return total;
}
"""


@pytest.fixture(scope="module")
def analysis():
    return compiler_pipeline.CompilerPipeline().run(SOURCE)


@pytest.fixture(scope="module")
def report(analysis):
    return HashAnalysisPipeline(benchmark_runner=BenchmarkRunner(repeats=1),
                                security_options=dict(bits=7, targets=6, structural_samples=3)).run(analysis)


def test_consumes_real_analysis_result(analysis, report):
    assert isinstance(report, HashAnalysisReport)
    assert len(report.per_function) == 11
    assert report.workload_summary["total_identifiers"] == analysis.workload_metrics.total_identifiers


def test_symbol_table_replay_matches_backend1_symbol_counts(analysis, report):
    symbols = analysis.symbol_table.symbols
    decls = sum(1 for s in symbols if s.role.name == "DECLARATION")
    refs = len(symbols) - decls
    for r in report.per_function:
        st = r.symbol_table
        assert st is not None
        assert st.declarations + st.redeclarations == decls
        assert st.resolutions == refs
        assert st.scopes == len(analysis.scopes)


def test_outcome_of_replay_does_not_depend_on_hash_function(report):
    outcomes = {(r.symbol_table.declarations, r.symbol_table.resolutions, r.symbol_table.unresolved)
                for r in report.per_function}
    assert len(outcomes) == 1


def test_probe_frequencies_come_from_real_workload(analysis, report):
    freq = analysis.workload_metrics.identifier_frequency
    assert sum(freq.values()) == analysis.workload_metrics.total_identifiers
    assert all(r.weighted_avg_probes >= 1.0 for r in report.per_function)
