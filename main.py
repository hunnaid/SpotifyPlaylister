import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

def main():
    """
    Main function to run the updater
    """

    # load environment variables
    load_dotenv()

    print("starting...")

    # authenticate
    scope = "playlist-read-private playlist-modify-public playlist-modify-private"

    try:
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
        user = sp.current_user()
        print(f"Authenticated as {user['display_name']}")
    except Exception as e:
        print(f"Error during authentication: {e}")
        return

    # targets
    try:
        artist_name = os.getenv('ARTIST_NAME')
        playlist_id = os.getenv('PLAYLIST_ID')

        if not artist_name or not playlist_id:
            raise ValueError("ARTIST_NAME or PLAYLIST_ID environment variables are not set.")

        print(f"Target Artist: {artist_name}")
        print(f"Target Playlist ID: {playlist_id}")
    except ValueError as e:
        print(e)
        return

    print(f"Target Artist: {artist_name}")
    print(f"Target Playlist ID: {playlist_id}")

    # fetch existing songs
    existing_track_ids = set()

    results = sp.playlist_items(playlist_id, fields='items.track.id,next')
    tracks = results['items']

    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])

    for item in tracks:
        if item['track'] and item['track']['id']:
            existing_track_ids.add(item['track']['id'])

    # fetch all tracks for artist
    search_result = sp.search(q=f'artist:{artist_name}', type='artist', limit=1)

    if not search_result['artists']['items']:
        print(f"No artist found with name {artist_name}")
        return
    artist_id = search_result['artists']['items'][0]['id']
    print(f"Found artist ID: {artist_id}")

    # get all albums
    artist_albums = []
    results = sp.artist_albums(artist_id, album_type='album,single', limit=50)
    artist_albums.extend(results['items'])

    while results['next']:
        results = sp.next(results)
        artist_albums.extend(results['items'])

    # compare and filter for new songs
    all_artist_track_ids = set()
    for album in artist_albums:
        album_id = album['id']
        album_tracks = sp.album_tracks(album_id, limit=50)['items']

        for track in album_tracks:
            all_artist_track_ids.add(track['id'])

    tracks_to_add_ids = list(all_artist_track_ids - existing_track_ids)

    # add new songs to the playlist
    if not tracks_to_add_ids:
        print("No new tracks to add.")
    else:
        for i in range(0, len(tracks_to_add_ids), 100):
            batch = tracks_to_add_ids[i:i + 100]
            try:
                sp.playlist_add_items(playlist_id, batch)
            except Exception as e:
                print(f"Error adding tracks to playlist: {e}")
                return

    print("update done.")


if __name__ == "__main__":
    main()
