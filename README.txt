ELDENVALE RPG v1.2 (Python + pygame, PC & Android)

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
