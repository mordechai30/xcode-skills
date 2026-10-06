"""Test operation facts, deadlines, output limits, and local backend routes."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import manager
from lifecycle.response import render
from lifecycle.diagnostics import StreamDiagnostics
from operations.kill import execute as kill
from operations.pause import execute as pause


class AcceptanceGapTests(unittest.TestCase):
    def test_build_uncertainty_preserves_actual_transport_cause(self):
        from operations.build import finish
        with tempfile.TemporaryDirectory() as folder:
            log = Path(folder)/'log.txt'
            ctx = {'log':log}
            value = finish(type('Args',(),{})(),ctx,{'status':'uncertain','message':'BuildProject: transport deadline exceeded'})
            self.assertEqual(value['stage'],'build')
            self.assertIn('transport deadline exceeded',value['message'])
            self.assertIn('Reconcile',value['next'])

    def test_debug_status_without_launch_identity_remains_uncertain(self):
        from operations.status import execute
        backend = Mock()
        backend.debug_status.return_value = {'status':'success','state':'running','pid':300}
        ctx = {'backend':backend,'runtime':{},'session':{'debugger':True,'state':'uncertain','app':None}}
        value = execute(type('Args',(),{'_context':ctx})(), ROOT)
        self.assertEqual(value['status'], 'uncertain')
        self.assertEqual(value['state'], 'uncertain')
        self.assertIsNone(ctx['session']['app'])

    def test_watch_preserves_breakpoint_and_retention(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            file=root/'main.swift';file.write_text('fixture')
            locator={'data_dir':folder,'runtime_identity':{'pid':200}}
            stopped={'status':'success','state':'paused','stops':[{'file':str(file),'line':9,'frame':'DISCARDED_FRAME'*1000,'breakpoints':[7]}]}
            cases=[(['set-breakpoint','--file',str(file),'--line','9'], {'breakpoint':7,'resolved':True}), (['continue','--keep-breakpoint'], {'kept':7})]
            for argv,facts in cases:
                output=io.StringIO()
                with patch.object(manager,'ROOT',root), patch.object(manager,'read_json',return_value=locator), patch.object(manager,'verify_identity',return_value=True), patch.object(manager,'connect',side_effect=[{'status':'success','state':'running','watch':True,**facts},stopped]), patch.object(sys,'argv',['manager',*argv]), contextlib.redirect_stdout(output):
                    self.assertEqual(manager.main(),0)
                self.assertIn('main.swift:9',output.getvalue())
                self.assertNotIn('breakpoint\":',output.getvalue())
                self.assertNotIn('DISCARDED_FRAME',output.getvalue())
                self.assertLessEqual(len(output.getvalue().encode()),200)

    def test_expired_queued_pause_never_calls_debugger(self):
        backend=Mock()
        ctx={'backend':backend,'session':{'debugger':True},'runtime':{}}
        args=manager.parser().parse_args(['pause']);args._deadline=0
        result=manager.dispatch(args,ctx)
        self.assertEqual(result['status'],'uncertain')
        backend.debug_status.assert_not_called()
        backend.debug_action.assert_not_called()
        with patch('operations.pause.debug_context') as debug:
            self.assertEqual(pause(args,ROOT)['status'],'uncertain')
            debug.assert_not_called()

    def test_pause_lock_expires_while_another_operation_owns_it(self):
        import time
        from lifecycle.state import operation_lock
        with tempfile.TemporaryDirectory() as folder:
            with operation_lock(Path(folder)):
                with self.assertRaisesRegex(TimeoutError, 'Pause expired while queued'):
                    with operation_lock(Path(folder), deadline=time.monotonic()+.02):
                        self.fail('An expired queued request acquired the lock')

    def test_sb_helper_load_does_not_import_another_package(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('independent_sb_helper', ROOT/'scripts/backend/lldb_controller.py')
        controller = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'lldb':Mock(),'lifecycle':None,'lifecycle.output':None}):
            spec.loader.exec_module(controller)
        self.assertTrue(callable(controller.handle))

    def test_controller_rejects_expired_interrupt_before_target_access(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('deadline_controller', ROOT/'scripts/backend/lldb_controller.py')
        controller = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'lldb':Mock()}):
            spec.loader.exec_module(controller)
        debugger = Mock()
        with self.assertRaises(TimeoutError):
            controller.handle(debugger, {'action':'pause','_deadline':0}, {})
        debugger.GetSelectedTarget.assert_not_called()

    def test_controller_consumes_state_events_without_recording(self):
        import importlib.util
        api = Mock()
        api.SBProcess.EventIsProcessEvent.return_value = True
        spec = importlib.util.spec_from_file_location('event_controller', ROOT/'scripts/backend/lldb_controller.py')
        controller = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'lldb':api}):
            spec.loader.exec_module(controller)
        listener = Mock()
        listener.GetNextEvent.side_effect = [True,False]
        controller.consume_events(listener)
        api.SBProcess.GetStateFromEvent.assert_called_once()

    def test_inspection_limits_preserve_output_and_error(self):
        for detail,limit in ((False,200),(True,500)):
            text=render({'status':'success','output':'tick = 4\n'+'界'*5000,'error':'command warning','_detail':detail},'debugger-command')
            self.assertIn('tick = 4',text)
            self.assertIn('command warning',text)
            self.assertIn('…',text)
            self.assertNotIn('log',text)
            self.assertLessEqual(len(text.encode()),limit)
        self.assertLessEqual(len(render({'status':'success','warning':'界'*5000}).encode()),200)

    def test_split_diagnostics_and_repeated_occurrences(self):
        parser=StreamDiagnostics()
        self.assertEqual(parser.feed('ordinary\nmain.swift:2: err'),'')
        self.assertIn('error: failure',parser.feed('or: failure\n  2 | bad\n    | ^\n'))
        self.assertIn('note:',parser.feed('main.swift:1: note: declared here\n'))
        self.assertEqual(parser.feed('ordinary\n'),'')
        self.assertEqual(parser.feed('warning: final',final=True),'warning: final')
        self.assertEqual(parser.feed('warning: final\n'),'warning: final')

    def test_error_wrapper_discards_transcript_and_duplicate_envelope(self):
        from lifecycle.diagnostics import diagnostics
        text = 'ORDINARY_TRANSCRIPT_MARKER\nmain.cpp:2: error: actual failure\n'
        result = diagnostics({'isError':True,'content':[{'type':'text','text':text}]})
        self.assertNotIn('ORDINARY_TRANSCRIPT_MARKER', result)
        self.assertEqual(result.count('actual failure'), 1)
        result = diagnostics({'structured':{'errors':[{'classification':'error','message':'actual failure'}]},'content':[{'text':text}]})
        self.assertEqual(result.count('actual failure'), 1)

    def test_routine_selection_keeps_normal_budget(self):
        text = render({'status':'needs_user_input','message':'Choose a product','choices':['Product'+str(index) for index in range(100)]})
        self.assertLessEqual(len(text.encode()), 200)
        self.assertIn('needs input',text)

    def test_failure_named_path_is_not_a_diagnostic(self):
        parser = StreamDiagnostics()
        self.assertEqual(parser.feed('/usr/bin/xcodebuild -project /tmp/failure-fixtures/App.xcodeproj\n'), '')
        self.assertIn('actual failure', parser.feed('/tmp/failure-fixtures/main.cpp:2: error: actual failure\n'))

    def test_ordinary_unterminated_output_does_not_accumulate(self):
        parser = StreamDiagnostics()
        for _ in range(50):
            self.assertEqual(parser.feed('ordinary-data-' * 1000), '')
            self.assertLessEqual(len(parser.pending), 4096)
        self.assertEqual(parser.feed('\nmain.swift:2: err'), '')
        self.assertIn('error: actual failure', parser.feed('or: actual failure\n'))

    def test_final_unterminated_error_preserves_failure_cause(self):
        from lifecycle.output import drain
        import os
        read, write = os.pipe()
        os.write(write, b'main.swift:9: error: final failure')
        os.close(write)
        ctx = {}
        drain(os.fdopen(read, 'rb'), ctx, 'Compiler')
        self.assertIn('final failure', ctx['last_diagnostic'])
        self.assertEqual(len(ctx['evidence']), 1)

    def test_unknown_app_still_cleans_verified_helpers(self):
        backend=Mock()
        ctx={'backend':backend,'runtime':{},'session':{'state':'uncertain','app':None,'debugger':False,'product':{},'dedicated':[{'pid':300}]}}
        with patch('operations.kill.terminate_identity',return_value={'status':'success'}) as terminate, patch('operations.kill.save_session'):
            result=kill(type('Args',(),{'_context':ctx})(),ROOT)
        terminate.assert_called_once_with({'pid':300})
        backend.close.assert_called_once_with(ctx)
        self.assertEqual(result['app'],'unverified')
        self.assertEqual(result['helpers'],'terminated')
        self.assertEqual(result['status'],'uncertain')

    def test_close_error_does_not_block_helper_fallback(self):
        backend = Mock()
        backend.close.side_effect = TimeoutError('Owned transport close failed')
        ctx = {'backend':backend,'runtime':{},'session':{'state':'uncertain','app':None,'debugger':False,'product':{},'dedicated':[{'pid':300}]}}
        with patch('operations.kill.terminate_identity',return_value={'status':'success'}) as terminate, patch('operations.kill.save_session'):
            result = kill(type('Args',(),{'_context':ctx})(), ROOT)
        terminate.assert_called_once_with({'pid':300})
        self.assertEqual(result['helpers'], 'terminated')
        self.assertEqual(result['app'], 'unverified')

    def test_recovery_releases_terminated_app_under_pid_one(self):
        from operations.kill import recover
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            app = {'pid':300,'parentPID':301}
            session = {'app':app,'state':'uncertain','dedicated':[], 'selection':{'configuration':'Debug'}}
            zombie = {'status':'zombie','identity':{'pid':300,'parentPID':1,'state':'Z'}}
            with patch('operations.kill.read_json',return_value=session), patch('operations.kill.capture_identity',return_value={'pid':300,'parentPID':1,'state':'Z'}), patch('operations.kill.terminate_identity',return_value=zombie) as terminate:
                result = recover(path, {'data_dir':folder})
            self.assertEqual(result['status'],'success')
            terminate.assert_called_once_with(app)
            self.assertEqual(json.loads((path/'session.json').read_text())['state'],'closed')

    def test_no_package_inheritance_or_reflective_delegation(self):
        import ast
        for path in (ROOT/'scripts/backend').glob('package_*.py'):
            tree=ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node,ast.ClassDef): self.assertFalse(node.bases)
                if isinstance(node,ast.FunctionDef): self.assertNotEqual(node.name,'__getattr__')

    def test_inspection_diagnostic_text_is_not_archived(self):
        """Keep inspection text in the returned value, never in diagnostic storage.
        An inspected string containing error labels must not bypass the byte limit.
        """
        if not (ROOT/'scripts/backend/apple.py').exists():
            self.skipTest('Native route has no Apple bridge')
        from backend import apple
        marker = 'error: DISCARDED_INSPECTION_MARKER' + 'x' * 1000
        connection = Mock()
        connection.call.return_value = {'structured':{'output':marker}}
        with tempfile.TemporaryDirectory() as folder:
            log = Path(folder)/'log.txt'
            ctx = {'runtime':{'bridge':connection},'log':log}
            result = apple.call(ctx, 'InvokeDebuggerCommand', {'command':'frame variable value'})
            self.assertEqual(result['output'], marker)
            self.assertFalse(log.exists())
            self.assertFalse(log.exists())

    def test_apple_helper_loaded_once(self):
        if not (ROOT/'scripts/backend/apple.py').exists(): self.skipTest('Native route has no Apple helper')
        from backend import apple
        ctx={'runtime':{}}
        response={'output':'SKILL_RESULT={"status":"success","state":"running"}'}
        with patch.object(apple,'call',return_value=response) as call:
            apple.debug_action(ctx,'status')
            apple.debug_action(ctx,'status')
        self.assertIn('spec_from_file_location',call.call_args_list[0].args[2]['command'])
        self.assertNotIn('spec_from_file_location',call.call_args_list[1].args[2]['command'])

    def test_mobile_combined_invokes_one_build_and_launch(self):
        if not (ROOT/'scripts/backend/mobilebuildmcp.py').exists(): self.skipTest('Combined route is Mobile-only')
        from backend import mobilebuildmcp as mobile
        args=type('Args',(),{'operation':'run','configuration':'Release','no_debugger':False,'_combined':True})()
        product={'product':'/fixture/App.app','executable':'/fixture/App.app/Contents/MacOS/App'}
        result={'status':'success','envelope':{'data':{'summary':{'status':'SUCCEEDED'},'artifacts':{'appPath':product['product'],'processId':200}}}}
        ctx={'runtime':{},'selection':{'arguments':['--mode','test']}}
        with patch.object(mobile,'macos_context'),patch.object(mobile,'matching_processes',return_value=[]),patch.object(mobile,'tool',return_value=result) as call,patch.object(mobile,'capture_identity',return_value={'pid':200}),patch.object(mobile,'verify_identity',return_value=True),patch.object(mobile,'traced',return_value=False):
            outcome=mobile.launch(args,ctx,product)
        call.assert_called_once_with(ctx,'build_run_macos',{'launchArgs':['--mode','test']})
        self.assertEqual(outcome['build']['status'],'success')
        self.assertEqual(outcome['status'],'success')

if __name__=='__main__': unittest.main()
