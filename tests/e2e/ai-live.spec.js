const {
  test,
  expect,
  clickAndMark,
  captureEvidence,
  openDashboard,
  waitForMapReady,
  installSpeechMonitor,
} = require("./support/evidence");

test.describe("Integración opcional con Gemini real", () => {
  test.skip(
    process.env.E2E_LIVE_GEMINI !== "1",
    "Activa E2E_LIVE_GEMINI=1 para usar las credenciales configuradas en .env.",
  );

  test("11 - Gemini real interpreta texto y modifica los filtros", async ({
    page,
    evidence,
  }) => {
    evidence.recordVideo();
    await installSpeechMonitor(page);
    await openDashboard(page, evidence);
    const initialOffers = Number(
      (await page.locator("#kpi-sedes-oferta").innerText()).replace(/\D/g, ""),
    );

    const requestField = page.locator("#asistente-solicitud");
    await clickAndMark(
      page,
      evidence,
      requestField,
      "Escribir una solicitud simple, en español, para el servicio real de Gemini.",
    );
    await requestField.fill("filtra las sedes públicas");
    await clickAndMark(
      page,
      evidence,
      page.locator("#asistente-enviar"),
      "Enviar la solicitud al servicio Gemini configurado en el .env.",
    );
    await expect(page.locator("#asistente-respuesta")).toContainText(
      "apliqué los filtros solicitados",
      { timeout: 90000 },
    );
    await expect(page.locator("#filtro-naturaleza")).toContainText("Pública");
    await expect
      .poll(async () =>
        Number(
          (await page.locator("#kpi-sedes-oferta").innerText()).replace(
            /\D/g,
            "",
          ),
        ),
      )
      .toBeLessThan(initialOffers);
    const filteredOffers = Number(
      (await page.locator("#kpi-sedes-oferta").innerText()).replace(/\D/g, ""),
    );
    expect(filteredOffers).toBeLessThan(initialOffers);
    await expect(page.locator("#kpi-sedes-privadas")).toHaveText("0");

    const mapState = await waitForMapReady(page);
    evidence.addStep(
      `Gemini real interpretó la instrucción y Quirón aplicó el filtro público; sedes ${initialOffers} → ${filteredOffers}; mapa cargado=${mapState.mapLoaded}.`,
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
      "Indicadores actualizados por la acción devuelta por Gemini.",
      page.locator(".panel-kpis"),
    );
  });
});
