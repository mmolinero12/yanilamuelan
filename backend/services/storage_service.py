"""Persiste el original intacto y la respuesta completa en disco local."""
import json
import re
from pathlib import Path
from uuid import uuid4
from backend.core.config import settings
from shared.config import project_path


class StorageService:
    def guardar_original(self, nombre: str, datos: bytes) -> tuple[str, Path]:
        identificador = uuid4().hex
        nombre = nombre.replace("\\", "/").rsplit("/", 1)[-1]
        nombre = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", nombre).strip(" .")
        # El prefijo evita también nombres reservados de Windows como CON.docx.
        destino = project_path(settings.documents_path) / f"{identificador}_{nombre}"
        destino.parent.mkdir(parents=True, exist_ok=True)
        with destino.open("xb") as archivo:
            archivo.write(datos)
        return identificador, destino

    def ruta_resultado(self, identificador: str) -> Path:
        return project_path(settings.generated_path) / f"{identificador}.json"

    def guardar_resultado(self, destino: Path, respuesta) -> None:
        destino.parent.mkdir(parents=True, exist_ok=True)
        temporal = destino.with_suffix(".json.tmp")
        try:
            with temporal.open("x", encoding="utf-8") as archivo:
                json.dump(respuesta.model_dump(mode="json", exclude_none=True), archivo,
                          ensure_ascii=False, indent=2)
            temporal.replace(destino)
        finally:
            temporal.unlink(missing_ok=True)
