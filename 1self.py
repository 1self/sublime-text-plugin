import sublime_plugin, sublime
from threading import Thread
import time
from time import sleep
import json
import copy
import collections
import logging
import datetime
import os
import sys

ST_VERSION = int(sublime.version())
PLUGIN_VERSION = 'v0.0.13'
QD_URL = "http://app.1self.co" # keep this http instead of https so that it works on ubuntu and other OS where https is not supported for python. "urllib.error.URLError: <urlopen error unknown url type: https>"
AUTHORIZAION = {
    'app-id': 'app-id-598358b6aacda229634d443c9539662b',
    'app-secret': 'app-secret-782411ad58934863f63545ccc180e407ffbe66cf5e9e02d31c2647ea786ead33'
}
SETTINGS_FILE = "1self.sublime-settings"
package_name = "1Self"

try:
    import urllib.request as urllib2
except:
    import urllib2


event_persister = collections.deque()
stream_id = ""
write_token = ""

QD_LOGS_DIRECTORY_PATH = os.path.join(os.path.expanduser("~"), ".qd");
if not os.path.exists(QD_LOGS_DIRECTORY_PATH):
    os.makedirs(QD_LOGS_DIRECTORY_PATH)

LOG_FILENAME = os.path.abspath(os.path.join(os.path.expanduser("~"), ".qd", "qd_st_plugin.log"))

logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG,format='%(asctime)s %(levelname)s:%(message)s')

def get_localtime_isoformat():
    now = datetime.datetime.now()
    utcnow = datetime.datetime.utcnow()
    diff = now - utcnow
    hh,mm = divmod((diff.days * 24*60*60 + diff.seconds + 30) // 60, 60)
    return "%s%+03d:%02d" % (now.isoformat(), hh, mm)

def plugin_loaded():
    print('Initializing 1self plugin')
    global SETTINGS
    SETTINGS = sublime.load_settings(SETTINGS_FILE)
    VERSION = SETTINGS.get("VERSION")
    if(VERSION != PLUGIN_VERSION):
        SETTINGS.set("VERSION", str(PLUGIN_VERSION))
        sublime.save_settings(SETTINGS_FILE)

    after_loaded()


def after_loaded():
    global stream_id
    global write_token

    get_stream_id_if_not_present()

    stream_id = SETTINGS.get("streamId")
    write_token = SETTINGS.get("writeToken")

def plugin_unloaded():
    from package_control import events

    if events.pre_upgrade(package_name):
        print('Upgrading from %s!' % events.pre_upgrade(package_name))
    elif events.remove(package_name):
        print('Removing %s!' % events.remove(package_name))
        event = create_uninstall_event()
        if event is not None:
            send_event_to_platform(event)

def send_event_to_platform(event):
    url = QD_URL + "/v1/streams/" + stream_id + "/events"
    data = json.dumps(event)
    utf_encoded_data = data.encode('utf8')
    req = urllib2.Request(url, utf_encoded_data, {'Content-Type': 'application/json', 'Authorization': write_token})
    response = urllib2.urlopen(req)
    result = response.read()
    return result

def create_uninstall_event():
    if stream_id is None or len(stream_id) is 0:
        return None

    dt = get_localtime_isoformat()

    st_version_string = "Sublime Text " + str(ST_VERSION)
    event = {
        "dateTime": dt,
        "streamid": stream_id,
        "source": "Sublime Text Plugin",
        "version": PLUGIN_VERSION,
        "objectTags": [
            "Computer",
            "Software",
            "Sublime"
        ],
        "actionTags": [
            "Uninstall"
        ],
        "properties": {
            "version": PLUGIN_VERSION,
            "Environment": st_version_string
        }
    }
    return event 

def get_stream_id_if_not_present():

    if SETTINGS.get('streamId'):
        return True
    else:
        event = {}
        url = QD_URL + "/v1/streams"
        authorization = AUTHORIZAION['app-id'] + ":" + AUTHORIZAION['app-secret']
        data = json.dumps(event)
        utf_encoded_data = data.encode('utf8')
        req = urllib2.Request(url, utf_encoded_data, 
            {
                'Content-Type': 'application/json',
                'Authorization': authorization
            })
        response = urllib2.urlopen(req)
        result = response.read()
        #print(result)

        json_result = json.loads(result.decode('utf8'))

        SETTINGS.set("streamId", str(json_result['streamid']))
        SETTINGS.set("readToken", str(json_result['readToken']))  
        SETTINGS.set("writeToken", str(json_result['writeToken']))  
        sublime.save_settings(SETTINGS_FILE)


class OneSelfListener(sublime_plugin.EventListener):
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
            # logging.debug(
            #     "isUserActive : %s inactivityDuration : %s sec" % (
            #         self.is_user_active, self.inactivity_duration()))
            try:
                if self.is_user_active:
                    if self.inactivity_duration() >= self.THRESHOLD_INACTIVITY_DURATION:
                        self.inactive_session_start_time = self.active_session_end_time
                        self.log_event_qd(self.activity_duration())
                        self.mark_user_as_inactive()
                        # logging.debug(
                        #     "User is inactive now isUserActive : %s and activityDuration was : %s sec" % (
                        #         self.is_user_active, self.activity_duration()))
                sleep(self.THRESHOLD_INACTIVITY_DURATION)
            except Exception as e:
                logging.error("Error occured while detecting activity")
                logging.exception(e)
                break

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
    #     logging.debug("isUserActive : %s activeDuration: %s sec" % (self.is_user_active, self.activity_duration()))

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
        if time_duration_in_seconds > 0:
            activity_event = self.create_activity_event(time_duration_in_seconds)
            self.persist(activity_event)

    def create_activity_event(self, time_duration_in_seconds):
        dt = get_localtime_isoformat()

        st_version_string = "Sublime Text " + str(ST_VERSION)
        event = {
            "dateTime": dt,
            "streamid": stream_id,
            "source": "Sublime Text Plugin",
            "version": PLUGIN_VERSION,
            "objectTags": [
                "Computer",
                "Software"
            ],
            "actionTags": [
                "Develop"
            ],
            "properties": {
                "duration": time_duration_in_seconds,
                "Environment": st_version_string
            }
        }
        return event

    def persist(self, event):
        event_persister.append(event)

    def send_events_from_queue(self):
        while True:
            event_persister_copy = copy.deepcopy(event_persister)
            # logging.debug("Event Queue:")
            # logging.debug(event_persister)
            if event_persister_copy:
                logging.debug("Event present in queue")
                event = event_persister_copy.popleft()
                try:
                    logging.debug("Trying to send event to platform")
                    logging.debug(event)
                    self.send_event_to_platform(event)
                    event_persister.popleft()
                    logging.debug("Event sent successfully")
                except Exception as e:
                    logging.debug("Event not sent due to some problem")
                    logging.exception(e)
                    sleep(300)
            else:
                #logging.debug("No event found in queue.. sleeping for 1 minute")
                sleep(60)


    def send_event_to_platform(self, event):
        url = QD_URL + "/v1/streams/" + stream_id + "/events"
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
    unload_handler = plugin_unloaded
