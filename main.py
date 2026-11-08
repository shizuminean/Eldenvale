# -*- coding: utf-8 -*-
"""Eldenvale RPG - Python + pygame (PC & Android).

Bagian berkas:  1 inti & helper gambar | 2 aset | 3 dunia & state | 4 logika game
                5 layar (title, HUD, dialog, menu, tas) | 6 input | 7 loop utama   (battle real-time: combat.py)
"""
import os, sys, json, math, random, copy, traceback, time as _pytime
from collections import deque
from ai_rumor import fetch_async, pop_rumor
import daily_quest

os.environ.setdefault('SDL_ANDROID_TRAP_BACK_BUTTON', '1')    # tombol Back tidak menutup aplikasi
import pygame
from data import *
import village as V
import combat

VERSION = '1.7.0'
BASE = os.path.dirname(os.path.abspath(__file__))
A = lambda *p: os.path.join(BASE, 'assets', *p)
ANDROID = 'ANDROID_ARGUMENT' in os.environ or 'ANDROID_PRIVATE' in os.environ


def _writable(d):
    try:
        if not d: return False
        os.makedirs(d, exist_ok=True)
        t = os.path.join(d, '.wtest')
        with open(t, 'w') as f: f.write('1')
        os.remove(t)
        return True
    except Exception:
        return False


DATA = next((d for d in ((os.environ.get('ANDROID_PRIVATE') if ANDROID else None), BASE, os.path.expanduser('~')) if _writable(d)), BASE)
SAVE, SETF, LOGF = (os.path.join(DATA, n) for n in ('save.json', 'settings.json', 'crash.log'))


def log_exc(where=''):
    msg = traceback.format_exc()
    try: sys.stderr.write(f"[eldenvale] {where}\n{msg}\n")
    except Exception: pass
    try:
        if os.path.exists(LOGF) and os.path.getsize(LOGF) > 200000: os.remove(LOGF)
        with open(LOGF, 'a') as f: f.write(f"--- {_pytime.strftime('%Y-%m-%d %H:%M:%S')} {where}\n{msg}\n")
    except Exception: pass
    return msg


# ---------------- setelan ----------------
S = {'fx': True, 'fps': 60, 'show_fps': False, 'shadows': True, 'names': True, 'wander': True, 'shake': True,
     'touch': 'auto', 'tsize': 1, 'talpha': 1, 'speed': 1}
S0 = dict(S)


def load_settings():
    try:
        with open(SETF) as f: d = json.load(f)
        if isinstance(d, dict):
            for key in S0:
                if key in d: S[key] = d[key]
    except Exception: pass


def save_settings():
    try:
        with open(SETF, 'w') as f: json.dump(S, f)
    except Exception: pass


# ---------------- layar ----------------
W, H = 1280, 720
SAFE_X, SAFE_Y = 26, 14
screen = None
clock = None


def pick_size():
    """Kanvas logika: tinggi tetap, lebar mengikuti rasio layar HP supaya tidak ada yang terpotong."""
    env = os.environ.get('ELDEN_SIZE')
    if env:
        try:
            a, b = env.lower().split('x'); return int(a), int(b)
        except Exception: pass
    if not ANDROID: return 1280, 720
    try: dw, dh = pygame.display.get_desktop_sizes()[0]
    except Exception: dw, dh = 16, 9
    ratio = max(dw, dh) / float(max(1, min(dw, dh)))
    h = 540
    w = int(round(h * ratio / 2.0)) * 2
    if w < 960: w = 960; h = min(780, int(round(960 / ratio / 2.0)) * 2)   # layar lebih 'kotak' (tablet): tambah tinggi, bukan potong
    return min(1260, w), h


def make_screen():
    global screen
    base = (pygame.FULLSCREEN if ANDROID else pygame.RESIZABLE) | pygame.SCALED
    for fl, vs in ((base, True), (base, False), (pygame.FULLSCREEN if ANDROID else 0, False), (0, False)):
        try:
            screen = pygame.display.set_mode((W, H), fl, vsync=1) if vs else pygame.display.set_mode((W, H), fl)
            return
        except Exception:
            log_exc('set_mode')
    raise RuntimeError('Tidak bisa membuat layar')


# ---------------- tema ----------------
C_BG, C_GOLD, C_GOLD_D = (9, 13, 28), (243, 200, 108), (176, 132, 58)
C_TEXT, C_MUTE, C_SHADOW = (240, 243, 252), (158, 170, 202), (4, 7, 18)
C_GREEN, C_RED, C_MP, C_XP, C_BLUE = (84, 212, 122), (236, 86, 94), (92, 152, 255), (246, 198, 84), (84, 140, 244)
C_INK, C_INK2 = (62, 42, 22), (112, 84, 52)          # teks di atas kertas perkamen (tas)


class NullFont:
    """Cadangan terakhir bila font gagal dimuat: game tetap jalan tanpa teks."""
    def __init__(self, s): self.h = int(s * 1.4)
    def render(self, t, aa, col): return pygame.Surface((max(1, len(t) * self.h // 2), self.h), pygame.SRCALPHA)
    def size(self, t): return (len(t) * self.h // 2, self.h)
    def get_height(self): return self.h


def mkfont(fname, size):
    for src in (A('fonts', fname), None):
        try: return pygame.font.Font(src, size)
        except Exception: log_exc('font ' + fname)
    return NullFont(size)


F_XS = F_S = F_SB = F_M = F_MB = F_L = F_XL = F_T = None


def init_fonts():
    global F_XS, F_S, F_SB, F_M, F_MB, F_L, F_XL, F_T
    F_XS, F_S, F_SB = mkfont('Poppins-Medium.ttf', 12), mkfont('Poppins-Regular.ttf', 15), mkfont('Poppins-Bold.ttf', 15)
    F_M, F_MB, F_L = mkfont('Poppins-Medium.ttf', 18), mkfont('Poppins-Bold.ttf', 18), mkfont('Poppins-Bold.ttf', 25)
    F_XL, F_T = mkfont('Poppins-Bold.ttf', 36), mkfont('Poppins-Bold.ttf', 68)


# ---------------- cache (kunci anti-lag) ----------------
_TC, _PC, _GC, _IC, _II, _MC, _HC, _VC, _TG = ({} for _ in range(9))


def clamp(v, a, b): return a if v < a else (b if v > b else v)
def mix(c1, c2, t): return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def rt(t, font, col):
    k = (t, id(font), col); s = _TC.get(k)
    if s is None:
        if len(_TC) > 1200: _TC.clear()
        s = _TC[k] = font.render(t, True, col) if t else pygame.Surface((1, font.get_height()), pygame.SRCALPHA)
    return s


def txt(t, x, y, font=None, col=C_TEXT, shadow=True, anchor='l'):
    font = font or F_M; s = rt(t, font, col); w = s.get_width()
    if anchor == 'c': x -= w // 2
    elif anchor == 'r': x -= w
    if shadow: screen.blit(rt(t, font, C_SHADOW), (x, y + 2))
    screen.blit(s, (x, y))
    return w


def fit(t, font, w):
    if font.size(t)[0] <= w: return t
    while t and font.size(t + '...')[0] > w: t = t[:-1]
    return t.rstrip() + '...'


def _hard(cur, font, w, out):
    while len(cur) > 1 and font.size(cur)[0] > w:
        k = len(cur)
        while k > 1 and font.size(cur[:k])[0] > w: k -= 1
        out.append(cur[:k]); cur = cur[k:]
    return cur


def wrap(t, font, w):
    out = []
    for para in t.split('\n'):
        cur = ''
        for wd in para.split(' '):
            trial = wd if not cur else cur + ' ' + wd
            if font.size(trial)[0] <= w: cur = trial
            else:
                if cur: out.append(cur)
                cur = _hard(wd, font, w, out)
        out.append(cur)
    return out


def vgrad(w, h, top, bot, rad=0, alpha=255):
    w, h = max(1, int(w)), max(1, int(h)); k = (w, h, top, bot, rad, alpha); s = _GC.get(k)
    if s is None:
        if len(_GC) > 500: _GC.clear()
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        for y in range(h): pygame.draw.line(s, mix(top, bot, y / max(1, h - 1)) + (alpha,), (0, y), (w, y))
        if rad > 0:
            m = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.rect(m, (255, 255, 255, 255), (0, 0, w, h), border_radius=rad)
            s.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        _GC[k] = s
    return s


def shape(r, fill=None, rad=8, border=None, bw=2):
    """Kotak membulat semi-transparan (fill & border boleh RGBA)."""
    r = pygame.Rect(r)
    if r.w <= 0 or r.h <= 0: return
    k = (r.w, r.h, fill, rad, border, bw); s = _PC.get(k)
    if s is None:
        if len(_PC) > 600: _PC.clear()
        s = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        if fill: pygame.draw.rect(s, fill, (0, 0, r.w, r.h), border_radius=rad)
        if border: pygame.draw.rect(s, border, (0, 0, r.w, r.h), bw, border_radius=rad)
        _PC[k] = s
    screen.blit(s, r.topleft)


def panel(r, a=214, rad=14, gold=False):
    r = pygame.Rect(r)
    if r.w <= 4 or r.h <= 4: return
    k = ('panel', r.w, r.h, a, rad, gold); s = _PC.get(k)
    if s is None:
        if len(_PC) > 600: _PC.clear()
        s = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        s.blit(vgrad(r.w, r.h, (24, 33, 64), (11, 16, 34), rad, a), (0, 0))
        pygame.draw.rect(s, (C_GOLD + (235,)) if gold else (122, 144, 206, 130), (0, 0, r.w, r.h), 2, border_radius=rad)
        pygame.draw.line(s, (255, 255, 255, 24), (rad, 3), (max(rad, r.w - rad), 3))
        _PC[k] = s
    screen.blit(s, r.topleft)


def veil(a, col=(6, 9, 20)):
    k = (W, H, a, col); s = _VC.get(k)
    if s is None:
        if len(_VC) > 24: _VC.clear()
        s = pygame.Surface((W, H), pygame.SRCALPHA); s.fill(col + (a,)); _VC[k] = s
    screen.blit(s, (0, 0))


def fade_v(r, a_top, a_bot, col=(5, 8, 20)):
    """Gradien transparansi vertikal (untuk keterbacaan teks di atas peta)."""
    r = pygame.Rect(r); k = ('fv', r.w, r.h, a_top, a_bot, col); s = _GC.get(k)
    if s is None:
        s = pygame.Surface((max(1, r.w), max(1, r.h)), pygame.SRCALPHA)
        for y in range(r.h): pygame.draw.line(s, col + (int(a_top + (a_bot - a_top) * y / max(1, r.h - 1)),), (0, y), (r.w, y))
        _GC[k] = s
    screen.blit(s, r.topleft)


def bar(x, y, w, h, v, m, col, label=None):
    r = pygame.Rect(x, y, w, h); rad = h // 2
    shape(r, (6, 9, 20, 225), rad, (96, 112, 160, 150), 1)
    fw = int((w - 2) * clamp(v / float(max(1, m)), 0.0, 1.0))
    if fw >= 3: screen.blit(vgrad(fw, h - 2, mix(col, (255, 255, 255), 0.32), mix(col, (0, 0, 0), 0.22), max(1, rad - 1)), (x + 1, y + 1))
    if label: txt(label, x + w // 2, y + (h - F_XS.get_height()) // 2, F_XS, C_TEXT, True, 'c')


BTN = {'primary': ((98, 154, 255), (46, 92, 204), (170, 204, 255)), 'gold': ((255, 218, 128), (208, 152, 58), (255, 238, 176)),
       'dark': ((52, 66, 112), (28, 36, 72), (118, 136, 198)), 'danger': ((242, 108, 116), (180, 52, 64), (255, 170, 176)),
       'off': ((66, 72, 94), (44, 48, 66), (96, 102, 126))}


def button(r, label, kind='primary', sel=False, font=None, icon=None, cap=None):
    r = pygame.Rect(r); top, bot, edge = BTN[kind]
    if sel: top, bot = mix(top, (255, 255, 255), 0.2), mix(bot, (255, 255, 255), 0.12)
    screen.blit(vgrad(r.w, r.h, top, bot, 12), r.topleft)
    shape(r, None, 12, edge + ((255,) if sel else (170,)), 3 if sel else 2)
    col = (44, 30, 8) if kind == 'gold' else C_TEXT; font = font or F_MB
    ic = int(min(r.h * 0.5, 30)) if icon else 0; lw = font.size(label)[0] if label else 0
    tot = lw + (ic + 10 if icon and label else ic)
    x = r.centerx - tot // 2
    if icon: screen.blit(icon_s(icon, ic, col), (x, r.centery - ic // 2)); x += ic + (10 if label else 0)
    if label:
        ty = r.centery - font.get_height() // 2 - (7 if cap else 0)
        txt(label, x, ty, font, col, kind != 'gold')
        if cap: txt(cap, r.centerx, ty + font.get_height() - 3, F_XS, mix(col, (0, 0, 0), 0.2) if kind == 'gold' else C_MUTE, False, 'c')


def tag(text, col=(255, 240, 190), dot=None):
    k = (text, col, dot); s = _TG.get(k)
    if s is None:
        if len(_TG) > 400: _TG.clear()
        t = rt(text, F_XS, col); pad = 9; dw = 14 if dot else 0; w = t.get_width() + pad * 2 + dw; h = 22
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(s, (8, 12, 26, 190), (0, 0, w, h), border_radius=11)
        pygame.draw.rect(s, (255, 255, 255, 46), (0, 0, w, h), 1, border_radius=11)
        x = pad
        if dot: pygame.draw.circle(s, dot + (255,), (pad + 3, h // 2), 4); x += dw
        s.blit(t, (x, (h - t.get_height()) // 2 + 1)); _TG[k] = s
    return s


# ---------------- ikon vektor (digambar 4x lalu diperkecil = halus, tanpa emoji) ----------------
def _I(s, c, u): return lambda x, y: (int(x * u), int(y * u))


def _ic_bag(s, c, u):
    pygame.draw.rect(s, c, (int(3.5 * u), int(8 * u), int(17 * u), int(13.5 * u)), border_radius=int(3.5 * u))
    pygame.draw.rect(s, c, (int(7 * u), int(2.5 * u), int(10 * u), int(10 * u)), max(1, int(2.2 * u)), border_radius=int(4 * u))
    pygame.draw.rect(s, (0, 0, 0, 0), (int(9.5 * u), int(12.5 * u), int(5 * u), int(3.6 * u)), border_radius=int(1.2 * u))


def _ic_gear(s, c, u):
    cx = cy = 12 * u
    for i in range(8):
        a = i * math.pi / 4
        pts = [(int(cx + math.cos(a + da) * rr * u), int(cy + math.sin(a + da) * rr * u)) for da, rr in ((-0.21, 7.0), (-0.21, 10.8), (0.21, 10.8), (0.21, 7.0))]
        pygame.draw.polygon(s, c, pts)
    pygame.draw.circle(s, c, (int(cx), int(cy)), int(8.3 * u))
    pygame.draw.circle(s, (0, 0, 0, 0), (int(cx), int(cy)), int(3.5 * u))


def _ic_save(s, c, u):
    pygame.draw.rect(s, c, (int(4 * u), int(4 * u), int(16 * u), int(16 * u)), border_radius=int(2.4 * u))
    pygame.draw.rect(s, (0, 0, 0, 0), (int(7.5 * u), int(4 * u), int(8 * u), int(5.2 * u)))
    pygame.draw.rect(s, (0, 0, 0, 0), (int(7.5 * u), int(13 * u), int(9 * u), int(7 * u)), border_radius=int(1 * u))
    pygame.draw.rect(s, c, (int(9 * u), int(14.5 * u), int(6 * u), int(5.5 * u)))


def _ic_load(s, c, u):
    w = max(1, int(2.4 * u)); p = lambda x, y: (int(x * u), int(y * u))
    pygame.draw.lines(s, c, False, [p(4, 14), p(4, 20), p(20, 20), p(20, 14)], w)
    pygame.draw.line(s, c, p(12, 3.5), p(12, 13), max(1, int(3 * u)))
    pygame.draw.polygon(s, c, [p(6.5, 10.5), p(17.5, 10.5), p(12, 16.5)])


def _ic_close(s, c, u):
    p = lambda x, y: (int(x * u), int(y * u)); w = max(1, int(3 * u))
    pygame.draw.line(s, c, p(6, 6), p(18, 18), w); pygame.draw.line(s, c, p(18, 6), p(6, 18), w)


def _ic_chat(s, c, u):
    pygame.draw.rect(s, c, (int(3 * u), int(4 * u), int(18 * u), int(12.5 * u)), border_radius=int(4 * u))
    pygame.draw.polygon(s, c, [(int(7 * u), int(15 * u)), (int(7 * u), int(21 * u)), (int(13.5 * u), int(15 * u))])
    for x in (8, 12, 16): pygame.draw.circle(s, (0, 0, 0, 0), (int(x * u), int(10.2 * u)), max(1, int(1.2 * u)))


def _ic_potion(s, c, u):
    pygame.draw.circle(s, c, (int(12 * u), int(15.2 * u)), int(6.8 * u))
    pygame.draw.rect(s, c, (int(9.6 * u), int(4.5 * u), int(4.8 * u), int(6 * u)))
    pygame.draw.rect(s, c, (int(8.4 * u), int(2.6 * u), int(7.2 * u), int(2.6 * u)), border_radius=int(1 * u))
    pygame.draw.line(s, (0, 0, 0, 0), (int(7.6 * u), int(15.6 * u)), (int(16.4 * u), int(15.6 * u)), max(1, int(1.3 * u)))


def _ic_sword(s, c, u):
    p = lambda x, y: (int(x * u), int(y * u))
    pygame.draw.line(s, c, p(7.5, 16.5), p(19, 5), max(1, int(3.2 * u)))
    pygame.draw.polygon(s, c, [p(19, 2.6), p(21.4, 5), p(19.6, 6.6), p(17.4, 4.4)])
    pygame.draw.line(s, c, p(5.2, 13.6), p(10.4, 18.8), max(1, int(2.6 * u)))
    pygame.draw.line(s, c, p(7.6, 16.4), p(4.6, 19.4), max(1, int(2.8 * u)))
    pygame.draw.circle(s, c, p(4.2, 19.8), int(1.7 * u))


def _ic_bolt(s, c, u):
    pygame.draw.polygon(s, c, [(int(x * u), int(y * u)) for x, y in ((13.6, 2), (5, 13.4), (11, 13.4), (9, 22), (19, 10), (13, 10))])


def _ic_run(s, c, u):
    p = lambda x, y: (int(x * u), int(y * u)); w = max(1, int(3 * u))
    pygame.draw.lines(s, c, False, [p(4.5, 6), p(10.5, 12), p(4.5, 18)], w); pygame.draw.lines(s, c, False, [p(12.5, 6), p(18.5, 12), p(12.5, 18)], w)


def _ic_chev_d(s, c, u):
    pygame.draw.lines(s, c, False, [(int(5 * u), int(8.5 * u)), (int(12 * u), int(15.5 * u)), (int(19 * u), int(8.5 * u))], max(1, int(3 * u)))


def _ic_chev_u(s, c, u):
    pygame.draw.lines(s, c, False, [(int(5 * u), int(15.5 * u)), (int(12 * u), int(8.5 * u)), (int(19 * u), int(15.5 * u))], max(1, int(3 * u)))


def _ic_chev_r(s, c, u):
    pygame.draw.lines(s, c, False, [(int(8.5 * u), int(5 * u)), (int(15.5 * u), int(12 * u)), (int(8.5 * u), int(19 * u))], max(1, int(3 * u)))


def _ic_coin(s, c, u):
    pygame.draw.circle(s, c, (int(12 * u), int(12 * u)), int(10 * u))
    pygame.draw.circle(s, (0, 0, 0, 0), (int(12 * u), int(12 * u)), int(6.6 * u), max(1, int(1.6 * u)))
    pygame.draw.rect(s, (0, 0, 0, 0), (int(10.8 * u), int(8 * u), int(2.4 * u), int(8 * u)))


def _ic_diamond(s, c, u):
    pygame.draw.polygon(s, c, [(int(12 * u), int(2.5 * u)), (int(20 * u), int(12 * u)), (int(12 * u), int(21.5 * u)), (int(4 * u), int(12 * u))])


def _ic_play(s, c, u):
    pygame.draw.polygon(s, c, [(int(7 * u), int(4 * u)), (int(20 * u), int(12 * u)), (int(7 * u), int(20 * u))])


def _ic_home(s, c, u):
    pygame.draw.polygon(s, c, [(int(12 * u), int(3 * u)), (int(21.5 * u), int(11.5 * u)), (int(2.5 * u), int(11.5 * u))])
    pygame.draw.rect(s, c, (int(5 * u), int(11 * u), int(14 * u), int(9.5 * u)))
    pygame.draw.rect(s, (0, 0, 0, 0), (int(10 * u), int(14.5 * u), int(4 * u), int(6 * u)))


ICONS = {'bag': _ic_bag, 'gear': _ic_gear, 'save': _ic_save, 'load': _ic_load, 'close': _ic_close, 'chat': _ic_chat, 'potion': _ic_potion,
         'sword': _ic_sword, 'bolt': _ic_bolt, 'run': _ic_run, 'down': _ic_chev_d, 'up': _ic_chev_u, 'right': _ic_chev_r, 'coin': _ic_coin,
         'diamond': _ic_diamond, 'play': _ic_play, 'home': _ic_home}


def icon_s(name, size, col=(255, 255, 255)):
    size = max(4, int(size)); k = (name, size, col); s = _IC.get(k)
    if s is None:
        if len(_IC) > 500: _IC.clear()
        big = size * 4; s = pygame.Surface((big, big), pygame.SRCALPHA)
        fn = ICONS.get(name)
        if fn: fn(s, col + (255,), big / 24.0)
        s = _IC[k] = pygame.transform.smoothscale(s, (size, size))
    return s


# ============================================================ 2. ASET
def _ph(w=48, h=64):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(s, (214, 92, 140, 150), (0, 0, w, h), border_radius=6)
    pygame.draw.rect(s, (255, 255, 255, 200), (0, 0, w, h), 2, border_radius=6)
    return s


def img(*p, alpha=True):
    """Muat gambar; kalau gagal, kembalikan penanda kotak supaya game tetap jalan (tidak crash)."""
    try:
        s = pygame.image.load(A(*p))
        return s.convert_alpha() if alpha else s.convert()
    except Exception:
        log_exc('img ' + '/'.join(p)); return _ph()


def load(name, h=None, scale=None):
    s = img(name)
    if scale: size = (max(1, int(s.get_width() * scale)), max(1, int(s.get_height() * scale)))
    else: size = (max(1, int(s.get_width() * h / max(1, s.get_height()))), int(h))
    return pygame.transform.smoothscale(s, size)


def icon(iid, size):
    k = (iid, size); s = _II.get(k)
    if s is None:
        im = img('items', f"it_{ITEMS[iid]['icon']}.png"); sc = size / float(max(im.get_size()))
        s = _II[k] = pygame.transform.smoothscale(im, (max(1, int(im.get_width() * sc)), max(1, int(im.get_height() * sc))))
    return s


def mon_img(m, h=None):
    h = h or m['size']; k = (m['img'], h); s = _MC.get(k)
    if s is None:
        im = img('mon', f"m_{m['img']}.png"); sc = h / float(max(1, im.get_height()))
        s = _MC[k] = pygame.transform.smoothscale(im, (max(1, int(im.get_width() * sc)), int(h)))
    return s


class Sheet:
    def __init__(self, who, h=66, scale=None):
        self.f, self.ff, self.idle, self.idlef = {}, {}, {}, {}
        for d in ('down', 'side', 'up'):
            fr, i = [], 0
            while os.path.exists(A(f'{who}_{d}_{i}.png')):
                fr.append(load(f'{who}_{d}_{i}.png', h, scale)); i += 1
            if not fr: fr = [_ph(36, int(h or 66))]
            if len(fr) == 1: fr.append(fr[0])
            self.f[d] = fr; self.ff[d] = [pygame.transform.flip(x, True, False) for x in fr]
            p = f'{who}_idle_{d}.png'
            self.idle[d] = load(p, h, scale) if os.path.exists(A(p)) else fr[0]
            self.idlef[d] = pygame.transform.flip(self.idle[d], True, False)

    def get(self, d, step, flip=False, moving=True):
        if not moving: return (self.idlef if flip else self.idle)[d]
        fr = (self.ff if flip else self.f)[d]
        return fr[int(step) % len(fr)]


SHEETS = {}


def sheet_for(who):
    if who not in SHEETS: SHEETS[who] = Sheet(who, 70)
    return SHEETS[who]


MAP = HMAP = SHADOW = hero = BAT_IDLE = BAT_ATK = PORT_HUD = None
MW = MH = HW = HH = HGW = HGH = 0
HGRID = []
HS = 0.43
BLOCK, WILD, DOORR = [], [], {}

splash_state = dict(label='', p=0.0)


def splash(label, p):
    """Layar muat: tampil seketika supaya game tidak terlihat 'hitam' / mati saat aset dimuat."""
    try:
        pygame.event.pump()
        screen.fill(C_BG)
        screen.blit(vgrad(W, H, (22, 32, 66), (8, 11, 24)), (0, 0))
        txt("ELDENVALE", W // 2, H // 2 - 92, F_XL, C_GOLD, True, 'c')
        txt("Memuat dunia...", W // 2, H // 2 - 36, F_S, C_MUTE, False, 'c')
        bw = min(380, W - 120); bx = (W - bw) // 2
        bar(bx, H // 2 + 4, bw, 14, p, 1.0, C_GOLD)
        txt(label, W // 2, H // 2 + 28, F_XS, C_MUTE, False, 'c')
        pygame.display.flip()
    except Exception:
        log_exc('splash')


def load_world():
    global MAP, MW, MH, HMAP, HW, HH, HGW, HGH, HGRID, SHADOW, BLOCK, WILD, DOORR, DOORS, TOWN, GATE, GATE_OUT
    TOWN = V.build_town()                       # v1.5: desa dibangun lewat kode (tilemap + sprite)
    MAP = TOWN.ground; MW, MH = V.MW, V.MH
    BLOCK = list(TOWN.block); DOORS = TOWN.doors; GATE, GATE_OUT = TOWN.gate, TOWN.gate_out
    HMAP = img('hunt.png', alpha=False); HW, HH = HMAP.get_size()
    hm = img('hunt_mask.png', alpha=False); HGW, HGH = hm.get_size()
    HGRID = [[hm.get_at((i, j))[0] > 128 for i in range(HGW)] for j in range(HGH)]
    SHADOW = pygame.Surface((40, 16), pygame.SRCALPHA)
    pygame.draw.ellipse(SHADOW, (0, 0, 0, 96), SHADOW.get_rect())
    WILD = []   # tidak ada battle mendadak di desa; monster hanya di Hutan Berburu
    DOORR = {k_: pygame.Rect(*v_['trig']) for k_, v_ in DOORS.items()}
    for _n in NPCS: _n['pos'] = V.NPC_POS.get(_n['name'], _n['pos'])   # posisi NPC sudah divalidasi (tidak di dalam bangunan/tebing)


def make_portrait(d, zoom=1.0, dy=0.04, ci=None):
    ci = P.char if ci is None else ci
    base = img('chars', f'c{ci}_idle_down.png'); bw, bh = base.get_size()
    crop = base.subsurface((0, 0, bw, max(1, int(bh * 0.56)))).copy()
    sc = d * zoom / float(bw)
    crop = pygame.transform.smoothscale(crop, (max(1, int(bw * sc)), max(1, int(crop.get_height() * sc))))
    s = pygame.Surface((d, d), pygame.SRCALPHA)
    pygame.draw.circle(s, (38, 54, 112, 255), (d // 2, d // 2), d // 2)
    s.blit(crop, ((d - crop.get_width()) // 2, int(d * dy)))
    m = pygame.Surface((d, d), pygame.SRCALPHA); pygame.draw.circle(m, (255, 255, 255, 255), (d // 2, d // 2), d // 2)
    s.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return s


# ---------- v1.6: pilihan karakter pemain ----------
CHARS = [dict(name='Hana', title='Miko Bunga Merah'), dict(name='Selene', title='Penyihir Malam'),
         dict(name='Kaelen', title='Pengembara Berjubah'), dict(name='Ronan', title='Pemburu Bulu Putih')]
CHAR_SHEETS, CS_RAW, CS_SCL = {}, {}, {}
CS = dict(idx=0)


def char_sheet(ci):
    if ci not in CHAR_SHEETS: CHAR_SHEETS[ci] = Sheet(f'chars/c{ci}', scale=HS)
    return CHAR_SHEETS[ci]


def char_pic(ci, kind, f, h):
    """Gambar karakter untuk layar pilih (kind 'idle' atau 'down'), diskalakan ke tinggi h dan di-cache."""
    k = (ci, kind, f, h); s_ = CS_SCL.get(k)
    if s_ is None:
        rk = (ci, kind, f); raw = CS_RAW.get(rk)
        if raw is None: raw = CS_RAW[rk] = img('chars', f'c{ci}_idle_down.png' if kind == 'idle' else f'c{ci}_down_{f}.png')
        s_ = CS_SCL[k] = pygame.transform.smoothscale(raw, (max(1, int(raw.get_width() * h / float(max(1, raw.get_height())))), max(1, int(h))))
    return s_


def apply_char(ci):
    global hero, BAT_IDLE, BAT_ATK, PORT_HUD, PORT
    try: ci = int(ci)
    except Exception: ci = 0
    if not (0 <= ci < len(CHARS)): ci = 0
    P.char = ci; hero = char_sheet(ci)
    BAT_IDLE = load(f'chars/c{ci}_battle_idle.png', scale=HS * 3); BAT_ATK = load(f'chars/c{ci}_battle_atk.png', scale=HS * 3)
    PORT_HUD = make_portrait(60, ci=ci)
    INT_CACHE.clear()
    if PORT is not None: PORT = make_portrait(max(8, int(196 * US)), 1.02, 0.05, ci)


def load_sprites():
    global HS
    probe = img('chars', 'c0_idle_down.png'); HS = 76.0 / max(1, probe.get_height())
    apply_char(P.char)


# ---------- UI tas (seni kiri/kanan) : skala menyesuaikan layar ----------
US = 0.7
UL = UR_ = None
LX = LY = RX = RY = 0
CELLS, TABR, SLOTR = [], [], {}
TRASH = GOLDBAR = NAMEBOX = INFO = SET_AREA = CLOSE = pygame.Rect(0, 0, 1, 1)
PORT = None
PORT_C = (0, 0)
DIM0 = None
ROWH = 48


def Lr(x, y, w, h, o='L'):
    ox, oy = (LX, LY) if o == 'L' else (RX, RY)
    return pygame.Rect(ox + int(x * US), oy + int(y * US), int(w * US), int(h * US))


def load_ui():
    global US, UL, UR_, LX, LY, RX, RY, CELLS, TABR, SLOTR, TRASH, GOLDBAR, NAMEBOX, INFO, SET_AREA, CLOSE, PORT, PORT_C, DIM0
    US = min(0.74, (W - 2 * 76 - 12) / 1490.0, (H - 16) / 955.0)
    UL, UR_ = load('ui/ui_left.png', scale=US), load('ui/ui_right.png', scale=US)
    tw = UL.get_width() + UR_.get_width() + 12
    LX, LY = (W - tw) // 2, (H - UL.get_height()) // 2
    RX, RY = LX + UL.get_width() + 12, LY
    CELLS = [Lr(c, r, 98, 97) for r in (268, 382, 494, 608, 720) for c in (103, 217, 330, 444, 558, 671)]
    TABR = [Lr(x, 150, 106, 94) for x in (89, 217, 329, 441, 553, 666)]
    TRASH, GOLDBAR = Lr(689, 833, 82, 74), Lr(86, 836, 597, 68)
    SLOTR = {'helm': Lr(45, 333, 114, 112, 'R'), 'cloak': Lr(45, 454, 114, 112, 'R'), 'neck': Lr(45, 575, 114, 112, 'R'),
             'weapon': Lr(479, 333, 112, 112, 'R'), 'armor': Lr(479, 454, 112, 112, 'R'), 'boots': Lr(479, 575, 112, 112, 'R')}
    NAMEBOX, INFO = Lr(275, 124, 306, 170, 'R'), Lr(40, 708, 551, 171, 'R')
    SET_AREA = Lr(100, 262, 590, 548)
    CLOSE = pygame.Rect(W - 70 + 8, SAFE_Y + 6, 54, 54)
    PORT_C = (RX + int(150 * US), RY + int(205 * US))
    PORT = make_portrait(max(8, int(196 * US)), 1.02, 0.05, P.char)
    DIM0 = pygame.Surface(TABR[0].size, pygame.SRCALPHA); pygame.draw.rect(DIM0, (70, 70, 75, 200), DIM0.get_rect(), border_radius=10)


# ============================================================ 3. DUNIA & STATE
GATE, GATE_OUT = pygame.Rect(1340, 2036, 120, 30), (1400, 1990)   # diisi ulang oleh load_world()
DOORS, TOWN = {}, None
HEXIT, HENTRY = pygame.Rect(660, 892, 52, 24), (696, 830)
DOOR_NAME = {'inn': 'Penginapan', 'church': 'Gereja', 'potion': 'Toko Ramuan', 'smith': 'Pandai Besi', 'green': 'Rumah Nenek Wren', 'windmill': 'Guild Petualang'}
NPCS = [
    dict(name="Sir Aldric", who="n05", pos=(800, 330), kind="quest", r=40, still=True),
    dict(name="Mira", who="n27", pos=(700, 565), kind="girl", r=150),
    dict(name="Cale si Pedagang", who="n29", pos=(1010, 470), kind="chat", r=110,
         lines=["Barang dagangan terbaik ada di toko Orn dan Brom!", "Monster di Hutan Berburu menjatuhkan bahan yang laku mahal."]),
    dict(name="Anya", who="n19", pos=(585, 500), kind="chat", r=90,
         lines=["Aku pernah masuk gereja. Di dalamnya megah sekali!", "Ssst, kata orang ada Raja Slime di padang hijau Hutan Berburu."]),
    dict(name="Fenn si Pemanah", who="n14", pos=(1120, 520), kind="archer", r=130),
    dict(name="Kesatria Ines", who="n18", pos=(1000, 330), kind="chat", r=100,
         lines=["Aku berpatroli di sini setiap hari.", "Monster di Hutan Berburu bisa dilihat dari jauh. Hindari yang terlalu kuat!"]),
    dict(name="Madam Ruby", who="n11", pos=(900, 520), kind="seer", r=90,
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
NPCS.append(dict(name="Petani Tomo", who="n15", pos=(1190, 1742), kind="farmer", r=0, still=True))
for _n in NPCS: _n['pos'] = V.NPC_POS.get(_n['name'], _n['pos'])
HNPCS = [dict(name="Pemburu Rhea", who="n15", pos=(1345, 415), kind="camp", r=0, still=True)]
area = 'town'


def anpcs():
    if area != 'town': return HNPCS
    return [] if is_night() else NPCS   # v1.2: malam, penduduk tidur di penginapan


def init_npc(n):
    home = n.setdefault('home0', tuple(n['pos']))
    n.update(pos=list(home), home=home, d='down', flip=False, anim=0, moving=False, tgt=None,
             wait=pygame.time.get_ticks() + random.randint(500, 3500), spd=random.uniform(34, 52))


class P:
    x, y = float(V.SPAWN[0]), float(V.SPAWN[1])
    ix, iy = 0.0, 0.0
    d, step, flip, dist, moving = 'down', 0, False, 0.0, False
    lv, xp, gold = 1, 0, 60
    hp = maxhp = 60
    mp = maxmp = 20
    atk, df = 9, 3
    char = 0
    wl = 0
    slimes = 0
    quest = 0
    bag = []
    eq = {}
    tm = 420.0
    day = 1
    gq = {}
    farm = {}


DEFAULT = dict(x=float(V.SPAWN[0]), y=float(V.SPAWN[1]), lv=1, xp=0, gold=60, hp=60, maxhp=60, mp=20, maxmp=20, atk=9, df=3, wl=0, slimes=0, quest=0,
               bag=[['potion_hp', 3], ['potion_mp', 1], ['bread', 2], ['dagger', 1]] + [list(x) for x in START_SEEDS], tm=420.0, day=1, gq={}, farm={})
MAXBAG = 30
SAVE_KEYS = ['x', 'y', 'lv', 'xp', 'gold', 'hp', 'maxhp', 'mp', 'maxmp', 'atk', 'df', 'wl', 'slimes', 'quest', 'bag', 'eq', 'tm', 'day', 'gq', 'farm', 'char']


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
    slot = SLOT_OF[ITEMS[i]['type']]; old = P.eq.get(slot)
    remove_item(i); P.eq[slot] = i
    if old: add_item(old)
    return slot


def unequip(slot):
    i = P.eq.get(slot)
    if i and add_item(i): P.eq[slot] = None; return True
    return False


def quick_heal():
    for s in P.bag:
        it = ITEMS[s[0]]
        if it['type'] == 'use' and it.get('hp') and P.hp < P.maxhp:
            use_item(s[0]); note(f"Memakai {it['name']}"); return
    note("Tidak ada item pemulih HP." if P.hp < P.maxhp else "HP sudah penuh.")


# ---------------- state umum ----------------
mode = 'title'
loc = None       # None = luar, selain itu id interior
cur = None
dialog = menu = None
toast = ("", 0)
debug = False
walk_t = 0
door_lock = 0
touch_seen = False
err_info = None
inv = dict(tab=0, sel=-1, slot=None, snap=None, soff=0.0)
title = dict(idx=0, items=[], t0=0, last_esc=0)


def note(t):
    global toast; toast = (t, pygame.time.get_ticks() + 2600)


def say(name, lines, cb=None):
    global dialog, mode
    dialog = dict(name=name, lines=lines if isinstance(lines, list) else [lines], i=0, cb=cb, shown=0.0, wl=None, wi=-1); mode = 'dialog'
    reset_touch()


def mi(label, fn, iid=None, right='', cost=None):
    return dict(label=label, fn=fn, iid=iid, right=right, cost=cost)


def open_menu(title_, items):
    global menu, mode
    menu = dict(title=title_, items=items + [mi("Tutup", None)], idx=0, off=0.0, drag=None); mode = 'menu'; reset_touch()


def close_menu():
    global menu, mode
    menu = None; mode = 'explore'


def heal_full(): P.hp, P.mp = P.maxhp, P.maxmp


def gain(xp, gold):
    P.xp += xp; P.gold += gold; msgs = []
    while P.xp >= need(P.lv):
        P.xp -= need(P.lv); P.lv += 1
        P.maxhp += 12; P.maxmp += 4; P.atk += 3; P.df += 1
        heal_full(); msgs.append(f"Naik level! Lv {P.lv}")
    return msgs


# ---------------- collision & NPC luar ----------------
def hunt_ok(r):
    for px, py in (r.topleft, (r.right - 1, r.top), (r.left, r.bottom - 1), (r.right - 1, r.bottom - 1)):
        i, j = px // 16, py // 16
        if not (0 <= i < HGW and 0 <= j < HGH and HGRID[j][i]): return False
    return True


def safe_spot(x, y):
    """Titik terdekat dari (x, y) di desa yang tidak terblokir (bangunan, pohon, tebing, air, NPC). Mencegah pemain nyangkut."""
    return V.free_spot(lambda px, py: blocked(px, py), float(x), float(y), 900, 12)


def blocked(x, y, skip=None):
    r = feet(x, y)
    if area == 'town':
        if TOWN.hit(r): return True
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
        x, y = n['pos']
        if abs(x - P.x) > 1000 or abs(y - P.y) > 700: continue   # jauh dari layar: lewati (hemat CPU)
        near = math.hypot(x - P.x, y - P.y) < 85
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
REC = {1: ('Lv 1+', (150, 255, 150)), 2: ('Lv 4+', (255, 235, 120)), 3: ('Lv 7+', (255, 170, 80)), 9: ('BOSS', (255, 110, 110))}
HM = []


def build_hunt():
    HM.clear()
    for _nm, _x, _y, _r in HUNT_SPAWNS:
        _m = MBY[_nm]; _h = 110 if _m['tier'] == 9 else max(36, min(100, int(_m['size'] * 0.36)))
        HM.append(dict(m=_m, home=(_x, _y), pos=[float(_x), float(_y)], r=_r, h=_h, alive=True, respawn=0, imm=0, flip=False, tgt=None,
                       wait=0, anim=random.randint(0, 3000), spd={1: 40, 2: 55, 3: 70, 9: 45}[_m['tier']], chase=False))
        combat.init_enemy(HM[-1])


def hm_img(e):
    k = (e['m']['img'], e['h'], e['flip']); im = _HC.get(k)
    if im is None:
        base = mon_img(e['m'], e['h'])
        im = pygame.transform.flip(base, True, False) if e['flip'] else base
        _HC[k] = im
    return im


def hm_ok(x, y): return hunt_ok(pygame.Rect(int(x) - 6, int(y) - 3, 12, 6))


HCELL = 16


def hm_walk(i, j): return 0 <= i < HGW and 0 <= j < HGH and HGRID[j][i]


def hm_path(s_, g_):
    """Jalur BFS 8 arah di grid masker hutan dari sel s_ ke sel g_ (tanpa memotong sudut tembok). None jika tak terjangkau."""
    if s_ == g_: return []
    if not (hm_walk(*s_) and hm_walk(*g_)): return None
    prev = {s_: None}; q = deque([s_])
    while q:
        c = q.popleft()
        if c == g_: break
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            nb = (c[0] + di, c[1] + dj)
            if nb in prev or not hm_walk(*nb): continue
            if di and dj and not (hm_walk(c[0] + di, c[1]) and hm_walk(c[0], c[1] + dj)): continue
            prev[nb] = c; q.append(nb)
    if g_ not in prev: return None
    path, c = [], g_
    while c != s_: path.append(c); c = prev[c]
    path.reverse(); return path


def enter_area(a, pos):
    global area, door_lock
    area = a; P.x, P.y = float(pos[0]), float(pos[1]); door_lock = pygame.time.get_ticks() + 900; reset_touch(); combat.reset()
    if a == 'town' and blocked(P.x, P.y): P.x, P.y = safe_spot(P.x, P.y)
    if a == 'hunt':
        for e in HM:
            e['imm'] = pygame.time.get_ticks() + 1500; e['chase'] = False; e['st'] = 'idle'; e['agg'] = 0; e['kbt'] = 0
            if e['alive']: e['hp'] = float(e['maxhp'])
    note("Hutan Berburu: hindari monster yang terlalu kuat!" if a == 'hunt' else "Kembali ke Eldenvale")


# ---------------- interior ----------------
INT_CACHE = {}


def build_interior(iid):
    if iid in INT_CACHE: return INT_CACHE[iid]
    r = V.build_interior(iid); im = r['surf']
    s = min((W - 40) / float(im.get_width()), (H - 40) / float(im.get_height()), 2.2)
    surf = pygame.transform.smoothscale(im, (int(im.get_width() * s), int(im.get_height() * s)))
    k = s * 0.7
    spec = INTERIORS[iid]['npc']
    npcs, shs = [], {}
    if spec:
        nm, who, kind = spec
        npcs.append(dict(name=nm, who=who, kind=kind, pos=list(r['npc_pos']), d='down', flip=False, moving=False, anim=0)); shs[who] = Sheet(who, h=int(70 * k))
    # perabot diskalakan sekali; digambar bersama pemain menurut sumbu-Y (pemain bisa berada di belakang perabot)
    objs = [(by, pygame.transform.smoothscale(o, (max(1, int(o.get_width() * s)), max(1, int(o.get_height() * s)))), int(x * s), int(y * s)) for (by, o, x, y) in r['objs']]
    c = dict(id=iid, s=s, surf=surf, ox=(W - surf.get_width()) // 2, oy=(H - surf.get_height()) // 2, floor=r['floor'],
             solid=r['solid'], exit=r['exit'], spawn=r['spawn'], links=r['links'], label=r['label'], objs=objs, beds=r['beds'],
             hs=Sheet(f'chars/c{P.char}', scale=HS * k), sh=shs, npcs=npcs, k=k)
    c['sleep'] = []
    if r['sleep']:   # penduduk tidur di kamar penginapan saat malam
        for n_, pos_ in zip(NPCS, r['sleep']):
            sh_ = Sheet(n_['who'], h=int(70 * k))
            c['sleep'].append(dict(im=pygame.transform.rotate(sh_.get('down', 0, False, False), 90), pos=pos_))
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
    P.x, P.y = DOORS[iid]['out']; door_lock = pygame.time.get_ticks() + 700; reset_touch()
    note("Masuk: " + DOOR_NAME[iid])


def leave():
    global loc, cur, door_lock
    P.x, P.y = DOORS[loc]['out']; loc = None; cur = None; P.d = 'down'; door_lock = pygame.time.get_ticks() + 700; reset_touch()


# ---------------- waktu, malam & guild (v1.2) ----------------
MS_PER_MIN = 1500                 # 1 menit game = 1,5 detik nyata (1 hari ~ 36 menit)
NIGHT_START, NIGHT_END = 21 * 60, 5 * 60


def is_night(): return P.tm >= NIGHT_START or P.tm < NIGHT_END


def night_level():
    t = P.tm
    if 19 * 60 <= t < 21 * 60: return 0.6 * (t - 19 * 60) / 120.0
    if t >= 21 * 60 or t < 4 * 60 + 30: return 0.6
    if 4 * 60 + 30 <= t < 6 * 60: return 0.6 * (6 * 60 - t) / 90.0
    return 0.0


def clock_str():
    m = int(P.tm); h, mn = (m // 60) % 24, m % 60
    ph = 'Malam' if (m < 5 * 60 or m >= 19 * 60) else 'Pagi' if m < 11 * 60 else 'Siang' if m < 15 * 60 else 'Sore'
    return f"Hari {P.day}  {h:02d}:{mn:02d} ({ph})"


def on_night():
    note("Malam tiba. Penduduk kembali ke penginapan.")
    for n in NPCS: n['pos'] = list(n['home']); n['tgt'] = None; n['moving'] = False


def on_morning(): note("Pagi tiba. Penduduk kembali ke alun-alun.")


# ---------------- v1.5 pertanian ----------------
def on_new_day():
    planted = any(p[1] for p in P.farm.values())
    rain = V.new_day(P.farm)
    if planted: note("Hujan turun! Semua tanaman tersiram." if rain else "Hari baru. Siram tanamanmu agar tumbuh.")


def farm_hint(key):
    p = P.farm.get(key)
    if not p: return "Cangkul tanah"
    if not p[1]: return "Tanam benih"
    if V.ripe(p): return "Panen " + CROPS[p[1]]['name']
    if not p[3]: return "Siram " + CROPS[p[1]]['name']
    return f"{CROPS[p[1]]['name']}: {min(p[2], CROPS[p[1]]['days'])}/{CROPS[p[1]]['days']} hari"


def plant_menu(key):
    seeds = [(i, c) for i, c in P.bag if ITEMS[i].get('seed')]
    if not seeds: note("Kamu tidak punya benih. Beli di Petani Tomo."); return
    def go(iid):
        if count(iid) < 1: return
        remove_item(iid, 1); P.farm[key][1] = ITEMS[iid]['seed']; P.farm[key][2] = 0; P.farm[key][3] = 0
        close_menu(); note(f"Menanam {ITEMS[iid]['name']}")
    open_menu("Pilih benih", [mi(ITEMS[i]['name'], lambda i=i: go(i), i, f"x{c}") for i, c in seeds])


def farm_act():
    key = V.facing_plot(P.x, P.y, P.d, P.flip)
    if not key: return False
    p = P.farm.get(key)
    if not p: P.farm[key] = [1, None, 0, 0]; note("Tanah dicangkul."); return True
    if not p[1]: plant_menu(key); return True
    cr = CROPS[p[1]]
    if V.ripe(p):
        n = random.choice([1, 2, 2, 3]); iid = 'crop_' + p[1]
        if not add_item(iid, n): note("Tas penuh!"); return True
        P.farm[key] = [1, None, 0, 0]; msgs = gain(3 + cr['days'], 0)
        note(f"Panen {cr['name']} x{n}!"); [note(m) for m in msgs]; return True
    if not p[3]: p[3] = 1; note(f"{cr['name']} disiram."); return True
    note(f"{cr['name']} sedang tumbuh ({min(p[2], cr['days'])}/{cr['days']} hari).")
    return True


def gq_get(qid): return P.gq.setdefault(qid, dict(st='new', n=0))


def gq_prog(q):
    if q['kind'] == 'item': return min(q['need'], count(q['match']))
    return min(q['need'], gq_get(q['id'])['n'])


def gq_status(q):
    st = gq_get(q['id'])['st']
    if st == 'done': return 'Selesai'
    if st == 'new': return 'Baru'
    p = gq_prog(q)
    return 'Siap!' if p >= q['need'] else f"{p}/{q['need']}"


def quest_lines():
    out = [quest_text()] if quest_text() else []
    for q in GQ:
        if gq_get(q['id'])['st'] == 'active': out.append(f"{q['name']}: {gq_prog(q)}/{q['need']}")
    return out


def apply_daily(q):
    """Ganti misi harian di papan guild (misi biasa tidak disentuh)."""
    if q: GQ[:] = [g for g in GQ if not g.get('daily')] + [q]


def guild_board():
    open_menu("Papan Misi Guild", [mi(q['name'], lambda q=q: guild_act(q), None, gq_status(q)) for q in GQ])


def guild_act(q):
    st = gq_get(q['id'])
    if st['st'] == 'done': note("Misi ini sudah selesai."); return
    if st['st'] == 'new':
        st['st'] = 'active'; st['n'] = 0; close_menu(); note(f"Misi diterima: {q['name']}"); return
    if gq_prog(q) < q['need']:
        close_menu(); note(f"{q['name']}: {gq_prog(q)}/{q['need']}. {q['desc']}"); return
    st['st'] = 'done'
    if q['kind'] == 'item': remove_item(q['match'], q['need'])
    msgs = gain(q['xp'], q['gold'])
    rew = f"{q['gold']} emas, {q['xp']} XP"
    if q.get('item'):
        if add_item(q['item']): rew += f", {ITEMS[q['item']]['name']}"
        else: rew += " (tas penuh, hadiah item hilang)"
    close_menu()
    say(GUILD_MASTER, [f"Misi \"{q['name']}\" selesai! Kerja bagus.", f"Hadiahmu: {rew}."], lambda: [note(m) for m in msgs])


# ---------------- NPC logika ----------------
def open_shop(title_, stock, extra=()):
    items = []
    for iid, price in stock:
        def buy(iid=iid, price=price):
            if P.gold < price: note("Emas tidak cukup."); return
            if not add_item(iid): note("Tas penuh!"); return
            P.gold -= price; note(f"Membeli {ITEMS[iid]['name']}")
        items.append(mi(ITEMS[iid]['name'], buy, iid, f"{price} G", price))
    open_menu(title_, items + list(extra))


def talk(n):
    px, py = (P.x, P.y) if loc is None else (P.ix, P.iy)
    face(n, px, py); k, nm = n['kind'], n['name']
    if k == 'quest':
        if P.quest == 0:
            say(nm, ["Selamat datang di Eldenvale, pengelana.", "Slime di Hutan Berburu makin banyak dan mengganggu ladang desa.",
                     "Kalahkan 5 slime di Hutan Berburu (lewat gerbang selatan). Hadiahnya 120 emas!"], lambda: setattr(P, 'quest', 1))
        elif P.quest == 1:
            if P.slimes >= 5:
                P.quest = 2; say(nm, ["Kau berhasil! Desa ini berutang budi padamu.", "Ini hadiahmu: 120 emas, 40 XP, dan sebuah Elixir."],
                                 lambda: ([note(m) for m in gain(40, 120)], add_item('elixir'), setattr(P, 'quest', 3)))
            else: say(nm, [f"Slime terkalahkan: {P.slimes}/5. Cari di Hutan Berburu."])
        else: say(nm, ["Terima kasih sudah menjaga desa. Hati-hati dengan Raja Slime dan monster di jalan selatan."])
    elif k == 'priest':
        say(nm, ["Cahaya melindungimu. Biarkan aku menyembuhkan lukamu."], lambda: (heal_full(), note("HP & MP pulih penuh!")))
    elif k == 'inn':
        def rest():
            if P.gold >= 10: P.gold -= 10; heal_full(); note("Istirahat nyenyak. HP & MP pulih (-10 G)")
            else: note("Emas tidak cukup.")
            close_menu()
        def sleep_morning():   # v1.2: tidur malam sampai pagi (waktu melompat ke 06:00)
            if P.gold < 10: note("Emas tidak cukup."); close_menu(); return
            P.gold -= 10; heal_full()
            if P.tm >= 6 * 60: P.day += 1; on_new_day()
            P.tm = 6 * 60.0
            close_menu()
            say("Penginapan", ["Kau berbaring dan tertidur lelap...", "Saat terbangun, pagi sudah tiba. HP & MP pulih penuh."])
        if is_night():
            say(nm, ["Semua tamu sudah terlelap. Mau menginap sampai pagi?"], lambda: open_menu("Menginap?", [mi("Tidur sampai pagi", sleep_morning, None, "10 G", 10)]))
        else:
            say(nm, ["Penginapan Eldenvale! Menginap hanya 10 emas.", "Mau tidur sampai pagi? Tanamanmu akan tumbuh."], lambda: open_menu("Menginap?", [mi("Istirahat sebentar", rest, None, "10 G", 10), mi("Tidur sampai pagi", sleep_morning, None, "10 G", 10)]))
    elif k == 'seer':   # v1.3: peramal; desas-desus dari Groq jika kunci tersedia, selain itu teks cadangan
        fresh = pop_rumor()
        say(nm, [f"Aku melihat... {fresh}"] if fresh else n['lines'])
        fetch_async(BASE)
    elif k == 'guild':
        say(nm, ["Selamat datang di Guild Petualang Eldenvale!", "Ambil misi dari papan, selesaikan di Hutan Berburu, lalu serahkan di sini."], guild_board)
    elif k in ('shop', 'camp'):
        def sell_all():
            tot = sum(ITEMS[i]['val'] * c for i, c in P.bag if ITEMS[i]['type'] == 'mat')
            if tot <= 0: note("Tidak ada bahan untuk dijual."); return
            P.bag[:] = [s for s in P.bag if ITEMS[s[0]]['type'] != 'mat']; P.gold += tot; note(f"Menjual bahan: +{tot} G")
        def shop_menu():
            tot = sum(ITEMS[i]['val'] * c for i, c in P.bag if ITEMS[i]['type'] == 'mat')
            open_shop("Toko Kemah" if k == 'camp' else "Toko Ramuan", SHOP_ORN, [mi("Jual semua bahan", sell_all, None, f"+{tot} G")])
        say(nm, ["Ramuan segar, langsung dari kuali! Aku juga membeli bahan monster." if k == 'shop' else "Kemah pemburu! Beli ramuan di sini, dan jual bahan hasil buruanmu."], shop_menu)
    elif k == 'smith':
        def up():
            c = 50 * (P.wl + 1)
            if P.gold < c: note("Emas tidak cukup."); return
            P.gold -= c; P.wl += 1; P.atk += 3; note(f"Senjata ditempa +{P.wl}! ATK +3")
        say(nm, ["Besi yang baik butuh api yang panas!"],
            lambda: open_shop("Pandai Besi", SHOP_BROM, [mi(f"Tempa senjata (ATK +3)", up, None, f"{50 * (P.wl + 1)} G", 50 * (P.wl + 1))]))
    elif k == 'farmer':
        def sell_crops():
            tot = sum(ITEMS[i]['val'] * c for i, c in P.bag if ITEMS[i].get('crop'))
            if tot <= 0: note("Belum ada hasil panen untuk dijual."); return
            P.bag[:] = [s_ for s_ in P.bag if not ITEMS[s_[0]].get('crop')]; P.gold += tot; note(f"Menjual hasil panen: +{tot} G")
        def farm_menu():
            tot = sum(ITEMS[i]['val'] * c for i, c in P.bag if ITEMS[i].get('crop'))
            open_shop("Toko Benih", SHOP_SEEDS, [mi("Jual semua hasil panen", sell_crops, None, f"+{tot} G")])
        say(nm, ["Selamat datang di ladang Eldenvale! Aku Tomo.", "Cangkul tanah, tanam benih, siram tiap hari, lalu panen.", "Berdirilah menghadap petak lalu tekan Z / tombol A."], farm_menu)
    elif k == 'archer':
        say(nm, ["Monster kecil sekarang hanya ada di Hutan Berburu, lewat gerbang selatan.", "Lewati gerbang selatan untuk ke Hutan Berburu. Monster di sana terlihat, tapi ada Vampir penjaga gua. Bawa ramuan!"])
    elif k == 'granny':
        say(nm, random.choice([["Selamat datang, nak. Mau teh hangat?", "Dulu desa ini jauh lebih sepi."],
                               ["Monster paling kuat menjatuhkan Orb Ungu. Harganya mahal sekali!"]]))
    elif k == 'chat': say(nm, n['lines'])
    else: say(nm, ["Ada kincir angin dan ladang di sana. Kata kakek, sungai itu berasal dari air terjun ajaib."])


def near_npc():
    if loc is None:
        best, bd = None, 70
        for n in anpcs():
            d = math.hypot(n['pos'][0] - P.x, n['pos'][1] - P.y)
            if d < bd: best, bd = n, d
        return best
    best, bd = None, 80
    for n in cur['npcs']:
        d = math.hypot(n['pos'][0] - P.ix, n['pos'][1] - P.iy)
        if d < bd: best, bd = n, d
    return best


def sleep_in_bed():
    """Tidur di kasur: layar memudar, HP/MP pulih, waktu melompat ke 06:00 (hari baru bila sudah lewat 06:00)."""
    snap = screen.copy(); ov = pygame.Surface((W, H)); ov.fill((4, 6, 16)); clk = pygame.time.Clock()
    for i in range(16):
        screen.blit(snap, (0, 0)); ov.set_alpha(int(255 * (i + 1) / 16.0)); screen.blit(ov, (0, 0)); pygame.display.flip(); pygame.event.pump(); clk.tick(40)
    heal_full()
    if P.tm >= 6 * 60: P.day += 1; on_new_day()
    P.tm = 6 * 60.0
    screen.fill((4, 6, 16)); txt("Zzz...", W // 2, H // 2 - 10, F_L, C_TEXT, False, 'c'); pygame.display.flip(); pygame.time.delay(650)
    for i in range(16):
        draw_interior(); ov.set_alpha(int(255 * (1 - (i + 1) / 16.0))); screen.blit(ov, (0, 0)); pygame.display.flip(); pygame.event.pump(); clk.tick(40)
    reset_touch(); note("Kamu terbangun segar. HP & MP pulih penuh. Pagi hari!")


def bed_act():
    if loc is None or not cur.get('beds'): return False
    fb = ifeet(P.ix, P.iy).inflate(56, 56)
    if not any(fb.colliderect(b) for b in cur['beds']): return False
    cost = 10 if cur['id'] == 'inn2' else 0
    def go():
        if P.gold < cost: note("Emas tidak cukup."); close_menu(); return
        P.gold -= cost; close_menu(); sleep_in_bed()
    open_menu("Tidur di kasur?", [mi("Tidur sampai pagi", go, None, f"{cost} G" if cost else "Gratis", cost)])
    return True


def interact():
    n = near_npc()
    if n: talk(n)
    elif loc is None and area == 'town': farm_act()
    elif loc is not None: bed_act()


# ---------------- battle: lihat combat.py (real-time, di peta Hutan) ----------------
def world_snapshot():
    (draw_outdoor if loc is None else draw_interior)()
    return screen.copy()


def veil_on(surf, a, col=(6, 9, 22)):
    v = pygame.Surface(surf.get_size(), pygame.SRCALPHA); v.fill(col + (a,)); surf.blit(v, (0, 0))




# ---------------- simpan / muat / game baru ----------------
def save(quiet=False):
    try:
        d = {k: getattr(P, k) for k in SAVE_KEYS}
        d['area'] = area; d['v'] = VERSION
        tmp = SAVE + '.tmp'
        with open(tmp, 'w') as f: json.dump(d, f)
        os.replace(tmp, SAVE)
        if not quiet: note("Game disimpan.")
        return True
    except Exception:
        log_exc('save')
        if not quiet: note("Gagal menyimpan.")
        return False


def has_save(): return os.path.exists(SAVE)


def loadgame():
    global loc, cur, area
    if not os.path.exists(SAVE): note("Belum ada save."); return False
    try:
        with open(SAVE) as f: d = json.load(f)
        P.farm = {}; P.char = 0
        for k, v in d.items():
            if k in ('pot', 'eth', 'v'): continue
            if k == 'area': area = v if v in ('town', 'hunt') else 'town'; continue
            if k in SAVE_KEYS: setattr(P, k, v)
        if 'farm' not in d:
            for _i, _c in START_SEEDS: add_item(_i, _c)
        if 'pot' in d: add_item('potion_hp', d['pot'])
        if 'eth' in d: add_item('potion_mp', d['eth'])
        P.bag = [list(s) for s in P.bag if isinstance(s, (list, tuple)) and len(s) == 2 and s[0] in ITEMS]
        P.eq = {s: (P.eq.get(s) if P.eq.get(s) in ITEMS else None) for s in SLOT_NAME}
        if not isinstance(P.farm, dict): P.farm = {}
        P.farm = {k_: v_ for k_, v_ in P.farm.items() if isinstance(v_, list) and len(v_) == 4 and (v_[1] is None or v_[1] in CROPS)}
        P.hp = clamp(int(P.hp), 1, P.maxhp); P.mp = clamp(int(P.mp), 0, P.maxmp)
        if area == 'town' and blocked(P.x, P.y): P.x, P.y = safe_spot(P.x, P.y)
        if area == 'hunt' and not hunt_ok(feet(P.x, P.y)): P.x, P.y = float(HENTRY[0]), float(HENTRY[1])
        apply_char(P.char)
        loc = cur = None; reset_touch(); note("Game dimuat.")
        return True
    except Exception:
        log_exc('load'); note("Save rusak."); return False


def new_game():
    global area, loc, cur, dialog, menu
    for k, v in DEFAULT.items(): setattr(P, k, copy.deepcopy(v))
    P.eq = {s: None for s in SLOT_NAME}; P.eq['weapon'] = 'sword_iron'
    P.ix = P.iy = 0.0; P.d, P.flip, P.moving, P.dist = 'down', False, False, 0.0
    area = 'town'; loc = cur = None; dialog = menu = None
    for n in NPCS + HNPCS: init_npc(n)
    for e in HM: e.update(alive=True, pos=[float(e['home'][0]), float(e['home'][1])], imm=0, tgt=None, wait=0, chase=False)
    reset_touch()


# ============================================================ 4. LAYAR
# ---------------- kontrol sentuh ----------------
fingers, joy_vec = {}, [0.0, 0.0]
JR, JC0, joy_c = 84, (150, 400), [150, 400]
TB, T_BASE, T_KNOB, T_BTN, flash_btn = {}, None, None, {}, {}
HB, HUD_L, HUD_G, HUD_Q = {}, pygame.Rect(0, 0, 1, 1), pygame.Rect(0, 0, 1, 1), pygame.Rect(0, 0, 1, 1)
HUD_RW = 206


def build_hud():
    global HB, HUD_L, HUD_G, HUD_Q
    bs, gap = 62, 10; x = W - SAFE_X - bs
    HB = {'TAS': pygame.Rect(x - 2 * (bs + gap), SAFE_Y, bs, bs), 'SETELAN': pygame.Rect(x - (bs + gap), SAFE_Y, bs, bs), 'SIMPAN': pygame.Rect(x, SAFE_Y, bs, bs)}
    HUD_L = pygame.Rect(SAFE_X, SAFE_Y, 296, 90)
    HUD_G = pygame.Rect(W - SAFE_X - HUD_RW, SAFE_Y + bs + 8, HUD_RW, 40)
    HUD_Q = pygame.Rect(W - SAFE_X - HUD_RW, HUD_G.bottom + 8, HUD_RW, 70)


def build_touch():
    global JR, JC0, joy_c, TB, T_BASE, T_KNOB, T_BTN
    sz = S['tsize']; al = (110, 165, 220)[int(S['talpha'])]; JR = int(84 * sz)
    JC0 = (SAFE_X + 26 + JR, H - SAFE_Y - 22 - JR); joy_c = [JC0[0], JC0[1]]
    ar, br = int(54 * sz), int(40 * sz)
    ax, ay = W - SAFE_X - 22 - ar, H - SAFE_Y - 40 - ar
    TB = {'A': (ax, ay, ar), 'B': (ax - ar - br - 20, ay + ar - br, br)}
    d = 2 * JR + 8
    T_BASE = pygame.Surface((d, d), pygame.SRCALPHA)
    pygame.draw.circle(T_BASE, (255, 255, 255, al // 5), (d // 2, d // 2), JR)
    pygame.draw.circle(T_BASE, (255, 255, 255, al), (d // 2, d // 2), JR, 3)
    pygame.draw.circle(T_BASE, (255, 255, 255, al // 3), (d // 2, d // 2), int(JR * 0.55), 2)
    kd = int(78 * sz); T_KNOB = pygame.Surface((kd, kd), pygame.SRCALPHA)
    pygame.draw.circle(T_KNOB, (255, 226, 150, min(255, al + 40)), (kd // 2, kd // 2), kd // 2)
    pygame.draw.circle(T_KNOB, (255, 250, 220, min(255, al + 70)), (kd // 2, kd // 2), kd // 2 - 10)
    T_BTN = {}
    for nm, (_, _, r) in TB.items():
        s = pygame.Surface((2 * r + 8, 2 * r + 8), pygame.SRCALPHA); c = (r + 4, r + 4)
        pygame.draw.circle(s, (12, 18, 38, min(255, al + 30)), c, r)
        pygame.draw.circle(s, (C_GOLD if nm == 'A' else (120, 190, 255)) + (min(255, al + 80),), c, r, 4)
        ic = icon_s('chat' if nm == 'A' else 'potion', int(r * 0.95), C_GOLD if nm == 'A' else (150, 210, 255)); s.blit(ic, (c[0] - ic.get_width() // 2, c[1] - ic.get_height() // 2))
        T_BTN[nm] = s
    combat.build_layout()


def show_touch(): return S['touch'] == 'on' or (S['touch'] == 'auto' and (ANDROID or touch_seen))


def reset_touch():
    fingers.clear(); joy_vec[0] = joy_vec[1] = 0.0; joy_c[0], joy_c[1] = JC0


def update_joy(x, y):
    dx, dy = x - joy_c[0], y - joy_c[1]; d = math.hypot(dx, dy)
    if d > JR: dx, dy = dx * JR / d, dy * JR / d
    joy_vec[0], joy_vec[1] = dx / JR, dy / JR


def draw_touch():
    if mode != 'explore': return
    hunt = combat.active()
    if not show_touch() and not hunt: return
    t = pygame.time.get_ticks()
    if show_touch():
        act = 'joy' in fingers.values()
        cx, cy = (joy_c[0], joy_c[1]) if act else JC0
        screen.blit(T_BASE, (cx - JR - 4, cy - JR - 4)); k = T_KNOB.get_width() // 2
        screen.blit(T_KNOB, (int(cx + joy_vec[0] * JR) - k, int(cy + joy_vec[1] * JR) - k))
    if hunt: combat.draw_buttons(); return    # di Hutan: tombol Serang + 4 skill + ramuan (combat.py)
    near = near_npc(); on = {'A': near is not None, 'B': P.hp < P.maxhp}
    for nm, (bx, by, r) in TB.items():
        s = T_BTN[nm]; screen.blit(s, (bx - r - 4, by - r - 4))
        if flash_btn.get(nm, 0) > t: pygame.draw.circle(screen, (255, 255, 255), (bx, by), r, 3)
        elif on[nm]:
            pulse = 3 + int(2 * math.sin(t / 220.0)); pygame.draw.circle(screen, C_GOLD if nm == 'A' else (150, 210, 255), (bx, by), r + pulse, 2)
        cap = ("Bicara" if not near else fit(near['name'], F_XS, 120)) if nm == 'A' else "Ramuan"
        txt(cap, bx, by + r + 8, F_XS, C_TEXT, True, 'c')


# ---------------- HUD ----------------
def quest_text():
    return {0: "Bicara dengan Sir Aldric di dekat gereja", 1: f"Kalahkan Slime {min(P.slimes, 5)}/5 di Hutan Berburu",
            2: "Lapor ke Sir Aldric", 3: "Semua misi selesai"}.get(P.quest, "")


def draw_hud():
    r = HUD_L; panel(r, 208, 18)
    screen.blit(PORT_HUD, (r.x + 12, r.y + 15)); pygame.draw.circle(screen, C_GOLD, (r.x + 42, r.y + 45), 30, 2)
    pygame.draw.circle(screen, (24, 34, 72), (r.x + 58, r.y + 66), 13); pygame.draw.circle(screen, C_GOLD, (r.x + 58, r.y + 66), 13, 2)
    txt(str(P.lv), r.x + 58, r.y + 66 - F_XS.get_height() // 2, F_XS, C_GOLD, False, 'c')
    bx, bw = r.x + 84, r.w - 84 - 14
    txt("Kael", bx, r.y + 5, F_SB, C_TEXT); txt("Ksatria", r.right - 14, r.y + 8, F_XS, C_MUTE, False, 'r')
    bar(bx, r.y + 33, bw, 18, P.hp, P.maxhp, C_GREEN, f"HP {P.hp}/{P.maxhp}")
    bar(bx, r.y + 55, bw, 15, P.mp, P.maxmp, C_MP, f"MP {P.mp}/{P.maxmp}")
    bar(bx, r.y + 75, bw, 6, P.xp, need(P.lv), C_XP)
    for nm, hr in HB.items():
        active = (nm == 'TAS' and mode == 'inv')
        button(hr, '', 'primary' if active else 'dark', icon={'TAS': 'bag', 'SETELAN': 'gear', 'SIMPAN': 'save'}[nm])
    g = HUD_G; panel(g, 208, 14)
    screen.blit(icon_s('coin', 24, C_GOLD), (g.x + 12, g.centery - 12)); txt(str(P.gold), g.x + 44, g.centery - F_MB.get_height() // 2, F_MB, C_GOLD)
    txt(f"Tas {len(P.bag)}/{MAXBAG}", g.right - 12, g.centery - F_XS.get_height() // 2, F_XS, C_MUTE, False, 'r')
    q = HUD_Q; lines = []
    for _t in quest_lines(): lines += wrap(_t, F_S, q.w - 28)
    lines = lines[:4]; q.h = 36 + len(lines) * 19; panel(q, 208, 14)
    screen.blit(icon_s('diamond', 14, C_GOLD), (q.x + 12, q.y + 10)); txt("MISI", q.x + 32, q.y + 5, F_XS, C_GOLD, False)
    txt(clock_str(), q.right - 12, q.y + 5, F_XS, C_MUTE, False, 'r')
    for i, l in enumerate(lines): txt(l, q.x + 14, q.y + 28 + i * 19, F_S, C_TEXT, False if i else True)
    if not ANDROID and not show_touch():
        t = ("WASD / Panah: jalan    J / Spasi: serang    1 2 3 4: skill    P: ramuan    I: tas" if combat.active() else
             "WASD / Panah: jalan    Z / Spasi: bicara & berladang    I: tas    P: ramuan    F5: simpan")
        w = F_XS.size(t)[0] + 36; hr = pygame.Rect((W - w) // 2, H - 38, w, 28); shape(hr, (8, 12, 26, 170), 14, (255, 255, 255, 36), 1)
        txt(t, W // 2, hr.y + 5, F_XS, C_MUTE, False, 'c')


def draw_toast():
    t = pygame.time.get_ticks()
    if t >= toast[1] or not toast[0]: return
    left, right = SAFE_X + HUD_L.w + 14, W - SAFE_X - HUD_RW - 14
    avail = right - left
    if avail >= 280 and mode in ('explore', 'dialog', 'menu'): tw, y = min(avail, 460), SAFE_Y
    elif mode == 'inv': tw, y = min(W - 2 * SAFE_X, 460), SAFE_Y
    else: tw, y = min(W - 2 * SAFE_X, 460), SAFE_Y + 98
    lines = wrap(toast[0], F_S, tw - 32)[:2]; h = 18 + len(lines) * 21
    k = clamp((toast[1] - t) / 2600.0, 0.0, 1.0); slide = int(max(0.0, (k - 0.92)) * 12 * 20) if k > 0.92 else 0
    w = max(max(F_S.size(l)[0] for l in lines) + 36, 150) if lines else 150
    r = pygame.Rect(0, 0, w, h); r.midtop = (W // 2 if (avail < 280 or mode == 'inv') else (left + right) // 2, y - slide)
    panel(r, 232, 14, True)
    for i, l in enumerate(lines): txt(l, r.centerx, r.y + 9 + i * 21, F_S, C_TEXT, True, 'c')


# ---------------- title ----------------
def title_items():
    it = []
    if has_save(): it.append(('Lanjutkan', 'continue', 'gold', 'play'))
    it.append(('Game Baru', 'new', 'primary' if has_save() else 'gold', 'sword'))
    if not ANDROID: it.append(('Keluar', 'quit', 'dark', 'close'))
    return it


def title_rects():
    n = len(title['items']); bw, bh, gap = min(360, W - 80), 60, 14
    y0 = int(H * 0.43)
    return [pygame.Rect((W - bw) // 2, y0 + i * (bh + gap), bw, bh) for i in range(n)]


def enter_title():
    global mode, dialog, menu
    mode = 'title'; dialog = menu = None; title['items'] = title_items(); title['idx'] = 0; reset_touch()


def title_pick(i):
    global mode, game_started
    if not (0 <= i < len(title['items'])): return
    act = title['items'][i][1]
    if act == 'continue':
        if loadgame(): game_started = True; mode = 'explore'
    elif act == 'new': enter_charsel()
    elif act == 'quit': quit_game()


def enter_charsel():
    global mode
    mode = 'charsel'; CS['idx'] = P.char if 0 <= P.char < len(CHARS) else 0; reset_touch()


def charsel_confirm():
    global game_started
    ci = CS['idx']; new_game(); apply_char(ci); game_started = True
    say("Narator", [f"Selamat datang di Eldenvale, {CHARS[ci]['name']}. Desa kecil di tepi hutan ini akan menjadi awal perjalananmu.",
                    "Temui Sir Aldric di dekat gereja. Ketuk ikon tas untuk membuka inventory dan setelan."])


def charsel_layout():
    n = len(CHARS); cols = 4 if W >= H * 1.3 else 2; rows = (n + cols - 1) // cols; gap = 14; bh = 56
    by = H - SAFE_Y - bh - 8; top = int(H * 0.17); avail = max(60, by - 14 - top)
    cw = max(60, min(260, (W - 2 * SAFE_X - gap * (cols - 1)) // cols)); ch = max(60, min(380, (avail - gap * (rows - 1)) // rows))
    gw = cols * cw + gap * (cols - 1); gh = rows * ch + gap * (rows - 1); x0 = (W - gw) // 2; y0 = top + max(0, (avail - gh) // 2)
    cards = [pygame.Rect(x0 + (i % cols) * (cw + gap), y0 + (i // cols) * (ch + gap), cw, ch) for i in range(n)]
    bw = min(220, (W - 2 * SAFE_X - gap) // 2)
    btns = [pygame.Rect(W // 2 - gap // 2 - bw, by, bw, bh), pygame.Rect(W // 2 + gap // 2, by, bw, bh)]
    return cards, btns, cols


def charsel_key(k, ok):
    n = len(CHARS); cols = charsel_layout()[2]; i = CS['idx']
    if k == K.K_LEFT: CS['idx'] = (i - 1) % n
    elif k == K.K_RIGHT: CS['idx'] = (i + 1) % n
    elif k == K.K_UP and i - cols >= 0: CS['idx'] = i - cols
    elif k == K.K_DOWN and i + cols < n: CS['idx'] = i + cols
    elif ok: charsel_confirm()
    elif k == K.K_ESCAPE: enter_title()


def charsel_press(x, y):
    cards, btns, _ = charsel_layout(); p = (x, y)
    for i, r in enumerate(cards):
        if r.collidepoint(p): CS['idx'] = i; return
    if btns[0].inflate(10, 10).collidepoint(p): enter_title()
    elif btns[1].inflate(10, 10).collidepoint(p): charsel_confirm()


def draw_charsel():
    draw_town_bg(); t = pygame.time.get_ticks()
    txt("PILIH KARAKTER", W // 2, max(SAFE_Y, int(H * 0.045)), F_L, C_GOLD, True, 'c')
    txt("Pilih tokoh yang akan kamu mainkan", W // 2, max(SAFE_Y, int(H * 0.045)) + F_L.get_height() + 2, F_XS, C_MUTE, False, 'c')
    cards, btns, _ = charsel_layout()
    for i, r in enumerate(cards):
        sel = i == CS['idx']; panel(r, 236 if sel else 186, 16, sel)
        if sel: shape(r, None, 16, C_GOLD + (255,), 3)
        ty = r.bottom - F_XS.get_height() - 10; ny = ty - F_MB.get_height() - 2; gy = ny - 6
        ph = max(24, min(gy - r.y - 14, int(r.w * 1.05)))
        sh_ = pygame.Surface((int(ph * 0.7), max(4, int(ph * 0.12))), pygame.SRCALPHA); pygame.draw.ellipse(sh_, (0, 0, 0, 110), sh_.get_rect())
        screen.blit(sh_, (r.centerx - sh_.get_width() // 2, gy - sh_.get_height() // 2 - 2))
        pim = char_pic(i, 'down', (t // 170) % 4, ph) if sel else char_pic(i, 'idle', 0, ph)
        screen.blit(pim, (r.centerx - pim.get_width() // 2, gy - pim.get_height() - (int(abs(math.sin(t / 170.0)) * 3) if sel else 0)))
        txt(CHARS[i]['name'], r.centerx, ny, F_MB, C_GOLD if sel else C_TEXT, True, 'c')
        txt(CHARS[i]['title'], r.centerx, ty, F_XS, C_MUTE, False, 'c')
    button(btns[0], 'Kembali', 'dark', False, F_MB, 'close'); button(btns[1], 'Mulai', 'gold', True, F_MB, 'play')


def spaced(text, font, col, gap):
    k = ('sp', text, id(font), col, gap); s = _TG.get(k)
    if s is None:
        parts = [rt(c, font, col) for c in text]; w = sum(p.get_width() for p in parts) + gap * (len(parts) - 1)
        s = pygame.Surface((max(1, w), font.get_height()), pygame.SRCALPHA); x = 0
        for p in parts: s.blit(p, (x, 0)); x += p.get_width() + gap
        _TG[k] = s
    return s


def draw_town_bg():
    t = pygame.time.get_ticks(); k = 0.5 + 0.5 * math.sin(t / 7000.0)
    cx = int(300 + (MW - W - 600) * k) if MW > W + 600 else 0; cy = int(clamp((MH - H) * (0.40 + 0.1 * math.sin(t / 9000.0)), 0, max(0, MH - H)))
    screen.fill((0, 0, 0)); screen.blit(MAP, ((W - MW) // 2 if MW < W else 0, 0), (cx, cy, min(W, MW), min(H, MH)))
    for (_by, _im, _x, _y) in V.visible_objs(TOWN, cx, cy, W, H): screen.blit(_im, (_x - cx, _y - cy))
    if S['fx']: V.draw_effects(screen, TOWN, cx, cy, 0, 0, W, H, t, 0.0)
    veil(96, (6, 10, 28)); fade_v((0, 0, W, int(H * 0.5)), 150, 0); fade_v((0, int(H * 0.55), W, H - int(H * 0.55)), 0, 190)


def draw_title():
    draw_town_bg()
    ty = int(H * 0.085); a = rt("ELDENVALE", F_T, C_GOLD)
    txt("ELDENVALE", W // 2, ty, F_T, C_GOLD, True, 'c')
    s = spaced("PETUALANGAN RPG", F_S, C_TEXT, 7); screen.blit(s, ((W - s.get_width()) // 2, ty + a.get_height() + 2))
    pygame.draw.line(screen, C_GOLD, (W // 2 - 70, ty + a.get_height() + 34), (W // 2 + 70, ty + a.get_height() + 34), 2)
    for i, r in enumerate(title_rects()):
        lab, act, kind, ic = title['items'][i]; button(r, lab, kind, i == title['idx'], F_MB, ic)
    txt(f"Versi {VERSION}", SAFE_X, H - SAFE_Y - 22, F_XS, C_MUTE, False)
    hint = "Ketuk untuk memilih" if (ANDROID or touch_seen) else "Panah + Enter / klik untuk memilih"
    txt(hint, W - SAFE_X, H - SAFE_Y - 22, F_XS, C_MUTE, False, 'r')


# ---------------- dialog ----------------
def dialog_rect():
    h = 150 if H < 640 else 176
    return pygame.Rect(SAFE_X, H - h - SAFE_Y, W - 2 * SAFE_X, h)


def dialog_advance():
    global dialog, mode
    d = dialog
    if d is None: return
    full = d['lines'][d['i']]
    if d['shown'] < len(full): d['shown'] = float(len(full)); return
    d['i'] += 1; d['shown'] = 0.0; d['wi'] = -1
    if d['i'] >= len(d['lines']):
        cb = d['cb']; dialog = None; mode = 'explore'
        if cb: cb()


def draw_dialog():
    d = dialog; r = dialog_rect(); panel(r, 232, 18, True)
    full = d['lines'][d['i']]
    if d['wi'] != d['i']: d['wl'] = wrap(full, F_M, r.w - 64); d['wi'] = d['i']
    nm = d['name']; nw = F_MB.size(nm)[0] + 40; nr = pygame.Rect(r.x + 22, r.y - 18, nw, 36)
    screen.blit(vgrad(nw, 36, (252, 214, 130), (206, 150, 58), 12), nr.topleft); shape(nr, None, 12, (255, 240, 190, 220), 2)
    txt(nm, nr.centerx, nr.y + 3, F_MB, (44, 30, 8), False, 'c')
    rem = int(d['shown']); y = r.y + 30
    for l in d['wl'][:4]:
        part = l[:max(0, rem)]
        if part: txt(part, r.x + 32, y, F_M, C_TEXT)
        rem -= len(l) + 1; y += 30
    if d['shown'] >= len(full):
        t = pygame.time.get_ticks(); bob = int(3 * math.sin(t / 180.0)); last = d['i'] >= len(d['lines']) - 1
        screen.blit(icon_s('down', 22, C_GOLD), (r.right - 50, r.bottom - 38 + bob))
        txt("Ketuk" if (ANDROID or touch_seen) else "Z / Spasi", r.right - 60, r.bottom - 34, F_XS, C_MUTE, False, 'r')


def update_dialog(dt):
    if dialog and mode == 'dialog': dialog['shown'] += dt * 0.055


# ---------------- menu (toko, dll) ----------------
ROW = 54


def menu_geo():
    n = len(menu['items']); pw = min(580, W - 2 * SAFE_X - 10); head = 66; foot = 14
    maxh = H - 2 * SAFE_Y - 12; vis = max(2, (maxh - head - foot) // ROW); show = min(n, vis); ph = head + show * ROW + foot
    box = pygame.Rect((W - pw) // 2, (H - ph) // 2, pw, ph)
    lr = pygame.Rect(box.x + 12, box.y + head, pw - 24, show * ROW)
    return box, lr, max(0, n * ROW - lr.h)


def menu_ensure_visible():
    box, lr, mx = menu_geo(); top = menu['idx'] * ROW
    if top < menu['off']: menu['off'] = float(top)
    elif top + ROW > menu['off'] + lr.h: menu['off'] = float(top + ROW - lr.h)
    menu['off'] = clamp(menu['off'], 0.0, float(mx))


def draw_menu():
    veil(120); box, lr, mx = menu_geo(); panel(box, 240, 20, True)
    txt(menu['title'], box.x + 24, box.y + 14, F_L, C_GOLD)
    gr = pygame.Rect(0, 0, 124, 34); gr.topright = (box.right - 22, box.y + 18); shape(gr, (8, 12, 26, 190), 17, (255, 255, 255, 50), 1)
    screen.blit(icon_s('coin', 20, C_GOLD), (gr.x + 10, gr.y + 7)); txt(str(P.gold), gr.right - 12, gr.y + 5, F_MB, C_GOLD, False, 'r')
    pygame.draw.line(screen, (120, 140, 200), (box.x + 22, box.y + 62), (box.right - 22, box.y + 62), 1)
    screen.set_clip(lr)
    for i, it in enumerate(menu['items']):
        y = lr.y + i * ROW - int(menu['off'])
        if y > lr.bottom or y + ROW < lr.y: continue
        rr = pygame.Rect(lr.x, y + 3, lr.w - 14, ROW - 6); on = i == menu['idx']
        afford = it['cost'] is None or P.gold >= it['cost']
        shape(rr, (70, 100, 190, 215) if on else (255, 255, 255, 14), 12, (C_GOLD + (255,)) if on else None, 2)
        x = rr.x + 14
        if it['iid']: screen.blit(icon(it['iid'], 36), (x, rr.centery - 18)); x += 50
        col = C_MUTE if it['fn'] is None else (C_TEXT if afford else (150, 150, 168))
        txt(fit(it['label'], F_M, rr.w - (x - rr.x) - 120), x, rr.centery - F_M.get_height() // 2, F_M, col)
        if it['right']: txt(it['right'], rr.right - 16, rr.centery - F_M.get_height() // 2, F_MB, C_GOLD if afford else C_RED, True, 'r')
    screen.set_clip(None)
    if mx > 0:
        th = max(24, int(lr.h * lr.h / float(lr.h + mx))); ty = lr.y + int((lr.h - th) * (menu['off'] / float(mx)))
        shape(pygame.Rect(lr.right - 7, ty, 5, th), (200, 214, 255, 150), 3)


def menu_activate():
    it = menu['items'][menu['idx']]
    if it['fn'] is None: close_menu()
    else: it['fn']()


# ---------------- gambar dunia ----------------
def cam(mw, mh, px, py):
    if mw <= W: cx, ox = 0, (W - mw) // 2
    else: cx, ox = max(0, min(mw - W, int(px - W / 2))), 0
    if mh <= H: cy, oy = 0, (H - mh) // 2
    else: cy, oy = max(0, min(mh - H, int(py - H / 2))), 0
    return cx, cy, ox, oy


_NV = {}


def night_veil(lv):
    v = _NV.get((W, H))
    if v is None: v = _NV[(W, H)] = pygame.Surface((W, H), pygame.SRCALPHA)
    v.fill((10, 16, 52, int(lv * 170))); screen.blit(v, (0, 0))


_VG = {}


def vignette():
    """Vinyet digambar sebagai 4 strip tepi (48 px) yang di-cache, bukan satu blit RGBA seluas layar tiap frame."""
    v = _VG.get((W, H))
    if v is None:
        full = pygame.Surface((W, H), pygame.SRCALPHA); B = 48
        for i in range(B): pygame.draw.rect(full, (8, 6, 20, int(0.075 * (B - i) ** 1.35)), (i, i, W - 2 * i, H - 2 * i), 1)
        v = _VG[(W, H)] = (full.subsurface((0, 0, W, B)).copy(), full.subsurface((0, H - B, W, B)).copy(),
                           full.subsurface((0, B, B, H - 2 * B)).copy(), full.subsurface((W - B, B, B, H - 2 * B)).copy())
    t_, b_, l_, r_ = v
    screen.blit(t_, (0, 0)); screen.blit(b_, (0, H - 48)); screen.blit(l_, (0, 48)); screen.blit(r_, (W - 48, 48))


# Penghemat otomatis: bila rata-rata frame di desa terlalu lambat selama beberapa detik, efek diturunkan bertahap
# (1 = tanpa efek air/kupu-kupu/vinyet/cahaya lampu, 2 = tanpa pencahayaan). Tidak mengubah pengaturan yang tersimpan.
_PERF = dict(acc=0.0, n=0, bad=0, lite=0)


def perf_watch(dt):
    if mode != 'explore' or loc is not None or area != 'town': _PERF['acc'] = 0.0; _PERF['n'] = 0; return
    _PERF['acc'] += dt; _PERF['n'] += 1
    if _PERF['acc'] < 1500: return
    avg = _PERF['acc'] / _PERF['n']; _PERF['acc'] = 0.0; _PERF['n'] = 0
    if avg > max(24.0, 1000.0 / max(1, S['fps']) * 1.35): _PERF['bad'] += 1
    else: _PERF['bad'] = 0
    if _PERF['bad'] >= 2 and _PERF['lite'] < 2:
        _PERF['lite'] += 1; _PERF['bad'] = 0
        note("Grafis dihemat otomatis agar lebih lancar" if _PERF['lite'] == 1 else "Pencahayaan dimatikan agar lebih lancar")


def dusk_tint():
    m = P.tm
    a = 0.0
    if 16.5 * 60 <= m < 19 * 60: a = (m - 16.5 * 60) / 150.0
    elif 19 * 60 <= m < 20 * 60: a = 1.0 - (m - 19 * 60) / 60.0
    elif 5 * 60 <= m < 7 * 60: a = 0.8 * (1.0 - abs(m - 6 * 60) / 60.0)
    if a > 0.02:
        v = _NV.get((W, H, 'd'))
        if v is None: v = _NV[(W, H, 'd')] = pygame.Surface((W, H), pygame.SRCALPHA)
        v.fill((255, 140, 60, int(a * 46))); screen.blit(v, (0, 0))


def draw_outdoor():
    mp, mw, mh = (MAP, MW, MH) if area == 'town' else (HMAP, HW, HH)
    cx, cy, ox, oy = cam(mw, mh, P.x, P.y)
    if area == 'hunt': _sx, _sy = combat.shake_off(); ox += _sx; oy += _sy      # getar layar saat kena / skill
    if ox or oy: screen.fill((6, 10, 18))
    screen.blit(mp, (ox, oy), (cx, cy, min(W, mw), min(H, mh)))
    if area == 'hunt': combat.draw_ground(cx, cy, ox, oy)                     # ring target, telegraf serangan musuh, bidik skill
    ents = []
    if area == 'town':   # v1.5: objek desa (rumah, pohon, taman) & tanaman ladang ikut diurutkan menurut Y
        for (by_, im_, x_, y_) in V.visible_objs(TOWN, cx, cy, W, H): ents.append((by_, im_, (x_, y_), None, None, None))
        for (by_, im_, x_, y_) in V.draw_farm(screen, TOWN, P.farm, cx, cy, ox, oy, W, H): ents.append((by_, im_, (x_, y_), None, None, None))
    for n in anpcs():
        im = sheet_for(n['who']).get(n['d'], n['anim'] // 200, n['flip'], n['moving'])
        ents.append((n['pos'][1], im, n['pos'], n, -int(abs(math.sin(n['anim'] / 110.0)) * 3) if n['moving'] else 0, None))
    if area == 'hunt':
        for e in HM:
            if e['alive']: ents.append((e['pos'][1], hm_img(e), e['pos'], None, -int(abs(math.sin(e['anim'] / 140.0)) * 4), e))
    ents.append((P.y, hero.get(P.d, P.step, P.flip, P.moving), (P.x, P.y), None, 0, None))
    near = near_npc() if mode == 'explore' else None; t = pygame.time.get_ticks()
    for _, im, (x, y), n, bob, e in sorted(ents, key=lambda q: q[0]):
        if bob is None: screen.blit(im, (int(x - cx + ox), int(y - cy + oy))); continue
        sx, sy = int(x - cx + ox), int(y - cy + oy)
        if sx < -150 or sx > W + 150 or sy < -150 or sy > H + 150: continue
        if e: im = combat.enemy_img(e, im)
        elif n is None and area == 'hunt': im = combat.player_img(im)
        if S['shadows']: screen.blit(SHADOW, (sx - 20, sy - 9))
        screen.blit(im, (sx - im.get_width() // 2, sy - im.get_height() + 6 + bob))
        top = sy - im.get_height() + bob
        if e:
            lab, col = REC[e['m']['tier']]; tg = tag(f"{e['m']['name']}  {lab}", C_TEXT, col); bs_ = combat.bar_shown(e)
            screen.blit(tg, (sx - tg.get_width() // 2, top - (38 if bs_ else 26)))
            if e['chase'] and e['st'] != 'wind':
                cy_ = top - (64 if bs_ else 40)
                pygame.draw.circle(screen, C_RED, (sx, cy_), 11); pygame.draw.circle(screen, (255, 255, 255), (sx, cy_), 11, 2)
                txt("!", sx, cy_ - F_SB.get_height() // 2 - 1, F_SB, (255, 255, 255), False, 'c')
        elif n and S['names']:
            tg = tag(n['name'], (255, 240, 190)); screen.blit(tg, (sx - tg.get_width() // 2, top - 22))
            if n is near: screen.blit(icon_s('down', 20, C_GOLD), (sx - 10, top - 44 + int(3 * math.sin(t / 160.0))))
    if area == 'hunt': combat.draw_over(cx, cy, ox, oy)       # tebasan, proyektil, bar HP, angka damage
    amb = V.ambient(P.tm); lv = min(1.0, amb[3] / 150.0)
    if area == 'town':
        if S['fx'] and _PERF['lite'] < 1: V.draw_effects(screen, TOWN, cx, cy, ox, oy, W, H, t, lv)
        if _PERF['lite'] < 2: V.draw_lighting(screen, TOWN, cx, cy, ox, oy, W, H, amb, P.x - cx + ox, P.y - cy + oy - 30, t, S['fx'] and _PERF['lite'] < 1)
        if mode == 'explore' and loc is None:
            fk = V.facing_plot(P.x, P.y, P.d, P.flip)
            if fk:
                fr = V.plot_rect(fk).move(-cx + ox, -cy + oy); pulse = 150 + int(90 * math.sin(t / 180.0))
                pygame.draw.rect(screen, (pulse, int(pulse * 0.85), 70), fr, 3, border_radius=4)
                tg = tag(farm_hint(fk), C_GOLD); screen.blit(tg, (fr.centerx - tg.get_width() // 2, fr.y - tg.get_height() - 6))
    else: V.draw_lighting(screen, TOWN, cx, cy, ox, oy, W, H, amb, 0, 0, t, False)
    if S['fx'] and _PERF['lite'] < 1: vignette()
    if debug:
        if area == 'town':
            for b in BLOCK: pygame.draw.rect(screen, (255, 0, 0), b.move(-cx + ox, -cy + oy), 2)
            for b, _ in WILD: pygame.draw.rect(screen, (255, 255, 0), b.move(-cx + ox, -cy + oy), 2)
            for b in DOORR.values(): pygame.draw.rect(screen, (0, 255, 255), b.move(-cx + ox, -cy + oy), 2)
            pygame.draw.rect(screen, (0, 255, 255), GATE.move(-cx + ox, -cy + oy), 2)
        else: pygame.draw.rect(screen, (0, 255, 255), HEXIT.move(-cx + ox, -cy + oy), 2)


def draw_interior():
    c = cur; s = c['s']; screen.fill((4, 6, 14)); screen.blit(c['surf'], (c['ox'], c['oy']))
    ents = [(n['pos'][1], c['sh'][n['who']].get(n['d'], 0, n['flip'], False), n['pos'], n['name'], n) for n in c['npcs']]
    ents.append((P.iy, c['hs'].get(P.d, P.step, P.flip, P.moving), (P.ix, P.iy), None, None))
    for (by, im, x, y) in c['objs']: ents.append((by, im, (x, y), None, 'obj'))
    if is_night():
        for sl in c.get('sleep', []):
            im_ = sl['im']; ents.append((sl['pos'][1] + 40, im_, (int(sl['pos'][0] * s) - im_.get_width() // 2, int(sl['pos'][1] * s) - im_.get_height() // 2), None, 'zzz'))
    near = near_npc() if mode == 'explore' else None; t = pygame.time.get_ticks()
    for _, im, (x, y), nm, n in sorted(ents, key=lambda e: e[0]):
        if n == 'obj' or n == 'zzz':
            screen.blit(im, (c['ox'] + x, c['oy'] + y))
            if n == 'zzz': txt("z z Z", c['ox'] + x + im.get_width() // 2, c['oy'] + y - 12, F_XS, C_MUTE, True, 'c')
            continue
        sx, sy = c['ox'] + int(x * s), c['oy'] + int(y * s)
        if S['shadows']: screen.blit(SHADOW, (sx - 20, sy - 9))
        screen.blit(im, (sx - im.get_width() // 2, sy - im.get_height() + 6))
        if nm and S['names']:
            tg = tag(nm, (255, 240, 190)); screen.blit(tg, (sx - tg.get_width() // 2, sy - im.get_height() - 18))
            if n is near: screen.blit(icon_s('down', 20, C_GOLD), (sx - 10, sy - im.get_height() - 40 + int(3 * math.sin(t / 160.0))))
    fb = ifeet(P.ix, P.iy).inflate(80, 80)
    for b_ in c['beds']:   # petunjuk tidur
        if fb.colliderect(b_):
            tg = tag("Tidur (Z / A)" + ("  10 G" if c['id'] == 'inn2' else ""), C_GOLD); screen.blit(tg, (c['ox'] + int(b_.centerx * s) - tg.get_width() // 2, c['oy'] + int(b_.top * s) - 26)); break
    for lk in c['links']:   # petunjuk tangga
        r_ = lk['rect']; f_ = ifeet(P.ix, P.iy)
        if f_.inflate(60, 60).colliderect(r_):
            tg = tag(lk['label'], C_GOLD); screen.blit(tg, (c['ox'] + int((r_.centerx) * s) - tg.get_width() // 2, c['oy'] + int(r_.bottom * s) + 4))
    if debug:
        for r in c['floor']: pygame.draw.rect(screen, (0, 255, 0), pygame.Rect(c['ox'] + r.x * s, c['oy'] + r.y * s, r.w * s, r.h * s), 2)
        for r in c['solid']: pygame.draw.rect(screen, (255, 0, 0), pygame.Rect(c['ox'] + r.x * s, c['oy'] + r.y * s, r.w * s, r.h * s), 2)
    nm = c.get('label') or DOOR_NAME.get(loc, '')
    if nm: tg = tag(nm, C_GOLD); screen.blit(tg, ((W - tg.get_width()) // 2, H - SAFE_Y - 30))


# ---------------- layar error (bukan crash: game tetap tampil) ----------------
def draw_error():
    screen.fill(C_BG); screen.blit(vgrad(W, H, (40, 20, 34), (10, 12, 26)), (0, 0))
    pw, ph = min(640, W - 60), min(340, H - 40); r = pygame.Rect((W - pw) // 2, (H - ph) // 2, pw, ph); panel(r, 240, 18, True)
    txt("Terjadi kesalahan", r.centerx, r.y + 18, F_L, C_GOLD, True, 'c')
    msg = (err_info or {}).get('msg', ''); y = r.y + 70
    for l in wrap("Game tetap aman dan progres tidak hilang. Detail tercatat di crash.log.", F_S, r.w - 48)[:3]: txt(l, r.centerx, y, F_S, C_TEXT, False, 'c'); y += 22
    for l in wrap(msg, F_XS, r.w - 48)[:4]: txt(l, r.centerx, y + 6, F_XS, C_MUTE, False, 'c'); y += 18
    button(err_btn(), 'Lanjutkan', 'gold', True, F_MB, 'play')


def err_btn():
    pw, ph = min(640, W - 60), min(340, H - 40); r = pygame.Rect((W - pw) // 2, (H - ph) // 2, pw, ph)
    return pygame.Rect(r.centerx - 120, r.bottom - 76, 240, 56)


# ============================================================ 5. TAS & BATTLE
TYPE_NAME = {'weapon': 'Senjata', 'helm': 'Helm', 'armor': 'Baju', 'cloak': 'Jubah', 'neck': 'Aksesori', 'boots': 'Sepatu',
             'use': 'Ramuan / Makanan', 'mat': 'Bahan', 'misc': 'Lain-lain'}
PRESETS = [('Tinggi', dict(fps=60, fx=True, shadows=True, names=True, wander=True, shake=True)),
           ('Sedang', dict(fps=45, fx=False, shadows=True, names=False, wander=True, shake=False)),
           ('Rendah', dict(fps=30, fx=False, shadows=False, names=False, wander=False, shake=False))]
YN = {True: 'Ya', False: 'Tidak'}
SET_ROWS = [('fps', 'FPS maksimum', [30, 45, 60, 90, 120], {}), ('show_fps', 'Tampilkan FPS', [False, True], YN),
            ('fx', 'Efek visual (air, cahaya, kupu-kupu)', [True, False], YN), ('shadows', 'Bayangan karakter', [True, False], YN), ('names', 'Nama di atas NPC', [True, False], YN),
            ('wander', 'NPC berkeliaran', [True, False], YN), ('shake', 'Getar layar saat bertarung', [True, False], YN),
            ('touch', 'Kontrol sentuh', ['auto', 'on', 'off'], {'auto': 'Otomatis', 'on': 'Selalu', 'off': 'Sembunyi'}),
            ('tsize', 'Ukuran tombol', [0.8, 1, 1.2], {0.8: 'Kecil', 1: 'Sedang', 1.2: 'Besar'}),
            ('talpha', 'Transparansi tombol', [0, 1, 2], {0: 'Samar', 1: 'Sedang', 2: 'Jelas'}),
            ('speed', 'Kecepatan jalan', [0.8, 1, 1.25], {0.8: 'Santai', 1: 'Normal', 1.25: 'Cepat'})]
SROWH = 48


def sanitize_settings():
    for key, _, opts, _m in SET_ROWS:
        if S.get(key) not in opts: S[key] = S0[key]


def srows():
    return [('preset', 'Kualitas grafis')] + [(key, lab) for key, lab, _o, _m in SET_ROWS] + \
           [('act:save', 'Simpan game'), ('act:load', 'Muat game'), ('act:title', 'Kembali ke menu utama')]


def set_max_off(): return max(0, len(srows()) * SROWH - SET_AREA.h)


def srow_rect(i): return pygame.Rect(SET_AREA.x, SET_AREA.y + i * SROWH - int(inv['soff']), SET_AREA.w, SROWH - 6)


def preset_name():
    for n, p in PRESETS:
        if all(S[k_] == v_ for k_, v_ in p.items()): return n
    return 'Kustom'


def srow_do(i):
    key = srows()[i][0]
    _PERF['lite'] = 0; _PERF['bad'] = 0
    if key == 'preset':
        names = [n for n, _ in PRESETS]; c = preset_name()
        nxt = (names.index(c) + 1) % len(names) if c in names else 0; S.update(PRESETS[nxt][1])
    elif key == 'act:save': save()
    elif key == 'act:load':
        global mode
        if loadgame(): mode = 'explore'
    elif key == 'act:title': go_title()
    else:
        for k2, _, opts, _m in SET_ROWS:
            if k2 == key:
                j = opts.index(S[k2]) if S[k2] in opts else -1; S[k2] = opts[(j + 1) % len(opts)]
                if k2 in ('tsize', 'talpha'): build_touch()
    save_settings()


def flist():
    t = inv['tab']
    def ok(it):
        ty = it['type']
        return (t == 0 or (t == 1 and ty == 'weapon') or (t == 2 and ty in ('helm', 'armor', 'cloak', 'neck', 'boots'))
                or (t == 3 and ty == 'use') or (t == 4 and ty in ('mat', 'misc')))
    return [s for s in P.bag if ok(ITEMS[s[0]])]


def sel_item():
    if inv['slot']: return P.eq.get(inv['slot']), True
    l = flist(); return (l[inv['sel']][0], False) if 0 <= inv['sel'] < len(l) else (None, False)


def open_inv(tab=0):
    global mode
    s = world_snapshot(); veil_on(s, 170)
    inv.update(tab=tab, sel=-1, slot=None, snap=s, soff=0.0); mode = 'inv'; reset_touch()


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


def info_btns(eqd):
    b = INFO; bh = 30; y = b.bottom - bh - 5; gap = 8
    if eqd: return [pygame.Rect(b.x + 8, y, b.w - 16, bh)]
    bw = (b.w - 16 - gap * 2) // 3
    return [pygame.Rect(b.x + 8 + i * (bw + gap), y, bw, bh) for i in range(3)]


def draw_inv():
    screen.blit(inv['snap'], (0, 0)); screen.blit(UL, (LX, LY)); screen.blit(UR_, (RX, RY))
    tab = inv['tab']
    if tab != 0: screen.blit(DIM0, TABR[0].topleft)
    pygame.draw.rect(screen, (255, 225, 110), TABR[tab], 3, border_radius=10)
    txt(f"{TABS[tab]}" + (f"   {len(P.bag)}/{MAXBAG}" if tab != 5 else ""), LX + int(124 * US), LY + int(72 * US), F_M, C_TEXT)
    if tab == 5:
        shape(SET_AREA.inflate(18, 14), (226, 210, 180, 255), 12)
        screen.set_clip(SET_AREA)
        for i, (key, lab) in enumerate(srows()):
            r = srow_rect(i)
            if r.bottom < SET_AREA.y or r.y > SET_AREA.bottom: continue
            shape(r, (246, 236, 214, 235), 12, (150, 118, 70, 255), 2)
            txt(lab, r.x + 14, r.centery - F_S.get_height() // 2, F_S, C_INK, False)
            if key.startswith('act:'):
                screen.blit(icon_s({'act:save': 'save', 'act:load': 'load', 'act:title': 'home'}[key], 22, (46, 88, 180)), (r.right - 36, r.centery - 11))
            else:
                val = preset_name() if key == 'preset' else dict((a, d) for a, _, _, d in SET_ROWS)[key].get(S[key], str(S[key]))
                vw = F_XS.size(val)[0] + 24; vr = pygame.Rect(0, 0, vw, 28); vr.midright = (r.right - 10, r.centery)
                screen.blit(vgrad(vw, 28, (86, 140, 240), (44, 88, 190), 14), vr.topleft); txt(val, vr.centerx, vr.y + 4, F_XS, (255, 255, 255), False, 'c')
        screen.set_clip(None)
        mx = set_max_off()
        if mx > 0:
            th = max(24, int(SET_AREA.h * SET_AREA.h / float(SET_AREA.h + mx))); ty = SET_AREA.y + int((SET_AREA.h - th) * inv['soff'] / float(mx))
            shape(pygame.Rect(SET_AREA.right - 6, ty, 4, th), (120, 90, 50, 200), 2)
    else:
        for i, s in enumerate(flist()[:30]):
            r = CELLS[i]; ic = icon(s[0], int(r.w * 0.74)); screen.blit(ic, ic.get_rect(center=r.center))
            if s[1] > 1: txt(str(s[1]), r.right - 5, r.bottom - 21, F_XS, C_TEXT, True, 'r')
            if i == inv['sel'] and not inv['slot']: pygame.draw.rect(screen, (255, 225, 110), r, 3, border_radius=8)
    txt(f"{P.gold} G", GOLDBAR.x + int(80 * US), GOLDBAR.centery - F_MB.get_height() // 2, F_MB, C_INK, False)
    for slot, r in SLOTR.items():
        i = P.eq.get(slot)
        if i:
            pygame.draw.rect(screen, (96, 102, 130), r.inflate(-10, -10), border_radius=8); ic = icon(i, int(r.w * 0.78)); screen.blit(ic, ic.get_rect(center=r.center))
        if inv['slot'] == slot: pygame.draw.rect(screen, (255, 225, 110), r, 3, border_radius=8)
    screen.blit(PORT, PORT.get_rect(center=PORT_C))
    n = NAMEBOX; txt("Kael", n.x + 10, n.y + 3, F_MB, C_INK, False); txt(f"Lv {P.lv}", n.right - 10, n.y + 6, F_SB, (150, 96, 20), False, 'r')
    rows = [(f"HP {P.hp}/{P.maxhp}", P.hp, P.maxhp, C_GREEN), (f"MP {P.mp}/{P.maxmp}", P.mp, P.maxmp, C_MP), (f"XP {P.xp}/{need(P.lv)}", P.xp, need(P.lv), C_XP)]
    bh = max(13, min(18, (n.h - 36) // 3 - 4))
    for j, (lab, v, m, c) in enumerate(rows): bar(n.x + 10, n.y + 34 + j * (bh + 4), n.w - 20, bh, v, m, c, lab)
    iid, eqd = sel_item(); b = INFO
    if iid:
        it = ITEMS[iid]
        txt(fit(it['name'], F_SB, b.w - 110), b.x + 18, b.y + 1, F_SB, C_INK, False); txt(f"{it['val']} G", b.right - 20, b.y + 5, F_XS, C_INK2, False, 'r')
        txt(TYPE_NAME[it['type']], b.x + 18, b.y + 20, F_XS, C_INK2, False)
        stat = "  ".join(f"{lbl} +{it[k_]}" for k_, lbl in (('atk', 'ATK'), ('df', 'DEF')) if it.get(k_)) or it.get('desc', '')
        txt(fit(stat, F_XS, b.w - 40), b.x + 18, b.y + 36, F_XS, (30, 100, 50), False)
        labs = ['LEPAS'] if eqd else ['PAKAI' if it['type'] == 'use' else 'PASANG', 'JUAL', 'BUANG']; kinds = ['primary'] if eqd else ['primary', 'gold', 'danger']
        for r, lab, kd in zip(info_btns(eqd), labs, kinds): button(r, lab, kd, False, F_SB)
    else:
        txt(f"ATK {tatk()}   DEF {tdef()}", b.x + 18, b.y + 2, F_MB, C_INK, False)
        txt(f"Perlengkapan: +{eqsum('atk')} ATK, +{eqsum('df')} DEF", b.x + 18, b.y + 30, F_XS, C_INK2, False)
        txt("Ketuk item untuk melihat detail", b.x + 18, b.y + 48, F_XS, C_INK2, False)
        txt(f"Slime dikalahkan: {P.slimes}   Senjata +{P.wl}", b.x + 18, b.y + 66, F_XS, C_INK2, False)
    button(CLOSE, '', 'danger', False, F_MB, 'close')




# ============================================================ 6. INPUT
game_started = False
last_finger = -10000
K = pygame
KBACK = getattr(pygame, 'K_AC_BACK', None)
BG_EVENTS = tuple(getattr(pygame, n) for n in ('WINDOWFOCUSLOST', 'APP_WILLENTERBACKGROUND', 'APP_DIDENTERBACKGROUND') if hasattr(pygame, n))


def autosave():
    if game_started and mode not in ('title', 'error', 'charsel'): save(quiet=True)


def quit_game():
    autosave()
    try: pygame.quit()
    except Exception: pass
    sys.exit(0)


def go_title():
    autosave(); enter_title()


def close_inv():
    global mode
    mode = 'explore'; inv['snap'] = None


def recover():
    global mode, loc, cur, dialog, menu, err_info, area
    err_info = None; dialog = menu = None; loc = cur = None
    if area == 'town' and blocked(P.x, P.y): P.x, P.y = safe_spot(P.x, P.y)
    if area == 'hunt' and not hunt_ok(feet(P.x, P.y)): P.x, P.y = float(HENTRY[0]), float(HENTRY[1])
    reset_touch(); mode = 'explore' if game_started else 'title'  # charsel -> title
    if mode == 'title': enter_title()


def handle_key(k):
    global mode, debug
    if KBACK is not None and k == KBACK: k = pygame.K_ESCAPE
    ok = k in (K.K_RETURN, K.K_SPACE, K.K_z)
    if mode == 'title':
        n = len(title['items'])
        if k == K.K_UP: title['idx'] = (title['idx'] - 1) % n
        elif k == K.K_DOWN: title['idx'] = (title['idx'] + 1) % n
        elif ok: title_pick(title['idx'])
        elif k == K.K_ESCAPE:
            t = pygame.time.get_ticks()
            if t - title['last_esc'] < 2000: quit_game()
            title['last_esc'] = t; note("Tekan sekali lagi untuk keluar")
    elif mode == 'charsel': charsel_key(k, ok)
    elif mode == 'error':
        if ok or k == K.K_ESCAPE: recover()
    elif mode == 'explore':
        if k in (K.K_ESCAPE, K.K_i, K.K_TAB): open_inv(0)
        elif combat.active() and combat.key(k): pass      # Hutan: J/Spasi/Z serang, 1-4 skill, P ramuan
        elif ok: interact()
        elif k == K.K_p: quick_heal()
        elif k == K.K_F5: save()
        elif k == K.K_F9: loadgame()
        elif k == K.K_F1: debug = not debug
    elif mode == 'dialog':
        if ok or k == K.K_ESCAPE: dialog_advance()
    elif mode == 'menu':
        n = len(menu['items'])
        if k == K.K_UP: menu['idx'] = (menu['idx'] - 1) % n; menu_ensure_visible()
        elif k == K.K_DOWN: menu['idx'] = (menu['idx'] + 1) % n; menu_ensure_visible()
        elif ok: menu_activate()
        elif k == K.K_ESCAPE: close_menu()
    elif mode == 'inv':
        if k in (K.K_ESCAPE, K.K_i, K.K_TAB): close_inv()
        elif k == K.K_LEFTBRACKET: inv.update(tab=(inv['tab'] - 1) % 6, sel=-1, slot=None, soff=0.0)
        elif k == K.K_RIGHTBRACKET: inv.update(tab=(inv['tab'] + 1) % 6, sel=-1, slot=None, soff=0.0)
        elif inv['tab'] != 5:
            l = flist()
            if k == K.K_LEFT: inv['sel'] = max(0, inv['sel'] - 1); inv['slot'] = None
            elif k == K.K_RIGHT: inv['sel'] = min(len(l) - 1, inv['sel'] + 1); inv['slot'] = None
            elif k == K.K_UP: inv['sel'] = max(0, inv['sel'] - 6); inv['slot'] = None
            elif k == K.K_DOWN: inv['sel'] = min(len(l) - 1, inv['sel'] + 6); inv['slot'] = None
            elif ok: inv_activate()
        else:
            if k == K.K_DOWN: inv['soff'] = clamp(inv['soff'] + SROWH, 0, set_max_off())
            elif k == K.K_UP: inv['soff'] = clamp(inv['soff'] - SROWH, 0, set_max_off())



def press(fid, x, y):
    global mode
    p = (x, y)
    if mode == 'title':
        for i, r in enumerate(title_rects()):
            if r.inflate(10, 10).collidepoint(p): title['idx'] = i; title_pick(i); return
    elif mode == 'charsel': charsel_press(x, y)
    elif mode == 'error':
        if err_btn().inflate(20, 20).collidepoint(p): recover()
    elif mode == 'explore':
        for nm, r in HB.items():
            if r.inflate(10, 10).collidepoint(p):
                if nm == 'TAS': open_inv(0)
                elif nm == 'SETELAN': open_inv(5)
                else: save()
                return
        if combat.active() and combat.press(fid, x, y): return      # tombol Serang / skill / ramuan
        if show_touch():
            if not combat.active():
                for nm, (bx, by, br) in TB.items():
                    if math.hypot(x - bx, y - by) <= br + 22:
                        flash_btn[nm] = pygame.time.get_ticks() + 140
                        if nm == 'A': interact()
                        else: quick_heal()
                        return
            if x < W * 0.55 and y > HUD_L.bottom + 6 and 'joy' not in fingers.values():
                fingers[fid] = 'joy'; joy_c[0] = int(clamp(x, JR + 10, W - JR - 10)); joy_c[1] = int(clamp(y, HUD_L.bottom + JR // 2, H - JR - 10)); update_joy(x, y)
    elif mode == 'dialog': dialog_advance()
    elif mode == 'menu':
        box, lr, mx = menu_geo()
        if lr.collidepoint(p): fingers[fid] = 'menu'; menu['drag'] = dict(y0=y, off0=menu['off'], moved=False, y=y)
    elif mode == 'inv': inv_press(fid, x, y)



def inv_press(fid, x, y):
    p = (x, y)
    if CLOSE.inflate(14, 14).collidepoint(p): close_inv(); return
    for i, r in enumerate(TABR):
        if r.collidepoint(p): inv.update(tab=i, sel=-1, slot=None, soff=0.0); return
    iid, eqd = sel_item()
    if iid:
        for j, r in enumerate(info_btns(eqd)):
            if r.collidepoint(p):
                if j == 0: inv_activate()
                elif j == 1: inv_sell()
                else: inv_drop()
                return
    if TRASH.collidepoint(p): inv_drop(); return
    if inv['tab'] == 5:
        if SET_AREA.collidepoint(p): fingers[fid] = 'sdrag'; inv['drag'] = dict(y0=y, off0=inv['soff'], moved=False, y=y)
        return
    for slot, r in SLOTR.items():
        if r.collidepoint(p):
            if P.eq.get(slot): inv['slot'] = slot; inv['sel'] = -1
            return
    for i in range(min(30, len(flist()))):
        if CELLS[i].collidepoint(p):
            if inv['sel'] == i and not inv['slot']: inv_activate()
            else: inv['sel'] = i; inv['slot'] = None
            return


def move(fid, x, y):
    kind = fingers.get(fid)
    if kind == 'joy': update_joy(x, y)
    elif kind and kind[:2] == 'sk': combat.move(fid, x, y)
    elif kind == 'menu' and menu and menu.get('drag'):
        d = menu['drag']; d['y'] = y
        if abs(y - d['y0']) > 9: d['moved'] = True
        if d['moved']: menu['off'] = clamp(d['off0'] - (y - d['y0']), 0.0, float(menu_geo()[2]))
    elif kind == 'sdrag' and inv.get('drag'):
        d = inv['drag']; d['y'] = y
        if abs(y - d['y0']) > 9: d['moved'] = True
        if d['moved']: inv['soff'] = clamp(d['off0'] - (y - d['y0']), 0.0, float(set_max_off()))


def release(fid, x, y):
    kind = fingers.pop(fid, None)
    if kind == 'joy':
        joy_vec[0] = joy_vec[1] = 0.0; joy_c[0], joy_c[1] = JC0
    elif kind and kind[:2] == 'sk': combat.release(fid, kind)
    elif kind == 'menu' and menu and menu.get('drag'):
        d = menu['drag']; menu['drag'] = None
        if not d['moved']:
            box, lr, mx = menu_geo(); i = int((y - lr.y + menu['off']) // ROW)
            if 0 <= i < len(menu['items']): menu['idx'] = i; menu_activate()
    elif kind == 'sdrag' and inv.get('drag'):
        d = inv['drag']; inv['drag'] = None
        if not d['moved'] and SET_AREA.collidepoint((x, y)):
            i = int((y - SET_AREA.y + inv['soff']) // SROWH)
            if 0 <= i < len(srows()) and srow_rect(i).collidepoint((x, y)): srow_do(i)


def wheel(dy):
    if mode == 'menu' and menu: menu['off'] = clamp(menu['off'] - dy * ROW, 0.0, float(menu_geo()[2]))
    elif mode == 'inv' and inv['tab'] == 5: inv['soff'] = clamp(inv['soff'] - dy * SROWH, 0.0, float(set_max_off()))


def handle_events():
    global touch_seen, last_finger
    for e in pygame.event.get():
        t = e.type
        if t == pygame.QUIT: quit_game()
        elif t == pygame.KEYDOWN: handle_key(e.key)
        elif t in BG_EVENTS: autosave(); reset_touch()
        elif t == pygame.FINGERDOWN and ANDROID:
            last_finger = pygame.time.get_ticks(); touch_seen = True; press(e.finger_id, e.x * W, e.y * H)
        elif t == pygame.FINGERMOTION and ANDROID: move(e.finger_id, e.x * W, e.y * H)
        elif t == pygame.FINGERUP and ANDROID:
            last_finger = pygame.time.get_ticks(); release(e.finger_id, e.x * W, e.y * H)
            if not fingers: joy_vec[0] = joy_vec[1] = 0.0
        elif t == pygame.MOUSEBUTTONDOWN and e.button == 1 and (not ANDROID or pygame.time.get_ticks() - last_finger > 400):
            press('m', e.pos[0], e.pos[1])
        elif t == pygame.MOUSEMOTION and 'm' in fingers: move('m', e.pos[0], e.pos[1])
        elif t == pygame.MOUSEBUTTONUP and e.button == 1 and 'm' in fingers: release('m', e.pos[0], e.pos[1])
        elif t == pygame.MOUSEWHEEL: wheel(e.y)


# ============================================================ 7. UPDATE, DRAW, LOOP
enc_at = 240.0


def update_explore(dt):
    global walk_t, enc_at, door_lock, cur
    now = pygame.time.get_ticks(); kk = pygame.key.get_pressed()
    prev_tm = P.tm; P.tm += dt / MS_PER_MIN
    if P.tm >= 1440: P.tm -= 1440; P.day += 1; on_new_day()
    if prev_tm < NIGHT_START <= P.tm: on_night()
    elif prev_tm < NIGHT_END <= P.tm: on_morning()
    kx = int(bool(kk[K.K_RIGHT] or kk[K.K_d])) - int(bool(kk[K.K_LEFT] or kk[K.K_a]))
    ky = int(bool(kk[K.K_DOWN] or kk[K.K_s])) - int(bool(kk[K.K_UP] or kk[K.K_w]))
    jx, jy = joy_vec; jm = math.hypot(jx, jy)
    if kx or ky: n = math.hypot(kx, ky); vx, vy, mag = kx / n, ky / n, 1.0
    elif jm > 0.2: mag = min(1.0, (jm - 0.2) / 0.55); vx, vy = jx / jm, jy / jm
    else: vx = vy = mag = 0.0
    if combat.locked_move(): vx = vy = mag = 0.0       # sedang Terjang Badai: gerak diatur combat.py
    P.moving = mag > 0
    if P.moving:
        if abs(vx) >= abs(vy): P.d, P.flip = 'side', vx < 0
        else: P.d, P.flip = ('down' if vy > 0 else 'up'), False
        walk_t += dt; P.step = int(walk_t // 95)
        sp = 275.0 * S['speed'] * combat.speed_mult() * min(dt, 50) / 1000.0 * mag; ddx, ddy = vx * sp, vy * sp
        if loc is None:
            ox, oy = P.x, P.y
            if not blocked(P.x + ddx, P.y): P.x += ddx
            if not blocked(P.x, P.y + ddy): P.y += ddy
            P.dist += math.hypot(P.x - ox, P.y - oy)
        else:
            k = 0.85 / cur['s']; ox, oy = P.ix, P.iy
            if int_ok(P.ix + ddx * k, P.iy): P.ix += ddx * k
            if int_ok(P.ix, P.iy + ddy * k): P.iy += ddy * k
    if now < door_lock: return
    f = feet(P.x, P.y)
    if loc is None:
        if area == 'town':
            for iid, r in DOORR.items():
                if f.colliderect(r):
                    if iid == 'windmill' and is_night():
                        note("Guild tutup di malam hari. Kembali saat pagi."); P.x, P.y = DOORS[iid]['out']; door_lock = now + 900; return
                    enter(iid); return
            if f.colliderect(GATE): enter_area('hunt', HENTRY); return
        elif f.colliderect(HEXIT): enter_area('town', GATE_OUT); return
    else:
        fi = ifeet(P.ix, P.iy)
        for lk in cur['links']:
            if fi.colliderect(lk['rect']):
                cur = build_interior(lk['to']); P.ix, P.iy = lk['spawn']; P.d = 'down'; door_lock = now + 700; reset_touch(); return
        if fi.colliderect(cur['exit']): leave()


def update(dt):
    _dq = daily_quest.poll()
    if _dq: apply_daily(_dq)
    if mode == 'explore':
        update_explore(dt)
        if loc is None: update_npcs(dt)
    elif mode == 'dialog': update_dialog(dt)
    if loc is None: combat.update(dt)      # battle real-time (pemain + musuh + proyektil) & respawn musuh


def draw():
    if mode == 'title': draw_title(); return
    if mode == 'charsel': draw_charsel(); return
    if mode == 'error': draw_error(); return
    if mode == 'inv' and inv['snap'] is not None: draw_inv()
    else:
        if loc is None: draw_outdoor()
        else: draw_interior()
        draw_hud()
        if mode == 'explore': draw_touch()
        elif mode == 'dialog' and dialog: draw_dialog()
        elif mode == 'menu' and menu: draw_menu()
    draw_toast()
    if S['show_fps']: txt(f"{int(clock.get_fps())} FPS", W - SAFE_X, H - 22, F_XS, (200, 255, 200), True, 'r')


def handle_crash():
    global mode, err_info
    msg = log_exc('frame').strip().splitlines()
    err_info = dict(msg=msg[-1] if msg else 'Kesalahan tidak diketahui')
    mode = 'error'; reset_touch()


def frame():
    dt = clock.tick(S['fps'])
    perf_watch(dt); handle_events(); update(min(dt, 60)); draw(); pygame.display.flip()


def boot():
    global W, H, SAFE_X, clock
    load_settings(); pygame.init()
    W, H = pick_size(); SAFE_X = 36 if ANDROID else 26
    make_screen(); pygame.display.set_caption('Eldenvale RPG'); clock = pygame.time.Clock(); init_fonts(); sanitize_settings()
    steps = [('Memuat peta...', load_world), ('Memuat karakter...', load_sprites), ('Menyiapkan antarmuka...', load_ui)]
    for i, (lab, fn) in enumerate(steps): splash(lab, i / float(len(steps))); fn()
    splash('Siap', 1.0)
    apply_daily(daily_quest.default_quest()); daily_quest.start_fetch()   # v1.4 misi harian
    combat.bind(sys.modules[__name__]); build_hud(); build_touch(); build_hunt(); new_game(); enter_title()


def main():
    try: boot()
    except Exception:
        log_exc('boot')
        try:
            screen.fill(C_BG); txt("Gagal memuat game. Lihat crash.log", W // 2, H // 2, F_M, C_TEXT, False, 'c'); pygame.display.flip()
        except Exception: pass
        pygame.time.wait(4000) if hasattr(pygame.time, 'wait') else None
        return
    while True:
        try: frame()
        except SystemExit: raise
        except Exception:
            handle_crash()
            try: pygame.display.flip()
            except Exception: pass


if __name__ == '__main__': main()
