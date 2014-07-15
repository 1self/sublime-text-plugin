import sublime_plugin, sublime
from threading import Thread
import time
from time import sleep
import json
import copy
import collections
import logging
import datetime

try:
    import urllib.request as urllib2
except:
    import urllib2

ST_VERSION = int(sublime.version())
QD_URL = "http://app.quantifieddev.org"
SETTINGS = {}
SETTINGS_FILE = "QuantifiedDev.sublime-settings"
event_persister = collections.deque()
stream_id = ""
write_token = ""

def plugin_loaded():
    print('Initializing QuantifiedDev plugin')
    global SETTINGS
    SETTINGS = sublime.load_settings(SETTINGS_FILE)
    after_loaded()


def after_loaded():
    global stream_id
    global write_token

    get_stream_id_if_not_present()

    stream_id = SETTINGS.get("streamId")
    write_token = SETTINGS.get("writeToken")


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
        #print(result)

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
    THRESHOLD_INACTIVITY_DURATION = 60


    def on_post_save(self, view):
        self.handle_event()

    def on_activated(self, view):
        self.handle_event()

    def on_modified(self, view):
        self.handle_event()

    def sublime_activity_detector_thread(self):
        while True:
            # print(
            #     "isUserActive : %s inactivityDuration : %s sec" % (
            #         self.is_user_active, self.inactivity_duration()))
            if self.is_user_active:
                if self.inactivity_duration() >= self.THRESHOLD_INACTIVITY_DURATION:
                    self.inactive_session_start_time = self.active_session_end_time
                    self.log_event_qd(self.activity_duration())
                    self.mark_user_as_inactive()
                    # print(
                    #     "User is inactive now isUserActive : %s and activityDuration was : %s sec" % (
                    #         self.is_user_active, self.activity_duration()))
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
        # self.print_everything()

    # def print_everything(self):
    #     print("isUserActive : %s activeDuration: %s sec" % (self.is_user_active, self.activity_duration()))

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

    def log_event_qd(self, time_duration_in_seconds):
        time_duration_in_millis = time_duration_in_seconds * 1000
        activity_event = self.create_activity_event(time_duration_in_millis)
        self.persist(activity_event)

    def create_activity_event(self, time_duration_in_millis):
        st_version = ST_VERSION
        utc_datetime = datetime.datetime.utcnow()
        dt = utc_datetime.isoformat()

        st_version_string = "Sublime Text %(st_version)s" % locals()
        event = {
            "dateTime": dt,
            "streamid": stream_id,
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
                "Environment": st_version_string,
                "isUserActive": True,
                "duration": time_duration_in_millis
            }
        }
        return event

    def persist(self, event):
        event_persister.append(event)

    def send_events_from_queue(self):
        while True:
            event_persister_copy = copy.deepcopy(event_persister)
            # print("Event Queue:")
            # print(event_persister)
            if event_persister_copy:
                #print("Event present in queue")
                event = event_persister_copy.popleft()
                try:
                    print("Trying to send event to platform")
                    print(event)
                    self.send_event_to_platform(event)
                    event_persister.popleft()
                    print("Event sent successfully")
                except Exception as e:
                    logging.exception(e)
                    sleep(300)
                    #print("Event not sent due to some problem")
            else:
                #print("No event found in queue.. sleeping for 1 minute")
                sleep(30)


    def send_event_to_platform(self, event):
        qd_url = QD_URL
        stream_id_local = stream_id
        url = "%(qd_url)s/stream/%(stream_id_local)s/event" % locals()
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



# need to call plugin_loaded because only ST3 will auto-call it
if ST_VERSION < 3000:
    plugin_loaded()