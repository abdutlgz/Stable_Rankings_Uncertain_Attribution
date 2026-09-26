"""Subtype audit and fixed-design expanding-window screening pilot.

Adapted from the archived September 12 analysis to accept reconstructed
in-memory data. No frozen player estimates or private project paths are read.
"""
import math
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit

def subtype_audit(events):
    a = events.copy()
    match=pd.to_numeric(a.feed_matches_explicit_contributor,errors='coerce')
    if match.isna().any():match=a.feed_matches_explicit_contributor.astype(str).str.lower().map({'true':1,'false':0})
    assert len(a)==8560 and match.sum()==2644 and not match.isna().any()
    a['match']=match;rows=[]
    for name,g in a.groupby('turnover_family',dropna=False):
     n=len(g);h=int(g.match.sum());p=h/n;z=1.95996398454;den=1+z*z/n;center=(p+z*z/(2*n))/den;half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
     rows.append(dict(family=str(name),events=n,matches=h,agreement=p,wilson_low=center-half,wilson_high=center+half))
    subtype_rows=[]
    for name,g in a.groupby('subType',dropna=False):
     n=len(g);h=int(g.match.sum());p=h/n;z=1.95996398454;den=1+z*z/n;center=(p+z*z/(2*n))/den;half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
     subtype_rows.append(dict(subtype=str(name),events=n,matches=h,agreement=p,wilson_low=center-half,wilson_high=center+half))
    assert sum(r['events'] for r in subtype_rows)==8560 and sum(r['matches'] for r in subtype_rows)==2644
    return {'families': rows, 'subtypes': subtype_rows}

def screening_pilot(cohort):
    c = cohort.copy()
    assert len(c) == 808
    features=['steals_per100_prior','foul_raw_rate_prior','turnover_contrast_estimate_prior','foul_vs_shot_contrast_estimate_prior']
    assert np.isfinite(c[features+['steals_per100_next','foul_raw_rate_next']].to_numpy()).all()
    X=(c.groupby('transition')[features].rank(method='average',pct=True).to_numpy()-.5)*math.sqrt(12)
    y=np.zeros(len(c));trans=c.transition.to_numpy()
    for t in np.unique(trans):
     ix=np.flatnonzero(trans==t);k=math.ceil(len(ix)/4);target=ix[np.argsort(-c.iloc[ix].steals_per100_next.to_numpy(),kind='stable')[:k]];y[target]=1
    models={'logit_steals':[0],'logit_steals_fouls':[0,1],'logit_plus_components':[0,1,2,3]}
    folds=[];totals={n:dict(hits=0,selected=0,steals_sum=0.,fouls_sum=0.,brier_sum=0.,n=0) for n in ['prior_steals',*models]}
    for t in np.unique(trans)[2:]:
     tr=trans<t;te=trans==t;ids=np.flatnonzero(te);k=math.ceil(len(ids)/4);scores={'prior_steals':c.loc[te,'steals_per100_prior'].to_numpy()};probs={}
     for name,cols in models.items():
      A=np.column_stack([np.ones(tr.sum()),X[tr][:,cols]]);B=np.column_stack([np.ones(te.sum()),X[te][:,cols]])
      def obj(w):
       z=A@w;p=expit(z);return float(np.logaddexp(0,z).sum()-y[tr]@z+.5*(w[1:]@w[1:])), A.T@(p-y[tr])+np.r_[0,w[1:]]
      fit=minimize(obj,np.zeros(A.shape[1]),jac=True,method='L-BFGS-B',options={'maxiter':1000,'gtol':1e-8});assert fit.success,fit.message
      scores[name]=B@fit.x;probs[name]=expit(scores[name])
     for name,score in scores.items():
      chosen=ids[np.argsort(-score,kind='stable')[:k]];h=int(y[chosen].sum());st=float(c.iloc[chosen].steals_per100_next.sum());fo=float(c.iloc[chosen].foul_raw_rate_next.sum());bs=float(((probs[name]-y[te])**2).sum()) if name in probs else None
      folds.append(dict(transition=str(t),model=name,train_pairs=int(tr.sum()),test_pairs=int(te.sum()),quota=k,hits=h,precision=h/k,mean_next_steals_per100=st/k,mean_next_feed_foul_rate=fo/k,brier=bs/te.sum() if bs is not None else None))
      v=totals[name];v['hits']+=h;v['selected']+=k;v['steals_sum']+=st;v['fouls_sum']+=fo;v['n']+=int(te.sum());v['brier_sum']+=bs or 0
    summary={n:dict(precision=v['hits']/v['selected'],hits=v['hits'],selected=v['selected'],test_pairs=v['n'],mean_next_steals_per100=v['steals_sum']/v['selected'],mean_next_feed_foul_rate=v['fouls_sum']/v['selected'],brier=v['brier_sum']/v['n'] if n!='prior_steals' else None) for n,v in totals.items()}
    return {'screening_summary': summary, 'folds': folds}
