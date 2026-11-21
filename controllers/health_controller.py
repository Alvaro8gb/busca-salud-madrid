"""Controlador: coordina Modelo y Vistas. Recibe la intención del usuario, consulta el modelo y decide qué vista pinta."""

from __future__ import annotations

import streamlit as st
import pandas as pd

from models.health_model import HealthModel
from models.repository import HealthCenterRepository
from models.location_service import geocode_location, rank_by_external_route
from views.detail_view import DetailView
from views.location_search_view import LocationSearchView
from views.map_view import MapView
from views.sidebar_view import SidebarView
from views.stats_view import StatsView
from views.table_view import TableView


@st.cache_data(ttl=3600, max_entries=1, show_spinner="Descargando centros sanitarios…")
def _load_centers() -> pd.DataFrame:
    return HealthCenterRepository().load_centers()


@st.cache_resource(ttl=3600, show_spinner="Preparando centros sanitarios…")
def _load_model() -> HealthModel:
    """El modelo se construye una sola vez y se reutiliza entre interacciones."""
    return HealthModel(_load_centers())


class HealthController:
    def __init__(self) -> None:
        self.model = _load_model()

    def run(self) -> None:
        st.title("Centros sanitarios de la Comunidad de Madrid")

        # 1) La vista recoge la intención del usuario en el panel principal.
        criteria = SidebarView.render(self.model.catalog())

        # 2) El modelo resuelve la consulta.
        resultados = self.model.search(criteria)
        resumen = self.model.summarize(resultados)

        # 3) Las vistas pintan el resultado.
        StatsView.render_kpis(resumen)
        sin_ubicacion = resumen["total"] - resumen["con_ubicacion"]
        if sin_ubicacion:
            st.caption(
                f"{sin_ubicacion} centros de la selección no tienen coordenadas válidas y no aparecen en el mapa."
            )

        location, reason, radius_km, search_submitted = LocationSearchView.render(
            self.model.catalog().especialidades
        )

        if search_submitted:
            gps_coordinates = st.session_state.get("gps_coordinates")
            origin = None

            if location.strip():
                with st.spinner("Buscando la ubicación…"):
                    try:
                        origin = geocode_location(location)
                        if origin is None:
                            st.warning("No se encontró esa ubicación en Madrid.")
                    except Exception as exc:
                        st.error(f"No se pudo geocodificar la ubicación: {exc}")
            elif gps_coordinates:
                origin = (
                    float(gps_coordinates["lat"]),
                    float(gps_coordinates["lon"]),
                    "Ubicación GPS",
                )

            if origin:
                lat, lon, label = origin
                st.caption(f"Origen: {label}")

                care_results = self.model.find_by_service(reason)
                care_results = care_results[care_results["registro"].isin(resultados["registro"])].head(100)

                if care_results.empty:
                    st.warning(f"No se encontraron centros con el servicio «{reason}».")
                else:
                    try:
                        ranked = rank_by_external_route(
                            lat,
                            lon,
                            care_results.to_dict("records"),
                        )
                    except Exception as exc:
                        st.error(f"No se pudo calcular las rutas: {exc}")
                        ranked = []

                    if not ranked:
                        st.warning("OSRM no pudo calcular una ruta para ningún centro.")
                    else:
                        ranked = [
                            center for center in ranked
                            if center["distancia_km"] <= radius_km
                        ]

                        if not ranked:
                            st.warning(
                                f"No hay centros con «{reason}» dentro de {radius_km:g} km."
                            )
                            st.session_state.pop("care_search_results", None)
                            st.session_state.pop("care_origin", None)
                            st.session_state.pop("care_radius_km", None)
                        else:
                            st.success(
                                f"Se encontraron {len(ranked)} centros dentro de {radius_km:g} km."
                            )
                            st.session_state["care_search_results"] = ranked
                            st.session_state["care_origin"] = {"lat": lat, "lon": lon}
                            st.session_state["care_radius_km"] = radius_km

                            ranked_df = pd.DataFrame(ranked)
                            st.dataframe(
                                ranked_df[[
                                    "tipo", "direccion", "municipio", "distancia_km",
                                    "duracion_min", "registro",
                                ]].rename(columns={
                                    "tipo": "Centro",
                                    "direccion": "Dirección",
                                    "municipio": "Municipio",
                                    "distancia_km": "Distancia (km)",
                                    "duracion_min": "Duración en coche (min)",
                                    "registro": "Registro",
                                }),
                                key="route_results",
                                hide_index=True,
                            )

                            first = ranked[0]
                            st.link_button(
                                "Abrir mejor ruta",
                                f"https://www.google.com/maps/dir/?api=1&origin={lat},{lon}&destination={first['lat']},{first['lon']}&travelmode=driving",
                                icon=":material/directions:",
                            )
            else:
                st.error("Introduce una ubicación o permite usar tu ubicación GPS.")

        tab_mapa, tab_tabla, tab_stats = st.tabs(["Mapa", "Tabla", "Estadísticas"])

        with tab_mapa:
            col_mapa, col_ficha = st.columns([3, 1])
            with col_mapa:
                nearby = st.session_state.get("care_search_results")
                map_origin = st.session_state.get("care_origin")
                map_radius = st.session_state.get("care_radius_km")
                map_results = pd.DataFrame(nearby) if nearby else resultados
                registro = MapView.render(map_results, map_origin, map_radius)
            with col_ficha:
                DetailView.render(self.model.get_center(registro) if registro else None)

        with tab_tabla:
            TableView.render(resultados)

        with tab_stats:
            StatsView.render_charts(self.model.breakdowns(resultados))
