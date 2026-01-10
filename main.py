import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import plotly.express as px

# --- 基本設定 ---
# 色設定（ラプソードの球種名に対応）
PITCH_COLORS = {
    'FB': '#FF4B4B', 'CB': '#1E90FF', 'SL': '#FF1493', 
    'CH': '#32CD32', 'SP': '#40E0D0', 'CT': '#8A2BE2', 
    'SI': '#FFA500', 'OTH': '#808080'
}

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
    st.set_page_config(layout="wide", page_title="Rapsodo Analysis Pro")

    # --- データ読み込み ---
    @st.cache_data
    def load_data():
        DATA_DIR = "data"
        all_data = []
        if os.path.exists(DATA_DIR):
            files = [f for f in os.listdir(DATA_DIR) if f.endswith(('.csv', '.xlsx'))]
            for f in files:
                path = os.path.join(DATA_DIR, f)
                try:
                    df = pd.read_excel(path) if f.endswith('.xlsx') else pd.read_csv(path)
                    if 'Pitcher First Name' in df.columns and 'Pitcher Last Name' in df.columns:
                        df['Pitcher'] = df['Pitcher Last Name'] + " " + df['Pitcher First Name']
                    
                    # 必須項目の数値化
                    cols = ['RelSpeed (KMH)', 'InducedVertBreak (CM)', 'HorzBreak (CM)', 'SpinRate', 'Spin Efficiency', 'PlateLocSide (CM)', 'PlateLocHeight (CM)']
                    for c in cols:
                        if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce')
                    
                    df['Date_str'] = pd.to_datetime(df['Pitch Created At']).dt.strftime('%Y-%m-%d')
                    all_data.append(df)
                except Exception as e:
                    st.error(f"ファイル読み込みエラー: {f} - {e}")
        return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

    df = load_data()

    if not df.empty:
        st.sidebar.header("Filter")
        pitcher = st.sidebar.selectbox("投手を選択", sorted(df['Pitcher First Name'].unique()))
        p_df = df[df['Pitcher'] == pitcher].copy()
        
        dates = st.sidebar.multiselect("日付選択", sorted(p_df['Date_str'].unique(), reverse=True))
        if dates: p_df = p_df[p_df['Date_str'].isin(dates)]

        mode = st.sidebar.radio("表示モード", ["Dashboard", "Analysis"])

        if mode == "Dashboard":
            st.header(f"📊 {pitcher}")
            c1, c2 = st.columns(2)
            with c1:
                fig, ax = plt.subplots(figsize=(6,6))
                for pt in p_df['Pitch Type'].unique():
                    sub = p_df[p_df['Pitch Type'] == pt]
                    ax.scatter(sub['HorzBreak (CM)'], sub['InducedVertBreak (CM)'], label=pt, color=PITCH_COLORS.get(pt, '#808080'), alpha=0.6)
                ax.axvline(0, color='black', lw=1); ax.axhline(0, color='black', lw=1)
                ax.set_xlim(-80, 80); ax.set_ylim(-80, 80); ax.set_xlabel("Horizontal Break (cm)"); ax.set_ylabel("Vertical Break (cm)"); ax.set_box_aspect(1); ax.legend()
                st.pyplot(fig)

            with c2:
                fig, ax = plt.subplots(figsize=(6,6))
                ax.add_patch(plt.Rectangle((-25, 45), 50, 60, fill=False, lw=2, color='black')) # Strike Zone
                for pt in p_df['Pitch Type'].unique():
                    sub = p_df[p_df['Pitch Type'] == pt]
                    ax.scatter(sub['PlateLocSide (CM)'], sub['PlateLocHeight (CM)'], color=PITCH_COLORS.get(pt, '#808080'), alpha=0.6)
                ax.set_xlim(-100, 100); ax.set_ylim(0, 200); ax.set_xlabel("Side (cm)"); ax.set_ylabel("Height (cm)"); ax.set_box_aspect(1)
                st.pyplot(fig)

            st.subheader("📋 Average Stats")
            agg_df = p_df.groupby('Pitch Type').agg({
                'Pitcher': 'count',
                'RelSpeed (KMH)': 'mean',
                'SpinRate': 'mean',
                'Spin Efficiency': 'mean',
                'InducedVertBreak (CM)': 'mean',
                'HorzBreak (CM)': 'mean'
            }).rename(columns={'Pitcher': 'Count', 'RelSpeed (KMH)': 'Speed', 'Spin Efficiency': 'Spin Eff%'}).reset_index()
            st.dataframe(agg_df.style.format(precision=1), use_container_width=True, hide_index=True)

        elif mode == "Analysis":
            item = st.sidebar.radio("Analysis Item", ["Spin Eff% vs Break", "Speed BoxPlot", "Gyro Degree"])
            if item == "Spin Eff% vs Break":
                fig = px.scatter(p_df, x="Spin Efficiency", y="InducedVertBreak (CM)", color="Pitch Type", color_discrete_map=PITCH_COLORS)
                st.plotly_chart(fig, use_container_width=True)
            elif item == "Speed BoxPlot":
                fig = px.box(p_df, x="Pitch Type", y="RelSpeed (KMH)", color="Pitch Type", color_discrete_map=PITCH_COLORS)
                st.plotly_chart(fig, use_container_width=True)
            elif item == "Gyro Degree":
                fig = px.scatter(p_df, x="Gyro Degree (deg)", y="SpinRate", color="Pitch Type", color_discrete_map=PITCH_COLORS)
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data found in 'data' folder.")
