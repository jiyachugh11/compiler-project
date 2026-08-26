"""Unit tests for the StringPool interning module."""

import pytest
from compiler.interning.string_pool import StringPool


@pytest.fixture
def pool() -> StringPool:
    """Fixture providing a fresh StringPool instance."""
    return StringPool()


def test_first_id_assignment(pool: StringPool) -> None:
    """Test that the first interned identifier receives ID 0."""
    id_count = pool.intern("count")
    assert id_count == 0
    assert pool.size() == 1
    assert len(pool) == 1


def test_sequential_ids(pool: StringPool) -> None:
    """Test that newly interned unique identifiers receive sequential 0-indexed IDs."""
    id0 = pool.intern("count")
    id1 = pool.intern("main")
    id2 = pool.intern("x")
    id3 = pool.intern("total")

    assert id0 == 0
    assert id1 == 1
    assert id2 == 2
    assert id3 == 3
    assert pool.size() == 4


def test_duplicate_interning_returns_same_id(pool: StringPool) -> None:
    """Test the example sequence:
    "count" -> 0
    "main"  -> 1
    "count" -> 0
    "x"     -> 2
    "main"  -> 1
    """
    id_count1 = pool.intern("count")
    id_main1 = pool.intern("main")
    id_count2 = pool.intern("count")
    id_x = pool.intern("x")
    id_main2 = pool.intern("main")

    assert id_count1 == 0
    assert id_main1 == 1
    assert id_count2 == 0
    assert id_x == 2
    assert id_main2 == 1
    assert pool.size() == 3


def test_different_strings_receive_different_ids(pool: StringPool) -> None:
    """Test that distinct strings always receive distinct IDs."""
    identifiers = ["alpha", "beta", "gamma", "delta", "epsilon"]
    ids = [pool.intern(ident) for ident in identifiers]

    assert len(ids) == len(set(ids))
    assert ids == list(range(len(identifiers)))


def test_string_to_id_lookup(pool: StringPool) -> None:
    """Test forward lookup from string to ID using get_id()."""
    pool.intern("foo")
    pool.intern("bar")

    assert pool.get_id("foo") == 0
    assert pool.get_id("bar") == 1
    assert pool.get_id("baz") is None


def test_id_to_string_lookup(pool: StringPool) -> None:
    """Test reverse lookup from ID to string using get_string()."""
    pool.intern("foo")
    pool.intern("bar")

    assert pool.get_string(0) == "foo"
    assert pool.get_string(1) == "bar"


def test_contains(pool: StringPool) -> None:
    """Test contains() and the Python `in` operator."""
    assert pool.contains("var") is False
    assert ("var" in pool) is False

    pool.intern("var")

    assert pool.contains("var") is True
    assert ("var" in pool) is True
    assert pool.contains("other") is False
    assert ("other" in pool) is False


def test_size_and_len(pool: StringPool) -> None:
    """Test size() and len() accurately track unique interned strings."""
    assert pool.size() == 0
    assert len(pool) == 0

    pool.intern("a")
    assert pool.size() == 1
    assert len(pool) == 1

    pool.intern("b")
    assert pool.size() == 2
    assert len(pool) == 2

    # Duplicate does not increase size
    pool.intern("a")
    assert pool.size() == 2
    assert len(pool) == 2


def test_empty_string_behavior(pool: StringPool) -> None:
    """Test that empty string is a valid internable string."""
    empty_id = pool.intern("")
    assert empty_id == 0
    assert pool.size() == 1
    assert pool.contains("") is True
    assert "" in pool
    assert pool.get_id("") == 0
    assert pool.get_string(0) == ""

    # Subsequent interning returns same ID
    assert pool.intern("") == 0

    # Other strings get next ID
    assert pool.intern("non_empty") == 1


def test_invalid_and_missing_lookups(pool: StringPool) -> None:
    """Test edge cases with out-of-bounds, negative, or nonexistent IDs."""
    pool.intern("first")
    pool.intern("second")

    # get_id for missing string
    assert pool.get_id("unknown") is None

    # get_string for negative or out-of-bounds IDs
    assert pool.get_string(-1) is None
    assert pool.get_string(2) is None
    assert pool.get_string(100) is None


def test_reverse_mapping_consistency(pool: StringPool) -> None:
    """Test that get_mapping() and get_all_strings() preserve exact 1-to-1 consistency."""
    words = ["int", "count", "while", "return", "status_flag"]
    for w in words:
        pool.intern(w)

    mapping = pool.get_mapping()
    all_strings = pool.get_all_strings()

    assert len(mapping) == len(words)
    assert len(all_strings) == len(words)
    assert all_strings == words

    for idx, word in enumerate(words):
        assert mapping[word] == idx
        assert pool.get_string(idx) == word
        assert pool.get_id(word) == idx


def test_clear_pool(pool: StringPool) -> None:
    """Test clearing the string pool resets state."""
    pool.intern("x")
    pool.intern("y")
    assert pool.size() == 2

    pool.clear()
    assert pool.size() == 0
    assert len(pool) == 0
    assert pool.get_id("x") is None
    assert pool.get_string(0) is None

    # Re-interning starts from 0 again
    assert pool.intern("z") == 0
