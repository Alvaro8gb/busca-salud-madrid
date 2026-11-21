import pandas as pd

from models.filters import FilterCriteria
from models.health_model import HealthModel


def make_centers():
    return pd.DataFrame([
        {
            "registro": "A1",
            "tipo": "Hospital general",
            "categoria": "Hospitales",
            "municipio": "Madrid",
            "titularidad": "Público",
            "servicios": ["Cardiología", "Urgencias y Emergencias"],
            "_servicios_set": frozenset({"Cardiología", "Urgencias y Emergencias"}),
            "_busqueda": "a1 hospital general madrid",
            "tiene_ubicacion": True,
        },
        {
            "registro": "A2",
            "tipo": "Centro de salud",
            "categoria": "Atención primaria",
            "municipio": "Alcorcón",
            "titularidad": "Privado",
            "servicios": ["Pediatría"],
            "_servicios_set": frozenset({"Pediatría"}),
            "_busqueda": "a2 centro de salud alcorcon",
            "tiene_ubicacion": True,
        },
    ])


def test_search_combines_all_filters():
    model = HealthModel(make_centers())
    criteria = FilterCriteria(
        categorias=("Hospitales",),
        municipios=("Madrid",),
        titularidades=("Público",),
        especialidades=("Cardiología",),
    )

    result = model.search(criteria)

    assert list(result["registro"]) == ["A1"]


def test_search_returns_all_with_empty_filters():
    model = HealthModel(make_centers())

    result = model.search(FilterCriteria())

    assert len(result) == 2


def test_find_by_service_matches_substring_and_location():
    model = HealthModel(make_centers())

    result = model.find_by_service("Urgencias")

    assert list(result["registro"]) == ["A1"]


def test_text_search_is_normalized():
    model = HealthModel(make_centers())

    result = model.search(FilterCriteria(texto="alcorcon"))

    assert list(result["registro"]) == ["A2"]
