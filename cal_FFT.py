import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="時系列データ & FFT解析・出力ツール", layout="wide")

st.title("📈 時系列データ & FFT解析 (10Hz)")
st.write("`.txt` ファイルをアップロードして解析し、結果をCSVでダウンロードできます。")

# サイドバー設定
st.sidebar.header("設定")
sampling_rate = st.sidebar.number_input("サンプリング周波数 (Hz)", value=10.0, step=1.0)
interval = 1.0 / sampling_rate

# ファイルアップローダー
uploaded_file = st.file_uploader("txtファイルを選択してください", type=["txt"])

if uploaded_file is not None:
    try:
        # 1. データの読み込み
        # 1列の数値データを想定
        data = pd.read_csv(uploaded_file, header=None, names=['Value'])['Value'].values
        n = len(data)
        
        if n < 2:
            st.error("データ数が少なすぎます。解析には少なくとも2点以上のデータが必要です。")
        else:
            # 時間軸の作成
            times = np.arange(n) * interval
            df_time = pd.DataFrame({'Time [s]': times, 'Value': data})

            # --- A. 時系列グラフの表示 ---
            st.subheader("1. 時間領域のデータ (Time Domain)")
            fig_time = px.line(df_time, x='Time [s]', y='Value', title="Original Time Series Signal")
            st.plotly_chart(fig_time, use_container_width=True)

            # --- B. FFT (高速フーリエ変換) の計算 ---
            # 実数FFTを実行
            fft_vals = np.fft.rfft(data)
            fft_freq = np.fft.rfftfreq(n, d=interval)
            
            # 振幅スペクトルの計算と正規化
            amplitude = np.abs(fft_vals) / (n / 2)
            amplitude[0] = amplitude[0] / 2 # 直流分(0Hz)の補正

            # FFT結果をDataFrameにまとめる
            df_fft = pd.DataFrame({
                'Frequency [Hz]': fft_freq,
                'Amplitude': amplitude
            })

            # --- C. FFTグラフの表示 ---
            st.subheader("2. 周波数領域のデータ (Frequency Domain)")
            
            # スライダーで表示範囲を絞れるようにする
            max_freq_limit = sampling_rate / 2
            display_freq = st.slider("表示する最大周波数 (Hz)", 0.0, max_freq_limit, max_freq_limit)
            df_fft_filtered = df_fft[df_fft['Frequency [Hz]'] <= display_freq]

            fig_fft = px.line(df_fft_filtered, x='Frequency [Hz]', y='Amplitude', 
                              title="FFT Amplitude Spectrum",
                              labels={'Amplitude': '振幅', 'Frequency [Hz]': '周波数 (Hz)'})
            st.plotly_chart(fig_fft, use_container_width=True)

            # --- D. FFT結果のダウンロード機能 ---
            st.subheader("3. 解析結果のダウンロード")
            
            # CSV形式に変換
            csv_data = df_fft.to_csv(index=False).encode('utf-8')

            st.download_button(
                label="FFT解析結果をCSVでダウンロード",
                data=csv_data,
                file_name='fft_analysis_results.csv',
                mime='text/csv',
            )

            # 補足：ピーク周波数の表示
            peak_idx = np.argmax(amplitude[1:]) + 1 # 0Hzを除外した最大値
            st.info(f"💡 最も強い周波数成分（ピーク）: **{fft_freq[peak_idx]:.3f} Hz**")

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
else:
    st.info("左側の「Browse files」から .txt ファイルをアップロードしてください。")
