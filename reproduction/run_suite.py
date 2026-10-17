"""Confirmatory run on fresh seeds (201-205) with the frozen controller, plus single-term ablations of C3.
Uses the repository runner and controllers unmodified."""
import sys, time, json
sys.path.insert(0,'/home/user/repo')
from pathlib import Path
import pandas as pd, traci
from simulation.runner import SimulationRunner
from controllers.fixed_time_controller import FixedTimeSignalController
from controllers.optimized_fixed_time_controller import OptimizedFixedTimeSignalController
from controllers.basic_density_controller import BasicDensityController
from controllers.proposed_adaptive_controller import ProposedAdaptiveSignalController as P
OUT=Path('/home/user/work/fresh/out'); DEM=Path('/home/user/work/fresh/demand'); CFG='/home/user/repo/scenarios/four_arm.sumocfg'
SC=['low','medium','high','oversaturated','asym_ns','asym_ew','dynamic']; SEEDS=[201,202,203,204,205]
VAR={'C0':lambda:FixedTimeSignalController(),'C1':lambda:OptimizedFixedTimeSignalController(),'C2':lambda:BasicDensityController(min_green=15,max_green=50,yellow_time=3,starvation_red_time=45),
     'C3':lambda:P(),'A_noGrowth':lambda:P(gamma=0.0),'A_noArrival':lambda:P(beta=0.0),'A_noWaiting':lambda:P(delta=0.0),'A_noRedAge':lambda:P(eta=0.0),'A_noHyst':lambda:P(hysteresis=0.0),
     'A_queueOnlyH':lambda:P(beta=0.0,gamma=0.0,delta=0.0,eta=0.0)}
state={}; _oc=traci.close
def cw(*a,**k):
    try:
        state['unf']=[{'veh':v,'acc_wait':traci.vehicle.getAccumulatedWaitingTime(v),'route':traci.vehicle.getRouteID(v),'depart':traci.vehicle.getDeparture(v)} for v in traci.vehicle.getIDList()]
        state['pending']=len(traci.simulation.getPendingVehicles())
    except Exception as e: state['unf']=[]; state['pending']=-1
    return _oc(*a,**k)
traci.close=cw
order=['C3','C0','C1','C2','A_noHyst','A_queueOnlyH','A_noArrival','A_noGrowth']
t0=time.time()
for v in order:
    for sc in SC:
        for s in SEEDS:
            tag=f'{v}_{sc}_{s}'
            if (OUT/f'sum_{tag}.json').exists(): continue
            ctrl=VAR[v](); r=SimulationRunner(config_path=CFG,route_path=str(DEM/f'demand_{sc}_seed{s}.rou.xml'),controller=ctrl,seed=s,warmup_duration=200,sim_duration=1000)
            res=r.run(); sm=dict(res['summary']); sm['phase_step_counts']=str(sm['phase_step_counts']); sm.update(variant=v,scenario=sc,seed=s,pending_end=state.get('pending'))
            res['vehicle_dataframe'].to_csv(OUT/f'veh_{tag}.csv.gz',index=False); pd.DataFrame(state.get('unf',[])).to_csv(OUT/f'unf_{tag}.csv.gz',index=False)
            if v=='C3': pd.DataFrame(ctrl.decisions_log).to_csv(OUT/f'dec_{tag}.csv.gz',index=False); res['step_dataframe'].to_csv(OUT/f'step_{tag}.csv.gz',index=False)
            json.dump(sm,open(OUT/f'sum_{tag}.json','w')); print(tag,sm['avg_waiting_time_s'],round(time.time()-t0),'s',flush=True)
print('ALL DONE',flush=True)
