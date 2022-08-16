import sys, os, shutil
import time
import urllib.request
from zipfile import ZipFile

remote_zip = r"remote_tmp.zip"

def download_url(url, save_path):
    with urllib.request.urlopen(url) as dl_file:
        with open(save_path, 'wb') as out_file:
            out_file.write(dl_file.read())

def copy_and_overwrite(src, dst):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)

# Autoupdater process
def autoupdate(local, remote_lnk):
    print(local)
    tmp = local + '.tmp'
    if not os.path.exists(tmp):
        os.mkdir(tmp)
    print(tmp)
    # Actually download data
    download_url(remote_lnk, remote_zip)
    print(remote_zip)
    remote_dir = remote_zip.replace('.zip', '/')
    print(remote_dir)
    # Needs work in temp dir

    try:
        with ZipFile(remote_zip, 'r') as z:
            print("Extracting...")
            z.extractall(tmp)
        print("Done extracting to %s" % tmp)
        # shutil.copytree(os.path.join(remote_dir, 'lt-maker/lt-maker'), tmp)
    except OSError as e:
        print("Failed to fully unzip remote %s to %s! %s" % (remote_dir, tmp, e))
        return

    try:
        print("Copy projects and saves")
        tmp_lt_editor = os.path.join(tmp, 'lt_editor/lt_editor')
        copy_and_overwrite(os.path.join(local, 'saves'), os.path.join(tmp_lt_editor, 'saves'))
        for fn in os.listdir(local):
            if fn.endswith('.ltproj') and not fn.startswith('autosave') and not fn.startswith('default'):
                copy_and_overwrite(os.path.join(local, fn), os.path.join(tmp_lt_editor, fn))
    except OSError as e:
        print("Failed to copy saves or project files to tmp directory %s! %s" % (tmp, e))
        return

    print("Your new editor is located here: %s" % tmp)
    print("Your saves have been copied.")
    print("All .ltproj files have been copied as well.")
    print("You can delete the current directory, and then")
    print("rename the *.tmp directory, and you should be good to go.")

if __name__ == '__main__':
    print(sys.argv)
    if len(sys.argv) < 3:
        print("Not enough arguments %s" % sys.argv)
    local, remote = sys.argv[1], sys.argv[2]
    print(local, remote)
    time.sleep(4)
    autoupdate(local, remote)
    time.sleep(5)
    input("Press Enter...")
