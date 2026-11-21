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
        #st.subheader("Filtros")

        texto = st.text_input(
            "Buscar",
            key=_KEYS["texto"],
            placeholder="Calle, municipio, nº de registro…",
        )

        filter_category, filter_owner = st.columns(2)
        with filter_category:
            categorias = st.pills(
                "Categoría",
                catalog.categorias,
                selection_mode="multi",
                key=_KEYS["categorias"],
            )
        with filter_owner:
            titularidades = st.pills(
                "Titularidad",
                ["Público", "Privado"],
                selection_mode="multi",
                key=_KEYS["titularidades"],
            )

        pool = categorias or catalog.categorias
        tipos_disponibles = sorted(
            {t for c in pool for t in catalog.tipos_por_categoria.get(c, [])}
        )
        st.session_state[_KEYS["tipos"]] = [
            t
            for t in st.session_state.get(_KEYS["tipos"], [])
            if t in tipos_disponibles
        ]

        with st.expander("Filtros opcionales", expanded=False):
            tipos = st.multiselect(
                "Tipo de centro", tipos_disponibles, key=_KEYS["tipos"]
            )
            municipios = st.multiselect(
                "Municipio", catalog.municipios, key=_KEYS["municipios"]
            )
            especialidades = st.multiselect(
                "Servicio / especialidad",
                catalog.especialidades,
                key=_KEYS["especialidades"],
            )

        st.button("Limpiar filtros", on_click=_reset_filters, icon=":material/filter_alt_off:")

        criteria = FilterCriteria(
            categorias=tuple(categorias),
            tipos=tuple(tipos),
            municipios=tuple(municipios),
            titularidades=tuple(titularidades),
            especialidades=tuple(especialidades),
            texto=texto,
        )
        return criteria
