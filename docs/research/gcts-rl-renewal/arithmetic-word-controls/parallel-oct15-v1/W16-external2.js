// UNEXECUTED functions.exec accounting Source. ROOT supplies a concrete frozen
// capsule only after current Source reviews; this file makes no actual call now.
async function observeActualW16ExpectedUnknown({runtime, caller, root_plan, external_meter_output, cwd}) {
  const quote = value => "'" + String(value).replace(/'/g, "'\\''") + "'";
  const nativeMeter = {"path":"/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-full52-integration-source-20261015/Q_native_terminal_meter_v2.py","sha256":"0129830110b8f46a1cfd376ced0cd147aa2f224665b4a0cce36ae82f2106d67e","bytes":6734};
  const utility = [runtime.path,'-I','-S','-B',nativeMeter.path,external_meter_output,runtime.path,'-I','-S','-B',caller.path,root_plan.path].map(quote).join(' ');

  const command = 'if [ -e '+quote(external_meter_output)+' ] || [ -L '+quote(external_meter_output)+' ]; then exit 2; fi\nexec '+utility;
  const observations = [];
  const started_ms = Date.now();
  let result = await tools.exec_command({cmd:command,workdir:cwd,yield_time_ms:1000,max_output_tokens:1800,sandbox_permissions:'require_escalated',justification:'Run the authorized separate W16 expected-UNKNOWN control with native process accounting so /bin/ps can observe its owned census and verifier children.'});
  observations.push({kind:'exec_command',observed_ms:Date.now(),result});
  while (result.session_id !== undefined && Date.now()-started_ms<90000) {
    const session=result.session_id;
    result=await tools.write_stdin({session_id:session,chars:'',yield_time_ms:1000,max_output_tokens:1800});
    observations.push({kind:'write_stdin',session_id:session,observed_ms:Date.now(),result});
  }
  const terminal=result.exit_code!==undefined && result.session_id===undefined;
  const terminal_observed_ms=terminal ? Date.now() : null;
  let probe=null;
  // No project/helper/oracle/Q Source is loaded in this external observer.
  // It runs ONLY AFTER true caller+native meter terminal, in the same chosen
  // global kernel domain. ROOT must parse its exact complete line as integers
  // and require this observed_ns < originalG+55 with timely readiness before20.
  // This deliberate20-late control never earns successful20 admission.
  const postTerminalNativeSource = [
    'import time',
    'clock, clock_id = time.clock_gettime_ns, time.CLOCK_MONOTONIC',
    'import json, types',
    "if type(clock) is not types.BuiltinFunctionType or clock.__module__ != 'time' or clock.__name__ != 'clock_gettime_ns' or type(clock_id) is not int: raise ValueError('native global clock callable/ID')",
    "if time.clock_gettime_ns is not clock or type(time.CLOCK_MONOTONIC) is not int or time.CLOCK_MONOTONIC != clock_id: raise ValueError('original native global clock')",
    'value = clock(clock_id)',
    "if time.clock_gettime_ns is not clock or type(time.CLOCK_MONOTONIC) is not int or time.CLOCK_MONOTONIC != clock_id or type(value) is not int or not 0 <= value < 2**63: raise ValueError('exact unchanged native observation')",
    "print(json.dumps({'schema':'ROOT-Q-post-terminal-native-observation-v1','CLOCK_DOMAIN':'time.clock_gettime_ns(time.CLOCK_MONOTONIC)','observed_ns':value,'clock_id':clock_id,'ROOT_resource_accepted':False},sort_keys=True,separators=(',',':')),flush=True)"
  ].join('\n');
  if (terminal) {
    observations.push({kind:'caller_terminal_boundary',observed_ms:terminal_observed_ms});
    const probeCommand=[runtime.path,'-I','-S','-B','-c',postTerminalNativeSource].map(quote).join(' ');
    probe=await tools.exec_command({cmd:probeCommand,workdir:cwd,yield_time_ms:1000,max_output_tokens:512});
    observations.push({kind:'post_terminal_native_exec',observed_ms:Date.now(),result:probe});
    while (probe.session_id!==undefined && Date.now()-started_ms<90000) {
      const session=probe.session_id;
      probe=await tools.write_stdin({session_id:session,chars:'',yield_time_ms:1000,max_output_tokens:512});
      observations.push({kind:'post_terminal_native_poll',session_id:session,observed_ms:Date.now(),result:probe});
    }
  }
  const completed_observation_ms=Date.now();
  const elapsed_ms=completed_observation_ms-started_ms;
  let previous_ms=started_ms;
  const wall_clock_brackets_valid=Number.isFinite(started_ms) && started_ms>=0
    && observations.every(item=>{const valid=Number.isFinite(item.observed_ms)&&item.observed_ms>=previous_ms;previous_ms=item.observed_ms;return valid;})
    && Number.isFinite(completed_observation_ms) && completed_observation_ms>=previous_ms
    && Number.isFinite(elapsed_ms) && elapsed_ms>=0;
  const probeComplete=probe!==null && probe.exit_code===0 && probe.session_id===undefined
    && typeof probe.output==='string' && probe.output.length<4096
    && probe.output.endsWith('\n') && probe.output.split('\n').length===2;
  return {schema:'ROOT-Q-W16-actual-tool-observations-v1',
    caller_source:caller,runtime,root_plan,external_terminal_meter:nativeMeter,
    external_terminal_meter_output:external_meter_output,
    terminal_meter_parse_and_raw_EOF_authentication_pending:true,
    started_ms,terminal_observed_ms,completed_observation_ms,elapsed_ms,finish_reserve_ms:1000,
    actual_terminal_observed:terminal,actual_exit_code:terminal?result.exit_code:null,
    unfinished_session_id:terminal?null:result.session_id,
    post_terminal_native_probe_complete:probeComplete,
    unfinished_probe_session_id:probe!==null&&probe.session_id!==undefined?probe.session_id:null,
    post_terminal_native_output:probeComplete?probe.output:null,
    post_terminal_native_integer_parse_and_W16_failure55_gate_pending:true,
    wall_clock_brackets_valid,
    external_owned60_candidate:terminal&&probeComplete&&wall_clock_brackets_valid&&elapsed_ms<=60000,
    external_caller90_with_finish1_candidate:terminal&&probeComplete&&wall_clock_brackets_valid&&elapsed_ms+1000<=90000,
    observations,
    scope:'W16 expectedUNKNOWN only: timely full census/readiness must precede originalG+20; actual same live verifier wait is rejected at/after20 and complete kill/reap/output/terminal must precede originalG+55. A successful20 stage is always false. External Date wall includes actual tool startup, interpreter/caller Source compilation/time import, true caller exit, native meter printing and post-terminal pinned-Python observation. Native W16 failure55 closure requires caller process exit before genuine post-terminal global observed_ns < original failure deadline; observed20-late is expected and never a successful20 resource/proof qualification. Native meter full EOF must yield terminal caller maxRSS; recompute the complete Owner closed child-lifetime overlap plus serialized observer maximum conservatively with that terminal caller peak. Meter/probe observer memory excluded like tool executor; all wall overhead charged. Only the initial native-meter/early-caller exec requests require_escalated process-accounting access for the genuine coordinator /bin/ps observer. This Source selection is not an actual execution grant; ROOT must separately authorize the concrete W16-only invocation. Polling and the postterminal clock-only probe retain their prior APIs. Root acceptance remains false until separate whole saved reconciliation.',
    ROOT_resource_accepted:false,ROOT_primary_accepted:false,full52_qualified:false,
    original_Q_theorem_accepted:false,successful20_stage:false,W16_expected_UNKNOWN_observation_pending:true,actual_invocation_only_if_ROOT_runs_later:true};
}
