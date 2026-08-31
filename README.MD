# GM-COMPONENTS EV3 - Observabilidad sobre Agentes IA

Proyecto académico desarrollado como continuación de las Evaluaciones Parciales 1 y 2 para la asignatura **Ingeniería de Soluciones con IA (ISY0101)**.

La EV1 implementó FAQ con RAG, recomendación inteligente, backend Node/Express y frontend Angular/Ionic.
La EV2 agregó una capa de agentes con LangChain sobre EV1.
La EV3 agrega observabilidad completa sobre los agentes de EV2 sin modificar su funcionamiento.

---

## 1. Qué se implementó en EV3

La EV3 incorpora un módulo independiente de observabilidad:

```text
ev3_observability/
```

Este módulo implementa:

- `metrics.py`: calcula precisión, consistencia y registra latencia por ejecución.
- `traceability.py`: escribe y lee trazas en formato JSONL.
- `analyzer.py`: analiza trazas y genera hallazgos técnicos.
- `recommendations.py`: genera recomendaciones por área basadas en métricas.
- `security.py`: valida inputs con patrones bloqueados y sanitización de logs.
- `dashboard.py`: dashboard standalone en Streamlit con gráficos Altair.

Se agregaron además:

- `agente/ev3_bridge.py`: carga los módulos EV3 con importlib desde FastAPI.
- `agente/ev3_api.py`: expone los endpoints EV3 en FastAPI.
- Tab EV3 en el frontend Angular con dashboard inline, gauges, barras, trazas, recomendaciones y validador de seguridad interactivo.

---

## 2. Arquitectura EV3

```text
Frontend Angular/Ionic (tab EV3)
  -> groq-proxy Node/Express (/api/ev3/*)
    -> FastAPI Python EV2 (/ev3/*)
      -> ev3_bridge.py
        -> metrics.py
        -> traceability.py (JSONL)
        -> analyzer.py
        -> recommendations.py
        -> security.py

Streamlit (dashboard.py)
  -> Lee directo desde logs/ev3_agent_traces.jsonl
  -> Independiente de FastAPI
```

---

## 3. Estructura principal

```text
.
|-- src/
|   |-- app/
|   |   |-- ia-hub/
|   |   |-- models/
|   |   |   |-- ev3-observability.models.ts
|   |   `-- services/
|   |       |-- ev3-observability.service.ts
|-- groq-proxy/
|   |-- routes/
|   |   |-- ev3.route.js
|   |-- services/
|   |   |-- ev3.service.js
|   `-- server.js
|-- agente/
|   |-- ev3_bridge.py
|   |-- ev3_api.py
|   |-- app.py
|   `-- requirements.txt
|-- ev3_observability/
|   |-- metrics.py
|   |-- traceability.py
|   |-- analyzer.py
|   |-- recommendations.py
|   |-- security.py
|   |-- dashboard.py
|   `-- logs/
|       `-- ev3_agent_traces.jsonl
|-- instalar_dependencias_ev2.bat
|-- iniciar_proyecto_completo_ev2.bat
|-- iniciar_consola_agentes_ev2.bat
`-- README.MD
```

---

## 4. Requisitos

- Node.js 18 o superior.
- npm.
- Python 3.11 disponible como `py -3.11`.
- Conexión a internet.
- Claves válidas para Groq, Voyage AI y MongoDB Atlas.
- Streamlit instalado en el entorno virtual (lo instala automáticamente el bat).

---

## 5. Variables de entorno

Crear el archivo:

```text
groq-proxy/.env
```

Basarse en:

```text
groq-proxy/.env.example
```

Ejemplo:

```env
PORT=8787

GROQ_API_KEY=YOUR_GROQ_API_KEY
CATALOG_API_URL=https://gmcomponents.onrender.com/backend/products/

VOYAGE_API_KEY=YOUR_VOYAGE_API_KEY
VOYAGE_MODEL=voyage-4-large
VOYAGE_EMBEDDINGS_URL=https://api.voyageai.com/v1/embeddings

MONGODB_URI=mongodb://USER:PASSWORD@HOST/faq_logs?ssl=true
MONGODB_DB=faq_logs
MONGODB_COLLECTION=gm_componentes_logs_faq
MONGODB_RECOMMENDATION_COLLECTION=gm_componentes_logs_recommendation
MONGODB_TTL_SECONDS=60
```

No subir archivos `.env` al repositorio.

---

## 6. Instalación

Ejecutar:

```powershell
instalar_dependencias_ev2.bat
```

Este script instala:

- dependencias del frontend Angular/Ionic,
- dependencias del backend EV1 groq-proxy,
- entorno virtual Python 3.11 en `agente/.venv`,
- dependencias Python de `agente/requirements.txt`,
- Streamlit y Altair para el dashboard EV3,
- crea la carpeta `ev3_observability/logs` si no existe,
- valida que EV3Bridge importe correctamente.

---

## 7. Ejecución del proyecto completo

```powershell
iniciar_proyecto_completo_ev2.bat
```

Este script levanta:

```text
EV1 groq-proxy           http://localhost:8787
EV2 FastAPI agentes      http://localhost:8790
EV3 Dashboard Streamlit  http://localhost:8501
Frontend Angular         http://localhost:4200
```

---

## 8. Consola de agentes EV2 con EV3

```powershell
iniciar_consola_agentes_ev2.bat
```

Este script levanta:

```text
EV3 Dashboard Streamlit  http://localhost:8501
EV1 groq-proxy           http://localhost:8787
EV2 FastAPI agentes      http://localhost:8790
Consola CLI agente/main.py
```

Al cerrar la consola se detienen todos los servicios automáticamente.

---

## 9. Endpoints EV3

Directo en FastAPI:

```text
GET  /ev3/health
GET  /ev3/metrics
GET  /ev3/traces
GET  /ev3/recommendations
GET  /ev3/security-check?message=...
POST /ev3/log-event
```

Por groq-proxy Node:

```text
GET  /api/ev3/health
GET  /api/ev3/metrics
GET  /api/ev3/traces
GET  /api/ev3/recommendations
GET  /api/ev3/security-check?message=...
```

---

## 10. Dashboards de observabilidad

### Dashboard Angular (integrado)

Disponible en el tab **EV3** del frontend en `http://localhost:4200`.

Incluye:

- estado de salud del sistema EV3,
- KPIs: total eventos, ejecuciones, errores, bloqueos de seguridad,
- gauges de precisión, consistencia, tasa de error y latencia,
- distribución por intent con barras,
- latencia por ejecución (últimas 8 trazas),
- hallazgos técnicos,
- recomendaciones por área con justificación,
- trazas recientes,
- validador de seguridad interactivo.

### Dashboard Streamlit (externo)

Disponible en `http://localhost:8501` una vez levantado el bat.

Incluye:

- gráficos Altair de distribución por intent,
- latencia por intent,
- uso de tools,
- hallazgos y recomendaciones,
- validador de seguridad,
- log raw de trazas JSONL.

---

## 11. Métricas implementadas (IL3.1)

| Métrica | Descripción |
|---|---|
| Precisión | Score heurístico por intent y herramientas usadas |
| Consistencia | Score basado en estabilidad del flujo |
| Latencia | Tiempo de ejecución por llamada en ms |
| Tasa de error | Porcentaje de errores sobre total de eventos |
| Bloqueos de seguridad | Cantidad de inputs bloqueados por filtros EV3 |
| Trazas incompletas | Ejecuciones sin evento de cierre registrado |

---

## 12. Seguridad y uso responsable (IL3.3)

El módulo `security.py` implementa:

- lista de patrones bloqueados (`BLOCKED_PATTERNS`),
- validación de inputs antes de procesar,
- sanitización de datos sensibles en logs,
- respuestas seguras ante inputs bloqueados.

El validador de seguridad interactivo está disponible en ambos dashboards.

---

## 13. Relación con indicadores de logro EV3

| Indicador | Implementación |
|---|---|
| IL3.1 | `metrics.py`: precisión, consistencia, latencia conectadas de punta a punta |
| IL3.2 | `traceability.py` + `analyzer.py`: trazas JSONL con hallazgos automáticos |
| IL3.3 | `security.py`: validación, sanitización y bloqueo de inputs |
| IL3.4 | `recommendations.py`: recomendaciones por área con justificación basada en métricas |

---

## 14. Limitaciones conocidas

Groq y Voyage AI pueden responder con errores de límite de uso en cuentas gratuitas. Esto no indica falla en la arquitectura sino restricción temporal del proveedor externo.

El dashboard Streamlit requiere que el bat esté activo. Si se abre el tab EV3 sin el bat corriendo, el botón "Abrir en nueva pestaña" mostrará error de conexión.

---

## 15. Autores
Marcelo Baeza - Matias Guzman 
Proyecto desarrollado para **ISY0101 — Ingeniería de Soluciones con IA**.