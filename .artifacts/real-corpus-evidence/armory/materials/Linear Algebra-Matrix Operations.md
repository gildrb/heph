[[linear-algebra.base]]

> Source: [Matrix (mathematics)](https://en.wikipedia.org/wiki/Matrix_(mathematics))
> License: Wikipedia content is available under CC BY-SA 4.0.

![[media/4461ba74a15c847918d15dc6be8019b76ab5d62f.png]]
An m × n matrix: the m rows are horizontal and the n columns are vertical. Each element of a matrix is often denoted by a variable with two [subscripts](https://en.wikipedia.org/wiki/Index_notation). For example, <em>a</em><sub>2,1</sub> represents the element at the second row and first column of the matrix.

In [mathematics](https://en.wikipedia.org/wiki/Mathematics), a **matrix** (pl.: **matrices**) is a [rectangular](https://en.wikipedia.org/wiki/Rectangle) array of [numbers](https://en.wikipedia.org/wiki/Number) or other [mathematical objects](https://en.wikipedia.org/wiki/Mathematical_objects) with elements or entries arranged in rows and columns, usually satisfying certain properties of [addition](https://en.wikipedia.org/wiki/Matrix_addition) and [[Matrix Multiplication|multiplication]].

For example, 

$$
{\begin{bmatrix}1&9&-13\\20&5&-6\end{bmatrix}}
$$

 denotes a matrix with two rows and three columns. This is often referred to as a "two-by-three matrix", a 2 × 3 matrix, or a matrix of dimension 2 × 3.

In [linear algebra](https://en.wikipedia.org/wiki/Linear_algebra), matrices are used as [linear maps](https://en.wikipedia.org/wiki/Linear_map). In [geometry](https://en.wikipedia.org/wiki/Geometry), matrices are used for [geometric transformations](https://en.wikipedia.org/wiki/Geometric_transformation) (for example [rotations](https://en.wikipedia.org/wiki/Rotation_(mathematics) "Rotation (mathematics)")) and [coordinate changes](https://en.wikipedia.org/wiki/Coordinate_change). In [numerical analysis](https://en.wikipedia.org/wiki/Numerical_analysis), many computational problems are solved by reducing them to a matrix computation, and this often involves computing with matrices of huge dimensions. Matrices are used in most areas of mathematics and scientific fields, either directly, or through their use in geometry and numerical analysis.

*[Square matrices](https://en.wikipedia.org/wiki/Square_matrices)*, matrices with the same number of rows and columns, play a major role in matrix theory. The [[Determinant]] of a square matrix is a number associated with the matrix, which is fundamental for the study of a square matrix; for example, a square matrix is [invertible](https://en.wikipedia.org/wiki/Invertible_matrix) if and only if it has a nonzero determinant and the [eigenvalues](https://en.wikipedia.org/wiki/Eigenvalue) of a square matrix are the roots of its [characteristic polynomial](https://en.wikipedia.org/wiki/Characteristic_polynomial), $\det(\lambda I-A)$.

**Matrix theory** is the [branch of mathematics](https://en.wikipedia.org/wiki/Branch_of_mathematics) that focuses on the study of matrices. It was initially a sub-branch of linear algebra, but soon grew to include subjects related to [graph theory](https://en.wikipedia.org/wiki/Graph_theory), [algebra](https://en.wikipedia.org/wiki/Algebra), [combinatorics](https://en.wikipedia.org/wiki/Combinatorics) and [statistics](https://en.wikipedia.org/wiki/Statistics).

## Definition

A matrix is a rectangular array of [numbers](https://en.wikipedia.org/wiki/Number) (or other mathematical objects), called the "entries" of the matrix. Matrices are subject to standard [operations](https://en.wikipedia.org/wiki/Operation_(mathematics) "Operation (mathematics)") such as [addition](#Basic_operations) and [multiplication](#Matrix_multiplication). Most commonly, a matrix over a [field](https://en.wikipedia.org/wiki/Field_(mathematics) "Field (mathematics)") $F$ is a rectangular array of [elements](https://en.wikipedia.org/wiki/Element_(mathematics)) of $F$. A **real matrix** and a **complex matrix** are matrices whose entries are respectively [real numbers](https://en.wikipedia.org/wiki/Real_number) or [complex numbers](https://en.wikipedia.org/wiki/Complex_number). More general types of entries are discussed [below](#Matrices_with_more_general_entries). For instance, this is a real matrix: 

$$
\mathbf {A} ={\begin{bmatrix}-1.3&0.6\\20.4&5.5\\9.7&-6.2\end{bmatrix}}.
$$

The numbers (or other objects) in the matrix are called its *entries* or its *elements*. The horizontal and vertical lines of entries in a matrix are respectively called *rows* and *columns*.

### Size

The size of a matrix is defined by the number of rows and columns it contains. There is no limit to the number of rows and columns that a matrix (in the usual sense) can have as long as they are positive integers. A matrix with m rows and n columns is called an m × n matrix, or m-by-n matrix, where m and n are called its *dimensions*. For example, the matrix ${\mathbf {A} }$ above is a 3 × 2 matrix.

Matrices with a single row are called *[row matrices](https://en.wikipedia.org/wiki/Row_matrix)* or *row vectors*, and those with a single column are called *[column matrices](https://en.wikipedia.org/wiki/Column_matrix)* or *column vectors*. A matrix with the same number of rows and columns is called a *[square matrix](https://en.wikipedia.org/wiki/Square_matrix)*. A matrix with an infinite number of rows or columns (or both) is called an [*infinite matrix*](#Infinite_matrices). In some contexts, such as [computer algebra programs](https://en.wikipedia.org/wiki/Computer_algebra_system), it is useful to consider a matrix with no rows or no columns, called an [*empty matrix*](#Empty_matrix).

|  |  |  |  |
|----|----|----|----|
| Name | Size | Example | Description |
| [Row matrix](https://en.wikipedia.org/wiki/Row_matrix) | $1\times n$ | ${\begin{bmatrix}3&7&2\end{bmatrix}}$ | A matrix with one row and more than one columns, sometimes used to represent a vector |
| [Column matrix](https://en.wikipedia.org/wiki/Column_matrix) | $n\times 1$ | ${\begin{bmatrix}4\\1\\8\end{bmatrix}}$ | A matrix with one column and more than one rows, sometimes used to represent a vector |
| [Square matrix](https://en.wikipedia.org/wiki/Square_matrix) | $n\times n$ | ${\begin{bmatrix}9&13&5\\1&11&7\\2&6&3\end{bmatrix}}$ | A matrix with the same number of rows and columns, sometimes used to represent a [linear transformation](#Linear_transformations) from a vector space to itself, such as [reflection](https://en.wikipedia.org/wiki/Reflection_(mathematics) "Reflection (mathematics)"), [rotation](https://en.wikipedia.org/wiki/Rotation_(mathematics) "Rotation (mathematics)"), or [shearing](https://en.wikipedia.org/wiki/Shear_mapping). |

Overview of a matrix size {.wikitable}

## Notation

The specifics of symbolic matrix notation vary widely, with some prevailing trends. Matrices are commonly written in [square brackets](https://en.wikipedia.org/wiki/Square_bracket) or [parentheses](https://en.wikipedia.org/wiki/Parentheses), so that an m × n matrix $\mathbf {A}$ is represented as 

$$
\mathbf {A} ={\begin{bmatrix}a_{11}&a_{12}&\cdots &a_{1n}\\a_{21}&a_{22}&\cdots &a_{2n}\\\vdots &\vdots &\ddots &\vdots \\a_{m1}&a_{m2}&\cdots &a_{mn}\end{bmatrix}}={\begin{pmatrix}a_{11}&a_{12}&\cdots &a_{1n}\\a_{21}&a_{22}&\cdots &a_{2n}\\\vdots &\vdots &\ddots &\vdots \\a_{m1}&a_{m2}&\cdots &a_{mn}\end{pmatrix}}.
$$

 This may be abbreviated by writing only a single generic term, possibly along with indices, as in 

$$
\mathbf {A} =\left(a_{ij}\right),\quad \left[a_{ij}\right],\quad {\text{or}}\quad \left(a_{ij}\right)_{1\leq i\leq m,\;1\leq j\leq n}
$$

 or $\mathbf {A} =(a_{i,j})_{1\leq i,j\leq n}$ in the case that $n=m$.

Matrices are usually symbolized using [upper-case](https://en.wikipedia.org/wiki/Upper-case) letters (such as ${\mathbf {A} }$ in the examples above), while the corresponding [lower-case](https://en.wikipedia.org/wiki/Lower-case) letters, with two subscript indices (e.g., $a_{11}$, or $a_{1,1}$), represent the entries. In addition to using upper-case letters to symbolize matrices, many authors use a special [typographical style](https://en.wikipedia.org/wiki/Emphasis_(typography) "Emphasis (typography)"), commonly boldface roman (non-italic), to further distinguish matrices from other mathematical objects. An alternative notation involves the use of a double-underline with the variable name, with or without boldface style, as in ${\underline {\underline {A}}}$.

The entry in the *i*th row and *j*th column of a matrix **A** is sometimes referred to as the ${i,j}$ or $(i,j)$ entry of the matrix, and commonly denoted by $a_{i,j}$ or $a_{ij}$. Alternative notations for that entry are ${\mathbf {A} [i,j]}$ and $\mathbf {A} _{i,j}$. For example, the $(1,3)$ entry of the following matrix $\mathbf {A}$ is 5 (also denoted $a_{13}$, $a_{1,3}$, $\mathbf {A} [1,3]$ or ${\mathbf {A} }_{1,3}$): 

$$
\mathbf {A} ={\begin{bmatrix}4&-7&\color {red}{5}&0\\-2&0&11&8\\19&1&-3&12\end{bmatrix}}
$$

Sometimes, the entries of a matrix can be defined by a formula such as $a_{i,j}=f(i,j)$. For example, each of the entries of the following matrix $\mathbf {A}$ is determined by the formula $a_{ij}=i-j$. 

$$
\mathbf {A} ={\begin{bmatrix}0&-1&-2&-3\\1&0&-1&-2\\2&1&0&-1\end{bmatrix}}
$$

 In this case, the matrix itself is sometimes defined by that formula, within square brackets or double parentheses. For example, the matrix above is defined as ${\mathbf {A} }=[i-j]$ or $\mathbf {A} =((i-j))$. If matrix size is m × n, the above-mentioned formula $f(i,j)$ is valid for any $i=1,\dots ,m$ and any $j=1,\dots ,n$. This can be specified separately or indicated using m × n as a subscript. For instance, the matrix $\mathbf {A}$ above is 3 × 4, and can be defined as ${\mathbf {A} }=[i-j](i=1,2,3;j=1,\dots ,4)$ or $\mathbf {A} =[i-j]_{3\times 4}$.

Some programming languages utilize doubly subscripted arrays (or arrays of arrays) to represent an {m-by-n matrix. Some programming languages start the numbering of array indexes at zero, in which case the entries of an m × n matrix are indexed by $0\leq i\leq m-1$ and $0\leq j\leq n-1$. This article follows the more common convention in mathematical writing where enumeration starts from 1.

The [set](https://en.wikipedia.org/wiki/Set_(mathematics) "Set (mathematics)") of all m-by-n real matrices is often denoted ${\mathcal {M}}(m,n)$, or ${\mathcal {M}}_{m\times n}(\mathbb {R} )$. The set of all m × n matrices over another [field](https://en.wikipedia.org/wiki/Field_(mathematics) "Field (mathematics)"), or over a [ring](https://en.wikipedia.org/wiki/Ring_(mathematics) "Ring (mathematics)") *R*, is similarly denoted ${\mathcal {M}}(m,n,R)$, or ${\mathcal {M}}_{m\times n}(R)$. If *m* = *n*, such as in the case of [square matrices](https://en.wikipedia.org/wiki/Square_matrices), one does not repeat the dimension: ${\mathcal {M}}(n,R)$, or ${\mathcal {M}}_{n}(R)$. Often, $M$, or $\operatorname {Mat}$, is used in place of ${\mathcal {M}}$.

## Basic operations

Several basic operations can be applied to matrices. Some, such as *transposition* and *submatrix* do not depend on the nature of the entries. Others, such as *matrix addition*, *scalar multiplication*, *matrix multiplication*, and *row operations* involve operations on matrix entries and therefore require that matrix entries are numbers or belong to a [field](https://en.wikipedia.org/wiki/Field_(mathematics) "Field (mathematics)") or a [ring](https://en.wikipedia.org/wiki/Ring_(mathematics) "Ring (mathematics)").

In this section, it is supposed that matrix entries belong to a fixed ring, which is typically a field of numbers.

### Addition

![[media/10ca7138bc799ae7fc766f52fccbb6b6dab8d879.png]]
Illustration of the addition of two matrices.

Matrix addition and subtraction require matrices of a consistent size, and are calculated entrywise. The *sum* **A** + **B** and the difference **A** − **B** of two m × n matrices are:

$$
{\begin{aligned}({\mathbf {A}}+{\mathbf {B}})_{i,j}={\mathbf {A}}_{i,j}+{\mathbf {B}}_{i,j},\quad 1\leq i\leq m,\quad 1\leq j\leq n.\\({\mathbf {A}}-{\mathbf {B}})_{i,j}={\mathbf {A}}_{i,j}-{\mathbf {B}}_{i,j},\quad 1\leq i\leq m,\quad 1\leq j\leq n.\end{aligned}}
$$

For example,

$$
{\begin{bmatrix}1&3&1\\1&0&0\end{bmatrix}}+{\begin{bmatrix}0&0&5\\7&5&0\end{bmatrix}}={\begin{bmatrix}1+0&3+0&1+5\\1+7&0+5&0+0\end{bmatrix}}={\begin{bmatrix}1&3&6\\8&5&0\end{bmatrix}}
$$

Familiar properties of numbers extend to these operations on matrices: for example, addition is [commutative](https://en.wikipedia.org/wiki/Commutative), that is, the matrix sum does not depend on the order of the summands: **A** + **B** = **B** + **A**.

### Scalar multiplication

The product *c***A** of a number c (also called a [scalar](https://en.wikipedia.org/wiki/Scalar_(mathematics) "Scalar (mathematics)") in this context) and a matrix **A** is computed by multiplying each entry of **A** by c: 

$$
(c{\mathbf {A}})_{i,j}=c\cdot {\mathbf {A}}_{i,j}
$$

 This operation is called *scalar multiplication*, but its result is not named "scalar product" to avoid confusion, since "scalar product" is often used as a synonym for "[inner product](https://en.wikipedia.org/wiki/Inner_product)". For example:

$$
2\cdot {\begin{bmatrix}1&8&-3\\4&-2&5\end{bmatrix}}={\begin{bmatrix}2\cdot 1&2\cdot 8&2\cdot -3\\2\cdot 4&2\cdot -2&2\cdot 5\end{bmatrix}}={\begin{bmatrix}2&16&-6\\8&-4&10\end{bmatrix}}
$$

Matrix subtraction is consistent with composition of matrix addition with scalar multiplication by –1:

$$
\mathbf {A} -\mathbf {B} =\mathbf {A} +(-1)\cdot \mathbf {B}
$$

### Transpose

The *transpose* of an m × n matrix **A** is the n × m matrix **A**<sup>T</sup> (also denoted **A**<sup>tr</sup> or <sup>t</sup>**A**) formed by turning rows into columns and vice versa: 

$$
\left({\mathbf {A}}^{\rm {T}}\right)_{i,j}={\mathbf {A}}_{j,i}.
$$

 For example: 

$$
{\begin{bmatrix}1&2&3\\0&-6&7\end{bmatrix}}^{\mathrm {T} }={\begin{bmatrix}1&0\\2&-6\\3&7\end{bmatrix}}
$$

The transpose is compatible with addition and scalar multiplication, as expressed by (*c***A**)<sup>T</sup> = *c*(**A**<sup>T</sup>) and (**A** + **B**)<sup>T</sup> = **A**<sup>T</sup> + **B**<sup>T</sup>. Finally, (**A**<sup>T</sup>)<sup>T</sup> = **A**.

### Matrix multiplication

![[media/873a6e5bc76183500704bdffb590b9ed42cbe1c3.png]]
Schematic depiction of the matrix product <strong>AB</strong> of two matrices <strong>A</strong> and <strong>B</strong>

*Multiplication* of two matrices corresponds to the composition of [linear transformations](#Linear_transformations) represented by each matrix. It is defined if and only if the number of columns of the left matrix is the same as the number of rows of the right matrix. If **A** is an m × n matrix and **B** is an n × p matrix, then their *matrix product* **AB** is the m × p matrix whose entries are given by the [dot product](https://en.wikipedia.org/wiki/Dot_product) of the corresponding row of **A** and the corresponding column of **B**: 

$$
[\mathbf {AB} ]_{i,j}=a_{i,1}b_{1,j}+a_{i,2}b_{2,j}+\cdots +a_{i,n}b_{n,j}=\sum _{r=1}^{n}a_{i,r}b_{r,j},
$$

 where 1 ≤ *i* ≤ *m* and 1 ≤ *j* ≤ *p*. For example, the underlined entry 2340 in the product is calculated as (2 × 1000) + (3 × 100) + (4 × 10) = 2340: 

$$
{\begin{aligned}{\begin{bmatrix}{\underline {2}}&{\underline {3}}&{\underline {4}}\\1&0&0\\\end{bmatrix}}{\begin{bmatrix}0&{\underline {1000}}\\1&{\underline {100}}\\0&{\underline {10}}\\\end{bmatrix}}&={\begin{bmatrix}3&{\underline {2340}}\\0&1000\\\end{bmatrix}}.\end{aligned}}
$$

Matrix multiplication satisfies the rules (**AB**)**C** = **A**(**BC**) ([associativity](https://en.wikipedia.org/wiki/Associativity)), and (**A** + **B**)**C** = **AC** + **BC** as well as **C**(**A** + **B**) = **CA** + **CB** (left and right [distributivity](https://en.wikipedia.org/wiki/Distributivity)), whenever the size of the matrices is such that the various products are defined. The product **AB** may be defined without **BA** being defined, namely if **A** and **B** are m × n and n × k matrices, respectively, and *m* ≠ *k*. Even if both products are defined, they generally need not be equal, that is: 

$$
{\mathbf {AB}}\neq {\mathbf {BA}}.
$$

In other words, matrix multiplication is not [commutative](https://en.wikipedia.org/wiki/Commutative_property), in marked contrast to (rational, real, or complex) numbers, whose product is independent of the order of the factors. An example of two matrices not commuting with each other is: 

$$
{\begin{bmatrix}1&2\\3&4\\\end{bmatrix}}{\begin{bmatrix}0&1\\0&0\\\end{bmatrix}}={\begin{bmatrix}0&1\\0&3\\\end{bmatrix}},
$$

 whereas 

$$
{\begin{bmatrix}0&1\\0&0\\\end{bmatrix}}{\begin{bmatrix}1&2\\3&4\\\end{bmatrix}}={\begin{bmatrix}3&4\\0&0\\\end{bmatrix}}.
$$

Besides the ordinary matrix multiplication just described, other less frequently used operations on matrices that can be considered forms of multiplication also exist, such as the [Hadamard product](https://en.wikipedia.org/wiki/Hadamard_product_(matrices) "Hadamard product (matrices)") and the [[Kronecker Product]]. They arise in solving matrix equations such as the [Sylvester equation](https://en.wikipedia.org/wiki/Sylvester_equation).

### Row operations

There are three types of row operations:

1.  row addition, that is, adding a row to another.
2.  row multiplication, that is, multiplying all entries of a row by a non-zero constant;
3.  row switching, that is, interchanging two rows of a matrix;

These operations are used in several ways, including solving [linear equations](https://en.wikipedia.org/wiki/Linear_equation) and finding [matrix inverses](https://en.wikipedia.org/wiki/Matrix_inverse) with [Gauss elimination](https://en.wikipedia.org/wiki/Gauss_elimination) and Gauss–Jordan elimination, respectively.

### Submatrix 

A **submatrix** of a matrix is a matrix obtained by deleting any collection of rows or columns or both. For example, from the following 3 × 4 matrix, we can construct a 2 × 3 submatrix by removing row 3 and column 2: 

$$
\mathbf {A} ={\begin{bmatrix}1&\color {red}{2}&3&4\\5&\color {red}{6}&7&8\\\color {red}{9}&\color {red}{10}&\color {red}{11}&\color {red}{12}\end{bmatrix}}\rightarrow {\begin{bmatrix}1&3&4\\5&7&8\end{bmatrix}}.
$$

The [minors](https://en.wikipedia.org/wiki/Minor_(linear_algebra) "Minor (linear algebra)") and cofactors of a matrix are found by computing the [[Determinant]] of certain submatrices.

A **principal submatrix** is a square submatrix obtained by removing certain rows and columns. The definition varies from author to author. According to some authors, a principal submatrix is a submatrix in which the set of row indices that remain is the same as the set of column indices that remain. Other authors define a principal submatrix as one in which the first k rows and columns, for some number k, are the ones that remain; this type of submatrix has also been called a **leading principal submatrix**.

## Linear equations

Matrices can be used to compactly write and work with multiple linear equations, that is, systems of linear equations. For example, if **A** is an m × n matrix, **x** designates a column vector (that is, n × 1 matrix) of n variables *x*<sub>1</sub>, *x*<sub>2</sub>, ..., *x*<sub>*n*</sub>, and **b** is an m × 1 column vector, then the matrix equation 

$$
\mathbf {Ax} =\mathbf {b}
$$

 is equivalent to the system of linear equations 

$$
{\begin{aligned}a_{1,1}x_{1}+a_{1,2}x_{2}+&\cdots +a_{1,n}x_{n}=b_{1}\\&\ \ \vdots \\a_{m,1}x_{1}+a_{m,2}x_{2}+&\cdots +a_{m,n}x_{n}=b_{m}\end{aligned}}
$$

Using matrices, this can be solved more compactly than would be possible by writing out all the equations separately. If *n* = *m* and the equations are [independent](https://en.wikipedia.org/wiki/Independent_equation), then this can be done by writing 

$$
\mathbf {x} =\mathbf {A} ^{-1}\mathbf {b}
$$

 where **A**<sup>−1</sup> is the [[Inverse Matrix]] of **A**. If **A** has no inverse, solutions—if any—can be found using its [generalized inverse](https://en.wikipedia.org/wiki/Generalized_inverse).

## Linear transformations

![[media/05a176ff2958ba931438191d24db587970f12f36.png]]
The vectors represented by a 2 × 2 matrix correspond to the sides of a unit square transformed into a parallelogram.

Matrices and matrix multiplication reveal their essential features when related to *linear transformations*, also known as *linear maps*. A real m-by-n matrix **A** gives rise to a linear transformation $\mathbb {R} ^{n}\to \mathbb {R} ^{m}$ mapping each vector **x** in $\mathbb {R} ^{n}$ to the (matrix) product **Ax**, which is a vector in $\mathbb {R} ^{m}.$ Conversely, each linear transformation $f:\mathbb {R} ^{n}\to \mathbb {R} ^{m}$ arises from a unique m-by-n matrix **A**: explicitly, the (*i*, *j*)-entry of **A** is the ith coordinate of *f* (**e**<sub>*j*</sub>), where **e**<sub>*j*</sub> = (0, ..., 0, 1, 0, ..., 0) is the [unit vector](https://en.wikipedia.org/wiki/Unit_vector) with 1 in the jth position and 0 elsewhere. The matrix **A** is said to represent the linear map f, and **A** is called the *transformation matrix* of f.

For example, the 2 × 2 matrix 

$$
\mathbf {A} ={\begin{bmatrix}a&c\\b&d\end{bmatrix}}
$$

 can be viewed as the transform of the [unit square](https://en.wikipedia.org/wiki/Unit_square) into a [parallelogram](https://en.wikipedia.org/wiki/Parallelogram) with vertices at (0, 0), (*a*, *b*), (*a* + *c*, *b* + *d*), and (*c*, *d*). The parallelogram pictured at the right is obtained by multiplying **A** with each of the column vectors $\left[{\begin{smallmatrix}0\\0\end{smallmatrix}}\right]$, $\left[{\begin{smallmatrix}1\\0\end{smallmatrix}}\right]$, $\left[{\begin{smallmatrix}1\\1\end{smallmatrix}}\right]$, and $\left[{\begin{smallmatrix}0\\1\end{smallmatrix}}\right]$ in turn. These vectors define the vertices of the unit square. The following table shows several 2 × 2 real matrices with the associated linear maps of $\mathbb {R} ^{2}$. The blue original is mapped to the green grid and shapes. The origin (0, 0) is marked with a black point.

<table class="wikitable" style="text-align:center; margin:1em auto 1em auto;">

[Horizontal shear](https://en.wikipedia.org/wiki/Shear_mapping)<br />
with <em>m</em> = 1.25.
[Reflection](https://en.wikipedia.org/wiki/Reflection_(mathematics)) through the vertical axis
[Squeeze mapping](https://en.wikipedia.org/wiki/Squeeze_mapping)<br />
with <em>r</em> = 3/2
[Scaling](https://en.wikipedia.org/wiki/Scaling_(geometry))<br />
by a factor of 3/2
[Rotation](https://en.wikipedia.org/wiki/Rotation_matrix)<br />
by π/6 = 30°

${\begin{bmatrix}1&1.25\\0&1\end{bmatrix}}$
${\begin{bmatrix}-1&0\\0&1\end{bmatrix}}$
${\begin{bmatrix}{\frac {3}{2}}&0\\0&{\frac {2}{3}}\end{bmatrix}}$
${\begin{bmatrix}{\frac {3}{2}}&0\\0&{\frac {3}{2}}\end{bmatrix}}$
${\begin{bmatrix}\cos \left({\frac {\pi }{6}}\right)&-\sin \left({\frac {\pi }{6}}\right)\\\sin \left({\frac {\pi }{6}}\right)&\cos \left({\frac {\pi }{6}}\right)\end{bmatrix}}$

![[media/25c3f45bc7e9c979ba1665a6ddeb6bc9c529641c.png]]
![[media/d203465111111fcd7b2b433450c970e856604431.png]]
![[media/37aa4e4e50e37571c7cfeae0ad90167847adb3c8.png]]
![[media/0ee33afebd262723e4697d90ac84481058d0a12b.png]]
![[media/2d56d4684db2797e355708de93c75d321c914823.png]]

</table>

Under the [1-to-1 correspondence](https://en.wikipedia.org/wiki/Bijection) between matrices and linear maps, matrix multiplication corresponds to [composition](https://en.wikipedia.org/wiki/Function_composition) of maps: if a k-by-m matrix **B** represents another linear map $g:\mathbb {R} ^{m}\to \mathbb {R} ^{k}$, then the composition *g* ∘ *f* is represented by **BA** since 

$$
(g\circ f)({\mathbf {x}})=g(f({\mathbf {x}}))=g({\mathbf {Ax}})={\mathbf {B}}({\mathbf {Ax}})=({\mathbf {BA}}){\mathbf {x}}.
$$

The last equality follows from the above-mentioned associativity of matrix multiplication.

The [rank of a matrix](https://en.wikipedia.org/wiki/Rank_of_a_matrix) **A** is the maximum number of [[Linear Independence|linearly independent]] row vectors of the matrix, which is the same as the maximum number of linearly independent column vectors. Equivalently it is the [dimension](https://en.wikipedia.org/wiki/Hamel_dimension) of the [image](https://en.wikipedia.org/wiki/Image_(mathematics) "Image (mathematics)") of the linear map represented by **A**. The [rank–nullity theorem](https://en.wikipedia.org/wiki/Rank%E2%80%93nullity_theorem) states that the dimension of the [kernel](https://en.wikipedia.org/wiki/Kernel_(matrix)) of a matrix plus the rank equals the number of columns of the matrix.

## Square matrix

A [square matrix](https://en.wikipedia.org/wiki/Square_matrix) is a matrix with the same number of rows and columns. An n-by-n matrix is known as a square matrix of order n. Any two square matrices of the same order can be added and multiplied. The entries a<sub>ii</sub> form the [main diagonal](https://en.wikipedia.org/wiki/Main_diagonal) of a square matrix. They lie on the imaginary line running from the top left corner to the bottom right corner of the matrix.

Square matrices of a given dimension form a [noncommutative ring](https://en.wikipedia.org/wiki/Noncommutative_ring), which is one of the most common examples of a noncommutative ring.

### Main types

|  |  |
|----|----|
| Name | Example with *n* = 3 |
| [Diagonal matrix](https://en.wikipedia.org/wiki/Diagonal_matrix) | ${\begin{bmatrix}a_{11}&0&0\\0&a_{22}&0\\0&0&a_{33}\\\end{bmatrix}}$ |
| [Lower triangular matrix](https://en.wikipedia.org/wiki/Lower_triangular_matrix) | ${\begin{bmatrix}a_{11}&0&0\\a_{21}&a_{22}&0\\a_{31}&a_{32}&a_{33}\\\end{bmatrix}}$ |
| [Upper triangular matrix](https://en.wikipedia.org/wiki/Upper_triangular_matrix) | ${\begin{bmatrix}a_{11}&a_{12}&a_{13}\\0&a_{22}&a_{23}\\0&0&a_{33}\\\end{bmatrix}}$ |

#### Diagonal and triangular matrix

If all entries of **A** below the main diagonal are zero, **A** is called an *upper [triangular matrix](https://en.wikipedia.org/wiki/Triangular_matrix)*. Similarly, if all entries of **A** above the main diagonal are zero, **A** is called a *lower triangular matrix*. If all entries outside the main diagonal are zero, **A** is called a [diagonal matrix](https://en.wikipedia.org/wiki/Diagonal_matrix).

#### Identity matrix

The *identity matrix* **I**<sub>*n*</sub> of size n is the n-by-n matrix in which all the elements on the [main diagonal](https://en.wikipedia.org/wiki/Main_diagonal) are equal to 1 and all other elements are equal to 0, for example, 

$$
{\begin{aligned}\mathbf {I} _{1}&={\begin{bmatrix}1\end{bmatrix}},\\[4pt]\mathbf {I} _{2}&={\begin{bmatrix}1&0\\0&1\end{bmatrix}},\\[4pt]\vdots &\\[4pt]\mathbf {I} _{n}&={\begin{bmatrix}1&0&\cdots &0\\0&1&\cdots &0\\\vdots &\vdots &\ddots &\vdots \\0&0&\cdots &1\end{bmatrix}}\end{aligned}}
$$

 It is a square matrix of order n, and also a special kind of [diagonal matrix](https://en.wikipedia.org/wiki/Diagonal_matrix). It is called an identity matrix because multiplication with it leaves a matrix unchanged: 

$$
{\mathbf {AI}}_{n}={\mathbf {I}}_{m}{\mathbf {A}}={\mathbf {A}}
$$

 for any m-by-n matrix **A**.

A scalar multiple of an identity matrix is called a *scalar* matrix.

#### Symmetric or skew-symmetric matrix

A square matrix **A** that is equal to its transpose, that is, **A** = **A**<sup>T</sup>, is a [symmetric matrix](https://en.wikipedia.org/wiki/Symmetric_matrix). If instead, **A** is equal to the negative of its transpose, that is, **A** = −**A**<sup>T</sup>, then **A** is a [skew-symmetric matrix](https://en.wikipedia.org/wiki/Skew-symmetric_matrix). In complex matrices, symmetry is often replaced by the concept of [Hermitian matrices](https://en.wikipedia.org/wiki/Hermitian_matrix), which satisfies **A**<sup>∗</sup> = **A**, where the star or [asterisk](https://en.wikipedia.org/wiki/Asterisk) denotes the [conjugate transpose](https://en.wikipedia.org/wiki/Conjugate_transpose) of the matrix, that is, the transpose of the [complex conjugate](https://en.wikipedia.org/wiki/Complex_conjugate) of **A**.

By the [[Spectral Theorem]], real symmetric matrices and complex Hermitian matrices have an [eigenbasis](https://en.wikipedia.org/wiki/Eigenbasis); that is, every vector is expressible as a [linear combination](https://en.wikipedia.org/wiki/Linear_combination) of eigenvectors. In both cases, all eigenvalues are real. This theorem can be generalized to infinite-dimensional situations related to matrices with infinitely many rows and columns.

#### Invertible matrix and its inverse

A square matrix **A** is called *[invertible](https://en.wikipedia.org/wiki/Invertible_matrix)* or *non-singular* if there exists a matrix **B** such that 

$$
{\mathbf {AB}}={\mathbf {BA}}={\mathbf {I}}_{n},
$$

 where **I**<sub>*n*</sub> is the n × n [identity matrix](https://en.wikipedia.org/wiki/Identity_matrix) with 1 for each entry on the [main diagonal](https://en.wikipedia.org/wiki/Main_diagonal) and 0 elsewhere. If **B** exists, it is unique and is called the *[inverse matrix](https://en.wikipedia.org/wiki/Invertible_matrix)* of **A**, denoted **A**<sup>−1</sup>.

There are many [algorithms](https://en.wikipedia.org/wiki/Algorithm) for testing whether a square matrix is invertible, and, if it is, computing its inverse. One of the oldest, which is still in common use is [Gaussian elimination](https://en.wikipedia.org/wiki/Gaussian_elimination).

#### Definite matrix

<table class="wikitable" style="float:right; text-align:center; margin:0ex 0ex 2ex 2ex;">

[[Positive-Definite Matrix|Positive definite matrix]]
[Indefinite matrix](https://en.wikipedia.org/wiki/Indefinite_matrix)

&#10;
${\begin{bmatrix}{\frac {1}{4}}&0\\0&1\\\end{bmatrix}}$
${\begin{bmatrix}{\frac {1}{4}}&0\\0&-{\frac {1}{4}}\end{bmatrix}}$

$Q(x,y)={\frac {1}{4}}x^{2}+y^{2}$
$Q(x,y)={\frac {1}{4}}x^{2}-{\frac {1}{4}}y^{2}$

![[media/212d31a022030dbf96eee2e23e4657b9da367a7a.png]]<br />
Points such that $Q(x,y)=1$<br />
([Ellipse](https://en.wikipedia.org/wiki/Ellipse))
![[media/fe2079612677c5e1be4255ff23ff4f8e08b08915.png]]<br />
Points such that $Q(x,y)=1$<br />
([Hyperbola](https://en.wikipedia.org/wiki/Hyperbola))

</table>

A symmetric real matrix **A** is called [[Positive-Definite Matrix|positive-definite]] if the associated [quadratic form](https://en.wikipedia.org/wiki/Quadratic_form) 

$$
f({\mathbf {x}})={\mathbf {x}}^{\rm {T}}{\mathbf {Ax}}
$$

 has a positive value for every nonzero vector **x** in $\mathbb {R} ^{n}$. If *f*(**x**) yields only negative values then **A** is [negative-definite](https://en.wikipedia.org/wiki/Definiteness_of_a_matrix#Negative_definite); if f does produce both negative and positive values then **A** is [indefinite](https://en.wikipedia.org/wiki/Definiteness_of_a_matrix#Indefinite). If the quadratic form f yields only non-negative values (positive or zero), the symmetric matrix is called *positive-semidefinite* (or if only non-positive values, then negative-semidefinite); hence the matrix is indefinite precisely when it is neither positive-semidefinite nor negative-semidefinite.

A symmetric matrix is positive-definite if and only if all its eigenvalues are positive, that is, the matrix is positive-semidefinite and it is invertible. The table at the right shows two possibilities for 2-by-2 matrices. The eigenvalues of a diagonal matrix are simply the entries along the diagonal, and so in these examples, the eigenvalues can be read directly from the matrices themselves. The first matrix has two eigenvalues that are both positive, while the second has one that is positive and another that is negative.

Allowing as input two different vectors instead yields the [bilinear form](https://en.wikipedia.org/wiki/Bilinear_form) associated to **A**: 

$$
B_{\mathbf {A}}({\mathbf {x}},{\mathbf {y}})={\mathbf {x}}^{\rm {T}}{\mathbf {Ay}}.
$$

In the case of complex matrices, the same terminology and results apply, with *symmetric matrix*, *quadratic form*, *bilinear form*, and *transpose* **x**<sup>T</sup> replaced respectively by [Hermitian matrix](https://en.wikipedia.org/wiki/Hermitian_matrix), [Hermitian form](https://en.wikipedia.org/wiki/Hermitian_form), [sesquilinear form](https://en.wikipedia.org/wiki/Sesquilinear_form), and [conjugate transpose](https://en.wikipedia.org/wiki/Conjugate_transpose) **x**<sup>H</sup>.

#### Orthogonal matrix

An *orthogonal matrix* is a square matrix with [real](https://en.wikipedia.org/wiki/Real_number) entries whose columns and rows are [orthogonal](https://en.wikipedia.org/wiki/Orthogonal) [unit vectors](https://en.wikipedia.org/wiki/Unit_vector) (that is, [orthonormal](https://en.wikipedia.org/wiki/Orthonormality) vectors). Equivalently, a matrix **A** is orthogonal if its [transpose](https://en.wikipedia.org/wiki/Transpose) is equal to its [inverse](https://en.wikipedia.org/wiki/Invertible_matrix): 

$$
\mathbf {A} ^{\mathrm {T} }=\mathbf {A} ^{-1},\,
$$

 which entails 

$$
\mathbf {A} ^{\mathrm {T} }\mathbf {A} =\mathbf {A} \mathbf {A} ^{\mathrm {T} }=\mathbf {I} _{n},
$$

 where **I**<sub>*n*</sub> is the [identity matrix](https://en.wikipedia.org/wiki/Identity_matrix) of size n.

An orthogonal matrix **A** is necessarily [invertible](https://en.wikipedia.org/wiki/Invertible_matrix) (with inverse **A**<sup>−1</sup> = **A**<sup>T</sup>), [unitary](https://en.wikipedia.org/wiki/Unitary_matrix) (**A**<sup>−1</sup> = **A**\*), and [normal](https://en.wikipedia.org/wiki/Normal_matrix) (**A**\***A** = **AA**\*). The [[Determinant]] of any orthogonal matrix is either +1 or −1. A *special orthogonal matrix* is an orthogonal matrix with [[Determinant]] +1. As a [[Linear Transformation]], every orthogonal matrix with determinant +1 is a pure [rotation](https://en.wikipedia.org/wiki/Rotation_(mathematics) "Rotation (mathematics)") without reflection, i.e., the transformation preserves the orientation of the transformed structure, while every orthogonal matrix with determinant −1 reverses the orientation, i.e., is a composition of a pure [reflection](https://en.wikipedia.org/wiki/Reflection_(mathematics) "Reflection (mathematics)") and a (possibly null) rotation. The identity matrices have determinant 1 and are pure rotations by an angle zero.

The [complex](https://en.wikipedia.org/wiki/Complex_number) analog of an orthogonal matrix is a [unitary matrix](https://en.wikipedia.org/wiki/Unitary_matrix).

### Main operations

#### Trace

The [trace](https://en.wikipedia.org/wiki/Trace_of_a_matrix), tr(**A**) of a square matrix **A** is the sum of its diagonal entries. While matrix multiplication is not commutative as mentioned [above](#_noncommutative), the trace of the product of two matrices is independent of the order of the factors: 

$$
\operatorname {tr} (\mathbf {AB} )=\operatorname {tr} (\mathbf {BA} ).
$$

 This is immediate from the definition of matrix multiplication: 

$$
\operatorname {tr} (\mathbf {AB} )=\sum _{i=1}^{m}\sum _{j=1}^{n}a_{ij}b_{ji}=\operatorname {tr} (\mathbf {BA} ).
$$

 It follows that the trace of the product of more than two matrices is independent of [cyclic permutations](https://en.wikipedia.org/wiki/Cyclic_permutation) of the matrices; however, this does not in general apply for arbitrary permutations. For example, tr(**ABC**) ≠ tr(**BAC**), in general. Also, the trace of a matrix is equal to that of its transpose, that is, 

$$
\operatorname {tr} ({\mathbf {A}})=\operatorname {tr} ({\mathbf {A}}^{\rm {T}}).
$$

#### Determinant

![[media/cb6ddef44011add4b3205fc87e28293e1a23cade.png]]
A linear transformation on $\mathbb {R} ^{2}$ given by the indicated matrix. The determinant of this matrix is −1, as the area of the green parallelogram at the right is 1, but the map reverses the [orientation](https://en.wikipedia.org/wiki/Orientation_(mathematics)), since it turns the counterclockwise orientation of the vectors to a clockwise one.

The *determinant* of a square matrix **A** (denoted det(**A**) or \|**A**\|) is a number encoding certain properties of the matrix. A matrix is invertible [if and only if](https://en.wikipedia.org/wiki/If_and_only_if) its determinant is nonzero. Its [absolute value](https://en.wikipedia.org/wiki/Absolute_value) equals the area (in $\mathbb {R} ^{2}$) or volume (in $\mathbb {R} ^{3}$) of the image of the unit square (or cube), while its sign corresponds to the orientation of the corresponding linear map: the determinant is positive if and only if the orientation is preserved.

The determinant of 2 × 2 matrices is given by 

$$
\det {\begin{bmatrix}a&b\\c&d\end{bmatrix}}=ad-bc.
$$

 The determinant of 3 × 3 matrices involves six terms ([rule of Sarrus](https://en.wikipedia.org/wiki/Rule_of_Sarrus)). The more lengthy [Leibniz formula](https://en.wikipedia.org/wiki/Leibniz_formula_for_determinants) generalizes these two formulae to all dimensions.

The determinant of a product of square matrices equals the product of their determinants: 

$$
\det({\mathbf {AB}})=\det({\mathbf {A}})\cdot \det({\mathbf {B}}),
$$

 or using alternate notation: 

$$
|{\mathbf {AB}}|=|{\mathbf {A}}|\cdot |{\mathbf {B}}|.
$$

 Adding a multiple of any row to another row, or a multiple of any column to another column, does not change the determinant. Interchanging two rows or two columns affects the determinant by multiplying it by −1. Using these operations, any matrix can be transformed to a lower (or upper) triangular matrix, and for such matrices, the determinant equals the product of the entries on the main diagonal; this provides a method to calculate the determinant of any matrix. Finally, the [Laplace expansion](https://en.wikipedia.org/wiki/Laplace_expansion) expresses the determinant in terms of [minors](https://en.wikipedia.org/wiki/Minor_(linear_algebra) "Minor (linear algebra)"), that is, determinants of smaller matrices. This expansion can be used for a recursive definition of determinants (taking as starting case the determinant of a 1 × 1 matrix, which is its unique entry, or even the determinant of a 0 × 0 matrix, which is 1), that can be seen to be equivalent to the Leibniz formula. Determinants can be used to solve [linear systems](https://en.wikipedia.org/wiki/Linear_system) using [Cramer's rule](https://en.wikipedia.org/wiki/Cramer%27s_rule), where the division of the determinants of two related square matrices equates to the value of each of the system's variables.

#### Eigenvalues and eigenvectors

A number $\lambda$ and a nonzero vector **v** satisfying 

$$
\mathbf {A} \mathbf {v} =\lambda \mathbf {v}
$$

 are called an *eigenvalue* and an *eigenvector* of **A**, respectively. The number λ is an eigenvalue of an n × n matrix **A** if and only if (**A** − *λ***I**<sub>*n*</sub>) is not invertible, which is [equivalent](https://en.wikipedia.org/wiki/Logical_equivalence) to $\det(\mathbf {A} -\lambda \mathbf {I} )=0.$ The polynomial *p*<sub>**A**</sub> in an [indeterminate](https://en.wikipedia.org/wiki/Indeterminate_(variable)) X given by evaluation of the determinant det(*X***I**<sub>*n*</sub> − **A**) is called the [characteristic polynomial](https://en.wikipedia.org/wiki/Characteristic_polynomial) of **A**. It is a [monic polynomial](https://en.wikipedia.org/wiki/Monic_polynomial) of [degree](https://en.wikipedia.org/wiki/Degree_of_a_polynomial) n. Therefore the polynomial equation *p*<sub>**A**</sub>(*λ*) = 0 has at most n different solutions, that is, eigenvalues of the matrix. They may be complex even if the entries of **A** are real. According to the [Cayley–Hamilton theorem](https://en.wikipedia.org/wiki/Cayley%E2%80%93Hamilton_theorem), *p*<sub>**A**</sub>(**A**) = **0**, that is, the result of substituting the matrix itself into its characteristic polynomial yields the [zero matrix](https://en.wikipedia.org/wiki/Zero_matrix).

## Computational aspects

Matrix calculations can be often performed with different techniques. Many problems can be solved by both direct algorithms and iterative approaches. For example, the eigenvectors of a square matrix can be obtained by finding a [sequence](https://en.wikipedia.org/wiki/Sequence_(mathematics)) of vectors **x**<sub>*n*</sub> [converging](https://en.wikipedia.org/wiki/Limit_of_a_sequence) to an eigenvector when n tends to [infinity](https://en.wikipedia.org/wiki/Infinity).

To choose the most appropriate algorithm for each specific problem, it is important to determine both the effectiveness and precision of all the available algorithms. The domain studying these matters is called [numerical linear algebra](https://en.wikipedia.org/wiki/Numerical_linear_algebra). As with other numerical situations, two main aspects are the [complexity](https://en.wikipedia.org/wiki/Complexity_analysis) of algorithms and their [[Numerical Stability]].

Determining the complexity of an algorithm means finding [upper bounds](https://en.wikipedia.org/wiki/Upper_bound) or estimates of how many elementary operations such as additions and multiplications of scalars are necessary to perform some algorithm, for example, multiplication of matrices. Calculating the matrix product of two n-by-n matrices using the definition given above needs *n*<sup>3</sup> multiplications, since for any of the *n*<sup>2</sup> entries of the product, n multiplications are necessary. The [Strassen algorithm](https://en.wikipedia.org/wiki/Strassen_algorithm) outperforms this "naive" algorithm; it needs only *n*<sup>2.807</sup> multiplications. Theoretically faster but impractical [matrix multiplication algorithms](https://en.wikipedia.org/wiki/Matrix_multiplication_algorithm) have been developed, as have speedups to this problem using [parallel algorithms](https://en.wikipedia.org/wiki/Parallel_algorithm) or [distributed computation](https://en.wikipedia.org/wiki/Distributed_computation) systems such as [MapReduce](https://en.wikipedia.org/wiki/MapReduce).

In many practical situations, additional information about the matrices involved is known. An important case concerns [sparse matrices](https://en.wikipedia.org/wiki/Sparse_matrix), that is, matrices whose entries are mostly zero. There are specifically adapted algorithms for, say, solving linear systems **Ax** = **b** for sparse matrices **A**, such as the [[Conjugate Gradient Method]].

An algorithm is, roughly speaking, numerically stable if little deviations in the input values do not lead to big deviations in the result. For example, one can calculate the inverse of a matrix by computing its [adjugate matrix](https://en.wikipedia.org/wiki/Adjugate_matrix): 

$$
{\mathbf {A}}^{-1}=\operatorname {adj} ({\mathbf {A}})/\det({\mathbf {A}}).
$$

 However, this may lead to significant rounding errors if the determinant of the matrix is very small. The [norm of a matrix](https://en.wikipedia.org/wiki/Matrix_norm) can be used to capture the [[Condition Number|conditioning]] of linear algebraic problems, such as computing a matrix's inverse.

## Decomposition

There are several methods to render matrices into a more easily accessible form. They are generally referred to as *matrix decomposition* or *matrix factorization* techniques. These techniques are of interest because they can make computations easier.

The [[LU Decomposition]] factors matrices as a product of lower (**L**) and an upper [triangular matrices](https://en.wikipedia.org/wiki/Triangular_matrix) (**U**). Once this decomposition is calculated, linear systems can be solved more efficiently by a simple technique called [forward and back substitution](https://en.wikipedia.org/wiki/Forward_substitution). Likewise, inverses of triangular matrices are algorithmically easier to calculate. The *Gaussian elimination* is a similar algorithm; it transforms any matrix to [row echelon form](https://en.wikipedia.org/wiki/Row_echelon_form). Both methods proceed by multiplying the matrix by suitable [elementary matrices](https://en.wikipedia.org/wiki/Elementary_matrix), which correspond to [permuting rows or columns](https://en.wikipedia.org/wiki/Permutation_matrix) and adding multiples of one row to another row. [[Singular Value Decomposition]] (SVD) expresses any matrix **A** as a product **UDV**<sup>∗</sup>, where **U** and **V** are [unitary matrices](https://en.wikipedia.org/wiki/Unitary_matrix) and **D** is a diagonal matrix.

![[media/a20c1ace09b97919eec6fd582bae285b63c841a4.png]]
An example of a matrix in Jordan normal form. The grey blocks are called Jordan blocks.

The [[Eigendecomposition]] or *diagonalization* expresses **A** as a product **VDV**<sup>−1</sup>, where **D** is a diagonal matrix and **V** is a suitable invertible matrix. If **A** can be written in this form, it is called [diagonalizable](https://en.wikipedia.org/wiki/Diagonalizable_matrix). More generally, and applicable to all matrices, the Jordan decomposition transforms a matrix into [Jordan normal form](https://en.wikipedia.org/wiki/Jordan_normal_form), that is to say matrices whose only nonzero entries are the eigenvalues *λ*<sub>1</sub> to λ<sub>n</sub> of **A**, placed on the main diagonal and possibly entries equal to one directly above the main diagonal, as shown at the right. Given the eigendecomposition, the nth power of **A** (that is, n-fold iterated matrix multiplication) can be calculated via 

$$
{\mathbf {A}}^{n}=({\mathbf {VDV}}^{-1})^{n}={\mathbf {VDV}}^{-1}{\mathbf {VDV}}^{-1}\ldots {\mathbf {VDV}}^{-1}={\mathbf {VD}}^{n}{\mathbf {V}}^{-1}
$$

 and the power of a diagonal matrix can be calculated by taking the corresponding powers of the diagonal entries, which is much easier than doing the exponentiation for **A** instead. This can be used to compute the [matrix exponential](https://en.wikipedia.org/wiki/Matrix_exponential) *e*<sup>**A**</sup>, a need frequently arising in solving [linear differential equations](https://en.wikipedia.org/wiki/Linear_differential_equation), [matrix logarithms](https://en.wikipedia.org/wiki/Matrix_logarithm) and [square roots of matrices](https://en.wikipedia.org/wiki/Square_root_of_a_matrix). To avoid numerically [[Condition Number|ill-conditioned]] situations, further algorithms such as the [Schur decomposition](https://en.wikipedia.org/wiki/Schur_decomposition) can be employed.

## Abstract algebraic aspects and generalizations

Matrices can be generalized in different ways. Abstract algebra uses matrices with entries in more general [fields](https://en.wikipedia.org/wiki/Field_(mathematics) "Field (mathematics)") or even [rings](https://en.wikipedia.org/wiki/Ring_(mathematics) "Ring (mathematics)"), while linear algebra codifies properties of matrices in the notion of linear maps. It is possible to consider matrices with infinitely many columns and rows. Another extension is [tensors](https://en.wikipedia.org/wiki/Tensor), which can be seen as higher-dimensional arrays of numbers, as opposed to vectors, which can often be realized as sequences of numbers, while matrices are rectangular or two-dimensional arrays of numbers. Matrices, subject to certain requirements tend to form [groups](https://en.wikipedia.org/wiki/Group_(mathematics) "Group (mathematics)") known as matrix groups. Similarly under certain conditions matrices form [rings](https://en.wikipedia.org/wiki/Ring_(mathematics) "Ring (mathematics)") known as [matrix rings](https://en.wikipedia.org/wiki/Matrix_ring). Though the product of matrices is not in general commutative, certain matrices form [fields](https://en.wikipedia.org/wiki/Field_(mathematics) "Field (mathematics)") sometimes called matrix fields. (However the term "matrix field" is ambiguous, also referring to certain forms of physical [fields](https://en.wikipedia.org/wiki/Field_(physics) "Field (physics)") that continuously map points of some space to matrices.) In general, matrices over any ring and their [[Matrix Multiplication|multiplication]] can be represented as the arrows and composition of arrows in a [category](https://en.wikipedia.org/wiki/Category_(mathematics) "Category (mathematics)"), the [category of matrices](https://en.wikipedia.org/wiki/Category_of_matrices) over that ring. The objects of this category are natural numbers, representing the dimensions of the matrices.

### Matrices with entries in a field or ring

This article focuses on matrices whose entries are real or complex numbers. However, matrices can be considered with much more general types of entries than real or complex numbers. As a first step of generalization, any [field](https://en.wikipedia.org/wiki/Field_(mathematics) "Field (mathematics)"), that is, a [set](https://en.wikipedia.org/wiki/Set_(mathematics) "Set (mathematics)") where [addition](https://en.wikipedia.org/wiki/Addition), [subtraction](https://en.wikipedia.org/wiki/Subtraction), [multiplication](https://en.wikipedia.org/wiki/Multiplication), and [division](https://en.wikipedia.org/wiki/Division_(mathematics) "Division (mathematics)") operations are defined and well-behaved, may be used instead of $\mathbb {R}$ or $\mathbb {C}$, for example [rational numbers](https://en.wikipedia.org/wiki/Rational_number) or [finite fields](https://en.wikipedia.org/wiki/Finite_field). For example, [coding theory](https://en.wikipedia.org/wiki/Coding_theory) makes use of matrices over finite fields. Wherever [eigenvalues](https://en.wikipedia.org/wiki/Eigenvalue) are considered, as these are roots of a polynomial, they may exist only in a larger field than that of the entries of the matrix. For instance, they may be complex in the case of a matrix with real entries. The possibility to reinterpret the entries of a matrix as elements of a larger field (for example, to view a real matrix as a complex matrix whose entries happen to be all real) then allows considering each square matrix to possess a full set of eigenvalues. Alternatively one can consider only matrices with entries in an [algebraically closed field](https://en.wikipedia.org/wiki/Algebraically_closed_field), such as $\mathbb {C} ,$ from the outset.

Matrices whose entries are [polynomials](https://en.wikipedia.org/wiki/Polynomial), and more generally, matrices with entries in a [ring](https://en.wikipedia.org/wiki/Ring_(mathematics) "Ring (mathematics)") R are widely used in mathematics. Rings are a more general notion than fields in that a division operation need not exist. The very same addition and multiplication operations of matrices extend to this setting, too. The set M(*n*, *R*) (also denoted M<sub>*n*</sub>(R)) of all square n-by-n matrices over R is a ring called [matrix ring](https://en.wikipedia.org/wiki/Matrix_ring), isomorphic to the [endomorphism ring](https://en.wikipedia.org/wiki/Endomorphism_ring) of the left R-[module](https://en.wikipedia.org/wiki/Module_(mathematics) "Module (mathematics)") R<sup>n</sup>. If the ring R is [commutative](https://en.wikipedia.org/wiki/Commutative_ring), that is, its multiplication is commutative, then the ring M(*n*, *R*) is also an [associative algebra](https://en.wikipedia.org/wiki/Associative_algebra) over *R*. The [[Determinant]] of square matrices over a commutative ring R can still be defined using the [Leibniz formula](https://en.wikipedia.org/wiki/Leibniz_formula_(determinant)); such a matrix is invertible if and only if its determinant is [invertible](https://en.wikipedia.org/wiki/Invertible) in R, generalizing the situation over a field F, where every nonzero element is invertible. Matrices over [superrings](https://en.wikipedia.org/wiki/Superring) are called [supermatrices](https://en.wikipedia.org/wiki/Supermatrix).

Matrices do not always have all their entries in the same ring – or even in any ring at all. One special but common case is [block matrices](https://en.wikipedia.org/wiki/Block_matrix), which may be considered as matrices whose entries themselves are matrices. The entries need not be square matrices, and thus need not be members of any [ring](https://en.wikipedia.org/wiki/Ring_(mathematics) "Ring (mathematics)"); but in order to multiply them, their sizes must fulfill certain conditions: each pair of submatrices that are multiplied in forming the overall product must have compatible sizes.

### Relationship to linear maps

Linear maps $\mathbb {R} ^{n}\to \mathbb {R} ^{m}$ are equivalent to m-by-n matrices, as described [above](#linear_maps). More generally, any linear map *f* : *V* → *W* between finite-[dimensional](https://en.wikipedia.org/wiki/Hamel_dimension) [[Vector Space|vector spaces]] can be described by a matrix **A** = (*a<sub>ij</sub>*), after choosing [bases](https://en.wikipedia.org/wiki/Basis_(linear_algebra) "Basis (linear algebra)") **v**<sub>1</sub>, ..., **v**<sub>*n*</sub> of V, and **w**<sub>1</sub>, ..., **w**<sub>*m*</sub> of W (so n is the dimension of V and m is the dimension of W), which is such that 

$$
f(\mathbf {v} _{j})=\sum _{i=1}^{m}a_{i,j}\mathbf {w} _{i}\qquad {\mbox{for}}\ j=1,\ldots ,n.
$$

 In other words, column j of **A** expresses the image of **v**<sub>*j*</sub> in terms of the basis vectors **w**<sub>*i*</sub> of W; thus this relation uniquely determines the entries of the matrix **A**. The matrix depends on the choice of the bases: different choices of bases give rise to different, but [equivalent matrices](https://en.wikipedia.org/wiki/Matrix_equivalence). Many of the above concrete notions can be reinterpreted in this light, for example, the transpose matrix **A**<sup>T</sup> describes the [transpose of the linear map](https://en.wikipedia.org/wiki/Transpose_of_a_linear_map) given by **A**, concerning the [dual bases](https://en.wikipedia.org/wiki/Dual_space).

These properties can be restated more naturally: the [category of matrices](https://en.wikipedia.org/wiki/Category_of_matrices) with entries in a field $k$ with multiplication as composition is [equivalent](https://en.wikipedia.org/wiki/Equivalence_of_categories) to the category of finite-dimensional [[Vector Space|vector spaces]] and linear maps over this field.

More generally, the set of m × n matrices can be used to represent the R-linear maps between the free modules R<sup>m</sup> and R<sup>n</sup> for an arbitrary ring R with unity. When *n* = *m* composition of these maps is possible, and this gives rise to the [matrix ring](https://en.wikipedia.org/wiki/Matrix_ring) of n × n matrices representing the [endomorphism ring](https://en.wikipedia.org/wiki/Endomorphism_ring) of R<sup>n</sup>.

### Matrix groups

A [group](https://en.wikipedia.org/wiki/Group_(mathematics) "Group (mathematics)") is a mathematical structure consisting of a set of objects together with a [binary operation](https://en.wikipedia.org/wiki/Binary_operation), that is, an operation combining any two objects to a third, subject to certain requirements. A group in which the objects are [invertible](https://en.wikipedia.org/wiki/Invertible_matrix) $n\times n$ matrices and the group operation is matrix multiplication is called a *matrix group* of degree $n$. Every such matrix group is a [subgroup](https://en.wikipedia.org/wiki/Subgroup) of (that is, a smaller group contained within) the group of *all* invertible $n\times n$ matrices, the [general linear group](https://en.wikipedia.org/wiki/General_linear_group) of degree $n$.

Any property of square matrices that is preserved under matrix products and inverses can be used to define a matrix group. For example, the set of all $n\times n$ matrices whose determinant is 1 form a group called the [special linear group](https://en.wikipedia.org/wiki/Special_linear_group) of degree $n$. The set of [orthogonal matrices](https://en.wikipedia.org/wiki/Orthogonal_matrices), determined by the condition 

$$
{\mathbf {M}}^{\rm {T}}{\mathbf {M}}={\mathbf {I}},
$$

 form the [orthogonal group](https://en.wikipedia.org/wiki/Orthogonal_group). Every orthogonal matrix has [[Determinant]] 1 or −1. Orthogonal matrices with determinant 1 form a group called the *special orthogonal group*.

Every [finite group](https://en.wikipedia.org/wiki/Finite_group) is [isomorphic](https://en.wikipedia.org/wiki/Isomorphic) to a matrix group, as one can see by considering the [regular representation](https://en.wikipedia.org/wiki/Regular_representation) of the [symmetric group](https://en.wikipedia.org/wiki/Symmetric_group). General groups can be studied using matrix groups, which are comparatively well understood, using [representation theory](https://en.wikipedia.org/wiki/Representation_theory).

### Infinite matrices

It is also possible to consider matrices with infinitely many rows and columns. The basic operations introduced above are defined the same way in this case. Matrix multiplication, however, and all operations stemming therefrom are only meaningful when restricted to certain matrices, since the [sum featuring in the above definition](#matrix_product) of the matrix product will contain an infinity of summands. An easy way to circumvent this issue is to restrict to *finitary matrices* all of whose rows (or columns) contain only finitely many nonzero terms. As in the finite case (see [above](#linear_maps)), where matrices describe linear maps, infinite matrices can be used to describe [operators on Hilbert spaces](https://en.wikipedia.org/wiki/Hilbert_space#Operators_on_Hilbert_spaces), where convergence and [continuity](https://en.wikipedia.org/wiki/Continuous_function) questions arise. However, the explicit point of view of matrices tends to obfuscate the matter, and the abstract and more powerful tools of [functional analysis](https://en.wikipedia.org/wiki/Functional_analysis) are used instead, by relating matrices to linear maps (as in the finite case [above](#linear_maps)), but imposing additional convergence and continuity constraints.

### Empty matrix

An *empty matrix* is a matrix in which the number of rows or columns (or both) is zero. Empty matrices can be a useful [base case](https://en.wikipedia.org/wiki/Base_case_(recursion)) for certain [recursive](https://en.wikipedia.org/wiki/Recursion) constructions, and can help to deal with maps involving the [zero vector space](https://en.wikipedia.org/wiki/Zero_vector_space). For example, if **A** is a 3 × 0 matrix and **B** is a 0 × 3 matrix, then **AB** is the 3 × 3 [zero matrix](https://en.wikipedia.org/wiki/Zero_matrix) corresponding to the null map from a 3-dimensional space V to itself, while **BA** is a 0 × 0 matrix. There is no common notation for empty matrices, but most [computer algebra systems](https://en.wikipedia.org/wiki/Computer_algebra_system) allow creating and computing with them. The determinant of the 0 × 0 matrix is conventionally defined to be 1, consistent with the [empty product](https://en.wikipedia.org/wiki/Empty_product) occurring in the Leibniz formula for the determinant. This value is also needed for consistency with the 2 × 2 case of the [Desnanot–Jacobi identity](https://en.wikipedia.org/wiki/Desnanot%E2%80%93Jacobi_identity) relating determinants to the determinants of smaller matrices.

### Matrices with entries in a semiring

A [semiring](https://en.wikipedia.org/wiki/Semiring) is similar to a ring, but elements need not have [additive inverses](https://en.wikipedia.org/wiki/Additive_inverse), therefore one cannot do subtraction freely there. The definition of addition and multiplication of matrices with entries in a ring applies to matrices with entries in a semiring without modification. Matrices of fixed size with entries in a semiring form a [commutative monoid](https://en.wikipedia.org/wiki/Commutative_monoid) $\operatorname {Mat} (m,n;R)$ under addition. Square matrices of fixed size with entries in a semiring form a semiring $\operatorname {Mat} (n;R)$ under addition and multiplication.

The determinant of an n × n square matrix $M$ with entries in a [commutative semiring](https://en.wikipedia.org/wiki/Commutative_semiring) $R$ cannot be defined in general because the definition would involve additive inverses of semiring elements. What plays its role instead is the pair of positive and negative determinants

$\det \nolimits _{+}M=\sum _{\sigma \in \operatorname {Alt} (n)}M_{1\sigma (1)}\cdots M_{n\sigma (n)}$

$\det \nolimits _{-}M=\sum _{\sigma \in \operatorname {Sym} (n)\setminus \operatorname {Alt} (n)}M_{1\sigma (1)}\cdots M_{n\sigma (n)}$

where the sums are taken over [even permutations](https://en.wikipedia.org/wiki/Even_permutation) and odd permutations, respectively.

### Matrices with entries in a category

Matrices and their multiplication can be defined with entries objects of a [category](https://en.wikipedia.org/wiki/Category_(mathematics) "Category (mathematics)") equipped with a "[tensor product](https://en.wikipedia.org/wiki/Monoidal_category)" similar to multiplication in a ring, having [coproducts](https://en.wikipedia.org/wiki/Coproduct) similar to addition in a ring, in that the former is [distributive](https://en.wikipedia.org/wiki/Distributive_property) over the latter. However, the multiplication thus defined may be only associative in a sense weaker than usual. These are part of a bigger structure called the *bicategory of matrices*. The complete description of the above summary for interested readers follows.

Let $({\mathcal {C}},\otimes ,I)$ be a [monoidal category](https://en.wikipedia.org/wiki/Monoidal_category) satisfying the following two conditions:

- All (small) [coproducts](https://en.wikipedia.org/wiki/Coproduct) exist; in particular, let $\varnothing$ be an [initial object](https://en.wikipedia.org/wiki/Initial_object).
- The functor $\otimes$ is distributive over coproducts; i.e., for all object $X$ and a family of objects $(Y_{i})_{i\in I}$ in ${\mathcal {C}}$, the canonical ${\mathcal {C}}$-morphisms 

$$
\coprod _{i\in I}(X\otimes Y_{i})\to X\otimes \coprod _{i\in I}Y_{i}
$$

$$
\coprod _{i\in I}(Y_{i}\otimes X)\to \left(\coprod _{i\in I}Y_{i}\right)\otimes X
$$

 are [isomorphisms](https://en.wikipedia.org/wiki/Isomorphism). In particular, the canonical morphisms $\varnothing \to X\otimes \varnothing$ and $\varnothing \to \varnothing \otimes X$ are isomorphisms.

Then, the [bicategory](https://en.wikipedia.org/wiki/Bicategory) of ${\mathcal {C}}$-matrices $\operatorname {Mat} ({\mathcal {C}})$ is as follows:

- The objects are the sets.
- A [1-morphism](https://en.wikipedia.org/wiki/1-morphism) $M\colon A\to B$ is a map $M\colon A\times B\to \operatorname {Ob} ({\mathcal {C}})$; this is just a matrix over ${\mathcal {C}}$.
  - The composition of 1-morphisms $M\colon A\to B$ and $N\colon B\to C$, which can be understood as matrix multiplication, is 

$$
(N\circ M)(a,c)=\coprod _{b\in B}M(a,b)\otimes N(b,c).
$$

  - The identity 1-morphism on $A$ is 

$$
\operatorname {id} _{A}(a,b)={\begin{cases}I&a=b\\\varnothing &a\neq b\end{cases}}.
$$

- A 2-morphism between 1-morphisms $M,N\colon A\to B$ is a family of ${\mathcal {C}}$-morphisms $(f_{ab}\colon M(a,b)\to N(a,b))_{(a,b)\in A\times B}$. The definition of vertical and horizontal composition of 2-morphisms is natural: the vertical composition is componentwise composition of ${\mathcal {C}}$-morphisms; the horizontal composition is that derived from the functoriality of $\otimes$ and the [universal property](https://en.wikipedia.org/wiki/Universal_property) of coproducts.

In general, the bicategory of matrices need not be a strict [2-category](https://en.wikipedia.org/wiki/2-category). For example, the composition of 1-morphisms may not be associative in the usual strict sense, but only up to [coherent](https://en.wikipedia.org/wiki/Coherency_(homotopy_theory) "Coherency (homotopy theory)") isomorphism.

## Applications

There are numerous applications of matrices, both in mathematics and other sciences. Some of them merely take advantage of the compact representation of a set of numbers in a matrix. For example, [Text mining](https://en.wikipedia.org/wiki/Text_mining) and automated [thesaurus](https://en.wikipedia.org/wiki/Thesaurus) compilation makes use of [document-term matrices](https://en.wikipedia.org/wiki/Document-term_matrix) such as [tf-idf](https://en.wikipedia.org/wiki/Tf-idf) to track frequencies of certain words in several documents.

Complex numbers can be represented by particular real 2-by-2 matrices via 

$$
a+ib\leftrightarrow {\begin{bmatrix}a&-b\\b&a\end{bmatrix}},
$$

 under which addition and multiplication of complex numbers and matrices correspond to each other. For example, 2-by-2 rotation matrices represent the multiplication with some complex number of [absolute value](https://en.wikipedia.org/wiki/Absolute_value) 1, as [above](#rotation_matrix). A similar interpretation is possible for [quaternions](https://en.wikipedia.org/wiki/Quaternion) and [Clifford algebras](https://en.wikipedia.org/wiki/Clifford_algebra) in general.

In [game theory](https://en.wikipedia.org/wiki/Game_theory) and [economics](https://en.wikipedia.org/wiki/Economics), the [payoff matrix](https://en.wikipedia.org/wiki/Payoff_matrix) encodes the payoff for two players, depending on which out of a given (finite) set of strategies the players choose. The expected outcome of the game, when both players play [mixed strategies](https://en.wikipedia.org/wiki/Mixed_strategy), is obtained by multiplying this matrix on both sides by vectors representing the strategies. The [minimax theorem](https://en.wikipedia.org/wiki/Minimax_theorem) central to game theory is closely related to the [duality theory of linear programs](https://en.wikipedia.org/wiki/Dual_linear_program), which are often formulated in terms of matrix-vector products.

Early [encryption](https://en.wikipedia.org/wiki/Encryption) techniques such as the [Hill cipher](https://en.wikipedia.org/wiki/Hill_cipher) also used matrices. However, due to the linear nature of matrices, these codes are comparatively easy to break. [Computer graphics](https://en.wikipedia.org/wiki/Computer_graphics) uses matrices to represent objects; to calculate transformations of objects using affine [rotation matrices](https://en.wikipedia.org/wiki/Rotation_matrix) to accomplish tasks such as projecting a three-dimensional object onto a two-dimensional screen, corresponding to a theoretical camera observation; and to apply image convolutions such as sharpening, blurring, edge detection, and more. Matrices over a [polynomial ring](https://en.wikipedia.org/wiki/Polynomial_ring) are important in the study of [control theory](https://en.wikipedia.org/wiki/Control_theory).

[Chemistry](https://en.wikipedia.org/wiki/Chemistry) makes use of matrices in various ways, particularly since the use of [quantum theory](https://en.wikipedia.org/wiki/Quantum_mechanics) to discuss [molecular bonding](https://en.wikipedia.org/wiki/Chemical_bond) and [spectroscopy](https://en.wikipedia.org/wiki/Spectroscopy). Examples are the [overlap matrix](https://en.wikipedia.org/wiki/Overlap_matrix) and the [Fock matrix](https://en.wikipedia.org/wiki/Fock_matrix) used in solving the [Roothaan equations](https://en.wikipedia.org/wiki/Roothaan_equations) to obtain the [molecular orbitals](https://en.wikipedia.org/wiki/Molecular_orbital) of the [Hartree–Fock method](https://en.wikipedia.org/wiki/Hartree%E2%80%93Fock_method).

### Graph theory

![[media/410b9685d02a4c2cdf135f475855e6faa147ebe4.png]]
An undirected graph with adjacency matrix: 

$$
{\begin{bmatrix}1&1&0\\1&0&1\\0&1&0\end{bmatrix}}.
$$

The [adjacency matrix](https://en.wikipedia.org/wiki/Adjacency_matrix) of a [finite graph](https://en.wikipedia.org/wiki/Finite_graph) is a basic notion of [graph theory](https://en.wikipedia.org/wiki/Graph_theory). It records which vertices of the graph are connected by an edge. Matrices containing just two different values (1 and 0 meaning for example "yes" and "no", respectively) are called [logical matrices](https://en.wikipedia.org/wiki/Logical_matrix). The [distance (or cost) matrix](https://en.wikipedia.org/wiki/Distance_matrix) contains information about the distances of the edges. These concepts can be applied to [websites](https://en.wikipedia.org/wiki/Website) connected by [hyperlinks](https://en.wikipedia.org/wiki/Hyperlink), or cities connected by roads etc., in which case (unless the connection network is extremely dense) the matrices tend to be [sparse](https://en.wikipedia.org/wiki/Sparse_matrix), that is, contain few nonzero entries. Therefore, specifically tailored matrix algorithms can be used in [network theory](https://en.wikipedia.org/wiki/Network_theory).

### Analysis and geometry

The [[Hessian Matrix]] of a [differentiable function](https://en.wikipedia.org/wiki/Differentiable_function) $f:\mathbb {R} ^{n}\to \mathbb {R}$ consists of the [second derivatives](https://en.wikipedia.org/wiki/Second_derivative) of ƒ concerning the several coordinate directions, that is, 

$$
H(f)=\left[{\frac {\partial ^{2}f}{\partial x_{i}\,\partial x_{j}}}\right].
$$

![[media/69fe3850f7b8594367b56250be2c63ce3fef76ee.png]]
At the [saddle point](https://en.wikipedia.org/wiki/Saddle_point) (<em>x</em> = 0, <em>y</em> = 0) (red) of the function <em>f</em> (<em>x</em>,−<em>y</em>) = <em>x</em><sup>2</sup> − <em>y</em><sup>2</sup>, the Hessian matrix ${\begin{bmatrix}2&0\\0&-2\end{bmatrix}}$ is [indefinite](https://en.wikipedia.org/wiki/Indefinite_matrix).

It encodes information about the local growth behavior of the function: given a [critical point](https://en.wikipedia.org/wiki/Critical_point_(mathematics) "Critical point (mathematics)") **x** = (*x*<sub>1</sub>, ..., *x<sub>n</sub>*), that is, a point where the first [partial derivatives](https://en.wikipedia.org/wiki/Partial_derivative) $\partial f/\partial x_{i}$ of f vanish, the function has a [local minimum](https://en.wikipedia.org/wiki/Local_minimum) if the Hessian matrix is [positive definite](https://en.wikipedia.org/wiki/Definiteness_of_a_matrix). [Quadratic programming](https://en.wikipedia.org/wiki/Quadratic_programming) can be used to find global minima or maxima of quadratic functions closely related to the ones attached to matrices (see [above](#quadratic_forms)).

Another matrix frequently used in geometrical situations is the [Jacobi matrix](https://en.wikipedia.org/wiki/Jacobian_matrix_and_determinant) of a differentiable map $f:\mathbb {R} ^{n}\to \mathbb {R} ^{m}$. If *f*<sub>1</sub>, ..., *f<sub>m</sub>* denote the components of f, then the Jacobi matrix is defined as 

$$
J(f)=\left[{\frac {\partial f_{i}}{\partial x_{j}}}\right]_{1\leq i\leq m,1\leq j\leq n}.
$$

 If *n* \> *m*, and if the rank of the Jacobi matrix attains its maximal value m, f is locally invertible at that point, by the [[Implicit Function Theorem]].

[Partial differential equations](https://en.wikipedia.org/wiki/Partial_differential_equation) can be classified by considering the matrix of coefficients of the highest-order differential operators of the equation. For [elliptic partial differential equations](https://en.wikipedia.org/wiki/Elliptic_partial_differential_equation) this matrix is positive definite, which has a decisive influence on the set of possible solutions of the equation in question.

The [finite element method](https://en.wikipedia.org/wiki/Finite_element_method) is an important numerical method to solve partial differential equations, widely applied in simulating complex physical systems. It attempts to approximate the solution to some equation by piecewise linear functions, where the pieces are chosen concerning a sufficiently fine grid, which in turn can be recast as a matrix equation.

### Probability theory and statistics

![[media/6fe772c1ac9e1c7e511e8e7ce671adb6ccdd116d.png]]
Two different Markov chains. The chart depicts the number of particles (of a total of 1000) in state "2". Both limiting values can be determined from the transition matrices, which are given by $\left[{\begin{smallmatrix}0.7&0\\0.3&1\end{smallmatrix}}\right]$ (red) and $\left[{\begin{smallmatrix}0.7&0.2\\0.3&0.8\end{smallmatrix}}\right]$ (black).

[Stochastic matrices](https://en.wikipedia.org/wiki/Stochastic_matrix) are square matrices whose rows are [probability vectors](https://en.wikipedia.org/wiki/Probability_vector), that is, whose entries are non-negative and sum up to one. Stochastic matrices are used to define [[Markov Chain|Markov chains]] with finitely many states. A row of the stochastic matrix gives the probability distribution for the next position of some particle currently in the state that corresponds to the row. Properties of the Markov chain—like [absorbing states](https://en.wikipedia.org/wiki/Absorbing_state), that is, states that any particle attains eventually—can be read off the eigenvectors of the transition matrices.

Statistics also makes use of matrices in many different forms. [Descriptive statistics](https://en.wikipedia.org/wiki/Descriptive_statistics) is concerned with describing data sets, which can often be represented as [data matrices](https://en.wikipedia.org/wiki/Data_matrix_(multivariate_statistics)), which may then be subjected to [dimensionality reduction](https://en.wikipedia.org/wiki/Dimensionality_reduction) techniques. The [covariance matrix](https://en.wikipedia.org/wiki/Covariance_matrix) encodes the mutual [variance](https://en.wikipedia.org/wiki/Variance) of several [random variables](https://en.wikipedia.org/wiki/Random_variable). Another technique using matrices are [linear least squares](https://en.wikipedia.org/wiki/Linear_least_squares), a method that approximates a finite set of pairs (*x*<sub>1</sub>, *y*<sub>1</sub>), (*x*<sub>2</sub>, *y*<sub>2</sub>), ..., (*x*<sub>*N*</sub>, *y*<sub>*N*</sub>), by a linear function 

$$
y_{i}\approx ax_{i}+b,\quad i=1,\ldots ,N
$$

 which can be formulated in terms of matrices, related to the [[Singular Value Decomposition]] of matrices.

[Random matrices](https://en.wikipedia.org/wiki/Random_matrix) are matrices whose entries are random numbers, subject to suitable [probability distributions](https://en.wikipedia.org/wiki/Probability_distribution), such as [matrix normal distribution](https://en.wikipedia.org/wiki/Matrix_normal_distribution). Beyond probability theory, they are applied in domains ranging from [number theory](https://en.wikipedia.org/wiki/Number_theory) to [physics](https://en.wikipedia.org/wiki/Physics).

### Quantum mechanics and particle physics

The first model of [quantum mechanics](https://en.wikipedia.org/wiki/Quantum_mechanics) ([Heisenberg](https://en.wikipedia.org/wiki/Werner_Heisenberg), 1925) used infinite-dimensional matrices to define the operators that took over the role of variables like position, momentum and energy from classical physics. (This is sometimes referred to as [matrix mechanics](https://en.wikipedia.org/wiki/Matrix_mechanics).) Matrices, both finite and infinite-dimensional, have since been employed for many purposes in quantum mechanics. One particular example is the [density matrix](https://en.wikipedia.org/wiki/Density_matrix), a tool used in calculating the [probabilities](https://en.wikipedia.org/wiki/Probabilities) of the outcomes of [measurements](https://en.wikipedia.org/wiki/Measurement_in_quantum_mechanics) performed on [physical systems](https://en.wikipedia.org/wiki/Physical_system).

Linear transformations and the associated [symmetries](https://en.wikipedia.org/wiki/Symmetry) play a [key role in modern physics](https://en.wikipedia.org/wiki/Symmetry_in_physics). For example, [elementary particles](https://en.wikipedia.org/wiki/Elementary_particle) in [quantum field theory](https://en.wikipedia.org/wiki/Quantum_field_theory) are classified as representations of the [Lorentz group](https://en.wikipedia.org/wiki/Lorentz_group) of special relativity and, more specifically, by their behavior under the [spin group](https://en.wikipedia.org/wiki/Spin_group). Concrete representations involving the [Pauli matrices](https://en.wikipedia.org/wiki/Pauli_matrices) and more general [gamma matrices](https://en.wikipedia.org/wiki/Gamma_matrices) are an integral part of the physical description of [fermions](https://en.wikipedia.org/wiki/Fermion), which behave as [spinors](https://en.wikipedia.org/wiki/Spinor). For the three lightest [quarks](https://en.wikipedia.org/wiki/Quark), there is a group-theoretical representation involving the [special unitary group](https://en.wikipedia.org/wiki/Special_unitary_group) SU(3); for their calculations, physicists use a convenient matrix representation known as the [Gell-Mann matrices](https://en.wikipedia.org/wiki/Gell-Mann_matrices), which are also used for the SU(3) [gauge group](https://en.wikipedia.org/wiki/Gauge_group) that forms the basis of the modern description of strong nuclear interactions, [quantum chromodynamics](https://en.wikipedia.org/wiki/Quantum_chromodynamics). The [Cabibbo–Kobayashi–Maskawa matrix](https://en.wikipedia.org/wiki/Cabibbo%E2%80%93Kobayashi%E2%80%93Maskawa_matrix), in turn, expresses the fact that the basic quark states that are important for [weak interactions](https://en.wikipedia.org/wiki/Weak_interaction) are not the same as, but linearly related to the basic quark states that define particles with specific and distinct [masses](https://en.wikipedia.org/wiki/Mass).

Another matrix serves as a key tool for describing the scattering experiments that form the cornerstone of experimental particle physics: Collision reactions such as occur in [particle accelerators](https://en.wikipedia.org/wiki/Particle_accelerator), where non-interacting particles head towards each other and collide in a small interaction zone, with a new set of non-interacting particles as the result, can be described as the scalar product of outgoing particle states and a linear combination of ingoing particle states. The linear combination is given by a matrix known as the [S-matrix](https://en.wikipedia.org/wiki/S-matrix), which encodes all information about the possible interactions between particles.

### Normal modes

A general application of matrices in physics is the description of linearly coupled harmonic systems. The [equations of motion](https://en.wikipedia.org/wiki/Equations_of_motion) of such systems can be described in matrix form, with a mass matrix multiplying a generalized velocity to give the kinetic term, and a [force](https://en.wikipedia.org/wiki/Force) matrix multiplying a displacement vector to characterize the interactions. The best way to obtain solutions is to determine the system's [eigenvectors](https://en.wikipedia.org/wiki/Eigenvector), its [normal modes](https://en.wikipedia.org/wiki/Normal_mode), by diagonalizing the matrix equation. Techniques like this are crucial when it comes to the internal dynamics of [molecules](https://en.wikipedia.org/wiki/Molecules): the internal vibrations of systems consisting of mutually bound component atoms. They are also needed for describing mechanical vibrations, and oscillations in electrical circuits.

### Geometrical optics

[Geometrical optics](https://en.wikipedia.org/wiki/Geometrical_optics) provides further matrix applications. In this approximative theory, the [wave nature](https://en.wikipedia.org/wiki/Light_wave) of light is neglected. The result is a model in which [light rays](https://en.wikipedia.org/wiki/Ray_(optics) "Ray (optics)") are indeed [geometrical rays](https://en.wikipedia.org/wiki/Ray_(geometry)). If the deflection of light rays by optical elements is small, the action of a [lens](https://en.wikipedia.org/wiki/Lens_(optics)) or reflective element on a given light ray can be expressed as multiplication of a two-component vector with a two-by-two matrix called [ray transfer matrix analysis](https://en.wikipedia.org/wiki/Ray_transfer_matrix_analysis): the vector's components are the light ray's slope and its distance from the optical axis, while the matrix encodes the properties of the optical element. There are two kinds of matrices, viz. a *refraction matrix* describing the refraction at a lens surface, and a *translation matrix*, describing the translation of the plane of reference to the next refracting surface, where another refraction matrix applies. The optical system, consisting of a combination of lenses and reflective elements, is simply described by the matrix resulting from the product of the components' matrices.

The [Jones calculus](https://en.wikipedia.org/wiki/Jones_calculus) models the [polarization](https://en.wikipedia.org/wiki/Polarization_(physics)) of a light source as a $2\times 2$ vector, and the effects of [optical filters](https://en.wikipedia.org/wiki/Optical_filter) on this polarization vector as a matrix.

### Electronics

Electronic circuits that are composed of linear components (such as resistors, inductors and capacitors) obey [Kirchhoff's circuit laws](https://en.wikipedia.org/wiki/Kirchhoff%27s_circuit_laws), which leads to a system of linear equations, which can be described with a matrix equation that relates the source currents and voltages to the resultant currents and voltages at each point in the circuit, and where the matrix entries are determined by the circuit.

## History

Matrices have a long history of application in solving [linear equations](https://en.wikipedia.org/wiki/Linear_equation) but they were known as arrays until the 1800s. The [Chinese text](https://en.wikipedia.org/wiki/Chinese_mathematics) *[The Nine Chapters on the Mathematical Art](https://en.wikipedia.org/wiki/The_Nine_Chapters_on_the_Mathematical_Art)* written in the 10th–2nd century BCE is the first example of the use of array methods to solve [simultaneous equations](https://en.wikipedia.org/wiki/System_of_linear_equations), including the concept of [[Determinant|determinants]]. In 1545 Italian mathematician [Gerolamo Cardano](https://en.wikipedia.org/wiki/Gerolamo_Cardano) introduced the method to Europe when he published *Ars Magna*. The [Japanese mathematician](https://en.wikipedia.org/wiki/Japanese_mathematics) [Seki](https://en.wikipedia.org/wiki/Seki_Kowa) used the same array methods to solve simultaneous equations in 1683. The Dutch mathematician [Jan de Witt](https://en.wikipedia.org/wiki/Jan_de_Witt) represented transformations using arrays in his 1659 book *Elements of Curves* (1659). Between 1700 and 1710 [Gottfried Wilhelm Leibniz](https://en.wikipedia.org/wiki/Gottfried_Wilhelm_Leibniz) publicized the use of arrays for recording information or solutions and experimented with over 50 different systems of arrays. [Cramer](https://en.wikipedia.org/wiki/Gabriel_Cramer) presented [his rule](https://en.wikipedia.org/wiki/Cramer%27s_rule) in 1750.

This use of the term *matrix* in mathematics (an English word for "womb" in the 19th century, from Latin, as well as a jargon word [in printing](https://en.wikipedia.org/wiki/Matrix_(printing) "Matrix (printing)"), [in biology](https://en.wikipedia.org/wiki/Matrix_(biology) "Matrix (biology)") and [in geology](https://en.wikipedia.org/wiki/Matrix_(geology) "Matrix (geology)")) was coined by [James Joseph Sylvester](https://en.wikipedia.org/wiki/James_Joseph_Sylvester) in 1850, who understood a matrix as an object giving rise to several determinants today called [minors](https://en.wikipedia.org/wiki/Minor_(linear_algebra) "Minor (linear algebra)"), that is to say, determinants of smaller matrices that derive from the original one by removing columns and rows. In an 1851 paper, Sylvester explains:

> I have in previous papers defined a "Matrix" as a rectangular array of terms, out of which different systems of determinants may be engendered from the womb of a common parent.

[Arthur Cayley](https://en.wikipedia.org/wiki/Arthur_Cayley) published a treatise on geometric transformations using matrices that were not rotated versions of the coefficients being investigated as had previously been done. Instead, he defined operations such as addition, subtraction, multiplication, and division as transformations of those matrices and showed the associative and distributive properties held. Cayley investigated and demonstrated the non-commutative property of matrix multiplication as well as the commutative property of matrix addition. Early matrix theory had limited the use of arrays almost exclusively to determinants and Cayley's abstract matrix operations were revolutionary. He was instrumental in proposing a matrix concept independent of equation systems. In 1858, Cayley published his *A memoir on the theory of matrices* in which he proposed and demonstrated the [Cayley–Hamilton theorem](https://en.wikipedia.org/wiki/Cayley%E2%80%93Hamilton_theorem).

The English mathematician [Cuthbert Edmund Cullis](https://en.wikipedia.org/wiki/Cuthbert_Edmund_Cullis) was the first to use modern bracket notation for matrices in 1913 and he simultaneously demonstrated the first significant use of the notation **A** = \[*a*<sub>*i*,*j*</sub>\] to represent a matrix where *a*<sub>*i*,*j*</sub> refers to the ith row and the jth column.

The modern study of determinants sprang from several sources. [Number-theoretical](https://en.wikipedia.org/wiki/Number_theory) problems led [Gauss](https://en.wikipedia.org/wiki/Gauss) to relate coefficients of [quadratic forms](https://en.wikipedia.org/wiki/Quadratic_form), that is, expressions such as *x*<sup>2</sup> + *xy* − 2*y*<sup>2</sup>, and [linear maps](https://en.wikipedia.org/wiki/Linear_map) in three dimensions to matrices. [Eisenstein](https://en.wikipedia.org/wiki/Gotthold_Eisenstein) further developed these notions, including the remark that, in modern parlance, [matrix products](https://en.wikipedia.org/wiki/Matrix_product) are [non-commutative](https://en.wikipedia.org/wiki/Non-commutative). [Cauchy](https://en.wikipedia.org/wiki/Augustin-Louis_Cauchy) was the first to prove general statements about determinants, using as the definition of the determinant of a matrix **A** = \[*a*<sub>*i*,*j*</sub>\] the following: replace the powers *a*<sub>*j*</sub><sup>*k*</sup> by *a*<sub>*j*,*k*</sub> in the [polynomial](https://en.wikipedia.org/wiki/Polynomial) 

$$
a_{1}a_{2}\cdots a_{n}\prod _{i<j}(a_{j}-a_{i}),
$$

 where $\textstyle \prod$ denotes the [product](https://en.wikipedia.org/wiki/Multiplication) of the indicated terms. He also showed, in 1829, that the [eigenvalues](https://en.wikipedia.org/wiki/Eigenvalue) of symmetric matrices are real. [Jacobi](https://en.wikipedia.org/wiki/Carl_Gustav_Jacob_Jacobi) studied "functional determinants"—later called [Jacobi determinants](https://en.wikipedia.org/wiki/Jacobian_matrix_and_determinant) by Sylvester—which can be used to describe geometric transformations at a local (or [infinitesimal](https://en.wikipedia.org/wiki/Infinitesimal)) level, see [above](#Jacobi_matrix). [Kronecker](https://en.wikipedia.org/wiki/Leopold_Kronecker)'s *Vorlesungen über die Theorie der Determinanten* and [Weierstrass](https://en.wikipedia.org/wiki/Karl_Weierstrass)'s *Zur Determinantentheorie*, both published in 1903, first treated determinants [axiomatically](https://en.wikipedia.org/wiki/Axiom), as opposed to previous more concrete approaches such as the mentioned formula of Cauchy. At that point, determinants were firmly established.

Many theorems were first established for small matrices only, for example, the [Cayley–Hamilton theorem](https://en.wikipedia.org/wiki/Cayley%E2%80%93Hamilton_theorem) was proved for 2 × 2 matrices by Cayley in the aforementioned memoir, and by [Hamilton](https://en.wikipedia.org/wiki/William_Rowan_Hamilton) for 4 × 4 matrices. [Frobenius](https://en.wikipedia.org/wiki/Georg_Frobenius), working on [bilinear forms](https://en.wikipedia.org/wiki/Bilinear_form), generalized the theorem to all dimensions (1898). Also at the end of the 19th century, the [Gauss–Jordan elimination](https://en.wikipedia.org/wiki/Gauss%E2%80%93Jordan_elimination) (generalizing a special case now known as [Gauss elimination](https://en.wikipedia.org/wiki/Gauss_elimination)) was established by [Wilhelm Jordan](https://en.wikipedia.org/wiki/Wilhelm_Jordan_(geodesist) "Wilhelm Jordan (geodesist)"). In the early 20th century, matrices attained a central role in linear algebra, partially due to their use in the classification of the [hypercomplex number](https://en.wikipedia.org/wiki/Hypercomplex_number) systems of the previous century.

The inception of [matrix mechanics](https://en.wikipedia.org/wiki/Matrix_mechanics) by [Heisenberg](https://en.wikipedia.org/wiki/Werner_Heisenberg), [Born](https://en.wikipedia.org/wiki/Max_Born) and [Jordan](https://en.wikipedia.org/wiki/Pascual_Jordan) led to studying matrices with infinitely many rows and columns. Later, [von Neumann](https://en.wikipedia.org/wiki/John_von_Neumann) carried out the [mathematical formulation of quantum mechanics](https://en.wikipedia.org/wiki/Mathematical_formulation_of_quantum_mechanics), by further developing [functional analytic](https://en.wikipedia.org/wiki/Functional_analysis) notions such as [linear operators](https://en.wikipedia.org/wiki/Linear_operator) on [Hilbert spaces](https://en.wikipedia.org/wiki/Hilbert_space), which, very roughly speaking, correspond to [Euclidean space](https://en.wikipedia.org/wiki/Euclidean_space), but with an infinity of [independent directions](https://en.wikipedia.org/wiki/Hamel_dimension).

### Other historical usages of the word "matrix" in mathematics

The word has been used in unusual ways by at least two authors of historical importance.

[Bertrand Russell](https://en.wikipedia.org/wiki/Bertrand_Russell) and [Alfred North Whitehead](https://en.wikipedia.org/wiki/Alfred_North_Whitehead) in their *[Principia Mathematica](https://en.wikipedia.org/wiki/Principia_Mathematica)* (1910–1913) use the word "matrix" in the context of their [axiom of reducibility](https://en.wikipedia.org/wiki/Axiom_of_reducibility). They proposed this axiom as a means to reduce any function to one of lower type, successively, so that at the "bottom" (0 order) the function is identical to its [extension](https://en.wikipedia.org/wiki/Extension_(predicate_logic) "Extension (predicate logic)"):

> Let us give the name of *matrix* to any function, of however many variables, that does not involve any [apparent variables](https://en.wikipedia.org/wiki/Apparent_variable). Then, any possible function other than a matrix derives from a matrix using generalization, that is, by considering the proposition that the function in question is true with all possible values or with some value of one of the arguments, the other argument or arguments remaining undetermined.

For example, a function Φ(*x*, *y*) of two variables x and y can be reduced to a *collection* of functions of a single variable, such as y, by "considering" the function for all possible values of "individuals" a<sub>i</sub> substituted in place of a variable x. And then the resulting collection of functions of the single variable y, that is, ∀*a*<sub>*i*</sub>: Φ(*a*<sub>*i*</sub>, *y*), can be reduced to a "matrix" of values by "considering" the function for all possible values of "individuals" *b*<sub>*i*</sub> substituted in place of variable y: 

$$
\forall b_{j}\forall a_{i}\colon \phi (a_{i},b_{j}).
$$

[Alfred Tarski](https://en.wikipedia.org/wiki/Alfred_Tarski) in his 1941 *Introduction to Logic* used the word "matrix" synonymously with the notion of [truth table](https://en.wikipedia.org/wiki/Truth_table) as used in mathematical logic.

## See also

- ![[media/1a9c6ad1ccebbc090fc7cd1c94d2142489246997.png]][Mathematics portal](https://en.wikipedia.org/wiki/Portal:Mathematics)

- [List of named matrices](https://en.wikipedia.org/wiki/List_of_named_matrices)
- [Gram–Schmidt process](https://en.wikipedia.org/wiki/Gram%E2%80%93Schmidt_process) – Orthonormalization of a set of vectors
- [Irregular matrix](https://en.wikipedia.org/wiki/Irregular_matrix)
- [[Matrix Calculus]] – Specialized notation for multivariable calculus
- [Matrix function](https://en.wikipedia.org/wiki/Matrix_function) – Function that maps matrices to matricesPages displaying short descriptions of redirect targets

## Notes

1.  ^   , Chapter XIII.
2.  , p. 209.
3.  , p. 37.
4.  ^   , p. 1.
5.  , p. 3.
6.  , p. 5.
7.  , p. 89.
8.  ^   "A matrix having at least one dimension equal to zero is called an empty matrix", [MATLAB Data Structures](https://system.nada.kth.se/unix/software/matlab/Release_14.1/techdoc/matlab_prog/ch_dat29.html) [Archived](https://web.archive.org/web/20091228102653/http://www.system.nada.kth.se/unix/software/matlab/Release_14.1/techdoc/matlab_prog/ch_dat29.html) 2009-12-28 at the [Wayback Machine](https://en.wikipedia.org/wiki/Wayback_Machine)
9.  , p. [71](https://books.google.com/books?id=ZfJdDwAAQBAJ&pg=PA71).
10. , p. [29](https://books.google.com/books?id=W5o4AAAAIAAJ&pg=PA29).
11. , pp. [52–53](https://books.google.com/books?id=2J0ndF_LmqoC&pg=PA52).
12. , p. [915](https://books.google.com/books?id=GYRX8ZYVNYQC&pg=PA915).
13. , p. [21](https://books.google.com/books?id=y24vEAAAQBAJ&pg=PA21).
14. , Ch. 5.
15. ^   .
16. For example, for $M$, see , [p. 48](https://books.google.com/books?id=RC4tDwAAQBAJ&pg=PA48); for $\operatorname {Mat}$, see , [p. 50](https://books.google.com/books?id=ovIYVIlithQC&pg=PA50).
17. **,_Definition_I.2.4_(scalar_multiplication),_and_Definition_I.2.33_(transpose)_17-0)** , Definition I.2.1 (addition), Definition I.2.4 (scalar multiplication), and Definition I.2.33 (transpose).
18. , p. 29.
19. , Theorem I.2.6.
20. , p. 30.
21. , p. [46](https://books.google.com/books?id=oQk9AAAAIAAJ&pg=PA46).
22. , pp. [6–7](https://books.google.com/books?id=2c011Aptsa8C&pg=PA6).
23. , p. [38](https://books.google.com/books?id=WtpVEAAAQBAJ&pg=PA38), The transpose of a matrix and its properties.
24. ^   , p. [9](https://books.google.com/books?id=4nfNCgAAQBAJ&pg=PA9).
25. , Definition I.2.20.
26. , Theorem I.2.24.
27. , p. 117.
28. , Ch. 4 and 5.
29. .
30. , p. [119–120](http://books.google.com/books?id=JO8GEQAAQBAJ&pg=PA119).
31. , p. [71](http://books.google.com/books?id=c_NEBAAAQBAJ&pg=PA71).
32. , p. [102](http://books.google.com/books?id=xi5omWiQ-3kC&pg=PA102).
33. , p. 16.
34. , p. 220.
35. ^   , p. 869.
36. , pp. 241, 244.
37. .
38. .
39. .
40. Horn, Roger A.; Johnson, Charles R. (2012), [Matrix Analysis](https://books.google.com/books?id=5I5AYeeh0JUC&pg=PA17) (2nd ed.), Cambridge University Press, p. 17, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-83940-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-83940-2).
41. , I.2.21 and 22.
42. , p. 95.
43. , pp. 1–2.
44. , pp. 494–495.
45. , p. [263](https://books.google.com/books?id=ZrBaRPVRLRoC&pg=PA263).
46. , p. [56](https://books.google.com/books?id=y24vEAAAQBAJ&pg=PA56).
47. , p. [60](https://books.google.com/books?id=2wzp9zQhA_IC&pg=PA60).
48. ^    .
49. , p. [264](https://books.google.com/books?id=uan0Dkn9HY8C&pg=PA264).
50. , p. 90). Note however that Greub follows a transposed convention of representing a transformation by multiplying a row vector by a matrix, rather than multiplying a matrix by a column vector, leading to the reversed order for the two matrices in the product that represents a composition.
51. , §VI.1.
52. , Definition II.3.3.
53. , Section III.1.
54. , Theorem II.3.22.
55. , p. [27](https://books.google.com/books?id=YmcQJoFyZ5gC&pg=PA27).
56. .
57. , p. [68](https://books.google.com/books?id=YmcQJoFyZ5gC&pg=PA68).
58. , p. 91.
59. ^   , p. 118.
60. , §0.9.1 Diagonal matrices.
61. , p. 138.
62. , Theorem 2.5.6.
63. , pp. 262–263.
64. , Definition I.2.28.
65. , Definition I.5.13.
66. , p. [62](https://books.google.com/books?id=YmcQJoFyZ5gC&pg=PA62).
67. , pp. 99–100.
68. , Chapter 7.
69. , Thm. 7.3.2.
70. , Theorem 7.2.1.
71. , p. 150.
72. , p. 169, Example 4.0.6.
73. , Appendix. Complex numbers.
74. , pp. 66–67.
75. , pp. 102–103.
76. , pp. 127, 153–154.
77. , p. 141.
78. , pp. 40, 42.
79. , p. 281.
80. , p. 226.
81. , p. 94.
82. , §0.5 Nonsingularity.
83. .
84. ["Matrix | mathematics"](https://britannica.com/science/matrix-mathematics), *Encyclopedia Britannica*, retrieved 2020-08-19
85. , Definition III.2.1.
86. , Theorem III.2.12.
87. , Corollary III.2.16.
88. , Theorem 1.4.1.
89. , Theorem III.3.18.
90. *Eigen* means "own" in [German](https://en.wikipedia.org/wiki/German_language) and in [Dutch](https://en.wikipedia.org/wiki/Dutch_language). See [Wiktionary](https://en.wiktionary.org/wiki/eigen).
91. , Definition III.4.1.
92. , Definition III.4.9.
93. , Corollary III.4.10.
94. , pp. [317–319](https://books.google.com/books?id=ypROEAAAQBAJ&pg=PA317).
95. , p. 265.
96. , Ch. 7.
97. .
98. , Algorithm 1.3.1.
99. .
100. .
101. , Chapters 9 and 10, esp. section 10.2.
102. , Chapter 2.3.
103. .
104. , Section 4.1.
105. , pp. 146–153.
106. , Theorem 2.5.4.
107. , Ch. 3.1, 3.2.
108. , Sections 14.5, 7, 8.
109. , Ch. 15.
110. , Ch. V.
111. .
112. , pp. 461–470, Chapter 7, §17 Matrix Rings, §17A Characterization and Examples.
113. , p. [302](https://books.google.com/books?id=iSAAEAAAQBAJ&pg=PA302), Definition 7.2.1.
114. .
115. , pp. [4-6](https://books.google.com/books?id=6B9MDgAAQBAJ&pg=PA4).
116. , p. [27](https://books.google.com/books?id=fk7u8awR0hIC&pg=PA27).
117. , pp. [115–116](https://books.google.com/books?id=ZIqADwAAQBAJ&pg=PA115).
118. , pp. [360–361](https://books.google.com/books?id=wK1XDwAAQBAJ&pg=PA360).
119. , p. [80](https://books.google.com/books?id=ylFR4h5BIDEC&pg=PA80).
120. , p. 643, XVII.1.
121. , Proposition XIII.4.16.
122. , Section L.2.
123. , pp. [54ff](https://books.google.com/books?id=uan0Dkn9HY8C&pg=PA54), 3.7 Partitioning of matrices.
124. , Section III.3.
125. , Section III.3.13.
126. , pp. 99–100.
127. , pp. 328–335, VII.1: Matrices and maps.
128. , p. 69.
129. , Def. 1.30.
130. .
131. , Theorem 1.2.
132. , Chapter 4.5.
133. , p. [20](https://books.google.com/books?id=vY_xBwAAQBAJ&pg=PA20).
134. , p. 198, Example 19.2.
135. See any reference in representation theory or [group representation](https://en.wikipedia.org/wiki/Group_representation).
136. See the item "Matrix" in Itô .
137. , pp. [34–39](https://books.google.com/books?id=kZ9cy6XyidEC&pg=PA34), 2.2 Dealing with infinite matrices.
138. , p. [334](https://books.google.com/books?id=LJtyhu8-xYwC&pg=PA334).
139. "Not much of matrix theory carries over to infinite-dimensional spaces, and what does is not so useful, but it sometimes helps." Halmos , p. 23, Chapter 5.
140. "Empty Matrix: A matrix is empty if either its row or column dimension is zero", [Glossary](https://omatrix.com/manual/glossary.htm) [Archived](https://web.archive.org/web/20090429015728/http://www.omatrix.com/manual/glossary.htm) 2009-04-29 at the [Wayback Machine](https://en.wikipedia.org/wiki/Wayback_Machine), O-Matrix v6 User Guide
141. , p. [213](https://books.google.com/books?id=zUh9I2mSKxgC&pg=PA213).
142. , p. [151](http://books.google.com/books?id=5w6lDgAAQBAJ&pg=PA151).
143. The notation of empty matrix is used differently from some sources like , p. [90](http://books.google.com/books?id=-c0NxJg4vHMC&pg=PA90) use $0_{0\times n}$, resembling the [zero matrix](https://en.wikipedia.org/wiki/Zero_matrix); , p. [151](http://books.google.com/books?id=5w6lDgAAQBAJ&pg=PA151) use ${\mathfrak {I}}_{0\times n}$.
144. , p. [750](https://books.google.com/books?id=0-3vDwAAQBAJ&pg=PA750).
145. , p. [19](https://books.google.com/books?id=LMRTDwAAQBAJ&pg=PA19).
146. ^   , 2087.
147. , 351.
148. , 222.
149. ^   , 137.
150. , Section 15.3.4.
151. , Ch. 2.8.
152. , p. [436](https://books.google.com/books?id=yvCC94xzJG8C&pg=PA436).
153. , Section 1.1.1.
154. , p. [390](https://books.google.com/books?id=U9slEQAAQBAJ&pg=PA390), 11.2.3 The expected payoff as a vector–matrix–vector product.
155. , pp. [136–137](https://books.google.com/books?id=6MO_RS4z0w8C&pg=PA136).
156. , Ch. 1.1.5 and 1.2.4.
157. , Ch. 7.
158. , p. [230](https://books.google.com/books?id=3X7S_965jywC&pg=PA230).
159. , p. [65–69](https://archive.org/details/introductiontoco0000jens/page/65/mode/2up?q=matrix).
160. , Ch. 8.1.
161. .
162. , p. [7](http://books.google.com/books?id=0xhra9vKCnUC&pg=PA7).
163. .
164. , Ch. XVI.6.
165. , Ch. 16.
166. , Ch. XVI.1.
167. Lang , Ch. XVI.5. For a more advanced, and more general statement see Lang , Ch. VI.2.
168. .
169. Šolin , Ch. 2.5. See also [stiffness method](https://en.wikipedia.org/wiki/Stiffness_method).
170. .
171. , Ch. 2.8.
172. [Healy, Michael](https://en.wikipedia.org/wiki/Michael_Healy_(statistician) "Michael Healy (statistician)") (1986), *Matrices for Statistics*, [Oxford University Press](https://en.wikipedia.org/wiki/Oxford_University_Press), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-19-850702-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-19-850702-4)
173. , p. 60, Ch. 2.2.
174. , Ch. 4.1.
175. [Conrey](https://en.wikipedia.org/wiki/Brian_Conrey) 
176. Zabrodin, Brézin & Kazakov et al. 
177. , Ch. 6.
178. , p. 20.
179. , sections I.8, II.4, and II.8.
180. , p. 73.
181. , Ch. 2.
182. **),_section_2.4.3.2._(Kobayashi–Maskawa_matrix)_182-0)** , section 1.6.3. (SU(3)), section 2.4.3.2. (Kobayashi–Maskawa matrix).
183. , Ch. 3.
184. , part II.
185. , 7.17.
186. , Ch. 5.
187. , pp. 747–749.
188. Shen, Crossley & Lun  cited by Bretscher , p. 1
189. ^      , pp. 564–565.
190. [Needham, Joseph](https://en.wikipedia.org/wiki/Joseph_Needham); [Wang Ling](https://en.wikipedia.org/wiki/Wang_Ling_(historian) "Wang Ling (historian)") (1959), [Science and Civilisation in China](https://books.google.com/books?id=jfQ9E0u4pLAC&pg=PA117), vol. III, Cambridge: Cambridge University Press, p. 117, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-05801-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-05801-8)`{{`[`cite book`](https://en.wikipedia.org/wiki/Template:Cite_book)`}}`: CS1 maint: ignored ISBN errors ([link](https://en.wikipedia.org/wiki/Category:CS1_maint:_ignored_ISBN_errors))
191. , p. 564.
192. .
193. .
194. [Murray, James](https://en.wikipedia.org/wiki/James_Murray_(lexicographer) "James Murray (lexicographer)"); [Bradley, Henry](https://en.wikipedia.org/wiki/Henry_Bradley), eds. (1908), ["Matrix"](https://archive.org/details/oed6barch/page/238/mode/1up), *[A New English Dictionary on Historical Principles](https://en.wikipedia.org/wiki/A_New_English_Dictionary_on_Historical_Principles)*, vol. 6, pt. 2 (M–N), Oxford: Clarendon Press, p. 238
195. The earliest published example is J. J. Sylvester (1850) "Additions to the articles in the September number of this journal, 'On a new class of theorems,' and on Pascal's theorem," *The London, Edinburgh, and Dublin Philosophical Magazine and Journal of Science*, **37**: 363-370. [From page 369](https://books.google.com/books?id=CBhDAQAAIAAJ&pg=PA369): "For this purpose, we must commence, not with a square, but with an oblong arrangement of terms consisting, suppose, of m lines and n columns. This does not in itself represent a determinant, but is, as it were, a Matrix out of which we may form various systems of determinants ... "
196. , p. 247, [Paper 37](https://books.google.com/books?id=5GQPlxWrDiEC&pg=PA247).
197. .
198. , Vol. 1, Ch. III, p. 96.
199. ^   .
200. .
201. Kronecker 
202. Weierstrass , pp. 271–286
203. .
204. .
205. .
206. , pp. 28–40.
207. , pp. 79, 106–107.
208. Whitehead, Alfred North; and Russell, Bertrand (1913) *Principia Mathematica to \*56*, Cambridge at the University Press, Cambridge UK (republished 1962) cf page 162ff.
209. , p. [40](https://books.google.com/books?id=5MeNCgAAQBAJ&pg=PA40).

## References

### Mathematical references

- Andrilli, Stephen; Hecker, David (2022), *Elementary Linear Algebra* (6th ed.), Academic Press, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780323984263](https://en.wikipedia.org/wiki/Special:BookSources/9780323984263)
- Anton, Howard (2010), [Elementary Linear Algebra](https://books.google.com/books?id=YmcQJoFyZ5gC&pg=PA414) (10th ed.), John Wiley & Sons, p. 414, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-470-45821-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-470-45821-1)
- [Arnold, Vladimir I.](https://en.wikipedia.org/wiki/Vladimir_Arnold) (1992), *Ordinary differential equations*, translated by Cooke, Roger, Berlin, DE; New York, NY: [Springer-Verlag](https://en.wikipedia.org/wiki/Springer-Verlag), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-54813-3](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-54813-3)
- [Artin, Michael](https://en.wikipedia.org/wiki/Michael_Artin) (1991), *Algebra*, [Prentice Hall](https://en.wikipedia.org/wiki/Prentice_Hall), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-89871-510-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-89871-510-1)
- Axler, Sheldon (1997), *Linear Algebra Done Right*, Undergraduate Texts in Mathematics (2nd ed.), Springer, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780387982595](https://en.wikipedia.org/wiki/Special:BookSources/9780387982595)
- Baker, Andrew J. (2003), [Matrix Groups: An Introduction to Lie Group Theory](https://archive.org/details/matrixgroupsintr0000bake), Berlin, DE; New York, NY: Springer-Verlag, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-85233-470-3](https://en.wikipedia.org/wiki/Special:BookSources/978-1-85233-470-3)
- Bau III, David; [Trefethen, Lloyd N.](https://en.wikipedia.org/wiki/Lloyd_N._Trefethen) (1997), *Numerical linear algebra*, Philadelphia, PA: Society for Industrial and Applied Mathematics, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-89871-361-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-89871-361-9)
- [Ben-Israel, Adi](https://en.wikipedia.org/wiki/Adi_Ben-Israel); [Greville, Thomas Nall Eden](https://en.wikipedia.org/wiki/Thomas_N._E._Greville) (2003), *Generalized Inverses: Theory and Applications* (2nd ed.), New York, NY: Springer, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/b97366](https://doi.org/10.1007%2Fb97366), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-00293-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-00293-4)
- Bernstein, Dennis S. (2009), *Matrix mathematics: theory, facts, and formulas* (2nd ed.), Princeton, N.J: Princeton University Press, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4008-3334-4](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4008-3334-4)
- Bhaya, Amit; Kaszkurewicz, Eugenius (2006), *Control Perspectives on Numerical Algorithms and Matrix Problems*, Advances in Design and Control, vol. 10, SIAM, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780898716023](https://en.wikipedia.org/wiki/Special:BookSources/9780898716023)
- Bierens, Herman J. (2004), *Introduction to the Mathematical and Statistical Foundations of Econometrics*, Cambridge University Press, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780521542241](https://en.wikipedia.org/wiki/Special:BookSources/9780521542241)
- Boos, Johann (2000), *Classical and Modern Methods in Summability*, Oxford mathematical monographs, Oxford University Press, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780198501657](https://en.wikipedia.org/wiki/Special:BookSources/9780198501657)
- Bretscher, Otto (2005), *Linear Algebra with Applications* (3rd ed.), Prentice Hall
- Bronson, Richard (1970), *Matrix Methods: An Introduction*, New York: [Academic Press](https://en.wikipedia.org/wiki/Academic_Press), [LCCN](https://en.wikipedia.org/wiki/LCCN_(identifier)) [70097490](https://lccn.loc.gov/70097490)
- Bronson, Richard (1989), *Schaum's outline of theory and problems of matrix operations*, New York: [McGraw–Hill](https://en.wikipedia.org/wiki/McGraw%E2%80%93Hill), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-07-007978-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-07-007978-6)
- Brown, William C. (1991), [Matrices and vector spaces](https://archive.org/details/matricesvectorsp0000brow), New York, NY: [Marcel Dekker](https://en.wikipedia.org/wiki/Marcel_Dekker), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8247-8419-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8247-8419-5)
- [Brualdi, Richard A.](https://en.wikipedia.org/wiki/Richard_A._Brualdi); Carmona, Ángeles; [van den Driessche, P.](https://en.wikipedia.org/wiki/Pauline_van_den_Driessche); Kirkland, Stephen; Stevanović, Dragan (2018), Encinas, Andrés M.; Mitjana, Margarida (eds.), *Combinatorial Matrix Theory*, Advanced Courses in Mathematics. CRM Barcelona, Birkhäuser/Springer, Cham, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-3-319-70953-6](https://doi.org/10.1007%2F978-3-319-70953-6), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-319-70952-9](https://en.wikipedia.org/wiki/Special:BookSources/978-3-319-70952-9), [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [3791450](https://mathscinet.ams.org/mathscinet-getitem?mr=3791450)
- Cameron, Peter J. (2014), ["Matrix groups"](https://webspace.maths.qmul.ac.uk/p.j.cameron/preprints/mgo.pdf) (PDF), in Hogben, Leslie (ed.), *Handbook of Linear Algebra*, Discrete Mathematics and its Applications (Boca Raton) (2nd ed.), CRC Press, Boca Raton, FL, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4665-0728-9](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4665-0728-9), [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [3013937](https://mathscinet.ams.org/mathscinet-getitem?mr=3013937)
- Carboni, Aurelio; Kasangian, Stefano; Walters, Robert (1987), "An axiomatics for bicategories of modules", *Journal of Pure and Applied Algebra*, **45** (2): 127–141, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/0022-4049(87)90065-X](https://doi.org/10.1016%2F0022-4049%2887%2990065-X), [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0889588](https://mathscinet.ams.org/mathscinet-getitem?mr=0889588), [Zbl](https://en.wikipedia.org/wiki/Zbl_(identifier)) [0615.18006](https://zbmath.org/?format=complete&q=an:0615.18006)
- Chahal, J. S. (2018), *Fundamentals of Linear Algebra*, CRC Press, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780429758119](https://en.wikipedia.org/wiki/Special:BookSources/9780429758119)
- Coburn, Nathaniel (1955), *Vector and tensor analysis*, New York, NY: Macmillan, [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [1029828](https://search.worldcat.org/oclc/1029828)
- Coleman, Thomas F.; Van Loan, Charles (1988), *Handbook for Matrix Computations*, Frontiers in Applied Mathematics, vol. 4, SIAM, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780898712278](https://en.wikipedia.org/wiki/Special:BookSources/9780898712278)
- Conrey, J. Brian (2007), *Ranks of elliptic curves and random matrix theory*, [Cambridge University Press](https://en.wikipedia.org/wiki/Cambridge_University_Press), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-69964-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-69964-8)
- Dossey, John A. (2002), *Discrete Mathematics* (4th ed.), Addison Wesley, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780321079121](https://en.wikipedia.org/wiki/Special:BookSources/9780321079121)
- [Conway, John B.](https://en.wikipedia.org/wiki/John_B._Conway) (1990), *A Course in Functional Analysis*, Graduate Texts in Mathematics, vol. 96 (2nd ed.), Springer, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-97245-5](https://en.wikipedia.org/wiki/Special:BookSources/0-387-97245-5)
- [Edwards, Harold M.](https://en.wikipedia.org/wiki/Harold_Edwards_(mathematician) "Harold Edwards (mathematician)") (2004), *Linear Algebra*, Springer Science & Business Media, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780817643706](https://en.wikipedia.org/wiki/Special:BookSources/9780817643706)
- Farid, F. O.; Khan, Israr Ali; Wang, Qing-Wen (2013), "On matrices over an arbitrary semiring and their generalized inverses", *Linear Algebra and its Applications*, **439** (7): 2085–2105, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.laa.2013.06.002](https://doi.org/10.1016%2Fj.laa.2013.06.002), [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [3090456](https://mathscinet.ams.org/mathscinet-getitem?mr=3090456), [Zbl](https://en.wikipedia.org/wiki/Zbl_(identifier)) [1283.15016](https://zbmath.org/?format=complete&q=an:1283.15016)
- Fraleigh, John B. (1976), *A First Course In Abstract Algebra* (2nd ed.), Reading: [Addison-Wesley](https://en.wikipedia.org/wiki/Addison-Wesley), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-201-01984-1](https://en.wikipedia.org/wiki/Special:BookSources/0-201-01984-1)
- Fudenberg, Drew; [Tirole, Jean](https://en.wikipedia.org/wiki/Jean_Tirole) (1983), *Game Theory*, [MIT Press](https://en.wikipedia.org/wiki/MIT_Press)
- Gentle, James E. (1998), *Numerical Linear Algebra for Applications in Statistics*, Springer, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780387985428](https://en.wikipedia.org/wiki/Special:BookSources/9780387985428)
- Ghosh, Shamik (1996), "Matrices over semirings", *Information Sciences*, **90** (1–4): 221–230, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/0020-0255(95)00283-9](https://doi.org/10.1016%2F0020-0255%2895%2900283-9), [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1388422](https://mathscinet.ams.org/mathscinet-getitem?mr=1388422), [Zbl](https://en.wikipedia.org/wiki/Zbl_(identifier)) [0884.15010](https://zbmath.org/?format=complete&q=an:0884.15010)
- Gilbarg, David; [Trudinger, Neil S.](https://en.wikipedia.org/wiki/Neil_Trudinger) (2001), *Elliptic partial differential equations of second order* (2nd ed.), Berlin, DE; New York, NY: Springer-Verlag, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-41160-4](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-41160-4)
- [Godsil, Chris](https://en.wikipedia.org/wiki/Chris_Godsil); [Royle, Gordon](https://en.wikipedia.org/wiki/Gordon_Royle) (2004), *Algebraic Graph Theory*, Graduate Texts in Mathematics, vol. 207, Berlin, DE; New York, NY: Springer-Verlag, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-95220-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-95220-8)
- [Golub, Gene H.](https://en.wikipedia.org/wiki/Gene_H._Golub); [Van Loan, Charles F.](https://en.wikipedia.org/wiki/Charles_F._Van_Loan) (1996), *Matrix Computations* (3rd ed.), Johns Hopkins, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8018-5414-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8018-5414-9)
- Greub, Werner Hildbert (1975), *Linear algebra*, Graduate Texts in Mathematics, Berlin, DE; New York, NY: Springer-Verlag, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-90110-7](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-90110-7)
- Grillet, Pierre Antoine (2007), *Abstract Algebra*, [Graduate Texts in Mathematics](https://en.wikipedia.org/wiki/Graduate_Texts_in_Mathematics), vol. 242 (2nd ed.), Springer, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780387715681](https://en.wikipedia.org/wiki/Special:BookSources/9780387715681)
- Hachenberger, Dirk; Jungnickel, Dieter (2020), *Topics in Galois Fields*, Algorithms and Computation in Mathematics, vol. 29, Cham: Springer, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-3-030-60806-4](https://doi.org/10.1007%2F978-3-030-60806-4), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-030-60804-0](https://en.wikipedia.org/wiki/Special:BookSources/978-3-030-60804-0), [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [4233161](https://mathscinet.ams.org/mathscinet-getitem?mr=4233161)
- [Halmos, Paul Richard](https://en.wikipedia.org/wiki/Paul_Halmos) (1982), *A Hilbert space problem book*, Graduate Texts in Mathematics, vol. 19 (2nd ed.), Berlin, DE; New York, NY: Springer-Verlag, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-90685-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-90685-0), [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0675952](https://mathscinet.ams.org/mathscinet-getitem?mr=0675952)
- Grossman, Stanley I. (1994), *Elementary Linear Algebra* (5th ed.), Saunders College Pub., [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780030973543](https://en.wikipedia.org/wiki/Special:BookSources/9780030973543)
- Hamilton, A. G. (1987), *A First Course in Linear Algebra: With Concurrent Examples*, Cambridge University Press, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780521310413](https://en.wikipedia.org/wiki/Special:BookSources/9780521310413)
- Hazewinkel, Michiel; Gubareni, Nadiya M. (2017), *Algebras, Rings and Modules, Volume 2: Non-commutative Algebras and Rings* (2nd ed.), CRC Press
- [Horn, Roger A.](https://en.wikipedia.org/wiki/Roger_Horn); [Johnson, Charles R.](https://en.wikipedia.org/wiki/Charles_Royal_Johnson) (1985), *Matrix Analysis*, Cambridge University Press, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-38632-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-38632-6)
- Householder, Alston S. (1975), *The theory of matrices in numerical analysis*, New York, NY: [Dover Publications](https://en.wikipedia.org/wiki/Dover_Publications), [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0378371](https://mathscinet.ams.org/mathscinet-getitem?mr=0378371)
- Hungerford, Thomas W. (1980), *Algebra*, Graduate Texts in Mathematics, vol. 73, Springer-Verlag, New York-Berlin, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-90518-9](https://en.wikipedia.org/wiki/Special:BookSources/0-387-90518-9), [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0600654](https://mathscinet.ams.org/mathscinet-getitem?mr=0600654)
- ISRD Group (2005), *Computer Graphics*, Tata McGraw–Hill, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-07-059376-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-07-059376-3)
- Itô, Kiyosi, ed. (1987), *Encyclopedic dictionary of mathematics. Vol. I-IV* (2nd ed.), MIT Press, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-262-09026-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-262-09026-1), [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0901762](https://mathscinet.ams.org/mathscinet-getitem?mr=0901762)
- Jeffrey, Alan (2010), *Matrix Operations for Engineers and Scientists: An Essential Guide in Linear Algebra*, Springer, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9789048192748](https://en.wikipedia.org/wiki/Special:BookSources/9789048192748)
- Johnston, Nathaniel (2021), *Introduction to Linear and Matrix Algebra*, Springer Nature, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9783030528119](https://en.wikipedia.org/wiki/Special:BookSources/9783030528119)
- Kreyszig, Erwin (1972), [Advanced Engineering Mathematics](https://archive.org/details/advancedengineer00krey) (3rd ed.), New York: [Wiley](https://en.wikipedia.org/wiki/John_Wiley_%26_Sons), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-50728-8](https://en.wikipedia.org/wiki/Special:BookSources/0-471-50728-8).
- Krzanowski, Wojtek J. (1988), *Principles of multivariate analysis*, Oxford Statistical Science Series, vol. 3, The Clarendon Press Oxford University Press, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-19-852211-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-19-852211-9), [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0969370](https://mathscinet.ams.org/mathscinet-getitem?mr=0969370)
- Lam, T. Y. (1999), *Lectures on Modules and Rings*, Graduate Texts in Mathematics, vol. 189, Springer-Verlag, New York, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-1-4612-0525-8](https://doi.org/10.1007%2F978-1-4612-0525-8), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-98428-3](https://en.wikipedia.org/wiki/Special:BookSources/0-387-98428-3), [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1653294](https://mathscinet.ams.org/mathscinet-getitem?mr=1653294)
- Lancaster, Peter; Tismenetsky, Miron (1985), *The Theory of Matrices: With Applications* (2nd ed.), Elsevier, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780080519081](https://en.wikipedia.org/wiki/Special:BookSources/9780080519081)
- [Lang, Serge](https://en.wikipedia.org/wiki/Serge_Lang) (1969), *Analysis II*, [Addison-Wesley](https://en.wikipedia.org/wiki/Addison-Wesley)
- [Lang, Serge](https://en.wikipedia.org/wiki/Serge_Lang) (1986), *Introduction to Linear Algebra* (2nd ed.), Springer, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9781461210702](https://en.wikipedia.org/wiki/Special:BookSources/9781461210702)
- Lang, Serge (1987), [Calculus of several variables](https://archive.org/details/calculusofsevera0000lang) (3rd ed.), Berlin, DE; New York, NY: Springer-Verlag, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-96405-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-96405-8)
- [Lang, Serge](https://en.wikipedia.org/wiki/Serge_Lang) (2002), *[Algebra](https://en.wikipedia.org/wiki/Algebra_(Lang))*, [Graduate Texts in Mathematics](https://en.wikipedia.org/wiki/Graduate_Texts_in_Mathematics), vol. 211 (Revised third ed.), New York: Springer-Verlag, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-95385-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-95385-4), [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1878556](https://mathscinet.ams.org/mathscinet-getitem?mr=1878556)
- Latouche, Guy; Ramaswami, Vaidyanathan (1999), *Introduction to matrix analytic methods in stochastic modeling* (1st ed.), Philadelphia, PA: Society for Industrial and Applied Mathematics, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-89871-425-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-89871-425-8)
- Manning, Christopher D.; Schütze, Hinrich (1999), *Foundations of statistical natural language processing*, MIT Press, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-262-13360-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-262-13360-9)
- Margalit, Dan; Rabinoff, Joseph (2019), ["Determinants and Volumes"](https://textbooks.math.gatech.edu/ila/determinants-volumes.html), *Interactive Linear Algebra*, Georgia Institute of Technology, retrieved 2025-05-10
- [Matoušek, Jiří](https://en.wikipedia.org/wiki/Ji%C5%99%C3%AD_Matou%C5%A1ek_(mathematician) "Jiří Matoušek (mathematician)"); Gärtner, Bernd (2007), *Understanding and Using Linear Programming*, Springer Science & Business Media, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9783540307174](https://en.wikipedia.org/wiki/Special:BookSources/9783540307174)
- Maxwell, E. A. (1969), *Algebraic Structure and Matrices, Being Part II of Advanced Algebra*, Cambridge University Press
- McHugh, Andrew (2025), *Finite Mathematics: An Introduction with Applications in Business, Social Sciences, and Music*, Academic Press, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780443290954](https://en.wikipedia.org/wiki/Special:BookSources/9780443290954)
- [Meckes, Elizabeth S.](https://en.wikipedia.org/wiki/Elizabeth_Meckes); Meckes, Mark W. (2018), *Linear Algebra*, Cambridge University Press, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9781316836026](https://en.wikipedia.org/wiki/Special:BookSources/9781316836026)
- Mehata, K. M.; Srinivasan, S. K. (1978), *Stochastic processes*, New York, NY: McGraw–Hill, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-07-096612-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-07-096612-3)
- Mello, David C. (2017), *Invitation to Linear Algebra*, Textbooks in Mathematics, CRC Press, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9781498779586](https://en.wikipedia.org/wiki/Special:BookSources/9781498779586)
- [Mirsky, Leonid](https://en.wikipedia.org/wiki/Leon_Mirsky) (1990), [An Introduction to Linear Algebra](https://books.google.com/books?id=ULMmheb26ZcC&q=linear+algebra+determinant&pg=PA1), Courier Dover Publications, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-486-66434-7](https://en.wikipedia.org/wiki/Special:BookSources/978-0-486-66434-7)
- Misra, Chandan; Bhattacharya, Sourangshu; Ghosh, Soumya K. (June 2022), "Stark: Fast and scalable Strassen's matrix multiplication using Apache Spark", *IEEE Transactions on Big Data*, **8** (3): 699–710, [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1811.07325](https://arxiv.org/abs/1811.07325), [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/tbdata.2020.2977326](https://doi.org/10.1109%2Ftbdata.2020.2977326)
- Nering, Evar D. (1970), *Linear Algebra and Matrix Theory* (2nd ed.), New York: [Wiley](https://en.wikipedia.org/wiki/John_Wiley_%26_Sons), [LCCN](https://en.wikipedia.org/wiki/LCCN_(identifier)) [76-91646](https://lccn.loc.gov/76-91646)
- Nocedal, Jorge; Wright, Stephen J. (2006), *Numerical Optimization* (2nd ed.), Berlin, DE; New York, NY: Springer-Verlag, p. 449, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-30303-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-30303-1)
- Oualline, Steve (2003), *Practical C++ programming*, [O'Reilly](https://en.wikipedia.org/wiki/O%27Reilly_Media), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-596-00419-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-596-00419-4)
- Perrone, Paolo (2024), [Starting Category Theory](https://www.worldscientific.com/worldscibooks/10.1142/13670), World Scientific, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1142/9789811286018_0005](https://doi.org/10.1142%2F9789811286018_0005), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-981-12-8600-1](https://en.wikipedia.org/wiki/Special:BookSources/978-981-12-8600-1)
- Pettofrezzo, Anthony J. (1978), *Matrices and Transformations*, Dover Books on Mathematics, Courier Corporation, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780486636344](https://en.wikipedia.org/wiki/Special:BookSources/9780486636344)
- Perlis, Sam (1991), [Theory of Matrices](https://books.google.com/books?id=5_sxtcnvLhoC&pg=PA103), Dover books on advanced mathematics, Courier Dover Corporation, p. 103, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-486-66810-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-486-66810-9)
- Pop; Furdui (2017), *Square Matrices of Order 2*, Springer International Publishing, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-319-54938-5](https://en.wikipedia.org/wiki/Special:BookSources/978-3-319-54938-5)
- Press, William H.; Flannery, Brian P.; [Teukolsky, Saul A.](https://en.wikipedia.org/wiki/Saul_Teukolsky); Vetterling, William T. (1992), ["LU Decomposition and Its Applications"](https://web.archive.org/web/20090906113144/http://www.mpi-hd.mpg.de/astrophysik/HEA/internal/Numerical_Recipes/f2-3.pdf) (PDF), *Numerical Recipes in FORTRAN: The Art of Scientific Computing* (2nd ed.), Cambridge University Press, pp. 34–42, archived from the original on 2009-09-06
- Protter, Murray H.; Morrey, Charles B. Jr. (1970), *College Calculus with Analytic Geometry* (2nd ed.), Reading: [Addison-Wesley](https://en.wikipedia.org/wiki/Addison-Wesley), [LCCN](https://en.wikipedia.org/wiki/LCCN_(identifier)) [76087042](https://lccn.loc.gov/76087042)
- Punnen, Abraham P.; Gutin, Gregory (2002), *The traveling salesman problem and its variations*, Boston, MA: Kluwer Academic Publishers, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4020-0664-7](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4020-0664-7)
- Ramachandra Rao, A.; Bhimasankaram, P. (2000), *Linear Algebra*, Texts and Readings in Mathematics, vol. 19 (2nd ed.), Springer, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9789386279019](https://en.wikipedia.org/wiki/Special:BookSources/9789386279019)
- Reutenauer, Christophe; Straubing, Howard (1984), "Inversion of matrices over a commutative semiring", *Journal of Algebra*, **88** (2): 350–360, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/0021-8693(84)90070-X](https://doi.org/10.1016%2F0021-8693%2884%2990070-X), [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0747520](https://mathscinet.ams.org/mathscinet-getitem?mr=0747520), [Zbl](https://en.wikipedia.org/wiki/Zbl_(identifier)) [0563.15011](https://zbmath.org/?format=complete&q=an:0563.15011)
- Reyes, Manuel (2025), "A tour of noncommutative spectral theories", *Notices of the American Mathematical Society*, **72** (2): 145–153, [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2409.08421](https://arxiv.org/abs/2409.08421), [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1090/noti3100](https://doi.org/10.1090%2Fnoti3100), [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [4854325](https://mathscinet.ams.org/mathscinet-getitem?mr=4854325)
- [Riehl, Emily](https://en.wikipedia.org/wiki/Emily_Riehl) (2016), [Category Theory in Context](https://books.google.com/books?id=6B9MDgAAQBAJ), Dover, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780486809038](https://en.wikipedia.org/wiki/Special:BookSources/9780486809038)
- Roth, Ron (2006), *Introduction to Coding Theory*, Cambridge University Press, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780521845045](https://en.wikipedia.org/wiki/Special:BookSources/9780521845045)
- Rowen, Louis Halle (2008), *Graduate Algebra: noncommutative view*, Providence, RI: [American Mathematical Society](https://en.wikipedia.org/wiki/American_Mathematical_Society), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8218-4153-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8218-4153-2)
- Schneider, Hans; Barker, George Phillip (2012), [Matrices and Linear Algebra](https://books.google.com/books?id=9vjBAgAAQBAJ&pg=PA251), Dover Books on Mathematics, Courier Dover Corporation, p. 251, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-486-13930-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-486-13930-2)
- Scott, J.; Tůma, M. (2023), "Sparse Matrices and Their Graphs", *Algorithms for Sparse Linear Systems*, Nečas Center Series, Cham: Birkhäuser, pp. 19–30, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-3-031-25820-6_2](https://doi.org/10.1007%2F978-3-031-25820-6_2), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-031-25819-0](https://en.wikipedia.org/wiki/Special:BookSources/978-3-031-25819-0)
- Serre, Denis (2007), *Matrices: Theory and Applications*, [Graduate Texts in Mathematics](https://en.wikipedia.org/wiki/Graduate_Texts_in_Mathematics), vol. 216, Springer Science & Business Media, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-1-4419-7683-3](https://doi.org/10.1007%2F978-1-4419-7683-3), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780387227580](https://en.wikipedia.org/wiki/Special:BookSources/9780387227580)
- Šolin, Pavel (2005), *Partial Differential Equations and the Finite Element Method*, [Wiley-Interscience](https://en.wikipedia.org/wiki/Wiley-Interscience), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-76409-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-76409-0)
- Stinson, Douglas R. (2005), *Cryptography*, Discrete Mathematics and its Applications, Chapman & Hall/CRC, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-58488-508-5](https://en.wikipedia.org/wiki/Special:BookSources/978-1-58488-508-5)
- Stoer, Josef; Bulirsch, Roland (2002), *Introduction to Numerical Analysis* (3rd ed.), Berlin, DE; New York, NY: Springer-Verlag, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-95452-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-95452-3)
- Suresh Kumar, K. S. (2009), *Electric Circuits and Networks*, Dorling Kindersley, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-81-317-1390-7](https://en.wikipedia.org/wiki/Special:BookSources/978-81-317-1390-7)
- Tang, K. T. (2006), *Mathematical Methods for Engineers and Scientists 1: Complex Analysis, Determinants and Matrices*, Springer, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-30273-5](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-30273-5)
- Tapp, Kristopher (2016), *Matrix Groups for Undergraduates*, Student Mathematical Library, vol. 79 (2nd ed.), Providence, Rhode Island: American Mathematical Society, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1090/stml/079](https://doi.org/10.1090%2Fstml%2F079), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4704-2722-1](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4704-2722-1), [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [3468869](https://mathscinet.ams.org/mathscinet-getitem?mr=3468869)
- [Van Loan, Charles F.](https://en.wikipedia.org/wiki/Charles_F._Van_Loan) (2000), "The ubiquitous Kronecker product", *[Journal of Computational and Applied Mathematics](https://en.wikipedia.org/wiki/Journal_of_Computational_and_Applied_Mathematics)*, **123** (1–2): 85–100, [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2000JCoAM.123...85L](https://ui.adsabs.harvard.edu/abs/2000JCoAM.123...85L), [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/S0377-0427(00)00393-9](https://doi.org/10.1016%2FS0377-0427%2800%2900393-9), [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1798520](https://mathscinet.ams.org/mathscinet-getitem?mr=1798520)
- Vassilevska Williams, Virginia; Xu, Yinzhan; Xu, Zixuan; Zhou, Renfei (2024), "New bounds for matrix multiplication: from alpha to omega", *Proceedings of the 2024 Annual ACM-SIAM Symposium on Discrete Algorithms (SODA)*, pp. 3792–3835, [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2307.07970](https://arxiv.org/abs/2307.07970), [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/1.9781611977912.134](https://doi.org/10.1137%2F1.9781611977912.134), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-61197-791-2](https://en.wikipedia.org/wiki/Special:BookSources/978-1-61197-791-2)
- Ward, J. P. (1997), [Quaternions and Cayley numbers](https://archive.org/details/quaternionscayle0000ward), Mathematics and its Applications, vol. 403, Dordrecht, NL: Kluwer Academic Publishers Group, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-94-011-5768-1](https://doi.org/10.1007%2F978-94-011-5768-1), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-7923-4513-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-7923-4513-8), [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1458894](https://mathscinet.ams.org/mathscinet-getitem?mr=1458894)
- Watkins, David S. (2002), [Fundamentals of Matrix Computations](https://books.google.com/books?id=xi5omWiQ-3kC), [John Wiley & Sons](https://en.wikipedia.org/wiki/John_Wiley_%26_Sons), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-46167-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-46167-8)
- [West, Douglas B.](https://en.wikipedia.org/wiki/Douglas_West_(mathematician) "Douglas West (mathematician)") (2020), *Combinatorial Mathematics*, Cambridge University Press, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9781108889520](https://en.wikipedia.org/wiki/Special:BookSources/9781108889520)
- Whitelaw, T. A. (1991), [Introduction to Linear Algebra](https://books.google.com/books?id=6M_kDzA7-qIC) (2nd ed.), CRC Press, p. 29, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780751401592](https://en.wikipedia.org/wiki/Special:BookSources/9780751401592)
- Zhang, Yanchun; Yu, Jeffrey Xu; Hou, Jingyu (2006), *Web Communities: Analysis and Construction*, Springer, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-27737-8](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-27737-8)

### Physics references

- Abłamowicz, Rafał (2000), *Clifford Algebras and their Applications in Mathematical Physics, Volume 1: Algebra and Physics*, Progress in Mathematical Physics, vol. 18, Birkhäuser / Springer, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780817641825](https://en.wikipedia.org/wiki/Special:BookSources/9780817641825)
- Bauchau, O. A.; Craig, J. I. (2009), *Structural Analysis: With Applications to Aerospace Structures*, Solid Mechanics and Its Applications, vol. 163, Springer, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9789048125166](https://en.wikipedia.org/wiki/Special:BookSources/9789048125166)
- [Boas, Mary L.](https://en.wikipedia.org/wiki/Mary_L._Boas) (2005), [*Mathematical Methods in the Physical Sciences*](https://en.wikipedia.org/wiki/Mathematical_Methods_in_the_Physical_Sciences) (3rd ed.), John Wiley & Sons, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-19826-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-19826-0)
- Bohm, Arno (2001), *Quantum Mechanics: Foundations and Applications*, Springer, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-95330-2](https://en.wikipedia.org/wiki/Special:BookSources/0-387-95330-2)
- Burgess, Cliff; Moore, Guy (2007), *The Standard Model. A Primer*, Cambridge University Press, [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2007smp..book.....B](https://ui.adsabs.harvard.edu/abs/2007smp..book.....B), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-86036-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-86036-9)
- [Gbur, Greg](https://en.wikipedia.org/wiki/Greg_Gbur) (2011), *Mathematical Methods in Optical Physics and Engineering*, Cambridge University Press, [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2011mmop.book.....G](https://ui.adsabs.harvard.edu/abs/2011mmop.book.....G), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-51610-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-51610-5)
- Guenther, Robert D. (1990), *Modern Optics*, John Wiley, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-60538-7](https://en.wikipedia.org/wiki/Special:BookSources/0-471-60538-7)
- Han, D.; Kim, Y. S.; Noz, Marilyn E. (September 1997), ["Jones-matrix formalism as a representation of the Lorentz group"](https://scholar.archive.org/work/g6cqiliqqrcjxalo44oayibjw4), *Journal of the Optical Society of America A*, **14** (9), Optica Publishing Group: 2290, [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[physics/9703032](https://arxiv.org/abs/physics/9703032), [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1997JOSAA..14.2290H](https://ui.adsabs.harvard.edu/abs/1997JOSAA..14.2290H), [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1364/josaa.14.002290](https://doi.org/10.1364%2Fjosaa.14.002290)
- [Itzykson, Claude](https://en.wikipedia.org/wiki/Claude_Itzykson); [Zuber, Jean-Bernard](https://en.wikipedia.org/wiki/Jean-Bernard_Zuber) (1980), [Quantum Field Theory](https://archive.org/details/quantumfieldtheo0000itzy), McGraw–Hill, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-07-032071-3](https://en.wikipedia.org/wiki/Special:BookSources/0-07-032071-3)
- Jensen, Frank (1999), [Introduction to Computational Chemistry](https://archive.org/details/introductiontoco0000jens), John Wiley & Sons, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-98085-4](https://en.wikipedia.org/wiki/Special:BookSources/0-471-98085-4)
- [Peres, Asher](https://en.wikipedia.org/wiki/Asher_Peres) (1993), [*Quantum Theory: Concepts and Methods*](https://en.wikipedia.org/wiki/Quantum_Theory:_Concepts_and_Methods), Kluwer, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-7923-3632-7](https://en.wikipedia.org/wiki/Special:BookSources/978-0-7923-3632-7)
- [Reichl, Linda E.](https://en.wikipedia.org/wiki/Linda_Reichl) (2004), *The transition to chaos: conservative classical systems and quantum manifestations*, Berlin, DE; New York, NY: Springer-Verlag, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-98788-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-98788-0)
- [Riley, Kenneth F.](https://en.wikipedia.org/wiki/Ken_Riley_(physicist) "Ken Riley (physicist)"); Hobson, Michael P.; Bence, Stephen J. (1997), *Mathematical methods for physics and engineering*, Cambridge University Press, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-55506-X](https://en.wikipedia.org/wiki/Special:BookSources/0-521-55506-X)
- [Schiff, Leonard I.](https://en.wikipedia.org/wiki/Leonard_I._Schiff) (1968), *Quantum Mechanics* (3rd ed.), McGraw–Hill
- [Weinberg, Steven](https://en.wikipedia.org/wiki/Steven_Weinberg) (1995), [The Quantum Theory of Fields. Volume I: Foundations](https://archive.org/details/quantumtheoryoff00stev), Cambridge University Press, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-55001-7](https://en.wikipedia.org/wiki/Special:BookSources/0-521-55001-7)
- Wherrett, Brian S. (1987), *Group Theory for Atoms, Molecules and Solids*, Prentice–Hall International, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-13-365461-3](https://en.wikipedia.org/wiki/Special:BookSources/0-13-365461-3)
- Ydri, Badis (2016), *Lectures on Matrix Field Theory*, Lecture Notes in Physics, vol. 929, Springer, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9783319460031](https://en.wikipedia.org/wiki/Special:BookSources/9783319460031)
- Zabrodin, Anton; [Brézin, Édouard](https://en.wikipedia.org/wiki/%C3%89douard_Br%C3%A9zin); Kazakov, Vladimir; Serban, Didina; [Wiegmann, Paul](https://en.wikipedia.org/wiki/Paul_Wiegmann) (2006), *Applications of Random Matrices in Physics (NATO Science Series II: Mathematics, Physics and Chemistry)*, Berlin, DE; New York, NY: [Springer-Verlag](https://en.wikipedia.org/wiki/Springer-Verlag), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4020-4530-1](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4020-4530-1)

### Historical references

- [Bôcher, Maxime](https://en.wikipedia.org/wiki/Maxime_B%C3%B4cher) (2004), *Introduction to Higher Algebra*, New York, NY: [Dover Publications](https://en.wikipedia.org/wiki/Dover_Publications), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-486-49570-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-486-49570-5), reprint of the 1907 original edition
- [Cayley, Arthur](https://en.wikipedia.org/wiki/Arthur_Cayley) (December 1858), "A memoir on the theory of matrices", *[Philosophical Transactions of the Royal Society of London](https://en.wikipedia.org/wiki/Philosophical_Transactions_of_the_Royal_Society_of_London)*, **148**: 17–37, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1098/rstl.1858.0002](https://doi.org/10.1098%2Frstl.1858.0002), [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [108649](https://www.jstor.org/stable/108649); reprinted in *The collected mathematical papers of Arthur Cayley*, vol. II, Cambridge University Press, 1889, [pp. 475–496](https://archive.org/details/collectedmathema02cayluoft/page/474).
- [Cayley, Arthur](https://en.wikipedia.org/wiki/Arthur_Cayley) (1889), [The collected mathematical papers of Arthur Cayley](https://quod.lib.umich.edu/cgi/t/text/pageviewer-idx?c=umhistmath;cc=umhistmath;rgn=full%20text;idno=ABS3153.0001.001;didno=ABS3153.0001.001;view=image;seq=00000140), vol. I (1841–1853), [Cambridge University Press](https://en.wikipedia.org/wiki/Cambridge_University_Press), pp. 123–126
- [Cramer, Gabriel](https://en.wikipedia.org/wiki/Gabriel_Cramer) (1750), [Introduction à l'Analyse des lignes Courbes algébriques](https://www.europeana.eu/resolve/record/03486/E71FE3799CEC1F8E2B76962513829D2E36B63015) (in French), Geneva: Europeana, pp. 656–659, retrieved 2012-05-18
- [Dieudonné, Jean](https://en.wikipedia.org/wiki/Jean_Dieudonn%C3%A9), ed. (1978), *Abrégé d'histoire des mathématiques 1700-1900*, Paris, FR: Hermann
- [Hawkins, Thomas](https://en.wikipedia.org/wiki/Thomas_W._Hawkins_Jr.) (1972), "Hypercomplex numbers, Lie groups, and the creation of group representation theory", *[Archive for History of Exact Sciences](https://en.wikipedia.org/wiki/Archive_for_History_of_Exact_Sciences)*, **8** (4): 243–287, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/bf00328434](https://doi.org/10.1007%2Fbf00328434)
- [Hawkins, Thomas](https://en.wikipedia.org/wiki/Thomas_W._Hawkins_Jr.) (1975), "Cauchy and the spectral theory of matrices", *[Historia Mathematica](https://en.wikipedia.org/wiki/Historia_Mathematica)*, **2**: 1–29, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/0315-0860(75)90032-4](https://doi.org/10.1016%2F0315-0860%2875%2990032-4), [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0469635](https://mathscinet.ams.org/mathscinet-getitem?mr=0469635)
- [Knobloch, Eberhard](https://en.wikipedia.org/wiki/Eberhard_Knobloch) (1994), "From Gauß to Weierstraß: determinant theory and its historical evaluations", in Sasaki, Chikara; Sugiura, Mitsuo; Dauben, Joseph W. (eds.), *The Intersection of History and Mathematics*, Science Networks: Historical Studies, vol. 15, Birkhäuser, pp. 51–66, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-3-0348-7521-9_5](https://doi.org/10.1007%2F978-3-0348-7521-9_5), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [3-7643-5029-6](https://en.wikipedia.org/wiki/Special:BookSources/3-7643-5029-6), [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1308079](https://mathscinet.ams.org/mathscinet-getitem?mr=1308079)
- Kosinski, A. A. (2001), "Cramer's Rule is due to Cramer", *[Mathematics Magazine](https://en.wikipedia.org/wiki/Mathematics_Magazine)*, **74** (4): 310–312, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2691101](https://doi.org/10.2307%2F2691101), [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2691101](https://www.jstor.org/stable/2691101)
- [Kronecker, Leopold](https://en.wikipedia.org/wiki/Leopold_Kronecker) (1897), [Hensel, Kurt](https://en.wikipedia.org/wiki/Kurt_Hensel) (ed.), [Leopold Kronecker's Werke](https://quod.lib.umich.edu/cgi/t/text/text-idx?c=umhistmath;idno=AAS8260.0002.001), Teubner
- [Miller, G. A.](https://en.wikipedia.org/wiki/George_Abram_Miller) (May 1930), "On the history of determinants", *[The American Mathematical Monthly](https://en.wikipedia.org/wiki/The_American_Mathematical_Monthly)*, **37** (5): 216–219, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/00029890.1930.11987058](https://doi.org/10.1080%2F00029890.1930.11987058), [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2299112](https://www.jstor.org/stable/2299112)
- Shen, Kangshen; [Crossley, John N.](https://en.wikipedia.org/wiki/John_Newsome_Crossley); Lun, Anthony Wah-Cheung (1999), *Nine Chapters of the Mathematical Art, Companion and Commentary* (2nd ed.), [Oxford University Press](https://en.wikipedia.org/wiki/Oxford_University_Press), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-19-853936-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-19-853936-0)
- [Sylvester, J. J.](https://en.wikipedia.org/wiki/James_Joseph_Sylvester) (1904), [Baker, H. F.](https://en.wikipedia.org/wiki/Henry_F._Baker) (ed.), [The Collected Mathematical Papers of James Joseph Sylvester, Volume I (1837–1853)](https://archive.org/details/collectedmathem01sylvrich), Cambridge, England: Cambridge University Press
- [van der Waerden, B. L.](https://en.wikipedia.org/wiki/Bartel_Leendert_van_der_Waerden), ed. (2007) \[1968\], *Sources of Quantum Mechanics*, Dover, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-486-45892-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-486-45892-2)
- [Tarski, Alfred](https://en.wikipedia.org/wiki/Alfred_Tarski) (1941), *Introduction to Logic and the Methodology of Deductive Sciences*, Oxford University Press, [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0003375](https://mathscinet.ams.org/mathscinet-getitem?mr=0003375); reprint of 1946 corrected printing, Dover Publications, 1995, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-486-28462-X](https://en.wikipedia.org/wiki/Special:BookSources/0-486-28462-X)
- [Weierstrass, Karl](https://en.wikipedia.org/wiki/Karl_Weierstrass) (1915), [Collected Works](https://quod.lib.umich.edu/cgi/t/text/text-idx?c=umhistmath;idno=AAN8481.0003.001), vol. 3

## Further reading

- ["Matrix"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society), 2001 \[1994\]
- Petersen, Kaare Brandt; Petersen, Michael Syskind (November 15, 2012), [The Matrix Cookbook](https://math.uwaterloo.ca/~hwolkowi//matrixcookbook.pdf) (PDF), University of Waterloo, retrieved 24 March 2014
- Brookes, Mike (2005), [The Matrix Reference Manual](https://web.archive.org/web/20081216124433/http://www.ee.ic.ac.uk/hp/staff/dmb/matrix/intro.html), London: [Imperial College](https://en.wikipedia.org/wiki/Imperial_College), archived from [the original](https://ee.ic.ac.uk/hp/staff/dmb/matrix/intro.html) on 16 December 2008, retrieved 10 Dec 2008

## External links

- O'Connor, J. J.; Robertson, E. F. (February 1996), ["Matrices and determinants"](https://mathshistory.st-andrews.ac.uk/HistTopics/Matrices_and_determinants/), *[MacTutor History of Mathematics Archive](https://en.wikipedia.org/wiki/MacTutor_History_of_Mathematics_Archive)*, [University of St Andrews](https://en.wikipedia.org/wiki/University_of_St_Andrews)
- [Matrices and Linear Algebra on the Earliest Uses Pages](https://economics.soton.ac.uk/staff/aldrich/matrices.htm)
- [Earliest Uses of Symbols for Matrices and Vectors](https://jeff560.tripod.com/matrices.html)
