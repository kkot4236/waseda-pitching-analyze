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
        if st.session_state.get("password_input") == "wbc1901":
            st.session_state["password_correct"] = True
        else:
            st.session_state["password_correct"] = False

    st.title("⚾️ 早稲田大学野球部 投手分析システム")
    st.text_input("パスワードを入力", type="password", on_change=password_entered, key="password_input")
    return False

if check_password():
    st.set_page_config(layout="wide", page_title="Waseda Pitching Analyze")

    # --- デザインCSS（シンプル版） ---
    st.markdown("""
        <style>
        .feedback-table { margin: auto; border-collapse: collapse; width: 100%; border: 1px solid #333; }
        .feedback-table th { background-color: #1e3a8a !important; color: white !important; padding: 12px; text-align: center !important; }
        .feedback-table td { padding: 10px; border: 1px solid #ccc; text-align: center !important; font-size: 16px; }
        </style>
    """, unsafe_allow_html=True)

    @st.cache_data
    def load_data():
        all_data = []
        data_dir = "data"
        if os.path.exists(data_dir):
            for file in os.listdir(data_dir):
                if file.endswith(('.csv', '.xlsx')):
                    path = os.path.join(data_dir, file)
                    try:
                        df = pd.read_excel(path) if file.endswith('.xlsx') else pd.read_csv(path)
                        df.columns = df.columns.str.strip()
                        
                        # --- 指定された正確な項目名に固定 ---
                        if 'Pitcher First Name' in df.columns: df['Player'] = df['Pitcher First Name']
                        if 'Pitch Created At' in df.columns: df['Date'] = pd.to_datetime(df['Pitch Created At']).dt.date
                        if 'RelSpeed (KMH)' in df.columns: df['Velo'] = pd.to_numeric(df['RelSpeed (KMH)'], errors='coerce')
                        if 'Spin Rate' in df.columns: df['Spin'] = pd.to_numeric(df['Spin Rate'], errors='coerce')

                        # 必要なデータが揃っている場合のみ採用
                        if 'Player' in df.columns and 'Velo' in df.columns:
                            all_data.append(df.dropna(subset=['Player', 'Velo']))
                    except: continue
        return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

    df = load_data()

    if not df.empty:
        mode = st.sidebar.radio("メニュー", ["チーム全体分析", "個人詳細分析"])

        if mode == "チーム全体分析":
            st.header("📊 投手 球速ランキング")
            all_dates = sorted(df['Date'].unique(), reverse=True)
            selected_dates = st.multiselect("日付を選択", all_dates, default=[all_dates[0]])
            
            if selected_dates:
                curr_df = df[df['Date'].isin(selected_dates)]
                summary = curr_df.groupby('Player').agg({'Velo': ['mean', 'max'], 'Spin': 'mean'})
                summary.columns = ['平均球速', 'MAX球速', '平均回転数']
                display_df = summary.sort_values('MAX球速', ascending=False).reset_index()

                st.write(display_df.to_html(classes='feedback-table', index=False, float_format='%.1f'), unsafe_allow_html=True)

        else:
            player = st.sidebar.selectbox("投手を選択", sorted(df['Player'].unique()))
            st.header(f"👤 {player} 分析")
            
            full_p_df = df[df['Player'] == player].copy()
            
            # 個人分析でも全期間か日付選択か選べるように追加
            analysis_scope = st.radio("分析範囲", ["全期間（総合）", "特定の日付を選択"], horizontal=True)
            if analysis_scope == "特定の日付を選択":
                p_dates = sorted(full_p_df['Date'].unique(), reverse=True)
                sel_p_dates = st.multiselect("日付を選択してください", p_dates, default=[p_dates[0]])
                p_df = full_p_df[full_p_df['Date'].isin(sel_p_dates)]
            else:
                p_df = full_p_df

            c1, c2, c3 = st.columns(3)
            c1.metric("MAX球速", f"{p_df['Velo'].max():.1f} km/h")
            c2.metric("平均球速", f"{p_df['Velo'].mean():.1f} km/h")
            c3.metric("平均回転数", f"{int(p_df['Spin'].mean()) if 'Spin' in p_df.columns else 0} rpm")

            st.subheader("📈 球速推移（通算）")
            trend = full_p_df.groupby('Date')['Velo'].agg(['mean', 'max']).reset_index()
            fig = px.line(trend, x='Date', y=['mean', 'max'], markers=True)
            fig.update_layout(yaxis_range=[125, 160]) # 縦軸を125-160に固定
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("📋 投球履歴")
            hist_cols = [c for c in ['Date', 'Velo', 'Spin'] if c in p_df.columns]
            hist = p_df[hist_cols].sort_values(['Date', 'Velo'], ascending=[False, False])
            st.write(hist.to_html(classes='feedback-table', index=False, float_format='%.1f'), unsafe_allow_html=True)
    else:
        st.warning("⚠️ データが読み込めませんでした。'data'フォルダのCSV内に 'Pitcher First Name', 'Pitch Created At', 'RelSpeed (KMH)' という項目があるか確認してください。")
