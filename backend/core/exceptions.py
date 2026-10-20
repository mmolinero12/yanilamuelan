class NuevamenteException(Exception):
    pass


class DocumentError(NuevamenteException):
    pass


class RagError(NuevamenteException):
    pass


class OrchestrationError(NuevamenteException):
    pass


class EvaluationError(NuevamenteException):
    pass


class StorageError(NuevamenteException):
    pass


class PipelineError(NuevamenteException):
    def __init__(self, etapa: str, mensaje: str, status_code: int = 502):
        super().__init__(mensaje)
        self.etapa = etapa
        self.status_code = status_code
