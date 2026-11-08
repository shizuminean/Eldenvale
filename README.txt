PERUBAHAN v1.7.0  (BATTLE REAL-TIME ala MOBA, tanpa popup / layar battle)
  - Layar battle giliran lama DIHAPUS. Monster tidak lagi membuka popup: semua pertarungan terjadi langsung di peta Hutan Berburu,
    secara real-time. Logika baru ada di combat.py (main.py hanya memanggilnya).
  - KONTROL (Android): joystick kiri untuk gerak. Kanan bawah: tombol SERANG besar (tahan = serang beruntun, kombo 3 pukulan,
    pukulan ke-3 lebih kuat + dorong) dikelilingi 4 SKILL + tombol Ramuan.
      Skill 1  Tebasan Merah   Lv 1   5 MP   cd 2,5 d   tebasan 150 derajat, damage 2x
      Skill 2  Terjang Badai   Lv 2   8 MP   cd 5 d     melesat 215 px menembus musuh, kebal sesaat
      Skill 3  Gempa Bumi      Lv 4   14 MP  cd 9 d     hantam area, damage 2,3x + STUN 1,3 d
      Skill 4  Badai Pedang    Lv 6   24 MP  cd 24 d    ULTIMATE: berputar 2,4 d, menyayat semua musuh sekitar, damage diterima -50%
    Tap skill = bidik otomatis ke musuh terdekat. TAHAN & GESER dari tombol skill = bidik manual (pratinjau area muncul), lepas = cast.
    Tombol Ramuan: pulihkan HP (atau MP bila HP penuh). Serangan yang kena memulihkan MP; MP juga pulih pelan sendiri di hutan.
  - KEYBOARD (PC): WASD/Panah gerak, J / Spasi / Z serang, 1 2 3 4 skill, P ramuan.
  - MUSUH: tiap monster punya pola. Sebelum menyerang muncul TELEGRAF (area merah yang mengisi + sprite berkedip merah), jadi bisa dihindari:
      melee (tebasan kerucut)  | charge: serigala/babi/kobra/kelelawar (terjang lurus)  | ranged: pemanah, penyihir, hantu, naga, golem kristal (proyektil)
      slam: golem lumut/treant/zombie/ghoul (hantam area)  | Raja Slime: hantam + lompat ke posisimu  | Vampir: tembakan 3 arah, terjang, gigit
    Musuh yang terkena bisa terdorong / ter-stun (boss hanya sedikit). Musuh yang dikejar terlalu jauh dari sarangnya akan pulang & memulihkan HP.
  - TAMPILAN: bar HP musuh & pemain di atas kepala, angka damage (kritis 12%), ring target di musuh terdekat, efek tebasan/ring/proyektil,
    getar layar (Setelan > Getar layar), bar HP boss di atas layar, tombol skill menampilkan cooldown + biaya MP + kunci level.
  - Kalah: emas -50%, bangun di alun-alun (seperti sebelumnya). Menang: XP, emas, drop, dan progres misi tetap berlaku.
  - Dihapus: encounter acak, layar battle, menu Serang/Tebasan/Item/Kabur.

PERUBAHAN v1.6.0  (pilih karakter pemain + rapikan lampu desa)
  - LAMPU: lampu jalan tidak lagi berdiri di atas tangga & jembatan. village.py punya daftar NOGO (3 zona: 2 tangga barat, jembatan timur);
    lampu & bendera yang menyentuh zona itu dilewati. LAMPS_A diganti: 12 titik di tepi jalan, di sisi luar tangga/jembatan.
  - Game Baru kini membuka layar PILIH KARAKTER: 4 tokoh (Hana, Selene, Kaelen, Ronan) dengan animasi jalan pada kartu yang dipilih.
    Kontrol: ketuk kartu lalu Mulai (Android) / panah + Enter (PC). Kembali / Esc = ke menu utama.
  - Sprite baru ada di assets/chars/cN_{down,side,up}_0..3.png (jalan 4 frame), cN_idle_*, cN_battle_idle/atk.
    Dipakai di dunia, interior, battle, potret HUD, dan potret tas.
  - Pilihan karakter disimpan di save (kunci 'char'); save lama otomatis memakai karakter 0 (Hana).

PERBAIKAN v1.5.1  (desa rapi, bayangan sesuai bentuk aset, tidak lag, respawn tidak nyangkut)
  - TATA LETAK DESA: rumah/pohon/semak/batu/bunga tidak lagi ditempel di koordinat acak. village.py kini membaca jenis tanah
    dari gambar latar + mask (rumput kosong / jalan tanah / batu & tangga / tebing & air) lewat kelas Terrain, lalu
    mencarikan titik rumput kosong terdekat untuk tiap rumah (fit): tidak menimpa jalan tanah, tangga, tebing, air, atau
    bangunan lain, dan area depan pintu selalu bisa dilewati. Lampu & bendera yang menabrak bangunan otomatis dilewati.
    Pohon: 70 -> 34 (jarak 170 px, jauh dari jalan/tebing), semak/batu 70 -> 40, bunga berkelompok bukan taburan acak.
    Kotak tabrakan rumah kini hanya sebatas badan bawah (bukan 70% tinggi sprite).
  - BAYANGAN: bukan elips generik lagi. cast_shadow() membuat bayangan dari SILUET sprite itu sendiri (dibalik, dipipihkan,
    dimiringkan), jadi kincir angin punya bayangan berbilah, pohon berbayangan tajuk, dst. Interior memakai cara yang sama.
  - LAG: pencahayaan malam/senja tidak lagi memakai overlay alpha layar penuh + puluhan blit RGBA_SUB/RGB_ADD besar tiap
    frame. Sekarang lightmap setengah resolusi -> diperbesar -> BLEND_RGB_MULT (siang: nol kerja; senja tanpa lampu: 1 fill).
    Vinyet digambar sebagai 4 strip tepi, bukan satu blit RGBA layar penuh. Ada penghemat otomatis: bila rata-rata frame
    di desa lambat >3 detik, efek diturunkan bertahap (tanpa efek/lampu, lalu tanpa pencahayaan) tanpa mengubah setelan.
  - RESPAWN NYANGKUT: setelah kalah, pemain dikirim ke (880, 560) -- koordinat desa lama. Di desa 2x itu titik tersebut
    ada DI DALAM kotak tabrakan penginapan: pemain tertutup sprite rumah dan semua langkah ditolak. Kini respawn memakai
    safe_spot() (titik bebas terdekat dari alun-alun), area diset ke desa lebih dulu, interior/dialog/menu dibersihkan.
    enter_area(), muat save, dan recover() juga memvalidasi posisi. Posisi NPC divalidasi agar tidak di dalam objek.
  - INTERIOR: furnitur otomatis dijaga tetap di dalam lantai; tumpang tindih (tong/meja di penginapan, lentera/meja di toko
    ramuan, peti di luar lantai, tanaman di dinding bawah) dirapikan.

ELDENVALE RPG v1.5 (Python + pygame, PC & Android)

YANG BARU DI v1.5  (desa & rumah dibangun ulang, sistem pertanian)
  - Desa lama (map.png) dan SEMUA interior lama (assets/int/*.png) dihapus. Desa baru dibangun lewat KODE
    (village.py) di atas LATAR assets/town_bg.png (plaza silang, tebing, sungai, air terjun, kolam).
    Gambar diskalakan 2x; tebing & air menjadi tabrakan lewat assets/town_mask.png. Bangunan, ladang,
    lampu, pohon, semak, batu, dan bunga ditata lewat kode di teras-teras yang terjangkau.
  - Rumah, pohon, dan tanaman diurutkan menurut Y: karakter bisa berjalan DI BELAKANG pohon & atap.
  - Interior baru untuk 6 bangunan (Penginapan, Gereja, Toko Ramuan, Pandai Besi, Rumah Nenek Wren,
    Guild di kincir angin): lantai papan/batu, dinding kayu, perabot, karpet, jendela, banner.
  - Tampilan: kilau air, asap cerobong, kupu-kupu (siang) & kunang-kunang (malam), cahaya lampu dan
    jendela saat malam, nuansa senja/fajar, vinyet, bayangan di bawah objek.
  - SISTEM PERTANIAN (96 petak di ladang barat daya, pagar kayu):
      Berdiri menghadap petak, tekan Z / Spasi / tombol A:
      1) tanah kosong -> dicangkul   2) tanah dicangkul -> pilih benih lalu tanam
      3) tanaman -> disiram (tanaman hanya tumbuh pada hari ia disiram, atau saat hujan 22%)
      4) tanaman matang -> panen (1-3 hasil + sedikit XP)
    8 tanaman: Gandum, Lobak, Wortel, Kubis, Kentang, Tomat, Terong, Ubi Manis (2-4 hari tumbuh).
    Petani Tomo (kios dekat ladang) menjual benih dan membeli hasil panen. Hasil panen juga bisa dimakan.
    Tidur di penginapan (kini bisa juga siang hari) melompat ke pagi dan menumbuhkan tanaman.
    Data ladang ikut tersimpan di save.

LAMPU, BENDERA, MALAM, TIDUR
  - Semua lampu jalan diganti sprite lampu baru (di posisi yang sama): lampu hitam ornamen di tepi jalan & ladang,
    lampu berspanduk merah di keempat sudut plaza. Ditambah 8 bendera tiang (sisi gereja, mulut plaza, jembatan).
  - Nuansa hari baru (village.py: AMB/ambient): fajar merah muda, siang terang, sore keemasan -> jingga -> ungu,
    malam biru. Saat gelap, lampu & jendela 'melubangi' kegelapan dengan cahaya hangat, dan pemain membawa cahaya kecil.
    (Dengan Efek visual mati, hanya selimut warna sederhana.)
  - Patah-patah: asap & kunang-kunang sebelumnya membuat ribuan Surface baru tiap frame; kini dikuantisasi (maks 8-39 di cache).
  - TIDUR DI KASUR: dekati kasur di dalam rumah (Rumah Nenek Wren = gratis, kamar lantai 2 penginapan = 10 G),
    tekan Z / tombol A, pilih "Tidur sampai pagi": layar memudar, HP/MP pulih, waktu ke 06:00 dan tanaman tumbuh.

RUMAH BARU
  - Rumah Pandai Besi kini memakai sprite rumah atap merah (isi & fungsi tetap).
  - Ditambah 2 rumah hiasan (tanpa interior): rumah bergaya Jepang di teras barat laut atas dan lumbung merah
    di teras barat daya dekat sumur.

LADANG & RUMPUT
  - Ladang memakai sprite ladang dari aset gambar (assets/spr/field_big.png). Status cangkul/siram digambar
    sebagai lapisan tanah gelap semi-transparan di atasnya.
  - Rumput liar 3 jenis (kecil, sedang, tinggi) tersebar di desa.

PERBAIKAN (lag & interior)
  - Lag: tabrakan desa kini memakai hash spasial (bukan 177 kotak tiap cek), kilau air per-bucket, NPC jauh
    tidak diperbarui. Efek visual bisa dimatikan: Setelan > "Efek visual" (preset Sedang/Rendah mematikannya).
  - Perabot interior kini digambar menurut sumbu-Y bersama pemain/NPC: pemain berdiri di belakang meja,
    kasur, rak, dll. dan tertutup perabot, tidak lagi 'menginjak' perabot.
  - Penginapan sekarang 2 lantai: lobi/kedai di lantai 1, tangga di kanan menuju kamar tidur lantai 2.
    Kasur diperkecil. Penduduk tidur di kamar lantai 2 saat malam.

DATA & KODE
  village.py : desa, interior, logika ladang (CROPS ada di data.py)
  assets/spr : sprite hasil potong dari sheet bangunan/tanaman/furnitur
  Save lama tetap bisa dimuat (posisi di dalam bangunan baru otomatis dipindah ke alun-alun).

YANG BARU DI v1.2
  - Desa: tidak ada lagi monster & battle mendadak di rumput. Monster hanya di Hutan Berburu.
  - Hutan Berburu: monster kini mengejar lewat jalur (BFS) sehingga tidak macet di tikungan/tembok.
    Boss Raja Slime dipindah ke padang hijau hutan.
  - Kincir angin = Guild Petualang (masuk lewat pintunya di kaki kincir). Ketua guild Maren
    memberi 4 misi dari papan misi: Berburu Serigala, Basmi Goblin, Pecahan Kristal, Pemburu Raja.
    Progres misi tampil di panel MISI.
  - Sistem malam: 1 hari game ~ 36 detik nyata (1 menit game = 1,5 detik). Malam mulai 21.00.
    Penduduk pulang & tidur di penginapan (terlihat saat masuk penginapan di malam hari).
    Di penginapan pilih "Tidur sampai pagi" (10 G) untuk melompat ke pagi dan memulihkan HP/MP.
    Guild tutup di malam hari.
  - Collision: kursi taman, pagar ladang & kampung, pohon, plang tukang besi, batu, dan tiang gerbang
    kini menghalangi jalan. Kincir angin tidak lagi terkunci dan bisa dimasuki.
  - Misi Sir Aldric (5 slime) sekarang dilakukan di Hutan Berburu.


JALANKAN DI PC
  pip install pygame
  python main.py
  Kontrol: WASD/Panah jalan, Z/Spasi bicara, I tas, P ramuan, F5 simpan, F9 muat.

BUILD APK
  Upload folder ini ke GitHub, tab Actions -> Build APK (workflow sudah ada).

YANG DIPERBAIKI DI v1.1
  - Game tidak lagi keluar sendiri: font dibundel (assets/fonts), layar dibuat dengan cadangan,
    aset gagal-muat diganti penanda (tidak crash), dan error apa pun ditangkap lalu ditampilkan
    di layar dengan tombol Lanjutkan. Detail tercatat di crash.log.
  - Layar muat + layar judul tampil langsung, jadi tidak ada layar hitam.
  - Tombol Back Android tidak menutup game. Progres disimpan otomatis saat ke background/keluar.
  - Layout mengikuti rasio layar (HP 16:9, 20:9, tablet 4:3, PC) tanpa terpotong.
  - UI baru: HUD, dialog, toko (bisa digulir), tas, setelan, battle, kontrol sentuh melayang.

CATATAN
  - Font Poppins (lisensi OFL). Tanpa emoji; semua ikon digambar vektor.
