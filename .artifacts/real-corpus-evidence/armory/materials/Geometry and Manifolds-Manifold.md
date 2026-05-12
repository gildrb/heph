[[geometry-manifolds.base]]

> Source: [[Manifold]]
> License: Wikipedia content is available under CC BY-SA 4.0.

![[media/4a5d86d093f4172d2e8e457551c47c45a18ee77b.png]]
The [Klein bottle](https://en.wikipedia.org/wiki/Klein_bottle) immersed in three-dimensional space

![[media/11fc79cb5987ec20266e37942f4eb5831b41814a.jpg]]
The surface of the Earth requires (at least) two charts to include every point without plotting the same point more than once on the same chart. Here the [globe](https://en.wikipedia.org/wiki/Globe) is decomposed into charts around the [North](https://en.wikipedia.org/wiki/North_Pole) and [South Poles](https://en.wikipedia.org/wiki/South_Pole).

In [mathematics](https://en.wikipedia.org/wiki/Mathematics), a **manifold** is a [topological space](https://en.wikipedia.org/wiki/Topological_space) that locally resembles [Euclidean space](https://en.wikipedia.org/wiki/Euclidean_space) near each point. More precisely, an $n$-dimensional manifold, or *$n$-manifold* for short, is a topological space with the property that each point has a [neighborhood](https://en.wikipedia.org/wiki/Neighbourhood_(mathematics) "Neighbourhood (mathematics)") that is [homeomorphic](https://en.wikipedia.org/wiki/Homeomorphic) to an [open subset](https://en.wikipedia.org/wiki/Open_(topology)) of $n$-dimensional Euclidean space.

One-dimensional manifolds include [lines](https://en.wikipedia.org/wiki/Line_(geometry) "Line (geometry)") and [circles](https://en.wikipedia.org/wiki/Circle), but not [self-crossing curves such as a figure-eight](https://en.wikipedia.org/wiki/Lemniscate). Two-dimensional manifolds are also called [surfaces](https://en.wikipedia.org/wiki/Surface_(topology) "Surface (topology)"). Examples include the [plane](https://en.wikipedia.org/wiki/Plane_(geometry)), the [sphere](https://en.wikipedia.org/wiki/Sphere), and the [torus](https://en.wikipedia.org/wiki/Torus), and also the [Klein bottle](https://en.wikipedia.org/wiki/Klein_bottle) and [real projective plane](https://en.wikipedia.org/wiki/Real_projective_plane).

The concept of a manifold is central to many parts of [geometry](https://en.wikipedia.org/wiki/Geometry) and modern [mathematical physics](https://en.wikipedia.org/wiki/Mathematical_physics) because it allows complicated structures to be described in terms of well-understood topological properties of simpler spaces. Manifolds naturally arise as solution sets of [systems of equations](https://en.wikipedia.org/wiki/Systems_of_equations) and as [graphs](https://en.wikipedia.org/wiki/Graph_of_a_function) of functions. The concept has applications in computer-graphics given the need to associate pictures with coordinates (e.g. [CT scans](https://en.wikipedia.org/wiki/CT_scan)).

Manifolds can be equipped with additional structure. One important class of manifolds are [differentiable manifolds](https://en.wikipedia.org/wiki/Differentiable_manifold); their [differentiable structure](https://en.wikipedia.org/wiki/Differentiable_structure) allows [calculus](https://en.wikipedia.org/wiki/Calculus) to be done. A [Riemannian metric](https://en.wikipedia.org/wiki/Riemannian_metric) on a manifold allows [distances](https://en.wikipedia.org/wiki/Distance) and [angles](https://en.wikipedia.org/wiki/Angle) to be measured. [Symplectic manifolds](https://en.wikipedia.org/wiki/Symplectic_manifold) serve as the [phase spaces](https://en.wikipedia.org/wiki/Phase_space) in the [Hamiltonian formalism](https://en.wikipedia.org/wiki/Hamiltonian_mechanics) of [classical mechanics](https://en.wikipedia.org/wiki/Classical_mechanics), while four-dimensional [Lorentzian manifolds](https://en.wikipedia.org/wiki/Lorentzian_manifold) model [spacetime](https://en.wikipedia.org/wiki/Spacetime) in [general relativity](https://en.wikipedia.org/wiki/General_relativity).

The study of manifolds requires working knowledge of calculus and [topology](https://en.wikipedia.org/wiki/Topology).

## Motivating examples

### Circle

![[media/386653ee27fed46199513308a9529323a53d7fa6.png]]
Figure 1: The four charts each map part of the circle to an open interval, and together cover the whole circle.

After a line, a circle is the simplest example of a topological manifold. Topology ignores bending, so a small piece of a circle is treated the same as a small piece of a line. Considering, for instance, the top part of the [unit circle](https://en.wikipedia.org/wiki/Unit_circle), *x*<sup>2</sup> + *y*<sup>2</sup> = 1, where the [*y*-coordinate](https://en.wikipedia.org/wiki/Cartesian_coordinate_system) is positive (indicated by the yellow arc in *Figure 1*). Any point of this arc can be uniquely described by its *x*-coordinate. So, [projection](https://en.wikipedia.org/wiki/Projection_(mathematics) "Projection (mathematics)") onto the first coordinate is a [continuous](https://en.wikipedia.org/wiki/Continuous_function_(topology)) and [invertible](https://en.wikipedia.org/wiki/Inverse_function) [mapping](https://en.wikipedia.org/wiki/Mapping_(mathematics)) from the upper arc to the [open interval](https://en.wikipedia.org/wiki/Open_interval) (−1, 1): 

$$
\chi _{\mathrm {top} }(x,y)=x.\,
$$

Such functions along with the open regions they map are called *[charts](https://en.wikipedia.org/wiki/Atlas_(topology)#Charts "Atlas (topology)")*. Similarly, there are charts for the bottom (red), left (blue), and right (green) parts of the circle: 

$$
{\begin{aligned}\chi _{\mathrm {bottom} }(x,y)&=x\\\chi _{\mathrm {left} }(x,y)&=y\\\chi _{\mathrm {right} }(x,y)&=y.\end{aligned}}
$$

Together, these parts cover the whole circle, and the four charts form an [atlas](https://en.wikipedia.org/wiki/Atlas_(topology) "Atlas (topology)") for the circle.

The top and right charts, $\chi _{\mathrm {top} }$ and $\chi _{\mathrm {right} }$ respectively, overlap in their domain: their intersection lies in the quarter of the circle where both $x$ and $y$-coordinates are positive. Both map this part into the interval $(0,1)$, though differently. Thus a function $T:(0,1)\rightarrow (0,1)=\chi _{\mathrm {right} }\circ \chi _{\mathrm {top} }^{-1}$ can be constructed, which takes values from the co-domain of $\chi _{\mathrm {top} }$ back to the circle using the inverse, followed by $\chi _{\mathrm {right} }$ back to the interval. If *a* is any number in $(0,1)$, then: 

$$
{\begin{aligned}T(a)&=\chi _{\mathrm {right} }\left(\chi _{\mathrm {top} }^{-1}\left[a\right]\right)\\&=\chi _{\mathrm {right} }\left(a,{\sqrt {1-a^{2}}}\right)\\&={\sqrt {1-a^{2}}}\end{aligned}}
$$

Such a function is called a [*transition map*](https://en.wikipedia.org/wiki/Atlas_(topology)#Transition_maps "Atlas (topology)").

![[media/7cded0e55e5ce546eb8bdd2494309074231fa530.png]]
Figure 2: A circle manifold chart based on slope, covering all but one point of the circle.

The top, bottom, left, and right charts do not form the only possible atlas. Charts need not be geometric projections, and the number of charts is a matter of choice. Consider the charts 

$$
\chi _{\mathrm {minus} }(x,y)=s={\frac {y}{1+x}}
$$

 and 

$$
\chi _{\mathrm {plus} }(x,y)=t={\frac {y}{1-x}}
$$

Here *s* is the slope of the line through the point at coordinates (*x*, *y*) and the fixed pivot point (−1, 0); similarly, *t* is the opposite of the slope of the line through the points at coordinates (*x*, *y*) and (+1, 0). The inverse mapping from *s* to (*x*, *y*) is given by 

$$
{\begin{aligned}x&={\frac {1-s^{2}}{1+s^{2}}}\\[5pt]y&={\frac {2s}{1+s^{2}}}\end{aligned}}
$$

It can be confirmed that *x*<sup>2</sup> + *y*<sup>2</sup> = 1 for all values of *s* and *t*. These two charts provide a second atlas for the circle, with the transition map 

$$
t={\frac {1}{s}}
$$

 (that is, one has this relation between *s* and *t* for every point where *s* and *t* are both nonzero).

Each chart omits a single point, either (−1, 0) for *s* or (+1, 0) for *t*, so neither chart alone is sufficient to cover the whole circle. It can be proved that it is not possible to cover the full circle with a single chart. For example, although it is possible to construct a circle from a single line interval by overlapping and "gluing" the ends, this does not produce a chart; a portion of the circle will be mapped to both ends at once, losing invertibility.

### Sphere

The [sphere](https://en.wikipedia.org/wiki/Sphere) is an example of a surface. The [unit sphere](https://en.wikipedia.org/wiki/Unit_sphere) of [implicit equation](https://en.wikipedia.org/wiki/Implicit_equation)

*x*<sup>2</sup> + *y*<sup>2</sup> + *z*<sup>2</sup> – 1 = 0

may be covered by an atlas of six [charts](https://en.wikipedia.org/wiki/Chart_(mathematics)): the plane *z* = 0 divides the sphere into two half spheres (*z* \> 0 and *z* \< 0), which may both be mapped on the disc *x*<sup>2</sup> + *y*<sup>2</sup> \< 1 by the projection on the *xy* plane of coordinates. This provides two charts; the four other charts are provided by a similar construction with the two other coordinate planes.

As with the circle, one may define one chart that covers the whole sphere excluding one point. Thus two charts are sufficient, but the sphere cannot be covered by a single chart.

This example is historically significant, as it has motivated the terminology; it became apparent that the whole surface of the [Earth](https://en.wikipedia.org/wiki/Earth) cannot have a plane representation consisting of a single [map](https://en.wikipedia.org/wiki/Map) (also called "chart", see [nautical chart](https://en.wikipedia.org/wiki/Nautical_chart)), and therefore one needs [atlases](https://en.wikipedia.org/wiki/Atlas) for covering the whole Earth surface.

### Other curves

![[media/f14a054d81366e3699ebf0de418fae69f9629ec2.png]]
Four manifolds from [algebraic curves](https://en.wikipedia.org/wiki/Algebraic_curve): ■ circles, ■ parabola, ■ hyperbola, ■ cubic.

Manifolds do not need to be [connected](https://en.wikipedia.org/wiki/Connected_space) (all in "one piece"); an example is a pair of separate circles.

Manifolds need not be [closed](https://en.wikipedia.org/wiki/Closed_manifold); thus a line segment without its end points is a manifold. They are never [countable](https://en.wikipedia.org/wiki/Countable_set), unless the dimension of the manifold is 0. Putting these freedoms together, other examples of manifolds are a [parabola](https://en.wikipedia.org/wiki/Parabola), a [hyperbola](https://en.wikipedia.org/wiki/Hyperbola), and the [locus](https://en.wikipedia.org/wiki/Locus_(mathematics) "Locus (mathematics)") of points on a [cubic curve](https://en.wikipedia.org/wiki/Cubic_curve) *y*<sup>2</sup> = *x*<sup>3</sup> − *x* (a closed loop piece and an open, infinite piece).

However, excluded are examples like two touching circles that share a point to form a figure-8; at the shared point, a satisfactory chart cannot be created. Even with the bending allowed by topology, the vicinity of the shared point looks like a "+", not a line. A "+" is not homeomorphic to a line segment, since deleting the center point from the "+" gives a space with four [components](https://en.wikipedia.org/wiki/Locally_connected_space) (i.e. pieces), whereas deleting a point from a line segment gives a space with at most two pieces; [topological operations](https://en.wikipedia.org/wiki/Homeomorphism) always preserve the number of pieces.

## Definition

Informally, a manifold is a [space](https://en.wikipedia.org/wiki/Topological_space) that is "modeled on" Euclidean space.

A manifold can be constructed by giving a collection of coordinate charts, that is, a covering by open sets with homeomorphisms to a Euclidean space, and patching functions<sup>\[*[clarification needed](https://en.wikipedia.org/wiki/Wikipedia:Please_clarify)*\]</sup>: homeomorphisms from one region of Euclidean space to another region if they correspond to the same part of the manifold in two different coordinate charts. A manifold can be given additional structure if the patching functions satisfy axioms beyond continuity. For instance, [differentiable manifolds](https://en.wikipedia.org/wiki/Differentiable_manifold) have homeomorphisms on overlapping neighborhoods [diffeomorphic](https://en.wikipedia.org/wiki/Diffeomorphic) with each other, so that the manifold has a well-defined set of functions which are differentiable in each neighborhood, thus differentiable on the manifold as a whole.

Formally, a (topological) manifold is a [second countable](https://en.wikipedia.org/wiki/Second_countable) [Hausdorff space](https://en.wikipedia.org/wiki/Hausdorff_space) that is locally homeomorphic to a Euclidean space.

*Second countable* and *Hausdorff* are [point-set](https://en.wikipedia.org/wiki/Point-set_topology) conditions; *second countable* excludes spaces which are in some sense 'too large' such as the [long line](https://en.wikipedia.org/wiki/Long_line_(topology) "Long line (topology)"), while *Hausdorff* excludes spaces such as ["the line with two origins"](https://en.wikipedia.org/wiki/Non-Hausdorff_manifold).

*Locally homeomorphic* to a Euclidean space means that every point has a neighborhood [homeomorphic](https://en.wikipedia.org/wiki/Homeomorphic) to an [open subset](https://en.wikipedia.org/wiki/Open_subset) of the [Euclidean space](https://en.wikipedia.org/wiki/Euclidean_space) $\mathbb {R} ^{n},$ for some nonnegative integer n.

This implies that either the point is an [isolated point](https://en.wikipedia.org/wiki/Isolated_point) (if $n=0$), or it has a neighborhood homeomorphic to the [open ball](https://en.wikipedia.org/wiki/Open_ball) 

$$
\mathbf {B} ^{n}=\left\{(x_{1},x_{2},\dots ,x_{n})\in \mathbb {R} ^{n}:x_{1}^{2}+x_{2}^{2}+\cdots +x_{n}^{2}<1\right\}.
$$

 This implies also that every point has a neighborhood homeomorphic to $\mathbb {R} ^{n}$ since $\mathbb {R} ^{n}$ is homeomorphic, and even [diffeomorphic](https://en.wikipedia.org/wiki/Diffeomorphic) to any open ball in it (for $n>0$).

The n that appears in the preceding definition is called the *local dimension* of the manifold. Generally manifolds are taken to have a constant local dimension, and the local dimension is then called the *dimension* of the manifold. This is, in particular, the case when manifolds are [connected](https://en.wikipedia.org/wiki/Connected_space). However, some authors admit manifolds that are not connected, and where different points can have different [dimensions](https://en.wikipedia.org/wiki/Dimension). If a manifold has a fixed dimension, this can be emphasized by calling it a pure manifold. For example, the (surface of a) sphere has a constant dimension of 2 and is therefore a pure manifold whereas the [disjoint union](https://en.wikipedia.org/wiki/Disjoint_union) of a sphere and a line in three-dimensional space is *not* a pure manifold. Since dimension is a local invariant (i.e. the map sending each point to the dimension of its neighbourhood over which a chart is defined, is [locally constant](https://en.wikipedia.org/wiki/Locally_constant)), each [connected component](https://en.wikipedia.org/wiki/Connected_space) has a fixed dimension.

[Sheaf-theoretically](https://en.wikipedia.org/wiki/Sheaf_(mathematics) "Sheaf (mathematics)"), a manifold is a [locally ringed space](https://en.wikipedia.org/wiki/Locally_ringed_space), whose structure [sheaf](https://en.wikipedia.org/wiki/Sheaf_(mathematics) "Sheaf (mathematics)") is locally isomorphic to the sheaf of continuous (or differentiable, or complex-analytic, etc.) functions on Euclidean space. This definition is mostly used when discussing analytic manifolds in [algebraic geometry](https://en.wikipedia.org/wiki/Algebraic_geometry).

## Charts, atlases, and transition maps

The spherical Earth is navigated using flat maps or charts, collected in an atlas. Similarly, a manifold can be described using [mathematical maps](https://en.wikipedia.org/wiki/Map_(mathematics) "Map (mathematics)"), called *coordinate charts*, collected in a mathematical *atlas*. It is not generally possible to describe a manifold with just one chart, because the global structure of the manifold is different from the simple structure of the charts. For example, no single flat map can represent the entire Earth without separation of adjacent features across the map's boundaries or duplication of coverage. When a manifold is constructed from multiple overlapping charts, the regions where they overlap carry information essential to understanding the global structure.

### Charts

A *coordinate map*, a *coordinate chart*, or simply a *chart*, of a manifold is an invertible map between a subset of the manifold and a simple space such that both the map and its inverse preserve the desired structure. For a topological manifold, the simple space is a subset of some Euclidean space $\mathbb {R} ^{n}$ and interest focuses on the topological structure. This structure is preserved by [homeomorphisms](https://en.wikipedia.org/wiki/Homeomorphisms), invertible maps that are continuous in both directions.

In the case of a differentiable manifold, a set of *charts* called an *atlas*, whose *transition functions* (see below) are all differentiable, allows us to do calculus on it. [Polar coordinates](https://en.wikipedia.org/wiki/Polar_coordinates), for example, form a chart for the plane $\mathbb {R} ^{2}$ minus the positive *x*-axis and the origin. Another example of a chart is the map χ<sub>top</sub> mentioned above, a chart for the circle.

### Atlases

The description of most manifolds requires more than one chart. A specific collection of charts which covers a manifold is called an *[atlas](https://en.wikipedia.org/wiki/Atlas_(topology) "Atlas (topology)")*. An atlas is not unique as all manifolds can be covered in multiple ways using different combinations of charts. Two atlases are said to be equivalent if their union is also an atlas.

The atlas containing all possible charts consistent with a given atlas is called the *maximal atlas* (i.e. an equivalence class containing that given atlas). Unlike an ordinary atlas, the maximal atlas of a given manifold is unique. Though useful for definitions, it is an abstract object and not used directly (e.g. in calculations).

A manifold can be defined as a topological space equipped with an atlas (and in some definitions, a maximal atlas).

### Transition maps

Charts in an atlas may overlap and a single point of a manifold may be represented in several charts. If two charts overlap, parts of them represent the same region of the manifold, just as a map of Europe and a map of Russia may both contain Moscow. Given two overlapping charts, a *transition function* can be defined which goes from an open ball in $\mathbb {R} ^{n}$ to the manifold and then back to another (or perhaps the same) open ball in $\mathbb {R} ^{n}$. The resultant map, like the map *T* in the circle example above, is called a *change of coordinates*, a *coordinate transformation*, a *transition function*, or a *transition map*.

### Additional structure

An atlas can also be used to define additional structure on the manifold. The structure is first defined on each chart separately. If all transition maps are compatible with this structure, the structure transfers to the manifold.

This is the standard way differentiable manifolds are defined. If the transition functions of an atlas for a topological manifold preserve the natural differential structure of $\mathbb {R} ^{n}$ (that is, if they are [diffeomorphisms](https://en.wikipedia.org/wiki/Diffeomorphism)), the differential structure transfers to the manifold and turns it into a differentiable manifold. [Complex manifolds](https://en.wikipedia.org/wiki/Complex_manifold) are introduced in an analogous way by requiring that the transition functions of an atlas are [holomorphic functions](https://en.wikipedia.org/wiki/Holomorphic_function). For [symplectic manifolds](https://en.wikipedia.org/wiki/Symplectic_manifold), the transition functions must be [symplectomorphisms](https://en.wikipedia.org/wiki/Symplectomorphism).

The structure on the manifold depends on the atlas, but sometimes different atlases can be said to give rise to the same structure. Such atlases are called *compatible*.

These notions are made precise in general through the use of [pseudogroups](https://en.wikipedia.org/wiki/Pseudogroup).

## Manifold with boundary

![[media/be5d14f356a604929611de8ca7740295c2126760.png]]
A smooth 2-manifold: The interior chart with transition map <em>φ</em><sub>1</sub> maps an open subset around an interior point to an open Euclidean subset, while the boundary chart with transition map <em>φ</em><sub>2</sub> maps a closed subset around a boundary point to a closed Euclidean subset. The boundary is itself a 1-manifold without boundary, so the chart with transition map <em>φ</em><sub>3</sub> must map to an open Euclidean subset.

A **manifold with boundary** is a manifold with an edge. For example, a [disk](https://en.wikipedia.org/wiki/Disk_(mathematics) "Disk (mathematics)") (circle plus interior) is a [2-manifold](https://en.wikipedia.org/wiki/2-manifold) with as boundary the circle, a [1-manifold](https://en.wikipedia.org/wiki/1-manifold). The boundary of an $n$-manifold with boundary is an $(n-1)$-manifold. In three dimensions, a [ball](https://en.wikipedia.org/wiki/Ball_(mathematics) "Ball (mathematics)") (sphere plus interior) is a 3-manifold with boundary. Its boundary is a sphere, a 2-manifold.

In technical language, a manifold with boundary is a space containing both interior points and boundary points. Every interior point has a neighborhood homeomorphic to the open $n$-ball $\textstyle \{(x_{1},x_{2},\dots ,x_{n})\mid \sum x_{i}^{2}<1\}$. Every boundary point has a neighborhood homeomorphic to the "half" $n$-ball $\textstyle \{(x_{1},x_{2},\dots ,x_{n})\mid \sum x_{i}^{2}<1{\text{ and }}x_{1}\geq 0\}$. Any homeomorphism between half-balls must send points with $x_{1}=0$ to points with $x_{1}=0$. This invariance allows to "define" boundary points; see next paragraph.

If in addition we are considering differentiable manifolds, then a [square](https://en.wikipedia.org/wiki/Square) with interior is not a manifold with boundary. The four vertices are neither locally diffeomorphic to Euclidean space nor to Euclidean half-space. This is an example of a differentiable manifold with corners. Similarly, products of differentiable manifolds with boundaries are not generally differentiable manifolds with boundaries, but instead are differentiable manifolds with corners.

### Boundary and interior

Let $M$ be a manifold with boundary. The **interior** of $M$, denoted $\operatorname {Int} M$, is the set of points in $M$ which have neighborhoods homeomorphic to an open subset of $\mathbb {R} ^{n}$. The **boundary** of $M$, denoted $\partial M$, is the [complement](https://en.wikipedia.org/wiki/Complement_(set_theory) "Complement (set theory)") of $\operatorname {Int} M$ in $M$. The boundary points can be characterized as those points which land on the boundary hyperplane $(x_{n}=0)$ of $\mathbb {R} _{+}^{n}$ under some coordinate chart.

If $M$ is a manifold with boundary of dimension $n$, then $\operatorname {Int} M$ is a manifold (without boundary) of dimension $n$ and $\partial M$ is a manifold (without boundary) of dimension $n-1$.

## Construction

A single manifold can be constructed in different ways, each stressing a different aspect of the manifold, thereby leading to a slightly different viewpoint.

### Charts

![[media/d134734cdc88d209da268641ccebec1948a1f20e.png]]
The chart maps the part of the sphere with positive <em>z</em> coordinate to a disc.

Perhaps the simplest way to construct a manifold is the one used in the example above of the circle. First, a subset of $\mathbb {R} ^{2}$ is identified, and then an atlas covering this subset is constructed. The concept of *manifold* grew historically from constructions like this. Here is another example, applying this method to the construction of a sphere:

#### Sphere with charts

A sphere can be treated in almost the same way as the circle. In mathematics a sphere is just the surface (not the solid interior), which can be defined as a subset of $\mathbb {R} ^{3}$: 

$$
S=\left\{(x,y,z)\in \mathbb {R} ^{3}\mid x^{2}+y^{2}+z^{2}=1\right\}.
$$

The sphere is two-dimensional, so each chart will map part of the sphere to an open subset of $\mathbb {R} ^{2}$. Consider the northern hemisphere, which is the part with positive *z* coordinate (coloured red in the picture on the right). The function χ defined by 

$$
\chi (x,y,z)=(x,y),\
$$

maps the northern hemisphere to the open [unit disc](https://en.wikipedia.org/wiki/Unit_disc) by projecting it on the (*x*, *y*) plane. A similar chart exists for the southern hemisphere. Together with two charts projecting on the (*x*, *z*) plane and two charts projecting on the (*y*, *z*) plane, an atlas of six charts is obtained which covers the entire sphere.

This can be easily generalized to higher-dimensional spheres.

### Patchwork

A manifold can be constructed by gluing together pieces in a consistent manner, making them into overlapping charts. This construction is possible for any manifold and hence it is often used as a characterisation, especially for differentiable and Riemannian manifolds. It focuses on an atlas, as the patches naturally provide charts, and since there is no exterior space involved it leads to an intrinsic view of the manifold.

The manifold is constructed by specifying an atlas, which is itself defined by transition maps. A point of the manifold is therefore an [equivalence class](https://en.wikipedia.org/wiki/Equivalence_class) of points which are mapped to each other by transition maps. Charts map equivalence classes to points of a single patch. There are usually strong demands on the consistency of the transition maps. For topological manifolds they are required to be homeomorphisms; if they are also diffeomorphisms, the resulting manifold is a differentiable manifold.

This can be illustrated with the transition map *t* = <sup>1</sup>⁄<sub>*s*</sub> from the second half of the circle example. Start with two copies of the line. Use the coordinate *s* for the first copy, and *t* for the second copy. Now, glue both copies together by identifying the point *t* on the second copy with the point *s* = <sup>1</sup>⁄<sub>*t*</sub> on the first copy (the points *t* = 0 and *s* = 0 are not identified with any point on the first and second copy, respectively). This gives a circle.

#### Intrinsic and extrinsic view

The first construction and this construction are very similar, but represent rather different points of view. In the first construction, the manifold is seen as [embedded](https://en.wikipedia.org/wiki/Embedding) in some Euclidean space. This is the *extrinsic view*. When a manifold is viewed in this way, it is easy to use intuition from Euclidean spaces to define additional structure. For example, in a Euclidean space, it is always clear whether a vector at some point is [tangential](https://en.wikipedia.org/wiki/Tangential) or [normal](https://en.wikipedia.org/wiki/Normal_vector) to some surface through that point.

The patchwork construction does not use any embedding, but simply views the manifold as a topological space by itself. This abstract point of view is called the *intrinsic view*. It can make it harder to imagine what a tangent vector might be, and there is no intrinsic notion of a [normal bundle](https://en.wikipedia.org/wiki/Normal_bundle), but instead there is an intrinsic [stable normal bundle](https://en.wikipedia.org/wiki/Stable_normal_bundle).

#### *n*-Sphere as a patchwork

The [n-sphere](https://en.wikipedia.org/wiki/Hypersphere) **S**<sup>*n*</sup> is a generalisation of the idea of a circle (1-sphere) and sphere (2-sphere) to higher dimensions. An *n*-sphere **S**<sup>*n*</sup> can be constructed by gluing together two copies of $\mathbb {R} ^{n}$. The transition map between them is [inversion in a sphere](https://en.wikipedia.org/wiki/Inversion_in_a_sphere), defined as 

$$
\mathbb {R} ^{n}\setminus \{0\}\to \mathbb {R} ^{n}\setminus \{0\}:x\mapsto x/\|x\|^{2}.
$$

This function is its own inverse and thus can be used in both directions. As the transition map is a [smooth function](https://en.wikipedia.org/wiki/Smooth_function), this atlas defines a smooth manifold. In the case *n* = 1, the example simplifies to the circle example given earlier.

### Identifying points of a manifold

It is possible to define different points of a manifold to be the same point. This can be visualized as gluing these points together in a single point, forming a [quotient space](https://en.wikipedia.org/wiki/Quotient_space_(topology) "Quotient space (topology)"). There is, however, no reason to expect such quotient spaces to be manifolds. Among the possible quotient spaces that are not necessarily manifolds, [orbifolds](https://en.wikipedia.org/wiki/Orbifold) and [CW complexes](https://en.wikipedia.org/wiki/CW_complex) are considered to be relatively [well-behaved](https://en.wikipedia.org/wiki/Well-behaved). An example of a quotient space of a manifold that is also a manifold is the [real projective space](https://en.wikipedia.org/wiki/Real_projective_space), identified as a quotient space of the corresponding sphere.

One method of identifying points (gluing them together) is through a right (or left) action of a [group](https://en.wikipedia.org/wiki/Group_(mathematics) "Group (mathematics)"), which [acts](https://en.wikipedia.org/wiki/Group_action_(mathematics)) on the manifold. Two points are identified if one is moved onto the other by some group element. If *M* is the manifold and *G* is the group, the resulting quotient space is denoted by *M* / *G* (or *G* \\ *M*).

Manifolds which can be constructed by identifying points include [tori](https://en.wikipedia.org/wiki/Torus#Topology) and [real projective spaces](https://en.wikipedia.org/wiki/Real_projective_space) (starting with a plane and a sphere, respectively).

### Gluing along boundaries

Two manifolds with boundaries can be glued together along a boundary. If this is done the right way, the result is also a manifold. Similarly, two boundaries of a single manifold can be glued together.

Formally, the gluing is defined by a [bijection](https://en.wikipedia.org/wiki/Bijection) between the two boundaries<sup>\[*[dubious](https://en.wikipedia.org/wiki/Wikipedia:Accuracy_dispute#Disputed_statement) – [discuss](https://en.wikipedia.org/wiki/Talk:Manifold#gluing_manifolds_with_boundary)*\]</sup>. Two points are identified when they are mapped onto each other. For a topological manifold, this bijection should be a homeomorphism, otherwise the result will not be a topological manifold. Similarly, for a differentiable manifold, it has to be a diffeomorphism. For other manifolds, other structures should be preserved.

A finite cylinder may be constructed as a manifold by starting with a strip \[0,1\] × \[0,1\] and gluing a pair of opposite edges on the boundary by a suitable diffeomorphism. A [projective plane](https://en.wikipedia.org/wiki/Projective_plane) may be obtained by gluing a sphere with a hole in it to a [Möbius strip](https://en.wikipedia.org/wiki/M%C3%B6bius_strip) along their respective circular boundaries.

###  Cartesian products

The [Cartesian product](https://en.wikipedia.org/wiki/Cartesian_product) of manifolds is also a manifold.

The dimension of the product manifold is the sum of the dimensions of its factors. Its topology is the [product topology](https://en.wikipedia.org/wiki/Product_topology), and a Cartesian product of charts is a chart for the product manifold. Thus, an atlas for the product manifold can be constructed using atlases for its factors. If these atlases define a differential structure on the factors, the corresponding atlas defines a differential structure on the product manifold. The same is true for any other structure defined on the factors. If one of the factors has a boundary, the product manifold also has a boundary. Cartesian products may be used to construct tori and finite [cylinders](https://en.wikipedia.org/wiki/Cylinder_(geometry)), for example, as **S**<sup>1</sup> × **S**<sup>1</sup> and **S**<sup>1</sup> × \[0,1\], respectively.

![[media/71cb8f69d6be0aa37416cc1ad0e9019dd3f9506b.png]]
A finite cylinder is a manifold with boundary.

## History

The study of manifolds combines many important areas of mathematics: it generalizes concepts such as [curves](https://en.wikipedia.org/wiki/Curve) and surfaces as well as ideas from [linear algebra](https://en.wikipedia.org/wiki/Linear_algebra) and topology.

### Early development

Before the modern concept of a manifold there were several important results.

[Non-Euclidean geometry](https://en.wikipedia.org/wiki/Non-Euclidean_geometry) considers spaces where [Euclid](https://en.wikipedia.org/wiki/Euclid)'s [parallel postulate](https://en.wikipedia.org/wiki/Parallel_postulate) fails. [Saccheri](https://en.wikipedia.org/wiki/Giovanni_Gerolamo_Saccheri) first studied such geometries in 1733, but sought only to disprove them. [Gauss](https://en.wikipedia.org/wiki/Carl_Friedrich_Gauss), [Bolyai](https://en.wikipedia.org/wiki/J%C3%A1nos_Bolyai) and [Lobachevsky](https://en.wikipedia.org/wiki/Nikolai_Ivanovich_Lobachevsky) independently discovered them 100 years later. Their research uncovered two types of spaces whose geometric structures differ from that of classical Euclidean space; these gave rise to [hyperbolic geometry](https://en.wikipedia.org/wiki/Hyperbolic_geometry) and [elliptic geometry](https://en.wikipedia.org/wiki/Elliptic_geometry). In the modern theory of manifolds, these notions correspond to Riemannian manifolds with constant negative and positive [curvature](https://en.wikipedia.org/wiki/Curvature), respectively.

Carl Friedrich Gauss may have been the first to consider abstract spaces as mathematical objects in their own right. His [theorema egregium](https://en.wikipedia.org/wiki/Theorema_egregium) gives a method for computing the curvature of a [surface](https://en.wikipedia.org/wiki/Surface_(topology) "Surface (topology)") without considering the [ambient space](https://en.wikipedia.org/wiki/Ambient_space) in which the surface lies. Such a surface would, in modern terminology, be called a manifold; and in modern terms, the theorem proved that the curvature of the surface is an [intrinsic property](https://en.wikipedia.org/wiki/Intrinsic_and_extrinsic_properties). Manifold theory has come to focus exclusively on these intrinsic properties (or invariants), while largely ignoring the extrinsic properties of the ambient space.

Another, more topological example of an intrinsic [property](https://en.wikipedia.org/wiki/Topological_property) of a manifold is its [Euler characteristic](https://en.wikipedia.org/wiki/Euler_characteristic). [Leonhard Euler](https://en.wikipedia.org/wiki/Leonhard_Euler) showed that for a convex [polytope](https://en.wikipedia.org/wiki/Polytope) in the three-dimensional Euclidean space with *V* [vertices](https://en.wikipedia.org/wiki/Vertex_(geometry) "Vertex (geometry)") (or corners), *E* edges, and *F* faces,

$$
V-E+F=2.\
$$

The same formula will hold if we project the vertices and edges of the polytope onto a sphere, creating a [topological map](https://en.wikipedia.org/wiki/Topological_map) with *V* vertices, *E* edges, and *F* faces, and in fact, will remain true for any spherical map, even if it does not arise from any convex polytope. Thus 2 is a topological invariant of the sphere, called its **Euler characteristic**. On the other hand, a [torus](https://en.wikipedia.org/wiki/Torus) can be sliced open by its 'parallel' and 'meridian' circles, creating a map with *V* = 1 vertex, *E* = 2 edges, and *F* = 1 face. Thus the Euler characteristic of the torus is 1 − 2 + 1 = 0. The Euler characteristic of other surfaces is a useful [topological invariant](https://en.wikipedia.org/wiki/Topological_invariant), which can be extended to higher dimensions using [Betti numbers](https://en.wikipedia.org/wiki/Betti_number). In the mid nineteenth century, the [Gauss–Bonnet theorem](https://en.wikipedia.org/wiki/Gauss%E2%80%93Bonnet_theorem) linked the Euler characteristic to the [Gaussian curvature](https://en.wikipedia.org/wiki/Gaussian_curvature).

### Synthesis

Investigations of [Niels Henrik Abel](https://en.wikipedia.org/wiki/Niels_Henrik_Abel) and [Carl Gustav Jacobi](https://en.wikipedia.org/wiki/Carl_Gustav_Jacobi) on inversion of [elliptic integrals](https://en.wikipedia.org/wiki/Elliptic_integral) in the first half of 19th century led them to consider special types of complex manifolds, now known as [Jacobians](https://en.wikipedia.org/wiki/Abelian_variety). [Bernhard Riemann](https://en.wikipedia.org/wiki/Bernhard_Riemann) further contributed to their theory, clarifying the geometric meaning of the process of [analytic continuation](https://en.wikipedia.org/wiki/Analytic_continuation) of functions of complex variables.

Riemann was the first one to do extensive work generalizing the idea of a surface to higher dimensions. The name *manifold* comes from Riemann's original [German](https://en.wikipedia.org/wiki/German_language) term, *Mannigfaltigkeit*, which [William Kingdon Clifford](https://en.wikipedia.org/wiki/William_Kingdon_Clifford) translated as "manifoldness". In his Göttingen inaugural lecture, Riemann described the set of all possible values of a variable with certain constraints as a *Mannigfaltigkeit*, because the variable can have *many* values. He distinguishes between *stetige Mannigfaltigkeit* and *diskrete* *Mannigfaltigkeit* (*continuous manifoldness* and *discontinuous manifoldness*), depending on whether the value changes continuously or not. As continuous examples, Riemann refers to not only colors and the locations of objects in space, but also the possible shapes of a spatial figure. Using [induction](https://en.wikipedia.org/wiki/Mathematical_induction), Riemann constructs an *n-fach ausgedehnte Mannigfaltigkeit* (*n times extended manifoldness* or *n-dimensional manifoldness*) as a continuous stack of (n−1) dimensional manifoldnesses. Riemann's intuitive notion of a *Mannigfaltigkeit* evolved into what is today formalized as a manifold. Riemannian manifolds and [Riemann surfaces](https://en.wikipedia.org/wiki/Riemann_surface) are named after Riemann.

### Poincaré's definition

In his very influential paper, [Analysis Situs](https://en.wikipedia.org/wiki/Analysis_Situs_(paper) "Analysis Situs (paper)"), Henri Poincaré gave a definition of a differentiable manifold (*variété*) which served as a precursor to the modern concept of a manifold.

In the first section of Analysis Situs, Poincaré defines a manifold as the [level set](https://en.wikipedia.org/wiki/Level_set) of a [continuously differentiable](https://en.wikipedia.org/wiki/Continuously_differentiable) function between Euclidean spaces that satisfies the nondegeneracy hypothesis of the [[Implicit Function Theorem]]. In the third section, he begins by remarking that the [graph](https://en.wikipedia.org/wiki/Graph_of_a_function) of a continuously differentiable function is a manifold in the latter sense. He then proposes a new, more general, definition of manifold based on a 'chain of manifolds' (*une chaîne des variétés*).

Poincaré's notion of a *chain of manifolds* is a precursor to the modern notion of atlas. In particular, he considers two manifolds defined respectively as graphs of functions $\theta (y)$ and $\theta '\left(y'\right)$. If these manifolds overlap (*a une partie commune*), then he requires that the coordinates $y$ depend continuously differentiably on the coordinates $y'$ and vice versa ('*...les $y$ sont fonctions analytiques des $y'$ et inversement*'). In this way he introduces a precursor to the notion of a [chart](#Charts) and of a [transition map](#Transition_maps).

For example, the unit circle in the plane can be thought of as the graph of the function $y={\sqrt {1-x^{2}}}$ or else the function $y=-{\sqrt {1-x^{2}}}$ in a neighborhood of every point except the points (1, 0) and (−1, 0); and in a neighborhood of those points, it can be thought of as the graph of, respectively, $x={\sqrt {1-y^{2}}}$ and $x=-{\sqrt {1-y^{2}}}$. The circle can be represented by a graph in the neighborhood of every point because the left hand side of its defining equation $x^{2}+y^{2}-1=0$ has nonzero gradient at every point of the circle. By the [[Implicit Function Theorem]], every [submanifold](https://en.wikipedia.org/wiki/Submanifold) of Euclidean space is locally the graph of a function.

[Hermann Weyl](https://en.wikipedia.org/wiki/Hermann_Weyl) gave an intrinsic definition for differentiable manifolds in his lecture course on Riemann surfaces in 1911–1912, opening the road to the general concept of a [topological space](https://en.wikipedia.org/wiki/Topological_space) that followed shortly. During the 1930s [Hassler Whitney](https://en.wikipedia.org/wiki/Hassler_Whitney) and others clarified the [foundational](https://en.wikipedia.org/wiki/Foundations_of_mathematics) aspects of the subject, and thus intuitions dating back to the latter half of the 19th century became precise, and developed through [differential geometry](https://en.wikipedia.org/wiki/Differential_geometry) and [Lie group](https://en.wikipedia.org/wiki/Lie_group) theory. Notably, the [Whitney embedding theorem](https://en.wikipedia.org/wiki/Whitney_embedding_theorem) showed that the intrinsic definition in terms of charts was equivalent to Poincaré's definition in terms of subsets of Euclidean space.

### Topology of manifolds: highlights

Two-dimensional manifolds, also known as a 2D *surfaces* embedded in our common 3D space, were considered by Riemann under the guise of [Riemann surfaces](https://en.wikipedia.org/wiki/Riemann_surface), and rigorously classified in the beginning of the 20th century by [Poul Heegaard](https://en.wikipedia.org/wiki/Poul_Heegaard) and [Max Dehn](https://en.wikipedia.org/wiki/Max_Dehn). Poincaré pioneered the study of three-dimensional manifolds and raised a fundamental question about them, today known as the [Poincaré conjecture](https://en.wikipedia.org/wiki/Poincar%C3%A9_conjecture). After nearly a century, [Grigori Perelman](https://en.wikipedia.org/wiki/Grigori_Perelman) proved the Poincaré conjecture (see the [Solution of the Poincaré conjecture](https://en.wikipedia.org/wiki/Poincar%C3%A9_conjecture#Solution)). [William Thurston](https://en.wikipedia.org/wiki/William_Thurston)'s [geometrization program](https://en.wikipedia.org/wiki/Geometrization_conjecture), formulated in the 1970s, provided a far-reaching extension of the Poincaré conjecture to the general three-dimensional manifolds. Four-dimensional manifolds were brought to the forefront of mathematical research in the 1980s by [Michael Freedman](https://en.wikipedia.org/wiki/Michael_Freedman) and in a different setting, by [Simon Donaldson](https://en.wikipedia.org/wiki/Simon_Donaldson), who was motivated by the then recent progress in theoretical physics ([Yang–Mills theory](https://en.wikipedia.org/wiki/Yang%E2%80%93Mills_theory)), where they serve as a substitute for ordinary 'flat' [spacetime](https://en.wikipedia.org/wiki/Spacetime). [Andrey Markov Jr.](https://en.wikipedia.org/wiki/Andrey_Markov_(Soviet_mathematician)) showed in 1960 that no algorithm exists for classifying four-dimensional manifolds. Important work on higher-dimensional manifolds, including [analogues of the Poincaré conjecture](https://en.wikipedia.org/wiki/Generalized_Poincar%C3%A9_conjecture), had been done earlier by [René Thom](https://en.wikipedia.org/wiki/Ren%C3%A9_Thom), [John Milnor](https://en.wikipedia.org/wiki/John_Milnor), [Stephen Smale](https://en.wikipedia.org/wiki/Stephen_Smale) and [Sergei Novikov](https://en.wikipedia.org/wiki/Sergei_Novikov_(mathematician) "Sergei Novikov (mathematician)"). A very pervasive and flexible technique underlying much work on the [topology of manifolds](https://en.wikipedia.org/wiki/Differential_topology) is [Morse theory](https://en.wikipedia.org/wiki/Morse_theory).

## Additional structure

### Topological manifolds

The simplest kind of manifold to define is the topological manifold, which looks locally like some "ordinary" Euclidean space $\mathbb {R} ^{n}$. By definition, all manifolds are topological manifolds, so the phrase "topological manifold" is usually used to emphasize that a manifold lacks additional structure, or that only its topological properties are being considered. Formally, a topological manifold is a topological space [locally homeomorphic](https://en.wikipedia.org/wiki/Local_homeomorphism) to a Euclidean space. This means that every point has a neighbourhood for which there exists a [homeomorphism](https://en.wikipedia.org/wiki/Homeomorphism) (a [bijective](https://en.wikipedia.org/wiki/Bijection) [continuous function](https://en.wikipedia.org/wiki/Continuous_function_(topology)) whose inverse is also continuous) mapping that neighbourhood to $\mathbb {R} ^{n}$. These homeomorphisms are the charts of the manifold.

A *topological* manifold looks locally like a Euclidean space in a rather weak manner: while for each individual chart it is possible to distinguish differentiable functions or measure distances and angles, merely by virtue of being a topological manifold a space does not have any *particular* and *consistent* choice of such concepts. In order to discuss such properties for a manifold, one needs to specify further structure and consider [differentiable manifolds](#Differentiable_manifolds) and [Riemannian manifolds](#Riemannian_manifolds) discussed below. In particular, the same underlying topological manifold can have several mutually incompatible classes of differentiable functions and an infinite number of ways to specify distances and angles.

Usually additional technical assumptions on the topological space are made to exclude pathological cases. It is customary to require that the space be [Hausdorff](https://en.wikipedia.org/wiki/Hausdorff_space) and [second countable](https://en.wikipedia.org/wiki/Second-countable_space).

The *dimension* of the manifold at a certain point is the dimension of the Euclidean space that the charts at that point map to (number *n* in the definition). All points in a [connected](https://en.wikipedia.org/wiki/Connected_space) manifold have the same dimension. Some authors require that all charts of a topological manifold map to Euclidean spaces of same dimension. In that case every topological manifold has a topological invariant, its dimension.

### Differentiable manifolds

For most applications, a special kind of topological manifold, namely, a **differentiable manifold**, is used. If the local charts on a manifold are compatible in a certain sense, one can define directions, tangent spaces, and differentiable functions on that manifold. In particular it is possible to use [calculus](https://en.wikipedia.org/wiki/Calculus) on a differentiable manifold. Each point of an *n*-dimensional differentiable manifold has a [[Tangent Space]]. This is an *n*-dimensional Euclidean space consisting of the [tangent vectors](https://en.wikipedia.org/wiki/Tangent_vectors) of the curves through the point.

Two important classes of differentiable manifolds are **smooth** and **[analytic manifolds](https://en.wikipedia.org/wiki/Analytic_manifold)**. For smooth manifolds the transition maps are smooth, that is, infinitely differentiable. Analytic manifolds are smooth manifolds with the additional condition that the transition maps are [analytic](https://en.wikipedia.org/wiki/Analytic_function) (they can be expressed as [power series](https://en.wikipedia.org/wiki/Power_series)). The sphere can be given analytic structure, as can most familiar curves and surfaces.

A [rectifiable set](https://en.wikipedia.org/wiki/Rectifiable_set) generalizes the idea of a piecewise smooth or [rectifiable curve](https://en.wikipedia.org/wiki/Rectifiable_curve) to higher dimensions; however, rectifiable sets are not in general manifolds.

### Riemannian manifolds

To measure distances and angles on manifolds, the manifold must be Riemannian. A *Riemannian manifold* is a differentiable manifold in which each [[Tangent Space]] is equipped with an [inner product](https://en.wikipedia.org/wiki/Inner_product_space) $\langle \cdot ,\cdot \rangle$ in a manner which varies smoothly from point to point. Given two tangent vectors $u$ and $v$, the inner product $\langle u,v\rangle$ gives a real number. The [dot](https://en.wikipedia.org/wiki/Dot_product) (or scalar) product is a typical example of an inner product. This allows one to define various notions such as length, [angles](https://en.wikipedia.org/wiki/Angle), [areas](https://en.wikipedia.org/wiki/Area) (or [volumes](https://en.wikipedia.org/wiki/Volume)), [curvature](https://en.wikipedia.org/wiki/Curvature) and [divergence](https://en.wikipedia.org/wiki/Divergence) of [vector fields](https://en.wikipedia.org/wiki/Vector_field).

All differentiable manifolds (of constant dimension) can be given the structure of a Riemannian manifold. The Euclidean space itself carries a natural structure of Riemannian manifold (the tangent spaces are naturally identified with the Euclidean space itself and carry the standard scalar product of the space). Many familiar curves and surfaces, including for example all *n*-spheres, are specified as subspaces of a Euclidean space and inherit a metric from their embedding in it.

### Finsler manifolds

A **Finsler manifold** allows the definition of distance but does not require the concept of angle; it is an analytic manifold in which each tangent space is equipped with a [norm](https://en.wikipedia.org/wiki/Normed_space), $\|\cdot \|$, in a manner which varies smoothly from point to point. This norm can be extended to a [metric](https://en.wikipedia.org/wiki/Metric_(mathematics)), defining the length of a curve; but it cannot in general be used to define an inner product.

Any Riemannian manifold is a Finsler manifold.

### Lie groups

**Lie groups**, named after [Sophus Lie](https://en.wikipedia.org/wiki/Sophus_Lie), are differentiable manifolds that carry also the structure of a [group](https://en.wikipedia.org/wiki/Group_(mathematics) "Group (mathematics)") which is such that the group operations are defined by smooth maps.

A Euclidean vector space with the group operation of vector addition is an example of a non-compact Lie group. A simple example of a [compact](https://en.wikipedia.org/wiki/Compact_space) Lie group is the circle: the group operation is simply rotation. This group, known as $\operatorname {U} (1)$, can be also characterised as the group of [complex numbers](https://en.wikipedia.org/wiki/Complex_number) of [modulus](https://en.wikipedia.org/wiki/Absolute_value) 1 with multiplication as the group operation.

Other examples of Lie groups include special groups of [matrices](https://en.wikipedia.org/wiki/Matrix_(mathematics) "Matrix (mathematics)"), which are all subgroups of the [general linear group](https://en.wikipedia.org/wiki/General_linear_group), the group of $n\times n$ matrices with non-zero determinant. If the matrix entries are [real numbers](https://en.wikipedia.org/wiki/Real_number), this will be an $n^{2}$-dimensional disconnected manifold. The [orthogonal groups](https://en.wikipedia.org/wiki/Orthogonal_group), the [symmetry groups](https://en.wikipedia.org/wiki/Symmetry_group) of the sphere and [hyperspheres](https://en.wikipedia.org/wiki/Hypersphere), are $n(n-1)/2$ dimensional manifolds, where $n-1$ is the dimension of the sphere. Further examples can be found in the [table of Lie groups](https://en.wikipedia.org/wiki/Table_of_Lie_groups).

### Other types of manifolds

- A *[complex manifold](https://en.wikipedia.org/wiki/Complex_manifold)* is a manifold whose charts take values in $\mathbb {C} ^{n}$ and whose transition functions are [holomorphic](https://en.wikipedia.org/wiki/Holomorphic_function) on the overlaps. These manifolds are the basic objects of study in [complex geometry](https://en.wikipedia.org/wiki/Complex_geometry). A one-complex-dimensional manifold is called a [Riemann surface](https://en.wikipedia.org/wiki/Riemann_surface). An $n$-dimensional complex manifold has dimension $2n$ as a real differentiable manifold.
- A *[CR manifold](https://en.wikipedia.org/wiki/CR_manifold)* is a manifold modeled on boundaries of domains in $\mathbb {C} ^{n}$.
- 'Infinite dimensional manifolds': to allow for infinite dimensions, one may consider [Banach manifolds](https://en.wikipedia.org/wiki/Banach_manifold) which are locally homeomorphic to [Banach spaces](https://en.wikipedia.org/wiki/Banach_space). Similarly, Fréchet manifolds are locally homeomorphic to [Fréchet spaces](https://en.wikipedia.org/wiki/Fr%C3%A9chet_space).
- A *[symplectic manifold](https://en.wikipedia.org/wiki/Symplectic_manifold)* is a kind of manifold which is used to represent the phase spaces in [classical mechanics](https://en.wikipedia.org/wiki/Classical_mechanics). They are endowed with a [2-form](https://en.wikipedia.org/wiki/Differential_form) that defines the [Poisson bracket](https://en.wikipedia.org/wiki/Poisson_bracket). A closely related type of manifold is a [contact manifold](https://en.wikipedia.org/wiki/Contact_geometry).
- A *[combinatorial manifold](https://en.wikipedia.org/wiki/Combinatorial_manifold)* is a kind of manifold which is discretization of a manifold. It usually means a [piecewise linear manifold](https://en.wikipedia.org/wiki/Piecewise_linear_manifold) made by [simplicial complexes](https://en.wikipedia.org/wiki/Simplicial_complexes).
- A *[digital manifold](https://en.wikipedia.org/wiki/Digital_manifold)* is a special kind of combinatorial manifold which is defined in digital space. See [digital topology](https://en.wikipedia.org/wiki/Digital_topology).

## Classification and invariants

Different notions of manifolds have different notions of classification and invariant; in this section we focus on smooth closed manifolds.

The classification of smooth closed manifolds is well understood *in principle*, except in [dimension 4](https://en.wikipedia.org/wiki/4-manifold): in low dimensions (2 and 3) it is geometric, via the [uniformization theorem](https://en.wikipedia.org/wiki/Uniformization_theorem) and the [solution of the Poincaré conjecture](https://en.wikipedia.org/wiki/Solution_of_the_Poincar%C3%A9_conjecture), and in high dimension (5 and above) it is algebraic, via [surgery theory](https://en.wikipedia.org/wiki/Surgery_theory). This is a classification in principle: the general question of whether two smooth manifolds are diffeomorphic is not computable in general. Further, specific computations remain difficult, and there are many open questions.

Orientable surfaces can be visualized, and their diffeomorphism classes enumerated, by genus. Given two orientable surfaces, one can determine if they are diffeomorphic by computing their respective genera and comparing: they are diffeomorphic if and only if the genera are equal, so the genus forms a [complete set of invariants](https://en.wikipedia.org/wiki/Complete_set_of_invariants).

This is much harder in higher dimensions: higher-dimensional manifolds cannot be directly visualized (though visual intuition is useful in understanding them), nor can their diffeomorphism classes be enumerated, nor can one in general determine if two different descriptions of a higher-dimensional manifold refer to the same object.

However, one can determine if two manifolds are *different* if there is some intrinsic characteristic that differentiates them. Such criteria are commonly referred to as **[invariants](https://en.wikipedia.org/wiki/Invariant_(mathematics) "Invariant (mathematics)")**, because, while they may be defined in terms of some presentation (such as the genus in terms of a triangulation), they are the same relative to all possible descriptions of a particular manifold: they are *invariant* under different descriptions.

One could hope to develop an arsenal of invariant criteria that would definitively classify all manifolds up to isomorphism. It is known that for manifolds of dimension 4 and higher, [no program exists](https://en.wikipedia.org/wiki/Classification_of_manifolds#Computability) that can decide whether two manifolds are diffeomorphic.

Smooth manifolds have [a rich set of invariants](https://en.wikipedia.org/wiki/Classification_of_manifolds#Enumeration_versus_invariants), coming from [point-set topology](https://en.wikipedia.org/wiki/Point-set_topology), classic algebraic topology, and [geometric topology](https://en.wikipedia.org/wiki/Geometric_topology). The most familiar invariants, which are visible for surfaces, are [orientability](https://en.wikipedia.org/wiki/Orientability) (a normal invariant, also detected by [homology](https://en.wikipedia.org/wiki/Singular_homology)) and [genus](https://en.wikipedia.org/wiki/Genus_(mathematics) "Genus (mathematics)") (a homological invariant).

Smooth closed manifolds have no local invariants (other than dimension), though geometric manifolds have local invariants, notably the [curvature of a Riemannian manifold](https://en.wikipedia.org/wiki/Curvature_of_Riemannian_manifolds) and the [torsion](https://en.wikipedia.org/wiki/Torsion_(differential_geometry)) of a manifold equipped with an [affine connection](https://en.wikipedia.org/wiki/Affine_connection). This distinction between local invariants and no local invariants is a common way to distinguish between geometry and topology. All invariants of a smooth closed manifold are thus global.

[Algebraic topology](https://en.wikipedia.org/wiki/Algebraic_topology) is a source of a number of important global invariant properties. Some key criteria include the *[simply connected](https://en.wikipedia.org/wiki/Simply_connected)* property and orientability (see below). Indeed, several branches of mathematics, such as [homology](https://en.wikipedia.org/wiki/Homology_(mathematics) "Homology (mathematics)") and [homotopy](https://en.wikipedia.org/wiki/Homotopy) theory, and the theory of [characteristic classes](https://en.wikipedia.org/wiki/Characteristic_classes) were founded in order to study invariant properties of manifolds.

## Surfaces

### Orientability

In dimensions two and higher, a simple but important invariant criterion is the question of whether a manifold admits a meaningful orientation. Consider a topological manifold with charts mapping to $\mathbb {R} ^{n}$. Given an [ordered basis](https://en.wikipedia.org/wiki/Basis_(linear_algebra)#Ordered_bases_and_coordinates "Basis (linear algebra)") for $\mathbb {R} ^{n}$, a chart causes its piece of the manifold to itself acquire a sense of ordering, which in 3-dimensions can be viewed as either right-handed or left-handed. Overlapping charts are not required to agree in their sense of ordering, which gives manifolds an important freedom. For some manifolds, like the sphere, charts can be chosen so that overlapping regions agree on their "handedness"; these are *[orientable](https://en.wikipedia.org/wiki/Orientability)* manifolds. For others, this is impossible. The latter possibility is easy to overlook, because any closed surface embedded (without self-intersection) in three-dimensional space is orientable.

Some illustrative examples of non-orientable manifolds include: (1) the [Möbius strip](https://en.wikipedia.org/wiki/M%C3%B6bius_strip), which is a manifold with boundary, (2) the [Klein bottle](https://en.wikipedia.org/wiki/Klein_bottle), which must intersect itself in its 3-space representation, and (3) the [real projective plane](https://en.wikipedia.org/wiki/Real_projective_plane), which arises naturally in geometry.

#### Möbius strip

![[media/710ad81d41b9d9c992d0bf60ffa199f397892fc9.png]]
Möbius strip

Begin with an infinite circular cylinder standing vertically, a manifold without boundary. Slice across it high and low to produce two circular boundaries, and the cylindrical strip between them. This is an orientable manifold with boundary, upon which "surgery" will be performed. Slice the strip open, so that it could unroll to become a rectangle, but keep a grasp on the cut ends. Twist one end 180°, making the inner surface face out, and glue the ends back together seamlessly. This results in a strip with a permanent half-twist: the Möbius strip. Its boundary is no longer a pair of circles, but (topologically) a single circle; and what was once its "inside" has merged with its "outside", so that it now has only a *single* side. Similarly to the Klein Bottle below, this two dimensional surface would need to intersect itself in two dimensions, but can easily be constructed in three or more dimensions.

#### Klein bottle

Take two Möbius strips; each has a single loop as a boundary. Straighten out those loops into circles, and let the strips distort into [cross-caps](https://en.wikipedia.org/wiki/Cross-cap). Gluing the circles together will produce a new, closed manifold without boundary, the Klein bottle. Closing the surface does nothing to improve the lack of orientability, it merely removes the boundary. Thus, the Klein bottle is a closed surface with no distinction between inside and outside. In three-dimensional space, a Klein bottle's surface must pass through itself. Building a Klein bottle which is not self-intersecting requires four or more dimensions of space.

#### Real projective plane

![[media/477f910aa768c8026ff4b57ada2a6d2e209af212.png]]
The [real projective plane](https://en.wikipedia.org/wiki/Real_projective_plane) is a two-dimensional manifold that cannot be realized in three dimensions without self-intersection, shown here as [Boy's surface](https://en.wikipedia.org/wiki/Boy%27s_surface).

Begin with a sphere centered on the origin. Every line through the origin pierces the sphere in two opposite points called *antipodes*. Although there is no way to do so physically, it is possible (by considering a [quotient space](https://en.wikipedia.org/wiki/Quotient_space_(topology) "Quotient space (topology)")) to mathematically merge each antipode pair into a single point. The closed surface so produced is the real projective plane, yet another non-orientable surface. It has a number of equivalent descriptions and constructions, but this route explains its name: all the points on any given line through the origin project to the same "point" on this "plane".

### Genus and the Euler characteristic

For two dimensional manifolds a key invariant property is the [genus](https://en.wikipedia.org/wiki/Genus_(mathematics) "Genus (mathematics)"), or "number of handles" present in a surface. A torus is a sphere with one handle, a double torus is a sphere with two handles, and so on. Indeed, it is possible to fully characterize compact, two-dimensional manifolds on the basis of genus and orientability. In higher-dimensional manifolds genus is replaced by the notion of [Euler characteristic](https://en.wikipedia.org/wiki/Euler_characteristic), and more generally [Betti numbers](https://en.wikipedia.org/wiki/Betti_number) and [homology](https://en.wikipedia.org/wiki/Homology_(mathematics) "Homology (mathematics)") and [cohomology](https://en.wikipedia.org/wiki/Cohomology).

## Maps of manifolds

![[media/0d8448f6d520c8b93effd766d41f59f0df3c2b7e.png]]
A [Morin surface](https://en.wikipedia.org/wiki/Morin_surface), an [immersion](https://en.wikipedia.org/wiki/Immersion_(mathematics)) used in [sphere eversion](https://en.wikipedia.org/wiki/Sphere_eversion)

Just as there are various types of manifolds, there are various types of [maps of manifolds](https://en.wikipedia.org/wiki/Maps_of_manifolds). In addition to continuous functions and smooth functions generally, there are maps with special properties. In [geometric topology](https://en.wikipedia.org/wiki/Geometric_topology) a basic type are [embeddings](https://en.wikipedia.org/wiki/Embedding), of which [knot theory](https://en.wikipedia.org/wiki/Knot_theory) is a central example, and generalizations such as [immersions](https://en.wikipedia.org/wiki/Immersion_(mathematics) "Immersion (mathematics)"), [submersions](https://en.wikipedia.org/wiki/Submersion_(mathematics) "Submersion (mathematics)"), [covering spaces](https://en.wikipedia.org/wiki/Covering_space), and [ramified covering spaces](https://en.wikipedia.org/wiki/Ramified_covering_space). Basic results include the [Whitney embedding theorem](https://en.wikipedia.org/wiki/Whitney_embedding_theorem) and [Whitney immersion theorem](https://en.wikipedia.org/wiki/Whitney_immersion_theorem).

In Riemannian geometry, one may ask for maps to preserve the Riemannian metric, leading to notions of [isometric embeddings](https://en.wikipedia.org/wiki/Isometric_embedding), [isometric immersions](https://en.wikipedia.org/wiki/Isometric_immersion), and [Riemannian submersions](https://en.wikipedia.org/wiki/Riemannian_submersion); a basic result is the [Nash embedding theorem](https://en.wikipedia.org/wiki/Nash_embedding_theorem).

### Scalar-valued functions

![[media/5cff1b76c880ddc0c2782685e13ae7f76a4fe350.png]]
3D color plot of the [spherical harmonics](https://en.wikipedia.org/wiki/Spherical_harmonics) of degree $n=5$

A basic example of maps between manifolds are scalar-valued functions on a manifold, 

$$
f\colon M\to \mathbb {R}
$$

 or 

$$
f\colon M\to \mathbb {C} ,
$$

sometimes called [regular functions](https://en.wikipedia.org/wiki/Regular_function) or [functionals](https://en.wikipedia.org/wiki/Functional_(mathematics) "Functional (mathematics)"), by analogy with algebraic geometry or linear algebra. These are of interest both in their own right, and to study the underlying manifold.

In geometric topology, most commonly studied are [Morse functions](https://en.wikipedia.org/wiki/Morse_function), which yield [handlebody](https://en.wikipedia.org/wiki/Handlebody) decompositions, while in [mathematical analysis](https://en.wikipedia.org/wiki/Mathematical_analysis), one often studies solution to [partial differential equations](https://en.wikipedia.org/wiki/Partial_differential_equations), an important example of which is [harmonic analysis](https://en.wikipedia.org/wiki/Harmonic_analysis), where one studies [harmonic functions](https://en.wikipedia.org/wiki/Harmonic_function): the kernel of the [Laplace operator](https://en.wikipedia.org/wiki/Laplace_operator). This leads to such functions as the [spherical harmonics](https://en.wikipedia.org/wiki/Spherical_harmonics), and to [heat kernel](https://en.wikipedia.org/wiki/Heat_kernel) methods of studying manifolds, such as [hearing the shape of a drum](https://en.wikipedia.org/wiki/Hearing_the_shape_of_a_drum) and some proofs of the [Atiyah–Singer index theorem](https://en.wikipedia.org/wiki/Atiyah%E2%80%93Singer_index_theorem).

## Generalizations of manifolds

Infinite dimensional manifolds  
The definition of a manifold can be generalized by dropping the requirement of finite dimensionality. Thus an infinite dimensional manifold is a topological space locally homeomorphic to a [topological vector space](https://en.wikipedia.org/wiki/Topological_vector_space) over the reals. This omits the point-set axioms, allowing higher cardinalities and [non-Hausdorff manifolds](https://en.wikipedia.org/wiki/Non-Hausdorff_manifold); and it omits finite dimension, allowing structures such as [Hilbert manifolds](https://en.wikipedia.org/wiki/Hilbert_manifold) to be modeled on [Hilbert spaces](https://en.wikipedia.org/wiki/Hilbert_spaces), [Banach manifolds](https://en.wikipedia.org/wiki/Banach_manifold) to be modeled on [Banach spaces](https://en.wikipedia.org/wiki/Banach_space), and [Fréchet manifolds](https://en.wikipedia.org/wiki/Fr%C3%A9chet_manifold) to be modeled on [Fréchet spaces](https://en.wikipedia.org/wiki/Fr%C3%A9chet_space). Usually one relaxes one or the other condition: manifolds with the point-set axioms are studied in [general topology](https://en.wikipedia.org/wiki/General_topology), while infinite-dimensional manifolds are studied in [functional analysis](https://en.wikipedia.org/wiki/Functional_analysis).

Orbifolds  
An [orbifold](https://en.wikipedia.org/wiki/Orbifold) is a generalization of manifold allowing for certain kinds of "[singularities](https://en.wikipedia.org/wiki/Mathematical_singularity)" in the topology. Roughly speaking, it is a space which locally looks like the quotients of some simple space (*e.g.* Euclidean space) by the [actions](https://en.wikipedia.org/wiki/Group_action_(mathematics)) of various [finite groups](https://en.wikipedia.org/wiki/Finite_group). The singularities correspond to fixed points of the group actions, and the actions must be compatible in a certain sense.

Algebraic varieties and schemes  
[Non-singular](https://en.wikipedia.org/wiki/Algebraic_curve#Singularities) algebraic varieties over the real or complex numbers are manifolds. One generalizes this first by allowing singularities, secondly by allowing different fields, and thirdly by emulating the patching construction of manifolds: just as a manifold is glued together from open subsets of Euclidean space, an [algebraic variety](https://en.wikipedia.org/wiki/Algebraic_variety) is glued together from affine algebraic varieties, which are zero sets of polynomials over algebraically closed fields. [Schemes](https://en.wikipedia.org/wiki/Scheme_(mathematics) "Scheme (mathematics)") are likewise glued together from affine schemes, which are a generalization of algebraic varieties. Both are related to manifolds, but are constructed algebraically using [sheaves](https://en.wikipedia.org/wiki/Sheaf_(mathematics) "Sheaf (mathematics)") instead of atlases.

Because of [singular points](https://en.wikipedia.org/wiki/Mathematical_singularity), a variety is in general not a manifold, though linguistically the French *variété*, German *Mannigfaltigkeit* and English *manifold* are largely [synonymous](https://en.wikipedia.org/wiki/Synonymous). In French an algebraic variety is called *une [variété algébrique](https://fr.wikipedia.org/wiki/vari%C3%A9t%C3%A9_alg%C3%A9brique)* (an *algebraic variety*), while a smooth manifold is called *une [variété différentielle](https://fr.wikipedia.org/wiki/vari%C3%A9t%C3%A9_diff%C3%A9rentielle)* (a *differential variety*).

Stratified space  
A "stratified space" is a space that can be divided into pieces ("strata"), with each stratum a manifold, with the strata fitting together in prescribed ways (formally, a [filtration](https://en.wikipedia.org/wiki/Filtration_(mathematics) "Filtration (mathematics)") by closed subsets). There are various technical definitions, notably a Whitney stratified space (see [Whitney conditions](https://en.wikipedia.org/wiki/Whitney_conditions)) for smooth manifolds and a [topologically stratified space](https://en.wikipedia.org/wiki/Topologically_stratified_space) for topological manifolds. Basic examples include [manifold with boundary](https://en.wikipedia.org/wiki/Manifold_with_boundary) (top dimensional manifold and codimension 1 boundary) and manifolds with corners (top dimensional manifold, codimension 1 boundary, codimension 2 corners). Whitney stratified spaces are a broad class of spaces, including algebraic varieties, analytic varieties, [semialgebraic sets](https://en.wikipedia.org/wiki/Semialgebraic_set), and [subanalytic sets](https://en.wikipedia.org/wiki/Subanalytic_set).

CW-complexes  
A [CW complex](https://en.wikipedia.org/wiki/CW_complex) is a topological space formed by gluing disks of different dimensionality together. In general the resulting space is singular, hence not a manifold. However, they are of central interest in algebraic topology, especially in [homotopy theory](https://en.wikipedia.org/wiki/Homotopy_theory).

Homology manifolds  
A [homology manifold](https://en.wikipedia.org/wiki/Homology_manifold) is a space that behaves like a manifold from the point of view of homology theory. These are not all manifolds, but (in high dimension) can be analyzed by surgery theory similarly to manifolds, and failure to be a manifold is a local obstruction, as in surgery theory.

Differential spaces  
Let $M$ be a nonempty set. Suppose that some family of real functions on $M$ was chosen. Denote it by $C\subseteq \mathbb {R} ^{M}$. It is an algebra with respect to the pointwise addition and multiplication. Let $M$ be equipped with the topology induced by $C$. Suppose also that the following conditions hold. First: for every $H\in C^{\infty }\left(\mathbb {R} ^{n}\right)$, where $n\in \mathbb {N}$, and arbitrary $f_{1},\dots ,f_{n}\in C$, the composition $H\circ \left(f_{1},\dots ,f_{n}\right)\in C$. Second: every function, which in every point of $M$ locally coincides with some function from $C$, also belongs to $C$. A pair $(M,C)$ for which the above conditions hold, is called a Sikorski differential space.

## See also

- [Submanifold](https://en.wikipedia.org/wiki/Submanifold) – Subset of a manifold that is a manifold itself; an injective immersion into a manifold
- [Geodesic](https://en.wikipedia.org/wiki/Geodesic) – Straight path on a curved surface or a Riemannian manifold
- [Directional statistics](https://en.wikipedia.org/wiki/Directional_statistics) – Subdiscipline of statistics: statistics on manifolds
- [List of manifolds](https://en.wikipedia.org/wiki/List_of_manifolds)
- [Timeline of manifolds](https://en.wikipedia.org/wiki/Timeline_of_manifolds) – Mathematics timeline
- [Mathematics of general relativity](https://en.wikipedia.org/wiki/Mathematics_of_general_relativity)

### By dimension

- [3-manifold](https://en.wikipedia.org/wiki/3-manifold) – Mathematical space
- [4-manifold](https://en.wikipedia.org/wiki/4-manifold) – Mathematical space
- [5-manifold](https://en.wikipedia.org/wiki/5-manifold) – Manifold of dimension five
- [Manifolds of mappings](https://en.wikipedia.org/wiki/Convenient_vector_space#Application:_Manifolds_of_mappings_between_finite_dimensional_manifolds)

## Notes

1.  E.g. see Riaza, Ricardo (2008), [Differential-Algebraic Systems: Analytical Aspects and Circuit Applications](https://books.google.com/books?id=HoOWxqWru1cC&pg=PA110), World Scientific, p. 110, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-981-279-181-8](https://en.wikipedia.org/wiki/Special:BookSources/978-981-279-181-8); Gunning, R. C. (1990), [Introduction to Holomorphic Functions of Several Variables, Volume 2](https://books.google.com/books?id=dKYhlJB1iOgC&pg=PA73), CRC Press, p. 73, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-534-13309-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-534-13309-2).
2.  Shigeyuki Morita; Teruko Nagase; Katsumi Nomizu (2001). [Geometry of Differential Forms](https://archive.org/details/geometryofdiffer00mori). American Mathematical Society. p. [12](https://archive.org/details/geometryofdiffer00mori/page/12). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-8218-1045-6](https://en.wikipedia.org/wiki/Special:BookSources/0-8218-1045-6).
4.  [Poincaré, H.](https://en.wikipedia.org/wiki/Henri_Poincar%C3%A9) (1895). "Analysis Situs". *Journal de l'École Polytechnique*. Serié 11 (in French). Gauthier-Villars.
5.  [Arnolʹd, V. I.](https://en.wikipedia.org/wiki/Vladimir_Arnold) (1998). ["О преподавании математики"](https://doi.org/10.4213%2Frm5) \[On Teaching Mathematics\]. *Uspekhi Mat. Nauk* (in Russian). **53** (319): 229–234. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.4213/rm5](https://doi.org/10.4213%2Frm5).; translation in Russian Math. Surveys 53 (1998), no. 1, 229–236
6.  [Whitney, H.](https://en.wikipedia.org/wiki/Hassler_Whitney) (1936). "Differentiable Manifolds". *Annals of Mathematics*. Second Series. **37** (3): 645–680. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/1968482](https://doi.org/10.2307%2F1968482). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [1968482](https://www.jstor.org/stable/1968482).
7.  Kervaire, M. (1961). "A Manifold which does not admit any differentiable structure". *[Comment. Math. Helv.](https://en.wikipedia.org/wiki/Comment._Math._Helv.)* **35** (1): 1–14. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/BF02565940](https://doi.org/10.1007%2FBF02565940). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [120977898](https://api.semanticscholar.org/CorpusID:120977898).
8.  Ross, Ethan (2024-04-01). ["Stratified vector bundles: Examples and constructions"](https://www.sciencedirect.com/science/article/pii/S0393044024000159). *Journal of Geometry and Physics*. **198** 105114. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2303.04200](https://arxiv.org/abs/2303.04200). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2024JGP...19805114R](https://ui.adsabs.harvard.edu/abs/2024JGP...19805114R). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.geomphys.2024.105114](https://doi.org/10.1016%2Fj.geomphys.2024.105114). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0393-0440](https://search.worldcat.org/issn/0393-0440). [Archived](https://web.archive.org/web/20240519023021/https://www.sciencedirect.com/science/article/pii/S0393044024000159) from the original on 2024-05-19. Retrieved 2024-05-19.
9.  Bryant, J.; Ferry, S.; Mio, W.; Weinberger, S. (1996). "Topology of homology manifolds". *Annals of Mathematics*. Second Series. **143** (3): 435–467. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[math/9304210](https://arxiv.org/abs/math/9304210). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2118532](https://doi.org/10.2307%2F2118532). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2118532](https://www.jstor.org/stable/2118532).
10. Sikorski, R. (1967). ["Abstract covariant derivative"](https://doi.org/10.4064%2Fcm-18-1-251-272). *Colloquium Mathematicum*. **18**: 251–272. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.4064/cm-18-1-251-272](https://doi.org/10.4064%2Fcm-18-1-251-272).

## References

- [Freedman, Michael H.](https://en.wikipedia.org/wiki/Michael_Freedman), and Quinn, Frank (1990) *Topology of 4-Manifolds*. Princeton University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-691-08577-3](https://en.wikipedia.org/wiki/Special:BookSources/0-691-08577-3).
- [Guillemin, Victor](https://en.wikipedia.org/wiki/Victor_Guillemin) and Pollack, Alan (1974) *Differential Topology*. Prentice-Hall. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-13-212605-2](https://en.wikipedia.org/wiki/Special:BookSources/0-13-212605-2). Advanced undergraduate / first-year graduate text inspired by Milnor.
- Hempel, John (1976) *3-Manifolds*. Princeton University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-8218-3695-1](https://en.wikipedia.org/wiki/Special:BookSources/0-8218-3695-1).
- [Hirsch, Morris](https://en.wikipedia.org/wiki/Morris_Hirsch), (1997) *Differential Topology*. Springer Verlag. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-90148-5](https://en.wikipedia.org/wiki/Special:BookSources/0-387-90148-5). The most complete account, with historical insights and excellent, but difficult, problems. The standard reference for those wishing to have a deep understanding of the subject.
- [Kirby, Robion C.](https://en.wikipedia.org/wiki/Robion_Kirby) and Siebenmann, Laurence C. (1977) *Foundational Essays on Topological Manifolds. Smoothings, and Triangulations*. Princeton University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-691-08190-5](https://en.wikipedia.org/wiki/Special:BookSources/0-691-08190-5). A detailed study of the [category](https://en.wikipedia.org/wiki/Category_theory) of topological manifolds.
- Lee, John M. (2000) *Introduction to Topological Manifolds*. Springer-Verlag. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-98759-2](https://en.wikipedia.org/wiki/Special:BookSources/0-387-98759-2). Detailed and comprehensive first-year graduate text.
- Lee, John M. (2003) *[Introduction to Smooth Manifolds](https://archive.org/details/GraduateTextsInMathematics218LeeJ.M.IntroductionToSmoothManifoldsSpringer2012)*. Springer-Verlag. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-95495-3](https://en.wikipedia.org/wiki/Special:BookSources/0-387-95495-3). Detailed and comprehensive first-year graduate text; sequel to *Introduction to Topological Manifolds*.
- [Massey, William S.](https://en.wikipedia.org/wiki/William_S._Massey) (1977) *Algebraic Topology: An Introduction*. Springer-Verlag. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-90271-6](https://en.wikipedia.org/wiki/Special:BookSources/0-387-90271-6).
- [Milnor, John](https://en.wikipedia.org/wiki/John_Milnor) (1997) *Topology from the Differentiable Viewpoint*. Princeton University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-691-04833-9](https://en.wikipedia.org/wiki/Special:BookSources/0-691-04833-9). Classic brief introduction to differential topology.
- [Munkres, James R.](https://en.wikipedia.org/wiki/James_Munkres) (1991) *[Analysis on Manifolds](https://archive.org/details/MunkresJ.R.AnalysisOnManifolds)*. Addison-Wesley (reprinted by Westview Press) [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-201-51035-9](https://en.wikipedia.org/wiki/Special:BookSources/0-201-51035-9). Undergraduate text treating manifolds in $\mathbb {R} ^{n}$.
- [Munkres, James R.](https://en.wikipedia.org/wiki/James_Munkres) (2000) *Topology*. Prentice Hall. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-13-181629-2](https://en.wikipedia.org/wiki/Special:BookSources/0-13-181629-2).
- Neuwirth, L. P., ed. (1975) *Knots, Groups, and 3-Manifolds. Papers Dedicated to the Memory of R. H. Fox*. Princeton University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-691-08170-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-691-08170-0).
- [Riemann, Bernhard](https://en.wikipedia.org/wiki/Bernhard_Riemann), *Gesammelte mathematische Werke und wissenschaftlicher Nachlass*, Sändig Reprint. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [3-253-03059-8](https://en.wikipedia.org/wiki/Special:BookSources/3-253-03059-8).
  - *[Grundlagen für eine allgemeine Theorie der Functionen einer veränderlichen complexen Grösse.](http://www.maths.tcd.ie/pub/HistMath/People/Riemann/Grund/)* The 1851 doctoral thesis in which "manifold" (*Mannigfaltigkeit*) first appears.
  - *[Ueber die Hypothesen, welche der Geometrie zu Grunde liegen.](http://www.maths.tcd.ie/pub/HistMath/People/Riemann/Geom/)* The 1854 Göttingen inaugural lecture (*Habilitationsschrift*).
- [Spivak, Michael](https://en.wikipedia.org/wiki/Michael_Spivak) (1965) *[Calculus on Manifolds: A Modern Approach to Classical Theorems of Advanced Calculus](https://archive.org/details/SpivakM.CalculusOnManifoldsPerseus2006Reprint)*. W.A. Benjamin Inc. (reprinted by Addison-Wesley and Westview Press). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-8053-9021-9](https://en.wikipedia.org/wiki/Special:BookSources/0-8053-9021-9). [Famously terse](https://en.wikipedia.org/wiki/Calculus_on_Manifolds_(book) "Calculus on Manifolds (book)") advanced undergraduate / first-year graduate text.
- [Spivak, Michael](https://en.wikipedia.org/wiki/Michael_Spivak) (1999) *A Comprehensive Introduction to Differential Geometry* (3rd edition) Publish or Perish Inc. Encyclopedic five-volume series presenting a systematic treatment of the theory of manifolds, Riemannian geometry, classical differential geometry, and numerous other topics at the first- and second-year graduate levels.
- Tu, Loring W. (2011). [*An Introduction to Manifolds*](https://en.wikipedia.org/wiki/An_Introduction_to_Manifolds) (2nd ed.). New York: Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4419-7399-3](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4419-7399-3).. Concise first-year graduate text.

## External links

- ["Manifold"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society), 2001 \[1994\]
- [Dimensions-math.org](http://www.dimensions-math.org/Dim_E.htm) (A film explaining and visualizing manifolds up to fourth dimension.)
- The [manifold atlas](http://www.map.mpim-bonn.mpg.de) [Archived](http://arquivo.pt/wayback/20160523161822/http%3A//www.map.mpim%2Dbonn.mpg.de/Main_Page) 2016-05-23 at the Portuguese Web Archive project of the [Max Planck Institute for Mathematics in Bonn](http://www.mpim-bonn.mpg.de)
- MIT Open Courseware: [Geometry of Manifolds](https://ocw.mit.edu/courses/18-965-geometry-of-manifolds-fall-2004/pages/lecture-notes/).
