const request = require("supertest");
const app = require("../app");

describe("requestLogger", () => {
  let escrituras;
  let espia;

  beforeEach(() => {
    escrituras = [];
    espia = jest.spyOn(process.stdout, "write").mockImplementation((texto) => {
      escrituras.push(String(texto));
      return true;
    });
  });

  afterEach(() => {
    espia.mockRestore();
  });

  function registrosHttp() {
    return escrituras
      .map((texto) => {
        try {
          return JSON.parse(texto);
        } catch (error) {
          return null;
        }
      })
      .filter((linea) => linea && linea.message === "http_request");
  }

  it("genera un X-Request-ID y lo escribe en el log como JSON", async () => {
    const res = await request(app).get("/ruta-que-no-existe");
    const id = res.headers["x-request-id"];
    expect(id).toBeTruthy();

    const [registro] = registrosHttp();
    expect(registro).toMatchObject({
      level: "warn",
      service: "groq-proxy",
      request_id: id,
      method: "GET",
      route: "sin_ruta",
      status_code: 404,
    });
    expect(typeof registro.duration_ms).toBe("number");
  });

  it("respeta el X-Request-ID que llega en la petición", async () => {
    const res = await request(app)
      .get("/ruta-que-no-existe")
      .set("X-Request-ID", "abc-12345678");
    expect(res.headers["x-request-id"]).toBe("abc-12345678");
    expect(registrosHttp()[0].request_id).toBe("abc-12345678");
  });

  it("descarta un X-Request-ID con formato inválido", async () => {
    const res = await request(app)
      .get("/ruta-que-no-existe")
      .set("X-Request-ID", "mal formato!!");
    expect(res.headers["x-request-id"]).not.toBe("mal formato!!");
  });

  it("no registra el health check ni /metrics", async () => {
    await request(app).get("/api/health");
    await request(app).get("/metrics");
    expect(registrosHttp()).toHaveLength(0);
  });
});