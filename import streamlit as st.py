import streamlit as st
import pandas as pd

# --- Application Header ---
st.title("🏗️ Alternative Material Estimator")
st.write("Compare standard concrete against CLC and Pozzolan-blended alternatives for weight and cost estimation.")

# --- Material Database (Constants) ---
# Densities are in kg/m3, Costs are estimated per m3
materials = {
    "Standard Concrete (OPC)": {"density": 2400, "cost_per_m3": 110, "compressive_strength_mpa": 25},
    "Cellular Lightweight Concrete (CLC)": {"density": 1200, "cost_per_m3": 130, "compressive_strength_mpa": 10},
    "Pozzolan Blend (20% Fly Ash)": {"density": 2350, "cost_per_m3": 95, "compressive_strength_mpa": 28}
}

# --- Sidebar Inputs ---
st.sidebar.header("Project Parameters")
volume_m3 = st.sidebar.number_input("Required Volume (cubic meters):", min_value=1.0, value=10.0, step=1.0)
application_type = st.sidebar.selectbox("Structural Application:", ["Load-bearing slab", "Partition wall", "Ferrocement shell"])

# --- Core Engine (Calculations) ---
results = []
for material, props in materials.items():
    total_weight_kg = props["density"] * volume_m3
    total_cost = props["cost_per_m3"] * volume_m3
    
    # Calculate weight reduction compared to OPC
    opc_weight = materials["Standard Concrete (OPC)"]["density"] * volume_m3
    weight_savings = opc_weight - total_weight_kg
    
    results.append({
        "Material": material,
        "Total Weight (kg)": total_weight_kg,
        "Weight Saved (kg)": weight_savings,
        "Total Cost ($)": total_cost,
        "Est. Strength (MPa)": props["compressive_strength_mpa"]
    })

df_results = pd.DataFrame(results)

# --- Main Dashboard Output ---
st.subheader(f"Analysis for {volume_m3} cubic meters - {application_type}")

# Display metrics side-by-side for quick comparison
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("OPC Total Weight", f"{df_results.iloc[0]['Total Weight (kg)']:,} kg")
with col2:
    st.metric("CLC Weight Saved", f"{df_results.iloc[1]['Weight Saved (kg)']:,} kg")
with col3:
    st.metric("Pozzolan Cost Savings", f"${(df_results.iloc[0]['Total Cost ($)'] - df_results.iloc[2]['Total Cost ($)']):,.2f}")

# Display full table
st.write("### Detailed Comparison")
st.dataframe(df_results.style.format({
    "Total Weight (kg)": "{:,.0f}",
    "Weight Saved (kg)": "{:,.0f}",
    "Total Cost ($)": "${:,.2f}"
}))

st.info("Note: Strength values are estimated at 28 days. Mix designs must be verified by a structural engineer.")