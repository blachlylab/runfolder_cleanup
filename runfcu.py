# illumina run folder cleanup
# Copyright (c) 2017 James S Blachly MD and THe Ohio State University
# MIT licensed
# SEE LICENSE file 

import os
import sys
import glob
import argparse
import shutil

# Typical layout of MiSeqOutput/<runfolder>/
# Config/
# Data/
# InterOp/
# Logs/
# Recipe/
# Thumbnail_Images/

# Layout of Data/
datatree_comment = """
Data
├── Intensities
│   ├── BaseCalls (fastq.gz files here)
│   │   ├── Alignment (BAM files, if present, here)
│   │   │   └── Logging
│   │   ├── L001 (control, filter files)
│   │   │   ├── C100.1 (bcl2 and stats files for each cycle)
│   │   │   │...
│   │   │   └── C99.1
│   │   ├── Matrix (matrix? files)
│   │   └── Phasing (phasing data)
│   ├── L001 (.locs files) 
│   └── Offsets ( ? )
├── RTALogs
└── TileStatus
"""
 
# TODO 
# examine "Config/"
# examine "InterOp/"

# TODO: support other lanes (hiseq; L001 limited to miseq)
purge_dirs = {  "Data/Intensities/BaseCalls/L001": "Per-cycle bcl, stats, and filter files",
                "Data/Intensities/BaseCalls/Matrix": "matrix files",
                "Data/Intensities/BaseCalls/Phasing": "phasing data",
                "Data/Intensities/L001": ".locs files",
                "Data/Intensities/Offsets": "offset data",
                "Data/RTALogs": "RTA log files",
                "Data/TileStatus": "tile files",
                "InterOp": "interop binary files",
                "Logs": "raw log files",
                "Thumbnail_Images": "thumbnail images",
}

# Note that although we want to preserve config.xml and RTAConfiguration.xml
# in Data/Intensities, (and probably also the XML files in Recipe/), there are
# > 1 GB of .XML files in the Logs directory that need to be purged so .xml
# is not included here in the failsafe ext list
safe_exts = [".fastq", ".fq", ".gz", ".bam", ".csv"]


parser = argparse.ArgumentParser(description="Clean up an illumina (presently miseq) run folder")
parser.add_argument("dir", help="absolute or relative pathname of directory to clean")
parser.add_argument("-n", "--dry-run", action="store_true", default=False, help="Display what would have been done, but do not delete anything")
args = parser.parse_args()

print("illumina run folder cleanup")
print("[{}]".format(args.dir))

# Sanitize pathname
#TODO

# Test exists
print("Testing path exists...", end="")
if not os.path.exists(args.dir):
    print("\n{} does not exist (or cannot be found)".format(args.dir))
    sys.exit(1)
else: print("ok")

# Test for access
print("Testing access...", end="")
if not os.access(args.dir, os.R_OK | os.W_OK | os.X_OK):
    print("\nCannot access {}".format(args.dir))
    sys.exit(1)
else: print("ok")

# Does this look like a runfolder?
print("Looking at run folder...", end="")
if not os.path.exists( os.path.join(args.dir, "RunInfo.xml") ):
    print("\nCould not find RunInfo.xml -- is this an illumina run folder?")
    sys.exit(1)
elif not os.path.exists( os.path.join(args.dir, "RTAComplete.txt") ):
    print("\nCould not find RTAComplete.txt -- cleaning up could damage in-progress analysis")
    sys.exit(1)
else: print("ok\n")

pre_disk = shutil.disk_usage(args.dir)  # filesystem level only

print("Beginning removal\n-----------------")
for leaf_dir,desc in purge_dirs.items():
    path = os.path.join( args.dir, leaf_dir)
    wildcard = os.path.join (path, "*")
    all_files = glob.glob( wildcard, recursive=True )
    remove_files = [ x for x in all_files if os.path.splitext(x)[1] not in safe_exts]
    diff = len(all_files) - len(remove_files)
    if diff < 0:
        print("WARNING: {} files with extensions in the safe list found in {}".format(diff, leaf))
        sys.exit(1)
    print("{} {}".format(len(all_files), desc))

    if args.dry_run:
        print("shutil.rmtree({}, ignore_errors=False, onerror=None)".format(path))
    else:
        shutil.rmtree(path, ignore_errors=False, onerror=None)

print("Done!")

post_disk = shutil.disk_usage(args.dir) # filesystem level only
print("\n")
print("Disk usage stats")
print("----------------")
print("pre : {}".format(pre_disk))
print("post: {}".format(post_disk))
