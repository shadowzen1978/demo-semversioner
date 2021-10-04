#!/bin/bash

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

echo "Current branch is $CURRENT_BRANCH"

echo -e "Commits since last push to remote origin:\n"

git --no-pager log --pretty=format:"%s" origin/$CURRENT_BRANCH..$CURRENT_BRANCH

# command output above does not have ending line break so need to add before exiting script
echo ""
