// groq-proxy/routes/ev3.route.js

const express = require('express');
const router = express.Router();
const ev3Service = require('../services/ev3.service');

router.get('/health', async (req, res) => {
  try {
    const data = await ev3Service.getHealth();
    res.json(data);
  } catch (err) {
    res.status(503).json({ error: err.message });
  }
});

router.get('/metrics', async (req, res) => {
  try {
    const data = await ev3Service.getMetrics();
    res.json(data);
  } catch (err) {
    res.status(503).json({ error: err.message });
  }
});

router.get('/traces', async (req, res) => {
  try {
    const data = await ev3Service.getTraces();
    res.json(data);
  } catch (err) {
    res.status(503).json({ error: err.message });
  }
});

router.get('/recommendations', async (req, res) => {
  try {
    const data = await ev3Service.getRecommendations();
    res.json(data);
  } catch (err) {
    res.status(503).json({ error: err.message });
  }
});

router.get('/security-check', async (req, res) => {
  const message = req.query.message || '';
  if (!message.trim()) {
    return res.status(400).json({ error: 'Parámetro message requerido' });
  }
  try {
    const data = await ev3Service.securityCheck(message);
    res.json(data);
  } catch (err) {
    res.status(503).json({ error: err.message });
  }
});

module.exports = router;