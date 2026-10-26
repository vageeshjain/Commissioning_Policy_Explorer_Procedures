import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

# Load Excel workbook
xls = pd.ExcelFile("EBI_RV_v5_suppfile2_tableonly.xlsx")

raw = pd.read_excel(
    xls,
    sheet_name=0,
    header=0
)

procedure_col = raw.columns[0]

count_cols = [
    "EBI (criteria)",
    "EBI (do not fund)",
    "Not in EBI",
    "Signpost to national guidance",
    "Under Review",
    "Total"
]

icb_cols = [
    c for c in raw.columns
    if c not in [procedure_col] + count_cols
]

status_map = {
    "✓": "FWC",
    "IFR": "IFR",
    "NG": "Other (Signpost / Under Review)",
    "UR": "Other (Signpost / Under Review)",
    "N/A": "No Policy Listed"
}

df = raw.copy()
df = df[df[procedure_col].notna()].copy()

for col in icb_cols:
    df[col] = (
        df[col]
        .replace(status_map)
        .fillna("No Policy Listed")
    )

procedures = ["All"] + sorted(
    df[procedure_col]
    .astype(str)
    .tolist()
)

icbs = ["All"] + list(icb_cols)

statuses = [
    "All",
    "FWC",
    "IFR",
    "Other (Signpost / Under Review)",
    "No Policy Listed"
]

def top_n_with_ties(df_in, sort_col, n=20):
    ranked = df_in.sort_values(
        sort_col,
        ascending=False
    )
    if len(ranked) >= n:
        cutoff = ranked.iloc[n - 1][sort_col]
        return ranked[ranked[sort_col] >= cutoff]
    return ranked

if "page" not in st.session_state:
    st.session_state.page = "National Dashboard"

st.sidebar.markdown("## Navigation")

if st.sidebar.button("📊 National Dashboard"):
    st.session_state.page = "National Dashboard"

if st.sidebar.button("🔍 Policy Explorer"):
    st.session_state.page = "Policy Explorer"

page = st.session_state.page

st.title("NHS Commissioning Policy Explorer")
st.markdown(
    "### A national dashboard of criteria-based procedure policies across English Integrated Care Boards"
)

with st.expander("About, Disclaimer and Citation"):
    st.write(
        """
        **Disclaimer**

        Data were extracted in 2025. Local commissioning policies may have changed since data collection.

        **Citation**

        Smyth et al. Access to criteria-based procedures in the National Health Service in England: a comparative policy analysis. BMJ Open, 2026.

        **Dashboard**

        EBI Observatory. Interactive tool for exploring variation in commissioning policies across English Integrated Care Boards.
        """
    )

with st.expander("Key"):
    st.write("FWC = Funded With Criteria")
    st.write("IFR = Individual Funding Request")
    st.write("Other = Signpost to National Guidance or Policy Under Review")

variation = []

for _, row in df.iterrows():
    variation.append({
        "Procedure": row[procedure_col],
        "FWC %": round(
            row["EBI (criteria)"] / 42 * 100,
            1
        ),
        "IFR %": round(
            row["EBI (do not fund)"] / 42 * 100,
            1
        ),
        "Other %": round(
            (
                row["Signpost to national guidance"]
                + row["Under Review"]
            ) / 42 * 100,
            1
        ),
        "No Policy %": round(
            row["Not in EBI"] / 42 * 100,
            1
        )
    })

var_df = pd.DataFrame(variation)

if page == "Policy Explorer":

    c1, c2, c3 = st.columns(3)

    with c1:
        selected_proc = st.selectbox(
            "Procedure",
            procedures
        )

    with c2:
        selected_icb = st.selectbox(
            "ICB",
            icbs
        )

    with c3:
        selected_status = st.selectbox(
            "Status",
            statuses
        )

    if selected_proc != "All" and selected_icb == "All":
        row = df[
            df[procedure_col] == selected_proc
        ].iloc[0]

        result = pd.DataFrame({
            "ICB": icb_cols,
            "Status": [
                row[x]
                for x in icb_cols
            ]
        })

        if selected_status != "All":
            result = result[
                result["Status"] == selected_status
            ]

        st.dataframe(
            result.reset_index(drop=True),
            use_container_width=True
        )

    elif selected_icb != "All" and selected_proc == "All":
        result = pd.DataFrame({
            "Procedure": df[procedure_col],
            "Status": df[selected_icb]
        })

        if selected_status != "All":
            result = result[
                result["Status"] == selected_status
            ]

        total = len(result)
        fwc = len(result[result["Status"] == "FWC"])
        ifr = len(result[result["Status"] == "IFR"])
        other = len(
            result[
                result["Status"]
                ==
                "Other (Signpost / Under Review)"
            ]
        )
        none = len(
            result[
                result["Status"]
                ==
                "No Policy Listed"
            ]
        )

        a, b, c, d = st.columns(4)
        a.metric(
            "FWC",
            f"{fwc} ({round(fwc/total*100,1) if total > 0 else 0}%)"
        )
        b.metric(
            "IFR",
            f"{ifr} ({round(ifr/total*100,1) if total > 0 else 0}%)"
        )
        c.metric(
            "Other",
            f"{other} ({round(other/total*100,1) if total > 0 else 0}%)"
        )
        d.metric(
            "No Policy",
            f"{none} ({round(none/total*100,1) if total > 0 else 0}%)"
        )

        st.dataframe(
            result.reset_index(drop=True),
            use_container_width=True
        )

    elif selected_icb != "All" and selected_proc != "All":
        row = df[
            df[procedure_col] == selected_proc
        ].iloc[0]

        value = row[selected_icb]

        st.subheader(selected_proc)

        if value == "FWC":
            st.success("✅ Funded With Criteria (FWC)")
        elif value == "IFR":
            st.warning("⚠️ Individual Funding Request (IFR)")
        elif value == "Other (Signpost / Under Review)":
            st.info("ℹ️ Signpost to National Guidance / Under Review")
        else:
            st.error("❌ No Policy Listed")

elif page == "National Dashboard":

    show_only_variable = st.checkbox(
        "Show only procedures with variation between ICBs",
        value=False
    )

    dashboard_df = var_df.copy()

    # This 'if' block only runs if the checkbox is checked (True). 
    # Since value=False, this code is skipped entirely and all 163 rows flow through!
    if show_only_variable:
        dashboard_df = dashboard_df[
            (
                (dashboard_df["FWC %"] > 0)
                & (dashboard_df["FWC %"] < 100)
            )
            |
            (
                (dashboard_df["IFR %"] > 0)
                & (dashboard_df["IFR %"] < 100)
            )
        ]
