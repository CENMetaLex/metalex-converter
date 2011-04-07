import sys, string
import codecs
from xml.sax import saxutils
import xml.parsers.expat
import pickle

# --- The ContentHandler

class BWBListGenerator():

    current = ""
    prev = ""
    changed = False
    prevcontent = ""
    
    bwblist = {}
    
    current_id = ''
    
    def __init__(self, out = sys.stdout):
        self._out = out

    # ContentHandler methods
        
    def startDocument(self):
        self._out.write(u'<?xml version="1.0" encoding="utf-8"?>\n')

    def startElement(self, name, attrs):
        if name == "__NS1:BWBId" :
            self.current = 'id'
        elif name == "__NS1:RegelingSoort" :
            self.current = 'soort'
        elif name == "__NS1:OfficieleTitel" :
            self.current = 'titel'
        elif name == "__NS1:DatumLaatsteWijziging" :
            self.current = 'laatste'
        elif name == "__NS1:VervalDatum" :
            self.current = 'verval'
        elif name == "__NS1:InwerkingtredingsDatum" and self.prev == "status":
            self.current = 'ciwtr'
        elif name == "__NS1:InwerkingtredingsDatum":
            self.current = 'iwtr'
        elif name == "__NS1:titel" :
            self.current = "ctitel"
        elif name == "__NS1:status" :
            self.current = "status"
        elif name == "__NS1:NietOfficieleTitel":
            self.current = "notitel"
        elif name == "__NS1:AfkortingLijst" :
            self.current = "afkortinglijst"
        elif name == "__NS1:Afkorting" :
            self.current = "afkorting"
        else :
            self.current = None
        
        self.changed = False
            

    def endElement(self, name):
        self.prev = self.current
        self.current = None

    def characters(self, content):
        # self._out.write("\nPrevious: " + self.prevcontent)
        
        pre = ""
        
        c = saxutils.escape(content).encode('utf-8')
        # c = content.encode('utf-8')
        
        if self.current == "id" :
            pre = "\n\nid:\t"
            self.current_id = c
        elif self.current == "soort" :
            pre = "\nsoort:\t"
        elif self.current == "titel" :
            self.bwblist[self.current_id] = c
            pre = "\ntitel:\t"
        elif self.current == "notitel" :
            pre = "\nnotitel:\t"
        # elif self.current == "ctitel" :
        #     # Keep the contents of this element for when we know its status
        #     self.prevcontent = content
        elif self.current == "status" :
            if c == "officieel" :
                pre = "\noctitel:\t"
            elif c == "redactioneel" :
                pre = "\nrctitel:\t"
            c = self.prevcontent 
        elif self.current == "laatste" :
            pre = "\nlaatst:\t"
        elif self.current == "verval" :
            pre = "\nverval:\t"
        elif self.current == "ciwtr" :
            pre = "\nciwtr:\t"
        elif self.current == "iwtr" :
            pre = "\niwtr:\t"
            
        if pre != "" :
            self._out.write(pre + c)
        
        if self.current :
            self.prevcontent = c
        
    def ignorableWhitespace(self, content):
        # self._out.write(content)
        pass
        
    def processingInstruction(self, target, data):
        self._out.write(u'<?%s %s?>' % (target, data))



blg = BWBListGenerator()

p = xml.parsers.expat.ParserCreate()
p.buffer_text = True

p.StartElementHandler = blg.startElement
p.EndElementHandler = blg.endElement
p.CharacterDataHandler = blg.characters

try:
    infile = file(sys.argv[1])
    p.ParseFile(infile)

    outfile = open(sys.argv[2], 'w')
    pickle.dump(blg.bwblist,outfile)
except :
    print "Missing or incorrect command line arguments.\nUsage: python getbwbids.py <BWBIdList> <OutfilePickle>"
