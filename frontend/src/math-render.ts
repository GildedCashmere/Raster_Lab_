import katex from 'katex';
const options = { displayMode: true, output: 'htmlAndMathml' as const, trust: false, throwOnError: true, strict: 'error' as const, maxExpand: 1000 };
export function mathHtml(tex: string): string {
  try { return katex.renderToString(tex, options); }
  catch { return '<span class="math-fallback">Equation unavailable. The explanation below describes this operation.</span>'; }
}
/** Render only the changed equation, never auto-scan the document. */
export function renderMath(target: HTMLElement, tex: string) {
  if (target.dataset.tex === tex) return;
  target.innerHTML = mathHtml(tex);
  target.dataset.tex = tex;
}
