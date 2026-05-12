[[numerical-methods.base]]

> Source: [[QR Decomposition]]
> License: Wikipedia content is available under CC BY-SA 4.0.

In [linear algebra](https://en.wikipedia.org/wiki/Linear_algebra), a **QR decomposition**, also known as a **QR factorization** or **QU factorization**, is a [decomposition](https://en.wikipedia.org/wiki/Matrix_decomposition) of a [matrix](https://en.wikipedia.org/wiki/Matrix_(mathematics) "Matrix (mathematics)") *A* into a product *A* = *QR* of an [orthonormal matrix](https://en.wikipedia.org/wiki/Orthonormal_matrix) *Q* and an [upper triangular matrix](https://en.wikipedia.org/wiki/Upper_triangular_matrix) *R*. QR decomposition is often used to solve the [linear least squares](https://en.wikipedia.org/wiki/Linear_least_squares_(mathematics)) (LLS) problem and is the basis for a particular [eigenvalue algorithm](https://en.wikipedia.org/wiki/Eigenvalue_algorithm), the [QR algorithm](https://en.wikipedia.org/wiki/QR_algorithm).

## Cases and definitions

### Square matrix

Any real [square matrix](https://en.wikipedia.org/wiki/Square_matrix) *A* may be decomposed as

$A=QR,$

where *Q* is an [orthogonal matrix](https://en.wikipedia.org/wiki/Orthogonal_matrix) (its columns are [orthogonal](https://en.wikipedia.org/wiki/Orthogonal) [unit vectors](https://en.wikipedia.org/wiki/Unit_vector) meaning $Q^{\textsf {T}}=Q^{-1}$) and *R* is an upper [triangular matrix](https://en.wikipedia.org/wiki/Triangular_matrix) (also called right triangular matrix). If *A* is [invertible](https://en.wikipedia.org/wiki/Invertible_matrix), then the factorization is unique if we require the diagonal elements of *R* to be positive.

If instead *A* is a complex square matrix, then there is a decomposition *A* = *QR* where *Q* is a [unitary matrix](https://en.wikipedia.org/wiki/Unitary_matrix) (so the [conjugate transpose](https://en.wikipedia.org/wiki/Conjugate_transpose) $Q^{\dagger }=Q^{-1}$).

If *A* has *n* [linearly independent](https://en.wikipedia.org/wiki/Linearly_independent) columns, then the first *n* columns of *Q* form an [orthonormal basis](https://en.wikipedia.org/wiki/Orthonormal_basis) for the [column space](https://en.wikipedia.org/wiki/Column_space) of *A*. More generally, the first *k* columns of *Q* form an orthonormal basis for the [span](https://en.wikipedia.org/wiki/Linear_span) of the first *k* columns of *A* for any 1 ≤ *k* ≤ *n*. The fact that any column *k* of *A* only depends on the first *k* columns of *Q* corresponds to the triangular form of *R*.

### Rectangular matrix

More generally, we can factor a complex *m*×*n* matrix *A*, with *m* ≥ *n*, as the product of an *m*×*m* [unitary matrix](https://en.wikipedia.org/wiki/Unitary_matrix) *Q* and an *m*×*n* upper triangular matrix *R*. As the bottom (*m*−*n*) rows of an *m*×*n* upper triangular matrix consist entirely of zeroes, it is often useful to partition *R*, or both *R* and *Q*:

$A=QR=Q{\begin{bmatrix}R_{1}\\0\end{bmatrix}}={\begin{bmatrix}Q_{1}&Q_{2}\end{bmatrix}}{\begin{bmatrix}R_{1}\\0\end{bmatrix}}=Q_{1}R_{1},$

where *R*<sub>1</sub> is an *n*×*n* upper triangular matrix, 0 is an (*m* − *n*)×*n* [zero matrix](https://en.wikipedia.org/wiki/Zero_matrix), *Q*<sub>1</sub> is *m*×*n*, *Q*<sub>2</sub> is *m*×(*m* − *n*), and *Q*<sub>1</sub> and *Q*<sub>2</sub> both have orthogonal columns.

, §5.2) call *Q*<sub>1</sub>*R*<sub>1</sub> the *thin QR factorization* of *A*; Trefethen and Bau call this the *reduced QR factorization*. If *A* is of full [rank](https://en.wikipedia.org/wiki/Matrix_rank) *n* and we require that the diagonal elements of *R*<sub>1</sub> are positive then *R*<sub>1</sub> and *Q*<sub>1</sub> are unique, but in general *Q*<sub>2</sub> is not. *R*<sub>1</sub> is then equal to the upper triangular factor of the [[Cholesky Decomposition]] of *A*\* *A* (= *A*<sup>T</sup>*A* if *A* is real).

### QL, RQ and LQ decompositions

Analogously, we can define QL, RQ, and LQ decompositions, with *L* being a *lower* triangular matrix.

## Computing the QR decomposition

There are several methods for actually computing the QR decomposition, such as the [Gram–Schmidt process](https://en.wikipedia.org/wiki/Gram%E2%80%93Schmidt_process), [Householder transformations](https://en.wikipedia.org/wiki/Householder_transformation), or [Givens rotations](https://en.wikipedia.org/wiki/Givens_rotation). Each has a number of advantages and disadvantages.

### Using the Gram–Schmidt process

Consider the [Gram–Schmidt process](https://en.wikipedia.org/wiki/Gram%E2%80%93Schmidt_process) applied to the columns of the full column rank matrix $A={\begin{bmatrix}\mathbf {a} _{1}&\cdots &\mathbf {a} _{n}\end{bmatrix}}$, with [inner product](https://en.wikipedia.org/wiki/Inner_product) $\langle \mathbf {v} ,\mathbf {w} \rangle =\mathbf {v} ^{\textsf {T}}\mathbf {w}$ (or $\langle \mathbf {v} ,\mathbf {w} \rangle =\mathbf {v} ^{\dagger }\mathbf {w}$ for the complex case).

Define the [projection](https://en.wikipedia.org/wiki/Vector_projection):

$\operatorname {proj} _{\mathbf {u} }\mathbf {a} ={\frac {\left\langle \mathbf {u} ,\mathbf {a} \right\rangle }{\left\langle \mathbf {u} ,\mathbf {u} \right\rangle }}{\mathbf {u} }$

then:

${\begin{aligned}\mathbf {u} _{1}&=\mathbf {a} _{1},&\mathbf {e} _{1}&={\frac {\mathbf {u} _{1}}{\|\mathbf {u} _{1}\|}}\\\mathbf {u} _{2}&=\mathbf {a} _{2}-\operatorname {proj} _{\mathbf {u} _{1}}\mathbf {a} _{2},&\mathbf {e} _{2}&={\frac {\mathbf {u} _{2}}{\|\mathbf {u} _{2}\|}}\\\mathbf {u} _{3}&=\mathbf {a} _{3}-\operatorname {proj} _{\mathbf {u} _{1}}\mathbf {a} _{3}-\operatorname {proj} _{\mathbf {u} _{2}}\mathbf {a} _{3},&\mathbf {e} _{3}&={\frac {\mathbf {u} _{3}}{\|\mathbf {u} _{3}\|}}\\&\;\;\vdots &&\;\;\vdots \\\mathbf {u} _{k}&=\mathbf {a} _{k}-\sum _{j=1}^{k-1}\operatorname {proj} _{\mathbf {u} _{j}}\mathbf {a} _{k},&\mathbf {e} _{k}&={\frac {\mathbf {u} _{k}}{\|\mathbf {u} _{k}\|}}\end{aligned}}$

We can now express the $\mathbf {a} _{i}$s over our newly computed orthonormal basis:

${\begin{aligned}\mathbf {a} _{1}&=\left\langle \mathbf {e} _{1},\mathbf {a} _{1}\right\rangle \mathbf {e} _{1}\\\mathbf {a} _{2}&=\left\langle \mathbf {e} _{1},\mathbf {a} _{2}\right\rangle \mathbf {e} _{1}+\left\langle \mathbf {e} _{2},\mathbf {a} _{2}\right\rangle \mathbf {e} _{2}\\\mathbf {a} _{3}&=\left\langle \mathbf {e} _{1},\mathbf {a} _{3}\right\rangle \mathbf {e} _{1}+\left\langle \mathbf {e} _{2},\mathbf {a} _{3}\right\rangle \mathbf {e} _{2}+\left\langle \mathbf {e} _{3},\mathbf {a} _{3}\right\rangle \mathbf {e} _{3}\\&\;\;\vdots \\\mathbf {a} _{k}&=\sum _{j=1}^{k}\left\langle \mathbf {e} _{j},\mathbf {a} _{k}\right\rangle \mathbf {e} _{j}\end{aligned}}$

where $\left\langle \mathbf {e} _{i},\mathbf {a} _{i}\right\rangle =\left\|\mathbf {u} _{i}\right\|$. This can be written in matrix form:

$A=QR$

where:

$Q={\begin{bmatrix}\mathbf {e} _{1}&\cdots &\mathbf {e} _{n}\end{bmatrix}}$

and

$R={\begin{bmatrix}\langle \mathbf {e} _{1},\mathbf {a} _{1}\rangle &\langle \mathbf {e} _{1},\mathbf {a} _{2}\rangle &\langle \mathbf {e} _{1},\mathbf {a} _{3}\rangle &\cdots &\langle \mathbf {e} _{1},\mathbf {a} _{n}\rangle \\0&\langle \mathbf {e} _{2},\mathbf {a} _{2}\rangle &\langle \mathbf {e} _{2},\mathbf {a} _{3}\rangle &\cdots &\langle \mathbf {e} _{2},\mathbf {a} _{n}\rangle \\0&0&\langle \mathbf {e} _{3},\mathbf {a} _{3}\rangle &\cdots &\langle \mathbf {e} _{3},\mathbf {a} _{n}\rangle \\\vdots &\vdots &\vdots &\ddots &\vdots \\0&0&0&\cdots &\langle \mathbf {e} _{n},\mathbf {a} _{n}\rangle \\\end{bmatrix}}.$

#### Example

Consider the decomposition of

$A={\begin{bmatrix}12&-51&4\\6&167&-68\\-4&24&-41\end{bmatrix}}.$

Recall that an orthonormal matrix $Q$ has the property $Q^{\textsf {T}}Q=I$.

Then, we can calculate $Q$ by means of Gram–Schmidt as follows:

${\begin{aligned}U={\begin{bmatrix}\mathbf {u} _{1}&\mathbf {u} _{2}&\mathbf {u} _{3}\end{bmatrix}}&={\begin{bmatrix}12&-69&-58/5\\6&158&6/5\\-4&30&-33\end{bmatrix}};\\Q={\begin{bmatrix}{\frac {\mathbf {u} _{1}}{\|\mathbf {u} _{1}\|}}&{\frac {\mathbf {u} _{2}}{\|\mathbf {u} _{2}\|}}&{\frac {\mathbf {u} _{3}}{\|\mathbf {u} _{3}\|}}\end{bmatrix}}&={\begin{bmatrix}6/7&-69/175&-58/175\\3/7&158/175&6/175\\-2/7&6/35&-33/35\end{bmatrix}}.\end{aligned}}$

Thus, we have

${\begin{aligned}Q^{\textsf {T}}A&=Q^{\textsf {T}}Q\,R=R;\\R&=Q^{\textsf {T}}A={\begin{bmatrix}14&21&-14\\0&175&-70\\0&0&35\end{bmatrix}}.\end{aligned}}$

#### Relation to RQ decomposition

The RQ decomposition transforms a matrix *A* into the product of an upper triangular matrix *R* (also known as right-triangular) and an orthogonal matrix *Q*. The only difference from QR decomposition is the order of these matrices.

QR decomposition is Gram–Schmidt orthogonalization of columns of *A*, started from the first column.

RQ decomposition is Gram–Schmidt orthogonalization of rows of *A*, started from the last row.

#### Advantages and disadvantages

The Gram-Schmidt process is inherently numerically unstable. While the application of the projections has an appealing geometric analogy to orthogonalization, the orthogonalization itself is prone to [numerical error](https://en.wikipedia.org/wiki/Numerical_error). A significant advantage is the ease of implementation.

### Using Householder reflections

![[media/ad6bb61e02a33b10ff589f2bb13a9c6c5f66b8e9.png]]
Householder reflection for QR-decomposition: The goal is to find a linear transformation that changes the vector $\mathbf {x}$ into a vector of the same length which is collinear to $\mathbf {e} _{1}$. We could use an orthogonal projection (Gram-Schmidt) but this will be numerically unstable if the vectors $\mathbf {x}$ and $\mathbf {e} _{1}$ are close to orthogonal. Instead, the Householder reflection reflects through the dotted line (chosen to bisect the angle between $\mathbf {x}$ and $\mathbf {e} _{1}$). The maximum angle with this transform is 45 degrees.

A Householder reflection (or *Householder transformation*) is a transformation that takes a vector and reflects it about some [plane](https://en.wikipedia.org/wiki/Plane_(mathematics) "Plane (mathematics)") or [hyperplane](https://en.wikipedia.org/wiki/Hyperplane). We can use this operation to calculate the *QR* factorization of an *m*-by-*n* matrix $A$ with *m* ≥ *n*.

*Q* can be used to reflect a vector in such a way that all coordinates but one disappear.

Let $\mathbf {x}$ be an arbitrary real *m*-dimensional column vector of $A$ such that $\|\mathbf {x} \|=|\alpha |$ for a scalar *α*. *α* should get the same sign as the $k$-th coordinate of $\mathbf {x}$, where $x_{k}$ is to be the pivot coordinate after which all entries are 0 in matrix *A*'s final upper triangular form. If the algorithm is implemented using [[Floating-Point Arithmetic]], then *α* should get the opposite sign to avoid [loss of significance](https://en.wikipedia.org/wiki/Loss_of_significance) (for example, when $\mathbf {x}$ is almost collinear with $\mathbf {e} _{1}$, $\|\mathbf {u} \|$ becomes "small" and $\mathbf {u} /\|\mathbf {u} \|$ is numerically unstable; the extreme case is $\|\mathbf {u} \|=0$, which causes the previous division to result in [NaN](https://en.wikipedia.org/wiki/NaN)).

In the complex case, set

$\alpha =-e^{i\arg x_{k}}\|\mathbf {x} \|$

and substitute transposition by conjugate transposition in the construction of *Q* below.

Then, where $\mathbf {e} _{1}$ is the vector \[1 0 ⋯ 0\]<sup>T</sup>, \|\| · \|\| is the [Euclidean norm](https://en.wikipedia.org/wiki/Euclidean_space#Euclidean_norm) and $I$ is an *m*×*m* [identity matrix](https://en.wikipedia.org/wiki/Identity_matrix), set

${\begin{aligned}\mathbf {u} &=\mathbf {x} -\alpha \mathbf {e} _{1},\\\mathbf {v} &={\frac {\mathbf {u} }{\|\mathbf {u} \|}},\\Q&=I-2\mathbf {v} \mathbf {v} ^{\textsf {T}}.\end{aligned}}$

Or, if $A$ is complex

$Q=I-2\mathbf {v} \mathbf {v} ^{\dagger }.$

$Q$ is an *m*-by-*m* Householder matrix, which is both symmetric and orthogonal (Hermitian and unitary in the complex case), and

$Q\mathbf {x} ={\begin{bmatrix}\alpha \\0\\\vdots \\0\end{bmatrix}}.$

This can be used to gradually transform an *m*-by-*n* matrix *A* to upper [triangular](https://en.wikipedia.org/wiki/Triangular_matrix) form. First, we multiply *A* with the Householder matrix *Q*<sub>1</sub> we obtain when we choose the first matrix column for **x**. This results in a matrix *Q*<sub>1</sub>*A* with zeros in the left column (except for the first row).

$Q_{1}A={\begin{bmatrix}\alpha _{1}&\star &\cdots &\star \\0&&&\\\vdots &&A'&\\0&&&\end{bmatrix}}$

This can be repeated for *A*′ (obtained from *Q*<sub>1</sub>*A* by deleting the first row and first column), resulting in a Householder matrix *Q*′<sub>2</sub>. Note that *Q*′<sub>2</sub> is smaller than *Q*<sub>1</sub>. Since we want it really to operate on *Q*<sub>1</sub>*A* instead of *A*′ we need to expand it to the upper left, filling in a 1, or in general:

$Q_{k}={\begin{bmatrix}I_{k-1}&0\\0&Q_{k}'\end{bmatrix}}.$

After $t$ iterations of this process, $t=\min(m-1,n)$,

$R=Q_{t}\cdots Q_{2}Q_{1}A$

is an upper triangular matrix. So, with

${\begin{aligned}Q^{\textsf {T}}&=Q_{t}\cdots Q_{2}Q_{1},\\Q&=Q_{1}^{\textsf {T}}Q_{2}^{\textsf {T}}\cdots Q_{t}^{\textsf {T}}\end{aligned}}$

$A=QR$ is a QR decomposition of $A$.

This method has greater [[Numerical Stability]] than the Gram–Schmidt method above.

In numerical tests the computed factors $Q_{c}$ and $R_{c}$ satisfy ${\frac {\|QR-Q_{c}R_{c}\|_{\infty }}{\|A\|_{\infty }}}=O(\varepsilon )$ at machine precision. Also, orthogonality is preserved: $\|Q_{c}^{\mathsf {T}}Q_{c}-I\|_{\infty }=O(\varepsilon )$. However, the accuracy of $Q_{c}$ and $R_{c}$ decrease with condition number: $\|Q-Q_{c}\|_{\infty }=O(\varepsilon \,\kappa _{\infty }(A)),\quad {\frac {\|R-R_{c}\|_{\infty }}{\|R\|_{\infty }}}=O(\varepsilon \,\kappa _{\infty }(A)).$

For a well-conditioned example ($n=4000$, $\kappa _{\infty }(A)\approx 3\times 10^{3}$): ${\frac {\|QR-Q_{c}R_{c}\|_{\infty }}{\|A\|_{\infty }}}\approx 1.6\times 10^{-15},$ $\|Q-Q_{c}\|_{\infty }\approx 1.6\times 10^{-15},$ ${\frac {\|R-R_{c}\|_{\infty }}{\|R\|_{\infty }}}\approx 4.3\times 10^{-14},$ $\|Q_{c}^{\mathsf {T}}Q_{c}-I\|_{\infty }\approx 1.1\times 10^{-13}.$

In an ill-conditioned test ($n=4000$, $\kappa _{\infty }(A)\approx 4\times 10^{18}$): ${\frac {\|QR-Q_{c}R_{c}\|_{\infty }}{\|A\|_{\infty }}}\approx 1.3\times 10^{-15},$ $\|Q-Q_{c}\|_{\infty }\approx 5.2\times 10^{-4},$ ${\frac {\|R-R_{c}\|_{\infty }}{\|R\|_{\infty }}}\approx 1.2\times 10^{-4},$ $\|Q_{c}^{\mathsf {T}}Q_{c}-I\|_{\infty }\approx 1.1\times 10^{-13}.$

The following table gives the number of operations in the *k*-th step of the QR-decomposition by the Householder transformation, assuming a square matrix with size *n*.

|  |  |
|----|----|
| Operation | Number of operations in the *k*-th step |
| Multiplications | $2(n-k+1)^{2}$ |
| Additions | $(n-k+1)^{2}+(n-k+1)(n-k)+2$ |
| Division | $1$ |
| Square root | $1$ |

Summing these numbers over the *n* − 1 steps (for a square matrix of size *n*), the complexity of the algorithm (in terms of floating point multiplications) is given by

${\frac {2}{3}}n^{3}+n^{2}+{\frac {1}{3}}n-2=O\left(n^{3}\right).$

#### Example

Let us calculate the decomposition of

$A={\begin{bmatrix}12&-51&4\\6&167&-68\\-4&24&-41\end{bmatrix}}.$

First, we need to find a reflection that transforms the first column of matrix *A*, vector $\mathbf {a} _{1}={\begin{bmatrix}12&6&-4\end{bmatrix}}^{\textsf {T}}$, into $\left\|\mathbf {a} _{1}\right\|\mathbf {e} _{1}={\begin{bmatrix}\alpha &0&0\end{bmatrix}}^{\textsf {T}}$.

Now,

$\mathbf {u} =\mathbf {x} -\alpha \mathbf {e} _{1},$

and

$\mathbf {v} ={\frac {\mathbf {u} }{\|\mathbf {u} \|}}.$

Here,

$\alpha =14$ and $\mathbf {x} =\mathbf {a} _{1}={\begin{bmatrix}12&6&-4\end{bmatrix}}^{\textsf {T}}$

Therefore

$\mathbf {u} ={\begin{bmatrix}-2&6&-4\end{bmatrix}}^{\textsf {T}}=2{\begin{bmatrix}-1&3&-2\end{bmatrix}}^{\textsf {T}}$ and $\mathbf {v} ={\frac {1}{\sqrt {14}}}{\begin{bmatrix}-1&3&-2\end{bmatrix}}^{\textsf {T}}$, and then

${\begin{aligned}Q_{1}={}&I-{\frac {2}{{\sqrt {14}}{\sqrt {14}}}}{\begin{bmatrix}-1\\3\\-2\end{bmatrix}}{\begin{bmatrix}-1&3&-2\end{bmatrix}}\\={}&I-{\frac {1}{7}}{\begin{bmatrix}1&-3&2\\-3&9&-6\\2&-6&4\end{bmatrix}}\\={}&{\begin{bmatrix}6/7&3/7&-2/7\\3/7&-2/7&6/7\\-2/7&6/7&3/7\\\end{bmatrix}}.\end{aligned}}$

Now observe:

$Q_{1}A={\begin{bmatrix}14&21&-14\\0&-49&-14\\0&168&-77\end{bmatrix}},$

so we already have almost a triangular matrix. We only need to zero the (3, 2) entry.

Take the (1, 1) [minor](https://en.wikipedia.org/wiki/Minor_(linear_algebra) "Minor (linear algebra)"), and then apply the process again to

$A'=M_{11}={\begin{bmatrix}-49&-14\\168&-77\end{bmatrix}}.$

By the same method as above, we obtain the matrix of the Householder transformation

$Q_{2}={\begin{bmatrix}1&0&0\\0&-7/25&24/25\\0&24/25&7/25\end{bmatrix}}$

after performing a direct sum with 1 to make sure the next step in the process works properly.

Now, we find

$Q=Q_{1}^{\textsf {T}}Q_{2}^{\textsf {T}}={\begin{bmatrix}6/7&-69/175&58/175\\3/7&158/175&-6/175\\-2/7&6/35&33/35\end{bmatrix}}.$

Or, to four decimal digits,

${\begin{aligned}Q&=Q_{1}^{\textsf {T}}Q_{2}^{\textsf {T}}={\begin{bmatrix}0.8571&-0.3943&0.3314\\0.4286&0.9029&-0.0343\\-0.2857&0.1714&0.9429\end{bmatrix}}\\R&=Q_{2}Q_{1}A=Q^{\textsf {T}}A={\begin{bmatrix}14&21&-14\\0&175&-70\\0&0&-35\end{bmatrix}}.\end{aligned}}$

The matrix *Q* is orthogonal and *R* is upper triangular, so *A* = *QR* is the required QR decomposition.

#### Advantages and disadvantages

The use of Householder transformations is inherently the most simple of the numerically stable QR decomposition algorithms due to the use of reflections as the mechanism for producing zeroes in the *R* matrix. However, the Householder reflection algorithm is bandwidth heavy and difficult to parallelize, as every reflection that produces a new zero element changes the entirety of both *Q* and *R* matrices.

#### Parallel implementation of Householder QR

The Householder QR method can be implemented in parallel with algorithms such as the TSQR algorithm (which stands for *Tall Skinny QR*). This algorithm can be applied in the case when the matrix *A* has *m \>\> n*. This algorithm uses a binary reduction tree to compute local householder QR decomposition at each node in the forward pass, and re-constitute the Q matrix in the backward pass. The [binary tree](https://en.wikipedia.org/wiki/Binary_tree) structure aims at decreasing the amount of communication between processor to increase performance.

### Using Givens rotations

QR decompositions can also be computed with a series of [Givens rotations](https://en.wikipedia.org/wiki/Givens_rotation). Each rotation zeroes an element in the subdiagonal of the matrix, forming the *R* matrix. The concatenation of all the Givens rotations forms the orthogonal *Q* matrix.

In practice, Givens rotations are not actually performed by building a whole matrix and doing a matrix multiplication. A Givens rotation procedure is used instead which does the equivalent of the sparse Givens matrix multiplication, without the extra work of handling the sparse elements. The Givens rotation procedure is useful in situations where only relatively few off-diagonal elements need to be zeroed, and is more easily parallelized than [Householder transformations](https://en.wikipedia.org/wiki/Householder_transformation).

#### Example

Let us calculate the decomposition of

$A={\begin{bmatrix}12&-51&4\\6&167&-68\\-4&24&-41\end{bmatrix}}.$

First, we need to form a [rotation matrix](https://en.wikipedia.org/wiki/Rotation_matrix) that will zero the lowermost left element, $a_{31}=-4$. We form this matrix using the Givens rotation method, and call the matrix $G_{1}$. We will first rotate the vector ${\begin{bmatrix}12&-4\end{bmatrix}}$, to point along the *X* axis. This vector has an angle $\theta =\arctan \left({\frac {-(-4)}{12}}\right)$. We create the orthogonal Givens rotation matrix, $G_{1}$:

${\begin{aligned}G_{1}&={\begin{bmatrix}\cos(\theta )&0&-\sin(\theta )\\0&1&0\\\sin(\theta )&0&\cos(\theta )\end{bmatrix}}\\&\approx {\begin{bmatrix}0.94868&0&-0.31622\\0&1&0\\0.31622&0&0.94868\end{bmatrix}}\end{aligned}}$

And the result of $G_{1}A$ now has a zero in the $a_{31}$ element.

$G_{1}A\approx {\begin{bmatrix}12.64911&-55.97231&16.76007\\6&167&-68\\0&6.64078&-37.6311\end{bmatrix}}$

We can similarly form Givens matrices $G_{2}$ and $G_{3}$, which will zero the sub-diagonal elements $a_{21}$ and $a_{32}$, forming a triangular matrix $R$. The orthogonal matrix $Q^{\textsf {T}}$ is formed from the product of all the Givens matrices $Q^{\textsf {T}}=G_{3}G_{2}G_{1}$. Thus, we have $G_{3}G_{2}G_{1}A=Q^{\textsf {T}}A=R$, and the *QR* decomposition is $A=QR$.

#### Advantages and disadvantages

The QR decomposition via Givens rotations is the most involved to implement, as the ordering of the rows required to fully exploit the algorithm is not trivial to determine. However, it has a significant advantage in that each new zero element $a_{ij}$ affects only the row with the element to be zeroed (*i*) and a row above (*j*). This makes the Givens rotation algorithm more bandwidth efficient and parallelizable than the Householder reflection technique.

### Using fast matrix multiplication

It is possible to compute the QR decomposition in a fast way with the use of [fast matrix multiplication algorithms](https://en.wikipedia.org/wiki/Computational_complexity_of_matrix_multiplication) in the time $O({n^{\omega }})$ for $~2.37\leq \omega <3$.

## Connection to a determinant or a product of eigenvalues

We can use QR decomposition to find the [[Determinant]] of a square matrix. Suppose a matrix is decomposed as $A=QR$. Then we have 

$$
\det A=\det Q\det R.
$$

$Q$ can be chosen such that $\det Q=1$. Thus, 

$$
\det A=\det R=\prod _{i}r_{ii}
$$

where the $r_{ii}$ are the entries on the diagonal of $R$. Furthermore, because the determinant equals the product of the eigenvalues, we have 

$$
\prod _{i}r_{ii}=\prod _{i}\lambda _{i}
$$

where the $\lambda _{i}$ are eigenvalues of $A$.

We can extend the above properties to a non-square complex matrix $A$ by introducing the definition of QR decomposition for non-square complex matrices and replacing eigenvalues with singular values.

Start with a QR decomposition for a non-square matrix *A*:

$A=Q{\begin{bmatrix}R\\0\end{bmatrix}},\qquad Q^{\dagger }Q=I$

where $0$ denotes the zero matrix and $Q$ is a unitary matrix.

From the properties of the [[Singular Value Decomposition]] (SVD) and the determinant of a matrix, we have

${\Big |}\prod _{i}r_{ii}{\Big |}=\prod _{i}\sigma _{i},$

where the $\sigma _{i}$ are the singular values of $A$.

Note that the singular values of $A$ and $R$ are identical, although their complex eigenvalues may be different. However, if *A* is square, then

${\prod _{i}\sigma _{i}}={\Big |}\prod _{i}\lambda _{i}{\Big |}.$

It follows that the QR decomposition can be used to efficiently calculate the product of the eigenvalues or singular values of a matrix.

## Column pivoting

Pivoted QR differs from ordinary Gram-Schmidt in that it takes the largest remaining column at the beginning of each new step—column pivoting— and thus introduces a [permutation matrix](https://en.wikipedia.org/wiki/Permutation_matrix) *P*:

$AP=QR\quad \iff \quad A=QRP^{\textsf {T}}$

Column pivoting is useful when *A* is (nearly) [rank deficient](https://en.wikipedia.org/wiki/Rank_deficient), or is suspected of being so. It can also improve numerical accuracy. *P* is usually chosen so that the diagonal elements of *R* are non-increasing: $\left|r_{11}\right|\geq \left|r_{22}\right|\geq \cdots \geq \left|r_{nn}\right|$. This can be used to find the (numerical) rank of *A* at lower computational cost than a [[Singular Value Decomposition]], forming the basis of so-called [rank-revealing QR algorithms](https://en.wikipedia.org/wiki/Rank-revealing_QR_algorithm).

## Using for solution to linear inverse problems

Compared to the direct matrix inverse, inverse solutions using QR decomposition are more numerically stable as evidenced by their reduced [[Condition Number|condition numbers]].

To solve the underdetermined ($m<n$) linear problem $A\mathbf {x} =\mathbf {b}$ where the matrix $A$ has dimensions $m\times n$ and rank $m$, first find the QR factorization of the transpose of $A$: $A^{\textsf {T}}=QR$, where *Q* is an orthogonal matrix (i.e. $Q^{\textsf {T}}=Q^{-1}$), and *R* has a special form: $R=\left[{\begin{smallmatrix}R_{1}\\0\end{smallmatrix}}\right]$. Here $R_{1}$ is a square $m\times m$ right triangular matrix, and the zero matrix has dimension $(n-m)\times m$. After some algebra, it can be shown that a solution to the [inverse problem](https://en.wikipedia.org/wiki/Inverse_problem) can be expressed as: $\mathbf {x} =Q\left[{\begin{smallmatrix}\left(R_{1}^{\textsf {T}}\right)^{-1}\mathbf {b} \\0\end{smallmatrix}}\right]$ where one may either find $R_{1}^{-1}$ by [Gaussian elimination](https://en.wikipedia.org/wiki/Gaussian_elimination) or compute $\left(R_{1}^{\textsf {T}}\right)^{-1}\mathbf {b}$ directly by [forward substitution](https://en.wikipedia.org/wiki/Triangular_matrix#Forward_and_back_substitution). The latter technique enjoys greater numerical accuracy and lower computations.

To find a solution ${\hat {\mathbf {x} }}$ to the overdetermined ($m\geq n$) problem $A\mathbf {x} =\mathbf {b}$ which minimizes the norm $\left\|A{\hat {\mathbf {x} }}-\mathbf {b} \right\|$, first find the QR factorization of $A$: $A=QR$. The solution can then be expressed as ${\hat {\mathbf {x} }}=R_{1}^{-1}\left(Q_{1}^{\textsf {T}}\mathbf {b} \right)$, where $Q_{1}$ is an $m\times n$ matrix containing the first $n$ columns of the full orthonormal basis $Q$ and where $R_{1}$ is as before. Equivalent to the underdetermined case, [back substitution](https://en.wikipedia.org/wiki/Triangular_matrix#Forward_and_back_substitution) can be used to quickly and accurately find this ${\hat {\mathbf {x} }}$ without explicitly inverting $R_{1}$. ($Q_{1}$ and $R_{1}$ are often provided by numerical libraries as an "economic" QR decomposition.)

## Generalizations

[Iwasawa decomposition](https://en.wikipedia.org/wiki/Iwasawa_decomposition) generalizes QR decomposition to semi-simple Lie groups.

## See also

- [Polar decomposition](https://en.wikipedia.org/wiki/Polar_decomposition)
- [[Eigendecomposition]] (spectral decomposition)
- [[LU Decomposition]]
- [[Singular Value Decomposition]]

## References

1.  ^    [Trefethen, Lloyd N.](https://en.wikipedia.org/wiki/Nick_Trefethen); Bau, David III (1997). *Numerical linear algebra*. Philadelphia, PA: [Society for Industrial and Applied Mathematics](https://en.wikipedia.org/wiki/Society_for_Industrial_and_Applied_Mathematics). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-898713-61-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-898713-61-9).
2.  [Stoer, Josef](https://en.wikipedia.org/wiki/Josef_Stoer); [Bulirsch, Roland](https://en.wikipedia.org/wiki/Roland_Bulirsch) (2002), *Introduction to Numerical Analysis* (3rd ed.), Springer, p. 225, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-95452-X](https://en.wikipedia.org/wiki/Special:BookSources/0-387-95452-X)
3.  [Holmes, Mark H.](https://en.wikipedia.org/wiki/Mark_H._Holmes) (2023). *Introduction to Scientific Computing and Data Analysis, 2nd Ed*. Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-031-22429-4](https://en.wikipedia.org/wiki/Special:BookSources/978-3-031-22429-4). 
4.  [Demmel, James](https://en.wikipedia.org/wiki/James_Demmel); [Grigori, Laura](https://en.wikipedia.org/wiki/Laura_Grigori) (12 Jun 2008). "Communication-optimal parallel and sequential QR and LU factorizations: theory and practice". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[0806.2159](https://arxiv.org/abs/0806.2159) \[[cs.NA](https://arxiv.org/archive/cs.NA)\].
5.  Schönhage, A. (1972). "Unitäre Transformationen großer Matrizen". *Numerische Mathematik*. **20**: 409–41. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/BF01402563](https://doi.org/10.1007%2FBF01402563).
6.  Knight, P. (1995). "Fast rectangular matrix multiplication and QR decomposition". *Linear Algebra and its Applications*. **221**: 69–81. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/0024-3795(93)00230-W](https://doi.org/10.1016%2F0024-3795%2893%2900230-W).
7.  [Strang, Gilbert](https://en.wikipedia.org/wiki/Gilbert_Strang) (2019). *Linear Algebra and Learning from Data* (1st ed.). Wellesley: Wellesley Cambridge Press. p. 143. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-692-19638-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-692-19638-0).
8.  [Parker, Robert L.](https://en.wikipedia.org/wiki/Robert_Ladislav_Parker) (1994). *Geophysical Inverse Theory*. Princeton, N.J.: Princeton University Press. Section 1.13. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-691-20683-7](https://en.wikipedia.org/wiki/Special:BookSources/978-0-691-20683-7). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [1134769155](https://search.worldcat.org/oclc/1134769155).

## Further reading

- [Golub, Gene H.](https://en.wikipedia.org/wiki/Gene_H._Golub); [Van Loan, Charles F.](https://en.wikipedia.org/wiki/Charles_F._Van_Loan) (1996), *Matrix Computations* (3rd ed.), Johns Hopkins, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8018-5414-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8018-5414-9).
- [Horn, Roger A.](https://en.wikipedia.org/wiki/Roger_Horn); Johnson, Charles R. (1985), *Matrix Analysis*, Cambridge University Press, sec. 2.8, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-38632-2](https://en.wikipedia.org/wiki/Special:BookSources/0-521-38632-2)
- [Press, William H.](https://en.wikipedia.org/wiki/William_H._Press); [Teukolsky, Saul A.](https://en.wikipedia.org/wiki/Saul_Teukolsky); Vetterling, William T.; [Flannery, Brian P.](https://en.wikipedia.org/wiki/Brian_P._Flannery) (2007), ["Section 2.10. QR Decomposition"](http://apps.nrbook.com/empanel/index.html?pg=102), *[Numerical Recipes](https://en.wikipedia.org/wiki/Numerical_Recipes): The Art of Scientific Computing* (3rd ed.), New York: Cambridge University Press, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-88068-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-88068-8)

## External links

- [Online Matrix Calculator](https://web.archive.org/web/20081212221215/http://www.bluebit.gr/matrix-calculator/) Performs QR decomposition of matrices.
- [LAPACK users manual](https://netlib.org/lapack/lug/node39.html) gives details of subroutines to calculate the QR decomposition
- [Mathematica users manual](https://web.archive.org/web/20061122183956/http://documents.wolfram.com/mathematica/functions/QRDecomposition) gives details and examples of routines to calculate QR decomposition
- [ALGLIB](https://www.alglib.net/) includes a partial port of the LAPACK to C++, C#, Delphi, etc.
- [Eigen::QR](http://eigen.tuxfamily.org/dox-devel/group__QR__Module.html) Includes C++ implementation of QR decomposition.
