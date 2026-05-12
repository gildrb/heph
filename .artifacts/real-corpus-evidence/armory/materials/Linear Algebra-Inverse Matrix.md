[[linear-algebra.base]]

> Source: [Invertible matrix](https://en.wikipedia.org/wiki/Invertible_matrix)
> License: Wikipedia content is available under CC BY-SA 4.0.

In [linear algebra](https://en.wikipedia.org/wiki/Linear_algebra), an **invertible matrix** (*non-singular*, *non-degenerate* or *regular*) is a [square matrix](https://en.wikipedia.org/wiki/Square_matrix) that has an [inverse](https://en.wikipedia.org/wiki/Multiplicative_inverse). In other words, if a matrix is invertible, it can be multiplied by its inverse matrix to yield the [identity matrix](https://en.wikipedia.org/wiki/Identity_matrix). Invertible matrices are the same size as their inverse.

The inverse of a matrix represents the inverse operation, meaning if a matrix is applied to a particular vector, followed by applying the matrix's inverse, the result is the original vector.

## Definition

An n-by-n [square matrix](https://en.wikipedia.org/wiki/Square_matrix) **A** is called **invertible** if there exists an n-by-n square matrix **B** such that

$$
\mathbf {AB} =\mathbf {BA} =\mathbf {I} _{n},
$$

where **I**<sub>*n*</sub> denotes the n-by-n [identity matrix](https://en.wikipedia.org/wiki/Identity_matrix) and the multiplication used is ordinary [[Matrix Multiplication]]. If this is the case, then the matrix **B** is uniquely determined by **A**, and is called the [*inverse*](https://en.wikipedia.org/wiki/Multiplicative_inverse) of **A**, denoted by **A**<sup>−1</sup>. **Matrix inversion** is the process of finding the matrix which when multiplied by the original matrix gives the identity matrix.

## Examples

Consider the following 2-by-2 matrix:

$\mathbf {A} ={\begin{pmatrix}-1&{\tfrac {3}{2}}\\1&-1\end{pmatrix}}$

The matrix $\mathbf {A}$ is invertible, as it has inverse $\mathbf {B} ={\begin{pmatrix}2&3\\2&2\end{pmatrix}},$ which can be confirmed by computing

$\mathbf {A} \mathbf {B} ={\begin{pmatrix}-1&{\tfrac {3}{2}}\\1&-1\end{pmatrix}}{\begin{pmatrix}2&3\\2&2\end{pmatrix}}={\begin{pmatrix}(-1)\times 2+{\tfrac {3}{2}}\times 2&(-1)\times 3+{\tfrac {3}{2}}\times 2\\1\times 2+(-1)\times 2&1\times 3+(-1)\times 2\end{pmatrix}}={\begin{pmatrix}1&0\\0&1\end{pmatrix}}=\mathbf {I} _{2}$

To check that it is invertible without finding an inverse, $\det \mathbf {A} =-{\frac {1}{2}}$ can be computed, which is non-zero.

On the other hand, this is a non-invertible matrix:

$\mathbf {C} ={\begin{pmatrix}2&4\\2&4\end{pmatrix}}$

We can see the rank of this 2-by-2 matrix is 1, which is *n* − 1 ≠ *n*, so it is non-invertible. Additionally, we can compute that the [[Determinant]] of $\mathbf {C}$ is 0, which is a [necessary and sufficient condition](https://en.wikipedia.org/wiki/Necessary_and_sufficient_condition) for a matrix to be non-invertible.

## Methods of matrix inversion

### Gaussian elimination

[Gaussian elimination](https://en.wikipedia.org/wiki/Gaussian_elimination) is a useful and easy way to compute the inverse of a matrix. To compute a matrix inverse using this method, an [augmented matrix](https://en.wikipedia.org/wiki/Augmented_matrix) is first created with the left side being the matrix to invert and the right side being the [identity matrix](https://en.wikipedia.org/wiki/Identity_matrix). Then, Gaussian elimination is used to convert the left side into the identity matrix, which causes the right side to become the inverse of the input matrix.

For example, take the following matrix: 

$$
\mathbf {A} ={\begin{pmatrix}-1&{\tfrac {3}{2}}\\1&-1\end{pmatrix}}
$$

The first step to compute its inverse is to create the augmented matrix 

$$
\left(\!\!{\begin{array}{cc|cc}-1&{\tfrac {3}{2}}&1&0\\1&-1&0&1\end{array}}\!\!\right)
$$

Call the first row of this matrix $R_{1}$ and the second row $R_{2}$. Then, add row 1 to row 2 $(R_{1}+R_{2}\to R_{2}).$ This yields 

$$
\left(\!\!{\begin{array}{cc|cc}-1&{\tfrac {3}{2}}&1&0\\0&{\tfrac {1}{2}}&1&1\end{array}}\!\!\right)
$$

Next, subtract row 2, multiplied by 3, from row 1 $(R_{1}-3\,R_{2}\to R_{1}),$ which yields 

$$
\left(\!\!{\begin{array}{cc|cc}-1&0&-2&-3\\0&{\tfrac {1}{2}}&1&1\end{array}}\!\!\right)
$$

Finally, multiply row 1 by −1 $(-R_{1}\to R_{1})$ and row 2 by 2 $(2\,R_{2}\to R_{2}).$ This yields the identity matrix on the left side and the inverse matrix on the right:

$$
\left(\!\!{\begin{array}{cc|cc}1&0&2&3\\0&1&2&2\end{array}}\!\!\right)
$$

Thus, 

$$
\mathbf {A} ^{-1}={\begin{pmatrix}2&3\\2&2\end{pmatrix}}
$$

 It works because the process of Gaussian elimination can be viewed as a sequence of applying left matrix multiplication using elementary row operations using [elementary matrices](https://en.wikipedia.org/wiki/Elementary_matrix) ($\mathbf {E} _{n}$), such as $\mathbf {E} _{n}\mathbf {E} _{n-1}\cdots \mathbf {E} _{2}\mathbf {E} _{1}\mathbf {A} =\mathbf {I}$

Applying right-multiplication using $\mathbf {A} ^{-1},$ we get $\mathbf {E} _{n}\mathbf {E} _{n-1}\cdots \mathbf {E} _{2}\mathbf {E} _{1}\mathbf {I} =\mathbf {I} \mathbf {A} ^{-1}.$ And the right side $\mathbf {I} \mathbf {A} ^{-1}=\mathbf {A} ^{-1},$ which is the inverse we want.

To obtain $\mathbf {E} _{n}\mathbf {E} _{n-1}\cdots \mathbf {E} _{2}\mathbf {E} _{1}\mathbf {I} ,$ we create the augmented matrix by combining **A** with **I** and applying [Gaussian elimination](https://en.wikipedia.org/wiki/Gaussian_elimination). The two portions will be transformed using the same sequence of elementary row operations. When the left portion becomes **I**, the right portion applied the same elementary row operation sequence will become **A**<sup>−1</sup>.

### Newton's method

A generalization of [Newton's method](https://en.wikipedia.org/wiki/Newton%27s_method) as used for a [multiplicative inverse algorithm](https://en.wikipedia.org/wiki/Multiplicative_inverse#Algorithms) may be convenient if it is convenient to find a suitable starting seed:

$X_{k+1}=2X_{k}-X_{k}AX_{k}$

[Victor Pan](https://en.wikipedia.org/wiki/Victor_Pan) and [John Reif](https://en.wikipedia.org/wiki/John_Reif) have done work that includes ways of generating a starting seed.

Newton's method is particularly useful when dealing with [families](https://en.wikipedia.org/wiki/Family_(set_theory)) of related matrices that behave enough like the sequence manufactured for the [homotopy](https://en.wikipedia.org/wiki/Homotopy) above: sometimes a good starting point for refining an approximation for the new inverse can be the already obtained inverse of a previous matrix that nearly matches the current matrix. For example, the pair of sequences of inverse matrices used in obtaining [matrix square roots by Denman–Beavers iteration](https://en.wikipedia.org/wiki/Matrix_square_root#By_Denman–Beavers_iteration). That may need more than one pass of the iteration at each new matrix, if they are not close enough together for just one to be enough. Newton's method is also useful for "touch up" corrections to the Gauss–Jordan algorithm which has been contaminated by small errors from [imperfect computer arithmetic](https://en.wikipedia.org/wiki/Round-off_error).

### Cayley–Hamilton method

The [Cayley–Hamilton theorem](https://en.wikipedia.org/wiki/Cayley%E2%80%93Hamilton_theorem) allows the inverse of **A** to be expressed in terms of det(**A**), traces and powers of **A**:

$\mathbf {A} ^{-1}={\frac {1}{\det(\mathbf {A} )}}\sum _{s=0}^{n-1}\mathbf {A} ^{s}\sum _{k_{1},k_{2},\ldots ,k_{n-1}}\prod _{l=1}^{n-1}{\frac {(-1)^{k_{l}+1}}{l^{k_{l}}k_{l}!}}\operatorname {tr} \left(\mathbf {A} ^{l}\right)^{k_{l}},$

where n is size of **A**, and tr(**A**) is the [trace](https://en.wikipedia.org/wiki/Trace_(linear_algebra) "Trace (linear algebra)") of matrix **A** given by the sum of the [main diagonal](https://en.wikipedia.org/wiki/Main_diagonal). The sum is taken over s and the sets of all $k_{l}\geq 0$ satisfying the linear [Diophantine equation](https://en.wikipedia.org/wiki/Diophantine_equation)

$s+\sum _{l=1}^{n-1}lk_{l}=n-1$

The formula can be rewritten in terms of complete [Bell polynomials](https://en.wikipedia.org/wiki/Bell_polynomials) of arguments $t_{l}=-(l-1)!\operatorname {tr} \left(A^{l}\right)$ as

$\mathbf {A} ^{-1}={\frac {1}{\det(\mathbf {A} )}}\sum _{s=1}^{n}\mathbf {A} ^{s-1}{\frac {(-1)^{n-1}}{(n-s)!}}B_{n-s}(t_{1},t_{2},\ldots ,t_{n-s})$

That is described in more detail under [Cayley–Hamilton method](https://en.wikipedia.org/wiki/Cayley%E2%80%93Hamilton_theorem#Determinant_and_inverse_matrix).

### Eigendecomposition

If matrix **A** can be eigendecomposed, and if none of its eigenvalues are zero, then **A** is invertible and its inverse is given by

$\mathbf {A} ^{-1}=\mathbf {Q} \mathbf {\Lambda } ^{-1}\mathbf {Q} ^{-1},$

where **Q** is the square (*N* × *N*) matrix whose ith column is the [eigenvector](https://en.wikipedia.org/wiki/Eigenvector) $q_{i}$ of **A**, and **Λ** is the [diagonal matrix](https://en.wikipedia.org/wiki/Diagonal_matrix) whose diagonal entries are the corresponding eigenvalues, that is, $\Lambda _{ii}=\lambda _{i}.$ If **A** is symmetric, **Q** is guaranteed to be an [orthogonal matrix](https://en.wikipedia.org/wiki/Orthogonal_matrix), therefore $\mathbf {Q} ^{-1}=\mathbf {Q} ^{\mathrm {T} }.$ Furthermore, because **Λ** is a diagonal matrix, its inverse is easy to calculate:

$\left[\Lambda ^{-1}\right]_{ii}={\frac {1}{\lambda _{i}}}$

### Cholesky decomposition

If matrix **A** is [[Positive-Definite Matrix|positive definite]], then its inverse can be obtained as

$\mathbf {A} ^{-1}=\left(\mathbf {L} ^{*}\right)^{-1}\mathbf {L} ^{-1},$

where **L** is the [lower triangular](https://en.wikipedia.org/wiki/Lower_triangular) [[Cholesky Decomposition]] of **A**, and **L**\* denotes the [conjugate transpose](https://en.wikipedia.org/wiki/Conjugate_transpose) of **L**.

### Analytic solution

Writing the transpose of the [matrix of cofactors](https://en.wikipedia.org/wiki/Matrix_of_cofactors), known as an [adjugate matrix](https://en.wikipedia.org/wiki/Adjugate_matrix), may also be an efficient way to calculate the inverse of *small* matrices, but the [recursive](https://en.wikipedia.org/wiki/Recursion) method is inefficient for large matrices. To determine the inverse, we calculate a matrix of cofactors:

$\mathbf {A} ^{-1}={1 \over {\begin{vmatrix}\mathbf {A} \end{vmatrix}}}\mathbf {C} ^{\mathrm {T} }={1 \over {\begin{vmatrix}\mathbf {A} \end{vmatrix}}}{\begin{pmatrix}\mathbf {C} _{11}&\mathbf {C} _{21}&\cdots &\mathbf {C} _{n1}\\\mathbf {C} _{12}&\mathbf {C} _{22}&\cdots &\mathbf {C} _{n2}\\\vdots &\vdots &\ddots &\vdots \\\mathbf {C} _{1n}&\mathbf {C} _{2n}&\cdots &\mathbf {C} _{nn}\\\end{pmatrix}}$

so that

$\left(\mathbf {A} ^{-1}\right)_{ij}={1 \over {\begin{vmatrix}\mathbf {A} \end{vmatrix}}}\left(\mathbf {C} ^{\mathrm {T} }\right)_{ij}={1 \over {\begin{vmatrix}\mathbf {A} \end{vmatrix}}}\left(\mathbf {C} _{ji}\right)$

where \|**A**\| is the [[Determinant]] of **A**, **C** is the matrix of cofactors, and **C**<sup>T</sup> represents the matrix [transpose](https://en.wikipedia.org/wiki/Transpose).

#### Inversion of 2 × 2 matrices

The *cofactor equation* listed above yields the following result for 2 × 2 matrices. Inversion of these matrices can be done as follows:

$\mathbf {A} ^{-1}={\begin{bmatrix}a&b\\c&d\\\end{bmatrix}}^{-1}={\frac {1}{\det \mathbf {A} }}{\begin{bmatrix}\,\,\,d&\!\!-b\\-c&\,a\\\end{bmatrix}}={\frac {1}{ad-bc}}{\begin{bmatrix}\,\,\,d&\!\!-b\\-c&\,a\\\end{bmatrix}}$

This is possible because 1/(*ad* − *bc*) is the [reciprocal](https://en.wikipedia.org/wiki/Reciprocal_(mathematics)) of the determinant of the matrix in question, and the same strategy could be used for other matrix sizes.

The Cayley–Hamilton method gives

$\mathbf {A} ^{-1}={\frac {1}{\det \mathbf {A} }}\left[\left(\operatorname {tr} \mathbf {A} \right)\mathbf {I} -\mathbf {A} \right]$

#### Inversion of 3 × 3 matrices

A [computationally efficient](https://en.wikipedia.org/wiki/Computationally_efficient) 3 × 3 matrix inversion is given by

$\mathbf {A} ^{-1}={\begin{bmatrix}a&b&c\\d&e&f\\g&h&i\\\end{bmatrix}}^{-1}={\frac {1}{\det(\mathbf {A} )}}{\begin{bmatrix}\,A&\,B&\,C\\\,D&\,E&\,F\\\,G&\,H&\,I\\\end{bmatrix}}^{\mathrm {T} }={\frac {1}{\det(\mathbf {A} )}}{\begin{bmatrix}\,A&\,D&\,G\\\,B&\,E&\,H\\\,C&\,F&\,I\\\end{bmatrix}}$

(where the [scalar](https://en.wikipedia.org/wiki/Scalar_(mathematics) "Scalar (mathematics)") A is not to be confused with the matrix **A**).

If the determinant is non-zero, the matrix is invertible, with the entries of the intermediary matrix on the right side above given by

${\begin{alignedat}{6}A&={}&(ei-fh),&\quad &D&={}&-(bi-ch),&\quad &G&={}&(bf-ce),\\B&={}&-(di-fg),&\quad &E&={}&(ai-cg),&\quad &H&={}&-(af-cd),\\C&={}&(dh-eg),&\quad &F&={}&-(ah-bg),&\quad &I&={}&(ae-bd).\\\end{alignedat}}$

The determinant of **A** can be computed by applying the [rule of Sarrus](https://en.wikipedia.org/wiki/Rule_of_Sarrus) as follows:

$\det(\mathbf {A} )=aA+bB+cC$

The Cayley–Hamilton decomposition gives

$\mathbf {A} ^{-1}={\frac {1}{\det(\mathbf {A} )}}\left({\tfrac {1}{2}}\left[(\operatorname {tr} \mathbf {A} )^{2}-\operatorname {tr} (\mathbf {A} ^{2})\right]\mathbf {I} -\mathbf {A} \operatorname {tr} \mathbf {A} +\mathbf {A} ^{2}\right)$

 The general 3 × 3 inverse can be expressed concisely in terms of the [cross product](https://en.wikipedia.org/wiki/Cross_product) and [triple product](https://en.wikipedia.org/wiki/Triple_product). If a matrix $\mathbf {A} ={\begin{bmatrix}\mathbf {x} _{0}&\mathbf {x} _{1}&\mathbf {x} _{2}\end{bmatrix}}$ (consisting of three column vectors, $\mathbf {x} _{0}$, $\mathbf {x} _{1}$, and $\mathbf {x} _{2}$) is invertible, its inverse is given by

$\mathbf {A} ^{-1}={\frac {1}{\det(\mathbf {A} )}}{\begin{bmatrix}{(\mathbf {x} _{1}\times \mathbf {x} _{2})}^{\mathrm {T} }\\{(\mathbf {x} _{2}\times \mathbf {x} _{0})}^{\mathrm {T} }\\{(\mathbf {x} _{0}\times \mathbf {x} _{1})}^{\mathrm {T} }\end{bmatrix}}$

The determinant of **A**, det(**A**), is equal to the triple product of **x**<sub>0</sub>, **x**<sub>1</sub>, and **x**<sub>2</sub>—the volume of the [parallelepiped](https://en.wikipedia.org/wiki/Parallelepiped) formed by the rows or columns:

$\det(\mathbf {A} )=\mathbf {x} _{0}\cdot (\mathbf {x} _{1}\times \mathbf {x} _{2})$

The correctness of the formula can be checked by using cross- and triple-product properties and by noting that for groups, left and right inverses always coincide. Intuitively, because of the cross products, each row of **A**<sup>–1</sup> is orthogonal to the non-corresponding two columns of **A** (causing the off-diagonal terms of $\mathbf {I} =\mathbf {A} ^{-1}\mathbf {A}$ be zero). Dividing by

$\det(\mathbf {A} )=\mathbf {x} _{0}\cdot (\mathbf {x} _{1}\times \mathbf {x} _{2})$

causes the diagonal entries of **I** = **A**<sup>−1</sup>**A** to be unity. For example, the first diagonal is:

$1={\frac {1}{\mathbf {x_{0}} \cdot (\mathbf {x} _{1}\times \mathbf {x} _{2})}}\mathbf {x_{0}} \cdot (\mathbf {x} _{1}\times \mathbf {x} _{2})$

#### Inversion of 4 × 4 matrices

With increasing dimension, expressions for the inverse of **A** get complicated. For *n* = 4, the Cayley–Hamilton method leads to an expression that is still tractable:

${\begin{aligned}\mathbf {A} ^{-1}={\frac {1}{\det(\mathbf {A} )}}{\Bigl (}&{\tfrac {1}{6}}{\bigl (}(\operatorname {tr} \mathbf {A} )^{3}-3\operatorname {tr} \mathbf {A} \operatorname {tr} (\mathbf {A} ^{2})+2\operatorname {tr} (\mathbf {A} ^{3}){\bigr )}\mathbf {I} \\[-3mu]&\ \ \ -{\tfrac {1}{2}}\mathbf {A} {\bigl (}(\operatorname {tr} \mathbf {A} )^{2}-\operatorname {tr} (\mathbf {A} ^{2}){\bigr )}+\mathbf {A} ^{2}\operatorname {tr} \mathbf {A} -\mathbf {A} ^{3}{\Bigr )}\end{aligned}}$

### Blockwise inversion

Let

$\mathbf {M} ={\begin{bmatrix}\mathbf {A} &\mathbf {B} \\\mathbf {C} &\mathbf {D} \end{bmatrix}}$

where **A**, **B**, **C** and **D** are [matrix sub-blocks](https://en.wikipedia.org/wiki/Block_matrix) of arbitrary size and $\mathbf {M} /\mathbf {A} :=\mathbf {D} -\mathbf {C} \mathbf {A} ^{-1}\mathbf {B}$ is the [Schur complement](https://en.wikipedia.org/wiki/Schur_complement) of **A**. (**A** must be square, so that it can be inverted. Furthermore, **A** and **D** − **CA**<sup>−1</sup>**B** must be nonsingular.)

Matrices can also be *inverted blockwise* by using the analytic inversion formula:

|  |  |  |
|----|----|----|
| ${\begin{bmatrix}\mathbf {A} &\mathbf {B} \\\mathbf {C} &\mathbf {D} \end{bmatrix}}^{-1}={\begin{bmatrix}\mathbf {A} ^{-1}+\mathbf {A} ^{-1}\mathbf {B} \ (\mathbf {M} /\mathbf {A} )^{-1}\mathbf {CA} ^{-1}&-\mathbf {A} ^{-1}\mathbf {B} \left(\mathbf {M} /\mathbf {A} \right)^{-1}\\-\left(\mathbf {M} /\mathbf {A} \right)^{-1}\mathbf {CA} ^{-1}&\left(\mathbf {M} /\mathbf {A} \right)^{-1}\end{bmatrix}},$ |  | 1 |

The strategy is particularly advantageous if **A** is diagonal and **M** / **A** is a small matrix, since they are the only matrices requiring inversion.

The [nullity theorem](https://en.wikipedia.org/wiki/Nullity_theorem) says that the nullity of **A** equals the nullity of the sub-block in the lower right of the inverse matrix, and that the nullity of **B** equals the nullity of the sub-block in the upper right of the inverse matrix.

The inversion procedure that led to Equation (**[1](#math_1)**) performed matrix block operations that operated on **C** and **D** first. Instead, if **A** and **B** are operated on first, and provided **D** and **M** / **D** := **A** − **BD**<sup>−1</sup>**C** are nonsingular, the result is

|  |  |  |
|----|----|----|
| ${\begin{bmatrix}\mathbf {A} &\mathbf {B} \\\mathbf {C} &\mathbf {D} \end{bmatrix}}^{-1}={\begin{bmatrix}\left(\mathbf {M} /\mathbf {D} \right)^{-1}&-\left(\mathbf {M} /\mathbf {D} \right)^{-1}\mathbf {BD} ^{-1}\\-\mathbf {D} ^{-1}\mathbf {C} \left(\mathbf {M} /\mathbf {D} \right)^{-1}&\quad \mathbf {D} ^{-1}+\mathbf {D} ^{-1}\mathbf {C} \left(\mathbf {M} /\mathbf {D} \right)^{-1}\mathbf {BD} ^{-1}\end{bmatrix}}.$ |  | 2 |

Equating the upper-left sub-matrices of Equations (**[1](#math_1)**) and (**[2](#math_2)**) leads to

|  |  |  |
|----|----|----|
| ${\begin{aligned}\left(\mathbf {A} -\mathbf {BD} ^{-1}\mathbf {C} \right)^{-1}&=\mathbf {A} ^{-1}+\mathbf {A} ^{-1}\mathbf {B} \left(\mathbf {D} -\mathbf {CA} ^{-1}\mathbf {B} \right)^{-1}\mathbf {CA} ^{-1}\\\left(\mathbf {A} -\mathbf {BD} ^{-1}\mathbf {C} \right)^{-1}\mathbf {BD} ^{-1}&=\mathbf {A} ^{-1}\mathbf {B} \left(\mathbf {D} -\mathbf {CA} ^{-1}\mathbf {B} \right)^{-1}\\\mathbf {D} ^{-1}\mathbf {C} \left(\mathbf {A} -\mathbf {BD} ^{-1}\mathbf {C} \right)^{-1}&=\left(\mathbf {D} -\mathbf {CA} ^{-1}\mathbf {B} \right)^{-1}\mathbf {CA} ^{-1}\\\mathbf {D} ^{-1}+\mathbf {D} ^{-1}\mathbf {C} \left(\mathbf {A} -\mathbf {BD} ^{-1}\mathbf {C} \right)^{-1}\mathbf {BD} ^{-1}&=\left(\mathbf {D} -\mathbf {CA} ^{-1}\mathbf {B} \right)^{-1}\end{aligned}}$ |  | 3 |

where Equation (**[3](#math_3)**) is the [Woodbury matrix identity](https://en.wikipedia.org/wiki/Woodbury_matrix_identity), which is equivalent to the [binomial inverse theorem](https://en.wikipedia.org/wiki/Binomial_inverse_theorem).

If **A** and **D** are both invertible, then the above two block matrix inverses can be combined to provide the simple factorization

|  |  |  |
|----|----|----|
| ${\begin{bmatrix}\mathbf {A} &\mathbf {B} \\\mathbf {C} &\mathbf {D} \end{bmatrix}}^{-1}={\begin{bmatrix}\left(\mathbf {A} -\mathbf {B} \mathbf {D} ^{-1}\mathbf {C} \right)^{-1}&\mathbf {0} \\\mathbf {0} &\left(\mathbf {D} -\mathbf {C} \mathbf {A} ^{-1}\mathbf {B} \right)^{-1}\end{bmatrix}}{\begin{bmatrix}\mathbf {I} &-\mathbf {B} \mathbf {D} ^{-1}\\-\mathbf {C} \mathbf {A} ^{-1}&\mathbf {I} \end{bmatrix}}.$ |  | 2 |

By the [Weinstein–Aronszajn identity](https://en.wikipedia.org/wiki/Weinstein%E2%80%93Aronszajn_identity), one of the two matrices in the block-diagonal matrix is invertible exactly when the other is.

This formula simplifies significantly when the upper right block matrix **B** is the [zero matrix](https://en.wikipedia.org/wiki/Zero_matrix). This formulation is useful when the matrices **A** and **D** have relatively simple inverse formulas (or [pseudo inverses](https://en.wikipedia.org/wiki/Moore%E2%80%93Penrose_inverse) in the case where the blocks are not all square. In this special case, the block matrix inversion formula stated in full generality above becomes

${\begin{bmatrix}\mathbf {A} &\mathbf {0} \\\mathbf {C} &\mathbf {D} \end{bmatrix}}^{-1}={\begin{bmatrix}\mathbf {A} ^{-1}&\mathbf {0} \\-\mathbf {D} ^{-1}\mathbf {CA} ^{-1}&\mathbf {D} ^{-1}\end{bmatrix}}$

If the given invertible matrix is a symmetric matrix with invertible block **A** the following block inverse formula holds

|  |  |  |
|----|----|----|
| ${\begin{bmatrix}\mathbf {A} &\mathbf {C} ^{T}\\\mathbf {C} &\mathbf {D} \end{bmatrix}}^{-1}={\begin{bmatrix}\mathbf {A} ^{-1}+\mathbf {A} ^{-1}\mathbf {C} ^{T}\mathbf {S} ^{-1}\mathbf {C} \mathbf {A} ^{-1}&-\mathbf {A} ^{-1}\mathbf {C} ^{T}\mathbf {S} ^{-1}\\-\mathbf {S} ^{-1}\mathbf {C} \mathbf {A} ^{-1}&\mathbf {S} ^{-1}\end{bmatrix}},$ |  | 4 |

where $\mathbf {S} =\mathbf {D} -\mathbf {C} \mathbf {A} ^{-1}\mathbf {C} ^{T}$. This requires 2 inversions of the half-sized matrices **A** and **S** and only 4 multiplications of half-sized matrices, if organized properly 

$$
{\begin{aligned}\mathbf {W} _{1}&=\mathbf {C} \mathbf {A} ^{-1},\\[3mu]\mathbf {W} _{2}&=\mathbf {W} _{1}\mathbf {C} ^{T}=\mathbf {C} \mathbf {A} ^{-1}\mathbf {C} ^{T},\\[3mu]\mathbf {W} _{3}&=\mathbf {S} ^{-1}\mathbf {W} _{1}=\mathbf {S} ^{-1}\mathbf {C} \mathbf {A} ^{-1},\\[3mu]\mathbf {W} _{4}&=\mathbf {W} _{1}^{T}\mathbf {W} _{3}=\mathbf {A} ^{-1}\mathbf {C} ^{T}\mathbf {S} ^{-1}\mathbf {C} \mathbf {A} ^{-1},\end{aligned}}
$$

 together with some additions, subtractions, negations and transpositions of negligible complexity. Any matrix $\mathbf {M}$ has an associated positive semidefinite, symmetric matrix $\mathbf {M} ^{T}\mathbf {M}$, which is exactly invertible (and positive definite), if and only if $\mathbf {M}$ is invertible. By writing $\mathbf {M} ^{-1}=\left(\mathbf {M} ^{T}\mathbf {M} \right)^{-1}\mathbf {M} ^{T}$ matrix inversion can be reduced to inverting symmetric matrices and 2 additional matrix multiplications, because the [positive definite matrix](https://en.wikipedia.org/wiki/Definite_matrix#Decomposition) $\mathbf {M} ^{T}\mathbf {M}$ satisfies the invertibility condition for its left upper block **A**.

Those formulas together allow to construct a [divide and conquer algorithm](https://en.wikipedia.org/wiki/Divide_and_conquer_algorithm) that uses blockwise inversion of associated symmetric matrices to invert a matrix with the same time complexity as the [matrix multiplication algorithm](https://en.wikipedia.org/wiki/Matrix_multiplication_algorithm) that is used internally. [Research into matrix multiplication complexity](https://en.wikipedia.org/wiki/Computational_complexity_of_matrix_multiplication) shows that there exist matrix multiplication algorithms with a complexity of *O*(*n*<sup>2.371552</sup>) operations, while the best proven lower bound is [Ω](https://en.wikipedia.org/wiki/Big_O_notation#Family_of_Bachmann–Landau_notations)(*n*<sup>2</sup> log *n*).

### By Neumann series

If a matrix **A** has the property that

$\lim _{n\to \infty }(\mathbf {I} -\mathbf {A} )^{n}=0$

then **A** is nonsingular and its inverse may be expressed by a [Neumann series](https://en.wikipedia.org/wiki/Neumann_series):

$\mathbf {A} ^{-1}=\sum _{n=0}^{\infty }(\mathbf {I} -\mathbf {A} )^{n}$

Truncating the sum results in an "approximate" inverse which may be useful as a [preconditioner](https://en.wikipedia.org/wiki/Preconditioner). Note that a truncated series can be accelerated exponentially by noting that the Neumann series is a [geometric sum](https://en.wikipedia.org/wiki/Geometric_sum). As such, it satisfies

$\sum _{n=0}^{2^{L}-1}(\mathbf {I} -\mathbf {A} )^{n}=\prod _{l=0}^{L-1}\left(\mathbf {I} +(\mathbf {I} -\mathbf {A} )^{2^{l}}\right)$

Therefore, only 2*L* − 2 matrix multiplications are needed to compute 2<sup>*L*</sup> terms of the sum.

More generally, if **A** is "near" the invertible matrix **X** in the sense that

$\lim _{n\to \infty }\left(\mathbf {I} -\mathbf {X} ^{-1}\mathbf {A} \right)^{n}=0\mathrm {~~or~~} \lim _{n\to \infty }\left(\mathbf {I} -\mathbf {A} \mathbf {X} ^{-1}\right)^{n}=0$

then **A** is nonsingular and its inverse is

$\mathbf {A} ^{-1}=\sum _{n=0}^{\infty }\left(\mathbf {X} ^{-1}(\mathbf {X} -\mathbf {A} )\right)^{n}\mathbf {X} ^{-1}~$

If it is also the case that **A** − **X** has [rank](https://en.wikipedia.org/wiki/Rank_(linear_algebra) "Rank (linear algebra)") 1 then this simplifies to

$\mathbf {A} ^{-1}=\mathbf {X} ^{-1}-{\frac {\mathbf {X} ^{-1}(\mathbf {A} -\mathbf {X} )\mathbf {X} ^{-1}}{1+\operatorname {tr} \left(\mathbf {X} ^{-1}(\mathbf {A} -\mathbf {X} )\right)}}~$

### *p*-adic approximation

If **A** is a matrix with [integer](https://en.wikipedia.org/wiki/Integer) or [rational](https://en.wikipedia.org/wiki/Rational_number) entries, and we seek a solution in [arbitrary-precision](https://en.wikipedia.org/wiki/Arbitrary-precision_arithmetic) rationals, a [p-adic](https://en.wikipedia.org/wiki/P-adic) approximation method converges to an exact solution in O(*n*<sup>4</sup> log<sup>2</sup> *n*), assuming standard O(*n*<sup>3</sup>) matrix multiplication is used. The method relies on solving n linear systems via Dixon's method of p-adic approximation (each in O(*n*<sup>3</sup> log<sup>2</sup> *n*)) and is available as such in software specialized in arbitrary-precision matrix operations, for example, in IML.

### Reciprocal basis vectors method

Given an *n* × *n* square matrix $\mathbf {X} =\left[x^{ij}\right]$, $1\leq i,j\leq n$, with n rows interpreted as n vectors $\mathbf {x} _{i}=x^{ij}\mathbf {e} _{j}$ ([Einstein summation](https://en.wikipedia.org/wiki/Einstein_summation) assumed) where the $\mathbf {e} _{j}$ are a standard [orthonormal basis](https://en.wikipedia.org/wiki/Orthonormal_basis) of [Euclidean space](https://en.wikipedia.org/wiki/Euclidean_space) $\mathbb {R} ^{n}$ ($\mathbf {e} _{i}=\mathbf {e} ^{i},\mathbf {e} _{i}\cdot \mathbf {e} ^{j}=\delta _{i}^{j}$), then using [Clifford algebra](https://en.wikipedia.org/wiki/Clifford_algebra) (or [geometric algebra](https://en.wikipedia.org/wiki/Geometric_algebra)) we compute the reciprocal (sometimes called [dual](https://en.wikipedia.org/wiki/Geometric_algebra#Dual_basis)) column vectors:

$\mathbf {x} ^{i}=x_{ji}\mathbf {e} ^{j}=(-1)^{i-1}(\mathbf {x} _{1}\wedge \cdots \wedge ()_{i}\wedge \cdots \wedge \mathbf {x} _{n})\cdot (\mathbf {x} _{1}\wedge \ \mathbf {x} _{2}\wedge \cdots \wedge \mathbf {x} _{n})^{-1}$

as the columns of the inverse matrix $\mathbf {X} ^{-1}=[x_{ji}].$ Note that, the place "$()_{i}$" indicates that "$\mathbf {x} _{i}$" is removed from that place in the above expression for $\mathbf {x} ^{i}$. We then have $\mathbf {X} \mathbf {X} ^{-1}=\left[\mathbf {x} _{i}\cdot \mathbf {x} ^{j}\right]=\left[\delta _{i}^{j}\right]=\mathbf {I} _{n}$, where $\delta _{i}^{j}$ is the [Kronecker delta](https://en.wikipedia.org/wiki/Kronecker_delta). We also have $\mathbf {X} ^{-1}\mathbf {X} =\left[\left(\mathbf {e} _{i}\cdot \mathbf {x} ^{k}\right)\left(\mathbf {e} ^{j}\cdot \mathbf {x} _{k}\right)\right]=\left[\mathbf {e} _{i}\cdot \mathbf {e} ^{j}\right]=\left[\delta _{i}^{j}\right]=\mathbf {I} _{n}$, as required. If the vectors $\mathbf {x} _{i}$ are not linearly independent, then $(\mathbf {x} _{1}\wedge \mathbf {x} _{2}\wedge \cdots \wedge \mathbf {x} _{n})=0$ and the matrix $\mathbf {X}$ is not invertible (has no inverse).

## Properties

### Singularity

Over a [field](https://en.wikipedia.org/wiki/Field_(mathematics) "Field (mathematics)"), a square matrix that is *not* invertible is called **singular** or **degenerate**. A square matrix with entries in a field is singular [if and only if](https://en.wikipedia.org/wiki/If_and_only_if) its [[Determinant]] is zero.

### Invertible matrix theorem

Let **A** be a square n-by-n matrix over a [field](https://en.wikipedia.org/wiki/Field_(mathematics) "Field (mathematics)") K (e.g., the field $\mathbb {R}$ of real numbers). The following statements are equivalent, i.e., they are either all true or all false for any given matrix:

- **A** is invertible, i.e. it has an inverse under matrix multiplication, i.e., there exists a **B** such that **AB** = **I**<sub>*n*</sub> = **BA**. (In that statement, "invertible" can equivalently be replaced with "left-invertible" or "right-invertible" in which one-sided inverses are considered.)
- The linear transformation mapping **x** to **Ax** is invertible, i.e., it has an inverse under function composition. (There, again, "invertible" can equivalently be replaced with either "left-invertible" or "right-invertible".)
- The [transpose](https://en.wikipedia.org/wiki/Transpose) **A**<sup>T</sup> is an invertible matrix.
- **A** is [row-equivalent](https://en.wikipedia.org/wiki/Row_equivalence) to the n-by-n [identity matrix](https://en.wikipedia.org/wiki/Identity_matrix) **I**<sub>*n*</sub>.
- **A** is [column-equivalent](https://en.wikipedia.org/wiki/Row_equivalence) to the n-by-n identity matrix **I**<sub>*n*</sub>.
- **A** has n [pivot positions](https://en.wikipedia.org/wiki/Pivot_position).
- **A** has full [rank](https://en.wikipedia.org/wiki/Rank_(linear_algebra) "Rank (linear algebra)"): rank **A** = *n*.
- **A** has a trivial [kernel](https://en.wikipedia.org/wiki/Kernel_(linear_algebra) "Kernel (linear algebra)"): ker(**A**) = {**0**}.
- The linear transformation mapping **x** to **Ax** is bijective; that is, the equation **Ax** = **b** has exactly one solution for each **b** in K<sup>n</sup>. (There, "bijective" can equivalently be replaced with "[injective](https://en.wikipedia.org/wiki/Injective)" or "[surjective](https://en.wikipedia.org/wiki/Surjective)".)
- The columns of **A** form a [basis](https://en.wikipedia.org/wiki/Basis_of_a_vector_space) of K<sup>n</sup>. (In this statement, "basis" can equivalently be replaced with either "linearly independent set" or "spanning set")
- The rows of **A** form a basis of K<sup>n</sup>. (Similarly, here, "basis" can equivalently be replaced with either "linearly independent set" or "spanning set")
- The [[Determinant]] of **A** is nonzero: det **A** ≠ 0. In general, a square matrix over a [commutative ring](https://en.wikipedia.org/wiki/Commutative_ring) is invertible if and only if its determinant is a [unit](https://en.wikipedia.org/wiki/Unit_(ring_theory) "Unit (ring theory)") (i.e. multiplicatively invertible element) of that ring.
- The number 0 is not an [eigenvalue](https://en.wikipedia.org/wiki/Eigenvalue) of **A**. (More generally, a number $\lambda$ is an eigenvalue of **A** if the matrix $\mathbf {A} -\lambda \mathbf {I}$ is singular, where **I** is the identity matrix.)
- The matrix **A** can be expressed as a finite product of [elementary matrices](https://en.wikipedia.org/wiki/Elementary_matrix).

### Other properties

Furthermore, the following properties hold for an invertible matrix **A**:

- $(\mathbf {A} ^{-1})^{-1}=\mathbf {A}$
- $(k\mathbf {A} )^{-1}=k^{-1}\mathbf {A} ^{-1}$ for nonzero scalar k
- $(\mathbf {Ax} )^{+}=\mathbf {x} ^{+}\mathbf {A} ^{-1}$ if **A** has orthonormal columns, where <sup>+</sup> denotes the [Moore–Penrose inverse](https://en.wikipedia.org/wiki/Moore%E2%80%93Penrose_inverse) and **x** is a vector
- $(\mathbf {A} ^{\mathrm {T} })^{-1}=(\mathbf {A} ^{-1})^{\mathrm {T} }$
- For any invertible n-by-n matrices **A** and **B**, $(\mathbf {AB} )^{-1}=\mathbf {B} ^{-1}\mathbf {A} ^{-1}.$ More generally, if $\mathbf {A} _{1},\dots ,\mathbf {A} _{k}$ are invertible n-by-n matrices, then $(\mathbf {A} _{1}\mathbf {A} _{2}\cdots \mathbf {A} _{k-1}\mathbf {A} _{k})^{-1}=\mathbf {A} _{k}^{-1}\mathbf {A} _{k-1}^{-1}\cdots \mathbf {A} _{2}^{-1}\mathbf {A} _{1}^{-1}.$
- $\det \mathbf {A} ^{-1}=(\det \mathbf {A} )^{-1}.$
- Left and right inverses are equal. That is, if $\mathbf {LA} =\mathbf {I}$ and $\mathbf {AR} =\mathbf {I}$ then $\mathbf {L} =\mathbf {L} (\mathbf {AR} )=(\mathbf {LA} )\mathbf {R} =\mathbf {R}$.

The rows of the inverse matrix **V** of a matrix **U** are [orthonormal](https://en.wikipedia.org/wiki/Orthonormal) to the columns of **U** (and vice versa interchanging rows for columns). To see this, suppose that **UV** = **VU** = **I** where the rows of **V** are denoted as $v_{i}^{\mathrm {T} }$ and the columns of **U** as $u_{j}$ for $1\leq i,j\leq n.$ Then clearly, the [Euclidean inner product](https://en.wikipedia.org/wiki/Dot_product) of any two $v_{i}^{\mathrm {T} }u_{j}=\delta _{i,j}.$ This property can also be useful in constructing the inverse of a square matrix in some instances, where a set of [orthogonal](https://en.wikipedia.org/wiki/Orthogonal) vectors (but not necessarily orthonormal vectors) to the columns of **U** are known. In which case, one can apply the iterative [Gram–Schmidt process](https://en.wikipedia.org/wiki/Gram%E2%80%93Schmidt_process) to this initial set to determine the rows of the inverse **V**.

A matrix that is its own inverse (i.e., a matrix **A** such that **A** = **A**<sup>−1</sup> and consequently **A**<sup>2</sup> = **I**) is called an [involutory matrix](https://en.wikipedia.org/wiki/Involutory_matrix).

### In relation to its adjugate

The [adjugate](https://en.wikipedia.org/wiki/Adjugate_matrix) of a matrix **A** can be used to find the inverse of **A** as follows:

If **A** is an invertible matrix, then

$\mathbf {A} ^{-1}={\frac {1}{\det(\mathbf {A} )}}\operatorname {adj} (\mathbf {A} )$

### In relation to the identity matrix

It follows from the [associativity](https://en.wikipedia.org/wiki/Associativity) of matrix multiplication that if

$\mathbf {AB} =\mathbf {I} \$

for *finite square* matrices **A** and **B**, then also

$\mathbf {BA} =\mathbf {I} \$

### Density

Over the field of real numbers, the set of singular n-by-n matrices, considered as a [subset](https://en.wikipedia.org/wiki/Subset) of $\mathbb {R} ^{n\times n},$ is a [null set](https://en.wikipedia.org/wiki/Null_set), that is, has [Lebesgue measure](https://en.wikipedia.org/wiki/Lebesgue_measure) zero. That is true because singular matrices are the roots of the [[Determinant]] function. It is a [continuous function](https://en.wikipedia.org/wiki/Continuous_function) because it is a [polynomial](https://en.wikipedia.org/wiki/Polynomial) in the entries of the matrix. Thus in the language of [measure theory](https://en.wikipedia.org/wiki/Measure_theory), [almost all](https://en.wikipedia.org/wiki/Almost_all) n-by-n matrices are invertible.

Furthermore, the set of n-by-n invertible matrices is [open](https://en.wikipedia.org/wiki/Open_set) and [dense](https://en.wikipedia.org/wiki/Dense_set) in the [topological space](https://en.wikipedia.org/wiki/Topological_space) of all n-by-n matrices. Equivalently, the set of singular matrices is [closed](https://en.wikipedia.org/wiki/Closed_set) and [nowhere dense](https://en.wikipedia.org/wiki/Nowhere_dense) in the space of n-by-n matrices.

In practice, however, non-invertible matrices may be encountered. In [numerical calculations](https://en.wikipedia.org/wiki/Numerical_analysis), matrices that are invertible but close to a non-invertible matrix may still be problematic and are said to be [[Condition Number|ill-conditioned]].

## Derivative of the matrix inverse

Suppose that the invertible matrix **A** depends on a parameter *t*. Then the [derivative](https://en.wikipedia.org/wiki/Derivative_of_matrix) of the inverse of **A** with respect to *t* is given by

${\frac {\mathrm {d} }{\mathrm {d} t}}\mathbf {A} ^{-1}=-\mathbf {A} ^{-1}{\frac {\mathrm {d} \mathbf {A} }{\mathrm {d} t}}\mathbf {A} ^{-1}$

To derive the above expression for the derivative of the inverse of **A**, one can differentiate the definition of the matrix inverse $\mathbf {A} ^{-1}\mathbf {A} =\mathbf {I}$ using the [product rule](https://en.wikipedia.org/wiki/Product_rule), and then solve for the derivative of the inverse of **A**:

$\mathbf {0} ={\frac {\mathrm {d} \mathbf {I} }{\mathrm {d} t}}={\frac {\mathrm {d} (\mathbf {A} ^{-1}\mathbf {A} )}{\mathrm {d} t}}={\frac {\mathrm {d} (\mathbf {A} ^{-1})}{\mathrm {d} t}}\mathbf {A} +\mathbf {A} ^{-1}{\frac {\mathrm {d} \mathbf {A} }{\mathrm {d} t}}$

Subtracting $\mathbf {A} ^{-1}{\frac {\mathrm {d} \mathbf {A} }{\mathrm {d} t}}$ from both ends of this formula, and multiplying on the right by $\mathbf {A} ^{-1}$ finishes the derivation.

If $\varepsilon$ is a small number then the derivative formula gives:

$\left(\mathbf {A} +\varepsilon \mathbf {X} \right)^{-1}=\mathbf {A} ^{-1}-\varepsilon \mathbf {A} ^{-1}\mathbf {X} \mathbf {A} ^{-1}+{\mathcal {O}}(\varepsilon ^{2})\,$

Given a positive integer $n$,

${\begin{aligned}{\frac {\mathrm {d} }{\mathrm {d} t}}\mathbf {A} ^{n}&=\sum _{i=1}^{n}\mathbf {A} ^{i-1}{\frac {\mathrm {d} \mathbf {A} }{\mathrm {d} t}}\mathbf {A} ^{n-i},\\{\frac {\mathrm {d} }{\mathrm {d} t}}\mathbf {A} ^{-n}&=-\sum _{i=1}^{n}\mathbf {A} ^{-i}{\frac {\mathrm {d} \mathbf {A} }{\mathrm {d} t}}\mathbf {A} ^{-(n+1-i)}\end{aligned}}$

In particular,

${\begin{aligned}(\mathbf {A} +\varepsilon \mathbf {X} )^{n}&=\mathbf {A} ^{n}+\varepsilon \sum _{i=1}^{n}\mathbf {A} ^{i-1}\mathbf {X} \mathbf {A} ^{n-i}+{\mathcal {O}}\left(\varepsilon ^{2}\right),\\(\mathbf {A} +\varepsilon \mathbf {X} )^{-n}&=\mathbf {A} ^{-n}-\varepsilon \sum _{i=1}^{n}\mathbf {A} ^{-i}\mathbf {X} \mathbf {A} ^{-(n+1-i)}+{\mathcal {O}}\left(\varepsilon ^{2}\right)\end{aligned}}$

## Generalizations

### Non-square matrices

Non-square matrices, i.e. m-by-n matrices for which *m* ≠ *n*, do not have an inverse. However, in some cases such a matrix may have a [left inverse](https://en.wikipedia.org/wiki/Inverse_element#Matrices) or [right inverse](https://en.wikipedia.org/wiki/Inverse_element#Matrices). If **A** is m-by-n and the [rank](https://en.wikipedia.org/wiki/Rank_(linear_algebra) "Rank (linear algebra)") of **A** is equal to *n*, (*n* ≤ *m*), then **A** has a left inverse, an *n*-by-*m* matrix **B** such that **BA** = **I**<sub>*n*</sub>. If **A** has rank *m* (*m* ≤ *n*), then it has a right inverse, an n-by-m matrix **B** such that **AB** = **I**<sub>*m*</sub>.

Some of the properties of inverse matrices are shared by [generalized inverses](https://en.wikipedia.org/wiki/Generalized_inverse) (such as the [Moore–Penrose inverse](https://en.wikipedia.org/wiki/Moore%E2%80%93Penrose_inverse)), which can be defined for any *m*-by-*n* matrix.

### In Abstract algebra

While the most common case is that of matrices over the [real](https://en.wikipedia.org/wiki/Real_number) or [complex](https://en.wikipedia.org/wiki/Complex_number) numbers, all of those definitions can be given for matrices over any [algebraic structure](https://en.wikipedia.org/wiki/Algebraic_structure) equipped with [addition](https://en.wikipedia.org/wiki/Addition) and [multiplication](https://en.wikipedia.org/wiki/Multiplication) (i.e. [rings](https://en.wikipedia.org/wiki/Ring_(mathematics) "Ring (mathematics)")). However, in the case of a ring being [commutative](https://en.wikipedia.org/wiki/Commutative_ring), the condition for a square matrix to be invertible is that its determinant is invertible in the ring, which in general is a stricter requirement than it being nonzero. For a [noncommutative ring](https://en.wikipedia.org/wiki/Noncommutative_ring), the usual determinant is not defined. The conditions for existence of left-inverse or right-inverse are more complicated, since a notion of rank does not exist over rings.

The set of *n* × *n* invertible matrices together with the operation of [[Matrix Multiplication]] and entries from ring R form a [group](https://en.wikipedia.org/wiki/Group_(mathematics) "Group (mathematics)"), the [general linear group](https://en.wikipedia.org/wiki/General_linear_group) of degree n, denoted GL<sub>*n*</sub>(*R*).

## Applications

For most practical applications, it is not necessary to invert a matrix to solve a [system of linear equations](https://en.wikipedia.org/wiki/System_of_linear_equations); however, for a unique solution, it is necessary for the matrix involved to be invertible.

Decomposition techniques like [[LU Decomposition]] are much faster than inversion, and various fast algorithms for special classes of linear systems have also been developed.

### Regression/least squares

Although an explicit inverse is not necessary to estimate the vector of unknowns, it is the easiest way to estimate their accuracy and is found in the diagonal of a matrix inverse (the posterior covariance matrix of the vector of unknowns). However, faster algorithms to compute only the diagonal entries of a matrix inverse are known in many cases.

### Matrix inverses in real-time simulations

### Matrix inverses in MIMO wireless communication

Matrix inversion also plays a significant role in the [MIMO](https://en.wikipedia.org/wiki/MIMO) (Multiple-Input, Multiple-Output) technology in [wireless communications](https://en.wikipedia.org/wiki/Wireless_communications). The MIMO system consists of *N* transmit and *M* receive antennas. Unique signals, occupying the same [frequency band](https://en.wikipedia.org/wiki/Frequency_band), are sent via *N* transmit antennas and are received via *M* receive antennas. The signal arriving at each receive antenna will be a [linear combination](https://en.wikipedia.org/wiki/Linear_combination) of the *N* transmitted signals forming an *N* × *M* transmission matrix **H**. It is crucial for the matrix **H** to be invertible so that the receiver can figure out the transmitted information.

## See also

- [Singular matrix](https://en.wikipedia.org/wiki/Singular_matrix)
- [Binomial inverse theorem](https://en.wikipedia.org/wiki/Binomial_inverse_theorem)
- [[LU Decomposition]]
- [Matrix decomposition](https://en.wikipedia.org/wiki/Matrix_decomposition)
- [Matrix square root](https://en.wikipedia.org/wiki/Matrix_square_root)
- [Minor (linear algebra)](https://en.wikipedia.org/wiki/Minor_(linear_algebra) "Minor (linear algebra)")
- [Partial inverse of a matrix](https://en.wikipedia.org/wiki/Partial_inverse_of_a_matrix)
- [Pseudoinverse](https://en.wikipedia.org/wiki/Pseudoinverse)
- [Rybicki Press algorithm](https://en.wikipedia.org/wiki/Rybicki_Press_algorithm)
- [[Singular Value Decomposition]]
- [Woodbury matrix identity](https://en.wikipedia.org/wiki/Woodbury_matrix_identity)

## References

1.  [Axler, Sheldon](https://en.wikipedia.org/wiki/Sheldon_Axler) (18 December 2014). *Linear Algebra Done Right*. [Undergraduate Texts in Mathematics](https://en.wikipedia.org/wiki/Undergraduate_Texts_in_Mathematics) (3rd ed.). [Springer Publishing](https://en.wikipedia.org/wiki/Springer_Publishing) (published 2015). p. 296. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-319-11079-0](https://en.wikipedia.org/wiki/Special:BookSources/978-3-319-11079-0).
2.  J.-S. Roger Jang (March 2001). ["Matrix Inverse in Block Form"](https://www.cs.nthu.edu.tw/~jang/book/addenda/matinv/matinv/).
3.  Pan, Victor; Reif, John (1985), *Efficient Parallel Solution of Linear Systems*, Proceedings of the 17th Annual ACM Symposium on Theory of Computing, Providence: [ACM](https://en.wikipedia.org/wiki/Association_for_Computing_Machinery)
5.  A proof can be found in the Appendix B of Kondratyuk, L. A.; Krivoruchenko, M. I. (1992). ["Superconducting quark matter in SU(2) color group"](https://www.researchgate.net/publication/226920070). *Zeitschrift für Physik A*. **344** (1): 99–115. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1992ZPhyA.344...99K](https://ui.adsabs.harvard.edu/abs/1992ZPhyA.344...99K). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/BF01291027](https://doi.org/10.1007%2FBF01291027). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [120467300](https://api.semanticscholar.org/CorpusID:120467300).
6.  Strang, Gilbert (2003). [Introduction to linear algebra](https://books.google.com/books?id=Gv4pCVyoUVYC) (3rd ed.). SIAM. p. 71. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-9614088-9-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-9614088-9-3)., [Chapter 2, page 71](https://books.google.com/books?id=Gv4pCVyoUVYC&pg=PA71)
7.  Bernstein, Dennis (2005). *Matrix Mathematics*. Princeton University Press. p. 44. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-691-11802-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-691-11802-4).
8.  Tzon-Tzer, Lu; Sheng-Hua, Shiou (2002). "Inverses of 2 × 2 block matrices". *Computers & Mathematics with Applications*. **43** (1–2): 119–129. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/S0898-1221(01)00278-4](https://doi.org/10.1016%2FS0898-1221%2801%2900278-4).
9.  Bernstein, Dennis (2005). *Matrix Mathematics*. Princeton University Press. p. 45. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-691-11802-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-691-11802-4).
10. ^   T. H. Cormen, C. E. Leiserson, R. L. Rivest, C. Stein, *Introduction to Algorithms*, 3rd ed., MIT Press, Cambridge, MA, 2009, §28.2.
11. [Ran Raz](https://en.wikipedia.org/wiki/Ran_Raz). On the complexity of matrix product. In Proceedings of the thirty-fourth annual ACM symposium on Theory of computing. ACM Press, 2002. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1145/509907.509932](https://doi.org/10.1145%2F509907.509932).
12. Stewart, Gilbert (1998). *Matrix Algorithms: Basic decompositions*. SIAM. p. 55. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-89871-414-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-89871-414-2).
13. Haramoto, H.; Matsumoto, M. (2009). ["A p-adic algorithm for computing the inverse of integer matrices"](https://doi.org/10.1016%2Fj.cam.2008.07.044). *Journal of Computational and Applied Mathematics*. **225** (1): 320–322. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2009JCoAM.225..320H](https://ui.adsabs.harvard.edu/abs/2009JCoAM.225..320H). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.cam.2008.07.044](https://doi.org/10.1016%2Fj.cam.2008.07.044).
14. ["IML - Integer Matrix Library"](https://cs.uwaterloo.ca/~astorjoh/iml.html). *cs.uwaterloo.ca*. Retrieved 14 April 2018.
15. Weisstein, Eric W. ["Invertible Matrix Theorem"](https://mathworld.wolfram.com/InvertibleMatrixTheorem.html). *mathworld.wolfram.com*. Retrieved 2020-09-08.
16. Horn, Roger A.; Johnson, Charles R. (1985). *Matrix Analysis*. [Cambridge University Press](https://en.wikipedia.org/wiki/Cambridge_University_Press). p. 14. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-38632-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-38632-6)..
17. Magnus, Jan R.; Neudecker, Heinz (1999). *Matrix Differential Calculus : with Applications in Statistics and Econometrics* (Revised ed.). New York: John Wiley & Sons. pp. 151–152. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-98633-X](https://en.wikipedia.org/wiki/Special:BookSources/0-471-98633-X).
18. [Roman, Stephen](https://en.wikipedia.org/wiki/Steven_Roman) (2008), *Advanced Linear Algebra*, [Graduate Texts in Mathematics](https://en.wikipedia.org/wiki/Graduate_Texts_in_Mathematics) (Third ed.), Springer, p. 446, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-72828-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-72828-5).
19. Lin, Lin; Lu, Jianfeng; Ying, Lexing; Car, Roberto; E, Weinan (2009). ["Fast algorithm for extracting the diagonal of the inverse matrix with application to the electronic structure analysis of metallic systems"](https://doi.org/10.4310%2FCMS.2009.v7.n3.a12). *Communications in Mathematical Sciences*. **7** (3): 755–777. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.4310/CMS.2009.v7.n3.a12](https://doi.org/10.4310%2FCMS.2009.v7.n3.a12).
20. Albreem, M.; Juntti, M.; Shahabuddin, S. (January 2020). "Efficient initialisation of iterative linear massive MIMO detectors using a stair matrix". *[Electronics Letters](https://en.wikipedia.org/wiki/Electronics_Letters)*. **56** (1): 50–52. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2020ElL....56...50A](https://ui.adsabs.harvard.edu/abs/2020ElL....56...50A). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1049/el.2019.2938](https://doi.org/10.1049%2Fel.2019.2938).

## Further reading

- ["Inversion of a matrix"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society), 2001 \[1994\]
- [Cormen, Thomas H.](https://en.wikipedia.org/wiki/Thomas_H._Cormen); [Leiserson, Charles E.](https://en.wikipedia.org/wiki/Charles_E._Leiserson); [Rivest, Ronald L.](https://en.wikipedia.org/wiki/Ron_Rivest); [Stein, Clifford](https://en.wikipedia.org/wiki/Clifford_Stein) (2001) \[1990\]. "28.4: Inverting matrices". [*Introduction to Algorithms*](https://en.wikipedia.org/wiki/Introduction_to_Algorithms) (2nd ed.). MIT Press and McGraw-Hill. pp. 755–760. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-262-03293-7](https://en.wikipedia.org/wiki/Special:BookSources/0-262-03293-7).
- Bernstein, Dennis S. (2009). [Matrix Mathematics: Theory, Facts, and Formulas](https://books.google.com/books?id=jgEiuHlTCYcC) (2nd ed.). Princeton University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0691140391](https://en.wikipedia.org/wiki/Special:BookSources/978-0691140391) – via [Google Books](https://en.wikipedia.org/wiki/Google_Books).
- Petersen, Kaare Brandt; Pedersen, Michael Syskind (November 15, 2012). ["The Matrix Cookbook"](https://www2.imm.dtu.dk/pubdb/views/edoc_download.php/3274/pdf/imm3274.pdf#page=17) (PDF). pp. 17–23.

## External links

- [Sanderson, Grant](https://en.wikipedia.org/wiki/Grant_Sanderson) (August 15, 2016). ["Inverse Matrices, Column Space and Null Space"](https://www.youtube.com/watch?v=uQhTuRlWMxw&list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab&index=7). *Essence of Linear Algebra*. [Archived](https://ghostarchive.org/varchive/youtube/20211103/uQhTuRlWMxw) from the original on 2021-11-03 – via [YouTube](https://en.wikipedia.org/wiki/YouTube).
- [Strang, Gilbert](https://en.wikipedia.org/wiki/Gilbert_Strang). ["Linear Algebra Lecture on Inverse Matrices"](https://ocw.mit.edu/courses/mathematics/18-06-linear-algebra-spring-2010/video-lectures/lecture-3-multiplication-and-inverse-matrices/). *[MIT OpenCourseWare](https://en.wikipedia.org/wiki/MIT_OpenCourseWare)*.
