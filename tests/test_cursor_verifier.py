"""Synthetic stream fixtures validate claims; they are not live CLI evidence."""
import importlib.util
import json
from pathlib import Path
import pytest


def module():
    path=Path(__file__).resolve().parents[1]/'tools/run_cursor_verifier.py'
    spec=importlib.util.spec_from_file_location('cursor_verifier_fixture',path)
    result=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def fixture_run(directory,events):
    log=directory/'stream.jsonl'
    log.write_text('\n'.join(json.dumps(e) for e in events),encoding='utf-8')
    (directory/'cli-evidence.json').write_text(json.dumps({'stage':{'returncode':0,'stdout':str(log)}}),encoding='utf-8')
    return directory


def test_exit_zero_without_result_is_not_success(tmp_path):
    with pytest.raises(ValueError):
        module().summarize(fixture_run(tmp_path,[]))


def test_started_delegation_is_not_completed_invocation(tmp_path):
    events=[{'type':'tool_call','subtype':'started','tool_call':{'taskToolCall':{'args':{'subagentType':{'custom':{'name':'dt-verifier'}}}}}},
            {'type':'result','subtype':'success','is_error':False,'result':'synthetic'}]
    assert module().summarize(fixture_run(tmp_path,events))['actual_dt_verifier_invoked'] is False


def test_custom_completed_task_and_unexpected_tool_are_distinguished(tmp_path):
    events=[{'type':'tool_call','subtype':'completed','call_id':'synthetic',
             'tool_call':{'taskToolCall':{'args':{'subagentType':{'custom':{'name':'dt-verifier'}}},'result':{'success':{}}}}},
            {'type':'tool_call','subtype':'completed','tool_call':{'shellToolCall':{}}},
            {'type':'result','subtype':'success','is_error':False,'result':'synthetic'}]
    result=module().summarize(fixture_run(tmp_path,events))
    assert result['actual_dt_verifier_invoked'] is True
    assert result['no_observed_shell_dcc_mcp_or_write_calls'] is False
