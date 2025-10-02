import re, pathlib, hashlib, json, datetime
from collections import defaultdict

# Always resolve from repo root
ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "docs"              # source markdown
OUT_DIR = ROOT / "public/snippets"   # output folder

TREE = {}  # structured manifest tree

def slugify(text: str) -> str:
    return (
        text.lower()
        .replace(" ", "-")
        .replace(")", "")
        .replace("(", "")
        .replace("/", "-")
        .replace(":", "")
        .replace("&", "and")
    )

def sectionize(md_text: str):
    """Split MD into (heading, body, heading_level) tuples for each ## section."""
    parts = re.split(r"(^#{2,3} .*$)", md_text, flags=re.MULTILINE)
    for i in range(1, len(parts), 2):
        heading_line = parts[i].strip()
        body = parts[i] + parts[i+1]
        heading_level = heading_line.count("#")  # ## → 2, ### → 3
        heading = heading_line.strip("# ").strip()
        yield heading, body, heading_level

def write_snippet(md_file: pathlib.Path, heading: str, body: str, heading_level: int, order: int):
    rel_path = md_file.relative_to(SRC_DIR).with_suffix("")  # e.g. getting-started/first-login
    slug = slugify(heading)

    # Output path
    outfile = OUT_DIR / rel_path.parent / f"{rel_path.name}-{slug}.snippet.md"
    outfile.parent.mkdir(parents=True, exist_ok=True)
    outfile.write_text(body.strip() + "\n", encoding="utf-8")

    # Compute hash + modified time
    sha256 = hashlib.sha256(body.encode("utf-8")).hexdigest()
    last_modified = datetime.datetime.utcfromtimestamp(md_file.stat().st_mtime).isoformat() + "Z"

    # Build hierarchy
    section = rel_path.parts[0]   # top-level folder (e.g. "getting-started")
    if section not in TREE:
        TREE[section] = {
            "title": section.replace("-", " ").title(),
            "slug": section,
            "children": []
        }

    TREE[section]["children"].append({
        "title": heading,
        "slug": str(outfile.relative_to(ROOT / "public")),
        "sha256": sha256,
        "order": order,
        "heading_level": heading_level,
        "last_modified": last_modified
    })

def main():
    for md_file in SRC_DIR.rglob("*.md"):
        text = md_file.read_text(encoding="utf-8")
        order = 1
        for heading, body, heading_level in sectionize(text):
            write_snippet(md_file, heading, body, heading_level, order)
            order += 1

    (ROOT / "public").mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest_file = ROOT / "public" / "snippets" / "mbi" / "manifest.json"
    manifest_file.parent.mkdir(parents=True, exist_ok=True)
    manifest_list = list(TREE.values())
    manifest_file.write_text(json.dumps(manifest_list, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()