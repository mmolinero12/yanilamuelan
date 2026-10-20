"""Coordina exclusivamente implementaciones reales del flujo de adaptación."""
import logging
from pathlib import Path
from threading import Lock
from pydantic import ValidationError

from backend.core.config import settings
from backend.core.exceptions import PipelineError
from backend.schemas.request import AdaptacionRequest
from backend.services.extraction_service import SUPPORTED_EXTENSIONS, extraer_texto
from backend.services.storage_service import StorageService
from backend.services.rag_service import RagService
from backend.services.orchestration_service import OrchestrationService
from backend.services.evaluation_service import EvaluationService
from shared.contratos import AlmacenamientoLocal, RespuestaFinal

logger = logging.getLogger(__name__)
_pipeline_lock = Lock()
FORMATOS = {
    "Flashcards de Memorización": "Flashcards",
    "Quiz Interactivo con Justificaciones": "Quiz",
    "Flashcards": "Flashcards", "Quiz": "Quiz",
}
ETIQUETAS = {"Flashcards": "Flashcards de Memorización", "Quiz": "Quiz Interactivo con Justificaciones"}


def adaptar_archivo(archivo, perfil_destinatario, formato_salida, nicho_sector, nivel_detalle):
    nombre = (archivo.filename or "").replace("\\", "/").rsplit("/", 1)[-1]
    if Path(nombre).suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise PipelineError("validacion", "Formato admitido: PDF, DOCX, PPTX, TXT o MD.", 415)
    formato = FORMATOS.get(formato_salida.strip())
    if not formato:
        raise PipelineError("validacion", "Selecciona Flashcards o Quiz.", 422)
    if not all(value.strip() for value in (perfil_destinatario, nicho_sector, nivel_detalle)):
        raise PipelineError("validacion", "Los parámetros no pueden estar vacíos.", 422)
    limite = settings.max_upload_mb * 1024 * 1024
    datos = archivo.file.read(limite + 1)
    if not datos or len(datos) > limite:
        raise PipelineError("validacion", "El archivo está vacío o supera el tamaño permitido.", 413)
    if not _pipeline_lock.acquire(blocking=False):
        raise PipelineError("ocupado", "Hay otra adaptación en curso. Intenta de nuevo al terminar.", 429)
    etapa = "almacenamiento_original"
    try:
        storage = StorageService()
        identificador, original = storage.guardar_original(nombre, datos)
        del datos
        etapa = "extraccion"
        texto = extraer_texto(original)
        request = AdaptacionRequest(
            documento_titulo=nombre, documento_contenido=texto,
            perfil_destinatario=perfil_destinatario, formato_salida=formato,
            nicho_sector=nicho_sector, nivel_detalle=nivel_detalle,
        )
        etapa = "indexacion"
        rag = RagService()
        doc_id = rag.indexar(request.documento_titulo, request.documento_contenido)
        etapa = "recuperacion"
        contexto = rag.buscar(doc_id, request.documento_titulo, top_k=settings.top_k)
        if not contexto:
            raise PipelineError(etapa, "ChromaDB no devolvió contexto para el documento.")
        etapa = "generacion"
        contenido = OrchestrationService().generar(
            documento_titulo=request.documento_titulo, contexto=contexto,
            perfil_destinatario=request.perfil_destinatario, formato_salida=formato,
            nicho_sector=request.nicho_sector, nivel_detalle=request.nivel_detalle,
        )
        etapa = "evaluacion"
        evaluacion = EvaluationService().evaluar(
            contenido, contexto, request.perfil_destinatario, formato
        )
        if evaluacion.claridad_pedagogica == "No evaluada":
            raise PipelineError(etapa, "Gemini no pudo completar la evaluación. "
                                "Comprueba los modelos configurados y la cuota disponible.")
        etapa = "almacenamiento_resultado"
        destino = storage.ruta_resultado(identificador)
        respuesta = RespuestaFinal(
            status="exito",
            metadatos={
                "doc_id": doc_id, "perfil_aplicado": request.perfil_destinatario,
                "formato_generado": ETIQUETAS[formato],
                "tiempo_estimado_estudio_minutos": contenido.tiempo_estimado_estudio_minutos,
                "conceptos_clave": contenido.conceptos_clave,
                "caracteres_extraidos": len(texto), "fragmentos_recuperados": len(contexto),
            },
            contenido_adaptado=contenido, evaluacion_calidad=evaluacion,
            almacenamiento_local=AlmacenamientoLocal(
                documento_original=str(original), resultado_generado=str(destino),
                status_guardado="guardado",
            ),
        )
        storage.guardar_resultado(destino, respuesta)
        logger.info("Adaptación completada: doc_id=%s", doc_id)
        return respuesta
    except PipelineError:
        raise
    except ValidationError as error:
        raise PipelineError(etapa, "Los datos no cumplen el contrato de adaptación.",
                            422 if etapa == "extraccion" else 502) from error
    except Exception as error:
        # Los mensajes externos pueden incluir credenciales: no devolverlos ni registrarlos.
        logger.error("Fallo en etapa %s (%s)", etapa, type(error).__name__)
        mensaje = ("No se pudo completar esta etapa. Revisa la configuración y las dependencias. "
                   "Para Gemini, verifica el acceso al modelo y la cuota disponible.")
        raise PipelineError(etapa, mensaje, 500 if etapa.startswith("almacenamiento") else 502) from error
    finally:
        _pipeline_lock.release()
