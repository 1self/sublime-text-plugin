import sublime

ST_VERSION = int(sublime.version())
PLUGIN_VERSION = 'v11'
QD_URL = "http://app.1self.co" # keep this http instead of https so that it works on ubuntu and other OS where https is not supported for python. "urllib.error.URLError: <urlopen error unknown url type: https>"
AUTHORIZAION = {
    'app-id': 'app-id-598358b6aacda229634d443c9539662b',
    'app-secret': 'app-secret-782411ad58934863f63545ccc180e407ffbe66cf5e9e02d31c2647ea786ead33'
}
SETTINGS_FILE = "1self.sublime-settings"