import sublime_plugin
from threading import Thread
import time
from time import sleep


try:
    import urllib.request as urllib2
except:
    import urllib2

    # def handle_action(self):
    # url = 'http://localhost:5000/stream/ZIBUWWLFTOBCNSYD/event'
    # data = json.dumps(eventJson)
    # binaryData = data.encode('utf8')
    # req = urllib2.Request(url, binaryData, {'Content-Type': 'application/json'})
    # req.add_header("Authorization", "GHbuKIiIgbQ6LBDr0uu26gW24ePbQA==")

    # response = urllib2.urlopen(req)
    # the_page = response.read()
    # {
    # "streamid": "ZIBUWWLFTOBCNSYD",
    # "writeToken": "GHbuKIiIgbQ6LBDr0uu26gW24ePbQA==",
    # "readToken": "b311N0ePqIJJqgxwUVNaiOzYvs4fIA==",
    # "_id": ObjectId("53a01f64a23308064a2ab5db")
    # }


class QuantifiedDevListener(sublime_plugin.EventListener):
    isUserActive = False
    activeSessionStartTime = time.time()
    activeSessionEndTime = activeSessionStartTime
    inactiveSessionStartTime = time.time()
    inactiveSessionEndTime = inactiveSessionStartTime
    THRESHOLD_INACTIVITY_DURATION = 30

    def on_post_save(self, view):
        self.handleEvent()

    def on_activated(self, view):
        self.handleEvent()

    def on_modified(self, view):
        self.handleEvent()

    def sublimeActivityDetectorThread(self):
        while True:
            print(
                "isUserActive : %s inactivityDuration : %s sec" % (self.isUserActive, round(self.inactivityDuration())))
            if self.isUserActive:
                if self.inactivityDuration() >= self.THRESHOLD_INACTIVITY_DURATION:
                    self.inactiveSessionStartTime = self.activeSessionEndTime
                    self.logEventQD(self.activityDuration())
                    self.markUserAsInactive()
                    print(
                        "User is inactive now isUserActive : %s and activityDuration was : %s sec" % (
                            self.isUserActive, round(self.activityDuration())))
            sleep(self.THRESHOLD_INACTIVITY_DURATION)

    def __init__(self):
        thread = Thread(target=self.sublimeActivityDetectorThread)
        thread.start()

    def handleEvent(self):
        if not self.isUserActive:
            self.startCountingActivity()
            self.markUserAsActive()
        elif self.inactivityDuration() >= self.THRESHOLD_INACTIVITY_DURATION:
            self.handleIdeaWakeupEvent()
        self.updateActivityEndCounter()
        self.printEverything()

    def printEverything(self):
        print("isUserActive : %s activeDuration: %s sec" % (self.isUserActive, round(self.activityDuration())))

    def startCountingActivity(self):
        self.activeSessionStartTime = time.time()
        self.inactiveSessionEndTime = self.activeSessionStartTime

    def markUserAsActive(self):
        self.isUserActive = True

    def handleIdeaWakeupEvent(self):
        self.logEventQD(self.activityDuration())
        self.startCountingActivity()

    def updateActivityEndCounter(self):
        self.activeSessionEndTime = time.time()

    def logEventQD(self, timeDurationInMillis):
        activityEvent = self.createActivityEvent(timeDurationInMillis)
        self.persist(activityEvent)

    def createActivityEvent(self, timeDurationInMillis):
        event = {
            "dateTime": "2014-06-30T14:50:39.000Z",
            "streamid": "ZIBUWWLFTOBCNSYD",
            "location": {
                "lat": 51.5,
                "long": -0.13
            },
            "source": "Sublime Text Plugin",
            "version": "0.0.1.beta1",
            "objectTags": [
                "Computer",
                "Software"
            ],
            "actionTags": [
                "Develop"
            ],
            "properties": {
                "Environment": "Sublime Text 3",
                "isUserActive": True,
                "duration": timeDurationInMillis
            }
        }
        return event

    def persist(self, event):
        writeToken = "write_token"
        print("event to be sent to server : %s " % event)
        # Configuration.repository.insert(event, writeToken)

    def inactivityDuration(self):
        return time.time() - self.activeSessionEndTime

    def activityDuration(self):
        return self.activeSessionEndTime - self.activeSessionStartTime

    def markUserAsInactive(self):
        self.isUserActive = False