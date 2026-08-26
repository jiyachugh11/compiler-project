"""String interning pool mapping identifiers to stable integer IDs."""

from typing import Dict, List, Optional


class StringPool:
    """Manages string interning for identifier deduplication and fast ID mapping.

    Guarantees:
    - Identifier string -> stable integer ID (0-indexed and sequential)
    - Repeated identifiers receive the exact same integer ID
    - Reverse mapping (ID -> string) is preserved and O(1) accessible
    """

    def __init__(self) -> None:
        self._str_to_id: Dict[str, int] = {}
        self._id_to_str: List[str] = []

    def intern(self, identifier: str) -> int:
        """Intern an identifier string and return its stable integer ID.

        If the identifier has already been interned, its existing ID is returned.
        Otherwise, a new sequential 0-indexed ID is assigned.

        Args:
            identifier: The string to intern.

        Returns:
            The stable integer ID for the identifier.
        """
        if identifier in self._str_to_id:
            return self._str_to_id[identifier]

        new_id = len(self._id_to_str)
        self._str_to_id[identifier] = new_id
        self._id_to_str.append(identifier)
        return new_id

    def get_id(self, identifier: str) -> Optional[int]:
        """Look up the integer ID for a previously interned string.

        Args:
            identifier: The string to look up.

        Returns:
            The integer ID if interned, else None.
        """
        return self._str_to_id.get(identifier)

    def get_string(self, intern_id: int) -> Optional[str]:
        """Retrieve the original identifier string for a given intern ID.

        Args:
            intern_id: The integer ID to look up.

        Returns:
            The original string if the ID exists in the pool, else None.
        """
        if isinstance(intern_id, int) and 0 <= intern_id < len(self._id_to_str):
            return self._id_to_str[intern_id]
        return None

    def contains(self, identifier: str) -> bool:
        """Check if an identifier has been interned in the pool.

        Args:
            identifier: The string to check.

        Returns:
            True if the identifier is interned, False otherwise.
        """
        return identifier in self._str_to_id

    def __contains__(self, identifier: str) -> bool:
        """Support the `in` operator (e.g. 'foo' in pool)."""
        return self.contains(identifier)

    def size(self) -> int:
        """Return the count of unique interned identifiers."""
        return len(self._id_to_str)

    def __len__(self) -> int:
        """Support `len(pool)`."""
        return self.size()

    def get_all_strings(self) -> List[str]:
        """Return a list of all interned strings ordered by their assigned integer IDs."""
        return list(self._id_to_str)

    def get_mapping(self) -> Dict[str, int]:
        """Return a copy of all interned string-to-ID mappings."""
        return dict(self._str_to_id)

    def clear(self) -> None:
        """Reset the pool, clearing all interned strings and IDs."""
        self._str_to_id.clear()
        self._id_to_str.clear()
