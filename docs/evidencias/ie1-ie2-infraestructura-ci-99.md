# Evidencia de infraestructura (IE1 e IE2) - CI #99

- **Run:** https://github.com/mat-345-max/gmcomponentes-devops-pipeline/actions/runs/45271271508
- **Commit:** `06c3e077f8030c98516d9864bae40cf3b94bd718`
- **Duración del despliegue (`DEPLOY_SECONDS`):** 13 s
- **Fecha (UTC):** 2026-11-23T21:52:45Z
- **Resultado global:** OK

## 1. Pods de la aplicación

```text
NAME                         READY   STATUS    RESTARTS   AGE   IP           NODE                          NOMINATED NODE   READINESS GATES
agente-5967dc6789-mrk64      1/1     Running   0          10m   10.244.0.6   gmcomponentes-control-plane   <none>           <none>
agente-5967dc6789-x7477      1/1     Running   0          10m   10.244.0.5   gmcomponentes-control-plane   <none>           <none>
frontend-78bbb96c69-p7r7s    1/1     Running   0          10m   10.244.0.7   gmcomponentes-control-plane   <none>           <none>
groq-proxy-b64d8cf77-6hmj7   1/1     Running   0          10m   10.244.0.8   gmcomponentes-control-plane   <none>           <none>
```

Pods Ready: 4/4 (esperados: 4 = groq-proxy 1 + agente 2 + frontend 1). **RESULTADO: OK**

## 2. Despliegues y rollouts

```text
NAME         READY   UP-TO-DATE   AVAILABLE   AGE
agente       2/2     2            2           10m
frontend     1/1     1            1           10m
groq-proxy   1/1     1            1           10m
deployment "groq-proxy" successfully rolled out
deployment "agente" successfully rolled out
deployment "frontend" successfully rolled out
```

## 3. Servicios

```text
NAME         TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)    AGE
agente       ClusterIP   10.96.16.246   <none>        8790/TCP   10m
frontend     ClusterIP   10.96.38.155   <none>        80/TCP     10m
groq-proxy   ClusterIP   10.96.2.247    <none>        8787/TCP   10m

NAME                                       TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)                      AGE
alloy                                      ClusterIP   10.96.42.249    <none>        12345/TCP                    8m3s
kube-prometheus-stack-grafana              ClusterIP   10.96.116.241   <none>        80/TCP                       9m42s
kube-prometheus-stack-kube-state-metrics   ClusterIP   10.96.160.119   <none>        8080/TCP                     9m42s
kube-prometheus-stack-operator             ClusterIP   10.96.231.132   <none>        443/TCP                      9m42s
kube-prometheus-stack-prometheus           ClusterIP   10.96.74.189    <none>        9090/TCP,8080/TCP            9m42s
loki                                       ClusterIP   10.96.104.242   <none>        3100/TCP,9095/TCP,9096/TCP   8m57s
loki-headless                              ClusterIP   None            <none>        3100/TCP,9095/TCP,9096/TCP   8m57s
loki-memberlist                            ClusterIP   None            <none>        7946/TCP                     8m57s
prometheus-operated                        ClusterIP   None            <none>        9090/TCP                     9m38s
pushgateway                                ClusterIP   10.96.129.9     <none>        9091/TCP                     9m13s
```

## 4. Targets de aplicación en Prometheus

Consulta: `up{namespace="gmcomponentes"}`

```text
service=agente pod=agente-5967dc6789-mrk64 up=1
service=agente pod=agente-5967dc6789-x7477 up=1
service=groq-proxy pod=groq-proxy-b64d8cf77-6hmj7 up=1
```

Targets arriba: 3 (esperados: 3 = groq-proxy 1 + agente 2). **RESULTADO: OK**

## 5. Logs en Loki por backend

### groq-proxy

Consulta: `{namespace="gmcomponentes"} | json | service="groq-proxy"`. Líneas recibidas (máx. 5 consultadas): 2.

```json
{ "timestamp": "2026-11-23T21:45:41.195Z", "level": "warn", "service": "groq-proxy", "message": "http_request", "request_id": "3d449084-8806-43db-9d9b-65b1d0f52d5e", "method": "GET", "route": "sin_ruta", "status_code": 404, "duration_ms": 0.66 }
```

**RESULTADO: OK**

### agente

Consulta: `{namespace="gmcomponentes"} | json | service="agente"`. Líneas recibidas (máx. 5 consultadas): 2.

```json
{ "timestamp": "2026-11-23T21:45:41.202Z", "level": "warn", "service": "agente", "message": "http_request", "request_id": "dbcaedc2-24e8-46f8-b6df-87f46300d1f6", "method": "GET", "route": "sin_ruta", "status_code": 404, "duration_ms": 0.4 }
```

**RESULTADO: OK**

## 6. Pruebas de servicio (HTTP)

| Servicio   | URL (port-forward)                  | Resultado     |
| ---------- | ----------------------------------- | ------------- |
| groq-proxy | `http://127.0.0.1:38787/api/health` | HTTP 200 (OK) |
| agente     | `http://127.0.0.1:38790/health`     | HTTP 200 (OK) |
| frontend   | `http://127.0.0.1:38080/healthz`    | HTTP 200 (OK) |

**Resultado global: OK**
