"""Vista: tabla de resultados con descarga."""

from __future__ import annotations

import pandas as pd
import streamlit as st

_COLUMNAS = {
    "registro": "Registro",
    "tipo": "Tipo de centro",
    "categoria": "Categoría",
    "titularidad": "Titularidad",
    "municipio": "Municipio",
    "direccion": "Dirección",
    "codigo_postal": "C.P.",
    "n_servicios": "Nº servicios",
    "servicios": "Servicios",
}


class TableView:
    @staticmethod
    def render(df: pd.DataFrame) -> None:
        tabla = df.head(5)[list(_COLUMNAS)].rename(columns=_COLUMNAS)
        st.dataframe(
            tabla,
            hide_index=True,
            width="stretch",
            height=560,
            column_config={"Servicios": st.column_config.ListColumn("Servicios")},
        )
        descarga = tabla.assign(Servicios=tabla["Servicios"].str.join(" | "))
        st.download_button(
            "Descargar resultados (CSV)",
            descarga.to_csv(index=False, sep=";").encode("utf-8-sig"),
            file_name="centros_filtrados.csv",
            mime="text/csv",
        )
