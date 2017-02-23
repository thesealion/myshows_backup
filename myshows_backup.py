from collections import OrderedDict
import datetime
import getpass
import hashlib
import json
import requests
import sys


API_ROOT = 'http://api.myshows.ru'
AUTH_URL = '/profile/login?login={username}&password={password_md5}'
SHOWS_URL = '/profile/shows/'
SHOW_URL = '/shows/{show_id}'
EPISODES_URL = '/profile/shows/{show_id}/'


def authenticate(session, username, password):
    md5 = hashlib.md5(password).hexdigest()
    res = session.get(AUTH_URL.format(username=username, password_md5=md5))
    res.raise_for_status()


def load(username, password):
    session = requests.session()
    session._get = session.get
    session.get = lambda url: session._get(API_ROOT + url)

    authenticate(session, username, password)
    data = session.get(SHOWS_URL).json()
    total = len(data)
    shows = []
    for n, show in enumerate(data.values(), 1):
        show_id = show['showId']
        show_data = session.get(SHOW_URL.format(show_id=show_id)).json()
        episodes = session.get(EPISODES_URL.format(show_id=show_id)).json()
        if not episodes:
            continue

        show = OrderedDict([('id', show_id), ('title', show_data['title']),
                            ('year', show_data['year']), ('episodes', [])])
        for watched_episode in episodes.values():
            episode_id = watched_episode['id']
            try:
                data = show_data['episodes'][str(episode_id)]
            except KeyError:
                data = {'title': '', 'seasonNumber': '', 'episodeNumber': ''}

            watched = datetime.datetime.strptime(watched_episode['watchDate'],
                                                 '%d.%m.%Y').date()
            item = OrderedDict([('id', episode_id), ('title', data['title']),
                                ('season', data['seasonNumber']),
                                ('number', data['episodeNumber']),
                                ('watched', watched.isoformat())])
            show['episodes'].append(item)
        show['episodes'].sort(key=lambda e: e['watched'])
        shows.append(show)
        sys.stderr.write('Getting shows: %d/%d\r' % (n, total))
    sys.stderr.write('\n')
    shows.sort(key=lambda show: show['episodes'][0]['watched'])
    return shows


if __name__ == '__main__':
    try:
        username = sys.argv[1]
    except IndexError:
        raise Exception('Usage: %s <username>' % sys.argv[0])
    password = getpass.getpass('Password for %s:' % username)
    data = load(username, password)
    json.dump(data, sys.stdout, indent=2)
