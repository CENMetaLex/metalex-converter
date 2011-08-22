'''
Created on 19 Aug 2011

@author: hoekstra
'''
from whoosh.index import create_in, open_dir
from whoosh.fields import ID, DATETIME, TEXT, Schema
from whoosh.query import *
from whoosh.qparser import QueryParser
import os.path
from xml.etree.ElementTree import ElementTree
import glob
from SPARQLWrapper import SPARQLWrapper, JSON
from datetime import datetime

SPARQL_ENDPOINT = "http://doc.metalex.eu:8000/sparql/"
INDEX_DIR = "/var/metalex/store/index"
#INDEX_DIR = "index"
DOCS_DIR = "/var/metalex/store/data"
#DOCS_DIR = ".."

tree = ElementTree()

filelist = glob.glob("{}/*_ml.xml".format(DOCS_DIR))


schema = Schema(uri=ID(stored=True),valid=DATETIME(stored=True),title=TEXT,ctitle=TEXT)

# should become /var/metalex/store/index
if not os.path.exists(INDEX_DIR) :
    os.mkdir(INDEX_DIR)
    ix = create_in(INDEX_DIR, schema)
else :
    ix = open_dir(INDEX_DIR)

writer = ix.writer()
searcher = ix.searcher()

print list(searcher.lexicon("uri"))

for f in filelist :
    print f
    try :
        file_root = tree.parse(f)
        uri = file_root.attrib['about']
        
        wq = Term("uri",uri.decode('utf-8'))
        
        results = searcher.search(wq)
        
        if len(results) > 1 :
            print "Document already indexed"
        else :
            q = """PREFIX dcterms: <http://purl.org/dc/terms/> 
                PREFIX metalex: <http://www.metalex.eu/schema/1.0#> 
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
                PREFIX foaf: <http://xmlns.com/foaf/0.1/>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
                
                SELECT DISTINCT ?title ?date ?ctitle WHERE {
                   <"""+uri+"""> a metalex:BibliographicExpression .
                   <"""+uri+"""> dcterms:valid ?date .
                   <"""+uri+"""> dcterms:title ?title .
                   OPTIONAL { <"""+uri+"""> dcterms:alternative ?ctitle . }
                } """
                
    
            sparql = SPARQLWrapper(SPARQL_ENDPOINT)
            sparql.setQuery(q)
            
            sparql.setReturnFormat(JSON)
            sparql_results = sparql.query().convert()
            
            
            for row in sparql_results['results']['bindings'] :
                title = row['title']['value']
                valid = row['date']['value']
                
                valid_date = datetime.strptime(valid,'%Y-%m-%d')
                
                if 'ctitle' in row :
                    ctitle = row['ctitle']['value']
                    writer.add_document(uri=uri.decode('utf-8'),title=title.decode('utf-8'), ctitle=ctitle.decode('utf-8'), valid=valid_date)
                else :
                    writer.add_document(uri=uri.decode('utf-8'),title=title.decode('utf-8'), valid=valid_date)
                    ctitle = ''
                
                
                print uri, title, ctitle, valid
            
        
    except Exception as e:
        print "Some error: {}".format(e)
        print e
        
writer.commit()

