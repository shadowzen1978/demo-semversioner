#!/usr/bin/env python3
# Minimum version of python 3.7 is required for this script
# Much if this logic relies on simple git commands run through subprocess
# If I more time I might rewrite this to use octokitpy to be more pythonic
# but that does necessitate an additional dependency and installation thereof.
# Being that this is intended to be run in automation pipelines, not having to worry
# About the installation of an additional dependency is probably worth the tradeoff.
import datetime
import os
import pprint
import re
import semversionerconfig
import subprocess
import sys
pp = pprint.PrettyPrinter(indent=4)

# Set a bunch of flags here.  Eventually will have most of these
# passable as cli args.
debug_mode=True
test_mode=True
use_test_messages= False
clean_release=True
clean_action='delete'
cwd = os.getcwd()
scriptpath = os.path.dirname(os.path.realpath(sys.argv[0]))

def main(argv):
    """The main loop of this script.
    Will get a list of git messages by comparing the current branch to the
    remote default branch.  Then will parse the list of messages to eliminate
    redundant messages and certain types of messages related to such actions like
    merge messages or automation tasks.

    Afterwards, will pass the cleaned up list of messages to semversioner script
    to create a list of changes to prepare a release.
    """
    current_branch = get_current_branch()
    remote_branch = 'origin/{}'.format(get_default_branch())
    repo_root = get_git_repo_top_level()
    semversioner_nr_folder = f"{repo_root}/.semversioner/next-release"
    print(f"Current branch:  {current_branch}\nRemote_branch:  {remote_branch}\nRepo Root: {repo_root}")

    default_change_type = set_default_change_type(current_branch)
    if debug_mode is True:
        print(f"Default change type: {default_change_type}")
    if default_change_type is None:
        # For now we have no further action to do if the default type cannot be
        # determined by the branch name.
        sys.exit(0)
    if clean_release is True:
        semversioner_clean_next_release(folder=semversioner_nr_folder,action=clean_action)
    #sys.exit(0)

    message_filter = semversionerconfig.semversioner_messages_regex_filter_list
    if debug_mode is True:
        print("*** Debug regex message filter:")
        print(message_filter)
        print("Looping evaluated values:")
        for s in message_filter:
            pattern = rf"{s}"
            print(pattern)
        print("*** End Debug message\n")


    if test_mode is True and use_test_messages is True:
        message_list = semversionerconfig.semversioner_test_message_list
    else:
        message_list = get_git_commit_messages(current_branch, remote_branch)

    #print(f"Message List:\n{message_list}")

    change_message_list = remove_dupe_messages(message_list)
    change_message_list = filter_message_list(change_message_list, message_filter)

    if debug_mode is True:
        print("\nChange messages:")
        for m in change_message_list:
            print(f"  - {m}")


    semversioner_create_change(
        change_list=change_message_list,
        default_change_type=default_change_type,
        run_location = repo_root)
    # TODO: from here will need to pass the list of messages to a function to create
    # change messages, using the branch name as a default value and basic message parsing
    # to determine if the commit message warrants a different level
    # semversioner_create_change() - iterate through the list and create changes
    # need to evaluate which directory to run in as semversioner creates files at level called.
    # provide an option to clean .semversioner/next-release folder if needed.


def semversioner_create_change(change_list, default_change_type, run_location):
    """Iterate of a list of changes and create a change entry for next release.
    We start with a default type but can evalaute for additional change types with some
    very basic checking of certain key phrases.

    Parameters
    ----------
    change_list : list
        List of change messages to act upon.

    default_change_type : string
        The default change type, if not overridden by additional evaluation.

    Returns
    -------

    """
    if debug_mode is True:
        print(
            "Original Current path:{}\nScript path: {}\nRun location: {}".format(
                cwd,
                scriptpath,
                run_location
                )
            )
        print(f"Attempting to change directory to '{run_location}'...")

    os.chdir(run_location)
    print("Running semversioner in '{}'".format(os.getcwd()))

    for message in change_list:
        if (re.match('^MAJOR:.*$', message, flags=re.IGNORECASE)) or (re.match('^.*BREAKING CHANGE.*$', message, flags=re.IGNORECASE)) or (re.match('^.*MAJOR CHANGE.*$', message, flags=re.IGNORECASE)):
            change_type = 'major'
        elif re.match('^MINOR:.*$', message, flags=re.IGNORECASE):
            change_type = 'minor'
        elif re.match('^PATCH:.*$', message, flags=re.IGNORECASE):
            change_type = 'patch'
        else:
            change_type = default_change_type

        if test_mode is True:
            print(f'TEST MODE:\nCommand to run:  semversioner add-change --type {change_type} --description "{message}"')
        else:
            add_change_command = f'semversioner add-change --type {change_type} --description "{message}"'
            subprocess_response = subprocess.run(add_change_command, shell=True, capture_output=True, text=True)
            if debug_mode is True:
                r_out = subprocess_response.stdout.rstrip()
                r_err = subprocess_response.stderr.rstrip()
                if r_err:
                    print(f"ERROR: {r_err}")
                else:
                    print(r_out)



def semversioner_clean_next_release(folder='.semversioner/next-release', action='backup'):
    """Cleans up next-release folder if it exists.  Can either backup or delete folder."""
    if os.path.exists(folder):
        if debug_mode is True:
            print(f"DEBUG: Folder found: {folder}")
        parent_folder = os.path.dirname(folder)
        if action == 'backup':
            timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            rename_folder = f"{parent_folder}/next-release.{timestamp}"
            if debug_mode is True:
                print(f"DEBUG: Backup Folder: {rename_folder}")
            if test_mode is True:
                #print(
                #    f"TEST MODE: {os.path.basename(folder)} would be renamed to {os.path.basename(rename_folder)} "
                #    f"in directory {os.path.commonpath([folder, rename_folder])}")
                print(
                    "TEST MODE: '{}' would be renamed to '{}' in directory '{}'".format(
                        os.path.basename(folder),
                        os.path.basename(rename_folder),
                        os.path.commonpath([folder, rename_folder])
                        )
                    )
            else:
                os.rename(folder,rename_folder)
        if action == 'delete':
            if test_mode is True:
                print(f"TEST MODE:  Will delete '{folder}' and contents.")
            else:
                for file in os.listdir(folder):
                    if debug_mode is True:
                        print(f"DEBUG: Removing file '{file}' from {folder}" )
                    os.remove(f"{folder}/{file}")
                os.rmdir(folder)
    else:
        if debug_mode is True:
            print(f"Folder NOT found: {folder}\n Nothing to clean.")



def get_git_repo_top_level():
    """Return the top level of the git repo."""
    get_top_level_command = 'git rev-parse --show-toplevel'
    subprocess_response = subprocess.run(get_top_level_command, shell=True, capture_output=True, text=True)
    #print(subprocess_response)
    git_repo_top_level = subprocess_response.stdout.strip()
    return git_repo_top_level



def set_default_change_type(branch_name):
    """Use the branch name to set the default type.

    Parameters
    ----------
    branch_name : string
        The name of the current branch to evaluate.

    Returns
    -------
    default_type : string
        The default change type determined by the branch.
        Returns 'None' if not determinable by branch name.

    """
    if re.match(r'^feature/.*$', branch_name, flags=re.IGNORECASE):
        default_type = 'minor'
    elif re.match(r'^[-A-Za-z]*fix/.*$', branch_name, flags=re.IGNORECASE):
        default_type = 'patch'
    else:
        default_type = None
        print("No default change type determined by branch. Branch should be "
              "prefixed by 'feature/' or '*fix/' in order to determine a "
              "release type.")

    return default_type


def get_git_commit_messages(this_branch, remote_branch='origin/master'):
    """We get commit messages and put into a list.

    Parameters
    ----------
    this_branch : string
        The current git branch.

    remote_branch : string
        The comparison git branch.

    Returns
    -------
    message_list : list
        Returns a list of messages if true
        If the value is none, exits with error message.

    """
    get_commit_messages_command = f'git --no-pager log --pretty=format:"%s" {remote_branch}..{this_branch}'
    subprocess_response = subprocess.run(get_commit_messages_command, shell=True, capture_output=True, text=True)
    #print(subprocess_response)
    message_list = subprocess_response.stdout.splitlines()
    # We want to reverse the order of messages so that the earlier changes are first.
    # This let's us create changelog info in a linear fashion.
    message_list.reverse()

    if message_list is None:
        print("Error generating list in get_git_commit_messages().")
        sys.exit(1)
    else:
        return message_list



def filter_message_list(messages, regex_filter_list=[]):
    """Filters the full list of messages so we don't include certain
    types like chore and merge messages into the changelog.

    Parameters
    ----------
    messages : list
        list of messages to process

    regex_filter_list : list
        A list of regex filters to apply to remove items from the messages
        list.  Each item in the list needs to be a raw string to be used
        correctly by the regex parser.

    Returns
    -------
    parsed_list : list
        A list of messages with elements that matched the regex list removed.

    """
    if len(regex_filter_list) == 0:
        # Include a basic filter list
        regex_filter_list = [
            r'^Merge branch.*$',
            r'^chore:.*$'
            ]
    if isinstance(messages, list):
        parsed_list = []
        for m in messages:
            matched = False
            for r in regex_filter_list:
                pattern = r
                if re.match(pattern, m, flags=re.IGNORECASE):
                    matched = True
                    if debug_mode is True:
                        print(f"Matches '{pattern}' filter:  '{m}'")
            if matched is False:
                parsed_list.append(m)
        return parsed_list
    else:
        print("Error: filter_message_list() only accepts a list as input")

def remove_dupe_messages(messages):
    """We want to preserve order in our change message list but not have duplicate messages.
    We could use set() but it doesn't preserve order so we need an alternate method.
    """
    if isinstance(messages, list):
        processed_list = [i for n, i in enumerate(messages) if i not in messages[:n]]
        return processed_list
    else:
        print("Error: remove_dupe_messages() only accepts a list as input")

def get_current_branch():
    """We get the current working branch here.
    """
    get_current_branch_command = 'git rev-parse --abbrev-ref HEAD'
    subprocess_response = subprocess.run(get_current_branch_command, shell=True, capture_output=True)
    current_branch = subprocess_response.stdout.decode('utf8').rstrip()
    return current_branch



def get_default_branch():
    """We get the default branch here.
    There is probably a better way to do this, or at least a way to work without assuming
    the remote is named 'origin' but this works for now.
    """
    get_default_branch_command = "git remote show origin | sed -n '/HEAD branch/s/.*: //p'"
    subprocess_response = subprocess.run(get_default_branch_command, shell=True, capture_output=True)
    default_branch =  subprocess_response.stdout.decode('utf8').rstrip()
    return default_branch


if __name__ == "__main__":  # Start the program
    main(sys.argv[1:])
