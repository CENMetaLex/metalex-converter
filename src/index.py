'''
Created on 19 Aug 2011

@author: hoekstra
'''
from whoosh.index import create_in
from whoosh.fields import ID, DATETIME, TEXT, Schema
import os.path
from xml.etree.ElementTree import ElementTree
import glob
from SPARQLWrapper import SPARQLWrapper, JSON
from datetime import datetime

SPARQL_ENDPOINT = "http://doc.metalex.eu:8000/sparql/"
INDEX_DIR = "/var/metalex/store/index"
DOCS_DIR = "/var/metalex/store/data"

tree = ElementTree()

list = glob.glob("{}/*_ml.xml".format(DOCS_DIR))


schema = Schema(uri=ID(stored=True),valid=DATETIME,title=TEXT)

# should become /var/metalex/store/index
if not os.path.exists("index") :
    os.mkdir("index")

ix = create_in("index", schema)

writer = ix.writer()

for f in list :
    print f
    try :
        file_root = tree.parse(f)
        uri = file_root.attrib['about']
        
        q = """PREFIX dcterms: <http://purl.org/dc/terms/> 
            PREFIX metalex: <http://www.metalex.eu/schema/1.0#> 
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            PREFIX foaf: <http://xmlns.com/foaf/0.1/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
            
            SELECT DISTINCT ?title ?date WHERE {
               <"""+uri+"""> a metalex:BibliographicExpression .
               <"""+uri+"""> dcterms:valid ?date .
               <"""+uri+"""> dcterms:title ?title .
            } """
            

        sparql = SPARQLWrapper(SPARQL_ENDPOINT)
        sparql.setQuery(q)
        
        sparql.setReturnFormat(JSON)
        sparql_results = sparql.query().convert()
        
        
        for row in sparql_results['results']['bindings'] :
            title = row['title']['value']
            valid = row['date']['value']
            
            valid_date = datetime.strptime(valid,'%Y-%m-%d')
            
            
            writer.add_document(uri=uri.decode('utf-8'),title=title.decode('utf-8'),valid=valid_date)
            print uri, title, valid
            
                    
    except Exception as e:
        print "Some error: {}".format(e)

