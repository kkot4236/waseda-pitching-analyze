import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

# --- パスワード設定 ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = None
    if st.session_state["password_correct"] == True: return True
    def password_entered():
        if st.session_state["password_input"] == "wbc1901":
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
        # リポジトリ内の全フォルダを探索
        for root, dirs, files in os.walk("."):
            for file in files:
                if file.endswith(('.csv', '.xlsx')):
                    path = os.path.join(root, file)
                    try:
                        # CSVとExcel両対応。CSVの場合はエンコーディングを考慮
                        if file.endswith('.xlsx'):
                            df = pd.read_excel(path)
                        else:
                            try:
                                df = pd.read_csv(path, encoding='utf-8')
                            except:
                                df = pd.read_csv(path, encoding='shift-jis')
                        
                        # カラム名の前後の空白を削除
                        df.columns = df.columns.str.strip()
                        
                        # 指定通り Pitcher First Name を表示名に使用
                        if 'Pitcher First Name' in df.columns:
                            df['PitcherDisplay'] = df['Pitcher First Name']
                        elif 'Pitcher' in df.columns:
                            df['PitcherDisplay'] = df['Pitcher']
                        else:
                            df['PitcherDisplay'] = "Unknown"

                        # 数値データの変換
                        num_cols = ['RelSpeed (KMH)', 'InducedVertBreak (CM)', 'HorzBreak (CM)', 'PlateLocSide (CM)', 'PlateLocHeight (CM)', 'SpinRate']
                        for c in num_cols:
                            if c in df.columns:
                                df[c] = pd.to_numeric(df[c], errors='coerce')
                        
                        all_data.append(df)
                    except:
                        continue
        return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

    df = load_data()

    if not df.empty:
        # 投手リストの取得
        pitcher_list = sorted(df['PitcherDisplay'].dropna().unique())
        
        if not pitcher_list or pitcher_list == ["Unknown"]:
            st.warning("データは見つかりましたが、投手名（Pitcher First Name）が空欄のようです。ファイルの中身を確認してください。")
            st.write("見つかったファイル:", df.columns.tolist())
        else:
            pitcher = st.sidebar.selectbox("投手を選択", pitcher_list)
            p_df = df[df['PitcherDisplay'] == pitcher].copy()

            st.header(f"📊 {pitcher} 投球分析レポート")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # 変化量グラフ
                fig, ax = plt.subplots(figsize=(6,6))
                for pt in p_df['Pitch Type'].unique():
                    sub = p_df[p_df['Pitch Type'] == pt]
                    ax.scatter(sub['HorzBreak (CM)'], sub['InducedVertBreak (CM)'], label=pt, color=PITCH_COLORS.get(pt, '#808080'), alpha=0.6)
                ax.axvline(0, color='black', lw=1); ax.axhline(0, color='black', lw=1)
                ax.set_xlim(-80, 80); ax.set_ylim(-80, 80)
                ax.set_title("変化量 (Movement cm)"); ax.set_box_aspect(1)
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
                ax.set_title("投球位置 (Location cm)"); ax.set_box_aspect(1)
                st.pyplot(fig)
            
            st.subheader("📋 球種別平均データ")
            show_cols = ['RelSpeed (KMH)', 'SpinRate', 'InducedVertBreak (CM)', 'HorzBreak (CM)']
            # 存在する列だけを表示
            actual_cols = [c for c in show_cols if c in p_df.columns]
            summary = p_df.groupby('Pitch Type')[actual_cols].mean()
            st.dataframe(summary.style.format(precision=1), use_container_width=True)
    else:
        st.error("ファイルが見つかりません。GitHubの 'data' フォルダにCSVまたはExcelが入っているか確認してください。")
