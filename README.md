# Raster Lab · Image Processing Lab

An Astro website with seven image editors and a dedicated FAQ page connected to a stateless FastAPI/NumPy engine for an undergraduate DSP project. Pillow handles decoding, encoding and EXIF normalization; our NumPy code performs every geometric, point, spatial and glitch operation. Preview and download use the same PNG returned by Python.

## Pages and workflow

| Route | Tool | Default controls |
| --- | --- | --- |
| `/` | Flip & rotate | Horizontal flip; also vertical flip and clockwise 90°, 180°, 270° rotations |
| `/point-operations` | Grayscale / colour inversion | Grayscale selected; no adjustment sliders |
| `/gamma-correction` | Gamma correction | One gamma slider `0.1–3`, default `1`; RGB gains and saturation `0–2`, default `1` |
| `/contrast-stretching` | Contrast stretching | Image-derived shared black/white points and Auto-range; optional gamma `0.1–3`, gains/saturation `0–2`, all default `1` |
| `/spatial-filtering` | Blur / Sharpen / Emboss | Blur selected; seven box/sharpen sizes and five emboss sizes, default 3x3; amount/strength 1, reverse relief off |
| `/edge-detection` | Generalized Sobel edges | Five kernel sizes, default 3x3; binary threshold off, threshold 128 when enabled |
| `/glitch-effect` | Glitch effect | RGB Shift, Horizontal Tearing, Static Noise, Scanlines: integer 0–100%, all default 0; seed 0; Surprise me |
| `/faq` | Frequently Asked Questions | 19 native expandable question cards; multiple answers can stay open |

Seven tool pages share navigation, upload, previews, dimensions, Apply, Reset, download, errors, formulas and theme. The eighth `/faq` page shares the header/navigation, theme and footer without loading editor behaviour. There is no separate homepage. The existing geometry route remains `/`.

Choose an image with the file picker or drop it onto the upload area. Select an operation or adjust sliders; its formula updates immediately. **Apply transformation** processes the original upload with the current settings. Every Apply starts from that original, so edits and rounding never accumulate. Download saves the actual returned full-resolution PNG.

**Reset** discards the edited result, shows the original in the output pane, and restores page defaults: horizontal flip, grayscale, or neutral adjustments as appropriate. Contrast restores the original image's automatic range too. Auto-range restores only contrast bounds; it leaves optional adjustments in place. Changing any operation/slider invalidates the previous result. New uploads discard earlier images/results and restore defaults.

Colour adjustments are in a labelled expandable group. The base formula, current values and processing order remain visible; detailed adjustment formulas can be expanded. Formula changes and slider movements do not send processing requests.

Images and settings remain in the active editor while it is used, including when the theme changes or an adjustment group closes. Navigating to another page starts a fresh workspace. Images are not transferred across pages or saved in localStorage.

### Light and dark themes

The shared **Dark mode** toggle is keyboard accessible and exposes its state with `aria-pressed`. A small inline head script applies the saved theme before paint. The only persisted app setting is `localStorage['raster-theme']` (`light` or `dark`). Until the user chooses, the site follows the OS preference, including live changes. Explicit choices persist across visits/pages and sync across tabs. If storage is unavailable, the editor and toggle still work; a choice cannot persist beyond that document.

### Design and rendered mathematics

Both themes share a CSS technical grid, amber selection/control accents, thin borders, restrained corners and diagonal upload hatching. Light uses warm off-white/cream with charcoal text; dark uses blue-charcoal surfaces with warm off-white text. On desktop the large comparison workspace occupies about two-thirds, with controls alongside. Mobile stacks controls, equations and uncropped previews. Themes never filter the actual image pixels.

Body type uses reliable system fonts; condensed headings use locally bundled Barlow Condensed. KaTeX is an npm dependency: `SiteLayout.astro` imports its CSS/font assets through Vite, with no runtime CDN. `math-definitions.ts` owns the trusted LaTeX templates, `Math.astro` renders initial equations during the static build, and `math-render.ts` targets only changed equation nodes in the browser. Rendering uses HTML **and MathML**, `trust: false`, finite numerical substitutions and a graceful explanatory fallback. Longer equations have local keyboard-accessible scrolling; mathematical fonts remain intact. Geometry mappings, grayscale/inversion, direct gamma, contrast, gains/saturation, convolution, emboss and Sobel are typeset consistently.

 Reference captures and earlier editor screenshots remain in [docs/design](docs/design/). Current screenshots: [education in light](docs/design/raster-education-light.png), [education in dark](docs/design/raster-education-dark.png), [FAQ in light](docs/design/raster-faq-light.png), [FAQ in dark](docs/design/raster-faq-dark.png), and [R at favicon sizes](docs/design/raster-r-sizes.png).

### Reading sections, FAQ and branding

Every tool has a permanently visible **How it works** section below the editor, available before upload and with JavaScript disabled. The header link jumps to that section on the current page and moves keyboard focus there. Geometry and point operations have five subsections; gamma, contrast, spatial filtering and Sobel each have six. The explanations define symbols, preserve the implementation's conventions and include verified numerical examples. Large coefficient tables and advanced editor details remain collapsible.

The shared type tokens use a 16px body, 14-15px supporting/control text, 12px secondary metadata, 17-18px desktop / 16px mobile reading text and 22-26px reading subsection headings. Single-column reading measures are capped at 76ch, with generous line height and subtle topic separators. Check at **100% browser zoom**. KaTeX equations keep their own mathematical fonts and local scrolling.

- `frontend/src/layouts/SiteLayout.astro`: common document, brand, eight-link navigation, pre-paint theme, footer and theme script.
- `frontend/src/components/HowItWorks.astro` and `frontend/src/content/education.ts`: static semantic educational content and KaTeX equations.
- `frontend/src/pages/faq.astro` and `frontend/src/content/faq.ts`: 19 accessible native question cards about mathematics, glitch settings/repeatability, formats, dimensions, transparency, processing and the unchanged 8 MiB/12 MP limits. Full-resolution 48 MP inputs remain unsupported.
- `frontend/public/favicon.svg`: the original geometric R, used both inline in the header and as the favicon. Header colour follows the theme accent; the standalone file has an amber fallback. No icon library or raster-generated mark is used.

## Glitch effect milestone

Open **http://localhost:4321/glitch-effect**. Four integer intensity sliders (0–100%, default zero) control a fixed NumPy pipeline: original RGB -> opposing wrapped RGB shifts -> wrapped horizontal strips -> shared-channel static noise -> odd-row darkening -> final round/clip -> original alpha. Intensities are not literal percentages of image displacement. All-zero returns decoded samples exactly, not original compressed bytes. Grayscale expands to RGB; alpha stays byte-for-byte at its source coordinates.

The page maintains an unsigned 32-bit seed (default 0). Manual changes preserve it; repeated Apply is reproducible. Separate local PCG64 streams prevent noise changes from regenerating tearing. **Surprise me ✨** picks balanced values and a fresh cryptographic seed; with an image loaded it applies once, otherwise it only updates settings. Reset retains the upload, clears the result and restores zero controls/seed; new uploads also restore defaults. No animation, codec datamoshing, new services or dependencies are introduced.

Implementation, exact mappings, memory policy and measured timings: [docs/glitch.md](docs/glitch.md). API fields: [docs/API.md](docs/API.md). Screenshots: [light](docs/design/raster-glitch-light.png), [dark](docs/design/raster-glitch-dark.png).

Latest glitch verification: **696 backend tests**, **20 frontend math/settings tests**, zero-diagnostic Astro check and eight-page production build. Actual Chrome checked the four effects separately and together, repeated Apply, Surprise with/without upload, stale responses, blob cleanup, errors/recovery, download byte equality, Reset, drag/drop, theme behavior and all six older default editor workflows. All eight routes passed 80 theme/width layout checks at normal zoom. Reference access was blocked; other browsers, physical devices, dedicated screen readers and concurrent load were not checked. See [docs/glitch.md](docs/glitch.md) for scope.

## Setup and local startup

Use Windows PowerShell from the repository root. Reuse the existing `.venv` and frontend packages. For a fresh checkout, use Python 3.13+ and Node satisfying `frontend/package.json` (currently >=22.23.4):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
npm --prefix frontend ci
```

Defaults work without environment files. To customize:

```powershell
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env
```

Start the backend in one terminal:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
```

Append `--env-file backend/.env` when using that file; Uvicorn does not automatically load it. Start Astro in a separate terminal, following the repository's background convention:

```powershell
npm --prefix frontend run dev -- --background
```

Open **http://localhost:4321**. API health: **http://localhost:8000/health**. Interactive API documentation: **http://localhost:8000/docs**. The backend must run for Apply and contrast range analysis to work.

```powershell
npm --prefix frontend run astro -- dev status
npm --prefix frontend run astro -- dev logs
npm --prefix frontend run astro -- dev stop
```

If a port is occupied, check for an existing server first. If Astro chooses another port, update backend allowed origins.

## Configuration and later hosting

| Variable | Default | Purpose |
| --- | --- | --- |
| Backend `MAX_UPLOAD_BYTES` | `8388608` | Exact upload file limit, inclusive: 8 MiB |
| Backend `MAX_IMAGE_PIXELS` | `12000000` | Decoded width × height limit, inclusive: 12 MP |
| Backend `ALLOWED_ORIGINS` | `http://localhost:4321,http://127.0.0.1:4321` | Comma-separated intended frontend origins |
| Frontend `PUBLIC_API_URL` | `http://localhost:8000` | API base URL, without endpoint suffix |
| Frontend `PUBLIC_MAX_UPLOAD_BYTES` | `8388608` | Browser validation and displayed file limit |
| Frontend `PUBLIC_MAX_IMAGE_PIXELS` | `12000000` | Browser validation and displayed pixel limit |

Limits must be positive integers; keep frontend and backend settings consistent. Backend validation is authoritative. Backend variables load on startup from the process environment or explicit `--env-file`. Frontend public variables are embedded at build time: restart development/rebuild production after changes. They must not contain secrets.

Build `frontend/dist` for a static host and run FastAPI separately behind HTTPS. Set the public API URL and exact production frontend origin(s); replace local origins rather than using a CORS wildcard. A same-origin reverse proxy can use `PUBLIC_API_URL=/api` and strip that prefix when forwarding. CORS is not authentication. Configure request and concurrency limits according to host memory; point operations use floating-point working arrays. No hosting service, database, accounts, or queue is added.

## Processing flow and image policy

1. The browser displays the original file locally, respecting EXIF orientation in supported browsers. Preview areas fit the full image with `object-fit: contain`; they do not crop or perform the requested operation.
2. On **contrast upload only**, Python reads dimensions and automatic bounds through `POST /inspect`. This applies the same decoding/orientation/format/size policy as processing, without producing an edited image. Range analysis and processing each receive the original file; neither retains it.
3. Apply sends `file`, `operation` and relevant settings to `POST /process`. FastAPI validates numeric settings and bounded upload data. Pillow identifies the actual format and checks dimensions/mode before decoding pixels; EXIF orientation is normalized once.
4. NumPy rearranges geometry coordinates, calculates point operations or filters spatial neighbourhoods. Decoding, mathematics and PNG encoding run in a worker thread to keep the async event loop responsive.
5. Python returns a PNG and dimensions. The browser previews and downloads that same blob. Visual preview scaling never reduces export resolution. Selection/upload/reset generation guards prevent stale responses from replacing current state. Obsolete object URLs are revoked.

Supported still inputs: JPEG, PNG and WebP. Extensions and client MIME types are not trusted by the API. Animated images, CMYK, high-depth PNG (including 16-bit RGB/RGBA), floating-point and unsupported modes are rejected with useful errors.

Geometry retains decoded `L`, `LA`, RGB and RGBA channels. Point and spatial operations expand grayscale to RGB (or LA to RGBA) with NumPy so RGB gains work consistently and grayscale satisfies `R'=G'=B'`. Alpha is preserved byte-for-byte throughout every operation. Bilevel expands to grayscale; palette and colour-key transparency expand to RGBA. Bounds ignore fully transparent pixels, but the requested arithmetic applies to their hidden colour channels too; alpha remains zero.

Outputs do not copy EXIF, ICC profiles, DPI or ancillary metadata. This prevents double orientation but can change colour-managed rendering of profiled originals. Values are exact relative to the decoded input; JPEG and ordinary WebP may already be lossy. No silent resizing, downsampling, or alpha flattening occurs.

Uploads may be temporarily spooled by the multipart parser, then closed/cleaned on completion or error. There is no permanent image storage or image-content logging. The request body ceiling is the file limit + 64 KiB multipart overhead, including streamed bodies. UI requests time out after 60 seconds. Cancelling prevents stale display; it cannot interrupt processing already running in a Python thread.

## Mathematics

The reference code is in `backend/processing/geometry.py`, `backend/processing/point.py`, and the shared spatial modules documented below, independent of HTTP, files and UI state. Inputs are not mutated. No ready-made point/image filters, `np.rot90`, or browser image transformations implement the operations.

### Geometric mappings

For original `I` of height `H`, width `W`, coordinates are zero-based `I[y,x]`, with rows increasing downwards and columns rightwards. `O` is the output; all channels move together.

| Operation | Source pixel for each output coordinate | Output height × width |
| --- | --- | --- |
| Horizontal flip | `O[y,x] = I[y,W-1-x]` | `H × W` |
| Vertical flip | `O[y,x] = I[H-1-y,x]` | `H × W` |
| 90° clockwise | `O[y,x] = I[H-1-x,y]` | `W × H` |
| 180° | `O[y,x] = I[H-1-y,W-1-x]` | `H × W` |
| 270° clockwise | `O[y,x] = I[x,W-1-y]` | `W × H` |

NumPy reversed slices and axis exchange implement these mappings, followed by `.copy()`. For `[[1,2,3],[4,5,6]]`, 90° clockwise gives `[[4,1],[5,2],[6,3]]`. No interpolation is needed. The existing geometry implementation is unchanged.

### Grayscale and inversion

```text
Y = 0.299R + 0.587G + 0.114B
R' = G' = B' = Y

R' = 255 - R
G' = 255 - G
B' = 255 - B
```

RGB weights approximate encoded intensity/luma, not physical luminance. Grayscale uses floating-point arithmetic followed by final rounding/clipping. Inversion changes colour channels only. There are no adjustment sliders or hidden non-neutral adjustments on this page.

### Gamma correction

```text
p_base = 255 * (p / 255)^gamma
Original -> gamma -> RGB gains -> saturation -> final output
```

`p` is an original channel in 0–255. Gamma is **the direct exponent**, not its reciprocal: below 1 brightens, above 1 darkens, 1 leaves the base unchanged. Apply independently to RGB. The page has exactly one gamma slider, range 0.1–3.0, default 1.0.

### Contrast stretching and auto-range

```text
p_base = clip(255 * (p - a) / (b - a), 0, 255)
Original -> contrast stretch -> optional gamma -> RGB gains -> saturation -> final output
```

`a` is the input black point, `b` the input white point. Manual settings require `0 <= a < b <= 255`. The same bounds apply to every RGB channel; per-channel bounds are not estimated. Base clipping is an intentional part of the formula.

Automatic bounds are the global min/max of visible RGB channel values after EXIF normalization. Pixels with alpha zero are ignored; partially transparent pixels count without weighting. A uniform colour may still have a valid span if its RGB channels differ. If automatic bounds coincide (e.g. uniform gray) or no pixels are visible, the base stays unchanged and the UI explains why. Optional adjustments still run. The sliders then show a clearly labelled proposed manual range of 0–255; moving either activates manual bounds. Auto-range or Reset returns to the automatic bypass. Explicit equal/reversed bounds are never accepted by the API.

### Shared adjustments and export

```text
# After the base operation (optional gamma first on the contrast page):
p_gamma = 255 * (p_base / 255)^gamma
C_gain = gain_C * C
Y = 0.299R_gain + 0.587G_gain + 0.114B_gain
C_out = Y + saturation * (C_gain - Y)
```

RGB gains range 0–2, default 1. Saturation range 0–2, default 1. Compute weighted intensity **after gains**. Saturation 0 gives equal RGB channels, 1 is neutral, above 1 increases colourfulness. The gamma page does not run an additional gamma stage: its base is already gamma correction.

Use float64 intermediates. Do not round/clip after gamma, gains or saturation; gained values can exceed 255 and must remain available to the saturation calculation. Round with NumPy `rint` (nearest, ties to even), clip to 0–255, and convert to uint8 only at final export. Neutral gamma/saturation are exact identity paths to avoid floating-point drift. Alpha bypasses all arithmetic and is copied unchanged.

## Spatial filtering and edge detection

`/spatial-filtering` contains **Blur, Sharpen, and Emboss**. `/edge-detection` contains **Sobel edges** with its own controls and explanations. Both use the existing shared editor, previews, errors, themes, Reset and PNG download.

Blur and unsharp-mask sharpening use exactly **3x3, 5x5, 7x7, 9x9, 11x11, 21x21, 31x31**, default 3x3. Emboss and Sobel remain at **3x3, 5x5, 7x7, 9x9, 11x11**. Native sliders store an index into these explicit lists, so intervening integers are never selected. All NxN labels and the current size remain visible. Switching from a large box size to Emboss clamps to 11x11.

Changing size changes the actual neighbourhood. Controls/formulas update immediately, without an image-processing request. Every Apply sends the original file and relevant parameters. Reset restores the default operation, 3x3, amount/strength 1, normal relief, continuous Sobel output and threshold 128. Continuous sliders also have synchronized numeric fields; invalid input disables Apply with an inline explanation. Auto-range/Reset clear obsolete validation errors.

### Shared implementation

- `backend/processing/convolution.py`: reusable signed float64 true convolution for H×W or H×W×channels arrays. Reverse the kernel along both axes, then multiply/accumulate neighbourhood samples. Correlation omits that reversal; asymmetric kernels therefore respond differently.
- `backend/processing/box_filter.py`: optimized box averaging using separable NumPy cumulative-sum differences. It pads with the same exact reflect convention, computes horizontal then vertical sums, divides by N squared once, and processes RGB channels separately. Work is O(HWC) with image-sized storage, without an HxWxNxN tensor. For arbitrary float input, changed summation order can differ from direct convolution at float64 roundoff level (tests use 1e-10 absolute / 1e-12 relative tolerance). Unsigned image sums are exact until division.
- `backend/processing/kernels.py`: box, unsharp, directional emboss and generalized Sobel generators, shared by filtering and the `/kernels` metadata endpoint.
- `backend/processing/spatial.py`: filter-specific colour conversion, signed responses, display conversion and optional Sobel thresholding.
- `backend/processing/channels.py`: shared point/spatial channel separation, float intensity and final export; alpha never goes through convolution.

Reflect padding excludes the border sample: a one-pixel pad of `[a,b,c]` is `[b,a,b,c,b]`. Reflection repeats as needed for a kernel larger than an image dimension; singleton axes repeat their sole value. Output width and height remain unchanged. The engine loops over kernel offsets and vectorizes row blocks, accumulating into a float image with a small scratch block. It allocates no H×W×N×N tensor, does no intermediate clipping/rounding, and never modifies input arrays or kernels. The direct reference runtime is O(HWCN²); working storage scales with the image, not the full window tensor.

### Box blur

```text
K_box[i,j] = 1/N²
O = I * K_box
```

The coefficients sum to 1 and constant images are preserved. Filter RGB channels independently. Larger neighbourhoods average a wider region and smooth more strongly.

### Sharpening

```text
B = I * K_box
O = I + a*(I - B)
K_sharp = (1+a)*delta - a*K_box
```

The equivalent real NxN kernel remains available for inspection and direct-reference checks. Production sharpening computes the same I + a*(I-B) using optimized box averaging. `delta` has 1 at the centre and 0 elsewhere. Coefficients sum to 1; amount `a` ranges 0–2, default 1; at zero the result is exactly the original RGB values. Signed responses can exceed 0–255 and are rounded/clipped only at export. This unsharp-mask formulation works at all seven box sizes; amount zero has an exact identity path.

### Emboss

```text
Y = 0.299R + 0.587G + 0.114B
m = (N-1)/2; i,j range from -m to m
K_raw[i,j] = i+j
K_emboss = K_raw / sum(abs(K_raw))
E = Y * K_emboss
O = 128 + strength*E
```

The 3×3 raw kernel is `[[-2,-1,0],[-1,0,1],[0,1,2]]`. Its sum is zero, so normalization uses the absolute coefficient sum (8 at 3×3), never the zero sum. Absolute-sum normalization keeps strength reasonably comparable across sizes. Strength ranges 0–2, default 1. Reverse relief negates E before adding the 128 display offset. Constant images produce middle gray, including at strength 0. Y is floating encoded intensity/luma, not physical luminance. Output has equal RGB channels and unchanged source alpha.

### Generalized Sobel

```text
S = binomial coefficient row of order N-1
D = full 1-D convolution of [-1,0,1] with binomial row of order N-3
Kx_raw = outer(S,D); Ky_raw = outer(D,S)
Kx = Kx_raw / sum(abs(Kx_raw)); Ky = Ky_raw / sum(abs(Ky_raw))
Gx = Y * Kx; Gy = Y * Ky
M = sqrt(Gx² + Gy²)
M_display = 255*M/max(M)
```

At 3×3, the raw pair is exactly:

```text
Kx                 Ky
-1  0  1           -1 -2 -1
-2  0  2            0  0  0
-1  0  1            1  2  1
```

Each divisor is 8 at 3×3. At 5×5, S is `[1,4,6,4,1]` and D is `[-1,-2,0,2,1]`. Standard-library binomial coefficients and small explicit loops construct every size; larger kernels are not repeated, resized or zero-padded versions of 3×3.

Gx responds to changes across columns (vertical boundaries); Gy responds across rows (horizontal boundaries). Keep both signed float responses until combining them. With true convolution their signs are reversed relative to the usual correlation convention; magnitude is unchanged by that joint sign reversal. Larger kernels include broader smoothing and alter fine-edge detail.

Max-based **display normalization** maps the strongest response to 255 and can make weak edges appear prominent. It does not preserve absolute gradient strength across images or kernel sizes. If the maximum is ≤1e-10, use an all-black magnitude image to suppress floating-point residuals on constant images. Optional binary thresholding is off by default; when enabled, output white where normalized **float** magnitude ≥ threshold and black otherwise, before final export rounding. Threshold range is 0–255, default 128. Threshold 0 makes every pixel white, including a flat image.

### Visible kernel matrices

The expandable matrix panel requests the actual selected coefficients from Python. It shows raw/scaled coefficients with a divisor: dividing the matrix by that factor gives the normalized kernel passed to convolution, **before** both axes are reversed. Blur's factor is N²; sharpening displays the equivalent scaled matrix divided by N²; emboss/Sobel show raw coefficients divided by their absolute sum. Emboss strength/reversal and Sobel thresholding are later display operations, so they do not change these kernels. Sharpening amount does change its kernel.

Both Sobel matrices are shown. Small 3x3/5x5 matrices use KaTeX bracket notation with divisors. Larger sizes have compact mathematical definitions and expandable full numerical tables with bounded keyboard-scrollable regions; a 31x31 table never widens the page. Displayed decimals use six places; computation retains float64 precision. Metadata has its own cancellation/generation guard, so an old matrix response cannot replace the newly selected size/operation. This is a coefficient-only request; no image is sent until Apply on these two pages.

### Spatial verification and performance

Tests cover every supported size, prefix-sum equivalence to direct convolution on non-square/tiny/singleton arrays and reflected borders, constants, normalized kernel sums, sharpening amount zero, signed responses, dimensions, alpha and input immutability. The original direct-convolution/derivative tests remain passing.

```powershell
.\.venv\Scripts\python.exe -m backend.benchmark_spatial --sizes 31
```

**31x31 complete API times**, median of three TestClient requests, RGBA gradient, default sharpening amount. Includes parsing, decoding, filtering and PNG encoding; excludes network/browser time. Same Python/NumPy/Pillow environment as below. No export downscaling; compressed inputs were 5,718 and 52,765 bytes.

| Operation | 1200x800 (0.96 MP) | 4000x3000 (12 MP) |
| --- | --- | --- |
| Box blur, 31x31 | 80.6 ms | 1103.8 ms |
| Sharpen, 31x31 | 86.0 ms | 1150.6 ms |

Before optimization, the same project's 11x11 direct-filter API medians at 12 MP were 3734.2 ms for blur and 3703.7 ms for sharpen. These are development measurements, not concurrent production-load guarantees. Prefix sums still need image-sized float64 arrays; channel-wise processing bounds memory but a 12 MP request can use hundreds of MiB. Keep host concurrency bounded. Emboss/Sobel retain the direct engine and five sizes; their prior 12 MP/11x11 API medians were 1881.3/2955.1 ms. Existing 8 MiB/12 MP limits and the 60-second UI timeout remain unchanged.

## API documentation

Interactive OpenAPI documentation at `/docs` includes operation names, numeric ranges, defaults and processing order. See [docs/API.md](docs/API.md) for multipart fields, errors and examples, including `/inspect` and `/kernels`. Existing geometry requests with just `file` and `operation` remain valid. `GET /health` remains `{"status":"ok"}`.

## Verification and performance

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests
npm --prefix frontend run test:math
npm --prefix frontend run check
npm --prefix frontend run build
.\.venv\Scripts\python.exe -m backend.benchmark
```

Current glitch checks are reported above and in [docs/glitch.md](docs/glitch.md). The following records the earlier redesign baseline:

- **567 backend tests passed**, including the 467 tests that existed before that task. Spatial tests cover all seven box/sharpen sizes and five derivative sizes, kernel sums and constants, identity, asymmetric true convolution, independently mapped reflected borders, signed directional responses, sharpening clipping, emboss offset/reversal, generalized Sobel, binary thresholds, alpha, pixel ranges, input immutability, size/parameter validation, and actual display metadata. Earlier tests cover known grayscale/inversion values, double inversion, gamma identity and 0.5/2 examples, contrast endpoints/intermediates, shared visible-channel bounds, constant/transparent cases, grayscale expansion, alpha/dimensions/input immutability, independently calculated adjustment order, no premature clipping/rounding, invalid/NaN/infinite parameters, multipart defaults, inapplicable settings and metadata validation.
- **Astro check:** zero errors, warnings or hints. **Production build:** seven static pages (six tools plus FAQ).
- **Mathematics:** 17 Node tests pass for every static/dynamic operation template, explanatory equations, HTML+MathML output, preserved direct gamma convention, numeric formatting and safe rendering failure/trust handling.
- **Chrome, this redesign:** all six routes completed upload/Apply/preview/actual PNG download/Reset. Download bytes matched the preview blob. All 24 spatial operation-size combinations and every geometry/point selection processed successfully; Stage A additionally compared all 14 box/sharpen combinations pixel-for-pixel with Python.
- **Responsive/themes/math:** 36 layout checks at 1440/390/320 px across all routes and both themes, plus expanded mobile formulas and 31x31 tables. No page overflow or math-rendering fallback; HTML+MathML and locally loaded math fonts verified. Native numeric keyboard entry, all shared adjustments, invalid values, Auto-range recovery, binary threshold, relief reversal, local matrix keyboard scrolling, loading/errors and stale-result protection checked. OS detection/live changes and persisted explicit overrides across the six routes checked.
- Screenshots were visually inspected and the interface reviewed with frontend-design and web-design-guidelines. See [docs/interface-review.md](docs/interface-review.md). Firefox/Safari, physical mobile devices, dedicated screen readers and concurrent production load remain untested.

Median of three requests, RGBA gradient, Python 3.13.7, NumPy 2.5.4, Pillow 13.0.0. Complete API time includes parsing/decode/math/PNG encode through TestClient, excluding network and browser rendering:

| Input | Operation | NumPy | Complete API |
| --- | --- | --- | --- |
| 1200 × 800 | Rotate 90° | 3.6 ms | 28.9 ms |
| 1200 × 800 | Gamma + gains + saturation | 81.4 ms | 121.3 ms |
| 1200 × 800 | Contrast + gamma + saturation | 96.6 ms | 142.6 ms |
| 4000 × 3000 | Rotate 90° | 45.2 ms | 336.8 ms |
| 4000 × 3000 | Gamma + gains + saturation | 1015.6 ms | 1358.7 ms |
| 4000 × 3000 | Contrast + gamma + saturation | 1207.6 ms | 1609.4 ms |

Benchmark settings: gamma page γ=.7, red gain=1.1, s=1.2; contrast auto-range, γ=1.1, s=.8; other gains neutral. Compressed inputs are 8,156 bytes (0.96 MP) and 64,230 bytes (12 MP). Hardware, compressibility, settings and concurrency affect times; this is not a production-load capacity claim. PNG output may exceed the 8 MiB input limit, while the pixel limit still bounds dimensions.

Manual local check: upload a non-square transparent image, try each tool, expand colour adjustments/formulas, Apply, download/open the PNG, then Reset. Change the theme and navigate across the seven tools; reload to confirm persistence. Try a uniform gray image and fully transparent PNG on contrast. Try Surprise me with/without a glitch upload and repeated Apply. Tab through controls and use arrows on radios/sliders. Stop the backend and confirm a helpful error.

## Earlier presentation and content verification

For the typography/education/FAQ update, Astro check passed with zero diagnostics, the production build produced seven pages, and all 17 math tests passed. Chrome checked 70 light/dark layouts across all seven pages at 100% zoom and 1440/1024/768/390/320px widths. No page-wide overflow or math-rendering failures occurred. Screenshots were visually inspected; equations and controls were refined for mobile reading.

All six upload/Apply/preview/download/Reset workflows still produced pixel-identical Python results and matching download blobs. Numerical educational examples were checked against the processing functions. The FAQ was tested with native keyboard disclosure and multiple answers open; header anchors focus each permanent explanation. Production reading content and equations remain visible with JavaScript disabled, and the FAQ still works without scripts. Exact copy changes, transparency-note wrapping and the vector R at 16px were checked in both themes.

The processing/API code, editor/theme scripts, original formula definitions, kernel lists and limit code were unchanged, verified by SHA-256 comparison. This was a presentation update; no new DSP algorithm was added. See [the current interface review](docs/interface-review.md) for details and browser-testing limits.

## Remaining limitations

Cross-browser and screen-reader testing have not been performed; browser automation used Chrome with generated fixtures. Images/settings are not transferred between pages. EXIF/colour profiles are not copied. Contrast range inspection requires the backend and an additional upload. Processing work already started in a worker thread cannot be cancelled. Arbitrary-angle rotation, cumulative edits, accounts, galleries and storage are outside this milestone. Spatial filtering keeps straight RGB values and the original alpha; hidden transparent colours can influence neighbouring pixels. Large matrices and wide equations scroll internally. Six-place matrix display formatting is approximate; computation retains float64 precision. Kernel metadata needs the Python API even before upload. Concurrent production load has not been benchmarked.
