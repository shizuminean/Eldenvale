# -*- coding: utf-8 -*-
"""Data game: item, monster, toko, interior rumah."""

GUILD_MASTER = 'Maren si Ketua Guild'   # v1.2


def I(name, typ, icon, val, **kw):
    d = dict(name=name, type=typ, icon=icon, val=val); d.update(kw); return d


ITEMS = {
    'seed_wheat': I('Benih Gandum', 'misc', 'seed_wheat', 6, desc='Tanam di kebun, panen setelah tumbuh.'),
    'seed_cabbage': I('Benih Kubis', 'misc', 'seed_cabbage', 8, desc='Tanam di kebun, panen setelah tumbuh.'),
    'seed_carrot': I('Benih Wortel', 'misc', 'seed_carrot', 7, desc='Tanam di kebun, panen setelah tumbuh.'),
    'wheat': I('Gandum', 'mat', 'crop_wheat', 6),
    'cabbage': I('Kubis', 'mat', 'crop_cabbage', 9),
    'carrot': I('Wortel', 'mat', 'crop_carrot', 7),
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

# v1.4: desa dibangun ulang (dari aset tanah, bangunan, pohon & lahan). Dibuat otomatis oleh gen_town.py.
TOWN = {'cell': 8, 'cw': 210, 'ch': 118, 'W': 1672, 'H': 941, 'rows': [[0, 0, 208], [1, 0, 208], [2, 0, 1], [2, 47, 48], [2, 63, 65], [2, 77, 81], [2, 87, 93], [2, 107, 107], [2, 116, 118], [2, 129, 130], [2, 159, 172], [2, 183, 199], [2, 207, 208], [3, 0, 1], [3, 11, 15], [3, 45, 58], [3, 61, 68], [3, 76, 93], [3, 105, 120], [3, 127, 133], [3, 135, 135], [3, 137, 138], [3, 162, 172], [3, 182, 199], [3, 207, 208], [4, 0, 1], [4, 9, 21], [4, 44, 95], [4, 102, 140], [4, 162, 174], [4, 180, 200], [4, 207, 208], [5, 0, 1], [5, 7, 21], [5, 35, 140], [5, 164, 200], [5, 207, 208], [6, 0, 1], [6, 6, 23], [6, 25, 25], [6, 27, 27], [6, 33, 88], [6, 91, 141], [6, 144, 145], [6, 164, 208], [7, 0, 81], [7, 92, 106], [7, 108, 129], [7, 131, 131], [7, 134, 152], [7, 166, 208], [8, 0, 45], [8, 52, 52], [8, 59, 59], [8, 63, 67], [8, 69, 79], [8, 90, 104], [8, 109, 112], [8, 115, 116], [8, 137, 153], [8, 162, 162], [8, 168, 208], [9, 0, 44], [9, 67, 76], [9, 91, 91], [9, 94, 104], [9, 140, 155], [9, 161, 162], [9, 169, 208], [10, 0, 9], [10, 11, 11], [10, 15, 16], [10, 18, 39], [10, 42, 43], [10, 71, 71], [10, 96, 102], [10, 141, 162], [10, 171, 208], [11, 0, 9], [11, 18, 19], [11, 21, 39], [11, 147, 162], [11, 172, 196], [11, 199, 208], [12, 0, 5], [12, 20, 34], [12, 37, 37], [12, 152, 163], [12, 172, 196], [12, 200, 208], [13, 0, 1], [13, 4, 5], [13, 7, 7], [13, 27, 31], [13, 152, 162], [13, 176, 177], [13, 180, 196], [13, 204, 204], [13, 207, 208], [14, 0, 1], [14, 161, 161], [14, 178, 197], [14, 207, 208], [15, 0, 1], [15, 164, 164], [15, 180, 198], [15, 207, 208], [16, 0, 1], [16, 129, 130], [16, 139, 140], [16, 164, 166], [16, 180, 189], [16, 191, 192], [16, 194, 198], [16, 207, 208], [17, 0, 1], [17, 129, 130], [17, 138, 141], [17, 155, 158], [17, 165, 166], [17, 181, 197], [17, 207, 208], [18, 0, 1], [18, 129, 149], [18, 151, 159], [18, 161, 166], [18, 182, 196], [18, 207, 208], [19, 0, 1], [19, 128, 166], [19, 184, 195], [19, 207, 208], [20, 0, 1], [20, 127, 127], [20, 130, 166], [20, 184, 195], [20, 207, 208], [21, 0, 1], [21, 129, 129], [21, 131, 168], [21, 184, 197], [21, 207, 208], [22, 0, 1], [22, 137, 151], [22, 155, 168], [22, 184, 199], [22, 207, 208], [23, 0, 1], [23, 137, 148], [23, 155, 168], [23, 184, 200], [23, 207, 208], [24, 0, 1], [24, 140, 146], [24, 165, 170], [24, 184, 204], [24, 207, 208], [25, 0, 1], [25, 167, 172], [25, 185, 204], [25, 207, 208], [26, 0, 1], [26, 167, 171], [26, 185, 204], [26, 207, 208], [27, 0, 1], [27, 167, 167], [27, 169, 169], [27, 171, 172], [27, 182, 203], [27, 207, 208], [28, 0, 1], [28, 171, 175], [28, 181, 203], [28, 207, 208], [29, 0, 1], [29, 117, 139], [29, 146, 166], [29, 170, 202], [29, 207, 208], [30, 0, 1], [30, 6, 6], [30, 81, 106], [30, 117, 139], [30, 146, 166], [30, 171, 198], [30, 207, 208], [31, 0, 1], [31, 8, 8], [31, 81, 106], [31, 117, 139], [31, 146, 166], [31, 172, 198], [31, 207, 208], [32, 0, 1], [32, 6, 8], [32, 32, 55], [32, 81, 106], [32, 117, 139], [32, 146, 166], [32, 172, 197], [32, 207, 208], [33, 0, 8], [33, 32, 55], [33, 81, 106], [33, 117, 139], [33, 146, 166], [33, 179, 179], [33, 181, 196], [33, 207, 208], [34, 0, 8], [34, 32, 55], [34, 81, 106], [34, 117, 139], [34, 146, 166], [34, 183, 195], [34, 207, 208], [35, 0, 8], [35, 32, 55], [35, 81, 106], [35, 117, 139], [35, 146, 166], [35, 207, 208], [36, 0, 8], [36, 32, 55], [36, 81, 106], [36, 117, 139], [36, 146, 166], [36, 207, 208], [37, 0, 5], [37, 7, 7], [37, 32, 55], [37, 81, 106], [37, 117, 139], [37, 146, 166], [37, 186, 192], [37, 207, 208], [38, 0, 3], [38, 5, 6], [38, 32, 55], [38, 81, 106], [38, 117, 139], [38, 146, 166], [38, 184, 195], [38, 207, 208], [39, 0, 1], [39, 32, 55], [39, 81, 106], [39, 117, 139], [39, 146, 166], [39, 183, 195], [39, 207, 208], [40, 0, 1], [40, 32, 55], [40, 74, 77], [40, 81, 106], [40, 117, 126], [40, 132, 139], [40, 146, 156], [40, 161, 166], [40, 169, 171], [40, 183, 196], [40, 207, 208], [41, 0, 1], [41, 32, 55], [41, 74, 77], [41, 81, 106], [41, 169, 171], [41, 183, 196], [41, 207, 208], [42, 0, 1], [42, 32, 55], [42, 74, 77], [42, 81, 106], [42, 169, 171], [42, 183, 197], [42, 207, 208], [43, 0, 1], [43, 32, 44], [43, 50, 55], [43, 81, 106], [43, 183, 198], [43, 207, 208], [44, 0, 1], [44, 184, 198], [44, 207, 208], [45, 0, 1], [45, 184, 199], [45, 207, 208], [46, 0, 1], [46, 184, 198], [46, 207, 208], [47, 0, 1], [47, 184, 201], [47, 207, 208], [48, 0, 1], [48, 185, 200], [48, 207, 208], [49, 0, 1], [49, 184, 199], [49, 207, 208], [50, 0, 1], [50, 183, 200], [50, 207, 208], [51, 0, 1], [51, 183, 208], [52, 0, 1], [52, 182, 195], [52, 197, 208], [53, 0, 1], [53, 182, 196], [53, 198, 208], [54, 0, 1], [54, 181, 195], [54, 198, 208], [55, 0, 1], [55, 180, 195], [55, 198, 208], [56, 0, 1], [56, 180, 195], [56, 199, 208], [57, 0, 1], [57, 180, 195], [57, 201, 208], [58, 0, 1], [58, 176, 196], [58, 200, 201], [58, 207, 208], [59, 0, 1], [59, 176, 196], [59, 207, 208], [60, 0, 1], [60, 97, 108], [60, 176, 195], [60, 207, 208], [61, 0, 1], [61, 14, 17], [61, 97, 108], [61, 175, 195], [61, 207, 208], [62, 0, 1], [62, 14, 17], [62, 97, 108], [62, 175, 193], [62, 195, 195], [62, 207, 208], [63, 0, 1], [63, 14, 17], [63, 97, 108], [63, 142, 144], [63, 174, 192], [63, 207, 208], [64, 0, 1], [64, 97, 108], [64, 142, 144], [64, 174, 192], [64, 207, 208], [65, 0, 1], [65, 97, 108], [65, 142, 144], [65, 161, 169], [65, 174, 192], [65, 207, 208], [66, 0, 1], [66, 97, 108], [66, 161, 169], [66, 173, 193], [66, 207, 208], [67, 0, 1], [67, 20, 42], [67, 97, 108], [67, 161, 169], [67, 171, 189], [67, 191, 191], [67, 207, 208], [68, 0, 1], [68, 20, 42], [68, 97, 108], [68, 161, 185], [68, 207, 208], [69, 0, 1], [69, 20, 42], [69, 97, 108], [69, 161, 183], [69, 207, 208], [70, 0, 1], [70, 20, 42], [70, 53, 71], [70, 159, 182], [70, 207, 208], [71, 0, 1], [71, 20, 42], [71, 53, 71], [71, 157, 180], [71, 207, 208], [72, 0, 1], [72, 20, 42], [72, 53, 71], [72, 157, 180], [72, 207, 208], [73, 0, 1], [73, 20, 42], [73, 53, 71], [73, 157, 179], [73, 207, 208], [74, 0, 1], [74, 20, 42], [74, 53, 71], [74, 136, 136], [74, 139, 139], [74, 141, 147], [74, 149, 152], [74, 156, 179], [74, 207, 208], [75, 0, 1], [75, 20, 42], [75, 53, 71], [75, 136, 179], [75, 207, 208], [76, 0, 1], [76, 20, 42], [76, 53, 71], [76, 137, 178], [76, 207, 208], [77, 0, 1], [77, 20, 42], [77, 53, 71], [77, 134, 177], [77, 207, 208], [78, 0, 1], [78, 20, 42], [78, 53, 71], [78, 133, 176], [78, 207, 208], [79, 0, 1], [79, 20, 42], [79, 53, 71], [79, 129, 175], [79, 207, 208], [80, 0, 1], [80, 15, 42], [80, 53, 71], [80, 105, 113], [80, 128, 175], [80, 207, 208], [81, 0, 1], [81, 15, 23], [81, 29, 42], [81, 53, 71], [81, 105, 113], [81, 129, 174], [81, 207, 208], [82, 0, 1], [82, 15, 22], [82, 53, 71], [82, 105, 113], [82, 129, 172], [82, 174, 174], [82, 207, 208], [83, 0, 1], [83, 15, 22], [83, 105, 113], [83, 129, 172], [83, 207, 208], [84, 0, 1], [84, 105, 113], [84, 129, 170], [84, 207, 208], [85, 0, 1], [85, 105, 113], [85, 128, 163], [85, 207, 208], [86, 0, 1], [86, 105, 113], [86, 129, 162], [86, 207, 208], [87, 0, 1], [87, 3, 4], [87, 90, 92], [87, 130, 162], [87, 207, 208], [88, 0, 6], [88, 90, 92], [88, 131, 161], [88, 167, 174], [88, 207, 208], [89, 0, 7], [89, 90, 92], [89, 132, 160], [89, 167, 174], [89, 199, 200], [89, 207, 208], [90, 0, 7], [90, 90, 92], [90, 151, 151], [90, 154, 155], [90, 167, 174], [90, 199, 200], [90, 207, 208], [91, 0, 10], [91, 90, 92], [91, 167, 174], [91, 199, 208], [92, 0, 11], [92, 199, 208], [93, 0, 12], [93, 199, 208], [94, 0, 11], [94, 27, 28], [94, 199, 208], [95, 0, 1], [95, 5, 13], [95, 24, 28], [95, 200, 208], [96, 0, 1], [96, 6, 14], [96, 23, 28], [96, 200, 208], [97, 0, 1], [97, 6, 17], [97, 20, 28], [97, 200, 208], [98, 0, 1], [98, 8, 27], [98, 201, 208], [99, 0, 1], [99, 8, 27], [99, 201, 203], [99, 206, 208], [100, 0, 1], [100, 7, 26], [100, 202, 202], [100, 206, 208], [101, 0, 1], [101, 11, 24], [101, 26, 26], [101, 205, 205], [101, 207, 208], [102, 0, 1], [102, 13, 23], [102, 204, 205], [102, 207, 208], [103, 0, 1], [103, 14, 22], [103, 96, 99], [103, 110, 113], [103, 207, 208], [104, 0, 1], [104, 96, 98], [104, 111, 113], [104, 164, 164], [104, 174, 175], [104, 207, 208], [105, 0, 1], [105, 31, 98], [105, 111, 161], [105, 163, 164], [105, 174, 175], [105, 207, 208], [106, 0, 1], [106, 31, 98], [106, 111, 161], [106, 167, 167], [106, 169, 175], [106, 177, 178], [106, 207, 208], [107, 0, 1], [107, 31, 98], [107, 111, 161], [107, 166, 175], [107, 179, 180], [107, 207, 208], [108, 0, 1], [108, 31, 98], [108, 111, 161], [108, 166, 175], [108, 179, 182], [108, 207, 208], [109, 0, 1], [109, 31, 98], [109, 111, 161], [109, 165, 180], [109, 207, 208], [110, 0, 1], [110, 154, 154], [110, 165, 180], [110, 207, 208], [111, 0, 1], [111, 152, 153], [111, 165, 180], [111, 207, 208], [112, 0, 1], [112, 152, 154], [112, 164, 180], [112, 207, 208], [113, 0, 1], [113, 152, 156], [113, 162, 180], [113, 207, 208], [114, 0, 1], [114, 150, 168], [114, 207, 208], [115, 0, 208], [116, 0, 208], [117, 0, 208]], 'spawn': (800, 590), 'gate': (797, 833, 85, 52), 'gate_out': (839, 751), 'gate_over': (773, 787), 'plots': [((276, 704, 196, 84), 4, 2), ((526, 704, 86, 84), 2, 2), ((666, 704, 50, 87), 2, 2)], 'npc': {'Sir Aldric': (830, 380), 'Mira': (600, 560), 'Cale si Pedagang': (1000, 420), 'Anya': (640, 500), 'Fenn si Pemanah': (1040, 470), 'Kesatria Ines': (1000, 350), 'Madam Ruby': (930, 500), 'Penyihir Selene': (700, 450), 'Kakek Odo': (880, 636), 'Penjaga Gerbang': (840, 770), 'Putri Elara': (900, 380), 'Lars si Petani': (700, 655)}}

# benih untuk kebun desa
SHOP_SEED = [('seed_wheat', 6), ('seed_cabbage', 8), ('seed_carrot', 7)]

# pintu luar (koordinat peta) -> interior
DOORS = {
    'inn': dict(trig=(365, 348, 28, 12), out=(379, 376)),
    'church': dict(trig=(736, 352, 28, 12), out=(750, 380)),
    'green': dict(trig=(1023, 324, 28, 12), out=(1037, 352)),
    'potion': dict(trig=(1258, 324, 28, 12), out=(1272, 352)),
    'smith': dict(trig=(197, 654, 28, 12), out=(211, 682)),
    'windmill': dict(trig=(488, 664, 28, 12), out=(502, 692)),
}
# interior: hasil bangun ulang (v1.3) dari aset tembok, pintu & perabot. Semua koordinat = piksel gambar (crop nol).
# exit = pintu tembok di dinding bawah; lantai berhenti di tepi atas pintu (pintu tidak bisa diinjak).
INTERIORS = {
    'inn': dict(crop=(0, 0, 402, 390), floor=[(24, 100, 354, 210)],
                solid=[(290, 141, 77, 32), (162, 154, 52, 38), (34, 154, 55, 39), (98, 154, 50, 39), (230, 210, 38, 13), (40, 281, 88, 17), (300, 276, 65, 34), (140, 292, 69, 25), (24, 348, 69, 26), (300, 352, 40, 24)],
                exit=(164, 310, 74, 80), spawn=(201, 290), npc=('Rosalind', 'n01', 'inn', (250, 258))),
    'potion': dict(crop=(0, 0, 414, 392), floor=[(24, 100, 366, 212)],
                solid=[(120, 121, 43, 14), (24, 141, 77, 32), (290, 146, 85, 36), (340, 182, 19, 11), (230, 245, 17, 11), (30, 250, 82, 30), (262, 280, 69, 25), (364, 300, 38, 23), (170, 318, 60, 16)],
                exit=(170, 312, 74, 80), spawn=(207, 300), npc=('Penyihir Orn', 'n25', 'shop', (200, 188))),
    'smith': dict(crop=(0, 0, 400, 246), floor=[(24, 84, 352, 102)],
                solid=[(300, 53, 46, 32), (24, 62, 65, 34), (250, 119, 28, 19), (118, 128, 48, 16), (340, 141, 20, 11), (362, 141, 20, 11), (150, 171, 50, 18), (40, 172, 43, 19)],
                exit=(172, 186, 56, 60), spawn=(200, 169), npc=('Brom si Pandai Besi', 'n02', 'smith', (120, 150))),
    'green': dict(crop=(0, 0, 400, 302), floor=[(24, 100, 352, 122)],
                solid=[(262, 127, 28, 19), (300, 138, 69, 26), (24, 156, 50, 39), (124, 189, 17, 11), (224, 209, 14, 11), (24, 221, 40, 14), (150, 217, 74, 27), (340, 226, 38, 23)],
                exit=(163, 222, 74, 80), spawn=(200, 210), npc=('Nenek Wren', 'n04', 'granny', (262, 192))),
    'church': dict(crop=(0, 0, 560, 430), floor=[(24, 124, 512, 206)],
                solid=[(26, 48, 81, 22), (480, 48, 81, 22), (30, 162, 72, 19), (400, 162, 72, 19), (230, 178, 94, 40), (60, 262, 78, 30), (360, 262, 78, 30), (180, 327, 31, 23), (360, 327, 31, 23), (40, 331, 45, 27), (470, 331, 45, 27), (230, 335, 82, 30)],
                exit=(234, 330, 92, 100), spawn=(280, 318), npc=('Pendeta Elias', 'n10', 'priest', (280, 262))),
    'windmill': dict(crop=(0, 0, 420, 300), floor=[(24, 124, 372, 96)],
                solid=[(120, 140, 65, 17), (26, 145, 30, 22), (340, 145, 30, 22), (60, 207, 43, 14), (270, 199, 62, 25)],
                exit=(173, 220, 74, 80), spawn=(210, 208), npc=(GUILD_MASTER, 'n11', 'guild', (210, 176))),
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
    # v1.3 misi tambahan
    dict(id='pig', name='Hama Babi', desc='Kalahkan 4 Babi Hutan di Hutan Berburu.', kind='kill', match='Babi Hutan',
         need=4, xp=50, gold=120, item='meat'),
    dict(id='bones', name='Tulang Belulang', desc='Kumpulkan 4 Tulang (jatuhan Kerangka & Zombie).', kind='item', match='bone',
         need=4, xp=70, gold=140, item='potion_mp2'),
    dict(id='cobra', name='Pemburu Kobra', desc='Kalahkan 2 Kobra di Hutan Berburu.', kind='kill', match='Kobra',
         need=2, xp=90, gold=200, item=None),
    dict(id='vampire', name='Penumpas Vampir', desc='Kalahkan Vampir penjaga gua di Hutan Berburu.', kind='kill', match='Vampir',
         need=1, xp=300, gold=600, item='armor_silver'),
]

# posisi (koordinat peta-interior, pusat sprite) tempat NPC tidur di penginapan saat malam
SLEEP_SPOTS = [(60, 150), (122, 150), (186, 150), (120, 228), (232, 236), (330, 205)]

