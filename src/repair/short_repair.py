# -*- coding: UTF-8 -*-

import xml.sax
import urllib2
import glob
import re
import sys

hcontainers = ['bijlage', 'wijzig-divisie', 'circulaire', 'afdeling', 'deel', 'definitie', 'boek', 'wijzig-artikel', 'aanhef', 'noot', 'wetcitaat', 'regeling', 'hoofdstuk', 'preambule', 'sub-paragraaf', 'titeldeel', 'wijzig-lid-groep', 'divisie', 'artikel.toelichting', 'artikel', 'citaat-artikel', 'officiele-inhoudsopgave', 'model', 'artikel.toelichtingartikel', 'paragraaf', 'verdragtekst', 'circulaire.divisie', 'enig-artikel', 'regeling-sluiting']
# shortlist = ['bijlage', 'circulaire', 'afdeling', 'deel', 'definitie', 'boek', 'wijzig-artikel', 'aanhef', 'noot', 'wetcitaat', 'regeling', 'hoofdstuk', 'preambule', 'sub-paragraaf', 'titeldeel', 'wijzig-lid-groep', 'artikel.toelichting', 'artikel', 'citaat-artikel', 'officiele-inhoudsopgave', 'model', 'artikel.toelichtingartikel', 'paragraaf', 'verdragtekst', 'enig-artikel', 'regeling-sluiting']
shortlist = ['artikel']

REALIZES = 'http://www.metalex.eu/schema/1.0#realizes'
SAMEAS = 'http://www.w3.org/2002/07/owl#sameAs'

GENERATEDBY = 'http://www.w3.org/ns/prov#wasGeneratedBy'
GENERATEDAT = 'http://www.w3.org/ns/prov#wasGeneratedAt'


shorts = {}

class ExpressionHandler(xml.sax.ContentHandler):
    
    parents = []
    def __init__(self):
        xml.sax.ContentHandler.__init__(self)
        
    def startElement(self, name, attrs):
        if name == 'meta':
            return
        
        expression = attrs.get('about',None)
        c = attrs.get('class',None)
        
        
        # print name, expression, c, self.parents
        if expression :      
                
            m = re.search('(/(?P<lang>\w\w)/)?(?P<date>\d\d\d\d-\d\d-\d\d)',expression)
            if m:
                d = m.group('date')
            else :
                d = None
                
            
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
                    

                    if expression != short and str(c) in shortlist :
                        shorts.setdefault(short,[]).append({'e': expression, 'w': work, 'shortw': shortwork})
                

                
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
        print mlfile
        try :
            xml.sax.parse(open(mlfile),ExpressionHandler())
            
            for short,v in shorts.items():
                if len(v) > 1 :
                    print "Collission detected for {}".format(short)
                    continue
                else :
                    expression = v[0]['e']
                    work = v[0]['w']
                    shortwork = v[0]['shortw']
                    
                    out.write("<{}> <{}> <{}> . \n".format(expression,SAMEAS,short))
                    out.write("<{}> <{}> <{}> . \n".format(work,SAMEAS,shortwork))
                    out.write("<{}> <{}> <{}> . \n".format(expression,REALIZES,shortwork))
        except Exception as e :
            print mlfile
            print e

    out.close()




    