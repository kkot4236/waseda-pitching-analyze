import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

# パスワード設定
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = None
    if st.session_state["password_correct"] == True: return True
    def password_entered():
        if st.session_state["password_input"] == "waseda123":
            st.session_state["password_correct"] = True
        else:
            st.session_state["password_correct"] = False
    st.title("⚾️ 早稲田大学野球部 Rapsodo分析")
    st.text_input("パスワードを入力", type="password", on_change=password_entered, key="password_input")
    return False

if check_password():
    st.set_page_config(layout="wide", page_title="Rapsodo Analysis")

    # 球種ごとの色設定
    PITCH_COLORS = {
        'FB': '#FF4B4B', 'CB': '#1E90FF', 'SL': '#FF1493', 
        'CH': '#32CD32', 'SP': '#40E0D0', 'CT': '#8A2BE2', 
        'SI': '#FFA500', 'OTH': '#808080'
    }

    @st.cache_data
    def load_data():
        all_data = []
        # dataフォルダおよびルートディレクトリからファイルを探す
        search_dirs = ["data", "Data", "."]
        for s_dir in search_dirs:
            if os.path.exists(s_dir):
                files = [f for f in os.listdir(s_dir) if f.endswith(('.csv', '.xlsx'))]
                for f in files:
                    path = os.path.join(s_dir, f)
                    try:
                        # CSVとExcel両方に対応
                        df = pd.read_excel(path) if f.endswith('.xlsx') else pd.read_csv(path)
                        
                        # 列名の前後の空白を削除
                        df.columns = df.columns.str.strip()
                        
                        # 投手名を「苗字 名前」で作成
                        if 'Pitcher Last Name' in df.columns and 'Pitcher First Name' in df.columns:
                            df['Pitcher'] = df['Pitcher Last Name'] + " " + df['Pitcher First Name']
                        elif 'Pitcher' not in df.columns:
                            df['Pitcher'] = "Unknown Player"
                        
                        # 数値変換（エラーはNaNにする）
                        num_cols = ['RelSpeed (KMH)', 'InducedVertBreak (CM)', 'HorzBreak (CM)', 'PlateLocSide (CM)', 'PlateLocHeight (CM)', 'SpinRate']
                        for c in num_cols:
                            if c in df.columns:
                                df[c] = pd.to_numeric(df[c], errors='coerce')
                        
                        all_data.append(df)
                    except:
                        continue
        
        if all_data:
            return pd.concat(all_data, ignore_index=True)
        return pd.DataFrame()

    df = load_data()

    if not df.empty:
        # 投手選択
        pitcher_list = sorted(df['Pitcher'].dropna().unique())
        pitcher = st.sidebar.selectbox("投手を選択", pitcher_list)
        p_df = df[df['Pitcher'] == pitcher].copy()

        st.header(f"📊 {pitcher} 投球分析")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 変化量グラフ
            fig, ax = plt.subplots(figsize=(6,6))
            for pt in p_df['Pitch Type'].unique():
                sub = p_df[p_df['Pitch Type'] == pt]
                ax.scatter(sub['HorzBreak (CM)'], sub['InducedVertBreak (CM)'], label=pt, color=PITCH_COLORS.get(pt, '#808080'), alpha=0.6)
            ax.axvline(0, color='black', lw=1); ax.axhline(0, color='black', lw=1)
            ax.set_xlim(-80, 80); ax.set_ylim(-80, 80)
            ax.set_title("変化量 (cm)"); ax.set_box_aspect(1)
            ax.legend(loc='upper right')
            st.pyplot(fig)

        with col2:
            # 投球位置グラフ
            fig, ax = plt.subplots(figsize=(6,6))
            # ストライクゾーンの枠
            ax.add_patch(plt.Rectangle((-25, 45), 50, 60, fill=False, lw=2, color='black'))
            for pt in p_df['Pitch Type'].unique():
                sub = p_df[p_df['Pitch Type'] == pt]
                ax.scatter(sub['PlateLocSide (CM)'], sub['PlateLocHeight (CM)'], color=PITCH_COLORS.get(pt, '#808080'), alpha=0.6)
            ax.set_xlim(-100, 100); ax.set_ylim(0, 200)
            ax.set_title("投球位置 (cm)"); ax.set_box_aspect(1)
            st.pyplot(fig)
        
        # 集計表
        st.subheader("種別平均データ")
        stats_cols = [c for c in ['RelSpeed (KMH)', 'SpinRate', 'InducedVertBreak (CM)', 'HorzBreak (CM)'] if c in p_df.columns]
        if stats_cols:
            summary = p_df.groupby('Pitch Type')[stats_cols].mean()
            st.dataframe(summary.style.format(precision=1), use_container_width=True)
    else:
        st.error("データが読み込めませんでした。GitHubのファイル名や列名を確認してください。")
        st.info("現在探している列名: Pitcher Last Name, Pitcher First Name, RelSpeed (KMH) など")
