[[linear-algebra.base]]

> Source: [Quadratic form](https://en.wikipedia.org/wiki/Quadratic_form)
> License: Wikipedia content is available under CC BY-SA 4.0.

In [mathematics](https://en.wikipedia.org/wiki/Mathematics), a **quadratic form** is a [polynomial](https://en.wikipedia.org/wiki/Polynomial) with terms all of [degree](https://en.wikipedia.org/wiki/Degree_of_a_polynomial) two ("[form](https://en.wikipedia.org/wiki/Form_(mathematics))" is another name for a [homogeneous polynomial](https://en.wikipedia.org/wiki/Homogeneous_polynomial)). For example, 

$$
4x^{2}+2xy-3y^{2}
$$

is a quadratic form in the variables x and y. The coefficients usually belong to a fixed [field](https://en.wikipedia.org/wiki/Field_(mathematics) "Field (mathematics)") K, such as the [real](https://en.wikipedia.org/wiki/Real_number) or [complex](https://en.wikipedia.org/wiki/Complex_number) numbers, and one speaks of a quadratic form *over* K. Over the reals, a quadratic form is said to be *[definite](https://en.wikipedia.org/wiki/Definite_quadratic_form)* if it takes the value zero only when all its variables are simultaneously zero; otherwise it is *[isotropic](https://en.wikipedia.org/wiki/Isotropic_quadratic_form)*.

Quadratic forms occupy a central place in various branches of mathematics, including [number theory](https://en.wikipedia.org/wiki/Number_theory), [linear algebra](https://en.wikipedia.org/wiki/Linear_algebra), [group theory](https://en.wikipedia.org/wiki/Group_theory) ([orthogonal groups](https://en.wikipedia.org/wiki/Orthogonal_group)), [differential geometry](https://en.wikipedia.org/wiki/Differential_geometry) (the [Riemannian metric](https://en.wikipedia.org/wiki/Riemannian_metric), the [second fundamental form](https://en.wikipedia.org/wiki/Second_fundamental_form)), [differential topology](https://en.wikipedia.org/wiki/Differential_topology) ([intersection forms](https://en.wikipedia.org/wiki/Intersection_form_(4-manifold)) of [[Manifold|manifolds]], especially [four-manifolds](https://en.wikipedia.org/wiki/Four-manifold)), [Lie theory](https://en.wikipedia.org/wiki/Lie_theory) (the [Killing form](https://en.wikipedia.org/wiki/Killing_form)), and [statistics](https://en.wikipedia.org/wiki/Quadratic_form_(statistics) "Quadratic form (statistics)") (where the exponent of a zero-mean [[Multivariate Normal Distribution]] has the quadratic form −**x**<sup>T</sup>**Σ**<sup>−1</sup>**x**).

Quadratic forms are not to be confused with [quadratic equations](https://en.wikipedia.org/wiki/Quadratic_equation), which have only one variable and may include terms of degree less than two. A quadratic form is a specific instance of the more general concept of [forms](https://en.wikipedia.org/wiki/Form_(mathematics)).

## Introduction

Quadratic forms are homogeneous quadratic polynomials in n variables. In the cases of one, two, and three variables they are called **unary**, **[binary](https://en.wikipedia.org/wiki/Binary_quadratic_form)**, and **ternary** and have the following explicit form: 

$$
{\begin{aligned}q(x)&=ax^{2}&&{\textrm {(unary)}}\\q(x,y)&=ax^{2}+bxy+cy^{2}&&{\textrm {(binary)}}\\q(x,y,z)&=ax^{2}+bxy+cy^{2}+dyz+ez^{2}+fxz&&{\textrm {(ternary)}}\end{aligned}}
$$

where a, ..., f are the **coefficients**.

The theory of quadratic forms and methods used in their study depend in a large measure on the nature of the coefficients, which may be [real](https://en.wikipedia.org/wiki/Real_number) or [complex numbers](https://en.wikipedia.org/wiki/Complex_number), [rational numbers](https://en.wikipedia.org/wiki/Rational_number), or [integers](https://en.wikipedia.org/wiki/Integer). In [linear algebra](https://en.wikipedia.org/wiki/Linear_algebra), [analytic geometry](https://en.wikipedia.org/wiki/Analytic_geometry), and in the majority of applications of quadratic forms, the coefficients are real or complex numbers. In the algebraic theory of quadratic forms, the coefficients are elements of a certain [field](https://en.wikipedia.org/wiki/Field_(algebra)). In the arithmetic theory of quadratic forms, the coefficients belong to a fixed [commutative ring](https://en.wikipedia.org/wiki/Commutative_ring), frequently the integers **Z** or the [p-adic integers](https://en.wikipedia.org/wiki/P-adic_integer) **Z**<sub>*p*</sub>. [Binary quadratic forms](https://en.wikipedia.org/wiki/Binary_quadratic_form) have been extensively studied in [number theory](https://en.wikipedia.org/wiki/Number_theory), in particular, in the theory of [quadratic fields](https://en.wikipedia.org/wiki/Quadratic_field), [continued fractions](https://en.wikipedia.org/wiki/Continued_fraction), and [modular forms](https://en.wikipedia.org/wiki/Modular_forms). The theory of integral quadratic forms in n variables has important applications to [algebraic topology](https://en.wikipedia.org/wiki/Algebraic_topology).

Using [homogeneous coordinates](https://en.wikipedia.org/wiki/Homogeneous_coordinates), a non-zero quadratic form in n variables defines an (*n* − 2)-dimensional [quadric](https://en.wikipedia.org/wiki/Quadric_(projective_geometry)) in the (*n* − 1)-dimensional [projective space](https://en.wikipedia.org/wiki/Projective_space). This is a basic construction in [projective geometry](https://en.wikipedia.org/wiki/Projective_geometry). In this way one may visualize 3-dimensional real quadratic forms as [conic sections](https://en.wikipedia.org/wiki/Conic_sections). An example is given by the three-dimensional [Euclidean space](https://en.wikipedia.org/wiki/Euclidean_space) and the [square](https://en.wikipedia.org/wiki/Square_(algebra) "Square (algebra)") of the [Euclidean norm](https://en.wikipedia.org/wiki/Euclidean_norm) expressing the [distance](https://en.wikipedia.org/wiki/Distance) between a point with coordinates (*x*, *y*, *z*) and the origin: 

$$
q(x,y,z)=d((x,y,z),(0,0,0))^{2}=\left\|(x,y,z)\right\|^{2}=x^{2}+y^{2}+z^{2}.
$$

A closely related notion with geometric overtones is a **quadratic space**, which is a pair (*V*, *q*), with V a [[Vector Space]] over a field K, and *q* : *V* → *K* a quadratic form on V. See *[§ Definitions](#Definitions)* below for the definition of a quadratic form on a vector space.

## History

The study of quadratic forms, in particular the question of whether a given integer can be the value of a quadratic form over the integers, dates back many centuries. One such case is [Fermat's theorem on sums of two squares](https://en.wikipedia.org/wiki/Fermat%27s_theorem_on_sums_of_two_squares), which determines when an integer may be expressed in the form *x*<sup>2</sup> + *y*<sup>2</sup>, where x, y are integers. This problem is related to the problem of finding [Pythagorean triples](https://en.wikipedia.org/wiki/Pythagorean_triple), which appeared in the second millennium BCE.

In 628, the Indian mathematician [Brahmagupta](https://en.wikipedia.org/wiki/Brahmagupta) wrote *[Brāhmasphuṭasiddhānta](https://en.wikipedia.org/wiki/Br%C4%81hmasphu%E1%B9%ADasiddh%C4%81nta)*, which includes, among many other things, a study of equations of the form *x*<sup>2</sup> − *ny*<sup>2</sup> = *c*. He considered what is now called [Pell's equation](https://en.wikipedia.org/wiki/Pell%27s_equation), *x*<sup>2</sup> − *ny*<sup>2</sup> = 1, and found a method for its solution. In Europe this problem was studied by [Brouncker](https://en.wikipedia.org/wiki/William_Brouncker,_2nd_Viscount_Brouncker), [Euler](https://en.wikipedia.org/wiki/Leonhard_Euler) and [Lagrange](https://en.wikipedia.org/wiki/Joseph_Louis_Lagrange).

In 1801 [Gauss](https://en.wikipedia.org/wiki/Carl_Friedrich_Gauss) published *[Disquisitiones Arithmeticae](https://en.wikipedia.org/wiki/Disquisitiones_Arithmeticae),* a major portion of which was devoted to a complete theory of [binary quadratic forms](https://en.wikipedia.org/wiki/Binary_quadratic_form) over the [integers](https://en.wikipedia.org/wiki/Integer). Since then, the concept has been generalized, and the connections with [quadratic number fields](https://en.wikipedia.org/wiki/Quadratic_number_field), the [modular group](https://en.wikipedia.org/wiki/Modular_group), and other areas of mathematics have been further elucidated.

## Associated symmetric matrix

Any *n* × *n* matrix A determines a quadratic form *q*<sub>*A*</sub> in n variables by 

$$
q_{A}(x_{1},\ldots ,x_{n})=\sum _{i=1}^{n}\sum _{j=1}^{n}a_{ij}{x_{i}}{x_{j}}=\mathbf {x} ^{\mathsf {T}}A\mathbf {x} ,
$$

 where *A* = (*a*<sub>*ij*</sub>).

### Example

Consider the case of quadratic forms in three variables *x*, *y*, *z*. The matrix A has the form 

$$
A={\begin{bmatrix}a&b&c\\d&e&f\\g&h&k\end{bmatrix}}.
$$

The above formula gives 

$$
q_{A}(x,y,z)=ax^{2}+ey^{2}+kz^{2}+(b+d)xy+(c+g)xz+(f+h)yz.
$$

So, two different matrices define the same quadratic form if and only if they have the same elements on the diagonal and the same values for the sums *b* + *d*, *c* + *g* and *f* + *h*. In particular, the quadratic form *q*<sub>*A*</sub> is defined by a unique [symmetric matrix](https://en.wikipedia.org/wiki/Symmetric_matrix) 

$$
A={\begin{bmatrix}a&{\frac {b+d}{2}}&{\frac {c+g}{2}}\\{\frac {b+d}{2}}&e&{\frac {f+h}{2}}\\{\frac {c+g}{2}}&{\frac {f+h}{2}}&k\end{bmatrix}}.
$$

This generalizes to any number of variables as follows.

### General case

Given a quadratic form *q*<sub>*A*</sub> over the real numbers, defined by the matrix *A* = \[ *a*<sub>*ij*</sub> \]<sup>*n*,*n*</sup>  
<sub>*i*,*j*=1,1</sub>, with indicies i and j independently varying from 1 through n ≥ 2, the matrix

$$
B\equiv \left[{\frac {a_{\;\!ij}+a_{\;\!ji}}{2}}\right]_{i,j=1,1}^{n,n}={\frac {1}{2}}\left(A+A^{\mathsf {T}}\right)
$$

is [symmetric](https://en.wikipedia.org/wiki/Symmetric_matrix), defines the same quadratic form as A, and is the unique symmetric matrix that defines *q*<sub>*A*</sub>.

So, over the real numbers (and, more generally, over a [field](https://en.wikipedia.org/wiki/Field_(mathematics) "Field (mathematics)") of [characteristic](https://en.wikipedia.org/wiki/Characteristic_(algebra) "Characteristic (algebra)") different from two), there is a [one-to-one correspondence](https://en.wikipedia.org/wiki/One-to-one_correspondence) between quadratic forms and [symmetric matrices](https://en.wikipedia.org/wiki/Symmetric_matrices) that determine them.

## Real quadratic forms

A fundamental problem is the classification of real quadratic forms under a [[Linear Transformation|linear change of variables]].

[Jacobi](https://en.wikipedia.org/wiki/Carl_Gustav_Jacobi) proved that, for every real quadratic form, there is an [orthogonal diagonalization](https://en.wikipedia.org/wiki/Orthogonal_diagonalization); that is, an [orthogonal change of variables](https://en.wikipedia.org/wiki/Orthogonal_transformation) that puts the quadratic form in a "[diagonal form](https://en.wikipedia.org/wiki/Diagonal_form)" 

$$
\lambda _{1}{\tilde {x}}_{1}^{2}+\lambda _{2}{\tilde {x}}_{2}^{2}+\cdots +\lambda _{n}{\tilde {x}}_{n}^{2},
$$

 where the associated symmetric matrix is [diagonal](https://en.wikipedia.org/wiki/Diagonal_matrix). Moreover, the coefficients *λ*<sub>1</sub>, *λ*<sub>2</sub>, ..., *λ*<sub>*n*</sub> are determined uniquely [up to](https://en.wikipedia.org/wiki/Up_to) a [permutation](https://en.wikipedia.org/wiki/Permutation).

If the change of variables is given by an [invertible matrix](https://en.wikipedia.org/wiki/Invertible_matrix) that is not necessarily orthogonal, one can suppose that all coefficients *λ*<sub>*i*</sub> are 0, +1, or −1. [Sylvester's law of inertia](https://en.wikipedia.org/wiki/Sylvester%27s_law_of_inertia) states that the numbers of each 0, +1, and −1 are [invariants](https://en.wikipedia.org/wiki/Invariant_(mathematics) "Invariant (mathematics)") of the quadratic form, in the sense that any other diagonalization will contain the same number of each. The **signature** of the quadratic form is the triple (*n*<sub>0</sub>, *n*<sub>+</sub>, *n*<sub>−</sub>), where these components count the number of 0s, number of +1s, and the number of −1s, respectively. [Sylvester](https://en.wikipedia.org/wiki/James_Joseph_Sylvester)'s law of inertia shows that this is a well-defined quantity attached to the quadratic form.

The case when all *λ*<sub>*i*</sub> have the same sign is especially important: in this case the quadratic form is called **[positive definite](https://en.wikipedia.org/wiki/Positive_definite_form)** (all +1) or **negative definite** (all −1). If none of the terms are 0, then the form is called nondegenerate; this includes positive definite, negative definite, and [isotropic quadratic form](https://en.wikipedia.org/wiki/Isotropic_quadratic_form) (a mix of +1 and −1); equivalently, a nondegenerate quadratic form is one whose associated symmetric form is a [nondegenerate bilinear form](https://en.wikipedia.org/wiki/Nondegenerate_form). A real vector space with an indefinite nondegenerate quadratic form of index (*p*, *q*) (count p of +1s, and q of −1s) is often denoted as ℝ<sup>*p*,*q*</sup> particularly in the physical theory of [spacetime](https://en.wikipedia.org/wiki/Spacetime).

The [discriminant of a quadratic form](https://en.wikipedia.org/wiki/Discriminant#Discriminant_of_a_quadratic_form), concretely the class of the determinant of a representing matrix in *K* / (*K*<sup>×</sup>)<sup>2</sup> (up to non-zero squares) can also be defined, and for a real quadratic form is a cruder invariant than signature, taking values of only "positive, zero, or negative". Zero corresponds to degenerate, while for a non-degenerate form it is the parity of the number of negative coefficients, (−1)<sup>*n*<sub>−</sub></sup>.

These results are reformulated in a different way below.

Let q be a quadratic form defined on an n-dimensional [real](https://en.wikipedia.org/wiki/Real_number) vector space. Let A be the matrix of the quadratic form q in a given basis. This means that A is a symmetric *n* × *n* matrix such that 

$$
q(v)=x^{\mathsf {T}}Ax,
$$

 where x is the column vector of coordinates of v in the chosen basis. Under a change of basis, the column x is multiplied on the left by an *n* × *n* [invertible matrix](https://en.wikipedia.org/wiki/Invertible_matrix) S, and the symmetric square matrix A is transformed into another symmetric square matrix B of the same size according to the formula 

$$
A\to B=S^{-1}AS~.
$$

Any symmetric matrix A can be transformed into a diagonal matrix 

$$
B={\begin{pmatrix}\lambda _{1}&0&\cdots &0\\0&\lambda _{2}&\cdots &0\\\vdots &\vdots &\ddots &0\\0&0&\cdots &\lambda _{n}\end{pmatrix}}
$$

 by a suitable choice of an *orthogonal* matrix S, and the diagonal entries of B are uniquely determined – this is Jacobi's theorem (*see* [skew-symmetric matrix](https://en.wikipedia.org/wiki/Skew-symmetric_matrix)). If S is allowed to be *any* invertible matrix then B can be made to have only 0, +1, and −1 on the diagonal, and the number of the entries of each type (*n*<sub>0</sub> for 0, *n*<sub>+</sub> for +1, and *n*<sub>−</sub> for −1) depends only on A. This is one of the formulations of Sylvester's law of inertia and the numbers *n*<sub>+</sub> and *n*<sub>−</sub> are called the **positive** and **negative** **indices of inertia**. Although their definition involved a choice of basis and consideration of the corresponding real symmetric matrix A, Sylvester's law of inertia means that they are invariants of the quadratic form q.

The quadratic form q is positive definite if *q*(*v*) \> 0 (similarly, negative definite if *q*(*v*) \< 0) for every nonzero vector v. When *q*(*v*) assumes both positive and negative values, q is an [isotropic quadratic form](https://en.wikipedia.org/wiki/Isotropic_quadratic_form). The theorems of Jacobi and [Sylvester](https://en.wikipedia.org/wiki/James_Joseph_Sylvester) show that any positive definite quadratic form in n variables can be brought to the sum of n squares by a suitable invertible linear transformation: geometrically, there is only *one* positive definite real quadratic form of every dimension. Its [isometry group](https://en.wikipedia.org/wiki/Isometry_group) is a *[compact](https://en.wikipedia.org/wiki/Compact_space)* [orthogonal group](https://en.wikipedia.org/wiki/Orthogonal_group), conventionally notated as O(*n*). This stands in contrast with the case of isotropic forms, when the corresponding group, the [indefinite orthogonal group](https://en.wikipedia.org/wiki/Indefinite_orthogonal_group) O(*p*, *q*), is non-compact. Further, the [isometry groups](https://en.wikipedia.org/wiki/Isometry_group) of Q and −*Q* are the same (O(*p*, *q*) ≈ O(*q*, *p*)), but the associated [Clifford algebras](https://en.wikipedia.org/wiki/Clifford_algebra) (and hence [pin groups](https://en.wikipedia.org/wiki/Pin_group)) are different.

## Definitions

A **quadratic form** over a field K is a map *q* : *V* → *K* from a finite-dimensional K-vector space to K such that *q*(*av*) = *a*<sup>2</sup>*q*(*v*) for all *a* ∈ *K*, *v* ∈ *V* and the function *q*(*u* + *v*) − *q*(*u*) − *q*(*v*) is a [bilinear form](https://en.wikipedia.org/wiki/Bilinear_form).

More concretely, an n-ary **quadratic form** over a field K is a [homogeneous polynomial](https://en.wikipedia.org/wiki/Homogeneous_polynomial) of degree 2 in n variables with coefficients in K: 

$$
q(x_{1},\ldots ,x_{n})=\sum _{i=1}^{n}\sum _{j=1}^{n}a_{ij}{x_{i}}{x_{j}},\quad a_{ij}\in K.
$$

This formula may be rewritten using matrices: let x be the [column vector](https://en.wikipedia.org/wiki/Column_vector) with components *x*<sub>1</sub>, ..., *x*<sub>*n*</sub> and *A* = (*a*<sub>*ij*</sub>) be the *n* × *n* matrix over K whose entries are the coefficients of q. Then 

$$
q(x)=x^{\mathsf {T}}Ax.
$$

A vector *v* = (*x*<sub>1</sub>, ..., *x*<sub>*n*</sub>) is a [null vector](https://en.wikipedia.org/wiki/Null_vector) if *q*(*v*) = 0.

Two n-ary quadratic forms φ and ψ over K are **equivalent** if there exists a nonsingular linear transformation *C* ∈ [GL](https://en.wikipedia.org/wiki/General_linear_group)(*n*, *K*) such that 

$$
\psi (x)=\varphi (Cx).
$$

Let the [characteristic](https://en.wikipedia.org/wiki/Characteristic_(field)) of K be different from 2. The coefficient matrix A of q may be replaced by the [symmetric matrix](https://en.wikipedia.org/wiki/Symmetric_matrix) (*A* + *A*<sup>T</sup>)/2 with the same quadratic form, so it may be assumed from the outset that A is symmetric. Moreover, a symmetric matrix A is uniquely determined by the corresponding quadratic form. Under an equivalence C, the symmetric matrix A of φ and the symmetric matrix B of ψ are related as follows: 

$$
B=C^{\mathsf {T}}AC.
$$

The **associated bilinear form** of a quadratic form q is defined by 

$$
b_{q}(x,y)={\tfrac {1}{2}}(q(x+y)-q(x)-q(y))=x^{\mathsf {T}}Ay=y^{\mathsf {T}}Ax.
$$

Thus, *b*<sub>*q*</sub> is a [symmetric bilinear form](https://en.wikipedia.org/wiki/Symmetric_bilinear_form) over K with matrix A. Conversely, any symmetric bilinear form b defines a quadratic form 

$$
q(x)=b(x,x),
$$

 and these two processes are the inverses of each other. As a consequence, over a field of characteristic not equal to 2, the theories of symmetric bilinear forms and of quadratic forms in n variables are essentially the same.

### Quadratic space

Given an n-dimensional [[Vector Space]] V over a field K, a *quadratic form* on V is a [function](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)") *Q* : *V* → *K* that has the following property: for some basis, the function q that maps the coordinates of *v* ∈ *V* to *Q*(*v*) is a quadratic form. In particular, if *V* = *K*<sup>*n*</sup> with its [standard basis](https://en.wikipedia.org/wiki/Standard_basis), one has 

$$
q(v_{1},\ldots ,v_{n})=Q([v_{1},\ldots ,v_{n}])\quad {\text{for}}\quad [v_{1},\ldots ,v_{n}]\in K^{n}.
$$

The [change of basis](https://en.wikipedia.org/wiki/Change_of_basis) formulas show that the property of being a quadratic form does not depend on the choice of a specific basis in V, although the quadratic form q depends on the choice of the basis.

A finite-dimensional vector space with a quadratic form is called a **quadratic space**.

The map Q is a [homogeneous function](https://en.wikipedia.org/wiki/Homogeneous_function) of degree 2, which means that it has the property that, for all a in K and v in V: 

$$
Q(av)=a^{2}Q(v).
$$

When the characteristic of K is not 2, the bilinear map *B* : *V* × *V* → *K* over K is defined: 

$$
B(v,w)={\tfrac {1}{2}}(Q(v+w)-Q(v)-Q(w)).
$$

 This bilinear form B is symmetric. That is, *B*(*x*, *y*) = *B*(*y*, *x*) for all x, y in V, and it determines Q: *Q*(*x*) = *B*(*x*, *x*) for all x in V.

When the characteristic of K is 2, so that 2 is not a [unit](https://en.wikipedia.org/wiki/Unit_(ring_theory) "Unit (ring theory)"), it is still possible to use a quadratic form to define a symmetric bilinear form *B*′(*x*, *y*) = *Q*(*x* + *y*) − *Q*(*x*) − *Q*(*y*). However, *Q*(*x*) can no longer be recovered from this *B*′ in the same way, since *B*′(*x*, *x*) = 0 for all x (and is thus alternating). Alternatively, there always exists a bilinear form *B*″ (not in general either unique or symmetric) such that *B*″(*x*, *x*) = *Q*(*x*).

The pair (*V*, *Q*) consisting of a finite-dimensional vector space V over K and a quadratic map Q from V to K is called a **quadratic space**, and B as defined here is the associated symmetric bilinear form of Q. The notion of a quadratic space is a coordinate-free version of the notion of quadratic form. Sometimes, Q is also called a quadratic form.

Two n-dimensional quadratic spaces (*V*, *Q*) and (*V*′, *Q*′) are **isometric** if there exists an invertible linear transformation *T* : *V* → *V*′ (**isometry**) such that 

$$
Q(v)=Q'(Tv){\text{ for all }}v\in V.
$$

The isometry classes of n-dimensional quadratic spaces over K correspond to the equivalence classes of n-ary quadratic forms over K.

### Generalization

Let R be a [commutative ring](https://en.wikipedia.org/wiki/Commutative_ring), M be an R-[module](https://en.wikipedia.org/wiki/Module_(mathematics) "Module (mathematics)"), and *b* : *M* × *M* → *R* be an R-bilinear form. A mapping *q* : *M* → *R* : *v* ↦ *b*(*v*, *v*) is the *associated quadratic form* of b, and *B* : *M* × *M* → *R* : (*u*, *v*) ↦ *q*(*u* + *v*) − *q*(*u*) − *q*(*v*) is the *polar form* of q.

A quadratic form *q* : *M* → *R* may be characterized in the following equivalent ways:

- There exists an R-bilinear form *b* : *M* × *M* → *R* such that *q*(*v*) is the associated quadratic form.
- *q*(*av*) = *a*<sup>2</sup>*q*(*v*) for all *a* ∈ *R* and *v* ∈ *M*, and the polar form of q is R-bilinear.

### Related concepts

Two elements v and w of V are called **[orthogonal](https://en.wikipedia.org/wiki/Orthogonal)** if *B*(*v*, *w*) = 0. The **kernel** of a bilinear form B consists of the elements that are orthogonal to every element of V. Q is **non-singular** if the kernel of its associated bilinear form is {0}. If there exists a non-zero v in V such that *Q*(*v*) = 0, the quadratic form Q is **[isotropic](https://en.wikipedia.org/wiki/Isotropic_quadratic_form)**, otherwise it is **[definite](https://en.wikipedia.org/wiki/Definite_quadratic_form)**. This terminology also applies to vectors and subspaces of a quadratic space. If the restriction of Q to a subspace U of V is identically zero, then U is **totally singular**.

The orthogonal group of a non-singular quadratic form Q is the group of the linear automorphisms of V that preserve Q: that is, the group of isometries of (*V*, *Q*) into itself.

If a quadratic space (*A*, *Q*) has a product so that A is an [algebra over a field](https://en.wikipedia.org/wiki/Algebra_over_a_field), and satisfies 

$$
\forall x,y\in A\quad Q(xy)=Q(x)Q(y),
$$

 then it is a [composition algebra](https://en.wikipedia.org/wiki/Composition_algebra).

## Equivalence of forms

Every quadratic form q in n variables over a field of characteristic not equal to 2 is [equivalent](https://en.wikipedia.org/wiki/Matrix_congruence) to a **diagonal form** 

$$
q(x)=a_{1}x_{1}^{2}+a_{2}x_{2}^{2}+\cdots +a_{n}x_{n}^{2}.
$$

Such a diagonal form is often denoted by ⟨*a*<sub>1</sub>, ..., *a*<sub>*n*</sub>⟩. Classification of all quadratic forms up to equivalence can thus be reduced to the case of diagonal forms.

## Geometric meaning

Using [Cartesian coordinates](https://en.wikipedia.org/wiki/Cartesian_coordinates) in three dimensions, let **x** ≡ \[*x*, *y*, *z*\]<sup>T</sup>, and let A be a [symmetric](https://en.wikipedia.org/wiki/Symmetric_matrix) 3-by-3 matrix. Then the geometric nature of the [solution set](https://en.wikipedia.org/wiki/Solution_set) of the equation **x**<sup>T</sup>A**x** + **b**<sup>T</sup>**x** = 1 depends on the eigenvalues of the matrix A.

If all [eigenvalues](https://en.wikipedia.org/wiki/Eigenvalue) of A are non-zero, then the solution set is an [ellipsoid](https://en.wikipedia.org/wiki/Ellipsoid) or a [hyperboloid](https://en.wikipedia.org/wiki/Hyperboloid).<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup> If all the eigenvalues are positive, then it is an ellipsoid; if all the eigenvalues are negative, then it is an *imaginary ellipsoid* (we get the equation of an ellipsoid but with imaginary radii); if some eigenvalues are positive and some are negative, then it is a hyperboloid; if the eigenvalues are all equal and positive, then it is a sphere (special case of an ellipsoid with all axes equal, corresponding to the presence of equal eigenvalues).

If there exist one or more eigenvalues *λ*<sub>*i*</sub> = 0, then the shape depends on the corresponding *b*<sub>*i*</sub>. If the corresponding *b*<sub>*i*</sub> ≠ 0, then the solution set is a [paraboloid](https://en.wikipedia.org/wiki/Paraboloid) (either elliptic or hyperbolic); if the corresponding *b*<sub>*i*</sub> = 0, then the dimension i degenerates and does not come into play, and the geometric meaning will be determined by other eigenvalues and other components of **b**. When the solution set is a [paraboloid](https://en.wikipedia.org/wiki/Paraboloid), whether it is elliptic or hyperbolic is determined by whether all other non-zero eigenvalues are of the same sign: If they are, then it is elliptic; otherwise, it is hyperbolic.

## Integral quadratic forms

Quadratic forms over the ring of integers are called **integral quadratic forms**, whereas the corresponding modules are **quadratic lattices** (sometimes, simply [lattices](https://en.wikipedia.org/wiki/Lattice_(group) "Lattice (group)")). They play an important role in [number theory](https://en.wikipedia.org/wiki/Number_theory) and [topology](https://en.wikipedia.org/wiki/Topology).

An integral quadratic form has integer coefficients, such as *x*<sup>2</sup> + *xy* + *y*<sup>2</sup>; equivalently, given a lattice Λ in a vector space V (over a field with characteristic 0, such as **Q** or **R**), a quadratic form Q is integral *with respect to* Λ if and only if it is integer-valued on Λ, meaning *Q*(*x*, *y*) ∈ **Z** if *x*, *y* ∈ Λ.

This is the current use of the term; in the past it was sometimes used differently, as detailed below.

### Historical use

Historically there was some confusion and controversy over whether the notion of **integral quadratic form** should mean:

*twos in*  
the quadratic form associated to a symmetric matrix with integer coefficients

*twos out*  
a polynomial with integer coefficients (so the associated symmetric matrix may have half-integer coefficients off the diagonal)

This debate was due to the confusion of quadratic forms (represented by polynomials) and symmetric bilinear forms (represented by matrices), and "twos out" is now the accepted convention; "twos in" is instead the theory of integral symmetric bilinear forms (integral symmetric matrices).

In "twos in", binary quadratic forms are of the form *ax*<sup>2</sup> + 2*bxy* + *cy*<sup>2</sup>, represented by the symmetric matrix 

$$
{\begin{pmatrix}a&b\\b&c\end{pmatrix}}
$$

 This is the convention [Gauss](https://en.wikipedia.org/wiki/Gauss) uses in *[Disquisitiones Arithmeticae](https://en.wikipedia.org/wiki/Disquisitiones_Arithmeticae)*.

In "twos out", binary quadratic forms are of the form *ax*<sup>2</sup> + *bxy* + *cy*<sup>2</sup>, represented by the symmetric matrix 

$$
{\begin{pmatrix}a&b/2\\b/2&c\end{pmatrix}}.
$$

Several points of view mean that *twos out* has been adopted as the standard convention. Those include:

- better understanding of the 2-adic theory of quadratic forms, the 'local' source of the difficulty;
- the ability to express any quadratic form in characteristic 2 via a (not necessarily symmetric) matrix;
- the [lattice](https://en.wikipedia.org/wiki/Lattice_(group) "Lattice (group)") point of view, which was generally adopted by the experts in the arithmetic of quadratic forms during the 1950s;
- the actual needs for integral quadratic form theory in [topology](https://en.wikipedia.org/wiki/Topology) for [intersection theory](https://en.wikipedia.org/wiki/Intersection_theory);
- the [Lie group](https://en.wikipedia.org/wiki/Lie_group) and [algebraic group](https://en.wikipedia.org/wiki/Algebraic_group) aspects.

### Universal quadratic forms

An integral quadratic form whose image consists of all the positive integers is sometimes called *universal*. [Lagrange's four-square theorem](https://en.wikipedia.org/wiki/Lagrange%27s_four-square_theorem) shows that *w*<sup>2</sup> + *x*<sup>2</sup> + *y*<sup>2</sup> + *z*<sup>2</sup> is universal. [Ramanujan](https://en.wikipedia.org/wiki/Ramanujan) generalized this *aw*<sup>2</sup> + *bx*<sup>2</sup> + *cy*<sup>2</sup> + *dz*<sup>2</sup> and found 54 multisets {*a*, *b*, *c*, *d*} that can each generate all positive integers, namely,

- {1, 1, 1, *d*}, 1 ≤ *d* ≤ 7
- {1, 1, 2, *d*}, 2 ≤ *d* ≤ 14
- {1, 1, 3, *d*}, 3 ≤ *d* ≤ 6
- {1, 2, 2, *d*}, 2 ≤ *d* ≤ 7
- {1, 2, 3, *d*}, 3 ≤ *d* ≤ 10
- {1, 2, 4, *d*}, 4 ≤ *d* ≤ 14
- {1, 2, 5, *d*}, 6 ≤ *d* ≤ 10

There are also forms whose image consists of all but one of the positive integers. For example, {1, 2, 5, 5} has 15 as the exception. Recently, the [15 and 290 theorems](https://en.wikipedia.org/wiki/15_and_290_theorems) have completely characterized universal integral quadratic forms: if all coefficients are integers, then it represents all positive integers if and only if it represents all integers up through 290; if it has an integral matrix, it represents all positive integers if and only if it represents all integers up through 15.

## See also

- [*ε*-quadratic form](https://en.wikipedia.org/wiki/%CE%95-quadratic_form)
- [Cubic form](https://en.wikipedia.org/wiki/Cubic_form)
- [Discriminant of a quadratic form](https://en.wikipedia.org/wiki/Discriminant#Discriminant_of_a_quadratic_form)
- [Hasse–Minkowski theorem](https://en.wikipedia.org/wiki/Hasse%E2%80%93Minkowski_theorem)
- [Quadric](https://en.wikipedia.org/wiki/Quadric)
- [Ramanujan's ternary quadratic form](https://en.wikipedia.org/wiki/Ramanujan%27s_ternary_quadratic_form)
- [Square class](https://en.wikipedia.org/wiki/Square_class)
- [Witt group](https://en.wikipedia.org/wiki/Witt_group)
- [Witt's theorem](https://en.wikipedia.org/wiki/Witt%27s_theorem)

## Notes

1.  A tradition going back to [Gauss](https://en.wikipedia.org/wiki/Gauss) dictates the use of manifestly even coefficients for the products of distinct variables, that is, 2*b* in place of b in binary forms and 2*b*, 2*d*, 2*f* in place of b, d, f in ternary forms. Both conventions occur in the literature.
2.  [away from 2](https://en.wikipedia.org/wiki/Localization_of_a_ring#Terminology), that is, if 2 is invertible in the ring, quadratic forms are equivalent to [symmetric bilinear forms](https://en.wikipedia.org/wiki/Symmetric_bilinear_form) (by the [polarization identities](https://en.wikipedia.org/wiki/Polarization_identities)), but at 2 they are different concepts; this distinction is particularly important for quadratic forms over the integers.
3.  [Babylonian Pythagoras](http://www-groups.dcs.st-and.ac.uk/~history/HistTopics/Babylonian_Pythagoras.html)
4.  [Brahmagupta biography](http://www-groups.dcs.st-and.ac.uk/~history/Biographies/Brahmagupta.html)
5.  [Bôcher, M.](https://en.wikipedia.org/wiki/Maxime_B%C3%B4cher) (1907). ["§ 45 Reduction of a quadratic form to a sum of squares"](https://babel.hathitrust.org/cgi/pt?id=uc1.b4248862;view=1up;seq=147). *Introduction to Higher Algebra*. (with E.P.R. DuVal). New York, NY: Macmillan. p. 129 – via [HathiTrust](https://en.wikipedia.org/wiki/HathiTrust).
6.  If a non-strict inequality (with ≥ or ≤) holds then the quadratic form q is called semidefinite.
7.  The theory of quadratic forms over a field of characteristic 2 has some pitfalls and many definitions and theorems must be restated with care to apply in this context.
8.  This alternating form associated with a quadratic form in characteristic 2 is of interest related to the [Arf invariant](https://en.wikipedia.org/wiki/Arf_invariant) – Irving Kaplansky (1974), *Linear Algebra and Geometry*, p. 27.
9.  The bilinear form to which a quadratic form is associated is not restricted to being symmetric, which is of significance when 2 is not a unit in R.

## References

- [O'Meara, O.T.](https://en.wikipedia.org/wiki/O._Timothy_O%27Meara) (2000), *Introduction to Quadratic Forms*, Berlin, New York: [Springer-Verlag](https://en.wikipedia.org/wiki/Springer-Verlag), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-66564-9](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-66564-9)
- [Conway, John Horton](https://en.wikipedia.org/wiki/John_Horton_Conway); Fung, Francis Y. C. (1997), *The Sensual (Quadratic) Form*, Carus Mathematical Monographs, The Mathematical Association of America, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-88385-030-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-88385-030-5)
- [Shafarevich, I. R.](https://en.wikipedia.org/wiki/Igor_Shafarevich); Remizov, A. O. (2012). [Linear Algebra and Geometry](https://www.springer.com/mathematics/algebra/book/978-3-642-30993-9). [Springer](https://en.wikipedia.org/wiki/Springer_Science%2BBusiness_Media). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-642-30993-9](https://en.wikipedia.org/wiki/Special:BookSources/978-3-642-30993-9).

## Further reading

- [Cassels, J.W.S.](https://en.wikipedia.org/wiki/J._W._S._Cassels) (1978). *Rational Quadratic Forms*. London Mathematical Society Monographs. Vol. 13. [Academic Press](https://en.wikipedia.org/wiki/Academic_Press). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-12-163260-1](https://en.wikipedia.org/wiki/Special:BookSources/0-12-163260-1). [Zbl](https://en.wikipedia.org/wiki/Zbl_(identifier)) [0395.10029](https://zbmath.org/?format=complete&q=an:0395.10029).
- Kitaoka, Yoshiyuki (1993). *Arithmetic of quadratic forms*. Cambridge Tracts in Mathematics. Vol. 106. Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-40475-4](https://en.wikipedia.org/wiki/Special:BookSources/0-521-40475-4). [Zbl](https://en.wikipedia.org/wiki/Zbl_(identifier)) [0785.11021](https://zbmath.org/?format=complete&q=an:0785.11021).
- [Lam, Tsit-Yuen](https://en.wikipedia.org/wiki/Tsit_Yuen_Lam) (2005). *Introduction to Quadratic Forms over Fields*. [Graduate Studies in Mathematics](https://en.wikipedia.org/wiki/Graduate_Studies_in_Mathematics). Vol. 67. [American Mathematical Society](https://en.wikipedia.org/wiki/American_Mathematical_Society). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-8218-1095-2](https://en.wikipedia.org/wiki/Special:BookSources/0-8218-1095-2). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [2104929](https://mathscinet.ams.org/mathscinet-getitem?mr=2104929). [Zbl](https://en.wikipedia.org/wiki/Zbl_(identifier)) [1068.11023](https://zbmath.org/?format=complete&q=an:1068.11023).
- [Milnor, J.](https://en.wikipedia.org/wiki/John_Milnor); Husemoller, D. (1973). *Symmetric Bilinear Forms*. [Ergebnisse der Mathematik und ihrer Grenzgebiete](https://en.wikipedia.org/wiki/Ergebnisse_der_Mathematik_und_ihrer_Grenzgebiete). Vol. 73. [Springer-Verlag](https://en.wikipedia.org/wiki/Springer-Verlag). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [3-540-06009-X](https://en.wikipedia.org/wiki/Special:BookSources/3-540-06009-X). [Zbl](https://en.wikipedia.org/wiki/Zbl_(identifier)) [0292.10016](https://zbmath.org/?format=complete&q=an:0292.10016).
- [O'Meara, O.T.](https://en.wikipedia.org/wiki/O._Timothy_O%27Meara) (1973). *Introduction to quadratic forms*. Die Grundlehren der mathematischen Wissenschaften. Vol. 117. [Springer-Verlag](https://en.wikipedia.org/wiki/Springer-Verlag). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [3-540-66564-1](https://en.wikipedia.org/wiki/Special:BookSources/3-540-66564-1). [Zbl](https://en.wikipedia.org/wiki/Zbl_(identifier)) [0259.10018](https://zbmath.org/?format=complete&q=an:0259.10018).
- [Pfister, Albrecht](https://en.wikipedia.org/wiki/Albrecht_Pfister_(mathematician) "Albrecht Pfister (mathematician)") (1995). [Quadratic Forms with Applications to Algebraic Geometry and Topology](https://archive.org/details/quadraticformswi0000pfis). London Mathematical Society lecture note series. Vol. 217. [Cambridge University Press](https://en.wikipedia.org/wiki/Cambridge_University_Press). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-46755-1](https://en.wikipedia.org/wiki/Special:BookSources/0-521-46755-1). [Zbl](https://en.wikipedia.org/wiki/Zbl_(identifier)) [0847.11014](https://zbmath.org/?format=complete&q=an:0847.11014).

## External links

- A.V.Malyshev (2001) \[1994\], ["Quadratic form"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society)
- A.V.Malyshev (2001) \[1994\], ["Binary quadratic form"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society)
