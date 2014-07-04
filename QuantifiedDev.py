import sublime_plugin
from threading import Thread
import time
from time import sleep
import json

try:
    import urllib.request as urllib2
except:
    import urllib2


class QuantifiedDevListener(sublime_plugin.EventListener):
    is_user_active = False
    active_session_start_time = time.time()
    active_session_end_time = active_session_start_time
    inactive_session_start_time = time.time()
    inactive_session_end_time = inactive_session_start_time
    THRESHOLD_INACTIVITY_DURATION = 30

    def on_post_save(self, view):
        self.handle_event()

    def on_activated(self, view):
        self.handle_event()

    def on_modified(self, view):
        self.handle_event()

    def sublime_activity_detector_thread(self):
        while True:
            print(
                "isUserActive : %s inactivityDuration : %s sec" % (
                    self.is_user_active, self.inactivity_duration()))
            if self.is_user_active:
                if self.inactivity_duration() >= self.THRESHOLD_INACTIVITY_DURATION:
                    self.inactive_session_start_time = self.active_session_end_time
                    self.log_event_qd(self.activity_duration())
                    self.mark_user_as_inactive()
                    print(
                        "User is inactive now isUserActive : %s and activityDuration was : %s sec" % (
                            self.is_user_active, self.activity_duration()))
            sleep(self.THRESHOLD_INACTIVITY_DURATION)

    def __init__(self):
        thread = Thread(target=self.sublime_activity_detector_thread)
        thread.start()

    def handle_event(self):
        if not self.is_user_active:
            self.start_counting_activity()
            self.mark_user_as_active()
        elif self.inactivity_duration() >= self.THRESHOLD_INACTIVITY_DURATION:
            self.handle_sublime_wakeup_event()
        self.update_activity_end_counter()
        self.print_everything()

    def print_everything(self):
        print("isUserActive : %s activeDuration: %s sec" % (self.is_user_active, self.activity_duration()))

    def start_counting_activity(self):
        self.active_session_start_time = time.time()
        self.inactive_session_end_time = self.active_session_start_time

    def mark_user_as_active(self):
        self.is_user_active = True

    def handle_sublime_wakeup_event(self):
        self.log_event_qd(self.activity_duration())
        self.start_counting_activity()

    def update_activity_end_counter(self):
        self.active_session_end_time = time.time()

    def log_event_qd(self, time_duration_in_millis):
        activity_event = self.create_activity_event(time_duration_in_millis)
        self.persist(activity_event)

    def create_activity_event(self, time_duration_in_millis):
        stream_id = "ZIBUWWLFTOBCNSYD"
        event = {
            "dateTime": "2014-06-30T14:50:39.000Z",
            "streamid": stream_id,
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
                "duration": time_duration_in_millis
            }
        }
        return event

    def persist(self, event):
        stream_id = "ZIBUWWLFTOBCNSYD"
        write_token = "GHbuKIiIgbQ6LBDr0uu26gW24ePbQA=="
        print("event to be sent to server : %s " % event)
        thread = Thread(target=self.send_event_to_platform, args=(event, stream_id, write_token))
        thread.start()

    def send_event_to_platform(self, event, stream_id, write_token):
        print("Started: sending")
        time.sleep(10)
        url = "http://localhost:5000/stream/%(stream_id)s/event" % locals()
        data = json.dumps(event)
        utf_encoded_data = data.encode('utf8')
        req = urllib2.Request(url, utf_encoded_data, {'Content-Type': 'application/json', 'Authorization': write_token})
        response = urllib2.urlopen(req)
        result = response.read()
        print("Sent successfully")

    def inactivity_duration(self):
        return round(time.time() - self.active_session_end_time)

    def activity_duration(self):
        return round(self.active_session_end_time - self.active_session_start_time)

    def mark_user_as_inactive(self):
        self.is_user_active = False