"""Vista: mapa interactivo (pydeck). Devuelve el nº de registro del centro seleccionado, si lo hay."""

from __future__ import annotations

import math

import pandas as pd
import pydeck as pdk
import streamlit as st

import config

_TOOLTIP_STYLE = {"backgroundColor": "#ffffff", "color": "#1f2937", "border": "1px solid #d1d5db", "fontSize": "12px"}
_RADIO_BASE = {"Hospitales": 260, "Atención primaria": 160}


class MapView:
    @staticmethod
    def render(
        df: pd.DataFrame,
        origin: dict | None = None,
        radius_km: float | None = None,
    ) -> dict | None:
        puntos = df[df["tiene_ubicacion"]]
        if puntos.empty:
            st.info("No hay centros con ubicación para los filtros seleccionados.")
            return None

        data = MapView._scatter_data(puntos)
        layers = [pdk.Layer(
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
        )]

        if origin:
            lat = origin["lat"]
            lon = origin["lon"]
            origin_data = [{
                "poligono": [[
                    [lon, lat - 0.0006],
                    [lon - 0.00055, lat + 0.00045],
                    [lon + 0.00055, lat + 0.00045],
                    [lon, lat - 0.0006],
                ]]
            }]
            layers.append(pdk.Layer(
                "PolygonLayer",
                id="origen",
                data=origin_data,
                get_polygon="poligono",
                get_fill_color=[25, 118, 210, 255],
                get_line_color=[255, 255, 255, 255],
                line_width_min_pixels=2,
                stroked=True,
                filled=True,
                extruded=False,
                pickable=False,
            ))
        if origin and radius_km:
            layers.append(pdk.Layer(
                "ScatterplotLayer",
                id="radio",
                data=[{"lat": origin["lat"], "lon": origin["lon"]}],
                get_position="[lon, lat]",
                get_fill_color=[25, 118, 210, 20],
                get_line_color=[25, 118, 210, 180],
                stroked=True,
                filled=True,
                get_radius=radius_km * 1000,
                radius_min_pixels=1,
                pickable=False,
            ))

        tooltip = {
            "html": "<b>{tipo}</b><br/>{direccion}<br/>{municipio}<br/>{n_servicios} servicios",
            "style": _TOOLTIP_STYLE,
        }
        MapView._legend(puntos)
        view_points = puntos
        if origin:
            origin_point = pd.DataFrame([{"lat": origin["lat"], "lon": origin["lon"]}])
            view_points = pd.concat([puntos[["lat", "lon"]], origin_point], ignore_index=True)

        deck = pdk.Deck(
            layers=layers,
            initial_view_state=MapView._view_state(view_points),
            tooltip=tooltip,
            map_style=pdk.map_styles.CARTO_LIGHT,
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
        return seleccion[0] if seleccion else None

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
