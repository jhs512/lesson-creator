# -*- coding: utf-8 -*-
"""lesson_schema.py — ALEPH 교안 페이지 스키마 검증기 (3단계).

페이지를 구조화된 JSON으로 작성하면 이 모듈이 구조를 검증한다.
구조 위반(정답 누락, 마커 짝, 과제 수, 되새김 수)이 표현 자체로 불가능해지는 게 목표.
표준 라이브러리만 사용한다.

파이썬 과정 전용이 아니다 — 네트워크·서버 교시를 위해 code 외에
command(터미널/cmd 명령), tool_steps(GUI 도구 절차), image(도식), bullets를
1급 요소로 지원하고, 모든 출력에 verified(measured|example)를 강제한다.

── 스키마 v1 ──

Page (type: "lesson" | "material")
  lesson:
    title: "N교시. …"
    lesson_role?: "concept"|"guided_practice"|"integrated_practice"
                                          # 생략하면 기존 실습 교시 규칙 유지
    lead: str                              # 리드 한 줄
    toc: [str]  (3~6개)
    preview: {intro?: str, element: Element}?   # 미리보기 (intro 생략 시 표준 문구)
    principle?: str                        # 미리보기 뒤 한 줄 원칙
    sections: [Section]                    # 과제는 섹션 body 안 task 요소
    extra_tasks?: [ExtraTask] (기존 역할 미지정 교시는 1개 이상)    # "추가 과제 — 빨리 끝났다면" 토글
    hard_problem?: ExtraTask               # "도전 문제" 토글 (2과목 규격)
    closing?: str                          # 다음 시간 예고 한 줄
    review: [str] (정확히 3개)
    fixtures?: {filename: content}         # 하니스가 실행 전 만들어 줄 파일들
    learning_terms?: [{term: str, aliases?: [str], introduced_by: str}]
                                          # 용어 첫 사용 게이트, 선언 시 1개 이상
                                          # introduced_by: 보이는 설명의 정확한 부분 문자열
  material:
    title, intro: str
    files: [{filename, lang, content, note?}]   # 데이터만 — 다른 요소 표현 불가

Section: {heading: str, importance: ""|"✅"|"❗", body: [Element]}

Element (kind로 구분):
  paragraph   {text}
  supplement  {title, body: [Element]}                # 기본 설명 뒤의 선택 보충. 중첩·과제는 불가
  definition  {term, en?, text}                       # > **term(en)** — text
  bullets     {items: [str], intro?: str}
  numbered_list {items: [str], intro?: str}           # 순서를 한 항목씩 표시하는 실제 번호 목록
  code        {lang, src, output?, output_label?,
               intent: "normal"|"preview"|"reinterpret"|"intentional_error"|"continuation",
               verified: "measured"|"example",        # output이 있으면 필수
               needs?: [filename]}                    # fixtures 중 실행에 필요한 파일
  command     {shell: "cmd"|"powershell"|"terminal", src, output?, output_label?,
               verified: "measured"|"example"}        # 네트워크·서버 교시용
  tool_steps  {tool: str, steps: [str], note?: str}   # GUI 도구 절차 (Wireshark 등)
  image       {src, caption?, text_content?: str, image_kind?, capture?}     # file-upload://… 도식
                                                      # text_content는 실제 그림의 레이블
                                                      # image_kind: concept_diagram|configuration_diagram|screenshot
                                                      # screenshot의 capture: {application, version, scenario, evidence}
  table       {headers: [str], rows: [[str]]}
  task        {task_type: "predict"|"experiment"|"action"|"challenge",
               instruction: str,
               element?: Element(code|command|tool_steps),
               observe?: [{point, expected}],         # experiment면 필수, expected 필수
               requirements?: [str],                  # challenge용
               setup_elements?: [Element],            # challenge 준비물(설정 파일 등)
               start_label?: str, answer_label?: str, # challenge 시작 틀·도움말 토글 안내
               goal_output?: str, goal_label?: str,   # challenge면 goal_output 필수
               answer?: {element: Element, hint?: str, explain?: str},
               no_answer_reason?: str}                # predict인데 정답 토글이 없으면 사유 필수

ExtraTask: {title, text, element?: Element, goal_output?, answer?: {element, hint?}}

번호는 렌더러가 자동 부여한다(과제 번호 밀림 원천 제거).

learning_terms는 학생용 출력에 넣지 않는 검수 메타데이터이다. 하니스는
lead → preview → principle → 본문(표·명령·UI·그림 포함) → 과제/정답 → 마무리를
실제 렌더 순서로 검사한다. 문단·정의·표 한 행·UI 한 단계 안의 첫 용어와 설명은
동시 소개로 인정한다. 제목·목차·절 제목은 예고이므로 제외한다. 선언한 설명이
없거나 첫 사용 뒤에 나오면 FAIL이다. 명령·코드·그림 레이블·캡션은 사용으로
세지만 설명으로 인정하지 않는다. 다른 선언 용어가 설명 속에서 먼저 등장해도
동일한 순서 검사를 받는다. 이 검사는 용어 목록의 완전성이나 난이도를 증명하지
않는다. 판단형 빌드업 검수는 별도로 수행한다.

learning_terms 활성 페이지의 모든 표시 image에는 text_content가 필수이다.
수정 가능한 SVG라면 lesson_term_flow.svg_text_content(local_svg_path)로 실제
<text>를 추출한다. 스크린샷·윤곽선 글자는 보이는 문자를 옮긴 뒤 그림과 대조한다.
파일명에서 추측한 목록이나 일부 용어만 적은 목록으로 대신하지 않는다.
text_content는 화면에 중복 출력하지 않으며 이미지의 표시 순서에서 검사한다.
"""
import ast
import json
import re
import sys

INTENTS = {"normal", "preview", "reinterpret", "intentional_error", "continuation"}
SHELLS = {"cmd", "powershell", "terminal"}
TASK_TYPES = {"predict", "experiment", "action", "challenge"}
ELEMENT_KINDS = {"paragraph", "definition", "bullets", "code", "command",
                 "tool_steps", "image", "table", "task", "supplement", "numbered_list"}
LESSON_ROLES = {"concept", "guided_practice", "integrated_practice"}

MARK_START = "<<<<<<<<<<<< 수정 시작 <<<<<<<<<<<<"
MARK_END = ">>>>>>>>>>>> 수정 끝 >>>>>>>>>>>>"


def _err(errors, path, msg):
    errors.append(f"{path}: {msg}")


def _check_markers(errors, path, src):
    s, e = src.count("수정 시작"), src.count("수정 끝")
    if s != e:
        _err(errors, path, f"수정 시작({s})/수정 끝({e}) 짝 불일치")


def _check_python(errors, path, src, intent):
    try:
        ast.parse(src)
    except SyntaxError as ex:
        if intent != "intentional_error":
            _err(errors, path, f"python 문법 오류 L{ex.lineno}: {ex.msg} (의도된 고장이면 intent=intentional_error)")
        return
    if intent == "intentional_error":
        _err(errors, path, "intent=intentional_error인데 문법 오류가 없다 — 실제로 고장난 코드인지 확인")


def _validate_element(errors, path, el, allow_task=True):
    kind = el.get("kind")
    if kind not in ELEMENT_KINDS:
        _err(errors, path, f"알 수 없는 kind '{kind}'")
        return
    if kind == "task" and not allow_task:
        _err(errors, path, "이 위치에는 task를 둘 수 없다")
        return
    if kind == "paragraph":
        if not el.get("text", "").strip():
            _err(errors, path, "paragraph.text 비어 있음")
    elif kind == "supplement":
        if not isinstance(el.get("title"), str) or not el["title"].strip():
            _err(errors, path, "supplement.title 필수")
        body = el.get("body")
        if not isinstance(body, list) or not body:
            _err(errors, path, "supplement.body는 비어 있지 않은 요소 목록이어야 한다")
        else:
            for i, child in enumerate(body):
                if child.get("kind") in ("supplement", "task"):
                    _err(errors, f"{path}.body[{i}]", "보충 안에 보충이나 필수 과제를 넣지 않는다")
                else:
                    _validate_element(errors, f"{path}.body[{i}]", child, allow_task=False)
    elif kind == "definition":
        if not el.get("term") or not el.get("text"):
            _err(errors, path, "definition은 term·text 필수")
    elif kind in ("bullets", "numbered_list"):
        if not el.get("items"):
            _err(errors, path, "bullets.items 비어 있음")
    elif kind == "code":
        src = el.get("src", "")
        if not src.strip():
            _err(errors, path, "code.src 비어 있음")
        lang = el.get("lang", "python")
        intent = el.get("intent", "normal")
        if intent not in INTENTS:
            _err(errors, path, f"intent '{intent}' 미지원")
        if el.get("output") is not None and el.get("verified") not in ("measured", "example"):
            _err(errors, path, "output이 있으면 verified(measured|example) 필수")
        if el.get("verified") == "example" and el.get("output") is not None and not el.get("output_label"):
            _err(errors, path, "verified=example이면 output_label(예시임을 알리는 문구) 필수")
        _check_markers(errors, path, src)
        if lang == "python" and intent in ("normal", "intentional_error"):
            _check_python(errors, path, src, intent)
    elif kind == "command":
        if el.get("shell") not in SHELLS:
            _err(errors, path, f"command.shell은 {sorted(SHELLS)} 중 하나")
        if not el.get("src", "").strip():
            _err(errors, path, "command.src 비어 있음")
        if el.get("output") is not None and el.get("verified") not in ("measured", "example"):
            _err(errors, path, "output이 있으면 verified(measured|example) 필수")
        if el.get("verified") == "example" and el.get("output") is not None and not el.get("output_label"):
            _err(errors, path, "verified=example이면 output_label 필수 (예: '출력 예시 — Windows 기준, 값은 환경마다 다르다')")
    elif kind == "tool_steps":
        if not el.get("tool") or not el.get("steps"):
            _err(errors, path, "tool_steps는 tool·steps 필수")
    elif kind == "image":
        if not el.get("src"):
            _err(errors, path, "image.src 필수 (file-upload://…)")
        if "text_content" in el and (not isinstance(el["text_content"], str) or not el["text_content"].strip()):
            _err(errors, path, "image.text_content는 실제 레이블을 담은 비어 있지 않은 문자열이어야 한다")
        if el.get("image_kind") not in (None, "concept_diagram", "configuration_diagram", "screenshot"):
            _err(errors, path, "image_kind는 concept_diagram|configuration_diagram|screenshot 중 하나")
        if el.get("image_kind") == "screenshot":
            capture = el.get("capture", {})
            if not isinstance(capture, dict) or any(not capture.get(k) for k in ("application", "version", "scenario", "evidence")):
                _err(errors, path, "실측 화면에는 capture.application·version·scenario·evidence가 필요하다 — 메타데이터만으로 실측 진위를 보장하지는 않는다")
    elif kind == "table":
        headers, rows = el.get("headers", []), el.get("rows", [])
        if not headers or not rows:
            _err(errors, path, "table은 headers·rows 필수")
        for i, row in enumerate(rows):
            if len(row) != len(headers):
                _err(errors, path, f"rows[{i}] 칸 수({len(row)})가 headers({len(headers)})와 다름")
    elif kind == "task":
        _validate_task(errors, path, el)


def _validate_task(errors, path, t):
    tt = t.get("task_type")
    if tt not in TASK_TYPES:
        _err(errors, path, f"task_type '{tt}' 미지원")
        return
    if not t.get("instruction", "").strip():
        _err(errors, path, "instruction 비어 있음")
    if t.get("element"):
        _validate_element(errors, path + ".element", t["element"], allow_task=False)
    for i, s in enumerate(t.get("setup_elements", [])):
        _validate_element(errors, f"{path}.setup[{i}]", s, allow_task=False)
    ans = t.get("answer")
    if ans:
        _validate_element(errors, path + ".answer", ans.get("element", {}), allow_task=False)
        hint = ans.get("hint", "")
        if re.search(r"(\d교시|Day \d)", hint):
            _err(errors, path, f"힌트에 교시/Day 참조 — 자체 서술로 (힌트: {hint[:40]})")
    if tt == "predict" and not ans and not t.get("no_answer_reason"):
        _err(errors, path, "predict 과제는 answer 필수 (본문에 답이 있으면 no_answer_reason에 사유)")
    if tt == "experiment":
        obs = t.get("observe", [])
        if not obs:
            _err(errors, path, "experiment 과제는 observe(관찰 포인트) 필수")
        for i, o in enumerate(obs):
            if not o.get("expected"):
                _err(errors, path, f"observe[{i}]에 expected 없음 — 기대 없는 관찰 금지")
    if tt == "challenge":
        if not t.get("requirements"):
            _err(errors, path, "challenge는 requirements 필수")
        if not t.get("goal_output"):
            _err(errors, path, "challenge는 goal_output 필수")
        if not ans:
            _err(errors, path, "challenge는 answer(정답 전문) 필수")
        tmpl, answer_el = t.get("element"), (ans or {}).get("element")
        if tmpl and answer_el and tmpl.get("kind") == "code" and answer_el.get("kind") == "code":
            tmpl_lines = {l.strip() for l in tmpl.get("src", "").splitlines()
                          if l.strip() and not l.strip().startswith("#")}
            ans_lines = {l.strip() for l in answer_el.get("src", "").splitlines()}
            missing = [l for l in tmpl_lines if l not in ans_lines]
            if missing:
                _err(errors, path, f"틀의 줄이 정답에 없음(틀⊂정답 위반): {missing[:2]}")
        # 채우기 주석의 참조 금지
        if tmpl:
            for line in tmpl.get("src", "").splitlines():
                if "여기를 채우기" in line and re.search(r"(\d교시|Day \d)", line):
                    _err(errors, path, "채우기 주석에 교시/Day 참조 — 자체 서술로")


def validate(page):
    """page dict → 오류 문자열 리스트 (빈 리스트면 통과)."""
    errors = []
    from lesson_term_flow import metadata_errors
    errors.extend(metadata_errors(page))
    ptype = page.get("type", "lesson")
    if ptype == "material":
        if not page.get("title") or not page.get("intro"):
            _err(errors, "material", "title·intro 필수")
        files = page.get("files", [])
        if not files:
            _err(errors, "material", "files 비어 있음")
        for i, f in enumerate(files):
            for k in ("filename", "lang", "content"):
                if not f.get(k):
                    _err(errors, f"files[{i}]", f"{k} 필수")
        extra = set(page.keys()) - {"type", "title", "intro", "files"}
        if extra:
            _err(errors, "material", f"실습 자료는 데이터만 — 허용 안 되는 필드 {sorted(extra)}")
        return errors
    if ptype != "lesson":
        _err(errors, "page", f"type '{ptype}' 미지원 (v1: lesson|material)")
        return errors

    if not re.match(r"^\d교시\. ", page.get("title", "")):
        _err(errors, "title", "'N교시. …' 형식이어야 한다")
    if not page.get("lead", "").strip():
        _err(errors, "lead", "리드 한 줄 필수")
    toc = page.get("toc", [])
    if not 3 <= len(toc) <= 6:
        _err(errors, "toc", f"미니 목차는 3~6개 ({len(toc)}개)")
    walkthrough = bool(page.get("walkthrough"))
    role = page.get("lesson_role")
    if role is not None and role not in LESSON_ROLES:
        _err(errors, "lesson_role", f"수업 유형은 {sorted(LESSON_ROLES)} 중 하나")
    if role == "concept" and walkthrough:
        _err(errors, "walkthrough", "개념 교시는 따라 하기 단계로 렌더하지 않는다")
    review = page.get("review", [])
    if not walkthrough and len(review) != 3:
        _err(errors, "review", f"되새김 질문은 정확히 3개 ({len(review)}개)")

    sections = page.get("sections", [])
    if not sections:
        _err(errors, "sections", "섹션이 없다")
    task_count = 0
    challenge_seen = False
    for si, sec in enumerate(sections):
        spath = f"sections[{si}]"
        if not sec.get("heading"):
            _err(errors, spath, "heading 필수")
        if sec.get("importance", "") not in ("", "✅", "❗"):
            _err(errors, spath, "importance는 ''|✅|❗")
        for bi, el in enumerate(sec.get("body", [])):
            epath = f"{spath}.body[{bi}]"
            _validate_element(errors, epath, el)
            if el.get("kind") == "task":
                task_count += 1
                if role == "concept" and el.get("task_type") != "predict":
                    _err(errors, epath, "개념 교시의 필수 활동은 이해 확인(predict)으로 작성하고 실행·구성 과제는 실습 교시로 옮긴다")
                if challenge_seen:
                    _err(errors, epath, "challenge 뒤에 또 과제가 있다 — 도전이 마지막이어야 한다")
                if el.get("task_type") == "challenge":
                    challenge_seen = True
    if role is None and not walkthrough and not 4 <= task_count <= 7:
        _err(errors, "tasks", f"교시당 과제는 체험형 여러 개 + 도전 1개, 총 4~7개 — 손 실습은 전부 번호를 단다 ({task_count}개)")
    if role is None and not walkthrough and not challenge_seen:
        _err(errors, "tasks", "마지막 과제(challenge형·직접 해보는 문제)가 없다")
    if role == "integrated_practice" and not challenge_seen:
        _err(errors, "tasks", "종합실습에는 스스로 연결해 완성하는 challenge 과제가 필요하다")
    if role == "guided_practice" and task_count == 0:
        _err(errors, "tasks", "따라 하는 실습 교시에는 실제 수행 과제가 필요하다")

    extra = page.get("extra_tasks", [])
    if role is None and not walkthrough and not extra:
        _err(errors, "extra_tasks", "추가 과제 토글은 1개 이상")
    for xi, x in enumerate(extra):
        if not x.get("title") or not x.get("text"):
            _err(errors, f"extra_tasks[{xi}]", "title·text 필수")
        if x.get("element"):
            _validate_element(errors, f"extra_tasks[{xi}].element", x["element"], allow_task=False)
        if x.get("answer"):
            _validate_element(errors, f"extra_tasks[{xi}].answer", x["answer"].get("element", {}), allow_task=False)
    hp = page.get("hard_problem")
    if hp:
        if not hp.get("title") or not hp.get("text"):
            _err(errors, "hard_problem", "title·text 필수")
        if not hp.get("answer"):
            _err(errors, "hard_problem", "도전 문제는 answer 필수")
    return errors


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    with open(sys.argv[1], encoding="utf-8") as f:
        page = json.load(f)
    errors = validate(page)
    for e in errors:
        print("SCHEMA-ERROR ", e)
    print(f"\n요약: SCHEMA-ERROR {len(errors)}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
