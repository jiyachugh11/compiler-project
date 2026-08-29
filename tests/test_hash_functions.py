"""Tests for hashing.functions."""

import pytest

from hashing.functions import (
    HASH_FUNCTIONS,
    crc32_hash,
    djb2,
    fnv1a,
    jenkins_one_at_a_time,
    sdbm,
)

ALL_FUNCTIONS = [djb2, fnv1a, sdbm, jenkins_one_at_a_time, crc32_hash]


@pytest.mark.parametrize("fn", ALL_FUNCTIONS)
def test_deterministic(fn):
    """Same input must always produce the same hash."""
    assert fn("hello_world") == fn("hello_world")


@pytest.mark.parametrize("fn", ALL_FUNCTIONS)
def test_returns_non_negative_int(fn):
    assert isinstance(fn("x"), int)
    assert fn("x") >= 0


@pytest.mark.parametrize("fn", ALL_FUNCTIONS)
def test_different_inputs_usually_differ(fn):
    """Not a proof of collision-freedom, just a sanity check that the
    function isn't degenerate (e.g. always returning 0)."""
    values = {fn(f"identifier_{i}") for i in range(200)}
    assert len(values) > 190


@pytest.mark.parametrize("fn", ALL_FUNCTIONS)
def test_empty_string(fn):
    """Must not raise on an empty string."""
    result = fn("")
    assert isinstance(result, int)


def test_registry_has_five_functions():
    assert len(HASH_FUNCTIONS) == 5
    assert set(HASH_FUNCTIONS.keys()) == {
        "DJB2", "FNV-1a", "SDBM", "Jenkins (one-at-a-time)", "CRC32",
    }


def test_djb2_known_value():
    # DJB2("") = 5381 (the seed, since the loop never runs)
    assert djb2("") == 5381


def test_registry_functions_are_callable_and_consistent():
    for name, fn in HASH_FUNCTIONS.items():
        h1 = fn("test_identifier")
        h2 = fn("test_identifier")
        assert h1 == h2, f"{name} is not deterministic"
