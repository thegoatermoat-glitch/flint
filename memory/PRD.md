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
- **Fixed reported bug**: `ServiceWorker script evaluation failed` (dead `ten8mystery/Flint` CDN) → repointed engine to bundled local files.
- **Fixed reported bug**: `$scramjetLoadController is not defined` after reload → moved engine files to `/engine/` (outside Scramjet's `/scramjet/` SW proxy prefix which was intercepting them).
- Fixed empty content pages → repointed to bundled local `../data/*.json`.
- **Removed Discord** everywhere: New Tab welcome-modal button, shortcut tile, dead CSS, and the Discord app entry in `apps.json`.
- **Added Movies feature**: `pages/movies.html` poster grid of 40 real movies from Plex free streaming; posters + slugs scraped/validated from `watch.plex.tv` (exact `og:image` posters via `images.plex.tv`); clicking a poster opens the movie in the Flint proxy browser via `postMessage({type:'navigate'})`. Data in `data/movies.json`. Added an "M0v13s" tile right after Games on the New Tab.
- **Leetspeak ('block word' cloaking)**: category labels/headings/titles → G4m3s, M0v13s, 4pps.
- **Vercel-ready**: root `vercel.json` (serves `frontend/public`, no build) + inner `frontend/public/vercel.json` (for Root Directory = frontend/public); both set `cleanUrls:false`, `Service-Worker-Allowed:/`, wasm content-type. `yarn build` copies public→build for build-based hosts. Docs in `DEPLOY.md`.
- Verified by testing agent iteration_1/2/3 — all in-scope checks 100% pass.

## Known / Out of Scope
- Live proxy browsing needs a reachable **wisp** websocket server. The bundled public wisp servers are unreachable from this container's network (inherent to the third-party tool); on a real deployment users' browsers may reach them.
- Cosmetic: a third-party telemetry counter is blocked by CORS (non-blocking).

## Backlog (P1/P2)
- P2: Add/refresh reliable wisp servers so live proxying works for end users.
- P2: Optional modern redesign of landing/browser UI (user chose as-is for now).
- P2: Self-host remaining external game/app cover images for full offline portability.
