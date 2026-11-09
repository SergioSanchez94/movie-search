const $ = (id) => document.getElementById(id);
const state = { query: "", page: 1, pages: 1, controller: null };
const imageBase = "https://image.tmdb.org/t/p/";

function el(tag, className, value) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (value !== undefined) node.textContent = value;
  return node;
}
function poster(path, size = "w342") {
  if (!path) return el("div", "poster", "Sin cartel");
  const img = el("img", "poster");
  img.src = imageBase + size + path;
  img.alt = "Cartel de la película";
  img.loading = "lazy";
  return img;
}
function year(date) { return date ? date.slice(0, 4) : "—"; }
function rating(value) { return value ? "★ " + Number(value).toFixed(1) : "Sin valorar"; }

async function getJson(url, signal) {
  const response = await fetch(url, { signal });
  let data;
  try { data = await response.json(); } catch { throw new Error("Respuesta inesperada del servidor"); }
  if (!response.ok) throw new Error(data.detail || "No se pudo completar la solicitud");
  return data;
}
function renderMovie(movie) {
  const button = el("button", "movie");
  button.type = "button";
  button.setAttribute("aria-label", "Ver ficha de " + (movie.title || "película"));
  button.append(poster(movie.poster_path), el("div", "movie-title", movie.title || "Sin título"));
  const meta = el("div", "meta");
  meta.append(el("span", "", year(movie.release_date)), el("span", "rating", rating(movie.vote_average)));
  button.append(meta);
  button.addEventListener("click", () => openDetail(movie.id));
  return button;
}
async function loadMovies() {
  state.controller?.abort();
  state.controller = new AbortController();
  const signal = state.controller.signal;
  $("movies").replaceChildren();
  $("message").textContent = "Cargando películas…";
  $("results-title").textContent = state.query ? 'Resultados de «' + state.query + '»' : "Películas populares";
  $("result-count").textContent = "";
  $("prev").hidden = $("next").hidden = true;
  $("page-info").textContent = "";
  const endpoint = state.query ? "/api/movies/search?q=" + encodeURIComponent(state.query) : "/api/movies/popular";
  try {
    const data = await getJson(endpoint + (endpoint.includes("?") ? "&" : "?") + "page=" + state.page, signal);
    const movies = data.results || [];
    state.pages = Math.min(data.total_pages || 1, 500);
    $("message").textContent = movies.length ? "" : "No se encontraron películas. Prueba con otro título.";
    $("result-count").textContent = (data.total_results || 0).toLocaleString("es-ES") + " películas";
    const fragment = document.createDocumentFragment();
    movies.forEach(movie => fragment.append(renderMovie(movie)));
    $("movies").append(fragment);
    $("page-info").textContent = "Página " + state.page + " de " + state.pages;
    $("prev").hidden = state.page <= 1;
    $("next").hidden = state.page >= state.pages;
  } catch (error) {
    if (error.name !== "AbortError") $("message").textContent = error.message;
  }
}
async function openDetail(id) {
  const dialog = $("detail-dialog");
  const content = $("detail-content");
  content.replaceChildren(el("p", "", "Cargando ficha…"));
  dialog.showModal();
  try {
    const movie = await getJson("/api/movies/" + encodeURIComponent(id));
    if (!dialog.open) return;
    const detail = el("div", "detail");
    const left = poster(movie.poster_path, "w500");
    const right = el("div");
    right.append(el("h2", "", movie.title || "Sin título"));
    if (movie.tagline) right.append(el("p", "tagline", movie.tagline));
    const facts = [year(movie.release_date), movie.runtime ? movie.runtime + " min" : null, rating(movie.vote_average), (movie.genres || []).map(g => g.name).join(" · ")].filter(Boolean);
    right.append(el("p", "facts", facts.join("  •  ")));
    right.append(el("p", "", movie.overview || "Sin sinopsis disponible."));
    detail.append(left, right);
    content.replaceChildren(detail);
  } catch (error) {
    if (dialog.open) content.replaceChildren(el("p", "message", error.message));
  }
}
$("search-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const query = $("search-input").value.trim();
  if (!query) return;
  state.query = query;
  state.page = 1;
  loadMovies();
});
$("prev").addEventListener("click", () => { if (state.page > 1) { state.page--; loadMovies(); $("results-title").scrollIntoView({behavior:"smooth"}); } });
$("next").addEventListener("click", () => { if (state.page < state.pages) { state.page++; loadMovies(); $("results-title").scrollIntoView({behavior:"smooth"}); } });
$("close-dialog").addEventListener("click", () => $("detail-dialog").close());
loadMovies();
