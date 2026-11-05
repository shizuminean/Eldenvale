# -*- coding: utf-8 -*-
"""Eldenvale RPG - Python + pygame (PC & Android)."""
import pygame, sys, os, random, json, math
from data import *

BASE = os.path.dirname(os.path.abspath(__file__))
A = lambda *p: os.path.join(BASE, 'assets', *p)
SAVE = os.path.join(BASE, 'save.json')
SETF = os.path.join(BASE, 'settings.json')
W, H = 1280, 720
ANDROID = 'ANDROID_ARGUMENT' in os.environ

# ---------------- setelan ----------------
S = {'fps': 60, 'show_fps': False, 'shadows': True, 'names': True, 'wander': True, 'shake': True,
     'touch': 'auto', 'tsize': 1, 'talpha': 1, 'speed': 1}
try: S.update(json.load(open(SETF)))
except Exception: pass


def save_settings():
    try: json.dump(S, open(SETF, 'w'))
    except Exception: pass


pygame.init()
_fl = (pygame.FULLSCREEN if ANDROID else pygame.RESIZABLE) | pygame.SCALED
try: screen = pygame.display.set_mode((W, H), _fl, vsync=1)
except Exception: screen = pygame.display.set_mode((W, H), _fl)
pygame.display.set_caption("Eldenvale RPG")
clock = pygame.time.Clock()


def F(s, b=False):
    try: return pygame.font.SysFont("arial,dejavusans,freesans", s, bold=b)
    except Exception: return pygame.font.Font(None, int(s * 1.25))


f_xs, f_14, f_s, f_m, f_l = F(13, True), F(14), F(18), F(22), F(34, True)

# ---------------- cache (kunci anti-lag) ----------------
_TC, _PC, _IC, _MC = {}, {}, {}, {}


def rt(t, font, col):
    k = (t, id(font), col); s = _TC.get(k)
    if s is None:
        if len(_TC) > 900: _TC.clear()
        s = _TC[k] = font.render(t, True, col)
    return s


def txt(t, x, y, font=f_m, col=(255, 255, 255)):
    screen.blit(rt(t, font, (0, 0, 0)), (x + 2, y + 2)); screen.blit(rt(t, font, col), (x, y))


def panel(r, a=225):
    k = (r[2], r[3], a); s = _PC.get(k)
    if s is None:
        s = pygame.Surface((r[2], r[3]), pygame.SRCALPHA)
        pygame.draw.rect(s, (18, 18, 38, a), s.get_rect(), border_radius=12)
        pygame.draw.rect(s, (220, 190, 110), s.get_rect(), 3, border_radius=12); _PC[k] = s
    screen.blit(s, (r[0], r[1]))


def wrap(t, font, w):
    out, cur = [], ""
    for wd in t.split(" "):
        if font.size(cur + wd)[0] > w: out.append(cur); cur = wd + " "
        else: cur += wd + " "
    return out + [cur]


def load(name, h=None, scale=None):
    img = pygame.image.load(A(name)).convert_alpha()
    if scale: size = (max(1, int(img.get_width() * scale)), max(1, int(img.get_height() * scale)))
    else: size = (max(1, int(img.get_width() * h / img.get_height())), h)
    return pygame.transform.smoothscale(img, size)


def icon(iid, size):
    k = (iid, size); s = _IC.get(k)
    if s is None:
        img = pygame.image.load(A('items', f"it_{ITEMS[iid]['icon']}.png")).convert_alpha()
        sc = size / max(img.get_size()); s = _IC[k] = pygame.transform.smoothscale(img, (max(1, int(img.get_width() * sc)), max(1, int(img.get_height() * sc))))
    return s


def mon_img(m):
    s = _MC.get(m['img'])
    if s is None:
        img = pygame.image.load(A('mon', f"m_{m['img']}.png")).convert_alpha()
        sc = m['size'] / img.get_height(); s = _MC[m['img']] = pygame.transform.smoothscale(img, (int(img.get_width() * sc), m['size']))
    return s


MAP = pygame.image.load(A('map.png')).convert()
MW, MH = MAP.get_size()
HMAP = pygame.image.load(A('hunt.png')).convert()
HW, HH = HMAP.get_size()
_hm = pygame.image.load(A('hunt_mask.png')); HGW, HGH = _hm.get_size()
HGRID = [[_hm.get_at((i, j))[0] > 128 for i in range(HGW)] for j in range(HGH)]
SHADOW = pygame.Surface((40, 16), pygame.SRCALPHA)
pygame.draw.ellipse(SHADOW, (0, 0, 0, 90), SHADOW.get_rect())


class Sheet:
    def __init__(self, who, h=66, scale=None):
        self.f, self.ff, self.idle, self.idlef = {}, {}, {}, {}
        for d in ('down', 'side', 'up'):
            fr, i = [], 0
            while os.path.exists(A(f'{who}_{d}_{i}.png')):
                fr.append(load(f'{who}_{d}_{i}.png', h, scale)); i += 1
            if len(fr) == 1: fr.append(fr[0])
            self.f[d] = fr; self.ff[d] = [pygame.transform.flip(x, True, False) for x in fr]
            p = f'{who}_idle_{d}.png'
            self.idle[d] = load(p, h, scale) if os.path.exists(A(p)) else fr[0]
            self.idlef[d] = pygame.transform.flip(self.idle[d], True, False)

    def get(self, d, step, flip=False, moving=True):
        if not moving: return (self.idlef if flip else self.idle)[d]
        fr = (self.ff if flip else self.f)[d]
        return fr[int(step) % len(fr)]


HS = 76 / pygame.image.load(A('hero_idle_down.png')).get_height()
hero = Sheet('hero', scale=HS)
BAT_IDLE = load('hero_battle_idle.png', scale=HS * 3)
BAT_ATK = load('hero_battle_atk.png', scale=HS * 3)
SHEETS = {}


def sheet_for(who):
    if who not in SHEETS: SHEETS[who] = Sheet(who, 70)
    return SHEETS[who]

# ---------------- dunia luar ----------------
BLOCK = [pygame.Rect(*r) for r in [
    (0, 0, MW, 50), (0, 0, 60, MH), (1470, 320, 300, 700), (1570, 0, 120, MH),
    (0, 0, 380, 245), (1340, 0, 100, 330), (1440, 0, 150, 270),
    (0, 790, 800, 200), (930, 830, 742, 111), (0, 920, MW, 30),
    (470, 115, 260, 150), (785, 50, 225, 210), (1075, 175, 185, 135), (390, 300, 175, 175),
    (1170, 360, 160, 125), (365, 480, 110, 150), (340, 585, 470, 85), (830, 355, 120, 100),
    (1040, 612, 345, 100), (1400, 330, 70, 215)]]
WILD = [(pygame.Rect(*r), z) for r, z in [((60, 590, 260, 120), 'near'), ((900, 720, 520, 95), 'near'), ((330, 700, 470, 90), 'near'),
                                           ((1400, 560, 70, 150), 'near'), ((805, 790, 125, 125), 'far')]]
DOORR = {k: pygame.Rect(*v['trig']) for k, v in DOORS.items()}
DOOR_NAME = {'inn': 'Penginapan', 'church': 'Gereja', 'potion': 'Toko Ramuan', 'smith': 'Pandai Besi', 'green': 'Rumah Nenek Wren'}

GATE, GATE_OUT = pygame.Rect(820, 890, 100, 24), (870, 850)
HEXIT, HENTRY = pygame.Rect(660, 892, 52, 24), (696, 830)
NPCS = [
    dict(name="Sir Aldric", who="n05", pos=(800, 330), kind="quest", r=40, still=True),
    dict(name="Mira", who="n27", pos=(700, 565), kind="girl", r=150),
    dict(name="Cale si Pedagang", who="n29", pos=(1010, 470), kind="chat", r=110,
         lines=["Barang dagangan terbaik ada di toko Orn dan Brom!", "Monster di Hutan Berburu menjatuhkan bahan yang laku mahal."]),
    dict(name="Anya", who="n19", pos=(560, 545), kind="chat", r=90,
         lines=["Aku pernah masuk gereja. Di dalamnya megah sekali!", "Ssst, kata orang ada Raja Slime di rumput luar desa."]),
    dict(name="Fenn si Pemanah", who="n14", pos=(1120, 520), kind="archer", r=130),
    dict(name="Kesatria Ines", who="n18", pos=(1000, 330), kind="chat", r=100,
         lines=["Aku berpatroli di sini setiap hari.", "Monster di Hutan Berburu bisa dilihat dari jauh. Hindari yang terlalu kuat!"]),
    dict(name="Madam Ruby", who="n11", pos=(900, 520), kind="chat", r=90,
         lines=["Aku meramal... kau akan segera naik level!", "Vampir penjaga gua di hutan itu sangat berbahaya."]),
    dict(name="Penyihir Selene", who="n26", pos=(700, 450), kind="chat", r=80,
         lines=["Esensi dari slime bagus untuk ramuan.", "Kumpulkan bahan, lalu jual ke Orn."]),
    dict(name="Kakek Odo", who="n03", pos=(1030, 560), kind="chat", r=0, still=True,
         lines=["Dulu aku berburu di hutan selatan. Sekarang cukup duduk di sini.", "Naga kecil penghuni hutan menjatuhkan Pedang Darah, konon."]),
    dict(name="Penjaga Gerbang", who="n08", pos=(812, 855), kind="chat", r=0, still=True,
         lines=["Gerbang selatan menuju Hutan Berburu.", "Monster di sana terlihat dan akan mengejarmu. Bawa ramuan!"]),
    dict(name="Putri Elara", who="n28", pos=(790, 420), kind="chat", r=0, still=True,
         lines=["Air mancur ini kesukaanku.", "Pahlawan sepertimu selalu disambut di Eldenvale."]),
]
HNPCS = [dict(name="Pemburu Rhea", who="n15", pos=(1345, 415), kind="camp", r=0, still=True)]
area = 'town'


def anpcs(): return NPCS if area == 'town' else HNPCS


def init_npc(n):
    n.update(pos=list(n['pos']), home=tuple(n['pos']), d='down', flip=False, anim=0, moving=False, tgt=None,
             wait=pygame.time.get_ticks() + random.randint(500, 3500), spd=random.uniform(34, 52))


for _n in NPCS + HNPCS: init_npc(_n)


class P:
    x, y = 880.0, 560.0
    ix, iy = 0.0, 0.0
    d, step, flip, dist, moving = 'down', 0, False, 0.0, False
    lv, xp, gold = 1, 0, 60
    hp = maxhp = 60
    mp = maxmp = 20
    atk, df = 9, 3
    wl = 0
    slimes = 0
    quest = 0
    bag = [['potion_hp', 3], ['potion_mp', 1], ['bread', 2], ['dagger', 1]]
    eq = {s: None for s in SLOT_NAME}


P.eq['weapon'] = 'sword_iron'
MAXBAG = 30


def need(lv): return 20 + lv * lv * 8
def feet(x, y): return pygame.Rect(int(x) - 12, int(y) - 12, 24, 14)
def eqsum(k): return sum(ITEMS[i].get(k, 0) for i in P.eq.values() if i)
def tatk(): return P.atk + eqsum('atk')
def tdef(): return P.df + eqsum('df')


# ---------------- tas ----------------
def count(i): return sum(c for k, c in P.bag if k == i)


def add_item(i, n=1):
    ok = True
    for _ in range(n):
        if ITEMS[i]['type'] in ('use', 'mat', 'misc'):
            sl = next((s for s in P.bag if s[0] == i and s[1] < 99), None)
            if sl: sl[1] += 1; continue
        if len(P.bag) >= MAXBAG: ok = False; break
        P.bag.append([i, 1])
    return ok


def remove_item(i, n=1):
    for s in P.bag:
        if s[0] == i:
            s[1] -= n
            if s[1] <= 0: P.bag.remove(s)
            return True
    return False


def use_item(i):
    it = ITEMS[i]; hp, mp = it.get('hp', 0), it.get('mp', 0)
    if not ((hp and P.hp < P.maxhp) or (mp and P.mp < P.maxmp)): return False
    P.hp = min(P.maxhp, P.hp + hp); P.mp = min(P.maxmp, P.mp + mp); remove_item(i); return True


def equip(i):
    slot = SLOT_OF[ITEMS[i]['type']]; old = P.eq[slot]
    remove_item(i); P.eq[slot] = i
    if old: add_item(old)
    return slot


def unequip(slot):
    i = P.eq[slot]
    if i and add_item(i): P.eq[slot] = None; return True
    return False


def quick_heal():
    for s in P.bag:
        it = ITEMS[s[0]]
        if it['type'] == 'use' and it.get('hp') and P.hp < P.maxhp:
            use_item(s[0]); note(f"Memakai {it['name']}"); return
    note("Tidak ada item pemulih HP." if P.hp < P.maxhp else "HP sudah penuh.")


# ---------------- state umum ----------------
mode = 'explore'
loc = None       # None = luar, selain itu id interior
cur = None
dialog = menu = battle = None
toast = ("", 0)
debug = False
walk_t = 0
door_lock = 0
touch_seen = False
inv = dict(tab=0, sel=-1, slot=None, snap=None)


def note(t):
    global toast; toast = (t, pygame.time.get_ticks() + 2300)


def say(name, lines, cb=None):
    global dialog, mode
    dialog = dict(name=name, lines=lines if isinstance(lines, list) else [lines], i=0, cb=cb); mode = 'dialog'


def open_menu(title, items):
    global menu, mode
    menu = dict(title=title, items=items + [("Tutup", None, None)], idx=0); mode = 'menu'


def heal_full(): P.hp, P.mp = P.maxhp, P.maxmp


def gain(xp, gold):
    P.xp += xp; P.gold += gold; msgs = []
    while P.xp >= need(P.lv):
        P.xp -= need(P.lv); P.lv += 1
        P.maxhp += 12; P.maxmp += 4; P.atk += 3; P.df += 1
        heal_full(); msgs.append(f"LEVEL UP! Lv {P.lv}")
    return msgs


# ---------------- collision & NPC luar ----------------
def hunt_ok(r):
    for px, py in (r.topleft, (r.right - 1, r.top), (r.left, r.bottom - 1), (r.right - 1, r.bottom - 1)):
        i, j = px // 16, py // 16
        if not (0 <= i < HGW and 0 <= j < HGH and HGRID[j][i]): return False
    return True


def blocked(x, y, skip=None):
    r = feet(x, y)
    if area == 'town':
        if any(r.colliderect(b) for b in BLOCK): return True
    elif not hunt_ok(r): return True
    for n in anpcs():
        if n is not skip and r.colliderect(feet(*n['pos']).inflate(10, 6)): return True
    if skip is not None and r.colliderect(feet(P.x, P.y).inflate(14, 8)): return True
    return False


def face(n, tx, ty):
    dx, dy = tx - n['pos'][0], ty - n['pos'][1]
    if abs(dx) > abs(dy): n['d'], n['flip'] = 'side', dx < 0
    else: n['d'], n['flip'] = ('down' if dy > 0 else 'up'), False


def update_npcs(dt):
    t = pygame.time.get_ticks()
    for n in anpcs():
        x, y = n['pos']; near = math.hypot(x - P.x, y - P.y) < 85
        if mode != 'explore' or near or not S['wander'] or n.get('still'):
            n['moving'] = False; n['tgt'] = None
            if mode == 'explore' and near: face(n, P.x, P.y)
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
        if dist < 4: n['tgt'] = None; n['moving'] = False; n['wait'] = t + random.randint(1500, 5000); continue
        sp = n['spd'] * min(dt, 50) / 1000
        nx, ny = x + dx / dist * sp, y + dy / dist * sp; moved = False
        if not blocked(nx, y, n): n['pos'][0] = nx; moved = True
        if not blocked(n['pos'][0], ny, n): n['pos'][1] = ny; moved = True
        if not moved: n['tgt'] = None; n['wait'] = t + 600; n['moving'] = False; continue
        if abs(dx) > abs(dy): n['d'], n['flip'] = 'side', dx < 0
        else: n['d'], n['flip'] = ('down' if dy > 0 else 'up'), False
        n['moving'] = True; n['anim'] += dt


# ---------------- monster berburu (terlihat di peta) ----------------
MBY = {m['name']: m for m in MONSTERS}
REC = {1: ('Lv 1+', (150, 255, 150)), 2: ('Lv 4+', (255, 235, 120)), 3: ('Lv 7+', (255, 170, 80)), 9: ('BOSS', (255, 90, 90))}
HM = []
for _nm, _x, _y, _r in HUNT_SPAWNS:
    _m = MBY[_nm]; _h = 110 if _m['tier'] == 9 else max(36, min(100, int(_m['size'] * 0.36)))
    HM.append(dict(m=_m, home=(_x, _y), pos=[float(_x), float(_y)], r=_r, h=_h, alive=True, respawn=0, imm=0, flip=False, tgt=None,
                   wait=0, anim=random.randint(0, 3000), spd={1: 40, 2: 55, 3: 70, 9: 45}[_m['tier']], chase=False))
_HC = {}


def hm_img(e):
    k = (e['m']['img'], e['h'], e['flip']); im = _HC.get(k)
    if im is None:
        base = pygame.image.load(A('mon', f"m_{e['m']['img']}.png")).convert_alpha()
        sc = e['h'] / base.get_height(); im = pygame.transform.smoothscale(base, (max(1, int(base.get_width() * sc)), e['h']))
        if e['flip']: im = pygame.transform.flip(im, True, False)
        _HC[k] = im
    return im


def hm_ok(x, y):
    r = pygame.Rect(int(x) - 6, int(y) - 3, 12, 6); return hunt_ok(r)


def update_hunt(dt):
    t = pygame.time.get_ticks()
    for e in HM:
        if not e['alive']:
            if t >= e['respawn']: e['alive'] = True; e['pos'] = [float(e['home'][0]), float(e['home'][1])]; e['imm'] = t + 2000
            continue
        if mode != 'explore' or loc is not None: continue
        x, y = e['pos']; dx, dy = P.x - x, P.y - y; dist = math.hypot(dx, dy)
        aggro = dist < (110 if e['m']['tier'] == 9 else 190) and t > e['imm']
        e['chase'] = aggro; e['anim'] += dt
        if aggro:
            sp = e['spd'] * 1.3 * min(dt, 50) / 1000; nx, ny = x + dx / dist * sp, y + dy / dist * sp
            if hm_ok(nx, y): e['pos'][0] = nx
            if hm_ok(e['pos'][0], ny): e['pos'][1] = ny
            e['flip'] = dx > 0
            if dist < 34: start_battle(ent=e); return
            continue
        if e['tgt'] is None:
            if t < e['wait']: continue
            hx, hy = e['home']; r = e['r']; tx, ty = hx + random.uniform(-r, r), hy + random.uniform(-r, r)
            if hm_ok(tx, ty): e['tgt'] = (tx, ty)
            else: e['wait'] = t + 300
            continue
        tx, ty = e['tgt']; ddx, ddy = tx - x, ty - y; dd = math.hypot(ddx, ddy)
        if dd < 4: e['tgt'] = None; e['wait'] = t + random.randint(1200, 4000); continue
        sp = e['spd'] * 0.6 * min(dt, 50) / 1000; nx, ny = x + ddx / dd * sp, y + ddy / dd * sp
        if hm_ok(nx, ny): e['pos'] = [nx, ny]; e['flip'] = ddx > 0
        else: e['tgt'] = None; e['wait'] = t + 500


def enter_area(a, pos):
    global area, door_lock
    area = a; P.x, P.y = float(pos[0]), float(pos[1]); door_lock = pygame.time.get_ticks() + 900; reset_touch()
    if a == 'hunt':
        for e in HM: e['imm'] = pygame.time.get_ticks() + 1500
    note("Hutan Berburu - monster terlihat di peta, hindari yang terlalu kuat!" if a == 'hunt' else "Kembali ke Eldenvale")


# ---------------- interior ----------------
INT_CACHE = {}


def build_interior(iid):
    if iid in INT_CACHE: return INT_CACHE[iid]
    d = INTERIORS[iid]; x0, y0 = d['crop'][0], d['crop'][1]
    img = pygame.image.load(A('int', iid + '.png')).convert()
    s = min(1180 / img.get_width(), 700 / img.get_height(), 2.2)
    surf = pygame.transform.smoothscale(img, (int(img.get_width() * s), int(img.get_height() * s)))
    k = s * 0.7; sub = lambda r: pygame.Rect(r[0] - x0, r[1] - y0, r[2], r[3])
    nm, who, kind, pos = d['npc']
    npc = dict(name=nm, who=who, kind=kind, pos=[pos[0] - x0, pos[1] - y0], d='down', flip=False, moving=False, anim=0)
    c = dict(id=iid, s=s, surf=surf, ox=(W - surf.get_width()) // 2, oy=(H - surf.get_height()) // 2, floor=[sub(r) for r in d['floor']],
             solid=[sub(r) for r in d['solid']], exit=sub(d['exit']), spawn=(d['spawn'][0] - x0, d['spawn'][1] - y0),
             hs=Sheet('hero', scale=HS * k), sh={who: Sheet(who, h=int(70 * k))}, npcs=[npc], k=k)
    INT_CACHE[iid] = c; return c


def ifeet(x, y): return pygame.Rect(int(x) - 9, int(y) - 5, 18, 7)


def int_ok(x, y):
    r = ifeet(x, y)
    for p in (r.topleft, r.topright, (r.left, r.bottom - 1), (r.right - 1, r.bottom - 1)):
        if not any(f.collidepoint(p) for f in cur['floor']): return False
    if any(r.colliderect(s) for s in cur['solid']): return False
    return not any(r.colliderect(ifeet(*n['pos']).inflate(14, 8)) for n in cur['npcs'])


def enter(iid):
    global loc, cur, door_lock
    cur = build_interior(iid); loc = iid
    P.ix, P.iy = cur['spawn']; P.d, P.flip = 'up', False
    P.x, P.y = DOORS[iid]['out']; door_lock = pygame.time.get_ticks() + 700
    note("Masuk: " + DOOR_NAME[iid])


def leave():
    global loc, cur, door_lock
    P.x, P.y = DOORS[loc]['out']; loc = None; cur = None; P.d = 'down'; door_lock = pygame.time.get_ticks() + 700


# ---------------- NPC logika ----------------
def open_shop(title, stock, extra=()):
    items = []
    for iid, price in stock:
        def buy(iid=iid, price=price):
            if P.gold < price: note("Emas tidak cukup."); return
            if not add_item(iid): note("Tas penuh!"); return
            P.gold -= price; note(f"Membeli {ITEMS[iid]['name']}")
        items.append((f"{ITEMS[iid]['name']} - {price} G", buy, iid))
    open_menu(title, items + list(extra))


def talk(n):
    global mode
    px, py = (P.x, P.y) if loc is None else (P.ix, P.iy)
    face(n, px, py); k, nm = n['kind'], n['name']
    if k == 'quest':
        if P.quest == 0:
            say(nm, ["Selamat datang di Eldenvale, pengelana.", "Slime di rumput luar desa makin banyak dan mengganggu ladang.",
                     "Kalahkan 5 slime di rumput selatan atau timur. Hadiahnya 120 emas!"], lambda: setattr(P, 'quest', 1))
        elif P.quest == 1:
            if P.slimes >= 5:
                P.quest = 2; say(nm, ["Kau berhasil! Desa ini berutang budi padamu.", "Ini hadiahmu: 120 emas, 40 XP, dan sebuah Elixir."],
                                 lambda: ([note(m) for m in gain(40, 120)], add_item('elixir'), setattr(P, 'quest', 3)))
            else: say(nm, [f"Slime terkalahkan: {P.slimes}/5. Cari di rumput luar desa."])
        else: say(nm, ["Terima kasih sudah menjaga desa. Hati-hati dengan Raja Slime dan monster di jalan selatan."])
    elif k == 'priest':
        say(nm, ["Cahaya melindungimu. Biarkan aku menyembuhkan lukamu."], lambda: (heal_full(), note("HP & MP pulih penuh!")))
    elif k == 'inn':
        def rest():
            global mode
            if P.gold >= 10: P.gold -= 10; heal_full(); note("Istirahat nyenyak. HP & MP pulih (-10 G)")
            else: note("Emas tidak cukup.")
        say(nm, ["Penginapan Eldenvale! Menginap hanya 10 emas."], lambda: open_menu("Menginap 10 emas?", [("Ya, menginap", rest, None)]))
    elif k in ('shop', 'camp'):
        def sell_all():
            tot = sum(ITEMS[i]['val'] * c for i, c in P.bag if ITEMS[i]['type'] == 'mat')
            if tot <= 0: note("Tidak ada bahan untuk dijual."); return
            P.bag[:] = [s for s in P.bag if ITEMS[s[0]]['type'] != 'mat']; P.gold += tot; note(f"Menjual bahan: +{tot} G")
        tot = sum(ITEMS[i]['val'] * c for i, c in P.bag if ITEMS[i]['type'] == 'mat')
        say(nm, ["Ramuan segar, langsung dari kuali! Aku juga membeli bahan monster." if k == 'shop' else "Kemah pemburu! Beli ramuan di sini, dan jual bahan hasil buruanmu."],
            lambda: open_shop("Toko Kemah" if k == 'camp' else "Toko Ramuan", SHOP_ORN, [(f"Jual semua bahan (+{tot} G)", sell_all, None)]))
    elif k == 'smith':
        def up():
            c = 50 * (P.wl + 1)
            if P.gold < c: note("Emas tidak cukup."); return
            P.gold -= c; P.wl += 1; P.atk += 3; note(f"Senjata ditempa +{P.wl}! ATK +3")
        say(nm, ["Besi yang baik butuh api yang panas!"],
            lambda: open_shop("Pandai Besi", SHOP_BROM, [(f"Tempa senjata ({50*(P.wl+1)} G, ATK +3)", up, None)]))
    elif k == 'archer':
        say(nm, ["Rumput selatan dan timur sering didatangi monster kecil.", "Lewati gerbang selatan untuk ke Hutan Berburu. Monster di sana terlihat, tapi ada Vampir penjaga gua. Bawa ramuan!"])
    elif k == 'granny':
        say(nm, random.choice([["Selamat datang, nak. Mau teh hangat?", "Dulu desa ini jauh lebih sepi."],
                               ["Monster paling kuat menjatuhkan Orb Ungu. Harganya mahal sekali!"]]))
    elif k == 'chat': say(nm, n['lines'])
    else: say(nm, ["Ada kincir angin dan ladang di sana. Kata kakek, sungai itu berasal dari air terjun ajaib."])


def interact():
    if loc is None:
        for n in anpcs():
            if math.hypot(n['pos'][0] - P.x, n['pos'][1] - P.y) < 70: talk(n); return
    else:
        for n in cur['npcs']:
            if math.hypot(n['pos'][0] - P.ix, n['pos'][1] - P.iy) < 80: talk(n); return


# ---------------- battle ----------------
MBY = {m['name']: m for m in MONSTERS}


def pick_monster(zone):
    r = random.random(); lv = P.lv
    if zone == 'near':
        if lv >= 3 and r < 0.03: return MBY[BOSS_NEAR]
        t = 2 if (lv >= 4 and r < 0.35) else 1
    else:
        if lv >= 6 and r < 0.03: return MBY[BOSS_FAR]
        t = 3 if (lv >= 6 and r < 0.45) else 2
    return random.choice([m for m in MONSTERS if m['tier'] == t])


def start_battle(zone='near', ent=None):
    global battle, mode
    m = ent['m'] if ent else pick_monster(zone); s = 1 + (P.lv - 1) * (0.08 if m['tier'] == 9 else 0.15)
    snap = screen.copy(); snap.fill((70, 70, 90), special_flags=pygame.BLEND_RGB_SUB); reset_touch()
    battle = dict(m=m, ent=ent, name=m['name'], hp=int(m['hp'] * s), maxhp=int(m['hp'] * s), atk=int(m['atk'] * s), xp=int(m['xp'] * s),
                  gold=int(m['gold'] * s), snap=snap, state='cmd', idx=0, log=f"{m['name']} muncul!", t=0, shake=0, flash=0,
                  atk_until=0, items=[], iidx=0)
    mode = 'battle'


def blog(t, state, delay=700):
    battle['log'] = t; battle['state'] = state; battle['t'] = pygame.time.get_ticks() + delay


def battle_items(): return [s[0] for s in P.bag if ITEMS[s[0]]['type'] == 'use'][:7]


def player_act(i):
    b = battle; now = pygame.time.get_ticks()
    if i == 0:
        d = max(1, tatk() + random.randint(-2, 3)); b['hp'] -= d; b['shake'] = 12; b['atk_until'] = now + 650
        blog(f"Kamu menyerang! {d} damage.", 'after')
    elif i == 1:
        if P.mp < 5: blog("MP tidak cukup!", 'cmd', 500); return
        P.mp -= 5; d = int(tatk() * 2 + random.randint(0, 4)); b['hp'] -= d; b['shake'] = 18; b['atk_until'] = now + 650
        blog(f"Tebasan Merah! {d} damage.", 'after')
    elif i == 2:
        b['items'] = battle_items()
        if not b['items']: blog("Tidak punya item!", 'cmd', 500)
        else: b['state'] = 'item'; b['iidx'] = 0
    elif i == 3:
        if random.random() < (0.3 if b['m']['tier'] == 9 else 0.6): blog("Berhasil kabur!", 'end_run', 800)
        else: blog("Gagal kabur!", 'enemy')


def battle_use(iid):
    if use_item(iid): blog(f"Memakai {ITEMS[iid]['name']}.", 'enemy')
    else: blog("HP/MP sudah penuh!", 'cmd', 500)


def update_battle():
    global mode, battle
    b = battle
    if b['shake'] > 0: b['shake'] -= 1
    if b['flash'] > 0: b['flash'] -= 1
    if pygame.time.get_ticks() < b['t']: return
    s = b['state']
    if s == 'after':
        if b['hp'] <= 0:
            if 'Slime' in b['name'] and P.quest == 1: P.slimes += 1
            msgs = gain(b['xp'], b['gold']); got = []
            for iid, ch in b['m']['drops']:
                if random.random() < ch:
                    if add_item(iid): got.append(ITEMS[iid]['name'])
                    else: got.append("(tas penuh)")
            txt_ = f"{b['name']} kalah! +{b['xp']} XP, +{b['gold']} G. " + " ".join(msgs)
            if got: txt_ += " Dapat: " + ", ".join(got)
            blog(txt_, 'end_win', 2400)
        else: b['state'] = 'enemy'
    elif s == 'enemy':
        d = max(1, b['atk'] - tdef() + random.randint(-1, 2)); P.hp -= d; b['flash'] = 10
        if P.hp <= 0: P.hp = 0; blog(f"{b['name']} menyerang {d}! Kamu tumbang...", 'end_lose', 1500)
        else: blog(f"{b['name']} menyerang! {d} damage.", 'cmd', 600)
    elif s in ('end_win', 'end_run'):
        e = b.get('ent'); t0 = pygame.time.get_ticks()
        if e:
            if s == 'end_win': e['alive'] = False; e['respawn'] = t0 + (120000 if e['m']['tier'] == 9 else 25000)
            else: e['imm'] = t0 + 4000
        mode = 'explore'; battle = None
    elif s == 'end_lose':
        P.gold //= 2; P.hp, P.mp = P.maxhp // 2, P.maxmp // 2
        for e in HM: e['pos'] = [float(e['home'][0]), float(e['home'][1])]; e['imm'] = pygame.time.get_ticks() + 3000
        mode = 'explore'; battle = None; enter_area('town', (880, 560)); note("Kamu pingsan & terbangun di alun-alun (emas -50%)")


def bar(x, y, w, v, m, col, h=14):
    pygame.draw.rect(screen, (30, 30, 40), (x, y, w, h), border_radius=5)
    pygame.draw.rect(screen, col, (x, y, int(w * max(0, v) / max(1, m)), h), border_radius=5)


def draw_battle():
    b = battle; t = pygame.time.get_ticks(); sh = S['shake']
    screen.blit(b['snap'], (0, 0))
    atk = t < b['atk_until']; pim = BAT_ATK if atk else BAT_IDLE
    ox = random.randint(-6, 6) if (b['flash'] and sh) else 0
    if atk:
        p = 1 - (b['atk_until'] - t) / 650; ox += int(math.sin(math.pi * p) * 520)
        if 0.3 < p < 0.75:
            ex = 900 + (random.randint(-6, 6) if sh else 0)
            for a, wd in ((0, 8), (24, 5)): pygame.draw.line(screen, (255, 255, 255), (ex - 90 + a, 250), (ex + 70 + a, 430), wd)
            pygame.draw.line(screen, (255, 230, 120), (ex - 70, 240), (ex + 90, 410), 4)
    screen.blit(pim, (170 + ox, 510 - pim.get_height() + (0 if atk else int(math.sin(t / 280) * 4))))
    if b['hp'] > 0 or b['state'] == 'after':
        im = mon_img(b['m']); sx = random.randint(-8, 8) if (b['shake'] and sh) else 0
        screen.blit(im, (900 + sx - im.get_width() // 2, 440 - im.get_height() + int(math.sin(t / 250) * 6)))
    txt(b['name'], 760, 80, f_l); bar(760, 130, 280, b['hp'], b['maxhp'], (220, 60, 60))
    panel((30, 30, 330, 100)); txt(f"Lv {P.lv}  HP {P.hp}/{P.maxhp}", 50, 40); bar(50, 75, 280, P.hp, P.maxhp, (80, 210, 90))
    txt(f"MP {P.mp}/{P.maxmp}", 50, 95, f_s)
    panel((20, 520, W - 40, 180))
    for i, l in enumerate(wrap(b['log'], f_m, 700)[:4]): txt(l, 45, 540 + i * 30)
    if b['state'] == 'cmd':
        for i, c in enumerate(["Serang", "Tebasan (5 MP)", "Item", "Kabur"]):
            on = i == b['idx']; txt(("> " if on else "  ") + c, 800 + (i % 2) * 230, 560 + (i // 2) * 55, f_m, (255, 220, 90) if on else (230, 230, 230))
    elif b['state'] == 'item':
        for i, iid in enumerate(b['items'] + [None]):
            on = i == b['iidx']; x, y = 790 + (i % 2) * 230, 540 + (i // 2) * 40
            if iid: screen.blit(icon(iid, 30), (x, y - 2)); txt(f"{ITEMS[iid]['name'][:12]} x{count(iid)}", x + 34, y, f_s, (255, 220, 90) if on else (230, 230, 230))
            else: txt("Kembali", x + 34, y, f_s, (255, 220, 90) if on else (230, 230, 230))


def battle_rects():
    b = battle
    if b['state'] == 'cmd': return [pygame.Rect(790 + (i % 2) * 230, 552 + (i // 2) * 55, 225, 50) for i in range(4)]
    return [pygame.Rect(790 + (i % 2) * 230, 536 + (i // 2) * 40, 225, 38) for i in range(len(b['items']) + 1)]


# ---------------- UI inventory ----------------
US = 680 / 955
UL, UR_ = load('ui/ui_left.png', scale=US), load('ui/ui_right.png', scale=US)
LX, LY = (W - UL.get_width() - UR_.get_width() - 14) // 2, (H - UL.get_height()) // 2
RX, RY = LX + UL.get_width() + 14, LY


def Lr(x, y, w, h, o='L'):
    ox, oy = (LX, LY) if o == 'L' else (RX, RY)
    return pygame.Rect(ox + int(x * US), oy + int(y * US), int(w * US), int(h * US))


CELLS = [Lr(c, r, 98, 97) for r in (268, 382, 494, 608, 720) for c in (103, 217, 330, 444, 558, 671)]
TABR = [Lr(x, 150, 106, 94) for x in (89, 217, 329, 441, 553, 666)]
TRASH, GOLDBAR = Lr(689, 833, 82, 74), Lr(86, 836, 597, 68)
SLOTR = {'helm': Lr(45, 333, 114, 112, 'R'), 'cloak': Lr(45, 454, 114, 112, 'R'), 'neck': Lr(45, 575, 114, 112, 'R'),
         'weapon': Lr(479, 333, 112, 112, 'R'), 'armor': Lr(479, 454, 112, 112, 'R'), 'boots': Lr(479, 575, 112, 112, 'R')}
NAMEBOX, INFO = Lr(271, 118, 332, 186, 'R'), Lr(40, 708, 551, 171, 'R')
BTN_USE = pygame.Rect(INFO.right - 118, INFO.y + 6, 108, 34)
BTN_SELL = pygame.Rect(INFO.right - 118, INFO.y + 44, 108, 34)
BTN_DROP = pygame.Rect(INFO.right - 118, INFO.y + 82, 108, 34)
CLOSE = pygame.Rect(W - 120, 14, 104, 38)
PORT_C = (RX + int(150 * US), RY + int(205 * US))
_pi = pygame.image.load(A('hero_idle_down.png')).convert_alpha()
_pi = pygame.transform.smoothscale(_pi.subsurface((0, 0, _pi.get_width(), int(_pi.get_height() * 0.5))).copy(), (int(_pi.get_width() * 0.5 * 1.4 * 1.7), int(_pi.get_height() * 0.5 * 0.5 * 1.7 * 1.4)))
PORT = pygame.Surface((int(198 * US),) * 2, pygame.SRCALPHA)
PORT.blit(_pi, ((PORT.get_width() - _pi.get_width()) // 2, 4))
_mask = pygame.Surface(PORT.get_size(), pygame.SRCALPHA); pygame.draw.circle(_mask, (255, 255, 255, 255), (PORT.get_width() // 2,) * 2, PORT.get_width() // 2)
PORT.blit(_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
DIM0 = pygame.Surface(TABR[0].size, pygame.SRCALPHA); pygame.draw.rect(DIM0, (70, 70, 75, 200), DIM0.get_rect(), border_radius=10)
TYPE_NAME = {'weapon': 'Senjata', 'helm': 'Helm', 'armor': 'Baju', 'cloak': 'Jubah', 'neck': 'Aksesori', 'boots': 'Sepatu',
             'use': 'Ramuan / Makanan', 'mat': 'Bahan', 'misc': 'Lain-lain'}

PRESETS = [('Tinggi', dict(fps=60, shadows=True, names=True, wander=True, shake=True)),
           ('Sedang', dict(fps=45, shadows=True, names=False, wander=True, shake=False)),
           ('Rendah', dict(fps=30, shadows=False, names=False, wander=False, shake=False))]
YN = {True: 'Ya', False: 'Tidak'}
SET_ROWS = [('fps', 'FPS maksimum', [30, 45, 60, 90, 120], {}), ('show_fps', 'Tampilkan FPS', [False, True], YN),
            ('shadows', 'Bayangan karakter', [True, False], YN), ('names', 'Nama di atas NPC', [True, False], YN),
            ('wander', 'NPC berkeliaran', [True, False], YN), ('shake', 'Getar layar di battle', [True, False], YN),
            ('touch', 'Kontrol sentuh', ['auto', 'on', 'off'], {'auto': 'Otomatis', 'on': 'Selalu', 'off': 'Sembunyi'}),
            ('tsize', 'Ukuran tombol', [0.8, 1, 1.2], {0.8: 'Kecil', 1: 'Sedang', 1.2: 'Besar'}),
            ('talpha', 'Transparansi tombol', [0, 1, 2], {0: 'Samar', 1: 'Sedang', 2: 'Jelas'}),
            ('speed', 'Kecepatan jalan', [0.8, 1, 1.25], {0.8: 'Santai', 1: 'Normal', 1.25: 'Cepat'})]
SET_AREA = Lr(100, 262, 590, 560)
ROWH = SET_AREA.height // (len(SET_ROWS) + 1)


def set_rect(i): return pygame.Rect(SET_AREA.x, SET_AREA.y + i * ROWH, SET_AREA.width, ROWH - 4)


def preset_name():
    for n, p in PRESETS:
        if all(S[k] == v for k, v in p.items()): return n
    return 'Kustom'


def cycle_setting(i):
    if i == 0:
        names = [n for n, _ in PRESETS]; cur_n = preset_name()
        nxt = (names.index(cur_n) + 1) % len(names) if cur_n in names else 0; S.update(PRESETS[nxt][1])
    else:
        key, _, opts, _ = SET_ROWS[i - 1]; j = opts.index(S[key]) if S[key] in opts else -1; S[key] = opts[(j + 1) % len(opts)]
        if key in ('tsize', 'talpha'): build_touch()
    save_settings()


def flist():
    t = inv['tab']
    def ok(it): ty = it['type']; return (t == 0 or (t == 1 and ty == 'weapon') or (t == 2 and ty in ('helm', 'armor', 'cloak', 'neck', 'boots'))
                                            or (t == 3 and ty == 'use') or (t == 4 and ty in ('mat', 'misc')))
    return [s for s in P.bag if ok(ITEMS[s[0]])]


def sel_item():
    if inv['slot']: return P.eq[inv['slot']], True
    l = flist(); return (l[inv['sel']][0], False) if 0 <= inv['sel'] < len(l) else (None, False)


def open_inv(tab=0):
    global mode
    inv.update(tab=tab, sel=-1, slot=None)
    s = screen.copy(); s.fill((90, 90, 110), special_flags=pygame.BLEND_RGB_SUB); inv['snap'] = s; mode = 'inv'


def inv_activate():
    iid, eqd = sel_item()
    if not iid: return
    it = ITEMS[iid]
    if eqd:
        if unequip(inv['slot']): note(f"Melepas {it['name']}"); inv['slot'] = None
        else: note("Tas penuh!")
    elif it['type'] == 'use':
        if use_item(iid): note(f"Memakai {it['name']}")
        else: note("HP/MP sudah penuh.")
    elif it['type'] in SLOT_OF: equip(iid); note(f"Memasang {it['name']}"); inv['sel'] = -1
    else: note("Item ini tidak bisa dipakai.")
    inv['sel'] = min(inv['sel'], len(flist()) - 1)


def inv_sell():
    iid, eqd = sel_item()
    if not iid or eqd: note("Pilih item di tas untuk dijual."); return
    remove_item(iid); P.gold += ITEMS[iid]['val']; note(f"Menjual {ITEMS[iid]['name']} (+{ITEMS[iid]['val']} G)")
    inv['sel'] = min(inv['sel'], len(flist()) - 1)


def inv_drop():
    iid, eqd = sel_item()
    if not iid or eqd: return
    remove_item(iid); note(f"Membuang {ITEMS[iid]['name']}"); inv['sel'] = min(inv['sel'], len(flist()) - 1)


def draw_inv():
    screen.blit(inv['snap'], (0, 0)); screen.blit(UL, (LX, LY)); screen.blit(UR_, (RX, RY))
    tab = inv['tab']
    if tab != 0: screen.blit(DIM0, TABR[0].topleft)
    pygame.draw.rect(screen, (255, 225, 110), TABR[tab], 4, border_radius=10)
    txt(f"{TABS[tab]}   ({len(P.bag)}/{MAXBAG})", LX + int(120 * US), LY + int(78 * US), f_m)
    if tab == 5:
        for i in range(len(SET_ROWS) + 1):
            r = set_rect(i); pygame.draw.rect(screen, (225, 205, 175), r, border_radius=8); pygame.draw.rect(screen, (120, 90, 50), r, 2, border_radius=8)
            if i == 0: lab, val = 'Kualitas grafis', preset_name()
            else: key, lab, _, mp = SET_ROWS[i - 1]; val = mp.get(S[key], str(S[key]))
            screen.blit(rt(lab, f_s, (50, 35, 20)), (r.x + 14, r.centery - 11)); v = rt(val, f_s, (20, 70, 150)); screen.blit(v, (r.right - v.get_width() - 14, r.centery - 11))
    else:
        l = flist()
        for i, s in enumerate(l[:30]):
            r = CELLS[i]; screen.blit(icon(s[0], int(r.w * 0.72)), icon(s[0], int(r.w * 0.72)).get_rect(center=r.center))
            if s[1] > 1: txt(str(s[1]), r.right - 24, r.bottom - 22, f_xs)
            if i == inv['sel'] and not inv['slot']: pygame.draw.rect(screen, (255, 225, 110), r, 3, border_radius=8)
    screen.blit(rt(f"{P.gold} G", f_m, (60, 40, 10)), (GOLDBAR.x + 70, GOLDBAR.y + 18))
    for slot, r in SLOTR.items():
        i = P.eq[slot]
        if i:
            pygame.draw.rect(screen, (120, 115, 125), r.inflate(-14, -14), border_radius=8); screen.blit(icon(i, int(r.w * 0.8)), icon(i, int(r.w * 0.8)).get_rect(center=r.center))
        if inv['slot'] == slot: pygame.draw.rect(screen, (255, 225, 110), r, 3, border_radius=8)
        screen.blit(rt(SLOT_NAME[slot], f_xs, (90, 70, 40)), (r.centerx - 22, r.bottom - 16))
    screen.blit(PORT, PORT.get_rect(center=PORT_C))
    n = NAMEBOX; txt("Kael", n.x + 12, n.y + 4, f_m, (60, 40, 10)); txt(f"Lv {P.lv}  Ksatria", n.x + 12, n.y + 30, f_s, (60, 40, 10))
    for j, (lab, v, m, c) in enumerate([("HP", P.hp, P.maxhp, (80, 210, 90)), ("MP", P.mp, P.maxmp, (90, 140, 255)), ("XP", P.xp, need(P.lv), (240, 190, 70))]):
        y = n.y + 58 + j * 22; screen.blit(rt(lab, f_xs, (60, 40, 10)), (n.x + 12, y)); bar(n.x + 40, y, n.width - 60, v, m, c, 14)
    iid, eqd = sel_item(); b = INFO
    if iid:
        it = ITEMS[iid]; txt(it['name'], b.x + 14, b.y + 8, f_s, (110, 50, 0))
        stat = "  ".join(f"{lbl} +{it[k]}" for k, lbl in (('atk', 'ATK'), ('df', 'DEF'), ('hp', 'HP'), ('mp', 'MP')) if it.get(k))
        txt(TYPE_NAME[it['type']], b.x + 14, b.y + 32, f_14, (70, 50, 30)); txt(stat, b.x + 14, b.y + 52, f_14, (20, 90, 30))
        for q, ln in enumerate(wrap(it.get('desc', ''), f_14, 250)[:2]): txt(ln, b.x + 14, b.y + 72 + q * 18, f_14, (70, 50, 30))
        txt(f"Harga jual {it['val']} G", b.x + 14, b.y + 100, f_14, (70, 50, 30))
        for r, lab in ((BTN_USE, 'LEPAS' if eqd else ('PAKAI' if it['type'] == 'use' else 'PASANG')), (BTN_SELL, 'JUAL'), (BTN_DROP, 'BUANG')):
            if eqd and r is not BTN_USE: continue
            pygame.draw.rect(screen, (60, 100, 190), r, border_radius=8); pygame.draw.rect(screen, (240, 210, 120), r, 2, border_radius=8)
            l = rt(lab, f_s, (255, 255, 255)); screen.blit(l, l.get_rect(center=r.center))
    else:
        txt(f"ATK {tatk()}   DEF {tdef()}", b.x + 14, b.y + 12, f_m, (110, 50, 0)); txt(f"Bonus perlengkapan: +{eqsum('atk')} ATK, +{eqsum('df')} DEF", b.x + 14, b.y + 46, f_14, (70, 50, 30))
        txt("Ketuk item untuk melihat detail.", b.x + 14, b.y + 72, f_14, (70, 50, 30)); txt(f"Kill Slime: {P.slimes}   Senjata +{P.wl}", b.x + 14, b.y + 94, f_14, (70, 50, 30))
    pygame.draw.rect(screen, (150, 50, 50), CLOSE, border_radius=8); pygame.draw.rect(screen, (240, 210, 120), CLOSE, 2, border_radius=8)
    l = rt("TUTUP", f_s, (255, 255, 255)); screen.blit(l, l.get_rect(center=CLOSE.center))


def inv_key(k):
    global mode
    if k in (pygame.K_ESCAPE, pygame.K_x, pygame.K_i, pygame.K_BACKSPACE): mode = 'explore'; return
    if k in (pygame.K_q, pygame.K_LEFTBRACKET): inv.update(tab=(inv['tab'] - 1) % 6, sel=-1, slot=None)
    elif k in (pygame.K_e, pygame.K_RIGHTBRACKET): inv.update(tab=(inv['tab'] + 1) % 6, sel=-1, slot=None)
    elif inv['tab'] != 5:
        n = len(flist()); d = {pygame.K_LEFT: -1, pygame.K_a: -1, pygame.K_RIGHT: 1, pygame.K_d: 1, pygame.K_UP: -6, pygame.K_w: -6, pygame.K_DOWN: 6, pygame.K_s: 6}.get(k)
        if d and n: inv['slot'] = None; inv['sel'] = max(0, min(n - 1, inv['sel'] + d if inv['sel'] >= 0 else 0))
        elif k in (pygame.K_z, pygame.K_RETURN, pygame.K_SPACE): inv_activate()
        elif k == pygame.K_DELETE: inv_drop()


def inv_tap(x, y):
    global mode
    if CLOSE.collidepoint(x, y): mode = 'explore'; return
    for i, r in enumerate(TABR):
        if r.collidepoint(x, y): inv.update(tab=i, sel=-1, slot=None); return
    if inv['tab'] == 5:
        for i in range(len(SET_ROWS) + 1):
            if set_rect(i).collidepoint(x, y): cycle_setting(i); return
    else:
        for i, r in enumerate(CELLS[:len(flist())]):
            if r.collidepoint(x, y):
                if inv['sel'] == i and not inv['slot']: inv_activate()
                else: inv['sel'] = i; inv['slot'] = None
                return
    for slot, r in SLOTR.items():
        if r.collidepoint(x, y) and P.eq[slot]: inv.update(slot=slot, sel=-1); return
    if TRASH.collidepoint(x, y): inv_drop(); return
    iid, eqd = sel_item()
    if iid:
        if BTN_USE.collidepoint(x, y): inv_activate()
        elif not eqd and BTN_SELL.collidepoint(x, y): inv_sell()
        elif not eqd and BTN_DROP.collidepoint(x, y): inv_drop()


# ---------------- sentuh ----------------
fingers, joy_vec = {}, [0.0, 0.0]
JC, JR, TB, T_BASE, T_KNOB, T_BTN = (175, 560), 100, {}, None, None, {}
HB = {'TAS': pygame.Rect(950, 84, 100, 40), 'SIMPAN': pygame.Rect(1060, 84, 100, 40), 'MUAT': pygame.Rect(1170, 84, 100, 40)}


def build_touch():
    global JR, TB, T_BASE, T_KNOB, T_BTN
    sz = S['tsize']; al = (70, 125, 185)[S['talpha']]; JR = int(100 * sz)
    TB = {'A': (1140, 575, int(62 * sz)), 'B': (1010, 635, int(48 * sz))}
    T_BASE = pygame.Surface((2 * JR + 8, 2 * JR + 8), pygame.SRCALPHA)
    pygame.draw.circle(T_BASE, (255, 255, 255, al // 3), (JR + 4, JR + 4), JR); pygame.draw.circle(T_BASE, (255, 255, 255, al + 40), (JR + 4, JR + 4), JR, 4)
    T_KNOB = pygame.Surface((int(90 * sz),) * 2, pygame.SRCALPHA); pygame.draw.circle(T_KNOB, (255, 230, 150, al + 30), (T_KNOB.get_width() // 2,) * 2, T_KNOB.get_width() // 2)
    T_BTN = {}
    for nm, (_, _, r) in TB.items():
        s = pygame.Surface((2 * r + 4, 2 * r + 4), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 200, 80, al) if nm == 'A' else (120, 200, 255, al), (r + 2, r + 2), r); pygame.draw.circle(s, (255, 255, 255, al + 50), (r + 2, r + 2), r, 4)
        t = f_l.render(nm, True, (255, 255, 255)); s.blit(t, (r + 2 - t.get_width() // 2, r - t.get_height() // 2 - 4))
        l = f_s.render("Bicara/OK" if nm == 'A' else "Ramuan", True, (255, 255, 255)); s.blit(l, (r + 2 - l.get_width() // 2, r + 14)); T_BTN[nm] = s


build_touch()


def show_touch(): return S['touch'] == 'on' or (S['touch'] == 'auto' and (ANDROID or touch_seen))


def draw_touch():
    if mode != 'explore' or not show_touch(): return
    screen.blit(T_BASE, (JC[0] - JR - 4, JC[1] - JR - 4)); k = T_KNOB.get_width() // 2
    screen.blit(T_KNOB, (int(JC[0] + joy_vec[0] * JR) - k, int(JC[1] + joy_vec[1] * JR) - k))
    for nm, (bx, by, r) in TB.items(): screen.blit(T_BTN[nm], (bx - r - 2, by - r - 2))


MAPMODE = 'logical'          # 'logical' = koordinat jari sudah relatif ke kanvas 1280x720; 'window' = relatif ke jendela (ada letterbox)
_votes = {'logical': 0, 'window': 0}
_lastf = None
active_f = set()


def f2l(nx, ny, mode_=None):
    mode_ = mode_ or MAPMODE
    if mode_ == 'logical': return nx * W, ny * H
    ww, wh = pygame.display.get_window_size(); sc = min(ww / W, wh / H)
    return (nx * ww - (ww - W * sc) / 2) / sc, (ny * wh - (wh - H * sc) / 2) / sc


def calibrate(mx, my):
    # sentuhan juga dikirim SDL sebagai klik mouse (sudah pasti benar); bandingkan dengan dua tafsiran koordinat jari
    global MAPMODE
    if not _lastf or pygame.time.get_ticks() - _lastf[0] > 300: return
    errs = {}
    for k in ('logical', 'window'):
        x, y = f2l(_lastf[1], _lastf[2], k); errs[k] = math.hypot(x - mx, y - my)
    if abs(errs['logical'] - errs['window']) < 8: return
    _votes[min(errs, key=errs.get)] += 1
    MAPMODE = 'logical' if _votes['logical'] >= _votes['window'] else 'window'


def reset_touch():
    fingers.clear(); joy_vec[0] = joy_vec[1] = 0.0


def update_joy(x, y):
    dx, dy = x - JC[0], y - JC[1]; d = math.hypot(dx, dy)
    if d > JR: dx, dy = dx * JR / d, dy * JR / d
    joy_vec[0], joy_vec[1] = dx / JR, dy / JR


def menu_rects():
    n = len(menu['items']); h = 70 + 44 * n; y0 = max(10, (H - h) // 2)
    return pygame.Rect(340, y0, 600, h), [pygame.Rect(360, y0 + 56 + i * 44, 560, 42) for i in range(n)]


def press(fid, x, y):
    if mode == 'explore':
        for nm, r in HB.items():
            if r.inflate(16, 16).collidepoint(x, y): handle_key({'TAS': pygame.K_i, 'SIMPAN': pygame.K_F5, 'MUAT': pygame.K_F9}[nm]); return
        if show_touch():
            for nm, (bx, by, br) in TB.items():
                if math.hypot(x - bx, y - by) <= br + 24: handle_key(pygame.K_z if nm == 'A' else pygame.K_p); return
            if x < 520 and y > 240: fingers[fid] = 'joy'; update_joy(x, y)
    elif mode == 'dialog': handle_key(pygame.K_z)
    elif mode == 'menu':
        for i, r in enumerate(menu_rects()[1]):
            if r.collidepoint(x, y): menu['idx'] = i; handle_key(pygame.K_z); return
    elif mode == 'inv': inv_tap(x, y)
    elif mode == 'battle':
        b = battle
        if b['state'] in ('cmd', 'item'):
            for i, r in enumerate(battle_rects()):
                if r.collidepoint(x, y):
                    if b['state'] == 'cmd': b['idx'] = i
                    else: b['iidx'] = i
                    handle_key(pygame.K_z); return


def move(fid, x, y):
    if fingers.get(fid) == 'joy': update_joy(x, y)


def release(fid):
    if fingers.pop(fid, None) == 'joy': joy_vec[0] = joy_vec[1] = 0.0


# ---------------- input keyboard ----------------
def handle_key(k):
    global mode, dialog, menu, debug
    ok = k in (pygame.K_z, pygame.K_RETURN, pygame.K_SPACE)
    if k == pygame.K_F1: debug = not debug
    if mode == 'explore':
        if ok: interact()
        elif k in (pygame.K_i, pygame.K_ESCAPE): open_inv(0)
        elif k == pygame.K_F2: open_inv(5)
        elif k == pygame.K_p: quick_heal()
        elif k == pygame.K_F5: save()
        elif k == pygame.K_F9: loadgame()
    elif mode == 'dialog' and ok:
        dialog['i'] += 1
        if dialog['i'] >= len(dialog['lines']):
            cb = dialog['cb']; dialog = None; mode = 'explore'
            if cb: cb()
    elif mode == 'menu':
        n = len(menu['items'])
        if k in (pygame.K_UP, pygame.K_w): menu['idx'] = (menu['idx'] - 1) % n
        elif k in (pygame.K_DOWN, pygame.K_s): menu['idx'] = (menu['idx'] + 1) % n
        elif k == pygame.K_ESCAPE: menu = None; mode = 'explore'
        elif ok:
            fn = menu['items'][menu['idx']][1]
            if fn is None: menu = None; mode = 'explore'
            else: fn()
    elif mode == 'inv': inv_key(k)
    elif mode == 'battle':
        b = battle
        if b['state'] == 'cmd':
            i = b['idx']
            if k in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d): b['idx'] = i ^ 1
            elif k in (pygame.K_UP, pygame.K_w, pygame.K_DOWN, pygame.K_s): b['idx'] = (i + 2) % 4
            elif ok: player_act(i)
        elif b['state'] == 'item':
            n = len(b['items']) + 1; i = b['iidx']
            if k in (pygame.K_LEFT, pygame.K_a, pygame.K_UP, pygame.K_w): b['iidx'] = (i - 1) % n
            elif k in (pygame.K_RIGHT, pygame.K_d, pygame.K_DOWN, pygame.K_s): b['iidx'] = (i + 1) % n
            elif k in (pygame.K_ESCAPE, pygame.K_x): b['state'] = 'cmd'
            elif ok:
                if i >= len(b['items']): b['state'] = 'cmd'
                else: battle_use(b['items'][i])


def save():
    try:
        d = {k: getattr(P, k) for k in ['x', 'y', 'lv', 'xp', 'gold', 'hp', 'maxhp', 'mp', 'maxmp', 'atk', 'df', 'wl', 'slimes', 'quest', 'bag', 'eq']}
        d['area'] = area; json.dump(d, open(SAVE, 'w')); note("Game disimpan.")
    except Exception: note("Gagal menyimpan.")


def loadgame():
    global loc, cur, area
    if not os.path.exists(SAVE): note("Belum ada save."); return
    try:
        d = json.load(open(SAVE))
        for k, v in d.items():
            if k in ('pot', 'eth'): continue
            if k == 'area': area = v if v in ('town', 'hunt') else 'town'; continue
            setattr(P, k, v)
        if 'pot' in d: add_item('potion_hp', d['pot'])
        if 'eth' in d: add_item('potion_mp', d['eth'])
        P.bag = [s for s in P.bag if s[0] in ITEMS]; P.eq = {s: (P.eq.get(s) if P.eq.get(s) in ITEMS else None) for s in SLOT_NAME}
        loc = cur = None; reset_touch(); note("Game dimuat.")
    except Exception: note("Save rusak.")


# ---------------- gambar dunia ----------------
def draw_outdoor():
    mp, mw, mh = (MAP, MW, MH) if area == 'town' else (HMAP, HW, HH)
    cx = max(0, min(mw - W, int(P.x - W / 2))); cy = max(0, min(mh - H, int(P.y - H / 2)))
    screen.blit(mp, (0, 0), (cx, cy, W, H)); t = pygame.time.get_ticks()
    ents = []
    for n in anpcs():
        im = sheet_for(n['who']).get(n['d'], n['anim'] // 200, n['flip'], n['moving'])
        ents.append((n['pos'][1], im, n['pos'], n['name'], -int(abs(math.sin(n['anim'] / 110)) * 3) if n['moving'] else 0, None))
    if area == 'hunt':
        for e in HM:
            if e['alive']: ents.append((e['pos'][1], hm_img(e), e['pos'], None, -int(abs(math.sin(e['anim'] / 140)) * 4), e))
    ents.append((P.y, hero.get(P.d, P.step, P.flip, P.moving), (P.x, P.y), None, 0, None))
    for _, im, (x, y), nm, bob, e in sorted(ents, key=lambda q: q[0]):
        sx, sy = int(x - cx), int(y - cy)
        if sx < -150 or sx > W + 150 or sy < -150 or sy > H + 150: continue
        if S['shadows']: screen.blit(SHADOW, (sx - 20, sy - 9))
        screen.blit(im, (sx - im.get_width() // 2, sy - im.get_height() + 6 + bob))
        top = sy - im.get_height() + bob
        if e:
            lab, col = REC[e['m']['tier']]; l = rt(f"{e['m']['name']}  {lab}", f_xs, col)
            screen.blit(rt(f"{e['m']['name']}  {lab}", f_xs, (0, 0, 0)), (sx - l.get_width() // 2 + 1, top - 15)); screen.blit(l, (sx - l.get_width() // 2, top - 16))
            if e['chase']: screen.blit(rt("!", f_m, (255, 80, 80)), (sx - 4, top - 38))
        elif nm and S['names']:
            lab = rt(nm, f_s, (255, 240, 180)); screen.blit(rt(nm, f_s, (0, 0, 0)), (sx - lab.get_width() // 2 + 1, top - 11)); screen.blit(lab, (sx - lab.get_width() // 2, top - 12))
    if debug:
        if area == 'town':
            for b in BLOCK: pygame.draw.rect(screen, (255, 0, 0), b.move(-cx, -cy), 2)
            for b, _ in WILD: pygame.draw.rect(screen, (255, 255, 0), b.move(-cx, -cy), 2)
            for b in DOORR.values(): pygame.draw.rect(screen, (0, 255, 255), b.move(-cx, -cy), 2)
            pygame.draw.rect(screen, (0, 255, 255), GATE.move(-cx, -cy), 2)
        else: pygame.draw.rect(screen, (0, 255, 255), HEXIT.move(-cx, -cy), 2)


def draw_interior():
    c = cur; s = c['s']; screen.fill((0, 0, 0)); screen.blit(c['surf'], (c['ox'], c['oy']))
    ents = [(n['pos'][1], c['sh'][n['who']].get(n['d'], 0, n['flip'], False), n['pos'], n['name']) for n in c['npcs']]
    ents.append((P.iy, c['hs'].get(P.d, P.step, P.flip, P.moving), (P.ix, P.iy), None))
    for _, im, (x, y), nm in sorted(ents, key=lambda e: e[0]):
        sx, sy = c['ox'] + int(x * s), c['oy'] + int(y * s)
        if S['shadows']: screen.blit(SHADOW, (sx - 20, sy - 9))
        screen.blit(im, (sx - im.get_width() // 2, sy - im.get_height() + 6))
        if nm and S['names']: lab = rt(nm, f_s, (255, 240, 180)); screen.blit(lab, (sx - lab.get_width() // 2, sy - im.get_height() - 12))
    if debug:
        for r in c['floor']: pygame.draw.rect(screen, (0, 255, 0), pygame.Rect(c['ox'] + r.x * s, c['oy'] + r.y * s, r.w * s, r.h * s), 2)
        for r in c['solid']: pygame.draw.rect(screen, (255, 0, 0), pygame.Rect(c['ox'] + r.x * s, c['oy'] + r.y * s, r.w * s, r.h * s), 2)


def draw_hud():
    panel((10, 10, 330, 92), 190)
    txt(f"Kael  Lv {P.lv}   XP {P.xp}/{need(P.lv)}", 24, 14, f_s); bar(24, 40, 290, P.hp, P.maxhp, (80, 210, 90)); bar(24, 62, 290, P.mp, P.maxmp, (90, 140, 255))
    txt(f"HP {P.hp}/{P.maxhp}", 30, 36, f_xs); txt(f"MP {P.mp}/{P.maxmp}", 30, 58, f_xs)
    panel((W - 330, 10, 320, 66), 190); txt(f"Emas {P.gold}   Tas {len(P.bag)}/{MAXBAG}", W - 318, 14, f_s)
    q = {0: "Quest: bicara dgn Sir Aldric", 1: f"Quest: kalahkan Slime {min(P.slimes, 5)}/5", 2: "Quest: lapor ke Sir Aldric", 3: "Quest selesai!"}[P.quest]
    txt(q, W - 318, 40, f_s, (255, 220, 120))
    if mode == 'explore':
        for nm, r in HB.items():
            panel(r, 200); l = rt(nm, f_s, (255, 255, 255)); screen.blit(l, l.get_rect(center=r.center))
    if not ANDROID and not show_touch(): txt("WASD/Panah: jalan  Z/Spasi: bicara  I: tas  P: ramuan  F2: setelan", 10, H - 26, f_14, (230, 230, 230))


def draw_dialog():
    panel((40, 500, W - 80, 190)); txt(dialog['name'], 70, 510, f_m, (255, 220, 100))
    for i, l in enumerate(wrap(dialog['lines'][dialog['i']], f_m, W - 180)[:4]): txt(l, 70, 548 + i * 30)
    txt("Ketuk layar >" if (ANDROID or touch_seen) else "Z / Spasi >", W - 210, 655, f_s, (200, 200, 200))


def draw_menu():
    box, rects = menu_rects(); panel(box); txt(menu['title'], box.x + 24, box.y + 12, f_m, (255, 220, 100))
    txt(f"{P.gold} G", box.right - 110, box.y + 14, f_s, (255, 230, 120))
    for i, (r, it) in enumerate(zip(rects, menu['items'])):
        on = i == menu['idx']
        if on: pygame.draw.rect(screen, (70, 90, 160), r, border_radius=8)
        x = r.x + 10
        if it[2]: screen.blit(icon(it[2], 34), (x, r.y + 4)); x += 44
        txt(it[0], x, r.y + 8, f_m, (255, 230, 120) if on else (230, 230, 230))


def draw_toast():
    if pygame.time.get_ticks() < toast[1]:
        panel((W // 2 - 300, 120, 600, 44)); l = rt(toast[0], f_s, (255, 255, 255)); screen.blit(l, l.get_rect(center=(W // 2, 142)))


# ---------------- update explore ----------------
def update_explore(dt):
    global walk_t
    kk = pygame.key.get_pressed()
    dx = (kk[pygame.K_RIGHT] or kk[pygame.K_d]) - (kk[pygame.K_LEFT] or kk[pygame.K_a])
    dy = (kk[pygame.K_DOWN] or kk[pygame.K_s]) - (kk[pygame.K_UP] or kk[pygame.K_w])
    if abs(joy_vec[0]) > 0.3: dx = 1 if joy_vec[0] > 0 else -1
    if abs(joy_vec[1]) > 0.3: dy = 1 if joy_vec[1] > 0 else -1
    if not (dx or dy): P.step = 0; P.moving = False; walk_t = 0
    else:
        sp = 275 * S['speed'] * min(dt, 50) / 1000 * (0.7071 if dx and dy else 1); moved = False
        if abs(dx) >= abs(dy) and dx: P.d, P.flip = 'side', dx < 0
        elif dy: P.d, P.flip = ('down' if dy > 0 else 'up'), False
        if loc is None:
            nx, ny = P.x + dx * sp, P.y + dy * sp
            if not blocked(nx, P.y): P.x = nx; moved = True
            if not blocked(P.x, ny): P.y = ny; moved = True
            if moved: P.dist += sp
        else:
            sp = sp * 0.85 / cur['s']; nx, ny = P.ix + dx * sp, P.iy + dy * sp
            if int_ok(nx, P.iy): P.ix = nx; moved = True
            if int_ok(P.ix, ny): P.iy = ny; moved = True
        if moved: walk_t += dt; P.step = int(walk_t // 95); P.moving = True
        else: P.step = 0; P.moving = False
    now = pygame.time.get_ticks()
    if loc is None:
        r = feet(P.x, P.y)
        if now > door_lock:
            if area == 'town':
                for iid, dr in DOORR.items():
                    if r.colliderect(dr): enter(iid); return
                if r.colliderect(GATE): enter_area('hunt', HENTRY); return
            elif r.colliderect(HEXIT): enter_area('town', GATE_OUT); return
        if area == 'town' and P.moving:
            for w, z in WILD:
                if r.colliderect(w) and P.dist > random.randint(260, 520): P.dist = 0; start_battle(z); return
    else:
        for n in cur['npcs']:
            if math.hypot(n['pos'][0] - P.ix, n['pos'][1] - P.iy) < 110: face(n, P.ix, P.iy)
        if ifeet(P.ix, P.iy).colliderect(cur['exit']) and now > door_lock: leave()


# ---------------- loop ----------------
say("Narator", ["Selamat datang di Eldenvale, desa kecil di tepi hutan.", "Temui Sir Aldric di dekat gereja. Ketuk TAS untuk membuka inventory dan setelan."])
while True:
    dt = clock.tick(S['fps'])
    for e in pygame.event.get():
        if e.type == pygame.QUIT: pygame.quit(); sys.exit()
        elif e.type == pygame.KEYDOWN: handle_key(e.key)
        elif e.type == pygame.FINGERDOWN:
            touch_seen = True; active_f.add(e.finger_id); _lastf = (pygame.time.get_ticks(), e.x, e.y); press(e.finger_id, *f2l(e.x, e.y))
        elif e.type == pygame.FINGERMOTION: move(e.finger_id, *f2l(e.x, e.y))
        elif e.type == pygame.FINGERUP:
            active_f.discard(e.finger_id); release(e.finger_id)
            if not active_f: reset_touch()
        elif e.type in (pygame.WINDOWFOCUSLOST, pygame.APP_WILLENTERBACKGROUND, pygame.APP_DIDENTERBACKGROUND): active_f.clear(); reset_touch()
        elif ANDROID and e.type == pygame.MOUSEBUTTONDOWN: calibrate(*e.pos)
        elif not ANDROID and e.type == pygame.MOUSEBUTTONDOWN and e.button == 1: press('m', *e.pos)
        elif not ANDROID and e.type == pygame.MOUSEMOTION and e.buttons[0]: move('m', *e.pos)
        elif not ANDROID and e.type == pygame.MOUSEBUTTONUP and e.button == 1: release('m')
    if mode == 'explore': update_explore(dt)
    elif mode == 'battle': update_battle()
    if mode != 'explore': P.moving = False; reset_touch() if (fingers or joy_vec[0] or joy_vec[1]) and mode != 'inv' else None
    if loc is None:
        update_npcs(dt)
        if area == 'hunt': update_hunt(dt)

    if mode == 'battle': draw_battle()
    elif mode == 'inv': draw_inv()
    else:
        draw_outdoor() if loc is None else draw_interior()
        draw_hud()
        if mode == 'dialog': draw_dialog()
        if mode == 'menu': draw_menu()
        draw_touch()
    draw_toast()
    if S['show_fps']: txt(f"{clock.get_fps():.0f} FPS", W - 100, H - 30, f_s, (120, 255, 120))
    pygame.display.flip()
