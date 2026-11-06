"""Make 'source for publishing/index.html' from the main page.

The main page ("Prayers and Blessings v2 (open this).html") is the file you edit.
The publish copy is the same page without the wrapper head/body tags, and its
font link points one folder up. Run after every edit:  python3 tools/sync_publish.py
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(ROOT, "Prayers and Blessings v2 (open this).html")
PUBLISH = os.path.join(ROOT, "source for publishing", "index.html")


def to_publish(html):
    i = html.index("<body>") + len("<body>")
    body = html[i:]
    end = body.rindex("</body></html>")
    body = body[:end].strip() + "\n"
    return body.replace('href="fonts/fonts.css"', 'href="../fonts/fonts.css"')


if __name__ == "__main__":
    with open(MAIN, encoding="utf-8") as f:
        out = to_publish(f.read())
    with open(PUBLISH, "w", encoding="utf-8") as f:
        f.write(out)
    print("wrote", PUBLISH)
