import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go

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

    # --- デザインCSS ---
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
        data_dir = "data"
        if os.path.exists(data_dir):
            for file in os.listdir(data_dir):
                if file.endswith(('.csv', '.xlsx')):
                    path = os.path.join(data_dir, file)
                    try:
                        df = pd.read_excel(path) if file.endswith('.xlsx') else pd.read_csv(path)
                        df.columns = df.columns.str.strip()
                        # マッピング
                        col_map = {
                            'Pitcher First Name': 'Player',
                            'Pitch Created At': 'Date',
                            'RelSpeed (KMH)': 'Velo',
                            'SpinRate': 'Spin',
                            'Pitch Type': 'PitchType',
                            'InducedVertBreak (CM)': 'IVB',
                            'HorzBreak (CM)': 'HB',
                            'PlateLocSide (CM)': 'LocX',
                            'PlateLocHeight (CM)': 'LocY',
                            'VertRelAngle': 'VRA',
                            'HorzRelAngle': 'HRA',
                            'Spin Efficiency': 'Eff'
                        }
                        for old, new in col_map.items():
                            if old in df.columns:
                                if new == 'Date':
                                    df[new] = pd.to_datetime(df[old], errors='coerce').dt.date
                                elif new in ['Velo', 'Spin', 'IVB', 'HB', 'LocX', 'LocY', 'VRA', 'HRA', 'Eff']:
                                    df[new] = pd.to_numeric(df[old], errors='coerce')
                                else:
                                    df[new] = df[old]
                        
                        df = df.dropna(subset=['Player', 'Date', 'Velo'])
                        all_data.append(df)
                    except: continue
        return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

    df = load_data()

    if not df.empty:
        # 1. 日付の選択
        all_dates = sorted(df['Date'].unique(), reverse=True)
        selected_date = st.sidebar.selectbox("1. 日付を選択", all_dates)
        
        # 2. 名前の選択
        date_df = df[df['Date'] == selected_date]
        all_players = sorted(date_df['Player'].unique())
        selected_player = st.sidebar.selectbox("2. 投手を選択", all_players)
        
        p_df = date_df[date_df['Player'] == selected_player].copy()

        st.header(f"📊 {selected_player} 分析 ({selected_date})")

        # --- グラフセクション ---
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("変化量グラフ (IVB vs HB)")
            if 'IVB' in p_df.columns and 'HB' in p_df.columns:
                fig_break = px.scatter(p_df, x='HB', y='IVB', color='PitchType',
                                     hover_data=['Velo'],
                                     range_x=[-80, 80], range_y=[-80, 80],
                                     labels={'HB': '水平変化 (cm)', 'IVB': '垂直変化 (cm)'})
                fig_break.add_hline(y=0, line_dash="dash", line_color="gray")
                fig_break.add_vline(x=0, line_dash="dash", line_color="gray")
                st.plotly_chart(fig_break, use_container_width=True)
            else:
                st.info("変化量データがありません")

        with col2:
            st.subheader("投球位置 (捕手視点)")
            if 'LocX' in p_df.columns and 'LocY' in p_df.columns:
                fig_loc = px.scatter(p_df, x='LocX', y='LocY', color='PitchType',
                                   range_x=[-100, 100], range_y=[0, 200],
                                   labels={'LocX': '左右 (cm)', 'LocY': '高さ (cm)'})
                # ストライクゾーンの目安
                fig_loc.add_shape(type="rect", x0=-25, y0=45, x1=25, y1=105,
                                line=dict(color="RoyalBlue", width=3))
                st.plotly_chart(fig_loc, use_container_width=True)
            else:
                st.info("投球位置データがありません")

        # --- 球種別統計表 ---
        st.subheader("📋 球種別平均データ")
        if 'PitchType' in p_df.columns:
            # 指定された項目の平均を計算
            stats_df = p_df.groupby('PitchType').agg({
                'Velo': 'mean',
                'Spin': 'mean',
                'VRA': 'mean',
                'HRA': 'mean',
                'Eff': 'mean'
            }).reset_index()
            
            stats_df.columns = ['球種', '平均球速', '平均回転数', 'リリース角度(縦)', 'リリース角度(横)', '回転効率(%)']
            
            # 回転効率を%表示にするなどの整形
            st.write(stats_df.to_html(classes='stats-table', index=False, float_format='%.1f'), unsafe_allow_html=True)
        
        # 詳細データ一覧
        with st.expander("全投球データを確認"):
            st.dataframe(p_df)

    else:
        st.warning("有効なデータが見つかりません。'data'フォルダのCSVを確認してください。")
