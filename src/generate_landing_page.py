from datetime import datetime
from dateutil.tz import gettz

#!/usr/bin/env python3
r"""
generate_landing_page.py
Genera landing page HTML dal database CSV.
Richiede: pip install jinja2 python-dateutil
"""
import os, csv, sys, re, unicodedata, json
from dateutil.parser import isoparse
from dateutil.tz import gettz
from jinja2 import Environment, FileSystemLoader, select_autoescape

# === CONFIGURAZIONE ===
# script is in src/, repo root is 1 level up
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT  = os.path.dirname(SCRIPT_DIR)

# now data/ and templates/ at repo root
data_csv      = os.path.join(REPO_ROOT, 'data', 'FI_DATABASE.csv')
template_dir  = os.path.join(REPO_ROOT, 'templates')
template_file = 'landing_template.html'
output_dir    = os.path.join(REPO_ROOT, 'output')
index_template = 'index_template.html'

LANGUAGES = ['en', 'it', 'fr', 'es', 'pt']

# Journal metadata
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

# Base URLs
tmpl_base     = 'https://formazione-insegnamento.eu'
ORIGINAL_BASE = JOURNAL_META['url'] + '/article/view'

# Utility to slugify text
def slugify(text, max_length=60):
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')[:max_length]

# Parse JSON authors
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

# Parse JSON references
def parse_references(ref_str):
    try:
        refs = json.loads(ref_str)
        processed = []
        for r in refs:
            r_html = re.sub(
                r'(https?://[^\s]+)',
                lambda m: f'<a href="{m.group(0)}" target="_blank">{m.group(0)}</a>',
                r
            )
            processed.append(r_html)
        return processed
    except:
        return []

# Verify input/output paths
def verify_paths():
    if not os.path.isfile(data_csv):
        print(f"Errore: CSV non trovato: {data_csv}")
        sys.exit(1)
    if not os.path.isdir(template_dir):
        print(f"Errore: template non trovato: {template_dir}")
        sys.exit(1)
    os.makedirs(output_dir, exist_ok=True)

# Initialize Jinja2 templates
env = None
template = None
index_tmpl = None

def init_template():
    global env, template, index_tmpl
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(['html','xml'])
    )
    env.filters['slugify'] = slugify
    template = env.get_template(template_file)
    index_tmpl = env.get_template(index_template)

# Helper to fetch multi-language fields
def get_field(row, base, lang=None):
    key = f"{base}_{lang}" if lang else base
    return (row.get(key, '') or '').strip()

# Main page generation
def generate_pages():
    verify_paths()
    init_template()
    count = 0
    archive = {}

    with open(data_csv, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for raw in reader:
            row = {k.strip(): v for k,v in raw.items()}
            aid = row.get('ArticleID','').strip()
            if not aid:
                continue

            # parse dates
            raw_cit = row.get('Citation_Date','')
            try:
                dt = isoparse(raw_cit).replace(tzinfo=gettz('Europe/Rome'))
                date_iso = dt.isoformat()
            except:
                date_iso = f"{raw_cit}T00:00:00+01:00"

            # title and slug
            title_en = get_field(row,'Title','en') or get_field(row,'Title','it') or ''
            slug = (row.get('Slug') or slugify(title_en) or aid).strip()

            # year, volume, issue
            raw_year = row.get('PublicationYear','').strip()
            try:
                year = str(int(float(raw_year)))
            except:
                year = raw_year or 'unknown-year'
            try:
                vol = str(int(year) - 2002)
            except:
                raw_vol = row.get('Volume','').strip()
                vol = raw_vol.replace(' ','-') or '0'
            raw_issue = row.get('Issue','').strip()
            issue = raw_issue.replace(' ','-') or '0'

            # build dirs and paths
            vol_dir = f"{year}-{vol}"
            issue_dir = issue
            filename = f"{slug}.html"
            rel_path = f"{vol_dir}/{issue_dir}/{filename}"
            out_dir = os.path.join(output_dir,vol_dir,issue_dir)
            os.makedirs(out_dir,exist_ok=True)
            out_file = os.path.join(out_dir,filename)

            # parse lists
            authors_list = parse_authors(row.get('Authors_Detail','[]'))
            refs_list    = parse_references(row.get('References','[]'))

            # page metadata
            general = {
                'Journal_Title': row.get('Journal_Title'),
                'Journal_ISSN': row.get('Journal_ISSN'),
                'Journal_Publisher': row.get('Journal_Publisher'),
                'PublicationDate': row.get('PublicationDate',''),
                'PublicationYear': year,
                'SubmissionDate': row.get('SubmissionDate',''),   # <-- FIXED HERE
                'IssueDate': row.get('IssueDate',''),
                'Volume': vol,
                'Issue': issue,
                'Pages': f"{row.get('First_Page','')}-{row.get('Last_Page','')}".strip('-'),
                'DOI': row.get('DOI'),
                'Citation_Date': raw_cit,
                'DatePublishedISO': date_iso,
                'Full_Text_HTML_URL': row.get('Full_Text_HTML_URL'),
                'PDF_URL': row.get('PDF_URL'),
                'Full_Text_XML_URL': row.get('Full_Text_XML_URL'),
                'License_URL': row.get('License_URL'),
                'License_Type': row.get('License_Type'),
                'Authors': authors_list,
                'Article_Type': row.get('Article_Type'),
                'References': refs_list
            }

            # render article page
            context = {
                'journal': JOURNAL_META,
                'general': general,
                'languages': [{
                    'lang': lg,
                    'title': get_field(row,'Title',lg),
                    'abstract': get_field(row,'Abstract',lg),
                    'keywords': get_field(row,'Keywords',lg)
                } for lg in LANGUAGES],
                'article_id': aid,
                'title_en': title_en,
                'path': rel_path,
                'mirror_url': f"{tmpl_base}/{rel_path}",
                'original_url': f"{ORIGINAL_BASE}/{aid}"
            }
            html = template.render(context)
            with open(out_file,'w',encoding='utf-8') as f:
                f.write(html)
            print(f"Generata: {out_file}")
            count += 1

            # build archive entry with sorting
            first_page = row.get('First_Page','').strip()
            if first_page.isdigit():
                sort_key = (1, int(first_page))
            else:
                sort_key = (0, first_page.lower() or '')

            archive.setdefault(year, {}) \
                   .setdefault(vol, {}) \
                   .setdefault(issue, []) \
                   .append({
                       'title_en': title_en,
                       'path': rel_path,
                       'authors': [a['name'] for a in authors_list if a.get('name')],
                       'pages': general['Pages'],
                       'page_sort_key': sort_key
                   })

    # render index page
    idx_html = index_tmpl.render(
        journal=JOURNAL_META,
        archive=archive,
        generated_at=datetime.now(gettz('Europe/Rome')).isoformat()
    )
    idx_file = os.path.join(output_dir,'index.html')
    with open(idx_file,'w',encoding='utf-8') as f:
        f.write(idx_html)
    print(f"Generata: {idx_file}")
    print(f"Totale: {count} pagine generate in '{output_dir}'.")

if __name__ == '__main__':
    generate_pages()
