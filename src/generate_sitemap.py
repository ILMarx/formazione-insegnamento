#!/usr/bin/env python3
import os
import xml.etree.ElementTree as ET

MIRROR_BASE = "https://formazione-insegnamento.eu"
SITE_ROOT = "."  # This is the current directory, i.e. your repo root

def list_html_files(site_root):
    urls = []
    for root, _, files in os.walk(site_root):
        for file in files:
            if file.endswith(".html"):
                if any(part.startswith('.') for part in os.path.relpath(root, site_root).split(os.sep)):
                    continue
                rel_path = os.path.relpath(os.path.join(root, file), site_root)
                url = f"{MIRROR_BASE}/{rel_path.replace(os.sep, '/')}"
                urls.append(url)
    return urls

def generate_sitemap(urls, site_root):
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for url in sorted(urls):
        url_el = ET.SubElement(urlset, "url")
        loc_el = ET.SubElement(url_el, "loc")
        loc_el.text = url
    tree = ET.ElementTree(urlset)
    sitemap_path = os.path.join(site_root, "sitemap.xml")
    tree.write(sitemap_path, encoding="utf-8", xml_declaration=True)
    print(f"Sitemap generated at: {sitemap_path}")

if __name__ == "__main__":
    urls = list_html_files(SITE_ROOT)
    generate_sitemap(urls, SITE_ROOT)
