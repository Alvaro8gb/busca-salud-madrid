# Centros sanitarios de la Comunidad de Madrid 

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://buscamadridsalud.streamlit.app/)

Aplicación web para buscar centros sanitarios de la Comunidad de Madrid mediante filtros tradicionales y búsquedas en lenguaje natural. Permite localizar centros cercanos, calcular rutas y visualizar los resultados en un mapa claro e interactivo.

## Ejecutar

Con Pipenv:

```bash
pipenv install
pipenv run app
```

También puede ejecutarse directamente:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Funcionalidades actuales

- Buscador en lenguaje natural en primer lugar dentro del panel de búsqueda.
- Detección automática de categoría, titularidad, tipo de centro, municipio, especialidad, motivo y radio de búsqueda.
- Filtros detectados editables.
- Caja de dirección independiente del texto de búsqueda.
- Obtención de la ubicación actual mediante GPS del navegador.
- Las coordenadas GPS no se sustituyen ni se muestran en el campo de texto de dirección.
- Priorización de la ubicación GPS sobre una dirección escrita cuando se realiza la búsqueda.
- Mapa base claro con Carto Positron.
- Marcador triangular azul para representar la ubicación actual del usuario.
- Círculo azul opcional para representar el radio de búsqueda.
- Cálculo de distancia y duración aproximada en coche mediante OSRM.
- Tabla de centros cercanos, ficha de detalle, estadísticas y descarga de resultados.

## Arquitectura MVC

```text
app.py                       Punto de entrada
config.py                    CRS, categorías y colores
data/                        CSV original conservado; no se usa en ejecución
models/
  repository.py              Carga y normaliza datos de los centros
  health_model.py            Catálogo, filtros, búsquedas y estadísticas
  filters.py                 DTOs: FilterCriteria y Catalog
  nlp_parser.py              Parser local de lenguaje natural basado en reglas
  location_service.py        Geocodificación, geocodificación inversa y rutas OSRM
views/
  location_search_view.py    Buscador NLP, dirección GPS y filtros editables
  sidebar_view.py            Filtros laterales
  map_view.py                Mapa pydeck claro, resultados y ubicación actual
  detail_view.py             Ficha del centro seleccionado
  table_view.py              Tabla y descarga CSV
  stats_view.py              KPIs y gráficos
controllers/
  health_controller.py       Coordina vistas, modelo, geolocalización y rutas
```

## Parser de búsquedas

La búsqueda actual utiliza `models/nlp_parser.py`, un parser ligero basado en expresiones regulares, aliases, normalización de texto y coincidencias aproximadas. Funciona sin una API externa y permite inferir filtros conocidos del catálogo sanitario.

## Trabajo futuro

- Sustituir o complementar el parser de NLP basado en reglas por un modelo de lenguaje para interpretar consultas más complejas y variadas.
- Acceder a proveedores de LLM diferentes mediante una librería gateway, de modo que se pueda cambiar de proveedor sin modificar el código de aplicación.
- Definir un contrato estructurado de salida para los filtros extraídos por el LLM, como categoría, titularidad, municipio, especialidad, dirección y radio.
- Mantener una estrategia de fallback al parser local cuando el servicio de LLM no esté disponible.
- Añadir pruebas comparativas entre el parser actual y las respuestas generadas por el LLM.

Posibles capacidades del gateway futuro: selección del proveedor y modelo mediante configuración, clave de API centralizada, control de reintentos y límites de uso, métricas de latencia, registro de costes y validación de respuestas.

## Notas sobre los datos

- Los datos se descargan desde la API CKAN de datos.comunidad.madrid y se cachean durante una hora con `st.cache_data`.
- El recurso tiene una fila por *(centro, servicio)*; se agrupa a una fila por centro.
- La aplicación necesita conexión a Internet para descargar datos, geocodificar direcciones, usar rutas OSRM y cargar el mapa base.
- Coordenadas en UTM ETRS89 huso 30N (EPSG:25830), convertidas a lat/lon con `pyproj`.
- 167 centros sin coordenadas válidas aparecen en la tabla, pero no en el mapa.
- La columna `NIF` se descarta por contener datos personales.
- El archivo no incluye nombre comercial del centro; se identifica por tipo, dirección y número de registro.
