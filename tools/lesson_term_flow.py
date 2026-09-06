# -*- coding: utf-8 -*-
"""Check declared learning terms against the order students actually read.

Usage: python3 tools/lesson_term_flow.py page.json

Opt in with page.learning_terms = [{"term": "인트라넷 서버",
"aliases": ["IntranetServer"], "introduced_by": "조직 안에서 사용하는 웹 화면을 제공한다."}].
The exact introduced_by substring must occur in a visible prose unit before, or
in the same unit as, the first use of the term or an alias. A paragraph,
definition, table row, or individual GUI step is one unit. Titles, TOC entries,
and section headings are roadmaps and do not count; task instructions do count.
Code, commands, image labels and captions count as uses, never as introductions.
Blank-line paragraphs are separate even inside one preview.intro string. Korean
prefix boundaries keep 로그 separate from 프로그램; Korean particles still count.
For overlapping English labels, a longer declared phrase owns its full span:
Domain Name System does not separately use the shorter label domain name.
Image.text_content must contain the visible labels extracted from the source
SVG (or transcribed and visually checked for a screenshot). It is inspection
metadata, not an additional caption. No OCR or invented keyword list is used.

This gate checks the declared inventory only. It cannot prove that the inventory
is complete or that an explanation is understandable. The human buildup review
must still check definitions, prerequisites and omitted terms. In particular,
declarations do not excuse an explanation that itself uses unknown vocabulary.
Legacy pages without learning_terms receive a SKIP, not a terminology PASS.
"""
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree


@dataclass(frozen=True)
class VisibleUnit:
    path: str
    text: str
    prose: bool = True
    image: bool = False


def svg_text_content(path):
    """Extract actual SVG <text> labels, in source order, for image metadata.

    An SVG using outlined text has no extractable labels and needs a checked
    transcription. This helper deliberately does not infer labels from a name.
    """
    root = ElementTree.parse(Path(path)).getroot()
    labels = ["".join(node.itertext()).strip() for node in root.iter()
              if node.tag.rsplit("}", 1)[-1] == "text"]
    return "\n".join(label for label in labels if label)


def _visible_units(page):
    """Yield visible content in lesson_render.render order, before escaping.

    Keep walkthrough/extra-answer behavior aligned with lesson_render: hidden
    source fields must not silently provide an introduction for visible uses.
    """
    def unit(path, value, prose=True, image=False):
        return VisibleUnit(path, value if isinstance(value, str) else "", prose, image)

    def output(el, path):
        if el.get("output") is not None:
            if el.get("output_label"):
                yield unit(path + ".output_label", el["output_label"])
            yield unit(path + ".output", el["output"], False)

    def answer(ans, path):
        if ans.get("hint"):
            yield unit(path + ".hint", ans["hint"])
        if ans.get("element"):
            yield from element(ans["element"], path + ".element")
        if ans.get("explain"):
            yield unit(path + ".explain", ans["explain"])

    def task(t, path):
        is_challenge = t.get("task_type") == "challenge"
        instruction = t.get("instruction", "")
        if is_challenge and not page.get("walkthrough") and t.get("title"):
            instruction = t["title"] + " — " + instruction
        yield unit(path + ".instruction", instruction)
        if is_challenge and not page.get("walkthrough"):
            for i, text in enumerate(t.get("requirements", [])):
                yield unit(f"{path}.requirements[{i}]", text)
        for i, el in enumerate(t.get("setup_elements", [])):
            yield from element(el, f"{path}.setup_elements[{i}]")
        if page.get("walkthrough") and is_challenge:
            ans = t.get("answer") or {}
            if ans.get("element"):
                yield from element(ans["element"], path + ".answer.element")
            elif t.get("element"):
                yield from element(t["element"], path + ".element")
            if t.get("goal_output"):
                yield unit(path + ".goal_output", t["goal_output"], False)
            if ans.get("explain"):
                yield unit(path + ".answer.explain", ans["explain"])
            return
        if t.get("element"):
            if is_challenge and not page.get("walkthrough") and t["element"].get("kind") == "code" and t.get("start_label"):
                yield unit(path + ".start_label", t["start_label"])
            yield from element(t["element"], path + ".element")
        if is_challenge:
            if t.get("goal_label"):
                yield unit(path + ".goal_label", t["goal_label"])
            yield unit(path + ".goal_output", t.get("goal_output", ""), False)
            if t.get("after_goal"):
                yield unit(path + ".after_goal", t["after_goal"])
        elif t.get("task_type") == "experiment":
            for i, obs in enumerate(t.get("observe", [])):
                yield unit(f"{path}.observe[{i}]",
                           obs.get("point", "") + " — " + obs.get("expected", ""))
        if not page.get("walkthrough") and t.get("answer"):
            yield from answer(t["answer"], path + ".answer")

    def element(el, path):
        kind = el.get("kind")
        if kind == "paragraph":
            yield unit(path + ".text", el.get("text", ""))
        elif kind == "supplement":
            # Supplement titles are roadmaps, like section headings.
            for i, child in enumerate(el.get("body", [])):
                yield from element(child, f"{path}.body[{i}]")
        elif kind == "definition":
            en = "(" + el["en"] + ")" if el.get("en") else ""
            yield unit(path, el.get("term", "") + en + " — " + el.get("text", ""))
        elif kind == "bullets":
            if el.get("intro"):
                yield unit(path + ".intro", el["intro"])
            for i, text in enumerate(el.get("items", [])):
                yield unit(f"{path}.items[{i}]", text)
        elif kind in ("code", "command"):
            yield unit(path + ".src", el.get("src", ""), False)
            yield from output(el, path)
        elif kind == "tool_steps":
            yield unit(path + ".tool", el.get("tool", ""))
            for i, text in enumerate(el.get("steps", [])):
                yield unit(f"{path}.steps[{i}]", text)
            if el.get("note"):
                yield unit(path + ".note", el["note"])
        elif kind == "image":
            yield unit(path + ".text_content", el.get("text_content", ""), False, True)
            if el.get("caption"):
                yield unit(path + ".caption", el["caption"], False)
        elif kind == "table":
            yield unit(path + ".headers", " | ".join(el.get("headers", [])))
            for i, row in enumerate(el.get("rows", [])):
                yield unit(f"{path}.rows[{i}]", " | ".join(row))
        elif kind == "task":
            yield from task(el, path)

    def extra(x, path):
        yield unit(path + ".text", x.get("title", "") + " — " + x.get("text", ""))
        if x.get("element"):
            yield from element(x["element"], path + ".element")
        if x.get("goal_output"):
            yield unit(path + ".goal_output", x["goal_output"], False)
        ans = x.get("answer") or {}
        if ans.get("hint"):
            yield unit(path + ".answer.hint", ans["hint"])
        if ans.get("element"):
            # render_extra shows answer source only, not its output/explain.
            yield unit(path + ".answer.element.src", ans["element"].get("src", ""), False)

    if page.get("type") == "material":
        yield unit("intro", page.get("intro", ""))
        for i, item in enumerate(page.get("files", [])):
            if item.get("note"):
                yield unit(f"files[{i}].note", item["note"])
            yield unit(f"files[{i}].content", item.get("content", ""), False)
        return
    yield unit("lead", page.get("lead", ""))
    pv = page.get("preview") or {}
    if pv:
        if pv.get("intro"):
            yield unit("preview.intro", pv["intro"])
        if pv.get("element"):
            yield from element(pv["element"], "preview.element")
    if page.get("principle"):
        yield unit("principle", page["principle"])
    for si, section in enumerate(page.get("sections", [])):
        for bi, el in enumerate(section.get("body", [])):
            yield from element(el, f"sections[{si}].body[{bi}]")
    if page.get("closing"):
        yield unit("closing", page["closing"])
    if page.get("walkthrough"):
        return
    for i, x in enumerate(page.get("extra_tasks", [])):
        yield from extra(x, f"extra_tasks[{i}]")
    if page.get("hard_problem"):
        yield from extra(page["hard_problem"], "hard_problem")
    for i, text in enumerate(page.get("review", [])):
        yield unit(f"review[{i}]", text)


def visible_units(page):
    """Split blank-line prose paragraphs while retaining render order and paths."""
    for item in _visible_units(page):
        paragraphs = re.split(r"\n\s*\n", item.text) if item.prose else [item.text]
        if len(paragraphs) == 1:
            yield item
        else:
            for i, paragraph in enumerate(paragraphs):
                yield VisibleUnit(f"{item.path}.paragraph[{i}]", paragraph, True)


def metadata_errors(page):
    """Validate optional declarations without running code or evaluating prose."""
    if "learning_terms" not in page:
        return []
    terms = page["learning_terms"]
    if not isinstance(terms, list) or not terms:
        return ["learning_terms: 활성화하려면 용어 선언을 1개 이상 담은 리스트가 필요하다"]
    errors = []
    for i, decl in enumerate(terms):
        path = f"learning_terms[{i}]"
        if not isinstance(decl, dict):
            errors.append(path + ": term·aliases·introduced_by를 가진 객체여야 한다")
            continue
        for key in ("term", "introduced_by"):
            if not isinstance(decl.get(key), str) or not decl[key].strip():
                errors.append(f"{path}.{key}: 비어 있지 않은 문자열 필수")
        aliases = decl.get("aliases", [])
        if not isinstance(aliases, list) or any(not isinstance(a, str) or not a.strip() for a in aliases):
            errors.append(path + ".aliases: 비어 있지 않은 문자열 리스트여야 한다")
    return errors


def _term_pattern(names):
    alternatives = []
    for name in sorted(set(names), key=len, reverse=True):
        # ASCII boundaries allow Korean particles (DNS가), while keeping DNS
        # separate from DNSServer and IP separate from ipconfig.
        if re.match(r"[A-Za-z0-9_]", name[0]):
            left = r"(?<![A-Za-z0-9_])"
        elif re.match(r"[가-힣]", name[0]):
            # Korean particles follow a noun, but an earlier syllable may be
            # part of a different word: 로그 must not match inside 프로그램.
            left = r"(?<![가-힣A-Za-z0-9_])"
        else:
            left = ""
        right = r"(?![A-Za-z0-9_])" if re.match(r"[A-Za-z0-9_]", name[-1]) else ""
        alternatives.append(left + re.escape(name) + right)
    return re.compile("|".join(alternatives), re.IGNORECASE)


def _first_uses(units, declarations):
    """Find uses without treating part of another English label as a new label.

    Domain Name in the declared expansion Domain Name System is not an
    independent mention of the domain-name concept. Prefer the longest declared
    English phrase for overlapping spans. Korean definitions still retain their
    ordinary dependency checks (e.g. an explanation using 서버 before its intro).
    """
    patterns = [_term_pattern([decl["term"]] + decl.get("aliases", [])) for decl in declarations]
    first = [None] * len(declarations)
    for n, item in enumerate(units):
        matches = [(i, match) for i, pattern in enumerate(patterns) for match in pattern.finditer(item.text)]
        for i, match in matches:
            if first[i] is not None:
                continue
            english = re.fullmatch(r"[A-Za-z][A-Za-z -]*", match.group()) is not None
            shadowed = english and any(
                other_i != i and other.start() <= match.start() and other.end() >= match.end()
                and other.end() - other.start() > match.end() - match.start()
                and re.fullmatch(r"[A-Za-z][A-Za-z -]* [A-Za-z-]+", other.group())
                for other_i, other in matches
            )
            if not shadowed:
                first[i] = n
    return first


def check_page(page):
    """Return (passed paths, failed (path, reason), skipped (path, reason))."""
    if "learning_terms" not in page:
        return [], [], [("term_flow", "learning_terms 미선언 — 용어 순서는 검사하지 않음")]
    errors = metadata_errors(page)
    if errors:
        return [], [("term_flow", error) for error in errors], []
    units = list(visible_units(page))
    first_uses = _first_uses(units, page["learning_terms"])
    passed, failed = [], []
    for item in units:
        if item.image and not item.text.strip():
            failed.append((item.path, "용어 검사 활성 페이지의 이미지에 text_content 레이블 목록이 없음"))
    for i, decl in enumerate(page["learning_terms"]):
        label = f"learning_terms[{i}] ({decl['term']})"
        first = first_uses[i]
        intro = next((n for n, item in enumerate(units)
                      if item.prose and decl["introduced_by"] in item.text), None)
        if intro is None:
            failed.append((label, "introduced_by 설명이 보이는 산문에 없음"))
        elif first is None:
            failed.append((label, "선언한 용어·별칭이 보이는 콘텐츠에 없음 — 선언과 본문을 맞출 것"))
        elif first < intro:
            failed.append((label, f"설명 전 사용: {units[first].path} → 설명: {units[intro].path}"))
        else:
            passed.append(label)
    return passed, failed, []


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    page = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    passed, failed, skipped = check_page(page)
    for path in passed:
        print(f"PASS  {path}")
    for path, why in skipped:
        print(f"SKIP  {path} — {why}")
    for path, why in failed:
        print(f"FAIL  {path} — {why}")
    print(f"\n용어 순서: PASS {len(passed)} / FAIL {len(failed)} / SKIP {len(skipped)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
