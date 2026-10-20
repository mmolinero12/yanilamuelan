from evaluacion.services.evaluador import evaluar_contenido


class EvaluationService:
    def evaluar(self, contenido, contexto, perfil_destinatario, formato_salida):
        return evaluar_contenido(contenido_generado=contenido, contexto=contexto,
                                 perfil_destinatario=perfil_destinatario, formato_salida=formato_salida)
