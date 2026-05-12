[[linear-algebra.base]]

> Source: [Definite matrix](https://en.wikipedia.org/wiki/Definite_matrix)
> License: Wikipedia content is available under CC BY-SA 4.0.

In [mathematics](https://en.wikipedia.org/wiki/Mathematics), a symmetric matrix $M$ with [real](https://en.wikipedia.org/wiki/Real_number) entries is **positive-definite** if the real number $\mathbf {x} ^{\mathsf {T}}M\mathbf {x}$ is positive for every nonzero real [column vector](https://en.wikipedia.org/wiki/Column_vector) $\mathbf {x} ,$ where $\mathbf {x} ^{\mathsf {T}}$ is the [row vector](https://en.wikipedia.org/wiki/Row_vector) [transpose](https://en.wikipedia.org/wiki/Transpose) of $\mathbf {x} .$ More generally, a [Hermitian matrix](https://en.wikipedia.org/wiki/Hermitian_matrix) (that is, a [complex matrix](https://en.wikipedia.org/wiki/Complex_matrix) equal to its [conjugate transpose](https://en.wikipedia.org/wiki/Conjugate_transpose)) is **positive-definite** if the real number $\mathbf {z} ^{*}M\mathbf {z}$ is positive for every nonzero complex column vector $\mathbf {z} ,$ where $\mathbf {z} ^{*}$ denotes the conjugate transpose of $\mathbf {z} .$

**Positive semi-definite** matrices are defined similarly, except that the scalars $\mathbf {x} ^{\mathsf {T}}M\mathbf {x}$ and $\mathbf {z} ^{*}M\mathbf {z}$ are required to be positive *or zero* (that is, nonnegative). **Negative-definite** and **negative semi-definite** matrices are defined analogously. A matrix that is not positive semi-definite and not negative semi-definite is sometimes called *indefinite*.

Some authors use more general definitions of definiteness, permitting the matrices to be non-symmetric or non-Hermitian. The properties of these generalized definite matrices are explored in [§ Extension for non-Hermitian square matrices](#Extension_for_non-Hermitian_square_matrices), below, but are not the main focus of this article.

## Definitions

In the following definitions, $\mathbf {x} ^{\mathsf {T}}$ is the transpose of $\mathbf {x} ,$ $\mathbf {z} ^{*}$ is the [conjugate transpose](https://en.wikipedia.org/wiki/Conjugate_transpose) of $\mathbf {z} ,$ and $\mathbf {0}$ denotes the n dimensional zero-vector.

### Definitions for real matrices

An $n\times n$ symmetric real matrix $M$ is said to be **positive-definite** if $\mathbf {x} ^{\mathsf {T}}M\mathbf {x} >0$ for all non-zero $\mathbf {x}$ in $\mathbb {R} ^{n}.$ Formally,

$M{\text{ positive-definite}}\quad \iff \quad \mathbf {x} ^{\mathsf {T}}M\mathbf {x} >0{\text{ for all }}\mathbf {x} \in \mathbb {R} ^{n}\setminus \{\mathbf {0} \}$

An $n\times n$ symmetric real matrix $M$ is said to be **positive-semidefinite** or **non-negative-definite** if $\mathbf {x} ^{\mathsf {T}}M\mathbf {x} \geq 0$ for all $\mathbf {x}$ in $\mathbb {R} ^{n}.$ Formally,

$M{\text{ positive semi-definite}}\quad \iff \quad \mathbf {x} ^{\mathsf {T}}M\mathbf {x} \geq 0{\text{ for all }}\mathbf {x} \in \mathbb {R} ^{n}$

An $n\times n$ symmetric real matrix $M$ is said to be **negative-definite** if $\mathbf {x} ^{\mathsf {T}}M\mathbf {x} <0$ for all non-zero $\mathbf {x}$ in $\mathbb {R} ^{n}.$ Formally,

$M{\text{ negative-definite}}\quad \iff \quad \mathbf {x} ^{\mathsf {T}}M\mathbf {x} <0{\text{ for all }}\mathbf {x} \in \mathbb {R} ^{n}\setminus \{\mathbf {0} \}$

An $n\times n$ symmetric real matrix $M$ is said to be **negative-semidefinite** or **non-positive-definite** if $\mathbf {x} ^{\mathsf {T}}M\mathbf {x} \leq 0$ for all $\mathbf {x}$ in $\mathbb {R} ^{n}.$ Formally,

$M{\text{ negative semi-definite}}\quad \iff \quad \mathbf {x} ^{\mathsf {T}}M\mathbf {x} \leq 0{\text{ for all }}\mathbf {x} \in \mathbb {R} ^{n}$

An $n\times n$ symmetric real matrix which is neither positive semidefinite nor negative semidefinite is called **indefinite**.

### Definitions for complex matrices

The following definitions all involve the term $\mathbf {z} ^{*}M\mathbf {z} .$ Notice that this is always a real number for any Hermitian square matrix $M.$

An $n\times n$ Hermitian complex matrix $M$ is said to be **positive-definite** if $\mathbf {z} ^{*}M\mathbf {z} >0$ for all non-zero $\mathbf {z}$ in $\mathbb {C} ^{n}.$ Formally,

$M{\text{ positive-definite}}\quad \iff \quad \mathbf {z} ^{*}M\mathbf {z} >0{\text{ for all }}\mathbf {z} \in \mathbb {C} ^{n}\setminus \{\mathbf {0} \}$

An $n\times n$ Hermitian complex matrix $M$ is said to be **positive semi-definite** or **non-negative-definite** if $\mathbf {z} ^{*}M\mathbf {z} \geq 0$ for all $\mathbf {z}$ in $\mathbb {C} ^{n}.$ Formally,

$M{\text{ positive semi-definite}}\quad \iff \quad \mathbf {z} ^{*}M\mathbf {z} \geq 0{\text{ for all }}\mathbf {z} \in \mathbb {C} ^{n}$

An $n\times n$ Hermitian complex matrix $M$ is said to be **negative-definite** if $\mathbf {z} ^{*}M\mathbf {z} <0$ for all non-zero $\mathbf {z}$ in $\mathbb {C} ^{n}.$ Formally,

$M{\text{ negative-definite}}\quad \iff \quad \mathbf {z} ^{*}M\mathbf {z} <0{\text{ for all }}\mathbf {z} \in \mathbb {C} ^{n}\setminus \{\mathbf {0} \}$

An $n\times n$ Hermitian complex matrix $M$ is said to be **negative semi-definite** or **non-positive-definite** if $\mathbf {z} ^{*}M\mathbf {z} \leq 0$ for all $\mathbf {z}$ in $\mathbb {C} ^{n}.$ Formally,

$M{\text{ negative semi-definite}}\quad \iff \quad \mathbf {z} ^{*}M\mathbf {z} \leq 0{\text{ for all }}\mathbf {z} \in \mathbb {C} ^{n}$

An $n\times n$ Hermitian complex matrix which is neither positive semidefinite nor negative semidefinite is called **indefinite**.

### Consistency between real and complex definitions

Since every real matrix is also a complex matrix, the definitions of "definiteness" for the two classes must agree.

For complex matrices, the most common definition says that $M$ is positive-definite if and only if $\mathbf {z} ^{*}M\mathbf {z}$ is real and positive for every non-zero complex column vectors $\mathbf {z} .$ This condition implies that $M$ is Hermitian (i.e. its transpose is equal to its conjugate), since $\mathbf {z} ^{*}M\mathbf {z}$ being real, it equals its conjugate transpose $\mathbf {z} ^{*}M^{*}\mathbf {z}$ for every $\mathbf {z} ,$ which implies $M=M^{*}.$

By this definition, a positive-definite *real* matrix $M$ is Hermitian, hence symmetric; and $\mathbf {z} ^{\mathsf {T}}M\mathbf {z}$ is positive for all non-zero *real* column vectors $\mathbf {z} .$ However the last condition alone is not sufficient for $M$ to be positive-definite. For example, if 

$$
M={\begin{bmatrix}1&1\\-1&1\end{bmatrix}},
$$

then for any real vector $\mathbf {z}$ with entries $a$ and $b$ we have $\mathbf {z} ^{\mathsf {T}}M\mathbf {z} =\left(a+b\right)a+\left(-a+b\right)b=a^{2}+b^{2},$ which is always positive if $\mathbf {z}$ is not zero. However, if $\mathbf {z}$ is the complex vector with entries 1 and $i$, one gets

$$
\mathbf {z} ^{*}M\mathbf {z} ={\begin{bmatrix}1&-i\end{bmatrix}}M{\begin{bmatrix}1\\i\end{bmatrix}}={\begin{bmatrix}1+i&1-i\end{bmatrix}}{\begin{bmatrix}1\\i\end{bmatrix}}=2+2i.
$$

which is not real. Therefore, $M$ is not positive-definite.

On the other hand, for a *symmetric* real matrix $M,$ the condition "$\mathbf {z} ^{\mathsf {T}}M\mathbf {z} >0$ for all nonzero real vectors $\mathbf {z}$" *does* imply that $M$ is positive-definite in the complex sense.

### Notation

If a Hermitian matrix $M$ is positive semi-definite, one sometimes writes $M\succeq 0$ and if $M$ is positive-definite one writes $M\succ 0.$ To denote that $M$ is negative semi-definite one writes $M\preceq 0$ and to denote that $M$ is negative-definite one writes $M\prec 0.$

The notation comes from [functional analysis](https://en.wikipedia.org/wiki/Functional_analysis) where positive semidefinite matrices define [positive operators](https://en.wikipedia.org/wiki/Positive_operator). If two matrices $A$ and $B$ satisfy $B-A\succeq 0,$ we can define a [non-strict partial order](https://en.wikipedia.org/wiki/Partially_ordered_set#Non-strict_partial_order) $B\succeq A$ that is [reflexive](https://en.wikipedia.org/wiki/Reflexive_relation), [antisymmetric](https://en.wikipedia.org/wiki/Antisymmetric_relation), and [transitive](https://en.wikipedia.org/wiki/Transitive_relation); It is not a [total order](https://en.wikipedia.org/wiki/Total_order), however, as $B-A,$ in general, may be indefinite.

A common alternative notation is $M\geq 0,$ $M>0,$ $M\leq 0,$ and $M<0$ for positive semi-definite and positive-definite, negative semi-definite and negative-definite matrices, respectively. This may be confusing, as sometimes [nonnegative matrices](https://en.wikipedia.org/wiki/Nonnegative_matrix) (respectively, nonpositive matrices) are also denoted in this way.

## Ramifications

It follows from the above definitions that a Hermitian matrix is positive-definite [if and only if](https://en.wikipedia.org/wiki/If_and_only_if) it is the matrix of a [positive-definite quadratic form](https://en.wikipedia.org/wiki/Positive-definite_quadratic_form) or [Hermitian form](https://en.wikipedia.org/wiki/Hermitian_form). In other words, a Hermitian matrix is positive-definite if and only if it defines an [inner product](https://en.wikipedia.org/wiki/Inner_product).

Positive-definite and positive-semidefinite matrices can be characterized in many ways, which may explain the importance of the concept in various parts of mathematics. A Hermitian matrix M is positive-definite if and only if it satisfies any of the following equivalent conditions.

- $M$ is [congruent](https://en.wikipedia.org/wiki/Congruent_matrices) with a [diagonal matrix](https://en.wikipedia.org/wiki/Diagonal_matrix) with positive real entries.
- $M$ is Hermitian, and all its [eigenvalues](https://en.wikipedia.org/wiki/Eigenvalue) are real and positive.
- $M$ is Hermitian, and all its leading [principal minors](https://en.wikipedia.org/wiki/Principal_minor) are positive.
- There exists an [invertible matrix](https://en.wikipedia.org/wiki/Invertible_matrix) $B$ with conjugate transpose $B^{*}$ such that $M=B^{*}B.$

A matrix is positive semi-definite if it satisfies similar equivalent conditions where "positive" is replaced by "nonnegative", "invertible matrix" is replaced by "matrix", and the word "leading" is removed.

Positive-definite and positive-semidefinite real matrices are at the basis of [[Convex Optimization]], since, given a [function of several real variables](https://en.wikipedia.org/wiki/Function_of_several_real_variables) that is twice [differentiable](https://en.wikipedia.org/wiki/Differentiable_function), then if its [[Hessian Matrix]] (matrix of its second partial derivatives) is positive-definite at a point $p,$ then the function is [convex](https://en.wikipedia.org/wiki/Convex_function) near p, and, conversely, if the function is convex near $p,$ then the Hessian matrix is positive-semidefinite at $p.$

The set of positive definite matrices is an [open](https://en.wikipedia.org/wiki/Open_set) [convex cone](https://en.wikipedia.org/wiki/Convex_cone), while the set of positive semi-definite matrices is a [closed](https://en.wikipedia.org/wiki/Closed_set) convex cone.

## Examples

- The [identity matrix](https://en.wikipedia.org/wiki/Identity_matrix) $I={\begin{bmatrix}1&0\\0&1\end{bmatrix}}$ is positive-definite (and as such also positive semi-definite). It is a real symmetric matrix, and, for any non-zero column vector **z** with real entries *a* and *b*, one has

$$
\mathbf {z} ^{\mathsf {T}}I\mathbf {z} ={\begin{bmatrix}a&b\end{bmatrix}}{\begin{bmatrix}1&0\\0&1\end{bmatrix}}{\begin{bmatrix}a\\b\end{bmatrix}}=a^{2}+b^{2}.
$$

 Seen as a complex matrix, for any non-zero column vector *z* with complex entries *a* and *b* one has 

$$
\mathbf {z} ^{*}I\mathbf {z} ={\begin{bmatrix}{\overline {a}}&{\overline {b}}\end{bmatrix}}{\begin{bmatrix}1&0\\0&1\end{bmatrix}}{\begin{bmatrix}a\\b\end{bmatrix}}={\overline {a}}a+{\overline {b}}b=|a|^{2}+|b|^{2}.
$$

  Either way, the result is positive since $\mathbf {z}$ is not the zero vector (that is, at least one of $a$ and $b$ is not zero).

- The real symmetric matrix 

$$
M={\begin{bmatrix}2&-1&0\\-1&2&-1\\0&-1&2\end{bmatrix}}
$$

 is positive-definite since for any non-zero column vector **z** with entries *a*, *b* and *c*, we have 

$$
{\begin{aligned}\mathbf {z} ^{\mathsf {T}}M\mathbf {z} =\left(\mathbf {z} ^{\mathsf {T}}M\right)\mathbf {z} &={\begin{bmatrix}(2a-b)&(-a+2b-c)&(-b+2c)\end{bmatrix}}{\begin{bmatrix}a\\b\\c\end{bmatrix}}\\&=(2a-b)a+(-a+2b-c)b+(-b+2c)c\\&=2a^{2}-ba-ab+2b^{2}-cb-bc+2c^{2}\\&=2a^{2}-2ab+2b^{2}-2bc+2c^{2}\\&=a^{2}+a^{2}-2ab+b^{2}+b^{2}-2bc+c^{2}+c^{2}\\&=a^{2}+(a-b)^{2}+(b-c)^{2}+c^{2}\end{aligned}}
$$

 This result is a sum of squares, and therefore non-negative; and is zero only if $a=b=c=0,$ that is, when $\mathbf {z}$ is the zero vector.

- For any real [invertible matrix](https://en.wikipedia.org/wiki/Invertible_matrix) $A,$ the product $A^{\mathsf {T}}A$ is a positive definite matrix (if the means of the columns of A are 0, then this is also called the [covariance matrix](https://en.wikipedia.org/wiki/Covariance_matrix)). A simple proof is that for any non-zero vector $\mathbf {z} ,$ the condition $\mathbf {z} ^{\mathsf {T}}A^{\mathsf {T}}A\mathbf {z} =(A\mathbf {z} )^{\mathsf {T}}(A\mathbf {z} )=\|A\mathbf {z} \|^{2}>0,$ since the invertibility of matrix $A$ means that $A\mathbf {z} \neq 0.$

- The example $M$ above shows that a matrix in which some elements are negative may still be positive definite. Conversely, a matrix whose entries are all positive is not necessarily positive definite, as for example 

$$
N={\begin{bmatrix}1&2\\2&1\end{bmatrix}},
$$

 for which ${\begin{bmatrix}-1&1\end{bmatrix}}N{\begin{bmatrix}-1&1\end{bmatrix}}^{\mathsf {T}}=-2<0.$

## Eigenvalues

Let $M$ be an $n\times n$ [Hermitian matrix](https://en.wikipedia.org/wiki/Hermitian_matrix) (this includes real [symmetric matrices](https://en.wikipedia.org/wiki/Symmetric_matrices)). All eigenvalues of $M$ are real, and their sign characterize its definiteness:

- $M$ is positive definite if and only if all of its eigenvalues are positive.
- $M$ is positive semi-definite if and only if all of its eigenvalues are non-negative.
- $M$ is negative definite if and only if all of its eigenvalues are negative.
- $M$ is negative semi-definite if and only if all of its eigenvalues are non-positive.
- $M$ is indefinite if and only if it has both positive and negative eigenvalues.

Let $PDP^{-1}$ be an [eigendecomposition](https://en.wikipedia.org/wiki/Eigendecomposition_of_a_matrix) of $M,$ where $P$ is a [unitary complex matrix](https://en.wikipedia.org/wiki/Unitary_matrix) whose columns comprise an [orthonormal basis](https://en.wikipedia.org/wiki/Orthonormal_basis) of [eigenvectors](https://en.wikipedia.org/wiki/Eigenvector) of $M,$ and $D$ is a *real* [diagonal matrix](https://en.wikipedia.org/wiki/Diagonal_matrix) whose [main diagonal](https://en.wikipedia.org/wiki/Main_diagonal) contains the corresponding [eigenvalues](https://en.wikipedia.org/wiki/Eigenvalue). The matrix $M$ may be regarded as a diagonal matrix $D$ that has been re-expressed in coordinates of the (eigenvectors) basis $P.$ Put differently, applying $M$ to some vector $\mathbf {z} ,$ giving $M\mathbf {z} ,$ is the same as [changing the basis](https://en.wikipedia.org/wiki/Change_of_basis) to the eigenvector coordinate system using $P^{-1},$ giving $P^{-1}\mathbf {z} ,$ applying the [stretching transformation](https://en.wikipedia.org/wiki/Transformation_matrix) $D$ to the result, giving $DP^{-1}\mathbf {z} ,$ and then changing the basis back using $P,$ giving $PDP^{-1}\mathbf {z} .$

With this in mind, the one-to-one change of variable $\mathbf {y} =P\mathbf {z}$ shows that $\mathbf {z} ^{*}M\mathbf {z}$ is real and positive for any complex vector $\mathbf {z}$ if and only if $\mathbf {y} ^{*}D\mathbf {y}$ is real and positive for any $y;$ in other words, if $D$ is positive definite. For a diagonal matrix, this is true only if each element of the main diagonal – that is, every eigenvalue of $M$ – is positive. Since the [[Spectral Theorem]] guarantees all eigenvalues of a Hermitian matrix to be real, the positivity of eigenvalues can be checked using [Descartes' rule of alternating signs](https://en.wikipedia.org/wiki/Descartes%27_rule_of_signs) when the [characteristic polynomial](https://en.wikipedia.org/wiki/Characteristic_polynomial) of a real, symmetric matrix $M$ is available.

## Decomposition

Let $M$ be an $n\times n$ [Hermitian matrix](https://en.wikipedia.org/wiki/Hermitian_matrix). $M$ is positive semidefinite if and only if it can be decomposed as a product 

$$
M=B^{*}B
$$

 of a matrix $B$ with its [conjugate transpose](https://en.wikipedia.org/wiki/Conjugate_transpose).

When $M$ is real, $B$ can be real as well and the decomposition can be written as 

$$
M=B^{\mathsf {T}}B.
$$

$M$ is positive definite if and only if such a decomposition exists with $B$ [invertible](https://en.wikipedia.org/wiki/Invertible_matrix). More generally, $M$ is positive semidefinite with rank $k$ if and only if a decomposition exists with a $k\times n$ matrix $B$ of full row rank (i.e. of rank $k$). Moreover, for any decomposition $M=B^{*}B,$ $\operatorname {rank} (M)=\operatorname {rank} (B).$

**Proof**

If $M=B^{*}B,$ then $x^{*}Mx=(x^{*}B^{*})(Bx)=\|Bx\|^{2}\geq 0,$ so $M$ is positive semidefinite. If moreover $B$ is invertible then the inequality is strict for $x\neq 0,$ so $M$ is positive definite. If $B$ is $k\times n$ of rank $k,$ then $\operatorname {rank} (M)=\operatorname {rank} (B^{*})=k.$

In the other direction, suppose $M$ is positive semidefinite. Since $M$ is Hermitian, it has an [eigendecomposition](https://en.wikipedia.org/wiki/Eigendecomposition_of_a_matrix#Decomposition_for_special_matrices) $M=Q^{-1}DQ$ where $Q$ is [unitary](https://en.wikipedia.org/wiki/Unitary_matrix) and $D$ is a diagonal matrix whose entries are the eigenvalues of $M$ Since $M$ is positive semidefinite, the eigenvalues are non-negative real numbers, so one can define $D^{\frac {1}{2}}$ as the diagonal matrix whose entries are non-negative square roots of eigenvalues. Then $M=Q^{-1}DQ=Q^{*}DQ=Q^{*}D^{\frac {1}{2}}D^{\frac {1}{2}}Q=Q^{*}D^{{\frac {1}{2}}*}D^{\frac {1}{2}}Q=B^{*}B$ for $B=D^{\frac {1}{2}}Q.$ If moreover $M$ is positive definite, then the eigenvalues are (strictly) positive, so $D^{\frac {1}{2}}$ is invertible, and hence $B=D^{\frac {1}{2}}Q$ is invertible as well. If $M$ has rank $k,$ then it has exactly $k$ positive eigenvalues and the others are zero, hence in $B=D^{\frac {1}{2}}Q$ all but $k$ rows are all zeroed. Cutting the zero rows gives a $k\times n$ matrix $B'$ such that $B'^{*}B'=B^{*}B=M.$

The columns $b_{1},\dots ,b_{n}$ of $B$ can be seen as vectors in the [complex](https://en.wikipedia.org/wiki/Complex_vector_space) or [real vector space](https://en.wikipedia.org/wiki/Real_vector_space) $\mathbb {R} ^{k},$ respectively. Then the entries of $M$ are [inner products](https://en.wikipedia.org/wiki/Inner_product) (that is [dot products](https://en.wikipedia.org/wiki/Dot_product), in the real case) of these vectors 

$$
M_{ij}=\langle b_{i},b_{j}\rangle .
$$

 In other words, a Hermitian matrix $M$ is positive semidefinite if and only if it is the [Gram matrix](https://en.wikipedia.org/wiki/Gram_matrix) of some vectors $b_{1},\dots ,b_{n}.$ It is positive definite if and only if it is the Gram matrix of some [linearly independent](https://en.wikipedia.org/wiki/Linearly_independent) vectors. In general, the rank of the Gram matrix of vectors $b_{1},\dots ,b_{n}$ equals the dimension of the space [spanned](https://en.wikipedia.org/wiki/Linear_span) by these vectors.

### Uniqueness up to unitary transformations

The decomposition is not unique: if $M=B^{*}B$ for some $k\times n$ matrix $B$ and if $Q$ is any [unitary](https://en.wikipedia.org/wiki/Unitary_matrix) $k\times k$ matrix (meaning $Q^{*}Q=QQ^{*}=I$), then $M=B^{*}B=B^{*}Q^{*}QB=A^{*}A$ for $A=QB.$

However, this is the only way in which two decompositions can differ: The decomposition is unique up to [unitary transformations](https://en.wikipedia.org/wiki/Unitary_transformation). More formally, if $A$ is a $k\times n$ matrix and $B$ is a $\ell \times n$ matrix such that $A^{*}A=B^{*}B,$ then there is a $\ell \times k$ matrix $Q$ with orthonormal columns (meaning $Q^{*}Q=I_{k\times k}$) such that $B=QA.$ When $\ell =k$ this means $Q$ is [unitary](https://en.wikipedia.org/wiki/Unitary_matrix).

This statement has an intuitive geometric interpretation in the real case: let the columns of $A$ and $B$ be the vectors $a_{1},\dots ,a_{n}$ and $b_{1},\dots ,b_{n}$ in $\mathbb {R} ^{k}.$ A real unitary matrix is an [orthogonal matrix](https://en.wikipedia.org/wiki/Orthogonal_matrix), which describes a [rigid transformation](https://en.wikipedia.org/wiki/Rigid_transformation) (an isometry of Euclidean space $\mathbb {R} ^{k}$) preserving the 0 point (i.e. [rotations](https://en.wikipedia.org/wiki/Rotation_matrix) and [reflections](https://en.wikipedia.org/wiki/Reflection_matrix), without translations). Therefore, the dot products $a_{i}\cdot a_{j}$ and $b_{i}\cdot b_{j}$ are equal if and only if some rigid transformation of $\mathbb {R} ^{k}$ transforms the vectors $a_{1},\dots ,a_{n}$ to $b_{1},\dots ,b_{n}$ (and 0 to 0).

### Square root

A Hermitian matrix $M$ is positive semidefinite if and only if there is a positive semidefinite matrix $B$ (in particular $B$ is Hermitian, so $B^{*}=B$) satisfying $M=BB.$ This matrix $B$ is unique, is called the *non-negative [square root](https://en.wikipedia.org/wiki/Square_root_of_a_matrix)* of $M,$ and is denoted with $B=M^{\frac {1}{2}}.$ When $M$ is positive definite, so is $M^{\frac {1}{2}},$ hence it is also called the *positive square root* of $M.$

The non-negative square root should not be confused with other decompositions $M=B^{*}B.$ Some authors use the name *square root* and $M^{\frac {1}{2}}$ for any such decomposition, or specifically for the [[Cholesky Decomposition]], or any decomposition of the form $M=BB;$ others only use it for the non-negative square root.

If $M\succ N\succ 0$ then $M^{\frac {1}{2}}\succ N^{\frac {1}{2}}\succ 0.$

### Cholesky decomposition

A Hermitian positive semidefinite matrix $M$ can be written as $M=LL^{*},$ where $L$ is lower triangular with non-negative diagonal (equivalently $M=B^{*}B$ where $B=L^{*}$ is upper triangular); this is the [[Cholesky Decomposition]]. If $M$ is positive definite, then the diagonal of $L$ is positive and the Cholesky decomposition is unique. Conversely if $L$ is lower triangular with nonnegative diagonal then $LL^{*}$ is positive semidefinite. The Cholesky decomposition is especially useful for efficient numerical calculations. A closely related decomposition is the [[Cholesky Decomposition|LDL decomposition]], $M=LDL^{*},$ where $D$ is diagonal and $L$ is [lower unitriangular](https://en.wikipedia.org/wiki/Triangular_matrix#Unitriangular_matrix).

### Williamson theorem

Any $2n\times 2n$ positive definite Hermitian real matrix $M$ can be diagonalized via symplectic (real) matrices. More precisely, [Williamson's theorem](https://en.wikipedia.org/wiki/Williamson_theorem) ensures the existence of symplectic $S\in \mathbf {Sp} (2n,\mathbb {R} )$ and diagonal real positive $D\in \mathbb {R} ^{n\times n}$ such that $SMS^{T}=D\oplus D$.

## Other characterizations

Let $M$ be an $n\times n$ [real symmetric matrix](https://en.wikipedia.org/wiki/Hermitian_matrix), and let $B_{1}(M)\equiv \{\mathbf {x} \in \mathbb {R} ^{n}:\mathbf {x} ^{\mathsf {T}}M\mathbf {x} \leq 1\}$ be the "unit ball" defined by $M.$ Then we have the following

- $B_{1}(\mathbf {v} \mathbf {v} ^{\mathsf {T}})$ is a solid slab sandwiched between $\pm \{\mathbf {w} :\langle \mathbf {w} ,\mathbf {v} \rangle =1\}.$
- $M\succeq 0$ if and only if $B_{1}(M)$ is an ellipsoid, or an ellipsoidal cylinder.
- $M\succ 0$ if and only if $B_{1}(M)$ is bounded, that is, it is an ellipsoid.
- If $N\succ 0,$ then $M\succeq N$ if and only if $B_{1}(M)\subseteq B_{1}(N);$ $M\succ N$ if and only if $B_{1}(M)\subseteq \operatorname {int} {\bigl (}B_{1}(N){\bigr )}.$
- If $N\succ 0,$ then $M\succeq {\frac {\mathbf {v} \mathbf {v} ^{\mathsf {T}}}{\mathbf {v} ^{\mathsf {T}}N\mathbf {v} }}$ for all $v\neq 0$ if and only if $B_{1}(M)\subset \bigcap _{\mathbf {v} ^{\mathsf {T}}N\mathbf {v} =1}B_{1}(\mathbf {v} \mathbf {v} ^{\mathsf {T}}).$ So, since the polar dual of an ellipsoid is also an ellipsoid with the same principal axes, with inverse lengths, we have 

$$
B_{1}(N^{-1})=\bigcap _{\mathbf {v} ^{\mathsf {T}}N\mathbf {v} =1}B_{1}(\mathbf {v} \mathbf {v} ^{\mathsf {T}})=\bigcap _{\mathbf {v} ^{\mathsf {T}}N\mathbf {v} =1}\{\mathbf {w} :|\langle \mathbf {w} ,\mathbf {v} \rangle |\leq 1\}.
$$

 That is, if $N$ is positive-definite, then $M\succeq {\frac {\mathbf {v} \mathbf {v} ^{\mathsf {T}}}{\mathbf {v} ^{\mathsf {T}}N\mathbf {v} }}$ for all $\mathbf {v} \neq \mathbf {0}$ if and only if $M\succeq N^{-1}.$

Let $M$ be an $n\times n$ [Hermitian matrix](https://en.wikipedia.org/wiki/Hermitian_matrix). The following properties are equivalent to $M$ being positive definite:

The associated sesquilinear form is an inner product  
The [sesquilinear form](https://en.wikipedia.org/wiki/Sesquilinear_form) defined by $M$ is the function $\langle \cdot ,\cdot \rangle$ from $\mathbb {C} ^{n}\times \mathbb {C} ^{n}$ to $\mathbb {C} ^{n}$ such that $\langle \mathbf {x} ,\mathbf {y} \rangle \equiv \mathbf {y} ^{*}M\mathbf {x}$ for all $\mathbf {x}$ and $\mathbf {y}$ in $\mathbb {C} ^{n},$ where $\mathbf {y} ^{*}$ is the conjugate transpose of $\mathbf {y} .$ For any complex matrix $M,$ this form is linear in $x$ and semilinear in $\mathbf {y} .$ Therefore, the form is an [inner product](https://en.wikipedia.org/wiki/Inner_product) on $\mathbb {C} ^{n}$ if and only if $\langle \mathbf {z} ,\mathbf {z} \rangle$ is real and positive for all nonzero $\mathbf {z} ;$ that is if and only if $M$ is positive definite. (In fact, every inner product on $\mathbb {C} ^{n}$ arises in this fashion from a Hermitian positive definite matrix.)

Its leading principal minors are all positive  
The kth [leading principal minor](https://en.wikipedia.org/wiki/Minor_(linear_algebra) "Minor (linear algebra)") of a matrix $M$ is the [[Determinant]] of its upper-left $k\times k$ sub-matrix. It turns out that a matrix is positive definite if and only if all these determinants are positive. This condition is known as [Sylvester's criterion](https://en.wikipedia.org/wiki/Sylvester%27s_criterion), and provides an efficient test of positive definiteness of a symmetric real matrix. Namely, the matrix is reduced to an [upper triangular matrix](https://en.wikipedia.org/wiki/Upper_triangular_matrix) by using [elementary row operations](https://en.wikipedia.org/wiki/Elementary_row_operations), as in the first part of the [Gaussian elimination](https://en.wikipedia.org/wiki/Gaussian_elimination) method, taking care to preserve the sign of its determinant during [pivoting](https://en.wikipedia.org/wiki/Pivot_element) process. Since the kth leading principal minor of a triangular matrix is the product of its diagonal elements up to row $k,$ Sylvester's criterion is equivalent to checking whether its diagonal elements are all positive. This condition can be checked each time a new row $k$ of the triangular matrix is obtained.

A positive semidefinite matrix is positive definite if and only if it is [invertible](https://en.wikipedia.org/wiki/Invertible_matrix). A matrix $M$ is negative (semi)definite if and only if $-M$ is positive (semi)definite.

## Quadratic forms

The (purely) [quadratic form](https://en.wikipedia.org/wiki/Quadratic_form) associated with a real $n\times n$ matrix $M$ is the function $Q:\mathbb {R} ^{n}\to \mathbb {R}$ such that $Q(\mathbf {x} )=\mathbf {x} ^{\mathsf {T}}M\mathbf {x}$ for all $\mathbf {x} .$ $M$ can be assumed symmetric by replacing it with ${\tfrac {1}{2}}\left(M+M^{\mathsf {T}}\right),$ since any asymmetric part will be zeroed-out in the double-sided product.

A symmetric matrix $M$ is positive definite if and only if its quadratic form is a [strictly convex function](https://en.wikipedia.org/wiki/Strictly_convex_function).

More generally, any [quadratic function](https://en.wikipedia.org/wiki/Quadratic_function) from $\mathbb {R} ^{n}$ to $\mathbb {R}$ can be written as $\mathbf {x} ^{\mathsf {T}}M\mathbf {x} +\mathbf {b} ^{\mathsf {T}}\mathbf {x} +c$ where $M$ is a symmetric $n\times n$ matrix, $\mathbf {b}$ is a real n vector, and $c$ a real constant. In the $n=1$ case, this is a parabola, and just like in the $n=1$ case, we have

**Theorem:** This quadratic function is strictly convex, and hence has a unique finite global minimum, if and only if $M$ is positive definite.

**Proof:** If $M$ is positive definite, then the function is strictly convex. Its gradient is zero at the unique point of $M^{-1}\mathbf {b} ,$ which must be the global minimum since the function is strictly convex. If $M$ is not positive definite, then there exists some vector $\mathbf {v}$ such that $\mathbf {v} ^{\mathsf {T}}M\mathbf {v} \leq 0,$ so the function $f(t)\equiv (t\mathbf {v} )^{\mathsf {T}}M(t\mathbf {v} )+b^{\mathsf {T}}(t\mathbf {v} )+c$ is a line or a downward parabola, thus not strictly convex and not having a global minimum.

For this reason, positive definite matrices play an important role in [optimization](https://en.wikipedia.org/wiki/Optimization_(mathematics)) problems.

## Simultaneous diagonalization

One symmetric matrix and another matrix that is both symmetric and positive definite can be [simultaneously diagonalized](https://en.wikipedia.org/wiki/Diagonalizable_matrix#Simultaneous_diagonalization). This is so although simultaneous diagonalization is not necessarily performed with a [similarity transformation](https://en.wikipedia.org/wiki/Matrix_similarity). This result does not extend to the case of three or more matrices. In this section we write for the real case. Extension to the complex case is immediate.

Let $M$ be a symmetric and $N$ a symmetric and positive definite matrix. Write the generalized eigenvalue equation as $\left(M-\lambda N\right)\mathbf {x} =0$ where we impose that $\mathbf {x}$ be normalized, i.e. $\mathbf {x} ^{\mathsf {T}}N\mathbf {x} =1.$ Now we use [[Cholesky Decomposition]] to write the inverse of $N$ as $Q^{\mathsf {T}}Q.$ Multiplying by $Q$ and letting $\mathbf {x} =Q^{\mathsf {T}}\mathbf {y} ,$ we get $Q\left(M-\lambda N\right)Q^{\mathsf {T}}\mathbf {y} =0,$ which can be rewritten as $\left(QMQ^{\mathsf {T}}\right)\mathbf {y} =\lambda \mathbf {y}$ where $\mathbf {y} ^{\mathsf {T}}\mathbf {y} =1.$ Manipulation now yields $MX=NX\Lambda$ where $X$ is a matrix having as columns the generalized eigenvectors and $\Lambda$ is a diagonal matrix of the generalized eigenvalues. Now premultiplication with $X^{\mathsf {T}}$ gives the final result: $X^{\mathsf {T}}MX=\Lambda$ and $X^{\mathsf {T}}NX=I,$ but note that this is no longer an orthogonal diagonalization with respect to the inner product where $\mathbf {y} ^{\mathsf {T}}\mathbf {y} =1.$ In fact, we diagonalized $M$ with respect to the inner product induced by $N.$

Note that this result does not contradict what is said on simultaneous diagonalization in the article [Diagonalizable matrix](https://en.wikipedia.org/wiki/Diagonalizable_matrix#Simultaneous_diagonalization), which refers to simultaneous diagonalization by a similarity transformation. Our result here is more akin to a simultaneous diagonalization of two quadratic forms, and is useful for optimization of one form under conditions on the other.

## Properties

### Induced partial ordering

For arbitrary square matrices $M,$ $N$ we write $M\geq N$ if $M-N\geq 0$ i.e., $M-N$ is positive semi-definite. This defines a [partial ordering](https://en.wikipedia.org/wiki/Partially_ordered_set) on the set of all square matrices. One can similarly define a strict partial ordering $M>N.$ The ordering is called the [Loewner order](https://en.wikipedia.org/wiki/Loewner_order).

### Inverse of positive definite matrix

Every positive definite matrix is [invertible](https://en.wikipedia.org/wiki/Invertible_matrix) and its inverse is also positive definite. If $M\geq N>0$ then $N^{-1}\geq M^{-1}>0.$ Moreover, by the [min-max theorem](https://en.wikipedia.org/wiki/Min-max_theorem), the kth largest eigenvalue of $M$ is greater than or equal to the kth largest eigenvalue of $N.$

### Scaling

If $M$ is positive definite and $r>0$ is a real number, then $rM$ is positive definite.

### Addition

- If $M$ and $N$ are positive-definite, then the sum $M+N$ is also positive-definite.
- If $M$ and $N$ are positive-semidefinite, then the sum $M+N$ is also positive-semidefinite.
- If $M$ is positive-definite and $N$ is positive-semidefinite, then the sum $M+N$ is also positive-definite.

### Multiplication

- If $M$ and $N$ are positive definite, then the products $MNM$ and $NMN$ are also positive definite. If $MN=NM,$ then $MN$ is also positive definite.
- If $M$ is positive semidefinite, then $A^{*}MA$ is positive semidefinite for any (possibly rectangular) matrix $A.$ If $M$ is positive definite and $A$ has full column rank, then $A^{*}MA$ is positive definite.

### Trace

The diagonal entries $m_{ii}$ of a positive-semidefinite matrix are real and non-negative. As a consequence the [trace](https://en.wikipedia.org/wiki/Trace_(linear_algebra) "Trace (linear algebra)"), $\operatorname {tr} (M)\geq 0.$ Furthermore, since every principal sub-matrix (in particular, 2-by-2) is positive semidefinite, 

$$
\left|m_{ij}\right|\leq {\sqrt {m_{ii}m_{jj}}}\quad \forall i,j
$$

 and thus, when $n\geq 1,$ 

$$
\max _{i,j}\left|m_{ij}\right|\leq \max _{i}m_{ii}
$$

An $n\times n$ Hermitian matrix $M$ is positive definite if it satisfies the following trace inequalities: 

$$
\operatorname {tr} (M)>0\quad \mathrm {and} \quad {\frac {(\operatorname {tr} (M))^{2}}{\operatorname {tr} (M^{2})}}>n-1.
$$

Another important result is that for any $M$ and $N$ positive-semidefinite matrices, $\operatorname {tr} (MN)\geq 0.$ This follows by writing $\operatorname {tr} (MN)=\operatorname {tr} (M^{\frac {1}{2}}NM^{\frac {1}{2}}).$ The matrix $M^{\frac {1}{2}}NM^{\frac {1}{2}}$ is positive-semidefinite and thus has non-negative eigenvalues, whose sum, the trace, is therefore also non-negative.

### Hadamard product

If $M,N\geq 0,$ although $MN$ is not necessary positive semidefinite, the [Hadamard product](https://en.wikipedia.org/wiki/Hadamard_product_(matrices) "Hadamard product (matrices)") is, $M\circ N\geq 0$ (this result is often called the [Schur product theorem](https://en.wikipedia.org/wiki/Schur_product_theorem)).

Regarding the Hadamard product of two positive semidefinite matrices $M=(m_{ij})\geq 0,$ $N\geq 0,$ there are two notable inequalities:

- Oppenheim's inequality: $\det(M\circ N)\geq \det(N)\prod \nolimits _{i}m_{ii}.$
- $\det(M\circ N)\geq \det(M)\det(N).$

### Kronecker product

If $M,N\geq 0,$ although $MN$ is not necessary positive semidefinite, the [[Kronecker Product]] $M\otimes N\geq 0.$

### Frobenius product

If $M,N\geq 0,$ although $MN$ is not necessary positive semidefinite, the [Frobenius inner product](https://en.wikipedia.org/wiki/Frobenius_inner_product) $M:N\geq 0$ (Lancaster–Tismenetsky, *The Theory of Matrices*, p. 218).

### Convexity

The set of positive semidefinite symmetric matrices is [convex](https://en.wikipedia.org/wiki/Convex_set). That is, if $M$ and $N$ are positive semidefinite, then for any $\alpha$ between 0 and 1, $\alpha M+\left(1-\alpha \right)N$ is also positive semidefinite. For any vector $\mathbf {x}$: 

$$
\mathbf {x} ^{\mathsf {T}}\left(\alpha M+\left(1-\alpha \right)N\right)\mathbf {x} =\alpha \mathbf {x} ^{\mathsf {T}}M\mathbf {x} +(1-\alpha )\mathbf {x} ^{\mathsf {T}}N\mathbf {x} \geq 0.
$$

This property guarantees that [semidefinite programming](https://en.wikipedia.org/wiki/Semidefinite_programming) problems converge to a globally optimal solution.

### Relation with cosine

The positive-definiteness of a matrix $A$ expresses that the angle $\theta$ between any vector $\mathbf {x}$ and its image $A\mathbf {x}$ is always $-\pi /2<\theta <+\pi /2:$

$$
\cos \theta ={\frac {\mathbf {x} ^{\mathsf {T}}A\mathbf {x} }{\lVert \mathbf {x} \rVert \lVert A\mathbf {x} \rVert }}={\frac {\langle \mathbf {x} ,A\mathbf {x} \rangle }{\lVert \mathbf {x} \rVert \lVert A\mathbf {x} \rVert }},\theta =\theta (\mathbf {x} ,A\mathbf {x} )\equiv {\widehat {\left(\mathbf {x} ,A\mathbf {x} \right)}}\equiv
$$

 the angle between $\mathbf {x}$ and $A\mathbf {x} .$

### Further properties

1.  If $M$ is a symmetric [Toeplitz matrix](https://en.wikipedia.org/wiki/Toeplitz_matrix), i.e. the entries $m_{ij}$ are given as a function of their absolute index differences: $m_{ij}=h(|i-j|),$ and the *strict* inequality $\sum _{j\neq 0}\left|h(j)\right|<h(0)$ holds, then $M$ is *strictly* positive definite.
2.  Let $M>0$ and $N$ Hermitian. If $MN+NM\geq 0$ (resp., $MN+NM>0$) then $N\geq 0$ (resp., $N>0$).
3.  If $M>0$ is real, then there is a $\delta >0$ such that $M>\delta I,$ where $I$ is the [identity matrix](https://en.wikipedia.org/wiki/Identity_matrix).
4.  If $M_{k}$ denotes the leading $k\times k$ minor, $\det \left(M_{k}\right)/\det \left(M_{k-1}\right)$ is the kth pivot during [[LU Decomposition]].
5.  A matrix is negative definite if its kth order leading [principal minor](https://en.wikipedia.org/wiki/Principal_minor) is negative when $k$ is odd, and positive when $k$ is even.
6.  If $M$ is a real positive definite matrix, then there exists a positive real number $m$ such that for every vector $\mathbf {v} ,$ $\mathbf {v} ^{\mathsf {T}}M\mathbf {v} \geq m\|\mathbf {v} \|_{2}^{2}.$
7.  A Hermitian matrix is positive semidefinite if and only if all of its principal minors are nonnegative. It is however not enough to consider the leading principal minors only, as is checked on the diagonal matrix with entries 0 and −1 .

### Block matrices and submatrices

A positive $2n\times 2n$ matrix may also be defined by [blocks](https://en.wikipedia.org/wiki/Block_matrix): 

$$
M={\begin{bmatrix}A&B\\C&D\end{bmatrix}}
$$

where each block is $n\times n,$ By applying the positivity condition, it immediately follows that $A$ and $D$ are hermitian, and $C=B^{*}.$

We have that $\mathbf {z} ^{*}M\mathbf {z} \geq 0$ for all complex $\mathbf {z} ,$ and in particular for $\mathbf {z} =[\mathbf {v} ,0]^{\mathsf {T}}.$ Then 

$$
{\begin{bmatrix}\mathbf {v} ^{*}&0\end{bmatrix}}{\begin{bmatrix}A&B\\B^{*}&D\end{bmatrix}}{\begin{bmatrix}\mathbf {v} \\0\end{bmatrix}}=\mathbf {v} ^{*}A\mathbf {v} \geq 0.
$$

A similar argument can be applied to $D,$ and thus we conclude that both $A$ and $D$ must be positive definite. The argument can be extended to show that any [principal submatrix](https://en.wikipedia.org/wiki/Matrix_(mathematics)#Submatrix "Matrix (mathematics)") of $M$ is itself positive definite.

Converse results can be proved with stronger conditions on the blocks, for instance, using the [Schur complement](https://en.wikipedia.org/wiki/Schur_complement#Conditions_for_positive_definiteness_and_semi-definiteness).

### Local extrema

A general [quadratic form](https://en.wikipedia.org/wiki/Quadratic_form) $f(\mathbf {x} )$ on $n$ real variables $x_{1},\ldots ,x_{n}$ can always be written as $\mathbf {x} ^{\mathsf {T}}M\mathbf {x}$ where $\mathbf {x}$ is the column vector with those variables, and $M$ is a symmetric real matrix. Therefore, the matrix being positive definite means that $f$ has a unique minimum (zero) when $\mathbf {x}$ is zero, and is strictly positive for any other $\mathbf {x} .$

More generally, a twice-differentiable real function $f$ on $n$ real variables has local minimum at arguments $x_{1},\ldots ,x_{n}$ if its [gradient](https://en.wikipedia.org/wiki/Gradient) is zero and its [[Hessian Matrix|Hessian]] (the matrix of all second derivatives) is positive semi-definite at that point. Similar statements can be made for negative definite and semi-definite matrices.

### Covariance

In [statistics](https://en.wikipedia.org/wiki/Statistics), the [covariance matrix](https://en.wikipedia.org/wiki/Covariance_matrix) of a [multivariate probability distribution](https://en.wikipedia.org/wiki/Multivariate_probability_distribution) is always positive semi-definite; and it is positive definite unless one variable is an exact linear function of the others. Conversely, every positive semi-definite matrix is the covariance matrix of some multivariate distribution.

## Extension for non-Hermitian square matrices

The definition of positive definite can be generalized by designating any complex matrix $M$ (e.g. real non-symmetric) as positive definite if ${\mathcal {R_{e}}}\left\{\mathbf {z} ^{*}M\mathbf {z} \right\}>0$ for all non-zero complex vectors $\mathbf {z} ,$ where ${\mathcal {R_{e}}}\{c\}$ denotes the real part of a [complex number](https://en.wikipedia.org/wiki/Complex_number) $c.$ Only the Hermitian part ${\frac {1}{2}}\left(M+M^{*}\right)$ determines whether the matrix is positive definite, and is assessed in the narrower sense above. Similarly, if $\mathbf {x}$ and $M$ are real, we have $\mathbf {x} ^{\mathsf {T}}M\mathbf {x} >0$ for all real nonzero vectors $\mathbf {x}$ if and only if the symmetric part ${\frac {1}{2}}\left(M+M^{\mathsf {T}}\right)$ is positive definite in the narrower sense. It is immediately clear that $\mathbf {x} ^{\mathsf {T}}M\mathbf {x} =\sum _{ij}x_{i}M_{ij}x_{j}$is insensitive to transposition of $M.$

A non-symmetric real matrix with only positive eigenvalues may have a symmetric part with negative eigenvalues, in which case it will not be positive (semi)definite. For example, the matrix $M=\left[{\begin{smallmatrix}4&9\\1&4\end{smallmatrix}}\right]$ has positive eigenvalues 1 and 7, yet $\mathbf {x} ^{\mathsf {T}}M\mathbf {x} =-2$ with the choice $\mathbf {x} =\left[{\begin{smallmatrix}-1\\1\end{smallmatrix}}\right]$.

In summary, the distinguishing feature between the real and complex case is that, a [bounded](https://en.wikipedia.org/wiki/Bounded_operator) positive operator on a complex Hilbert space is necessarily Hermitian, or self adjoint. The general claim can be argued using the [polarization identity](https://en.wikipedia.org/wiki/Polarization_identity). That is no longer true in the real case.

## Applications

### Heat conductivity matrix

Fourier's law of heat conduction, giving heat flux $\mathbf {q}$ in terms of the temperature gradient $\mathbf {g} =\nabla T$ is written for anisotropic media as $\mathbf {q} =-K\mathbf {g} ,$ in which $K$ is the [thermal conductivity](https://en.wikipedia.org/wiki/Thermal_conductivity) matrix. The negative is inserted in Fourier's law to reflect the expectation that heat will always flow from hot to cold. In other words, since the temperature gradient $\mathbf {g}$ always points from cold to hot, the heat flux $\mathbf {q}$ is expected to have a negative inner product with $\mathbf {g}$ so that $\mathbf {q} ^{\mathsf {T}}\mathbf {g} <0.$ Substituting Fourier's law then gives this expectation as $\mathbf {g} ^{\mathsf {T}}K\mathbf {g} >0,$ implying that the conductivity matrix should be positive definite. Ordinarily $K$ should be symmetric, however it becomes nonsymmetric in the presence of a magnetic field as in a [thermal Hall effect](https://en.wikipedia.org/wiki/Thermal_Hall_effect).

More generally in thermodynamics, the flow of heat and particles is a fully coupled system as described by the [Onsager reciprocal relations](https://en.wikipedia.org/wiki/Onsager_reciprocal_relations), and the coupling matrix is required to be positive semi-definite (possibly non-symmetric) in order that entropy production be nonnegative.

## See also

- [Covariance matrix](https://en.wikipedia.org/wiki/Covariance_matrix)
- [M-matrix](https://en.wikipedia.org/wiki/M-matrix)
- [Positive-definite function](https://en.wikipedia.org/wiki/Positive-definite_function)
- [Positive-definite kernel](https://en.wikipedia.org/wiki/Positive-definite_kernel)
- [Schur complement](https://en.wikipedia.org/wiki/Schur_complement)
- [Sylvester's criterion](https://en.wikipedia.org/wiki/Sylvester%27s_criterion)
- [Numerical range](https://en.wikipedia.org/wiki/Numerical_range)
- [Williamson theorem](https://en.wikipedia.org/wiki/Williamson_theorem)

## References

1.  van den Bos, Adriaan (March 2007). ["Appendix C: Positive semidefinite and positive definite matrices"](https://www.doi.org/10.1002/9780470173862.app3). *Parameter Estimation for Scientists and Engineers* (.pdf) (online ed.). John Wiley & Sons. pp. 259–263. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1002/9780470173862](https://doi.org/10.1002%2F9780470173862). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-047-017386-2](https://en.wikipedia.org/wiki/Special:BookSources/978-047-017386-2). Print ed. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780470147818](https://en.wikipedia.org/wiki/Special:BookSources/9780470147818)
2.  Boyd, Stephen; Vandenberghe, Lieven (8 March 2004). *Convex Optimization*. Cambridge University Press. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1017/cbo9780511804441](https://doi.org/10.1017%2Fcbo9780511804441). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-83378-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-83378-3).
3.  , p. 440, Theorem 7.2.7
4.  , p. 441, Theorem 7.2.10
5.  , p. 452, Theorem 7.3.11
6.  , p. 439, Theorem 7.2.6 with $k=2$
7.  , p. 431, Corollary 7.1.7
8.  , p. 485, Theorem 7.6.1
9.  , p. 438, Theorem 7.2.1
10. , p. 495, Corollary 7.7.4(a)
11. ^   , p. 430, Observation 7.1.3
12. , p. 431, Observation 7.1.8
13. , p. 430
14. Wolkowicz, Henry; Styan, George P.H. (1980). "Bounds for Eigenvalues using Traces". *Linear Algebra and Its Applications*. **29** (29). Elsevier: 471–506. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/0024-3795(80)90258-X](https://doi.org/10.1016%2F0024-3795%2880%2990258-X).
15. , p. 479, Theorem 7.5.3
16. , p. 509, Theorem 7.8.16
17. Styan, G.P. (1973). "Hadamard products and multivariate statistical analysis". *[Linear Algebra and Its Applications](https://en.wikipedia.org/wiki/Linear_Algebra_and_Its_Applications)*. **6**: 217–240. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/0024-3795(73)90023-2](https://doi.org/10.1016%2F0024-3795%2873%2990023-2)., Corollary 3.6, p. 227
18. Bhatia, Rajendra (2007). *Positive Definite Matrices*. Princeton, New Jersey: Princeton University Press. p. 8. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-691-12918-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-691-12918-1).
19. Weisstein, Eric W. ["Positive definite matrix"](http://mathworld.wolfram.com/PositiveDefiniteMatrix.html). *MathWorld*. Wolfram Research. Retrieved 26 July 2012.

## Sources

- Horn, Roger A.; Johnson, Charles R. (2013). *Matrix Analysis* (2nd ed.). [Cambridge University Press](https://en.wikipedia.org/wiki/Cambridge_University_Press). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-54823-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-54823-6).
- [Bhatia, Rajendra](https://en.wikipedia.org/wiki/Rajendra_Bhatia) (2007). *Positive Definite Matrices*. Princeton Series in Applied Mathematics. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-691-12918-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-691-12918-1).
- Bernstein, B.; Toupin, R.A. (1962). "Some properties of the Hessian matrix of a strictly convex function". *[Journal für die reine und angewandte Mathematik](https://en.wikipedia.org/wiki/Journal_f%C3%BCr_die_reine_und_angewandte_Mathematik)*. **210**: 67–72. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1515/crll.1962.210.65](https://doi.org/10.1515%2Fcrll.1962.210.65).

## External links

- ["Positive-definite form"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society), 2001 \[1994\]
- ["Positive definite matrix"](http://mathworld.wolfram.com/PositiveDefiniteMatrix.html). *Wolfram MathWorld*. Wolfram Research.
