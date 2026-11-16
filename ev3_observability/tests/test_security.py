import pytest
from ev3_observability.security import (
    validate_input,
    sanitize_for_logs,
    safe_eval,
)


class TestValidateInput:
    def test_bloquea_input_vacio(self):
        resultado = validate_input("")
        assert resultado.allowed is False
        assert resultado.category == "empty_input"

    def test_bloquea_patron_hackear(self):
        resultado = validate_input("como puedo hackear una cuenta")
        assert resultado.allowed is False
        assert resultado.category == "harmful_request"

    def test_bloquea_ddos(self):
        resultado = validate_input("quiero hacer un ataque ddos")
        assert resultado.allowed is False
        assert resultado.category == "harmful_request"

    def test_bloquea_dato_sensible_rut(self):
        resultado = validate_input("mi rut es 12.345.678-9")
        assert resultado.allowed is False
        assert resultado.category == "privacy_risk"

    def test_bloquea_dato_sensible_tarjeta(self):
        resultado = validate_input("mi tarjeta es 1234567812345678")
        assert resultado.allowed is False
        assert resultado.category == "privacy_risk"

    def test_permite_input_normal(self):
        resultado = validate_input("¿Cuál es el precio de la placa madre X?")
        assert resultado.allowed is True
        assert resultado.category == "safe"
        assert resultado.safe_response == ""


class TestSanitizeForLogs:
    def test_oculta_rut(self):
        texto = sanitize_for_logs("mi rut es 12.345.678-9")
        assert "12.345.678-9" not in texto
        assert "[RUT_OCULTO]" in texto

    def test_oculta_tarjeta(self):
        texto = sanitize_for_logs("tarjeta 1234567812345678")
        assert "1234567812345678" not in texto
        assert "[TARJETA_OCULTA]" in texto

    def test_oculta_password(self):
        texto = sanitize_for_logs("password=mi_clave_secreta")
        assert "mi_clave_secreta" not in texto
        assert "[OCULTO]" in texto

    def test_respeta_max_length(self):
        texto_largo = "a" * 1000
        resultado = sanitize_for_logs(texto_largo, max_length=50)
        assert len(resultado) == 50


class TestSafeEval:
    def test_evalua_expresion_valida(self):
        assert safe_eval("2 + 2") == "4"

    def test_rechaza_expresion_con_caracteres_no_permitidos(self):
        resultado = safe_eval("__import__('os').system('ls')")
        assert resultado == "Expresion no permitida."

    def test_maneja_error_de_expresion_malformada(self):
        resultado = safe_eval("2 + ")
        assert resultado == "Error en la expresion."