import requests
from lxml import html
from fuzzywuzzy import fuzz
import datetime

CHARTS_BASE_URL = "https://www.officialcharts.com"
CHARTS_SEARCH_ARTIST_URL_BASE = CHARTS_BASE_URL+"/search/artists"
CHARTS_SEARCH_TITLE_URL_BASE = CHARTS_BASE_URL+"/search/singles"


class Song:
    name = u""
    artist = u""
    peak_pos = 0
    date = datetime.datetime(1901, 1, 1)
    name_confidence = 0
    artist_confidence = 0
    avg_confidence = 0

    def __init__(self):
        pass


def retrieveSongs(artist_name, song_name):
    songs = []
    artist_url = retrieveArtistLink(artist_name)
    if artist_url:
        songs = parseArtistSearchSongs(artist_url)

    else:
        print "\tCouldn't find artist in charts, attempting song name search"
        songs = retrieveTitleSearchSongs(song_name)

    for song in songs:
        song.name_confidence = fuzz.ratio(song_name.lower(), song.name.lower())
        song.artist_confidence = fuzz.ratio(
            artist_name.lower(), song.artist.lower())

        # Put more emphasis on the song name matching
        song.avg_confidence = (song.artist_confidence+song.name_confidence*2)/3

    return songs


def retrieveTitleSearchSongs(song_name):
    title_search_url = "{}/{}".format(CHARTS_SEARCH_TITLE_URL_BASE,
                                      requests.utils.quote(song_name))
    print "\tSearching at {}".format(title_search_url)
    page_data = requests.get(title_search_url)
    tree = html.fromstring(page_data.content)
    # This is the main results table container
    singles_table = tree.find_class('chart-results-content')[0]

    singles_entries = [s for s in singles_table.getchildren()
                       if s.tag == "tr" and not s.get('class')]

    songs_found = []
    for entry in singles_entries:
        song = Song()
        try:
            song.artist = entry.find_class('artist')[0].xpath('a')[
                0].text.strip()
            song.name = entry.find_class('title')[0].xpath('a')[0].text.strip()
            song.peak_pos = int(entry.find_class('position')[0].text.strip())

            date = entry.find_class('date')[0]
            date_text = ""
            for text in date.itertext():
                date_text = date_text+text.strip()
            song.date = datetime.datetime.strptime(date_text, '%d.%m.%Y')

            songs_found.append(song)
        except:
            pass
            # print "Found non-song tr block"

    return songs_found


def retrieveArtistLink(artist_name):
    sanitized_artist_name = artist_name.replace(
        '&', '_and_ ').replace(' and ', ' ')
    artist_search_url = CHARTS_SEARCH_ARTIST_URL_BASE + "/" + requests.utils.quote(
        sanitized_artist_name)
    print "\tSearching at {}".format(artist_search_url)
    page_data = requests.get(CHARTS_SEARCH_ARTIST_URL_BASE + "/" + requests.utils.quote(
        sanitized_artist_name))
    tree = html.fromstring(page_data.content)

    artist_lis = []
    try:
        artist_list_divs = tree.find_class(
            'search-results-artist-list')[0].xpath('div')[0]

        for ul in artist_list_divs.xpath('div/ul[1]'):
            artist_lis.extend([li for li in ul.getchildren()])
    except:
        return None

    # Sometimes there are multiple artists listed for a query,
    # so we'll find the one that's a closest match
    artist_entries = []
    for li in artist_lis:
        a = li.xpath('a')[0]
        artist_text = a.text.strip()
        artist_href = a.get('href').strip()
        artist_entries.append(
            (artist_text, artist_href, fuzz.ratio(artist_name.lower(), artist_text.lower())))

    if not artist_entries:
        return None

    artist_entries = sorted(
        artist_entries, key=lambda entry: entry[2], reverse=True)

    print "\tUsing best guess '{}' as artist name, {}% confidence".format(
        artist_entries[0][0], artist_entries[0][2])
    return "{}{}".format(CHARTS_BASE_URL, artist_entries[0][1])


def parseArtistSearchSongs(artist_page_uri):
    page_data = requests.get(artist_page_uri)
    tree = html.fromstring(page_data.content)
    songs_tbl_body = tree.find_class('artist-products')[0]

    # There are actually several rows per song entry, and some are hidden
    # The one we're interested in doesn't have any classes applied
    els = [el for el in songs_tbl_body if not el.get('class')]

    songs = []
    for entry in els:
        try:
            song = Song()
            song.name = entry.xpath('td[2]/div/div[2]/div/a')[0].text.strip()
            song.peak_pos = int(entry.xpath('td[3]/span')[0].text.strip())
            song.artist = entry.xpath(
                'td[2]/div/div[2]/div[2]')[0].text.strip()
            date = entry.find_class('date')[0]
            date_text = ""
            for text in date.itertext():
                date_text = date_text+text.strip()
            song.date = datetime.datetime.strptime(date_text, '%d.%m.%Y')

            songs.append(song)
        except Exception as e:
            print "Error parsing Artist search: {}".format(e.message)
            pass

    return songs
