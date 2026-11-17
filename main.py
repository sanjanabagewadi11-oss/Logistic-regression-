
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ==========================================================
# ABC AUTO COMPONENTS - MANUFACTURING DIGITALIZATION
# Three integrated business use cases
# ==========================================================

st.set_page_config(
    page_title="ABC Auto Components",
    page_icon="🏭",
    layout="wide"
)

# ----------------------------------------------------------
# 1. COMPANY INFORMATION
# ----------------------------------------------------------

COMPANY = "ABC Auto Components Pvt. Ltd."

MATERIALS = [
    "Steel Sheets",
    "Copper Wire",
    "Plastic Granules",
    "Bearings",
    "Packaging Boxes"
]

SUPPLIERS = {
    "Steel Sheets": "Tata Steel Supplier",
    "Copper Wire": "CopperTech",
    "Plastic Granules": "PolyMould",
    "Bearings": "Precision Bearings",
    "Packaging Boxes": "PackRight"
}

# ----------------------------------------------------------
# 2. GENERATE INTEGRATED SAMPLE DATASET
# ----------------------------------------------------------

@st.cache_data
def generate_data():

    rng = np.random.default_rng(42)

    # INBOUND MATERIAL DATA
    inbound = pd.DataFrame({
        "material": MATERIALS,
        "supplier": [
            "Tata Steel Supplier",
            "CopperTech",
            "PolyMould",
            "Precision Bearings",
            "PackRight"
        ],
        "daily_demand": [100, 30, 80, 20, 150],
        "current_stock": [450, 250, 600, 100, 1200],
        "avg_lead_time": [5, 4, 6, 7, 3],
        "lead_time_std": [1.5, 1, 2, 2, 0.5],
        "unit_cost": [75, 650, 110, 250, 12]
    })

    # OUTBOUND DELIVERY DATA
    orders = []

    stages = ["First Mile", "Mid Mile", "Last Mile"]

    planned_days = {
        "First Mile": 1,
        "Mid Mile": 2,
        "Last Mile": 1
    }

    stage_delay = {
        "First Mile": 0.4,
        "Mid Mile": 0.9,
        "Last Mile": 0.6
    }

    carriers = {
        "First Mile": "Carrier A",
        "Mid Mile": "Carrier B",
        "Last Mile": "Carrier C"
    }

    for order_number in range(101, 161):

        for stage in stages:

            actual = max(
                0.5,
                rng.normal(
                    planned_days[stage] + stage_delay[stage],
                    0.65
                )
            )

            orders.append({
                "order_id": f"ORD{order_number}",
                "stage": stage,
                "planned_days": planned_days[stage],
                "actual_days": round(actual, 2),
                "carrier": carriers[stage],
                "route": rng.choice(
                    ["Route North", "Route South", "Route West"]
                )
            })

    outbound = pd.DataFrame(orders)

    # SUPPLIER DISRUPTION DATA
    disruption = []

    for i in range(1, 51):

        material = rng.choice(MATERIALS)

        supplier = SUPPLIERS[material]

        expected_arrival = int(
            rng.integers(2, 9)
        )

        required_days = int(
            rng.integers(3, 8)
        )

        backup = {
            "Steel Sheets": "SteelSource Ltd",
            "Copper Wire": "ElectroMetals",
            "Plastic Granules": "No Backup",
            "Bearings": "BearingHub",
            "Packaging Boxes": "BoxMakers"
        }[material]

        disruption.append({
            "production_order": f"PO{i:03d}",
            "supplier": supplier,
            "material": material,
            "required_in_days": required_days,
            "expected_arrival_days": expected_arrival,
            "material_quantity": int(rng.integers(100, 1000)),
            "estimated_penalty": int(rng.integers(5000, 20000)),
            "backup_supplier": backup
        })

    disruption = pd.DataFrame(disruption)

    return inbound, outbound, disruption


inbound, outbound, disruption = generate_data()

# ----------------------------------------------------------
# 3. PAGE HEADER
# ----------------------------------------------------------

st.title("🏭 ABC Auto Components - Manufacturing Control Tower")

st.markdown(
    
    """
    **Company:** ABC Auto Components Pvt. Ltd.

    **Purpose:** Analyse raw material inventory, outbound delivery
    performance and supplier disruption risks using Python.
    """
)

st.divider()

# ----------------------------------------------------------
# 4. SIDEBAR SETTINGS
# ----------------------------------------------------------

st.sidebar.header("Analysis Settings")

safety_factor = st.sidebar.slider(
    "Inventory safety factor",
    min_value=0.5,
    max_value=3.0,
    value=1.65,
    step=0.05
)

additional_delay = st.sidebar.slider(
    "Simulate additional supplier delay (days)",
    min_value=0,
    max_value=15,
    value=3
)

st.sidebar.info(
    "Adjust these settings to see how inventory "
    "and supplier risks change."
)

# ----------------------------------------------------------
# 5. USE CASE 1 - INBOUND REORDER ANALYSIS
# ----------------------------------------------------------

def analyse_inbound(data, z_factor):

    result = data.copy()

    result["safety_stock"] = (
        z_factor
        * result["daily_demand"]
        * result["lead_time_std"]
    )

    result["reorder_point"] = (
        result["daily_demand"]
        * result["avg_lead_time"]
        + result["safety_stock"]
    )

    result["stock_status"] = np.where(
        result["current_stock"] <= result["reorder_point"],
        "Reorder Required",
        "Stock Sufficient"
    )

    result["stock_gap"] = (
        result["reorder_point"] - result["current_stock"]
    ).clip(lower=0)

    return result


inbound_result = analyse_inbound(inbound, safety_factor)

# ----------------------------------------------------------
# 6. USE CASE 2 - OUTBOUND DELIVERY ANALYSIS
# ----------------------------------------------------------

def analyse_outbound(data):

    result = data.copy()

    result["delay_days"] = (
        result["actual_days"] - result["planned_days"]
    ).clip(lower=0)

    result["delivery_status"] = np.where(
        result["actual_days"] > result["planned_days"],
        "Delayed",
        "On Time"
    )

    summary = result.groupby("stage").agg(
        total_records=("order_id", "count"),
        average_planned_days=("planned_days", "mean"),
        average_actual_days=("actual_days", "mean"),
        average_delay=("delay_days", "mean"),
        delayed_records=("delivery_status",
                         lambda x: (x == "Delayed").sum())
    ).reset_index()

    summary["delay_rate"] = (
        summary["delayed_records"]
        / summary["total_records"]
        * 100
    )

    return result, summary


outbound_result, outbound_summary = analyse_outbound(outbound)

# ----------------------------------------------------------
# 7. USE CASE 3 - SUPPLIER DISRUPTION SIMULATION
# ----------------------------------------------------------

def analyse_disruption(data, delay):

    result = data.copy()

    result["simulated_arrival"] = (
        result["expected_arrival_days"] + delay
    )

    result["risk_status"] = np.where(
        result["simulated_arrival"] >
        result["required_in_days"],
        "At Risk",
        "Safe"
    )

    result["penalty_exposure"] = np.where(
        result["risk_status"] == "At Risk",
        result["estimated_penalty"],
        0
    )

    result["backup_status"] = np.where(
        result["backup_supplier"] == "No Backup",
        "No Backup Available",
        "Backup Listed - Verify Capacity"
    )

    return result


disruption_result = analyse_disruption(
    disruption,
    additional_delay
)

# ----------------------------------------------------------
# 8. DASHBOARD TABS
# ----------------------------------------------------------

tab1, tab2, tab3, tab4 = st.tabs([
    "Inbound Reorder Analysis",
    "Outbound Delivery Analysis",
    "Supplier Disruption Simulator",
    "Complete Dataset"
])

# ==========================================================
# TAB 1 - INBOUND
# ==========================================================

with tab1:

    st.header("Use Case 1: Inbound Reorder Point Analysis")

    st.write(
        "Identifies raw materials that need to be reordered "
        "based on daily demand, supplier lead time and stock."
    )

    col1, col2, col3 = st.columns(3)

    reorder_count = (
        inbound_result["stock_status"] == "Reorder Required"
    ).sum()

    col1.metric(
        "Total Materials",
        len(inbound_result)
    )

    col2.metric(
        "Materials to Reorder",
        int(reorder_count)
    )

    col3.metric(
        "Materials Sufficient",
        len(inbound_result) - int(reorder_count)
    )

    st.subheader("Material Reorder Analysis")

    st.dataframe(
        inbound_result.round(2),
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Current Stock vs Reorder Point")

    fig, ax = plt.subplots(figsize=(10, 5))

    x = np.arange(len(inbound_result))
    width = 0.35

    ax.bar(
        x - width / 2,
        inbound_result["current_stock"],
        width,
        label="Current Stock"
    )

    ax.bar(
        x + width / 2,
        inbound_result["reorder_point"],
        width,
        label="Reorder Point"
    )

    ax.set_xticks(x)
    ax.set_xticklabels(
        inbound_result["material"],
        rotation=20
    )

    ax.set_ylabel("Quantity (units)")
    ax.set_title("Current Inventory vs Reorder Point")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    st.pyplot(fig)
    plt.close(fig)

    st.subheader("Business Findings")

    for _, row in inbound_result.iterrows():

        if row["stock_status"] == "Reorder Required":

            st.warning(
                f'{row["material"]}: Reorder required. '
                f'Stock gap against reorder point: '
                f'{row["stock_gap"]:.2f} units.'
            )

        else:

            st.success(
                f'{row["material"]}: Current stock is sufficient.'
            )

    st.download_button(
        "Download Inbound Analysis CSV",
        inbound_result.to_csv(index=False),
        file_name="inbound_analysis.csv",
        mime="text/csv"
    )

# ==========================================================
# TAB 2 - OUTBOUND
# ==========================================================

with tab2:

    st.header("Use Case 2: Outbound Delivery Delay Analysis")

    st.write(
        "Identifies delays in First Mile, Mid Mile and "
        "Last Mile transportation."
    )

    col1, col2, col3 = st.columns(3)

    total_orders = outbound_result["order_id"].nunique()

    delayed_records = (
        outbound_result["delivery_status"] == "Delayed"
    ).sum()

    col1.metric(
        "Total Customer Orders",
        total_orders
    )

    col2.metric(
        "Delayed Stage Records",
        int(delayed_records)
    )

    col3.metric(
        "Total Stage Records",
        len(outbound_result)
    )

    st.subheader("Delivery Stage Summary")

    st.dataframe(
        outbound_summary.round(2),
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Average Delay by Transportation Stage")

    fig, ax = plt.subplots(figsize=(9, 5))

    ax.bar(
        outbound_summary["stage"],
        outbound_summary["average_delay"]
    )

    ax.set_ylabel("Average Delay (Days)")
    ax.set_title("Average Delay by Delivery Stage")
    ax.grid(axis="y", alpha=0.3)

    st.pyplot(fig)
    plt.close(fig)

    st.subheader("Delay Rate by Stage")

    fig, ax = plt.subplots(figsize=(9, 5))

    ax.bar(
        outbound_summary["stage"],
        outbound_summary["delay_rate"]
    )

    ax.set_ylabel("Delayed Records (%)")
    ax.set_title("Delivery Delay Percentage by Stage")
    ax.grid(axis="y", alpha=0.3)

    st.pyplot(fig)
    plt.close(fig)

    st.subheader("Detailed Delivery Records")

    st.dataframe(
        outbound_result.round(2),
        use_container_width=True,
        hide_index=True
    )

    worst_stage = outbound_summary.loc[
        outbound_summary["average_delay"].idxmax(),
        "stage"
    ]

    st.warning(
        f"Attention: {worst_stage} has the highest average "
        "delay in this dataset."
    )

    st.download_button(
        "Download Outbound Analysis CSV",
        outbound_result.to_csv(index=False),
        file_name="outbound_analysis.csv",
        mime="text/csv"
    )

# ==========================================================
# TAB 3 - SUPPLIER DISRUPTION
# ==========================================================

with tab3:

    st.header("Use Case 3: Supplier Disruption Simulator")

    st.write(
        "Simulates additional supplier delivery delays and "
        "identifies production orders that may be affected."
    )

    selected_supplier = st.selectbox(
        "Select Supplier",
        ["All Suppliers"] + sorted(
            disruption_result["supplier"].unique().tolist()
        )
    )

    if selected_supplier == "All Suppliers":

        filtered = disruption_result.copy()

    else:

        filtered = disruption_result[
            disruption_result["supplier"] == selected_supplier
        ].copy()

    at_risk = (
        filtered["risk_status"] == "At Risk"
    ).sum()

    total_penalty = filtered["penalty_exposure"].sum()

    no_backup = (
        filtered["backup_status"] == "No Backup Available"
    ).sum()

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Production Orders at Risk",
        int(at_risk)
    )

    col2.metric(
        "Estimated Penalty Exposure",
        f"₹{total_penalty:,.0f}"
    )

    col3.metric(
        "Orders Without Backup Supplier",
        int(no_backup)
    )

    st.subheader("Supplier Disruption Results")

    st.dataframe(
        filtered.round(2),
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Required Arrival vs Simulated Arrival")

    material_summary = filtered.groupby("material").agg(
        required_day=("required_in_days", "mean"),
        simulated_day=("simulated_arrival", "mean")
    ).reset_index()

    fig, ax = plt.subplots(figsize=(10, 5))

    x = np.arange(len(material_summary))
    width = 0.35

    ax.bar(
        x - width / 2,
        material_summary["required_day"],
        width,
        label="Required Arrival"
    )

    ax.bar(
        x + width / 2,
        material_summary["simulated_day"],
        width,
        label="Simulated Arrival"
    )

    ax.set_xticks(x)
    ax.set_xticklabels(
        material_summary["material"],
        rotation=20
    )

    ax.set_ylabel("Days")
    ax.set_title("Production Requirement vs Simulated Arrival")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    st.pyplot(fig)
    plt.close(fig)

    st.subheader("Recommended Actions")

    if at_risk > 0:

        st.warning(
            f"{at_risk} production orders may be affected "
            "by the selected disruption scenario."
        )

    else:

        st.success(
            "No production orders are at risk in this scenario."
        )

    if no_backup > 0:

        st.warning(
            f"{no_backup} orders have no backup supplier listed. "
            "Identify alternative suppliers."
        )

    st.info(
        "Verify actual backup supplier capacity, available "
        "inventory and production requirements before making "
        "purchasing decisions."
    )

    st.download_button(
        "Download Disruption Analysis CSV",
        filtered.to_csv(index=False),
        file_name="supplier_disruption_analysis.csv",
        mime="text/csv"
    )

# ==========================================================
# TAB 4 - COMPLETE DATASET
# ==========================================================

with tab4:

    st.header("Complete Company Dataset")

    st.write(
        "These are the sample records used by all three "
        "business use cases."
    )

    dataset_choice = st.selectbox(
        "Select Dataset",
        [
            "Inbound Materials",
            "Outbound Deliveries",
            "Supplier Disruption"
        ]
    )

    if dataset_choice == "Inbound Materials":

        st.dataframe(
            inbound,
            use_container_width=True,
            hide_index=True
        )

    elif dataset_choice == "Outbound Deliveries":

        st.dataframe(
            outbound,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.dataframe(
            disruption,
            use_container_width=True,
            hide_index=True
        )

    st.success(
        "All three use cases use the same ABC Auto Components "
        "company example."
    )

# ----------------------------------------------------------
# FOOTER
# ----------------------------------------------------------

st.divider()

st.caption(
    "ABC Auto Components Pvt. Ltd. | Manufacturing "
    "Digitalization Project | Python, NumPy, Pandas, "
    "Matplotlib and Streamlit"
)
