"""Independent re-execution of the 140 final-evaluation runs using the repository's own runner/controllers.
Captures step data, vehicle records, controller decision logs, and end-of-run state of unfinished vehicles.
Nothing in the repository is modified; traci.close is wrapped only to record end-of-run state."""
import sys, time, json
sys.path.insert(0,'/home/user/repo')
from pathlib import Path
import pandas as pd, traci
from simulation.runner import SimulationRunner
import importlib.util
spec=importlib.util.spec_from_file_location('final_eval','/home/user/repo/scripts/run_final_test_evaluation.py'); fe=importlib.util.module_from_spec(spec); spec.loader.exec_module(fe)
OUT=Path('/home/user/work/rerun/out'); OUT.mkdir(exist_ok=True)
state={}
_orig_close=traci.close
def close_wrapper(*a,**k):
    try:
        rows=[]
        for v in traci.vehicle.getIDList():
            rows.append({'veh':v,'acc_wait':traci.vehicle.getAccumulatedWaitingTime(v),'route':traci.vehicle.getRouteID(v),'depart':traci.vehicle.getDeparture(v) if hasattr(traci.vehicle,'getDeparture') else float('nan'),'timeloss':traci.vehicle.getTimeLoss(v)})
        state['unfinished']=rows
    except Exception as e:
        state['unfinished']=[]; state['err']=str(e)
    return _orig_close(*a,**k)
traci.close=close_wrapper
rows=[]; t0=time.time()
for c_id,ctype in fe.CONTROLLERS:
    for sc in fe.SCENARIOS:
        for seed in fe.SEEDS:
            tag=f'{c_id[:2]}_{sc}_{seed}'
            if (OUT/f'sum_{tag}.json').exists(): continue
            ctrl=fe.create_controller_instance(ctype)
            r=SimulationRunner(config_path=fe.CONFIG_PATH,route_path=str(fe.DEMAND_DIR/f'demand_{sc}_seed{seed}.rou.xml'),controller=ctrl,seed=seed,warmup_duration=200,sim_duration=1000)
            res=r.run(); s=res['summary']
            res['step_dataframe'].to_csv(OUT/f'step_{tag}.csv.gz',index=False)
            res['vehicle_dataframe'].to_csv(OUT/f'veh_{tag}.csv.gz',index=False)
            pd.DataFrame(state.get('unfinished',[])).to_csv(OUT/f'unf_{tag}.csv.gz',index=False)
            if hasattr(ctrl,'decisions_log') and ctrl.decisions_log: pd.DataFrame(ctrl.decisions_log).to_csv(OUT/f'dec_{tag}.csv.gz',index=False)
            s=dict(s); s['phase_step_counts']=str(s['phase_step_counts']); s.update(controller_id=c_id,scenario=sc,seed=seed)
            json.dump(s,open(OUT/f'sum_{tag}.json','w'))
            print(tag,s['avg_waiting_time_s'],round(time.time()-t0),'s',flush=True)
print('ALL DONE',flush=True)
