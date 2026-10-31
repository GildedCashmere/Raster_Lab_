# Raster Lab: current handover

Updated 2026-10-22. Glitch effect milestone is complete. Read root `AGENTS.md`, `frontend/AGENTS.md`, and `README.md` before further implementation.

## Latest addition: Glitch effect

- New `/glitch-effect` is the seventh tool, immediately before FAQ (eighth page, 19 questions). Shared editor/layout/theme/R mark, four 0..100 integer sliders with percentage number inputs, Apply/Reset/download, KaTeX and six permanent educational subsections.
- `backend/processing/glitch.py`: original RGB -> wrapped red/right + blue/left shift -> seeded wrapped bands -> shared RGB uniform noise -> odd-row darkening -> final ties-even round/clip -> original alpha at original coordinates. Input immutable; L/LA expand like point tools; all-zero exact decoded samples. No dependencies or existing algorithm changes. Limits remain 8 MiB/12 MP.
- Seed 0 by default, uint32; separate SeedSequence/PCG64 streams. Manual changes preserve seed. `frontend/src/glitch-settings.ts` generates curated Surprise settings with browser cryptographic randomness; exactly one automatic request if uploaded. Reset/new upload restore zero settings/seed and retain normal shared behavior. Stale protection/object-URL cleanup reused.
- Verified: **696 backend tests**, **20 math/settings tests**, Astro check zero diagnostics, eight-page production build. Actual Chrome: individual/combined effects and pixel equality, repeated Apply, Surprise with/without upload, keyboard/numeric validation, stale response, revoked blobs, loading/error recovery, download, Reset, drag/drop; six prior editor default regressions; 80 eight-route theme/width checks; FAQ/navigation, theme persistence/OS default, permanent education with JS disabled. Other browsers/devices/screen readers/concurrent load untested.
- Local three-run median at 12 MP: NumPy 283.2ms, complete TestClient API 1954.6ms; one RGB float32 workspace alone is 144MB decimal, additional buffers required. Reference could not be viewed (network blocked).
- Full mappings/measurements/checks: `docs/glitch.md`; screenshots `docs/design/raster-glitch-light.png` and `raster-glitch-dark.png`. Browser QA helper `.browser-check/glitch-qa.py` (ignored). Local dev frontend/backend were running at 4321/8000 during this task; recheck before launching duplicates.

The earlier presentation checkpoint below is retained as historical context; its seven-page counts and unchanged-script statement describe that earlier task only.

## Architecture

- Static Astro + TypeScript/browser JavaScript + plain CSS frontend; FastAPI backend; independent NumPy algorithms; Pillow only for image decoding/encoding and EXIF orientation. Python commands use the root `.venv`.
- Seven routes: `/` (geometry), `/point-operations`, `/gamma-correction`, `/contrast-stretching`, `/spatial-filtering`, `/edge-detection`, and `/faq`.
- Shared frontend: `SiteLayout.astro` (navigation/theme/header/footer), `ToolLayout.astro`, `Editor.astro`, `HowItWorks.astro`, `styles/editor.css`, and `scripts/editor.ts`. Educational content is in `content/education.ts`; FAQ data in `content/faq.ts`.
- KaTeX is bundled locally. `Math.astro` renders static HTML+MathML; `math-definitions.ts` and `math-render.ts` handle trusted application templates and targeted dynamic updates with trust disabled. Large real coefficient tables remain expandable.
- Backend routes in `backend/main.py`: `/health`, multipart `/process` returning PNG, `/inspect` for contrast bounds, and `/kernels` for actual kernel metadata. Processing runs in a worker thread.
- `backend/processing/`: geometry, point operations, shared channel handling, direct true convolution, kernel generation, spatial operations, and optimized `box_filter.py`.

## Completed design and content

- Shared warm light / charcoal dark themes, amber accents, subtle technical grid, local Barlow Condensed headings, readable body text, large uncropped image comparisons and compact controls. Explicit theme choice persists in localStorage; otherwise OS preference applies before paint.
- Typography now uses 16px body, 17–18px desktop reading text (16px mobile), 22–26px subsection headings, comfortable line height and a roughly 76-character reading column.
- All six tools have permanently visible, semantic, page-specific “How it works” sections below the editor, with five or six subsections and static equations. Header links jump to/focus the current section. Main formula panels still update with controls.
- `/faq` has 15 accessible native details/summary cards, multiple open answers, plus/minus indicators, theme styling and active navigation.
- Original vector R replaces the four-square mark in the shared header and favicon (`frontend/public/favicon.svg`). Wordmark retained; old bottom-right DSP footer label removed.
- Requested exact output copy: “Full resolutions as well as image transparency (Alpha) is preserved”. Exact requested grayscale description is applied; inversion description remains operation-specific.
- Latest task changed presentation/content only: backend/API, editor/theme scripts, formula definitions, kernel lists and limits were unchanged by hash comparison.

## Constraints to preserve

- Each Apply processes the original upload, never the previous result. Keep cancellation/stale-request protection, object-URL cleanup, defaults/Reset, real Python previews and PNG downloads.
- JPEG/PNG/WebP inputs; limits remain 8 MiB and 12,000,000 pixels. Full-resolution 48 MP is unsupported; no silent downscaling. EXIF orientation is normalized. No accounts, database, permanent image gallery or invented privacy guarantees.
- Five geometry operations only; quarter turns swap dimensions without interpolation. Keep input arrays unchanged and preserve alpha exactly.
- Gamma uses the DIRECT exponent `255*(p/255)^gamma`: below 1 brightens, above 1 darkens. Gamma -> RGB gains -> saturation -> final rounding/clipping. Gains are multipliers, not channel gamma.
- Contrast uses common RGB bounds and clipped linear mapping, then optional gamma -> gains -> saturation. Auto-range ignores fully transparent pixels. Equal automatic bounds skip the base stretch; invalid manual bounds are rejected.
- Blur/sharpen sizes exactly 3,5,7,9,11,21,31; emboss/Sobel exactly 3,5,7,9,11; default 3. Sliders map indices to these lists.
- Own float64 separable cumulative sums optimize box blur; sharpen is `I + amount*(I-B)`. Direct convolution remains the readable reference, reverses both kernel axes, and uses NumPy edge-excluding reflect padding. No Pillow/OpenCV/SciPy filters or huge neighborhood tensors.
- Emboss uses normalized directional grayscale convolution plus 128 offset. Sobel uses actual generalized binomial kernels, signed gradients, magnitude, max display normalization and optional threshold on normalized values before rounding.
- Float intermediates are preserved until final conversion except defined contrast base clipping. Spatial alpha is carried separately, not premultiplied: hidden RGB may influence neighbors.

## Verification already completed

- Earlier algorithm/redesign stages: **567 backend tests passed**. 31x31 complete API median timings (three runs): 1200x800 RGBA blur 80.6ms / sharpen 86.0ms; 4000x3000 blur 1103.8ms / sharpen 1150.6ms. Memory can still reach hundreds of MiB; no concurrent-load guarantee.
- Latest presentation task: Astro check zero diagnostics; seven-page production build; **17 math tests passed**. Backend tests were not rerun for this presentation-only change.
- Actual Chrome verification: all seven pages, both themes, five widths (1440/1024/768/390/320) at normal 100% zoom; no page overflow or math rendering errors. All six upload/Apply/preview/download/Reset workflows matched Python pixels and downloaded preview bytes.
- Also checked keyboard anchors/FAQ/focus, JavaScript-disabled static explanations and FAQ, OS theme detection/persistence, exact copy wrapping, expanded large matrices, and R mark at 16px. Earlier stage checked all spatial operation/size combinations.
- Not checked: Firefox/Safari, physical mobile devices, dedicated screen readers or concurrent load. Latest detailed review: `docs/interface-review.md`.
- Screenshots: `docs/design/raster-education-light.png`, `raster-education-dark.png`, `raster-faq-light.png`, `raster-faq-dark.png`, `raster-r-sizes.png`. Historical milestones remain in `docs/progress.md`.

## Run and validate (PowerShell from repository root)

Run the two development servers in separate terminals:

```powershell
npm --prefix frontend run dev -- --background
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
```

Open http://localhost:4321; backend health is http://localhost:8000/health. These development servers were left running at the last check; temporary preview and headless browser processes were closed. Recheck before starting duplicate servers.

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests
npm --prefix frontend run test:math
npm --prefix frontend run check
npm --prefix frontend run build
.\.venv\Scripts\python.exe -m backend.benchmark_spatial --sizes 31
```

See README for setup; example environments are `backend/.env.example` and `frontend/.env.example`. Default API URL is localhost:8000; CORS permits intended localhost/127.0.0.1 frontend origins on port 4321. Preview on another port needs explicit CORS configuration.

Git status remains the original all-untracked project tree (`.agents/`, AGENTS, README, backend, docs, frontend, etc.). No staging, reset, clean or commit was performed. Preserve all existing work. Browser helpers/fixtures are in ignored `.browser-check/`; reusable Chrome CDP helper is `design-review.py` there.
