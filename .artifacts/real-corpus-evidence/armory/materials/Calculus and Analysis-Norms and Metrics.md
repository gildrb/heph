[[calculus-analysis.base]]

> Source: [Norm (mathematics)](https://en.wikipedia.org/wiki/Norm_(mathematics))
> License: Wikipedia content is available under CC BY-SA 4.0.

In [mathematics](https://en.wikipedia.org/wiki/Mathematics), a **norm** is a [function](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)") from a real or complex [[Vector Space]] to the non-negative real numbers that behaves in certain ways like the distance from the [origin](https://en.wikipedia.org/wiki/Origin_(mathematics) "Origin (mathematics)"): it [commutes](https://en.wikipedia.org/wiki/Equivariant_map) with scaling, obeys a form of the [triangle inequality](https://en.wikipedia.org/wiki/Triangle_inequality), and zero is only at the origin. In particular, the [Euclidean distance](https://en.wikipedia.org/wiki/Euclidean_distance) in a [Euclidean space](https://en.wikipedia.org/wiki/Euclidean_space) is defined by a norm on the associated [Euclidean vector space](https://en.wikipedia.org/wiki/Euclidean_vector_space), called the [Euclidean norm](#Euclidean_norm), the [2-norm](#p-norm), or, sometimes, the **magnitude** or **length** of the vector. This norm can be defined as the [square root](https://en.wikipedia.org/wiki/Square_root) of the [inner product](https://en.wikipedia.org/wiki/Inner_product) of a vector with itself.

A [seminorm](https://en.wikipedia.org/wiki/Seminorm) satisfies the first two properties of a norm but may be zero for vectors other than the origin. A vector space with a specified norm is called a [normed vector space](https://en.wikipedia.org/wiki/Normed_vector_space). In a similar manner, a vector space with a seminorm is called a *seminormed vector space*.

The term **pseudonorm** has been used for several related meanings. It may be a synonym of "seminorm". It can also refer to a norm that can take infinite values or to certain functions parametrised by a [directed set](https://en.wikipedia.org/wiki/Directed_set).

## Definition

Given a [[Vector Space]] $X$ over a [subfield](https://en.wikipedia.org/wiki/Field_extension) $F$ of the complex numbers $\mathbb {C} ,$ a **norm** on $X$ is a [real-valued function](https://en.wikipedia.org/wiki/Real-valued_function) $p:X\to \mathbb {R}$ with the following properties, where $|s|$ denotes the usual [absolute value](https://en.wikipedia.org/wiki/Absolute_value) of a scalar $s$:

1.  [Subadditivity](https://en.wikipedia.org/wiki/Subadditive_function) / [Triangle inequality](https://en.wikipedia.org/wiki/Triangle_inequality):  
    $p(x+y)\leq p(x)+p(y)$ for all $x,y\in X.$
2.  [Absolute homogeneity](https://en.wikipedia.org/wiki/Homogeneous_function):  
    $p(sx)=|s|p(x)$ for all $x\in X$ and all scalars $s.$
3.  [Positive definiteness](https://en.wikipedia.org/wiki/Positive_definiteness) / Positiveness / Point-separating:  
    for all $x\in X,$ if $p(x)=0,$ then $x=0.$
    - Because property (2.) implies $p(0)=0,$ some authors replace property (3.) with the equivalent condition: for every $x\in X,$ $p(x)=0$ if and only if $x=0.$

A [seminorm](https://en.wikipedia.org/wiki/Seminorm) on $X$ is a function $p:X\to \mathbb {R}$ that has properties (1.) and (2.) so that in particular, every norm is also a seminorm (and thus also a [sublinear functional](https://en.wikipedia.org/wiki/Sublinear_function)). However, there exist seminorms that are not norms. Properties (1.) and (2.) imply that if $p$ is a norm (or more generally, a seminorm), then $p(0)=0$ and that $p$ also has the following property:

1.  
2.  [Non-negativity](https://en.wikipedia.org/wiki/Nonnegative): $p(x)\geq 0$ for all $x\in X.$

Some authors include non-negativity as part of the definition of "norm", although this is not necessary. Although this article defined "*positive*" to be a synonym of "positive definite", some authors instead define "*positive*" to be a synonym of "non-negative"; these definitions are not equivalent.

### Notation

If a norm $p:X\to \mathbb {R}$ is given on a vector space $X,$ then the norm of a vector $z\in X$ is usually denoted by enclosing it within double vertical lines: $\|z\|=p(z)$, as proposed by [Stefan Banach](https://en.wikipedia.org/wiki/Stefan_Banach) in his doctoral thesis from 1920. Such notation is also sometimes used if $p$ is only a seminorm. For the length of a vector in Euclidean space (which is an example of a norm, as [explained below](#Euclidean_norm)), the notation $|x|$ with single vertical lines is also widespread.

## Examples

Every (real or complex) vector space admits a norm: If $x_{\bullet }=\left(x_{i}\right)_{i\in I}$ is a [Hamel basis](https://en.wikipedia.org/wiki/Hamel_basis) for a vector space $X$ then the real-valued map that sends $x=\sum _{i\in I}s_{i}x_{i}\in X$ (where all but finitely many of the scalars $s_{i}$ are $0$) to $\sum _{i\in I}\left|s_{i}\right|$ is a norm on $X.$ There are also a large number of norms that exhibit additional properties that make them useful for specific problems.

### Absolute-value norm

The [absolute value](https://en.wikipedia.org/wiki/Absolute_value) $|x|$ is a norm on the vector space formed by the [real](https://en.wikipedia.org/wiki/Real_number) or [complex numbers](https://en.wikipedia.org/wiki/Complex_number). The complex numbers form a [one-dimensional vector space](https://en.wikipedia.org/wiki/Dimension_(vector_space) "Dimension (vector space)") over themselves and a two-dimensional vector space over the reals; the absolute value is a norm for these two structures.

Any norm $p$ on a one-dimensional vector space $X$ is equivalent (up to scaling) to the absolute value norm, meaning that there is a norm-preserving [isomorphism](https://en.wikipedia.org/wiki/Isomorphism) of vector spaces $f:\mathbb {F} \to X,$ where $\mathbb {F}$ is either $\mathbb {R}$ or $\mathbb {C} ,$ and norm-preserving means that $|x|=p(f(x)).$ This isomorphism is given by sending $1\in \mathbb {F}$ to a vector of norm $1,$ which exists since such a vector is obtained by multiplying any non-zero vector by the inverse of its norm.

### Euclidean norm

On the $n$-dimensional [Euclidean space](https://en.wikipedia.org/wiki/Euclidean_space) $\mathbb {R} ^{n},$ the intuitive notion of length of the vector ${\boldsymbol {x}}=\left(x_{1},x_{2},\ldots ,x_{n}\right)$ is captured by the formula 

$$
\|{\boldsymbol {x}}\|_{2}:={\sqrt {x_{1}^{2}+\cdots +x_{n}^{2}}}.
$$

This is the **Euclidean norm**, which gives the ordinary distance from the origin to the point ***X***—a consequence of the [Pythagorean theorem](https://en.wikipedia.org/wiki/Pythagorean_theorem). This operation may also be referred to as "SRSS", which is an acronym for the **s**quare **r**oot of the **s**um of **s**quares.

The Euclidean norm is by far the most commonly used norm on $\mathbb {R} ^{n},$ but there are other norms on this vector space as will be shown below. However, all these norms are equivalent in the sense that they all define the same topology on finite-dimensional spaces.

The [inner product](https://en.wikipedia.org/wiki/Inner_product) of two vectors of a [Euclidean vector space](https://en.wikipedia.org/wiki/Euclidean_vector_space) is the [dot product](https://en.wikipedia.org/wiki/Dot_product) of their [coordinate vectors](https://en.wikipedia.org/wiki/Coordinate_vector) over an [orthonormal basis](https://en.wikipedia.org/wiki/Orthonormal_basis). Hence, the Euclidean norm can be written in a [coordinate-free](https://en.wikipedia.org/wiki/Coordinate-free) way as 

$$
\|{\boldsymbol {x}}\|:={\sqrt {{\boldsymbol {x}}\cdot {\boldsymbol {x}}}}.
$$

The Euclidean norm is also called the **quadratic norm**, **$L^{2}$ norm**, **$\ell ^{2}$ norm**, **2-norm**, or **square norm**; see [$L^{p}$ space](https://en.wikipedia.org/wiki/Lp_space). It defines a [distance function](https://en.wikipedia.org/wiki/Distance_function) called the **Euclidean length**, **$L^{2}$ distance**, or **$\ell ^{2}$ distance**.

The set of vectors in $\mathbb {R} ^{n+1}$ whose Euclidean norm is a given positive constant forms an [$n$-sphere](https://en.wikipedia.org/wiki/N-sphere).

#### Euclidean norm of complex numbers

The Euclidean norm of a [complex number](https://en.wikipedia.org/wiki/Complex_number) is the [absolute value](https://en.wikipedia.org/wiki/Absolute_value#Complex_numbers) (also called the **modulus**) of it, if the [complex plane](https://en.wikipedia.org/wiki/Complex_plane) is identified with the [Euclidean plane](https://en.wikipedia.org/wiki/Euclidean_plane) $\mathbb {R} ^{2}.$ This identification of the complex number $x+iy$ as a vector in the Euclidean plane, makes the quantity ${\sqrt {x^{2}+y^{2}}}$ (as first suggested by Euler) the Euclidean norm associated with the complex number. For $z=x+iy$, the norm can also be written as ${\sqrt {{\bar {z}}z}}$ where ${\bar {z}}$ is the [complex conjugate](https://en.wikipedia.org/wiki/Complex_conjugate) of $z\,.$

### Quaternions and octonions

There are exactly four [Euclidean Hurwitz algebras](https://en.wikipedia.org/wiki/Hurwitz%27s_theorem_(composition_algebras) "Hurwitz's theorem (composition algebras)") over the [real numbers](https://en.wikipedia.org/wiki/Real_number). These are the real numbers $\mathbb {R} ,$ the complex numbers $\mathbb {C} ,$ the [quaternions](https://en.wikipedia.org/wiki/Quaternion) $\mathbb {H} ,$ and lastly the [octonions](https://en.wikipedia.org/wiki/Octonion) $\mathbb {O} ,$ where the dimensions of these spaces over the real numbers are $1,2,4,{\text{ and }}8,$ respectively. The canonical norms on $\mathbb {R}$ and $\mathbb {C}$ are their [absolute value](https://en.wikipedia.org/wiki/Absolute_value) functions, as discussed previously.

The canonical norm on $\mathbb {H}$ of [quaternions](https://en.wikipedia.org/wiki/Quaternion) is defined by 

$$
\lVert q\rVert ={\sqrt {\,qq^{*}~}}={\sqrt {\,q^{*}q~}}={\sqrt {\,a^{2}+b^{2}+c^{2}+d^{2}~}}
$$

 for every quaternion $q=a+b\,\mathbf {i} +c\,\mathbf {j} +d\,\mathbf {k}$ in $\mathbb {H} .$ This is the same as the Euclidean norm on $\mathbb {H}$ considered as the vector space $\mathbb {R} ^{4}.$ Similarly, the canonical norm on the [octonions](https://en.wikipedia.org/wiki/Octonion) is just the Euclidean norm on $\mathbb {R} ^{8}.$

### Finite-dimensional complex normed spaces

On an $n$-dimensional [complex space](https://en.wikipedia.org/wiki/Complex_coordinate_space) $\mathbb {C} ^{n},$ the most common norm is 

$$
\|{\boldsymbol {z}}\|:={\sqrt {\left|z_{1}\right|^{2}+\cdots +\left|z_{n}\right|^{2}}}={\sqrt {z_{1}{\bar {z}}_{1}+\cdots +z_{n}{\bar {z}}_{n}}}.
$$

In this case, the norm can be expressed as the [square root](https://en.wikipedia.org/wiki/Square_root) of the [inner product](https://en.wikipedia.org/wiki/Inner_product) of the vector and itself: 

$$
\|{\boldsymbol {x}}\|:={\sqrt {{\boldsymbol {x}}^{H}~{\boldsymbol {x}}}},
$$

 where ${\boldsymbol {x}}$ is represented as a [column vector](https://en.wikipedia.org/wiki/Column_vector) ${\begin{bmatrix}x_{1}\;x_{2}\;\dots \;x_{n}\end{bmatrix}}^{\rm {T}}$ and ${\boldsymbol {x}}^{H}$ denotes its [conjugate transpose](https://en.wikipedia.org/wiki/Conjugate_transpose).

This formula is valid for any [inner product space](https://en.wikipedia.org/wiki/Inner_product_space), including Euclidean and complex spaces. For complex spaces, the inner product is equivalent to the [complex dot product](https://en.wikipedia.org/wiki/Complex_dot_product). Hence the formula in this case can also be written using the following notation: 

$$
\|{\boldsymbol {x}}\|:={\sqrt {{\boldsymbol {x}}\cdot {\boldsymbol {x}}}}.
$$

### Taxicab norm or Manhattan norm

$$
\|{\boldsymbol {x}}\|_{1}:=\sum _{i=1}^{n}\left|x_{i}\right|.
$$

 The name relates to the distance a taxi has to drive in a rectangular [street grid](https://en.wikipedia.org/wiki/Street_grid) (like that of the [New York](https://en.wikipedia.org/wiki/New_York_City) borough of [Manhattan](https://en.wikipedia.org/wiki/Manhattan)) to get from the origin to the point $x.$

The set of vectors whose 1-norm is a given constant forms the surface of a [cross polytope](https://en.wikipedia.org/wiki/Cross_polytope), which has dimension equal to the dimension of the vector space minus 1. The Taxicab norm is also called the **$\ell ^{1}$ norm**. The distance derived from this norm is called the [Manhattan distance](https://en.wikipedia.org/wiki/Manhattan_distance) or **$\ell ^{1}$ distance**.

The 1-norm is simply the sum of the absolute values of the columns.

In contrast, 

$$
\sum _{i=1}^{n}x_{i}
$$

 is not a norm because it may yield negative results.

### *p*-norm

Let $p\geq 1$ be a real number. The $p$-norm (also called $\ell ^{p}$-norm) of vector $\mathbf {x} =(x_{1},\ldots ,x_{n})$ is 

$$
\|\mathbf {x} \|_{p}:={\biggl (}\sum _{i=1}^{n}\left|x_{i}\right|^{p}{\biggr )}^{1/p}.
$$

 For $p=1,$ we get the [taxicab norm](#Taxicab_norm_or_Manhattan_norm), for $p=2$ we get the [Euclidean norm](#Euclidean_norm), and as $p$ approaches $\infty$ the $p$-norm approaches the [infinity norm](https://en.wikipedia.org/wiki/Uniform_norm) or [maximum norm](#Maximum_norm_.28special_case_of:_infinity_norm.2C_uniform_norm.2C_or_supremum_norm.29): 

$$
\|\mathbf {x} \|_{\infty }:=\max _{i}\left|x_{i}\right|.
$$

 The $p$-norm is related to the [generalized mean](https://en.wikipedia.org/wiki/Generalized_mean) or power mean.

For $p=2,$ the $\|\,\cdot \,\|_{2}$-norm is even induced by a canonical [inner product](https://en.wikipedia.org/wiki/Inner_product) $\langle \,\cdot ,\,\cdot \rangle ,$ meaning that $\|\mathbf {x} \|_{2}={\sqrt {\langle \mathbf {x} ,\mathbf {x} \rangle }}$ for all vectors $\mathbf {x} .$ This inner product can be expressed in terms of the norm by using the [polarization identity](https://en.wikipedia.org/wiki/Polarization_identity). On $\ell ^{2},$ this inner product is the *Euclidean inner product* defined by 

$$
\langle \left(x_{n}\right)_{n},\left(y_{n}\right)_{n}\rangle _{\ell ^{2}}~=~\sum _{n}{\overline {x_{n}}}y_{n}
$$

 while for the space $L^{2}(X,\mu )$ associated with a [measure space](https://en.wikipedia.org/wiki/Measure_(mathematics) "Measure (mathematics)") $(X,\Sigma ,\mu ),$ which consists of all [square-integrable functions](https://en.wikipedia.org/wiki/Square-integrable_function), this inner product is 

$$
\langle f,g\rangle _{L^{2}}=\int _{X}{\overline {f(x)}}g(x)\,\mathrm {d} x.
$$

This definition is still of some interest for $0<p<1,$ but the resulting function does not define a norm, because it violates the [triangle inequality](https://en.wikipedia.org/wiki/Triangle_inequality). What is true for this case of $0<p<1,$ even in the measurable analog, is that the corresponding $L^{p}$ class is a vector space, and it is also true that the function 

$$
\int _{X}|f(x)-g(x)|^{p}~\mathrm {d} \mu
$$

 (without $p$th root) defines a distance that makes $L^{p}(X)$ into a complete metric [topological vector space](https://en.wikipedia.org/wiki/Topological_vector_space). These spaces are of great interest in [functional analysis](https://en.wikipedia.org/wiki/Functional_analysis), [probability theory](https://en.wikipedia.org/wiki/Probability_theory) and [harmonic analysis](https://en.wikipedia.org/wiki/Harmonic_analysis). However, aside from trivial cases, this topological vector space is not locally convex, and has no continuous non-zero linear forms. Thus the topological dual space contains only the zero functional.

The partial derivative of the $p$-norm is given by 

$$
{\frac {\partial }{\partial x_{k}}}\|\mathbf {x} \|_{p}={\frac {x_{k}\left|x_{k}\right|^{p-2}}{\|\mathbf {x} \|_{p}^{p-1}}}.
$$

The derivative with respect to $x,$ therefore, is 

$$
{\frac {\partial \|\mathbf {x} \|_{p}}{\partial \mathbf {x} }}=\left({\frac {\mathbf {x} \circ |\mathbf {x} |^{p-2}}{\|\mathbf {x} \|_{p}^{p-1}}}\right)^{\top }.
$$

 where $\circ$ denotes [Hadamard product](https://en.wikipedia.org/wiki/Hadamard_product_(matrices) "Hadamard product (matrices)") and $|\cdot |$ is used for absolute value of each component of the vector.

For the special case of $p=2,$ this becomes 

$$
{\frac {\partial }{\partial x_{k}}}\|\mathbf {x} \|_{2}={\frac {x_{k}}{\|\mathbf {x} \|_{2}}},
$$

 or 

$$
{\frac {\partial }{\partial \mathbf {x} }}\|\mathbf {x} \|_{2}=\left({\frac {\mathbf {x} }{\|\mathbf {x} \|_{2}}}\right)^{\top }.
$$

### Maximum norm (special case of: infinity norm, uniform norm, or supremum norm)

![[media/867b796029a0963ffe636d34f64408257afeb59a.png]]
$\|x\|_{\infty }=1$

If $\mathbf {x}$ is some vector such that $\mathbf {x} =(x_{1},x_{2},\ldots ,x_{n}),$ then: 

$$
\|\mathbf {x} \|_{\infty }:=\max \left(\left|x_{1}\right|,\ldots ,\left|x_{n}\right|\right).
$$

The set of vectors whose infinity norm is a given constant, $c,$ forms the surface of a [hypercube](https://en.wikipedia.org/wiki/Hypercube) with edge length $2c.$

### Energy norm

The energy norm of a vector ${\boldsymbol {x}}=\left(x_{1},x_{2},\ldots ,x_{n}\right)\in \mathbb {R} ^{n}$ is defined in terms of a [symmetric](https://en.wikipedia.org/wiki/Symmetric_matrix) [positive definite](https://en.wikipedia.org/wiki/Definite_matrix) matrix $A\in \mathbb {R} ^{n}$ as

$$
{\|{\boldsymbol {x}}\|}_{A}:={\sqrt {{\boldsymbol {x}}^{T}\cdot A\cdot {\boldsymbol {x}}}}.
$$

It is clear that if $A$ is the [identity matrix](https://en.wikipedia.org/wiki/Identity_matrix), this norm corresponds to the [Euclidean norm](#Euclidean_norm). If $A$ is diagonal, this norm is also called a *weighted norm*. The energy norm is induced by the [inner product](https://en.wikipedia.org/wiki/Inner_product_space) given by $\langle {\boldsymbol {x}},{\boldsymbol {y}}\rangle _{A}:={\boldsymbol {x}}^{T}\cdot A\cdot {\boldsymbol {y}}$ for ${\boldsymbol {x}},{\boldsymbol {y}}\in \mathbb {R} ^{n}$.

In general, the value of the norm is dependent on the [spectrum](https://en.wikipedia.org/wiki/Spectrum_of_a_matrix) of $A$: For a vector ${\boldsymbol {x}}$ with a Euclidean norm of one, the value of ${\|{\boldsymbol {x}}\|}_{A}$ is bounded from below and above by the smallest and largest absolute [[Eigenvalues and Eigenvectors|eigenvalues]] of $A$ respectively, where the bounds are achieved if ${\boldsymbol {x}}$ coincides with the corresponding (normalized) eigenvectors. Based on the symmetric [matrix square root](https://en.wikipedia.org/wiki/Square_root_of_a_matrix) $A^{1/2}$, the energy norm of a vector can be written in terms of the standard Euclidean norm as

$$
{\|{\boldsymbol {x}}\|}_{A}={\|A^{1/2}{\boldsymbol {x}}\|}_{2}.
$$

### Zero norm

In probability and functional analysis, the zero norm induces a complete metric topology for the space of [measurable functions](https://en.wikipedia.org/wiki/Measurable_function) and for the [F-space](https://en.wikipedia.org/wiki/F-space) of sequences with F–norm $(x_{n})\mapsto \sum _{n}{2^{-n}x_{n}/(1+x_{n})}.$ Here we mean by *F-norm* some real-valued function $\lVert \cdot \rVert$ on an F-space with distance $d,$ such that $\lVert x\rVert =d(x,0).$ The *F*-norm described above is not a norm in the usual sense because it lacks the required homogeneity property.

#### Hamming distance of a vector from zero

In [metric geometry](https://en.wikipedia.org/wiki/Metric_geometry), the [discrete metric](https://en.wikipedia.org/wiki/Discrete_metric) takes the value one for distinct points and zero otherwise. When applied coordinate-wise to the elements of a vector space, the discrete distance defines the *[Hamming distance](https://en.wikipedia.org/wiki/Hamming_distance)*, which is important in [coding](https://en.wikipedia.org/wiki/Coding_theory) and [information theory](https://en.wikipedia.org/wiki/Information_theory). In the field of real or complex numbers, the distance of the discrete metric from zero is not homogeneous in the non-zero point; indeed, the distance from zero remains one as its non-zero argument approaches zero. However, the discrete distance of a number from zero does satisfy the other properties of a norm, namely the triangle inequality and positive definiteness. When applied component-wise to vectors, the discrete distance from zero behaves like a non-homogeneous "norm", which counts the number of non-zero components in its vector argument; again, this non-homogeneous "norm" is discontinuous.

In [signal processing](https://en.wikipedia.org/wiki/Signal_processing) and [statistics](https://en.wikipedia.org/wiki/Statistics), [David Donoho](https://en.wikipedia.org/wiki/David_Donoho) referred to the *zero* **"***norm***"** with quotation marks. Following Donoho's notation, the zero "norm" of $x$ is simply the number of non-zero coordinates of $x,$ or the Hamming distance of the vector from zero. When this "norm" is localized to a bounded set, it is the limit of $p$-norms as $p$ approaches 0. Of course, the zero "norm" is **not** truly a norm, because it is not [positive homogeneous](https://en.wikipedia.org/wiki/Homogeneous_function#Positive_homogeneity). Indeed, it is not even an F-norm in the sense described above, since it is discontinuous, jointly and severally, with respect to the scalar argument in scalar–vector multiplication and with respect to its vector argument. [Abusing terminology](https://en.wikipedia.org/wiki/Abuse_of_terminology), some engineers<sup>\[*[who?](https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Words_to_watch#Unsupported_attributions)*\]</sup> omit Donoho's quotation marks and inappropriately call the number-of-non-zeros function the $L^{0}$ norm, echoing the notation for the [Lebesgue space](https://en.wikipedia.org/wiki/Lp_space) of [measurable functions](https://en.wikipedia.org/wiki/Measurable_function).

### Infinite dimensions

The generalization of the above norms to an infinite number of components leads to [$\ell ^{p}$ and $L^{p}$ spaces](https://en.wikipedia.org/wiki/Lp_space) for $p\geq 1\,,$ with norms

$$
\|x\|_{p}={\bigg (}\sum _{i\in \mathbb {N} }\left|x_{i}\right|^{p}{\bigg )}^{1/p}{\text{ and }}\ \|f\|_{p,X}={\bigg (}\int _{X}|f(x)|^{p}~\mathrm {d} x{\bigg )}^{1/p}
$$

for complex-valued sequences and functions on $X\subseteq \mathbb {R} ^{n}$ respectively, which can be further generalized (see [Haar measure](https://en.wikipedia.org/wiki/Haar_measure)). These norms are also valid in the limit as $p\rightarrow +\infty$, giving a [supremum norm](https://en.wikipedia.org/wiki/Supremum_norm), and are called $\ell ^{\infty }$ and $L^{\infty }\,.$

Any [inner product](https://en.wikipedia.org/wiki/Inner_product) induces in a natural way the norm $\|x\|:={\sqrt {\langle x,x\rangle }}.$

Other examples of infinite-dimensional normed vector spaces can be found in the [Banach space](https://en.wikipedia.org/wiki/Banach_space) article.

Generally, these norms do not give the same topologies. For example, an infinite-dimensional $\ell ^{p}$ space gives a [strictly finer topology](https://en.wikipedia.org/wiki/Finer_topology) than an infinite-dimensional $\ell ^{q}$ space when $p<q\,.$

### Composite norms

Other norms on $\mathbb {R} ^{n}$ can be constructed by combining the above; for example 

$$
\|x\|:=2\left|x_{1}\right|+{\sqrt {3\left|x_{2}\right|^{2}+\max(\left|x_{3}\right|,2\left|x_{4}\right|)^{2}}}
$$

 is a norm on $\mathbb {R} ^{4}.$

For any norm and any [injective](https://en.wikipedia.org/wiki/Injective_function) [[Linear Transformation]] $A$ we can define a new norm of $x,$ equal to 

$$
\|Ax\|.
$$

 In 2D, with $A$ a rotation by 45° and a suitable scaling, this changes the taxicab norm into the maximum norm. Each $A$ applied to the taxicab norm, up to inversion and interchanging of axes, gives a different unit ball: a [parallelogram](https://en.wikipedia.org/wiki/Parallelogram) of a particular shape, size, and orientation.

In 3D, this is similar but different for the 1-norm ([octahedrons](https://en.wikipedia.org/wiki/Octahedron)) and the maximum norm ([prisms](https://en.wikipedia.org/wiki/Prism_(geometry) "Prism (geometry)") with parallelogram base).

There are examples of norms that are not defined by "entrywise" formulas. For instance, the [Minkowski functional](https://en.wikipedia.org/wiki/Minkowski_functional) of a centrally-symmetric convex body in $\mathbb {R} ^{n}$ (centered at zero) defines a norm on $\mathbb {R} ^{n}$ (see [§ Classification of seminorms: absolutely convex absorbing sets](#Classification_of_seminorms:_absolutely_convex_absorbing_sets) below).

All the above formulas also yield norms on $\mathbb {C} ^{n}$ without modification.

There are also norms on spaces of matrices (with real or complex entries), the so-called [matrix norms](https://en.wikipedia.org/wiki/Matrix_norms).

### In abstract algebra

Let $E$ be a [finite extension](https://en.wikipedia.org/wiki/Finite_extension) of a field $k$ of [inseparable degree](https://en.wikipedia.org/wiki/Inseparable_degree) $p^{\mu },$ and let $k$ have algebraic closure $K.$ If the distinct [embeddings](https://en.wikipedia.org/wiki/Field_homomorphism) of $E$ are $\left\{\sigma _{j}\right\}_{j},$ then the **Galois-theoretic norm** of an element $\alpha \in E$ is the value $\left(\prod _{j}{\sigma _{k}(\alpha )}\right)^{p^{\mu }}.$ As that function is homogeneous of degree [$[E:k]$](https://en.wikipedia.org/wiki/Degree_of_a_field_extension "Degree of a field extension"), the Galois-theoretic norm is not a norm in the sense of this article. However, the $[E:k]$-th root of the norm (assuming that concept makes sense) is a norm.

#### Composition algebras

The concept of norm $N(z)$ in [composition algebras](https://en.wikipedia.org/wiki/Composition_algebra) does *not* share the usual properties of a norm since [null vectors](https://en.wikipedia.org/wiki/Null_vector) are allowed. A composition algebra $(A,{}^{*},N)$ consists of an [algebra over a field](https://en.wikipedia.org/wiki/Algebra_over_a_field) $A,$ an [involution](https://en.wikipedia.org/wiki/Involution_(mathematics) "Involution (mathematics)") ${}^{*},$ and a [quadratic form](https://en.wikipedia.org/wiki/Quadratic_form) [$N(z)=zz^{*}$](https://en.wikipedia.org/wiki/Degree_of_a_field_extension) called the "norm".

The characteristic feature of composition algebras is the [homomorphism](https://en.wikipedia.org/wiki/Homomorphism) property of $N$: for the product $wz$ of two elements $w$ and $z$ of the composition algebra, its norm satisfies $N(wz)=N(w)N(z).$ In the case of [division algebras](https://en.wikipedia.org/wiki/Division_algebra) $\mathbb {R} ,$ $\mathbb {C} ,$ $\mathbb {H} ,$ and $\mathbb {O}$ the composition algebra norm is the square of the norm discussed above. In those cases the norm is a [definite quadratic form](https://en.wikipedia.org/wiki/Definite_quadratic_form). In the [split algebras](https://en.wikipedia.org/wiki/Split_algebra) the norm is an [isotropic quadratic form](https://en.wikipedia.org/wiki/Isotropic_quadratic_form).

## Properties

For any norm $p:X\to \mathbb {R}$ on a vector space $X,$ the [reverse triangle inequality](https://en.wikipedia.org/wiki/Reverse_triangle_inequality) holds: 

$$
p(x\pm y)\geq |p(x)-p(y)|{\text{ for all }}x,y\in X.
$$

 If $u:X\to Y$ is a continuous linear map between normed spaces, then the norm of $u$ and the norm of the [transpose](https://en.wikipedia.org/wiki/Transpose) of $u$ are equal.

For the [$L^{p}$ norms](https://en.wikipedia.org/wiki/Lp_space), we have [Hölder's inequality](https://en.wikipedia.org/wiki/H%C3%B6lder%27s_inequality) 

$$
|\langle x,y\rangle |\leq \|x\|_{p}\|y\|_{q}\qquad {\frac {1}{p}}+{\frac {1}{q}}=1.
$$

 A special case of this is the [Cauchy–Schwarz inequality](https://en.wikipedia.org/wiki/Cauchy%E2%80%93Schwarz_inequality): 

$$
\left|\langle x,y\rangle \right|\leq \|x\|_{2}\|y\|_{2}.
$$

![[media/2b97ce4c5e5217e0986a672ba54e401203282eea.png]]
Illustrations of [unit circles](https://en.wikipedia.org/wiki/Unit_circle) in different norms.

Every norm is a [seminorm](https://en.wikipedia.org/wiki/Seminorm) and thus satisfies all [properties of the latter](https://en.wikipedia.org/wiki/Seminorm#Algebraic_properties). In turn, every seminorm is a [sublinear function](https://en.wikipedia.org/wiki/Sublinear_function) and thus satisfies all [properties of the latter](https://en.wikipedia.org/wiki/Sublinear_function#Properties). In particular, every norm is a [convex function](https://en.wikipedia.org/wiki/Convex_function).

### Equivalence

The concept of [unit circle](https://en.wikipedia.org/wiki/Unit_circle) (the set of all vectors of norm 1) is different in different norms: for the 1-norm, the unit circle is a [square](https://en.wikipedia.org/wiki/Square_(geometry)) oriented as a diamond; for the 2-norm (Euclidean norm), it is the well-known unit [circle](https://en.wikipedia.org/wiki/Circle); while for the infinity norm, it is an axis-aligned square. For any $p$-norm, it is a [superellipse](https://en.wikipedia.org/wiki/Superellipse) with congruent axes (see the accompanying illustration). Due to the definition of the norm, the unit circle must be [convex](https://en.wikipedia.org/wiki/Convex_set) and centrally symmetric (therefore, for example, the unit ball may be a rectangle but cannot be a triangle, and $p\geq 1$ for a $p$-norm).

In terms of the vector space, the seminorm defines a [topology](https://en.wikipedia.org/wiki/Topology) on the space, and this is a [Hausdorff](https://en.wikipedia.org/wiki/Hausdorff_space) topology precisely when the seminorm can distinguish between distinct vectors, which is again equivalent to the seminorm being a norm. The topology thus defined (by either a norm or a seminorm) can be understood either in terms of sequences or open sets. A [sequence](https://en.wikipedia.org/wiki/Sequence) of vectors $\{v_{n}\}$ is said to [converge](https://en.wikipedia.org/wiki/Modes_of_convergence) in norm to $v,$ if $\left\|v_{n}-v\right\|\to 0$ as $n\to \infty .$ Equivalently, the topology consists of all sets that can be represented as a union of open [balls](https://en.wikipedia.org/wiki/Ball_(mathematics) "Ball (mathematics)"). If $(X,\|\cdot \|)$ is a normed space then $\|x-y\|=\|x-z\|+\|z-y\|{\text{ for all }}x,y\in X{\text{ and }}z\in [x,y].$

Two norms $\|\cdot \|_{\alpha }$ and $\|\cdot \|_{\beta }$ on a vector space $X$ are called **equivalent** if they induce the same topology, which happens if and only if there exist positive real numbers $C$ and $D$ such that for all $x\in X$ 

$$
C\|x\|_{\alpha }\leq \|x\|_{\beta }\leq D\|x\|_{\alpha }.
$$

 For instance, if $p>r\geq 1$ on $\mathbb {C} ^{n},$ then 

$$
\|x\|_{p}\leq \|x\|_{r}\leq n^{(1/r-1/p)}\|x\|_{p}.
$$

In particular, 

$$
\|x\|_{2}\leq \|x\|_{1}\leq {\sqrt {n}}\|x\|_{2}
$$

$$
\|x\|_{\infty }\leq \|x\|_{2}\leq {\sqrt {n}}\|x\|_{\infty }
$$

$$
\|x\|_{\infty }\leq \|x\|_{1}\leq n\|x\|_{\infty },
$$

 That is, 

$$
\|x\|_{\infty }\leq \|x\|_{2}\leq \|x\|_{1}\leq {\sqrt {n}}\|x\|_{2}\leq n\|x\|_{\infty }.
$$

 If the vector space is a finite-dimensional real or complex one, all norms are equivalent. On the other hand, in the case of infinite-dimensional vector spaces, not all norms are equivalent.

Equivalent norms define the same notions of continuity and convergence and for many purposes do not need to be distinguished. To be more precise the uniform structure defined by equivalent norms on the vector space is [uniformly isomorphic](https://en.wikipedia.org/wiki/Uniformly_isomorphic). This form of equivalence should not be mistaken to imply that norms are always interchangeable. In the context of model fitting, for example, different norms can lead to different fits and different algorithm efficiencies.

## Classification of seminorms: absolutely convex absorbing sets

All seminorms on a vector space $X$ can be classified in terms of [absolutely convex](https://en.wikipedia.org/wiki/Absolutely_convex) [absorbing subsets](https://en.wikipedia.org/wiki/Absorbing_set) $A$ of $X.$ To each such subset corresponds a seminorm $p_{A}$ called the **[gauge](https://en.wikipedia.org/wiki/Minkowski_functional)** of $A,$ defined as 

$$
p_{A}(x):=\inf\{r\in \mathbb {R} :r>0,x\in rA\}
$$

 where $\inf _{}$ is the [infimum](https://en.wikipedia.org/wiki/Infimum), with the property that 

$$
\left\{x\in X:p_{A}(x)<1\right\}~\subseteq ~A~\subseteq ~\left\{x\in X:p_{A}(x)\leq 1\right\}.
$$

 Conversely:

Any [locally convex topological vector space](https://en.wikipedia.org/wiki/Locally_convex_topological_vector_space) has a [local basis](https://en.wikipedia.org/wiki/Local_basis) consisting of absolutely convex sets. A common method to construct such a basis is to use a family $(p)$ of seminorms $p$ that [separates points](https://en.wikipedia.org/wiki/Separation_axiom): the collection of all finite intersections of sets $\{p<1/n\}$ turns the space into a [locally convex topological vector space](https://en.wikipedia.org/wiki/Locally_convex_topological_vector_space) so that every p is [continuous](https://en.wikipedia.org/wiki/Continuous_function).

Such a method is used to design [weak and weak\* topologies](https://en.wikipedia.org/wiki/Weak_topology).

norm case:

Suppose now that $(p)$ contains a single $p:$ since $(p)$ is [separating](https://en.wikipedia.org/wiki/Separation_axiom), $p$ is a norm, and $A=\{p<1\}$ is its open [unit ball](https://en.wikipedia.org/wiki/Unit_ball). Then $A$ is an absolutely convex [bounded](https://en.wikipedia.org/wiki/Bounded_set) neighbourhood of 0, and $p=p_{A}$ is continuous.

The converse is due to [Andrey Kolmogorov](https://en.wikipedia.org/wiki/Andrey_Kolmogorov): any locally convex and locally bounded topological vector space is [normable](https://en.wikipedia.org/wiki/Normable). Precisely:

If $X$ is an absolutely convex bounded neighbourhood of 0, the gauge $g_{X}$ (so that $X=\{g_{X}<1\}$ is a norm.

## See also

- [Asymmetric norm](https://en.wikipedia.org/wiki/Asymmetric_norm) – Generalization of the concept of a norm
- [F-seminorm](https://en.wikipedia.org/wiki/F-seminorm) – Topological vector space whose topology can be defined by a metricPages displaying short descriptions of redirect targets
- [Gowers norm](https://en.wikipedia.org/wiki/Gowers_norm) – Class of norms in additive combinatorics
- [Kadec norm](https://en.wikipedia.org/wiki/Kadec_norm) – All infinite-dimensional, separable Banach spaces are homeomorphicPages displaying short descriptions of redirect targets
- [Least-squares spectral analysis](https://en.wikipedia.org/wiki/Least-squares_spectral_analysis) – Periodicity computation method
- [Mahalanobis distance](https://en.wikipedia.org/wiki/Mahalanobis_distance) – Statistical distance measure
- [Magnitude (mathematics)](https://en.wikipedia.org/wiki/Magnitude_(mathematics) "Magnitude (mathematics)") – Property determining comparison and ordering
- [Matrix norm](https://en.wikipedia.org/wiki/Matrix_norm) – Norm on a vector space of matrices
- [Minkowski distance](https://en.wikipedia.org/wiki/Minkowski_distance) – Vector distance using pth powers
- [Minkowski functional](https://en.wikipedia.org/wiki/Minkowski_functional) – Function made from a set
- [Operator norm](https://en.wikipedia.org/wiki/Operator_norm) – Measure of the "size" of linear operators
- [Paranorm](https://en.wikipedia.org/wiki/Paranorm) – Topological vector space whose topology can be defined by a metricPages displaying short descriptions of redirect targets
- [Relation of norms and metrics](https://en.wikipedia.org/wiki/Relation_of_norms_and_metrics) – Mathematical space with a notion of distancePages displaying short descriptions of redirect targets
- [Seminorm](https://en.wikipedia.org/wiki/Seminorm) – Mathematical function
- [Sublinear function](https://en.wikipedia.org/wiki/Sublinear_function) – Type of function in linear algebra

## References

1.  ^   Knapp, A.W. (2005). *Basic Real Analysis*. Birkhäuser. p. [1](https://en.wikipedia.org/wiki/1)(https://books.google.com/books?id=4ZZCAAAAQBAJ&pg=279). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-817-63250-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-817-63250-2).
2.  ["Pseudonorm"](https://www.spektrum.de/lexikon/mathematik/pseudonorm/8161). *www.spektrum.de* (in German). Retrieved 2022-05-12.
3.  Hyers, D. H. (1939-09-01). ["Pseudo-normed linear spaces and Abelian groups"](https://dx.doi.org/10.1215/s0012-7094-39-00551-x). *Duke Mathematical Journal*. **5** (3). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1215/s0012-7094-39-00551-x](https://doi.org/10.1215%2Fs0012-7094-39-00551-x). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0012-7094](https://search.worldcat.org/issn/0012-7094).
4.  Pugh, C.C. (2015). *Real Mathematical Analysis*. Springer. p. [page 28](https://books.google.com/books?id=2NVJCgAAQBAJ&pg=PA28). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-319-17770-0](https://en.wikipedia.org/wiki/Special:BookSources/978-3-319-17770-0). Prugovečki, E. (1981). *Quantum Mechanics in Hilbert Space*. p. [page 20](https://books.google.com/books?id=GxmQxn2PF3IC&pg=PA20).
5.  ^   , p. 200.
6.  Rudin, W. (1991). *Functional Analysis*. p. 25.
7.  , pp. 120–121.
8.  , pp. 20–21.
9.  ^    Weisstein, Eric W. ["Vector Norm"](https://mathworld.wolfram.com/VectorNorm.html). *mathworld.wolfram.com*. Retrieved 2020-08-24.
10. Chopra, Anil (2012). *Dynamics of Structures, 4th Ed*. Prentice-Hall. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-13-285803-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-13-285803-8).
11. Weisstein, Eric W. ["Norm"](https://mathworld.wolfram.com/Norm.html). *mathworld.wolfram.com*. Retrieved 2020-08-24.
12. Except in $\mathbb {R} ^{1},$ where it coincides with the Euclidean norm, and $\mathbb {R} ^{0},$ where it is trivial.
13. Saad, Yousef (2003), *Iterative Methods for Sparse Linear Systems*, p. 32, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-89871-534-7](https://en.wikipedia.org/wiki/Special:BookSources/978-0-89871-534-7)
14. Rolewicz, Stefan (1987), *Functional analysis and control theory: Linear systems*, Mathematics and its Applications (East European Series), vol. 29 (Translated from the Polish by Ewa Bednarczuk ed.), Dordrecht; Warsaw: D. Reidel Publishing Co.; PWN—Polish Scientific Publishers, pp. xvi, 524, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-94-015-7758-8](https://doi.org/10.1007%2F978-94-015-7758-8), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [90-277-2186-6](https://en.wikipedia.org/wiki/Special:BookSources/90-277-2186-6), [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0920371](https://mathscinet.ams.org/mathscinet-getitem?mr=0920371), [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [13064804](https://search.worldcat.org/oclc/13064804)
15. Lang, Serge (2002) \[1993\]. *Algebra* (Revised 3rd ed.). New York: Springer Verlag. p. 284. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-95385-X](https://en.wikipedia.org/wiki/Special:BookSources/0-387-95385-X).
16. , pp. 242–243.
17. ^   [Golub, Gene](https://en.wikipedia.org/wiki/Gene_H._Golub); Van Loan, Charles F. (1996). *Matrix Computations* (Third ed.). Baltimore: The Johns Hopkins University Press. p. 53. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-8018-5413-X](https://en.wikipedia.org/wiki/Special:BookSources/0-8018-5413-X).
18. , pp. 107–113.
19. Conrad, Keith. ["Equivalence of norms"](https://kconrad.math.uconn.edu/blurbs/gradnumthy/equivnorms.pdf) (PDF). *kconrad.math.uconn.edu*. Retrieved September 7, 2020.
20. ["Relation between p-norms"](https://math.stackexchange.com/q/218046). *Mathematics Stack Exchange*.

## Bibliography

- [Bourbaki, Nicolas](https://en.wikipedia.org/wiki/Nicolas_Bourbaki) (1987) \[1981\]. *Topological Vector Spaces: Chapters 1–5*. [Éléments de mathématique](https://en.wikipedia.org/wiki/%C3%89l%C3%A9ments_de_math%C3%A9matique). Translated by Eggleston, H.G.; Madan, S. Berlin New York: Springer-Verlag. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [3-540-13627-4](https://en.wikipedia.org/wiki/Special:BookSources/3-540-13627-4). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [17499190](https://search.worldcat.org/oclc/17499190).
- Khaleelulla, S. M. (1982). *Counterexamples in Topological Vector Spaces*. [Lecture Notes in Mathematics](https://en.wikipedia.org/wiki/Lecture_Notes_in_Mathematics). Vol. 936. Berlin, Heidelberg, New York: [Springer-Verlag](https://en.wikipedia.org/wiki/Springer-Verlag). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-11565-6](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-11565-6). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [8588370](https://search.worldcat.org/oclc/8588370).
- Kubrusly, Carlos S. (2011). *The Elements of Operator Theory* (Second ed.). Boston: [Birkhäuser](https://en.wikipedia.org/wiki/Birkh%C3%A4user). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8176-4998-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8176-4998-2). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [710154895](https://search.worldcat.org/oclc/710154895).
- Narici, Lawrence; Beckenstein, Edward (2011). *Topological Vector Spaces*. Pure and applied mathematics (Second ed.). Boca Raton, FL: CRC Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1584888666](https://en.wikipedia.org/wiki/Special:BookSources/978-1584888666). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [144216834](https://search.worldcat.org/oclc/144216834).
- [Schaefer, Helmut H.](https://en.wikipedia.org/wiki/Helmut_H._Schaefer); Wolff, Manfred P. (1999). *Topological Vector Spaces*. [GTM](https://en.wikipedia.org/wiki/Graduate_Texts_in_Mathematics). Vol. 8 (Second ed.). New York, NY: Springer New York Imprint Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4612-7155-0](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4612-7155-0). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [840278135](https://search.worldcat.org/oclc/840278135).
- [Trèves, François](https://en.wikipedia.org/wiki/Fran%C3%A7ois_Tr%C3%A8ves) (2006) \[1967\]. *Topological Vector Spaces, Distributions and Kernels*. Mineola, N.Y.: Dover Publications. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-486-45352-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-486-45352-1). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [853623322](https://search.worldcat.org/oclc/853623322).
- [Wilansky, Albert](https://en.wikipedia.org/wiki/Albert_Wilansky) (2013). *Modern Methods in Topological Vector Spaces*. Mineola, New York: Dover Publications, Inc. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-486-49353-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-486-49353-4). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [849801114](https://search.worldcat.org/oclc/849801114).
