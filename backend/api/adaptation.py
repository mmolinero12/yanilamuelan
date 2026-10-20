from fastapi import APIRouter, File, Form, UploadFile

from backend.services.adaptation_service import adaptar_archivo
from shared.contratos import RespuestaFinal

router = APIRouter(
    prefix="/adapt",
    tags=["Adaptación"],
)


@router.post("", response_model=RespuestaFinal, response_model_exclude_none=True)
def adapt(
    archivo: UploadFile = File(...),
    perfil_destinatario: str = Form(..., min_length=1),
    formato_salida: str = Form(..., min_length=1),
    nicho_sector: str = Form(..., min_length=1),
    nivel_detalle: str = Form(..., min_length=1),
):
    try:
        return adaptar_archivo(archivo, perfil_destinatario, formato_salida,
                               nicho_sector, nivel_detalle)
    finally:
        archivo.file.close()
