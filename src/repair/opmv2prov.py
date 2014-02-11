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
ORGANIZATION = "http://www.w3.org/ns/prov#Organization"
GENERATED = "http://www.w3.org/ns/prov#wasGeneratedBy"
ENDED = "http://www.w3.org/ns/prov#endedAtTime"
GENERATEDTIME = "http://www.w3.org/ns/prov#wasGeneratedAtTime"
ACTEDONBEHALF = "http://www.w3.org/ns/prov#actedOnBehalfOf"
NAME = "http://xmlns.com/foaf/0.1/name"
LABEL = "http://www.w3.org/2000/01/rdf-schema#label"
TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"



class FunctieHandler(xml.sax.ContentHandler):
    
    functie = False
    organisatie = False
    
    def __init__(self):
        xml.sax.ContentHandler.__init__(self)
        
    def startElement(self, name, attrs):
        self.expression_uri = attrs.get('about',None)
        c = attrs.get('class',None)
        
        ### Create the process once we find the root element
        if name == 'root' and self.expression_uri:
                self.process_uri = self.expression_uri.replace('/id/','/id/process/')
                
                self.write(self.process_uri,TYPE,ACTIVITY)
                
                m = re.search('(?P<date>\d\d\d\d-\d\d-\d\d)',self.process_uri)
                if m:
                    self.date = m.group('date')
                    self.writed(self.process_uri,ENDED,self.date)
                else :
                    self.date = None
            
        # For any other expression, we state that the process we just made generated the entity
        if self.expression_uri:
            self.write(self.expression_uri,TYPE,ENTITY)
            
            self.write(self.expression_uri,GENERATED,self.process_uri)
            
            if self.date :
                self.writed(self.expression_uri,GENERATEDTIME,self.date)
        
        # If the class of the element is functie or organisatie, we set the flag for handling its content
        if c == 'functie':
            self.functie = True
            
        if c == 'organisatie':
            self.organisatie = True
            
    def endElement(self, name):
        self.functie = False
        self.organisatie = False
        self.agent_uri = None
        
    def characters(self, content):
        # Functie is usually the name of a minister or state-secretary
        if self.functie == True:
            agent_title = content.replace('\n',' ').replace('\t',' ').strip(' ,.:;').encode('utf-8')
            if agent_title != '':
                 agent_uri = 'http://doc.metalex.eu/id/agent/' + urllib2.quote(agent_title.replace(' ','_'))
                 self.agent_uri = agent_uri
                 
                 
                 
            
                 
                 
                 self.write(self.process_uri,ASSOCIATED,agent_uri)
                 self.write(self.expression_uri,ATTRIBUTED,agent_uri)
                 self.writes(agent_uri,NAME,agent_title)
                 self.writes(agent_uri,LABEL,agent_title)
                 self.write(agent_uri,TYPE,AGENT)
        
        # Sometimes this information is split in a name and an organisation.
        if self.organisatie == True:
            org_title = content.replace('\n',' ').replace('\t',' ').strip(' ,.:;').encode('utf-8')
            if org_title != '':
                org_uri = 'http://doc.metalex.eu/id/agent/' + urllib2.quote(org_title.replace(' ','_'))
                
                self.write(self.process_uri,ASSOCIATED,org_uri)
                self.write(self.expression_uri,ATTRIBUTED,org_uri)
                self.writes(org_uri,NAME,org_title)
                self.write(org_uri,TYPE,ORGANIZATION)
                
                if self.agent_uri :
                    self.write(org_uri,ACTEDONBEHALF,self.agent_uri)
            

        
    def write(self,s,p,o):
        out.write("<{}> <{}> <{}> .\n".format(s,p,o))
        
    def writes(self,s,p,string):
        out.write("<{}> <{}> \"{}\"^^<http://www.w3.org/2001/XMLSchema#string> .\n".format(s,p,string))
        
    def writed(self,s,p,date):
        out.write("<{}> <{}> \"{}\"^^<http://www.w3.org/2001/XMLSchema#date> .\n".format(s,p,date))
        


if __name__ == '__main__':
    print "Usage: opmv2prov [MetaLexFilesMask] [OutFile.nt]"
    
    print sys.argv
    path = sys.argv[1]
    outpath = sys.argv[2]
    out = open(outpath,'w')
    for mlfile in glob.glob(path):
        try :
            xml.sax.parse(open(mlfile),FunctieHandler())
        except Exception as e :
            print mlfile
            print e

    out.close()