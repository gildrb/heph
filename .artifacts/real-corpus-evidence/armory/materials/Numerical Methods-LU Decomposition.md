[[numerical-methods.base]]

> Source: [[LU Decomposition]]
> License: Wikipedia content is available under CC BY-SA 4.0.

In [numerical analysis](https://en.wikipedia.org/wiki/Numerical_analysis) and [linear algebra](https://en.wikipedia.org/wiki/Linear_algebra), **lower–upper** (**LU**) **decomposition** or **factorization** factors a [matrix](https://en.wikipedia.org/wiki/Matrix_(mathematics) "Matrix (mathematics)") as the product of a lower [triangular matrix](https://en.wikipedia.org/wiki/Triangular_matrix) and an upper triangular matrix (see [[Matrix Multiplication]] and [matrix decomposition](https://en.wikipedia.org/wiki/Matrix_decomposition)). The product sometimes includes a [permutation matrix](https://en.wikipedia.org/wiki/Permutation_matrix) as well. LU decomposition can be viewed as the matrix form of [Gaussian elimination](https://en.wikipedia.org/wiki/Gaussian_elimination). Computers usually solve square [systems of linear equations](https://en.wikipedia.org/wiki/System_of_linear_equations) using LU decomposition, and it is also a key step when inverting a matrix or computing the [[Determinant]] of a matrix. It is also sometimes referred to as **LR** decomposition (factors into left and right triangular matrices). The LU decomposition was introduced by the Polish astronomer [Tadeusz Banachiewicz](https://en.wikipedia.org/wiki/Tadeusz_Banachiewicz) in 1938, who first wrote product equation $LU=A=h^{T}g$ (The last form in his alternate yet equivalent matrix notation appears as $g\times h$). While most elimination and LU algorithms employ equations of the form $element:=element-vector\times vector$ Banachiewicz wrote it as $vector:=vector-submatrix\times vector$, in this way revealing additional problem symmetry.

## Definitions

![[media/a5830b7fc5f6462bc9681d4d3db83bb0cd01df3b.png]]
LDU decomposition of a [Walsh matrix](https://en.wikipedia.org/wiki/Walsh_matrix)

Let A be a square matrix. An **LU factorization** refers to expression of A into product of two factors – a lower triangular matrix L and an upper triangular matrix U: *A* = *LU*. Sometimes factorization is impossible without prior reordering of A to prevent division by zero or uncontrolled growth of rounding errors hence alternative expression becomes *PAQ* = *LU*, where in formal notation [permutation matrices](https://en.wikipedia.org/wiki/Permutation_matrices) factors P and Q indicate permutation of rows (or columns) of A. In theory P (or Q) are obtained by permutations of rows (or columns) of the [identity matrix](https://en.wikipedia.org/wiki/Identity_matrix), in practice the corresponding permutations are applied directly to rows (or columns) of A.

Matrix A of side n has $n^{2}$ coefficients while two triangle matrices combined contain *n*(*n* + 1) coefficients, therefore n coefficients of matrices LU are not independent. Usual convention is to set L unitriangular, i.e. with all n main diagonal elements equal one. However, setting instead U matrix unitriangular reduces to the same procedure after [transpose](https://en.wikipedia.org/wiki/Transpose) of matrix product (cf. properties of matrix transposition): 

$$
B=A^{\textsf {T}}=(LU)^{\textsf {T}}=U^{\textsf {T}}L^{\textsf {T}}.
$$

 After transposition, *U*<sup>T</sup> is lower triangle while *L*<sup>T</sup> is upper unitriangular factor of B. This demonstrates also, that operations on rows (e.g. pivoting) are equivalent to those on columns of a transposed matrix, and in general choice of row or column algorithm offers no advantage.

In the lower triangular matrix all elements above the main diagonal are zero, in the upper triangular matrix, all the elements below the diagonal are zero. For example, for a 3 × 3 matrix A, its LU decomposition looks like this: 

$$
{\begin{bmatrix}a_{11}&a_{12}&a_{13}\\a_{21}&a_{22}&a_{23}\\a_{31}&a_{32}&a_{33}\end{bmatrix}}={\begin{bmatrix}\ell _{11}&0&0\\\ell _{21}&\ell _{22}&0\\\ell _{31}&\ell _{32}&\ell _{33}\end{bmatrix}}{\begin{bmatrix}u_{11}&u_{12}&u_{13}\\0&u_{22}&u_{23}\\0&0&u_{33}\end{bmatrix}}.
$$

Without a proper ordering or permutations in the matrix, the factorization may fail to materialize. For example, it is easy to verify (by expanding the [[Matrix Multiplication]]) that $a_{11}=\ell _{11}u_{11}$. If $a_{11}=0$, then at least one of $\ell _{11}$ and $u_{11}$ has to be zero, which implies that either L or U is [singular](https://en.wikipedia.org/wiki/Singular_matrix). This is impossible if A is nonsingular (invertible). In terms of operations, zeroing/elimination of remaining elements of first column of A involves division of $a_{21},a_{31}$ with $a_{11}$, impossible if it is 0. This is a procedural problem. It can be removed by simply reordering the rows of A so that the first element of the permuted matrix is nonzero. The same problem in subsequent factorization steps can be removed the same way. For numerical stability against rounding errors/division by small numbers it is important to select $a_{11}$ of large [absolute value](https://en.wikipedia.org/wiki/Absolute_value) (cf. pivoting).

### LU Through recursion

The above example of 3 × 3 matrices demonstrates that matrix product of top row and leftmost columns of involved matrices plays special role for LU to succeed. Let us mark consecutive versions of matrices with $(0),\;(1),\dots$ and then let us write matrix product $A\equiv A^{(0)}=L^{(0)}U^{(0)}$ in such way that these rows and columns are separated from the rest. In doing so we shall use [block matrix](https://en.wikipedia.org/wiki/Block_matrix) notation, such that e.g. $a\equiv a_{11}$ is an ordinary number, ${\bf {w}}^{\textsf {T}}\equiv (a_{12},a_{13})^{\textsf {T}}$ is a [row vector](https://en.wikipedia.org/wiki/Row_and_column_vectors) and ${\bf {v}}=(a_{21},a_{31})$ is a column vector and $A'$ is sub-matrix of matrix $A^{(0)}$ without top row and leftmost column. Then we can replace $A^{(0)}=L^{(0)}U^{(0)}$ with a block [matrix product](https://en.wikipedia.org/wiki/Matrix_product). Namely it turns out that one can multiply matrix blocks in such way as if they were ordinary numbers, i.e. row times column, except that now their components are sub-matrices, sometimes reduced to scalars or vectors. Thus $u{\bf {l}}$ denotes a vector obtained from ${\bf {l}}$ after multiplication of each component by a number $u$, ${\bf {lu}}^{\textsf {T}}$ is an [outer product](https://en.wikipedia.org/wiki/Outer_product) of vectors ${\bf {l,u}}$, i.e. a matrix which first column is $u_{12}{\bf {l}}$, next is $u_{13}{\bf {l}}$ and so on for all components of ${\bf {u}}$ and $L^{(1)}U^{(1)}$ is a product of sub-matrices of $L^{(0)},\;U^{(0)}$ 

$$
{\begin{aligned}\left({\begin{array}{c|c}a&{\bf {w}}^{\textsf {T}}\\\hline \\[-0.5em]{\bf {v}}&\quad A'\quad \\[-0.5em]\\\end{array}}\right)&=\left({\begin{array}{c|c}{\rm {1}}&{\bf {0}}^{\textsf {T}}\\\hline \\[-0.5em]{\bf {l}}&\quad L^{(1)}\quad \\[-0.5em]\\\end{array}}\right)\;\left({\begin{array}{c|c}u&{\bf {u}}^{\textsf {T}}\\\hline \\[-0.5em]{\bf {0}}&\quad U^{(1)}\\[-0.5em]\\\end{array}}\right)\\&=\left({\begin{array}{c|c}u&{\bf {u}}^{\textsf {T}}\\\hline \\[-0.5em]u{\bf {l}}&\quad {\bf {lu}}^{\textsf {T}}+L^{(1)}U^{(1)}\\[-0.5em]\\\end{array}}\right)\end{aligned}}
$$

From equality of first and last matrices follow final $u=a$, ${\bf {u=w}}$, ${\bf {l}}={(1/a)}{\bf {v}}$ while matrix $A'$ becomes updated/replaced with $A^{(1)}\equiv L^{(1)}U^{(1)}=$ $A'-{\bf {lu}}^{\textsf {T}}$. Now comes the crucial observation: nothing prevents us to treat $A^{(1)}$ the same way as we did with $A^{(0)}$, repeatedly. If dimension of $A$ is n × n, after *n*− 1 such steps all columns ${\bf {v}}$ form sub-diagonal part of triangle matrix $L$ and all pivots $a$ combined with rows ${\bf {w}}^{\textsf {T}}$ form upper triangle matrix $U$, as required. In the above example *n* = 3 so only two steps suffice.

The above procedure demonstrates that at no step the top diagonal pivot element $a$ of consecutive sub-matrices can be zero. To avoid it columns or rows may be swapped so that $a$ becomes nonzero. Such procedure involving permutation is called *LUP*, decomposition with pivoting.

Permutation of columns corresponds to matrix product $AQ^{(0)}$ where $Q^{(0)}$ is a permutation matrix, i.e. the identity matrix $I$ after the same column permutation. After all steps such LUP decomposition applies to $AQ^{(0)}\cdots Q^{(n-1)}\equiv AQ=LU$. Present computation scheme and similar in Cormen et al. are examples of *recurrence algorithms*. They demonstrate two general properties of LU factorization:

1.  the need for pivoting at each step; and
2.  final values of L and U matrices are obtained gradually, one row or column per step.

Recurrence algorithms are not overly costly in terms of algebraic operations yet they suffer from practical disadvantage due to need to update and store most elements of A at each step. It will be seen that by reordering calculations it is possible to dispose with storage of intermediate values.

### LU factorization with partial pivoting

It turns out that a proper permutation of rows (or columns) to select column (or row) absolute maximal pivot *a*<sub>11</sub> is sufficient for numerically stable LU factorization, except for known pathological cases. It is called **LU factorization with partial pivoting** (LUP): 

$$
PA=LU,\quad (AQ=LU),
$$

 where L and U are again lower and upper triangular matrices, and P and Q are corresponding [permutation matrices](https://en.wikipedia.org/wiki/Permutation_matrices), which, when correspondingly left- and right-multiplied to A, reorder the rows and columns of A. It turns out that all square matrices can be factorized in this form, and the factorization is numerically stable in practice. This makes LUP decomposition a useful technique in practice.

A variant called **rook pivoting** at each step involves search of maximum element the way rook moves on a chessboard, along column, row, column again and so on till reaching a pivot maximal in both its row and column. It can be proven that for large matrices of random elements its cost of operations at each step is similarly to partial pivoting proportional to the length of matrix side unlike its square for full pivoting.

### LU factorization with full pivoting

An **LU factorization with full pivoting** involves both row and column permutations to find absolute maximum element in the whole submatrix: 

$$
PAQ=LU,
$$

 where L, U, and P are defined as before, and Q is a permutation matrix that reorders the columns of A.

### Lower-diagonal-upper (LDU) decomposition

A **lower-diagonal-upper decomposition** (LDU) is a decomposition of the form 

$$
A=LDU,
$$

 where D is a [diagonal matrix](https://en.wikipedia.org/wiki/Diagonal_matrix), and L and U are [unitriangular matrices](https://en.wikipedia.org/wiki/Triangular_matrix#Unitriangular_matrix), meaning that all the entries on the diagonals of L and U are one.

### Rectangular matrices

Above we required that A be a square matrix, but these decompositions can all be generalized to rectangular matrices as well. In that case, L and D are square matrices both of which have the same number of rows as A, and U has exactly the same dimensions as A. 'Upper triangular' should be interpreted as having only zero entries below the main diagonal, which starts at the upper left corner. Similarly, the more precise term for U is that it is the [row echelon form](https://en.wikipedia.org/wiki/Row_echelon_form) of the matrix A.

## Example

We factor the following 2 × 2 matrix: 

$$
{\begin{bmatrix}4&3\\6&3\end{bmatrix}}={\begin{bmatrix}\ell _{11}&0\\\ell _{21}&\ell _{22}\end{bmatrix}}{\begin{bmatrix}u_{11}&u_{12}\\0&u_{22}\end{bmatrix}}.
$$

One way to find the LU decomposition of this simple matrix would be to simply solve the linear equations by inspection. Expanding the [[Matrix Multiplication]] gives 

$$
\left\{{\begin{alignedat}{4}\ell _{11}\cdot u_{11}&&\;+\;&&0\cdot 0&&\;=\;&&4\\\ell _{11}\cdot u_{12}&&\;+\;&&0\cdot u_{22}&&\;=\;&&3\\\ell _{21}\cdot u_{11}&&\;+\;&&\ell _{22}\cdot 0&&\;=\;&&6\\\ell _{21}\cdot u_{12}&&\;+\;&&\ell _{22}\cdot u_{22}&&\;=\;&&3\end{alignedat}}\right.
$$

This system of equations is [underdetermined](https://en.wikipedia.org/wiki/Underdetermined_system). In this case any two nonzero elements of L and U matrices are parameters of the solution and can be set arbitrarily to any nonzero value. Therefore, to find the unique LU decomposition, it is necessary to put some restriction on L and U matrices. For example, we can conveniently require the lower triangular matrix L to be a unit triangular matrix, so that all the entries of its main diagonal are set to one. Then the system of equations has the following solution: 

$$
{\begin{aligned}\ell _{11}&=\ell _{22}=1\\\ell _{21}&=1.5\\u_{11}&=4\\u_{12}&=3\\u_{22}&=-1.5\end{aligned}}
$$

Substituting these values into the LU decomposition above yields 

$$
{\begin{bmatrix}4&3\\6&3\end{bmatrix}}={\begin{bmatrix}1&0\\1.5&1\end{bmatrix}}{\begin{bmatrix}4&3\\0&-1.5\end{bmatrix}}.
$$

## Existence and uniqueness

### Square matrices

Any square matrix A admits LUP and PLU factorizations. If A is [invertible](https://en.wikipedia.org/wiki/Invertible_matrix), then it admits an LU (or LDU) factorization [if and only if](https://en.wikipedia.org/wiki/If_and_only_if) all its leading principal [minors](https://en.wikipedia.org/wiki/Minor_(linear_algebra) "Minor (linear algebra)") are nonzero (for example $\left[{\begin{smallmatrix}0&1\\1&0\end{smallmatrix}}\right]$ does not admit an LU or LDU factorization). If A is a [singular matrix](https://en.wikipedia.org/wiki/Singular_matrix) of rank k, then it admits an LU factorization if the first k leading principal minors are nonzero, although the converse is not true.

If a square, invertible matrix has an LDU factorization (with all diagonal entries of L and U equal to 1), then the factorization is unique. In that case, the LU factorization is also unique if we require that the diagonal of either L or U consists of ones.

In general, any square matrix *A*<sub>*n*×*n*</sub> could have one of the following:

1.  a unique LU factorization (as mentioned above);
2.  infinitely many LU factorizations if any of the first (*n* − 1) columns are linearly dependent;
3.  no LU factorization if the first (*n* − 1) columns are linearly independent and at least one leading principal minor is zero.

In Case 3, one can approximate an LU factorization by changing a diagonal entry a<sub>ij</sub> to *a<sub>ij</sub>* ± *ε* to avoid a zero leading principal minor.

### Symmetric positive-definite matrices

If A is a symmetric (or [Hermitian](https://en.wikipedia.org/wiki/Hermitian_matrix), if A is complex) [[Positive-Definite Matrix]], we can arrange matters so that U is the [conjugate transpose](https://en.wikipedia.org/wiki/Conjugate_transpose) of L. That is, we can write A as 

$$
A=LL^{*}\,.
$$

This decomposition is called the [[Cholesky Decomposition]]. If A is positive definite, then the Cholesky decomposition exists and is unique. Furthermore, computing the Cholesky decomposition is more efficient and [[Numerical Stability|numerically more stable]] than computing some other LU decompositions.

### General matrices

For a (not necessarily invertible) matrix over any field, the exact necessary and sufficient conditions under which it has an LU factorization are known. The conditions are expressed in terms of the ranks of certain submatrices. The Gaussian elimination algorithm for obtaining LU decomposition has also been extended to this most general case.

## Algorithms

### Closed formula

When an LDU factorization exists and is unique, there is a closed (explicit) formula for the elements of L, D, and U in terms of ratios of determinants of certain submatrices of the original matrix A. In particular, *D*<sub>1</sub> = *A*<sub>1,1</sub>, and for *i* = 2, ... , *n*, D<sub>i</sub> is the ratio of the i-th principal submatrix to the (*i* − 1)-th principal submatrix. Computation of the determinants is [computationally expensive](https://en.wikipedia.org/wiki/Computational_complexity), so this explicit formula is not used in practice.

### Using Gaussian elimination

The following algorithm is essentially a modified form of [Gaussian elimination](https://en.wikipedia.org/wiki/Gaussian_elimination). Computing an LU decomposition using this algorithm requires 2/3*n*<sup>3</sup> floating-point operations, ignoring lower-order terms. Partial [pivoting](https://en.wikipedia.org/wiki/Pivot_element) adds only a quadratic term; this is not the case for full pivoting.

#### Generalized explanation

##### Notation

Given an N × N matrix $A=(a_{i,j})_{1\leq i,j\leq N}$, define $A^{(0)}$ as the original, unmodified version of the matrix A. The parenthetical superscript (e.g., (0)) of the matrix A is the version of the matrix. The matrix *A*<sup>(*n*)</sup> is the A matrix in which the elements below the [main diagonal](https://en.wikipedia.org/wiki/Main_diagonal) have already been eliminated to 0 through Gaussian elimination for the first n columns.

Below is a matrix to observe to help us remember the notation (where each ∗ represents any [real number](https://en.wikipedia.org/wiki/Real_number) in the matrix):

$A^{(n-1)}={\begin{pmatrix}*&&&\cdots &&&*\\0&\ddots &&&&\\&\ddots &*&&&\\\vdots &&0&a_{n,n}^{(n-1)}&&&\vdots \\&&\vdots &a_{i,n}^{(n-1)}&*\\&&&\vdots &\vdots &\ddots \\0&\cdots &0&a_{i,n}^{(n-1)}&*&\cdots &*\end{pmatrix}}$

##### Procedure

During this process, we gradually modify the matrix A using row operations until it becomes the matrix U in which all the elements below the main diagonal are equal to zero. During this, we will simultaneously create two separate matrices P and L, such that *PA* = *LU*.

We define the final [permutation matrix](https://en.wikipedia.org/wiki/Permutation_matrix) P as the identity matrix which has all the same rows swapped in the same order as the A matrix while it transforms into the matrix U. For our matrix *A*<sup>(*n*−1)</sup>, we may start by swapping rows to provide the desired conditions for the n-th column. For example, we might swap rows to perform partial pivoting, or we might do it to set the pivot element a<sub>n,n</sub> on the main diagonal to a nonzero number so that we can complete the Gaussian elimination.

For our matrix *A*<sup>(*n*−1)</sup>, we want to set every element below $a_{n,n}^{(n-1)}$ to zero (where $a_{n,n}^{(n-1)}$ is the element in the n-th column of the main diagonal). We will denote each element below $a_{n,n}^{(n-1)}$ as $a_{i,n}^{(n-1)}$ (where *i* = *n*+1, ... , *N*). To set $a_{i,n}^{(n-1)}$ to zero, we set *row<sub>i</sub>* = *row<sub>i</sub>* − (*ℓ<sub>i,n</sub>*)⋅*row<sub>n</sub>* for each row i. For this operation, $\ell _{i,n}:={a_{i,n}^{(n-1)}}/{a_{n,n}^{(n-1)}}$. Once we have performed the row operations for the first *N* − 1 columns, we have obtained an [upper triangular](https://en.wikipedia.org/wiki/Upper-triangular) matrix *A*<sup>(*N*−1)</sup> which is denoted by U.

We can also create the [lower triangular](https://en.wikipedia.org/wiki/Lower_triangular) matrix denoted as L, by directly inputting the previously calculated values of ℓ<sub>i,n</sub> via the formula below.

$$
L={\begin{pmatrix}1&0&\cdots &0\\\ell _{2,1}&\ddots &\ddots &\vdots \\\vdots &\ddots &\ddots &0\\\ell _{N,1}&\cdots &\ell _{N,N-1}&1\end{pmatrix}}
$$

#### Example

If we are given the matrix 

$$
A={\begin{pmatrix}0&5&{\frac {22}{3}}\\4&2&1\\2&7&9\\\end{pmatrix}},
$$

 we will choose to implement partial pivoting and thus swap the first and second row so that our matrix A and the first iteration of our P matrix respectively become 

$$
A^{(0)}={\begin{pmatrix}4&2&1\\0&5&{\frac {22}{3}}\\2&7&9\\\end{pmatrix}},\quad P^{(0)}={\begin{pmatrix}0&1&0\\1&0&0\\0&0&1\\\end{pmatrix}}.
$$

 Once we have swapped the rows, we can eliminate the elements below the main diagonal on the first column by performing 

$$
{\begin{alignedat}{0}row_{2}=row_{2}-(\ell _{2,1})\cdot row_{1}\\row_{3}=row_{3}-(\ell _{3,1})\cdot row_{1}\end{alignedat}}
$$

 such that, 

$$
{\begin{alignedat}{0}\ell _{2,1}={\frac {0}{4}}=0\\\ell _{3,1}={\frac {2}{4}}=0.5\end{alignedat}}
$$

 Once these rows have been subtracted, we have derived from *A*<sup>(1)</sup> the matrix 

$$
A^{(1)}={\begin{pmatrix}4&2&1\\0&5&{\frac {22}{3}}\\0&6&8.5\\\end{pmatrix}}.
$$

Because we are implementing partial pivoting, we swap the second and third rows of our derived matrix and the current version of our P matrix respectively to obtain 

$$
A^{(1)}={\begin{pmatrix}4&2&1\\0&6&8.5\\0&5&{\frac {22}{3}}\\\end{pmatrix}},\quad P^{(1)}={\begin{pmatrix}0&1&0\\0&0&1\\1&0&0\\\end{pmatrix}}.
$$

 Now, we eliminate the elements below the main diagonal on the second column by performing *row*<sub>3</sub> = *row*<sub>3</sub> − (*ℓ*<sub>3,2</sub>)⋅*row*<sub>2</sub> such that *ℓ*<sub>3,2</sub> = 5/6. Because no nonzero elements exist below the main diagonal in our current iteration of A after this row subtraction, this row subtraction derives our final A matrix (denoted as U) and final P matrix: 

$$
A^{(2)}=A^{(N-1)}=U={\begin{pmatrix}4&2&1\\0&6&8.5\\0&0&0.25\\\end{pmatrix}},\quad P={\begin{pmatrix}0&1&0\\0&0&1\\1&0&0\\\end{pmatrix}}.
$$

 After also switching the corresponding rows, we obtain our final L matrix: 

$$
L={\begin{pmatrix}1&0&0\\\ell _{3,1}&1&0\\\ell _{2,1}&\ell _{3,2}&1\\\end{pmatrix}}={\begin{pmatrix}1&0&0\\0.5&1&0\\0&{\frac {5}{6}}&1\\\end{pmatrix}}
$$

Now these matrices have a relation such that *PA* = *LU*.

#### Relations when no rows are swapped

If we did not swap rows at all during this process, we can perform the row operations simultaneously for each column n by setting $A^{(n)}:=L_{n}^{-1}A^{(n-1)},$ where $L_{n}^{-1}$ is the N × N identity matrix with its n-th column replaced by the [transposed](https://en.wikipedia.org/wiki/Transpose) vector (0  ⋯  0  1  −*ℓ*<sub>*n*+1,*n*</sub>  ⋯  −*ℓ*<sub>*N*,*n*</sub>)<sup>T</sup>.

In other words, the lower triangular matrix 

$$
L_{n}^{-1}={\begin{pmatrix}1&&&&&\\&\ddots &&&&\\&&1&&&\\&&-\ell _{n+1,n}&&&\\&&\vdots &&\ddots &\\&&-\ell _{N,n}&&&1\end{pmatrix}}.
$$

Performing all the row operations for the first *N* − 1 columns using the $A^{(n)}:=L_{n}^{-1}A^{(n-1)}$ formula is equivalent to finding the decomposition 

$$
A=L_{1}L_{1}^{-1}A^{(0)}=L_{1}A^{(1)}=L_{1}L_{2}L_{2}^{-1}A^{(1)}=L_{1}L_{2}A^{(2)}=\dotsm =L_{1}\dotsm L_{N-1}A^{(N-1)}.
$$

 Denote *L* = *L*<sub>1</sub> ⋯ *L*<sub>*N*−1</sub> so that *A* = *LA*<sup>(*N*−1)</sup> = *LU*.

Now let's compute the sequence of *L*<sub>1</sub> ⋯ *L*<sub>*N*−1</sub>. We know that L<sub>i</sub> has the following formula: 

$$
L_{n}={\begin{pmatrix}1&&&&&\\&\ddots &&&&\\&&1&&&\\&&\ell _{n+1,n}&&&\\&&\vdots &&\ddots &\\&&\ell _{N,n}&&&1\end{pmatrix}}
$$

If there are two lower triangular matrices with 1s in the main diagonal, and neither have a nonzero item below the main diagonal in the same column as the other, then we can include all nonzero items at their same location in the product of the two matrices. For example:

$\left({\begin{array}{ccccc}1&0&0&0&0\\77&1&0&0&0\\12&0&1&0&0\\63&0&0&1&0\\7&0&0&0&1\end{array}}\right)\left({\begin{array}{ccccc}1&0&0&0&0\\0&1&0&0&0\\0&22&1&0&0\\0&33&0&1&0\\0&44&0&0&1\end{array}}\right)=\left({\begin{array}{ccccc}1&0&0&0&0\\77&1&0&0&0\\12&22&1&0&0\\63&33&0&1&0\\7&44&0&0&1\end{array}}\right)$

Finally, multiply L<sub>1</sub> together and generate the fused matrix denoted as L (as previously mentioned). Using the matrix L, we obtain *A* = *LU*.

It is clear that in order for this algorithm to work, one needs to have $a_{n,n}^{(n-1)}\neq 0$ at each step (see the definition of ℓ<sub>i,n</sub>. If this assumption fails at some point, one needs to interchange n-th row with another row below it before continuing. This is why an LU decomposition in general looks like *P*<sup>−1</sup>*A* = *LU*.

#### LU Banachiewicz decomposition

![[media/2cad84ef1549670fa989d4e32d6c9e52e042f309.jpg]]
Illustration of operation of Banachiewicz LU algorithm to obtain 3-rd row and column of respectively matrices U and L. Involved matrices are named above squares marking their content. Matrix products and subtractions are applied only to elements in the thick frame boxes. Green filled thin frame boxes indicate values already known, from previous stages. Blue boxes indicate places in U and L matrices for storing of results.

Although Banachiewicz (1938) LU decomposition algorithm preceded the advent of programmed electronic computers, it was ready made for direct implementation into code as index swapping, transpose and column by column multiplication remain native built capabilities of the most programming languages and they are handled by compilers alone with little delay of the actual execution. The peculiar matrix notation used by Banachiewicz enabled him to multiply matrices column by column, a convenient feature for mechanical calculations as he could reveal consecutive factors by sliding a ruler to next rows of matrices. For human readers however, his equations are best transformed into standard matrix notation. To obtain from a full matrix A triangle matrices U and L calculations, start by copying top row and leftmost column of A respectively into corresponding positions of matrices U and L. The known unit diagonal elements of L are not stored nor used throughout the whole process. Next calculations continue for the subsequent rows and columns till the bottom right corner of A.

The figure illustrates calculations for 3rd row and column, assuming previous stages were already completed. Involved matrices are named above squares marking their content. Matrix products and subtractions are applied only to elements in the thick frame boxes. Green filled thin frame boxes indicate values already known, from previous stages. Blue boxes indicate places in U and L matrices for storing of results. Note that at each stage the result elements of L need to be divided by the corresponding pivot element on the main diagonal of U. This applies to the leftmost column of L too.

Note that after completion of 3rd stage the involved elements of matrix A are no longer used and neither those from the previous stages. This enables replacement of these elements with the result values of U and L, i.e. execution of LU decomposition *in place*, so that the whole A is replaced with U and L except for the unit diagonal of L. Banachiewicz LU algorithm is well suited for partial pivoting by choosing the absolute maximum pivot from the newly calculated row of U and subsequently swapping its columns so that it lands on the main diagonal. More details can be figured out from inspection of the enclosed Fortran90 code.

All partial pivoting LU algorithms cost roughly the same amount, of order $O\left({2 \over 3}n^{3}\right)$ operations, where n is the number of rows or columns of A.

#### LU Crout decomposition

Note that the decomposition obtained through this procedure is a *Doolittle decomposition*: the main diagonal of L is composed solely of ones. If one would proceed by removing elements *above* the main diagonal by adding multiples of the *columns* (instead of removing elements *below* the diagonal by adding multiples of the *rows*), we would obtain a *[Crout decomposition](https://en.wikipedia.org/wiki/Crout_matrix_decomposition)*, where the main diagonal of U is of ones.

Another (equivalent) way of producing a Crout decomposition of a given matrix A is to obtain a Doolittle decomposition of the transpose of A. Indeed, if *A*<sup>T</sup> = *L*<sub>0</sub>*U*<sub>0</sub> is the LU-decomposition obtained through the algorithm presented in this section, then by taking *L* = *U*<sup>T</sup>  
<sub>0</sub> and *U* = *L*<sup>T</sup>  
<sub>0</sub>, we have that *A* = *LU* is a Crout decomposition.

### Randomized algorithm

It is possible to find a low rank approximation to an LU decomposition using a [randomized algorithm](https://en.wikipedia.org/wiki/Randomized_algorithm). Given an input matrix A and a desired low rank k, the randomized LU returns permutation matrices P, Q and lower/upper trapezoidal matrices L, U of size m × k and k × n respectively, such that [with high probability](https://en.wikipedia.org/wiki/With_high_probability) ‖*PAQ* − *LU*‖<sub>2</sub> ≤ *Cσ*<sub>*k*+1</sub>, where C is a constant that depends on the parameters of the algorithm and *σ*<sub>*k*+1</sub> is the (*k*+1)-th singular value of the input matrix A.

### Theoretical complexity

If two matrices of order n can be multiplied in time *M*(*n*), where *M*(*n*) ≥ *n*<sup>*a*</sup> for some *a* \> 2, then an LU-decomposition can be computed in time O(*M*(*n*)). This means, for example, that an O(*n*<sup>2.376</sup>) algorithm exists based on the [Coppersmith–Winograd algorithm](https://en.wikipedia.org/wiki/Coppersmith%E2%80%93Winograd_algorithm). See also for [fast matrix multiplication algorithms](https://en.wikipedia.org/wiki/Computational_complexity_of_matrix_multiplication) article for more details.

### Sparse-matrix decomposition

Special algorithms have been developed for factorizing large [sparse matrices](https://en.wikipedia.org/wiki/Sparse_matrix). These algorithms attempt to find sparse factors L and U. Ideally, the cost of computation is determined by the number of nonzero entries, rather than by the size of the matrix.

These algorithms use the freedom to exchange rows and columns to minimize fill-in (entries that change from an initial zero to a nonzero value during the execution of an algorithm).

General treatment of orderings that minimize fill-in can be addressed using [graph theory](https://en.wikipedia.org/wiki/Graph_theory).

## Applications

### Solving linear equations

Given a system of linear equations in matrix form 

$$
A\mathbf {x} =\mathbf {b} ,
$$

we want to solve the equation for **x**, given A and **b**. Suppose we have already obtained the LUP decomposition of A such that *PA* = *LU*, so *LU***x** = *P***b**.

In this case the solution is done in two logical steps:

1.  First, we solve the equation *L***y** = *P***b** for **y**.
2.  Second, we solve the equation *U***x** = **y** for **x**.

In both cases we are dealing with triangular matrices (L and U), which can be solved directly by [forward and backward substitution](https://en.wikipedia.org/wiki/Triangular_matrix#Forward_and_back_substitution) without using the [Gaussian elimination](https://en.wikipedia.org/wiki/Gaussian_elimination) process (however we do need this process or equivalent to compute the LU decomposition itself).

The above procedure can be repeatedly applied to solve the equation multiple times for different **b**. In this case it is faster (and more convenient) to do an LU decomposition of the matrix A once and then solve the triangular matrices for the different **b**, rather than using Gaussian elimination each time. The matrices L and U could be thought to have "encoded" the Gaussian elimination process.

The cost of solving a system of linear equations is approximately 2/3*n*<sup>3</sup> floating-point operations if the matrix A has size n. This makes it twice as fast as algorithms based on [[QR Decomposition]], which costs about 4/3*n*<sup>3</sup> floating-point operations when [Householder reflections](https://en.wikipedia.org/wiki/Householder_reflection) are used. For this reason, LU decomposition is usually preferred.

### Inverting a matrix

When solving systems of equations, **b** is usually treated as a vector with a length equal to the height of matrix A. In matrix inversion however, instead of vector **b**, we have matrix B, where B is an n × p matrix, so that we are trying to find a matrix X (also a n × p matrix): 

$$
AX=LUX=B.
$$

We can use the same algorithm presented earlier to solve for each column of matrix X. Now suppose that B is the identity matrix of size n, I<sub>n</sub>. It follows that the result X must be the inverse of A.

### Computing the determinant

Given the LUP decomposition *A* = *P*<sup>−1</sup>*LU* of a square matrix A, the determinant of A can be computed straightforwardly as 

$$
{\begin{aligned}\det(A)&=\det \left(P^{-1}\right)\det(L)\det(U)\\&=(-1)^{S}\left(\prod _{i=1}^{n}l_{ii}\right)\left(\prod _{i=1}^{n}u_{ii}\right).\end{aligned}}
$$

The second equation follows from the fact that the determinant of a triangular matrix is simply the product of its diagonal entries, and that the determinant of a permutation matrix is equal to (−1)<sup>*S*</sup> where S is the number of row exchanges in the decomposition.

In the case of LU decomposition with full pivoting, det(*A*) also equals the right-hand side of the above equation, if we let S be the total number of row and column exchanges.

The same method readily applies to LU decomposition by setting P equal to the identity matrix.

## History

![[media/4b3de1788e4191bc7a56577d0b2620c05186e650.jpg]]
LU decomposition: LU factors and their product in original Banachiewicz(1938) matrix notation

The LU decomposition is related to elimination of linear systems of equations, as e.g. described by Ralston. The solution of N linear equations in N unknowns by elimination was already known to ancient Chinese. Before Gauss many mathematicians in Eurasia were performing and perfecting it yet as the method became relegated to school grade, few of them left any detailed descriptions. Thus the name Gaussian elimination is only a convenient abbreviation of a complex history.

The Polish astronomer Tadeusz Banachiewicz introduced the LU decomposition in 1938. About Banachiewicz, Paul Dwyer stated:

> It appears that Gauss and Doolittle applied the method \[of elimination\] only to symmetric equations. More recent authors, for example, Aitken, Banachiewicz, Dwyer, and Crout ... have emphasized the use of the method, or variations of it, in connection with non-symmetric problems ... Banachiewicz ... saw the point ... that the basic problem is really one of matrix factorization, or "decomposition" as he called it.

— Paul Dwyer, *Linear Computations* (1951)

Banachiewicz was the first to consider elimination in terms of matrices and in this way formulated LU decomposition, as demonstrated by his graphic illustration. His calculations follow ordinary matrix ones, yet notation deviates in that he preferred to write one factor transposed, to be able to multiply them mechanically column by column, by sliding ruler down consecutive rows of both (using [arithmometer](https://en.wikipedia.org/wiki/Arithmometer)). Combined with swapped order of indices his formulae in modern notation read 

$$
{\begin{aligned}{\mathbf {x} }\cdot IA'={\mathbf {0} }&\rightarrow A'{\mathbf {x} =0}\equiv (A|{\mathbf {l} }){\mathbf {x} },\\A=G\cdot H&\rightarrow A^{T}=G^{T}H,\end{aligned}}
$$

where *IA* → *A*<sup>T</sup>; **x** ≡ \[*x*<sub>1</sub>, ... , *x<sub>n</sub>*, −1\]; *A*′ refers to A extended with the last column; and the last component of **x** is −1. Matrix formulae to calculate rows and columns of LU factors by recursion are given in the remaining part of Banachiewicz's paper as Eq. (2.3) and (2.4). This paper by Banachiewicz contains both derivation of LU and *R*<sup>T</sup>*R* factors of respectively non-symmetric and symmetric matrices. They are sometimes confused as later publications tend to tie his name solely with the rediscovery of Cholesky decomposition. Banachiewicz himself can be excused of inaction as already next year he suffered from persecution by occupiers, spending three month in [the Sachsenhausen Concentration Camp](https://en.wikipedia.org/wiki/Sachsenhausen_concentration_camp), on release from which he carried himself from a train his collaborator and co-prisoner Antoni Wilk, who died of exhaustion a week later.

## Code examples

### Fortran90 code example

    Module mlu
          Implicit None
          Integer, Parameter :: SP = Kind(1d0) ! set I/O real precision
          Private
          Public luban, lusolve
    Contains
          Subroutine luban (a, tol, g, h, ip, condinv, detnth)
    ! By Banachiewicz (1938, hereafter B38) LU decomposition method calculates such
    ! triangles L=G^T, and U=H  that square B=A^T=G^TH=LU. Partial pivoting
    ! by column permutation IP(:) is modern addition.
    ! Within the code a, g correspond to B38 A^T and G^T, so that a=gh holds.
    !
    ! Normal use is for square A, however for RHS l already known
    ! input of (A|l)^T yields (L|y^T)^T where x in L^Tx=y is solution of Ax=l.
             Real (SP), Intent (In) :: a (:, :)! input matrix A(m,n), n<=m
             Real (SP), Intent (In) :: tol ! tolerance for near zero pivot
             Real (SP), Intent (Out) :: g (size(a,dim=1), size(a,dim=2)) ! L(m,n)
             Real (SP), Intent (Out) :: h (size(a,dim=2), size(a,dim=2)) ! U(n,n)
                                           ! note U columns are permuted
             Real (SP), Intent (Out) :: condinv ! 1/cond(A), 0 for singular A
             Real (SP), Intent (Out) :: detnth  ! sign*Abs(det(A))**(1/n)
             Integer, Intent (Out)   :: ip (size(a, dim=2)) ! columns permutation
    !
             Integer :: k, n, j, l, isig
             Real (SP) :: tol0, pivmax, pivmin, piv
    !
             n = size (a, dim=2)
             tol0 = Max (tol, 3._SP*epsilon(tol0))! use default for tol=0
    !
    ! Rectangular A and G are permitted under condition:
             If (n > size(a, dim=1) .Or. n < 1) Stop 91
             Forall (k=1:n) ip (k) = k
             h = 0._SP
             g = 0._SP
             isig = 1
             detnth = 0._SP
             pivmax = Maxval (Abs (a(1, :)))
             pivmin = pivmax
    !
             Do k = 1, n
    ! Banachiewicz (1938) Eq. (2.3)
                h(k, ip(k:)) = a(k, ip(k:)) - Matmul(g(k, :k-1), h(:k-1, ip(k:)))
    !
    ! Find row pivot
                j = (Maxloc(Abs(h(k, ip(k:))), dim=1) + k-1)
                If (j /= k) Then ! Swap columns j and k
                   isig = - isig ! Change Det(A) sign because of permutation
                   l = ip (k)
                   ip (k) = ip (j)
                   ip (j) = l
                End If
                piv = Abs (h(k, ip(k)))
                pivmax = Max (piv, pivmax) ! Adjust condinv
                pivmin = Min (piv, pivmin)
                If (piv < tol0) Then ! singular matrix
                   isig = 0
                   pivmax = 1._SP
                   Exit
                Else ! Account for pivot contribution to Det(A) sign and value
                   If (h(k, ip(k)) < 0._SP) isig = - isig
                   detnth = detnth + Log (piv)
                End If
    !
    ! Transposed Banachiewicz (1938) Eq. (2.4)
                g (k+1:, k) = (a(k+1:, ip(k)) - &
                   Matmul(g(k+1:, :k-1), h(:k-1, ip(k)))) / h (k, ip(k))
                g (k, k) = 1._SP
             End Do
    !
             detnth = isig * Exp (detnth/n)
             condinv = Abs (isig) * pivmin / pivmax
    ! Test for square A(n,n) by uncommenting below
    !         Print *, '|AQ-LU| ',Maxval (Abs(a(:,ip(:))-Matmul(g, h(:,ip(:)))))
          End Subroutine luban

          Subroutine lusolve(l,u,ip,x)
    ! Solves Ax=b system using triangle factors LU=A      
             Real (SP), Intent (In)    :: l (:, :) ! lower triangle matrix L(n,n)
             Real (SP), Intent (In)    :: u (:, :) ! upper triangle matrix U(n,n)
             Integer, Intent (In)      :: ip (:)   ! columns permutation IP(n)
             Real (SP), Intent (InOut) :: x (:, :) ! Input: m sets of RHSs B(n,m), 
                              ! Output: the corresponding sets of unknowns X(n,m)

             Integer :: n, m, i, j

             n = size(ip)
             m = size(x, dim=2)
             If (n<1.Or.m<1.Or.Any([n,n]/=shape(l)).Or.Any(shape(l)/=shape(u)).Or. &
                n/=size(x,dim=1)) Stop 91
             Do i = 1, m
                Do j = 1, n
                   x(j,i) = x(j,i)-dot_product(x(:j-1,i),l(j,:j-1))
                End Do
                Do j = n, 1, -1
                   x(j,i) = (x(j,i)-dot_product(x(j+1:,i),u(j,ip(j+1:)))) / &
                      u(j,ip(j))
                End Do
             End Do
          End Subroutine lusolve     
    End Module mlu

### C code example

    /* INPUT: A - array of pointers to rows of a square matrix having dimension N
     *        Tol - small tolerance number to detect failure when the matrix is near degenerate
     * OUTPUT: Matrix A is changed, it contains a copy of both matrices L-E and U as A=(L-E)+U such that P*A=L*U.
     *        The permutation matrix is not stored as a matrix, but in an integer vector P of size N+1 
     *        containing column indexes where the permutation matrix has "1". The last element P[N]=S+N, 
     *        where S is the number of row exchanges needed for determinant computation, det(P)=(-1)^S    
     */
    int LUPDecompose(double **A, int N, double Tol, int *P) {

        int i, j, k, imax; 
        double maxA, *ptr, absA;

        for (i = 0; i <= N; i++)
            P[i] = i; //Unit permutation matrix, P[N] initialized with N

        for (i = 0; i < N; i++) {
            maxA = 0.0;
            imax = i;

            for (k = i; k < N; k++)
                if ((absA = fabs(A[k][i])) > maxA) { 
                    maxA = absA;
                    imax = k;
                }

            if (maxA < Tol) return 0; //failure, matrix is degenerate

            if (imax != i) {
                //pivoting P
                j = P[i];
                P[i] = P[imax];
                P[imax] = j;

                //pivoting rows of A
                ptr = A[i];
                A[i] = A[imax];
                A[imax] = ptr;

                //counting pivots starting from N (for determinant)
                P[N]++;
            }

            for (j = i + 1; j < N; j++) {
                A[j][i] /= A[i][i];

                for (k = i + 1; k < N; k++)
                    A[j][k] -= A[j][i] * A[i][k];
            }
        }

        return 1;  //decomposition done 
    }

    /* INPUT: A,P filled in LUPDecompose; b - rhs vector; N - dimension
     * OUTPUT: x - solution vector of A*x=b
     */
    void LUPSolve(double **A, int *P, double *b, int N, double *x) {

        for (int i = 0; i < N; i++) {
            x[i] = b[P[i]];

            for (int k = 0; k < i; k++)
                x[i] -= A[i][k] * x[k];
        }

        for (int i = N - 1; i >= 0; i--) {
            for (int k = i + 1; k < N; k++)
                x[i] -= A[i][k] * x[k];

            x[i] /= A[i][i];
        }
    }

    /* INPUT: A,P filled in LUPDecompose; N - dimension
     * OUTPUT: IA is the inverse of the initial matrix
     */
    void LUPInvert(double **A, int *P, int N, double **IA) {

        for (int j = 0; j < N; j++) {
            for (int i = 0; i < N; i++) {
                IA[i][j] = P[i] == j ? 1.0 : 0.0;

                for (int k = 0; k < i; k++)
                    IA[i][j] -= A[i][k] * IA[k][j];
            }

            for (int i = N - 1; i >= 0; i--) {
                for (int k = i + 1; k < N; k++)
                    IA[i][j] -= A[i][k] * IA[k][j];

                IA[i][j] /= A[i][i];
            }
        }
    }

    /* INPUT: A,P filled in LUPDecompose; N - dimension. 
     * OUTPUT: Function returns the determinant of the initial matrix
     */
    double LUPDeterminant(double **A, int *P, int N) {

        double det = A[0][0];

        for (int i = 1; i < N; i++)
            det *= A[i][i];

        return (P[N] - N) % 2 == 0 ? det : -det;
    }

### C# code example

    public class SystemOfLinearEquations
    {
        public double[] SolveUsingLU(double[,] matrix, double[] rightPart, int n)
        {
            // decomposition of matrix
            double[,] lu = new double[n, n];
            double sum = 0;
            for (int i = 0; i < n; i++)
            {
                for (int j = i; j < n; j++)
                {
                    sum = 0;
                    for (int k = 0; k < i; k++)
                        sum += lu[i, k] * lu[k, j];
                    lu[i, j] = matrix[i, j] - sum;
                }
                for (int j = i + 1; j < n; j++)
                {
                    sum = 0;
                    for (int k = 0; k < i; k++)
                        sum += lu[j, k] * lu[k, i];
                    lu[j, i] = (1 / lu[i, i]) * (matrix[j, i] - sum);
                }
            }

            // lu = L+U-I
            // find solution of Ly = b
            double[] y = new double[n];
            for (int i = 0; i < n; i++)
            {
                sum = 0;
                for (int k = 0; k < i; k++)
                    sum += lu[i, k] * y[k];
                y[i] = rightPart[i] - sum;
            }
            // find solution of Ux = y
            double[] x = new double[n];
            for (int i = n - 1; i >= 0; i--)
            {
                sum = 0;
                for (int k = i + 1; k < n; k++)
                    sum += lu[i, k] * x[k];
                x[i] = (1 / lu[i, i]) * (y[i] - sum);
            }
            return x;
        }
    }

### MATLAB code example

    function LU = LUDecompDoolittle(A)
        n = length(A);
        LU = A;
        for k = 2:n
            for i = 1 : k-1
                lamda = LU(k,i) / LU (i, i);
                LU(k,i) = lamda;
                LU(k,i+1:n) = LU(k,i+1:n) - LU(i,i+1:n) * lamda;
            end
        end
    end

    function x = SolveLinearSystem(LU, B)
        n = length(LU);
        y = zeros(size(B));
        % find solution of Ly = B
        for i = 1:n
            y(i,:) = B(i,:) - LU(i,1:i)*y(1:i,:);
        end
        % find solution of Ux = y
        x = zeros(size(B));
        for i = n:(-1):1
            x(i,:) = (y(i,:) - LU(i,(i + 1):n)*x((i + 1):n,:))/LU(i, i);
        end    
    end

    A = [ 4 3 3; 6 3 3; 3 4 3 ]
    LU = LUDecompDoolittle(A)
    B = [ 1 2 3; 4 5 6; 7 8 9; 10 11 12 ]'
    x = SolveLinearSystem(LU, B)
    A * x

## See also

- [Block LU decomposition](https://en.wikipedia.org/wiki/Block_LU_decomposition)
- [Bruhat decomposition](https://en.wikipedia.org/wiki/Bruhat_decomposition)
- [[Cholesky Decomposition]]
- [Crout matrix decomposition](https://en.wikipedia.org/wiki/Crout_matrix_decomposition)
- [Incomplete LU factorization](https://en.wikipedia.org/wiki/Incomplete_LU_factorization)
- [LU Reduction](https://en.wikipedia.org/wiki/LU_Reduction)
- [Matrix decomposition](https://en.wikipedia.org/wiki/Matrix_decomposition)
- [[QR Decomposition]]

## Notes

1.  ^    .
2.  , p. [819](https://archive.org/details/introduction-to-algorithms-third-edition-2009/page/819/), 28.1: Solving systems of linear equations.
3.  ^   , Corollary 3.
4.  , p. 166.
5.  , p. 161.
6.  ; , p. [133](https://archive.org/details/linear-algebra-its-applications-6th/page/133/), 2.5: Matrix Factorizations.
7.  , Leading Principal Minor.
8.  ^   , Corollary 3.5.5
9.  , Theorem 3.5.2.
10. Nhiayi, Ly; Phan-Yamada, Tuyetdong (2021). "Examining Possible LU Decomposition". *North American GeoGebra Journal*. **9** (1).
11. .
12. .
13. , pp. 112, 119.
14. Shabat, Gil; Shmueli, Yaniv; Aizenbud, Yariv; Averbuch, Amir (2016). "Randomized LU Decomposition". *[Applied and Computational Harmonic Analysis](https://en.wikipedia.org/wiki/Applied_and_Computational_Harmonic_Analysis)*. **44** (2): 246–272. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1310.7202](https://arxiv.org/abs/1310.7202). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.acha.2016.04.006](https://doi.org/10.1016%2Fj.acha.2016.04.006). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [1900701](https://api.semanticscholar.org/CorpusID:1900701).
15. .
16. , p. 152.
17. , p. 121.
18. .
19. .
20. .

## References

- [Banachiewicz, T.](https://en.wikipedia.org/wiki/Tadeusz_Banachiewicz) (1938), ["Méthode de résolution numérique des équations linéaires …"](https://www.oa.uj.edu.pl/pbl/books/T_Banachiewicz_1938_Bull.Acad.Pol.Ser.A.No.10-12_p.393-404.pdf) (PDF), *Bull. Intern. De l'Acad. Polonaise, Série A. Sc. Math.*: 393–404.
- Bunch, James R.; [Hopcroft, John](https://en.wikipedia.org/wiki/John_Hopcroft) (1974), "Triangular factorization and inversion by fast matrix multiplication", *[Mathematics of Computation](https://en.wikipedia.org/wiki/Mathematics_of_Computation)*, **28** (125): 231–236, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2005828](https://doi.org/10.2307%2F2005828), [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[1813/6003](https://hdl.handle.net/1813%2F6003), [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0025-5718](https://search.worldcat.org/issn/0025-5718), [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2005828](https://www.jstor.org/stable/2005828).
- [Cormen, Thomas H.](https://en.wikipedia.org/wiki/Thomas_H._Cormen); [Leiserson, Charles E.](https://en.wikipedia.org/wiki/Charles_E._Leiserson); [Rivest, Ronald L.](https://en.wikipedia.org/wiki/Ronald_L._Rivest); [Stein, Clifford](https://en.wikipedia.org/wiki/Clifford_Stein) (2009), [*Introduction to Algorithms*](https://en.wikipedia.org/wiki/Introduction_to_Algorithms) (3rd ed.), MIT Press and McGraw-Hill, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-262-03293-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-262-03293-3).
- Dwyer, Paul S. (1951), *Linear Computations*, New York: Wiley.
- [Golub, Gene H.](https://en.wikipedia.org/wiki/Gene_H._Golub); [Van Loan, Charles F.](https://en.wikipedia.org/wiki/Charles_F._Van_Loan) (1996), *Matrix Computations* (3rd ed.), Baltimore: Johns Hopkins, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8018-5414-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8018-5414-9).
- Hart, Roger (2011), *The Chinese Roots of Linear Algebra*, Baltimore: Johns Hopkins, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0801897559](https://en.wikipedia.org/wiki/Special:BookSources/978-0801897559).
- Horn, Roger A.; Johnson, Charles R. (1985), *Matrix Analysis*, Cambridge University Press, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-38632-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-38632-6). See Section 3.5. *N* − 1
- Householder, Alston S. (1975), *The Theory of Matrices in Numerical Analysis*, New York: [Dover Publications](https://en.wikipedia.org/wiki/Dover_Publications), [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0378371](https://mathscinet.ams.org/mathscinet-getitem?mr=0378371).
- Lay, David C.; Lay, Steven R.; McDonald, Judi J. (2021), [Linear Algebra and its Applications](https://archive.org/details/linear-algebra-its-applications-6th/) (Sixth ed.), Pearson, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-13-585125-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-13-585125-8).
- Okunev, Pavel; Johnson, Charles R. (1997), *Necessary And Sufficient Conditions For Existence of the LU Factorization of an Arbitrary Matrix*, [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[math.NA/0506382](https://arxiv.org/abs/math.NA/0506382).
- Poole, David (2006), *Linear Algebra: A Modern Introduction* (2nd ed.), Canada: Thomson Brooks/Cole, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-534-99845-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-534-99845-5).
- Ralston, Anthony (1965), *A First Course in Numerical Analysis*, New York: McGraw-Hill, Inc, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-070-51157-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-070-51157-6).
- Press, WH; Teukolsky, SA; Vetterling, WT; Flannery, BP (2007), ["Section 2.3"](http://apps.nrbook.com/empanel/index.html?pg=48), *Numerical Recipes: The Art of Scientific Computing* (3rd ed.), New York: Cambridge University Press, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-88068-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-88068-8).
- [Trefethen, Lloyd N.](https://en.wikipedia.org/wiki/Lloyd_Nicholas_Trefethen); Bau, David (1997), *Numerical linear algebra*, Philadelphia: Society for Industrial and Applied Mathematics, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-89871-361-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-89871-361-9).
- Rigotti, Luca (2001), [ECON 2001 - Introduction to Mathematical Methods, Lecture 8](https://sites.pitt.edu/~luca/ECON2001/)

## External links

**References**

- [LU decomposition](http://mathworld.wolfram.com/LUDecomposition.html) on *MathWorld*.
- [LU decomposition](http://www.math-linux.com/spip.php?article51) on *Math-Linux*.
- [LU decomposition](http://numericalmethods.eng.usf.edu/topics/lu_decomposition.html) at *Holistic Numerical Methods Institute*
- [LU matrix factorization](http://www.mathworks.com/help/techdoc/ref/lu.html). MATLAB reference.

**Computer code**

- [LAPACK](http://www.netlib.org/lapack/) is a collection of FORTRAN subroutines for solving dense linear algebra problems
- [ALGLIB](http://www.alglib.net/) includes a partial port of the LAPACK to C++, C#, Delphi, etc.
- [C++ code](https://web.archive.org/web/20120301111350/http://www.johnloomis.org/ece538/notes/Matrix/ludcmp.html), Prof. J. Loomis, [University of Dayton](https://en.wikipedia.org/wiki/University_of_Dayton)
- [C code](http://www.mymathlib.com/matrices/linearsystems/doolittle.html), Mathematics Source Library
- [Rust code](https://github.com/NJdevPro/Rmatrix/blob/main/src/rmatrix.rs)
- [LU in X10](https://web.archive.org/web/20100429160954/http://docs.codehaus.org/display/XTENLANG/LU)

**Online resources**

- [WebApp descriptively solving systems of linear equations with LU Decomposition](https://archive.today/20110425223706/http://sole.ooz.ie/)
- [Matrix Calculator with steps, including LU decomposition](https://matrixcalc.org/),
- [LU Decomposition Tool](https://web.archive.org/web/20081020061504/http://www.uni-bonn.de/~manfear/matrix_lu.php), uni-bonn.de
- [LU Decomposition](http://demonstrations.wolfram.com/LUDecomposition/) by [Ed Pegg, Jr.](https://en.wikipedia.org/wiki/Ed_Pegg,_Jr.), [The Wolfram Demonstrations Project](https://en.wikipedia.org/wiki/The_Wolfram_Demonstrations_Project), 2007.
