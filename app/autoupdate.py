import sys, os, subprocess
import urllib.request

remote_repo = r"https://gitlab.com/rainlash/lt-maker/-/releases/permalink/latest/downloads/lex_talionis_maker"
remote_latest = r"https://gitlab.com/rainlash/lt-maker/-/releases/permalink/latest"
metadata = "version.txt"

def check_version(a: str, b: str) -> bool:
    """
    Returns True if a > b, False otherwise
    """
    a = a.replace('.', '').replace('-', '')
    b = b.replace('.', '').replace('-', '')
    return a != b

def download_url(url, save_path):
    with urllib.request.urlopen(url) as dl_file:
        with open(save_path, 'wb') as out_file:
            out_file.write(dl_file.read())

def get_redirected_url(url): # https://stackoverflow.com/questions/5538280/determining-redirected-url-in-python
    opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler)
    request = opener.open(url)
    return request.url

# Check
def check_for_update() -> bool:
    version_url = get_redirected_url(remote_latest)
    version_num = version_url.index("releases/") + len("releases/") # Will point to start of release ID
    new_version = version_url[version_num:]
    print(new_version, version_url)

    if os.path.exists(metadata):
        with open(metadata) as fp:
            lines = [l.strip() for l in fp.readlines()]
            cur_version = lines[0]

        print(new_version)
        print(cur_version)
        if check_version(new_version, cur_version):
            print("Needs update! %s %s" % (new_version, cur_version))
            return True
        else:
            print("Does not need update! %s %s" % (new_version, cur_version))
            return False
    else:
        print("Cannot find version.txt, so needs update: %s!" % metadata)
        return True

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


if __name__ == '__main__':
    check_for_update()