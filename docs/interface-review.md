# Interface review: Glitch effect

Reviewed the new page and changed shared controls using frontend-design and the freshly fetched [Web Interface Guidelines](https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md). Retained Raster Lab's existing design; no new UI framework or dependency. Reference glitch URL was unavailable (network blocked); no reference visual inspection is claimed for this task.

- `frontend/src/components/RangeControl.astro:6` — pass: labelled native sliders, associated descriptions, synchronized integer number fields, explicit percent suffix, accessible percent value text, nearby validation and existing keyboard focus.
- `frontend/src/components/Editor.astro:42` — pass: exactly four glitch sliders; native Surprise action below them; shared original/output, loading/status, Reset and PNG download. Source-based Apply explanation remains visible.
- `frontend/src/scripts/editor.ts:320` — pass: Surprise uses curated values/cryptographic seed, clears invalid fields, updates formulas and auto-submits once only with upload. Existing abort/generation and blob lifetime handling retained; tested with a deliberately delayed old response.
- `frontend/src/math-definitions.ts:12` — pass: compact stage equations render HTML+MathML with trust disabled; current parameters update without requests. Wide math scrolls inside focusable regions. Condensed formula after first rendered review to leave more room for previews.
- `frontend/src/content/education.ts:17` — pass: six permanent semantic subsections, static KaTeX, precise wrapping/order/alpha/seed explanations. New section remains present with script execution disabled.
- `frontend/src/styles/editor.css:55` — pass: eight navigation links retain active/focus states and readable type; two-column mobile navigation pairs Glitch effect with FAQ. Both theme tokens style controls, previews and equations without filtering image pixels.

Actual Chrome checks: normal zoom, all eight pages × two themes × five widths (1440/1024/768/390/320), no page overflow/formula fallback. Each glitch slider separately/combined, real PNG pixel equivalence/download, Surprise both states, integer invalid recovery, keyboard slider/focus, source-based repeated Apply, Reset/new uploads/drop, loading/error recovery, stale response and revoked URL. Six previous editors passed default upload/Apply/pixel/Reset checks. Native FAQ keyboard, theme OS preference/persistence, and education anchor passed. Finished desktop/mobile screenshots were viewed in both themes; captures in `docs/design/raster-glitch-*.png`.

No unresolved finding in the new feature scope. Other browsers, physical devices and dedicated screen readers were not tested. Detailed verification and measurements: [glitch.md](glitch.md).

## Earlier typography/content review

Reviewed the changed interface with the installed frontend-design and web-design-guidelines skills. The current [Web Interface Guidelines](https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md) were fetched for this review. Vayce's educational and FAQ sections were inspected in Chrome as layout references; Raster Lab's explanations were written against its own NumPy implementation.

## Current findings

- `frontend/src/layouts/SiteLayout.astro:35` — pass: shared original vector R, unchanged wordmark, labelled native navigation and one active page. Six tools plus FAQ share early theme application and the two-part footer. Decorative mark is hidden from assistive technology.
- `frontend/src/components/HowItWorks.astro:9` — pass: a permanent semantic section, labelled h2/h3 hierarchy, no disclosure controls, keyboard-focusable anchor target, statically rendered paragraphs and HTML+MathML equations. Five topics for geometry/point; six for each other tool.
- `frontend/src/styles/editor.css:11` — pass: shared 16px body, 14-15px supporting/control text and 12px secondary metadata. Reading text is 17-18px on desktop and 16px on mobile, with a 76ch maximum measure and 1.75 line height. Headings are 22-26px. Math fonts remain intact and overflow stays local.
- `frontend/src/pages/faq.astro:9` — pass: 15 native details/summary cards, multiple answers allowed, keyboard disclosure state, visible focus and decorative plus/minus indicators. No custom accordion script.
- `frontend/src/components/Editor.astro:71` — pass: requested transparency sentence wraps beside/before Download without collision. The grayscale replacement is exact in initial and live selected states; inversion retains its own explanation.
- `frontend/public/favicon.svg:1` — pass: one geometric, font-independent SVG source is used in the header and favicon. Inspected at native 16, 24 and 32px on both background colours; header colour follows theme tokens.

No outstanding findings in the changed scope. The processing engine, API, editor/theme scripts, original formula definitions, kernel lists and configured limit code are byte-identical to the task's starting versions (SHA-256 comparison).

## Actual checks for this update

- Astro check: zero errors, warnings or hints. Production build: seven static pages. All 17 existing math tests pass.
- Chrome at 100% zoom (device pixel ratio 1 and visual viewport scale 1): 70 layout/theme checks across all seven pages at 1440, 1024, 768, 390 and 320px. No page-level horizontal overflow or equation-rendering fallback. Desktop and mobile screenshots were visually inspected in both themes; short educational examples were reformatted into multiple lines after mobile review.
- All six tools completed upload, Apply, PNG preview, actual download and Reset. Preview pixels matched the Python functions, including alpha; download bytes matched the preview response. Existing algorithms and controls were preserved.
- Published grayscale, inversion, gamma 0.5/2, contrast and rotation numerical examples were verified with the actual processing functions.
- Header anchors reached and focused each tool's permanent reading section. Native Enter/Space FAQ disclosure, multiple open answers, keyboard focus and theme persistence were exercised. Production first paint used the OS dark preference before an explicit choice.
- With JavaScript disabled, every production tool's reading section had visible layout and static equations. The FAQ still expanded with native Space input.
- Expanded 31x31 sharpening and 11x11 emboss/Sobel matrices were also checked at 1440/320px in both themes, with the larger type and no page overflow.
- Final production checks verified the refined type sizes and short equation layouts at desktop/mobile widths. Exact grayscale/inversion selection copy and transparency-note wrapping were checked in both themes at 1440/390/320px.

Current screenshots: [education light](design/raster-education-light.png), [education dark](design/raster-education-dark.png), [FAQ light](design/raster-faq-light.png), [FAQ dark](design/raster-faq-dark.png), [R at small sizes](design/raster-r-sizes.png).

Firefox/Safari, physical mobile hardware and dedicated screen readers were not tested. Production-build checks cover static content/theme/assets; image workflow tests used the existing development frontend/API origins. The application's default 8 MiB / 12 MP limits remain in force.

---

# Earlier review: two-theme redesign


Reviewed the six-page editor using the installed **frontend-design** and **web-design-guidelines** skills. The current [Web Interface Guidelines](https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md) were fetched for the review. The [Vayce gamma reference](https://vayce.app/tools/gamma-correction/) was visually inspected in both themes using Chrome; its light/dark captures are in `docs/design/`. The project retains its own branding and direct-exponent gamma.

## Design and implementation

Warm off-white/cream light and blue-charcoal dark palettes share an amber accent, a quiet 32px CSS technical grid, diagonal upload/empty hatching, thin borders, restrained corners and clear active navigation. Barlow Condensed bold headings and KaTeX fonts are bundled locally; body/technical text uses reliable system sans/monospace fallbacks. Mathematical fonts are not overridden. Images use contain fitting with themed checkers and no theme filters.

The desktop editor uses a two-thirds original/output workspace and one-third control rail. Mobile stacks upload/controls, visible formulas and large previews. The selected formula is visible above the comparison, with current values, concise explanations and optional deeper mathematics. No marketing hero precedes the tool.

## Findings resolved

- `frontend/src/styles/editor.css:1` — shared semantic light/dark tokens now cover every control, checker, formula, matrix, error, disabled and loading state; filled amber sliders and keyboard focus are consistent. Motion respects reduced-motion preferences.
- `frontend/src/components/RangeControl.astro:7` — synchronized numerical inputs have labels, native range/step validation and nearby error messages; sliders retain keyboard controls.
- `frontend/src/scripts/editor.ts:94` — Auto-range clears invalid number state. Number fields inherit fieldset disabling naturally and become editable after contrast analysis. These behaviours were checked with native keyboard entry, not only DOM assignment.
- `frontend/src/components/Math.astro:7` — equations use HTML+MathML, application-owned templates, pre-rendered static math, targeted live updates, readable local overflow and focusable equation regions.
- `frontend/src/math-render.ts:2` — KaTeX trust is disabled; invalid templates fall back gracefully without displaying raw commands or breaking the editor. No document-wide auto-render scan.
- `frontend/src/scripts/kernel-display.ts:1` — actual Python coefficients appear as 3x3/5x5 LaTeX matrices; larger sizes use compact definitions and expandable, keyboard-scrollable full tables. Both Sobel kernels and divisors are retained.
- `frontend/src/layouts/ToolLayout.astro:18` — theme is set in the head before paint. Native links retain routes and aria-current; the toggle retains its accessible pressed state and storage/OS behaviour.

## Actual verification

Chrome tested all six pages through upload, Apply, preview, actual PNG download and Reset. Download bytes matched the displayed response blob. All 24 spatial operation-size combinations processed; every geometry/point selection, reverse emboss and binary Sobel formulas were exercised. Stage A checked all 14 box/sharpen combinations pixel-for-pixel against Python.

36 responsive checks covered all six pages in both themes at 1440, 390 and 320px; screenshots were visually inspected at desktop/mobile sizes. Additional mobile checks opened detailed mathematics and 31x31 tables; the 768px large-matrix layout was also checked. Equations/matrices scroll locally without page overflow. No raw-source fallback or runtime exceptions occurred. Static production pages contain KaTeX HTML and MathML; the four used heading/math font assets returned HTTP 200 from local hashed build paths.

Native keyboard tests covered numeric entry for contrast and all five shared adjustments, invalid-value errors, Auto-range recovery, keyboard theme toggling, visible focus and matrix horizontal scrolling. Theme checks covered first-visit OS detection, live OS changes, explicit persistence across all routes/navigation, blocked storage and first-contentful-paint dark theme in the production build. Reduced motion disables spinner animation. Loading/error states were inspected in both themes using delayed/injected responses; changing settings prevented delayed results from becoming current.

Measured semantic contrast ratios:

| Pair | Light | Dark |
| --- | --- | --- |
| Primary text / surface | 16.17:1 | 14.47:1 |
| Muted text / surface | 5.90:1 | 7.30:1 |
| Formula text / formula surface | 14.33:1 | 15.03:1 |
| Parameters / formula surface | 5.60:1 | 9.38:1 |
| Primary button text / accent | 5.34:1 | 7.24:1 |
| Error text / error surface | 5.79:1 | 9.23:1 |
| Control outline / surface | 3.12:1 | 3.46:1 |

No outstanding findings in the reviewed scope. Firefox/Safari, physical devices, dedicated screen readers and concurrent production load were not tested. This is not a full assistive-technology certification. Finished local screenshots: [light](design/raster-lab-light.png), [dark](design/raster-lab-dark.png).
