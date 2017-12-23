"""Finds out all the people you need to follow to follow all the same people as another user. Then, optionally, follows them for you."""
import configparser
import csv

import tweepy
from tqdm import tqdm

# Getting API Keys

CONFIG = configparser.ConfigParser()
CONFIG.read("secrets.ini")

# Gonna have to get ur own keys to use this
API_KEY = CONFIG["API KEYS"]["ConsumerKey"]
API_SECRET = CONFIG["API KEYS"]["ConsumerSecret"]

# https://gist.github.com/garrettdreyfus/8153571
def yes_or_no(question):
    while "the answer is invalid":
        reply = str(input(question + ' (y/n): ')).lower().strip()
        if reply[0] == 'y':
            return True
        if reply[0] == 'n':
            return False


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
def two_lists_to_csv(list1, list2, filename):
    with open(filename, 'w') as csv_file:
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
    for chunk in tqdm(chunks(ids, 100)):
        usernames += get_100_usernames(chunk)
    return usernames

# https://codereview.stackexchange.com/a/101947
def get_list_of_friends(target_id):
    ids = []
    for friend in tqdm(tweepy.Cursor(API.friends_ids, id=target_id).items()):
        ids.append(friend)
    return ids


TARGET = API.get_user(input("Target Username (who we'll be copying from): "))

print("Getting List of Friends (Following) of Target...")
TARGET_FRIEND_IDS = get_list_of_friends(TARGET)

print("Converting IDs to names...")
TARGET_FRIEND_NAMES = get_usernames(TARGET_FRIEND_IDS)

print("Saving to CSV...")
two_lists_to_csv(TARGET_FRIEND_IDS, TARGET_FRIEND_NAMES,
                 "./output/targetfriends.csv")

print("Getting List of Your Friends (Following)...")
YOUR_FRIEND_IDS = get_list_of_friends(API.me().id)

print("Converting IDs to names...")
YOUR_FRIEND_IDS = get_usernames(YOUR_FRIEND_IDS)

print("Saving to CSV...")
two_lists_to_csv(YOUR_FRIEND_IDS, YOUR_FRIEND_IDS, "./output/yourfriends.csv")

print("Subtracting who you've already followed...")
DIFF_FRIEND_IDS = [f for f in TARGET_FRIEND_IDS if f not in YOUR_FRIEND_IDS]

print("Converting ids to names...")
DIFF_FRIEND_NAMES = get_usernames(YOUR_FRIEND_IDS)

print("Saving to CSV...")
two_lists_to_csv(DIFF_FRIEND_IDS, DIFF_FRIEND_NAMES, "./output/diffriends.csv")

print(TARGET_FRIEND_IDS)
print("To follow everyone that Target follows, you need to follow:\n\n\n" +
      "\n@".join(TARGET_FRIEND_NAMES))
print("At some point your account may be limited and unable to follow any more people. Probably will go away.  ¯\_(ツ)_/¯")
if yes_or_no("Are you sure you want to (try to) follow %s users?" % len(DIFF_FRIEND_IDS)):
    print("Begin following.")
    for followtuple in zip(tqdm(DIFF_FRIEND_IDS), DIFF_FRIEND_NAMES):
        user_id, name = followtuple
        tqdm.write("Following @" + name + "...")
        API.create_friendship(user_id)
