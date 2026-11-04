"""HUN-125 / HUN-127 / HUN-130 / HUN-204: static release page `site/index.html` in the Graphite Mint theme (spec rev 25, neon layer). Standard library only."""
import hashlib
import re
import subprocess
import unittest
from html.parser import HTMLParser
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site"
PAGE = SITE / "index.html"
THEME = SITE / "theme.css"
COLOUR = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(")

# Spec rev 25 "Design tokens": name -> value. The values are copied from the spec's :root block.
TOKENS = {
    "--bg": "#121413", "--bg-sunken": "#0E100F", "--bg-hover": "#181B1A",
    "--line-subtle": "#1F2321", "--line": "#262B29", "--line-strong": "#2C3230", "--line-header": "#232826",
    "--text-strong": "#EAEDEA", "--text": "#DCE0DD", "--text-2": "#ABB3AE", "--text-nav": "#B5BCB7",
    "--text-muted": "#8C9590", "--text-dim": "#6E7772",
    "--accent": "#7EDDB0", "--accent-hover": "#B2EDCF",
    "--neon": "#3CF5A8", "--neon-soft": "rgba(60, 245, 168, 0.08)", "--neon-line": "rgba(60, 245, 168, 0.35)",
    "--neon-bar": "rgba(60, 245, 168, 0.30)",
    "--glow-text": "0 0 12px rgba(60, 245, 168, 0.35)",
    "--glow-box": "0 0 0 1px rgba(60, 245, 168, 0.25), 0 0 18px rgba(60, 245, 168, 0.25)",
    "--glow-dot": "0 0 8px #3CF5A8",
    "--glow-line": "drop-shadow(0 0 3px rgba(60, 245, 168, 0.6))",
    "--on-accent": "#0E100F", "--dot-idle": "#3A413E",
    "--header-h": "64px", "--sidebar-w": "248px", "--content-max": "920px",
}
FONT_LINKS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">',
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
    '<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">',
)
FAMILY = [
    ("Easy Kit", "https://easy-kits.vercel.app/"),
    ("Easy Verifier", "https://easy-verifier.vercel.app/"),
    ("Easy UI", "https://easy-ui-mcp.vercel.app/"),
    ("Easy Memory", "https://easy-memory.vercel.app/"),
    ("Easy Personal", "https://easy-personal.vercel.app/"),
]
GITHUB = "https://github.com/thunderkds/easy-memory-mcp"
# The Easy Kit link used to point here; spelled in two parts so this file does not hold the string it checks for.
OLD_KIT_HOST = "personal-agentic-claude" + ".vercel.app"
EASY_PERSONAL = "https://easy-personal.vercel.app/"
SECTION_ORDER = ["problem", "context", "how", "run", "use", "dashboard", "rollback", "numbers", "limits"]
# Visible words (the wide pictures, not the hidden tall copies) outside <details> on the page before HUN-204 (pictures carry the explanation: at most 150 more).
VISIBLE_WORDS_BEFORE = 794
# This repo's store on 3 Nov 2026 (counts only): notes saved per day for the 30 days 5 Oct .. 3 Nov.
SPARK_NOTES = [0] * 24 + [63, 23, 41, 0, 3, 13]
# sha256 of the two theme.css blocks as the spec rev 25 export gives them (tokens `:root`, then component CSS).
SPEC_ROOT_SHA256 = "a7ba10aeab3bc94a5184eab59c5e2574df0a108d8b3d26890883619170e29d45"
SPEC_COMPONENTS_SHA256 = "730b8e5a36ef56cf87fb2b02288241d93bee292a398b6f22442abf947e7a5e3a"
# Neon highlights table: the only selectors whose rules may use a --neon* or --glow-* token.
NEON_SELECTORS = {
    # theme.css (spec component block)
    ".btn-primary", ".codebox .prompt", ".strip .num", ".step-no", ".card.is-highlight", ".bar > span",
    # page rules
    "html.no-glow", ".glyph", '.fam[aria-current="page"]::before', ".sidebar ul a.active", ".eyebrow",
    ".bar-val", ".fl-no", ".fl-main-line",
    ".st-mark", ".st-line", ".stepper > li",
    # HUN-204: the memory lane's token bar, the soft chart bars, the sparkline (today's bar is the current one)
    ".fl-bar-on", ".bar.is-soft > span", ".sp-bar", ".sp-bar.is-today",
}
# Soft mint is for ordinary links, hover and the focus ring only.
ACCENT_SELECTORS = {"a", "a:hover", ":focus-visible", ".skip-link"}
GLOW_VALUES = {"none", "var(--glow-text)", "var(--glow-box)", "var(--glow-dot)", "var(--glow-line)",
               "inset 0 0 0 1px var(--neon-line)", "brightness(1.08)"}


def _luminance(hex_colour):
    channels = [int(hex_colour[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def _contrast(a, b):
    la, lb = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _rules(css):
    """(selector, body) pairs of every rule in `css`, comments dropped, :root excluded."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"^:root \{.*?^\}", "", css, flags=re.S | re.M)
    out = []
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        for selector in m.group(1).split(","):
            out.append((" ".join(selector.split()), m.group(2)))
    return out


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


def _plain_text(markup):
    """Tags replaced by a space, whitespace collapsed: the text a reader sees, in order."""
    text = " ".join(re.sub(r"<[^>]+>", " ", markup).split())
    return re.sub(r"\s+([,.;:)])", r"\1", re.sub(r"\(\s+", "(", text))


class _Words(HTMLParser):
    """Counts the words in the body outside <details>, <style> and <script>. SVG text counts; the tall copy of a picture
    is the same words again (shown only below 800 px), so it does not."""
    def __init__(self):
        super().__init__()
        self.count, self._skip, self._body, self._tall = 0, 0, False, False

    def handle_starttag(self, tag, attrs):
        if tag == "body":
            self._body = True
        if tag in ("details", "style", "script"):
            self._skip += 1
        if tag == "svg" and "flow-tall" in dict(attrs).get("class", "").split():
            self._tall = True

    def handle_endtag(self, tag):
        if tag in ("details", "style", "script"):
            self._skip -= 1
        if tag == "svg":
            self._tall = False

    def handle_data(self, data):
        if self._body and not self._skip and not self._tall:
            self.count += len(data.split())


class SitePageTest(unittest.TestCase):
    def section(self, sid):
        return re.search(r'<section id="%s">(.*?)</section>' % sid, self.html, re.S).group(1)

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

    def test_theme_css_is_byte_identical_to_spec_rev_25(self):
        cut = self.css.index("\n\nhtml { background")
        root, components = self.css[:cut], self.css[cut + 2:]
        self.assertEqual(hashlib.sha256(root.encode()).hexdigest(), SPEC_ROOT_SHA256)
        self.assertEqual(hashlib.sha256(components.encode()).hexdigest(), SPEC_COMPONENTS_SHA256)

    def test_no_undefined_or_removed_custom_property(self):
        declared = set(re.findall(r"(--[a-z0-9-]+)\s*:", self.all_css))
        used = set(re.findall(r"var\((--[a-z0-9-]+)", self.all_css + self.html))
        self.assertEqual(sorted(used - declared), [])
        for gone in ("--accent-soft", "--accent-line"):
            self.assertNotIn(gone, self.all_css + self.html)

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

    # AC3 no gradient, blur, colour animation, rings; glow only through the glow tokens
    def test_no_forbidden_effects(self):
        for word in ("gradient", "backdrop-filter", "transition", "animation", "@keyframes"):
            self.assertNotIn(word, self.all_css, word)
        self.assertNotIn("<circle", self.html)
        self.assertNotIn("stroke-dasharray", self.html)
        self.assertNotIn("<linearGradient", self.html)
        self.assertEqual(self.scan.with_class("div", "ring"), [])

    # HUN-130: neon highlight layer
    def test_shadows_and_filters_use_only_the_glow_tokens(self):
        found = re.findall(r"(?<![-\w])(text-shadow|box-shadow|filter)\s*:\s*([^;}]+)", self.all_css)
        self.assertTrue(found)
        for prop, value in found:
            self.assertIn(value.strip(), GLOW_VALUES, prop)

    def test_neon_and_glow_only_on_the_highlight_selectors(self):
        used = set()
        for selector, body in _rules(self.css) + _rules(self.local_style):
            if re.search(r"var\(--(neon|glow)", body):
                used.add(selector)
                self.assertIn(selector, NEON_SELECTORS, selector)
            if re.search(r"var\(--accent(?!-hover)", body):
                self.assertIn(selector, ACCENT_SELECTORS, selector)
        self.assertEqual(used, NEON_SELECTORS - {"html.no-glow"})  # the override sets the tokens to none
        style_attrs = re.findall(r'style="([^"]*)"', self.html)
        self.assertTrue(all(re.fullmatch(r"width:[\d.]+%", s) for s in style_attrs), style_attrs)

    def test_neon_treatments_match_the_table(self):
        local, theme = {}, {}
        for table, css in ((local, self.local_style), (theme, self.css)):
            for selector, body in _rules(css):
                table[selector] = table.get(selector, "") + body
        active = local[".sidebar ul a.active"]
        for part in ("background:var(--neon-soft)", "color:var(--neon)", "text-shadow:var(--glow-text)",
                     "box-shadow:inset 0 0 0 1px var(--neon-line)"):
            self.assertIn(part, active)
        self.assertIn("background:var(--neon); box-shadow:var(--glow-dot)", local['.fam[aria-current="page"]::before'])
        self.assertIn("color:var(--neon)", local[".glyph"])
        self.assertIn("color:var(--neon); text-shadow:var(--glow-text)", local[".eyebrow"])
        self.assertIn("stroke:var(--neon)", local[".fl-main-line"])
        self.assertIn("filter:var(--glow-line)", local[".fl-main-line"])
        self.assertIn("filter:var(--glow-line)", local[".st-line"])
        self.assertIn("box-shadow:var(--glow-dot)", local[".st-mark"])
        self.assertIn("fill:var(--neon); text-shadow:var(--glow-text)", local[".fl-no"])
        self.assertIn("color:var(--neon); text-shadow:var(--glow-text)", local[".bar-val"])
        self.assertEqual(local[".fl-bar-on"].strip(), "fill:var(--neon);")
        self.assertEqual(local[".bar.is-soft > span"].replace(" ", ""), "background:var(--neon-bar);box-shadow:none;")
        self.assertEqual(local[".sp-bar"].strip(), "fill:var(--neon-bar);")
        self.assertEqual(local[".sp-bar.is-today"].strip(), "fill:var(--neon);")
        self.assertIn("background: var(--neon)", theme[".btn-primary"])
        self.assertIn("box-shadow: var(--glow-box)", theme[".btn-primary"])
        self.assertIn("filter: brightness(1.08)", theme[".btn-primary:hover"])
        self.assertIn("border-color: var(--neon-line)", theme[".card.is-highlight"])
        self.assertIn("background: var(--neon); box-shadow: var(--glow-dot)", theme[".bar > span"])
        self.assertEqual(theme[".codebox .prompt"].split(";")[0].strip(), "color: var(--neon)")
        self.assertNotIn("glow", theme[".codebox .prompt"])

    def test_no_glow_class_switches_every_glow_token_off(self):
        m = re.search(r"html\.no-glow\s*\{([^}]*)\}", self.local_style)
        self.assertIsNotNone(m)
        self.assertEqual(sorted(re.findall(r"(--glow-[a-z]+)\s*:\s*none", m.group(1))),
                         ["--glow-box", "--glow-dot", "--glow-line", "--glow-text"])
        glow_tokens = re.findall(r"(--glow-[a-z]+)\s*:", re.search(r"^:root \{(.*?)^\}", self.css, re.S | re.M).group(1))
        self.assertEqual(sorted(glow_tokens), ["--glow-box", "--glow-dot", "--glow-line", "--glow-text"])
        self.assertNotIn("no-glow", self.html.split("<body")[1].split("<script>")[0])  # opt-in by the user, never preset

    def test_neon_contrast_holds(self):
        tokens = {"--bg": "#121413", "--neon": "#3CF5A8", "--on-accent": "#0E100F"}
        self.assertGreaterEqual(_contrast(tokens["--neon"], tokens["--bg"]), 4.5)
        self.assertGreaterEqual(_contrast(tokens["--on-accent"], tokens["--neon"]), 4.5)

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
        links = re.findall(r'<a class="(fam|btn btn-secondary)" href="([^"]+)"([^>]*)>([^<]+)</a>', drawer)
        self.assertEqual([(l[3], l[1]) for l in links], FAMILY + [("GitHub", GITHUB)])
        current = [l[3] for l in links if 'aria-current="page"' in l[2]]
        self.assertEqual(current, ["Easy Memory"])
        self.assertEqual(drawer.count('aria-current="page"'), 1)

    def test_five_link_header_family_moves_to_sidebar_below_1100(self):
        # Five family links + brand + version pill + GitHub need ~1083px; below 1100 the header copy hides and the
        # sidebar/drawer copy shows instead, so the links never overlap or clip the header.
        block = re.search(r"@media \(max-width:1099px\) \{(.*?)\n  \}", self.local_style, re.S)
        self.assertIsNotNone(block, "no (max-width:1099px) block")
        rules = dict(_rules(block.group(1)))
        self.assertIn("display:none", rules[".site-header .family"])
        self.assertIn("display:flex", rules[".drawer-family"])
        self.assertIn("flex-direction:column", rules[".drawer-family"])

    def test_sidebar_groups_and_items(self):
        self.assertEqual(self.scan.by_class["group-label"], ["// overview", "// guide", "// reference"])
        side = re.search(r'<nav id="site-nav".*?</nav>', self.html, re.S).group(0)
        items = re.findall(r'<a href="#([^"]+)">([^<]+)</a>', side)
        self.assertEqual(items, [
            ("problem", "Problem and solution"), ("context", "Context"), ("how", "How it works"),
            ("run", "Install"), ("use", "Use it"), ("dashboard", "See it in Easy Personal"),
            ("rollback", "Remove it"), ("numbers", "Measured"), ("limits", "Known limits"),
        ])
        groups = re.findall(r'<p class="group-label"[^>]*>([^<]+)</p>\s*<ul[^>]*>(.*?)</ul>', side, re.S)
        self.assertEqual([(g, re.findall(r'href="#([^"]+)"', ul)) for g, ul in groups], [
            ("// overview", ["problem", "context", "how"]),
            ("// guide", ["run", "use", "dashboard", "rollback"]),
            ("// reference", ["numbers", "limits"]),
        ])

    def test_section_order_and_anchors(self):
        sections = re.findall(r'<section id="([^"]+)">', self.html)
        self.assertEqual(sections, SECTION_ORDER)
        main = re.search(r"<main.*?</main>", self.html, re.S).group(0)
        self.assertEqual(len(re.findall(r"<section\b", main)), len(SECTION_ORDER))  # scroll-spy reads main > section[id]
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
        self.assertEqual(len(flows), 6)  # three pictures (problem, flow, note), each in a wide and a tall layout
        for a in flows:
            self.assertEqual(a.get("role"), "img")
            self.assertTrue(len(a.get("aria-label", "")) > 80)
            self.assertNotIn("aria-hidden", a)
        flow = re.search(r'<svg class="flow flow-wide".*?</svg>', self.section("how"), re.S).group(0)
        titles = re.findall(r'<text class="fl-title"[^>]*>([^<]+)</text>', flow)
        self.assertEqual(titles, ["Your answer", "Stop hook", "Note store", "Prompt hook", "Next prompt",
                                  "Word weights", "MCP server"])
        # The main loop is mint (four arrows + the legend sample); side paths use the neutral line class.
        self.assertEqual(flow.count('class="fl-main-line"'), 5)
        self.assertEqual(flow.count('class="fl-line"'), 3)

    # HUN-204 AC 1: the Easy Kit link
    def test_easy_kit_link_points_to_easy_kits_and_the_old_host_is_gone(self):
        self.assertEqual(self.html.count('<a class="fam" href="https://easy-kits.vercel.app/">Easy Kit</a>'), 2)  # header + drawer
        self.assertNotIn(OLD_KIT_HOST, self.html)
        root = SITE.parent
        # Tracked files only: git-ignored local logs (memory/event-trace/) may quote the old host.
        # tasks/ guides quote the old host to describe the change.
        tracked = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True,
                                 check=True).stdout.decode().split("\0")
        found = []
        for name in filter(None, tracked):
            if name.startswith("tasks/"):
                continue
            try:
                text = (root / name).read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if OLD_KIT_HOST in text:
                found.append(name)
        self.assertEqual(found, [])

    # HUN-204 AC 2: problem and solution
    def test_problem_and_solution_two_lane_picture(self):
        sec = self.section("problem")
        self.assertIn("<h2>Problem and solution</h2>", sec)
        svgs = re.findall(r"<svg ([^>]*)>(.*?)</svg>", sec, re.S)
        self.assertEqual([("flow flow-wide" in a, "flow flow-tall" in a) for a, _ in svgs], [(True, False), (False, True)])
        for attrs, body in svgs:
            self.assertIn('role="img"', attrs)
            label = re.search(r'aria-label="([^"]+)"', attrs).group(1)
            self.assertIn("Without memory", label)
            self.assertIn("With memory", label)
            text = _plain_text(body)
            self.assertIn("Without memory", text)
            self.assertIn("With memory", text)
            self.assertIn('class="fl-bar"', body)
            self.assertIn('class="fl-bar-on"', body)
            self.assertEqual(body.count('class="fl-main-line"'), 3)  # the memory lane is the neon one
        self.assertEqual(re.findall(r"<p><strong>([^<]+)</strong>", sec), ["Without memory.", "With memory."])
        self.assertEqual(re.findall(r'<li class="chip">([^<]+)</li>', sec),
                         ["notes are data, not instructions", "a hook never blocks you", "nothing written in your repo"])
        self.assertNotIn("What it is", self.html)

    # HUN-204 AC 3: how a note is saved
    def test_how_a_note_is_saved_figure(self):
        sec = self.section("how")
        self.assertEqual(sec.count("<h3>How a note is saved</h3>"), 1)
        self.assertLess(sec.index('class="flow flow-wide"'), sec.index("How a note is saved"))  # under the existing flow
        figure = sec[sec.index("How a note is saved"):]
        svgs = re.findall(r"<svg ([^>]*)>(.*?)</svg>", figure, re.S)
        self.assertEqual(len(svgs), 2)  # wide and tall layout
        for attrs, body in svgs:
            self.assertIn('role="img"', attrs)
            label = re.search(r'aria-label="([^"]+)"', attrs).group(1)
            text = _plain_text(body)
            for word in ("question", "answer", "time", "cited files", "sha256", "CHANGED:", "DELETED:"):
                self.assertIn(word, text, word)
            for word in ("question", "answer", "time", "cited", "sha256", "CHANGED:", "DELETED:"):
                self.assertIn(word, label, word)

    # HUN-204 AC 4: token chart
    def test_context_token_chart(self):
        sec = self.section("context")
        self.assertNotIn('class="cards"', sec)
        self.assertEqual(self.scan.with_class("article", "card"), [])
        chart = re.search(r'<div class="chart">(.*?)</div>\s*<details', sec, re.S).group(1)
        bars = re.findall(r'<div class="(bar[^"]*)" role="img" aria-label="([^"]+)"><span style="width:([\d.]+)%"></span></div>', chart)
        self.assertEqual([(c, w) for c, _, w in bars], [("bar is-ref", "100"), ("bar is-soft", "42"), ("bar is-soft", "85"),
                                                       ("bar is-shipped", "71"), ("bar is-shipped", "73")])
        labels = [l for _, l, _ in bars]
        self.assertIn("100%", labels[0])
        self.assertIn("without memory", labels[0].lower())
        self.assertIn("42%", labels[1])
        self.assertIn("about 85%", labels[2])
        self.assertIn("71%", labels[3])
        self.assertIn("73%", labels[4])
        self.assertEqual(re.findall(r'<span class="bar-name">([^<]+)</span>', chart),
                         ["Without memory", "exp 01", "exp 02", "exp 03 · repo A", "exp 03 · repo B"])
        values = [_plain_text(v) for v in re.findall(r'<span class="bar-val[^"]*">(.*?)</span>\s*</div>', chart, re.S)]
        self.assertEqual(values, ["100%", "42% −58%", "~85% ~−15%", "71% −29%", "73% −27%"])
        # the shipped method is the highlighted one: only its two bars use the neon fill (the bare .bar > span rule)
        self.assertIn("exp 03", self.scan.by_class["bar-name"][3])
        self.assertEqual(chart.count("is-shipped"), 2)
        self.assertIn("is-muted", re.findall(r'<span class="(bar-val[^"]*)"', chart)[1])
        self.assertNotIn("is-muted", re.findall(r'<span class="(bar-val[^"]*)"', chart)[3])
        self.assertEqual(len(re.findall(r"<details", sec)), 1)
        self.assertIn("Does memory from the last session cut tokens on a follow-up?", sec.split("<details")[1])

    # HUN-204 AC 5: the Easy Personal panel with this repo's numbers
    def test_dashboard_panel_shows_the_snapshot(self):
        sec = self.section("dashboard")
        self.assertIn("<h2>See it in Easy Personal</h2>", sec)
        self.assertIn('<a href="%s">' % EASY_PERSONAL, sec)
        text = _plain_text(sec)
        for line in ("this repo, 3 Nov 2026", "easy-memory", "143 notes", "saved per day, last 30 days",
                     "Hit rate 70% of 56 prompts", "Memory on vs off",
                     "On 3 sessions 23.2M tokens / session", "Off 5 sessions 16.6M tokens / session",
                     "too few sessions to compare (3 on / 5 off, need 10 each)",
                     "Easy Personal reads report.json, which easy-memory refreshes about once an hour",
                     "counts only, never note text"):
            self.assertIn(line, text, line)
        spark = re.search(r'<svg class="spark"([^>]*)>(.*?)</svg>', sec, re.S)
        self.assertIn('role="img"', spark.group(1))
        self.assertIn("last 30 days", spark.group(1))
        rects = re.findall(r'<rect class="(sp-bar[^"]*)" data-n="(\d+)"', spark.group(2))
        self.assertEqual(len(rects), 30)
        self.assertEqual([int(n) for _, n in rects], SPARK_NOTES)
        self.assertEqual(sum(SPARK_NOTES), 143)  # the bars add up to the total
        self.assertEqual([c for c, _ in rects].count("sp-bar is-today"), 1)
        self.assertEqual(rects[-1][0], "sp-bar is-today")
        self.assertNotRegex(sec, r"\b(Saves|Uses)\b")
        self.assertNotRegex(_plain_text(sec.split("<details")[0]), r"\d+\s*% (saved|fewer|less|cheaper)")
        self.assertEqual(len(re.findall(r"<details", sec)), 1)

    # HUN-204 AC 6: no release notes
    def test_release_notes_are_gone(self):
        self.assertNotIn('id="notes"', self.html)
        self.assertNotIn('href="#notes"', self.html)
        self.assertNotIn("Release notes", self.html)
        self.assertNotIn("RELEASE_v0.1.0", self.html)
        self.assertNotRegex(self.local_style, r"\.rn\b")
        self.assertEqual(self.scan.with_class("dl", "rn"), [])
        footer = re.search(r"<footer>(.*?)</footer>", self.html, re.S).group(1)
        self.assertIn("Easy Memory v0.1.0 prototype", footer)
        self.assertIn('<a href="%s">source</a>' % GITHUB, footer)
        self.assertNotIn("release plan", footer)

    # HUN-204: pictures carry the explanation
    def test_visible_words_grow_by_at_most_150(self):
        words = _Words()
        words.feed(self.html)
        self.assertLessEqual(words.count, VISIBLE_WORDS_BEFORE + 150, words.count)

    def test_install_stepper_has_codeboxes(self):
        self.assertEqual(self.scan.by_class["step-no"], ["01", "02", "03", "end"])
        stepper = re.search(r'<ol class="stepper"[^>]*>(.*?)</ol>', self.html, re.S).group(1)
        self.assertEqual(re.findall(r"<h3>([^<]+)</h3>", stepper), ["Get the code", "Preview", "Install", "Check"])
        self.assertEqual(stepper.count('class="codebox"'), 3)
        self.assertEqual(len(self.scan.with_class("div", "codebox")), 4)
        self.assertEqual(len(self.scan.by_class["prompt"]), 8)
        self.assertEqual(set(self.scan.by_class["prompt"]), {"$"})
        self.assertEqual(len([a for t, a in self.scan.tags if t == "button" and "data-copy" in a]), 4)

    def test_install_stepper_boxes_are_equal_from_720_up(self):
        """HUN-133: the three step items share rows, so code boxes, Copy buttons and captions line up."""
        css = re.sub(r"/\*.*?\*/", "", self.local_style, flags=re.S)
        wide = re.search(r"@media \(min-width:720px\) \{(.*?\n  \})", css, re.S)
        self.assertIsNotNone(wide, "no (min-width:720px) block")
        rules = dict(_rules(wide.group(1)))
        item = rules[".stepper > li"]
        self.assertIn("grid-template-rows:subgrid", item)
        self.assertIn("grid-row:span 4", item)
        self.assertIn("flex:1", rules[".stepper .codebox code"])
        # the stacked layout (< 720) keeps boxes sized to their content
        stacked = re.search(r"@media \(max-width:719px\) \{(.*?)\n  \}", css, re.S).group(1)
        self.assertNotIn("subgrid", stacked)

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

    def test_header_outer_height_is_header_h(self):
        # --header-h is the total height with the 1px bottom border, so the inner box gives that 1px back.
        self.assertRegex(self.local_style, r"\.header-inner\s*\{[^}]*height:calc\(var\(--header-h\) - 1px\)")
        self.assertRegex(self.local_style, r"\.site-header\s*\{[^}]*border-bottom:1px solid var\(--line-header\)")
        self.assertRegex(self.local_style, r"\.sidebar\s*\{[^}]*top:var\(--header-h\)")

    def test_stats_strip_is_two_columns_below_720(self):
        media = re.search(r"@media \(max-width:719px\) \{(.*)\n  \}\n</style>", self.local_style + "</style>", re.S)
        self.assertIsNotNone(media)
        block = media.group(1)
        self.assertRegex(block, r"\.strip\.stats\s*\{\s*--cols:2;\s*\}")
        self.assertRegex(block, r"\.strip\.stats > :nth-child\(3\)\s*\{[^}]*grid-column:1 / -1")

    def test_no_task_ids_and_no_built_section(self):
        self.assertNotIn("HUN-", self.html)
        self.assertNotIn("#built", self.html)
        self.assertNotIn('id="built"', self.html)
        self.assertNotIn("How it was built", self.html)

    def test_each_section_folds_its_detail(self):
        for sid in SECTION_ORDER:
            sec = re.search(r'<section id="%s">(.*?)</section>' % sid, self.html, re.S).group(1)
            self.assertEqual(sec.count('<details class="more">'), 1, sid)
            self.assertEqual(sec.count("<summary>More detail</summary>"), 1, sid)
            self.assertTrue(sec.rstrip().endswith("</details>"), sid)  # at the end of the section

    # AC6 content kept (spot checks; the full fact inventory is in the TASK_REVIEW evidence)
    def test_content_kept(self):
        for text in ("Coding agents pay again for what an earlier session already found out.",
                     "python3 easy_memory.py install --dry-run",
                     "1.69 MB",
                     "7,831-file repo, 200 notes",
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
