const {
  test,
  expect,
  clickAndMark,
  captureEvidence,
  openDashboard,
  waitForMapReady,
  installSpeechMonitor,
  readMockGeminiRequests,
} = require("./support/evidence");

test("09 - Texto procesado por Gemini aplica una acción", async ({
  page,
  evidence,
}) => {
  test.skip(
    process.env.E2E_LIVE_GEMINI === "1",
    "El modo real usa la prueba opcional 11 y no el servidor Gemini simulado.",
  );
  evidence.recordVideo();
  await installSpeechMonitor(page);
  await openDashboard(page, evidence);
  const initialOffers = Number(
    (await page.locator("#kpi-sedes-oferta").innerText()).replace(/\D/g, ""),
  );
  const initialPrivadas = Number(
    (await page.locator("#kpi-sedes-privadas").innerText()).replace(/\D/g, ""),
  );

  const requestField = page.locator("#asistente-solicitud");
  await clickAndMark(
    page,
    evidence,
    requestField,
    "Introducir una instrucción en lenguaje natural para que la interprete el asistente.",
  );
  await requestField.fill("filtra las sedes públicas");

  const submit = page.locator("#asistente-enviar");
  await clickAndMark(
    page,
    evidence,
    submit,
    "Enviar el texto al backend para su interpretación por el modelo Gemini de prueba.",
  );
  await expect(page.locator("#asistente-respuesta")).toContainText(
    "apliqué los filtros solicitados",
    { timeout: 20000 },
  );
  await expect(page.locator("#filtro-naturaleza")).toContainText("Pública");
  await expect
    .poll(async () =>
      Number(
        (await page.locator("#kpi-sedes-oferta").innerText()).replace(/\D/g, ""),
      ),
    )
    .toBeLessThan(initialOffers);
  const filteredOffers = Number(
    (await page.locator("#kpi-sedes-oferta").innerText()).replace(/\D/g, ""),
  );
  expect(
    Number((await page.locator("#kpi-sedes-publicas").innerText()).replace(/\D/g, "")),
  ).toBeGreaterThan(0);
  await expect(page.locator("#kpi-sedes-privadas")).toHaveText("0");
  expect(initialPrivadas).toBeGreaterThan(0);
  const mapState = await waitForMapReady(page);
  evidence.addStep(
    `Verificar que la respuesta del modelo aplicó el filtro en la interfaz: sedes con oferta ${initialOffers} → ${filteredOffers}, ${await page.locator("#kpi-sedes-publicas").innerText()} sedes públicas y 0 privadas; mapa cargado=${mapState.mapLoaded}.`,
  );

  const requests = await readMockGeminiRequests();
  const aiRequest = requests.find((request) =>
    request.prompt.includes("filtra las sedes públicas"),
  );
  expect(aiRequest, "El backend no envió el texto al endpoint Gemini.").toBeDefined();
  expect(aiRequest.hasApiKey).toBe(true);
  expect(aiRequest.model).toMatch(/^[A-Za-z0-9._-]+$/);
  evidence.addStep(
    "Confirmar que el servidor envió el texto al endpoint compatible con Gemini y recibió una instrucción JSON válida.",
  );

  const responseText = await page.locator("#asistente-respuesta").innerText();
  await expect
    .poll(() => page.evaluate(() => window.__quironSpokenUtterances || []))
    .toContainEqual(
      expect.objectContaining({
        text: expect.stringContaining("apliqué los filtros solicitados"),
        lang: "es-CO",
      }),
    );
  evidence.setNarrationText(responseText);
  await captureEvidence(
    page,
    evidence,
    "Indicadores actualizados por la acción solicitada en lenguaje natural.",
    page.locator(".panel-kpis"),
  );
});
