import sys

import dbaccess
import chart_scraper
import requests
import datetime

two_years_ago = datetime.datetime.now() - datetime.timedelta(days=730)
five_years_ago = datetime.datetime.now()-datetime.timedelta(days=1825)
nineteen_seventy = datetime.datetime(1970, 1, 1)

db_mgr = dbaccess.MyriadDBManager(sys.argv[1])
songs_list = db_mgr.getSongList()

for db_entry in songs_list:
    chart_song = None
    print "{} - {}...".format(db_entry['artist'], db_entry['title'])

    try:
        # Retrieve a list of chart-entry songs that roughly match the title and
        # artist of the song in the database
        songs = chart_scraper.retrieveSongs(
            db_entry['artist'], db_entry['title'])

        # Sort the songs by the average confidence, highest first
        score_ordered_songs = sorted(
            songs, key=lambda chart_song: chart_song.avg_confidence, reverse=True)

        if score_ordered_songs[0].avg_confidence > 60:
            chart_song = score_ordered_songs[0]
    except Exception as e:
        print "Error: {}".format(e.message)

    if not chart_song:
        print "\tNo chart entry found"
        db_mgr.setSongCategory(
            db_entry['id'], db_mgr.categories[db_mgr.CATEGORY_OTHER].id)
        continue

    print u"\t{} by {}: #{} ({}) ({}%)".format(
        chart_song.name, chart_song.artist, chart_song.peak_pos, chart_song.date.strftime('%d/%m/%Y'), chart_song.avg_confidence).encode('utf-8')

    if chart_song.date.month == 12 and chart_song.date.day > 18:
        print "\tChristmas Song"
        db_mgr.setSongCategory(
            db_entry['id'], db_mgr.categories[db_mgr.CATEGORY_CHRISTMAS].id)
        continue

    cat_id = db_mgr.CATEGORY_OTHER  # Start off as 'Other' - long ago, no chart
    if chart_song.peak_pos == 1:
        cat_id += 0x010000
    elif chart_song.peak_pos <= 10:
        cat_id += 0x001000

    # Only carry on if the song was top ten or more, otherwise we'll just call it
    # 'other'
    if cat_id != 0x000000:
        if chart_song.date > two_years_ago:
            cat_id += 0x000100
        elif chart_song.date > five_years_ago:
            cat_id += 0x000010
        elif chart_song.date > nineteen_seventy:
            cat_id += 0x000001
        else:
            # It was top-ten, but too long ago
            cat_id = db_mgr.CATEGORY_OTHER

    print "\tCategory: {}".format(db_mgr.categories[cat_id].description)
    db_mgr.setSongCategory(db_entry['id'], db_mgr.categories[cat_id].id)
