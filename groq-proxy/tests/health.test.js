const request = require("supertest");
const app = require("../app");

describe("GET /api/health", () => {
  it("responde 200", async () => {
    const res = await request(app).get("/api/health");
    expect(res.statusCode).toBe(200);
  });
});

describe("ruta inexistente", () => {
  it("responde 404", async () => {
    const res = await request(app).get("/api/no-existe");
    expect(res.statusCode).toBe(404);
  });
});