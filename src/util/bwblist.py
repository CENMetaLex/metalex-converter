# -*- coding: utf-8 -*-
'''
MetaLex Converter
=================

@author: Rinke Hoekstra
@contact: hoekstra@uva.nl
@organization: Universiteit van Amsterdam
@version: 0.1
@status: beta
@website: http://doc.metalex.eu
@copyright: 2011, Rinke Hoekstra, Universiteit van Amsterdam

@license: MetaLex Converter is free software, you can redistribute it and/or modify
it under the terms of GNU Affero General Public License
as published by the Free Software Foundation, either version 3
of the License, or (at your option) any later version.

You should have received a copy of the the GNU Affero
General Public License, along with MetaLex Converter. If not, see


Additional permission under the GNU Affero GPL version 3 section 7:

If you modify this Program, or any covered work, by linking or
combining it with other code, such other code is not for that reason
alone subject to any of the requirements of the GNU Affero GPL
version 3.

@summary: This module contains a script for converting the XML representation of the list of all BWB identifiers to a 
Python dictionary, and storing it to a pickle file for use by the convert_bwb.py script

'''

import sys
from xml.sax import saxutils
import xml.parsers.expat
import pickle
import urllib2
import zipfile
import StringIO
from datetime import date
import logging

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
        pass

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


class DebugWriter():
    
    def write(self, text):
        logging.debug(text)

class BWBList():
    
    def __init__(self):
        dw = DebugWriter()
        self.blg = BWBListGenerator(dw)
        
        p = xml.parsers.expat.ParserCreate()
        p.buffer_text = True
        
        p.StartElementHandler = self.blg.startElement
        p.EndElementHandler = self.blg.endElement
        p.CharacterDataHandler = self.blg.characters
        
        
        bwbidlist_filename = 'BWBIdList.xml'
        bwbidlist_url = 'http://wetten.overheid.nl/BWBIdService/BWBIdList.xml.zip'
        pickle_filename = 'pickles/bwbid_list_{0}.pickle'.format(date.today())
        
        logging.info("Loading zipped BWB ID list from {0}.".format(bwbidlist_url))
        response = urllib2.urlopen(bwbidlist_url)
        bwbidlist_zipped_string = response.read()
        bwbidlist_zipped_file = StringIO.StringIO(bwbidlist_zipped_string)
        bwbidlist_zip = zipfile.ZipFile(bwbidlist_zipped_file)
        logging.info("Unzipping BWB ID list to {0}.".format(bwbidlist_filename))
        bwbidlist_zip.extract(bwbidlist_filename)
        
        logging.info("Loading and parsing BWB ID list from {0}.".format(bwbidlist_filename))
        infile = file(bwbidlist_filename)
        p.ParseFile(infile)
        
        logging.info("Dumping BWB ID list dictionary to {0}.".format(pickle_filename))
        outfile = open(pickle_filename, 'w')
        pickle.dump(self.blg.bwblist,outfile)
        
    def getBWBIds(self):
        return self.blg.bwblist

