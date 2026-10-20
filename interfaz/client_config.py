"""Configuración del cliente HTTP, sin importar componentes del backend."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
API_PREFIX = os.getenv("API_PREFIX", "/api/v1").rstrip("/")
ADAPT_URL = f"{BACKEND_URL}{API_PREFIX}/adapt"
API_TIMEOUT_SECONDS = float(os.getenv("API_TIMEOUT_SECONDS", "300"))
