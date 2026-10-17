import sys; sys.path.insert(0,'/home/user/repo'); sys.path.insert(0,'/home/user/repo/scripts')
from pathlib import Path
from generate_routes import generate_routes
out=Path('/home/user/work/fresh/demand'); seeds=[201,202,203,204,205]
sym={'low':0.04,'medium':0.08,'high':0.14,'oversaturated':0.18}
asym={'asym_ns':{"N":0.14,"S":0.14,"E":0.03,"W":0.03},'asym_ew':{"N":0.03,"S":0.03,"E":0.14,"W":0.14}}
dyn=[{"t_start":0,"t_end":300,"probs":{k:0.04 for k in 'NSEW'}},{"t_start":300,"t_end":700,"probs":{k:0.15 for k in 'NSEW'}},{"t_start":700,"t_end":1000,"probs":{k:0.05 for k in 'NSEW'}}]
n=0
for s in seeds:
    for k,p in sym.items(): generate_routes(str(out/f'demand_{k}_seed{s}.rou.xml'),sim_duration=1000,seed=s,p_arrival_per_arm=p); n+=1
    for k,p in asym.items(): generate_routes(str(out/f'demand_{k}_seed{s}.rou.xml'),sim_duration=1000,seed=s,p_arrival_per_arm=p); n+=1
    generate_routes(str(out/f'demand_dynamic_seed{s}.rou.xml'),sim_duration=1000,seed=s,dynamic_schedule=dyn); n+=1
print('generated',n)
