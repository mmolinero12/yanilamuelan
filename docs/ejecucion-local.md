# Ejecución real en Windows

Ejecutar desde la raíz del repositorio. Cada comando usa su propio entorno.

```powershell
.venv-backend/Scripts/python.exe -m pip install -r backend/requirements.txt
.venv-frontend/Scripts/python.exe -m pip install -r interfaz/requirements.txt
```

La configuración se carga desde el `.env` de la raíz, independientemente del directorio de trabajo.
Las variables existentes del proceso tienen prioridad. `.env.example` enumera los nombres admitidos.
El `.env` real no debe versionarse. Los clientes Gemini mantienen TLS verificado con certificados del sistema.

En una terminal:

```powershell
.venv-backend/Scripts/python.exe -X utf8 -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

En otra terminal:

```powershell
.venv-frontend/Scripts/python.exe -X utf8 -m streamlit run interfaz/app.py
```

`GET /api/v1/health` comprueba el proceso API. El prefijo puede cambiar con `API_PREFIX`.
La URL del backend en Streamlit se configura con `BACKEND_URL`; `API_TIMEOUT_SECONDS` controla su espera.
Tras modificar el `.env`, reiniciar ambos procesos.

## Contrato de adaptación

`POST /api/v1/adapt` ahora recibe `multipart/form-data`, en lugar del JSON anterior:

- `archivo`: archivo original PDF, DOCX, PPTX, TXT o MD.
- `perfil_destinatario`, `formato_salida`, `nicho_sector`, `nivel_detalle`: campos de formulario.

Acepta `Flashcards` y `Quiz`, además de las dos etiquetas correspondientes de la interfaz.
El frontend envía el original sin decodificarlo. El backend valida, guarda sus bytes, extrae el texto,
indexa con el módulo RAG, recupera contexto filtrado por `doc_id`, genera, evalúa y guarda la respuesta.
No hay respuestas simuladas en el flujo de ejecución.

Los originales quedan en `DOCUMENTS_PATH`, con un UUID como prefijo y su extensión original.
La respuesta JSON completa queda en `GENERATED_PATH`. Chroma persiste en `CHROMA_PERSIST_DIR`.
Todas las rutas relativas se resuelven contra la raíz del repositorio.
La respuesta incluye `almacenamiento_local` y `metadatos.doc_id`; no declara una subida a OCI.
`almacenamiento_oci` es opcional para conservar compatibilidad con su contrato anterior.

Un error devuelve HTTP 4xx/5xx con `detail.etapa` y `detail.mensaje`, sin mensajes externos que puedan
contener credenciales. Si Gemini no logra evaluar, la adaptación no se presenta como completa.
El original y cualquier índice ya creado se conservan si una etapa posterior falla; no hay rollback
ni reanudación automática. Reintentar crea una nueva indexación.

## Límites actuales

- Máximo inicial: 10 MiB por archivo (`MAX_UPLOAD_MB`).
- DOCX/PPTX: límite de 50 MiB de contenido descomprimido.
- No incluye OCR ni extracción del texto contenido únicamente en imágenes, gráficos o SmartArt.
- DOCX extrae párrafos y tablas; PPTX extrae cuadros de texto, tablas y grupos de formas.
- Una adaptación simultánea por proceso; usar un solo worker. Las adicionales reciben HTTP 429.
- Los reintentos de embeddings están limitados por `MAX_EMBEDDING_ATTEMPTS`.
- Un timeout del cliente no cancela necesariamente el trabajo del backend.

## Verificación

```powershell
.venv-backend/Scripts/python.exe -m pip install -r backend/requirements-dev.txt
.venv-backend/Scripts/python.exe -m pytest backend/tests evaluacion/tests -q
.venv-backend/Scripts/python.exe -m pytest orquestacion-agentes/tests -q
.venv-frontend/Scripts/python.exe -m unittest discover -s interfaz/tests -v
```

Las pruebas automáticas de integración usan Chroma y almacenamiento reales en directorios temporales;
solo sustituyen las llamadas externas a Gemini. Las pruebas de interfaz verifican el envío multipart
y que los errores no se conviertan en resultados ficticios.

Para consultar acceso a los modelos sin imprimir credenciales:

```powershell
.venv-backend/Scripts/python.exe scripts/check_gemini_models.py
```

La siguiente verificación consume cuota real de Gemini y crea originales, índices y resultados locales:

```powershell
.venv-backend/Scripts/python.exe scripts/verify_real_pipeline.py
```

Para verificar también el cliente Streamlit contra HTTP real, sin abrir un navegador:

```powershell
.venv-backend/Scripts/python.exe scripts/verify_real_pipeline.py --streamlit
```

Esta opción levanta un Uvicorn temporal en un puerto libre y lo cierra al terminar, sin tocar
los servidores existentes. Usa AppTest con el estado producido por la carga de archivo y deja
que Streamlit envíe el multipart real; no sustituye requests, RAG ni Gemini.

Para las dos VMs posteriores: instalar frontend y backend en entornos separados, incluir `shared/`
en el despliegue backend, apuntar `BACKEND_URL` a la VM backend y configurar las tres rutas persistentes
en el volumen montado. Este cambio no configura Nginx, OCI Object Storage ni servicios del sistema.

El envío de archivo y parámetros sigue el contrato multipart de [FastAPI](https://fastapi.tiangolo.com/tutorial/request-forms-and-files/).
