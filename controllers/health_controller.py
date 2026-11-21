"""Controlador: coordina Modelo y Vistas. Recibe la intención del usuario, consulta el modelo y decide qué vista pinta."""

from __future__ import annotations

import streamlit as st
import pandas as pd

from models.health_model import HealthModel
from models.repository import HealthCenterRepository
from views.detail_view import DetailView
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

        # 1) La vista recoge la intención del usuario (filtros).
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

        tab_mapa, tab_tabla, tab_stats = st.tabs(["Mapa", "Tabla", "Estadísticas"])

        with tab_mapa:
            col_mapa, col_ficha = st.columns([3, 1])
            with col_mapa:
                registro = MapView.render(resultados)
            with col_ficha:
                DetailView.render(self.model.get_center(registro) if registro else None)

        with tab_tabla:
            TableView.render(resultados)

        with tab_stats:
            StatsView.render_charts(self.model.breakdowns(resultados))
