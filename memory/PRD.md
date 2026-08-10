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

## Work Done (2026-07)
- **Fixed proxy WISP URLs**: replaced `wss://wisp-proxy.preview.emergentagent.com/api/wisp[2]` with `wss://wisp-proxy.emergent.host/api/wisp[2]` in `script.js` (+ localStorage migration off the old preview URL). Both verified accepting WebSocket connections.
- **Fixed "invalid messageport" proxy error** (root cause: `window.html` loaded `@mercuryworkshop/bare-mux` from CDN **unpinned/latest**, which drifted out of sync with the local `bareworker.js` worker → handshake mismatch). Fix: pinned bare-mux client to **@2.1.9** in `window.html` and replaced local `bareworker.js` with the matching **2.1.9** worker (kept local/same-origin because SharedWorker can't load cross-origin). Verified: proxy loads example.com cleanly.
- **Movies revamped to in-app player**: replaced Plex out-links with a **47-film Internet Archive** catalog (public-domain/classic/cult films — Night of the Living Dead, Nosferatu, His Girl Friday, DOOM-era classics, etc.). `data/movies.json` schema now `{name,id,embed,image}` (embed=`archive.org/embed/{id}`, image=`archive.org/services/img/{id}`). `pages/movies.html` now opens a themed in-app player overlay (iframe) with Fullscreen/Close/Esc. NO pirate stream aggregators used (declined by design).
- **Games cleanup + new working titles**: audited all 312 entries → 58 dead (deleted `ten8mystery/Vertex-Gold-Assets` + missing `freebuisness/html` files, mostly commercial titles with no legit embeddable replacement). Removed the 58; added **28 verified-working free games**: 14 open-source HTML5 games via `raw.githack.com` (2048, Tetris, Flappy Bird, Pac-Man, Space Invaders, Asteroids, Breakout, HexGL, Astray, Hextris, Clumsy Bird, Duck Hunt, Chrome Dino, Canyon Racer) + 14 playable classic arcade/DOS games via Internet Archive embeds (DOOM, Wolfenstein 3D, Prince of Persia, Oregon Trail, Pac-Man, Lemmings, SimCity, Tetris, Arkanoid, Digger, Pango, Paratrooper, Number Munchers, Test Drive). Final count: **282 games**.
- **Improved game loader** (`pages/g.html`): `document.write` path now injects a `<base href>` so games' relative asset paths resolve against their real host (repairs games that previously rendered blank).
- Verified via screenshots: proxy browse, movies in-app player, 2048, DOOM, Flappy Bird all working.

## Work Done (2026-07, cont.) — Real content + proxy routing
- **Expanded games to 338**: added **56 more real, famous Internet Archive games** (arcade via internetarcade + MS-DOS via softwarelibrary_msdos_games), all emulator-playable embeds — Mortal Kombat, Metal Slug, Q*bert, Joust, Defender, Out Run, Tron, Marble Madness, Centipede, Gauntlet, Rampage, Space Invaders, Berzerk, Paperboy, Commando, Crystal Castles, Moon Patrol, 1942, Aladdin, Golden Axe, Dune II, Master of Orion, Duke Nukem 3D, Jazz Jackrabbit, Maniac Mansion, Monkey Island, Mortal Kombat (DOS), DOOM II, Tomb Raider, Prince of Persia, Oregon Trail, SimCity, Lode Runner, Battle Chess, Monopoly, Bomberman, etc. All 70 IA-embed game IDs validated (0 invalid).
- **Expanded movies to 70**: added 23 more recognizable public-domain films (My Man Godfrey, A Star Is Born 1937, The Gold Rush, The Kid, White Zombie, M (Fritz Lang), The 39 Steps-era Hitchcock, Beat the Devil, Kansas City Confidential, The Hitch-Hiker, Robot Monster, Santa Claus Conquers the Martians, Reefer Madness, etc.). All verified to have playable video derivatives.
- **Internet Archive titles now load THROUGH the Flint proxy** (so they work even when archive.org is blocked on the network). Added `window.flintProxyEncode(url)` in `script.js` (exposes `sharedScramjet.encodeUrl` → `/scramjet/<encoded>` path). `movies.html` and `g.html` (IA embeds only) route their iframe through this when running inside the proxy frame; direct fallback for standalone access. Verified end-to-end: "Night of the Living Dead" (movie) and DOOM (game) both load via `/scramjet/https%3A%2F%2Farchive.org...` through Scramjet+WISP.
- NOTE: Open-source githack games (2048, Tetris, Flappy Bird, DOOM-clone, etc.) still load directly (not archive.org). No pirate stream/game sources used anywhere.

## Known / Out of Scope
- Live proxy browsing needs a reachable **wisp** websocket server. The bundled public wisp servers are unreachable from this container's network (inherent to the third-party tool); on a real deployment users' browsers may reach them.
- Cosmetic: a third-party telemetry counter is blocked by CORS (non-blocking).

## Backlog (P1/P2)
- P2: Add/refresh reliable wisp servers so live proxying works for end users.
- P2: Optional modern redesign of landing/browser UI (user chose as-is for now).
- P2: Self-host remaining external game/app cover images for full offline portability.
