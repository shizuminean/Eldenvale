"""Dijalankan GitHub Action setiap hari. Meminta Groq membuat satu misi, memvalidasinya, lalu menulis quests/daily.json.

Kunci diambil dari environment GROQ_API_KEY (GitHub secret). Jika AI gagal atau hasilnya tidak valid,
misi dipilih secara deterministik dari tanggal, sehingga misi tetap berganti setiap hari.
"""
import os, sys, json, random, datetime, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import daily_quest as dq
from data import ITEMS

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.1-8b-instant"
TODAY = datetime.datetime.now(datetime.timezone.utc).date().isoformat()


def ask_ai(key):
    prompt = (
        "Buat SATU misi harian untuk game RPG fantasi Eldenvale dalam Bahasa Indonesia. "
        "Balas HANYA JSON dengan kunci: title (maks 30 karakter), desc (maks 90 karakter), "
        "kind ('kill' atau 'item'), match, need, xp (20-200), gold (50-300), item (id item hadiah atau null).\n"
        f"Jika kind='kill', match HARUS salah satu dari: {json.dumps(dq.KILL_TARGETS, ensure_ascii=False)}; need 1-6.\n"
        f"Jika kind='item', match HARUS salah satu dari: {json.dumps(dq.DROP_ITEMS)}; need 1-4.\n"
        f"Item hadiah harus salah satu dari: {json.dumps(sorted(ITEMS))} atau null.")
    body = json.dumps({"model": MODEL, "max_tokens": 250, "temperature": 0.9,
                       "messages": [{"role": "user", "content": prompt}]}).encode("utf-8")
    req = urllib.request.Request(GROQ_URL, data=body, headers={
        "Authorization": "Bearer " + key, "Content-Type": "application/json", "User-Agent": "EldenvaleRPG-gen/1.4"})
    with urllib.request.urlopen(req, timeout=30) as r:
        text = json.load(r)["choices"][0]["message"]["content"]
    return json.loads(text[text.index("{"): text.rindex("}") + 1])


def fallback():
    rng = random.Random(TODAY)
    target = rng.choice(dq.KILL_TARGETS)
    return {"title": f"Buru {target}", "desc": f"Kalahkan 3 {target} di Hutan Berburu.", "kind": "kill",
            "match": target, "need": 3, "xp": 60, "gold": 130, "item": None}


def main():
    key = os.environ.get("GROQ_API_KEY", "").strip()
    quest = None
    if key:
        for attempt in range(2):
            try:
                quest = dq.validate({"date": TODAY, "quest": ask_ai(key)})
                if quest: break
            except Exception as e:
                print("AI gagal:", e)
    else:
        print("GROQ_API_KEY kosong, memakai misi cadangan.")
    if not quest:
        quest = dq.validate({"date": TODAY, "quest": fallback()})
    out = {"date": TODAY, "quest": {k: quest[k] for k in ("name", "desc", "kind", "match", "need", "xp", "gold", "item")}}
    out["quest"]["title"] = out["quest"].pop("name")
    with open(os.path.join(ROOT, "quests", "daily.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("Misi harian:", out["quest"]["title"], "-", out["quest"]["desc"])


if __name__ == "__main__":
    main()
