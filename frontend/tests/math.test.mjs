import { test } from 'node:test';
import assert from 'node:assert/strict';
import { formulaFor, mathNumber, adjustments, convolution, intensity, optionalGamma, sobelConstruction } from '../src/math-definitions.ts';
import { mathHtml } from '../src/math-render.ts';
import { surpriseSettings, DEFAULT_GLITCH_SEED } from '../src/glitch-settings.ts';
import { education } from '../src/content/education.ts';

for (const operation of ['horizontal_flip', 'vertical_flip', 'rotate_90', 'rotate_180', 'rotate_270', 'grayscale', 'inversion', 'gamma', 'contrast', 'blur', 'sharpen', 'emboss', 'sobel', 'glitch']) {
  test(`${operation}: static and dynamic templates parse into accessible mathematics`, () => {
    for (const tex of [formulaFor(operation), formulaFor(operation, true, true)]) {
      const html = mathHtml(tex);
      assert.ok(html.includes('katex-html'));
      assert.ok(html.includes('<math xmlns="http://www.w3.org/1998/Math/MathML"'));
      assert.ok(!html.includes('math-fallback'));
    }
  });
}

test('Glitch educational equations render using HTML and MathML', () => {
  for (const topic of education.glitch.topics) for (const block of topic.blocks) if (block.kind === 'equation') {
    assert.ok(mathHtml(block.tex).includes('katex-mathml'));
    assert.ok(!mathHtml(block.tex).includes('math-fallback'));
  }
});

test('Surprise ranges are bounded and each curated profile is reachable', () => {
  assert.equal(DEFAULT_GLITCH_SEED, 0);
  const expected = [[55, 0, 0, 5], [15, 40, 15, 30], [10, 5, 5, 10], [45, 55, 20, 40]];
  for (let profile = 0; profile < 4; profile++) {
    const words = [profile * 0x4000_0000, 0, 0, 0, 0, 42];
    const settings = surpriseSettings(() => words.shift());
    assert.equal(settings.seed, 42);
    assert.deepEqual(Object.values(settings.values), expected[profile]);
  }
  const maximum = surpriseSettings(() => 0xffff_ffff);
  assert.equal(maximum.seed, 0xffff_ffff);
  assert.deepEqual(Object.values(maximum.values), [85, 90, 45, 75]);
});
test('Explanatory equations render without raw-source fallback', () => {
  for (const tex of [adjustments, convolution, intensity, optionalGamma, sobelConstruction]) assert.ok(!mathHtml(tex).includes('math-fallback'));
});
test('Our gamma is the direct exponent, including the post-stretch gamma', () => {
  for (const tex of [formulaFor('gamma'), optionalGamma]) {
    assert.ok(tex.includes('^\\gamma'));
    assert.ok(!tex.includes('1/'));
  }
});
test('Numeric substitutions retain zeros and reject non-finite values', () => {
  for (const value of [0, 10, 100, 255, .1, .5, 1.2]) assert.equal(Number(mathNumber(value)), value);
  assert.equal(mathNumber(100, 0), '100');
  for (const value of [NaN, Infinity, -Infinity]) assert.equal(mathNumber(value), '0');
});
test('Malformed mathematics fails gracefully; TeX cannot create trusted links', () => {
  assert.ok(mathHtml('\\notAnApplicationCommand').includes('math-fallback'));
  assert.ok(!mathHtml('\\href{https://example.com}{link}').includes('<a '));
});
