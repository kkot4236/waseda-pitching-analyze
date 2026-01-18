import streamlit as st
import pandas as pd
import os
import plotly.express as px

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
    st.title("⚾️ 早稲田大学野球部 投手分析システム")
    st.text_input("パスワードを入力", type="password", on_change=password_entered, key="pitcher_password_input")
    return False

if check_password():
    # --- 投手用デザインCSS ---
    st.markdown("""
        <style>
        .pitcher-table { margin: auto; border-collapse: collapse; width: 100%; border: 1px solid #333; }
        .pitcher-table th { background-color: #1e3a8a !important; color: white !important; padding: 10px; text-align: center !important; }
        .pitcher-table td { padding: 8px; border: 1px solid #ccc; text-align: center !important; }
        </style>
    """, unsafe_allow_html=True)

    @st.cache_data
    def load_pitcher_data():
        all_data = []
        for root, dirs, files in os.walk("."):
            for file in files:
                if file.endswith(('.csv', '.xlsx')):
                    path = os.path.join(root, file)
                    try:
                        df = pd.read_excel(path) if file.endswith('.xlsx') else pd.read_csv(path)
                        df.columns = df.columns.str.strip()
                        
                        # 投手用カラム名のマッピング (Rapsodo/Trackman対応)
                        name_map = {'Pitcher First Name': 'Player', 'Pitcher': 'Player', 'Last Name': 'Player'}
                        for old, new in name_map.items():
                            if old in df.columns: df['Player'] = df[old]
                        
                        date_map = {'Pitch Created At': 'Date', 'Date': 'Date', 'Time': 'Date'}
                        for old, new in date_map.items():
                            if old in df.columns: df['Date'] = pd.to_datetime(df[old]).dt.date
                        
                        # 投球データの数値化
                        val_cols = {'Velocity (KMH)': 'Velo', 'ReleaseSpeed': 'Velo', 'Spin Rate': 'Spin', 'SpinRate': 'Spin'}
                        for old, new in val_cols.items():
                            if old in df.columns: df[new] = pd.to_numeric(df[old], errors='coerce')
                        
                        if 'Player' in df.columns and ('Velo' in df.columns or 'Spin' in df.columns):
                            all_data.append(df.dropna(subset=['Player']))
                    except: continue
        return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

    df_p = load_pitcher_data()

    if not df_p.empty:
        # メニュー
        p_list = sorted(df_p['Player'].unique())
        selected_p = st.sidebar.selectbox("投手を選択", p_list)
        p_df = df_p[df_p['Player'] == selected_p].copy()
        
        st.header(f"Pitching Analysis: {selected_p}")

        # 指標表示
        c1, c2, c3 = st.columns(3)
        if 'Velo' in p_df.columns:
            c1.metric("MAX速度", f"{p_df['Velo'].max():.1f} km/h")
            c2.metric("平均速度", f"{p_df['Velo'].mean():.1f} km/h")
        if 'Spin' in p_df.columns:
            c3.metric("平均回転数", f"{int(p_df['Spin'].mean())} rpm")

        # 速度推移グラフ
        if 'Velo' in p_df.columns:
            st.subheader("📈 球速推移")
            trend = p_df.groupby('Date')['Velo'].agg(['mean', 'max']).reset_index()
            fig = px.line(trend, x='Date', y=['mean', 'max'], markers=True)
            # 投手用は 110 ~ 160 くらいで固定が見やすいかもしれません
            fig.update_layout(yaxis_range=[110, 160])
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("📋 投球詳細履歴")
        cols_to_show = [c for c in ['Date', 'Velo', 'Spin', 'PitchType'] if c in p_df.columns]
        st.write(p_df[cols_to_show].sort_values('Date', ascending=False).to_html(classes='pitcher-table', index=False, float_format='%.1f'), unsafe_allow_html=True)
    else:
        st.error("投手データが見つかりません。CSVのカラム名を確認してください。")
