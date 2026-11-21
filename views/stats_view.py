"""Vista: indicadores y gráficos de resumen."""

from __future__ import annotations

import pandas as pd
import streamlit as st


class StatsView:
    @staticmethod
    def render_kpis(resumen: dict) -> None:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Centros", f"{resumen['total']:,}".replace(",", "."))
        c2.metric("En el mapa", f"{resumen['con_ubicacion']:,}".replace(",", "."))
        c3.metric("Municipios", resumen["municipios"])
        c4.metric("Públicos", f"{resumen['publicos']:,}".replace(",", "."))

    @staticmethod
    def render_charts(desgloses: dict[str, pd.Series]) -> None:
        if all(serie.empty for serie in desgloses.values()):
            st.info("Sin datos para mostrar.")
            return
        columnas = st.columns(2)
        for i, (titulo, serie) in enumerate(desgloses.items()):
            with columnas[i % 2]:
                st.markdown(f"**{titulo}**")
                st.bar_chart(serie, horizontal=True, height=320)
