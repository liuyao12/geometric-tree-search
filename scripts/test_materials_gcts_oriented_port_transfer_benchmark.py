#!/usr/bin/env python3

from materials_gcts_irregular_port_atlas import (
    compile_frozen_target_atlas, compile_irregular_port_program,
    enumerate_frozen_port_occurrences)
from materials_gcts_generic import benchmark_systems


def test_frozen_oriented_ports_transfer_without_refitting_on_two_copies():
    training = next(item for item in benchmark_systems()
                    if item.name == "NaCl-rocksalt")
    program = compile_irregular_port_program(
        training.species, training.positions)
    # A proper rigid transform changes every global coordinate/frame but none
    # of the frozen metric types or relative ports.
    target_positions = tuple((-point[1] + 4.3, point[0] - 2.1,
                              point[2] + .8)
                             for point in training.positions)
    frozen = enumerate_frozen_port_occurrences(
        program, training.species, target_positions,
        maximum_per_support_type=16)
    target = compile_frozen_target_atlas(program, frozen)
    train_keys = {(port.parent_type, port.child_type,
                   port.symmetry_orbit_key) for port in program.atlas.ports}
    assert program.atlas.ports
    assert target.ports
    assert any((port.parent_type, port.child_type,
                port.symmetry_orbit_key) in train_keys
               for port in target.ports)
    assert frozen.pose_fit_failures == 0


if __name__ == "__main__":
    test_frozen_oriented_ports_transfer_without_refitting_on_two_copies()
    print("frozen oriented-port transfer: passed")
