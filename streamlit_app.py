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

# Evaluation group explanations
evaluation_contexts = {
    "All States": """This includes all congressional districts in the Southeastern U.S. This is the default view of all the charts provided""",
    "Independent Commission": """These states (Louisiana, Virginia) use independent or court ordered commissions for redistricting. They are intended to reduce political intervention.""",
    "Republican Legislatures": """These states allow their legislatures to draw congressional maps. In all these states, Republicans often do not have to worry about potential concerns of partisan fairness / minority representation.""",
    "Competitive States": """Georgia, North Carolina, and Virginia are considered politically competitive (within 10 percent of winning margin). However, many of these states after controlled by the Republican party.""",
    "Conservative States": """These states consistently vote Republican. They often do not vote for the Democratic party. Despite this, a sizable amount of minority voters often live in these states."""
}

# Demographic focus descriptions
demo_contexts = {
    "Total Minority": "This combines all non-white racial/ethnic groups. It accounts all groups of ethnic groups.",
    "Black": "The Black population plays a significant role in many Southern states' Democratic voting base. They are commonly found in rural / urban areas impacted by the history of racial segeration.",
    "Hispanic": "Though growing, Hispanic populations are not evenly distributed in the Southeast. They are most prevalent in Florida.",
    "Asian": "Smaller in proportion but growing in urban centers, Asian populations are more likely to be found in the Atlanta metro.",
    "Native": "Native American populations are extremely small in the Southeast.",
    "Pacific": "Pacific Islander populations are extremely small in the Southeast."
}

# Load data and set page config
df = load_data()
st.set_page_config(layout="wide")
st.title("Southeast U.S. Congressional Voting & Demographics Dashboard")

# Introduction
st.markdown("### Introduction")
st.write("This dashboard provides an interactive exploration of the relationship between partisan voting margins and minority demographics in congressional districts across the Southeastern United States. As a user, you are free to explore what the dashboard offers. " \
"If you are confused with terminology, descriptions have been placed for your convience. The partisan voting margin is determined by a left - right scale where negative values indicate a Democratic lead and positive values are a Republican lead")

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

# Context Sections
st.markdown("### Context")
st.write("**State Group:**")
st.info(evaluation_contexts[state_group])
st.write("**Demographic Focus:**")
st.write(demo_contexts[selected_demo])

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
rule = alt.Chart(pd.DataFrame({'x': [50]})).mark_rule(strokeDash=[2, 2], color='red').encode(x='x:Q')

# Combine the scatterplot and rule
scatter = scatter + rule

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

# Annotate the chart with percentages
democratic_annotations = alt.Chart(stacked_data[stacked_data['Party'] == 'Democratic %']).mark_text(
    color='white',
    dx=-600
).encode(
    y=alt.Y("State:N", sort="-x"),
    x=alt.X("Percentage:Q", stack="normalize"),
    text=alt.Text('Percentage:Q', format=".1f")
)

republican_annotations = alt.Chart(stacked_data[stacked_data['Party'] == 'Republican %']).mark_text(
    color='white',
    dx=-15
).encode(
    y=alt.Y("State:N", sort="-x"),
    x=alt.X("Percentage:Q", stack="normalize"),
    text=alt.Text('Percentage:Q', format=".1f")
)

# Combine the chart and annotations
stacked_chart = stacked_chart + democratic_annotations + republican_annotations

# Summary Statistics
summary_df = filtered_df.groupby("State")[["Partisan Margin", "Minority Percentage"]].mean().reset_index()
summary_df = summary_df.round(2)

# KPI Cards
avg_margin = round(filtered_df["Partisan Margin"].mean(), 2)
avg_minority = round(filtered_df["Minority Percentage"].mean(), 2)
num_districts = len(filtered_df)

# Display Layout
st.markdown("### Key Metrics")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Average Vote Margin", avg_margin)
with col2:
    st.metric("Average Minority %", avg_minority)
with col3:
    st.metric("Number of Districts", num_districts)

st.markdown("### Visualizations")
col1, col2 = st.columns(2)
with col1:
    st.markdown("#### Partisan Margin by State")
    st.write('A boxplot showing the distribution of partisan vote margins across selected states. Each point represents a congressional district. Hover to inspect more details')
    st.altair_chart(combined_margin, use_container_width=True)
    st.markdown("#### Party Vote Composition by State")
    st.write("A bar chart displaying the average party composition across selected states.")
    st.altair_chart(stacked_chart, use_container_width=True)
with col2:
    st.markdown("#### Minority Share vs Partisan Margin")
    st.write("A scatterplot comparing the percentage of minorities living in a given district versus the partisan margin.")
    st.altair_chart(scatter, use_container_width=True)

st.markdown("### Summary Statistics")
st.write(summary_df)