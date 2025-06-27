import streamlit as st
import pandas as pd
import altair as alt
import random

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

with st.expander("\U0001F4D6 Key Terms"):
    st.markdown("""
    - **Partisan Margin**: Difference between Republican and Democratic % (Rep% - Dem%). A positive value indicates Republican lead; a negative value indicates Democratic lead.
    - **Minority %**: Total non-white population as a percentage of district population.
    - **Boxplot**: Visual summary of the spread and skewness of a dataset.
    """)

colA, colB, colC = st.columns(3)
with colA:
    state_group = st.selectbox("State Group", list(state_groups.keys()))
    selected_states = (
        sorted(df["State"].unique()) if state_group == "All States"
        else state_groups[state_group]
    )
    selected_states = st.multiselect(
        "States (customizable)", sorted(df["State"].unique()),
        default=selected_states
    )

with colB:
    selected_group = st.selectbox("Minority % Group", ["All", "Below 35%", "35–50%", "50–75%", "75%+"])

with colC:
    selected_demo = st.selectbox("Demographic Focus", ["Total Minority", "Hispanic", "Black", "Asian", "Native", "Pacific"])

# -- Contextual Narratives --
st.markdown("### Context")
st.info(f"**State Group:** {evaluation_contexts[state_group]}")
st.caption(f"**Demographic Focus:** {demo_contexts[selected_demo]}")

# -- Filter Data --
filtered_df = df[df["State"].isin(selected_states)]
if selected_group != "All":
    ranges = {
        "Below 35%": (0, 35), "35–50%": (35, 50),
        "50–75%": (50, 75), "75%+": (75, 100)
    }
    lo, hi = ranges[selected_group]
    filtered_df = filtered_df[(filtered_df["Minority Percentage"] >= lo) & (filtered_df["Minority Percentage"] < hi)]

demo_col = "Minority Percentage" if selected_demo == "Total Minority" else f"{selected_demo} %"

# -- Color palette --

safe_colors = [
    "#E69F00", "#56B4E9", "#009E73", "#F0E442",
    "#0072B2", "#D55E00", "#CC79A7", "#999999"
]
unique_states = sorted(filtered_df["State"].unique())
safe_12_colors = [
    "#E69F00", "#56B4E9", "#009E73", "#F0E442",
    "#0072B2", "#D55E00", "#CC79A7", "#999999",
    "#117733", "#88CCEE", "#DDCC77", "#AA4499"
]
palette = alt.Scale(domain=unique_states, range=safe_12_colors[:len(unique_states)])
color = alt.Color("State:N", scale=palette)

# -- Charts --
st.markdown("### Key Metrics")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Average Vote Margin", round(filtered_df["Partisan Margin"].mean(), 2))
with col2:
    st.metric("Average Minority %", round(filtered_df["Minority Percentage"].mean(), 2))
with col3:
    st.metric("Number of Districts", len(filtered_df))

st.markdown("### Visualizations")
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Partisan Margin by State")
    st.caption("A boxplot with overlaid points showing vote margins by congressional district.")
    
    
    box = alt.Chart(filtered_df).mark_boxplot(
    extent="min-max",
    size=30,
    color="lightgray"
    ).encode(
    x=alt.X("State:N"),
    y=alt.Y("Partisan Margin:Q", format=".2f")
    )
    points = alt.Chart(filtered_df).mark_circle(size=60, opacity=0.5).encode(
        x="State:N",
        y="Partisan Margin:Q",
        color=color,
        tooltip=[alt.Tooltip("CD_Num:N"), alt.Tooltip("Partisan Margin:Q", format=".2f")]
    )
    st.altair_chart(box + points, use_container_width=True)

    st.markdown("#### Party Vote Composition by State")
    st.caption("This chart displays the average party vote share per state, based on composite data from 2016–2020 elections.")

    # Clean and filter the data
    vote_df = df[df["State"].isin(selected_states)].copy()
    vote_df = vote_df[vote_df["E_16-20_COMP_Total"] > 0]

    # Aggregate by state
    vote_grouped = vote_df.groupby("State")[["E_16-20_COMP_Dem", "E_16-20_COMP_Rep", "E_16-20_COMP_Total"]].sum().reset_index()

    vote_grouped["Democratic %"] = (vote_grouped["E_16-20_COMP_Dem"] / vote_grouped["E_16-20_COMP_Total"]) * 100
    vote_grouped["Republican %"] = (vote_grouped["E_16-20_COMP_Rep"] / vote_grouped["E_16-20_COMP_Total"]) * 100
    vote_grouped["Other %"] = 100 - vote_grouped["Democratic %"] - vote_grouped["Republican %"]

    vote_long = vote_grouped[["State", "Democratic %", "Republican %", "Other %"]].melt(
        id_vars="State", var_name="Party", value_name="Percentage"
    )

    bar = alt.Chart(vote_long).mark_bar().encode(
        y=alt.Y("State:N", sort="-x"),
        x=alt.X("Percentage:Q", stack="normalize", title="Vote Share"),
        color=alt.Color("Party:N", scale=alt.Scale(
            domain=["Democratic %", "Republican %", "Other %"],
            range=["#00AEF3", "#E81B23", "#808080"]
        )),
        tooltip=["State", "Party", alt.Tooltip("Percentage:Q", format=".1f")]
    ).properties(width=600, height=400)
    
    st.altair_chart(bar, use_container_width=True)

with col2:
    st.markdown("#### Minority Share vs. Partisan Margin")
    st.caption("Explores how minority presence relates to party advantage.")
    scatter = alt.Chart(filtered_df).mark_circle(size=60).encode(
        x=alt.X(demo_col, title=f"{selected_demo} %"),
        y=alt.Y("Partisan Margin:Q", format = ".2f"),
        color=color,
        tooltip=["CD_Num", "State", alt.Tooltip(demo_col, format=".2f"), alt.Tooltip("Partisan Margin:Q", format=".2f")]
    )
    rule = alt.Chart(pd.DataFrame({'x': [50]})).mark_rule(strokeDash=[2, 2], color='red').encode(x='x:Q')
    st.altair_chart(scatter + rule, use_container_width=True)

with st.expander("📋 View Vote % Table"):
    st.dataframe(vote_grouped[["State", "Democratic %", "Republican %", "Other %"]].round(1))

# -- Summary Table --
st.markdown("### Summary Statistics")
summary_df = filtered_df.groupby("State")[["Partisan Margin", "Minority Percentage"]].mean().reset_index().round(2)
st.dataframe(summary_df) 