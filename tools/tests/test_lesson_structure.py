"""Behavioral coverage for supplements and reading-structure diagnostics."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lesson_harness import run_page
from lesson_render import render
from lesson_schema import validate
from lesson_structure import check_structure
from lesson_term_flow import check_page
from render_lesson_preview import render as preview


def prose(text):
    return {"kind": "paragraph", "text": text}


def supplement(*body):
    return {"kind": "supplement", "title": "저장된 답 확인", "body": list(body)}


def page(*body):
    return {"type": "lesson", "title": "1교시. 답 읽기", "lead": "같은 질문을 다시 해 보자.",
            "toc": ["질문", "확인", "정리"], "walkthrough": True,
            "sections": [{"heading": "질문", "body": list(body)},
                         {"heading": "확인", "body": [prose("관찰 결과를 비교한다.")]},
                         {"heading": "정리", "body": [prose("값이 달라진 이유를 말한다.")]}]}


class StructureTests(unittest.TestCase):
    def test_obvious_diagram_legend_is_reviewed_without_failing(self):
        p = page(prose("인터넷 구름과 번개, 지그재그 선은 중간 연결을 줄여 그린 기호다."))
        passed, failed, review = check_structure(p)
        self.assertEqual(failed, [])
        self.assertTrue(any("그림 기호 자체" in reason for _, reason in review))

    def test_packet_destination_explanation_is_not_diagram_legend(self):
        p = page(prose("DNS 응답 패킷의 목적지는 PC이고, 응답 안의 A 값은 후속 웹 통신의 목적지로 사용된다."))
        self.assertFalse(any("그림 기호 자체" in reason for _, reason in check_structure(p)[2]))

    def test_supplement_survives_markdown_and_html(self):
        p = page(prose("이름에 맞는 주소를 찾는다."), supplement(prose("추가 비교 설명이다.")))
        self.assertEqual(validate(p), [])
        md = render(p)
        self.assertIn("<summary>보충 — 저장된 답 확인</summary>", md)
        html = preview(md, p["title"])
        self.assertIn("<details>", html)
        self.assertIn("추가 비교 설명이다.", html)

    def test_required_term_cannot_rely_on_closed_supplement(self):
        p = page(prose("한 번 받은 답을 다시 쓸 수 있다."),
                 supplement(prose("캐시는 받은 답을 잠시 저장한 사본이다.")),
                 prose("캐시의 주소를 확인한다."))
        p["learning_terms"] = [{"term": "캐시", "introduced_by": "받은 답을 잠시 저장한 사본이다."}]
        self.assertEqual(check_page(p)[1], [])
        self.assertIn("보충을 닫은 본문", check_structure(p)[1][0][1])
        self.assertTrue(run_page(p)[1])

    def test_optional_only_term_can_be_introduced_in_supplement(self):
        p = page(prose("주소 결과를 읽는다."),
                 supplement(prose("캐시는 받은 답을 잠시 저장한 사본이다.")))
        p["learning_terms"] = [{"term": "캐시", "introduced_by": "받은 답을 잠시 저장한 사본이다."}]
        self.assertEqual(run_page(p)[1], [])

    def test_supplement_code_output_is_really_executed(self):
        code = {"kind": "code", "lang": "python", "src": "print(2 + 3)",
                "output": "5", "verified": "measured"}
        p = page(prose("계산 결과를 확인한다."), supplement(code))
        self.assertEqual(run_page(p)[1], [])
        code["output"] = "6"
        self.assertIn("출력 불일치", run_page(p)[1][0][1])

    def test_optional_extra_can_build_on_supplement(self):
        p = page(prose("주소 결과를 읽는다."),
                 supplement(prose("캐시는 받은 답을 잠시 저장한 사본이다.")))
        p.pop('walkthrough')
        p['learning_terms'] = [{'term': '캐시', 'introduced_by': '받은 답을 잠시 저장한 사본이다.'}]
        p['extra_tasks'] = [{'title': '더 확인하기', 'text': '캐시의 주소도 비교한다.'}]
        self.assertEqual(check_page(p)[1], [])
        self.assertEqual(check_structure(p)[1], [])

    def test_image_labels_inside_supplement_still_need_introduction(self):
        p = page(prose("주소 결과를 읽는다."), supplement(
            {"kind": "image", "src": "example.png", "text_content": "캐시"},
            prose("캐시는 받은 답을 저장한 사본이다.")))
        p["learning_terms"] = [{"term": "캐시", "introduced_by": "받은 답을 저장한 사본이다."}]
        self.assertIn("설명 전 사용", check_page(p)[1][0][1])
        del p["sections"][0]["body"][1]["body"][0]["text_content"]
        self.assertTrue(any("text_content" in path for path, _ in check_page(p)[1]))

    def test_nested_supplement_and_task_are_rejected(self):
        for child in (supplement(prose("추가")), {"kind": "task", "task_type": "action", "instruction": "실행한다."}):
            self.assertTrue(any("보충 안에" in e for e in validate(page(supplement(child)))))

    def test_repeated_explanation_is_advisory_but_task_setup_is_allowed(self):
        text = "원본에는 담당자가 등록한 주소가 있고 저장한 사본은 일정 시간이 지나면 다시 확인한다. " * 3
        p = page(prose(text), prose(text))
        self.assertEqual(check_structure(p)[1], [])
        self.assertTrue(any("반복" in why for _, why in check_structure(p)[2]))
        p = page(prose(text), {"kind": "task", "task_type": "action", "instruction": "비교한다.",
                              "setup_elements": [prose(text)]})
        self.assertEqual(check_structure(p)[2], [])

    def test_stale_and_reordered_toc_entries_are_reported(self):
        p = page(prose("주소를 읽는다."))
        self.assertEqual(check_structure(p)[2], [])
        p["toc"] = ["확인", "질문", "없는 제목"]
        self.assertEqual(len(check_structure(p)[2]), 2)


if __name__ == "__main__":
    unittest.main()
