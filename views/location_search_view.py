"""Búsqueda por ubicación y motivo de atención."""

from __future__ import annotations

import streamlit as st
from models.location_service import reverse_geocode_location

_GEOLOCATION_COMPONENT = st.components.v2.component(
    "madrid_health_geolocation",
    html="""
<button id="gps-button" type="button">Usar mi ubicación GPS</button>
<p id="gps-status" role="status"></p>
""",
    css="""
button {
  width: 100%;
  min-height: 38px;
  border: 1px solid var(--st-border-color, #d9d9d9);
  border-radius: 8px;
  background: var(--st-secondary-background-color, #f0f2f6);
  color: var(--st-text-color, #262730);
  cursor: pointer;
}
button:hover { border-color: var(--st-primary-color, #ff4b4b); }
p { margin: 8px 0 0; font-size: 0.85rem; }
""",
    js="""
export default function (component) {
  const { parentElement, setStateValue, setTriggerValue } = component;
  const button = parentElement.querySelector("#gps-button");
  const status = parentElement.querySelector("#gps-status");

  button.onclick = () => {
    status.textContent = "Solicitando ubicación…";
    if (!navigator.geolocation) {
      status.textContent = "Este navegador no permite obtener la ubicación.";
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = position.coords.latitude;
        const lon = position.coords.longitude;
        status.textContent = "Ubicación obtenida.";
        setStateValue("coordinates", { lat, lon });
        setTriggerValue("requested", true);
      },
      (error) => {
        status.textContent = "No se pudo obtener la ubicación: " + error.message;
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 300000 }
    );
  };
}
""",
)


class LocationSearchView:
    @staticmethod
    def render(servicios: list[str]) -> tuple[str, str, float, bool]:
        st.subheader("Buscar atención cercana")

        with st.form("location_search", border=True):
            gps_result = _GEOLOCATION_COMPONENT(
                key="gps_location",
                data={"label": "Usar mi ubicación GPS"},
                on_coordinates_change=lambda: None,
                on_requested_change=lambda: None,
            )

            coordinates = getattr(gps_result, "coordinates", None)
            if coordinates:
                st.session_state["gps_coordinates"] = coordinates
                address = reverse_geocode_location(
                    float(coordinates["lat"]), float(coordinates["lon"])
                )
                if address:
                    st.session_state["care_location"] = address

            location, reason, radius_km, submitted = None, None, 10, False
            with st.container(horizontal=True, vertical_alignment="bottom"):
                location = st.text_input(
                    "Ubicación",
                    placeholder="Ej. Calle Alcalá 1, Madrid",
                    key="care_location",
                )
                submitted = st.form_submit_button(
                    "Buscar centros",
                    icon=":material/search:",
                    type="primary",
                )

            reason_col, radius_col = st.columns(2)
            with reason_col:
                reason = st.selectbox(
                    "Motivo o servicio",
                    ["Urgencias y Emergencias", *servicios],
                    key="care_reason",
                )
            with radius_col:
                radius_km = st.slider(
                    "Radio de búsqueda (km)",
                    min_value=1,
                    max_value=50,
                    value=10,
                    step=1,
                    key="care_radius",
                )

        return location, reason, float(radius_km), submitted
