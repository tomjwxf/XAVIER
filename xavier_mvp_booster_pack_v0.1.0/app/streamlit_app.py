import os, json, glob
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

from pathlib import Path

st.set_page_config(page_title="Xavier KPI", layout="wide")

st.title("Xavier — Receipt KPIs (Demo)")

path = st.text_input("Receipts folder (local path or repo checkout)", "test_vectors/receipts")

def load_receipts(folder):
    recs = []
    for p in glob.glob(os.path.join(folder, "*.json")):
        try:
            with open(p) as f:
                recs.append(json.load(f))
        except Exception:
            pass
    return recs

recs = load_receipts(path)

col1, col2, col3 = st.columns(3)
col1.metric("Receipts loaded", f"{len(recs)}")
if recs:
    latencies = [r.get("receipt_emission_ms", 0) for r in recs if isinstance(r.get("receipt_emission_ms"), int)]
    p95 = int(np.percentile(latencies, 95)) if latencies else 0
    col2.metric("p95 emission (ms)", f"{p95}")
    coverage = int(100 * (len([r for r in recs if r.get('incident_code') is None]) / max(len(recs),1)))
    col3.metric("Coverage (no incidents)", f"{coverage}%")

    st.subheader("Latency histogram (ms)")
    fig = plt.figure()
    plt.hist(latencies, bins=min(20, max(5, len(latencies)//2)))
    plt.xlabel("receipt_emission_ms")
    plt.ylabel("count")
    st.pyplot(fig)

st.download_button("Download Auditor Pack (zip)", data=b"", file_name="AUDITOR_PACK_PLACEHOLDER.zip", disabled=True, help="Use make_auditor_pack.py to generate this zip and upload somewhere.")
