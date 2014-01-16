import logging
import os
import subprocess
import glob
import argparse

def load_files(mask, password='dba', format='turtle'):
    
    for filename in glob.glob(path):
        logging.info('Loading {}'.format(filename))
        load_file(password, os.path.abspath(filename))
    
def load_file(filename, password='dba', format='turtle'):
    logging.debug("Loading into Virtuoso using 'isql-v'")

    if format == 'turtle':
        method = 'DB.DBA.TTLP_MT'
    elif format == 'RDF/XML':
        method = 'RDF_LOAD_RDFXML_MT' 
    else :
        logging.error("Upload format not supported!")
        return

    command = 'echo "{} (file_to_string_output(\'{}\'),\'\',\'{}\');" | isql-v -U dba -P {}'.format(method, absolute_filename, self.rdf_graph_uri, password )

    try :
        out = subprocess.check_output(command)
        logging.info(out)
    except Exception as e:
        logging.error("Could not load file into virtuoso")
    
    try :
        command = 'echo "checkpoint;" | isql-v -U dba -P {}'.format(password)
        out = subprocess.check_output(command)
        logging.info(out)
    except Exception as e :
        logging.error("Could not create checkpoint")
    
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Bulk load files into Virtuoso')
    parser.add_argument('mask', help='File mask')
    parser.add_argument('-p', '--password', type=str, default='dba', help='Password of the "dba" user in Virtuoso')
    parser.add_argument('-f', '--format', type=str, default='turtle', help='Format of the file, may be "turtle" or "RDF/XML"')
    args = parser.parse_args()
    
    load_files(args.mask, args.password, args.format)
    