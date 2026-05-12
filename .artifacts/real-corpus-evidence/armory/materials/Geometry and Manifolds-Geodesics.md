[[geometry-manifolds.base]]

> Source: [Geodesic](https://en.wikipedia.org/wiki/Geodesic)
> License: Wikipedia content is available under CC BY-SA 4.0.

![[media/9236693512864ed92ae9d65d0d420f143ec2b160.png]]
[Klein quartic](https://en.wikipedia.org/wiki/Klein_quartic) with 28 geodesics (marked by 7 colors and 4 patterns)

In [geometry](https://en.wikipedia.org/wiki/Geometry), a **geodesic** ([/ˌdʒiː.əˈdɛsɪk, -oʊ-, -ˈdiːsɪk, -zɪk/](https://en.wikipedia.org/wiki/Help:IPA/English)) is a [curve](https://en.wikipedia.org/wiki/Curve) representing in some sense the locally shortest path ([arc](https://en.wikipedia.org/wiki/Arc_(geometry))) between two points in a [surface](https://en.wikipedia.org/wiki/Differential_geometry_of_surfaces), or more generally in a [Riemannian manifold](https://en.wikipedia.org/wiki/Riemannian_manifold). The term also has meaning in any [differentiable manifold](https://en.wikipedia.org/wiki/Differentiable_manifold) with a [connection](https://en.wikipedia.org/wiki/Connection_(mathematics) "Connection (mathematics)"). It is a generalization of the notion of a "[straight line](https://en.wikipedia.org/wiki/Line_(geometry) "Line (geometry)")".

The noun *[geodesic](https://en.wiktionary.org/wiki/geodesic)* and the adjective *[geodetic](https://en.wiktionary.org/wiki/geodetic)* come from *[geodesy](https://en.wikipedia.org/wiki/Geodesy)*, the science of measuring the size and shape of [Earth](https://en.wikipedia.org/wiki/Earth), though many of the underlying principles can be applied to any [ellipsoidal](https://en.wikipedia.org/wiki/Ellipsoidal_geodesic) geometry. In the original sense, a geodesic was the shortest route between two points on the Earth's [surface](https://en.wikipedia.org/wiki/Planetary_surface). For a [spherical Earth](https://en.wikipedia.org/wiki/Spherical_Earth), it is a [segment](https://en.wikipedia.org/wiki/Line_segment) of a [great circle](https://en.wikipedia.org/wiki/Great_circle) (see also [great-circle distance](https://en.wikipedia.org/wiki/Great-circle_distance)). The term has since been generalized to more abstract mathematical spaces; for example, in [graph theory](https://en.wikipedia.org/wiki/Graph_theory), one might consider a [geodesic](https://en.wikipedia.org/wiki/Distance_(graph_theory) "Distance (graph theory)") between two [vertices](https://en.wikipedia.org/wiki/Vertex_(graph_theory) "Vertex (graph theory)")/nodes of a [graph](https://en.wikipedia.org/wiki/Graph_(discrete_mathematics) "Graph (discrete mathematics)").

In a [Riemannian manifold](https://en.wikipedia.org/wiki/Riemannian_manifold) or submanifold, geodesics are characterised by the property of having vanishing [geodesic curvature](https://en.wikipedia.org/wiki/Geodesic_curvature). More generally, in the presence of an [affine connection](https://en.wikipedia.org/wiki/Affine_connection), a geodesic is defined to be a curve whose [[Tangent Space|tangent vectors]] remain parallel if they are [transported](https://en.wikipedia.org/wiki/Parallel_transport) along it. Applying this to the [Levi-Civita connection](https://en.wikipedia.org/wiki/Levi-Civita_connection) of a [Riemannian metric](https://en.wikipedia.org/wiki/Riemannian_metric) recovers the previous notion.

Geodesics are of particular importance in [general relativity](https://en.wikipedia.org/wiki/General_relativity). Timelike [geodesics in general relativity](https://en.wikipedia.org/wiki/Geodesics_in_general_relativity) describe the motion of [free falling](https://en.wikipedia.org/wiki/Free_fall) [test particles](https://en.wikipedia.org/wiki/Test_particles).

## Introduction

A locally shortest path between two given points in a curved space, assumed to be a [Riemannian manifold](https://en.wikipedia.org/wiki/Riemannian_manifold), can be defined by using the [equation](https://en.wikipedia.org/wiki/Equation) for the [length](https://en.wikipedia.org/wiki/Arc_length) of a [curve](https://en.wikipedia.org/wiki/Curve) (a function *f* from an [open interval](https://en.wikipedia.org/wiki/Open_interval) of **[R](https://en.wikipedia.org/wiki/Real_number_line)** to the space), and then minimizing this length between the points using the [calculus of variations](https://en.wikipedia.org/wiki/Calculus_of_variations). This has some minor technical problems because there is an infinite-dimensional space of different ways to parameterize the shortest path. It is simpler to restrict the set of curves to those that are parameterized "with constant speed" 1, meaning that the distance from *f*(*s*) to *f*(*t*) along the curve equals \|*s*−*t*\|. Equivalently, a different quantity may be used, termed the energy of the curve; minimizing the energy leads to the same equations for a geodesic (here "constant velocity" is a consequence of minimization).<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup> Intuitively, one can understand this second formulation by noting that an [elastic band](https://en.wikipedia.org/wiki/Elastic_band) stretched between two points will contract its width, and in so doing will minimize its energy. The resulting shape of the band is a geodesic.

It is possible that several different curves between two points minimize the distance, as is the case for two diametrically opposite points on a sphere. In such a case, any of these curves is a geodesic.

A contiguous segment of a geodesic is again a geodesic.

In general, geodesics are not the same as "shortest curves" between two points, though the two concepts are closely related. The difference is that geodesics are only *locally* the shortest distance between points, and are parameterized with "constant speed". Going the "long way round" on a [great circle](https://en.wikipedia.org/wiki/Great_circle) between two points on a sphere is a geodesic but not the shortest path between the points. The map $t\to t^{2}$ from the unit interval on the real number line to itself gives the shortest path between 0 and 1, but is not a geodesic because the velocity of the corresponding motion of a point is not constant.

Geodesics are commonly seen in the study of [[Riemannian Geometry]] and more generally [metric geometry](https://en.wikipedia.org/wiki/Metric_geometry). In [general relativity](https://en.wikipedia.org/wiki/General_relativity), geodesics in [spacetime](https://en.wikipedia.org/wiki/Spacetime) describe the motion of [point particles](https://en.wikipedia.org/wiki/Point_particle) under the influence of gravity alone. In particular, the path taken by a falling rock, an orbiting [satellite](https://en.wikipedia.org/wiki/Satellite), or the shape of a [planetary orbit](https://en.wikipedia.org/wiki/Planetary_orbit) are all geodesics in curved spacetime. More generally, the topic of [sub-Riemannian geometry](https://en.wikipedia.org/wiki/Sub-Riemannian_geometry) deals with the paths that objects may take when they are not free, and their movement is constrained in various ways.

This article presents the mathematical formalism involved in defining, finding, and proving the existence of geodesics, in the case of [Riemannian manifolds](https://en.wikipedia.org/wiki/Riemannian_manifold). The article [Levi-Civita connection](https://en.wikipedia.org/wiki/Levi-Civita_connection) discusses the more general case of a [pseudo-Riemannian manifold](https://en.wikipedia.org/wiki/Pseudo-Riemannian_manifold) and [geodesic (general relativity)](https://en.wikipedia.org/wiki/Geodesic_(general_relativity)) discusses the special case of general relativity in greater detail.

### Examples

![[media/063f129fd20426deef45572a180eeae19f7e3cca.png]]
A [geodesic on a triaxial ellipsoid](https://en.wikipedia.org/wiki/Geodesics_on_a_triaxial_ellipsoid).

![[media/b4abe166084a89abba56b4e051177bd4402a22e4.gif]]
If an insect is placed on a surface and continually walks "forward", by definition it will trace out a geodesic.

The most familiar examples are the straight lines in [Euclidean geometry](https://en.wikipedia.org/wiki/Euclidean_geometry). On a [sphere](https://en.wikipedia.org/wiki/Sphere), the images of geodesics are the [great circles](https://en.wikipedia.org/wiki/Great_circle). The shortest path from point *A* to point *B* on a sphere is given by the shorter [arc](https://en.wikipedia.org/wiki/Arc_(geometry)) of the great circle passing through *A* and *B*. If *A* and *B* are [antipodal points](https://en.wikipedia.org/wiki/Antipodal_point), then there are *infinitely many* shortest paths between them. [Geodesics on an ellipsoid](https://en.wikipedia.org/wiki/Geodesics_on_an_ellipsoid) behave in a more complicated way than on a sphere; in particular, they are not closed in general (see figure).

### Triangles

![[media/4197bbc7fa543123d4d4fbd78150f143bcc7132b.png]]
A geodesic triangle on the sphere.

A **geodesic triangle** is formed by the geodesics joining each pair out of three points on a given surface. On the sphere, the geodesics are [great circle](https://en.wikipedia.org/wiki/Great_circle) arcs, forming a [spherical triangle](https://en.wikipedia.org/wiki/Spherical_triangle).

![[media/dff89bc9e87a5265c2a0192012917ada76f03b74.jpg]]
Geodesic triangles in spaces of positive (top), negative (middle) and zero (bottom) curvature.

## Metric geometry

In [metric geometry](https://en.wikipedia.org/wiki/Metric_geometry), a geodesic is a curve which is everywhere [locally](https://en.wikipedia.org/wiki/Locally) a [distance](https://en.wikipedia.org/wiki/Distance) minimizer. More precisely, a [curve](https://en.wikipedia.org/wiki/Curve) *γ* : *I* → *M* from an interval *I* of the reals to the [metric space](https://en.wikipedia.org/wiki/Metric_space) *M* is a **geodesic** if there is a [constant](https://en.wikipedia.org/wiki/Mathematical_constant) *v* ≥ 0 such that for any *t* ∈ *I* there is a neighborhood *J* of *t* in *I* such that for any *t*<sub>1</sub>, *t*<sub>2</sub> ∈ *J* we have

$d(\gamma (t_{1}),\gamma (t_{2}))=v\left|t_{1}-t_{2}\right|.$

This generalizes the notion of geodesic for Riemannian manifolds. However, in metric geometry the geodesic considered is often equipped with [natural parameterization](https://en.wikipedia.org/wiki/Curve#Lengths_of_curves), i.e. in the above identity *v* = 1 and

$d(\gamma (t_{1}),\gamma (t_{2}))=\left|t_{1}-t_{2}\right|.$

If the last equality is satisfied for all *t*<sub>1</sub>, *t*<sub>2</sub> ∈ *I*, the geodesic is called a **minimizing geodesic** or **shortest path**.

In general, a metric space may have no geodesics, except constant curves. At the other extreme, any two points in a [length metric space](https://en.wikipedia.org/wiki/Length_metric_space) are joined by a minimizing sequence of [rectifiable paths](https://en.wikipedia.org/wiki/Rectifiable_path), although this minimizing sequence need not converge to a geodesic. The [metric Hopf-Rinow theorem](https://en.wikipedia.org/wiki/Hopf%E2%80%93Rinow_theorem#Variations_and_generalizations) provides situations where a length space is automatically a geodesic space.

Common examples of geodesic metric spaces that are often not manifolds include [metric graphs](https://en.wikipedia.org/wiki/Metric_graph), (locally compact) metric [polyhedral complexes](https://en.wikipedia.org/wiki/Polyhedral_complex), infinite-dimensional [pre-Hilbert spaces](https://en.wikipedia.org/wiki/Pre-Hilbert_space), and [real trees](https://en.wikipedia.org/wiki/Real_tree).

## Riemannian geometry

In a [Riemannian manifold](https://en.wikipedia.org/wiki/Riemannian_manifold) $M$ with [metric tensor](https://en.wikipedia.org/wiki/Metric_tensor) $g$, the length $L$ of a continuously differentiable curve $\gamma :[a,b]\to M$ is defined by

$L(\gamma )=\int _{a}^{b}{\sqrt {g_{\gamma (t)}({\dot {\gamma }}(t),{\dot {\gamma }}(t))}}\,dt.$

The distance $d(p,q)$ between two points $p$ and $q$ of $M$ is defined as the [infimum](https://en.wikipedia.org/wiki/Infimum) of the length taken over all continuous, piecewise continuously differentiable curves $\gamma :[a,b]\to M$ such that $\gamma (a)=p$ and $\gamma (b)=q$. In Riemannian geometry, all geodesics are locally distance-minimizing paths, but the converse is not true. In fact, only paths that are both locally distance minimizing and parameterized proportionately to arc-length are geodesics.

Another equivalent way of defining geodesics on a Riemannian manifold, is to define them as the minima of the following [action](https://en.wikipedia.org/wiki/Action_(physics) "Action (physics)") or [energy functional](https://en.wikipedia.org/wiki/Energy_functional)

$E(\gamma )={\frac {1}{2}}\int _{a}^{b}g_{\gamma (t)}({\dot {\gamma }}(t),{\dot {\gamma }}(t))\,dt.$

All minima of $E$ are also minima of $L$, but $L$ is a bigger set since paths that are minima of $L$ can be arbitrarily re-parameterized (without changing their length), while minima of $E$ cannot. For a piecewise $C^{1}$ curve (more generally, a $W^{1,2}$ curve), the [Cauchy–Schwarz inequality](https://en.wikipedia.org/wiki/Cauchy%E2%80%93Schwarz_inequality) gives

$L(\gamma )^{2}\leq 2(b-a)E(\gamma )$

with equality if and only if $g(\gamma ',\gamma ')$ is equal to a constant a.e.; the path should be travelled at constant speed. It happens that minimizers of $E(\gamma )$ also minimize $L(\gamma )$, because they turn out to be affinely parameterized, and the inequality is an equality. The usefulness of this approach is that the problem of seeking minimizers of $E$ is a more robust variational problem. Indeed, $E(\gamma )$ is a "convex function" of $\gamma$, so that within each isotopy class of "reasonable functions", one ought to expect existence, uniqueness, and regularity of minimizers. In contrast, "minimizers" of the functional $L(\gamma )$ are generally not very regular, because arbitrary reparameterizations are allowed.

The [Euler–Lagrange equations](https://en.wikipedia.org/wiki/Euler%E2%80%93Lagrange_equation) of motion for the functional $E$ are then given in local coordinates by

${\frac {d^{2}x^{\lambda }}{dt^{2}}}+\Gamma _{\mu \nu }^{\lambda }{\frac {dx^{\mu }}{dt}}{\frac {dx^{\nu }}{dt}}=0,$

where $\Gamma _{\mu \nu }^{\lambda }$ are the [Christoffel symbols](https://en.wikipedia.org/wiki/Christoffel_symbols) of the metric. This is the **geodesic equation**, discussed [below](#Affine_geodesics).

### Calculus of variations

Techniques of the classical [calculus of variations](https://en.wikipedia.org/wiki/Calculus_of_variations) can be applied to examine the energy functional $E$. The [first variation](https://en.wikipedia.org/wiki/First_variation) of energy is defined in local coordinates by

$\delta E(\gamma )(\varphi )=\left.{\frac {\partial }{\partial t}}\right|_{t=0}E(\gamma +t\varphi ).$

The [critical points](https://en.wikipedia.org/wiki/Critical_point_(mathematics) "Critical point (mathematics)") of the first variation are precisely the geodesics. The [second variation](https://en.wikipedia.org/wiki/Second_variation) is defined by

$\delta ^{2}E(\gamma )(\varphi ,\psi )=\left.{\frac {\partial ^{2}}{\partial s\,\partial t}}\right|_{s=t=0}E(\gamma +t\varphi +s\psi ).$

In an appropriate sense, zeros of the second variation along a geodesic $\gamma$ arise along [Jacobi fields](https://en.wikipedia.org/wiki/Jacobi_field). Jacobi fields are thus regarded as variations through geodesics.

By applying variational techniques from [classical mechanics](https://en.wikipedia.org/wiki/Classical_mechanics), one can also regard [geodesics as Hamiltonian flows](https://en.wikipedia.org/wiki/Geodesics_as_Hamiltonian_flows). They are solutions of the associated [Hamilton equations](https://en.wikipedia.org/wiki/Hamilton_equation), with [(pseudo-)Riemannian metric](https://en.wikipedia.org/wiki/Pseudo_Riemannian_metric) taken as [Hamiltonian](https://en.wikipedia.org/wiki/Hamiltonian_mechanics).

## Affine geodesics

A **geodesic** on a [smooth manifold](https://en.wikipedia.org/wiki/Differentiable_manifold) $M$ with an [affine connection](https://en.wikipedia.org/wiki/Affine_connection) $\nabla$ is defined as a [curve](https://en.wikipedia.org/wiki/Curve) $\gamma (t)$ such that [parallel transport](https://en.wikipedia.org/wiki/Parallel_transport) along the curve preserves the tangent vector to the curve, so

|  |  |  |
|----|----|----|
| $\nabla _{\dot {\gamma }}{\dot {\gamma }}=0$ |  | 1 |

at each point along the curve, where ${\dot {\gamma }}$ is the derivative with respect to $t$. More precisely, in order to define the covariant derivative of ${\dot {\gamma }}$ it is necessary first to extend ${\dot {\gamma }}$ to a continuously differentiable [vector field](https://en.wikipedia.org/wiki/Vector_field) in an [open set](https://en.wikipedia.org/wiki/Open_set). However, the resulting value of (**[1](#math_1)**) is independent of the choice of extension.

Using [local coordinates](https://en.wikipedia.org/wiki/Local_coordinates) on $M$, we can write the **geodesic equation** (using the [summation convention](https://en.wikipedia.org/wiki/Summation_convention)) as

${\frac {d^{2}\gamma ^{\lambda }}{dt^{2}}}+\Gamma _{\mu \nu }^{\lambda }{\frac {d\gamma ^{\mu }}{dt}}{\frac {d\gamma ^{\nu }}{dt}}=0\ ,$

where $\gamma ^{\mu }=x^{\mu }\circ \gamma (t)$ are the coordinates of the curve $\gamma (t)$ and $\Gamma _{\mu \nu }^{\lambda }$ are the [Christoffel symbols](https://en.wikipedia.org/wiki/Christoffel_symbol) of the connection $\nabla$. This is an [ordinary differential equation](https://en.wikipedia.org/wiki/Ordinary_differential_equation) for the coordinates. It has a unique solution, given an initial position and an initial velocity. Therefore, from the point of view of [classical mechanics](https://en.wikipedia.org/wiki/Classical_mechanics), geodesics can be thought of as trajectories of [free particles](https://en.wikipedia.org/wiki/Free_particle) in a manifold. Indeed, the equation $\nabla _{\dot {\gamma }}{\dot {\gamma }}=0$ means that the [acceleration vector](https://en.wikipedia.org/wiki/Acceleration_(differential_geometry) "Acceleration (differential geometry)") of the curve has no components in the direction of the surface (and therefore it is perpendicular to the tangent plane of the surface at each point of the curve). So, the motion is completely determined by the bending of the surface. This is also the idea of general relativity where particles move on geodesics and the bending is caused by gravity.

### Existence and uniqueness

The *local existence and uniqueness theorem* for geodesics states that geodesics on a smooth manifold with an [affine connection](https://en.wikipedia.org/wiki/Affine_connection) exist, and are unique. More precisely:

For any point *p* in *M* and for any vector *V* in *T<sub>p</sub>M* (the [[Tangent Space]] to *M* at *p*) there exists a unique geodesic $\gamma \,$ : *I* → *M* such that

$\gamma (0)=p\,$ and

${\dot {\gamma }}(0)=V,$

where *I* is a maximal [open interval](https://en.wikipedia.org/wiki/Open_interval) in **R** containing 0.

The proof of this theorem follows from the theory of [ordinary differential equations](https://en.wikipedia.org/wiki/Ordinary_differential_equation), by noticing that the geodesic equation is a second-order ODE. Existence and uniqueness then follow from the [Picard–Lindelöf theorem](https://en.wikipedia.org/wiki/Picard%E2%80%93Lindel%C3%B6f_theorem) for the solutions of ODEs with prescribed initial conditions. γ depends [smoothly](https://en.wikipedia.org/wiki/Smooth_function) on both *p* and *V*.

In general, *I* may not be all of **R** as for example for an open disc in **R**<sup>2</sup>. Any γ extends to all of ℝ if and only if M is [geodesically complete](https://en.wikipedia.org/wiki/Geodesic_manifold).

### Geodesic flow

**Geodesic [flow](https://en.wikipedia.org/wiki/Flow_(mathematics) "Flow (mathematics)")** is a local **R**-[action](https://en.wikipedia.org/wiki/Group_action_(mathematics)) on the [tangent bundle](https://en.wikipedia.org/wiki/Tangent_bundle) *TM* of a manifold *M* defined in the following way

$G^{t}(V)={\dot {\gamma }}_{V}(t)$

where *t* ∈ **R**, *V* ∈ *TM* and $\gamma _{V}$ denotes the geodesic with initial data ${\dot {\gamma }}_{V}(0)=V$. Thus, *$G^{t}(V)=\exp(tV)$* is the [exponential map](https://en.wikipedia.org/wiki/Exponential_map_(Riemannian_geometry) "Exponential map (Riemannian geometry)") of the vector *tV*. A closed orbit of the geodesic flow corresponds to a [closed geodesic](https://en.wikipedia.org/wiki/Closed_geodesic) on *M*.

On a (pseudo-)Riemannian manifold, the geodesic flow is identified with a [Hamiltonian flow](https://en.wikipedia.org/wiki/Hamiltonian_flow) on the cotangent bundle. The [Hamiltonian](https://en.wikipedia.org/wiki/Hamiltonian_mechanics) is then given by the inverse of the (pseudo-)Riemannian metric, evaluated against the [canonical one-form](https://en.wikipedia.org/wiki/Canonical_one-form). In particular the flow preserves the (pseudo-)Riemannian metric $g$, i.e.

$g(G^{t}(V),G^{t}(V))=g(V,V).\,$

In particular, when *V* is a unit vector, $\gamma _{V}$ remains unit speed throughout, so the geodesic flow is tangent to the [unit tangent bundle](https://en.wikipedia.org/wiki/Unit_tangent_bundle). [Liouville's theorem](https://en.wikipedia.org/wiki/Liouville%27s_theorem_(Hamiltonian) "Liouville's theorem (Hamiltonian)") implies invariance of a kinematic measure on the unit tangent bundle.

### Geodesic spray

The geodesic flow defines a family of curves in the [tangent bundle](https://en.wikipedia.org/wiki/Tangent_bundle). The derivatives of these curves define a [vector field](https://en.wikipedia.org/wiki/Vector_field) on the [total space](https://en.wikipedia.org/wiki/Total_space) of the tangent bundle, known as the **geodesic [spray](https://en.wikipedia.org/wiki/Spray_(mathematics) "Spray (mathematics)")**.

More precisely, an affine connection gives rise to a splitting of the [double tangent bundle](https://en.wikipedia.org/wiki/Double_tangent_bundle) TT*M* into [horizontal](https://en.wikipedia.org/wiki/Horizontal_bundle) and [vertical bundles](https://en.wikipedia.org/wiki/Vertical_bundle):

$TTM=H\oplus V.$

The double tangent bundle can be visualized as the space of simultaneous changes of both the base point and velocity, without committing to any method to transport velocity across base points.

For any $x\in M,\;v\in T_{x}M$, the vertical fiber $V_{(x,v)}$ is determined by the projection map $\pi :TM\to M$. It consists of all ways to change the velocity $v$ while fixing the base point $x$, and it is essentially a copy of $T_{x}M$ translated from $(x,0)$ to $(x,v)$. The affine connection then selects where $(x,v)$ would land under a change of base point while "fixing" velocity, which spans out the horizontal fiber $H_{(x,v)}$. Conversely, given the split, transporting a vector $v$ along a trajectory $\gamma$ simply means dragging the vector along the horizontal bundle, i.e. lifting the trajectory twice, from $\gamma (t)$ in $M$ to $(\gamma (t),{\dot {\gamma }}(t))$ in $TM$ to $(\gamma (t),v(t),a(t))$ in $H$, with the condition that $d\pi (\gamma (t),v,a(t))=(\gamma (t),{\dot {\gamma }}(t))$.

The geodesic spray is the unique horizontal vector field *W* satisfying

$d\pi W_{(x,v)}=(x,v)$

at each point $x\in M,\;v\in T_{x}M$, here $d\pi :TTM\to TM$denotes the [pushforward (differential)](https://en.wikipedia.org/wiki/Pushforward_(differential) "Pushforward (differential)") along the projection $\pi :TM\to M$. Intuitively, $d\pi$ discards the change to velocity and preserves change to base point.

More generally, the same construction allows one to construct a vector field for any [Ehresmann connection](https://en.wikipedia.org/wiki/Ehresmann_connection) on the tangent bundle. For the resulting vector field to be a spray (on the deleted tangent bundle T*M* \\{0}) it is enough that the connection be equivariant under positive rescalings, that is, it is enough that, if $w\in T_{x}M$ is transported by $\gamma$ to $w'\in T_{x'}M$, then $kw$ must be transported to $kw'$ for any $k>0$. It is not necessary that, if $u\in T_{x}M$ is also transported to $u'\in T_{x'}M$, then $w+u$ must be transported $w'+u'$.

That is, (cf. [Ehresmann connection#Vector bundles and covariant derivatives](https://en.wikipedia.org/wiki/Ehresmann_connection#Vector_bundles_and_covariant_derivatives)) it is enough that the horizontal distribution satisfy

$H_{\lambda X}=d(S_{\lambda })_{X}H_{X}\,$

for every *X* ∈ T*M* \\{0} and λ \> 0. Here *d*(*S*<sub>λ</sub>) is the [pushforward](https://en.wikipedia.org/wiki/Pushforward_(differential) "Pushforward (differential)") along the scalar homothety $S_{\lambda }:X\mapsto \lambda X.$ A particular case of a non-linear connection arising in this manner is that associated to a [Finsler manifold](https://en.wikipedia.org/wiki/Finsler_manifold).

Equivariance under positive rescalings is necessary to ensure that vector transport is well-defined along directed paths, that is, given any parameterization $\gamma :I\to M$ of the curve, and any strictly monotonically increasing "change of timing" $f:\mathbb {R} \to \mathbb {R}$, the new parameterization $\gamma \circ f$ still produces the same vector transport. Without equivariance under positive rescalings, vector transport along a directed path depends on the specific parameterization.

### Affine and projective geodesics

Equation (**[1](#math_1)**) is invariant under affine reparameterizations; that is, parameterizations of the form

$t\mapsto at+b$

where *a* and *b* are constant real numbers. Thus apart from specifying a certain class of embedded curves, the geodesic equation also determines a preferred class of parameterizations on each of the curves. Accordingly, solutions of (**[1](#math_1)**) are called geodesics with **affine parameter**.

An affine connection is *determined by* its family of affinely parameterized geodesics, up to [torsion](https://en.wikipedia.org/wiki/Torsion_tensor) (, Chapter 6, Addendum I). The torsion itself does not, in fact, affect the family of geodesics, since the geodesic equation depends only on the symmetric part of the connection. More precisely, if $\nabla ,{\bar {\nabla }}$ are two connections such that the difference tensor

$D(X,Y)=\nabla _{X}Y-{\bar {\nabla }}_{X}Y$

is [skew-symmetric](https://en.wikipedia.org/wiki/Skew-symmetric_matrix), then $\nabla$ and ${\bar {\nabla }}$ have the same geodesics, with the same affine parameterizations. Furthermore, there is a unique connection having the same geodesics as $\nabla$, but with vanishing torsion.

Geodesics without a particular parameterization are described by a [projective connection](https://en.wikipedia.org/wiki/Projective_connection).

## Computational methods

Efficient solvers for the minimal geodesic problem on surfaces have been proposed by Mitchell, Kimmel, Crane, and others.

## Ribbon test

A ribbon "test" is a way of finding a geodesic on a physical surface. The idea is to fit a bit of paper around a straight line (a ribbon) onto a curved surface as closely as possible without stretching or squishing the ribbon (without changing its internal geometry).

For example, when a ribbon is wound as a ring around a cone, the ribbon would not lie on the cone's surface but stick out, so that circle is not a geodesic on the cone. If the ribbon is adjusted so that all its parts touch the cone's surface, it would give an approximation to a geodesic.

Mathematically the ribbon test can be formulated as finding a mapping $f:N(\ell )\to S$ of a [neighborhood](https://en.wikipedia.org/wiki/Neighborhood_(mathematics)) $N$ of a line $\ell$ in a plane into a surface $S$ so that the mapping $f$ "doesn't change the distances around $\ell$ by much"; that is, at the distance $\varepsilon$ from $l$ we have $g_{N}-f^{*}(g_{S})=O(\varepsilon ^{2})$ where $g_{N}$ and $g_{S}$ are [metrics](https://en.wikipedia.org/wiki/Metric_tensor) on $N$ and $S$.

## Examples of applications

While geometric in nature, the idea of a shortest path is so general that it easily finds extensive use in nearly all sciences, and in some other disciplines as well.

### Topology and geometric group theory

- In a surface with negative [Euler characteristic](https://en.wikipedia.org/wiki/Euler_characteristic), any (free) homotopy class determines a unique (closed) geodesic for a [hyperbolic](https://en.wikipedia.org/wiki/Hyperbolic_surface) metric. These geodesics contribute significantly to the geometric understanding of the action of [mapping classes](https://en.wikipedia.org/wiki/Mapping_class_group_of_a_surface).
- [Geodesic metric spaces](https://en.wikipedia.org/wiki/Geodesic_metric_space) and [length spaces](https://en.wikipedia.org/wiki/Length_space) behave particularly well with isometric [group actions](https://en.wikipedia.org/wiki/Group_action) ([Švarc-Milnor lemma](https://en.wikipedia.org/wiki/%C5%A0varc%E2%80%93Milnor_lemma), [Hopf-Rinow theorem](https://en.wikipedia.org/wiki/Hopf%E2%80%93Rinow_theorem#Variations_and_generalizations), [Morse lemma](https://en.wikipedia.org/wiki/Quasi-isometry#Quasigeodesics_and_the_Morse_lemma)...). They are often an adequate framework for generalizing results from Riemannian geometry to constructions that reflect the geometry of a group. For instance, [Gromov-hyperbolicity](https://en.wikipedia.org/wiki/Hyperbolic_metric_space) can be understood in terms of geodesic triangle thinness, and [CAT(0)](https://en.wikipedia.org/wiki/CAT(k)_space "CAT(k) space") can be stated in terms of angles between geodesics.

### Probability, statistics and machine learning

- [Optimal transport](https://en.wikipedia.org/wiki/Optimal_transport) can be understood as the problem of finding geodesic paths in spaces of measures.
- In [information geometry](https://en.wikipedia.org/wiki/Information_geometry), [divergences](https://en.wikipedia.org/wiki/Divergence_(statistics) "Divergence (statistics)") such as the [[Kullback-Leibler Divergence]] play a role analogous to that of a Riemannian metric, allowing analogies for [connections](https://en.wikipedia.org/wiki/Metric_connection) and geodesics.

### Physics

- In [classical mechanics](https://en.wikipedia.org/wiki/Classical_mechanics), [trajectories](https://en.wikipedia.org/wiki/Trajectory) minimize an energy according to the [Hamilton-Jacobi equation](https://en.wikipedia.org/wiki/Hamilton%E2%80%93Jacobi_equation), which can be regarded as a similar idea to geodesics. In some special cases, [the two notions actually coincide](https://en.wikipedia.org/wiki/Geodesics_as_Hamiltonian_flows).
- [Relativity theory](https://en.wikipedia.org/wiki/Theory_of_relativity) models [spacetime](https://en.wikipedia.org/wiki/Spacetime) as a [Lorentzian manifold](https://en.wikipedia.org/wiki/Lorentzian_manifold), where light follows Lorentzian geodesics.

### Chemistry

- In [theoretical](https://en.wikipedia.org/wiki/Theoretical_chemistry) and [computational chemistry](https://en.wikipedia.org/wiki/Computational_chemistry), the intrinsic reaction coordinate of a [potential energy surface](https://en.wikipedia.org/wiki/Potential_energy_surface) (PES) can be calculated as a geodesic between local minima ([intermediates](https://en.wikipedia.org/wiki/Reaction_intermediate)) and saddle points ([transition states](https://en.wikipedia.org/wiki/Transition_state)).
- In [molecular dynamics](https://en.wikipedia.org/wiki/Molecular_dynamics), [protein conformations](https://en.wikipedia.org/wiki/Protein_structure) can be treated as points on a curved manifold, wherein geodesics represent the shortest, least-distorting paths between structures and can help approximate observed transitions and intramolecular interactions.

### Biology

- The study of how the [nervous system](https://en.wikipedia.org/wiki/Nervous_system) optimizes muscular movement may be approached by endowing a [configuration space](https://en.wikipedia.org/wiki/Configuration_space_(physics) "Configuration space (physics)") of the body with a [Riemannian metric](https://en.wikipedia.org/wiki/Riemannian_metric) that measures the effort, so that the problem can be stated in terms of geodesy.
- [Geodesic distance](https://en.wikipedia.org/wiki/Geodesic_distance) is often used to measure the length of paths for signal propagation in neurons.
- The structures of geodesics in large molecules plays a role in the study of [protein folds](https://en.wikipedia.org/wiki/Protein_folds).
- The structure of [compound eyes](https://en.wikipedia.org/wiki/Compound_eye), many parts of which are being held together and supported by a geodesic dome grid on the outside surface of the eye.

### Engineering

Geodesics serve as the basis to calculate:

- geodesic airframes; see [geodesic airframe](https://en.wikipedia.org/wiki/Geodesic_airframe) or [geodetic airframe](https://en.wikipedia.org/wiki/Geodetic_airframe)
- horizontal distances on or near Earth; see [Earth geodesics](https://en.wikipedia.org/wiki/Earth_geodesics)
- mapping images on surfaces, for rendering; see [UV mapping](https://en.wikipedia.org/wiki/UV_mapping)
- robot [motion planning](https://en.wikipedia.org/wiki/Motion_planning) (e.g., when painting car parts); see [Shortest path problem](https://en.wikipedia.org/wiki/Shortest_path_problem)
- geodesic shortest path (GSP) correction over [Poisson surface reconstruction](https://en.wikipedia.org/wiki/Poisson_surface_reconstruction) (e.g. in [digital dentistry](https://en.wikipedia.org/wiki/Digital_dentistry)); without GSP reconstruction often results in self-intersections within the surface

## See also

- [Introduction to the mathematics of general relativity](https://en.wikipedia.org/wiki/Introduction_to_the_mathematics_of_general_relativity)
- [Clairaut's relation](https://en.wikipedia.org/wiki/Clairaut%27s_relation) – Formula in classical differential geometryPages displaying short descriptions of redirect targets
- [Differentiable curve](https://en.wikipedia.org/wiki/Differentiable_curve) – Study of curves from a differential point of view
- [Differential geometry of surfaces](https://en.wikipedia.org/wiki/Differential_geometry_of_surfaces)
- [Geodesic circle](https://en.wikipedia.org/wiki/Geodesic_circle)
- [Hopf–Rinow theorem](https://en.wikipedia.org/wiki/Hopf%E2%80%93Rinow_theorem) – Gives equivalent statements about the geodesic completeness of Riemannian manifolds
- [Intrinsic metric](https://en.wikipedia.org/wiki/Intrinsic_metric) – Concept in geometry/topology
- [Isotropic line](https://en.wikipedia.org/wiki/Isotropic_line) – Line along which a quadratic form applied to any two points' displacement is zero
- [Jacobi field](https://en.wikipedia.org/wiki/Jacobi_field) – Vector field in Riemannian geometry
- [Morse theory](https://en.wikipedia.org/wiki/Morse_theory) – Analyzes the topology of a manifold by studying differentiable functions on that manifold
- [Zoll surface](https://en.wikipedia.org/wiki/Zoll_surface) – Surface homeomorphic to a sphere
- [The spider and the fly problem](https://en.wikipedia.org/wiki/The_spider_and_the_fly_problem) – Recreational geodesics problem

## Notes

1.  For two points on a sphere that are not antipodes, there are two great circle arcs of different lengths connecting them, both of which are geodesics.
2.  ^   For a [pseudo-Riemannian manifold](https://en.wikipedia.org/wiki/Pseudo-Riemannian_manifold), e.g., a [Lorentzian manifold](https://en.wikipedia.org/wiki/Lorentzian_manifold), the definition is more complicated.
3.  The path is a local maximum of the interval *k* rather than a local minimum.

## References

1.  ["geodesic"](https://web.archive.org/web/20200316193343/https://www.lexico.com/definition/geodesic). *[Lexico](https://en.wikipedia.org/wiki/Lexico) UK English Dictionary*. [Oxford University Press](https://en.wikipedia.org/wiki/Oxford_University_Press). Archived from [the original](http://www.lexico.com/definition/geodesic) on 2020-03-16.
2.  ["geodesic"](https://www.merriam-webster.com/dictionary/geodesic). *[Merriam-Webster.com Dictionary](https://en.wikipedia.org/wiki/Merriam-Webster)*. Merriam-Webster. [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [1032680871](https://search.worldcat.org/oclc/1032680871).
3.  Mitchell, J.; Mount, D.; Papadimitriou, C. (1987). ["The Discrete Geodesic Problem"](https://epubs.siam.org/doi/10.1137/0216045). *[SIAM Journal on Computing](https://en.wikipedia.org/wiki/SIAM_Journal_on_Computing)*. **16** (4): 647–668. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/0216045](https://doi.org/10.1137%2F0216045).
4.  Kimmel, R.; Sethian, J. A. (1998). ["Computing Geodesic Paths on Manifolds"](https://www.pnas.org/content/pnas/95/15/8431.full.pdf) (PDF). *[Proceedings of the National Academy of Sciences](https://en.wikipedia.org/wiki/Proceedings_of_the_National_Academy_of_Sciences)*. **95** (15): 8431–8435. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1998PNAS...95.8431K](https://ui.adsabs.harvard.edu/abs/1998PNAS...95.8431K). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1073/pnas.95.15.8431](https://doi.org/10.1073%2Fpnas.95.15.8431). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [21092](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC21092). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [9671694](https://pubmed.ncbi.nlm.nih.gov/9671694). [Archived](https://ghostarchive.org/archive/20221009/https://www.pnas.org/content/pnas/95/15/8431.full.pdf) (PDF) from the original on 2022-10-09.
5.  Crane, K.; Weischedel, C.; Wardetzky, M. (2017). ["The Heat Method for Distance Computation"](https://dl.acm.org/doi/10.1145/3131280). *[Communications of the ACM](https://en.wikipedia.org/wiki/Communications_of_the_ACM)*. **60** (11): 90–99. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1145/3131280](https://doi.org/10.1145%2F3131280). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [7078650](https://api.semanticscholar.org/CorpusID:7078650).
6.  Vsauce (2017-11-02). [Which Way Is Down?](https://www.youtube.com/watch?v=Xc4xYacTu-E). Retrieved 2025-03-26 – via YouTube.
7.  Aguilar-Mogas, Antoni; Giménez, Xavier; Bofill, Josep Maria (2008-03-14). "Finding reaction paths using the potential energy as reaction coordinate". *The Journal of Chemical Physics*. **128** (10): 104102. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1063/1.2834930](https://doi.org/10.1063%2F1.2834930). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0021-9606](https://search.worldcat.org/issn/0021-9606). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [18345872](https://pubmed.ncbi.nlm.nih.gov/18345872).
8.  Hait, Diptarka; Estrada Pabón, Jan D.; Stöhr, Martin; Martínez, Todd J. (2025-11-25). "Locating Ab Initio Transition States via Geodesic Construction on Machine-Learned Potential Energy Surfaces". *Journal of Chemical Theory and Computation*. **21** (22): 11632–11644. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2507.17968](https://arxiv.org/abs/2507.17968). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1021/acs.jctc.5c01221](https://doi.org/10.1021%2Facs.jctc.5c01221). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1549-9626](https://search.worldcat.org/issn/1549-9626). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [41190940](https://pubmed.ncbi.nlm.nih.gov/41190940).
9.  Diepeveen, Willem; Esteve-Yagüe, Carlos; Lellmann, Jan; Öktem, Ozan; Schönlieb, Carola-Bibiane (2024-08-13). ["Riemannian geometry for efficient analysis of protein dynamics data"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11331106). *Proceedings of the National Academy of Sciences of the United States of America*. **121** (33) e2318951121. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1073/pnas.2318951121](https://doi.org/10.1073%2Fpnas.2318951121). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1091-6490](https://search.worldcat.org/issn/1091-6490). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [11331106](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11331106). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [39121160](https://pubmed.ncbi.nlm.nih.gov/39121160).
10. Neilson, Peter D.; Neilson, Megan D.; Bye, Robin T. (2015-12-01). ["A Riemannian geometry theory of human movement: The geodesic synergy hypothesis"](https://www.sciencedirect.com/science/article/abs/pii/S0167945715300208). *Human Movement Science*. **44**: 42–72. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.humov.2015.08.010](https://doi.org/10.1016%2Fj.humov.2015.08.010). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0167-9457](https://search.worldcat.org/issn/0167-9457). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [26302481](https://pubmed.ncbi.nlm.nih.gov/26302481).
11. Beshkov, Kosio; Tiesinga, Paul (2022-02-01). ["Geodesic-based distance reveals nonlinear topological features in neural activity from mouse visual cortex"](https://link.springer.com/article/10.1007/s00422-021-00906-5). *Biological Cybernetics*. **116** (1): 53–68. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s00422-021-00906-5](https://doi.org/10.1007%2Fs00422-021-00906-5). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1432-0770](https://search.worldcat.org/issn/1432-0770). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [34816322](https://pubmed.ncbi.nlm.nih.gov/34816322).
12. Zanotti, Giuseppe; Guerra, Concettina (2003-01-16). ["Is tensegrity a unifying concept of protein folds?"](https://www.sciencedirect.com/science/article/pii/S001457930203853X). *FEBS Letters*. **534** (1): 7–10. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2003FEBSL.534....7Z](https://ui.adsabs.harvard.edu/abs/2003FEBSL.534....7Z). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/S0014-5793(02)03853-X](https://doi.org/10.1016%2FS0014-5793%2802%2903853-X). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0014-5793](https://search.worldcat.org/issn/0014-5793). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [12527354](https://pubmed.ncbi.nlm.nih.gov/12527354).
13. Klassen, Filiz; Kronenburg, Robert (March 10, 2006). *Transportable Environments 3*. Taylor & Francis. p. 175. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-134-28879-3](https://en.wikipedia.org/wiki/Special:BookSources/978-1-134-28879-3).

- [Spivak, Michael](https://en.wikipedia.org/wiki/Michael_Spivak) (1999), *A Comprehensive introduction to differential geometry (Volume 2)*, Houston, TX: Publish or Perish, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-914098-71-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-914098-71-3)

## Further reading

- Adler, Ronald; Bazin, Maurice; Schiffer, Menahem (1975), *Introduction to General Relativity* (2nd ed.), New York: [McGraw-Hill](https://en.wikipedia.org/wiki/McGraw-Hill), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-07-000423-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-07-000423-8). *See chapter 2*.
- [Abraham, Ralph H.](https://en.wikipedia.org/wiki/Ralph_Abraham_(mathematician) "Ralph Abraham (mathematician)"); [Marsden, Jerrold E.](https://en.wikipedia.org/wiki/Jerrold_E._Marsden) (1978), *Foundations of mechanics*, London: Benjamin-Cummings, [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1978fome.book.....A](https://ui.adsabs.harvard.edu/abs/1978fome.book.....A), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8053-0102-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8053-0102-1). *See section 2.7*.
- Jost, Jürgen (2002), *Riemannian Geometry and Geometric Analysis*, Berlin, New York: [Springer-Verlag](https://en.wikipedia.org/wiki/Springer-Verlag), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-42627-1](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-42627-1). *See section 1.4*.
- Kobayashi, Shoshichi; Nomizu, Katsumi (1996), *Foundations of Differential Geometry*, vol. 1 (New ed.), Wiley-Interscience, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-15733-3](https://en.wikipedia.org/wiki/Special:BookSources/0-471-15733-3).
- [Landau, L. D.](https://en.wikipedia.org/wiki/Lev_Landau); [Lifshitz, E. M.](https://en.wikipedia.org/wiki/Evgeny_Lifshitz) (1975), *Classical Theory of Fields*, Oxford: Pergamon, [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1975ctf..book.....L](https://ui.adsabs.harvard.edu/abs/1975ctf..book.....L), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-08-018176-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-08-018176-9). *See section 87*.
- [Misner, Charles W.](https://en.wikipedia.org/wiki/Charles_W._Misner); [Thorne, Kip](https://en.wikipedia.org/wiki/Kip_Thorne); [Wheeler, John Archibald](https://en.wikipedia.org/wiki/John_Archibald_Wheeler) (1973), [*Gravitation*](https://en.wikipedia.org/wiki/Gravitation_(book) "Gravitation (book)"), W. H. Freeman, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-7167-0344-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-7167-0344-0)
- Ortín, Tomás (2004), *Gravity and strings*, [Cambridge University Press](https://en.wikipedia.org/wiki/Cambridge_University_Press), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-82475-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-82475-0). Note especially pages 7 and 10.
- Volkov, Yu.A. (2001) \[1994\], ["Geodesic line"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society).
- [Weinberg, Steven](https://en.wikipedia.org/wiki/Steven_Weinberg) (1972), [Gravitation and Cosmology: Principles and Applications of the General Theory of Relativity](https://archive.org/details/gravitationcosmo00stev_0), New York: [John Wiley & Sons](https://en.wikipedia.org/wiki/John_Wiley_%26_Sons), [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1972gcpa.book.....W](https://ui.adsabs.harvard.edu/abs/1972gcpa.book.....W), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-92567-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-92567-5). *See chapter 3*.

## External links

- [Geodesics Revisited](http://www.cmsim.eu/papers_pdf/january_2012_papers/25_CMSIM_2012_Pokorny_1_281-298.pdf) — Introduction to geodesics including two ways of derivation of the equation of geodesic with applications in geometry (geodesic on a sphere and on a [torus](https://en.wikipedia.org/wiki/Torus)), mechanics ([brachistochrone](https://en.wikipedia.org/wiki/Brachistochrone)) and optics (light beam in inhomogeneous medium).
- [Totally geodesic submanifold](http://www.map.mpim-bonn.mpg.de/Totally_geodesic_submanifold) [Archived](https://web.archive.org/web/20150810004925/http://www.map.mpim-bonn.mpg.de/Totally_geodesic_submanifold) 2015-08-10 at the [Wayback Machine](https://en.wikipedia.org/wiki/Wayback_Machine) at the Manifold Atlas
