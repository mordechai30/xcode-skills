"""Verify documented public commands and record only byte counts in one Markdown table.
No implementation imports or backend connection details are needed by this caller.
"""
import argparse
from datetime import datetime,timezone
from pathlib import Path
import shutil
import signal
import subprocess
import time

ROOT=Path(__file__).resolve().parents[1]
HEADER='# Per-task response and log sizes\n\nSizes are UTF-8 bytes. Response includes stdout, stderr, and newline. Current operations must create or update no logs. Log size is measured after the task; — means no log changed.\n\n| Skill | Project | Config | Test | Operation | Result | Response bytes | Added log bytes | Log bytes |\n|---|---|---|---|---|---|---:|---:|---:|\n'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--fixtures',type=Path,required=True)
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--scenario',choices=('baseline','debug','extra','failure'),required=True)
    args=parser.parse_args()
    args.report.parent.mkdir(parents=True,exist_ok=True)
    fixture='HelloCpp';config='Debug';folder=args.fixtures/fixture
    def call(operation,*inputs,interrupt=False):
        logs=folder/ROOT.name
        before={p:(p.stat().st_size,p.stat().st_mtime_ns) for p in logs.glob('log-*.txt')}
        command=[str(ROOT/'scripts/manager.py'),operation,*map(str,inputs)]
        if interrupt:
            process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            time.sleep(1)
            if process.poll() is None:process.send_signal(signal.SIGINT)
            stdout,stderr=process.communicate(timeout=60);code=process.returncode
        else:
            result=subprocess.run(command,capture_output=True,timeout=7800)
            stdout,stderr,code=result.stdout,result.stderr,result.returncode
        text=stdout.decode()
        limit=500 if code or '--detail' in inputs else 200
        assert not stderr and len(stdout)<=limit,(operation,text,stderr)
        after={p:(p.stat().st_size,p.stat().st_mtime_ns) for p in logs.glob('log-*.txt')}
        assert after==before, 'An operation created or updated a log'
        changed=[]
        cells=(ROOT.name,fixture,config,args.scenario,operation,'succeeded' if code==0 else 'incomplete' if 'incomplete' in text else 'rejected',len(stdout)+len(stderr),0,'—')
        line='| '+' | '.join(map(str,cells))+' |\n'
        marker='\n## Earlier interface measurements\n'
        if args.report.exists() and marker in args.report.read_text():
            text_report=args.report.read_text()
            args.report.write_text(text_report.replace(marker,line+marker,1))
        else:
            fresh=not args.report.exists()
            with args.report.open('a') as stream:
                if fresh:stream.write(HEADER)
                stream.write(line)
        return text,code
    def ok(operation,*inputs):
        text,code=call(operation,*inputs)
        assert code==0,(fixture,operation,text)
        return text
    def select():
        return ['--package',folder,'--product','HelloSwift'] if fixture=='HelloSwiftPackage' else ['--project',folder/(fixture+'.xcodeproj'),'--scheme',fixture,'--target',fixture]
    try:
        assert ok('status')=='Status: no app.\n'
        if args.scenario=='baseline':
            for fixture in ('HelloCpp','HelloObjCpp','HelloSwift','HelloSwiftPackage'):
                folder=args.fixtures/fixture
                for config in ('Debug','Release'):
                    ok('build',*select(),'--configuration',config)
                    assert ok('status')=='Status: no app.\n'
                    ok('run',*select(),'--configuration',config)
                    assert ok('status') in ('Status: running.\n','Status: exited.\n')
                    ok('kill');assert ok('status')=='Status: no app.\n'
                config='Debug'
                ok('run',*select(),'--configuration',config,'--no-debugger')
                assert ok('status') in ('Status: running.\n','Status: exited.\n')
                ok('kill');assert ok('status')=='Status: no app.\n'
                print(ROOT.name,fixture,'baseline passed',flush=True)
        elif args.scenario=='debug':
            for fixture,filename,line in (('HelloCpp','main.cpp',15),('HelloObjCpp','main.mm',19),('HelloSwift','main.swift',9),('HelloSwiftPackage','Sources/HelloSwift/main.swift',9)):
                folder=args.fixtures/fixture
                ok('run',*select(),'--configuration','Debug')
                text,code=call('set-breakpoint','--file',folder/filename,'--line',line)
                assert code==0 or 'pending' in text,(fixture,text)
                deadline=time.monotonic()+15
                while 'paused' not in ok('status'):
                    assert time.monotonic()<deadline,'Breakpoint did not stop'
                    time.sleep(.1)
                inspected=ok('debugger-command','--command','frame variable tick')
                assert 'tick =' in inspected,(fixture,inspected)
                ok('continue','--keep-breakpoint')
                assert 'paused' in ok('status')
                ok('continue');assert 'running' in ok('status')
                ok('pause');assert 'paused' in ok('status')
                ok('continue');ok('kill')
                assert ok('status')=='Status: no app.\n'
                print(ROOT.name,fixture,'debug passed',flush=True)
            fixture='HelloSwiftPackage';folder=args.fixtures/fixture;config='Release'
            ok('run',*select(),'--configuration','Release',*(['--arguments','--exit'] if ROOT.name!='apple-mcp-xcode-op' else ['--arguments','--exit']))
            deadline=time.monotonic()+5
            while 'exited' not in ok('status'):
                assert time.monotonic()<deadline,'Immediate exit not observed'
                time.sleep(.1)
            ok('kill');assert ok('status')=='Status: no app.\n'
        elif args.scenario=='extra':
            ok('run',*select(),'--configuration','Debug')
            text,code=call('set-breakpoint','--file',folder/'main.cpp','--line',18,interrupt=True)
            assert 'interrupted' in text.lower(),text
            assert 'running' in ok('status')
            ok('kill')
            if ROOT.name!='apple-mcp-xcode-op':
                inputs=[*select(),'--configuration','Debug','--no-debugger']
                if ROOT.name=='direct-xcode-op':inputs+=['--working-directory',folder]
                ok('run',*inputs,'--arguments','--stay-alive','--mode','test')
                ps=subprocess.check_output(['ps','-axo','pid,args'],text=True)
                process=next(line for line in ps.splitlines() if 'HelloCpp.app/Contents/MacOS/HelloCpp --stay-alive --mode test' in line)
                if ROOT.name=='direct-xcode-op':
                    pid=process.strip().split()[0]
                    working=subprocess.check_output(['/usr/sbin/lsof','-a','-p',pid,'-d','cwd','-Fn'],text=True)
                    assert 'n'+str(folder) in working,working
                ok('kill')
            if ROOT.name!='direct-xcode-op':
                for option in ('--arguments','--working-directory'):
                    inputs=[*select(),'--configuration','Debug',option]
                    if option=='--working-directory':inputs.append(folder)
                    text,code=call('run',*inputs)
                    assert code and option in text,(option,text)
            assert ok('status')=='Status: no app.\n'
        elif args.scenario=='failure':
            copy=args.report.parent/'failure-fixtures-minimal'/ROOT.name/'HelloCpp'
            assert not copy.exists(),'Use a fresh failure fixture copy'
            shutil.copytree(folder,copy,ignore=shutil.ignore_patterns('Build','DerivedData',*('direct-xcode-op','apple-mcp-xcode-op','mobilebuildmcp-xcode-op')))
            with (copy/'main.cpp').open('a') as stream:stream.write('\n#error SKILL_FAILURE_MARKER\n')
            folder=copy
            text,code=call('build',*select(),'--configuration','Debug')
            assert code and 'SKILL_FAILURE_MARKER' in text,text
            assert ok('status')=='Status: no app.\n'
    finally:
        text,code=call('status')
        if text!='Status: no app.\n':
            ok('kill')
    print(ROOT.name,args.scenario,'passed',flush=True)


if __name__=='__main__':main()
