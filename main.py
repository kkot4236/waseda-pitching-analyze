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
        # 安全にセッション状態を確認・更新
        pw = st.session_state.get("password_input", "")
        if pw == "wbc1901":
            st.session_state["password_correct"] = True
        else:
            st.session_state["password_correct"] = False

    st.title("⚾️ 早稲田大学野球部 投手分析システム")
    st.text_input("パスワードを入力", type="password", on_change=password_entered, key="password_input")
    
    if st.session_state.get("password_correct") == False:
        st.error("パスワードが違います")
    return False

if check_password():
    st.set_page_config(layout="wide", page_title="Waseda Pitching Analyze")

    # --- デザインCSS ---
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
                        
                        # --- 指定された項目名で抽出 ---
                        # 名前
                        if 'Pitcher First Name' in df.columns:
                            df['Player'] = df['Pitcher First Name']
                        
                        # 日付（エラーになる値を強制的に削除）
                        if 'Pitch Created At' in df.columns:
                            df['Date'] = pd.to_datetime(df['Pitch Created At'], errors='coerce').dt.date
                        
                        # 球速
                        if 'RelSpeed (KMH)' in df.columns:
                            df['Velo'] = pd.to_numeric(df['RelSpeed (KMH)'], errors='coerce')
                        
                        # 回転数
                        if 'Spin Rate' in df.columns:
                            df['Spin'] = pd.to_numeric(df['Spin Rate'], errors='coerce')

                        # Player, Date, Velo が揃っていて、かつ不正値でない行だけ残す
                        df = df.dropna(subset=['Player', 'Date', 'Velo'])
                        if not df.empty:
                            all_data.append(df)
                    except: continue
        
        if not all_data:
            return pd.DataFrame()
        return pd.concat(all_data, ignore_index=True)

    df = load_data()

    if not df.empty:
        mode = st.sidebar.radio("メニュー", ["チーム全体分析", "個人詳細分析"])

        if mode == "チーム全体分析":
            st.header("📊 投手 球速ランキング")
            # 日付リスト作成時に None を排除してソート
            all_dates = sorted([d for d in df['Date'].unique() if d is not None], reverse=True)
            
            if all_dates:
                selected_dates = st.multiselect("日付を選択", all_dates, default=[all_dates[0]])
                
                if selected_dates:
                    curr_df = df[df['Date'].isin(selected_dates)]
                    # 回転数がある場合とない場合で集計を変える
                    agg_cols = {'Velo': ['mean', 'max']}
                    if 'Spin' in curr_df.columns:
                        agg_cols['Spin'] = 'mean'
                    
                    summary = curr_df.groupby('Player').agg(agg_cols)
                    
                    # カラム名の整理
                    summary.columns = ['平均球速', 'MAX球速'] + (['平均回転数'] if 'Spin' in agg_cols else [])
                    display_df = summary.sort_values('MAX球速', ascending=False).reset_index()

                    st.write(display_df.to_html(classes='feedback-table', index=False, float_format='%.1f'), unsafe_allow_html=True)
            else:
                st.info("有効な日付データがありません。")

        else:
            player = st.sidebar.selectbox("投手を選択", sorted(df['Player'].unique()))
            st.header(f"👤 {player} 分析")
            full_p_df = df[df['Player'] == player].copy()
            
            analysis_scope = st.radio("分析範囲", ["全期間（総合）", "特定の日付を選択"], horizontal=True)
            if analysis_scope == "特定の日付を選択":
                p_dates = sorted([d for d in full_p_df['Date'].unique() if d is not None], reverse=True)
                sel_p_dates = st.multiselect("日付を選択してください", p_dates, default=[p_dates[0]])
                p_df = full_p_df[full_p_df['Date'].isin(sel_p_dates)]
            else:
                p_df = full_p_df

            if not p_df.empty:
                c1, c2, c3 = st.columns(3)
                c1.metric("MAX球速", f"{p_df['Velo'].max():.1f} km/h")
                c2.metric("平均球速", f"{p_df['Velo'].mean():.1f} km/h")
                spin_val = p_df['Spin'].mean() if 'Spin' in p_df.columns else 0
                c3.metric("平均回転数", f"{int(spin_val)} rpm")

                st.subheader("📈 球速推移（通算）")
                trend = full_p_df.groupby('Date')['Velo'].agg(['mean', 'max']).reset_index()
                fig = px.line(trend, x='Date', y=['mean', 'max'], markers=True)
                fig.update_layout(yaxis_range=[125, 160])
                st.plotly_chart(fig, use_container_width=True)

                st.subheader("📋 投球履歴")
                hist_cols = [c for c in ['Date', 'Velo', 'Spin'] if c in p_df.columns]
                hist = p_df[hist_cols].sort_values(['Date', 'Velo'], ascending=[False, False])
                st.write(hist.to_html(classes='feedback-table', index=False, float_format='%.1f'), unsafe_allow_html=True)
    else:
        st.warning("⚠️ 有効な投手データが見つかりません。")
        st.info("CSVの項目名を確認してください:\n- Pitcher First Name\n- Pitch Created At\n- RelSpeed (KMH)")
