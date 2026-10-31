export type ToolId = 'geometry' | 'point' | 'gamma' | 'contrast' | 'spatial' | 'edges' | 'glitch';
export const tools = {
  geometry: { route: '/', label: 'Flip & rotate', title: 'A fresh perspective.', description: 'Flip, rotate, and get your image just right.', defaultOperation: 'horizontal_flip' },
  point: { route: '/point-operations', label: 'Point operations', title: 'Colour, pixel by pixel.', description: 'Explore grayscale and colour inversion, with the mathematics in view.', defaultOperation: 'grayscale' },
  gamma: { route: '/gamma-correction', label: 'Gamma correction', title: 'Find the right light.', description: 'Reshape intensity with a power law, then fine-tune colour.', defaultOperation: 'gamma' },
  contrast: { route: '/contrast-stretching', label: 'Contrast stretching', title: 'Make more of your range.', description: 'Map an input range to 0–255, with one shared range for all RGB channels.', defaultOperation: 'contrast' },
  spatial: { route: '/spatial-filtering', label: 'Spatial filtering', title: 'Work with the neighbourhood.', description: 'Blur, sharpen, and emboss with explainable convolution kernels.', defaultOperation: 'blur' },
  edges: { route: '/edge-detection', label: 'Edge detection', title: 'Find the boundaries.', description: 'Explore directional intensity changes with generalized Sobel kernels.', defaultOperation: 'sobel' },
  glitch: { route: '/glitch-effect', label: 'Glitch effect', title: 'Disrupt the signal.', description: 'Combine colour separation, displaced bands, static and scanlines in one repeatable still-image effect.', defaultOperation: 'glitch' },
} satisfies Record<ToolId, { route: string; label: string; title: string; description: string; defaultOperation: string }>;

export const operations = {
  glitch: { name: 'Glitch effect', description: 'Remap, add noise, modulate rows', icon: 'image', explanation: 'x/y index columns/rows; W is width. C is any RGB channel; green stays put in stage 1. δy shifts a band; η is shared RGB noise. r, t, n, s are intensities ÷ 100; d = round(0.03Wr), A = 64n. Alpha stays at its source coordinates.' },
  horizontal_flip: { name: 'Flip horizontal', description: 'Mirror left to right', icon: 'horizontal', explanation: 'Reverse the columns. Each output pixel takes the pixel at the mirrored horizontal coordinate.' },
  vertical_flip: { name: 'Flip vertical', description: 'Mirror top to bottom', icon: 'vertical', explanation: 'Reverse the rows. Each output pixel takes the pixel at the mirrored vertical coordinate.' },
  rotate_90: { name: 'Rotate 90°', description: 'Clockwise quarter turn', icon: 'rotate', explanation: 'Exchange the axes and reverse the source row coordinate. Output width and height swap.' },
  rotate_180: { name: 'Rotate 180°', description: 'Half turn', icon: 'rotate', explanation: 'Reverse both rows and columns. The image dimensions stay the same.' },
  rotate_270: { name: 'Rotate 270°', description: 'Clockwise three-quarter turn', icon: 'rotate', explanation: 'Exchange the axes and reverse the source column coordinate. Output width and height swap.' },
  grayscale: { name: 'Grayscale', description: 'Weighted RGB intensity', icon: 'image', explanation: 'R, G, B are the pixel’s colour values. Y is an luma approximation and not exactly physical luminance. The result was rounded and clipped keeping transparency (alpha) unchanged' },
  inversion: { name: 'Colour inversion', description: 'Reverse colour values', icon: 'image', explanation: 'Subtract each RGB channel from 255. Dark values become light; colours become their complements. Alpha stays unchanged.' },
  gamma: { name: 'Gamma correction', description: 'Adjust the power-law curve', icon: 'image', explanation: 'p is an original RGB channel (0–255). γ is the exponent directly: below 1 brightens, above 1 darkens, and 1 leaves base values unchanged.' },
  contrast: { name: 'Contrast stretching', description: 'Expand a shared input range', icon: 'image', explanation: 'p is an original RGB channel. a is the input black point; b is the white point. Use the same a and b for every channel, with 0 ≤ a < b ≤ 255.' },
  blur: { name: 'Blur', description: 'Average neighbouring pixels', icon: 'image', explanation: 'N is the selected neighbourhood width. All N² coefficients sum to 1. Convolve each RGB channel independently; larger neighbourhoods produce stronger smoothing. ∗ means true convolution.' },
  sharpen: { name: 'Sharpen', description: 'Unsharp-mask convolution', icon: 'image', explanation: 'a is the sharpening amount. δ has 1 at the centre and 0 elsewhere. The equivalent N×N kernel sums to 1 and enhances detail relative to the box-blurred image. At a = 0 it is exactly the identity.' },
  emboss: { name: 'Emboss', description: 'Directional grayscale relief', icon: 'image', explanation: 't is the emboss strength. Centred row/column coordinates i, j run from −(N−1)/2 to +(N−1)/2. The directional kernel sums to 0; divide by its absolute sum, never by its zero sum. Y approximates intensity/luma. Add 128 to show signed relief as grayscale; reverse relief negates E.' },
  sobel: { name: 'Sobel edges', description: 'Combine directional gradients', icon: 'image', explanation: 'Gx responds across columns, emphasizing vertical boundaries; Gy responds across rows, emphasizing horizontal boundaries. Magnitude combines both signed responses without clipping them. Max-based display normalization can make weak edges more visible. A negligible maximum gives black.' },
};
export type Operation = keyof typeof operations;
