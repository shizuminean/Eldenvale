# -*- coding: utf-8 -*-
"""Misi harian. Dibuat oleh AI (Groq) lewat GitHub Action, lalu diambil game dari URL raw GitHub.

Kunci API TIDAK ada di game. Game hanya membaca JSON publik, dan setiap isinya divalidasi.
Jika jaringan gagal atau JSON tidak valid, game memakai assets/daily_default.json.
Modul ini tidak memakai pygame, sehingga bisa dipakai juga oleh script generator.
"""
import os, json, threading, urllib.request
from data import MONSTERS, HUNT_SPAWNS, ITEMS

# Ganti dengan URL raw file quests/daily.json di repo Anda, contoh:
# https://raw.githubusercontent.com/NAMA_USER/NAMA_REPO/main/quests/daily.json
DAILY_URL = "https://raw.githubusercontent.com/shizuminean/Eldenvale/main/quests/daily.json"

KILL_TARGETS = sorted({s[0] for s in HUNT_SPAWNS})
_SPAWNED = {s[0] for s in HUNT_SPAWNS}   # hanya monster yang benar-benar muncul di hutan
DROP_ITEMS = sorted({d[0] for m in MONSTERS if m['name'] in _SPAWNED for d in m['drops']})
_BASE = os.path.dirname(os.path.abspath(__file__))
_result = []
_started = [False]


def validate(raw):
    """Kembalikan dict quest yang aman, atau None jika tidak valid."""
    try:
        q = raw['quest'] if isinstance(raw, dict) and 'quest' in raw else raw
        date = str(raw.get('date', 'x')) if isinstance(raw, dict) else 'x'
        kind, match = q['kind'], str(q['match'])
        need = int(q['need']); xp = int(q.get('xp', 60)); gold = int(q.get('gold', 120))
        title = str(q['title']).strip()[:30]; desc = str(q['desc']).strip()[:90]
        item = q.get('item') or None
    except (KeyError, TypeError, ValueError, AttributeError):
        return None
    if not title or not desc: return None
    if kind == 'kill':
        if match not in KILL_TARGETS or not 1 <= need <= 6: return None
    elif kind == 'item':
        if match not in DROP_ITEMS or not 1 <= need <= 4: return None
    else:
        return None
    if not (20 <= xp <= 200 and 50 <= gold <= 300): return None
    if item is not None and item not in ITEMS: return None
    return dict(id='daily-' + date, name=title, desc=desc, kind=kind, match=match, need=need,
                xp=xp, gold=gold, item=item, daily=True)


def default_quest():
    try:
        with open(os.path.join(_BASE, 'assets', 'daily_default.json'), encoding='utf-8') as f:
            return validate(json.load(f))
    except (OSError, ValueError):
        return None


def start_fetch(timeout=4):
    """Ambil misi harian dari internet di thread terpisah (tidak membuat layar macet)."""
    if _started[0]: return
    _started[0] = True

    def run():
        try:
            req = urllib.request.Request(DAILY_URL, headers={'User-Agent': 'EldenvaleRPG/1.4'})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                q = validate(json.load(r))
            if q: _result.append(q)
        except Exception:
            pass
    threading.Thread(target=run, daemon=True).start()


def poll():
    """Kembalikan quest harian dari internet sekali saja, setelah tersedia."""
    return _result.pop(0) if _result else None
