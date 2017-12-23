# Migrate Twitter "Friends"
A repository for migrating the list of people you follow (friends) from one account to another.

**Note: For some reason twitter calls people who you follow "Friends" so I'll do that too.**

## Setup
0. Clone this repo to your computer and stuff.
1. Go to apps.twitter.com
2. Make an app with read write permissions
3. Get the consumer key and secret
4. Make a new file called `secrets.ini` with these contents: 
  ```
  [API KEYS]
  ConsumerKey = [INSERT CONSUMER KEY]
  ConsumerSecret = [INSERT CONSUMER SECRET]
  ```
5. Add your key and secret into it.

## Usage
1. Run it.
2. Go to the displayed web address, 
3. Log in to the twitter account you want to migrate your Friends to. 
4. Press authorize
5. Get the code, and paste it in to the command line when it asks for it.
6. When it asks for the target username, enter the username (minus the "@") that you want to migrate Friends from.
7. Wait and hope the gods of twitter don't rate limit you 🤞

## Dependencies 
* [Tweepy](https://github.com/tweepy/tweepy) for twittering
* [TQDM](https://github.com/tqdm/tqdm) for pretty pretty progress bars
