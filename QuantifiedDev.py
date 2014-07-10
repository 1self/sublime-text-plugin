import sublime_plugin, sublime
from threading import Thread
import time
from time import sleep
import json
import copy
import collections

try:
    import urllib.request as urllib2
except:
    import urllib2

QD_URL = "http://localhost:5000"
SETTINGS = {}
SETTINGS_FILE = "QuantifiedDev.sublime-settings"
event_persister = collections.deque()

def plugin_loaded():
    print('Initializing QuantifiedDev plugin')
    global SETTINGS
    SETTINGS = sublime.load_settings(SETTINGS_FILE)
    after_loaded()


def after_loaded():
    get_stream_id_if_not_present()


def get_stream_id_if_not_present():

    if SETTINGS.get('streamId'):
        return True
    else:
        event = {}
        qd_url = QD_URL
        url = "%(qd_url)s/stream" % locals()
        data = json.dumps(event)
        utf_encoded_data = data.encode('utf8')
        req = urllib2.Request(url, utf_encoded_data, {'Content-Type': 'application/json'})
        response = urllib2.urlopen(req)
        result = response.read()
        print(result)

        json_result = json.loads(result.decode('utf8'))

        SETTINGS.set("streamId", str(json_result['streamid']))
        SETTINGS.set("readToken", str(json_result['readToken']))  
        SETTINGS.set("writeToken", str(json_result['writeToken']))  
        sublime.save_settings(SETTINGS_FILE)


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
        thread = Thread(target=self.send_events_from_queue)
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
        stream_id = SETTINGS.get("streamId")
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
        stream_id = SETTINGS.get("streamId")
        write_token = SETTINGS.get("writeToken")
        tuple = (event, stream_id, write_token)
        event_persister.append(tuple)

    def send_events_from_queue(self):
        while True:
            event_persister_copy = copy.deepcopy(event_persister)
            print("Event Queue:")
            print(event_persister)
            if event_persister_copy:
                print("Event present in queue")
                event_tuple = event_persister_copy.popleft()
                event = event_tuple[0]
                stream_id = event_tuple[1]
                write_token = event_tuple[2]
                try:
                    print("Trying to send event to platform")
                    self.send_event_to_platform(event, stream_id, write_token)
                    event_persister.popleft()
                    print("Event sent successfully")
                    print(event)
                except:
                    sleep(15)
                    print("Event not sent due to some problem")
            else:
                print("No event found in queue.. sleeping for 1 minute")
                sleep(30)


    def send_event_to_platform(self, event, stream_id, write_token):
        qd_url = QD_URL
        url = "%(qd_url)s/stream/%(stream_id)s/event" % locals()
        data = json.dumps(event)
        utf_encoded_data = data.encode('utf8')
        req = urllib2.Request(url, utf_encoded_data, {'Content-Type': 'application/json', 'Authorization': write_token})
        response = urllib2.urlopen(req)
        result = response.read()

    def inactivity_duration(self):
        return round(time.time() - self.active_session_end_time)

    def activity_duration(self):
        return round(self.active_session_end_time - self.active_session_start_time)

    def mark_user_as_inactive(self):
        self.is_user_active = False