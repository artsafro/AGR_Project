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
    verifier = module()
    source = directory/'input.txt'
    source.write_text('synthetic input', encoding='utf-8')
    record = verifier.RunRecord.create(directory, 'run', {'source':source}, {'fixture':'synthetic'})
    directory = record.directory
    log=directory/'stream.jsonl'
    log.write_text('\n'.join(json.dumps(e) for e in events),encoding='utf-8')
    process = directory/'process.json'
    process.write_text(json.dumps({'cli_exit_code':0}), encoding='utf-8')
    record.new_attempt()
    stage = {'status':'produced','returncode':0,'signature':'synthetic-signature',
             'input_fingerprint':record.fingerprint(),
             'outputs':verifier.file_evidence({'transcript':log,'process':process})}
    ledger = record.read()
    ledger['attempts'][0]['stages']['cursor_verifier'] = stage
    verifier.atomic_json(record.path, ledger)
    verifier.atomic_json(directory/'cli-evidence.json', {'evidence_version':2,
        'stage_name':'cursor_verifier','inputs':record.inputs,'context':record.context,'stage':stage})
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


SUCCESS = {'type':'result','subtype':'success','is_error':False,'result':'synthetic'}


def test_modified_transcript_preserves_previous_verdict(tmp_path):
    directory = fixture_run(tmp_path, [SUCCESS])
    verifier = module()
    verifier.summarize(directory)
    original = {name:(directory/name).read_bytes() for name in
                ('cursor-verifier-summary.json','verdict.md')}
    (directory/'stream.jsonl').write_text(json.dumps(SUCCESS)+'\n'+json.dumps(SUCCESS), encoding='utf-8')
    with pytest.raises(ValueError, match='changed'):
        verifier.summarize(directory)
    assert all((directory/name).read_bytes() == data for name,data in original.items())


@pytest.mark.parametrize('mutation', ['failed', 'ledger', 'inputs', 'legacy'])
def test_invalid_binding_preserves_existing_reports(tmp_path, mutation):
    directory = fixture_run(tmp_path, [SUCCESS])
    verifier = module()
    verifier.summarize(directory)
    previous = (directory/'cursor-verifier-summary.json').read_bytes()
    previous_verdict = (directory/'verdict.md').read_bytes()
    facts = json.loads((directory/'cli-evidence.json').read_text())
    if mutation == 'failed':
        facts['stage']['status'] = 'failed'
    elif mutation == 'ledger':
        facts['stage']['signature'] = 'not-authoritative'
    elif mutation == 'inputs':
        Path(facts['inputs']['source']).write_text('changed input')
    else:
        facts.pop('evidence_version')
    verifier.atomic_json(directory/'cli-evidence.json', facts)
    with pytest.raises(ValueError): verifier.summarize(directory)
    assert (directory/'cursor-verifier-summary.json').read_bytes() == previous
    assert (directory/'verdict.md').read_bytes() == previous_verdict


def test_owned_command_passes_timeout_and_declares_hashed_transcript(tmp_path, monkeypatch):
    verifier = module()
    record = verifier.RunRecord.create(tmp_path, 'owned', {}, {})
    attempt = record.new_attempt()
    calls = []
    monkeypatch.setattr(record, 'run_stage', lambda *args, **kwargs: calls.append((args,kwargs)) or {'status':'interrupted'})
    result = verifier.owned_command(record, attempt, 'cursor_version', ['synthetic-cli','--version'], 2)
    assert result['status'] == 'interrupted'
    args, kwargs = calls[0]
    assert kwargs['timeout'] == 2
    assert args[0] == 'cursor_version'
    assert set(args[2]) == {'process','transcript','stderr'}
    assert args[1][-2] == '--worker'


def test_version_failure_records_evidence_and_never_starts_review(tmp_path, monkeypatch):
    verifier = module()
    monkeypatch.setattr(verifier, 'ROOT', tmp_path)
    cli = tmp_path/'synthetic-cli.cmd'
    cli.write_text('fixture only')
    for path in ['.cursor/agents/dt-verifier.md','jobs/ORCH-OBR22-NPM/STATE.md',
                 'jobs/ORCH-OBR22-NPM/pilot-spec.json',
                 'docs/organization/local-orchestration/execution-evidence.json',
                 'docs/organization/local-orchestration/REVIEW.md']:
        file = tmp_path/path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text('synthetic')
    calls = []
    def interrupted(record, attempt, stage, argv, timeout):
        calls.append((stage, argv, timeout))
        return {'status':'interrupted','reason':'timeout'}
    monkeypatch.setattr(verifier, 'owned_command', interrupted)
    monkeypatch.setattr('sys.argv', ['verifier','--run-id','synthetic','--cli',str(cli),'--timeout','1'])
    with pytest.raises(SystemExit) as error: verifier.main()
    assert error.value.code == 1
    assert calls == [('cursor_version', [str(cli),'--version'], 1)]
    evidence = tmp_path/'jobs/ORCH-OBR22-NPM/cli-runs/synthetic/cli-version-evidence.json'
    assert json.loads(evidence.read_text())['stage']['reason'] == 'timeout'


def test_synthetic_worker_outputs_are_ledger_bound(tmp_path):
    """Only a local Python fixture is executed; no Cursor service is invoked."""
    import sys
    verifier = module()
    record = verifier.RunRecord.create(tmp_path, 'worker', {}, {'fixture':'synthetic'})
    attempt = record.new_attempt()
    result = verifier.owned_command(record, attempt, 'cursor_verifier',
        [sys.executable, '-c', 'print(' + repr(json.dumps(SUCCESS)) + ')'], 10)
    assert result['status'] == 'produced'
    assert verifier.file_evidence({k:v['path'] for k,v in result['outputs'].items()}) == result['outputs']
    verifier.atomic_json(record.directory/'cli-evidence.json', {'evidence_version':2,
        'stage_name':'cursor_verifier','inputs':record.inputs,'context':record.context,'stage':result})
    assert verifier.summarize(record.directory)['stream_result'] == 'success'
