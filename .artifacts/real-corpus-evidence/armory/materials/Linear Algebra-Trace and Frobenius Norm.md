[[linear-algebra.base]]

> Source: [Matrix norm](https://en.wikipedia.org/wiki/Matrix_norm)
> License: Wikipedia content is available under CC BY-SA 4.0.

In the field of [mathematics](https://en.wikipedia.org/wiki/Mathematics), [norms](https://en.wikipedia.org/wiki/Vector_norm) are defined for elements within a [[Vector Space]]. Specifically, when the vector space comprises matrices, such norms are referred to as **matrix norms**. Matrix norms differ from vector norms in that they must also interact with [[Matrix Multiplication|matrix multiplication.]]

## Preliminaries

Given a [field](https://en.wikipedia.org/wiki/Field_(mathematics) "Field (mathematics)") $\ K\$ of either [real](https://en.wikipedia.org/wiki/Real_number) or [complex numbers](https://en.wikipedia.org/wiki/Complex_number) (or any complete subset thereof), let $\ K^{m\times n}\$ be the K-[[Vector Space]] of matrices with $m$ rows and $n$ columns and entries in the field $\ K~.$ A matrix norm is a [norm](https://en.wikipedia.org/wiki/Norm_(mathematics) "Norm (mathematics)") on $\ K^{m\times n}~.$

Norms are often expressed with [double vertical bars](https://en.wikipedia.org/wiki/Double_vertical_bar) (like so: $\ \|A\|\$). Thus, the matrix norm is a [function](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)") $\ \|\cdot \|:K^{m\times n}\to \mathbb {R} ^{0+}\$ that must satisfy the following properties:

For all scalars $\ \alpha \in K\$ and matrices $\ A,B\in K^{m\times n}\ ,$

- $\|A\|\geq 0\$ (*positive-valued*)
- $\|A\|=0\iff A=0_{m,n}$ (*definite*)
- $\left\|\alpha \ A\right\|=\left|\alpha \right|\ \left\|A\right\|\$ (*absolutely homogeneous*)
- $\|A+B\|\leq \|A\|+\|B\|\$ (*sub-additive* or satisfying the *triangle inequality*)

The only feature distinguishing matrices from rearranged vectors is [[Matrix Multiplication|multiplication]]. Matrix norms are particularly useful if they are also **sub-multiplicative**:

- $\ \left\|AB\right\|\leq \left\|A\right\|\left\|B\right\|\$

Every norm on $\ K^{n\times n}\$ can be rescaled to be sub-multiplicative; in some books, the terminology *matrix norm* is reserved for sub-multiplicative norms.

## Unitary invariance

A matrix norm is called unitarily invariant if for all unitary matrices $U,V$ and matrix $A$, $\lVert UAV\rVert =\lVert A\rVert$.

A symmetric gauge function is an absolute [vector norm](https://en.wikipedia.org/wiki/Vector_norm) $\phi :\mathbb {C} ^{p}\to \mathbb {R} ^{+}$ such that $\phi (Px)=\phi (x)$ for any [permutation matrix](https://en.wikipedia.org/wiki/Permutation_matrix) $P$. That is:

- **Non-negativity:** $\phi (x)\geq 0$, and $\phi (x)=0$ if and only if $x=0$.
- **Positive homogeneity:** $\phi (\alpha x)=|\alpha |\phi (x)$ for any real number $\alpha$.
- **Triangle inequality:** $\phi (x+y)\leq \phi (x)+\phi (y)$.
- **Symmetry:** $\phi (Px)=\phi (x)$ for any permutation matrix $P$.

A norm is a unitarily invariant matrix norm [if and only if](https://en.wikipedia.org/wiki/If_and_only_if) it is a symmetric gauge function on the vector of singular values. 

## Matrix norms induced by vector norms

Suppose a [vector norm](https://en.wikipedia.org/wiki/Vector_norm) $\|\cdot \|_{\alpha }$ on $K^{n}$ and a vector norm $\|\cdot \|_{\beta }$ on $K^{m}$ are given. Any $m\times n$ matrix A induces a linear operator from $K^{n}$ to $K^{m}$ with respect to the standard basis, and one defines the corresponding *induced norm* or *[operator norm](https://en.wikipedia.org/wiki/Operator_norm)* or *subordinate norm* on the space $K^{m\times n}$ of all $m\times n$ matrices as follows: 

$$
\|A\|_{\alpha ,\beta }=\sup\{\|Ax\|_{\beta }:x\in K^{n}{\text{ such that }}\|x\|_{\alpha }\leq 1\}
$$

 where $\sup$ denotes the [supremum](https://en.wikipedia.org/wiki/Infimum_and_supremum). This norm measures how much the mapping induced by $A$ can stretch vectors. Depending on the vector norms $\|\cdot \|_{\alpha }$, $\|\cdot \|_{\beta }$ used, notation other than $\|\cdot \|_{\alpha ,\beta }$ can be used for the operator norm.

### Matrix norms induced by vector *p*-norms

If the [p-norm for vectors](https://en.wikipedia.org/wiki/Vector_norm#p-norm) ($1\leq p\leq \infty$) is used for both spaces $K^{n}$ and $K^{m},$ then the corresponding operator norm is: 

$$
\|A\|_{p}=\sup\{\|Ax\|_{p}:x\in K^{n}{\text{ such that }}\|x\|_{p}\leq 1\}.
$$

 These induced norms are different from the ["entry-wise"](#%22Entry-wise%22_matrix_norms) *p*-norms and the [Schatten *p*-norms](https://en.wikipedia.org/wiki/Schatten_norm) for matrices treated below, which are also usually denoted by $\|A\|_{p}.$

Geometrically speaking, one can imagine a *p*-norm unit ball $V_{p,n}=\{x\in K^{n}:\|x\|_{p}\leq 1\}$ in $K^{n}$, then apply the linear map $A$ to the ball. It would end up becoming a distorted convex shape $AV_{p,n}\subset K^{m}$, and $\|A\|_{p}$ measures the longest "radius" of the distorted convex shape. In other words, we must take a *p*-norm unit ball $V_{p,m}$ in $K^{m}$, then multiply it by at least $\|A\|_{p}$, in order for it to be large enough to contain $AV_{p,n}$.

#### *p* = 1 or ∞

When $\ p=1\ ,$ or $\ p=\infty \ ,$ we have simple formulas.

$$
\|A\|_{1}=\max _{1\leq j\leq n}\sum _{i=1}^{m}\left|a_{ij}\right|\ ,
$$

which is simply the maximum absolute column sum of the matrix. 

$$
\|A\|_{\infty }=\max _{1\leq i\leq m}\sum _{j=1}^{n}\left|a_{ij}\right|\ ,
$$

 which is simply the maximum absolute row sum of the matrix.

For example, for 

$$
A={\begin{bmatrix}-3&5&7\\~~2&6&4\\~~0&2&8\\\end{bmatrix}}\ ,
$$

 we have that 

$$
\|A\|_{1}=\max {\bigl \{}\ |{-3}|+2+0\ ,~5+6+2\ ,~7+4+8\ {\bigr \}}=\max {\bigl \{}\ 5\ ,~13\ ,~19\ {\bigr \}}=19\ ,
$$

$$
\|A\|_{\infty }=\max {\bigl \{}\ |{-3}|+5+7\ ,~2+6+4\ ,~0+2+8\ {\bigr \}}=\max {\bigl \{}\ 15\ ,~12\ ,~10\ {\bigr \}}=15~.
$$

#### Spectral norm (*p* = 2)

 When $p=2$ (the [Euclidean norm](https://en.wikipedia.org/wiki/Euclidean_norm) or $\ell _{2}$-norm for vectors), the induced matrix norm is the *spectral norm*. The two values do *not* coincide in infinite dimensions — see [Spectral radius](https://en.wikipedia.org/wiki/Spectral_radius) for further discussion. The spectral radius should not be confused with the spectral norm. The spectral norm of a matrix $A$ is the largest [singular value](https://en.wikipedia.org/wiki/Singular_value) of $A$, i.e., the square root of the largest [eigenvalue](https://en.wikipedia.org/wiki/Eigenvalue) of the matrix $A^{*}A,$ where $A^{*}$ denotes the [conjugate transpose](https://en.wikipedia.org/wiki/Conjugate_transpose) of $A$:

$$
\|A\|_{2}={\sqrt {\lambda _{\max }\left(A^{*}A\right)}}=\sigma _{\max }(A).
$$

where $\sigma _{\max }(A)$ represents the largest singular value of matrix $A.$

There are further properties:

- $\|A\|_{2}=\sup\{x^{*}Ay:x\in K^{m},y\in K^{n}{\text{ with }}\|x\|_{2}=\|y\|_{2}=1\}.$ Proved by the [Cauchy–Schwarz inequality](https://en.wikipedia.org/wiki/Cauchy%E2%80%93Schwarz_inequality).
- $\|A^{*}A\|_{2}=\|AA^{*}\|_{2}=\|A\|_{2}^{2}$. Proven by [[Singular Value Decomposition]] (SVD) on $A$.
- $\|A\|_{2}=\sigma _{\mathrm {max} }(A)\leq \|A\|_{\rm {F}}={\sqrt {\sum _{i}\sigma _{i}(A)^{2}}}$, where $\|A\|_{\textrm {F}}$ is the [Frobenius norm](#Frobenius_norm). Equality holds if and only if the matrix $A$ is a rank-one matrix or a zero matrix.
- Conversely, $\|A\|_{\textrm {F}}\leq \min(m,n)^{1/2}\|A\|_{2}$.

- $\|A\|_{2}={\sqrt {\rho (A^{*}A)}}\leq {\sqrt {\|A^{*}A\|_{\infty }}}\leq {\sqrt {\|A\|_{1}\|A\|_{\infty }}}$.

### Matrix norms induced by vector *α*- and *β*-norms

We can generalize the above definition. Suppose we have vector norms $\|\cdot \|_{\alpha }$ and $\|\cdot \|_{\beta }$ for spaces $K^{n}$ and $K^{m}$ respectively; the corresponding operator norm is 

$$
\|A\|_{\alpha ,\beta }=\sup\{\|Ax\|_{\beta }:x\in K^{n}{\text{ such that }}\|x\|_{\alpha }\leq 1\}
$$

 In particular, the $\|A\|_{p}$ defined previously is the special case of $\|A\|_{p,p}$.

In the special cases of $\alpha =2$ and $\beta =\infty$, the induced matrix norms can be computed by

$$
\|A\|_{2,\infty }=\max _{1\leq i\leq m}\|A_{i:}\|_{2},
$$

 where $A_{i:}$ is the i-th row of matrix $A$.

In the special cases of $\alpha =1$ and $\beta =2$, the induced matrix norms can be computed by

$$
\|A\|_{1,2}=\max _{1\leq j\leq n}\|A_{:j}\|_{2},
$$

 where $A_{:j}$ is the j-th column of matrix $A$.

Hence, $\|A\|_{2,\infty }$ and $\|A\|_{1,2}$ are the maximum row and column 2-norm of the matrix, respectively.

### Properties

Any operator norm is [consistent](#Consistent_and_compatible_norms) with the vector norms that induce it, giving 

$$
\|Ax\|_{\beta }\leq \|A\|_{\alpha ,\beta }\|x\|_{\alpha }.
$$

Suppose $\|\cdot \|_{\alpha ,\beta }$; $\|\cdot \|_{\beta ,\gamma }$; and $\|\cdot \|_{\alpha ,\gamma }$ are operator norms induced by the respective pairs of vector norms $(\|\cdot \|_{\alpha },\|\cdot \|_{\beta })$; $(\|\cdot \|_{\beta },\|\cdot \|_{\gamma })$; and $(\|\cdot \|_{\alpha },\|\cdot \|_{\gamma })$. Then,

$\|AB\|_{\alpha ,\gamma }\leq \|A\|_{\beta ,\gamma }\|B\|_{\alpha ,\beta };$

this follows from 

$$
\|ABx\|_{\gamma }\leq \|A\|_{\beta ,\gamma }\|Bx\|_{\beta }\leq \|A\|_{\beta ,\gamma }\|B\|_{\alpha ,\beta }\|x\|_{\alpha }
$$

 and 

$$
\sup _{\|x\|_{\alpha }=1}\|ABx\|_{\gamma }=\|AB\|_{\alpha ,\gamma }.
$$

### Square matrices

Suppose $\|\cdot \|_{\alpha ,\alpha }$ is an operator norm on the space of square matrices $K^{n\times n}$ induced by vector norms $\|\cdot \|_{\alpha }$ and $\|\cdot \|_{\alpha }$. Then, the operator norm is a sub-multiplicative matrix norm: 

$$
\|AB\|_{\alpha ,\alpha }\leq \|A\|_{\alpha ,\alpha }\|B\|_{\alpha ,\alpha }.
$$

Moreover, any such norm satisfies the inequality

|  |  |  |
|----|----|----|
| 

$$
(\|A^{r}\|_{\alpha ,\alpha })^{1/r}\geq \rho (A)
$$

 |  | 1 |

for all positive integers *r*, where *ρ*(*A*) is the [spectral radius](https://en.wikipedia.org/wiki/Spectral_radius) of A. For [symmetric](https://en.wikipedia.org/wiki/Symmetric_matrix) or [hermitian](https://en.wikipedia.org/wiki/Hermitian_matrix) A, we have equality in (**[1](#math_1)**) for the 2-norm, since in this case the 2-norm *is* precisely the spectral radius of A. For an arbitrary matrix, we may not have equality for any norm; a counterexample would be 

$$
A={\begin{bmatrix}0&1\\0&0\end{bmatrix}},
$$

 which has vanishing spectral radius. In any case, for any matrix norm, we have the [spectral radius formula](https://en.wikipedia.org/wiki/Spectral_radius#Gelfand's_formula): 

$$
\lim _{r\to \infty }\|A^{r}\|^{1/r}=\rho (A).
$$

### Energy norms

If the vector norms $\|\cdot \|_{\alpha }$ and $\|\cdot \|_{\beta }$ are given in terms of [energy norms](https://en.wikipedia.org/wiki/Norm_(mathematics)#Energy_norm "Norm (mathematics)") based on [symmetric](https://en.wikipedia.org/wiki/Symmetric_matrix) [positive definite](https://en.wikipedia.org/wiki/Definite_matrix) matrices $P$ and $Q$ respectively, the resulting operator norm is given as 

$$
\|A\|_{P,Q}=\sup\{\|Ax\|_{Q}:\|x\|_{P}\leq 1\}.
$$

Using the symmetric [matrix square roots](https://en.wikipedia.org/wiki/Square_root_of_a_matrix) of $P$ and $Q$ respectively, the operator norm can be expressed as the spectral norm of a modified matrix:

$$
\|A\|_{P,Q}=\|Q^{1/2}AP^{-1/2}\|_{2}.
$$

## Consistent and compatible norms

A matrix norm $\|\cdot \|$ on $K^{m\times n}$ is called *consistent* with a vector norm $\|\cdot \|_{\alpha }$ on $K^{n}$ and a vector norm $\|\cdot \|_{\beta }$ on $K^{m}$, if: 

$$
\left\|Ax\right\|_{\beta }\leq \left\|A\right\|\left\|x\right\|_{\alpha }
$$

 for all $A\in K^{m\times n}$ and all $x\in K^{n}$. In the special case of *m* = *n* and $\alpha =\beta$, $\|\cdot \|$ is also called *compatible* with $\|\cdot \|_{\alpha }$.

All induced norms are consistent by definition. Also, any sub-multiplicative matrix norm on $K^{n\times n}$ induces a compatible vector norm on $K^{n}$ by defining $\left\|v\right\|:=\left\|\left(v,v,\dots ,v\right)\right\|$.

## "Entry-wise" matrix norms

These norms treat an $m\times n$ matrix as a vector of size $m\cdot n$, and use one of the familiar vector norms. For example, using the *p*-norm for vectors, *p* ≥ 1, we get:

$\|A\|_{p,p}=\|\mathrm {vec} (A)\|_{p}=\left(\sum _{i=1}^{m}\sum _{j=1}^{n}|a_{ij}|^{p}\right)^{1/p}$

This is a different norm from the induced *p*-norm (see above) and the Schatten *p*-norm (see below), but the notation is the same.

The special case *p* = 2 is the Frobenius norm, and *p* = ∞ yields the maximum norm.

### *L*<sub>2,1</sub> and *L<sub>p,q</sub>* norms

Let $(a_{1},\ldots ,a_{n})$ be the dimension m columns of matrix $A$. From the original definition, the matrix $A$ presents n data points in an m-dimensional space. The $L_{2,1}$ norm is the sum of the Euclidean norms of the columns of the matrix:

$\|A\|_{2,1}=\sum _{j=1}^{n}\|a_{j}\|_{2}=\sum _{j=1}^{n}\left(\sum _{i=1}^{m}|a_{ij}|^{2}\right)^{1/2}$

The $L_{2,1}$ norm as an [error function](https://en.wikipedia.org/wiki/Error_function) is more robust, since the error for each data point (a column) is not squared. It is used in [robust data analysis](https://en.wikipedia.org/wiki/Robust_data_analysis) and [sparse coding](https://en.wikipedia.org/wiki/Sparse_coding).

For *p*, *q* ≥ 1, the $L_{2,1}$ norm can be generalized to the $L_{p,q}$ norm as follows:

$\|A\|_{p,q}=\left(\sum _{j=1}^{n}\left(\sum _{i=1}^{m}|a_{ij}|^{p}\right)^{\frac {q}{p}}\right)^{\frac {1}{q}}.$

### Frobenius norm

When *p* = *q* = 2 for the $L_{p,q}$ norm, it is called the **Frobenius norm** or the **Hilbert–Schmidt norm**, though the latter term is used more frequently in the context of operators on (possibly infinite-dimensional) [Hilbert space](https://en.wikipedia.org/wiki/Hilbert_space). This norm can be defined in various ways:

$\|A\|_{\text{F}}={\sqrt {\sum _{i}^{m}\sum _{j}^{n}|a_{ij}|^{2}}}={\sqrt {\operatorname {trace} \left(A^{*}A\right)}}={\sqrt {\sum _{i=1}^{\min\{m,n\}}\sigma _{i}^{2}(A)}},$

where the [trace](https://en.wikipedia.org/wiki/Trace_(matrix)) is the sum of diagonal entries, and $\sigma _{i}(A)$ are the [singular values](https://en.wikipedia.org/wiki/Singular_value) of $A$. The second equality is proven by explicit computation of $\mathrm {trace} (A^{*}A)$. The third equality is proven by [[Singular Value Decomposition]] of $A$, and the fact that the trace is invariant under circular shifts.

The Frobenius norm is an extension of the Euclidean norm to $K^{n\times n}$ and comes from the [Frobenius inner product](https://en.wikipedia.org/wiki/Frobenius_inner_product) on the space of all matrices.

The Frobenius norm is sub-multiplicative and is very useful for [numerical linear algebra](https://en.wikipedia.org/wiki/Numerical_linear_algebra). The sub-multiplicativity of Frobenius norm can be proved using the [Cauchy–Schwarz inequality](https://en.wikipedia.org/wiki/Cauchy%E2%80%93Schwarz_inequality). In fact, it is more than sub-multiplicative, as 

$$
\|AB\|_{F}\leq \|A\|_{op}\|B\|_{F}
$$

where the operator norm $\|\cdot \|_{op}\leq \|\cdot \|_{F}$.

Frobenius norm is often easier to compute than induced norms, and has the useful property of being invariant under [rotations](https://en.wikipedia.org/wiki/Rotation_matrix) (and [unitary](https://en.wikipedia.org/wiki/Unitary_operator) operations in general). That is, $\|A\|_{\text{F}}=\|AU\|_{\text{F}}=\|UA\|_{\text{F}}$ for any unitary matrix $U$. This property follows from the cyclic nature of the trace ($\operatorname {trace} (XYZ)=\operatorname {trace} (YZX)=\operatorname {trace} (ZXY)$):

$\|AU\|_{\text{F}}^{2}=\operatorname {trace} \left((AU)^{*}AU\right)=\operatorname {trace} \left(U^{*}A^{*}AU\right)=\operatorname {trace} \left(UU^{*}A^{*}A\right)=\operatorname {trace} \left(A^{*}A\right)=\|A\|_{\text{F}}^{2},$

and analogously:

$\|UA\|_{\text{F}}^{2}=\operatorname {trace} \left((UA)^{*}UA\right)=\operatorname {trace} \left(A^{*}U^{*}UA\right)=\operatorname {trace} \left(A^{*}A\right)=\|A\|_{\text{F}}^{2},$

where we have used the unitary nature of $U$ (that is, $U^{*}U=UU^{*}=\mathbf {I}$).

It also satisfies

$\|A^{*}A\|_{\text{F}}=\|AA^{*}\|_{\text{F}}\leq \|A\|_{\text{F}}^{2}$

and

$\|A+B\|_{\text{F}}^{2}=\|A\|_{\text{F}}^{2}+\|B\|_{\text{F}}^{2}+2\operatorname {Re} \left(\langle A,B\rangle _{\text{F}}\right),$

where $\langle A,B\rangle _{\text{F}}$ is the [Frobenius inner product](https://en.wikipedia.org/wiki/Frobenius_inner_product), and Re is the real part of a complex number (irrelevant for real matrices)

### Max norm

The **max norm** is the elementwise norm in the limit as *p* = *q* goes to infinity:

$\|A\|_{\max }=\max _{i,j}|a_{ij}|.$

This norm is not [sub-multiplicative](#Definition); but modifying the right-hand side to ${\sqrt {mn}}\max _{i,j}\vert a_{ij}\vert$ makes it so.

Note that in some literature (such as [Communication complexity](https://en.wikipedia.org/wiki/Communication_complexity)), an alternative definition of max-norm, also called the $\gamma _{2}$-norm, refers to the factorization norm:

$\gamma _{2}(A)=\min _{U,V:A=UV^{T}}\|U\|_{2,\infty }\|V\|_{2,\infty }=\min _{U,V:A=UV^{T}}\max _{i,j}\|U_{i,:}\|_{2}\|V_{j,:}\|_{2}$

## Schatten norms

The Schatten *p*-norms arise when applying the *p*-norm to the vector of [[Singular Value Decomposition|singular values]] of a matrix. If the singular values of the $m\times n$ matrix $A$ are denoted by *σ<sub>i</sub>*, then the Schatten *p*-norm is defined by

$\|A\|_{p}=\left(\sum _{i=1}^{\min\{m,n\}}\sigma _{i}^{p}(A)\right)^{1/p}.$

These norms again share the notation with the induced and entry-wise *p*-norms, but they are different.

All Schatten norms are sub-multiplicative. They are also unitarily invariant, which means that $\|A\|=\|UAV\|$ for all matrices $A$ and all [unitary matrices](https://en.wikipedia.org/wiki/Unitary_matrix) $U$ and $V$.

The most familiar cases are *p* = 1, 2, ∞. The case *p* = 2 yields the Frobenius norm, introduced before. The case *p* = ∞ yields the spectral norm, which is the operator norm induced by the vector 2-norm (see above). Finally, *p* = 1 yields the **nuclear norm** (also known as the *trace norm*, or the [[Singular Value Decomposition|Ky Fan]] 'n'-norm), defined as:

$\|A\|_{*}=\operatorname {trace} \left({\sqrt {A^{*}A}}\right)=\sum _{i=1}^{\min\{m,n\}}\sigma _{i}(A),$

where ${\sqrt {A^{*}A}}$ denotes a positive semidefinite matrix $B$ such that $BB=A^{*}A$. More precisely, since $A^{*}A$ is a [positive semidefinite matrix](https://en.wikipedia.org/wiki/Positive_semidefinite_matrix), its [square root](https://en.wikipedia.org/wiki/Square_root_of_a_matrix) is well defined. The nuclear norm $\|A\|_{*}$ is a [convex envelope](https://en.wikipedia.org/wiki/Convex_envelope) of the rank function ${\text{rank}}(A)$, so it is often used in [mathematical optimization](https://en.wikipedia.org/wiki/Mathematical_optimization) to search for low-rank matrices.

Combining [von Neumann's trace inequality](https://en.wikipedia.org/wiki/Von_Neumann%27s_trace_inequality) with [Hölder's inequality](https://en.wikipedia.org/wiki/H%C3%B6lder%27s_inequality) for Euclidean space yields a version of [Hölder's inequality](https://en.wikipedia.org/wiki/H%C3%B6lder%27s_inequality) for Schatten norms for $1/p+1/q=1$:

$\left|\operatorname {trace} (A^{*}B)\right|\leq \|A\|_{p}\|B\|_{q},$

In particular, this implies the Schatten norm inequality

$\|A\|_{F}^{2}\leq \|A\|_{p}\|A\|_{q}.$

## Monotone norms

A matrix norm $\|\cdot \|$ is called *monotone* if it is monotonic with respect to the [Loewner order](https://en.wikipedia.org/wiki/Loewner_order). Thus, a matrix norm is increasing if

$A\preccurlyeq B\Rightarrow \|A\|\leq \|B\|.$

The Frobenius norm and spectral norm are examples of monotone norms.

## Cut norms

Another source of inspiration for matrix norms arises from considering a matrix as the [adjacency matrix](https://en.wikipedia.org/wiki/Adjacency_matrix) of a [weighted](https://en.wikipedia.org/wiki/Weighted_graph), [directed graph](https://en.wikipedia.org/wiki/Directed_graph). The so-called "cut norm" measures how close the associated graph is to being [bipartite](https://en.wikipedia.org/wiki/Bipartite_graph): 

$$
\|A\|_{\Box }=\max _{S\subseteq [n],T\subseteq [m]}{\left|\sum _{s\in S,t\in T}{A_{t,s}}\right|}
$$

 where *A* ∈ *K*<sup>*m*×*n*</sup>. Equivalent definitions (up to a constant factor) impose the conditions 2\|*S*\| \> *n* & 2\|*T*\| \> *m*; *S* = *T*; or *S* ∩ *T* = ∅.

The cut-norm is equivalent to the induced operator norm ‖·‖<sub>∞→1</sub>, which is itself equivalent to another norm, called the [Grothendieck](https://en.wikipedia.org/wiki/Grothendieck_inequality) norm.

To define the Grothendieck norm, first note that a linear operator *K*<sup>1</sup> → *K*<sup>1</sup> is just a scalar, and thus extends to a linear operator on any *K<sup>k</sup>* → *K<sup>k</sup>*. Moreover, given any choice of basis for *K<sup>n</sup>* and *K<sup>m</sup>*, any linear operator *K<sup>n</sup>* → *K<sup>m</sup>* extends to a linear operator (*K*<sup>*k*</sup>)<sup>*n*</sup> → (*K*<sup>*k*</sup>)<sup>*m*</sup>, by letting each matrix element on elements of *K<sup>k</sup>* via [scalar multiplication](https://en.wikipedia.org/wiki/Scalar_multiplication). The Grothendieck norm is the norm of that extended operator; in symbols: 

$$
\|A\|_{G,k}=\sup _{{\text{each }}u_{j},v_{j}\in K^{k};\|u_{j}\|=\|v_{j}\|=1}{\sum _{j\in [n],\ell \in [m]}{(u_{j}\cdot v_{j})A_{\ell ,j}}}
$$

The Grothendieck norm depends on choice of basis (usually taken to be the [standard basis](https://en.wikipedia.org/wiki/Standard_basis)) and k.

## Equivalence of norms

For any two matrix norms $\|\cdot \|_{\alpha }$ and $\|\cdot \|_{\beta }$, we have that:

$r\|A\|_{\alpha }\leq \|A\|_{\beta }\leq s\|A\|_{\alpha }$

for some positive numbers *r* and *s*, for all matrices $A\in K^{m\times n}$. In other words, all norms on $K^{m\times n}$ are *equivalent*; they induce the same [topology](https://en.wikipedia.org/wiki/Topology_(structure)) on $K^{m\times n}$. This is true because the vector space $K^{m\times n}$ has the finite [dimension](https://en.wikipedia.org/wiki/Dimension_(mathematics)) $m\times n$.

Moreover, for every matrix norm $\|\cdot \|$ on $\mathbb {R} ^{n\times n}$ there exists a unique positive real number $k$ such that $\ell \|\cdot \|$ is a sub-multiplicative matrix norm for every $\ell \geq k$; to wit,

$k=\sup\{\Vert AB\Vert \,:\,\Vert A\Vert \leq 1,\Vert B\Vert \leq 1\}.$

A sub-multiplicative matrix norm $\|\cdot \|_{\alpha }$ is said to be *minimal*, if there exists no other sub-multiplicative matrix norm $\|\cdot \|_{\beta }$ satisfying $\|\cdot \|_{\beta }<\|\cdot \|_{\alpha }$.

### Examples of norm equivalence

Let $\|A\|_{p}$ once again refer to the norm induced by the vector *p*-norm (as above in the Induced norm section).

For matrix $A\in \mathbb {R} ^{m\times n}$ of [rank](https://en.wikipedia.org/wiki/Rank_(linear_algebra) "Rank (linear algebra)") $r$, the following inequalities hold:

- $\|A\|_{2}\leq \|A\|_{F}\leq {\sqrt {r}}\|A\|_{2}$
- $\|A\|_{F}\leq \|A\|_{*}\leq {\sqrt {r}}\|A\|_{F}$
- $\|A\|_{\max }\leq \|A\|_{2}\leq {\sqrt {mn}}\|A\|_{\max }$
- ${\frac {1}{\sqrt {n}}}\|A\|_{\infty }\leq \|A\|_{2}\leq {\sqrt {m}}\|A\|_{\infty }$
- ${\frac {1}{\sqrt {m}}}\|A\|_{1}\leq \|A\|_{2}\leq {\sqrt {n}}\|A\|_{1}.$

## See also

- [Dual norm](https://en.wikipedia.org/wiki/Dual_norm)
- [Logarithmic norm](https://en.wikipedia.org/wiki/Logarithmic_norm)

## Notes

1.  The condition only applies when the product is defined, such as the case of [square matrices](https://en.wikipedia.org/wiki/Square_matrix) ($\ m=n\$). More generally, multiplication of the matrices must be possible: $\ A\in K^{\ell \times m}\$ and $\ B\in K^{m\times n}~;$ further, the two norms $\ \|A\|\$ and $\ \|B\|\$ must either have the same definitions, only differing in the matrix dimensions, or two different types of norms that are none the less "consistent" (see below).

## References

1.  ^   Weisstein, Eric W. ["Matrix norm"](https://mathworld.wolfram.com/MatrixNorm.html). *mathworld.wolfram.com*. Retrieved 2020-08-24.
2.  ^     ["Matrix norms"](http://fourier.eng.hmc.edu/e161/lectures/algebra/node12.html). *fourier.eng.hmc.edu*. Retrieved 2020-08-24.
3.  Malek-Shahmirzadi, Massoud (1983). "A characterization of certain classes of matrix norms". *Linear and Multilinear Algebra*. **13** (2): 97–99. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/03081088308817508](https://doi.org/10.1080%2F03081088308817508). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0308-1087](https://search.worldcat.org/issn/0308-1087).
4.  ^   Horn, Roger A. (2012). *Matrix analysis*. Johnson, Charles R. (2nd ed.). Cambridge, UK: Cambridge University Press. pp. 340–341. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-139-77600-4](https://en.wikipedia.org/wiki/Special:BookSources/978-1-139-77600-4). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [817236655](https://search.worldcat.org/oclc/817236655).
5.  Carl D. Meyer, Matrix Analysis and Applied Linear Algebra, §5.2, p.281, Society for Industrial & Applied Mathematics, June 2000.
6.  Ding, Chris; Zhou, Ding; He, Xiaofeng; Zha, Hongyuan (June 2006). *R1-PCA: Rotational invariant L1-norm principal component analysis for robust subspace factorization*. 23rd International Conference on Machine Learning. ICML '06. Pittsburgh, PA: [Association for Computing Machinery](https://en.wikipedia.org/wiki/Association_for_Computing_Machinery). pp. 281–288. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1145/1143844.1143880](https://doi.org/10.1145%2F1143844.1143880). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [1-59593-383-2](https://en.wikipedia.org/wiki/Special:BookSources/1-59593-383-2).
7.  Fan, Ky. (1951). ["Maximum properties and inequalities for the eigenvalues of completely continuous operators"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1063464). *Proceedings of the National Academy of Sciences of the United States of America*. **37** (11): 760–766. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1951PNAS...37..760F](https://ui.adsabs.harvard.edu/abs/1951PNAS...37..760F). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1073/pnas.37.11.760](https://doi.org/10.1073%2Fpnas.37.11.760). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [1063464](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1063464). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [16578416](https://pubmed.ncbi.nlm.nih.gov/16578416).
8.  Ciarlet, Philippe G. (1989). *Introduction to numerical linear algebra and optimisation*. Cambridge, England: Cambridge University Press. p. 57. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0521327881](https://en.wikipedia.org/wiki/Special:BookSources/0521327881).
9.  ^   Frieze, Alan; Kannan, Ravi (1999-02-01). ["Quick Approximation to Matrices and Applications"](https://doi.org/10.1007/s004930050052). *Combinatorica*. **19** (2): 175–220. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s004930050052](https://doi.org/10.1007%2Fs004930050052). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1439-6912](https://search.worldcat.org/issn/1439-6912). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [15231198](https://api.semanticscholar.org/CorpusID:15231198).
10. ^   [Lovász László](https://en.wikipedia.org/wiki/L%C3%A1szl%C3%B3_Lov%C3%A1sz) (2012). "The cut distance". *Large Networks and Graph Limits*. AMS Colloquium Publications. Vol. 60. Providence, RI: American Mathematical Society. pp. 127–131. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8218-9085-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8218-9085-1). Note that Lovász rescales ‖*A*‖<sub>□</sub> to lie in \[0, 1\].
11. ^    [Alon, Noga](https://en.wikipedia.org/wiki/Noga_Alon); Naor, Assaf (2004-06-13). ["Approximating the cut-norm via Grothendieck's inequality"](https://doi.org/10.1145/1007352.1007371). *Proceedings of the thirty-sixth annual ACM symposium on Theory of computing*. STOC '04. Chicago, IL, USA: Association for Computing Machinery. pp. 72–80. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1145/1007352.1007371](https://doi.org/10.1145%2F1007352.1007371). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-58113-852-8](https://en.wikipedia.org/wiki/Special:BookSources/978-1-58113-852-8). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [1667427](https://api.semanticscholar.org/CorpusID:1667427).
12. [Golub, Gene](https://en.wikipedia.org/wiki/Gene_Golub); [Charles F. Van Loan](https://en.wikipedia.org/wiki/Charles_Van_Loan) (1996). Matrix Computations – Third Edition. Baltimore: The Johns Hopkins University Press, 56–57. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-8018-5413-X](https://en.wikipedia.org/wiki/Special:BookSources/0-8018-5413-X).
13. Roger Horn and Charles Johnson. *Matrix Analysis,* Chapter 5, Cambridge University Press, 1985. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-38632-2](https://en.wikipedia.org/wiki/Special:BookSources/0-521-38632-2).

## Bibliography

- [James W. Demmel](https://en.wikipedia.org/wiki/James_W._Demmel), Applied Numerical Linear Algebra, section 1.7, published by SIAM, 1997.
- Carl D. Meyer, Matrix Analysis and Applied Linear Algebra, published by SIAM, 2000. [1](https://en.wikipedia.org/wiki/1)(http://www.matrixanalysis.com)
- [John Watrous](https://en.wikipedia.org/wiki/John_Watrous_(computer_scientist) "John Watrous (computer scientist)"), Theory of Quantum Information, [2.3 Norms of operators](https://web.archive.org/web/20160304053759/https://cs.uwaterloo.ca/~watrous/CS766/LectureNotes/02.pdf), lecture notes, University of Waterloo, 2011.
