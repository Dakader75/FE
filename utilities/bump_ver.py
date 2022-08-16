import datetime
import fileinput
import os
import re

# version updater -- run this once before commit to automatically use the correct version
# version_format = 'YYYY.MM.DDa'

current_date = str(datetime.datetime.now())
year = current_date[:4]
month = current_date[5:7]
day = current_date[8:10]

files_to_change = ['./metadata.txt', './app/constants.py']

new_version_prefix = '.'.join([year, month, day])
print("new version prefix: %s" % new_version_prefix)

for fn in files_to_change:
    print("Searching %s..." % fn)
    to_match = r'\d\d\d\d.\d\d.\d\d[a-z]'
    if not os.path.exists(fn):
        print("%s don't exist!" % fn)
        continue
    for line in fileinput.input(fn, inplace=True):
        match = re.search(to_match, line)
        if not match:
            print(line, end='')
            continue
        span = match.span()
        substr = line[span[0]:span[1]]
        last_char = substr[-1]
        old_version_prefix = substr[:-1]
        if new_version_prefix == old_version_prefix:
            new_last_char = str(chr(ord(last_char) + 1))
        else:
            new_last_char = 'a'
        new_version = new_version_prefix + new_last_char
        line = line.replace(substr, new_version)
        print(line, end='')
