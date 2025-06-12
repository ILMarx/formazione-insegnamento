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

def clean_ref(r: str) -> str:
    """
    1) strip leading/trailing quotes
    2) collapse Excel-style "" → "
    3) remove literal \" sequences
    4) strip any HTML tags
    5) strip stray trailing quote on a URL
    """
    # 1 & 2
    text = r.strip().lstrip('"').rstrip('"').replace('""', '"')
    # 3
    text = text.replace('\\"', '')
    # 4 remove any HTML tags
    if re.search(r'<\/?[a-z][^>]*>', text, flags=re.IGNORECASE):
        text = re.sub(r'<[^>]+>', '', text).strip()
    # 5 drop a trailing quote after a URL, if any
    text = re.sub(r'(https?://[^\s"]+)"$', r'\1', text)
    return text

# === CONFIGURAZIONE DI BASE ===
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT  = os.path.dirname(SCRIPT_DIR)

data_csv      = os.path.join(REPO_ROOT, 'data', 'FI_metadata.csv')
template_dir  = os.path.join(REPO_ROOT, 'templates')
template_file = 'landing_template.html'
output_dir    = os.path.join(REPO_ROOT, 'output')
index_template = 'index_template.html'

LANGUAGES = ['en', 'it', 'fr', 'es', 'pt']

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

tmpl_base     = 'https://formazione-insegnamento.eu'
ORIGINAL_BASE = JOURNAL_META['url'] + '/article/view'

def slugify(text, max_length=60):
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')[:max_length]

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

def parse_references(ref_str: str):
    """
    1) try to JSON-load into a list of strings
    2) if that fails, split on </p> or blank lines, stripping any tags
    3) clean each via clean_ref()
    4) hyperlink URLs
    """
    txt = (ref_str or '').strip()
    # If wrapped in quotes, drop them and un-escape Excel-style
    if txt.startswith('"') and txt.endswith('"'):
        txt = txt[1:-1].replace('""', '"')

    # attempt JSON-parse
    try:
        raw = json.loads(txt)
        if not isinstance(raw, list):
            raise ValueError
        entries = raw
    except Exception:
        # fallback: split on HTML paragraphs or double newlines
        if '<p>' in txt.lower():
            parts = re.split(r'</p\s*>', txt, flags=re.IGNORECASE)
            entries = [re.sub(r'<[^>]+>', '', p).strip() for p in parts if p.strip()]
        else:
            entries = [p.strip() for p in re.split(r'\n{2,}', txt) if p.strip()]

    # clean + hyperlink each
    out = []
    for r in entries:
        c = clean_ref(r)
        c = re.sub(
            r'(https?://[^\s<]+)',
            lambda m: f'<a href="{m.group(0)}" target="_blank">{m.group(0)}</a>',
            c
        )
        out.append(c)
    return out

def verify_paths():
    if not os.path.isfile(data_csv):
        print(f"Errore: CSV non trovato: {data_csv}")
        sys.exit(1)
    if not os.path.isdir(template_dir):
        print(f"Errore: template non trovato: {template_dir}")
        sys.exit(1)
    os.makedirs(output_dir, exist_ok=True)

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

def get_field(row, base, lang=None):
    key = f"{base}_{lang}" if lang else base
    return (row.get(key, '') or '').strip()

def generate_pages():
    verify_paths()
    init_template()
    count = 0
    archive = {}
    now_string = datetime.now(gettz('Europe/Rome')).isoformat()

    with open(data_csv, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        all_rows = [dict((k.strip(), v) for k, v in row.items()) for row in reader]

        def safe_int(val):
            try: return int(val)
            except: return 0

        def first_page_sort(val):
            matches = re.findall(r'\d+', val)
            return int(matches[0]) if matches else 0

        def extract_year_from_issue(r):
            try:
                return isoparse(r.get('IssueDate', '')).year
            except:
                return 0
        
        rows = sorted(
            all_rows,
            key=lambda r: (
                extract_year_from_issue(r),
                safe_int(r.get('Volume', '0')),
                safe_int(r.get('Issue', '0')),
                first_page_sort(r.get('First_Page', '0'))
            )
        )

        for row in rows:
            aid = row.get('ArticleID','').strip()
            if not aid:
                continue

            raw_cit = row.get('Citation_Date','')
            try:
                dt = isoparse(raw_cit).replace(tzinfo=gettz('Europe/Rome'))
                date_iso = dt.isoformat()
            except:
                date_iso = f"{raw_cit}T00:00:00+01:00"

            title_en = get_field(row,'Title','en') or get_field(row,'Title','it') or ''
            slug_raw = row.get('Slug') or title_en or aid
            slug = slugify(slug_raw) or f"article-{aid}"

            issue_date_str = row.get('IssueDate', '').strip()
            try:
                issue_date = isoparse(issue_date_str)
                year = str(issue_date.year)
            except:
                year = 'unknown-year'
            vol = row.get('Volume','').strip() or '0'
            issue = row.get('Issue','').strip() or '0'

            vol_dir = f"{year}-{vol}"
            issue_dir = issue
            filename = f"{slug}.html"
            rel_path = f"{vol_dir}/{issue_dir}/{filename}"
            out_dir = os.path.join(output_dir,vol_dir,issue_dir)
            os.makedirs(out_dir,exist_ok=True)
            out_file = os.path.join(out_dir,filename)

            authors_list = parse_authors(row.get('Authors_Detail','[]'))
            refs_list    = parse_references(row.get('References',''))

            general = {
                'Journal_Title': row.get('Journal_Title'),
                'Journal_ISSN': row.get('Journal_ISSN'),
                'Journal_Publisher': row.get('Journal_Publisher'),
                'PublicationDate': row.get('PublicationDate',''),
                'PublicationYear': year,
                'SubmissionDate': row.get('SubmissionDate',''),
                'AcceptanceDate':  row.get('Accepted',''),
                'IssueDate': row.get('IssueDate',''),
                'Volume': row.get('Volume', ''),
                'Issue': row.get('Issue', ''),
                'Pages': f"{row.get('First_Page','')}-{row.get('Last_Page','')}".strip('-'),
                'DOI': row.get('DOI'),
                'Citation_Date': raw_cit,
                'DatePublishedISO': date_iso,
                'Full_Text_HTML_URL': row.get('HTML_URL_viewer'),
                'PDF_URL': row.get('PDF_URL_viewer'),
                'Full_Text_HTML_File': row.get('HTML_URL_file',''),
                'Full_Text_PDF_File': row.get('PDF_URL_file',''),
                'License_URL': row.get('License_URL'),
                'License_Type': row.get('License_Type'),
                'Copyrighted':    row.get('Copyrighted',''),
                'Updated':        row.get('Updated',''),
                'Withdrawn':      row.get('Withdrawn',''),
                'Authors': authors_list,
                'Article_Type': row.get('Article_Type'),
                'References': refs_list
            }

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
                'original_url': f"{ORIGINAL_BASE}/{aid}",
                'generated_at': now_string
            }
            html = template.render(context)
            with open(out_file,'w',encoding='utf-8') as f:
                f.write(html)
            print(f"Generata: {out_file}")
            count += 1

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

    idx_html = index_tmpl.render(
        journal=JOURNAL_META,
        archive=archive,
        generated_at=now_string
    )
    idx_file = os.path.join(output_dir,'index.html')
    with open(idx_file,'w',encoding='utf-8') as f:
        f.write(idx_html)
    print(f"Generata: {idx_file}")
    print(f"Totale: {count} pagine generate in '{output_dir}'.")

if __name__ == '__main__':
    generate_pages()
