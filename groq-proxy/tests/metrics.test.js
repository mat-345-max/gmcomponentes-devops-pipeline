const request = require("supertest");
const app = require("../app");

describe("GET /metrics", () => {
  it("responde 200 con formato Prometheus", async () => {
    const res = await request(app).get("/metrics");
    expect(res.statusCode).toBe(200);
    expect(res.headers["content-type"]).toContain("text/plain");
    expect(res.text).toContain("process_cpu_user_seconds_total");
  });

  it("cuenta las peticiones recibidas", async () => {
    await request(app).get("/api/health");
    const res = await request(app).get("/metrics");
    expect(res.text).toMatch(
      /http_requests_total\{[^}]*route="\/api\/health"[^}]*status_code="200"[^}]*\}\s+\d+/
    );
  });
});