import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(page_title="Manufacturing Digitalization Control Tower", page_icon="🏭", layout="wide")

# ---------- Theme / helpers ----------
st.markdown("""
<style>
.block-container {padding-top: 1.6rem; padding-bottom: 2rem;}
.hero {padding: 1.2rem 1.4rem; border-radius: 16px; background: linear-gradient(120deg,#102a43,#176b87); color:white; margin-bottom:1rem;}
.hero h1 {margin:0; font-size:2rem;} .hero p {margin:.4rem 0 0 0; opacity:.9;}
.small-note {color:#6b7280; font-size:.88rem;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>🏭 Manufacturing Digitalization Control Tower</h1><p>One workspace • Three use cases • From supplier variability to delivery performance and disruption response</p></div>', unsafe_allow_html=True)
st.caption("Demo data is synthetic. Upload your own CSVs using the column templates described in each tab before using results for business decisions.")

def csv_download(df, filename, label):
    st.download_button(label, df.to_csv(index=False).encode("utf-8"), file_name=filename, mime="text/csv")

def read_upload(uploaded, fallback):
    if uploaded is None:
        return fallback.copy(), "Built-in demo data"
    try:
        df = pd.read_csv(uploaded)
        return df, uploaded.name
    except Exception as e:
        st.error(f"Could not read CSV: {e}")
        return fallback.copy(), "Built-in demo data"

def missing_cols(df, cols):
    return [c for c in cols if c not in df.columns]

def metric_row(items):
    cols = st.columns(len(items))
    for col, (label, value, help_text) in zip(cols, items):
        col.metric(label, value, help=help_text)

# ---------- Demo datasets ----------
rng = np.random.default_rng(27)
n1 = 180
suppliers = np.array(["SUP-A", "SUP-B", "SUP-C", "SUP-D", "SUP-E"])
quoted = rng.choice([3, 4, 5, 6, 7], n1, p=[.1,.2,.3,.25,.15])
actual = np.maximum(1, np.round(quoted + rng.normal([0,1,0,2,1][0], 1.7, n1))).astype(int)
# Add distinct supplier effects
supplier1 = rng.choice(suppliers, n1)
for i, s in enumerate(suppliers):
    mask = supplier1 == s
    actual[mask] = np.maximum(1, np.round(quoted[mask] + rng.normal([0.2,1.8,0.5,2.4,1.2][i], [0.8,1.8,1.0,2.2,1.4][i], mask.sum()))).astype(int)
daily_demand = rng.integers(15, 75, n1)
inventory = rng.integers(100, 700, n1)
case1_demo = pd.DataFrame({
    "supplier": supplier1,
    "material": rng.choice(["Steel Coil","Resin","Copper Wire","Fasteners","Packaging"], n1),
    "quoted_lead_time_days": quoted,
    "actual_lead_time_days": actual,
    "daily_demand_units": daily_demand,
    "current_stock_units": inventory,
    "unit_cost": rng.uniform(2, 40, n1).round(2)
})

n2=240
order_ids=[f"ORD-{i:04d}" for i in range(1,n2+1)]
stage_rows=[]
for oid in order_ids:
    route=rng.choice(["Route North","Route South","Route East","Route West"])
    base_delays={"First Mile":rng.normal(.4,.8),"Mid Mile":rng.normal(.8,1.5),"Last Mile":rng.normal(1.1,1.8)}
    for stage in ["First Mile","Mid Mile","Last Mile"]:
        plan=float(rng.integers(1,5) if stage!="Mid Mile" else rng.integers(2,7))
        stage_delay=max(-.5,base_delays[stage]+rng.normal(0,.8))
        actual_days=max(.25,plan+stage_delay)
        stage_rows.append((oid,route,stage,round(plan,2),round(actual_days,2),rng.choice(["Carrier X","Carrier Y","Carrier Z"])))
case2_demo=pd.DataFrame(stage_rows,columns=["order_id","route","stage","planned_days","actual_days","carrier"])

# Case 3: supplier disruption order/material impact data
n3=90
supplier3=rng.choice(["SUP-A","SUP-B","SUP-C","SUP-D","SUP-E"],n3,p=[.2,.24,.18,.23,.15])
backup_map={"SUP-A":"SUP-X","SUP-B":"No backup","SUP-C":"SUP-Y","SUP-D":"SUP-Z","SUP-E":"No backup"}
case3_demo=pd.DataFrame({
    "supplier_id":supplier3,
    "material":rng.choice(["Steel Coil","Resin","Copper Wire","Fasteners","Packaging"],n3),
    "production_order":[f"PO-{i:04d}" for i in range(1,n3+1)],
    "customer_order":[f"CO-{i:04d}" for i in range(1,n3+1)],
    "required_in_days":rng.integers(4,18,n3),
    "expected_arrival_in_days":rng.integers(1,13,n3),
    "material_qty":rng.integers(20,500,n3),
    "estimated_penalty":rng.integers(100,2500,n3),
    "backup_supplier":[backup_map[s] for s in supplier3]
})

tab1, tab2, tab3, tab4 = st.tabs([
    "① Inbound Reorder Optimizer", "② Outbound Delay Detective", "③ Supplier Disruption Simulator", "Data & How to Use"
])

# ---------- Use case 1 ----------
with tab1:
    st.subheader("Inbound | Reorder points under supplier variability")
    st.write("Estimate a reorder point using actual supplier lead-time variation, rather than relying only on a quoted lead time and a flat buffer.")
    uploaded = st.file_uploader("Upload inbound / supplier lead-time CSV", type="csv", key="inbound")
    df, source = read_upload(uploaded, case1_demo)
    required=["supplier","quoted_lead_time_days","actual_lead_time_days","daily_demand_units","current_stock_units"]
    miss=missing_cols(df, required)
    if miss:
        st.error("Missing required columns: " + ", ".join(miss))
        st.info("Use the sample template available in the Data & How to Use tab.")
    else:
        for c in ["quoted_lead_time_days","actual_lead_time_days","daily_demand_units","current_stock_units"]:
            df[c]=pd.to_numeric(df[c],errors="coerce")
        df=df.dropna(subset=required)
        df=df[(df.actual_lead_time_days>=0)&(df.daily_demand_units>=0)&(df.current_stock_units>=0)]
        if df.empty:
            st.warning("No valid rows found after cleaning.")
        else:
            service = st.slider("Safety factor (higher = more protection)", 0.0, 3.0, 1.65, 0.05, help="A simple configurable multiplier applied to lead-time standard deviation; not a formal service-level guarantee.")
            summary=df.groupby("supplier", dropna=False).agg(
                orders=("actual_lead_time_days","count"),
                quoted_avg=("quoted_lead_time_days","mean"),
                actual_avg=("actual_lead_time_days","mean"),
                lead_time_sd=("actual_lead_time_days","std"),
                demand_avg=("daily_demand_units","mean"),
                stock_avg=("current_stock_units","mean")
            ).reset_index()
            summary["lead_time_sd"]=summary["lead_time_sd"].fillna(0)
            summary["safety_stock"]=service*summary["demand_avg"]*summary["lead_time_sd"]
            summary["reorder_point"]=summary["demand_avg"]*summary["actual_avg"]+summary["safety_stock"]
            summary["reorder_point"]=np.ceil(summary["reorder_point"]).astype(int)
            summary["stock_status"]=np.where(summary["stock_avg"]<=summary["reorder_point"],"REORDER","Stock adequate")
            avg_late=(df.actual_lead_time_days>df.quoted_lead_time_days).mean()*100
            metric_row([
                ("Suppliers", f"{df.supplier.nunique():,}", "Distinct suppliers in the cleaned data"),
                ("Orders / records", f"{len(df):,}", "Valid records used"),
                ("Records later than quote", f"{avg_late:.1f}%", "Share of records where actual lead time exceeded quoted lead time"),
                ("Suppliers flagged", f"{(summary.stock_status=='REORDER').sum():,}", "Average stock at or below calculated reorder point")
            ])
            st.markdown("#### Supplier reorder recommendations")
            st.dataframe(summary.sort_values("reorder_point",ascending=False), use_container_width=True, hide_index=True)
            fig, ax=plt.subplots(figsize=(10,4.2))
            x=np.arange(len(summary))
            ax.bar(x-.18,summary["actual_avg"],width=.36,label="Actual avg lead time")
            ax.bar(x+.18,summary["quoted_avg"],width=.36,label="Quoted avg lead time")
            ax.set_xticks(x,summary["supplier"].astype(str),rotation=25,ha="right")
            ax.set_ylabel("Days"); ax.set_title("Quoted vs actual supplier lead time"); ax.legend(); ax.grid(axis="y",alpha=.25)
            st.pyplot(fig); plt.close(fig)
            st.download_button("Download supplier reorder recommendations",summary.to_csv(index=False).encode(), "reorder_recommendations.csv","text/csv")
            st.caption(f"Data source: {source}. Formula: reorder point = average daily demand × average actual lead time + safety factor × average daily demand × lead-time standard deviation.")
            st.warning("This is a screening estimate. For production use, account for demand variability, service-level targets, review period, minimum order quantities and supplier-specific policies.")

# ---------- Use case 2 ----------
with tab2:
    st.subheader("Outbound | Find which delivery stage causes delay")
    st.write("Break down total delivery performance into first-mile, mid-mile and last-mile stages to identify where time is being lost.")
    uploaded=st.file_uploader("Upload outbound delivery-stage CSV",type="csv",key="outbound")
    df,source=read_upload(uploaded,case2_demo)
    required=["order_id","stage","planned_days","actual_days"]
    miss=missing_cols(df,required)
    if miss:
        st.error("Missing required columns: "+", ".join(miss))
        st.info("Expected stage values: First Mile, Mid Mile, Last Mile. See template in Data & How to Use.")
    else:
        df["stage"]=df["stage"].astype(str).str.strip()
        for c in ["planned_days","actual_days"]:
            df[c]=pd.to_numeric(df[c],errors="coerce")
        df=df.dropna(subset=required)
        df["delay_days"]=df["actual_days"]-df["planned_days"]
        df["late"]=df["delay_days"]>0
        stage_order=["First Mile","Mid Mile","Last Mile"]
        agg=df.groupby("stage").agg(
            records=("order_id","count"),
            planned_avg_days=("planned_days","mean"),
            actual_avg_days=("actual_days","mean"),
            avg_delay_days=("delay_days","mean"),
            late_rate_pct=("late",lambda x:100*x.mean())
        ).reset_index()
        agg["stage"]=pd.Categorical(agg["stage"],categories=stage_order,ordered=True)
        agg=agg.sort_values("stage")
        if not df.empty:
            worst=agg.sort_values("avg_delay_days",ascending=False).iloc[0]
            metric_row([
                ("Stage records",f"{len(df):,}","Rows used in stage analysis"),
                ("Orders",f"{df.order_id.nunique():,}","Unique order identifiers"),
                ("Worst average-delay stage",str(worst.stage),"Highest average actual minus planned days"),
                ("Overall late stage records",f"{df.late.mean()*100:.1f}%","Share of stage records with actual duration above plan")
            ])
            left,right=st.columns(2)
            with left:
                fig,ax=plt.subplots(figsize=(7,4))
                ax.bar(agg["stage"].astype(str),agg["avg_delay_days"])
                ax.axhline(0,linewidth=1)
                ax.set_ylabel("Average delay (days)"); ax.set_title("Average delay by delivery stage"); ax.tick_params(axis="x",rotation=20); ax.grid(axis="y",alpha=.25)
                st.pyplot(fig); plt.close(fig)
            with right:
                fig,ax=plt.subplots(figsize=(7,4))
                ax.bar(agg["stage"].astype(str),agg["late_rate_pct"])
                ax.set_ylabel("Late stage records (%)"); ax.set_ylim(0,100); ax.set_title("Late-record rate by stage"); ax.tick_params(axis="x",rotation=20); ax.grid(axis="y",alpha=.25)
                st.pyplot(fig); plt.close(fig)
            st.markdown("#### Stage performance table")
            st.dataframe(agg, use_container_width=True, hide_index=True)
            if "route" in df.columns:
                st.markdown("#### Route comparison")
                route_agg=df.groupby(["route","stage"]).agg(avg_delay_days=("delay_days","mean"),late_rate_pct=("late",lambda x:100*x.mean())).reset_index()
                pivot=route_agg.pivot(index="route",columns="stage",values="avg_delay_days")
                st.dataframe(pivot, use_container_width=True)
            st.download_button("Download stage analysis",agg.to_csv(index=False).encode(),"delivery_stage_analysis.csv","text/csv")
            st.caption(f"Data source: {source}. Delay is calculated as actual stage duration minus planned stage duration; negative values mean ahead of plan.")
            st.info("To calculate true OTIF (on-time, in-full), add planned and actual delivered dates plus ordered and delivered quantities. This demo analyzes stage delays, not full in-full performance.")

# ---------- Use case 3 ----------
with tab3:
    st.subheader("Supplier risk | Interactive disruption what-if control tower")
    st.write("Simulate a supplier delay and immediately see potentially affected production/customer orders, estimated penalty exposure and backup-supplier coverage.")
    uploaded=st.file_uploader("Upload supplier-to-order impact CSV",type="csv",key="disruption")
    df,source=read_upload(uploaded,case3_demo)
    required=["supplier_id","material","production_order","customer_order","required_in_days","expected_arrival_in_days","material_qty","estimated_penalty","backup_supplier"]
    miss=missing_cols(df,required)
    if miss:
        st.error("Missing required columns: "+", ".join(miss))
        st.info("See the sample template in Data & How to Use.")
    else:
        for c in ["required_in_days","expected_arrival_in_days","material_qty","estimated_penalty"]:
            df[c]=pd.to_numeric(df[c],errors="coerce")
        df=df.dropna(subset=required)
        if not df.empty:
            supplier_options=sorted(df.supplier_id.astype(str).unique())
            chosen=st.selectbox("Supplier reporting a disruption",supplier_options)
            default_delay=3
            delay=st.slider("Expected additional delay (days)",1,30,default_delay)
            affected=df[df.supplier_id.astype(str)==chosen].copy()
            affected["simulated_arrival_day"]=affected["expected_arrival_in_days"]+delay
            affected["shortage_risk"]=affected["simulated_arrival_day"]>affected["required_in_days"]
            affected["mitigation_status"]=np.where(
                affected["backup_supplier"].astype(str).str.lower().isin(["no backup","none","nan",""]),
                "No backup listed","Backup listed — verify capacity"
            )
            penalty=float(affected.loc[affected["shortage_risk"],"estimated_penalty"].sum())
            no_backup=int((affected["mitigation_status"]=="No backup listed").sum())
            metric_row([
                ("Affected order rows",f"{len(affected):,}","Rows linked to selected supplier"),
                ("Production orders",f"{affected.production_order.nunique():,}","Unique production orders"),
                ("Estimated penalty exposure",f"{penalty:,.0f}","Sum of supplied estimated penalties; not a forecast"),
                ("Rows without backup",f"{no_backup:,}","Backup supplier is missing or marked No backup")
            ])
            st.markdown("#### Impacted order list")
            st.dataframe(affected[["supplier_id","material","production_order","customer_order","required_in_days","simulated_arrival_day","material_qty","estimated_penalty","backup_supplier","mitigation_status"]],use_container_width=True,hide_index=True)
            left,right=st.columns(2)
            with left:
                bymat=affected.groupby("material").size().sort_values(ascending=False)
                fig,ax=plt.subplots(figsize=(7,4))
                ax.bar(bymat.index.astype(str),bymat.values)
                ax.set_ylabel("Affected order rows"); ax.set_title("Impact by material"); ax.tick_params(axis="x",rotation=25); ax.grid(axis="y",alpha=.25)
                st.pyplot(fig); plt.close(fig)
            with right:
                backup=affected["mitigation_status"].value_counts()
                fig,ax=plt.subplots(figsize=(7,4))
                ax.bar(backup.index.astype(str),backup.values)
                ax.set_ylabel("Order rows"); ax.set_title("Backup coverage indicator"); ax.tick_params(axis="x",rotation=15); ax.grid(axis="y",alpha=.25)
                st.pyplot(fig); plt.close(fig)
            st.download_button("Download disruption impact report",affected.to_csv(index=False).encode(),"disruption_impact_report.csv","text/csv")
            st.caption(f"Data source: {source}. This is a what-if screening tool. It compares expected arrival plus simulated delay against the material required-by day and shows supplied penalty estimates.")
            st.warning("A backup supplier being listed does not mean it has capacity or is approved. Add inventory on hand, bill of materials, supplier capacity, production schedules and actual customer due dates before treating the output as an operational plan.")

# ---------- Data & help ----------
with tab4:
    st.subheader("Data templates and setup")
    st.write("Each use case accepts a CSV upload. If no file is uploaded, the app uses synthetic demo data so you can test the interface immediately.")
    st.markdown("#### 1. Inbound reorder optimizer — required columns")
    st.code("supplier,material,quoted_lead_time_days,actual_lead_time_days,daily_demand_units,current_stock_units,unit_cost",language="text")
    csv_download(case1_demo,"sample_inbound_supplier_data.csv","Download inbound sample CSV")
    st.dataframe(case1_demo.head(8),use_container_width=True,hide_index=True)
    st.markdown("#### 2. Outbound delay detective — required columns")
    st.code("order_id,stage,planned_days,actual_days\n# optional: route, carrier",language="text")
    csv_download(case2_demo,"sample_outbound_stage_data.csv","Download outbound sample CSV")
    st.dataframe(case2_demo.head(8),use_container_width=True,hide_index=True)
    st.markdown("#### 3. Supplier disruption simulator — required columns")
    st.code("supplier_id,material,production_order,customer_order,required_in_days,expected_arrival_in_days,material_qty,estimated_penalty,backup_supplier",language="text")
    csv_download(case3_demo,"sample_supplier_disruption_data.csv","Download disruption sample CSV")
    st.dataframe(case3_demo.head(8),use_container_width=True,hide_index=True)
    st.markdown("#### Run locally")
    st.code("python -m venv .venv\n# Windows PowerShell\n.\\.venv\\Scripts\\Activate.ps1\npython -m pip install -r requirements.txt\nstreamlit run app.py",language="powershell")
    st.markdown("#### Dataset sources for real-world practice")
    st.markdown("""
- [Supply Chain Data Hub — public supply-chain datasets](https://supplychaindatahub.org/datasets/) — includes a synthetic delivery-delay dataset and disruption-monitoring data.
- [US Purchasing & Procurement Dataset (CSV)](https://huggingface.co/datasets/mindweave/purchasing-procurement-us) — purchase orders, goods receipts and supplier lead-time information.
- [Accenture Supply Chain Resilience Challenge (Kaggle)](https://www.kaggle.com/competitions/datathon-2022-upc-accenture/data) — historical orders and outbound shipment fields.
- [Supply Chain Inventory Dataset (Kaggle)](https://www.kaggle.com/datasets/ziya07/high-dimensional-supply-chain-inventory-dataset) — inventory, sales, lead times and reorder-point-related fields.
""")
    st.caption("Public datasets rarely contain every field required by all three use cases. You may need to join tables or rename columns to match the templates. Check each dataset's licence and terms before business/commercial use.")

st.markdown("---")
st.markdown('<div class="small-note">Manufacturing Digitalization Control Tower • Prototype for analysis and demonstration • Validate all assumptions before operational use.</div>',unsafe_allow_html=True)
