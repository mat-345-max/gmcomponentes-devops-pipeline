"""
ev3_bridge.py - Puente entre EV2 Agent Service y EV3 Observability
Carga la capa EV3 ubicada en la raiz del proyecto:
ev3_observability/
Se usa importlib para evitar errores visuales de imports en VS Code/Pylance.
"""

from __future__ import annotations
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EV3_PATH = PROJECT_ROOT / "ev3_observability"

if str(EV3_PATH) not in sys.path:  # NUEVO
    sys.path.insert(0, str(EV3_PATH))  # NUEVO


def _load_module(module_name: str, file_path: Path) -> ModuleType:
    if not file_path.exists():
        raise ImportError(f"No existe el archivo EV3: {file_path}")
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"No se pudo cargar modulo EV3: {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


try:
    metrics_module = _load_module("ev3_metrics_module", EV3_PATH / "metrics.py")
    security_module = _load_module("ev3_security_module", EV3_PATH / "security.py")
    traceability_module = _load_module(
        "ev3_traceability_module", EV3_PATH / "traceability.py"
    )

    ev3_metrics: Any = metrics_module.ev3_metrics
    sanitize_for_logs: Any = security_module.sanitize_for_logs
    validate_input: Any = security_module.validate_input
    generate_trace_id: Any = traceability_module.generate_trace_id
    log_agent_end: Any = traceability_module.log_agent_end
    log_agent_start: Any = traceability_module.log_agent_start
    log_security_block: Any = traceability_module.log_security_block

    EV3_AVAILABLE = True
    EV3_LOAD_ERROR = ""

except Exception as error:
    EV3_AVAILABLE = False
    EV3_LOAD_ERROR = str(error)
    ev3_metrics = None
    sanitize_for_logs = None
    validate_input = None
    generate_trace_id = None
    log_agent_end = None
    log_agent_start = None
    log_security_block = None


# ─────────────────────────────────────────────
# Clase EV3Bridge — usada por ev3_api.py
# ─────────────────────────────────────────────


class EV3Bridge:
    """Interfaz orientada a objetos sobre los módulos EV3 ya cargados."""

    def __init__(self):
        self.ev3_available = EV3_AVAILABLE
        self._error = EV3_LOAD_ERROR

    # ── paths ──────────────────────────────────
    def get_log_path(self) -> Path | None:
        log = EV3_PATH / "logs" / "ev3_agent_traces.jsonl"
        return log if log.exists() else None

    # ── módulos lazy ───────────────────────────
    def get_metrics_collector(self):
        """Retorna la instancia singleton ev3_metrics (EV3MetricsCollector)."""
        return ev3_metrics  # ya es instancia, no clase

    def get_analyzer(self):
        """Carga y retorna el módulo analyzer con la clase EV3Analyzer."""
        if not self.ev3_available:
            return None
        try:
            return _load_module("ev3_analyzer_module", EV3_PATH / "analyzer.py")
        except Exception as e:
            print(f"[EV3Bridge] Error cargando analyzer: {e}")  # NUEVO temporal
            return None

    def get_recommendations(self):
        """Carga y retorna el módulo recommendations con EV3RecommendationEngine."""
        if not self.ev3_available:
            return None
        try:
            return _load_module(
                "ev3_recommendations_module", EV3_PATH / "recommendations.py"
            )
        except Exception:
            return None

    def get_security(self):
        """Retorna el módulo security ya cargado."""
        if not self.ev3_available:
            return None
        return security_module
