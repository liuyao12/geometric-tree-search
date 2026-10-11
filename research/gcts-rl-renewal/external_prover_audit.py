"""Replay saved external derivations and distrust provenance/step mutations."""
import argparse,copy,json,pathlib,re,time
from external_prover_inputs import sha,make_input
from external_prover_check import check_output,records,leaves,replay_refutation,grounding,closed

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='.gcts-active/external-prover-20261011');a=ap.parse_args();out=pathlib.Path(a.output)
    began=time.perf_counter();s=json.loads((out/'summary.json').read_text());plan=json.loads((out/'plan.json').read_text())
    if sha((out/'plan.json').read_bytes())!=s['plan_sha256']:raise ValueError('frozen plan changed')
    for p,h in s['source_sha256'].items():
        if sha(pathlib.Path(p).read_bytes())!=h:raise ValueError('measured source changed')
    reader=pathlib.Path('docs/research/gcts-rl-renewal/first-order-families-reader-001.json').read_bytes()
    if sha(reader)!=s['reader_sha256']:raise ValueError('donor reader changed')
    cases={c['spec']['id']:c for c in json.loads(reader)['cases']}
    successful=0;steps=0;mutants=[];trees=0
    for obs in s['observations']:
        library=obs['lane']!='theory-only';stem=obs['case']+'-'+('library' if library else 'theory')
        p=out/(stem+'.p');m=json.loads(p.with_suffix('.mapping.json').read_text());fresh=make_input(cases[obs['case']],library);fresh['input_path']=str(p)
        if fresh!=m or sha(p.read_bytes())!=obs['input_sha256']:raise ValueError('input mapping provenance')
        name=stem+'-r'+str(obs['repetition']);text=(out/(name+'.tstp')).read_text()
        if sha(text)!=obs['output_sha256'] or sha((out/(name+'.stderr')).read_bytes())!=obs['stderr_sha256']:raise ValueError('output hash')
        if obs['certificate_status']!='checked_complete_derivation':continue
        checked=check_output(text,m,str(p));successful+=1;steps+=checked['steps'];rs=records(text)
        # Alter a file-backed hypothesis while preserving valid TPTP syntax.
        source=next(r for r in rs if r['source'].get('head')=='file' and r['role']!='conjecture')
        pattern=r'((?:fof|cnf)\('+re.escape(source['name'])+r',\s*'+re.escape(source['role'])+r',).*?(,\s*file\()'
        altered,n=re.subn(pattern,r'\g<1> $false\g<2>',text,count=1)
        if n!=1:raise ValueError('mutation construction')
        last=rs[-1]['name']
        # The final contradiction has no logical premise in this corruption.
        old=next(line for line in text.splitlines() if line.startswith('cnf('+last+','))
        new='cnf('+last+', '+rs[-1]['role']+", ($false), inference(cn,[status(thm)],[]), ['proof'])."
        missing=text.replace(old,new,1)
        broken=text.replace('inference(assume_negation,[status(cth)],[goal])','inference(assume_negation,[status(cth)],[])',1)
        for tag,mutant in [('input-formula',altered),('unsupported-empty-parent',missing),('missing-negated-goal',broken)]:
            try:check_output(mutant,m,str(p))
            except ValueError as e:mutants.append(dict(observation=name,mutation=tag,status='rejected',reason=str(e)))
            else:raise ValueError('accepted corrupt trace '+name+' '+tag)
        # Reconstruct local clause instances and corrupt each generated proof
        # tree. No empty branch may justify a root equality contradiction.
        byname={r['name']:r for r in rs}
        for ch in checked['checks']:
            if 'refutation' not in ch:continue
            formulas=[closed(byname[n]['formula']) for n in ch['parents']]+[('not',closed(byname[ch['name']]['formula']))]
            cs,_=grounding(formulas);bad=copy.deepcopy(ch['refutation']);bad['tree']=['euf']
            try:replay_refutation(cs,bad)
            except ValueError:trees+=1
            else:raise ValueError('accepted empty equality conflict')
    result=dict(status='passed',successful_derivations=successful,proof_steps=steps,rejected_recipient_trace_corruptions=len(mutants),rejected_local_refutation_corruptions=trees,mutations=mutants,seconds=time.perf_counter()-began,
                scope='Fresh logical replay of every successful external trace and exact input/source/hash binding. The prior native ground admissions are reused, not reexecuted. This validator remains a separate first-order certificate checker rather than the native Wang checker.')
    (out/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='mutations'},indent=2))

if __name__=='__main__':main()
