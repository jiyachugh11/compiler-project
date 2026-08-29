"""Tests for hashing.hash_table.HashTable."""

import pytest

from hashing.hash_table import HashTable


def constant_hash(_key: str) -> int:
    """Forces every key into bucket 0 -- used to test collision counting."""
    return 0


def identity_like_hash(key: str) -> int:
    return sum(ord(c) for c in key)


def test_insert_and_lookup():
    table = HashTable(bucket_count=8, hash_fn=identity_like_hash)
    table.insert("foo", 1)
    table.insert("bar", 2)
    assert table.lookup("foo") == 1
    assert table.lookup("bar") == 2
    assert table.lookup("missing") is None


def test_contains():
    table = HashTable(bucket_count=8, hash_fn=identity_like_hash)
    table.insert("foo", 1)
    assert table.contains("foo") is True
    assert table.contains("baz") is False


def test_update_existing_key_does_not_increase_size_or_count_collision():
    table = HashTable(bucket_count=8, hash_fn=identity_like_hash)
    table.insert("foo", 1)
    table.insert("foo", 2)  # update, not a new key
    assert table.size == 1
    assert table.collisions == 0
    assert table.lookup("foo") == 2


def test_collision_counting_with_forced_collisions():
    table = HashTable(bucket_count=4, hash_fn=constant_hash)
    table.insert("a")
    table.insert("b")
    table.insert("c")
    # first insert: empty bucket, no collision. next two: bucket occupied.
    assert table.collisions == 2
    assert table.size == 3
    assert table.max_chain_length() == 3


def test_load_factor():
    table = HashTable(bucket_count=10, hash_fn=identity_like_hash)
    for i in range(5):
        table.insert(f"id{i}", i)
    assert table.load_factor() == pytest.approx(0.5)


def test_bucket_distribution_length_matches_bucket_count():
    table = HashTable(bucket_count=16, hash_fn=identity_like_hash)
    for i in range(10):
        table.insert(f"id{i}", i)
    dist = table.bucket_distribution()
    assert len(dist) == 16
    assert sum(dist) == 10


def test_non_empty_buckets():
    table = HashTable(bucket_count=4, hash_fn=constant_hash)
    table.insert("a")
    table.insert("b")
    assert table.non_empty_buckets() == 1  # everything hashed to bucket 0


def test_invalid_bucket_count_raises():
    with pytest.raises(ValueError):
        HashTable(bucket_count=0, hash_fn=identity_like_hash)


def test_estimated_memory_bytes_is_positive_and_grows_with_size():
    small = HashTable(bucket_count=8, hash_fn=identity_like_hash)
    small.insert("a", 1)

    large = HashTable(bucket_count=8, hash_fn=identity_like_hash)
    for i in range(50):
        large.insert(f"identifier_{i}", i)

    assert small.estimated_memory_bytes() > 0
    assert large.estimated_memory_bytes() > small.estimated_memory_bytes()
