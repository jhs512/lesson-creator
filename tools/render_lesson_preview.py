#!/usr/bin/env python3
"""Render lesson Markdown to a self-contained local HTML preview.

This deliberately supports the subset emitted by lesson_render.py: headings,
paragraphs, lists, tables, blockquotes, fenced code blocks, and details toggles.
It has no network or third-party package dependency.
"""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path


FENCE_RE = re.compile(r"^\s*```([^`]*)\s*$")
TABLE_DIVIDER_RE = re.compile(r"^\s*\|?(?:\s*:?-+:?\s*\|)+\s*:?-+:?\s*\|?\s*$")


def inline(text: str) -> str:
    placeholders: list[str] = []

    def protect_image(match: re.Match[str]) -> str:
        alt = html.escape(match.group(1), quote=True)
        source = html.escape(match.group(2), quote=True)
        placeholders.append(
            f'<figure><img src="{source}" alt="{alt}" loading="lazy"><figcaption>{alt}</figcaption></figure>'
        )
        return f"\x00{len(placeholders) - 1}\x00"

    def protect_code(match: re.Match[str]) -> str:
        placeholders.append(f"<code>{html.escape(match.group(1))}</code>")
        return f"\x00{len(placeholders) - 1}\x00"

    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", protect_image, text)
    text = re.sub(r"`([^`]+)`", protect_code, text)
    # lesson_render.py escapes brackets for Notion. Restore them before parsing
    # Markdown links so the local preview does not leave stray backslashes.
    text = text.replace(r"\[", "[").replace(r"\]", "]")
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    text = text.replace(r"\_", "_").replace(r"\[", "[").replace(r"\]", "]")
    for index, value in enumerate(placeholders):
        text = text.replace(f"\x00{index}\x00", value)
    return text


def cells(line: str) -> list[str]:
    return [part.strip() for part in line.strip().strip("|").split("|")]


def render(markdown: str, title: str) -> str:
    lines = markdown.splitlines()
    body: list[str] = []
    paragraph: list[str] = []
    list_type: str | None = None
    in_code = False
    code_language = "text"
    code_lines: list[str] = []
    details_depth = 0
    index = 0

    def flush_paragraph() -> None:
        if paragraph:
            body.append(f"<p>{inline(' '.join(paragraph))}</p>")
            paragraph.clear()

    def close_list() -> None:
        nonlocal list_type
        if list_type:
            body.append(f"</{list_type}>")
            list_type = None

    while index < len(lines):
        raw = lines[index]
        line = raw[1:] if details_depth and raw.startswith("\t") else raw
        fence = FENCE_RE.match(line)

        if in_code:
            if fence:
                escaped = html.escape("\n".join(code_lines))
                language_class = re.sub(r"[^a-z0-9_-]+", "-", code_language.lower()).strip("-")
                body.append(
                    f'<pre><code class="language-{html.escape(language_class or "text")}">{escaped}</code></pre>'
                )
                in_code = False
                code_lines.clear()
            else:
                code_lines.append(line)
            index += 1
            continue

        if fence:
            flush_paragraph()
            close_list()
            in_code = True
            code_language = fence.group(1).strip() or "text"
            index += 1
            continue

        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            close_list()
            index += 1
            continue

        standalone_image = re.fullmatch(r"!\[([^\]]*)\]\(([^)]+)\)", stripped)
        if standalone_image:
            flush_paragraph()
            close_list()
            alt = html.escape(standalone_image.group(1), quote=True)
            source = html.escape(standalone_image.group(2), quote=True)
            body.append(
                f'<figure><img src="{source}" alt="{alt}" loading="lazy">'
                f'<figcaption>{alt}</figcaption></figure>'
            )
            index += 1
            continue

        notion_image = re.fullmatch(r'<image\s+src="([^"]+)">(.*?)</image>', stripped)
        if notion_image:
            flush_paragraph()
            close_list()
            source = html.escape(notion_image.group(1), quote=True)
            caption = html.escape(notion_image.group(2).strip(), quote=True)
            body.append(
                f'<figure><img src="{source}" alt="{caption}" loading="lazy">'
                f'<figcaption>{caption}</figcaption></figure>'
            )
            index += 1
            continue

        if stripped == "<details>":
            flush_paragraph()
            close_list()
            body.append("<details>")
            details_depth += 1
            index += 1
            continue
        if stripped == "</details>":
            flush_paragraph()
            close_list()
            body.append("</details>")
            details_depth = max(0, details_depth - 1)
            index += 1
            continue
        summary = re.fullmatch(r"<summary>(.*)</summary>", stripped)
        if summary:
            flush_paragraph()
            close_list()
            body.append(f"<summary>{inline(summary.group(1))}</summary>")
            index += 1
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading:
            flush_paragraph()
            close_list()
            level = len(heading.group(1))
            body.append(f"<h{level}>{inline(heading.group(2))}</h{level}>")
            index += 1
            continue

        if line.lstrip().startswith("> "):
            flush_paragraph()
            close_list()
            body.append(f"<blockquote>{inline(line.lstrip()[2:])}</blockquote>")
            index += 1
            continue

        if stripped.startswith("<table"):
            flush_paragraph()
            close_list()
            header_row = 'header-row="true"' in stripped
            table_source: list[str] = [stripped]
            index += 1
            while index < len(lines):
                table_line = lines[index].strip()
                table_source.append(table_line)
                index += 1
                if table_line == "</table>":
                    break
            rows = re.findall(r"<tr>(.*?)</tr>", "".join(table_source), re.DOTALL)
            body.append('<div class="table-wrap"><table>')
            for row_index, row_source in enumerate(rows):
                row_cells = re.findall(r"<td>(.*?)</td>", row_source, re.DOTALL)
                tag = "th" if header_row and row_index == 0 else "td"
                body.append("<thead><tr>" if tag == "th" else "<tr>")
                body.extend(f"<{tag}>{inline(cell.strip())}</{tag}>" for cell in row_cells)
                body.append("</tr></thead>" if tag == "th" else "</tr>")
            body.append("</table></div>")
            continue

        if (
            "|" in line
            and index + 1 < len(lines)
            and TABLE_DIVIDER_RE.match(lines[index + 1])
        ):
            flush_paragraph()
            close_list()
            headers = cells(line)
            index += 2
            rows: list[list[str]] = []
            while index < len(lines) and "|" in lines[index] and lines[index].strip():
                rows.append(cells(lines[index]))
                index += 1
            body.append("<div class=\"table-wrap\"><table><thead><tr>")
            body.extend(f"<th>{inline(cell)}</th>" for cell in headers)
            body.append("</tr></thead><tbody>")
            for row in rows:
                body.append("<tr>")
                body.extend(f"<td>{inline(cell)}</td>" for cell in row)
                body.append("</tr>")
            body.append("</tbody></table></div>")
            continue

        bullet = re.match(r"^\s*[-*]\s+(.+)$", line)
        numbered = re.match(r"^\s*\d+[.)]\s+(.+)$", line)
        if bullet or numbered:
            flush_paragraph()
            wanted = "ul" if bullet else "ol"
            if list_type != wanted:
                close_list()
                list_type = wanted
                body.append(f"<{wanted}>")
            value = (bullet or numbered).group(1)
            body.append(f"<li>{inline(value)}</li>")
            index += 1
            continue

        close_list()
        paragraph.append(stripped)
        index += 1

    flush_paragraph()
    close_list()
    if in_code:
        raise ValueError("닫히지 않은 코드 펜스가 있다")

    content = "\n".join(body)
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>
:root {{ color-scheme: light dark; --bg:#ffffff; --fg:#242424; --muted:#666; --line:#dedede; --code:#f5f7fa; --accent:#2563eb; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#171717; --fg:#f0f0f0; --muted:#aaa; --line:#414141; --code:#22262b; --accent:#8ab4ff; }} }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--fg); font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Noto Sans KR",sans-serif; font-size:17px; line-height:1.78; }}
main {{ max-width:920px; margin:0 auto; padding:64px 44px 120px; }}
h1 {{ font-size:2.2rem; line-height:1.25; margin:0 0 36px; letter-spacing:-.035em; }}
h2 {{ font-size:1.55rem; line-height:1.35; margin:64px 0 18px; padding-bottom:10px; border-bottom:1px solid var(--line); letter-spacing:-.025em; }}
h3 {{ font-size:1.22rem; margin:38px 0 12px; }}
p {{ margin:12px 0; }}
ul,ol {{ padding-left:1.6rem; margin:12px 0 22px; }}
li {{ margin:5px 0; }}
blockquote {{ margin:20px 0; padding:12px 18px; border-left:4px solid var(--accent); background:color-mix(in srgb,var(--accent) 8%,transparent); }}
code {{ font-family:"SFMono-Regular",Consolas,monospace; font-size:.91em; background:var(--code); padding:.15em .38em; border-radius:5px; }}
pre {{ overflow:auto; margin:20px 0 28px; padding:20px 22px; border:1px solid var(--line); border-radius:10px; background:var(--code); line-height:1.55; tab-size:4; }}
pre code {{ padding:0; background:transparent; white-space:pre; }}
details {{ margin:14px 0 26px; padding:12px 16px; border:1px solid var(--line); border-radius:9px; }}
details details {{ margin-left:8px; }}
summary {{ cursor:pointer; font-weight:700; }}
.table-wrap {{ overflow:auto; margin:20px 0 30px; }}
table {{ width:100%; border-collapse:collapse; }}
th,td {{ padding:10px 12px; border:1px solid var(--line); text-align:left; vertical-align:top; }}
th {{ background:var(--code); }}
a {{ color:var(--accent); }}
figure {{ margin:26px 0 34px; }}
figure img {{ display:block; width:100%; height:auto; border:1px solid var(--line); border-radius:12px; background:#fff; }}
figcaption {{ margin-top:9px; color:var(--muted); font-size:.9rem; line-height:1.55; text-align:center; }}
@media (max-width:650px) {{ main {{ padding:34px 20px 80px; }} body {{ font-size:16px; }} }}
</style>
</head>
<body><main>
{content}
</main></body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--title", help="문서에 H1이 없을 때 사용할 제목")
    args = parser.parse_args()
    source = args.source.read_text(encoding="utf-8")
    # 문서 첫 줄의 H1만 제목으로 인정한다. 코드 안의 `# 수정 시작` 같은
    # 주석을 제목으로 오인하면 로컬 미리보기의 제목과 H1이 사라진다.
    title_match = re.match(r"^\ufeff?#\s+([^\r\n]+)", source)
    title = title_match.group(1) if title_match else (args.title or args.source.stem)
    if not title_match and args.title:
        source = f"# {args.title}\n\n{source}"
    rendered = render(source, title)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
