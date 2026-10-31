"""Stateless upload -> EXIF normalization -> NumPy -> PNG API."""

from dataclasses import dataclass
from io import BytesIO
import os
from typing import Annotated, Literal

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError
from starlette.concurrency import run_in_threadpool
from starlette.types import ASGIApp, Receive, Scope, Send

from backend.processing.geometry import OPERATIONS
from backend.processing.glitch import glitch_effect, DEFAULT_SEED, MAX_SEED
from backend.processing.kernels import SpatialOperation, kernel_description, validate_size
from backend.processing.spatial import box_blur, sharpen, emboss, sobel_edges
from backend.processing.point import (
    contrast_stretch, gamma_correction, grayscale, inversion, visible_range,
    validate_adjustments, validate_bounds,
)

Operation = Literal[
    "horizontal_flip", "vertical_flip", "rotate_90", "rotate_180", "rotate_270",
    "grayscale", "inversion", "gamma", "contrast",
    "blur", "sharpen", "emboss", "sobel", "glitch",
]


@dataclass(frozen=True)
class Settings:
    max_upload_bytes: int = 8 * 1024 * 1024
    max_pixels: int = 12_000_000
    allowed_origins: tuple[str, ...] = (
        "http://localhost:4321", "http://127.0.0.1:4321"
    )

    def __post_init__(self):
        if self.max_upload_bytes <= 0 or self.max_pixels <= 0:
            raise ValueError("Upload and pixel limits must be positive.")

    @classmethod
    def from_env(cls):
        defaults = cls()
        return cls(
            max_upload_bytes=int(os.getenv("MAX_UPLOAD_BYTES", defaults.max_upload_bytes)),
            max_pixels=int(os.getenv("MAX_IMAGE_PIXELS", defaults.max_pixels)),
            allowed_origins=tuple(
                origin.strip() for origin in os.getenv(
                    "ALLOWED_ORIGINS", ",".join(defaults.allowed_origins)
                ).split(",") if origin.strip()
            ),
        )


class UploadBodyLimit:
    """Bound multipart traffic, including chunked bodies, before it is spooled.

    The file has its own exact limit; 64 KiB accommodates multipart headers
    and the operation field. No Content-Length header is trusted as proof.
    """

    def __init__(self, app: ASGIApp, max_bytes: int):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http" or scope["path"] not in {"/process", "/inspect"}:
            return await self.app(scope, receive, send)
        received = 0

        async def bounded_receive():
            nonlocal received
            message = await receive()
            received += len(message.get("body", b""))
            if received > self.max_bytes:
                raise HTTPException(413, "Upload is too large. Choose a smaller image.")
            return message

        await self.app(scope, bounded_receive, send)


def decode_image(data: bytes, settings: Settings) -> np.ndarray:
    """Validate before full decoding, then normalize orientation and modes."""
    try:
        with Image.open(BytesIO(data)) as source:
            if source.format not in {"JPEG", "PNG", "WEBP"}:
                raise HTTPException(415, "Unsupported image format. Use JPEG, PNG, or WebP.")
            if source.width * source.height > settings.max_pixels:
                raise HTTPException(
                    413, f"Image exceeds the {settings.max_pixels:,} pixel limit. Choose a smaller image."
                )
            if getattr(source, "is_animated", False):
                raise HTTPException(415, "Animated images are not supported. Use a still image.")
            # Pillow exposes 16-bit RGB/RGBA PNGs as 8-bit RGB/RGBA modes.
            # Inspect the PNG IHDR bit depth to avoid silently losing precision.
            if source.format == "PNG" and data[12:16] == b"IHDR" and data[24] > 8:
                raise HTTPException(415, "16-bit PNG images are not supported. Export an 8-bit image.")
            if source.mode not in {"1", "L", "LA", "P", "RGB", "RGBA"}:
                raise HTTPException(415, "Unsupported colour mode. Export an 8-bit grayscale, RGB, or RGBA image.")
            # Pillow is used only for metadata normalization and image I/O.
            source.load()
            normalized = ImageOps.exif_transpose(source)
            if normalized.mode == "P" or "transparency" in normalized.info:
                normalized = normalized.convert("RGBA")
            elif normalized.mode == "1":
                normalized = normalized.convert("L")
            return np.array(normalized)
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise HTTPException(413, "Image dimensions are too large. Choose a smaller image.") from exc
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError) as exc:
        raise HTTPException(400, "Cannot decode this image. Upload a valid JPEG, PNG, or WebP file.") from exc



class ImageInfo(BaseModel):
    width: int
    height: int
    black_point: int | None
    white_point: int | None
    range_status: Literal["ready", "constant", "transparent"]


class KernelMatrix(BaseModel):
    name: str
    coefficients: list[list[float]]
    divisor: float
    normalized_sum: float


class KernelDescription(BaseModel):
    operation: SpatialOperation
    kernel_size: int
    kernels: list[KernelMatrix]
    convention: str


def inspect_image(data: bytes, settings: Settings) -> dict:
    pixels = decode_image(data, settings)
    a, b = visible_range(pixels)
    return ImageInfo(
        width=pixels.shape[1], height=pixels.shape[0], black_point=a, white_point=b,
        range_status="transparent" if a is None else "constant" if a == b else "ready",
    ).model_dump()


def process_image(data: bytes, operation: Operation, settings: Settings,
                  parameters: dict | None = None) -> Response:
    """Decode, calculate and encode on a worker thread; never retain images."""
    pixels = decode_image(data, settings)
    parameters = parameters or {}
    if operation in OPERATIONS:
        result = OPERATIONS[operation](pixels)
    elif operation == "grayscale":
        result = grayscale(pixels)
    elif operation == "inversion":
        result = inversion(pixels)
    elif operation == "gamma":
        result = gamma_correction(pixels, **parameters)
    elif operation == "contrast":
        result = contrast_stretch(pixels, **parameters)
    elif operation == "glitch":
        result = glitch_effect(pixels, **parameters)
    else:
        filters = {"blur": box_blur, "sharpen": sharpen, "emboss": emboss, "sobel": sobel_edges}
        result = filters[operation](pixels, **parameters)
    output = BytesIO()
    Image.fromarray(result).save(output, format="PNG")
    return Response(
        output.getvalue(), media_type="image/png",
        headers={
            "Content-Disposition": f'attachment; filename="image-{operation}.png"',
            "Cache-Control": "no-store",
            "X-Original-Width": str(pixels.shape[1]),
            "X-Original-Height": str(pixels.shape[0]),
            "X-Output-Width": str(result.shape[1]),
            "X-Output-Height": str(result.shape[0]),
        },
    )


async def read_upload(file: UploadFile, settings: Settings) -> bytes:
    """Bound the read and close temporary uploads on success and error."""
    try:
        data = await file.read(settings.max_upload_bytes + 1)
        if len(data) > settings.max_upload_bytes:
            raise HTTPException(413, f"File exceeds the {settings.max_upload_bytes:,} byte limit. Choose a smaller image.")
        if not data:
            raise HTTPException(400, "The uploaded file is empty. Choose an image.")
        return data
    finally:
        await file.close()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    application = FastAPI(title="Image Processing Lab API")
    application.add_middleware(UploadBodyLimit, max_bytes=settings.max_upload_bytes + 64 * 1024)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
        expose_headers=["X-Original-Width", "X-Original-Height", "X-Output-Width", "X-Output-Height"],
    )

    @application.get("/health")
    def health():
        return {"status": "ok"}

    @application.post("/inspect", response_model=ImageInfo,
                      summary="Read original dimensions and visible-channel auto-range")
    async def inspect(file: Annotated[UploadFile, File()]):
        data = await read_upload(file, settings)
        info = await run_in_threadpool(inspect_image, data, settings)
        return JSONResponse(info, headers={"Cache-Control": "no-store"})

    @application.get("/kernels", response_model=KernelDescription, summary="Inspect the actual spatial kernel coefficients",
                     description="Raw/scaled matrices divided by their divisors give the normalized kernels before convolution reverses both axes. No image is uploaded or processed.")
    def kernels(
        operation: SpatialOperation,
        kernel_size: Annotated[int, Query(ge=3, le=31)] = 3,
        amount: Annotated[float, Query(ge=0, le=2, allow_inf_nan=False)] = 1.0,
    ):
        try:
            return kernel_description(operation, kernel_size, amount)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc

    @application.post("/process", response_class=Response, responses={
        200: {"content": {"image/png": {}}, "description": "Full-resolution processed PNG"},
        400: {"description": "Empty or invalid image"},
        413: {"description": "Upload or pixel count too large"},
        415: {"description": "Unsupported format, mode, or animated image"},
        422: {"description": "Invalid operation, non-finite/out-of-range parameters, or invalid bounds"},
    }, description=(
        "All operations recompute from the uploaded original. "
        "Gamma uses the exponent directly, then RGB gains, then saturation. "
        "Contrast first clips 255*(p-a)/(b-a), then gamma, gains, saturation. "
        "Omit both contrast bounds for visible-channel auto-range; constant/transparent "
        "auto-ranges skip the base stretch. Explicit bounds require 0 <= a < b <= 255. "
        "Grayscale/inversion and geometry accept only neutral adjustments. "
        "Alpha is preserved. Float intermediates are rounded (ties to even) and clipped once at export."
        " Spatial operations use reflect padding. Blur/sharpen sizes are 3,5,7,9,11,21,31; "
        "emboss/Sobel sizes are 3,5,7,9,11. Box averaging uses equivalent prefix sums. "
        "Blur uses a unit-sum box; sharpen its equivalent unsharp kernel; emboss normalized "
        "directional grayscale plus 128; Sobel combines signed derivatives and max-normalizes "
        "the magnitude, optionally applying >= threshold to normalized float values."
        " Glitch uses integer shift/tear/noise/scanlines percentages 0..100 and an "
        "unsigned 32-bit seed (default 0): wrapped RGB shift, wrapped bands, shared "
        "RGB noise, odd-row darkening, then export. Alpha stays at source coordinates."
    ))
    async def process(
        file: Annotated[UploadFile, File(description="JPEG, PNG, or WebP image")],
        operation: Annotated[Operation, Form()],
        gamma: Annotated[float, Form(ge=0.1, le=3.0, allow_inf_nan=False, description="Direct exponent; below 1 brightens, above 1 darkens")] = 1.0,
        red_gain: Annotated[float, Form(ge=0, le=2, allow_inf_nan=False)] = 1.0,
        green_gain: Annotated[float, Form(ge=0, le=2, allow_inf_nan=False)] = 1.0,
        blue_gain: Annotated[float, Form(ge=0, le=2, allow_inf_nan=False)] = 1.0,
        saturation: Annotated[float, Form(ge=0, le=2, allow_inf_nan=False)] = 1.0,
        black_point: Annotated[float | None, Form(ge=0, le=255, allow_inf_nan=False)] = None,
        white_point: Annotated[float | None, Form(ge=0, le=255, allow_inf_nan=False)] = None,
        kernel_size: Annotated[int, Form(ge=3, le=31, description="Blur/sharpen: 3,5,7,9,11,21,31. Emboss/Sobel: 3,5,7,9,11.")] = 3,
        amount: Annotated[float, Form(ge=0, le=2, allow_inf_nan=False, description="Sharpening amount")] = 1.0,
        strength: Annotated[float, Form(ge=0, le=2, allow_inf_nan=False, description="Emboss strength")] = 1.0,
        reverse_relief: Annotated[bool, Form()] = False,
        binary_threshold: Annotated[bool, Form()] = False,
        threshold: Annotated[float, Form(ge=0, le=255, allow_inf_nan=False)] = 128.0,
        shift: Annotated[int, Form(ge=0, le=100, description="Glitch RGB shift intensity, integer percent")] = 0,
        tear: Annotated[int, Form(ge=0, le=100, description="Glitch band tearing intensity, integer percent")] = 0,
        noise: Annotated[int, Form(ge=0, le=100, description="Glitch monochrome noise intensity, integer percent")] = 0,
        scanlines: Annotated[int, Form(ge=0, le=100, description="Glitch odd-row darkening intensity, integer percent")] = 0,
        seed: Annotated[int, Form(ge=0, le=MAX_SEED, description="Glitch seed, unsigned 32-bit integer")] = DEFAULT_SEED,
    ):
        try:
            adjustments = dict(gamma=gamma, red_gain=red_gain, green_gain=green_gain,
                               blue_gain=blue_gain, saturation=saturation)
            try:
                validate_adjustments(**adjustments)
                validate_bounds(black_point, white_point)
                validate_size(kernel_size, operation)
            except ValueError as exc:
                raise HTTPException(422, str(exc)) from exc
            if operation not in {"gamma", "contrast"} and any(value != 1 for value in adjustments.values()):
                raise HTTPException(422, "Adjustments are supported only for gamma and contrast operations.")
            if operation != "contrast" and black_point is not None:
                raise HTTPException(422, "Input bounds are supported only for contrast stretching.")
            spatial = operation in {"blur", "sharpen", "emboss", "sobel"}
            if not spatial and kernel_size != 3:
                raise HTTPException(422, "Kernel size is supported only for spatial operations.")
            if operation != "sharpen" and amount != 1:
                raise HTTPException(422, "Sharpening amount applies only to sharpening.")
            if operation != "emboss" and (strength != 1 or reverse_relief):
                raise HTTPException(422, "Strength and reverse relief apply only to emboss.")
            if operation != "sobel" and (binary_threshold or threshold != 128):
                raise HTTPException(422, "Binary threshold controls apply only to Sobel.")
            if operation != "glitch" and (any((shift, tear, noise, scanlines)) or seed != DEFAULT_SEED):
                raise HTTPException(422, "Glitch intensities and seed apply only to glitch.")
            parameters = adjustments if operation in {"gamma", "contrast"} else {}
            if operation == "glitch":
                parameters = dict(shift=shift, tear=tear, noise=noise, scanlines=scanlines, seed=seed)
            if operation == "contrast":
                parameters.update(black_point=black_point, white_point=white_point)
            if spatial:
                parameters = {"kernel_size": kernel_size}
                if operation == "sharpen":
                    parameters.update(amount=amount)
                elif operation == "emboss":
                    parameters.update(strength=strength, reverse_relief=reverse_relief)
                elif operation == "sobel":
                    parameters.update(binary_threshold=binary_threshold, threshold=threshold)
            data = await read_upload(file, settings)
            return await run_in_threadpool(process_image, data, operation, settings, parameters)
        finally:
            await file.close()

    return application


app = create_app()
