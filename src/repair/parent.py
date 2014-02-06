import xml.sax
import urllib2
import glob
import re
import sys

PARENT = 'http://www.metalex.eu/schema/1.0#parent'

class ExpressionHandler(xml.sax.ContentHandler):
    
    def __init__(self):
        xml.sax.ContentHandler.__init__(self)
        
    def startElement(self, name, attrs):
        if 'about' in attrs:
            expression = attrs.getValue("about")

            m = re.search('(?P<regulation>.*BWB.*?)/(?P<path>.*/)?(?P<hcontainer>(artikel|enig-artikel|aanhef|artikel\.toelichting|preambule|deel|bijlage|definitie|noot|circulaire.divisie|circulaire|regeling-sluiting|verdragtekst|titeldeel|hoofdstuk|paragraaf|regeling|wijzig-artikel|afdeling)/.+?/)(.*/)?(?P<lang>\w{2})?/(?P<date>\d\d\d\d-\d\d-\d\d)', expression)

            if not m:
                m = re.search('(?P<regulation>.*BWB.*?)/(.*/)?(?P<lang>\w{2})?/(?P<date>\d\d\d\d-\d\d-\d\d)', expression)
        
            if not m:
                m = re.search('(?P<regulation>.*BWB.*?)/(.*/)?(?P<date>\d\d\d\d-\d\d-\d\d)', expression)
        
            if not m :
                print expression
                return
                
            parent = ""
            groups = m.groupdict()
            for p in ['regulation','path','hcontainer','lang','date'] :
                if p in groups and groups[p]: 
                    parent += "{}/".format(groups[p])

            parent = parent.rstrip('/')
            parent = parent.replace('//','/')
            parent = parent.replace('http:/doc','http://doc')
           
            if not parent == expression :
                out.write("<{}> <{}> <{}> . \n".format(expression,PARENT,parent))
                
            
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




    