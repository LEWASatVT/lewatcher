import subprocess, shlex, os, ConfigParser, time

os.chdir(os.path.dirname(os.path.realpath(__file__)))

c = ConfigParser.RawConfigParser()
c.read(os.path.abspath("config"))

iicmd = "ii -i iirc " + c.get("irc", "iiargs")

ii = subprocess.Popen(shlex.split(iicmd))

try:
    while 1:
        os.system('bash -c "echo \\\"/j {}\\\" > iirc/*/in"'.format(c.get("irc", "chan")))
        os.system('bash -c "python2 watcher.py > iirc/*/{}/in"'.format(c.get("irc", "chan")))
        time.sleep(60)
finally:
    ii.terminate()
