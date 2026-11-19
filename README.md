# The World Today — Thursday 19 November 2026

One 1024×1024 newspaper front page summing up the day's world news:
**46 stories in 7 regions, 12 drawn panels, a UTC timeline, two real
photos, and a by-the-numbers box.** Every fact was checked against
reporting of 19 November 2026 (AP, Reuters, AFP, UN, IAEA, NRL, AJ,
NASA, IMD, FIFA, APEC); every story carries its source tag on the
page.

## What is on the page

- **Lead:** Trump, Xi and Putin meet in Shenzhen — the first-ever
  trilateral of sitting US, Chinese and Russian presidents, at Kylin
  Villa, 14:30, on the APEC sidelines; no big deal expected, New
  START expires February 2026, Xi opened APEC with a $20m pledge.
  The hero panel is drawn: the three flags on poles.
- **Photos (real, freely licensed):** Van Gogh's *Blossoming
  Chestnut Trees* (1890, public domain) — sold for $190.4m, a record
  for the artist; Trump and Xi at Zhongnanhai in May (White House,
  public domain). Captions are honest about when each photo was
  taken.
- **The day in UTC:** seven timed beats from the Van Gogh sale
  (00:00) to GTA VI's 99 Metascore (16:00).
- **Regions:** North America 7, Latin America 6, Europe 8, Oceania 3,
  Africa 6, Middle East 7, Asia-Pacific 9 — each with a drawn glyph
  (star, sun, EU ring, acacia, oil drop, torii, wave) and a story
  count.
- **By the numbers:** Van Gogh sale, Anthropic IPO, GTA VI
  Metascore, Xi's APEC pledge, COP31 disputed items, Kahana's
  speaker votes, APEC economies, AFCON teams qualified.

## Rebuild

```sh
python3 generate.py            # writes entry.png (1024x1024)
python3 generate.py entry.png  # same, explicit path
```

Deterministic: no clock, no randomness, no network. Two runs produce
byte-identical PNGs (sha256 verified). The generator raises instead of
drawing overflows — a headline, deck, column, or box that does not
fit fails loudly rather than printing clipped text.

## Files

- `generate.py` — the whole page: layout, drawn panels, data.
- `main.py` — harness entry point; copies `entry.png` to
  `$MAKEFUN_OUTPUT_DIR/entry.png`.
- `entry.png` — the rendered front page.
- `assets/` — the two photos used on the page.
