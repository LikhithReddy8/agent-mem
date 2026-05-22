"""
Local mcp package (agent-mem project).

The installed `mcp` library uses the same top-level package name.  To avoid
shadowing it we pre-register the library's submodules in sys.modules here,
before any of our own submodules are imported.
"""
import sys
import os

_site_pkgs = next(
    (p for p in sys.path if "site-packages" in p and os.path.isdir(os.path.join(p, "mcp"))),
    None,
)
if _site_pkgs:
    _old_path = sys.path[:]
    sys.path = [_site_pkgs] + [p for p in sys.path if os.path.abspath(p) != os.path.abspath(os.path.dirname(__file__))]
    # Only pre-import if not already loaded from site-packages
    _mcp_lib_file = os.path.join(_site_pkgs, "mcp", "__init__.py")
    if "mcp._lib" not in sys.modules:
        import importlib.util as _ilu
        # Register installed mcp submodules that our server.py needs
        for _sub in ("mcp.server", "mcp.server.stdio", "mcp.server.lowlevel", "mcp.types"):
            if _sub not in sys.modules:
                try:
                    # Temporarily remove local mcp from modules to allow real import
                    _saved_mcp = sys.modules.pop("mcp", None)
                    import importlib as _il
                    _mod = _il.import_module(_sub)
                    sys.modules[_sub] = _mod
                    if _saved_mcp is not None:
                        sys.modules["mcp"] = _saved_mcp
                except Exception:
                    if _saved_mcp is not None:
                        sys.modules["mcp"] = _saved_mcp
    sys.path = _old_path
