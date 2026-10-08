const fs = require("node:fs/promises");
const {
  test,
  expect,
  clickAndMark,
  openDashboard,
  installSpeechMonitor,
  installMockSpeechRecognition,
} = require("./support/evidence");

test("08 - Asistente: descarga local del detalle", async ({ page, evidence }) => {
  evidence.recordVideo();
  await installSpeechMonitor(page);
  await openDashboard(page, evidence);
  const requestField = page.locator("#asistente-solicitud");
  await clickAndMark(
    page,
    evidence,
    requestField,
    "Activar el campo de solicitud del asistente.",
  );
  await requestField.fill("descarga el detalle filtrado");

  const downloadPromise = page.waitForEvent("download");
  await clickAndMark(
    page,
    evidence,
    page.locator("#asistente-enviar"),
    "Enviar la orden local de descarga del detalle.",
  );
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toContain("detalle_oferta_quirurgica");
  await expect(page.locator("#asistente-respuesta")).toContainText(
    "descargué el detalle filtrado",
    { timeout: 15000 },
  );
  await expect
    .poll(() => page.evaluate(() => window.__quironSpokenUtterances || []))
    .toContainEqual(
      expect.objectContaining({
        text: expect.stringContaining("descargué el detalle filtrado"),
        lang: "es-CO",
      }),
    );
  const responseText = await page.locator("#asistente-respuesta").innerText();
  evidence.setNarrationText(responseText);
  evidence.addStep(
    "Comprobar que la respuesta se envió a speechSynthesis en español colombiano y preparar video con voz narrada.",
  );

  const filePath = await download.path();
  expect(filePath).not.toBeNull();
  const content = (await fs.readFile(filePath, "utf8")).replace(/^\uFEFF/, "");
  expect(content.split(/\r?\n/, 1)[0]).toContain("sede_id");
  expect(content.split(/\r?\n/).length).toBeGreaterThan(1);
});

test("10 - Dictado por voz y respuesta hablada", async ({ page, evidence }) => {
  evidence.recordVideo();
  await installSpeechMonitor(page);
  await installMockSpeechRecognition(page);
  await openDashboard(page, evidence);

  const microphone = page.getByRole("button", { name: "Dictar solicitud por voz" });
  await clickAndMark(
    page,
    evidence,
    microphone,
    "Iniciar dictado pulsando «Hablar».",
  );
  const activeMicrophone = page.locator("#asistente-microfono");
  await expect(activeMicrophone).toHaveText("Detener");
  evidence.addStep(
    "Comprobar que el botón entra en estado de escucha después del evento de inicio del micrófono.",
  );

  await page.evaluate(() => {
    window.__quironMockRecognition.emitFinalTranscript(
      "descarga el detalle filtrado",
    );
  });
  evidence.addStep(
    "Simular una transcripción final reconocida por el navegador: «descarga el detalle filtrado».",
  );

  const downloadPromise = page.waitForEvent("download");
  await clickAndMark(
    page,
    evidence,
    page.getByRole("button", { name: "Detener dictado" }),
    "Detener el micrófono y enviar la transcripción al asistente.",
  );
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toContain("detalle_oferta_quirurgica");
  await expect(page.locator("#asistente-respuesta")).toContainText(
    "descargué el detalle filtrado",
    { timeout: 15000 },
  );
  await expect
    .poll(() => page.evaluate(() => window.__quironSpokenUtterances || []))
    .toContainEqual(
      expect.objectContaining({
        text: expect.stringContaining("descargué el detalle filtrado"),
        lang: "es-CO",
      }),
    );

  const responseText = await page.locator("#asistente-respuesta").innerText();
  evidence.setNarrationText(responseText);
  evidence.addStep(
    "Verificar que el asistente pidió a speechSynthesis reproducir su respuesta en español colombiano; el MP4 incorpora una narración audible.",
  );
  await page.locator(".panel-kpis").scrollIntoViewIfNeeded();
  const downloadPath = await download.path();
  expect(downloadPath).not.toBeNull();
  const content = (await fs.readFile(downloadPath, "utf8")).replace(/^\uFEFF/, "");
  expect(content.split(/\r?\n/, 1)[0]).toContain("sede_id");
});
