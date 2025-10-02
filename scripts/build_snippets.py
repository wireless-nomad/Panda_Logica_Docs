import re, pathlib, hashlib, json, datetime

# Always resolve from repo root
ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "docs"              # source markdown
OUT_DIR = ROOT / "public/snippets"   # output folder

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
    """Split MD into (heading, body, heading_level) tuples for each ## or ### section."""
    parts = re.split(r"(^#{2,3} .*$)", md_text, flags=re.MULTILINE)
    for i in range(1, len(parts), 2):
        heading_line = parts[i].strip()
        body = parts[i] + parts[i+1]
        heading_level = heading_line.count("#")  # ## → 2, ### → 3
        heading = heading_line.strip("# ").strip()
        yield heading, body, heading_level

def write_snippet(docset: str, md_file: pathlib.Path, heading: str, body: str, heading_level: int, order: int, tree: dict):
    rel_path = md_file.relative_to(SRC_DIR / docset).with_suffix("")  # e.g. getting-started/first-login
    slug = slugify(heading)

    # Output path
    outfile = OUT_DIR / docset / rel_path.parent / f"{rel_path.name}-{slug}.snippet.md"
    outfile.parent.mkdir(parents=True, exist_ok=True)
    outfile.write_text(body.strip() + "\n", encoding="utf-8")

    # Compute hash + modified time
    sha256 = hashlib.sha256(body.encode("utf-8")).hexdigest()
    last_modified = datetime.datetime.utcfromtimestamp(md_file.stat().st_mtime).isoformat() + "Z"

    # Section name = first part of path (e.g. "getting-started")
    if rel_path.parts:
        section = rel_path.parts[0]
    else:
        section = "root"

    if section not in tree:
        tree[section] = {
            "title": section.replace("-", " ").title(),
            "slug": section,
            "children": []
        }

    tree[section]["children"].append({
        "title": heading,
        "slug": str(outfile.relative_to(ROOT / "public")),
        "sha256": sha256,
        "order": order,
        "heading_level": heading_level,
        "last_modified": last_modified
    })

def build_docset(docset: str):
    tree = {}
    docset_src = SRC_DIR / docset
    for md_file in docset_src.rglob("*.md"):
        text = md_file.read_text(encoding="utf-8")
        order = 1
        for heading, body, heading_level in sectionize(text):
            write_snippet(docset, md_file, heading, body, heading_level, order, tree)
            order += 1

    # Write manifest.json into docset folder
    manifest_file = ROOT / "public" / "snippets" / docset / "manifest.json"
    manifest_file.parent.mkdir(parents=True, exist_ok=True)
    manifest_list = list(tree.values())
    manifest_file.write_text(json.dumps(manifest_list, indent=2), encoding="utf-8")

def main():
    # detect all docsets (top-level folders under docs/)
    for docset_dir in SRC_DIR.iterdir():
        if docset_dir.is_dir():
            build_docset(docset_dir.name)

if __name__ == "__main__":
    main()