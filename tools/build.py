"""Static site generator for The Future Farmer's Table.

Run:  python3 tools/build.py
Writes HTML pages to the repo root plus assets/js/data.js.
"""
import datetime as dt
import html
import json
import math
import os

from content import (FIELDS, FIELD_ORDER, SPACES, LEVELS, PRICES, TIMES, KITS, KIT, BEGINNER_PICKS,
                     WORKSHOPS, WS, GUIDES, GUIDE, LOCATION)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIZES = json.load(open(os.path.join(ROOT, "assets/img/sizes.json")))
VERSION = dt.datetime.now().strftime("%Y%m%d%H%M")
TODAY = dt.date(2026, 10, 29)
SITE = "The Future Farmer's Table"
BASE_URL = "https://future-farmers-table.vercel.app"

e = html.escape


# ------------------------------------------------------------------ helpers
def img(name, alt, sizes="100vw", cls="", eager=False, vt=None, attrs=""):
    w, h = SIZES[name]
    sw, sh = 720, round(h * 720 / w)
    loading = 'fetchpriority="high"' if eager else 'loading="lazy"'
    style = f' style="view-transition-name: {vt}"' if vt else ""
    c = f' class="{cls}"' if cls else ""
    return (f'<img{c} src="/assets/img/{name}.webp" srcset="/assets/img/{name}-sm.webp {sw}w, /assets/img/{name}.webp {w}w" '
            f'sizes="{sizes}" width="{w}" height="{h}" alt="{e(alt)}" {loading} decoding="async"{style}{attrs}>')


def icon(name, cls="icon"):
    return f'<svg class="{cls}" aria-hidden="true"><use href="#i-{name}"></use></svg>'


def money(n, cents=False):
    return f"${n:,.2f}" if cents else f"${n:,.0f}" if n == int(n) else f"${n:,.2f}"


def plural(n, one, many=None):
    return f"{n} {one if n == 1 else (many or one + 's')}"


def days_label(k):
    return "Tool" if k["days"] is None else f'{k["days"]} days'


def fmt_date(iso, long=False):
    d = dt.date.fromisoformat(iso)
    return d.strftime("%A, %B %-d") if long else d.strftime("%a %b %-d")


def fmt_time(t):
    h, m = map(int, t.split(":"))
    suffix = "am" if h < 12 else "pm"
    h12 = h % 12 or 12
    return f"{h12}:{m:02d}{suffix}" if m else f"{h12}{suffix}"


def session_id(ws, s):
    return f'{ws["slug"]}@{s[0]}T{s[1]}'


ICONS = {
    "search": '<circle cx="11" cy="11" r="6.5"/><path d="m20 20-4.2-4.2"/>',
    "user": '<circle cx="12" cy="8.5" r="3.5"/><path d="M5 20c1.2-3.6 4-5.5 7-5.5s5.8 1.9 7 5.5"/>',
    "bag": '<path d="M5.5 8.5h13l-1 11.5h-11z"/><path d="M9 8.5V7a3 3 0 0 1 6 0v1.5"/>',
    "menu": '<path d="M4 9h16M4 15h16"/>',
    "close": '<path d="M6 6l12 12M18 6 6 18"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "minus": '<path d="M5 12h14"/>',
    "check": '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
    "chev": '<path d="m6 9 6 6 6-6"/>',
    "leaf": '<path d="M5 19c0-8 5-13 14-14 0 9-5 14-13 14"/><path d="M5 19l8-8"/>',
    "clock": '<circle cx="12" cy="12" r="8"/><path d="M12 8v4l2.5 2"/>',
    "pin": '<path d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0 1 13 0c0 5.4-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.3"/>',
    "calendar": '<rect x="4" y="5.5" width="16" height="14.5" rx="2"/><path d="M4 10h16M8.5 3.5v4M15.5 3.5v4"/>',
    "users": '<circle cx="9" cy="9" r="3"/><path d="M3.5 19c.8-3 3-4.5 5.5-4.5s4.7 1.5 5.5 4.5"/><circle cx="17" cy="9.5" r="2.4"/><path d="M16 14.6c2.2.1 3.9 1.5 4.5 4.4"/>',
    "info": '<circle cx="12" cy="12" r="8"/><path d="M12 11v5M12 8h.01"/>',
    "lock": '<rect x="5.5" y="10.5" width="13" height="9.5" rx="2"/><path d="M8.5 10.5V8a3.5 3.5 0 0 1 7 0v2.5"/>',
    "truck": '<path d="M3.5 7h10v9h-10zM13.5 10h4l3 3v3h-7z"/><circle cx="7.5" cy="17.5" r="1.5"/><circle cx="17" cy="17.5" r="1.5"/>',
    "sprout": '<path d="M12 20v-8"/><path d="M12 12c0-3-2-5-6-5 0 3 2 5 6 5z"/><path d="M12 14c0-3 2-6 6.5-6 0 3.5-2.5 6-6.5 6z"/>',
    "level": '<path d="M5 19v-4M10 19v-8M15 19V8M20 19V5"/>',
}


def sprite():
    syms = "".join(f'<symbol id="i-{k}" viewBox="0 0 24 24">{v}</symbol>' for k, v in ICONS.items())
    return f'<svg width="0" height="0" style="position:absolute" aria-hidden="true">{syms}</svg>'


def logomark(size=26):
    dots = ['<circle cx="13" cy="13" r="1.9"/>']
    for i in range(8):
        a = i * math.pi / 4
        dots.append(f'<circle cx="{13 + 5.4 * math.cos(a):.2f}" cy="{13 + 5.4 * math.sin(a):.2f}" r="1.35"/>')
    for i in range(12):
        a = i * math.pi / 6 + math.pi / 12
        dots.append(f'<circle cx="{13 + 10 * math.cos(a):.2f}" cy="{13 + 10 * math.sin(a):.2f}" r="1.05"/>')
    return f'<svg viewBox="0 0 26 26" width="{size}" height="{size}" fill="currentColor" aria-hidden="true">{"".join(dots)}</svg>'


# ------------------------------------------------------------------ chrome
NAV = [("Kits", "/shop", "shop"), ("Workshops", "/workshops", "workshops"), ("Learn", "/learn", "learn"), ("About", "/about", "about")]


def head(title, desc, page, og_img="og"):
    full = title if title == SITE else f"{title} · {SITE}"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(full)}</title>
<meta name="description" content="{e(desc)}">
<meta name="theme-color" content="#ffffff">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<meta property="og:type" content="website">
<meta property="og:title" content="{e(full)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{BASE_URL}/assets/img/{og_img}.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="preload" href="/assets/fonts/geist.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/syne.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/css/styles.css?v={VERSION}">
<script>document.documentElement.classList.add('js');setTimeout(function(){{document.querySelectorAll('[data-reveal]').forEach(function(e){{e.classList.add('is-in')}})}},3000)</script>
<script type="module" src="/assets/js/main.js"></script>
</head>
<body data-page="{page}">
{sprite()}
<a class="skip-link" href="#main">Skip to content</a>
"""


def banner():
    return """<div class="demo-banner" data-banner hidden>A concept store designed for a university course. Browse freely: the cart and checkout are a demo and never take payment. <a href="/about#notes">About this project</a></div>"""


def nav(active):
    links = "".join(
        f'<a class="nav__link" href="{href}"{" aria-current=\"page\"" if key == active else ""}>{label}</a>'
        for label, href, key in NAV)
    mlinks = "".join(f'<a href="{href}">{label}{icon("chev", "icon")}</a>'.replace('icon"', 'icon" style="transform:rotate(-90deg)"', 1) for label, href, _ in NAV)
    return f"""{banner()}
<header class="nav" data-nav>
  <div class="container nav__inner">
    <a class="logo" href="/" aria-label="{SITE}, home">{logomark()}<span class="logo__word">Future Farmer’s Table</span></a>
    <nav class="nav__links" aria-label="Main">{links}</nav>
    <div class="nav__actions">
      <button class="btn btn--metal btn--icon btn--sm nav__search" type="button" data-search-open aria-label="Search">{icon("search")}</button>
      <div class="account">
        <button class="btn btn--metal btn--icon btn--sm nav__account" type="button" data-account aria-expanded="false" aria-controls="account-pop" aria-label="Account">{icon("user")}</button>
        <div class="popover" id="account-pop" role="dialog" aria-label="Account">
          <p class="ink" style="font-weight:500;margin-bottom:6px">Accounts aren’t part of this demo</p>
          <p>Your cart and lesson progress are saved in this browser, so you can pick up where you left off.</p>
        </div>
      </div>
      <a class="btn btn--solid btn--sm nav__cta" href="/shop?level=beginner">Start growing</a>
      <a class="cart-link" href="/cart" data-cart-link aria-label="Cart, 0 items">{icon("bag")}<span class="cart-link__count" data-cart-count>0</span></a>
      <button class="btn btn--metal btn--icon btn--sm menu-btn" type="button" data-menu-toggle aria-expanded="false" aria-controls="menu" aria-label="Menu">{icon("menu")}</button>
    </div>
  </div>
</header>
<div class="menu" id="menu" data-menu>
  <nav aria-label="Mobile">{mlinks}</nav>
  <div class="menu__quick">
    <button class="btn btn--metal btn--sm" type="button" data-search-open>{icon("search", "icon icon--sm")}Search</button>
  </div>
  <a class="btn btn--solid btn--block" href="/shop?level=beginner">Start growing</a>
</div>
"""


def footer(minimal=False):
    legal = f"""<div class="footer__legal"><span>© 2026 Future Farmer’s Table. A concept store designed by Ella Kim for SI 407. No real orders or payments are processed.</span><span><a href="/about#notes">Design notes</a></span></div>"""
    if minimal:
        return f'<footer class="footer" style="padding-block:var(--s-6)"><div class="container">{legal.replace('class="footer__legal"', 'class="footer__legal" style="margin-top:0;border-top:0;padding-top:0"')}</div></footer>'
    cols = [
        ("Shop", [("Hydroponics", "/shop?category=hydroponics"), ("Vertical farming", "/shop?category=vertical"), ("Alternative proteins", "/shop?category=alt-proteins"), ("Fungi", "/shop?category=fungi"), ("All kits", "/shop")]),
        ("Learn", [("Grow guides", "/learn"), ("How it works", "/about#how"), ("Reading roots", "/learn/reading-roots")]),
        ("Workshops", [("All workshops", "/workshops"), ("Family Saturdays", "/workshops/seed-to-sprout-family"), ("Mushroom night", "/workshops/mushroom-night")]),
        ("Company", [("About", "/about"), ("The greenhouse", "/about#studio"), ("Design notes", "/about#notes")]),
    ]
    colhtml = "".join(
        f'<div class="footer__col"><h2>{t}</h2><ul>{"".join(f"<li><a href=\"{h}\">{l}</a></li>" for l, h in links)}</ul></div>'
        for t, links in cols)
    return f"""<footer class="footer">
  <div class="container">
    <div class="footer__grid">
      <div class="footer__about">
        <a class="logo" href="/">{logomark()}<span class="logo__word">Future Farmer’s Table</span></a>
        <p>Kits and experiences for growing the future of food at home.</p>
        <form class="newsletter" data-newsletter novalidate>
          <label for="nl-email">Grow with us: monthly notes</label>
          <div class="newsletter__row">
            <input id="nl-email" type="email" name="email" placeholder="Email address" autocomplete="email" required>
            <button class="btn btn--glass btn--sm" type="submit">Join</button>
          </div>
          <p class="newsletter__msg" data-newsletter-msg aria-live="polite"></p>
        </form>
      </div>
      <div class="footer__cols">{colhtml}</div>
    </div>
    {legal}
  </div>
</footer>"""


def overlays():
    return f"""<div class="search" data-search role="dialog" aria-modal="true" aria-label="Search" hidden>
  <div class="search__panel">
    <div class="search__field">{icon("search")}<input type="search" placeholder="Search kits, workshops and guides" aria-label="Search" data-search-input autocomplete="off" role="combobox" aria-expanded="true" aria-controls="search-results"><span class="kbd">esc</span></div>
    <div class="search__results" id="search-results" role="listbox" data-search-results></div>
  </div>
</div>
<div class="toasts" data-toasts aria-live="polite" aria-atomic="false"></div>
</body>
</html>"""


def page(path, title, desc, active, body, page_id=None, minimal=False, header_html=None):
    out = head(title, desc, page_id or active) + (header_html if header_html is not None else nav(active))
    out += f'<main id="main">{body}</main>' + footer(minimal) + overlays()
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(out)


# ------------------------------------------------------------------ components
def kit_card(k, vt=False, sizes="(min-width: 1000px) 30vw, 50vw"):
    status = "Sold out" if k["soldout"] else FIELDS[k["field"]]["short"]
    attrs = (f'data-kit="{k["slug"]}" data-field="{k["field"]}" data-level="{k["level"]}" data-space="{k["space"]}" '
             f'data-price="{k["price_bucket"]}" data-time="{k["time_bucket"]}" data-cost="{k["price"]}" '
             f'data-days="{k["days"] if k["days"] is not None else 999}" data-order="{k["n"]}" data-soldout="{str(k["soldout"]).lower()}"')
    if k["soldout"]:
        price = f'<div class="kit-card__price"><span class="meta">{k["back"]}</span></div>'
        btn = f'<button class="add" type="button" disabled aria-label="{e(k["name"])} is sold out">{icon("plus")}<span class="add__label">Sold out</span></button>'
    else:
        price = f'<div class="kit-card__price"><span class="price">{money(k["price"])}</span><span class="meta">{k["meta"]}</span></div>'
        btn = (f'<button class="add" type="button" data-add="{k["slug"]}" aria-label="Add {e(k["name"])} to cart">'
               f'{icon("plus", "icon i-plus")}{icon("check", "icon i-check")}<span class="add__label">Add to cart</span></button>')
    return f"""<article class="kit-card" {attrs}>
  <a class="kit-card__media" href="/kits/{k["slug"]}" tabindex="-1" aria-hidden="true">{img(k["gallery"][0], k["name"], sizes, vt=f"kit-{k['slug']}" if vt else None)}</a>
  <div class="kit-card__body">
    <div class="kit-card__meta"><span class="kit-card__status" data-status data-default="{status}">{status}</span><span>{LEVELS[k["level"]]} · {days_label(k)}</span></div>
    <h3 class="kit-card__name"><a href="/kits/{k["slug"]}">{e(k["name"])}</a></h3>
    <p class="kit-card__desc">{e(k["desc"])}</p>
  </div>
  <div class="kit-card__foot">{price}{btn}</div>
</article>"""


def section_head(eyebrow, title, text="", link=None, h="h2", cls="h3"):
    a = f'<a class="btn btn--metal btn--sm" href="{link[1]}">{link[0]}</a>' if link else ""
    p = f'<p class="small">{text}</p>' if text else ""
    return f"""<div class="section-head"><p class="eyebrow">{eyebrow}</p><div class="section-head__row"><div class="stack"><{h} class="{cls}">{title}</{h}>{p}</div>{a}</div></div>"""


def next_sessions(limit=3):
    rows = []
    for w in WORKSHOPS:
        for s in w["sessions"]:
            if s[3] > 0:
                rows.append((s[0], s[1], w, s))
    rows.sort(key=lambda r: (r[0], r[1]))
    return rows[:limit]


def ws_card(w):
    upcoming = [s for s in w["sessions"]]
    pills = ""
    for s in upcoming[:4]:
        full = s[3] == 0
        pills += (f'<a class="date-pill{" is-full" if full else ""}" href="/workshops/{w["slug"]}?session={session_id(w, s)}">'
                  f'<strong>{fmt_date(s[0])}</strong><span>{fmt_time(s[1])} · {"Full" if full else f"{s[3]} seats left"}</span></a>')
    return f"""<article class="ws-card" data-field="{w["field"]}">
  <div class="ws-card__img">{img(w["img"], w["title"], "(min-width: 860px) 40vw, 100vw")}</div>
  <div class="ws-card__body">
    <p class="eyebrow">{FIELDS[w["field"]]["name"]} · {w["level"]}</p>
    <h2 class="h4 ws-card__title"><a href="/workshops/{w["slug"]}">{e(w["title"])}</a></h2>
    <p>{e(w["summary"])}</p>
    <div class="ws-card__facts"><span>{icon("clock")}{w["duration"]}</span><span>{icon("pin")}Ann Arbor greenhouse</span><span class="price">{money(w["price"])} per seat</span></div>
    <div class="ws-card__next">{pills}</div>
  </div>
</article>"""


def guide_card(g):
    k = KIT[g["kit"]]
    return f"""<article class="guide-card" data-guide="{g["slug"]}" data-field="{g["field"]}" data-lessons="{len(g["lessons"])}">
  <div class="guide-card__img">{img(g["img"], g["title"], "(min-width: 900px) 30vw, 100vw")}</div>
  <p class="meta"><span>{FIELDS[g["field"]]["name"]}</span><span>{g["read"]} read</span><span>{len(g["lessons"])} lessons</span></p>
  <h3 class="h6"><a href="/learn/{g["slug"]}">{e(g["title"])}</a></h3>
  <p class="small">{e(g["summary"])}</p>
  <div class="progress" data-progress><div class="progress__bar"><span></span></div><span data-progress-label>Not started</span></div>
</article>"""


# ------------------------------------------------------------------ pages
def build_home():
    tiles = [("harvest", "01&nbsp;&nbsp;Harvest daily", "Hands harvesting basil from a steel greenhouse bench", "tall"),
             ("workshop-together", "03&nbsp;&nbsp;Learn together", "A workshop group tasting microgreens around a greenhouse table", "wide"),
             ("roots", "02&nbsp;&nbsp;Roots in water", "White roots growing in a glass of water under a seedling", "tall"),
             ("fungi-greenhouse", "04&nbsp;&nbsp;Fungi on coffee", "Oyster mushrooms fruiting from a steel grow chamber", "wide")]
    col = lambda items: '<div class="collage__col">' + "".join(
        f'<figure class="tile tile--{shape} grow" data-reveal>{img(n, alt, "(min-width: 900px) 25vw, 50vw", eager=True)}<figcaption class="tile__cap">{cap}</figcaption></figure>'
        for i, (n, cap, alt, shape) in items) + "</div>"
    collage = col([(0, tiles[0]), (1, tiles[1])]) + col([(2, tiles[2]), (3, tiles[3])])

    # fit finder
    def opts(d, sel):
        return "".join(f'<option value="{k}"{" selected" if k == sel else ""}>{v}</option>' for k, v in d.items())
    space_opts = {"countertop": "countertop", "shelf-wall": "shelf or a bit of wall", "tabletop": "table and a cupboard"}
    level_opts = {"beginner": "new to growing", "intermediate": "ready for a challenge"}
    budget_opts = {"under-50": "under $50", "50-100": "around $50 – $100", "over-100": "over $100", "any": "whatever it takes"}
    time_opts = {"under-2": "in under two weeks", "2-4": "within a month", "any": "whenever it's ready"}
    default_fit = sum(1 for k in KITS if k["space"] == "countertop" and k["level"] == "beginner" and k["price_bucket"] in ("under-50", "50-100") and k["time_bucket"] == "under-2")
    finder = f"""<section class="section--tight" aria-labelledby="finder-title">
  <div class="container">
    <div class="finder" data-finder>
      <p class="eyebrow" id="finder-title">Find a kit that fits</p>
      <p class="finder__sentence">I have a <select aria-label="Space" name="space">{opts(space_opts, "countertop")}</select>, I’m <select aria-label="Experience" name="level">{opts(level_opts, "beginner")}</select>, I’d like to spend <select aria-label="Budget" name="price">{opts(budget_opts, "50-100")}</select> and harvest <select aria-label="Time to harvest" name="time">{opts(time_opts, "under-2")}</select>.</p>
      <div class="finder__foot">
        <div class="finder__thumbs" data-finder-thumbs aria-hidden="true"></div>
        <div style="display:flex;align-items:center;gap:var(--s-5);flex-wrap:wrap">
          <p class="finder__count" data-finder-count aria-live="polite">{default_fit} kits fit</p>
          <a class="btn btn--solid" href="/shop" data-finder-link>Show kits</a>
        </div>
      </div>
    </div>
  </div>
</section>"""

    picks = "".join(kit_card(KIT[s], vt=True, sizes="(min-width: 1000px) 22vw, 50vw") for s in BEGINNER_PICKS)
    fields4 = [("hydroponics", "Hydroponics", "roots"), ("alt-proteins", "Alternative proteins", "alt-proteins"), ("vertical", "Vertical farming", "vertical-shelf"), ("fungi", "Fungi", "ws-mushroom-night"), ("food-tech", "Emerging food tech", "food-tech")]
    fieldcards = "".join(
        f'<a class="field-card" href="/shop?category={key}"><div class="field-card__img">{img(im, name, "(min-width: 900px) 22vw, 50vw")}</div><h3>{name}</h3><p>{FIELDS[key]["blurb"]}</p><span class="field-card__count">{plural(sum(1 for k in KITS if k["field"] == key), "kit")}</span></a>'
        for key, name, im in fields4)
    sessions = "".join(
        f'<a class="ws-mini" href="/workshops/{w["slug"]}?session={session_id(w, s)}" style="display:grid;gap:var(--s-3)"><div class="tile tile--wide">{img(w["img"], w["title"], "(min-width: 900px) 30vw, 100vw")}</div><p class="eyebrow">{fmt_date(s[0])} · {fmt_time(s[1])}</p><h3 class="h6">{e(w["title"])}</h3><p class="seat-meter"><span class="seat-meter__bar"><span style="width:{round(100 * (1 - s[3] / w["capacity"]))}%"></span></span>{s[3]} of {w["capacity"]} seats left</p></a>'
        for d, t, w, s in next_sessions(3))
    guides = "".join(guide_card(g) for g in GUIDES[:3])
    n_sessions = sum(len(w["sessions"]) for w in WORKSHOPS)

    body = f"""
<section class="hero">
  <div class="container hero__grid">
    <div class="hero__copy">
      <p class="eyebrow rise" data-reveal>Food-tech kits and workshops</p>
      <h1 class="h1 rise" data-reveal>Grow the future of food, at home.</h1>
      <p class="lead measure rise" data-reveal>Hydroponics, alternative proteins and vertical farming, shrunk to fit your kitchen, with lessons that explain the science as it grows.</p>
      <div class="hero__actions rise" data-reveal><a class="btn btn--solid" href="/shop">Explore kits</a><a class="btn btn--bone" href="/workshops">Book a workshop</a></div>
      <nav class="hero__fields rise" data-reveal aria-label="Fields"><a href="/shop?category=hydroponics">Hydroponics</a><a href="/shop?category=alt-proteins">Alt proteins</a><a href="/shop?category=vertical">Vertical farming</a><a href="/shop?category=food-tech">Food tech</a></nav>
    </div>
    <div class="collage">{collage}</div>
  </div>
</section>
{finder}
<section class="section">
  <div class="container">
    {section_head("Start here", "Kits for a first harvest", "Beginner level, small footprints, and every one comes with guided lessons.", ("All kits", "/shop"))}
    <div class="kit-grid kit-grid--4">{picks}</div>
  </div>
</section>
<section class="band" aria-labelledby="band-title">
  <div class="band__img">{img("vertical-farm", "Rows of stacked greens under pink grow lights in a glass vertical farm")}</div>
  <div class="container band__inner">
    <div class="stack">
      <p class="eyebrow">Vertical farming</p>
      <h2 class="h2" id="band-title">Food, grown closer to home.</h2>
      <p>Stacked, sunlit and soil-free. We bring the techniques of indoor farms to a shelf in your kitchen.</p>
    </div>
    <a class="btn btn--glass" href="/about#how">See how it works</a>
  </div>
</section>
<section class="section">
  <div class="container">
    {section_head("What we teach", "Five ways to grow the future", "Every kit and workshop belongs to one of five fields shaping how we’ll eat next.")}
    <div class="fields fields--5">{fieldcards}</div>
  </div>
</section>
<section class="section section--mist">
  <div class="container">
    {section_head("Workshops", "Learn it with your hands", "Small groups at our Ann Arbor greenhouse. Every session sends you home with something growing.", ("All workshops", "/workshops"))}
    <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(min(100%,280px),1fr))">{sessions}</div>
  </div>
</section>
<section class="section">
  <div class="container">
    {section_head("Grow guides", "Lessons that come with every kit", "Short, practical and written for first-time growers.", ("All guides", "/learn"))}
    <div class="guide-grid">{guides}</div>
  </div>
</section>
<section class="section" style="padding-top:0">
  <div class="container">
    <h2 class="h3 statement">Every kit is a lesson. Every harvest is a small piece of the future.</h2>
    <div class="stats">
      <div class="stat"><p><span class="stat__n">14</span><span class="stat__u">days</span></p><p>From seed to first harvest on the Countertop Grow Kit</p></div>
      <div class="stat"><p><span class="stat__n">90%</span><span class="stat__u">less water</span></p><p>Than greens grown in soil, because hydroponics recirculates it</p></div>
      <div class="stat"><p><span class="stat__n">{n_sessions}</span><span class="stat__u">sessions</span></p><p>Hands-on workshops this season</p></div>
      <div class="stat"><p><span class="stat__n">{len(FIELDS)}</span><span class="stat__u">fields</span></p><p>Of future food, at one table</p></div>
    </div>
  </div>
</section>"""
    page("index.html", SITE, "Hydroponic, fungi, vertical-farming and alternative-protein kits with guided lessons, plus hands-on workshops in Ann Arbor.", "home", body)


def build_shop():
    def count(attr, val):
        return sum(1 for k in KITS if k[attr] == val)
    cats = '<a href="/shop" data-cat="" aria-current="true">All products <sup>' + str(len(KITS)) + "</sup></a>" + "".join(
        f'<a href="/shop?category={f}" data-cat="{f}">{FIELDS[f]["name"]} <sup>{count("field", f)}</sup></a>' for f in FIELD_ORDER)

    def group(key, title, options, attr):
        rows = "".join(
            f'<label class="check"><input type="checkbox" name="{key}" value="{v}"><span class="check__label">{lab}</span><span class="check__count" data-count="{key}:{v}">{count(attr, v)}</span></label>'
            for v, lab in options.items())
        return f'<details class="filter-group" open><summary>{title}{icon("chev")}</summary><div class="filter-group__body">{rows}</div></details>'
    groups = (group("level", "Level", LEVELS, "level") + group("space", "Space needed", SPACES, "space") +
              group("price", "Price", PRICES, "price_bucket") + group("time", "Time to harvest", TIMES, "time_bucket"))
    chips = '<button class="chip is-active" type="button" data-cat-chip="">All kits</button>' + "".join(
        f'<button class="chip" type="button" data-cat-chip="{f}">{FIELDS[f]["name"]}</button>' for f in FIELD_ORDER)
    cards = "".join(kit_card(k, vt=True) for k in KITS)
    sort = f"""<label class="select"><span class="meta">Sort</span><select data-sort aria-label="Sort kits"><option value="featured">Featured</option><option value="price-asc">Price: low to high</option><option value="price-desc">Price: high to low</option><option value="harvest">Fastest harvest</option></select>{icon("chev")}</label>"""
    sheet_sort = "".join(f'<button class="chip" type="button" data-sheet-sort="{v}">{l}</button>' for v, l in [("featured", "Featured"), ("price-asc", "Price: low to high"), ("price-desc", "Price: high to low"), ("harvest", "Fastest harvest")])
    body = f"""
<div class="container">
  <div class="page-head">
    <div class="section-head"><nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a><span>/</span><span aria-current="page">Kits</span></nav><h1 class="h2" data-shop-title>All kits</h1></div>
  </div>
  <div class="toolbar">
    <div class="toolbar__filters" data-active-filters><span class="meta">Showing every kit</span></div>
    <div class="toolbar__right"><span class="result-count" data-result-count aria-live="polite">{len(KITS)} of {len(KITS)} kits</span>{sort}</div>
  </div>
  <div class="shop">
    <aside class="sidebar" aria-label="Filters">
      <p class="eyebrow" style="margin-bottom:var(--s-3)">Shop by category</p>
      <nav class="cats" data-cats>{cats}</nav>
      <p class="eyebrow" style="margin-bottom:var(--s-2)">Filter by</p>
      <form data-filters>{groups}</form>
    </aside>
    <div>
      <div class="mobile-bar">
        <div class="chip-row" data-cat-chips>{chips}</div>
        <div class="mobile-bar__row"><button class="btn btn--bone btn--sm" type="button" data-sheet-open>Filter and sort<span data-filter-badge></span></button><span class="result-count" data-result-count-m>{len(KITS)} kits</span></div>
      </div>
      <div class="kit-grid" data-grid style="margin-top:var(--s-5)">{cards}</div>
      <div class="empty" data-empty hidden><h2 class="h4">No kits match all of those filters</h2><p>Try removing one, or start from kits for first-time growers.</p><div style="display:flex;gap:var(--s-3);flex-wrap:wrap"><button class="btn btn--solid" type="button" data-clear>Clear filters</button><a class="btn btn--metal" href="/shop?level=beginner">Beginner kits</a></div></div>
    </div>
  </div>
</div>
<dialog class="sheet" data-sheet aria-label="Filter and sort">
  <div class="sheet__head"><p class="ink" style="font-weight:500">Filter and sort</p><button class="btn btn--metal btn--icon btn--sm" type="button" data-sheet-close aria-label="Close filters">{icon("close")}</button></div>
  <div class="sheet__body">
    <p class="eyebrow">Sort by</p>
    <div class="chip-wrap">{sheet_sort}</div>
    <form data-filters-m>{groups}</form>
  </div>
  <div class="sheet__foot"><button class="btn btn--bone" type="button" data-clear>Clear all</button><button class="btn btn--solid" type="button" data-sheet-close data-sheet-apply>Show {len(KITS)} kits</button></div>
</dialog>"""
    page("shop.html", "All kits", "Browse grow kits by level, space, price and time to harvest.", "shop", body)


def build_product(k):
    f = FIELDS[k["field"]]
    thumbs = "".join(
        f'<button class="gallery__thumb" type="button" data-thumb="{g}" aria-label="Show image {i + 1}"{" aria-current=\"true\"" if i == 0 else ""}>{img(g, "", "120px")}</button>'
        for i, g in enumerate(k["gallery"][:4]))
    lesson_word = "lesson" if k["lessons"] == 1 else "lessons"
    sub = f'One-time purchase · {k["lessons"]} guided {lesson_word} included' if k["lessons"] else "One-time purchase"
    if k["soldout"]:
        stock = '<span class="stock stock--out">Sold out</span>'
        ctas = f'<button class="btn btn--solid btn--lg btn--block" type="button" disabled>Sold out · {k["back"].lower()}</button><button class="btn btn--metal btn--lg btn--block" type="button" data-notify>Notify me when it’s back</button>'
        qty = ""
    else:
        stock = '<span class="stock">In stock</span>'
        ctas = (f'<button class="btn btn--solid btn--lg btn--block" type="button" data-buy="{k["slug"]}"><span data-buy-label>Add to cart</span></button>'
                f'<button class="btn btn--metal btn--lg btn--block" type="button" data-save="{k["slug"]}" aria-pressed="false">Save for later</button>')
        qty = f'<div class="buy__row"><span class="small ink">Quantity</span><div class="qty" data-qty><button type="button" data-step="-1" aria-label="Decrease quantity" disabled>{icon("minus")}</button><output aria-live="polite">1</output><button type="button" data-step="1" aria-label="Increase quantity">{icon("plus")}</button></div></div>'
    li = lambda xs: "".join(f"<li>{e(x)}</li>" for x in xs)
    acc = [
        ("Key features", f'{len(k["features"])} points', f'<ul>{li(k["features"])}</ul>', True),
        ("What’s included", f'{len(k["included"])} items', f'<ul>{li(k["included"])}</ul>', False),
        ("How it works", f'{len(k["how"])} steps', f'<ol>{li(k["how"])}</ol>', False),
        ("Care and harvest", f'~{k["days"]} days' if k["days"] else "Care", f'<p>{e(k["care"])}</p>', False),
    ]
    if k["lessons"]:
        g = GUIDE[k["guide"]]
        acc.append(("Guided learning", f'{k["lessons"]} {lesson_word}', f'<p>{e(g["summary"])}</p><p><a class="btn--link btn" href="/learn/{g["slug"]}">Preview the first lesson</a></p>', False))
    acc_html = "".join(
        f'<details{" open" if o else ""}><summary><span class="acc__n">{i + 1:02d}</span><span class="acc__t">{t}</span><span class="acc__m">{m}</span>{icon("plus")}</summary><div class="acc__body">{b}</div></details>'
        for i, (t, m, b, o) in enumerate(acc))
    w_, d_, h_ = k["dims"]
    # Scale drawing: the area above the counter line (85% of the box) is scene_h cm tall; the box is 16:10.
    scene_h = max(60, h_ * 1.3, w_ / 1.6 * 0.85 * 1.15)
    box_w_cm = 1.6 * scene_h / 0.85
    shape_w, shape_h = w_ / box_w_cm * 100, h_ / scene_h * 85
    cabinet = ""
    if k["space"] == "countertop" and 45 < scene_h * 0.92:
        cabinet = f'<div class="fit__cabinet" style="bottom:{15 + 45 / scene_h * 85:.1f}%"><span>Typical upper cabinet, 45 cm above the counter</span></div>'
    surface = {"countertop": "Counter", "shelf-wall": "Surface", "tabletop": "Table"}[k["space"]]

    harvest = ""
    if k["stages"]:
        last = len(k["stages"]) - 1
        stages = "".join(
            f'<li class="stage{" is-active" if i == 0 else ""}" data-stage="{d}"><p class="stage__day">Day {d}</p><h3>{e(t)}</h3><p>{e(x)}</p></li>'
            for i, (d, t, x) in enumerate(k["stages"]))
        ticks = "".join(f'<span style="--x:{(i / last * 100) if last else 0:.2f}%">Day {d}</span>' for i, (d, _, _) in enumerate(k["stages"]))
        harvest = f"""<section class="section--tight" aria-labelledby="harvest-title">
  <div class="container">
    <div class="harvest" data-harvest>
      <div class="harvest__head"><p class="eyebrow">Your first harvest</p><h2 class="h3" id="harvest-title">What happens, day by day</h2><p>Drag along the line to see what your {e(k["name"])} is doing at each stage, from unboxing to the first harvest.</p></div>
      <div class="harvest__scale">
        <div class="harvest__track"><span class="harvest__fill" data-fill style="width:0%"></span></div>
        <input type="range" min="0" max="{last}" step="1" value="0" aria-label="Growing stage" aria-valuetext="Day {k["stages"][0][0]}: {e(k["stages"][0][1])}" data-day>
        <span class="harvest__knob" data-knob style="left:0%"></span>
        <div class="harvest__ticks">{ticks}</div>
      </div>
      <ol class="harvest__stages">{stages}</ol>
    </div>
  </div>
</section>"""
    related = [x for x in KITS if x["slug"] != k["slug"] and x["field"] == k["field"]] + [x for x in KITS if x["slug"] != k["slug"] and x["field"] != k["field"]]
    related = related[:4]
    w = WS.get(k["workshop"])
    ws_block = ""
    if w:
        s = next((s for s in w["sessions"] if s[3] > 0), w["sessions"][0])
        ws_block = f"""<div class="takeaway"><img src="/assets/img/{w["img"]}-sm.webp" alt="" width="72" height="90" loading="lazy"><div><p class="meta">Prefer to learn in person?</p><p class="ink" style="font-weight:500"><a class="btn--link btn" style="color:var(--ink)" href="/workshops/{w["slug"]}">{e(w["title"])}</a></p><p class="meta">Next: {fmt_date(s[0])}, {fmt_time(s[1])} · {money(w["price"])}</p></div></div>"""
    body = f"""
<div class="container">
  <nav class="crumbs" aria-label="Breadcrumb" style="padding-top:var(--s-6)"><a href="/shop">Kits</a><span>/</span><a href="/shop?category={k["field"]}">{f["name"]}</a><span>/</span><span aria-current="page">{e(k["name"])}</span></nav>
  <div class="pdp">
    <div class="gallery" data-gallery>
      <div class="gallery__main">{img(k["gallery"][0], k["name"], "(min-width: 960px) 55vw, 100vw", eager=True, vt=f"kit-{k['slug']}", attrs=" data-main")}</div>
      <div class="gallery__thumbs">{thumbs}</div>
    </div>
    <div class="buy">
      <div class="buy__top"><span class="eyebrow">{f["name"]} · Kit {k["n"]:02d}</span>{stock}</div>
      <h1 class="h3">{e(k["name"])}</h1>
      <p>{e(k["long"])}</p>
      <div class="buy__price"><span class="price">{money(k["price"], True)}</span><span class="meta">USD</span></div>
      <p class="meta">{sub}</p>
      <dl class="specs"><div><dt>Level</dt><dd>{LEVELS[k["level"]]}</dd></div><div><dt>Harvest</dt><dd>{f'{k["days"]} days' if k["days"] else "Tool"}</dd></div><div><dt>Space</dt><dd>{SPACES[k["space"]]}</dd></div></dl>
      {qty}
      <div class="buy__ctas">{ctas}</div>
      <p class="ship-note">{icon("leaf")}Ships in 2–3 business days. Free shipping over $75.</p>
      <div class="promise"><strong>The first-harvest promise</strong><p>If nothing sprouts in 21 days, tell us and we’ll send new seeds or culture, free.</p></div>
      <div class="acc">{acc_html}</div>
      {ws_block}
    </div>
  </div>
</div>
{harvest}
<section class="section">
  <div class="container">
    {section_head("Will it fit?", "Size and space", "")}
    <div class="fit">
      <div class="fit__box" role="img" aria-label="Scale drawing: {w_} cm wide and {h_} cm tall{', with room to spare under a standard upper cabinet' if cabinet and h_ < 45 else ''}.">{cabinet}<div class="fit__counter"><span>{surface}</span></div><div class="fit__shape" style="width:{shape_w:.1f}%;height:{shape_h:.1f}%"><span class="fit__dim fit__dim--w">{w_} cm</span><span class="fit__dim fit__dim--h">{h_} cm</span></div></div>
      <div class="stack"><p class="lead">{e(k["fits"])}</p><dl><div><dt>Width</dt><dd>{w_} cm ({w_ / 2.54:.1f} in)</dd></div><div><dt>Depth</dt><dd>{d_} cm ({d_ / 2.54:.1f} in)</dd></div><div><dt>Height</dt><dd>{h_} cm ({h_ / 2.54:.1f} in)</dd></div><div><dt>Space type</dt><dd>{SPACES[k["space"]]}</dd></div></dl></div>
    </div>
  </div>
</section>
<section class="section" style="padding-top:0">
  <div class="container">
    {section_head("Pairs well with", "Complete the setup", f"Refills and companion kits that grow alongside the {e(k['name'])}.", ("All kits", "/shop"))}
    <div class="kit-grid kit-grid--4">{"".join(kit_card(x, sizes="(min-width: 1000px) 22vw, 50vw") for x in related)}</div>
  </div>
</section>"""
    page(f"kits/{k['slug']}.html", k["name"], f"{k['desc']} {LEVELS[k['level']]}, {days_label(k)} to harvest, {money(k['price'])}.", "shop", body, page_id="product")


def build_cart():
    body = f"""
<div class="container">
  <div class="page-head"><div class="section-head"><p class="eyebrow" data-cart-eyebrow>Cart</p><div class="section-head__row"><h1 class="h2">Your cart</h1><a class="btn btn--metal btn--sm" href="/shop">Continue shopping</a></div></div></div>
  <div class="cart" data-cart-root>
    <noscript><p>Your cart needs JavaScript to load.</p></noscript>
  </div>
</div>"""
    page("cart.html", "Your cart", "Review your kits and workshop bookings.", "cart", body)


def build_checkout():
    hdr = f"""<header class="co-head"><div class="container"><a class="logo" href="/">{logomark()}<span class="logo__word">Future Farmer’s Table</span></a><span class="secure">{icon("lock", "icon icon--sm")}Secure checkout · demo</span><a class="btn btn--metal btn--sm" href="/cart">Back to cart</a></div></header>"""
    states = ["MI", "OH", "IN", "IL", "WI", "NY", "CA", "TX", "WA", "MA", "Other"]
    st = "".join(f"<option>{s}</option>" for s in states)
    body = f"""
<div class="container">
  <div class="co" data-checkout>
    <div>
      <ol class="steps-nav" data-steps><li class="is-current"><span>01</span>Delivery</li><li><span>02</span>Payment</li><li><span>03</span>Confirmation</li></ol>
      <form class="co-step" data-step="delivery" novalidate>
        <h1 class="h3" style="margin-bottom:var(--s-6)">Where should it go?</h1>
        <fieldset class="form-block"><legend class="form-block__title"><span>01</span>Contact</legend>
          <div class="field"><label for="email">Email</label><input id="email" name="email" type="email" autocomplete="email" required placeholder="you@example.com"><p class="field__help" data-help>We’ll send your receipt and lesson links here.</p></div>
        </fieldset>
        <fieldset class="form-block" data-ship-block><legend class="form-block__title"><span>02</span>Delivery address</legend>
          <div class="form-grid">
            <div class="field"><label for="fn">First name</label><input id="fn" name="first" autocomplete="given-name" required></div>
            <div class="field"><label for="ln">Last name</label><input id="ln" name="last" autocomplete="family-name" required></div>
            <div class="field full"><label for="addr">Street address</label><input id="addr" name="street" autocomplete="address-line1" required></div>
            <div class="field"><label for="city">City</label><input id="city" name="city" autocomplete="address-level2" required></div>
            <div class="field"><label for="state">State</label><select id="state" name="state" autocomplete="address-level1">{st}</select></div>
            <div class="field"><label for="zip">ZIP code</label><input id="zip" name="zip" autocomplete="postal-code" inputmode="numeric" required pattern="[0-9]{{5}}"><p class="field__help" data-help>5 digits</p></div>
          </div>
        </fieldset>
        <fieldset class="form-block" data-ship-block><legend class="form-block__title"><span>03</span>Delivery method</legend>
          <div class="options" data-ship-options></div>
        </fieldset>
        <fieldset class="form-block" data-ws-block hidden><legend class="form-block__title"><span>02</span>Your name for the guest list</legend>
          <div class="form-grid"><div class="field"><label for="wfn">First name</label><input id="wfn" name="wfirst" autocomplete="given-name"></div><div class="field"><label for="wln">Last name</label><input id="wln" name="wlast" autocomplete="family-name"></div></div>
        </fieldset>
        <div class="co-actions"><a class="btn btn--link" href="/cart">Return to cart</a><button class="btn btn--solid btn--lg" type="submit">Continue to payment</button></div>
      </form>
      <form class="co-step" data-step="payment" hidden novalidate>
        <h1 class="h3" style="margin-bottom:var(--s-6)">Payment</h1>
        <div class="review" data-review></div>
        <fieldset class="form-block"><legend class="form-block__title"><span>04</span>Payment method</legend>
          <div class="demo-note">{icon("info")}<p>This is a student demo. No payment is taken, and the card below is a test number that never leaves your browser.</p></div>
          <div class="form-grid">
            <div class="field full"><label for="cc">Card number</label><input id="cc" value="4242 4242 4242 4242" readonly></div>
            <div class="field"><label for="exp">Expiry</label><input id="exp" value="12 / 29" readonly></div>
            <div class="field"><label for="cvc">CVC</label><input id="cvc" value="123" readonly></div>
          </div>
        </fieldset>
        <div class="co-actions"><button class="btn btn--link" type="button" data-back>Back to delivery</button><button class="btn btn--solid btn--lg" type="submit" data-place>Place order</button></div>
      </form>
      <section class="co-step" data-step="done" hidden aria-live="polite"></section>
    </div>
    <aside class="co-summary" data-collapsed="true" data-co-summary>
      <button class="summary-toggle" type="button" data-summary-toggle aria-expanded="false"><span>Show order summary</span><span class="price" data-summary-total>$0.00</span></button>
      <div class="co-summary__body" data-summary-body></div>
    </aside>
  </div>
</div>"""
    page("checkout.html", "Checkout", "Checkout (demo).", "checkout", body, minimal=True, header_html=hdr)


def build_workshops():
    chips = '<button class="chip is-active" type="button" data-ws-filter="">All workshops</button>' + "".join(
        f'<button class="chip" type="button" data-ws-filter="{f}">{FIELDS[f]["name"]}</button>' for f in FIELD_ORDER if any(w["field"] == f for w in WORKSHOPS))
    cards = "".join(ws_card(w) for w in WORKSHOPS)
    body = f"""
<div class="container">
  <div class="page-head">
    <div class="section-head"><nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a><span>/</span><span aria-current="page">Workshops</span></nav>
      <div class="section-head__row"><h1 class="h2">Workshops at the greenhouse</h1></div>
      <p class="lead measure">Small, hands-on sessions in Ann Arbor. You build something, taste something, and leave with something growing.</p>
    </div>
  </div>
  <div class="chip-row" style="margin-block:var(--s-7) var(--s-8);flex-wrap:wrap" data-ws-chips>{chips}</div>
  <div class="ws-list" data-ws-list>{cards}</div>
</div>
<section class="section">
  <div class="container split">
    <div class="split__img">{img("about-greenhouse-dusk", "The glass greenhouse studio at dusk", "(min-width: 900px) 45vw, 100vw")}</div>
    <div class="stack">
      <p class="eyebrow">Where</p>
      <h2 class="h3">{LOCATION}</h2>
      <p>A glass studio surrounded by meadow grass, ten minutes from downtown. Long steel benches, four growing systems, and a small kitchen for tastings.</p>
      <p class="small">Sessions run with 8 to 16 people. Free cancellation up to 48 hours before.</p>
    </div>
  </div>
</section>"""
    page("workshops.html", "Workshops", "Hands-on hydroponics, mushroom, microgreen, fermentation and tasting workshops.", "workshops", body)


def build_workshop(w):
    k = KIT[w["takeaway"]]
    sessions = ""
    first_open = next((i for i, s in enumerate(w["sessions"]) if s[3] > 0), 0)
    for i, s in enumerate(w["sessions"]):
        sid = session_id(w, s)
        full = s[3] == 0
        seats = "Full" if full else f"{s[3]} of {w['capacity']} seats left"
        low = (not full) and s[3] <= 3
        sessions += (f'<label class="session"><input type="radio" name="session" value="{sid}" data-seats="{s[3]}" data-date="{s[0]}" data-start="{s[1]}" data-end="{s[2]}"'
                     f'{" checked" if i == first_open else ""}{" disabled" if full else ""}><span class="session__dot"></span>'
                     f'<span class="session__when"><strong>{fmt_date(s[0], True)}</strong><span>{fmt_time(s[1])} – {fmt_time(s[2])}</span></span>'
                     f'<span class="session__seats{" is-low" if low else ""}">{seats}</span></label>')
    agenda = "".join(f'<li><time>{t}</time><div><strong>{e(a)}</strong><span class="small">{e(b)}</span></div></li>' for t, a, b in w["agenda"])
    body_p = "".join(f"<p>{e(p)}</p>" for p in w["body"])
    others = [x for x in WORKSHOPS if x["slug"] != w["slug"]][:2]
    body = f"""
<div class="container">
  <nav class="crumbs" aria-label="Breadcrumb" style="padding-top:var(--s-6)"><a href="/workshops">Workshops</a><span>/</span><span aria-current="page">{e(w["title"])}</span></nav>
  <div class="book">
    <div class="book__media">
      <div class="tile">{img(w["img"], w["title"], "(min-width: 960px) 55vw, 100vw", eager=True)}</div>
      <div class="stack" style="margin-top:var(--s-7)">
        <p class="eyebrow">{FIELDS[w["field"]]["name"]} · {w["level"]}</p>
        <h1 class="h3">{e(w["title"])}</h1>
        <p class="lead">{e(w["summary"])}</p>
        <div class="ws-card__facts"><span>{icon("clock")}{w["duration"]}</span><span>{icon("users")}Up to {w["capacity"]} people</span><span>{icon("pin")}{LOCATION}</span></div>
      </div>
    </div>
    <div class="book__details">
      <div class="stack">{body_p}</div>
      <div style="margin-top:var(--s-9)">
        {section_head("Plan", "How the session runs", h="h2", cls="h5")}
        <ol class="agenda">{agenda}</ol>
      </div>
    </div>
    <div class="book__panel" data-booking data-ws="{w["slug"]}" data-price="{w["price"]}">
      <div class="buy__top"><span class="eyebrow">Book a seat</span><span class="price">{money(w["price"])} <span class="meta">per seat</span></span></div>
      <fieldset><legend class="small ink" style="font-weight:500;margin-bottom:var(--s-3)">Choose a date</legend><div class="sessions">{sessions}</div></fieldset>
      <div class="buy__row"><span class="small ink">Seats</span><div class="qty" data-seat-qty><button type="button" data-step="-1" aria-label="Fewer seats" disabled>{icon("minus")}</button><output aria-live="polite">1</output><button type="button" data-step="1" aria-label="More seats">{icon("plus")}</button></div></div>
      <div class="total-row"><span class="small">Total</span><span class="price" data-ws-total>{money(w["price"], True)}</span></div>
      <button class="btn btn--solid btn--lg btn--block" type="button" data-book><span data-book-label>Book 1 seat</span></button>
      <p class="meta">Free cancellation up to 48 hours before. Bookings are part of the demo cart.</p>
      <a class="takeaway" href="/kits/{k["slug"]}">{img(k["gallery"][0], k["name"], "72px")}<div><p class="meta">Included</p><p class="small ink" style="font-weight:500">{e(w["takeaway_note"])}</p></div></a>
    </div>
  </div>
</div>
<section class="section" style="padding-top:0">
  <div class="container">
    {section_head("More workshops", "Other sessions this season", "", ("All workshops", "/workshops"))}
    <div class="ws-list">{"".join(ws_card(x) for x in others)}</div>
  </div>
</section>"""
    page(f"workshops/{w['slug']}.html", w["title"], w["summary"], "workshops", body, page_id="workshop")


def build_learn():
    chips = '<button class="chip is-active" type="button" data-guide-filter="">All guides</button>' + "".join(
        f'<button class="chip" type="button" data-guide-filter="{f}">{FIELDS[f]["name"]}</button>' for f in FIELD_ORDER)
    feat = GUIDES[0]
    body = f"""
<div class="container">
  <div class="page-head">
    <div class="section-head"><nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a><span>/</span><span aria-current="page">Learn</span></nav>
      <h1 class="h2">Grow guides</h1>
      <p class="lead measure">The lessons that come with every kit, free to read. Mark lessons as done and your progress stays in this browser.</p>
    </div>
  </div>
  <section class="section--tight">
    <a class="split" href="/learn/{feat["slug"]}" style="align-items:center">
      <div class="split__img">{img(feat["img"], feat["title"], "(min-width: 900px) 45vw, 100vw", eager=True)}</div>
      <div class="stack"><p class="eyebrow">Start here · {len(feat["lessons"])} lessons · {feat["read"]}</p><h2 class="h3">{e(feat["title"])}</h2><p>{e(feat["summary"])}</p><span class="btn btn--solid" style="justify-self:start;width:max-content">Start the first lesson</span></div>
    </a>
  </section>
  <div class="chip-row" style="margin-block:var(--s-7) var(--s-6);flex-wrap:wrap" data-guide-chips>{chips}</div>
  <div class="guide-grid" data-guide-grid style="padding-bottom:var(--section)">{"".join(guide_card(g) for g in GUIDES)}</div>
</div>"""
    page("learn.html", "Grow guides", "Free grow guides for hydroponics, fungi, microgreens, alternative proteins and spirulina.", "learn", body)


def build_guide(g):
    k = KIT[g["kit"]]
    lessons = "".join(
        f'<li class="lesson" data-lesson="{i}"><span class="lesson__n">{i + 1:02d}</span><div><h2>{e(t)}</h2><p class="lesson__time">{e(when)}</p><p>{e(p)}</p><ul>{"".join(f"<li>{e(x)}</li>" for x in pts)}</ul>'
        f'<label class="check lesson__done"><input type="checkbox" data-done="{i}"><span class="check__label">Mark lesson as done</span></label></div></li>'
        for i, (t, when, p, pts) in enumerate(g["lessons"]))
    w = WS.get(k["workshop"])
    ws = f'<a class="takeaway" href="/workshops/{w["slug"]}"><img src="/assets/img/{w["img"]}-sm.webp" alt="" width="72" height="90" loading="lazy"><div><p class="meta">Learn it in person</p><p class="small ink" style="font-weight:500">{e(w["title"])}</p></div></a>' if w else ""
    body = f"""
<div class="container">
  <nav class="crumbs" aria-label="Breadcrumb" style="padding-top:var(--s-6)"><a href="/learn">Learn</a><span>/</span><span aria-current="page">{e(g["title"])}</span></nav>
  <header style="display:grid;gap:var(--s-4);padding-top:var(--s-7);max-width:52rem">
    <p class="eyebrow">{FIELDS[g["field"]]["name"]} · {g["level"]} · {g["read"]} read</p>
    <h1 class="h2">{e(g["title"])}</h1>
    <p class="lead">{e(g["summary"])}</p>
  </header>
  <div class="tile" style="aspect-ratio:21/9;margin-top:var(--s-8)">{img(g["img"], g["title"], "100vw", eager=True)}</div>
  <div class="article" data-guide="{g["slug"]}" data-lessons="{len(g["lessons"])}">
    <ol class="lessons">{lessons}</ol>
    <aside class="aside">
      <div class="note"><p class="ink" style="font-weight:500">Your progress</p><div class="progress" data-progress><div class="progress__bar"><span></span></div><span data-progress-label>0 of {len(g["lessons"])}</span></div></div>
      <div class="tip"><strong>Grower’s tip.</strong> {e(g["tip"])}</div>
      <div class="stack"><p class="eyebrow">The kit for this guide</p>{kit_card(k, sizes="320px")}</div>
      {ws}
    </aside>
  </div>
</div>"""
    page(f"learn/{g['slug']}.html", g["title"], g["summary"], "learn", body, page_id="guide")


def build_about():
    steps = [("Choose a kit that fits", "Filter by the space you have, your experience, your budget and how soon you want to eat something. Every card shows level and days to harvest up front."),
             ("Grow with guided lessons", "Each kit unlocks short lessons that explain what the plant, fungus or culture is doing, step by step."),
             ("Harvest, then go further", "Pick your first harvest, then come to a workshop to try the next field. If nothing sprouts in 21 days, we replace it.")]
    steps_html = "".join(f'<div class="step"><span class="step__n">{i + 1:02d}</span><h3 class="h5">{t}</h3><p>{d}</p></div>' for i, (t, d) in enumerate(steps))
    fields4 = [("hydroponics", "roots"), ("vertical", "vertical-shelf"), ("alt-proteins", "alt-proteins"), ("fungi", "fungi-greenhouse"), ("food-tech", "food-tech")]
    fieldcards = "".join(f'<a class="field-card" href="/shop?category={key}"><div class="field-card__img">{img(im, FIELDS[key]["name"], "(min-width: 900px) 22vw, 50vw")}</div><h3>{FIELDS[key]["name"]}</h3><p>{FIELDS[key]["blurb"]}</p></a>' for key, im in fields4)
    body = f"""
<section class="about-hero">
  {img("about-greenhouse-dusk", "A glass greenhouse glowing at dusk in a meadow", eager=True)}
  <div class="container" style="padding-block:var(--s-12) var(--s-10)">
    <p class="eyebrow" style="color:rgba(255,255,255,.75)">About</p>
    <h1 class="h1">Future food should start on a kitchen counter.</h1>
    <p class="lead">We design kits and workshops that make new ways of growing food small enough to try at home, and clear enough that a first-timer actually harvests something.</p>
  </div>
</section>
<section class="section">
  <div class="container split">
    <div class="split__img">{img("about-kitchen", "A countertop hydroponic garden in a small apartment kitchen at golden hour", "(min-width: 900px) 45vw, 100vw")}</div>
    <div class="stack">
      <p class="eyebrow">Why we exist</p>
      <h2 class="h3">Most people want to try growing food. Most never start.</h2>
      <p>The hard part isn’t space or money. It’s not knowing which kit fits a small apartment, whether it’s too advanced, and whether it will actually grow. So every product here answers four questions before you buy: how much space, what level, what it costs, and how long until you eat something.</p>
    </div>
  </div>
</section>
<section class="section section--mist" id="how">
  <div class="container">
    {section_head("How it works", "From box to first harvest", "")}
    <div class="steps">{steps_html}</div>
  </div>
</section>
<section class="section">
  <div class="container">
    {section_head("What we teach", "Five fields of future food", "")}
    <div class="fields fields--5">{fieldcards}</div>
  </div>
</section>
<section class="section" id="studio" style="padding-top:0">
  <div class="container split split--flip">
    <div class="split__img">{img("about-workbench", "Seedlings, a trowel and seed envelopes on a steel greenhouse bench", "(min-width: 900px) 45vw, 100vw")}</div>
    <div class="stack">
      <p class="eyebrow">The greenhouse</p>
      <h2 class="h3">A studio for experiments you can taste</h2>
      <p>Our workshops run in a glass studio in Ann Arbor with long steel benches, four growing systems and a small tasting kitchen. Groups stay small so everyone gets their hands dirty.</p>
      <a class="btn btn--bone" href="/workshops" style="justify-self:start;width:max-content">See upcoming workshops</a>
    </div>
  </div>
</section>
<section class="section section--mist" id="notes">
  <div class="container">
    {section_head("Design notes", "About this project", "The Future Farmer’s Table is a concept store designed and built by Ella Kim for SI 407 at the University of Michigan. Products, workshops and prices are fictional, and the cart and checkout never take payment.")}
    <div class="notes">
      <div class="note"><p class="eyebrow">Problem statement</p><p class="h6">How might we help first-time growers with little space quickly find a kit that fits their space, skill level and budget, and feel sure they’ll actually harvest something?</p><p class="small">That question shaped the filters (level, space, price, time to harvest), the fit finder on the home page, the day-by-day harvest timeline on each kit, and the first-harvest promise.</p></div>
      <div class="note"><p class="eyebrow">What I learned from competitors</p><ul>
        <li><strong>Auk:</strong> calm, product-first studio photography, so every kit here is shot on the same bone sweep and cards compare at a glance.</li>
        <li><strong>Click &amp; Grow:</strong> filters with live counts. I added level and days to harvest, which their cards don’t show.</li>
        <li><strong>AeroGarden:</strong> a clear card hierarchy with a quick add. Here the add button only reacts to the button itself, never the whole card.</li></ul></div>
      <div class="note"><p class="eyebrow">Moodboard</p><ul>
        <li><strong>A24:</strong> editorial pacing and big, quiet type.</li>
        <li><strong>Nothing:</strong> precise, technical details such as mono day counters and small labels.</li>
        <li><strong>Figure and 1X:</strong> cinematic, warm photography of technology living in real homes.</li></ul></div>
      <div class="note"><p class="eyebrow">Visual direction</p><p>Organic Futurism: greenhouse photography, translucent glass buttons, brushed-metal surfaces, Syne for headings and Geist for everything you read. Green is reserved for actions and status.</p></div>
    </div>
  </div>
</section>"""
    page("about.html", "About", "Why we design kits and workshops that make future food small enough to try at home.", "about", body)


def build_404():
    popular = "".join(f'<a class="btn btn--metal btn--sm" href="/kits/{s}">{KIT[s]["name"]}</a>' for s in ["countertop-grow-kit", "microgreens-tower", "oyster-mushroom-lab"])
    body = f"""
<div class="container lost">
  <div class="stack">
    <p class="eyebrow">Error 404 · Page not found</p>
    <h1 class="h1">This page hasn’t sprouted yet.</h1>
    <p class="lead measure">The link may be broken, or the kit you’re looking for has moved to a new shelf. Let’s get you back to something growing.</p>
    <div class="hero__actions" style="margin-top:var(--s-5)"><a class="btn btn--solid" href="/">Back to home</a><a class="btn btn--bone" href="/shop">Browse all kits</a></div>
    <p class="eyebrow" style="margin-top:var(--s-7)">Popular right now</p>
    <div class="lost__popular">{popular}</div>
  </div>
  <figure class="tile">{img("roots", "A seedling with long white roots in a glass of water", "(min-width: 900px) 45vw, 100vw", eager=True)}<figcaption class="tile__cap">404&nbsp;&nbsp;Roots still forming</figcaption></figure>
</div>"""
    page("404.html", "Page not found", "This page hasn't sprouted yet.", "404", body)


# ------------------------------------------------------------------ data + extras
def write_data():
    kits = [{k2: k[k2] for k2 in ("slug", "name", "field", "level", "space", "price", "days", "soldout", "meta", "desc", "price_bucket", "time_bucket", "n", "guide")} | {"img": k["gallery"][0], "fieldName": FIELDS[k["field"]]["name"], "short": FIELDS[k["field"]]["short"]} for k in KITS]
    ws = [{"slug": w["slug"], "title": w["title"], "field": w["field"], "price": w["price"], "img": w["img"], "capacity": w["capacity"],
           "sessions": [{"id": session_id(w, s), "date": s[0], "start": s[1], "end": s[2], "seats": s[3], "label": f"{fmt_date(s[0], True)}, {fmt_time(s[1])} – {fmt_time(s[2])}", "short": f"{fmt_date(s[0])}, {fmt_time(s[1])}"} for s in w["sessions"]]} for w in WORKSHOPS]
    guides = [{"slug": g["slug"], "title": g["title"], "field": g["field"], "img": g["img"], "lessons": len(g["lessons"])} for g in GUIDES]
    js = ("// Generated by tools/build.py. Do not edit by hand.\n"
          f"export const KITS = {json.dumps(kits, ensure_ascii=False)};\n"
          f"export const WORKSHOPS = {json.dumps(ws, ensure_ascii=False)};\n"
          f"export const GUIDES = {json.dumps(guides, ensure_ascii=False)};\n"
          f"export const FIELDS = {json.dumps({k: v['name'] for k, v in FIELDS.items()}, ensure_ascii=False)};\n")
    with open(os.path.join(ROOT, "assets/js/data.js"), "w") as f:
        f.write(js)


def write_extras():
    with open(os.path.join(ROOT, "favicon.svg"), "w") as f:
        f.write(logomark(32).replace('fill="currentColor"', 'fill="#426831"'))
    with open(os.path.join(ROOT, "vercel.json"), "w") as f:
        json.dump({"cleanUrls": True, "trailingSlash": False,
                   "headers": [{"source": "/assets/img/(.*)", "headers": [{"key": "Cache-Control", "value": "public, max-age=31536000, immutable"}]}]}, f, indent=2)
    urls = ["/", "/shop", "/workshops", "/learn", "/about"] + [f"/kits/{k['slug']}" for k in KITS] + [f"/workshops/{w['slug']}" for w in WORKSHOPS] + [f"/learn/{g['slug']}" for g in GUIDES]
    with open(os.path.join(ROOT, "sitemap.txt"), "w") as f:
        f.write("\n".join(urls) + "\n")


if __name__ == "__main__":
    build_home(); build_shop(); build_cart(); build_checkout(); build_workshops(); build_learn(); build_about(); build_404()
    for k in KITS: build_product(k)
    for w in WORKSHOPS: build_workshop(w)
    for g in GUIDES: build_guide(g)
    write_data(); write_extras()
    print("built", 8 + len(KITS) + len(WORKSHOPS) + len(GUIDES), "pages")
