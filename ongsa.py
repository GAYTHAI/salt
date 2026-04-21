import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# --- Application Header ---
st.set_page_config(layout="wide")
st.title("📊 Advanced SFD/BMD Calculator")
st.write("Dynamically add any combination of loads and select your support condition.")

# --- Sidebar Inputs ---
st.sidebar.header("1. Beam Parameters")
L = st.sidebar.number_input("Beam Length (m):", min_value=1.0, value=10.0, step=1.0)
support_type = st.sidebar.selectbox(
    "Support Condition:", 
    ["Simply Supported", "Cantilever (Fixed Left)", "Cantilever (Fixed Right)"]
)

# --- Dynamic Load Inputs ---
st.header("2. Define Loads (Downward)")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Point Loads (kN)")
    # Default data for point loads
    pl_init = pd.DataFrame([{"Magnitude (kN)": 50.0, "Location (m)": 5.0}])
    # data_editor allows the user to add/delete rows dynamically
    pl_df = st.data_editor(pl_init, num_rows="dynamic", hide_index=True)

with col2:
    st.subheader("Distributed Loads (kN/m)")
    # Default data for Uniformly Distributed Loads (UDL)
    udl_init = pd.DataFrame([{"Magnitude (kN/m)": 10.0, "Start (m)": 0.0, "End (m)": 10.0}])
    udl_df = st.data_editor(udl_init, num_rows="dynamic", hide_index=True)

# --- Core Engine (Reactions & Macaulay Integration) ---
# 1. Calculate Total Applied Forces and Moments
F_tot = 0.0
M_tot = 0.0  # Moment about x=0

for _, row in pl_df.iterrows():
    if pd.notna(row["Magnitude (kN)"]) and pd.notna(row["Location (m)"]):
        P = row["Magnitude (kN)"]
        a = row["Location (m)"]
        F_tot -= P           # Downward force
        M_tot -= (P * a)     # Clockwise moment about x=0

for _, row in udl_df.iterrows():
    if pd.notna(row["Magnitude (kN/m)"]) and pd.notna(row["Start (m)"]) and pd.notna(row["End (m)"]):
        w = row["Magnitude (kN/m)"]
        start = row["Start (m)"]
        end = row["End (m)"]
        if end > start:
            force = w * (end - start)
            centroid = (start + end) / 2.0
            F_tot -= force
            M_tot -= (force * centroid)

# 2. Calculate Support Reactions
Ra, Ma = 0.0, 0.0

if support_type == "Simply Supported":
    Rb = -M_tot / L
    Ra = -F_tot - Rb
    reaction_text = f"Left Support ($R_a$): **{Ra:.2f} kN** | Right Support ($R_b$): **{Rb:.2f} kN**"

elif support_type == "Cantilever (Fixed Left)":
    Ra = -F_tot
    Ma = -M_tot
    reaction_text = f"Fixed Left ($x=0$) -> Vertical ($R_a$): **{Ra:.2f} kN** | Moment ($M_a$): **{Ma:.2f} kNm**"

elif support_type == "Cantilever (Fixed Right)":
    # For a right cantilever, the left side has 0 reaction. 
    # Integration will handle the right-side reactions automatically.
    Rb = -F_tot
    Mb = -M_tot + (L * F_tot)
    reaction_text = f"Fixed Right ($x=L$) -> Vertical ($R_b$): **{Rb:.2f} kN** | Moment ($M_b$): **{Mb:.2f} kNm**"

# 3. Generate Diagram Arrays (Macaulay's Method)
x = np.linspace(0, L, 1000)
V = np.zeros_like(x)
M = np.zeros_like(x)

# Apply Left Boundary Conditions
V += Ra
M += (Ra * x) - Ma

# Step-integrate Point Loads
for _, row in pl_df.iterrows():
    if pd.notna(row["Magnitude (kN)"]) and pd.notna(row["Location (m)"]):
        P = row["Magnitude (kN)"]
        a = row["Location (m)"]
        if P > 0:
            V -= np.where(x >= a, P, 0)
            M -= np.where(x >= a, P * (x - a), 0)

# Step-integrate Distributed Loads
for _, row in udl_df.iterrows():
    if pd.notna(row["Magnitude (kN/m)"]) and pd.notna(row["Start (m)"]) and pd.notna(row["End (m)"]):
        w = row["Magnitude (kN/m)"]
        start = row["Start (m)"]
        end = row["End (m)"]
        if w > 0 and end > start:
            # Apply load starting at 'start'
            V -= np.where(x >= start, w * (x - start), 0)
            M -= np.where(x >= start, (w / 2.0) * (x - start)**2, 0)
            # Cut off the load at 'end' by applying an inverse upward load
            V += np.where(x >= end, w * (x - end), 0)
            M += np.where(x >= end, (w / 2.0) * (x - end)**2, 0)

# --- Dashboard Output ---
st.divider()
st.subheader("Support Reactions")
st.info(reaction_text)

# Render Plots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
fig.tight_layout(pad=5.0)

# Shear Force Plot
ax1.plot(x, V, color='#1f77b4', linewidth=2.5)
ax1.fill_between(x, V, 0, alpha=0.3, color='#1f77b4')
ax1.axhline(0, color='black', linewidth=1.5)
ax1.set_title("Shear Force Diagram (SFD)", fontsize=14)
ax1.set_ylabel("Shear Force (kN)", fontsize=12)
ax1.grid(True, linestyle='--', alpha=0.6)
# Annotate max/min shear
ax1.text(0.01, 0.95, f"Max Shear: {np.max(V):.2f} kN", transform=ax1.transAxes, color='green', fontweight='bold')
ax1.text(0.01, 0.05, f"Min Shear: {np.min(V):.2f} kN", transform=ax1.transAxes, color='red', fontweight='bold')

# Bending Moment Plot
ax2.plot(x, M, color='#ff7f0e', linewidth=2.5)
ax2.fill_between(x, M, 0, alpha=0.3, color='#ff7f0e')
ax2.axhline(0, color='black', linewidth=1.5)
ax2.set_title("Bending Moment Diagram (BMD)", fontsize=14)
ax2.set_xlabel("Distance along Beam (m)", fontsize=12)
ax2.set_ylabel("Bending Moment (kNm)", fontsize=12)
ax2.grid(True, linestyle='--', alpha=0.6)
# Annotate max/min moment
ax2.text(0.01, 0.95, f"Max Moment: {np.max(M):.2f} kNm", transform=ax2.transAxes, color='green', fontweight='bold')
ax2.text(0.01, 0.05, f"Min Moment: {np.min(M):.2f} kNm", transform=ax2.transAxes, color='red', fontweight='bold')

st.pyplot(fig)