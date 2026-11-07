const { test, expect, openDashboard, captureEvidence } = require("./support/evidence");

const CSV_VALIDO = [
  "SEDE -NOMBRE;DIRECCION;TELEFONO;CORREO ELECTRÓNICO;NATURALEZA;TIPO DE PRESTADOR;213 - CIRUGÍA PLÁSTICA Y ESTÉTICA;369 - CIRUGÍA ESTÉTICA",
  "Clínica ETL;Calle 1 # 2-3;6010000000;etl@example.com;Privada;IPS;X;",
].join("\n");

const CSV_INVALIDO = [
  "nombre;direccion",
  "Clínica sin esquema;Calle 1",
].join("\n");

async function cargarCsv(page, nombre, contenido) {
  await page
    .locator("#etl-carga-csv input[type=file]")
    .setInputFiles({
      name: nombre,
      mimeType: "text/csv",
      buffer: Buffer.from(contenido, "utf8"),
    });
}

test("12 - Carga CSV y trazabilidad del proceso ETL", async ({ page, evidence }) => {
  await openDashboard(page, evidence);
  const historico = page.locator("#etl-tabla-historico");
  const mapeo = page.locator("#etl-tabla-mapeo");

  await expect(historico).toContainText("Extracción");
  await expect(mapeo).toContainText("Campo origen");
  await expect(page.locator("#etl-estado")).toContainText("SHA-256");
  evidence.addStep(
    "Verificar el histórico y mapeo de campos de la carga inicial.",
  );

  await cargarCsv(page, "etl-fixture.csv", CSV_VALIDO);
  await expect(page.locator("#etl-estado")).toContainText(
    "etl-fixture.csv",
    { timeout: 30000 },
  );
  await expect(page.locator("#kpi-sedes-oferta")).toHaveText("1");
  await expect(historico).toContainText("Geocodificación");
  await expect(mapeo).toContainText("sede_id");
  await expect(mapeo).toContainText("No se reutilizan coordenadas");
  await expect(page.locator("#mapa-oferta-quirurgica")).toContainText(
    "CSV distinto a la fuente original",
  );
  evidence.addStep(
    "Cargar un CSV compatible y comprobar la actualización del dataset y el motivo por el que no se muestran coordenadas.",
  );
  await captureEvidence(
    page,
    evidence,
    "El CSV válido actualiza el indicador, conserva la traza y evita reutilizar coordenadas de otra fuente.",
    page.locator(".panel-etl"),
  );

  await cargarCsv(page, "etl-invalido.csv", CSV_INVALIDO);
  await expect(page.locator("#etl-panel-errores")).toBeVisible();
  await expect(page.locator("#etl-panel-errores")).toContainText(
    "columnas obligatorias",
    { timeout: 30000 },
  );
  await expect(page.locator("#kpi-sedes-oferta")).toHaveText("1");
  await expect(historico).toContainText("Validación");
  evidence.addStep(
    "Cargar un CSV con esquema inválido y comprobar el error visible y la conservación del dataset válido.",
  );
  await captureEvidence(
    page,
    evidence,
    "El archivo inválido informa el error, se conserva el último dataset válido y el historial registra el intento.",
    page.locator(".panel-etl"),
  );
});
