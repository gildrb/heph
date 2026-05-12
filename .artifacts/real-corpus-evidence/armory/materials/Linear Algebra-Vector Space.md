[[linear-algebra.base]]

> Source: [[Vector Space]]
> License: Wikipedia content is available under CC BY-SA 4.0.

![[media/ff04488ef6aaeb82b4ebb426c82d6e21dbf65164.png]]
Vector addition and scalar multiplication: a vector <strong>v</strong> (blue) is added to another vector  <strong>w</strong> (red, upper illustration). Below,  <strong>w</strong> is stretched by a factor of 2, yielding the sum <strong>v</strong> + 2<strong>w</strong>.

In [mathematics](https://en.wikipedia.org/wiki/Mathematics) and [physics](https://en.wikipedia.org/wiki/Physics), a **vector space** (also called a **linear space**) is a [set](https://en.wikipedia.org/wiki/Set_(mathematics) "Set (mathematics)") whose elements, often called [*vectors*](https://en.wikipedia.org/wiki/Vector_(mathematics_and_physics) "Vector (mathematics and physics)"), can be added together and multiplied ("scaled") by numbers called [*scalars*](https://en.wikipedia.org/wiki/Scalar_(mathematics) "Scalar (mathematics)"). The operations of vector addition and [scalar multiplication](https://en.wikipedia.org/wiki/Scalar_multiplication) must satisfy certain requirements, called *vector [axioms](https://en.wikipedia.org/wiki/Axiom)*. **Real vector spaces** and **complex vector spaces** are kinds of vector spaces based on different kinds of scalars: [real numbers](https://en.wikipedia.org/wiki/Real_numbers) and [complex numbers](https://en.wikipedia.org/wiki/Complex_numbers). Scalars can also be, more generally, elements of any [field](https://en.wikipedia.org/wiki/Field_(mathematics) "Field (mathematics)").

Vector spaces generalize [Euclidean vectors](https://en.wikipedia.org/wiki/Euclidean_vector), which allow modeling of [physical quantities](https://en.wikipedia.org/wiki/Physical_quantity) (such as [forces](https://en.wikipedia.org/wiki/Force) and [velocity](https://en.wikipedia.org/wiki/Velocity)) that have not only a [magnitude](https://en.wikipedia.org/wiki/Magnitude_(mathematics) "Magnitude (mathematics)"), but also a [direction](https://en.wikipedia.org/wiki/Orientation_(geometry) "Orientation (geometry)"). The concept of vector spaces is fundamental for [linear algebra](https://en.wikipedia.org/wiki/Linear_algebra), together with the concept of [matrices](https://en.wikipedia.org/wiki/Matrix_(mathematics) "Matrix (mathematics)"), which allows computing in vector spaces. This provides a concise and synthetic way for manipulating and studying [systems of linear equations](https://en.wikipedia.org/wiki/Systems_of_linear_equations).

Vector spaces are characterized by their [dimension](https://en.wikipedia.org/wiki/Dimension_(vector_space) "Dimension (vector space)"), which, roughly speaking, specifies the number of independent directions in the space. This means that for two vector spaces over a given field and with the same dimension, the properties that depend only on the vector-space structure are exactly the same (technically, the vector spaces are [isomorphic](https://en.wikipedia.org/wiki/Isomorphic)). A vector space is *finite-dimensional* if its dimension is a [natural number](https://en.wikipedia.org/wiki/Natural_number). Otherwise, it is *infinite-dimensional*, and its dimension is an [infinite cardinal](https://en.wikipedia.org/wiki/Transfinite_number). Finite-dimensional vector spaces occur naturally in [geometry](https://en.wikipedia.org/wiki/Geometry) and related areas. Infinite-dimensional vector spaces occur in many areas of mathematics. For example, [polynomial rings](https://en.wikipedia.org/wiki/Polynomial_ring) are [countably](https://en.wikipedia.org/wiki/Countably_infinite) infinite-dimensional vector spaces, and many [function spaces](https://en.wikipedia.org/wiki/Function_space) have the [cardinality of the continuum](https://en.wikipedia.org/wiki/Cardinality_of_the_continuum) as a dimension.

Many vector spaces that are considered in mathematics are also endowed with other [structures](https://en.wikipedia.org/wiki/Mathematical_structure). This is the case of [algebras](https://en.wikipedia.org/wiki/Algebra_over_a_field), which include [field extensions](https://en.wikipedia.org/wiki/Field_extension), polynomial rings, [associative algebras](https://en.wikipedia.org/wiki/Associative_algebra) and [Lie algebras](https://en.wikipedia.org/wiki/Lie_algebra). This is also the case of [topological vector spaces](https://en.wikipedia.org/wiki/Topological_vector_space), which include function spaces, [inner product spaces](https://en.wikipedia.org/wiki/Inner_product_space), [normed spaces](https://en.wikipedia.org/wiki/Normed_vector_space), [Hilbert spaces](https://en.wikipedia.org/wiki/Hilbert_space) and [Banach spaces](https://en.wikipedia.org/wiki/Banach_space).

## Definition and basic properties

In this article, vectors are represented in boldface to distinguish them from scalars.

A vector space over a [field](https://en.wikipedia.org/wiki/Field_(mathematics) "Field (mathematics)") F is a non-empty [set](https://en.wikipedia.org/wiki/Set_(mathematics) "Set (mathematics)") V together with a [binary operation](https://en.wikipedia.org/wiki/Binary_operation) and a [binary function](https://en.wikipedia.org/wiki/Binary_function) that satisfy the eight [axioms](https://en.wikipedia.org/wiki/Axiom) listed below. In this context, the elements of V are commonly called *vectors*, and the elements of F are called *scalars*.

- The binary operation, called *vector addition* or simply *addition* assigns to any two vectors **v** and **w** in V a third vector in V which is commonly written as **v** + **w**, and called the *sum* of these two vectors.

- The binary function, called *[scalar multiplication](https://en.wikipedia.org/wiki/Scalar_multiplication)*, assigns to any scalar a in F and any vector **v** in V another vector in V, which is denoted *a***v**.

To have a vector space, the eight following [axioms](https://en.wikipedia.org/wiki/Axiom) must be satisfied for every **u**, **v** and **w** in V, and a and b in F.

|  |  |
|----|----|
| Axiom | Statement |
| [Associativity](https://en.wikipedia.org/wiki/Associativity) of vector addition | **u** + (**v** + **w**) = (**u** + **v**) + **w** |
| [Commutativity](https://en.wikipedia.org/wiki/Commutativity) of vector addition | **u** + **v** = **v** + **u** |
| [Identity element](https://en.wikipedia.org/wiki/Identity_element) of vector addition | There exists an element **0** ∈ *V*, called the *[zero vector](https://en.wikipedia.org/wiki/Zero_vector)*, such that **v** + **0** = **v** for all **v** ∈ *V*. |
| [Inverse elements](https://en.wikipedia.org/wiki/Inverse_element) of vector addition | For every **v** ∈ *V*, there exists an element −**v** ∈ *V*, called the *[additive inverse](https://en.wikipedia.org/wiki/Additive_inverse)* of **v**, such that **v** + (−**v**) = **0**. |
| Compatibility of scalar multiplication with field multiplication | *a*(*b***v**) = (*ab*)**v**  |
| Identity element of scalar multiplication | 1**v** = **v**, where 1 denotes the [multiplicative identity](https://en.wikipedia.org/wiki/Multiplicative_identity) in F. |
| [Distributivity](https://en.wikipedia.org/wiki/Distributivity) of scalar multiplication with respect to vector addition   | *a*(**u** + **v**) = *a***u** + *a***v** |
| Distributivity of scalar multiplication with respect to field addition | (*a* + *b*)**v** = *a***v** + *b***v** |

When the scalar field is the [real numbers](https://en.wikipedia.org/wiki/Real_number), the vector space is called a *real vector space*, and when the scalar field is the [complex numbers](https://en.wikipedia.org/wiki/Complex_number), the vector space is called a *complex vector space*. These two cases are the most common ones, but vector spaces with scalars in an arbitrary field F are also commonly considered. Such a vector space is called an F-*vector space* or a *vector space over F*.

An equivalent definition of a vector space can be given, which is much more concise but less elementary: the first four axioms (related to vector addition) say that a vector space is an [abelian group](https://en.wikipedia.org/wiki/Abelian_group) under addition, and the four remaining axioms (related to the scalar multiplication) say that this operation defines a [ring homomorphism](https://en.wikipedia.org/wiki/Ring_homomorphism) from the field *F* into the [endomorphism ring](https://en.wikipedia.org/wiki/Endomorphism_ring) of this group. Specifically, the distributivity of scalar multiplication with respect to vector addition means that multiplication by a scalar *a* is an [endomorphism](https://en.wikipedia.org/wiki/Endomorphism) of the group. The remaining three axiom establish that the [function](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)") that maps a scalar *a* to the multiplication by *a* is a ring homomorphism from the field to the endomorphism ring of the group.

Subtraction of two vectors can be defined as 

$$
\mathbf {v} -\mathbf {w} =\mathbf {v} +(-\mathbf {w} ).
$$

Direct consequences of the axioms include that, for every $s\in F$ and $\mathbf {v} \in V,$ one has

- $0\mathbf {v} =\mathbf {0} ,$
- $s\mathbf {0} =\mathbf {0} ,$
- $(-1)\mathbf {v} =-\mathbf {v} ,$
- $s\mathbf {v} =\mathbf {0}$ implies $s=0$ or $\mathbf {v} =\mathbf {0} .$

Even more concisely, a vector space is a [module](https://en.wikipedia.org/wiki/Module_(mathematics) "Module (mathematics)") over a [field](https://en.wikipedia.org/wiki/Field_(mathematics) "Field (mathematics)").

## Bases, vector coordinates, and subspaces

![[media/9088428a4874a2709eeb94391aa4990368b117fc.png]]
A vector <strong>v</strong> in <strong>R</strong><sup>2</sup> (blue) expressed in terms of different bases: using the [standard basis](https://en.wikipedia.org/wiki/Standard_basis) of <strong>R</strong><sup>2</sup>: <strong>v</strong> = <em>x</em><strong>e</strong><sub>1</sub> + <em>y</em><strong>e</strong><sub>2</sub> (black), and using a different, non-[orthogonal](https://en.wikipedia.org/wiki/Orthogonal_vector) basis: <strong>v</strong> = <strong>f</strong><sub>1</sub> + <strong>f</strong><sub>2</sub> (red).

[Linear combination](https://en.wikipedia.org/wiki/Linear_combination)  
Given a set G of elements of a F-vector space V, a linear combination of elements of G is an element of V of the form 

$$
a_{1}\mathbf {g} _{1}+a_{2}\mathbf {g} _{2}+\cdots +a_{k}\mathbf {g} _{k},
$$

 where $a_{1},\ldots ,a_{k}\in F$ and $\mathbf {g} _{1},\ldots ,\mathbf {g} _{k}\in G.$ The scalars $a_{1},\ldots ,a_{k}$ are called the *coefficients* of the linear combination.

[[Linear Independence]]  
The elements of a subset G of a F-vector space V are said to be *linearly independent* if no element of G can be written as a linear combination of the other elements of G. Equivalently, they are linearly independent if two linear combinations of elements of G define the same element of V if and only if they have the same coefficients. Also equivalently, they are linearly independent if a linear combination results in the zero vector if and only if all its coefficients are zero.

[Linear subspace](https://en.wikipedia.org/wiki/Linear_subspace)  
A *linear subspace* or *vector subspace* W of a vector space V is a non-empty subset of V that is [closed](https://en.wikipedia.org/wiki/Closure_(mathematics) "Closure (mathematics)") under vector addition and scalar multiplication; that is, the sum of two elements of W and the product of an element of W by a scalar belong to W. This implies that every linear combination of elements of W belongs to W. A linear subspace is a vector space for the induced addition and scalar multiplication; this means that the closure property implies that the axioms of a vector space are satisfied.  
The closure property also implies that *every [intersection](https://en.wikipedia.org/wiki/Intersection_(set_theory) "Intersection (set theory)") of linear subspaces is a linear subspace.*

[Linear span](https://en.wikipedia.org/wiki/Linear_span)  
Given a subset G of a vector space V, the *linear span* or simply the *span* of G is the smallest linear subspace of V that contains G, in the sense that it is the intersection of all linear subspaces that contain G. The span of G is also the set of all linear combinations of elements of G.  
If W is the span of G, one says that G *spans* or *generates* W, and that G is a *[spanning set](https://en.wikipedia.org/wiki/Spanning_set)* or a *generating set* of W.

[Basis](https://en.wikipedia.org/wiki/Basis_(linear_algebra) "Basis (linear algebra)") and [dimension](https://en.wikipedia.org/wiki/Dimension_(vector_space) "Dimension (vector space)")  
A subset of a vector space is a *basis* if its elements are linearly independent and span the vector space. Every vector space has at least one basis, or many in general (see [Basis (linear algebra) § Proof that every vector space has a basis](https://en.wikipedia.org/wiki/Basis_(linear_algebra)#Proof_that_every_vector_space_has_a_basis "Basis (linear algebra)")). Moreover, all bases of a vector space have the same [cardinality](https://en.wikipedia.org/wiki/Cardinality), which is called the *dimension* of the vector space (see [Dimension theorem for vector spaces](https://en.wikipedia.org/wiki/Dimension_theorem_for_vector_spaces)). This is a fundamental property of vector spaces, which is detailed in the remainder of the section.

*Bases* are a fundamental tool for the study of vector spaces, especially when the dimension is finite. In the infinite-dimensional case, the existence of infinite bases, often called [Hamel bases](https://en.wikipedia.org/wiki/Hamel_bases), depends on the [axiom of choice](https://en.wikipedia.org/wiki/Axiom_of_choice). It follows that, in general, no base can be explicitly described. For example, the [real numbers](https://en.wikipedia.org/wiki/Real_number) form an infinite-dimensional vector space over the [rational numbers](https://en.wikipedia.org/wiki/Rational_number), for which no specific basis is known.

Consider a basis $(\mathbf {b} _{1},\mathbf {b} _{2},\ldots ,\mathbf {b} _{n})$ of a vector space V of dimension n over a field F. The definition of a basis implies that every $\mathbf {v} \in V$ may be written 

$$
\mathbf {v} =a_{1}\mathbf {b} _{1}+\cdots +a_{n}\mathbf {b} _{n},
$$

 with $a_{1},\dots ,a_{n}$ in F, and that this decomposition is unique. The scalars $a_{1},\ldots ,a_{n}$ are called the *coordinates* of **v** on the basis. They are also said to be the *coefficients* of the decomposition of **v** on the basis. One also says that the n-[tuple](https://en.wikipedia.org/wiki/Tuple) of the coordinates is the [coordinate vector](https://en.wikipedia.org/wiki/Coordinate_vector) of **v** on the basis, since the set $F^{n}$ of the n-tuples of elements of F is a vector space for [componentwise](https://en.wikipedia.org/wiki/Componentwise_operation) addition and scalar multiplication, whose dimension is n.

The [one-to-one correspondence](https://en.wikipedia.org/wiki/One-to-one_correspondence) between vectors and their coordinate vectors maps vector addition to vector addition and scalar multiplication to scalar multiplication. It is thus a [vector space isomorphism](https://en.wikipedia.org/wiki/Vector_space_isomorphism), which allows translating reasonings and computations on vectors into reasonings and computations on their coordinates.

## History

Vector spaces stem from [affine geometry](https://en.wikipedia.org/wiki/Affine_geometry), via the introduction of [coordinates](https://en.wikipedia.org/wiki/Coordinate) in the plane or three-dimensional space. Around 1636, French mathematicians [René Descartes](https://en.wikipedia.org/wiki/Ren%C3%A9_Descartes) and [Pierre de Fermat](https://en.wikipedia.org/wiki/Pierre_de_Fermat) founded [analytic geometry](https://en.wikipedia.org/wiki/Analytic_geometry) by identifying solutions to an equation of two variables with points on a plane [curve](https://en.wikipedia.org/wiki/Curve). To achieve geometric solutions without using coordinates, [Bolzano](https://en.wikipedia.org/wiki/Bernhard_Bolzano) introduced, in 1804, certain operations on points, lines, and planes, which are predecessors of vectors.  introduced the notion of [barycentric coordinates](https://en.wikipedia.org/wiki/Barycentric_coordinates_(mathematics)).  introduced an [equivalence relation](https://en.wikipedia.org/wiki/Equivalence_relation) on directed line segments that share the same length and direction which he called [equipollence](https://en.wikipedia.org/wiki/Equipollence_(geometry) "Equipollence (geometry)"). A [Euclidean vector](https://en.wikipedia.org/wiki/Euclidean_vector) is then an [equivalence class](https://en.wikipedia.org/wiki/Equivalence_class) of that relation.

Vectors were reconsidered with the presentation of [complex numbers](https://en.wikipedia.org/wiki/Complex_numbers) by [Argand](https://en.wikipedia.org/wiki/Jean-Robert_Argand) and [Hamilton](https://en.wikipedia.org/wiki/William_Rowan_Hamilton) and the inception of [quaternions](https://en.wikipedia.org/wiki/Quaternion) by the latter. They are elements in **R**<sup>2</sup> and **R**<sup>4</sup>; treating them using [linear combinations](https://en.wikipedia.org/wiki/Linear_combination) goes back to [Laguerre](https://en.wikipedia.org/wiki/Laguerre) in 1867, who also defined [systems of linear equations](https://en.wikipedia.org/wiki/System_of_linear_equations).

In 1857, [Cayley](https://en.wikipedia.org/wiki/Arthur_Cayley) introduced the [matrix notation](https://en.wikipedia.org/wiki/Matrix_notation) which allows for harmonization and simplification of [linear maps](https://en.wikipedia.org/wiki/Linear_map). Around the same time, [Grassmann](https://en.wikipedia.org/wiki/Grassmann) studied the barycentric calculus initiated by Möbius. He envisaged sets of abstract objects endowed with operations. In his work, the concepts of [[Linear Independence]] and [dimension](https://en.wikipedia.org/wiki/Dimension), as well as [scalar products](https://en.wikipedia.org/wiki/Scalar_product) are present. Grassmann's 1844 work exceeds the framework of vector spaces as well since his considering multiplication led him to what are today called [algebras](https://en.wikipedia.org/wiki/Algebras_over_a_field). Italian mathematician [Peano](https://en.wikipedia.org/wiki/Giuseppe_Peano) was the first to give the modern definition of vector spaces and linear maps in 1888, although he called them "linear systems". Peano's axiomatization allowed for vector spaces with infinite dimension, but Peano did not develop that theory further. In 1897, [Salvatore Pincherle](https://en.wikipedia.org/wiki/Salvatore_Pincherle) adopted Peano's axioms and made initial inroads into the theory of infinite-dimensional vector spaces.

An important development of vector spaces is due to the construction of [function spaces](https://en.wikipedia.org/wiki/Function_spaces) by [Henri Lebesgue](https://en.wikipedia.org/wiki/Henri_Lebesgue). This was later formalized by [Banach](https://en.wikipedia.org/wiki/Stefan_Banach) and [Hilbert](https://en.wikipedia.org/wiki/David_Hilbert), around 1920. At that time, [algebra](https://en.wikipedia.org/wiki/Algebra) and the new field of [functional analysis](https://en.wikipedia.org/wiki/Functional_analysis) began to interact, notably with key concepts such as [spaces of *p*-integrable functions](https://en.wikipedia.org/wiki/Lp_space) and [Hilbert spaces](https://en.wikipedia.org/wiki/Hilbert_space).

## Examples

### Arrows in the plane

![[media/2d8ee9b552df099502f65a4056856bc882a67dc7.png]]

Vector addition: the sum **v** + **w** (black) of the vectors **v** (blue) and **w** (red) is shown.

![[media/579c57c51515c36b7fab15b72452e68bfd219ea8.png]]

Scalar multiplication: the multiples −**v** and 2**w** are shown.

The first example of a vector space consists of [arrows](https://en.wikipedia.org/wiki/Arrow_(symbol) "Arrow (symbol)") in a fixed [plane](https://en.wikipedia.org/wiki/Plane_(geometry)), starting at one fixed point. This is used in physics to describe [forces](https://en.wikipedia.org/wiki/Force) or [velocities](https://en.wikipedia.org/wiki/Velocity). Given any two such arrows, **v** and **w**, the [parallelogram](https://en.wikipedia.org/wiki/Parallelogram) spanned by these two arrows contains one diagonal arrow that starts at the origin, too. This new arrow is called the *sum* of the two arrows, and is denoted **v** + **w**. In the special case of two arrows on the same line, their sum is the arrow on this line whose length is the sum or the difference of the lengths, depending on whether the arrows have the same direction. Another operation that can be done with arrows is scaling: given any positive [real number](https://en.wikipedia.org/wiki/Real_number) *a*, the arrow that has the same direction as **v**, but is dilated or shrunk by multiplying its length by *a*, is called *multiplication* of **v** by *a*. It is denoted *a***v**. When *a* is negative, *a***v** is defined as the arrow pointing in the opposite direction instead.

The following shows a few examples: if *a* = 2, the resulting vector *a***w** has the same direction as **w**, but is stretched to the double length of **w** (the second image). Equivalently, 2**w** is the sum **w** + **w**. Moreover, (−1)**v** = −**v** has the opposite direction and the same length as **v** (blue vector pointing down in the second image).

### Ordered pairs of numbers

A second key example of a vector space is provided by pairs of real numbers x and y. The order of the components x and y is significant, so such a pair is also called an [ordered pair](https://en.wikipedia.org/wiki/Ordered_pair). Such a pair is written as (*x*, *y*). The sum of two such pairs and the multiplication of a pair with a number is defined as follows: 

$$
{\begin{aligned}(x_{1},y_{1})+(x_{2},y_{2})&=(x_{1}+x_{2},y_{1}+y_{2}),\\a(x,y)&=(ax,ay).\end{aligned}}
$$

The first example above reduces to this example if an arrow is represented by a pair of [Cartesian coordinates](https://en.wikipedia.org/wiki/Cartesian_coordinates) of its endpoint.

### Coordinate space

The simplest example of a vector space over a field *F* is the field *F* itself with its addition viewed as vector addition and its multiplication viewed as scalar multiplication. More generally, all [*n*-tuples](https://en.wikipedia.org/wiki/Tuple) (sequences of length *n*) 

$$
(a_{1},a_{2},\dots ,a_{n})
$$

 of elements *a*<sub>*i*</sub> of *F* form a vector space that is usually denoted *F*<sup>*n*</sup> and called a **coordinate space**. The case *n* = 1 is the above-mentioned simplest example, in which the field *F* is also regarded as a vector space over itself. The case *F* = **R** and *n* = 2 (so **R**<sup>2</sup>) reduces to the previous example.

### Complex numbers and other field extensions

The set of [complex numbers](https://en.wikipedia.org/wiki/Complex_numbers) **C**, numbers that can be written in the form *x* + *iy* for [real numbers](https://en.wikipedia.org/wiki/Real_numbers) *x* and *y* where *i* is the [imaginary unit](https://en.wikipedia.org/wiki/Imaginary_unit), form a vector space over the reals with the usual addition and multiplication: (*x* + *iy*) + (*a* + *ib*) = (*x* + *a*) + *i*(*y* + *b*) and *c* ⋅ (*x* + *iy*) = (*c* ⋅ *x*) + *i*(*c* ⋅ *y*) for real numbers *x*, *y*, *a*, *b* and *c*. The various axioms of a vector space follow from the fact that the same rules hold for complex number arithmetic. The example of complex numbers is essentially the same as (that is, it is *isomorphic* to) the vector space of ordered pairs of real numbers mentioned above: if we think of the complex number *x* + *i* *y* as representing the ordered pair (*x*, *y*) in the [complex plane](https://en.wikipedia.org/wiki/Complex_plane) then we see that the rules for addition and scalar multiplication correspond exactly to those in the earlier example.

More generally, [field extensions](https://en.wikipedia.org/wiki/Field_extension) provide another class of examples of vector spaces, particularly in algebra and [algebraic number theory](https://en.wikipedia.org/wiki/Algebraic_number_theory): a field *F* containing a smaller field *E* is an *E*-vector space, by the given multiplication and addition operations of *F*. For example, the complex numbers are a vector space over **R**, and the field extension $\mathbf {Q} (i{\sqrt {5}})$ is a vector space over **Q**.

### Function spaces

![[media/b1254717f8e5da4554e12bdaa34479e2f1f8620e.png]]
Addition of functions: the sum of the sine and the exponential function is $\sin +\exp :\mathbb {R} \to \mathbb {R}$ with $(\sin +\exp )(x)=\sin(x)+\exp(x)$.

Functions from any fixed set Ω to a field *F* also form vector spaces, by performing addition and scalar multiplication pointwise. That is, the sum of two functions *f* and *g* is the function $(f+g)$ given by 

$$
(f+g)(w)=f(w)+g(w),
$$

 and similarly for multiplication. Such function spaces occur in many geometric situations, when Ω is the [real line](https://en.wikipedia.org/wiki/Real_line) or an [interval](https://en.wikipedia.org/wiki/Interval_(mathematics) "Interval (mathematics)"), or other [subsets](https://en.wikipedia.org/wiki/Subset) of **R**. Many notions in topology and analysis, such as [continuity](https://en.wikipedia.org/wiki/Continuous_function), [integrability](https://en.wikipedia.org/wiki/Integral) or [differentiability](https://en.wikipedia.org/wiki/Differentiability) are well-behaved with respect to linearity: sums and scalar multiples of functions possessing such a property still have that property. Therefore, the set of such functions are vector spaces, whose study belongs to [functional analysis](https://en.wikipedia.org/wiki/Functional_analysis).

### Linear equations

Systems of [homogeneous linear equations](https://en.wikipedia.org/wiki/Homogeneous_linear_equation) are closely tied to vector spaces. For example, the solutions of 

$$
{\begin{alignedat}{9}&&a\,&&+\,3b\,&\,+&\,&c&\,=0\\4&&a\,&&+\,2b\,&\,+&\,2&c&\,=0\\\end{alignedat}}
$$

 are given by triples with arbitrary $a,$ $b=a/2,$ and $c=-5a/2.$ They form a vector space: sums and scalar multiples of such triples still satisfy the same ratios of the three variables; thus they are solutions, too. [Matrices](https://en.wikipedia.org/wiki/Matrix_(mathematics) "Matrix (mathematics)") can be used to condense multiple linear equations as above into one vector equation, namely

$$
A\mathbf {x} =\mathbf {0} ,
$$

where $A={\begin{bmatrix}1&3&1\\4&2&2\end{bmatrix}}$ is the matrix containing the coefficients of the given equations, $\mathbf {x}$ is the vector $(a,b,c),$ $A\mathbf {x}$ denotes the [matrix product](https://en.wikipedia.org/wiki/Matrix_product), and $\mathbf {0} =(0,0)$ is the zero vector. In a similar vein, the solutions of homogeneous *linear differential equations* form vector spaces. For example,

$$
f^{\prime \prime }(x)+2f^{\prime }(x)+f(x)=0
$$

yields $f(x)=ae^{-x}+bxe^{-x},$ where $a$ and $b$ are arbitrary constants, and $e^{x}$ is the [natural exponential function](https://en.wikipedia.org/wiki/Natural_exponential_function).

## Linear maps and matrices

The relation of two vector spaces can be expressed by *linear map* or *[[Linear Transformation]]*. They are [functions](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)") that reflect the vector space structure, that is, they preserve sums and scalar multiplication: 

$$
{\begin{aligned}f(\mathbf {v} +\mathbf {w} )&=f(\mathbf {v} )+f(\mathbf {w} ),\\f(a\cdot \mathbf {v} )&=a\cdot f(\mathbf {v} )\end{aligned}}
$$

 for all $\mathbf {v}$ and $\mathbf {w}$ in $V,$ all $a$ in $F.$

An *[isomorphism](https://en.wikipedia.org/wiki/Isomorphism)* is a linear map *f* : *V* → *W* such that there exists an [inverse map](https://en.wikipedia.org/wiki/Inverse_map) *g* : *W* → *V*, which is a map such that the two possible [compositions](https://en.wikipedia.org/wiki/Function_composition) *f* ∘ *g* : *W* → *W* and *g* ∘ *f* : *V* → *V* are [identity maps](https://en.wikipedia.org/wiki/Identity_function). Equivalently, *f* is both one-to-one ([injective](https://en.wikipedia.org/wiki/Injective)) and onto ([surjective](https://en.wikipedia.org/wiki/Surjective)). If there exists an isomorphism between *V* and *W*, the two spaces are said to be *isomorphic*; they are then essentially identical as vector spaces, since all identities holding in *V* are, via *f*, transported to similar ones in *W*, and vice versa via *g*.

![[media/f99b0d4b09f1a6dc3457fb8a24deee360f6eefef.png]]
Describing an arrow vector <strong>v</strong> by its coordinates <em>x</em> and <em>y</em> yields an isomorphism of vector spaces.

For example, the arrows in the plane and the ordered pairs of numbers vector spaces in the introduction above (see [§ Examples](#Examples)) are isomorphic: a planar arrow **v** departing at the [origin](https://en.wikipedia.org/wiki/Origin_(mathematics) "Origin (mathematics)") of some (fixed) [coordinate system](https://en.wikipedia.org/wiki/Coordinate_system) can be expressed as an ordered pair by considering the *x*- and *y*-component of the arrow, as shown in the image at the right. Conversely, given a pair (*x*, *y*), the arrow going by *x* to the right (or to the left, if *x* is negative), and *y* up (down, if *y* is negative) turns back the arrow **v**.

Linear maps *V* → *W* between two vector spaces form a vector space Hom<sub>*F*</sub>(*V*, *W*), also denoted L(*V*, *W*), or 𝓛(*V*, *W*). The space of linear maps from *V* to *F* is called the *[dual vector space](https://en.wikipedia.org/wiki/Dual_vector_space)*, denoted *V*<sup>∗</sup>. Via the injective [natural](https://en.wikipedia.org/wiki/Natural_(category_theory)) map *V* → *V*<sup>∗∗</sup>, any vector space can be embedded into its *bidual*; the map is an isomorphism if and only if the space is finite-dimensional.

Once a basis of *V* is chosen, linear maps *f* : *V* → *W* are completely determined by specifying the images of the basis vectors, because any element of *V* is expressed uniquely as a linear combination of them. If dim *V* = dim *W*, a [1-to-1 correspondence](https://en.wikipedia.org/wiki/Bijection) between fixed bases of *V* and *W* gives rise to a linear map that maps any basis element of *V* to the corresponding basis element of *W*. It is an isomorphism, by its very definition. Therefore, two vector spaces over a given field are isomorphic if their dimensions agree and vice versa. Another way to express this is that any vector space over a given field is *completely classified* ([up to](https://en.wikipedia.org/wiki/Up_to) isomorphism) by its dimension, a single number. In particular, any *n*-dimensional *F*-vector space *V* is isomorphic to *F*<sup>*n*</sup>. However, there is no "canonical" or preferred isomorphism; an isomorphism *φ* : *F*<sup>*n*</sup> → *V* is equivalent to the choice of a basis of *V*, by mapping the standard basis of *F*<sup>*n*</sup> to *V*, via *φ*.

### Matrices

![[media/3284b7b830f53f4cfad0a09827f60fee9f3f425e.png]]
A typical matrix

*Matrices* are a useful notion to encode linear maps. They are written as a rectangular array of scalars as in the image at the right. Any *m*-by-*n* matrix $A$ gives rise to a linear map from *F*<sup>*n*</sup> to *F*<sup>*m*</sup>, by the following 

$$
\mathbf {x} =(x_{1},x_{2},\ldots ,x_{n})\mapsto \left(\sum _{j=1}^{n}a_{1j}x_{j},\sum _{j=1}^{n}a_{2j}x_{j},\ldots ,\sum _{j=1}^{n}a_{mj}x_{j}\right),
$$

 where $\sum$ denotes [summation](https://en.wikipedia.org/wiki/Summation), or by using the [[Matrix Multiplication]] of the matrix $A$ with the coordinate vector $\mathbf {x}$:

$$
\mathbf {x} \mapsto A\mathbf {x} .
$$

Moreover, after choosing bases of *V* and *W*, *any* linear map *f* : *V* → *W* is uniquely represented by a matrix via this assignment.

![[media/ca0c04adcab6c8586f7b31f05ecef250c94aa82c.png]]
The volume of this [parallelepiped](https://en.wikipedia.org/wiki/Parallelepiped) is the absolute value of the determinant of the 3-by-3 matrix formed by the vectors <strong>r</strong><sub>1</sub>, <strong>r</strong><sub>2</sub>, and <strong>r</strong><sub>3</sub>.

The [[Determinant]] det (*A*) of a [square matrix](https://en.wikipedia.org/wiki/Square_matrix) *A* is a scalar that tells whether the associated map is an isomorphism or not: to be so it is sufficient and necessary that the determinant is nonzero. The linear transformation of **R**<sup>*n*</sup> corresponding to a real *n*-by-*n* matrix is [orientation preserving](https://en.wikipedia.org/wiki/Orientation_(vector_space) "Orientation (vector space)") if and only if its determinant is positive.

### Eigenvalues and eigenvectors

[Endomorphisms](https://en.wikipedia.org/wiki/Endomorphism), linear maps *f* : *V* → *V*, are particularly important since in this case vectors **v** can be compared with their image under *f*, *f*(**v**). Any nonzero vector **v** satisfying *λ***v** = *f*(**v**), where *λ* is a scalar, is called an *eigenvector* of *f* with *eigenvalue* *λ*. Equivalently, **v** is an element of the [kernel](https://en.wikipedia.org/wiki/Kernel_(linear_algebra) "Kernel (linear algebra)") of the difference *f* − *λ* · Id (where Id is the [identity map](https://en.wikipedia.org/wiki/Identity_function) *V* → *V*). If *V* is finite-dimensional, this can be rephrased using determinants: *f* having eigenvalue *λ* is equivalent to 

$$
\det(f-\lambda \cdot \operatorname {Id} )=0.
$$

 By spelling out the definition of the determinant, the expression on the left hand side can be seen to be a polynomial function in *λ*, called the [characteristic polynomial](https://en.wikipedia.org/wiki/Characteristic_polynomial) of *f*. If the field *F* is large enough to contain a zero of this polynomial (which automatically happens for *F* [algebraically closed](https://en.wikipedia.org/wiki/Algebraically_closed_field), such as *F* = **C**) any linear map has at least one eigenvector. The vector space *V* may or may not possess an [eigenbasis](https://en.wikipedia.org/wiki/Eigenbasis), a basis consisting of eigenvectors. This phenomenon is governed by the [Jordan canonical form](https://en.wikipedia.org/wiki/Jordan_canonical_form) of the map. The set of all eigenvectors corresponding to a particular eigenvalue of *f* forms a vector space known as the *eigenspace* corresponding to the eigenvalue (and *f*) in question.

## Basic constructions

In addition to the above concrete examples, there are a number of standard linear algebraic constructions that yield vector spaces related to given ones.

### Subspaces and quotient spaces

![[media/aa70ee8aa27249630bbc005163460e21ff2ece76.png]]
A line passing through the [origin](https://en.wikipedia.org/wiki/Origin_(mathematics)) (blue, thick) in [R3](https://en.wikipedia.org/wiki/Euclidean_space) is a linear subspace. It is the intersection of two [planes](https://en.wikipedia.org/wiki/Plane_(mathematics)) (green and yellow).

A nonempty [subset](https://en.wikipedia.org/wiki/Subset) $W$ of a vector space $V$ that is closed under addition and scalar multiplication (and therefore contains the $\mathbf {0}$-vector of $V$) is called a *linear subspace* of $V$, or simply a *subspace* of $V$, when the ambient space is unambiguously a vector space. Subspaces of $V$ are vector spaces (over the same field) in their own right. The intersection of all subspaces containing a given set $S$ of vectors is called its [span](https://en.wikipedia.org/wiki/Linear_span), and it is the smallest subspace of $V$ containing the set $S$. Expressed in terms of elements, the span is the subspace consisting of all the [linear combinations](https://en.wikipedia.org/wiki/Linear_combination) of elements of $S$.

Linear subspace of dimension 1 and 2 are referred to as a *line* (also *vector line*), and a *plane* respectively. If *W* is an *n*-dimensional vector space, any subspace of dimension 1 less, i.e., of dimension $n-1$ is called a *[hyperplane](https://en.wikipedia.org/wiki/Hyperplane)*.

The counterpart to subspaces are *quotient vector spaces*. Given any subspace $W\subseteq V$, the quotient space $V/W$ ("$V$ [modulo](https://en.wikipedia.org/wiki/Modular_arithmetic) $W$") is defined as follows: as a set, it consists of 

$$
\mathbf {v} +W=\{\mathbf {v} +\mathbf {w} :\mathbf {w} \in W\},
$$

 where $\mathbf {v}$ is an arbitrary vector in $V$. The sum of two such elements $\mathbf {v} _{1}+W$ and $\mathbf {v} _{2}+W$ is $\left(\mathbf {v} _{1}+\mathbf {v} _{2}\right)+W$, and scalar multiplication is given by $a\cdot (\mathbf {v} +W)=(a\cdot \mathbf {v} )+W$. The key point in this definition is that $\mathbf {v} _{1}+W=\mathbf {v} _{2}+W$ [if and only if](https://en.wikipedia.org/wiki/If_and_only_if) the difference of $\mathbf {v} _{1}$ and $\mathbf {v} _{2}$ lies in $W$. This way, the quotient space "forgets" information that is contained in the subspace $W$.

The [kernel](https://en.wikipedia.org/wiki/Kernel_(algebra) "Kernel (algebra)") $\ker(f)$ of a linear map $f:V\to W$ consists of vectors $\mathbf {v}$ that are mapped to $\mathbf {0}$ in $W$. The kernel and the [image](https://en.wikipedia.org/wiki/Image_(mathematics) "Image (mathematics)") $\operatorname {im} (f)=\{f(\mathbf {v} ):\mathbf {v} \in V\}$ are subspaces of $V$ and $W$, respectively.

An important example is the kernel of a linear map $\mathbf {x} \mapsto A\mathbf {x}$ for some fixed matrix $A$. The kernel of this map is the subspace of vectors $\mathbf {x}$ such that $A\mathbf {x} =\mathbf {0}$, which is precisely the set of solutions to the system of homogeneous linear equations belonging to $A$. This concept also extends to linear differential equations 

$$
a_{0}f+a_{1}{\frac {df}{dx}}+a_{2}{\frac {d^{2}f}{dx^{2}}}+\cdots +a_{n}{\frac {d^{n}f}{dx^{n}}}=0,
$$

 where the coefficients $a_{i}$ are functions in $x,$ too. In the corresponding map 

$$
f\mapsto D(f)=\sum _{i=0}^{n}a_{i}{\frac {d^{i}f}{dx^{i}}},
$$

 the [derivatives](https://en.wikipedia.org/wiki/Derivative) of the function $f$ appear linearly (as opposed to $f^{\prime \prime }(x)^{2}$, for example). Since differentiation is a linear procedure (that is, $(f+g)^{\prime }=f^{\prime }+g^{\prime }$ and $(c\cdot f)^{\prime }=c\cdot f^{\prime }$ for a constant $c$) this assignment is linear, called a [linear differential operator](https://en.wikipedia.org/wiki/Linear_differential_operator). In particular, the solutions to the differential equation $D(f)=0$ form a vector space (over **R** or **C**).

The existence of kernels and images is part of the statement that the [category of vector spaces](https://en.wikipedia.org/wiki/Category_of_vector_spaces) (over a fixed field $F$) is an [abelian category](https://en.wikipedia.org/wiki/Abelian_category), that is, a corpus of mathematical objects and structure-preserving maps between them (a [category](https://en.wikipedia.org/wiki/Category_(mathematics) "Category (mathematics)")) that behaves much like the [category of abelian groups](https://en.wikipedia.org/wiki/Category_of_abelian_groups). Because of this, many statements such as the [first isomorphism theorem](https://en.wikipedia.org/wiki/First_isomorphism_theorem) (also called [rank–nullity theorem](https://en.wikipedia.org/wiki/Rank%E2%80%93nullity_theorem) in matrix-related terms) 

$$
V/\ker(f)\;\equiv \;\operatorname {im} (f)
$$

 and the second and third isomorphism theorem can be formulated and proven in a way very similar to the corresponding statements for [groups](https://en.wikipedia.org/wiki/Group_(mathematics) "Group (mathematics)").

### Direct product and direct sum

The *direct product* of vector spaces and the *direct sum* of vector spaces are two ways of combining an indexed family of vector spaces into a new vector space.

The *direct product* $\textstyle {\prod _{i\in I}V_{i}}$ of a family of vector spaces $V_{i}$ consists of the set of all tuples $\left(\mathbf {v} _{i}\right)_{i\in I}$, which specify for each index $i$ in some [index set](https://en.wikipedia.org/wiki/Index_set) $I$ an element $\mathbf {v} _{i}$ of $V_{i}$. Addition and scalar multiplication is performed componentwise. A variant of this construction is the *direct sum* $\bigoplus _{i\in I}V_{i}$ (also called [coproduct](https://en.wikipedia.org/wiki/Coproduct) and denoted $\coprod _{i\in I}V_{i}$), where only tuples with finitely many nonzero vectors are allowed. If the index set $I$ is finite, the two constructions agree, but in general they are different.

### Tensor product

The *tensor product* $V\otimes _{F}W,$ or simply $V\otimes W,$ of two vector spaces $V$ and $W$ is one of the central notions of [multilinear algebra](https://en.wikipedia.org/wiki/Multilinear_algebra), which deals with extending notions such as linear maps to several variables. A map $g:V\times W\to X$ from the [Cartesian product](https://en.wikipedia.org/wiki/Cartesian_product) $V\times W$ is called [bilinear](https://en.wikipedia.org/wiki/Bilinear_map) if $g$ is linear in both variables $\mathbf {v}$ and $\mathbf {w} .$ That is to say, for fixed $\mathbf {w}$ the map $\mathbf {v} \mapsto g(\mathbf {v} ,\mathbf {w} )$ is linear in the sense above and likewise for fixed $\mathbf {v} .$

![[media/a69fc00ec50114e4298eaaaa82e188ae8cba8c91.png]]
[Commutative diagram](https://en.wikipedia.org/wiki/Commutative_diagram) depicting the universal property of the tensor product

The tensor product is a particular vector space that is a *universal* recipient of bilinear maps $g,$ as follows. It is defined as the vector space consisting of finite (formal) sums of symbols called [tensors](https://en.wikipedia.org/wiki/Tensor) 

$$
\mathbf {v} _{1}\otimes \mathbf {w} _{1}+\mathbf {v} _{2}\otimes \mathbf {w} _{2}+\cdots +\mathbf {v} _{n}\otimes \mathbf {w} _{n},
$$

 subject to the rules 

$$
{\begin{alignedat}{6}a\cdot (\mathbf {v} \otimes \mathbf {w} )~&=~(a\cdot \mathbf {v} )\otimes \mathbf {w} ~=~\mathbf {v} \otimes (a\cdot \mathbf {w} ),&&~~{\text{ where }}a{\text{ is a scalar}}\\(\mathbf {v} _{1}+\mathbf {v} _{2})\otimes \mathbf {w} ~&=~\mathbf {v} _{1}\otimes \mathbf {w} +\mathbf {v} _{2}\otimes \mathbf {w} &&\\\mathbf {v} \otimes (\mathbf {w} _{1}+\mathbf {w} _{2})~&=~\mathbf {v} \otimes \mathbf {w} _{1}+\mathbf {v} \otimes \mathbf {w} _{2}.&&\\\end{alignedat}}
$$

 These rules ensure that the map $f$ from the $V\times W$ to $V\otimes W$ that maps a [tuple](https://en.wikipedia.org/wiki/Tuple) $(\mathbf {v} ,\mathbf {w} )$ to $\mathbf {v} \otimes \mathbf {w}$ is bilinear. The universality states that given *any* vector space $X$ and *any* bilinear map $g:V\times W\to X,$ there exists a unique map $u,$ shown in the diagram with a dotted arrow, whose [composition](https://en.wikipedia.org/wiki/Function_composition) with $f$ equals $g$: $u(\mathbf {v} \otimes \mathbf {w} )=g(\mathbf {v} ,\mathbf {w} ).$ This is called the [universal property](https://en.wikipedia.org/wiki/Universal_property) of the tensor product, an instance of the method—much used in advanced abstract algebra—to indirectly define objects by specifying maps from or to this object.

## Vector spaces with additional structure

From the point of view of linear algebra, vector spaces are completely understood insofar as any vector space over a given field is characterized, up to isomorphism, by its dimension. However, vector spaces *per se* do not offer a framework to deal with the question—crucial to analysis—whether a sequence of functions [converges](https://en.wikipedia.org/wiki/Limit_of_a_sequence) to another function. Likewise, linear algebra is not adapted to deal with [infinite series](https://en.wikipedia.org/wiki/Infinite_series), since the addition operation allows only finitely many terms to be added. Therefore, the needs of [functional analysis](https://en.wikipedia.org/wiki/Functional_analysis) require considering additional structures.

A vector space may be given a [partial order](https://en.wikipedia.org/wiki/Partial_order) $\,\leq ,\,$ under which some vectors can be compared. For example, $n$-dimensional real space $\mathbf {R} ^{n}$ can be ordered by comparing its vectors componentwise. [Ordered vector spaces](https://en.wikipedia.org/wiki/Ordered_vector_space), for example [Riesz spaces](https://en.wikipedia.org/wiki/Riesz_space), are fundamental to [Lebesgue integration](https://en.wikipedia.org/wiki/Lebesgue_integration), which relies on the ability to express a function as a difference of two positive functions 

$$
f=f^{+}-f^{-}.
$$

 where $f^{+}$ denotes the positive part of $f$ and $f^{-}$ the negative part.

### Normed vector spaces and inner product spaces

"Measuring" vectors is done by specifying a [norm](https://en.wikipedia.org/wiki/Norm_(mathematics) "Norm (mathematics)"), a datum which measures lengths of vectors, or by an [inner product](https://en.wikipedia.org/wiki/Inner_product), which measures angles between vectors. Norms and inner products are denoted $|\mathbf {v} |$ and $\langle \mathbf {v} ,\mathbf {w} \rangle ,$ respectively. The datum of an inner product entails that lengths of vectors can be defined too, by defining the associated norm $|\mathbf {v} |:={\sqrt {\langle \mathbf {v} ,\mathbf {v} \rangle }}.$ Vector spaces endowed with such data are known as *normed vector spaces* and *inner product spaces*, respectively.

Coordinate space $F^{n}$ can be equipped with the standard [dot product](https://en.wikipedia.org/wiki/Dot_product): 

$$
\langle \mathbf {x} ,\mathbf {y} \rangle =\mathbf {x} \cdot \mathbf {y} =x_{1}y_{1}+\cdots +x_{n}y_{n}.
$$

 In $\mathbf {R} ^{2},$ this reflects the common notion of the angle between two vectors $\mathbf {x}$ and $\mathbf {y} ,$ by the [law of cosines](https://en.wikipedia.org/wiki/Law_of_cosines): 

$$
\mathbf {x} \cdot \mathbf {y} =\cos \left(\angle (\mathbf {x} ,\mathbf {y} )\right)\cdot |\mathbf {x} |\cdot |\mathbf {y} |.
$$

 Because of this, two vectors satisfying $\langle \mathbf {x} ,\mathbf {y} \rangle =0$ are called [orthogonal](https://en.wikipedia.org/wiki/Orthogonal). An important variant of the standard dot product is used in [Minkowski space](https://en.wikipedia.org/wiki/Minkowski_space): $\mathbf {R} ^{4}$ endowed with the Lorentz product 

$$
\langle \mathbf {x} |\mathbf {y} \rangle =x_{1}y_{1}+x_{2}y_{2}+x_{3}y_{3}-x_{4}y_{4}.
$$

 In contrast to the standard dot product, it is not [positive definite](https://en.wikipedia.org/wiki/Positive_definite_bilinear_form): $\langle \mathbf {x} |\mathbf {x} \rangle$ also takes negative values, for example, for $\mathbf {x} =(0,0,0,1).$ Singling out the fourth coordinate—[corresponding to time](https://en.wikipedia.org/wiki/Timelike), as opposed to three space-dimensions—makes it useful for the mathematical treatment of [special relativity](https://en.wikipedia.org/wiki/Special_relativity). Note that in other conventions time is often written as the first, or "zeroeth" component so that the Lorentz product is written 

$$
\langle \mathbf {x} |\mathbf {y} \rangle =-x_{0}y_{0}+x_{1}y_{1}+x_{2}y_{2}+x_{3}y_{3}.
$$

### Topological vector spaces

Convergence questions are treated by considering vector spaces $V$ carrying a compatible [topology](https://en.wikipedia.org/wiki/Topological_space), a structure that allows one to talk about elements being [close to each other](https://en.wikipedia.org/wiki/Neighborhood_(topology)). Compatible here means that addition and scalar multiplication have to be [continuous maps](https://en.wikipedia.org/wiki/Continuous_map). Roughly, if $\mathbf {x}$ and $\mathbf {y}$ in $V$, and $a$ in $F$ vary by a bounded amount, then so do $\mathbf {x} +\mathbf {y}$ and $a\mathbf {x} .$ To make sense of specifying the amount a scalar changes, the field $F$ also has to carry a topology in this context; a common choice is the reals or the complex numbers.

In such *topological vector spaces* one can consider [series](https://en.wikipedia.org/wiki/Series_(mathematics) "Series (mathematics)") of vectors. The [infinite sum](https://en.wikipedia.org/wiki/Infinite_sum) 

$$
\sum _{i=1}^{\infty }f_{i}~=~\lim _{n\to \infty }f_{1}+\cdots +f_{n}
$$

 denotes the [limit](https://en.wikipedia.org/wiki/Limit_of_a_sequence) of the corresponding finite partial sums of the sequence $f_{1},f_{2},\ldots$ of elements of $V.$ For example, the $f_{i}$ could be (real or complex) functions belonging to some [function space](https://en.wikipedia.org/wiki/Function_space) $V,$ in which case the series is a [function series](https://en.wikipedia.org/wiki/Function_series). The [mode of convergence](https://en.wikipedia.org/wiki/Modes_of_convergence) of the series depends on the topology imposed on the function space. In such cases, [pointwise convergence](https://en.wikipedia.org/wiki/Pointwise_convergence) and [uniform convergence](https://en.wikipedia.org/wiki/Uniform_convergence) are two prominent examples.

![[media/978de4c00fb7f44fe656e65370644674af45277b.png]]
[Unit "spheres"](https://en.wikipedia.org/wiki/Unit_ball) in $\mathbf {R} ^{2}$ consist of plane vectors of norm 1. Depicted are the unit spheres in different [$p$-norms](https://en.wikipedia.org/wiki/Lp_norm), for $p=1,2,$ and $\infty .$ The bigger diamond depicts points of 1-norm equal to 2.

A way to ensure the existence of limits of certain infinite series is to restrict attention to spaces where any [Cauchy sequence](https://en.wikipedia.org/wiki/Cauchy_sequence) has a limit; such a vector space is called [complete](https://en.wikipedia.org/wiki/Completeness_(topology)). Roughly, a vector space is complete provided that it contains all necessary limits. For example, the vector space of polynomials on the unit interval $[0,1],$ equipped with the [topology of uniform convergence](https://en.wikipedia.org/wiki/Topology_of_uniform_convergence) is not complete because any continuous function on $[0,1]$ can be uniformly approximated by a sequence of polynomials, by the [Weierstrass approximation theorem](https://en.wikipedia.org/wiki/Weierstrass_approximation_theorem). In contrast, the space of *all* continuous functions on $[0,1]$ with the same topology is complete. A norm gives rise to a topology by defining that a sequence of vectors $\mathbf {v} _{n}$ converges to $\mathbf {v}$ if and only if 

$$
\lim _{n\to \infty }|\mathbf {v} _{n}-\mathbf {v} |=0.
$$

 Banach and Hilbert spaces are complete topological vector spaces whose topologies are given, respectively, by a norm and an inner product. Their study—a key piece of [functional analysis](https://en.wikipedia.org/wiki/Functional_analysis)—focuses on infinite-dimensional vector spaces, since all norms on finite-dimensional topological vector spaces give rise to the same notion of convergence. The image at the right shows the equivalence of the $1$-norm and $\infty$-norm on $\mathbf {R} ^{2}:$ as the unit "balls" enclose each other, a sequence converges to zero in one norm if and only if it so does in the other norm. In the infinite-dimensional case, however, there will generally be inequivalent topologies, which makes the study of topological vector spaces richer than that of vector spaces without additional data.

From a conceptual point of view, all notions related to topological vector spaces should match the topology. For example, instead of considering all linear maps (also called [functionals](https://en.wikipedia.org/wiki/Functional_(mathematics) "Functional (mathematics)")) $V\to W,$ maps between topological vector spaces are required to be continuous. In particular, the (topological) dual space $V^{*}$ consists of continuous functionals $V\to \mathbf {R}$ (or to $\mathbf {C}$). The fundamental [Hahn–Banach theorem](https://en.wikipedia.org/wiki/Hahn%E2%80%93Banach_theorem) is concerned with separating subspaces of appropriate topological vector spaces by continuous functionals.

#### Banach spaces

*[Banach spaces](https://en.wikipedia.org/wiki/Banach_space)*, introduced by [Stefan Banach](https://en.wikipedia.org/wiki/Stefan_Banach), are complete normed vector spaces.

A first example is [the vector space $\ell ^{p}$](https://en.wikipedia.org/wiki/Lp_space) consisting of infinite vectors with real entries $\mathbf {x} =\left(x_{1},x_{2},\ldots ,x_{n},\ldots \right)$ whose [$p$-norm](https://en.wikipedia.org/wiki/P-norm) $(1\leq p\leq \infty )$ given by 

$$
\|\mathbf {x} \|_{\infty }:=\sup _{i}|x_{i}|\qquad {\text{ for }}p=\infty ,{\text{ and }}
$$

$$
\|\mathbf {x} \|_{p}:=\left(\sum _{i}|x_{i}|^{p}\right)^{\frac {1}{p}}\qquad {\text{ for }}p<\infty .
$$

The topologies on the infinite-dimensional space $\ell ^{p}$ are inequivalent for different $p.$ For example, the sequence of vectors $\mathbf {x} _{n}=\left(2^{-n},2^{-n},\ldots ,2^{-n},0,0,\ldots \right),$ in which the first $2^{n}$ components are $2^{-n}$ and the following ones are $0,$ converges to the [zero vector](https://en.wikipedia.org/wiki/Zero_vector) for $p=\infty ,$ but does not for $p=1:$ 

$$
\|\mathbf {x} _{n}\|_{\infty }=\sup(2^{-n},0)=2^{-n}\to 0,
$$

 but 

$$
\|\mathbf {x} _{n}\|_{1}=\sum _{i=1}^{2^{n}}2^{-n}=2^{n}\cdot 2^{-n}=1.
$$

More generally than sequences of real numbers, functions $f:\Omega \to \mathbb {R}$ are endowed with a norm that replaces the above sum by the [Lebesgue integral](https://en.wikipedia.org/wiki/Lebesgue_integral) 

$$
\|f\|_{p}:=\left(\int _{\Omega }|f(x)|^{p}\,{d\mu (x)}\right)^{\frac {1}{p}}.
$$

The space of [integrable functions](https://en.wikipedia.org/wiki/Integrable_function) on a given [domain](https://en.wikipedia.org/wiki/Domain_of_a_function) $\Omega$ (for example an interval) satisfying $\|f\|_{p}<\infty ,$ and equipped with this norm are called [Lebesgue spaces](https://en.wikipedia.org/wiki/Lp_space), denoted $L^{\;\!p}(\Omega ).$

These spaces are complete. (If one uses the [Riemann integral](https://en.wikipedia.org/wiki/Riemann_integral) instead, the space is *not* complete, which may be seen as a justification for Lebesgue's integration theory.) Concretely this means that for any sequence of Lebesgue-integrable functions $f_{1},f_{2},\ldots ,f_{n},\ldots$ with $\|f_{n}\|_{p}<\infty ,$ satisfying the condition 

$$
\lim _{k,\ n\to \infty }\int _{\Omega }\left|f_{k}(x)-f_{n}(x)\right|^{p}\,{d\mu (x)}=0
$$

 there exists a function $f(x)$ belonging to the vector space $L^{\;\!p}(\Omega )$ such that 

$$
\lim _{k\to \infty }\int _{\Omega }\left|f(x)-f_{k}(x)\right|^{p}\,{d\mu (x)}=0.
$$

Imposing boundedness conditions not only on the function, but also on its [derivatives](https://en.wikipedia.org/wiki/Derivative) leads to [Sobolev spaces](https://en.wikipedia.org/wiki/Sobolev_space).

#### Hilbert spaces

![[media/518b563c28d31a573ad65ebd9bd489575bbc6e5f.gif]]
The succeeding snapshots show summation of 1 to 5 terms in approximating a periodic function (blue) by finite sum of sine functions (red).

Complete inner product spaces are known as *Hilbert spaces*, in honor of [David Hilbert](https://en.wikipedia.org/wiki/David_Hilbert). The Hilbert space $L^{2}(\Omega ),$ with inner product given by 

$$
\langle f\ ,\ g\rangle =\int _{\Omega }f(x){\overline {g(x)}}\,dx,
$$

 where ${\overline {g(x)}}$ denotes the [complex conjugate](https://en.wikipedia.org/wiki/Complex_conjugate) of $g(x),$ is a key case.

By definition, in a Hilbert space, any Cauchy sequence converges to a limit. Conversely, finding a sequence of functions $f_{n}$ with desirable properties that approximate a given limit function is equally crucial. Early analysis, in the guise of the [Taylor approximation](https://en.wikipedia.org/wiki/Taylor_approximation), established an approximation of [differentiable functions](https://en.wikipedia.org/wiki/Differentiable_function) $f$ by polynomials. By the [Stone–Weierstrass theorem](https://en.wikipedia.org/wiki/Stone%E2%80%93Weierstrass_theorem), every continuous function on $[a,b]$ can be approximated as closely as desired by a polynomial. A similar approximation technique by [trigonometric functions](https://en.wikipedia.org/wiki/Trigonometric_function) is commonly called [Fourier expansion](https://en.wikipedia.org/wiki/Fourier_expansion), and is much applied in engineering. More generally, and more conceptually, the theorem yields a simple description of what "basic functions", or, in abstract Hilbert spaces, what basic vectors suffice to generate a Hilbert space $H,$ in the sense that the *[closure](https://en.wikipedia.org/wiki/Closure_(topology) "Closure (topology)")* of their span (that is, finite linear combinations and limits of those) is the whole space. Such a set of functions is called a *basis* of $H,$ its cardinality is known as the [Hilbert space dimension](https://en.wikipedia.org/wiki/Hilbert_space_dimension). Not only does the theorem exhibit suitable basis functions as sufficient for approximation purposes, but also together with the [Gram–Schmidt process](https://en.wikipedia.org/wiki/Gram%E2%80%93Schmidt_process), it enables one to construct a [basis of orthogonal vectors](https://en.wikipedia.org/wiki/Orthogonal_basis). Such orthogonal bases are the Hilbert space generalization of the coordinate axes in finite-dimensional [Euclidean space](https://en.wikipedia.org/wiki/Euclidean_space).

The solutions to various [differential equations](https://en.wikipedia.org/wiki/Differential_equation) can be interpreted in terms of Hilbert spaces. For example, a great many fields in physics and engineering lead to such equations, and frequently solutions with particular physical properties are used as basis functions, often orthogonal. As an example from physics, the time-dependent [Schrödinger equation](https://en.wikipedia.org/wiki/Schr%C3%B6dinger_equation) in [quantum mechanics](https://en.wikipedia.org/wiki/Quantum_mechanics) describes the change of physical properties in time by means of a [partial differential equation](https://en.wikipedia.org/wiki/Partial_differential_equation), whose solutions are called [wavefunctions](https://en.wikipedia.org/wiki/Wavefunction). Definite values for physical properties such as energy, or momentum, correspond to [eigenvalues](https://en.wikipedia.org/wiki/Eigenvalue) of a certain (linear) [differential operator](https://en.wikipedia.org/wiki/Differential_operator) and the associated wavefunctions are called [eigenstates](https://en.wikipedia.org/wiki/Eigenstate). The [[Spectral Theorem]] decomposes a linear [compact operator](https://en.wikipedia.org/wiki/Compact_operator) acting on functions in terms of these eigenfunctions and their eigenvalues.

### Algebras over fields

![[media/4f5cb4c2b0ffe7c71d1c566b3f3ba0d066e0b5e3.png]]
A [hyperbola](https://en.wikipedia.org/wiki/Hyperbola), given by the equation $x\cdot y=1.$ The [coordinate ring](https://en.wikipedia.org/wiki/Coordinate_ring) of functions on this hyperbola is given by $\mathbf {R} [x,y]/(x\cdot y-1),$ an infinite-dimensional vector space over $\mathbf {R} .$

General vector spaces do not possess a multiplication between vectors. A vector space equipped with an additional [bilinear operator](https://en.wikipedia.org/wiki/Bilinear_operator) defining the multiplication of two vectors is an *algebra over a field* (or *F*-algebra if the field *F* is specified).

For example, the set of all [polynomials](https://en.wikipedia.org/wiki/Polynomial) $p(t)$ forms an algebra known as the [polynomial ring](https://en.wikipedia.org/wiki/Polynomial_ring): using that the sum of two polynomials is a polynomial, they form a vector space; they form an algebra since the product of two polynomials is again a polynomial. Rings of polynomials (in several variables) and their [quotients](https://en.wikipedia.org/wiki/Quotient_ring) form the basis of [algebraic geometry](https://en.wikipedia.org/wiki/Algebraic_geometry), because they are [rings of functions of algebraic geometric objects](https://en.wikipedia.org/wiki/Coordinate_ring).

Another crucial example are *[Lie algebras](https://en.wikipedia.org/wiki/Lie_algebra)*, which are neither commutative nor associative, but the failure to be so is limited by the constraints ($[x,y]$ denotes the product of $x$ and $y$):

- $[x,y]=-[y,x]$ ([anticommutativity](https://en.wikipedia.org/wiki/Anticommutativity)), and
- $[x,[y,z]]+[y,[z,x]]+[z,[x,y]]=0$ ([Jacobi identity](https://en.wikipedia.org/wiki/Jacobi_identity)).

Examples include the vector space of $n$-by-$n$ matrices, with $[x,y]=xy-yx,$ the [commutator](https://en.wikipedia.org/wiki/Commutator) of two matrices, and $\mathbf {R} ^{3},$ endowed with the [cross product](https://en.wikipedia.org/wiki/Cross_product).

The [tensor algebra](https://en.wikipedia.org/wiki/Tensor_algebra) $\operatorname {T} (V)$ is a formal way of adding products to any vector space $V$ to obtain an algebra. As a vector space, it is spanned by symbols, called simple [tensors](https://en.wikipedia.org/wiki/Tensor) 

$$
\mathbf {v} _{1}\otimes \mathbf {v} _{2}\otimes \cdots \otimes \mathbf {v} _{n},
$$

 where the [degree](https://en.wikipedia.org/wiki/Rank_of_a_tensor) $n$ varies. The multiplication is given by concatenating such symbols, imposing the [distributive law](https://en.wikipedia.org/wiki/Distributive_law) under addition, and requiring that scalar multiplication commute with the tensor product ⊗, much the same way as with the tensor product of two vector spaces introduced in the above section on [tensor products](#Tensor_product). In general, there are no relations between $\mathbf {v} _{1}\otimes \mathbf {v} _{2}$ and $\mathbf {v} _{2}\otimes \mathbf {v} _{1}.$ Forcing two such elements to be equal leads to the [symmetric algebra](https://en.wikipedia.org/wiki/Symmetric_algebra), whereas forcing $\mathbf {v} _{1}\otimes \mathbf {v} _{2}=-\mathbf {v} _{2}\otimes \mathbf {v} _{1}$ yields the [exterior algebra](https://en.wikipedia.org/wiki/Exterior_algebra).

## Related structures

### Vector bundles

![[media/db96f1fa9737ffbf1c663c49685e8e75090f3246.png]]
A Möbius strip. Locally, it [looks like](https://en.wikipedia.org/wiki/Homeomorphism) <em>U</em> × <strong>R</strong>.

A *vector bundle* is a family of vector spaces parametrized continuously by a [topological space](https://en.wikipedia.org/wiki/Topological_space) *X*. More precisely, a vector bundle over *X* is a topological space *E* equipped with a continuous map 

$$
\pi :E\to X
$$

 such that for every *x* in *X*, the [fiber](https://en.wikipedia.org/wiki/Fiber_(mathematics) "Fiber (mathematics)") π<sup>−1</sup>(*x*) is a vector space. The case dim *V* = 1 is called a [line bundle](https://en.wikipedia.org/wiki/Line_bundle). For any vector space *V*, the projection *X* × *V* → *X* makes the product *X* × *V* into a ["trivial" vector bundle](https://en.wikipedia.org/wiki/Trivial_bundle). Vector bundles over *X* are required to be [locally](https://en.wikipedia.org/wiki/Locally) a product of *X* and some (fixed) vector space *V*: for every *x* in *X*, there is a [neighborhood](https://en.wikipedia.org/wiki/Neighborhood_(topology)) *U* of *x* such that the restriction of π to π<sup>−1</sup>(*U*) is isomorphic to the trivial bundle *U* × *V* → *U*. Despite their locally trivial character, vector bundles may (depending on the shape of the underlying space *X*) be "twisted" in the large (that is, the bundle need not be (globally isomorphic to) the trivial bundle *X* × *V*). For example, the [Möbius strip](https://en.wikipedia.org/wiki/M%C3%B6bius_strip) can be seen as a line bundle over the circle *S*<sup>1</sup> (by [identifying open intervals with the real line](https://en.wikipedia.org/wiki/Homeomorphism#Examples)). It is, however, different from the [cylinder](https://en.wikipedia.org/wiki/Cylinder_(geometry)) *S*<sup>1</sup> × **R**, because the latter is [orientable](https://en.wikipedia.org/wiki/Orientable_manifold) whereas the former is not.

Properties of certain vector bundles provide information about the underlying topological space. For example, the [tangent bundle](https://en.wikipedia.org/wiki/Tangent_bundle) consists of the collection of [[Tangent Space|tangent spaces]] parametrized by the points of a differentiable manifold. The tangent bundle of the circle *S*<sup>1</sup> is globally isomorphic to *S*<sup>1</sup> × **R**, since there is a global nonzero [vector field](https://en.wikipedia.org/wiki/Vector_field) on *S*<sup>1</sup>. In contrast, by the [hairy ball theorem](https://en.wikipedia.org/wiki/Hairy_ball_theorem), there is no (tangent) vector field on the [2-sphere](https://en.wikipedia.org/wiki/2-sphere) *S*<sup>2</sup> which is everywhere nonzero. [K-theory](https://en.wikipedia.org/wiki/K-theory) studies the isomorphism classes of all vector bundles over some topological space. In addition to deepening topological and geometrical insight, it has purely algebraic consequences, such as the classification of finite-dimensional real [division algebras](https://en.wikipedia.org/wiki/Division_algebra): **R**, **C**, the [quaternions](https://en.wikipedia.org/wiki/Quaternion) **H** and the [octonions](https://en.wikipedia.org/wiki/Octonion) **O**.

The [cotangent bundle](https://en.wikipedia.org/wiki/Cotangent_bundle) of a differentiable manifold consists, at every point of the manifold, of the dual of the tangent space, the [cotangent space](https://en.wikipedia.org/wiki/Cotangent_space). [Sections](https://en.wikipedia.org/wiki/Section_(fiber_bundle) "Section (fiber bundle)") of that bundle are known as [differential one-forms](https://en.wikipedia.org/wiki/Differential_form).

### Modules

*Modules* are to [rings](https://en.wikipedia.org/wiki/Ring_(mathematics) "Ring (mathematics)") what vector spaces are to fields: the same axioms, applied to a ring *R* instead of a field *F*, yield modules. The theory of modules, compared to that of vector spaces, is complicated by the presence of ring elements that do not have [multiplicative inverses](https://en.wikipedia.org/wiki/Multiplicative_inverse). For example, modules need not have bases, as the **Z**-module (that is, [abelian group](https://en.wikipedia.org/wiki/Abelian_group)) [**Z**/2**Z**](https://en.wikipedia.org/wiki/Modular_arithmetic) shows; those modules that do (including all vector spaces) are known as [free modules](https://en.wikipedia.org/wiki/Free_module). Nevertheless, a vector space can be compactly defined as a [module](https://en.wikipedia.org/wiki/Module_(mathematics) "Module (mathematics)") over a [ring](https://en.wikipedia.org/wiki/Ring_(mathematics) "Ring (mathematics)") which is a [field](https://en.wikipedia.org/wiki/Field_(mathematics) "Field (mathematics)"), with the elements being called vectors. Some authors use the term *vector space* to mean modules over a [division ring](https://en.wikipedia.org/wiki/Division_ring). The algebro-geometric interpretation of commutative rings via their [spectrum](https://en.wikipedia.org/wiki/Spectrum_of_a_ring) allows the development of concepts such as [locally free modules](https://en.wikipedia.org/wiki/Locally_free_module), the algebraic counterpart to vector bundles.

### Affine and projective spaces

![[media/bab961e01dd7f24d565c64260b485696412d304e.png]]
An [affine plane](https://en.wikipedia.org/wiki/Affine_space) (light blue) in <strong>R</strong><sup>3</sup>. It is a two-dimensional subspace shifted by a vector <strong>x</strong> (red).

Roughly, *affine spaces* are vector spaces whose origins are not specified. More precisely, an affine space is a set with a [free transitive](https://en.wikipedia.org/wiki/Transitive_group_action) vector space [action](https://en.wikipedia.org/wiki/Group_action_(mathematics)). In particular, a vector space is an affine space over itself, by the map 

$$
V\times V\to W,\;(\mathbf {v} ,\mathbf {a} )\mapsto \mathbf {a} +\mathbf {v} .
$$

 If *W* is a vector space, then an affine subspace is a subset of *W* obtained by translating a linear subspace *V* by a fixed vector **x** ∈ *W*; this space is denoted by **x** + *V* (it is a [coset](https://en.wikipedia.org/wiki/Coset) of *V* in *W*) and consists of all vectors of the form **x** + **v** for **v** ∈ *V*. An important example is the space of solutions of a system of inhomogeneous linear equations 

$$
A\mathbf {v} =\mathbf {b}
$$

 generalizing the homogeneous case discussed in the [above section](#equation3) on linear equations, which can be found by setting $\mathbf {b} =\mathbf {0}$ in this equation. The space of solutions is the affine subspace **x** + *V* where **x** is a particular solution of the equation, and *V* is the space of solutions of the homogeneous equation (the [nullspace](https://en.wikipedia.org/wiki/Nullspace) of *A*).

The set of one-dimensional subspaces of a fixed finite-dimensional vector space *V* is known as *projective space*; it may be used to formalize the idea of [parallel](https://en.wikipedia.org/wiki/Parallel_(geometry) "Parallel (geometry)") lines intersecting at infinity. [Grassmannians](https://en.wikipedia.org/wiki/Grassmannian_manifold) and [flag manifolds](https://en.wikipedia.org/wiki/Flag_manifold) generalize this by parametrizing linear subspaces of fixed dimension *k* and [flags](https://en.wikipedia.org/wiki/Flag_(linear_algebra) "Flag (linear algebra)") of subspaces, respectively.

## Notes

1.  It is also common, especially in physics, to denote vectors with an arrow on top: ${\vec {v}}.$ It is also common, especially in higher mathematics, to not use any typographical method for distinguishing vectors from other mathematical objects.
2.  Scalar multiplication is not to be confused with the [scalar product](https://en.wikipedia.org/wiki/Scalar_product), which is an additional operation on some specific vector spaces, called [inner product spaces](https://en.wikipedia.org/wiki/Inner_product_space). Scalar multiplication is the multiplication of a vector *by* a scalar that produces a vector, while the scalar product is a multiplication of two vectors that produces a scalar.
3.  This axiom is not an [associative property](https://en.wikipedia.org/wiki/Associative_property), since it refers to two different operations, scalar multiplication and field multiplication. So, it is independent from the associativity of field multiplication, which is assumed by field axioms.
4.  This is typically the case when a vector space is also considered as an [affine space](https://en.wikipedia.org/wiki/Affine_space). In this case, a linear subspace contains the [zero vector](https://en.wikipedia.org/wiki/Zero_vector), while an affine subspace does not necessarily contain it.
5.  Some authors, such as , choose to start with this [equivalence relation](https://en.wikipedia.org/wiki/Equivalence_relation) and derive the concrete shape of $V/W$ from this.
6.  This requirement implies that the topology gives rise to a [uniform structure](https://en.wikipedia.org/wiki/Uniform_structure), , loc = ch. II.
7.  The [triangle inequality](https://en.wikipedia.org/wiki/Triangle_inequality) for $\|f+g\|_{p}\leq \|f\|_{p}+\|g\|_{p}$ is provided by the [Minkowski inequality](https://en.wikipedia.org/wiki/Minkowski_inequality). For technical reasons, in the context of functions one has to identify functions that agree [almost everywhere](https://en.wikipedia.org/wiki/Almost_everywhere) to get a norm, and not only a [seminorm](https://en.wikipedia.org/wiki/Seminorm).
8.  "Many functions in $L^{2}$ of Lebesgue measure, being unbounded, cannot be integrated with the classical Riemann integral. So spaces of Riemann integrable functions would not be complete in the $L^{2}$ norm, and the orthogonal decomposition would not apply to them. This shows one of the advantages of Lebesgue integration.", , §5.3, p. 125.
9.  For $p\neq 2,$ $L^{p}(\Omega )$ is not a Hilbert space.
10. A basis of a Hilbert space is not the same thing as a basis of a linear algebra. For distinction, a linear algebra basis for a Hilbert space is called a [Hamel basis](https://en.wikipedia.org/wiki/Hamel_basis).
11. That is, there is a [homeomorphism](https://en.wikipedia.org/wiki/Homeomorphism) from π<sup>−1</sup>(*U*) to *V* × *U* which restricts to linear isomorphisms between fibers.
12. A line bundle, such as the tangent bundle of *S*<sup>1</sup> is trivial if and only if there is a [section](https://en.wikipedia.org/wiki/Section_(fiber_bundle) "Section (fiber bundle)") that vanishes nowhere, see , Corollary 8.3. The sections of the tangent bundle are just [vector fields](https://en.wikipedia.org/wiki/Vector_field).

## Citations

1.  .
2.  , p. 86.
3.  , ch. 1, p. 27.
4.  , p. 87.
5.  , p. [185](https://books.google.com/books?id=Ces-AAAAQBAJ&pg=PA185); , p. 86.
6.  , p. 17.
7.  , §1.1, Definition 2.
8.  , p. 94.
9.  , pp. 99–101.
10. , p. 92.
11. ^   , p. [14](https://books.google.com/books?id=gLbiBQAAQBAJ&pg=PA14).
12. , pp. 41–42.
13. , p. 10–11; , p. [212](https://books.google.com/books?id=1PJ-WHepeBsC&pg=PA212).
14. .
15. , p. [450](https://books.google.com/books?id=RM1D3mFw2u0C&pg=PA450).
16. , p. [126](https://books.google.com/books?id=prfuUT0Sw-AC&pg=PA126).
17. , p. [12](https://books.google.com/books?id=1hzYCwAAQBAJ&pg=PA12).
18. , ch. "Algèbre linéaire et algèbre multilinéaire", pp. 78–91.
19. .
20. .
21. .
22. .
23. .
24. .
25. , ch. IX.
26. .
27. , pp. 268–271.
28. .
29. ; .
30. , p. [355](https://books.google.com/books?id=w4T3DwAAQBAJ&pg=PA355).
31. , p. [358–359](https://books.google.com/books?id=w4T3DwAAQBAJ&pg=PA358).
32. , p. [11](https://books.google.com/books?id=-lzAee3uQtIC&pg=PA11).
33. , ch. I.1.
34. , ch. V.1.
35. , ch. XII.3., p. 335.
36. , ch. VI.3..
37. , ch. 2, p. 45.
38. , ch. IV.4, Corollary, p. 106.
39. , ch. 7.3.
40. , Example IV.2.6.
41. , ch. VI.6.
42. , p. 28, Ex. 9.
43. , Theorem IV.2.1, p. 95.
44. , Th. 2.5 and 2.6, p. 49.
45. , ch. V.1.
46. , ch. V.3., Corollary, p. 106.
47. , Theorem VII.9.8, p. 198.
48. , ch. 8, p. 135–156.
49. , ch. IX.4.
50. , ch. 8, p. 140.
51. , ch. 1, p. 29.
52. , ch. 1, p. 35.
53. , ch. 10.4.
54. , ch. 3, p. 64.
55. , ch. IV.3..
56. , ch. 2, p. 48.
57. , ch. 7.4.
58. .
59. , ch. 1, pp. 31–32.
60. , ch. XVI.1.
61. , Th. 14.3. See also [Yoneda lemma](https://en.wikipedia.org/wiki/Yoneda_lemma).
62. , p.3.
63. , pp. 204–205.
64. , ch. 2, p. 48.
65. , ch. 9.
66. , ch. 1.2.
67. ; .
68. , p. 7.
69. , §4.11-5
70. , §1.5-5
71. , Proposition III.7.2.
72. , p. 34–36.
73. , Cor. 4.1.2, p. 69.
74. , ch. 11.
75. , Theorem 11.2, p. 102.
76. , ch. 5.
77. , ch. 12.
78. , p.190.
79. , Th. XIII.6, p. 349.
80. , Th. III.1.1.
81. , Lemma III.16.11.
82. , Chapter 11.
83. , Chapter 1.
84. , ch. XVII.3.
85. , ch. III.1, p. 121.
86. , ch. 1.6.
87. .
88. , ch. XVI.7.
89. , ch. XVI.8.
90. , ch. 3.
91. , §34, p. 108.
92. .
93. .
94. , ch. 12.
95. .
96. , Example 5.13.5, p. 436.
97. , Exercise 5.13.15–17, p. 442.
98. .

## References

### Algebra

- Anton, Howard; Rorres, Chris (2010), *Elementary Linear Algebra: Applications Version* (10th ed.), John Wiley & Sons
- [Artin, Michael](https://en.wikipedia.org/wiki/Michael_Artin) (1991), *Algebra*, [Prentice Hall](https://en.wikipedia.org/wiki/Prentice_Hall), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-89871-510-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-89871-510-1)
- Brown, William A. (1991), [Matrices and vector spaces](https://archive.org/details/matricesvectorsp0000brow), New York: M. Dekker, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8247-8419-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8247-8419-5)
- Grillet, Pierre Antoine (2007), *Abstract algebra*, Graduate Texts in Mathematics, vol. 242, Springer Science & Business Media, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-0-387-71568-1](https://doi.org/10.1007%2F978-0-387-71568-1), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-71568-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-71568-1)
- [Halmos, Paul R.](https://en.wikipedia.org/wiki/Paul_R._Halmos) (1948), *Finite Dimensional Vector Spaces*, vol. 7, Princeton University Press
- Heil, Christopher (2011), *A Basis Theory Primer: Expanded Edition*, Applied and Numerical Harmonic Analysis, Birkhäuser, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-0-8176-4687-5](https://doi.org/10.1007%2F978-0-8176-4687-5), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8176-4687-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8176-4687-5)
- Jain, M. C. (2001), [Vector Spaces and Matrices in Physics](https://books.google.com/books?id=-lzAee3uQtIC), CRC Press, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8493-0978-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8493-0978-6)
- Joshi, K. D. (1989), *Foundations of Discrete Mathematics*, John Wiley & Sons
- Kreyszig, Erwin (2020), [Advanced Engineering Mathematics](https://books.google.com/books?id=w4T3DwAAQBAJ), John Wiley & Sons, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-119-45592-9](https://en.wikipedia.org/wiki/Special:BookSources/978-1-119-45592-9)
- Lang, Serge (1987), *Linear algebra*, Undergraduate Texts in Mathematics (3rd ed.), Springer, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-1-4757-1949-9](https://doi.org/10.1007%2F978-1-4757-1949-9), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4757-1949-9](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4757-1949-9)
- [Lang, Serge](https://en.wikipedia.org/wiki/Serge_Lang) (2002), *[Algebra](https://en.wikipedia.org/wiki/Algebra_(Lang))*, [Graduate Texts in Mathematics](https://en.wikipedia.org/wiki/Graduate_Texts_in_Mathematics), vol. 211 (Revised third ed.), New York: Springer-Verlag, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-95385-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-95385-4), [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1878556](https://mathscinet.ams.org/mathscinet-getitem?mr=1878556)
- [Mac Lane, Saunders](https://en.wikipedia.org/wiki/Saunders_Mac_Lane) (1999), *Algebra* (3rd ed.), American Mathematical Soc., pp. 193–222, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8218-1646-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8218-1646-2)
- Meyer, Carl D. (2000), [Matrix Analysis and Applied Linear Algebra](http://www.matrixanalysis.com/), [SIAM](https://en.wikipedia.org/wiki/Society_for_Industrial_and_Applied_Mathematics), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-89871-454-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-89871-454-8)
- Nicholson, W. Keith (2018), ["Linear Algebra with Applications"](https://lyryx.com/linear-algebra-applications/), *Lyryx*
- [Roman, Steven](https://en.wikipedia.org/wiki/Steven_Roman) (2005), *Advanced Linear Algebra*, Graduate Texts in Mathematics, vol. 135 (2nd ed.), Berlin, New York: [Springer-Verlag](https://en.wikipedia.org/wiki/Springer-Verlag), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-24766-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-24766-3)
- Spindler, Karlheinz (1993), *Abstract Algebra with Applications: Volume 1: Vector spaces and groups*, CRC, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8247-9144-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8247-9144-5)
- Springer, T.A. (2000), [Linear Algebraic Groups](https://books.google.com/books?id=Ces-AAAAQBAJ), Springer, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8176-4840-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8176-4840-4)
- Stoll, R. R.; Wong, E. T. (1968), *Linear Algebra*, Academic Press
- [van der Waerden, Bartel Leendert](https://en.wikipedia.org/wiki/Bartel_Leendert_van_der_Waerden) (1993), *Algebra* (in German) (9th ed.), Berlin, New York: [Springer-Verlag](https://en.wikipedia.org/wiki/Springer-Verlag), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-56799-8](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-56799-8)

### Analysis

- [Bourbaki, Nicolas](https://en.wikipedia.org/wiki/Nicolas_Bourbaki) (1987), *Topological vector spaces*, Elements of mathematics, Berlin, New York: [Springer-Verlag](https://en.wikipedia.org/wiki/Springer-Verlag), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-13627-9](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-13627-9)
- [Bourbaki, Nicolas](https://en.wikipedia.org/wiki/Nicolas_Bourbaki) (2004), *Integration I*, Berlin, New York: [Springer-Verlag](https://en.wikipedia.org/wiki/Springer-Verlag), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-41129-1](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-41129-1)
- Braun, Martin (1993), *Differential equations and their applications: an introduction to applied mathematics*, Berlin, New York: [Springer-Verlag](https://en.wikipedia.org/wiki/Springer-Verlag), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-97894-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-97894-9)
- BSE-3 (2001) \[1994\], ["Tangent plane"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society)
- [Choquet, Gustave](https://en.wikipedia.org/wiki/Gustave_Choquet) (1966), *Topology*, Boston, MA: [Academic Press](https://en.wikipedia.org/wiki/Academic_Press)
- Dennery, Philippe; Krzywicki, Andre (1996), *Mathematics for Physicists*, Courier Dover Publications, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-486-69193-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-486-69193-0)
- Dudley, Richard M. (1989), *Real analysis and probability*, The Wadsworth & Brooks/Cole Mathematics Series, Pacific Grove, CA: Wadsworth & Brooks/Cole Advanced Books & Software, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-534-10050-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-534-10050-6)
- Dunham, William (2005), *The Calculus Gallery*, [Princeton University Press](https://en.wikipedia.org/wiki/Princeton_University_Press), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-691-09565-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-691-09565-3)
- [Evans, Lawrence C.](https://en.wikipedia.org/wiki/Lawrence_C._Evans) (1998), *Partial differential equations*, Providence, R.I.: [American Mathematical Society](https://en.wikipedia.org/wiki/American_Mathematical_Society), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8218-0772-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8218-0772-9)
- Folland, Gerald B. (1992), *Fourier Analysis and Its Applications*, Brooks-Cole, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-534-17094-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-534-17094-3)
- Gasquet, Claude; Witomski, Patrick (1999), *Fourier Analysis and Applications: Filtering, Numerical Computation, Wavelets*, Texts in Applied Mathematics, New York: Springer-Verlag, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-98485-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-98485-8)
- Ifeachor, Emmanuel C.; Jervis, Barrie W. (2001), *Digital Signal Processing: A Practical Approach* (2nd ed.), Harlow, Essex, England: Prentice-Hall (published 2002), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-201-59619-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-201-59619-9)
- Krantz, Steven G. (1999), *A Panorama of Harmonic Analysis*, Carus Mathematical Monographs, Washington, DC: Mathematical Association of America, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-88385-031-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-88385-031-2)
- [Kreyszig, Erwin](https://en.wikipedia.org/wiki/Erwin_Kreyszig) (1988), *Advanced Engineering Mathematics* (6th ed.), New York: John Wiley & Sons, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-85824-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-85824-9)
- [Kreyszig, Erwin](https://en.wikipedia.org/wiki/Erwin_Kreyszig) (1989), *Introductory functional analysis with applications*, Wiley Classics Library, New York: [John Wiley & Sons](https://en.wikipedia.org/wiki/John_Wiley_%26_Sons), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-50459-7](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-50459-7), [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0992618](https://mathscinet.ams.org/mathscinet-getitem?mr=0992618)
- [Lang, Serge](https://en.wikipedia.org/wiki/Serge_Lang) (1983), *Real analysis*, [Addison-Wesley](https://en.wikipedia.org/wiki/Addison-Wesley), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-201-14179-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-201-14179-5)
- [Lang, Serge](https://en.wikipedia.org/wiki/Serge_Lang) (1993), *Real and functional analysis*, Berlin, New York: [Springer-Verlag](https://en.wikipedia.org/wiki/Springer-Verlag), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-94001-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-94001-4)
- Loomis, Lynn H. (2011) \[1953\], *An introduction to abstract harmonic analysis*, Dover, [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[2027/uc1.b4250788](https://hdl.handle.net/2027%2Fuc1.b4250788), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-486-48123-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-486-48123-4), [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [702357363](https://search.worldcat.org/oclc/702357363)
- Narici, Lawrence; Beckenstein, Edward (2011). *Topological Vector Spaces*. Pure and applied mathematics (Second ed.). Boca Raton, FL: CRC Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1584888666](https://en.wikipedia.org/wiki/Special:BookSources/978-1584888666). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [144216834](https://search.worldcat.org/oclc/144216834).
- Rudin, Walter (1991), *Functional analysis* (2 ed.), McGraw-Hill, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0070542368](https://en.wikipedia.org/wiki/Special:BookSources/0070542368)
- [Schaefer, Helmut H.](https://en.wikipedia.org/wiki/Helmut_H._Schaefer); Wolff, Manfred P. (1999). *Topological Vector Spaces*. [GTM](https://en.wikipedia.org/wiki/Graduate_Texts_in_Mathematics). Vol. 8 (Second ed.). New York, NY: Springer New York Imprint Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4612-7155-0](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4612-7155-0). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [840278135](https://search.worldcat.org/oclc/840278135).
- [Treves, François](https://en.wikipedia.org/wiki/Fran%C3%A7ois_Tr%C3%A8ves) (1967), *Topological vector spaces, distributions and kernels*, Boston, MA: [Academic Press](https://en.wikipedia.org/wiki/Academic_Press)

### Historical references

- [Banach, Stefan](https://en.wikipedia.org/wiki/Stefan_Banach) (1922), ["Sur les opérations dans les ensembles abstraits et leur application aux équations intégrales (On operations in abstract sets and their application to integral equations)"](http://matwbn.icm.edu.pl/ksiazki/fm/fm3/fm3120.pdf) (PDF), *[Fundamenta Mathematicae](https://en.wikipedia.org/wiki/Fundamenta_Mathematicae)* (in French), **3**: 133–181, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.4064/fm-3-1-133-181](https://doi.org/10.4064%2Ffm-3-1-133-181), [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0016-2736](https://search.worldcat.org/issn/0016-2736)
- [Bolzano, Bernard](https://en.wikipedia.org/wiki/Bernard_Bolzano) (1804), [Betrachtungen über einige Gegenstände der Elementargeometrie (Considerations of some aspects of elementary geometry)](http://dml.cz/handle/10338.dmlcz/400338) (in German)
- [Bellavitis, Giuso](https://en.wikipedia.org/wiki/Giusto_Bellavitis) (1833), "Sopra alcune applicazioni di un nuovo metodo di geometria analitica", *Il poligrafo giornale di scienze, lettre ed arti*, **13**, Verona: 53–61.
- [Bourbaki, Nicolas](https://en.wikipedia.org/wiki/Nicolas_Bourbaki) (1969), *Éléments d'histoire des mathématiques (Elements of history of mathematics)* (in French), Paris: Hermann
- Dorier, Jean-Luc (1995), ["A general outline of the genesis of vector space theory"](http://archive-ouverte.unige.ch/unige:16642), *[Historia Mathematica](https://en.wikipedia.org/wiki/Historia_Mathematica)*, **22** (3): 227–261, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1006/hmat.1995.1024](https://doi.org/10.1006%2Fhmat.1995.1024), [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1347828](https://mathscinet.ams.org/mathscinet-getitem?mr=1347828)
- [Fourier, Jean Baptiste Joseph](https://en.wikipedia.org/wiki/Joseph_Fourier) (1822), [Théorie analytique de la chaleur](https://books.google.com/books?id=TDQJAAAAIAAJ) (in French), Chez Firmin Didot, père et fils
- [Grassmann, Hermann](https://en.wikipedia.org/wiki/Hermann_Grassmann) (1844), [Die Lineale Ausdehnungslehre - Ein neuer Zweig der Mathematik](https://books.google.com/books?id=bKgAAAAAMAAJ&pg=PA1) (in German), O. Wigand, reprint: Grassmann, Hermann (2000), Kannenberg, L.C. (ed.), *Extension Theory*, translated by Kannenberg, Lloyd C., Providence, R.I.: [American Mathematical Society](https://en.wikipedia.org/wiki/American_Mathematical_Society), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8218-2031-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8218-2031-5)
- Guo, Hongyu (2021-06-16), [What Are Tensors Exactly?](https://books.google.com/books?id=5dM3EAAAQBAJ), World Scientific, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-981-12-4103-1](https://en.wikipedia.org/wiki/Special:BookSources/978-981-12-4103-1)
- [Hamilton, William Rowan](https://en.wikipedia.org/wiki/William_Rowan_Hamilton) (1853), [Lectures on Quaternions](https://historical.library.cornell.edu/cgi-bin/cul.math/docviewer?did=05230001&seq=9), Royal Irish Academy
- [Möbius, August Ferdinand](https://en.wikipedia.org/wiki/August_Ferdinand_M%C3%B6bius) (1827), [Der Barycentrische Calcul : ein neues Hülfsmittel zur analytischen Behandlung der Geometrie (Barycentric calculus: a new utility for an analytic treatment of geometry)](https://web.archive.org/web/20061123192612/http://mathdoc.emath.fr/cgi-bin/oeitem?id=OE_MOBIUS__1_1_0) (in German), archived from [the original](http://mathdoc.emath.fr/cgi-bin/oeitem?id=OE_MOBIUS__1_1_0) on 2006-11-23
- Moore, Gregory H. (1995), "The axiomatization of linear algebra: 1875–1940", *[Historia Mathematica](https://en.wikipedia.org/wiki/Historia_Mathematica)*, **22** (3): 262–303, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1006/hmat.1995.1025](https://doi.org/10.1006%2Fhmat.1995.1025)
- [Peano, Giuseppe](https://en.wikipedia.org/wiki/Giuseppe_Peano) (1888), *Calcolo Geometrico secondo l'Ausdehnungslehre di H. Grassmann preceduto dalle Operazioni della Logica Deduttiva* (in Italian), Turin`{{`[`citation`](https://en.wikipedia.org/wiki/Template:Citation)`}}`: CS1 maint: location missing publisher ([link](https://en.wikipedia.org/wiki/Category:CS1_maint:_location_missing_publisher))
- Peano, G. (1901) [Formulario mathematico](https://en.wikipedia.org/wiki/Formulario_mathematico): [vct axioms](https://archive.org/details/formulairedesmat00pean/page/194) via [Internet Archive](https://en.wikipedia.org/wiki/Internet_Archive)

### Further references

- [Ashcroft, Neil](https://en.wikipedia.org/wiki/Neil_Ashcroft); [Mermin, N. David](https://en.wikipedia.org/wiki/N._David_Mermin) (1976), [Solid State Physics](https://archive.org/details/solidstatephysic00ashc), Toronto: Thomson Learning, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-03-083993-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-03-083993-1)
- [Atiyah, Michael Francis](https://en.wikipedia.org/wiki/Michael_Atiyah) (1989), *K-theory*, Advanced Book Classics (2nd ed.), [Addison-Wesley](https://en.wikipedia.org/wiki/Addison-Wesley), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-201-09394-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-201-09394-0), [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1043170](https://mathscinet.ams.org/mathscinet-getitem?mr=1043170)
- [Atiyah, Michael Francis](https://en.wikipedia.org/wiki/Michael_Atiyah); [Macdonald, Ian Grant](https://en.wikipedia.org/wiki/Ian_G._Macdonald) (1969), *Introduction to Commutative Algebra*, Advanced Book Classics, [Addison-Wesley](https://en.wikipedia.org/wiki/Addison-Wesley)
- Blass, Andreas (1984), ["Existence of bases implies the axiom of choice"](http://www.math.lsa.umich.edu/~ablass/bases-AC.pdf) (PDF), *Axiomatic set theory*, Contemporary Mathematics volume 31, Providence, R.I.: [American Mathematical Society](https://en.wikipedia.org/wiki/American_Mathematical_Society), pp. 31–33, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8218-5026-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8218-5026-8), [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0763890](https://mathscinet.ams.org/mathscinet-getitem?mr=0763890)
- [Bourbaki, Nicolas](https://en.wikipedia.org/wiki/Nicolas_Bourbaki) (1998), *Elements of Mathematics : Algebra I Chapters 1-3*, Berlin, New York: [Springer-Verlag](https://en.wikipedia.org/wiki/Springer-Verlag), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-64243-5](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-64243-5)
- [Bourbaki, Nicolas](https://en.wikipedia.org/wiki/Nicolas_Bourbaki) (1989), *General Topology. Chapters 1-4*, Berlin, New York: [Springer-Verlag](https://en.wikipedia.org/wiki/Springer-Verlag), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-64241-1](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-64241-1)
- [Coxeter, Harold Scott MacDonald](https://en.wikipedia.org/wiki/Harold_Scott_MacDonald_Coxeter) (1987), *Projective Geometry* (2nd ed.), Berlin, New York: [Springer-Verlag](https://en.wikipedia.org/wiki/Springer-Verlag), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-96532-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-96532-1)
- Eisenberg, Murray; Guy, Robert (1979), "A proof of the hairy ball theorem", *[The American Mathematical Monthly](https://en.wikipedia.org/wiki/American_Mathematical_Monthly)*, **86** (7): 572–574, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2320587](https://doi.org/10.2307%2F2320587), [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2320587](https://www.jstor.org/stable/2320587)
- [Eisenbud, David](https://en.wikipedia.org/wiki/David_Eisenbud) (1995), *Commutative algebra*, Graduate Texts in Mathematics, vol. 150, Berlin, New York: [Springer-Verlag](https://en.wikipedia.org/wiki/Springer-Verlag), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-94269-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-94269-8), [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1322960](https://mathscinet.ams.org/mathscinet-getitem?mr=1322960)
- Goldrei, Derek (1996), *Classic Set Theory: A guided independent study* (1st ed.), London: [Chapman and Hall](https://en.wikipedia.org/wiki/Chapman_and_Hall), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-412-60610-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-412-60610-6)
- [Griffiths, David J.](https://en.wikipedia.org/wiki/David_J._Griffiths) (1995), *Introduction to Quantum Mechanics*, Upper Saddle River, NJ: [Prentice Hall](https://en.wikipedia.org/wiki/Prentice_Hall), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-13-124405-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-13-124405-4)
- [Halmos, Paul R.](https://en.wikipedia.org/wiki/Paul_R._Halmos) (1974), *Finite-dimensional vector spaces*, Berlin, New York: [Springer-Verlag](https://en.wikipedia.org/wiki/Springer-Verlag), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-90093-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-90093-3)
- Halpern, James D. (Jun 1966), "Bases in Vector Spaces and the Axiom of Choice", *[Proceedings of the American Mathematical Society](https://en.wikipedia.org/wiki/Proceedings_of_the_American_Mathematical_Society)*, **17** (3): 670–673, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2035388](https://doi.org/10.2307%2F2035388), [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2035388](https://www.jstor.org/stable/2035388)
- Hughes-Hallett, Deborah; McCallum, William G.; Gleason, Andrew M. (2013), *Calculus : Single and Multivariable* (6 ed.), [John Wiley & Sons](https://en.wikipedia.org/wiki/John_Wiley_%26_Sons), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0470-88861-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0470-88861-2)
- Husemoller, Dale (1994), *Fibre Bundles* (3rd ed.), Berlin, New York: [Springer-Verlag](https://en.wikipedia.org/wiki/Springer-Verlag), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-94087-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-94087-8)
- Jost, Jürgen (2005), *Riemannian Geometry and Geometric Analysis* (4th ed.), Berlin, New York: [Springer-Verlag](https://en.wikipedia.org/wiki/Springer-Verlag), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-25907-7](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-25907-7)
- [Kreyszig, Erwin](https://en.wikipedia.org/wiki/Erwin_Kreyszig) (1991), *Differential geometry*, New York: [Dover Publications](https://en.wikipedia.org/wiki/Dover_Publications), pp. xiv+352, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-486-66721-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-486-66721-8)
- Kreyszig, Erwin (1999), [Advanced Engineering Mathematics](https://archive.org/details/advancedengineer0008krey) (8th ed.), New York: [John Wiley & Sons](https://en.wikipedia.org/wiki/John_Wiley_%26_Sons), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-15496-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-15496-9)
- Luenberger, David (1997), *Optimization by vector space methods*, New York: [John Wiley & Sons](https://en.wikipedia.org/wiki/John_Wiley_%26_Sons), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-18117-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-18117-0)
- [Mac Lane, Saunders](https://en.wikipedia.org/wiki/Saunders_Mac_Lane) (1998), [*Categories for the Working Mathematician*](https://en.wikipedia.org/wiki/Categories_for_the_Working_Mathematician) (2nd ed.), Berlin, New York: [Springer-Verlag](https://en.wikipedia.org/wiki/Springer-Verlag), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-98403-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-98403-2)
- [Misner, Charles W.](https://en.wikipedia.org/wiki/Charles_W._Misner); [Thorne, Kip](https://en.wikipedia.org/wiki/Kip_Thorne); [Wheeler, John Archibald](https://en.wikipedia.org/wiki/John_Archibald_Wheeler) (1973), [*Gravitation*](https://en.wikipedia.org/wiki/Gravitation_(book) "Gravitation (book)"), W. H. Freeman, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-7167-0344-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-7167-0344-0)
- Naber, Gregory L. (2003), *The geometry of Minkowski spacetime*, New York: [Dover Publications](https://en.wikipedia.org/wiki/Dover_Publications), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-486-43235-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-486-43235-9), [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [2044239](https://mathscinet.ams.org/mathscinet-getitem?mr=2044239)
- [Schönhage, A.](https://en.wikipedia.org/wiki/Arnold_Sch%C3%B6nhage); [Strassen, Volker](https://en.wikipedia.org/wiki/Volker_Strassen) (1971), "Schnelle Multiplikation großer Zahlen (Fast multiplication of big numbers)", *Computing* (in German), **7** (3–4): 281–292, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/bf02242355](https://doi.org/10.1007%2Fbf02242355), [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0010-485X](https://search.worldcat.org/issn/0010-485X), [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [9738629](https://api.semanticscholar.org/CorpusID:9738629)
- [Spivak, Michael](https://en.wikipedia.org/wiki/Michael_Spivak) (1999), *A Comprehensive Introduction to Differential Geometry (Volume Two)*, Houston, TX: Publish or Perish
- [Stewart, Ian](https://en.wikipedia.org/wiki/Ian_Stewart_(mathematician) "Ian Stewart (mathematician)") (1975), [Galois Theory](https://archive.org/details/galoistheory0000stew), [Chapman and Hall](https://en.wikipedia.org/wiki/Chapman_and_Hall) Mathematics Series, London: [Chapman and Hall](https://en.wikipedia.org/wiki/Chapman_and_Hall), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-412-10800-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-412-10800-6)
- Varadarajan, V. S. (1974), *Lie groups, Lie algebras, and their representations*, [Prentice Hall](https://en.wikipedia.org/wiki/Prentice_Hall), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-13-535732-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-13-535732-3)
- Wallace, G.K. (Feb 1992), ["The JPEG still picture compression standard"](https://web.archive.org/web/20070113155847/http://www.csc.ncsu.edu/faculty/rhee/export/papers/TheJPEGStillPictureCompressionStandard.pdf) (PDF), *IEEE Transactions on Consumer Electronics*, **38** (1): xviii–xxxiv, [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.318.4292](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.318.4292), [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/30.125072](https://doi.org/10.1109%2F30.125072), [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0098-3063](https://search.worldcat.org/issn/0098-3063), archived from [the original](http://www.csc.ncsu.edu/faculty/rhee/export/papers/TheJPEGStillPictureCompressionStandard.pdf) (PDF) on 2007-01-13, retrieved 2017-10-25
- [Weibel, Charles A.](https://en.wikipedia.org/wiki/Charles_Weibel) (1994), *An introduction to homological algebra*, Cambridge Studies in Advanced Mathematics, vol. 38, Cambridge University Press, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-55987-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-55987-4), [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1269324](https://mathscinet.ams.org/mathscinet-getitem?mr=1269324), [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [36131259](https://search.worldcat.org/oclc/36131259)

## External links

- ["Vector space"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society), 2001 \[1994\]
