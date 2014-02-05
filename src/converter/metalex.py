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

@summary: This module defines the MetaLexConverter class which is a generic conversion script 
for legal XML to CEN MetaLex XML, accompanying RDF and Pajek Networks
'''



import xml.dom.minidom
import re
import hashlib
import uuid
from rdflib import ConjunctiveGraph, Namespace, Literal, URIRef, RDF, XSD
from util import CiteGraph, ConversionReport
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
import urllib2
import urllib
import base64
import logging
import os
import subprocess





class MetaLexConverter():

    # Base URI for newly created elements
    top_uri = "http://doc.metalex.eu/id/"
    doc_uri = "http://doc.metalex.eu/doc/"

    # MetaLex namespaces
    MO = Namespace('http://www.metalex.eu/schema/1.0#')
    MS = Namespace('http://www.metalex.eu/schema/1.0#')    

    # Standard namespaces
    RDFS = Namespace('http://www.w3.org/2000/01/rdf-schema#')
    XML = Namespace('http://www.w3.org/XML/1998/namespace')
    OWL = Namespace('http://www.w3.org/2002/07/owl#')
    XHTML = Namespace('http://www.w3.org/1999/xhtml#')
    OPMV = Namespace('http://purl.org/net/opmv/ns#')
    TIME = Namespace('http://www.w3.org/2006/time#')
    DCTERMS = Namespace('http://purl.org/dc/terms/')
    FOAF = Namespace('http://xmlns.com/foaf/0.1/')
    SEM = Namespace('http://semanticweb.cs.vu.nl/2009/11/sem/')

   
    # Standard elements
    root = "root"
    id = "id"
    hc = "hcontainer"
    hct = "hcontainer_text"
    c = "container"
    ce = "container_ext"
    b = "block"
    i = "inline"
    ht = "htitle"
    r = "root"
    mc = "mcontainer"
    ms = "milestone"
    m = "meta"
    ci = "cite"

    # Class attribute for CSS rendering  
    cl = 'class'
    
    # Type attribute, for linking to base ontology
    t = str(RDF.type)

    schemaLocation = "xsi:schemaLocation"
    xmlns = "xmlns"
    xmlns_xsi = "xmlns:xsi"
    xmlns_xml = "xmlns:xml"
    
    # Standard RDFa attributes
    r = "rel"
    h = "href"
    p = "property"
    l = 'xml:lang'
    s = "src"
    ct = "content"
    a = "about"
    dt = "datatype"
    # Standard MetaLex attributes
    n = "name"
    
    label = str(RDFS.label)
    
    # Standard semantic relations
    realizes = MO["realizes"]
    parent = MO["partOf"]
    previous = MO["previous"]
    next = MO["next"]
    cites = MO["cites"]
    result = MO["result"]
    
    sameAs = OWL["sameAs"]
    

    def __init__(self, id, doc, source_doc_uri, version, modification_type, abbreviation, title, profile, flags):
        self.flags = flags
        self.bwbid = id
        
        # Set conversion flags
        self.inline_metadata = flags['inline_metadata']
        self.produce_rdf = flags['produce_rdf']
        self.produce_graph = flags['produce_graph']
        self.profile = profile
        
        
        
        # Create the source document
        self.source_doc = doc
        self.source_doc_uri = source_doc_uri
        # Create the target document
        self.target_doc = xml.dom.minidom.getDOMImplementation().createDocument(self.MS, self.root, None)

        # Make sure we create a new RDF graph for every document
        self.graph = ConjunctiveGraph()
        
        # Get the ontology base for the source elements
        self.o = self.profile.lookup('ontology_base')        
        self.WO = Namespace(self.o)

        # Set instance-variables for version, modification type and report        
        self.v = version
        if modification_type :
            self.modification_type = self.WO[modification_type]
        else :
            self.modification_type = None
        self.abbreviation = abbreviation
        self.title = title
        self.report = ConversionReport(id)
        
        # Bind namespaces to graph
        self.graph.namespace_manager.bind('mo',self.MO)
        self.graph.namespace_manager.bind('xhtml',self.XHTML)
        self.graph.namespace_manager.bind('wo',self.WO)
        self.graph.namespace_manager.bind('owl',self.OWL)
        self.graph.namespace_manager.bind('xml',self.XML)
        self.graph.namespace_manager.bind('rdfs',self.RDFS)
        self.graph.namespace_manager.bind('opmv',self.OPMV)
        self.graph.namespace_manager.bind('time',self.TIME)
        self.graph.namespace_manager.bind('dcterms',self.DCTERMS)
        self.graph.namespace_manager.bind('foaf',self.FOAF)
        self.graph.namespace_manager.bind('sem',self.SEM)

        # Create a new citation graph...
        self.cg = CiteGraph()

        self.source_root_uri = ""
        self.creation_event_uri = ""
        

        


    # ----------
    # Basic Functions
    # ----------
    def handleRoot(self):
        # Get the root element for the source and target DOM tree
        
        target_root = self.target_doc.documentElement
        
        self.source_root_uri = self.bwbid
        logging.debug("Starting {0} ...".format(self.source_root_uri))
        
        # Determine URIs for the root node
        work_uri = self.top_uri + self.source_root_uri         
        self.root_work_uri = work_uri
        
        # Check whether the document is empty or not
        if len(self.source_doc.getElementsByTagName(self.profile.lookup('error')))>0 :
            logging.warning("Document is empty: Assuming {0} was repealed on latest version date ({1}).".format(self.bwbid, self.v))
            # Repealed regulations don't have a language
            expression_uri = self.getExpressionURI(work_uri,'')
            self.rdf_graph_uri = expression_uri 
            self.createLegislativeModificationEvent(target_root, expression_uri)
            self.setNamespaces(target_root)
            
            if self.title :
                additional_attrs = {self.DCTERMS['title'] : self.title }
            else :
                additional_attrs = {}
            
            if self.abbreviation :
                additional_attrs[self.DCTERMS['alternative']] = self.abbreviation 
                
            self.handleMetadata(target_root, None, expression_uri, work_uri, {}, additional_attrs)
            return self.report.getReport()
        
        source_root = self.source_doc.getElementsByTagName(self.profile.lookup(self.root))[0]
        lang_tag = self.setLanguageTag(source_root, target_root, "")
        expression_uri = self.getExpressionURI(work_uri, lang_tag)
        self.rdf_graph_uri = expression_uri   
        
        if self.source_root_uri != source_root.getAttribute(self.profile.lookup('root_id')) :
            self.rdf_graph_uri = "http://foo.bar/error"
            logging.error("BWBID {0} and identifier of root element do not match! (which is highly unlikely)".format(self.source_root_uri))
            return self.report.getReport()


        # Create attributes for the root node        
        self.createLegislativeModificationEvent(target_root, expression_uri)
        
        self.createIdentifyingAttributes(source_root, target_root, expression_uri)
                
        self.setNamespaces(target_root)
        
        # Some 'additional' metadata: source_doc_uri, title and alternative title (abbreviation)
        
        additional_attrs = {self.DCTERMS['source'] : self.source_doc_uri}
        
        if self.title :
            additional_attrs[self.DCTERMS['title']] = self.title 
        
        if self.abbreviation :
            additional_attrs[self.DCTERMS['alternative']] = self.abbreviation 
            
        self.handleMetadata(target_root, None, expression_uri, work_uri, source_root.attributes, additional_attrs)
        
        # Report the substitution
        self.report.addSubstitution(self.root)

        for element in source_root.childNodes :
            self.handle(element,target_root,work_uri,work_uri,expression_uri,target_root, lang_tag)
        
        logging.debug("({0} done)".format(self.source_root_uri))
        
        return self.report.getReport()




    def handle(self, source_node, target_parent_node, base_work_uri, target_parent_work_uri, target_parent_expression_uri, metadata_parent, lang_tag, index = 1):
        # =====
        # TODO: 
        # 1) Check correct reference to parent source_node from elements that may have been moved to ensure conformance to CML
        # ===== 
        

        if source_node.nodeType == source_node.ELEMENT_NODE :
            # ==========
            # Deal with HContainers
            # ==========
            if source_node.tagName in self.profile.lookup(self.hc) :
                target_node = self.target_doc.createElement(self.hc)
                
                work_uri, short_work_uri = self.getHContainerWorkURI(source_node, base_work_uri, index)

                lang_tag = self.setLanguageTag(source_node, target_node, lang_tag)
                expression_uri = self.getExpressionURI(work_uri, lang_tag)
                short_expression_uri = self.getExpressionURI(short_work_uri, lang_tag)
                
                self.createIdentifyingAttributes(source_node, target_node, expression_uri)
                
                # caption = self.getText([source_node.getElementsByTagName("kop")[0]])
                
                ontology_type = self.o + source_node.tagName
                
                if short_expression_uri != expression_uri :
                    additional_attrs = {self.t : ontology_type, self.sameAs: short_expression_uri }
                else :
                    additional_attrs = {self.t : ontology_type }

                self.handleMetadata(target_node, target_parent_expression_uri, expression_uri, work_uri, source_node.attributes, additional_attrs)
                
                target_parent_node.appendChild(target_node)
                self.report.addSubstitution(self.hc)
                
                index_counter = 0
                for element in source_node.childNodes :
                    if element.nodeType != element.TEXT_NODE:
                        index_counter += 1
                    self.handle(element,target_node,work_uri, work_uri, expression_uri,target_node,lang_tag,index_counter)

            # ==========
            # Deal with Text-HContainers (such as articles)
            # ==========
            elif source_node.tagName in self.profile.lookup(self.hct) :
                target_node = self.target_doc.createElement(self.hc)

                # hoofdstuk/kop/nr
                work_uri, short_work_uri = self.getHContainerWorkURI(source_node, base_work_uri, index)
                
                lang_tag = self.setLanguageTag(source_node, target_node, lang_tag)
                expression_uri = self.getExpressionURI(work_uri, lang_tag)
                short_expression_uri = self.getExpressionURI(short_work_uri, lang_tag)
                
                self.createIdentifyingAttributes(source_node, target_node, expression_uri)

                # caption = self.getText([source_node.getElementsByTagName("kop")[0]])
                
                ontology_type = self.o + source_node.tagName
                
                if short_expression_uri != expression_uri :
                    additional_attrs = {self.t : ontology_type, self.sameAs: short_expression_uri }
                else :
                    additional_attrs = {self.t : ontology_type }
                
                self.handleMetadata(target_node, target_parent_expression_uri, expression_uri, work_uri, source_node.attributes, additional_attrs)

                # Deal with the htitle (kop)
                self.handle(source_node.getElementsByTagName("kop")[0],target_node,work_uri,work_uri, expression_uri,target_node, lang_tag)
                
                container_node = self.target_doc.createElement(self.c)
                container_node.setAttributeNode(self.createItemIdentifier(container_node))
                container_node.setAttributeNode(self.createNameAttribute(container_node))
                container_node.setAttributeNode(self.createClassAttribute(container_node))

                self.report.addSubstitution(self.hc)
                self.report.addCorrection(source_node.tagName)
                
                index_counter =0
                for element in source_node.childNodes :
                    if element.nodeName != "kop" :
                        if element.nodeType != element.TEXT_NODE:
                            index_counter += 1
                        self.handle(element,container_node,work_uri,work_uri, expression_uri,container_node,lang_tag, index_counter)
                
                target_node.appendChild(container_node)
                target_parent_node.appendChild(target_node)

            # ==========
            # Deal with Containers
            # ==========
            elif source_node.tagName in self.profile.lookup(self.c) :
                target_node = self.target_doc.createElement(self.c)
                
                work_uri, expression_uri, lang_tag = self.createSHA1Element(source_node, target_node, base_work_uri, target_parent_work_uri, target_parent_expression_uri, target_node, lang_tag, index)
                
                target_parent_node.appendChild(target_node)
                self.report.addSubstitution(self.c)
                
                index_counter = 0
                for element in source_node.childNodes :
                    if element.nodeType != element.TEXT_NODE:
                        index_counter += 1
                    self.handle(element,target_node, base_work_uri, work_uri, expression_uri, target_node, lang_tag, index_counter)

            # ==========
            # Deal with Blocks
            # ==========
            elif source_node.tagName in self.profile.lookup(self.b) :
                target_node = self.target_doc.createElement(self.b)

                work_uri, expression_uri, lang_tag = self.createSHA1Element(source_node, target_node, base_work_uri, target_parent_work_uri, target_parent_expression_uri, metadata_parent, lang_tag, index)

                target_parent_node.appendChild(target_node)
                self.report.addSubstitution(self.b)

                index_counter = 0
                for element in source_node.childNodes :
                    if element.nodeType != element.TEXT_NODE:
                        index_counter += 1
                    self.handle(element,target_node,base_work_uri, work_uri, expression_uri, metadata_parent, lang_tag, index_counter)


            # ==========
            # Deal with Special Containers (need to be put underneath parent container... the metadata_parent)
            # ==========
            elif source_node.tagName in self.profile.lookup(self.ce) :
                target_node = self.target_doc.createElement(self.c)

                work_uri, expression_uri, lang_tag = self.createSHA1Element(source_node, target_node, base_work_uri, target_parent_work_uri, target_parent_expression_uri, metadata_parent, lang_tag, index)

                metadata_parent.appendChild(target_node)
                self.report.addSubstitution(self.c)
                self.report.addCorrection(source_node.tagName)

                index_counter = 0
                for element in source_node.childNodes :
                    if element.nodeType != element.TEXT_NODE:
                        index_counter += 1
                    self.handle(element,target_node,base_work_uri, work_uri, expression_uri, metadata_parent, lang_tag, index_counter)
                    
            # ==========
            # Deal with hTitles
            # ==========
            elif source_node.tagName in self.profile.lookup(self.ht) :
                target_node = self.target_doc.createElement(self.ht)

                work_uri, expression_uri, lang_tag = self.createSHA1Element(source_node, target_node, base_work_uri, target_parent_work_uri, target_parent_expression_uri, metadata_parent, lang_tag, index)

                target_parent_node.appendChild(target_node)

                self.report.addSubstitution(self.ht)
                
                index_counter = 0
                for element in source_node.childNodes :
                    if element.nodeType != element.TEXT_NODE:
                        index_counter += 1
                    self.handle(element,target_node,base_work_uri, work_uri, expression_uri, metadata_parent, lang_tag, index_counter)
                    
            # ==========
            # Deal with an Inline element 
            # Ensure that the element occurs inside a block, 
            # as it often doesn't according to the mapping to the source XML
            # ==========                    
            elif source_node.tagName in self.profile.lookup(self.i) :
                target_node = self.target_doc.createElement(self.i)

                # Add the metadata for inline elements to the container parent.
                work_uri, expression_uri, lang_tag = self.createSHA1Element(source_node, target_node, base_work_uri, target_parent_work_uri, target_parent_expression_uri, metadata_parent, lang_tag, index)

                
                if target_parent_node.tagName != self.b and target_parent_node.tagName != self.ht and target_parent_node.tagName != self.i:
                    block_node = self.createBlock(target_node)
                    target_parent_node.appendChild(block_node)
                    
                    self.report.addSubstitution(self.i)
                    self.report.addCorrection(source_node.tagName)
                else :
                    self.report.addSubstitution(self.i)
                    target_parent_node.appendChild(target_node)

                index_counter = 0
                for element in source_node.childNodes :
                    if element.nodeType != element.TEXT_NODE:
                        index_counter += 1
                    self.handle(element,target_node,base_work_uri, work_uri, expression_uri, metadata_parent, lang_tag, index_counter)                
                          


            # ==========
            # Deal with Milestone
            # Ensure that the element occurs inside a block, 
            # as it often doesn't according to the mapping to the source XML
            # ==========
            elif source_node.tagName in self.profile.lookup(self.ms) :
                target_node = self.target_doc.createElement(self.ms)

                # Add the metadate for inline elements to the container parent.
                work_uri, expression_uri, lang_tag = self.createSHA1Element(source_node, target_node, base_work_uri, target_parent_work_uri, target_parent_expression_uri, metadata_parent, lang_tag, index)

                if target_parent_node.tagName != self.b and target_parent_node.tagName != self.ht and target_parent_node.tagName != self.i:
                    block_node = self.createBlock(target_node)
                    target_parent_node.appendChild(block_node)
                    
                    self.report.addSubstitution(self.m)
                    self.report.addCorrection(source_node.tagName)
                else :
                    self.report.addSubstitution(self.m)
                    target_parent_node.appendChild(target_node)
                    

            # ==========
            # Deal with Cite
            # ==========
            elif source_node.tagName in self.profile.lookup(self.ci) :
                target_node = self.target_doc.createElement(self.i)

                # Add the metadata for citation elements to the container parent
                work_uri, expression_uri, lang_tag = self.createSHA1Element(source_node, target_node, base_work_uri, target_parent_work_uri, target_parent_expression_uri, metadata_parent, lang_tag, index)
                target_parent_node.appendChild(target_node)
                self.report.addSubstitution(self.i)
                
                index_counter = 0
                for element in source_node.childNodes :
                    if element.nodeType != element.TEXT_NODE:
                        index_counter += 1
                    self.handle(element,target_node,base_work_uri, work_uri, expression_uri, metadata_parent, lang_tag, index_counter)

            else :
                logging.warning('Node {1} in {0} does not occur in mapping list.'.format(target_parent_expression_uri, source_node.tagName))

                
        elif source_node.nodeType == source_node.TEXT_NODE :
            # target_node = self.target_doc.createTextNode()
            
            text = self.stripSpaces(source_node.data)
            # .encode('ascii','xmlcharrefreplace')
            
            if text != ' ' and text != '' and text != '\n':
                # print '\"' + text + '\"'
                target_node = self.target_doc.createTextNode(text)
                
                self.report.addSubstitution('text')
                target_parent_node.appendChild(target_node)
            else :
                # Don't insert empty TEXT_NODEs
                pass
            
            # Don't continue handling, because text nodes do not have children.
        else :
            # If the node is not an element, nor a text node, then do nothing
            pass



    # ----------
    # Utility Functions
    # ----------

    def createLegislativeModificationEvent(self, node, expression_uri):
        mcontainer, new = self.getMContainer(node)
        
        self.creation_event_uri = self.top_uri + 'event/' + self.source_root_uri + '/' + self.v
        self.creation_process_uri = self.top_uri + 'process/' + self.source_root_uri + '/' + self.v
        
        date = self.top_uri + 'date/' + self.v
        
        # ===========
        # Add the modification event
        # ===========
        meta = self.createHrefMeta(self.creation_event_uri, self.t, self.MO['LegislativeModification'])
        if meta : mcontainer.appendChild(meta)
        
        meta = self.createHrefMeta(expression_uri, self.MO['resultOf'], self.creation_event_uri)
        if meta : mcontainer.appendChild(meta)
        
        # ===========
        # Add the modification type
        # ===========
        if self.modification_type :
            meta = self.createHrefMeta(self.creation_event_uri, self.t, self.modification_type)
            if meta : mcontainer.appendChild(meta)
        
        # ===========
        # Add the modification event date
        # ===========
        meta = self.createHrefMeta(self.creation_event_uri, self.MO['date'], date)
        if meta: mcontainer.appendChild(meta)
        
        meta = self.createHrefMeta(date, self.t, self.MO['Date'])
        if meta: mcontainer.appendChild(meta)

        meta = self.createHrefMeta(date, self.t, self.TIME['Instant'])
        if meta: mcontainer.appendChild(meta)
 
        # ===========
        # Add the modification event date value
        # ===========
        meta = self.createPropertyMeta(date, RDF.value, self.v)
        if meta : mcontainer.appendChild(meta)
        
        meta = self.createPropertyMeta(expression_uri, self.DCTERMS['valid'], self.v)
        if meta : mcontainer.appendChild(meta)
        
        # ===========
        # Add a Simple Event Model description
        # ===========
        meta = self.createHrefMeta(self.creation_event_uri, self.t, self.SEM['Event'])
        if meta : mcontainer.appendChild(meta) 
        
        meta = self.createHrefMeta(self.creation_event_uri, self.SEM['eventType'], self.MO['LegislativeModification'])
        if meta : mcontainer.appendChild(meta)
        
        meta = self.createHrefMeta(self.creation_event_uri, self.SEM['hasTime'], date)
        if meta : mcontainer.appendChild(meta)
        
        meta = self.createHrefMeta(date, self.t, self.SEM['Time'])
        if meta : mcontainer.appendChild(meta)
        
        meta = self.createHrefMeta(date, self.SEM['timeType'], self.MO['Date'])
        if meta : mcontainer.appendChild(meta)
        
        meta = self.createPropertyMeta(date, self.SEM['hasTimeStamp'], self.v)
        if meta : mcontainer.appendChild(meta)
        
        # ===========
        # Add a Open Provenance Model process
        # ===========
        meta = self.createHrefMeta(self.creation_process_uri, self.t, self.OPMV['Process'])
        if meta : mcontainer.appendChild(meta)
        
        meta = self.createHrefMeta(self.creation_process_uri, self.TIME['hasEnd'],date)
        if meta : mcontainer.appendChild(meta)
        
        meta = self.createHrefMeta(expression_uri, self.OPMV['wasGeneratedBy'],self.creation_process_uri)
        if meta : mcontainer.appendChild(meta)    
        
        meta = self.createHrefMeta(expression_uri, self.t, self.OPMV['Artifact'])
        if meta : mcontainer.appendChild(meta)     
        
        meta = self.createHrefMeta(expression_uri, self.OPMV['wasGeneratedAt'], date)
        if meta : mcontainer.appendChild(meta)    
        
        meta = self.createPropertyMeta(date, self.TIME['inXSDDateTime'], self.v)
        if meta: mcontainer.appendChild(meta)
        

 
        # ===========
        # Finally add the mcontainer to the node (if it's new)
        # ===========
        if new == True : 
            node.appendChild(mcontainer)                 
        
                

        

    def setNamespaces(self, new_root):
        
        schema_location = self.target_doc.createAttribute(self.schemaLocation)
        schema_location.value = "http://www.metalex.eu/metalex/1.0 ../src/metalex-relaxed.xsd"
        new_root.setAttributeNode(schema_location)
        
        xmlns = self.target_doc.createAttribute(self.xmlns)
        xmlns.value = "http://www.metalex.eu/metalex/1.0" 
        new_root.setAttributeNode(xmlns)
        
        xmlns_xsi = self.target_doc.createAttribute(self.xmlns_xsi)
        xmlns_xsi.value = "http://www.w3.org/2001/XMLSchema-instance" 
        new_root.setAttributeNode(xmlns_xsi)
        
        xmlns_xml = self.target_doc.createAttribute(self.xmlns_xml)
        xmlns_xml.value = "http://www.w3.org/XML/1998/namespace" 
        new_root.setAttributeNode(xmlns_xml)
             


    def getMContainer(self, node):
        new = False
        # Get the existing mcontainer, or create a new one.
        if node.getElementsByTagName(self.mc).length == 0:
            mcontainer = self.target_doc.createElement(self.mc)
            mcontainer.setAttributeNode(self.createNameAttribute(mcontainer))
            new = True
        else:
            mcontainer = node.getElementsByTagName(self.mc).item(0)
        return mcontainer, new

    def handleMetadata(self, node, parent_expression_uri, expression_uri, work_uri, attributes, additional_attrs = None):

        
        mcontainer, new = self.getMContainer(node)
        
        # ===========
        # Add type to expression level identifier
        # ===========
        meta = self.createHrefMeta(expression_uri, self.t, self.MO['BibliographicExpression'])
        if meta : mcontainer.appendChild(meta)
        
        # ===========
        # Add reference to work level identifier
        # ===========
        meta = self.createHrefMeta(expression_uri, self.realizes, work_uri)
        if meta : mcontainer.appendChild(meta)
        
        # ===========
        # Add type to work level identifier
        # ===========
        meta = self.createHrefMeta(work_uri, self.t, self.MO['BibliographicWork'])
        if meta : mcontainer.appendChild(meta)
        
        # ===========
        # Add reference to various manifestation level identifiers
        # ===========
        html_page = expression_uri.replace(self.top_uri, self.doc_uri) + '/data.html'
        xml_doc = expression_uri.replace(self.top_uri, self.doc_uri) + '/data.xml'
        rdf_doc = expression_uri.replace(self.top_uri, self.doc_uri) + '/data.rdf'
        meta = self.createHrefMeta(expression_uri, self.FOAF['homepage'], html_page)
        if meta : mcontainer.appendChild(meta)
        meta = self.createHrefMeta(expression_uri, self.FOAF['page'], xml_doc)
        if meta : mcontainer.appendChild(meta)
        meta = self.createHrefMeta(expression_uri, self.RDFS['isDefinedBy'], rdf_doc)
        if meta : mcontainer.appendChild(meta)


        
        
        
        # ===========
        # Add result relation between creation event and expression
        # ===========
        meta = self.createHrefMeta(self.creation_event_uri, self.result, expression_uri)
        if meta : mcontainer.appendChild(meta)
          

        
        # ===========
        # Add reference to expression-level parent
        # ===========
        
        # TODO: Include language tag in expression of parent work URI. 
        # Perhaps the parent_expression_uri chain should be replaced by parent_expression_uri's throughout.
        if parent_expression_uri :
            meta = self.createHrefMeta(expression_uri, self.parent, parent_expression_uri)
            if meta : mcontainer.appendChild(meta)     
                  

        
        # ===========
        # Add the 'additional attributes' if they exist
        # ===========
        if additional_attrs :
            for k in additional_attrs :
                # Check if we're dealing with a URI or a Literal
                if re.match('^http',additional_attrs[k]) :
                    meta = self.createHrefMeta(expression_uri, k, additional_attrs[k])
                    if meta : mcontainer.appendChild(meta)
                else :
                    meta = self.createPropertyMeta(expression_uri, k, additional_attrs[k])
                    if meta : mcontainer.appendChild(meta)
                
        
        # ===========
        # Transfer other attributes from BWB node  
        # ===========      
        for k in attributes.keys():
            
            # Get the attribute's value
            value = attributes[k].value
            
            # Only do stuff if the attribute has a value
            if value != '' :
                # If we're dealing with a 'cite_target' attribute, create a href URI for known non-URI identifiers (e.g. JuriConnect)
                if k in self.profile.lookup('cite_target') :
                    target = self.mintTargetURI(value)
                
                    # Add an edge to the citegraph
                    self.cg.update((expression_uri,target))
                
                    meta = self.createHrefMeta(expression_uri, self.cites, target)
                    if meta : mcontainer.appendChild(meta)
                
                    
                # Always add the original attribute, unless it is the xml:lang property
                if k != "xml:lang" :
                    meta = self.createPropertyMeta(expression_uri, self.WO[k], attributes[k].value)   
                else :
                    # Add a custom language property, as xml:lang cannot be used as rdf:Property in the ontology.
                    meta = self.createPropertyMeta(expression_uri, self.MO['lang'], attributes[k].value)            
                    
                if meta : mcontainer.appendChild(meta)
                
        # ===========
        # Finally add the mcontainer to the node (if it's new)
        # ===========
        if new == True : 
            node.appendChild(mcontainer)
    
    def mintTargetURI(self,value):
        target = self.convertJuriConnect(value)

        if target == None :
            target = self.top_uri + value

        return target
            
    def getHContainerWorkURI(self, node, base_work_id, index):
        try :
            nr = self.getText(node.getElementsByTagName("nr")[0].childNodes)
            work_uri = "{0}/{1}/{2}".format(base_work_id,node.localName.encode('utf-8'),nr.strip().encode('utf-8'))
            short_work_uri = "{0}/{1}/{2}".format(self.root_work_uri,node.localName.encode('utf-8'),nr.strip().encode('utf-8'))
        except :
            work_uri = "{0}/{1}/{2}".format(base_work_id,node.localName.encode('utf-8'),index)
            short_work_uri = "{0}/{1}/{2}".format(self.root_work_uri,node.localName.encode('utf-8'),index)
            
        return work_uri, short_work_uri
            
    def createClassAttribute(self, node):
        new_class = self.target_doc.createAttributeNS(str(self.XHTML),self.cl)
        new_class.value = node.tagName
        return new_class
        
    def createNameAttribute(self, node):
        new_name = self.target_doc.createAttribute(self.n)
        new_name.value = node.tagName
        return new_name


    # Retrieve text from child nodes (strip XML elements).
    def getText(self, nodelist):
        rc = []
        # For all child nodes, recursively get the 'data' of each child node (the text)
        for node in nodelist:
            if node.nodeType == node.TEXT_NODE:
                # Append + extra spacing for security, we'll remove the doubles later
                rc.append(' ' + node.data.encode('utf-8') + ' ' )
            else:
                rc.append(self.getText(node.childNodes))

        # Return the UTF-8 encoding of the text with all occurrences of multiple spaces replaced by a single one
        return self.stripSpaces(''.join(rc))   

    # Retrieve text from child nodes of particular element types
    def getTextForElements(self, nodelist, elementTypes):
        rc = []
        # For all child nodes, recursively get the 'data' of each child node (the text)
        for node in nodelist:
            if node.nodeType == node.ELEMENT_NODE and node.tagName in elementTypes:
                rc.append(self.getText(node.childNodes))
            elif node.nodeType == node.TEXT_NODE:
                # Append + extra spacing for security, we'll remove the doubles later
                rc.append(' ' + node.data.encode('utf-8') + ' ') 

        # Return the UTF-8 encoding of the text with all occurrences of multiple spaces replaced by a single one
        return self.stripSpaces(''.join(rc))

    def stripSpaces(self, text):
        return re.sub(r'\s\s+',' ', re.sub(r'\n',' ', text))

    def stripTexts(self, node):
        cNodes = node.childNodes 
        for child in cNodes :
            # child.normalize()
            if child.nodeType == child.TEXT_NODE and child.data.isspace() :
                node.removeChild(child)
                child.unlink()


    def createHrefMeta(self, s, p, o):
        if self.produce_rdf :
            self.graph.add((URIRef(s), URIRef(p), URIRef(o)))
        
        if self.inline_metadata :
            meta = self.target_doc.createElement(self.m)
            meta.setAttributeNode(self.createNameAttribute(meta))
            meta.setAttributeNode(self.createItemIdentifier(meta))
    
            about = self.target_doc.createAttribute(self.a)
            about.value = s
    
            rel = self.target_doc.createAttribute(self.r)
            rel.value = p
    
            href = self.target_doc.createAttribute(self.h)
            href.value = o
    
            meta.setAttributeNode(about)
            meta.setAttributeNode(rel)
            meta.setAttributeNode(href)
    
            return meta
        else :
            return None

    def createPropertyMeta(self, s, p, o):
        
        if re.match('^\d\d\d\d-\d\d-\d\d$',o) :
            dtype = XSD.date
        elif re.match('^\d+$',o) :
            dtype = XSD.int
        else :
            dtype = XSD.string
        
        if self.produce_rdf: 
            self.graph.add((URIRef(s), URIRef(p), Literal(o, datatype=dtype)))
        
        if self.inline_metadata :
            meta = self.target_doc.createElement(self.m)
            meta.setAttributeNode(self.createNameAttribute(meta))
            meta.setAttributeNode(self.createItemIdentifier(meta))
    
            about = self.target_doc.createAttribute(self.a)
            about.value = s
    
            prop = self.target_doc.createAttribute(self.p)
            prop.value = p
    
            datatype = self.target_doc.createAttribute(self.dt)
            datatype.value = dtype
                
            content = self.target_doc.createAttribute(self.ct)
            content.value = o
    
            meta.setAttributeNode(about)
            meta.setAttributeNode(prop)
            meta.setAttributeNode(datatype)
            meta.setAttributeNode(content)

            return meta
        else :
            return None

    def createItemIdentifier(self, new_node):
        # Create the Item Level identifier
        item_id = str(uuid.uuid4())
           
        new_id = self.target_doc.createAttribute(self.id)
        new_id.value = item_id
        return new_id
        
        
    def createIdentifyingAttributes(self, node, new_node, expression_uri):
        new_node.setAttributeNode(self.createItemIdentifier(new_node))
        
        # Add an RDFa about attribute for the expression URI
        about = self.target_doc.createAttribute(self.a)
        about.value = expression_uri
        new_node.setAttributeNode(about)
        
        new_node.setAttributeNode(self.createNameAttribute(new_node))
        new_node.setAttributeNode(self.createClassAttribute(node))    
        
        
         

    def createSHA1Element(self, source_node, target_node, base_work_uri, target_parent_work_uri, target_parent_expression_uri, metadata_parent, lang_tag, index):
        # TODO: check for integer lang_tag


        # TODO: TEST WHETHER base_work_uri SHOULD BE REPLACED BY target_parent_work_uri
        # CHANGE HAS BEEN MADE, UNTESTED
        
        work_uri = target_parent_work_uri + "/" + source_node.localName + "/" + str(index)
        
        # Containers and blocks don't have nice identifiers, so we create a SHA1 hash of the 'plain' text contained in the element.
        sha1_hex = hashlib.sha1(self.getText(source_node.childNodes)).hexdigest()
        sha1_id = base_work_uri + "/" + source_node.localName + "/" + sha1_hex 

        self.createIdentifyingAttributes(source_node, target_node, sha1_id)
        
        lang_tag = self.setLanguageTag(source_node, target_node, lang_tag)
        expression_uri = self.getExpressionURI(work_uri, lang_tag)
        
        additional_attrs = { self.sameAs : sha1_id }

        additional_attrs[self.t] = self.o + source_node.tagName
        
        self.handleMetadata(metadata_parent, target_parent_expression_uri, expression_uri, work_uri, source_node.attributes, additional_attrs)
        
        return work_uri, expression_uri, lang_tag

    def convertJuriConnect(self, juriconnect):
        # example:   1.0:v:BWBR0011823&amp;artikel=8



        # Check whether it is a JuriConnect identifier (i.e. the regex produces a match), 
        # then do something fancy, otherwise return None
        if re.match('\d.\d:\w:([BWBRV]{4}\d{7})',juriconnect) :
            # Use a Regex to get the relevant parts from the juriconnect identifier
            svalue = re.split('[:|&|;|=]',juriconnect)
        

            # This is the work-level identifier if no article is referred to
            target = self.top_uri + svalue[2]                

            # Get all hcontainers from the profile
            hcl = list(self.profile.lookup('hcontainer'))
            hcl[len(hcl):] = list(self.profile.lookup('hcontainer_text'))
            
            
            # TODO: Check whether this is correct
            for hc in hcl :
                if svalue.count(hc) > 0 :
                    # This is the work-level identifier for the target of the citation if it refers to a hcontainer
                    target += '/' + svalue[svalue.index(hc)] + '/' + svalue[svalue.index(hc)+1]
                    break 


            if svalue[1] == 'c' and svalue.count('g') == 0:
                # If the Juriconnect reference is of type 'c', and no date is specified, 
                # add the current version of this document to date the reference
                target += '/' + self.v
            elif svalue.count('g') > 0:
                # Otherwise, if the date is specified, add that date to the reference
                target += '/' + svalue[svalue.index('g')+1]    

            return target
        else :
            return None
        
        
    def printXML(self):
        return self.target_doc.toprettyxml()
        
    def writeXML(self, filename):
        # Write the target_document to a file using the pretty printer
        target_file = open(filename, 'w')
        target_file.write(self.target_doc.toprettyxml(encoding = 'utf-8'))
        target_file.close()

    def writeRDF(self, filename, upload_url, format='turtle'):
        # Serialize to file
        self.graph.serialize(destination=filename, format=format)     
        logging.debug("Serialized to {0}".format(filename))  
        
        if upload_url :
            logging.debug("Uploading RDF triples to : {0}".format(upload_url))
            
            if self.flags['store'] == 'cliopatria' :
                register_openers()
                 
                data = {"data" : open(filename, "rb"), "dataFormat": format, "baseURI" : self.rdf_graph_uri }
                 
                datagen, headers = multipart_encode(data)
                request = urllib2.Request(upload_url, datagen, headers)
                
                if 'user' in self.flags :
                    auth_string = "{0}:{1}".format(self.flags['user'],self.flags['pass'])
                    auth_string_b64 = base64.b64encode(auth_string)
                    request.add_header('Authorization','Basic '+auth_string_b64)
                    
                reply = urllib2.urlopen(request).read()
                logging.debug(reply)
            elif self.flags['store'] == '4store' :
                upload_url = upload_url + "/data/"
                logging.debug("Upload URL for 4Store : {0}".format(upload_url))
                
                if format == 'turtle' :
                    mime = 'application/x-turtle'
                elif format == 'RDF/XML' :
                    mime = 'application/rdf+xml'
                
                graph = self.graph.serialize(format=format)
                    
                data = {"data" : graph, "mime-type": mime, "graph" : self.rdf_graph_uri }
                     
                data_encoded = urllib.urlencode(data)
    
                request = urllib2.Request(upload_url, data=data_encoded)
    
                reply = urllib2.urlopen(request).read()
    
                logging.debug(reply)
                
#                with open(filename, "rb") as h:
#                    data = h.read() 
#    
#                request = urllib2.Request(upload_url, data)
#                if format == 'turtle' :
#                    request.add_header('Content-Type','application/x-turtle')
#                elif format == 'RDF/XML' :
#                    request.add_header('Content-Type','application/rdf+xml')
#                    
#                request.get_method = lambda: 'PUT'
#                reply = urllib2.urlopen(request).read()
#                logging.debug(reply)
            elif self.flags['store'] == 'virtuoso':
                logging.debug("Loading into Virtuoso using 'isql-v'")
                
                password = self.flags['virtuoso_pw']
                
                if format == 'turtle':
                    method = 'DB.DBA.TTLP_MT'
                elif format == 'RDF/XML':
                    method = 'RDF_LOAD_RDFXML_MT' 
                else :
                    logging.error("Upload format not supported!")
                    return
                
                
                graph_uri = self.rdf_graph_uri
                
                # Uncommenting the below Will use one giant graph for Virtuoso
                # graph_uri = 'http://doc.metalex.eu'
                
                absolute_filename = os.path.abspath(filename)
                
                logging.info('Writing graph uri to .graph file')
                (fn, ext) = os.path.splitext(filename) 
                
                graph_filename = fn + '.graph'
                
                graph_file = open(graph_filename,'w')
                graph_file.write(graph_uri)
                graph_file.close()
                
                command = 'echo "{} (file_to_string_output(\'{}\'),\'\',\'{}\',256);" | isql-v -U dba -P {}'.format(method, absolute_filename, graph_uri, password )
                
                try :
                    out = subprocess.check_output(command,shell=True)
                    logging.info(out)
                except Exception as e:
                    logging.error("Could not load file into virtuoso")
                
            else: 
                logging.error("Store type not supported, or no store type set. Was expecting one of cliopatria, 4store, virtuoso.")
        
        
    def writeGraph(self, filename, format='pajek') :
        # Write the graph to a file using the specified format
        target_file = open(filename, 'w')
        
        if format == 'pajek' :
            target_file.write(self.cg.writePajek())
        elif format == 'DOT' :
            target_file.write(self.cg.writeDOT())

        target_file.close()
        
    def getCited(self) :
        return self.cg.getNodes()

    def createBlock(self, new_node):
        block_node = self.target_doc.createElement(self.b)
        block_node.setAttributeNode(self.createItemIdentifier(block_node))
        block_node.setAttributeNode(self.createNameAttribute(block_node))
        block_node.setAttributeNode(self.createClassAttribute(block_node))
        block_node.appendChild(new_node)
        return block_node
    
    def setLanguageTag(self, source_node, target_node, lang_tag):
        lt = source_node.getAttribute(u'xml:lang')
        
        lt_attribute = self.target_doc.createAttribute('xml:lang')
        
        if lt == "" and lang_tag == "" :
            return ""
        elif lt == "" :
            lt = lang_tag

        lt_attribute.value = lt   
        target_node.setAttributeNode(lt_attribute)
        
        return lt



    def getExpressionURI(self, work_uri, lang_tag):
        if lang_tag == "":
            expression_uri = work_uri + "/" + self.v
        else:
            try :
                expression_uri = work_uri + "/" + lang_tag + "/" + self.v
            except Exception as e:
                logging.error("Decoding problem:")
                logging.error(self.v)
                logging.error(work_uri)
                logging.error(lang_tag)
                raise(e)
            
        return expression_uri


        
        
        
