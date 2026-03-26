const DATA_URL = "/data/dashboard.json";
const ROUTE_THEME_REFERENCE = {
  family: "growth",
  growth: "family",
  fantasy: "adventure",
  adventure: "fantasy",
  animals: "moral_emotion",
  moral_emotion: "family",
};
const SERIES_COLORS = ["#0f3d43", "#b16f3e", "#73876f", "#c89c43", "#734b38"];

document.addEventListener("DOMContentLoaded", async () => {
  const page = document.body.dataset.page || "home";
  const root = document.getElementById("site-root");
  if (!root) return;

  try {
    const response = await fetch(DATA_URL);
    if (!response.ok) throw new Error(`Failed to fetch dashboard data: ${response.status}`);
    const data = await response.json();
    renderShell(root, page, data);
  } catch (error) {
    console.error(error);
    root.innerHTML = `
      <main class="main-pane">
        <section class="hero-panel reveal">
          <p class="eyebrow">Dashboard unavailable</p>
          <h1 class="display-title">The app data bundle is missing.</h1>
          <p class="lead">Rebuild the project assets with <code class="mono">make python-assets</code> or <code class="mono">python -m childlit_toolkit modern</code>, then redeploy.</p>
        </section>
      </main>
    `;
  }
});

function renderShell(root, page, data) {
  const pageMarkup = renderPage(page, data);
  root.innerHTML = `
    <div class="site-shell">
      ${renderSidebar(page, data)}
      <main class="main-pane">
        <header class="mobile-header reveal">
          <div>
            <div class="brand-kicker">LitScope</div>
            <div class="mobile-brand">Children's Literature Discovery</div>
          </div>
          <a class="ghost-cta" href="/explorer">Open Explorer</a>
        </header>
        <div class="page">${pageMarkup}</div>
        <footer class="footer">
          Built from the Aarhus 2016 project and rebuilt as a public discovery surface. Use <a class="inline-link" href="/report">Research Report</a> for method detail and <a class="inline-link" href="https://github.com/bozliu/aarhus-childrens-literature-toolkit">GitHub</a> for the full repo.
        </footer>
      </main>
    </div>
  `;

  if (page === "explorer") attachExplorer(data);
  if (page === "themes") attachThemes(data);
  if (page === "sentiment") attachSentiment(data);
  animateSelection();
}

function renderSidebar(page, data) {
  return `
    <aside class="sidebar">
      <div class="brand-lockup">
        <div class="brand-mark">LitScope</div>
        <div class="brand-kicker">Children's Literature Discovery</div>
        <h1 class="brand-title">A public-facing corpus product for Libraries & EdTech.</h1>
        <p class="brand-copy">Compare books, trace themes, inspect sentiment arcs, and audit the canon without pretending the corpus predicts plot or market outcomes.</p>
      </div>
      <nav class="sidebar-nav">
        ${data.navigation
          .map(
            (item) => `
            <a class="nav-link ${isActiveRoute(page, item.href) ? "active" : ""}" href="${item.href}">
              <span class="nav-label">${escapeHtml(item.label)}</span>
              <span class="nav-description">${escapeHtml(item.description)}</span>
            </a>
          `
          )
          .join("")}
      </nav>
      <div class="sidebar-actions">
        <a class="cta" href="/dashboard">Open overview</a>
        <a class="ghost-cta" href="/explorer">Search titles</a>
        <div class="sidebar-note">
          <strong>${formatNumber(data.summary.nBooks)} books</strong>, ${formatNumber(data.summary.totalWords)} words, and a stable 20-book legacy benchmark remain visible throughout the app.
        </div>
      </div>
    </aside>
  `;
}

function renderPage(page, data) {
  switch (page) {
    case "dashboard":
      return renderDashboardPage(data);
    case "explorer":
      return renderExplorerPage(data);
    case "themes":
      return renderThemesPage(data);
    case "sentiment":
      return renderSentimentPage(data);
    case "corpus":
      return renderCorpusPage(data);
    case "home":
    default:
      return renderHomePage(data);
  }
}

function renderHomePage(data) {
  const featuredBooks = data.books.slice(0, 4);
  return `
    <section class="hero-panel reveal" style="--delay:0">
      <div class="hero-grid">
        <div class="stack">
          <p class="eyebrow">Dashboard-first public release</p>
          <h1 class="display-title">Turn children’s literature into a discovery surface, not just a pile of texts.</h1>
          <p class="lead">This site turns the rebuilt Aarhus corpus into a real comparison and curation interface: title lookup, similar books, theme-led reading lists, sentiment pacing, and collection audit in one place.</p>
          <div class="hero-actions">
            <a class="cta" href="/dashboard">Open the dashboard</a>
            <a class="ghost-cta" href="/explorer">Search titles</a>
            <a class="ghost-cta" href="/report">Methodology report</a>
          </div>
          <div class="pill-row">
            <span class="tag">Not a story predictor</span>
            <span class="tag subtle">Built on real repo data</span>
            <span class="tag subtle">Designed for Libraries & EdTech</span>
          </div>
        </div>
        <div class="stack">
          <div class="floating-card reveal" style="--delay:1">
            <p class="metric-label">Collection snapshot</p>
            <div class="metric-grid">
              ${metricCard("Books", formatNumber(data.summary.nBooks), "Public-domain titles in the current live catalog.")}
              ${metricCard("Words", formatCompactNumber(data.summary.totalWords), "Shared across the same R and Python outputs. Exact totals stay visible deeper in the dashboard.")}
              ${metricCard("Legacy core", formatNumber(data.summary.legacyBooks), "Canonical 2016 benchmark titles kept intact.")}
              ${metricCard("Year span", `${data.summary.minYear}-${data.summary.maxYear}`, "Makes historical clustering visible rather than hidden.")}
            </div>
          </div>
          <div class="panel reveal" style="--delay:2">
            <h2 class="mini-title">What this helps you decide</h2>
            <div class="signal-list">
              ${data.insights
                .map(
                  (item) => `
                    <div class="signal-item">
                      <strong>${escapeHtml(item.title)}</strong>
                      <span>${escapeHtml(item.detail)}</span>
                    </div>
                  `
                )
                .join("")}
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="panel reveal" style="--delay:1">
      <div class="page-header">
        <div class="page-header-copy">
          <p class="eyebrow">Quick start</p>
          <h2 class="section-title">Choose the workflow that matches the decision you need to make.</h2>
          <p class="section-copy">This mirrors the public product surface: start from a known title, a theme, a pacing question, or the collection itself.</p>
        </div>
      </div>
      <div class="feature-grid">
        <article class="signal-item">
          <strong>Find Similar Books</strong>
          <span>Start from one title and move through explainable semantic neighbors for recommendation, shelf extension, and discovery.</span>
          <a class="inline-link" href="/explorer">Open Book Explorer</a>
        </article>
        <article class="signal-item">
          <strong>Explore Themes</strong>
          <span>Build friendship, family, growth, fantasy, or adventure reading lists using transparent theme profiles instead of weak tags.</span>
          <a class="inline-link" href="/themes">Open Theme Analysis</a>
        </article>
        <article class="signal-item">
          <strong>Analyze Sentiment</strong>
          <span>Compare calmer and more turbulent narrative pacing to support classroom sequencing and reading-path design.</span>
          <a class="inline-link" href="/sentiment">Open Sentiment Arcs</a>
        </article>
        <article class="signal-item">
          <strong>Audit the Corpus</strong>
          <span>Check provenance, authorship balance, and historical clustering before you make a public-facing catalog claim.</span>
          <a class="inline-link" href="/corpus">Open Corpus Insights</a>
        </article>
      </div>
    </section>

    <section class="two-column">
      <article class="panel reveal" style="--delay:2">
        <div class="page-header">
          <div class="page-header-copy">
            <p class="eyebrow">Current capability</p>
            <h2 class="section-title">What the product does today</h2>
          </div>
        </div>
        <div class="signal-list">
          <div class="signal-item"><strong>Discovery and comparison</strong><span>Search titles, inspect neighbors, and compare books through theme signals and pacing.</span></div>
          <div class="signal-item"><strong>Character-centered reading</strong><span>Use recurring entity surfaces to find books that are especially strong for classroom discussion or character-led recommendation.</span></div>
          <div class="signal-item"><strong>Collection review</strong><span>Audit provenance, historical concentration, and metadata balance before turning the corpus into a public-facing recommendation layer.</span></div>
        </div>
      </article>
      <article class="panel reveal" style="--delay:3">
        <div class="page-header">
          <div class="page-header-copy">
            <p class="eyebrow">Capability boundary</p>
            <h2 class="section-title">What it does not claim</h2>
          </div>
        </div>
        <div class="signal-list">
          <div class="signal-item"><strong>Not a plot forecaster</strong><span>The current system does not predict next-chapter events, endings, or story outcomes.</span></div>
          <div class="signal-item"><strong>Not a sales or quality score</strong><span>It does not infer literary quality, market success, or validated pedagogy scores.</span></div>
          <div class="signal-item"><strong>Not a complete map of the field</strong><span>The live corpus is historically grounded and intentionally auditable, which means it is also canon-aware and incomplete by design.</span></div>
        </div>
      </article>
    </section>

    <section class="panel reveal" style="--delay:4">
      <div class="page-header">
        <div class="page-header-copy">
          <p class="eyebrow">Use cases</p>
          <h2 class="section-title">Who this dashboard is most useful for right now.</h2>
          <p class="section-copy">The current MVP is strongest when people need explainable discovery, comparison, and curation signals rather than opaque recommendation scores.</p>
        </div>
      </div>
      <div class="feature-grid">
        <article class="signal-item">
          <strong>For Libraries</strong>
          <span>Build themed reading lists, identify adjacent titles, and make canon bias visible before turning the corpus into a recommendation layer.</span>
        </article>
        <article class="signal-item">
          <strong>For Educators</strong>
          <span>Choose books by theme mix, narrative pacing, and character density to support classroom comparison and discussion design.</span>
        </article>
        <article class="signal-item">
          <strong>For Researchers</strong>
          <span>Use the corpus as a transparent, auditable benchmark for studying clustering, theme distribution, and historical representation.</span>
        </article>
      </div>
    </section>

    <section class="panel reveal" style="--delay:5">
      <div class="page-header">
        <div class="page-header-copy">
          <p class="eyebrow">Featured titles</p>
          <h2 class="section-title">A few books to start with</h2>
          <p class="section-copy">These are rendered from the real corpus manifest, not from placeholder commercial catalog data.</p>
        </div>
        <a class="ghost-cta" href="/explorer">Open full catalog</a>
      </div>
      <div class="feature-grid">
        ${featuredBooks.map((book, index) => renderFeaturedBook(book, index)).join("")}
      </div>
    </section>
  `;
}

function renderDashboardPage(data) {
  const recommendationCards = data.corpus.recommendations
    .map(
      (item) => `
      <div class="recommendation-item">
        <strong>${escapeHtml(item.title)}</strong>
        <span>${escapeHtml(item.detail)}</span>
      </div>
    `
    )
    .join("");
  const topNeighbors = data.books
    .map((book) => ({
      title: book.title,
      neighbor: book.similar[0]?.title || "n/a",
      score: book.similar[0]?.score || 0,
    }))
    .filter((item) => item.neighbor !== "n/a")
    .sort((a, b) => b.score - a.score)
    .slice(0, 6);

  return `
    <section class="page-header reveal">
      <div class="page-header-copy">
        <p class="eyebrow">Overview</p>
        <h1 class="section-title">The dashboard turns the corpus into decisions.</h1>
        <p class="section-copy">Use this route when you need the big picture first: catalog size, collection shape, quick entrypoints, and the strongest signals that deserve deeper inspection.</p>
      </div>
      <div class="tag-row">
        <span class="tag">Discovery dashboard</span>
        <span class="tag subtle">Recommendation is one layer</span>
      </div>
    </section>
    <section class="metric-grid">
      ${metricCard("Titles", formatNumber(data.summary.nBooks), "Current live books available to compare.")}
      ${metricCard("Total words", formatNumber(data.summary.totalWords), "Shared across manifests, charts, and routes.")}
      ${metricCard("Legacy anchor", formatNumber(data.summary.legacyBooks), "Trusted 2016 benchmark titles kept intact.")}
      ${metricCard("Coverage", `${data.summary.minYear}-${data.summary.maxYear}`, "Historical span visible in the corpus audit.")}
    </section>
    <section class="surface-grid">
      <article class="panel reveal" style="--delay:1">
        <p class="eyebrow">Quick start</p>
        <h2 class="section-title">Where to go next</h2>
        <div class="signal-list">
          <div class="signal-item"><strong>Need a related-title answer?</strong><span>Jump into <a class="inline-link" href="/explorer">Book Explorer</a> and start from a known title.</span></div>
          <div class="signal-item"><strong>Need a themed list?</strong><span>Use <a class="inline-link" href="/themes">Theme Analysis</a> to find strong books for family, growth, fantasy, adventure, animals, or moral-emotion shelves.</span></div>
          <div class="signal-item"><strong>Need pacing comparison?</strong><span>Use <a class="inline-link" href="/sentiment">Sentiment Arcs</a> to compare calmer and more turbulent narrative experiences.</span></div>
          <div class="signal-item"><strong>Need a collection audit?</strong><span>Open <a class="inline-link" href="/corpus">Corpus Insights</a> before making broad claims from the catalog.</span></div>
        </div>
      </article>
      <article class="panel reveal" style="--delay:2">
        <p class="eyebrow">Collection recommendations</p>
        <h2 class="section-title">What the audit is already telling us</h2>
        <div class="recommendation-list">${recommendationCards}</div>
      </article>
    </section>
    <section class="two-column">
      <article class="panel reveal" style="--delay:2">
        <p class="eyebrow">Semantic neighborhood</p>
        <h2 class="section-title">Which books sit near each other?</h2>
        <div class="chart-shell">
          ${renderScatterChart(data.books, "projection.x", "projection.y", {
            xLabel: "Similarity axis x",
            yLabel: "Similarity axis y",
            sizeLabel: "wordCount",
          })}
          <div class="chart-caption">Signal: proximity in the current retrieval layer. Decision: which related titles to surface next. Limit: this is corpus-level similarity, not personalized recommendation.</div>
        </div>
      </article>
      <article class="panel reveal" style="--delay:3">
        <p class="eyebrow">Strongest top-1 neighbors</p>
        <h2 class="section-title">Interpretable adjacency examples</h2>
        <div class="table-shell">
          <table>
            <thead><tr><th>Title</th><th>Closest current neighbor</th><th>Score</th></tr></thead>
            <tbody>
              ${topNeighbors
                .map(
                  (item) => `
                  <tr>
                    <td><a class="inline-link" href="/explorer?book=${slugify(item.title)}">${escapeHtml(item.title)}</a></td>
                    <td>${escapeHtml(item.neighbor)}</td>
                    <td>${formatFloat(item.score, 3)}</td>
                  </tr>
                `
                )
                .join("")}
            </tbody>
          </table>
        </div>
      </article>
    </section>
  `;
}

function renderExplorerPage(data) {
  const initialBook = findBookFromQuery(data.books) || data.books[0];
  return `
    <section class="page-header reveal">
      <div class="page-header-copy">
        <p class="eyebrow">Book Explorer</p>
        <h1 class="section-title">Search the live corpus and inspect one title deeply.</h1>
        <p class="section-copy">This route is designed for librarians, reading platforms, and curriculum teams who need a decision-ready answer from one known title.</p>
      </div>
      <span class="tag">Real manifest data only</span>
    </section>
    <section class="surface-grid" id="explorer-root" data-default-book="${initialBook.id}">
      <article class="panel reveal" style="--delay:1">
        <div class="search-shell">
          <input class="search-input" id="explorer-search" type="search" placeholder="Search by title or author" />
          <div class="signal-item">
            <strong>What happens here</strong>
            <span>Search a title, inspect its strongest theme signals, see its sentiment profile, and use the neighbor list as an explainable recommendation surface.</span>
          </div>
          <div class="book-list" id="explorer-list"></div>
        </div>
      </article>
      <article class="panel reveal" style="--delay:2">
        <div id="explorer-detail"></div>
      </article>
    </section>
  `;
}

function renderThemesPage(data) {
  return `
    <section class="page-header reveal">
      <div class="page-header-copy">
        <p class="eyebrow">Theme Analysis</p>
        <h1 class="section-title">Build lists around themes instead of weak catalog labels.</h1>
        <p class="section-copy">Theme signals stay close to the current configured seeds, so this page is best used for transparent list building and comparison rather than for claims about universal literary ontology.</p>
      </div>
      <span class="tag">Seed-guided and auditable</span>
    </section>
    <section class="panel reveal" style="--delay:1">
      <div class="theme-tabs" id="theme-tabs"></div>
    </section>
    <section class="two-column" id="themes-root"></section>
  `;
}

function renderSentimentPage(data) {
  const curated = pickSentimentDefaults(data.books).map((book) => book.id);
  return `
    <section class="page-header reveal">
      <div class="page-header-copy">
        <p class="eyebrow">Sentiment Arcs</p>
        <h1 class="section-title">Compare narrative pacing without pretending it is literary quality.</h1>
        <p class="section-copy">This view works best as a reading-experience and discussion-planning surface. It helps teams compare calmer and more volatile books across the live corpus.</p>
      </div>
      <span class="tag subtle">Windowed sentiment only</span>
    </section>
    <section class="panel reveal" style="--delay:1">
      <div class="search-shell">
        <input class="search-input" id="sentiment-search" type="search" placeholder="Filter books before selecting up to 5" />
        <div class="tag-row" id="sentiment-selected"></div>
        <div class="book-list" id="sentiment-catalog" data-default-books="${curated.join(",")}"></div>
      </div>
    </section>
    <section class="two-column" id="sentiment-root"></section>
  `;
}

function renderCorpusPage(data) {
  const dominantDecade = data.corpus.timeline.reduce((best, current) => (current.nBooks > best.nBooks ? current : best), data.corpus.timeline[0]);
  const genderLeader = data.corpus.genderMix[0];
  return `
    <section class="page-header reveal">
      <div class="page-header-copy">
        <p class="eyebrow">Corpus Insights</p>
        <h1 class="section-title">Audit the collection before turning it into a public claim.</h1>
        <p class="section-copy">This is the route to use when you need provenance, balance, and collection-risk visibility rather than a single-book answer.</p>
      </div>
      <span class="tag">Canon-aware by design</span>
    </section>
    <section class="metric-grid">
      ${metricCard("Decades covered", formatNumber(data.corpus.timeline.length), "Grouped from the real manifest publication years.")}
      ${metricCard("Dominant decade", `${dominantDecade.decade}s`, "A reminder that the corpus is historically concentrated.")}
      ${metricCard("Top metadata share", genderLeader ? `${genderLeader.authorGender}: ${formatNumber(genderLeader.nBooks)}` : "n/a", "Visible so balance issues stay explicit.")}
      ${metricCard("Audit rows", formatNumber(data.corpus.inventory.reduce((sum, row) => sum + row.n_files, 0)), "Files currently tracked across core, legacy, and validation sets.")}
    </section>
    <section class="two-column">
      <article class="panel reveal" style="--delay:1">
        <p class="eyebrow">Temporal distribution</p>
        <h2 class="section-title">Where the catalog clusters</h2>
        <div class="chart-shell">
          ${renderTimelineChart(data.corpus.timeline)}
          <div class="chart-caption">Signal: historical concentration in the live corpus. Decision: whether the collection is broad enough for the public claim you want to make. Limit: this is the current benchmark corpus, not the whole field.</div>
        </div>
      </article>
      <article class="panel reveal" style="--delay:2">
        <p class="eyebrow">Collection balance</p>
        <h2 class="section-title">Split and authorship mix</h2>
        <div class="detail-list">
          ${renderMixList("Corpus split", data.corpus.splitMix, "splitLabel")}
          ${renderMixList("Authorship metadata", data.corpus.genderMix, "authorGender")}
        </div>
      </article>
    </section>
    <section class="two-column">
      <article class="panel reveal" style="--delay:3">
        <p class="eyebrow">Operational recommendations</p>
        <h2 class="section-title">What the audit suggests next</h2>
        <div class="recommendation-list">
          ${data.corpus.recommendations
            .map(
              (item) => `
                <div class="recommendation-item">
                  <strong>${escapeHtml(item.title)}</strong>
                  <span>${escapeHtml(item.detail)}</span>
                </div>
              `
            )
            .join("")}
        </div>
      </article>
      <article class="panel reveal" style="--delay:4">
        <p class="eyebrow">Auxiliary validation</p>
        <h2 class="section-title">Local reference corpora</h2>
        <div class="table-shell">
          <table>
            <thead><tr><th>Source</th><th>Words</th><th>TTR</th><th>AFINN / 10k</th></tr></thead>
            <tbody>
              ${data.corpus.auxiliaryValidation
                .map(
                  (row) => `
                  <tr>
                    <td>${escapeHtml(row.source)}</td>
                    <td>${formatNumber(row.word_count)}</td>
                    <td>${formatFloat(row.type_token_ratio, 4)}</td>
                    <td>${formatFloat(row.afinn_per_10k, 2)}</td>
                  </tr>
                `
                )
                .join("")}
            </tbody>
          </table>
        </div>
      </article>
    </section>
  `;
}

function attachExplorer(data) {
  const listEl = document.getElementById("explorer-list");
  const detailEl = document.getElementById("explorer-detail");
  const searchEl = document.getElementById("explorer-search");
  const root = document.getElementById("explorer-root");
  if (!listEl || !detailEl || !searchEl || !root) return;

  const books = [...data.books].sort((a, b) => a.title.localeCompare(b.title));
  let filtered = books;
  let selected = books.find((book) => book.id === root.dataset.defaultBook) || books[0];

  const renderList = () => {
    listEl.innerHTML = filtered
      .map(
        (book) => `
        <div class="book-list-item ${selected?.id === book.id ? "active" : ""}" data-book-id="${book.id}">
          <p class="book-title">${escapeHtml(book.title)}</p>
          <div class="book-meta">${escapeHtml(book.author)} · ${book.publicationYear} · ${escapeHtml(book.splitLabel)}</div>
        </div>
      `
      )
      .join("");
  };

  const renderDetail = () => {
    if (!selected) {
      detailEl.innerHTML = `<div class="empty-state">Select a book to inspect its metadata, strongest themes, narrative pacing, and related-title neighbors.</div>`;
      return;
    }
    const sentimentSeries = [{ label: selected.title, points: selected.sentiment.windows }];
    detailEl.innerHTML = `
      <div class="detail-grid">
        <div class="page-header">
          <div class="page-header-copy">
            <p class="eyebrow">Selected title</p>
            <h2 class="section-title">${escapeHtml(selected.title)}</h2>
            <p class="section-copy">${escapeHtml(selected.summary)}</p>
          </div>
          <div class="tag-row">
            <span class="tag">${escapeHtml(selected.splitLabel)}</span>
            <span class="tag subtle">${selected.ageBandLabel}</span>
          </div>
        </div>
        <div class="metric-grid">
          ${metricCard("Words", formatNumber(selected.wordCount), "Used for chunking and comparability." )}
          ${metricCard("Sentences", formatNumber(selected.sentenceCount), "Approximate sentence-level scale." )}
          ${metricCard("Pacing", escapeHtml(selected.sentiment.label), "Windowed sentiment summary." )}
          ${metricCard("Type/token", formatFloat(selected.typeTokenRatio, 4), "Lexical variety in the cleaned text." )}
        </div>
        <div class="two-column">
          <div class="panel">
            <p class="eyebrow">Theme profile</p>
            <div class="badge-grid">
              ${selected.themes
                .slice(0, 6)
                .map((theme) => `<span class="theme-chip">${escapeHtml(theme.label)} <b>${formatFloat(theme.score, 1)}</b></span>`)
                .join("")}
            </div>
            <div class="chart-caption">Signal: strongest guided themes in this book. Decision: where the title fits in shelf design or thematic list building. Limit: these values follow the current seed vocabulary.</div>
          </div>
          <div class="panel">
            <p class="eyebrow">Similar titles</p>
            <div class="signal-list">
              ${selected.similar
                .map(
                  (item) => `
                    <div class="signal-item">
                      <strong><a class="inline-link" href="/explorer?book=${slugify(item.title)}">${escapeHtml(item.title)}</a></strong>
                      <span>Current corpus similarity score: ${formatFloat(item.score, 3)}</span>
                    </div>
                  `
                )
                .join("")}
            </div>
          </div>
        </div>
        <div class="two-column">
          <div class="panel">
            <p class="eyebrow">Sentiment arc</p>
            <div class="chart-shell">
              ${renderLineChart(sentimentSeries)}
              <div class="chart-caption">Signal: narrative pacing over twelve windows. Decision: compare steadier and more volatile books without turning the curve into a quality score. Limit: this remains a lexicon-backed fallback in the current runtime.</div>
            </div>
          </div>
          <div class="panel">
            <p class="eyebrow">Entity surface</p>
            <div class="signal-list">
              ${
                selected.entities.length
                  ? selected.entities
                      .map(
                        (entity) => `
                        <div class="signal-item">
                          <strong>${escapeHtml(entity.name)}</strong>
                          <span>${formatNumber(entity.count)} mentions · ${formatFloat(entity.per10k, 2)} per 10k tokens</span>
                        </div>
                      `
                      )
                      .join("")
                  : `<div class="empty-state">No stable entities were extracted for this title under the current fallback backend.</div>`
              }
            </div>
          </div>
        </div>
        <div class="panel">
          <p class="eyebrow">Provenance and topic note</p>
          <div class="detail-list">
            <div class="detail-item"><strong>Source</strong><span><a class="inline-link" href="${selected.sourceUrl}" target="_blank" rel="noreferrer">Project Gutenberg record</a> with local path <code class="mono">${escapeHtml(selected.localPath)}</code>.</span></div>
            <div class="detail-item"><strong>Dominant topic proxy</strong><span>${selected.dominantTopic ? `${escapeHtml(selected.dominantTopic.id)} with share ${formatFloat(selected.dominantTopic.share, 3)} and top terms ${escapeHtml(selected.dominantTopic.terms)}` : "No topic row available for this title."}</span></div>
          </div>
        </div>
      </div>
    `;
  };

  renderList();
  renderDetail();

  searchEl.addEventListener("input", (event) => {
    const query = String(event.target.value || "").trim().toLowerCase();
    filtered = books.filter((book) => `${book.title} ${book.author}`.toLowerCase().includes(query));
    if (selected && !filtered.some((book) => book.id === selected.id)) {
      selected = filtered[0] || null;
      updateQuery(selected?.id || "");
    }
    renderList();
    renderDetail();
  });

  listEl.addEventListener("click", (event) => {
    const target = event.target.closest("[data-book-id]");
    if (!target) return;
    selected = books.find((book) => book.id === target.dataset.bookId) || selected;
    updateQuery(selected.id);
    renderList();
    renderDetail();
  });
}

function attachThemes(data) {
  const tabsEl = document.getElementById("theme-tabs");
  const root = document.getElementById("themes-root");
  if (!tabsEl || !root) return;

  const params = new URLSearchParams(window.location.search);
  let currentTheme = params.get("theme") || data.themes[0]?.id || "family";

  const render = () => {
    tabsEl.innerHTML = data.themes
      .map(
        (theme) => `
        <button class="tag-button ${theme.id === currentTheme ? "active" : ""}" data-theme-id="${theme.id}">
          ${escapeHtml(theme.label)}
        </button>
      `
      )
      .join("");

    const theme = data.themes.find((item) => item.id === currentTheme) || data.themes[0];
    const referenceTheme = ROUTE_THEME_REFERENCE[theme.id] || "moral_emotion";
    const comparisonPoints = data.books.map((book) => ({
      title: book.title,
      x: getThemeScore(book, theme.id),
      y: getThemeScore(book, referenceTheme),
      wordCount: book.wordCount,
    }));
    root.innerHTML = `
      <article class="panel reveal" style="--delay:1">
        <div class="stack">
          <p class="eyebrow">Theme overview</p>
          <h2 class="section-title">${escapeHtml(theme.label)}</h2>
          <p class="section-copy">${escapeHtml(theme.description)}</p>
          <div class="metric-grid">
            ${metricCard("Mean score", formatFloat(theme.stats.mean, 2), "Average score across the live corpus.")}
            ${metricCard("Median score", formatFloat(theme.stats.median, 2), "Typical title-level intensity for this theme.")}
            ${metricCard("Peak score", formatFloat(theme.stats.max, 2), "Strongest current title in the corpus.")}
            ${metricCard("Reference axis", escapeHtml(labelizeTheme(referenceTheme)), "Secondary comparison axis in the scatter view.")}
          </div>
          <div class="signal-list">
            ${theme.topBooks
              .slice(0, 6)
              .map(
                (book) => `
                <div class="signal-item">
                  <strong><a class="inline-link" href="/explorer?book=${slugify(book.title)}">${escapeHtml(book.title)}</a> · ${formatFloat(book.score, 2)}</strong>
                  <span>${escapeHtml(book.summary)}</span>
                </div>
              `
              )
              .join("")}
          </div>
        </div>
      </article>
      <article class="panel reveal" style="--delay:2">
        <p class="eyebrow">Theme comparison</p>
        <h2 class="section-title">${escapeHtml(theme.label)} vs. ${escapeHtml(labelizeTheme(referenceTheme))}</h2>
        <div class="chart-shell">
          ${renderThemeScatter(comparisonPoints, theme.id, referenceTheme)}
          <div class="chart-caption">Signal: relative position of each book on two interpretable theme axes. Decision: which titles fit one theme strongly versus balancing two adjacent reading-list directions. Limit: the axes come from the current seed-guided vocabulary.</div>
        </div>
      </article>
    `;
  };

  tabsEl.addEventListener("click", (event) => {
    const button = event.target.closest("[data-theme-id]");
    if (!button) return;
    currentTheme = button.dataset.themeId;
    updateQuery(null, { theme: currentTheme });
    render();
  });

  render();
}

function attachSentiment(data) {
  const catalogEl = document.getElementById("sentiment-catalog");
  const selectedEl = document.getElementById("sentiment-selected");
  const root = document.getElementById("sentiment-root");
  const searchEl = document.getElementById("sentiment-search");
  if (!catalogEl || !selectedEl || !root || !searchEl) return;

  const books = [...data.books].sort((a, b) => a.title.localeCompare(b.title));
  const defaultIds = (catalogEl.dataset.defaultBooks || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
  let filtered = books;
  let selectedIds = new Set(defaultIds.slice(0, 3));

  const renderCatalog = () => {
    catalogEl.innerHTML = filtered
      .map(
        (book) => `
        <div class="book-list-item ${selectedIds.has(book.id) ? "active" : ""}" data-book-id="${book.id}">
          <p class="book-title">${escapeHtml(book.title)}</p>
          <div class="book-meta">${escapeHtml(book.author)} · ${escapeHtml(book.sentiment.label)} · mean ${formatFloat(book.sentiment.mean, 3)}</div>
        </div>
      `
      )
      .join("");
  };

  const renderSelected = () => {
    const selectedBooks = books.filter((book) => selectedIds.has(book.id));
    selectedEl.innerHTML = selectedBooks
      .map(
        (book) => `
          <button class="tag-button active" data-book-id="${book.id}">
            ${escapeHtml(book.title)}
          </button>
        `
      )
      .join("");

    const series = selectedBooks.map((book) => ({ label: book.title, points: book.sentiment.windows }));
    const mostVolatile = [...books].sort((a, b) => b.sentiment.volatility - a.sentiment.volatility).slice(0, 6);
    root.innerHTML = `
      <article class="panel reveal" style="--delay:2">
        <p class="eyebrow">Comparison chart</p>
        <h2 class="section-title">Narrative pacing across selected books</h2>
        <div class="chart-shell">
          ${renderLineChart(series)}
          <div class="legend">
            ${selectedBooks
              .map(
                (book, index) => `
                  <span><span class="legend-swatch" style="background:${SERIES_COLORS[index % SERIES_COLORS.length]}"></span>${escapeHtml(book.title)}</span>
                `
              )
              .join("")}
          </div>
          <div class="chart-caption">Signal: windowed sentiment movement across the selected books. Decision: compare calmer and more turbulent reading experiences. Limit: the curve is an interpretive proxy, not a quality ranking.</div>
        </div>
      </article>
      <article class="panel reveal" style="--delay:3">
        <p class="eyebrow">Pattern overview</p>
        <h2 class="section-title">Volatility and tone in the full catalog</h2>
        <div class="signal-list">
          ${mostVolatile
            .map(
              (book) => `
                <div class="signal-item">
                  <strong><a class="inline-link" href="/explorer?book=${book.id}">${escapeHtml(book.title)}</a></strong>
                  <span>${escapeHtml(book.sentiment.label)} · volatility ${formatFloat(book.sentiment.volatility, 3)} · mean ${formatFloat(book.sentiment.mean, 3)}</span>
                </div>
              `
            )
            .join("")}
        </div>
      </article>
    `;
  };

  renderCatalog();
  renderSelected();

  searchEl.addEventListener("input", (event) => {
    const query = String(event.target.value || "").trim().toLowerCase();
    filtered = books.filter((book) => `${book.title} ${book.author}`.toLowerCase().includes(query));
    renderCatalog();
  });

  catalogEl.addEventListener("click", (event) => {
    const target = event.target.closest("[data-book-id]");
    if (!target) return;
    const id = target.dataset.bookId;
    if (selectedIds.has(id)) {
      selectedIds.delete(id);
    } else if (selectedIds.size < 5) {
      selectedIds.add(id);
    }
    renderCatalog();
    renderSelected();
  });

  selectedEl.addEventListener("click", (event) => {
    const button = event.target.closest("[data-book-id]");
    if (!button) return;
    selectedIds.delete(button.dataset.bookId);
    renderCatalog();
    renderSelected();
  });
}

function renderFeaturedBook(book, index) {
  return `
    <article class="panel reveal" style="--delay:${index + 1}">
      <p class="eyebrow">${escapeHtml(book.splitLabel)}</p>
      <h3 class="mini-title">${escapeHtml(book.title)}</h3>
      <p class="section-copy">${escapeHtml(book.author)} · ${book.publicationYear}</p>
      <p class="body-copy">${escapeHtml(book.summary)}</p>
      <div class="tag-row">
        ${book.themes.slice(0, 2).map((theme) => `<span class="tag subtle">${escapeHtml(theme.label)} ${formatFloat(theme.score, 1)}</span>`).join("")}
      </div>
      <p><a class="inline-link" href="/explorer?book=${book.id}">Inspect this title</a></p>
    </article>
  `;
}

function metricCard(label, value, copy) {
  return `
    <div class="metric-card reveal">
      <div class="metric-label">${escapeHtml(label)}</div>
      <div class="metric-value">${escapeHtml(value)}</div>
      <div class="metric-copy">${escapeHtml(copy)}</div>
    </div>
  `;
}

function renderMixList(title, rows, labelKey) {
  return `
    <div class="detail-item">
      <strong>${escapeHtml(title)}</strong>
      <div class="signal-list">
        ${rows
          .map(
            (row) => `
            <div class="signal-item">
              <strong>${escapeHtml(row[labelKey])}</strong>
              <span>${formatNumber(row.nBooks)} books · ${row.totalWords ? `${formatNumber(row.totalWords)} words` : "metadata count"}</span>
            </div>
          `
          )
          .join("")}
      </div>
    </div>
  `;
}

function renderLineChart(series) {
  if (!series.length) {
    return `<div class="empty-state">Select at least one book to draw a sentiment arc.</div>`;
  }
  const width = 820;
  const height = 320;
  const margin = { top: 18, right: 20, bottom: 34, left: 38 };
  const allPoints = series.flatMap((item) => item.points.map((point) => point.score));
  const min = Math.min(...allPoints, -0.04);
  const max = Math.max(...allPoints, 0.08);
  const xScale = (windowIndex) =>
    margin.left + ((windowIndex - 1) / 11) * (width - margin.left - margin.right);
  const yScale = (value) => margin.top + ((max - value) / (max - min || 1)) * (height - margin.top - margin.bottom);
  const ticks = [min, (min + max) / 2, max];

  const paths = series
    .map((item, index) => {
      const d = item.points.map((point, pointIndex) => `${pointIndex === 0 ? "M" : "L"} ${xScale(point.window)} ${yScale(point.score)}`).join(" ");
      return `<path d="${d}" fill="none" stroke="${SERIES_COLORS[index % SERIES_COLORS.length]}" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"></path>`;
    })
    .join("");

  const labels = Array.from({ length: 12 }, (_, idx) => idx + 1)
    .map(
      (tick) => `
      <text x="${xScale(tick)}" y="${height - 10}" text-anchor="middle" font-size="11" fill="#5f6a63">${tick}</text>
    `
    )
    .join("");

  const grid = ticks
    .map(
      (tick) => `
      <g>
        <line x1="${margin.left}" x2="${width - margin.right}" y1="${yScale(tick)}" y2="${yScale(tick)}" stroke="rgba(21,37,38,0.12)" stroke-dasharray="4 6"></line>
        <text x="${margin.left - 12}" y="${yScale(tick) + 4}" text-anchor="end" font-size="11" fill="#5f6a63">${formatFloat(tick, 2)}</text>
      </g>
    `
    )
    .join("");

  return `
    <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Sentiment line chart">
      ${grid}
      <line x1="${margin.left}" x2="${width - margin.right}" y1="${height - margin.bottom}" y2="${height - margin.bottom}" stroke="rgba(21,37,38,0.24)"></line>
      <line x1="${margin.left}" x2="${margin.left}" y1="${margin.top}" y2="${height - margin.bottom}" stroke="rgba(21,37,38,0.24)"></line>
      ${paths}
      ${labels}
      <text x="${width / 2}" y="${height - 2}" text-anchor="middle" font-size="12" fill="#5f6a63">Narrative window</text>
    </svg>
  `;
}

function renderScatterChart(books) {
  const width = 760;
  const height = 420;
  const margin = { top: 22, right: 24, bottom: 38, left: 40 };
  const xs = books.map((book) => book.projection.x);
  const ys = books.map((book) => book.projection.y);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const maxWords = Math.max(...books.map((book) => book.wordCount));
  const xScale = (value) => margin.left + ((value - minX) / (maxX - minX || 1)) * (width - margin.left - margin.right);
  const yScale = (value) => margin.top + ((maxY - value) / (maxY - minY || 1)) * (height - margin.top - margin.bottom);
  const circles = books
    .map((book) => {
      const radius = 5 + (book.wordCount / maxWords) * 14;
      return `
        <g>
          <circle cx="${xScale(book.projection.x)}" cy="${yScale(book.projection.y)}" r="${radius}" fill="rgba(15,61,67,0.18)" stroke="#0f3d43" stroke-width="1.5"></circle>
          <text x="${xScale(book.projection.x) + radius + 4}" y="${yScale(book.projection.y) + 3}" font-size="11" fill="#435352">${escapeHtml(book.title)}</text>
        </g>
      `;
    })
    .join("");
  return `
    <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Book neighborhood scatter plot">
      <line x1="${margin.left}" x2="${width - margin.right}" y1="${height - margin.bottom}" y2="${height - margin.bottom}" stroke="rgba(21,37,38,0.24)"></line>
      <line x1="${margin.left}" x2="${margin.left}" y1="${margin.top}" y2="${height - margin.bottom}" stroke="rgba(21,37,38,0.24)"></line>
      ${circles}
      <text x="${width / 2}" y="${height - 6}" text-anchor="middle" font-size="12" fill="#5f6a63">Embedding projection x</text>
      <text x="${margin.left - 22}" y="${height / 2}" transform="rotate(-90 ${margin.left - 22} ${height / 2})" text-anchor="middle" font-size="12" fill="#5f6a63">Embedding projection y</text>
    </svg>
  `;
}

function renderThemeScatter(points, xTheme, yTheme) {
  const width = 760;
  const height = 420;
  const margin = { top: 22, right: 24, bottom: 40, left: 40 };
  const maxX = Math.max(...points.map((point) => point.x), 1);
  const maxY = Math.max(...points.map((point) => point.y), 1);
  const maxWords = Math.max(...points.map((point) => point.wordCount));
  const xScale = (value) => margin.left + (value / maxX) * (width - margin.left - margin.right);
  const yScale = (value) => margin.top + ((maxY - value) / maxY) * (height - margin.top - margin.bottom);
  const circles = points
    .map((point) => {
      const radius = 5 + (point.wordCount / maxWords) * 10;
      return `
        <g>
          <circle cx="${xScale(point.x)}" cy="${yScale(point.y)}" r="${radius}" fill="rgba(200,156,67,0.18)" stroke="#b16f3e" stroke-width="1.5"></circle>
          <text x="${xScale(point.x) + radius + 4}" y="${yScale(point.y) + 3}" font-size="11" fill="#435352">${escapeHtml(point.title)}</text>
        </g>
      `;
    })
    .join("");
  return `
    <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Theme scatter plot">
      <line x1="${margin.left}" x2="${width - margin.right}" y1="${height - margin.bottom}" y2="${height - margin.bottom}" stroke="rgba(21,37,38,0.24)"></line>
      <line x1="${margin.left}" x2="${margin.left}" y1="${margin.top}" y2="${height - margin.bottom}" stroke="rgba(21,37,38,0.24)"></line>
      ${circles}
      <text x="${width / 2}" y="${height - 6}" text-anchor="middle" font-size="12" fill="#5f6a63">${escapeHtml(labelizeTheme(xTheme))}</text>
      <text x="${margin.left - 22}" y="${height / 2}" transform="rotate(-90 ${margin.left - 22} ${height / 2})" text-anchor="middle" font-size="12" fill="#5f6a63">${escapeHtml(labelizeTheme(yTheme))}</text>
    </svg>
  `;
}

function renderTimelineChart(rows) {
  const maxBooks = Math.max(...rows.map((row) => row.nBooks), 1);
  return `
    <div class="signal-list">
      ${rows
        .map(
          (row) => `
            <div class="signal-item">
              <strong>${row.decade}s</strong>
              <div style="display:grid;gap:8px;">
                <div style="height:10px;border-radius:999px;background:rgba(15,61,67,0.08);overflow:hidden;">
                  <div style="height:100%;width:${(row.nBooks / maxBooks) * 100}%;background:linear-gradient(90deg,#0f3d43,#b16f3e);"></div>
                </div>
                <span>${formatNumber(row.nBooks)} books · ${formatNumber(row.totalWords)} words</span>
              </div>
            </div>
          `
        )
        .join("")}
    </div>
  `;
}

function pickSentimentDefaults(books) {
  return [...books]
    .sort((a, b) => b.sentiment.volatility - a.sentiment.volatility)
    .slice(0, 3);
}

function getThemeScore(book, themeId) {
  return Number((book.themes.find((theme) => theme.id === themeId) || {}).score || 0);
}

function findBookFromQuery(books) {
  const params = new URLSearchParams(window.location.search);
  const requested = params.get("book");
  if (!requested) return null;
  return books.find((book) => book.id === requested || slugify(book.title) === requested) || null;
}

function updateQuery(bookId, extra = {}) {
  const url = new URL(window.location.href);
  if (bookId) {
    url.searchParams.set("book", bookId);
  } else {
    url.searchParams.delete("book");
  }
  Object.entries(extra).forEach(([key, value]) => {
    if (value == null || value === "") url.searchParams.delete(key);
    else url.searchParams.set(key, value);
  });
  window.history.replaceState({}, "", url);
}

function isActiveRoute(page, href) {
  if (href === "/" && page === "home") return true;
  if (href === "/report") return false;
  return href === `/${page}`;
}

function formatNumber(value) {
  return new Intl.NumberFormat("en-US").format(Number(value || 0));
}

function formatCompactNumber(value) {
  return new Intl.NumberFormat("en-US", {
    notation: "compact",
    maximumFractionDigits: 2,
  }).format(Number(value || 0));
}

function formatFloat(value, digits = 2) {
  return Number(value || 0).toFixed(digits);
}

function slugify(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function labelizeTheme(themeId) {
  return String(themeId || "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (match) => match.toUpperCase());
}

function getByPath(object, path) {
  return path.split(".").reduce((current, key) => (current == null ? current : current[key]), object);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function animateSelection() {
  document.querySelectorAll(".reveal").forEach((element, index) => {
    element.style.setProperty("--delay", element.style.getPropertyValue("--delay") || `${index}`);
  });
}
