#!/bin/bash

# This script will get the last commit message that is not a merge message.

LAST_COMMIT_MESSAGE=$(git --no-pager log --pretty=format:"%s" -n 1)

echo -e "Last commit message is:\n $LAST_COMMIT_MESSAGE\n"
COUNTER=1

while [[ "$LAST_COMMIT_MESSAGE" =~ ^Merge[[:space:]]branch.*$
          || "$LAST_COMMIT_MESSAGE" =~ ^chore:.*$ ]]; do
  echo "Last message is merge message: $LAST_COMMIT_MESSAGE"
  LAST_COMMIT_MESSAGE=$(git --no-pager log --pretty=format:"%s" -n 1 --skip $COUNTER)
  COUNTER=$((COUNTER+1))
done

echo "Final message: $LAST_COMMIT_MESSAGE"

export GIT_LAST_COMMIT_MESSAGE="$LAST_COMMIT_MESSAGE"
