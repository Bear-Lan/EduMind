import { marked } from 'marked';
import markedKatex from 'marked-katex-extension';

marked.use(markedKatex({
  throwOnError: false,
  nonStandard: true,
  strict: 'ignore',
  trust: false,
}));

export function renderMarkdown(text) {
  if (!text) return '';

  const normalized = text.replace(
    /\n\s*[-*_]{3,}\s*\n/g,
    '\n\n---\n\n',
  );

  return marked.parse(normalized);
}
