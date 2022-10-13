import requests
from pprint import pprint
from copy import deepcopy
import math
from functools import reduce
import time


# Pre-reqs
# 1. Install python: https://www.python.org/downloads/
# 2. Install the `requests` library on command line with `pip install requests`

# Steps
# 1. Get your authentication (OAuth) tokens using the directions below
# 2. Update the variables `prev_account_auth` and `curr_account_auth` with the auth tokens that you obtained 
# 2. Go to the bottom of the file and uncomment the line for adding your liked songs from the old account to new account
# 3, Run this file. `python transfer_tracks.py`
# 4. Follow instructions that pop up when you run the program
# 5. If there are errors, let me know

# OAuth token for getting liked songs 
# obtain OAuth token here: https://developer.spotify.com/console/get-current-user-saved-tracks/
# click `Get Token`, select the option for `user-library-read`, and copy the token here
# make sure you are logged in with your ```old``` account on the Spotify website when you get the token 
prev_account_auth = 'replace me with auth token for old account'

# OAuth token for setting liked songs
# obtain OAuth token here: https://developer.spotify.com/console/put-current-user-saved-tracks/
# click `Get Token`, select the option for `user-library-modify`, and copy the token here
# make sure you are logged in with your ```new``` account on the Spotify website when you get the token 
curr_account_auth = 'replace me with auth token for new account'


def get_headers(auth):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'
    }
    headers['Authorization'] = headers['Authorization'].format(auth)
    return headers 


def get_liked_tracks(auth=prev_account_auth, limit=50):
    get_liked_tracks_url = 'https://api.spotify.com/v1/me/tracks?market=US&limit={}&offset={}' 

    liked_tracks = []
    headers = get_headers(auth)
    url = get_liked_tracks_url.format(limit, 0)
    while True: 
        if url is None:
            break

        output = requests.get(url, headers=headers)
        json_response = output.json()
        if output.status_code != 200:
            print('ERROR: Failed to fetch liked tracks: url={} response={}'.format(url, json_response))
            return []

        for track_data in json_response['items']:
            id = track_data['track']['id']
            name = track_data['track']['name']
            liked_tracks.append((id, name))
        
        url = json_response['next']
        print('Found {} tracks'.format(len(liked_tracks)))

    liked_tracks.reverse()

    print()
    print('Completed finding liked tracks')
    print('Total tracks found: {}'.format(len(liked_tracks)))
    print('Oldest track: {}'.format(liked_tracks[0]))
    print('Newest track: {}'.format(liked_tracks[-1]))
    print()

    return liked_tracks


def modify_liked_tracks(tracks, auth, limit=50, sleep_duration=None, set_tracks=False, delete_tracks=False):
    modify_liked_tracks_url = 'https://api.spotify.com/v1/me/tracks?ids={}'
    
    # setting auth token
    headers = get_headers(auth)
    
    num_bins = math.ceil(len(tracks) / limit)
    for i in range(num_bins):
        start_idx = i*limit
        end_idx = (i+1)*limit
        print("Sending tracks [{}-{}). set={}, delete={}".format(start_idx, end_idx, set_tracks, delete_tracks))

        # a list of `limit` number of tracks
        tracks_subset = tracks[start_idx:end_idx]
        
        ids = list(map(lambda track_info: track_info[0], tracks_subset))
        formatted_ids = reduce(lambda x, y: x + '%2C' + y, ids)
        url = modify_liked_tracks_url.format(formatted_ids)

        
        if set_tracks:
            output = requests.put(url, headers=headers)
        
        if delete_tracks:
            output = requests.delete(url, headers=headers)

        if output.status_code != 200:
            print('ERROR: Failed to set liked tracks: {}'.format(output.text))
            return False 
        
        # need slight delay because the PUT request returning a status code is async from when the song gets added to the Liked Songs list 
        # without the delay some songs will get added in the wrong order
        if sleep_duration:
            time.sleep(sleep_duration)
    
    return True


def set_liked_tracks(tracks, sleep_duration, auth=curr_account_auth):
    success = modify_liked_tracks(tracks, auth, limit=1, sleep_duration=sleep_duration, set_tracks=True)
    if success:
        print('Completed adding tracks to liked songs')
        print('If the song order looks incorrect, re-run this and use a longer duration to wait between adding songs')


def delete_liked_tracks(tracks, auth=curr_account_auth):
    success = modify_liked_tracks(tracks, auth, delete_tracks=True)
    if success:
        print('Completed deleting tracks from liked songs')


ADD_SELECTION = 'add'
DELETE_SELECTION = 'delete'
if __name__ == '__main__':
    user_selection = input('Type "add" and then enter to add songs from old account to new account.\nType "delete" and then enter to remove the songs you added from the old account.\nEnter anything else to exit the program.\n').strip()
    print()

    if user_selection != ADD_SELECTION and user_selection != DELETE_SELECTION:
        print('Exiting program')
        exit()

    
    # the next few lines deletes the liked songs you've added from your old account 
    if user_selection == DELETE_SELECTION:
        prev_liked_tracks = get_liked_tracks()
        delete_liked_tracks(prev_liked_tracks, curr_account_auth)

    # the rest of the code below adds the liked songs from your old account to your new account. 
    # if you see songs getting added in the wrong order, re-run the code and select "delete" to delete all the songs
    # then run the code again and select "add" and use a higher wait duration
    duration = input('Optional: Enter a number (in seconds) to specify the duration to wait before adding another song.\nThe longer the wait, the more likely your songs will be added in the correct order.\nPress enter to use default value of 0.2 seconds.\n')
    print()

    try:
        duration = float(duration)
    except:
        print('Unable to convert your input to a number. Using default value of 0.2 seconds')
        duration = 0.2

    if user_selection == ADD_SELECTION:
        prev_liked_tracks = get_liked_tracks()
        set_liked_tracks(prev_liked_tracks, sleep_duration=duration)

