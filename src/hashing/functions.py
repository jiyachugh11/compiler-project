"""String hash function implementations.

Each function has the signature (str) -> int and returns a non-negative
integer hash. All are deterministic and independent of Python's built-in
`hash()` (which is salted per-process for security and would make results
non-reproducible across runs).
"""

import zlib
from typing import Callable, Dict


def djb2(s: str) -> int:
    """Bernstein's DJB2 hash: h = h*33 + c, seeded at 5381."""
    h = 5381
    for ch in s:
        h = ((h * 33) + ord(ch)) & 0xFFFFFFFF
    return h


def fnv1a(s: str) -> int:
    """FNV-1a 32-bit hash: XOR byte in, then multiply by the FNV prime."""
    fnv_prime = 0x01000193
    h = 0x811C9DC5  # FNV offset basis
    for byte in s.encode("utf-8"):
        h ^= byte
        h = (h * fnv_prime) & 0xFFFFFFFF
    return h


def sdbm(s: str) -> int:
    """SDBM hash: h = c + (h << 6) + (h << 16) - h."""
    h = 0
    for ch in s:
        h = (ord(ch) + (h << 6) + (h << 16) - h) & 0xFFFFFFFF
    return h


def jenkins_one_at_a_time(s: str) -> int:
    """Jenkins' one-at-a-time hash."""
    h = 0
    for byte in s.encode("utf-8"):
        h = (h + byte) & 0xFFFFFFFF
        h = (h + (h << 10)) & 0xFFFFFFFF
        h ^= (h >> 6)
    h = (h + (h << 3)) & 0xFFFFFFFF
    h ^= (h >> 11)
    h = (h + (h << 15)) & 0xFFFFFFFF
    return h & 0xFFFFFFFF


def crc32_hash(s: str) -> int:
    """CRC32 checksum used as a hash function (stdlib zlib, no extra deps).

    Included as the "one additional reasonable hash function": it's a real,
    widely used algorithm (not a toy), gives a useful contrast point since
    it's designed for error-detection rather than hash-table distribution,
    and needs no third-party dependency.
    """
    return zlib.crc32(s.encode("utf-8")) & 0xFFFFFFFF


# Registry used by the benchmark suite to iterate over all functions by name.
HASH_FUNCTIONS: Dict[str, Callable[[str], int]] = {
    "DJB2": djb2,
    "FNV-1a": fnv1a,
    "SDBM": sdbm,
    "Jenkins (one-at-a-time)": jenkins_one_at_a_time,
    "CRC32": crc32_hash,
}
