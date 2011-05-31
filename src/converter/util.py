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

@summary: This module defines the Profile and CiteGraph classes which are used by MetaLexConverter 
to store and retrieve mappings, and to build and write citation graphs, respectively.
'''

import re
import csv


class Profile():

    def __init__(self, profile):
        self.dictionary = {}
        try :
            dictReader = csv.reader(open(profile), delimiter= '\t')
            for row in dictReader :
                if row[0] in self.dictionary :
                    self.dictionary[row[0]].append(row[1])
                else :
                    self.dictionary[row[0]] = [row[1]]   
                    # print "Added {0} as {1}".format(row[1],row[0])
        except :
            raise Exception('Dictionary {0} does not exist, or empty line!'.format(profile))

    def lookup(self, key) :
        v = self.dictionary[key]
        if len(v) > 1 :
            # print v
            return v
        else :
            # print v[0]
            return v[0]
    
    def keys(self):
        return self.dictionary.keys()
        
    def values(self):
        return self.dictionary.values()


class CiteGraph():
    
    def __init__(self):
        # Nodes is a list of nodes
        self.nodes = []
    
        # Edges is a list of tuples of nodes (no duplicates)
        self.edges = []
        
        # Weights is a dictionary of edge weights, indexed by edge in the edges set
        self.weights = {}
                
    def beautify(self, n):
        # Try to extract a nice name for the reference, otherwise use the full URI
        
        hcontainers = "afdeling|bijlage|boek|circulaire\.divisie|citaat\-artikel|deel|divisie|hoofdstuk|model|officiele\-inhoudsopgave|paragraaf|sub\-paragraaf|titeldeel|verdragtekst|wetcitaat|wijzig\-artikel|wijzig\-divisie|wijzig\-lid\-groep|artikel"
        
                
        hcontainer_re = re.search('([BWBRV]{4}\d{7}).*('+hcontainers+')\/([\w\d\.\ \-\_]+).*',n)
        if hcontainer_re :    
            n = "{0} {1} {2}".format(hcontainer_re.group(1), hcontainer_re.group(2), hcontainer_re.group(3))
        else :
            # All other references are recorded at work level identifiers of an entire document
            bwb_re = re.search('([BWBRV]{4}\d{7})',n)
            if bwb_re :
                n = "{0}".format(bwb_re.group(1))
                    
        return n
                    
                    
                    
    def update(self, edgeURIs):
        (sourceURI, targetURI) = edgeURIs
        
        source = self.beautify(sourceURI)
        target = self.beautify(targetURI)
        
        if not(source in self.nodes) :
            self.nodes.append(source)
        if not(target in self.nodes) :
            self.nodes.append(target)
                
        edge = (source, target)       
                
        if edge in self.edges :
            self.weights[edge] += 1
        else :
            self.edges.append(edge)
            self.weights[edge] = 1
            
    def append(self, cg):
        for edge in cg.edges :
            (source, target) = edge

            if not(source in self.nodes) :
                self.nodes.append(source)
            if not(target in self.nodes) :
                self.nodes.append(target)
            
            if edge in self.edges :
                self.weights[edge] += cg.weights[edge]
            else :
                self.edges.append(edge)
                self.weights[edge] = cg.weights[edge]            
        
    def writeDOT(self) :
        maxweight = 0
        for e in self.weights:
            w = self.weights[e]
            if w > maxweight : 
                maxweight = w
            
        dot = "digraph G {\n"
        
        for n in self.nodes :
            dot += "{0} [label = '{0}']\n".format(n)
            
        for (source, target) in self.edges :
            weight = self.weights[(source,target)]
            penwidth = (float(weight)/float(maxweight))*10
            dot += "{0} -> {1} [penwidth = {2}, weight = {3}]; \n".format(source, target, penwidth, weight)  
            
        dot += "}\n"
        
        return dot    


    def writePajek(self):
        # Get the number of vertices
        pajek = "*Vertices\t{0}\n".format(len(self.nodes))
        
        for i,n in enumerate(self.nodes) :
            pajek += '{0} "{1}" 0.0 0.0 0.0 ic White bc Black\n'.format(i+1,n)
            
        pajek += "*Arcs\n"
        for (source, target) in self.edges :
            sid = self.nodes.index(source)
            tid = self.nodes.index(target)
            weight = self.weights[(source,target)]
            pajek += "{0} {1} {2} c Black\n".format(sid+1,tid+1,weight)

        return pajek

    def getNodes(self):
        return self.nodes


class ConversionReport():
    # Class for documenting the conversion and number of required 'corrections' 
    # against the source XML to ensure CML compliance
    
    def __init__(self, id):
        self.docid = id
        
        self.substitutions = {}
        self.corrections = {}
        
    def addSubstitution(self, element):
        if element in self.substitutions :
            self.substitutions[element] += 1
        else :
            self.substitutions[element] = 1
            
    def addCorrection(self, element):
        if element in self.corrections :
            self.corrections[element] += 1
        else :
            self.corrections[element] = 1
            
    def getReport(self):
        return {'docid' : self.docid, 'corrections' : self.corrections, 'substitutions' : self.substitutions}
    
    
