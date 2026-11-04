ELDENVALE RPG v1.1
PC     : pip install pygame ; python main.py
         WASD/Panah jalan | Z/Spasi bicara/masuk pintu | P ramuan | Esc menu & pengaturan | F1 debug (kotak pintu/zona)
HP     : joystick kiri, tombol A (bicara/masuk) & B (ramuan), tombol MENU kanan atas -> Pengaturan
APK    : push ke GitHub (branch main) -> tab Actions -> Build APK -> unduh artifact "eldenvale-apk"

Baru di v1.1
- Masuk 8 bangunan (jalan ke pintu lalu tekan atas / tombol A): penginapan, balai desa, toko, pandai besi, rumah hijau, kincir, lumbung, dermaga
- 57 monster dengan kemampuan (racun, api, serap HP, serangan dahsyat, serang ganda), monster elit, makin kuat saat malam
- Siang-malam dengan cahaya: lampu jalan, jendela, tungku, api unggun, lentera pemain, kunang-kunang, sinar matahari
- Optimasi: cache teks/panel, overlay tanpa alokasi per frame, batas FPS, auto-turunkan kualitas
- Menu Pengaturan (kualitas, cahaya, partikel, FPS, waktu, transparansi kontrol, simpan otomatis)
Koordinat pintu ada di tabel DOORS di main.py bila ingin digeser.
