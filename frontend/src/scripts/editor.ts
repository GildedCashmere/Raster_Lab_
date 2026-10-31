// Python produces every processed image; the browser displays response blobs.
import { API_URL, MAX_UPLOAD_BYTES, MAX_IMAGE_PIXELS, uploadLimitLabel, pixelLimitLabel } from '../config';
import { operations, tools, type Operation, type ToolId } from '../tools';
import { createKernelDisplay } from './kernel-display';
import { sizesFor } from '../kernel-sizes';
import { renderMath } from '../math-render';
import { formulaFor, mathNumber } from '../math-definitions';
import { DEFAULT_GLITCH_SEED, glitchNames, surpriseSettings } from '../glitch-settings';
const element = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const tool = element('editor').dataset.tool as ToolId;
const fileInput = element<HTMLInputElement>('file-input');
const dropZone = element('drop-zone');
const form = element<HTMLFormElement>('transform-form');
const apply = element<HTMLButtonElement>('apply');
const reset = element<HTMLButtonElement>('reset');
const download = element<HTMLButtonElement>('download');
const originalImage = element<HTMLImageElement>('original-image');
const outputImage = element<HTMLImageElement>('output-image');
const status = element('status');
let file: File | null = null;
let originalUrl: string | null = null;
let outputUrl: string | null = null;
let outputOperation = '';
let generation = 0;
let fileGeneration = 0;
let controller: AbortController | null = null;
let inspectController: AbortController | null = null;
let loading = false;
let inspecting = false;
let automatic = true;
let glitchSeed = DEFAULT_GLITCH_SEED;
interface ImageInfo { width: number; height: number; black_point: number | null; white_point: number | null; range_status: 'ready' | 'constant' | 'transparent'; }
let imageInfo: ImageInfo | null = null;
const number = new Intl.NumberFormat();
const dimensions = (w: number, h: number) => `${number.format(w)} × ${number.format(h)} px`;
const selected = (): Operation => (new FormData(form).get('operation') ?? tools[tool].defaultOperation) as Operation;
const control = (name: string) => form.elements.namedItem(name) as HTMLInputElement;
const numeric = (name: string) => Number(control(name).value);
const kernelSize = () => sizesFor(selected())[numeric('kernel_size')]!;
const adjustable = tool === 'gamma' || tool === 'contrast';
const spatial = tool === 'spatial' || tool === 'edges';
const kernelDisplay = spatial ? createKernelDisplay() : null;
const adjustmentNames = ['gamma', 'red_gain', 'green_gain', 'blue_gain', 'saturation'];

function message(text: string, state = 'idle') {
  element('status-text').textContent = text;
  status.dataset.state = state;
}
function syncControls() {
  apply.disabled = !file || loading || inspecting || !!form.querySelector('input[type=number]:invalid:not(:disabled)') || (tool === 'contrast' && !imageInfo);
  reset.disabled = !file || inspecting;
  download.disabled = !outputUrl || loading;
  if (tool === 'contrast') element<HTMLFieldSetElement>('contrast-bounds').disabled = !imageInfo || inspecting;
  element('apply-text').textContent = loading ? 'Processing…' : 'Apply transformation';
  element('loading-overlay').hidden = !loading;
  element('previews').setAttribute('aria-busy', String(loading || inspecting));
}
function cancelRequest() {
  generation++;
  controller?.abort();
  controller = null;
  loading = false;
}
function clearOutput() {
  outputImage.hidden = true;
  outputImage.removeAttribute('src');
  if (outputUrl) URL.revokeObjectURL(outputUrl);
  outputUrl = null;
  outputOperation = '';
  element('output-empty').hidden = false;
  element('output-dimensions').textContent = 'No operation applied';
  element('result-tag').textContent = file ? 'Ready to apply' : 'Awaiting image';
}
function boundConstraints() {
  const a = control('black_point');
  const b = control('white_point');
  // Native slider limits prevent crossing; guard programmatic changes as well.
  a.value = String(Math.max(0, Math.min(Number(a.value), Number(b.value) - 1, 254)));
  b.value = String(Math.min(255, Math.max(Number(b.value), Number(a.value) + 1, 1)));
  a.max = String(Number(b.value) - 1);
  b.min = String(Number(a.value) + 1);
}
function restoreAutoRange() {
  automatic = true;
  const a = control('black_point');
  const b = control('white_point');
  for (const name of ['black_point', 'white_point']) {
    element(`${name}-number`).removeAttribute('aria-invalid');
    element(`${name}-error`).hidden = true;
  }
  // Reset dynamic constraints before assigning the new automatic values.
  a.min = '0'; a.max = '254'; b.min = '1'; b.max = '255';
  a.value = String(imageInfo?.range_status === 'ready' ? imageInfo.black_point : 0);
  b.value = String(imageInfo?.range_status === 'ready' ? imageInfo.white_point : 255);
  boundConstraints();
}
function defaults() {
  // Range input defaultValue is the page's original value, never a processed result.
  if (tool === 'contrast') {
    control('black_point').max = '254'; control('white_point').min = '1';
  }
  form.reset();
  if (tool === 'glitch') glitchSeed = DEFAULT_GLITCH_SEED;
  for (const input of form.querySelectorAll<HTMLInputElement>('input[data-range]')) {
    input.removeAttribute('aria-invalid'); element(`${input.dataset.range}-error`).hidden = true;
  }
  if (tool === 'contrast') restoreAutoRange();
  updateFormula();
}
function rangeDescription(): string {
  if (!imageInfo) return 'Upload an image to read its visible RGB range.';
  if (!automatic) return `Manual input: ${numeric('black_point')}–${numeric('white_point')}. Output range: 0–255.`;
  if (imageInfo.range_status === 'constant') return `Automatic range: ${imageInfo.black_point}–${imageInfo.white_point} (constant image). The base stays unchanged. Sliders show a proposed manual range of 0–255; move either to use manual bounds.`;
  if (imageInfo.range_status === 'transparent') return 'No visible pixels: the base stays unchanged. Sliders show a proposed manual range of 0–255; move either to use manual bounds. Alpha stays unchanged.';
  return `Automatic input: ${imageInfo.black_point}–${imageInfo.white_point}. Output range: 0–255. Fully transparent pixels are ignored.`;
}
function updateFormula() {
  const name = selected();
  const operation = operations[name];
  element('formula-heading').textContent = operation.name;
  renderMath(element('formula-equation'), formulaFor(name, name === 'emboss' && control('reverse_relief').checked, name === 'sobel' && control('binary_threshold').checked));
  element('formula-description').textContent = operation.explanation;
  if (tool === 'glitch') {
    const r = numeric('shift') / 100;
    // Mirror Python round-to-nearest, ties-to-even for the nonnegative shift.
    const raw = 0.03 * originalImage.width * r;
    const floor = Math.floor(raw);
    const distance = raw - floor === 0.5 ? floor + floor % 2 : Math.round(raw);
    const d = file ? String(distance) : String.raw`\operatorname{round}(0.03Wr)`;
    const values = String.raw`\begin{aligned}(r,t,n,s)&=(${glitchNames.map(name => mathNumber(numeric(name) / 100)).join(',')})\\d&=${d},\quad A=${mathNumber(64 * numeric('noise') / 100)},\quad q_{\mathrm{odd}}=${mathNumber(1 - 0.85 * numeric('scanlines') / 100, 4)}\\\mathrm{seed}&=${glitchSeed}\end{aligned}`;
    renderMath(element('formula-values'), values);
    for (const name of glitchNames) control(name).setAttribute('aria-valuetext', `${numeric(name)} percent intensity`);
  }
  if (spatial) {
    const sizes = sizesFor(name);
    const slider = control('kernel_size');
    const stops = document.querySelector<HTMLElement>('.kernel-stops')!;
    if (slider.max !== String(sizes.length - 1)) {
      slider.max = String(sizes.length - 1);
      stops.replaceChildren(...sizes.map(size => {
        const span = document.createElement('span'); span.dataset.size = String(size); span.textContent = `${size}\u00d7${size}`; return span;
      }));
    }
    const size = kernelSize();
    element<HTMLOutputElement>('kernel_size-value').value = `${size}\u00d7${size}`;
    element('kernel-size-help').textContent = `${sizes.length} sizes, up to ${sizes.at(-1)}\u00d7${sizes.at(-1)}. The selected size changes the actual neighbourhood.`;
    slider.setAttribute('aria-valuetext', `${size} by ${size}`);
    for (const label of document.querySelectorAll<HTMLElement>('.kernel-stops [data-size]')) label.dataset.selected = String(Number(label.dataset.size) === size);
    if (tool === 'spatial') {
      for (const kind of ['sharpen', 'emboss']) {
        const group = element<HTMLFieldSetElement>(`${kind}-controls`);
        group.hidden = name !== kind; group.disabled = name !== kind;
      }
    }
    let values = `N=${size},\\quad K\\in\\mathbb{R}^{${size}\\times${size}}`;
    if (name === 'sharpen') values += `,\\quad a=${mathNumber(numeric('amount'))}`;
    if (name === 'emboss') values += `,\\quad t=${mathNumber(numeric('strength'))}`;
    if (name === 'sobel') {
      const binary = control('binary_threshold').checked;
      element('threshold-controls').hidden = !binary;
      control('threshold').disabled = !binary;
      values += binary ? `,\\quad T=${mathNumber(numeric('threshold'), 0)}` : ',\\quad \\text{continuous}';
    }
    renderMath(element('formula-values'), values);
    kernelDisplay?.update(name, size, name === 'sharpen' ? numeric('amount') : 1);
  }
  if (adjustable) {
    const gains = ['red_gain', 'green_gain', 'blue_gain'].map(name => mathNumber(numeric(name))).join(',');
    let values = `\\gamma&=${mathNumber(numeric('gamma'))},\\quad s=${mathNumber(numeric('saturation'))}\\\\(g_R,g_G,g_B)&=(${gains})`;
    if (tool === 'contrast') {
      const a = automatic && imageInfo ? imageInfo.black_point : numeric('black_point');
      const b = automatic && imageInfo ? imageInfo.white_point : numeric('white_point');
      const bypass = automatic && imageInfo && imageInfo.range_status !== 'ready';
      values = (bypass ? 'p_{\\mathrm{base}}&=p\\quad\\text{(automatic base unchanged)}\\\\' : `a&=${a},\\quad b=${b},\\quad [0,255]_{\\mathrm{out}}\\\\`) + values;
      element('range-note').textContent = rangeDescription();
    }
    renderMath(element('formula-values'), `\\begin{aligned}${values}\\end{aligned}`);
  }
  for (const input of form.querySelectorAll<HTMLInputElement>('input[type="range"]')) {
    const progress = 100 * (Number(input.value) - Number(input.min)) / (Number(input.max) - Number(input.min));
    input.style.setProperty('--fill', `${progress}%`);
    if (input.name === 'kernel_size') continue;
    element<HTMLOutputElement>(`${input.name}-value`).value = input.step === '1' ? input.value : Number(input.value).toFixed(2);
    const numberInput = element<HTMLInputElement>(`${input.name}-number`);
    numberInput.min = input.min; numberInput.max = input.max;
    // Fieldset disabled state is inherited naturally. Copy only an input's
    // own state, so contrast numbers become usable after range analysis.
    numberInput.disabled = input.disabled;
    if (numberInput.getAttribute('aria-invalid') !== 'true') numberInput.value = input.value;
  }
}
async function apiError(response: Response): Promise<string> {
  const body = await response.json().catch(() => null);
  if (typeof body?.detail === 'string') return body.detail;
  if (Array.isArray(body?.detail)) return body.detail.map((error: { loc?: string[]; msg?: string }) => `${error.loc?.at(-1) ?? 'Setting'}: ${error.msg ?? 'invalid value'}`).join(' ');
  return `Processing failed (${response.status}). Check the image and settings, then try again.`;
}
async function analyzeOriginal(candidate: File, token: number) {
  inspecting = true;
  const request = new AbortController();
  inspectController = request;
  syncControls();
  message('Reading the original image’s visible RGB range with Python…');
  const data = new FormData(); data.append('file', candidate);
  const timeout = window.setTimeout(() => request.abort(), 60_000);
  try {
    const response = await fetch(`${API_URL}/inspect`, { method: 'POST', body: data, signal: request.signal });
    if (!response.ok) throw new Error(await apiError(response));
    const info: ImageInfo = await response.json();
    if (token !== fileGeneration) return;
    imageInfo = info;
    element('original-dimensions').textContent = dimensions(info.width, info.height);
    restoreAutoRange(); updateFormula();
    message(info.range_status === 'ready' ? 'Automatic range ready. Adjust the settings, then Apply.' : 'Image ready. Its automatic range has no span, so the base stays unchanged until you choose manual bounds.', 'success');
  } catch (error) {
    if (token !== fileGeneration) return;
    const detail = request.signal.aborted ? 'Range analysis timed out.' : error instanceof TypeError ? 'Cannot reach the image API.' : error instanceof Error ? error.message : 'Range analysis failed.';
    message(`${detail} Check the backend and choose the image again to retry.`, 'error');
  } finally {
    window.clearTimeout(timeout);
    if (token === fileGeneration) { inspecting = false; inspectController = null; syncControls(); }
  }
}
async function loadFile(candidate?: File) {
  if (!candidate) return;
  cancelRequest();
  inspectController?.abort(); inspectController = null; inspecting = false;
  const token = ++fileGeneration;
  clearOutput();
  file = null; imageInfo = null;
  defaults();
  originalImage.hidden = true; originalImage.removeAttribute('src');
  if (originalUrl) URL.revokeObjectURL(originalUrl);
  originalUrl = null;
  element('original-empty').hidden = false;
  element('original-dimensions').textContent = 'No image loaded';
  element('original-format').textContent = 'Original file';
  element('file-name').textContent = 'No image selected'; element('file-name').title = '';
  element('result-tag').textContent = 'Awaiting image';
  syncControls();
  if (!/\.(jpe?g|png|webp)$/i.test(candidate.name) && !['image/jpeg', 'image/png', 'image/webp'].includes(candidate.type)) {
    message('Choose a JPEG, PNG, or WebP image.', 'error'); return;
  }
  if (candidate.size > MAX_UPLOAD_BYTES) {
    message(`This file exceeds ${uploadLimitLabel}. Choose a smaller image.`, 'error'); return;
  }
  const url = URL.createObjectURL(candidate);
  const preview = new Image(); preview.src = url;
  message('Opening your image…');
  try {
    await preview.decode();
    if (token !== fileGeneration) { URL.revokeObjectURL(url); return; }
    if (preview.naturalWidth * preview.naturalHeight > MAX_IMAGE_PIXELS) {
      URL.revokeObjectURL(url); message(`This image exceeds ${pixelLimitLabel}. Choose a smaller image.`, 'error'); return;
    }
  } catch {
    URL.revokeObjectURL(url);
    if (token === fileGeneration) message('This image could not be opened. Choose a valid JPEG, PNG, or WebP.', 'error');
    return;
  }
  file = candidate; originalUrl = url;
  originalImage.src = url; originalImage.width = preview.naturalWidth; originalImage.height = preview.naturalHeight;
  originalImage.hidden = false; element('original-empty').hidden = true;
  element('file-name').textContent = candidate.name; element('file-name').title = candidate.name;
  element('original-dimensions').textContent = dimensions(preview.naturalWidth, preview.naturalHeight);
  element('original-format').textContent = `${(candidate.size / 1024 / 1024).toFixed(2)} MiB`;
  element('result-tag').textContent = 'Ready to apply';
  if (tool === 'glitch') updateFormula();
  if (tool === 'contrast') void analyzeOriginal(candidate, token);
  else { message('Image ready. Choose your settings, then Apply.', 'success'); syncControls(); }
}
element('choose-file').addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', () => { void loadFile(fileInput.files?.[0]); fileInput.value = ''; });
let dragDepth = 0;
dropZone.addEventListener('dragenter', event => { event.preventDefault(); dragDepth++; dropZone.classList.add('dragging'); });
dropZone.addEventListener('dragover', event => { event.preventDefault(); });
dropZone.addEventListener('dragleave', () => { if (--dragDepth <= 0) { dragDepth = 0; dropZone.classList.remove('dragging'); } });
dropZone.addEventListener('drop', event => {
  event.preventDefault(); dragDepth = 0; dropZone.classList.remove('dragging');
  if (event.dataTransfer?.files.length !== 1) { message('Drop one image at a time.', 'error'); return; }
  void loadFile(event.dataTransfer.files[0]);
});
window.addEventListener('dragover', event => { if (event.dataTransfer?.types.includes('Files')) event.preventDefault(); });
window.addEventListener('drop', event => { if (event.dataTransfer?.types.includes('Files')) event.preventDefault(); });
function settingsChanged(target?: EventTarget | null) {
  if (target instanceof HTMLInputElement && ['black_point', 'white_point'].includes(target.name)) { automatic = false; boundConstraints(); }
  cancelRequest(); clearOutput(); updateFormula(); syncControls();
  if (!inspecting) message(`${operations[selected()].name}: settings ready. Apply to process the original.`);
}
// input updates formulas immediately; neither input nor change sends an API request.
form.addEventListener('input', event => {
  const input = event.target;
  if (input instanceof HTMLInputElement && input.dataset.range) {
    const valid = input.value !== '' && input.checkValidity();
    input.setAttribute('aria-invalid', String(!valid));
    const error = element(`${input.dataset.range}-error`);
    error.hidden = valid;
    error.textContent = `Enter ${input.min} to ${input.max}, in steps of ${input.step}.`;
    if (!valid) {
      cancelRequest(); clearOutput(); syncControls();
      message('Check the highlighted numerical value before applying.', 'error'); return;
    }
    const slider = control(input.dataset.range);
    slider.value = input.value; settingsChanged(slider); return;
  }
  if (input instanceof HTMLInputElement && input.type === 'range' && input.name !== 'kernel_size') {
    element(`${input.name}-number`).removeAttribute('aria-invalid'); element(`${input.name}-error`).hidden = true;
  }
  settingsChanged(input);
});
form.addEventListener('change', event => {
  if (!(event.target instanceof HTMLInputElement) || !['range', 'number'].includes(event.target.type)) settingsChanged(event.target);
});
if (tool === 'contrast') element('auto-range').addEventListener('click', () => { restoreAutoRange(); settingsChanged(); });
if (tool === 'glitch') element('surprise').addEventListener('click', () => {
  const surprise = surpriseSettings();
  glitchSeed = surprise.seed === glitchSeed ? (surprise.seed ^ 1) >>> 0 : surprise.seed;
  for (const name of glitchNames) {
    control(name).value = String(surprise.values[name]);
    element(`${name}-number`).removeAttribute('aria-invalid');
    element(`${name}-error`).hidden = true;
  }
  settingsChanged(); // Cancels older work and clears invalid numbers/results.
  if (file) form.requestSubmit();
  else message('New glitch settings are ready. Choose an image to try them; uploads restore page defaults.');
});
form.addEventListener('submit', async event => {
  event.preventDefault();
  if (!file || apply.disabled) return;
  cancelRequest(); clearOutput();
  const current = generation;
  const operation = selected(); const label = operations[operation].name;
  const requestController = new AbortController(); controller = requestController;
  loading = true; syncControls(); message('Processing your original image with the Python backend…');
  const data = new FormData(); data.append('file', file); data.append('operation', operation);
  if (tool === 'glitch') {
    for (const name of glitchNames) data.append(name, control(name).value);
    data.append('seed', String(glitchSeed));
  }
  if (adjustable) for (const name of adjustmentNames) data.append(name, control(name).value);
  if (spatial) {
    data.append('kernel_size', String(kernelSize()));
    if (operation === 'sharpen') data.append('amount', control('amount').value);
    if (operation === 'emboss') {
      data.append('strength', control('strength').value);
      data.append('reverse_relief', String(control('reverse_relief').checked));
    }
    if (operation === 'sobel') {
      data.append('binary_threshold', String(control('binary_threshold').checked));
      if (control('binary_threshold').checked) data.append('threshold', control('threshold').value);
    }
  }
  if (tool === 'contrast' && !automatic) { data.append('black_point', control('black_point').value); data.append('white_point', control('white_point').value); }
  const timeout = window.setTimeout(() => requestController.abort(), 60_000);
  let pendingUrl: string | null = null;
  try {
    const response = await fetch(`${API_URL}/process`, { method: 'POST', body: data, signal: requestController.signal });
    if (!response.ok) throw new Error(await apiError(response));
    if (!response.headers.get('content-type')?.includes('image/png')) throw new Error('The API did not return a PNG. Check the API URL configuration.');
    const blob = await response.blob();
    if (current !== generation) return;
    pendingUrl = URL.createObjectURL(blob);
    const preview = new Image(); preview.src = pendingUrl;
    await preview.decode();
    if (current !== generation) return;
    outputUrl = pendingUrl; pendingUrl = null; outputOperation = operation;
    outputImage.src = outputUrl; outputImage.width = preview.naturalWidth; outputImage.height = preview.naturalHeight;
    outputImage.alt = `Processed image: ${label.toLowerCase()}`; outputImage.hidden = false; element('output-empty').hidden = true;
    element('output-dimensions').textContent = dimensions(preview.naturalWidth, preview.naturalHeight);
    const sourceWidth = Number(response.headers.get('X-Original-Width')); const sourceHeight = Number(response.headers.get('X-Original-Height'));
    if (sourceWidth && sourceHeight) element('original-dimensions').textContent = dimensions(sourceWidth, sourceHeight);
    element('result-tag').textContent = label;
    message(`${label} applied. Your full-resolution PNG is ready to download.`, 'success');
  } catch (error) {
    if (current !== generation) return;
    message(requestController.signal.aborted ? 'The request timed out. Check the backend, then try again.' : error instanceof TypeError ? 'Cannot reach the image API. Start the Python backend and check the API URL and allowed origins.' : error instanceof Error ? error.message : 'Processing failed. Try uploading the image again.', 'error');
  } finally {
    window.clearTimeout(timeout);
    if (pendingUrl) URL.revokeObjectURL(pendingUrl);
    if (current === generation) { loading = false; controller = null; syncControls(); }
  }
});
reset.addEventListener('click', () => {
  cancelRequest(); defaults(); clearOutput();
  if (originalUrl) {
    outputImage.src = originalUrl; outputImage.width = originalImage.width; outputImage.height = originalImage.height;
    outputImage.alt = 'Original image restored after reset'; outputImage.hidden = false; element('output-empty').hidden = true;
    element('output-dimensions').textContent = element('original-dimensions').textContent; element('result-tag').textContent = 'Original restored';
  }
  syncControls(); message('Original restored. Default settings are ready; Apply to create a new result.');
});
download.addEventListener('click', () => {
  if (!outputUrl || !file || loading) return;
  const link = document.createElement('a'); link.href = outputUrl; link.download = `${file.name.replace(/\.[^.]+$/, '')}-${outputOperation}.png`;
  document.body.append(link); link.click(); link.remove();
});
window.addEventListener('pagehide', () => {
  cancelRequest(); fileGeneration++; inspectController?.abort();
  kernelDisplay?.dispose();
  if (originalUrl) URL.revokeObjectURL(originalUrl);
  if (outputUrl) URL.revokeObjectURL(outputUrl);
});
window.addEventListener('pageshow', event => { if (event.persisted) location.reload(); });
updateFormula();
