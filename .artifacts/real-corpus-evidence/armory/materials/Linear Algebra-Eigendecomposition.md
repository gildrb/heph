[[linear-algebra.base]]

> Source: [Eigendecomposition of a matrix](https://en.wikipedia.org/wiki/Eigendecomposition_of_a_matrix)
> License: Wikipedia content is available under CC BY-SA 4.0.

In [linear algebra](https://en.wikipedia.org/wiki/Linear_algebra), **eigendecomposition** is the [factorization](https://en.wikipedia.org/wiki/Matrix_factorization) of a [matrix](https://en.wikipedia.org/wiki/Matrix_(mathematics) "Matrix (mathematics)") into a [canonical form](https://en.wikipedia.org/wiki/Canonical_form), whereby the matrix is represented in terms of its [[Eigenvalues and Eigenvectors]]. Only [diagonalizable matrices](https://en.wikipedia.org/wiki/Diagonalizable_matrix) can be factorized in this way. When the matrix being factorized is a [normal](https://en.wikipedia.org/wiki/Normal_matrix) or real [symmetric matrix](https://en.wikipedia.org/wiki/Symmetric_matrix), the decomposition is called "spectral decomposition", derived from the [[Spectral Theorem]].

## Fundamental theory of matrix eigenvectors and eigenvalues

A (nonzero) vector **v** of dimension N is an eigenvector of a square *N* × *N* matrix **A** if it satisfies a [linear equation](https://en.wikipedia.org/wiki/Linear_equation) of the form 

$$
\mathbf {A} \mathbf {v} =\lambda \mathbf {v}
$$

 for some scalar λ. Then λ is called the eigenvalue corresponding to **v**. Geometrically speaking, the eigenvectors of **A** are the vectors that **A** merely elongates or shrinks, and the amount that they elongate/shrink by is the eigenvalue. The above equation is called the eigenvalue equation or the eigenvalue problem.

This yields an equation for the eigenvalues 

$$
p\left(\lambda \right)=\det \left(\mathbf {A} -\lambda \mathbf {I} \right)=0.
$$

 We call *p*(*λ*) the [characteristic polynomial](https://en.wikipedia.org/wiki/Characteristic_polynomial), and the equation, called the characteristic equation, is an Nth-order polynomial equation in the unknown λ. This equation will have N<sub>λ</sub> distinct solutions, where 1 ≤ *N<sub>λ</sub>* ≤ *N*. The set of solutions, that is, the eigenvalues, is called the [spectrum](https://en.wikipedia.org/wiki/Spectrum_of_a_matrix) of **A**.

If the field of scalars is [algebraically closed](https://en.wikipedia.org/wiki/Algebraically_closed_field), then we can [factor](https://en.wikipedia.org/wiki/Factorization) p as 

$$
p(\lambda )=\left(\lambda -\lambda _{1}\right)^{n_{1}}\left(\lambda -\lambda _{2}\right)^{n_{2}}\cdots \left(\lambda -\lambda _{N_{\lambda }}\right)^{n_{N_{\lambda }}}=0.
$$

 The integer n<sub>i</sub> is termed the [algebraic multiplicity](https://en.wikipedia.org/wiki/Algebraic_multiplicity) of eigenvalue λ<sub>i</sub>. The algebraic multiplicities sum to N: $\sum _{i=1}^{N_{\lambda }}{n_{i}}=N.$

For each eigenvalue λ<sub>i</sub>, we have a specific eigenvalue equation 

$$
\left(\mathbf {A} -\lambda _{i}\mathbf {I} \right)\mathbf {v} =0.
$$

 There will be 1 ≤ *m*<sub>*i*</sub> ≤ *n*<sub>*i*</sub> [linearly independent](https://en.wikipedia.org/wiki/Linearly_independent) solutions to each eigenvalue equation. The linear combinations of the *m*<sub>*i*</sub> solutions (except the one which gives the zero vector) are the eigenvectors associated with the eigenvalue *λ*<sub>*i*</sub>. The integer *m*<sub>*i*</sub> is termed the [geometric multiplicity](https://en.wikipedia.org/wiki/Geometric_multiplicity) of *λ*<sub>*i*</sub>. It is important to keep in mind that the algebraic multiplicity *n*<sub>*i*</sub> and geometric multiplicity *m*<sub>*i*</sub> may or may not be equal, but we always have *m*<sub>*i*</sub> ≤ *n*<sub>*i*</sub>. The simplest case is of course when *m*<sub>*i*</sub> = *n*<sub>*i*</sub> = 1. The total number of linearly independent eigenvectors, *N*<sub>**v**</sub>, can be calculated by summing the geometric multiplicities 

$$
\sum _{i=1}^{N_{\lambda }}{m_{i}}=N_{\mathbf {v} }.
$$

The eigenvectors can be indexed by eigenvalues, using a double index, with **v**<sub>*ij*</sub> being the jth eigenvector for the ith eigenvalue. The eigenvectors can also be indexed using the simpler notation of a single index **v**<sub>*k*</sub>, with *k* = 1, 2, ..., *N*<sub>**v**</sub>.

## Eigendecomposition of a matrix

Let **A** be a square *n* × *n* matrix with n linearly independent eigenvectors q<sub>i</sub> (where *i* = 1, ..., *n*). Then **A** can be [factored](https://en.wikipedia.org/wiki/Matrix_decomposition) as 

$$
\mathbf {A} =\mathbf {Q} \mathbf {\Lambda } \mathbf {Q} ^{-1}
$$

 where **Q** is the square *n* × *n* matrix whose ith column is the eigenvector q<sub>i</sub> of **A**, and **Λ** is the [diagonal matrix](https://en.wikipedia.org/wiki/Diagonal_matrix) whose diagonal elements are the corresponding eigenvalues, *Λ<sub>ii</sub>* = *λ<sub>i</sub>*. Note that only [diagonalizable matrices](https://en.wikipedia.org/wiki/Diagonalizable_matrix) can be factorized in this way. For example, the [defective matrix](https://en.wikipedia.org/wiki/Defective_matrix) $\left[{\begin{smallmatrix}1&1\\0&1\end{smallmatrix}}\right]$ (which is a [shear matrix](https://en.wikipedia.org/wiki/Shear_matrix)) cannot be diagonalized.

The n eigenvectors q<sub>i</sub> are usually normalized, but they don't have to be. A non-normalized set of n eigenvectors, v<sub>i</sub> can also be used as the columns of **Q**. That can be understood by noting that the magnitude of the eigenvectors in **Q** gets canceled in the decomposition by the presence of **Q**<sup>−1</sup>. If one of the eigenvalues *λ<sub>i</sub>* has multiple linearly independent eigenvectors (that is, the geometric multiplicity of *λ<sub>i</sub>* is greater than 1), then these eigenvectors for this eigenvalue *λ<sub>i</sub>* can be chosen to be mutually [orthogonal](https://en.wikipedia.org/wiki/Orthogonality_(mathematics) "Orthogonality (mathematics)"); however, if two eigenvectors belong to two different eigenvalues, it may be impossible for them to be orthogonal to each other (see Example below). One special case is that if **A** is a normal matrix, then by the spectral theorem, it's always possible to diagonalize **A** in an [orthonormal basis](https://en.wikipedia.org/wiki/Orthonormal_basis) {q<sub>i</sub>}.

The decomposition can be derived from the fundamental property of eigenvectors: 

$$
{\begin{aligned}\mathbf {A} \mathbf {v} &=\lambda \mathbf {v} \\\mathbf {A} \mathbf {Q} &=\mathbf {Q} \mathbf {\Lambda } \\\mathbf {A} &=\mathbf {Q} \mathbf {\Lambda } \mathbf {Q} ^{-1}.\end{aligned}}
$$

 The linearly independent eigenvectors q<sub>i</sub> with nonzero eigenvalues form a basis (not necessarily orthonormal) for all possible products *A***x**, for **x** ∈ **C**<sup>*n*</sup>, which is the same as the [image](https://en.wikipedia.org/wiki/Image_(mathematics) "Image (mathematics)") (or [range](https://en.wikipedia.org/wiki/Range_of_a_function)) of the corresponding [matrix transformation](https://en.wikipedia.org/wiki/Matrix_transformation), and also the [column space](https://en.wikipedia.org/wiki/Column_space) of the matrix **A**. The number of linearly independent eigenvectors q<sub>i</sub> with nonzero eigenvalues is equal to the [rank](https://en.wikipedia.org/wiki/Rank_(linear_algebra) "Rank (linear algebra)") of the matrix **A**, and also the dimension of the image (or range) of the corresponding matrix transformation, as well as its column space.

The linearly independent eigenvectors q<sub>i</sub> with an eigenvalue of zero form a basis (which can be chosen to be orthonormal) for the [null space](https://en.wikipedia.org/wiki/Null_space) (also known as the kernel) of the matrix transformation **A**.

### Example

The 2 × 2 real matrix **A** 

$$
\mathbf {A} ={\begin{bmatrix}1&0\\1&3\\\end{bmatrix}}
$$

 may be decomposed into a diagonal matrix through multiplication of a non-singular matrix **Q** 

$$
\mathbf {Q} ={\begin{bmatrix}a&b\\c&d\end{bmatrix}}\in \mathbb {R} ^{2\times 2}.
$$

Then 

$$
{\begin{bmatrix}a&b\\c&d\end{bmatrix}}^{-1}{\begin{bmatrix}1&0\\1&3\end{bmatrix}}{\begin{bmatrix}a&b\\c&d\end{bmatrix}}={\begin{bmatrix}x&0\\0&y\end{bmatrix}},
$$

 for some real diagonal matrix $\left[{\begin{smallmatrix}x&0\\0&y\end{smallmatrix}}\right]$.

Multiplying both sides of the equation on the left by **Q**: 

$$
{\begin{bmatrix}1&0\\1&3\end{bmatrix}}{\begin{bmatrix}a&b\\c&d\end{bmatrix}}={\begin{bmatrix}a&b\\c&d\end{bmatrix}}{\begin{bmatrix}x&0\\0&y\end{bmatrix}}.
$$

 The above equation can be decomposed into two [simultaneous equations](https://en.wikipedia.org/wiki/Simultaneous_equation): 

$$
{\begin{cases}{\begin{bmatrix}1&0\\1&3\end{bmatrix}}{\begin{bmatrix}a\\c\end{bmatrix}}={\begin{bmatrix}ax\\cx\end{bmatrix}}\\[1.2ex]{\begin{bmatrix}1&0\\1&3\end{bmatrix}}{\begin{bmatrix}b\\d\end{bmatrix}}={\begin{bmatrix}by\\dy\end{bmatrix}}\end{cases}}.
$$

 Factoring out the [eigenvalues](https://en.wikipedia.org/wiki/Eigenvalue) x and y: 

$$
{\begin{cases}{\begin{bmatrix}1&0\\1&3\end{bmatrix}}{\begin{bmatrix}a\\c\end{bmatrix}}=x{\begin{bmatrix}a\\c\end{bmatrix}}\\[1.2ex]{\begin{bmatrix}1&0\\1&3\end{bmatrix}}{\begin{bmatrix}b\\d\end{bmatrix}}=y{\begin{bmatrix}b\\d\end{bmatrix}}\end{cases}}
$$

 Letting 

$$
\mathbf {a} ={\begin{bmatrix}a\\c\end{bmatrix}},\quad \mathbf {b} ={\begin{bmatrix}b\\d\end{bmatrix}},
$$

 this gives us two vector equations: 

$$
{\begin{cases}\mathbf {A} \mathbf {a} =x\mathbf {a} \\\mathbf {A} \mathbf {b} =y\mathbf {b} \end{cases}}
$$

 And can be represented by a single vector equation involving two solutions as eigenvalues: 

$$
\mathbf {A} \mathbf {u} =\lambda \mathbf {u}
$$

 where λ represents the two eigenvalues x and y, and **u** represents the vectors **a** and **b**.

Shifting *λ***u** to the left hand side and factoring **u** out 

$$
\left(\mathbf {A} -\lambda \mathbf {I} \right)\mathbf {u} =\mathbf {0}
$$

 Since **Q** is non-singular, it is essential that **u** is nonzero. Therefore, 

$$
\det(\mathbf {A} -\lambda \mathbf {I} )=0
$$

 Thus 

$$
(1-\lambda )(3-\lambda )=0
$$

 giving us the solutions of the eigenvalues for the matrix **A** as *λ* = 1 or *λ* = 3, and the resulting diagonal matrix from the eigendecomposition of **A** is thus $\left[{\begin{smallmatrix}1&0\\0&3\end{smallmatrix}}\right]$.

Putting the solutions back into the above simultaneous equations 

$$
{\begin{cases}{\begin{bmatrix}1&0\\1&3\end{bmatrix}}{\begin{bmatrix}a\\c\end{bmatrix}}=1{\begin{bmatrix}a\\c\end{bmatrix}}\\[1.2ex]{\begin{bmatrix}1&0\\1&3\end{bmatrix}}{\begin{bmatrix}b\\d\end{bmatrix}}=3{\begin{bmatrix}b\\d\end{bmatrix}}\end{cases}}
$$

Solving the equations, we have 

$$
a=-2c\quad {\text{and}}\quad b=0,\qquad c,d\in \mathbb {R} \setminus \{0\}.
$$

 Thus the matrix **Q** required for the eigendecomposition of **A** is 

$$
\mathbf {Q} ={\begin{bmatrix}-2c&0\\c&d\end{bmatrix}},\qquad c,d\in \mathbb {R} \setminus \{0\},
$$

 that is: 

$$
{\begin{bmatrix}-2c&0\\c&d\end{bmatrix}}^{-1}{\begin{bmatrix}1&0\\1&3\end{bmatrix}}{\begin{bmatrix}-2c&0\\c&d\end{bmatrix}}={\begin{bmatrix}1&0\\0&3\end{bmatrix}},\qquad c,d\in \mathbb {R} \setminus \{0\}.
$$

The exclusion of the number 0 from the set of real numbers, $\mathbb {R}$, is necessary to ensure that the matrix $\mathbf {Q}$ is non-singular.

### Matrix inverse via eigendecomposition

If a matrix **A** can be eigendecomposed and if none of its eigenvalues are zero, then **A** is [invertible](https://en.wikipedia.org/wiki/Invertible_matrix) and its inverse is given by 

$$
\mathbf {A} ^{-1}=\mathbf {Q} \mathbf {\Lambda } ^{-1}\mathbf {Q} ^{-1}
$$

 If $\mathbf {A}$ is a symmetric matrix, since $\mathbf {Q}$ is formed from the eigenvectors of $\mathbf {A}$, $\mathbf {Q}$ is guaranteed to be an [orthogonal matrix](https://en.wikipedia.org/wiki/Orthogonal_matrix), therefore $\mathbf {Q} ^{-1}=\mathbf {Q} ^{\mathrm {T} }$. Furthermore, because **Λ** is a [diagonal matrix](https://en.wikipedia.org/wiki/Diagonal_matrix), its inverse is easy to calculate: 

$$
\left[\mathbf {\Lambda } ^{-1}\right]_{ii}={\frac {1}{\lambda _{i}}}
$$

#### Practical implications

When eigendecomposition is used on a matrix of measured, real [data](https://en.wikipedia.org/wiki/Data), the [inverse](https://en.wikipedia.org/wiki/Inverse_function) may be less valid when all eigenvalues are used unmodified in the form above. This is because as eigenvalues become relatively small, their contribution to the inversion is large. Those near zero or at the "noise" of the measurement system will have undue influence and could hamper solutions (detection) using the inverse.

Two mitigations have been proposed: truncating small or zero eigenvalues, and extending the lowest reliable eigenvalue to those below it. See also [Tikhonov regularization](https://en.wikipedia.org/wiki/Tikhonov_regularization) as a statistically motivated but biased method for rolling off eigenvalues as they become dominated by noise.

The first mitigation method is similar to a sparse sample of the original matrix, removing components that are not considered valuable. However, if the solution or detection process is near the noise level, truncating may remove components that influence the desired solution.

The second mitigation extends the eigenvalue so that lower values have much less influence over inversion, but do still contribute, such that solutions near the noise will still be found.

The reliable eigenvalue can be found by assuming that eigenvalues of extremely similar and low value are a good representation of measurement noise (which is assumed low for most systems).

If the eigenvalues are rank-sorted by value, then the reliable eigenvalue can be found by minimization of the [Laplacian](https://en.wikipedia.org/wiki/Laplace_operator) of the sorted eigenvalues: 

$$
\min \left|\nabla ^{2}\lambda _{\mathrm {s} }\right|
$$

 where the eigenvalues are subscripted with an s to denote being sorted. The position of the minimization is the lowest reliable eigenvalue. In measurement systems, the square root of this reliable eigenvalue is the average noise over the components of the system.

## Functional calculus

The eigendecomposition allows for much easier computation of [power series](https://en.wikipedia.org/wiki/Power_series) of matrices. If *f* (*x*) is given by 

$$
f(x)=a_{0}+a_{1}x+a_{2}x^{2}+\cdots
$$

 then we know that 

$$
f\!\left(\mathbf {A} \right)=\mathbf {Q} \,f\!\left(\mathbf {\Lambda } \right)\mathbf {Q} ^{-1}
$$

 Because **Λ** is a [diagonal matrix](https://en.wikipedia.org/wiki/Diagonal_matrix), functions of **Λ** are very easy to calculate: 

$$
\left[f\left(\mathbf {\Lambda } \right)\right]_{ii}=f\left(\lambda _{i}\right)
$$

The off-diagonal elements of *f* (**Λ**) are zero; that is, *f* (**Λ**) is also a diagonal matrix. Therefore, calculating *f* (**A**) reduces to just calculating the function on each of the eigenvalues.

A similar technique works more generally with the [holomorphic functional calculus](https://en.wikipedia.org/wiki/Holomorphic_functional_calculus), using 

$$
\mathbf {A} ^{-1}=\mathbf {Q} \mathbf {\Lambda } ^{-1}\mathbf {Q} ^{-1}
$$

 from [above](#Matrix_inverse_via_eigendecomposition). Once again, we find that 

$$
\left[f\left(\mathbf {\Lambda } \right)\right]_{ii}=f\left(\lambda _{i}\right)
$$

### Examples

$$
{\begin{aligned}\mathbf {A} ^{2}&=\left(\mathbf {Q} \mathbf {\Lambda } \mathbf {Q} ^{-1}\right)\left(\mathbf {Q} \mathbf {\Lambda } \mathbf {Q} ^{-1}\right)=\mathbf {Q} \mathbf {\Lambda } \left(\mathbf {Q} ^{-1}\mathbf {Q} \right)\mathbf {\Lambda } \mathbf {Q} ^{-1}=\mathbf {Q} \mathbf {\Lambda } ^{2}\mathbf {Q} ^{-1}\\[1.2ex]\mathbf {A} ^{n}&=\mathbf {Q} \mathbf {\Lambda } ^{n}\mathbf {Q} ^{-1}\\[1.2ex]\exp \mathbf {A} &=\mathbf {Q} \exp(\mathbf {\Lambda } )\mathbf {Q} ^{-1}\end{aligned}}
$$

 which are examples for the functions $f(x)=x^{2},\;f(x)=x^{n},\;f(x)=\exp {x}$. Furthermore, $\exp {\mathbf {A} }$ is the [matrix exponential](https://en.wikipedia.org/wiki/Matrix_exponential).

## Decomposition for spectral matrices

Spectral matrices are matrices that possess distinct eigenvalues and a complete set of eigenvectors. This characteristic allows spectral matrices to be fully diagonalizable, meaning they can be decomposed into simpler forms using eigendecomposition. This decomposition process reveals fundamental insights into the matrix's structure and behavior, particularly in fields such as quantum mechanics, signal processing, and numerical analysis.

### Normal matrices

A complex-valued square matrix $A$ is [normal](https://en.wikipedia.org/wiki/Normal_matrix) (meaning , $\mathbf {A} ^{*}\mathbf {A} =\mathbf {A} \mathbf {A} ^{*}$, where $\mathbf {A} ^{*}$ is the [conjugate transpose](https://en.wikipedia.org/wiki/Conjugate_transpose)) if and only if it can be decomposed as $\mathbf {A} =\mathbf {U} \mathbf {\Lambda } \mathbf {U} ^{*}$, where $\mathbf {U}$ is a [unitary matrix](https://en.wikipedia.org/wiki/Unitary_matrix) (meaning $\mathbf {U} ^{*}=\mathbf {U} ^{-1}$) and $\mathbf {\Lambda } =$ diag($\lambda _{1},\ldots ,\lambda _{n}$) is a [diagonal matrix](https://en.wikipedia.org/wiki/Diagonal_matrix). The columns $\mathbf {u} _{1},\cdots ,\mathbf {u} _{n}$ of $\mathbf {U}$ form an [orthonormal basis](https://en.wikipedia.org/wiki/Orthonormal_basis) and are eigenvectors of $\mathbf {A}$ with corresponding eigenvalues $\lambda _{1},\ldots ,\lambda _{n}$.

For example, consider the 2 x 2 normal matrix $\mathbf {A} ={\begin{bmatrix}1&2\\2&1\end{bmatrix}}$.

The eigenvalues are $\lambda _{1}=3$ and $\lambda _{2}=-1$.

The (normalized) eigenvectors corresponding to these eigenvalues are $\mathbf {u} _{1}={\frac {1}{\sqrt {2}}}{\begin{bmatrix}1\\1\end{bmatrix}}$ and $\mathbf {u} _{2}={\frac {1}{\sqrt {2}}}{\begin{bmatrix}-1\\1\end{bmatrix}}$.

The diagonalization is $\mathbf {A} =\mathbf {U} \mathbf {\Lambda } \mathbf {U} ^{*}$, where $\mathbf {U} ={\begin{bmatrix}1/{\sqrt {2}}&1/{\sqrt {2}}\\1/{\sqrt {2}}&-1/{\sqrt {2}}\end{bmatrix}}$, $\mathbf {\Lambda } =$${\begin{bmatrix}3&0\\0&-1\end{bmatrix}}$ and $\mathbf {U} ^{*}=\mathbf {U} ^{-1}=$${\begin{bmatrix}1/{\sqrt {2}}&1/{\sqrt {2}}\\1/{\sqrt {2}}&-1/{\sqrt {2}}\end{bmatrix}}$.

The verification is $\mathbf {U} \mathbf {\Lambda } \mathbf {U} ^{*}=$${\begin{bmatrix}1/{\sqrt {2}}&1/{\sqrt {2}}\\1/{\sqrt {2}}&-1/{\sqrt {2}}\end{bmatrix}}$${\begin{bmatrix}3&0\\0&-1\end{bmatrix}}$${\begin{bmatrix}1/{\sqrt {2}}&1/{\sqrt {2}}\\1/{\sqrt {2}}&-1/{\sqrt {2}}\end{bmatrix}}$$={\begin{bmatrix}1&2\\2&1\end{bmatrix}}=\mathbf {A}$.

This example illustrates the process of diagonalizing a normal matrix $\mathbf {A}$ by finding its eigenvalues and eigenvectors, forming the unitary matrix $\mathbf {U}$, the diagonal matrix $\mathbf {\Lambda }$, and verifying the decomposition.

![[media/0a7dbeab2b025771c37f55baf9d0d35a80d634fc.png]]
Subsets of important classes of matrices

### Real symmetric matrices

As a special case, for every *n* × *n* real [symmetric matrix](https://en.wikipedia.org/wiki/Symmetric_matrix), the eigenvalues are real and the eigenvectors can be chosen real and [orthonormal](https://en.wikipedia.org/wiki/Orthonormal). Thus a real symmetric matrix **A** can be decomposed as $\mathbf {A} =\mathbf {Q} \mathbf {\Lambda } \mathbf {Q} ^{\mathsf {T}}$, where **Q** is an [orthogonal matrix](https://en.wikipedia.org/wiki/Orthogonal_matrix) whose columns are the real, orthonormal eigenvectors of **A**, and **Λ** is a diagonal matrix whose entries are the eigenvalues of **A**.

### Diagonalizable matrices

[Diagonalizable matrices](https://en.wikipedia.org/wiki/Diagonalizable_matrix) can be decomposed using eigendecomposition, provided they have a full set of linearly independent eigenvectors. They can be expressed as$\mathbf {A} =\mathbf {P} \mathbf {D} \mathbf {P} ^{-1}$, where $\mathbf {P}$ is a matrix whose columns are eigenvectors of $\mathbf {A}$, and $\mathbf {D}$ is a diagonal matrix consisting of the corresponding eigenvalues of $\mathbf {A}$.

### Positive definite matrices

Positive [definite matrices](https://en.wikipedia.org/wiki/Definite_matrix) are matrices for which all eigenvalues are positive. They can be decomposed as $\mathbf {A} =\mathbf {L} \mathbf {L} ^{\mathsf {T}}$ using the [[Cholesky Decomposition]], where $\mathbf {L}$ is a lower triangular matrix.

### Unitary and Hermitian matrices

[Unitary matrices](https://en.wikipedia.org/wiki/Unitary_matrix) satisfy $\mathbf {U} \mathbf {U} ^{*}=\mathbf {I}$ (real case) or $\mathbf {U} \mathbf {U} ^{\dagger }=\mathbf {I}$ (complex case), where $\mathbf {U} ^{*}$denotes the [conjugate transpose](https://en.wikipedia.org/wiki/Conjugate_transpose) and $\mathbf {U} ^{\dagger }$denotes the conjugate transpose. They diagonalize using [unitary transformations](https://en.wikipedia.org/wiki/Unitary_transformation).

[Hermitian matrices](https://en.wikipedia.org/wiki/Hermitian_matrix) satisfy $\mathbf {H} =\mathbf {H} ^{\dagger }$, where $\mathbf {H} ^{\dagger }$denotes the conjugate transpose. They can be diagonalized using unitary or [orthogonal matrices](https://en.wikipedia.org/wiki/Orthogonal_matrix).

## Useful facts

### Useful facts regarding eigenvalues

- The product of the eigenvalues is equal to the [[Determinant]] of **A** 

$$
\det \left(\mathbf {A} \right)=\prod _{i=1}^{N_{\lambda }}{\lambda _{i}^{n_{i}}}
$$

 Note that each eigenvalue is raised to the power *n<sub>i</sub>*, the [algebraic multiplicity](https://en.wikipedia.org/wiki/Algebraic_multiplicity).
- The sum of the eigenvalues is equal to the [trace](https://en.wikipedia.org/wiki/Trace_(linear_algebra) "Trace (linear algebra)") of **A** 

$$
\operatorname {tr} \left(\mathbf {A} \right)=\sum _{i=1}^{N_{\lambda }}{{n_{i}}\lambda _{i}}
$$

 Note that each eigenvalue is multiplied by *n<sub>i</sub>*, the [algebraic multiplicity](https://en.wikipedia.org/wiki/Algebraic_multiplicity).
- If the eigenvalues of **A** are *λ*<sub>*i*</sub>, and **A** is invertible, then the eigenvalues of **A**<sup>−1</sup> are simply *λ*<sup>−1</sup>  
  <sub>*i*</sub>.
- If the eigenvalues of **A** are *λ*<sub>*i*</sub>, then the eigenvalues of *f* (**A**) are simply *f* (*λ*<sub>*i*</sub>), for any [holomorphic function](https://en.wikipedia.org/wiki/Holomorphic_function) f and any **A** for which *f* (**A**) is well-defined.

### Useful facts regarding eigenvectors

- If **A** is [Hermitian](https://en.wikipedia.org/wiki/Hermitian_matrix) and full-rank, the basis of eigenvectors may be chosen to be mutually [orthogonal](https://en.wikipedia.org/wiki/Orthogonal). The eigenvalues are real.
- The eigenvectors of **A**<sup>−1</sup> are the same as the eigenvectors of **A**.
- Eigenvectors are only defined up to a multiplicative constant. That is, if **Av** = *λ***v** then *c***v** is also an eigenvector for any scalar *c* ≠ 0. In particular, −**v** and *e*<sup>*iθ*</sup>**v** (for any *θ*) are also eigenvectors.
- In the case of degenerate eigenvalues (an eigenvalue having more than one eigenvector), the eigenvectors have an additional freedom of linear transformation, that is to say, any linear (orthonormal) combination of eigenvectors sharing an eigenvalue (in the degenerate subspace) is itself an eigenvector (in the subspace).

### Useful facts regarding eigendecomposition

- **A** can be eigendecomposed if and only if the number of linearly independent eigenvectors, *N*<sub>**v**</sub>, equals the dimension of an eigenvector: *N*<sub>**v**</sub> = *N*
- If the field of scalars is algebraically closed and if *p*(*λ*) has no repeated roots, that is, if $N_{\lambda }=N,$ then **A** can be eigendecomposed.
- The statement "**A** can be eigendecomposed" does *not* imply that **A** has an inverse as some eigenvalues may be zero, making **A** not invertible.
- The statement "**A** has an inverse" does *not* imply that **A** can be eigendecomposed. A counterexample is $\left[{\begin{smallmatrix}1&1\\0&1\end{smallmatrix}}\right]$, which is an invertible [defective matrix](https://en.wikipedia.org/wiki/Defective_matrix).

### Useful facts regarding matrix inverse

- **A** can be inverted [if and only if](https://en.wikipedia.org/wiki/If_and_only_if) all eigenvalues are nonzero: 

$$
\lambda _{i}\neq 0\quad \forall \,i
$$

- If *λ<sub>i</sub>* ≠ 0 *and* *N*<sub>**v**</sub> = *N*, the inverse is given by 

$$
\mathbf {A} ^{-1}=\mathbf {Q} \mathbf {\Lambda } ^{-1}\mathbf {Q} ^{-1}
$$

## Numerical computations

### Numerical computation of eigenvalues

Suppose that we want to compute the eigenvalues of a given matrix. If the matrix is small, we can compute them symbolically using the [characteristic polynomial](https://en.wikipedia.org/wiki/Characteristic_polynomial). However, this is often impossible for larger matrices, in which case we must use a [numerical method](https://en.wikipedia.org/wiki/Numerical_analysis).

In practice, eigenvalues of large matrices are not computed using the characteristic polynomial. Computing the polynomial becomes expensive in itself, and exact (symbolic) roots of a high-degree polynomial can be difficult to compute and express: the [Abel–Ruffini theorem](https://en.wikipedia.org/wiki/Abel%E2%80%93Ruffini_theorem) implies that the roots of high-degree (5 or above) polynomials cannot in general be expressed simply using nth roots. Therefore, general algorithms to find eigenvectors and eigenvalues are [iterative](https://en.wikipedia.org/wiki/Iterative_method).

Iterative numerical algorithms for approximating roots of polynomials exist, such as [Newton's method](https://en.wikipedia.org/wiki/Newton%27s_method), but in general it is impractical to compute the characteristic polynomial and then apply these methods. One reason is that small [round-off errors](https://en.wikipedia.org/wiki/Round-off_error) in the coefficients of the characteristic polynomial can lead to large errors in the eigenvalues and eigenvectors: the roots are an extremely [ill-conditioned](https://en.wikipedia.org/wiki/Ill-conditioned) function of the coefficients.

A simple and accurate iterative method is the [power method](https://en.wikipedia.org/wiki/Power_method): a [random](https://en.wikipedia.org/wiki/Random) vector **v** is chosen and a sequence of [unit vectors](https://en.wikipedia.org/wiki/Unit_vector) is computed as 

$$
{\frac {\mathbf {A} \mathbf {v} }{\left\|\mathbf {A} \mathbf {v} \right\|}},{\frac {\mathbf {A} ^{2}\mathbf {v} }{\left\|\mathbf {A} ^{2}\mathbf {v} \right\|}},{\frac {\mathbf {A} ^{3}\mathbf {v} }{\left\|\mathbf {A} ^{3}\mathbf {v} \right\|}},\ldots
$$

This [sequence](https://en.wikipedia.org/wiki/Sequence) will [almost always](https://en.wikipedia.org/wiki/Almost_always) converge to an eigenvector corresponding to the eigenvalue of greatest magnitude, provided that **v** has a nonzero component of this eigenvector in the eigenvector basis (and also provided that there is only one eigenvalue of greatest magnitude). This simple algorithm is useful in some practical applications; for example, [Google](https://en.wikipedia.org/wiki/Google) uses it to calculate the [page rank](https://en.wikipedia.org/wiki/PageRank) of documents in their search engine. Also, the power method is the starting point for many more sophisticated algorithms. For instance, by keeping not just the last vector in the sequence, but instead looking at the [span](https://en.wikipedia.org/wiki/Linear_span) of *all* the vectors in the sequence, one can get a better (faster converging) approximation for the eigenvector, and this idea is the basis of [Arnoldi iteration](https://en.wikipedia.org/wiki/Arnoldi_iteration). Alternatively, the important [QR algorithm](https://en.wikipedia.org/wiki/QR_algorithm) is also based on a subtle transformation of a power method.

### Numerical computation of eigenvectors

Once the eigenvalues are computed, the eigenvectors could be calculated by solving the equation 

$$
\left(\mathbf {A} -\lambda _{i}\mathbf {I} \right)\mathbf {v} _{i,j}=\mathbf {0}
$$

 using [Gaussian elimination](https://en.wikipedia.org/wiki/Gaussian_elimination) or [any other method](https://en.wikipedia.org/wiki/System_of_linear_equations#Solving_a_linear_system) for solving [matrix equations](https://en.wikipedia.org/wiki/System_of_linear_equations).

However, in practical large-scale eigenvalue methods, the eigenvectors are usually computed in other ways, as a byproduct of the eigenvalue computation. In [[Power Iteration]], for example, the eigenvector is actually computed before the eigenvalue (which is typically computed by the [Rayleigh quotient](https://en.wikipedia.org/wiki/Rayleigh_quotient) of the eigenvector). In the QR algorithm for a [Hermitian matrix](https://en.wikipedia.org/wiki/Hermitian_matrix) (or any normal matrix), the orthonormal eigenvectors are obtained as a product of the **Q** matrices from the steps in the algorithm. (For more general matrices, the QR algorithm yields the [Schur decomposition](https://en.wikipedia.org/wiki/Schur_decomposition) first, from which the eigenvectors can be obtained by a [backsubstitution](https://en.wikipedia.org/wiki/Backsubstitution) procedure.) For Hermitian matrices, the [Divide-and-conquer eigenvalue algorithm](https://en.wikipedia.org/wiki/Divide-and-conquer_eigenvalue_algorithm) is more efficient than the QR algorithm if both eigenvectors and eigenvalues are desired.

## Additional topics

### Generalized eigenspaces

Recall that the *geometric* multiplicity of an eigenvalue can be described as the dimension of the associated eigenspace, the [nullspace](https://en.wikipedia.org/wiki/Kernel_(linear_algebra) "Kernel (linear algebra)") of *λ***I** − **A**. The algebraic multiplicity can also be thought of as a dimension: it is the dimension of the associated **[generalized eigenspace](https://en.wikipedia.org/wiki/Generalized_eigenspace)** (1st sense), which is the nullspace of the matrix (*λ***I** − **A**)<sup>*k*</sup> for *any sufficiently large k*. That is, it is the space of *[generalized eigenvectors](https://en.wikipedia.org/wiki/Generalized_eigenvector)* (first sense), where a generalized eigenvector is any vector which *eventually* becomes 0 if *λ***I** − **A** is applied to it enough times successively. Any eigenvector is a generalized eigenvector, and so each eigenspace is contained in the associated generalized eigenspace. This provides an easy proof that the geometric multiplicity is always less than or equal to the algebraic multiplicity.

This usage should not be confused with the *generalized eigenvalue problem* described below.

### Conjugate eigenvector

A **conjugate eigenvector** or **coneigenvector** is a vector sent after transformation to a scalar multiple of its conjugate, where the scalar is called the **conjugate eigenvalue** or **coneigenvalue** of the linear transformation. The coneigenvectors and coneigenvalues represent essentially the same information and meaning as the regular eigenvectors and eigenvalues, but arise when an alternative coordinate system is used. The corresponding equation is 

$$
\mathbf {A} \mathbf {v} =\lambda \mathbf {v} ^{*}.
$$

 For example, in coherent electromagnetic scattering theory, the linear transformation **A** represents the action performed by the scattering object, and the eigenvectors represent polarization states of the electromagnetic wave. In [optics](https://en.wikipedia.org/wiki/Optics), the coordinate system is defined from the wave's viewpoint, known as the [Forward Scattering Alignment](https://en.wikipedia.org/wiki/Forward_Scattering_Alignment) (FSA), and gives rise to a regular eigenvalue equation, whereas in [radar](https://en.wikipedia.org/wiki/Radar), the coordinate system is defined from the radar's viewpoint, known as the [Back Scattering Alignment](https://en.wikipedia.org/wiki/Back_Scattering_Alignment) (BSA), and gives rise to a coneigenvalue equation.

### Generalized eigenvalue problem

A **generalized eigenvalue problem** (second sense) is the problem of finding a (nonzero) vector **v** that obeys 

$$
\mathbf {A} \mathbf {v} =\lambda \mathbf {B} \mathbf {v}
$$

 where **A** and **B** are matrices. If **v** obeys this equation, with some λ, then we call **v** the *generalized eigenvector* of **A** and **B** (in the second sense), and λ is called the *generalized eigenvalue* of **A** and **B** (in the second sense) which corresponds to the generalized eigenvector **v**. The possible values of λ must obey the following equation 

$$
\det(\mathbf {A} -\lambda \mathbf {B} )=0.
$$

If *n* linearly independent vectors {**v**<sub>1</sub>, …, **v**<sub>*n*</sub>} can be found, such that for every *i* ∈ {1, …, *n*}, **Av**<sub>*i*</sub> = *λ<sub>i</sub>***Bv**<sub>*i*</sub>, then we define the matrices **P** and **D** such that 

$$
P={\begin{bmatrix}|&&|\\\mathbf {v} _{1}&\cdots &\mathbf {v} _{n}\\|&&|\end{bmatrix}}\equiv {\begin{bmatrix}(\mathbf {v} _{1})_{1}&\cdots &(\mathbf {v} _{n})_{1}\\\vdots &&\vdots \\(\mathbf {v} _{1})_{n}&\cdots &(\mathbf {v} _{n})_{n}\end{bmatrix}}
$$

$$
(D)_{ij}={\begin{cases}\lambda _{i},&{\text{if }}i=j\\0,&{\text{otherwise}}\end{cases}}
$$

 Then the following equality holds 

$$
\mathbf {A} =\mathbf {B} \mathbf {P} \mathbf {D} \mathbf {P} ^{-1}
$$

 And the proof is 

$$
\mathbf {A} \mathbf {P} =\mathbf {A} {\begin{bmatrix}|&&|\\\mathbf {v} _{1}&\cdots &\mathbf {v} _{n}\\|&&|\end{bmatrix}}={\begin{bmatrix}|&&|\\A\mathbf {v} _{1}&\cdots &A\mathbf {v} _{n}\\|&&|\end{bmatrix}}={\begin{bmatrix}|&&|\\\lambda _{1}B\mathbf {v} _{1}&\cdots &\lambda _{n}B\mathbf {v} _{n}\\|&&|\end{bmatrix}}={\begin{bmatrix}|&&|\\B\mathbf {v} _{1}&\cdots &B\mathbf {v} _{n}\\|&&|\end{bmatrix}}\mathbf {D} =\mathbf {B} \mathbf {P} \mathbf {D}
$$

And since **P** is invertible, we multiply the equation from the right by its inverse, finishing the proof.

The set of matrices of the form **A** − *λ***B**, where λ is a complex number, is called a *pencil*; the term *[matrix pencil](https://en.wikipedia.org/wiki/Matrix_pencil)* can also refer to the pair (**A**, **B**) of matrices.

If **B** is invertible, then the original problem can be written in the form 

$$
\mathbf {B} ^{-1}\mathbf {A} \mathbf {v} =\lambda \mathbf {v}
$$

 which is a standard eigenvalue problem. However, in most situations it is preferable not to perform the inversion, but rather to solve the generalized eigenvalue problem as stated originally. This is especially important if **A** and **B** are [Hermitian matrices](https://en.wikipedia.org/wiki/Hermitian_matrices), since in this case **B**<sup>−1</sup>**A** is not generally Hermitian and important properties of the solution are no longer apparent.

If **A** and **B** are both symmetric or Hermitian, and **B** is also a [[Positive-Definite Matrix]], the eigenvalues *λ<sub>i</sub>* are real and eigenvectors **v**<sub>1</sub> and **v**<sub>2</sub> with distinct eigenvalues are **B**-orthogonal (**v**<sub>1</sub><sup>\*</sup>**Bv**<sub>2</sub> = 0). In this case, eigenvectors can be chosen so that the matrix **P** defined above satisfies 

$$
\mathbf {P} ^{*}\mathbf {B} \mathbf {P} =\mathbf {I}
$$

 or 

$$
\mathbf {P} \mathbf {P} ^{*}\mathbf {B} =\mathbf {I} ,
$$

 and there exists a [basis](https://en.wikipedia.org/wiki/Basis_(linear_algebra) "Basis (linear algebra)") of generalized eigenvectors (it is not a [defective](https://en.wikipedia.org/wiki/Defective_matrix) problem). This case is sometimes called a *Hermitian definite pencil* or *definite pencil*.

## See also

- [Eigenvalue perturbation](https://en.wikipedia.org/wiki/Eigenvalue_perturbation)
- [Frobenius covariant](https://en.wikipedia.org/wiki/Frobenius_covariant)
- [Householder transformation](https://en.wikipedia.org/wiki/Householder_transformation)
- [Jordan normal form](https://en.wikipedia.org/wiki/Jordan_normal_form)
- [List of matrices](https://en.wikipedia.org/wiki/List_of_matrices)
- [Matrix decomposition](https://en.wikipedia.org/wiki/Matrix_decomposition)
- [[Singular Value Decomposition]]
- [Sylvester's formula](https://en.wikipedia.org/wiki/Sylvester%27s_formula)

## Notes

1.  [Golub, Gene H.](https://en.wikipedia.org/wiki/Gene_H._Golub); [Van Loan, Charles F.](https://en.wikipedia.org/wiki/Charles_F._Van_Loan) (1996), *Matrix Computations* (3rd ed.), Baltimore: [Johns Hopkins University Press](https://en.wikipedia.org/wiki/Johns_Hopkins_University_Press), p. 310, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8018-5414-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8018-5414-9)
2.  [Kreyszig, Erwin](https://en.wikipedia.org/wiki/Erwin_Kreyszig) (1972), [Advanced Engineering Mathematics](https://archive.org/details/advancedengineer00krey) (3rd ed.), New York: [Wiley](https://en.wikipedia.org/wiki/John_Wiley_%26_Sons), p. 273, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-50728-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-50728-4)
3.  Nering, Evar D. (1970). *Linear Algebra and Matrix Theory* (2nd ed.). New York: [Wiley](https://en.wikipedia.org/wiki/John_Wiley_%26_Sons). p. 270. [LCCN](https://en.wikipedia.org/wiki/LCCN_(identifier)) [76091646](https://lccn.loc.gov/76091646).
4.  Hayde, A. F.; Twede, D. R. (2002). Shen, Sylvia S. (ed.). "Observations on relationship between eigenvalues, instrument noise and detection performance". *Imaging Spectrometry VIII*. Proceedings of SPIE. **4816**: 355. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2002SPIE.4816..355H](https://ui.adsabs.harvard.edu/abs/2002SPIE.4816..355H). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1117/12.453777](https://doi.org/10.1117%2F12.453777). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [120953647](https://api.semanticscholar.org/CorpusID:120953647).
5.  Twede, D. R.; Hayden, A. F. (2004). Shen, Sylvia S; Lewis, Paul E (eds.). "Refinement and generalization of the extension method of covariance matrix inversion by regularization". *Imaging Spectrometry IX*. Proceedings of SPIE. **5159**: 299. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2004SPIE.5159..299T](https://ui.adsabs.harvard.edu/abs/2004SPIE.5159..299T). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1117/12.506993](https://doi.org/10.1117%2F12.506993). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [123123072](https://api.semanticscholar.org/CorpusID:123123072).
6.  Allaire, Grégoire (2008). [Numerical linear algebra](https://archive.org/details/numericallineara0000alla). Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-34159-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-34159-0).
7.  , p. 133, Theorem 2.5.3
8.  ^     Shores, Thomas S (2006). ["Applied linear algebra and matrix analysis"](https://archive.org/details/appliedlinearalg0000shor).
9.  , p. 136, Corollary 2.5.11
10. Carl D. Meyer (2023). *Matrix analysis and applied linear algebra* (2nd ed.). Society for Industrial and Applied Mathematics. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9781611977431](https://en.wikipedia.org/wiki/Special:BookSources/9781611977431).
11. ^       [Trefethen, Lloyd N.](https://en.wikipedia.org/wiki/Lloyd_N._Trefethen); Bau, David (1997). *Numerical Linear Algebra*. SIAM. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-89871-361-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-89871-361-9).
12. [Ipsen, Ilse](https://en.wikipedia.org/wiki/Ilse_Ipsen), and Rebecca M. Wills, *[Analysis and Computation of Google's PageRank](https://www4.ncsu.edu/~ipsen/ps/slides_imacs.pdf) [Archived](https://web.archive.org/web/20180921014418/https://www4.ncsu.edu/~ipsen/ps/slides_imacs.pdf) 2018-09-21 at the [Wayback Machine](https://en.wikipedia.org/wiki/Wayback_Machine)*, 7th IMACS International Symposium on Iterative Methods in Scientific Computing, Fields Institute, Toronto, Canada, 5–8 May 2005.
13. [Quarteroni, Alfio](https://en.wikipedia.org/wiki/Alfio_Quarteroni); Sacco, Riccardo; Saleri, Fausto (2000). "section 5.8.2". [Numerical Mathematics](https://books.google.com/books?id=YVpyyi1M7vUC). Springer. p. 15. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-98959-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-98959-4).
14. ^    Bai, Z.; [Demmel, J.](https://en.wikipedia.org/wiki/James_Demmel); [Dongarra, J.](https://en.wikipedia.org/wiki/Jack_Dongarra); Ruhe, A.; Van Der Vorst, H., eds. (2000). "Generalized Hermitian Eigenvalue Problems". [Templates for the Solution of Algebraic Eigenvalue Problems: A Practical Guide](https://web.archive.org/web/20100821063624/http://www.cs.utk.edu/~dongarra/etemplates/node156.html). Philadelphia: SIAM. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-89871-471-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-89871-471-5). Archived from [the original](https://cs.utk.edu/~dongarra/etemplates/node156.html) on 2010-08-21. Retrieved 2022-09-09.
15. [Parlett, Beresford N.](https://en.wikipedia.org/wiki/Beresford_Parlett) (1998). [The symmetric eigenvalue problem](https://epubs.siam.org/doi/book/10.1137/1.9781611971163) (Reprint. ed.). Philadelphia: Society for Industrial and Applied Mathematics. p. 345. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/1.9781611971163](https://doi.org/10.1137%2F1.9781611971163). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-89871-402-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-89871-402-9).

## References

- Franklin, Joel N. (1968). [Matrix Theory](https://archive.org/details/matrixtheory0000fran). Dover Publications. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-486-41179-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-486-41179-8).
- Horn, Roger A.; Johnson, Charles R. (1985). *Matrix Analysis*. Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-38632-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-38632-6).
- Horn, Roger A.; Johnson, Charles R. (1991). [Topics in Matrix Analysis](https://archive.org/details/topicsinmatrixan0000horn). Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-46713-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-46713-1).
- Strang, G. (1998). *Introduction to Linear Algebra* (3rd ed.). Wellesley-Cambridge Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-9614088-5-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-9614088-5-5).

## External links

- [Interactive program & tutorial of Spectral Decomposition](https://people.revoledu.com/kardi/tutorial/LinearAlgebra/SpectralDecomposition.html).
