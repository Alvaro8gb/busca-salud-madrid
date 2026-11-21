"""Repositorio: consulta la API, limpia y devuelve un registro por centro."""

from __future__ import annotations

import json
from urllib.parse import urlencode
from urllib.request import urlopen

import numpy as np
import pandas as pd
from pyproj import Transformer

import config

API_URL = "https://datos.comunidad.madrid/api/3/action/datastore_search"
RESOURCE_ID = "2948b4da-8b39-42b7-b667-779a5284f39d"
PAGE_SIZE = 1000

# El CSV original tiene erratas en los nombres de columna; se normalizan aquí.
COLUMNAS = {
    "centro_nro_registro": "registro",
    "centro_tipo": "tipo",
    "dependecia_funcional": "dependencia_funcional",
    "dependecia_patrimonial": "dependencia_patrimonial",
    "oferta_asistecial": "servicio",
    "municipio_nombre": "municipio",
    "direccion_vial_tipo": "via_tipo",
    "direccion_vial_nombre": "via_nombre",
    "direccion_vial_nro": "via_numero",
    "direccion_informacon_adicional": "direccion_extra",
    "direccion_codigo_postal": "codigo_postal",
    "localizacion_coordenada_x": "utm_x",
    "localizacion_coordenada_y": "utm_y",
}


class HealthCenterRepository:
    def load_centers(self) -> pd.DataFrame:
        raw = pd.DataFrame(self._load_records()).drop(columns=["_id", "rank"], errors="ignore")
        # Se descarta la columna NIF a propósito: contiene datos personales.
        raw = raw.rename(columns=COLUMNAS).drop(columns=["NIF"], errors="ignore")
        raw = raw.astype("string").apply(lambda col: col.str.strip()).replace("", pd.NA)

        # El CSV trae una fila por (centro, servicio): se agrupa a un registro por centro.
        grouped = raw.groupby("registro", sort=False)
        centers = grouped.first().drop(columns=["servicio"])
        centers["servicios"] = grouped["servicio"].agg(
            lambda s: sorted(set(s.dropna()))
        )
        centers = centers.reset_index()
        centers["n_servicios"] = centers["servicios"].str.len()

        centers = self._add_coordinates(centers)
        centers = self._add_derived_fields(centers)
        return centers

    @staticmethod
    def _load_records() -> list[dict]:
        records = []
        offset = 0
        total = None

        while total is None or offset < total:
            query = urlencode(
                {"resource_id": RESOURCE_ID, "limit": PAGE_SIZE, "offset": offset}
            )
            with urlopen(f"{API_URL}?{query}", timeout=30) as response:
                payload = json.load(response)

            if not payload.get("success"):
                raise RuntimeError("La API de datos de Madrid devolvió una respuesta fallida.")

            result = payload.get("result", {})
            page = result.get("records", [])
            if total is None:
                total = result.get("total")
                if not isinstance(total, int):
                    raise ValueError("La API no devolvió el total de registros esperado.")

            if not page and offset < total:
                raise RuntimeError("La API devolvió una página vacía antes de completar los datos.")

            records.extend(page)
            offset += len(page)

        if not records:
            raise RuntimeError("La API no devolvió centros sanitarios.")

        return records

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _add_coordinates(df: pd.DataFrame) -> pd.DataFrame:
        x = pd.to_numeric(df["utm_x"], errors="coerce").to_numpy(dtype=float)
        y = pd.to_numeric(df["utm_y"], errors="coerce").to_numpy(dtype=float)
        valid = np.isfinite(x) & np.isfinite(y) & (x > 0) & (y > 0)

        lon = np.full(len(df), np.nan)
        lat = np.full(len(df), np.nan)
        transformer = Transformer.from_crs(
            config.CRS_ORIGEN, config.CRS_DESTINO, always_xy=True
        )
        lon[valid], lat[valid] = transformer.transform(x[valid], y[valid])

        (lat_min, lat_max), (lon_min, lon_max) = config.BBOX_LAT, config.BBOX_LON
        inside = (
            (lat >= lat_min) & (lat <= lat_max) & (lon >= lon_min) & (lon <= lon_max)
        )
        lat[~inside] = np.nan
        lon[~inside] = np.nan

        df["lat"], df["lon"] = lat, lon
        df["tiene_ubicacion"] = inside
        return df.drop(columns=["utm_x", "utm_y"])

    @staticmethod
    def _add_derived_fields(df: pd.DataFrame) -> pd.DataFrame:
        df["categoria"] = (
            df["tipo"]
            .map(config.CATEGORIA_POR_TIPO)
            .fillna(config.CATEGORIA_POR_DEFECTO)
        )

        df["titularidad"] = np.where(
            df["dependencia_patrimonial"].isna(),
            "Sin dato",
            np.where(
                df["dependencia_patrimonial"].isin(config.TITULARIDAD_PUBLICA),
                "Público",
                "Privado",
            ),
        )

        via = (
            df["via_tipo"].fillna("").str.capitalize()
            + " "
            + df["via_nombre"].fillna("")
        ).str.strip()
        numero = df["via_numero"].fillna("")
        df["direccion"] = [f"{v}, {n}" if n else v for v, n in zip(via, numero)]
        df["direccion"] = df["direccion"].replace("", "Dirección no disponible")
        df["municipio"] = df["municipio"].fillna("Sin dato")
        df = df.drop(columns=["via_tipo", "via_nombre", "via_numero"])

        # Columnas auxiliares (prefijo _) para acelerar las búsquedas.
        df["_servicios_set"] = df["servicios"].map(frozenset)
        df["_busqueda"] = (
            df[["registro", "tipo", "municipio", "direccion"]]
            .fillna("")
            .agg(" ".join, axis=1)
        ).map(normalize_text)
        return df


def normalize_text(text: str) -> str:
    """Minúsculas y sin acentos, para búsquedas tolerantes."""
    import unicodedata

    decomposed = unicodedata.normalize("NFD", str(text).lower())
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
