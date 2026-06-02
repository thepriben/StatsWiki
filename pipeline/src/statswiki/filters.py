FILTERS = (
    "MediaWiki:", "Portal:", "File:", "Help:", "Category:", "Main_Page",
    "User:", "Template:", "Special:", "Wikipedia:", "Talk:", "Draft:",
)

REDIRECTS = {
    "2019–20 coronavirus pandemic": "Q81068910",
    "United States presidential election, 2016": "Q699872",
    "List of Presidents of the United States": "Q35073",
    "Stranger Things (TV series)": "Q19798734",
    "Meghan Markle": "Q3304418",
}


def skip(article: str) -> bool:
    return any(article.startswith(p) for p in FILTERS)
