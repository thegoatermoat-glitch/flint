// Vercel Serverless Function: FlintAI chat via OpenRouter (OpenAI-compatible).
// Served at https://<your-domain>/api/ai/chat (Vercel auto-detects /api).
//
// The OpenRouter API key is read from the OPENROUTER_API_KEY environment
// variable, so it stays server-side and is NEVER exposed in the static page.
// Set it in Vercel -> Project -> Settings -> Environment Variables:
//   OPENROUTER_API_KEY = <your key from https://openrouter.ai/keys>
// Optionally override the model with OPENROUTER_MODEL.
//
// Request body (stateless full history):
//   { "system": "persona...", "messages": [ { "role": "user"|"assistant",
//     "text": "...", "images": ["data:image/png;base64,...."] }, ... ] }
// Response: { "reply": "..." }

const OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions";
const DEFAULT_MODEL = "google/gemini-3-flash-preview"; // Gemini 3 Flash via OpenRouter

function toOpenAIMessages(system, messages) {
  const out = [{ role: "system", content: system || "You are FlintAI, a helpful assistant." }];
  for (const m of messages) {
    if (Array.isArray(m.images) && m.images.length) {
      const content = [{ type: "text", text: m.text || "" }];
      for (const url of m.images) {
        if (url) content.push({ type: "image_url", image_url: { url } });
      }
      out.push({ role: m.role, content });
    } else {
      out.push({ role: m.role, content: m.text || "" });
    }
  }
  return out;
}

module.exports = async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ detail: "Method not allowed" });
  }

  const key = process.env.OPENROUTER_API_KEY;
  if (!key) {
    return res.status(500).json({ detail: "OPENROUTER_API_KEY is not configured on the server." });
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

  const payload = {
    model: process.env.OPENROUTER_MODEL || DEFAULT_MODEL,
    messages: toOpenAIMessages(system, messages),
    temperature: 0.7,
  };

  try {
    const r = await fetch(OPENROUTER_URL, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${key}`,
        "Content-Type": "application/json",
        "HTTP-Referer": "https://flin.space",
        "X-Title": "Flint",
      },
      body: JSON.stringify(payload),
    });
    const data = await r.json();
    if (r.status >= 400 || data.error) {
      const msg = data.error && (data.error.message || data.error);
      return res.status(502).json({ detail: msg || `OpenRouter error (${r.status})` });
    }
    const reply = data.choices?.[0]?.message?.content || "(no response)";
    return res.status(200).json({ reply });
  } catch (e) {
    return res.status(502).json({ detail: String(e && e.message ? e.message : e) });
  }
};
