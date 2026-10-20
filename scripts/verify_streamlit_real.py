"""Ejecutar con el entorno frontend y un backend real ya disponible."""
import argparse
from pathlib import Path

from streamlit.testing.v1 import AppTest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("archivo", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    app = AppTest.from_file(str(root / "interfaz" / "app.py"), default_timeout=360)
    # AppTest no implementa la carga interactiva de file_uploader.
    # Se introduce exactamente el estado que produce el callback de carga.
    app.session_state["paso_actual"] = 2
    app.session_state["archivo_bytes"] = args.archivo.read_bytes()
    app.session_state["documento_titulo"] = args.archivo.name
    app.run()
    app.button[-1].click().run(timeout=360)
    if len(app.exception) or app.session_state["paso_actual"] != 3:
        print("Streamlit FALLO:", app.session_state["error_generacion"]
              if "error_generacion" in app.session_state else "Error de ejecución")
        return 1
    body = app.session_state["resultado"]
    assert body["metadatos"]["doc_id"]
    assert body["almacenamiento_local"]["status_guardado"] == "guardado"
    assert body["evaluacion_calidad"]["claridad_pedagogica"] != "No evaluada"
    assert Path(body["almacenamiento_local"]["documento_original"]).read_bytes() == args.archivo.read_bytes()
    print("Streamlit HTTP real OK", "doc_id=" + body["metadatos"]["doc_id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
