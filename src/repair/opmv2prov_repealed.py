from SPARQLWrapper import SPARQLWrapper

q = """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX opmv: <http://purl.org/net/opmv/ns#>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX dcterms: <http://purl.org/dc/terms/>

CONSTRUCT {
  ?e prov:wasGeneratedAtTime ?t .
  ?e prov:wasGeneratedBy ?p .
  ?p prov:endedAtTime ?t .  
  ?p a prov:Activity .
} WHERE {
  ?e dcterms:valid ?t .
  ?e opmv:wasGeneratedBy ?p .
  MINUS {?e prov:wasGeneratedAtTime ?time}
} 
"""

sparql = SPARQLWrapper('http://doc.metalex.eu:8000/sparql')

sparql.setQuery(q)

r = sparql.query().convert()

r.serialize('opmv2prov_repealed.n3',format='turtle')