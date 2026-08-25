
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Urban Shade Planning Optimizer", page_icon="🌳", layout="wide")

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

st.markdown("""
<style>
:root{--ink:#15233f;--muted:#67758e;--line:#e5ebf3;--bg:#f6f8fb;--green:#20a65a;--blue:#2777e8;--orange:#f3a43b;--purple:#7354e8;--red:#ea5a5a}
.stApp{background:var(--bg);color:var(--ink)}
.block-container{max-width:1500px;padding-top:1.15rem}
[data-testid="stSidebar"]{background:#fff;border-right:1px solid var(--line)}
.hero{background:linear-gradient(135deg,#edf9ef 0%,#edf7ff 52%,#fff6ed 100%);border:1px solid #dfe9e2;border-radius:24px;padding:30px;margin-bottom:20px}
.hero h1{font-size:2.25rem;margin:0;color:var(--ink)!important}.hero p{color:#61708a;font-size:1.05rem;margin:.35rem 0 0}
.pill{display:inline-block;padding:7px 12px;border-radius:999px;border:1px solid #d9e5e0;background:#fff;color:#36506a;margin:8px 8px 0 0;font-size:.86rem}
.card{background:#fff;border:1px solid var(--line);border-radius:18px;padding:17px;box-shadow:0 8px 24px rgba(22,42,76,.05)}
.small{color:var(--muted);font-size:.84rem}.value{font-size:1.85rem;font-weight:800;color:var(--ink)}
.good{background:#effaf4;border:1px solid #cfeede;border-radius:14px;padding:13px}
.warn{background:#fff7ea;border:1px solid #f0dbb9;border-radius:14px;padding:13px}
.alert{background:#fff1f1;border:1px solid #f0cece;border-radius:14px;padding:13px}
.footer{color:#6b7890;font-size:.82rem;text-align:center}
</style>
""", unsafe_allow_html=True)

def norm(df):
    df=df.copy()
    df.columns=[str(c).strip().lower().replace(" ","_") for c in df.columns]
    return df

def score_records(df):
    x=df.copy()
    x["shade_gap"]=100-x["shade_coverage_pct"]
    x["pedestrian_pressure"]=np.clip(x["pedestrian_count_day"]/18000*100,0,100)
    x["heat_pressure"]=np.clip(x["heat_exposure_index"],0,100)
    x["impervious_pressure"]=x["impervious_surface_pct"].clip(0,100)
    x["heat_priority_score"]=(0.42*x["heat_pressure"]+0.24*x["shade_gap"]+0.18*x["pedestrian_pressure"]+0.10*x["impervious_pressure"]+0.06*x["dryness_index"]*100).round(1)
    x["priority_band"]=pd.cut(x["heat_priority_score"],bins=[-1,30,50,70,101],labels=["Monitor","Review","High Priority","Critical Priority"])
    return x

st.sidebar.markdown("## 🌳 ShadePlan Local")
st.sidebar.caption("Cooler streets • healthier communities • local-first planning")
up=st.sidebar.file_uploader("Upload urban-shade CSV",type=["csv"])
opp=st.sidebar.file_uploader("Upload opportunity CSV",type=["csv"])
base_df=norm(pd.read_csv(up)) if up else pd.read_csv(DATA/"sample_urban_shade_registry.csv")
opps=norm(pd.read_csv(opp)) if opp else pd.read_csv(DATA/"sample_shade_opportunities.csv")
required=["segment_id","zone","land_use","surface_temp_c","heat_exposure_index","shade_coverage_pct","pedestrian_count_day","tree_canopy_pct","shelter_coverage_pct","shaded_walkway_pct","impervious_surface_pct","monthly_rainfall_mm","dryness_index"]
missing=[c for c in required if c not in base_df.columns]
if missing:
    st.error("Missing required columns: "+", ".join(missing)); st.stop()
df=score_records(base_df)

st.sidebar.markdown("---")
zones=sorted(df["zone"].astype(str).unique())
uses=sorted(df["land_use"].astype(str).unique())
selzones=st.sidebar.multiselect("Zones",zones,default=zones)
seluses=st.sidebar.multiselect("Land use",uses,default=uses)
minscore=st.sidebar.slider("Minimum priority score",0,100,0)
view=df[df["zone"].isin(selzones)&df["land_use"].isin(seluses)&(df["heat_priority_score"]>=minscore)].copy()

st.markdown("""
<div class="hero">
<div class="small">URBAN CLIMATE • PEDESTRIAN HEAT • SHADE INVESTMENT</div>
<h1>Cool the routes people use most.</h1>
<p>Identify where trees, shelters, cool roofs and shaded walkways may reduce pedestrian heat exposure using transparent local planning signals.</p>
<span class="pill">🌡️ Heat exposure</span><span class="pill">🌳 Tree canopy</span><span class="pill">🛖 Shade structures</span><span class="pill">🏠 Cool roofs</span><span class="pill">🚶 Shaded walkways</span><span class="pill">📊 Explainable</span>
</div>
""",unsafe_allow_html=True)

avgtemp=float(view["surface_temp_c"].mean()) if len(view) else 0
highzones=int((view["heat_priority_score"]>=70).sum())
deficit=float(((100-view["shade_coverage_pct"])/100).sum()/max(1,len(view)))
people=int(view["pedestrian_count_day"].sum())
potential=float(opps["cooling_potential_c"].mean()) if len(opps) else 0
recsites=int((opps["priority_score"]>=70).sum())

metrics=[
("High heat segments",highzones,"Priority attention"),
("Avg surface temp",f"{avgtemp:.1f}°C","Local screening context"),
("Shade-deficit index",f"{deficit:.2f}","Relative planning gap"),
("People exposed / day",f"{people:,}","Pedestrian volume context"),
("Avg cooling potential",f"{potential:.1f}°C","Intervention sample"),
("Recommended sites",recsites,"Top-priority opportunities")]
cols=st.columns(6)
for c,(title,val,note) in zip(cols,metrics):
    with c: st.markdown(f"<div class='card'><div class='small'>{title}</div><div class='value'>{val}</div><div class='small'>{note}</div></div>",unsafe_allow_html=True)

st.markdown("### Urban heat intelligence")
a,b,c=st.columns([1.15,1.0,.85])
with a:
    agg=view.groupby("zone",as_index=False).agg(avg_heat=("heat_exposure_index","mean"),pedestrians=("pedestrian_count_day","sum"))
    fig=px.scatter(agg,x="avg_heat",y="pedestrians",size="pedestrians",color="avg_heat",hover_name="zone",
                   title="Heat exposure × pedestrian volume")
    fig.update_layout(margin=dict(l=0,r=0,t=45,b=0),paper_bgcolor="white")
    st.plotly_chart(fig,use_container_width=True)
with b:
    imp=opps.groupby("recommended_intervention",as_index=False)["cooling_potential_c"].mean().sort_values("cooling_potential_c",ascending=True)
    fig=px.bar(imp,x="cooling_potential_c",y="recommended_intervention",orientation="h",text_auto=".1f",
               title="Intervention cooling potential")
    fig.update_layout(margin=dict(l=0,r=0,t=45,b=0),paper_bgcolor="white")
    st.plotly_chart(fig,use_container_width=True)
with c:
    band=view["priority_band"].value_counts().reindex(["Critical Priority","High Priority","Review","Monitor"]).fillna(0).reset_index()
    band.columns=["band","count"]
    fig=px.pie(band,names="band",values="count",hole=.58,title="Priority mix")
    fig.update_layout(margin=dict(l=0,r=0,t=45,b=0),paper_bgcolor="white")
    st.plotly_chart(fig,use_container_width=True)

st.markdown("### Exposure & shade-gap analytics")
d,e=st.columns(2)
with d:
    heat=view.pivot_table(index="zone",columns="land_use",values="heat_priority_score",aggfunc="mean",fill_value=0)
    fig=px.imshow(heat,text_auto=".0f",aspect="auto",title="Zone × land-use priority heatmap")
    fig.update_layout(margin=dict(l=0,r=0,t=45,b=0),paper_bgcolor="white")
    st.plotly_chart(fig,use_container_width=True)
with e:
    fig=px.scatter(view,x="shade_coverage_pct",y="surface_temp_c",size="pedestrian_count_day",color="land_use",
                   hover_name="segment_id",title="Shade coverage × surface temperature",
                   labels={"shade_coverage_pct":"Shade coverage (%)","surface_temp_c":"Surface temperature (°C)"})
    fig.update_layout(margin=dict(l=0,r=0,t=45,b=0),paper_bgcolor="white")
    st.plotly_chart(fig,use_container_width=True)

st.markdown("### Priority locations")
top=view.sort_values("heat_priority_score",ascending=False).head(15)
st.dataframe(top[["segment_id","zone","land_use","surface_temp_c","shade_coverage_pct","pedestrian_count_day","heat_priority_score","priority_band"]],
             use_container_width=True,hide_index=True)

st.markdown("### Intervention planner")
i1,i2,i3,i4=st.columns(4)
with i1: tree_weight=st.slider("Tree-canopy weight",0.0,1.0,.30,.05)
with i2: shade_weight=st.slider("Structure weight",0.0,1.0,.25,.05)
with i3: walk_weight=st.slider("Walkway weight",0.0,1.0,.25,.05)
with i4: roof_weight=st.slider("Cool-roof weight",0.0,1.0,.20,.05)
w=np.array([tree_weight,shade_weight,walk_weight,roof_weight]); w=w/w.sum() if w.sum()>0 else np.array([1,0,0,0])
plan=opps.copy()
plan["intervention_priority_score"]=(w[0]*(100-plan["shade_deficit_km2"]*60).clip(0,100)+w[1]*plan["cooling_potential_c"].clip(0,5)*20+w[2]*plan["pedestrians_exposed_day"].clip(0,20000)/200+w[3]*plan["priority_score"].clip(0,100)).round(1)
plan=plan.sort_values("intervention_priority_score",ascending=False)
st.dataframe(plan[["site_id","zone","recommended_intervention","cooling_potential_c","pedestrians_exposed_day","estimated_cost","intervention_priority_score"]].head(15),
             use_container_width=True,hide_index=True)
st.download_button("⬇️ Export shade intervention plan",data=plan.to_csv(index=False).encode(),
                   file_name="urban_shade_intervention_plan.csv",mime="text/csv")
st.download_button("⬇️ Export screened segments",data=df.to_csv(index=False).encode(),
                   file_name="urban_shade_screened_segments.csv",mime="text/csv")

st.markdown("<div class='good'><b>Planning note:</b> Use the outputs to prioritize site investigation and intervention design. Validate with field measurements, accessibility needs, tree suitability, utilities, maintenance requirements, water availability, land ownership, local climate observations, and community input.</div>",unsafe_allow_html=True)
st.markdown("<div class='alert'><b>Decision boundary:</b> This tool does not determine exact planting locations, guarantee cooling outcomes, or replace qualified urban planners, arborists, engineers, public-health professionals, accessibility specialists, or municipal approvals.</div>",unsafe_allow_html=True)
st.markdown("<div class='footer'>100% local CSV processing • No external APIs • Explainable planning rules • Human/community review required</div>",unsafe_allow_html=True)
