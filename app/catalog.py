"""Read public search-result metadata from a fixed catalog host.

No download URLs, magnet links, or external links are returned.
The upstream markup has not been verified; selectors may need adjustment.
"""
import re
import unicodedata

import httpx
from bs4 import BeautifulSoup
from fastapi import HTTPException

SEARCH_URL = "https://www47.mejortorrent.eu/busqueda"
MAX_RESULTS = 40


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.casefold())
    return "".join(c for c in value if not unicodedata.combining(c))


def parse_results(html: str, query: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    for element in soup(["script", "style", "nav", "header", "footer", "form"]):
        element.decompose()
    terms = [term for term in re.findall(r"\w+", normalize(query)) if len(term) > 1]
    if not terms:
        return []
    matches = []
    seen = set()
    # Only inspect result-like containers, not every navigation link on the page.
    selectors = "article, .resultado, .result, .search-result, .card, .item, tbody tr, .list-group-item"
    for node in soup.select(selectors):
        title_node = node.select_one("h2, h3, h4, .title, .titulo, a[title]")
        if title_node is None:
            continue
        title = (title_node.get("title") or title_node.get_text(" ", strip=True)).strip()
        title = re.sub(r"\s+", " ", title)[:200]
        if len(title) < 3 or not all(term in normalize(title) for term in terms):
            continue
        key = normalize(title)
        if key in seen:
            continue
        seen.add(key)
        summary = re.sub(r"\s+", " ", node.get_text(" ", strip=True))
        summary = summary[:320]
        matches.append({"title": title, "description": summary if summary != title else ""})
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
            raise HTTPException(502, "El catálogo ha redirigido la solicitud.")
        response.raise_for_status()
        if "html" not in response.headers.get("content-type", "").lower():
            raise HTTPException(502, "El catálogo no ha devuelto HTML.")
        if len(response.content) > 2_000_000:
            raise HTTPException(502, "La respuesta del catálogo es demasiado grande.")
        results = parse_results(response.text, query)
        return {"query": query, "results": results, "count": len(results)}
    except httpx.TimeoutException:
        raise HTTPException(504, "Tiempo de espera agotado al consultar el catálogo.") from None
    except httpx.HTTPStatusError as exc:
        raise HTTPException(502, f"El catálogo no está disponible (HTTP {exc.response.status_code}).") from None
    except httpx.RequestError:
        raise HTTPException(502, "No se ha podido conectar con el catálogo.") from None
