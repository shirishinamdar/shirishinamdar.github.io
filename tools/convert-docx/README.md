# Word -> Chirpy post converter

Turns a weekly `.docx` lab note into a Chirpy-themed Jekyll post. Lives at `tools/convert-docx/docx_to_chirpy.py`.

## One-time setup

Install pandoc once on your machine:

```powershell
# Windows
winget install --id JohnMacFarlane.Pandoc
```

```bash
# macOS
brew install pandoc

# Linux
sudo apt install pandoc
```

Verify: `pandoc --version` should print 2.x or 3.x.

## Weekly workflow

1. Drop the week's `.docx` into `drafts-source/` at the repo root. Keep the source docs there — they're excluded from the published site, but a useful archive of what you actually wrote.
2. To convert **one** doc, run from the repo root:

   ```powershell
   python tools\convert-docx\docx_to_chirpy.py drafts-source\my-topic.docx `
       --title "Clear, Specific Title with the Hook" `
       --slug  "short-url-slug" `
       --categories "Cybersecurity,Topic" `
       --tags "tag1,tag2,tag3"
   ```

   To convert **all** the docs in a folder at once (batch mode):

   ```powershell
   python tools\convert-docx\docx_to_chirpy.py drafts-source
   ```

   In batch mode, each post's title and slug are auto-derived from the filename; you'll edit those in the post afterwards.

   Common flags:

   - `--draft` -> write to `_drafts/<slug>.md` instead of `_posts/`. Drafts don't publish until moved into `_posts/` with a date prefix.
   - `--dry-run` -> print the result to stdout, don't touch files. Use this first if you're unsure.
   - `--cover N` -> use the Nth image (1-based) as the cover. `--cover none` omits it.
   - `--date YYYY-MM-DD` -> override the post date (defaults to today, ET).
   - `--keep-trailer` -> disable the auto-strip of "Key Points / Future Work / Supervisor / Weekly Status" boilerplate (see below).

### Auto-stripped boilerplate

The script automatically removes any trailing section with one of these headings (case-insensitive, as either an `## H2` heading or a `**bold**` line):

- `Key Points`
- `Future Work`
- `Weekly Status` / `Weekly Update` / `Weekly Report`
- `Status Report` / `Status Update`
- `Supervisor` (and `Updates for Supervisor / Manager / Team`)
- `Action Items` / `Pending Items` / `To-do`
- `Reporting To`

This is meant for the status-report footers you include in your weekly docs. Everything from the first matching heading to the end of the document gets dropped. If a particular post legitimately uses one of these headings as real content, pass `--keep-trailer` to disable the stripping.

3. Open the new file in `_posts/YYYY-MM-DD-<slug>.md`. **Edit it.** The script does mechanical conversion — it does not write your post. At minimum, every published post on this site should have:
   - a one-line **lab disclaimer** if it's offensive/lab content,
   - a **TL;DR** of 2-4 sentences immediately after the title,
   - real H2 (`##`) and H3 (`###`) headings — Chirpy's TOC needs them,
   - a **"What I learned" / "Why this matters"** section that shows reasoning, not just steps,
   - a **defenses or limitations** section if the topic is offensive,
   - **alt text** on every image (currently the script copies whatever Pandoc produced, which is usually empty).
4. Preview locally before pushing:

   ```powershell
   bundle exec jekyll s
   ```

   Open <http://127.0.0.1:4000>. Click into the post. Verify: every image renders, the TOC sidebar has entries, the cover image shows, no Liquid errors in the console.
5. Commit and push:

   ```powershell
   git add _posts assets/img/posts tools drafts-source _config.yml
   git commit -m "Post: <title>"
   git push
   ```

   GitHub Actions runs `htmlproofer` on the build. If any image link is broken, deploy fails. Fix locally, repush.

## How to write better source docs

The converter is only as good as the input. Habits that will save you cleanup time:

- In Word, use **Heading 1** for the title and **Heading 2 / Heading 3** for sections. Don't use bold paragraphs as fake headings — Pandoc won't promote them, and your TOC will be empty.
- Start each new doc from a **blank file**, not from last week's. Stale leftover content is the #1 thing I have to strip when converting.
- Give every screenshot a **caption** in Word (Insert -> Caption, or just a line of italic text below the image). Even better: rename images before insertion so they sort meaningfully (`01-user-creation.png`, `02-bios-boot.png`).
- One topic per doc. Long docs that mix two topics should be two posts.

## What the converter does and doesn't do

**Does:**

- Runs pandoc to convert `.docx` -> GFM markdown.
- Extracts embedded images and copies them into `assets/img/blog/<slug>/`.
- Rewrites image paths to `/assets/img/blog/<slug>/<filename>`.
- Normalizes Word smart quotes, en/em dashes, and soft line breaks.
- Splits text-attached inline images onto their own paragraph.
- Un-indents block-quoted images (Word indentation artifact).
- Drops a leading bold "title" line if it duplicates the front matter title.
- Builds Chirpy-compliant front matter with title, date+IST offset, categories, tags, and a cover image.

**Does not:**

- Promote bold paragraphs to headings (you should fix those in Word).
- Write your TL;DR, takeaways, or disclaimers (those are your voice).
- Compress or rename images — same filenames pandoc emits (`image1.jpeg`, `image2.jpeg`...).
- Touch tables that pandoc emitted as raw HTML — you may need to manually rewrite to GFM.
- Strip unrelated content — anything in your `.docx` ends up in the post.

## Files this tool touches

| Location | What |
| --- | --- |
| `_posts/YYYY-MM-DD-<slug>.md` | The published post (or `_drafts/<slug>.md` with `--draft`). |
| `assets/img/blog/<slug>/` | Copies of the images referenced in the post. |
| `drafts-source/` | Where you keep the original `.docx` source files (git-tracked, excluded from build). |
| `tools/convert-docx/` | The script itself. |

Nothing outside these paths is modified.
