import re

CITATION_RE = re.compile(r"^\[[\d,\s]+\]$")
INLINE_SPLIT_RE = re.compile(r"(\*\*.+?\*\*|\[[\d,\s]+\])")
TABLE_SEPARATOR_RE = re.compile(r"^\|[\s\-:|]+\|$")


def parse_inline(text: str) -> list[tuple[str, bool, bool]]:
    """
    Splits a line into (text, is_bold, is_citation) runs. Citations (e.g. "[1, 2]")
    are flagged so renderers can show them as small superscript badges.
    """
    runs = []
    for part in INLINE_SPLIT_RE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            runs.append((part[2:-2], True, False))
        elif CITATION_RE.match(part):
            runs.append((part, False, True))
        else:
            runs.append((part, False, False))
    return runs


def parse_markdown(markdown: str) -> list[dict]:
    """
    Parses a subset of Markdown into block dicts:
      {"type": "h1"|"h2"|"h3", "text": str}
      {"type": "bullet"|"numbered"|"p", "runs": [(text, bold, citation), ...]}
      {"type": "table", "rows": [[cell_text, ...], ...]}  (first row is header)
    """
    blocks = []
    lines = markdown.split("\n")
    i, n = 0, len(lines)
    while i < n:
        line = lines[i].rstrip()
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if stripped.startswith("### "):
            blocks.append({"type": "h3", "text": stripped[4:].strip()})
            i += 1
            continue
        if stripped.startswith("## "):
            blocks.append({"type": "h2", "text": stripped[3:].strip()})
            i += 1
            continue
        if stripped.startswith("# "):
            blocks.append({"type": "h1", "text": stripped[2:].strip()})
            i += 1
            continue

        if stripped.startswith("|"):
            table_lines = []
            while i < n and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            rows = []
            for tl in table_lines:
                if TABLE_SEPARATOR_RE.match(tl):
                    continue
                cells = [c.strip() for c in tl.strip("|").split("|")]
                rows.append(cells)
            if rows:
                blocks.append({"type": "table", "rows": rows})
            continue

        if stripped[:2] in ("- ", "* ") or stripped[:2] == "-\t":
            blocks.append({"type": "bullet", "runs": parse_inline(stripped[2:].strip())})
            i += 1
            continue

        m = re.match(r"^(\d+)\.\s+(.*)", stripped)
        if m:
            blocks.append({"type": "numbered", "runs": parse_inline(m.group(2))})
            i += 1
            continue

        blocks.append({"type": "p", "runs": parse_inline(stripped)})
        i += 1

    return blocks
