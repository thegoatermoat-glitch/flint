// Vercel Serverless Function: FlintAI chat via Google Gemini.
// Served at https://<your-domain>/api/ai/chat (Vercel auto-detects /api).
//
// The Gemini API key is read from the GEMINI_API_KEY environment variable, so
// it stays server-side and is NEVER exposed in the static page source.
// Set it in Vercel -> Project -> Settings -> Environment Variables:
//   GEMINI_API_KEY = <your key from https://aistudio.google.com/apikey>
//
// Request body (stateless full history):
//   { "system": "persona...", "messages": [ { "role": "user"|"assistant",
//     "text": "...", "images": ["data:image/png;base64,...."] }, ... ] }
// Response: { "reply": "..." }

const MODEL = "gemini-flash-latest"; // dynamic alias -> current Gemini Flash

function parseDataUrl(u) {
  const m = /^data:([^;]+);base64,(.*)$/.exec(u || "");
  if (m) return { mime_type: m[1], data: m[2] };
  return { mime_type: "image/jpeg", data: (u || "").replace(/^data:[^,]*,/, "") };
}

module.exports = async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ detail: "Method not allowed" });
  }

  const key = process.env.GEMINI_API_KEY;
  if (!key) {
    return res.status(500).json({ detail: "GEMINI_API_KEY is not configured on the server." });
  }

  let body = req.body;
  if (typeof body === "string") {
    try { body = JSON.parse(body); } catch { body = {}; }
  }
  const system = (body && body.system) || "";
  const messages = (body && body.messages) || [];
  if (!Array.isArray(messages) || messages.length === 0) {
    return res.status(400).json({ detail: "messages is required" });
  }

  const contents = messages.map((m) => {
    const parts = [];
    if (m.text) parts.push({ text: m.text });
    for (const img of m.images || []) {
      const { mime_type, data } = parseDataUrl(img);
      if (data) parts.push({ inline_data: { mime_type, data } });
    }
    return { role: m.role === "assistant" ? "model" : "user", parts };
  });

  const payload = {
    contents,
    generationConfig: { temperature: 0.7 },
    safetySettings: [
      { category: "HARM_CATEGORY_HARASSMENT", threshold: "BLOCK_ONLY_HIGH" },
      { category: "HARM_CATEGORY_HATE_SPEECH", threshold: "BLOCK_ONLY_HIGH" },
      { category: "HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold: "BLOCK_ONLY_HIGH" },
      { category: "HARM_CATEGORY_DANGEROUS_CONTENT", threshold: "BLOCK_ONLY_HIGH" },
    ],
  };
  if (system) payload.systemInstruction = { parts: [{ text: system }] };

  try {
    const r = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent?key=${encodeURIComponent(key)}`,
      { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }
    );
    const data = await r.json();
    if (data.error) {
      return res.status(502).json({ detail: data.error.message || "Gemini request failed" });
    }
    const reply =
      (data.candidates?.[0]?.content?.parts || []).map((p) => p.text || "").join("") || "(no response)";
    return res.status(200).json({ reply });
  } catch (e) {
    return res.status(502).json({ detail: String(e && e.message ? e.message : e) });
  }
}
