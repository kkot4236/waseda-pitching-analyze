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
    st.set_page_config(layout="wide", page_title="Waseda Pitcher Analytics")

    st.markdown("""
        <style>
        .stats-table { margin: auto; border-collapse: collapse; width: 100%; border: 1px solid #333; font-size: 14px; }
        .stats-table th { background-color: #1e3a8a !important; color: white !important; padding: 8px; text-align: center !important; }
        .stats-table td { padding: 8px; border: 1px solid #ccc; text-align: center !important; }
        </style>
    """, unsafe_allow_html=True)

    @st.cache_data
    def load_data():
        all_data = []
        # 現在のフォルダとdataフォルダの両方を再帰的に探す
        for root, dirs, files in os.walk("."):
            for file in files:
                if file.endswith(('.csv', '.xlsx')):
                    path = os.path.join(root, file)
                    try:
                        df = pd.read_excel(path) if file.endswith('.xlsx') else pd.read_csv(path)
                        df.columns = df.columns.str.strip()
                        
                        # カラムの紐付け（柔軟に対応）
                        mapping = {
                            'Player': ['Pitcher First Name', 'Pitcher', 'Player'],
                            'Date': ['Pitch Created At', 'Date'],
                            'Velo': ['RelSpeed (KMH)', 'Velo', 'Velocity'],
                            'Spin': ['SpinRate', 'Spin Rate', 'Spin'],
                            'PitchType': ['Pitch Type', 'PitchType'],
                            'IVB': ['InducedVertBreak (CM)', 'IVB'],
                            'HB': ['HorzBreak (CM)', 'HB'],
                            'LocX': ['PlateLocSide (CM)', 'LocX'],
                            'LocY': ['PlateLocHeight (CM)', 'LocY'],
                            'VRA': ['VertRelAngle', 'VRA'],
                            'HRA': ['HorzRelAngle', 'HRA'],
                            'Eff': ['Spin Efficiency', 'Spin Efficiency (%)', 'Eff']
                        }
                        
                        new_df = pd.DataFrame()
                        for target, opts in mapping.items():
                            for opt in opts:
                                if opt in df.columns:
                                    if target == 'Date':
                                        new_df[target] = pd.to_datetime(df[opt], errors='coerce').dt.date
                                    else:
                                        new_df[target] = pd.to_numeric(df[opt], errors='coerce') if target != 'PitchType' else df[opt]
                                    break
                        
                        if 'Player' in new_df.columns and 'Velo' in new_df.columns:
                            all_data.append(new_df.dropna(subset=['Player', 'Date', 'Velo']))
                    except: continue
        return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

    df = load_data()

    if not df.empty:
        # 1. 日付選択
        all_dates = sorted([d for d in df['Date'].unique() if d is not None], reverse=True)
        selected_date = st.sidebar.selectbox("1. 日付を選択", all_dates)
        
        # 2. 名前選択
        date_df = df[df['Date'] == selected_date]
        all_players = sorted(date_df['Player'].unique())
        selected_player = st.sidebar.selectbox("2. 投手を選択", all_players)
        
        p_df = date_df[date_df['Player'] == selected_player].copy()

        st.header(f"📊 {selected_player} 分析 ({selected_date})")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("変化量グラフ (IVB vs HB)")
            # 軸を -80 〜 80 に固定
            fig_break = px.scatter(p_df, x='HB', y='IVB', color='PitchType',
                                 range_x=[-80, 80], range_y=[-80, 80],
                                 labels={'HB': '水平変化 (cm)', 'IVB': '垂直変化 (cm)'})
            fig_break.add_hline(y=0, line_dash="dash", line_color="black")
            fig_break.add_vline(x=0, line_dash="dash", line_color="black")
            fig_break.update_yaxes(scaleanchor="x", scaleratio=1)
            st.plotly_chart(fig_break, use_container_width=True)

        with col2:
            st.subheader("投球位置 (捕手視点)")
            fig_loc = px.scatter(p_df, x='LocX', y='LocY', color='PitchType',
                               range_x=[-60, 60], range_y=[0, 200],
                               labels={'LocX': '左右 (cm)', 'LocY': '高さ (cm)'})
            fig_loc.add_shape(type="rect", x0=-25, y0=45, x1=25, y1=105, line=dict(color="black", width=2))
            st.plotly_chart(fig_loc, use_container_width=True)

        st.subheader("📋 球種別平均データ")
        if not p_df.empty:
            # 集計
            stats = p_df.groupby('PitchType').agg({
                'Velo': ['count', 'mean'],
                'Spin': 'mean',
                'VRA': 'mean',
                'HRA': 'mean',
                'Eff': 'mean'
            }).reset_index()
            stats.columns = ['球種', '投球数', '平均球速', '回転数', '角度(縦)', '角度(横)', '回転効率']
            st.write(stats.to_html(classes='stats-table', index=False, float_format='%.1f'), unsafe_allow_html=True)
            
    else:
        st.warning("データが見つかりません。CSVファイルが正しくアップロードされているか確認してください。")
        st.info("ファイルが 'data' フォルダ、もしくはアプリと同じ場所に配置されている必要があります。")
