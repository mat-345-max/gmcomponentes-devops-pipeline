import pytest
from ev3_observability.metrics import EV3MetricsCollector


@pytest.fixture
def collector():
    return EV3MetricsCollector()


class TestTimer:
    def test_stop_timer_sin_start_devuelve_cero(self, collector):
        assert collector.stop_timer("trace-inexistente") == 0.0

    def test_start_y_stop_timer_devuelve_latencia_positiva(self, collector):
        collector.start_timer("trace-1")
        latencia = collector.stop_timer("trace-1")
        assert latencia >= 0.0


class TestEstimatePrecision:
    def test_respuesta_vacia_devuelve_cero(self, collector):
        assert collector.estimate_precision("faq", "") == 0.0

    def test_con_error_devuelve_score_bajo(self, collector):
        score = collector.estimate_precision("faq", "algo", {"error": "fallo"})
        assert score == 0.2

    def test_faq_con_producto_destacado_sube_score(self, collector):
        respuesta_larga = "Esta es una respuesta suficientemente larga sobre el producto."
        score = collector.estimate_precision(
            "faq", respuesta_larga, {"productoDestacado": True}
        )
        assert score > 0.45

    def test_recommendation_con_suggestions_sube_score(self, collector):
        respuesta_larga = "Te recomiendo estos componentes para tu setup gamer."
        score = collector.estimate_precision(
            "recommendation", respuesta_larga, {"suggestions": ["item1", "item2"]}
        )
        assert score > 0.4

    def test_catalog_con_matches_da_075(self, collector):
        score = collector.estimate_precision("catalog", "resultado", {"matches": ["a"]})
        assert score == 0.75

    def test_catalog_sin_matches_da_045(self, collector):
        score = collector.estimate_precision("catalog", "resultado", {"matches": []})
        assert score == 0.45


class TestEstimateConsistency:
    def test_faq_con_tool_correcta_sube_score(self, collector):
        score = collector.estimate_consistency(
            "faq", ["gm_components_faq_rag_ev1"], {"source": "faq_agent"}
        )
        assert score == 1.0

    def test_faq_sin_tool_correcta_score_base(self, collector):
        score = collector.estimate_consistency("faq", [], {})
        assert score == 0.5

    def test_recommendation_con_tool_correcta(self, collector):
        score = collector.estimate_consistency(
            "recommendation",
            ["gm_components_recommendation_ev1"],
            {"source": "recommendation_agent"},
        )
        assert score == 1.0


class TestRecordCallAndSummary:
    def test_record_call_agrega_registro(self, collector):
        collector.record_call(
            trace_id="t1",
            session_id="s1",
            agent_name="orchestrator",
            intent="faq",
            user_message="hola",
            answer="respuesta de prueba suficientemente larga",
            status="ok",
            latency_ms=120.5,
            used_tools=["gm_components_faq_rag_ev1"],
        )
        assert len(collector.records) == 1
        assert collector.records[0].intent == "faq"

    def test_summary_con_registros_vacios(self, collector):
        resumen = collector.summary()
        assert resumen["total_requests"] == 0
        assert resumen["error_rate"] == 0.0

    def test_summary_calcula_error_rate(self, collector):
        collector.record_call(
            trace_id="t1", session_id="s1", agent_name="orchestrator",
            intent="faq", user_message="hola", answer="respuesta",
            status="ok", latency_ms=100,
        )
        collector.record_call(
            trace_id="t2", session_id="s1", agent_name="orchestrator",
            intent="faq", user_message="hola", answer="",
            status="error", latency_ms=50, error="fallo",
        )
        resumen = collector.summary()
        assert resumen["total_requests"] == 2
        assert resumen["total_errors"] == 1
        assert resumen["error_rate"] == 0.5

    def test_reset_limpia_registros(self, collector):
        collector.record_call(
            trace_id="t1", session_id="s1", agent_name="orchestrator",
            intent="faq", user_message="hola", answer="respuesta",
            status="ok", latency_ms=100,
        )
        collector.reset()
        assert collector.records == []