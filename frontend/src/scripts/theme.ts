const toggle = document.getElementById('theme-toggle') as HTMLButtonElement;
const system = matchMedia('(prefers-color-scheme: dark)');
let explicit: string | null = null;
try { explicit = localStorage.getItem('raster-theme'); } catch { /* Theme works without storage. */ }
if (explicit !== 'dark' && explicit !== 'light') explicit = null;

function applyTheme(theme: string) {
  document.documentElement.dataset.theme = theme;
  document.documentElement.style.colorScheme = theme;
  toggle.setAttribute('aria-pressed', String(theme === 'dark'));
  const meta = document.querySelector<HTMLMetaElement>('meta[name="theme-color"]');
  if (meta) meta.content = theme === 'dark' ? '#0b1016' : '#f6f3ec';
}
applyTheme(document.documentElement.dataset.theme ?? 'light');
toggle.addEventListener('click', () => {
  explicit = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  applyTheme(explicit);
  try { localStorage.setItem('raster-theme', explicit); } catch { /* Retain choice in this document. */ }
});
system.addEventListener('change', () => { if (!explicit) applyTheme(system.matches ? 'dark' : 'light'); });
window.addEventListener('storage', (event) => {
  if (event.key !== 'raster-theme' && event.key !== null) return;
  explicit = event.newValue === 'light' || event.newValue === 'dark' ? event.newValue : null;
  applyTheme(explicit ?? (system.matches ? 'dark' : 'light'));
});
