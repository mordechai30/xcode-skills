#!/usr/bin/env python3
"""Route macOS operations and retain the skill-owned backend connection.
Follow-up commands reach the same runtime through a relative local socket.
"""
import argparse
from lifecycle.runtime import namespace, serve, start
import json
from pathlib import Path
import sys
import time
import traceback

from lifecycle.channel import connect
from lifecycle.process import verify_identity
from lifecycle.state import append_log, operation_lock, read_json
from lifecycle.output import collect
from lifecycle.response import emit
from operations import build, run, set_breakpoint, pause, continue_session, kill, debugger_command

# Explicit public operation routing; no reflective module discovery.
OPERATIONS = {"build": build, "run": run, "set-breakpoint": set_breakpoint, "pause": pause,
              "continue": continue_session, "kill": kill, "debugger-command": debugger_command}


class RequestParser(argparse.ArgumentParser):
    """Keep help and argument errors on the bounded response path.
    Parsing never writes argparse diagnostics directly to stdout or stderr.
    """
    def error(self, message):
        """Return a parse error to the public entrypoint.
        Full argparse usage is replaced by the local examples reference.
        """
        raise ValueError(message)

    def print_help(self, file=None):
        """Provide compact help through the same public emitter.
        Detailed examples are packaged locally.
        """
        emit({"status": "success", "message": "build|run|set-breakpoint|pause|continue|kill|debugger-command. See references/examples.md."})
from operations.common import ask, context

# Installed package root used for this skill's locator and metadata.
ROOT = Path(__file__).resolve().parents[1]


def parser():
    """Create the shared CLI inputs.
    Private service inputs are accepted only by the runtime entry path.
    """
    result = RequestParser(description='Manage one macOS Xcode app or SwiftPM executable context.')
    result.add_argument('operation', choices=['build', 'run', 'set-breakpoint', 'pause', 'continue', 'kill', 'debugger-command'])
    for key in ('project', 'workspace', 'package', 'file', 'working-directory', 'derived-data'):
        result.add_argument('--' + key, type=Path)
    result.add_argument('--configuration', choices=['Debug', 'Release'])
    for key in ('scheme', 'destination', 'command'):
        result.add_argument('--' + key)
    result.add_argument('--target', '--product', dest='target')
    result.add_argument('--architecture', choices=['arm64', 'x86_64'])
    result.add_argument('--line', type=int)
    result.add_argument('--no-debugger', action='store_true')
    result.add_argument('--keep-breakpoint', action='store_true')
    result.add_argument('--arguments', nargs=argparse.REMAINDER, default=[])
    return result


def validate(args):
    """Reject incomplete requests before backend actions.
    Discovery fills selections only when exactly one candidate exists.
    """
    if sum(bool(getattr(args, key, None)) for key in ('project', 'workspace', 'package')) > 1:
        raise ValueError('Select one project, workspace, or package.')
    if args.operation in ('build', 'run') and (not (args.project or args.workspace or args.package) or not args.configuration):
        raise ValueError('Build and Run require a container and configuration.')
    if args.operation == 'set-breakpoint' and (not args.file or not args.file.is_file() or not args.line or args.line < 1):
        raise ValueError('Set Breakpoint requires an existing source file and a positive line.')
    if args.operation == 'debugger-command' and not args.command:
        raise ValueError('Inspection requires --command.')
    if args.keep_breakpoint and args.operation != 'continue':
        raise ValueError('--keep-breakpoint applies only to Continue.')


def dispatch(args, ctx):
    """Call one imported operation against the retained context.
    Save complete results and errors in the session log.
    """
    args._context = ctx
    try:
        value = OPERATIONS[args.operation].execute(args, ROOT)
    except ValueError as error:
        value = ask(str(error))
    except Exception as error:
        if ctx.get('log'):
            append_log(ctx['log'], 'Operation exception', ''.join(traceback.format_tb(error.__traceback__)) + type(error).__name__)
        value = {'status': 'uncertain', 'message': str(error)}
    if ctx.get('log'):
        append_log(ctx['log'], args.operation + ' outcome', value.get('message', value.get('status', 'uncertain')))
        value.setdefault('log', str(ctx['log']))
    collect(ctx)
    return value


def main():
    """Send a request and report verified outcomes.
    Interrupted watching leaves app and debugger state unchanged.
    """
    if len(sys.argv) > 1 and sys.argv[1] == '_serve':
        serve(Path(sys.argv[2]), ROOT, dispatch)
        return 0
    args = parser().parse_args()
    validate(args)
    values = {key: str(value.resolve()) if isinstance(value, Path) else value for key, value in vars(args).items()}
    with operation_lock(ROOT):
        locator = read_json(ROOT / '.active-session.json')
        if locator:
            if args.operation in ('build', 'run'):
                result = ask('Kill and complete cleanup before Build or another Run.', ['kill', 'wait'])
            elif not locator.get('runtime_identity') or not verify_identity(locator['runtime_identity']):
                if args.operation == 'kill':
                    from operations.kill import recover
                    result = recover(ROOT, locator)
                else:
                    result = ask('Retained runtime is lost. Use Kill recovery; do not attach another debugger.', ['kill', 'wait'])
            else:
                try:
                    result = connect(locator['data_dir'], 'm.sock', values, timeout=60)
                except (OSError, RuntimeError) as error:
                    if args.operation == 'kill':
                        from operations.kill import recover
                        result = recover(ROOT, locator)
                    else:
                        result = ask('Retained channel is lost: ' + str(error), ['kill', 'wait'])
        elif args.operation == 'run':
            result = start(namespace(values), ROOT)
            locator = read_json(ROOT / '.active-session.json')
        elif args.operation == 'build':
            ctx = context(args, ROOT)
            result = dispatch(args, ctx)
            close = getattr(ctx['backend'], 'close', None)
            if close:
                close(ctx)
        else:
            result = ask('No skill-owned app session exists. Use Run first.')
    if result.get('watch') and locator:
        try:
            while True:
                state = connect(locator['data_dir'], 'm.sock', {'operation': '_watch'})
                if state.get('state') != 'running':
                    result = state | {'log': result.get('log')}
                    break
                time.sleep(.3)
        except KeyboardInterrupt:
            result = {'status': 'success', 'message': 'Watching interrupted. Session remains available.'}
        except (OSError, RuntimeError) as error:
            result = ask('Watch connection lost. Use Kill or wait: ' + str(error))
    emit(result, args.operation)
    return 0 if result.get('status') == 'success' else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except ValueError as error:
        emit(ask(str(error)))
        raise SystemExit(2)
    except KeyboardInterrupt:
        emit({'status': 'uncertain', 'message': 'Request interrupted. Inspect the owned session before retry.'})
        raise SystemExit(130)
    except Exception as error:
        (ROOT / 'last-error.txt').write_text(traceback.format_exc())
        emit({'status': 'uncertain', 'message': str(error)})
        raise SystemExit(2)
