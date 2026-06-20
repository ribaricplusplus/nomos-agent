import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(page_title="Fake Nomos Dashboard", layout="wide")

st.title("⚡ Fake Nomos Dashboard")

conn = sqlite3.connect("nomos.db")

cases = pd.read_sql_query("SELECT * FROM cases", conn)
call_logs = pd.read_sql_query("SELECT * FROM call_logs", conn)
audit_logs = pd.read_sql_query("SELECT * FROM audit_logs", conn)

# ======================
# KPI CARDS
# ======================

total_cases = len(cases)
open_cases = len(cases[cases["case_status"] == "OPEN"])
total_calls = len(call_logs)
total_updates = len(audit_logs)

col1, col2, col3, col4 = st.columns(4)

col1.metric("📋 Total Cases", total_cases)
col2.metric("🟢 Open Cases", open_cases)
col3.metric("📞 Calls Made", total_calls)
col4.metric("📝 Audit Updates", total_updates)

st.divider()

# ======================
# CASES
# ======================

st.header("📋 Cases")
st.dataframe(cases, use_container_width=True)

# ======================
# CALL LOGS
# ======================

st.header("📞 Call Logs")
st.dataframe(call_logs, use_container_width=True)

# ======================
# AUDIT LOGS
# ======================

st.header("📝 Audit Logs")
st.dataframe(audit_logs, use_container_width=True)

conn.close()