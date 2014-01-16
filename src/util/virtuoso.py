import logging
import os
import subprocess
import glob
import argparse
import re

def load_files(mask, password='dba', format='turtle'):
    
    for filename in glob.glob(mask):
        logging.info('Loading {}'.format(filename))
        load_file(os.path.abspath(filename), password=password, format=format)
    
def load_file(filename, password='dba', format='turtle'):
    logging.debug("Loading into Virtuoso using 'isql-v'")

    m = re.search(r'(?P<bwbid>BWB\w\d+)_(?P<date>\d\d\d\d-\d\d-\d\d)',filename)
    
    graph_uri = "http://doc.metalex.eu/id/{}/{}".format(m.group('bwbid'),m.group('date'))


    if format == 'turtle':
        method = 'DB.DBA.TTLP_MT'
    elif format == 'RDF/XML':
        method = 'RDF_LOAD_RDFXML_MT' 
    else :
        logging.error("Upload format not supported!")
        return

    command = 'echo "{} (file_to_string_output(\'{}\'),\'\',\'{}\');" | isql-v -U dba -P {}'.format(method, filename, graph_uri, password )

    try :
        logging.debug(command)
        out = subprocess.check_output(command)
        logging.info(out)
    except Exception as e:
        logging.error("Could not load file into virtuoso")
    
    try :
        command = 'echo "checkpoint;" | isql-v -U dba -P {}'.format(password)
        logging.debug(command)
        out = subprocess.check_output(command)
        logging.info(out)
    except Exception as e :
        logging.error("Could not create checkpoint")
    
    
if __name__ == '__main__':
    
    logging.setlevel(logging.DEBUG)
    
    parser = argparse.ArgumentParser(description='Bulk load files into Virtuoso')
    parser.add_argument('mask', help='File mask')
    parser.add_argument('-p', '--password', type=str, default='dba', help='Password of the "dba" user in Virtuoso')
    parser.add_argument('-f', '--format', type=str, default='turtle', help='Format of the file, may be "turtle" or "RDF/XML"')
    args = parser.parse_args()
    
    load_files(args.mask, password=args.password, format=args.format)
    