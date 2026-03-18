"""Autenticación simple para la web app de Veta."""

import os
import streamlit as st

from src.web.secrets_helper import get_web_password


def _inject_login_css():
    """Inyecta CSS para la página de login."""
    css_path = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def load_password() -> str:
    """Carga la contraseña desde st.secrets o settings.yaml."""
    return get_web_password()


def check_auth() -> bool:
    """Muestra login si no está autenticado. Retorna True si el usuario está logueado."""
    if st.session_state.get("authenticated"):
        return True

    _inject_login_css()

    # Centrar el formulario con card estilizada
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown('''
        <div class="veta-login-container">
            <div class="veta-login-icon">📊</div>
            <div class="veta-login-title">Veta Strategist AI</div>
            <div class="veta-login-subtitle">Ingresá la contraseña del equipo para continuar</div>
        </div>
        ''', unsafe_allow_html=True)

        password = st.text_input("Contraseña", type="password", key="login_password", label_visibility="collapsed", placeholder="Contraseña del equipo")

        if st.button("Entrar", type="primary", use_container_width=True):
            correct_password = load_password()
            if password == correct_password:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")

    return False


def logout():
    """Cierra la sesión."""
    st.session_state["authenticated"] = False
    st.rerun()
