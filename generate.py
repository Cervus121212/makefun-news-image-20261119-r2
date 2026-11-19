#!/usr/bin/env python3
"""The World Today - Thursday 19 November 2026 (r2).

One 1024x1024 newspaper front page summing up the day's world news.
46 stories in 7 regions, 12 drawn panels, a UTC timeline, two real
photos, and a by-the-numbers box. Drawn with PIL + DejaVu/Noto fonts.

Deterministic: no clock, no randomness, no network. Run it twice and
the bytes are identical.

Usage:
    python3 generate.py [out/entry.png]
    MAKEFUN_OUTPUT_DIR=out python3 generate.py
"""

import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")

# Newsprint palette: warm paper, near-black ink, hairlines, one accent
# colour per region. Drawn panels use the same inks so the page reads
# as one printed sheet, not a collage.
PAPER = (247, 243, 234)
INK = (20, 20, 20)
INK_SOFT = (74, 74, 74)
HAIRLINE = (160, 155, 145)
GREEN_DARK = (27, 94, 32)
RED = (178, 34, 34)
PANEL = (235, 230, 220)

NA = (31, 58, 95)
LATAM = (46, 125, 50)
EUROPE = (123, 31, 48)
AFRICA = (176, 124, 20)
MEAST = (0, 121, 107)
ASIA = (178, 34, 34)
OCEANIA = (94, 53, 140)

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
NOTO_DIR = "/usr/share/fonts/truetype/noto"


def font(name, size):
    try:
        return ImageFont.truetype(os.path.join(FONT_DIR, name), size)
    except OSError:
        return ImageFont.load_default()


def serif_b(size):
    return font("DejaVuSerif-Bold.ttf", size)


def serif(size):
    return font("DejaVuSerif.ttf", size)


def sans(size):
    """Noto Sans regular (narrower than DejaVu, fits more per line)."""
    try:
        return ImageFont.truetype(os.path.join(NOTO_DIR,
                                               "NotoSans-Regular.ttf"),
                                  size)
    except OSError:
        return font("DejaVuSans.ttf", size)


def sans_b(size):
    """Noto Sans bold: all 46 brief headlines fit one line at 12px."""
    try:
        return ImageFont.truetype(os.path.join(NOTO_DIR,
                                               "NotoSans-Bold.ttf"), size)
    except OSError:
        return font("DejaVuSans-Bold.ttf", size)


def text_w(draw, text, fnt):
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0]


def wrap(draw, text, fnt, max_w):
    """Greedy word wrap. Returns lines that fit max_w."""
    lines = []
    for para in text.split("\n"):
        words = para.split()
        if not words:
            lines.append("")
            continue
        cur = words[0]
        for word in words[1:]:
            trial = cur + " " + word
            if text_w(draw, trial, fnt) <= max_w:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
    return lines


def draw_lines(draw, lines, x, y, fnt, fill, leading):
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += leading
    return y


def cover_crop(im, tw, th, focus_y=0.5):
    """Centre-crop to the target aspect, then resize (Lanczos)."""
    sw, sh = im.size
    target = tw / th
    src = sw / sh
    if src > target:
        nw = int(sh * target)
        left = (sw - nw) // 2
        im = im.crop((left, 0, left + nw, sh))
    else:
        nh = int(sw / target)
        slack = sh - nh
        top = int(slack * focus_y)
        im = im.crop((0, top, sw, top + nh))
    return im.resize((tw, th), Image.LANCZOS)


def rule(draw, x0, y, x1, width=2, fill=INK):
    draw.line([(x0, y), (x1, y)], fill=fill, width=width)


# ---------------------------------------------------------------- icons
# Every icon is drawn with vector primitives: no clip art, no pasted
# bitmaps. They are the page's drawn panels, counted in the README.
# All icons take s = the side of the square box they draw inside.

def draw_globe(draw, x, y, s, color, width=2):
    """A small world: circle, two meridians, one parallel."""
    r = s // 2
    draw.ellipse([x, y, x + s, y + s], outline=color, width=width)
    cx, cy = x + r, y + r
    draw.ellipse([cx - r // 2, y, cx + r // 2, y + s],
                 outline=color, width=width)
    draw.line([(x, cy), (x + s, cy)], fill=color, width=width)
    draw.arc([x, y + r // 3, x + s, y + s - r // 3],
             start=200, end=340, fill=color, width=width)


def draw_sun(draw, x, y, s, color, width=2):
    """Disc with eight short rays, contained in an s-by-s box."""
    cx, cy = x + s // 2, y + s // 2
    r = s // 2 - 4
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color,
                 width=width)
    for k in range(8):
        ang = math.radians(k * 45)
        x1 = cx + int((r + 1) * math.cos(ang))
        y1 = cy + int((r + 1) * math.sin(ang))
        x2 = cx + int((s // 2 - 1) * math.cos(ang))
        y2 = cy + int((s // 2 - 1) * math.sin(ang))
        draw.line([(x1, y1), (x2, y2)], fill=color, width=width)


def draw_star(draw, x, y, s, color):
    """Five-point star, filled, contained in an s-by-s box."""
    cx, cy = x + s // 2, y + s // 2
    r = s // 2 - 1
    pts = []
    for k in range(10):
        ang = math.radians(-90 + k * 36)
        rr = r if k % 2 == 0 else int(r * 0.42)
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    draw.polygon(pts, fill=color)


def draw_eu_stars(draw, x, y, s, color):
    """Twelve dots in a circle, the European flag's ring."""
    cx, cy = x + s // 2, y + s // 2
    rr = s // 2 - 4
    for k in range(12):
        ang = math.radians(k * 30 - 90)
        px = cx + int(rr * math.cos(ang))
        py = cy + int(rr * math.sin(ang))
        draw.ellipse([px - 2, py - 2, px + 2, py + 2], fill=color)


def draw_acacia(draw, x, y, s, color, width=2):
    """Flat-topped acacia with a small sun."""
    cx = x + s // 2
    draw.line([(cx, y + s - 4), (cx, y + s // 2)], fill=color, width=width)
    draw.line([(cx, y + s // 2), (cx - 6, y + s // 2 + 6)],
              fill=color, width=width)
    draw.ellipse([x + 3, y + 6, x + s - 3, y + s // 2 + 4], fill=color)
    draw.ellipse([x + s - 8, y + 1, x + s - 2, y + 7], outline=color,
                 width=width)


def draw_drop(draw, x, y, s, color):
    """An oil drop: round body, pointed top."""
    cx = x + s // 2
    draw.polygon([(cx, y + 2), (cx - s // 3, y + s // 2),
                  (cx + s // 3, y + s // 2)], fill=color)
    draw.ellipse([x + 3, y + s // 2 - 4, x + s - 3, y + s - 2], fill=color)


def draw_torii(draw, x, y, s, color, width=3):
    """A torii gate: two pillars, two crossbars."""
    draw.line([(x + 5, y + 8), (x + s - 5, y + 8)], fill=color, width=width)
    draw.line([(x + 8, y + 15), (x + s - 8, y + 15)],
              fill=color, width=width)
    draw.line([(x + 9, y + 8), (x + 9, y + s - 2)], fill=color, width=width)
    draw.line([(x + s - 9, y + 8), (x + s - 9, y + s - 2)],
              fill=color, width=width)


def draw_wave(draw, x, y, s, color, width=2):
    """Three stacked wave arcs and a sun dot, in an s-by-s box."""
    for k in range(3):
        yy = y + 4 + k * 7
        draw.arc([x + 2, yy, x + s - 2, yy + 10], start=200, end=340,
                 fill=color, width=width)
    draw.ellipse([x + s - 10, y, x + s - 4, y + 6], fill=color)


# ---------------------------------------------------------------- flags
# The hero panel flies the three summit flags on poles.

def draw_us_flag(draw, x, y, w, h):
    for k in range(13):
        y0 = y + k * h // 13
        y1 = y + (k + 1) * h // 13
        col = (178, 34, 52) if k % 2 == 0 else (255, 255, 255)
        draw.rectangle([x, y0, x + w - 1, y1 - 1], fill=col)
    cw, ch = w * 2 // 5, h * 7 // 13
    draw.rectangle([x, y, x + cw - 1, y + ch - 1], fill=(60, 59, 110))
    for r in range(5):
        for c in range(6):
            px = x + 4 + c * 5
            py = y + 4 + r * 5
            draw.ellipse([px, py, px + 1, py + 1], fill=(255, 255, 255))
    draw.rectangle([x, y, x + w - 1, y + h - 1], outline=INK, width=1)


def draw_cn_flag(draw, x, y, w, h):
    draw.rectangle([x, y, x + w - 1, y + h - 1], fill=(222, 0, 0))
    gold = (255, 222, 0)
    draw_star(draw, x + 6, y + 6, 16, gold)
    for sx, sy in ((30, 6), (36, 12), (36, 20), (30, 25)):
        draw_star(draw, x + sx, y + sy, 7, gold)
    draw.rectangle([x, y, x + w - 1, y + h - 1], outline=INK, width=1)


def draw_ru_flag(draw, x, y, w, h):
    draw.rectangle([x, y, x + w - 1, y + h // 3 - 1], fill=(255, 255, 255))
    draw.rectangle([x, y + h // 3, x + w - 1, y + 2 * h // 3 - 1],
                   fill=(0, 57, 166))
    draw.rectangle([x, y + 2 * h // 3, x + w - 1, y + h - 1],
                   fill=(204, 0, 0))
    draw.rectangle([x, y, x + w - 1, y + h - 1], outline=INK, width=1)


def draw_flags_scene(draw, x0, y0, w, h):
    """Drawn hero panel: the three flags on poles, first trilateral."""
    draw.rectangle([x0, y0, x0 + w - 1, y0 + h - 1], fill=PANEL)
    draw.text((x0 + 12, y0 + 8), "FIRST-EVER TRILATERAL",
              font=sans_b(13), fill=INK)
    fw, fh = 84, 56
    fy = y0 + 44
    xs = [x0 + 12, x0 + 108, x0 + 204]
    for fx in xs:
        draw.line([(fx + fw // 2, fy - 16), (fx + fw // 2, fy)],
                  fill=INK, width=2)
        draw.ellipse([fx + fw // 2 - 3, fy - 20, fx + fw // 2 + 3,
                      fy - 14], fill=INK)
    draw_us_flag(draw, xs[0], fy, fw, fh)
    draw_cn_flag(draw, xs[1], fy, fw, fh)
    draw_ru_flag(draw, xs[2], fy, fw, fh)
    draw.line([(x0 + 12, fy + fh + 6), (x0 + w - 12, fy + fh + 6)],
              fill=HAIRLINE, width=1)
    draw.text((x0 + 12, y0 + h - 32), "KYLIN VILLA, SHENZHEN — 14:30",
              font=sans_b(13), fill=INK)


# ---------------------------------------------------------------- data
# Every story was checked against reporting of 19 November 2026.
# Headline <= 30 chars (one line at 12px bold in a 221px column),
# deck <= 32 chars (one line at 11px), source tag = the outlet.

LEAD = {
    "kicker": "DIPLOMACY  ·  SUMMIT",
    "head": "TRUMP, XI AND PUTIN MEET\nIN SHENZHEN",
    "deck": "First three-way summit at Kylin Villa, 14:30 — no big deal expected.",
    "facts": "New START expires Feb 2026  ·  Xi opened APEC with $20m  ·  Trump–Putin bilateral too",
}

PHOTOS = [
    {"file": "vangogh.jpg", "focus_y": 0.35, "w": 230,
     "mini": "VAN GOGH SELLS FOR $190.4M",
     "cap": "Blossoming Chestnut Trees, 1890."},
    {"file": "trump_xi.jpg", "focus_y": 0.45, "w": 722,
     "mini": "TRUMP AND XI BEFORE THE SUMMIT",
     "cap": "Trump and Xi at Zhongnanhai in May. (White House)"},
]

TIMELINE = [
    ("00:00", "Van Gogh sells for $190.4m"),
    ("00:10", "Gaza ground op under way"),
    ("02:01", "RLWC26 teams announced"),
    ("05:00", "GTA VI out in the US"),
    ("05:23", "Xi pledges $20m for APEC"),
    ("06:30", "Trilateral at Kylin Villa"),
    ("16:00", "GTA VI scores 99 on Metacritic"),
]

# (headline, deck, source)
NA_BRIEFS = [
    ("JEFFRIES PICKED FOR SPEAKER", "First Black Speaker nominee.", "AP"),
    ("PELTOLA WINS ALASKA SENATE", "Dems take Senate 56-44.", "AP"),
    ("GTA VI LAUNCHES WORLDWIDE", "13 years after GTA V.", "AP"),
    ("ANTHROPIC IPO HITS $81.3BN", "Largest listing ever.", "AP"),
    ("VOYAGER 1 HITS ONE LIGHT-DAY", "50 years after launch.", "NASA"),
    ("GTA VI AT 30 FPS ON CONSOLE", "No 60 FPS mode at launch.", "AP"),
    ("TRUMP, PUTIN TO MEET ALONE", "One-on-one also planned.", "AP"),
]

LATAM_BRIEFS = [
    ("ISOLATED AWÁ SEEN IN AMAZON", "Rare images raise alarm.", "AJ"),
    ("HAITIANS BACK SALVADOR TROOPS", "Protest supports deployment.", "AJ"),
    ("VINICIUS TREBLE IN 7-0 WIN", "12-minute hat-trick.", "AJ"),
    ("GTA VI PARTIES SWEEP LATAM", "Mexico to Brazil celebrate.", "AP"),
    ("CARACAS TALKS OPEN ROUND FOUR", "Government, opposition meet.", "AP"),
    ("SHEINBAUM, TRUMP TALK TRADE", "Mexico at APEC table.", "APEC"),
]

EU_BRIEFS = [
    ("ESTONIA TO SHUT RUSSIA BORDER", "Closure planned from Dec.", "AP"),
    ("PRAGUE PROTESTS MEDIA LAW", "Hundreds of thousands march.", "AP"),
    ("SPAIN GENERAL STRIKE BITES", "Ports, factories disrupted.", "AP"),
    ("MÉLENCHON COULD WIN IN FRANCE", "Justice minister's warning.", "AP"),
    ("COP31: 144 ITEMS STILL DISPUTED", "Draft admits 1.5°C missed.", "AP"),
    ("VANUATU DEMANDS COP31 REFORM", "Warns of backsliding.", "AP"),
    ("EU WARNS CHINA OVER TAIWAN", "Metsola hits intimidation.", "AP"),
    ("GERMANY SHIELDS UKRAINE AID", "Proof against Le Pen.", "AP"),
]

AF_BRIEFS = [
    ("TROOPS MASS ON ETHIOPIA BORDER", "Eritrea denies clash reports.", "AP"),
    ("KENYA DROUGHT HITS MILK SUPPLY", "Shortages worsen.", "AP"),
    ("NIGERIA POLICE BILL ADVANCES", "Tinubu backs state police.", "AP"),
    ("AFCON 2027: NINE TEAMS THROUGH", "Hosts + six qualify.", "AP"),
    ("NIGERIA RISES TO FIFA RANK 29", "Top five in Africa.", "FIFA"),
    ("NIGERIA HELD 0-0 BY TANZANIA", "Must win in March.", "AP"),
]

ME_BRIEFS = [
    ("PEACE BOARD WARNS BOTH SIDES", "UN told truce is failing.", "AP"),
    ("IRAN URANIUM UNVERIFIABLE: IAEA", "Stockpile goes unverifiable.", "IAEA"),
    ("NETANYAHU PRESSES U.S. ON IRAN", "Seeks strikes on Tehran.", "AP"),
    ("ISRAELI SPY CHIEF LOBBIES U.S.", "Joint Iran strikes urged.", "AP"),
    ("KUWAIT REPELS IRANIAN ATTACK", "One missing, 11 injured.", "AP"),
    ("SAUDI-LED STRIKES HIT YEMEN", "Coalition hits Houthis.", "AP"),
    ("KAHANA ELECTED KNESSET SPEAKER", "66 votes; no coalition yet.", "AP"),
]

AS_BRIEFS = [
    ("XI OPENS APEC WITH $20M PLEDGE", "Asia-Pacific cooperation fund.", "AP"),
    ("XI, PUTIN PUSH MULTIPOLAR ORDER", "APEC talks in Shenzhen.", "AP"),
    ("CHINA SNUBS TAKAICHI AT APEC", "Cool welcome in Shenzhen.", "AP"),
    ("TAKAICHI, PUTIN TALK 30 MINUTES", "Japan on alert over summit.", "AP"),
    ("INDIA, JAPAN HOLD 2+2 TALKS", "Defence, foreign ministers.", "AP"),
    ("BANGLADESH WAGE PROTESTS", "Third week; factories shut.", "AP"),
    ("AKVAN NEARS LANDFALL", "Machilipatnam–Puri, 20 Nov.", "IMD"),
    ("INDIA VS NZ TEST IN WELLINGTON", "First Test starts today.", "AP"),
    ("SINDHU BACK IN TOP FIVE", "Badminton rankings.", "AP"),
]

OC_BRIEFS = [
    ("FIJI DROUGHT EMERGENCY GROWS", "Dry spell may last to 2027.", "AP"),
    ("CYCLONE XAVIER MENACES PACIFIC", "Winds, seas dangerous.", "AP"),
    ("RLWC26 TEAMS ANNOUNCED", "Nine nations honoured.", "NRL"),
]

# Columns: (region name, colour, icon fn, briefs). Balanced so no
# column overflows the grid budget.
COLUMNS = [
    [("NORTH AMERICA", NA, draw_star, NA_BRIEFS),
     ("LATIN AMERICA", LATAM, draw_sun, LATAM_BRIEFS)],
    [("EUROPE", EUROPE, draw_eu_stars, EU_BRIEFS),
     ("OCEANIA", OCEANIA, draw_wave, OC_BRIEFS)],
    [("AFRICA", AFRICA, draw_acacia, AF_BRIEFS),
     ("MIDDLE EAST", MEAST, draw_drop, ME_BRIEFS)],
    [("ASIA-PACIFIC", ASIA, draw_torii, AS_BRIEFS)],
]

NUMBERS = [
    ("Van Gogh sale", "$190.4m"),
    ("Anthropic IPO", "$81.3bn"),
    ("GTA VI Metascore", "99 / 147"),
    ("Xi APEC pledge", "$20m"),
    ("COP31 disputed items", "144"),
    ("Kahana speaker votes", "66"),
    ("APEC economies", "21"),
    ("AFCON teams qualified", "9"),
]


# ---------------------------------------------------------------- layout

def draw_masthead(draw):
    """Nameplate, date line, rules. Plus a globe and a sun, drawn."""
    y = 10
    draw_globe(draw, 40, 18, 30, INK)
    draw_sun(draw, W - 70, 18, 30, INK)
    title = "THE WORLD TODAY"
    fnt = serif_b(50)
    tw = text_w(draw, title, fnt)
    draw.text(((W - tw) // 2, y), title, font=fnt, fill=INK)
    y = 72
    rule(draw, 28, y, W - 28, width=3)
    y += 8
    left = "THURSDAY 19 NOVEMBER 2026"
    mid = "46 STORIES  ·  7 REGIONS  ·  DATE-CHECKED"
    right = "WORLD NEWS IN ONE PAGE"
    draw.text((28, y), left, font=sans_b(16), fill=INK)
    mw = text_w(draw, mid, sans(14))
    draw.text(((W - mw) // 2, y + 1), mid, font=sans(14), fill=INK_SOFT)
    rw = text_w(draw, right, sans(14))
    draw.text((W - 28 - rw, y + 1), right, font=sans(14), fill=INK_SOFT)
    y += 24
    rule(draw, 28, y, W - 28, width=1, fill=HAIRLINE)
    return y + 8


def draw_lead(draw, page, top):
    """Hero drawn panel left; kicker, headline, deck, facts right."""
    x0, y0 = 28, top
    x = 344
    # Measure the text column first: the flags panel must be exactly as
    # tall as the text, or the photo band below overlaps the deck.
    head_lines = LEAD["head"].split("\n")
    if len(head_lines) > 2:
        raise ValueError("lead headline must fit two lines")
    deck_lines = wrap(draw, LEAD["deck"], sans(17), 652)
    total = 2 + 24 + len(head_lines) * 36 + 4 + len(deck_lines) * 21 \
        + 4 + 16 + 4
    draw_flags_scene(draw, x0, y0, 300, total)
    draw.rectangle([x0, y0, x0 + 299, y0 + total - 1], outline=INK, width=2)
    y = y0 + 2
    f_kick = sans_b(17)
    draw.text((x, y), LEAD["kicker"], font=f_kick, fill=GREEN_DARK)
    kw = text_w(draw, LEAD["kicker"], f_kick)
    draw.line([(x + kw + 10, y + 9), (x + kw + 46, y + 9)],
              fill=GREEN_DARK, width=3)
    y += 24
    y = draw_lines(draw, head_lines, x, y, serif_b(34), INK, 36)
    y += 4
    y = draw_lines(draw, deck_lines, x, y, sans(17), INK_SOFT, 21)
    y += 4
    draw.text((x, y), LEAD["facts"], font=sans_b(13), fill=INK)
    return y0 + total


def draw_photos(draw, page, top):
    """Two real photos with mini-headlines and captions."""
    y = top
    x = 28
    bottom = y
    for ph in PHOTOS:
        w = ph["w"]
        f_mini = sans_b(13)
        if text_w(draw, ph["mini"], f_mini) > w:
            raise ValueError("mini-headline too wide: %r" % ph["mini"])
        draw.text((x, y), ph["mini"], font=f_mini, fill=INK)
        py = y + 20
        photo = Image.open(os.path.join(ASSETS, ph["file"])).convert("RGB")
        ph_im = cover_crop(photo, w, 118, focus_y=ph["focus_y"])
        page.paste(ph_im, (x, py))
        draw.rectangle([x, py, x + w - 1, py + 117], outline=INK, width=2)
        cy = py + 118 + 4
        cap = wrap(draw, ph["cap"], sans(11), w)
        for line in cap:
            draw.text((x, cy), line, font=sans(11), fill=INK_SOFT)
            cy += 13
        bottom = max(bottom, cy)
        x += w + 16
    return bottom + 4


def draw_timeline(draw, top):
    """The day in UTC: label on its own row, times, line, labels."""
    y = top
    draw_globe(draw, 28, y, 14, INK)
    draw.text((46, y + 1), "THE DAY IN UTC", font=sans_b(12), fill=INK)
    line_y = y + 30
    x0, x1 = 28, 996
    draw.line([(x0, line_y), (x1, line_y)], fill=HAIRLINE, width=2)
    n = len(TIMELINE)
    for i, (t, label) in enumerate(TIMELINE):
        cx = x0 + int((x1 - x0) * (i + 0.5) / n)
        draw.ellipse([cx - 4, line_y - 4, cx + 4, line_y + 4],
                     fill=RED, outline=INK, width=1)
        tw = text_w(draw, t, sans_b(11))
        draw.text((cx - tw // 2, y + 15), t, font=sans_b(11), fill=RED)
        ll = wrap(draw, label, sans(10), 128)
        ly = line_y + 7
        for ln in ll[:2]:
            lw = text_w(draw, ln, sans(10))
            draw.text((cx - lw // 2, ly), ln, font=sans(10), fill=INK_SOFT)
            ly += 10
    return y + 58


def draw_region_head(draw, x, y, w, name, color, icon, count):
    """Coloured square with a drawn glyph, name, story count, rule."""
    draw.rectangle([x, y, x + 33, y + 33], fill=color)
    icon(draw, x + 2, y + 2, 30, (255, 255, 255))
    fnt = sans_b(14)
    draw.text((x + 42, y + 7), name, font=fnt, fill=INK)
    cnt = "%d" % count
    cw = text_w(draw, cnt, sans_b(14))
    draw.text((x + w - cw, y + 7), cnt, font=sans_b(14), fill=color)
    rule(draw, x, y + 36, x + w, width=2, fill=color)
    return y + 42


def draw_brief(draw, x, y, w, head, deck, source, color):
    """One story: bold headline (one line), deck + source tag."""
    f_head = sans_b(12)
    if text_w(draw, head, f_head) > w:
        raise ValueError("headline too long for one line: %r" % head)
    draw.text((x, y), head, font=f_head, fill=INK)
    y += 13
    f_deck = sans(11)
    line = deck + "  ·  " + source
    if text_w(draw, line, f_deck) > w:
        raise ValueError("deck+source too long: %r" % line)
    draw.text((x, y), deck, font=f_deck, fill=INK_SOFT)
    dw = text_w(draw, deck + "  ·  ", f_deck)
    draw.text((x + dw, y), source, font=sans_b(11), fill=color)
    return y + 11 + 4


def draw_numbers(draw, x, y, w, h):
    """By-the-numbers box: eight stats from the day."""
    if h < 150:
        raise ValueError("numbers box too small: %d px" % h)
    draw.rectangle([x, y, x + w - 1, y + h - 1], outline=INK, width=2)
    draw.rectangle([x, y, x + w - 1, y + 22], fill=INK)
    draw.text((x + 8, y + 4), "BY THE NUMBERS", font=sans_b(13),
              fill=PAPER)
    yy = y + 30
    for label, val in NUMBERS:
        draw.text((x + 8, yy), label, font=sans(12), fill=INK_SOFT)
        vw = text_w(draw, val, sans_b(12))
        draw.text((x + w - 8 - vw, yy), val, font=sans_b(12), fill=INK)
        yy += 15
    if yy + 4 > y + h:
        raise ValueError("numbers content overflows box by %d px"
                         % (yy + 4 - y - h))
    return y + h


def draw_grid(draw, top, bottom):
    """Four columns of region blocks; fail loudly on overflow."""
    cols_x = [28, 272, 516, 760]
    col_w = 221
    for ci, col in enumerate(COLUMNS):
        x = cols_x[ci]
        y = top
        for name, color, icon, briefs in col:
            y = draw_region_head(draw, x, y, col_w, name, color, icon,
                                 len(briefs))
            for head, deck, source in briefs:
                y = draw_brief(draw, x, y, col_w, head, deck, source,
                               color)
            y += 6
        if y - 6 > bottom:
            raise ValueError("column %d overflows grid by %d px"
                             % (ci, y - 6 - bottom))
        if ci == 3:
            # Asia column ends early: fill the rest with the numbers box.
            box_h = bottom - (y - 6) - 4
            if box_h < 150:
                raise ValueError("numbers box too small: %d px" % box_h)
            draw_numbers(draw, x, y - 6 + 4, col_w, box_h)


def draw_footer(draw):
    y = H - 34
    rule(draw, 28, y, W - 28, width=1, fill=HAIRLINE)
    fnt = sans(11)
    line = ("Photos: Trump and Xi (White House)  ·  Van Gogh, 1890 "
            "(public domain)  ·  12 drawn panels  ·  Sources: AP, "
            "Reuters, AFP, UN, IAEA, NRL, AJ  ·  Date-checked 19 Nov 2026")
    tw = text_w(draw, line, fnt)
    if tw > W - 56:
        raise ValueError("footer too wide: %d px" % tw)
    draw.text(((W - tw) // 2, y + 8), line, font=fnt, fill=INK_SOFT)


def build():
    page = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(page)
    y = draw_masthead(draw)
    y = draw_lead(draw, page, y + 4)
    y = draw_photos(draw, page, y + 8)
    y = draw_timeline(draw, y + 8)
    draw_grid(draw, y + 8, 972)
    draw_footer(draw)
    return page


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "")
    if len(sys.argv) > 1:
        out = sys.argv[1]
    elif outdir:
        out = os.path.join(outdir, "entry.png")
    else:
        out = os.path.join(HERE, "entry.png")
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    page = build()
    page.save(out, format="PNG", optimize=True)
    size = os.path.getsize(out)
    print("wrote %s (%d bytes, %dx%d)" % (out, size, W, H))
    if size > 1048576:
        print("ERROR: over the 1 MiB limit")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
