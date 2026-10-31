import { API_URL } from '../config';
import { renderMath } from '../math-render';
import { mathNumber } from '../math-definitions';

interface KernelInfo { name: string; coefficients: number[][]; divisor: number; normalized_sum: number; }
interface KernelResponse { kernels: KernelInfo[]; kernel_size: number; }

// Small coefficient metadata only. This module never reads or filters image pixels.
export function createKernelDisplay() {
  const container = document.getElementById('kernel-matrices')!;
  const status = document.getElementById('kernel-status')!;
  const formatter = new Intl.NumberFormat('en', { maximumFractionDigits: 6, useGrouping: false });
  let generation = 0;
  let controller: AbortController | null = null;
  let timer = 0;
  let key = '';

  function update(operation: string, size: number, amount: number) {
    const next = `${operation}/${size}/${operation === 'sharpen' ? amount : 1}`;
    if (key === next) return;
    key = next;
    const token = ++generation;
    controller?.abort();
    window.clearTimeout(timer);
    container.replaceChildren();
    container.setAttribute('aria-busy', 'true');
    status.textContent = `Reading the selected ${size}×${size} coefficients…`;
    timer = window.setTimeout(async () => {
      const request = new AbortController();
      controller = request;
      const timeout = window.setTimeout(() => request.abort(), 15_000);
      try {
        const query = new URLSearchParams({ operation, kernel_size: String(size), amount: String(operation === 'sharpen' ? amount : 1) });
        const response = await fetch(`${API_URL}/kernels?${query}`, { signal: request.signal });
        if (!response.ok) throw new Error('Kernel metadata unavailable');
        const data: KernelResponse = await response.json();
        if (token !== generation) return;
        for (const kernel of data.kernels) {
          const figure = document.createElement('figure');
          figure.className = 'kernel-matrix';
          const compact = document.createElement('p');
          compact.className = 'control-hint';
          compact.textContent = `${kernel.name}: ${size}×${size}, ${size * size} coefficients; normalization factor 1/${formatter.format(kernel.divisor)}.`;
          figure.append(compact);
          const equation = document.createElement('div');
          equation.className = 'math-block matrix-equation';
          equation.tabIndex = 0; equation.setAttribute('role', 'region');
          equation.setAttribute('aria-label', `${kernel.name}, normalized kernel definition`);
          const symbol = ({ K_box: 'K_{\\mathrm{box}}', K_sharp: 'K_{\\mathrm{sharp}}', K_emboss: 'K_{\\mathrm{emboss}}', Kx: 'K_x', Ky: 'K_y' } as Record<string, string>)[kernel.name];
          if (size <= 5) {
            const entries = kernel.coefficients.map(row => row.map(value => mathNumber(value, 6)).join('&')).join('\\\\');
            renderMath(equation, `${symbol}=\\frac{1}{${mathNumber(kernel.divisor, 6)}}\\begin{bmatrix}${entries}\\end{bmatrix}`);
          } else {
            const definition = operation === 'blur' ? `\\frac{1}{${size * size}}\\mathbf{1}_{${size}\\times${size}}`
              : operation === 'sharpen' ? `(1+${mathNumber(amount)})\\delta-\\frac{${mathNumber(amount)}}{${size * size}}\\mathbf{1}_{${size}\\times${size}}`
              : `\\frac{1}{${mathNumber(kernel.divisor, 6)}}${symbol}^{\\mathrm{raw}}`;
            renderMath(equation, `${symbol}=${definition}`);
          }
          figure.append(equation);
          const full = document.createElement('details');
          full.className = 'full-matrix';
          const summary = document.createElement('summary');
          summary.textContent = `Full ${size}×${size} coefficient matrix`;
          full.append(summary);
          const scroll = document.createElement('div');
          scroll.className = 'matrix-scroll';
          scroll.tabIndex = 0;
          scroll.setAttribute('role', 'region');
          scroll.setAttribute('aria-label', `${kernel.name}, ${size} by ${size} coefficient matrix; scroll to inspect`);
          const table = document.createElement('table');
          table.setAttribute('translate', 'no');
          const caption = document.createElement('caption');
          caption.textContent = `${kernel.name} = displayed matrix ÷ ${formatter.format(kernel.divisor)}`;
          table.append(caption);
          const body = document.createElement('tbody');
          for (const row of kernel.coefficients) {
            const tr = document.createElement('tr');
            for (const value of row) {
              const td = document.createElement('td');
              td.textContent = formatter.format(value);
              tr.append(td);
            }
            body.append(tr);
          }
          table.append(body); scroll.append(table); full.append(scroll); figure.append(full);
          const note = document.createElement('p');
          note.className = 'control-hint';
          note.textContent = `Normalized coefficient sum: ${formatter.format(kernel.normalized_sum)}. Displayed decimals rounded to 6 places.`;
          figure.append(note); container.append(figure);
        }
        status.textContent = `${size}×${size} matrices from the Python generators. Divide by each factor before convolution.`;
      } catch {
        if (token !== generation) return;
        key = '';
        status.textContent = 'Kernel preview unavailable. Check the Python backend, then select a size or operation to retry.';
      } finally {
        window.clearTimeout(timeout);
        if (token === generation) { controller = null; container.setAttribute('aria-busy', 'false'); }
      }
    }, 100);
  }
  function dispose() {
    generation++;
    controller?.abort();
    window.clearTimeout(timer);
  }
  return { update, dispose };
}
