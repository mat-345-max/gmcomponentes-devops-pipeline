#!/usr/bin/env bash
# Recolecta la evidencia de infraestructura del clúster kind (EV3) mientras está activo.
# Uso: bash scripts/recolectar_evidencias.sh [archivo_salida]
# Escribe un informe en Markdown, lo agrega al resumen del job y falla si falta
# alguna evidencia: 3 targets de aplicación, logs de cada backend o pods Ready.
set -uo pipefail

SALIDA="${1:-artifacts/evidencia-infraestructura.md}"
NS_APP=gmcomponentes
NS_MON=monitoring
FALLOS=0
mkdir -p "$(dirname "$SALIDA")"
: > "$SALIDA"

PIDS=()
limpiar() { for p in "${PIDS[@]:-}"; do [ -n "$p" ] && kill "$p" 2>/dev/null || true; done; }
trap limpiar EXIT

pf() { kubectl port-forward -n "$1" "$2" "$3" >/dev/null 2>&1 & PIDS+=($!); }
pf "$NS_MON" svc/kube-prometheus-stack-prometheus 39090:9090
pf "$NS_MON" svc/loki 33100:3100
pf "$NS_APP" svc/groq-proxy 38787:8787
pf "$NS_APP" svc/agente 38790:8790
pf "$NS_APP" svc/frontend 38080:80
sleep 5

escribir() { printf '%s\n' "$*" >> "$SALIDA"; }
bloque() { escribir '```text'; cat >> "$SALIDA"; escribir '```'; }

escribir "# Evidencia de infraestructura (EV3)"
escribir ""
escribir "- Run: ${GITHUB_SERVER_URL:-https://github.com}/${GITHUB_REPOSITORY:-local}/actions/runs/${GITHUB_RUN_ID:-0}"
escribir "- Commit: ${GITHUB_SHA:-desconocido}"
escribir "- Duración del despliegue (DEPLOY_SECONDS): ${DEPLOY_SECONDS:-no disponible} s"
escribir "- Fecha (UTC): $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# 1) Pods
escribir ""; escribir "## 1. Pods de la aplicación"
kubectl get pods -n "$NS_APP" -o wide 2>&1 | bloque
LISTOS=$(kubectl get pods -n "$NS_APP" -o json 2>/dev/null | jq '[.items[] | select(.status.phase=="Running" and ([.status.containerStatuses[]?.ready] | all))] | length')
TOTAL=$(kubectl get pods -n "$NS_APP" -o json 2>/dev/null | jq '.items | length')
LISTOS=${LISTOS:-0}; TOTAL=${TOTAL:-0}
escribir "Pods Ready: $LISTOS/$TOTAL (esperados: 4 = groq-proxy 1 + agente 2 + frontend 1)"
if [ "$TOTAL" -lt 4 ] || [ "$LISTOS" -ne "$TOTAL" ]; then escribir "RESULTADO: FALLA"; FALLOS=$((FALLOS+1)); else escribir "RESULTADO: OK"; fi

# 2) Rollouts
escribir ""; escribir "## 2. Despliegues y rollouts"
kubectl get deployments -n "$NS_APP" 2>&1 | bloque
for d in groq-proxy agente frontend; do
  SAL=$(kubectl rollout status "deployment/$d" -n "$NS_APP" --timeout=60s 2>&1) || FALLOS=$((FALLOS+1))
  printf '%s\n' "$SAL" | bloque
done

# 3) Servicios (nombres y puertos)
escribir ""; escribir "## 3. Servicios"
{ kubectl get svc -n "$NS_APP" 2>&1; echo; kubectl get svc -n "$NS_MON" 2>&1; } | bloque

# 4) Targets de Prometheus
escribir ""; escribir "## 4. Targets de aplicación en Prometheus (up{namespace=\"$NS_APP\"})"
UP=0; TARGETS=""
for i in $(seq 1 6); do
  RESP=$(curl -s -G http://127.0.0.1:39090/api/v1/query --data-urlencode "query=up{namespace=\"$NS_APP\"}" 2>/dev/null || true)
  UP=$(printf '%s' "$RESP" | jq '[.data.result[]? | select(.value[1]=="1")] | length' 2>/dev/null || echo 0)
  TARGETS=$(printf '%s' "$RESP" | jq -r '.data.result[]? | "service=\(.metric.service) pod=\(.metric.pod) up=\(.value[1])"' 2>/dev/null || true)
  [ "${UP:-0}" -ge 3 ] && break
  sleep 10
done
printf '%s\n' "${TARGETS:-sin resultados}" | bloque
escribir "Targets arriba: ${UP:-0} (esperados: 3 = groq-proxy 1 + agente 2)"
if [ "${UP:-0}" -ge 3 ]; then escribir "RESULTADO: OK"; else escribir "RESULTADO: FALLA"; FALLOS=$((FALLOS+1)); fi

# 5) Logs por backend en Loki
escribir ""; escribir "## 5. Logs en Loki por backend"
for i in 1 2 3; do
  curl -s -o /dev/null http://127.0.0.1:38787/api/no-existe || true
  curl -s -o /dev/null http://127.0.0.1:38790/no-existe || true
done
for svc in groq-proxy agente; do
  N=0; MUESTRA=""
  for i in $(seq 1 6); do
    RESP=$(curl -s -G http://127.0.0.1:33100/loki/api/v1/query_range \
      --data-urlencode "query={namespace=\"$NS_APP\"} | json | service=\"$svc\"" \
      --data-urlencode 'limit=5' 2>/dev/null || true)
    N=$(printf '%s' "$RESP" | jq '[.data.result[]?.values[]?] | length' 2>/dev/null || echo 0)
    MUESTRA=$(printf '%s' "$RESP" | jq -r '[.data.result[]?.values[]?[1]][0] // empty' 2>/dev/null || true)
    [ "${N:-0}" -ge 1 ] && break
    sleep 10
  done
  escribir ""; escribir "### $svc"
  escribir "Consulta: {namespace=\"$NS_APP\"} | json | service=\"$svc\""
  escribir "Líneas recibidas (máx. 5 consultadas): ${N:-0}"
  printf '%s\n' "${MUESTRA:-sin líneas}" | bloque
  if [ "${N:-0}" -ge 1 ]; then escribir "RESULTADO: OK"; else escribir "RESULTADO: FALLA"; FALLOS=$((FALLOS+1)); fi
done

# 6) Pruebas de servicio
escribir ""; escribir "## 6. Pruebas de servicio (HTTP)"
for par in "groq-proxy|http://127.0.0.1:38787/api/health" "agente|http://127.0.0.1:38790/health" "frontend|http://127.0.0.1:38080/healthz"; do
  NOMBRE=${par%%|*}; URL=${par#*|}
  CODIGO=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$URL" 2>/dev/null || echo 000)
  if [ "$CODIGO" = "200" ]; then R=OK; else R=FALLA; FALLOS=$((FALLOS+1)); fi
  escribir "- $NOMBRE $URL -> HTTP $CODIGO ($R)"
done

escribir ""
if [ "$FALLOS" -eq 0 ]; then escribir "## Resultado global: OK"; else escribir "## Resultado global: FALLA ($FALLOS controles)"; fi
[ -n "${GITHUB_STEP_SUMMARY:-}" ] && cat "$SALIDA" >> "$GITHUB_STEP_SUMMARY"
cat "$SALIDA"
[ "$FALLOS" -eq 0 ]