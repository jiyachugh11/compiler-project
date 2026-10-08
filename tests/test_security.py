"""Tests for hashing.security (preimage / second-preimage analysis)."""

from hashing.functions import djb2, linux_dcache_hash, lose_lose, murmur3_32
from hashing.security import (
    analyze, sha256_reference, structural_second_preimage,
)

IDS = ["count", "total", "buffer", "index", "node_ptr", "result", "temp", "ez"]


def test_djb2_has_constructive_second_preimage():
    y = structural_second_preimage(djb2, "count")
    assert y is not None and y != "count" and djb2(y) == djb2("count")


def test_djb2_pair_relation():
    # (c_i + 1, c_{i+1} - 33) preserves the hash because 33*(c+1) + (d-33) == 33*c + d
    assert djb2("ez") == djb2("fY")


def test_lose_lose_and_kernel_hash_are_structurally_weak():
    for fn in (lose_lose, linux_dcache_hash):
        y = structural_second_preimage(fn, "count")
        assert y is not None and fn(y) == fn("count") and y != "count"


def test_strong_hashes_have_no_cheap_second_preimage_in_bounded_search():
    for fn in (murmur3_32, sha256_reference):
        assert all(structural_second_preimage(fn, x) is None for x in IDS)


def test_analyze_result_shape_and_verdicts():
    weak = analyze(djb2, IDS, structural_samples=5)
    strong = analyze(sha256_reference, IDS, structural_samples=5)
    assert weak.structural_second_preimages_found == 5 and weak.structural_example
    assert "Structural weakness" in weak.verdict
    assert strong.structural_second_preimages_found == 0
    assert "not a security proof" in strong.verdict


def test_effort_ratio_is_near_one_for_random_like_function():
    r = analyze(sha256_reference, IDS, bits=8, targets=40, structural_samples=1)
    assert 0.5 < r.preimage_effort_ratio < 2.0
    assert 0.5 < r.second_preimage_effort_ratio < 2.0
    assert r.bits_tested == 8 and r.targets_tested == 40


def test_deterministic_for_same_seed():
    a = analyze(murmur3_32, IDS, bits=8, targets=10, structural_samples=2, seed=7)
    b = analyze(murmur3_32, IDS, bits=8, targets=10, structural_samples=2, seed=7)
    assert a == b


def test_works_on_tiny_or_empty_workload():
    assert analyze(murmur3_32, [], bits=6, targets=4, structural_samples=2).targets_tested == 4
