import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- Application Header ---
st.title("📊 Quick SFD/BMD Generator")
st.write("A lightweight tool to instantly visualize Shear Force and Bending Moment Diagrams for a simply supported beam.")

# --- Sidebar Inputs ---
st.sidebar.header("1. Beam Parameters")
# Input beam length
L = st.sidebar.number_input("Beam Length (m):", min_value=1.0, value=10.0, step=1.0)

st.sidebar.header("2. Point Load Configuration")
# Input load magnitude and location
P = st.sidebar.number_input("Load Magnitude (kN):", min_value=0.0, value=50.0, step=5.0)
a = st.sidebar.number_input("Distance from Left Support (m):", min_value=0.0, max_value=float(L), value=L/2, step=0.5)

# --- Core Engine (Calculations) ---
# Calculate Support Reactions
# Sum of moments about A = 0 -> Rb * L = P * a
Rb = (P * a) / L
# Sum of vertical forces = 0 -> Ra + Rb = P
Ra = P - Rb

# Generate x coordinates across the beam (500 points for smooth plotting)
x = np.linspace(0, L, 500)

# Calculate Shear Force (V) array
# V = Ra (before the load), V = Ra - P (after the load)
V = np.where(x < a, Ra, Ra - P)

# Calculate Bending Moment (M) array
# M = Ra * x (before the load), M = Ra * x - P * (x - a) (after the load)
M = np.where(x < a, Ra * x, Ra * x - P * (x - a))

# --- Dashboard Output ---
st.header("Support Reactions")
col1, col2 = st.columns(2)
col1.metric(label="Left Support Reaction ($R_a$)", value=f"{Ra:.2f} kN")
col2.metric(label="Right Support Reaction ($R_b$)", value=f"{Rb:.2f} kN")

st.header("Structural Diagrams")

# Initialize the plot (2 rows, 1 column)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))
fig.tight_layout(pad=4.0)

# Plot 1: Shear Force Diagram (SFD)
ax1.plot(x, V, color='#1f77b4', linewidth=2)
ax1.fill_between(x, V, 0, alpha=0.3, color='#1f77b4')
ax1.axhline(0, color='black', linewidth=1.5)
ax1.set_title("Shear Force Diagram (SFD)")
ax1.set_ylabel("Shear Force (kN)")
ax1.grid(True, linestyle='--', alpha=0.6)

# Plot 2: Bending Moment Diagram (BMD)
ax2.plot(x, M, color='#ff7f0e', linewidth=2)
ax2.fill_between(x, M, 0, alpha=0.3, color='#ff7f0e')
ax2.axhline(0, color='black', linewidth=1.5)
ax2.set_title("Bending Moment Diagram (BMD)")
ax2.set_xlabel("Distance along Beam (m)")
ax2.set_ylabel("Bending Moment (kNm)")
ax2.grid(True, linestyle='--', alpha=0.6)

# Render the plot in Streamlit
st.pyplot(fig)