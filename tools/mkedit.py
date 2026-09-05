# -*- coding: utf-8 -*-
"""mkedit.py — 노션 update_content 페이로드를 안전하게 만든다.

사용법:
    python3 tools/mkedit.py <edits.json>

edits.json은 한글 원문 그대로(UTF-8) 쓴 [{"old_str": ..., "new_str": ...}, ...] 목록이다.
이 스크립트가 두 가지를 해 준다.
 1) new_str 전체를 lesson_lint.py의 오타 거부 목록·의심 음절·한글-숫자-한글 패턴으로 먼저 검사한다.
    걸리면 출력하지 않고 종료 코드 1 — 발행 금지.
 2) 통과하면 ensure_ascii=True로 이스케이프한 JSON을 찍는다. 그대로 복사해 도구 인자로 쓴다.

손으로 \\uXXXX를 적다가 음절이 깨지는 사고(2026-09-02~03 4회)를 막기 위한 장치다.
"""
import json
import re
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from lesson_lint import TYPO_SUBSTRINGS, SUSPICIOUS_SYLLABLES


def check(text, where):
    bad = []
    for pat in TYPO_SUBSTRINGS:
        if pat in text:
            bad.append(f"{where}: 오타 거부 목록 '{pat}'")
    for ch in text:
        if ch in SUSPICIOUS_SYLLABLES:
            bad.append(f"{where}: 의심 음절 '{ch}'")
    m = re.search(r"[가-힣][0-9][가-힣]", text)
    if m:
        bad.append(f"{where}: 한글-숫자-한글 '{m.group(0)}' — 이스케이프 잘림 의심")
    return bad


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    with open(sys.argv[1], encoding="utf-8") as f:
        edits = json.load(f)
    bad = []
    for i, e in enumerate(edits):
        bad += check(e.get("new_str", ""), f"edits[{i}].new_str")
    if bad:
        for b in bad:
            print("ERROR " + b, file=sys.stderr)
        print(f"\n{len(bad)}건 — 고치기 전에는 출력하지 않는다.", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(edits, ensure_ascii=True))


if __name__ == "__main__":
    main()
