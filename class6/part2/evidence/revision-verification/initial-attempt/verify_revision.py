"""Run the delivered scripts from a relocated copy against two isolated stacks."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from urllib.request import urlopen

SOURCE = Path('C:/Users/Viclant/Desktop/JWT-Part2-Submission')
WORK = Path(__file__).resolve().parent
COPY = WORK / 'relocated-submission'
OUT = SOURCE / 'evidence/revision-verification'
OUT.mkdir(parents=True, exist_ok=True)
assert not COPY.exists(), 'Refusing to reuse an existing relocated environment'
shutil.copytree(SOURCE, COPY, ignore=shutil.ignore_patterns('__pycache__', '.env', 'revision-verification'))
shutil.copy2(WORK / 'revision-prediction.json', OUT / 'revision-prediction.json')
records = []
started = datetime.now(timezone(timedelta(hours=8))).isoformat()
assert datetime.fromisoformat(json.loads((OUT / 'revision-prediction.json').read_text())['recorded_at']) < datetime.fromisoformat(started)


def run(args, cwd=COPY, env=None, required=True):
    t = time.time()
    result = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace')
    records.append({'command': [str(a) for a in args], 'cwd': str(cwd), 'exit_code': result.returncode,
                    'elapsed_seconds': round(time.time()-t,3), 'output': result.stdout + result.stderr})
    (OUT / 'commands.json').write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
    if required and result.returncode:
        raise RuntimeError('Command failed: ' + ' '.join(str(a) for a in args[:4]))
    return result


stacks = []
summary = {'started_at': started, 'scope': 'Relocated copy, fresh independent test databases, no original service changed',
           'prediction_file': 'revision-prediction.json', 'passed': False}
try:
    for folder, project, port, variable in [('lab','jwt-part2-review-weak',8085,'PART2_PORT'),
                                             ('class7-control','jwt-part2-review-control',8086,'CONTROL_PORT')]:
        cwd = COPY / folder
        env = dict(os.environ, **{variable: str(port), 'PYTHONUTF8':'1'})
        run([sys.executable, 'setup_keys.py'], cwd, env)
        compose = ['docker','compose','-p',project,'-f','compose.yaml']
        stacks.append((cwd,env,compose,project))
        print('Starting isolated stack:', project, 'port', port, flush=True)
        run(compose+['up','-d','--build'], cwd, env)
        for attempt in range(60):
            try:
                with urlopen(f'http://127.0.0.1:{port}/healthz',timeout=2) as response:
                    if response.status == 200:break
            except OSError:time.sleep(1)
        else:raise RuntimeError('Health check did not pass')
        observed=run(compose+['exec','-T','web','sha256sum','/app/app.py'],cwd,env).stdout.split()[0]
        expected=hashlib.sha256((cwd/'web/app.py').read_bytes()).hexdigest()
        assert observed==expected
        summary[folder+'_app_sha256']=observed
    env = dict(os.environ, PYTHONUTF8='1')
    # CWD is intentionally outside the package and --wordlist is omitted.
    p2out=OUT/'part2'
    run([sys.executable, str(COPY/'scripts/part2.py'), '--base','http://127.0.0.1:8085', '--out',str(p2out)],WORK,env)
    p2=json.loads((p2out/'part2-results.json').read_text())
    assert p2['overall_passed'] and len(p2['checks'])==8 and all(c['body_matches_expected'] and not c['cookie_sent'] for c in p2['checks'])
    controlout=OUT/'control'
    controlargs=[sys.executable,str(COPY/'scripts/part2-class7-control.py'),'--base','http://127.0.0.1:8086',
                 '--part2-results',str(p2out/'part2-results.json'),'--secret-file',str(COPY/'class7-control/.env')]
    run(controlargs+['--out',str(controlout)],WORK,env)
    control=json.loads((controlout/'class7-control.json').read_text())
    assert control['overall_passed'] and len(control['checks'])==3 and control['candidates_tried']==15
    failures=[]
    empty=WORK/'empty-wordlist.txt';empty.write_text('',encoding='utf-8')
    cases=[('missing wordlist',[sys.executable,str(COPY/'scripts/part2.py'),'--wordlist',str(WORK/'does-not-exist.txt')]),
           ('empty wordlist',[sys.executable,str(COPY/'scripts/part2.py'),'--wordlist',str(empty)]),
           ('missing positive-control key',[sys.executable,str(COPY/'scripts/part2-class7-control.py'),
                    '--part2-results',str(p2out/'part2-results.json'),'--secret-file',str(WORK/'missing.env')]),
           ('refuse evidence overwrite',[sys.executable,str(COPY/'scripts/part2.py'),'--out',str(p2out)])]
    for label,args in cases:
        outcome=run(args,WORK,env,required=False)
        assert outcome.returncode != 0
        failures.append({'case':label,'exit_code':outcome.returncode,'passed':True})
    # Exercise the live evidence helper, including its repaired default wordlist.
    helper="import importlib.util; s=importlib.util.spec_from_file_location('evidence_page',r'"+str(COPY/'scripts/part2-evidence-server.py')+"'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); m.BASE_PORT=8085; page=m.build(); assert '12.6' in page and 's3cr3t' in page; print('live page and package-relative wordlist: PASS')"
    run([sys.executable,'-c',helper],WORK,env)
    summary.update(passed=True, part2_checks_passed=8,part2_checks_total=8,
                   strong_control_checks_passed=3,strong_control_checks_total=3,
                   wordlist_candidates=15,weak_key_candidates_tried=p2['key_recovery']['candidates_tried'],
                   weak_key_search_seconds=p2['key_recovery']['seconds'],negative_checks=failures,
                   relocated_default_wordlist_passed=True,live_evidence_helper_passed=True)
except Exception as error:
    summary.update(error_type=type(error).__name__,error=str(error))
    print('Verification failed:',type(error).__name__,str(error),flush=True)
finally:
    cleanup=[]
    for cwd,env,compose,project in stacks:
        down=run(compose+['down'],cwd,env,required=False)
        remaining=run(compose+['ps','--all','--format','json'],cwd,env,required=False).stdout.strip()
        volumes=run(['docker','volume','ls','--filter','label=com.docker.compose.project='+project,'--format','{{.Name}}'],cwd,env,required=False).stdout.splitlines()
        cleanup.append({'project':project,'down_exit_code':down.returncode,'remaining_containers':remaining,
                        'retained_volumes':volumes,'volume_deletion_requested':False,
                        'passed':down.returncode==0 and not remaining and bool(volumes)})
    summary['cleanup']=cleanup
    summary['cleanup_passed']=len(cleanup)==2 and all(c['passed'] for c in cleanup)
    summary['passed']=summary['passed'] and summary['cleanup_passed']
    summary['finished_at']=datetime.now(timezone(timedelta(hours=8))).isoformat()
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    shutil.copy2(Path(__file__),OUT/'verify_revision.py')
    print(json.dumps(summary,indent=2),flush=True)
sys.exit(0 if summary['passed'] else 1)
