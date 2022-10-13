import requests
from pprint import pprint
from copy import deepcopy
import math
from functools import reduce
import time
import sys
from datetime import datetime

# Pre-reqs
# 1. Install python: https://www.python.org/downloads/
# 2. Install the `requests` library on command line with `pip install requests`

# Steps
# 1. Press Ctrl+S/Cmd+S to download this file
# 2. Get your authentication (OAuth) tokens using the directions below
# 3. Update the variables `PREV_ACCOUNT_AUTH` and `CURR_ACCOUNT_AUTH` with the auth tokens that you obtained 
# 4. Go to the bottom of the file and uncomment the line for adding your liked songs from the old account to new account
# 5, Run this file. `python transfer_tracks.py`
# 6. Follow instructions that pop up when you run the program

# OAuth token for getting liked songs 
# Steps:
# 1. Log into https://open.spotify.com/ with your old account
# 2. Obtain OAuth token here: https://developer.spotify.com/console/get-current-user-saved-tracks/
# 3. Click `Get Token`, select the option for `user-library-read`
# 4. Copy the token to the text below
PREV_ACCOUNT_AUTH = "replace this text between quotes with auth token for your old account"

# OAuth token for setting liked songs
# Steps:
# 1. Log into https://open.spotify.com/ with your old account
# 2. Obtain OAuth token here: https://developer.spotify.com/console/put-current-user-saved-tracks/
# 3. Click `Get Token`, select the option for `user-library-modify`
# 4. Copy the token to the text below
CURR_ACCOUNT_AUTH = "replace this text between quotes with auth token for your new account"


# Toggles on testing mode. Set to true to not modify user accounts
TESTING = False

# Deletes the last n lines in the STDOUT
def delete_prints(n=1):
    for _ in range(n):
        sys.stdout.write("\x1b[1A")  # cursor up one line
        sys.stdout.write("\x1b[2K")  # delete the last line


# Returns headers for using Spotify API
def get_headers(auth):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'
    }
    headers['Authorization'] = headers['Authorization'].format(auth)
    return headers 


# Gets liked tracks from a user's account
# Returns a list of (song_id, song_name) tuples
def get_liked_tracks(auth=PREV_ACCOUNT_AUTH, limit=50):
    get_liked_tracks_url = 'https://api.spotify.com/v1/me/tracks?market=US&limit={}&offset={}' 

    liked_tracks = []
    headers = get_headers(auth)
    url = get_liked_tracks_url.format(limit, 0)
    while True: 
        if url is None:
            break
        
        print('Found {} tracks'.format(len(liked_tracks)))
        
        output = requests.get(url, headers=headers)
        if output.status_code != 200:
            print('ERROR: Failed to fetch liked tracks: url={} response={}'.format(url, output.text))
            return []

        json_response = output.json()
        for track_data in json_response['items']:
            id = track_data['track']['id']
            name = track_data['track']['name']
            liked_tracks.append((id, name))
        
        url = json_response['next']
        delete_prints(n=1)

    liked_tracks.reverse()

    print()
    print('Completed finding liked tracks')
    print('Total tracks found: {}'.format(len(liked_tracks)))
    print('Oldest track: {}'.format(liked_tracks[0][1]))
    print('Newest track: {}'.format(liked_tracks[-1][1]))
    print()

    current_date = datetime.now().strftime("%Y%m%d-%H:%M:%S")
    with open('liked_songs_{}.txt'.format(current_date), 'w') as f:
        for track in liked_tracks:
            f.write('{}\t{}\n'.format(track[0], track[1]))

    return liked_tracks


# Takes in a list of (song_id, song_name) tuples and either sets or deletes them from a user's account
def modify_liked_tracks(tracks, auth, limit=50, sleep_duration=None, set_tracks=False, delete_tracks=False):
    modify_liked_tracks_url = 'https://api.spotify.com/v1/me/tracks?ids={}'
    
    # setting auth token
    headers = get_headers(auth)
    num_bins = math.ceil(len(tracks) / limit)
    for i in range(num_bins):
        start_idx = i*limit
        end_idx = (i+1)*limit

        print("Modifying liked songs. Progress: {:0.2f}%".format((start_idx * 100) / len(tracks)))

        # a list of `limit` number of tracks
        tracks_subset = tracks[start_idx:end_idx]
        
        ids = list(map(lambda track_info: track_info[0], tracks_subset))
        formatted_ids = reduce(lambda x, y: x + '%2C' + y, ids)
        url = modify_liked_tracks_url.format(formatted_ids)

        
        if not TESTING and set_tracks:
            output = requests.put(url, headers=headers)
        
        if not TESTING and delete_tracks:
            output = requests.delete(url, headers=headers)

        if not TESTING and output.status_code != 200:
            print('ERROR: Failed to set liked tracks: {}'.format(output.text))
            return False 
        
        # need slight delay because the PUT request returning a status code is async from when the song gets added to the Liked Songs list 
        # without the delay some songs will get added in the wrong order
        if sleep_duration:
            time.sleep(sleep_duration)

        delete_prints(n=1)
    
    return True


def set_liked_tracks(sleep_duration, auth=CURR_ACCOUNT_AUTH):
    prev_liked_tracks = get_liked_tracks()
    
    should_continue = input('If the following looks correct, enter `yes` to continue. Enter anything else to exit the program.\n')
    print()

    if should_continue != 'yes':
        print('User did not input `yes`. Exiting program')
        return
        
    success = modify_liked_tracks(prev_liked_tracks, auth, limit=1, sleep_duration=sleep_duration, set_tracks=True)
    if success:
        print('Completed adding tracks to liked songs')
        print('If the song order looks incorrect, re-run this and use a longer duration to wait between adding songs')


def delete_liked_tracks(auth=CURR_ACCOUNT_AUTH):
    prev_liked_tracks = get_liked_tracks()
    
    should_continue = input('If the following looks correct, enter `yes` to continue. Enter anything else to exit the program.\n')
    print()

    if should_continue != 'yes':
        print('User did not input `yes`. Exiting program')
        return

    success = modify_liked_tracks(prev_liked_tracks, auth, delete_tracks=True)
    if success:
        print('Completed deleting tracks from liked songs')


ADD_SELECTION = 'add'
DELETE_SELECTION = 'delete'
if __name__ == '__main__':
    if TESTING:
        print('Currently in testing mode')

    user_selection = input('Type "add" and then enter to add songs from old account to new account.\nType "delete" and then enter to remove the songs you added from the old account.\nEnter anything else to exit the program.\n').strip()
    print()

    if user_selection != ADD_SELECTION and user_selection != DELETE_SELECTION:
        print('Exiting program')
        exit()

    
    # the next few lines deletes the liked songs you've added from your old account 
    if user_selection == DELETE_SELECTION:
        delete_liked_tracks()

    # the rest of the code below adds the liked songs from your old account to your new account. 
    # if you see songs getting added in the wrong order, re-run the code and select "delete" to delete all the songs
    # then run the code again and select "add" and use a higher wait duration
    if user_selection == ADD_SELECTION:
        duration = input('Optional: Enter a number (in seconds) to specify the duration to wait between adding songs.\nThe longer the wait, the more likely your songs will be added in the correct order.\nPress enter to use default value of 0.2 seconds.\n')
        print()

        try:
            duration = float(duration)
        except:
            print('Unable to convert your input to a number. Using default value of 0.2 seconds')
            duration = 0.2

        set_liked_tracks(sleep_duration=duration)

