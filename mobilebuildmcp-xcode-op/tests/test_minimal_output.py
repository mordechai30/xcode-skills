"""Check useful public output and forbidden retention through real routing."""
import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import manager
from lifecycle.output import record_detail
from lifecycle.diagnostics import diagnostics
from lifecycle.state import append_log
from lifecycle.response import render


class MinimalOutputTests(unittest.TestCase):
    def test_public_build_surfaces_warning_and_logs_exact_response(self):
        """Exercise manager parsing, dispatch, rendering, and log emission.
        Backend diagnostics must appear publicly without setup or metadata.
        """
        with tempfile.TemporaryDirectory() as folder:
            project=Path(folder)/'App.xcodeproj';project.mkdir()
            log=Path(folder)/'log.txt'
            ctx={'runtime':{},'backend':Mock(),'log':log,'data_dir':Path(folder)}
            def build(args,root):
                record_detail(ctx,'Diagnostics','main.swift:12: warning: unused value')
                append_log(log,'Stage','GetTargetBuildSettings INTERNAL_MARKER')
                return {'status':'success','pid':999,'debugger':False,'log':str(log)}
            output=io.StringIO()
            with patch.object(manager,'ROOT',Path(folder)),patch.object(manager,'context',return_value=ctx),patch.object(manager.OPERATIONS['build'],'execute',side_effect=build),patch.object(sys,'argv',['manager','build','--project',str(project),'--configuration','Debug']),contextlib.redirect_stdout(output):
                self.assertEqual(manager.main(),0)
            public=output.getvalue();stored=log.read_text()
            self.assertIn('Build succeeded.',public)
            self.assertIn('warning: unused value',public)
            self.assertLessEqual(len(public.encode()),200)
            self.assertTrue(stored.endswith(public))
            self.assertNotIn('INTERNAL_MARKER',stored)
            self.assertNotIn('999',public)
            self.assertNotIn('debugger',public)

    def test_diagnostic_fields_ignore_unrelated_json_strings(self):
        """Read explicit domain diagnostic fields only.
        Arbitrary metadata and rendered envelopes must not become log data.
        """
        value={'structured':{'data':{'diagnostics':[{'severity':'warning','message':'actual warning'}],'artifacts':{'metadata':'error: PRIVATE_MARKER'}}},'content':[{'text':'error: DUPLICATE_MARKER'}]}
        result=diagnostics(value)
        self.assertIn('actual warning',result)
        self.assertNotIn('PRIVATE_MARKER',result)
        self.assertNotIn('DUPLICATE_MARKER',result)

    def test_inspection_is_the_only_success_payload(self):
        """Hide routine details but preserve requested values and errors.
        Large Unicode inspection output remains valid UTF-8 within its allowance.
        """
        value={'status':'success','pid':999,'debugger':True,'breakpoint':3,'removed':3,'message':'PRIVATE_MARKER','output':'tick = 4'}
        self.assertEqual(render(value,'continue'),'Continue succeeded.\n')
        inspected=render(value,'debugger-command')
        self.assertIn('tick = 4',inspected)
        self.assertNotIn('PRIVATE_MARKER',inspected)
        for detail,limit in ((False,200),(True,500)):
            text=render({'status':'success','output':'tick = 4\n'+'界'*1000,'error':'actual command error','_detail':detail},'debugger-command')
            self.assertIn('tick = 4',text)
            self.assertIn('actual command error',text)
            self.assertIn('…',text)
            self.assertLessEqual(len(text.encode()),limit)

    def test_apple_inspection_uses_completed_sb_command(self):
        """Use LLDB completion evidence despite a partial outer response.
        The caller command executes once in the existing helper.
        """
        if not (ROOT/'scripts/backend/apple.py').exists():
            self.skipTest('Apple helper only')
        from backend import apple
        result={'output':'SKILL_RESULT={"status":"success","output":"tick = 4","current":{"state":"paused"}}','isWaitingForMore':True}
        with patch.object(apple,'call',return_value=result) as call:
            value=apple.debug_action({'runtime':{'sb_helper_loaded':True}},'command',command='frame variable tick')
        self.assertEqual(value['status'],'success')
        self.assertEqual(value['output'],'tick = 4')
        call.assert_called_once()
        self.assertIn('"action": "command"',call.call_args.args[2]['command'])

    def test_mobile_package_uses_build_then_owned_launch(self):
        """Avoid background launcher PID ambiguity and premature Build success.
        The resolved executable uses one direct launch after the package Build.
        """
        from argparse import Namespace
        from backend.package_mobile import Adapter
        base=Mock()
        adapter=Adapter(base)
        args=Namespace(configuration='Release',operation='run',no_debugger=False)
        ctx={'selection':{'package':'/package','target':'Product','configuration':'Release'},'runtime':{}}
        self.assertFalse(adapter.embedded_build(args))
        with patch.object(adapter,'mobile_values',return_value={'packagePath':'/package','configuration':'Release'}):
            adapter.build(args,ctx)
        self.assertEqual(base.tool.call_args.args[1],'swift_package_build')
        product={'executable':'/package/.build/release/Product'}
        with patch('backend.package_mobile.native.launch',return_value={'status':'success','state':'exited'}) as launch:
            self.assertEqual(adapter.launch(args,ctx,product)['state'],'exited')
        launch.assert_called_once_with(args,ctx,product)
        self.assertEqual(base.tool.call_count,1)

    def test_setting_while_paused_is_not_reported_as_a_hit(self):
        """Distinguish breakpoint installation from actual hit evidence.
        Paused execution alone cannot establish that the new breakpoint fired.
        """
        value={'status':'success','state':'paused','resolved':True,'location':'main.swift:9','watch':False}
        self.assertNotIn('hit',render(value,'set-breakpoint'))
        value.update(watch=True,_hit=True)
        self.assertIn('hit: main.swift:9',render(value,'set-breakpoint'))

    def test_debug_app_diagnostics_forward_without_an_extra_archive(self):
        """Forward filtered child diagnostics to the existing parent reader.
        The parent performs the sole log write and public warning collection.
        """
        output=io.StringIO()
        with contextlib.redirect_stdout(output):
            record_detail({'forward':True},'App diagnostics','main.swift:9: warning: runtime warning')
        with tempfile.TemporaryDirectory() as folder:
            log=Path(folder)/'log.txt';ctx={'log':log}
            record_detail(ctx,'Diagnostics',output.getvalue().strip())
            self.assertEqual(log.read_text().count('runtime warning'),1)
            self.assertIn('runtime warning',ctx['public_warning'])

    def test_partial_startup_requeries_only_state(self):
        """Reconcile a late startup reply with one read-only state request.
        The helper is loaded once and no launch or mutation is repeated.
        """
        if not (ROOT/'scripts/backend/apple.py').exists():
            self.skipTest('Apple helper only')
        from backend import apple
        responses=[{'output':'','isWaitingForMore':True},{'output':'SKILL_RESULT={"status":"success","state":"running","pid":200}','isWaitingForMore':False}]
        with patch.object(apple,'call',side_effect=responses) as call:
            value=apple.debug_status({'runtime':{}})
        self.assertEqual(value['state'],'running')
        self.assertEqual(call.call_count,2)
        self.assertIn('spec_from_file_location',call.call_args_list[0].args[2]['command'])
        self.assertNotIn('spec_from_file_location',call.call_args_list[1].args[2]['command'])

    def test_interrupted_request_logs_the_exact_public_bytes(self):
        """Retain interrupted request output without querying the backend again.
        The same bounded text is emitted and appended to the owned log.
        """
        with tempfile.TemporaryDirectory() as folder:
            log=Path(folder)/'log.txt';output=io.StringIO()
            with patch.object(manager,'read_json',side_effect=[{'data_dir':folder},{'log':str(log)}]),patch.object(sys,'argv',['manager','set-breakpoint']),contextlib.redirect_stdout(output):
                manager.emit_exception({'status':'uncertain','message':'Request interrupted. Use Status.'})
            self.assertEqual(output.getvalue(),log.read_text())
            self.assertLessEqual(len(output.getvalue().encode()),500)

    def test_build_command_summary_is_not_diagnostic_context(self):
        """Drop repeated compiler invocation summaries after Build failure.
        Preserve the actual source error and its caret context.
        """
        value='main.cpp:21: error: actual failure\n 21 | #error actual failure\n | ^\n** BUILD FAILED **\nThe following build commands failed:\n\tCompileC /private/build/main.o /private/source/main.cpp normal arm64\n\tBuilding project App with scheme App'
        result=diagnostics(value)
        self.assertIn('#error actual failure',result)
        self.assertNotIn('CompileC',result)
        self.assertNotIn('Building project',result)
        self.assertNotIn('commands failed',result)
