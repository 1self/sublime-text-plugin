git stash
zip -r 1self.sublime-package . -x generate_package.sh *.idea* *.git*  **.pyc*  **.script*
git stash apply
