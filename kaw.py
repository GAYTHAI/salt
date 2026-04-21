import streamlit as st
import pandas as pd
from indeterminatebeam import Beam, Support, PointLoadV, TrapezoidalLoadV, PointTorque
import plotly.graph_objects as go

# --- Application Header ---
st.set_page_config(layout="wide", page_title="Pro SFD/BMD Calculator")
st.title("🏗️ Professional SFD & BMD Calculator")
st.write("Supports indeterminate beams, point moments, and complex distributed loads (Uniform, Triangular, Trapezoidal).")

# --- 1. Beam & Supports ---
st.header("1. Beam & Support Conditions")
col_beam, col_sup = st.columns([1, 2])

with col_beam:
    L = st.number_input("Beam Length (m):", min_value=1.0, value=10.0, step=1.0)

with col_sup:
    st.write("Define Supports (Pin, Roller, Fixed)")
    sup_init = pd.DataFrame([
        {"Location (m)": 0.0, "Type": "Pin"},
        {"Location (m)": 10.0, "Type": "Roller"}
    ])
    sup_df = st.data_editor(sup_init, num_rows="dynamic", hide_index=True)

# --- 2. Load Definitions ---
st.header("2. Define Applied Loads")
st.info("Note: Enter magnitudes as positive numbers. The engine assumes standard gravity/downward acting forces.")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Point Loads (kN)")
    pl_init = pd.DataFrame([{"Magnitude (kN)": 50.0, "Location (m)": 5.0}])
    pl_df = st.data_editor(pl_init, num_rows="dynamic", hide_index=True)

with col2:
    st.subheader("Distributed Loads (kN/m)")
    st.caption("For Uniform: Start Mag = End Mag. For Triangular: Set one Mag to 0.")
    dl_init = pd.DataFrame([{
        "Start Loc (m)": 0.0, "End Loc (m)": 5.0, 
        "Start Mag (kN/m)": 10.0, "End Mag (kN/m)": 20.0 
    }])
    dl_df = st.data_editor(dl_init, num_rows="dynamic", hide_index=True)

with col3:
    st.subheader("Point Moments (kNm)")
    st.caption("Positive = Clockwise, Negative = Anti-Clockwise")
    pm_init = pd.DataFrame([{"Magnitude (kNm)": 0.0, "Location (m)": 0.0}]) 
    pm_df = st.data_editor(pm_init, num_rows="dynamic", hide_index=True)

# --- 3. Core Engine & Visualization ---
st.divider()
st.header("Structural Analysis")

try:
    beam_length = float(L)
    beam = Beam(beam_length)

    # Dictionary for Support mappings
    support_dict = {
        "Fixed": (1, 1, 1),
        "Pin": (1, 1, 0),
        "Roller": (0, 1, 0)
    }
    
    # ---------------------------------------------------------
    # NEW FEATURE: CUSTOM VISUAL LOAD DIAGRAM (FREE BODY DIAGRAM)
    # ---------------------------------------------------------
    fig_fbd = go.Figure()
    
    # Draw Beam
    fig_fbd.add_trace(go.Scatter(x=[0, beam_length], y=[0, 0], mode='lines', line=dict(color='black', width=6), showlegend=False))
    
    # Add Supports to visual and engine
    for _, row in sup_df.iterrows():
        if pd.notna(row["Location (m)"]) and pd.notna(row["Type"]):
            loc = float(row["Location (m)"])
            sup_type = row["Type"]
            
            # Add to engine
            if sup_type in support_dict:
                beam.add_supports(Support(loc, support_dict[sup_type]))
                
            # Add to visual
            symbol = 'triangle-up' if sup_type in ["Pin", "Roller"] else 'square'
            color = '#1f77b4' if sup_type in ["Pin", "Roller"] else 'gray'
            size = 18 if sup_type in ["Pin", "Roller"] else 12
            fig_fbd.add_trace(go.Scatter(
                x=[loc], y=[0], mode='markers', 
                marker=dict(symbol=symbol, size=size, color=color), 
                name=f"{sup_type} Support", hoverinfo="name+x"
            ))

    # Add Point Loads to visual and engine
    for _, row in pl_df.iterrows():
        if pd.notna(row["Magnitude (kN)"]) and pd.notna(row["Location (m)"]):
            if row["Magnitude (kN)"] != 0:
                mag = float(row["Magnitude (kN)"])
                loc = float(row["Location (m)"])
                
                # Add to engine
                beam.add_loads(PointLoadV(-mag, loc))
                
                # Add to visual (Red downward arrows)
                fig_fbd.add_annotation(
                    x=loc, y=0.1, ax=loc, ay=1.2, 
                    xref='x', yref='y', axref='x', ayref='y',
                    showarrow=True, arrowhead=2, arrowsize=1.5, arrowwidth=2.5, arrowcolor='red'
                )
                fig_fbd.add_annotation(x=loc, y=1.35, text=f"{mag} kN", showarrow=False, font=dict(color="red", size=12))

    # Add Distributed Loads to visual and engine
    for _, row in dl_df.iterrows():
        if all(pd.notna(row[col]) for col in ["Start Loc (m)", "End Loc (m)", "Start Mag (kN/m)", "End Mag (kN/m)"]):
            if row["Start Mag (kN/m)"] != 0 or row["End Mag (kN/m)"] != 0:
                start_mag = float(row["Start Mag (kN/m)"])
                end_mag = float(row["End Mag (kN/m)"])
                start_loc = float(row["Start Loc (m)"])
                end_loc = float(row["End Loc (m)"])
                
                # Add to engine
                beam.add_loads(TrapezoidalLoadV([-start_mag, -end_mag], [start_loc, end_loc]))
                
                # Add to visual (Orange shaded area)
                max_mag = max(abs(start_mag), abs(end_mag))
                h_start = (start_mag / max_mag) * 0.8 + 0.1 # Scaled for visual fit
                h_end = (end_mag / max_mag) * 0.8 + 0.1
                
                fig_fbd.add_trace(go.Scatter(
                     x=[start_loc, start_loc, end_loc, end_loc],
                     y=[0.05, h_start, h_end, 0.05],
                     fill='toself', fillcolor='rgba(255, 127, 14, 0.3)', line=dict(color='#ff7f0e', width=1.5),
                     name="Dist Load", showlegend=False, hoverinfo="none"
                ))
                fig_fbd.add_annotation(
                    x=(start_loc+end_loc)/2, y=max(h_start, h_end)+0.15, 
                    text=f"{start_mag} to {end_mag} kN/m", showarrow=False, font=dict(color="#ff7f0e", size=11)
                )

    # Add Point Moments to visual and engine
    for _, row in pm_df.iterrows():
        if pd.notna(row["Magnitude (kNm)"]) and pd.notna(row["Location (m)"]):
            if row["Magnitude (kNm)"] != 0:
                mag = float(row["Magnitude (kNm)"])
                loc = float(row["Location (m)"])
                
                # Add to engine
                beam.add_loads(PointTorque(-mag, loc))
                
                # Add to visual (Circular emoji representation)
                dir_text = "↻" if mag > 0 else "↺"
                fig_fbd.add_annotation(
                    x=loc, y=-0.5, text=f"{dir_text} {abs(mag)} kNm", 
                    showarrow=False, font=dict(color="purple", size=16)
                )

    # Format the FBD layout
    fig_fbd.update_yaxes(range=[-1, 1.8], showticklabels=False, showgrid=False, zeroline=False)
    fig_fbd.update_xaxes(range=[-0.5, beam_length + 0.5], title="Beam Length (m)", showgrid=False, zeroline=False)
    fig_fbd.update_layout(height=280, margin=dict(l=20, r=20, t=30, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

    # Render FBD
    st.subheader("Free Body Diagram (Load Placement)")
    st.plotly_chart(fig_fbd, use_container_width=True)
    st.divider()

    # ---------------------------------------------------------
    # SOLVE AND PLOT CHARTS
    # ---------------------------------------------------------
    beam.analyse()

    fig_react = beam.plot_reaction_force()
    fig_shear = beam.plot_shear_force()
    fig_moment = beam.plot_bending_moment()
    
    for fig in [fig_react, fig_shear, fig_moment]:
        fig.update_layout(margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

    st.subheader("Support Reactions")
    st.plotly_chart(fig_react, use_container_width=True)

    col_plot1, col_plot2 = st.columns(2)
    with col_plot1:
        st.subheader("Shear Force Diagram")
        st.plotly_chart(fig_shear, use_container_width=True)
        
    with col_plot2:
        st.subheader("Bending Moment Diagram")
        st.plotly_chart(fig_moment, use_container_width=True)

except Exception as e:
    st.error(f"⚠️ Analysis Error: The structure might be unstable (e.g., missing supports) or inputs are invalid. \n\nDetails: {e}")