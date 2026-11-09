"""Read public search-result metadata from a fixed catalog host.

No download URLs, magnet links, or external links are returned.
The upstream markup has not been verified; selectors may need adjustment.
"""
import logging
import re
import unicodedata

import httpx
from bs4 import BeautifulSoup
from fastapi import HTTPException

SEARCH_URL = "https://www47.mejortorrent.eu/busqueda"
MAX_RESULTS = 40
logger = logging.getLogger(__name__)


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.casefold())
    return "".join(c for c in value if not unicodedata.combining(c))


def parse_results(html: str, query: str) -> list[dict[str, str]]:
    """Read result titles from anchors, including table-style search layouts."""
    soup = BeautifulSoup(html, "html.parser")
    for element in soup(["script", "style", "nav", "header", "footer", "form"]):
        element.decompose()
    terms = [term for term in re.findall(r"\w+", normalize(query)) if len(term) > 1]
    if not terms:
        return []

    matches = []
    seen = set()
    # The catalog may present search entries as plain anchors inside a table,
    # rather than article/card elements. Never return the href or downloads.
    for anchor in soup.select("a"):
        title = re.sub(r"\s+", " ", anchor.get_text(" ", strip=True)).strip()[:200]
        if not title or len(title) < 3:
            continue
        normalized = normalize(title)
        if not all(term in normalized for term in terms):
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        quality_match = re.search(
            r"4K|2160p|1080p|720p|BDRemux|BluRay|FullBluRay|MicroHD|DVDRip|WEB[- .]?DL",
            title,
            flags=re.IGNORECASE,
        )
        matches.append({
            "title": title,
            "quality": quality_match.group(0) if quality_match else "",
            "description": "",
        })
        if len(matches) >= MAX_RESULTS:
            break
    return matches


async def search_catalog(query: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=12.0, follow_redirects=False) as client:
            response = await client.get(
                SEARCH_URL,
                params={"q": query},
                headers={"User-Agent": "MovieSearch/1.0 (metadata search; no downloads)"},
            )
        if response.is_redirect:
            logger.warning("Catalog redirected: HTTP %s", response.status_code)
            raise HTTPException(502, "El catálogo ha redirigido la solicitud (HTTP " + str(response.status_code) + ").")
        response.raise_for_status()
        if "html" not in response.headers.get("content-type", "").lower():
            raise HTTPException(502, "El catálogo no ha devuelto HTML.")
        if len(response.content) > 2_000_000:
            raise HTTPException(502, "La respuesta del catálogo es demasiado grande.")
        results = parse_results(response.text, query)
        return {"query": query, "results": results, "count": len(results)}
    except httpx.TimeoutException:
        logger.warning("Catalog request timed out")
        raise HTTPException(504, "Tiempo de espera agotado al consultar el catálogo.") from None
    except httpx.HTTPStatusError as exc:
        logger.warning("Catalog returned HTTP %s", exc.response.status_code)
        raise HTTPException(502, f"El catálogo no está disponible (HTTP {exc.response.status_code}).") from None
    except httpx.RequestError as exc:
        logger.warning("Catalog connection error: %s", type(exc).__name__)
        raise HTTPException(502, "No se ha podido conectar con el catálogo (" + type(exc).__name__ + ").") from None
