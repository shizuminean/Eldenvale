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
    """Lapisan di atas sprite ladang. 0 = (tidak dipakai), 1 = dicangkul (tanah gembur gelap), 2 = disiram (lebih gelap, basah)."""
    s = pygame.Surface((TS, TS), pygame.SRCALPHA)
    if kind == 0: return s
    base = [(0, 0, 0), (86, 54, 30), (38, 28, 24)][kind]; al = [0, 176, 214][kind]
    pygame.draw.rect(s, base + (al,), (1, 1, TS - 2, TS - 2), border_radius=4)
    for yy in (7, 18, 29):
        pygame.draw.line(s, _shade(base, -22) + (min(255, al + 30),), (3, yy), (TS - 4, yy), 3)
        pygame.draw.line(s, _shade(base, 26) + (150 if kind == 1 else 90,), (3, yy - 2), (TS - 4, yy - 2), 1)
    if kind == 2:
        for _ in range(4): s.set_at((rng.randrange(4, TS - 4), rng.randrange(4, TS - 4)), (120, 170, 220, 200))
    pygame.draw.rect(s, _shade(base, -30) + (200,), (1, 1, TS - 2, TS - 2), 1, border_radius=4)
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


# ------------------------------------------------------------------ bayangan dari siluet sprite
def cast_shadow(dst, im, cx, by, squash=0.2, shear=0.7, a=64):
    """Bayangan = siluet sprite itu sendiri: dibalik ke tanah, dipipihkan, sedikit dimiringkan ke kanan.
    Bentuknya selalu mengikuti aset (rumah, pohon, tiang lampu...), bukan elips generik. Di-cache per sprite."""
    k = ('cs', id(im), squash, shear, a)
    sh = _BL.get(k)
    if sh is None:
        iw, ih = im.get_size()
        hh = max(3, int(ih * squash))
        sil = im.copy()
        sil.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)      # RGB -> 0, alpha tetap
        sil.fill((12, 26, 10, 0), special_flags=pygame.BLEND_RGBA_ADD)      # warna bayangan (hijau tua)
        sil.fill((255, 255, 255, a), special_flags=pygame.BLEND_RGBA_MULT)  # kekuatan bayangan
        sq = pygame.transform.smoothscale(pygame.transform.flip(sil, False, True), (iw, hh))
        ow = iw + int(shear * hh) + 2
        sh = pygame.Surface((ow, hh), pygame.SRCALPHA)
        for row in range(hh): sh.blit(sq, (int(shear * row), row), (0, row, iw, 1))
        _BL[k] = sh
    dst.blit(sh, (cx - im.get_width() // 2, by - 2))


SH_HOUSE, SH_TREE, SH_POLE, SH_LOW = (0.16, 0.9, 78), (0.2, 0.85, 62), (0.12, 1.0, 62), (0.34, 0.5, 58)


def free_spot(blocked_fn, x, y, maxr=640, step=12):
    """Titik bebas terdekat dari (x, y): spiral keluar sampai blocked_fn(px, py) False."""
    if not blocked_fn(x, y): return x, y
    for r in range(step, maxr, step):
        n = max(8, int(2 * math.pi * r / step))
        for i in range(n):
            ang = 6.2832 * i / n
            px, py = x + math.cos(ang) * r, y + math.sin(ang) * r
            if not blocked_fn(px, py): return px, py
    return x, y


# ------------------------------------------------------------------ dunia desa
# Latar = gambar desa buatan (assets/town_bg.png, 1672x941) diskalakan KS kali. Tebing & air menjadi tabrakan lewat
# assets/town_mask.png (sel 8 piksel gambar asli: R = terblokir, G = air).
KS = 2.0
MW, MH = int(1672 * KS), int(941 * KS)
CELL = int(8 * KS)


class Town:
    def hit(self, r):
        """True jika kotak r menyentuh sel tebing/air/tepi peta."""
        if r.left < 24 or r.top < 24 or r.right > MW - 24 or r.bottom > MH - 8: return True
        m, cw = self.mask, self.mw
        g = self.grid
        for gy in range(r.top >> 6, (r.bottom >> 6) + 1):
            for gx in range(r.left >> 6, (r.right >> 6) + 1):
                for b in g.get((gx, gy), ()):
                    if r.colliderect(b): return True
        for cy in range(max(0, r.top // CELL), min(self.mh, r.bottom // CELL + 1)):
            row = m[cy]
            for cx in range(max(0, r.left // CELL), min(cw, r.right // CELL + 1)):
                if row[cx]: return True
        return False


class Terrain:
    """Jenis tanah per sel (16 px dunia): rumput kosong / jalan tanah, batu & tangga / tebing & air.
    Dipakai supaya rumah, pohon, dan taman HANYA diletakkan di rumput yang benar-benar kosong
    (tidak menimpa jalan tanah, tangga, tebing, air, atau plaza)."""
    def __init__(self, bg, mask, mw, mh):
        self.mw, self.mh = mw, mh
        ng = [[0] * (mw + 1) for _ in range(mh + 1)]      # integral: sel bukan-rumput
        bl = [[0] * (mw + 1) for _ in range(mh + 1)]      # integral: sel terblokir
        for y in range(mh):
            rs = rb = 0
            mrow, ng0, ng1, bl0, bl1 = mask[y], ng[y], ng[y + 1], bl[y], bl[y + 1]
            for x in range(mw):
                if mrow[x]: g_ = False; blk = True
                else:
                    r, g, b = bg.get_at((x * 8 + 4, y * 8 + 4))[:3]
                    g_ = g > r + 15 and g > b + 50; blk = False
                rs += (not g_); rb += blk
                ng1[x + 1] = ng0[x + 1] + rs; bl1[x + 1] = bl0[x + 1] + rb
        self.ng, self.bl = ng, bl

    def _sum(self, I, r):
        c0, r0 = r.left // CELL, r.top // CELL
        c1, r1 = (r.right - 1) // CELL, (r.bottom - 1) // CELL
        if c0 < 0 or r0 < 0 or c1 >= self.mw or r1 >= self.mh: return 1 << 20
        return I[r1 + 1][c1 + 1] - I[r0][c1 + 1] - I[r1 + 1][c0] + I[r0][c0]

    def grass(self, rect, m=0):
        """Seluruh sel di rect (diperlebar m sel) adalah rumput."""
        return self._sum(self.ng, rect.inflate(m * CELL * 2, m * CELL * 2)) == 0

    def walk(self, rect):
        """Tidak ada sel tebing/air di rect."""
        return self._sum(self.bl, rect) == 0


# (id, sprite, pusat-x, dasar-y, lebar, tetap)  -- 'tetap' = persis di titik itu; selain itu dicarikan titik rumput kosong terdekat
BUILDINGS = [
    ('church', 'b_church', 1676, 536, 400, True), ('windmill', 'b_windmill', 1020, 690, 240, False), ('inn', 'b_inn', 800, 690, 300, False),
    ('potion', 'b_potion', 2100, 690, 280, False), ('green', 'b_green', 2500, 690, 300, False), ('smith', 'b_red', 660, 1470, 280, False),
]
# rumah hiasan (tanpa interior): (sprite, pusat-x, dasar-y, lebar)
DECOR_HOUSES = [('b_japan', 800, 180, 170), ('b_barn', 844, 1058, 180)]
FLAGS = [(1446, 552, 'flag_a'), (1906, 552, 'flag_b'), (1150, 746, 'flag_c'), (1150, 940, 'flag_c'), (2190, 746, 'flag_d'), (2190, 940, 'flag_d'),
         (2962, 746, 'flag_b'), (3236, 746, 'flag_a')]
FARM = dict(c0=49, r0=29, cols=11, rows=5)
FARM_RECT = pygame.Rect(FARM['c0'] * TS, FARM['r0'] * TS, FARM['cols'] * TS, FARM['rows'] * TS)

NPC_POS = {
    'Sir Aldric': (1700, 610), 'Mira': (1300, 800), 'Cale si Pedagang': (2060, 806), 'Anya': (820, 800),
    'Fenn si Pemanah': (2400, 800), 'Kesatria Ines': (1480, 640), 'Madam Ruby': (1880, 640), 'Penyihir Selene': (1330, 940),
    'Kakek Odo': (1420, 1030), 'Penjaga Gerbang': (1640, 1790), 'Putri Elara': (2000, 930), 'Petani Tomo': (2270, 1108),
}
SPAWN = (1700, 960)
LAMPS_A = [(500, 742), (1020, 742), (2300, 742), (2900, 742), (360, 934), (1000, 934), (2420, 934), (2900, 934)]


def build_town():
    rng = random.Random(1507)
    bg0 = pygame.image.load(os.path.join(_BASE, 'assets', 'town_bg.png')).convert()
    ground = pygame.transform.smoothscale(bg0, (MW, MH))
    mk = pygame.image.load(os.path.join(_BASE, 'assets', 'town_mask.png'))
    mw, mh = mk.get_size()
    px_ = [[mk.get_at((x, y)) for x in range(mw)] for y in range(mh)]
    mask = [[c[0] > 128 for c in row] for row in px_]
    water_tiles = [(x * CELL, y * CELL) for y in range(mh) for x in range(mw) if px_[y][x][1] > 128 and x % 2 == 0 and y % 2 == 0]
    terr = Terrain(bg0, mask, mw, mh)
    tex = random.Random(77)
    soil = [tex_soil(tex, 0), tex_soil(tex, 1), tex_soil(tex, 2)]

    # --- ladang: petak tanah kosong + pagar
    fld = spr('field_big', w=FARM_RECT.w + 30, h=FARM_RECT.h + 33)   # sprite ladang dari aset gambar
    ground.blit(fld, (FARM_RECT.x - 15, FARM_RECT.y - 18))

    objs, block, glows, lamp_pts = [], [], [], []
    occ = []                                  # kotak terlarang untuk dekorasi acak
    vis_occ = []                              # kotak tampilan bangunan: tidak boleh tumpang tindih

    def add(im, cx, by, sh=None):
        """sh = (squash, shear, alpha) bayangan siluet; None = tanpa bayangan."""
        w, h = im.get_size()
        if sh: cast_shadow(ground, im, cx, by, *sh)
        objs.append((by, im, cx - w // 2, by - h))

    def fit(cx, by, iw, ih, rad=(380, 130), step=16):
        """Titik terdekat dari (cx, by) di mana badan bangunan seluruhnya di rumput kosong, depan pintu bisa dilewati,
        dan tidak menimpa bangunan lain."""
        fw, fd = int(iw * 0.86), max(40, int(ih * 0.30))
        best = None
        for dy in range(-rad[1], rad[1] + 1, step):
            for dx in range(-rad[0], rad[0] + 1, step):
                x, y = cx + dx, by + dy
                if not terr.grass(pygame.Rect(x - fw // 2, y - fd, fw, fd), 1): continue
                if not terr.walk(pygame.Rect(x - 52, y, 104, 46)): continue
                vr = pygame.Rect(x - iw // 2 - 24, y - ih, iw + 48, ih + 16)
                if any(vr.colliderect(o) for o in vis_occ): continue
                c = dx * dx + 1.6 * dy * dy
                if best is None or c < best[0]: best = (c, x, y)
        return (best[1], best[2]) if best else (cx, by)

    def spot_free(rect):
        return terr.walk(rect) and not any(rect.colliderect(o) for o in vis_occ)

    doors, smoke = {}, []
    for bid, sp, pcx, pby, w, fixed in BUILDINGS:
        im = spr(sp, w=w); iw, ih = im.get_size()
        cx, by = (pcx, pby) if fixed else fit(pcx, pby, iw, ih)
        vis_occ.append(pygame.Rect(cx - iw // 2 - 24, by - ih, iw + 48, ih + 16))
        add(im, cx, by, SH_HOUSE)
        block.append(pygame.Rect(cx - int(iw * 0.43), by - int(ih * 0.34), int(iw * 0.86), int(ih * 0.34) - 4))
        doors[bid] = dict(trig=(cx - 22, by - 6, 44, 18), out=(cx, by + 42))
        occ.append(pygame.Rect(cx - iw // 2 - 50, by - ih, iw + 100, ih + 120))
        glows += [(cx - int(iw * 0.2), by - int(ih * 0.30), 46, (255, 190, 90)), (cx + int(iw * 0.2), by - int(ih * 0.30), 46, (255, 190, 90))]
        if bid == 'inn': smoke.append((cx - iw // 2 + int(0.31 * iw), by - ih + 12))
    for sp, pcx, pby, w in DECOR_HOUSES:
        im = spr(sp, w=w); iw, ih = im.get_size()
        cx, by = fit(pcx, pby, iw, ih, (260, 100))
        vis_occ.append(pygame.Rect(cx - iw // 2 - 24, by - ih, iw + 48, ih + 16))
        add(im, cx, by, SH_HOUSE)
        block.append(pygame.Rect(cx - int(iw * 0.43), by - int(ih * 0.34), int(iw * 0.86), int(ih * 0.34) - 4))
        occ.append(pygame.Rect(cx - iw // 2 - 50, by - ih, iw + 100, ih + 120))
        glows += [(cx - int(iw * 0.2), by - int(ih * 0.35), 40, (255, 190, 90)), (cx + int(iw * 0.2), by - int(ih * 0.35), 40, (255, 190, 90))]

    # plaza: lampu di keempat pedestal sudut, bangku, papan misi
    for (px, py) in [(1222, 722), (2120, 722), (1222, 1044), (2120, 1044)]:
        im = spr('lamp_b', h=132); add(im, px, py, SH_POLE); lamp_pts.append((px, py - 112)); glows.append((px, py - 112, 120, (255, 200, 110)))
        block.append(pygame.Rect(px - 8, py - 10, 16, 10)); occ.append(pygame.Rect(px - 40, py - 110, 80, 130))
    for (px, py) in [(1480, 1030), (1900, 1030)]:
        im = spr('bench_b', w=92); add(im, px, py, SH_LOW); block.append(pygame.Rect(px - 40, py - 20, 80, 18)); occ.append(pygame.Rect(px - 60, py - 60, 120, 100))
    add(spr('board', w=96), 1500, 702, SH_LOW); block.append(pygame.Rect(1500 - 36, 702 - 28, 72, 24)); occ.append(pygame.Rect(1440, 600, 120, 130))
    # sumur: dicarikan titik rumput kosong dekat tepi jalan
    wim = spr('well', w=120); wx, wy = fit(1070, 1110, 120, wim.get_height(), (240, 90))
    add(wim, wx, wy, SH_HOUSE); block.append(pygame.Rect(wx - 38, wy - 40, 76, 36)); occ.append(pygame.Rect(wx - 70, wy - 130, 140, 160))
    vis_occ.append(pygame.Rect(wx - 70, wy - wim.get_height(), 140, wim.get_height() + 16))

    # lampu jalan di tepi jalan utama (dilewati bila menabrak bangunan / tebing)
    for (px, py) in LAMPS_A:
        r_ = pygame.Rect(px - 36, py - 112, 72, 124)
        if not terr.walk(pygame.Rect(px - 10, py - 12, 20, 14)) or any(r_.colliderect(o) for o in vis_occ): continue
        im = spr('lamp_a', h=112); add(im, px, py, SH_POLE); lamp_pts.append((px, py - 96)); glows.append((px, py - 96, 90, (255, 200, 110)))
        block.append(pygame.Rect(px - 6, py - 8, 12, 8)); occ.append(pygame.Rect(px - 30, py - 110, 60, 130))

    # bendera tiang (hiasan berbayang, pangkal tiang menghalangi sedikit); dilewati bila menabrak bangunan
    for (px, py, nm) in FLAGS:
        r_ = pygame.Rect(px - 40, py - 150, 80, 170)
        if any(r_.colliderect(o) for o in vis_occ): continue
        im = spr(nm, h=148); add(im, px, py, SH_POLE); block.append(pygame.Rect(px - 6, py - 8, 12, 8)); occ.append(r_)

    # gerbang selatan (ujung jalan)
    gi = spr('gate_arch', w=270); add(gi, 1676, MH - 6, None)
    block += [pygame.Rect(1676 - 135 + 4, MH - 6 - 70, 52, 66), pygame.Rect(1676 + 135 - 56, MH - 6 - 70, 52, 66)]
    lamp_pts += [(1676 - 112, MH - 106), (1676 + 112, MH - 106)]; glows += [(1676 - 112, MH - 106, 100, (255, 200, 110)), (1676 + 112, MH - 106, 100, (255, 200, 110))]
    occ.append(pygame.Rect(1500, MH - 260, 360, 260))
    gate = pygame.Rect(1616, MH - 38, 120, 30); gate_out = (1676, MH - 110)

    # ladang: pagar kayu (celah di sisi barat untuk jalan), kios benih
    fx0, fy0, fx1, fy1 = FARM_RECT.x - 36, FARM_RECT.y - 36, FARM_RECT.right + 36, FARM_RECT.bottom + 36
    for xx in range(fx0, fx1, 80):
        w_ = min(80, fx1 - xx); add(spr('fenceA', w=w_), xx + w_ // 2, fy0 + 20); add(spr('fenceA', w=w_), xx + w_ // 2, fy1 + 20)
    block += [pygame.Rect(fx0, fy0 + 4, fx1 - fx0, 12), pygame.Rect(fx0, fy1 + 4, fx1 - fx0, 12)]
    gy0, gy1 = fy0 + 120, fy0 + 190            # celah gerbang di sisi barat
    for (xx, y0, y1) in [(fx0 - 4, fy0 + 10, gy0), (fx0 - 4, gy1, fy1 + 14), (fx1 - 4, fy0 + 10, fy1 + 14)]:
        pygame.draw.rect(ground, (96, 58, 26), (xx, y0, 8, y1 - y0)); pygame.draw.rect(ground, (150, 100, 50), (xx + 1, y0, 3, y1 - y0))
        for yy in range(y0, y1, TS): pygame.draw.rect(ground, (120, 76, 34), (xx - 3, yy, 14, 12), border_radius=3); pygame.draw.rect(ground, (176, 124, 64), (xx - 2, yy + 1, 12, 4))
        block.append(pygame.Rect(xx, y0, 8, y1 - y0))
    for yy in (gy0, gy1):
        add(spr('lamp_a', h=100), fx0 + 2, yy + 6, SH_POLE); lamp_pts.append((fx0 + 2, yy - 82)); glows.append((fx0 + 2, yy - 82, 70, (255, 200, 110)))
    add(spr('stall', w=170), 2260, 1070, SH_HOUSE); block.append(pygame.Rect(2260 - 72, 1070 - 70, 144, 66))
    add(spr('crate', w=40), fx1 + 30, fy0 + 40, SH_LOW); add(spr('barrel_c', w=34), fx1 + 34, fy1 + 10, SH_LOW)
    occ += [pygame.Rect(fx0 - 80, fy0 - 80, fx1 - fx0 + 220, fy1 - fy0 + 160), pygame.Rect(2160, 960, 220, 160)]

    # --- pohon, semak, batu, bunga: hanya di rumput kosong (jauh dari jalan, tangga, tebing, air), jarang & berkelompok
    def cell_list(margin):
        out = []
        for cy in range(2, mh - 2):
            for cx in range(2, mw - 2):
                if terr.grass(pygame.Rect(cx * CELL, cy * CELL, CELL, CELL), margin): out.append((cx * CELL + CELL // 2, cy * CELL + CELL // 2))
        return out
    c_tree, c_low = cell_list(3), cell_list(1)
    taken = [(x, y) for (x, y) in NPC_POS.values()]

    def ok(x, y, dist):
        for r in occ:
            if r.collidepoint(x, y): return False
        for (tx, ty) in taken:
            if abs(tx - x) < dist and abs(ty - y) < dist * 0.7: return False
        return True
    rng.shuffle(c_tree); rng.shuffle(c_low)
    TREES = ['oak2', 'oak3', 'oak1', 'apple2', 'pine2', 'pine3', 'pine1', 'cherry2', 'autumn2']
    nt = 0
    for (x, y) in c_tree:
        if nt >= 34: break
        if y < 150 or not ok(x, y, 170): continue
        k = rng.choice(TREES); im = spr(k); w, h = im.get_size()
        add(im, x, y, SH_TREE); block.append(pygame.Rect(x - 9, y - 14, 18, 14)); taken.append((x, y)); nt += 1
    nb = 0
    for (x, y) in c_low:
        if nb >= 40: break
        if not ok(x, y, 95): continue
        if rng.random() < 0.2:
            im = spr(rng.choice(['rock0', 'rock1', 'rock2'])); w, h = im.get_size(); add(im, x, y, SH_LOW)
            block.append(pygame.Rect(x - w // 2 + 6, y - h // 2, w - 12, h // 2))
        else:
            im = spr(rng.choice(['bush0', 'bush1', 'bush2', 'bush3', 'bush4'])); w, h = im.get_size(); add(im, x, y, SH_LOW); block.append(pygame.Rect(x - 14, y - 12, 28, 12))
        taken.append((x, y)); nb += 1
    FL = ['fl0', 'fl1', 'fl2', 'fl4', 'fl5', 'fl6', 'fl7', 'fl8', 'fl9', 'fl10', 'fl11']
    nc = 0
    for (x, y) in c_low:    # bunga berkelompok (3-6 tangkai sejenis), bukan taburan acak
        if nc >= 30: break
        if not ok(x, y, 1) or rng.random() > 0.05: continue
        kinds = rng.sample(FL, 2)
        for _ in range(rng.randrange(3, 7)):
            fx, fy = x + rng.randrange(-34, 35), y + rng.randrange(-18, 19)
            if not terr.grass(pygame.Rect(fx - 4, fy - 4, 8, 8), 0) or not ok(fx, fy, 1): continue
            im = spr(rng.choice(kinds), h=rng.randrange(20, 28)); ground.blit(im, (fx - im.get_width() // 2, fy - im.get_height()))
        nc += 1
    gr = [('grass_a', (20, 28)), ('grass_b', (30, 40)), ('grass_c', (38, 50))]
    for (x, y) in c_low:   # rumput liar 3 jenis (hiasan datar), jarang
        if rng.random() < 0.16 and ok(x, y, 1):
            nm, (h0, h1) = gr[rng.randrange(3)]
            im = spr(nm, h=rng.randrange(h0, h1)); ground.blit(im, (x + rng.randrange(-5, 5) - im.get_width() // 2, y - im.get_height()))

    objs.sort(key=lambda o: o[0])
    T_ = Town()
    T_.ground, T_.objs, T_.block, T_.doors, T_.gate, T_.gate_out = ground, objs, block, doors, gate, gate_out
    T_.glows, T_.lamps, T_.smoke, T_.water, T_.soil = glows, lamp_pts, smoke, water_tiles, soil
    T_.mask, T_.mw, T_.mh, T_.size = mask, mw, mh, (MW, MH)
    T_.grid = {}
    for b in block:
        for gy in range(b.top >> 6, (b.bottom >> 6) + 1):
            for gx in range(b.left >> 6, (b.right >> 6) + 1): T_.grid.setdefault((gx, gy), []).append(b)
    T_.wb = {}
    for i, (x, y) in enumerate(water_tiles):
        if i % 3 == 0: T_.wb.setdefault((x >> 8, y >> 8), []).append((x, y, i))
    T_.fauna = [(x, y, rng.random() * 6.28) for (x, y) in rng.sample(c_tree, min(10, len(c_tree)))]
    # NPC tidak boleh berdiri di dalam bangunan / pohon / tebing: geser ke titik bebas terdekat
    for nm_, (x, y) in list(NPC_POS.items()):
        NPC_POS[nm_] = free_spot(lambda qx, qy: T_.hit(pygame.Rect(int(qx) - 12, int(qy) - 12, 24, 14)), x, y, 500, 12)
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
    """Kilau air, asap cerobong, kupu-kupu/kunang-kunang, cahaya lampu & jendela saat malam (hanya bila efek visual aktif)."""
    for bx in range(max(0, int(cx) >> 8), (int(cx + W) >> 8) + 1):
        for by_ in range(max(0, int(cy) >> 8), (int(cy + H) >> 8) + 1):
            for (x, y, i) in town.wb.get((bx, by_), ()):
                ph = (t / 900.0 + i * 0.37) % 1.0
                if ph < 0.35:
                    a = int(255 * math.sin(ph / 0.35 * math.pi))
                    pygame.draw.rect(screen, (150 + a // 4, 214 + a // 8, 252), (x - cx + ox + (i * 7) % 26, y - cy + oy + (i * 13) % 30, 8, 2))
    for k, (x, y) in enumerate(town.smoke):
        sx0, sy0 = x - cx + ox, y - cy + oy
        if sx0 < -60 or sx0 > W + 60 or sy0 < -120 or sy0 > H + 60: continue
        for j in range(4):
            ph = ((t / 2600.0) + j / 4.0 + k * 0.3) % 1.0
            q = int(ph * 8)                                   # 8 tahap -> hanya 8 surface di-cache
            blob(screen, int(sx0 + math.sin(ph * 5 + j) * 8 + ph * 18), int(sy0 - ph * 70), 5 + q * 2, (236 - q * 5, 236 - q * 5, 242 - q * 5), 150 - q * 18)
    if night < 0.15:
        for i, (fx, fy, ph0) in enumerate(town.fauna[:6]):
            x = fx + math.sin(t / 1900.0 + ph0) * 60 + math.sin(t / 700.0 + i) * 8; y = fy + math.cos(t / 2300.0 + ph0 * 2) * 40
            sx, sy = int(x - cx + ox), int(y - cy + oy)
            if -20 < sx < W + 20 and -20 < sy < H + 20:
                fl = int(3 * abs(math.sin(t / 110.0 + i * 1.7))); col = [(255, 236, 120), (255, 160, 200), (170, 210, 255)][i % 3]
                pygame.draw.rect(screen, col, (sx - 1 - fl, sy - 2, 2 + fl, 3)); pygame.draw.rect(screen, col, (sx + 1, sy - 2, 2 + fl, 3)); pygame.draw.rect(screen, (60, 40, 30), (sx, sy - 1, 1, 3))
    elif night > 0.25:
        for i, (fx, fy, ph0) in enumerate(town.fauna[:6]):
            x = fx + math.sin(t / 2100.0 + ph0) * 70; y = fy + math.cos(t / 1700.0 + ph0) * 50
            sx, sy = int(x - cx + ox), int(y - cy + oy)
            if -20 < sx < W + 20 and -20 < sy < H + 20:
                a_ = int(2.99 * (0.5 + 0.5 * math.sin(t / 500.0 + i * 2.1)))   # 3 tingkat kilau
                blob(screen, sx, sy, 7, (200, 255, 120), 30 + a_ * 22); pygame.draw.rect(screen, (230, 255, 160), (sx, sy, 2, 2))


# ------------------------------------------------------------------ nuansa pagi / sore / malam
# (menit, (r, g, b, alpha)): warna selimut cahaya sepanjang hari. Alpha 0 = terang penuh.
AMB = [(0, (14, 22, 72, 150)), (300, (20, 30, 84, 142)), (360, (255, 150, 120, 54)), (420, (255, 196, 150, 18)), (480, (255, 210, 160, 0)),
       (990, (255, 210, 130, 0)), (1050, (255, 178, 84, 40)), (1110, (255, 118, 66, 70)), (1170, (110, 60, 120, 100)), (1230, (30, 34, 92, 136)),
       (1290, (14, 22, 72, 150)), (1440, (14, 22, 72, 150))]


def ambient(tm):
    for (m0, c0), (m1, c1) in zip(AMB, AMB[1:]):
        if m0 <= tm < m1:
            f = (tm - m0) / float(m1 - m0)
            return tuple(int(c0[i] + (c1[i] - c0[i]) * f) for i in range(4))
    return AMB[-1][1]


_LM, _LD = {}, {}


def light_disk(r, col, lvl):
    """Cakram cahaya radial (hitam di tepi -> warna di tengah), di-cache. Dipakai ADD pada lightmap."""
    k = (r, col, lvl); s = _LD.get(k)
    if s is None:
        s = _LD[k] = pygame.Surface((r * 2, r * 2))
        for i in range(r, 0, -2):
            f = (1.0 - i / float(r)) ** 1.6 * lvl / 8.0
            pygame.draw.circle(s, (int(col[0] * f), int(col[1] * f), int(col[2] * f)), (r, r), i)
    return s


def draw_lighting(screen, town, cx, cy, ox, oy, W, H, amb, px, py, t, lights=True):
    """Nuansa pagi / sore / malam. Siang: tidak ada kerja sama sekali. Senja tanpa lampu: satu fill MULT (sangat murah).
    Gelap: lightmap setengah resolusi (selimut gelap + cakram cahaya lampu/jendela/pemain, ADD), diperbesar lalu di-MULT
    ke layar. Tidak ada lagi overlay alpha layar penuh + puluhan blit RGBA_SUB / RGB_ADD besar tiap frame (penyebab lag)."""
    a = amb[3]
    if a <= 2: return
    k = a / 255.0
    mc = (int(255 - (255 - amb[0]) * k), int(255 - (255 - amb[1]) * k), int(255 - (255 - amb[2]) * k))
    if not lights or a < 44:
        screen.fill(mc, special_flags=pygame.BLEND_RGB_MULT); return
    hw, hh = (W + 1) // 2, (H + 1) // 2
    lm = _LM.get((W, H))
    if lm is None: lm = _LM[(W, H)] = (pygame.Surface((hw, hh)), pygame.Surface((W, H)))
    small, full = lm
    small.fill(mc)
    lvl = max(1, min(8, int((a - 30) / 14)))
    for (x, y, r, col) in town.glows:
        sx, sy = int(x - cx + ox), int(y - cy + oy); rr = int(r * 1.3)
        if sx < -rr or sx > W + rr or sy < -rr or sy > H + rr: continue
        d = light_disk(max(6, rr // 2), col, lvl)
        small.blit(d, (sx // 2 - d.get_width() // 2, sy // 2 - d.get_height() // 2), special_flags=pygame.BLEND_RGB_ADD)
    if px or py:
        d = light_disk(75, (255, 226, 176), lvl)   # cahaya di sekitar pemain
        small.blit(d, (int(px) // 2 - 75, int(py) // 2 - 75), special_flags=pygame.BLEND_RGB_ADD)
    pygame.transform.scale(small, (W, H), full)
    screen.blit(full, (0, 0), special_flags=pygame.BLEND_RGB_MULT)


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
        s.surf = pygame.Surface((W, H)); s.solid = []; s.items = []; s.ground = []; s.wallitems = []; s.links = []; s.beds = []
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

    def put(s, name, cx, by, w=None, h=None, fp=(0.94, 0.55), solid=True, ground=False, wall=False, flip=False, bed=False):
        im = spr(name, w=w, h=h, flip=flip); iw, ih = im.get_size()
        if not wall and not ground:
            cx = max(18 + iw // 2, min(s.W - 18 - iw // 2, cx)); by = min(by, s.H - 24)   # tetap di dalam lantai
        (s.ground if ground else s.wallitems if wall else s.items).append((by, im, cx - iw // 2, by - ih))
        if bed: s.beds.append(pygame.Rect(cx - iw // 2, by - ih, iw, ih))
        if solid and not ground and not wall:
            fw, fh = int(iw * fp[0]), int(ih * fp[1]); s.solid.append(pygame.Rect(cx - fw // 2, by - fh, fw, fh))
        return im

    def carpet(s, x, y, w, h, col=(176, 38, 34)):
        pygame.draw.rect(s.surf, _shade(col, -50), (x - 2, y - 2, w + 4, h + 4), border_radius=3)
        pygame.draw.rect(s.surf, col, (x, y, w, h), border_radius=3)
        pygame.draw.rect(s.surf, (222, 176, 66), (x + 5, y + 5, w - 10, h - 10), 2, border_radius=2)
        for yy in range(y + 12, y + h - 8, 14): pygame.draw.rect(s.surf, _shade(col, 18), (x + 10, yy, w - 20, 2))

    def finish(s, npc_pos, spawn_y=None, sleep=(), label=None, exit_door=True, spawn=None):
        for (_, im, x, y) in s.ground: s.surf.blit(im, (x, y))
        for (_, im, x, y) in sorted(s.wallitems, key=lambda o: o[0]): s.surf.blit(im, (x, y))
        for (by, im, x, y) in s.items: cast_shadow(s.surf, im, x + im.get_width() // 2, by, 0.16, 0.8, 70)
        W, H, wh, cx = s.W, s.H, s.wh, s.W // 2
        vg = pygame.Surface((W, H), pygame.SRCALPHA)   # vinyet halus
        for i in range(26): pygame.draw.rect(vg, (20, 8, 0, int(4 + (26 - i) * 2.2)), (i, i, W - 2 * i, H - 2 * i), 1)
        s.surf.blit(vg, (0, 0))
        floor = [pygame.Rect(18, wh, W - 36, H - wh - 18), pygame.Rect(cx - 44, H - 40, 88, 40)]
        return dict(surf=s.surf, objs=sorted(s.items, key=lambda o: o[0]), floor=floor, solid=s.solid,
                    exit=pygame.Rect(cx - 38, H - 14, 76, 12) if exit_door else pygame.Rect(-500, -500, 1, 1),
                    spawn=spawn or (cx, H - 62), npc_pos=npc_pos, sleep=list(sleep), links=s.links, label=label, beds=s.beds)


def _stairs(r, cx, by, to, spawn, label):
    r.put('ladder', cx, by, w=64, fp=(0.9, 0.35))
    r.links.append(dict(rect=pygame.Rect(cx - 30, by + 4, 60, 24), to=to, spawn=spawn, label=label))


def _inn():
    """Penginapan lantai 1: lobi / kedai. Tangga di kanan menuju kamar tidur lantai 2."""
    r = Room(640, 440, 96, 'wood', 11)
    r.put('window_a', 90, 84, h=60, wall=True); r.put('window_a', 530, 84, h=60, wall=True)
    r.put('banner_a', 215, 98, h=66, wall=True); r.put('banner_b', 445, 98, h=66, wall=True)
    r.put('shelf_w', 330, 100, w=128, wall=True)
    r.put('fireplace', 120, 138, w=108, fp=(0.8, 0.3))
    _stairs(r, 572, 150, 'inn2', (574, 200), 'Naik ke kamar')
    r.put('rug_blue', 200, 392, w=210, solid=False, ground=True); r.put('rug_red', 478, 372, w=150, solid=False, ground=True)
    r.put('desk', 300, 236, w=104, fp=(0.96, 0.6)); r.put('desk', 404, 236, w=104, fp=(0.96, 0.6))
    r.put('barrel_c', 206, 232, w=40, fp=(0.8, 0.6)); r.put('lantern_b', 470, 236, w=26, fp=(0.6, 0.5))
    r.put('table_big', 200, 360, w=112, fp=(0.86, 0.55)); r.put('chair_a', 128, 362, w=32, fp=(0.8, 0.55)); r.put('chair_a', 272, 362, w=32, fp=(0.8, 0.55), flip=True)
    r.put('table_fl', 478, 340, w=96, fp=(0.86, 0.55)); r.put('chair_a', 414, 346, w=30, fp=(0.8, 0.55)); r.put('chair_a', 542, 346, w=30, fp=(0.8, 0.55), flip=True)
    r.put('barrel_a', 52, 300, w=44, fp=(0.8, 0.55)); r.put('chest', 586, 250, w=58, fp=(0.9, 0.55)); r.put('potplant', 40, 410, w=36, fp=(0.7, 0.5))
    return r.finish((352, 192), label='Penginapan - Lantai 1', spawn=(320, 372))


def _inn2():
    """Penginapan lantai 2: kamar tidur (kasur kecil + meja nakas)."""
    r = Room(640, 440, 96, 'wood', 12)
    for x in (110, 320, 520): r.put('window_a', x, 84, h=60, wall=True)
    _stairs(r, 572, 150, 'inn', (574, 200), 'Turun ke lobi')
    r.put('rug_blue', 300, 428, w=150, solid=False, ground=True)
    beds = []
    for row, by in enumerate((206, 352)):
        for i, x in enumerate((84, 224, 364)):
            r.put('bed_blue' if (i + row) % 2 == 0 else 'bed_green', x, by, w=50, fp=(0.96, 0.8), bed=True); beds.append((x, by - 38))
            r.put('shelf_s', x + 44, by - 2, w=26, fp=(0.9, 0.5))
    r.put('cupboard', 574, 330, w=62, fp=(0.94, 0.55)); r.put('potplant', 592, 410, w=34, fp=(0.7, 0.5)); r.put('lantern_a', 470, 300, w=26, fp=(0.6, 0.5))
    r.put('chest', 520, 400, w=54, fp=(0.9, 0.55))
    spots = beds + [(250, 290), (330, 290), (420, 400), (60, 410)]
    return r.finish((0, 0), sleep=spots, label='Penginapan - Lantai 2', exit_door=False, spawn=(574, 200))


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
    r.put('lantern_a', 168, 236, w=30, fp=(0.6, 0.3))
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
    r.put('stove', 470, 140, w=104, fp=(0.9, 0.4)); r.put('bed_green', 70, 250, w=54, fp=(0.96, 0.8), bed=True); r.put('shelf_a', 232, 134, w=110, fp=(0.95, 0.4))
    r.put('rug_green', 300, 395, w=120, solid=False, ground=True)
    r.put('table_fl', 330, 316, w=104, fp=(0.85, 0.5)); r.put('chair_a', 262, 326, w=32, fp=(0.8, 0.5)); r.put('chair_a', 400, 326, w=32, fp=(0.8, 0.5), flip=True)
    r.put('potplant', 50, 394, w=44, fp=(0.6, 0.4)); r.put('barrel_c', 515, 390, w=40, fp=(0.8, 0.5)); r.put('lantern_b', 140, 200, w=26, fp=(0.6, 0.3))
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


_BUILD = {'inn': _inn, 'inn2': _inn2, 'church': _church, 'potion': _potion, 'smith': _smith, 'green': _green, 'windmill': _guild}


def build_interior(iid): return _BUILD[iid]()
