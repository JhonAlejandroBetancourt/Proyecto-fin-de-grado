import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Add common project roots to the Python path.
for candidate in (ROOT, ROOT / "src", ROOT / "app"):
    if candidate.exists():
        sys.path.insert(0, str(candidate))


def _load_create_app():
    search_paths = (
        ROOT / "quiron" / "server.py",
        ROOT / "src" / "quiron" / "server.py",
        ROOT / "app" / "quiron" / "server.py",
    )

    for file_path in search_paths:
        if file_path.exists():
            spec = importlib.util.spec_from_file_location("quiron.server", file_path)
            if spec is not None and spec.loader is not None:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module.create_app

    raise ImportError("Could not find quiron.server. Check the project layout.")


create_app = _load_create_app()
app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)