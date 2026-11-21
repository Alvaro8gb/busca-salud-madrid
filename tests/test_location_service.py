from unittest.mock import Mock, patch

from models.location_service import geocode_location, rank_by_external_route


def test_geocode_location_returns_coordinates():
    response = Mock()
    response.json.return_value = [{
        "lat": "40.4168",
        "lon": "-3.7038",
        "display_name": "Madrid, España",
    }]
    response.raise_for_status.return_value = None

    with patch("models.location_service.requests.get", return_value=response):
        result = geocode_location.__wrapped__("Madrid")

    assert result == (40.4168, -3.7038, "Madrid, España")


def test_rank_by_external_route_orders_by_duration():
    destinations = [
        {"registro": "A", "lat": 40.42, "lon": -3.70},
        {"registro": "B", "lat": 40.45, "lon": -3.68},
    ]
    response = Mock()
    response.json.return_value = {
        "code": "Ok",
        "durations": [[0, 600, 300]],
        "distances": [[0, 8000, 4000]],
    }
    response.raise_for_status.return_value = None

    with patch("models.location_service.requests.get", return_value=response):
        result = rank_by_external_route.__wrapped__(40.41, -3.71, destinations)

    assert [item["registro"] for item in result] == ["B", "A"]
    assert result[0]["duracion_min"] == 5.0
    assert result[0]["distancia_km"] == 4.0


def test_rank_by_external_route_rejects_osrm_error():
    destinations = [{"registro": "A", "lat": 40.42, "lon": -3.70}]
    response = Mock()
    response.json.return_value = {"code": "NoRoute", "message": "Sin ruta"}
    response.raise_for_status.return_value = None

    with patch("models.location_service.requests.get", return_value=response):
        try:
            rank_by_external_route.__wrapped__(40.41, -3.71, destinations)
            assert False, "Expected RuntimeError"
        except RuntimeError as exc:
            assert "Sin ruta" in str(exc)
