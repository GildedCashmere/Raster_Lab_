# Image Processing Lab

## Goal and scope

Build a polished image-processing website for an electronics undergraduate's university DSP project, with a structure suitable for later public hosting. The academic priority is correct, explainable mathematics; the website must provide a usable interface around the actual Python engine.

Required operations:
- Spatial convolution: blur, sharpen, emboss, and edge detection.
- Point operations: grayscale, colour inversion, gamma correction, and contrast stretching.
- Geometric transformations: horizontal/vertical flips and rotation.
- Still-image glitch: wrapped RGB separation, horizontal band tearing, monochrome static and scanline modulation.

Start rotation with 90, 180, and 270 degrees. Arbitrary-angle rotation is an optional extension requiring inverse coordinate mapping and a documented interpolation method; do not silently include it in the initial scope.

## Stack and repository

- `frontend/`: Astro, TypeScript/browser JavaScript, and plain CSS. Use Astro's static output unless a concrete requirement needs server rendering.
- `backend/main.py`: FastAPI application and API routes.
- `backend/processing/`: independent NumPy processing functions and kernel definitions.
- `backend/tests/`: pytest tests; use httpx/FastAPI TestClient for API tests.
- Pillow: image decoding, encoding, and orientation metadata handling.
- `.venv/`: Python virtual environment in the repository root.
- `backend/requirements.txt`: Python dependencies; `frontend/package.json` and its lockfile: frontend dependencies.

Keep one backend directory directly under the root. Inspect existing code before modifying it. Preserve useful working code and follow existing conventions. Add frameworks or infrastructure only when a concrete feature justifies them.

## DSP implementation requirements

- Perform all required image operations in the Python backend using our own NumPy arithmetic, indexing, and convolution implementation.
- NumPy array operations, slicing, broadcasting, padding, reductions, and matrix operations are allowed. Do not replace the core algorithms with Pillow filters/transforms, OpenCV filters, SciPy convolution, or browser CSS filters.
- Keep processing functions independent of FastAPI, uploads, filesystem paths, and frontend state. Accept arrays and explicit parameters; return new results without modifying the input.
- Point operations use the channels at the same pixel. Document the RGB weights used for grayscale and describe the result as an intensity/luma approximation, not physical luminance. Inversion uses `255 - channel_value` for 8-bit RGB.
- Flips and right-angle rotations use explicit index/coordinate mappings. Check width/height swaps and preserve pixel values exactly.
- Implement one reusable spatial convolution engine accepting odd square kernels; keep kernel generators separate. Blur/sharpen expose exactly 3,5,7,9,11,21,31; emboss/Sobel expose 3,5,7,9,11. Use an index slider mapped to these explicit lists, default 3x3; maximum box size 31x31.
- Implement true convolution by reversing the kernel along both spatial axes. Explain the distinction from correlation, especially for asymmetric kernels.
- Document the padding rule and preserve image dimensions for spatial filtering. Process colour channels independently, or explicitly convert to grayscale for an edge algorithm.
- Use signed floating-point intermediate values to prevent unsigned overflow and preserve negative filter responses. Define each filter's display conversion: clipping for sharpening, an explicit offset for embossing, and a documented magnitude/absolute-value rule for edges. Round and clip to the valid range when producing the final 8-bit image.
- State each kernel's normalization, purpose, and expected behaviour. Avoid normalizing by the kernel sum when that sum is zero, as with many edge kernels.
- Prioritize readable reference code. If performance requires vectorization or another optimization, preserve an explainable implementation and verify that numerical results remain equivalent.

## Website behaviour

- Provide image upload, operation controls, Apply, Reset, an original/processed comparison, and processed-image download.
- Keep the original image available. Reset restores the original and default controls. Make it clear whether an operation starts from the original or from an existing result; use the original as the default for the first milestone.
- Handle loading, empty, success, and error states. Prevent overlapping requests from displaying stale results. Revoke obsolete browser object URLs.
- Use accessible labels, keyboard controls, visible focus states, responsive layouts, and readable contrast. Use `frontend-design` for interface work and `web-design-guidelines` for review when those skills are installed.
- Keep the selected operation's coordinate mapping or base formula visible, with current parameter values and a concise explanation. Every processing page must also have a permanently visible, page-specific How it works reading section below the editor. Only advanced explanations and coefficient tables may remain collapsible. Never claim the app uses AI unless an AI feature is actually implemented.

## Pages, themes, and point-operation controls

- Provide seven tool pages: geometry at `/`, grayscale/inversion at `/point-operations`, gamma at `/gamma-correction`, contrast at `/contrast-stretching`, Blur/Sharpen/Emboss at `/spatial-filtering`, Sobel at `/edge-detection`, and `/glitch-effect`. Sobel has its own page and controls. `/faq` is the eighth informational page with 19 native details/summary question cards, supporting multiple open answers. Do not add a separate homepage or placeholder processing pages.
- Share `SiteLayout.astro` for all eight pages, including seven-tool navigation with Glitch effect immediately before the active FAQ link, theme toggle and footer. `ToolLayout.astro` wraps the processing pages. Preserve shared upload, original/output previews and dimensions, status/errors, Apply, Reset, and PNG download. Each page keeps its active settings while in use. Cross-page image transfer is not required; do not persist uploaded images in browser storage.
- Support light and dark themes across every component, including formulas, image checkers, loading, errors, disabled controls, and focus states. Apply the theme before paint. Persist only the user's theme choice in localStorage; use the OS preference until a choice exists. Handle unavailable storage without breaking the editor.
- Geometry keeps all five existing transformations. Show its coordinate mapping and short explanation immediately when selected, even before upload.
- Grayscale/inversion has an operation selector and **no sliders**. Update the visible formula immediately on selection. Grayscale uses `Y = 0.299R + 0.587G + 0.114B`, with `R'=G'=B'=Y`; inversion uses `C'=255-C` independently for RGB. Keep alpha unchanged.
- Gamma has one direct-exponent slider, `0.1..3.0`, default `1`. Use `p_base = 255*(p/255)^gamma`: below 1 brightens; above 1 darkens. Then provide RGB gains `0..2` and saturation `0..2`, all default `1`. Do not add another gamma slider.
- Contrast uses `p_base = clip(255*(p-a)/(b-a), 0, 255)` with shared RGB bounds `0 <= a < b <= 255`. Provide black/white point sliders and Auto-range. Initialize bounds from the decoded original's global visible-channel minimum and maximum, ignoring alpha-zero pixels. Show selected input and nominal output range `0..255`.
- Equal automatic bounds or no visible pixels mean an unchanged **base** image; show why and avoid division by zero. Subsequent adjustments still apply. Reject equal/invalid manual bounds. If sliders propose a valid manual range for a degenerate automatic range, clearly distinguish the proposal from the active automatic bypass. Auto-range and Reset restore the original image-derived range.
- Contrast adds optional gamma `0.1..3.0` (default `1`), followed by RGB gains and saturation `0..2` (default `1`). Adjustments may use a clearly labelled expandable group.
- Processing order is fixed: gamma page `original -> gamma -> gains -> saturation -> export`; contrast page `original -> clipped stretch -> gamma -> gains -> saturation -> export`. Gains use `C_gain=gain_C*C`. Saturation uses intensity **after gains**, `Y=.299R+.587G+.114B`, then `C_out=Y+s*(C-Y)`. Describe Y as an intensity/luma approximation. Saturation 0 gives grayscale; 1 is neutral; above 1 increases colourfulness.
- Keep floating-point precision between adjustments. Apart from the defined base contrast clipping, round and clip only at final uint8 export (document round-to-nearest, ties-to-even). Preserve alpha exactly. Point operations expand L/LA to RGB/RGBA so gains work consistently; geometry retains its existing mode handling.
- Formula/control changes update immediately without processing requests. Each Apply recomputes from the uploaded original, never a rounded previous result. Reset restores the page's defaults and discards the edited result. Preserve cancellation/generation guards and object-URL cleanup for both metadata and processing requests.
- Keep `POST /process` multipart fields `file` and `operation` compatible with geometry. New numeric parameters must be finite and within range. Explicit contrast bounds must be supplied together and satisfy `a < b`; omitted bounds mean auto-range. Reject inapplicable non-neutral adjustments. A bounded stateless metadata endpoint may read dimensions/range on contrast upload, using the same format, mode, EXIF, byte, and pixel validation as processing.
- Test known grayscale/inversion values, double inversion, gamma identities and 0.5/2 examples, contrast endpoints/intermediates, constant/transparent auto-ranges, invalid/non-finite settings, neutral controls, saturation zero, alpha/dimensions/input immutability, processing order, and API parameters. Retain all geometry tests. Check themes, persistence, navigation, controls, formulas, Apply/Reset, errors, and downloads in a browser when available; report unperformed checks.

## Shared visual design and mathematical rendering

- Preserve all existing routes and use shared tokens/components. The visual identity uses a subtle CSS technical grid, locally bundled Barlow Condensed bold headings, readable system body fonts, small monospace technical labels, amber controls, thin borders and restrained rounding. Light uses warm off-white/cream with charcoal text; dark uses near-black blue/charcoal with warm off-white text. Define distinct accessible palettes; never filter or invert actual preview pixels.
- On desktop the image workspace occupies roughly two-thirds and the control rail one-third. On mobile stack upload/controls, visible mathematics and original/output previews. Fit complete images without cropping or stretching; use themed transparency checkers and subtle diagonal hatching for empty/upload areas. Keep the tool above marketing content.
- Keep sliders amber with filled tracks, visible thumbs, keyboard access and synchronized labelled number fields for continuous settings. Kernel size remains an index into the explicit operation-specific list, with every NxN label visible. Invalid numeric input blocks Apply and shows a nearby message; Reset/Auto-range clear obsolete validation errors.
- Render all equations using the local npm KaTeX dependency and bundled CSS/fonts, with HTML-and-MathML output, trust disabled, application-owned templates and finite numeric substitutions. Share definitions in `frontend/src/math-definitions.ts`, static Astro rendering in `Math.astro`, and targeted/cached browser updates in `math-render.ts`. Never scan/re-render the whole page on slider input. Render failures must show a helpful fallback without raw TeX or breaking the editor.
- Keep the main equation/current parameter values visible above previews. Use fractions, powers/subscripts, gamma, aligned equations, convolution sums and actual bracketed small matrices. Preserve KaTeX's math fonts. Longer equations scroll locally and remain keyboard accessible; do not shrink them into unreadability or cause page overflow. The main How it works reading section stays visible; advanced tables and secondary formula detail may expand.
- Small (3x3/5x5) kernels have actual LaTeX matrices with normalization factors; larger kernels use compact definitions/dimensions and expandable, bounded keyboard-scrollable numerical tables. Keep the actual coefficients available, label raw/scaled coefficients and divisors, and show both Sobel kernels. Metadata comes from the backend generators.
- Preserve direct-exponent gamma and the established adjustment order. Reference websites supply visual inspiration only. Persist the explicit theme before paint and follow OS preference otherwise; retain errors/loading/disabled/focus and reduced-motion behaviour in both themes.
- Run `npm --prefix frontend run test:math` for template parsing, MathML output, numeric substitutions, direct-exponent notation and safe fallback, plus Astro check/build. Review actual desktop/mobile light/dark pages and document any untested browsers or assistive technology.

## Educational content, FAQ and typography

- Educational changes must preserve processing, API behaviour, editor scripting, limits, base formulas, controls, channel handling and supported kernel sizes. Feature additions may extend the shared architecture without changing existing operations. Use implementation-verified examples and explain the actual direct-exponent gamma, shared RGB bounds, reflect padding, true reversal, export rounding and alpha policy.
- On every processing route, render `HowItWorks.astro` as a normal semantic section with id `how-it-works`, a heading and 4-6 page-specific subsections. Content lives in `frontend/src/content/education.ts`. It must be visible before upload and remain readable without JavaScript. The header anchor jumps to and focuses this section on the current page, including mobile. Never make this main reading section an accordion.
- Keep the existing dynamic formula panel near previews. Educational equations use the same static KaTeX integration. Set readable paragraph measures around 65-80 characters, comfortable topic spacing and subtle separators; avoid the old three-column explanatory strip.
- Typography is assessed at normal 100% browser zoom: body 16px, supporting UI around 14-15px, secondary metadata at least 12px, reading text 17-18px on desktop / 16px on mobile, and reading subsection headings 22-26px. Keep equations legible, locally scrollable and free of page-level overflow. Preserve the display headings, amber accents and both themes.
- FAQ content lives in `frontend/src/content/faq.ts`. Cover categories, formats, both 8 MiB/12 MP limits, unsupported full-resolution 48 MP input, dimensions, alpha, original-based Apply, gamma, contrast, blur, sharpen versus edges, emboss, thresholding, PNG export and Python upload handling. Do not invent format support, browser-only processing, storage policies or larger-image modes. Native cards need labels, visible focus, plus/minus indicators and light/dark styling.
- The original vector capital R in `frontend/public/favicon.svg` is the single reusable brand asset: import it inline in the shared header and use the same file for the favicon. Keep the Raster Lab wordmark. The SVG must remain clear at 16px and inherit the theme accent in the header.
- Preserve the exact requested UI copy: `Full resolutions as well as image transparency (Alpha) is preserved`. The grayscale formula description is `R, G, B are the pixel’s colour values. Y is an luma approximation and not exactly physical luminance. The result was rounded and clipped keeping transparency (alpha) unchanged`. Keep inversion copy specific to inversion. The shared footer omits `Image Processing Lab / DSP`.

## Spatial filtering and edge detection

- Preserve the shared warm-light / charcoal-dark amber visual identity and workflow. Spatial filtering has a Blur/Sharpen/Emboss selector; Edge detection is dedicated to Sobel. Use the operation-specific seven-position box/sharpen or five-position derivative size slider, with all labels and the selected NxN size explicit. Each Apply filters the original, not an existing result; Reset restores 3x3 and page defaults.
- The reusable NumPy convolution engine supports grayscale and RGB arrays, reflect padding (excluding the edge sample), preserved dimensions, true reversal of both kernel axes, and signed float64 output. Do not clip/cast inside the engine or build H×W×N×N neighbourhood tensors. Offset loops with vectorized row blocks are acceptable; preserve explainable reference tests.
- Box averaging uses separable NumPy cumulative sums with the direct engine's exact reflect padding (edge sample excluded), processing RGB channels separately. Retain direct convolution as the reference and test float64 equivalence at borders, tiny/non-square images, constants, alpha, and identity. Blur/sharpen support 21 and 31; never extend derivative kernels beyond 11.
- Box blur uses `K=1/N²`, sum 1, independently on RGB. Sharpen uses the equivalent kernel `(1+a)delta-a*K_box`, sum 1, amount `0..2`, default `1`; `a=0` is identity. This implements `O=I+a*(I-I*K_box)` at every size.
- Emboss uses floating intensity `Y=.299R+.587G+.114B`, centred raw coefficients `i+j`, divided by their absolute sum. The kernel sums to zero. Export `128+strength*(Y*K_emboss)`, strength `0..2`, default `1`; reverse relief negates the signed response before adding 128. Output grayscale RGB/RGBA, retaining alpha.
- Sobel generates S from binomial order N-1 and D from full explicit convolution of `[-1,0,1]` with binomial order N-3. Use `outer(S,D)` and `outer(D,S)`, each divided by its absolute sum. The 3x3 raw pair must be standard Sobel; larger kernels must be generated at their actual size.
- Compute signed Gx/Gy without clipping, then `sqrt(Gx²+Gy²)`. Scale magnitude to 0..255 by its maximum for display; maximum <=1e-10 yields black. Explain that normalization can emphasize weak edges. Optional binary threshold is off by default; when on, white where normalized float magnitude >= T, black otherwise. T defaults to 128, range 0..255. Threshold 0 yields all white, including flat images.
- Gx detects changes across columns/vertical boundaries; Gy across rows/horizontal boundaries. Larger Sobel kernels broaden smoothing and alter fine detail. True convolution may reverse signs relative to correlation; magnitude is unaffected by simultaneous sign reversal.
- Display the current formula, values, explanation, and actual selected kernels on both pages, with clear raw/scaled-versus-normalized labels and divisors. Show both Sobel kernels. Use expandable/keyboard-scrollable matrices for large sizes, matching existing mathematical typography in both themes. A lightweight kernel-metadata API must reuse the processing generators, not a duplicate browser filtering algorithm.
- Preserve the shared alpha policy: expand L/LA to RGB/RGBA for filtering, separate alpha, filter straight RGB or floating intensity, then reattach the original alpha unchanged. Hidden RGB may influence neighbouring pixels; do not silently flatten or alpha-weight the image. Round/clip only final exports. Keep existing byte/pixel limits and processing feedback.
- Verify all seven box/sharpen sizes and five derivative sizes, kernel sums/constants, sharpen identity, emboss middle gray, Sobel directions and constant images, the exact 3x3 Sobel pair, reflected borders, an asymmetric convolution case, alpha, dimensions, signed intermediates, clipping, input immutability, API parameters, and matrix metadata. Preserve all earlier tests and document measured performance.

## Backend and future hosting

### Glitch effect

- `backend/processing/glitch.py` implements `glitch_effect` independently of the API. Exactly four integer intensity controls: `shift`, `tear`, `noise`, `scanlines`, each 0..100, default 0; seed is an integer 0..4294967295, default 0. Reject invalid/fractional/non-finite/out-of-range values and non-default glitch parameters on other operations.
- Order: original RGB -> channel separation -> horizontal tearing -> monochrome noise -> scanlines -> final rounding/clipping -> original alpha. Never accumulate results. All-zero copies decoded samples exactly (L/LA expand to RGB/RGBA), not compressed file bytes.
- Red shifts right and blue left by `round(.03*W*shift/100)` (nearest, ties to even); green stays. Horizontal remapping uses circular wrap. Tearing selects `ceil(12*t)` sequential potentially overlapping strips, roughly 0.5..4% high, displacement up to about `.12*W*t` with safe integer minima. One-row/column images skip tearing. No per-pixel Python loops.
- Noise amplitude is `64*noise/100`; one uniform sample per pixel is shared across RGB. Odd rows multiply by `1-.85*scanlines/100`, including the added noise. Use an owned float32 RGB workspace and bounded noise blocks; round/clip only the final output, ties to even. Alpha bypasses all stages at its original coordinates, without premultiplication.
- NumPy SeedSequence spawns separate local PCG64 streams for tearing/noise. Manual changes and repeated Apply preserve seed. `Surprise me` uses browser cryptographic randomness, curated balanced ranges and a fresh seed; it auto-applies once only if an image exists. Reset and new uploads follow shared defaults, including seed 0; do not persist images/seeds.
- Keep current values/KaTeX formulas near previews and six permanent educational subsections describing wrapping, streams, order, clipping and alpha. This simulates signal corruption, not real file corruption, datamoshing, animation or one convolution kernel. Keep 8 MiB/12 MP limits and existing algorithms. See `docs/glitch.md` for mappings and measurements.

### Shared API policy

- Preserve `GET /health`; use a documented `POST /process` contract for the image and operation settings. Return the processed image with its correct media type.
- Validate operation names, parameter ranges, decoded image formats, upload size, pixel count, and supported colour modes. Handle corrupt images with useful client errors.
- Define how EXIF orientation, transparency, and grayscale inputs are handled. Apply a consistent policy and explain any limitations.
- Process requests without retaining uploaded images by default. Avoid logging image contents or secrets. Temporary upload storage must be cleaned up.
- Keep API URLs and deployment settings configurable. Allow only intended frontend origins in CORS settings; distinguish local and production configuration.
- Use an Apply button initially. Bound image size and processing work; do not silently resize full-resolution downloads. Disclose any reduced-resolution preview or export limit.
- FastAPI does not make CPU-heavy convolution faster. Avoid blocking an async event loop with long synchronous processing; choose a suitable execution strategy and measure representative processing times.
- Keep the first release stateless. Add accounts, databases, persistent galleries, queues, or deployment services only when required by an agreed feature.

## Verification and documentation

- Check algorithms against independently calculated small arrays, not only visual appearance or another implementation of the same code.
- Cover known grayscale/inversion values; double inversion and double flip identities; four quarter-turn rotations; and non-square images.
- For convolution, check an identity kernel, a known blur result, border handling, clipping, a signed edge response, and an asymmetric kernel that distinguishes convolution from correlation.
- Test successful image upload/download and invalid files, unsupported operations, and configured size limits.
- Add a frontend `check` script that runs `astro check`. Run backend tests, Astro checks, and the frontend build when the corresponding code changes. Visually inspect the upload-to-download workflow when browser tooling is available; report honestly when it is not.
- Document setup, local startup, API settings, mathematical methods, limitations, and measured performance in README/documentation. Keep dependency declarations and lockfiles consistent.

Commands from the project root in Windows PowerShell:

```powershell
npm --prefix frontend run dev
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
.\.venv\Scripts\python.exe -m pytest backend/tests
npm --prefix frontend run check
npm --prefix frontend run build
```

Run the frontend and backend servers in separate terminals. Use the root virtual environment explicitly for Python commands.

## Milestones

1. Working upload-to-download website with horizontal/vertical flips and right-angle rotations.
2. Four shared tool pages, light/dark themes, visible mathematics, grayscale/inversion, gamma correction, and contrast stretching with shared adjustments.
3. Reusable convolution/kernel generators, a Blur/Sharpen/Emboss page, and a dedicated Sobel page; blur/sharpen support seven sizes and derivatives five sizes with visible matrices and verified mathematics.
4. Interface refinement, academic explanations, performance checks, and deployment documentation.

Complete and verify each requested milestone before expanding scope. Explain what changed, the mathematical method, what was tested, and any remaining limitations. Keep the code understandable enough for the student to explain to a professor.
