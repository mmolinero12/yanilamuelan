from shared.module_loader import load_module


class RagService:
    def indexar(self, titulo: str, contenido: str) -> str:
        return load_module("ingesta_rag", "services.ingestion").indexar_documento(titulo, contenido)

    def buscar(self, doc_id: str, query: str, top_k: int = 5):
        return load_module("ingesta_rag", "services.retrieving_service").buscar_contexto(doc_id, query, top_k)
