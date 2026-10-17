import json, glob, re, numpy as np, pandas as pd
from scipy import stats
OUT='/home/user/work/fresh/out/'; DEM='/home/user/work/fresh/demand/'
SC=['low','medium','high','oversaturated','asym_ns','asym_ew','dynamic']
R=pd.DataFrame([json.load(open(f)) for f in glob.glob(OUT+'sum_*.json')]); print(len(R))
R=R.rename(columns={'avg_waiting_time_s':'wait','avg_travel_time_s':'tt','avg_delay_s':'tl','avg_queue_length_veh':'queue','phase_switch_count':'sw','cohort_a_completed':'thr','max_red_duration_s':'maxred'})
def sch(sc,s):
    d=[float(x) for x in re.findall(r'depart="([\d.]+)"',open(DEM+f'demand_{sc}_seed{s}.rou.xml').read())]; return sum(1 for x in d if x>=200)
R['sched']=[sch(a,b) for a,b in zip(R.scenario,R.seed)]; R['share']=R.thr/R.sched
R.to_csv('fresh_summary.csv',index=False)
pd.set_option('display.width',250)
m=R.pivot_table(index='scenario',columns='variant',values='wait',aggfunc='mean').reindex(SC)[['C0','C1','C2','C3','A_noHyst','A_queueOnlyH','A_noArrival','A_noGrowth']]
s=R.pivot_table(index='scenario',columns='variant',values='wait',aggfunc='std').reindex(SC)[m.columns]
print((m.round(2).astype(str)+' ('+s.round(2).astype(str)+')').to_string())
def paired(a,b,k='wait'):
    rows=[]
    for sc in SC:
        x=R[(R.scenario==sc)&(R.variant==a)].sort_values('seed')[k].values; y=R[(R.scenario==sc)&(R.variant==b)].sort_values('seed')[k].values
        d=x-y; sd=d.std(ddof=1); h=stats.t.ppf(.975,4)*sd/np.sqrt(5)
        p=stats.ttest_1samp(d,0).pvalue if sd>0 else 1.0
        rows.append(dict(scenario=sc,a=a,b=b,mean_a=x.mean(),mean_b=y.mean(),diff=d.mean(),lo=d.mean()-h,hi=d.mean()+h,dz=d.mean()/sd if sd>0 else 0,p=p,wins=int((d<0).sum()),pct=100*(y.mean()-x.mean())/y.mean()))
    return pd.DataFrame(rows)
allp=pd.concat([paired('C3',b) for b in ['C0','C1','C2']]+[paired('C3',b) for b in ['A_noHyst','A_queueOnlyH','A_noArrival','A_noGrowth']])
# BH over the 21 primary tests only
prim=allp[allp.b.isin(['C0','C1','C2'])].copy(); p=prim.p.values; n=len(p); o=np.argsort(p); q=np.empty(n); r=np.empty(n,int); r[o]=np.arange(1,n+1); qq=p*n/r; qs=np.minimum.accumulate(qq[o][::-1])[::-1]; q[o]=np.minimum(qs,1); prim['q']=q
allp=allp.merge(prim[['scenario','b','q']],on=['scenario','b'],how='left'); allp.to_csv('fresh_paired.csv',index=False)
print(allp[allp.b.isin(['C1','C2'])][['scenario','b','mean_a','mean_b','diff','lo','hi','dz','p','q','wins','pct']].round(3).to_string())
print(allp[allp.b=='C0'][['scenario','pct','q']].round(3).to_string())
print(allp[~allp.b.isin(['C0','C1','C2'])][['scenario','b','mean_a','mean_b','diff','lo','hi','p','pct']].round(2).to_string())
print(R.pivot_table(index='scenario',columns='variant',values='sw',aggfunc='mean').reindex(SC)[['C1','C2','C3','A_noHyst','A_queueOnlyH','A_noArrival','A_noGrowth']].round(1).to_string())
print((R.pivot_table(index='scenario',columns='variant',values='share',aggfunc='mean').reindex(SC)*100).round(1)[['C0','C1','C2','C3']].to_string())
