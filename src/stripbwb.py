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
@deprecated: No longer used

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

@summary: DEPRECATED. This module contains a script for retrieving the text from BWB XML files, and splitting it into sentences.

'''


import xml.dom.minidom
import urllib
import nltk.data
import uuid
import codecs

# Load the Dutch sentence splitter tokenizer from Punkt NLTK
splitter = nltk.data.load('tokenizers/punkt/dutch.pickle')

# Global counter for sentences and sentence fragments
scount = 0


# ----------
# Utility Functions
# ----------

# Retrieve text from child nodes (strip XML elements).
def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            lines = node.data.splitlines()
            if len(lines)>1 :
                for l in lines:
                    if l != '':
                        rc.append(" " + l.lstrip())
            else :
                rc.append(node.data)
        else:
            rc.append(getText(node.childNodes))
            
    return ''.join(rc)

def stripTexts(node):
    cNodes = node.childNodes 
    for child in cNodes :
        # child.normalize()
        if child.nodeType == child.TEXT_NODE and child.data.isspace() :
            node.removeChild(child)
            child.unlink()


# ----------
# Basic Functions
# ----------


def handleBWB(bwbid,doc):
    print "Starting %s ..." % bwbid
    # bwbid = getBWBid(doc.getElementsByTagName("wetgeving")[0])
    handleArticles(bwbid, doc.getElementsByTagName("artikel"))
    print "... end %s." % bwbid

    
def getBWBid(wetgeving):
    return wetgeving.getAttribute("bwb-id")
    
def handleArticles(bwbid, articles):
    # Previous article ID is None
    prevaid =  None 
    for a in articles:
        previd = handleArticle(bwbid, prevaid, a)

def handleArticle(bwbid, prevaid, a):
    nr = getText(a.getElementsByTagName("nr")[0].childNodes)
    # Create Juriconnect id for article
    aid = bwbid+"/artikel="+nr
    
    # Remove whitespace between child nodes
    stripTexts(a)
    
    # Previous sentence or member ID is None
    previd = None
    cNodes = a.childNodes
    for c in cNodes :
        if c.nodeName == "lid":
            previd = handleLid(aid, previd, c)
        elif c.nodeName == "al" or c.nodeName == "lijst":
            previd = handleAlineaOrList(aid, previd, c)
    
    return aid


def handleLid(aid, prevlidid, lid):
    lidnr = getText(lid.getElementsByTagName("lidnr")[0].childNodes)
    lidid = aid+"/lid="+lidnr

    # Remove whitespace between child nodes
    stripTexts(lid)

    previd = None
    cNodes = lid.childNodes
    for c in cNodes :
        if c.nodeName == "al" or c.nodeName == "lijst":
            previd = handleAlineaOrList(lidid, previd, c)
    
    return lidid

def handleAlineaOrList(pid, previd, al):

    if al.nodeName == "lijst":
        return handleLijst(pid, previd, al)
    else:
        if al.previousSibling:
            if al.previousSibling.nodeName == "lijst" :
                # skip, previous was list
                return previd
        if al.nextSibling:
            if al.nextSibling.nodeName == "lijst":
                # skip, next is list
                return previd
                
        return handleSimpleAlinea(pid, previd, al)

        
def handleSimpleAlinea(pid, previd, al):
    t = getText(al.childNodes)
    if t.isspace() or len(t) == 0:
        return

    # Split the paragraph into separate sentences
    sentences = splitter.tokenize(t.strip())
    for s in sentences :
        sid = handleSentence(pid, previd, s)

def handleSentence(pid, previd, s):
    global scount
    global out
    scount += 1
    print >> out, "%s/s%s\n%s" % (pid, scount, s)
    return scount


# ----------
# List Functions
# ----------

    
def handleListItem(pid, previd, li):
    # Remove all superfluous text nodes
    stripTexts(li)
    
    linr = li.getElementsByTagName('li.nr')[0]
    lirnt = getText(linr.childNodes).strip('.')
    
    liid = pid + '/li=' + lirnt
    
    # INCORRECT
    # This is not correct, as these alineas are definitely not independent sentences, or at least: they shouldn't be.
    cNodes = li.childNodes
    for c in cNodes:
        if c.nodeName == "al" or c.nodeName == "lijst":
            previd = handleAlineaOrList(liid, previd, c)
        
    return previd

def handleLijst(pid, previd, lijst):
    global out
    prefix, postfix = False, False
    stripTexts(lijst)
    
    prev = lijst.previousSibling
    last = lijst.lastChild
    next = lijst.nextSibling
    
    if prev:
        prevText = getText(prev.childNodes)
    
        sentences = splitter.tokenize(prevText.strip())

        # For all preceding sentences, until the one just before the list, do:
        for s in sentences[:-1] :
            previd = handleSentence(pid, previd,s)
            
        # If the sentence before the list does not end with a colon or semicolon, it is a separate sentence
        if sentences[-1].endswith(':') or sentences[-1].endswith(';'):
            print >> out, "<LIJST>"
            previd = handleSentence(pid,previd, sentences[-1])
        else:
            previd = handleSentence(pid, previd, sentences[-1])
            print >> out, "<LIJST>"
    else:
        print >> out, "<LIJST>"
    

    if last:
        lastText = getText(last.getElementsByTagName("al")[0].childNodes).rstrip()
        
        if lastText.endswith('.') :
            postfix = False
        elif next: 
            postfix = True
        
        
    cNodes = lijst.childNodes
    for child in cNodes[:-1] :
        if child.nodeName == "li":
            previd = handleListItem(pid,previd,child)
        

    if postfix :
        nextText = getText(next.childNodes)
        sentences = splitter.tokenize(nextText) 
        
        # First handle the last item of the regular list
        previd = handleListItem(pid, previd, cNodes[-1])
        # Get the text of the first 'sentence', as it is the last sentence of the list
        previd = handleSentence(pid, previd, sentences[0])
        
        print >> out, "</LIJST>"
        
        # For all succeeding sentences, until the one just before the list, treat them as separate sentences:
        for s in sentences[1:] :
            previd = handleSentence(pid, previd,s)

    elif not(postfix) and next :
        # NOTE: The last item on the list is a special case, but for now we don't treat it as such.
        previd = handleListItem(pid, previd,cNodes[-1])
        print >> out, "</LIJST>"
        previd = handleSimpleAlinea(pid, previd, next)
    else :
        previd = handleListItem(pid, previd,cNodes[-1])
        print >> out, "</LIJST>"
    
    return previd
    

bwbids = ['BWBR0001939','BWBR0001860']

for bwbid in bwbids:
    scount = 0 # Reset sentence counter
    # Load the regulation XML
    usock = urllib.urlopen('http://wetten.overheid.nl/xml.php?regelingID='+bwbid)

    # Parse regulation into DOM tree
    doc = xml.dom.minidom.parse(usock)

    # Close socket to URL
    usock.close()

    out = codecs.open(bwbid+'.txt', 'w', encoding='utf-8')
    try:
        # AND FINALLY....
        # Call handler on parsed XML structure
        handleBWB(bwbid, doc)
    finally:
        out.close()


