# 12 · Phase 3 — the frontend

React + TypeScript + Vite app in `web/`, covering all six screens from the
wireframes with meaningful motion throughout.

## Screens

- **Auth** (`/signin`, `/signup`) — one component, two modes.
- **Dashboard** (`/`) — checks list with animated score bars, pulsing status pills,
  live polling while any check is queued/running.
- **New check** (`/new`) — drag-drop or paste, animated dropzone.
- **Report** (`/report/:id`) — the centrepiece: the annotated manuscript + a margin
  panel (score rings, Sources tab, AI-writing tab). Polls until the check is done.
- **Sources** (`/sources`) — the org's reference repository, bulk upload.
- **Members / Settings** — org and profile (fuller in later phases).

## The hero: the manuscript

`components/manuscript/Manuscript.tsx` renders the submission as a document.
Matched passages get a highlighter that sweeps in on load; AI-flagged sentences
get a red-pen wavy underline. Hovering a source dims all but that source's matches.

## Design system

`styles/tokens.css`. Cool paper (#FBFBFA), electric cobalt (#2540F5) accent,
Fraunces + Geist type. Meaning colours (highlighter, red-pen) appear only inside
the manuscript. Motion is meaningful (score counters, status pulses, the load
sweep), not decorative; respects prefers-reduced-motion.

## Stack

Vite, React Router (animated transitions), TanStack Query (data + polling),
Framer Motion. Auth is a context holding a JWT in localStorage.

## Running

See `web/README.md`: `npm run dev` with the backend on :8000.

## Next

Phase 4 — coverage (Wikipedia ingestion, web-search fallback, quote exclusion),
or Phase 5 — production deploy.
