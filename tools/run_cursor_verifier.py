"""Start the external Cursor CLI in read-only mode against the completed pilot.

Requires user authorization for sending workspace context to Cursor.
No credentials, global settings, DCC or MCP approval are changed.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from dt_ai.core.run_record import RunRecord,atomic_json,file_evidence


def owned_command(record, attempt, stage, argv, timeout):
    """Capture the CLI under the existing ledger's timeout/tree ownership."""
    config = attempt / (stage + '-command.json')
    outputs = {name: attempt / (stage + suffix) for name, suffix in
               [('process', '-process.json'), ('transcript', '-stdout.jsonl'), ('stderr', '-stderr.log')]}
    atomic_json(config, {'argv': argv, 'cwd': str(ROOT),
                         **{name: str(path) for name, path in outputs.items()}})
    record.inputs[stage + '_command'] = str(config)
    return record.run_stage(stage,
        [sys.executable, str(Path(__file__).resolve()), '--worker', str(config)],
        outputs, cwd=ROOT, timeout=timeout)


def summarize(directory):
    directory=Path(directory).resolve()
    facts=json.loads((directory/'cli-evidence.json').read_text(encoding='utf-8'))
    if facts.get('evidence_version') != 2 or facts.get('stage_name') != 'cursor_verifier':
        raise ValueError('Legacy or unbound evidence cannot establish verification')
    stage=facts['stage']
    if stage.get('status') not in ('produced', 'verified'):
        raise ValueError('Stage is not produced or verified')
    record = RunRecord(directory, facts['inputs'], facts['context'])
    matches = [a['stages'].get('cursor_verifier') for a in record.read()['attempts']
               if a['stages'].get('cursor_verifier', {}).get('signature') == stage.get('signature')]
    if len(matches) != 1 or matches[0] != stage:
        raise ValueError('Evidence does not match the authoritative run ledger')
    if record.fingerprint() != stage['input_fingerprint']:
        raise ValueError('Verification inputs changed')
    outputs = {name: item['path'] for name, item in stage['outputs'].items()}
    if file_evidence(outputs) != stage['outputs']:
        raise ValueError('Saved CLI outputs or transcript changed')
    stream=Path(stage['outputs']['transcript']['path'])
    transcript = stream.read_bytes()
    if hashlib.sha256(transcript).hexdigest() != stage['outputs']['transcript']['sha256']:
        raise ValueError('Transcript changed during readback')
    if json.loads(Path(outputs['process']).read_text(encoding='utf-8')).get('cli_exit_code') != 0:
        raise ValueError('CLI process did not exit successfully')
    events=[json.loads(line) for line in transcript.decode('utf-8').splitlines() if line.startswith('{')]
    results=[e for e in events if e.get('type')=='result']
    if stage.get('returncode')!=0 or not results or results[-1].get('is_error') is not False or results[-1].get('subtype')!='success':
        raise ValueError('CLI success not established by exit code and stream result')
    tasks=[e for e in events if e.get('type')=='tool_call' and e.get('subtype')=='completed'
           and 'taskToolCall' in e.get('tool_call',{})]
    delegated=[e for e in tasks if e['tool_call']['taskToolCall'].get('args',{}).get('subagentType',{}).get('custom',{}).get('name')=='dt-verifier'
               and 'success' in e['tool_call']['taskToolCall'].get('result',{})]
    kinds=sorted({name for e in events for name in e.get('tool_call',{})})
    reads=sorted({e['tool_call']['readToolCall']['args']['path'] for e in events
                  if e.get('subtype')=='completed' and 'readToolCall' in e.get('tool_call',{})})
    summary={'cli_exit_code':0,'stream_result':'success','duration_ms':results[-1].get('duration_ms'),
             'actual_dt_verifier_invoked':bool(delegated),'delegation_tool':'taskToolCall' if delegated else None,
             'delegation_call_ids':[e['call_id'] for e in delegated],
             'observed_tool_types':kinds,'observed_read_paths':reads,
             'no_observed_shell_dcc_mcp_or_write_calls':set(kinds)<= {'taskToolCall','readToolCall'},
             'transcript':str(stream),'transcript_sha256':hashlib.sha256(transcript).hexdigest(),
             'delivery_passed':False,'summary_generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             'limitation':'Verification of CLI connection and actual delegation; raw DCC artifacts not rechecked by this narrow document review'}
    atomic_json(directory/'cursor-verifier-summary.json',summary)
    verdict=results[-1].get('result','')
    (directory/'verdict.md').write_text('# Cursor CLI verifier verdict\n\n'+str(verdict)+'\n',encoding='utf-8')
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    operation=parser.add_mutually_exclusive_group(required=True)
    operation.add_argument('--run-id')
    operation.add_argument('--summarize',type=Path,help='Parse an existing transcript locally; no CLI invocation')
    parser.add_argument('--cli',type=Path,default=Path(os.environ.get('LOCALAPPDATA', ''))/'cursor-agent/agent.cmd')
    parser.add_argument('--timeout',type=int,default=180)
    args=parser.parse_args()
    if args.timeout <= 0: parser.error('--timeout must be positive')
    if args.summarize:
        print(json.dumps(summarize(args.summarize),ensure_ascii=True))
        return
    cli=args.cli.resolve()
    if not cli.is_file():raise FileNotFoundError(cli)
    relative=['.cursor/agents/dt-verifier.md','jobs/ORCH-OBR22-NPM/STATE.md',
              'jobs/ORCH-OBR22-NPM/pilot-spec.json',
              'docs/organization/local-orchestration/execution-evidence.json',
              'docs/organization/local-orchestration/REVIEW.md']
    inputs={p:ROOT/p for p in relative}
    inputs['launcher']=Path(__file__).resolve()
    inputs['cli_launcher']=cli
    prompt=('Read-only verification for the local Digital Twin pilot. Use the actual project dt-verifier subagent if this CLI supports custom subagents. '
            'If delegation is unavailable say explicitly that this is a direct CLI review and do not pretend a subagent ran. '
            'Read only these requested evidence files apart from automatically loaded workspace instructions: '+', '.join(relative)+'. '
            'Do not edit files, execute shell commands, use MCP or DCC, install tools or read credentials. '
            'Report in Russian the verified scope, technical transfer status, full delivery status, AGR counts, remaining gates and evidence paths. '
            'Report whether actual custom subagent delegation happened and cite the tool used. A configured agent file alone does not prove delegation. '
            'Use the executed evidence rather than treating the original spec as proof of execution.')
    record=RunRecord.create(ROOT/'jobs/ORCH-OBR22-NPM/cli-runs',args.run_id,inputs,
                            {'cli':str(cli),'mode':'ask','sandbox':'disabled (Windows unsupported; allowlist mode)',
                             'authorization':'User 2026-10-01 explicitly permitted these five files and workspace instructions to the Cursor service',
                             'prompt':prompt})
    attempt=record.new_attempt()
    probe=owned_command(record, attempt, 'cursor_version', [str(cli), '--version'], args.timeout)
    atomic_json(record.directory/'cli-version-evidence.json', {'stage':probe,'delivery_passed':False})
    if probe['status'] not in ('produced','verified') or probe.get('returncode') != 0:
        raise SystemExit(1)
    version=Path(probe['outputs']['transcript']['path']).read_text(encoding='utf-8').strip()
    record.inputs['cli_version'] = probe['outputs']['transcript']['path']
    record.context['version'] = version
    command=[str(cli),'--workspace',str(ROOT),'--mode','ask','--sandbox','disabled',
             '--print','--trust','--output-format','stream-json',prompt]
    result=owned_command(record, attempt, 'cursor_verifier', command, args.timeout)
    evidence={'cli':str(cli),'version':version,'mode':'ask','sandbox':'disabled (Windows unsupported; allowlist mode)',
              'evidence_version':2,'stage_name':'cursor_verifier',
              'inputs':record.inputs,'context':record.context,
              'stage':result,'delivery_passed':False,
              'limitation':'CLI exit status is not proof of actual subagent invocation or model delivery'}
    atomic_json(record.directory/'cli-evidence.json',evidence)
    print(json.dumps({'run':str(record.directory),'status':result['status'],
                      'stdout':str(attempt/'cursor_verifier-stdout.jsonl'),
                      'stderr':str(attempt/'cursor_verifier-stderr.log')},ensure_ascii=False))
    if result['status'] not in ('produced','verified'):raise SystemExit(1)
    summarize(record.directory)


if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--worker':
        config=json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
        with Path(config['transcript']).open('xb') as stdout, Path(config['stderr']).open('xb') as stderr:
            code=subprocess.call(config['argv'],cwd=config['cwd'],stdout=stdout,stderr=stderr)
        atomic_json(config['process'],{'cli_exit_code':code})
        raise SystemExit(code)
    main()
