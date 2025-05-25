<!DOCTYPE html>
<html lang="{{ journal.language }}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <meta name="alternate-site" content="This is an officially curated alternate landing page for repository, SEO, and indexing purposes. Maintained by the Executive Editorial Office and Pensa MultiMedia.">

  <title>{{ languages[0].title }} | {{ journal.title }} (Alternate Landing Page)</title>
  <meta name="description" content="{{ languages[0].abstract }}">
  <meta name="keywords" content="{{ languages[0].keywords }}">
  <link rel="canonical" href="{{ mirror_url }}">

  <!-- Journal-level metadata -->
  <meta name="journal_title" content="{{ journal.title }}">
  <meta name="journal_abbrev" content="{{ journal.abbrev }}">
  <meta name="journal_alternative" content="{{ journal.alternative }}">
  <meta name="journal_publisher" content="{{ journal.publisher }}">
  <meta name="journal_editor" content="{{ journal.editor }}">
  <meta name="journal_director" content="{{ journal.director }}">
  <meta name="journal_issn" content="{{ journal.issn }}">
  <meta name="journal_issn_l" content="{{ journal.issn_l }}">
  <meta name="journal_url" content="{{ journal.url }}">
  <meta name="journal_license" content="{{ journal.license }}">

  {% for sec in languages %}
    <meta name="DC.Title" xml:lang="{{ sec.lang }}" content="{{ sec.title }}">
    <meta name="DC.Description" xml:lang="{{ sec.lang }}" content="{{ sec.abstract }}">
    <meta name="DC.Subject" xml:lang="{{ sec.lang }}" content="{{ sec.keywords }}">
  {% endfor %}

  <meta name="DC.Publisher" content="{{ journal.publisher }}">
  <meta name="DC.Rights" content="CC BY 4.0">
  <meta name="DC.Identifier" content="{{ mirror_url }}">
  <meta name="DC.Source" content="{{ journal.url }}">
  <meta name="DC.Type" content="Text.Serial.Journal">
  <meta name="DC.Language" content="{{ journal.language }}">
  <meta name="DC.Rights.Holder" content="Pensa MultiMedia (until 2022); Authors (from 2022)">
  <meta name="DC.Coverage" content="Italia; Europa; internazionale">
  <meta name="DC.Date.issued" content="{{ general.IssueDate }}">
  <meta name="DC.Date.available" content="{{ general.PublicationDate }}">

  <!-- JATS4R / Highwire -->
  <meta name="citation_title" content="{{ languages[0].title }}">
  {% for auth in general.Authors %}
    <meta name="citation_author" content="{{ auth.name }}">
  {% endfor %}
  <meta name="citation_publication_date" content="{{ general.IssueDate }}T00:00:00+01:00">
  <meta name="citation_online_date" content="{{ general.PublicationDate }}T00:00:00+01:00">
  <meta name="citation_journal_title" content="{{ journal.title }}">
  <meta name="citation_issn" content="{{ journal.issn }}">
  <meta name="citation_firstpage" content="{{ general.Pages.split('-')[0] }}">
  <meta name="citation_lastpage" content="{{ general.Pages.split('-')[1] if '-' in general.Pages else '' }}">
  <meta name="citation_pdf_url" content="{{ general.PDF_URL }}">
  <meta name="citation_fulltext_html_url" content="{{ mirror_url }}">
  {% for ref in general.References %}
    <meta name="DC.Relation" content="{{ ref|striptags }}">
    <meta name="citation_reference" content="{{ ref|striptags }}">
  {% endfor %}

  <!-- JSON-LD Schema.org -->
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "ScholarlyArticle",
    "headline": "{{ languages[0].title }}",
    "name": [{% for sec in languages %}{"@value": "{{ sec.title }}", "@language": "{{ sec.lang }}"}{% if not loop.last %}, {% endif %}{% endfor %}],
    "author": [
      {% for auth in general.Authors %}{"@type": "Person", "name": "{{ auth.name }}", "url": "{{ auth.orcid }}"}{% if not loop.last %}, {% endif %}{% endfor %}
    ],
    "publisher": { "@type": "Organization", "name": "{{ journal.publisher }}" },
    "datePublished": "{{ general.IssueDate }}T00:00:00+01:00",
    "dateCreated": "{{ general.PublicationDate }}T00:00:00+01:00",
    "inLanguage": "{{ journal.language }}",
    "citation": [{% for ref in general.References %}"{{ ref|striptags }}"{% if not loop.last %}, {% endif %}{% endfor %}],
    "isAccessibleForFree": true,
    "license": "{{ journal.license }}",
    "identifier": "{{ general.DOI }}",
    "url": "{{ mirror_url }}",
    "sameAs": "{{ journal.url }}",
    "mainEntityOfPage": "{{ mirror_url }}",
    "additionalProperty": [
      {
        "@type": "PropertyValue",
        "name": "alternate",
        "value": "This is an officially maintained alternate landing page by the Executive Editorial Office and Pensa MultiMedia."
      }
    ]
  }
  </script>

  <!-- Open Graph -->
  <meta property="og:type" content="article">
  <meta property="og:title" content="{{ languages[0].title }}">
  <meta property="og:description" content="{{ languages[0].abstract }}">
  <meta property="og:url" content="{{ mirror_url }}">
  <meta property="og:site_name" content="{{ journal.title }} (Indexing Archive)">
  {% for sec in languages %}
    <meta property="og:locale:alternate" content="{{ sec.lang }}">
  {% endfor %}
  <meta property="og:locale" content="en_US">

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{{ languages[0].title }}">
  <meta name="twitter:description" content="{{ languages[0].abstract }}">
