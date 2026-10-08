"""Tests for hashing.metrics."""

import math

import pytest

from hashing.functions import djb2, lose_lose, xxhash32
from hashing.metrics import (
    avalanche, avalanche_samples, distribution_stats, weighted_average_probes,
)


def test_perfectly_uniform_distribution():
    d = distribution_stats([1] * 10)
    assert d.empty_bucket_ratio == 0 and d.stddev_chain_length == 0
    assert d.colliding_pairs == 0 and d.chi_square_normalized == 0


def test_everything_in_one_bucket_is_flagged():
    d = distribution_stats([10] + [0] * 9)
    assert d.colliding_pairs == 45
    assert d.empty_bucket_ratio == pytest.approx(0.9)
    assert d.collision_ratio_vs_ideal > 5
    assert d.chi_square_normalized > 5


def test_expected_empty_ratio_matches_poisson():
    d = distribution_stats([1, 1, 0, 0])      # alpha = 0.5
    assert d.expected_empty_bucket_ratio == pytest.approx(math.exp(-0.5))


def test_empty_input_is_safe():
    assert distribution_stats([]).colliding_pairs == 0


def test_weighted_probes_uses_frequency():
    probes = {"hot": 1, "cold": 3}
    assert weighted_average_probes(probes, {"hot": 9, "cold": 1}) == pytest.approx(1.2)
    assert weighted_average_probes(probes, {}) == 0.0


def test_avalanche_samples_topped_up_deterministically():
    a = avalanche_samples(["x", "y"])
    assert len(a) >= 64 and a[:2] == ["x", "y"]
    assert a == avalanche_samples(["x", "y"])


def test_avalanche_separates_good_from_bad():
    s = avalanche_samples(["count", "total", "index"])
    good, bad = avalanche(xxhash32, s), avalanche(lose_lose, s)
    assert good.quality > 0.9 and abs(good.mean_flip_probability - 0.5) < 0.05
    assert bad.quality < 0.3
    assert avalanche(djb2, s).quality < good.quality


def test_avalanche_empty():
    assert avalanche(djb2, []).trials == 0
