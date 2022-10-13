import requests
from pprint import pprint
from copy import deepcopy
import math
from functools import reduce
import time

# Pre-reqs
# 1. Install python
# 2. Install requests on command line with `pip install requests`

# Steps
# 1. Get your auth tokens using the directions below
# 2. Go to the bottom of the file and uncomment the line for adding your liked songs from the old account to new account
# 3, Run this file `python transfer_tracks.py`
# 4. If you need to delete the liked songs you've transfered from your old account, then uncomment the line at the bottom of the file to delete your liked songs and re-comment out the line for adding liked songs

# OAuth token for getting liked songs 
# obtain OAuth here: https://developer.spotify.com/console/get-current-user-saved-tracks/
# click `Get Token`, select the option for `user-library-read`, and copy the token here
# make sure you are logged in with your ```old``` account on the Spotify website when you get the token 
prev_account_auth = 'replace me with auth token for old account'

# OAuth token for setting liked songs
# obtain OAuth here: https://developer.spotify.com/console/put-current-user-saved-tracks/
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


def get_liked_tracks(auth, limit=50):
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

    # pprint(liked_tracks)
    liked_tracks.reverse()
    print('Found {} tracks'.format(len(liked_tracks)))
    print('Oldest track: {}'.format(liked_tracks[0]))
    print('Newest track: {}'.format(liked_tracks[-1]))
    return liked_tracks


def modify_liked_tracks(tracks, auth, limit=50, sleep_duration=None, set_tracks=False, delete_tracks=False):
    modify_liked_tracks_url = 'https://api.spotify.com/v1/me/tracks?ids={}'
    
    # setting auth token
    headers = get_headers(auth)
    
    num_bins = math.ceil(len(tracks) / limit)
    for i in range(num_bins):
        start_idx = i*limit
        end_idx = (i+1)*limit
        print("Sending tracks {}-{}. set={}, delete={}".format(start_idx+1, end_idx, set_tracks, delete_tracks))

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
            return 
        
        # need slight delay because the PUT request returning a status code is async from when the song gets added to the Liked Songs list 
        # without the delay some songs will get added in the wrong order
        if sleep_duration:
            time.sleep(sleep_duration)
        
    print('Completed adding tracks to liked songs')


def set_liked_tracks(tracks, auth, sleep_duration=0.1):
    modify_liked_tracks(tracks, auth, limit=1, sleep_duration=sleep_duration, set_tracks=True)


def delete_liked_tracks(tracks, auth):
    modify_liked_tracks(tracks, auth, delete_tracks=True)


if __name__ == '__main__':
    prev_liked_tracks = get_liked_tracks(prev_account_auth)
    
    # uncomment the line below to add the liked songs from your old account to your new account. if you see songs getting added in the wrong order, run `delete_liked_tracks()` to delete all the songs, and then re-run `set_liked_tracks()` with a higher `sleep_duration`. default value is 0.1s
    # set_liked_tracks(prev_liked_tracks, curr_account_auth, sleep_duration=0.1)

    # uncomment the line below to delete the liked songs you've added from your old account 
    # delete_liked_tracks(prev_liked_tracks, curr_account_auth)
    
