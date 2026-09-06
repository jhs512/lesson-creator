"""Validate bundled lessons and produce self-contained local preview folders."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    output = ROOT / 'build/day3'
    output.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT/'examples/day3/assets', output/'assets', dirs_exist_ok=True)
    for source in sorted((ROOT/'examples/day3').glob('lesson*.json')):
        name = source.stem
        page = json.loads(source.read_text(encoding='utf-8'))
        commands = [
            ['lesson_render.py', str(source), str(output/f'{name}.md')],
            ['lesson_harness.py', str(source)],
            ['lesson_lint.py', str(output/f'{name}.md'), *(['--role', page['lesson_role']] if page.get('lesson_role') else [])],
            ['render_lesson_preview.py', str(output/f'{name}.md'), str(output/f'{name}.html'), '--title', page['title']],
        ]
        for tool, *args in commands:
            result = subprocess.run([sys.executable, str(ROOT/'tools'/tool), *args], capture_output=True, text=True)
            (output/f'{name}.{tool[:-3]}.txt').write_text(result.stdout+result.stderr, encoding='utf-8')
            if result.returncode:
                print(result.stdout+result.stderr)
                return result.returncode
            print(name, tool, result.stdout.strip().splitlines()[-1])
    print(f'Preview files: {output}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
