# Glitch effect

Route: `/glitch-effect`, seventh tool, before FAQ. Multipart `/process` operation: `glitch`. Still images only; existing JPEG/PNG/WebP validation, EXIF policy, 8 MiB/12 MP limits and PNG exports are reused. No new dependencies.

## Controls, mapping and order

Exactly four integer sliders from 0 to 100, default 0, with synchronized numeric percentage fields. Let r=shift/100, t=tear/100, n=noise/100, s=scanlines/100; W/H are width/height. These are effect intensities, not literal displacement percentages.

1. **RGB Shift:** d=round(.03Wr), nearest ties to even. Red samples `(x-d) mod W`, green stays put, blue samples `(x+d) mod W`. Zero bypasses this stage. A positive setting may round to zero on narrow images.
2. **Horizontal Tearing:** for positive t choose ceil(12t) bands. Heights are random inclusive integers between max(1,round(.005H)) and min(H-1,max(lower,round(.04H))), clamping the lower bound to the upper if needed. Each start lies in 0..H-height. Displacement magnitude is a uniform integer 1..min(W-1,max(1,round(.12Wt))), with a random sign. Roll complete RGB strips horizontally; bands may overlap and apply sequentially. No single band spans all rows. H<2 or W<2 skips tearing. Zero chooses no bands. Integer minima dominate the approximate percentages on tiny images.
3. **Static Noise:** A=64n; one float32 uniform sample in [-A,A) per pixel is added equally to RGB. Expected mean is zero, though a finite realization may have a nonzero mean. No independent colour speckles or early clipping. Zero bypasses sampling.
4. **Scanlines:** even rows stay unchanged; odd zero-based rows multiply by 1-.85s, including noise already present. At 100%, odd rows retain 15%. This is row-dependent amplitude modulation, not convolution.
5. **Export:** nearest/ties-even rounding, clip to 0..255, uint8 conversion, then original alpha at original coordinates. No intermediate clipping.

All-zero takes an exact integer copy path. L/LA expand to RGB/RGBA like other colour tools. Width/height never change; input arrays are untouched. Alpha is never rolled, darkened or noised. This straight-RGB artistic choice can change colours under partial transparency. It is not premultiplied-alpha filtering, actual file corruption or codec datamoshing. Decoded pixel identity does not mean compressed-byte identity.

## Repeatability and browser state

Seed is an unsigned 32-bit integer, 0..4294967295, default 0. `SeedSequence(seed).spawn(2)` supplies local PCG64 streams independently for tearing and noise. Noise does not redraw tearing; tearing's random consumption does not alter noise. Reproducibility applies to identical images/settings/seeds in this implementation, not an asserted cross-version random-file standard.

Manual slider/numeric changes update formulas without requests or changing seed. Apply always submits the original file. `Surprise me` uses `crypto.getRandomValues`, chooses a curated profile and a fresh seed, updates all four values, and auto-applies exactly once if an image is loaded. Equal seed draws are adjusted to ensure the new seed differs from the page's prior seed. Profiles (inclusive ranges in shift/tear/noise/scanlines order):

| Profile | Shift | Tear | Noise | Scanlines |
| --- | --- | --- | --- | --- |
| Colour split | 55–90 | 0–12 | 0–8 | 5–25 |
| Broken signal | 15–45 | 40–75 | 15–35 | 30–65 |
| Soft interference | 10–30 | 5–25 | 5–15 | 10–30 |
| Heavy glitch | 45–85 | 55–90 | 20–45 | 40–75 |

Reset retains the original upload, discards the result and restores zero controls/seed. New uploads also restore defaults, following existing editors. No uploaded image or seed is persisted. Abort controllers and generation guards protect newer results; obsolete blob URLs are revoked.

## Implementation and performance

`backend/processing/glitch.py` owns validation, band construction and the NumPy pipeline. One owned float32 RGB workspace uses 144 MB decimal at 12 MP; input, output, roll temporaries, decoding and PNG encoding require additional memory. Noise is generated in 128-row blocks and broadcast over channels. Final rounding/clipping reuse the workspace. Small loops visit bands/blocks, never individual pixels. CPU work remains in the API worker thread.

Actual local medians, three runs, all stages active (65/70/30/40, seed42), RGBA synthetic gradient input:

| Dimensions | NumPy pipeline | Complete TestClient API |
| --- | --- | --- |
| 1200×800 | 18.3 ms | 154.0 ms |
| 4000×3000 (12 MP) | 283.2 ms | 1954.6 ms |

API measurement includes multipart parsing, decoding and PNG encoding, but excludes network/browser time. PNG compressibility affects latency. These are local measurements, not throughput or concurrent-load guarantees. No exported resizing or larger-image support was added.

## Verification

- 696 backend tests passed (129 new): exact zero samples, known wrapped shifts/rounding, known seeded bands and noise, scanline parity, order before clipping, independent streams, repeatability/different seeds, alpha/dimensions/input immutability, tiny/non-square images and multipart validation/reused limits.
- 20 frontend math/settings tests passed; Astro check has zero diagnostics; build generated eight static pages. KaTeX uses HTML+MathML with trust disabled, including static educational formulas.
- Actual headless Chrome, normal 100% zoom: file picker and drag/drop; independent and combined settings; preview pixels compared to Python; repeated Apply; Surprise with/without image and exactly one auto-request; integer validation and keyboard sliders/focus; delayed older response rejected; obsolete blob revoked; loading/errors/recovery; actual download bytes equal preview; Reset and replacement uploads.
- Existing six editors passed default upload/Apply/pixel/Reset checks. Eight routes passed both themes at 1440/1024/768/390/320px (80 layouts) without page overflow or formula fallbacks. Active navigation, FAQ native keyboard, theme OS default/persistence and education anchor checked. Finished screenshots in `docs/design/raster-glitch-light.png` and `raster-glitch-dark.png`.
- Reference URL could not be viewed: web access failed and Chrome reported `ERR_NETWORK_ACCESS_DENIED`. Followed the requested mathematical workflow and existing design. Firefox/Safari, physical mobile devices, dedicated screen readers and concurrent load were not tested.

Web-design-guidelines review of the changed interface: labelled native sliders/numbers/buttons, supporting text associations, visible focus, live status, local math scrolling, responsive navigation, preserved colour tokens and reduced-motion rules. No unresolved feature-specific accessibility finding; this is not a screen-reader certification.
