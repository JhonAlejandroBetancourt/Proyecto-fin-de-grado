const http = require("node:http");

const requests = [];
const PORT = 8051;

const server = http.createServer((request, response) => {
  if (request.method === "GET" && request.url === "/health") {
    response.writeHead(200, { "content-type": "text/plain" });
    response.end("ready");
    return;
  }

  if (request.method === "GET" && request.url === "/__requests") {
    response.writeHead(200, { "content-type": "application/json" });
    response.end(JSON.stringify(requests));
    return;
  }

  if (
    request.method !== "POST" ||
    !/^\/v1beta\/models\/[A-Za-z0-9._-]+:generateContent$/.test(request.url)
  ) {
    response.writeHead(404, { "content-type": "text/plain" });
    response.end("not found");
    return;
  }

  let body = "";
  request.setEncoding("utf8");
  request.on("data", (chunk) => {
    body += chunk;
  });
  request.on("end", () => {
    let payload;
    try {
      payload = JSON.parse(body);
    } catch {
      response.writeHead(400, { "content-type": "text/plain" });
      response.end("invalid json");
      return;
    }

    const prompt = payload.contents?.[0]?.parts?.[0]?.text || "";
    requests.push({
      prompt,
      model: request.url.split("/").pop().replace(/:generateContent$/, ""),
      hasApiKey: Boolean(request.headers["x-goog-api-key"]),
    });

    const publicNature = {
      understood: true,
      clear_filters: false,
      change_services: false,
      services: [],
      change_nature: true,
      nature: ["Pública"],
      change_providers: false,
      providers: [],
      change_name_search: false,
      name_search: "",
      focus_sede: "",
      download_detail: false,
    };
    const modelOutput = /filtr|naturaleza|p[uú]blic/i.test(prompt)
      ? publicNature
      : {
          ...publicNature,
          understood: false,
          change_nature: false,
          nature: [],
        };

    response.writeHead(200, { "content-type": "application/json" });
    response.end(
      JSON.stringify({
        candidates: [
          {
            content: {
              parts: [{ text: JSON.stringify(modelOutput) }],
            },
          },
        ],
      }),
    );
  });
});

server.listen(PORT, "127.0.0.1");
