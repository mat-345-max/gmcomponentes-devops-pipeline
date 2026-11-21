const request = require("supertest");
const app = require("../app");

describe("correlación de peticiones con el agente", () => {
  let fetchEspia;

  beforeEach(() => {
    fetchEspia = jest.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({ answer: "hola" }),
    });
  });

  afterEach(() => {
    fetchEspia.mockRestore();
  });

  it("reenvía el X-Request-ID al servicio de agentes", async () => {
    const res = await request(app)
      .post("/api/agent/chat")
      .set("X-Request-ID", "trace-12345678")
      .send({ message: "hola" });

    expect(res.statusCode).toBe(200);
    expect(fetchEspia).toHaveBeenCalledTimes(1);
    const opciones = fetchEspia.mock.calls[0][1];
    expect(opciones.headers["X-Request-ID"]).toBe("trace-12345678");
  });

  it("genera un id y lo reenvía cuando la petición no trae uno", async () => {
    await request(app).post("/api/agent/chat").send({ message: "hola" });

    const opciones = fetchEspia.mock.calls[0][1];
    expect(opciones.headers["X-Request-ID"]).toBeTruthy();
  });
});