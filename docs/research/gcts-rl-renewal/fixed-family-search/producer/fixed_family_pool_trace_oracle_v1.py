"""Prospective independent whole-pool transaction/order oracle. SOURCE ONLY.

No production imports, scientific loader or CLI. A future separately reviewed
auditor must pass pinned independent point/transaction/body libraries and five
descriptors rebuilt independently from literal source data. This object does
not search: it reconstructs operations demanded by a recorded tape. Parent
exclusion is called only after that tape auditor reconstructs child exhaustion.
"""
import copy
import hashlib


class FixedPoolTransactions:
    def __init__(self,state,descriptors,group_epoch,context,authority,registry,
                 point,body,transactions):
        self.p,self.b,self.transactions=point,body,transactions
        point.need(isinstance(state,transactions.PointState),
            'independent complete raw-domain PointState required, not the earlier controlled-only State')
        self.base=transactions.TransactionState(state,group_epoch)
        self.descriptors=copy.deepcopy(sorted(descriptors,key=lambda d:(d['fixed_priority'],d['pool_index'])))
        point.need(len(self.descriptors)==5,'all exact independently reconstructed fixed proposals')
        self.context,self.authority,self.registry=context,authority,registry
        self.group_epoch=group_epoch
        self.invariant=point.digest([state.epoch,state.recipes,state.roots])
        self.hints=[dict(status='waiting',reason=None,eligible=[],decision=['unresolved',None,0,None],revision=0)
                    for _ in self.descriptors]
        self.revision,self.hint_trail=0,0
        self.sync();self.hint_trail=0

    @property
    def state(self):return self.base.state

    @property
    def censuses(self):return self.base.censuses

    @property
    def body_epoch(self):return self.group_epoch

    def _view(self,descriptor,choice,old):
        p,b,s=self.p,self.b,self.state
        if old['status']=='retired':
            return dict(status='retired',reason=old['reason'],eligible=[],decision=choice,revision=self.revision)
        reason=None;pending=[];additional={}
        if (p.digest([s.epoch,s.recipes,s.roots])!=self.invariant
                or descriptor['body_authority_epoch']!=self.group_epoch
                or descriptor['graph_binding']['model_epoch']!=s.epoch):
            reason='stale_frozen_authority'
        else:
            for value,identifier in zip(descriptor['members'],descriptor['full_member_ids']):
                key=b.key(value)
                if key in s.selected:
                    t,m=p.points(s.recipes[key[0]],key[1],key[2],s.height)
                    if p.decorate(key,t,m,s.recipes,self.context,self.authority,self.registry)['id']!=identifier:
                        reason='selected_identity_mismatch';break
                    continue
                if not s.legal(key):reason='pending_member_illegal';break
                pending.append(key)
                # Literal palette gives one unit of support at this row.
                # Shared exact members are already deduplicated in the group.
                for x,y,value in p.points(s.recipes[key[0]],key[1],key[2],s.height)[0]:
                    additional[x,y]=additional.get((x,y),0)+value
                    if s.totals[y]+additional[x,y]>1:
                        reason='pending_aggregate_overcapacity';break
                if reason:break
            if reason is None:
                for x,y,value in descriptor['aggregate_m']:
                    if (x,y) in s.marks and s.marks[x,y]!=value:
                        reason='aggregate_remote_mark_conflict';break
        eligible=([b.key_data(k) for k in pending if choice[0]=='branch' and k[1]==choice[1]]
                  if reason is None else [])
        status='retired' if reason else ('consumed' if not pending else ('ready' if eligible else 'waiting'))
        return dict(status=status,reason=reason,eligible=eligible,decision=choice,revision=self.revision)

    def full(self):
        graph=self.base.full()['graph']
        return dict(graph=graph,hint_states=copy.deepcopy(self.hints),hint_revision=self.revision,
            descriptor_ids=[d['descriptor_id'] for d in self.descriptors],root_rejected=[],authority_epoch=self.group_epoch)

    def sync(self):
        # Complete raw point census in TransactionState.full establishes the
        # decision before any hint inspection. Hints never affect degrees.
        choice=self.transactions.decision(self.base.full())
        self.hint_trail+=1;self.revision+=1
        for index,descriptor in enumerate(self.descriptors):
            old=self.hints[index];new=self._view(descriptor,choice,old)
            if self.p.canonical(old)!=self.p.canonical(new):
                self.hint_trail+=1;self.hints[index]=new
        return choice

    def checkpoint(self):
        return [self.base.graph_trail,self.hint_trail,self.revision,
            self.p.digest([d['descriptor_id'] for d in self.descriptors]),self.p.digest(self.full())]

    def saved(self):
        return (self.base.saved(),self.hint_trail,self.revision,copy.deepcopy(self.hints))

    def restore(self,saved):
        base,self.hint_trail,self.revision,self.hints=copy.deepcopy(saved)
        self.base.restore(base)
        # Deep snapshots revive parent hint state only on paired rollback;
        # a subsequent resync cannot revive a branch-retired descriptor.

    def apply(self,key):
        choice=self.transactions.decision(self.base.full())
        self.p.need(self.state.legal(key) and choice[0] in ('branch','forced') and key[1]==choice[1],
                    'complete primitive legality and global scheduler before one placement')
        if choice[0]=='forced':
            domain=list(self.state.candidates(choice[1]))
            self.p.need(domain==[key],'forced singleton before any hint preference')
        self.state.apply(key);self.base.graph_trail+=1;self.sync()

    def exclude(self,key):
        self.p.need(self.state.legal(key),'restored-parent legal key before proved child exclusion')
        self.state.excluded[key[1]].add(key);self.base.graph_trail+=1;self.sync()

    def order(self,choice):
        self.b.equal(choice,self.transactions.decision(self.base.full()),'current full graph decision')
        self.p.need(choice[0] in ('branch','forced'),'hint order only after global scheduler')
        self.sync()
        base=list(self.state.candidates(choice[1]));preferred=[];seen=set()
        if choice[0]=='branch':
            for hint in self.hints:
                if hint['status']=='ready':
                    for value in hint['eligible']:
                        key=self.b.key(value)
                        self.p.need(key in base,'ready full key belongs to complete point domain')
                        if key not in seen:seen.add(key);preferred.append(key)
        ordered=preferred+[key for key in base if key not in seen]
        self.p.need(len(ordered)==len(base) and set(ordered)==set(base),'complete fallback permutation')
        if choice[0]=='forced':self.b.equal(ordered,base,'forced order unchanged')
        projection=dict(schema='fixed-whole-family-order-trace-v1',descriptor_order=[
            dict(descriptor_id=d['descriptor_id'],fixed_priority=d['fixed_priority'],status=h['status'],reason=h['reason'],eligible=h['eligible'])
            for d,h in zip(self.descriptors,self.hints)],preferred_keys=[self.b.key_data(k) for k in preferred],
            preferred_keys_sha256=self.p.digest([self.b.key_data(k) for k in preferred]),
            advice_scope='Pending structural source-body obligations, not newly proved premises or a completed proof')
        return base,ordered,projection

    def compact(self):
        full=self.full();projection=copy.deepcopy(full)
        for domain in projection['graph']['domains']:del domain['factors']
        return dict(full_semantic_sha256=self.p.digest(full),projection=projection)


def key_stream_sha(keys,body,point):
    return hashlib.sha256(('\n'.join(point.canonical(body.key_data(k)) for k in keys)+'\n').encode()).hexdigest()
