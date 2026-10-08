const fs = require("node:fs/promises");
const {
  test,
  expect,
  clickAndMark,
  selectFirstService,
  openDashboard,
  waitForMapReady,
} = require("./support/evidence");

async function downloadCsv(page, evidence, buttonName) {
  const downloadPromise = page.waitForEvent("download");
  await clickAndMark(
    page,
    evidence,
    page.getByRole("button", { name: buttonName }),
    `Pulsar «${buttonName}» para descargar el CSV.`,
  );
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toMatch(/^quiron_[a-z_]+_\d{8}_\d{6}\.csv$/);
  const filePath = await download.path();
  expect(filePath).not.toBeNull();
  const content = (await fs.readFile(filePath, "utf8")).replace(/^\uFEFF/, "");
  return { download, content };
}

test("04 - Descarga del detalle filtrado", async ({ page, evidence }) => {
  await openDashboard(page, evidence);
  const serviceLabel = await selectFirstService(page, evidence);
  await waitForMapReady(page);
  const serviceCode = serviceLabel.split(" · ", 1)[0];
  const { download, content } = await downloadCsv(
    page,
    evidence,
    "Descargar detalle filtrado",
  );

  expect(download.suggestedFilename()).toContain("detalle_oferta_quirurgica");
  const [header, ...rows] = content.trim().split(/\r?\n/);
  const columns = header.split(",");
  const serviceColumn = columns.indexOf("codigo_servicio");
  expect(columns).toContain("sede_id");
  expect(serviceColumn).toBeGreaterThanOrEqual(0);
  expect(rows.length).toBeGreaterThan(0);
  expect(rows.every((row) => row.includes(`,${serviceCode},`))).toBeTruthy();
});

test("05 - Descarga del resumen por servicio", async ({ page, evidence }) => {
  await openDashboard(page, evidence);
  const { download, content } = await downloadCsv(
    page,
    evidence,
    "Descargar resumen por servicio",
  );

  expect(download.suggestedFilename()).toContain("resumen_por_servicio");
  const rows = content.trim().split(/\r?\n/);
  expect(rows[0]).toBe("codigo_servicio,nombre_servicio,sedes");
  expect(rows.length).toBeGreaterThan(1);
});

test("06 - Descarga del resumen por naturaleza", async ({ page, evidence }) => {
  await openDashboard(page, evidence);
  const { download, content } = await downloadCsv(
    page,
    evidence,
    "Descargar resumen por naturaleza",
  );

  expect(download.suggestedFilename()).toContain("resumen_por_naturaleza");
  const rows = content.trim().split(/\r?\n/);
  expect(rows[0]).toBe("naturaleza,sedes");
  expect(rows.length).toBeGreaterThan(1);
});

test("07 - Descarga de metadata y trazabilidad", async ({ page, evidence }) => {
  await openDashboard(page, evidence);
  const { download, content } = await downloadCsv(
    page,
    evidence,
    "Descargar metadata y trazabilidad",
  );

  expect(download.suggestedFilename()).toContain("metadata_trazabilidad");
  const rows = content.trim().split(/\r?\n/);
  expect(rows[0]).toBe("campo,valor");
  expect(rows.some((row) => row.startsWith("entidad_publicadora,"))).toBeTruthy();
  expect(rows.some((row) => row.startsWith("cobertura_datos_total_registros,"))).toBeTruthy();
});
