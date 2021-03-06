#!/usr/bin/env python
__author__ = 'adamkoziol,mikeknowles'


class MetadataPrinter(object):
    def printmetadata(self):
        import json
        import sys
        import os
        # Iterate through each sample in the analysis
        for sample in self.metadata:
            if type(sample.general.fastqfiles) is list:
                sample.software.python = sys.version
                sample.software.arch = ", ".join(os.uname())
                # Set the name of the json file
                jsonfile = '{}/{}_metadata.json'.format(sample.general.outputdirectory, sample.name)
                # Open the metadata file to write
                with open(jsonfile, 'wb') as metadatafile:
                    # Write the json dump of the object dump to the metadata file
                    json.dump(dict(sample), metadatafile, sort_keys=True, indent=4, separators=(',', ': '))

    def __init__(self, inputobject):
        self.metadata = inputobject.runmetadata.samples
        self.printmetadata()
