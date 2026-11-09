# Movie Search

Buscador web de películas con **FastAPI** y la API de **The Movie Database (TMDB)**. Incluye búsqueda por título, películas populares, fichas con sinopsis, cartel, año, duración y valoración, y paginación.

## Requisitos

- Python 3.10 o posterior
- Una clave de API gratuita de [TMDB](https://www.themoviedb.org/settings/api)

## Iniciar en GitHub Codespaces

1. Abre el repositorio en Codespaces y ejecuta:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   ```

2. Edita `.env` y sustituye `replace_with_your_tmdb_api_key` por tu clave de TMDB. **Nunca subas la clave a GitHub.** Como alternativa, configura `TMDB_API_KEY` como secreto de Codespaces.
3. Inicia la aplicación:

   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

4. Abre el puerto **8000** desde la pestaña **Ports** de Codespaces (o visita http://localhost:8000 en tu equipo).

## API

- `GET /api/health`: estado del servidor y configuración de TMDB
- `GET /api/movies/popular?page=1`: películas populares
- `GET /api/movies/search?q=Interstellar&page=1`: búsqueda de películas
- `GET /api/movies/{movie_id}`: ficha de película
- `GET /docs`: documentación OpenAPI interactiva

## Privacidad y atribución

No utiliza base de datos ni almacena búsquedas. Los metadatos proceden de TMDB. Esta aplicación no está avalada ni certificada por TMDB. No descarga películas ni proporciona enlaces a torrents.
