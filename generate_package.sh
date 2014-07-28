git stash
zip -r QuantifiedDev.sublime-package . -x generate_package.sh *.idea* *.git*  **.pyc*  **.script*
git stash apply
