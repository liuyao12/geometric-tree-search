    engine_milestone_records=[None,None,None,None]
    milestone_stages=('FIRST_ROOT_FAMILY_PLAN_READY','FIRST_ROOT_FAMILY_EVENT_READY',
        'FIRST_ROOT_PRIMITIVE_PLACED','FIRST_CHILD_DECISION_READY')
    milestone_phases=('M1_PLAN_READY','M2_EVENT_READY','M3_PLACE_RETURN','M4_CHILD_DECISION')
    def capture_engine_milestone(stage,record):
        # Native20 metadata only; retain owned COW references without traversal.
        # The late bounded journal is raw evidence, never scientific admission.
        if (tick is not phase_tick or phase_tick.__code__ is not phase_tick_code
                or phase_tick.__defaults__ is not phase_tick_defaults
                or phase_tick.__kwdefaults__ is not phase_tick_kwdefaults):
            raise RuntimeError('original milestone native endpoint changed')
        phase_tick()
        if type(stage)is not str or stage not in milestone_stages or type(record)is not dict:
            return
        ordinal=milestone_stages.index(stage)
        if (engine_milestone_records[ordinal]is not None
                or any(engine_milestone_records[i]is None for i in range(ordinal))
                or record.get('schema')!='unit-row-first-family-engine-milestone-v1'
                or record.get('stage')!=stage or record.get('diagnostic_only')is not True
                or record.get('scientific_acceptance')is not False):
            return
        phase(milestone_phases[ordinal])
        native_ns=phase_tick()
        engine_milestone_records[ordinal]={'ordinal':ordinal+1,'stage':stage,
            'native_ns':native_ns,'record':record}
