"""String hash function implementations.

Every function has the signature (str) -> int and returns a non-negative
32-bit integer. All are deterministic and independent of Python's built-in
``hash()`` (which is salted per process and would make runs irreproducible).

Families included
-----------------
Classic string hashes   DJB2, SDBM, FNV-1, FNV-1a, Jenkins one-at-a-time
Modern non-crypto       MurmurHash3 (x86_32), xxHash32
Checksums               CRC32, Adler-32
Kernel                  Linux dcache name hash (partial_name_hash + golden-ratio finalizer)
Baseline (deliberately  "lose-lose" (sum of characters, K&R 1st edition)
poor)

Murmur3, xxHash32, CRC32 and Adler-32 are verified against independent
reference implementations in the test-suite. All are pure Python on purpose,
so timings compare algorithms on equal footing (no function gets a native-C
advantage).
"""

from typing import Callable, Dict, NamedTuple

_M32 = 0xFFFFFFFF


def _rotl32(x: int, r: int) -> int:
    return ((x << r) | (x >> (32 - r))) & _M32


# --------------------------------------------------------------------------
# Original five
# --------------------------------------------------------------------------
def djb2(s: str) -> int:
    """Bernstein's DJB2: h = h*33 + c, seeded at 5381."""
    h = 5381
    for ch in s:
        h = ((h * 33) + ord(ch)) & _M32
    return h


def fnv1a(s: str) -> int:
    """FNV-1a 32-bit: XOR the byte in, then multiply by the FNV prime."""
    h = 0x811C9DC5
    for byte in s.encode("utf-8"):
        h ^= byte
        h = (h * 0x01000193) & _M32
    return h


def sdbm(s: str) -> int:
    """SDBM: h = c + (h << 6) + (h << 16) - h."""
    h = 0
    for ch in s:
        h = (ord(ch) + (h << 6) + (h << 16) - h) & _M32
    return h


def jenkins_one_at_a_time(s: str) -> int:
    """Jenkins' one-at-a-time hash."""
    h = 0
    for byte in s.encode("utf-8"):
        h = (h + byte) & _M32
        h = (h + (h << 10)) & _M32
        h ^= h >> 6
    h = (h + (h << 3)) & _M32
    h ^= h >> 11
    h = (h + (h << 15)) & _M32
    return h & _M32


def _build_crc_table() -> tuple:
    table = []
    for n in range(256):
        c = n
        for _ in range(8):
            c = (c >> 1) ^ 0xEDB88320 if c & 1 else c >> 1
        table.append(c)
    return tuple(table)


_CRC_TABLE = _build_crc_table()


def crc32_hash(s: str) -> int:
    """CRC-32 (IEEE 802.3, table-driven) used as a hash.

    Deliberately implemented in pure Python rather than calling ``zlib``:
    every function here then runs on the same interpreter footing, so the
    timing comparison is not skewed by one function being native C code.
    Verified bit-for-bit against ``zlib.crc32`` in the tests.
    """
    crc = _M32
    for byte in s.encode("utf-8"):
        crc = _CRC_TABLE[(crc ^ byte) & 0xFF] ^ (crc >> 8)
    return crc ^ _M32


# --------------------------------------------------------------------------
# Added after the 0th review
# --------------------------------------------------------------------------
def fnv1(s: str) -> int:
    """FNV-1 32-bit: multiply first, then XOR (the older sibling of FNV-1a)."""
    h = 0x811C9DC5
    for byte in s.encode("utf-8"):
        h = (h * 0x01000193) & _M32
        h ^= byte
    return h


def murmur3_32(s: str, seed: int = 0) -> int:
    """MurmurHash3 x86_32 (Austin Appleby), the hash used by many hash maps."""
    data = s.encode("utf-8")
    c1, c2 = 0xCC9E2D51, 0x1B873593
    h = seed & _M32
    n = len(data)
    nblocks = n // 4

    for i in range(nblocks):
        k = int.from_bytes(data[4 * i:4 * i + 4], "little")
        k = (k * c1) & _M32
        k = _rotl32(k, 15)
        k = (k * c2) & _M32
        h ^= k
        h = _rotl32(h, 13)
        h = (h * 5 + 0xE6546B64) & _M32

    tail = data[nblocks * 4:]
    k = 0
    if len(tail) >= 3:
        k ^= tail[2] << 16
    if len(tail) >= 2:
        k ^= tail[1] << 8
    if len(tail) >= 1:
        k ^= tail[0]
        k = (k * c1) & _M32
        k = _rotl32(k, 15)
        k = (k * c2) & _M32
        h ^= k

    h ^= n
    h ^= h >> 16
    h = (h * 0x85EBCA6B) & _M32
    h ^= h >> 13
    h = (h * 0xC2B2AE35) & _M32
    h ^= h >> 16
    return h


_P1, _P2, _P3, _P4, _P5 = 2654435761, 2246822519, 3266489917, 668265263, 374761393


def xxhash32(s: str, seed: int = 0) -> int:
    """xxHash32 (Yann Collet): very fast, strong avalanche."""
    data = s.encode("utf-8")
    n = len(data)
    i = 0

    def rnd(acc: int, inp: int) -> int:
        acc = (acc + inp * _P2) & _M32
        acc = _rotl32(acc, 13)
        return (acc * _P1) & _M32

    if n >= 16:
        v1 = (seed + _P1 + _P2) & _M32
        v2 = (seed + _P2) & _M32
        v3 = seed & _M32
        v4 = (seed - _P1) & _M32
        while i <= n - 16:
            v1 = rnd(v1, int.from_bytes(data[i:i + 4], "little"))
            v2 = rnd(v2, int.from_bytes(data[i + 4:i + 8], "little"))
            v3 = rnd(v3, int.from_bytes(data[i + 8:i + 12], "little"))
            v4 = rnd(v4, int.from_bytes(data[i + 12:i + 16], "little"))
            i += 16
        h = (_rotl32(v1, 1) + _rotl32(v2, 7) + _rotl32(v3, 12) + _rotl32(v4, 18)) & _M32
    else:
        h = (seed + _P5) & _M32

    h = (h + n) & _M32
    while i + 4 <= n:
        h = (h + int.from_bytes(data[i:i + 4], "little") * _P3) & _M32
        h = (_rotl32(h, 17) * _P4) & _M32
        i += 4
    while i < n:
        h = (h + data[i] * _P5) & _M32
        h = (_rotl32(h, 11) * _P1) & _M32
        i += 1

    h ^= h >> 15
    h = (h * _P2) & _M32
    h ^= h >> 13
    h = (h * _P3) & _M32
    h ^= h >> 16
    return h


def adler32_hash(s: str) -> int:
    """Adler-32 checksum (pure Python; verified against ``zlib.adler32``).
    Weak on short strings; a useful contrast."""
    a, b = 1, 0
    for byte in s.encode("utf-8"):
        a = (a + byte) % 65521
        b = (b + a) % 65521
    return (b << 16) | a


def linux_dcache_hash(s: str) -> int:
    """Linux-kernel style name hash.

    Mirrors the kernel's directory-entry (dcache) string hash:
    ``partial_name_hash(c, h) = (h + (c << 4) + (c >> 4)) * 11`` per character,
    followed by the 32-bit golden-ratio multiplicative finalizer
    (``GOLDEN_RATIO_32 = 0x9E3779B1``) used by ``hash_32``/``end_name_hash``.
    Computed here in 32-bit arithmetic (the kernel uses ``unsigned long``).
    """
    h = 0
    for byte in s.encode("utf-8"):
        h = ((h + (byte << 4) + (byte >> 4)) * 11) & _M32
    return (h * 0x9E3779B1) & _M32


def lose_lose(s: str) -> int:
    """K&R 'lose-lose': the sum of the characters.

    Deliberately terrible (anagrams always collide, values cluster in a tiny
    range). Included as a *baseline* so the metrics visibly separate a bad
    hash from a good one.
    """
    return sum(s.encode("utf-8")) & _M32


class HashInfo(NamedTuple):
    family: str
    description: str


# name -> callable. Original five first so earlier reports stay comparable.
HASH_FUNCTIONS: Dict[str, Callable[[str], int]] = {
    "DJB2": djb2,
    "FNV-1a": fnv1a,
    "SDBM": sdbm,
    "Jenkins (one-at-a-time)": jenkins_one_at_a_time,
    "CRC32": crc32_hash,
    "FNV-1": fnv1,
    "MurmurHash3": murmur3_32,
    "xxHash32": xxhash32,
    "Adler-32": adler32_hash,
    "Linux dcache": linux_dcache_hash,
    "Lose-lose (baseline)": lose_lose,
}

HASH_INFO: Dict[str, HashInfo] = {
    "DJB2": HashInfo("Classic string hash", "h = h*33 + c; tiny and fast, popular in compilers."),
    "FNV-1a": HashInfo("Classic string hash", "XOR then multiply by FNV prime; good distribution for short keys."),
    "SDBM": HashInfo("Classic string hash", "h = c + (h<<6) + (h<<16) - h; used in sdbm/gawk."),
    "Jenkins (one-at-a-time)": HashInfo("Classic string hash", "Add/shift/xor mixing with a final avalanche."),
    "CRC32": HashInfo("Checksum", "Error-detection polynomial code reused as a hash."),
    "FNV-1": HashInfo("Classic string hash", "Multiply then XOR; weaker low-bit mixing than FNV-1a."),
    "MurmurHash3": HashInfo("Modern non-crypto", "32-bit block mixer with strong finalizer; used by many hash maps."),
    "xxHash32": HashInfo("Modern non-crypto", "Very fast with strong avalanche."),
    "Adler-32": HashInfo("Checksum", "Two running sums mod 65521; poor on short inputs."),
    "Linux dcache": HashInfo("Kernel", "Linux dentry name hash: partial_name_hash + golden-ratio finalizer."),
    "Lose-lose (baseline)": HashInfo("Baseline (poor)", "Sum of characters; deliberately bad reference point."),
}
