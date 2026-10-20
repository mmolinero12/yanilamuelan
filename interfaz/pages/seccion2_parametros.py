import sys
from pathlib import Path
import streamlit as st
import requests

RAIZ_DIR = Path(__file__).resolve().parent.parent
if str(RAIZ_DIR) not in sys.path:
    sys.path.append(str(RAIZ_DIR))

from theme import PALETTE
from constants import PERFILES, FORMATOS, NIVELES
from client_config import ADAPT_URL, API_TIMEOUT_SECONDS

# Fallback si constants no tiene alguna lista
if not PERFILES:
    PERFILES = [
        "Principiante / Transición de Carrera",
        "Desarrollador Junior / Semi Senior",
        "Líder Técnico / Arquitecto",
        "Gestor / Ejecutivo (No Técnico)",
    ]

FORMATOS_SELECCION = [
    "Flashcards de Memorización",
    "Quiz Interactivo con Justificaciones",
]

NIVELES_DETALLE = ["Básico", "Intermedio", "Avanzado"]


def volver_al_paso_1():
    st.session_state["paso_actual"] = 1


def generar():
    st.session_state["resultado"] = None
    st.session_state.pop("error_generacion", None)
    solicitud = {
        "perfil_destinatario": st.session_state.get("param_perfil", "General"),
        "formato_salida": st.session_state.get("param_formato", FORMATOS_SELECCION[0]),
        "nicho_sector": st.session_state.get("param_nicho", "").strip() or "General",
        "nivel_detalle": st.session_state.get("param_nivel", "Intermedio"),
    }
    st.session_state["solicitud"] = solicitud
    datos = st.session_state.get("archivo_bytes")
    if not datos:
        st.session_state["error_generacion"] = "Carga un documento antes de generar."
        return
    try:
        with st.spinner("Procesando documento, recuperando contexto y consultando Gemini..."):
            resp = requests.post(
                ADAPT_URL, data=solicitud,
                files={"archivo": (st.session_state["documento_titulo"], datos,
                                    "application/octet-stream")},
                timeout=(10, API_TIMEOUT_SECONDS),
            )
        if not resp.ok:
            try:
                detail = resp.json().get("detail", {})
            except ValueError:
                detail = {}
            if isinstance(detail, dict):
                mensaje = detail.get("mensaje", "La API rechazó la solicitud.")
                etapa = detail.get("etapa", "validacion")
                st.session_state["error_generacion"] = f"{etapa}: {mensaje} (HTTP {resp.status_code})"
            else:
                st.session_state["error_generacion"] = f"La API rechazó los datos (HTTP {resp.status_code})."
            return
        resultado = resp.json()
        if not isinstance(resultado, dict) or resultado.get("status") != "exito":
            raise ValueError("Respuesta inesperada de la API.")
        st.session_state["resultado"] = resultado
        st.session_state["paso_actual"] = 3
    except requests.Timeout:
        st.session_state["error_generacion"] = (
            "La API superó el tiempo de espera. Puede seguir procesando el documento; "
            "comprueba el backend antes de reintentar."
        )
    except requests.RequestException:
        st.session_state["error_generacion"] = "No se pudo contactar al backend. Comprueba su dirección y disponibilidad."
    except ValueError:
        st.session_state["error_generacion"] = "El backend devolvió una respuesta inválida."


def render():
    if st.session_state.get("error_generacion"):
        st.error(st.session_state["error_generacion"])
    col_izq, col_centro, col_der = st.columns([0.8, 3.4, 0.8])

    with col_centro:
        with st.container(border=True):
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;">
                    <span style="color: {PALETTE.get('primary', '#0094F0')}; font-weight: bold; font-size: 13px;">PASO 2 DE 3</span>
                    <span style="color: {PALETTE.get('text', '#FFFFFF')}; opacity: 0.5; font-size: 12px;">• Parámetros</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                f"<h3 style='text-align: center; color: {PALETTE.get('accent', '#F59F0A')};'>"
                "Personaliza tu material</h3>",
                unsafe_allow_html=True,
            )

            titulo = st.session_state.get("documento_titulo")
            if titulo:
                st.caption(f"📄 Documento: {titulo}")

            st.selectbox("¿Para quién es el contenido?", PERFILES, key="param_perfil")
            st.selectbox("Formato de salida", FORMATOS_SELECCION, key="param_formato")
            st.text_input(
                "Nicho o sector",
                key="param_nicho",
                placeholder="Ej.: salud, educación, finanzas",
            )
            st.selectbox("Nivel de detalle", NIVELES_DETALLE, key="param_nivel")

            col_a, col_b = st.columns(2)
            with col_a:
                st.button("← Volver", on_click=volver_al_paso_1, use_container_width=True)
            with col_b:
                st.button("Generar", type="primary", on_click=generar, use_container_width=True)


if __name__ == "__main__":
    render()
