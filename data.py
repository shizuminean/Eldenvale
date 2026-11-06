# -*- coding: utf-8 -*-
"""Data game: item, monster, toko, interior rumah."""

GUILD_MASTER = 'Maren si Ketua Guild'   # v1.2


def I(name, typ, icon, val, **kw):
    d = dict(name=name, type=typ, icon=icon, val=val); d.update(kw); return d


ITEMS = {
    # --- senjata ---
    'dagger': I('Belati', 'weapon', '13', 40, atk=3),
    'sword_iron': I('Pedang Besi', 'weapon', '0', 60, atk=4),
    'sword_silver': I('Pedang Perak', 'weapon', '1', 140, atk=7),
    'bow': I('Busur Emas', 'weapon', '10', 160, atk=8),
    'staff': I('Tongkat Kristal', 'weapon', '8', 220, atk=9),
    'halberd': I('Tombak Bulan', 'weapon', '5', 180, atk=9),
    'axe': I('Kapak Perang', 'weapon', '6', 200, atk=11),
    'sword_crystal': I('Pedang Kristal', 'weapon', '3', 320, atk=14),
    'sword_blood': I('Pedang Darah', 'weapon', '2', 600, atk=19),
    # --- helm ---
    'hood': I('Tudung Kain', 'helm', '17b', 45, df=2),
    'hat_wizard': I('Topi Penyihir', 'helm', '17a', 60, df=2),
    'helm_bronze': I('Helm Perunggu', 'helm', '17c', 50, df=3),
    'helm_iron': I('Helm Besi', 'helm', '16', 80, df=4),
    'helm_wing': I('Helm Sayap', 'helm', '14', 220, df=7),
    'helm_wing2': I('Helm Sayap Emas', 'helm', '15', 260, df=8),
    # --- baju ---
    'armor_silver': I('Zirah Perak', 'armor', '19', 180, df=8),
    'armor_gold': I('Zirah Kerajaan', 'armor', '18', 320, df=11),
    'armor_blood': I('Zirah Darah', 'armor', '20', 520, df=14),
    # --- jubah ---
    'cloak_blue': I('Jubah Biru', 'cloak', '21a', 70, df=3),
    'cloak_green': I('Jubah Hutan', 'cloak', '21b', 90, df=3, atk=1),
    # --- aksesori ---
    'ring_sapphire': I('Cincin Safir', 'neck', '26', 120, atk=2),
    'ring_ruby': I('Cincin Perak', 'neck', '27', 150, atk=3),
    'ring_gold': I('Cincin Emas', 'neck', '28', 180, atk=2, df=1),
    'neck_chain': I('Kalung Rantai', 'neck', '29', 100, df=2),
    'neck_sapphire': I('Kalung Safir', 'neck', '30', 200, df=3, atk=1),
    'neck_purple': I('Kalung Ungu', 'neck', '31', 240, atk=4),
    'neck_gold': I('Liontin Emas', 'neck', '32', 260, df=4, atk=1),
    # --- sepatu ---
    'boots_leather': I('Sepatu Kulit', 'boots', '38', 35, df=2),
    'boots_dark': I('Sepatu Gelap', 'boots', '40', 70, df=3),
    'boots_iron': I('Sepatu Besi', 'boots', '39', 90, df=4),
    # --- ramuan ---
    'potion_hp': I('Ramuan Merah', 'use', '42', 8, hp=40, desc='Pulihkan 40 HP'),
    'potion_mp': I('Ramuan Biru', 'use', '43', 10, mp=20, desc='Pulihkan 20 MP'),
    'potion_hp2': I('Ramuan Hijau', 'use', '44', 25, hp=100, desc='Pulihkan 100 HP'),
    'tonic': I('Tonik Mawar', 'use', '49', 6, hp=25, desc='Pulihkan 25 HP'),
    'potion_mp2': I('Ramuan Cyan', 'use', '52', 28, mp=50, desc='Pulihkan 50 MP'),
    'elixir': I('Elixir Emas', 'use', '45', 40, hp=60, mp=30, desc='Pulihkan 60 HP dan 30 MP'),
    # --- makanan ---
    'apple': I('Apel', 'use', '74', 3, hp=12, desc='Pulihkan 12 HP'),
    'bread': I('Roti', 'use', '75', 4, hp=20, desc='Pulihkan 20 HP'),
    'meat': I('Daging Mentah', 'use', '76', 6, hp=35, desc='Pulihkan 35 HP'),
    'fish': I('Ikan', 'use', '77', 5, hp=28, desc='Pulihkan 28 HP'),
    'cheese': I('Keju', 'use', '78', 5, hp=18, desc='Pulihkan 18 HP'),
    'drumstick': I('Paha Ayam', 'use', '79', 9, hp=45, desc='Pulihkan 45 HP'),
    'stew': I('Sup Hangat', 'use', '80', 14, hp=70, mp=10, desc='Pulihkan 70 HP dan 10 MP'),
    'cake': I('Kue', 'use', '81', 12, hp=30, mp=10, desc='Pulihkan 30 HP dan 10 MP'),
    'cupcake': I('Cupcake', 'use', '82', 8, hp=22, desc='Pulihkan 22 HP'),
    'blueberry': I('Blueberry', 'use', '83', 3, hp=8, mp=4, desc='Pulihkan 8 HP dan 4 MP'),
    'grapes': I('Anggur', 'use', '84', 3, hp=8, mp=4, desc='Pulihkan 8 HP dan 4 MP'),
    'carrot': I('Wortel', 'use', '85', 2, hp=10, desc='Pulihkan 10 HP'),
    'cabbage': I('Kubis', 'use', '86', 2, hp=12, desc='Pulihkan 12 HP'),
    # --- bahan ---
    'wood': I('Kayu', 'mat', '65', 6), 'hide': I('Kulit Hewan', 'mat', '66', 10),
    'cloth': I('Kain', 'mat', '68', 8), 'cloth_red': I('Kain Merah', 'mat', '67', 12),
    'horn': I('Tanduk', 'mat', '70', 15), 'bone': I('Tulang', 'mat', '71', 6),
    'iron_bar': I('Besi Batang', 'mat', '64', 25), 'silver_bar': I('Perak Batang', 'mat', '58', 70),
    'gold_bar': I('Emas Batang', 'mat', '57', 120), 'ruby': I('Rubi', 'mat', '59', 60),
    'sapphire': I('Safir', 'mat', '60', 55), 'amethyst': I('Amethyst', 'mat', '61', 50),
    'emerald': I('Zamrud', 'mat', '62', 50), 'topaz': I('Topaz', 'mat', '63', 45),
    'gem_blue': I('Kristal Biru', 'mat', '56', 40), 'pearl': I('Mutiara Merah Muda', 'mat', '72', 90),
    'shard': I('Pecahan Kristal', 'mat', '73', 20), 'ice_crystal': I('Kristal Es', 'mat', '95', 40),
    'orb': I('Orb Ungu', 'mat', '96', 150), 'ess_water': I('Esensi Air', 'mat', '97', 18),
    'ess_leaf': I('Esensi Daun', 'mat', '98', 18), 'ess_fire': I('Esensi Api', 'mat', '99', 22),
    # --- lain-lain ---
    'key_gold': I('Kunci Emas', 'misc', '100', 30), 'map': I('Peta Desa', 'misc', '54', 20),
    'letter': I('Surat Bersegel', 'misc', '55', 10), 'book': I('Buku Sihir', 'misc', '103', 80),
}
for k, v in ITEMS.items(): v['id'] = k
SLOT_OF = {'weapon': 'weapon', 'helm': 'helm', 'armor': 'armor', 'cloak': 'cloak', 'neck': 'neck', 'boots': 'boots'}
SLOT_NAME = {'helm': 'Helm', 'cloak': 'Jubah', 'neck': 'Aksesori', 'weapon': 'Senjata', 'armor': 'Baju', 'boots': 'Sepatu'}
TABS = ['Semua', 'Senjata', 'Perlengkapan', 'Ramuan & Makanan', 'Bahan & Lainnya', 'Setelan']

SHOP_ORN = [('potion_hp', 15), ('potion_mp', 20), ('potion_hp2', 45), ('elixir', 80), ('bread', 8), ('apple', 5), ('stew', 30)]
SHOP_BROM = [('dagger', 40), ('sword_iron', 120), ('sword_silver', 280), ('axe', 400), ('helm_bronze', 90), ('helm_iron', 160),
             ('armor_silver', 360), ('cloak_blue', 110), ('boots_leather', 70), ('boots_iron', 150)]


def M(name, img, hp, atk, xp, gold, size, tier, drops):
    return dict(name=name, img=img, hp=hp, atk=atk, xp=xp, gold=gold, size=size, tier=tier, drops=drops)


MONSTERS = [
    M('Slime Biru', '0', 22, 6, 9, 7, 110, 1, [('ess_water', .35), ('apple', .15), ('potion_hp', .06)]),
    M('Slime Hijau', '1', 26, 7, 11, 8, 110, 1, [('ess_leaf', .35), ('cabbage', .2), ('potion_hp', .06)]),
    M('Slime Ungu', '2', 30, 8, 13, 9, 100, 1, [('amethyst', .18), ('ess_water', .25), ('potion_mp', .08)]),
    M('Slime Jingga', '3', 28, 8, 12, 9, 130, 1, [('ess_fire', .3), ('carrot', .2)]),
    M('Kelelawar', '11', 24, 8, 11, 8, 120, 1, [('bone', .3), ('cloth_red', .12)]),
    M('Babi Hutan', '7', 42, 9, 16, 11, 170, 1, [('meat', .5), ('hide', .4)]),
    M('Serigala Hitam', '5', 55, 13, 24, 18, 190, 2, [('hide', .55), ('bone', .3), ('boots_leather', .04)]),
    M('Serigala Putih', '6', 60, 14, 26, 19, 190, 2, [('hide', .5), ('shard', .2), ('cloak_blue', .03)]),
    M('Goblin', '13', 46, 11, 20, 14, 210, 2, [('iron_bar', .25), ('apple', .2), ('sword_iron', .05), ('dagger', .08)]),
    M('Goblin Perisai', '14', 55, 12, 24, 16, 200, 2, [('iron_bar', .3), ('helm_bronze', .06), ('bread', .25)]),
    M('Goblin Pemanah', '17', 40, 13, 22, 15, 210, 2, [('wood', .4), ('bow', .05), ('cloth', .2)]),
    M('Bandit', '15', 48, 14, 26, 24, 210, 2, [('gold_bar', .05), ('potion_hp', .2), ('hood', .08), ('ring_gold', .04)]),
    M('Laba-laba Merah', '9', 50, 13, 25, 17, 200, 2, [('cloth_red', .2), ('ruby', .1), ('horn', .1)]),
    M('Kerangka', '19', 62, 14, 28, 20, 220, 2, [('bone', .7), ('helm_iron', .05), ('sword_silver', .03)]),
    M('Kerangka Penyihir', '20', 50, 16, 30, 22, 220, 2, [('bone', .5), ('staff', .05), ('potion_mp', .2), ('hat_wizard', .06)]),
    M('Zombie', '22', 80, 17, 40, 28, 230, 3, [('cloth', .3), ('bone', .4), ('potion_hp2', .08)]),
    M('Ghoul', '23', 90, 19, 46, 32, 230, 3, [('horn', .3), ('emerald', .12), ('boots_dark', .05)]),
    M('Hantu Tengkorak', '27', 70, 20, 48, 34, 220, 3, [('ess_water', .4), ('orb', .08), ('neck_purple', .08)]),
    M('Kesatria Kerangka', '28', 110, 21, 60, 40, 250, 3, [('iron_bar', .5), ('armor_silver', .06), ('helm_wing', .05), ('sword_crystal', .02)]),
    M('Golem Lumut', '30', 140, 22, 70, 46, 250, 3, [('ess_leaf', .4), ('emerald', .2), ('topaz', .15)]),
    M('Kobra', '40', 85, 21, 50, 33, 220, 3, [('hide', .4), ('horn', .2), ('potion_mp2', .1)]),
    M('Kalajengking', '41', 80, 22, 52, 34, 210, 3, [('horn', .4), ('ruby', .12)]),
    M('Treant', '38', 130, 21, 66, 44, 260, 3, [('wood', .7), ('ess_leaf', .4), ('cloak_green', .06)]),
    M('Tanaman Buas', '39', 95, 20, 55, 36, 230, 3, [('ess_leaf', .5), ('cabbage', .4), ('stew', .1)]),
    M('Golem Kristal', '31', 150, 24, 78, 52, 250, 3, [('sapphire', .3), ('shard', .4), ('ice_crystal', .2), ('neck_sapphire', .05)]),
    M('Naga Kecil', '44', 120, 25, 80, 55, 240, 3, [('ess_fire', .4), ('topaz', .2), ('armor_gold', .03), ('sword_blood', .02)]),
    M('Raja Slime', '4', 220, 16, 140, 160, 270, 9, [('orb', .6), ('pearl', .4), ('gold_bar', .3), ('elixir', .5)]),
    M('Vampir', '48', 300, 26, 260, 300, 330, 9, [('armor_blood', .15), ('sword_blood', .1), ('gold_bar', .5), ('orb', .4)]),
]
BOSS_NEAR, BOSS_FAR = 'Raja Slime', 'Vampir'

# pintu luar (koordinat peta) -> interior
DOORS = {
    'inn': dict(trig=(612, 268, 40, 24), out=(632, 302)),
    'church': dict(trig=(868, 262, 50, 26), out=(893, 300)),
    'potion': dict(trig=(1172, 312, 42, 22), out=(1193, 346)),
    'smith': dict(trig=(520, 477, 50, 22), out=(545, 512)),
    'green': dict(trig=(1185, 487, 50, 22), out=(1210, 522)),
    'windmill': dict(trig=(412, 604, 24, 22), out=(424, 642)),   # v1.2: kincir angin = Guild Petualang
}
# interior: crop = bbox pada gambar asli; semua rect memakai koordinat gambar asli
INTERIORS = {
    'inn': dict(crop=(12, 28, 414, 418), floor=[(45, 150, 345, 246)], solid=[(70, 262, 70, 50), (62, 318, 75, 48), (300, 305, 90, 55)],
                exit=(130, 385, 150, 22), spawn=(205, 368), npc=('Rosalind', 'n01', 'inn', (250, 235))),
    'potion': dict(crop=(1108, 32, 1522, 424), floor=[(1140, 200, 350, 195)], solid=[(1290, 225, 130, 65)],
                   exit=(1235, 385, 110, 22), spawn=(1290, 368), npc=('Penyihir Orn', 'n25', 'shop', (1330, 305))),
    'smith': dict(crop=(30, 446, 430, 692), floor=[(45, 545, 365, 130)], solid=[(85, 548, 100, 55), (190, 612, 48, 40), (270, 590, 80, 45)],
                  exit=(255, 662, 90, 22), spawn=(300, 648), npc=('Brom si Pandai Besi', 'n02', 'smith', (150, 635))),
    'green': dict(crop=(1116, 450, 1516, 752), floor=[(1135, 600, 355, 140)], solid=[(1205, 640, 90, 45), (1300, 612, 60, 60), (1135, 600, 45, 60)],
                  exit=(1210, 722, 90, 22), spawn=(1255, 700), npc=('Nenek Wren', 'n04', 'granny', (1410, 665))),
    'church': dict(crop=(455, 2, 1092, 602), floor=[(495, 365, 530, 150), (690, 290, 195, 255)], solid=[(540, 395, 70, 95), (950, 400, 55, 55)],
                   exit=(735, 520, 95, 25), spawn=(782, 498), npc=('Pendeta Elias', 'n10', 'priest', (700, 440))),
    # v1.2 guild petualang (gambar dibuat khusus, koordinat = piksel gambar, crop nol)
    'windmill': dict(crop=(0, 0, 420, 300), floor=[(18, 186, 384, 110)], solid=[(118, 150, 184, 36), (320, 222, 64, 36)],
                     exit=(190, 280, 40, 20), spawn=(210, 255), npc=(GUILD_MASTER, 'n11', 'guild', (210, 128))),
}

# monster berburu yang terlihat di peta Hutan Berburu: (nama, x, y, radius jelajah)
HUNT_SPAWNS = [('Slime Hijau', 616, 504, 70), ('Slime Ungu', 696, 568, 60), ('Slime Biru', 760, 488, 60), ('Kelelawar', 552, 424, 80),
               ('Babi Hutan', 488, 600, 70), ('Serigala Hitam', 360, 360, 70), ('Serigala Putih', 424, 472, 70), ('Goblin', 792, 696, 70),
               ('Goblin Pemanah', 888, 696, 60), ('Laba-laba Merah', 568, 664, 60), ('Kerangka', 328, 232, 50), ('Bandit', 584, 440, 60),
               ('Kobra', 664, 600, 40), ('Zombie', 1304, 392, 70), ('Ghoul', 1192, 440, 60), ('Golem Lumut', 1336, 472, 50), ('Vampir', 328, 168, 40),
               ('Raja Slime', 728, 568, 30)]   # v1.2: boss dipindah ke hutan (dulu hanya di battle acak desa)


# ================= v1.2 =================

# misi guild (papan di kincir angin). kind 'kill' = hitung kemenangan melawan monster yang namanya memuat `match`;
# kind 'item' = hitung item `match` di tas. Hadiah: gold, xp, dan (opsional) satu item.
GQ = [
    dict(id='wolf', name='Berburu Serigala', desc='Kalahkan 3 Serigala di Hutan Berburu.', kind='kill', match='Serigala',
         need=3, xp=60, gold=150, item=None),
    dict(id='goblin', name='Basmi Goblin', desc='Kalahkan 4 Goblin di Hutan Berburu.', kind='kill', match='Goblin',
         need=4, xp=80, gold=180, item='potion_hp2'),
    dict(id='crystal', name='Pecahan Kristal', desc='Kumpulkan 2 Pecahan Kristal (jatuhan Serigala Putih).', kind='item',
         match='shard', need=2, xp=50, gold=160, item=None),
    dict(id='boss', name='Pemburu Raja', desc='Kalahkan Raja Slime di Hutan Berburu.', kind='kill', match='Raja Slime',
         need=1, xp=150, gold=400, item='helm_wing'),
]

# posisi (koordinat peta-interior, pusat sprite) tempat NPC tidur di penginapan saat malam
SLEEP_SPOTS = [(110, 128), (168, 268), (165, 178), (240, 184), (300, 190), (205, 372)]

# objek yang harus menghalangi langkah di peta desa (kursi, pagar, pohon, plang, batu, tiang, meja pedagang)
TOWN_SOLID = [
    # kursi taman
    (137, 412, 30, 14), (193, 414, 34, 14), (790, 302, 38, 13), (958, 305, 30, 16), (507, 530, 73, 24), (602, 528, 70, 30),
    # tunggul & kemah
    (122, 402, 14, 12), (229, 404, 22, 14), (265, 262, 22, 12), (357, 812, 22, 14), (1322, 790, 22, 14), (1462, 820, 22, 14),
    (170, 372, 24, 16), (44, 332, 74, 36), (146, 318, 46, 34),
    # lapak pedagang
    (1262, 268, 46, 16), (1218, 300, 44, 30),
    # papan nama / plang tukang besi
    (580, 370, 26, 16),
    # pagar
    (107, 566, 156, 14), (376, 160, 12, 322), (400, 468, 200, 14), (1233, 488, 140, 18), (1100, 565, 80, 16),
    (1355, 393, 18, 88), (953, 653, 75, 18),
    # pagar ladang (dengan celah di sisi barat untuk jalan ke kincir angin)
    (337, 575, 66, 16), (337, 575, 12, 23), (337, 652, 12, 25), (337, 657, 473, 20), (560, 563, 120, 12),
    # kincir angin (menara) & tumpukan ladang yang bisa dilalui hanya di pintunya
    (386, 520, 74, 86), (455, 585, 355, 72),
    # tiang gerbang plaza
    (823, 600, 24, 70), (923, 600, 30, 70),
    # tembok batu & batu
    (52, 740, 186, 50), (1400, 700, 55, 110), (647, 686, 36, 22),
    # pohon (batang pohon / batas tanaman, ukuran kecil di tanah)
    (333, 296, 14, 10), (420, 208, 14, 10), (340, 414, 14, 10), (350, 336, 12, 10), (106, 281, 14, 10),
    (286, 682, 14, 10), (103, 703, 14, 10), (273, 521, 14, 10), (286, 834, 14, 10), (223, 834, 14, 10), (453, 850, 14, 10),
    (573, 835, 14, 10), (746, 893, 14, 10), (696, 536, 14, 10), (936, 566, 14, 10), (1006, 601, 16, 12), (626, 404, 14, 10),
    (742, 216, 16, 12), (1042, 288, 16, 10), (1286, 228, 14, 10), (1313, 388, 14, 10), (1386, 388, 14, 10), (1420, 240, 14, 10),
    (1186, 852, 14, 10), (1486, 787, 14, 10),
]
