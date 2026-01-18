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
    st.text_input("パスワードを入力", type="password", on_change=password_entered, key="password_input")
    return False

if check_password():
    st.set_page_config(layout="wide", page_title="Waseda Pitching Analyze")

    # --- デザインの定義 (CSS) ---
    st.markdown("""
        <style>
        .feedback-table {
            margin: auto;
            border-collapse: collapse;
            width: 100%;
            font-family: sans-serif;
            border: 1px solid #333;
        }
        .feedback-table th {
            background-color: #1e3a8a !important; /* 投手用は少し濃い青にしています */
            color: white !important;
            padding: 12px;
            border: 1px solid #333;
            text-align: center !important;
        }
        .feedback-table td {
            padding: 10px;
            border: 1px solid #ccc;
            text-align: center !important;
            font-size: 16px;
        }
        /* 145km/h以上などの色分け用 */
        .v-high { background-color: #ff4b4b !important; color: white !important; font-weight: bold; }
        .high { background-color: #ffcccc !important; color: #b30000 !important; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)

    @st.cache_data
    def load_data():
        all_data = []
        for root, dirs, files in os.walk("."):
            for file in files:
                if file.endswith(('.csv', '.xlsx')):
                    path = os.path.join(root, file)
                    try:
                        df = pd.read_excel(path) if file.endswith('.xlsx') else pd.read_csv(path)
                        df.columns = df.columns.str.strip()
                        
                        # 投手用カラム名のマッピング (Rapsodo/Trackman)
                        if 'Pitcher First Name' in df.columns: df['Player'] = df['Pitcher First Name']
                        elif 'Pitcher' in df.columns: df['Player'] = df['Pitcher']
                        
                        if 'Pitch Created At' in df.columns: df['Date'] = pd.to_datetime(df['Pitch Created At']).dt.date
                        elif 'Date' in df.columns: df['Date'] = pd.to_datetime(df['Date']).dt.date
                        
                        # 球速と回転数の取得 (エラーが出ないよう get を使用)
                        df['Velo'] = pd.to_numeric(df.get('Velocity (KMH)', df.get('ReleaseSpeed', 0)), errors='coerce')
                        df['Spin'] = pd.to_numeric(df.get('SpinRate', df.get('Spin Rate', 0)), errors='coerce')
                        
                        df = df.dropna(subset=['Player'])
                        df = df[df['Velo'] > 0]
                        all_data.append(df)
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

                # HTMLテーブルの構築
                table_html = '<table class="feedback-table"><thead><tr>'
                for col in display_df.columns: table_html += f'<th>{col}</th>'
                table_html += '</tr></thead><tbody>'
                for _, row in display_df.iterrows():
                    table_html += '<tr>'
                    for col in display_df.columns:
                        val = row[col]
                        css_class = ""
                        if col == 'MAX球速':
                            if val >= 150: css_class = ' class="v-high"'
                            elif val >= 145: css_class = ' class="high"'
                        
                        d_val = f"{val:.1f}" if col != '平均回転数' else f"{int(val)}"
                        table_html += f'<td{css_class}>{d_val}</td>'
                    table_html += '</tr>'
                st.write(table_html + '</tbody></table>', unsafe_allow_html=True)

        else:
            player = st.sidebar.selectbox("投手を選択", sorted(df['Player'].unique()))
            st.header(f"👤 {player} 分析")
            
            full_p_df = df[df['Player'] == player].copy()
            
            analysis_type = st.radio("分析範囲", ["総合", "特定の日付"], horizontal=True)
            if analysis_type == "特定の日付":
                p_dates = sorted(full_p_df['Date'].unique(), reverse=True)
                sel_dates = st.multiselect("日付を選択", p_dates, default=[p_dates[0]])
                p_df = full_p_df[full_p_df['Date'].isin(sel_dates)]
            else:
                p_df = full_p_df

            c1, c2, c3 = st.columns(3)
            c1.metric("MAX球速", f"{p_df['Velo'].max():.1f} km/h")
            c2.metric("平均球速", f"{p_df['Velo'].mean():.1f} km/h")
            c3.metric("平均回転数", f"{int(p_df['Spin'].mean())} rpm")

            st.subheader("📈 球速推移（通算）")
            trend = full_p_df.groupby('Date')['Velo'].agg(['mean', 'max']).reset_index()
            fig = px.line(trend, x='Date', y=['mean', 'max'], markers=True)
            fig.update_layout(yaxis_range=[120, 160]) # 投手のボリューム層に合わせて調整
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("📋 投球詳細履歴")
            hist = p_df[['Date', 'Velo', 'Spin']].sort_values(['Date', 'Velo'], ascending=[False, False])
            st.write(hist.to_html(classes='feedback-table', index=False, float_format='%.1f'), unsafe_allow_html=True)

    else:
        st.info("投手データのCSVファイルをdataフォルダに入れてください。")
