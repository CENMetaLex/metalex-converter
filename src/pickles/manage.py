'''
Created on 31 Mar 2011

@author: hoekstra
'''
import pickle
import sys


if __name__ == '__main__':
    if len(sys.argv) > 2 :
        print "Adding {0} to {1}".format(sys.argv[2],sys.argv[3])
        pickle_file = file(sys.argv[1],'rw')
        list = pickle.load(pickle_file)
        list[sys.argv[2]] = sys.argv[3]
        pickle.dump(list,pickle_file)
        pickle_file.close()
        print "Done..."
    else :
        print "No pickle operation specified on command line\n"
