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
        if st.session_state["password_input"] == "wbc1901":
            st.session_state["password_correct"] = True
        else:
            st.session_state["password_correct"] = False
    st.title("⚾️ 早稲田大学野球部 Rapsodo分析")
    st.text_input("パスワードを入力", type="password", on_change=password_entered, key="password_input")
    return False

if check_password():
    st.set_page_config(layout="wide", page_title="Rapsodo Analysis")

    # 色設定
    PITCH_COLORS = {'FB': '#FF4B4B', 'CB': '#1E90FF', 'SL': '#FF1493', 'CH': '#32CD32', 'SP': '#40E0D0', 'CT': '#8A2BE2', 'SI': '#FFA500'}

    @st.cache_data
    def load_data():
        all_data = []
        # 全てのフォルダとファイルを探索する
        for root, dirs, files in os.walk("."):
            for file in files:
                if file.endswith(('.csv', '.xlsx')):
                    path = os.path.join(root, file)
                    try:
                        # CSVとExcel両方に対応
                        df = pd.read_excel(path) if file.endswith('.xlsx') else pd.read_csv(path)
                        
                        # カラム名のクリーニング（スペース削除など）
                        df.columns = df.columns.str.strip()
                        
                        if 'Pitcher First Name' in df.columns:
                            df['Pitcher'] = df['Pitcher Last Name'] + " " + df['Pitcher First Name']
                        
                        # 数値変換の強制
                        num_cols = ['RelSpeed (KMH)', 'InducedVertBreak (CM)', 'HorzBreak (CM)', 'PlateLocSide (CM)', 'PlateLocHeight (CM)']
                        for c in num_cols:
                            if c in df.columns:
                                df[c] = pd.to_numeric(df[c], errors='coerce')
                        
                        all_data.append(df)
                    except:
                        continue
        return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

    df = load_data()

    if not df.empty:
        # 投手リストの作成（不明な場合はファイル名を表示）
        pitcher_list = sorted(df['Pitcher'].dropna().unique()) if 'Pitcher' in df.columns else []
        if not pitcher_list:
            st.error("投手名データが見つかりません。ファイルの中身を確認してください。")
        else:
            pitcher = st.sidebar.selectbox("投手を選択", pitcher_list)
            p_df = df[df['Pitcher'] == pitcher]

            st.header(f"📊 {pitcher} 投球分析")
            col1, col2 = st.columns(2)
            
            with col1:
                fig, ax = plt.subplots(figsize=(6,6))
                for pt in p_df['Pitch Type'].unique():
                    sub = p_df[p_df['Pitch Type'] == pt]
                    ax.scatter(sub['HorzBreak (CM)'], sub['InducedVertBreak (CM)'], label=pt, color=PITCH_COLORS.get(pt, '#808080'), alpha=0.6)
                ax.axvline(0, color='black'); ax.axhline(0, color='black')
                ax.set_xlim(-80, 80); ax.set_ylim(-80, 80); ax.set_box_aspect(1); ax.set_title("Movement (cm)")
                ax.legend()
                st.pyplot(fig)

            with col2:
                fig, ax = plt.subplots(figsize=(6,6))
                ax.add_patch(plt.Rectangle((-25, 45), 50, 60, fill=False, lw=2)) # Strike Zone
                for pt in p_df['Pitch Type'].unique():
                    sub = p_df[p_df['Pitch Type'] == pt]
                    ax.scatter(sub['PlateLocSide (CM)'], sub['PlateLocHeight (CM)'], color=PITCH_COLORS.get(pt, '#808080'), alpha=0.6)
                ax.set_xlim(-100, 100); ax.set_ylim(0, 200); ax.set_box_aspect(1); ax.set_title("Location (cm)")
                st.pyplot(fig)
            
            st.subheader("平均データ")
            # 利用可能なカラムだけで集計
            show_cols = [c for c in ['RelSpeed (KMH)', 'SpinRate', 'InducedVertBreak (CM)', 'HorzBreak (CM)'] if c in p_df.columns]
            st.dataframe(p_df.groupby('Pitch Type')[show_cols].mean().style.format(precision=1))
    else:
        st.error("ファイルが1つも見つかりません。GitHubにデータがアップロードされているか確認してください。")
