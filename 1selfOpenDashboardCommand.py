import sublime, sublime_plugin, webbrowser


QD_URL = "https://app.1self.co"

class GoTo1selfDashboardCommand(sublime_plugin.TextCommand):
   def run(self,edit):
        SETTINGS = {}
        SETTINGS_FILE = "1self.sublime-settings"
        SETTINGS = sublime.load_settings(SETTINGS_FILE)
        stream_id = SETTINGS.get("streamId")
        read_token = SETTINGS.get("readToken")
        qd_url = QD_URL

        url = "%(qd_url)s/dashboard?streamId=%(stream_id)s&readToken=%(read_token)s" % locals()
        webbrowser.open_new_tab(url)
