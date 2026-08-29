"""Integration test proving Backend 2 works with Backend 1's *real*
AnalysisResult, not just the fake double used in the other unit tests.

Skipped automatically if Backend 1's `compiler` package isn't importable
(e.g. before the two branches are merged into the same src/ tree) --
nothing here should block Backend 2's own test suite from passing
independently.
"""

import pytest

from hashing.models import HashAnalysisReport
from hashing.pipeline import HashAnalysisPipeline

compiler_pipeline = pytest.importorskip("compiler.pipeline")


SAMPLE_C_SOURCE = """
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


def test_backend2_consumes_real_backend1_analysis_result():
    analysis = compiler_pipeline.CompilerPipeline().run(SAMPLE_C_SOURCE)

    report = HashAnalysisPipeline().run(analysis)

    assert isinstance(report, HashAnalysisReport)
    assert len(report.per_function) == 5
    assert report.recommended_function
    assert report.workload_summary["total_identifiers"] == (
        analysis.workload_metrics.total_identifiers
    )
