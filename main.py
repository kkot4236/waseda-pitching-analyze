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

    PITCH_COLORS = {
        'FB': '#FF4B4B', 'CB': '#1E90FF', 'SL': '#FF1493', 
        'CH': '#32CD32', 'SP': '#40E0D0', 'CT': '#8A2BE2', 
        'SI': '#FFA500', 'OTH': '#808080'
    }

    @st.cache_data
    def load_data():
        all_data = []
        for root, dirs, files in os.walk("."):
            for file in files:
                if file.endswith(('.csv', '.xlsx')):
                    path = os.path.join(root, file)
                    try:
                        if file.endswith('.xlsx'):
                            df = pd.read_excel(path)
                        else:
                            try:
                                df = pd.read_csv(path, encoding='utf-8')
                            except:
                                df = pd.read_csv(path, encoding='shift-jis')
                        
                        df.columns = df.columns.str.strip()
                        
                        # 日付の抽出 (Pitch Created At から yyyy-mm-dd を作成)
                        if 'Pitch Created At' in df.columns:
                            df['Date'] = pd.to_datetime(df['Pitch Created At']).dt.strftime('%Y-%m-%d')
                        else:
                            df['Date'] = "Unknown Date"

                        # 投手名の設定
                        if 'Pitcher First Name' in df.columns:
                            df['PitcherDisplay'] = df['Pitcher First Name']
                        else:
                            df['PitcherDisplay'] = "Unknown"

                        # ストライク判定
                        if 'Is Strike' in df.columns:
                            df['is_strike_bool'] = df['Is Strike'].map({'Y': True, 'N': False})
                        
                        # 数値変換
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
        # --- サイドバー操作 ---
        st.sidebar.header("検索フィルター")
        
        # 1. 日付を選択 (降順：新しい日付が上)
        date_list = sorted(df['Date'].unique(), reverse=True)
        selected_date = st.sidebar.selectbox("日付を選択", date_list)
        
        # 日付で絞り込み
        date_filtered_df = df[df['Date'] == selected_date]
        
        # 2. その日に投げた投手のみを選択肢に出す
        pitcher_list = sorted(date_filtered_df['PitcherDisplay'].dropna().unique())
        
        if not pitcher_list:
            st.warning(f"{selected_date} のデータに投手名が見つかりません。")
        else:
            selected_pitcher = st.sidebar.selectbox("投手を選択", pitcher_list)
            p_df = date_filtered_df[date_filtered_df['PitcherDisplay'] == selected_pitcher].copy()

            # --- メイン画面 ---
            st.header(f"📊 {selected_pitcher} 投球分析 ({selected_date})")
            
            col1, col2 = st.columns(2)
            
            with col1:
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
                fig, ax = plt.subplots(figsize=(6,6))
                ax.add_patch(plt.Rectangle((-25, 45), 50, 60, fill=False, lw=2, color='black'))
                for pt in p_df['Pitch Type'].unique():
                    sub = p_df[p_df['Pitch Type'] == pt]
                    ax.scatter(sub['PlateLocSide (CM)'], sub['PlateLocHeight (CM)'], color=PITCH_COLORS.get(pt, '#808080'), alpha=0.6)
                ax.set_xlim(-100, 100); ax.set_ylim(0, 200)
                ax.set_title("投球位置 (Location cm)"); ax.set_box_aspect(1)
                st.pyplot(fig)
            
            # --- 集計表 ---
            st.subheader("📋 球種別平均データ")
            
            # 必要なカラムの存在確認
            summary_cols = {'RelSpeed (KMH)': '平均球速', 'SpinRate': '回転数', 'InducedVertBreak (CM)': '縦変化', 'HorzBreak (CM)': '横変化'}
            agg_dict = {col: 'mean' for col in summary_cols.keys() if col in p_df.columns}
            if 'is_strike_bool' in p_df.columns:
                agg_dict['is_strike_bool'] = 'mean'
            
            summary = p_df.groupby('Pitch Type').agg(agg_dict)
            
            if 'is_strike_bool' in summary.columns:
                summary['Strike %'] = summary['is_strike_bool'] * 100
                summary = summary.drop(columns=['is_strike_bool'])
            
            summary = summary.rename(columns=summary_cols)
            st.dataframe(summary.style.format(precision=1), use_container_width=True)
    else:
        st.error("ファイルが見つかりません。")
