# -*- coding: utf-8 -*-
"""
Created on Thu Apr 23 16:52:03 2020

Author: linzhu
"""
import os
import sys 
sys.path.append('../base/')
from DATImage import DATImage


def getListOfFiles(dirName):
    '''
    For the given path, get the List of all files in the directory tree 
    '''
    # create a list of file and sub directories 
    # names in the given directory 
    listOfFile = os.listdir(dirName)
    allFiles = list()
    # Iterate over all the entries
    for entry in listOfFile:
        # Create full path
        fullPath = os.path.join(dirName, entry)
        # If entry is a directory then get the list of files in this directory 
        if os.path.isdir(fullPath):
            allFiles = allFiles + getListOfFiles(fullPath)
        else:
            allFiles.append(fullPath) 
    allFiles = [fileName.replace('\\','/') for fileName in allFiles]           
    return allFiles

def extractMetaData(file, metadata, keys='all'):
    if keys == 'all':
        keys = metadata.keys()        
    with open(file,'w') as f:
        # time stamp and file header
        f.write('Time Stamp:\t{}\n'.format(
                  metadata['timestamp'].strftime("%Y-%m-%d %H:%M:%S")))
        for key in keys:
            if type(metadata[key]) is int:
                f.write('{:<18}\t{:g}\n'.format(key+':', metadata[key]))
            elif type(metadata[key]) is list:
                if len(metadata[key]) == 1:
                    f.write('{:<18}\t{:g}\n'.format(key+':', metadata[key]))
                elif len(metadata[key]) == 2:
                    f.write('{:<18}\t{:g} {}\n'.format(key+':', metadata[key][0], metadata[key][1]))
                else:
                    pass
                
        

if __name__ == '__main__':
    keys = []
    dirName = '../testfiles'
    # Get the list of all files in directory tree at given path
    listOfFiles = getListOfFiles(dirName)
    #file = '../testfiles/LEED.dat'
    for file in listOfFiles:
        file_log = file[:-3]+'txt'
        im = DATImage(file)
        extractMetaData(file_log, im.metadata)