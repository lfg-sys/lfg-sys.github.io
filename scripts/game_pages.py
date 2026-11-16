"""Builds one web page per game at /g/<id>/ from the app's public catalogue (decision 170).

Run nightly by .github/workflows/game-pages.yml. Pages only change when the game's details change, so a night
with no changes commits nothing. Prices are left off on purpose: they change daily and live in the app.
Pages for games that leave the catalogue are kept, so a link someone shared keeps working.
"""
import html, json, os, sys, urllib.request

CATALOGUE = 'https://vulgyfzelewuceatdloj.supabase.co/storage/v1/object/public/public-data/catalogue-v1.json'
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
    if not v:
        return ''
    vid = e(v['id'])
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
        count = f'{n/1e6:.1f}M' if n >= 1e6 else f'{n/1e3:.0f}k' if n >= 1e4 else f'{n:,}'
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
                     for k, u in (g.get('stores') or {}).items() if u)
    hours = f"<p class=\"small\">About {round(g['hoursMain'])} hours to finish the main story.</p>" if g.get('hoursMain') else ''
    age = f'<p class="small">Age rating {int(g["age"])}+.</p>' if g.get('age') else ''
    meta_desc = e((hook or desc)[:160])
    return f'''<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}: gameplay and where to get it · Looking For Game</title>
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
        with urllib.request.urlopen(CATALOGUE, timeout=120) as r:
            games = json.load(r)['games']
    if len(games) < 1000:
        sys.exit(f'Only {len(games)} games in the catalogue: not touching the pages.')
    changed = 0
    for g in games:
        gid = g.get('id') or ''
        if not gid or '/' in gid or gid.startswith('.'):
            continue
        d = os.path.join(ROOT, 'g', gid)
        p = os.path.join(d, 'index.html')
        new = page(g)
        try:
            if open(p, encoding='utf-8').read() == new:
                continue
        except FileNotFoundError:
            pass
        os.makedirs(d, exist_ok=True)
        open(p, 'w', encoding='utf-8').write(new)
        changed += 1
    print(f'{len(games)} games, {changed} pages written')


if __name__ == '__main__':
    main()
