import re, pathlib, hashlib, json
import markdown, bleach

SRC_DIR = pathlib.Path("docs")  # where your .md files live
OUT_DIR = pathlib.Path("public/snippets")  # where to output snippet html
MANIFEST = {}

# Bleach whitelist
ALLOWED_TAGS = bleach.sanitizer.ALLOWED_TAGS.union(
    {"h1","h2","h3","p","ul","ol","li","pre","code","blockquote","strong","em","a"}
)
ALLOWED_ATTRS = {"a": ["href","title","rel","target"]}

def sanitize(html: str) -> str:
    return bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS)

def sectionize(md_text: str):
    """Split MD into (heading, body) tuples for each ## section."""
    parts = re.split(r"(^## .*$)", md_text, flags=re.MULTILINE)
    for i in range(1, len(parts), 2):
        heading = parts[i].strip("# ").strip()
        body = parts[i] + parts[i+1]
        yield heading, body

def write_snippet(path, heading, body):
    html = markdown.markdown(body, extensions=["extra"])
    clean = sanitize(html)
    slug = heading.lower().replace(" ", "-").replace(")", "").replace("(", "")
    outfile = OUT_DIR / f"{path}-{slug}.snippet.html"
    outfile.parent.mkdir(parents=True, exist_ok=True)
    outfile.write_text(clean, encoding="utf-8")

    sha256 = hashlib.sha256(clean.encode("utf-8")).hexdigest()
    MANIFEST[str(outfile.relative_to("public"))] = {"sha256": sha256}

def main():
    for md_file in SRC_DIR.rglob("*.md"):
        text = md_file.read_text(encoding="utf-8")
        path = md_file.stem  # e.g. first-login
        for heading, body in sectionize(text):
            write_snippet(path, heading, body)

    # ✅ Ensure public/ exists
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Write manifest.json
    manifest_file = pathlib.Path("public/manifest.json")
    manifest_file.write_text(json.dumps(MANIFEST, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()