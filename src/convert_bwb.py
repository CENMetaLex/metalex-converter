from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup
from datetime import date
from converter.metalex import MetaLexConverter
from converter.util import Profile, CiteGraph
import codecs
import csv
import os.path
import pickle
import re
import sys
import urllib2
import xml.dom.minidom
import glob
import string



def getVersionInfo(bwbid):
    uri = 'http://wetten.overheid.nl/{0}/informatie'.format(bwbid)

    try: 
        info = urllib2.urlopen(uri)
        html = info.read()
        soup = BeautifulSoup(html)
        title = None
        abbreviation = None
        type = None
        
        divs = soup.findAll(id="inhoud-titel")
        for div in divs :
            match = re.search(r'<h2>(.*?)</h2>', str(div))
            if match :
                title = match.group(1).strip()
                break
        
        table_rows = soup.findAll("tr")
        for row in table_rows :
            match = re.search(r'Afkorting:</th><td> (.*?)<', str(row))
            if match :
                abbreviation = match.group(1).strip()
                if abbreviation == "Geen" :
                    abbreviation = None
                continue
            
            match = re.search(r'<tr.*?><td.*?><p><b>(\d\d)-(\d\d)-(\d\d\d\d)</b></p></td><td.*?>(.*?)</td><td.*?>(.*?)</td>', str(row))
            if match :
#                print "1 pre", match.group(5)
                if match.group(5) != "":
                    text = string.replace(match.group(5),'<p>','')
                    text = string.replace(text,'</p>','')
                    type = string.replace(BeautifulStoneSoup(text, convertEntities=BeautifulStoneSoup.HTML_ENTITIES).contents[0].strip(),' ','_')
#                    print "1 ", type
                    if not re.match(r'\w{6,}',type) :
#                        print "2 pre", match.group(4)
                        if match.group(4) != "" :
                            text = string.replace(match.group(4),'<p>','')
                            text = string.replace(text,'</p>','')
                            type = string.replace(BeautifulStoneSoup(text, convertEntities=BeautifulStoneSoup.HTML_ENTITIES).contents[0].strip(),' ','_')
#                            print "2 ", type
                            if not re.match(r'\w{6,}',type) :
                                type = None
                return "{0}-{1}-{2}".format(match.group(3), match.group(2), match.group(1)), type, abbreviation, title
    except Exception as e:
        print e
        print "ERROR: Error loading version info from HTML page. Are you sure the BWBID is valid?"
        return None
    
    return str(date.today()), type, abbreviation, title

def convert(bwbid, cite_graph, profile, reports, flags):
    data_dir = flags['data_dir']
    out_dir = flags['out_dir']
    
    
    print "Starting conversion for {0} ...".format(bwbid)
    
    if flags['no_update'] :
        if glob.glob('{0}{1}_*-*-*.xml'.format(data_dir, bwbid)) :
            print "Some version of {0} already exists, skipping ...".format(bwbid)
            return
        
    if flags['skip_if_existing'] :
        if glob.glob('{0}{1}_*-*-*_ml.xml'.format(out_dir, bwbid)) :
            print "Some MetaLex XML version already exists, skipping ..."
            return

    print "Getting version date from info URL..."
    date_version, modification_type, abbreviation, title = getVersionInfo(bwbid)
    if not(date_version) :
        print "No version date for {0}. Skipping...".format(bwbid)
        return
    
    print "Title:               {0}".format(title)
    print "Abbreviation:        {0}".format(abbreviation)
    print "Modification type:   {0}".format(modification_type)
    print "Latest version date: {0}".format(date_version)
    print "... done"

    source_doc_filename = '{0}{1}_{2}.xml'.format(data_dir, bwbid, date_version)
    target_doc_filename = '{0}{1}_{2}_ml.xml'.format(out_dir, bwbid, date_version)
    target_rdf_filename = '{0}{1}_{2}.n3'.format(out_dir, bwbid, date_version)
    target_net_filename = '{0}{1}_{2}.net'.format(out_dir, bwbid, date_version)



    # Set doc to none to be able to detect whether it has already been loaded from URL
    doc = None

    if not os.path.isfile(source_doc_filename) :
        # First open the BWB document from URL and save it to a file. Ensure proper encoding
        print "Loading source from URL..."
        socket = urllib2.urlopen('http://wetten.overheid.nl/xml.php?regelingID=' + bwbid)
        # Parse regulation into DOM tree
        doc = xml.dom.minidom.parse(socket)
        # Close socket to URL or file
        socket.close()
        print "... done"
        print "Storing source to file..."
        # Save a copy of the file in the data cache
        bwb_file = codecs.open(source_doc_filename, 'w')
        bwb_file.write(doc.toprettyxml(encoding = 'utf-8'))
        bwb_file.close()
        print "... done"

    if not doc :
        print "Loading source from file..."
        # Open the BWB document from file
        socket = open(source_doc_filename, 'r')
        # Parse regulation into DOM tree
        doc = xml.dom.minidom.parse(socket)
        # Close socket to URL or file
        socket.close()
        print "... done"

    ml_converter = MetaLexConverter(bwbid, doc, date_version, modification_type, abbreviation, title, profile, flags)

    # Handle the regulation...
    print "Starting conversion..."
    try :
        ml_converter.handleRoot()
        print "... done"
    
        print "Storing output to files ..."
        # print ml_converter.printXML()
        print "Writing {0}".format(target_doc_filename)
        ml_converter.writeXML(target_doc_filename)
        
        if flags['produce_rdf'] :
            print "Writing {0}".format(target_rdf_filename)
            ml_converter.writeRDF(target_rdf_filename, flags['rdf_upload_url'], 'turtle')
            
        if flags['produce_graph'] :
            print "Writing {0}".format(target_net_filename)
            ml_converter.writeGraph(target_net_filename, 'pajek')
    
        print "... done"
    
        if cite_graph != None and flags['produce_graph'] and flags['produce_full_graph']:
            print "Appending citegraph ..."
            cite_graph.append(ml_converter.cg)
            print "... done"
    
        # Append conversion report
        reports.append(ml_converter.report.getReport())
    
        print "... done converting {0}".format(bwbid)
    
        # Make sure to delete the ml_converter, to save up on garbage collection
        del ml_converter
        del doc
    except UnicodeDecodeError:
        print "UnicodeDecodeError: Skipping conversion of {0}...".format(bwbid)
    except :
        print "Unexpected error:", sys.exc_info()[0]
        raise


def convertAll(bwbid_dict, flags):
    try :
        total = len(bwbid_dict)
        count = 0

        cg = CiteGraph()

        reports = []
        profile = Profile('./converter/bwb-mapping.txt')
        

        for bwbid in bwbid_dict :
            count += 1
            print "\n------\nProcessing {0}/{1} ({2}%)\n------\n".format(count, total, (float(count) / float(total)) * 100)
            try :
                convert(bwbid, cg, profile, reports, flags)
            except KeyboardInterrupt:
                print "Conversion Aborted on document ID: {0}".format(bwbid)
                break

        if flags['produce_graph'] and flags['produce_full_graph']:
            print "Writing full graph to file \'{0}\'...".format(flags['graph_file'])
            target_file = open(flags['graph_file'], 'w')
            target_file.write(cg.writePajek())
            target_file.close()
            print "... done"

        processReports(reports, profile, flags['report_file'])

        print "\n------\nDONE\n------\n"

    except IOError as (errno, strerror):
        print "I/O error({0}): {1}".format(errno, strerror)



def processReports(reports, profile, report_file):
    reportwriter = csv.writer(open(report_file, 'w'))

    keys = profile.keys()

    reportwriter.writerow(['Substitutions'])
    reportwriter.writerow(['Document ID'] + keys)
    for r in reports :
        subs = r['substitutions']
        doc = r['docid']

        subsrow = []

        for k in keys :
            if k in subs :
                subsrow.append(subs[k])
            else :
                subsrow.append(0)
        reportwriter.writerow([doc] + subsrow)

    values = set()

    # Flatten the list of values from the profile...
    vs = [item for sublist in profile.values() for item in sublist if item in profile.lookup('hcontainer_text') or item in profile.lookup('container_ext') or item in profile.lookup('inline') or item in profile.lookup('milestone')]
    for v in vs:
        values.add(v)

    reportwriter.writerow(['Corrections'])
    reportwriter.writerow(['Document ID'] + list(values))
    for r in reports :
        corrs = r['corrections']
        doc = r['docid']

        corrsrow = []

        for v in values :
            if v in corrs:
                corrsrow.append(corrs[v])
            else :
                corrsrow.append(0)

        reportwriter.writerow([doc] + corrsrow)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        flags = {'inline_metadata': True, 'produce_rdf': True, 'produce_graph': True, 'produce_report': True, 'skip_if_existing': False, 'report_file': '../out/report.csv', 'data_dir': '../data/', 'out_dir' : '../out/', 'graph_file': '../out/full_graph_{0}.net'.format(date.today()), 'rdf_upload_url': None, 'no_update': False, 'produce_full_graph': True}

        
        if '--no-inline-metadata' in sys.argv :
            flags['inline_metadata'] = False
            print "Not producing inline metadata"
        if '--no-rdf' in sys.argv :
            flags['produce_rdf'] = False
            print "Not producing an RDF graph"
        if '--no-graph' in sys.argv :
            flags['produce_graph'] = False
            print "Not producing a citation graph"
        if '--no-full-graph' in sys.argv :
            flags['produce_full_graph'] = False
            print "Not producing a full citation graph for all converted files"
        if '--no-report' in sys.argv :
            flags['produce_report'] = False
            print "Not producing a report"
        if '--skip-if-existing' in sys.argv :
            flags['skip_if_existing'] = True
            print "Skipping if MetaLex XML already exists"
        if '--no-update' in sys.argv :
            flags['no_update'] = True
            print "Skipping if any XML version of BWB document already exists"
            
        
        if '--data-dir' in sys.argv :
            flags['data_dir'] = sys.argv[sys.argv.index('--data-dir')+1]
            print "Data directory set to: {0}".format(flags['data_dir'])
        if '--out-dir' in sys.argv :
            flags['out_dir'] = sys.argv[sys.argv.index('--out-dir')+1]
            print "Output directory set to: {0}".format(flags['out_dir'])
        if '--report-file' in sys.argv :
            flags['report_file'] = sys.argv[sys.argv.index('--report-file')+1]
            print "Report file set to: {0}".format(flags['report_file'])
        if '--graph-file' in sys.argv :
            flags['graph_file'] = sys.argv[sys.argv.index('--graph-file')+1]
            print "Graph file set to: {0}".format(flags['graph_file'])
            
        if '--rdf-upload-url' in sys.argv :
            flags['rdf_upload_url'] = sys.argv[sys.argv.index('--rdf-upload-url')+1]
            print "Will upload RDF to: {0}".format(flags['rdf_upload_url'])
            
            if '-user' in sys.argv and '-pass' in sys.argv :
                flags['user'] = sys.argv[sys.argv.index('-user')+1]
                flags['pass'] = sys.argv[sys.argv.index('-pass')+1]
        
        
        if '--pickle' in sys.argv :
            pickle_file = sys.argv[sys.argv.index('--pickle')+1]
            print "Pickle source: {0}\n".format(pickle_file)
            id_list_file = open(pickle_file, 'r')
            bwbid_dict = pickle.load(id_list_file)
            id_list_file.close()
            convertAll(bwbid_dict, flags)
        elif '--bwbid' in sys.argv :
            bwbid = sys.argv[sys.argv.index('--bwbid')+1]
            print "BWB Document: {0}\n".format(bwbid)
            bwbid_dict = {}
            bwbid_dict[bwbid] = ''
            convertAll(bwbid_dict, flags)
        elif '--all' in sys.argv :
            print "Will proceed to process *all* sources from http://www.wetten.nl.\n"
            pickle_file = 'pickles/bwbid_list.pickle'
            print "Pickle source: {0}\n".format(pickle_file)
            id_list_file = open(pickle_file, 'r')
            bwbid_dict = pickle.load(id_list_file)
            id_list_file.close()
            convertAll(bwbid_dict,flags)
    else :
        print """BWB Converter v0.1a 
Copyright (c) 2011, Rinke Hoekstra, Universiteit van Amsterdam
Licensed under the LGPL v3 (see http://www.gnu.org/licenses/lgpl-3.0.txt)
        

        Usage:
        python convert_bwb.py [--pickle <file>|--bwbid <id>|--all] [conversion flags]
        
        Command line options:
        --pickle <file>         Load list of BWB identifiers from specified pickle file
        --bwbid <id>            Only convert document with specified BWB identifier
        --all                   Convert all known documents in wetten.nl
        
        Conversion flags
        --no-inline-metadata    Do not produce inline metadata inside CEN MetaLex documents (will save a lot of space)
        --no-rdf                Do not produce a Turtle RDF file for metadata generated by the conversion
        --no-graph              Do not produce a citation graph
        --no-full-graph         Do not produce a full graph for the entire conversion
        --no-report             Do not produce a conversion report
        
        --skip-if-existing      Skip conversion if MetaLex XML file already exists.
        --no-update             Skip conversion if some BWB XML version of the file already exists locally (useful for debugging)
        
        --data-dir <dir>        Location of locally available files for the conversion, default is '../data/'
        --out-dir <dir>         Location for target files of the conversion, default is '../out'
        --graph-file <file>     Output citation graph to specified file, default is '../out/full_graph.net'
        --report-file <file>    Output conversion report to specified file
        
        --rdf-upload-url <url>  Sesame compliant RDF upload URL
        -user                   Username for RDF upload (if required)
        -pass                   Password for RDF upload (if required)
        """
