#!/usr/bin/env python
import subprocess
import os
import metadataReader

__author__ = 'adamkoziol,mikeknowles'


class Basic(object):
    def basic(self):
        from accessoryFunctions import GenObject, MetadataObject, filer, make_path
        from glob import glob
        import os
        import errno
        # Grab any .fastq files in the path
        fastqfiles = glob('{}*.fastq*'.format(self.path))
        # Extract the base name of the globbed name + path provided
        fastqnames = map(lambda x: os.path.split(x)[1], filer(fastqfiles))
        # Iterate through the names of the fastq files
        for fastqname in sorted(fastqnames):
            # Set the name
            metadata = MetadataObject()
            metadata.name = fastqname
            # Set the destination folder
            outputdir = '{}{}'.format(self.path, fastqname)
            # Make the destination folder
            make_path(outputdir)
            # Get the fastq files specific to the fastqname
            specificfastq = glob('{}{}*.fastq*'.format(self.path, fastqname))
            # Link the files to the output folder
            try:
                # Link the .gz files to :self.path/:filename
                map(lambda x: os.symlink(x, '{}/{}'.format(outputdir, os.path.split(x)[1])), specificfastq)
            # Except os errors
            except OSError as exception:
                # If there is an exception other than the file exists, raise it
                if exception.errno != errno.EEXIST:
                    raise
            # Initialise the general category
            metadata.general = GenObject()
            # Populate the .fastqfiles category of :self.metadata
            metadata.general.fastqfiles = [fastq for fastq in glob('{}/{}*.fastq*'.format(outputdir, fastqname))
                                           if 'trimmed' not in fastq]
            # Add the output directory to the metadata
            metadata.general.outputdirectory = outputdir
            # Append the metadata to the list of samples
            self.samples.append(metadata)
        # Grab metadata from previous runs
        metadata = metadataReader.MetadataReader(self)
        # Update self.samples
        self.samples = metadata.samples
        self.readlength()

    def readlength(self):
        """Calculates the read length of the fastq files. Short reads will not be able to be assembled properly with the
        default parameters used for spades."""
        from accessoryFunctions import GenObject
        # Iterate through the samples
        for sample in self.samples:
            # Only perform this step if the forward and reverse lengths have not been loaded into the metadata
            if not sample.run.forwardlength and not sample.run.reverselength:
                # Initialise the .header attribute for each sample
                sample.header = GenObject()
                sample.commands = GenObject()
                # Set /dev/null
                devnull = open(os.devnull, 'wb')
                # Only process the samples if the file type is a list
                if type(sample.general.fastqfiles) is list:
                    # Set the forward fastq to be the first entry in the list
                    forwardfastq = sample.general.fastqfiles[0]
                    # If the files are gzipped, then zcat must be used instead of cat
                    if '.gz' in forwardfastq:
                        command = 'zcat'
                    else:
                        command = 'cat'
                    # Read in the output of the (z)cat of the fastq file piped through head to read only the first 1000
                    # lines. Will make a string of the first 1000 lines in the file
                    forwardreads = subprocess.Popen("{} {} | head -n 1000".format(command, forwardfastq),
                                                    shell=True,
                                                    stdout=subprocess.PIPE,
                                                    stderr=devnull).communicate()[0].rstrip()
                    # Set the length of the reads as follows: the highest value (max) of the length of the sequence. The
                    # sequence was extracted from the rest of the lines in the fastq file. Example of first four lines:
                    """
                    @M02466:126:000000000-AKF4P:1:1101:11875:1838 1:N:0:1
                    TCATAACGCAGTGAAACGCTTTAACAAAAGCGGAGACACGCCACTATTTGTCAATATTTCGTATGATACATTTTTAGAAAATCAAGAAGAGTTGCACGA
                    +
                    AA,B89C,@++B,,,,C,:BFF9,C,,,,,6+++++:,C,8C+BE,EFF9FC,6E,EFGF@F<F@9F9E<FFGGGC8,,,,CC<,,,,,,6CE,C<C,,
                    """
                    # The line with the sequence information occurs every four lines (1, 5, 9, etc). This can be
                    # represented by linenumber % 4 == 1
                    forwardlength = max([len(sequence) for iterator, sequence in enumerate(forwardreads.split('\n'))
                                         if iterator % 4 == 1])
                    sample.run.forwardlength = forwardlength
                    # For paired end analyses, also calculate the length of the reverse reads
                    if len(sample.general.fastqfiles) == 2:
                        reversefastq = sample.general.fastqfiles[1]
                        reversereads = subprocess.Popen("{} {} | head -n 1000".format(command, reversefastq),
                                                        shell=True,
                                                        stdout=subprocess.PIPE,
                                                        stderr=devnull).communicate()[0].rstrip()
                        sample.run.reverselength = max([len(sequence) for iterator, sequence in
                                                        enumerate(reversereads.split('\n')) if iterator % 4 == 1])
                    # Populate metadata of single end reads with 'NA'
                    else:
                        sample.header.reverselength = 'NA'

    def __init__(self, inputobject):
        self.samples = []
        self.path = inputobject.path
        self.kmers = inputobject.kmers
        self.basic()
