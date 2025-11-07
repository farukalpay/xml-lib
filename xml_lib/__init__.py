"""Compatibility package exposing modules from :mod:`cli.xml_lib`."""

from __future__ import annotations

import importlib
import sys
from types import ModuleType
from typing import Iterable

_upstream: ModuleType = importlib.import_module("cli.xml_lib")

__all__ = list(getattr(_upstream, "__all__", ()))
__doc__ = getattr(_upstream, "__doc__", None)
__version__ = getattr(_upstream, "__version__", None)

for name in __all__:
    globals()[name] = getattr(_upstream, name)

if hasattr(_upstream, "__path__"):
    __path__ = list(_upstream.__path__)  # type: ignore[attr-defined]
else:  # pragma: no cover - upstream should always be a package
    __path__ = []

sys.modules.setdefault("cli.xml_lib", _upstream)


def __getattr__(name: str):
    return getattr(_upstream, name)


def __dir__() -> Iterable[str]:
    return sorted(set(__all__) | set(dir(_upstream)))
