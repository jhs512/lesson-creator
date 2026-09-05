"""Regression cases for the novice terminology gate, with no external packages."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lesson_harness import run_page
from lesson_schema import validate
from lesson_term_flow import check_page, svg_text_content, visible_units


INTRO = "조직 안에서 사용하는 웹 화면을 제공하는 서버를 인트라넷 서버라고 한다."


def paragraph(text):
    return {"kind": "paragraph", "text": text}


def sample(*body):
    return {
        "type": "lesson", "title": "1교시. 인트라넷 서버 알아보기",
        "lead": "이름을 알아보기 전에 화면을 제공하는 역할부터 살펴보자.",
        "toc": ["인트라넷 서버", "동작", "확인"],
        "walkthrough": True,
        "sections": [{"heading": "인트라넷 서버", "body": list(body)}],
        "learning_terms": [{"term": "인트라넷 서버", "aliases": ["IntranetServer"],
                            "introduced_by": INTRO}],
    }


class TermFlowTests(unittest.TestCase):
    def assertPass(self, page):
        passed, failed, skipped = check_page(page)
        self.assertEqual(failed, [])
        self.assertEqual(skipped, [])
        self.assertEqual(len(passed), len(page["learning_terms"]))

    def test_same_paragraph_intro_and_later_alias_pass(self):
        self.assertPass(sample(paragraph(INTRO), paragraph("IntranetServer를 연다.")))

    def test_first_use_in_image_before_prose_fails(self):
        page = sample({"kind": "image", "src": "file-upload://test",
                       "text_content": "PC0\nIntranetServer 192.168.20.100",
                       "caption": "연결을 살펴보자."}, paragraph(INTRO))
        failed = check_page(page)[1]
        self.assertEqual(len(failed), 1)
        self.assertIn("body[0].text_content", failed[0][1])

    def test_moving_explanation_after_use_fails(self):
        page = sample(paragraph(INTRO), paragraph("IntranetServer를 연다."))
        self.assertPass(page)
        page["sections"][0]["body"].reverse()
        self.assertIn("설명 전 사용", check_page(page)[1][0][1])

    def test_absent_or_metadata_only_explanation_fails(self):
        page = sample(paragraph("IntranetServer를 연다."))
        self.assertIn("보이는 산문에 없음", check_page(page)[1][0][1])

    def test_caption_cannot_supply_explanation(self):
        page = sample({"kind": "image", "src": "file-upload://test",
                       "text_content": "IntranetServer", "caption": INTRO})
        self.assertIn("보이는 산문에 없음", check_page(page)[1][0][1])

    def test_code_cannot_supply_explanation(self):
        page = sample({"kind": "code", "lang": "text", "src": INTRO})
        self.assertIn("보이는 산문에 없음", check_page(page)[1][0][1])

    def test_image_inventory_mandatory_even_if_caption_has_no_term(self):
        page = sample(paragraph(INTRO), {"kind": "image", "src": "file-upload://test",
                                       "caption": "케이블의 위치"})
        failed = check_page(page)[1]
        self.assertEqual(len(failed), 1)
        self.assertIn("text_content", failed[0][0])

    def test_legacy_pages_are_explicit_skip(self):
        page = sample({"kind": "image", "src": "file-upload://test"})
        del page["learning_terms"]
        passed, failed, skipped = check_page(page)
        self.assertEqual(passed, [])
        self.assertEqual(failed, [])
        self.assertIn("미선언", skipped[0][1])

    def test_ascii_aliases_are_not_substrings_of_other_names(self):
        intro = "DNS는 이름에 대응하는 주소를 찾는 기능이다."
        page = sample(paragraph("DNSServer와 CustomDNSRecord라는 장비 이름이 있다."),
                      paragraph(intro), paragraph("dns가 응답했다."))
        page["learning_terms"] = [{"term": "DNS", "introduced_by": intro}]
        self.assertPass(page)
        page["lead"] = "DNS가 응답했다."
        self.assertIn("설명 전 사용: lead", check_page(page)[1][0][1])

    def test_definition_dependency_is_not_exempt_from_first_use(self):
        page = sample(paragraph(INTRO), paragraph("서버는 다른 컴퓨터의 요청에 응답하는 역할이다."))
        page["learning_terms"].append({"term": "서버", "introduced_by": "서버는 다른 컴퓨터의 요청에 응답하는 역할이다."})
        self.assertEqual(len(check_page(page)[1]), 1)
        self.assertIn("(서버)", check_page(page)[1][0][0])

    def test_korean_term_not_inside_unrelated_word_but_particles_count(self):
        intro = "로그는 일어난 일을 남긴 기록이다."
        page = sample(paragraph("프로그램을 연다."), paragraph(intro))
        page["learning_terms"] = [{"term": "로그", "introduced_by": intro}]
        self.assertPass(page)
        page["lead"] = "로그를 읽는다."
        self.assertIn("설명 전 사용: lead", check_page(page)[1][0][1])

    def test_longer_declared_english_phrase_owns_its_full_span(self):
        page = sample(paragraph("DNS(Domain Name System)는 주소를 찾는 체계다."),
                      paragraph("도메인 이름(domain name)은 점으로 나눈 이름이다."))
        page["learning_terms"] = [
            {"term": "DNS", "aliases": ["Domain Name System"], "introduced_by": "주소를 찾는 체계다."},
            {"term": "도메인 이름", "aliases": ["domain name"], "introduced_by": "점으로 나눈 이름이다."},
        ]
        self.assertPass(page)
        page["lead"] = "domain name을 살펴본다."
        self.assertIn("설명 전 사용: lead", check_page(page)[1][0][1])

    def test_multiline_preview_prose_cannot_hide_late_introduction(self):
        page = sample()
        page["preview"] = {"intro": "IntranetServer를 연다.\n\n" + INTRO,
                           "element": paragraph("완료")}
        self.assertIn("preview.intro.paragraph[0]", check_page(page)[1][0][1])

    def test_label_and_explanation_in_same_table_row_pass(self):
        page = sample({"kind": "table", "headers": ["이름", "뜻"],
                       "rows": [["IntranetServer", INTRO]]})
        self.assertPass(page)

    def test_preview_precedes_principle(self):
        page = sample()
        page["preview"] = {"intro": "완료한 모습을 보자.", "element": paragraph("IntranetServer를 연다.")}
        page["principle"] = INTRO
        self.assertIn("preview.element.text", check_page(page)[1][0][1])

    def test_custom_challenge_start_label_precedes_code(self):
        page = sample({"kind": "task", "task_type": "challenge", "instruction": "설정한다.",
                       "start_label": INTRO, "element": {"kind": "code", "lang": "text", "src": "IntranetServer"}})
        page["walkthrough"] = False
        self.assertPass(page)
        page["sections"][0]["body"][0]["start_label"] = "IntranetServer를 확인한다."
        page["sections"][0]["body"].append(paragraph(INTRO))
        self.assertIn("start_label", check_page(page)[1][0][1])

    def test_commands_ui_and_answers_count_as_uses(self):
        for early in [
            {"kind": "command", "shell": "cmd", "src": "ping IntranetServer"},
            {"kind": "tool_steps", "tool": "장비 창", "steps": ["IntranetServer를 클릭한다."]},
            {"kind": "task", "task_type": "predict", "instruction": "이름을 읽자.",
             "answer": {"element": paragraph("IntranetServer이다.")}},
        ]:
            with self.subTest(early=early["kind"]):
                page = sample(early, paragraph(INTRO))
                page["walkthrough"] = False
                self.assertIn("설명 전 사용", check_page(page)[1][0][1])

    def test_unrendered_walkthrough_answer_cannot_supply_intro(self):
        page = sample({"kind": "task", "task_type": "action", "instruction": "IntranetServer를 연다.",
                       "answer": {"element": paragraph(INTRO)}})
        self.assertIn("보이는 산문에 없음", check_page(page)[1][0][1])

    def test_walkthrough_challenge_uses_complete_answer_not_hidden_starter(self):
        page = sample(paragraph(INTRO), {
            "kind": "task", "task_type": "challenge", "instruction": "주소를 확인한다.",
            "requirements": ["렌더하지 않는 요구사항"],
            "element": paragraph("렌더하지 않는 틀"),
            "answer": {"element": paragraph("IntranetServer를 확인한다."), "hint": "렌더하지 않는 힌트"},
            "goal_output": "성공", "after_goal": "렌더하지 않는 안내",})
        shown = "\n".join(unit.text for unit in visible_units(page))
        self.assertNotIn("렌더하지 않는", shown)
        self.assertPass(page)

    def test_extra_answer_hidden_explain_and_output_cannot_supply_intro(self):
        page = sample(paragraph("IntranetServer를 연다."))
        page["walkthrough"] = False
        page["extra_tasks"] = [{"title": "확인", "text": "출력을 읽자.",
            "answer": {"element": {"kind": "code", "src": "print('done')", "output": INTRO},
                       "explain": INTRO}}]
        self.assertIn("보이는 산문에 없음", check_page(page)[1][0][1])

    def test_invalid_metadata_reports_errors_without_crashing(self):
        for value in [None, [], "DNS", [None], [{"term": "DNS", "aliases": "DNS"}]]:
            with self.subTest(value=value):
                page = sample()
                page["learning_terms"] = value
                self.assertTrue(check_page(page)[1])
                self.assertTrue(validate(page))

    def test_harness_failure_and_process_exit_include_terms(self):
        page = sample(paragraph("IntranetServer를 연다."), paragraph(INTRO))
        self.assertTrue(run_page(page)[1])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "page.json"
            path.write_text(json.dumps(page, ensure_ascii=False), encoding="utf-8")
            result = subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1] / "lesson_harness.py"), str(path)],
                                    capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("learning_terms", result.stdout)

    def test_svg_actual_labels_include_nested_tspans(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "diagram.svg"
            path.write_text('<svg xmlns="http://www.w3.org/2000/svg"><title>hidden metadata</title>'
                            '<text>PC0</text><text>Intranet<tspan>Server</tspan></text></svg>', encoding="utf-8")
            self.assertEqual(svg_text_content(path), "PC0\nIntranetServer")


if __name__ == "__main__":
    unittest.main()
