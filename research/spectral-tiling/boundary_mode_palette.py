#!/usr/bin/env python3
"""An exact boundary-trace encoding and a sampled atlas of its eleven fields.

The aperiodicity theorem is Jeandel--Rao's, not a finite-patch inference.
The accompanying Notes give the analytic Fourier and boundary-form proofs.
This script records exact trace/flux bookkeeping and renders formulas; it does
not solve a numerical eigenproblem or implement a tiling/search engine.
"""
from pathlib import Path
from fractions import Fraction
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parent

# Jeandel--Rao, arXiv:1506.06492v4, Figure 4, left-to-right order.
# The SVG's labels are W,E,N,S; the tuples here are explicitly W,E,S,N.
COLORS = [
    (0, 0, 1, 0), (0, 3, 2, 1), (1, 0, 2, 2), (1, 1, 0, 2),
    (1, 3, 2, 3), (3, 0, 1, 1), (3, 1, 1, 1), (3, 1, 2, 2),
    (3, 3, 3, 1), (2, 2, 1, 0), (2, 2, 0, 2),
]
SIDES = ('west', 'east', 'south', 'north')


def field(a, x, y):
    """Static superposition of ordinary homogeneous Neumann square modes."""
    w, e, s, n = a
    ax, ay = (1+math.cos(math.pi*x))/2, (1+math.cos(math.pi*y))/2
    bx, by = (1-math.cos(2*math.pi*x))/2, (1-math.cos(2*math.pi*y))/2
    return (w*ax+e*(1-ax))*by+(s*ay+n*(1-ay))*bx


def helmholtz_field(a, x, y):
    w, e, s, n = a
    return ((1-x)*w+x*e)*math.sin(math.pi*y)+((1-y)*s+y*n)*math.sin(math.pi*x)


def cosine_coefficients(a):
    w, e, s, n = a
    return [Fraction(w+e+s+n, 4), Fraction(w-e, 4), Fraction(s-n, 4),
            -Fraction(w+e, 4), -Fraction(s+n, 4), Fraction(e-w, 4), Fraction(n-s, 4)]


MODES = [(0, 0), (1, 0), (0, 1), (0, 2), (2, 0), (1, 2), (2, 1)]


def projected_flux_matrix():
    # Exact moments: <sin,sin>=1/2, pi*<1-t,sin>=pi*<t,sin>=1.
    norm_squared = Fraction(1, 2)
    cross_moment = Fraction(1)
    rows = []
    for i in range(4):
        paired = i ^ 1
        row = [Fraction(0)]*4
        row[i], row[paired] = Fraction(1), Fraction(-1)
        for j in range(4):
            if j not in (i, paired):
                row[j] = -cross_moment/norm_squared
        rows.append([int(x) for x in row])
    assert rows == [[1, -1, -2, -2], [-1, 1, -2, -2],
                    [-2, -2, 1, -1], [-2, -2, -1, 1]]
    assert all(rows[i][j] == rows[j][i] for i in range(4) for j in range(4))
    return rows


def render_atlas(amplitudes):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize

    t = np.linspace(0, 1, 181)
    x, y = np.meshgrid(t, t)
    ax, ay = (1+np.cos(np.pi*x))/2, (1+np.cos(np.pi*y))/2
    bx, by = (1-np.cos(2*np.pi*x))/2, (1-np.cos(2*np.pi*y))/2
    fields = [(w*ax+e*(1-ax))*by+(s*ay+n*(1-ay))*bx
              for w, e, s, n in amplitudes]
    maximum = max(float(z.max()) for z in fields)
    norm = Normalize(vmin=0, vmax=maximum)
    fig, axes = plt.subplots(3, 4, figsize=(10.6, 8.4))
    fig.subplots_adjust(left=.06, right=.88, bottom=.03, top=.86, hspace=.50, wspace=.42)
    for index, (ax, a, z) in enumerate(zip(axes.flat, amplitudes, fields), 1):
        image = ax.imshow(z, origin='lower', extent=(0, 1, 0, 1), cmap='viridis', norm=norm,
                          interpolation='bilinear')
        w, e, s, n = a
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(r'$v_{%d}$' % index, fontsize=14, pad=31)
        for px, py, value in [(-.10, .5, w), (1.10, .5, e), (.5, -.10, s), (.5, 1.065, n)]:
            ax.text(px, py, r'$%d$' % value, transform=ax.transAxes, ha='center', va='center', fontsize=12)
    axes.flat[-1].axis('off')
    axes.flat[-1].text(.5, .5, 'Edge labels give\nfixed amplitudes.\nShared color scale.',
                     ha='center', va='center', transform=axes.flat[-1].transAxes, fontsize=11)
    color_ax = fig.add_axes([.92, .18, .018, .56])
    colorbar = fig.colorbar(image, cax=color_ax)
    colorbar.set_label(r'$v(x,y)$', fontsize=13)
    fig.suptitle('Eleven allowed superpositions of Neumann modes', fontsize=17, y=.976)
    target = ROOT/'boundary-mode-palette.png'
    fig.savefig(target, dpi=160, facecolor='white')
    plt.close(fig)
    return {'file': target.name, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
            'sample_grid_per_field': [181, 181], 'shared_range': [0, maximum],
            'meaning': 'Sampled exact formulas. No independent normalization or FEM solve.'}


def main():
    amplitudes = [tuple(c+1 for c in tile) for tile in COLORS]
    assert len(set(COLORS)) == 11 and {c for tile in COLORS for c in tile} == {0, 1, 2, 3}
    B = projected_flux_matrix()
    horizontal = [[int(a[1] == b[0]) for b in COLORS] for a in COLORS]
    vertical = [[int(a[3] == b[2]) for b in COLORS] for a in COLORS]
    # At t=1/2 the common profile is exactly one. Distinct amplitudes imply
    # distinct entire traces, not merely a match at a finite sampling grid.
    for i, a in enumerate(amplitudes):
        for j, b in enumerate(amplitudes):
            assert horizontal[i][j] == int(a[1] == b[0])
            assert vertical[i][j] == int(a[3] == b[2])

    # Supplement the analytic trace identities with independent edge evaluation.
    maximum_trace_error = 0.
    maximum_expansion_error = 0.
    maximum_sample_flux = 0.
    maximum_helmholtz_trace_error = 0.
    for a in amplitudes:
        for t in (.0, .127, .5, .781, 1.):
            points = ((0, t), (1, t), (t, 0), (t, 1))
            for side, (x, y) in enumerate(points):
                maximum_trace_error = max(maximum_trace_error,
                    abs(field(a, x, y)-a[side]*math.sin(math.pi*t)**2))
                maximum_helmholtz_trace_error = max(maximum_helmholtz_trace_error,
                    abs(helmholtz_field(a, x, y)-a[side]*math.sin(math.pi*t)))
            for x, y in [(t, .381), (.219, t), *points]:
                c = cosine_coefficients(a)
                expanded = sum(float(co)*math.cos(m*math.pi*x)*math.cos(n*math.pi*y)
                               for co, (m, n) in zip(c, MODES))
                maximum_expansion_error = max(maximum_expansion_error, abs(expanded-field(a, x, y)))
            # Differentiate the seven genuine cosine modes independently.
            for side, (x, y) in enumerate(points):
                derivative = sum(float(co)*(-m*math.pi*math.sin(m*math.pi*x)*math.cos(n*math.pi*y)
                                           if side < 2 else -n*math.pi*math.cos(m*math.pi*x)*math.sin(n*math.pi*y))
                                 for co, (m, n) in zip(cosine_coefficients(a), MODES))
                maximum_sample_flux = max(maximum_sample_flux, abs(derivative))
    assert maximum_trace_error < 2e-15 and maximum_helmholtz_trace_error < 2e-15
    assert maximum_expansion_error < 4e-15 and maximum_sample_flux < 1e-14

    # Exact modal traces: at x=0,1 the cosine is respectively 1,(-1)^m.
    # sin^2(pi*t) has cosine coefficients (1/2,0,-1/2) at n=0,1,2.
    for a in amplitudes:
        coefficients = cosine_coefficients(a)
        for side in range(4):
            trace = {0: Fraction(0), 1: Fraction(0), 2: Fraction(0)}
            for c, (m, n) in zip(coefficients, MODES):
                frequency = n if side < 2 else m
                fixed_frequency = m if side < 2 else n
                sign = (-1)**fixed_frequency if side in (1, 3) else 1
                trace[frequency] += c*sign
            assert trace == {0: Fraction(a[side], 2), 1: Fraction(0), 2: -Fraction(a[side], 2)}

    # The alternative single-frequency lift fails flux matching for this palette.
    # The sine and linear parts are linearly independent. Vanishing vertical
    # seam flux would require S_left+S_right=N_left+N_right=0, and horizontal
    # seam flux would require W_bottom+W_top=E_bottom+E_top=0.
    assert all(all(value > 0 for value in a) for a in amplitudes)
    output = {
        'date': '2026-10-09', 'status': 'passed',
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'source': {'authors': 'Emmanuel Jeandel and Michael Rao',
                   'title': 'An aperiodic set of 11 Wang tiles',
                   'url': 'https://arxiv.org/html/1506.06492v4#S4.F4',
                   'figure': 4, 'theorem': 3,
                   'extraction': 'Math labels and their positions in the authors\' Figure 4 SVG; left-to-right order.'},
        'tuple_order': list(SIDES), 'color_amplitude_map': [1, 2, 3, 4],
        'palette': [{'id': i+1, 'colors': list(c), 'edge_amplitudes': list(a),
                     'cosine_coefficients': [str(x) for x in cosine_coefficients(a)]}
                    for i, (c, a) in enumerate(zip(COLORS, amplitudes))],
        'Neumann_cosine_modes': [{'indices': list(k), 'normalized_eigenvalue': sum(x*x for x in k)} for k in MODES],
        'number_of_Neumann_modes': 7, 'normalized_eigenvalues_used': [0, 1, 4, 5],
        'edge_carrier_space_dimension': 4,
        'horizontal_adjacency': horizontal, 'vertical_adjacency': vertical,
        'directed_value_compatible_pairs': {'horizontal': sum(map(sum, horizontal)),
                                          'vertical': sum(map(sum, vertical))},
        'projected_outward_flux_matrix': B, 'boundary_basis_norm_squared': '1/2',
        'maximum_sample_trace_error': maximum_trace_error,
        'maximum_sample_cosine_expansion_error': maximum_expansion_error,
        'maximum_sample_Neumann_normal_derivative': maximum_sample_flux,
        'single_frequency_alternative': {'normalized_Helmholtz_value': 1, 'basis_dimension': 4,
            'maximum_sample_trace_error': maximum_helmholtz_trace_error,
            'fixed_operator': 'Trace in F and P_F outward_flux = B trace; common self-adjoint nonlocal operator. Lowest eigenvalue pi^2 has multiplicity four by the boundary-form proof in the Notes.',
            'flux_matching': 'Impossible for the strictly positive palette; this alternative has interface sources.'},
        'placement_model': 'One unit square per integer grid cell; translations only; fixed amplitude palette; equality of scalar traces.',
        'aperiodicity': 'Exact bijection to the cited Wang set. Infinite existence and absence of nonzero grid periods use Jeandel--Rao\'s theorem, not these finite pair checks.',
        'flux_matching': 'The total static field is continuously matched and every square has exactly zero outward normal derivative. Each summand is a homogeneous Neumann eigenfunction.',
        'limitations': 'The total static field combines four eigenvalues; it is not a single Helmholtz eigenfunction, and separate frequencies generally do not match. The finite coefficient palette is essential. Reflections of states are excluded. No tiling/search engine or wave evolution is constructed.',
        'atlas': render_atlas(amplitudes),
    }
    (ROOT/'boundary-mode-palette.json').write_text(json.dumps(output, indent=2)+'\n')
    print(json.dumps({key: output[key] for key in ['status', 'number_of_Neumann_modes', 'directed_value_compatible_pairs',
                                                'maximum_sample_trace_error', 'maximum_sample_Neumann_normal_derivative']}, indent=2))


if __name__ == '__main__':
    main()
