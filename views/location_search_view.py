"""Búsqueda por ubicación y motivo de atención."""

from __future__ import annotations

import streamlit as st

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


_RESET_KEYS = (
    "unified_health_query",
    "gps_coordinates",
    "gps_address_applied",
    "nlp_query_signature",
    "nlp_categorias",
    "nlp_titularidades",
    "nlp_tipos",
    "nlp_municipios",
    "nlp_especialidades",
    "nlp_location",
    "nlp_reason",
    "nlp_radius",
    "care_search_results",
    "care_origin",
    "care_radius_km",
)

_FILTER_WIDGET_KEYS = (
    "nlp_categorias", "nlp_titularidades", "nlp_tipos",
    "nlp_municipios", "nlp_especialidades", "nlp_location",
    "nlp_reason", "nlp_radius",
)


def _clear_all_filters() -> None:
    for key in _RESET_KEYS:
        st.session_state.pop(key, None)


class LocationSearchView:
    @staticmethod
    def render(catalog) -> tuple[object, bool]:
        from models.nlp_parser import parse_search

        st.subheader("Buscar atención sanitaria")

        query = st.text_input(
            "Describe lo que buscas",
            key="unified_health_query",
            placeholder="Ej. Cardiología pública, privado, para niños",
            type="default",
        )

        detected = parse_search(query, catalog)

        query_signature = query.strip().lower()
        if st.session_state.get("nlp_query_signature") != query_signature:
            st.session_state["nlp_query_signature"] = query_signature
            st.session_state["nlp_categorias"] = list(detected.categorias)
            st.session_state["nlp_titularidades"] = list(detected.titularidades)
            st.session_state["nlp_tipos"] = list(detected.tipos)
            st.session_state["nlp_municipios"] = list(detected.municipios)
            st.session_state["nlp_especialidades"] = list(detected.especialidades)
            st.session_state["nlp_reason"] = detected.reason or "Sin motivo específico"
            st.session_state["nlp_radius"] = int(detected.radius_km)
            st.session_state["nlp_location"] = detected.location

        if "nlp_location" not in st.session_state:
            st.session_state["nlp_location"] = detected.location

        with st.container(border=True):
            st.subheader("Dirección")

            gps_result = _GEOLOCATION_COMPONENT(
                key="gps_location",
                data={"label": "Usar mi ubicación GPS"},
                on_coordinates_change=lambda: None,
                on_requested_change=lambda: None,
            )

            coordinates = getattr(gps_result, "coordinates", None)
            if coordinates:
                lat = float(coordinates["lat"])
                lon = float(coordinates["lon"])
                st.session_state["gps_coordinates"] = {"lat": lat, "lon": lon}
                st.session_state["care_origin"] = {"lat": lat, "lon": lon}

            location = st.text_input(
                "Dirección o municipio",
                key="nlp_location",
                placeholder="Ej. Calle Alcalá 1, Madrid",
                label_visibility="collapsed",
            )

        submitted = st.button(
            "Analizar y buscar",
            icon=":material/search:",
            type="primary",
            key="unified_search_submit",
        )

        with st.expander("Filtros detectados y editables", expanded=False):
            tipos_disponibles = sorted({
                tipo
                for tipos in catalog.tipos_por_categoria.values()
                for tipo in tipos
            })

            categorias = st.pills(
                "Categoría",
                catalog.categorias,
                selection_mode="multi",
                key="nlp_categorias",
            )
            titularidades = st.pills(
                "Titularidad",
                ["Público", "Privado"],
                selection_mode="multi",
                key="nlp_titularidades",
            )
            tipos = st.multiselect(
                "Tipo de centro",
                tipos_disponibles,
                key="nlp_tipos",
            )
            municipios = st.multiselect(
                "Municipio",
                catalog.municipios,
                key="nlp_municipios",
            )
            especialidades = st.multiselect(
                "Servicio / especialidad",
                catalog.especialidades,
                key="nlp_especialidades",
            )
            reason_options = ["Sin motivo específico", "Urgencias y Emergencias", *catalog.especialidades]
            reason = st.selectbox(
                "Motivo principal",
                reason_options,
                index=0,
                key="nlp_reason",
            )
            if reason == "Sin motivo específico":
                reason = ""
            radius_km = st.slider(
                "Radio de búsqueda (km)",
                min_value=1,
                max_value=50,
                key="nlp_radius",
            )

            from models.filters import FilterCriteria

            edited = FilterCriteria(
                categorias=tuple(categorias),
                tipos=tuple(tipos),
                municipios=tuple(municipios),
                titularidades=tuple(titularidades),
                especialidades=tuple(especialidades),
                texto=detected.texto,
                location=location,
                reason=reason,
                radius_km=float(radius_km),
            )

        st.button(
            "Limpiar todos los filtros",
            icon=":material/filter_alt_off:",
            on_click=_clear_all_filters,
        )

        return edited, submitted
