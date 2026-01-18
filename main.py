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
                        
                        # 項目マッピング（ご提示いただいたCSVの正式名称）
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
                                else:
                                    df[new] = pd.to_numeric(df[old], errors='coerce') if new != 'PitchType' else df[old]
                        
                        df = df.dropna(subset=['Player', 'Date', 'Velo'])
                        all_data.append(df)
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
            # 軸の範囲を -80 〜 80 に固定
            fig_break = px.scatter(p_df, x='HB', y='IVB', color='PitchType',
                                 hover_data=['Velo'],
                                 range_x=[-80, 80], range_y=[-80, 80],
                                 labels={'HB': '水平変化 (cm)', 'IVB': '垂直変化 (cm)'})
            
            # 補助線
            fig_break.add_hline(y=0, line_dash="dash", line_color="black")
            fig_break.add_vline(x=0, line_dash="dash", line_color="black")
            
            # グラフの縦横比を正方形に近くして直感的にする
            fig_break.update_yaxes(scaleanchor="x", scaleratio=1)
            st.plotly_chart(fig_break, use_container_width=True)

        with col2:
            st.subheader("投球位置 (捕手視点)")
            # 軸の範囲を 左右±60, 高さ0〜200 に固定
            fig_loc = px.scatter(p_df, x='LocX', y='LocY', color='PitchType',
                               range_x=[-60, 60], range_y=[0, 200],
                               labels={'LocX': '左右 (cm)', 'LocY': '高さ (cm)'})
            # ストライクゾーンの枠線
            fig_loc.add_shape(type="rect", x0=-25, y0=45, x1=25, y1=105,
                            line=dict(color="black", width=2))
            st.plotly_chart(fig_loc, use_container_width=True)

        # 球種別統計表
        st.subheader("📋 球種別平均データ")
        target_cols = ['Velo', 'Spin', 'VRA', 'HRA', 'Eff']
        actual_cols = [c for c in target_cols if c in p_df.columns]
        
        if 'PitchType' in p_df.columns:
            # 球種ごとの投球数も追加してみました
            stats_df = p_df.groupby('PitchType').agg({
                'Velo': 'count',  # 投球数カウント用
                **{c: 'mean' for c in actual_cols}
            }).reset_index()
            
            # カラム名の日本語化
            rename_dict = {
                'PitchType': '球種', 'Velo': '投球数', 'Spin': '回転数',
                'VRA': 'リリース角度(縦)', 'HRA': 'リリース角度(横)', 'Eff': '回転効率(%)'
            }
            # 球種別平均球速の列を正しくセット
            stats_df['Velo_mean'] = p_df.groupby('PitchType')['Velo'].mean().values
            
            # 列の並び替えと名前変更
            final_cols = ['PitchType', 'Velo', 'Velo_mean', 'Spin', 'VRA', 'HRA', 'Eff']
            stats_df = stats_df[final_cols]
            stats_df.columns = ['球種', '投球数', '平均球速', '回転数', 'リリース角度(縦)', 'リリース角度(横)', '回転効率(%)']
            
            st.write(stats_df.to_html(classes='stats-table', index=False, float_format='%.1f'), unsafe_allow_html=True)
            
    else:
        st.warning("データが見つかりません。")
