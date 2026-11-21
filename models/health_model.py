"""Modelo: reglas de negocio sobre los centros sanitarios (consulta, filtros, estadísticas)."""

from __future__ import annotations

import pandas as pd

from models.filters import Catalog, FilterCriteria
from models.repository import normalize_text


class HealthModel:
    def __init__(self, centers: pd.DataFrame):
        self._centers = centers

    # ----------------------------------------------------------------- consultas
    def catalog(self) -> Catalog:
        c = self._centers
        tipos_por_categoria = {
            cat: sorted(group["tipo"].unique()) for cat, group in c.groupby("categoria")
        }
        especialidades = sorted(c["servicios"].explode().dropna().unique())
        return Catalog(
            categorias=sorted(c["categoria"].unique()),
            tipos_por_categoria=tipos_por_categoria,
            municipios=sorted(c["municipio"].unique()),
            titularidades=sorted(c["titularidad"].unique()),
            especialidades=especialidades,
        )

    def search(self, criteria: FilterCriteria) -> pd.DataFrame:
        df = self._centers
        mask = pd.Series(True, index=df.index)

        if criteria.categorias:
            mask &= df["categoria"].isin(criteria.categorias)
        if criteria.tipos:
            mask &= df["tipo"].isin(criteria.tipos)
        if criteria.municipios:
            mask &= df["municipio"].isin(criteria.municipios)
        if criteria.titularidades:
            mask &= df["titularidad"].isin(criteria.titularidades)
        if criteria.especialidades:
            wanted = set(criteria.especialidades)
            mask &= df["_servicios_set"].map(lambda s: not wanted.isdisjoint(s))
        if criteria.texto.strip():
            mask &= df["_busqueda"].str.contains(
                normalize_text(criteria.texto.strip()), regex=False
            )

        return df[mask]

    def get_center(self, registro: str) -> dict | None:
        match = self._centers[self._centers["registro"] == registro]
        return None if match.empty else match.iloc[0].to_dict()

    # -------------------------------------------------------------- estadísticas
    @staticmethod
    def summarize(df: pd.DataFrame) -> dict:
        return {
            "total": len(df),
            "con_ubicacion": int(df["tiene_ubicacion"].sum()),
            "municipios": int(df["municipio"].nunique()),
            "publicos": int((df["titularidad"] == "Público").sum()),
        }

    @staticmethod
    def breakdowns(df: pd.DataFrame, top: int = 10) -> dict[str, pd.Series]:
        return {
            "Por tipo de centro": df["tipo"].value_counts().head(top),
            "Por municipio": df["municipio"].value_counts().head(top),
            "Por titularidad": df["titularidad"].value_counts(),
            "Servicios más ofertados": df["servicios"]
            .explode()
            .dropna()
            .value_counts()
            .head(top),
        }
