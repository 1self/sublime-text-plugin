import sublime, sublime_plugin, webbrowser

class GoToQuantifiedDevDashboardCommand(sublime_plugin.TextCommand):
   def run(self,edit):
        SETTINGS = {}
        SETTINGS_FILE = "QuantifiedDev.sublime-settings"
        SETTINGS = sublime.load_settings(SETTINGS_FILE)
        stream_id = SETTINGS.get("streamId")
        read_token = SETTINGS.get("readToken")
        url = "http://localhost:5000/dashboard?streamId=%(stream_id)s&readToken=%(read_token)s" % locals()  
        webbrowser.open_new_tab(url)