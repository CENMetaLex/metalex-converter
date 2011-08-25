'''
Created on 25 Aug 2011

@author: hoekstra
'''

class RSSFeed(object):
    '''
    classdocs
    '''

    

    def __init__(self,params):
        '''
        Constructor
        '''
        self.feed = []
    
    def add(self, uri, title, date, time):
        self.feed.append({'uri': uri, 'title': title, 'date': date, 'time': time})
        
    
        
    