import feedparser

DUST2_FEED = "https://www.dust2.us/rss/news"
STEAMDB_FEED = "https://steamdb.info/app/730/history/feed/"


def get_latest_dust2():
    feed = feedparser.parse(DUST2_FEED)
    article = feed.entries[0]

    return {
        "title": article.title,
        "link": article.link
    }


def get_latest_steamdb():
    feed = feedparser.parse(STEAMDB_FEED)
    update = feed.entries[0]

    return {
        "title": update.title,
        "link": update.link
    }