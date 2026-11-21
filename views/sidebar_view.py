"""Vista: barra lateral con los filtros. Solo dibuja widgets y devuelve lo que el usuario eligió."""

from __future__ import annotations

import streamlit as st

from models.filters import Catalog, FilterCriteria

_KEYS = {
    "categorias": "f_categorias",
    "tipos": "f_tipos",
    "municipios": "f_municipios",
    "titularidades": "f_titularidades",
    "especialidades": "f_especialidades",
    "texto": "f_texto",
}


def _reset_filters() -> None:
    for name, key in _KEYS.items():
        if name == "texto":
            st.session_state[key] = ""
        else:
            st.session_state[key] = []


class SidebarView:
    @staticmethod
    def render(catalog: Catalog) -> FilterCriteria:
        st.sidebar.header("Filtros")
        st.sidebar.caption("Si dejas un filtro vacío, se muestran todos los valores.")

        texto = st.sidebar.text_input(
            "Buscar",
            key=_KEYS["texto"],
            placeholder="Calle, municipio, nº de registro…",
        )
        st.sidebar.subheader("Tipo de centro")
        categorias = st.sidebar.multiselect(
            "Categoría", catalog.categorias, key=_KEYS["categorias"]
        )

        # Los tipos disponibles dependen de las categorías elegidas.
        pool = categorias or catalog.categorias
        tipos_disponibles = sorted(
            {t for c in pool for t in catalog.tipos_por_categoria.get(c, [])}
        )
        # Evita que quede seleccionado un tipo que ya no está disponible.
        st.session_state[_KEYS["tipos"]] = [
            t
            for t in st.session_state.get(_KEYS["tipos"], [])
            if t in tipos_disponibles
        ]
        tipos = st.sidebar.multiselect(
            "Tipo de centro", tipos_disponibles, key=_KEYS["tipos"]
        )

        with st.sidebar.expander("Más filtros", expanded=False):
            municipios = st.multiselect(
                "Municipio", catalog.municipios, key=_KEYS["municipios"]
            )
            titularidades = st.multiselect(
                "Titularidad", catalog.titularidades, key=_KEYS["titularidades"]
            )
            especialidades = st.multiselect(
                "Servicio / especialidad",
                catalog.especialidades,
                key=_KEYS["especialidades"],
            )

        st.sidebar.button("Limpiar filtros", on_click=_reset_filters, width="stretch")

        criteria = FilterCriteria(
            categorias=tuple(categorias),
            tipos=tuple(tipos),
            municipios=tuple(municipios),
            titularidades=tuple(titularidades),
            especialidades=tuple(especialidades),
            texto=texto,
        )
        return criteria
