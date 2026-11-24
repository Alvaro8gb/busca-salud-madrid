import pytest

from models.filters import Catalog
from models.nlp_parser import parse_search


@pytest.fixture
def catalog():
    return Catalog(
        categorias=["Hospitales", "Atención primaria", "Clínicas dentales"],
        tipos_por_categoria={
            "Hospitales": ["Hospital general", "Hospital especializado"],
            "Atención primaria": ["Centro de salud"],
        },
        municipios=["Madrid", "Alcorcón", "Majadahonda"],
        titularidades=["Público", "Privado"],
        especialidades=["Cardiología", "Pediatría", "Urgencias y Emergencias"],
    )


def test_parse_public_cardio_in_madrid(catalog):
    result = parse_search(
        "Necesito cardiología pública en Madrid con un radio de 10 km",
        catalog,
    )

    assert "Público" in result.titularidades
    assert "Madrid" in result.municipios
    assert "Cardiología" in result.especialidades
    assert result.reason == "Cardiología"
    assert result.texto == ""
    assert result.location == "Madrid"
    assert result.radius_km == 10


def test_unrecognized_query_terms_are_kept_for_text_search(catalog):
    result = parse_search("Busco un centro veterinario en Madrid", catalog)

    assert "Madrid" in result.municipios
    assert result.texto == "centro veterinario"


def test_parse_private_municipality_and_distance(catalog):
    result = parse_search(
        "Centro privado de pediatría cerca de Alcorcón radio 5 km",
        catalog,
    )

    assert "Privado" in result.titularidades
    assert "Alcorcón" in result.municipios
    assert "Pediatría" in result.especialidades
    assert result.location == "Alcorcón"
    assert result.radius_km == 5


def test_parse_meters_as_kilometers(catalog):
    result = parse_search("Urgencias a menos de 3000 metros en Madrid", catalog)

    assert "Madrid" in result.municipios
    assert "Urgencias y Emergencias" in result.especialidades
    assert result.radius_km == 3


@pytest.mark.parametrize(
    ("query", "expected_service"),
    [
        ("Necesito un pediatra para niños", "Pediatría"),
        ("Busco atención para niños pequeños", "Pediatría"),
        ("Pediatra2 cerca de Madrid", "Pediatría"),
        ("Urgencias para un accidente", "Urgencias y Emergencias"),
        ("Me duele el corazón", "Cardiología"),
    ],
)
def test_pediatric_and_common_aliases(catalog, query, expected_service):
    result = parse_search(query, catalog)

    assert expected_service in result.especialidades
    assert result.reason == expected_service


def test_empty_query_returns_no_filters(catalog):
    result = parse_search("", catalog)

    assert result.categorias == ()
    assert result.tipos == ()
    assert result.municipios == ()
    assert result.titularidades == ()
    assert result.especialidades == ()
    assert result.location == ""
    assert result.radius_km == 10


@pytest.mark.parametrize(
    ("query", "field", "expected"),
    [
        ("hospitales en Madrid", "categorias", "Hospitales"),
        ("hospital general en Madrid", "tipos", "Hospital general"),
        ("clínica dental pública en Madrid", "titularidades", "Público"),
        ("urgencias pediátricas en Madrid", "especialidades", "Pediatría"),
    ],
)
def test_extracted_catalog_filters_do_not_leak_into_free_text(catalog, query, field, expected):
    result = parse_search(query, catalog)

    assert expected in getattr(result, field)
    assert result.texto == ""


def test_municipality_requires_word_boundaries(catalog):
    result = parse_search("Busco cardiología en Madridista", catalog)

    assert result.municipios == ()
    assert "Madridista" in result.texto
