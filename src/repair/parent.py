from SPARQLWrapper import SPARQLWrapper, JSON
import re

hcontainers = ["afdeling","bijlage","boek","circulaire.divisie","citaat-artikel","deel","divisie","hoofdstuk","model","officiele-inhoudsopgave","paragraaf","sub-paragraaf","titeldeel","verdragtekst","wetcitaat","wijzig-artikel","wijzig-divisie","wijzig-lid-groep","artikel"]

ENDPOINT = 'http://doc.metalex.eu:8000/sparql/'
PARENT = 'http://www.metalex.eu/schema/1.0#parent'

outfile = 'mappings_{}.nt'
posfile = 'last'



if __name__ == '__main__':
    print "This script queries the MDS for all expressions, and generates 'parent' relations between expressions and their parent HContainer elements"
    
    sparql = SPARQLWrapper(ENDPOINT)
    sparql.setReturnFormat(JSON)
    
    query = """
        PREFIX metalex: <http://www.metalex.eu/schema/1.0#>
        SELECT DISTINCT ?e WHERE {{
            ?e a metalex:BibliographicExpression .
        }} LIMIT {0} OFFSET {1}
    """
    
    step = 200000
    pos  = int(open(posfile,'r').read())
    
    while True:
        print "OFFSET {} LIMIT {}".format(pos,step)
        out = open(outfile.format(pos),'w')
        
        sparql.setQuery(query.format(step,pos))
        print "Running query",
        results = sparql.query().convert()
        print "... done"
        if len(results) < 1 :
            print "No more results"
            out.close()
            break
            
        for r in results['results']['bindings'] :
            expression = r['e']['value']
            m = re.search('(?P<regulation>.*BWB.*?)/(?P<path>.*/)?(?P<hcontainer>(artikel|enig-artikel|aanhef|artikel\.toelichting|preambule|deel|bijlage|definitie|noot|circulaire.divisie|circulaire|regeling-sluiting|verdragtekst|titeldeel|hoofdstuk|paragraaf|regeling|wijzig-artikel|afdeling)/.+?/)(.*/)?(?P<lang>\w{2})?/(?P<date>\d\d\d\d-\d\d-\d\d)', expression)

            if not m:
                m = re.search('(?P<regulation>.*BWB.*?)/(.*/)?(?P<lang>\w{2})?/(?P<date>\d\d\d\d-\d\d-\d\d)', expression)
            
            if not m:
                m = re.search('(?P<regulation>.*BWB.*?)/(.*/)?(?P<date>\d\d\d\d-\d\d-\d\d)', expression)
            
            if not m :
                print m
                continue
            parent = ""
            groups = m.groupdict()
            for p in ['regulation','path','hcontainer','lang','date'] :
                if p in groups and groups[p]: 
                    parent += "{}/".format(groups[p])

            parent = parent.rstrip('/')
            parent = parent.replace('//','/')
            parent = parent.replace('http:/doc','http://doc')
               
            out.write("<{}> <{}> <{}> . \n".format(expression,PARENT,parent))
        
        pos += step
        
        open(posfile,'w').write(str(pos))
        out.close()
            


    