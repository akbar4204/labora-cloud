from __future__ import annotations

import mimetypes
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

import pandas as pd
import streamlit as st
from supabase import Client, create_client

APP_NAME = "LABORA"
APP_TAGLINE = "Sistem manajemen perangkat pembelajaran laboratorium"
STORAGE_BUCKET = "labora-documents"
MAX_UPLOAD_MB = 25
ALLOWED_DOC_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".jpg", ".jpeg", ".png", ".txt"
}

TABLES: Dict[str, List[str]] = {
    "dokumen_inti": [
        "id_dokumen", "kategori", "kode", "judul_dokumen", "versi", "status",
        "penanggung_jawab", "unit", "tanggal_update", "prioritas", "file_ref", "deskripsi",
    ],
    "inventaris_kebutuhan": [
        "id_kebutuhan", "kelompok_dokumen", "nama_dokumen", "ketersediaan", "tingkat_kebutuhan",
        "gap", "prioritas_tindak_lanjut", "target_selesai", "pic", "catatan_gap_analysis",
    ],
    "sop": [
        "id_sop", "kode_sop", "judul_sop", "tujuan", "ruang_lingkup", "ringkasan_langkah",
        "status", "versi", "pic", "review_berikutnya",
    ],
    "modul_k3": [
        "id_modul", "judul_modul", "materi_pokok", "sasaran", "durasi_menit", "metode",
        "status", "penanggung_jawab", "catatan",
    ],
    "instruksi_kerja": [
        "id_ik", "kode_ik", "judul_instruksi", "langkah_utama", "alat_terkait", "apd_wajib",
        "status", "pic", "catatan",
    ],
    "logbook": [
        "id", "tanggal", "laboratorium", "kegiatan", "petugas", "status_kegiatan",
        "temuan_kendala", "tindak_lanjut", "verifikator", "created_at",
    ],
    "evaluasi": [
        "id_evaluasi", "tanggal", "unit", "aspek", "skor", "kategori", "rekomendasi", "reviewer",
    ],
    "panduan": ["id", "bagian", "isi", "urutan"],
}

TABLE_HEADER_MAP = {
    "id_dokumen": "ID Dokumen",
    "kategori": "Kategori",
    "kode": "Kode",
    "judul_dokumen": "Judul Dokumen",
    "versi": "Versi",
    "status": "Status",
    "penanggung_jawab": "Penanggung Jawab",
    "unit": "Unit",
    "tanggal_update": "Tanggal Update",
    "prioritas": "Prioritas",
    "file_ref": "Referensi File",
    "deskripsi": "Deskripsi",
    "id_kebutuhan": "ID Kebutuhan",
    "kelompok_dokumen": "Kelompok Dokumen",
    "nama_dokumen": "Nama Dokumen",
    "ketersediaan": "Ketersediaan",
    "tingkat_kebutuhan": "Tingkat Kebutuhan",
    "gap": "Gap",
    "prioritas_tindak_lanjut": "Prioritas Tindak Lanjut",
    "target_selesai": "Target Selesai",
    "pic": "PIC",
    "catatan_gap_analysis": "Catatan Gap Analysis",
    "id_sop": "ID SOP",
    "kode_sop": "Kode SOP",
    "judul_sop": "Judul SOP",
    "tujuan": "Tujuan",
    "ruang_lingkup": "Ruang Lingkup",
    "ringkasan_langkah": "Ringkasan Langkah",
    "review_berikutnya": "Review Berikutnya",
    "id_modul": "ID Modul",
    "judul_modul": "Judul Modul",
    "materi_pokok": "Materi Pokok",
    "sasaran": "Sasaran",
    "durasi_menit": "Durasi (menit)",
    "metode": "Metode",
    "catatan": "Catatan",
    "id_ik": "ID IK",
    "kode_ik": "Kode IK",
    "judul_instruksi": "Judul Instruksi",
    "langkah_utama": "Langkah Utama",
    "alat_terkait": "Alat Terkait",
    "apd_wajib": "APD Wajib",
    "tanggal": "Tanggal",
    "laboratorium": "Laboratorium",
    "kegiatan": "Kegiatan",
    "petugas": "Petugas",
    "status_kegiatan": "Status Kegiatan",
    "temuan_kendala": "Temuan / Kendala",
    "tindak_lanjut": "Tindak Lanjut",
    "verifikator": "Verifikator",
    "id_evaluasi": "ID Evaluasi",
    "aspek": "Aspek",
    "skor": "Skor",
    "rekomendasi": "Rekomendasi",
    "reviewer": "Reviewer",
    "bagian": "Bagian",
    "isi": "Isi",
    "urutan": "Urutan",
    "created_at": "Dibuat Pada",
}


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --line:#e6edf5;
            --text:#13233a;
            --muted:#617289;
            --blue:#0d2b52;
            --teal:#138a9f;
            --soft:#f5f8fc;
            --warn:#fff4df;
            --danger:#ffe6e8;
            --ok:#e6fbf5;
        }

        .stApp {
            background: linear-gradient(180deg, #f3f7fb 0%, #fbfdff 100%);
        }

        .block-container {
            max-width: 1280px;
            padding-top: 0.8rem;
            padding-bottom: 2rem;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0b2342 0%, #123763 50%, #173f73 100%);
            border-right: 1px solid rgba(255,255,255,.08);
        }

        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stMarkdown,
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] h4,
        [data-testid="stSidebar"] h5,
        [data-testid="stSidebar"] h6,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] div:not(button):not(button *) {
            color: #ffffff !important;
        }

        .sidebar-card {
            background: linear-gradient(135deg, rgba(255,255,255,.12), rgba(255,255,255,.04));
            border: 1px solid rgba(255,255,255,.10);
            border-radius: 20px;
            padding: 1rem;
            margin-bottom: .9rem;
            box-shadow: 0 14px 30px rgba(0,0,0,.12);
        }

        .sidebar-brand {
            font-size: 1.55rem;
            font-weight: 800;
            margin-bottom: .2rem;
            color: #ffffff !important;
        }

        .sidebar-sub {
            font-size: .94rem;
            color: rgba(255,255,255,.82) !important;
            line-height: 1.5;
        }

        .sidebar-role {
            display:inline-block;
            margin-top:.35rem;
            padding:.36rem .72rem;
            border-radius:999px;
            background: rgba(30, 220, 200, .14);
            border: 1px solid rgba(130,255,239,.18);
            font-weight:700;
            color:#ffffff !important;
        }

        .hero {
            background: linear-gradient(135deg, #0d2b52 0%, #1d5f93 58%, #1d9a95 100%);
            border-radius: 28px;
            padding: 1.4rem 1.4rem 1.2rem 1.4rem;
            color: #fff;
            box-shadow: 0 20px 35px rgba(13,43,82,.18);
            margin-bottom: 1rem;
        }

        .hero h1 {
            color: #ffffff !important;
            margin: 0 0 .45rem 0;
            font-size: 2.15rem;
            line-height: 1.1;
        }

        .hero p {
            margin: 0;
            color: rgba(255,255,255,.92);
            line-height: 1.65;
            font-size: 1rem;
        }

        .chip-wrap {
            display:flex;
            flex-wrap:wrap;
            gap:.55rem;
            margin-top:1rem;
        }

        .chip {
            border-radius: 999px;
            padding: .45rem .78rem;
            background: rgba(255,255,255,.12);
            border: 1px solid rgba(255,255,255,.15);
            font-weight:700;
            font-size:.86rem;
            color:#ffffff !important;
        }

        .metric-box {
            background:#fff;
            border:1px solid var(--line);
            border-radius: 22px;
            padding: 1rem 1rem .9rem;
            box-shadow: 0 10px 22px rgba(15,23,42,.05);
            margin-bottom: .9rem;
            min-height: 118px;
        }

        .metric-label {
            font-size:.9rem;
            color: var(--muted);
        }

        .metric-value {
            font-size: 2rem;
            font-weight: 800;
            color: var(--text);
            line-height: 1.15;
        }

        .section-box {
            background: linear-gradient(180deg, #ffffff 0%, #fcfdff 100%);
            border:1px solid var(--line);
            border-radius: 22px;
            padding: 1rem 1rem .9rem;
            box-shadow: 0 12px 24px rgba(15,23,42,.05);
            margin-bottom: .95rem;
        }

        .section-title {
            font-size: 1rem;
            font-weight: 800;
            color: var(--text);
            margin-bottom: .7rem;
        }

        .action-card {
            background:#fff;
            border:1px solid var(--line);
            border-radius:20px;
            padding:1rem;
            box-shadow: 0 10px 22px rgba(15,23,42,.05);
            min-height: 140px;
        }

        .action-card h4 {
            margin:0 0 .35rem 0;
            color: var(--text);
        }

        .action-card p {
            margin:0;
            color: var(--muted);
            line-height:1.55;
        }

        .callout {
            padding:.95rem 1rem;
            border-radius:18px;
            border:1px solid var(--line);
            margin-bottom:.7rem;
            line-height:1.55;
        }

        .callout.warn {background: var(--warn);}
        .callout.danger {background: var(--danger);}
        .callout.ok {background: var(--ok);}

        .small-muted {
            font-size:.84rem;
            color: rgba(255,255,255,.76) !important;
            margin-top:.35rem;
        }

        [data-testid="stDataFrame"] {
            border-radius: 16px !important;
            overflow: hidden !important;
            border: 1px solid var(--line) !important;
            box-shadow: 0 10px 22px rgba(15,23,42,.05) !important;
        }

        [data-testid="stSidebar"] .stButton > button {
            width:100% !important;
            border-radius:14px !important;
            border:1px solid rgba(0,0,0,.10) !important;
            background: linear-gradient(180deg, #ffffff 0%, #edf2f8 100%) !important;
            color:#13233a !important;
            font-weight:800 !important;
            box-shadow: 0 10px 18px rgba(0,0,0,.12) !important;
            min-height: 44px;
        }

        [data-testid="stSidebar"] .stButton > button * {
            color:#13233a !important;
            fill:#13233a !important;
            font-weight:800 !important;
        }

        [data-testid="stSidebar"] .stButton > button:hover {
            background: linear-gradient(180deg, #ffffff 0%, #e7eef7 100%) !important;
            border:1px solid rgba(0,0,0,.16) !important;
        }

        [data-testid="stSidebar"] div[role="radiogroup"] > label {
            background: rgba(255,255,255,.05);
            border:1px solid rgba(255,255,255,.08);
            border-radius: 14px;
            padding: .55rem .7rem;
            margin-bottom: .3rem;
            transition: all .18s ease;
        }

        [data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
            background: rgba(255,255,255,.12);
            transform: translateX(2px);
        }

        .stTextInput input,
        .stTextArea textarea,
        .stDateInput input,
        .stNumberInput input,
        .stSelectbox div[data-baseweb="select"] > div,
        .stMultiSelect div[data-baseweb="select"] > div {
            border-radius: 14px !important;
        }

        @media (max-width: 768px) {
            .block-container {
                padding-top: 0.5rem;
                padding-bottom: 1.25rem;
            }

            .hero {
                border-radius: 22px;
                padding: 1.1rem 1rem 1rem 1rem;
                margin-bottom: .85rem;
            }

            .hero h1 {
                font-size: 1.85rem !important;
            }

            .hero p {
                font-size: .96rem !important;
                line-height: 1.6 !important;
            }

            .chip-wrap {
                gap: .45rem;
            }

            .chip {
                font-size: .8rem;
                padding: .4rem .68rem;
            }

            .metric-box {
                border-radius: 18px;
                padding: .9rem .9rem .8rem;
                min-height: 100px;
            }

            .metric-value {
                font-size: 1.7rem;
            }

            .section-box {
                border-radius: 18px;
                padding: .9rem .9rem .8rem;
            }

            .section-title {
                font-size: .96rem;
            }

            .action-card {
                border-radius: 18px;
                padding: .9rem;
                min-height: auto;
            }

            .sidebar-card {
                border-radius: 18px;
                padding: .9rem;
            }

            [data-testid="stSidebar"] .stButton > button {
                min-height: 42px;
                font-size: .95rem !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def safe_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0)


def parse_date_column(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce")


def prettify_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns={c: TABLE_HEADER_MAP.get(c, str(c).replace("_", " ").title()) for c in df.columns})


def render_table(df: pd.DataFrame, height: Optional[int] = None) -> None:
    frame = prettify_columns(df.copy())
    st.dataframe(frame, hide_index=True, use_container_width=True, height=height)


def render_metric(label: str, value: str | int | float) -> None:
    st.markdown(
        f'<div class="metric-box"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>',
        unsafe_allow_html=True,
    )


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value).strip()).lower()


def sanitize_filename(name: str) -> str:
    name = Path(name).name
    stem = Path(name).stem
    suffix = Path(name).suffix.lower()
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._-")
    stem = stem[:80] if stem else "file"
    return f"{stem}{suffix}"


def guess_mime_type(file_name: str) -> str:
    guessed, _ = mimetypes.guess_type(file_name)
    return guessed or "application/octet-stream"


def next_id(prefix: str, existing: pd.Series) -> str:
    values = existing.astype(str).tolist()
    nums: List[int] = []
    for item in values:
        if item.startswith(prefix):
            digits = "".join(ch for ch in item if ch.isdigit())
            if digits:
                nums.append(int(digits))
    return f"{prefix}-{(max(nums) + 1 if nums else 1):03d}"


def go_to(menu_name: str) -> None:
    st.session_state["menu_selection"] = menu_name


@st.cache_resource(show_spinner=False)
def get_supabase() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["service_role_key"]
    return create_client(url, key)


def auth_users() -> List[Dict[str, str]]:
    users = st.secrets.get("auth", {}).get("users", [])
    parsed: List[Dict[str, str]] = []
    for item in users:
        username = str(item.get("username", "")).strip().lower()
        password = str(item.get("password", "")).strip()
        role = str(item.get("role", "Reviewer")).strip() or "Reviewer"
        if username and password:
            parsed.append({"username": username, "password": password, "role": role})
    return parsed


def storage_public_base() -> Optional[str]:
    try:
        custom = st.secrets.get("storage", {}).get("public_base_url", "")
        if custom:
            return str(custom).rstrip("/")
        supabase_url = st.secrets["supabase"]["url"].rstrip("/")
        return f"{supabase_url}/storage/v1/object/public/{STORAGE_BUCKET}"
    except Exception:
        return None


def build_public_url(file_ref: str) -> Optional[str]:
    if not file_ref:
        return None
    base = storage_public_base()
    if not base:
        return None
    clean_path = file_ref.lstrip("/")
    return f"{base}/{clean_path}"


def show_setup_error(exc: Exception) -> None:
    st.error("Aplikasi belum siap dipakai karena konfigurasi Streamlit secrets atau Supabase belum lengkap.")
    st.code(str(exc))
    st.markdown(
        "Tambahkan secrets Supabase dan auth ke **App settings > Secrets** di Streamlit Community Cloud. "
        "Lihat file `secrets.example.toml` dan `README_DEPLOY.md`."
    )


class Database:
    def __init__(self, client: Client):
        self.client = client

    def fetch_table(self, table: str, order_by: Optional[str] = None) -> pd.DataFrame:
        query = self.client.table(table).select("*")
        if order_by:
            query = query.order(order_by)
        response = query.execute()
        rows = response.data or []
        return pd.DataFrame(rows)

    def insert_row(self, table: str, row: Dict[str, Any]) -> None:
        self.client.table(table).insert(row).execute()

    def update_row_by_id(self, table: str, id_column: str, id_value: str, updates: Dict[str, Any]) -> None:
        self.client.table(table).update(updates).eq(id_column, id_value).execute()

    def delete_storage_file(self, file_ref: str) -> None:
        clean_path = str(file_ref).strip().lstrip("/")
        if not clean_path:
            return
        self.client.storage.from_(STORAGE_BUCKET).remove([clean_path])

    def upload_document(self, uploaded_file, kategori: str, kode: str) -> str:
        suffix = Path(uploaded_file.name).suffix.lower()
        if suffix not in ALLOWED_DOC_EXTENSIONS:
            raise ValueError(f"Format file {suffix} belum diizinkan.")

        size_mb = uploaded_file.size / (1024 * 1024)
        if size_mb > MAX_UPLOAD_MB:
            raise ValueError(f"Ukuran file melebihi {MAX_UPLOAD_MB} MB.")

        category_slug = re.sub(r"[^a-z0-9]+", "-", kategori.lower()).strip("-") or "dokumen"
        code_slug = re.sub(r"[^A-Za-z0-9_-]+", "_", kode.strip())[:40] or "file"
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_name = sanitize_filename(uploaded_file.name)
        object_path = f"{category_slug}/{code_slug}_{timestamp}_{uuid4().hex[:8]}_{safe_name}"
        file_bytes = uploaded_file.getvalue()

        self.client.storage.from_(STORAGE_BUCKET).upload(
            path=object_path,
            file=file_bytes,
            file_options={
                "content-type": guess_mime_type(uploaded_file.name),
                "upsert": "false",
            },
        )
        return object_path


def load_data(db: Database) -> Dict[str, pd.DataFrame]:
    data: Dict[str, pd.DataFrame] = {}
    order_map = {
        "dokumen_inti": "tanggal_update",
        "inventaris_kebutuhan": "target_selesai",
        "sop": "kode_sop",
        "modul_k3": "judul_modul",
        "instruksi_kerja": "kode_ik",
        "logbook": "tanggal",
        "evaluasi": "tanggal",
        "panduan": "urutan",
    }

    for table, columns in TABLES.items():
        df = db.fetch_table(table, order_by=order_map.get(table))
        if df.empty:
            data[table] = pd.DataFrame(columns=columns)
            continue
        for col in columns:
            if col not in df.columns:
                df[col] = ""
        data[table] = df[columns].fillna("")

    return data


def login_form() -> None:
    st.markdown(
        f"""
        <div class="hero" style="margin-top:.3rem;">
            <div style="font-size:.9rem; opacity:.92; margin-bottom:.35rem;">
                Pilot Dashboard Manajemen Laboratorium Pembelajaran
            </div>
            <h1>{APP_NAME}</h1>
            <p>{APP_TAGLINE}. Masuk sebagai admin atau reviewer untuk mengakses modul LABORA dengan alur kerja yang lebih sederhana.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Login Aplikasi")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Masuk", type="primary", use_container_width=True):
        user = next((u for u in auth_users() if u["username"] == username.strip().lower()), None)
        if user and password == user["password"]:
            st.session_state["logged_in"] = True
            st.session_state["username"] = username.strip().lower()
            st.session_state["role"] = user["role"]
            st.session_state["menu_selection"] = "Beranda & Prioritas"
            st.session_state["show_welcome"] = True
            st.rerun()
        st.error("Username atau password tidak sesuai.")

    st.caption("Kredensial dibaca dari Streamlit secrets, bukan dari kode sumber.")


def sidebar_identity() -> str:
    role = st.session_state.get("role", "-")
    options = [
        "Beranda & Prioritas",
        "Cari & Buka Dokumen",
        "Cek Gap & Tindak Lanjut",
        "Input Harian",
        "Evaluasi & Insight",
        "Pusat Dokumen",
        "Kelola File",
        "Panduan",
    ]
    if role == "Admin":
        options.append("Panel Admin")

    current = st.session_state.get("menu_selection", options[0])
    if current not in options:
        current = options[0]

    st.sidebar.markdown(
        f"""
        <div class="sidebar-card">
            <div class="sidebar-brand">LABORA</div>
            <div class="sidebar-sub">Sistem manajemen perangkat pembelajaran laboratorium</div>
        </div>
        <div class="sidebar-card">
            <div class="sidebar-sub">Login sebagai:</div>
            <div class="sidebar-role">{role}</div>
            <div class="sidebar-sub" style="margin-top:.55rem;">User: <b>{st.session_state.get("username", "-")}</b></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    menu = st.sidebar.radio("Area Kerja", options, index=options.index(current), key="menu_radio")
    st.session_state["menu_selection"] = menu

    st.sidebar.markdown("### Aksi Cepat")
    if st.sidebar.button("🔎 Cari dokumen", use_container_width=True):
        go_to("Cari & Buka Dokumen")
        st.rerun()
    if st.sidebar.button("📌 Lihat gap prioritas", use_container_width=True):
        go_to("Cek Gap & Tindak Lanjut")
        st.rerun()
    if role == "Admin" and st.sidebar.button("📝 Tambah data harian", use_container_width=True):
        go_to("Input Harian")
        st.rerun()
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    st.sidebar.markdown('<div class="small-muted">Keluar dari sesi aktif aplikasi</div>', unsafe_allow_html=True)
    return menu


def render_welcome_strip() -> None:
    if st.session_state.get("show_welcome"):
        role = st.session_state.get("role", "Pengguna")
        st.success(
            f"Selamat datang. Anda masuk sebagai {role}. Mulai dari Beranda & Prioritas untuk melihat pekerjaan terpenting hari ini."
        )
        if st.button("Tutup panduan singkat"):
            st.session_state["show_welcome"] = False
            st.rerun()


def render_dashboard(data: Dict[str, pd.DataFrame]) -> None:
    dokumen_df = data["dokumen_inti"].copy()
    inventaris_df = data["inventaris_kebutuhan"].copy()
    evaluasi_df = data["evaluasi"].copy()
    logbook_df = data["logbook"].copy()

    total_docs = len(dokumen_df)
    final_docs = int((dokumen_df["status"].astype(str).str.lower() == "final").sum()) if not dokumen_df.empty else 0
    draft_docs = int((dokumen_df["status"].astype(str).str.lower() == "draft").sum()) if not dokumen_df.empty else 0
    gap_docs = int(safe_numeric(inventaris_df.get("gap", pd.Series(dtype=float))).sum()) if not inventaris_df.empty else 0
    avg_eval = float(safe_numeric(evaluasi_df.get("skor", pd.Series(dtype=float))).mean()) if not evaluasi_df.empty else 0.0

    if not dokumen_df.empty:
        dokumen_df["tanggal_update_parsed"] = parse_date_column(dokumen_df["tanggal_update"])
        high_priority_drafts = dokumen_df[
            dokumen_df["prioritas"].astype(str).str.lower().eq("tinggi") &
            dokumen_df["status"].astype(str).str.lower().ne("final")
        ].sort_values("tanggal_update_parsed", ascending=False)
    else:
        high_priority_drafts = dokumen_df

    if not inventaris_df.empty:
        inventaris_df["target_selesai_parsed"] = parse_date_column(inventaris_df["target_selesai"])
        urgent_gaps = inventaris_df[safe_numeric(inventaris_df["gap"]) > 0].sort_values("target_selesai_parsed").head(6)
    else:
        urgent_gaps = inventaris_df

    low_eval = evaluasi_df.copy()
    if not low_eval.empty:
        low_eval["skor_num"] = safe_numeric(low_eval["skor"])
        low_eval = low_eval.sort_values("skor_num", ascending=True).head(5)

    chips = "".join([
        f'<div class="chip">{total_docs} dokumen inti</div>',
        f'<div class="chip">{final_docs} dokumen final</div>',
        f'<div class="chip">{draft_docs} dokumen draft</div>',
        f'<div class="chip">{gap_docs} gap aktif</div>',
        f'<div class="chip">Skor evaluasi {avg_eval:.1f}</div>',
    ])

    st.markdown(
        f"""
        <div class="hero">
            <div style="font-size:.86rem; opacity:.92; margin-bottom:.35rem;">Pilot Dashboard Manajemen Laboratorium Pembelajaran</div>
            <h1>Prioritas Hari Ini</h1>
            <p>LABORA membantu pengguna menemukan pekerjaan berikutnya: dokumen yang harus ditinjau, gap yang perlu ditutup, dan aktivitas harian yang perlu dicatat.</p>
            <div class="chip-wrap">{chips}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        render_metric("Dokumen Inti", total_docs)
    with c2:
        render_metric("Draft Perlu Review", draft_docs)

    c3, c4 = st.columns(2)
    with c3:
        render_metric("Gap Aktif", gap_docs)
    with c4:
        render_metric("Rata-rata Evaluasi", f"{avg_eval:.1f}")

    st.markdown('<div class="section-box"><div class="section-title">Tiga Fokus Utama</div>', unsafe_allow_html=True)
    if high_priority_drafts.empty:
        st.markdown('<div class="callout ok">Tidak ada dokumen prioritas tinggi berstatus draft saat ini.</div>', unsafe_allow_html=True)
    else:
        draft_titles = "<br>".join(
            [f"• {row['judul_dokumen']} ({row['unit']})" for _, row in high_priority_drafts.head(3).iterrows()]
        )
        st.markdown(f'<div class="callout danger"><b>Dokumen draft prioritas tinggi</b><br>{draft_titles}</div>', unsafe_allow_html=True)

    if urgent_gaps.empty:
        st.markdown('<div class="callout ok">Tidak ada gap aktif pada inventaris kebutuhan.</div>', unsafe_allow_html=True)
    else:
        gap_titles = "<br>".join(
            [f"• {row['nama_dokumen']} - target {row['target_selesai']}" for _, row in urgent_gaps.head(3).iterrows()]
        )
        st.markdown(f'<div class="callout warn"><b>Gap yang perlu ditindaklanjuti</b><br>{gap_titles}</div>', unsafe_allow_html=True)

    if low_eval.empty:
        st.markdown('<div class="callout ok">Belum ada evaluasi yang perlu disorot.</div>', unsafe_allow_html=True)
    else:
        low_titles = "<br>".join(
            [f"• {row['unit']} - {row['aspek']} ({int(row['skor_num'])})" for _, row in low_eval.head(3).iterrows()]
        )
        st.markdown(f'<div class="callout warn"><b>Skor evaluasi terendah</b><br>{low_titles}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-box"><div class="section-title">Logbook Terbaru</div>', unsafe_allow_html=True)
    latest_log = (
        logbook_df[["tanggal", "laboratorium", "kegiatan", "petugas"]].sort_values("tanggal", ascending=False).head(5)
        if not logbook_df.empty else logbook_df
    )
    render_table(latest_log, height=240)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-box"><div class="section-title">Dokumen Terakhir Diperbarui</div>', unsafe_allow_html=True)
    recent_docs = (
        dokumen_df.sort_values("tanggal_update_parsed", ascending=False)[["kategori", "judul_dokumen", "status", "tanggal_update"]].head(5)
        if not dokumen_df.empty else dokumen_df
    )
    render_table(recent_docs, height=220)
    st.markdown('</div>', unsafe_allow_html=True)


def global_search_results(data: Dict[str, pd.DataFrame], keyword: str) -> pd.DataFrame:
    keyword = keyword.strip()
    if not keyword:
        return pd.DataFrame()

    frames: List[pd.DataFrame] = []
    sources = {
        "Dokumen Inti": (data["dokumen_inti"], ["judul_dokumen", "kode", "kategori", "unit", "deskripsi", "file_ref"]),
        "SOP": (data["sop"], ["judul_sop", "kode_sop", "tujuan", "ruang_lingkup", "ringkasan_langkah", "pic"]),
        "Modul K3": (data["modul_k3"], ["judul_modul", "materi_pokok", "sasaran", "metode", "penanggung_jawab"]),
        "Instruksi Kerja": (data["instruksi_kerja"], ["judul_instruksi", "kode_ik", "langkah_utama", "alat_terkait", "apd_wajib", "pic"]),
    }

    for source_name, (df, cols) in sources.items():
        if df.empty:
            continue
        joined = df[cols].astype(str).apply(lambda col: col.str.contains(keyword, case=False, na=False))
        mask = joined.any(axis=1)
        if mask.any():
            matched = df.loc[mask].copy()
            matched.insert(0, "sumber", source_name)
            frames.append(matched)

    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def render_search(data: Dict[str, pd.DataFrame]) -> None:
    st.subheader("Cari & Buka Dokumen")
    st.caption("Cari lintas dokumen inti, SOP, modul K3, dan instruksi kerja dari satu tempat.")

    keyword = st.text_input(
        "Cari judul, kode, unit, PIC, atau kata kunci lain",
        placeholder="contoh: APD, inventaris, K3, praktikum"
    )

    if not keyword.strip():
        st.info("Masukkan kata kunci untuk memulai pencarian.")
        return

    results = global_search_results(data, keyword)
    if results.empty:
        st.warning("Tidak ada hasil yang cocok dengan kata kunci tersebut.")
        return

    st.success(f"Ditemukan {len(results)} hasil yang relevan.")
    source_filter = st.multiselect(
        "Filter sumber",
        sorted(results["sumber"].unique().tolist()),
        default=sorted(results["sumber"].unique().tolist())
    )
    if source_filter:
        results = results[results["sumber"].isin(source_filter)]

    for _, row in results.head(30).iterrows():
        title = row.get("judul_dokumen") or row.get("judul_sop") or row.get("judul_modul") or row.get("judul_instruksi")
        with st.expander(f"{row['sumber']} — {title}"):
            for col, val in row.items():
                if pd.isna(val) or str(val).strip() == "":
                    continue
                label = TABLE_HEADER_MAP.get(col, str(col).replace("_", " ").title())
                st.markdown(f"**{label}:** {val}")

            if row["sumber"] == "Dokumen Inti":
                public_url = build_public_url(str(row.get("file_ref", "")))
                if public_url:
                    st.link_button("Buka referensi dokumen", public_url)
                elif str(row.get("file_ref", "")).strip():
                    st.info(f"File referensi tercatat, tetapi URL publik belum tersedia: {row.get('file_ref', '')}")


def render_gap_analysis(data: Dict[str, pd.DataFrame]) -> None:
    st.subheader("Cek Gap & Tindak Lanjut")
    df = data["inventaris_kebutuhan"].copy()
    if df.empty:
        st.info("Belum ada data inventaris kebutuhan.")
        return

    df["gap_num"] = safe_numeric(df["gap"])
    df["target_selesai_parsed"] = parse_date_column(df["target_selesai"])

    priority = st.selectbox("Filter tingkat kebutuhan", ["Semua"] + sorted(df["tingkat_kebutuhan"].astype(str).unique().tolist()))
    availability = st.selectbox("Filter ketersediaan", ["Semua"] + sorted(df["ketersediaan"].astype(str).unique().tolist()))
    only_gap = st.checkbox("Tampilkan hanya item yang masih ada gap", value=True)

    filtered = df.copy()
    if priority != "Semua":
        filtered = filtered[filtered["tingkat_kebutuhan"] == priority]
    if availability != "Semua":
        filtered = filtered[filtered["ketersediaan"] == availability]
    if only_gap:
        filtered = filtered[filtered["gap_num"] > 0]

    c1, c2, c3 = st.columns(3)
    c1.metric("Item dengan Gap", int((filtered["gap_num"] > 0).sum()) if not filtered.empty else 0)
    c2.metric(
        "Gap Prioritas Tinggi",
        int(((filtered["gap_num"] > 0) & (filtered["tingkat_kebutuhan"].astype(str).str.lower() == "tinggi")).sum()) if not filtered.empty else 0
    )
    c3.metric(
        "Deadline Terdekat",
        filtered["target_selesai_parsed"].min().strftime("%Y-%m-%d")
        if not filtered.empty and filtered["target_selesai_parsed"].notna().any()
        else "-"
    )

    urgent = filtered.sort_values(["target_selesai_parsed", "gap_num"], ascending=[True, False]).head(5)
    if not urgent.empty:
        st.markdown("### Fokus Tindak Lanjut")
        for _, row in urgent.iterrows():
            level_cls = "danger" if str(row["tingkat_kebutuhan"]).lower() == "tinggi" else "warn"
            st.markdown(
                f'<div class="callout {level_cls}"><b>{row["nama_dokumen"]}</b><br>'
                f'Ketersediaan: {row["ketersediaan"]} | Gap: {int(row["gap_num"])} | '
                f'Target: {row["target_selesai"]} | PIC: {row["pic"]}<br>'
                f'{row["catatan_gap_analysis"]}</div>',
                unsafe_allow_html=True,
            )

    render_table(
        filtered[[
            "kelompok_dokumen", "nama_dokumen", "ketersediaan", "tingkat_kebutuhan", "gap",
            "prioritas_tindak_lanjut", "target_selesai", "pic", "catatan_gap_analysis"
        ]],
        height=360
    )


def render_input_harian(data: Dict[str, pd.DataFrame], db: Database) -> None:
    st.subheader("Input Harian")
    role = st.session_state.get("role")
    if role != "Admin":
        st.info("Reviewer dapat melihat data, tetapi input harian hanya tersedia untuk Admin.")
        return

    tabs = st.tabs(["Tambah Logbook", "Tambah Evaluasi", "Tambah Dokumen Inti"])

    with tabs[0]:
        with st.form("form_logbook"):
            c1, c2 = st.columns(2)
            tanggal = c1.date_input("Tanggal", value=date.today())
            lab = c2.text_input("Laboratorium", placeholder="Lab Kimia Dasar")
            kegiatan = st.text_input("Kegiatan")
            c3, c4 = st.columns(2)
            petugas = c3.text_input("Petugas")
            status = c4.selectbox("Status kegiatan", ["Selesai", "Proses", "Tertunda"])
            kendala = st.text_area("Temuan / Kendala")
            tindak_lanjut = st.text_area("Tindak lanjut")
            verifikator = st.text_input("Verifikator")

            if st.form_submit_button("Simpan logbook", type="primary"):
                required = [lab, kegiatan, petugas, verifikator]
                if not all(str(v).strip() for v in required):
                    st.error("Laboratorium, kegiatan, petugas, dan verifikator wajib diisi.")
                else:
                    db.insert_row("logbook", {
                        "tanggal": str(tanggal),
                        "laboratorium": lab.strip(),
                        "kegiatan": kegiatan.strip(),
                        "petugas": petugas.strip(),
                        "status_kegiatan": status,
                        "temuan_kendala": kendala.strip(),
                        "tindak_lanjut": tindak_lanjut.strip(),
                        "verifikator": verifikator.strip(),
                    })
                    st.success("Logbook berhasil disimpan.")
                    st.rerun()

    with tabs[1]:
        with st.form("form_evaluasi"):
            next_eval_id = next_id("EVA", data["evaluasi"]["id_evaluasi"]) if not data["evaluasi"].empty else "EVA-001"
            st.text_input("ID Evaluasi", value=next_eval_id, disabled=True)

            c1, c2 = st.columns(2)
            tanggal = c1.date_input("Tanggal evaluasi", value=date.today())
            unit = c2.text_input("Unit / Laboratorium")
            aspek = st.text_input("Aspek")

            c3, c4 = st.columns(2)
            skor = c3.number_input("Skor", min_value=0, max_value=100, value=80)
            kategori = c4.selectbox("Kategori", ["Baik", "Cukup", "Kurang"])

            rekomendasi = st.text_area("Rekomendasi")
            reviewer = st.text_input("Reviewer")

            if st.form_submit_button("Simpan evaluasi", type="primary"):
                required = [unit, aspek, reviewer]
                if not all(str(v).strip() for v in required):
                    st.error("Unit, aspek, dan reviewer wajib diisi.")
                else:
                    db.insert_row("evaluasi", {
                        "id_evaluasi": next_eval_id,
                        "tanggal": str(tanggal),
                        "unit": unit.strip(),
                        "aspek": aspek.strip(),
                        "skor": int(skor),
                        "kategori": kategori,
                        "rekomendasi": rekomendasi.strip(),
                        "reviewer": reviewer.strip(),
                    })
                    st.success("Evaluasi berhasil disimpan.")
                    st.rerun()

    with tabs[2]:
        with st.form("form_dokumen"):
            next_doc_id = next_id("DOC", data["dokumen_inti"]["id_dokumen"]) if not data["dokumen_inti"].empty else "DOC-001"
            st.text_input("ID Dokumen", value=next_doc_id, disabled=True)

            c1, c2, c3 = st.columns(3)
            kategori = c1.selectbox("Kategori", ["SOP", "Modul K3", "Instruksi Kerja", "Logbook", "Evaluasi", "Panduan", "Lainnya"])
            kode = c2.text_input("Kode")
            versi = c3.text_input("Versi", value="1.0")

            judul = st.text_input("Judul Dokumen")

            c4, c5, c6 = st.columns(3)
            status = c4.selectbox("Status", ["Draft", "Final", "Review"])
            penanggung_jawab = c5.text_input("Penanggung Jawab")
            unit = c6.text_input("Unit")

            c7, c8 = st.columns(2)
            tanggal_update = c7.date_input("Tanggal update", value=date.today())
            prioritas = c8.selectbox("Prioritas", ["Tinggi", "Sedang", "Rendah"])

            upload_mode = st.radio("Sumber referensi dokumen", ["Upload file", "Isi path manual", "Tanpa file"], horizontal=True)
            uploaded_doc = None
            manual_file_ref = ""

            if upload_mode == "Upload file":
                uploaded_doc = st.file_uploader(
                    f"Upload file dokumen (maks. {MAX_UPLOAD_MB} MB)",
                    type=[ext.lstrip(".") for ext in sorted(ALLOWED_DOC_EXTENSIONS)],
                    key="doc_upload_input",
                )
            elif upload_mode == "Isi path manual":
                manual_file_ref = st.text_input("Referensi file / URL", placeholder="misalnya https://... atau path file")

            deskripsi = st.text_area("Deskripsi")

            if st.form_submit_button("Simpan dokumen", type="primary"):
                required = [kode, judul, penanggung_jawab, unit]
                if not all(str(v).strip() for v in required):
                    st.error("Kode, judul dokumen, penanggung jawab, dan unit wajib diisi.")
                    return

                if not data["dokumen_inti"].empty:
                    existing_code = data["dokumen_inti"]["kode"].astype(str).map(normalize_text)
                    existing_title = data["dokumen_inti"]["judul_dokumen"].astype(str).map(normalize_text)
                    if normalize_text(kode) in set(existing_code):
                        st.error("Kode dokumen sudah ada. Gunakan kode yang berbeda.")
                        return
                    if normalize_text(judul) in set(existing_title):
                        st.error("Judul dokumen sudah ada. Gunakan judul berbeda atau ubah data yang lama.")
                        return

                file_ref = ""
                if upload_mode == "Upload file":
                    if uploaded_doc is None:
                        st.error("Silakan upload file dokumen terlebih dahulu.")
                        return
                    try:
                        file_ref = db.upload_document(uploaded_doc, kategori, kode)
                    except Exception as exc:
                        st.error(f"Gagal mengunggah dokumen ke storage online: {exc}")
                        return
                elif upload_mode == "Isi path manual":
                    if not manual_file_ref.strip():
                        st.error("Referensi file manual belum diisi.")
                        return
                    file_ref = manual_file_ref.strip()

                db.insert_row("dokumen_inti", {
                    "id_dokumen": next_doc_id,
                    "kategori": kategori,
                    "kode": kode.strip(),
                    "judul_dokumen": judul.strip(),
                    "versi": versi.strip(),
                    "status": status,
                    "penanggung_jawab": penanggung_jawab.strip(),
                    "unit": unit.strip(),
                    "tanggal_update": str(tanggal_update),
                    "prioritas": prioritas,
                    "file_ref": file_ref,
                    "deskripsi": deskripsi.strip(),
                })
                st.success("Dokumen inti berhasil disimpan.")
                st.rerun()


def render_documents_hub(data: Dict[str, pd.DataFrame]) -> None:
    st.subheader("Pusat Dokumen")
    section = st.radio(
        "Jenis Dokumen",
        ["Dokumen Inti", "SOP", "Modul K3", "Instruksi Kerja"],
        horizontal=True,
        label_visibility="collapsed"
    )

    if section == "Dokumen Inti":
        df = data["dokumen_inti"].copy()
        c1, c2 = st.columns(2)
        category = c1.selectbox("Filter Kategori", ["Semua"] + sorted(df["kategori"].astype(str).unique().tolist()) if not df.empty else ["Semua"])
        status = c2.selectbox("Filter Status", ["Semua"] + sorted(df["status"].astype(str).unique().tolist()) if not df.empty else ["Semua"])
        keyword = st.text_input("Cari Judul / Kode / Unit")

        filtered = df.copy()
        if not filtered.empty:
            if category != "Semua":
                filtered = filtered[filtered["kategori"] == category]
            if status != "Semua":
                filtered = filtered[filtered["status"] == status]
            if keyword.strip():
                mask = (
                    filtered["judul_dokumen"].astype(str).str.contains(keyword, case=False, na=False)
                    | filtered["kode"].astype(str).str.contains(keyword, case=False, na=False)
                    | filtered["unit"].astype(str).str.contains(keyword, case=False, na=False)
                )
                filtered = filtered[mask]

        render_table(filtered)
        st.download_button(
            "Unduh hasil filter (CSV)",
            filtered.to_csv(index=False).encode("utf-8-sig"),
            file_name="dokumen_inti_filter.csv",
            mime="text/csv"
        )

    elif section == "SOP":
        render_table(data["sop"])
    elif section == "Modul K3":
        render_table(data["modul_k3"])
    else:
        render_table(data["instruksi_kerja"])


def render_kelola_file(data: Dict[str, pd.DataFrame], db: Database) -> None:
    st.subheader("Kelola File")
    st.caption("Hapus file langsung dari storage online dan bersihkan referensinya dari database.")

    role = st.session_state.get("role")
    if role != "Admin":
        st.info("Menu ini hanya tersedia untuk Admin.")
        return

    df = data["dokumen_inti"].copy()
    if df.empty:
        st.info("Belum ada data dokumen inti.")
        return

    df_with_file = df[df["file_ref"].astype(str).str.strip() != ""].copy()
    if df_with_file.empty:
        st.info("Belum ada dokumen yang memiliki file terlampir.")
        return

    keyword = st.text_input(
        "Cari dokumen yang file-nya ingin dihapus",
        placeholder="judul dokumen, kode, kategori, unit, atau nama file"
    )

    filtered = df_with_file.copy()
    if keyword.strip():
        mask = (
            filtered["judul_dokumen"].astype(str).str.contains(keyword, case=False, na=False)
            | filtered["kode"].astype(str).str.contains(keyword, case=False, na=False)
            | filtered["kategori"].astype(str).str.contains(keyword, case=False, na=False)
            | filtered["unit"].astype(str).str.contains(keyword, case=False, na=False)
            | filtered["file_ref"].astype(str).str.contains(keyword, case=False, na=False)
        )
        filtered = filtered[mask]

    if filtered.empty:
        st.warning("Tidak ada dokumen yang cocok dengan pencarian.")
        return

    render_table(
        filtered[[
            "id_dokumen", "kategori", "kode", "judul_dokumen", "status", "unit", "file_ref"
        ]],
        height=320
    )

    options_map = {
        f"{row['judul_dokumen']} | {row['kode']} | {row['file_ref']}": row["id_dokumen"]
        for _, row in filtered.iterrows()
    }

    selected_label = st.selectbox(
        "Pilih dokumen yang file-nya akan dihapus",
        options=list(options_map.keys())
    )

    selected_id = options_map[selected_label]
    selected_row = filtered[filtered["id_dokumen"] == selected_id].iloc[0]
    selected_file_ref = str(selected_row["file_ref"]).strip()

    st.warning("Aksi ini akan menghapus file dari Supabase Storage dan mengosongkan kolom file_ref di database.")
    confirm = st.checkbox("Saya yakin ingin menghapus file ini")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Hapus file terpilih", type="primary", use_container_width=True, disabled=not confirm):
            try:
                db.delete_storage_file(selected_file_ref)
                db.update_row_by_id(
                    "dokumen_inti",
                    "id_dokumen",
                    selected_id,
                    {"file_ref": ""}
                )
                st.success("File berhasil dihapus dan referensi file di database sudah dibersihkan.")
                st.rerun()
            except Exception as exc:
                st.error(f"Gagal menghapus file: {exc}")

    with col2:
        public_url = build_public_url(selected_file_ref)
        if public_url:
            st.link_button("Buka file saat ini", public_url, use_container_width=True)


def render_evaluasi(data: Dict[str, pd.DataFrame]) -> None:
    st.subheader("Evaluasi & Insight")
    df = data["evaluasi"].copy()
    if df.empty:
        st.info("Belum ada data evaluasi.")
        return

    df["skor_num"] = safe_numeric(df["skor"])
    score = df["skor_num"]

    c1, c2, c3 = st.columns(3)
    c1.metric("Jumlah Evaluasi", len(df))
    c2.metric("Rata-rata Skor", f"{float(score.mean()):.1f}")
    c3.metric("Skor Terendah", f"{float(score.min()):.0f}")

    unit_summary = df.groupby("unit", as_index=False)["skor_num"].mean().sort_values("skor_num")
    st.markdown("### Unit dengan Skor Terendah")
    render_table(unit_summary.rename(columns={"skor_num": "skor"}).head(5), height=230)

    st.markdown("### Detail Evaluasi")
    render_table(
        df[["tanggal", "unit", "aspek", "skor", "kategori", "rekomendasi", "reviewer"]].sort_values("tanggal", ascending=False),
        height=360
    )


def render_admin_panel(data: Dict[str, pd.DataFrame]) -> None:
    st.subheader("Panel Admin")
    st.info("Panel admin pada versi cloud fokus pada monitoring data, storage online, dan pengecekan konfigurasi deploy.")

    total_files = int(data["dokumen_inti"]["file_ref"].astype(str).str.strip().ne("").sum()) if not data["dokumen_inti"].empty else 0
    col1, col2, col3 = st.columns(3)
    col1.metric("Dokumen dengan lampiran", total_files)
    col2.metric("Jumlah logbook", len(data["logbook"]))
    col3.metric("Jumlah evaluasi", len(data["evaluasi"]))

    st.markdown("### Konfigurasi deploy")
    st.write("- Database: Supabase Postgres")
    st.write(f"- Storage bucket: `{STORAGE_BUCKET}`")
    st.write("- Secrets: dibaca dari Streamlit Community Cloud")
    st.write("- Akun pengguna: admin/reviewer dari secrets, bukan hardcoded di repo")


def render_guidance(data: Dict[str, pd.DataFrame]) -> None:
    st.subheader("Panduan")
    st.markdown('<div class="section-box"><div class="section-title">Mulai dalam 3 langkah</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="action-card"><h4>1. Lihat prioritas</h4><p>Buka Beranda & Prioritas untuk melihat draft penting, gap aktif, dan skor evaluasi terendah.</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="action-card"><h4>2. Cari dokumen</h4><p>Gunakan Cari & Buka Dokumen untuk menemukan metadata dokumen dari satu tempat.</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="action-card"><h4>3. Input harian</h4><p>Admin dapat menambah logbook, evaluasi, dan dokumen inti langsung dari aplikasi.</p></div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("### Isi Panduan Data")

    panduan_df = data["panduan"].sort_values("urutan") if not data["panduan"].empty and "urutan" in data["panduan"].columns else data["panduan"]
    for _, row in panduan_df.iterrows():
        st.markdown(f"#### {row['bagian']}")
        st.write(row["isi"])


def main() -> None:
    st.set_page_config(page_title=APP_NAME, page_icon="🧪", layout="centered")
    inject_css()

    try:
        supabase = get_supabase()
    except Exception as exc:
        show_setup_error(exc)
        return

    if not auth_users():
        st.error("Belum ada user pada secrets.auth.users. Tambahkan minimal 1 admin dan 1 reviewer.")
        return

    db = Database(supabase)

    if not st.session_state.get("logged_in"):
        login_form()
        return

    try:
        data = load_data(db)
    except Exception as exc:
        st.error(f"Gagal memuat data dari Supabase: {exc}")
        return

    menu = sidebar_identity()
    render_welcome_strip()

    if menu == "Beranda & Prioritas":
        render_dashboard(data)
    elif menu == "Cari & Buka Dokumen":
        render_search(data)
    elif menu == "Cek Gap & Tindak Lanjut":
        render_gap_analysis(data)
    elif menu == "Input Harian":
        render_input_harian(data, db)
    elif menu == "Evaluasi & Insight":
        render_evaluasi(data)
    elif menu == "Pusat Dokumen":
        render_documents_hub(data)
    elif menu == "Kelola File":
        render_kelola_file(data, db)
    elif menu == "Panel Admin":
        if st.session_state.get("role") != "Admin":
            st.warning("Menu ini hanya dapat diakses oleh Admin.")
        else:
            render_admin_panel(data)
    elif menu == "Panduan":
        render_guidance(data)


if __name__ == "__main__":
    main()
