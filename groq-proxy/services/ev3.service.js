// groq-proxy/services/ev3.service.js
const fetch = require('node-fetch');

const EV3_BASE = process.env.AGENT_SERVICE_URL || 'http://localhost:8790';

async function ev3Fetch(path) {
  const res = await fetch(`${EV3_BASE}${path}`);
  if (!res.ok) throw new Error(`EV3 FastAPI error ${res.status} en ${path}`);
  return res.json();
}

async function getHealth()          { return ev3Fetch('/ev3/health'); }
async function getMetrics()         { return ev3Fetch('/ev3/metrics'); }
async function getTraces()          { return ev3Fetch('/ev3/traces'); }
async function getRecommendations() { return ev3Fetch('/ev3/recommendations'); }

async function securityCheck(message) {
  const encoded = encodeURIComponent(message);
  return ev3Fetch(`/ev3/security-check?message=${encoded}`);
}

async function logEv3Event(eventData) {
  try {
    const res = await fetch(`${EV3_BASE}/ev3/log-event`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(eventData),
    });
    if (!res.ok) return null;
    return res.json();
  } catch (_) {
    return null; // EV3 nunca debe romper el flujo EV1
  }
}

module.exports = {
  getHealth,
  getMetrics,
  getTraces,
  getRecommendations,
  securityCheck,
  logEv3Event,
};