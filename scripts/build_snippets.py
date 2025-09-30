import re, pathlib, hashlib, json
import markdown, bleach

# Always resolve from repo root (script may be called from anywhere)
ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "docs"              # source markdown
OUT_DIR = ROOT / "public/snippets"   # output folder
MANIFEST = {}

# Bleach whitelist
ALLOWED_TAGS = bleach.sanitizer.ALLOWED_TAGS.union(
    {"h1","h2","h3","p","ul","ol","li","pre","code","blockquote","strong","em","a"}
)
ALLOWED_ATTRS = {"a": ["href","title","rel","target"]}

def sanitize(html: str) -> str:
    return bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS)

def slugify(text: str) -> str:
    return (
        text.lower()
        .replace(" ", "-")
        .replace(")", "")
        .replace("(", "")
        .replace("/", "-")
        .replace(":", "")
    )

def sectionize(md_text: str):
    """Split MD into (heading, body) tuples for each ## section."""
    parts = re.split(r"(^## .*$)", md_text, flags=re.MULTILINE)
    for i in range(1, len(parts), 2):
        heading = parts[i].strip("# ").strip()
        body = parts[i] + parts[i+1]
        yield heading, body

def write_snippet(md_file: pathlib.Path, heading: str, body: str):
    html = markdown.markdown(body, extensions=["extra"])
    clean = sanitize(html)

    # Mirror docs/ folder structure under snippets/
    rel_path = md_file.relative_to(SRC_DIR).with_suffix("")  # e.g. getting-started/first-login
    slug = slugify(heading)                                  # e.g. 4-run-your-first-query
    outfile = OUT_DIR / rel_path.parent / f"{rel_path.name}-{slug}.snippet.html"

    outfile.parent.mkdir(parents=True, exist_ok=True)
    outfile.write_text(clean, encoding="utf-8")

    sha256 = hashlib.sha256(clean.encode("utf-8")).hexdigest()
    manifest_key = str(outfile.relative_to(ROOT / "public"))   # ✅ fix here
    MANIFEST[manifest_key] = {
        "sha256": sha256,
        "heading": heading
    }

def main():
    for md_file in SRC_DIR.rglob("*.md"):
        text = md_file.read_text(encoding="utf-8")
        for heading, body in sectionize(text):
            write_snippet(md_file, heading, body)

    # ✅ Ensure both public/ and public/snippets/ exist
    (ROOT / "public").mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ✅ Write manifest.json in <repo-root>/public/ (not relative CWD)
    manifest_file = ROOT / "public" / "manifest.json"
    manifest_file.write_text(json.dumps(MANIFEST, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()