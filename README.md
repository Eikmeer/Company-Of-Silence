# Company of Silence

## Adding a new post
Create a new file in `content/posts/`, named however you like using
lowercase letters and hyphens — the filename becomes the web address.
For example, `content/posts/on-waiting.md` becomes `/posts/on-waiting.html`.

Inside the file:

    ---
    title: On Waiting
    date: 2026-09-05
    ---

    Your first paragraph goes here.

    A second paragraph. Leave a blank line between paragraphs.
    A single line break, like this one,
    stays a line break instead of starting a new paragraph — useful for poems.

    Use **double asterisks** for bold and *single asterisks* for italic.

That's it — no HTML, no code. The newest post (by date) automatically
becomes the homepage's "01 / Featured" piece, and shows up at the top
of the Contents list.

## Removing a post
Delete its `.md` file from `content/posts/`.

## Editing existing text
Open the post's `.md` file and edit the words directly — same markdown
rules as above.

## Editing homepage copy (headlines, taglines, footer text)
All of it lives in `content/site.md` as plain `key: value` lines.

## Editing the About / Discard pages
Edit `content/about.md` / `content/discard.md` directly.

## Restyling (colors, fonts)
Open `style.css` — the very top has a `:root { ... }` block with
named variables (`--color-bg`, `--color-text`, `--font-body`, etc).
Change a value there and it updates everywhere on the site. Everything
below that block is regular CSS if you want to go further.

## Turning on the subscribe form
Create a free account at buttondown.email, then in `content/site.md`
replace `YOUR-BUTTONDOWN-USERNAME` with your real username.

## How this builds
`build.py` is a small dependency-free Python script that reads
everything in `content/` and generates the finished site into `_site/`.
You never need to run it by hand if this repo is connected to Netlify —
see the deployment instructions in the chat. If you do want to preview
locally: `python3 build.py`, then open `_site/index.html` in a browser.
