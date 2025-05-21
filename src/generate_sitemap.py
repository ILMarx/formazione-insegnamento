#!/usr/bin/env python3
import os
import xml.etree.ElementTree as ET

MIRROR_BASE = "https://formazione-insegnamento.eu"
OUTPUT_DIR = "output"  # or wherever your built site is

def list_html_files(output_dir):
    urls = []
    for root, _, files in os.walk(output_dir):
        for file in files:
            if file.endswith(".html"):
                rel_path = os.path.relpath(os.path.join(root, file), output_dir)
                # Use .replace(os.sep, "/") for cross-platform compatibility
                url = f"{MIRROR_BASE}/{rel_path.replace(os.sep, '/')}"
                urls.append(url)
    return urls

def generate_sitemap(urls, output_dir):
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for url in sorted(urls):
        url_el = ET.SubElement(urlset, "url")
        loc_el = ET.SubElement(url_el, "loc")
        loc_el.text = url
    tree = ET.ElementTree(urlset)
    sitemap_path = os.path.join(output_dir, "sitemap.xml")
    tree.write(sitemap_path, encoding="utf-8", xml_declaration=True)
    print(f"Sitemap generated at: {sitemap_path}")

if __name__ == "__main__":
    urls = list_html_files(OUTPUT_DIR)
    generate_sitemap(urls, OUTPUT_DIR)
