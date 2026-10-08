"""Tests for hashing.hash_table.HashTable."""

import pytest

from hashing.hash_table import HashTable


def constant_hash(_key):
    return 0


def sum_hash(key):
    return sum(ord(c) for c in key)


def test_insert_lookup_contains():
    t = HashTable(8, sum_hash)
    t.insert("foo", 1)
    t.insert("bar", 2)
    assert t.lookup("foo") == 1 and t.lookup("bar") == 2 and t.lookup("zzz") is None
    assert t.contains("foo") and not t.contains("baz")


def test_update_does_not_grow_or_count_collisions():
    t = HashTable(8, sum_hash)
    t.insert("foo", 1)
    t.insert("foo", 2)
    assert t.size == 1 and t.collisions == 0 and t.lookup("foo") == 2


def test_bucket_collisions_with_forced_collisions():
    t = HashTable(4, constant_hash)
    for k in "abc":
        t.insert(k)
    assert t.collisions == 2
    assert t.max_chain_length() == 3
    assert t.colliding_pairs() == 3          # C(3,2)


def test_full_hash_collision_vs_bucket_collision():
    """'ab' and 'ba' share the full digest; 'c' only shares the bucket."""
    h = {"ab": 10, "ba": 10, "c": 14}.__getitem__   # 14 mod 4 == 10 mod 4
    t = HashTable(4, h)
    for k in ("ab", "ba", "c"):
        t.insert(k)
    assert t.full_hash_collisions == 1       # ab/ba
    assert t.collisions == 2                 # ba and c both found an occupied bucket


def test_every_full_collision_is_a_bucket_collision():
    t = HashTable(16, lambda k: len(k))
    for k in ["aa", "bb", "cc", "ddd", "eee"]:
        t.insert(k)
    assert t.collisions >= t.full_hash_collisions


def test_probes_counts_chain_position():
    t = HashTable(4, constant_hash)
    for k in "abc":
        t.insert(k)
    assert [t.probes(k) for k in "abc"] == [1, 2, 3]
    assert t.probes("missing") is None
    assert t.chain_length_for("anything") == 3


def test_load_factor_and_distribution():
    t = HashTable(10, sum_hash)
    for i in range(5):
        t.insert(f"id{i}", i)
    assert t.load_factor() == pytest.approx(0.5)
    dist = t.bucket_distribution()
    assert len(dist) == 10 and sum(dist) == 5
    assert t.non_empty_buckets() == sum(1 for c in dist if c)


def test_invalid_bucket_count():
    with pytest.raises(ValueError):
        HashTable(0, sum_hash)


def test_memory_estimate_grows():
    small, large = HashTable(8, sum_hash), HashTable(8, sum_hash)
    small.insert("a", 1)
    for i in range(50):
        large.insert(f"identifier_{i}", i)
    assert 0 < small.estimated_memory_bytes() < large.estimated_memory_bytes()
