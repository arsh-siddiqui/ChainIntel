# ChainIntel Frontend

Next.js 14 (App Router) + TypeScript strict + Tailwind CSS interface for ChainIntel.

## Quickstart

```bash
npm install
copy .env.local.example .env.local   # macOS/Linux: cp .env.local.example .env.local
npm run dev                          # http://localhost:3000
```

The backend must be running on `http://localhost:8000` (see `NEXT_PUBLIC_API_URL`).

## Scripts

| Command | Purpose |
|---|---|
| `npm run dev` | Development server on :3000 |
| `npm run build` | Production build |
| `npm run start` | Serve the production build |
| `npm run lint` | ESLint (next/core-web-vitals) |
| `npm run typecheck` | `tsc --noEmit` (strict) |
| `npm test` | Vitest unit tests (16 tests) |
| `npm run e2e` | Playwright e2e (needs both servers; `npx playwright install chromium` first) |

## Structure

- `app/` — 11 route pages: dashboard, wallet investigation (8 tabs), transaction explorer, graph analysis, threat intelligence, OSINT correlation, alerts & monitoring, investigation cases (+ detail), evidence, reports, settings
- `components/` — layout shell, UI primitives, DataTable, charts, React Flow graph canvas, wallet panels
- `lib/` — typed API client, query client, formatters, zod validators, constants
- `hooks/` — investigation pipeline hook (progress stepper), health/mode polling
- `types/` — API-facing interfaces

Design system: light theme, white/`#F8FAFC` surfaces, navy text, blue `#2563EB` primary, teal/amber/red/purple semantic accents, Inter font, rounded cards with subtle borders. Demo vs live data is always badged.
