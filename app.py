import os, re
import streamlit as st
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from sqlmodel import Session, select
from db import get_engine, init_db, User, Subject, FileItem
from utils import ensure_dirs, sha256_bytes, hash_password, verify_password
from datetime import datetime

load_dotenv()

# Config / paths
DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
ensure_dirs(DATA_DIR / "uploads")
ensure_dirs(DATA_DIR / "public" / "rubrics")
ensure_dirs(DATA_DIR / "public" / "course_info")
ensure_dirs(DATA_DIR / "public" / "cap")

DB_PATH = DATA_DIR / "mytimes.db"
engine = get_engine(str(DB_PATH))
init_db(engine)

st.set_page_config(page_title="Sistem Filing – Statistik UiTM N9", layout="wide")
st.title("Sistem Filing – Jabatan Statistik UiTM N9 (Seremban)")

# --- First-run seeding from seed/all_users_credentials.xlsx & subjects_master_with_periods_v2.xlsx
def seed_users_if_empty():
    with Session(engine) as s:
        count = s.exec(select(User)).first()
        if count is not None:
            return
    seed_path = Path(__file__).parent / "seed" / "all_users_credentials.xlsx"
    if seed_path.exists():
        df = pd.read_excel(seed_path)
        rows = []
        for _, r in df.iterrows():
            pw = str(r.get("password","")).strip()
            rows.append(User(
                category=str(r.get("category","")).upper() or "LECTURER",
                role=str(r.get("role","")).upper() or "LECTURER",
                name=str(r.get("name","")),
                username=str(r.get("username","")).lower(),
                password_hash=hash_password(pw if pw else "ChangeMe!123"),
                notes=str(r.get("notes",""))
            ))
        with Session(engine) as s:
            for u in rows:
                s.add(u)
            s.commit()

def seed_subjects_if_empty():
    with Session(engine) as s:
        any_subj = s.exec(select(Subject)).first()
        if any_subj is not None:
            return
    seed_path = Path(__file__).parent / "seed" / "subjects_master_with_periods_v2.xlsx"
    if seed_path.exists():
        df = pd.read_excel(seed_path)
        rows = []
        for _, r in df.iterrows():
            rows.append(Subject(
                code=str(r.get("subject_code","")).strip(),
                name=str(r.get("subject_name","")).strip(),
                lic=str(r.get("LIC","")).strip(),
                lic_start=str(r.get("LIC_start","")).strip(),
                lic_end=str(r.get("LIC_end","")).strip(),
                rp=str(r.get("RP","")).strip(),
                rp_start=str(r.get("RP_start","")).strip(),
                rp_end=str(r.get("RP_end","")).strip(),
            ))
        with Session(engine) as s:
            for u in rows:
                if u.code:
                    s.add(u)
            s.commit()

seed_users_if_empty()
seed_subjects_if_empty()

# ---- Auth (simple inline form)
st.sidebar.header("Log Masuk")
username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")
login_btn = st.sidebar.button("Login")

user = None
if login_btn:
    with Session(engine) as s:
        u = s.exec(select(User).where(User.username == username.lower())).first()
        if u and verify_password(password, u.password_hash):
            user = u
            st.session_state["user"] = {"username": u.username, "role": u.role, "category": u.category, "name": u.name}
        else:
            st.sidebar.error("Username atau kata laluan salah.")
elif "user" in st.session_state:
    ss = st.session_state["user"]
    with Session(engine) as s:
        user = s.exec(select(User).where(User.username == ss["username"])).first()

if not user:
    st.info("Sila log masuk untuk akses fungsi (Admin/KPP/AJK/Auditor/Lecturer). Untuk public view, jalankan public_view.py")
    st.stop()

st.sidebar.success(f"Log masuk sebagai: {user.username} ({user.role})")
st.sidebar.write("Kategori:", user.category)
if st.sidebar.button("Log Keluar"):
    st.session_state.pop("user", None)
    st.rerun()

# ---- Tabs by role
role = user.role.upper()
tabs = st.tabs(["Upload", "Arkib", "Subjek (LIC/RP)", "Admin"] if role in {"ADMIN","KPP","AJK","AUDITOR","LECTURER"} else ["Upload","Arkib"])

# Upload tab (Lecturer/AJK/Admin/KPP)
with tabs[0]:
    st.subheader("Muat Naik Dokumen Kursus")
    with Session(engine) as s:
        subjects = s.exec(select(Subject).order_by(Subject.code)).all()
    if not subjects:
        st.warning("Belum ada subjek dalam sistem. (Admin → tambah subjek)")
    else:
        submap = {f"{x.code} — {x.name}": x.code for x in subjects}
        sub_label = st.selectbox("Subjek", list(submap.keys()))
        subject_code = submap[sub_label]

        col1, col2, col3 = st.columns(3)
        with col1:
            role_sel = st.selectbox("Peranan dalam subjek", ["LIC","RP","STAFF"])
        with col2:
            doc_type = st.selectbox("Jenis Dokumen", ["rubrics","course_info","cap","lesson_plan","slt","jsu_final","jsu_test","jsu_project","surat_lantikan_lic","surat_lantikan_rp"])
        with col3:
            semester = st.text_input("Semester", value="Okt 2025")

        file = st.file_uploader("Pilih fail", type=None)
        if file and st.button("Upload"):
            data = file.read()
            digest = sha256_bytes(data)
            # Public documents go to /public/<type>/ ; others to /uploads/
            if doc_type in {"rubrics","course_info","cap"}:
                dest_dir = DATA_DIR/"public"/doc_type
            else:
                dest_dir = DATA_DIR/"uploads"
            dest_dir.mkdir(parents=True, exist_ok=True)
            safe_name = f"{subject_code}_{role_sel}_{doc_type}_{semester}_{digest[:8]}_{file.name}"
            dest = dest_dir/safe_name
            if not dest.exists():
                with open(dest, "wb") as fh:
                    fh.write(data)
            with Session(engine) as s:
                rec = FileItem(subject_code=subject_code, uploader_username=user.username, role=role_sel, doc_type=doc_type, semester=semester, path=str(dest), sha256=digest)
                s.add(rec); s.commit()
            st.success("Berjaya dimuat naik & DISIMPAN KEKAL ✅")

# Arkib tab (role visibility)
with tabs[1]:
    st.subheader("Arkib Dokumen")
    q = st.text_input("Cari (kod/nama fail/jenis/semester/uploader):")
    with Session(engine) as s:
        rows = s.exec(select(FileItem).order_by(FileItem.uploaded_at.desc())).all()
    df = pd.DataFrame([r.__dict__ for r in rows]) if rows else pd.DataFrame()
    if df.empty:
        st.info("Tiada dokumen.")
    else:
        # Role filter: AUDITOR can see all (read-only). LECTURER sees own uploads by default.
        if role == "LECTURER":
            df = df[df["uploader_username"] == user.username]
        # search filter
        if q:
            ql = q.lower()
            df = df[df.apply(lambda r: any(ql in str(v).lower() for v in r.values), axis=1)]
        st.dataframe(df[["subject_code","doc_type","semester","uploader_username","uploaded_at","path"]], use_container_width=True)
        # download buttons
        for _, r in df.iterrows():
            p = Path(r["path"])
            if p.exists():
                with open(p, "rb") as fh:
                    st.download_button("Muat Turun", data=fh, file_name=p.name, key=str(p))

# Subjek tab (view LIC/RP) – visible to all roles
with tabs[2]:
    st.subheader("Senarai Subjek (Siapa LIC/RP & Tempoh Lantikan)")
    with Session(engine) as s:
        subs = s.exec(select(Subject).order_by(Subject.code)).all()
    df = pd.DataFrame([{
        "subject_code": x.code, "subject_name": x.name,
        "LIC": x.lic, "LIC_start": x.lic_start, "LIC_end": x.lic_end,
        "RP": x.rp, "RP_start": x.rp_start, "RP_end": x.rp_end
    } for x in subs])
    q2 = st.text_input("Cari subjek/nama pensyarah")
    if not df.empty and q2:
        ql = q2.lower()
        df = df[df.apply(lambda r: any(ql in str(v).lower() for v in r.values), axis=1)]
    st.dataframe(df, use_container_width=True)

# Admin tab
with tabs[3]:
    if role not in {"ADMIN","KPP","AJK"}:
        st.info("Hanya Admin/KPP/AJK boleh akses tetapan ini.")
    else:
        st.subheader("Pentadbiran")
        st.markdown("**Pengguna**")
        # List users
        with Session(engine) as s:
            users = s.exec(select(User).order_by(User.username)).all()
        udf = pd.DataFrame([{"category":u.category,"role":u.role,"name":u.name,"username":u.username,"notes":u.notes} for u in users])
        st.dataframe(udf, use_container_width=True, height=250)
        st.caption("Nota: Tukar kata laluan melalui arahan CLI atau modul mudah alih (boleh tambah UI kemudian).")

        st.markdown("---")
        st.markdown("**Subjek**")
        # Add/remove subjects
        with Session(engine) as s:
            subs = s.exec(select(Subject).order_by(Subject.code)).all()
        sdf = pd.DataFrame([{"code":x.code,"name":x.name,"LIC":x.lic,"RP":x.rp} for x in subs])
        st.dataframe(sdf, use_container_width=True, height=250)

        colA, colB = st.columns(2)
        with colA:
            st.write("Tambah Subjek")
            new_code = st.text_input("Kod")
            new_name = st.text_input("Nama")
            if st.button("Tambah"):
                if new_code and new_name:
                    with Session(engine) as s:
                        s.add(Subject(code=new_code.strip(), name=new_name.strip()))
                        try:
                            s.commit(); st.success("Ditambah.")
                        except Exception as e:
                            st.error(f"Gagal tambah: {e}")
                else:
                    st.warning("Isi kod & nama.")
        with colB:
            st.write("Buang Subjek")
            del_code = st.text_input("Kod untuk dibuang")
            if st.button("Buang"):
                with Session(engine) as s:
                    sub = s.exec(select(Subject).where(Subject.code == del_code.strip())).first()
                    if sub:
                        s.delete(sub); s.commit(); st.success("Dibuang.")
                    else:
                        st.warning("Kod tidak ditemui.")
