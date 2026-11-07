# -*- coding: utf-8 -*-
"""Eldenvale v1.5 - desa, interior rumah & ladang, semuanya dibangun lewat KODE.

Desa = tilemap (rumput, jalan tanah, batu plaza, sungai, kolam, jembatan) yang digambar dari tekstur buatan kode,
lalu ditata dengan sprite (bangunan, pohon, taman). Objek tinggi (rumah, pohon) diurutkan menurut sumbu-Y bersama
pemain & NPC, jadi karakter bisa berjalan DI BELAKANG pohon/rumah. Interior dibuat per-ruangan dari lantai papan,
dinding kayu, dan perabot. Ladang punya 96 petak: cangkul -> tanam -> siram -> tumbuh tiap hari -> panen.
"""
import os, math, random
import pygame

TS = 40                      # ukuran 1 tile (piksel dunia)
_BASE = os.path.dirname(os.path.abspath(__file__))
_SC = {}


# ------------------------------------------------------------------ sprite
def _ph(w=40, h=40):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(s, (214, 92, 140, 160), (0, 0, w, h), 2)
    return s


def spr(name, w=None, h=None, flip=False):
    """Sprite dari assets/spr, diskalakan ke lebar/tinggi (rasio dijaga) dan di-cache."""
    k = (name, w, h, flip)
    s = _SC.get(k)
    if s is not None: return s
    base = _SC.get(name)
    if base is None:
        try: base = pygame.image.load(os.path.join(_BASE, 'assets', 'spr', name + '.png')).convert_alpha()
        except Exception: base = _ph()
        _SC[name] = base
    bw, bh = base.get_size()
    if w is None and h is None: w, h = bw, bh
    elif w is None: w = max(1, int(bw * h / float(bh)))
    elif h is None: h = max(1, int(bh * w / float(bw)))
    s = pygame.transform.smoothscale(base, (int(w), int(h))) if (w, h) != (bw, bh) else base
    if flip: s = pygame.transform.flip(s, True, False)
    _SC[k] = s
    return s


# ------------------------------------------------------------------ tekstur buatan kode
def _shade(c, d): return tuple(max(0, min(255, v + d)) for v in c)


def _speckle(s, rng, cols, n):
    for _ in range(n):
        s.set_at((rng.randrange(TS), rng.randrange(TS)), rng.choice(cols))


def tex_grass(rng):
    s = pygame.Surface((TS, TS)); s.fill((88, 172, 54))
    _speckle(s, rng, [(104, 190, 66), (72, 150, 44), (118, 204, 76), (80, 160, 48)], 90)
    for _ in range(4):   # rumput kecil
        x, y = rng.randrange(3, TS - 3), rng.randrange(5, TS - 1)
        c = rng.choice([(124, 212, 84), (64, 140, 40)])
        pygame.draw.line(s, c, (x, y), (x - 1, y - 3)); pygame.draw.line(s, c, (x, y), (x + 1, y - 4))
    return s


def tex_dirt(rng):
    s = pygame.Surface((TS, TS)); s.fill((196, 150, 94))
    _speckle(s, rng, [(176, 132, 80), (214, 170, 114), (160, 120, 72), (206, 160, 104)], 110)
    for _ in range(2):
        x, y = rng.randrange(2, TS - 4), rng.randrange(2, TS - 4)
        pygame.draw.rect(s, (150, 146, 140), (x, y, 3, 2)); s.set_at((x, y), (190, 186, 178))
    return s


def tex_cobble(rng, tone=0):
    s = pygame.Surface((TS, TS)); s.fill((104, 102, 112))   # semen
    y = 0
    for row in range(2):
        x = 0 if row == 0 else -rng.randrange(5, 12)
        while x < TS:
            w = rng.randrange(13, 22)
            col = _shade((178, 174, 168), rng.randrange(-16, 14) + tone)
            r = pygame.Rect(x + 1, y + 1, w - 2, TS // 2 - 2)
            pygame.draw.rect(s, col, r, border_radius=4)
            pygame.draw.line(s, _shade(col, 22), (r.x + 2, r.y + 1), (r.right - 3, r.y + 1))
            pygame.draw.line(s, _shade(col, -26), (r.x + 2, r.bottom - 1), (r.right - 3, r.bottom - 1))
            if rng.random() < 0.3: s.set_at((r.x + rng.randrange(3, max(4, r.w - 3)), r.y + rng.randrange(3, r.h - 3)), _shade(col, -34))
            x += w
        y += TS // 2
    return s


def tex_water(rng):
    s = pygame.Surface((TS, TS)); s.fill((46, 150, 228))
    _speckle(s, rng, [(60, 166, 238), (36, 134, 214)], 50)
    for _ in range(3):
        x, y = rng.randrange(2, TS - 12), rng.randrange(3, TS - 3)
        pygame.draw.line(s, (136, 208, 250), (x, y), (x + rng.randrange(6, 12), y))
    return s


def tex_soil(rng, kind):
    """kind 0 = tanah belum dicangkul, 1 = dicangkul (alur), 2 = disiram (gelap)."""
    base = [(150, 108, 66), (118, 78, 44), (84, 54, 34)][kind]
    s = pygame.Surface((TS, TS)); s.fill(base)
    _speckle(s, rng, [_shade(base, 14), _shade(base, -14)], 60)
    if kind:
        for yy in (6, 17, 28):
            pygame.draw.line(s, _shade(base, -26), (1, yy), (TS - 2, yy), 3)
            pygame.draw.line(s, _shade(base, 20), (1, yy - 2), (TS - 2, yy - 2), 1)
    else:
        for _ in range(5): s.set_at((rng.randrange(TS), rng.randrange(TS)), (96, 168, 56))
    pygame.draw.rect(s, _shade(base, -34), (0, 0, TS, TS), 1)
    return s


_BL = {}


def blob(dst, x, y, r, col, a):
    k = (r, col, a); s = _BL.get(k)
    if s is None:
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, col + (a,), (r, r), r); _BL[k] = s
    dst.blit(s, (x - r, y - r))


def shadow(dst, cx, by, w, h, a=70):
    k = ('sh', w, h, a); s = _BL.get(k)
    if s is None:
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (10, 20, 10, a), (0, 0, w, h)); _BL[k] = s
    dst.blit(s, (cx - w // 2, by - h // 2))


_GL = {}


def glow_surf(r, col):
    k = (r, col); s = _GL.get(k)
    if s is None:
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        for i in range(r, 0, -3):
            f = 1.0 - i / float(r)
            pygame.draw.circle(s, col + (int(110 * f * f + 6),), (r, r), i)
        _GL[k] = s
    return s


# ------------------------------------------------------------------ dunia desa
# Latar = gambar desa buatan (assets/town_bg.png, 1672x941) diskalakan KS kali. Tebing & air menjadi tabrakan lewat
# assets/town_mask.png (sel 8 piksel gambar asli: R = terblokir, G = air, B = rumput kosong untuk dekorasi).
KS = 2.0
MW, MH = int(1672 * KS), int(941 * KS)
CELL = int(8 * KS)


class Town:
    def hit(self, r):
        """True jika kotak r menyentuh sel tebing/air/tepi peta."""
        if r.left < 24 or r.top < 24 or r.right > MW - 24 or r.bottom > MH - 8: return True
        m, cw = self.mask, self.mw
        for cy in range(max(0, r.top // CELL), min(self.mh, r.bottom // CELL + 1)):
            row = m[cy]
            for cx in range(max(0, r.left // CELL), min(cw, r.right // CELL + 1)):
                if row[cx]: return True
        return False


# (id, sprite, pusat-x, dasar-y, lebar) dalam koordinat dunia
BUILDINGS = [
    ('church', 'b_church', 1676, 536, 400), ('inn', 'b_inn', 780, 690, 300), ('windmill', 'b_windmill', 1090, 662, 240),
    ('potion', 'b_potion', 2100, 680, 280), ('green', 'b_green', 2500, 690, 300), ('smith', 'b_smith', 660, 1470, 280),
]
FARM = dict(c0=49, r0=29, cols=11, rows=5)
FARM_RECT = pygame.Rect(FARM['c0'] * TS, FARM['r0'] * TS, FARM['cols'] * TS, FARM['rows'] * TS)

NPC_POS = {
    'Sir Aldric': (1700, 610), 'Mira': (1300, 800), 'Cale si Pedagang': (2060, 806), 'Anya': (820, 800),
    'Fenn si Pemanah': (2400, 800), 'Kesatria Ines': (1480, 640), 'Madam Ruby': (1880, 640), 'Penyihir Selene': (1330, 940),
    'Kakek Odo': (1420, 1030), 'Penjaga Gerbang': (1640, 1790), 'Putri Elara': (2000, 930), 'Petani Tomo': (2270, 1108),
}
SPAWN = (1700, 960)


def build_town():
    rng = random.Random(1507)
    ground = pygame.image.load(os.path.join(_BASE, 'assets', 'town_bg.png')).convert()
    ground = pygame.transform.smoothscale(ground, (MW, MH))
    mk = pygame.image.load(os.path.join(_BASE, 'assets', 'town_mask.png'))
    mw, mh = mk.get_size()
    mask = [[mk.get_at((x, y))[0] > 128 for x in range(mw)] for y in range(mh)]
    water_tiles, freec = [], []
    for y in range(mh):
        for x in range(mw):
            c = mk.get_at((x, y))
            if c[1] > 128 and x % 2 == 0 and y % 2 == 0: water_tiles.append((x * CELL, y * CELL))
            if c[2] > 128: freec.append((x * CELL + CELL // 2, y * CELL + CELL // 2))
    tex = random.Random(77)
    soil = [tex_soil(tex, 0), tex_soil(tex, 1), tex_soil(tex, 2)]

    # --- ladang: petak tanah kosong + pagar
    for rr in range(FARM['rows']):
        for cc in range(FARM['cols']): ground.blit(soil[0], ((FARM['c0'] + cc) * TS, (FARM['r0'] + rr) * TS))
    pygame.draw.rect(ground, (84, 54, 34), FARM_RECT.inflate(6, 6), 3)

    objs, block, glows, lamp_pts = [], [], [], []
    occ = []                                  # kotak terlarang untuk dekorasi acak

    def add(im, cx, by, shadow_w=0):
        w, h = im.get_size()
        if shadow_w: shadow(ground, cx, by - 2, shadow_w, max(8, shadow_w // 4))
        objs.append((by, im, cx - w // 2, by - h))

    doors = {}
    for bid, sp, cx, by, w in BUILDINGS:
        im = spr(sp, w=w); iw, ih = im.get_size()
        add(im, cx, by, int(w * 0.95))
        block.append(pygame.Rect(cx - int(iw * 0.46), by - ih + int(ih * 0.30), int(iw * 0.92), int(ih * 0.70) - 8))
        doors[bid] = dict(trig=(cx - 22, by - 6, 44, 18), out=(cx, by + 42))
        occ.append(pygame.Rect(cx - iw // 2 - 50, by - ih, iw + 100, ih + 110))
        glows += [(cx - int(iw * 0.2), by - int(ih * 0.30), 46, (255, 190, 90)), (cx + int(iw * 0.2), by - int(ih * 0.30), 46, (255, 190, 90))]
    inn_h = int(217 * 300 / 288.0)
    smoke = [(780 - 150 + int(0.31 * 300), 690 - inn_h + 12)]

    # plaza: lampu di keempat pedestal sudut, bangku, papan misi, sumur
    for (px, py) in [(1222, 722), (2120, 722), (1222, 1044), (2120, 1044)]:
        im = spr('lampA', w=40); add(im, px, py, 30); lamp_pts.append((px, py - 84)); glows.append((px, py - 84, 120, (255, 200, 110)))
        block.append(pygame.Rect(px - 8, py - 10, 16, 10)); occ.append(pygame.Rect(px - 40, py - 110, 80, 130))
    for (px, py) in [(1480, 1030), (1900, 1030)]:
        im = spr('bench_b', w=92); add(im, px, py, 70); block.append(pygame.Rect(px - 40, py - 20, 80, 18)); occ.append(pygame.Rect(px - 60, py - 60, 120, 100))
    add(spr('board', w=96), 1500, 702, 70); block.append(pygame.Rect(1500 - 36, 702 - 28, 72, 24)); occ.append(pygame.Rect(1440, 600, 120, 130))
    add(spr('well', w=120), 940, 1090, 100); block.append(pygame.Rect(940 - 38, 1090 - 40, 76, 36)); occ.append(pygame.Rect(870, 960, 140, 150))
    for (px, py) in [(500, 742), (1020, 742), (2300, 742), (2900, 742), (360, 934), (1000, 934)]:   # lampu jalan di tepi jalan utama
        im = spr('lampC', w=26); add(im, px, py, 20); lamp_pts.append((px, py - 96)); glows.append((px, py - 96, 90, (255, 200, 110)))
        block.append(pygame.Rect(px - 6, py - 8, 12, 8)); occ.append(pygame.Rect(px - 30, py - 110, 60, 130))

    # gerbang selatan (ujung jalan)
    gi = spr('gate_arch', w=270); add(gi, 1676, MH - 6, 0)
    block += [pygame.Rect(1676 - 135 + 4, MH - 6 - 70, 52, 66), pygame.Rect(1676 + 135 - 56, MH - 6 - 70, 52, 66)]
    lamp_pts += [(1676 - 112, MH - 106), (1676 + 112, MH - 106)]; glows += [(1676 - 112, MH - 106, 100, (255, 200, 110)), (1676 + 112, MH - 106, 100, (255, 200, 110))]
    occ.append(pygame.Rect(1500, MH - 260, 360, 260))
    gate = pygame.Rect(1616, MH - 38, 120, 30); gate_out = (1676, MH - 110)

    # ladang: pagar kayu (celah di sisi barat untuk jalan), kios benih
    fx0, fy0, fx1, fy1 = FARM_RECT.x - 36, FARM_RECT.y - 36, FARM_RECT.right + 36, FARM_RECT.bottom + 36
    for xx in range(fx0, fx1, 80):
        w_ = min(80, fx1 - xx); add(spr('fenceA', w=w_), xx + w_ // 2, fy0 + 20, 0); add(spr('fenceA', w=w_), xx + w_ // 2, fy1 + 20, 0)
    block += [pygame.Rect(fx0, fy0 + 4, fx1 - fx0, 12), pygame.Rect(fx0, fy1 + 4, fx1 - fx0, 12)]
    gy0, gy1 = fy0 + 120, fy0 + 190            # celah gerbang di sisi barat
    for (xx, y0, y1) in [(fx0 - 4, fy0 + 10, gy0), (fx0 - 4, gy1, fy1 + 14), (fx1 - 4, fy0 + 10, fy1 + 14)]:
        pygame.draw.rect(ground, (96, 58, 26), (xx, y0, 8, y1 - y0)); pygame.draw.rect(ground, (150, 100, 50), (xx + 1, y0, 3, y1 - y0))
        for yy in range(y0, y1, TS): pygame.draw.rect(ground, (120, 76, 34), (xx - 3, yy, 14, 12), border_radius=3); pygame.draw.rect(ground, (176, 124, 64), (xx - 2, yy + 1, 12, 4))
        block.append(pygame.Rect(xx, y0, 8, y1 - y0))
    for yy in (gy0, gy1):
        add(spr('lampD', w=22), fx0 + 2, yy + 6, 14); lamp_pts.append((fx0 + 2, yy - 92)); glows.append((fx0 + 2, yy - 92, 70, (255, 200, 110)))
    add(spr('stall', w=170), 2260, 1070, 150); block.append(pygame.Rect(2260 - 72, 1070 - 70, 144, 66))
    add(spr('crate', w=40), fx1 + 30, fy0 + 40, 30); add(spr('barrel_c', w=34), fx1 + 34, fy1 + 10, 26)
    occ += [pygame.Rect(fx0 - 80, fy0 - 80, fx1 - fx0 + 220, fy1 - fy0 + 160), pygame.Rect(2160, 960, 220, 160)]

    # --- pohon, semak, batu, bunga di rumput kosong
    taken = [(x, y) for (x, y) in NPC_POS.values()]

    def ok(x, y, dist):
        for r in occ:
            if r.collidepoint(x, y): return False
        for (tx, ty) in taken:
            if abs(tx - x) < dist and abs(ty - y) < dist * 0.7: return False
        return True
    cells = freec[:]; rng.shuffle(cells)
    TREES = ['oak2', 'oak3', 'oak1', 'apple2', 'pine2', 'pine3', 'pine1', 'cherry2', 'autumn2']
    nt = 0
    for (x, y) in cells:
        if nt >= 70: break
        x += rng.randrange(-6, 6); y += rng.randrange(-6, 6)
        if y < 140 or not ok(x, y, 120): continue
        k = rng.choice(TREES); im = spr(k); w, h = im.get_size()
        add(im, x, y, int(w * 0.8)); block.append(pygame.Rect(x - 9, y - 14, 18, 14)); taken.append((x, y)); nt += 1
    nb = 0
    for (x, y) in cells:
        if nb >= 70: break
        if not ok(x, y, 70): continue
        if rng.random() < 0.22:
            im = spr(rng.choice(['rock0', 'rock1', 'rock2'])); w, h = im.get_size(); add(im, x, y, int(w * 0.8))
            block.append(pygame.Rect(x - w // 2 + 6, y - h // 2, w - 12, h // 2))
        else:
            im = spr(rng.choice(['bush0', 'bush1', 'bush2', 'bush3', 'bush4'])); w, h = im.get_size(); add(im, x, y, int(w * 0.8)); block.append(pygame.Rect(x - 14, y - 12, 28, 12))
        taken.append((x, y)); nb += 1
    for (x, y) in cells:
        if rng.random() < 0.16 and ok(x, y, 1):
            im = spr(rng.choice(['fl0', 'fl1', 'fl2', 'fl4', 'fl5', 'fl6', 'fl7', 'fl8', 'fl9', 'fl10', 'fl11']), h=rng.randrange(20, 30))
            ground.blit(im, (x - im.get_width() // 2, y - im.get_height()))
    for (px, py, nm) in [(700, 702, 'bed0'), (900, 702, 'bed1'), (2000, 692, 'bed2'), (2220, 692, 'bed3'), (2400, 702, 'bed1'), (2610, 702, 'bed0'),
                         (560, 1482, 'bed4'), (770, 1482, 'bed0'), (1190, 706, 'bed2')]:
        im = spr(nm, w=60); add(im, px, py, 46); block.append(pygame.Rect(px - 22, py - 14, 44, 12))

    objs.sort(key=lambda o: o[0])
    T_ = Town()
    T_.ground, T_.objs, T_.block, T_.doors, T_.gate, T_.gate_out = ground, objs, block, doors, gate, gate_out
    T_.glows, T_.lamps, T_.smoke, T_.water, T_.soil = glows, lamp_pts, smoke, water_tiles, soil
    T_.mask, T_.mw, T_.mh, T_.size = mask, mw, mh, (MW, MH)
    T_.fauna = [(x, y, rng.random() * 6.28) for (x, y) in rng.sample(freec, min(10, len(freec)))]
    return T_


# ------------------------------------------------------------------ gambar dinamis desa
_CROP_IMG = {}


def crop_img(crop, stage):
    k = (crop, stage); s = _CROP_IMG.get(k)
    if s is None:
        base = spr(f'crop_{crop}_{stage}'); w, h = base.get_size()
        f = min(0.64, 46.0 / max(w, h)); s = _CROP_IMG[k] = spr(f'crop_{crop}_{stage}', w=max(8, int(w * f)), h=max(8, int(h * f)))
    return s


def visible_objs(town, cx, cy, W, H):
    out = []
    for (by, im, x, y) in town.objs:
        if x + im.get_width() < cx - 20 or x > cx + W + 20 or by < cy - 20 or y > cy + H + 20: continue
        out.append((by, im, x, y))
    return out


def draw_farm(screen, town, plots, cx, cy, ox, oy, W, H):
    """Petak ladang (tanah dicangkul/disiram) digambar tiap frame; tanaman dikembalikan sebagai objek berurut-Y."""
    c0 = max(0, int(cx // TS)); c1 = int((cx + W) // TS)
    r0 = max(0, int(cy // TS)); r1 = int((cy + H) // TS)
    ents = []
    for r in range(FARM['r0'], FARM['r0'] + FARM['rows']):
        if r < r0 or r > r1: continue
        for c in range(FARM['c0'], FARM['c0'] + FARM['cols']):
            if c < c0 or c > c1: continue
            p = plots.get(f'{c},{r}')
            if not p: continue
            screen.blit(town.soil[2 if p[3] else 1], (c * TS - cx + ox, r * TS - cy + oy))
            if p[1]:
                im = crop_img(p[1], stage_of(p[1], p[2]))
                ents.append(((r + 1) * TS - 4, im, c * TS + TS // 2 - im.get_width() // 2, (r + 1) * TS - 4 - im.get_height()))
    return ents


def draw_effects(screen, town, cx, cy, ox, oy, W, H, t, night):
    """Kilau air, asap cerobong, kupu-kupu/kunang-kunang, cahaya lampu & jendela saat malam."""
    for i, (x, y) in enumerate(town.water):
        sx, sy = x - cx + ox, y - cy + oy
        if sx < -TS or sx > W or sy < -TS or sy > H: continue
        ph = (t / 900.0 + i * 0.37) % 1.0
        if ph < 0.35:
            a = int(255 * math.sin(ph / 0.35 * math.pi))
            pygame.draw.rect(screen, (150 + a // 4, 214 + a // 8, 252), (sx + (i * 7) % 26, sy + (i * 13) % 30, 8, 2))
    for k, (x, y) in enumerate(town.smoke):
        for j in range(5):
            ph = ((t / 2600.0) + j / 5.0 + k * 0.3) % 1.0
            sx = x - cx + ox + math.sin(ph * 5 + j) * 8 + ph * 18; sy = y - cy + oy - ph * 70
            r = int(5 + ph * 11); g = int(236 - ph * 40)
            blob(screen, int(sx), int(sy), r, (g, g, g + 6), int(150 * (1 - ph)))
    if night < 0.15:
        for i, (fx, fy, ph0) in enumerate(town.fauna):
            x = fx + math.sin(t / 1900.0 + ph0) * 60 + math.sin(t / 700.0 + i) * 8; y = fy + math.cos(t / 2300.0 + ph0 * 2) * 40
            sx, sy = int(x - cx + ox), int(y - cy + oy)
            if -20 < sx < W + 20 and -20 < sy < H + 20:
                fl = int(3 * abs(math.sin(t / 110.0 + i * 1.7))); col = [(255, 236, 120), (255, 160, 200), (170, 210, 255)][i % 3]
                pygame.draw.rect(screen, col, (sx - 1 - fl, sy - 2, 2 + fl, 3)); pygame.draw.rect(screen, col, (sx + 1, sy - 2, 2 + fl, 3)); pygame.draw.rect(screen, (60, 40, 30), (sx, sy - 1, 1, 3))
    elif night > 0.25:
        for i, (fx, fy, ph0) in enumerate(town.fauna):
            x = fx + math.sin(t / 2100.0 + ph0) * 70; y = fy + math.cos(t / 1700.0 + ph0) * 50
            sx, sy = int(x - cx + ox), int(y - cy + oy)
            if -20 < sx < W + 20 and -20 < sy < H + 20:
                a = 0.5 + 0.5 * math.sin(t / 500.0 + i * 2.1)
                blob(screen, sx, sy, 7, (200, 255, 120), int(60 * a)); pygame.draw.rect(screen, (230, 255, 160), (sx, sy, 2, 2))
    if night > 0.03:
        for (x, y, r, col) in town.glows:
            sx, sy = x - cx + ox, y - cy + oy
            if sx < -r or sx > W + r or sy < -r or sy > H + r: continue
            g = glow_surf(r, col)
            screen.blit(g, (sx - r, sy - r), special_flags=pygame.BLEND_RGBA_ADD) if night > 0.3 else screen.blit(g, (sx - r, sy - r))


# ------------------------------------------------------------------ ladang (logika)
from data import CROPS
# plots[f"{c},{r}"] = [tilled(1), crop_id|None, umur(hari), disiram(0/1)]


def stage_of(crop, age):
    d = CROPS[crop]['days']
    return 3 if age >= d else min(2, (age * 3) // d)


def ripe(p): return bool(p and p[1] and p[2] >= CROPS[p[1]]['days'])


def plot_key_at(x, y):
    c, r = int(x // TS), int(y // TS)
    if FARM['c0'] <= c < FARM['c0'] + FARM['cols'] and FARM['r0'] <= r < FARM['r0'] + FARM['rows']: return f'{c},{r}'
    return None


def facing_plot(px, py, d, flip):
    """Petak di depan pemain (kaki di px,py)."""
    dx, dy = {'down': (0, 1), 'up': (0, -1), 'side': (-1 if flip else 1, 0)}[d]
    for dist in (30, 44, 14):
        k = plot_key_at(px + dx * dist, py - 6 + dy * dist)
        if k: return k
    return None


def new_day(plots, rain=None):
    """Hari baru: tanaman yang disiram bertambah umur; hujan menyiram semua petak yang ditanami."""
    if rain is None: rain = random.random() < 0.22
    for p in plots.values():
        if p[1] and (p[3] or rain): p[2] += 1
        p[3] = 0
    return rain


def plot_rect(key):
    c, r = [int(v) for v in key.split(',')]
    return pygame.Rect(c * TS, r * TS, TS, TS)


# ------------------------------------------------------------------ interior
class Room:
    def __init__(s, W, H, wh=96, floor='wood', seed=1):
        s.W, s.H, s.wh, s.rng = W, H, wh, random.Random(seed)
        s.surf = pygame.Surface((W, H)); s.solid = []; s.items = []; s.ground = []; s.wallitems = []
        s.floor = floor
        s._floor(); s._walls()

    def _floor(s):
        W, H, wh, rng = s.W, s.H, s.wh, s.rng
        if s.floor == 'stone':
            for y in range(wh, H, TS):
                for x in range(0, W, TS): s.surf.blit(tex_cobble(rng, rng.randrange(-4, 10)), (x, y))
            return
        base = {'wood': (216, 154, 80), 'dark': (160, 104, 58)}[s.floor]
        y = wh; row = 0
        while y < H:
            col = _shade(base, -10 if row % 2 else 4)
            pygame.draw.rect(s.surf, col, (0, y, W, 20))
            pygame.draw.line(s.surf, _shade(col, -32), (0, y + 19), (W, y + 19)); pygame.draw.line(s.surf, _shade(col, 16), (0, y), (W, y))
            x = rng.randrange(0, 120)
            while x < W:
                pygame.draw.line(s.surf, _shade(col, -30), (x, y), (x, y + 19)); x += rng.randrange(90, 180)
            for _ in range(5):
                gx = rng.randrange(W); pygame.draw.line(s.surf, _shade(col, 10), (gx, y + rng.randrange(3, 16)), (gx + rng.randrange(10, 36), y + rng.randrange(3, 16)))
            y += 20; row += 1

    def _walls(s):
        W, H, wh, rng = s.W, s.H, s.wh, s.rng
        stone = s.floor == 'stone'
        wc = (150, 148, 158) if stone else (206, 150, 82)
        pygame.draw.rect(s.surf, wc, (0, 0, W, wh))
        if stone:
            for yy in range(0, wh - 16, 16):
                xx = -(rng.randrange(0, 20))
                while xx < W:
                    w = rng.randrange(26, 44); c = _shade((156, 154, 164), rng.randrange(-12, 12))
                    pygame.draw.rect(s.surf, c, (xx + 1, yy + 1, w - 2, 14), border_radius=3); pygame.draw.line(s.surf, _shade(c, 22), (xx + 3, yy + 2), (xx + w - 4, yy + 2)); xx += w
        else:
            for yy in range(6, wh - 14, 12):
                pygame.draw.line(s.surf, _shade(wc, -22), (0, yy), (W, yy)); pygame.draw.line(s.surf, _shade(wc, 14), (0, yy + 1), (W, yy + 1))
            for _ in range(40):
                gx, gy = rng.randrange(W), rng.randrange(wh - 16); pygame.draw.line(s.surf, _shade(wc, 10), (gx, gy), (gx + rng.randrange(8, 24), gy))
        pygame.draw.rect(s.surf, (112, 70, 34), (0, 0, W, 12)); pygame.draw.line(s.surf, (170, 112, 58), (0, 2), (W, 2), 2)
        for x in range(0, W + 1, 150):
            pygame.draw.rect(s.surf, (116, 72, 34), (max(0, x - 7), 0, 14, wh - 14)); pygame.draw.line(s.surf, (170, 112, 58), (max(0, x - 7) + 2, 0), (max(0, x - 7) + 2, wh - 14), 2)
        for x in range(0, W, 30):   # dasar batu
            c = _shade((150, 148, 156), rng.randrange(-14, 14)); pygame.draw.rect(s.surf, c, (x, wh - 14, 29, 14), border_radius=2); pygame.draw.line(s.surf, _shade(c, 26), (x + 1, wh - 13), (x + 27, wh - 13))
        sh = pygame.Surface((W, 14), pygame.SRCALPHA)
        for i in range(14): pygame.draw.rect(sh, (30, 16, 4, int(80 * (1 - i / 14.0))), (0, i, W, 1))
        s.surf.blit(sh, (0, wh))
        # dinding samping & bawah
        for (x, w) in ((0, 18), (W - 18, 18)):
            pygame.draw.rect(s.surf, (112, 70, 34), (x, wh, w, H - wh)); pygame.draw.rect(s.surf, (170, 112, 58), (x + 3, wh, 4, H - wh))
        pygame.draw.rect(s.surf, (96, 58, 26), (0, H - 18, W, 18)); pygame.draw.line(s.surf, (150, 100, 50), (0, H - 17), (W, H - 17), 2)
        cx = W // 2
        pygame.draw.rect(s.surf, (176, 172, 160), (cx - 46, H - 18, 92, 18)); pygame.draw.rect(s.surf, (120, 40, 36), (cx - 38, H - 18, 76, 14), border_radius=2)
        pygame.draw.rect(s.surf, (214, 170, 70), (cx - 38, H - 18, 76, 14), 2, border_radius=2)

    def put(s, name, cx, by, w=None, h=None, fp=(0.9, 0.45), solid=True, ground=False, wall=False, flip=False):
        im = spr(name, w=w, h=h, flip=flip); iw, ih = im.get_size()
        (s.ground if ground else s.wallitems if wall else s.items).append((by, im, cx - iw // 2, by - ih))
        if solid and not ground and not wall:
            fw, fh = int(iw * fp[0]), int(ih * fp[1]); s.solid.append(pygame.Rect(cx - fw // 2, by - fh, fw, fh))
        return im

    def carpet(s, x, y, w, h, col=(176, 38, 34)):
        pygame.draw.rect(s.surf, _shade(col, -50), (x - 2, y - 2, w + 4, h + 4), border_radius=3)
        pygame.draw.rect(s.surf, col, (x, y, w, h), border_radius=3)
        pygame.draw.rect(s.surf, (222, 176, 66), (x + 5, y + 5, w - 10, h - 10), 2, border_radius=2)
        for yy in range(y + 12, y + h - 8, 14): pygame.draw.rect(s.surf, _shade(col, 18), (x + 10, yy, w - 20, 2))

    def finish(s, npc_pos, spawn_y=None, sleep=()):
        for (_, im, x, y) in s.ground: s.surf.blit(im, (x, y))
        for (_, im, x, y) in sorted(s.wallitems, key=lambda o: o[0]): s.surf.blit(im, (x, y))
        for (by, im, x, y) in sorted(s.items, key=lambda o: o[0]):
            shadow(s.surf, x + im.get_width() // 2, by - 2, int(im.get_width() * 0.8), 10, 60)
            s.surf.blit(im, (x, y))
        W, H, wh, cx = s.W, s.H, s.wh, s.W // 2
        vg = pygame.Surface((W, H), pygame.SRCALPHA)   # vinyet halus
        for i in range(26): pygame.draw.rect(vg, (20, 8, 0, int(4 + (26 - i) * 2.2)), (i, i, W - 2 * i, H - 2 * i), 1)
        s.surf.blit(vg, (0, 0))
        floor = [pygame.Rect(18, wh, W - 36, H - wh - 18), pygame.Rect(cx - 44, H - 40, 88, 40)]
        return dict(surf=s.surf, floor=floor, solid=s.solid, exit=pygame.Rect(cx - 38, H - 14, 76, 12), spawn=(cx, H - 62),
                    npc_pos=npc_pos, sleep=list(sleep))


def _inn():
    r = Room(640, 480, 96, 'wood', 11)
    r.put('window_a', 150, 84, h=62, wall=True); r.put('window_a', 490, 84, h=62, wall=True)
    r.put('banner_a', 70, 98, h=70, wall=True); r.put('banner_b', 570, 98, h=70, wall=True)
    r.put('fireplace', 320, 134, w=112, fp=(0.8, 0.3))
    r.put('rug_blue', 320, 400, w=230, solid=False, ground=True)
    beds = []
    for i, x in enumerate((70, 148)):
        r.put('bed_blue' if i % 2 == 0 else 'bed_green', x, 262, w=70, fp=(0.9, 0.9)); beds.append((x, 220))
    for i, x in enumerate((492, 570)):
        r.put('bed_green' if i % 2 == 0 else 'bed_blue', x, 262, w=70, fp=(0.9, 0.9)); beds.append((x, 220))
    for i, x in enumerate((70, 148)):
        r.put('bed_blue2', x, 410, w=70, fp=(0.9, 0.9)); beds.append((x, 368))
    for i, x in enumerate((492, 570)):
        r.put('bed_blue2', x, 410, w=70, fp=(0.9, 0.9)); beds.append((x, 368))
    r.put('table_big', 320, 340, w=130, fp=(0.8, 0.5)); r.put('chair_a', 240, 346, w=34, fp=(0.8, 0.5)); r.put('chair_a', 400, 346, w=34, fp=(0.8, 0.5), flip=True)
    r.put('desk', 250, 202, w=100, fp=(0.9, 0.55)); r.put('barrel_c', 396, 205, w=44, fp=(0.8, 0.5))
    r.put('potplant', 36 + 18, 130, w=38, fp=(0.6, 0.4)); r.put('lantern_a', 590, 200, w=30, fp=(0.6, 0.3))
    spots = beds + [(250, 440), (390, 440)]
    return r.finish((340, 190), sleep=spots)


def _church():
    r = Room(680, 500, 110, 'stone', 12)
    r.put('window_a', 130, 100, h=74, wall=True); r.put('window_a', 550, 100, h=74, wall=True); r.put('window_b', 340, 98, h=70, wall=True)
    r.put('banner_a', 60, 112, h=84, wall=True); r.put('banner_b', 620, 112, h=84, wall=True); r.put('banner_a', 235, 112, h=84, wall=True); r.put('banner_b', 445, 112, h=84, wall=True)
    r.carpet(310, 170, 60, 312)
    r.put('table_big', 340, 156, w=140, fp=(0.8, 0.45)); r.put('lantern_a', 250, 150, w=32, fp=(0.6, 0.3)); r.put('lantern_a', 430, 150, w=32, fp=(0.6, 0.3))
    for by in (270, 336, 402):
        r.put('bench_b', 190, by, w=130, fp=(0.95, 0.6)); r.put('bench_b', 490, by, w=130, fp=(0.95, 0.6))
    r.put('potplant', 56, 150, w=40, fp=(0.6, 0.4)); r.put('potplant', 624, 150, w=40, fp=(0.6, 0.4)); r.put('chest', 620, 460, w=60, fp=(0.9, 0.5)); r.put('barrel_c', 60, 468, w=40, fp=(0.8, 0.5))
    return r.finish((340, 214))


def _potion():
    r = Room(600, 440, 96, 'dark', 13)
    r.put('window_b', 300, 86, h=56, wall=True)
    r.put('shelf_big', 120, 150, w=128, fp=(0.95, 0.4)); r.put('cabinet', 490, 150, w=104, fp=(0.95, 0.4)); r.put('shelf_w', 300, 134, w=120, wall=True)
    r.carpet(150, 300, 300, 110, (96, 46, 150))
    r.put('desk', 252, 244, w=104, fp=(0.95, 0.55)); r.put('desk', 352, 244, w=104, fp=(0.95, 0.55))
    r.put('cauldron', 490, 288, w=74, fp=(0.8, 0.5)); r.put('potplant', 60, 330, w=44, fp=(0.6, 0.4)); r.put('barrel_a', 544, 384, w=46, fp=(0.8, 0.5)); r.put('crate', 52, 410, w=50, fp=(0.9, 0.35))
    r.put('lantern_a', 200, 220, w=30, fp=(0.6, 0.3))
    return r.finish((302, 204))


def _smith():
    r = Room(600, 440, 96, 'stone', 14)
    r.put('window_b', 330, 84, h=56, wall=True)
    r.put('fireplace', 130, 140, w=126, fp=(0.85, 0.3)); r.put('weapon_rack', 470, 128, w=100, fp=(0.9, 0.35))
    r.put('anvil_tbl', 340, 268, w=110, fp=(0.9, 0.6)); r.put('crate', 548, 220, w=50, fp=(0.9, 0.35)); r.put('barrel_a', 64, 296, w=54, fp=(0.8, 0.5)); r.put('barrel_b', 540, 380, w=38, fp=(0.8, 0.5))
    r.put('chest', 70, 410, w=74, fp=(0.9, 0.5)); r.put('lantern_a', 230, 190, w=28, fp=(0.6, 0.3)); r.put('lantern_a', 440, 330, w=28, fp=(0.6, 0.3))
    return r.finish((236, 228))


def _green():
    r = Room(560, 420, 96, 'wood', 15)
    r.put('window_a', 190, 84, h=62, wall=True); r.put('clock', 330, 100, h=60, solid=False, wall=True)
    r.put('stove', 470, 140, w=104, fp=(0.9, 0.4)); r.put('bed_green', 70, 250, w=76, fp=(0.9, 0.9)); r.put('shelf_a', 232, 134, w=110, fp=(0.95, 0.4))
    r.put('rug_green', 300, 395, w=120, solid=False, ground=True)
    r.put('table_fl', 330, 316, w=104, fp=(0.85, 0.5)); r.put('chair_a', 262, 326, w=32, fp=(0.8, 0.5)); r.put('chair_a', 400, 326, w=32, fp=(0.8, 0.5), flip=True)
    r.put('potplant', 50, 410, w=44, fp=(0.6, 0.4)); r.put('barrel_c', 515, 390, w=40, fp=(0.8, 0.5)); r.put('lantern_b', 140, 200, w=26, fp=(0.6, 0.3))
    return r.finish((330, 222))


def _guild():
    r = Room(600, 440, 96, 'wood', 16)
    r.put('window_a', 130, 84, h=62, wall=True); r.put('window_a', 470, 84, h=62, wall=True)
    r.put('board', 300, 134, w=124, fp=(0.9, 0.3)); r.put('banner_a', 50, 98, h=70, wall=True); r.put('banner_b', 550, 98, h=70, wall=True)
    r.put('shelf_a', 90, 160, w=108, fp=(0.95, 0.4)); r.put('cabinet', 520, 160, w=100, fp=(0.95, 0.4))
    r.carpet(200, 300, 200, 112)
    r.put('desk', 250, 258, w=104, fp=(0.95, 0.55)); r.put('desk', 352, 258, w=104, fp=(0.95, 0.55))
    r.put('bench_a', 110, 372, w=84, fp=(0.95, 0.5)); r.put('bench_a', 490, 372, w=84, fp=(0.95, 0.5)); r.put('barrel_c', 560, 300, w=42, fp=(0.8, 0.5)); r.put('crate', 44, 300, w=44, fp=(0.9, 0.35))
    r.put('lantern_a', 130, 230, w=28, fp=(0.6, 0.3)); r.put('lantern_a', 470, 230, w=28, fp=(0.6, 0.3))
    return r.finish((302, 212))


_BUILD = {'inn': _inn, 'church': _church, 'potion': _potion, 'smith': _smith, 'green': _green, 'windmill': _guild}


def build_interior(iid): return _BUILD[iid]()
