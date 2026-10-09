import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

xls = pd.ExcelFile("EBI_RV_v3.xlsx")
df = pd.read_excel(xls, sheet_name=0)
ri_df = pd.read_excel(
    xls,
    sheet_name="RI and CVI",
    header=None
)

ri_df = ri_df.iloc[:, 2:10]

ri_df.columns = [
    "Procedure",
    "FWC",
    "IFR",
    "Other",
    "Documentation Completeness",
    "Restriction Index",
    "All-ICB CVI",
    "Decision-based CVI"
]

ri_df = ri_df.iloc[2:].reset_index(drop=True)

ri_df = ri_df[
    ri_df["Procedure"].notna()
]

ri_df["Restriction Index"] = pd.to_numeric(
    ri_df["Restriction Index"],
    errors="coerce"
)

ri_df["All-ICB CVI"] = pd.to_numeric(
    ri_df["All-ICB CVI"],
    errors="coerce"
)

ri_df["Decision-based CVI"] = pd.to_numeric(
    ri_df["Decision-based CVI"],
    errors="coerce"
)

ri_df["Documentation Completeness"] = pd.to_numeric(
    ri_df["Documentation Completeness"],
    errors="coerce"
)
procedure_col = df.columns[0]
icb_cols = df.columns[1:43]

df = df.replace("ü", "FWC")
df = df.replace("✓", "FWC")

df[procedure_col] = (
    df[procedure_col]
    .astype(str)
    .str.strip()
)

procedures = [
    x for x in df[procedure_col].dropna().unique().tolist()
    if "%" not in str(x)
]

procedures = ["All"] + sorted(procedures)

icbs = ["All"] + list(icb_cols)

statuses = [
    "All",
    "FWC",
    "IFR",
    "Policy under review",
    "No Policy Listed"
]

if "page" not in st.session_state:
    st.session_state.page = "National Dashboard"

st.sidebar.markdown("## Navigation")

if st.sidebar.button("📊 National Dashboard"):
    st.session_state.page = "National Dashboard"

if st.sidebar.button("📈 Restriction Index & CVI"):
    st.session_state.page = "Restriction Index & CVI"

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

        Data were extracted in 2025. Local commissioning policies may have changed since data collection. Users should verify current policies directly with the relevant Integrated Care Board before relying on the information presented.

        **Citation**

        For methods and data sources see:

        Smyth et al. *Access to criteria-based procedures in the National Health Service in England: a comparative policy analysis*. BMJ Open, 2026.

        **Dashboard**

        EBI Observatory. Interactive tool for exploring variation in commissioning policies, Restriction Index (RI) and Commissioning Variation Index (CVI) across English ICBs.
        """
    )
with st.expander("Key"):
    st.write("FWC = Funded With Criteria")
    st.write("IFR = Individual Funding Request")

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

        row = df[df[procedure_col] == selected_proc].iloc[0]

        result = pd.DataFrame({
            "ICB": icb_cols,
            "Status": [
                "No Policy Listed" if pd.isna(row[x]) else row[x]
                for x in icb_cols
            ]
        })

        if selected_status != "All":
            result = result[result["Status"] == selected_status]

        total = len(result)

        fwc = len(result[result["Status"] == "FWC"])
        ifr = len(result[result["Status"] == "IFR"])
        none = len(result[result["Status"] == "No Policy Listed"])

        st.dataframe(
            result,
            use_container_width=True
        )

    elif selected_icb != "All" and selected_proc == "All":

        result = pd.DataFrame({
            "Procedure": df[procedure_col],
            "Status": df[selected_icb]
        })

        result["Status"] = result["Status"].fillna(
            "No Policy Listed"
        )

        if selected_status != "All":
            result = result[result["Status"] == selected_status]

        total = len(result)

        fwc = len(result[result["Status"] == "FWC"])
        ifr = len(result[result["Status"] == "IFR"])
        none = len(result[result["Status"] == "No Policy Listed"])

        a, b, c = st.columns(3)

        a.metric(
            "FWC",
            f"{fwc} ({round(fwc/total*100,1)}%)"
        )

        b.metric(
            "IFR",
            f"{ifr} ({round(ifr/total*100,1)}%)"
        )

        c.metric(
            "No Policy",
            f"{none} ({round(none/total*100,1)}%)"
        )

        st.dataframe(
            result,
            use_container_width=True
        )

    elif selected_icb != "All" and selected_proc != "All":

        row = df[df[procedure_col] == selected_proc].iloc[0]

        value = row[selected_icb]

        if pd.isna(value):
            value = "No Policy Listed"

        st.subheader(selected_proc)

        if value == "FWC":
            st.success("✅ Funded With Criteria (FWC)")
        elif value == "IFR":
            st.warning("⚠️ Individual Funding Request (IFR)")
        elif value == "Policy under review":
            st.info("🔵 Policy Under Review")
        else:
            st.error(f"❌ {value}")

elif page == "National Dashboard":

    variation = []

    for _, row in df.iterrows():

        vals = pd.Series(
            [row[x] for x in icb_cols]
        ).fillna("No Policy Listed")

        total = len(vals)

        variation.append({
            "Procedure": row[procedure_col],
            "FWC %": round(sum(vals == "FWC") / total * 100, 1),
            "IFR %": round(sum(vals == "IFR") / total * 100, 1),
            "No Policy %": round(sum(vals == "No Policy Listed") / total * 100, 1)
        })

    var_df = pd.DataFrame(variation)

    show_only_variable = st.checkbox(
        "Show only procedures with variation between ICBs",
        value=True
    )

    if show_only_variable:
        var_df = var_df[
            (var_df["FWC %"] > 0)
            & (var_df["FWC %"] < 100)
        ]

    a, b, c, d, e = st.columns(5)

    a.metric(
        "Procedures",
        len(var_df)
    )

    b.metric(
        "ICBs",
        len(icb_cols)
    )

    c.metric(
        "Mean FWC %",
        f"{round(var_df['FWC %'].mean(),1)}%"
    )

    d.metric(
        "Mean IFR %",
        f"{round(var_df['IFR %'].mean(),1)}%"
    )

    e.metric(
        "Mean No Policy %",
        f"{round(var_df['No Policy %'].mean(),1)}%"
    )

    st.subheader("Highest IFR Procedures")

    st.dataframe(
        var_df.sort_values(
            "IFR %",
            ascending=False
        ).head(20),
        use_container_width=True
    )

    st.subheader("Highest FWC Procedures")

    st.dataframe(
        var_df.sort_values(
            "FWC %",
            ascending=False
        ).head(20),
        use_container_width=True
    )

    st.subheader("All Procedures")

    st.dataframe(
        var_df.sort_values(
            "Procedure"
        ),
        use_container_width=True
    )
elif page == "Restriction Index & CVI":
    st.subheader("Restriction Index & CVI")

    procedure = st.selectbox(
        "Procedure",
        ["All"] + sorted(
            ri_df["Procedure"]
            .astype(str)
            .unique()
            .tolist()
        )
    )

    if procedure != "All":

        row = ri_df[
            ri_df["Procedure"].astype(str)
            == procedure
        ].iloc[0]

        a, b, c, d = st.columns(4)

        a.metric(
            "Restriction Index",
            round(row["Restriction Index"], 2)
            if pd.notna(row["Restriction Index"])
            else "N/A"
        )

        b.metric(
            "Documentation Completeness",
            f"{round(row['Documentation Completeness'],1)}%"
            if pd.notna(row["Documentation Completeness"])
            else "N/A"
        )

        c.metric(
            "All-ICB CVI",
            f"{round(row['All-ICB CVI'],1)}%"
            if pd.notna(row["All-ICB CVI"])
            else "N/A"
        )

        d.metric(
            "Decision-based CVI",
            f"{round(row['Decision-based CVI'],1)}%"
            if pd.notna(row["Decision-based CVI"])
            else "N/A"
        )

    st.subheader("Most Restrictive Procedures")

    st.dataframe(
        ri_df[
            ri_df["Restriction Index"].notna()
        ]
        .sort_values(
            "Restriction Index",
            ascending=False
        )[
            [
                "Procedure",
                "Restriction Index",
                "Decision-based CVI"
            ]
        ],
        use_container_width=True
    )

    st.subheader("Most Variable Procedures")

    st.dataframe(
        ri_df[
            ri_df["Decision-based CVI"].notna()
        ]
        .sort_values(
            "Decision-based CVI",
            ascending=False
        )[
            [
                "Procedure",
                "Decision-based CVI",
                "Restriction Index"
            ]
        ],
        use_container_width=True
    )
