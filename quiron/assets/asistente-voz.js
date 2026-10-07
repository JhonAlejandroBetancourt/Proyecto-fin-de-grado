(() => {
  const ids = {
    input: "asistente-solicitud",
    microphone: "asistente-microfono",
    send: "asistente-enviar",
    status: "asistente-estado",
    response: "asistente-respuesta",
    focus: "mapa-enfoque-pendiente",
  };

  function conectarAsistente() {
    const input = document.getElementById(ids.input);
    const microphone = document.getElementById(ids.microphone);
    const send = document.getElementById(ids.send);
    const status = document.getElementById(ids.status);
    const response = document.getElementById(ids.response);
    const focus = document.getElementById(ids.focus);

    if (!input || !microphone || !send || !status || !response || !focus) {
      return false;
    }

    if (microphone.dataset.voiceReady === "true") {
      return true;
    }
    microphone.dataset.voiceReady = "true";

    const Recognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    function enviarSolicitud(texto) {
      const setter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype,
        "value",
      ).set;
      setter.call(input, texto);
      input.dispatchEvent(new Event("input", { bubbles: true }));
      input.dispatchEvent(new Event("change", { bubbles: true }));
      send.click();
    }

    if (!Recognition) {
      microphone.disabled = true;
      microphone.title = "El dictado no está disponible en este navegador";
      status.textContent =
        "El dictado no está disponible en este navegador. Puedes escribir tu solicitud.";
    } else {
      const reconocimiento = new Recognition();
      reconocimiento.lang = "es-CO";
      reconocimiento.continuous = true;
      reconocimiento.interimResults = true;
      let dictadoActivo = false;
      let detenerSolicitado = false;
      let errorDictado = false;
      let transcripcion = [];

      microphone.addEventListener("click", () => {
        if (dictadoActivo) {
          detenerSolicitado = true;
          dictadoActivo = false;
          status.textContent = "Procesando el dictado…";
          reconocimiento.stop();
          return;
        }

        transcripcion = [];
        detenerSolicitado = false;
        errorDictado = false;
        try {
          dictadoActivo = true;
          reconocimiento.start();
        } catch (error) {
          dictadoActivo = false;
          if (error.name !== "InvalidStateError") {
            status.textContent =
              "No pude iniciar el micrófono. Revisa los permisos del navegador.";
          }
        }
      });

      reconocimiento.addEventListener("start", () => {
        microphone.textContent = "Detener";
        microphone.setAttribute("aria-label", "Detener dictado");
        microphone.title = "Detener dictado";
        status.textContent =
          "Escuchando. Pulsa Detener cuando termines de hablar.";
      });

      reconocimiento.addEventListener("result", (event) => {
        let textoParcial = "";
        for (
          let indice = event.resultIndex;
          indice < event.results.length;
          indice += 1
        ) {
          const resultado = event.results[indice];
          const texto = resultado[0]?.transcript?.trim();
          if (!texto) {
            continue;
          }
          if (resultado.isFinal) {
            transcripcion.push(texto);
          } else {
            textoParcial = texto;
          }
        }

        status.textContent = textoParcial
          ? `Escuchando: ${textoParcial}`
          : "Escuchando. Pulsa Detener cuando termines de hablar.";
      });

      reconocimiento.addEventListener("error", (event) => {
        dictadoActivo = false;
        errorDictado = true;
        microphone.textContent = "Hablar";
        microphone.setAttribute(
          "aria-label",
          "Dictar solicitud por voz",
        );
        microphone.title = "Dictar solicitud por voz";
        const mensajes = {
          "not-allowed":
            "No hay permiso para usar el micrófono. Puedes escribir la solicitud.",
          "no-speech": "No detecté voz. Inténtalo otra vez o escribe la solicitud.",
          network: "Falló el servicio de reconocimiento de voz del navegador.",
        };
        status.textContent =
          mensajes[event.error] ||
          "No pude reconocer la voz. Puedes escribir la solicitud.";
      });

      reconocimiento.addEventListener("end", () => {
        if (dictadoActivo && !detenerSolicitado && !errorDictado) {
          window.setTimeout(() => {
            if (!dictadoActivo || detenerSolicitado || errorDictado) {
              return;
            }
            try {
              reconocimiento.start();
            } catch (error) {
              dictadoActivo = false;
              status.textContent =
                "El dictado se interrumpió. Puedes volver a pulsar Hablar.";
              microphone.textContent = "Hablar";
              microphone.setAttribute(
                "aria-label",
                "Dictar solicitud por voz",
              );
              microphone.title = "Dictar solicitud por voz";
            }
          }, 250);
          return;
        }

        microphone.textContent = "Hablar";
        microphone.setAttribute(
          "aria-label",
          "Dictar solicitud por voz",
        );
        microphone.title = "Dictar solicitud por voz";

        const texto = transcripcion.join(" ").trim();
        if (texto) {
          enviarSolicitud(texto);
        } else if (!errorDictado) {
          status.textContent =
            "No alcancé a reconocer la voz. Inténtalo de nuevo.";
        }
      });
    }

    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        send.click();
      }
    });

    send.addEventListener("click", () => {
      if (input.value.trim()) {
        status.textContent = "Procesando la solicitud…";
      }
    });

    if ("speechSynthesis" in window) {
      const observadorRespuesta = new MutationObserver(() => {
        const texto = response.textContent.trim();
        if (!texto) {
          return;
        }
        window.speechSynthesis.cancel();
        const voz = new SpeechSynthesisUtterance(texto);
        voz.lang = "es-CO";
        window.speechSynthesis.speak(voz);
      });
      observadorRespuesta.observe(response, {
        childList: true,
        characterData: true,
        subtree: true,
      });
    }

    let ultimoEnfoque = "";
    const observadorEnfoque = new MutationObserver(() => {
      const contenido = focus.textContent.trim();
      if (!contenido) {
        return;
      }

      let comando;
      try {
        comando = JSON.parse(contenido);
      } catch {
        status.textContent = "No pude preparar el acercamiento del mapa.";
        return;
      }

      if (!comando.id || comando.id === ultimoEnfoque) {
        return;
      }
      ultimoEnfoque = comando.id;

      const grafico = document.querySelector(
        "#mapa-oferta-quirurgica .js-plotly-plot",
      );
      if (!grafico || !window.Plotly) {
        status.textContent = "No pude encontrar el mapa para acercar la sede.";
        return;
      }

      grafico.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });

      const aplicarEnfoque = () => {
        const traza = grafico._fullData?.find(
          (elemento) =>
            elemento.type === "scattermap" ||
            elemento.type === "scattermapbox",
        );
        if (!traza?.lat || !traza?.lon) {
          return;
        }

        const contieneSede = Array.from(traza.lat).some(
          (latitud, indice) =>
            Math.abs(Number(latitud) - comando.lat) < 0.00001 &&
            Math.abs(Number(traza.lon[indice]) - comando.lon) < 0.00001,
        );
        if (!contieneSede) {
          return;
        }

        const mapa = grafico._fullLayout?.map;
        if (!mapa) {
          return;
        }

        const yaEnfocado =
          Math.abs(mapa.center.lat - comando.lat) < 0.00001 &&
          Math.abs(mapa.center.lon - comando.lon) < 0.00001 &&
          Math.abs(mapa.zoom - comando.zoom) < 0.01;
        if (yaEnfocado) {
          return;
        }

        window.Plotly.relayout(grafico, {
          "map.center": {
            lat: comando.lat,
            lon: comando.lon,
          },
          "map.zoom": comando.zoom,
        });
      };

      grafico.on("plotly_afterplot", aplicarEnfoque);
      window.setTimeout(() => {
        grafico.removeListener("plotly_afterplot", aplicarEnfoque);
      }, 4000);
      window.setTimeout(aplicarEnfoque, 250);
    });
    observadorEnfoque.observe(focus, {
      childList: true,
      characterData: true,
      subtree: true,
    });

    return true;
  }

  if (conectarAsistente()) {
    return;
  }

  const observador = new MutationObserver(() => {
    if (conectarAsistente()) {
      observador.disconnect();
    }
  });
  observador.observe(document.documentElement, {
    childList: true,
    subtree: true,
  });
})();
