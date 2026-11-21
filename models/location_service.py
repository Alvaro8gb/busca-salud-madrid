"""Servicios externos de geocodificación y rutas."""

from __future__ import annotations

import streamlit as st
import pandas as pd
import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"
OSRM_TABLE_URL = "https://router.project-osrm.org/table/v1/driving"


@st.cache_data(ttl=86400, max_entries=200)
def geocode_location(address: str) -> tuple[float, float, str] | None:
    """Convierte una dirección o municipio en coordenadas mediante Nominatim."""
    query = f"{address.strip()}, Comunidad de Madrid, España"
    response = requests.get(
        NOMINATIM_URL,
        params={
            "q": query,
            "format": "jsonv2",
            "limit": 1,
            "addressdetails": 1,
            "countrycodes": "es",
            "bounded": 1,
            "viewbox": "-4.58,41.25,-3.05,39.78",
        },
        headers={"User-Agent": "busca-salud-madrid/1.0"},
        timeout=15,
    )
    response.raise_for_status()
    matches = response.json()
    if not matches:
        return None

    match = matches[0]
    return float(match["lat"]), float(match["lon"]), match["display_name"]


@st.cache_data(ttl=86400, max_entries=200)
def reverse_geocode_location(lat: float, lon: float) -> str | None:
    """Convierte coordenadas GPS en una dirección legible."""
    response = requests.get(
        NOMINATIM_REVERSE_URL,
        params={
            "lat": lat,
            "lon": lon,
            "format": "jsonv2",
            "addressdetails": 1,
            "zoom": 18,
        },
        headers={"User-Agent": "busca-salud-madrid/1.0"},
        timeout=15,
    )
    response.raise_for_status()
    result = response.json()
    return result.get("display_name")


@st.cache_data(ttl=3600, max_entries=50)
def rank_by_external_route(
    origin_lat: float,
    origin_lon: float,
    destinations: list[dict],
) -> list[dict]:
    """Ordena destinos por duración de viaje calculada por OSRM."""
    if not destinations:
        return []

    points = [(origin_lon, origin_lat)] + [
        (float(center["lon"]), float(center["lat"])) for center in destinations
    ]
    coordinates = ";".join(f"{lon:.6f},{lat:.6f}" for lon, lat in points)

    response = requests.get(
        f"{OSRM_TABLE_URL}/{coordinates}",
        params={"sources": 0, "annotations": "duration,distance"},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("code") != "Ok":
        raise RuntimeError(payload.get("message", "OSRM no pudo calcular las rutas."))

    durations = payload["durations"][0]
    distances = payload["distances"][0]

    ranked = []
    for index, center in enumerate(destinations, start=1):
        duration = durations[index]
        distance = distances[index]
        if duration is None or distance is None:
            continue
        item = dict(center)
        item["duracion_min"] = round(duration / 60, 1)
        item["distancia_km"] = round(distance / 1000, 1)
        ranked.append(item)

    ranked.sort(key=lambda center: center["duracion_min"])
    return ranked
