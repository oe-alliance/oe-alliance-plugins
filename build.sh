#!/bin/sh

# Script by Persian Prince for https://github.com/OpenVisionE2
# You're not allowed to remove my copyright or reuse this script without putting this header.

setup_git() {
  git config --global user.email "bot@oe-alliance.org"
  git config --global user.name "oe-alliance/oe-alliance-plugins python bot"
}

commit_files() {
  git clean -fd
  rm -rf *.pyc
  rm -rf *.pyo
  rm -rf *.mo
  git checkout python3
  ./PEP8.sh
}

upload_files() {
  git remote add upstream https://${GITHUB_TOKEN}@github.com/oe-alliance/oe-alliance-plugins.git > /dev/null 2>&1
  git push --quiet upstream python3 || echo "failed to push with error $?"
}

setup_git
commit_files
upload_files
