"""Verifica que Streamlit envíe bytes y no fabrique resultados ante errores."""
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


class ClientTests(unittest.TestCase):
    def preparar(self):
        app = AppTest.from_file(str(APP))
        app.session_state["paso_actual"] = 2
        app.session_state["archivo_bytes"] = b"bytes originales de documento"
        app.session_state["documento_titulo"] = "original.docx"
        app.run()
        self.assertEqual(len(app.exception), 0)
        return app

    def test_error_http_permanece_en_parametros_sin_resultado(self):
        app = self.preparar()
        response = Mock(ok=False, status_code=502)
        response.json.return_value = {"detail": {"etapa": "generacion", "mensaje": "Sin cuota"}}
        with patch("requests.post", return_value=response) as post:
            app.button[-1].click().run()
        self.assertEqual(app.session_state["paso_actual"], 2)
        self.assertIsNone(app.session_state["resultado"])
        self.assertIn("Sin cuota", app.error[0].value)
        self.assertEqual(post.call_args.kwargs["files"]["archivo"][1], b"bytes originales de documento")
        self.assertNotIn("json", post.call_args.kwargs)

    def test_error_de_red_no_genera_contenido(self):
        import requests
        app = self.preparar()
        with patch("requests.post", side_effect=requests.ConnectionError):
            app.button[-1].click().run()
        self.assertIsNone(app.session_state["resultado"])
        self.assertEqual(len(app.error), 1)
        self.assertEqual(len(app.exception), 0)

    def test_resultado_real_se_muestra_con_almacenamiento_local(self):
        app = self.preparar()
        response = Mock(ok=True)
        response.json.return_value = {
            "status": "exito", "metadatos": {"formato_generado": "Flashcards de Memorización",
                                             "doc_id": "documento-real"},
            "contenido_adaptado": {"titulo": "Resultado API", "items": [{"frente": "VCN", "dorso": "Red"}]},
            "evaluacion_calidad": {"anclaje_fuente_score": 1.0, "claridad_pedagogica": "Alta"},
            "almacenamiento_local": {"documento_original": "original.docx", "resultado_generado": "resultado.json"},
        }
        with patch("requests.post", return_value=response):
            app.button[-1].click().run()
        self.assertEqual(app.session_state["paso_actual"], 3)
        self.assertEqual(len(app.exception), 0)
        self.assertIn("localmente", app.success[0].value)


if __name__ == "__main__":
    unittest.main()
