# Image Processing Lab API

Local base URL: `http://localhost:8000`. Interactive documentation: `/docs`; schema: `/openapi.json`. All endpoints are stateless. Configure the API base URL in the frontend and allowed browser origins in the backend as described in the root README.

## Health

`GET /health` → `200 application/json`, `{"status":"ok"}`.

## Process an original image

`POST /process`, multipart form data. Supply a new copy of the **original** file on every Apply. The server has no editing session or saved image.

| Field | Default / requirements |
| --- | --- |
| `file` | Required binary still JPEG, PNG or WebP, up to configured byte/pixel limits |
| `operation` | Required: `horizontal_flip`, `vertical_flip`, `rotate_90`, `rotate_180`, `rotate_270`, `grayscale`, `inversion`, `gamma`, `contrast`, `blur`, `sharpen`, `emboss`, `sobel`, `glitch` |
| `gamma` | Finite number, inclusive `0.1..3`, default `1`; direct exponent |
| `red_gain` | Finite number, inclusive `0..2`, default `1` |
| `green_gain` | Finite number, inclusive `0..2`, default `1` |
| `blue_gain` | Finite number, inclusive `0..2`, default `1` |
| `saturation` | Finite number, inclusive `0..2`, default `1` |
| `black_point` | Optional finite number `0..255`; contrast only; supply with `white_point` |
| `white_point` | Optional finite number `0..255`; contrast only; must exceed `black_point` |
| `kernel_size` | Integer: Blur/sharpen: exactly `3`, `5`, `7`, `9`, `11`, `21`, `31`; Emboss/Sobel: `3`, `5`, `7`, `9`, `11`; default `3`; spatial operations |
| `amount` | Sharpen only: finite `0..2`, default `1` |
| `strength` | Emboss only: finite `0..2`, default `1` |
| `reverse_relief` | Emboss only: boolean, default `false` |
| `binary_threshold` | Sobel only: boolean, default `false` (continuous grayscale) |
| `threshold` | Sobel: finite `0..255`, default `128`; used only when binary thresholding is enabled |
| `shift` | Glitch RGB separation intensity: integer `0..100`, default `0` |
| `tear` | Glitch horizontal band intensity: integer `0..100`, default `0` |
| `noise` | Glitch shared-channel static intensity: integer `0..100`, default `0` |
| `scanlines` | Glitch odd-row darkening intensity: integer `0..100`, default `0` |
| `seed` | Glitch integer seed, inclusive `0..4294967295`, default `0` |

Fields are multipart text values, not a JSON request body. Fractional bounds are accepted by the API; the interface's black/white sliders use integer steps. Omit both bounds for automatic contrast range. Explicit equal/reversed bounds or only one bound return `422`. Geometry, grayscale and inversion reject non-neutral adjustments; all non-contrast operations reject explicit contrast bounds. Non-finite values (`NaN`, `Infinity`, `-Infinity`), non-numeric values and out-of-range numbers return `422`, including when inapplicable to the selected operation.

Point gamma/gains/saturation are available only for `gamma` and `contrast`. Other operations reject non-neutral values. Non-default spatial settings are rejected for inapplicable operations (for example `amount=2` with Blur, or `kernel_size=5` with Gamma). Kernel sizes not in the operation-specific set are rejected, including even sizes and fractional numbers. Boolean form fields accept standard FastAPI boolean text, including `true` and `false`.

### Arithmetic contract

**Glitch:** `operation=glitch` uses shift -> tearing -> noise -> scanlines -> final rounding/clipping. The integer intensities scale effect strength, not image-width percentages. Red/right and blue/left shift by `round(.03*W*shift/100)` with horizontal wrap. Tearing uses up to 12 seeded strips with circular RGB displacement. Shared RGB uniform noise has amplitude `64*noise/100`; odd rows then multiply by `1-.85*scanlines/100`. Separate local PCG64 streams are spawned from seed for tearing/noise. All-zero copies decoded samples exactly with L/LA expansion to RGB/RGBA. Alpha always remains at source coordinates. Uses float32 and bounded noise blocks, final nearest/ties-even round and clipping. Repeated identical requests give identical pixels. Non-default glitch fields on other operations return 422; existing operation contracts are unchanged. See [glitch.md](glitch.md) for precise band construction.

```powershell
curl.exe -f http://localhost:8000/process -F "file=@C:/images/photo.png" -F "operation=glitch" -F "shift=65" -F "tear=50" -F "noise=20" -F "scanlines=35" -F "seed=42" --output glitch.png
```

- Geometry uses the existing exact index mappings, including width/height swaps for quarter turns.
- Grayscale: `Y=.299R+.587G+.114B`; output `R'=G'=B'=Y`. Y approximates encoded intensity/luma, not physical luminance.
- Inversion: `C'=255-C` on RGB only.
- Gamma: `255*(p/255)^gamma`, independently on RGB, followed by RGB gains and saturation. Gamma below 1 brightens, above 1 darkens.
- Contrast: `clip(255*(p-a)/(b-a),0,255)` with **one shared** a/b pair for RGB. Then optional gamma with the same formula, RGB gains, saturation.
- Blur: `I*K_box`, where every coefficient is `1/N²`; process RGB independently.
- Sharpen: mathematically convolve with `(1+amount)*delta - amount*K_box`, equivalent to `I + amount*(I-I*K_box)`; kernel sum 1, amount 0 identity.
- Emboss: floating `Y=.299R+.587G+.114B`; centred raw `i+j`, divided by its absolute sum. Display `128 + strength*(Y*K_emboss)`; reverse relief negates the signed response before offset.
- Sobel: binomial smoothing S (order N−1), derivative D (full convolution of `[-1,0,1]` with binomial order N−3), outer products for Kx/Ky divided by their absolute sums. Combine signed Gx/Gy as `sqrt(Gx²+Gy²)` before clipping. Normalize magnitude by its maximum to 0–255 for display; maximum ≤1e-10 yields black. If binary enabled, threshold normalized float values with `>= threshold` before rounding. Threshold 0 yields white everywhere.
- Gains: `C_gain=gain_C*C`. Compute `Y=.299R_gain+.587G_gain+.114B_gain` **after gains**; saturation is `C_out=Y+s*(C_gain-Y)`. Saturation 0 gives grayscale, 1 is neutral, above 1 increases colourfulness.
- Existing point/spatial operations work in float64 without rounding/clipping between adjustments, except contrast's defined base clip; glitch uses float32. Final export is `clip(rint(values),0,255).astype(uint8)`; `rint` rounds nearest, ties to even. Neutral gamma/saturation use exact identity paths. Alpha bypasses all arithmetic and is copied unchanged.

Automatic contrast bounds use the global RGB channel extrema of the orientation-normalized original, ignoring alpha-zero pixels. Partial alpha counts without weighting. If the automatic range has equal bounds or no visible pixels, **skip only the base stretch**, retaining original base values. Later gamma/gains/saturation still apply. This bypass is available only for automatic ranges; equal manual bounds are invalid.

Point/spatial operations expand grayscale L/LA to RGB/RGBA with NumPy. Emboss/Sobel return equal RGB channels, with source alpha unchanged. All spatial filters use reflect padding excluding the edge sample and true convolution (reverse both kernel axes), preserve dimensions, and retain signed float intermediates. They filter straight RGB values, including hidden colours; alpha is separated and reattached without filtering. Geometry retains its existing channel layout. Palette and colour-key transparency become RGBA; bilevel becomes grayscale. Unsupported modes and animations are rejected. See the root README for full EXIF/colour-mode policies and mathematics.

### Response

`200 image/png`, with a download filename and `Cache-Control: no-store`. Headers exposed through CORS:

- `X-Original-Width`, `X-Original-Height`: after EXIF normalization.
- `X-Output-Width`, `X-Output-Height`: actual PNG dimensions.

No resizing or alpha flattening occurs. EXIF, ICC profiles, DPI and ancillary metadata are not copied. The browser previews and downloads this same PNG blob.

```powershell
# Existing geometry requests remain valid.
curl.exe -f http://localhost:8000/process -F "file=@C:/images/photo.png" -F "operation=rotate_90" --output rotated.png

curl.exe -f http://localhost:8000/process -F "file=@C:/images/photo.png" -F "operation=grayscale" --output grayscale.png

curl.exe -f http://localhost:8000/process -F "file=@C:/images/photo.png" -F "operation=gamma" -F "gamma=0.5" -F "red_gain=1.1" -F "saturation=0.8" --output gamma.png

curl.exe -f http://localhost:8000/process -F "file=@C:/images/photo.png" -F "operation=contrast" -F "black_point=30" -F "white_point=220" -F "gamma=1.2" --output contrast.png

# Automatic range: omit both bounds.
curl.exe -f http://localhost:8000/process -F "file=@C:/images/photo.png" -F "operation=contrast" --output automatic.png

curl.exe -f http://localhost:8000/process -F "file=@C:/images/photo.png" -F "operation=blur" -F "kernel_size=31" --output blur.png

curl.exe -f http://localhost:8000/process -F "file=@C:/images/photo.png" -F "operation=sharpen" -F "kernel_size=7" -F "amount=1.5" --output sharpen.png

curl.exe -f http://localhost:8000/process -F "file=@C:/images/photo.png" -F "operation=emboss" -F "kernel_size=5" -F "strength=1.2" -F "reverse_relief=true" --output emboss.png

curl.exe -f http://localhost:8000/process -F "file=@C:/images/photo.png" -F "operation=sobel" -F "kernel_size=9" -F "binary_threshold=true" -F "threshold=100" --output edges.png
```

## Inspect original dimensions and contrast range

`POST /inspect`, multipart `file` only. Uses the same file/format/mode/animation/size/EXIF validation as `/process`. It decodes original pixels for analysis and returns metadata, with no edited-image output or retention. The contrast page calls this once per upload; Auto-range and Reset reuse the returned metadata.

`200 application/json`, `Cache-Control: no-store`:

```json
{
  "width": 900,
  "height": 600,
  "black_point": 29,
  "white_point": 255,
  "range_status": "ready"
}
```

`range_status` is `ready` for distinct bounds, `constant` for equal bounds, or `transparent` for no visible pixels. Transparent images return `null` for both bounds. Width/height reflect normalized orientation. The typed OpenAPI response documents these fields.

```powershell
curl.exe -f http://localhost:8000/inspect -F "file=@C:/images/photo.png"
```

## Kernel metadata (no image upload)

`GET /kernels?operation=sobel&kernel_size=3`

Query fields: required `operation` (`blur`, `sharpen`, `emboss`, `sobel`); `kernel_size` default 3, blur/sharpen 3/5/7/9/11/21/31, emboss/Sobel 3/5/7/9/11; finite `amount` 0–2, default 1, used for the sharpening kernel only. This lightweight endpoint uses the same Python generators as image processing. It returns typed OpenAPI metadata; no image is decoded or filtered.

```json
{
  "operation": "sobel",
  "kernel_size": 3,
  "kernels": [
    {
      "name": "Kx",
      "coefficients": [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]],
      "divisor": 8,
      "normalized_sum": 0
    },
    {
      "name": "Ky",
      "coefficients": [[-1, -2, -1], [0, 0, 0], [1, 2, 1]],
      "divisor": 8,
      "normalized_sum": 0
    }
  ],
  "convention": "Displayed coefficients divided by divisor give the kernel before true-convolution reversal."
}
```

`coefficients / divisor` is the normalized kernel before reversal. Blur/sharpen divisors are N²; emboss/Sobel divisors are the raw absolute coefficient sum. Sharpen coefficients are its equivalent kernel scaled by N². Both Sobel matrices are returned. Strength, relief reversal and threshold are subsequent response/display settings, so they do not alter the displayed emboss/Sobel kernels. Matrix display rounds decimals to six places while calculations retain float64 precision.

The frontend may request these small matrices as operation/size/amount changes; **image processing still happens only on Apply**. Unknown operations, disallowed sizes, or invalid/non-finite amount return `422`.

```powershell
curl.exe -f "http://localhost:8000/kernels?operation=sharpen&kernel_size=11&amount=1.5"
```

## Errors, limits and cleanup

| Status | Meaning |
| --- | --- |
| `400` | Empty, corrupt, truncated or undecodable image/malformed upload |
| `413` | File exceeds `MAX_UPLOAD_BYTES` or decoded dimensions exceed `MAX_IMAGE_PIXELS` |
| `415` | Unsupported actual format, colour mode, 16-bit PNG or animation |
| `422` | Missing fields, unknown operation, invalid/non-finite/out-of-range/inapplicable settings, or invalid manual bounds |

Error bodies have a `detail` field. Explicit image/parameter errors use readable strings. FastAPI field-validation errors use an array of objects with `loc`, `msg` and `type`; clients should support both shapes. Do not assume every error response is an image.

Defaults: 8 MiB per file, 12 million pixels, plus a hard request-body ceiling of file limit + 64 KiB for multipart overhead, including chunked uploads. The pixel limit applies before full decoding. Downloads preserve full dimensions and may be larger in bytes than the uploaded file. Multipart temporary resources close on success/error. Decode/math/encode execute in a worker thread; cancellation cannot interrupt already-running CPU work. No uploaded/result image is retained after its request.

Blur/sharpen use separable prefix-sum box averaging with the exact existing reflect convention. Sharpen computes I + amount*(I-B), equivalent to its displayed kernel. The direct float64 convolution remains the reference. Larger matrices retain their real NxN coefficients in expandable, internally scrollable tables. Sizes 21/31 are valid only for blur/sharpen; the maximum supported box size is 31. The UI slider sends an actual size, never its internal list index. KaTeX renders equations and small matrices locally; numerical tables retain access to all coefficients.
