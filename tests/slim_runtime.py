"""Validate the actual portable worker with external socket connections denied."""
import argparse,hashlib,importlib.util,json,pathlib,socket,sys,time
p=argparse.ArgumentParser();p.add_argument('--bundle',required=True);p.add_argument('--cache',required=True);p.add_argument('--fixtures',required=True);p.add_argument('--report',required=True);p.add_argument('--baseline');p.add_argument('--require-cuda',action='store_true');a=p.parse_args()
bundle=pathlib.Path(a.bundle).resolve();worker=bundle/'桌面端/resources/worker';sys.path.insert(0,str(worker))
attempts=[];connect=socket.socket.connect
def offline(self,address):
    if isinstance(address,tuple) and address[0] in {'127.0.0.1','::1','localhost'}:return connect(self,address)
    attempts.append(str(address));raise RuntimeError('External connection denied')
socket.socket.connect=offline
spec=importlib.util.spec_from_file_location('shipped_worker',worker/'main.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
engine=module.Engine();started=time.perf_counter();status=engine.load(str(bundle/'桌面端/resources/bundled-model'),a.cache)
if a.require_cuda:assert status['device']=='cuda',status
fixtures=pathlib.Path(a.fixtures);images=sorted(fixtures.glob('*.png'));assert len(images)>=2
entries=[{'hash':hashlib.sha256(f.read_bytes()).hexdigest(),'path':str(f)} for f in images]
initial_encodes=engine.asset_encodes;engine.index(entries);engine.index_thread.join(timeout=120);assert not engine.index_thread.is_alive()
allowed=[e['hash'] for e in entries];query_file=fixtures/'query.jpg';query=engine.query(image=str(query_file if query_file.exists() else images[0]),allowed=allowed);text=engine.query(text='游戏背包界面，物品格子和装备',allowed=allowed)
assert query['matches'][0]['hash']==entries[0]['hash'];assert len(text['matches'])==len(entries)
clip,dino=engine.encode(image=str(images[0]));assert len(clip)==512 and len(dino)==384
if a.baseline:
    old=json.loads(pathlib.Path(a.baseline).read_text(encoding='utf-8-sig'))
    assert engine.asset_encodes==initial_encodes,'Existing query database must be reusable without encoding assets'
    assert old['modelId']==status['modelId'] and old['imageTop']==query['matches'][0]['hash']
    assert old['textOrder']==[m['hash'] for m in text['matches']]
    assert max(abs(x-y) for x,y in zip(clip,old['clip']))<1e-5
    assert max(abs(x-y) for x,y in zip(dino,old['dino']))<1e-5
assert not attempts,attempts
report={'success':True,'device':status['device'],'modelId':status['modelId'],'indexCount':len(engine.indexed),'assetEncodes':engine.asset_encodes,'imageTop':query['matches'][0]['hash'],'textOrder':[m['hash'] for m in text['matches']],'imageQueryMs':query['ms'],'textQueryMs':text['ms'],'clip':clip,'dino':dino,'externalConnectionAttempts':attempts,'baselineCompared':bool(a.baseline),'seconds':round(time.perf_counter()-started,2),'boundary':'Functional fixture checks, not project retrieval accuracy or P95 acceptance'}
pathlib.Path(a.report).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in {'clip','dino'}},ensure_ascii=False),flush=True)
