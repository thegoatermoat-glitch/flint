# Deploying Flint (static site)

Flint is a **pure static site** (HTML / CSS / JS). All files live in:

```
frontend/public/
```

That folder is fully self-contained — no build step, no backend. You can host it on any static host.

## Vercel
Two options:

**A. Deploy this whole repo** — a `vercel.json` is included at the repo root that points Vercel at `frontend/public`. Just import the repo, no settings needed.

**B. Deploy only the site folder** — set the Vercel project **Root Directory** to `frontend/public`, Framework Preset = **Other**, and leave Build/Install commands empty.

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
