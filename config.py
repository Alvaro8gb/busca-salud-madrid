"""Configuración global de la aplicación."""

# Sistema de coordenadas: el CSV usa UTM ETRS89 huso 30N; el mapa necesita WGS84.
CRS_ORIGEN = "EPSG:25830"
CRS_DESTINO = "EPSG:4326"

# Caja envolvente aproximada de la Comunidad de Madrid (descarta coordenadas erróneas).
BBOX_LAT = (39.8, 41.3)
BBOX_LON = (-5.2, -3.0)

# Agrupación de los 24 tipos de centro en categorías legibles (para filtrar y colorear).
CATEGORIA_POR_TIPO = {
    "Hospital general": "Hospitales",
    "Hospital especializado": "Hospitales",
    "Hospital de media y larga estancia": "Hospitales",
    "Hospital de salud mental y tratamiento de toxicomanías": "Hospitales",
    "Otros centros con internamiento": "Hospitales",
    "Centro de salud": "Atención primaria",
    "Consultorio de atención primaria": "Atención primaria",
    "Clínica dental": "Clínicas dentales",
    "Consulta médica": "Consultas",
    "Consulta de otros profesionales sanitarios": "Consultas",
    "Centro de salud mental": "Centros especializados",
    "Centro de diagnóstico": "Centros especializados",
    "Centro de diálisis": "Centros especializados",
    "Centro de cirugía mayor ambulatoria": "Centros especializados",
    "Centro de reproducción humana asistida": "Centros especializados",
    "Centro de interrupción voluntaria del embarazo": "Centros especializados",
    "Centro de reconocimiento": "Centros especializados",
    "Centro de transfusión": "Centros especializados",
    "Banco de tejidos": "Centros especializados",
    "Otros centros especializados": "Centros especializados",
    "Centro Polivalente": "Centros especializados",
}
CATEGORIA_POR_DEFECTO = "Otros"

# Color RGB por categoría (lo usa la vista del mapa).
COLOR_POR_CATEGORIA = {
    "Hospitales": [214, 39, 40],
    "Atención primaria": [31, 119, 180],
    "Clínicas dentales": [44, 160, 44],
    "Consultas": [255, 127, 14],
    "Centros especializados": [148, 103, 189],
    "Otros": [127, 127, 127],
}

# Dependencia patrimonial considerada pública.
TITULARIDAD_PUBLICA = {
    "Servicio Madrileño de Salud",
    "Municipal",
    "Comunidad Autónoma",
    "Otros Administración Central",
    "Ministerio de Justicia",
}
