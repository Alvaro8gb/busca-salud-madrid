# Centros sanitarios de la Comunidad de Madrid (Streamlit + MVC)

## Ejecutar
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Arquitectura MVC
```
app.py                       Punto de entrada
config.py                    CRS, categorías y colores
data/                        CSV original conservado; no se usa en ejecución
models/                      MODELO  (sin dependencias de Streamlit)
  repository.py              Consulta la API CKAN, limpia, agrupa a 1 fila por centro, UTM -> WGS84
  health_model.py            Reglas de negocio: catálogo, búsqueda/filtros, estadísticas
  filters.py                 DTOs: FilterCriteria y Catalog
views/                       VISTAS  (solo dibujan; no contienen lógica de negocio)
  sidebar_view.py            Filtros
  map_view.py                Mapa pydeck interactivo con puntos
  detail_view.py             Ficha del centro seleccionado
  table_view.py              Tabla + descarga CSV
  stats_view.py              KPIs y gráficos
controllers/
  health_controller.py       CONTROLADOR: lee filtros de la vista -> consulta al modelo -> pinta vistas
```

## Notas sobre los datos
- Los datos se descargan desde la API CKAN de datos.comunidad.madrid y se cachean durante una hora con `st.cache_data`.
- El recurso tiene una fila por *(centro, servicio)*; se agrupa a una fila por centro.
- La aplicación necesita conexión a Internet para la primera descarga y cuando caduca la caché.
- Coordenadas en UTM ETRS89 huso 30N (EPSG:25830), convertidas a lat/lon con `pyproj`.
- 167 centros sin coordenadas válidas: aparecen en la tabla, no en el mapa.
- La columna `NIF` se descarta (contiene datos personales).
- El archivo no incluye nombre comercial del centro; se identifica por tipo, dirección y nº de registro.
