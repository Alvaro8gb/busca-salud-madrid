"""Punto de entrada.  Ejecutar con:  streamlit run app.py"""

import streamlit as st

st.set_page_config(
    page_title="BuscaSalud CM", page_icon="🏥", layout="centered"
)

st.logo("assests/logo.png", size="large")

from controllers.health_controller import HealthController  # noqa: E402

HealthController().run()
