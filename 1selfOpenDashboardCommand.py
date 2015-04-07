import sublime, sublime_plugin, webbrowser


QD_URL = "http://www.1self.co"

class GoTo1selfDashboardCommand(sublime_plugin.TextCommand):
   def run(self,edit):
        SETTINGS = {}
        SETTINGS_FILE = "1self.sublime-settings"
        SETTINGS = sublime.load_settings(SETTINGS_FILE)
        stream_id = SETTINGS.get("streamId")
        read_token = SETTINGS.get("readToken")
        VERSION = SETTINGS.get("VERSION")
        qd_url = QD_URL

        url = "%(qd_url)s/?streamid=%(stream_id)s&readToken=%(read_token)s&appid=app-id-598358b6aacda229634d443c9539662b&version=%(VERSION)s" % locals()
        print(url)
        webbrowser.open_new_tab(url)