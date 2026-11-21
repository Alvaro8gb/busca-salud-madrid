"""Vista: ficha de detalle del centro seleccionado en el mapa."""

from __future__ import annotations

import streamlit as st


class DetailView:
    @staticmethod
    def render(centro: dict | None) -> None:
        st.subheader("Ficha del centro")
        if not centro:
            st.caption("Haz clic en un punto del mapa para ver aquí sus datos.")
            return

        st.markdown(f"**{centro['tipo']}**")
        st.caption(f"Nº de registro: {centro['registro']}")
        direccion = centro["direccion"]
        if centro.get("direccion_extra"):
            direccion += f" ({centro['direccion_extra']})"
        st.markdown(
            f"{direccion}  \n{centro.get('codigo_postal') or ''} {centro['municipio']}"
        )
        st.markdown(
            f"**Titularidad:** {centro['titularidad']}  \n"
            f"**Dependencia funcional:** {centro.get('dependencia_funcional') or 'Sin dato'}  \n"
            f"**Dependencia patrimonial:** {centro.get('dependencia_patrimonial') or 'Sin dato'}"
        )
        if centro.get("tiene_ubicacion"):
            lat, lon = centro["lat"], centro["lon"]
            st.link_button(
                "Abrir en OpenStreetMap",
                f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=18/{lat}/{lon}",
            )
        with st.expander(f"Servicios ({centro['n_servicios']})", expanded=True):
            st.markdown("\n".join(f"- {s}" for s in centro["servicios"]))
