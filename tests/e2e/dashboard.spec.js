const {
  test,
  expect,
  clickAndMark,
  captureEvidence,
  selectFirstService,
  openDashboard,
  waitForMapReady,
} = require("./support/evidence");

test("01 - Carga inicial del dashboard", async ({ page, evidence }) => {
  await openDashboard(page, evidence);

  await expect(page).toHaveTitle("Quirón · Oferta Quirúrgica de Bogotá D.C.");
  await expect(page.getByRole("heading", { name: "Quirón", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Explorar la oferta" })).toBeVisible();
  await expect(page.locator("#kpi-sedes-totales")).not.toBeEmpty();
  await expect(page.locator("#kpi-sedes-oferta")).not.toBeEmpty();
  await expect(page.locator("#mapa-oferta-quirurgica .js-plotly-plot")).toBeVisible();
  await expect(page.locator("#mapa-sedes-visibles")).not.toBeEmpty();
  await expect(page.locator("#mapa-sedes-sin-coordenadas")).not.toBeEmpty();
  await expect(page.locator("#mapa-cobertura")).not.toBeEmpty();
  await expect(page.getByRole("heading", { name: "Descargar resultados" })).toBeVisible();
  evidence.addStep(
    "Verificar el título, los indicadores, el mapa y la zona de descargas.",
  );
  await page.locator("#titulo-filtros").scrollIntoViewIfNeeded();
  await captureEvidence(
    page,
    evidence,
    "Vista inicial con la identidad, trazabilidad, filtros e indicadores del dashboard.",
  );
  await page.locator("#mapa-oferta-quirurgica").scrollIntoViewIfNeeded();
  await captureEvidence(
    page,
    evidence,
    "Mapa de la oferta visible y renderizado en el navegador.",
    page.locator("#mapa-oferta-quirurgica"),
  );
});

test("02 - Filtrar y restablecer resultados", async ({ page, evidence }) => {
  await openDashboard(page, evidence);
  const metricSelectors = [
    "#kpi-sedes-totales",
    "#kpi-sedes-oferta",
    "#kpi-tipos-servicio",
    "#kpi-sedes-publicas",
    "#kpi-sedes-privadas",
    "#mapa-sedes-visibles",
    "#mapa-sedes-sin-coordenadas",
  ];
  const readMetrics = async () =>
    Object.fromEntries(
      await Promise.all(
        metricSelectors.map(async (selector) => [
          selector,
          (await page.locator(selector).innerText()).trim(),
        ]),
      ),
    );
  const initialMetrics = await readMetrics();
  const initialOffers = parseDashboardCount(initialMetrics["#kpi-sedes-oferta"]);
  const initialMapped = parseDashboardCount(initialMetrics["#mapa-sedes-visibles"]);
  evidence.addStep(
    `Registrar los valores iniciales de los indicadores: ${initialMetrics["#kpi-sedes-oferta"]} sedes con oferta, ${initialMetrics["#kpi-tipos-servicio"]} códigos quirúrgicos y ${initialMapped} sedes visibles en el mapa.`,
  );

  const serviceLabel = await selectFirstService(page, evidence);
  await expect(page.locator("#estado-filtros")).toContainText(
    "Resultado filtrado",
    { timeout: 15000 },
  );
  const filteredMetrics = await readMetrics();
  const filteredOffers = parseDashboardCount(
    filteredMetrics["#kpi-sedes-oferta"],
  );
  const filteredMapped = parseDashboardCount(
    filteredMetrics["#mapa-sedes-visibles"],
  );

  expect(
    filteredOffers,
    "El KPI de sedes con oferta debe disminuir al filtrar por un solo servicio.",
  ).toBeLessThan(initialOffers);
  expect(
    filteredMetrics["#kpi-tipos-servicio"],
    "El KPI de códigos quirúrgicos debe reflejar el único servicio seleccionado.",
  ).toBe("1");
  expect(
    filteredMapped,
    "El número de sedes visibles en el mapa debe disminuir para el servicio filtrado.",
  ).toBeLessThan(initialMapped);
  expect(filteredMetrics["#kpi-sedes-totales"]).toBe(
    initialMetrics["#kpi-sedes-totales"],
  );
  const filteredMap = await waitForMapReady(page);
  evidence.addStep(
    `Esperar el nuevo render cartográfico tras el filtro; mapa cargado=${filteredMap.mapLoaded}, estilo cargado=${filteredMap.styleLoaded}, lienzo=${filteredMap.canvasWidth}×${filteredMap.canvasHeight}.`,
  );
  evidence.addStep(
    `Seleccionar «${serviceLabel}» debe actualizar los indicadores: sedes ${initialMetrics["#kpi-sedes-oferta"]} → ${filteredMetrics["#kpi-sedes-oferta"]}, códigos quirúrgicos ${initialMetrics["#kpi-tipos-servicio"]} → ${filteredMetrics["#kpi-tipos-servicio"]}, sedes visibles ${initialMapped} → ${filteredMapped}.`,
  );
  await captureEvidence(
    page,
    evidence,
    `Indicadores después de seleccionar «${serviceLabel}»; se comprueba visualmente la variación de los conteos.`,
    page.locator(".panel-kpis"),
  );

  await clickAndMark(
    page,
    evidence,
    page.getByRole("button", { name: "Limpiar filtros" }),
    "Pulsar «Limpiar filtros» para restablecer el dashboard.",
  );
  await expect(page.locator("#estado-filtros")).toContainText(
    "Mostrando toda la oferta quirúrgica registrada",
    { timeout: 15000 },
  );
  await expect
    .poll(readMetrics, {
      message: "Los indicadores y el mapa deben volver a sus valores iniciales al limpiar.",
    })
    .toEqual(initialMetrics);
  await waitForMapReady(page);
  evidence.addStep(
    "Verificar que todos los indicadores y los conteos del mapa vuelven exactamente a los valores iniciales.",
  );
  await captureEvidence(
    page,
    evidence,
    "Indicadores restaurados tras limpiar los filtros.",
    page.locator(".panel-kpis"),
  );
});

test("03 - Búsqueda sin coincidencias y recuperación", async ({ page, evidence }) => {
  await openDashboard(page, evidence);
  const search = page.locator("#filtro-texto-sede");
  await clickAndMark(page, evidence, search, "Activar la búsqueda de sedes.");
  await search.fill("zz-sede-e2e-sin-coincidencias");
  evidence.addStep("Escribir un nombre inexistente y confirmar la búsqueda con Enter.");
  await search.press("Enter");

  await expect(page.locator("#estado-filtros")).toContainText(
    "No se encontraron sedes",
    { timeout: 15000 },
  );
  await waitForMapReady(page);
  await captureEvidence(
    page,
    evidence,
    "Mensaje presentado cuando la búsqueda no encuentra sedes.",
  );
  await clickAndMark(
    page,
    evidence,
    page.getByRole("button", { name: "Limpiar filtros" }),
    "Pulsar «Limpiar filtros» y recuperar la oferta completa.",
  );
  await expect(page.locator("#estado-filtros")).toContainText(
    "Mostrando toda la oferta quirúrgica registrada",
    { timeout: 15000 },
  );
});

function parseDashboardCount(value) {
  const digits = value.replace(/[^\d]/g, "");
  if (!digits) {
    throw new Error(`El indicador no contiene un número: "${value}"`);
  }
  return Number(digits);
}
