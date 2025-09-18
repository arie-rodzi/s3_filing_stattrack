import os, re
import streamlit as st
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from dateutil import parser as dtparser

load_dotenv()
DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
PUBLIC_DIR = DATA_DIR / "public"
EXCEL_PATH = DATA_DIR / "Lantikan LIC Mac 2024.xlsx"  # optional: read direct
ALLOWED_TYPES = {"rubrics","course_info","cap"}

st.set_page_config(page_title="Portal Umum – Statistik UiTM N9", layout="wide")
st.title("Portal Umum – Jabatan Statistik UiTM N9 (Seremban)")

# A) Dokumen Umum
st.subheader("A. Dokumen Umum (View-Only)")
if not PUBLIC_DIR.exists():
    st.warning("Folder /data/public belum ada.")
else:
    files = []
    for p in PUBLIC_DIR.rglob("*"):
        if p.is_file():
            parts = p.relative_to(PUBLIC_DIR).parts
            jenis = parts[0].lower() if parts else ""
            if jenis in ALLOWED_TYPES:
                files.append({"type": jenis, "filename": p.name, "path": str(p)})
    dfp = pd.DataFrame(files).sort_values(["type","filename"]) if files else pd.DataFrame()
    q = st.text_input("Cari dokumen (jenis/nama fail)")
    if not dfp.empty:
        if q:
            ql = q.lower()
            dfp = dfp[dfp.apply(lambda r: ql in r["type"].lower() or ql in r["filename"].lower(), axis=1)]
        for _, r in dfp.iterrows():
            st.write(f"**{r['type'].upper()}** — {r['filename']}")
            with open(r["path"], "rb") as fh:
                st.download_button("Muat Turun", data=fh, file_name=r["filename"], key=r["path"])

st.markdown("---")

# B) Jadual LIC/RP (load from seeded master, not necessarily Excel)
st.subheader("B. Senarai LIC/RP & Tempoh Lantikan")
MASTER_XLSX = DATA_DIR / "subjects_master_with_periods_v2.xlsx"
df = None
try:
    df = pd.read_excel(MASTER_XLSX)
except Exception:
    # fallback: try csv
    try:
        df = pd.read_csv(MASTER_XLSX.with_suffix(".csv"))
    except Exception:
        st.error("Master LIC/RP belum dimuat naik ke /data.")
        df = None

if df is not None and not df.empty:
    q2 = st.text_input("Cari (kod/nama subjek atau nama pensyarah)")
    if q2:
        ql = q2.lower()
        df = df[df.apply(lambda r: any(ql in str(v).lower() for v in r.values), axis=1)]
    st.dataframe(df[["subject_code","subject_name","LIC","LIC_start","LIC_end","RP","RP_start","RP_end"]], use_container_width=True)
