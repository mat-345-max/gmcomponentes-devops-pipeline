"""
dashboard.py - Dashboard EV3 GM-COMPONENTS

Dashboard Streamlit para visualizar:
- Metricas de observabilidad
- Trazabilidad por logs JSONL
- Bloqueos de seguridad
- Hallazgos tecnicos
- Recomendaciones de optimizacion

Ejecutar desde ev3_observability:
streamlit run dashboard.py
"""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from analyzer import analyze_traces, build_findings
from recommendations import generate_recommendations
from security import BLOCKED_PATTERNS, safe_eval, validate_input
from traceability import TRACE_LOG_FILE, clear_traces, read_traces


st.set_page_config(
    page_title="EV3 Observabilidad GM-COMPONENTS",
    page_icon="EV3",
    layout="wide",
)

st.title("EV3 - Observabilidad y Trazabilidad GM-COMPONENTS")
st.caption(
    "Dashboard de monitoreo para agentes IA: metricas, trazabilidad, seguridad "
    "y recomendaciones tecnicas."
)


stats = analyze_traces()
traces = read_traces()


tab_metrics, tab_trace, tab_security, tab_findings, tab_raw = st.tabs(
    [
        "Observabilidad",
        "Trazabilidad",
        "Seguridad",
        "Hallazgos y recomendaciones",
        "Log raw",
    ]
)


with tab_metrics:
    st.subheader("Metricas principales")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Ejecuciones iniciadas", stats["total_agent_starts"])
    col2.metric("Ejecuciones finalizadas", stats["total_agent_ends"])
    col3.metric("Errores", stats["total_errors"])
    col4.metric("Bloqueos seguridad", stats["total_security_blocks"])

    col5, col6, col7, col8, col9 = st.columns(5)
    col5.metric("Latencia promedio", f"{stats['avg_latency_ms']} ms")
    col6.metric("Latencia maxima", f"{stats['max_latency_ms']} ms")
    col7.metric("Trazas incompletas", stats["incomplete_traces"])
    col8.metric("Precision promedio", stats["avg_precision_score"])
    col9.metric("Consistencia promedio", stats["avg_consistency_score"])

    st.divider()

    left, right = st.columns(2)

    with left:
        st.markdown("**Distribucion por intent**")
        if stats["intents"]:
            df_intents = pd.DataFrame(
                list(stats["intents"].items()),
                columns=["Intent", "Cantidad"],
            )

            chart_intents = (
                alt.Chart(df_intents)
                .mark_bar(size=36)
                .encode(
                    x=alt.X("Intent:N", title="Intent"),
                    y=alt.Y("Cantidad:Q", title="Cantidad", axis=alt.Axis(format="d")),
                    tooltip=["Intent", "Cantidad"],
                    color=alt.Color("Intent:N", legend=None),
                )
                .properties(height=260)
            )

            st.altair_chart(chart_intents, use_container_width=True)
        else:
            st.info("Aun no hay intents registrados.")

    with right:
        st.markdown("**Latencia promedio por intent**")
        if stats["avg_latency_by_intent"]:
            df_latency = pd.DataFrame(
                list(stats["avg_latency_by_intent"].items()),
                columns=["Intent", "Latencia promedio ms"],
            )

            chart_latency = (
                alt.Chart(df_latency)
                .mark_bar(size=36)
                .encode(
                    x=alt.X("Intent:N", title="Intent"),
                    y=alt.Y("Latencia promedio ms:Q", title="Latencia promedio ms"),
                    tooltip=["Intent", "Latencia promedio ms"],
                    color=alt.Color("Intent:N", legend=None),
                )
                .properties(height=260)
            )

            st.altair_chart(chart_latency, use_container_width=True)
        else:
            st.info("Aun no hay latencias registradas.")

    st.divider()

    st.markdown("**Uso de tools**")
    if stats["tools"]:
        df_tools = pd.DataFrame(
            list(stats["tools"].items()),
            columns=["Tool", "Usos"],
        ).sort_values("Usos", ascending=False)
        st.dataframe(df_tools, use_container_width=True)
    else:
        st.info("Aun no hay tools registradas.")


with tab_trace:
    st.subheader("Trazabilidad de ejecuciones")

    if not traces:
        st.info("Aun no hay trazas registradas.")
    else:
        df = pd.DataFrame(traces)

        preferred_columns = [
            "logged_at",
            "event",
            "trace_id",
            "session_id",
            "intent",
            "status",
            "source",
            "latency_ms",
            "message_preview",
            "answer_preview",
            "error",
            "reason",
        ]

        visible_columns = [col for col in preferred_columns if col in df.columns]
        remaining_columns = [col for col in df.columns if col not in visible_columns]

        st.dataframe(
            df[visible_columns + remaining_columns],
            use_container_width=True,
            height=420,
        )

    st.divider()

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**Ultimos errores**")
        if stats["recent_errors"]:
            st.dataframe(pd.DataFrame(stats["recent_errors"]), use_container_width=True)
        else:
            st.success("No hay errores recientes registrados.")

    with col_b:
        st.markdown("**Trazas incompletas**")
        if stats["incomplete_traces"] > 0:
            st.warning(
                f"Se detectaron {stats['incomplete_traces']} trazas incompletas. "
                "Revisar cortes entre inicio y fin de ejecucion."
            )
        else:
            st.success("No hay trazas incompletas detectadas.")


with tab_security:
    st.subheader("Seguridad y uso responsable")

    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.markdown("**Validador de input**")
        test_input = st.text_area(
            "Escribe una consulta para probar el filtro EV3:",
            placeholder="Ejemplo: tienen stock de rtx 4060",
            height=120,
        )

        if test_input:
            result = validate_input(test_input)

            if result.allowed:
                st.success("Input permitido por la capa EV3.")
            else:
                st.error("Input bloqueado por la capa EV3.")
                st.write(f"Categoria: `{result.category}`")
                st.write(f"Razon: `{result.reason}`")
                st.info(result.safe_response)

        st.divider()

        st.markdown("**Calculadora segura**")
        expression = st.text_input(
            "Expresion matematica:", placeholder="2 + 2 * (3 - 1)"
        )
        if expression:
            st.write(safe_eval(expression))

    with col2:
        st.markdown("**Patrones bloqueados**")
        for pattern in BLOCKED_PATTERNS:
            st.code(pattern, language="regex")

        st.divider()

        st.markdown("**Bloqueos recientes**")
        if stats["recent_blocks"]:
            st.dataframe(pd.DataFrame(stats["recent_blocks"]), use_container_width=True)
        else:
            st.info("No hay bloqueos registrados en el log.")


with tab_findings:
    st.subheader("Hallazgos tecnicos")

    findings = build_findings()
    for item in findings:
        st.write(f"- {item}")

    st.divider()

    st.subheader("Recomendaciones de optimizacion")

    recommendations = generate_recommendations(stats)

    for rec in recommendations:
        with st.container(border=True):
            st.markdown(f"**Area:** {rec['area']}")
            st.markdown(f"**Recomendacion:** {rec['recommendation']}")
            st.markdown(f"**Justificacion:** {rec['justification']}")

    st.divider()

    st.subheader("Resumen para reporte EV3")

    st.text_area(
        "Texto base",
        value=(
            f"Durante la observacion del agente se registraron "
            f"{stats['total_agent_ends']} ejecuciones finalizadas, "
            f"{stats['total_errors']} errores, "
            f"{stats['total_security_blocks']} bloqueos de seguridad y una latencia "
            f"promedio de {stats['avg_latency_ms']} ms. "
            "Estos datos permiten evaluar el comportamiento del agente, detectar "
            "puntos de mejora y proponer optimizaciones de rendimiento, seguridad "
            "y escalabilidad."
        ),
        height=160,
    )


with tab_raw:
    st.subheader("Archivo JSONL de trazabilidad")

    st.code(str(TRACE_LOG_FILE), language="text")

    if TRACE_LOG_FILE.exists():
        content = TRACE_LOG_FILE.read_text(encoding="utf-8")
        st.code(content if content.strip() else "(log vacio)", language="json")
    else:
        st.info("El archivo de log aun no existe.")

    st.divider()

    if st.button("Limpiar trazas EV3"):
        clear_traces()
        st.success("Trazas limpiadas. Recarga el dashboard para ver los cambios.")
