[[geometry-manifolds.base]]

> Source: [[Tangent Space]]
> License: Wikipedia content is available under CC BY-SA 4.0.

In [mathematics](https://en.wikipedia.org/wiki/Mathematics), the **tangent space** of a [[Manifold]] is a generalization of *[tangent lines](https://en.wikipedia.org/wiki/Tangent_line)* to curves in [two-dimensional space](https://en.wikipedia.org/wiki/Plane_(mathematics) "Plane (mathematics)") and *[tangent planes](https://en.wikipedia.org/wiki/Tangent#Tangent_plane_to_a_surface)* to surfaces in [three-dimensional space](https://en.wikipedia.org/wiki/Three-dimensional_space) in higher dimensions. In the context of physics, the tangent space to a manifold at a point can be viewed as the space of possible velocities for a particle moving on the manifold.

## Informal description

![[media/c754d0aab0f1b17531e5622296b71b699b44e9e9.png]]
A pictorial representation of the tangent space of a single point $P(r,\theta ,\phi )$ on a [sphere](https://en.wikipedia.org/wiki/Sphere). A vector in this tangent space represents a possible velocity (of something moving on the sphere) at $P$. After moving in that direction to a nearby point, the velocity would then be given by a vector in the tangent space of that point—a different tangent space that is not shown.

In [differential geometry](https://en.wikipedia.org/wiki/Differential_geometry), one can attach to every point $x$ of a [differentiable manifold](https://en.wikipedia.org/wiki/Differentiable_manifold) a *tangent space*—a real [[Vector Space]] that intuitively contains the possible directions in which one can tangentially pass through $x$. The elements of the tangent space at $x$ are called the *[tangent vectors](https://en.wikipedia.org/wiki/Tangent_vector)* at $x$. This is a generalization of the notion of a [vector](https://en.wikipedia.org/wiki/Vector_(mathematics_and_physics) "Vector (mathematics and physics)"), based at a given initial point, in a [Euclidean space](https://en.wikipedia.org/wiki/Euclidean_space). The [dimension](https://en.wikipedia.org/wiki/Dimension_of_a_vector_space) of the tangent space at every point of a [connected](https://en.wikipedia.org/wiki/Connected_space) manifold is the same as that of the [[Manifold]] itself.

For example, if the given manifold is a $2$-[sphere](https://en.wikipedia.org/wiki/Sphere), then one can picture the tangent space at a point as the plane that touches the sphere at that point and is [perpendicular](https://en.wikipedia.org/wiki/Perpendicular) to the sphere's radius through the point. More generally, if a given manifold is thought of as an [embedded](https://en.wikipedia.org/wiki/Embedding) [submanifold](https://en.wikipedia.org/wiki/Submanifold) of [Euclidean space](https://en.wikipedia.org/wiki/Euclidean_space), then one can picture a tangent space in this literal fashion. This was the traditional approach toward defining [parallel transport](https://en.wikipedia.org/wiki/Parallel_transport). Many authors in [differential geometry](https://en.wikipedia.org/wiki/Differential_geometry) and [general relativity](https://en.wikipedia.org/wiki/General_relativity) use it. More strictly, this defines an affine tangent space, which is distinct from the space of tangent vectors described by modern terminology.

In [algebraic geometry](https://en.wikipedia.org/wiki/Algebraic_geometry), in contrast, there is an intrinsic definition of the *tangent space at a point* of an [algebraic variety](https://en.wikipedia.org/wiki/Algebraic_variety) $V$ that gives a vector space with dimension at least that of $V$ itself. The points $p$ at which the dimension of the tangent space is exactly that of $V$ are called *non-singular* points; the others are called *singular* points. For example, a curve that crosses itself does not have a unique tangent line at that point. The singular points of $V$ are those where the "test to be a manifold" fails. See [Zariski tangent space](https://en.wikipedia.org/wiki/Zariski_tangent_space).

Once the tangent spaces of a manifold have been introduced, one can define [vector fields](https://en.wikipedia.org/wiki/Vector_field), which are abstractions of the velocity field of particles moving in space. A vector field attaches to every point of the manifold a vector from the tangent space at that point, in a smooth manner. Such a vector field serves to define a generalized [ordinary differential equation](https://en.wikipedia.org/wiki/Ordinary_differential_equation) on a manifold: A solution to such a differential equation is a differentiable [curve](https://en.wikipedia.org/wiki/Curve) on the manifold whose derivative at any point is equal to the tangent vector attached to that point by the vector field.

All the tangent spaces of a manifold may be "glued together" to form a new differentiable manifold with twice the dimension of the original manifold, called the *[tangent bundle](https://en.wikipedia.org/wiki/Tangent_bundle)* of the manifold.

## Formal definitions

The informal description above relies on a manifold's ability to be embedded into an ambient vector space $\mathbb {R} ^{m}$ so that the tangent vectors can "stick out" of the manifold into the ambient space. However, it is more convenient to define the notion of a tangent space based solely on the manifold itself.

There are various equivalent ways of defining the tangent spaces of a manifold. While the definition via the velocity of curves is intuitively the simplest, it is also the most cumbersome to work with. More elegant and abstract approaches are described below.

### Definition via tangent curves

In the embedded-manifold picture, a tangent vector at a point $x$ is thought of as the *velocity* of a [curve](https://en.wikipedia.org/wiki/Curve#Topology) passing through the point $x$. We can therefore define a tangent vector as an equivalence class of curves passing through $x$ while being tangent to each other at $x$.

Suppose that $M$ is a $C^{k}$ [differentiable manifold](https://en.wikipedia.org/wiki/Differentiable_manifold) (with [smoothness](https://en.wikipedia.org/wiki/Smoothness) $k\geq 1$) and that $x\in M$. Pick a [[Manifold|coordinate chart]] $\varphi :U\to \mathbb {R} ^{n}$, where $U$ is an [open subset](https://en.wikipedia.org/wiki/Open_set) of $M$ containing $x$. Suppose further that two curves $\gamma _{1},\gamma _{2}:(-1,1)\to M$ with ${\gamma _{1}}(0)=x={\gamma _{2}}(0)$ are given such that both $\varphi \circ \gamma _{1},\varphi \circ \gamma _{2}:(-1,1)\to \mathbb {R} ^{n}$ are differentiable in the ordinary sense (we call these *differentiable curves initialized at $x$*). Then $\gamma _{1}$ and $\gamma _{2}$ are said to be *equivalent* at $0$ if and only if the derivatives of $\varphi \circ \gamma _{1}$ and $\varphi \circ \gamma _{2}$ at $0$ coincide. This defines an [equivalence relation](https://en.wikipedia.org/wiki/Equivalence_relation) on the set of all differentiable curves initialized at $x$, and [equivalence classes](https://en.wikipedia.org/wiki/Equivalence_class) of such curves are known as *tangent vectors* of $M$ at $x$. The equivalence class of any such curve $\gamma$ is denoted by $\gamma '(0)$. The *tangent space* of $M$ at $x$, denoted by $T_{x}M$, is then defined as the set of all tangent vectors at $x$; it does not depend on the choice of coordinate chart $\varphi :U\to \mathbb {R} ^{n}$.

![[media/79a67a1c4197bd2190e11341ff52b2439e70d5cd.png]]
The tangent space $T_{x}M$ and a tangent vector $v\in T_{x}M$, along a curve traveling through $x\in M$.

To define vector-space operations on $T_{x}M$, we use a chart $\varphi :U\to \mathbb {R} ^{n}$ and define a [map](https://en.wikipedia.org/wiki/Map_(mathematics) "Map (mathematics)") $\mathrm {d} {\varphi }_{x}:T_{x}M\to \mathbb {R} ^{n}$ by ${\mathrm {d} {\varphi }_{x}}(\gamma '(0)):={\frac {\mathrm {d} (\varphi \circ \gamma )}{\mathrm {d} {t}}}(0),$ where $\gamma \in \gamma '(0)$. The map $\mathrm {d} {\varphi }_{x}$ turns out to be [bijective](https://en.wikipedia.org/wiki/Bijective) and may be used to transfer the vector-space operations on $\mathbb {R} ^{n}$ over to $T_{x}M$, thus turning the latter set into an $n$-dimensional real vector space. Again, one needs to check that this construction does not depend on the particular chart $\varphi :U\to \mathbb {R} ^{n}$ and the curve $\gamma$ being used, and in fact it does not.

### Definition via derivations

Suppose now that $M$ is a $C^{\infty }$ manifold. A real-valued function $f:M\to \mathbb {R}$ is said to belong to ${C^{\infty }}(M)$ if and only if for every coordinate chart $\varphi :U\to \mathbb {R} ^{n}$, the map $f\circ \varphi ^{-1}:\varphi [U]\subseteq \mathbb {R} ^{n}\to \mathbb {R}$ is infinitely differentiable. Note that ${C^{\infty }}(M)$ is a real [associative algebra](https://en.wikipedia.org/wiki/Associative_algebra) with respect to the [pointwise product](https://en.wikipedia.org/wiki/Pointwise_product) and sum of functions and scalar multiplication.

A *[derivation](https://en.wikipedia.org/wiki/Derivation_(abstract_algebra))* at $x\in M$ is defined as a [linear map](https://en.wikipedia.org/wiki/Linear_map) $D:{C^{\infty }}(M)\to \mathbb {R}$ that satisfies the Leibniz identity 

$$
\forall f,g\in {C^{\infty }}(M):\qquad D(fg)=D(f)\cdot g(x)+f(x)\cdot D(g),
$$

 which is modeled on the [product rule](https://en.wikipedia.org/wiki/Product_rule) of calculus.

(For every identically constant function $f={\text{const}},$ it follows that $D(f)=0$).

Denote $T_{x}M$ the set of all derivations at $x.$ Setting

- $(D_{1}+D_{2})(f):={D}_{1}(f)+{D}_{2}(f)$ and
- $(\lambda \cdot D)(f):=\lambda \cdot D(f)$

turns $T_{x}M$ into a vector space.

#### Generalizations

Generalizations of this definition are possible, for instance, to [complex manifolds](https://en.wikipedia.org/wiki/Complex_manifold) and [algebraic varieties](https://en.wikipedia.org/wiki/Algebraic_variety). However, instead of examining derivations $D$ from the full algebra of functions, one must instead work at the level of [germs](https://en.wikipedia.org/wiki/Germ_(mathematics) "Germ (mathematics)") of functions. The reason for this is that the [structure sheaf](https://en.wikipedia.org/wiki/Structure_sheaf) may not be [fine](https://en.wikipedia.org/wiki/Injective_sheaf#Fine_sheaves) for such structures. For example, let $X$ be an algebraic variety with [structure sheaf](https://en.wikipedia.org/wiki/Structure_sheaf) ${\mathcal {O}}_{X}$. Then the [Zariski tangent space](https://en.wikipedia.org/wiki/Zariski_tangent_space) at a point $p\in X$ is the collection of all $\mathbb {k}$-derivations $D:{\mathcal {O}}_{X,p}\to \mathbb {k}$, where $\mathbb {k}$ is the [ground field](https://en.wikipedia.org/wiki/Ground_field) and ${\mathcal {O}}_{X,p}$ is the [stalk](https://en.wikipedia.org/wiki/Stalk_(sheaf) "Stalk (sheaf)") of ${\mathcal {O}}_{X}$ at $p$.

### Equivalence of the definitions

For $x\in M$ and a differentiable curve $\gamma :(-1,1)\to M$ such that $\gamma (0)=x,$ define ${D_{\gamma }}(f):=(f\circ \gamma )'(0)$ (where the derivative is taken in the ordinary sense because $f\circ \gamma$ is a function from $(-1,1)$ to $\mathbb {R}$). One can ascertain that $D_{\gamma }(f)$ is a derivation at the point $x,$ and that equivalent curves yield the same derivation. Thus, for an equivalence class $\gamma '(0),$ we can define ${D_{\gamma '(0)}}(f):=(f\circ \gamma )'(0),$ where the curve $\gamma \in \gamma '(0)$ has been chosen arbitrarily. The map $\gamma '(0)\mapsto D_{\gamma '(0)}$ is a vector space isomorphism between the space of the equivalence classes $\gamma '(0)$ and the space of derivations at the point $x.$

### Definition via cotangent spaces

Again, we start with a $C^{\infty }$ manifold $M$ and a point $x\in M$. Consider the [ideal](https://en.wikipedia.org/wiki/Ideal_(ring_theory) "Ideal (ring theory)") $I$ of $C^{\infty }(M)$ that consists of all smooth functions $f$ vanishing at $x$, i.e., $f(x)=0$. Then $I$ and $I^{2}$ are both real vector spaces, and the [quotient space](https://en.wikipedia.org/wiki/Quotient_space_(linear_algebra) "Quotient space (linear algebra)") $I/I^{2}$ can be shown to be [isomorphic](https://en.wikipedia.org/wiki/Isomorphism) to the [cotangent space](https://en.wikipedia.org/wiki/Cotangent_space) $T_{x}^{*}M$ through the use of [Taylor's theorem](https://en.wikipedia.org/wiki/Taylor%27s_theorem). The tangent space $T_{x}M$ may then be defined as the [dual space](https://en.wikipedia.org/wiki/Dual_space) of $I/I^{2}$.

While this definition is the most abstract, it is also the one that is most easily transferable to other settings, for instance, to the [varieties](https://en.wikipedia.org/wiki/Algebraic_variety) considered in [algebraic geometry](https://en.wikipedia.org/wiki/Algebraic_geometry).

If $D$ is a derivation at $x$, then $D(f)=0$ for every $f\in I^{2}$, which means that $D$ gives rise to a linear map $I/I^{2}\to \mathbb {R}$. Conversely, if $r:I/I^{2}\to \mathbb {R}$ is a linear map, then $D(f):=r\left((f-f(x))+I^{2}\right)$ defines a derivation at $x$. This yields an equivalence between tangent spaces defined via derivations and tangent spaces defined via cotangent spaces.

## Properties

If $M$ is an open subset of $\mathbb {R} ^{n}$, then $M$ is a $C^{\infty }$ manifold in a natural manner (take coordinate charts to be [identity maps](https://en.wikipedia.org/wiki/Identity_function) on open subsets of $\mathbb {R} ^{n}$), and the tangent spaces are all naturally identified with $\mathbb {R} ^{n}$.

### Tangent vectors as directional derivatives

Another way to think about tangent vectors is as [directional derivatives](https://en.wikipedia.org/wiki/Directional_derivative). Given a vector $v$ in $\mathbb {R} ^{n}$, one defines the corresponding directional derivative at a point $x\in \mathbb {R} ^{n}$ by

$\forall f\in {C^{\infty }}(\mathbb {R} ^{n}):\qquad (D_{v}f)(x):=\left.{\frac {\mathrm {d} }{\mathrm {d} {t}}}[f(x+tv)]\right|_{t=0}=\sum _{i=1}^{n}v^{i}{\frac {\partial f}{\partial x^{i}}}(x).$

This map is naturally a derivation at $x$. Furthermore, every derivation at a point in $\mathbb {R} ^{n}$ is of this form. Hence, there is a one-to-one correspondence between vectors (thought of as tangent vectors at a point) and derivations at a point.

As tangent vectors to a general manifold at a point can be defined as derivations at that point, it is natural to think of them as directional derivatives. Specifically, if $v$ is a tangent vector to $M$ at a point $x$ (thought of as a derivation), then define the directional derivative $D_{v}$ in the direction $v$ by

$\forall f\in {C^{\infty }}(M):\qquad {D_{v}}(f):=v(f).$

If we think of $v$ as the initial velocity of a differentiable curve $\gamma$ initialized at $x$, i.e., $v=\gamma '(0)$, then instead, define $D_{v}$ by

$\forall f\in {C^{\infty }}(M):\qquad {D_{v}}(f):=(f\circ \gamma )'(0).$

### Basis of the tangent space at a point

For a $C^{\infty }$ manifold $M$, if a chart $\varphi =(x^{1},\ldots ,x^{n}):U\to \mathbb {R} ^{n}$ is given with $p\in U$, then one can define an ordered basis $\left\{\left.{\frac {\partial }{\partial x^{1}}}\right|_{p},\dots ,\left.{\frac {\partial }{\partial x^{n}}}\right|_{p}\right\}$ of $T_{p}M$ by

$\forall i\in \{1,\ldots ,n\},~\forall f\in {C^{\infty }}(M):\qquad {\left.{\frac {\partial }{\partial x^{i}}}\right|_{p}}(f):=\left({\frac {\partial }{\partial x^{i}}}{\Big (}f\circ \varphi ^{-1}{\Big )}\right){\Big (}\varphi (p){\Big )}.$

Then for every tangent vector $v\in T_{p}M$, one has

$v=\sum _{i=1}^{n}v^{i}\left.{\frac {\partial }{\partial x^{i}}}\right|_{p}.$

This formula therefore expresses $v$ as a linear combination of the basis tangent vectors $\left.{\frac {\partial }{\partial x^{i}}}\right|_{p}\in T_{p}M$ defined by the coordinate chart $\varphi :U\to \mathbb {R} ^{n}$.

### The derivative of a map

Every smooth (or differentiable) map $\varphi :M\to N$ between smooth (or differentiable) manifolds induces natural [linear maps](https://en.wikipedia.org/wiki/Linear_map) between their corresponding tangent spaces:

$\mathrm {d} {\varphi }_{x}:T_{x}M\to T_{\varphi (x)}N.$

If the tangent space is defined via differentiable curves, then this map is defined by

${\mathrm {d} {\varphi }_{x}}(\gamma '(0)):=(\varphi \circ \gamma )'(0).$

If, instead, the tangent space is defined via derivations, then this map is defined by

$[\mathrm {d} {\varphi }_{x}(D)](f):=D(f\circ \varphi ).$

The linear map $\mathrm {d} {\varphi }_{x}$ is called variously the *derivative*, *total derivative*, *differential*, or *pushforward* of $\varphi$ at $x$. It is frequently expressed using a variety of other notations:

$D\varphi _{x},\qquad (\varphi _{*})_{x},\qquad \varphi '(x).$

In a sense, the derivative is the best linear approximation to $\varphi$ near $x$. Note that when $N=\mathbb {R}$, then the map $\mathrm {d} {\varphi }_{x}:T_{x}M\to \mathbb {R}$ coincides with the usual notion of the [differential](https://en.wikipedia.org/wiki/Differential_(calculus)) of the function $\varphi$. In [local coordinates](https://en.wikipedia.org/wiki/Local_coordinates) the derivative of $\varphi$ is given by the [Jacobian](https://en.wikipedia.org/wiki/Jacobian_matrix_and_determinant).

An important result regarding the derivative map is the following:

**Theorem**—If $\varphi :M\to N$ is a [local diffeomorphism](https://en.wikipedia.org/wiki/Local_diffeomorphism) at $x$ in $M$, then $\mathrm {d} {\varphi }_{x}:T_{x}M\to T_{\varphi (x)}N$ is a linear [isomorphism](https://en.wikipedia.org/wiki/Isomorphism). Conversely, if $\varphi :M\to N$ is continuously differentiable and $\mathrm {d} {\varphi }_{x}$ is an isomorphism, then there is an [open neighborhood](https://en.wikipedia.org/wiki/Open_set) $U$ of $x$ such that $\varphi$ maps $U$ diffeomorphically onto its image.

This is a generalization of the [inverse function theorem](https://en.wikipedia.org/wiki/Inverse_function_theorem) to maps between manifolds.

## See also

- [Coordinate-induced basis](https://en.wikipedia.org/wiki/Coordinate-induced_basis)
- [Cotangent space](https://en.wikipedia.org/wiki/Cotangent_space)
- [Differential geometry of curves](https://en.wikipedia.org/wiki/Differential_geometry_of_curves)
- [Exponential map](https://en.wikipedia.org/wiki/Exponential_map_(Riemannian_geometry) "Exponential map (Riemannian geometry)")
- [[Vector Space]]

## Notes

1.  do Carmo, Manfredo P. (1976). *Differential Geometry of Curves and Surfaces*. Prentice-Hall.:
2.  Dirac, Paul A. M. (1996) \[1975\]. *General Theory of Relativity*. Princeton University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-691-01146-X](https://en.wikipedia.org/wiki/Special:BookSources/0-691-01146-X).
3.  Chris J. Isham (1 January 2002). [Modern Differential Geometry for Physicists](https://books.google.com/books?id=DCn9bjBe27oC&pg=PA70). Allied Publishers. pp. 70–72. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-81-7764-316-9](https://en.wikipedia.org/wiki/Special:BookSources/978-81-7764-316-9).
4.  Lerman, Eugene. ["An Introduction to Differential Geometry"](https://web.archive.org/web/20230608072428/https://faculty.math.illinois.edu/~lerman/518/f11/8-19-11.pdf) (PDF). p. 12. Archived from [the original](https://faculty.math.illinois.edu/~lerman/518/f11/8-19-11.pdf) (PDF) on 2023-06-08. Retrieved 2021-04-09.

## References

- Lee, Jeffrey M. (2009), *Manifolds and Differential Geometry*, [Graduate Studies in Mathematics](https://en.wikipedia.org/wiki/Graduate_Studies_in_Mathematics), vol. 107, Providence: American Mathematical Society.
- Michor, Peter W. (2008), *Topics in Differential Geometry*, Graduate Studies in Mathematics, vol. 93, Providence: American Mathematical Society.
- [Spivak, Michael](https://en.wikipedia.org/wiki/Michael_Spivak) (1965), [Calculus on Manifolds: A Modern Approach to Classical Theorems of Advanced Calculus](https://archive.org/details/SpivakM.CalculusOnManifolds_201703), W. A. Benjamin, Inc., [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8053-9021-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8053-9021-6).

## External links

- [Tangent Planes](http://mathworld.wolfram.com/TangentPlane.html) at MathWorld
