import datetime
import hashlib
import requests


AUTH_URL = 'http://api.myshows.ru/profile/login?login={username}&password={password_md5}'
SHOWS_URL = 'http://api.myshows.ru/profile/shows/'
SHOW_URL = 'http://api.myshows.ru/shows/{show_id}'
EPISODES_URL = 'http://api.myshows.ru/profile/shows/{show_id}/'


def authenticate(session, username, password):
    md5 = hashlib.md5(password).hexdigest()
    res = session.get(AUTH_URL.format(username=username, password_md5=md5))
    res.raise_for_status()


def load(username, password):
    session = requests.session()

    authenticate(session, username, password)
    shows = session.get(SHOWS_URL).json()
    all_episodes = []
    shows_count = 0
    for show in shows.values():
        show_id = show['showId']
        show_data = session.get(SHOW_URL.format(show_id=show_id)).json()
        episodes = session.get(EPISODES_URL.format(show_id=show_id)).json()
        if not episodes:
            continue

        for watched_episode in episodes.values():
            episode_id = watched_episode['id']
            try:
                data = show_data['episodes'][str(episode_id)]
            except KeyError:
                data = {'title': '', 'seasonNumber': '', 'episodeNumber': ''}

            watched = datetime.datetime.strptime(watched_episode['watchDate'],
                                                 '%d.%m.%Y').date()
            item = (show_id, show_data['title'], show_data['year'],
                    episode_id, data['title'], data['seasonNumber'],
                    data['episodeNumber'], watched.isoformat())
            all_episodes.append(item)
        shows_count += 1
    all_episodes.sort(key=lambda i: i[-1])

