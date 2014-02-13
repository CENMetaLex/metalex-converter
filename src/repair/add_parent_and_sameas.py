# -*- coding: UTF-8 -*-

import xml.sax
import urllib2
import glob
import re
import sys

hcontainers = ['bijlage', 'wijzig-divisie', 'circulaire', 'afdeling', 'deel', 'definitie', 'boek', 'wijzig-artikel', 'aanhef', 'noot', 'wetcitaat', 'regeling', 'hoofdstuk', 'preambule', 'sub-paragraaf', 'titeldeel', 'wijzig-lid-groep', 'divisie', 'artikel.toelichting', 'artikel', 'citaat-artikel', 'officiele-inhoudsopgave', 'model', 'artikel.toelichtingartikel', 'paragraaf', 'verdragtekst', 'circulaire.divisie', 'enig-artikel', 'regeling-sluiting']
# shortlist = ['bijlage', 'circulaire', 'afdeling', 'deel', 'definitie', 'boek', 'wijzig-artikel', 'aanhef', 'noot', 'wetcitaat', 'regeling', 'hoofdstuk', 'preambule', 'sub-paragraaf', 'titeldeel', 'wijzig-lid-groep', 'artikel.toelichting', 'artikel', 'citaat-artikel', 'officiele-inhoudsopgave', 'model', 'artikel.toelichtingartikel', 'paragraaf', 'verdragtekst', 'enig-artikel', 'regeling-sluiting']
shortlist = ['artikel']
antishortlist = ['bijlage']

PARENT = 'http://www.metalex.eu/schema/1.0#parent'
REALIZES = 'http://www.metalex.eu/schema/1.0#realizes'
SAMEAS = 'http://www.w3.org/2002/07/owl#sameAs'

GENERATEDBY = 'http://www.w3.org/ns/prov#wasGeneratedBy'
GENERATEDAT = 'http://www.w3.org/ns/prov#wasGeneratedAt'


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
                
            m = re.search('(/(?P<lang>\w\w)/)?(?P<date>\d\d\d\d-\d\d-\d\d)',expression)
            if m:
                d = m.group('date')
                
            
            if str(c) in hcontainers or name == 'root':
                self.parents.append(expression)
                
                
                m = re.search('(?P<bwb>.*/BWB.*?/)(?P<path>.*/)?(?P<hcontainer>{}/.*?)(?P<version>/.*)'.format(c),expression)
                
                if not m:
                    pass
                else :
                    short = "{}{}{}".format(m.group('bwb'),m.group('hcontainer'),m.group('version'))
                    shortwork = "{}{}".format(m.group('bwb'),m.group('hcontainer'))
                    work = "{}{}{}".format(m.group('bwb'),m.groupdict('')['path'],m.group('hcontainer')).replace('//','/').replace(':/','://')
                    activity = "{}{}".format(m.group('bwb').replace('/id/','/id/process/'),m.group('version')).replace('//','/').replace(':/','://')
                    
                    
                    
                    out.write("<{}> <{}> <{}> . \n".format(expression,GENERATEDBY,activity))
                    
                    if d:
                        out.write("<{}> <{}> \"{}\"^^<http://www.w3.org/2001/XMLSchema#date> . \n".format(expression,GENERATEDAT,d))
                    
                    if self.parent_types != []:
                        if expression != short and str(c) in shortlist and not self.parent_types[-1] in antishortlist :
                            print str(c), self.parent_types[-1], expression
                            out.write("<{}> <{}> <{}> . \n".format(expression,SAMEAS,short))
                        if work != shortwork and str(c) in shortlist and not self.parent_types[-1] in antishortlist:
                            print str(c), self.parent_types[-1], expression
                            out.write("<{}> <{}> <{}> . \n".format(work,SAMEAS,shortwork))
                            out.write("<{}> <{}> <{}> . \n".format(expression,REALIZES,shortwork))
                
                self.parent_types.append(str(c))
                
            elif self.parents != [] :
                self.parents.append(self.parents[-1])
                self.parent_types.append(self.parent_types[-1])
                
        else :
            self.parents.append(self.parents[-1])
            self.parent_types.append(self.parent_types[-1])
            


        
        
                
    def endElement(self, name):
        if self.parents != [] :
            del self.parents[-1]
        if self.parent_types != []:
            del self.parent_types[-1]
       
                



if __name__ == '__main__':
    print "Usage: python add_parent_and_sameas.py '[MetaLexFilesMask]' [OutFile.nt]"
    
    print sys.argv
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




    