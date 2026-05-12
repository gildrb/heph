[[ai-math.base]]

> Source: [Linear algebra](https://en.wikipedia.org/wiki/Linear_algebra)
> License: Wikipedia content is available under CC BY-SA 4.0.

**Linear algebra** is the branch of [mathematics](https://en.wikipedia.org/wiki/Mathematics) concerning [linear equations](https://en.wikipedia.org/wiki/Linear_equation) such as

$a_{1}x_{1}+\cdots +a_{n}x_{n}=b,$

[linear maps](https://en.wikipedia.org/wiki/Linear_map) such as

$(x_{1},\ldots ,x_{n})\mapsto a_{1}x_{1}+\cdots +a_{n}x_{n},$

and their representations in [[Vector Space|vector spaces]] and through [matrices](https://en.wikipedia.org/wiki/Matrix_(mathematics) "Matrix (mathematics)").

![[media/aa70ee8aa27249630bbc005163460e21ff2ece76.png]]
In three-dimensional [Euclidean space](https://en.wikipedia.org/wiki/Euclidean_space), these three planes represent solutions to linear equations, and their intersection represents the set of common solutions: in this case, a unique point. The blue line is the common solution to two of these equations.

Linear algebra is central to almost all areas of mathematics. For instance, linear algebra is fundamental in modern presentations of [geometry](https://en.wikipedia.org/wiki/Geometry), including for defining basic objects such as [lines](https://en.wikipedia.org/wiki/Line_(geometry) "Line (geometry)"), [planes](https://en.wikipedia.org/wiki/Plane_(geometry)) and [rotations](https://en.wikipedia.org/wiki/Rotation_(mathematics) "Rotation (mathematics)"). Also, [functional analysis](https://en.wikipedia.org/wiki/Functional_analysis), a branch of [mathematical analysis](https://en.wikipedia.org/wiki/Mathematical_analysis), may be viewed as the application of linear algebra to [function spaces](https://en.wikipedia.org/wiki/Space_of_functions).

Linear algebra is also used in most sciences and fields of [engineering](https://en.wikipedia.org/wiki/Engineering) because it allows [modeling](https://en.wikipedia.org/wiki/Mathematical_model) many natural phenomena, and computing efficiently with such models. For [nonlinear systems](https://en.wikipedia.org/wiki/Nonlinear_system), which cannot be modeled with linear algebra, it is often used for dealing with [first-order approximations](https://en.wikipedia.org/wiki/First-order_approximation), using the fact that the [differential](https://en.wikipedia.org/wiki/Differential_(mathematics) "Differential (mathematics)") of a [multivariate function](https://en.wikipedia.org/wiki/Multivariate_function) at a point is the linear map that best approximates the function near that point.

## History

The procedure (using counting rods) for solving simultaneous linear equations now called [Gaussian elimination](https://en.wikipedia.org/wiki/Gaussian_elimination) appears in the ancient Chinese mathematical text [Chapter Eight: *Rectangular Arrays*](https://en.wikipedia.org/wiki/Rod_calculus#System_of_linear_equations) of *[The Nine Chapters on the Mathematical Art](https://en.wikipedia.org/wiki/The_Nine_Chapters_on_the_Mathematical_Art)*. Its use is illustrated in eighteen problems, with two to five equations.

[Systems of linear equations](https://en.wikipedia.org/wiki/Systems_of_linear_equations) arose in Europe with the introduction in 1637 by [René Descartes](https://en.wikipedia.org/wiki/Ren%C3%A9_Descartes) of [coordinates](https://en.wikipedia.org/wiki/Coordinates) in [geometry](https://en.wikipedia.org/wiki/Geometry). In fact, in this new geometry, now called [Cartesian geometry](https://en.wikipedia.org/wiki/Cartesian_geometry), lines and planes are represented by linear equations, and computing their intersections amounts to solving systems of linear equations.

The first systematic methods for solving linear systems used [[Determinant|determinants]] and were first considered by [Leibniz](https://en.wikipedia.org/wiki/Gottfried_Wilhelm_Leibniz) in 1693. In 1750, [Gabriel Cramer](https://en.wikipedia.org/wiki/Gabriel_Cramer) used them for giving explicit solutions of linear systems, now called [Cramer's rule](https://en.wikipedia.org/wiki/Cramer%27s_rule). Later, [Gauss](https://en.wikipedia.org/wiki/Gauss) further described the method of elimination, which was initially listed as an advancement in [geodesy](https://en.wikipedia.org/wiki/Geodesy).

In 1844 [Hermann Grassmann](https://en.wikipedia.org/wiki/Hermann_Grassmann) published his "Theory of Extension" which included foundational new topics of what is today called linear algebra. In 1848, [James Joseph Sylvester](https://en.wikipedia.org/wiki/James_Joseph_Sylvester) introduced the term *matrix*, which is Latin for *womb*.

Linear algebra grew with ideas noted in the [complex plane](https://en.wikipedia.org/wiki/Complex_plane). For instance, two numbers w and z in $\mathbb {C}$ have a difference *w* – *z*, and the line segments *wz* and 0(*w* − *z*) are of the same length and direction. The segments are [equipollent](https://en.wikipedia.org/wiki/Equipollence_(geometry) "Equipollence (geometry)"). The four-dimensional system $\mathbb {H}$ of [quaternions](https://en.wikipedia.org/wiki/Quaternion) was discovered by [W.R. Hamilton](https://en.wikipedia.org/wiki/William_Rowan_Hamilton) in 1843. The term *vector* was introduced as **v** = *x***i** + *y***j** + *z***k** representing a point in space. The quaternion difference *p* – *q* also produces a segment equipollent to *pq*. Other [hypercomplex number](https://en.wikipedia.org/wiki/Hypercomplex_number) systems also used the idea of a linear space with a [basis](https://en.wikipedia.org/wiki/Basis_(linear_algebra) "Basis (linear algebra)").

[Arthur Cayley](https://en.wikipedia.org/wiki/Arthur_Cayley) introduced [[Matrix Multiplication]] and the [[Inverse Matrix]] in 1856, making possible the [general linear group](https://en.wikipedia.org/wiki/General_linear_group). The mechanism of [group representation](https://en.wikipedia.org/wiki/Group_representation) became available for describing complex and hypercomplex numbers. Crucially, Cayley used a single letter to denote a matrix, thus treating a matrix as an aggregate object. He also realized the connection between matrices and determinants and wrote "There would be many things to say about this theory of matrices which should, it seems to me, precede the theory of determinants".

[Benjamin Peirce](https://en.wikipedia.org/wiki/Benjamin_Peirce) published his *Linear Associative Algebra* (1872), and his son [Charles Sanders Peirce](https://en.wikipedia.org/wiki/Charles_Sanders_Peirce) extended the work later.

The [telegraph](https://en.wikipedia.org/wiki/Telegraph) required an explanatory system, and the 1873 publication by [James Clerk Maxwell](https://en.wikipedia.org/wiki/James_Clerk_Maxwell) of *[A Treatise on Electricity and Magnetism](https://en.wikipedia.org/wiki/A_Treatise_on_Electricity_and_Magnetism)* instituted a [field theory](https://en.wikipedia.org/wiki/Field_theory_(physics)) of forces and required [differential geometry](https://en.wikipedia.org/wiki/Differential_geometry) for expression. Linear algebra is flat differential geometry and serves in tangent spaces to [[Manifold|manifolds]]. Electromagnetic symmetries of spacetime are expressed by the [Lorentz transformations](https://en.wikipedia.org/wiki/Lorentz_transformation), and much of the history of linear algebra is the [history of Lorentz transformations](https://en.wikipedia.org/wiki/History_of_Lorentz_transformations).

The first modern and more precise definition of a vector space was introduced by [Peano](https://en.wikipedia.org/wiki/Peano) in 1888; by 1900, a theory of linear transformations of finite-dimensional vector spaces had emerged. Linear algebra took its modern form in the first half of the twentieth century when many ideas and methods of previous centuries were generalized as [abstract algebra](https://en.wikipedia.org/wiki/Abstract_algebra). The development of computers led to increased research in efficient [algorithms](https://en.wikipedia.org/wiki/Algorithm) for Gaussian elimination and matrix decompositions, and linear algebra became an essential tool for modeling and simulations.

## Vector spaces

Until the 19th century, linear algebra was introduced through [systems of linear equations](https://en.wikipedia.org/wiki/Systems_of_linear_equations) and [matrices](https://en.wikipedia.org/wiki/Matrix_(mathematics) "Matrix (mathematics)"). In modern mathematics, the presentation through *vector spaces* is generally preferred, since it is more [synthetic](https://en.wikipedia.org/wiki/Synthetic_geometry), more general (not limited to the finite-dimensional case), and conceptually simpler, although more abstract.

A vector space over a [field](https://en.wikipedia.org/wiki/Field_(mathematics) "Field (mathematics)") *F* (often the field of the [real numbers](https://en.wikipedia.org/wiki/Real_number) or of the [complex numbers](https://en.wikipedia.org/wiki/Complex_number)) is a [set](https://en.wikipedia.org/wiki/Set_(mathematics) "Set (mathematics)") *V* equipped with two [binary operations](https://en.wikipedia.org/wiki/Binary_operation). [Elements](https://en.wikipedia.org/wiki/Element_(mathematics)) of *V* are called *vectors*, and elements of *F* are called *scalars*. The first operation, *[vector addition](https://en.wikipedia.org/wiki/Vector_addition)*, takes any two vectors **v** and **w** and outputs a third vector **v** + **w**. The second operation, *[scalar multiplication](https://en.wikipedia.org/wiki/Scalar_multiplication)*, takes any scalar *a* and any vector **v** and outputs a new vector *a***v**. The axioms that addition and scalar multiplication must satisfy are the following. (In the list below, **u**, **v** and **w** are arbitrary elements of *V*, and *a* and *b* are arbitrary scalars in the field *F*.)

|  |  |
|----|----|
| **Axiom** | **Signification** |
| [Associativity](https://en.wikipedia.org/wiki/Associativity) of addition | **u** + (**v** + **w**) = (**u** + **v**) + **w** |
| [Commutativity](https://en.wikipedia.org/wiki/Commutativity) of addition | **u** + **v** = **v** + **u** |
| [Identity element](https://en.wikipedia.org/wiki/Identity_element) of addition | There exists an element **0** in *V*, called the *[zero vector](https://en.wikipedia.org/wiki/Zero_vector)* (or simply *zero*), such that **v** + **0** = **v** for all **v** in *V*. |
| [Inverse elements](https://en.wikipedia.org/wiki/Inverse_element) of addition | For every **v** in *V*, there exists an element −**v** in *V*, called the *[additive inverse](https://en.wikipedia.org/wiki/Additive_inverse)* of **v**, such that **v** + (−**v**) = **0** |
| [Distributivity](https://en.wikipedia.org/wiki/Distributivity) of scalar multiplication with respect to vector addition | *a*(**u** + **v**) = *a***u** + *a***v** |
| Distributivity of scalar multiplication with respect to field addition | (*a* + *b*)**v** = *a***v** + *b***v** |
| Compatibility of scalar multiplication with field multiplication | *a*(*b***v**) = (*ab*)**v** |
| Identity element of scalar multiplication | 1**v** = **v**, where 1 denotes the [multiplicative identity](https://en.wikipedia.org/wiki/Multiplicative_identity) of F. |

The first four axioms mean that *V* is an [abelian group](https://en.wikipedia.org/wiki/Abelian_group) under addition.

The elements of a specific vector space may have various natures; for example, they could be [tuples](https://en.wikipedia.org/wiki/Tuple), [sequences](https://en.wikipedia.org/wiki/Sequence), [functions](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)"), [polynomials](https://en.wikipedia.org/wiki/Polynomial_ring), or [matrices](https://en.wikipedia.org/wiki/Matrix_(mathematics) "Matrix (mathematics)"). Linear algebra is concerned with the properties of such objects that are common to all vector spaces.

### Linear maps

**Linear maps** are [mappings](https://en.wikipedia.org/wiki/Map_(mathematics) "Map (mathematics)") between vector spaces that preserve the vector-space structure. Given two vector spaces *V* and *W* over a field F, a linear map (also called, in some contexts, linear transformation or linear mapping) is a [map](https://en.wikipedia.org/wiki/Map_(mathematics) "Map (mathematics)")

$T:V\to W$

that is compatible with addition and scalar multiplication, that is

$T(\mathbf {u} +\mathbf {v} )=T(\mathbf {u} )+T(\mathbf {v} ),\quad T(a\mathbf {v} )=aT(\mathbf {v} )$

for any vectors **u**,**v** in *V* and scalar *a* in F.

An equivalent condition is that

$T(a\mathbf {u} +b\mathbf {v} )=aT(\mathbf {u} )+bT(\mathbf {v} )$

for any vectors **u**, **v** in *V* and scalars *a*, *b* in F.

When *V* = *W* are the same vector space, a linear map *T* : *V* → *V* is also known as a *linear operator* on V.

A [bijective](https://en.wikipedia.org/wiki/Bijective) linear map between two vector spaces (that is, every vector from the second space is associated with exactly one in the first) is an [isomorphism](https://en.wikipedia.org/wiki/Isomorphism). Because an isomorphism preserves linear structure, two isomorphic vector spaces are "essentially the same" from the linear algebra point of view, in the sense that they cannot be distinguished by using vector space properties. An essential question in linear algebra is testing whether a linear map is an isomorphism or not, and, if it is not an isomorphism, finding its [range](https://en.wikipedia.org/wiki/Range_of_a_function) (or image) and the set of elements that are mapped to the zero vector, called the [kernel](https://en.wikipedia.org/wiki/Kernel_(linear_operator)) of the map. All these questions can be solved by using [Gaussian elimination](https://en.wikipedia.org/wiki/Gaussian_elimination) or some variant of this [algorithm](https://en.wikipedia.org/wiki/Algorithm).

### Subspaces, span, and basis

The study of those subsets of vector spaces that are in themselves vector spaces under the induced operations is fundamental, similarly as for many mathematical structures. These subsets are called [linear subspaces](https://en.wikipedia.org/wiki/Linear_subspace). More precisely, a linear subspace of a vector space V over a field F is a [subset](https://en.wikipedia.org/wiki/Subset) W of V such that **u** + **v** and *a***u** are in W, for every **u**, **v** in W, and every a in F. (These conditions suffice for implying that W is a vector space.)

For example, given a linear map *T* : *V* → *W*, the [image](https://en.wikipedia.org/wiki/Image_(function)) *T*(*V*) of V, and the [inverse image](https://en.wikipedia.org/wiki/Inverse_image) *T*<sup>−1</sup>(**0**) of **0** (called [kernel](https://en.wikipedia.org/wiki/Kernel_(linear_algebra) "Kernel (linear algebra)") or null space), are linear subspaces of W and V, respectively.

Another important way of forming a subspace is to consider [linear combinations](https://en.wikipedia.org/wiki/Linear_combination) of a set S of vectors: the set of all sums

$a_{1}\mathbf {v} _{1}+a_{2}\mathbf {v} _{2}+\cdots +a_{k}\mathbf {v} _{k},$

where **v**<sub>1</sub>, **v**<sub>2</sub>, ..., **v**<sub>*k*</sub> are in S, and *a*<sub>1</sub>, *a*<sub>2</sub>, ..., *a*<sub>*k*</sub> are in F form a linear subspace called the [span](https://en.wikipedia.org/wiki/Linear_span) of S. The span of S is also the intersection of all linear subspaces containing S. In other words, it is the smallest (for the inclusion relation) linear subspace containing S.

A set of vectors is [linearly independent](https://en.wikipedia.org/wiki/Linearly_independent) if none is in the span of the others. Equivalently, a set S of vectors is linearly independent if the only way to express the zero vector as a linear combination of elements of S is to take zero for every coefficient a<sub>i</sub>.

A set of vectors that spans a vector space is called a [spanning set](https://en.wikipedia.org/wiki/Spanning_set) or [generating set](https://en.wikipedia.org/wiki/Generating_set). If a spanning set S is *linearly dependent* (that is not linearly independent), then some element **w** of S is in the span of the other elements of S, and the span would remain the same if one were to remove **w** from S. One may continue to remove elements of S until getting a *linearly independent spanning set*. Such a linearly independent set that spans a vector space V is called a [basis](https://en.wikipedia.org/wiki/Basis_(linear_algebra) "Basis (linear algebra)") of *V*. The importance of bases lies in the fact that they are simultaneously minimal-generating sets and maximal independent sets. More precisely, if S is a linearly independent set, and T is a spanning set such that *S* ⊆ *T*, then there is a basis B such that *S* ⊆ *B* ⊆ *T*.

Any two bases of a vector space *V* have the same [cardinality](https://en.wikipedia.org/wiki/Cardinality), which is called the [dimension](https://en.wikipedia.org/wiki/Dimension_(vector_space) "Dimension (vector space)") of *V*; this is the [dimension theorem for vector spaces](https://en.wikipedia.org/wiki/Dimension_theorem_for_vector_spaces). Moreover, two vector spaces over the same field F are [isomorphic](https://en.wikipedia.org/wiki/Isomorphic) if and only if they have the same dimension.

If any basis of *V* (and therefore every basis) has a finite number of elements, *V* is a *finite-dimensional vector space*. If *U* is a subspace of *V*, then dim *U* ≤ dim *V*. In the case where *V* is finite-dimensional, the equality of the dimensions implies *U* = *V*.

If *U*<sub>1</sub> and *U*<sub>2</sub> are subspaces of *V*, then

$\dim(U_{1}+U_{2})=\dim U_{1}+\dim U_{2}-\dim(U_{1}\cap U_{2}),$

where *U*<sub>1</sub> + *U*<sub>2</sub> denotes the span of *U*<sub>1</sub> ∪ *U*<sub>2</sub>.

## Matrices

Matrices allow explicit manipulation of finite-dimensional vector spaces and [linear maps](https://en.wikipedia.org/wiki/Linear_map). Their theory is thus an essential part of linear algebra.

Let V be a finite-dimensional vector space over a field *F*, and (**v**<sub>1</sub>, **v**<sub>2</sub>, ..., **v**<sub>*m*</sub>) be a basis of *V* (thus m is the dimension of *V*). By definition of a basis, the map

${\begin{aligned}(a_{1},\ldots ,a_{m})&\mapsto a_{1}\mathbf {v} _{1}+\cdots a_{m}\mathbf {v} _{m}\\F^{m}&\to V\end{aligned}}$

is a [bijection](https://en.wikipedia.org/wiki/Bijection) from *F<sup>m</sup>*, the set of the [sequences](https://en.wikipedia.org/wiki/Sequence_(mathematics)) of m elements of F, onto V. This is an [isomorphism](https://en.wikipedia.org/wiki/Isomorphism) of vector spaces, if *F<sup>m</sup>* is equipped with its standard structure of vector space, where vector addition and scalar multiplication are done component by component.

This isomorphism allows representing a vector by its [inverse image](https://en.wikipedia.org/wiki/Inverse_image) under this isomorphism, that is by the [coordinate vector](https://en.wikipedia.org/wiki/Coordinate_vector) (*a*<sub>1</sub>, ..., *a<sub>m</sub>*) or by the [column matrix](https://en.wikipedia.org/wiki/Column_matrix)

${\begin{bmatrix}a_{1}\\\vdots \\a_{m}\end{bmatrix}}.$

If W is another finite dimensional vector space (possibly the same), with a basis (**w**<sub>1</sub>, ..., **w**<sub>*n*</sub>), a linear map f from W to V is well defined by its values on the basis elements, that is (*f*(**w**<sub>1</sub>), ..., *f*(**w**<sub>*n*</sub>)). Thus, f is well represented by the list of the corresponding column matrices. That is, if

$f(w_{j})=a_{1,j}v_{1}+\cdots +a_{m,j}v_{m},$

for *j* = 1, ..., *n*, then f is represented by the matrix

${\begin{bmatrix}a_{1,1}&\cdots &a_{1,n}\\\vdots &\ddots &\vdots \\a_{m,1}&\cdots &a_{m,n}\end{bmatrix}},$

with m rows and n columns.

[[Matrix Multiplication]] is defined in such a way that the product of two matrices is the matrix of the [composition](https://en.wikipedia.org/wiki/Function_composition) of the corresponding linear maps, and the product of a matrix and a column matrix is the column matrix representing the result of applying the represented linear map to the represented vector. It follows that the theory of finite-dimensional vector spaces and the theory of matrices are two different languages for expressing the same concepts.

Two matrices that encode the same linear transformation in different bases are called [similar](https://en.wikipedia.org/wiki/Similar_(linear_algebra)). It can be proved that two matrices are similar if and only if one can transform one into the other by [elementary row and column operations](https://en.wikipedia.org/wiki/Elementary_matrix). For a matrix representing a linear map from W to V, the row operations correspond to change of bases in V and the column operations correspond to change of bases in W. Every matrix is similar to an [identity matrix](https://en.wikipedia.org/wiki/Identity_matrix) possibly bordered by zero rows and zero columns. In terms of vector spaces, this means that, for any linear map from W to V, there are bases such that a part of the basis of W is mapped bijectively on a part of the basis of V, and that the remaining basis elements of W, if any, are mapped to zero. [Gaussian elimination](https://en.wikipedia.org/wiki/Gaussian_elimination) is the basic algorithm for finding these elementary operations, and proving these results.

## Linear systems

A finite set of linear equations in a finite set of variables, for example, *x*<sub>1</sub>, *x*<sub>2</sub>, ..., *x<sub>n</sub>*, or *x*, *y*, ..., *z* is called a **system of linear equations** or a **linear system**.

Systems of linear equations form a fundamental part of linear algebra. Historically, linear algebra and matrix theory have been developed for solving such systems. In the modern presentation of linear algebra through vector spaces and matrices, many problems may be interpreted in terms of linear systems.

For example, let

|  |  |  |
|----|----|----|
| ${\begin{alignedat}{7}2x&&\;+\;&&y&&\;-\;&&z&&\;=\;&&8\\-3x&&\;-\;&&y&&\;+\;&&2z&&\;=\;&&-11\\-2x&&\;+\;&&y&&\;+\;&&2z&&\;=\;&&-3\end{alignedat}}$ |  | [S](#math_S) |

be a linear system.

To such a system, one may associate its matrix

$M=\left[{\begin{array}{rrr}2&1&-1\\-3&-1&2\\-2&1&2\end{array}}\right].$

and its right member vector

$\mathbf {v} ={\begin{bmatrix}8\\-11\\-3\end{bmatrix}}.$

Let T be the linear transformation associated with the matrix M. A solution of the system (**[S](#math_S)**) is a vector

$\mathbf {X} ={\begin{bmatrix}x\\y\\z\end{bmatrix}}$

such that

$T(\mathbf {X} )=\mathbf {v} ,$

that is an element of the [preimage](https://en.wikipedia.org/wiki/Preimage) of v by T.

Let (**[S′](#math_S′)**) be the associated [homogeneous system](https://en.wikipedia.org/wiki/Homogeneous_system_of_linear_equations), where the right-hand sides of the equations are put to zero:

|  |  |  |
|----|----|----|
| ${\begin{alignedat}{7}2x&&\;+\;&&y&&\;-\;&&z&&\;=\;&&0\\-3x&&\;-\;&&y&&\;+\;&&2z&&\;=\;&&0\\-2x&&\;+\;&&y&&\;+\;&&2z&&\;=\;&&0\end{alignedat}}$ |  | [S′](#math_S′) |

The solutions of (**[S′](#math_S′)**) are exactly the elements of the [kernel](https://en.wikipedia.org/wiki/Kernel_(linear_algebra) "Kernel (linear algebra)") of T or, equivalently, M.

The [Gaussian-elimination](https://en.wikipedia.org/wiki/Gaussian_elimination) consists of performing [elementary row operations](https://en.wikipedia.org/wiki/Elementary_row_operation) on the [augmented matrix](https://en.wikipedia.org/wiki/Augmented_matrix)

$\left[\!{\begin{array}{c|c}M&\mathbf {v} \end{array}}\!\right]=\left[{\begin{array}{rrr|r}2&1&-1&8\\-3&-1&2&-11\\-2&1&2&-3\end{array}}\right]$

for putting it in [reduced row echelon form](https://en.wikipedia.org/wiki/Reduced_row_echelon_form). These row operations do not change the set of solutions of the system of equations. In the example, the reduced echelon form is

$\left[\!{\begin{array}{c|c}M&\mathbf {v} \end{array}}\!\right]=\left[{\begin{array}{rrr|r}1&0&0&2\\0&1&0&3\\0&0&1&-1\end{array}}\right],$

showing that the system (**[S](#math_S)**) has the unique solution

${\begin{aligned}x&=2\\y&=3\\z&=-1.\end{aligned}}$

More generally, a system of $m$ linear equations in $n$ variables can be written as $A\mathbf {x} =\mathbf {b}$ where

$A=(a_{ij})_{m\times n}$

$\mathbf {x} ={\begin{bmatrix}x_{1}\\\vdots \\x_{n}\end{bmatrix}}$

$\mathbf {b} ={\begin{bmatrix}b_{1}\\\vdots \\b_{m}\end{bmatrix}}$

If $m=n$ and the matrix $A$ is invertible, then the system has the unique solution $\mathbf {x} =A^{-1}\mathbf {b}$.

It follows from this matrix interpretation of linear systems that the same methods can be applied for solving linear systems and for many operations on matrices and linear transformations, which include the computation of the [ranks](https://en.wikipedia.org/wiki/Rank_of_a_matrix), [kernels](https://en.wikipedia.org/wiki/Kernel_(linear_algebra) "Kernel (linear algebra)"), [matrix inverses](https://en.wikipedia.org/wiki/Matrix_inverse).

## Endomorphisms and square matrices

A linear [endomorphism](https://en.wikipedia.org/wiki/Endomorphism) is a linear map that maps a vector space V to itself. If V has a basis of n elements, such an endomorphism is represented by a square matrix of size n.

Concerning general linear maps, linear endomorphisms, and square matrices have some specific properties that make their study an important part of linear algebra, which is used in many parts of mathematics, including [geometric transformations](https://en.wikipedia.org/wiki/Geometric_transformation), [coordinate changes](https://en.wikipedia.org/wiki/Coordinate_change), [quadratic forms](https://en.wikipedia.org/wiki/Quadratic_form), and many other parts of mathematics.

### Determinant

The *determinant* of a square matrix A is defined to be

$\sum _{\sigma \in S_{n}}(-1)^{\sigma }a_{1\sigma (1)}\cdots a_{n\sigma (n)},$

where *S<sub>n</sub>* is the [group of all permutations](https://en.wikipedia.org/wiki/Symmetric_group) of n elements, σ is a permutation, and (−1)<sup>*σ*</sup> the [parity](https://en.wikipedia.org/wiki/Parity_of_a_permutation) of the permutation. A matrix is [invertible](https://en.wikipedia.org/wiki/Invertible_matrix) if and only if the determinant is invertible (i.e., nonzero if the scalars belong to a field).

[Cramer's rule](https://en.wikipedia.org/wiki/Cramer%27s_rule) is a [closed-form expression](https://en.wikipedia.org/wiki/Closed-form_expression), in terms of determinants, of the solution of a [system of n linear equations in n unknowns](https://en.wikipedia.org/wiki/System_of_linear_equations). Cramer's rule is useful for reasoning about the solution, but, except for *n* = 2 or 3, it is rarely used for computing a solution, since [Gaussian elimination](https://en.wikipedia.org/wiki/Gaussian_elimination) is a faster algorithm.

The *determinant of an endomorphism* is the determinant of the matrix representing the endomorphism in terms of some ordered basis. This definition makes sense since this determinant is independent of the choice of the basis.

### Eigenvalues and eigenvectors

If f is a linear endomorphism of a vector space V over a field F, an *eigenvector* of f is a nonzero vector v of V such that *f*(*v*) = *av* for some scalar a in F. This scalar a is an *eigenvalue* of f.

If the dimension of V is finite, and a basis has been chosen, f and v may be represented, respectively, by a square matrix M and a column matrix z; the equation defining eigenvectors and eigenvalues becomes

$Mz=az.$

Using the [identity matrix](https://en.wikipedia.org/wiki/Identity_matrix) I, whose entries are all zero, except those of the main diagonal, which are equal to one, this may be rewritten

$(M-aI)z=0.$

As z is supposed to be nonzero, this means that *M* – *aI* is a [singular matrix](https://en.wikipedia.org/wiki/Singular_matrix), and thus that its determinant det (*M* − *aI*) equals zero. The eigenvalues are thus the [roots](https://en.wikipedia.org/wiki/Root_of_a_function) of the [polynomial](https://en.wikipedia.org/wiki/Polynomial)

$\det(xI-M).$

If V is of dimension n, this is a [monic polynomial](https://en.wikipedia.org/wiki/Monic_polynomial) of degree n, called the [characteristic polynomial](https://en.wikipedia.org/wiki/Characteristic_polynomial) of the matrix (or of the endomorphism), and there are, at most, n eigenvalues.

If a basis exists that consists only of eigenvectors, the matrix of f on this basis has a very simple structure: it is a [diagonal matrix](https://en.wikipedia.org/wiki/Diagonal_matrix) such that the entries on the [main diagonal](https://en.wikipedia.org/wiki/Main_diagonal) are eigenvalues, and the other entries are zero. In this case, the endomorphism and the matrix are said to be [diagonalizable](https://en.wikipedia.org/wiki/Diagonalizable_matrix). More generally, an endomorphism and a matrix are also said diagonalizable, if they become diagonalizable after [extending](https://en.wikipedia.org/wiki/Field_extension) the field of scalars. In this extended sense, if the characteristic polynomial is [square-free](https://en.wikipedia.org/wiki/Square-free_polynomial), then the matrix is diagonalizable.

A [symmetric matrix](https://en.wikipedia.org/wiki/Symmetric_matrix) is always diagonalizable. There are non-diagonalizable matrices, the simplest being

${\begin{bmatrix}0&1\\0&0\end{bmatrix}}$

(it cannot be diagonalizable since its square is the [zero matrix](https://en.wikipedia.org/wiki/Zero_matrix), and the square of a nonzero diagonal matrix is never zero).

When an endomorphism is not diagonalizable, there are bases on which it has a simple form, although not as simple as the diagonal form. The [Frobenius normal form](https://en.wikipedia.org/wiki/Frobenius_normal_form) does not need to extend the field of scalars and makes the characteristic polynomial immediately readable on the matrix. The [Jordan normal form](https://en.wikipedia.org/wiki/Jordan_normal_form) requires to extension of the field of scalar for containing all eigenvalues and differs from the diagonal form only by some entries that are just above the main diagonal and are equal to 1.

## Duality

A [linear form](https://en.wikipedia.org/wiki/Linear_form) is a linear map from a vector space V over a field F to the field of scalars F, viewed as a vector space over itself. Equipped by [pointwise](https://en.wikipedia.org/wiki/Pointwise) addition and multiplication by a scalar, the linear forms form a vector space, called the **dual space** of V, and usually denoted V\* or V′.

If **v**<sub>1</sub>, ..., **v**<sub>*n*</sub> is a basis of V (this implies that V is finite-dimensional), then one can define, for *i* = 1, ..., *n*, a linear map *v<sub>i</sub>*\* such that *v<sub>i</sub>*\*(**v**<sub>*i*</sub>) = 1 and *v<sub>i</sub>*\*(**v**<sub>*j*</sub>) = 0 if *j* ≠ *i*. These linear maps form a basis of *V*\*, called the [dual basis](https://en.wikipedia.org/wiki/Dual_basis) of **v**<sub>1</sub>, ..., **v**<sub>*n*</sub>. (If V is not finite-dimensional, the *v<sub>i</sub>*\* may be defined similarly; they are linearly independent, but do not form a basis.)

For **v** in V, the map

$f\to f(\mathbf {v} )$

is a linear form on V\*. This defines the [canonical linear map](https://en.wikipedia.org/wiki/Canonical_map) from V into (*V*\*)\*, the dual of V\*, called the **[double dual](https://en.wikipedia.org/wiki/Double_dual)** or **[bidual](https://en.wikipedia.org/wiki/Bidual)** of V. This canonical map is an [isomorphism](https://en.wikipedia.org/wiki/Isomorphism) if V is finite-dimensional, and this allows identifying V with its bidual. (In the infinite-dimensional case, the canonical map is injective, but not surjective.)

There is thus a complete symmetry between a finite-dimensional vector space and its dual. This motivates the frequent use, in this context, of the [bra–ket notation](https://en.wikipedia.org/wiki/Bra%E2%80%93ket_notation)

$\langle f,\mathbf {x} \rangle$

for denoting *f*(**x**).

### Dual map

Let

$f:V\to W$

be a linear map. For every linear form h on W, the [composite function](https://en.wikipedia.org/wiki/Composite_function) *h* ∘ *f* is a linear form on V. This defines a linear map

$f^{*}:W^{*}\to V^{*}$

between the dual spaces, which is called the **dual** or the **transpose** of f.

If V and W are finite-dimensional, and M is the matrix of f in terms of some ordered bases, then the matrix of f\* over the dual bases is the [transpose](https://en.wikipedia.org/wiki/Transpose) *M*<sup>T</sup> of M, obtained by exchanging rows and columns.

If elements of vector spaces and their duals are represented by column vectors, this duality may be expressed in [bra–ket notation](https://en.wikipedia.org/wiki/Bra%E2%80%93ket_notation) by

$\langle h^{\mathsf {T}},M\mathbf {v} \rangle =\langle h^{\mathsf {T}}M,\mathbf {v} \rangle .$

To highlight this symmetry, the two members of this equality are sometimes written

$\langle h^{\mathsf {T}}\mid M\mid \mathbf {v} \rangle .$

### Inner-product spaces

Besides these basic concepts, linear algebra also studies vector spaces with additional structure, such as an [inner product](https://en.wikipedia.org/wiki/Inner_product). The inner product is an example of a [bilinear form](https://en.wikipedia.org/wiki/Bilinear_form), and it gives the vector space a geometric structure by allowing for the definition of length and angles. Formally, an *inner product* is a map.

$\langle \cdot ,\cdot \rangle :V\times V\to F$

that satisfies the following three [axioms](https://en.wikipedia.org/wiki/Axiom) for all vectors **u**, **v**, **w** in *V* and all scalars *a* in *F*:

- [Conjugate](https://en.wikipedia.org/wiki/Complex_conjugate) symmetry:
  $\langle \mathbf {u} ,\mathbf {v} \rangle ={\overline {\langle \mathbf {v} ,\mathbf {u} \rangle }}.$

In $\mathbb {R}$, it is symmetric.

- [Linearity](https://en.wikipedia.org/wiki/Linear) in the first argument:
  ${\begin{aligned}\langle a\mathbf {u} ,\mathbf {v} \rangle &=a\langle \mathbf {u} ,\mathbf {v} \rangle .\\\langle \mathbf {u} +\mathbf {v} ,\mathbf {w} \rangle &=\langle \mathbf {u} ,\mathbf {w} \rangle +\langle \mathbf {v} ,\mathbf {w} \rangle .\end{aligned}}$
- [Positive-definiteness](https://en.wikipedia.org/wiki/Definite_bilinear_form):
  $\langle \mathbf {v} ,\mathbf {v} \rangle \geq 0$

with equality only for **v** = 0.

We can define the length of a vector **v** in *V* by

$\|\mathbf {v} \|^{2}=\langle \mathbf {v} ,\mathbf {v} \rangle ,$

and we can prove the [Cauchy–Schwarz inequality](https://en.wikipedia.org/wiki/Cauchy%E2%80%93Schwarz_inequality):

$|\langle \mathbf {u} ,\mathbf {v} \rangle |\leq \|\mathbf {u} \|\cdot \|\mathbf {v} \|.$

In particular, the quantity

${\frac {|\langle \mathbf {u} ,\mathbf {v} \rangle |}{\|\mathbf {u} \|\cdot \|\mathbf {v} \|}}\leq 1,$

and so we can call this quantity the cosine of the angle between the two vectors.

Two vectors are orthogonal if ⟨**u**, **v**⟩ = 0. An orthonormal basis is a basis where all basis vectors have length 1 and are orthogonal to each other. Given any finite-dimensional vector space, an orthonormal basis could be found by the [Gram–Schmidt](https://en.wikipedia.org/wiki/Gram%E2%80%93Schmidt) procedure. Orthonormal bases are particularly easy to deal with, since if **v** = *a*<sub>1</sub> **v**<sub>1</sub> + ⋯ + *a<sub>n</sub>* **v**<sub>*n*</sub>, then

$a_{i}=\langle \mathbf {v} ,\mathbf {v} _{i}\rangle .$

The inner product facilitates the construction of many useful concepts. For instance, given a transform *T*, we can define its [Hermitian conjugate](https://en.wikipedia.org/wiki/Hermitian_conjugate) *T\** as the linear transform satisfying

$\langle T\mathbf {u} ,\mathbf {v} \rangle =\langle \mathbf {u} ,T^{*}\mathbf {v} \rangle .$

If *T* satisfies *TT\** = *T\*T*, we call *T* [normal](https://en.wikipedia.org/wiki/Normal_matrix). It turns out that normal matrices are precisely the matrices that have an orthonormal system of eigenvectors that span *V*.

## Relationship with geometry

There is a strong relationship between linear algebra and [geometry](https://en.wikipedia.org/wiki/Geometry), which started with the introduction by [René Descartes](https://en.wikipedia.org/wiki/Ren%C3%A9_Descartes), in 1637, of [Cartesian coordinates](https://en.wikipedia.org/wiki/Cartesian_coordinates). In this new (at that time) geometry, now called [Cartesian geometry](https://en.wikipedia.org/wiki/Cartesian_geometry), points are represented by [Cartesian coordinates](https://en.wikipedia.org/wiki/Cartesian_coordinates), which are sequences of three real numbers (in the case of the usual [three-dimensional space](https://en.wikipedia.org/wiki/Three-dimensional_space)). The basic objects of geometry, which are [lines](https://en.wikipedia.org/wiki/Line_(geometry) "Line (geometry)") and [planes](https://en.wikipedia.org/wiki/Plane_(geometry)) are represented by linear equations. Thus, computing intersections of lines and planes amounts to solving systems of linear equations. This was one of the main motivations for developing linear algebra.

Most [geometric transformation](https://en.wikipedia.org/wiki/Geometric_transformation), such as [translations](https://en.wikipedia.org/wiki/Translation_(geometry) "Translation (geometry)"), [rotations](https://en.wikipedia.org/wiki/Rotation), [reflections](https://en.wikipedia.org/wiki/Reflection_(mathematics) "Reflection (mathematics)"), [rigid motions](https://en.wikipedia.org/wiki/Rigid_motion), [isometries](https://en.wikipedia.org/wiki/Isometry), and [projections](https://en.wikipedia.org/wiki/Projection_(mathematics) "Projection (mathematics)") transform lines into lines. It follows that they can be defined, specified, and studied in terms of linear maps. This is also the case of [homographies](https://en.wikipedia.org/wiki/Homography) and [Möbius transformations](https://en.wikipedia.org/wiki/M%C3%B6bius_transformation) when considered as transformations of a [projective space](https://en.wikipedia.org/wiki/Projective_space).

Until the end of the 19th century, geometric spaces were defined by [axioms](https://en.wikipedia.org/wiki/Axiom) relating points, lines, and planes ([synthetic geometry](https://en.wikipedia.org/wiki/Synthetic_geometry)). Around this date, it appeared that one may also define geometric spaces by constructions involving vector spaces (see, for example, [Projective space](https://en.wikipedia.org/wiki/Projective_space) and [Affine space](https://en.wikipedia.org/wiki/Affine_space)). It has been shown that the two approaches are essentially equivalent. In classical geometry, the involved vector spaces are vector spaces over the reals, but the constructions may be extended to vector spaces over any field, allowing considering geometry over arbitrary fields, including [finite fields](https://en.wikipedia.org/wiki/Finite_field).

Presently, most textbooks introduce geometric spaces from linear algebra, and geometry is often presented, at the elementary level, as a subfield of linear algebra.

## Usage and applications

Linear algebra is used in almost all areas of mathematics, thus making it relevant in almost all scientific domains that use mathematics. These applications may be divided into several wide categories.

### Functional analysis

[Functional analysis](https://en.wikipedia.org/wiki/Functional_analysis) studies [function spaces](https://en.wikipedia.org/wiki/Function_space). These are vector spaces with additional structure, such as [Hilbert spaces](https://en.wikipedia.org/wiki/Hilbert_space). Linear algebra is thus a fundamental part of functional analysis and its applications, which include, in particular, [quantum mechanics](https://en.wikipedia.org/wiki/Quantum_mechanics) ([wave functions](https://en.wikipedia.org/wiki/Wave_function)) and [Fourier analysis](https://en.wikipedia.org/wiki/Fourier_analysis) ([orthogonal basis](https://en.wikipedia.org/wiki/Orthogonal_basis)).

### Scientific computation

Nearly all [scientific computations](https://en.wikipedia.org/wiki/Scientific_computation) involve linear algebra. Consequently, linear algebra algorithms have been highly optimized. [BLAS](https://en.wikipedia.org/wiki/Basic_Linear_Algebra_Subprograms) and [LAPACK](https://en.wikipedia.org/wiki/LAPACK) are the best known implementations. For improving efficiency, some of them configure the algorithms automatically, at run time, to adapt them to the specificities of the computer ([cache](https://en.wikipedia.org/wiki/Cache_(computing) "Cache (computing)") size, number of available [cores](https://en.wikipedia.org/wiki/Multi-core_processor), ...).

Since the 1960s there have been processors with specialized instructions for optimizing the operations of linear algebra, optional array processors under the control of a conventional processor, supercomputers designed for array processing and conventional processors augmented with vector registers.

Some contemporary [processors](https://en.wikipedia.org/wiki/Processor_(computing) "Processor (computing)"), typically [graphics processing units](https://en.wikipedia.org/wiki/Graphics_processing_units) (GPU), are designed with a matrix structure, for optimizing the operations of linear algebra.

### Geometry of ambient space

The [modeling](https://en.wikipedia.org/wiki/Mathematical_model) of [ambient space](https://en.wikipedia.org/wiki/Ambient_space) is based on [geometry](https://en.wikipedia.org/wiki/Geometry). Sciences concerned with this space use geometry widely. This is the case with [mechanics](https://en.wikipedia.org/wiki/Mechanics) and [robotics](https://en.wikipedia.org/wiki/Robotics), for describing [rigid body dynamics](https://en.wikipedia.org/wiki/Rigid_body_dynamics); [geodesy](https://en.wikipedia.org/wiki/Geodesy) for describing [Earth shape](https://en.wikipedia.org/wiki/Earth_shape); [perspectivity](https://en.wikipedia.org/wiki/Perspectivity), [computer vision](https://en.wikipedia.org/wiki/Computer_vision), and [computer graphics](https://en.wikipedia.org/wiki/Computer_graphics), for describing the relationship between a scene and its plane representation; and many other scientific domains.

In all these applications, [synthetic geometry](https://en.wikipedia.org/wiki/Synthetic_geometry) is often used for general descriptions and a qualitative approach, but for the study of explicit situations, one must compute with [coordinates](https://en.wikipedia.org/wiki/Coordinates). This requires the heavy use of linear algebra.

### Study of complex systems

Most physical phenomena are modeled by [partial differential equations](https://en.wikipedia.org/wiki/Partial_differential_equation). To solve them, one usually decomposes the space in which the solutions are searched into small, mutually interacting [cells](https://en.wikipedia.org/wiki/Discretization). For [linear systems](https://en.wikipedia.org/wiki/Linear_system) this interaction involves [linear functions](https://en.wikipedia.org/wiki/Linear_function). For [nonlinear systems](https://en.wikipedia.org/wiki/Nonlinear_systems), this interaction is often approximated by linear functions.This is called a linear model or first-order approximation. Linear models are frequently used for complex nonlinear real-world systems because they make [parametrization](https://en.wikipedia.org/wiki/Parametrization_(geometry) "Parametrization (geometry)") more manageable. In both cases, very large matrices are generally involved. [Weather forecasting](https://en.wikipedia.org/wiki/Weather_forecasting) (or more specifically, [parametrization for atmospheric modeling](https://en.wikipedia.org/wiki/Parametrization_(atmospheric_modeling) "Parametrization (atmospheric modeling)")) is a typical example of a real-world application, where the whole Earth [atmosphere](https://en.wikipedia.org/wiki/Atmosphere) is divided into cells of, say, 100 km of width and 100 km of height.

### Fluid mechanics, fluid dynamics, and thermal energy systems



Linear algebra, a branch of mathematics dealing with [vector spaces](https://en.wikipedia.org/wiki/Vector_spaces) and [linear mappings](https://en.wikipedia.org/wiki/Linear_mapping) between these spaces, plays a critical role in various engineering disciplines, including [fluid mechanics](https://en.wikipedia.org/wiki/Fluid_mechanics), [fluid dynamics](https://en.wikipedia.org/wiki/Fluid_dynamics), and [thermal energy](https://en.wikipedia.org/wiki/Thermal_energy) systems. Its application in these fields is multifaceted and indispensable for solving complex problems.

In [fluid mechanics](https://en.wikipedia.org/wiki/Fluid_mechanics), linear algebra is integral to understanding and solving problems related to the behavior of fluids. It assists in the modeling and simulation of fluid flow, providing essential tools for the analysis of [fluid dynamics](https://en.wikipedia.org/wiki/Fluid_dynamics) problems. For instance, linear algebraic techniques are used to solve systems of [differential equations](https://en.wikipedia.org/wiki/Differential_equations) that describe fluid motion. These equations, often complex and [non-linear](https://en.wikipedia.org/wiki/Non-linear), can be linearized using linear algebra methods, allowing for simpler solutions and analyses.

In the field of fluid dynamics, linear algebra finds its application in [computational fluid dynamics](https://en.wikipedia.org/wiki/Computational_fluid_dynamics) (CFD), a branch that uses [numerical analysis](https://en.wikipedia.org/wiki/Numerical_analysis) and [data structures](https://en.wikipedia.org/wiki/Data_structure) to solve and analyze problems involving fluid flows. CFD relies heavily on linear algebra for the computation of fluid flow and [heat transfer](https://en.wikipedia.org/wiki/Heat_transfer) in various applications. For example, the [Navier–Stokes equations](https://en.wikipedia.org/wiki/Navier%E2%80%93Stokes_equations), fundamental in [fluid dynamics](https://en.wikipedia.org/wiki/Fluid_dynamics), are often solved using techniques derived from linear algebra. This includes the use of [matrices](https://en.wikipedia.org/wiki/Matrix_(mathematics) "Matrix (mathematics)") and [vectors](https://en.wikipedia.org/wiki/Vector_(mathematics_and_physics) "Vector (mathematics and physics)") to represent and manipulate fluid flow fields.

Furthermore, linear algebra plays a crucial role in [thermal energy](https://en.wikipedia.org/wiki/Thermal_energy) systems, particularly in [power systems](https://en.wikipedia.org/wiki/Power_systems) analysis. It is used to model and optimize the generation, [transmission](https://en.wikipedia.org/wiki/Electric_power_transmission), and [distribution](https://en.wikipedia.org/wiki/Electric_power_distribution) of electric power. Linear algebraic concepts such as matrix operations and [eigenvalue](https://en.wikipedia.org/wiki/Eigenvalue) problems are employed to enhance the efficiency, reliability, and economic performance of [power systems](https://en.wikipedia.org/wiki/Power_systems). The application of linear algebra in this context is vital for the design and operation of modern [power systems](https://en.wikipedia.org/wiki/Power_systems), including [renewable energy](https://en.wikipedia.org/wiki/Renewable_energy) sources and [smart grids](https://en.wikipedia.org/wiki/Smart_grid).

Overall, the application of linear algebra in [fluid mechanics](https://en.wikipedia.org/wiki/Fluid_mechanics), [fluid dynamics](https://en.wikipedia.org/wiki/Fluid_dynamics), and [thermal energy](https://en.wikipedia.org/wiki/Thermal_energy) systems is an example of the profound interconnection between [mathematics](https://en.wikipedia.org/wiki/Mathematics) and [engineering](https://en.wikipedia.org/wiki/Engineering). It provides engineers with the necessary tools to model, analyze, and solve complex problems in these domains, leading to advancements in technology and industry.

## Extensions and generalizations

This section presents several related topics that do not appear generally in elementary textbooks on linear algebra but are commonly considered, in advanced mathematics, as parts of linear algebra.

### Module theory

The existence of multiplicative inverses in fields is not involved in the axioms defining a vector space. One may thus replace the field of scalars by a [ring](https://en.wikipedia.org/wiki/Ring_(mathematics) "Ring (mathematics)") R, and this gives the structure called a **module** over R, or R-module.

The concepts of linear independence, span, basis, and linear maps (also called [module homomorphisms](https://en.wikipedia.org/wiki/Module_homomorphism)) are defined for modules exactly as for vector spaces, with the essential difference that, if R is not a field, there are modules that do not have any basis. The modules that have a basis are the [free modules](https://en.wikipedia.org/wiki/Free_module), and those that are spanned by a finite set are the [finitely generated modules](https://en.wikipedia.org/wiki/Finitely_generated_module). Module homomorphisms between finitely generated free modules may be represented by matrices. The theory of matrices over a ring is similar to that of matrices over a field, except that [[Determinant|determinants]] exist only if the ring is [commutative](https://en.wikipedia.org/wiki/Commutative_ring), and that a square matrix over a commutative ring is [invertible](https://en.wikipedia.org/wiki/Invertible_matrix) only if its determinant has a [multiplicative inverse](https://en.wikipedia.org/wiki/Multiplicative_inverse) in the ring.

Vector spaces are completely characterized by their dimension (up to an isomorphism). In general, there is not such a complete classification for modules, even if one restricts oneself to finitely generated modules. However, every module is a [cokernel](https://en.wikipedia.org/wiki/Cokernel) of a homomorphism of free modules.

Modules over the integers can be identified with [abelian groups](https://en.wikipedia.org/wiki/Abelian_group), since the multiplication by an integer may be identified as a repeated addition. Most of the theory of abelian groups may be extended to modules over a [principal ideal domain](https://en.wikipedia.org/wiki/Principal_ideal_domain). In particular, over a principal ideal domain, every submodule of a free module is free, and the [fundamental theorem of finitely generated abelian groups](https://en.wikipedia.org/wiki/Fundamental_theorem_of_finitely_generated_abelian_groups) may be extended straightforwardly to finitely generated modules over a principal ring.

There are many rings for which there are algorithms for solving linear equations and systems of linear equations. However, these algorithms have generally a [computational complexity](https://en.wikipedia.org/wiki/Computational_complexity) that is much higher than similar algorithms over a field. For more details, see [Linear equation over a ring](https://en.wikipedia.org/wiki/Linear_equation_over_a_ring).

### Multilinear algebra and tensors

In [multilinear algebra](https://en.wikipedia.org/wiki/Multilinear_algebra), one considers multivariable linear transformations, that is, mappings that are linear in each of several different variables. This line of inquiry naturally leads to the idea of the [dual space](https://en.wikipedia.org/wiki/Dual_space), the vector space *V\** consisting of linear maps *f* : *V* → *F* where *F* is the field of scalars. Multilinear maps *T* : *V<sup>n</sup>* → *F* can be described via [tensor products](https://en.wikipedia.org/wiki/Tensor_product) of elements of *V\**.

If, in addition to vector addition and scalar multiplication, there is a bilinear vector product *V* × *V* → *V*, the vector space is called an [algebra](https://en.wikipedia.org/wiki/Algebra_over_a_field); for instance, associative algebras are algebras with an associate vector product (like the algebra of square matrices, or the algebra of polynomials).

### Topological vector spaces

Vector spaces that are not finite-dimensional often require additional structure to be tractable. A [normed vector space](https://en.wikipedia.org/wiki/Normed_vector_space) is a vector space along with a function called a [norm](https://en.wikipedia.org/wiki/Norm_(mathematics) "Norm (mathematics)"), which measures the "size" of elements. The norm induces a [metric](https://en.wikipedia.org/wiki/Metric_(mathematics)), which measures the distance between elements, and induces a [topology](https://en.wikipedia.org/wiki/Topological_space), which allows for a definition of continuous maps. The metric also allows for a definition of [limits](https://en.wikipedia.org/wiki/Limit_(mathematics) "Limit (mathematics)") and [completeness](https://en.wikipedia.org/wiki/Complete_metric_space) – a normed vector space that is complete is known as a [Banach space](https://en.wikipedia.org/wiki/Banach_space). A complete metric space along with the additional structure of an [inner product](https://en.wikipedia.org/wiki/Inner_product_space) (a conjugate symmetric [sesquilinear form](https://en.wikipedia.org/wiki/Sesquilinear_form)) is known as a [Hilbert space](https://en.wikipedia.org/wiki/Hilbert_space), which is in some sense a particularly well-behaved Banach space. [Functional analysis](https://en.wikipedia.org/wiki/Functional_analysis) applies the methods of linear algebra alongside those of [mathematical analysis](https://en.wikipedia.org/wiki/Mathematical_analysis) to study various function spaces; the central objects of study in functional analysis are [L<sup>p</sup> spaces](https://en.wikipedia.org/wiki/Lp_space), which are Banach spaces, and especially the *L*<sup>2</sup> space of square-integrable functions, which is the only Hilbert space among them. Functional analysis is of particular importance to quantum mechanics, the theory of partial differential equations, digital signal processing, and electrical engineering. It also provides the foundation and theoretical framework that underlies the Fourier transform and related methods.

## See also

- [Fundamental matrix (computer vision)](https://en.wikipedia.org/wiki/Fundamental_matrix_(computer_vision) "Fundamental matrix (computer vision)")
- [Geometric algebra](https://en.wikipedia.org/wiki/Geometric_algebra)
- [Linear programming](https://en.wikipedia.org/wiki/Linear_programming)
- [Linear regression](https://en.wikipedia.org/wiki/Linear_regression), a statistical estimation method
- [Numerical linear algebra](https://en.wikipedia.org/wiki/Numerical_linear_algebra)
- [Outline of linear algebra](https://en.wikipedia.org/wiki/Outline_of_linear_algebra)
- [Transformation matrix](https://en.wikipedia.org/wiki/Transformation_matrix)

## Explanatory notes

1.  This axiom is not asserting the associativity of an operation, since there are two operations in question, scalar multiplication *b***v**; and field multiplication: *ab*.
2.  This may have the consequence that some physically interesting solutions are omitted.

## Citations

1.  Banerjee, Sudipto; Roy, Anindya (2014). *Linear Algebra and Matrix Analysis for Statistics*. Texts in Statistical Science (1st ed.). Chapman and Hall/CRC. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1420095388](https://en.wikipedia.org/wiki/Special:BookSources/978-1420095388).
2.  Strang, Gilbert (July 19, 2005). *Linear Algebra and Its Applications* (4th ed.). Brooks Cole. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-03-010567-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-03-010567-8).
3.  Weisstein, Eric. ["Linear Algebra"](http://mathworld.wolfram.com/LinearAlgebra.html). *[MathWorld](https://en.wikipedia.org/wiki/MathWorld)*. Wolfram. Retrieved 16 April 2012.
4.  Hart, Roger (2010). [The Chinese Roots of Linear Algebra](https://books.google.com/books?id=zLPm3xE2qWgC). [JHU Press](https://en.wikipedia.org/wiki/JHU_Press). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780801899584](https://en.wikipedia.org/wiki/Special:BookSources/9780801899584).
5.  ^     [Vitulli, Marie](https://en.wikipedia.org/wiki/Marie_A._Vitulli). ["A Brief History of Linear Algebra and Matrix Theory"](https://web.archive.org/web/20120910034016/http://darkwing.uoregon.edu/~vitulli/441.sp04/LinAlgHistory.html). *Department of Mathematics*. University of Oregon. Archived from [the original](http://darkwing.uoregon.edu/~vitulli/441.sp04/LinAlgHistory.html) on 2012-09-10. Retrieved 2014-07-08.
6.  Koecher, M., Remmert, R. (1991). Hamilton’s Quaternions. In: Numbers. Graduate Texts in Mathematics, vol 123. Springer, New York, NY. [https://doi.org/10.1007/978-1-4612-1005-4_10](https://doi.org/10.1007/978-1-4612-1005-4_10)
7.  [Benjamin Peirce](https://en.wikipedia.org/wiki/Benjamin_Peirce) (1872) *Linear Associative Algebra*, lithograph, new edition with corrections, notes, and an added 1875 paper by Peirce, plus notes by his son [Charles Sanders Peirce](https://en.wikipedia.org/wiki/Charles_Sanders_Peirce), published in the *American Journal of Mathematics* v. 4, 1881, Johns Hopkins University, pp. 221–226, *Google* [Eprint](https://books.google.com/books?id=LQgPAAAAIAAJ&pg=PA221) and as an extract, D. Van Nostrand, 1882, *Google* [Eprint](https://archive.org/details/bub_gb_De0GAAAAYAAJ).
8.  , ch. 1, p. 27)
9.  p. 82, §3.59
10. p. 23, §1.45
11. , p. 2)
12. , p. 65)
13. , p. 324)
14. , p. 87)
15. , p. 57)
16. pp. 76–77, § 4.4.1–4.4.6
17. p. 37 §2.1.3
18. p. 20, §13
19. p. 101, §3.94
20. P. K. Jain, Khalil Ahmad (1995). ["5.1 Definitions and basic properties of inner product spaces and Hilbert spaces"](https://books.google.com/books?id=yZ68h97pnAkC&pg=PA203). *Functional analysis* (2nd ed.). New Age International. p. 203. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [81-224-0801-X](https://en.wikipedia.org/wiki/Special:BookSources/81-224-0801-X).
21. Eduard Prugovec̆ki (1981). ["Definition 2.1"](https://books.google.com/books?id=GxmQxn2PF3IC&pg=PA18). *Quantum mechanics in Hilbert space* (2nd ed.). Academic Press. pp. 18 *ff*. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-12-566060-X](https://en.wikipedia.org/wiki/Special:BookSources/0-12-566060-X).
22. [Emil Artin](https://en.wikipedia.org/wiki/Emil_Artin) (1957) *[Geometric Algebra](https://en.wikipedia.org/wiki/Geometric_Algebra_(book) "Geometric Algebra (book)")* [Interscience Publishers](https://en.wikipedia.org/wiki/Interscience_Publishers)
23. *IBM System/36O Model 40 - Sum of Products Instruction-RPQ W12561 - Special Systems Feature*. [IBM](https://en.wikipedia.org/wiki/IBM). L22-6902.
24. *IBM System/360 Custom Feature Description: 2938 Array Processor Model 1, - RPQ W24563; Model 2, RPQ 815188*. [IBM](https://en.wikipedia.org/wiki/IBM). A24-3519.
25. Barnes, George; Brown, Richard; Kato, Maso; Kuck, David; Slotnick, Daniel; Stokes, Richard (August 1968). ["The ILLIAC IV Computer"](http://gordonbell.azurewebsites.net/cgb%20files/computer%20structures%20readings%20and%20examples%201971.pdf) (PDF). *[IEEE Transactions on Computers](https://en.wikipedia.org/wiki/IEEE_Transactions_on_Computers)*. **C.17** (8): 746–757. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1968ITCmp.100..746B](https://ui.adsabs.harvard.edu/abs/1968ITCmp.100..746B). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/tc.1968.229158](https://doi.org/10.1109%2Ftc.1968.229158). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0018-9340](https://search.worldcat.org/issn/0018-9340). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [206617237](https://api.semanticscholar.org/CorpusID:206617237). Retrieved October 31, 2024.
26. [Star-100 - Hardware Reference Manual](http://bitsavers.trailing-edge.com/pdf/cdc/cyber/cyber_200/60256000_STAR-100hw_Dec75.pdf) (PDF). Revision 9. [Control Data Corporation](https://en.wikipedia.org/wiki/Control_Data_Corporation). December 15, 1975. 60256000. Retrieved October 31, 2024.
27. [Cray-1 - Computer System - Hardware Reference Manual](http://bitsavers.trailing-edge.com/pdf/cray/CRAY-1/2240004C_CRAY-1_Hardware_Reference_Nov77.pdf) (PDF). Rev. C. [Cray Research, Inc.](https://en.wikipedia.org/wiki/Cray_Research,_Inc.) November 4, 1977. 2240004. Retrieved October 31, 2024.
28. [IBM Enterprise Systems Architecture/370 and System/370 Vector Operations](http://bitsavers.org/pdf/ibm/370/vectorFacility/SA22-7125-3_Vector_Operations_Aug88.pdf) (PDF) (Fourth ed.). [IBM](https://en.wikipedia.org/wiki/IBM). August 1988. SA22-7125-3. Retrieved October 31, 2024.
29. ["GPU Performance Background User's Guide"](https://docs.nvidia.com/deeplearning/performance/dl-performance-gpu-background/index.html). *NVIDIA Docs*. Retrieved 2024-10-29.
30. Savov, Ivan (2017). *No Bullshit Guide to Linear Algebra*. MinireferenceCo. pp. 150–155. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780992001025](https://en.wikipedia.org/wiki/Special:BookSources/9780992001025).
31. ["Special Topics in Mathematics with Applications: Linear Algebra and the Calculus of Variations | Mechanical Engineering"](https://ocw.mit.edu/courses/2-035-special-topics-in-mathematics-with-applications-linear-algebra-and-the-calculus-of-variations-spring-2007/). *MIT OpenCourseWare*.
32. ["Energy and power systems"](https://engineering.ucdenver.edu/electrical-engineering/research/energy-and-power-systems). *engineering.ucdenver.edu*.
33. ["ME Undergraduate Curriculum | FAMU-FSU"](https://eng.famu.fsu.edu/me/undergraduate-curriculum#:~:text=MAS+3105+Linear+Algebra+(3),and+eigenvectors,+linear+transformations,+applications)). *eng.famu.fsu.edu*.

## General and cited sources

- Anton, Howard (1987), *Elementary Linear Algebra* (5th ed.), New York: [Wiley](https://en.wikipedia.org/wiki/John_Wiley_%26_Sons), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-84819-0](https://en.wikipedia.org/wiki/Special:BookSources/0-471-84819-0)
- [Axler, Sheldon](https://en.wikipedia.org/wiki/Sheldon_Axler) (2024), *Linear Algebra Done Right*, [Undergraduate Texts in Mathematics](https://en.wikipedia.org/wiki/Undergraduate_Texts_in_Mathematics) (4th ed.), [Springer Publishing](https://en.wikipedia.org/wiki/Springer_Publishing), [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-3-031-41026-0](https://doi.org/10.1007%2F978-3-031-41026-0), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-031-41026-0](https://en.wikipedia.org/wiki/Special:BookSources/978-3-031-41026-0), [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [3308468](https://mathscinet.ams.org/mathscinet-getitem?mr=3308468)
- Beauregard, Raymond A.; Fraleigh, John B. (1973), [A First Course In Linear Algebra: with Optional Introduction to Groups, Rings, and Fields](https://archive.org/details/firstcourseinlin0000beau), Boston: [Houghton Mifflin Company](https://en.wikipedia.org/wiki/Houghton_Mifflin_Company), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-395-14017-X](https://en.wikipedia.org/wiki/Special:BookSources/0-395-14017-X)
- [Golub, Gene H.](https://en.wikipedia.org/wiki/Gene_H._Golub); [Van Loan, Charles F.](https://en.wikipedia.org/wiki/Charles_F._Van_Loan) (1996), *Matrix Computations*, Johns Hopkins Studies in Mathematical Sciences (3rd ed.), Baltimore: [Johns Hopkins University Press](https://en.wikipedia.org/wiki/Johns_Hopkins_University_Press), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8018-5414-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8018-5414-9)
- [Halmos, Paul Richard](https://en.wikipedia.org/wiki/Paul_Halmos) (1974), *Finite-Dimensional Vector Spaces*, [Undergraduate Texts in Mathematics](https://en.wikipedia.org/wiki/Undergraduate_Texts_in_Mathematics) (1958 2nd ed.), [Springer Publishing](https://en.wikipedia.org/wiki/Springer_Publishing), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-90093-4](https://en.wikipedia.org/wiki/Special:BookSources/0-387-90093-4), [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [1251216](https://search.worldcat.org/oclc/1251216)
- Harper, Charlie (1976), *Introduction to Mathematical Physics*, New Jersey: [Prentice-Hall](https://en.wikipedia.org/wiki/Prentice-Hall), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-13-487538-9](https://en.wikipedia.org/wiki/Special:BookSources/0-13-487538-9)
- [Katznelson, Yitzhak](https://en.wikipedia.org/wiki/Yitzhak_Katznelson); Katznelson, Yonatan R. (2008), *A (Terse) Introduction to Linear Algebra*, [American Mathematical Society](https://en.wikipedia.org/wiki/American_Mathematical_Society), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8218-4419-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8218-4419-9)
- [Roman, Steven](https://en.wikipedia.org/wiki/Steven_Roman) (March 22, 2005), *Advanced Linear Algebra*, [Graduate Texts in Mathematics](https://en.wikipedia.org/wiki/Graduate_Texts_in_Mathematics) (2nd ed.), Springer, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-24766-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-24766-3)

## Further reading

### History

- Fearnley-Sander, Desmond, "[Hermann Grassmann and the Creation of Linear Algebra](https://www.jstor.org/stable/pdf/2320145.pdf)", American Mathematical Monthly **86** (1979), pp. 809–817.
- [Grassmann, Hermann](https://en.wikipedia.org/wiki/Hermann_Grassmann) (1844), *Die lineale Ausdehnungslehre ein neuer Zweig der Mathematik: dargestellt und durch Anwendungen auf die übrigen Zweige der Mathematik, wie auch auf die Statik, Mechanik, die Lehre vom Magnetismus und die Krystallonomie erläutert*, Leipzig: O. Wigand

### Introductory textbooks

- Anton, Howard (2005), *Elementary Linear Algebra (Applications Version)* (9th ed.), Wiley International
- Banerjee, Sudipto; Roy, Anindya (2014), *Linear Algebra and Matrix Analysis for Statistics*, Texts in Statistical Science (1st ed.), Chapman and Hall/CRC, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1420095388](https://en.wikipedia.org/wiki/Special:BookSources/978-1420095388)
- Bretscher, Otto (2004), *Linear Algebra with Applications* (3rd ed.), Prentice Hall, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-13-145334-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-13-145334-0)
- Farin, Gerald; [Hansford, Dianne](https://en.wikipedia.org/wiki/Dianne_Hansford) (2004), *Practical Linear Algebra: A Geometry Toolbox*, AK Peters, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-56881-234-2](https://en.wikipedia.org/wiki/Special:BookSources/978-1-56881-234-2)
- [Hefferon, Jim](https://en.wikipedia.org/wiki/Jim_Hefferon) (2020). [Linear Algebra](https://hefferon.net/linearalgebra/) (4th ed.). [Ann Arbor, Michigan](https://en.wikipedia.org/wiki/Ann_Arbor,_Michigan): Orthogonal Publishing. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-944325-11-4](https://en.wikipedia.org/wiki/Special:BookSources/978-1-944325-11-4). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [1178900366](https://search.worldcat.org/oclc/1178900366). [OL](https://en.wikipedia.org/wiki/OL_(identifier)) [30872051M](https://openlibrary.org/books/OL30872051M).
- Kolman, Bernard; Hill, David R. (2007), *Elementary Linear Algebra with Applications* (9th ed.), Prentice Hall, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-13-229654-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-13-229654-0)
- Lay, David C. (2005), *Linear Algebra and Its Applications* (3rd ed.), Addison Wesley, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-321-28713-7](https://en.wikipedia.org/wiki/Special:BookSources/978-0-321-28713-7)
- Leon, Steven J. (2006), [Linear Algebra With Applications](https://archive.org/details/linearalgebrawit00leon) (7th ed.), Pearson Prentice Hall, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-13-185785-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-13-185785-8)
- Murty, Katta G. (2014) *[Computational and Algorithmic Linear Algebra and n-Dimensional Geometry](http://www.worldscientific.com/worldscibooks/10.1142/8261)*, World Scientific Publishing, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-981-4366-62-5](https://en.wikipedia.org/wiki/Special:BookSources/978-981-4366-62-5). *[Chapter 1: Systems of Simultaneous Linear Equations](http://www.worldscientific.com/doi/suppl/10.1142/8261/suppl_file/8261_chap01.pdf)*
- Noble, B. & Daniel, J.W. (2nd Ed. 1977) *[1](https://en.wikipedia.org/wiki/1)(https://www.pearson.com/us/higher-education/program/Noble-Applied-Linear-Algebra-3rd-Edition/PGM17768.html)*, Pearson Higher Education, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0130413437](https://en.wikipedia.org/wiki/Special:BookSources/978-0130413437).
- Poole, David (2010), *Linear Algebra: A Modern Introduction* (3rd ed.), Cengage – Brooks/Cole, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-538-73545-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-538-73545-2)
- Ricardo, Henry (2010), *A Modern Introduction To Linear Algebra* (1st ed.), CRC Press, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4398-0040-9](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4398-0040-9)
- Sadun, Lorenzo (2008), *Applied Linear Algebra: the decoupling principle* (2nd ed.), AMS, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8218-4441-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8218-4441-0)
- [Strang, Gilbert](https://en.wikipedia.org/wiki/Gilbert_Strang) (2016), *Introduction to Linear Algebra* (5th ed.), Wellesley-Cambridge Press, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-09802327-7-6](https://en.wikipedia.org/wiki/Special:BookSources/978-09802327-7-6)
- The Manga Guide to Linear Algebra (2012), by [Shin Takahashi](https://en.wikipedia.org/wiki/Shin_Takahashi), Iroha Inoue and Trend-Pro Co., Ltd., [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-59327-413-9](https://en.wikipedia.org/wiki/Special:BookSources/978-1-59327-413-9)

### Advanced textbooks

- Bhatia, Rajendra (November 15, 1996), *Matrix Analysis*, [Graduate Texts in Mathematics](https://en.wikipedia.org/wiki/Graduate_Texts_in_Mathematics), Springer, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-94846-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-94846-1)
- [Demmel, James W.](https://en.wikipedia.org/wiki/James_Demmel) (August 1, 1997), *Applied Numerical Linear Algebra*, SIAM, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-89871-389-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-89871-389-3)
- [Dym, Harry](https://en.wikipedia.org/wiki/Harry_Dym) (2007), *Linear Algebra in Action*, AMS, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8218-3813-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8218-3813-6)
- [Gantmacher, Felix R.](https://en.wikipedia.org/wiki/Felix_Gantmacher) (2005), *Applications of the Theory of Matrices*, Dover Publications, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-486-44554-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-486-44554-0)
- Gantmacher, Felix R. (1990), *Matrix Theory Vol. 1* (2nd ed.), American Mathematical Society, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8218-1376-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8218-1376-8)
- Gantmacher, Felix R. (2000), *Matrix Theory Vol. 2* (2nd ed.), American Mathematical Society, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8218-2664-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8218-2664-5)
- [Gelfand, Israel M.](https://en.wikipedia.org/wiki/Israel_Gelfand) (1989), *Lectures on Linear Algebra*, Dover Publications, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-486-66082-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-486-66082-0)
- Glazman, I. M.; Ljubic, Ju. I. (2006), *Finite-Dimensional Linear Analysis*, Dover Publications, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-486-45332-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-486-45332-3)
- Golan, Johnathan S. (January 2007), *The Linear Algebra a Beginning Graduate Student Ought to Know* (2nd ed.), Springer, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4020-5494-5](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4020-5494-5)
- Golan, Johnathan S. (August 1995), *Foundations of Linear Algebra*, Kluwer, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-7923-3614-3](https://en.wikipedia.org/wiki/Special:BookSources/0-7923-3614-3)
- Greub, Werner H. (October 16, 1981), *Linear Algebra*, Graduate Texts in Mathematics (4th ed.), Springer, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8018-5414-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8018-5414-9)
- Hoffman, Kenneth; [Kunze, Ray](https://en.wikipedia.org/wiki/Ray_Kunze) (1971), *Linear algebra* (2nd ed.), Englewood Cliffs, N.J.: Prentice-Hall, Inc., [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0276251](https://mathscinet.ams.org/mathscinet-getitem?mr=0276251)
- [Halmos, Paul R.](https://en.wikipedia.org/wiki/Paul_Halmos) (August 20, 1993), *Finite-Dimensional Vector Spaces*, [Undergraduate Texts in Mathematics](https://en.wikipedia.org/wiki/Undergraduate_Texts_in_Mathematics), Springer, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-90093-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-90093-3)
- Friedberg, Stephen H.; Insel, Arnold J.; Spence, Lawrence E. (September 7, 2018), *Linear Algebra* (5th ed.), Pearson, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-13-486024-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-13-486024-4)
- [Horn, Roger A.](https://en.wikipedia.org/wiki/Roger_Horn); [Johnson, Charles R.](https://en.wikipedia.org/wiki/Charles_Royal_Johnson) (February 23, 1990), *Matrix Analysis*, Cambridge University Press, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-38632-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-38632-6)
- Horn, Roger A.; Johnson, Charles R. (June 24, 1994), *Topics in Matrix Analysis*, Cambridge University Press, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-46713-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-46713-1)
- [Lang, Serge](https://en.wikipedia.org/wiki/Serge_Lang) (March 9, 2004), *Linear Algebra*, Undergraduate Texts in Mathematics (3rd ed.), Springer, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-96412-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-96412-6)
- [Marcus, Marvin](https://en.wikipedia.org/wiki/Marvin_Marcus); [Minc, Henryk](https://en.wikipedia.org/wiki/Henryk_Minc) (2010), *A Survey of Matrix Theory and Matrix Inequalities*, Dover Publications, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-486-67102-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-486-67102-4)
- Meyer, Carl D. (February 15, 2001), [Matrix Analysis and Applied Linear Algebra](https://web.archive.org/web/20091031193126/http://matrixanalysis.com/DownloadChapters.html), Society for Industrial and Applied Mathematics (SIAM), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-89871-454-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-89871-454-8), archived from [the original](http://www.matrixanalysis.com/DownloadChapters.html) on October 31, 2009
- [Mirsky, L.](https://en.wikipedia.org/wiki/Leon_Mirsky) (1990), *An Introduction to Linear Algebra*, Dover Publications, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-486-66434-7](https://en.wikipedia.org/wiki/Special:BookSources/978-0-486-66434-7)
- [Shafarevich, I. R.](https://en.wikipedia.org/wiki/Igor_Shafarevich); Remizov, A. O (2012), [Linear Algebra and Geometry](https://www.springer.com/mathematics/algebra/book/978-3-642-30993-9), [Springer](https://en.wikipedia.org/wiki/Springer_Science%2BBusiness_Media), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-642-30993-9](https://en.wikipedia.org/wiki/Special:BookSources/978-3-642-30993-9)
- [Shilov, Georgi E.](https://en.wikipedia.org/wiki/Georgiy_Shilov) (June 1, 1977), *Linear algebra*, Dover Publications, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-486-63518-7](https://en.wikipedia.org/wiki/Special:BookSources/978-0-486-63518-7)
- Shores, Thomas S. (December 6, 2006), *Applied Linear Algebra and Matrix Analysis*, Undergraduate Texts in Mathematics, Springer, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-33194-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-33194-2)
- Smith, Larry (May 28, 1998), *Linear Algebra*, Undergraduate Texts in Mathematics, Springer, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-98455-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-98455-1)
- [Trefethen, Lloyd N.](https://en.wikipedia.org/wiki/Lloyd_N._Trefethen); Bau, David (1997), *Numerical Linear Algebra*, SIAM, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-898-71361-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-898-71361-9)

### Study guides and outlines

- Leduc, Steven A. (May 1, 1996), *Linear Algebra (Cliffs Quick Review)*, Cliffs Notes, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8220-5331-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8220-5331-6)
- Lipschutz, Seymour; Lipson, Marc (December 6, 2000), *Schaum's Outline of Linear Algebra* (3rd ed.), McGraw-Hill, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-07-136200-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-07-136200-9)
- Lipschutz, Seymour (January 1, 1989), *3,000 Solved Problems in Linear Algebra*, McGraw–Hill, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-07-038023-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-07-038023-3)
- McMahon, David (October 28, 2005), *Linear Algebra Demystified*, McGraw–Hill Professional, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-07-146579-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-07-146579-3)
- Zhang, Fuzhen (April 7, 2009), *Linear Algebra: Challenging Problems for Students*, The Johns Hopkins University Press, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8018-9125-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8018-9125-0)

## External links

### Online Resources

- [MIT Linear Algebra Video Lectures](https://ocw.mit.edu/courses/mathematics/18-06-linear-algebra-spring-2010/), a series of 34 recorded lectures by Professor [Gilbert Strang](https://en.wikipedia.org/wiki/Gilbert_Strang) (Spring 2010)
- [International Linear Algebra Society](https://www.math.technion.ac.il/iic/)
- ["Linear algebra"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society), 2001 \[1994\]
- [Linear Algebra](https://mathworld.wolfram.com/topics/LinearAlgebra.html) on [MathWorld](https://en.wikipedia.org/wiki/MathWorld)
- [Matrix and Linear Algebra Terms](http://www.economics.soton.ac.uk/staff/aldrich/matrices.htm) on [Earliest Known Uses of Some of the Words of Mathematics](http://jeff560.tripod.com/mathword.html)
- [Earliest Uses of Symbols for Matrices and Vectors](http://jeff560.tripod.com/matrices.html) on [Earliest Uses of Various Mathematical Symbols](http://jeff560.tripod.com/mathsym.html)
- [Essence of linear algebra](https://www.youtube.com/playlist?list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab), a video presentation from [3Blue1Brown](https://en.wikipedia.org/wiki/3Blue1Brown) of the basics of linear algebra, with emphasis on the relationship between the geometric, the matrix and the abstract points of view

### Online books

- Beezer, Robert A. (2009) \[2004\]. [A First Course in Linear Algebra](http://linear.ups.edu). [Gainesville, Florida](https://en.wikipedia.org/wiki/Gainesville,_Florida): [University Press of Florida](https://en.wikipedia.org/wiki/University_Press_of_Florida). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9781616100049](https://en.wikipedia.org/wiki/Special:BookSources/9781616100049).
- Connell, Edwin H. (2004) \[1999\]. [Elements of Abstract and Linear Algebra](https://www.math.miami.edu/~ec/book/). [University of Miami](https://en.wikipedia.org/wiki/University_of_Miami), [Coral Gables, Florida](https://en.wikipedia.org/wiki/Coral_Gables,_Florida): Self-published.
- [Hefferon, Jim](https://en.wikipedia.org/wiki/Jim_Hefferon) (2020). [Linear Algebra](https://hefferon.net/linearalgebra/) (4th ed.). [Ann Arbor, Michigan](https://en.wikipedia.org/wiki/Ann_Arbor,_Michigan): Orthogonal Publishing. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-944325-11-4](https://en.wikipedia.org/wiki/Special:BookSources/978-1-944325-11-4). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [1178900366](https://search.worldcat.org/oclc/1178900366). [OL](https://en.wikipedia.org/wiki/OL_(identifier)) [30872051M](https://openlibrary.org/books/OL30872051M).
- [Margalit, Dan](https://en.wikipedia.org/wiki/Dan_Margalit_(mathematician) "Dan Margalit (mathematician)"); Rabinoff, Joseph (2019). [Interactive Linear Algebra](https://textbooks.math.gatech.edu/ila/). [Georgia Institute of Technology](https://en.wikipedia.org/wiki/Georgia_Institute_of_Technology), [Atlanta, Georgia](https://en.wikipedia.org/wiki/Atlanta,_Georgia): Self-published.
- Matthews, Keith R. (2013) \[1991\]. [Elementary Linear Algebra](http://www.numbertheory.org/book/). [University of Queensland](https://en.wikipedia.org/wiki/University_of_Queensland), [Brisbane, Australia](https://en.wikipedia.org/wiki/Brisbane,_Australia): Self-published.
- Mikaelian, Vahagn H. (2020) \[2017\]. [Linear Algebra: Theory and Algorithms](https://www.researchgate.net/publication/318066716). [Yerevan, Armenia](https://en.wikipedia.org/wiki/Yerevan,_Armenia): Self-published – via [ResearchGate](https://en.wikipedia.org/wiki/ResearchGate).
- Sharipov, Ruslan, *[Course of linear algebra and multidimensional geometry](https://arxiv.org/abs/math.HO/0405323)*
- [Treil, Sergei](https://en.wikipedia.org/wiki/Sergei_Treil), *[Linear Algebra Done Wrong](https://www.math.brown.edu/~treil/papers/LADW/LADW.html)*
