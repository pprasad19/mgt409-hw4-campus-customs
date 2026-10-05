# Campus Customs — frontend

The storefront: React 19 + Vite 8 + TypeScript, talking to the FastAPI backend
on port 8000.

**Setup and run instructions are in the [project README](../README.md).** The
data pack has to be in place and the backend running before this is useful, so
start there rather than here.

```bash
npm install
npm run dev        # http://localhost:5173
```

Node 20.19 or newer (or 22.12+), which `package.json` declares in `engines`.

`/api` and `/static` are proxied to `http://127.0.0.1:8000` by `vite.config.ts`,
so only port 5173 needs to be open in a browser and the image paths stored in
the database work unchanged.

## Where things are

| | |
| --- | --- |
| `src/pages/` | Home, Products, ProductDetail, About, LogIn, CreateAccount, NotFound |
| `src/components/` | chat widget, chat results band, product cards, colour swatches, command palette, nav bar, theme toggle, ticker |
| `src/auth/` | auth context and hook — session token, current user |
| `src/chat/` | context for the product cards the agent returns |
| `src/colors.ts` | all 22 catalogue colour names mapped to hex |
| `src/index.css` | the whole design system, light and dark |

`npm run lint` reports a handful of React advisory warnings and exits clean;
`npm run build` runs `tsc -b` first, so a type error fails the build.

The design decisions behind all of this are in
[`output/design.md`](../output/design.md).
