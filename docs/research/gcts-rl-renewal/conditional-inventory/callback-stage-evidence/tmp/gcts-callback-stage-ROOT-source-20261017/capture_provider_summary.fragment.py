    provider_return_slots=[None,None]
    diagnostic_capture={'legacy':latest_observations,'provider_returns':provider_return_slots}
    summary_counters=('planned_assignments','attempted_assignments','binding_attempts',
        'ground_environment_proposals','distinct_environment_attempts','full_expansions',
        'checked_expansions','preflight_checks','native_member_exclusions','native_adaptations',
        'checked_instances','duplicate_instances','offered_instances','head_gate_calls',
        'head_gate_receipts_returned','head_gate_conflicting_plans','head_gate_no_known_conflict',
        'head_gate_unknown','head_gate_absent_head_passes','head_gate_downstream_assignments')
    def capture_provider_summary(ordinal,value):
        # Original20 metadata only. Never traverse/copy/hash or mutate the report.
        # An absent slot never blocks the existing scientific callback.
        if (tick is not phase_tick or phase_tick.__code__ is not phase_tick_code
                or phase_tick.__defaults__ is not phase_tick_defaults
                or phase_tick.__kwdefaults__ is not phase_tick_kwdefaults):
            raise RuntimeError('original summary native endpoint changed')
        native_ns=phase_tick()
        if type(ordinal)is not int or not 1<=ordinal<=2 or type(value)is not dict:
            return
        batch=value.get('batch');report=value.get('report')
        if type(batch)is not dict or type(report)is not dict:
            return
        status=batch.get('status');instances=batch.get('instances')
        reason=report.get('reason');work=report.get('work');accounting=report.get('accounting')
        if (type(status)is not str or len(status)>64 or type(instances)is not list
                or len(instances)>1 or type(reason)is not str or len(reason)>256
                or type(work)is not dict or type(accounting)is not dict
                or len(accounting)!=len(summary_counters)):
            return
        steps=work.get('steps')
        if type(steps)is not int or not 0<=steps<=1000000:
            return
        for key in summary_counters:
            count=accounting.get(key)
            if type(count)is not int or not 0<=count<=1000000:
                return
        summary={'ordinal':ordinal,'native_ns':native_ns,'batch_status':status,
            'instance_count':len(instances),'provider_reason':reason,'provider_steps':steps,
            'accounting':{key:accounting[key]for key in summary_counters}}
        if (tick is not phase_tick or phase_tick.__code__ is not phase_tick_code
                or phase_tick.__defaults__ is not phase_tick_defaults
                or phase_tick.__kwdefaults__ is not phase_tick_kwdefaults):
            raise RuntimeError('original summary native endpoint changed')
        phase_tick()
        provider_return_slots[ordinal-1]=summary
