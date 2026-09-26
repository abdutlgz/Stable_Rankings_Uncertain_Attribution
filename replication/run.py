"""Portable raw-data computation; only aggregate outputs leave memory."""
from pathlib import Path
import argparse,hashlib,json,shutil,sys
ROOT=Path(__file__).resolve().parent

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def safe_path(root,relative):
 p=root/relative
 if Path(relative).is_absolute() or '..' in Path(relative).parts:raise ValueError('Unsafe manifest path')
 return p

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--import-data',type=Path);parser.add_argument('--check-only',action='store_true');args=parser.parse_args()
 manifest=json.loads((ROOT/'package_manifest.json').read_text())
 for name,digest in manifest['files'].items():
  if sha(safe_path(ROOT,name))!=digest:raise ValueError(f'Package input changed: {name}')
 data=json.loads((ROOT/'data_manifest.json').read_text())['files']
 for row in data:
  target=safe_path(ROOT,row['path'])
  if args.import_data:
   source=safe_path(args.import_data,row['path'])
   if sha(source)!=row['sha256']:raise ValueError(f'Data checksum mismatch: {row["path"]}')
   if source.resolve()!=target.resolve():
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
  if not target.is_file() or sha(target)!=row['sha256']:raise ValueError(f'Missing or changed data: {row["path"]}')
 if args.check_only:
  print('All package and data hashes verified.');return
 sys.path.insert(0,str(ROOT/'src'))
 import numpy as np
 import pandas as pd
 from audit_historical_structured_credit import build_season,summarize_group
 from audit_measurement import load_matchups,load_nba_pbp,turnover_player_games
 from build_matchup_panel import build_player_season
 from fit_empirical_dynamic_model import fit_one_season
 from build_external_defender_events import credited_counts
 from validate_defender_pressure import experiment_rolling
 from validate_external_construct import build_cohort,cluster_bootstrap_indices,BOOTSTRAP_REPLICATES,BOOTSTRAP_SEED
 from audit_sloan_v6_inference import screen,correlation_adjustment
 from bound_receiver_partial_identification import season_edges
 from scipy.stats import spearmanr
 from screening_pilot import subtype_audit,screening_pilot
 expected=json.loads((ROOT/'expected_aggregates.json').read_text())
 result={};events=[];measurement={}
 for year in (2023,2024):
  frame,_=build_season(year);events.append(frame)
  pbp,_=load_nba_pbp(year);_,_,s=turnover_player_games(load_matchups(year),pbp)
  measurement[str(year)]={k:s[k] for k in expected['reconciliation'][str(year)]}
  print(f'{year}: measurement audit completed',flush=True)
 audit_events=pd.concat(events,ignore_index=True)
 result['assignment']=summarize_group(audit_events);result['reconciliation']=measurement
 pilot_result=subtype_audit(audit_events)
 del audit_events
 del events,frame,pbp
 stages=[];rates=[];credits=[];fits=[];volumes=[]
 for year in range(2017,2025):
  rates.append(build_player_season(year));stage,fit=fit_one_season(year,maxiter=500)
  if not fit['success']:raise RuntimeError(f'Fit did not converge: {year}')
  stages.append(stage);fits.append({'season':year,'converged':True})
  external,_=credited_counts(year);credits.append(external)
  e=season_edges(year);volume=e.groupby('matchups_person_id',as_index=False).agg(matchup_fga=('matchup_field_goals_attempted','sum'),possessions=('partial_possessions','sum'));volume['season']=year;volumes.append(volume)
  print(f'{year}: model and credits rebuilt',flush=True)
 rates=pd.concat(rates,ignore_index=True);stages=pd.concat(stages,ignore_index=True);credits=pd.concat(credits,ignore_index=True);keys=['matchups_person_id','season']
 rolling,_,_=experiment_rolling(rates);result['persistence']=rolling['median_transition_rho']
 panel=stages.merge(rates[keys+['main_team','turnover_full_adjusted_rate','foul_raw_rate']],on=keys,validate='one_to_one').merge(credits,on=keys,how='left',validate='one_to_one')
 for col in ['steals','blocks']:
  panel[col]=panel[col].fillna(0.);panel[col+'_per100']=100*panel[col]/panel.partial_possessions
 cohort=build_cohort(panel)
 pilot_result.update(screening_pilot(cohort))
 ids=cohort.matchups_person_id.to_numpy();transitions=cohort.transition.to_numpy()
 values=cohort[['turnover_full_adjusted_rate_prior','turnover_contrast_estimate_prior','steals_per100_prior','steals_per100_next']].to_numpy()
 precision=screen(values,transitions,ids);draws=[];fractional=[]
 for index in cluster_bootstrap_indices(ids,BOOTSTRAP_REPLICATES,BOOTSTRAP_SEED):
  a=screen(values[index],transitions[index],ids[index]);b=screen(values[index],transitions[index],ids[index],fractional=True)
  draws.append(a[1]-a[0]);fractional.append(b[1]-b[0])
 result['headline']={'pairs':len(cohort),'unique_defenders':int(cohort.matchups_person_id.nunique()),'baseline_precision':float(precision[0]),'proposed_precision':float(precision[1]),'simple_precision':float(precision[2]),'precision_advantage_ci95':np.percentile(draws,[2.5,97.5]).tolist(),'fractional_ci95':np.percentile(fractional,[2.5,97.5]).tolist()}
 panel=panel.merge(pd.concat(volumes,ignore_index=True),on=keys,validate='one_to_one');p=panel[panel.partial_possessions.ge(500)&panel.matchup_fga.gt(0)];shots=100*p.matchup_fga/p.possessions
 result['construct']={}
 for name,col in [('raw_pressure','turnover_full_adjusted_rate'),('turnover_contrast','turnover_contrast_estimate')]:
  row={}
  for target in ['steals','blocks']:
   row[f'vs_{target}_per100']=float(spearmanr(p[col],p[target+'_per100']).statistic)
   row[f'vs_{target}_given_shot_volume']=correlation_adjustment(p[col],p[target+'_per100'],shots)['conventional']
  result['construct'][name]=row
 def compare(a,b,label=''):
  if isinstance(b,dict):
   for k,v in b.items():compare(a[k],v,label+'/'+k)
  elif isinstance(b,list):
   if len(a)!=len(b):raise AssertionError(label+' length mismatch')
   for i,v in enumerate(b):compare(a[i],v,label+'/'+str(i))
  elif isinstance(b,str) or b is None:
   if a!=b:raise AssertionError(label+' mismatch')
  else:np.testing.assert_allclose(a,b,atol=1e-10,rtol=0,err_msg=label)
 compare(result,expected)
 compare(pilot_result,json.loads((ROOT/"pilot/expected_results.json").read_text()),"pilot")
 result["pilot"]=pilot_result
 for row in data:
  if sha(ROOT/row['path'])!=row['sha256']:raise ValueError('Research input changed during computation')
 dest=ROOT/'results';dest.mkdir(exist_ok=True)
 result.update(status='pass',scope='Portable headline, subtype and screening-pilot raw-data replication; aggregate reference agreement, not independent implementation or full supplementary replication',fits=fits)
 (dest/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
 print('PASS: all checked aggregate results reproduced from raw data.',flush=True)

if __name__=='__main__':main()
