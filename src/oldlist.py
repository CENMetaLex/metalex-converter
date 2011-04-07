def handleLIAlinea(bwbid,al):
    if al.previousSibling:
        if al.previousSibling.nodeName == "lijst" :
            # skip, previous was list
            pass
        elif al.nextSibling:
            if al.nextSibling.nodeName == "lijst":
                # skip, next is list
                handleSubLijst(bwbid,al.nextSibling)
            else: 
                handleLISimpleAlinea(bwbid,al)
        else: 
            handleLISimpleAlinea(bwbid,al)
    else: 
        handleLISimpleAlinea(bwbid,al)        

def handleLid(bwbid,lid):
    lidnr = getText(lid.getElementsByTagName("lidnr")[0].childNodes)
    bwbid = bwbid+"&lid="+lidnr

    # Remove whitespace between child nodes
    stripTexts(lid)

    cNodes = lid.childNodes

    for child in cNodes :
        if child.nodeName == "al":
            handleAlinea(bwbid,child)


        
def handleLISimpleAlinea(bwbid,al):
    t = getText(al.childNodes)
    if t.isspace() or len(t) == 0:
        return

    sentences = splitter.tokenize(t.strip())
    for s in sentences :
        handleSentenceFragment(bwbid,s)
        


def handleListSentence(bwbid, s):
    printSentence(bwbid,s,'list')

def handleSentenceFragment(bwbid, s):
    printSentence(bwbid,s,'sfragment')
    
def handleLastSentenceFragment(bwbid, s):
    printSentence(bwbid,s,'sfragment&last=true')    
    

def handleListItem(bwbid, li):
    # Remove all superfluous text nodes
    stripTexts(li)
    
    linr = li.getElementsByTagName('li.nr')[0]
    lirnt = getText(linr.childNodes).strip('.')
    
    bwbid += '&li=' + lirnt
    
    # INCORRECT
    # This is not correct, as these alineas are definitely not independent sentences, or at least: they shouldn't be.
    als = li.getElementsByTagName('al')
    for al in als:
        handleLIAlinea(bwbid,al)

# # INCOMPLETE
# def handleLastListItem(bwbid, li):
#     # Remove all superfluous text nodes
#     stripTexts(li)
# 
#     linr = li.getElementsByTagName('li.nr')[0]
#     lirnt = getText(linr.childNodes).strip('.')
# 
#     bwbid += '&li=' + lirnt 
# 
#     cNodes = li.childNodes
#     for c in cNodes[:-1]:
#         if c.nodeName == "al":
#             handleLIAlinea(bwbid,al)  
#     
#     last = cNodes[-1]
#     if last.nodeName == "al":
#         handleLIAlinea(bwbid,al) 



def handleLijst(bwbid,lijst):
    prefix, postfix = False, False
    stripTexts(lijst)
    
    prev = lijst.previousSibling
    last = lijst.lastChild
    next = lijst.nextSibling
    
        
    lText = ""
    
    if prev:
        prevText = getText(prev.childNodes)
    
        sentences = splitter.tokenize(prevText.strip())

        # For all preceding sentences, until the one just before the list, do:
        for s in sentences[:-1] :
            handleSentence(bwbid,s)
            
        # If the sentence before the list does not end with a colon or semicolon, it is a separate sentence
        if sentences[-1].endswith(':') or sentences[-1].endswith(';'):
            handleSentenceFragment(bwbid,sentences[-1])
        else:
            handleSentence(bwbid,sentences[-1])
    

    if last:
        lastText = getText(last.getElementsByTagName("al")[0].childNodes).rstrip()
        
        if lastText.endswith('.') :
            postfix = False
        elif next: 
            postfix = True
        
        
    cNodes = lijst.childNodes
    for child in cNodes[:-1] :
        if child.nodeName == "li":
            handleListItem(bwbid,child)
        

    if postfix :
        nextText = getText(next.childNodes)
        sentences = splitter.tokenize(nextText) 
        
        # First handle the last item of the regular list
        handleListItem(bwbid, cNodes[-1])
        # Get the text of the first 'sentence', as it is the last sentence of the list
        handleLastSentenceFragment(bwbid, sentences[0])
        
        # For all succeeding sentences, until the one just before the list, treat them as separate sentences:
        for s in sentences[1:] :
            handleSentence(bwbid,s)

    elif not(postfix) and next :
        # NOTE: The last item on the list is a special case, but for now we don't treat it as such.
        handleListItem(bwbid,cNodes[-1])
        handleSimpleAlinea(bwbid,next)


def handleSubLijst(bwbid,lijst):
    prefix, postfix = False, False
    stripTexts(lijst)

    prev = lijst.previousSibling
    last = lijst.lastChild
    next = lijst.nextSibling


    lText = ""

    if prev:
        prevText = getText(prev.childNodes)

        sentences = splitter.tokenize(prevText.strip())

        # For all preceding sentences, until the one just before the list, do:
        for s in sentences[:-1] :
            handleSentenceFragment(bwbid,s)


    if last:
        lastText = getText(last.getElementsByTagName("al")[0].childNodes).rstrip()

        if lastText.endswith('.') :
            postfix = False
        elif next: 
            postfix = True


    cNodes = lijst.childNodes
    for child in cNodes[:-1] :
        if child.nodeName == "li":
            handleListItem(bwbid,child)


    if postfix :
        nextText = getText(next.childNodes)
        sentences = splitter.tokenize(nextText) 

        # First handle the last item of the regular list
        handleListItem(bwbid, cNodes[-1])
        # Get the text of the first 'sentence', as it is the last sentence of the list
        handleLastSentenceFragment(bwbid, sentences[0])

        # For all succeeding sentences, until the one just before the list, treat them as separate sentences:
        for s in sentences[1:] :
            handleSentenceFragment(bwbid,s)

    elif not(postfix) and next :
        # NOTE: The last item on the list is a special case, but for now we don't treat it as such.
        handleListItem(bwbid,cNodes[-1])
        handleLISimpleAlinea(bwbid,next)