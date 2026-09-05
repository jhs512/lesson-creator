import sys
import unittest
import subprocess
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lesson_render import esc, render_task


class ProseRenderingTests(unittest.TestCase):
    def test_citation_is_not_escaped_into_literal_brackets(self):
        source = '풀이 [응답의 의미 — RFC 7505](https://www.rfc-editor.org/rfc/rfc7505.html#section-3)'
        self.assertEqual(esc(source), source)

    def test_code_and_literal_brackets_still_keep_their_distinct_meaning(self):
        self.assertEqual(esc('`[code_value]`와 [설명]'), '`[code_value]`와 \\[설명\\]')

    def test_link_target_underscores_are_preserved(self):
        source = '[자료](https://example.test/a_b)와 [일반]'
        self.assertEqual(esc(source), '[자료](https://example.test/a_b)와 \\[일반\\]')

    def test_report_start_label_does_not_claim_execution(self):
        task = {'task_type':'challenge', 'title':'보고서', 'instruction':'작성하자.',
                'element':{'kind':'code','lang':'markdown','src':'# 제목'},
                'start_label':'편집기에 복사하자.', 'goal_output':'# 완성',
                'answer':{'element':{'kind':'code','lang':'markdown','src':'# 완성'}}}
        rendered = '\n'.join(render_task(task, 1))
        self.assertIn('편집기에 복사하자.', rendered)
        self.assertNotIn('그대로 실행되는 상태', rendered)

    def test_linter_rejects_notion_nested_citation_artifact(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'sample.md'
            path.write_text('[근거]([https://www.rfc-editor.org/rfc/rfc7505](https://www.rfc-editor.org/rfc/rfc7505))')
            result = subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1] / 'lesson_lint.py'), str(path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('출처 링크 중첩', result.stdout)


if __name__ == '__main__':
    unittest.main()
