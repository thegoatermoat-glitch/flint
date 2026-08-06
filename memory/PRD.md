# Flint — PRD

## Original Problem Statement
User uploaded `flnt-main.zip` (the "Flint" web proxy/unblocker — Scramjet-based, by MercuryWorkshop/ten8mystery) and asked to "use this as a start for a website, frontend only."

## User Choices (explicit)
- Host the existing site **AS-IS** (no redesign).
- Keep it **plain HTML/CSS/JS** (no React rebuild).
- Keep the external **wisp** proxy servers as-is.
- "Just get it running and make sure it can be redeployed to other hosters like Vercel etc."

## Architecture
- Pure static site in `frontend/public/` (HTML/CSS/JS, service worker, Scramjet proxy engine + local assets, JSON data files).
- Served locally on port 3000 by `frontend/server.js` — a zero-dependency Node static server (serves index.html at `/`, no cleanUrls redirects, sets `Service-Worker-Allowed: /` for sw.js and `application/wasm` for .wasm).
- No backend, no MongoDB used.

## Work Done (2026-06)
- Set up static hosting: replaced CRA start with `node server.js`; site lives in `frontend/public/`.
- **Fixed reported bug**: `ServiceWorker script evaluation failed`. Root cause = the `ten8mystery/Flint` CDN (scramjet.all/sync/wasm) is now **404 (dead)**. Repointed `sw.js`, `script.js`, `window.html`, `embed.html` to the **bundled local** `/scramjet/` files (byte-identical to the known-good build). SW now registers successfully.
- Fixed empty content pages: `g.html` (games), `a.html` (apps), `nt.html` (quotes), `vm.html` (VMs) fetched JSON from dead external repo URLs → repointed to the bundled local `../data/*.json`.
- Added deployment configs: root `vercel.json`, `frontend/public/netlify.toml`, and `DEPLOY.md`.
- Verified by testing agent (iteration_1): SW registers, all pages/assets serve, grids populate. 100% of in-scope checks pass.

## Known / Out of Scope
- Live proxy browsing needs a reachable **wisp** websocket server. The bundled public wisp servers are unreachable from this container's network (inherent to the third-party tool); on a real deployment users' browsers may reach them.
- Cosmetic: a third-party telemetry counter is blocked by CORS (non-blocking).

## Backlog (P1/P2)
- P2: Add/refresh reliable wisp servers so live proxying works for end users.
- P2: Optional modern redesign of landing/browser UI (user chose as-is for now).
- P2: Self-host remaining external game/app cover images for full offline portability.
