(() => {
  const selector = "#mapa-oferta-quirurgica .js-plotly-plot";

  function conectarTooltip() {
    const grafico = document.querySelector(selector);

    if (
      !grafico
      || typeof grafico.on !== "function"
      || !window.Plotly
      || !window.Plotly.Fx
    ) {
      return false;
    }

    if (grafico.dataset.tooltipResizeListener === "true") {
      return true;
    }

    grafico.dataset.tooltipResizeListener = "true";
    grafico.on("plotly_relayout", (cambios) => {
      if (cambios && cambios.autosize === true) {
        window.Plotly.Fx.unhover(grafico);
      }
    });

    const capaTooltip = grafico.querySelector(".hoverlayer");

    if (capaTooltip) {
      const corregirPosicionTexto = () => {
        capaTooltip.querySelectorAll(".hovertext").forEach((tooltip) => {
          const fondo = tooltip.querySelector("path");
          const texto = tooltip.querySelector("text");
          const lineas = texto
            ? [...texto.children].filter(
              (elemento) => elemento.tagName.toLowerCase() === "tspan",
            )
            : [];
          const ultimaLinea = lineas[lineas.length - 1];

          if (!fondo || !texto || !ultimaLinea) {
            return;
          }

          const tamanoFuente = Number.parseFloat(
            window.getComputedStyle(texto).fontSize,
          );
          const cajaFondo = fondo.getBBox();
          const desplazamientoFinal = Number.parseFloat(
            ultimaLinea.getAttribute("dy"),
          );

          if (
            !Number.isFinite(tamanoFuente)
            || !Number.isFinite(desplazamientoFinal)
            || cajaFondo.height === 0
          ) {
            return;
          }

          const posicionCorrecta = (
            cajaFondo.y
            + cajaFondo.height
            - tamanoFuente / 2
            - desplazamientoFinal * tamanoFuente
          );

          if (!Number.isFinite(posicionCorrecta)) {
            return;
          }

          const posicionTexto = Number.parseFloat(
            texto.getAttribute("y"),
          );

          if (
            !Number.isFinite(posicionTexto)
            || Math.abs(posicionTexto - posicionCorrecta) > 1
          ) {
            texto.setAttribute(
              "y",
              String(posicionCorrecta),
            );
          }

          lineas.forEach((linea) => {
            const posicionLinea = Number.parseFloat(
              linea.getAttribute("y"),
            );

            if (
              !Number.isFinite(posicionLinea)
              || Math.abs(posicionLinea - posicionCorrecta) > 1
            ) {
              linea.setAttribute(
                "y",
                String(posicionCorrecta),
              );
            }
          });
        });
      };

      const observadorTooltip = new MutationObserver(
        corregirPosicionTexto,
      );

      observadorTooltip.observe(
        capaTooltip,
        {
          attributes: true,
          attributeFilter: ["d", "dy", "y"],
          childList: true,
          subtree: true,
        },
      );
    }

    let anchoAnterior = grafico.clientWidth;
    let altoAnterior = grafico.clientHeight;

    new ResizeObserver(() => {
      const ancho = grafico.clientWidth;
      const alto = grafico.clientHeight;

      if (
        ancho !== anchoAnterior
        || alto !== altoAnterior
      ) {
        anchoAnterior = ancho;
        altoAnterior = alto;
        window.Plotly.Fx.unhover(grafico);
      }
    }).observe(grafico);

    return true;
  }

  if (conectarTooltip()) {
    return;
  }

  const observador = new MutationObserver(() => {
    if (conectarTooltip()) {
      observador.disconnect();
    }
  });

  observador.observe(document.documentElement, {
    childList: true,
    subtree: true,
  });
})();
