# -*- coding: utf-8 -*-
"""Desas-desus dinamis dari Groq (opsional). Kunci TIDAK ditanam di kode.

Sumber kunci (urutan): environment variable GROQ_API_KEY, lalu file groq_key.txt di folder game.
Jika kunci tidak ada atau jaringan gagal, game memakai teks cadangan (tidak pernah crash).
Panggilan berjalan di thread terpisah agar layar tidak macet.
"""
import os, json, threading, urllib.request

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.1-8b-instant"
RUMORS = []
_busy = [False]


def _key(base):
    k = os.environ.get("GROQ_API_KEY", "").strip()
    if k: return k
    try:
        with open(os.path.join(base, "groq_key.txt"), encoding="utf-8") as f: return f.read().strip()
    except OSError:
        return ""


def fetch_async(base):
    """Minta satu desas-desus baru di latar belakang. Hasilnya masuk ke RUMORS."""
    if _busy[0] or len(RUMORS) >= 3: return
    key = _key(base)
    if not key: return
    _busy[0] = True

    def run():
        try:
            body = json.dumps({
                "model": MODEL, "max_tokens": 60, "temperature": 0.9,
                "messages": [
                    {"role": "system", "content": "Kamu penulis dialog game RPG fantasi bernama Eldenvale. "
                     "Tulis SATU kalimat pendek (maks 25 kata) berbahasa Indonesia berupa desas-desus atau ramalan. "
                     "Tanpa tanda kutip, tanpa awalan."},
                    {"role": "user", "content": "Buat satu desas-desus baru untuk pahlawan yang sedang bertanya."}]}).encode("utf-8")
            req = urllib.request.Request(GROQ_URL, data=body, headers={
                "Authorization": "Bearer " + key, "Content-Type": "application/json",
                "User-Agent": "EldenvaleRPG/1.3"})
            with urllib.request.urlopen(req, timeout=8) as r:
                text = json.load(r)["choices"][0]["message"]["content"].strip()
            if text: RUMORS.append(text.strip('"')[:180])
        except Exception:
            pass
        finally:
            _busy[0] = False

    threading.Thread(target=run, daemon=True).start()


def pop_rumor():
    return RUMORS.pop(0) if RUMORS else None
