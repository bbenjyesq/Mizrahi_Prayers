"""Checks the printed booklets and the publish copy. Run: python3 tests/test_booklets.py

Booklet membership mirrors the BK rules in the page script. booklets_expected.json
holds the membership from before the data-booklet change, so a change that drops
or adds a prayer in a booklet fails here.
"""
import json, os, re, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from sync_publish import MAIN, PUBLISH, to_publish  # noqa: E402

HTML = open(MAIN, encoding="utf-8").read()
EXPECTED = json.load(open(os.path.join(ROOT, "tests", "booklets_expected.json"), encoding="utf-8"))

RULES = {
    "friday": lambda g, b: g == "shabbat",
    "day": lambda g, b: g == "day" or b == "day",
    "havdalah": lambda g, b: g == "havdalah",
    "kaddish": lambda g, b: g == "minyan",
    "daily": lambda g, b: g == "daily",
    "mitzvot": lambda g, b: g == "mitzvot",
    "pesukei": lambda g, b: g == "pesukei",
    "tikkun": lambda g, b: g == "tikkun",
}


def sections(html):
    for m in re.finditer(r'<section class="prayer[^"]*"([^>]*)>', html):
        yield dict(re.findall(r'(data-[a-z-]+)="([^"]*)"', m.group(1)))


class Booklets(unittest.TestCase):
    def test_membership_unchanged(self):
        for name, rule in RULES.items():
            got = [a["data-title"] for a in sections(HTML) if rule(a.get("data-group", ""), a.get("data-booklet", ""))]
            self.assertEqual(got, EXPECTED[name], f"booklet {name} changed")

    def test_no_save_pdf_left(self):
        self.assertFalse("Save PDF" in HTML, "Save PDF still in page")

    def test_publish_copy_in_sync(self):
        with open(PUBLISH, encoding="utf-8") as f:
            self.assertEqual(f.read(), to_publish(HTML), "run python3 tools/sync_publish.py")

    def test_hash_decode_cannot_throw(self):
        # a link ending in "#%" made decodeURIComponent throw and stopped the page script
        for line in HTML.splitlines():
            if "decodeURIComponent(" in line:
                self.assertIn("try {", line, "decodeURIComponent must sit inside try/catch")

    def test_audio_wired_up(self):
        # each recording: file on disk, a length in the DUR table, and the "Audio" badge on its section
        dur = re.search(r"var DUR = \{([^}]*)\}", HTML).group(1)
        used = set()
        for m in re.finditer(r'<section class="prayer[^"]*"[^>]*>(.*?)</section>', HTML, re.S):
            body = m.group(1)
            srcs = re.findall(r'<audio [^>]*src="audio/([a-z0-9-]+)\.mp3"', body)
            self.assertEqual(bool(srcs), 'class="aud"' in body, "Audio badge and player must go together")
            for key in srcs:
                used.add(key)
                self.assertTrue(os.path.exists(os.path.join(ROOT, "audio", key + ".mp3")), key + ".mp3 missing")
                self.assertIn("'%s':" % key, dur, key + " missing from DUR")
        on_disk = {f[:-4] for f in os.listdir(os.path.join(ROOT, "audio")) if f.endswith(".mp3")}
        self.assertEqual(on_disk - used, set(), "audio files not used by any section")

    def test_fonts_are_local(self):
        self.assertFalse("fonts.googleapis.com" in HTML)
        self.assertFalse("fonts.gstatic.com" in HTML)
        self.assertTrue(os.path.exists(os.path.join(ROOT, "fonts", "fonts.css")))


if __name__ == "__main__":
    unittest.main()
