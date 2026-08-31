// groq-proxy/routes/faq.route.js
const express = require('express');
const { handleFaq } = require('../services/faq.service');
const { logEv3Event } = require('../services/ev3.service');
const router = express.Router();

router.post('/', async (req, res) => {
  const startTime = Date.now();
  try {
    const result = await handleFaq(req.body);
    const latency_ms = Date.now() - startTime;

    // Registrar en EV3 de forma silenciosa
    logEv3Event({
      source: 'faq_ev1',
      intent: 'faq',
      message: req.body?.pregunta || '',
      latency_ms,
      status: 'ok',
      has_product: !!result?.productoDestacado,
      suggestions_count: (result?.sugerencias || []).length,
    });

    return res.json(result);
  } catch (error) {
    const latency_ms = Date.now() - startTime;
    console.error('Error interno FAQ:', error);

    logEv3Event({
      source: 'faq_ev1',
      intent: 'faq',
      message: req.body?.pregunta || '',
      latency_ms,
      status: 'error',
      error: error.message,
    });

    return res.status(500).json({
      error: 'Error interno FAQ',
      detail: error.message
    });
  }
});

module.exports = router;