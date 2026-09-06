# -*- coding: utf-8 -*-
"""lesson_lint.py — ALEPH 교안 페이지 기계 검수기.

사용법:
    python3 tools/lesson_lint.py <페이지본문.md> [--type lesson|cover|material]

발행 전 초안과 발행 후 fetch 덤프 양쪽에 돌린다.
ERROR가 하나라도 있으면 종료 코드 1 — 발행/완료 금지.
WARN은 사람이 하나씩 판정한다(전부 열거하는 것 자체가 목적).
"""
import ast
import re
import sys

# ── 세션에서 실제로 발생했던 한글 오타 패턴 (재발 검출용 거부 목록) ──
TYPO_SUBSTRINGS = [
    "좍히", "좍힌", "좍혀", "좍힐", "왜복", "어그나", "어그난", "어긋닌",
    "바뀜 수", "바뀜다", "바뀜는", "바뀜었", "바뀜까", "캐프스톤", "갈아뀜",
    "가벼게", "가벽게", "준비뜐", "안 뜐", "멀셝", "섮여", "캐묻된",
    "익힐다", "익힙다", "뜸다", "무달이다", "첧", "꾲", "꼲", "잋", "뒜",
    "끩", "곷", "뮘", "쉝", "뜼", "옞기", "뿌대", "벼대", "깔낌", "쪼걠",
    "쪼갬 때", "아낌다", "잠그다.", "뜨다 —", "끈어야", "느가로", "나닉",
    "곶란", "곶난", "둠야", "둡야", "캐스톤",
    "부들고", "엉뚜", "섮여", "겉봉", "쪼간 ", "서버과", "잡핀다",
    "흔어", "바뀜어", "퀈", "오퀈", "보람 것", "앵은 사람", "잠시 끔다",
]
# 자모 조합상 한국어에 사실상 없는 음절(단독 등장 시 오타 의심)
SUSPICIOUS_SYLLABLES = "잋뒜뜐섮셝첧끩꾲꼲곷뮘쉝뜼옞걠벰퀈"

ALLOWED_SYMBOLS = {"✅", "❗"}
FORBIDDEN_WORDS = ["제출", "조별 채널", "조원"]

REVIEW_HEADER = "되새김 문제"


def is_emoji(ch):
    cp = ord(ch)
    if ch in ALLOWED_SYMBOLS:
        return False
    return (
        0x1F000 <= cp <= 0x1FAFF
        or 0x2600 <= cp <= 0x27BF
        or cp in (0x2B50, 0x2B55, 0x203C, 0x2049)
        or 0x1F1E6 <= cp <= 0x1F1FF
    )


def split_blocks(lines):
    """(kind, lang, start_line, [lines]) 목록으로 분해. kind: prose|code"""
    blocks = []
    buf, start = [], 1
    in_code, lang = False, ""
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            if not in_code:
                if buf:
                    blocks.append(("prose", "", start, buf))
                in_code = True
                lang = stripped[3:].strip()
                buf, start = [], i
            else:
                blocks.append(("code", lang, start, buf))
                in_code = False
                buf, start = [], i + 1
            continue
        buf.append((i, line))
    if buf:
        blocks.append(("code" if in_code else "prose", lang if in_code else "", start, buf))
    return blocks


def collect_defined_names(tree):
    defined = set(dir(__builtins__)) if not isinstance(__builtins__, dict) else set(__builtins__.keys())
    defined |= {"True", "False", "None", "self"}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.add(node.name)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                a = node.args
                for arg in a.args + a.posonlyargs + a.kwonlyargs:
                    defined.add(arg.arg)
                if a.vararg:
                    defined.add(a.vararg.arg)
                if a.kwarg:
                    defined.add(a.kwarg.arg)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                defined.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign, ast.For, ast.withitem, ast.comprehension)):
            targets = []
            if isinstance(node, ast.Assign):
                targets = node.targets
            elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
                targets = [node.target]
            elif isinstance(node, ast.For):
                targets = [node.target]
            elif isinstance(node, ast.withitem):
                targets = [node.optional_vars] if node.optional_vars else []
            elif isinstance(node, ast.comprehension):
                targets = [node.target]
            for t in targets:
                for n in ast.walk(t):
                    if isinstance(n, ast.Name):
                        defined.add(n.id)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            defined.add(node.name)
    return defined


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path")
    parser.add_argument("--type", choices=("lesson", "cover", "material"), default="lesson")
    parser.add_argument("--role", choices=("concept", "guided_practice", "integrated_practice"))
    args = parser.parse_args()
    path = args.path
    with open(path, encoding="utf-8") as f:
        text = f.read()
    lines = text.split("\n")
    errors, warns = [], []

    # ── 줄 단위 검사 ──
    in_code = False
    for i, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            in_code = not in_code
            if in_code and line.strip() == "```":
                errors.append((i, "코드 펜스에 언어 지정 없음 (```python / ```bash / ```plain text ...)"))
            continue
        for pat in TYPO_SUBSTRINGS:
            if pat in line:
                errors.append((i, f"오타 거부 목록 일치: '{pat}'"))
        for ch in line:
            if ch in SUSPICIOUS_SYLLABLES:
                errors.append((i, f"의심 음절 '{ch}' — 코드포인트 오타 가능성"))
            if is_emoji(ch):
                errors.append((i, f"금지 이모지 '{ch}' (허용: ✅ ❗)"))
        # 유니코드 이스케이프 잘림 흔적 — 한글 음절 뒤에 숫자가 붙고 다시 한글이 이어진다
        m = re.search(r"[가-힣][0-9][가-힣]", line)
        if m:
            warns.append((i, f"한글-숫자-한글 붙음 '{m.group(0)}' — \\uXXXX 잘림 의심"))
        if "- [ ]" in line or "- [x]" in line:
            errors.append((i, "체크박스 금지"))
        for w in FORBIDDEN_WORDS:
            if w in line:
                errors.append((i, f"금지어 '{w}'"))
        if re.search(r"\]\(https?://[A-Za-z0-9_.-]+\.(py|md|json|csv|txt|log)\)", line):
            errors.append((i, "파일명 자동 링크 — 백틱으로 교체"))
        m2 = re.search(r"\[([A-Za-z0-9_.-]+\.(com|net|org|io|kr|co\.kr))\]\(https?://", line)
        if m2:
            errors.append((i, f"도메인 자동 링크 '{m2.group(1)}' — 백틱으로 감싸 재발행"))
        if re.search(r"\[[^\]\n]+\]\(\[https?://", line):
            errors.append((i, "출처 링크 중첩 — 이스케이프된 링크가 노션에서 자동 링크로 변형됨"))
        if re.search(r"\*\*\*\*", line):
            errors.append((i, "볼드 마커 깨짐(****) — 볼드 안에 백틱을 넣지 말 것"))
        if not in_code:
            if re.search(r"[가-힣](?<!아)니다[.!?)\"”']?\s*$", line.strip()) or re.search(r"(하세요|해요)[.!?)\"”']?\s*$", line.strip()):
                warns.append((i, "본문 존댓말 어미 의심 (인용·대사·에러 메시지면 무시)"))
            elif re.search(r"[가-힣](?<!아)니다\.", line) and '"' not in line and "'" not in line and "“" not in line and "`" not in line:
                warns.append((i, "본문 중간 존댓말 의심 (인용이면 무시)"))
        # SKILL ⑧ 참조 검출 — 판단은 사람이, 열거는 기계가
        ref = re.search(r"(\d교시|과제 \d|Day \d)", line)
        if ref:
            # "**과제 N. ..." 헤더가 자기 번호+표준 문구("[여기를 채우기]를 채워")로 걸리는 오탐 제외
            if line.strip().startswith("**과제"):
                pass
            elif "여기를 채우기" in line or "힌트:" in line:
                errors.append((i, f"채우기/힌트에 참조 '{ref.group(1)}' — 자체 서술로 교체"))
            elif any(k in line for k in ("그대로", "가져", "참조", "요구사항", "저장한", "완성하자", "도전")):
                warns.append((i, f"참조 '{ref.group(1)}' — 지워도 풀 수 있는지 판정할 것: {line.strip()[:60]}"))

    # ── 마커 짝 검사 ──
    starts = text.count("수정 시작")
    ends = text.count("수정 끝")
    if starts != ends:
        errors.append((0, f"수정 시작({starts})/수정 끝({ends}) 짝 불일치"))

    # ── 토글 짝 검사 ──
    if text.count("<details>") != text.count("</details>"):
        errors.append((0, "<details> 짝 불일치"))
    if text.count("<summary>") != text.count("</summary>"):
        errors.append((0, "<summary> 짝 불일치"))

    # ── 파이썬 블록 검사 ──
    blocks = split_blocks(lines)
    prev_prose_tail = ""
    for kind, lang, start, blk in blocks:
        if kind == "prose":
            prev_prose_tail = "\n".join(l for _, l in blk[-5:])
            continue
        src = "\n".join(l for _, l in blk)
        # Cisco IOS 설정 블록은 초보자가 입력 명령과 현재 모드를 구분할 수 있게
        # 장비명+프롬프트(Switch(config)# 등)를 함께 보여 준다.
        if lang.lower() == "bash" and "configure terminal" in src:
            if not re.search(r"^(?:Switch|Router)(?:\([^\n)]*\))?[>#]\s+\S", src, re.M):
                errors.append((start, "Cisco IOS 설정 블록에 장비명·모드 프롬프트 없음 (예: Switch(config)#)"))
        if lang.lower() != "python":
            continue
        intentional = any(k in src or k in prev_prose_tail for k in ("실수한 코드", "고장", "실수 —", "에러 시연"))
        try:
            tree = ast.parse(src)
        except SyntaxError as e:
            if not intentional:
                errors.append((start + (e.lineno or 1), f"python 블록 문법 오류: {e.msg} (의도된 고장이면 '실수한 코드'/'고장' 표기)"))
            continue
        # 완전체 검사 — 정의 없이 쓰는 이름
        if not intentional and "해석된다" not in prev_prose_tail and "# (" not in src.split("\n")[0]:
            defined = collect_defined_names(tree)
            missing = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id not in defined:
                    missing.add(node.id)
            if missing:
                warns.append((start, f"완전체 의심 — 정의 없는 이름 {sorted(missing)} (미리보기/해석 재표기면 무시)"))

    # ── 되새김 3문 검사 ──
    if REVIEW_HEADER in text:
        seg = text.split(REVIEW_HEADER, 1)[1]
        bullets = [l for l in seg.split("\n") if l.strip().startswith("- ")]
        if len(bullets) != 3:
            warns.append((0, f"되새김 질문이 3개가 아님 ({len(bullets)}개)"))

    # ── 구성 계기판 (Day 8 5교시 = 템포 기준점) ──
    task_heads = re.findall(r"^\*\*과제 (\d+)[.． ]([^\n]*)", text, re.M)
    n_tasks = len(task_heads)
    code_blocks = sum(1 for k, lang, _, _ in blocks if k == "code" and lang.lower() in ("python", "bash"))
    traps = sum(text.count(k) for k in ("실수한 코드", "에러 시연", "고장난 코드", "일부러 고장"))
    has_takeaway = "챙겨 가기" in text
    if (has_takeaway or REVIEW_HEADER in text) and not re.search(r'<image\b|!\[[^\]]*\]\(', text):
        warns.append((0, "시각 설명 이미지 없음 — 핵심 동작의 흐름도·구성도·시간축 필요 여부를 검토"))
    if REVIEW_HEADER in text and args.role is None:  # 기존 코딩 교시의 템포 기준
        if n_tasks and n_tasks < 4:
            warns.append((0, f"과제 {n_tasks}개 — 템포 기준(체험형 여러 개+도전, 4개 이상)에 미달"))
        if task_heads and "도전" not in task_heads[-1][1]:
            warns.append((0, "마지막 과제가 도전이 아님 — 도전으로 끝나야 한다"))
        if code_blocks < 8:
            warns.append((0, f"실행 코드 블록 {code_blocks}개 — 손 과제 총량 부족 의심 (기준 8개 이상)"))
        if traps < 2:
            warns.append((0, f"함정·에러 시연 {traps}개 — 교시당 2개 이상 권장"))
        if not has_takeaway:
            warns.append((0, "챙겨 가기 표 없음"))
    print(f"METRIC 유형 {args.role or 'legacy'} / 과제 {n_tasks}개 / 코드 블록 {code_blocks}개 / 함정 {traps}개 / 챙겨가기 {'있음' if has_takeaway else '없음'}")

    # ── 결과 출력 ──
    for lineno, msg in sorted(errors):
        print(f"ERROR  L{lineno:>4}  {msg}")
    for lineno, msg in sorted(warns):
        print(f"WARN   L{lineno:>4}  {msg}")
    print(f"\n요약: ERROR {len(errors)} / WARN {len(warns)}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
