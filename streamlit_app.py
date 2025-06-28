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

# Unsure how this could work but lets hope it does
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



if len(filtered_df) < 5:
    st.warning(
        f"⚠️ Only {len(filtered_df)} congressional district{'s' if len(filtered_df) == 1 else 's'} found based on your current filters. "
        "You may want to broaden your selection for a more meaningful analysis."
    )

else:

    st.markdown("### Visualizations")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Partisan Margin by State")
        st.caption("A boxplot with overlaid points showing vote margins by congressional district.")
        
        box = alt.Chart(filtered_df).mark_boxplot(
            extent="min-max",
            size=30,
            color="gray",
        ).encode(
            x=alt.X("State:N"),
            y=alt.Y("Partisan Margin:Q", axis=alt.Axis(format=".2f"))
        )

        points = alt.Chart(filtered_df).mark_circle(size=60, opacity=0.5).encode(
            x="State:N",
            y=alt.Y("Partisan Margin:Q", axis=alt.Axis(format=".2f")),
            color=color,
            tooltip=[
                alt.Tooltip("CD_Num:N"),
                alt.Tooltip("Partisan Margin:Q", format=".2f")
            ]
        )

        st.altair_chart(box + points, use_container_width=True)

        st.markdown("### Vote Share Breakdown by Party")

        # Use same vote_grouped data (reuse or regenerate if needed)
        vote_df = df[df["State"].isin(selected_states)].copy()
        vote_df = vote_df[vote_df["E_16-20_COMP_Total"] > 0]
        vote_grouped = vote_df.groupby("State")[["E_16-20_COMP_Dem", "E_16-20_COMP_Rep", "E_16-20_COMP_Total"]].sum().reset_index()
        vote_grouped["Democratic %"] = (vote_grouped["E_16-20_COMP_Dem"] / vote_grouped["E_16-20_COMP_Total"]) * 100
        vote_grouped["Republican %"] = (vote_grouped["E_16-20_COMP_Rep"] / vote_grouped["E_16-20_COMP_Total"]) * 100

        # Democratic Vote Bar Chart
        dem_chart = alt.Chart(vote_grouped).mark_bar(color="#00AEF3").encode(
            y=alt.Y("State:N", sort=alt.EncodingSortField(field="Democratic %", order="ascending")),
            x=alt.X("Democratic %:Q", title="Democratic Vote %"),
            tooltip=["State", alt.Tooltip("Democratic %:Q", format=".1f")]
        ).properties(
            title="Democratic Vote Share by State",
            width=400,
            height=450
        )

        # Republican Vote Bar Chart
        rep_chart = alt.Chart(vote_grouped).mark_bar(color="#E81B23").encode(
            y=alt.Y("State:N", sort=alt.EncodingSortField(field="Republican %", order="descending")),
            x=alt.X("Republican %:Q", title="Republican Vote %"),
            tooltip=["State", alt.Tooltip("Republican %:Q", format=".1f")]
        ).properties(
            title="Republican Vote Share by State",
            width=400,
            height=450
        )

        # Side-by-side layout
        colA, colB = st.columns(2)
        with colA:
            st.altair_chart(dem_chart, use_container_width=True)
        with colB:
            st.altair_chart(rep_chart, use_container_width=True)


    with col2:
        st.markdown("#### Minority Share vs. Partisan Margin")
        st.caption("Explores how minority presence relates to party advantage.")

        scatter = alt.Chart(filtered_df).mark_circle(size=60).encode(
            x=alt.X(demo_col, title=f"{selected_demo} %"),
            y=alt.Y("Partisan Margin:Q", axis=alt.Axis(format=".2f")),
            color=color,
            tooltip=[
                "CD_Num", "State",
                alt.Tooltip(demo_col, format=".2f"),
                alt.Tooltip("Partisan Margin:Q", format=".2f")
            ]
        )

        rule = alt.Chart(pd.DataFrame({'x': [50]})).mark_rule(
            strokeDash=[2, 2], color='red'
        ).encode(x='x:Q')

        st.altair_chart(scatter + rule, use_container_width=True)

        st.markdown("### 🔍 Demographics & Voting Correlation Matrix")
        st.caption("This heatmap shows the Pearson correlation between racial/ethnic group proportions and voting patterns across districts.")

        # Select columns for correlation
        corr_cols = [
            "Minority Percentage", "Black %", "Hispanic %", "Asian %", "Native %", "Pacific %",
            "Democratic %", "Republican %", "Partisan Margin"
        ]

        # Compute correlation matrix
        corr_df = (
            filtered_df[corr_cols]
            .corr()
            .loc[["Minority Percentage", "Black %", "Hispanic %", "Asian %", "Native %", "Pacific %"],  # rows
                ["Democratic %", "Republican %", "Partisan Margin"]]  # cols
            .round(2)
            .reset_index()
            .melt(id_vars="index", var_name="Vote Metric", value_name="Correlation")
            .rename(columns={"index": "Demographic"})
        )

        # Heatmap chart
        heatmap = alt.Chart(corr_df).mark_rect().encode(
            x=alt.X("Vote Metric:N", title="Voting Variable"),
            y=alt.Y("Demographic:N", title="Demographic Group"),
            color=alt.Color("Correlation:Q", scale=alt.Scale(scheme="redblue", domain=(-1, 1))),
            tooltip=[
                "Demographic", "Vote Metric",
                alt.Tooltip("Correlation:Q", format=".2f")
            ]
        ).properties(width=500, height=400)

        # Add numeric annotations
        text = alt.Chart(corr_df).mark_text(baseline="middle").encode(
            x="Vote Metric:N",
            y="Demographic:N",
            text=alt.Text("Correlation:Q", format=".2f"),
            color=alt.condition(
                "datum.Correlation > 0.5 || datum.Correlation < -0.5",
                alt.value("white"),
                alt.value("black")
            )
        )

        st.altair_chart(heatmap + text, use_container_width=True)


    st.markdown("### Summary Statistics")
    summary_df = filtered_df.groupby("State")[["Partisan Margin", "Minority Percentage"]].mean().reset_index().round(2)
    st.dataframe(summary_df)

# --- Key Insights / Takeaways Section ---
st.markdown("### 📌 Key Insights")
st.info(
    """
    **1. Minority populations often correlate with more Democratic-leaning districts**, especially where the Black population is a major demographic. 
    States like **Georgia and North Carolina** show this more clearly in competitive areas.

    **2. Conservative states still contain diverse districts** with high minority populations — however, many of these districts still show strong Republican margins, indicating potential effects of district design or turnout.

    **3. States with Independent Commissions (like Virginia)** tend to show slightly more balanced or moderate voting patterns, compared to those with partisan-controlled redistricting.

    **4. There is significant variation within states**, so state-level averages may obscure important district-level dynamics.

    Use the filters above to explore these patterns and generate your own insights!
    """
)