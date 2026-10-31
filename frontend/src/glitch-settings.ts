// Only Surprise me changes the seed. Manual input never draws random values.
export const DEFAULT_GLITCH_SEED = 0;
export const glitchNames = ['shift', 'tear', 'noise', 'scanlines'] as const;
export type GlitchName = typeof glitchNames[number];

// Colour split, broken signal, soft interference, heavy glitch; no extra selector.
const profiles = [
  [[55, 90], [0, 12], [0, 8], [5, 25]],
  [[15, 45], [40, 75], [15, 35], [30, 65]],
  [[10, 30], [5, 25], [5, 15], [10, 30]],
  [[45, 85], [55, 90], [20, 45], [40, 75]],
] as const;

export function surpriseSettings(randomWord: () => number = () => crypto.getRandomValues(new Uint32Array(1))[0]!): { seed: number; values: Record<GlitchName, number> } {
  const unit = () => randomWord() / 0x1_0000_0000;
  const profile = profiles[Math.floor(unit() * profiles.length)]!;
  const values = Object.fromEntries(glitchNames.map((name, index) => {
    const [low, high] = profile[index]!;
    return [name, low + Math.floor(unit() * (high - low + 1))];
  })) as Record<GlitchName, number>;
  return { seed: randomWord(), values };
}
