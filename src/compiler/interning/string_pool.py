"""String interning pool mapping identifiers to stable integer IDs."""

from typing import Dict, List, Optional


class StringPool:
    """Manages string interning for identifier deduplication and fast ID mapping.

    Guarantees:
    - Identifier string -> stable integer ID (0-indexed or sequential)
    - Repeated identifiers receive the exact same integer ID
    - Reverse mapping (ID -> string) is preserved
    """

    def __init__(self) -> None:
        self._str_to_id: Dict[str, int] = {}
        self._id_to_str: List[str] = []

    def intern(self, identifier: str) -> int:
        """Intern an identifier string and return its stable integer ID."""
        raise NotImplementedError("String interning will be implemented in the next phase.")

    def get_string(self, intern_id: int) -> Optional[str]:
        """Retrieve the original identifier string for a given intern ID."""
        raise NotImplementedError("String interning will be implemented in the next phase.")

    def get_mapping(self) -> Dict[str, int]:
        """Return a copy of all interned string-to-ID mappings."""
        return dict(self._str_to_id)

    def __len__(self) -> int:
        """Return the count of unique interned identifiers."""
        return len(self._id_to_str)
