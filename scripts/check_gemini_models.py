"""Consulta acceso a modelos sin mostrar credenciales ni respuestas de error externas."""
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from shared.config import ENV_FILE
from shared.gemini_transport import gemini_client_args
from google import genai


def main():
    keys = [key.strip() for key in os.getenv("GEMINI_API_KEYS", "").split(",") if key.strip()]
    keys += [os.getenv(name, "").strip() for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY")]
    keys = list(dict.fromkeys(key for key in keys if key))
    if not keys:
        print("No hay claves configuradas.")
        return 1
    try:
        with genai.Client(api_key=keys[0], http_options={
            "timeout": 20000, "client_args": gemini_client_args()
        }) as client:
            available = {model.name.removeprefix("models/"): model.supported_actions
                         for model in client.models.list()}
    except Exception as error:
        print("No se pudo consultar el catálogo:", type(error).__name__)
        cause = error
        while cause is not None:
            print("Causa:", type(cause).__name__, "errno:", getattr(cause, "errno", None),
                  "TLS:", getattr(cause, "verify_code", None))
            description = str(cause).lower()
            print("Diagnóstico:", ", ".join(word for word in (
                "certificate", "ssl", "10013", "getaddrinfo", "refused", "proxy", "timed out"
            ) if word in description) or "sin categoría conocida")
            cause = cause.__cause__
        return 1
    for variable in ("GEMINI_MODEL", "GEMINI_MODEL_RESPALDO", "MODELO_EMBEDDINGS"):
        name = os.getenv(variable, "").removeprefix("models/")
        print(variable, name, "DISPONIBLE" if name in available else "NO DISPONIBLE")
    print("Modelos Flash disponibles:", ", ".join(name for name, actions in available.items()
          if "flash" in name and "generateContent" in (actions or [])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
