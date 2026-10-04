"""Test bootstrap — make the plugin importable by its tests.

pytest config (pyproject.toml) puts the repo root on sys.path so the plain
``schemas``/``tools`` modules import. The root ``__init__.py`` uses relative
imports (required for the packaging shape), so tests must load it as a
package under a synthetic name instead of the broken
``from __init__ import ...`` top-level form.
"""

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

if "native_extract" not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        "native_extract",
        ROOT / "__init__.py",
        submodule_search_locations=[str(ROOT)],
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["native_extract"] = module
    spec.loader.exec_module(module)
