// src/app/models/ev3-observability.models.ts

export interface Ev3Health {
  status: string;
  ev3_enabled: boolean;
  message: string;
}

export interface Ev3Metrics {
  status: string;
  metrics: Record<string, unknown>;
  error?: string;
}

export interface Ev3Trace {
  trace_id?: string;
  event?: string;
  timestamp?: string;
  intent?: string;
  agent?: string;
  latency_ms?: number;
  status?: string;
  [key: string]: unknown;
}

export interface Ev3Analysis {
  total_events?: number;
  agent_starts?: number;
  agent_ends?: number;
  errors?: number;
  security_blocks?: number;
  incomplete_traces?: number;
  avg_latency_ms?: number;
  max_latency_ms?: number;
  avg_precision_score?: number; // NUEVO
  avg_consistency_score?: number; // NUEVO
  intents?: Record<string, number>;
  tools?: Record<string, number>;
  findings?: string[];
  [key: string]: unknown;
}

export interface Ev3TracesResponse {
  status: string;
  analysis: Ev3Analysis;
  traces: Ev3Trace[];
  error?: string;
}

export interface Ev3Recommendation {
  type?: string;
  title?: string;
  description?: string;
  priority?: string;
  [key: string]: unknown;
}

export interface Ev3RecommendationsResponse {
  status: string;
  recommendations: Ev3Recommendation[];
  error?: string;
}

export interface Ev3SecurityResult {
  safe: boolean;
  reason: string;
  category?: string;
  safe_response?: string;
  error?: string;
}
