[[calculus-analysis.base]]

> Source: [Convex set](https://en.wikipedia.org/wiki/Convex_set)
> License: Wikipedia content is available under CC BY-SA 4.0.

![[media/c491f854e4cb2ac16d6ddc33109d9b39abe917bc.png]]
Illustration of a convex set shaped like a deformed circle. The line segment joining points <em>x</em> and <em>y</em> lies completely within the set, illustrated in green. Since this is true for any potential locations of two points within the set, the set is convex.

![[media/0e1a44c8f19add574ed9a903e157c8b8b7ad47cd.png]]
Illustration of a non-convex set. The line segment joining points <em>x</em> and <em>y</em> partially extends outside of the set, illustrated in red, and the intersection of the set with the line occurs in two places, illustrated in black.

In [geometry](https://en.wikipedia.org/wiki/Geometry), a [set of points](https://en.wikipedia.org/wiki/Point_set) is **convex** if it contains every [line segment](https://en.wikipedia.org/wiki/Line_segment) between two points in the set. For example, a solid [cube](https://en.wikipedia.org/wiki/Cube_(geometry)) is a convex set, but anything that is hollow or has an indent, such as a [crescent](https://en.wikipedia.org/wiki/Crescent) shape, is not convex.

The [boundary](https://en.wikipedia.org/wiki/Boundary_(topology) "Boundary (topology)") of a convex set in the plane is always a [convex curve](https://en.wikipedia.org/wiki/Convex_curve). The intersection of all the convex sets that contain a given subset A of Euclidean space is called the [convex hull](https://en.wikipedia.org/wiki/Convex_hull) of A. It is the smallest convex set containing A.

A [convex function](https://en.wikipedia.org/wiki/Convex_function) is a [real-valued function](https://en.wikipedia.org/wiki/Real-valued_function) defined on an [interval](https://en.wikipedia.org/wiki/Interval_(mathematics) "Interval (mathematics)") with the property that its [epigraph](https://en.wikipedia.org/wiki/Epigraph_(mathematics) "Epigraph (mathematics)") (the set of points on or above the [graph](https://en.wikipedia.org/wiki/Graph_of_a_function) of the function) is a convex set. [Convex minimization](https://en.wikipedia.org/wiki/Convex_minimization) is a subfield of [optimization](https://en.wikipedia.org/wiki/Mathematical_optimization) that studies the problem of minimizing convex functions over convex sets. The branch of mathematics devoted to the study of properties of convex sets and convex functions is called [convex analysis](https://en.wikipedia.org/wiki/Convex_analysis).

Spaces in which convex sets are defined include the [Euclidean spaces](https://en.wikipedia.org/wiki/Euclidean_space), the [affine spaces](https://en.wikipedia.org/wiki/Affine_space) over the [real numbers](https://en.wikipedia.org/wiki/Real_number), and certain [non-Euclidean geometries](https://en.wikipedia.org/wiki/Non-Euclidean_geometry).

## Definitions

![[media/0d75398543c341801a071345c13c298cab8131f1.png]]
A [function](https://en.wikipedia.org/wiki/Convex_function) is convex if and only if its [epigraph](https://en.wikipedia.org/wiki/Epigraph_(mathematics)), the region (in green) above its [graph](https://en.wikipedia.org/wiki/Graph_of_a_function) (in blue), is a convex set.

Let S be a [[Vector Space]] or an [affine space](https://en.wikipedia.org/wiki/Affine_space) over the [real numbers](https://en.wikipedia.org/wiki/Real_number), or, more generally, over some [ordered field](https://en.wikipedia.org/wiki/Ordered_field) (this includes Euclidean spaces, which are affine spaces). A [subset](https://en.wikipedia.org/wiki/Subset) C of S is **convex** if, for all x and y in C, the [line segment](https://en.wikipedia.org/wiki/Line_segment) connecting x and y is included in C.

This means that the [affine combination](https://en.wikipedia.org/wiki/Affine_combination) (1 − *t*)*x* + *ty* belongs to C for all x,y in C and t in the [interval](https://en.wikipedia.org/wiki/Interval_(mathematics) "Interval (mathematics)") \[0, 1\]. This implies that convexity is invariant under [affine transformations](https://en.wikipedia.org/wiki/Affine_transformation). Further, it implies that a convex set in a [real](https://en.wikipedia.org/wiki/Real_number) or [complex](https://en.wikipedia.org/wiki/Complex_number) [topological vector space](https://en.wikipedia.org/wiki/Topological_vector_space) is [path-connected](https://en.wikipedia.org/wiki/Path-connected) (and therefore also [connected](https://en.wikipedia.org/wiki/Connected_space)).

A set C is strictly convex if every point on the line segment connecting x and y other than the endpoints is inside the [topological interior](https://en.wikipedia.org/wiki/Interior_(topology) "Interior (topology)") of C. A closed convex subset is strictly convex if and only if every one of its [boundary points](https://en.wikipedia.org/wiki/Boundary_(topology) "Boundary (topology)") is an [extreme point](https://en.wikipedia.org/wiki/Extreme_point).

A set C is **[absolutely convex](https://en.wikipedia.org/wiki/Absolutely_convex)** if it is convex and [balanced](https://en.wikipedia.org/wiki/Balanced_set).

### Examples

The convex [subsets](https://en.wikipedia.org/wiki/Subset) of **R** (the set of real numbers) are the intervals and the points of **R**. Some examples of convex subsets of the [Euclidean plane](https://en.wikipedia.org/wiki/Euclidean_plane) are solid [regular polygons](https://en.wikipedia.org/wiki/Regular_polygon), solid triangles, and intersections of solid triangles. Some examples of convex subsets of a [Euclidean 3-dimensional space](https://en.wikipedia.org/wiki/Euclidean_space) are the [Archimedean solids](https://en.wikipedia.org/wiki/Archimedean_solid) and the [Platonic solids](https://en.wikipedia.org/wiki/Platonic_solid). The [Kepler-Poinsot polyhedra](https://en.wikipedia.org/wiki/Kepler-Poinsot_polyhedra) are examples of non-convex sets.

### Non-convex set

A set that is not convex is called a *non-convex set*. A [polygon](https://en.wikipedia.org/wiki/Polygon) that is not a [convex polygon](https://en.wikipedia.org/wiki/Convex_polygon) is sometimes called a [concave polygon](https://en.wikipedia.org/wiki/Concave_polygon), and some sources more generally use the term *concave set* to mean a non-convex set, but most authorities prohibit this usage.

The [complement](https://en.wikipedia.org/wiki/Complement_(set_theory) "Complement (set theory)") of a convex set, such as the [epigraph](https://en.wikipedia.org/wiki/Epigraph_(mathematics) "Epigraph (mathematics)") of a [concave function](https://en.wikipedia.org/wiki/Concave_function), is sometimes called a *reverse convex set*, especially in the context of [mathematical optimization](https://en.wikipedia.org/wiki/Mathematical_optimization).

## Properties

Given r points *u*<sub>1</sub>, ..., *u<sub>r</sub>* in a convex set S, and r [nonnegative numbers](https://en.wikipedia.org/wiki/Negative_number) *λ*<sub>1</sub>, ..., *λ<sub>r</sub>* such that *λ*<sub>1</sub> + ... + *λ<sub>r</sub>* = 1, the [affine combination](https://en.wikipedia.org/wiki/Affine_combination) 

$$
\sum _{k=1}^{r}\lambda _{k}u_{k}
$$

 belongs to S. As the definition of a convex set is the case *r* = 2, this property characterizes convex sets.

Such an affine combination is called a [convex combination](https://en.wikipedia.org/wiki/Convex_combination) of *u*<sub>1</sub>, ..., *u<sub>r</sub>*. The **convex hull** of a subset S of a real vector space is defined as the intersection of all convex sets that contain S. More concretely, the convex hull is the set of all convex combinations of points in S. In particular, this is a convex set.

A *(bounded) [convex polytope](https://en.wikipedia.org/wiki/Convex_polytope)* is the convex hull of a finite subset of some Euclidean space **R***n*.

### Intersections and unions

The collection of convex subsets of a vector space, an affine space, or a [Euclidean space](https://en.wikipedia.org/wiki/Euclidean_space) has the following properties:

1. The [empty set](https://en.wikipedia.org/wiki/Empty_set) and the whole space are convex.
2. The intersection of any collection of convex sets is convex.
3. The *[union](https://en.wikipedia.org/wiki/Union_(sets))* of a collection of convex sets is convex if those sets form a [chain](https://en.wikipedia.org/wiki/Total_order#Chains) (a totally ordered set) under inclusion. For this property, the restriction to chains is important, as the union of two convex sets need not be convex.

### Closed convex sets

[Closed](https://en.wikipedia.org/wiki/Closed_set) convex sets are convex sets that contain all their [limit points](https://en.wikipedia.org/wiki/Limit_points). They can be characterised as the intersections of *closed [half-spaces](https://en.wikipedia.org/wiki/Half-space_(geometry) "Half-space (geometry)")* (sets of points in space that lie on and to one side of a [hyperplane](https://en.wikipedia.org/wiki/Hyperplane)).

From what has just been said, it is clear that such intersections are convex, and they will also be closed sets. To prove the converse, i.e., every closed convex set may be represented as such intersection, one needs the [supporting hyperplane theorem](https://en.wikipedia.org/wiki/Supporting_hyperplane_theorem) in the form that for a given closed convex set C and point P outside it, there is a closed half-space H that contains C and not P. The supporting hyperplane theorem is a special case of the [Hahn–Banach theorem](https://en.wikipedia.org/wiki/Hahn%E2%80%93Banach_theorem) of [functional analysis](https://en.wikipedia.org/wiki/Functional_analysis).

### Face of a convex set

A **face** of a convex set $C$ is a convex subset $F$ of $C$ such that whenever a point $p$ in $F$ lies strictly between two points $x$ and $y$ in $C$, both $x$ and $y$ must be in $F$. Equivalently, for any $x,y\in C$ and any real number $0<t<1$ such that $(1-t)x+ty$ is in $F$, $x$ and $y$ must be in $F$. According to this definition, $C$ itself and the empty set are faces of $C$; these are sometimes called the *trivial faces* of $C$. An **[extreme point](https://en.wikipedia.org/wiki/Extreme_point)** of $C$ is a point that is a face of $C$.

Let $C$ be a convex set in $\mathbb {R} ^{n}$ that is [compact](https://en.wikipedia.org/wiki/Compact_space) (or equivalently, closed and [bounded](https://en.wikipedia.org/wiki/Bounded_set)). Then $C$ is the convex hull of its extreme points. More generally, each compact convex set in a [locally convex topological vector space](https://en.wikipedia.org/wiki/Locally_convex_topological_vector_space) is the closed convex hull of its extreme points (the [Krein–Milman theorem](https://en.wikipedia.org/wiki/Krein%E2%80%93Milman_theorem)).

For example:

- A [triangle](https://en.wikipedia.org/wiki/Triangle) in the plane (including the region inside) is a compact convex set. Its nontrivial faces are the three vertices and the three edges. (So the only extreme points are the three vertices.)
- The only nontrivial faces of the [closed unit disk](https://en.wikipedia.org/wiki/Closed_unit_disk) $\{(x,y)\in \mathbb {R} ^{2}:x^{2}+y^{2}\leq 1\}$ are its extreme points, namely the points on the [unit circle](https://en.wikipedia.org/wiki/Unit_circle) $S^{1}=\{(x,y)\in \mathbb {R} ^{2}:x^{2}+y^{2}=1\}$.

### Convex sets and rectangles

Let C be a [convex body](https://en.wikipedia.org/wiki/Convex_body) in the plane (a convex set whose interior is non-empty). We can inscribe a rectangle *r* in C such that a [homothetic](https://en.wikipedia.org/wiki/Homothetic_transformation) copy *R* of *r* is circumscribed about C. The positive homothety ratio is at most 2 and: 

$$
{\tfrac {1}{2}}\cdot \operatorname {Area} (R)\leq \operatorname {Area} (C)\leq 2\cdot \operatorname {Area} (r)
$$

### Blaschke-Santaló diagrams

The set ${\mathcal {K}}^{2}$ of all planar convex bodies can be parameterized in terms of the convex body [diameter](https://en.wikipedia.org/wiki/Diameter_of_a_set) *D*, its inradius *r* (the biggest circle contained in the convex body) and its circumradius *R* (the smallest circle containing the convex body). In fact, this set can be described by the set of inequalities given by 

$$
2r\leq D\leq 2R
$$

$$
R\leq {\frac {\sqrt {3}}{3}}D
$$

$$
r+R\leq D
$$

$$
D^{2}{\sqrt {4R^{2}-D^{2}}}\leq 2R(2R+{\sqrt {4R^{2}-D^{2}}})
$$

 and can be visualized as the image of the function *g* that maps a convex body to the **R**2 point given by (*r*/*R*, *D*/2*R*). The image of this function is known a (*r*, *D*, *R*) Blachke-Santaló diagram.

![[media/0ae0d3ee6c6c6916aa084ee54208b932a2968858.jpg]]
Blaschke-Santaló (<em>r</em>, <em>D</em>, <em>R</em>) diagram for planar convex bodies. $\mathbb {L}$ denotes the line segment, $\mathbb {I} _{\frac {\pi }{3}}$ the equilateral triangle, $\mathbb {RT}$ the [Reuleaux triangle](https://en.wikipedia.org/wiki/Reuleaux_triangle) and $\mathbb {B} _{2}$ the unit circle.

Alternatively, the set ${\mathcal {K}}^{2}$ can also be parametrized by its width (the smallest distance between any two different parallel support hyperplanes), perimeter and area.

### Other properties

Let *X* be a topological vector space and $C\subseteq X$ be convex.

- $\operatorname {Cl} C$ and $\operatorname {Int} C$ are both convex (i.e. the closure and interior of convex sets are convex).
- If $a\in \operatorname {Int} C$ and $b\in \operatorname {Cl} C$ then $[a,b[\,\subseteq \operatorname {Int} C$ (where $[a,b[\,:=\left\{(1-r)a+rb:0\leq r<1\right\}$).
- If $\operatorname {Int} C\neq \emptyset$ then:
 - $\operatorname {cl} \left(\operatorname {Int} C\right)=\operatorname {Cl} C$, and
 - $\operatorname {Int} C=\operatorname {Int} \left(\operatorname {Cl} C\right)=C^{i}$, where $C^{i}$ is the [algebraic interior](https://en.wikipedia.org/wiki/Algebraic_interior) of *C*.

## Convex hulls and Minkowski sums

### Convex hulls

Every subset A of the vector space is contained within a smallest convex set (called the *convex hull* of A), namely the intersection of all convex sets containing A. The convex-hull operator Conv() has the characteristic properties of a [closure operator](https://en.wikipedia.org/wiki/Closure_operator):

- *extensive*: *S* ⊆ Conv(*S*),
- *[non-decreasing](https://en.wikipedia.org/wiki/Monotone_function#Monotonicity_in_order_theory)*: *S* ⊆ *T* implies that Conv(*S*) ⊆ Conv(*T*), and
- *[idempotent](https://en.wikipedia.org/wiki/Idempotence)*: Conv(Conv(*S*)) = Conv(*S*).

The convex-hull operation is needed for the set of convex sets to form a [lattice](https://en.wikipedia.org/wiki/Lattice_(order) "Lattice (order)"), in which the ["*join*" operation](https://en.wikipedia.org/wiki/Join_and_meet) is the convex hull of the union of two convex sets 

$$
\operatorname {Conv} (S)\vee \operatorname {Conv} (T)=\operatorname {Conv} (S\cup T)=\operatorname {Conv} {\bigl (}\operatorname {Conv} (S)\cup \operatorname {Conv} (T){\bigr )}.
$$

 The intersection of any collection of convex sets is itself convex, so the convex subsets of a (real or complex) vector space form a complete [lattice](https://en.wikipedia.org/wiki/Lattice_(order) "Lattice (order)").

### Minkowski addition

![[media/0df1f2544674e370375b83742f2c55c4ff95b3f5.png]]
[Minkowski addition](https://en.wikipedia.org/wiki/Minkowski_addition) of sets. The [sum](https://en.wikipedia.org/wiki/Sumset) of the squares Q<sub>1</sub>=[0,1]2 and Q<sub>2</sub>=[1,2]2 is the square Q<sub>1</sub>+Q<sub>2</sub>=[1,3]2.

In a real vector-space, the *[Minkowski sum](https://en.wikipedia.org/wiki/Minkowski_addition)* of two (non-empty) sets, *S*<sub>1</sub> and *S*<sub>2</sub>, is defined to be the [set](https://en.wikipedia.org/wiki/Sumset) *S*<sub>1</sub> + *S*<sub>2</sub> formed by the addition of vectors element-wise from the summand-sets 

$$
S_{1}+S_{2}=\{x_{1}+x_{2}:x_{1}\in S_{1},x_{2}\in S_{2}\}.
$$

 More generally, the *Minkowski sum* of a finite family of (non-empty) sets *S<sub>n</sub>* is the set formed by element-wise addition of vectors 

$$
\sum _{n}S_{n}=\left\{\sum _{n}x_{n}:x_{n}\in S_{n}\right\}.
$$

For Minkowski addition, the *zero set* {0} containing only the [zero vector](https://en.wikipedia.org/wiki/Null_vector) 0 has [special importance](https://en.wikipedia.org/wiki/Identity_element): For every non-empty subset S of a vector space 

$$
S+\{0\}=S;
$$

 in algebraic terminology, {0} is the [identity element](https://en.wikipedia.org/wiki/Identity_element) of Minkowski addition (on the collection of non-empty sets).

### Convex hulls of Minkowski sums

Minkowski addition behaves well with respect to the operation of taking convex hulls, as shown by the following proposition:

Let *S*<sub>1</sub>, *S*<sub>2</sub> be subsets of a real vector-space, the [convex hull](https://en.wikipedia.org/wiki/Convex_hull) of their Minkowski sum is the Minkowski sum of their convex hulls 

$$
\operatorname {Conv} (S_{1}+S_{2})=\operatorname {Conv} (S_{1})+\operatorname {Conv} (S_{2}).
$$

This result holds more generally for each finite collection of non-empty sets: 

$$
{\text{Conv}}\left(\sum _{n}S_{n}\right)=\sum _{n}{\text{Conv}}\left(S_{n}\right).
$$

In mathematical terminology, the [operations](https://en.wikipedia.org/wiki/Operation_(mathematics) "Operation (mathematics)") of Minkowski summation and of forming [convex hulls](https://en.wikipedia.org/wiki/Convex_hull) are [commuting](https://en.wikipedia.org/wiki/Commutativity) operations.

### Minkowski sums of convex sets

The Minkowski sum of two compact convex sets is compact. The sum of a compact convex set and a closed convex set is closed.

The following famous theorem, proved by Dieudonné in 1966, gives a sufficient condition for the difference of two closed convex subsets to be closed. It uses the concept of a **recession cone** of a non-empty convex subset *S*, defined as: 

$$
\operatorname {rec} S=\left\{x\in X\,:\,x+S\subseteq S\right\},
$$

 where this set is a [convex cone](https://en.wikipedia.org/wiki/Convex_cone) containing $0\in X$ and satisfying $S+\operatorname {rec} S=S$. Note that if *S* is closed and convex then $\operatorname {rec} S$ is closed and for all $s_{0}\in S$, 

$$
\operatorname {rec} S=\bigcap _{t>0}t(S-s_{0}).
$$

**Theorem** (Dieudonné). Let *A* and *B* be non-empty, closed, and convex subsets of a [locally convex topological vector space](https://en.wikipedia.org/wiki/Locally_convex_topological_vector_space) such that $\operatorname {rec} A\cap \operatorname {rec} B$ is a linear subspace. If *A* or *B* is [locally compact](https://en.wikipedia.org/wiki/Locally_compact) then *A* − *B* is closed.

## Generalizations and extensions for convexity

The notion of convexity in the Euclidean space may be generalized by modifying the definition in some or other aspects. The common name "generalized convexity" is used, because the resulting objects retain certain properties of convex sets.

### Star-convex (star-shaped) sets

Let C be a set in a real or complex vector space. C is **star convex (star-shaped)** if there exists an *x*<sub>0</sub> in C such that the line segment from *x*<sub>0</sub> to any point y in C is contained in C. Hence a non-empty convex set is always star-convex but a star-convex set is not always convex.

### Orthogonal convexity

An example of generalized convexity is **orthogonal convexity**.

A set S in the Euclidean space is called **orthogonally convex** or **ortho-convex**, if any segment parallel to any of the coordinate axes connecting two points of S lies totally within S. It is easy to prove that an intersection of any collection of orthoconvex sets is orthoconvex. Some other properties of convex sets are valid as well.

### Non-Euclidean geometry

The definition of a convex set and a convex hull extends naturally to geometries which are not Euclidean by defining a [geodesically convex set](https://en.wikipedia.org/wiki/Geodesic_convexity) to be one that contains the [geodesics](https://en.wikipedia.org/wiki/Geodesic) joining any two points in the set.

### Order topology

Convexity can be extended for a [totally ordered set](https://en.wikipedia.org/wiki/Totally_ordered_set) X endowed with the [order topology](https://en.wikipedia.org/wiki/Order_topology).

Let *Y* ⊆ *X*. The subspace Y is a convex set if for each pair of points *a*, *b* in Y such that *a* ≤ *b*, the interval \[*a*, *b*\] = {*x* ∈ *X* \| *a* ≤ *x* ≤ *b*} is contained in Y. That is, Y is convex if and only if for all *a*, *b* in Y, *a* ≤ *b* implies \[*a*, *b*\] ⊆ *Y*.

A convex set is *not* connected in general: a counter-example is given by the subspace {1,2,3} in **Z**, which is both convex and not connected.

### Convexity spaces

The notion of convexity may be generalised to other objects, if certain properties of convexity are selected as [axioms](https://en.wikipedia.org/wiki/Axiom).

Given a set X, a **convexity** over X is a collection *𝒞* of subsets of X satisfying the following axioms:

1. The empty set and X are in *𝒞*.
2. The intersection of any collection from *𝒞* is in *𝒞*.
3. The union of a [chain](https://en.wikipedia.org/wiki/Total_order) (with respect to the [inclusion relation](https://en.wikipedia.org/wiki/Inclusion_relation)) of elements of *𝒞* is in *𝒞*.

The elements of *𝒞* are called convex sets and the pair (*X*, *𝒞*) is called a **convexity space**. For the ordinary convexity, the first two axioms hold, and the third one is trivial.

For an alternative definition of abstract convexity, more suited to [discrete geometry](https://en.wikipedia.org/wiki/Discrete_geometry), see the *convex geometries* associated with [antimatroids](https://en.wikipedia.org/wiki/Antimatroid).

### Convex spaces

Convexity can be generalised as an abstract algebraic structure: a space is convex if it is possible to take convex combinations of points.

## See also

- [Absorbing set](https://en.wikipedia.org/wiki/Absorbing_set)
- [Algorithmic problems on convex sets](https://en.wikipedia.org/wiki/Algorithmic_problems_on_convex_sets)
- [Bounded set (topological vector space)](https://en.wikipedia.org/wiki/Bounded_set_(topological_vector_space) "Bounded set (topological vector space)")
- [Brouwer fixed-point theorem](https://en.wikipedia.org/wiki/Brouwer_fixed-point_theorem)
- [Complex convexity](https://en.wikipedia.org/wiki/Complex_convexity)
- [Convex cone](https://en.wikipedia.org/wiki/Convex_cone)
- [Convex series](https://en.wikipedia.org/wiki/Convex_series)
- [Convex metric space](https://en.wikipedia.org/wiki/Convex_metric_space)
- [Carathéodory's theorem (convex hull)](https://en.wikipedia.org/wiki/Carath%C3%A9odory%27s_theorem_(convex_hull) "Carathéodory's theorem (convex hull)")
- [Choquet theory](https://en.wikipedia.org/wiki/Choquet_theory)
- [Helly's theorem](https://en.wikipedia.org/wiki/Helly%27s_theorem)
- [Holomorphically convex hull](https://en.wikipedia.org/wiki/Holomorphically_convex_hull)
- [Integrally-convex set](https://en.wikipedia.org/wiki/Integrally-convex_set)
- [John ellipsoid](https://en.wikipedia.org/wiki/John_ellipsoid)
- [Pseudoconvexity](https://en.wikipedia.org/wiki/Pseudoconvexity)
- [Radon's theorem](https://en.wikipedia.org/wiki/Radon%27s_theorem)
- [Shapley–Folkman lemma](https://en.wikipedia.org/wiki/Shapley%E2%80%93Folkman_lemma)
- [Symmetric set](https://en.wikipedia.org/wiki/Symmetric_set)

## References

1. Morris, Carla C.; Stark, Robert M. (24 August 2015). [Finite Mathematics: Models and Applications](https://books.google.com/books?id=ZgJyCgAAQBAJ&q=convex+region&pg=PA121). John Wiley & Sons. p. 121. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9781119015383](https://en.wikipedia.org/wiki/Special:BookSources/9781119015383). Retrieved 5 April 2017.
2. Kjeldsen, Tinne Hoff. ["History of Convexity and Mathematical Programming"](https://web.archive.org/web/20170811100026/http://www.mathunion.org/ICM/ICM2010.4/Main/icm2010.4.3233.3257.pdf) (PDF). *Proceedings of the International Congress of Mathematicians* (ICM 2010): 3233–3257. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1142/9789814324359_0187](https://doi.org/10.1142%2F9789814324359_0187). Archived from [the original](http://www.mathunion.org/ICM/ICM2010.4/Main/icm2010.4.3233.3257.pdf) (PDF) on 2017-08-11. Retrieved 5 April 2017.
3. [Halmos, Paul R.](https://en.wikipedia.org/wiki/Paul_Richard_Halmos) (8 November 1982). *A Hilbert Space Problem Book*. [Graduate Texts in Mathematics](https://en.wikipedia.org/wiki/Graduate_Texts_in_Mathematics). Vol. 19 (2nd ed.). New York: [Springer-Verlag](https://en.wikipedia.org/wiki/Springer_Publishing). p. 5. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-90685-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-90685-0). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [8169781](https://search.worldcat.org/oclc/8169781).
4. McConnell, Jeffrey J. (2006). [Computer Graphics: Theory Into Practice](https://archive.org/details/computergraphics0000mcco/page/130). Jones & Bartlett Learning. p. [130](https://archive.org/details/computergraphics0000mcco/page/130). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-7637-2250-2](https://en.wikipedia.org/wiki/Special:BookSources/0-7637-2250-2)..
5. [Weisstein, Eric W.](https://en.wikipedia.org/wiki/Eric_W._Weisstein) ["Concave"](https://mathworld.wolfram.com/Concave.html). *[MathWorld](https://en.wikipedia.org/wiki/MathWorld)*.
6. Takayama, Akira (1994). [Analytical Methods in Economics](https://books.google.com/books?id=_WmZA0MPlmEC&pg=PA54). University of Michigan Press. p. 54. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780472081356](https://en.wikipedia.org/wiki/Special:BookSources/9780472081356). “An often seen confusion is a "concave set". Concave and convex functions designate certain classes of functions, not of sets, whereas a convex set designates a certain class of sets, and not a class of functions. A "concave set" confuses sets with functions.”
7. Corbae, Dean; Stinchcombe, Maxwell B.; Zeman, Juraj (2009). [An Introduction to Mathematical Analysis for Economic Theory and Econometrics](https://books.google.com/books?id=j5P83LtzVO8C&pg=PT347). Princeton University Press. p. 347. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9781400833085](https://en.wikipedia.org/wiki/Special:BookSources/9781400833085). “There is no such thing as a concave set.”
8. Meyer, Robert (1970). ["The validity of a family of optimization methods"](https://minds.wisconsin.edu/bitstream/handle/1793/57508/TR28.pdf?sequence=1) (PDF). *SIAM Journal on Control and Optimization*. **8**: 41–54. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/0308003](https://doi.org/10.1137%2F0308003). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0312915](https://mathscinet.ams.org/mathscinet-getitem?mr=0312915)..
9. ^ Soltan, Valeriu, *Introduction to the Axiomatic Theory of Convexity*, Ştiinţa, [Chişinău](https://en.wikipedia.org/wiki/Chi%C5%9Fin%C4%83u), 1984 (in Russian).
10. ^ Singer, Ivan (1997). *Abstract convex analysis*. Canadian Mathematical Society series of monographs and advanced texts. New York: John Wiley & Sons, Inc. pp. xxii+491. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-16015-6](https://en.wikipedia.org/wiki/Special:BookSources/0-471-16015-6). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1461544](https://mathscinet.ams.org/mathscinet-getitem?mr=1461544).
11. , p. 162.
12. , p. 166.
13. Lassak, M. (1993). "Approximation of convex bodies by rectangles". *Geometriae Dedicata*. **47**: 111–117. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/BF01263495](https://doi.org/10.1007%2FBF01263495). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [119508642](https://api.semanticscholar.org/CorpusID:119508642).
14. ^ Santaló, L. (1961). "Sobre los sistemas completos de desigualdades entre tres elementos de una figura convexa planas". *Mathematicae Notae*. **17**: 82–104.
15. ^ Brandenberg, René; González Merino, Bernardo (2017). ["A complete 3-dimensional Blaschke-Santaló diagram"](http://mia.ele-math.com/20-22). *Mathematical Inequalities & Applications* (2): 301–348. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1404.6808](https://arxiv.org/abs/1404.6808). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.7153/mia-20-22](https://doi.org/10.7153%2Fmia-20-22). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1331-4343](https://search.worldcat.org/issn/1331-4343).
16. The [empty set](https://en.wikipedia.org/wiki/Empty_set) is important in Minkowski addition, because the empty set annihilates every other subset: For every subset S of a vector space, its sum with the empty set is empty: $S+\emptyset =\emptyset$.
17. Theorem 3 (pages 562–563): [Krein, M.](https://en.wikipedia.org/wiki/Mark_Krein); Šmulian, V. (1940). "On regularly convex sets in the space conjugate to a Banach space". *Annals of Mathematics*. Second Series. **41** (3): 556–583. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/1968735](https://doi.org/10.2307%2F1968735). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [1968735](https://www.jstor.org/stable/1968735).
18. For the commutativity of [Minkowski addition](https://en.wikipedia.org/wiki/Minkowski_addition) and [convexification](https://en.wikipedia.org/wiki/Convex_hull), see Theorem 1.1.2 (pages 2–3) in Schneider; this reference discusses much of the literature on the [convex hulls](https://en.wikipedia.org/wiki/Convex_hull) of [Minkowski](https://en.wikipedia.org/wiki/Minkowski_addition) [sumsets](https://en.wikipedia.org/wiki/Sumset) in its "Chapter 3 Minkowski addition" (pages 126–196): Schneider, Rolf (1993). [Convex bodies: The Brunn–Minkowski theory](https://archive.org/details/convexbodiesbrun0000schn). Encyclopedia of mathematics and its applications. Vol. 44. Cambridge: Cambridge University Press. pp. xiv+490. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-35220-7](https://en.wikipedia.org/wiki/Special:BookSources/0-521-35220-7). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1216521](https://mathscinet.ams.org/mathscinet-getitem?mr=1216521).
19. Lemma 5.3: Aliprantis, C.D.; Border, K.C. (2006). *Infinite Dimensional Analysis, A Hitchhiker's Guide*. Berlin: Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-29587-7](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-29587-7).
20. Zălinescu, C. (2002). [Convex analysis in general vector spaces](https://archive.org/details/convexanalysisge00zali_934). River Edge, NJ: World Scientific Publishing Co., Inc. p. [7](https://archive.org/details/convexanalysisge00zali_934/page/n27). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [981-238-067-1](https://en.wikipedia.org/wiki/Special:BookSources/981-238-067-1). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1921556](https://mathscinet.ams.org/mathscinet-getitem?mr=1921556).
21. Rawlins G.J.E. and Wood D, "Ortho-convexity and its generalizations", in: *Computational Morphology*, 137-152. [Elsevier](https://en.wikipedia.org/wiki/Elsevier), 1988.
22. [Munkres, James](https://en.wikipedia.org/wiki/James_Munkres); *Topology*, Prentice Hall; 2nd edition (December 28, 1999). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-13-181629-2](https://en.wikipedia.org/wiki/Special:BookSources/0-13-181629-2).
23. van De Vel, Marcel L. J. (1993). *Theory of convex structures*. North-Holland Mathematical Library. Amsterdam: North-Holland Publishing Co. pp. xvi+540. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-444-81505-8](https://en.wikipedia.org/wiki/Special:BookSources/0-444-81505-8). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1234493](https://mathscinet.ams.org/mathscinet-getitem?mr=1234493).

## Bibliography

- [Rockafellar, R. T.](https://en.wikipedia.org/wiki/R._Tyrrell_Rockafellar) (1997) \[1970\]. [Convex Analysis](https://books.google.com/books?id=1TiOka9bx3sC). Princeton, NJ: Princeton University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [1-4008-7317-7](https://en.wikipedia.org/wiki/Special:BookSources/1-4008-7317-7).

## External links

- ["Convex subset"](https://www.encyclopediaofmath.org/). *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*. [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society). 2001 \[1994\].
- [Lectures on Convex Sets](http://www.fmf.uni-lj.si/~lavric/lauritzen.pdf), notes by Niels Lauritzen, at [Aarhus University](https://en.wikipedia.org/wiki/Aarhus_University), March 2010.
