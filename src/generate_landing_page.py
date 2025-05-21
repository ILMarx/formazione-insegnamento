from datetime import datetime
from dateutil.tz import gettz

#!/usr/bin/env python3
r"""
generate_landing_page.py
Genera landing page HTML dal database CSV in C:\dev\mirror_page_creator\output.
Richiede: pip install jinja2 python-dateutil
"""
import os, csv, sys, re, unicodedata, json
from dateutil.parser import isoparse
from dateutil.tz import gettz
from jinja2 import Environment, FileSystemLoader, select_autoescape

# === CONFIGURATION ===
# script is in src/, repo root is one level up
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT  = os.path.dirname(SCRIPT_DIR)

# now data/ and templates/ at repo root
DATA_CSV      = os.path.join(REPO_ROOT, 'data', 'FI_DATABASE.csv')
TEMPLATE_DIR  = os.path.join(REPO_ROOT, 'templates')
TEMPLATE_FILE = 'landing_template.html'
OUTPUT_DIR    = os.path.join(REPO_ROOT, 'output')
INDEX_TEMPLATE = 'index_template.html'

LANGUAGES = ['en', 'it', 'fr', 'es', 'pt']

# Metadati periodico
JOURNAL_META = {
    'title': 'Formazione & insegnamento',
    'alternative': 'Formazione e insegnamento',
    'abbrev': 'Form. insegn. (Online)',
    'issn': '2279-7505',
    'issn_l': '1973-4778',
    'publisher': 'Pensa MultiMedia',
    'creator': 'Umberto Margiotta',
    'editor': 'Andrea Mattia Marcelli',
    'director': 'Rita Minello',
    'contributors_corporate': [
        'SIREF – Società Italiana per la Ricerca Educativa e Formativa',
        'SSIS Veneto',
        'SIEMeS – Società Italiana Educazione Motoria e Sportiva'
    ],
    'description': 'Rivista open access sullo studio delle regioni educativo-formative.',
    'keywords': 'formazione, insegnamento, pedagogia, ricerca educativa',
    'language': 'it',
    'url': 'https://ojs.pensamultimedia.it/index.php/siref',
    'license': 'https://creativecommons.org/licenses/by/4.0'
}

# Base URLs for mirror and original
MIRROR_BASE   = 'https://formazione-insegnamento.eu'
ORIGINAL_BASE = JOURNAL_META['url'] + '/article/view'

# Utility: crea slug

def slugify(text, max_length=60):
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')[:max_length]

# Parsing JSON authors e references

def parse_authors(detail_str):
    try:
        authors = json.loads(detail_str)
        return [
            {
                'name': a.get('name'),
                'affiliation': a.get('affiliation'),
                'orcid': a.get('orcid'),
                'email': a.get('email'),
                'country': a.get('country')
            }
            for a in authors
        ]
    except:
        return []

def parse_references(ref_str):
    try:
        refs = json.loads(ref_str)
        processed = []
        for r in refs:
            r_html = re.sub(r'(https?://[^\s]+)',
                            lambda m: f'<a href="{m.group(0)}" target="_blank">{m.group(0)}</a>',
                            r)
            processed.append(r_html)
        return processed
    except:
        return []

# Verify paths

def verify_paths():
    if not os.path.isfile(DATA_CSV):
        print(f"Errore: CSV non trovato: {DATA_CSV}")
        sys.exit(1)
    if not os.path.isdir(TEMPLATE_DIR):
        print(f"Errore: template non trovato: {TEMPLATE_DIR}")
        sys.exit(1)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

# Init Jinja2
env = None
template = None
index_template = None

def init_template():
    global env, template, index_template
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(['html', 'xml'])
    )
    env.filters['slugify'] = slugify
    template = env.get_template(TEMPLATE_FILE)
    index_template = env.get_template(INDEX_TEMPLATE)

# Helper per campi multilingua

def get_field(row, base, lang=None):
    key = f"{base}_{lang}" if lang else base
    return (row.get(key, '') or '').strip()

# Generazione pagine
def generate_pages():
    verify_paths()
    init_template()
    count = 0
    archive = {}  # {year: {vol: {issue: [ {title, slug, path}, ...]}}}

    with open(DATA_CSV, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for raw in reader:
            row = {k.strip().lstrip('\ufeff'): v for k, v in raw.items()}
            aid = row.get('ArticleID', '').strip()
            if not aid:
                continue

            # Date handling
            raw_cit = row.get('Citation_Date', '')
            try:
                dt = isoparse(raw_cit).replace(tzinfo=gettz('Europe/Rome'))
                date_iso = dt.isoformat()
            except:
                date_iso = f"{raw_cit}T00:00:00+01:00"

            # Build path parts, omitting empty‐issue directories
            title_en = get_field(row, 'Title', 'en')
            slug     = slugify(title_en)
            year     = row.get('PublicationYear', 'unknown-year')
            vol      = row.get('Volume', '0')
            issue    = row.get('Issue', '').strip()
            filename = f"{aid}-{slug}.html"

            if issue:
                # has an issue → year/vol/issue/… 
                subdir   = os.path.join(OUTPUT_DIR, year, vol, issue)
                rel_path = f"{year}/{vol}/{issue}/{filename}"
            else:
                # no issue → just year/vol/…
                subdir   = os.path.join(OUTPUT_DIR, year, vol)
                rel_path = f"{year}/{vol}/{filename}"

            os.makedirs(subdir, exist_ok=True)
            outfile = os.path.join(subdir, filename)

            # Parse lists
            authors_list    = parse_authors(row.get('Authors_Detail','[]'))
            references_list = parse_references(row.get('References','[]'))

            general = {
                'Journal_Title':     row.get('Journal_Title'),
                'Journal_ISSN':      row.get('Journal_ISSN'),
                'Journal_Publisher': row.get('Journal_Publisher'),
                'PublicationDate':   row.get('PublicationDate',''),
                'PublicationYear':   row.get('PublicationYear',''),
                'SubmissionDate':    row.get('SubmissionDate',''),
                'IssueDate':         row.get('IssueDate',''),
                'Volume':            row.get('Volume') or 'missing data',
                'Issue':             row.get('Issue')  or 'missing data',
                'Pages':             f"{row.get('First_Page','')}-{row.get('Last_Page','')}".strip('-'),
                'DOI':               row.get('DOI'),
                'Citation_Date':     raw_cit,
                'DatePublishedISO':  date_iso,
                'Full_Text_HTML_URL':row.get('Full_Text_HTML_URL'),
                'PDF_URL':           row.get('PDF_URL'),
                'Full_Text_XML_URL': row.get('Full_Text_XML_URL'),
                'License_URL':       row.get('License_URL'),
                'License_Type':      row.get('License_Type'),
                'Authors':           authors_list,
                'Article_Type':      row.get('Article_Type'),
                'References':        references_list
            }

            # Multilingual sections
            langs = []
            for lg in LANGUAGES:
                langs.append({
                    'lang':     lg,
                    'title':    get_field(row, 'Title', lg)   or 'missing data',
                    'abstract': get_field(row, 'Abstract', lg)or 'missing data',
                    'keywords': get_field(row, 'Keywords', lg)or 'missing data'
                })

            context = {
                'journal':      JOURNAL_META,
                'general':      general,
                'languages':    langs,
                'article_id':   aid,
                'path':         rel_path,
                'mirror_url':   f"{MIRROR_BASE}/{rel_path}",
                'original_url': f"{ORIGINAL_BASE}/{aid}"
            }

            html = template.render(context)
            with open(outfile, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"Generata: {outfile}")
            count += 1

    # Generate index.html
    idx_html = index_template.render(
        journal=JOURNAL_META,
        archive=archive,
        generated_at=datetime.now(gettz('Europe/Rome')).isoformat()
    )
    with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(idx_html)
    print("Generata: index.html")

    print(f"Totale: {count} pagine generate in '{OUTPUT_DIR}'.")

if __name__ == '__main__':
    generate_pages()
    # Call the sitemap generator after all pages are generated
    import subprocess
    subprocess.run(["python3", "generate_sitemap.py"])
