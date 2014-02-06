import xml.sax
import urllib2
import glob
import re
import sys

hcontainers = ['root','bijlage', 'wijzig-divisie', 'circulaire', 'afdeling', 'deel', 'definitie', 'boek', 'wijzig-artikel', 'aanhef', 'noot', 'wetcitaat', 'regeling', 'hoofdstuk', 'preambule', 'sub-paragraaf', 'titeldeel', 'wijzig-lid-groep', 'divisie', 'artikel.toelichting', 'artikel', 'citaat-artikel', 'officiele-inhoudsopgave', 'model', 'artikel.toelichtingartikel', 'paragraaf', 'verdragtekst', 'circulaire.divisie', 'enig-artikel', 'regeling-sluiting']

PARENT = 'http://www.metalex.eu/schema/1.0#parent'

class ExpressionHandler(xml.sax.ContentHandler):
    
    parents = []
    
    def __init__(self):
        xml.sax.ContentHandler.__init__(self)
        
    def startElement(self, name, attrs):
        # print self.parents
        #print attrs
        if 'about' in attrs and self.parents != []:
            expression = attrs.getValue('about')
            print attrs
            if self.parents != [] :
                out.write("<{}> <{}> <{}> . \n".format(expression,PARENT,self.parents[-1]))
                
            if 'class' in attrs.keys():
                c = attrs.getValue('class')
                print "yes"
                
                if c in hcontainers:
                    self.parents.append(expression)
                else :
                    self.parents.append(self.parents[-1])
            


        
        
                
    def endElement(self, name):
        if self.parents != [] :
            del self.parents[-1]
       
                
            
    def write(self,s,p,o):
        out.write("<{}> <{}> <{}> .\n".format(s,p,o))
        
    def writes(self,s,p,string):
        out.write("<{}> <{}> \"{}\"^^<http://www.w3.org/2001/XMLSchema#string> .\n".format(s,p,string))
        
    def writed(self,s,p,date):
        out.write("<{}> <{}> \"{}\"^^<http://www.w3.org/2001/XMLSchema#date> .\n".format(s,p,date))
        


if __name__ == '__main__':
    print "Usage: parent [MetaLexFilesMask] [OutFile.nt]"
    
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




    