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

    triggerparams = 'name host site medium metric low high interval threshold reset email irc'.split()
    triggertypes = [str, str, str, str, str, float, float, int, int, int, str, str]

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
        timestamp = (datetime.now()-timedelta(minutes=self.reset)).isoformat()
        ts = requests.get(self.host+tsurl, params={'since': timestamp})
        data = ts.json()["data"]

        unacceptable = []
        for value, time in data[-self.interval:]:
            if value > self.high or value < self.low:
                unacceptable.append([value, time])

        if len(unacceptable) > self.threshold:
            if not self.inevent():
                self.seteventstatus(True)
                self.notify(unacceptable)
        elif self.inevent():
            reset = True
            for value, time in data[-self.interval:]:
                if value > self.high or value < self.low:
                    reset = False
                    break
            if reset:
                self.seteventstatus(False)

    def inevent(self):
        eventfn = self.name+"-inevent"
        return os.path.isfile(eventfn)

    def seteventstatus(self, inevent):
        eventfn = self.name+"-inevent"
        if inevent:
            open(eventfn, "w").close()
        else:
            if self.inevent():
                os.remove(eventfn)

    def notify(self, unacceptable):
        print "{0} ({1}) not within [{2}, {3}]! {4}".format(
            self.metric, self.medium, self.low, self.high, self.irc)
        print unacceptable
        if self.email != "":
            import sendgrid
            sg = sendgrid.SendGridClient(self.sguser, self.sgpass)
            sg.send(
                sendgrid.Mail(**{
                    "to": self.email.split(","),
                    #"from": "marcus@wanners.net",
                    "subject": "LEWAS {0} Event: Outside of range ({1},{2})".format(
                        self.metric, self.low, self.high),
                    "text": str(unacceptable)
                })
            )


c = Config()
for trigspec in c.triggers:
    t = Checker(trigspec)
    t.check()
