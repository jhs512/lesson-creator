"""Review observable reading structure without scoring prose quality.

FAIL: a registered term used in required content is explained only in an
optional supplement. REVIEW: stale/out-of-order TOC entries, repeated long
prose, or a supplement before the section's basic explanation. Repeated
exercise setup and answers are deliberately excluded from duplicate review.
Topic continuity, paraphrased repetition and explanation depth need the judge.
"""
import copy
import re

from lesson_term_flow import _first_uses, check_page, metadata_errors, visible_units


def check_structure(page):
    """Return (passed paths, failures, review notes); notes never fail a build."""
    if page.get("type") == "material":
        return [], [], []
    passed, failed, review = [], [], []
    sections = page.get("sections", [])
    headings = [section.get("heading", "") for section in sections]
    cursor = 0
    for i, heading in enumerate(page.get("toc", [])):
        try:
            cursor = headings.index(heading, cursor) + 1
        except ValueError:
            review.append((f"toc[{i}]", f"목차 제목이 본문에 없거나 순서가 다름: {heading}"))
    if page.get("toc") and not review:
        passed.append("structure.toc")

    seen = {}

    def inspect_prose(text, path):
        if re.search(r"[①-⑳].*[①-⑳]", text):
            review.append((path, "문장 안에 순서 번호가 나열됨 — numbered_list로 항목을 나눌지 검수"))
        if (re.search(r"구름|번개|지그재그|봉투\s*모양|아이콘\s*모양", text)
                and re.search(r"표시|기호|뜻|의미|나타내", text)):
            review.append((path, "그림 기호 자체의 설명이 있음 — 눈으로 알 수 있는 묘사인지, 기술 이해에 필요한 설명인지 검수"))
        for index, paragraph in enumerate(re.split(r"\n\s*\n", text)):
            normalized = re.sub(r"\s+", " ", paragraph.replace("`", "")).strip()
            # Short transitions often repeat usefully. This is a locator for
            # review, never a demand to reduce the number of characters.
            if len(normalized) < 80:
                continue
            location = f"{path}.paragraph[{index}]"
            if normalized in seen:
                review.append((location, f"같은 설명이 반복됨: {seen[normalized]} — 합치거나 반복 목적을 검수"))
            else:
                seen[normalized] = location

    inspect_prose(page.get("lead", ""), "lead")
    inspect_prose((page.get("preview") or {}).get("intro", ""), "preview.intro")
    has_supplement = False
    for si, section in enumerate(sections):
        has_basic = False
        for bi, el in enumerate(section.get("body", [])):
            path = f"sections[{si}].body[{bi}]"
            kind = el.get("kind")
            if page.get("lesson_role") == "concept" and kind in ("command", "tool_steps"):
                review.append((path, "개념 교시에 실행·조작 절차가 있음 — 설명용 사례인지 실습 교시로 옮길 활동인지 검수"))
            if kind in ("paragraph", "definition"):
                inspect_prose(el.get("text", ""), path)
                has_basic = True
            elif kind == "supplement":
                has_supplement = True
                if not has_basic:
                    review.append((path, "보충이 기본 설명보다 먼저 나옴 — 관련 개념 뒤로 옮길지 검수"))
                for i, child in enumerate(el.get("body", [])):
                    if child.get("kind") in ("paragraph", "definition"):
                        inspect_prose(child.get("text", ""), f"{path}.body[{i}]")

    if has_supplement and page.get("learning_terms") and not metadata_errors(page):
        core = copy.deepcopy(page)

        def strip_supplements(value):
            if isinstance(value, dict):
                return {key: strip_supplements(item) for key, item in value.items()}
            if isinstance(value, list):
                return [strip_supplements(item) for item in value
                        if not (isinstance(item, dict) and item.get("kind") == "supplement")]
            return value

        core = strip_supplements(core)
        # Extra activities are optional too; they may build on a supplement.
        core['extra_tasks'] = []
        core.pop('hard_problem', None)
        terms = page["learning_terms"]
        uses = _first_uses(list(visible_units(core)), terms)
        core["learning_terms"] = [term for term, use in zip(terms, uses) if use is not None]
        if core["learning_terms"]:
            _, core_failed, _ = check_page(core)
            if core_failed:
                failed.extend(("structure.core_terms", f"보충을 닫은 본문: {path} — {why}")
                              for path, why in core_failed)
            else:
                passed.append("structure.core_terms")
    return passed, failed, review
