from flask import Flask, request, Response
import datetime
from xml.sax.saxutils import escape

app = Flask(__name__)

# Simulated article records (normally load from DB or JSON)
ARTICLES = [
    {
        'identifier': 'oai:formazione-insegnamento.eu:2024/23/7766',
        'datestamp': '2025-01-01',
        'title': {
            'en': 'Transversal Skills and Professional Motivation in Qualifying Courses for Secondary School: An Exploratory Investigation',
            'it': "Competenze trasversali e motivazione professionale nei percorsi abilitanti per la scuola secondaria: Un'indagine esplorativa",
            # ... other languages
        },
        'creator': [
            'Gianluca Amatori',
            'Maria Buccolo',
            'Alessia Travaglini',
        ],
        'subject': {
            'en': "Professional motivation; Skills; Training; Transversal skills; University",
            # ... other languages
        },
        'description': {
            'en': "Teacher training represents a crucial challenge for the construction of equitable, inclusive and accessible school contexts. ...",
            # ... other languages
        },
        'publisher': "Pensa MultiMedia",
        'date': '2025-01-01',
        'type': 'Text',
        'format': 'text/html',
        'identifier_url': 'https://formazione-insegnamento.eu/2024/23/7766-transversal-skills-and-professional-motivation-in-qualifying.html',
        'source': "Formazione & insegnamento",
        'language': 'it',
        'rights': 'CC BY 4.0',
        # ... more fields as needed
    },
    # Add more records as needed
]

BASE_URL = "https://formazione-insegnamento.eu/oai"

def oai_record_xml(article):
    return f"""
    <record>
      <header>
        <identifier>{escape(article['identifier'])}</identifier>
        <datestamp>{article['datestamp']}</datestamp>
        <setSpec>formazione-insegnamento</setSpec>
      </header>
      <metadata>
        <oai_dc:dc 
          xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" 
          xmlns:dc="http://purl.org/dc/elements/1.1/" 
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
          xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/ 
                              http://www.openarchives.org/OAI/2.0/oai_dc.xsd">
          <dc:title xml:lang="en">{escape(article['title']['en'])}</dc:title>
          <dc:title xml:lang="it">{escape(article['title']['it'])}</dc:title>
          {''.join(f'<dc:creator>{escape(c)}</dc:creator>' for c in article['creator'])}
          <dc:subject xml:lang="en">{escape(article['subject']['en'])}</dc:subject>
          <dc:description xml:lang="en">{escape(article['description']['en'])}</dc:description>
          <dc:publisher>{escape(article['publisher'])}</dc:publisher>
          <dc:date>{escape(article['date'])}</dc:date>
          <dc:type>{escape(article['type'])}</dc:type>
          <dc:format>{escape(article['format'])}</dc:format>
          <dc:identifier>{escape(article['identifier_url'])}</dc:identifier>
          <dc:source>{escape(article['source'])}</dc:source>
          <dc:language>{escape(article['language'])}</dc:language>
          <dc:rights>{escape(article['rights'])}</dc:rights>
        </oai_dc:dc>
      </metadata>
    </record>
    """

@app.route("/oai")
def oai_pmh():
    verb = request.args.get('verb')
    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    if verb == "Identify":
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">
  <responseDate>{now}</responseDate>
  <request verb="Identify">{BASE_URL}</request>
  <Identify>
    <repositoryName>Formazione &amp; insegnamento Mirror Archive</repositoryName>
    <baseURL>{BASE_URL}</baseURL>
    <protocolVersion>2.0</protocolVersion>
    <adminEmail>your@email.com</adminEmail>
    <earliestDatestamp>2025-01-01</earliestDatestamp>
    <deletedRecord>no</deletedRecord>
    <granularity>YYYY-MM-DD</granularity>
  </Identify>
</OAI-PMH>
"""
        return Response(xml, mimetype="application/xml")

    elif verb == "ListRecords":
        metadataPrefix = request.args.get("metadataPrefix")
        if metadataPrefix != "oai_dc":
            return Response("badArgument: Only oai_dc supported", status=400)
        records = "\n".join([oai_record_xml(a) for a in ARTICLES])
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">
  <responseDate>{now}</responseDate>
  <request verb="ListRecords" metadataPrefix="oai_dc">{BASE_URL}</request>
  <ListRecords>
    {records}
  </ListRecords>
</OAI-PMH>
"""
        return Response(xml, mimetype="application/xml")

    elif verb == "GetRecord":
        identifier = request.args.get("identifier")
        metadataPrefix = request.args.get("metadataPrefix")
        if metadataPrefix != "oai_dc":
            return Response("badArgument: Only oai_dc supported", status=400)
        for a in ARTICLES:
            if a['identifier'] == identifier:
                xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">
  <responseDate>{now}</responseDate>
  <request verb="GetRecord" identifier="{identifier}" metadataPrefix="oai_dc">{BASE_URL}</request>
  <GetRecord>
    {oai_record_xml(a)}
  </GetRecord>
</OAI-PMH>
"""
                return Response(xml, mimetype="application/xml")
        return Response("idDoesNotExist", status=404)

    else:
        # Supported verbs: Identify, ListRecords, GetRecord
        return Response("badVerb", status=400)

if __name__ == "__main__":
    app.run(port=8080, debug=True)

