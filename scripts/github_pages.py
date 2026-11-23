"""Configure/poll the explicitly requested repository; credentials never printed or saved."""
import argparse,os,subprocess,json,time
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('action',choices=['enable','status']);args=parser.parse_args()
p=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',text=True,capture_output=True,env={**os.environ,'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'never'})
if p.returncode:raise SystemExit('GitHub authentication unavailable in configured credential helper.')
d=dict(line.split('=',1) for line in p.stdout.splitlines() if '=' in line)
s=requests.Session();s.auth=(d.get('username',''),d.get('password',''));s.headers.update({'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'})
base='https://api.github.com/repos/Doofen-bit/Crazy-Micky'
if args.action=='enable':
 r=s.get(base+'/pages',timeout=30)
 if r.status_code==404:r=s.post(base+'/pages',json={'build_type':'workflow'},timeout=30)
 elif r.ok and r.json().get('build_type')!='workflow':r=s.put(base+'/pages',json={'build_type':'workflow'},timeout=30)
 print('Pages configuration status:',r.status_code)
 if not r.ok:print(r.json().get('message'));raise SystemExit(1)
 print('Pages URL:',r.json().get('html_url','Configured'))
else:
 r=s.get(base+'/actions/runs',timeout=30);r.raise_for_status()
 runs=[{k:x.get(k) for k in ['id','head_sha','name','status','conclusion','html_url','created_at']} for x in r.json()['workflow_runs'][:5]]
 print(json.dumps(runs,indent=2))
 page=s.get(base+'/pages',timeout=30)
 info=page.json() if page.ok else {}
 public=requests.get('https://doofen-bit.github.io/Crazy-Micky/',timeout=30)
 record={'repository':'https://github.com/Doofen-bit/Crazy-Micky','url':'https://doofen-bit.github.io/Crazy-Micky/','pages_status':info.get('status'),'build_type':info.get('build_type'),'public_http_status':public.status_code,'title_found':'Stress, across time' in public.text,'runs':runs}
 print('Public HTTP:',record['public_http_status'],'title verified:',record['title_found'])
 (ROOT/'audit/deployment.json').write_text(json.dumps(record,indent=2))
