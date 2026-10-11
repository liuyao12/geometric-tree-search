"""Independent tiny lifecycle artifact reconstruction, prospective and gated.

No producer import. Literal unit placements are enumerated by our own records
adapter; rollback here restores deep snapshots, independently of producer
delta trails. Tiny DFS establishes every excluded child's finite exhaustion.
No actual geometry model or native authority is loaded.
"""
import copy
import json
from independent_lifecycle_records_v1 import (
    literal_model, expected_descriptor, check_graph_state, need, json_equal,
    expected_body, AUTHORED_MEMBERS,
)
from lifecycle_oracle_v2 import key, integer, sha, canonical


def key_data(k):
    return [k[0],k[1],list(k[2])]


def graph_data(oracle, palette, selected, excluded):
    """Derive all values and factor counts from full raw placement enumeration."""
    selected=[key_data(k) for k in selected]
    excluded=[key_data(k) for k in excluded]
    s=oracle.state(selected,excluded); height=len(oracle.required)
    base=oracle.state(selected)
    domains=[]
    for row in range(height):
        factors=[]
        if not s['total'][0,row]:
            for i,r in enumerate(palette):
                if (1,row) in s['marks'] and s['marks'][1,row]!=r['output']:continue
                if not r['inputs']:
                    factors.append([i,0,0,False,1]);continue
                masks=[]
                for port,code in enumerate(r['inputs']):
                    allowed=[source for source in range(row)
                        if ((1,source) not in s['marks'] or s['marks'][1,source]==code)
                        and ((2+port,row) not in s['marks'] or s['marks'][2+port,row]==source-row)]
                    masks.append(sum(1<<source for source in allowed))
                a,b=masks; different=r['inputs'][0]!=r['inputs'][1]
                raw=[k for k in base['domains'].get((0,row),[]) if k[0]==i]
                if raw:factors.append([i,a,b,different,len(raw)])
        raw=base['domains'].get((0,row),[])
        removed=sorted(k for k in s['excluded'] if k in raw)
        domains.append(dict(factors=factors,base_count=len(raw),excluded_legal=[key_data(k) for k in removed],
                            count=len(s['domains'].get((0,row),[]))))
    data=dict(totals=[s['total'][0,r] for r in range(height)],
        marks=[[*p,v,s['mark_refs'][p]] for p,v in sorted(s['marks'].items())],
        order=selected,selected_generations=[[key_data(k),s['generations'][k]] for k in sorted(s['selected'])],
        roots=[oracle.roots[0,r] for r in range(height)],
        excluded=[[key_data(k) for k in sorted(s['excluded']) if k[1]==r] for r in range(height)],
        domains=domains,model_epoch=oracle.binding['model_epoch'])
    kind,point=s['decision']; row=point[1] if point is not None else None
    decision=[kind,row,len(s['domains'].get(point,[])) if point is not None else 0,
              oracle.roots[point] if point is not None else None]
    return data,s,decision


def current_hint(compiled,state,decision,revision,old=None):
    """Retirement is branch-absorbing until an explicit paired rollback."""
    if old is not None and old['status']=='retired':
        return dict(status='retired',reason=old['reason'],eligible=[],decision=decision,revision=revision)
    pending=[k for k in compiled['members'] if k not in state['selected']]
    legal={k for values in state['domains'].values() for k in values}
    reason=None
    if any(k not in legal for k in pending):reason='pending_member_illegal'
    else:
        extra={}
        for k in pending:
            p=(0,k[1]); extra[p]=extra.get(p,0)+1
            if state['total'][p]+extra[p]>1:reason='pending_aggregate_overcapacity';break
        if reason is None and any(p in state['marks'] and state['marks'][p]!=v for p,v in compiled['marks'].items()):
            reason='aggregate_remote_mark_conflict'
    eligible=[k for k in pending if decision[0]=='branch' and k[1]==decision[1]] if reason is None else []
    status='retired' if reason else ('consumed' if not pending else ('ready' if eligible else 'waiting'))
    return dict(status=status,reason=reason,eligible=[key_data(k) for k in eligible],decision=decision,revision=revision)


class SnapshotController:
    """Separate full-state implementation: no use of producer graph/trail."""
    def __init__(self, record, authorities, initial=None):
        self.oracle,self.binding,self.placements,self.palette=literal_model(record)
        self.descriptors=copy.deepcopy(record['descriptors'])
        self.authority_epoch=record['state']['authority_epoch']
        self.compiled=[expected_descriptor(d,authorities[d['body_authority_epoch']],self.oracle,self.palette,self.placements)
                       for d in self.descriptors]
        self.rejected=copy.deepcopy(record['state']['root_rejected'])
        self.selected=[]; self.excluded=set(); self.revision=0; self.hints=[]
        self.graph_trail=0; self.hint_trail=[]
        self.checkpoints={}
        if initial is None:
            _,state,d=self.graph()
            self.hints=[dict(status='waiting',reason=None,eligible=[],decision=['unresolved',None,0,None],revision=0)
                        for _ in self.compiled]
            self.resync();self.hint_trail.clear()
        else:
            self.selected=[key(k) for k in initial['graph']['order']]
            self.excluded={key(k) for values in initial['graph']['excluded'] for k in values}
            self.revision=integer(initial['hint_revision'])
            self.graph_trail=len(self.selected)+len(self.excluded)
            # Every retained resync trails one revision and all hint states,
            # because the fresh revision itself is part of each HintState.
            self.hint_trail=[('preexisting_exact_checkpoint_entry',i) for i in
                range((len(self.compiled)+1)*(self.revision-1))]
            _,state,d=self.graph()
            self.hints=[current_hint(c,state,d,self.revision) for c in self.compiled]
            need(json_equal(self.semantic(),initial),'independent exact initial state')

    def graph(self):return graph_data(self.oracle,self.palette,self.selected,self.excluded)

    def semantic(self):
        g,_,_=self.graph()
        return dict(graph=g,hint_states=copy.deepcopy(self.hints),hint_revision=self.revision,
            descriptor_ids=[d['descriptor_id'] for d in self.descriptors],root_rejected=copy.deepcopy(self.rejected),
            authority_epoch=self.authority_epoch)

    def resync(self):
        _,s,d=self.graph();self.hint_trail.append(('revision',self.revision));self.revision+=1
        for i,c in enumerate(self.compiled):
            h=current_hint(c,s,d,self.revision,self.hints[i])
            if h!=self.hints[i]:self.hint_trail.append(('state',i,copy.deepcopy(self.hints[i])));self.hints[i]=h
        return d

    def ordered(self):
        d=self.resync();_,s,_=self.graph()
        need(d[0] in ('branch','forced'),'ordering current global graph decision')
        base=s['domains'][0,d[1]]; preferred=[]
        if d[0]=='branch':
            for h in self.hints:
                if h['status']=='ready':
                    for k in map(key,h['eligible']):
                        if k not in preferred:preferred.append(k)
        result=preferred+[k for k in base if k not in preferred]
        need(len(result)==len(base) and set(result)==set(base),'complete fallback permutation')
        return result

    def checkpoint(self):
        values=[self.graph_trail,len(self.hint_trail),self.revision,
                sha([d['descriptor_id'] for d in self.descriptors]),sha(self.semantic())]
        self.checkpoints[tuple(values)]=(copy.deepcopy(self.selected),copy.deepcopy(self.excluded),
            self.revision,copy.deepcopy(self.hints),self.graph_trail,copy.deepcopy(self.hint_trail))
        return values

    def rollback(self,cp):
        need(tuple(cp) in self.checkpoints,'exact known paired checkpoint')
        self.selected,self.excluded,self.revision,self.hints,self.graph_trail,self.hint_trail=copy.deepcopy(self.checkpoints[tuple(cp)])
        need(sha(self.semantic())==cp[-1],'independent deep-snapshot rollback exact')

    def apply(self,k,scheduler=True):
        k=key(k);_,s,d=self.graph()
        need(k in {x for values in s['domains'].values() for x in values},'exact legal candidate')
        if scheduler:
            need(d[0] in ('branch','forced') and k[1]==d[1],'global scheduler authority')
            if d[0]=='forced':need(s['domains'][0,d[1]]==[k],'forced singleton')
        self.selected.append(k);self.graph_trail+=1
        self.resync()

    def exclude(self,k,resync=True):
        k=key(k);_,s,_=self.graph()
        need(k in {x for values in s['domains'].values() for x in values},'restored-parent legal exclusion')
        self.excluded.add(k);self.graph_trail+=1
        if resync:self.resync()


def check_record(record,authorities):
    c=SnapshotController(record,authorities,initial=record['state'])
    graph,state,d=c.graph()
    need(json_equal(graph,record['state']['graph']),'every value/factor/ordered exclusion/generation matches')
    need(json_equal(record['complete_domains'],[[key_data(k) for k in state['domains'].get((0,r),[]) ]
        for r in range(len(c.oracle.required))]),'complete raw candidate universe and ordering')
    # A snapshot alone cannot justify absorbing retired state; its origins are
    # separately checked by controlled transaction and complete DFS replay.
    return c


def replay_dfs(controller,max_attempts):
    """Independent complete finite DFS; each dead/exhausted child is established.

    No wall clock cutoff is synthesized here. The finite traces must fit the
    declared attempt bound and independent owned lifetime gate.
    """
    c=controller; events=[];attempts=0;backtracks=0
    def emit(kind,**data):events.append(dict(kind=kind,**data,state=c.semantic()))
    def undo(cp):c.rollback(cp);emit('paired_rollback',checkpoint=cp)
    entry=c.checkpoint()
    def visit():
        nonlocal attempts,backtracks
        frame=c.checkpoint()
        while True:
            _,_,d=c.graph();emit('global_decision',decision=d)
            if d[0]=='dead':
                emit('proved_dead_child');undo(frame);return 'exhausted_finite_marked_subtree'
            if d[0]=='complete':c.resync();return 'finite_exact_point_tiling'
            if attempts>=max_attempts:
                emit('budget_unknown_no_exclusion');undo(frame);return 'unknown_budget'
            first=c.ordered()[0]
            if d[0]=='forced':
                c.apply(first);attempts+=1;emit('primitive_step',key=key_data(first));continue
            parent=c.checkpoint();c.apply(first);attempts+=1;emit('primitive_step',key=key_data(first))
            status=visit()
            if status=='finite_exact_point_tiling':return status
            undo(parent)
            if status=='unknown_budget':undo(frame);return status
            need(status=='exhausted_finite_marked_subtree','unknown cannot authorize exclusion')
            backtracks+=1;c.exclude(first)
            emit('parent_local_exhausted_child_exclusion',key=key_data(first),child_status=status)
    status=visit()
    if status!='finite_exact_point_tiling':undo(entry)
    return dict(status=status,events=events,attempts=attempts,backtracks=backtracks)
