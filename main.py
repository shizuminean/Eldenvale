# -*- coding: utf-8 -*-
"""Chronicle of Eldenvale - RPG desktop (Python + pygame)."""
import pygame, sys, os, random, json, math

BASE = os.path.dirname(os.path.abspath(__file__))
A = lambda *p: os.path.join(BASE, 'assets', *p)
SAVE = os.path.join(BASE, 'save.json')
W, H = 1280, 720

pygame.init()
ANDROID = 'ANDROID_ARGUMENT' in os.environ
screen = pygame.display.set_mode((W, H), (pygame.FULLSCREEN if ANDROID else pygame.RESIZABLE) | pygame.SCALED)
pygame.display.set_caption("Eldenvale RPG")
clock = pygame.time.Clock()
def F(s, b=False):
    try: return pygame.font.SysFont("arial,dejavusans,freesans", s, bold=b)
    except Exception: return pygame.font.Font(None, int(s * 1.25))
f_s, f_m, f_l = F(18), F(22), F(34, True)

MAP = pygame.image.load(A('map.png')).convert()
MW, MH = MAP.get_size()


def load(name, h):
    img = pygame.image.load(A(name)).convert_alpha()
    return pygame.transform.smoothscale(img, (max(1, int(img.get_width() * h / img.get_height())), h))


class Sheet:
    def __init__(self, who, h):
        self.f = {}
        for d in ('down', 'side', 'up'):
            fr = [load(f'{who}_{d}_{i}.png', h) for i in (0, 1) if os.path.exists(A(f'{who}_{d}_{i}.png'))]
            if len(fr) == 1:
                fr.append(fr[0])
            self.f[d] = fr

    def get(self, d, step, flip=False):
        im = self.f[d][step % 2]
        return pygame.transform.flip(im, True, False) if flip else im


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
WILD = [(60, 590, 260, 120, 1), (900, 720, 520, 95, 1), (330, 700, 470, 90, 1),
        (1400, 560, 70, 150, 1), (800, 850, 130, 70, 2), (40, 260, 290, 290, 0)]
WILD = [pygame.Rect(*w[:4]) for w in WILD[:5]]

NPCS = [
    dict(name="Sir Aldric", who="knight", pos=(800, 330), kind="quest"),
    dict(name="Suster Lyra", who="priest", pos=(895, 292), kind="priest"),
    dict(name="Penyihir Orn", who="mage", pos=(1165, 320), kind="shop"),
    dict(name="Brom si Pandai Besi", who="smith", pos=(520, 492), kind="smith"),
    dict(name="Rosalind", who="rose", pos=(650, 290), kind="inn"),
    dict(name="Fenn si Pemanah", who="archer", pos=(1120, 520), kind="archer"),
    dict(name="Mira", who="girl", pos=(700, 565), kind="girl"),
]
SPR = {}
hero = Sheet('hero', 66)
for n in NPCS:
    SPR[n['who']] = Sheet(n['who'], 66)


# ---------- state ----------
class P:  # player
    x, y = 880.0, 520.0
    d, step, flip, dist = 'down', 0, False, 0.0
    lv, xp, gold = 1, 0, 40
    hp = maxhp = 60
    mp = maxmp = 20
    atk, df = 9, 3
    pot, eth = 3, 1
    wl = 0
    slimes = 0
    quest = 0  # 0 belum,1 aktif,2 selesai,3 diambil


def need(lv): return 20 + lv * lv * 8


def feet(x, y): return pygame.Rect(int(x) - 12, int(y) - 12, 24, 14)


def blocked(x, y):
    r = feet(x, y)
    if any(r.colliderect(b) for b in BLOCK): return True
    for n in NPCS:
        if r.colliderect(feet(*n['pos']).inflate(10, 6)): return True
    return False


mode = 'explore'
dialog = None      # dict(name, lines, i, cb)
menu = None        # dict(title, items, idx)
toast = ("", 0)
debug = False
walk_t = 0
battle = None


def say(name, lines, cb=None):
    global dialog, mode
    dialog = dict(name=name, lines=lines if isinstance(lines, list) else [lines], i=0, cb=cb)
    mode = 'dialog'


def note(t): 
    global toast; toast = (t, pygame.time.get_ticks() + 2200)


def open_menu(title, items):
    global menu, mode
    menu = dict(title=title, items=items + [("Tutup", None)], idx=0); mode = 'menu'


def heal_full(): P.hp, P.mp = P.maxhp, P.maxmp


def gain(xp, gold):
    P.xp += xp; P.gold += gold; msgs = []
    while P.xp >= need(P.lv):
        P.xp -= need(P.lv); P.lv += 1
        P.maxhp += 12; P.maxmp += 4; P.atk += 3; P.df += 1
        heal_full(); msgs.append(f"LEVEL UP! Sekarang Lv {P.lv}")
    return msgs


# ---------- NPC logic ----------
def talk(n):
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
            say(nm, ["Terima kasih sudah menjaga desa. Berhati-hatilah di hutan dalam."])
    elif k == 'priest':
        say(nm, ["Cahaya melindungimu. Biarkan aku menyembuhkan lukamu."], lambda: (heal_full(), note("HP & MP pulih penuh!")))
    elif k == 'inn':
        def rest():
            if P.gold >= 10: P.gold -= 10; heal_full(); note("Istirahat nyenyak. HP & MP pulih (-10 emas)")
            else: note("Emas tidak cukup.")
        say(nm, ["Penginapan Eldenvale! Menginap hanya 10 emas."], lambda: open_menu("Menginap 10 emas?", [("Ya, menginap", rest)]))
    elif k == 'shop':
        def buy(item, price):
            def f():
                if P.gold < price: note("Emas tidak cukup."); return
                P.gold -= price; setattr(P, item, getattr(P, item) + 1); note(f"Membeli 1 {'Ramuan' if item=='pot' else 'Ether'}")
            return f
        say(nm, ["Ramuan segar, langsung dari kuali!"], lambda: open_menu("Toko Ramuan", [("Ramuan HP (30) - 15 emas", buy('pot', 15)), ("Ether MP (15) - 20 emas", buy('eth', 20))]))
    elif k == 'smith':
        def up():
            c = 50 * (P.wl + 1)
            if P.gold < c: note("Emas tidak cukup."); return
            P.gold -= c; P.wl += 1; P.atk += 3; note(f"Senjata +{P.wl}! ATK naik 3")
        say(nm, ["Besi yang baik butuh api yang panas!"], lambda: open_menu(f"Tempa senjata ({50*(P.wl+1)} emas, ATK +3)", [("Tempa", up)]))
    elif k == 'archer':
        say(nm, ["Rumput di selatan dan timur sering didatangi monster.", "Makin ke selatan jalan tanah, makin kuat musuhnya. Bawa ramuan!"])
    else:
        say(nm, ["Ada kincir angin dan ladang di sana. Kata kakek, sungai itu berasal dari air terjun ajaib."])


# ---------- battle ----------
KINDS = {'Slime': (22, 6, 9, 7, (80, 200, 255)), 'Goblin': (38, 9, 16, 13, (110, 170, 70)), 'Serigala': (55, 13, 24, 18, (140, 140, 160))}


def start_battle(deep=False):
    global battle, mode
    names = ['Slime', 'Slime', 'Goblin'] if not deep else ['Goblin', 'Serigala', 'Serigala']
    nm = random.choice(names); hp, atk, xp, gd, col = KINDS[nm]
    s = 1 + (P.lv - 1) * 0.18
    battle = dict(name=nm, hp=int(hp * s), maxhp=int(hp * s), atk=int(atk * s), xp=int(xp * s), gold=int(gd * s), col=col,
                  snap=screen.copy(), state='cmd', idx=0, log=f"Seekor {nm} liar muncul!", t=0, shake=0, flash=0)
    mode = 'battle'


def blog(t, state, delay=700):
    battle['log'] = t; battle['state'] = state; battle['t'] = pygame.time.get_ticks() + delay


def player_act(i):
    b = battle
    if i == 0:
        d = max(1, P.atk + random.randint(-2, 3) - 0); b['hp'] -= d; b['shake'] = 12
        blog(f"Kamu menyerang! {d} damage.", 'after')
    elif i == 1:
        if P.mp < 5: blog("MP tidak cukup!", 'cmd', 500); return
        P.mp -= 5; d = int(P.atk * 2 + random.randint(0, 4)); b['hp'] -= d; b['shake'] = 18
        blog(f"Tebasan Merah! {d} damage.", 'after')
    elif i == 2:
        if P.pot > 0: P.pot -= 1; P.hp = min(P.maxhp, P.hp + 30); blog("Minum Ramuan: HP +30.", 'enemy')
        elif P.eth > 0: P.eth -= 1; P.mp = min(P.maxmp, P.mp + 15); blog("Minum Ether: MP +15.", 'enemy')
        else: blog("Tidak punya item!", 'cmd', 500)
    elif i == 3:
        if random.random() < 0.6: blog("Berhasil kabur!", 'end_run', 800)
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
            if b['name'] == 'Slime' and P.quest == 1: P.slimes += 1
            msgs = gain(b['xp'], b['gold'])
            blog(f"{b['name']} kalah! +{b['xp']} XP, +{b['gold']} emas. " + " ".join(msgs), 'end_win', 1600)
        else: b['state'] = 'enemy'
    elif s == 'enemy':
        d = max(1, b['atk'] - P.df + random.randint(-1, 2)); P.hp -= d; b['flash'] = 10
        if P.hp <= 0: P.hp = 0; blog(f"{b['name']} menyerang {d}! Kamu tumbang...", 'end_lose', 1500)
        else: blog(f"{b['name']} menyerang! {d} damage.", 'cmd', 600)
    elif s in ('end_win', 'end_run'): mode = 'explore'; battle = None
    elif s == 'end_lose':
        P.gold //= 2; P.hp, P.mp = P.maxhp // 2, P.maxmp // 2; P.x, P.y = 880.0, 520.0
        mode = 'explore'; battle = None; note("Kamu pingsan & terbangun di alun-alun (emas -50%)")


def draw_enemy(name, col, cx, cy, t):
    bob = int(math.sin(t / 250) * 6)
    if name == 'Slime':
        pygame.draw.ellipse(screen, col, (cx - 70, cy - 50 + bob, 140, 100))
        pygame.draw.ellipse(screen, (255, 255, 255), (cx - 35, cy - 25 + bob, 18, 26)); pygame.draw.ellipse(screen, (255, 255, 255), (cx + 17, cy - 25 + bob, 18, 26))
        pygame.draw.circle(screen, (20, 20, 40), (cx - 26, cy - 8 + bob), 6); pygame.draw.circle(screen, (20, 20, 40), (cx + 26, cy - 8 + bob), 6)
    elif name == 'Goblin':
        pygame.draw.rect(screen, col, (cx - 40, cy - 30 + bob, 80, 100), border_radius=18)
        pygame.draw.circle(screen, col, (cx, cy - 55 + bob), 38)
        pygame.draw.polygon(screen, col, [(cx - 34, cy - 65 + bob), (cx - 80, cy - 85 + bob), (cx - 30, cy - 45 + bob)])
        pygame.draw.polygon(screen, col, [(cx + 34, cy - 65 + bob), (cx + 80, cy - 85 + bob), (cx + 30, cy - 45 + bob)])
        pygame.draw.circle(screen, (255, 230, 60), (cx - 14, cy - 58 + bob), 7); pygame.draw.circle(screen, (255, 230, 60), (cx + 14, cy - 58 + bob), 7)
        pygame.draw.line(screen, (90, 60, 30), (cx + 50, cy + 60 + bob), (cx + 80, cy - 40 + bob), 8)
    else:
        pygame.draw.ellipse(screen, col, (cx - 90, cy - 20 + bob, 180, 90))
        pygame.draw.circle(screen, col, (cx - 85, cy - 15 + bob), 36)
        pygame.draw.polygon(screen, col, [(cx - 105, cy - 40 + bob), (cx - 95, cy - 75 + bob), (cx - 75, cy - 42 + bob)])
        pygame.draw.circle(screen, (255, 60, 60), (cx - 95, cy - 20 + bob), 6)
        pygame.draw.polygon(screen, col, [(cx + 85, cy + bob), (cx + 140, cy - 35 + bob), (cx + 95, cy + 30 + bob)])


def bar(x, y, w, v, m, col):
    pygame.draw.rect(screen, (30, 30, 40), (x, y, w, 14), border_radius=5)
    pygame.draw.rect(screen, col, (x, y, int(w * max(0, v) / max(1, m)), 14), border_radius=5)


def txt(t, x, y, font=f_m, col=(255, 255, 255)):
    screen.blit(font.render(t, True, (0, 0, 0)), (x + 2, y + 2)); screen.blit(font.render(t, True, col), (x, y))


def panel(r, a=225):
    s = pygame.Surface((r[2], r[3]), pygame.SRCALPHA); pygame.draw.rect(s, (18, 18, 38, a), s.get_rect(), border_radius=12)
    pygame.draw.rect(s, (220, 190, 110), s.get_rect(), 3, border_radius=12); screen.blit(s, (r[0], r[1]))


def wrap(t, font, w):
    out, cur = [], ""
    for wd in t.split(" "):
        if font.size(cur + wd)[0] > w: out.append(cur); cur = wd + " "
        else: cur += wd + " "
    return out + [cur]


def draw_battle():
    b = battle; t = pygame.time.get_ticks()
    screen.blit(b['snap'], (0, 0)); ov = pygame.Surface((W, H), pygame.SRCALPHA); ov.fill((0, 0, 20, 150)); screen.blit(ov, (0, 0))
    pim = hero.get('side', t // 300)
    pim = pygame.transform.smoothscale(pim, (pim.get_width() * 3, pim.get_height() * 3))
    ox = random.randint(-6, 6) if b['flash'] else 0
    screen.blit(pim, (220 + ox, 320))
    if b['hp'] > 0 or b['state'] == 'after':
        sx = random.randint(-8, 8) if b['shake'] else 0
        draw_enemy(b['name'], b['col'], 900 + sx, 330, t)
    txt(f"{b['name']}", 760, 120, f_l); bar(760, 175, 280, b['hp'], b['maxhp'], (220, 60, 60))
    panel((30, 30, 330, 100)); txt(f"Lv {P.lv}  HP {P.hp}/{P.maxhp}", 50, 40); bar(50, 75, 280, P.hp, P.maxhp, (80, 210, 90))
    txt(f"MP {P.mp}/{P.maxmp}", 50, 95, f_s); 
    panel((20, 520, W - 40, 180))
    for i, l in enumerate(wrap(b['log'], f_m, 620)[:4]): txt(l, 45, 540 + i * 30)
    if b['state'] == 'cmd':
        for i, c in enumerate(["Serang", f"Tebasan (5 MP)", f"Item (R{P.pot}/E{P.eth})", "Kabur"]):
            col = (255, 220, 90) if i == b['idx'] else (230, 230, 230)
            txt(("> " if i == b['idx'] else "  ") + c, 800 + (i % 2) * 230, 560 + (i // 2) * 55, f_m, col)


# ---------- gambar dunia ----------
def draw_world():
    cx = max(0, min(MW - W, int(P.x - W / 2))); cy = max(0, min(MH - H, int(P.y - H / 2)))
    screen.blit(MAP, (0, 0), (cx, cy, W, H))
    ents = [(n['pos'][1], SPR[n['who']].get('down', 0), n['pos'], n['name']) for n in NPCS]
    ents.append((P.y, hero.get(P.d, P.step, P.flip), (P.x, P.y), None))
    for _, im, (x, y), nm in sorted(ents, key=lambda e: e[0]):
        sx, sy = int(x - cx), int(y - cy)
        pygame.draw.ellipse(screen, (0, 0, 0, 80), (sx - 18, sy - 8, 36, 14))
        screen.blit(im, (sx - im.get_width() // 2, sy - im.get_height() + 6))
        if nm: 
            lab = f_s.render(nm, True, (255, 240, 180)); screen.blit(lab, (sx - lab.get_width() // 2, sy - im.get_height() - 12))
    if debug:
        for b in BLOCK: pygame.draw.rect(screen, (255, 0, 0), b.move(-cx, -cy), 2)
        for b in WILD: pygame.draw.rect(screen, (255, 255, 0), b.move(-cx, -cy), 2)
    panel((10, 10, 330, 92), 190)
    txt(f"Lv {P.lv}  XP {P.xp}/{need(P.lv)}", 24, 14, f_s); bar(24, 40, 290, P.hp, P.maxhp, (80, 210, 90)); bar(24, 62, 290, P.mp, P.maxmp, (90, 140, 255))
    txt(f"HP {P.hp}/{P.maxhp}", 30, 36, F(13, True)); txt(f"MP {P.mp}/{P.maxmp}", 30, 58, F(13, True))
    txt(f"Emas {P.gold}   Ramuan {P.pot}   Ether {P.eth}", 20, 80, F(15)) if False else None
    panel((W - 330, 10, 320, 66), 190)
    txt(f"Emas {P.gold}  Ramuan {P.pot}  Ether {P.eth}", W - 318, 14, f_s)
    q = {0: "Quest: bicara dgn Sir Aldric", 1: f"Quest: kalahkan Slime {min(P.slimes,5)}/5", 2: "Quest: lapor ke Sir Aldric", 3: "Quest selesai!"}[P.quest]
    txt(q, W - 318, 40, f_s, (255, 220, 120))
    if not ANDROID: txt("WASD/Panah: jalan  Z/Spasi: bicara  P: ramuan  F5 simpan  F9 muat", 10, H - 26, F(14), (230, 230, 230))
    if pygame.time.get_ticks() < toast[1]: 
        panel((W // 2 - 300, 120, 600, 44)); txt(toast[0], W // 2 - 285, 128, f_s)


def draw_dialog():
    panel((40, 500, W - 80, 190))
    txt(dialog['name'], 70, 510, f_m, (255, 220, 100))
    for i, l in enumerate(wrap(dialog['lines'][dialog['i']], f_m, W - 180)[:4]): txt(l, 70, 548 + i * 30)
    txt("Ketuk layar >" if ANDROID else "Z / Spasi >", W - 210, 655, f_s, (200, 200, 200))


def draw_menu():
    h = 80 + 44 * len(menu['items']); panel((380, 200, 520, h))
    txt(menu['title'], 405, 215, f_m, (255, 220, 100))
    for i, (lbl, _) in enumerate(menu['items']):
        txt(("> " if i == menu['idx'] else "  ") + lbl, 410, 265 + i * 44, f_m, (255, 230, 120) if i == menu['idx'] else (230, 230, 230))


def save():
    try: json.dump({k: getattr(P, k) for k in ['x', 'y', 'lv', 'xp', 'gold', 'hp', 'maxhp', 'mp', 'maxmp', 'atk', 'df', 'pot', 'eth', 'wl', 'slimes', 'quest']}, open(SAVE, 'w')); note("Game disimpan.")
    except Exception: note("Gagal menyimpan.")


def loadgame():
    if os.path.exists(SAVE):
        for k, v in json.load(open(SAVE)).items(): setattr(P, k, v)
        note("Game dimuat.")
    else: note("Belum ada save.")


def near_npc():
    for n in NPCS:
        if math.hypot(n['pos'][0] - P.x, n['pos'][1] - P.y) < 70: return n


# ---------- loop ----------
def handle_key(k):
    global mode, dialog, menu, debug
    ok = k in (pygame.K_z, pygame.K_RETURN, pygame.K_SPACE)
    if k == pygame.K_F1: debug = not debug
    if mode == 'explore':
        if ok:
            n = near_npc()
            if n: talk(n)
        elif k == pygame.K_p:
            if P.pot > 0 and P.hp < P.maxhp: P.pot -= 1; P.hp = min(P.maxhp, P.hp + 30); note("HP +30")
        elif k == pygame.K_F5: save()
        elif k == pygame.K_F9: loadgame()
        elif k == pygame.K_ESCAPE: pygame.quit(); sys.exit()
    elif mode == 'dialog' and ok:
        dialog['i'] += 1
        if dialog['i'] >= len(dialog['lines']):
            cb = dialog['cb']; dialog = None; mode = 'explore'
            if cb: cb()
    elif mode == 'menu':
        if k in (pygame.K_UP, pygame.K_w): menu['idx'] = (menu['idx'] - 1) % len(menu['items'])
        elif k in (pygame.K_DOWN, pygame.K_s): menu['idx'] = (menu['idx'] + 1) % len(menu['items'])
        elif k == pygame.K_ESCAPE: menu = None; mode = 'explore'
        elif ok:
            fn = menu['items'][menu['idx']][1]
            if fn is None: menu = None; mode = 'explore'
            else: fn()
    elif mode == 'battle' and battle['state'] == 'cmd':
        i = battle['idx']
        if k in (pygame.K_LEFT, pygame.K_a): battle['idx'] = i ^ 1
        elif k in (pygame.K_RIGHT, pygame.K_d): battle['idx'] = i ^ 1
        elif k in (pygame.K_UP, pygame.K_w, pygame.K_DOWN, pygame.K_s): battle['idx'] = (i + 2) % 4
        elif ok: player_act(i)


# ---------- kontrol sentuh ----------
fingers = {}
joy_vec = [0.0, 0.0]
JC, JR = (170, 570), 100
BTN = {'A': (1140, 575, 62), 'B': (1010, 635, 48)}
SBTN = {'SIMPAN': pygame.Rect(1050, 90, 100, 38), 'MUAT': pygame.Rect(1160, 90, 100, 38)}
touch_seen = False


def to_logical(nx, ny):
    ww, wh = pygame.display.get_window_size(); sc = min(ww / W, wh / H)
    return (nx * ww - (ww - W * sc) / 2) / sc, (ny * wh - (wh - H * sc) / 2) / sc


def update_joy(x, y):
    dx, dy = x - JC[0], y - JC[1]; d = math.hypot(dx, dy)
    if d > JR: dx, dy = dx * JR / d, dy * JR / d
    joy_vec[0], joy_vec[1] = dx / JR, dy / JR


def press(fid, x, y):
    if mode == 'explore':
        for nm, (bx, by, br) in BTN.items():
            if math.hypot(x - bx, y - by) <= br + 12:
                handle_key(pygame.K_z if nm == 'A' else pygame.K_p); return
        for nm, r in SBTN.items():
            if r.collidepoint(x, y):
                handle_key(pygame.K_F5 if nm == 'SIMPAN' else pygame.K_F9); return
        if x < 480 and y > 280: fingers[fid] = 'joy'; update_joy(x, y)
    elif mode == 'dialog': handle_key(pygame.K_z)
    elif mode == 'menu':
        for i in range(len(menu['items'])):
            if pygame.Rect(400, 258 + i * 44, 480, 42).collidepoint(x, y):
                menu['idx'] = i; handle_key(pygame.K_z); return
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
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    pygame.draw.circle(s, (255, 255, 255, 45), JC, JR); pygame.draw.circle(s, (255, 255, 255, 110), JC, JR, 4)
    pygame.draw.circle(s, (255, 230, 150, 170), (int(JC[0] + joy_vec[0] * JR), int(JC[1] + joy_vec[1] * JR)), 42)
    for nm, (bx, by, br) in BTN.items():
        pygame.draw.circle(s, (255, 200, 80, 120) if nm == 'A' else (120, 200, 255, 120), (bx, by), br)
        pygame.draw.circle(s, (255, 255, 255, 170), (bx, by), br, 4)
        t = f_l.render(nm, True, (255, 255, 255)); s.blit(t, (bx - t.get_width() // 2, by - t.get_height() // 2 - 6))
        l = f_s.render("Bicara/OK" if nm == 'A' else "Ramuan", True, (255, 255, 255)); s.blit(l, (bx - l.get_width() // 2, by + 14))
    for nm, r in SBTN.items():
        pygame.draw.rect(s, (20, 20, 40, 170), r, border_radius=8); pygame.draw.rect(s, (220, 190, 110, 230), r, 2, border_radius=8)
        t = f_s.render(nm, True, (255, 255, 255)); s.blit(t, (r.centerx - t.get_width() // 2, r.centery - t.get_height() // 2))
    screen.blit(s, (0, 0))


say("Narator", ["Selamat datang di Eldenvale, desa kecil di tepi hutan.", "Temui Sir Aldric di dekat gereja untuk memulai petualanganmu."])
title = True
while True:
    dt = clock.tick(60)
    for e in pygame.event.get():
        if e.type == pygame.QUIT: pygame.quit(); sys.exit()
        elif e.type == pygame.KEYDOWN: handle_key(e.key)
        elif e.type == pygame.FINGERDOWN: touch_seen = True; press(e.finger_id, *to_logical(e.x, e.y))
        elif e.type == pygame.FINGERMOTION: move(e.finger_id, *to_logical(e.x, e.y))
        elif e.type == pygame.FINGERUP: release(e.finger_id)
        elif not ANDROID and e.type == pygame.MOUSEBUTTONDOWN and e.button == 1: press('m', *e.pos)
        elif not ANDROID and e.type == pygame.MOUSEMOTION and e.buttons[0]: move('m', *e.pos)
        elif not ANDROID and e.type == pygame.MOUSEBUTTONUP and e.button == 1: release('m')

    if mode == 'explore':
        kk = pygame.key.get_pressed()
        dx = (kk[pygame.K_RIGHT] or kk[pygame.K_d]) - (kk[pygame.K_LEFT] or kk[pygame.K_a])
        dy = (kk[pygame.K_DOWN] or kk[pygame.K_s]) - (kk[pygame.K_UP] or kk[pygame.K_w])
        if abs(joy_vec[0]) > 0.3: dx = 1 if joy_vec[0] > 0 else -1
        if abs(joy_vec[1]) > 0.3: dy = 1 if joy_vec[1] > 0 else -1
        if dx or dy:
            sp = 3.2 * (0.7071 if dx and dy else 1)
            nx, ny = P.x + dx * sp, P.y + dy * sp
            if not blocked(nx, P.y): P.x = nx
            if not blocked(P.x, ny): P.y = ny
            if abs(dx) >= abs(dy) and dx: P.d, P.flip = 'side', dx < 0
            elif dy: P.d, P.flip = ('down' if dy > 0 else 'up'), False
            walk_t += dt; P.step = walk_t // 160; P.dist += sp
            r = feet(P.x, P.y)
            if any(r.colliderect(w) for w in WILD) and P.dist > random.randint(260, 520):
                P.dist = 0; start_battle(deep=P.y > 840)
        else: P.step = 0
    elif mode == 'battle': update_battle()

    screen.fill((0, 0, 0))
    if mode == 'battle': draw_battle()
    else:
        draw_world()
        if mode == 'dialog': draw_dialog()
        if mode == 'menu': draw_menu()
        draw_touch()
    pygame.display.flip()
