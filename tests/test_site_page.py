"""HUN-125 / HUN-127: static release page `site/index.html` in the Graphite Mint theme. Standard library only."""
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site"
PAGE = SITE / "index.html"
THEME = SITE / "theme.css"
COLOUR = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(")

# Spec "Design tokens": name -> value. The values are copied from the spec's :root block.
TOKENS = {
    "--bg": "#121413", "--bg-sunken": "#0E100F", "--bg-hover": "#181B1A",
    "--line-subtle": "#1F2321", "--line": "#262B29", "--line-strong": "#2C3230", "--line-header": "#232826",
    "--text-strong": "#EAEDEA", "--text": "#DCE0DD", "--text-2": "#ABB3AE", "--text-nav": "#B5BCB7",
    "--text-muted": "#8C9590", "--text-dim": "#6E7772",
    "--accent": "#7EDDB0", "--accent-hover": "#B2EDCF",
    "--accent-soft": "rgba(126, 221, 176, 0.09)", "--accent-line": "rgba(126, 221, 176, 0.33)",
    "--on-accent": "#0E100F", "--dot-idle": "#3A413E",
    "--header-h": "64px", "--sidebar-w": "248px", "--content-max": "920px",
}
FONT_LINKS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">',
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
    '<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">',
)
FAMILY = [
    ("Easy Kit", "https://personal-agentic-claude.vercel.app/"),
    ("Easy Memory", "https://easy-memory.vercel.app/"),
    ("Easy Verifier", "https://easy-verifier.vercel.app/"),
]
GITHUB = "https://github.com/thunderkds/easy-memory-mcp"


class _Scan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.hrefs, self.tags = set(), [], []
        self.by_class = {}   # class token -> list of element texts
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
            for token in a.get("class", "").split():
                self.by_class.setdefault(token, []).append("".join(buf).strip())
            if t == tag:
                break

    def with_class(self, tag, token):
        return [a for t, a in self.tags if t == tag and token in a.get("class", "").split()]


class SitePageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = PAGE.read_text(encoding="utf-8")
        cls.css = THEME.read_text(encoding="utf-8")
        cls.scan = _Scan()
        cls.scan.feed(cls.html)
        cls.local_style = re.search(r"<style>(.*?)</style>", cls.html, re.S).group(1)
        cls.all_css = cls.css + cls.local_style

    # AC1 tokens
    def test_theme_root_holds_the_spec_tokens(self):
        root = re.search(r"^:root \{(.*?)^\}", self.css, re.S | re.M).group(1)
        for name, value in TOKENS.items():
            self.assertRegex(root, r"%s:\s*%s;" % (re.escape(name), re.escape(value)), name)

    def test_no_colour_literal_outside_the_token_block(self):
        root_less = re.sub(r"^:root \{.*?^\}", "", self.css, flags=re.S | re.M)
        # The spec's ::selection rule is the one component rule that carries an rgba() value.
        self.assertEqual(COLOUR.findall(root_less), ["rgba("])
        self.assertIn("::selection { background: rgba(126, 221, 176, 0.25)", root_less)
        self.assertEqual(COLOUR.findall(self.local_style), [])
        rest = re.sub(r"<style>.*?</style>", "", self.html, flags=re.S)
        rest = re.sub(r'<link rel="icon"[^>]*>', "", rest)  # favicon excepted (token-equal values, percent-encoded)
        self.assertEqual(COLOUR.findall(rest), [])
        others = [p.name for p in SITE.iterdir() if p.name not in ("index.html", "theme.css")]
        self.assertEqual(others, [])

    def test_page_links_theme_css(self):
        self.assertTrue(any(t == "link" and a.get("href") == "theme.css" and a.get("rel") == "stylesheet"
                            for t, a in self.scan.tags))

    # AC2 fonts, no other external request
    def test_only_the_spec_font_links_are_external(self):
        for link in FONT_LINKS:
            self.assertIn(link, self.html)
        for tag, a in self.scan.tags:
            if tag == "script":
                self.assertNotIn("src", a)
            if tag == "link":
                href = a.get("href", "")
                external = href.startswith("http")
                if external:
                    self.assertTrue(href.startswith(("https://fonts.googleapis.com", "https://fonts.gstatic.com")), href)
            if tag in ("img", "iframe", "source", "video", "audio", "embed", "object"):
                self.fail("unexpected external resource tag " + tag)
        self.assertNotRegex(self.all_css, r"@import|url\(\s*['\"]?https?:")
        self.assertEqual(sorted(set(re.findall(r'font-family:[^;]*', self.local_style))), [])

    # AC3 no gradient, glow, shadow, blur, colour animation, rings
    def test_no_forbidden_effects(self):
        for word in ("gradient", "text-shadow", "box-shadow", "backdrop-filter", "filter:",
                     "transition", "animation", "@keyframes"):
            self.assertNotIn(word, self.all_css, word)
        self.assertNotIn("<circle", self.html)
        self.assertNotIn("stroke-dasharray", self.html)
        self.assertNotIn("<linearGradient", self.html)
        self.assertEqual(self.scan.with_class("div", "ring"), [])

    def test_type_rules(self):
        self.assertNotRegex(self.all_css, r"font-weight:\s*[7-9]00|font:\s*[7-9]00")
        self.assertNotIn("text-transform", self.all_css)

    # AC4 shell
    def test_header_shell_and_family_nav(self):
        html = self.html
        self.assertIn("memory kit · v0.1.0 prototype", html)
        header = re.search(r'<header class="site-header">(.*?)</header>', html, re.S).group(1)
        self.assertRegex(header, r'<svg class="glyph"[^>]*aria-hidden="true"')
        self.assertIn("<span>Easy Memory</span>", header)
        nav = re.search(r'<nav class="family" aria-label="Easy Kit family">(.*?)</nav>', header, re.S).group(1)
        links = re.findall(r'<a class="(fam|btn btn-secondary)" href="([^"]+)"([^>]*)>([^<]+)</a>', nav)
        self.assertEqual([(l[3], l[1]) for l in links], FAMILY + [("GitHub", GITHUB)])
        current = [l[3] for l in links if 'aria-current="page"' in l[2]]
        self.assertEqual(current, ["Easy Memory"])
        self.assertEqual(header.count("aria-current"), 1)

    def test_drawer_repeats_the_family_nav(self):
        drawer = re.search(r'<nav class="family drawer-family"[^>]*>(.*?)</nav>', self.html, re.S).group(1)
        for name, url in FAMILY:
            self.assertIn('href="%s"' % url, drawer)
        self.assertEqual(drawer.count('aria-current="page"'), 1)

    def test_sidebar_groups_and_items(self):
        self.assertEqual(self.scan.by_class["group-label"], ["// overview", "// guide", "// reference"])
        side = re.search(r'<nav id="site-nav".*?</nav>', self.html, re.S).group(0)
        items = re.findall(r'<a href="#([^"]+)">([^<]+)</a>', side)
        self.assertEqual(items, [
            ("what", "What it is"), ("context", "Context"), ("how", "How it works"),
            ("run", "Install"), ("use", "Use it"), ("rollback", "Remove it"),
            ("numbers", "Measured"), ("limits", "Known limits"), ("notes", "Release notes"),
        ])

    def test_section_order_and_anchors(self):
        sections = re.findall(r'<section id="([^"]+)">', self.html)
        self.assertEqual(sections, ["what", "context", "how", "run", "use", "rollback", "numbers", "limits", "notes"])
        self.assertIn('<body id="top">', self.html)

    def test_in_page_links_have_targets(self):
        self.assertTrue(self.scan.hrefs)
        missing = [h for h in self.scan.hrefs if h not in self.scan.ids]
        self.assertEqual(missing, [])

    # AC5 Easy Memory components
    def test_hero(self):
        self.assertEqual(self.scan.by_class["eyebrow"], ["> per-repo memory for claude code"])
        self.assertRegex(self.html, r'<h1>Easy Memory</h1>')
        self.assertRegex(self.html, r'<a class="btn btn-primary" href="%s"[^>]*>View the source on GitHub</a>' % re.escape(GITHUB))
        self.assertRegex(self.html, r'<a class="btn btn-secondary" href="#run">Install</a>')

    def test_highlights_strip_has_three_cells(self):
        strip = re.search(r'<ul class="strip c3"[^>]*>(.*?)</ul>', self.html, re.S).group(1)
        self.assertEqual(re.findall(r'<strong class="step-title">([^<]+)</strong>', strip),
                         ["Local", "Hooks and MCP", "Measured on yourself"])

    def test_how_it_works_flow_is_an_accessible_svg(self):
        flows = [a for t, a in self.scan.tags if t == "svg" and "flow" in a.get("class", "").split()]
        self.assertEqual(len(flows), 2)  # wide and tall layout of the same flow
        for a in flows:
            self.assertEqual(a.get("role"), "img")
            self.assertTrue(len(a.get("aria-label", "")) > 80)
            self.assertNotIn("aria-hidden", a)
        flow = re.search(r'<svg class="flow flow-wide".*?</svg>', self.html, re.S).group(0)
        titles = re.findall(r'<text class="fl-title"[^>]*>([^<]+)</text>', flow)
        self.assertEqual(titles, ["Your answer", "Stop hook", "Note store", "Prompt hook", "Next prompt",
                                  "Word weights", "MCP server"])
        # The main loop is mint (four arrows + the legend sample); side paths use the neutral line class.
        self.assertEqual(flow.count('class="fl-main-line"'), 5)
        self.assertEqual(flow.count('class="fl-line"'), 3)

    def test_experiment_cards(self):
        cards = self.scan.with_class("article", "card")
        self.assertEqual(len(cards), 3)
        self.assertEqual([("is-highlight" in c["class"].split()) for c in cards], [False, False, True])
        self.assertEqual(self.scan.by_class["big"], ["−58%", "~−15%", "−29% / −27%"])
        self.assertEqual(self.scan.by_class["exp"], ["exp 01", "exp 02", "exp 03 · shipped"])
        self.assertEqual(self.scan.by_class["shipped"], ["exp 03 · shipped"])

    def test_install_stepper_has_codeboxes(self):
        self.assertEqual(self.scan.by_class["step-no"], ["01", "02", "03", "end"])
        stepper = re.search(r'<ol class="stepper"[^>]*>(.*?)</ol>', self.html, re.S).group(1)
        self.assertEqual(re.findall(r"<h3>([^<]+)</h3>", stepper), ["Get the code", "Preview", "Install", "Check"])
        self.assertEqual(stepper.count('class="codebox"'), 3)
        self.assertEqual(len(self.scan.with_class("div", "codebox")), 4)
        self.assertEqual(len(self.scan.by_class["prompt"]), 8)
        self.assertEqual(set(self.scan.by_class["prompt"]), {"$"})
        self.assertEqual(len([a for t, a in self.scan.tags if t == "button" and "data-copy" in a]), 4)

    def test_use_it_switch_strip_and_commands(self):
        days = re.search(r'<ol class="days"[^>]*>(.*?)</ol>', self.html, re.S).group(1)
        self.assertEqual(re.findall(r'<span class="d-state">(on|off)</span>', days), ["on", "off"] * 4)
        cmds = re.search(r'<ul class="cmds"[^>]*>(.*?)</ul>', self.html, re.S).group(1)
        self.assertEqual(cmds.count("<li>"), 4)

    def test_remove_it_triggers_are_short_labels(self):
        sec = re.search(r'<section id="rollback">(.*?)</section>', self.html, re.S).group(1)
        chips = re.findall(r'<li class="chip">([^<]+)</li>', sec)
        self.assertEqual(chips, ["hook error on every prompt", "prompts ≥ 1 s",
                                 "MCP fails in claude mcp list", "permission prompt on open"])

    def test_measured_bar_chart_and_stats(self):
        bars = re.findall(r'<div class="bar" role="img" aria-label="([^"]+)"><span style="width:([\d.]+)%"></span></div>', self.html)
        self.assertEqual(bars, [("Prompt hook p95: 0.212 s of a 1 s limit", "21.2"),
                                ("Stop hook p95: 0.066 s of a 2 s limit", "3.3")])
        self.assertAlmostEqual(0.212 / 1 * 100, 21.2)
        self.assertAlmostEqual(0.066 / 2 * 100, 3.3)
        self.assertEqual(self.scan.by_class["num"], ["0.024 s", "1.69 MB", "307"])
        self.assertRegex(self.html, r'<ul class="strip stats c3">')

    def test_known_limits_status_is_plain_words(self):
        self.assertEqual(self.scan.by_class["status"], ["open", "open", "open", "accepted", "to run"])
        self.assertNotRegex(self.html, r'class="tag')
        self.assertNotIn(".tag", self.local_style)

    # HUN-127: container, no task IDs, no "built" section, folded detail
    def test_container_stops_growing(self):
        self.assertRegex(self.local_style, r"--container-max:\s*1280px")
        self.assertRegex(self.local_style, r"\.container\s*\{[^}]*max-width:var\(--container-max\)[^}]*margin:0 auto")
        self.assertIn('<div class="header-inner container">', self.html)
        self.assertIn('<div class="shell container">', self.html)

    def test_no_task_ids_and_no_built_section(self):
        self.assertNotIn("HUN-", self.html)
        self.assertNotIn("#built", self.html)
        self.assertNotIn('id="built"', self.html)
        self.assertNotIn("How it was built", self.html)

    def test_release_notes_groups(self):
        notes = re.search(r'<section id="notes">(.*?)</section>', self.html, re.S).group(1)
        self.assertEqual(re.findall(r"<dt>([^<]+)</dt>", notes), ["save", "recall", "control", "measure", "install"])
        self.assertNotIn("<details", notes)

    def test_each_section_folds_its_detail(self):
        for sid in ("what", "context", "how", "run", "use", "rollback", "numbers", "limits"):
            sec = re.search(r'<section id="%s">(.*?)</section>' % sid, self.html, re.S).group(1)
            self.assertEqual(sec.count('<details class="more">'), 1, sid)
            self.assertEqual(sec.count("<summary>More detail</summary>"), 1, sid)
            self.assertTrue(sec.rstrip().endswith("</details>"), sid)  # at the end of the section

    # AC6 content kept (spot checks; the full fact inventory is in the TASK_REVIEW evidence)
    def test_content_kept(self):
        for text in ("Coding agents pay again for what an earlier session already found out.",
                     "python3 easy_memory.py install --dry-run",
                     "1.69 MB", "Independent end-to-end smoke and latency checks.",
                     "docs/RELEASE_v0.1.0.md", "7,831-file repo, 200 notes",
                     "A 400 MB transcript used 808 MB.", "settings.json.easy-memory.bak.&lt;time&gt;"):
            self.assertIn(text, self.html)

    # AC7 responsive
    def test_responsive_rules(self):
        css = self.local_style
        self.assertIn("@media (max-width:1023px)", css)
        self.assertIn("@media (max-width:719px)", css)
        self.assertIn("min-height:44px", css)
        self.assertIn("overflow-x:auto", self.css.replace(": ", ":") + css)
        for table_wrap in self.scan.with_class("div", "table-wrap"):
            self.assertEqual(table_wrap.get("tabindex"), "0")
            self.assertTrue(table_wrap.get("aria-label"))

    # AC8 accessibility
    def test_skip_link_is_first_and_targets_main(self):
        first_a = next(a for t, a in self.scan.tags if t == "a")
        self.assertEqual(first_a.get("class"), "skip-link")
        self.assertEqual(first_a.get("href"), "#main")
        self.assertIn("main", self.scan.ids)

    def test_focus_ring_and_decorative_svg(self):
        self.assertIn(":focus-visible { outline: 2px solid var(--accent)", self.css)
        svgs = [a for t, a in self.scan.tags if t == "svg"]
        self.assertTrue(svgs)
        for a in svgs:  # the flow diagrams are role="img" with a label; every other svg is decorative
            if a.get("role") == "img":
                self.assertTrue(a.get("aria-label"))
            else:
                self.assertEqual(a.get("aria-hidden"), "true")

    def test_buttons_have_names(self):
        for m in re.finditer(r"<button([^>]*)>([^<]*)</button>", self.html):
            self.assertTrue(m.group(2).strip() or "aria-label" in m.group(1))
        for m in re.finditer(r'<button[^>]*data-copy[^>]*aria-label="(Copy[^"]*)"[^>]*>Copy</button>', self.html):
            self.assertTrue(m.group(1).startswith("Copy"))  # label in name
        self.assertEqual(len(re.findall(r'<button[^>]*data-copy', self.html)), 4)

    def test_primary_button_text_stays_on_accent(self):
        self.assertIn("a.btn-primary:hover { color:var(--on-accent); }", self.local_style)


if __name__ == "__main__":
    unittest.main()
