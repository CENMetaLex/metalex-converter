# -*- coding: UTF-8 -*-

import xml.sax
import urllib2
import glob
import re
import sys

hcontainers = ['bijlage', 'wijzig-divisie', 'circulaire', 'afdeling', 'deel', 'definitie', 'boek', 'wijzig-artikel', 'aanhef', 'noot', 'wetcitaat', 'regeling', 'hoofdstuk', 'preambule', 'sub-paragraaf', 'titeldeel', 'wijzig-lid-groep', 'divisie', 'artikel.toelichting', 'artikel', 'citaat-artikel', 'officiele-inhoudsopgave', 'model', 'artikel.toelichtingartikel', 'paragraaf', 'verdragtekst', 'circulaire.divisie', 'enig-artikel', 'regeling-sluiting']
# shortlist = ['bijlage', 'circulaire', 'afdeling', 'deel', 'definitie', 'boek', 'wijzig-artikel', 'aanhef', 'noot', 'wetcitaat', 'regeling', 'hoofdstuk', 'preambule', 'sub-paragraaf', 'titeldeel', 'wijzig-lid-groep', 'artikel.toelichting', 'artikel', 'citaat-artikel', 'officiele-inhoudsopgave', 'model', 'artikel.toelichtingartikel', 'paragraaf', 'verdragtekst', 'enig-artikel', 'regeling-sluiting']


PARENT = 'http://www.metalex.eu/schema/1.0#parent'


class ExpressionHandler(xml.sax.ContentHandler):
    
    parents = []
    parent_types = []
    def __init__(self):
        xml.sax.ContentHandler.__init__(self)
        
    def startElement(self, name, attrs):
        # print self.parents
        #print attrs
        # print self.attributes
        if name == 'meta':
            return
        
        expression = attrs.get('about',None)
        c = attrs.get('class',None)
        
        
        # print name, expression, c, self.parents
        if expression :      
            if self.parents != [] :
                out.write("<{}> <{}> <{}> . \n".format(expression,PARENT,self.parents[-1]))
                
            if str(c) in hcontainers or name == 'root':
                self.parents.append(expression)
            elif self.parents != [] :
                self.parents.append(self.parents[-1])
                
        else :
            self.parents.append(self.parents[-1])
            


        
        
                
    def endElement(self, name):
        if self.parents != [] :
            del self.parents[-1]
        if self.parent_types != []:
            del self.parent_types[-1]
       
                



if __name__ == '__main__':
    print "Usage: python parent_repair.py '[MetaLexFilesMask]' [OutFile.nt]"
    
    if len(sys.argv) > 3 :
        print "You gave me {}\nBut probably meant something different"
        quit()

    path = sys.argv[1]
    outpath = sys.argv[2]
    out = open(outpath,'w')
    for mlfile in glob.glob(path):
        print mlfile
        try :
            xml.sax.parse(open(mlfile),ExpressionHandler())
        except Exception as e :
            print mlfile
            print e

    out.close()




    