# zipify
import os, shutil, sys

directory = os.path.abspath(sys.argv[1])
if os.path.isdir(directory):
    print("Zipping %s..." % directory)
    shutil.make_archive(directory, 'zip', directory)
else:
    print("Error! Could not locate %s" % directory)
