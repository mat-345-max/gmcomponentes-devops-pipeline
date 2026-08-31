// groq-proxy/routes/recommendation.route.js
const express = require('express');
const { handleRecommendation } = require('../services/recommendation.service');
const { saveRecommendationLog } = require('../lib/mongo-log');
const { logEv3Event } = require('../services/ev3.service');
const router = express.Router();

router.post('/frontend-log', async (req, res) => {
  try {
    await saveRecommendationLog({
      tipo: 'recommendation_frontend',
      event: req.body?.event || 'unknown',
      sessionId: req.body?.sessionId || null,
      payload: req.body?.payload || {},
      source: 'frontend'
    });
    return res.json({ ok: true });
  } catch (error) {
    console.error('Error guardando frontend log Recommendation:', error);
    return res.status(500).json({
      ok: false,
      error: 'Error guardando frontend log Recommendation',
      detail: error.message
    });
  }
});

router.post('/', async (req, res) => {
  const startTime = Date.now();
  try {
    const result = await handleRecommendation(req.body);
    const latency_ms = Date.now() - startTime;

    await saveRecommendationLog({
      tipo: 'recommendation',
      pregunta: req.body?.message || '',
      budget: req.body?.budget || req.body?.state?.budget || null,
      step: req.body?.step || 'initial',
      state: req.body?.state || null,
      mode: result?.mode || null,
      answer: result?.answer || '',
      nextStep: result?.nextStep || null,
      quickOptions: Array.isArray(result?.quickOptions) ? result.quickOptions : [],
      suggestions: Array.isArray(result?.suggestions) ? result.suggestions : [],
      aiContext: result?.aiContext || null,
      confidence: typeof result?.confidence === 'number' ? result.confidence : null,
      source: 'backend'
    });

    // Registrar en EV3 de forma silenciosa
    logEv3Event({
      source: 'recommendation_ev1',
      intent: 'recommendation',
      message: req.body?.message || '',
      step: req.body?.step || 'initial',
      latency_ms,
      status: 'ok',
      mode: result?.mode || null,
      suggestions_count: (result?.suggestions || []).length,
    });

    return res.json(result);
  } catch (error) {
    const latency_ms = Date.now() - startTime;
    console.error('Error interno Recommendation:', error);

    await saveRecommendationLog({
      tipo: 'recommendation',
      pregunta: req.body?.message || '',
      budget: req.body?.budget || req.body?.state?.budget || null,
      step: req.body?.step || 'initial',
      state: req.body?.state || null,
      mode: 'error',
      answer: '',
      nextStep: null,
      quickOptions: [],
      suggestions: [],
      aiContext: null,
      confidence: null,
      error: error.message,
      source: 'backend'
    });

    logEv3Event({
      source: 'recommendation_ev1',
      intent: 'recommendation',
      message: req.body?.message || '',
      step: req.body?.step || 'initial',
      latency_ms,
      status: 'error',
      error: error.message,
    });

    return res.status(500).json({
      error: 'Error interno Recommendation',
      detail: error.message
    });
  }
});

module.exports = router;