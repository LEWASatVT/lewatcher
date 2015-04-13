import requests, ConfigParser, os
from datetime import timedelta, datetime

triggerparams = 'host site medium metric low high interval threshold'.split()
triggertypes = [str, str, str, str, float, float, int, int]
triggertypes = {triggerparams[i]: triggertypes[i] for i in range(len(triggerparams))}

class Config():
    def __init__(self, config="config"):
        c = ConfigParser.RawConfigParser()
        c.read(os.path.abspath(config))
        self.triggers = []
	for s in c.sections():
            if s.startswith("watch-"):
                t = [triggertypes[o](c.get(s, o)) for o in triggerparams]
                self.triggers.append(t)

class Checker():
    def __init__(self, host, site, medium, metric, low, high, interval, threshold):
        for p in triggerparams:
            setattr(self, p, locals().get(p))

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
            print value
            if value > self.high or value < self.low:
                unacceptable.append([value, time])

        if len(unacceptable) > self.threshold:
            #TODO: configurable actions
            print "{0} ({1}) not within [{2}, {3}]! marcusw".format(
                self.metric, self.medium, self.low, self.high)
            print unacceptable

c = Config()
for targs in c.triggers:
    t = Checker(*targs)
    t.check()
