'''
Created on 29 Jun 2011

@author: hoekstra
'''


import pickle
import urllib2
import zipfile
import StringIO
from datetime import date
import logging
from xml.etree.ElementTree import ElementTree, register_namespace
from glob import glob


    



class BWBTree():
    
    bwbid_list = {}
    
    def __init__(self):
        bwbidlist_filename = 'BWBIdList.xml'
#        bwbidlist_filename = 'bwbidlist_test.xml'
        bwbidlist_url = 'http://wetten.overheid.nl/BWBIdService/BWBIdList.xml.zip'
        pickle_filename = 'pickles/bwbid_list_{0}.pickle'.format(date.today())
        
        if glob(pickle_filename) :
            logging.info("Today's BWB ID list dictionary pickle already exists, loading directly from pickle  ...")
            self.bwbid_list = pickle.load(open(pickle_filename, 'r'))
            return
        
        logging.info("Loading zipped BWB ID list from {0}.".format(bwbidlist_url))
        response = urllib2.urlopen(bwbidlist_url)
        bwbidlist_zipped_string = response.read()
        bwbidlist_zipped_file = StringIO.StringIO(bwbidlist_zipped_string)
        bwbidlist_zip = zipfile.ZipFile(bwbidlist_zipped_file)
        logging.info("Unzipping BWB ID list to {0}.".format(bwbidlist_filename))
        bwbidlist_zip.extract(bwbidlist_filename)
        
        logging.info("Checking validity of BWB ID list in {0}".format(bwbidlist_filename))
        
        bwbidlist_checked_filename = self.checkBWBXML(bwbidlist_filename)
        
        logging.info("Loading and parsing BWB ID list from {0}.".format(bwbidlist_checked_filename))
        
        register_namespace('','http://schemas.overheid.nl/bwbidservice')
        tree = ElementTree()
        tree.parse(bwbidlist_checked_filename)
        
        
        self.pickFromTree(tree)
        
#        pprint(self.bwbid_list)
        
        logging.info("Dumping BWB ID list dictionary to {0}.".format(pickle_filename))
        outfile = open(pickle_filename, 'w')
        pickle.dump(self.bwbid_list,outfile)
        
    def checkBWBXML(self, bwbidlist_filename):
        bwbidlist_checked_filename = 'checked_{0}'.format(bwbidlist_filename)
        bwbidlist_file = open(bwbidlist_filename,'r')
        bwbidlist_checked_file = open(bwbidlist_checked_filename,'w')
        
        firstline = bwbidlist_file.next()
        bwbidlist_checked_file.write(firstline)
        for line in bwbidlist_file :
            if '<?xml' in line :
                logging.error("ERROR: Found superfluous XML processing instruction in BWB ID list, returning only first part.")
                before, match, after = line.partition('<?xml')
                bwbidlist_checked_file.write(before)
                bwbidlist_checked_file.close()
                return bwbidlist_checked_filename
            else :
                bwbidlist_checked_file.write(line)
        
        logging.info("No problems found in BWB ID list XML...")
        bwbidlist_checked_file.close()
        return bwbidlist_checked_filename
    
    def pickFromTree(self, tree):
#        print tostring(tree.getroot())
        logging.info("BWB ID list was generated on "+ tree.getroot().find('{http://schemas.overheid.nl/bwbidservice}GegenereerdOp').text)
        
        regeling_infos = tree.getroot().findall('.//{http://schemas.overheid.nl/bwbidservice}RegelingInfo')
        for ri in regeling_infos:
            bwbid = ri.find('{http://schemas.overheid.nl/bwbidservice}BWBId')
#            print bwbid.text
            datum_laatste = ri.find('{http://schemas.overheid.nl/bwbidservice}DatumLaatsteWijziging')
            datum_verval = ri.find('{http://schemas.overheid.nl/bwbidservice}VervalDatum')
#            datum_iwtr = ri.find('{http://schemas.overheid.nl/bwbidservice}InwerkingtredingsDatum').text
            titel_officieel = ri.find('{http://schemas.overheid.nl/bwbidservice}OfficieleTitel')
            soort = ri.find('{http://schemas.overheid.nl/bwbidservice}RegelingSoort')
            
            citeertitel_lijst = ri.find('{http://schemas.overheid.nl/bwbidservice}CiteertitelLijst')
            ct_list = []
            if citeertitel_lijst is not None:
                for ct in citeertitel_lijst:
                    titel_citeer = ct.find('{http://schemas.overheid.nl/bwbidservice}titel')
                    titel_citeer_status = ct.find('{http://schemas.overheid.nl/bwbidservice}status')
                    titel_citeer_iwtr = ct.find('{http://schemas.overheid.nl/bwbidservice}InwerkingtredingsDatum')
                    if titel_citeer_iwtr is not None :
                        ct_list.append({'titel': titel_citeer.text, 'status': titel_citeer_status.text, 'iwtr': titel_citeer_iwtr.text})
                    else :
                        ct_list.append({'titel': titel_citeer.text, 'status': titel_citeer_status.text, 'iwtr': None})
    
            afkorting_lijst = ri.find('{http://schemas.overheid.nl/bwbidservice}AfkortingLijst')
            ak_list = []
            if afkorting_lijst is not None :
                afkortingen = afkorting_lijst.findall('{http://schemas.overheid.nl/bwbidservice}Afkorting')
                for titel_afkorting in afkortingen:
                    ak_list.append({'afkorting': titel_afkorting.text})
            
            niet_officiele_titel_lijst = ri.find('{http://schemas.overheid.nl/bwbidservice}NietOfficieleTitelLijst')
            not_list = []
            if niet_officiele_titel_lijst is not None :
                not_titels = niet_officiele_titel_lijst.findall('{http://schemas.overheid.nl/bwbidservice}NietOfficieleTitel')
                for titel_niet_officieel in not_titels:
                    not_list.append({'titel': titel_niet_officieel.text})
     
            bwbid_dict = {}
            bwbid_dict['laatste'] = datum_laatste.text
            if datum_verval is not None :
                bwbid_dict['verval'] = datum_verval.text
            else :
                bwbid_dict['verval'] = None
            if titel_officieel is not None:
                bwbid_dict['titel'] = titel_officieel.text
            else :
                bwbid_dict['titel'] = ''
            bwbid_dict['soort'] = soort.text
            bwbid_dict['afkortingen'] = ak_list
            bwbid_dict['citeertitels'] = ct_list
            bwbid_dict['no_titels'] = not_list 
            
            self.bwbid_list[bwbid.text] = bwbid_dict
            
    def getBWBIds(self):
        return self.bwbid_list

if __name__ == '__main__':
    bwbsoup = BWBTree()


