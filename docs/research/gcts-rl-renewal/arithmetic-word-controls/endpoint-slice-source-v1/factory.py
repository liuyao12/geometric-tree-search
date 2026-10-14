"""UNEXECUTED Source-copy fragment for a cold caller's private recipe loop.

This is not a loader, CLI, cheaper search guard, or mathematical admission.
Source-copy this exact factory into the reviewed worker's own module, using
its original guarded helper functions. The new driver must anchor the returned
FunctionType before/after every call and use it only in observer initialization.
Full runtime.check remains mandatory at fixed32-row boundaries and before any
constructed observer is exposed. ROOT owns future integration and activation.
"""


def make_recipe_allocation_guard(*, graph_module, driver_module, graph, runtime,
                                source_records, cached_source_buffers,
                                module_anchors, full_guard, phase_evidence):
    # The existing guarded caller authenticates/anchors this factory before
    # entry and after return. No module or Source file is loaded here.
    original_state = function_state
    state_code = original_state.__code__
    original_need = need
    need_code = original_need.__code__
    original_isfunction = inspect.isfunction
    isfunction_code = original_isfunction.__code__
    isfunction_anchor = original_state(original_isfunction)
    original_function_type = types.FunctionType
    # Original native lookup primitives are captured under the cold caller's
    # complete preguard; their closure identities are caller-sealed before use.
    # Entry custody must not resolve a newly shadowed globals/type/vars/tuple.
    original_globals, original_vars = globals, vars
    original_type, original_tuple = type, tuple
    original_dict, original_dict_get = dict, dict.get
    original_code_type = types.CodeType
    original_ValueError = ValueError
    original_module_type = types.ModuleType
    original_clock = time.perf_counter
    original_usage = resource.getrusage
    original_self = resource.RUSAGE_SELF
    original_getframe = sys._getframe
    original_modules = sys.modules
    module_bindings = tuple((name, globals()[name]) for name in
                            ('json', 'sys', 'time', 'resource', 'types', 'inspect'))
    helpers = tuple((name, globals()[name], globals()[name].__code__,
                     original_state(globals()[name])) for name in
        ('need', 'function_state', 'canonical', 'value_state', 'executable_state', 'unchanged_executable',
         'exact_function_anchors', 'check_exact_functions', 'endpoint_anchor', 'check_endpoint'))
    original_need(type(full_guard) is original_function_type
                  and full_guard is runtime.guard and full_guard.__globals__ is globals()
                  and full_guard.__module__ == __name__
                  and full_guard.__code__.co_filename == make_recipe_allocation_guard.__code__.co_filename,
                  'allocation endpoint slice belongs to the original cold caller, not a supplied callback')
    full_anchor = original_state(full_guard)
    # Mutable counters are diagnostic output only, not guard or proof authority.
    original_need(type(phase_evidence) is dict and phase_evidence == {
        'schema': 'Q-private-allocation-phase-evidence-v1',
        'factory_started': False, 'factory_returned': False,
        'factory_capture_seconds': None, 'boundary_entries': 0,
        'boundary_returns': 0, 'last_started_recipe_index': None,
        'last_returned_boundary_recipe_index': None,
        'completed_recipe_comparisons_observed': 0,
        'completed_boundary_inclusive_seconds': 0.0, 'constructor_returned': False,
        'constructor_recipe_interfaces': None}, 'fresh diagnostic counter wire only')
    phase_started = original_clock()
    phase_evidence['factory_started'] = True
    original_need(graph_module is module_anchors['point_graph']
                  and driver_module is module_anchors['driver']
                  and type(graph) is graph_module.PointGraph and type(runtime) is driver_module.Runtime,
                  'exact originally loaded module and initialized object endpoints')
    original_need(set(module_anchors) == set(EXECUTED_ROLES) - {'worker'},
                  'exact original executed role ledger, no additional allocation executable')
    buffers = []
    for role, module in module_anchors.items():
        record = source_records[role]
        raw = cached_source_buffers[role]
        original_need(type(raw) is bytes and len(raw) == record['bytes']
                      and hashlib.sha256(raw).hexdigest() == record['sha256']
                      and module.__file__ == record['path'] and original_modules.get(module.__name__) is module,
                      'once authenticated original cached bytes and module identity')
        buffers.append((role, module, module.__name__, module.__file__, raw,
                        record['path'], record['sha256'], record['bytes']))
    buffers = tuple(buffers)
    original_need(graph_module.json is json and driver_module.json is json
                  and runtime.clock is original_clock and runtime.usage is original_usage,
                  'exact delegated JSON modules and native clock/resource endpoints')
    recipes = graph.recipes
    recipe_class = graph_module.Recipe
    original_need(type(recipes) is tuple and type(recipe_class) is type,
                  'entire original immutable recipe container')
    fields = ('index', 'identifier', 'witness_text', 'premise_texts', 'output', 'inputs')
    recipe_records = []
    for index, recipe in enumerate(recipes):
        if (time.perf_counter is not original_clock or resource.getrusage is not original_usage
                or original_clock() >= runtime.deadline
                or original_clock() - runtime.began >= 55
                or original_usage(original_self).ru_maxrss >= 524288000):
            raise TimeoutError('whole allocation-slice capture exceeds original limits')
        original_need(type(recipe) is recipe_class and set(vars(recipe)) == set(fields)
                      and recipe.index == index, 'complete original Recipe records, never a shortlist')
        recipe_records.append((recipe, tuple((name, getattr(recipe, name), type(getattr(recipe, name)))
                                             for name in fields)))
    recipe_records = tuple(recipe_records)
    runtime_fields = tuple((name, getattr(runtime, name)) for name in driver_module.Runtime.__slots__)
    original_need(runtime.deadline == runtime.began + 20, 'same original absolute20, no new window')
    original_began, original_deadline = runtime.began, runtime.deadline
    observer_class = driver_module.FirstSelectedProofObserver
    initializer = observer_class.__init__
    initializer_anchor = original_state(initializer)
    driver_functions = tuple((name, getattr(driver_module, name),
                              original_state(getattr(driver_module, name)))
                             for name in ('canonical', 'need', 'function_state', 'invoke'))
    # This is an explicit reachable endpoint census for the actual strict
    # canonical dumps and str-only Recipe getters. It does not traverse every
    # unused JSON/module constant and serialize values at every local boundary.
    # The unchanged full guard still snapshots those namespaces at32/end.
    json_modules = (json, json.decoder, json.scanner, json.encoder)
    json_aliases = ((json, 'decoder', json.decoder), (json, 'scanner', json.scanner),
                   (json, 'encoder', json.encoder),
                   (json.decoder, 'scanner', json.scanner))
    json_function_names = ((json, ('dumps', 'loads', 'detect_encoding')),
        (json.decoder, ('JSONObject', 'JSONArray', 'py_scanstring', '_decode_uXXXX')),
        (json.encoder, ('py_encode_basestring', 'py_encode_basestring_ascii', '_make_iterencode')),
        (json.scanner, ('py_make_scanner',)))
    json_functions = tuple((owner, name, vars(owner)[name],
                            original_state(vars(owner)[name]))
                           for owner, names in json_function_names for name in names)
    json_binding_names = ((json, ('JSONEncoder', 'JSONDecoder', 'JSONDecodeError')),
        (json.decoder, ('JSONDecoder', 'JSONDecodeError', 'scanstring', 'c_scanstring')),
        (json.encoder, ('JSONEncoder', 'c_make_encoder', 'encode_basestring',
                        'encode_basestring_ascii', 'c_encode_basestring', 'c_encode_basestring_ascii')),
        (json.scanner, ('make_scanner', 'c_make_scanner')))
    json_bindings = tuple((owner, name, vars(owner)[name])
                         for owner, names in json_binding_names for name in names)
    original_need(json.encoder.c_make_encoder is not None
                  and json.encoder.encode_basestring is json.encoder.c_encode_basestring
                  and json.encoder.encode_basestring_ascii is json.encoder.c_encode_basestring_ascii
                  and json.decoder.scanstring is json.decoder.c_scanstring,
                  'this declared slice requires original native JSON hooks, no fallback exemption')
    # Small actually reachable constant tables are sealed by literal identity
    # and ordered entries, without delegated JSON canonicalization of them.
    json_constants = []
    for owner, names in ((json.decoder, ('_CONSTANTS', 'BACKSLASH', 'WHITESPACE_STR')),
                         (json.encoder, ('ESCAPE_DCT', 'INFINITY'))):
        for name in names:
            value = vars(owner)[name]
            entries = tuple((key, child, type(child)) for key, child in value.items()) if type(value) is dict else None
            json_constants.append((owner, name, value, type(value), entries))
    json_constants = tuple(json_constants)
    decoder = json._default_decoder
    original_need(type(decoder) is json.JSONDecoder, 'actual default decoder, never a replacement')
    decoder_anchor = endpoint_anchor(decoder)
    decoder_names = tuple(vars(decoder))
    decoder_fields = tuple((name, value, type(value)) for name, value in vars(decoder).items())
    decoder_functions = tuple((value, original_state(value)) for _, value, _ in decoder_fields
                              if original_isfunction(value))
    scanner = decoder.scan_once
    scanner_type = type(scanner)
    scanner_mro = scanner_type.__mro__
    original_need(scanner_type is json.scanner.c_make_scanner and scanner_type.__module__ == '_json',
                  'original native scanner only')
    scanner_call = next((vars(parent)['__call__'] for parent in scanner_mro
                         if '__call__' in vars(parent)), None)
    scanner_effective = scanner.__call__
    # Complete class namespace/MRO identities remain immediate. Function
    # bodies/defaults/cells are immediate for actual property/attribute dispatch
    # and JSON construction/encode/decode; unused Graph method bodies remain
    # under the original full guard at32/end, not a broad object exemption.
    class_records = []
    class_functions = []
    seen_classes = set()
    immediate_classes = (recipe_class, type(runtime), json.JSONDecoder,
                         json.JSONEncoder, json.JSONDecodeError)
    for root in (recipe_class, type(graph), type(runtime), json.JSONDecoder,
                 json.JSONEncoder, json.JSONDecodeError, scanner_type,
                 json.encoder.c_make_encoder):
        for parent in root.__mro__:
            if parent is object or parent in seen_classes:
                continue
            seen_classes.add(parent)
            records = tuple(vars(parent).items())
            class_records.append((parent, type(parent), parent.__mro__, records))
            for name, value in records:
                if isinstance(value, property):
                    for accessor in ('fget', 'fset', 'fdel'):
                        function = getattr(value, accessor)
                        if function is not None:
                            class_functions.append((value, accessor, function, original_state(function)))
                else:
                    function = value.__func__ if isinstance(value, (staticmethod, classmethod)) else value
                    if original_isfunction(function) and (parent in immediate_classes
                            or name in ('__getattribute__', '__getattr__')):
                        class_functions.append((parent, name, function, original_state(function)))
    class_records, class_functions = tuple(class_records), tuple(class_functions)
    # Name resolution is part of the actual delegated executable endpoint.
    # co_names conservatively includes attributes as well as global reads; all
    # nested code constants are included (e.g. iterencode's floatstr). Extra
    # absence checks are custody checks, never mathematical grammar filters.
    resolution_functions = [make_recipe_allocation_guard, full_guard, initializer,
                            original_isfunction]
    resolution_functions.extend(function for _, function, _, _ in helpers)
    resolution_functions.extend(function for _, function, _ in driver_functions)
    resolution_functions.extend(function for _, _, function, _ in json_functions)
    resolution_functions.extend(function for _, _, function, _ in class_functions)
    resolution_functions.extend(function for function, _ in decoder_functions)
    resolution_scopes = {}
    resolution_signatures = []
    for function in resolution_functions:
        namespace = function.__globals__
        original_need(original_type(namespace) is original_dict,
                      'actual Python callable global dictionary, no proxy')
        resolution_signatures.append((function, namespace, original_state(function)))
        scope = resolution_scopes.setdefault(id(namespace), [namespace, set()])
        original_need(scope[0] is namespace, 'unique actual global dictionary identities')
        pending = [function.__code__]
        while pending:
            code = pending.pop()
            scope[1].update(code.co_names)
            pending.extend(child for child in code.co_consts
                           if original_type(child) is original_code_type)
    resolution_records = []
    namespace_records = []
    for namespace, names in resolution_scopes.values():
        builtin_holder = namespace.get('__builtins__')
        builtin_kind = original_type(builtin_holder)
        original_need(builtin_kind in (original_dict, original_module_type),
                      'original standard builtin dictionary/module only')
        builtin_namespace = builtin_holder if builtin_kind is original_dict else original_vars(builtin_holder)
        original_need(original_type(builtin_namespace) is original_dict,
                      'actual native builtin resolution dictionary')
        namespace_records.append((namespace, original_tuple(namespace), builtin_holder,
                                  builtin_kind, builtin_namespace))
        for name in sorted(names):
            global_present = name in namespace
            global_value = original_dict_get(namespace, name)
            builtin_present = name in builtin_namespace
            builtin_value = original_dict_get(builtin_namespace, name)
            resolution_records.append((namespace, name, global_present, global_value,
                                       builtin_namespace, builtin_present, builtin_value))
    resolution_records, namespace_records = original_tuple(resolution_records), original_tuple(namespace_records)
    # Even unused added JSON globals can change future builtin fallback. Name
    # tuples are cheap identity/presence custody, not recursive value snapshots.
    relevant_namespace_records = original_tuple((module, original_vars(module),
                                                original_tuple(original_vars(module)))
        for module in json_modules + (graph_module, driver_module))
    progress = {'index': -1, 'busy': False}

    def allocation_guard(*, index, recipe):
        # These direct rejections precede all potentially mutable validators.
        # The driver independently seals this exact function/defaults/cells at
        # every caller; this function is not its own source of entry authority.
        # Direct native-only resolution gates precede ANY mutable helper,
        # builtin-name lookup or module property used by the existing body.
        if original_type(original_globals()) is not original_dict:
            raise original_ValueError('original caller global dictionary type changed')
        for namespace, keys, holder, holder_kind, builtin_namespace in namespace_records:
            if original_type(namespace) is not original_dict or original_tuple(namespace) != keys:
                raise original_ValueError('reachable callable namespace added/lost names')
            if (original_dict_get(namespace, '__builtins__') is not holder
                    or original_type(holder) is not holder_kind
                    or (holder if holder_kind is original_dict else original_vars(holder)) is not builtin_namespace):
                raise original_ValueError('actual reachable builtin mapping identity/type changed')
        for module, namespace, keys in relevant_namespace_records:
            if (original_type(module) is not original_module_type
                    or original_vars(module) is not namespace or original_tuple(namespace) != keys):
                raise original_ValueError('actual relevant module namespace added/lost names')
        for namespace, name, global_present, global_value, builtin_namespace, builtin_present, builtin_value in resolution_records:
            if ((name in namespace) is not global_present
                    or original_dict_get(namespace, name) is not global_value
                    or (name in builtin_namespace) is not builtin_present
                    or original_dict_get(builtin_namespace, name) is not builtin_value):
                raise original_ValueError('actual reachable global/builtin presence or identity changed')
        if time.perf_counter is not original_clock:
            raise ValueError('original allocation diagnostic clock changed')
        boundary_started = original_clock()
        phase_evidence['boundary_entries'] += 1
        phase_evidence['last_started_recipe_index'] = index
        if any(globals().get(name) is not module for name, module in module_bindings):
            raise ValueError('original actual allocation module binding changed')
        if function_state is not original_state or original_state.__code__ is not state_code:
            raise ValueError('original allocation function-state validator changed')
        if need is not original_need or original_need.__code__ is not need_code:
            raise ValueError('original allocation rejector changed')
        if inspect.isfunction is not original_isfunction or original_isfunction.__code__ is not isfunction_code:
            raise ValueError('original function-type predicate changed')
        if types.FunctionType is not original_function_type or types.ModuleType is not original_module_type:
            raise ValueError('original Python function/module type changed')
        if any(type(module) is not original_module_type for _, module in module_bindings):
            raise ValueError('original allocation module acquired a custom attribute endpoint')
        if any(type(module) is not original_module_type for _, module, _, _, _, _, _, _ in buffers):
            raise ValueError('original project module acquired a custom attribute endpoint')
        if time.perf_counter is not original_clock or resource.getrusage is not original_usage or resource.RUSAGE_SELF != original_self:
            raise ValueError('original allocation clock/resource binding changed')
        if sys._getframe is not original_getframe or sys.modules is not original_modules:
            raise ValueError('original frame/cache endpoints changed')
        if any(globals().get(name) is not fn or fn.__code__ is not code for name, fn, code, _ in helpers):
            raise ValueError('original allocation helper identity/code changed')
        if original_state(original_isfunction) != isfunction_anchor:
            raise ValueError('original function predicate defaults/cells changed')
        if any(original_state(fn) != anchor for _, fn, _, anchor in helpers):
            raise ValueError('original allocation helper defaults/cells changed')
        if original_state(full_guard) != full_anchor:
            raise ValueError('original complete cold guard authority changed')
        for function, namespace, signature in resolution_signatures:
            if function.__globals__ is not namespace or original_state(function) != signature:
                raise ValueError('original reachable function globals/code/default/cells changed')
        # Original relevant class/dispatch authority precedes field reads.
        # No broad executable_state/value_state/JSON encoding is delegated here.
        for owner, kind, mro, records in class_records:
            if type(owner) is not kind or owner.__mro__ != mro or any(a is not b for a, b in zip(owner.__mro__, mro)):
                raise ValueError('actual allocation class type/MRO changed')
            actual = vars(owner)
            if tuple(actual) != tuple(name for name, _ in records) or any(actual[name] is not value for name, value in records):
                raise ValueError('actual allocation class namespace/descriptor identity changed')
        for owner, name, function, anchor in class_functions:
            actual = getattr(owner, name) if isinstance(owner, property) else vars(owner)[name]
            if isinstance(actual, (staticmethod, classmethod)):
                actual = actual.__func__
            if actual is not function or original_state(function) != anchor:
                raise ValueError('actual allocation accessor/constructor/JSON method code/default/cells changed')
        if any(type(module) is not original_module_type for module in json_modules):
            raise ValueError('actual JSON module gained custom attribute authority')
        if any(vars(owner).get(name) is not value for owner, name, value in json_aliases + json_bindings):
            raise ValueError('actual JSON class/module/native hook binding changed')
        for owner, name, function, anchor in json_functions:
            if vars(owner).get(name) is not function or original_state(function) != anchor:
                raise ValueError('actual JSON Python function code/default/cells changed')
        for owner, name, value, kind, entries in json_constants:
            if vars(owner).get(name) is not value or type(value) is not kind:
                raise ValueError('actual JSON constant binding changed')
            if entries is not None and (tuple(value) != tuple(key for key, _, _ in entries)
                    or any(value[key] is not child or type(child) is not child_type for key, child, child_type in entries)):
                raise ValueError('actual JSON constant table entries changed')
        if runtime.guard is not full_guard:
            raise ValueError('original Runtime guard field changed')
        if (graph_module.Recipe is not recipe_class or graph_module.PointGraph is not type(graph)
                or driver_module.Runtime is not type(runtime)
                or driver_module.FirstSelectedProofObserver is not observer_class
                or observer_class.__init__ is not initializer):
            raise ValueError('original allocation class/initializer binding changed')
        if original_state(initializer) != initializer_anchor:
            raise ValueError('original observer initialization code/default/cells changed')
        if type(index) is not int or not 0 <= index < len(recipe_records):
            raise ValueError('exact complete recipe index required')
        if recipe is not recipe_records[index][0] or graph.recipes is not recipes or type(recipe) is not recipe_class:
            raise ValueError('allocation recipe must be the original indexed graph occurrence')
        if progress['busy'] or index not in (progress['index'], progress['index'] + 1):
            raise ValueError('recursive, skipped or reversed allocation row')
        # Invocation is confined to the real private constructor frame. It
        # cannot be reused as a cheap proof/search/point/checker guard later.
        frame = original_getframe(1)
        active = None
        try:
            for _ in range(4):
                if frame is None:
                    break
                if frame.f_code is initializer_anchor[1]:
                    active = frame
                    break
                frame = frame.f_back
            if (active is None or active.f_locals.get('graph') is not graph
                    or active.f_locals.get('runtime') is not runtime
                    or active.f_locals.get('allocation_guard') is not allocation_guard):
                raise ValueError('localized endpoint guard is initializer-only')
            primitive_records = active.f_locals.get('primitives')
            if type(primitive_records) is not list or len(primitive_records) != index:
                raise ValueError('diagnostics require actual completed comparison-prefix length')
            # Each record appended only after the original complete comparisons.
            # This is observation of that fact, not accepted prefix or fit.
            phase_evidence['completed_recipe_comparisons_observed'] = len(primitive_records)
        finally:
            del frame, active
        if any(getattr(runtime, name) is not value for name, value in runtime_fields):
            raise ValueError('original Runtime fixed fields changed')
        if original_clock() >= original_deadline or original_clock() - original_began >= 55 or original_usage(original_self).ru_maxrss >= 524288000:
            raise TimeoutError('same allocation20/worker55/500 deadline or memory exhausted')
        progress['busy'] = True
        try:
            for role, module, name, file, raw, path, sha, size in buffers:
                record = source_records[role]
                if (module_anchors[role] is not module or original_modules.get(name) is not module
                        or module.__name__ != name or module.__file__ != file
                        or cached_source_buffers[role] is not raw
                        or (record['path'], record['sha256'], record['bytes']) != (path, sha, size)):
                    raise ValueError('original cached raw Source/module ledger replaced')
            if graph_module.json is not json or driver_module.json is not json:
                raise ValueError('actual delegated JSON module changed')
            if any(getattr(driver_module, name) is not fn or original_state(fn) != anchor
                   for name, fn, anchor in driver_functions):
                raise ValueError('actual canonical/predicate/delegation endpoint changed')
            if set(vars(recipe)) != set(fields):
                raise ValueError('original Recipe namespace gained a shadow')
            for name, value, kind in recipe_records[index][1]:
                if getattr(recipe, name) is not value or type(value) is not kind:
                    raise ValueError('original indexed Recipe wire/port field replaced')
            if json._default_decoder is not decoder or type(decoder) is not json.JSONDecoder or tuple(vars(decoder)) != decoder_names:
                raise ValueError('actual default decoder identity/type/namespace changed')
            if any(getattr(decoder, name) is not value or type(value) is not kind for name, value, kind in decoder_fields):
                raise ValueError('actual default decoder hook/scanner fields changed')
            if any(original_state(fn) != anchor for fn, anchor in decoder_functions):
                raise ValueError('actual decoder Python hook code/defaults/cells changed')
            check_endpoint(decoder, decoder_anchor)
            if decoder.scan_once is not scanner or type(scanner) is not scanner_type or scanner_type.__mro__ != scanner_mro:
                raise ValueError('actual native scanner identity/type/MRO changed')
            if next((vars(parent)['__call__'] for parent in scanner_mro if '__call__' in vars(parent)), None) is not scanner_call:
                raise ValueError('actual native scanner callable descriptor changed')
            effective = scanner.__call__
            if type(effective) is not type(scanner_effective) or getattr(effective, '__self__', None) is not scanner:
                raise ValueError('actual native scanner effective receiver changed')
            # Repeat exact originally captured resolution custody after checks;
            # no changed binding is accepted by re-capture or a helper shim.
            # Direct native-only resolution gates precede ANY mutable helper,
            # builtin-name lookup or module property used by the existing body.
            if original_type(original_globals()) is not original_dict:
                raise original_ValueError('original caller global dictionary type changed')
            for namespace, keys, holder, holder_kind, builtin_namespace in namespace_records:
                if original_type(namespace) is not original_dict or original_tuple(namespace) != keys:
                    raise original_ValueError('reachable callable namespace added/lost names')
                if (original_dict_get(namespace, '__builtins__') is not holder
                        or original_type(holder) is not holder_kind
                        or (holder if holder_kind is original_dict else original_vars(holder)) is not builtin_namespace):
                    raise original_ValueError('actual reachable builtin mapping identity/type changed')
            for module, namespace, keys in relevant_namespace_records:
                if (original_type(module) is not original_module_type
                        or original_vars(module) is not namespace or original_tuple(namespace) != keys):
                    raise original_ValueError('actual relevant module namespace added/lost names')
            for namespace, name, global_present, global_value, builtin_namespace, builtin_present, builtin_value in resolution_records:
                if ((name in namespace) is not global_present
                        or original_dict_get(namespace, name) is not global_value
                        or (name in builtin_namespace) is not builtin_present
                        or original_dict_get(builtin_namespace, name) is not builtin_value):
                    raise original_ValueError('actual reachable global/builtin presence or identity changed')
            # Direct post-delegation helper/callback/clock checks precede trust
            # in any completed allocation boundary. No authority is re-sealed.
            if any(globals().get(name) is not module for name, module in module_bindings):
                raise ValueError('original allocation module changed during checks')
            if function_state is not original_state or original_state.__code__ is not state_code or need is not original_need or original_need.__code__ is not need_code:
                raise ValueError('original allocation predicates changed during delegated validators')
            if any(globals().get(name) is not fn or fn.__code__ is not code for name, fn, code, _ in helpers):
                raise ValueError('original allocation helper changed during checks')
            if any(original_state(fn) != anchor for _, fn, _, anchor in helpers) or original_state(full_guard) != full_anchor:
                raise ValueError('original allocation captured authority changed during checks')
            if time.perf_counter is not original_clock or resource.getrusage is not original_usage or resource.RUSAGE_SELF != original_self:
                raise ValueError('original allocation clock changed during checks')
            if original_clock() >= original_deadline or original_clock() - original_began >= 55 or original_usage(original_self).ru_maxrss >= 524288000:
                raise TimeoutError('allocation boundary completed after unchanged limits')
            progress['index'] = index
        finally:
            progress['busy'] = False
        # Counter metadata itself is charged. No failed boundary is counted as
        # a successful return; incomplete-boundary costs remain outside this
        # sum and the whole caller/owner clocks remain authoritative.
        if time.perf_counter is not original_clock or resource.getrusage is not original_usage:
            raise ValueError('original diagnostic completion clocks changed')
        phase_evidence['completed_boundary_inclusive_seconds'] += original_clock() - boundary_started
        phase_evidence['boundary_returns'] += 1
        phase_evidence['last_returned_boundary_recipe_index'] = index
        if original_clock() >= original_deadline or original_clock() - original_began >= 55 or original_usage(original_self).ru_maxrss >= 524288000:
            phase_evidence['boundary_returns'] -= 1
            raise TimeoutError('allocation metadata completed after unchanged limits')

    # Full guarded caller runs immediately after return and alone marks the
    # factory_returned latch. Diagnostic data never authorizes construction.
    if time.perf_counter is not original_clock or resource.getrusage is not original_usage:
        raise ValueError('original factory diagnostic clocks changed')
    phase_evidence['factory_capture_seconds'] = original_clock() - phase_started
    if original_clock() >= original_deadline or original_clock() - original_began >= 55 or original_usage(original_self).ru_maxrss >= 524288000:
        raise TimeoutError('allocation-slice capture metadata exceeds unchanged limits')
    return allocation_guard
