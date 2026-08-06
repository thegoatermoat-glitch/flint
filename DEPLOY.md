# Deploying Flint (static site)

Flint is a **pure static site** (HTML / CSS / JS). All files live in:

```
frontend/public/
```

That folder is fully self-contained — no build step, no backend. You can host it on any static host.

## Vercel
This repo is ready for Vercel with **zero build step** (it's pure static). Pick either:

**Option A — Import the whole repo (easiest).**
A `vercel.json` at the repo root tells Vercel to serve `frontend/public` directly (no install, no build). Just "Add New → Project", import the repo, and deploy. Nothing else to configure.

**Option B — Point Vercel at the site folder.**
In the Vercel project settings set **Root Directory = `frontend/public`**, Framework Preset = **Other**. A `vercel.json` inside that folder sets the correct headers. Leave Build & Install commands empty.

Both options set:
- `cleanUrls: false` (Flint links to explicit `.html` files)
- `Service-Worker-Allowed: /` on `sw.js` and `Content-Type: application/wasm` on `.wasm`

> If a host insists on a build, `yarn build` (in `frontend/`) just copies `public/` → `build/`, so you can also use Build Command `yarn build` with Output Directory `frontend/build`.

## Netlify
- Drag-and-drop the `frontend/public` folder into Netlify, **or**
- Connect the repo and set **Publish directory** to `frontend/public` (a `netlify.toml` is already inside that folder).

## GitHub Pages / Cloudflare Pages / any static host
Upload the contents of `frontend/public/`. `index.html` is the entry point.

## Local preview (already running here)
```
cd frontend
yarn start   # serves frontend/public on port 3000
```

## Notes
- Service worker (`sw.js`) must be served from the site root so its scope is `/`.
- `.wasm` files must be served with `Content-Type: application/wasm` (handled in the included configs).
- Scramjet core + wisp proxy servers load from external CDNs/servers already referenced in the code.
