import json, glob, re, sys
import numpy as np, pandas as pd
OUT='/home/user/work/rerun/out/'; REPO='/home/user/repo/'
SC=['low','medium','high','oversaturated','asym_ns','asym_ew','dynamic']; CT=['C0','C1','C2','C3']
CID={'C0':'C0_Original_FixedTime','C1':'C1_Webster_FixedTime','C2':'C2_Basic_Queue','C3':'C3_Proposed_Adaptive'}
# ---- 1. reproduction
rows=[json.load(open(f)) for f in glob.glob(OUT+'sum_*.json')]
R=pd.DataFrame(rows); print('re-executed runs:',len(R))
ren={'cohort_a_completed':'throughput_cohort_a','avg_waiting_time_s':'mean_waiting_time_s','avg_travel_time_s':'mean_travel_time_s','avg_delay_s':'mean_delay_s','total_delay_s':'total_delay_s','avg_stops_per_veh':'mean_stops_per_veh','mean_speed_mps':'mean_speed_mps','avg_queue_length_veh':'mean_queue_veh','max_queue_length_veh':'max_queue_veh','phase_switch_count':'phase_switch_count','total_yellow_lost_time_s':'total_yellow_lost_time_s','max_red_duration_s':'max_red_duration_s'}
R=R.rename(columns=ren); F=pd.read_csv(REPO+'results/final_test_results_per_seed.csv')
M=R.merge(F,on=['controller_id','scenario','seed'],suffixes=('_re',''))
mism=0; tot=0
for c in ren.values():
    a=M[c+'_re'].astype(float); b=M[c].astype(float); tot+=len(M); mism+=int((~np.isclose(a,b,atol=1e-9)).sum())
print(f'reproduction: {len(M)} runs x {len(ren)} metrics = {tot} values; mismatches = {mism}')
R['c']=R.controller_id.str[:2]
# ---- 2. scheduled vehicles (route files) & completion shares
def sched(sc,seed):
    d=[float(x) for x in re.findall(r'depart="([\d.]+)"',open(REPO+f'scenarios/demand/demand_{sc}_seed{seed}.rou.xml').read())]
    return len(d), sum(1 for x in d if x>=200)
S=[]
for r in R.itertuples():
    tot,aft=sched(r.scenario,r.seed); S.append((tot,aft))
R['sched_all']=[s[0] for s in S]; R['sched_after200']=[s[1] for s in S]
R['completion_share']=R.throughput_cohort_a/R.sched_after200
# ---- 3. direction-level waiting + unfinished (inclusive)
dirw=[];inc=[]
for r in R.itertuples():
    tag=f'{r.c}_{r.scenario}_{r.seed}'
    v=pd.read_csv(OUT+f'veh_{tag}.csv.gz'); a=v[v.cohort=='A_eval_pure'].copy(); a['orig']=a.route_id.str[0]; a['dir']=np.where(a.orig.isin(['N','S']),'NS','EW')
    for d,g in a.groupby('dir'): dirw.append(dict(c=r.c,scenario=r.scenario,seed=r.seed,dir=d,n=len(g),mean_wait=g.waiting_time.mean(),max_wait=g.waiting_time.max()))
    try: u=pd.read_csv(OUT+f'unf_{tag}.csv.gz')
    except Exception: u=pd.DataFrame(columns=['acc_wait','depart'])
    u=u[u.depart>=200] if len(u) else u
    nA=len(a); nU=len(u); sumA=a.waiting_time.sum(); sumU=u.acc_wait.sum() if nU else 0.0
    inc.append(dict(c=r.c,scenario=r.scenario,seed=r.seed,nA=nA,nUnfinished=nU,meanA=a.waiting_time.mean() if nA else np.nan,meanUnf=(u.acc_wait.mean() if nU else np.nan),inclusive=(sumA+sumU)/max(nA+nU,1)))
D=pd.DataFrame(dirw); I=pd.DataFrame(inc)
D.to_csv('/home/user/work/rerun/analysis/direction_waiting_per_run.csv',index=False); I.to_csv('/home/user/work/rerun/analysis/inclusive_waiting_per_run.csv',index=False); R.to_csv('/home/user/work/rerun/analysis/rerun_summary.csv',index=False)
pd.set_option('display.width',200)
print(D.groupby(['scenario','c','dir']).mean_wait.mean().unstack('dir').round(1).head(20))
print(I.groupby(['scenario','c'])[['nA','nUnfinished','meanA','inclusive']].mean().round(1).head(20))
