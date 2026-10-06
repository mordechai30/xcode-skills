"""Run a backend Clean and retain its outcome in the active Build log."""
from lifecycle.state import append_log


def execute(args, ctx):
    """Clean the selected configuration without launching an application.

    Return the backend result so Build can stop when prerequisite Clean fails.
    """
    try:
        result = ctx['backend'].clean(args, ctx)
    except (RuntimeError, OSError, TimeoutError) as error:
        result = {'status': 'uncertain', 'message': str(error)}
    append_log(ctx['log'], 'Clean result', result['status'])
    return result
