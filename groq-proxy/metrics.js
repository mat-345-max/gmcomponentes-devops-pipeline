const client = require('prom-client');

// Registro propio para no mezclar métricas si el módulo se carga más de una vez
const register = new client.Registry();

// Métricas del proceso: CPU, memoria, event loop, etc.
client.collectDefaultMetrics({ register });

const httpRequestsTotal = new client.Counter({
  name: 'http_requests_total',
  help: 'Total de peticiones HTTP recibidas',
  labelNames: ['method', 'route', 'status_code'],
  registers: [register]
});

const httpRequestDuration = new client.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duración de las peticiones HTTP en segundos',
  labelNames: ['method', 'route', 'status_code'],
  buckets: [0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
  registers: [register]
});

function metricsMiddleware(req, res, next) {
  const end = httpRequestDuration.startTimer();

  res.on('finish', () => {
    // Las rutas inexistentes se agrupan en una sola etiqueta
    // para que no se generen series infinitas
    const route = req.route ? `${req.baseUrl}${req.route.path}` : 'sin_ruta';
    const labels = {
      method: req.method,
      route,
      status_code: res.statusCode
    };

    httpRequestsTotal.inc(labels);
    end(labels);
  });

  next();
}

async function metricsHandler(req, res) {
  res.set('Content-Type', register.contentType);
  res.end(await register.metrics());
}

module.exports = { metricsMiddleware, metricsHandler, register };