import xml.sax
import urllib2
import glob
import re
import sys

ASSOCIATED = "http://www.w3.org/ns/prov#wasAssociatedWith"
ATTRIBUTED = "http://www.w3.org/ns/prov#wasAttributedTo"
ACTIVITY = "http://www.w3.org/ns/prov#Activity"
ENTITY = "http://www.w3.org/ns/prov#Entity"
AGENT = "http://www.w3.org/ns/prov#Agent"
GENERATED = "http://www.w3.org/ns/prov#wasGeneratedBy"
ENDED = "http://www.w3.org/ns/prov#endedAtTime"
GENERATEDTIME = "http://www.w3.org/ns/prov#wasGeneratedAtTime"
NAME = "http://xmlns.com/foaf/0.1/name"
TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"

class FunctieHandler(xml.sax.ContentHandler):
    
    functie = False
    
    def __init__(self):
        xml.sax.ContentHandler.__init__(self)
        
    def startElement(self, name, attrs):
        if name == 'root':
            if 'about' in attrs:
                self.expression_uri = attrs.getValue("about")
                self.process_uri = self.expression_uri.replace('/id/','/id/process/')
            
                m = re.search('(?P<date>\d\d\d\d-\d\d-\d\d)',self.process_uri)
                self.date = m.group('date')
        
        if "class" in attrs and attrs.getValue("class") == 'functie':
            self.functie = True
            
    def endElement(self, name):
        self.functie = False
        
    def characters(self, content):
        if self.functie == True:
            agent_title = content.strip(' ,.:;')
            agent_uri = 'http://doc.metalex.eu/id/agent/' + urllib2.quote(agent_title.replace(' ','_'))
            
            self.write(self.process_uri,TYPE,ACTIVITY)
            self.write(self.expression_uri,TYPE,ENTITY)
            
            self.writed(self.process_uri,ENDED,self.date)
            self.write(self.expression_uri,GENERATED,self.process_uri)
            self.writed(self.expression_uri,GENERATEDTIME,self.date)
            self.write(self.process_uri,ASSOCIATED,agent_uri)
            self.write(self.expression_uri,ATTRIBUTED,agent_uri)
            self.writes(agent_uri,NAME,agent_title)
            self.write(agent_uri,TYPE,AGENT)
            
            

        
    def write(self,s,p,o):
        out.write("<{}> <{}> <{}> .\n".format(s,p,o))
        
    def writes(self,s,p,string):
        out.write("<{}> <{}> \"{}\"^^http://www.w3.org/2001/XMLSchema#string .\n".format(s,p,string))
        
    def writed(self,s,p,date):
        out.write("<{}> <{}> \"{}\"^^http://www.w3.org/2001/XMLSchema#date .\n".format(s,p,date))
        


if __name__ == '__main__':
    print "Usage: opmv2prov [MetaLexFilesMask] [OutFile.nt]"
    path = sys.argv(0)
    outpath = sys.argv(1)
    out = open(outpath,'w')
    for mlfile in glob.glob(path):
        print mlfile
        xml.sax.parse(open(mlfile),FunctieHandler())

    out.close()