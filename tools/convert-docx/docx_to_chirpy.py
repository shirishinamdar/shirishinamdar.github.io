#!/usr/bin/env python3
"""docx_to_chirpy.py — convert a Word document into a Chirpy Jekyll post.

Pipeline:
  1. Pandoc converts .docx -> GFM markdown, extracting embedded images.
  2. We post-process: rewrite image paths to /assets/img/blog/<slug>/,
     copy images into the repo, normalize Word's smart quotes/dashes,
     split inline-attached images onto their own paragraph, un-indent
     block-quoted images, and strip a leading bold "title" line that
     duplicates the front matter title.
  3. Front matter is prepended with Chirpy fields (title, date,
     categories, tags, image cover).
  4. Output written to _posts/YYYY-MM-DD-<slug>.md (or _drafts/<slug>.md).

Usage examples:
  python tools/convert-docx/docx_to_chirpy.py drafts-source/ophcrack.docx
  python tools/convert-docx/docx_to_chirpy.py foo.docx --title "My Title" \
      --categories "Cybersecurity,Tools" --tags "soc,passwords"
  python tools/convert-docx/docx_to_chirpy.py foo.docx --draft --dry-run

Requires: pandoc on PATH. Install:
  Windows: winget install --id JohnMacFarlane.Pandoc
  macOS:   brew install pandoc
  Linux:   apt install pandoc
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ----- defaults -----
DEFAULT_TZ = timezone(timedelta(hours=-4))  # America/New_York EDT; switch to -5 in winter (EST) or use zoneinfo
DEFAULT_CATEGORIES = ["Cybersecurity"]
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")

# Trailer signals — section titles that mark the start of weekly status-report
# boilerplate (supervisor updates, future work, action items, etc). Everything
# from the first match to the end of the document is stripped. Override with
# --keep-trailer if a particular post legitimately uses one of these headings.
TRAILER_SIGNALS = [
    r"key\s*points?",
    r"future\s*work",
    r"weekly\s*status",
    r"weekly\s*update",
    r"weekly\s*report",
    r"status\s*report",
    r"status\s*update",
    r"supervisor",
    r"action\s*items?",
    r"pending\s*items?",
    r"to[\s\-]?dos?",
    r"updates?\s*for\s*(?:supervisor|manager|team)",
    r"reporting\s*to",
]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def find_repo_root(start: Path) -> Path:
    """Walk up from `start` until we find _config.yml (the Jekyll repo root)."""
    for path in [start.resolve(), *start.resolve().parents]:
        if (path / "_config.yml").is_file():
            return path
    sys.exit(f"error: no _config.yml found above {start}")


def slugify(text: str) -> str:
    """Lowercase, hyphenated, ASCII-only — safe for filenames and URLs."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "post"


def require_pandoc() -> str:
    p = shutil.which("pandoc")
    if not p:
        sys.exit(
            "error: pandoc not on PATH.\n"
            "Windows: winget install --id JohnMacFarlane.Pandoc\n"
            "macOS:   brew install pandoc\n"
            "Linux:   sudo apt install pandoc"
        )
    return p


def yaml_quote(s: str) -> str:
    """Quote a YAML scalar only if it contains characters that would break parsing."""
    if re.search(r'[:#\[\]{},&*!|>\'"%@`]', s) or s.strip() != s:
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return s


def tz_offset(dt: datetime) -> str:
    """Format tz offset as '+0530' (Chirpy/Jekyll-compatible)."""
    off = dt.utcoffset() or timedelta(0)
    total = int(off.total_seconds())
    sign = "+" if total >= 0 else "-"
    total = abs(total)
    return f"{sign}{total // 3600:02d}{(total % 3600) // 60:02d}"


# ---------------------------------------------------------------------------
# pandoc + post-processing
# ---------------------------------------------------------------------------

def run_pandoc(pandoc: str, docx: Path, work: Path) -> str:
    """Run pandoc; return GFM markdown. Images land under <work>/media/."""
    md_file = work / "out.md"
    subprocess.run(
        [pandoc, str(docx), "-t", "gfm", f"--extract-media={work}", "-o", str(md_file)],
        check=True,
    )
    return md_file.read_text(encoding="utf-8")


def normalize_typography(md: str) -> str:
    """Replace Word's smart punctuation with plain ASCII; collapse Pandoc's
    backslash line breaks (which come from Word's soft returns)."""
    table = {
        "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "--",
        "\u2026": "...", "\u00a0": " ",
    }
    for k, v in table.items():
        md = md.replace(k, v)
    md = re.sub(r"\\(\r?\n)", r"\1", md)  # drop trailing-backslash soft breaks
    return md


def split_inline_images(md: str) -> str:
    """`text...![](img)` -> `text...\\n\\n![](img)`. Word loves to inline images."""
    return re.sub(r"([^\n!])(!\[[^\]]*\]\([^)]+\))", r"\1\n\n\2", md)


def unindent_blockquoted_images(md: str) -> str:
    """`> ![](img)` is almost always a Word indent, not a quote. Strip the `>`."""
    return re.sub(
        r"^>\s*(!\[[^\]]*\]\([^)]+\))\s*$", r"\1", md, flags=re.MULTILINE
    )


def strip_trailer(md: str) -> tuple[str, str | None]:
    """Drop trailing weekly-status boilerplate (Key Points, Future Work,
    Supervisor Updates, etc). Returns (cleaned_md, stripped_text_or_None).
    Cuts at the earliest heading or bold-only line whose label matches a
    pattern in TRAILER_SIGNALS."""
    sig = "|".join(TRAILER_SIGNALS)
    patterns = [
        rf"^#{{1,6}}\s+(?:{sig})\b[^\n]*$",           # ## Key Points
        rf"^\*\*\s*(?:{sig})\b[^*\n]*\*\*[\s:]*$",     # **Key Points:**
        rf"^(?:{sig})\b[^*\n]*\*\*[\s:]*$",            # Key Points:** (Word broke opening ** to prev line)
        rf"^\*\*\s*(?:{sig})\b[^*\n]*$",               # **Key Points (closing ** dropped)
    ]
    earliest = None
    for p in patterns:
        m = re.search(p, md, flags=re.IGNORECASE | re.MULTILINE)
        if m and (earliest is None or m.start() < earliest.start()):
            earliest = m
    if not earliest:
        return md, None
    cut = earliest.start()
    return md[:cut].rstrip() + "\n", md[cut:].strip()


def detect_title_from_body(md: str) -> str | None:
    """If the first non-empty line is a bold-only paragraph, treat it as the title."""
    for line in md.splitlines():
        s = line.strip()
        if not s:
            continue
        m = re.match(r"\*\*(.+?)\*\*\s*$", s)
        if not m:
            return None
        title = re.sub(r"\s+:\s*", ": ", m.group(1).strip())
        return title
    return None


def strip_leading_title_line(md: str, title: str) -> str:
    """Drop a leading bold title line so it doesn't duplicate the front matter title."""
    lines = md.splitlines()
    out: list[str] = []
    dropped = False
    for line in lines:
        if not dropped:
            s = line.strip()
            if not s:
                continue  # skip leading blanks while we look
            m = re.match(r"\*\*(.+?)\*\*\s*$", s)
            if m and m.group(1).strip().rstrip(":").lower() == title.rstrip(":").lower():
                dropped = True
                continue
            out.append(line)
            dropped = True  # the doc starts with non-bold; nothing to strip
        else:
            out.append(line)
    return "\n".join(out).lstrip("\n")


def rewrite_and_collect_images(
    md: str, slug: str, work: Path, dest_dir: Path
) -> tuple[str, list[Path]]:
    """Rewrite image paths to /assets/img/blog/<slug>/<filename> and copy images.
    Returns (rewritten_md, list_of_copied_files_in_doc_order)."""
    site_prefix = f"/assets/img/blog/{slug}/"
    copied: list[Path] = []

    def repl(m: re.Match) -> str:
        alt = m.group(1)
        raw = m.group(2).strip()
        # Pandoc emits paths relative to the markdown's directory (work/).
        candidate = (work / raw).resolve()
        if not candidate.is_file():
            # Pandoc sometimes nests `media/media/`. Fall back to filename match.
            tail = Path(raw).name
            hits = list(work.rglob(tail))
            if hits:
                candidate = hits[0]
            else:
                return m.group(0)  # leave unmodified if we can't find it
        # Copy if not already done
        dest = dest_dir / candidate.name
        if dest not in copied:
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(candidate, dest)
            copied.append(dest)
        return f"![{alt}]({site_prefix}{candidate.name})"

    md = IMAGE_RE.sub(repl, md)
    return md, copied


# ---------------------------------------------------------------------------
# front matter
# ---------------------------------------------------------------------------

def build_front_matter(
    title: str,
    when: datetime,
    categories: list[str],
    tags: list[str],
    cover: Path | None,
    cover_alt: str,
) -> str:
    date_str = f"{when.strftime('%Y-%m-%d %H:%M:%S')} {tz_offset(when)}"
    cats = ", ".join(yaml_quote(c) for c in categories)
    lines = [
        "---",
        f"title: {yaml_quote(title)}",
        f"date: {date_str}",
        f"categories: [{cats}]",
    ]
    if tags:
        lines.append(f"tags: [{', '.join(yaml_quote(t) for t in tags)}]")
    if cover is not None:
        lines += [
            "image:",
            f"  path: /assets/img/blog/{cover.parent.name}/{cover.name}",
            f"  alt: {yaml_quote(cover_alt)}",
        ]
    lines += ["---", ""]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description="Convert a .docx into a Chirpy Jekyll post.")
    ap.add_argument("docx", type=Path, help="input .docx")
    ap.add_argument("--title", help="post title (default: detected from doc)")
    ap.add_argument("--slug", help="URL slug (default: from filename)")
    ap.add_argument("--date", help="YYYY-MM-DD (default: today)")
    ap.add_argument("--categories", default=",".join(DEFAULT_CATEGORIES),
                    help='comma-separated, default: "Cybersecurity"')
    ap.add_argument("--tags", default="", help="comma-separated tags")
    ap.add_argument("--cover", default="1",
                    help='1-based image index for cover image (default 1); pass "none" to omit')
    ap.add_argument("--draft", action="store_true",
                    help="write to _drafts/<slug>.md instead of _posts/")
    ap.add_argument("--dry-run", action="store_true",
                    help="print result; do not write files")
    ap.add_argument("--keep-trailer", action="store_true",
                    help="do not auto-strip 'Key Points / Future Work / Supervisor' boilerplate")
    args = ap.parse_args()

    # Batch mode: directory input -> process every .docx inside
    if args.docx.is_dir():
        docx_files = sorted(
            p for p in args.docx.glob("*.docx") if not p.name.startswith("~$")
        )
        if not docx_files:
            sys.exit(f"no .docx files found in {args.docx}")
        if args.title or args.slug:
            sys.exit("error: --title and --slug are not supported in batch mode "
                     "(they'd apply to every doc). Run per-file for those.")
        for d in docx_files:
            print(f"\n--- {d.name} ---")
            args.docx = d
            convert_one(args)
        return

    if not args.docx.is_file():
        sys.exit(f"error: not a file or directory: {args.docx}")
    convert_one(args)


def convert_one(args) -> None:
    pandoc = require_pandoc()
    repo = find_repo_root(args.docx if args.docx.is_absolute() else Path.cwd())

    # 1. pandoc -> markdown + extracted media in a temp workdir
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        md = run_pandoc(pandoc, args.docx, work)

        # 2. detect title before we strip it
        detected = detect_title_from_body(md) or args.docx.stem.replace("-", " ").title()
        title = args.title or detected

        # 3. derive slug + date
        slug = slugify(args.slug or Path(args.docx).stem)
        if args.date:
            when = datetime.strptime(args.date, "%Y-%m-%d").replace(
                hour=datetime.now(DEFAULT_TZ).hour,
                minute=datetime.now(DEFAULT_TZ).minute,
                tzinfo=DEFAULT_TZ,
            )
        else:
            when = datetime.now(DEFAULT_TZ)

        # 4. process body
        md = normalize_typography(md)
        md = unindent_blockquoted_images(md)
        md = split_inline_images(md)
        md = strip_leading_title_line(md, title)

        # 4a. strip weekly-status boilerplate (Key Points / Future Work / Supervisor / etc)
        if not args.keep_trailer:
            md, dropped = strip_trailer(md)
            if dropped:
                preview = dropped.splitlines()[0][:80]
                print(f"  stripped trailing section starting with: {preview}")

        dest_media = repo / "assets" / "img" / "blog" / slug
        md, images = rewrite_and_collect_images(md, slug, work, dest_media)

        # 5. cover image
        cover_path: Path | None = None
        cover_alt = title
        if args.cover.lower() != "none" and images:
            try:
                idx = int(args.cover) - 1
                if 0 <= idx < len(images):
                    cover_path = images[idx]
            except ValueError:
                pass

        # 6. assemble
        cats = [c.strip() for c in args.categories.split(",") if c.strip()]
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        front = build_front_matter(title, when, cats, tags, cover_path, cover_alt)
        body = md.strip() + "\n"
        full = front + body

        # 7. write
        if args.draft:
            out = repo / "_drafts" / f"{slug}.md"
        else:
            out = repo / "_posts" / f"{when.strftime('%Y-%m-%d')}-{slug}.md"

        if args.dry_run:
            print("=" * 60)
            print(f"would write: {out}")
            print(f"images copied: {len(images)} -> {dest_media}")
            print("=" * 60)
            print(full)
            return

        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(full, encoding="utf-8")
        print(f"wrote: {out}")
        print(f"images: {len(images)} -> {dest_media}")


if __name__ == "__main__":
    main()
