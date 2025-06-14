'''
Dashboard for Southeastern US Districts

1) be user-friendly interface 
2) enables others to explore the data. 
3) use effective visual mappings with interactivity
4) offering users to engage with your data in meaningful ways.

Your dashboard should include:

a) At least one UI interaction (e.g., dropdown, slider, checkbox)
b) At least one within-visualization interaction (e.g., clicking, brushing)
c) Tooltip functionality for exploring data values
d) At least two coordinated visualizations (e.g., selection in one affects the other)

'''

import streamlit as st
import pandas as pd
import altair as alt
import random as rd
# Set the page to a wide layout for better visualization

@st.cache_data
def load_data():
    df = pd.read_csv("https://raw.githubusercontent.com/j-linarez/DataVizProject/refs/heads/main/Southeast%20Region%20Congressional%20Districts.csv")
    df["Democratic %"] = (df["E_16-20_COMP_Dem"] / df["E_16-20_COMP_Total"]) * 100
    df["Republican %"] = (df["E_16-20_COMP_Rep"] / df["E_16-20_COMP_Total"]) * 100
    df["Partisan Margin"] = df["Republican %"] - df["Democratic %"]
    minority_cols = {
        "Hispanic": "T_20_CENS_Hispanic",
        "Black": "T_20_CENS_Black",
        "Asian": "T_20_CENS_Asian",
        "Native": "T_20_CENS_Native",
        "Pacific": "T_20_CENS_Pacific"
    }
    df["Total Minority Population"] = df[list(minority_cols.values())].sum(axis=1)
    df["Minority Percentage"] = (df["Total Minority Population"] / df["T_20_CENS_Total"]) * 100
    for label, col in minority_cols.items():
        df[f"{label} %"] = (df[col] / df["T_20_CENS_Total"]) * 100
    return df

# Define state groups
state_groups = {
    "All States": None,
    "Independent Commission": ["Louisiana", "Virginia"],
    "Republican Legislatures": [
        "Arkansas", "Mississippi", "Alabama", "Georgia", "Florida",
        "South Carolina", "North Carolina", "Tennessee", "Kentucky", "West Virginia", "Virginia"
    ],
    "Competitive States": ["Georgia", "North Carolina", "Virginia"],
    "Conservative States": [
        "Arkansas", "Louisiana", "Mississippi", "Alabama", "Tennessee",
        "West Virginia", "Kentucky", "South Carolina", "Florida"
    ]
}

# Load data and set page config
df = load_data()
st.set_page_config(layout="wide")
st.title("Southeast U.S. Congressional Voting & Demographics Dashboard")

# UI Controls
st.markdown("### Filters")
colA, colB, colC = st.columns([2, 2, 2])
with colA:
    state_group = st.selectbox("State Group", list(state_groups.keys()))
    if state_group == "All States":
        selected_states = st.multiselect(
            "States",
            options=sorted(df["State"].unique()),
            default=sorted(df["State"].unique())
        )
    else:
        selected_states = st.multiselect(
            "States in Group (you can modify)",
            options=sorted(df["State"].unique()),
            default=state_groups[state_group]
        )

with colB:
    selected_group = st.selectbox("Minority % Group", [
        "All", "Below 35%", "35–50%", "50–75%", "75%+"
    ])

with colC:
    selected_demo = st.selectbox("Demographic Focus", [
        "Total Minority", "Hispanic", "Black", "Asian", "Native", "Pacific"
    ])

# Data Filtering Logic
filtered_df = df[df["State"].isin(selected_states)]

if selected_group != "All":
    if selected_group == "Below 35%":
        filtered_df = filtered_df[filtered_df["Minority Percentage"] < 35]
    elif selected_group == "35–50%":
        filtered_df = filtered_df[(filtered_df["Minority Percentage"] >= 35) & (filtered_df["Minority Percentage"] < 50)]
    elif selected_group == "50–75%":
        filtered_df = filtered_df[(filtered_df["Minority Percentage"] >= 50) & (filtered_df["Minority Percentage"] < 75)]
    elif selected_group == "75%+":
        filtered_df = filtered_df[filtered_df["Minority Percentage"] >= 75]

# Choose column for demographic focus
if selected_demo == "Total Minority":
    demo_col = "Minority Percentage"
else:
    demo_col = f"{selected_demo} %"

# Shared selection
brush = alt.selection_interval(encodings=["x"])

# Box + Dot Chart
margin_chart = alt.Chart(filtered_df).mark_boxplot(extent="min-max").encode(
    x=alt.X("State:N", title="State"),
    y=alt.Y("Partisan Margin:Q", title="Partisan Voting Margin"),
    color=alt.value("lightgray")
).properties(width=600, height=400)

points = alt.Chart(filtered_df).mark_circle(size=60, opacity=0.5, color="black").encode(
    x="State:N",
    y="Partisan Margin:Q",
    tooltip=["CD_Num", "State", "Partisan Margin"]
).add_selection(brush)

combined_margin = margin_chart + points

# Minority vs Margin Scatter
scatter = alt.Chart(filtered_df).mark_circle(size=60, opacity=0.6).encode(
    x=alt.X(f"{demo_col}:Q", title=f"{selected_demo} %"),
    y=alt.Y("Partisan Margin:Q", title="Partisan Margin"),
    color=alt.Color("State:N"),
    tooltip=["CD_Num", "State", demo_col, "Partisan Margin"]
).add_selection(brush).properties(width=600, height=400)

# Vote Composition Chart
party_df = df[df["State"].isin(selected_states)].groupby("State")[["E_16-20_COMP_Dem", "E_16-20_COMP_Rep", "E_16-20_COMP_Total"]].sum()
party_df["Democratic %"] = (party_df["E_16-20_COMP_Dem"] / party_df["E_16-20_COMP_Total"]) * 100
party_df["Republican %"] = (party_df["E_16-20_COMP_Rep"] / party_df["E_16-20_COMP_Total"]) * 100
party_df["Other %"] = 100 - party_df["Democratic %"] - party_df["Republican %"]
stacked_data = party_df.reset_index()[["Democratic %", "Republican %", "Other %", "State"]].melt(id_vars="State", var_name="Party", value_name="Percentage")

stacked_chart = alt.Chart(stacked_data).mark_bar().encode(
    y=alt.Y("State:N", sort="-x"),
    x=alt.X("Percentage:Q", stack="normalize"),
    color=alt.Color("Party:N", scale=alt.Scale(domain=["Democratic %", "Republican %", "Other %"],
                                               range=["#00AEF3", "#E81B23", "#808080"])),
    tooltip=["State", "Party", "Percentage"]
).properties(width=600, height=400)

# Summary Statistics
summary_df = filtered_df.groupby("State")[["Partisan Margin", "Minority Percentage"]].mean().reset_index()

# KPI Cards
avg_margin = filtered_df["Partisan Margin"].mean()
avg_minority = filtered_df["Minority Percentage"].mean()
num_districts = len(filtered_df)

# Display Layout
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Average Vote Margin", avg_margin)
with col2:
    st.metric("Average Minority %", avg_minority)
with col3:
    st.metric("Number of Districts", num_districts)

col1, col2 = st.columns(2)
with col1:
    st.altair_chart(combined_margin, use_container_width=True)
    st.altair_chart(stacked_chart, use_container_width=True)
with col2:
    st.altair_chart(scatter, use_container_width=True)

st.write("### Summary Statistics")
st.write(summary_df)