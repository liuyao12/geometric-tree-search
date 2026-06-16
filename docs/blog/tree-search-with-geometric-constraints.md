<!--
Edit this Markdown file to update the GCTS HTML article pages.
The browser pages fetch and render this file, with embedded HTML as a fallback.
-->

# Geometrically Constrained Tree Search I — Learning matching rules in tiling

We describe a general method, **Geometrically Constrained Tree Search (GCTS)**, to solve certain combinatorial problems of tree search with "geometric constraints", in some respect similar to methods in **geometric deep learning**, specifically *equivariant* neural networks. For illustration we shall focus on the tiling problem: given a set of tiles (in 2D or 3D), with or without local matching rules, determine if and how they tile the plane or space, or a subset with prescribed boundary. The core algorithm is to learn a pattern of markings on the tiles that may be used to accelerate the tree search, by identifying and excluding unwanted branches. When working, it shall compensate for a rudimentary (greedy and slow, no heuristics) tree search algorithm, and may provide an *interpretable* and *provably correct* algorithm. It shall become clear what is meant by all this.

We shall further restrict to tilings that can be placed on a lattice, i.e., all the vertices shall be on a lattice. In fact, this study was partly inspired by the discovery of the hat and the turtle ([Smith et al, 2023](https://cs.uwaterloo.ca/~csk/hat/)) which, aside from being a solution to the "ein stein" problem that was the holy grail for much of tiling theory, actually live on the $A_2$ lattice. This goes to show that, despite their rather rigid nature, lattice tilings are rich enough to be a furtile playground for combinatorial and discrete geometry, and as a portal to logic and computation via Wang tiles. Moreover, it appears that many known [space-fillers](../../apps/3d-lattice-tiler/) are lattice tiles on the standard integer lattice in $\mathbb{R}^3$.

## Tiles and tilings

Let's fix the (standard) $\mathbb{Z}^3$ lattice in the Euclidean 3-space. By a **lattice tile** (or **tile** for short) we shall mean a function


$$
 t: \mathbb{Z}^3 \to \mathbb{R} 
$$


that is *finitely* supported, taking values between 0 and 1, inclusive. The interpretation of the value $t({\bf x})$ at a point ${\bf x} \in \mathbb{Z}^3$ shall be the "solid angle" at ${\bf x}$, or the proportion of the $\epsilon$-neighborhood of ${\bf x}$ that is supposed to be "inside the tile". (We leave aside the question if or when a polyhedral tile *in the usual sense*, with all its vertices on the lattice, has a *faithful* realization as a lattice tile per our definition.)

A lattice tile $t$ is said **to tile** space if there exists a subset $K$ of the group $G$ of symmetries of the lattice such that


$$
 \sum_{g \in K} t(g^{-1} {\bf x}) = 1
$$


as a function on $\mathbb{Z}^3$. The group $G$ consists of permuting and reversing the axes, and translating by integral vectors. Similar definition can be made for a set of tiles $\{t_1, t_2, \ldots,  t_n \}$ **to tile** space:


$$
 \sum_{i=1}^{n} \sum_{g \in K_i} t_i(g^{-1} {\bf x}) = 1
$$


(If the right-hand side is replaced by a constant $N > 1$, it is known as a *multi-tiling*, or an *$N$-fold tiling*.)

*Example.* The regular tetrahedron. The vertices are $[1,0,0]$, $[0,1,0]$, $[0,0,1]$, and $[1,1,1]$, where the solid angle is irrational, thus the regular tetrahedron does not tile space. However, together with the regular octahedron (with vertices at $\pm {\bf e}_i$, $i=1,2,3$), they do tile space, in a unique way.

Naturally, if the tile $t_i$ itself has inherent symmetry, in the sense that $t_i({\bf x}) = t_i(g^{-1}{\bf x})$, we should "quotient it out" from $G$ when searching for $K_i$.

*Example.* The tetrahedron with vertices at $[0,0,0]$, $[1,0,0]$, $[1,1,0]$, and $[1,1,1]$ does tile space, with six copies filling a unit cube. The value at the four vertices are 1, 3, 3, and 1 forty-eighths, respectively.

*Example.* The hat and the turtle (see figures). Each is a 14-sided polygon lying on the $x_1+x_2+x_3=0$ plane, and we can turn it into a cylinder to fit our 3D tiling game. Alternatively, we may restrict $G$ to symmetries of the sublattice, and to assign the values to be (plain-old, 2D) angles. It happens that the only values are 3, 4, 6, 8, and 9 twelveths. The remarkable fact about the hat (and the turtle) is that it tiles the plane, and *only* non-periodically ([Smith et al, 2023](https://cs.uwaterloo.ca/~csk/hat/)).

![Observable attachment](https://static.observableusercontent.com/files/de43ce7110c6497283e1992a2a620cc026a9b6b7ad14529590de50373890d14b6288a824373b9194e140ef3ec8a49fc618ee5293eb8644a46d20e62afb689f9e)

![Observable attachment](https://static.observableusercontent.com/files/35a021f043676a7deb9490a0d8fdf7718f6c1a0c252cb52b19e4a785259af61273ab214769baf3426614edf052490476a2fc4bbccbe08ffc3332c4d9d7315375)

Finding the subsets $K_i$ (or showing none exists) is a problem of combinatorial tree search. We could place the first tile anywhere (or simply with $i=1$, $g=1$), and for a specific ${\bf p}$ with $0 < t_1({\bf p}) < 1$, there are *finitely* many ways to place the second tile (choices of $i$ and $g \in G$) such that $t_i(g^{-1} {\bf p}) > 0$ and


$$
 t_1({\bf x}) + t_i(g^{-1} {\bf x}) \leq 1
$$


for all ${\bf x}$, and we put this $g$ in $K_i$, and repeat the process. Thus we obtain a finite-branching tree to search over. A branch stops or dies if it runs out of choices (for any "boundary point" ${\bf p}$). We are particularly interested in tiles that admit nontrivial tilings: neither too restricted that the branchings all have a unique choice, nor too loose that *any* branch appears to lead to valid tilings. Note that this algorithm could not tell whether a (partial) tiling is periodic, and by itself is unable to say if it actually extends to a tiling of the whole space.

In practice, it may be more natural to "branch over" faces instead of boundary points; and we may adopt simple rules to choose the face or the point ${\bf p}$ for each branching, but no need to employ more sophisticated heuristics. This is essentially what is implemented [here](../../apps/3d-lattice-tiler/).

## Markings and matching rules

When playing jigsaw puzzles, we would direct our attention to the colors and patterns on the pieces; two pieces fit not just by the geometry (shape of the boundary) but the patterns have to "match". Similarly in tiling, we would often, for the sake of forcing aperiodicity, introduce "markings" on the tiles, along with "matching rules" that the markings need to match in certain ways. Not the least, the Wang tiles work via color matching. Let's formalize all these in a definition, specialized for our discrete setting.

By a **marking** on a lattice tile $t$, we shall mean a function


$$
 m : \mathbb{Z}^3 \to \mathbb{R}
$$


with support that *may be larger* than that of the tile. We say that $t$ **tiles** space **with marking $m$** if, in addition to the above, we have for any $g, h \in K$,


$$
 m(g^{-1} {\bf x}) = m(h^{-1} {\bf x})
$$


on the overlap of their supports. This way, all these transformed functions would *glue* to be a "global section" of this (trivial) sheaf.

It is natural to extend this definition to a vector bundle:


$$
 m : \mathbb{Z}^3 \to \mathbb{R}^n
$$


and there is an action of $G$ on $\mathbb{R}^n$ (a representation), then the matching rule would be


$$
 g\cdot m(g^{-1} {\bf x}) = h \cdot m(h^{-1} {\bf x})
$$


on the overlap.

*Example.* The turtle admits a marking of straight lines (see [Akiyama & Araki](https://arxiv.org/abs/2307.12322) or [mathblock8128](https://mathblock8128.wordpress.com/)). The two colors represent $\pm 1$ values for the lattice points on *three* separate markings, or a rank-3 bundle. The group $G$ acts on $\mathbb{R}^3$ by permuting and negating the components (swapping the two colors upon reflections). Note that the domain of each marking may be taken to be arbitrarily long, a sign of long-range order.

![](https://mathblock8128.wordpress.com/wp-content/uploads/2023/08/spar_crossing_control_landscape_cb_2.png?w=800)

*Example.* The classic "domino puzzle" (with the checkerboard argument) may be cast as a problem of tiling with marking. It seems that a good source of candidates for markings would be the eigenfunctions of the Laplacian operator, with Dirichlet or Neumann (or mixed) boundary conditions.

The (naive) tiling algorithm can be easily modified to incorporate this kind of matching rule, simply by excluding those branches that disagree on overlap, and keeping track of a "global section" from all the tiles. This turns out to work remarkably well for the turtle.

## Geometric Deep Learning

We have reduced tiling to its combinatorics, though the markings do retain a geometric flavor, one might say. Where does deep learning come in? As we have seen, the (naive) tiling algorithm for the turtle is greatly accelerated when we enforce the matching rules with straight line markings, which incidentally were identified by human intelligence. It seems natural (and perfectly set up) for a simple machine learning algorithm to *learn* the markings on this and other tiles, from enough (or even a complete set of) positive and negative samples of local patches. The presence of group action may remind one of *equivariant* neural networks, sometimes branded as *geometric deep learning*.

Another component, more of a *reinforcement learning* nature, may be necessary for a full resolution of the tiling problem. It shall attempt to learn or recognize "patches" or "clusters" of tiles that may themselves have markings on them, giving rise to periodic tilings or hierarchical structure of aperiodic tilings. It may not be out of place to note that Wang's original papers were titled *Proving Theorems by Pattern Recognition I* & *II*.

## Draft: From tiles to arbitrary search trees

One may try to turn a general tree search problem into a geometrically constrained one by assigning every node, or every partial state, a position in a two-dimensional plane. The placement is not meant to be merely a visualization. It should carry information about which continuations are still viable, which local patterns are forbidden, and which partial configurations are equivalent up to a symmetry or a harmless deformation.

In this view, the learned geometric rules play the role that the tile shape and markings played above. The shape says which placements are physically impossible because they overlap or leave an unfillable boundary. The markings say which placements are semantically impossible because the local labels cannot be glued into a consistent global section. For a non-tiling tree search problem, the corresponding rules might be learned from examples of successful and failed branches: neighboring nodes in the plane must satisfy learned compatibility constraints, and a partial branch dies when its local neighborhood cannot be completed.

The practical hope is that the plane becomes a low-dimensional certificate language for pruning. Instead of asking a policy network to guess the next move directly, we ask it to learn the obstructions: regions that cannot coexist, boundary patterns that force a small number of continuations, and markings that expose hidden invariants. Then a search procedure can remain simple and checkable while the learned geometry supplies the domain knowledge. In that sense GCTS would be a cousin of MCTS, but with geometric viability replacing rollout value as the organizing principle.
