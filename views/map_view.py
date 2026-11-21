"""Vista: mapa interactivo (pydeck). Devuelve el nº de registro del centro seleccionado, si lo hay."""

from __future__ import annotations

import math

import pandas as pd
import pydeck as pdk
import streamlit as st

import config

_TOOLTIP_STYLE = {"backgroundColor": "#1f2937", "color": "white", "fontSize": "12px"}
_RADIO_BASE = {"Hospitales": 260, "Atención primaria": 160}


class MapView:
    @staticmethod
    def render(df: pd.DataFrame) -> str | None:
        puntos = df[df["tiene_ubicacion"]]
        if puntos.empty:
            st.info("No hay centros con ubicación para los filtros seleccionados.")
            return None

        data = MapView._scatter_data(puntos)
        layer = pdk.Layer(
            "ScatterplotLayer",
            id="centros",
            data=data,
            get_position="[lon, lat]",
            get_fill_color="color",
            get_radius="radio",
            radius_min_pixels=3,
            radius_max_pixels=16,
            pickable=True,
            auto_highlight=True,
        )
        tooltip = {
            "html": "<b>{tipo}</b><br/>{direccion}<br/>{municipio}<br/>{n_servicios} servicios",
            "style": _TOOLTIP_STYLE,
        }
        MapView._legend(puntos)
        deck = pdk.Deck(
            layers=[layer],
            initial_view_state=MapView._view_state(puntos),
            tooltip=tooltip,
        )

        event = st.pydeck_chart(
            deck,
            height=620,
            key="mapa_puntos",
            on_select="rerun",
            selection_mode="single-object",
        )
        objetos = (event.selection or {}).get("objects", {}) if event else {}
        seleccion = objetos.get("centros") or []
        return seleccion[0].get("registro") if seleccion else None

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _scatter_data(puntos: pd.DataFrame) -> pd.DataFrame:
        data = puntos[
            ["registro", "tipo", "direccion", "municipio", "n_servicios", "lat", "lon"]
        ].copy()
        data["color"] = (
            puntos["categoria"].map(config.COLOR_POR_CATEGORIA).map(lambda c: c + [200])
        )
        data["radio"] = puntos["categoria"].map(_RADIO_BASE).fillna(70)
        return data

    @staticmethod
    def _view_state(puntos: pd.DataFrame) -> pdk.ViewState:
        lat_min, lat_max = puntos["lat"].min(), puntos["lat"].max()
        lon_min, lon_max = puntos["lon"].min(), puntos["lon"].max()
        span = max(
            lat_max - lat_min,
            (lon_max - lon_min) * math.cos(math.radians(lat_min)),
            0.002,
        )
        zoom = max(8.0, min(15.0, math.log2(360 / span) - 1.2))
        return pdk.ViewState(
            latitude=float((lat_min + lat_max) / 2),
            longitude=float((lon_min + lon_max) / 2),
            zoom=zoom,
            pitch=0,
        )

    @staticmethod
    def _legend(puntos: pd.DataFrame) -> None:
        presentes = [
            c for c in config.COLOR_POR_CATEGORIA if c in set(puntos["categoria"])
        ]
        items = " &nbsp; ".join(
            f"<span style='color:rgb({','.join(map(str, config.COLOR_POR_CATEGORIA[c]))})'>●</span> {c}"
            for c in presentes
        )
        st.markdown(
            f"<div style='font-size:0.85rem'>{items}</div>", unsafe_allow_html=True
        )
