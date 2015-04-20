import requests, ConfigParser, os
from datetime import timedelta, datetime

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

    triggerparams = 'name host site medium metric low high interval threshold'.split()
    triggertypes = [str, str, str, str, str, float, float, int, int]

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

        unacceptable = []
        for value, time in ts.json()["data"]:
            if value > self.high or value < self.low:
                unacceptable.append([value, time])

        if len(unacceptable) > self.threshold:
            #TODO: configurable actions
            print "{0} ({1}) not within [{2}, {3}]!".format(
                self.metric, self.medium, self.low, self.high)
            print unacceptable

    def notify(self):
        storefn = os.path.abspath()
        if os.path.isfile(storefn):
            last = open(os.path.abspath(config), 'r').readline().strip()

c = Config()
for trigspec in c.triggers:
    t = Checker(trigspec)
    t.check()
