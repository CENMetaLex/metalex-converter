# -*- coding: utf-8 -*-
'''
MetaLex Converter
=================

@author: Rinke Hoekstra
@contact: hoekstra@uva.nl
@organization: Universiteit van Amsterdam
@version: 0.1
@status: beta
@website: http://doc.metalex.eu
@copyright: 2011, Rinke Hoekstra, Universiteit van Amsterdam

@license: MetaLex Converter is free software, you can redistribute it and/or modify
it under the terms of GNU Affero General Public License
as published by the Free Software Foundation, either version 3
of the License, or (at your option) any later version.

You should have received a copy of the the GNU Affero
General Public License, along with MetaLex Converter. If not, see


Additional permission under the GNU Affero GPL version 3 section 7:

If you modify this Program, or any covered work, by linking or
combining it with other code, such other code is not for that reason
alone subject to any of the requirements of the GNU Affero GPL
version 3.

@summary: This module produces a Whoosh index of the titles and citation titles of expressions of all works in the triple store.

'''
from whoosh.index import create_in, open_dir
from whoosh.fields import ID, DATETIME, TEXT, Schema
from whoosh.query import *
from whoosh.qparser import QueryParser
import os.path
import glob
from SPARQLWrapper import SPARQLWrapper, JSON
from datetime import datetime
import re


SPARQL_ENDPOINT = "http://doc.metalex.eu:8000/sparql/"
INDEX_DIR = "/var/metalex/store/index"
#INDEX_DIR = "index"
DOCS_DIR = "/var/metalex/store/data"
#DOCS_DIR = ".."



filelist = glob.glob("{}/*_ml.xml".format(DOCS_DIR))


schema = Schema(uri = ID(stored = True), valid = DATETIME(stored = True), title = TEXT, ctitle = TEXT)

# should become /var/metalex/store/index
if not os.path.exists(INDEX_DIR) :
    os.mkdir(INDEX_DIR)
    ix = create_in(INDEX_DIR, schema)
else :
    ix = open_dir(INDEX_DIR)

writer = ix.writer()
searcher = ix.searcher()

#print list(searcher.lexicon("uri"))

bwbid_set = set()
expression_uri_set = set()

sparql = SPARQLWrapper(SPARQL_ENDPOINT)

# Get all BWBIDs and Work URIs from the files currently in the store
for f in filelist :
    match = re.search(r'(?P<bwbid>BWB.*?)_', f)
    if match == None :
        print "No match for BWBID, strange..."
    else :
        bwbid_set.add(match.group('bwbid'))

# Get all Expression URIs that realise the works we just found
for bwbid in bwbid_set :
    print bwbid

    work_uri = "http://doc.metalex.eu/id/{}".format(bwbid)

    # Query to retrieve all expressions of a  work

    q = """PREFIX dcterms: <http://purl.org/dc/terms/> 
                PREFIX metalex: <http://www.metalex.eu/schema/1.0#> 
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
                PREFIX foaf: <http://xmlns.com/foaf/0.1/>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
                
                SELECT DISTINCT ?expression WHERE {
                   <""" + work_uri + """> a metalex:BibliographicWork .
                   ?expression metalex:realizes <""" + work_uri + """> .
                } """

    sparql.setQuery(q)
    sparql.setReturnFormat(JSON)
    sparql_results = sparql.query().convert()


    for row in sparql_results['results']['bindings'] :
        expression_uri = row['expression']['value']
        expression_uri_set.add(expression_uri)


# Get relevant metadata for expressions not currently indexed.
for uri in expression_uri_set :
    try :
        wq = Term("uri", uri.decode('utf-8'))

        results = searcher.search(wq)

        if len(results) > 1 :
            print "Document {} already indexed".format(uri)
        else :
            q = """PREFIX dcterms: <http://purl.org/dc/terms/> 
                PREFIX metalex: <http://www.metalex.eu/schema/1.0#> 
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
                PREFIX foaf: <http://xmlns.com/foaf/0.1/>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
                
                SELECT DISTINCT ?title ?date ?ctitle WHERE {
                   <""" + uri + """> a metalex:BibliographicExpression .
                   <""" + uri + """> dcterms:valid ?date .
                   <""" + uri + """> dcterms:title ?title .
                   OPTIONAL { <""" + uri + """> dcterms:alternative ?ctitle . }
                } """


            sparql = SPARQLWrapper(SPARQL_ENDPOINT)
            sparql.setQuery(q)

            sparql.setReturnFormat(JSON)
            sparql_results = sparql.query().convert()


            for row in sparql_results['results']['bindings'] :
#                print row
                title = row['title']['value']
                valid = row['date']['value']
                
                if type(title) != unicode :
                    title = title.decode('utf-8')
                if type(uri) != unicode :
                        uri = uri.decode('utf-8')

                valid_date = datetime.strptime(valid, '%Y-%m-%d')

                if 'value' in row['ctitle'] :
                    ctitle = row['ctitle']['value']
                    if type(ctitle) != unicode :
                        ctitle = ctitle.decode('utf-8')
                    writer.add_document(uri = uri, title = title, ctitle = ctitle, valid = valid_date)
                    print uri, title, ctitle, valid
                else :
                    writer.add_document(uri = uri, title = title, valid = valid_date)
                    print uri, title, valid


                


    except Exception as e:
        print "Some error: {}".format(e)
        print e

writer.commit()

