#!/usr/bin/env python3
"""
Company of Silence — site builder.

Reads plain markdown files from content/ and generates the full static
site into _site/. No external dependencies — just the Python standard
library, so this runs anywhere Python 3 runs, including Netlify's
build servers, with nothing to install.

To add a post: create content/posts/your-post-slug.md with:

    ---
    title: Your Title Here
    date: 2026-09-01
    ---

    First paragraph.

    Second paragraph. Use **bold** and *italic* if you like.
    A single line break, like this,
    stays a line break — handy for poems.

Then run:  python3 build.py
Or just push to GitHub if this repo is connected to Netlify — it runs
this same command automatically.

To remove a post: delete its .md file and rebuild.
To restyle: edit the :root {} block at the top of style.css.
To change homepage copy: edit content/site.md.
"""

import re, os, html, datetime, math, shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(ROOT, 'content')
OUT = os.path.join(ROOT, '_site')


# ------------------------------------------------------------------
# Frontmatter + markdown parsing (minimal, dependency-free)
# ------------------------------------------------------------------

def parse_frontmatter(text):
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', text, flags=re.S)
    if not m:
        return {}, text.strip()
    fm_block, body = m.group(1), m.group(2)
    fm = {}
    for line in fm_block.splitlines():
        if ':' in line:
            key, val = line.split(':', 1)
            fm[key.strip()] = val.strip()
    return fm, body.strip()


def inline_md(s):
    s = html.escape(s, quote=False)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'\*(.+?)\*', r'<em>\1</em>', s)
    s = s.replace('\n', '<br>\n        ')
    return s


def markdown_to_paragraphs_html(body):
    blocks = re.split(r'\n\s*\n', body.strip())
    return [f'<p>{inline_md(b.strip())}</p>' for b in blocks if b.strip()]


def markdown_to_plain(body):
    blocks = re.split(r'\n\s*\n', body.strip())
    plain = []
    for b in blocks:
        b = re.sub(r'\*\*(.+?)\*\*', r'\1', b)
        b = re.sub(r'\*(.+?)\*', r'\1', b)
        b = b.replace('\n', ' ')
        plain.append(b.strip())
    return plain


def parse_date(s):
    s = s.strip()
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d'):
        try:
            return datetime.datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"Could not parse date: {s!r} — use YYYY-MM-DD or YYYY-MM-DD HH:MM")


def slugify(title):
    s = title.lower()
    s = re.sub(r"[''\"]", '', s)
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s


def reading_time(word_count):
    return max(1, math.ceil(word_count / 200))


def esc(s):
    return html.escape(s, quote=False)


# ------------------------------------------------------------------
# Load content
# ------------------------------------------------------------------

site_fm, _ = parse_frontmatter(open(os.path.join(CONTENT, 'site.md')).read())

posts = []
posts_dir = os.path.join(CONTENT, 'posts')
for fname in sorted(os.listdir(posts_dir)):
    if not fname.endswith('.md'):
        continue
    slug = fname[:-3]
    fm, body = parse_frontmatter(open(os.path.join(posts_dir, fname)).read())
    if 'title' not in fm or 'date' not in fm:
        raise ValueError(f"{fname}: needs both 'title' and 'date' in frontmatter")
    paragraphs_html = markdown_to_paragraphs_html(body)
    plain = markdown_to_plain(body)
    word_count = sum(len(p.split()) for p in plain)
    posts.append({
        'slug': slug,
        'title': fm['title'],
        'date': parse_date(fm['date']),
        'paragraphs_html': paragraphs_html,
        'plain_paragraphs': plain,
        'word_count': word_count,
        'reading_min': reading_time(word_count),
    })

posts.sort(key=lambda p: p['date'])

about_fm, about_body = parse_frontmatter(open(os.path.join(CONTENT, 'about.md')).read())
discard_fm, discard_body = parse_frontmatter(open(os.path.join(CONTENT, 'discard.md')).read())


# ------------------------------------------------------------------
# Templates
# ------------------------------------------------------------------

FONT_LINK = '''<link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Libre+Baskerville:wght@400;700&family=Marck+Script&display=swap" rel="stylesheet">'''

BUTTONDOWN_USERNAME = site_fm.get('buttondown_username', 'YOUR-BUTTONDOWN-USERNAME')
BRAND = site_fm.get('brand', 'Company of Silence')


def head(title, description, css_path):
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  {FONT_LINK}
  <link rel="stylesheet" href="{css_path}">
</head>
<body>'''


def header(root_prefix):
    return f'''  <header class="site-header">
    <a class="brand" href="{root_prefix}index.html">{esc(BRAND)}</a>
    <button class="menu-toggle" aria-label="Open menu" aria-expanded="false">Menu</button>
  </header>

  <div class="drawer" aria-hidden="true">
    <button class="drawer-close" aria-label="Close menu">Close</button>
    <nav>
      <a href="{root_prefix}about.html">About</a>
      <a href="{root_prefix}index.html#contents">Contents</a>
      <a href="{root_prefix}discard.html">Discard</a>
    </nav>
    <div class="subscribe-box">
      <p>Receive a quiet note.</p>
      <form id="subscribe" action="https://buttondown.email/api/emails/embed-subscribe/{BUTTONDOWN_USERNAME}" method="post" target="popupwindow" onsubmit="window.open('https://buttondown.email/{BUTTONDOWN_USERNAME}', 'popupwindow')">
        <input type="email" name="email" placeholder="Enter your email address" aria-label="Email address" required>
        <input type="hidden" value="1" name="embed">
        <button type="submit">Sign me up</button>
      </form>
      <small id="form-message"></small>
    </div>
  </div>
'''


def footer(root_prefix):
    year = datetime.datetime.now().year
    return f'''  <footer>
    <div class="foot-brand">{esc(BRAND)}</div>
    <div>{esc(site_fm.get('footer_tagline', ''))}</div>
    <div>&copy; {year} {esc(BRAND)}</div>
  </footer>
  <script src="{root_prefix}script.js"></script>
</body>
</html>'''


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)


# ------------------------------------------------------------------
# Build
# ------------------------------------------------------------------

if os.path.exists(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT)

shutil.copy(os.path.join(ROOT, 'style.css'), os.path.join(OUT, 'style.css'))
shutil.copy(os.path.join(ROOT, 'script.js'), os.path.join(OUT, 'script.js'))

# ---- individual post pages ----
for i, p in enumerate(posts):
    prev_post = posts[i - 1] if i > 0 else None
    next_post = posts[i + 1] if i < len(posts) - 1 else None
    excerpt = p['plain_paragraphs'][0] if p['plain_paragraphs'] else ''
    description = (excerpt[:150] + '…') if len(excerpt) > 150 else excerpt

    prev_link = f'<a href="{prev_post["slug"]}.html">&larr; {esc(prev_post["title"])}</a>' if prev_post else '<span></span>'
    next_link = f'<a href="{next_post["slug"]}.html">{esc(next_post["title"])} &rarr;</a>' if next_post else '<span></span>'

    out = head(f'{p["title"]} — {BRAND}', description, '../style.css')
    out += header('../')
    out += f'''  <main>
    <section class="article">
      <p class="eyebrow">{esc(BRAND)}</p>
      <h1>{esc(p["title"])}</h1>
      <p class="meta">{p["date"].strftime("%B %-d, %Y")} &middot; {p["reading_min"]} min read</p>
      <div class="article-body">
        {chr(10).join('        ' + para for para in p["paragraphs_html"])}
      </div>
      <nav class="post-nav" aria-label="Post navigation">
        {prev_link}
        {next_link}
      </nav>
    </section>
  </main>
'''
    out += footer('../')
    write(os.path.join(OUT, 'posts', f'{p["slug"]}.html'), out)

# ---- homepage ----
featured = posts[-1] if posts else None

list_rows = ''
for p in reversed(posts):
    list_rows += f'''        <a href="posts/{p["slug"]}.html">
          <span>{p["date"].strftime("%B %Y")}</span>
          <strong>{esc(p["title"])}</strong>
          <em>{p["reading_min"]:02d} min</em>
        </a>
'''

if featured:
    featured_excerpt_source = ' '.join(featured['plain_paragraphs'][:2])
    featured_excerpt = (featured_excerpt_source[:220] + '…') if len(featured_excerpt_source) > 220 else featured_excerpt_source
    featured_block = f'''      <article>
        <p class="meta">{featured["date"].strftime("%B %-d, %Y")} &middot; {featured["reading_min"]} min read</p>
        <h2>{esc(featured["title"])}</h2>
        <p class="excerpt">{esc(featured_excerpt)}</p>
        <a href="posts/{featured["slug"]}.html" class="read-link">Read piece <span>&#8599;</span></a>
      </article>'''
else:
    featured_block = '      <p>Nothing published yet.</p>'

index = head(
    f'{BRAND} — {site_fm.get("hero_line1","")} {site_fm.get("hero_line2","")}',
    site_fm.get('intro', ''),
    'style.css'
)
index += header('')
index += f'''  <main id="home">
    <section class="hero">
      <p class="wordmark">{esc(BRAND)}</p>
      <p class="eyebrow">{esc(site_fm.get('eyebrow',''))}</p>
      <h1>{esc(site_fm.get('hero_line1',''))}<br>{esc(site_fm.get('hero_line2',''))}</h1>
      <p class="intro">{esc(site_fm.get('intro',''))}</p>
      <a class="scroll-link" href="#featured">&darr; Begin reading</a>
    </section>

    <section id="featured" class="featured">
      <div class="section-label">01 / Featured</div>
{featured_block}
    </section>

    <section id="about" class="split">
      <div class="section-label">02 / About</div>
      <div>
        <h2>{esc(about_fm.get('title',''))}</h2>
        <p>{esc(site_fm.get('about_teaser',''))}</p>
        <a href="about.html" class="text-link">More about this place</a>
      </div>
    </section>

    <section id="contents" class="contents">
      <div class="section-label">03 / Contents</div>
      <h2>{esc(site_fm.get('contents_heading',''))}</h2>
      <p class="intro">{esc(site_fm.get('contents_intro',''))}</p>
      <div class="list">
{list_rows}      </div>
    </section>

    <section id="discards" class="discards">
      <div class="section-label">04 / Discard</div>
      <blockquote>&ldquo;{esc(site_fm.get('discard_quote',''))}&rdquo;</blockquote>
      <p>{esc(site_fm.get('discard_teaser',''))}</p>
      <a href="discard.html" class="text-link">Visit the discard pile</a>
    </section>
  </main>
'''
index += footer('')
write(os.path.join(OUT, 'index.html'), index)

# ---- about page ----
about = head(f'About — {BRAND}', site_fm.get('about_teaser', ''), 'style.css')
about += header('')
about += f'''  <main>
    <section class="page-section">
      <div class="section-label">02 / About</div>
      <h1>{esc(about_fm.get('title',''))}</h1>
      {chr(10).join('      ' + p for p in markdown_to_paragraphs_html(about_body))}
      <p><a href="index.html#contents" class="text-link">Read the collected pieces</a></p>
    </section>
  </main>
'''
about += footer('')
write(os.path.join(OUT, 'about.html'), about)

# ---- discard page ----
discard = head(f'Discard — {BRAND}', site_fm.get('discard_teaser', ''), 'style.css')
discard += header('')
discard += f'''  <main>
    <section class="page-section">
      <div class="section-label">05 / Discard</div>
      <h1>{esc(discard_fm.get('title',''))}</h1>
      {chr(10).join('      ' + p for p in markdown_to_paragraphs_html(discard_body))}
      <p><a href="index.html" class="text-link">Back to the front page</a></p>
    </section>
  </main>
'''
discard += footer('')
write(os.path.join(OUT, 'discard.html'), discard)

print(f"Built {len(posts)} posts + index/about/discard into _site/")
