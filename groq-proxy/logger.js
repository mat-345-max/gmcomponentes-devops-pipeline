const { randomUUID } = require('crypto');

const SERVICE = 'groq-proxy';

// Rutas que se consultan todo el tiempo (Prometheus y probes de salud).
// No se registran en el log para no llenar Loki de ruido.
const RUTAS_SILENCIADAS = new Set(['/metrics', '/api/health']);

function write(level, message, fields = {}) {
  const linea = {
    timestamp: new Date().toISOString(),
    level,
    service: SERVICE,
    message,
    ...fields
  };
  process.stdout.write(`${JSON.stringify(linea)}\n`);
}

const logger = {
  info: (message, fields) => write('info', message, fields),
  warn: (message, fields) => write('warn', message, fields),
  error: (message, fields) => write('error', message, fields)
};

function obtenerRequestId(req) {
  const entrante = req.headers['x-request-id'];
  // Solo se acepta un id con formato razonable, para no copiar al log texto arbitrario
  if (typeof entrante === 'string' && /^[A-Za-z0-9._-]{8,64}$/.test(entrante)) {
    return entrante;
  }
  return randomUUID();
}

function requestLogger(req, res, next) {
  const requestId = obtenerRequestId(req);
  req.requestId = requestId;
  res.setHeader('X-Request-ID', requestId);

  const inicio = process.hrtime.bigint();

  res.on('finish', () => {
    if (RUTAS_SILENCIADAS.has(req.path)) {
      return;
    }

    const duracionMs = Number(process.hrtime.bigint() - inicio) / 1e6;
    const nivel = res.statusCode >= 500 ? 'error' : res.statusCode >= 400 ? 'warn' : 'info';

    write(nivel, 'http_request', {
      request_id: requestId,
      method: req.method,
      route: req.route ? `${req.baseUrl}${req.route.path}` : 'sin_ruta',
      status_code: res.statusCode,
      duration_ms: Math.round(duracionMs * 100) / 100
    });
  });

  next();
}

module.exports = { logger, requestLogger };