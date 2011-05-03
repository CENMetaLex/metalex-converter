'''
Created on 27 Apr 2011

@author: hoekstra
'''
import glob
import re
from poster.streaminghttp import register_openers
from SPARQLWrapper import SPARQLWrapper, JSON
import urllib2
import subprocess



class FourStore():
    
    def __init__(self, url):
        self.url = url
        
    def uploadFiles(self, uriprefix, path):
        mask = path + '/*.n3'
        for f in glob.iglob(mask) :
            chunks = re.split('/|_|\.', f)
            graph_uri = uriprefix + chunks[-3] + '/' + chunks[-2]
            print graph_uri
            
            upload_url = self.url + "/data/" + graph_uri
            
            if not self.check_available(graph_uri) :
                print f, upload_url 
                
                register_openers()
                 
                with open(f, "rb") as h:
                    data = h.read() 
    
                request = urllib2.Request(upload_url, data)
                request.add_header('Content-Type','application/x-turtle')
                request.get_method = lambda: 'PUT'
                reply = urllib2.urlopen(request).read()
                
                print reply
            else :
                print "Graph already loaded: {0}".format(graph_uri)
            
    def check_available(self,graph_uri):
        q = "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\nPREFIX metalex: <http://www.metalex.eu/schema/1.0#>\nASK { <"+graph_uri+"> rdf:type ?x .}"
        
        sparql = SPARQLWrapper("http://doc.metalex.eu:8000/sparql/")
        sparql.setQuery(q)
        
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
    
        return results['boolean']            
            
    def loadFiles(self, uriprefix, path):
        mask = path + '/*.n3'
        for f in glob.iglob(mask) :
            chunks = re.split('/|_|\.', f)
            graph_uri = uriprefix + chunks[-3] + '/' + chunks[-2]
            print f, graph_uri        
        
            command = ['4s-import','metalex','--model',graph_uri,f]
            
            returncode = subprocess.call(command)
            print "Return code: ", returncode
            


if __name__ == '__main__':
    fs = FourStore('http://doc.metalex.eu:8000')
    
    fs.loadFiles('http://doc.metalex.eu/id/', '../../out')
            
            
