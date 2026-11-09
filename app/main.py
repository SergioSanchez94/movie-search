"""Movie Search API and web application."""
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from .catalog import search_catalog
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()
ROOT = Path(__file__).resolve().parent.parent
app = FastAPI(title="Movie Search", version="1.0.0")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
TMDB_BASE = "https://api.themoviedb.org/3"


@app.get("/", include_in_schema=False)
async def home():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/api/health")
async def health():
    return {"status": "ok", "tmdb_configured": bool(os.getenv("TMDB_API_KEY"))}


async def tmdb_get(path: str, params: dict | None = None):
    api_key = os.getenv("TMDB_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=503, detail="Configura TMDB_API_KEY en el archivo .env")
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            response = await client.get(
                f"{TMDB_BASE}{path}",
                params={"api_key": api_key, "language": "es-ES", **(params or {})},
            )
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="TMDB no ha respondido a tiempo") from None
    except httpx.HTTPStatusError as exc:
        status = 503 if exc.response.status_code in (401, 403, 429) else 502
        raise HTTPException(status_code=status, detail="No se pudieron obtener datos de TMDB") from None
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="No se pudo conectar con TMDB") from None


@app.get("/api/movies/search")
async def search_movies(q: str = Query(min_length=1, max_length=120), page: int = Query(default=1, ge=1, le=500)):
    return await tmdb_get("/search/movie", {"query": q.strip(), "page": page, "include_adult": "false"})


@app.get("/api/movies/popular")
async def popular_movies(page: int = Query(default=1, ge=1, le=500)):
    return await tmdb_get("/movie/popular", {"page": page})


@app.get("/api/movies/{movie_id}")
async def movie_detail(movie_id: int):
    if movie_id <= 0:
        raise HTTPException(status_code=422, detail="Identificador no válido")
    return await tmdb_get(f"/movie/{movie_id}")


@app.get("/api/catalog/search")
async def catalog_search(q: str = Query(min_length=2, max_length=120)):
    return await search_catalog(q.strip())
