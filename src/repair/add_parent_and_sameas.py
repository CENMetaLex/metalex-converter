import xml.sax
import urllib2
import glob
import re
import sys

hcontainers = ['bijlage', 'wijzig-divisie', 'circulaire', 'afdeling', 'deel', 'definitie', 'boek', 'wijzig-artikel', 'aanhef', 'noot', 'wetcitaat', 'regeling', 'hoofdstuk', 'preambule', 'sub-paragraaf', 'titeldeel', 'wijzig-lid-groep', 'divisie', 'artikel.toelichting', 'artikel', 'citaat-artikel', 'officiele-inhoudsopgave', 'model', 'artikel.toelichtingartikel', 'paragraaf', 'verdragtekst', 'circulaire.divisie', 'enig-artikel', 'regeling-sluiting']

PARENT = 'http://www.metalex.eu/schema/1.0#parent'
REALIZES = 'http://www.metalex.eu/schema/1.0#realizes'
SAMEAS = 'http://www.w3.org/2002/07/owl#sameAs'

class ExpressionHandler(xml.sax.ContentHandler):
    
    parents = []
    
    def __init__(self):
        xml.sax.ContentHandler.__init__(self)
        
    def startElement(self, name, attrs):
        # print self.parents
        #print attrs
        # print self.attributes
        
        expression = attrs.get('about',None)
        c = attrs.get('class',None)
        
        
        # print name, expression, c, self.parents
        
        if expression :
            if self.parents != [] :
                out.write("<{}> <{}> <{}> . \n".format(expression,PARENT,self.parents[-1]))
                
            if str(c) in hcontainers or name == 'hcontainer' or name == 'root':
                self.parents.append(expression)
                
                m = re.search('(?P<bwb>.*/BWB.*?/)(?P<path>.*/)?(?P<hcontainer>{})(?P<version>/.*)'.format(c),expression)
                
                if not m:
                    pass
                else :
                    short = "{}{}{}".format(m.group('bwb'),m.group('hcontainer'),m.group('version'))
                    shortwork = "{}{}{}".format(m.group('bwb'),m.group('hcontainer'))
                    out.write("<{}> <{}> <{}> . \n".format(expression,SAMEAS,short))
                    out.write("<{}> <{}> <{}> . \n".format(expression,REALIZES,shortwork))
                
            elif self.parents != [] :
                self.parents.append(self.parents[-1])
                
        else :
            self.parents.append(self.parents[-1])
            


        
        
                
    def endElement(self, name):
        if self.parents != [] :
            del self.parents[-1]
       
                



if __name__ == '__main__':
    print "Usage: python add_parent_and_sameas.py '[MetaLexFilesMask]' [OutFile.nt]"
    
    print sys.argv
    path = sys.argv[1]
    outpath = sys.argv[2]
    out = open(outpath,'w')
    for mlfile in glob.glob(path):
        try :
            xml.sax.parse(open(mlfile),ExpressionHandler())
        except Exception as e :
            print mlfile
            print e

    out.close()




    