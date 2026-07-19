from abc import ABC, abstractmethod
from typing import Optional
from solid_checker.ir.models import Module


class BaseAdapter(ABC):
    """Abstract base class for language adapters."""

    @abstractmethod
    def parse(self, file_path: str, source: str) -> Module:
        """Parse source code into a normalized IR Module."""
        ...

    @property
    @abstractmethod
    def language(self) -> str:
        """Return the language name this adapter handles."""
        ...

    @property
    def supported_extensions(self) -> list[str]:
        """Return file extensions this adapter handles."""
        return []
