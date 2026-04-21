# LABORA - Streamlit Community Cloud + Supabase

Versi ini sudah dirombak agar lebih aman untuk launch skala kecil.

## Perubahan utama
- Database Excel diganti **Supabase Postgres**.
- Upload dokumen tidak lagi disimpan ke folder lokal, tetapi ke **Supabase Storage**.
- Username/password admin dan reviewer dibaca dari **Streamlit secrets**.
- Cocok untuk di-deploy ke **Streamlit Community Cloud**.

## 1) Siapkan Supabase
Buat project baru di Supabase, lalu jalankan isi file `supabase_schema.sql` di SQL Editor.

Setelah itu, buat bucket storage bernama:

`labora-documents`

Saran paling cepat untuk sidang:
- buat bucket sebagai **public**
- gunakan file upload maksimal kecil-menengah

## 2) Masukkan data awal dari Excel lama
Jalankan script berikut di lokal:

```bash
python seed_from_excel.py "data_labora(2).xlsx" "SUPABASE_URL" "SERVICE_ROLE_KEY"
```

Script ini akan memindahkan sheet Excel ke tabel Supabase.

## 3) Buat repository GitHub
Upload file berikut ke repo GitHub:
- `app.py`
- `requirements.txt`
- `.streamlit/config.toml`
- `README_DEPLOY.md`

## 4) Deploy ke Streamlit Community Cloud
Langkah ringkas:
1. Push repo ke GitHub.
2. Buka Streamlit Community Cloud.
3. Klik **Create app**.
4. Pilih repo dan file `app.py`.
5. Tambahkan secrets di App settings > Secrets.
6. Deploy.

## 5) Isi secrets di Streamlit
Salin isi `secrets.example.toml`, lalu isi nilai asli Anda.

Contoh:

```toml
[supabase]
url = "https://YOUR_PROJECT.supabase.co"
service_role_key = "YOUR_SERVICE_ROLE_KEY"

[storage]
public_base_url = "https://YOUR_PROJECT.supabase.co/storage/v1/object/public/labora-documents"

[[auth.users]]
username = "admin"
password = "password_admin_kuat"
role = "Admin"

[[auth.users]]
username = "reviewer"
password = "password_reviewer_kuat"
role = "Reviewer"
```

## 6) Catatan keamanan
- Jangan commit service role key ke GitHub.
- Jangan taruh password login di `app.py`.
- Untuk sidang, gunakan akun demo terpisah dari akun operasional nyata.
- Batasi uploader ke admin saja.

## 7) Catatan upload file
Pada aplikasi ini:
- kategori dokumen otomatis jadi folder di bucket storage
- path file disimpan ke kolom `file_ref`
- reviewer bisa membuka file dari URL publik bucket

## 8) Uji sebelum sidang
- login admin berhasil
- login reviewer berhasil
- dashboard tampil
- tambah 1 logbook berhasil
- tambah 1 evaluasi berhasil
- tambah 1 dokumen dan upload file berhasil
- reviewer bisa buka dokumen dari hasil pencarian
