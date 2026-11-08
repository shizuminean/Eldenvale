# -*- coding: utf-8 -*-
"""Eldenvale RPG - battle REAL-TIME (aksi RPG, kontrol ala MOBA) langsung di peta Hutan Berburu.

Tidak ada layar / popup battle. Monster berkeliaran di peta, mengejar, lalu memberi TELEGRAF serangan (area merah
yang mengisi) sebelum memukul, sehingga bisa dihindari. Pemain bertarung dengan:
  - joystick (gerak)            - tombol SERANG (tahan = serang beruntun, kombo 3 pukulan)
  - 4 skill dengan cooldown + MP (tap = bidik otomatis ke musuh terdekat, geser = bidik manual seperti MOBA)
  - tombol ramuan (HP, atau MP bila HP penuh)
Keyboard: WASD/Panah gerak, J / Spasi / Z serang, 1-4 skill, P ramuan.

Modul ini tidak mengimpor main.py; main.py memanggil bind(<modul main>) sekali saat boot.
"""
import math, random
import pygame

g = None   # modul game (diisi lewat bind)


def bind(mod):
    global g
    g = mod
    reset()


def T(): return pygame.time.get_ticks()


# ------------------------------------------------------------------ data
SK = [
    dict(name='Tebasan Merah', lv=1, mp=5,  cd=2500,  ico='sword',   col=(255, 110, 100), key='1', aim='cone',
         desc='Tebasan lebar 150 derajat'),
    dict(name='Terjang Badai', lv=2, mp=8,  cd=5000,  ico='run',     col=(110, 200, 255), key='2', aim='line',
         desc='Melesat menembus musuh, kebal sesaat'),
    dict(name='Gempa Bumi',    lv=4, mp=14, cd=9000,  ico='bolt',    col=(255, 205, 100), key='3', aim='circle',
         desc='Hantam tanah: damage area + stun'),
    dict(name='Badai Pedang',  lv=6, mp=24, cd=24000, ico='diamond', col=(205, 140, 255), key='4', aim='circle',
         desc='Berputar 2,4 detik, menyayat semua musuh sekitar'),
]
BASIC = dict(mult=(1.0, 1.0, 1.7), rad=(84, 84, 104), half=(1.05, 1.05, 1.4), gap=(360, 360, 520), kb=(10, 10, 70), lunge=(10, 10, 26), mp=(1, 1, 2))
DASH_DIST, DASH_MS = 215.0, 190
ULT_MS, ULT_TICK, ULT_R = 2400, 200, 150
QUAKE_R = 138
SLASH_R, SLASH_HALF = 128, 1.3

KIND = {'Babi Hutan': 'charge', 'Serigala Hitam': 'charge', 'Serigala Putih': 'charge', 'Kobra': 'charge', 'Kalajengking': 'charge',
        'Kelelawar': 'charge', 'Laba-laba Merah': 'charge',
        'Goblin Pemanah': 'ranged', 'Kerangka Penyihir': 'ranged', 'Hantu Tengkorak': 'ranged', 'Naga Kecil': 'ranged', 'Golem Kristal': 'ranged',
        'Golem Lumut': 'slam', 'Treant': 'slam', 'Zombie': 'slam', 'Ghoul': 'slam',
        'Raja Slime': 'boss1', 'Vampir': 'boss2'}
BOLT = {'Goblin Pemanah': (235, 205, 120), 'Kerangka Penyihir': (175, 110, 255), 'Hantu Tengkorak': (150, 230, 255),
        'Naga Kecil': (255, 140, 60), 'Golem Kristal': (140, 220, 255), 'Vampir': (230, 50, 90)}
WIND = dict(swing=430, dash=650, shot=520, fan=720, slam=850, leap=950)
CDR = dict(melee=(700, 1200), charge=(1200, 1900), ranged=(1300, 1900), slam=(1400, 2200), boss1=(1200, 2000), boss2=(1000, 1700))
DASH_V = 520.0

C = {}
BTN = {}


def reset():
    C.clear()
    C.update(cd=[0, 0, 0, 0], atk_ready=0, combo=0, combo_t=0, inv=0, dash=None, ult_until=0, ult_tick=0, swing=None,
             fx=[], proj=[], flt=[], shake=0, flash=0, pot_ready=0, mp_acc=0.0, last_hit=0, drag={}, hint=0,
             cast_flash=[0, 0, 0, 0], pot_flash=0, busy=0)


reset()


# ------------------------------------------------------------------ status
def active():
    return g is not None and g.mode == 'explore' and g.loc is None and g.area == 'hunt'


def speed_mult():
    t = T()
    if t < C['ult_until']: return 0.65
    if C['swing'] and t < C['swing']['t0'] + 150: return 0.8
    return 1.0


def locked_move():
    return C['dash'] is not None


def shake_off():
    if not g.S.get('shake', True): return 0, 0
    t = T()
    if t >= C['shake']: return 0, 0
    k = (C['shake'] - t) / 160.0
    return int(random.randint(-5, 5) * min(1.0, k)), int(random.randint(-5, 5) * min(1.0, k))


# ------------------------------------------------------------------ musuh
def rescale(e):
    m = e['m']; boss = m['tier'] == 9; s = 1 + (g.P.lv - 1) * (0.08 if boss else 0.15)
    e['maxhp'] = int(m['hp'] * s * 1.5); e['hp'] = float(e['maxhp']); e['atk'] = int(m['atk'] * s)
    e['xp'] = int(m['xp'] * s); e['gold'] = int(m['gold'] * s)


def init_enemy(e):
    m = e['m']; boss = m['tier'] == 9
    e.update(kind=KIND.get(m['name'], 'melee'), boss=boss, st='idle', st_t=0, sk=None, w0=0, cdr=0, hit=0, kbx=0.0, kby=0.0, kbt=0, agg=0,
             dv=(0.0, 0.0), tp=None, lp0=None, aim=(0.0, 1.0), hitp=False, path=None, pt=0,
             reach=int(26 + e['h'] * 0.35), rad=max(14, int(e['h'] * 0.3)), hp=1.0, maxhp=1, atk=m['atk'], xp=m['xp'], gold=m['gold'])
    rescale(e)


def respawn(e):
    e['alive'] = True; e['pos'] = [float(e['home'][0]), float(e['home'][1])]; e['imm'] = T() + 2000
    e['st'] = 'idle'; e['chase'] = False; e['agg'] = 0; e['kbt'] = 0; e['cdr'] = 0; e['sk'] = None
    rescale(e)


def alive_list():
    return [e for e in g.HM if e['alive']]


def nearest_enemy(maxd, px=None, py=None):
    P = g.P; px = P.x if px is None else px; py = P.y if py is None else py
    best, bd = None, maxd
    for e in g.HM:
        if not e['alive']: continue
        d = math.hypot(e['pos'][0] - px, e['pos'][1] - py) - e['rad']
        if d < bd: best, bd = e, d
    return best


def bar_shown(e):
    return e['alive'] and (e.get('chase') or e['hp'] < e['maxhp'] - 0.5)


def update_enemies(dt):
    t = T()
    for e in g.HM:
        if not e['alive']:
            if t >= e['respawn']: respawn(e)
            continue
        if not active(): continue
        step_enemy(e, dt, t)
        if not active(): break   # pemain kalah di tengah loop
    if active(): separate()


def walk_to(e, tx, ty, speed, dtm):
    x, y = e['pos']; ddx, ddy = tx - x, ty - y; dd = max(0.001, math.hypot(ddx, ddy)); sp = speed * dtm
    nx, ny = x + ddx / dd * sp, y + ddy / dd * sp; moved = False
    if g.hm_ok(nx, y): e['pos'][0] = nx; moved = True
    if g.hm_ok(e['pos'][0], ny): e['pos'][1] = ny; moved = True
    return moved


def step_enemy(e, dt, t):
    P = g.P; dtm = min(dt, 50) / 1000.0; e['anim'] += dt
    if e['kbt'] > t:
        nx, ny = e['pos'][0] + e['kbx'] * dtm, e['pos'][1] + e['kby'] * dtm
        if g.hm_ok(nx, e['pos'][1]): e['pos'][0] = nx
        if g.hm_ok(e['pos'][0], ny): e['pos'][1] = ny
    x, y = e['pos']; dx, dy = P.x - x, P.y - y; dist = max(0.001, math.hypot(dx, dy)); ux, uy = dx / dist, dy / dist
    st = e['st']
    if st == 'stun':
        if t >= e['st_t']: e['st'] = 'chase'
        return
    if st == 'wind':
        if (t - e['w0']) < 0.55 * WIND[e['sk']] and e['sk'] in ('swing', 'shot'): e['aim'] = (ux, uy)
        if abs(dx) > 1: e['flip'] = dx > 0
        if t >= e['st_t']: resolve(e, t)
        return
    if st == 'act': act_step(e, dtm, t); return
    if st == 'rec':
        if t >= e['st_t']: e['st'] = 'chase'
        return
    boss = e['boss']; hx, hy = e['home']
    go = (dist < (150 if boss else 260)) if e['chase'] else (dist < (110 if boss else 190))
    go = (go or t < e['agg']) and t > e['imm'] and P.hp > 0
    if go and math.hypot(x - hx, y - hy) > (700 if boss else 560):   # tali kekang: terlalu jauh dari sarang -> pulang
        go = False; e['agg'] = 0; e['imm'] = t + 2500
    if go and not e['chase']:
        if e['hp'] >= e['maxhp']: rescale(e)
        e['cdr'] = max(e['cdr'], t + 450)
    e['chase'] = go
    if go:
        e['st'] = 'chase'; chase_step(e, dtm, t, dx, dy, dist, ux, uy)
    else:
        e['st'] = 'idle'; idle_step(e, dt, t)


def pick_skill(e, dist):
    k = e['kind']; reach = e['reach']
    if k == 'melee': return 'swing' if dist <= reach else None
    if k == 'charge':
        if dist <= reach: return 'swing'
        if 100 <= dist <= 215: return 'dash'
    elif k == 'ranged':
        if 90 <= dist <= 340: return 'shot'
    elif k == 'slam':
        if dist <= 112: return 'slam'
        if dist <= reach: return 'swing'
    elif k == 'boss1':
        if dist <= 140: return 'slam'
        if 170 <= dist <= 420: return 'leap'
    elif k == 'boss2':
        if dist <= reach + 24: return 'swing'
        if 140 <= dist <= 400: return random.choice(('fan', 'dash'))
    return None


def begin(e, sk, t):
    P = g.P; dx, dy = P.x - e['pos'][0], P.y - e['pos'][1]; d = max(0.001, math.hypot(dx, dy))
    e['sk'] = sk; e['st'] = 'wind'; e['w0'] = t; e['st_t'] = t + WIND[sk]; e['aim'] = (dx / d, dy / d)
    if sk == 'leap': e['tp'] = (P.x, P.y)


def chase_step(e, dtm, t, dx, dy, dist, ux, uy):
    k = e['kind']; boss = e['boss']
    if abs(dx) > 1: e['flip'] = dx > 0
    if t >= e['cdr']:
        sk = pick_skill(e, dist)
        if sk: begin(e, sk, t); return
    spd = e['spd'] * (2.0 if boss else 2.4)
    if k == 'ranged':
        if dist > 270: go_near(e, dtm, t, spd, dist)
        elif dist < 150: walk_to(e, e['pos'][0] - ux * 60, e['pos'][1] - uy * 60, spd * 0.9, dtm)
        else: walk_to(e, e['pos'][0] - uy * 60, e['pos'][1] + ux * 60, spd * 0.45, dtm)
        return
    stop = e['reach'] * 0.85 if k not in ('slam', 'boss1') else 90
    if dist > stop: go_near(e, dtm, t, spd, dist)
    elif dist < stop + 60: walk_to(e, e['pos'][0] - uy * 60, e['pos'][1] + ux * 60, spd * 0.3, dtm)


def go_near(e, dtm, t, spd, dist):
    x, y = e['pos']; P = g.P; tx, ty = P.x, P.y
    if dist > 110:   # jalur BFS (mengikuti tikungan & tembok), dihitung ulang tiap 400 ms
        if t >= e['pt']:
            e['path'] = g.hm_path((int(x) // g.HCELL, int(y) // g.HCELL), (int(P.x) // g.HCELL, int(P.y) // g.HCELL)) or []
            e['pt'] = t + 400
        path = e['path'] or []
        while path and math.hypot(path[0][0] * g.HCELL + 8 - x, path[0][1] * g.HCELL + 8 - y) < 4: path.pop(0)
        if path: tx, ty = path[0][0] * g.HCELL + 8, path[0][1] * g.HCELL + 8
    if not walk_to(e, tx, ty, spd, dtm): e['pt'] = 0


def idle_step(e, dt, t):
    dtm = min(dt, 50) / 1000.0; e['path'] = None
    if e['hp'] < e['maxhp']: e['hp'] = min(float(e['maxhp']), e['hp'] + e['maxhp'] * 0.10 * dtm)
    if e['tgt'] is None:
        if t < e['wait']: return
        hx, hy = e['home']; r = e['r']; tx, ty = hx + random.uniform(-r, r), hy + random.uniform(-r, r)
        if g.hm_ok(tx, ty): e['tgt'] = (tx, ty)
        else: e['wait'] = t + 300
        return
    tx, ty = e['tgt']; x, y = e['pos']; ddx, ddy = tx - x, ty - y; dd = math.hypot(ddx, ddy)
    if dd < 4: e['tgt'] = None; e['wait'] = t + random.randint(1200, 4000); return
    sp = e['spd'] * (1.4 if math.hypot(x - e['home'][0], y - e['home'][1]) > e['r'] * 1.5 else 0.6) * dtm
    nx, ny = x + ddx / dd * sp, y + ddy / dd * sp
    if g.hm_ok(nx, ny): e['pos'] = [nx, ny]; e['flip'] = ddx > 0
    else: e['tgt'] = None; e['wait'] = t + 500


def finish(e, t, rec):
    e['st'] = 'rec'; e['st_t'] = t + rec; e['cdr'] = t + rec + random.randint(*CDR[e['kind']]); e['hitp'] = False


def resolve(e, t):
    sk = e['sk']; x, y = e['pos']; ax, ay = e['aim']; P = g.P; atk = e['atk']; boss = e['boss']
    dist = math.hypot(P.x - x, P.y - y)
    if sk == 'swing':
        fx_slash(x, y, ax, ay, e['reach'] + 16, 1.1, (255, 90, 80), 240)
        if dist <= e['reach'] + 16 + 4 and (P.x - x) * ax + (P.y - y) * ay >= -0.1 * dist: hurt_player(1.0, x, y, atk)
        finish(e, t, 520)
    elif sk == 'dash':
        e['st'] = 'act'; e['st_t'] = t + 380; e['dv'] = (ax * DASH_V, ay * DASH_V); e['hitp'] = False
    elif sk == 'shot':
        spawn_proj(e, ax, ay, 1.0, 300); finish(e, t, 450)
    elif sk == 'fan':
        for a in (-0.32, 0.0, 0.32):
            c, s = math.cos(a), math.sin(a); spawn_proj(e, ax * c - ay * s, ax * s + ay * c, 0.7, 290)
        finish(e, t, 650)
    elif sk == 'slam':
        R = 120 if boss else 100; fx_ring(x, y, R, (255, 120, 80), 380)
        C['shake'] = t + 200 if dist < 500 else C['shake']
        if dist <= R: hurt_player(1.35, x, y, atk, 90)
        finish(e, t, 800)
    elif sk == 'leap':
        e['st'] = 'act'; e['st_t'] = t + 420; e['w0'] = t; e['lp0'] = (x, y)


def act_step(e, dtm, t):
    P = g.P; x, y = e['pos']; sk = e['sk']; atk = e['atk']
    if sk == 'dash':
        n = max(1, int(math.hypot(*e['dv']) * dtm / 6.0)); sx, sy = e['dv'][0] * dtm / n, e['dv'][1] * dtm / n; ok = True
        for _ in range(n):
            if g.hm_ok(e['pos'][0] + sx, e['pos'][1]): e['pos'][0] += sx
            else: ok = False
            if g.hm_ok(e['pos'][0], e['pos'][1] + sy): e['pos'][1] += sy
            else: ok = False
        if e['dv'][0]: e['flip'] = e['dv'][0] > 0
        if not e['hitp'] and math.hypot(P.x - e['pos'][0], P.y - e['pos'][1]) <= e['rad'] + 22:
            e['hitp'] = True; hurt_player(1.25, e['pos'][0], e['pos'][1], atk, 110); finish(e, t, 650); return
        if not ok or t >= e['st_t']: finish(e, t, 650)
    elif sk == 'leap':
        p = min(1.0, (t - e['w0']) / 420.0); lx, ly = e['lp0']; tx, ty = e['tp']
        nx, ny = lx + (tx - lx) * p, ly + (ty - ly) * p
        if g.hm_ok(nx, ny): e['pos'] = [nx, ny]
        if p >= 1.0:
            R = 108; fx_ring(e['pos'][0], e['pos'][1], R, (255, 90, 70), 420); C['shake'] = t + 220
            if math.hypot(P.x - e['pos'][0], P.y - e['pos'][1]) <= R: hurt_player(1.3, e['pos'][0], e['pos'][1], atk, 100)
            finish(e, t, 900)
    else: finish(e, t, 400)


def separate():
    P = g.P
    es = [e for e in g.HM if e['alive'] and e['st'] != 'act' and abs(e['pos'][0] - P.x) < 700 and abs(e['pos'][1] - P.y) < 520]
    for i in range(len(es)):
        a = es[i]
        for j in range(i + 1, len(es)):
            b = es[j]; dx, dy = b['pos'][0] - a['pos'][0], b['pos'][1] - a['pos'][1]; d = math.hypot(dx, dy); m = (a['rad'] + b['rad']) * 0.9
            if 0.01 < d < m:
                push = (m - d) * 0.3; ux, uy = dx / d, dy / d
                if g.hm_ok(b['pos'][0] + ux * push, b['pos'][1] + uy * push): b['pos'][0] += ux * push; b['pos'][1] += uy * push
                if g.hm_ok(a['pos'][0] - ux * push, a['pos'][1] - uy * push): a['pos'][0] -= ux * push; a['pos'][1] -= uy * push


# ------------------------------------------------------------------ proyektil musuh
def spawn_proj(e, ax, ay, mult, speed):
    x, y = e['pos']; col = BOLT.get(e['m']['name'], (255, 120, 120))
    C['proj'].append(dict(x=x + ax * 18, y=y + ay * 18, vx=ax * speed, vy=ay * speed, end=T() + 1700, mult=mult, atk=e['atk'], r=11, col=col, boss=e['boss']))


def update_proj(dtm, t):
    P = g.P; keep = []
    for p in C['proj']:
        if t >= p['end']: continue
        n = max(1, int(math.hypot(p['vx'], p['vy']) * dtm / 8.0)); sx, sy = p['vx'] * dtm / n, p['vy'] * dtm / n; dead = False
        for _ in range(n):
            p['x'] += sx; p['y'] += sy
            if not g.hm_ok(p['x'], p['y']): dead = True; fx_spark(p['x'], p['y'], p['col']); break
            if P.hp > 0 and math.hypot(P.x - p['x'], P.y - p['y']) <= p['r'] + 14:
                hurt_player(p['mult'], p['x'] - p['vx'], p['y'] - p['vy'], p['atk'], 40); fx_spark(p['x'], p['y'], p['col']); dead = True; break
        if not dead: keep.append(p)
    C['proj'] = keep


# ------------------------------------------------------------------ efek
def fx_add(**k):
    k['t0'] = T(); C['fx'].append(k)
    if len(C['fx']) > 80: del C['fx'][0]


def fx_slash(x, y, ax, ay, r, half, col, dur): fx_add(k='slash', x=x, y=y, ax=ax, ay=ay, r=r, half=half, col=col, dur=dur)
def fx_ring(x, y, r, col, dur): fx_add(k='ring', x=x, y=y, r=r, col=col, dur=dur)
def fx_spark(x, y, col): fx_add(k='spark', x=x, y=y, col=col, dur=260)


def flt(x, y, text, col, big=False):
    C['flt'].append(dict(x=x + random.randint(-8, 8), y=y, text=text, col=col, big=big, t0=T()))
    if len(C['flt']) > 40: del C['flt'][0]


# ------------------------------------------------------------------ damage
def calc_edmg(atk, mult):
    return max(1, int(atk * mult - g.tdef() * 0.6 + random.randint(-1, 2)))


def hurt_player(mult, sx, sy, atk, kb=70):
    P = g.P; t = T()
    if P.hp <= 0: return False
    if t < C['inv']:
        flt(P.x, P.y - 70, "Luput!", (150, 225, 255)); return False
    d = calc_edmg(atk, mult)
    if t < C['ult_until']: d = max(1, d // 2)
    P.hp -= d; C['flash'] = t + 240; C['last_hit'] = t; C['shake'] = t + 160
    flt(P.x, P.y - 70, "-%d" % d, (255, 95, 95), True)
    dx, dy = P.x - sx, P.y - sy; n = max(0.001, math.hypot(dx, dy)); st = kb * 0.18
    nx, ny = P.x + dx / n * st, P.y + dy / n * st
    if not g.blocked(nx, P.y): P.x = nx
    if not g.blocked(P.x, ny): P.y = ny
    if P.hp <= 0: P.hp = 0; defeat()
    return True


def hit_enemy(e, mult, kb=0, stun=0, src=None):
    P = g.P; t = T()
    base = g.tatk() * mult * (1.0 + 0.04 * (P.lv - 1)); crit = random.random() < 0.12
    d = max(1, int(base * random.uniform(0.9, 1.1) * (1.6 if crit else 1.0)))
    if e['hp'] >= e['maxhp'] and not e['chase']: rescale(e)
    e['hp'] -= d; e['hit'] = t + 130; e['agg'] = t + 8000; e['chase'] = True
    flt(e['pos'][0], e['pos'][1] - e['h'] * 0.85, ("%d!" % d) if crit else str(d), (255, 225, 110) if crit else (255, 255, 255), crit or mult >= 1.5)
    sx, sy = src if src else (P.x, P.y); dx, dy = e['pos'][0] - sx, e['pos'][1] - sy; n = max(0.001, math.hypot(dx, dy))
    if kb:
        k = kb * (0.25 if e['boss'] else 1.0); e['kbx'], e['kby'] = dx / n * k / 0.14, dy / n * k / 0.14; e['kbt'] = t + 140
        if kb >= 60 and e['st'] == 'wind' and not e['boss']: e['st'] = 'rec'; e['st_t'] = t + 450
    if stun:
        e['st'] = 'stun'; e['st_t'] = t + int(stun * (0.35 if e['boss'] else 1.0)); e['sk'] = None
    fx_spark(e['pos'][0], e['pos'][1] - e['h'] * 0.5, (255, 240, 200))
    if e['hp'] <= 0: kill(e)
    return d


def kill(e):
    t = T(); P = g.P; m = e['m']
    e['alive'] = False; e['chase'] = False; e['st'] = 'idle'; e['respawn'] = t + (120000 if e['boss'] else 25000)
    try: im = g.hm_img(e); fx_add(k='ghost', im=im, x=e['pos'][0], y=e['pos'][1], dur=450)
    except Exception: pass
    fx_ring(e['pos'][0], e['pos'][1], 60, (255, 240, 180), 350)
    if 'Slime' in m['name'] and P.quest == 1: P.slimes += 1
    for q in g.GQ:
        if q['kind'] == 'kill' and q['match'] in m['name'] and g.gq_get(q['id'])['st'] == 'active': g.gq_get(q['id'])['n'] += 1
    got = []
    for iid, ch in m['drops']:
        if random.random() < ch:
            got.append(g.ITEMS[iid]['name'] if g.add_item(iid) else "(tas penuh)")
    lv0 = P.lv; msgs = g.gain(e['xp'], e['gold'])
    flt(e['pos'][0], e['pos'][1] - e['h'] - 8, "+%d XP  +%d G" % (e['xp'], e['gold']), (190, 255, 190), True)
    if msgs: flt(P.x, P.y - 96, "NAIK LEVEL! Lv %d" % P.lv, (255, 230, 120), True); fx_ring(P.x, P.y, 120, (255, 230, 120), 700)
    g.note("%s dikalahkan!  %s" % (m['name'], ("Dapat: " + ", ".join(got)) if got else "") + ("  " + msgs[-1] if msgs else ""))


def defeat():
    P = g.P; t = T()
    P.gold //= 2; P.hp, P.mp = P.maxhp // 2, P.maxmp // 2
    for e in g.HM:
        e['pos'] = [float(e['home'][0]), float(e['home'][1])]; e['imm'] = t + 3000; e['chase'] = False; e['st'] = 'idle'; e['agg'] = 0
        e['hp'] = float(e['maxhp'])
    g.loc = g.cur = None; g.dialog = g.menu = None; g.mode = 'explore'; g.area = 'town'   # area dulu: safe_spot() memakai peta desa
    P.moving = False; P.step = 0; P.d, P.flip = 'down', False
    reset()
    g.enter_area('town', g.safe_spot(*g.V.SPAWN)); g.note("Kamu pingsan & terbangun di alun-alun (emas -50%)")


# ------------------------------------------------------------------ aksi pemain
def face(ax, ay):
    P = g.P
    if abs(ax) >= abs(ay): P.d, P.flip = 'side', ax < 0
    else: P.d, P.flip = ('down' if ay > 0 else 'up'), False


def facing_vec():
    P = g.P
    if P.d == 'side': return (-1.0, 0.0) if P.flip else (1.0, 0.0)
    return (0.0, 1.0) if P.d == 'down' else (0.0, -1.0)


def aim_dir(manual=None, rng=230):
    P = g.P
    if manual: return manual
    e = nearest_enemy(rng)
    if e:
        dx, dy = e['pos'][0] - P.x, e['pos'][1] - P.y; d = max(0.001, math.hypot(dx, dy)); return (dx / d, dy / d)
    return facing_vec()


def in_arc(px, py, ax, ay, e, rad, half):
    dx, dy = e['pos'][0] - px, e['pos'][1] - py; d = math.hypot(dx, dy)
    if d - e['rad'] > rad: return False
    if d <= e['rad'] + 6: return True
    c = max(-1.0, min(1.0, (dx * ax + dy * ay) / d))
    return math.acos(c) <= half + math.asin(min(1.0, e['rad'] / d))


def lunge(ax, ay, dist):
    P = g.P; n = max(1, int(dist / 4));
    for _ in range(n):
        nx, ny = P.x + ax * 4, P.y + ay * 4
        if not g.blocked(nx, P.y): P.x = nx
        if not g.blocked(P.x, ny): P.y = ny


def attack(manual=None):
    t = T(); P = g.P
    if not active() or P.hp <= 0 or t < C['atk_ready'] or C['dash'] or t < C['busy']: return False
    if t - C['combo_t'] > 900: C['combo'] = 0
    n = C['combo']; C['combo'] = (n + 1) % 3; C['combo_t'] = t
    ax, ay = aim_dir(manual); face(ax, ay)
    rad, half = BASIC['rad'][n], BASIC['half'][n]; C['atk_ready'] = t + BASIC['gap'][n]
    C['swing'] = dict(t0=t, dur=BASIC['gap'][n] - 40, ax=ax, ay=ay, r=rad, half=half, col=(255, 245, 210) if n < 2 else (255, 205, 110), n=n)
    lunge(ax, ay, BASIC['lunge'][n]); hits = 0
    for e in alive_list():
        if in_arc(P.x, P.y, ax, ay, e, rad, half): hit_enemy(e, BASIC['mult'][n], BASIC['kb'][n]); hits += 1
    if hits: P.mp = min(P.maxmp, P.mp + BASIC['mp'][n])
    if n == 2 and hits: C['shake'] = t + 130
    return True


def cast(i, manual=None):
    t = T(); P = g.P; s = SK[i]
    if not active() or P.hp <= 0 or C['dash']: return False
    if P.lv < s['lv']:
        if t > C['hint']: g.note("%s terbuka di Lv %d" % (s['name'], s['lv'])); C['hint'] = t + 1200
        return False
    if t < C['cd'][i]: return False
    if P.mp < s['mp']:
        if t > C['hint']: g.note("MP tidak cukup! (%d MP)" % s['mp']); C['hint'] = t + 1200
        return False
    P.mp -= s['mp']; C['cd'][i] = t + s['cd']; C['cast_flash'][i] = t + 180; C['atk_ready'] = max(C['atk_ready'], t + 220)
    mult = 1.0 + 0.05 * (P.lv - 1); hits = 0
    if i == 0:
        ax, ay = aim_dir(manual); face(ax, ay)
        C['swing'] = dict(t0=t, dur=300, ax=ax, ay=ay, r=SLASH_R, half=SLASH_HALF, col=s['col'], n=3)
        lunge(ax, ay, 20)
        for e in alive_list():
            if in_arc(P.x, P.y, ax, ay, e, SLASH_R, SLASH_HALF): hit_enemy(e, 2.0 * mult, 48); hits += 1
        C['shake'] = t + 130
    elif i == 1:
        ax, ay = aim_dir(manual, 320); face(ax, ay)
        C['dash'] = dict(t0=t, t1=t + DASH_MS, ax=ax, ay=ay, x0=P.x, y0=P.y, done=set(), mult=1.6 * mult)
        C['inv'] = t + DASH_MS + 140
    elif i == 2:
        fx_ring(P.x, P.y, QUAKE_R, s['col'], 480); fx_ring(P.x, P.y, QUAKE_R * 0.6, (255, 255, 220), 360); C['shake'] = t + 220
        for e in alive_list():
            if math.hypot(e['pos'][0] - P.x, e['pos'][1] - P.y) - e['rad'] <= QUAKE_R: hit_enemy(e, 2.3 * mult, 70, 1300); hits += 1
    elif i == 3:
        C['ult_until'] = t + ULT_MS; C['ult_tick'] = t; C['busy'] = 0
        fx_ring(P.x, P.y, ULT_R, s['col'], 500)
    return True


def potion():
    t = T(); P = g.P
    if not active() or t < C['pot_ready']: return False
    hp0, mp0 = P.hp, P.mp
    if P.hp < P.maxhp:
        g.quick_heal()
    elif P.mp < P.maxmp:
        for sl in P.bag:
            it = g.ITEMS[sl[0]]
            if it['type'] == 'use' and it.get('mp') and not it.get('hp'): g.use_item(sl[0]); g.note("Memakai %s" % it['name']); break
        else: g.note("Tidak ada ramuan MP.")
    else: g.note("HP & MP sudah penuh.")
    if P.hp > hp0: flt(P.x, P.y - 70, "+%d" % (P.hp - hp0), (130, 255, 150), True)
    if P.mp > mp0: flt(P.x, P.y - 90, "+%d MP" % (P.mp - mp0), (130, 190, 255))
    if P.hp > hp0 or P.mp > mp0: C['pot_ready'] = t + 1200; C['pot_flash'] = t + 200; return True
    return False


# ------------------------------------------------------------------ update pemain
def update_player(dt):
    t = T(); P = g.P; dtm = min(dt, 50) / 1000.0
    if not active(): return
    C['mp_acc'] += dtm * 0.7
    while C['mp_acc'] >= 1.0:
        C['mp_acc'] -= 1.0
        if P.mp < P.maxmp: P.mp += 1
    d = C['dash']
    if d:
        P.moving = False
        p = min(1.0, (t - d['t0']) / float(DASH_MS)); tx, ty = d['x0'] + d['ax'] * DASH_DIST, d['y0'] + d['ay'] * DASH_DIST
        want = DASH_DIST * p; have = math.hypot(P.x - d['x0'], P.y - d['y0'])
        n = max(1, int(max(0.0, want - have) / 5.0 + 0.999))
        for _ in range(n):
            if math.hypot(P.x - d['x0'], P.y - d['y0']) >= want: break
            nx, ny = P.x + d['ax'] * 5, P.y + d['ay'] * 5; moved = False
            if not g.blocked(nx, P.y): P.x = nx; moved = True
            if not g.blocked(P.x, ny): P.y = ny; moved = True
            if not moved: d['t1'] = t; break
            for e in alive_list():
                if id(e) not in d['done'] and math.hypot(e['pos'][0] - P.x, e['pos'][1] - P.y) <= e['rad'] + 34:
                    d['done'].add(id(e)); hit_enemy(e, d['mult'], 90, 0, (d['x0'], d['y0']))
        if len(C['fx']) < 70: fx_add(k='ghostp', x=P.x, y=P.y, dur=240)
        if t >= d['t1'] or p >= 1.0: C['dash'] = None
    if t < C['ult_until'] and t >= C['ult_tick']:
        C['ult_tick'] = t + ULT_TICK; fx_ring(P.x, P.y, ULT_R * 0.8, SK[3]['col'], 260)
        for e in alive_list():
            if math.hypot(e['pos'][0] - P.x, e['pos'][1] - P.y) - e['rad'] <= ULT_R: hit_enemy(e, 1.3 * (1.0 + 0.05 * (P.lv - 1)), 28)
    kk = pygame.key.get_pressed()
    if kk[pygame.K_j] or 'atk' in g.fingers.values(): attack()
    if C['swing'] and t > C['swing']['t0'] + C['swing']['dur']: C['swing'] = None
    update_proj(dtm, t)
    C['fx'] = [f for f in C['fx'] if t - f['t0'] < f['dur']]
    C['flt'] = [f for f in C['flt'] if t - f['t0'] < 1000]


def update(dt):
    """Dipanggil tiap frame dari update(): pemain, musuh, proyektil."""
    if g.mode == 'explore' and g.loc is None and g.area == 'hunt': update_player(dt)
    update_enemies(dt)


# ------------------------------------------------------------------ input
def build_layout():
    ax, ay, ar = g.TB['A']; sz = float(g.S['tsize']); sr = int(34 * sz); ur = int(40 * sz); d = ar + sr + int(34 * sz)
    BTN.clear(); BTN['A'] = (ax, ay, ar)
    for i, a in enumerate((172, 212, 252, 296)):
        r = ur if i == 3 else sr; dd = d + (int(8 * sz) if i == 3 else 0)
        x = int(ax + dd * math.cos(math.radians(a))); y = int(ay + dd * math.sin(math.radians(a)))
        BTN['S%d' % i] = (min(x, g.W - g.SAFE_X - r), y, r)
    br = int(30 * sz); BTN['B'] = (BTN['S0'][0] - sr - br - int(14 * sz), BTN['S0'][1] + int(26 * sz), br)


def press(fid, x, y):
    """Sentuh/klik di mode jelajah Hutan. True bila mengenai tombol battle."""
    if not BTN: build_layout()
    for nm, (bx, by, r) in BTN.items():
        if math.hypot(x - bx, y - by) > r + (22 if nm == 'A' else 12): continue
        if nm == 'A':
            if g.near_npc(): g.interact(); return True
            g.fingers[fid] = 'atk'; attack()
        elif nm == 'B': potion()
        else:
            i = int(nm[1]); g.fingers[fid] = 'sk%d' % i; C['drag'][fid] = dict(i=i, bx=bx, by=by, aim=None)
        return True
    return False


def move(fid, x, y):
    d = C['drag'].get(fid)
    if d:
        dx, dy = x - d['bx'], y - d['by']; n = math.hypot(dx, dy)
        d['aim'] = (dx / n, dy / n) if n > 20 else None


def release(fid, kind):
    d = C['drag'].pop(fid, None)
    if d and kind and kind.startswith('sk'): cast(d['i'], d['aim'])


def key(k):
    """Tombol keyboard di Hutan. True bila ditangani."""
    K = pygame
    if k in (K.K_SPACE, K.K_z, K.K_RETURN, K.K_j):
        if g.near_npc(): g.interact()
        else: attack()
        return True
    for i, kk in enumerate((K.K_1, K.K_2, K.K_3, K.K_4)):
        if k == kk: cast(i); return True
    if k == K.K_p: potion(); return True
    return False


# ------------------------------------------------------------------ gambar
def _apoly(pts, rgba, width=0):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; x0, y0 = int(min(xs)) - 3, int(min(ys)) - 3
    w, h = int(max(xs)) - x0 + 4, int(max(ys)) - y0 + 4
    if w <= 0 or h <= 0 or w > 1600 or h > 1000: return
    s = pygame.Surface((w, h), pygame.SRCALPHA); pygame.draw.polygon(s, rgba, [(px - x0, py - y0) for px, py in pts], width); g.screen.blit(s, (x0, y0))


def _acircle(cx, cy, r, rgba, width=0):
    r = int(r)
    if r < 2 or r > 700: return
    s = pygame.Surface((2 * r + 6, 2 * r + 6), pygame.SRCALPHA); pygame.draw.circle(s, rgba, (r + 3, r + 3), r, width); g.screen.blit(s, (int(cx) - r - 3, int(cy) - r - 3))


def _cone(sx, sy, ax, ay, r, half, rgba, width=0, n=14):
    a0 = math.atan2(ay, ax); pts = [(sx, sy)]
    for k in range(n + 1):
        a = a0 - half + 2 * half * k / n; pts.append((sx + math.cos(a) * r, sy + math.sin(a) * r))
    _apoly(pts, rgba, width)


def _rect(sx, sy, ax, ay, length, wid, rgba, width=0):
    px, py = -ay * wid / 2, ax * wid / 2
    _apoly([(sx + px, sy + py), (sx + px + ax * length, sy + py + ay * length), (sx - px + ax * length, sy - py + ay * length), (sx - px, sy - py)], rgba, width)


def draw_ground(cx, cy, ox, oy):
    """Lapisan tanah: ring target, telegraf serangan musuh, pratinjau bidik skill. Digambar di bawah sprite."""
    P = g.P; t = T(); px, py = P.x - cx + ox, P.y - cy + oy
    tg = nearest_enemy(230)
    if tg:
        sx, sy = tg['pos'][0] - cx + ox, tg['pos'][1] - cy + oy; r = tg['rad'] + 6
        s = pygame.Surface((int(r * 2) + 4, int(r * 1.1)), pygame.SRCALPHA); pygame.draw.ellipse(s, (255, 70, 70, 190), s.get_rect(), 3); g.screen.blit(s, (int(sx - r - 2), int(sy - r * 0.55 + 2)))
    for e in g.HM:
        if not e['alive'] or e['st'] != 'wind': continue
        sx, sy = e['pos'][0] - cx + ox, e['pos'][1] - cy + oy; ax, ay = e['aim']; sk = e['sk']; p = min(1.0, (t - e['w0']) / float(WIND[sk]))
        fill, edge = (255, 50, 50, 46), (255, 80, 70, 210); inner = (255, 60, 50, 105)
        if sk == 'swing':
            R = e['reach'] + 16; _cone(sx, sy, ax, ay, R, 1.1, fill); _cone(sx, sy, ax, ay, R * p, 1.1, inner); _cone(sx, sy, ax, ay, R, 1.1, edge, 2)
        elif sk == 'dash':
            L = DASH_V * 0.38; W_ = (e['rad'] + 22) * 2; _rect(sx, sy, ax, ay, L, W_, fill); _rect(sx, sy, ax, ay, L * p, W_, inner); _rect(sx, sy, ax, ay, L, W_, edge, 2)
        elif sk in ('shot', 'fan'):
            for a in ((-0.32, 0.0, 0.32) if sk == 'fan' else (0.0,)):
                c, s_ = math.cos(a), math.sin(a); bx, by = ax * c - ay * s_, ax * s_ + ay * c
                pygame.draw.line(g.screen, (255, 90, 80), (int(sx), int(sy)), (int(sx + bx * 340 * p), int(sy + by * 340 * p)), 3)
        elif sk == 'slam':
            R = 120 if e['boss'] else 100; _acircle(sx, sy, R, fill); _acircle(sx, sy, R * p, inner); _acircle(sx, sy, R, edge, 3)
        elif sk == 'leap' and e['tp']:
            tx, ty = e['tp'][0] - cx + ox, e['tp'][1] - cy + oy; R = 108
            _acircle(tx, ty, R, fill); _acircle(tx, ty, R * p, inner); _acircle(tx, ty, R, edge, 3)
            pygame.draw.line(g.screen, (255, 90, 80), (int(sx), int(sy)), (int(tx), int(ty)), 2)
    for fid, d in C['drag'].items():   # pratinjau bidik saat jari menahan tombol skill
        s_ = SK[d['i']]
        if g.P.lv < s_['lv'] or t < C['cd'][d['i']]: continue
        ax, ay = aim_dir(d['aim'], 320 if d['i'] == 1 else 230); col = s_['col']
        if s_['aim'] == 'cone': _cone(px, py, ax, ay, SLASH_R, SLASH_HALF, col + (50,)); _cone(px, py, ax, ay, SLASH_R, SLASH_HALF, col + (200,), 2)
        elif s_['aim'] == 'line': _rect(px, py, ax, ay, DASH_DIST, 64, col + (50,)); _rect(px, py, ax, ay, DASH_DIST, 64, col + (200,), 2)
        else:
            R = QUAKE_R if d['i'] == 2 else ULT_R; _acircle(px, py, R, col + (45,)); _acircle(px, py, R, col + (200,), 3)
    if t < C['ult_until']:
        k = (C['ult_until'] - t) / float(ULT_MS); _acircle(px, py, ULT_R, SK[3]['col'] + (int(40 + 30 * math.sin(t / 60.0)),)); _acircle(px, py, ULT_R, SK[3]['col'] + (170,), 2)


_TINT = {}


def _tinted(im, rgb, key):
    k = (id(im), key); s = _TINT.get(k)
    if s is None:
        if len(_TINT) > 80: _TINT.clear()
        s = im.copy(); s.fill(rgb + (0,), special_flags=pygame.BLEND_RGB_ADD); _TINT[k] = s
    return s


def enemy_img(e, im):
    """Sprite musuh + kilatan putih saat terkena, dan gemetar saat stun."""
    t = T()
    if t < e['hit']: return _tinted(im, (150, 150, 150), 'w')
    if e['st'] == 'wind':   # memerah saat bersiap menyerang
        p = (t - e['w0']) / float(WIND[e['sk']])
        if (int(t / 90) % 2) == 0 and p > 0.4: return _tinted(im, (90, 0, 0), 'r')
    return im


_POSE = {}


def player_img(im):
    t = T(); P = g.P; s = C['swing']; res = im
    if C['dash'] or (s and t < s['t0'] + s['dur'] * 0.75):
        base = g.BAT_ATK
        if base is not None and (C['dash'] or abs((s or C['dash'])['ax']) >= 0.35 or (s or C['dash'])['ay'] > 0):
            k = id(base); pose = _POSE.get(k)
            if pose is None:
                _POSE.clear(); pose = _POSE[k] = pygame.transform.smoothscale(base, (max(1, base.get_width() // 3), max(1, base.get_height() // 3)))
            ax = (C['dash'] or s)['ax']; res = pygame.transform.flip(pose, True, False) if ax < 0 else pose
    if t < C['flash'] and (int(t / 70) % 2) == 0: res = _tinted(res, (120, 0, 0), 'p')
    if C['dash'] and t < C['inv']:
        res = res.copy(); res.set_alpha(150)      # kebal & transparan saat Terjang Badai
    return res


def _bar(x, y, w, h, v, m, col):
    x, y, w, h = int(x), int(y), int(w), max(2, int(h)); rad = max(1, h // 2)
    pygame.draw.rect(g.screen, (4, 6, 16), (x - 2, y - 2, w + 4, h + 4), border_radius=rad + 2)
    pygame.draw.rect(g.screen, (30, 36, 62), (x - 1, y - 1, w + 2, h + 2), border_radius=rad + 1)
    k = max(0.0, min(1.0, v / float(max(1, m)))); fw = int(w * k)
    if fw > 0:
        g.screen.blit(g.vgrad(fw, h, g.mix(col, (255, 255, 255), 0.35), g.mix(col, (0, 0, 0), 0.25), rad), (x, y))
        if h >= 5: g.screen.blit(g.gloss(fw, h, rad, 90), (x, y))


def draw_over(cx, cy, ox, oy):
    """Lapisan atas: efek tebasan, proyektil, bar HP, angka damage."""
    P = g.P; t = T(); scr = g.screen
    for f in C['fx']:
        k = (t - f['t0']) / float(f['dur']); sx, sy = f['x'] - cx + ox, f['y'] - cy + oy; kd = f['k']
        if kd == 'slash':
            a = math.atan2(f['ay'], f['ax']); half = f['half']; r = f['r']; sweep = min(1.0, k * 1.6); n = 12
            a_end = a - half + 2 * half * sweep; a_beg = a - half; pts = []
            for i in range(n + 1): pts.append((sx + math.cos(a_beg + (a_end - a_beg) * i / n) * r, sy - 24 + math.sin(a_beg + (a_end - a_beg) * i / n) * r * 0.9))
            for i in range(n, -1, -1): pts.append((sx + math.cos(a_beg + (a_end - a_beg) * i / n) * r * 0.62, sy - 24 + math.sin(a_beg + (a_end - a_beg) * i / n) * r * 0.55))
            _apoly(pts, f['col'] + (int(220 * (1 - k)),))
        elif kd == 'ring':
            r = f['r'] * (0.25 + 0.75 * min(1.0, k * 1.5)); _acircle(sx, sy, r, f['col'] + (int(210 * (1 - k)),), 5); _acircle(sx, sy, r * 0.85, f['col'] + (int(70 * (1 - k)),))
        elif kd == 'spark':
            for i in range(6):
                a = i * 1.047 + f['x']; d = 6 + 20 * k; pygame.draw.line(scr, f['col'], (int(sx + math.cos(a) * d * 0.4), int(sy - 24 + math.sin(a) * d * 0.4)), (int(sx + math.cos(a) * d), int(sy - 24 + math.sin(a) * d)), 2)
        elif kd == 'ghost':
            im = f['im'].copy(); im.set_alpha(int(220 * (1 - k))); scr.blit(im, (int(sx - im.get_width() / 2), int(sy - im.get_height() + 6 - 18 * k)))
        elif kd == 'ghostp':
            _acircle(sx, sy - 22, 16 * (1 - k) + 4, SK[1]['col'] + (int(110 * (1 - k)),))
    for p in C['proj']:
        sx, sy = p['x'] - cx + ox, p['y'] - cy + oy - 26; col = p['col']
        _acircle(sx, sy, p['r'] + 6, col + (70,)); _acircle(sx, sy, p['r'], col + (230,)); _acircle(sx, sy, p['r'] * 0.45, (255, 255, 255, 240))
        pygame.draw.line(scr, col, (int(sx), int(sy)), (int(sx - p['vx'] * 0.06), int(sy - p['vy'] * 0.06)), 4)
    if t < C['ult_until']:   # bilah berputar
        for i in range(3):
            a = t / 90.0 + i * 2.094; bx, by = P.x - cx + ox + math.cos(a) * ULT_R * 0.7, P.y - cy + oy - 24 + math.sin(a) * ULT_R * 0.55
            _acircle(bx, by, 14, SK[3]['col'] + (210,)); _acircle(bx, by, 7, (255, 255, 255, 240))
    for e in g.HM:   # bar HP musuh
        if not bar_shown(e): continue
        sx, sy = e['pos'][0] - cx + ox, e['pos'][1] - cy + oy
        if sx < -100 or sx > g.W + 100 or sy < -60 or sy > g.H + 160: continue
        w = 92 if e['boss'] else 46; _bar(sx - w / 2, sy - e['h'] - 10, w, 6, e['hp'], e['maxhp'], g.C_RED)
        if e['st'] == 'stun': g.txt("STUN", sx, sy - e['h'] - 28, g.F_XS, (255, 230, 120), True, 'c')
    if g.area == 'hunt':   # bar HP & MP di atas kepala pemain
        sx, sy = P.x - cx + ox, P.y - cy + oy
        _bar(sx - 30, sy - 92, 60, 6, P.hp, P.maxhp, g.C_GREEN); _bar(sx - 30, sy - 84, 60, 3, P.mp, P.maxmp, g.C_MP)
    for f in C['flt']:
        k = (t - f['t0']) / 1000.0; sx, sy = f['x'] - cx + ox, f['y'] - cy + oy - int(k * 54)
        g.txt(f['text'], sx, sy, g.F_L if f['big'] else g.F_MB, f['col'], True, 'c')


def draw_boss_bar():
    t = T(); b = None
    for e in g.HM:
        if e['alive'] and e['boss'] and e.get('chase'): b = e; break
    if not b: return
    w = min(460, g.W - 2 * g.SAFE_X - 440); w = max(w, 220); x = (g.W - w) // 2; y = g.SAFE_Y + 70
    g.panel(pygame.Rect(x - 22, y - 8, w + 44, 62), 220, 14, True)
    g.txt(b['m']['name'], g.W // 2, y - 2, g.F_SB, g.C_TEXT, True, 'c')
    _bar(x, y + 28, w, 14, b['hp'], b['maxhp'], g.C_RED)


# ------------------------------------------------------------------ tombol
_BC = {}


def _btn_bg(r, col):
    k = (r, col); s = _BC.get(k)
    if s is None:
        s = _BC[k] = g.disc(r, (30, 40, 78), (10, 14, 32), col, 236, 64)
    return s


def draw_buttons():
    t = T(); P = g.P; scr = g.screen
    if not BTN: build_layout()
    touch = g.show_touch()
    ax, ay, ar = BTN['A']; near = g.near_npc()
    scr.blit(_btn_bg(ar, g.C_GOLD if not near else (120, 220, 255)), (ax - ar - 4, ay - ar - 4))
    ic = g.icon_s('chat' if near else 'sword', int(ar * 0.95), g.C_GOLD); scr.blit(ic, (ax - ic.get_width() // 2, ay - ic.get_height() // 2))
    if 'atk' in g.fingers.values(): pygame.draw.circle(scr, (255, 255, 255), (ax, ay), ar, 3)
    if not near:
        for i in range(3):   # titik kombo
            on = (C['combo'] > i) and (t - C['combo_t'] < 900)
            pygame.draw.circle(scr, g.C_GOLD if on else (70, 78, 110), (ax - 14 + i * 14, ay + ar + 10), 5)
    cap = fit_cap("Bicara" if near else ("J" if not touch else ""))
    if cap: g.txt(cap, ax, ay + ar + 20, g.F_XS, g.C_TEXT, True, 'c')
    for i, s in enumerate(SK):
        bx, by, r = BTN['S%d' % i]; locked = P.lv < s['lv']; rem = max(0, C['cd'][i] - t); ready = (not locked) and rem == 0
        enough = P.mp >= s['mp']; col = s['col'] if (ready and enough) else ((90, 96, 120) if locked else tuple(int(c * 0.55) for c in s['col']))
        scr.blit(_btn_bg(r, col), (bx - r - 4, by - r - 4))
        ic = g.icon_s(s['ico'], int(r * 1.0), col if not locked else (110, 116, 140)); scr.blit(ic, (bx - ic.get_width() // 2, by - ic.get_height() // 2))
        if rem > 0 and not locked:
            frac = rem / float(s['cd']); a0 = -math.pi / 2; pts = [(bx, by)]
            for k in range(25): a = a0 + 2 * math.pi * frac * k / 24; pts.append((bx + math.cos(a) * (r - 2), by + math.sin(a) * (r - 2)))
            _apoly(pts, (0, 0, 0, 165))
            g.txt("%.1f" % (rem / 1000.0) if rem < 10000 else str(int(rem / 1000.0 + 0.99)), bx, by - g.F_SB.get_height() // 2, g.F_SB, (255, 255, 255), True, 'c')
        if C['cast_flash'][i] > t: pygame.draw.circle(scr, (255, 255, 255), (bx, by), r + 3, 4)
        elif ready and enough and (int(t / 400) % 2 == 0): pygame.draw.circle(scr, s['col'], (bx, by), r + 3, 2)
        if i in [d['i'] for d in C['drag'].values()]: pygame.draw.circle(scr, (255, 255, 255), (bx, by), r + 5, 3)
        g.txt("Lv %d" % s['lv'] if locked else "%d MP" % s['mp'], bx, by + r + 3, g.F_XS, (255, 150, 150) if (locked or not enough) else g.C_MP, True, 'c')
        if not touch: g.txt(s['key'], bx - r + 6, by - r + 2, g.F_XS, (255, 255, 255), True, 'c')
    bx, by, r = BTN['B']; heal = P.hp < P.maxhp or P.mp < P.maxmp; rem = max(0, C['pot_ready'] - t)
    scr.blit(_btn_bg(r, (150, 210, 255) if heal else (80, 90, 120)), (bx - r - 4, by - r - 4))
    ic = g.icon_s('potion', int(r * 0.95), (150, 210, 255)); scr.blit(ic, (bx - ic.get_width() // 2, by - ic.get_height() // 2))
    if rem > 0: _acircle(bx, by, r - 2, (0, 0, 0, 150))
    if C['pot_flash'] > t: pygame.draw.circle(scr, (255, 255, 255), (bx, by), r + 3, 3)
    n = sum(c for k_, c in P.bag if g.ITEMS[k_]['type'] == 'use' and (g.ITEMS[k_].get('hp') or g.ITEMS[k_].get('mp')))
    g.txt("Ramuan x%d" % n, bx, by + r + 3, g.F_XS, g.C_TEXT, True, 'c')
    draw_boss_bar()


def fit_cap(t): return t
