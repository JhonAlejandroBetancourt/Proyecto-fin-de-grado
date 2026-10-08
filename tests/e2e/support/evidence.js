const fs = require("node:fs/promises");
const path = require("node:path");
const os = require("node:os");
const { spawnSync } = require("node:child_process");
const { PDFDocument, StandardFonts, rgb } = require("pdf-lib");
const { test: base, expect } = require("@playwright/test");

const PROJECT_ROOT = path.resolve(__dirname, "../../..");
const REPORT_DIR = path.join(PROJECT_ROOT, "reportes", "pruebas_funcionales");

const SCENARIOS = {
  "01": {
    title: "Carga inicial del dashboard",
    description:
      "Comprueba que Quirón abre correctamente y presenta su identidad, indicadores principales, filtros, panel cartográfico y zona de exportación.",
  },
  "02": {
    title: "Filtrar y restablecer resultados",
    description:
      "Compara los KPI de sedes, códigos quirúrgicos y cobertura del mapa antes y después de filtrar por servicio; limpia los filtros y comprueba que todos recuperan exactamente sus valores iniciales.",
  },
  "03": {
    title: "Búsqueda sin coincidencias y recuperación",
    description:
      "Busca un nombre deliberadamente inexistente, comprueba el mensaje de cero resultados y restablece el dashboard.",
  },
  "04": {
    title: "Descarga del detalle filtrado",
    description:
      "Filtra por servicio, descarga el detalle y comprueba que el CSV contiene registros correspondientes al filtro.",
  },
  "05": {
    title: "Descarga del resumen por servicio",
    description:
      "Descarga el resumen por código de servicio y comprueba el nombre, los encabezados y las filas del archivo CSV.",
  },
  "06": {
    title: "Descarga del resumen por naturaleza",
    description:
      "Descarga el resumen por naturaleza jurídica y comprueba las categorías y cantidades del archivo CSV.",
  },
  "07": {
    title: "Descarga de metadata y trazabilidad",
    description:
      "Descarga la metadata y comprueba que incluye procedencia y contexto del conjunto de datos.",
  },
  "08": {
    title: "Asistente: descarga local del detalle",
    description:
      "Envía una orden de descarga reconocida localmente por el asistente y comprueba la respuesta y el CSV, sin llamar a Gemini.",
  },
  "09": {
    title: "Texto procesado por Gemini aplica una acción",
    description:
      "Envía texto en lenguaje natural, verifica la solicitud-respuesta del servicio compatible con Gemini y comprueba que el filtro modifica indicadores y mapa.",
  },
  "10": {
    title: "Dictado por voz y respuesta hablada",
    description:
      "Simula el reconocimiento de voz, ejecuta la acción correspondiente y comprueba que el asistente solicita reproducir su respuesta en español.",
  },
  "11": {
    title: "Gemini real interpreta texto y modifica los filtros",
    description:
      "Envía una solicitud de prueba a Gemini real y comprueba que su respuesta cambia los filtros e indicadores del dashboard.",
  },
};

const test = base.extend({
  evidence: async ({ page }, use, testInfo) => {
    testInfo.evidenceSteps = [];
    testInfo.evidenceScreenshots = [];
    testInfo.videoFrames = [];
    await use({
      title: testInfo.title,
      evidenceSteps: testInfo.evidenceSteps,
      evidenceScreenshots: testInfo.evidenceScreenshots,
      setNarrationText: (text) => {
        testInfo.narrationText = text;
        testInfo.narrationAt = Date.now();
      },
      recordVideo: () => {
        testInfo.recordNarrationVideo = true;
      },
      isVideoEnabled: () => testInfo.recordNarrationVideo === true,
      addVideoFrame: (filePath) => {
        if (testInfo.recordNarrationVideo) {
          testInfo.videoFrames.push({
            path: filePath,
            recordedAt: Date.now(),
          });
        }
      },
      addStep: (description) => testInfo.evidenceSteps.push(description),
    });
    const finalScreenshot = path.join(
      REPORT_DIR,
      `${scenarioFileStem(testInfo)}.png`,
    );
    await fs.mkdir(REPORT_DIR, { recursive: true });
    await page.screenshot({
      path: finalScreenshot,
      animations: "disabled",
    });
    testInfo.evidenceScreenshots.push({
      path: finalScreenshot,
      step: "Estado final tras completar las comprobaciones del escenario.",
      number: null,
      label: "Resultado final",
    });
    let videoError = null;
    if (testInfo.recordNarrationVideo && testInfo.narrationText) {
      try {
        testInfo.videoFrames.push({
          path: finalScreenshot,
          recordedAt: Date.now(),
        });
        await saveNarratedVideo(testInfo);
      } catch (error) {
        videoError = error;
        testInfo.evidenceSteps.push(
          `No se pudo generar el video hablado: ${error.message}`,
        );
      }
    }
    await writeEvidence(testInfo, videoError);
    if (videoError) {
      throw videoError;
    }
  },
});

async function clickAndMark(page, evidence, locator, description) {
  await locator.scrollIntoViewIfNeeded();
  await locator.waitFor({ state: "visible" });
  const box = await locator.boundingBox();
  if (!box) {
    throw new Error(`No se pudo localizar el control: ${description}`);
  }

  const markerNumber = evidence.evidenceSteps.length + 1;
  const screenshotPath = path.join(
    REPORT_DIR,
    `${scenarioFileStem(evidence)}_paso_${String(markerNumber).padStart(2, "0")}.png`,
  );
  await page.evaluate(
    ({ x, y, number }) => {
      document
        .querySelectorAll("[data-e2e-click-marker]")
        .forEach((marker) => marker.remove());
      const marker = document.createElement("div");
      marker.textContent = String(number);
      marker.dataset.e2eClickMarker = "true";
      marker.setAttribute("aria-hidden", "true");
      Object.assign(marker.style, {
        position: "fixed",
        left: `${x}px`,
        top: `${y}px`,
        width: "32px",
        height: "32px",
        transform: "translate(-50%, -50%)",
        display: "grid",
        placeItems: "center",
        border: "3px solid white",
        borderRadius: "50%",
        background: "#c62828",
        color: "white",
        font: "700 17px Arial, sans-serif",
        boxShadow: "0 1px 8px #222",
        pointerEvents: "none",
        zIndex: "2147483647",
      });
      document.body.appendChild(marker);
    },
    {
      x: box.x + box.width / 2,
      y: box.y + box.height / 2,
      number: markerNumber,
    },
  );

  evidence.addStep(description);
  await locator.click();
  await fs.mkdir(REPORT_DIR, { recursive: true });
  await page.screenshot({
    path: screenshotPath,
    animations: "disabled",
  });
  evidence.addVideoFrame(screenshotPath);
  evidence.evidenceScreenshots.push({
    path: screenshotPath,
    step: description,
    number: markerNumber,
    label: `Paso ${markerNumber}`,
  });
}

async function captureEvidence(page, evidence, description, locator = null) {
  let screenshotPath = path.join(
    REPORT_DIR,
    `${scenarioFileStem(evidence)}_evidencia_${String(
      evidence.evidenceScreenshots.length + 1,
    ).padStart(2, "0")}.png`,
  );
  await fs.mkdir(REPORT_DIR, { recursive: true });
  if (evidence.isVideoEnabled()) {
    if (locator) {
      await locator.scrollIntoViewIfNeeded();
      const videoFramePath = screenshotPath.replace(".png", "_video.png");
      await page.screenshot({
        path: videoFramePath,
        animations: "disabled",
      });
      evidence.addVideoFrame(videoFramePath);
    } else {
      await page.screenshot({
        path: screenshotPath,
        animations: "disabled",
      });
      evidence.addVideoFrame(screenshotPath);
    }
  }
  if (locator) {
    await locator.scrollIntoViewIfNeeded();
    await locator.screenshot({
      path: screenshotPath,
      animations: "disabled",
    });
  } else {
    if (!evidence.isVideoEnabled()) {
      await page.screenshot({
        path: screenshotPath,
        animations: "disabled",
      });
    }
  }
  evidence.evidenceScreenshots.push({
    path: screenshotPath,
    step: description,
    number: null,
    label: "Comprobación visual",
  });
}

async function selectFirstService(page, evidence) {
  await clickAndMark(
    page,
    evidence,
    page.locator("#filtro-servicio"),
    "Abrir el selector de servicio quirúrgico.",
  );
  const option = page.getByRole("option").first();
  await option.waitFor({ state: "visible" });
  const label = await option.innerText();
  await clickAndMark(
    page,
    evidence,
    option,
    `Seleccionar el primer servicio disponible: ${label}.`,
  );
  return label;
}

async function openDashboard(page, evidence) {
  await page.goto("/");
  await expect(page).toHaveTitle("Quirón · Oferta Quirúrgica de Bogotá D.C.");
  await waitForMapReady(page);
  evidence.addStep(
    "Esperar a que Plotly, el estilo cartográfico, el lienzo y las teselas del mapa estén cargados antes de continuar.",
  );
}

async function waitForMapReady(page, timeout = 90000) {
  const graph = page.locator("#mapa-oferta-quirurgica .js-plotly-plot");
  await graph.waitFor({ state: "visible" });
  const failedRequests = [];
  const onRequestFailed = (request) => {
    failedRequests.push(
      `${request.url()}: ${request.failure()?.errorText || "fallo de red"}`,
    );
  };
  page.on("requestfailed", onRequestFailed);
  const deadline = Date.now() + timeout;
  let state = {};
  try {
    while (Date.now() < deadline) {
      state = await graph.evaluate((element) => {
        const traces = element._fullData || [];
        const mapFigure = element._fullLayout?.map;
        const map = mapFigure?._subplot?.map;
        const canvas = element.querySelector(".maplibregl-canvas");
        const annotation =
          element.querySelector(".annotation-text")?.textContent || "";
        const emptyMap = traces.length === 0 && Boolean(annotation.trim());
        return {
          traces: traces.length,
          mapExists: Boolean(map),
          styleLoaded:
            typeof map?.isStyleLoaded === "function"
              ? map.isStyleLoaded()
              : false,
          mapLoaded:
            typeof map?.loaded === "function" ? map.loaded() : false,
          canvasWidth: canvas?.width || 0,
          canvasHeight: canvas?.height || 0,
          emptyMap,
          annotation,
        };
      });
      const emptyMapReady = state.emptyMap;
      const plottedMapReady =
        state.traces > 0 &&
        state.mapExists &&
        state.styleLoaded &&
        state.mapLoaded &&
        state.canvasWidth > 0 &&
        state.canvasHeight > 0;
      if (emptyMapReady || plottedMapReady) {
        return state;
      }
      await page.waitForTimeout(300);
    }
  } finally {
    page.off("requestfailed", onRequestFailed);
  }

  throw new Error(
    `El mapa no terminó de cargar en ${timeout} ms. ` +
      `Estado final: ${JSON.stringify(state)}. ` +
      `Solicitudes fallidas: ${failedRequests.join(" | ") || "ninguna"}.`,
  );
}

async function installSpeechMonitor(page) {
  await page.addInitScript(() => {
    const synthesis = window.speechSynthesis;
    if (!synthesis) {
      window.__quironSpokenUtterances = [];
      return;
    }
    window.__quironSpokenUtterances = [];
    synthesis.speak = (utterance) => {
      window.__quironSpokenUtterances.push({
        text: utterance.text,
        lang: utterance.lang,
      });
    };
  });
}

async function installMockSpeechRecognition(page) {
  await page.addInitScript(() => {
    class MockSpeechRecognition extends EventTarget {
      start() {
        window.__quironMockRecognition = this;
        this.dispatchEvent(new Event("start"));
      }

      stop() {
        this.dispatchEvent(new Event("end"));
      }

      emitFinalTranscript(text) {
        const alternative = { transcript: text, confidence: 1 };
        const result = { 0: alternative, length: 1, isFinal: true };
        const results = { 0: result, length: 1 };
        const event = new Event("result");
        Object.defineProperty(event, "resultIndex", { value: 0 });
        Object.defineProperty(event, "results", { value: results });
        this.dispatchEvent(event);
      }
    }

    window.SpeechRecognition = MockSpeechRecognition;
  });
}

async function readMockGeminiRequests() {
  const response = await fetch("http://127.0.0.1:8051/__requests");
  if (!response.ok) {
    throw new Error(`Gemini de prueba respondió HTTP ${response.status}.`);
  }
  return response.json();
}

async function saveNarratedVideo(testInfo) {
  if (process.platform !== "win32") {
    throw new Error(
      "La generación de video con voz requiere Windows y una voz SAPI en español.",
    );
  }

  const fileStem = scenarioFileStem(testInfo);
  const videoPath = path.join(REPORT_DIR, `${fileStem}.mp4`);
  const audioPath = path.join(os.tmpdir(), `${fileStem}-${testInfo.workerIndex}.wav`);

  try {
    if (testInfo.videoFrames.length === 0) {
      throw new Error("No se capturaron fotogramas para el video.");
    }
    synthesizeSpanishAudio(testInfo.narrationText, audioPath);
    const startDelay = Math.max(
      0,
      Number(testInfo.narrationAt || Date.now()) -
        testInfo.videoFrames[0].recordedAt -
        250,
    );
    const inputs = ["-y"];
    for (const frame of testInfo.videoFrames) {
      inputs.push(
        "-loop",
        "1",
        "-framerate",
        "2",
        "-t",
        "2.5",
        "-i",
        frame.path,
      );
    }
    inputs.push("-i", audioPath);
    const videoFilters = testInfo.videoFrames
      .map(
        (_, index) =>
          `[${index}:v:0]scale=1280:720:force_original_aspect_ratio=decrease,` +
          "pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=24," +
          `format=yuv420p[v${index}]`,
      )
      .join(";");
    const concatInputs = testInfo.videoFrames
      .map((_, index) => `[v${index}]`)
      .join("");
    const filter = `${videoFilters};${concatInputs}concat=n=${testInfo.videoFrames.length}:v=1:a=0[vout];` +
      `[${testInfo.videoFrames.length}:a:0]adelay=${startDelay}|${startDelay},apad[aout]`;
    runFfmpeg([
      ...inputs,
      "-filter_complex",
      filter,
      "-map",
      "[vout]",
      "-map",
      "[aout]",
      "-c:v",
      "libx264",
      "-preset",
      "veryfast",
      "-crf",
      "28",
      "-pix_fmt",
      "yuv420p",
      "-c:a",
      "aac",
      "-b:a",
      "128k",
      "-shortest",
      "-movflags",
      "+faststart",
      videoPath,
    ]);
  } finally {
    await fs.rm(audioPath, { force: true });
  }
}

function synthesizeSpanishAudio(text, outputPath) {
  const command = [
    "$ErrorActionPreference = 'Stop'",
    "Add-Type -AssemblyName System.Speech",
    "$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer",
    "$voice = $synth.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Culture.Name -like 'es-*' } | Select-Object -First 1",
    "if (-not $voice) { throw 'No hay una voz SAPI en español instalada.' }",
    "$synth.SelectVoice($voice.VoiceInfo.Name)",
    "$synth.SetOutputToWaveFile($env:E2E_TTS_OUTPUT)",
    "$synth.Speak($env:E2E_TTS_TEXT)",
    "$synth.Dispose()",
  ].join("; ");
  const result = spawnSync(
    "powershell.exe",
    ["-NoProfile", "-NonInteractive", "-Command", command],
    {
      encoding: "utf8",
      env: {
        ...process.env,
        E2E_TTS_OUTPUT: outputPath,
        E2E_TTS_TEXT: text,
      },
    },
  );
  if (result.error || result.status !== 0) {
    throw new Error(
      `No se pudo generar la narración en español: ${
        result.error?.message || result.stderr || result.stdout
      }`,
    );
  }
}

function runFfmpeg(args) {
  const result = spawnSync("ffmpeg.exe", args, {
    encoding: "utf8",
    windowsHide: true,
  });
  if (result.error || result.status !== 0) {
    throw new Error(
      `No se pudo generar el video con audio: ${
        result.error?.message || result.stderr || result.stdout
      }`,
    );
  }
}

function scenarioFileStem(testInfo) {
  const number = testInfo.title.match(/^(\d{2})/);
  const readableTitle = testInfo.title
    .replace(/^\d{2}\s*-\s*/, "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
  return `${number ? number[1] : "00"}_${readableTitle}`;
}

async function writeEvidence(testInfo, videoError) {
  await fs.mkdir(REPORT_DIR, { recursive: true });
  const fileStem = scenarioFileStem(testInfo);
  const pdfPath = path.join(REPORT_DIR, `${fileStem}.pdf`);
  const scenarioNumber = fileStem.slice(0, 2);
  const scenario = SCENARIOS[scenarioNumber] || {
    title: testInfo.title,
    description: "Prueba funcional de la plataforma Quirón.",
  };
  const baseURL = testInfo.project.use.baseURL || "http://127.0.0.1:8050";

  await createPdfReport({
    pdfPath,
    screenshotPaths: testInfo.evidenceScreenshots,
    title: scenario.title,
    description: scenario.description,
    steps: testInfo.evidenceSteps,
    result: videoError
      ? "FALLIDA"
      : testInfo.status === "passed"
        ? "APROBADA"
        : testInfo.status === "skipped"
          ? "OMITIDA"
          : "FALLIDA",
    baseURL,
    scenarioNumber,
    narrationText: testInfo.narrationText,
  });
}

async function createPdfReport({
  pdfPath,
  screenshotPaths,
  title,
  description,
  steps,
  result,
  baseURL,
  scenarioNumber,
  narrationText,
}) {
  const document = await PDFDocument.create();
  document.setTitle(`${scenarioNumber} - ${title}`);
  document.setAuthor("Pruebas funcionales de Quirón");
  const regular = await document.embedFont(StandardFonts.Helvetica);
  const bold = await document.embedFont(StandardFonts.HelveticaBold);
  const [pageWidth, pageHeight] = [842, 595];
  const margin = 34;
  const purple = rgb(0.2, 0.04, 0.4);
  const muted = rgb(0.35, 0.32, 0.42);
  const cover = document.addPage([pageWidth, pageHeight]);
  drawHeader(cover, bold, regular, purple, muted, margin, pageWidth);
  let y = pageHeight - 86;
  y = drawParagraph(
    cover,
    `${scenarioNumber} - ${title}`,
    bold,
    19,
    margin,
    y,
    pageWidth - 2 * margin,
    purple,
    25,
  );
  cover.drawRectangle({
    x: margin,
    y: y - 23,
    width: 103,
    height: 19,
    color: result === "APROBADA" ? rgb(0.88, 0.95, 0.9) : rgb(0.99, 0.89, 0.89),
  });
  cover.drawText(`Resultado: ${result}`, {
    x: margin + 7,
    y: y - 18,
    font: bold,
    size: 9,
    color: result === "APROBADA" ? rgb(0.12, 0.4, 0.25) : rgb(0.65, 0.1, 0.1),
  });
  y -= 42;

  for (const [label, value] of [
    ["Objetivo", description],
    ["Aplicación", baseURL],
    [
      "Fecha",
      new Date().toLocaleString("es-CO", { timeZone: "America/Bogota" }),
    ],
    ...(narrationText ? [["Texto de voz reproducido", narrationText]] : []),
  ]) {
    y = drawLabeledParagraph(
      cover,
      label,
      value,
      bold,
      regular,
      margin,
      y,
      pageWidth - 2 * margin,
    );
    y -= 5;
  }

  y -= 5;
  cover.drawText("Pasos ejecutados", {
    x: margin,
    y,
    font: bold,
    size: 12,
    color: purple,
  });
  y -= 20;
  const reportSteps = steps.length
    ? steps
    : ["Comprobación visual de la carga inicial."];
  for (const [index, step] of reportSteps.entries()) {
    y = drawParagraph(
      cover,
      `${index + 1}. ${step}`,
      regular,
      8.5,
      margin + 5,
      y,
      pageWidth - 2 * margin - 5,
      muted,
      11,
    );
    y -= 4;
  }

  cover.drawText(
    "Las capturas siguientes muestran el resultado de cada paso; los círculos numerados señalan los clics.",
    {
      x: margin,
      y: 22,
      font: regular,
      size: 8,
      color: muted,
    },
  );

  for (const screenshot of screenshotPaths) {
    const page = document.addPage([pageWidth, pageHeight]);
    drawHeader(page, bold, regular, purple, muted, margin, pageWidth);
    page.drawText(screenshot.label || "Evidencia", {
      x: margin,
      y: pageHeight - 78,
      font: bold,
      size: 14,
      color: purple,
    });
    const descriptionY = pageHeight - 98;
    const imageBytes = await fs.readFile(screenshot.path);
    const image = await document.embedPng(imageBytes);
    const descriptionLines = wrapText(
      screenshot.step,
      regular,
      8.5,
      pageWidth - 2 * margin,
    );
    descriptionLines.forEach((line, index) => {
      page.drawText(line, {
        x: margin,
        y: descriptionY - index * 11,
        font: regular,
        size: 8.5,
        color: muted,
      });
    });
    const maxImageWidth = pageWidth - 2 * margin;
    const maxImageHeight = descriptionY - descriptionLines.length * 11 - 34;
    const scale = Math.min(
      maxImageWidth / image.width,
      maxImageHeight / image.height,
    );
    const imageWidth = image.width * scale;
    const imageHeight = image.height * scale;
    page.drawImage(image, {
      x: (pageWidth - imageWidth) / 2,
      y: 26,
      width: imageWidth,
      height: imageHeight,
    });
    page.drawText(
      `Prueba ${scenarioNumber} | Página ${document.getPageCount()}`,
      {
        x: margin,
        y: 12,
        font: regular,
        size: 7,
        color: muted,
      },
    );
  }

  await writePdfWithRetry(pdfPath, await document.save());
}

async function writePdfWithRetry(pdfPath, contents) {
  const temporaryPath = `${pdfPath}.${process.pid}.tmp`;
  try {
    await fs.writeFile(temporaryPath, contents);
    for (let attempt = 0; attempt < 5; attempt += 1) {
      try {
        await fs.rename(temporaryPath, pdfPath);
        return;
      } catch (error) {
        if (!["EBUSY", "EPERM", "EACCES"].includes(error.code)) {
          throw error;
        }
        if (attempt === 4) {
          const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
          const alternatePath = pdfPath.replace(
            /\.pdf$/,
            `_generado_${timestamp}.pdf`,
          );
          await fs.rename(temporaryPath, alternatePath);
          console.warn(
            `El PDF existente está bloqueado; se guardó el informe nuevo en ${alternatePath}.`,
          );
          return;
        }
        await new Promise((resolve) => setTimeout(resolve, 250 * (attempt + 1)));
      }
    }
  } finally {
    await fs.rm(temporaryPath, { force: true });
  }
}

function drawHeader(page, bold, regular, purple, muted, margin, pageWidth) {
  page.drawText("Quirón", {
    x: margin,
    y: 559,
    font: bold,
    size: 15,
    color: purple,
  });
  page.drawText("Informe de prueba funcional", {
    x: pageWidth - margin - 150,
    y: 561,
    font: regular,
    size: 9,
    color: muted,
  });
  page.drawLine({
    start: { x: margin, y: 548 },
    end: { x: pageWidth - margin, y: 548 },
    thickness: 1.5,
    color: rgb(0.43, 0.28, 0.69),
  });
}

function drawLabeledParagraph(
  page,
  label,
  value,
  bold,
  regular,
  x,
  y,
  maxWidth,
) {
  page.drawText(`${label}:`, {
    x,
    y,
    font: bold,
    size: 8.5,
    color: rgb(0.18, 0.15, 0.24),
  });
  const labelWidth = bold.widthOfTextAtSize(`${label}: `, 8.5);
  return drawParagraph(
    page,
    value,
    regular,
    8.5,
    x + labelWidth,
    y,
    maxWidth - labelWidth,
    rgb(0.18, 0.15, 0.24),
    11,
  );
}

function drawParagraph(page, text, font, size, x, y, maxWidth, color, lineHeight) {
  const lines = wrapText(text, font, size, maxWidth);
  lines.forEach((line, index) => {
    page.drawText(line, {
      x,
      y: y - index * lineHeight,
      font,
      size,
      color,
    });
  });
  return y - lines.length * lineHeight;
}

function wrapText(text, font, size, maxWidth) {
  const normalized = String(text)
    .replace(/→/g, "->")
    .replace(/[“”]/g, '"')
    .replace(/[‘’]/g, "'");
  const words = normalized.split(/\s+/).filter(Boolean);
  const lines = [];
  let line = "";
  for (const word of words) {
    const candidate = line ? `${line} ${word}` : word;
    if (font.widthOfTextAtSize(candidate, size) <= maxWidth) {
      line = candidate;
    } else {
      if (line) {
        lines.push(line);
      }
      line = word;
    }
  }
  if (line) {
    lines.push(line);
  }
  return lines;
}

module.exports = {
  test,
  expect,
  clickAndMark,
  captureEvidence,
  selectFirstService,
  openDashboard,
  waitForMapReady,
  installSpeechMonitor,
  installMockSpeechRecognition,
  readMockGeminiRequests,
};
