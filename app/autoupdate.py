import sys, os, subprocess
import urllib.request

from app.constants import VERSION

remote_repo = r"https://www.dropbox.com/s/q8ii1e4rd3e97et/lt_editor.zip?dl=1"
remote_metadata = r"https://www.dropbox.com/s/3kilsxojvdiogvb/metadata.txt?dl=1"

def check_version(a: str, b: str) -> bool:
    """
    Returns True if a > b, False otherwise
    """
    a = a.replace('.', '').replace('-', '')
    b = b.replace('.', '').replace('-', '')
    return a > b

def download_url(url, save_path):
    with urllib.request.urlopen(url) as dl_file:
        with open(save_path, 'wb') as out_file:
            out_file.write(dl_file.read())
    
# Check
def check_for_update() -> bool:
    metadata = 'metadata.txt.tmp'
    try:
        download_url(remote_metadata, metadata)
    except:
        print("Could not access internet!")
        return False
    if os.path.exists(metadata):
        with open(metadata) as fp:
            lines = [l.strip() for l in fp.readlines()]
            version = lines[0]
        print(version)
        print(VERSION)
        if check_version(version, VERSION):
            print("Needs update! %s %s" % (version, VERSION))
            return True
        else:
            print("Does not need update! %s %s" % (version, VERSION))
            return False
    else:
        print("Cannot find metadata loc: %s!" % metadata)
        return None

CREATE_NEW_CONSOLE = 0x00000010

# Start a new process that will update all files
def update() -> bool:
    print("Starting Process! %s" % remote_repo)
    print("Executable: %s" % sys.executable)
    local = os.path.dirname(sys.executable)
    print("Local: %s" % local)
    cwd = os.path.abspath(os.getcwd())
    print("Current working directory: %s" % cwd)
    pid = subprocess.Popen(['./autoupdater.exe', cwd, remote_repo], creationflags=CREATE_NEW_CONSOLE).pid
    # Just for testing
    # pid = subprocess.Popen(['python', 'autoupdater.py', local, remote_repo], creationflags=CREATE_NEW_CONSOLE).pid

    print("pid: %d" % pid)
    return True
