import streamlit as st
import pandas as pd
import plotly.express as px
import os
import numpy as np

# Page configuration
st.set_page_config(page_title="Player Wellness Monitoring", layout="wide")

# App title
st.title("Player Wellness Monitoring")

# Fixed Excel file path
file_path = r"C:\Users\asus\Desktop\app\monitoraggio_benessere.xlsx"

# Check if file exists
if not os.path.exists(file_path):
    st.error(f"Excel file not found at: {file_path}")
    st.info("Please make sure the file exists and the path is correct.")
else:
    # Load data
    df = pd.read_excel(file_path)
    df.columns = [c.strip().capitalize() for c in df.columns]
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # Sidebar - mode selection
    st.sidebar.header("View mode")
    mode = st.sidebar.radio(
        "Choose what to display:",
        ["Team comparison by date", "Player progress"]
    )

    # -----------------------------------------------------------
    # TEAM COMPARISON BY DATE
    # -----------------------------------------------------------
    if mode == "Team comparison by date":
        available_dates = sorted(df["Date"].dropna().unique())
        date_labels = [d.strftime("%d %b %Y") for d in available_dates]
        selected_label = st.selectbox("Select a date:", date_labels)
        selected_date = available_dates[date_labels.index(selected_label)]

        df_day = df[df["Date"] == selected_date]

        st.subheader(f"Team data - {selected_date.strftime('%d %b %Y')}")

        # Calculate team average row
        avg_row = {
            "Player": "TEAM AVERAGE",
            "Physical": df_day["Physical"].mean(),
            "Psychological": df_day["Psychological"].mean(),
            "Nutrition": df_day["Nutrition"].mean(),
            "Sleep": df_day["Sleep"].mean(),
            "Other": ""
        }
        df_day_with_avg = pd.concat([df_day, pd.DataFrame([avg_row])], ignore_index=True)

        # Order columns
        table = df_day_with_avg[["Player", "Physical", "Psychological", "Nutrition", "Sleep", "Other"]]

        # Highlight average row
        def highlight_average(row):
            if row["Player"] == "TEAM AVERAGE":
                return ["background-color: #e0e0e0; font-weight: bold;"] * len(row)
            else:
                return [""] * len(row)

        table_styled = (
            table.style
            .apply(highlight_average, axis=1)
            .format("{:.0f}", subset=["Physical", "Psychological", "Nutrition", "Sleep"])
            .set_table_styles(
                [
                    {"selector": "th", "props": [("font-size", "14px"), ("text-align", "center")]},
                    {"selector": "td", "props": [("font-size", "13px"), ("padding", "3px 6px"), ("text-align", "center")]},
                ]
            )
        )

        st.dataframe(
            table_styled,
            use_container_width=True,
            hide_index=True,
            height=min(500, 80 + 30 * len(df_day_with_avg))
        )

        st.subheader("Team comparison chart")

        df_melt = df_day.melt(
            id_vars=["Player"],
            value_vars=["Physical", "Psychological", "Nutrition", "Sleep"],
            var_name="Parameter",
            value_name="Value"
        )

        fig_bar = px.bar(
            df_melt,
            x="Player",
            y="Value",
            color="Parameter",
            barmode="group",
            text_auto=True,
            title=f"Team comparison - {selected_date.strftime('%d %b %Y')}",
            labels={"Value": "Rating (1–10)", "Player": "Player"}
        )
        fig_bar.update_layout(yaxis_range=[0, 10])
        st.plotly_chart(fig_bar, use_container_width=True)

    # -----------------------------------------------------------
    # PLAYER PROGRESS
    # -----------------------------------------------------------
    elif mode == "Player progress":
        players = sorted(df["Player"].dropna().unique().tolist())
        player = st.selectbox("Select a player:", players)

        df_player = df[df["Player"] == player].sort_values("Date")

        for col in ["Physical", "Psychological", "Nutrition", "Sleep"]:
            df_player[col] = pd.to_numeric(df_player[col], errors="coerce")

        # Add jitter to avoid overlapping
        df_melt = df_player.melt(
            id_vars=["Date", "Other"],
            value_vars=["Physical", "Psychological", "Nutrition", "Sleep"],
            var_name="Parameter",
            value_name="Value"
        )
        df_melt["Value_jitter"] = df_melt["Value"] + np.random.uniform(-0.1, 0.1, len(df_melt))
        df_melt["Date_str"] = df_melt["Date"].dt.strftime("%d %b %Y")

        # Trend chart
        fig = px.line(
            df_melt,
            x="Date_str",
            y="Value_jitter",
            color="Parameter",
            markers=True,
            hover_data=["Other", "Value"],
            title=f"Performance trend - {player}",
            labels={"Date_str": "Date", "Value_jitter": "Rating (1–10)"}
        )

        fig.update_traces(line=dict(width=4))
        fig.update_layout(yaxis_range=[0, 10])
        st.plotly_chart(fig, use_container_width=True)

        # Last 7 days overview (ascending order)
        st.subheader("Last 7 days overview")
        recent_df = df_player.sort_values("Date", ascending=True).tail(7)
        recent_df = recent_df[["Date", "Physical", "Psychological", "Nutrition", "Sleep", "Other"]]
        recent_df["Date"] = recent_df["Date"].dt.strftime("%d %b %Y")

        st.dataframe(
            recent_df.style.format("{:.0f}", subset=["Physical", "Psychological", "Nutrition", "Sleep"]),
            use_container_width=True,
            hide_index=True,
            height=min(400, 60 + 30 * len(recent_df))
        )

        st.subheader("Average values")
        avg = df_player[["Physical", "Psychological", "Nutrition", "Sleep"]].mean()
        st.write(avg.to_frame("Average").style.format("{:.0f}"))
