"""HUN-123: static release page `site/index.html`. Standard library only."""
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

PAGE = Path(__file__).resolve().parent.parent / "site" / "index.html"
COLOUR = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(")


class _Scan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.hrefs, self.tags = set(), [], []
        self.text_of_n = []
        self._stack = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append((tag, a))
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "a" and a.get("href", "").startswith("#"):
            self.hrefs.append(a["href"][1:])
        self._stack.append((tag, a, []))

    def handle_data(self, data):
        for _, _, buf in self._stack:
            buf.append(data)

    def handle_endtag(self, tag):
        while self._stack:
            t, a, buf = self._stack.pop()
            if "n" in a.get("class", "").split():
                self.text_of_n.append("".join(buf).strip())
            if t == tag:
                break


class SitePageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = PAGE.read_text(encoding="utf-8")
        cls.scan = _Scan()
        cls.scan.feed(cls.html)

    def _style(self):
        return re.search(r"<style>(.*?)</style>", self.html, re.S).group(1)

    def test_no_colour_literal_outside_root(self):
        style = self._style()
        outside = re.sub(r"(?m)^  :root \{.*?^  \}", "", style, flags=re.S)
        self.assertNotEqual(outside, style, ":root block not found")
        self.assertEqual(COLOUR.findall(outside), [])
        rest = re.sub(r"<style>.*?</style>", "", self.html, flags=re.S)
        rest = re.sub(r'<link rel="icon"[^>]*>', "", rest)  # favicon excepted
        self.assertEqual(COLOUR.findall(rest), [])

    def test_in_page_links_have_targets(self):
        self.assertTrue(self.scan.hrefs)
        missing = [h for h in self.scan.hrefs if h not in self.scan.ids]
        self.assertEqual(missing, [])

    def test_rings_are_decorative_and_value_is_text(self):
        rings = [m for m in re.finditer(r'<div class="ring">(.*?)</div></div>', self.html, re.S)]
        self.assertGreaterEqual(len(rings), 1)
        for m in rings:
            inner = m.group(1)
            self.assertIn('<svg', inner)
            self.assertRegex(inner, r'<svg[^>]*aria-hidden="true"')
            self.assertNotIn("<text", inner)  # value is not drawn in the SVG
            self.assertRegex(inner, r'</svg><div class="n">[^<]+$')

    def test_measured_values_are_text(self):
        for value in ("0.212 s", "0.066 s", "1.69 MB", "307"):
            self.assertIn(value, self.scan.text_of_n)

    def test_no_external_resources(self):
        for tag, a in self.scan.tags:
            if tag == "script":
                self.assertNotIn("src", a)
            if tag == "link" and a.get("rel") == "stylesheet":
                self.fail("external stylesheet")
        self.assertNotRegex(self.html, r"@import|url\(\s*['\"]?https?:")


if __name__ == "__main__":
    unittest.main()
