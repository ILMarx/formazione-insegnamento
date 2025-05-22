#!/usr/bin/env python3
import os
import xml.etree.ElementTree as ET
from datetime import datetime

# === Configuration ===
MIRROR_BASE = "https://formazione-insegnamento.eu"
SITE_ROOT   = "."  # We're running this from the root of gh-pages checkout
EXCLUDE_DIRS = {'.git', '.github', 'assets', 'css', 'js'}  # tweak as needed

# === Helper to indent XML ===
def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for child in elem:
            indent(child, level+1)
        if not child.tail or not child.tail.strip():
            child.tail = i
    if level and (not elem.tail or not elem.tail.strip()):
        elem.tail = i

# === List all HTML files under SITE_ROOT ===
def list_html_files(site_root):
    urls = []
    for root, dirs, files in os.walk(site_root):
        # skip excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith('.')]
        for file in files:
            if not file.endswith(".html"):
                continue
            # skip dot‐files
            if file.startswith('.'):
                continue
            abs_path = os.path.join(root, file)
            # compute web‐relative path
            rel_path = os.path.relpath(abs_path, site_root)
            url = f"{MIRROR_BASE}/{rel_path.replace(os.sep, '/')}"
            urls.append((url, abs_path))
    return urls

# === Generate the sitemap.xml ===
def generate_sitemap(entries, site_root):
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")

    for url, file_path in sorted(entries, key=lambda x: x[0]):
        url_el = ET.SubElement(urlset, "url")
        loc_el = ET.SubElement(url_el, "loc")
        loc_el.text = url

        # add lastmod from file mtime
        mtime = os.path.getmtime(file_path)
        lastmod = datetime.utcfromtimestamp(mtime).strftime('%Y-%m-%dT%H:%M:%SZ')
        lm_el = ET.SubElement(url_el, "lastmod")
        lm_el.text = lastmod

    # pretty‐print
    indent(urlset)

    tree = ET.ElementTree(urlset)
    out_path = os.path.join(site_root, "sitemap.xml")
    tree.write(out_path, encoding="utf-8", xml_declaration=True)
    print(f"Sitemap generated at: {out_path}")

if __name__ == "__main__":
    entries = list_html_files(SITE_ROOT)
    if not entries:
        print("No HTML files found — is SITE_ROOT correct?")
    else:
        generate_sitemap(entries, SITE_ROOT)
