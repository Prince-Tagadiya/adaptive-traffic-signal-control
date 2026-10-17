import glob, numpy as np, pandas as pd
OUT='/home/user/work/rerun/out/'; SC=['low','medium','high','oversaturated','asym_ns','asym_ew','dynamic']; SEEDS=[42,43,44,45,46]
H=0.20; GMIN=15
def green_intervals(step):
    ph=step.tl_phase.values; out=[]; cur=None; n=0
    for p in ph:
        if p in (0,2):
            if cur==p: n+=1
            else:
                if cur is not None: out.append(n)
                cur=p; n=1
        else:
            if cur is not None: out.append(n); cur=None; n=0
    return out
rows=[]; reasons=[]; ext=[]; comp=[]
for sc in SC:
    for c in ['C1','C2','C3']:
        gi=[]
        for s in SEEDS:
            st=pd.read_csv(OUT+f'step_{c}_{sc}_{s}.csv.gz'); gi+=green_intervals(st)
        rows.append(dict(scenario=sc,c=c,mean_green=np.mean(gi),median_green=np.median(gi),p90_green=np.percentile(gi,90),max_green=max(gi),n_intervals=len(gi)))
    # C3 decision diagnostics
    rc={}; band=0; maint=0; extras=[]; nseg=0; ct=[]
    for s in SEEDS:
        d=pd.read_csv(OUT+f'dec_C3_{sc}_{s}.csv.gz'); ct+=d.Compute_Time_us.tolist()
        for k,v in d.Switch_Reason.value_counts().items(): rc[k]=rc.get(k,0)+v
        d['opp']=np.where(d.Switch_Reason.str.endswith('_NS')|(d.Switch_Reason.str.contains('SWITCH_EW_HIGHER')),d.Score_EW-d.Score_NS,d.Score_NS-d.Score_EW)
        # maintain rows: direction stays; delta = opposing minus current
        m=d[d.Switch_Reason.str.startswith('PRESSURE_MAINTAIN')].copy()
        m['delta']=np.where(m.Switch_Reason.str.endswith('_NS'),m.Score_EW-m.Score_NS,m.Score_NS-m.Score_EW)
        maint+=len(m); band+=int(((m.delta>0)&(m.delta<=H)).sum())
        # segments between yellow blocks
        t=d.sim_time.values; rs=d.Switch_Reason.values
        seg_start=0
        for i in range(1,len(d)):
            if rs[i]=='YELLOW_CLEARANCE' and rs[i-1]!='YELLOW_CLEARANCE':
                seg=d.iloc[seg_start:i]; sw=seg.iloc[-1]
                post=seg[~seg.Switch_Reason.isin(['MIN_GREEN_HOLD','YELLOW_CLEARANCE'])].copy()
                if len(post) and str(sw.Switch_Reason).startswith('PRESSURE_SWITCH'):
                    post['delta']=np.where(post.Switch_Reason.str.endswith('_NS')|post.Switch_Reason.str.contains('SWITCH_EW_HIGHER'),post.Score_EW-post.Score_NS,post.Score_NS-post.Score_EW)
                    pos=post[post.delta>0]
                    if len(pos): extras.append(post.sim_time.iloc[-1]-pos.sim_time.iloc[0]); nseg+=1
            if rs[i]!='YELLOW_CLEARANCE' and rs[i-1]=='YELLOW_CLEARANCE': seg_start=i
    tot_sw=sum(v for k,v in rc.items() if 'SWITCH' in k or k in('MAX_GREEN_EXCEEDED','STARVATION_CEILING'))
    reasons.append(dict(scenario=sc,switches=tot_sw,pressure=sum(v for k,v in rc.items() if 'PRESSURE_SWITCH' in k),max_green=rc.get('MAX_GREEN_EXCEEDED',0),starvation=rc.get('STARVATION_CEILING',0),
        maintain_steps=maint,maintain_in_band=band,band_share=band/max(maint,1),mean_extra_hold=np.mean(extras) if extras else np.nan,share_intervals_extra_gt0=np.mean(np.array(extras)>0) if extras else np.nan,n_pressure_intervals=len(extras),
        comp_mean_us=np.mean(ct),comp_median_us=np.median(ct),comp_p99_us=np.percentile(ct,99),comp_max_us=max(ct)))
G=pd.DataFrame(rows); Rz=pd.DataFrame(reasons)
G.to_csv('analysis/green_durations.csv',index=False); Rz.to_csv('analysis/c3_decision_diagnostics.csv',index=False)
pd.set_option('display.width',250); pd.set_option('display.max_columns',30)
print(G.round(1).to_string()); print(Rz.round(3).to_string())
