#!/usr/bin/env python
from subprocess import Popen, PIPE, STDOUT
import os
import errno

__author__ = 'adamkoziol,mikeknowles'


def make_path(inpath):
    """
    from: http://stackoverflow.com/questions/273192/check-if-a-directory-exists-and-create-it-if-necessary \
    does what is indicated by the URL
    :param inpath: string of the supplied path
    """
    try:
        # os.makedirs makes parental folders as required
        os.makedirs(inpath)
    # Except os errors
    except OSError as exception:
        # If the os error is anything but directory exists, then raise
        if exception.errno != errno.EEXIST:
            raise


def get_version(exe):
    """
    :param exe: :type list required
    """
    assert isinstance(exe, list)
    return Popen(exe, stdout=PIPE, stderr=STDOUT).stdout.read()


def make_dict():
    """Makes Perl-style dictionaries"""
    from collections import defaultdict
    return defaultdict(make_dict)


def printtime(string, start):
    """Prints a string in bold with the elapsed time
    :param string: a string to be printed in bold
    :param start: integer of the starting time
    """
    import time
    m, s = divmod(time.time() - start, 60)
    h, m = divmod(m, 60)
    strtime = "{0:0.0f}hr {1:0.0f}m {2:0.03f}s".format(h, m, s) if h else "{0:0.0f}m {1:0.03f}s".format(m, s)
    print('\n\033[1m' + "[Elapsed Time: {}] {}".format(strtime, string) + '\033[0m')


# Initialise globalcount
globalcount = 0


def dotter():
    """Prints formatted time to stdout at the start of a line, as well as a "."
    whenever the length of the line is equal or lesser than 80 "." long"""
    import time
    import sys
    # Use a global variable
    global globalcount
    if globalcount <= 80:
        sys.stdout.write('.')
        globalcount += 1
    else:
        sys.stdout.write('\n[{0:s}] .'.format(time.strftime("%H:%M:%S")))
        globalcount = 1


def execute(command, outfile="", **kwargs):
    """
    Allows for dots to be printed to the terminal while waiting for a long system call to run
    :param command: the command to be executed
    :param outfile: optional string of an output file
    from https://stackoverflow.com/questions/4417546/constantly-print-subprocess-output-while-process-is-running
    """
    import sys
    import time
    # Initialise count
    count = 0
    # Initialise the starting time
    start = int(time.time())
    maxtime = 0
    # Removing Shell=True to prevent excess memory use thus shlex split if needed
    if type(command) is not list and "shell" not in kwargs:
        import shlex
        command = shlex.split(command)
    # Run the commands - direct stdout to PIPE and stderr to stdout
    # DO NOT USE subprocess.PIPE if not writing it!
    if outfile:
        process = Popen(command, stdout=PIPE, stderr=STDOUT, **kwargs)
    else:
        devnull = open(os.devnull, 'wb')
        process = Popen(command, stdout=devnull, stderr=STDOUT, **kwargs)
    # Write the initial time
    sys.stdout.write('[{:}] '.format(time.strftime('%H:%M:%S')))
    # Create the output file - if not provided, then nothing should happen
    writeout = open(outfile, "ab+") if outfile else ""
    # Poll process for new output until finished
    while True:
        # If an output file name is provided
        if outfile:
            # Get stdout into a variable
            nextline = process.stdout.readline()
            # Print stdout to the file
            writeout.write(nextline)
        # Break from the loop if the command is finished
        if process.poll() is not None:
            break
        # Adding sleep commands slowed down this method when there was lots of output. Difference between the start time
        # of the analysis and the current time. Action on each second passed
        currenttime = int(time.time())
        if currenttime - start > maxtime:
            # Set the max time for each iteration
            maxtime = currenttime - start
            # Print up to 80 dots on a line, with a one second delay between each dot
            if count <= 80:
                sys.stdout.write('.')
                count += 1
            # Once there are 80 dots on a line, start a new line with the the time
            else:
                sys.stdout.write('\n[{:}] .'.format(time.strftime('%H:%M:%S')))
                count = 1
    # Close the output file
    writeout.close() if outfile else ""
    sys.stdout.write('\n')


def filer(filelist, extension='fastq'):
    """
    Helper script that creates a set of the stain names created by stripping off parts of the filename.
    Hopefully handles different naming conventions (e.g. 2015-SEQ-001_S1_L001_R1_001.fastq(.gz),
    2015-SEQ-001_R1_001.fastq.gz, 2015-SEQ-001_R1.fastq.gz, 2015-SEQ-001_1.fastq.gz, and 2015-SEQ-001_1.fastq.gz
    all become 2015-SEQ-001)
    :param filelist: List of files to parse
    :param extension: the file extension to use. Default value is 'fastq
    """
    import re
    # Initialise the set
    fileset = set()
    for seqfile in filelist:
        # Search for the conventional motifs present following strain names
        # _S\d+_L001_R\d_001.fastq(.gz) is a typical unprocessed Illumina fastq file
        if re.search("_S\d+_L001", seqfile):
            fileset.add(re.split("_S\d+_L001", seqfile)[0])
        # Files with _R\d_001.fastq(.gz) are created in the SPAdes assembly pipeline
        elif re.search("_R\d_001", seqfile):
            fileset.add(re.split("_R\d_001", seqfile)[0])
        # _R\d.fastq(.gz) represents a simple naming scheme for paired end reads
        elif re.search("R\d.{}".format(extension), seqfile):
            fileset.add(re.split("_R\d.{}".format(extension), seqfile)[0])
        # _\d.fastq is always possible
        elif re.search("[-_]\d.{}".format(extension), seqfile):
            fileset.add(re.split("[-_]\d.{}".format(extension), seqfile)[0])
        # .fastq is the last option
        else:
            fileset.add(re.split(".{}".format(extension), seqfile)[0])
        dotter()
    return fileset


def relativesymlink(src_file, dest_file):
    ret = get_version(['ln', '-s', '-r', src_file, dest_file])
    if ret and 'File exists' not in ret:
        raise Exception(ret)


class GenObject(object):
    """Object to store static variables"""

    def __init__(self, x=None):
        start = x if x else {}
        # start = (lambda y: y if y else {})(x)
        super(GenObject, self).__setattr__('datastore', start)

    def __getattr__(self, key):
        return self.datastore[key]

    def __setattr__(self, key, value):
        if value:
            self.datastore[key] = value
        else:
            self.datastore[key] = "NA"

    def __iter__(self):
        for key in self.datastore:
            value = getattr(self, key)
            if isinstance(value, (list, dict, tuple)):
                yield (key, getattr(self, key))
            else:
                yield (key, str(getattr(self, key)))


class MetadataObject(object):
    """Object to store static variables"""

    def __init__(self):
        """Create datastore attr with empty dict"""
        super(MetadataObject, self).__setattr__('datastore', {})

    def __getattr__(self, key):
        """:key is retrieved from datastore if exists, for nested attr recursively :self.__setattr__
        May need some improvement not include builtin methods"""
        if key not in self.datastore and key != "keys":
            self.__setattr__(key, value=GenObject())
        return self.datastore[key]

    def __setattr__(self, key, value, **args):
        """Add :value to :key in datastore or create GenObject for nested attr"""
        if args:
            self.datastore[key].value = args
        else:
            self.datastore[key] = value

    def __iter__(self):
        """Prints only the nested dictionary values; removes __methods__ and __members__ attributes"""
        for attr in self.datastore:
            if not attr.startswith('__'):
                value = getattr(self, attr)
                if isinstance(value, (basestring, int, float, bool, long)):
                    yield (attr, value)
                elif not isinstance(value, (MetadataObject, GenObject, type)):
                    if any(isinstance(x, (MetadataObject, GenObject, type)) for x in value):
                        yield (attr, [dict(v) for v in value])
                    elif isinstance(value, dict):
                        if any(isinstance(value[x], (MetadataObject, GenObject, type)) for x in value):
                            yield (attr, dict((v, dict(value[v])) for v in value))
                        else:
                            yield (attr, value)
                    else:
                        yield (attr, value)
                else:
                    try:
                        yield (attr, dict(value))
                    except TypeError:
                        print attr, value


def logstr(*args):
    yield "{}\n".__add__("-".__mul__(60).__add__("\n")).__mul__(len(args)).format(*args)


def which(cmd, mode=os.F_OK | os.X_OK, path=None):
    """Given a command, mode, and a PATH string, return the path which
    conforms to the given mode on the PATH, or None if there is no such
    file.

    :param cmd: str
    :param mode defaults to os.F_OK | os.X_OK.
    :param path defaults to the result
    of os.environ.get("PATH"), or can be overridden with a custom search
    path.

    """
    # Check that a given file can be accessed with the correct mode.
    # Additionally check that `file` is not a directory, as on Windows
    # directories pass the os.access check.
    import sys

    def _access_check(fn, mode):
        return os.path.exists(fn) and os.access(fn, mode) and not os.path.isdir(fn)

    # If we're given a path with a directory part, look it up directly rather
    # than referring to PATH directories. This includes checking relative to the
    # current directory, e.g. ./script
    if os.path.dirname(cmd):
        if _access_check(cmd, mode):
            return cmd
        return None

    if path is None:
        path = os.environ.get("PATH", os.defpath)
    if not path:
        return None
    path = path.split(os.pathsep)

    if sys.platform == "win32":
        # The current directory takes precedence on Windows.
        if not os.curdir in path:
            path.insert(0, os.curdir)

        # PATHEXT is necessary to check on Windows.
        pathext = os.environ.get("PATHEXT", "").split(os.pathsep)
        # See if the given file matches any of the expected path extensions.
        # This will allow us to short circuit when given "python.exe".
        # If it does match, only test that one, otherwise we have to try
        # others.
        if any(cmd.lower().endswith(ext.lower()) for ext in pathext):
            files = [cmd]
        else:
            files = [cmd + ext for ext in pathext]
    else:
        # On other platforms you don't have things like PATHEXT to tell you
        # what file suffixes are executable, so just pass on cmd as-is.
        files = [cmd]

    seen = set()
    for dir in path:
        normdir = os.path.normcase(dir)
        if normdir not in seen:
            seen.add(normdir)
            for thefile in files:
                name = os.path.join(dir, thefile)
                if _access_check(name, mode):
                    return name
    return None
