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
DATA_CSV     = os.path.join(REPO_ROOT, 'data', 'FI_DATABASE.csv')
TEMPLATE_DIR = os.path.join(REPO_ROOT, 'templates')
TEMPLATE_FILE = 'landing_template.html'
OUTPUT_DIR   = os.path.join(REPO_ROOT, 'output')

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

def init_template():
    global env, template
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template(TEMPLATE_FILE)

# Helper per campi multilingua

def get_field(row, base, lang=None):
    key = f"{base}_{lang}" if lang else base
    return (row.get(key, '') or '').strip()

# Generazione pagine

def generate_pages():
    verify_paths()
    init_template()
    count = 0
    with open(DATA_CSV, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for raw in reader:
            row = {k.strip().lstrip('\ufeff'): v for k, v in raw.items()}
            aid = row.get('ArticleID', '').strip()
            if not aid:
                continue

            # Date handling with new fields
            publication_date = row.get('PublicationDate', '')
            submission_date = row.get('SubmissionDate', '')
            issue_date = row.get('IssueDate', '')
            raw_citation = row.get('Citation_Date', '')
            try:
                dt = isoparse(raw_citation).replace(tzinfo=gettz('Europe/Rome'))
                date_iso = dt.isoformat()
            except:
                date_iso = f"{raw_citation}T00:00:00+01:00"

            # Slug and output file
            title_en = get_field(row, 'Title', 'en')
            slug = slugify(title_en)
            outfile = os.path.join(OUTPUT_DIR, f"{aid}-{slug}.html")

            # Meta generali including new date fields
            authors_list = parse_authors(row.get('Authors_Detail','[]'))
            references_list = parse_references(row.get('References','[]'))
            general = {
                'Journal_Title': row.get('Journal_Title'),
                'Journal_ISSN': row.get('Journal_ISSN'),
                'Journal_Publisher': row.get('Journal_Publisher'),
                'PublicationDate': publication_date,
                'PublicationYear': row.get('PublicationYear', ''),
                'SubmissionDate': submission_date,
                'IssueDate': issue_date,
                'Volume': row.get('Volume') or 'missing data',
                'Issue': row.get('Issue') or 'missing data',
                'License_URL': row.get('License_URL'),
                'License_Type': row.get('License_Type'),
                'DOI': row.get('DOI'),
                'Citation_Date': raw_citation,
                'DatePublishedISO': date_iso,
                'Pages': f"{row.get('First_Page','')}-{row.get('Last_Page','')}".strip('-'),
                'Full_Text_HTML_URL': row.get('Full_Text_HTML_URL'),
                'PDF_URL': row.get('PDF_URL'),
                'Full_Text_XML_URL': row.get('Full_Text_XML_URL'),
                'Authors': authors_list,
                'Article_Type': row.get('Article_Type'),
                'References': references_list
            }

            # Language sections
            languages = []
            for lg in LANGUAGES:
                languages.append({
                    'lang': lg,
                    'title': get_field(row, 'Title', lg) or 'missing data',
                    'abstract': get_field(row, 'Abstract', lg) or 'missing data',
                    'keywords': get_field(row, 'Keywords', lg) or 'missing data'
                })

            context = {
                'journal': JOURNAL_META,
                'general': general,
                'languages': languages,
                'article_id': aid
            }

            rendered = template.render(context)
            with open(outfile, 'w', encoding='utf-8') as f:
                f.write(rendered)
            print(f"Generata: {outfile}")
            count += 1
    print(f"Totale: {count} pagine generate in '{OUTPUT_DIR}'.")

if __name__ == '__main__':
    generate_pages()
