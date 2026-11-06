ELDENVALE RPG v1.1 (Python + pygame, PC & Android)

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
