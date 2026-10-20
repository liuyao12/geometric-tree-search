(() => {
  const input = document.querySelector('#project-search');
  const cards = [...document.querySelectorAll('.project-card')];
  const sections = [...document.querySelectorAll('.project-section')];
  const count = document.querySelector('#project-count');
  const status = document.querySelector('#search-status');
  const empty = document.querySelector('.empty-state');
  const normalize = (value) => value.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const entries = cards.map((card) => ({ card, terms: normalize(`${card.dataset.search} ${card.closest("section").querySelector("h2").textContent}`) }));
  function filter() {
    const words = normalize(input.value).trim().split(/\s+/).filter(Boolean);
    let visible = 0;
    for (const { card, terms } of entries) {
      card.hidden = !words.every((word) => terms.includes(word));
      if (!card.hidden) visible++;
    }
    let visibleSections = 0;
    for (const section of sections) {
      const matches = [...section.querySelectorAll('.project-card')].filter((card) => !card.hidden).length;
      section.hidden = matches === 0;
      const badge = section.querySelector('.section-count');
      badge.textContent = String(matches).padStart(2, '0');
      badge.setAttribute('aria-label', `${matches} ${matches === 1 ? 'project' : 'projects'}`);
      if (matches) visibleSections++;
    }
    empty.hidden = visible !== 0;
    count.textContent = words.length ? `${visible} of ${cards.length} projects · ${visibleSections} ${visibleSections === 1 ? 'perspective' : 'perspectives'}` : `${cards.length} projects across three perspectives`;
    status.textContent = words.length ? `${visible} matching ${visible === 1 ? 'project' : 'projects'}.` : `All ${cards.length} projects shown.`;
  }
  input.addEventListener('input', filter);
  input.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') { input.value = ''; filter(); }
  });
  document.querySelector('#clear-search').addEventListener('click', () => {
    input.value = '';
    filter();
    input.focus();
  });
  // Category jumps always show their full category, even after a search.
  for (const link of document.querySelectorAll('.category-jump')) {
    link.addEventListener('click', () => { input.value = ''; filter(); });
  }
  document.querySelector('.search').hidden = false;
  filter();
})();
