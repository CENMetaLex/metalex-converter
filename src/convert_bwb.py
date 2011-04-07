from BeautifulSoup import BeautifulSoup
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



def getVersion(bwbid):
    uri = 'http://wetten.overheid.nl/{0}/informatie'.format(bwbid)

    info = urllib2.urlopen(uri)
    html = info.read()
    soup = BeautifulSoup(html)
    table_rows = soup.findAll("tr")
    for row in table_rows :
        # print row
        match = re.search(r'<tr.*?><td.*?><p><b>(\d\d)-(\d\d)-(\d\d\d\d)', str(row))
        if match :
            return "{0}-{1}-{2}".format(match.group(3), match.group(2), match.group(1))

    return str(date.today())

def convert(bwbid, flags):
    cite_graph = flags['cite_graph']
    reports = flags['reports']
    data_dir = flags['data_dir']
    
    
    print "Starting conversion for {0} ...".format(bwbid)

    print "Getting version date from info URL..."
    date_version = getVersion(bwbid)
    print "Latest version date: {0}".format(date_version)
    print "... done"

    source_doc_filename = '{0}{1}_{2}.xml'.format(data_dir, bwbid, date_version)
    target_doc_filename = '{0}{1}_{2}_ml.xml'.format(data_dir, bwbid, date_version)
    target_rdf_filename = '{0}{1}_{2}.n3'.format(data_dir, bwbid, date_version)
    target_net_filename = '{0}{1}_{2}.net'.format(data_dir, bwbid, date_version)

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

    ml_converter = MetaLexConverter(bwbid, doc, date_version, flags)

    # Handle the regulation...
    print "Starting conversion..."
    ml_converter.handleRoot()
    print "... done"

    print "Storing output to files ..."
    # print ml_converter.printXML()
    print "Writing {0}".format(target_doc_filename)
    ml_converter.writeXML(target_doc_filename)
    
    if flags['produce_rdf'] :
        print "Writing {0}".format(target_rdf_filename)
        ml_converter.writeRDF(target_rdf_filename, 'turtle')
        
    if flags['produce_graph'] :
        print "Writing {0}".format(target_net_filename)
        ml_converter.writeGraph(target_net_filename, 'pajek')

    print "... done"

    if cite_graph != None and flags['produce_graph'] :
        print "Appending citegraph ..."
        cite_graph.append(ml_converter.cg)
        print "... done"

    # Append conversion report
    reports.append(ml_converter.report.getReport())

    print "... done converting {0}".format(bwbid)

    # Make sure to delete the ml_converter, to save up on garbage collection
    del ml_converter
    del doc


def convertAll(bwbid_dict, flags):
    try :
        total = len(bwbid_dict)
        count = 0

        cg = CiteGraph()

        reports = []
        profile = Profile('./converter/bwb-mapping.txt')
        
        flags['cite_graph': cg]
        flags['reports': reports]
        flags['profile': profile]

        for bwbid in bwbid_dict :
            count += 1
            print "\n------\nProcessing {0}/{1} ({2}%)\n------\n".format(count, total, (float(count) / float(total)) * 100)
            try :
                convert(bwbid, flags)
            except KeyboardInterrupt:
                print "Conversion Aborted on document ID: {0}".format(bwbid)
                break

        if flags['produce_graph'] :
            print "Writing full graph to file ..."
            target_file = open(flags['graph_file'], 'w')
            target_file.write(cg.writePajek())
            target_file.close()
            print "... done"

        processReports(reports, profile)

        print "\n------\nDONE\n------\n"

    except IOError as (errno, strerror):
        print "I/O error({0}): {1}".format(errno, strerror)



def processReports(reports, profile):
    reportwriter = csv.writer(open('report.csv', 'w'))

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
        flags = {'inline_metadata': True, 'produce_rdf': True, 'produce_graph': True, 'produce_report': True, 'report_file': 'out.csv', 'data_dir': '../data/', 'graph_file': '../out/full_graph.net'}

        
        if '--no-inline-metadata' in sys.argv :
            flags['inline_metadata'] = False
        if '--no-rdf' in sys.argv :
            flags['produce_rdf'] = False
        if '--no-graph' in sys.argv :
            flags['produce_graph'] = False
        if '--no-report' in sys.argv :
            flags['produce_report'] = False
            
        if '--data-dir' in sys.argv :
            flags['data_dir'] = sys.argv[sys.argv.index('--data-dir')+1]
        if '--report-file' in sys.argv :
            flags['report_file'] = sys.argv[sys.argv.index('--report-file')+1]
        if '--graph-file' in sys.argv :
            flags['graph_file'] = sys.argv[sys.argv.index('--graph-file')+1]
        
        
        if '--pickle' in sys.argv :
            pickle = sys.argv[sys.argv.index('--pickle')+1]
            print "Pickle source: {0}\n".format(pickle)
            id_list_file = open(pickle, 'r')
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
            convertAll('pickles/bwbid_list.pickle',flags)
    else :
        print """BWB Converter v0.1a 
Copyright (c) 2011, Rinke Hoekstra, Universiteit van Amsterdam
Licenced under the LGPL v3 (see http://www.gnu.org/licenses/lgpl-3.0.txt)
        

        Usage:
        python convert_bwb.py [--pickle <file>|--bwbid <id>|--all] [--no-inline-metadata] [--no-rdf] [--no-graph] [--no-report] [--data-dir <dir>] [--graph-file <file>] [--report-file <file>]
        
        Command line options:
        --pickle <file>       Load list of BWB identifiers from specified pickle file
        --bwbid <id>          Only convert document with specified BWB identifier
        --all                 Convert all known documents in wetten.nl
        
        Conversion flags
        --no-inline-metadata  Do not produce inline metadata inside CEN MetaLex documents (will save a lot of space)
        --no-rdf              Do not produce a Turtle RDF file for metadata generated by the conversion
        --no-graph            Do not produce a citation graph
        --no-report           Do not produce a conversion report
        
        --data-dir <dir>      Location of source and target files for the conversion, default is '../data/'
        --graph-file <file>   Output citation graph to specified file, default is '../out/full_graph.net'
        --report-file <file>  Output conversion report to specified file
        """
