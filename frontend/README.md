# Raster Lab frontend

Astro static output, TypeScript browser code, and plain CSS. No UI framework or browser-side image transformations.

Six routes share `ToolLayout.astro` and `Editor.astro`: `/`, `/point-operations`, `/gamma-correction`, `/contrast-stretching`, `/spatial-filtering`, `/edge-detection`. `RangeControl.astro` provides the common sliders; `tools.ts` defines tool names, coordinate mappings and base formulas. `editor.ts` owns the active editor's file/settings/request lifecycle. `theme.ts` handles the shared toggle, with an inline head script applying the theme before paint. Only the theme preference is stored; images are not persisted or transferred across pages.

See the [root README](../README.md) for setup, both development servers, environment variables, API contract, coordinate mappings, verification results, and limitations.

From the repository root:

```powershell
npm --prefix frontend ci
npm --prefix frontend run dev -- --background
npm --prefix frontend run check
npm --prefix frontend run build
```

Open http://localhost:4321 and run the Python backend separately. Copy `.env.example` to `.env` if changing the default API URL or limits. Public variables are embedded at build time.

Spatial filtering and edge detection reuse `KernelControls.astro`, `KernelPanel.astro`, and `kernel-display.ts`. The matrix display requests small coefficient metadata from Python; images are processed only on Apply. Kernel sizes are 3, 5, 7, 9, 11 (native range step 2). No browser filter implementation is used.
