"""Tests for hashing.functions (all 11 hash functions)."""

import random
import string
import zlib

import pytest

from hashing.functions import (
    HASH_FUNCTIONS, HASH_INFO, adler32_hash, crc32_hash, djb2, fnv1, fnv1a,
    jenkins_one_at_a_time, linux_dcache_hash, lose_lose, murmur3_32, sdbm, xxhash32,
)

ALL = list(HASH_FUNCTIONS.items())


@pytest.mark.parametrize("name,fn", ALL)
def test_deterministic_nonnegative_32bit(name, fn):
    h = fn("hello_world")
    assert h == fn("hello_world")
    assert isinstance(h, int) and 0 <= h <= 0xFFFFFFFF


@pytest.mark.parametrize("name,fn", ALL)
def test_empty_string_does_not_raise(name, fn):
    assert isinstance(fn(""), int)


WEAK = {"Lose-lose (baseline)", "Adler-32"}   # known to collide heavily on similar short strings


@pytest.mark.parametrize("name,fn", [(n, f) for n, f in ALL if n not in WEAK])
def test_not_degenerate(name, fn):
    assert len({fn(f"identifier_{i}") for i in range(300)}) > 285


def test_known_weak_functions_do_collide_on_similar_identifiers():
    keys = [f"identifier_{i}" for i in range(300)]
    distinct = lambda fn: len({fn(k) for k in keys})   # noqa: E731
    assert distinct(adler32_hash) < 250
    assert distinct(lose_lose) < 100
    assert distinct(murmur3_32) == 300


def test_registry_has_eleven_functions_and_info_for_each():
    assert len(HASH_FUNCTIONS) == 11
    assert set(HASH_INFO) == set(HASH_FUNCTIONS)
    assert list(HASH_FUNCTIONS)[:5] == ["DJB2", "FNV-1a", "SDBM", "Jenkins (one-at-a-time)", "CRC32"]


def test_known_vectors():
    assert djb2("") == 5381
    assert murmur3_32("test") == 0xBA6BD213
    assert xxhash32("") == 0x02CC5D05
    assert fnv1a("") == 0x811C9DC5 and fnv1("") == 0x811C9DC5
    assert fnv1a("a") == 0xE40C292C          # published FNV-1a 32-bit test vector
    assert crc32_hash("123456789") == 0xCBF43926   # CRC-32 check value


def _random_strings(n_lengths=70, per=15, seed=11):
    rng = random.Random(seed)
    for n in range(n_lengths):
        for _ in range(per):
            yield "".join(rng.choice(string.printable) for _ in range(n))


def test_crc32_and_adler32_match_zlib():
    for s in _random_strings():
        b = s.encode()
        assert crc32_hash(s) == zlib.crc32(b)
        assert adler32_hash(s) == zlib.adler32(b)


def test_murmur_and_xxhash_match_reference_libraries_if_installed():
    mmh3 = pytest.importorskip("mmh3")
    xxhash = pytest.importorskip("xxhash")
    for s in _random_strings():
        b = s.encode()
        assert murmur3_32(s) == mmh3.hash(b, 0, signed=False)
        assert xxhash32(s) == xxhash.xxh32_intdigest(b)


def test_lose_lose_is_anagram_blind():
    assert lose_lose("listen") == lose_lose("silent")
    assert murmur3_32("listen") != murmur3_32("silent")


def test_linux_dcache_formula():
    h = 0
    for c in b"ab":
        h = ((h + (c << 4) + (c >> 4)) * 11) & 0xFFFFFFFF
    assert linux_dcache_hash("ab") == (h * 0x9E3779B1) & 0xFFFFFFFF
