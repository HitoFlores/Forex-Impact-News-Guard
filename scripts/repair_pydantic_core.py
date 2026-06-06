from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / ".venv" / "Lib" / "site-packages" / "pydantic_core"
SOURCE = Path(
    r"C:\Program Files\LM Studio\resources\app\.webpack\bin\extensions\backends\vendor\_amphibian"
    r"\app-harmony-win-x86@7\Lib\site-packages\pydantic_core"
)


def main() -> None:
    TARGET.mkdir(parents=True, exist_ok=True)
    for path in TARGET.glob("__pycache__"):
        if path.is_dir():
            shutil.rmtree(path)
    shutil.copy2(SOURCE / "_pydantic_core.cp311-win_amd64.pyd", TARGET / "_pydantic_core.cp311-win_amd64.pyd")
    for name in ("__init__.py", "core_schema.py", "_pydantic_core.pyi", "py.typed"):
        shutil.copy2(SOURCE / name, TARGET / name)

    source_pydantic = SOURCE.parent / "pydantic"
    target_pydantic = ROOT / ".venv" / "Lib" / "site-packages" / "pydantic"
    if target_pydantic.exists():
        shutil.rmtree(target_pydantic)
    shutil.copytree(source_pydantic, target_pydantic)

    source_dist = SOURCE.parent / "pydantic-2.12.4.dist-info"
    site_packages = ROOT / ".venv" / "Lib" / "site-packages"
    for pattern in ("pydantic*.dist-info", "pydantic_core*.dist-info"):
        for dist_dir in site_packages.glob(pattern):
            if dist_dir.is_dir():
                shutil.rmtree(dist_dir)
    shutil.copytree(source_dist, site_packages / "pydantic-2.12.4.dist-info")


if __name__ == "__main__":
    main()
