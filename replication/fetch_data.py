"""Retrieve immutable upstream archives; verify bytes before installing inputs."""
from pathlib import Path
import argparse,hashlib,json,shutil,tarfile,tempfile
from urllib.request import urlopen
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parent

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def main():
 p=argparse.ArgumentParser();p.add_argument('--destination',type=Path,default=ROOT);args=p.parse_args()
 m=json.loads((ROOT/'upstream_manifest.json').read_text());dest=args.destination.resolve();dest.mkdir(parents=True,exist_ok=True)
 def retrieve(a):
  with tempfile.TemporaryDirectory(prefix='sloan-fetch-') as tmp:
   archive=Path(tmp)/a['name']
   with urlopen(a['url'],timeout=90) as response,archive.open('wb') as f:shutil.copyfileobj(response,f)
   if sha(archive)!=a['sha256']:raise ValueError(f'Upstream archive mismatch: {a["name"]}')
   for row in a['outputs']:
    if Path(row['path']).is_absolute() or '..' in Path(row['path']).parts:raise ValueError('Unsafe output path')
    target=dest/row['path'];target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
     if sha(target)!=row['sha256']:raise ValueError(f'Refusing to overwrite changed input: {row["path"]}')
     continue
    staging=Path(tmp)/(target.name+'.verified')
    if row['member']:
     with tarfile.open(archive,'r:xz') as bundle:
      member=bundle.getmember(row['member'])
      if not member.isfile():raise ValueError('Expected regular CSV member')
      with bundle.extractfile(member) as source,staging.open('wb') as f:shutil.copyfileobj(source,f)
    else:shutil.copyfile(archive,staging)
    if sha(staging)!=row['sha256']:raise ValueError(f'Unpacked input mismatch: {row["path"]}')
    shutil.copyfile(staging,target)
  print(f'Verified {a["name"]}',flush=True)
  return a['name']
 with ThreadPoolExecutor(max_workers=4) as pool:verified=list(pool.map(retrieve,m['archives']))
 with urlopen(m['license_url'],timeout=30) as response:license_bytes=response.read()
 if hashlib.sha256(license_bytes).hexdigest()!=m['license_sha256']:raise ValueError('Upstream license changed')
 result={'status':'pass','commit':m['commit'],'archive_count':len(verified),'input_count':sum(len(a['outputs']) for a in m['archives']),'license_hash_verified':True,'scope':'Public byte retrieval verified; not redistribution clearance'}
 (dest/'public_retrieval_verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)

if __name__=='__main__':main()
