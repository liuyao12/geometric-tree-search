(() => {
  const markdownPath = document.currentScript?.dataset?.markdown || 'docs/blog/tree-search-with-geometric-constraints.md';

  const stageRules = [
    { test: text => /^Tiles and tilings$/i.test(text), stage: 'tile' },
    { test: text => /^Markings and matching rules$/i.test(text), stage: 'markings' },
    { test: text => text.startsWith('A lattice tile') && text.includes('to tile'), stage: 'tiling' },
    { test: text => text.startsWith('The (naive) tiling algorithm'), stage: 'markedTiling' }
  ];

  const escapeHtml = value => value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');

  const normalizeHref = href => {
    if (/^(?:[a-z]+:|#|\/)/i.test(href)) return href;
    if (location.pathname.endsWith('/GCTS-I.html')) return href.replace(/^\.\.\/\.\.\//, './');
    return href;
  };

  const inlineMarkdown = source => {
    let text = escapeHtml(source);
    text = text.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (_, alt, src) => `<img src="${escapeHtml(src)}" alt="${escapeHtml(alt || 'Markdown image')}">`);
    text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, label, href) => `<a href="${escapeHtml(normalizeHref(href))}">${label}</a>`);
    text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/(^|[^*])\*([^*]+)\*/g, '$1<em>$2</em>');
    text = text.replace(/\$([^$\n]+)\$/g, (_, expr) => `\\(${expr.trim()}\\)`);
    return text;
  };

  const stageFor = text => stageRules.find(rule => rule.test(text))?.stage;

  const renderMarkdown = markdown => {
    const body = markdown.replace(/^<!--([\s\S]*?)-->\s*/, '').trim();
    const blocks = body.split(/\n{2,}/).map(block => block.trim()).filter(Boolean);
    const nodes = [];
    for (let i = 0; i < blocks.length; i += 1) {
      const block = blocks[i];
      if (/^#\s+/.test(block)) continue;
      if (/^##\s+/.test(block)) {
        const text = block.replace(/^##\s+/, '').trim();
        const h2 = document.createElement('h2');
        h2.innerHTML = inlineMarkdown(text);
        const stage = stageFor(text);
        if (stage) h2.dataset.demoStage = stage;
        if (/^Draft:/i.test(text)) h2.classList.add('article-wide');
        nodes.push(h2);
        continue;
      }
      if (/^\$\$[\s\S]*\$\$$/.test(block)) {
        const div = document.createElement('div');
        div.className = 'math-display';
        div.textContent = `\\[${block.replace(/^\$\$|\$\$$/g, '').trim()}\\]`;
        nodes.push(div);
        continue;
      }
      if (/^!\[[^\]]*\]\([^)]+\)(?:\n!\[[^\]]*\]\([^)]+\))*$/.test(block)) {
        const images = block.split('\n');
        const wrapper = document.createElement(images.length > 1 ? 'div' : 'figure');
        if (images.length > 1) wrapper.className = 'figure-grid';
        images.forEach(line => {
          const match = line.match(/^!\[([^\]]*)\]\(([^)]+)\)$/);
          const figure = document.createElement('figure');
          const img = document.createElement('img');
          img.src = match[2];
          img.alt = match[1] || 'Markdown image';
          figure.append(img);
          if (images.length > 1) wrapper.append(figure); else wrapper.append(img);
        });
        nodes.push(wrapper);
        continue;
      }
      const p = document.createElement('p');
      p.innerHTML = inlineMarkdown(block.replace(/\n/g, ' '));
      const text = p.textContent.trim();
      const stage = stageFor(text);
      if (stage) p.dataset.demoStage = stage;
      if (nodes.some(node => node.matches?.('h2.article-wide')) && /^One may|^In this view|^The practical hope/.test(text)) {
        p.classList.add('article-wide');
      }
      nodes.push(p);
    }
    return nodes;
  };

  const loadMarkdownArticle = async () => {
    const article = document.querySelector('.article-content');
    if (!article) return;
    try {
      const response = await fetch(markdownPath, { cache: 'no-cache' });
      if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
      const markdown = await response.text();
      const demo = article.querySelector('.floating-demo');
      const rendered = renderMarkdown(markdown);
      if (demo) {
        const tileStageIndex = rendered.findIndex(node => node.dataset?.demoStage === 'tile');
        rendered.splice(tileStageIndex >= 0 ? tileStageIndex : 0, 0, demo);
      }
      article.replaceChildren(...rendered);
      window.dispatchEvent(new CustomEvent('gcts:markdown-rendered'));
      if (window.MathJax?.typesetPromise) window.MathJax.typesetPromise([article]);
    } catch (error) {
      console.warn(`Could not load ${markdownPath}; using embedded article fallback.`, error);
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadMarkdownArticle, { once: true });
  } else {
    loadMarkdownArticle();
  }
})();
