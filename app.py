"""Punto de entrada.  Ejecutar con:  streamlit run app.py"""

import streamlit as st

st.set_page_config(
    page_title="Centros sanitarios de Madrid", page_icon="🏥", layout="wide"
)

from controllers.health_controller import HealthController  # noqa: E402

HealthController().run()
