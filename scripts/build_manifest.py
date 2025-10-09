#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# ------------ helpers ------------

HEADING_RE = re.compile(r'^(#{1,6})\s+(.+?)\s*$', re.UNICODE)

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def first_heading_level(md_text: str) -> Optional[int]:
    for line in md_text.splitlines():
        m = HEADING_RE.match(line)
        if m:
            return len(m.group(1))
    return None

def title_from_file(p: Path, md_text: str) -> str:
    # Prefer first heading text; else derive from filename
    for line in md_text.splitlines():
        m = HEADING_RE.match(line)
        if m:
            return m.group(2).strip()
    # Derive from filename (remove extension, replace separators, split camel case)
    name = p.stem
    name = name.replace('_', ' ').replace('-', ' ')
    name = re.sub(r'(?<=[a-z0-9])([A-Z])', r' \1', name)  # CamelCase -> Camel Case
    # Tidy double spaces
    name = re.sub(r'\s{2,}', ' ', name)
    return name.strip().title()

def iso_utc(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()

# ------------ core build ------------

def collect_md_files(root: Path) -> List[Path]:
    return [p for p in root.rglob('*.md') if p.is_file()]

def relative_slug(root: Path, p: Path) -> str:
    # Always forward slashes
    return str(p.relative_to(root)).replace(os.sep, '/')

def folder_has_exactly_one_md(folder: Path) -> Tuple[bool, Optional[Path]]:
    md_files = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() == '.md']
    subfolders = [d for d in folder.iterdir() if d.is_dir()]
    # collapse rule: exactly one .md and no subfolders with .md content
    if len(md_files) == 1:
        # if any subfolder contains md, we shouldn't collapse
        for d in subfolders:
            if any(x.suffix.lower() == '.md' for x in d.rglob('*.md')):
                return (False, None)
        return (True, md_files[0])
    return (False, None)

def build_node_for_md(root: Path, p: Path) -> Dict[str, Any]:
    text = p.read_text(encoding='utf-8', errors='ignore')
    title = title_from_file(p, text)
    lvl = first_heading_level(text) or 2
    return {
        "title": title,
        "slug": relative_slug(root, p),
        "sha256": sha256_file(p),
        "order": 0,  # filled later
        "heading_level": lvl,
        "last_modified": iso_utc(p.stat().st_mtime)
    }

def build_tree(root: Path, folder: Path) -> List[Dict[str, Any]]:
    """
    Returns a list of child nodes for 'folder'.
    Each child is either:
      - a folder node: { title, slug, children: [...] }
      - a page node for an .md file (as per build_node_for_md)
    The collapse rule is applied at each subfolder.
    """
    children: List[Dict[str, Any]] = []

    # 1) Add direct .md files in this folder
    for md in sorted([x for x in folder.iterdir() if x.is_file() and x.suffix.lower() == '.md']):
        children.append(build_node_for_md(root, md))

    # 2) Recurse into subfolders
    for sub in sorted([d for d in folder.iterdir() if d.is_dir()]):
        # skip hidden/system folders by convention
        if sub.name.startswith('.') or sub.name.lower() in ('.git', '.github', '__pycache__', 'node_modules'):
            continue

        collapse, the_md = folder_has_exactly_one_md(sub)
        if collapse and the_md is not None:
            # lift the single page up to current level (no folder node)
            children.append(build_node_for_md(root, the_md))
        else:
            # build folder node with children
            sub_children = build_tree(root, sub)
            # If folder has no markdown at all, skip it
            if not sub_children:
                continue

            # folder node gets a title from folder name, slug is its relative path
            title = re.sub(r'[_-]+', ' ', sub.name).strip().title()
            node = {
                "title": title,
                "slug": str(sub.relative_to(root)).replace(os.sep, '/'),
                "children": sub_children
            }
            children.append(node)

    # 3) Assign order per sibling set (stable: folders first by title, then pages by title)
    def key_fn(n: Dict[str, Any]) -> Tuple[int, str]:
        is_folder = 0 if "children" in n else 1  # folders first
        return (is_folder, n["title"].lower())

    children.sort(key=key_fn)

    # apply 1-based order only to page nodes
    order_counter = 1
    for n in children:
        if "children" in n:
            # recursively apply order inside
            pass
        else:
            n["order"] = order_counter
            order_counter += 1

    return children

def build_manifest(root: Path) -> List[Dict[str, Any]]:
    """
    Top-level manifest as a list. If you want a single root like {"title":"MBI",...},
    wrap this list as needed in your viewer.
    """
    return build_tree(root, root)

# ------------ CLI ------------

def main():
    ap = argparse.ArgumentParser(description="Build manifest.json for Markdown docs.")
    ap.add_argument("root", help="Root folder to scan (e.g., path to v1.0.0.2)")
    ap.add_argument("--out", default="manifest.json", help="Output filename (written under root)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Root folder not found: {root}")

    manifest = build_manifest(root)

    out_path = root / args.out
    out_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {out_path}")

if __name__ == "__main__":
    main()
