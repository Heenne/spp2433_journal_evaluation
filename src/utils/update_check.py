"""Check the GitHub Releases page for a newer packaged application version."""

import json
import re
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


REPOSITORY = "Heenne/spp2433_journal_evaluation"
LATEST_RELEASE_API = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"
LATEST_RELEASE_PAGE = f"https://github.com/{REPOSITORY}/releases/latest"
_VERSION_PATTERN = re.compile(
    r"^v?(\d+)\.(\d+)\.(\d+)(?:[-.]([0-9A-Za-z][0-9A-Za-z.-]*))?$"
)


def packaged_application_version(executable_path: str | None = None) -> str | None:
    """Read the version encoded in the packaged executable's release filename."""
    if executable_path is None:
        if not getattr(sys, "frozen", False):
            return None
        executable_path = sys.executable

    stem = Path(executable_path).stem
    prefix = "PointCloudEvaluation-"
    if not stem.startswith(prefix):
        return None

    version = stem[len(prefix):]
    if version.endswith("-runtime"):
        version = version[:-len("-runtime")]
    match = _VERSION_PATTERN.fullmatch(version)
    return version.lstrip("v") if match else None


def is_newer_version(candidate: str, current: str) -> bool:
    """Compare the numeric release components and optional prerelease suffix."""
    candidate_match = _VERSION_PATTERN.fullmatch(candidate.removeprefix("v"))
    current_match = _VERSION_PATTERN.fullmatch(current.removeprefix("v"))
    if candidate_match is None or current_match is None:
        return False

    candidate_parts = tuple(map(int, candidate_match.groups()[:3]))
    current_parts = tuple(map(int, current_match.groups()[:3]))
    if candidate_parts != current_parts:
        return candidate_parts > current_parts

    candidate_suffix = candidate_match.group(4)
    current_suffix = current_match.group(4)
    if candidate_suffix is None:
        return current_suffix is not None
    if current_suffix is None:
        return False
    return candidate_suffix.lower() > current_suffix.lower()


def fetch_newer_release(current_version: str) -> dict | None:
    """Return the latest release details when it is newer; fail silently offline."""
    request = Request(
        LATEST_RELEASE_API,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "SPP2433-PointCloudEvaluation",
        },
    )
    try:
        with urlopen(request, timeout=4) as response:
            release = json.loads(response.read(1_000_000).decode("utf-8"))
    except (OSError, URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError):
        return None

    tag = release.get("tag_name") if isinstance(release, dict) else None
    if not isinstance(tag, str) or not is_newer_version(tag, current_version):
        return None

    release_url = release.get("html_url")
    if not isinstance(release_url, str) or not release_url.startswith(
        f"https://github.com/{REPOSITORY}/releases/"
    ):
        release_url = LATEST_RELEASE_PAGE
    return {"version": tag, "url": release_url}
