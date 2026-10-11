"""Fresh complete logical replay and corruption checks for the Hilbert control."""
import argparse,copy,json,pathlib,re,time
from external_hilbert_run import EXPECTED,validate_theory,evaluate_countermodel,dependencies
from external_prover_inputs import sha,make_input,canonical
from external_prover_check import check_output,records,closed,grounding,replay_refutation,native_formula,entails

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='.gcts-active/external-hilbert-20261011');a=ap.parse_args();out=pathlib.Path(a.output);began=time.perf_counter()
    s=json.loads((out/'summary.json').read_text());plan=json.loads((out/'plan.json').read_text())
    if sha((out/'plan.json').read_bytes())!=s['plan_sha256']:raise ValueError('frozen plan changed')
    for p,h in s['source_sha256'].items():
        if sha(pathlib.Path(p).read_bytes())!=h:raise ValueError('measured source changed')
    snaps=[]
    for n,h in EXPECTED.items():
        b=(out/n).read_bytes()
        if sha(b)!=h:raise ValueError('geometry snapshot changed')
        snaps.append(json.loads(b))
    positive,negative=snaps;cases={positive['positive']['id']:dict(spec=positive['positive'],inventory=positive['inventory'],native_records=positive['native_records']),negative['spec']['id']:dict(spec=negative['spec'],inventory=negative['inventory'],native_records=negative['native_records'])}
    accepted=0;steps=0;model_checks=0;mutants=[];tree_mutants=0;lemma_checks=0;admissions=[]
    for entry in plan['inputs']:
        c=cases[entry['case']];validate_theory(c['spec']);family=entry['lane']!='theory-only';m=make_input(c,family);m['input_path']=entry['input_path']
        p=pathlib.Path(entry['input_path'])
        if json.loads(p.with_suffix('.mapping.json').read_text())!=m or sha(p.read_bytes())!=entry['input_sha256']:raise ValueError('input identity changed')
        if sha(p.with_suffix('.mapping.json').read_bytes())!=entry['mapping_sha256']:raise ValueError('mapping digest')
        defs={d['name']:d for d in c['inventory']['native_blocks']};native={q['id']:q for q in c['native_records']}
        for e in m['entries']:
            if e['role']!='lemma':continue
            d=defs[e['original_name']];q=native[e['native_admission']]
            if sha(canonical(q['request']))!=q['request_sha256'] or d not in q['request']['blocks'] or q['request']['theory']!=c['spec']['theory'] or q['result']['status']!='accepted':raise ValueError('ground native admission provenance')
            deps=dependencies(d,c['spec']);ch=entails([native_formula(c['spec']['theory']['axioms'][n],m) for n in deps],native_formula(e['formula'],m))
            if ch['status']!='checked':raise ValueError('lemma logical interface replay unknown')
            lemma_checks+=1;admissions.append(dict(case=entry['case'],name=e['original_name'],native_query=q['id'],native_request_sha256=q['request_sha256'],dependencies=deps))
        if entry['case']==negative['spec']['id']:
            evaluate_countermodel(c['spec'],m['entries'],negative['countermodel']);model_checks+=1
    # Explicit feature rejection protects future PA/schema exports.
    bad=copy.deepcopy(positive['positive']);bad['theory']['schemas']=['unexported']
    try:validate_theory(bad)
    except ValueError:pass
    else:raise ValueError('silently ignored schema')
    bad=copy.deepcopy(positive['positive']);bad['theory']['hidden_axioms']={}
    try:validate_theory(bad)
    except ValueError:pass
    else:raise ValueError('silently ignored theory feature')
    for o in s['observations']:
        family=o['lane']!='theory-only';stem=o['case']+'-'+('library' if family else 'theory');base=stem+'-r'+str(o['repetition']);m=json.loads((out/(stem+'.mapping.json')).read_text());text=(out/(base+'.tstp')).read_text()
        if sha(text)!=o['output_sha256'] or sha((out/(base+'.stderr')).read_bytes())!=o['stderr_sha256']:raise ValueError('returned trace changed')
        if o['certificate_status']!='checked_complete_derivation':continue
        checked=check_output(text,m,m['input_path']);accepted+=1;steps+=checked['steps'];rs=records(text)
        r=next(r for r in rs if r['source'].get('head')=='file' and r['role']!='conjecture')
        pattern=r'((?:fof|cnf)\('+re.escape(r['name'])+r',\s*'+re.escape(r['role'])+r',).*?(,\s*file\()'
        altered,n=re.subn(pattern,r'\g<1> $false\g<2>',text,count=1)
        if n!=1:raise ValueError('input mutation construction')
        last=rs[-1];line=next(ln for ln in text.splitlines() if ln.startswith('cnf('+last['name']+','));empty=text.replace(line,'cnf('+last['name']+', '+last['role']+", ($false), inference(cn,[status(thm)],[]), ['proof']).",1)
        broken=text.replace('inference(assume_negation,[status(cth)],[goal])','inference(assume_negation,[status(cth)],[])',1)
        for label,mutant in [('changed-input',altered),('empty-contradiction-parents',empty),('missing-negated-goal',broken)]:
            try:check_output(mutant,m,m['input_path'])
            except ValueError as e:mutants.append(dict(observation=base,mutation=label,status='rejected',reason=str(e)))
            else:raise ValueError('corrupt external derivation passed')
        byname={r['name']:r for r in rs}
        for ch in checked['checks']:
            if 'refutation' not in ch:continue
            cs,_=grounding([closed(byname[n]['formula']) for n in ch['parents']]+[('not',closed(byname[ch['name']]['formula']))]);bad=copy.deepcopy(ch['refutation']);bad['tree']=['euf']
            try:replay_refutation(cs,bad)
            except ValueError:tree_mutants+=1
            else:raise ValueError('unjustified equality conflict passed')
    result=dict(status='passed',successful_derivations=accepted,proof_lines=steps,independent_lemma_checks=lemma_checks,admissions=admissions,countermodel_replays=model_checks,rejected_trace_corruptions=len(mutants),rejected_local_refutation_corruptions=tree_mutants,rejected_unexported_theory_features=2,mutations=mutants,seconds=time.perf_counter()-began,
                scope='Exact statement/library/source/output binding, fresh complete logical checks and corrupted-proof rejection. Reused geometry native acceptances are bound to exact requests; native computations and GCTS graphs are not reexecuted here.')
    (out/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['admissions','mutations']},indent=2))

if __name__=='__main__':main()
