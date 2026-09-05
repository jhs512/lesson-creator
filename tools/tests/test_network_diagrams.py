"""Focused checks for the diagram generator's sharing/portability contract."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from PIL import Image

SCRIPT=Path(__file__).resolve().parents[1]/'build_network_diagrams.py'
spec=importlib.util.spec_from_file_location('network_diagrams', SCRIPT)
diagrams=importlib.util.module_from_spec(spec)
spec.loader.exec_module(diagrams)


class NetworkDiagramTests(unittest.TestCase):
    def test_import_does_not_create_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            subprocess.run([
                sys.executable, '-c',
                'import runpy; runpy.run_path(__import__("sys").argv[1])',
                str(SCRIPT),
            ], cwd=temporary, check=True, capture_output=True)
            self.assertEqual(list(Path(temporary).iterdir()), [])

    def test_missing_explicit_font_is_reported_before_writing(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary)/'output'
            result=subprocess.run([
                sys.executable, str(SCRIPT), '--font',
                str(Path(temporary)/'missing.ttf'), '--out', str(output),
            ], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('Cannot read font', result.stderr)
            self.assertFalse(output.exists())

    def test_no_detected_font_provides_actionable_error(self):
        with patch.object(diagrams, 'font_candidates', return_value=()):
            with self.assertRaisesRegex(ValueError, r'--font'):
                diagrams.resolve_font()

    def test_svg_uses_selected_font_family_and_custom_output(self):
        try:
            font, family=diagrams.resolve_font()
        except ValueError:
            self.skipTest('No installed Korean font available for rendering.')
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary)/'custom'
            canvas=diagrams.Canvas('sample', '한글 테스트', out=output, font=font)
            self.assertFalse(output.exists())
            canvas.save()
            tree=ET.parse(output/'sample.svg')
            elements=tree.findall('.//{http://www.w3.org/2000/svg}text')
            self.assertTrue(elements)
            self.assertTrue(all(e.get('font-family')==f'{family}, sans-serif' for e in elements))
            with Image.open(output/'sample.png') as rendered:
                self.assertEqual(rendered.size, (1800,1100))

    def test_contact_sheet_ignores_prior_sheet_and_unrelated_images(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary)
            for slug in diagrams.FIGURE_SLUGS:
                Image.new('RGB', (10,10), 'white').save(output/f'{slug}.png')
            # These files must never be opened by the sheet builder.
            (output/'contact_sheet.png').write_text('old sheet placeholder')
            (output/'unrelated.png').write_text('not an image')
            diagrams.make_contact_sheet(output)
            diagrams.make_contact_sheet(output)
            with Image.open(output/'contact_sheet.png') as sheet:
                self.assertEqual(sheet.size, (1400,4900))
            self.assertEqual((output/'unrelated.png').read_text(), 'not an image')


if __name__=='__main__':
    unittest.main()
