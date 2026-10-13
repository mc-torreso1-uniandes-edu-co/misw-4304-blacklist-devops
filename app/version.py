from pathlib import Path

from app import constants


def read_app_version(version_file: Path) -> str:
    if not version_file.is_file():
        return constants.DEFAULT_APP_VERSION
    version = version_file.read_text(encoding="utf-8").strip()
    return version or constants.DEFAULT_APP_VERSION
