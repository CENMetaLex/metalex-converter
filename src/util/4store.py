'''
Created on 27 Apr 2011

@author: hoekstra
'''
import glob
import re
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
import urllib2



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
            
            print f, upload_url 
            
            register_openers()
             
            with open(f, "rb") as h:
                data = h.read() 
            
#            data = {"data" : open(f, "rb") }
             
#            datagen, headers = multipart_encode(data)
            request = urllib2.Request(upload_url, data)
            request.add_header('Content-Type','application/x-turtle')
            request.get_method = lambda: 'PUT'
            reply = urllib2.urlopen(request).read()
            
            print reply
            
            
            
            

if __name__ == '__main__':
    fs = FourStore('http://doc.metalex.eu:8000')
    
    fs.uploadFiles('http://doc.metalex.eu/id/', '../../out')
            
            
