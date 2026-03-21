import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from scipy.signal import find_peaks
import numpy as np

# ページ設定
st.set_page_config(page_title="ピーク・ボトム解析エディタ", layout="wide")

st.title("📈 測定データ解析エディタ (10Hz対応)")
st.write("TXTデータを読み込み、検出されたピークを編集します。🔴＝極大、🔵＝極小。時間は小数点1桁で出力します。")

# サイドバー設定
st.sidebar.header("1. 解析パラメータ")
hz = st.sidebar.number_input("サンプリング周波数 (Hz)", value=10.0, step=1.0)
prom_val = st.sidebar.slider("自動検出の感度 (プロミネンス)", 0.0, 5.0, 0.2, step=0.01)

# 1. ファイルアップロード
uploaded_file = st.file_uploader("1列の数値データが入ったTXTファイルを選択してください", type=['txt'])

if uploaded_file is not None:
    try:
        # 2. データの読み込み
        df_raw = pd.read_csv(uploaded_file, header=None, sep='\s+')
        y_values = pd.to_numeric(df_raw.iloc[:, 0], errors='coerce').dropna().values
        
        # 時間軸の計算 (10Hz = 0.1s step)
        # 浮動小数点の誤差を防ぐため、計算後に小数点第1位で丸める
        time_step = 1.0 / hz
        time_seconds = np.round(np.arange(len(y_values)) * time_step, 1)

        # 3. 自動検出 (Y軸の値のみで判断)
        peaks_idx, _ = find_peaks(y_values, prominence=prom_val)
        valleys_idx, _ = find_peaks(-y_values, prominence=prom_val)

        # 全ピークをまとめてデータフレーム化
        df_peaks = pd.DataFrame({
            "採用": True,
            "判定": "🔴 極大値 (山)",
            "時間[s]": time_seconds[peaks_idx],
            "値": y_values[peaks_idx],
            "type": "peak"
        })
        df_valleys = pd.DataFrame({
            "採用": True,
            "判定": "🔵 極小値 (谷)",
            "時間[s]": time_seconds[valleys_idx],
            "値": y_values[valleys_idx],
            "type": "valley"
        })
        
        # 時系列に並べ替え
        df_combined = pd.concat([df_peaks, df_valleys]).sort_values("時間[s]").reset_index(drop=True)

        # 4. データエディタで手動選別
        st.subheader("📋 検出リストの編集")
        st.info("不要なデータの「採用」チェックを外してください。")
        
        edited_df = st.data_editor(
            df_combined,
            column_config={
                "採用": st.column_config.CheckboxColumn("採用", default=True),
                "判定": st.column_config.TextColumn("判定 (種別)"),
                "時間[s]": st.column_config.NumberColumn("発生時間", format="%.1f s"), # 表示も小数点1桁
                "値": st.column_config.NumberColumn("Y軸の値", format="%.3f"),
                "type": None 
            },
            disabled=["判定", "時間[s]", "値"],
            hide_index=True,
            use_container_width=True
        )

        # 有効なデータのみを抽出
        df_final = edited_df[edited_df["採用"] == True]

        # 5. グラフ作成
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=time_seconds, y=y_values,
            mode='lines', name='測定波形',
            line=dict(color='lightgray', width=1),
            opacity=0.5,
            hoverinfo='skip'
        ))

        # 採用された山
        f_peaks = df_final[df_final["type"] == "peak"]
        fig.add_trace(go.Scatter(
            x=f_peaks["時間[s]"], y=f_peaks["値"],
            mode='markers+text', name='採用: 山',
            marker=dict(color='red', size=10, symbol='triangle-up'),
            text=[f"{v:.2f}" for v in f_peaks["値"]],
            textposition="top center"
        ))

        # 採用された谷
        f_valleys = df_final[df_final["type"] == "valley"]
        fig.add_trace(go.Scatter(
            x=f_valleys["時間[s]"], y=f_valleys["値"],
            mode='markers+text', name='採用: 谷',
            marker=dict(color='blue', size=10, symbol='triangle-down'),
            text=[f"{v:.2f}" for v in f_valleys["値"]],
            textposition="bottom center"
        ))

        fig.update_layout(
            title="解析結果グラフ（編集反映済み）",
            xaxis_title="時間 [秒]", yaxis_title="測定値",
            template="plotly_white", height=500,
            hovermode="x unified"
        )

        st.plotly_chart(fig, use_container_width=True)

        # 6. 保存処理
        st.subheader("📥 解析結果の出力")
        
        # 出力用のデータフレームを作成
        save_df = df_final[["時間[s]", "判定", "値"]].copy()
        
        # 判定からアイコンを除去
        save_df["判定"] = save_df["判定"].str.replace("🔴 ", "").str.replace("🔵 ", "")
        
        # 【重要】時間を小数点1桁の文字列に書式設定
        save_df["時間[s]"] = save_df["時間[s]"].map(lambda x: f"{x:.1f}")
        
        csv = save_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="編集後のリストをCSVで保存",
            data=csv,
            file_name="peak_analysis_final.csv",
            mime="text/csv",
        )

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
else:
    st.info("TXTファイルをアップロードしてください。")
