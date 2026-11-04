# -*- coding: utf-8 -*-
"""Chronicle of Eldenvale - RPG (Python + pygame) v1.1
Baru: masuk rumah, 57 monster, cahaya siang-malam, optimasi performa, menu pengaturan."""
import pygame, sys, os, random, json, math

BASE = os.path.dirname(os.path.abspath(__file__))
A = lambda *p: os.path.join(BASE, 'assets', *p)
ANDROID = 'ANDROID_ARGUMENT' in os.environ
DATA = (os.environ.get('ANDROID_PRIVATE') or BASE) if ANDROID else BASE
SAVE = os.path.join(DATA, 'save.json')
SETF = os.path.join(DATA, 'settings.json')
W, H = 1280, 720

pygame.init()
screen = pygame.display.set_mode((W, H), (pygame.FULLSCREEN if ANDROID else pygame.RESIZABLE) | pygame.SCALED)
pygame.display.set_caption("Eldenvale RPG")
clock = pygame.time.Clock()
ADD, MULT = pygame.BLEND_RGB_ADD, pygame.BLEND_RGB_MULT


def F(s, b=False):
    try: return pygame.font.SysFont("arial,dejavusans,freesans", s, bold=b)
    except Exception: return pygame.font.Font(None, int(s * 1.25))


f_xs, f_s, f_m, f_l = F(13, True), F(18), F(22), F(34, True)

# ---------- pengaturan ----------
OPTS = [
    ('preset', 'Kualitas grafik', ['Rendah', 'Sedang', 'Tinggi', 'Kustom']),
    ('light', 'Pencahayaan', ['Mati', 'Hemat', 'Normal', 'Tinggi']),
    ('part', 'Partikel (kunang-kunang)', ['Mati', 'Sedikit', 'Banyak']),
    ('rays', 'Sinar matahari', ['Mati', 'Hidup']),
    ('fps', 'Batas FPS', ['30', '45', '60']),
    ('showfps', 'Tampilkan FPS', ['Mati', 'Hidup']),
    ('auto', 'Auto-turunkan kualitas', ['Mati', 'Hidup']),
    ('tod', 'Waktu', ['Otomatis', 'Pagi', 'Siang', 'Senja', 'Malam']),
    ('shake', 'Guncangan layar', ['Mati', 'Hidup']),
    ('touch', 'Transparansi kontrol', ['Tipis', 'Sedang', 'Tebal']),
    ('autosave', 'Simpan otomatis', ['Mati', 'Hidup']),
]
PRESETS = [dict(light=1, part=0, rays=0, fps=1), dict(light=2, part=1, rays=0, fps=1), dict(light=3, part=2, rays=1, fps=2)]
DEF = dict(preset=1, light=2, part=1, rays=0, fps=1, showfps=0, auto=1, tod=0, shake=1, touch=1, autosave=1)
FPS_VALUES = [30, 45, 60]
S = dict(DEF)


def load_settings():
    try:
        with open(SETF) as fh: d = json.load(fh)
        for k, v in d.items():
            if k in DEF and isinstance(v, int): S[k] = v
        for k, _, vals in OPTS: S[k] = max(0, min(len(vals) - 1, S[k]))
    except Exception: pass


def save_settings():
    try:
        with open(SETF, 'w') as fh: json.dump(S, fh)
    except Exception: pass


load_settings()

# ---------- aset ----------
MAP = pygame.image.load(A('map.png')).convert()
MW, MH = MAP.get_size()
SHADOW = pygame.Surface((40, 16), pygame.SRCALPHA)
pygame.draw.ellipse(SHADOW, (0, 0, 0, 90), SHADOW.get_rect())


def load(name, h=None, scale=None):
    img = pygame.image.load(A(name)).convert_alpha()
    if scale: size = (max(1, int(img.get_width() * scale)), max(1, int(img.get_height() * scale)))
    else: size = (max(1, int(img.get_width() * h / img.get_height())), h)
    return pygame.transform.smoothscale(img, size)


class Sheet:
    def __init__(self, who, h=66, scale=None):
        self.f, self.idle = {}, {}
        for d in ('down', 'side', 'up'):
            fr, i = [], 0
            while os.path.exists(A(f'{who}_{d}_{i}.png')):
                fr.append(load(f'{who}_{d}_{i}.png', h, scale)); i += 1
            if len(fr) == 1: fr.append(fr[0])
            self.f[d] = fr
            p = f'{who}_idle_{d}.png'
            self.idle[d] = load(p, h, scale) if os.path.exists(A(p)) else fr[0]
        self.flipped = {}

    def get(self, d, step, flip=False, moving=True):
        fr = self.f[d]
        im = fr[int(step) % len(fr)] if moving else self.idle[d]
        if not flip: return im
        r = self.flipped.get(id(im))          # cache gambar terbalik (hemat CPU)
        if r is None: r = self.flipped[id(im)] = pygame.transform.flip(im, True, False)
        return r


# ---------- cache teks & panel (anti-lag) ----------
_tc, _pc = {}, {}


def tr(t, font, col):
    k = (t, id(font), col); s = _tc.get(k)
    if s is None:
        if len(_tc) > 700: _tc.clear()
        s = _tc[k] = font.render(t, True, col)
    return s


def txt(t, x, y, font=f_m, col=(255, 255, 255)):
    screen.blit(tr(t, font, (0, 0, 0)), (x + 2, y + 2)); screen.blit(tr(t, font, col), (x, y))


def panel(r, a=225):
    k = (r[2], r[3], a); s = _pc.get(k)
    if s is None:
        s = pygame.Surface((r[2], r[3]), pygame.SRCALPHA)
        pygame.draw.rect(s, (18, 18, 38, a), s.get_rect(), border_radius=12)
        pygame.draw.rect(s, (220, 190, 110), s.get_rect(), 3, border_radius=12)
        _pc[k] = s
    screen.blit(s, (r[0], r[1]))


def bar(x, y, w, v, m, col):
    pygame.draw.rect(screen, (30, 30, 40), (x, y, w, 14), border_radius=5)
    pygame.draw.rect(screen, col, (x, y, int(w * max(0, v) / max(1, m)), 14), border_radius=5)


def wrap(t, font, w):
    out, cur = [], ""
    for wd in t.split(" "):
        if font.size(cur + wd)[0] > w: out.append(cur); cur = wd + " "
        else: cur += wd + " "
    return out + [cur]


def clamp(v, a, b): return a if v < a else b if v > b else v


# ---------- dunia / collision ----------
BLOCK = [pygame.Rect(*r) for r in [
    (0, 0, MW, 50), (0, 0, 60, MH), (1470, 320, 300, 700), (1570, 0, 120, MH),
    (0, 0, 380, 245), (1340, 0, 100, 330), (1440, 0, 150, 270),
    (0, 790, 800, 200), (930, 830, 742, 111), (0, 920, MW, 30),
    (470, 115, 260, 150),   # penginapan
    (785, 50, 225, 210),    # gereja
    (1075, 175, 185, 135),  # toko ramuan
    (390, 300, 175, 175),   # pandai besi
    (1170, 360, 160, 125),  # rumah hijau
    (365, 480, 110, 150),   # kincir
    (340, 585, 470, 85),    # ladang
    (830, 355, 120, 100),   # air mancur
    (1040, 612, 345, 100),  # kolam
    (1400, 330, 70, 215),   # sungai
    (335, 650, 20, 20),
]]
# zona monster: (rect, tier) -> 0 padang, 1 perkemahan barat, 2 hutan dalam
ZONES = [(pygame.Rect(*r), t) for r, t in [
    ((60, 590, 260, 120), 0), ((900, 720, 520, 95), 0), ((330, 700, 470, 90), 0),
    ((1400, 560, 70, 150), 0), ((800, 790, 130, 130), 2), ((60, 260, 290, 290), 1)]]

# pintu rumah: rect pemicu (tepat di bawah bangunan), out = posisi pemain saat keluar
DOORS = {
    'inn':    dict(name='Penginapan',          rect=(600, 265, 64, 28),  out=(632, 309)),
    'church': dict(name='Balai Desa & Gereja', rect=(860, 260, 66, 28),  out=(893, 304)),
    'shop':   dict(name='Toko Ramuan',         rect=(1160, 310, 68, 28), out=(1194, 354)),
    'smith':  dict(name='Pandai Besi',         rect=(508, 475, 64, 28),  out=(540, 519)),
    'house':  dict(name='Rumah Hijau',         rect=(1172, 485, 62, 28), out=(1203, 529)),
    'mill':   dict(name='Kincir Angin',        rect=(388, 670, 64, 28),  out=(420, 714)),
    'barn':   dict(name='Lumbung',             rect=(703, 670, 64, 28),  out=(735, 714)),
    'dock':   dict(name='Dermaga Perahu',      rect=(1193, 712, 64, 28), out=(1225, 756)),
}
for _d in DOORS.values(): _d['r'] = pygame.Rect(*_d['rect'])

# interior: floor = area boleh dilewati, obs = rintangan, exit = zona pintu keluar (koordinat gambar)
# lights: (x, y, radius, warna, jenis)  jenis: lamp / fire / win
INT = {
    'inn': dict(img='home', name='Penginapan Eldenvale', floor=[(30, 130, 340, 215), (160, 335, 80, 45)], obs=[(50, 235, 100, 60)],
                exit=(165, 342, 70, 36), spawn=(200, 322), chests=[],
                npcs=[dict(name='Rosalind', who='rose', kind='inn', pos=(290, 180))],
                lights=[(88, 252, 110, (255, 150, 60), 'fire'), (105, 95, 80, (255, 235, 190), 'win'), (335, 70, 80, (255, 235, 190), 'win'),
                        (95, 100, 70, (255, 200, 120), 'lamp'), (200, 290, 120, (255, 200, 130), 'lamp')]),
    'shop': dict(img='shop', name='Toko Ramuan', floor=[(30, 165, 350, 175), (165, 335, 80, 45)], obs=[(225, 165, 110, 90), (350, 150, 40, 200)],
                 exit=(170, 345, 70, 35), spawn=(205, 322), chests=[],
                 npcs=[dict(name='Penyihir Orn', who='mage', kind='shop', pos=(200, 160))],
                 lights=[(150, 125, 120, (255, 210, 140), 'lamp'), (290, 120, 120, (255, 210, 140), 'lamp'), (205, 290, 130, (255, 200, 120), 'lamp'),
                         (100, 280, 90, (255, 120, 80), 'lamp')]),
    'smith': dict(img='smith', name='Pandai Besi Brom', floor=[(45, 125, 300, 100), (175, 215, 80, 27)], obs=[(130, 135, 50, 40), (105, 95, 90, 25)],
                  exit=(180, 220, 70, 22), spawn=(215, 203), chests=[],
                  npcs=[dict(name='Brom si Pandai Besi', who='smith', kind='smith', pos=(270, 160))],
                  lights=[(110, 115, 140, (255, 110, 30), 'fire'), (320, 55, 80, (255, 235, 190), 'win'), (260, 120, 90, (255, 190, 100), 'lamp')]),
    'house': dict(img='house', name='Rumah Hijau', floor=[(25, 100, 345, 150), (170, 245, 80, 50)], obs=[(25, 95, 60, 55)],
                  exit=(175, 262, 70, 30), spawn=(210, 232),
                  chests=[dict(id='house', pos=(330, 225), pot=1, gold=15)],
                  npcs=[dict(name='Tuan Edric', who='noble', kind='edric', pos=(300, 180))],
                  lights=[(190, 105, 80, (255, 235, 190), 'win'), (60, 120, 80, (255, 220, 150), 'lamp'), (330, 120, 90, (255, 215, 150), 'lamp')]),
    'mill': dict(img='mill', name='Kincir Angin', floor=[(150, 90, 235, 175), (235, 262, 70, 40)], obs=[(200, 145, 50, 40), (365, 110, 25, 90)],
                 exit=(240, 275, 60, 28), spawn=(265, 246),
                 chests=[dict(id='mill', pos=(200, 230), gold=25)],
                 npcs=[dict(name='Lina si Penggiling', who='girl', kind='miller', pos=(320, 200))],
                 lights=[(265, 40, 80, (255, 235, 190), 'win'), (290, 95, 110, (255, 210, 150), 'lamp'), (200, 190, 100, (255, 200, 130), 'lamp')]),
    'dock': dict(img='dock', name='Dermaga Perahu', floor=[(28, 70, 172, 110), (90, 172, 70, 40)], obs=[(60, 85, 60, 35)],
                 exit=(95, 185, 60, 28), spawn=(125, 158),
                 chests=[dict(id='dock', pos=(175, 95), gold=60)],
                 npcs=[dict(name='Pak Darma', who='knight', kind='fisher', pos=(60, 150))],
                 lights=[(40, 80, 90, (255, 190, 100), 'fire'), (150, 80, 90, (255, 190, 100), 'fire')]),
    'barn': dict(img='barn', name='Lumbung', floor=[(30, 115, 495, 150), (295, 262, 75, 60)], obs=[(55, 170, 130, 50), (470, 105, 60, 50)],
                 exit=(298, 285, 68, 32), spawn=(332, 248),
                 chests=[dict(id='barn', pos=(260, 150), pot=2, gold=30)],
                 npcs=[],
                 lights=[(360, 35, 100, (255, 235, 190), 'win'), (150, 100, 110, (255, 210, 140), 'lamp'), (440, 200, 100, (255, 200, 130), 'lamp')]),
    'church': dict(img='castle', name='Balai Desa & Gereja', floor=[(115, 305, 425, 200), (285, 495, 95, 80)], obs=[(190, 380, 80, 90), (465, 395, 70, 70)],
                   exit=(290, 548, 85, 30), spawn=(332, 518),
                   chests=[dict(id='church', pos=(150, 330), eth=1, gold=40)],
                   npcs=[dict(name='Suster Lyra', who='priest', kind='priest', pos=(330, 345))],
                   lights=[(330, 100, 120, (255, 235, 190), 'win'), (180, 250, 130, (255, 225, 160), 'lamp'), (480, 250, 130, (255, 225, 160), 'lamp'),
                           (330, 400, 190, (255, 215, 150), 'lamp'), (160, 440, 110, (255, 200, 120), 'lamp'), (500, 440, 110, (255, 200, 120), 'lamp')]),
}

WNPCS = [
    dict(name="Sir Aldric", who="knight", pos=(800, 330), kind="quest"),
    dict(name="Suster Lyra", who="priest", pos=(895, 292), kind="priest"),
    dict(name="Penyihir Orn", who="mage", pos=(1165, 320), kind="shop"),
    dict(name="Brom si Pandai Besi", who="smith", pos=(520, 492), kind="smith"),
    dict(name="Rosalind", who="rose", pos=(650, 290), kind="inn"),
    dict(name="Fenn si Pemanah", who="archer", pos=(1120, 520), kind="archer"),
    dict(name="Mira", who="girl", pos=(700, 565), kind="girl"),
]
NPCS = WNPCS
SPR = {}
HERO_H0 = pygame.image.load(A('hero_idle_down.png')).get_height()
HS = 76 / HERO_H0   # skala karakter utama
hero = Sheet('hero', scale=HS)
BAT_IDLE = load('hero_battle_idle.png', scale=HS * 3)
BAT_ATK = load('hero_battle_atk.png', scale=HS * 3)
RADIUS = {'quest': 70, 'priest': 55, 'shop': 55, 'smith': 70, 'inn': 80, 'archer': 130, 'girl': 150}
for n in NPCS:
    SPR[n['who']] = Sheet(n['who'], 66)
    n.update(pos=list(n['pos']), home=tuple(n['pos']), r=RADIUS.get(n['kind'], 70), d='down', flip=False,
             anim=0, moving=False, tgt=None, wait=pygame.time.get_ticks() + random.randint(500, 3500),
             spd=random.uniform(34, 52))


# ---------- state ----------
class P:  # player
    x, y = 880.0, 520.0
    ix, iy = 0.0, 0.0     # posisi di dalam rumah
    d, step, flip, dist, moving = 'down', 0, False, 0.0, False
    lv, xp, gold = 1, 0, 40
    hp = maxhp = 60
    mp = maxmp = 20
    atk, df = 9, 3
    pot, eth = 3, 1
    wl = 0
    slimes = 0
    quest = 0  # 0 belum,1 aktif,2 selesai,3 diambil
    tod = 9.0  # jam permainan
    opened = []
    status = 0


SAVE_KEYS = ['x', 'y', 'lv', 'xp', 'gold', 'hp', 'maxhp', 'mp', 'maxmp', 'atk', 'df', 'pot', 'eth', 'wl', 'slimes', 'quest', 'tod', 'opened']


def need(lv): return 20 + lv * lv * 8


def feet(x, y): return pygame.Rect(int(x) - 12, int(y) - 12, 24, 14)


def blocked(x, y, skip=None):
    r = feet(x, y)
    if r.collidelist(BLOCK) >= 0: return True
    for n in NPCS:
        if n is not skip and r.colliderect(feet(*n['pos']).inflate(10, 6)): return True
    if skip is not None and r.colliderect(feet(P.x, P.y).inflate(14, 8)): return True
    return False


def face(n, tx, ty):
    dx, dy = tx - n['pos'][0], ty - n['pos'][1]
    if abs(dx) > abs(dy): n['d'], n['flip'] = 'side', dx < 0
    else: n['d'], n['flip'] = ('down' if dy > 0 else 'up'), False


mode = 'explore'
scene = None       # None = dunia luar, selain itu kunci rumah
CUR = None         # data interior aktif
dialog = None      # dict(name, lines, i, cb)
menu = None        # dict(title, items, idx)
toast = ("", 0)
debug = False
walk_t = 0
battle = None
fade = None
sidx = 0           # indeks baris pengaturan


def update_npcs(dt):
    t = pygame.time.get_ticks()
    for n in NPCS:
        x, y = n['pos']
        far = abs(x - P.x) > 800 or abs(y - P.y) > 500
        if far: continue                                       # NPC jauh dari layar tidak diproses
        if mode != 'explore' or math.hypot(x - P.x, y - P.y) < 85:   # berhenti & menoleh ke pemain
            n['moving'] = False; n['tgt'] = None
            if mode == 'explore': face(n, P.x, P.y)
            continue
        if n['tgt'] is None:
            n['moving'] = False
            if t < n['wait']:
                if random.random() < 0.006: n['d'], n['flip'] = random.choice([('down', False), ('up', False), ('side', False), ('side', True)])
                continue
            hx, hy = n['home']; r = n['r']
            tx, ty = hx + random.uniform(-r, r), hy + random.uniform(-r * 0.6, r * 0.6)
            if blocked(tx, ty, n): n['wait'] = t + 250; continue
            n['tgt'] = (tx, ty)
        tx, ty = n['tgt']; dx, dy = tx - x, ty - y; dist = math.hypot(dx, dy)
        if dist < 4:
            n['tgt'] = None; n['moving'] = False; n['wait'] = t + random.randint(1500, 5000); continue
        sp = n['spd'] * min(dt, 50) / 1000
        nx, ny = x + dx / dist * sp, y + dy / dist * sp
        moved = False
        if not blocked(nx, y, n): n['pos'][0] = nx; moved = True
        if not blocked(n['pos'][0], ny, n): n['pos'][1] = ny; moved = True
        if not moved: n['tgt'] = None; n['wait'] = t + 600; n['moving'] = False; continue
        if abs(dx) > abs(dy): n['d'], n['flip'] = 'side', dx < 0
        else: n['d'], n['flip'] = ('down' if dy > 0 else 'up'), False
        n['moving'] = True; n['anim'] += dt


def say(name, lines, cb=None):
    global dialog, mode
    dialog = dict(name=name, lines=lines if isinstance(lines, list) else [lines], i=0, cb=cb)
    mode = 'dialog'


def note(t):
    global toast; toast = (t, pygame.time.get_ticks() + 2200)


def open_menu(title, items, close=True):
    global menu, mode
    menu = dict(title=title, items=items + ([("Tutup", None)] if close else []), idx=0); mode = 'menu'


def heal_full(): P.hp, P.mp = P.maxhp, P.maxmp


def gain(xp, gold):
    P.xp += xp; P.gold += gold; msgs = []
    while P.xp >= need(P.lv):
        P.xp -= need(P.lv); P.lv += 1
        P.maxhp += 12; P.maxmp += 4; P.atk += 3; P.df += 1
        heal_full(); msgs.append(f"LEVEL UP! Sekarang Lv {P.lv}")
    return msgs


# ---------- transisi layar ----------
FADE = pygame.Surface((W, H)); FADE.fill((0, 0, 0))


def go(cb):
    global fade
    if fade is None: fade = dict(t0=pygame.time.get_ticks(), half=240, cb=cb, done=False)


def update_fade():
    global fade
    if not fade: return
    t = pygame.time.get_ticks() - fade['t0']
    if t >= fade['half'] and not fade['done']: fade['done'] = True; fade['cb']()
    if t >= fade['half'] * 2: fade = None


def draw_fade():
    if not fade: return
    t = pygame.time.get_ticks() - fade['t0']; h = fade['half']
    a = t / h if t < h else 2 - t / h
    FADE.set_alpha(int(255 * clamp(a, 0, 1))); screen.blit(FADE, (0, 0))


# ---------- masuk / keluar rumah ----------
ISH = {}


def isheet(who, hpx):
    k = (who, hpx)
    if k not in ISH:
        if len(ISH) > 30: ISH.clear()
        ISH[k] = Sheet('hero', scale=hpx / HERO_H0) if who == 'hero' else Sheet(who, hpx)
    return ISH[k]


def make_chest(w, h, opened):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    body = (150, 95, 40); dark = (90, 55, 25); gold = (240, 200, 80)
    pygame.draw.rect(s, dark, (0, h // 3, w, h - h // 3), border_radius=4)
    pygame.draw.rect(s, body, (2, h // 3 + 2, w - 4, h - h // 3 - 4), border_radius=3)
    if opened:
        pygame.draw.rect(s, (30, 20, 10), (3, h // 3 - 2, w - 6, 8))
        pygame.draw.rect(s, body, (0, 0, w, h // 4), border_radius=4)
    else:
        pygame.draw.rect(s, body, (0, 0, w, h // 3 + 2), border_radius=6)
        pygame.draw.rect(s, gold, (w // 2 - 4, h // 3 - 3, 8, 10), border_radius=2)
    pygame.draw.rect(s, gold, (0, h // 3 + 3, w, 3))
    return s


def build_scene(key):
    global CUR
    d = INT[key]
    img = pygame.image.load(A('rooms', d['img'] + '.png')).convert()
    w, h = img.get_size()
    s = min(1180 / w, 640 / h, 2.4)
    scaled = pygame.transform.smoothscale(img, (int(w * s), int(h * s)))
    ph = int(54 * s); nh = int(54 * s * 66 / 76)
    npcs = [dict(nd, pos=list(nd['pos']), d='down', flip=False) for nd in d['npcs']]
    CUR = dict(key=key, d=d, img=scaled, s=s, ox=(W - scaled.get_width()) // 2, oy=(H - scaled.get_height()) // 2 + 14,
               floor=[pygame.Rect(*r) for r in d['floor']], obs=[pygame.Rect(*r) for r in d['obs']], exit=pygame.Rect(*d['exit']),
               npcs=npcs, chests=[dict(c) for c in d['chests']], hero=isheet('hero', ph),
               sh={n['who']: isheet(n['who'], nh) for n in npcs},
               shadow=pygame.transform.smoothscale(SHADOW, (max(8, int(34 * s)), max(4, int(12 * s)))),
               chest_img=(make_chest(int(26 * s), int(20 * s), False), make_chest(int(26 * s), int(20 * s), True)))


def enter_building(key):
    def cb():
        global scene
        door = DOORS[key]; P.x, P.y = door['out']
        build_scene(key); scene = key
        P.ix, P.iy = INT[key]['spawn']; P.d = 'up'; P.step = 0; P.moving = False
        joy_vec[0] = joy_vec[1] = 0.0
        if S['autosave']: save(True)
    go(cb)


def leave_building():
    def cb():
        global scene, CUR
        scene = None; CUR = None; P.d = 'down'; P.moving = False
        joy_vec[0] = joy_vec[1] = 0.0
    go(cb)


def ifeet(x, y): return pygame.Rect(int(x) - 8, int(y) - 8, 16, 10)


def iblocked(x, y, skip=None):
    r = ifeet(x, y); c = CUR
    for p in ((r.left, r.top), (r.right - 1, r.top), (r.left, r.bottom - 1), (r.right - 1, r.bottom - 1)):
        if not any(f.collidepoint(p) for f in c['floor']): return True
    if r.collidelist(c['obs']) >= 0: return True
    for n in c['npcs']:
        if r.colliderect(ifeet(*n['pos']).inflate(12, 8)): return True
    for ch in c['chests']:
        if r.colliderect(ifeet(*ch['pos']).inflate(10, 6)): return True
    return False


def near_door():
    r = feet(P.x, P.y).inflate(10, 12)
    for k, d in DOORS.items():
        if r.colliderect(d['r']): return k


# ---------- NPC logic ----------
def talk(n, px=None, py=None):
    face(n, P.x if px is None else px, P.y if py is None else py)
    k, nm = n['kind'], n['name']
    if k == 'quest':
        if P.quest == 0:
            say(nm, ["Selamat datang di Eldenvale, pengelana.", "Slime di hutan selatan makin banyak dan mengganggu ladang.",
                     "Kalahkan 5 slime di rumput luar desa. Hadiahnya 120 emas!"], lambda: setattr(P, 'quest', 1))
        elif P.quest == 1:
            if P.slimes >= 5:
                P.quest = 2; say(nm, ["Kau berhasil! Desa ini berutang budi padamu.", "Ini hadiahmu: 120 emas dan 40 XP."],
                                 lambda: ([note(m) for m in gain(40, 120)], setattr(P, 'quest', 3)))
            else:
                say(nm, [f"Slime terkalahkan: {P.slimes}/5. Cari di rumput luar desa (selatan & timur)."])
        else:
            say(nm, ["Terima kasih sudah menjaga desa. Berhati-hatilah di hutan dalam.", "Dan jangan keluar malam-malam: mayat hidup berkeliaran."])
    elif k == 'priest':
        say(nm, ["Cahaya melindungimu. Biarkan aku menyembuhkan lukamu."], lambda: (heal_full(), setattr(P, 'status', 0), note("HP & MP pulih penuh!")))
    elif k == 'inn':
        def rest():
            if P.gold >= 10:
                P.gold -= 10; heal_full()
                if S['tod'] == 0: P.tod = 7.5       # menginap = bangun pagi
                note("Istirahat nyenyak. HP & MP pulih (-10 emas)")
            else: note("Emas tidak cukup.")
        say(nm, ["Penginapan Eldenvale! Menginap hanya 10 emas.", "Bangun-bangun sudah pagi lagi, lho."], lambda: open_menu("Menginap 10 emas?", [("Ya, menginap", rest)]))
    elif k == 'shop':
        def buy(item, price):
            def f():
                if P.gold < price: note("Emas tidak cukup."); return
                P.gold -= price; setattr(P, item, getattr(P, item) + 1); note(f"Membeli 1 {'Ramuan' if item == 'pot' else 'Ether'}")
            return f
        say(nm, ["Ramuan segar, langsung dari kuali!"], lambda: open_menu("Toko Ramuan", [("Ramuan HP (30) - 15 emas", buy('pot', 15)), ("Ether MP (15) - 20 emas", buy('eth', 20))]))
    elif k == 'smith':
        def up():
            c = 50 * (P.wl + 1)
            if P.gold < c: note("Emas tidak cukup."); return
            P.gold -= c; P.wl += 1; P.atk += 3; note(f"Senjata +{P.wl}! ATK naik 3")
        say(nm, ["Besi yang baik butuh api yang panas!"], lambda: open_menu(f"Tempa senjata ({50 * (P.wl + 1)} emas, ATK +3)", [("Tempa", up)]))
    elif k == 'archer':
        say(nm, ["Rumput di selatan dan timur sering didatangi monster.", "Makin ke selatan jalan tanah, makin kuat musuhnya. Bawa ramuan!"])
    elif k == 'edric':
        def gift():
            if 'edric' in P.opened: note("Tuan Edric tersenyum ramah."); return
            P.opened.append('edric'); P.eth += 2; note("Mendapat 2 Ether!")
        say(nm, ["Malam hari hutan dipenuhi mayat hidup dan hantu.", "Mereka kuat, tapi hadiahnya juga besar. Bawa ramuan!", "Ini, ambil sedikit bekalku."], gift)
    elif k == 'miller':
        def eat(c, hp, mp, nama):
            def f():
                if P.gold < c: note("Emas tidak cukup."); return
                P.gold -= c; P.hp = min(P.maxhp, P.hp + hp); P.mp = min(P.maxmp, P.mp + mp); note(f"{nama}! HP +{hp} MP +{mp}")
            return f
        say(nm, ["Roti gandum baru keluar dari oven!"], lambda: open_menu("Roti & Susu", [("Roti gandum (HP+40) - 12 emas", eat(12, 40, 0, "Nyam")), ("Susu segar (MP+15) - 10 emas", eat(10, 0, 15, "Segar"))]))
    elif k == 'fisher':
        def fish():
            if P.gold < 5: note("Emas tidak cukup."); return
            P.gold -= 5; r = random.random()
            if r < 0.12: P.pot += 1; note("Dapat Ramuan dalam botol!")
            elif r < 0.55: g = random.randint(8, 22); P.gold += g; note(f"Ikan besar! Dijual {g} emas")
            else: note("Hanya sampah... coba lagi.")
        say(nm, ["Dermaga ini sepi, tapi ikannya melimpah.", "Konon di hutan terdalam ada naga tua yang menjaga harta."], lambda: open_menu("Memancing 5 emas?", [("Pancing!", fish)]))
    else:
        say(nm, ["Ada kincir angin dan ladang di sana. Kata kakek, sungai itu berasal dari air terjun ajaib.", "Masuk saja ke rumah-rumah, pintunya selalu terbuka!"])


def open_chest(c):
    if c['id'] in P.opened: note("Peti ini sudah kosong."); return
    P.opened.append(c['id']); parts = []
    for k, nm in (('gold', 'emas'), ('pot', 'Ramuan'), ('eth', 'Ether')):
        v = c.get(k, 0)
        if v:
            parts.append(f"{v} {nm}")
            if k == 'gold': P.gold += v
            else: setattr(P, k, getattr(P, k) + v)
    note("Peti terbuka: " + ", ".join(parts))


# ---------- monster ----------
# key: (nama, power, kemampuan)   kemampuan: poison burn drain heavy fast
MON = {
    'slime_biru': ('Slime Biru', 1, None), 'slime_hijau': ('Slime Hijau', 1.2, None), 'slime_ungu': ('Slime Ungu', 2, None),
    'slime_oranye': ('Slime Api', 4, 'burn'), 'raja_slime': ('Raja Slime', 14, 'heavy'),
    'babi_hutan': ('Babi Hutan', 2.5, 'fast'), 'babi_raksasa': ('Babi Raksasa', 6.5, 'heavy'), 'kelelawar': ('Kelelawar', 1.5, 'fast'),
    'goblin': ('Goblin', 3, None), 'goblin_perisai': ('Goblin Perisai', 5, None), 'goblin_pemanah': ('Goblin Pemanah', 4.5, 'fast'),
    'bandit': ('Bandit', 5, 'fast'), 'bandit_elit': ('Bandit Elit', 11, 'fast'),
    'serigala': ('Serigala', 5, 'fast'), 'serigala_putih': ('Serigala Salju', 6, 'fast'),
    'laba_merah': ('Laba-laba Merah', 5.5, 'poison'), 'laba_hitam': ('Laba-laba Hitam', 10, 'poison'), 'bunga_buas': ('Bunga Buas', 6, 'poison'),
    'rangka': ('Prajurit Rangka', 8, None), 'rangka_penyihir': ('Penyihir Rangka', 10, 'burn'), 'zombi': ('Zombi', 8, 'heavy'),
    'ghoul': ('Ghoul', 9, 'poison'), 'lendir': ('Lendir Racun', 7, 'poison'), 'kobra': ('Kobra', 9, 'poison'), 'kalajengking': ('Kalajengking', 9.5, 'poison'),
    'golem_lumut': ('Golem Lumut', 12, 'heavy'),
    'bayangan': ('Bayangan', 12, 'drain'), 'tengkorak_api': ('Tengkorak Api', 13, 'burn'), 'hantu': ('Hantu Rantai', 13, 'drain'),
    'wraith': ('Wraith', 15, 'drain'), 'ksatria_rangka': ('Ksatria Rangka', 16, None), 'malaikat_maut': ('Malaikat Maut', 18, 'drain'),
    'golem_kristal': ('Golem Kristal', 18, 'heavy'), 'api': ('Elemental Api', 17, 'burn'), 'es': ('Elemental Es', 17, None),
    'treant': ('Treant', 19, 'heavy'), 'drake': ('Drake', 20, 'burn'), 'wyvern': ('Wyvern', 16, 'fast'), 'laba_kristal': ('Laba Kristal', 15, 'poison'),
    'hydra': ('Hydra', 24, 'poison'), 'vampir': ('Vampir', 22, 'drain'), 'lich': ('Lich', 26, 'drain'), 'ksatria_gelap': ('Ksatria Gelap', 24, 'heavy'),
    'ksatria_hitam': ('Ksatria Hitam', 25, 'heavy'), 'iblis': ('Iblis', 28, 'burn'), 'iblis_sayap': ('Iblis Bersayap', 27, 'fast'),
    'golem_batu': ('Golem Batu', 14, 'heavy'), 'golem_zamrud': ('Golem Zamrud', 22, 'heavy'), 'anjing_neraka': ('Anjing Neraka', 21, 'burn'),
    'binatang_gelap': ('Binatang Gelap', 20, 'fast'), 'naga_putih': ('Naga Putih', 30, 'heavy'), 'naga_es': ('Naga Es', 30, None),
    'naga_emas': ('Naga Emas', 34, 'burn'), 'naga_laut': ('Naga Laut', 32, 'poison'), 'naga_void': ('Naga Void', 38, 'drain'),
    'dewi': ('Dewi Cahaya', 30, 'drain'), 'treant_kuno': ('Treant Kuno', 32, 'heavy'),
}
POOL = {
    0: ['slime_biru', 'slime_hijau', 'slime_hijau', 'slime_biru', 'babi_hutan', 'kelelawar', 'goblin', 'slime_ungu'],
    1: ['serigala', 'serigala_putih', 'goblin_pemanah', 'goblin_perisai', 'bandit', 'laba_merah', 'babi_raksasa', 'slime_oranye', 'bunga_buas'],
    2: ['rangka', 'zombi', 'ghoul', 'kobra', 'kalajengking', 'laba_hitam', 'rangka_penyihir', 'bandit_elit', 'lendir', 'golem_lumut'],
    3: ['bayangan', 'tengkorak_api', 'hantu', 'wraith', 'ksatria_rangka', 'golem_kristal', 'api', 'es', 'treant', 'drake', 'wyvern', 'laba_kristal', 'golem_batu'],
    4: ['raja_slime', 'hydra', 'vampir', 'lich', 'ksatria_gelap', 'ksatria_hitam', 'iblis', 'iblis_sayap', 'anjing_neraka', 'binatang_gelap', 'malaikat_maut', 'golem_zamrud'],
    5: ['naga_putih', 'naga_es', 'naga_emas', 'naga_laut', 'naga_void', 'dewi', 'treant_kuno'],
}
MSPR = {}


def get_mon(key):
    s = MSPR.get(key)
    if s is None:
        img = pygame.image.load(A('monsters', key + '.png')).convert_alpha()
        h = clamp(int(img.get_height() * 1.35), 150, 270)
        s = pygame.transform.smoothscale(img, (max(1, int(img.get_width() * h / img.get_height())), h))
        if len(MSPR) > 10: MSPR.pop(next(iter(MSPR)))
        MSPR[key] = s
    return s


def pick_monster(tier):
    dk = darkness()
    t = tier
    if P.lv >= 8 and random.random() < 0.3: t = min(t + 1, 4)
    if dk > 0.5 and random.random() < 0.35: t = min(t + 1, 4)   # malam: monster lebih kuat
    elite = random.random() < 0.06
    if elite: t = min(t + 1, 5)
    return random.choice(POOL[t]), elite


def start_battle(tier=0):
    global battle, mode
    key, elite = pick_monster(tier)
    nm, p, ab = MON[key]
    s = 1 + (P.lv - 1) * 0.18; m = 1.6 if elite else 1.0
    hp = int((14 + p * 8) * s * m)
    snap = screen.copy()
    ov = pygame.Surface((W, H), pygame.SRCALPHA); ov.fill((0, 0, 20, 150)); snap.blit(ov, (0, 0))   # digelapkan sekali saja
    battle = dict(name=('[Elit] ' if elite else '') + nm, key=key, hp=hp, maxhp=hp, atk=int((3.5 + p * 1.8) * s * (1.25 if elite else 1)),
                  xp=int((4 + p * 3.8) * s * m), gold=int((3 + p * 3) * s * m), ab=ab, turn=0, spr=get_mon(key),
                  snap=snap, state='cmd', idx=0, log=f"{'Monster elit' if elite else 'Seekor'} {nm} muncul!", t=0, shake=0, flash=0, atk_until=0)
    P.status = 0
    mode = 'battle'


def blog(t, state, delay=700):
    battle['log'] = t; battle['state'] = state; battle['t'] = pygame.time.get_ticks() + delay


def player_act(i):
    b = battle
    sh = 1 if S['shake'] else 0
    if i == 0:
        d = max(1, P.atk + random.randint(-2, 3)); b['hp'] -= d; b['shake'] = 12 * sh; b['atk_until'] = pygame.time.get_ticks() + 650
        blog(f"Kamu menyerang! {d} damage.", 'after')
    elif i == 1:
        if P.mp < 5: blog("MP tidak cukup!", 'cmd', 500); return
        P.mp -= 5; d = int(P.atk * 2 + random.randint(0, 4)); b['hp'] -= d; b['shake'] = 18 * sh; b['atk_until'] = pygame.time.get_ticks() + 650
        blog(f"Tebasan Merah! {d} damage.", 'after')
    elif i == 2:
        if P.pot > 0:
            P.pot -= 1; P.hp = min(P.maxhp, P.hp + 30); cured = P.status > 0; P.status = 0
            blog("Minum Ramuan: HP +30." + (" Racun/api hilang." if cured else ""), 'enemy')
        elif P.eth > 0: P.eth -= 1; P.mp = min(P.maxmp, P.mp + 15); blog("Minum Ether: MP +15.", 'enemy')
        else: blog("Tidak punya item!", 'cmd', 500)
    elif i == 3:
        if b['key'].startswith('naga') or b['key'] in ('raja_slime', 'dewi'): blog("Musuh ini terlalu cepat untuk ditinggal kabur!", 'enemy')
        elif random.random() < 0.6: blog("Berhasil kabur!", 'end_run', 800)
        else: blog("Gagal kabur!", 'enemy')


def update_battle():
    global mode, battle
    b = battle
    if b['shake'] > 0: b['shake'] -= 1
    if b['flash'] > 0: b['flash'] -= 1
    if pygame.time.get_ticks() < b['t']: return
    s = b['state']
    if s == 'after':
        if b['hp'] <= 0:
            if b['key'].startswith('slime') and P.quest == 1: P.slimes += 1
            msgs = gain(b['xp'], b['gold'])
            blog(f"{b['name']} kalah! +{b['xp']} XP, +{b['gold']} emas. " + " ".join(msgs), 'end_win', 1600)
        else: b['state'] = 'enemy'
    elif s == 'enemy':
        b['turn'] += 1; ab = b['ab']; nm = b['name']
        d = max(1, b['atk'] - P.df + random.randint(-1, 2))
        if ab == 'heavy' and b['turn'] % 3 == 0: d = int(d * 1.8) + 1; msg = f"{nm} melancarkan serangan dahsyat! {d} damage."
        elif ab == 'fast' and random.random() < 0.25: d += max(1, d // 2); msg = f"{nm} menyerang dua kali! {d} damage."
        else: msg = f"{nm} menyerang! {d} damage."
        if P.status > 0: d += 3; P.status -= 1; msg += " (+3 efek racun/api)"
        elif ab in ('poison', 'burn') and random.random() < 0.4: P.status = 3; msg += " Kamu terkena racun!" if ab == 'poison' else " Kamu terbakar!"
        if ab == 'drain': h = max(1, d // 2); b['hp'] = min(b['maxhp'], b['hp'] + h); msg += f" Menyerap {h} HP."
        P.hp -= d; b['flash'] = 10 if S['shake'] else 0
        if P.hp <= 0: P.hp = 0; blog(f"{nm} menyerang {d}! Kamu tumbang...", 'end_lose', 1500)
        else: blog(msg, 'cmd', 600)
    elif s in ('end_win', 'end_run'):
        mode = 'explore'; battle = None; P.status = 0
        if S['autosave'] and s == 'end_win': save(True)
    elif s == 'end_lose':
        P.gold //= 2; P.hp, P.mp = P.maxhp // 2, P.maxmp // 2; P.x, P.y = 880.0, 520.0; P.status = 0
        mode = 'explore'; battle = None
        if scene: leave_building()
        note("Kamu pingsan & terbangun di alun-alun (emas -50%)")


ENEMY_SHADOW = pygame.Surface((220, 40), pygame.SRCALPHA)
pygame.draw.ellipse(ENEMY_SHADOW, (0, 0, 0, 110), ENEMY_SHADOW.get_rect())


def draw_battle():
    b = battle; t = pygame.time.get_ticks()
    screen.blit(b['snap'], (0, 0))
    pim = BAT_ATK if t < b.get('atk_until', 0) else BAT_IDLE
    ox = random.randint(-6, 6) if b['flash'] else 0
    screen.blit(pim, (170 + ox, 510 - pim.get_height() + int(math.sin(t / 280) * 4)))
    if b['hp'] > 0 or b['state'] == 'after':
        sx = random.randint(-8, 8) if b['shake'] else 0
        sp = b['spr']; bob = int(math.sin(t / 250) * 6)
        screen.blit(ENEMY_SHADOW, (900 + sx - 110, 440))
        screen.blit(sp, (900 + sx - sp.get_width() // 2, 450 - sp.get_height() + bob))
    txt(f"{b['name']}", 760, 120, f_l); bar(760, 175, 280, b['hp'], b['maxhp'], (220, 60, 60))
    panel((30, 30, 330, 100)); txt(f"Lv {P.lv}  HP {P.hp}/{P.maxhp}" + ("  [Efek]" if P.status else ""), 50, 40); bar(50, 75, 280, P.hp, P.maxhp, (80, 210, 90))
    txt(f"MP {P.mp}/{P.maxmp}", 50, 95, f_s)
    panel((20, 520, W - 40, 180))
    for i, l in enumerate(wrap(b['log'], f_m, 620)[:4]): txt(l, 45, 540 + i * 30)
    if b['state'] == 'cmd':
        for i, c in enumerate(["Serang", "Tebasan (5 MP)", f"Item (R{P.pot}/E{P.eth})", "Kabur"]):
            col = (255, 220, 90) if i == b['idx'] else (230, 230, 230)
            txt(("> " if i == b['idx'] else "  ") + c, 800 + (i % 2) * 230, 560 + (i // 2) * 55, f_m, col)


# ---------- waktu & cahaya ----------
AMB = [(0, (45, 52, 105)), (4.5, (48, 56, 110)), (6, (190, 150, 150)), (7.5, (250, 235, 215)), (9, (255, 255, 250)), (16, (255, 252, 245)),
       (17.5, (255, 205, 150)), (19, (150, 95, 120)), (20.5, (55, 58, 110)), (24, (45, 52, 105))]
FIXED_TOD = [None, 7.5, 12.5, 18.3, 23.0]
AMB_NOW, DARK = (255, 255, 255), 0.0


def cur_tod():
    f = FIXED_TOD[S['tod']]
    return P.tod if f is None else f


def ambient(h):
    for i in range(len(AMB) - 1):
        h0, c0 = AMB[i]; h1, c1 = AMB[i + 1]
        if h0 <= h <= h1:
            k = (h - h0) / (h1 - h0)
            return tuple(int(c0[j] + (c1[j] - c0[j]) * k) for j in range(3))
    return AMB[0][1]


def update_light_state():
    global AMB_NOW, DARK
    AMB_NOW = ambient(cur_tod() % 24)
    DARK = clamp(1 - (AMB_NOW[0] * .3 + AMB_NOW[1] * .59 + AMB_NOW[2] * .11) / 255, 0, 1)


def darkness(): return DARK


def tod_str():
    h = cur_tod() % 24
    nm = 'Pagi' if 5 <= h < 10 else 'Siang' if 10 <= h < 15 else 'Sore' if 15 <= h < 18 else 'Senja' if 18 <= h < 20.5 else 'Malam'
    return f"{nm} {int(h):02d}:{int((h % 1) * 60):02d}"


_gl = {}


def glow(r, col, lv):
    """sprite cahaya radial (hitam di luar) untuk blending ADD. lv 1..6"""
    k = (r, col, lv); s = _gl.get(k)
    if s is None:
        if len(_gl) > 220: _gl.clear()
        s = pygame.Surface((r * 2, r * 2)); s.fill((0, 0, 0))
        f0 = lv / 6.0; steps = max(8, min(r, 48))
        for i in range(steps, 0, -1):
            k2 = i / steps; f = (1 - k2) ** 2 * f0
            pygame.draw.circle(s, (int(col[0] * f), int(col[1] * f), int(col[2] * f)), (r, r), max(1, int(r * k2)))
        _gl[k] = s
    return s


def make_vig(lw, lh):
    s = pygame.Surface((lw, lh)); steps = 24
    s.fill((153, 153, 153))
    for i in range(steps, 0, -1):
        t = i / steps; v = int(255 * (1 - 0.4 * t ** 3))
        w, h = int(lw * (0.45 + 0.9 * t)), int(lh * (0.45 + 0.9 * t))
        pygame.draw.ellipse(s, (v, v, v), ((lw - w) // 2, (lh - h) // 2, w, h))
    return s


LM_CACHE = {}


def apply_light(amb, lights):
    ml = S['light']
    if ml == 0: return
    if ml == 1:      # hemat: tint satu kali + kilau aditif (sangat ringan)
        screen.fill(amb, special_flags=MULT)
        for sx, sy, r, col, it in lights:
            rr = max(8, (int(r * 0.5) // 8) * 8)
            screen.blit(glow(rr, col, int(clamp(round(it * 5), 1, 6))), (int(sx - rr), int(sy - rr)), special_flags=ADD)
        return
    ls = 4 if ml == 2 else 3
    ent = LM_CACHE.get(ls)
    if ent is None:
        lw, lh = W // ls, H // ls
        ent = LM_CACHE[ls] = (pygame.Surface((lw, lh)), pygame.Surface((W, H)), make_vig(lw, lh))
    lm, full, vig = ent
    lm.fill(amb); lm.blit(vig, (0, 0), special_flags=MULT)
    for sx, sy, r, col, it in lights:
        rr = max(6, (int(r / ls) // 6) * 6)
        lm.blit(glow(rr, col, int(clamp(round(it * 6), 1, 6))), (int(sx / ls - rr), int(sy / ls - rr)), special_flags=ADD)
    if ml == 3:
        try: pygame.transform.smoothscale(lm, (W, H), full)
        except Exception: pygame.transform.scale(lm, (W, H), full)
    else: pygame.transform.scale(lm, (W, H), full)
    screen.blit(full, (0, 0), special_flags=MULT)
    for sx, sy, r, col, it in lights:       # bloom kecil di sumber cahaya
        if it > 0.35:
            rr = max(6, (int(r * 0.2) // 6) * 6)
            screen.blit(glow(rr, col, int(clamp(round(it * 2.5), 1, 3))), (int(sx - rr), int(sy - rr)), special_flags=ADD)


# lampu dunia luar: (x, y, radius, warna, jenis)
LAMP, WIN, FIRE = (255, 205, 130), (255, 195, 115), (255, 135, 45)
WLIGHTS = [
    (741, 212, 190, LAMP, 'lamp'), (1039, 218, 190, LAMP, 'lamp'), (714, 344, 190, LAMP, 'lamp'), (1065, 348, 190, LAMP, 'lamp'),
    (800, 517, 170, LAMP, 'lamp'), (970, 511, 170, LAMP, 'lamp'), (837, 571, 170, LAMP, 'lamp'), (938, 571, 170, LAMP, 'lamp'),
    (511, 207, 110, WIN, 'win'), (551, 209, 110, WIN, 'win'), (672, 204, 110, WIN, 'win'), (895, 218, 130, WIN, 'win'), (890, 189, 90, WIN, 'win'),
    (1148, 235, 110, WIN, 'win'), (1217, 235, 110, WIN, 'win'), (1194, 272, 80, WIN, 'win'),
    (434, 385, 110, WIN, 'win'), (540, 402, 100, WIN, 'win'), (1194, 425, 110, WIN, 'win'), (1269, 419, 110, WIN, 'win'),
    (491, 402, 170, FIRE, 'fire'), (181, 379, 230, FIRE, 'fire'), (890, 402, 170, (120, 190, 255), 'cool'),
]


def lint(kind, i, t):
    if kind == 'lamp': return 0.2 + 0.8 * DARK
    if kind == 'win': return max(0.0, DARK * 1.1 - 0.15)
    if kind == 'fire': return (0.55 + 0.45 * DARK) * (0.9 + 0.1 * math.sin(t / 70 + i * 1.7) + 0.05 * math.sin(t / 37 + i * 2.3))
    return 0.12 + 0.7 * DARK


def world_lights(cx, cy, t):
    out = []
    for i, (x, y, r, col, kind) in enumerate(WLIGHTS):
        sx, sy = x - cx, y - cy
        if sx < -r or sx > W + r or sy < -r or sy > H + r: continue
        it = lint(kind, i, t)
        if it > 0.12: out.append((sx, sy, r, col, it))
    if DARK > 0.3: out.append((P.x - cx, P.y - cy - 30, 150, (255, 235, 200), 0.55 * DARK))   # lentera pemain
    return out


def int_amb():
    d = clamp(DARK / 0.78, 0, 1)
    return tuple(int(a + (b - a) * d) for a, b in zip((228, 218, 208), (105, 105, 140)))


def int_lights(t):
    c = CUR; s = c['s']; d = clamp(DARK / 0.78, 0, 1); out = []
    for i, (x, y, r, col, kind) in enumerate(c['d']['lights']):
        if kind == 'win':
            if DARK < 0.5: col, it = (255, 240, 200), 0.9 * (1 - d) + 0.15
            else: col, it = (120, 150, 230), 0.4
        elif kind == 'fire': it = (0.8 + 0.2 * d) * (0.9 + 0.1 * math.sin(t / 70 + i * 1.7) + 0.05 * math.sin(t / 37 + i * 2.3))
        else: it = 0.5 + 0.4 * d
        out.append((c['ox'] + x * s, c['oy'] + y * s, r * s, col, clamp(it, 0, 1)))
    return out


RAYS = {}


def get_rays(gold):
    k = 'gold' if gold else 'day'
    if k not in RAYS:
        ls = 4; lw, lh = W // ls, H // ls
        s = pygame.Surface((lw, lh)); s.fill((0, 0, 0))
        col = (54, 34, 10) if gold else (26, 24, 12)
        for i in range(6):
            x0 = lw * (0.2 + 0.15 * i); wd = lw * (0.035 + 0.018 * (i % 3))
            for layer in range(3):
                f = (layer + 1) / 3; ww = wd * (1.7 - 0.55 * layer)
                pygame.draw.polygon(s, tuple(int(v * f) for v in col), [(x0, 0), (x0 + ww, 0), (x0 + ww - lw * 0.5, lh), (x0 - lw * 0.5, lh)])
        full = pygame.Surface((W, H)); pygame.transform.scale(s, (W, H), full); RAYS[k] = full
    return RAYS[k]


def draw_rays(t):
    if not S['rays'] or DARK > 0.35 or S['light'] == 0: return
    h = cur_tod() % 24
    screen.blit(get_rays(h < 8.2 or h > 16.5), (int(math.sin(t / 3500) * 18), 0), special_flags=ADD)


PART = []


def init_particles():
    n = [0, 14, 32][S['part']]
    PART[:] = [[random.uniform(0, W), random.uniform(0, H), random.uniform(-14, 14), random.uniform(-12, 8), random.uniform(0, 6.28)] for _ in range(n)]


def update_particles(dt):
    s = dt / 1000
    for p in PART:
        p[0] += p[2] * s; p[1] += p[3] * s; p[4] += s * 2
        if p[0] < -10: p[0] = W + 5
        elif p[0] > W + 10: p[0] = -5
        if p[1] < -10: p[1] = H + 5
        elif p[1] > H + 10: p[1] = -5
        if random.random() < 0.02: p[2] = random.uniform(-14, 14); p[3] = random.uniform(-12, 8)


def draw_particles():
    if not PART or S['light'] == 0: return
    night = DARK > 0.35
    for i, p in enumerate(PART):
        if night:
            lv = int(2.5 + 2.5 * math.sin(p[4]))
            if lv < 1: continue
            spr = glow(7, (190, 255, 110), min(lv, 5)); r = 7
        else:
            if i % 2: continue
            spr = glow(4, (200, 190, 140), 2); r = 4
        screen.blit(spr, (int(p[0]) - r, int(p[1]) - r), special_flags=ADD)


# ---------- gambar dunia ----------
CAM = [0, 0]


def draw_hud():
    panel((10, 10, 330, 92), 190)
    txt(f"Lv {P.lv}  XP {P.xp}/{need(P.lv)}", 24, 14, f_s); bar(24, 40, 290, P.hp, P.maxhp, (80, 210, 90)); bar(24, 62, 290, P.mp, P.maxmp, (90, 140, 255))
    txt(f"HP {P.hp}/{P.maxhp}", 30, 36, f_xs); txt(f"MP {P.mp}/{P.maxmp}", 30, 58, f_xs)
    panel((W - 330, 10, 320, 88), 190)
    txt(f"Emas {P.gold}  Ramuan {P.pot}  Ether {P.eth}", W - 318, 14, f_s)
    q = {0: "Quest: bicara dgn Sir Aldric", 1: f"Quest: kalahkan Slime {min(P.slimes, 5)}/5", 2: "Quest: lapor ke Sir Aldric", 3: "Quest selesai!"}[P.quest]
    txt(q, W - 318, 38, f_s, (255, 220, 120))
    txt(tod_str(), W - 318, 62, f_s, (190, 220, 255))
    if scene:
        panel((W // 2 - 170, 10, 340, 40), 190); lab = tr(INT[scene]['name'], f_m, (255, 240, 180)); screen.blit(lab, (W // 2 - lab.get_width() // 2, 17))
    if not ANDROID: txt("WASD/Panah: jalan  Z/Spasi: bicara/masuk  P: ramuan  Esc: menu  F5 simpan  F9 muat", 10, H - 26, F13, (230, 230, 230))
    if pygame.time.get_ticks() < toast[1]:
        panel((W // 2 - 300, 120, 600, 44)); txt(toast[0], W // 2 - 285, 128, f_s)


F13 = F(14)


def draw_world():
    t = pygame.time.get_ticks()
    cx = clamp(int(P.x - W / 2), 0, MW - W); cy = clamp(int(P.y - H / 2), 0, MH - H); CAM[0], CAM[1] = cx, cy
    screen.blit(MAP, (0, 0), (cx, cy, W, H))
    ents = []
    for n in NPCS:
        x, y = n['pos']
        if x < cx - 80 or x > cx + W + 80 or y < cy - 40 or y > cy + H + 200: continue
        ents.append((y, SPR[n['who']].get(n['d'], n['anim'] // 190, n['flip'], n['moving']), n['pos'], n['name']))
    ents.append((P.y, hero.get(P.d, P.step, P.flip, P.moving), (P.x, P.y), None))
    labels = []
    for _, im, (x, y), nm in sorted(ents, key=lambda e: e[0]):
        sx, sy = int(x - cx), int(y - cy)
        screen.blit(SHADOW, (sx - 20, sy - 9))
        screen.blit(im, (sx - im.get_width() // 2, sy - im.get_height() + 6))
        if nm: labels.append((nm, sx, sy - im.get_height() - 12))
    for k, d in DOORS.items():       # penanda pintu
        r = d['r']; dx, dy = r.centerx - P.x, r.centery - P.y
        if dx * dx + dy * dy < 240 * 240:
            x, y = r.centerx - cx, r.top - cy - 4 + int(math.sin(t / 260) * 4)
            pygame.draw.polygon(screen, (40, 30, 10), [(x, y - 13), (x - 11, y + 5), (x + 11, y + 5)])
            pygame.draw.polygon(screen, (255, 220, 100), [(x, y - 10), (x - 8, y + 3), (x + 8, y + 3)])
            if dx * dx + dy * dy < 130 * 130: labels.append((d['name'], x, y - 36))
    if S['light'] and DARK > 0.06: apply_light(AMB_NOW, world_lights(cx, cy, t))
    draw_rays(t); draw_particles()
    for nm, x, y in labels:
        lab = tr(nm, f_s, (255, 240, 180)); screen.blit(lab, (x - lab.get_width() // 2, y))
    if debug:
        for b in BLOCK: pygame.draw.rect(screen, (255, 0, 0), b.move(-cx, -cy), 2)
        for b, _ in ZONES: pygame.draw.rect(screen, (255, 255, 0), b.move(-cx, -cy), 2)
        for d in DOORS.values(): pygame.draw.rect(screen, (0, 255, 255), d['r'].move(-cx, -cy), 2)
        for x, y, r, col, kind in WLIGHTS: pygame.draw.circle(screen, col, (x - cx, y - cy), 6, 2)
    draw_hud()


def draw_interior():
    t = pygame.time.get_ticks(); c = CUR; s = c['s']; ox, oy = c['ox'], c['oy']
    screen.fill((6, 6, 10)); screen.blit(c['img'], (ox, oy))
    ents = []
    for n in c['npcs']: ents.append((n['pos'][1], c['sh'][n['who']].get(n['d'], 0, n['flip'], False), n['pos'], n['name']))
    for ch in c['chests']: ents.append((ch['pos'][1], c['chest_img'][1 if ch['id'] in P.opened else 0], ch['pos'], None))
    ents.append((P.iy, c['hero'].get(P.d, P.step, P.flip, P.moving), (P.ix, P.iy), None))
    labels = []
    for _, im, (x, y), nm in sorted(ents, key=lambda e: e[0]):
        sx, sy = int(ox + x * s), int(oy + y * s)
        screen.blit(c['shadow'], (sx - c['shadow'].get_width() // 2, sy - c['shadow'].get_height() // 2))
        screen.blit(im, (sx - im.get_width() // 2, sy - im.get_height() + int(im.get_height() * 0.08)))
        if nm: labels.append((nm, sx, sy - im.get_height() - 8))
    if S['light']: apply_light(int_amb(), int_lights(t))
    for nm, x, y in labels:
        lab = tr(nm, f_s, (255, 240, 180)); screen.blit(lab, (x - lab.get_width() // 2, y))
    if debug:
        for f in c['floor']: pygame.draw.rect(screen, (0, 255, 0), pygame.Rect(ox + f.x * s, oy + f.y * s, f.w * s, f.h * s), 2)
        for f in c['obs']: pygame.draw.rect(screen, (255, 0, 0), pygame.Rect(ox + f.x * s, oy + f.y * s, f.w * s, f.h * s), 2)
        e = c['exit']; pygame.draw.rect(screen, (0, 255, 255), pygame.Rect(ox + e.x * s, oy + e.y * s, e.w * s, e.h * s), 2)
    draw_hud()


def draw_dialog():
    panel((40, 500, W - 80, 190))
    txt(dialog['name'], 70, 510, f_m, (255, 220, 100))
    if dialog.get('wi') != dialog['i']: dialog['w'] = wrap(dialog['lines'][dialog['i']], f_m, W - 180); dialog['wi'] = dialog['i']
    for i, l in enumerate(dialog['w'][:4]): txt(l, 70, 548 + i * 30)
    txt("Ketuk layar >" if ANDROID else "Z / Spasi >", W - 210, 655, f_s, (200, 200, 200))


def draw_menu():
    h = 80 + 44 * len(menu['items']); panel((380, 200, 520, h))
    txt(menu['title'], 405, 215, f_m, (255, 220, 100))
    for i, (lbl, _) in enumerate(menu['items']):
        txt(("> " if i == menu['idx'] else "  ") + lbl, 410, 265 + i * 44, f_m, (255, 230, 120) if i == menu['idx'] else (230, 230, 230))


# ---------- simpan / muat ----------
def save(silent=False):
    try:
        with open(SAVE, 'w') as fh: json.dump({k: getattr(P, k) for k in SAVE_KEYS}, fh)
        if not silent: note("Game disimpan.")
    except Exception:
        if not silent: note("Gagal menyimpan.")


def loadgame():
    global scene, CUR
    if not os.path.exists(SAVE): note("Belum ada save."); return
    try:
        with open(SAVE) as fh: d = json.load(fh)
        for k, v in d.items():
            if k in SAVE_KEYS: setattr(P, k, v)
        P.opened = list(P.opened) if isinstance(P.opened, list) else []
        scene = None; CUR = None; P.status = 0
        note("Game dimuat.")
    except Exception: note("Save rusak, tidak bisa dimuat.")


def near_npc():
    for n in NPCS:
        if math.hypot(n['pos'][0] - P.x, n['pos'][1] - P.y) < 70: return n


def near_int():
    best, bd = None, 1e9
    for n in CUR['npcs']:
        d = math.hypot(n['pos'][0] - P.ix, n['pos'][1] - P.iy)
        if d < 46 and d < bd: best, bd = ('npc', n), d
    for ch in CUR['chests']:
        d = math.hypot(ch['pos'][0] - P.ix, ch['pos'][1] - P.iy)
        if d < 46 and d < bd: best, bd = ('chest', ch), d
    return best


# ---------- pengaturan ----------
ACTIONS = ['Simpan game', 'Muat game', 'Reset pengaturan', 'Kembali ke game']
NROWS = len(OPTS) + len(ACTIONS)
SY0, SRH = 100, 36
TJ = TK = TB = TM = None
joy_vec = [0.0, 0.0]
JC, JR = (170, 570), 100
BTN = {'A': (1140, 575, 62), 'B': (1010, 635, 48)}
SBTN = {'MENU': pygame.Rect(1160, 106, 100, 38)}
fingers = {}
touch_seen = False
K_BACK = getattr(pygame, 'K_AC_BACK', None)


def rebuild_touch():
    global TJ, TK, TB, TM
    m = [0.55, 1.0, 1.5][S['touch']]
    al = lambda v: int(min(255, v * m))
    TJ = pygame.Surface((JR * 2 + 8, JR * 2 + 8), pygame.SRCALPHA)
    pygame.draw.circle(TJ, (255, 255, 255, al(45)), (JR + 4, JR + 4), JR); pygame.draw.circle(TJ, (255, 255, 255, al(110)), (JR + 4, JR + 4), JR, 4)
    TK = pygame.Surface((90, 90), pygame.SRCALPHA); pygame.draw.circle(TK, (255, 230, 150, al(170)), (45, 45), 42)
    TB = pygame.Surface((248, 178), pygame.SRCALPHA)
    for nm, (bx, by, br) in BTN.items():
        c = (bx - 958, by - 509)
        pygame.draw.circle(TB, (255, 200, 80, al(120)) if nm == 'A' else (120, 200, 255, al(120)), c, br)
        pygame.draw.circle(TB, (255, 255, 255, al(170)), c, br, 4)
        t = f_l.render(nm, True, (255, 255, 255)); TB.blit(t, (c[0] - t.get_width() // 2, c[1] - t.get_height() // 2 - 6))
        l = f_s.render("Bicara/OK" if nm == 'A' else "Ramuan", True, (255, 255, 255)); TB.blit(l, (c[0] - l.get_width() // 2, c[1] + 14))
    r = SBTN['MENU']; TM = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
    pygame.draw.rect(TM, (20, 20, 40, al(170)), TM.get_rect(), border_radius=8); pygame.draw.rect(TM, (220, 190, 110, al(230)), TM.get_rect(), 2, border_radius=8)
    t = f_s.render("MENU", True, (255, 255, 255)); TM.blit(t, (r.w // 2 - t.get_width() // 2, r.h // 2 - t.get_height() // 2))


def apply_settings():
    rebuild_touch(); init_particles()


def change_opt(i, d):
    key, _, vals = OPTS[i]
    if key == 'preset':
        n = (S['preset'] + d) % 3 if S['preset'] < 3 else (0 if d > 0 else 2)
        S['preset'] = n; S.update(PRESETS[n])
    else:
        S[key] = (S[key] + d) % len(vals)
        if key in ('light', 'part', 'rays', 'fps'): S['preset'] = 3
    apply_settings(); save_settings()


def settings_action(a):
    global mode
    if a == 0: save()
    elif a == 1: loadgame()
    elif a == 2: S.update(DEF); apply_settings(); save_settings(); note("Pengaturan direset.")
    else: mode = 'explore'


def open_settings():
    global menu, mode, sidx
    menu = None; mode = 'settings'; sidx = 0


def quit_game(): pygame.quit(); sys.exit()


def open_pause():
    open_menu("Jeda", [("Pengaturan", open_settings), ("Simpan game", save), ("Muat game", loadgame)] + ([] if ANDROID else [("Keluar game", quit_game)]))


def draw_settings():
    screen.fill((10, 10, 22))
    panel((150, 30, 980, 666), 240)
    txt("Pengaturan", 190, 45, f_l, (255, 220, 100))
    for i in range(NROWS):
        y = SY0 + i * SRH; sel = i == sidx
        if sel: pygame.draw.rect(screen, (70, 60, 110), (170, y - 2, 940, SRH - 2), border_radius=8)
        col = (255, 230, 120) if sel else (230, 230, 230)
        if i < len(OPTS):
            key, label, vals = OPTS[i]
            txt(label, 200, y + 2, f_m, col)
            txt("<", 760, y + 2, f_m, col); vt = tr(vals[S[key]], f_m, col); screen.blit(vt, (900 - vt.get_width() // 2, y + 2)); txt(">", 1040, y + 2, f_m, col)
        else: txt(ACTIONS[i - len(OPTS)], 200, y + 2, f_m, col)
    txt("Ketuk < > untuk mengubah. Auto-kualitas menurunkan grafik jika game terasa berat." if ANDROID else "Atas/Bawah: pilih   Kiri/Kanan: ubah   Enter: OK   Esc: kembali", 190, 652, f_s, (200, 200, 200))


# ---------- input ----------
def handle_key(k):
    global mode, dialog, menu, debug, sidx
    if fade: return
    ok = k in (pygame.K_z, pygame.K_RETURN, pygame.K_SPACE)
    back = k == pygame.K_ESCAPE or (K_BACK is not None and k == K_BACK)
    if k == pygame.K_F1: debug = not debug
    if mode == 'explore':
        if ok:
            if scene:
                it = near_int()
                if it and it[0] == 'npc': talk(it[1], P.ix, P.iy)
                elif it: open_chest(it[1])
            else:
                n = near_npc()
                if n: talk(n)
                else:
                    dk = near_door()
                    if dk: enter_building(dk)
        elif k == pygame.K_p:
            if P.pot > 0 and P.hp < P.maxhp: P.pot -= 1; P.hp = min(P.maxhp, P.hp + 30); note("HP +30")
        elif k == pygame.K_F5: save()
        elif k == pygame.K_F9: loadgame()
        elif back: open_pause()
    elif mode == 'dialog' and ok:
        dialog['i'] += 1
        if dialog['i'] >= len(dialog['lines']):
            cb = dialog['cb']; dialog = None; mode = 'explore'
            if cb: cb()
    elif mode == 'menu':
        if k in (pygame.K_UP, pygame.K_w): menu['idx'] = (menu['idx'] - 1) % len(menu['items'])
        elif k in (pygame.K_DOWN, pygame.K_s): menu['idx'] = (menu['idx'] + 1) % len(menu['items'])
        elif back: menu = None; mode = 'explore'
        elif ok:
            fn = menu['items'][menu['idx']][1]
            if fn is None: menu = None; mode = 'explore'
            else: fn()
    elif mode == 'settings':
        if k in (pygame.K_UP, pygame.K_w): sidx = (sidx - 1) % NROWS
        elif k in (pygame.K_DOWN, pygame.K_s): sidx = (sidx + 1) % NROWS
        elif k in (pygame.K_LEFT, pygame.K_a) and sidx < len(OPTS): change_opt(sidx, -1)
        elif k in (pygame.K_RIGHT, pygame.K_d) and sidx < len(OPTS): change_opt(sidx, 1)
        elif back: mode = 'explore'
        elif ok:
            if sidx < len(OPTS): change_opt(sidx, 1)
            else: settings_action(sidx - len(OPTS))
    elif mode == 'battle' and battle['state'] == 'cmd':
        i = battle['idx']
        if k in (pygame.K_LEFT, pygame.K_a): battle['idx'] = i ^ 1
        elif k in (pygame.K_RIGHT, pygame.K_d): battle['idx'] = i ^ 1
        elif k in (pygame.K_UP, pygame.K_w, pygame.K_DOWN, pygame.K_s): battle['idx'] = (i + 2) % 4
        elif ok: player_act(i)


def to_logical(nx, ny):
    ww, wh = pygame.display.get_window_size(); sc = min(ww / W, wh / H)
    return (nx * ww - (ww - W * sc) / 2) / sc, (ny * wh - (wh - H * sc) / 2) / sc


def update_joy(x, y):
    dx, dy = x - JC[0], y - JC[1]; d = math.hypot(dx, dy)
    if d > JR: dx, dy = dx * JR / d, dy * JR / d
    joy_vec[0], joy_vec[1] = dx / JR, dy / JR


def press(fid, x, y):
    global sidx
    if fade: return
    if mode == 'explore':
        for nm, (bx, by, br) in BTN.items():
            if math.hypot(x - bx, y - by) <= br + 12:
                handle_key(pygame.K_z if nm == 'A' else pygame.K_p); return
        if SBTN['MENU'].collidepoint(x, y): handle_key(pygame.K_ESCAPE); return
        if x < 480 and y > 280: fingers[fid] = 'joy'; update_joy(x, y)
    elif mode == 'dialog': handle_key(pygame.K_z)
    elif mode == 'menu':
        for i in range(len(menu['items'])):
            if pygame.Rect(400, 258 + i * 44, 480, 42).collidepoint(x, y):
                menu['idx'] = i; handle_key(pygame.K_z); return
    elif mode == 'settings':
        i = int((y - SY0) // SRH)
        if 0 <= i < NROWS and 170 <= x <= 1110:
            sidx = i
            if i < len(OPTS): change_opt(i, -1 if 740 <= x < 830 else 1)
            else: settings_action(i - len(OPTS))
    elif mode == 'battle' and battle['state'] == 'cmd':
        for i in range(4):
            if pygame.Rect(790 + (i % 2) * 230, 552 + (i // 2) * 55, 225, 50).collidepoint(x, y):
                battle['idx'] = i; handle_key(pygame.K_z); return


def move(fid, x, y):
    if fingers.get(fid) == 'joy': update_joy(x, y)


def release(fid):
    if fingers.pop(fid, None) == 'joy': joy_vec[0] = joy_vec[1] = 0.0


def draw_touch():
    if not (ANDROID or touch_seen) or mode != 'explore': return
    screen.blit(TJ, (JC[0] - JR - 4, JC[1] - JR - 4))
    screen.blit(TK, (int(JC[0] + joy_vec[0] * JR) - 45, int(JC[1] + joy_vec[1] * JR) - 45))
    screen.blit(TB, (958, 509)); screen.blit(TM, SBTN['MENU'].topleft)


# ---------- auto-kualitas ----------
def degrade():
    if S['rays']: S['rays'] = 0; msg = "sinar matahari dimatikan"
    elif S['part']: S['part'] -= 1; msg = "partikel dikurangi"
    elif S['light'] > 1: S['light'] -= 1; msg = "pencahayaan diturunkan"
    else: return False
    S['preset'] = 3; apply_settings(); save_settings(); note("Auto-kualitas: " + msg); return True


# ---------- loop ----------
apply_settings(); update_light_state()
say("Narator", ["Selamat datang di Eldenvale, desa kecil di tepi hutan.", "Temui Sir Aldric di dekat gereja untuk memulai petualanganmu.",
                "Kamu bisa masuk ke rumah-rumah lewat pintunya. Malam hari hutan jadi lebih berbahaya!"])
frame = perf_sum = perf_n = 0
fps_txt = ""
while True:
    dt = clock.tick(FPS_VALUES[S['fps']])
    for e in pygame.event.get():
        if e.type == pygame.QUIT: pygame.quit(); sys.exit()
        elif e.type == pygame.KEYDOWN: handle_key(e.key)
        elif e.type == pygame.FINGERDOWN: touch_seen = True; press(e.finger_id, *to_logical(e.x, e.y))
        elif e.type == pygame.FINGERMOTION: move(e.finger_id, *to_logical(e.x, e.y))
        elif e.type == pygame.FINGERUP: release(e.finger_id)
        elif not ANDROID and e.type == pygame.MOUSEBUTTONDOWN and e.button == 1: press('m', *e.pos)
        elif not ANDROID and e.type == pygame.MOUSEMOTION and e.buttons[0]: move('m', *e.pos)
        elif not ANDROID and e.type == pygame.MOUSEBUTTONUP and e.button == 1: release('m')
    update_fade()
    if mode in ('explore', 'dialog', 'menu') and S['tod'] == 0: P.tod = (P.tod + dt / 1000 / 20) % 24
    update_light_state()

    if mode == 'explore' and not fade:
        kk = pygame.key.get_pressed()
        dx = (kk[pygame.K_RIGHT] or kk[pygame.K_d]) - (kk[pygame.K_LEFT] or kk[pygame.K_a])
        dy = (kk[pygame.K_DOWN] or kk[pygame.K_s]) - (kk[pygame.K_UP] or kk[pygame.K_w])
        if abs(joy_vec[0]) > 0.3: dx = 1 if joy_vec[0] > 0 else -1
        if abs(joy_vec[1]) > 0.3: dy = 1 if joy_vec[1] > 0 else -1
        if dx or dy:
            diag = 0.7071 if dx and dy else 1
            if scene:
                sp = 150 * min(dt, 50) / 1000 * diag
                nx, ny = P.ix + dx * sp, P.iy + dy * sp
                if not iblocked(nx, P.iy): P.ix = nx
                if not iblocked(P.ix, ny): P.iy = ny
            else:
                sp = 275 * min(dt, 50) / 1000 * diag
                nx, ny = P.x + dx * sp, P.y + dy * sp
                if not blocked(nx, P.y): P.x = nx
                if not blocked(P.x, ny): P.y = ny
            if abs(dx) >= abs(dy) and dx: P.d, P.flip = 'side', dx < 0
            elif dy: P.d, P.flip = ('down' if dy > 0 else 'up'), False
            walk_t += dt; P.step = int(walk_t // 105); P.dist += sp; P.moving = True
            if scene:
                if dy > 0 and ifeet(P.ix, P.iy).colliderect(CUR['exit']): leave_building()
            else:
                r = feet(P.x, P.y)
                if dy < 0:
                    dk = near_door()
                    if dk: enter_building(dk)
                zt = None
                for zr, tier in ZONES:
                    if r.colliderect(zr): zt = tier; break
                if zt is not None and P.dist > random.randint(260, 520):
                    P.dist = 0; start_battle(zt)
        else: P.step = 0; P.moving = False
        if scene:
            for n in CUR['npcs']:
                if math.hypot(n['pos'][0] - P.ix, n['pos'][1] - P.iy) < 90: face(n, P.ix, P.iy)
                else: n['d'], n['flip'] = 'down', False
    elif mode == 'battle': update_battle()
    if mode != 'explore': P.moving = False
    if not scene: update_npcs(dt)
    if PART and S['light'] and not scene: update_particles(dt)

    if mode == 'battle': draw_battle()
    elif mode == 'settings': draw_settings()
    else:
        if scene: draw_interior()
        else: draw_world()
        if mode == 'dialog': draw_dialog()
        if mode == 'menu': draw_menu()
        draw_touch()
    draw_fade()
    frame += 1
    if S['showfps']:
        if frame % 15 == 0: fps_txt = f"{clock.get_fps():.0f} FPS"
        txt(fps_txt, W // 2 - 30, H - 34, f_s, (140, 255, 140))
    # auto-turunkan kualitas bila fps jauh di bawah target (abaikan 5 detik pertama & saat transisi)
    if frame > 240 and mode in ('explore', 'dialog') and not fade:
        perf_sum += dt; perf_n += 1
        if perf_n >= 150:
            if S['auto'] and perf_sum / perf_n > (1000 / FPS_VALUES[S['fps']]) * 1.45: degrade()
            perf_sum = perf_n = 0
    pygame.display.flip()
