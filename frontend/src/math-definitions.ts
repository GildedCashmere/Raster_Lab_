import type { Operation } from './tools';

// Application-owned templates only; never interpolate filenames or user prose.
const tex = String.raw;
export const intensity = tex`Y=0.299R+0.587G+0.114B`;
export const convolution = tex`(I\ast K)[y,x]=\sum_{i=-m}^{m}\sum_{j=-m}^{m}K[i,j]\,I_{\mathrm{reflect}}[y-i,x-j],\quad m=\frac{N-1}{2}`;
export const adjustments = tex`\begin{aligned}C_{\mathrm{gain}}&=g_C\,C\\Y&=0.299R_{\mathrm{gain}}+0.587G_{\mathrm{gain}}+0.114B_{\mathrm{gain}}\\C_{\mathrm{out}}&=Y+s(C_{\mathrm{gain}}-Y)\end{aligned}`;
export const optionalGamma = tex`p_\gamma=255\left(\frac{p_{\mathrm{base}}}{255}\right)^\gamma`;
export const sobelConstruction = tex`\begin{aligned}S_j&=\binom{N-1}{j},\quad Q_j=\binom{N-3}{j},\quad D=[-1,0,1]\ast Q\\K_{x,\mathrm{raw}}&=S\otimes D,\quad K_{y,\mathrm{raw}}=D\otimes S\\K_d&=\frac{K_{d,\mathrm{raw}}}{\sum_{i,j}|K_{d,\mathrm{raw}}[i,j]|},\quad d\in\{x,y\}\end{aligned}`;

const formulas: Record<Operation, string> = {
  glitch: tex`\begin{aligned}R_1[y,x]&=R[y,(x-d)\bmod W],\quad B_1[y,x]=B[y,(x+d)\bmod W]\\C_2[y,x]&=C_1[y,(x-\delta_y)\bmod W]\\C_3[y,x]&=C_2[y,x]+\eta[y,x],\quad\eta\sim\mathcal{U}(-A,A)\\C_4[y,x]&=q_y C_3[y,x],\quad q_y=1-0.85s\,(y\bmod2)\end{aligned}`,
  horizontal_flip: tex`O[y,x]=I[y,W-1-x]`,
  vertical_flip: tex`O[y,x]=I[H-1-y,x]`,
  rotate_90: tex`O[y,x]=I[H-1-x,y]`,
  rotate_180: tex`O[y,x]=I[H-1-y,W-1-x]`,
  rotate_270: tex`O[y,x]=I[x,W-1-y]`,
  grayscale: tex`\begin{aligned}Y&=0.299R+0.587G+0.114B\\R'&=G'=B'=Y\end{aligned}`,
  inversion: tex`C'=255-C,\qquad C\in\{R,G,B\}`,
  gamma: tex`p_{\mathrm{base}}=255\left(\frac{p}{255}\right)^\gamma`,
  contrast: tex`p_{\mathrm{base}}=\operatorname{clip}\!\left(255\frac{p-a}{b-a},\,0,\,255\right)`,
  blur: tex`K_{\mathrm{box}}[i,j]=\frac{1}{N^2},\qquad O=I\ast K_{\mathrm{box}}`,
  sharpen: tex`\begin{aligned}B&=I\ast K_{\mathrm{box}},\qquad O=I+a(I-B)\\K_{\mathrm{sharp}}&=(1+a)\delta-aK_{\mathrm{box}}\end{aligned}`,
  emboss: tex`\begin{aligned}K_{\mathrm{raw}}[i,j]&=i+j\\K_{\mathrm{emboss}}&=\frac{K_{\mathrm{raw}}}{\sum_{i,j}|K_{\mathrm{raw}}[i,j]|}\\E&=Y\ast K_{\mathrm{emboss}},\qquad O=128+tE\end{aligned}`,
  sobel: tex`\begin{aligned}G_x&=Y\ast K_x,\qquad G_y=Y\ast K_y\\M&=\sqrt{G_x^2+G_y^2}\\M_{\mathrm{display}}&=\begin{cases}\dfrac{255M}{\max M}&\max M>10^{-10}\\0&\text{otherwise}\end{cases}\end{aligned}`,
};
export function formulaFor(operation: Operation, reverse = false, binary = false): string {
  let formula = formulas[operation];
  if (operation === 'emboss' && reverse) formula = formula.replace('128+tE', '128-tE');
  if (operation === 'sobel' && binary) formula = formula.replace(tex`\end{aligned}`, tex`\\O&=\begin{cases}255&M_{\mathrm{display}}\ge T\\0&M_{\mathrm{display}}<T\end{cases}\end{aligned}`);
  return formula;
}
// Numerical substitutions cannot inject TeX. Non-finite values never reach templates.
export function mathNumber(value: number, digits = 2): string {
  if (!Number.isFinite(value)) return '0';
  return digits === 0 ? String(Math.round(value)) : value.toFixed(digits).replace(/\.?0+$/, '') || '0';
}
