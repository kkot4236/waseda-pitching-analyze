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
        # 安全にセッション状態を更新
        if st.session_state.get("password_input") == "wbc1901":
            st.session_state["password_correct"] = True
        else:
            st.session_state["password_correct"] = False

    st.title("⚾️ 早稲田大学野球部 投手分析システム")
    st.text_input("パスワードを入力", type="password", on_change=password_entered, key="password_input")
    
    if st.session_state["password_correct"] == False:
        st.error("パスワードが違います")
    return False

if check_password():
    st.set_page_config(layout="wide", page_title="Waseda Pitching Analyze")

    # --- デザインCSS ---
    st.markdown("""
        <style>
        .feedback-table { margin: auto; border-collapse: collapse; width: 100%; border: 1px solid #333; }
        .feedback-table th { background-color: #1e3a8a !important; color: white !important; padding: 12px; text-align: center !important; }
        .feedback-table td { padding: 10px; border: 1px solid #ccc; text-align: center !important; }
        .v-high { background-color: #ff4b4b !important; color: white !important; font-weight: bold; }
        .high { background-color: #ffcccc !important; color: #b30000 !important; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)

    @st.cache_data
    def load_data():
        all_data = []
        # カレントディレクトリとdataフォルダの両方を探す
        target_dirs = [".", "data"]
        for d in target_dirs:
            if not os.path.exists(d): continue
            for file in os.listdir(d):
                if file.endswith(('.csv', '.xlsx')):
                    path = os.path.join(d, file)
                    try:
                        df = pd.read_excel(path) if file.endswith('.xlsx') else pd.read_csv(path)
                        df.columns = df.columns.str.strip()
                        
                        # --- 読み込み条件を大幅に緩和 ---
                        # 名前列
                        for col in ['Pitcher First Name', 'Pitcher', 'Player', '名前', 'Last Name']:
                            if col in df.columns: df['Player'] = df[col]; break
                        
                        # 日付列
                        for col in ['Pitch Created At', 'Date', '日付', 'Time']:
                            if col in df.columns: df['Date'] = pd.to_datetime(df[col]).dt.date; break
                        
                        # 球速列
                        for col in ['Velocity (KMH)', 'ReleaseSpeed', '球速', 'Velocity']:
                            if col in df.columns: df['Velo'] = pd.to_numeric(df[col], errors='coerce'); break
                            
                        # 回転数列
                        for col in ['SpinRate', 'Spin Rate', '回転数']:
                            if col in df.columns: df['Spin'] = pd.to_numeric(df[col], errors='coerce'); break

                        if 'Player' in df.columns and 'Velo' in df.columns:
                            all_data.append(df.dropna(subset=['Player', 'Velo']))
                    except: continue
        return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

    df = load_data()

    if not df.empty:
        # --- (ここにメインの分析画面コードが入ります) ---
        # 以前のコードの「mode = st.sidebar.radio...」以降をここに結合
        st.success(f"データを読み込みました: {len(df)} 件")
        
        player = st.sidebar.selectbox("投手を選択", sorted(df['Player'].unique()))
        p_df = df[df['Player'] == player].copy()
        
        st.header(f"👤 {player} 分析")
        c1, c2, c3 = st.columns(3)
        c1.metric("MAX球速", f"{p_df['Velo'].max():.1f} km/h")
        c2.metric("平均球速", f"{p_df['Velo'].mean():.1f} km/h")
        if 'Spin' in p_df.columns:
            c3.metric("平均回転数", f"{int(p_df['Spin'].mean())} rpm")

        st.subheader("📈 球速推移")
        trend = p_df.groupby('Date')['Velo'].agg(['mean', 'max']).reset_index()
        fig = px.line(trend, x='Date', y=['mean', 'max'], markers=True)
        fig.update_layout(yaxis_range=[120, 160])
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("📋 詳細履歴")
        show_cols = [c for c in ['Date', 'Velo', 'Spin'] if c in p_df.columns]
        st.write(p_df[show_cols].sort_values(['Date', 'Velo'], ascending=[False, False]).to_html(classes='feedback-table', index=False, float_format='%.1f'), unsafe_allow_html=True)
        
    else:
        st.warning("⚠️ CSVファイルは見つかりましたが、投手データ（名前や球速の列）が正しく読み込めませんでした。")
        st.info("CSVの1行目の項目名が 'Pitcher First Name' や 'Velocity (KMH)' になっているか確認してください。")
