# -*- coding: utf-8 -*-
"""lesson_render.py — 스키마 JSON → 노션용 마크다운 (3단계).

사용법:
    python3 tools/lesson_render.py <page.json> [출력.md]

SKILL의 노션 기술 규칙을 이 파일이 전담한다:
- 코드 밖 밑줄·대괄호 이스케이프 (\\_ \\[ \\]) — 백틱 안은 건드리지 않음
- 파일명 자동 백틱 (자동 링크 방지)
- 토글: <details><summary> + 내용 줄 탭, 코드 펜스 줄 탭(펜스 안 내용은 무탭)
- 코드 펜스 언어: python/bash/json…, 출력·목표 출력은 plain text
- 과제 번호 자동 부여, 표준 문구(도전 안내문, 정답 토글 꼬리말) 자동 삽입
- verified=example인 출력은 output_label 문구를 앞에 붙여 예시임을 밝힘

렌더 결과는 lesson_lint.py를 다시 통과해야 발행한다(이중 안전망).
"""
import json
import re
import sys

FILENAME_RE = re.compile(r"(?<![`A-Za-z0-9_./-])([A-Za-z0-9_.-]+\.(?:py|json|csv|txt|md|log|env|pcapng?))(?![`A-Za-z0-9_])")

CHALLENGE_LEAD = "직접 해보는 문제"
ANSWER_TAIL = "정답을 봤다면, 닫고 안 보고 다시 써 보자."
SHELL_LANG = {"cmd": "bash", "powershell": "bash", "terminal": "bash"}


def esc(text):
    """코드 밖 텍스트 이스케이프 + 파일명 백틱. 백틱 구간은 보존."""
    parts = text.split("`")
    for i in range(0, len(parts), 2):          # 짝수 인덱스 = 백틱 밖
        # Keep authored web citations intact. Escaping their brackets makes
        # Notion show a literal label plus an automatically linked raw URL.
        chunks = re.split(r"(\[[^\[\]\n]+\]\(https?://[^\s)]+\))", parts[i])
        for j in range(0, len(chunks), 2):
            seg = FILENAME_RE.sub(r"`\1`", chunks[j])
            chunks[j] = seg.replace("_", "\\_").replace("[", "\\[").replace("]", "\\]")
        parts[i] = "".join(chunks)
    out = "`".join(parts)
    # 파일명 백틱 처리로 새 백틱이 생긴 경우 이스케이프가 안 섞이게 재조립
    return out.replace("`\\_", "`_").replace("\\_`", "_`")


def esc_block(text):
    """여러 줄 산문."""
    return "\n".join(esc(l) for l in text.splitlines())


def fence(lang, body, indent=""):
    shown = "plain text" if lang in ("text", "plain text") else lang
    return f"{indent}```{shown}\n{body}\n{indent}```"


def render_output(el, indent=""):
    lines = []
    label = el.get("output_label")
    if label:
        lines.append(indent + esc(label))
    lines.append(fence("text", el["output"], indent))
    return lines


def render_element(el, indent=""):
    kind = el["kind"]
    if kind == "paragraph":
        return [indent + esc_block(el["text"])]
    if kind == "checkpoint_question":
        lines = [indent + "<details>", indent + f"<summary>{el['number']}번</summary>",
                 indent + "\t" + esc(el["question"])]
        lines += [indent + "\t- " + label + ". " + esc(option["text"])
                  for label, option in zip("ABCD", el["options"])]
        lines += [indent + "\t<details>", indent + "\t<summary>정답·해설 보기</summary>",
                  indent + "\t\t정답: " + el["correct"]]
        lines += [indent + "\t\t- " + label + ". " + esc(option["feedback"])
                  for label, option in zip("ABCD", el["options"])]
        lines += [indent + "\t</details>", indent + "</details>"]
        return lines
    if kind == "supplement":
        lines = [indent + "<details>", indent + "<summary>보충 — " + esc(el["title"]) + "</summary>"]
        for child in el["body"]:
            lines += render_element(child, indent + "\t")
        lines.append(indent + "</details>")
        return lines
    if kind == "definition":
        en = f"({el['en']})" if el.get("en") else ""
        return [indent + f"> **{esc(el['term'])}{esc(en)}** — {esc(el['text'])}"]
    if kind in ("bullets", "numbered_list"):
        lines = []
        if el.get("intro"):
            lines.append(indent + esc(el["intro"]))
        lines += [indent + (f"{n}. " if kind == "numbered_list" else "- ") + esc(item)
                  for n, item in enumerate(el["items"], 1)]
        return lines
    if kind == "code":
        lines = [fence(el.get("lang", "python"), el["src"], indent)]
        if el.get("output") is not None:
            lines += render_output(el, indent)
        return lines
    if kind == "command":
        lines = [fence(SHELL_LANG[el["shell"]], el["src"], indent)]
        if el.get("output") is not None:
            lines += render_output(el, indent)
        return lines
    if kind == "tool_steps":
        lines = [indent + esc(el["tool"])]
        lines += [indent + f"{i}. " + esc(s) for i, s in enumerate(el["steps"], 1)]
        if el.get("note"):
            lines.append(indent + esc(el["note"]))
        return lines
    if kind == "image":
        cap = esc(el.get("caption", ""))
        return [indent + f"<image src=\"{el['src']}\">{cap}</image>"]
    if kind == "table":
        lines = [indent + '<table header-row="true">', indent + "<tr>"]
        lines += [indent + f"<td>{esc(h)}</td>" for h in el["headers"]]
        lines.append(indent + "</tr>")
        for row in el["rows"]:
            lines.append(indent + "<tr>")
            lines += [indent + f"<td>{esc(c)}</td>" for c in row]
            lines.append(indent + "</tr>")
        lines.append(indent + "</table>")
        return lines
    raise ValueError(f"render_element: 미지원 kind {kind}")


def render_answer_toggle(ans, summary, tail=True):
    """정답 토글 — 내용 줄과 펜스 줄에 탭, 펜스 안은 무탭."""
    lines = [f"<details>", f"<summary>{summary}</summary>"]
    if ans.get("hint"):
        lines.append("\t힌트: " + esc(ans["hint"]))
    el = ans["element"]
    if el["kind"] in ("code", "command"):
        lang = el.get("lang", "python") if el["kind"] == "code" else SHELL_LANG[el["shell"]]
        lines.append(fence(lang, el["src"], "\t"))
        if el.get("output") is not None:
            for l in render_output(el, "\t"):
                lines.append(l)
    else:
        lines += render_element(el, "\t")
    if ans.get("explain"):
        lines.append("\t" + esc_block(ans["explain"]))
    if tail:
        lines.append("\t" + ANSWER_TAIL)
    lines.append("</details>")
    return lines


def render_task(t, n, label="과제"):
    lines = []
    tt = t["task_type"]
    if tt == "challenge":
        head = f"**과제 {n}. 도전 — {esc(t.get('title', ''))}**".replace(" — ****", "")
        lines.append(f"{head} — {esc(t['instruction'])}")
        if t.get("requirements"):
            lines.append("요구사항:")
            lines += ["- " + esc(r) for r in t["requirements"]]
        for s in t.get("setup_elements", []):
            lines += render_element(s)
        if t.get("element"):
            lines.append(t.get("start_label", "시작 틀 — 그대로 실행되는 상태다.") if t["element"]["kind"] == "code" else "")
            lines = [l for l in lines if l != ""]
            lines += render_element(t["element"])
        lines.append(esc(t.get("goal_label", "목표 출력")) + ":")
        lines.append(fence("text", t["goal_output"]))
        if t.get("after_goal"):
            lines.append(esc_block(t["after_goal"]))
        answer_is_code = t["answer"]["element"].get("kind") == "code" and t["answer"]["element"].get("lang", "python") not in ("markdown", "text")
        lines += render_answer_toggle(t["answer"], t.get("answer_label", "어려우면 — 정답 코드 참조" if answer_is_code else "진행이 막히면 — 확인 기준과 해설"), tail=answer_is_code)
        return lines
    lines.append(f"**{label} {n}.** {esc(t['instruction'])}")
    for s in t.get("setup_elements", []):
        lines += render_element(s)
    if t.get("element"):
        lines += render_element(t["element"])
    if tt == "experiment":
        lines.append("관찰 포인트:")
        for o in t["observe"]:
            exp = f" — {esc(o['expected'])}" if o.get("expected") else ""
            lines.append("- " + esc(o["point"]) + exp)
    if t.get("answer"):
        lines += render_answer_toggle(t["answer"], "정답 보기", tail=False)
    return lines


def render_walkthrough_step(t, n):
    """문제·정답 구조 없이 그대로 따라 하는 단계로 task 원본을 렌더한다."""
    lines = [f"### {n}단계. {esc(t['instruction'])}"]
    for s in t.get("setup_elements", []):
        lines += render_element(s)

    if t["task_type"] == "challenge":
        # 빈칸 시작 틀 대신 완성 명령을 바로 보여 준다.
        complete = t.get("answer", {}).get("element") or t.get("element")
        if complete:
            lines += render_element(complete)
        if t.get("goal_output"):
            lines.append("정상이라면 다음처럼 보인다.")
            lines.append(fence("text", t["goal_output"]))
        explain = t.get("answer", {}).get("explain")
        if explain:
            lines.append(esc_block(explain))
        return lines

    if t.get("element"):
        lines += render_element(t["element"])
    if t["task_type"] == "experiment" and t.get("observe"):
        lines.append("확인할 결과:")
        for o in t["observe"]:
            exp = f" — {esc(o['expected'])}" if o.get("expected") else ""
            lines.append("- " + esc(o["point"]) + exp)
    return lines


def render_extra(x):
    shown_title = esc(x["title"])
    # Notion은 굵은 글씨 안의 인라인 코드를 저장할 때 `****`를 끼워 넣을 수 있다.
    # 코드 표기가 든 제목은 굵게 감싸지 않아 발행 후 마커 파손을 막는다.
    title_markup = shown_title if "`" in shown_title else f"**{shown_title}**"
    lines = [f"\t{title_markup} — {esc(x['text'])}"]
    if x.get("element"):
        lines += render_element(x["element"], "\t")
    if x.get("goal_output"):
        lines.append("\t목표 출력:")
        lines.append(fence("text", x["goal_output"], "\t"))
    if x.get("answer"):
        ans = x["answer"]
        if ans.get("hint"):
            lines.append("\t힌트: " + esc(ans["hint"]))
        lines.append("\t정답 코드:")
        el = ans["element"]
        lang = el.get("lang", "python") if el["kind"] == "code" else SHELL_LANG[el["shell"]]
        lines.append(fence(lang, el["src"], "\t"))
    return lines


def render(page):
    if page.get("type") == "material":
        lines = [esc_block(page["intro"])]
        for f in page["files"]:
            lines.append(f"## `{f['filename']}`")
            if f.get("note"):
                lines.append(esc_block(f["note"]))
            lines.append(fence(f["lang"], f["content"]))
        return "\n".join(lines)

    lines = [esc_block(page["lead"])]
    lines += ["- " + esc(t) for t in page["toc"]]
    pv = page.get("preview")
    if pv:
        lines.append(esc(pv.get("intro", "이번 시간이 끝나면 다음과 같은 코드를 쓸 수 있게 된다. 먼저 가볍게 살펴보고 본격적으로 익혀 보자.")))
        lines += render_element(pv["element"])
    if page.get("principle"):
        lines.append(esc(page["principle"]))

    walkthrough = bool(page.get("walkthrough"))
    n = 0
    for sec in page["sections"]:
        imp = f" {sec['importance']}" if sec.get("importance") else ""
        lines.append(f"## {esc(sec['heading'])}{imp}")
        for el in sec["body"]:
            if el["kind"] == "task":
                n += 1
                lines += render_walkthrough_step(el, n) if walkthrough else render_task(el, n, "이해 확인" if page.get("lesson_role") == "concept" else "과제")
            else:
                lines += render_element(el)

    if page.get("closing"):
        lines.append(esc_block(page["closing"]))
    if walkthrough:
        return "\n".join(lines)
    if page.get("extra_tasks"):
        lines.append("<details>")
        lines.append("<summary>추가 과제 — 빨리 끝났다면</summary>")
        for x in page["extra_tasks"]:
            lines += render_extra(x)
        lines.append("</details>")
    hp = page.get("hard_problem")
    if hp:
        lines.append("<details>")
        lines.append("<summary>도전 문제 — 더 파고들고 싶다면</summary>")
        lines += render_extra(hp)
        lines.append("</details>")
    if page.get("review"):
        lines.append("## 되새김 문제")
        lines.append("다음 질문에 말로 답할 수 있으면 이번 시간을 제대로 이해한 것이다.")
        lines += ["- " + esc(q) for q in page["review"]]
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    with open(sys.argv[1], encoding="utf-8") as f:
        page = json.load(f)
    from lesson_schema import validate
    errors = validate(page)
    if errors:
        for e in errors:
            print("SCHEMA-ERROR ", e)
        sys.exit(1)
    md = render(page)
    if len(sys.argv) > 2:
        with open(sys.argv[2], "w", encoding="utf-8") as f:
            f.write(md)
        print(f"렌더 완료 → {sys.argv[2]}")
    else:
        print(md)


if __name__ == "__main__":
    main()
