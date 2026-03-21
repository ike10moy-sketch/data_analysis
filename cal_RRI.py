import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="Data Analyzer", layout="wide")
st.title("📊 CSV Analyzer: Combined Variability Index")

# 1. File Uploader
uploaded_file = st.file_uploader("Upload CSV file", type=['csv'])

if uploaded_file is not None:
    # 2. Load Data
    try:
        df = pd.read_csv(uploaded_file, sep=None, engine='python')
    except Exception as e:
        st.error(f"Error loading file: {e}")
        st.stop()

    if len(df.columns) < 3:
        st.error("The CSV must have at least 3 columns.")
        st.stop()

    # Extract columns (1st and 3rd)
    x_raw = df.iloc[:, 0]
    y_raw = df.iloc[:, 2]

    # --- Calculations ---
    # Amplitude = (Odd Row Y) - (Next Even Row Y)
    y_odd_rows = y_raw.iloc[0::2].reset_index(drop=True)
    y_even_rows = y_raw.iloc[1::2].reset_index(drop=True)
    min_len_amp = min(len(y_odd_rows), len(y_even_rows))
    amplitude = y_odd_rows[:min_len_amp] - y_even_rows[:min_len_amp]

    # Period = (Next Odd Row X) - (Current Odd Row X)
    x_odd_rows = x_raw.iloc[0::2].reset_index(drop=True)
    period = x_odd_rows.diff().dropna().reset_index(drop=True)

    # --- Statistics Calculation ---
    # Amplitude Stats
    amp_mean = amplitude.mean()
    amp_std = amplitude.std()
    amp_v = (amp_std / amp_mean * 100) if amp_mean != 0 else 0

    # Period Stats
    per_mean = period.mean()
    per_std = period.std()
    per_v = (per_std / per_mean * 100) if per_mean != 0 else 0

    # Combined Metric: log10( (CV_amp * 100) * (CV_period * 100) )
    product_v = amp_v * per_v
    combined_log_metric = np.log10(product_v) if product_v > 0 else 0

    # --- UI Display ---
    
    # Large Metric Display
    st.subheader("Combined Metric")
    st.metric(label="log10( (Amp SD/M * 100) * (Period SD/M * 100) )", value=f"{combined_log_metric:.4f}")

    # Summary Table
    st.subheader("📈 Detailed Statistics")
    stats_data = {
        "Feature": ["Amplitude", "Period"],
        "Mean": [f"{amp_mean:.4f}", f"{per_mean:.4f}"],
        "Std Deviation (SD)": [f"{amp_std:.4f}", f"{per_std:.4f}"],
        "CV * 100 (V)": [f"{amp_v:.4f}", f"{per_v:.4f}"]
    }
    st.table(pd.DataFrame(stats_data))

    # --- Visualizations ---
    st.divider()
    st.subheader("Visualizations")
    
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12))
    
    # 1. Raw Data Plot
    ax1.plot(x_raw, y_raw, marker='o', linestyle='-', color='gray', alpha=0.4)
    ax1.set_title("Original Data (Col 1 vs Col 3)")
    ax1.grid(True)

    # 2. Amplitude Plot
    ax2.plot(amplitude, marker='s', color='blue')
    ax2.axhline(amp_mean, color='red', linestyle='--')
    ax2.set_title(f"Amplitude (V_amp: {amp_v:.4f})")
    ax2.grid(True)

    # 3. Period Plot
    ax3.plot(period, marker='^', color='green')
    ax3.axhline(per_mean, color='red', linestyle='--')
    ax3.set_title(f"Period (V_per: {per_v:.4f})")
    ax3.grid(True)

    plt.tight_layout()
    st.pyplot(fig)

    # Data Values Preview
    with st.expander("View processed data values"):
        col_v1, col_v2 = st.columns(2)
        col_v1.write("Amplitude")
        col_v1.dataframe(amplitude)
        col_v2.write("Period")
        col_v2.dataframe(period)

else:
    st.info("Please upload a CSV file.")
