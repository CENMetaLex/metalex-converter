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

@summary: This module defines a utility script for adding records to a pickle file
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
