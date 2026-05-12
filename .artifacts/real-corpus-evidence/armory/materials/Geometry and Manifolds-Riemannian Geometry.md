[[geometry-manifolds.base]]

> Source: [[Riemannian Geometry]]
> License: Wikipedia content is available under CC BY-SA 4.0.

**Riemannian geometry** is the branch of [differential geometry](https://en.wikipedia.org/wiki/Differential_geometry) that studies [Riemannian manifolds](https://en.wikipedia.org/wiki/Riemannian_manifold). An example of a Riemannian manifold is a [surface](https://en.wikipedia.org/wiki/Surface_(mathematics) "Surface (mathematics)"), on which distances are measured by the length of curves on the surface. Riemannian geometry is the study of surfaces and their higher-dimensional analogs (called *[[Manifold|manifolds]]*), in which distances are calculated along curves belonging to the manifold. Formally, Riemannian geometry is the study of [smooth manifolds](https://en.wikipedia.org/wiki/Smooth_manifold) with a *Riemannian metric* (an [inner product](https://en.wikipedia.org/wiki/Inner_product) on the [[Tangent Space]] at each point that varies [smoothly](https://en.wikipedia.org/wiki/Smooth_function) from point to point). This gives, in particular, local notions of [angle](https://en.wikipedia.org/wiki/Angle), [length of curves](https://en.wikipedia.org/wiki/Arc_length), [surface area](https://en.wikipedia.org/wiki/Surface_area) and [volume](https://en.wikipedia.org/wiki/Volume). From those, some other global quantities can be derived by [integrating](https://en.wikipedia.org/wiki/Integral) local contributions.

Riemannian geometry originated with the vision of [Bernhard Riemann](https://en.wikipedia.org/wiki/Bernhard_Riemann) expressed in his inaugural lecture "*Über die Hypothesen, welche der Geometrie zu Grunde liegen*" ("On the Hypotheses on which Geometry is Based"). It is a very broad and abstract generalization of the [differential geometry of surfaces](https://en.wikipedia.org/wiki/Differential_geometry_of_surfaces) in [**R**<sup>3</sup>](https://en.wikipedia.org/wiki/Three-dimensional_space). Development of Riemannian geometry resulted in synthesis of diverse results concerning the geometry of surfaces and the behavior of [geodesics](https://en.wikipedia.org/wiki/Geodesic) on them, with techniques that can be applied to the study of [differentiable manifolds](https://en.wikipedia.org/wiki/Differentiable_manifold) of higher dimensions. It enabled the formulation of [Einstein](https://en.wikipedia.org/wiki/Albert_Einstein)'s [general theory of relativity](https://en.wikipedia.org/wiki/General_theory_of_relativity), made profound impact on [group theory](https://en.wikipedia.org/wiki/Group_theory) and [representation theory](https://en.wikipedia.org/wiki/Representation_theory), as well as [analysis](https://en.wikipedia.org/wiki/Global_analytic_function), and spurred the development of [algebraic](https://en.wikipedia.org/wiki/Algebraic_topology) and [differential topology](https://en.wikipedia.org/wiki/Differential_topology).

## Introduction

![[media/232d2d28a082b2d42120e0bfb2f3e8bb718390eb.jpeg]]
Bernhard Riemann

Riemannian geometry was first put forward in generality by Bernhard Riemann in the 19th century. It deals with a broad range of geometries whose [metric](https://en.wikipedia.org/wiki/Metric_(mathematics)) properties vary from point to point, including the standard types of [non-Euclidean geometry](https://en.wikipedia.org/wiki/Non-Euclidean_geometry). The main idea is that a space, like a surface in Euclidean space, carries what is known as a [Riemannian metric](https://en.wikipedia.org/wiki/Riemannian_metric), which arises by restricting the ambient [dot product](https://en.wikipedia.org/wiki/Dot_product) to vectors that are [tangent](https://en.wikipedia.org/wiki/Tangent_vector) to the surface. Riemann realized that the essential ingredient here was this [quadratic form](https://en.wikipedia.org/wiki/Quadratic_form) on tangent vectors, and that it could be generalized. The important thing, the intrinsic way that paths in the surface could be measured, was not how the surface sat in space, but how this quadratic form varied from point to point. Consider the simple case of a [cylinder](https://en.wikipedia.org/wiki/Cylinder): a flat piece of paper can be wrapped into a cylinder, but the "intrinsic distance", that is the distance that an insect must crawl to get from one point to another, is not changed by the warping of a flat paper into three dimensions. A more advanced example, known to Riemann, was that the [helicoid](https://en.wikipedia.org/wiki/Helicoid) could (after cutting along a generator) be deformed to a [catenoid](https://en.wikipedia.org/wiki/Catenoid) without altering the intrinsic geometry (what an ant sees).

![[media/a36afb22a6ff9d8930ba136edb0a8bb490af1999.gif]]
Deformation of a right-handed [helicoid](https://en.wikipedia.org/wiki/Helicoid) into a left-handed one and back again via a catenoid, preserving this intrinsic metric (length of sides of mesh)

Riemann's idea was that it was the quadratic form which matters most, rather than the particular way a surface might be realized in space (a cylinder versus a piece of paper, for example). Riemannian geometry thus studies the intrinsic geometry of a manifold, equipped with a quadratic form on tangent vectors at every point. An important idea is that manifolds, unlike surfaces, need not be described as embedded in any particular Euclidean space: they may be described in local coordinate patches. In each coordinate patch, the metric has one expression, and when going to another patch, the metric changes by well-defined rules (essentially the [[Chain Rule]]).

A modern theorem is that *every* [smooth manifold](https://en.wikipedia.org/wiki/Smooth_manifold) admits a [Riemannian metric](https://en.wikipedia.org/wiki/Riemannian_metric) (in fact, many Riemannian metrics). The properties of such metrics are useful to constrain the [topology](https://en.wikipedia.org/wiki/Differential_topology) of the original manifold.

In Riemannian geometry, as in Euclidean geometry, the quadratic form is [positive definite](https://en.wikipedia.org/wiki/Positive_definite). Relaxing this condition, and allowing that some non-zero vectors can be [null](https://en.wikipedia.org/wiki/Null_vector) under the quadratic form allows the structure of [pseudo-Riemannian manifolds](https://en.wikipedia.org/wiki/Pseudo-Riemannian_manifold), which (in four dimensions) are the main objects of the [theory of general relativity](https://en.wikipedia.org/wiki/General_relativity). On the other hand, replacing the quadratic form by a more general non-quadratic function leads to [Finsler geometry](https://en.wikipedia.org/wiki/Finsler_manifold).

There exists a close analogy of differential geometry with the mathematical structure of defects in regular crystals. [Dislocations](https://en.wikipedia.org/wiki/Dislocation) and [disclinations](https://en.wikipedia.org/wiki/Disclination) produce torsions and curvature.

The following articles provide some useful introductory material:

- [Metric tensor](https://en.wikipedia.org/wiki/Metric_tensor)
- [Riemannian manifold](https://en.wikipedia.org/wiki/Riemannian_manifold)
- [Levi-Civita connection](https://en.wikipedia.org/wiki/Levi-Civita_connection)
- [Curvature](https://en.wikipedia.org/wiki/Curvature)
- [Riemann curvature tensor](https://en.wikipedia.org/wiki/Riemann_curvature_tensor)
- [List of differential geometry topics](https://en.wikipedia.org/wiki/List_of_differential_geometry_topics)
- [Glossary of Riemannian and metric geometry](https://en.wikipedia.org/wiki/Glossary_of_Riemannian_and_metric_geometry)

## Classical theorems

What follows is an incomplete list of the most classical theorems in Riemannian geometry. The choice is made depending on its importance and elegance of formulation. Most of the results can be found in the classic monograph by [Jeff Cheeger](https://en.wikipedia.org/wiki/Jeff_Cheeger) and D. Ebin (see below).

The formulations given are far from being very exact or the most general. This list is oriented to those who already know the basic definitions and want to know what these definitions are about.

### General theorems

1.  **[Gauss–Bonnet theorem](https://en.wikipedia.org/wiki/Gauss%E2%80%93Bonnet_theorem)** The integral of the Gauss curvature on a compact 2-dimensional Riemannian manifold is equal to 2π*χ*(*M*) where *χ*(*M*) denotes the [Euler characteristic](https://en.wikipedia.org/wiki/Euler_characteristic) of *M*. This theorem has a generalization to any compact even-dimensional Riemannian manifold, see [generalized Gauss-Bonnet theorem](https://en.wikipedia.org/wiki/Generalized_Gauss-Bonnet_theorem).
2.  **[Nash embedding theorems](https://en.wikipedia.org/wiki/Nash_embedding_theorem)**. They state that every [Riemannian manifold](https://en.wikipedia.org/wiki/Riemannian_manifold) can be isometrically [embedded](https://en.wikipedia.org/wiki/Embedding) in a [Euclidean space](https://en.wikipedia.org/wiki/Euclidean_space) **R**<sup>*n*</sup>.

### Geometry in large

In all of the following theorems we assume some local behavior of the space (usually formulated using curvature assumption) to derive some information about the global structure of the space, including either some information on the topological type of the manifold or on the behavior of points at "sufficiently large" distances.

#### Pinched [sectional curvature](https://en.wikipedia.org/wiki/Sectional_curvature)

1.  **[Sphere theorem](https://en.wikipedia.org/wiki/Sphere_theorem).** If *M* is a simply connected compact *n*-dimensional Riemannian manifold with sectional curvature strictly pinched between 1/4 and 1 then *M* is diffeomorphic to a sphere.
2.  **Cheeger's finiteness theorem.** Given constants *C*, *D* and *V*, there are only finitely many (up to diffeomorphism) compact *n*-dimensional Riemannian manifolds with sectional curvature \|*K*\| ≤ *C*, diameter ≤ *D* and volume ≥ *V*.
3.  **[Gromov's almost flat manifolds](https://en.wikipedia.org/wiki/Almost_flat_manifold).** There is an ε<sub>*n*</sub> \> 0 such that if an *n*-dimensional Riemannian manifold has a metric with sectional curvature \|*K*\| ≤ ε<sub>*n*</sub> and diameter ≤ 1 then its finite cover is diffeomorphic to a [nil manifold](https://en.wikipedia.org/wiki/Nil_manifold).

#### Sectional curvature bounded below

1.  **Cheeger–Gromoll's [soul theorem](https://en.wikipedia.org/wiki/Soul_theorem).** If *M* is a non-compact complete non-negatively curved *n*-dimensional Riemannian manifold, then *M* contains a compact, totally geodesic submanifold *S* such that *M* is diffeomorphic to the normal bundle of *S* (*S* is called the **soul** of *M*.) In particular, if *M* has strictly positive curvature everywhere, then it is [diffeomorphic](https://en.wikipedia.org/wiki/Diffeomorphic) to **R**<sup>*n*</sup>. [G. Perelman](https://en.wikipedia.org/wiki/G._Perelman) in 1994 gave an astonishingly elegant/short proof of the Soul Conjecture: *M* is diffeomorphic to **R**<sup>*n*</sup> if it has positive curvature at only one point.
2.  **Gromov's Betti number theorem.** There is a constant *C* = *C*(*n*) such that if *M* is a compact connected *n*-dimensional Riemannian manifold with positive sectional curvature then the sum of its [Betti numbers](https://en.wikipedia.org/wiki/Betti_number) is at most *C*.
3.  **Grove–Petersen's finiteness theorem.** Given constants *C*, *D* and *V*, there are only finitely many homotopy types of compact *n*-dimensional Riemannian manifolds with sectional curvature *K* ≥ *C*, diameter ≤ *D* and volume ≥ *V*.

#### Sectional curvature bounded above

1.  The **[Cartan–Hadamard theorem](https://en.wikipedia.org/wiki/Cartan%E2%80%93Hadamard_theorem)** states that a complete [simply connected](https://en.wikipedia.org/wiki/Simply_connected) Riemannian manifold *M* with nonpositive sectional curvature is [diffeomorphic](https://en.wikipedia.org/wiki/Diffeomorphic) to the [Euclidean space](https://en.wikipedia.org/wiki/Euclidean_space) **R**<sup>*n*</sup> with *n* = dim *M* via the [exponential map](https://en.wikipedia.org/wiki/Exponential_map_(Riemannian_geometry) "Exponential map (Riemannian geometry)") at any point. It implies that any two points of a simply connected complete Riemannian manifold with nonpositive sectional curvature are joined by a unique geodesic.
2.  The [geodesic flow](https://en.wikipedia.org/wiki/Geodesic_flow) of any compact Riemannian manifold with negative sectional curvature is [ergodic](https://en.wikipedia.org/wiki/Ergodic).
3.  If *M* is a complete Riemannian manifold with sectional curvature bounded above by a strictly negative constant *k* then it is a [CAT(*k*) space](https://en.wikipedia.org/wiki/CAT(k)_space "CAT(k) space"). Consequently, its [fundamental group](https://en.wikipedia.org/wiki/Fundamental_group) Γ = π<sub>1</sub>(*M*) is [Gromov hyperbolic](https://en.wikipedia.org/wiki/Hyperbolic_group). This has many implications for the structure of the fundamental group:

- it is [finitely presented](https://en.wikipedia.org/wiki/Finitely_presented_group);
- the [word problem](https://en.wikipedia.org/wiki/Word_problem_for_groups) for Γ has a positive solution;
- the group Γ has finite virtual [cohomological dimension](https://en.wikipedia.org/wiki/Cohomological_dimension);
- it contains only finitely many [conjugacy classes](https://en.wikipedia.org/wiki/Conjugacy_class) of [elements of finite order](https://en.wikipedia.org/wiki/Torsion_(algebra) "Torsion (algebra)");
- the [abelian](https://en.wikipedia.org/wiki/Abelian_group) subgroups of Γ are [virtually cyclic](https://en.wikipedia.org/wiki/Virtually_cyclic_group), so that it does not contain a subgroup isomorphic to **Z**×**Z**.

#### Ricci curvature bounded below

1.  **[Myers theorem](https://en.wikipedia.org/wiki/Myers_theorem).** If a complete Riemannian manifold has positive Ricci curvature then its [fundamental group](https://en.wikipedia.org/wiki/Fundamental_group) is finite.
2.  **[Bochner's formula](https://en.wikipedia.org/wiki/Bochner%27s_formula).** If a compact Riemannian *n*-manifold has non-negative Ricci curvature, then its first Betti number is at most *n*, with equality if and only if the Riemannian manifold is a flat torus.
3.  **[Splitting theorem](https://en.wikipedia.org/wiki/Splitting_theorem).** If a complete *n*-dimensional Riemannian manifold has nonnegative Ricci curvature and a straight line (i.e. a geodesic that minimizes distance on each interval) then it is isometric to a direct product of the real line and a complete (*n*-1)-dimensional Riemannian manifold that has nonnegative Ricci curvature.
4.  **[Bishop–Gromov inequality](https://en.wikipedia.org/wiki/Bishop%E2%80%93Gromov_inequality).** The volume of a metric ball of radius *r* in a complete *n*-dimensional Riemannian manifold with positive Ricci curvature has volume at most that of the volume of a ball of the same radius *r* in Euclidean space.
5.  **[Gromov's compactness theorem](https://en.wikipedia.org/wiki/Gromov%27s_compactness_theorem_(geometry) "Gromov's compactness theorem (geometry)").** The set of all Riemannian manifolds with positive Ricci curvature and diameter at most *D* is [pre-compact](https://en.wikipedia.org/wiki/Metric_space) in the [Gromov-Hausdorff metric](https://en.wikipedia.org/wiki/Gromov-Hausdorff_convergence).

#### Negative Ricci curvature

1.  The [isometry group](https://en.wikipedia.org/wiki/Isometry) of a compact Riemannian manifold with negative Ricci curvature is [discrete](https://en.wikipedia.org/wiki/Discrete_group).
2.  Any smooth manifold of dimension *n* ≥ 3 admits a Riemannian metric with negative Ricci curvature. (*This is not true for surfaces*.)

#### Positive scalar curvature

1.  The *n*-dimensional torus does not admit a metric with positive scalar curvature.
2.  If the [injectivity radius](https://en.wikipedia.org/wiki/Glossary_of_Riemannian_and_metric_geometry) of a compact *n*-dimensional Riemannian manifold is ≥ π then the average scalar curvature is at most *n*(*n*-1).

## Notes

1.  [maths.tcd.ie](http://www.maths.tcd.ie/pub/HistMath/People/Riemann/Geom/)
2.  [Kleinert, Hagen](https://en.wikipedia.org/wiki/Hagen_Kleinert) (1989), [Gauge Fields in Condensed Matter Vol II](https://web.archive.org/web/20220822144725/http://users.physik.fu-berlin.de/~kleinert/kleiner_reb1/contents2.html), World Scientific, pp. 743–1440, archived from [the original](http://users.physik.fu-berlin.de/~kleinert/kleiner_reb1/contents2.html) on 2022-08-22, retrieved 2011-07-17
3.  [Kleinert, Hagen](https://en.wikipedia.org/wiki/Hagen_Kleinert) (2008), [Multivalued Fields in Condensed Matter, Electromagnetism, and Gravitation](https://web.archive.org/web/20220120205940/http://users.physik.fu-berlin.de/~kleinert/b11/psfiles/mvf.pdf) (PDF), World Scientific, pp. 1–496, [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2008mfcm.book.....K](https://ui.adsabs.harvard.edu/abs/2008mfcm.book.....K), archived from [the original](http://users.physik.fu-berlin.de/~kleinert/b11/psfiles/mvf.pdf) (PDF) on 2022-01-20, retrieved 2011-07-17
4.  Joachim Lohkamp has shown (Annals of Mathematics, 1994) that any manifold of dimension greater than two admits a metric of negative Ricci curvature.

## References

Books

- [Berger, Marcel](https://en.wikipedia.org/wiki/Marcel_Berger) (2000), [Riemannian Geometry During the Second Half of the Twentieth Century](https://archive.org/details/riemanniangeomet0000berg), University Lecture Series, vol. 17, Rhode Island: American Mathematical Society, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-8218-2052-4](https://en.wikipedia.org/wiki/Special:BookSources/0-8218-2052-4). *(Provides a historical review and survey, including hundreds of references.)*
- [Cheeger, Jeff](https://en.wikipedia.org/wiki/Jeff_Cheeger); Ebin, David G. (2008), *Comparison theorems in Riemannian geometry*, Providence, RI: AMS Chelsea Publishing; Revised reprint of the 1975 original.
- Gallot, Sylvestre; [Hulin, Dominique](https://en.wikipedia.org/wiki/Dominique_Hulin); Lafontaine, Jacques (2004), *Riemannian geometry*, Universitext (3rd ed.), Berlin: Springer-Verlag.
- Jost, Jürgen (2002), *Riemannian Geometry and Geometric Analysis*, Berlin: Springer-Verlag, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [3-540-42627-2](https://en.wikipedia.org/wiki/Special:BookSources/3-540-42627-2).
- Petersen, Peter (2006), *Riemannian Geometry*, Berlin: Springer-Verlag, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-98212-4](https://en.wikipedia.org/wiki/Special:BookSources/0-387-98212-4)

- From Riemann to Differential Geometry and Relativity (Lizhen Ji, Athanase Papadopoulos, and Sumio Yamada, Eds.) Springer, 2017, XXXIV, 647 p. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-319-60039-0](https://en.wikipedia.org/wiki/Special:BookSources/978-3-319-60039-0)

Papers

- [Brendle, Simon](https://en.wikipedia.org/wiki/Simon_Brendle); [Schoen, Richard M.](https://en.wikipedia.org/wiki/Richard_Schoen) (2008), "Classification of manifolds with weakly 1/4-pinched curvatures", *Acta Math*, **200**: 1–13, [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[0705.3963](https://arxiv.org/abs/0705.3963), [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2007arXiv0705.3963B](https://ui.adsabs.harvard.edu/abs/2007arXiv0705.3963B), [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s11511-008-0022-7](https://doi.org/10.1007%2Fs11511-008-0022-7), [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [15463483](https://api.semanticscholar.org/CorpusID:15463483)

## External links

- [Riemannian geometry](http://www.encyclopediaofmath.org/) by V. A. Toponogov at the [Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)
- [Weisstein, Eric W.](https://en.wikipedia.org/wiki/Eric_W._Weisstein), ["Riemannian Geometry"](https://mathworld.wolfram.com/RiemannianGeometry.html), *[MathWorld](https://en.wikipedia.org/wiki/MathWorld)*
