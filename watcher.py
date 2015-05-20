import requests, ConfigParser, os, traceback
from datetime import timedelta, datetime
import dateutil.parser, pytz
import urllib2

class Config():
    def __init__(self, config="config"):
        c = ConfigParser.RawConfigParser()
        c.read(os.path.abspath(config))
        self.triggers = []
	for s in c.sections():
            if s.startswith("watch-"):
                d = dict([(o, c.get(s, o)) for o in c.options(s)])
                d["name"] = s[6:]
                self.triggers.append(d)

class Checker():

    triggerparams = 'name host site medium metric low high interval threshold reset email irc sguser sgpass'.split()
    triggertypes = [str, str, str, str, str, float, float, int, int, int, str, str, str, str]

    def __init__(self, d):
        tt = {self.triggerparams[i]: self.triggertypes[i] for i in range(len(self.triggerparams))}
        for p in self.triggerparams:
            setattr(self, p, tt[p](d.get(p)))

    def gethalbyname(self, data, name):
        for d in data:
            if d["name"] == name:
                return d

    def check(self):
        r = requests.get(self.host+"/sites/"+self.site+"/metricgroups")
        d = self.gethalbyname(r.json(), self.medium)["_embedded"]
        tsurl = self.gethalbyname(d["metrics"], self.metric)["_links"]["timeseries"]["href"]
        timestamp = (datetime.now()-timedelta(minutes=self.interval)).isoformat()
        ts = requests.get(self.host+tsurl, params={'since': timestamp})
        data = ts.json()["data"]

        unacceptable = []
        for value, time in data[-self.interval:]:
            if value > self.high or value < self.low:
                unacceptable.append([time, value])

        inevent = self.inevent()
        if len(unacceptable) >= self.threshold:
            if not inevent:
                self.notify(unacceptable)
            self.seteventstatus(dateutil.parser.parse(unacceptable[-1][0]))

    def inevent(self):
        eventfn = self.name+"-inevent"
        if not os.path.isfile(eventfn):
            return False
        last = dateutil.parser.parse(open(eventfn, 'r').readline().strip())
        delta = dateutil.parser.parse(datetime.now(pytz.utc).isoformat())-last
        if delta >= timedelta(minutes=self.reset):
            self.seteventstatus(False)
            return False
        else:
            return True

    def seteventstatus(self, status):
        #status is either False, or the unix timestamp of the most recent unacceptable reading
        eventfn = self.name+"-inevent"
        if status:
            open(eventfn, "w").write(str(status)+"\n")
        else:
            try:
                os.remove(eventfn)
            except OSError:
                pass

    def notify(self, unacceptable):
        print "{0} ({1}) not within [{2}, {3}]! {4}".format(
            self.metric, self.medium, self.low, self.high, self.irc)
        print unacceptable
        if self.email != "":
            import sendgrid
            sg = sendgrid.SendGridClient(self.sguser, self.sgpass, raise_errors=True)
            text = "Recent samples outside of threshold range:\n\n"
            text += "\n".join([t + ": " + str(v) for t,v in unacceptable]) + "\n\n"
            text += "To see the conditions leading up to this event, and to watch it happen live, "
            text += "visit: http://www.lewas.centers.vt.edu/dataviewer/single_graph.html\n\n"
            email = sendgrid.Mail(**{
                    "to": [e.strip() for e in self.email.split(",")],
                    "from_email": "lewatcher@lewaspedia.enge.vt.edu",
                    "from_name": "LEWatcher",
                    "subject": "LEWAS {0} Event: Samples outside of range ({1}, {2})".format(
                        self.metric, self.low, self.high),
                    "text": text,
                })
            try:
                image = urllib2.urlopen('http://128.173.156.152:3580/nph-jpeg.cgi').read()
                email.add_attachment_stream(
                    'camera-'+datetime.now().isoformat()+'.jpg', image)
            except:
                traceback.print_exc()
            sg.send(email)


c = Config()
for trigspec in c.triggers:
    t = Checker(trigspec)
    t.check()
