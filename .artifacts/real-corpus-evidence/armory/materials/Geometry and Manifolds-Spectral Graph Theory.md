[[geometry-manifolds.base]]

> Source: [[Spectral Graph Theory]]
> License: Wikipedia content is available under CC BY-SA 4.0.

In [mathematics](https://en.wikipedia.org/wiki/Mathematics), **spectral [graph theory](https://en.wikipedia.org/wiki/Graph_theory)** is the study of the properties of a [graph](https://en.wikipedia.org/wiki/Graph_(discrete_mathematics) "Graph (discrete mathematics)") in relationship to the [characteristic polynomial](https://en.wikipedia.org/wiki/Characteristic_polynomial), [eigenvalues](https://en.wikipedia.org/wiki/Eigenvalue), and [eigenvectors](https://en.wikipedia.org/wiki/Eigenvector) of matrices associated with the graph, such as its [adjacency matrix](https://en.wikipedia.org/wiki/Adjacency_matrix) or [[Laplacian Matrix]].

The adjacency matrix of a simple undirected graph is a [real](https://en.wikipedia.org/wiki/Real_number) [symmetric matrix](https://en.wikipedia.org/wiki/Symmetric_matrix) and is therefore [orthogonally diagonalizable](https://en.wikipedia.org/wiki/Orthogonal_diagonalization); its eigenvalues are real [algebraic integers](https://en.wikipedia.org/wiki/Algebraic_integer).

While the adjacency matrix depends on the vertex labeling, its [spectrum](https://en.wikipedia.org/wiki/Spectrum_of_a_matrix) is a [graph invariant](https://en.wikipedia.org/wiki/Graph_invariant), although not a [complete](https://en.wikipedia.org/wiki/Complete_set_of_invariants) one.

Spectral graph theory is also concerned with graph parameters that are defined via multiplicities of eigenvalues of matrices associated to the graph, such as the [Colin de Verdière number](https://en.wikipedia.org/wiki/Colin_de_Verdi%C3%A8re_graph_invariant).

## Cospectral graphs

Two graphs are called **cospectral** or **isospectral** if the adjacency matrices of the graphs are [isospectral](https://en.wikipedia.org/wiki/Isospectral), that is, if the adjacency matrices have the same eigenvalues with multiplicity.

![[media/e48828ae2c492f3a51cd3a26a8dee54825b5dfed.png]]
Two cospectral [enneahedra](https://en.wikipedia.org/wiki/Enneahedron), the smallest possible cospectral [polyhedral graphs](https://en.wikipedia.org/wiki/Polyhedral_graph)

Cospectral graphs need not be [isomorphic](https://en.wikipedia.org/wiki/Graph_isomorphism), but isomorphic graphs are always cospectral.

### Graphs determined by their spectrum

A graph $G$ is said to be determined by its spectrum if any other graph with the same spectrum as $G$ is isomorphic to $G$.

Some first examples of families of graphs that are determined by their spectrum include:

- The [complete graphs](https://en.wikipedia.org/wiki/Complete_graph).
- The finite [starlike trees](https://en.wikipedia.org/wiki/Starlike_tree).

### Cospectral mates

Two graphs are said to be cospectral mates if they are cospectral but are non-isomorphic.

The smallest pair of cospectral mates is {*K*<sub>1,4</sub>, *C*<sub>4</sub> ∪ *K*<sub>1</sub>}, comprising the 5-vertex [star](https://en.wikipedia.org/wiki/Star_(graph_theory) "Star (graph theory)") and the [graph union](https://en.wikipedia.org/wiki/Graph_union) of the 4-vertex [cycle](https://en.wikipedia.org/wiki/Cycle_(graph_theory) "Cycle (graph theory)") and the single-vertex graph. The first example of cospectral graphs was reported by Collatz and Sinogowitz in 1957.

The smallest pair of [polyhedral](https://en.wikipedia.org/wiki/Polyhedral_graph) cospectral mates are [enneahedra](https://en.wikipedia.org/wiki/Enneahedron) with eight vertices each.

### Finding cospectral graphs

[Almost all](https://en.wikipedia.org/wiki/Almost_all) [trees](https://en.wikipedia.org/wiki/Tree_(graph_theory) "Tree (graph theory)") are cospectral, i.e., as the number of vertices grows, the fraction of trees for which there exists a cospectral tree goes to 1.

A pair of [regular graphs](https://en.wikipedia.org/wiki/Regular_graph) are cospectral if and only if their complements are cospectral.

A pair of [distance-regular graphs](https://en.wikipedia.org/wiki/Distance-regular_graph) are cospectral if and only if they have the same intersection array.

Cospectral graphs can also be constructed by means of the [Sunada method](https://en.wikipedia.org/wiki/Isospectral).

Another important source of cospectral graphs are the point-collinearity graphs and the line-intersection graphs of [point-line geometries](https://en.wikipedia.org/wiki/Incidence_geometry). These graphs are always cospectral but are often non-isomorphic.

## Cheeger inequality

The famous [Cheeger's inequality](https://en.wikipedia.org/wiki/Cheeger_constant#Cheeger.27s_inequality) from [[Riemannian Geometry]] has a discrete analogue involving the Laplacian matrix; this is perhaps the most important theorem in spectral graph theory and one of the most useful facts in algorithmic applications. It approximates the sparsest cut of a graph through the second eigenvalue of its Laplacian.

### Cheeger constant

The **Cheeger constant** (also **Cheeger number** or **isoperimetric number**) of a [graph](https://en.wikipedia.org/wiki/Graph_(discrete_mathematics) "Graph (discrete mathematics)") is a numerical measure of whether or not a graph has a "bottleneck". The Cheeger constant as a measure of "bottleneckedness" is of great interest in many areas: for example, constructing well-connected [networks of computers](https://en.wikipedia.org/wiki/Computer_networking), [card shuffling](https://en.wikipedia.org/wiki/Shuffling), and [low-dimensional topology](https://en.wikipedia.org/wiki/Geometric_topology) (in particular, the study of [hyperbolic](https://en.wikipedia.org/wiki/Hyperbolic_geometry) 3-[[Manifold|manifolds]]).

More formally, the Cheeger constant *h*(*G*) of a graph *G* on *n* vertices is defined as

$h(G)=\min _{0<|S|\leq {\frac {n}{2}}}{\frac {|\partial (S)|}{|S|}},$

where the minimum is over all nonempty sets *S* of at most *n*/2 vertices and ∂(*S*) is the *edge boundary* of *S*, i.e., the set of edges with exactly one endpoint in *S*.

### Cheeger inequality

When the graph *G* is *d*-regular, there is a relationship between *h*(*G*) and the spectral gap *d* − λ<sub>2</sub> of *G*. An inequality due to Dodziuk and independently [Alon](https://en.wikipedia.org/wiki/Noga_Alon) and [Milman](https://en.wikipedia.org/wiki/Vitali_Milman) states that

${\frac {1}{2}}(d-\lambda _{2})\leq h(G)\leq {\sqrt {2d(d-\lambda _{2})}}.$

This inequality is closely related to the [Cheeger bound](https://en.wikipedia.org/wiki/Cheeger_bound) for [Markov chains](https://en.wikipedia.org/wiki/Markov_chains) and can be seen as a discrete version of [Cheeger's inequality](https://en.wikipedia.org/wiki/Cheeger_constant#Cheeger.27s_inequality) in [[Riemannian Geometry]].

For general connected graphs that are not necessarily regular, an alternative inequality is given by Chung

${\frac {1}{2}}{\lambda }\leq {\mathbf {h} }(G)\leq {\sqrt {2\lambda }},$

where $\lambda$ is the least nontrivial eigenvalue of the normalized Laplacian, and ${\mathbf {h} }(G)$ is the (normalized) Cheeger constant

${\mathbf {h} }(G)=\min _{\emptyset \not =S\subset V(G)}{\frac {|\partial (S)|}{\min({\mathrm {vol} }(S),{\mathrm {vol} }({\bar {S}}))}}$

where ${\mathrm {vol} }(Y)$ is the sum of degrees of vertices in $Y$.

## Hoffman–Delsarte inequality

There is an eigenvalue bound for [independent sets](https://en.wikipedia.org/wiki/Independent_set_(graph_theory) "Independent set (graph theory)") in [regular graphs](https://en.wikipedia.org/wiki/Regular_graph), originally due to [Alan J. Hoffman](https://en.wikipedia.org/wiki/Alan_J._Hoffman) and Philippe Delsarte.

Suppose that $G$ is a $k$-regular graph on $n$ vertices with least eigenvalue $\lambda _{\mathrm {min} }$. Then:

$$
\alpha (G)\leq {\frac {n}{1-{\frac {k}{\lambda _{\mathrm {min} }}}}}
$$

where $\alpha (G)$ denotes its [independence number](https://en.wikipedia.org/wiki/Independence_number).

This bound has been applied to establish e.g. algebraic proofs of the [Erdős–Ko–Rado theorem](https://en.wikipedia.org/wiki/Erd%C5%91s%E2%80%93Ko%E2%80%93Rado_theorem) and its analogue for intersecting families of subspaces over [finite fields](https://en.wikipedia.org/wiki/Finite_field).

For general graphs which are not necessarily regular, a similar upper bound for the independence number can be derived by using the maximum eigenvalue $\lambda '_{max}$ of the normalized Laplacian of $G$: 

$$
\alpha (G)\leq n(1-{\frac {1}{\lambda '_{\mathrm {max} }}}){\frac {\mathrm {maxdeg} }{\mathrm {mindeg} }}
$$

 where ${\mathrm {maxdeg} }$ and ${\mathrm {mindeg} }$ denote the maximum and minimum degree in $G$, respectively. This a consequence of a more general inequality (pp. 109 in ): 

$$
{\mathrm {vol} }(X)\leq (1-{\frac {1}{\lambda '_{\mathrm {max} }}}){\mathrm {vol} }(V(G))
$$

 where $X$ is an independent set of vertices and ${\mathrm {vol} }(Y)$ denotes the sum of degrees of vertices in $Y$ .

## Historical outline

Spectral graph theory emerged in the 1950s and 1960s. Besides [graph theoretic](https://en.wikipedia.org/wiki/Graph_theory) research on the relationship between structural and spectral properties of graphs, another major source was research in [quantum chemistry](https://en.wikipedia.org/wiki/Quantum_chemistry), but the connections between these two lines of work were not discovered until much later. The 1980 monograph *Spectra of Graphs* by Cvetković, Doob, and Sachs summarised nearly all research to date in the area. In 1988 it was updated by the survey *Recent Results in the Theory of Graph Spectra*. The 3rd edition of *Spectra of Graphs* (1995) contains a summary of the further recent contributions to the subject.

The field of discrete geometric analysis, created and developed by [Toshikazu Sunada](https://en.wikipedia.org/wiki/Toshikazu_Sunada) in the 2000s, deals with spectral graph theory in terms of discrete Laplacians associated with weighted graphs. It finds application in various other fields, including [shape analysis](https://en.wikipedia.org/wiki/Spectral_shape_analysis).

A more recent development in spectral graph theory is vertex-frequency analysis, a set of techniques for solving problems in many real-life applications such as [signal processing](https://en.wikipedia.org/wiki/Signal_processing).

## See also

- [Strongly regular graph](https://en.wikipedia.org/wiki/Strongly_regular_graph)
- [Algebraic connectivity](https://en.wikipedia.org/wiki/Algebraic_connectivity)
- [Algebraic graph theory](https://en.wikipedia.org/wiki/Algebraic_graph_theory)
- [Spectral clustering](https://en.wikipedia.org/wiki/Spectral_clustering)
- [Spectral shape analysis](https://en.wikipedia.org/wiki/Spectral_shape_analysis)
- [Estrada index](https://en.wikipedia.org/wiki/Estrada_index)
- [Lovász theta](https://en.wikipedia.org/wiki/Lov%C3%A1sz_theta)
- [Expander graph](https://en.wikipedia.org/wiki/Expander_graph)

## References

1.  [Weisstein, Eric W.](https://en.wikipedia.org/wiki/Eric_W._Weisstein) ["Cospectral Graphs"](https://mathworld.wolfram.com/CospectralGraphs.html). *[MathWorld](https://en.wikipedia.org/wiki/MathWorld)*.
2.  Collatz, L. and Sinogowitz, U. "Spektren endlicher Grafen." Abh. Math. Sem. Univ. Hamburg 21, 63–77, 1957.
3.  [Hosoya, Haruo](https://en.wikipedia.org/wiki/Haruo_Hosoya); Nagashima, Umpei; Hyugaji, Sachiko (1994), "Topological twin graphs. Smallest pair of isospectral polyhedral graphs with eight vertices", *Journal of Chemical Information and Modeling*, **34** (2): 428–431, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1021/ci00018a033](https://doi.org/10.1021%2Fci00018a033).
4.  , pp. 275–307.
5.  Godsil, Chris (November 7, 2007). ["Are Almost All Graphs Cospectral?"](http://www.math.uwaterloo.ca/~cgodsil/pdfs/cospectral.pdf) (PDF).
6.  Sunada, Toshikazu (1985), "Riemannian coverings and isospectral manifolds", *Ann. of Math.*, **121** (1): 169–186, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/1971195](https://doi.org/10.2307%2F1971195), [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [1971195](https://www.jstor.org/stable/1971195).
7.  8.  Definition 2.1 in 
9.  J.Dodziuk, Difference Equations, Isoperimetric inequality and Transience of Certain Random Walks, Trans. Amer. Math. Soc. 284 (1984), no. 2, 787-794.
10. .
11. Theorem 2.4 in 
12. ^    [Chung, Fan](https://en.wikipedia.org/wiki/Fan_Chung) (1997). American Mathematical Society (ed.). [Spectral Graph Theory](http://www.math.ucsd.edu/~fan/research/revised.html). Providence, R. I. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0821803158](https://en.wikipedia.org/wiki/Special:BookSources/0821803158). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1421568](https://mathscinet.ams.org/mathscinet-getitem?mr=1421568)\[first 4 chapters are available in the website\]`{{`[`cite book`](https://en.wikipedia.org/wiki/Template:Cite_book)`}}`: CS1 maint: postscript ([link](https://en.wikipedia.org/wiki/Category:CS1_maint:_postscript))
13. Godsil, Chris (May 2009). ["Erdős-Ko-Rado Theorems"](https://www.math.uwaterloo.ca/~cgodsil/pdfs/ekrs-clg.pdf) (PDF).
14. Godsil, C. D.; Meagher, Karen (2016). *Erdős-Ko-Rado theorems : algebraic approaches*. Cambridge, United Kingdom. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9781107128446](https://en.wikipedia.org/wiki/Special:BookSources/9781107128446). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [935456305](https://search.worldcat.org/oclc/935456305).`{{`[`cite book`](https://en.wikipedia.org/wiki/Template:Cite_book)`}}`: CS1 maint: location missing publisher ([link](https://en.wikipedia.org/wiki/Category:CS1_maint:_location_missing_publisher))
16. Dragoš M. Cvetković, Michael Doob, [Horst Sachs](https://en.wikipedia.org/wiki/Horst_Sachs), *Spectra of Graphs* (1980)
17. Cvetković, Dragoš M.; Doob, Michael; Gutman, Ivan; Torgasev, A. (1988). [Recent Results in the Theory of Graph Spectra](http://www.sciencedirect.com/science/bookseries/01675060/36). Annals of Discrete mathematics. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-444-70361-6](https://en.wikipedia.org/wiki/Special:BookSources/0-444-70361-6).
18. Sunada, Toshikazu (2008), "Discrete geometric analysis", *Proceedings of Symposia in Pure Mathematics*, **77**: 51–86, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1090/pspum/077/2459864](https://doi.org/10.1090%2Fpspum%2F077%2F2459864), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780821844717](https://en.wikipedia.org/wiki/Special:BookSources/9780821844717)`{{`[`citation`](https://en.wikipedia.org/wiki/Template:Citation)`}}`: CS1 maint: work parameter with ISBN ([link](https://en.wikipedia.org/wiki/Category:CS1_maint:_work_parameter_with_ISBN)).
19. Shuman, David I; Ricaud, Benjamin; Vandergheynst, Pierre (March 2016). "Vertex-frequency analysis on graphs". *Applied and Computational Harmonic Analysis*. **40** (2): 260–291. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1307.5708](https://arxiv.org/abs/1307.5708). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.acha.2015.02.005](https://doi.org/10.1016%2Fj.acha.2015.02.005). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1063-5203](https://search.worldcat.org/issn/1063-5203). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [16487065](https://api.semanticscholar.org/CorpusID:16487065).
20. Stankovic, Ljubisa; Dakovic, Milos; Sejdic, Ervin (July 2017). "Vertex-Frequency Analysis: A Way to Localize Graph Spectral Components \[Lecture Notes\]". *IEEE Signal Processing Magazine*. **34** (4): 176–182. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2017ISPM...34..176S](https://ui.adsabs.harvard.edu/abs/2017ISPM...34..176S). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/msp.2017.2696572](https://doi.org/10.1109%2Fmsp.2017.2696572). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1053-5888](https://search.worldcat.org/issn/1053-5888). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [19969572](https://api.semanticscholar.org/CorpusID:19969572).
21. Sakiyama, Akie; Watanabe, Kana; Tanaka, Yuichi (September 2016). "Spectral Graph Wavelets and Filter Banks With Low Approximation Error". *IEEE Transactions on Signal and Information Processing over Networks*. **2** (3): 230–245. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/tsipn.2016.2581303](https://doi.org/10.1109%2Ftsipn.2016.2581303). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [2373-776X](https://search.worldcat.org/issn/2373-776X). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [2052898](https://api.semanticscholar.org/CorpusID:2052898).
22. Behjat, Hamid; Richter, Ulrike; Van De Ville, Dimitri; Sornmo, Leif (2016-11-15). ["Signal-Adapted Tight Frames on Graphs"](http://infoscience.epfl.ch/record/223159). *IEEE Transactions on Signal Processing*. **64** (22): 6017–6029. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2016ITSP...64.6017B](https://ui.adsabs.harvard.edu/abs/2016ITSP...64.6017B). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/tsp.2016.2591513](https://doi.org/10.1109%2Ftsp.2016.2591513). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1053-587X](https://search.worldcat.org/issn/1053-587X). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [12844791](https://api.semanticscholar.org/CorpusID:12844791).

- Alon; Spencer (2011), *The probabilistic method*, Wiley.
- [Brouwer, Andries](https://en.wikipedia.org/wiki/Andries_Brouwer); Haemers, Willem H. (2011), [Spectra of Graphs](http://www.win.tue.nl/~aeb/2WF02/spectra.pdf) (PDF), Springer
- Hoory; Linial; Wigderson (2006), [Expander graphs and their applications](https://www.cs.huji.ac.il/~nati/PAPERS/expander_survey.pdf) (PDF)
- [Chung, Fan](https://en.wikipedia.org/wiki/Fan_Chung) (1997). American Mathematical Society (ed.). [Spectral Graph Theory](http://www.math.ucsd.edu/~fan/research/revised.html). Providence, R. I. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0821803158](https://en.wikipedia.org/wiki/Special:BookSources/0821803158). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1421568](https://mathscinet.ams.org/mathscinet-getitem?mr=1421568)\[first 4 chapters are available in the website\]`{{`[`cite book`](https://en.wikipedia.org/wiki/Template:Cite_book)`}}`: CS1 maint: postscript ([link](https://en.wikipedia.org/wiki/Category:CS1_maint:_postscript))
- Bogdan, Nica (2018). *"A Brief Introduction to Spectral Graph Theory"*. Zurich: EMS Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-03719-188-0](https://en.wikipedia.org/wiki/Special:BookSources/978-3-03719-188-0).
- [Pavel Kurasov (2024), Spectral Geometry of Graphs, Springer(Birkhauser), Open Access (CC4.0).](https://doi.org/10.1007/978-3-662-67872-5)
- Naderi, Kiyan; Pankrashkin, Konstantin (2025), [Introduction to Spectral Graph Theory](https://doi.org/10.1007/978-3-032-01708-6), Springer, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-032-01708-6](https://en.wikipedia.org/wiki/Special:BookSources/978-3-032-01708-6)

## External links

- [Spielman, Daniel](https://en.wikipedia.org/wiki/Daniel_Spielman) (2011). ["Spectral Graph Theory"](http://www.cs.yale.edu/~spielman/PAPERS/SGTChapter.pdf) (PDF). \[chapter from Combinatorial Scientific Computing\]
- Spielman, Daniel (2007). ["Spectral Graph Theory and its Applications"](http://cs-www.cs.yale.edu/homes/spielman/sgta/). \[presented at FOCS 2007 Conference\]
- Spielman, Daniel (2004). ["Spectral Graph Theory and its Applications"](http://www.cs.yale.edu/homes/spielman/eigs/). \[course page and lecture notes\]
