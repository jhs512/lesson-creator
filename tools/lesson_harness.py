# -*- coding: utf-8 -*-
"""lesson_harness.py — 스키마 JSON의 코드·출력 및 용어 첫 사용 검증 (4단계).

사용법:
    python3 tools/lesson_harness.py <page.json>

대상: kind=code, lang=python, intent=normal, verified=measured 인 요소와
     challenge의 answer(+goal_output). 예측형 과제는 정답 토글의 plain text 블록을
     본문 코드의 기대 출력으로 삼아 자동 대조한다(정답 출력을 손으로 적고 끝나는 구멍 차단). 임시 폴더에 page.fixtures의 파일을
     만들어 놓고 블록을 실행해 stdout을 output/goal_output과 대조한다.

건너뛰는 것(사유 출력): verified=example(LLM·네트워크·Windows 등 재현 불가 환경),
intent가 normal이 아닌 블록, python이 아닌 블록(command 등).
승인 게이트 input() 이 있는 블록은 자동 y 입력으로 진행한다.

page.learning_terms가 있으면 lesson_term_flow.check_page도 실행한다.
선언한 용어의 설명이 첫 사용보다 늦거나, 이미지의 text_content(실제
레이블 목록)가 빠지면 FAIL이다. 메타데이터 없는 기존 페이지는 이 검사를
SKIP한다. 용어 목록의 완전성·설명의 이해 가능성은 별도 저지에서 검수한다.
선언 형식과 판정 단위는 lesson_term_flow.py 및 lesson_schema.py를 참조한다.

supplement의 코드도 같은 방식으로 실행한다. lesson_structure는 보충을
닫은 필수 본문의 용어 설명을 검사하고, 목차·중복 문단·보충 위치에 관한
REVIEW를 출력한다. REVIEW는 읽기 검수할 위치이며 실패나 분량 축소 명령이 아니다.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def norm(s):
    return "\n".join(l.rstrip() for l in (s or "").strip().splitlines())


def iter_code_targets(page):
    """(경로, code요소, 기대출력) 나열."""
    def walk_el(path, el):
        if el.get("kind") == "task":
            t = el
            if t.get("element"):
                tel = t["element"]
                ans_el = (t.get("answer") or {}).get("element") or {}
                # 예측형 과제 — 정답 토글의 plain text 출력이 곧 본문 코드의 기대 출력이다
                if (tel.get("kind") == "code" and tel.get("output") is None
                        and tel.get("verified") != "example"
                        and ans_el.get("kind") == "code"
                        and ans_el.get("lang") in ("text", "plain text")):
                    tel = dict(tel)
                    tel["output"] = ans_el["src"]
                    tel.setdefault("verified", "measured")
                yield from walk_el(path + ".element", tel)
            for i, s in enumerate(t.get("setup_elements", [])):
                yield from walk_el(f"{path}.setup[{i}]", s)
            ans = t.get("answer")
            if ans and ans.get("element"):
                expected = t.get("goal_output") if t.get("task_type") == "challenge" else \
                    ans["element"].get("output")
                el2 = dict(ans["element"])
                if expected is not None and el2.get("output") is None:
                    el2["output"] = expected
                    el2.setdefault("verified", "measured")
                yield from walk_el(path + ".answer", el2)
        elif el.get("kind") == "code":
            yield path, el
        elif el.get("kind") == "supplement":
            for i, child in enumerate(el.get("body", [])):
                yield from walk_el(f"{path}.body[{i}]", child)
    for si, sec in enumerate(page.get("sections", [])):
        for bi, el in enumerate(sec.get("body", [])):
            yield from walk_el(f"sections[{si}].body[{bi}]", el)
    for xi, x in enumerate(page.get("extra_tasks", []) + ([page["hard_problem"]] if page.get("hard_problem") else [])):
        if x.get("element"):
            yield from walk_el(f"extra[{xi}].element", x["element"])
        if x.get("answer"):
            el2 = dict(x["answer"]["element"])
            if x.get("goal_output") and el2.get("output") is None:
                el2["output"] = x["goal_output"]
                el2.setdefault("verified", "measured")
            yield from walk_el(f"extra[{xi}].answer", el2)


def run_page(page):
    passed, failed, skipped = [], [], []
    from lesson_term_flow import check_page
    term_passed, term_failed, term_skipped = check_page(page)
    passed.extend(term_passed)
    failed.extend(term_failed)
    skipped.extend(term_skipped)
    from lesson_structure import check_structure
    structure_passed, structure_failed, _ = check_structure(page)
    passed.extend(structure_passed)
    failed.extend(structure_failed)
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        for name, content in page.get("fixtures", {}).items():
            (tmpdir / name).parent.mkdir(parents=True, exist_ok=True)
            (tmpdir / name).write_text(content, encoding="utf-8")
        for path, el in iter_code_targets(page):
            if el.get("lang", "python") != "python":
                skipped.append((path, "python 아님"))
                continue
            if el.get("intent", "normal") != "normal":
                skipped.append((path, f"intent={el.get('intent')}"))
                continue
            if el.get("output") is None:
                skipped.append((path, "기대 출력 없음"))
                continue
            if el.get("verified") != "measured":
                skipped.append((path, "verified=example (재현 불가 환경)"))
                continue
            src = el["src"]
            try:
                r = subprocess.run([sys.executable, "-c", src], cwd=tmpdir,
                                   capture_output=True, text=True, timeout=30,
                                   input="y\n" * 10)
            except subprocess.TimeoutExpired:
                failed.append((path, "실행 30초 초과"))
                continue
            got = norm(r.stdout + (("\n" + r.stderr.strip()) if r.returncode != 0 else ""))
            want = norm(el["output"])
            if got == want:
                passed.append(path)
            else:
                failed.append((path, f"출력 불일치\n  기대: {want[:200]!r}\n  실제: {got[:200]!r}"))
    return passed, failed, skipped


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    with open(sys.argv[1], encoding="utf-8") as f:
        page = json.load(f)
    passed, failed, skipped = run_page(page)
    for p in passed:
        print(f"PASS  {p}")
    for p, why in skipped:
        print(f"SKIP  {p} — {why}")
    for p, why in failed:
        print(f"FAIL  {p} — {why}")
    from lesson_structure import check_structure
    _, _, review = check_structure(page)
    for p, why in review:
        print(f"REVIEW  {p} — {why}")
    print(f"\n요약: PASS {len(passed)} / FAIL {len(failed)} / SKIP {len(skipped)} / REVIEW {len(review)}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
