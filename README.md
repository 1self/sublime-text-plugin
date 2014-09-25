#Sublime Text Plugin for QuantifiedDev

### Overview

QuantifiedDev is Quantified Self for developers - self knowledge through numbers.
i.e. You can see interesting stats and correlations drawn from your daily builds
<a href="http://www.quantifieddev.org/app">here</a>.
Sublime Text Plugin tracks amount of time user is active in Sublime Text Editor.

# Installation
Go to menu item named 'View', then click 'Show Console'
Type following in the console

####  for Sublime Text 2
```python
import urllib2,os,hashlib;pf = 'QuantifiedDev.sublime-package';ipp = sublime.installed_packages_path();os.makedirs( ipp ) if not os.path.exists(ipp) else None;urllib2.install_opener( urllib2.build_opener( urllib2.ProxyHandler()) );by = urllib2.urlopen( 'http://app.quantifieddev.org/' + pf.replace(' ', '%20')).read();open( os.path.join( ipp, pf), 'wb' ).write(by)
```
Restart Sublime Text 2 after installation of plugin

#### for Sublime Text 3
```python
import urllib.request, os, hashlib; pf = 'QuantifiedDev.sublime-package'; ipp = sublime.installed_packages_path(); urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler()));by = urllib.request.urlopen('http://app.quantifieddev.org/' + pf.replace(' ', '%20') ).read();open(os.path.join(ipp, pf), 'wb').write(by)
```
You don't need to restart Sublime Text 3. Plugin is active now.

### How do I see my stats
1. Open Sublime Text editor
2. Go to Tools -> QuantifiedDev -> Go to QuantifiedDev Dashboard or CTRL + SHIFT + p -> Go to QuantifiedDev Dashboard


#### Plugin logs path
Plugin logs are stored in "~/.qd/qd_st_plugin.log" where '~' is your machines' home folder.

### Information collected by Plugin:
User activity in Sublime Text.
