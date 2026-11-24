"""Builds one web page per game at /g/<id>/ from the app's public catalogue (decision 170).

Run nightly by .github/workflows/game-pages.yml. Pages only change when the game's details change, so a night
with no changes commits nothing. Prices are left off on purpose: they change daily and live in the app.
Pages for games that leave the catalogue are kept, so a link someone shared keeps working.

It also writes /sitemap.xml and /robots.txt (24 Nov 2026). Nothing on the site links to the game pages, so the sitemap
is how search engines find them. It lists the home page, the privacy and terms pages, and one line per game that is in
the catalogue tonight; a kept page for a game that has left the catalogue is not listed. No dates are given, because a
page's date would change nightly for no reason. One sitemap file holds up to 50,000 addresses; the script stops rather
than write a bigger one.
The page title leads with the game's name, then what the page shows (Matthew, 24 Nov 2026). It does not say "price":
the page shows none.
"""
import html, json, os, re, sys, urllib.request

# Cloudflare's copy first (free to download), Supabase's as the fallback: the same order as the app.
CATALOGUES = ['https://pub-bb2d21f9f297475aaa9b820aaef8ab9e.r2.dev/catalogue-v1.json',
              'https://vulgyfzelewuceatdloj.supabase.co/storage/v1/object/public/public-data/catalogue-v1.json']
SITE = 'https://lfgame.co.uk'
GET_APP = SITE + '/#join'  # closed test; becomes the Play listing at public launch
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

PLATFORMS = {'pc': 'PC', 'ps4': 'PS4', 'ps5': 'PS5', 'xone': 'Xbox One', 'xsx': 'Xbox Series X|S', 'sw': 'Switch',
             'sw2': 'Switch 2', 'mac': 'Mac', 'linux': 'Linux', 'ios': 'iPhone', 'android': 'Android'}
GENRES = {'openworld': 'Open world', 'coop': 'Co-op', 'multi': 'Multiplayer', 'solo': 'Single player', 'rpg': 'RPG',
          'mmo': 'MMO', 'sim': 'Simulation', 'roguelite': 'Roguelite', 'cosy': 'Cosy', 'metroid': 'Metroidvania',
          'souls': 'Soulslike', 'story': 'Story-rich'}
STORES = {'steam': 'Steam', 'epic': 'Epic Games Store', 'gog': 'GOG', 'playstation': 'PlayStation Store',
          'xbox': 'Xbox Store', 'nintendo': 'Nintendo eShop', 'itch': 'itch.io', 'official': 'Official site', 'battlenet': 'Battle.net', 'ea': 'EA app'}

e = lambda s: html.escape(str(s or ''), quote=True)


def label(map_, k):
    return map_.get(k) or k.replace('-', ' ').capitalize()


def video(g):
    vids = g.get('videos') or []
    v = next((x for x in vids if x.get('tab') == 'gameplay'), vids[0] if vids else None)
    if not v or not re.fullmatch(r'[A-Za-z0-9_-]{11}', str(v.get('id') or '')):
        return ''
    vid = v['id']
    start = f"&start={int(v['startS'])}" if v.get('startS') else ''
    # A thumbnail first: YouTube only loads (and sets nothing) once the visitor presses play.
    return f'''<div class="video" data-src="https://www.youtube-nocookie.com/embed/{vid}?autoplay=1&rel=0{start}">
  <img src="https://i.ytimg.com/vi/{vid}/hqdefault.jpg" alt="Gameplay video of {e(g['title'])}" loading="lazy">
  <button aria-label="Play gameplay video">&#9654;</button></div>'''


def rating(g):
    r, n, src = g.get('rating'), g.get('ratingCount'), g.get('ratingSource')
    if not r:
        return ''
    if src == 'steam' and n:
        # Rounded, so a page doesn't change (and get re-published) every time a game picks up a few reviews.
        count = f'{n/1e6:.1f}M' if n >= 1e6 else f'{n/1e3:.0f}k' if n >= 1e4 else f'{round(n, -2):,}' if n >= 1000 else 'under 1,000' if n >= 100 else 'a few'
        return f'<p class="rating"><b>{r}%</b> positive on Steam ({count} reviews)</p>'
    return f'<p class="rating"><b>{r}</b> / 100 critic score</p>'


def page(g):
    gid, title = g['id'], g['title']
    hook = g.get('hook') or ''
    desc = g.get('description') or ''
    cover = f"https://images.igdb.com/igdb/image/upload/t_cover_big/{g['cover']}.jpg" if g.get('cover') else SITE + '/assets/icon.png'
    when = 'Coming soon' if g.get('comingSoon') else (str(g['year']) if g.get('year') else '')
    by = ' · '.join(x for x in [e(g.get('studio')), e(when)] if x)
    plats = ''.join(f'<li>{e(label(PLATFORMS, p))}</li>' for p in g.get('platforms') or [])
    genres = ''.join(f'<li>{e(label(GENRES, x))}</li>' for x in (g.get('genres') or [])[:6])
    stores = ''.join(f'<a class="store" href="{e(u)}" rel="nofollow noopener">{e(label(STORES, k))}</a>'
                     for k, u in (g.get('stores') or {}).items() if isinstance(u, str) and u.startswith('https://'))
    hours = f"<p class=\"small\">About {round(g['hoursMain'])} hours to finish the main story.</p>" if g.get('hoursMain') else ''
    age = f'<p class="small">Age rating {int(g["age"])}+.</p>' if g.get('age') else ''
    meta_desc = e((hook or desc)[:160])
    return f'''<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}: gameplay and where to buy · Looking For Game</title>
<meta name="description" content="{meta_desc}">
<link rel="canonical" href="{SITE}/g/{e(gid)}/">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{meta_desc}">
<meta property="og:image" content="{e(cover)}">
<meta property="og:url" content="{SITE}/g/{e(gid)}/">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Looking For Game">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0B0C10">
<link rel="icon" href="/assets/favicon.png">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Space+Grotesk:wght@700&display=swap">
<link rel="stylesheet" href="/g/game.css">
</head>
<body>
<main>
<a class="brand" href="/"><img src="/assets/icon-180.png" alt="">Looking For Game</a>
<article class="card">
  <div class="top">
    <img class="cover" src="{e(cover)}" alt="Cover of {e(title)}" width="132" height="176">
    <div>
      <h1>{e(title)}</h1>
      <p class="by">{by}</p>
      {rating(g)}
    </div>
  </div>
  {f'<p class="hook">{e(hook)}</p>' if hook else ''}
  {video(g)}
  {f'<p>{e(desc)}</p>' if desc and desc != hook else ''}
  {f'<h2>Platforms</h2><ul class="tags">{plats}</ul>' if plats else ''}
  {f'<h2>Genres</h2><ul class="tags">{genres}</ul>' if genres else ''}
  {hours}{age}
  {f'<h2>Where to get it</h2><div class="stores">{stores}</div>' if stores else ''}
</article>
<section class="cta">
  <p><b>Swipe through real gameplay, save the games you like and get told when they go on sale.</b></p>
  <a class="button" href="{GET_APP}">Get Looking For Game</a>
</section>
<p class="foot">Game details from <a href="https://www.igdb.com">IGDB</a>; video from YouTube. <a href="/privacy/">Privacy</a> · <a href="/terms/">Terms</a></p>
</main>
<script src="/g/game.js" defer></script>
</body>
</html>
'''


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else None
    if src:
        games = json.load(open(src, encoding='utf-8'))['games']
    else:
        games, problem = None, None
        for url in CATALOGUES:
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'lfgame-pages'})
                with urllib.request.urlopen(req, timeout=120) as r:
                    games = json.load(r)['games']
                break
            except Exception as ex:  # try the next copy
                problem = ex
        if games is None:
            sys.exit(f'Could not download the catalogue: {problem}')
    if len(games) < 1000:
        sys.exit(f'Only {len(games)} games in the catalogue: not touching the pages.')
    changed, listed = 0, []
    for g in games:
        gid = g.get('id') or ''
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,250}', gid):
            continue
        d = os.path.join(ROOT, 'g', gid)
        p = os.path.join(d, 'index.html')
        listed.append(gid)
        new = page(g)
        try:
            if open(p, encoding='utf-8').read() == new:
                continue
        except FileNotFoundError:
            pass
        os.makedirs(d, exist_ok=True)
        open(p, 'w', encoding='utf-8').write(new)
        changed += 1
    listed.sort()
    urls = [SITE + '/', SITE + '/privacy/', SITE + '/terms/'] + [f'{SITE}/g/{gid}/' for gid in listed]
    if len(urls) > 50000:
        sys.exit(f'{len(urls)} addresses: more than one sitemap file can hold. Split it before going on.')
    sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
               + ''.join(f'<url><loc>{e(u)}</loc></url>\n' for u in urls) + '</urlset>\n')
    robots = f'User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n'
    for name, text in (('sitemap.xml', sitemap), ('robots.txt', robots)):
        path = os.path.join(ROOT, name)
        try:
            if open(path, encoding='utf-8').read() == text:
                continue
        except FileNotFoundError:
            pass
        open(path, 'w', encoding='utf-8', newline='\n').write(text)
        print(name, 'written')
    print(f'{len(games)} games, {changed} pages written, {len(urls)} addresses in the sitemap')


if __name__ == '__main__':
    main()
