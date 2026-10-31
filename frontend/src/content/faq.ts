import { uploadLimitLabel, pixelLimitLabel } from '../config';
import { formulaFor } from '../math-definitions';

export const faq = [
  {
    question: 'What do the four glitch sliders change?',
    paragraphs: ['RGB Shift separates red and blue horizontally in opposite directions. Horizontal Tearing displaces selected RGB strips. Static Noise adds one random intensity sample to all colour channels at each pixel. Scanlines darken odd-indexed rows. All four range from 0 to 100% intensity, not literal displacement percentages. The fixed order is separation, tearing, noise, then scanlines. These simulate signal corruption, not actual file damage or codec datamoshing.'],
  },
  {
    question: 'Why does applying the glitch effect again give the same result?',
    paragraphs: ['Each request starts from the same original upload. The settings and a seed determine the result, including tearing and noise. Manual slider changes preserve that seed. Tearing and noise use separate random streams, so changing noise does not choose new tearing bands. Defaults and Reset use seed zero.'],
  },
  {
    question: 'What does Surprise me change?',
    paragraphs: ['It chooses four balanced slider values and a fresh unsigned 32-bit random seed. With an image loaded it processes the new combination once. Without an image it updates settings without uploading anything. Manual adjustments still wait for Apply. Choosing a new image restores the page defaults, just as on the other tools.'],
  },
  {
    question: 'Does a glitch change dimensions or transparency?',
    paragraphs: ['No. It preserves width, height and source alpha at its original coordinates. Only RGB values move or change, so colours underneath partial transparency can differ. Horizontal remapping wraps around the image edges. All four sliders at zero return the decoded original samples exactly, with grayscale expanded to RGB when needed; exported PNG bytes can still differ from the uploaded compressed file.'],
  },
  {
    question: 'What are geometric, point and spatial operations?',
    paragraphs: ['Geometric operations rearrange pixel coordinates, as in a flip or right-angle rotation. Point operations calculate new colour values using the channels at the same position, as in grayscale, inversion, gamma and contrast stretching. Spatial operations combine neighbouring pixels through a kernel; blur, sharpening, emboss and Sobel belong to this category.'],
  },
  {
    question: 'Which image formats and sizes can I upload?',
    paragraphs: [`Still JPEG, PNG and WebP inputs are supported, up to ${uploadLimitLabel} per file and ${pixelLimitLabel} of decoded pixels. Use 8-bit grayscale, RGB or RGBA. Palette transparency and grayscale-plus-alpha are handled during decoding/channel preparation. Animated files, CMYK, 16-bit PNG and unsupported colour modes are rejected. The API checks the decoded format, not just the filename.`],
  },
  {
    question: 'Why are there both file-size and megapixel limits?',
    paragraphs: ['The file-size limit bounds the uploaded compressed data. The pixel limit bounds the decoded array and the work needed for processing. A highly compressed image can have a small file size but a very large pixel array; floating-point filtering needs additional working memory. An image must satisfy both limits. Megapixels are width multiplied by height, divided by one million.'],
  },
  {
    question: 'Can I process a full-resolution 48 MP image?',
    paragraphs: [`No. A 48-million-pixel upload exceeds the current ${pixelLimitLabel} limit even if its file fits within ${uploadLimitLabel}. Raster Lab rejects oversized inputs rather than silently reducing them. Resize the image outside the tool before uploading. Larger-image support is a future feature, not a current export or processing mode.`],
  },
  {
    question: 'Will the output keep my image dimensions?',
    paragraphs: ['Point operations, spatial filters, flips and a 180° turn preserve decoded width and height. Clockwise 90° and 270° rotations exchange them because rows become columns: a 900 × 600 image becomes 600 × 900. EXIF orientation is normalized before processing, so dimensions refer to the correctly oriented input. Exports are not downscaled.'],
  },
  {
    question: 'What does transparency or alpha mean?',
    paragraphs: ['Alpha is a separate channel describing pixel opacity. In 8-bit images, zero means fully transparent, 255 means fully opaque, and intermediate values mean partial opacity. The checkerboard in the preview helps reveal transparent areas.', 'Geometry moves alpha with each pixel. Colour and spatial calculations copy source alpha unchanged. Spatial filters process straight RGB, including hidden colours under transparent pixels, so those colours can influence neighbouring results; alpha itself is not blurred. JPEG has no alpha channel.'],
  },
  {
    question: 'Does Apply accumulate edits?',
    paragraphs: ['No. Each Apply sends the original uploaded image and current settings to Python. A new result replaces the previous one; it is never computed from a rounded preview. Reset discards the result and restores defaults, including the image-derived contrast range. Choosing a new image clears the previous result. Navigating to another tool starts a fresh workspace.'],
  },
  {
    question: 'Which gamma values brighten or darken the image?',
    paragraphs: ['Raster Lab uses gamma directly as the exponent. Values below one brighten intermediate base values; values above one darken them; one is neutral. Gamma ranges from 0.1 to 3.0 and defaults to 1. Black and white remain fixed in the base power law for positive gamma. The later RGB gains and saturation controls can change values further and can cause final clipping.'],
    equation: formulaFor('gamma'),
  },
  {
    question: 'Why does automatic contrast stretching sometimes look unchanged?',
    paragraphs: ['Auto-range takes the minimum and maximum across visible RGB channel values, ignoring fully transparent pixels. If those values already span 0–255, the base mapping is unchanged. A few endpoint values can therefore make an otherwise low-contrast image use the full automatic range.', 'For equal automatic bounds or no visible pixels, only the base stretch is skipped; optional adjustments still work. Manual bounds can narrow the interval, but values outside it are clipped.'],
  },
  {
    question: 'Why can a small blur kernel look subtle?',
    paragraphs: ['A 3 × 3 box averages only nine nearby samples. On a large image that covers a small region, so broad structures barely change. Blur supports 3 × 3, 5 × 5, 7 × 7, 9 × 9, 11 × 11, 21 × 21 and 31 × 31. Larger neighbourhoods average over more detail; they do not change export dimensions.'],
  },
  {
    question: 'How does sharpening differ from edge detection?',
    paragraphs: ['Sharpening adds a scaled original-minus-blur difference back to the colour image. It enhances detail while retaining the image’s overall appearance; amount zero is unchanged. Sobel edge detection instead measures directional intensity changes and displays their combined magnitude as a grayscale boundary map. Its brightness is normalized for display, so it is not a direct measure of absolute edge strength across images.'],
  },
  {
    question: 'What does emboss do?',
    paragraphs: ['Emboss converts RGB to weighted grayscale, applies a zero-sum directional kernel and adds a middle-gray offset of 128. Positive and negative responses become opposing light and dark relief. Strength scales the response and Reverse relief changes its sign. A constant input gives middle gray. Emboss supports 3 × 3 through 11 × 11 in five discrete sizes, with source alpha unchanged.'],
  },
  {
    question: 'What changes when I enable Sobel binary thresholding?',
    paragraphs: ['The default Sobel image shows continuous grayscale edge magnitude. Binary thresholding compares the normalized floating-point display magnitude with T: values greater than or equal to T become white and the rest black. The threshold ranges from 0 to 255, default 128. It is applied before export rounding. At zero, every colour pixel becomes white, even on a flat image; alpha remains unchanged. Sobel keeps the five 3 × 3 to 11 × 11 kernel choices.'],
  },
  {
    question: 'Which format is downloaded?',
    paragraphs: ['Download PNG saves the actual processed PNG returned by Python, at the output’s full dimensions. PNG retains transparency when the source has alpha. The image you download comes from the same response blob as the processed preview. Output files do not copy EXIF, ICC profiles, DPI or other ancillary metadata; colour-managed rendering can therefore differ from a profiled original. A PNG download may be larger in bytes than its source file.'],
  },
  {
    question: 'Where does processing happen, and how are uploads handled?',
    paragraphs: ['The browser displays the original locally. Apply uploads that original to the FastAPI backend, where Pillow decodes the file and normalizes EXIF orientation, NumPy performs the calculation, and Pillow encodes the PNG. The contrast tool also uploads the original for range analysis when you upload it.', 'The application has no permanent image gallery or upload-retention feature. Multipart parsing may use temporary storage; upload handles are closed after requests. The editor does not save images in localStorage.'],
  },
];
