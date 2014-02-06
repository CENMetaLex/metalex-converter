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

@summary: This module defines a utility script for adding Simple Event Model descriptions for MetaLex events described in a 4Store triplestore
'''

import urllib2
import urllib
#from rdflib import ConjunctiveGraph
from SPARQLWrapper import SPARQLWrapper, JSON
#from poster.encode import multipart_encode
#import pprint

upload_url = "http://doc.metalex.eu:8000/data/"



# Get Graph URIs

q = """PREFIX dcterms: <http://purl.org/dc/terms/> 
PREFIX metalex: <http://www.metalex.eu/schema/1.0#> 
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX bwb: <http://doc.metalex.eu/bwb/ontology/>

SELECT DISTINCT ?x WHERE {
   ?x bwb:bwb-id ?id .
   ?x a metalex:BibliographicExpression .
}"""

sparql = SPARQLWrapper("http://doc.metalex.eu:8000/sparql/")
sparql.setQuery(q)
sparql.addCustomParameter("soft-limit", "-1")
    
sparql.setReturnFormat(JSON)

results = sparql.query().convert()

for result in results['results']['bindings'] :
    uri = result['x']['value']
    
    construct_query = """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX ml: <http://www.metalex.eu/schema/1.0#>
    PREFIX sem: <http://semanticweb.cs.vu.nl/2009/11/sem/>
    
    CONSTRUCT {
      ?e rdf:type sem:Event .
      ?e sem:eventType ml:LegislativeModification .
      ?e sem:hasTime ?d .
      ?d rdf:type sem:Time .
      ?d sem:timeType ml:Date .
      ?d sem:hasTimeStamp ?date .
    }
    WHERE {
     <"""+ uri + """> ml:resultOf ?e .
     ?e rdf:type ml:LegislativeModification .
     ?e ml:date ?d .
     ?d rdf:value ?date .
    } LIMIT 10"""
    
    sparql.setQuery(construct_query)
    
    graph = sparql.query().convert()
    
    print graph
    
    data = {"data" : graph, "mime-type": 'application/x-turtle', "graph" : uri }
                     
    data_encoded = urllib.urlencode(data)
    
    request = urllib2.Request(upload_url, data=data_encoded)
    
    reply = urllib2.urlopen(request).read()
    
    print reply
    
    
    

