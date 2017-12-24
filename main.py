"""Finds out all the people you need to follow to follow all the same people as another user. Then, optionally, follows them for you."""
import configparser
import csv
import errno
import os

import tweepy
from tqdm import tqdm

#Useful Constants
PATH_TO_TARGET_CSV = "./output/targetfriends.csv"
PATH_TO_USER_CSV = "./output/yourfriends.csv"
PATH_TO_DIFF_CSV = "./output/difffriends.csv"

# Getting API Keys

SECRETS = configparser.ConfigParser()
SECRETS.read("secrets.ini")

# Gonna have to get ur own keys to use this
API_KEY = SECRETS["API KEYS"]["ConsumerKey"]
API_SECRET = SECRETS["API KEYS"]["ConsumerSecret"]

# https://gist.github.com/garrettdreyfus/8153571
def yes_or_no(question):
    while "the answer is invalid":
        reply = str(input(question + ' (y/n): ')).lower().strip()
        if reply[0] == 'y':
            return True
        if reply[0] == 'n':
            return False

#Creating Folders
#https://stackoverflow.com/a/273227
try:
    os.makedirs("./output")
except OSError as e:
    if e.errno != errno.EEXIST:
        raise

# Setting Up API
AUTH = tweepy.OAuthHandler(API_KEY, API_SECRET, 'oob')
REDIRECT_URL = AUTH.get_authorization_url()
print("Go to " + REDIRECT_URL +
      " and sign in on the account you want to transfer your Following list to.")
API = tweepy.API(AUTH, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
AUTH.get_access_token(input("Enter the key that comes up here: "))

# https://stackoverflow.com/a/19302732
def list_to_csv(list_to_dump, filename):
    with open(filename, "w") as output:
        writer = csv.writer(output, lineterminator='\n')
        for val in list_to_dump:
            writer.writerow([val])

# https://stackoverflow.com/a/19302732
def two_lists_to_csv(header, in_list1, in_list2, filename):
    list1 = [header] + in_list1
    list2 = [" "] + in_list2
    with open(filename, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerows(zip(list1, list2))

# Wrote this one myself actually. It's for debugging.
def check_limits():
    limits = API.rate_limit_status()['resources']
    for category_name in limits:
        category = limits[category_name]
        for item_name in category:
            item = limits[category_name][item_name]
            if item['limit'] != item['remaining']:
                print(item_name, item)

# https://stackoverflow.com/a/312464
def chunks(my_list, len_of_chunk):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(my_list), len_of_chunk):
        yield my_list[i:i + len_of_chunk]

# https://stackoverflow.com/a/39320334
def get_100_usernames(list_of_ids):
    """ can only do lookup in steps of 100;
        so 'ids' should be a list of 100 ids
    """
    user_objs = API.lookup_users(user_ids=list_of_ids)
    return [user.screen_name for user in user_objs]

# This one too
def get_usernames(ids):
    usernames = []
    for chunk in tqdm(chunks(ids, 100), unit="hundred names"):
        usernames += get_100_usernames(chunk)
    return usernames

# Wow, this one as well
def retrieve_usernames(list_of_ids, dict_of_ids_to_names):
    """
    For retrieving usernames when we've already gotten them from twitter.
    For saving on API requests
    """
    usernames = []
    for user_id in list_of_ids:
        usernames.append(dict_of_ids_to_names[user_id])
    return usernames

# https://codereview.stackexchange.com/a/101947
def get_list_of_friends(target_id):
    ids = []
    for friend in tqdm(tweepy.Cursor(API.friends_ids, id=target_id).items(), unit="Friend"):
        ids.append(friend)
    return ids

def _check_csv_header_(filename, text_to_check_for):
    try:
        with open(filename) as csvfile:
            if list(csv.reader(csvfile))[0][0] == text_to_check_for:
                return True
            return False
    except IOError:
        return False


def detect_progress(name_of_target, name_of_user):
    """
    Returns Tuple (is_target_finished, is_user_finished, is_diff_finished)
    """
    is_target_finished = _check_csv_header_(PATH_TO_TARGET_CSV, name_of_target)
    is_user_finished = _check_csv_header_(PATH_TO_USER_CSV, name_of_user)
    is_diff_finished = _check_csv_header_(PATH_TO_DIFF_CSV, name_of_target + " - " + name_of_user)
    return (is_target_finished, is_user_finished, is_diff_finished)

def restore_progress(filename):
    """
    Returns
    -------
    id_list : list
        List of ids restored from the CSV
    name_list : list
        List of names restored from the CSV
    """
    with open(filename) as csvfile:
        csvfile = csv.reader(csvfile)
        csvfile = list(map(list, zip(*csvfile))) #https://stackoverflow.com/a/6473724 Transposing lists
        id_list = csvfile[0][1:]
        id_list = [int(s) for s in id_list]
        name_list = csvfile[1][1:]
        return id_list, name_list

TARGET = input("Target Username (who we'll be copying from): ")
MY_SCREEN_NAME = API.me().screen_name
PROGRESS = detect_progress(TARGET, MY_SCREEN_NAME)
USE_PROGRESS = yes_or_no("Should we use progress from last time? (Choose no if the target has followed anyone since last time or you haven't run this before)")
if not PROGRESS[0] or not USE_PROGRESS: #If we haven't already finished getting friends from the target 
    print("Getting List of Friends (Following) of Target...")
    TARGET_FRIEND_IDS = get_list_of_friends(TARGET)

    print("Converting IDs to names...")
    TARGET_FRIEND_NAMES = get_usernames(TARGET_FRIEND_IDS)

    print("Saving to CSV...")
    two_lists_to_csv(TARGET, TARGET_FRIEND_IDS, TARGET_FRIEND_NAMES, PATH_TO_TARGET_CSV)
else:
    print("Restoring Progress on Target...")
    TARGET_FRIEND_IDS, TARGET_FRIEND_NAMES = restore_progress(PATH_TO_TARGET_CSV)

#Save names for later
NAMES_DICT = dict(zip(TARGET_FRIEND_IDS, TARGET_FRIEND_NAMES))

print("Getting List of Your Friends (Following)...")
YOUR_FRIEND_IDS = get_list_of_friends(API.me().id)

print("Converting IDs to names...")
YOUR_FRIEND_NAMES = get_usernames(YOUR_FRIEND_IDS)

print("Saving to CSV...")
two_lists_to_csv(MY_SCREEN_NAME, YOUR_FRIEND_IDS, YOUR_FRIEND_NAMES, PATH_TO_USER_CSV)

print("Subtracting who you've already followed...")
DIFF_FRIEND_IDS = [f for f in TARGET_FRIEND_IDS if f not in YOUR_FRIEND_IDS]

print("Converting ids to names...")
DIFF_FRIEND_NAMES = retrieve_usernames(DIFF_FRIEND_IDS, NAMES_DICT)

print("Saving to CSV...")
two_lists_to_csv(TARGET+" - "+MY_SCREEN_NAME,DIFF_FRIEND_IDS, DIFF_FRIEND_NAMES, "./output/diffriends.csv")

print(TARGET_FRIEND_IDS)
print("To follow everyone that Target follows, you need to follow:\n\n\n" +
      "\n@".join(DIFF_FRIEND_NAMES))
print("At some point your account may be limited and unable to follow any more people. Probably will go away.  ¯\\_(ツ)_/¯")
if yes_or_no("Are you sure you want to (try to) follow %s users?" % len(DIFF_FRIEND_IDS)):
    print("Begin following.")
    for followtuple in zip(tqdm(DIFF_FRIEND_IDS, unit="Friend"), DIFF_FRIEND_NAMES):
        user_id, name = followtuple
        tqdm.write("Following @" + name + "...")
        API.create_friendship(user_id)
