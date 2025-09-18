# Sistem Filing – Jabatan Statistik UiTM N9 (Seremban)

**Stack**: Streamlit + SQLite (persisten)  
**Direka untuk**: Pensyarah, AJK, KPP, Auditor (login) & Public/Student (tanpa login, view-only untuk fail tertentu).

## Ciri Utama
- Storan kekal di **/data** (mount disk/volume pada Render/Railway/VPS).
- **Login & peranan**: LECTURER, AJK, KPP, ADMIN, AUDITOR (read-only).
- **Public page** (tanpa login): Papar Rubrics/Course Info/CAP + jadual **LIC/RP** & **tempoh lantikan**.
- **Upload**: Dokumen umum → `/data/public/{rubrics|course_info|cap}`; dokumen lain → `/data/uploads`.
- **Subjects master** disemai dari `seed/subjects_master_with_periods_v2.xlsx`.
- **Users** disemai dari `seed/all_users_credentials.xlsx` (kata laluan akan di-hash).

## Cara Jalan (Lokal / Server)
1. Pastikan Python 3.10+.
2. `pip install -r requirements.txt`
3. (Pilihan) salin `.env.example` ke `.env`:
   ```
   DATA_DIR=/data   # tukar jika mahu
   PORT=8501
   ```
4. Cipta folder data kekal (jika tiada): `/data/public/{rubrics,course_info,cap}` dan `/data/uploads`.
5. Jalankan app login:
   ```
   streamlit run app.py --server.port ${PORT:-8501} --server.address 0.0.0.0
   ```
6. Jalankan public view (opsyen kedua):
   ```
   streamlit run public_view.py --server.port 8502 --server.address 0.0.0.0
   ```

## Deploy ke Render (ringkas)
- Tambah **Persistent Disk** dan mount ke `/data`.
- Set environment variable: `DATA_DIR=/data`.
- Start command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`

## Struktur Data
- **/data/mytimes.db** – SQLite DB
- **/data/public/** – fail public (rubrics/course_info/cap)
- **/data/uploads/** – fail lain (lesson_plan, SLT, JSU, surat lantikan, dll.)

## Tukar Kata Laluan
- Buat kini melalui CLI/DB; UI reset password boleh ditambah kemudian.
