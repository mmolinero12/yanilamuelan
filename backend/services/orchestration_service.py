from shared.module_loader import load_module


class OrchestrationService:
    def generar(self, **parametros):
        return load_module("orquestacion_agentes", "main").generar_contenido_adaptado(**parametros)
