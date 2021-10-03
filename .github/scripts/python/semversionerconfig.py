# This is simply just a number of configuration elements for semversioner-based scripts.

# Elements in this list *have* to be in raw string format in order to be
# evaluated properly via regex commands
semversioner_messages_regex_filter_list = [
    r'^Merge branch.*$',
    r'^chore:.*$'
    ]

# A list of messages to test evaluation with
semversioner_test_message_list = [
    'test message 1',
    'test message 2',
    'test message 2',
    'Here is a default message:',
    'chore: a chore task',
    'Merge branch foo into branch bar',
    'Patch:  a patch change',
    "Minor:  a minor change",
    'Major:  a major change',
    "This is also a major change because I've added 'BREAKING CHANGE' in the message.",
    'Final test string'
    ]
