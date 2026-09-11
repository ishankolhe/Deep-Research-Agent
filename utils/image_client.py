import os
import requests

PEXELS_KEY = os.environ.get("PEXELS_API_KEY", "")


def find_image(query: str) -> str | None:
    """Returns a single image URL relevant to the query, or None if unavailable."""
    if not PEXELS_KEY:
        return None
    try:
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": PEXELS_KEY},
            params={"query": query, "per_page": 1},
            timeout=10,
        )
        resp.raise_for_status()
        photos = resp.json().get("photos", [])
        if photos:
            return photos[0]["src"]["large"]
    except Exception:
        return None
    return None


def download_image(url: str, dest_path: str) -> bool:
    """Downloads an image URL to a local path. Returns True on success."""
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        with open(dest_path, "wb") as f:
            f.write(resp.content)
        return True
    except Exception:
        return False
