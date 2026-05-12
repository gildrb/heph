[[linear-algebra.base]]

> Source: [[Matrix Multiplication]]
> License: Wikipedia content is available under CC BY-SA 4.0.

![[media/d35e26a39fbcd8adbfaa0cef521b074dad98d2ad.png]]
For matrix multiplication, the number of columns in the first matrix must be equal to the number of rows in the second matrix. The result matrix has the number of rows of the first and the number of columns of the second matrix.

In [mathematics](https://en.wikipedia.org/wiki/Mathematics), specifically in [linear algebra](https://en.wikipedia.org/wiki/Linear_algebra), **matrix multiplication** is a [binary operation](https://en.wikipedia.org/wiki/Binary_operation) that produces a [matrix](https://en.wikipedia.org/wiki/Matrix_(mathematics) "Matrix (mathematics)") from two matrices. For matrix multiplication, the number of columns in the first matrix must be equal to the number of rows in the second matrix. The resulting matrix, known as the **matrix product**, has the number of rows of the first and the number of columns of the second matrix. The product of matrices **A** and **B** is denoted as **AB**.

Matrix multiplication was first described by the French mathematician [Jacques Philippe Marie Binet](https://en.wikipedia.org/wiki/Jacques_Philippe_Marie_Binet) in 1812, to represent the [composition](https://en.wikipedia.org/wiki/Composition_of_functions) of [linear maps](https://en.wikipedia.org/wiki/Linear_map) that are represented by matrices. Matrix multiplication is thus a basic tool of [linear algebra](https://en.wikipedia.org/wiki/Linear_algebra), and as such has numerous applications in many areas of mathematics, as well as in [applied mathematics](https://en.wikipedia.org/wiki/Applied_mathematics), [statistics](https://en.wikipedia.org/wiki/Statistics), [physics](https://en.wikipedia.org/wiki/Physics), [economics](https://en.wikipedia.org/wiki/Economics), and [engineering](https://en.wikipedia.org/wiki/Engineering). Computing matrix products is a central operation in all computational applications of linear algebra.

## Notation

This article will use the following notational conventions: matrices are represented by capital letters in bold, e.g. **A**; [vectors](https://en.wikipedia.org/wiki/Euclidean_vector) in lowercase bold, e.g. **a**; and entries of vectors and matrices are italic (they are numbers from a field), e.g. *A* and *a*. [Index notation](https://en.wikipedia.org/wiki/Index_notation) is often the clearest way to express definitions, and is used as standard in the literature. The entry in row i, column j of matrix **A** is indicated by (**A**)<sub>*ij*</sub>, *A*<sub>*ij*</sub> or *a*<sub>*ij*</sub>. In contrast, a single subscript, e.g. **A**<sub>1</sub>, **A**<sub>2</sub>, is used to select a matrix (not a matrix entry) from a collection of matrices.

## Definitions

### Matrix times matrix

If **A** is an *m* × *n* matrix and **B** is an *n* × *p* matrix, 

$$
\mathbf {A} ={\begin{pmatrix}a_{11}&a_{12}&\cdots &a_{1n}\\a_{21}&a_{22}&\cdots &a_{2n}\\\vdots &\vdots &\ddots &\vdots \\a_{m1}&a_{m2}&\cdots &a_{mn}\\\end{pmatrix}},\quad \mathbf {B} ={\begin{pmatrix}b_{11}&b_{12}&\cdots &b_{1p}\\b_{21}&b_{22}&\cdots &b_{2p}\\\vdots &\vdots &\ddots &\vdots \\b_{n1}&b_{n2}&\cdots &b_{np}\\\end{pmatrix}}
$$

 the *matrix product* **C** = **AB** (denoted without multiplication signs or dots) is defined to be the *m* × *p* matrix 

$$
\mathbf {C} ={\begin{pmatrix}c_{11}&c_{12}&\cdots &c_{1p}\\c_{21}&c_{22}&\cdots &c_{2p}\\\vdots &\vdots &\ddots &\vdots \\c_{m1}&c_{m2}&\cdots &c_{mp}\\\end{pmatrix}}
$$

 such that 

$$
c_{ij}=a_{i1}b_{1j}+a_{i2}b_{2j}+\cdots +a_{in}b_{nj}=\sum _{k=1}^{n}a_{ik}b_{kj},
$$

 for *i* = 1, ..., *m* and *j* = 1, ..., *p*.

That is, the entry $c_{ij}$ of the product is obtained by multiplying term-by-term the entries of the ith row of **A** and the jth column of **B**, and summing these n products. In other words, $c_{ij}$ is the [dot product](https://en.wikipedia.org/wiki/Dot_product) of the ith row of **A** and the jth column of **B**.

Therefore, **AB** can also be written as 

$$
\mathbf {C} ={\begin{pmatrix}a_{11}b_{11}+\cdots +a_{1n}b_{n1}&a_{11}b_{12}+\cdots +a_{1n}b_{n2}&\cdots &a_{11}b_{1p}+\cdots +a_{1n}b_{np}\\a_{21}b_{11}+\cdots +a_{2n}b_{n1}&a_{21}b_{12}+\cdots +a_{2n}b_{n2}&\cdots &a_{21}b_{1p}+\cdots +a_{2n}b_{np}\\\vdots &\vdots &\ddots &\vdots \\a_{m1}b_{11}+\cdots +a_{mn}b_{n1}&a_{m1}b_{12}+\cdots +a_{mn}b_{n2}&\cdots &a_{m1}b_{1p}+\cdots +a_{mn}b_{np}\\\end{pmatrix}}
$$

Thus the product **AB** is defined if and only if the number of columns in **A** equals the number of rows in **B**, in this case *n*.

In most scenarios, the entries are numbers, but they may be any kind of [mathematical objects](https://en.wikipedia.org/wiki/Mathematical_object) for which an addition and a multiplication are defined, that are [associative](https://en.wikipedia.org/wiki/Associative_property), and such that the addition is [commutative](https://en.wikipedia.org/wiki/Commutative_property), and the multiplication is [distributive](https://en.wikipedia.org/wiki/Distributive_property) with respect to the addition. In particular, the entries may be matrices themselves (see [block matrix](https://en.wikipedia.org/wiki/Block_matrix)).

### Matrix times vector

A vector $\mathbf {x}$ of length $n$ can be viewed as a [column vector](https://en.wikipedia.org/wiki/Column_vector), corresponding to an $n\times 1$ matrix $\mathbf {X}$ whose entries are given by $\mathbf {X} _{i1}=\mathbf {x} _{i}.$ If $\mathbf {A}$ is an $m\times n$ matrix, the matrix-times-vector product denoted by $\mathbf {Ax}$ is then the vector $\mathbf {y}$ that, viewed as a column vector, is equal to the $m\times 1$ matrix $\mathbf {AX} .$ In index notation, this amounts to:

$y_{i}=\sum _{j=1}^{n}a_{ij}x_{j}.$

One way of looking at this is that the changes from "plain" vector to column vector and back are assumed and left implicit.

### Vector times matrix

Similarly, a vector $\mathbf {x}$ of length $n$ can be viewed as a [row vector](https://en.wikipedia.org/wiki/Row_vector), corresponding to a $1\times n$ matrix. To make it clear that a row vector is meant, it is customary in this context to represent it as the [transpose](https://en.wikipedia.org/wiki/Transpose) of a column vector; thus, one will see notations such as $\mathbf {x} ^{\mathrm {T} }\mathbf {A} .$ The identity $\mathbf {x} ^{\mathrm {T} }\mathbf {A} =(\mathbf {A} ^{\mathrm {T} }\mathbf {x} )^{\mathrm {T} }$ holds. In index notation, if $\mathbf {A}$ is an $n\times p$ matrix, $\mathbf {x} ^{\mathrm {T} }\mathbf {A} =\mathbf {y} ^{\mathrm {T} }$ amounts to: $y_{k}=\sum _{j=1}^{n}x_{j}a_{jk}.$

### Vector times vector

A vector with n components can be represented as a *1* × *n* matrix (a row-vector) or as a *n* × *1* matrix (a column-vector). Assuming that $\mathbf {a}$ and $\mathbf {b}$ are both column-vectors the [dot product](https://en.wikipedia.org/wiki/Dot_product) (or inner product) $\mathbf {a} \cdot \mathbf {b}$ is equal to the single entry of the $1\times 1$ matrix resulting from the matrix multiplication of the row-vector $\mathbf {a} ^{\mathrm {T} }$ with the column-vector $\mathbf {b}$, i.e. $\mathbf {a} ^{\mathrm {T} }\mathbf {b}$.

The matrix multiplication between the column-vector $\mathbf {a}$ and the row-vector $\mathbf {b} ^{\mathrm {T} }$, also known as outer-product $\mathbf {a} \mathbf {b} ^{\mathrm {T} }$, will, instead, give a *n* × *n* matrix.

### Illustration

![[media/df133f79b32438ac6732e482e6dc178f6bd61d94.png]]

The figure to the right illustrates diagrammatically the product of two matrices **A** and **B**, showing how each intersection in the product matrix corresponds to a row of **A** and a column of **B**. 

$$
{\overset {4\times 2{\text{ matrix}}}{\begin{bmatrix}a_{11}&a_{12}\\\cdot &\cdot \\a_{31}&a_{32}\\\cdot &\cdot \\\end{bmatrix}}}{\overset {2\times 3{\text{ matrix}}}{\begin{bmatrix}\cdot &b_{12}&b_{13}\\\cdot &b_{22}&b_{23}\\\end{bmatrix}}}={\overset {4\times 3{\text{ matrix}}}{\begin{bmatrix}\cdot &c_{12}&\cdot \\\cdot &\cdot &\cdot \\\cdot &\cdot &c_{33}\\\cdot &\cdot &\cdot \\\end{bmatrix}}}
$$

The values at the intersections, marked with circles in figure to the right, are: 

$$
{\begin{aligned}c_{12}&=a_{11}b_{12}+a_{12}b_{22}\\c_{33}&=a_{31}b_{13}+a_{32}b_{23}.\end{aligned}}
$$

## Fundamental applications

Historically, matrix multiplication has been introduced for facilitating and clarifying computations in [linear algebra](https://en.wikipedia.org/wiki/Linear_algebra). This strong relationship between matrix multiplication and linear algebra remains fundamental in all mathematics, as well as in [physics](https://en.wikipedia.org/wiki/Physics), [chemistry](https://en.wikipedia.org/wiki/Chemistry), [engineering](https://en.wikipedia.org/wiki/Engineering) and [computer science](https://en.wikipedia.org/wiki/Computer_science).

### Linear maps

If a [[Vector Space]] has a finite [basis](https://en.wikipedia.org/wiki/Basis_(linear_algebra) "Basis (linear algebra)"), its vectors are each uniquely represented by a finite [sequence](https://en.wikipedia.org/wiki/Sequence_(mathematics)) of scalars, called a [coordinate vector](https://en.wikipedia.org/wiki/Coordinate_vector), whose elements are the [coordinates](https://en.wikipedia.org/wiki/Coordinates) of the vector on the basis. These coordinate vectors form another vector space, which is [isomorphic](https://en.wikipedia.org/wiki/Isomorphism) to the original vector space. A coordinate vector is commonly organized as a [column matrix](https://en.wikipedia.org/wiki/Column_matrix) (also called a *column vector*), which is a matrix with only one column. So, a column vector represents both a coordinate vector, and a vector of the original vector space.

A [linear map](https://en.wikipedia.org/wiki/Linear_map) A from a vector space of dimension n into a vector space of dimension m maps a column vector

$\mathbf {x} ={\begin{pmatrix}x_{1}\\x_{2}\\\vdots \\x_{n}\end{pmatrix}}$

onto the column vector

$\mathbf {y} =A(\mathbf {x} )={\begin{pmatrix}a_{11}x_{1}+\cdots +a_{1n}x_{n}\\a_{21}x_{1}+\cdots +a_{2n}x_{n}\\\vdots \\a_{m1}x_{1}+\cdots +a_{mn}x_{n}\end{pmatrix}}.$

The linear map A is thus defined by the matrix

$\mathbf {A} ={\begin{pmatrix}a_{11}&a_{12}&\cdots &a_{1n}\\a_{21}&a_{22}&\cdots &a_{2n}\\\vdots &\vdots &\ddots &\vdots \\a_{m1}&a_{m2}&\cdots &a_{mn}\\\end{pmatrix}},$

and maps the column vector $\mathbf {x}$ to the matrix product

$\mathbf {y} =\mathbf {Ax} .$

If B is another linear map from the preceding vector space of dimension m, into a vector space of dimension p, it is represented by a $p\times m$ matrix $\mathbf {B} .$ A straightforward computation shows that the matrix of the [composite map](https://en.wikipedia.org/wiki/Function_composition) $B\circ A$ is the matrix product $\mathbf {BA} .$ The general formula $(B\circ A)(\mathbf {x} )=B(A(\mathbf {x} ))$) that defines the function composition is instanced here as a specific case of associativity of matrix product (see [§ Associativity](#Associativity) below):

$(\mathbf {BA} )\mathbf {x} =\mathbf {B} (\mathbf {Ax} )=\mathbf {BAx} .$

#### Geometric rotations

Using a [Cartesian coordinate](https://en.wikipedia.org/wiki/Cartesian_coordinate) system in a Euclidean plane, the [rotation](https://en.wikipedia.org/wiki/Rotation_(mathematics) "Rotation (mathematics)") by an angle $\alpha$ around the [origin](https://en.wikipedia.org/wiki/Origin_(mathematics) "Origin (mathematics)") is a linear map. More precisely, 

$$
{\begin{bmatrix}x'\\y'\end{bmatrix}}={\begin{bmatrix}\cos \alpha &-\sin \alpha \\\sin \alpha &\cos \alpha \end{bmatrix}}{\begin{bmatrix}x\\y\end{bmatrix}},
$$

 where the source point $(x,y)$ and its image $(x',y')$ are written as column vectors.

The composition of the rotation by $\alpha$ and that by $\beta$ then corresponds to the matrix product 

$$
{\begin{bmatrix}\cos \beta &-\sin \beta \\\sin \beta &\cos \beta \end{bmatrix}}{\begin{bmatrix}\cos \alpha &-\sin \alpha \\\sin \alpha &\cos \alpha \end{bmatrix}}={\begin{bmatrix}\cos \beta \cos \alpha -\sin \beta \sin \alpha &-\cos \beta \sin \alpha -\sin \beta \cos \alpha \\\sin \beta \cos \alpha +\cos \beta \sin \alpha &-\sin \beta \sin \alpha +\cos \beta \cos \alpha \end{bmatrix}}={\begin{bmatrix}\cos(\alpha +\beta )&-\sin(\alpha +\beta )\\\sin(\alpha +\beta )&\cos(\alpha +\beta )\end{bmatrix}},
$$

 where appropriate [trigonometric identities](https://en.wikipedia.org/wiki/List_of_trigonometric_identities#Angle_sum_and_difference_identities) are employed for the second equality. That is, the composition corresponds to the rotation by angle $\alpha +\beta$, as expected.

#### Resource allocation in economics

![[media/568f9fad1909c0181050fb6b041b98af4ce79ddd.png]]
The computation of the bottom left entry of $\mathbf {AB}$ corresponds to the consideration of all paths (highlighted) from basic commodity $b_{4}$ to final product $f_{1}$ in the production flow graph.

As an example, a fictitious factory uses 4 kinds of [basic commodities](https://en.wikipedia.org/wiki/Primary_commodity), $b_{1},b_{2},b_{3},b_{4}$ to produce 3 kinds of [intermediate goods](https://en.wikipedia.org/wiki/Intermediate_good), $m_{1},m_{2},m_{3}$, which in turn are used to produce 3 kinds of [final products](https://en.wikipedia.org/wiki/Final_product), $f_{1},f_{2},f_{3}$. The matrices

$\mathbf {A} ={\begin{pmatrix}1&0&1\\2&1&1\\0&1&1\\1&1&2\\\end{pmatrix}}$   and   $\mathbf {B} ={\begin{pmatrix}1&2&1\\2&3&1\\4&2&2\\\end{pmatrix}}$

provide the amount of basic commodities needed for a given amount of intermediate goods, and the amount of intermediate goods needed for a given amount of final products, respectively. For example, to produce one unit of intermediate good $m_{1}$, one unit of basic commodity $b_{1}$, two units of $b_{2}$, no units of $b_{3}$, and one unit of $b_{4}$ are needed, corresponding to the first column of $\mathbf {A}$.

Using matrix multiplication, compute

$\mathbf {AB} ={\begin{pmatrix}5&4&3\\8&9&5\\\ 6&5&3\\11&9&6\\\end{pmatrix}};$

this matrix directly provides the amounts of basic commodities needed for given amounts of final goods. For example, the bottom left entry of $\mathbf {AB}$ is computed as $1\cdot 1+1\cdot 2+2\cdot 4=11$, reflecting that $11$ units of $b_{4}$ are needed to produce one unit of $f_{1}$. Indeed, one $b_{4}$ unit is needed for $m_{1}$, one for each of two $m_{2}$, and $2$ for each of the four $m_{3}$ units that go into the $f_{1}$ unit, see picture.

In order to produce e.g. 100 units of the final product $f_{1}$, 80 units of $f_{2}$, and 60 units of $f_{3}$, the necessary amounts of basic goods can be computed as

$(\mathbf {AB} ){\begin{pmatrix}100\\80\\60\\\end{pmatrix}}={\begin{pmatrix}1000\\1820\\1180\\2180\end{pmatrix}},$

that is, $1000$ units of $b_{1}$, $1820$ units of $b_{2}$, $1180$ units of $b_{3}$, $2180$ units of $b_{4}$ are needed. Similarly, the product matrix $\mathbf {AB}$ can be used to compute the needed amounts of basic goods for other final-good amount data.

### System of linear equations

The general form of a [system of linear equations](https://en.wikipedia.org/wiki/System_of_linear_equations) is

${\begin{matrix}a_{11}x_{1}+\cdots +a_{1n}x_{n}=b_{1},\\a_{21}x_{1}+\cdots +a_{2n}x_{n}=b_{2},\\\vdots \\a_{m1}x_{1}+\cdots +a_{mn}x_{n}=b_{m}.\end{matrix}}$

Using same notation as above, such a system is equivalent with the single matrix [equation](https://en.wikipedia.org/wiki/Equation)

$\mathbf {Ax} =\mathbf {b} .$

### Dot product, bilinear form and sesquilinear form

The [dot product](https://en.wikipedia.org/wiki/Dot_product) of two column vectors is the unique entry of the matrix product

$\mathbf {x} ^{\mathsf {T}}\mathbf {y} ,$

where $\mathbf {x} ^{\mathsf {T}}$ is the [row vector](https://en.wikipedia.org/wiki/Row_vector) obtained by [transposing](https://en.wikipedia.org/wiki/Transpose) $\mathbf {x}$. (As usual, a 1×1 matrix is identified with its unique entry.)

More generally, any [bilinear form](https://en.wikipedia.org/wiki/Bilinear_form) over a vector space of finite dimension may be expressed as a matrix product

$\mathbf {x} ^{\mathsf {T}}\mathbf {Ay} ,$

and any [sesquilinear form](https://en.wikipedia.org/wiki/Sesquilinear_form) may be expressed as

$\mathbf {x} ^{\dagger }\mathbf {Ay} ,$

where $\mathbf {x} ^{\dagger }$ denotes the [conjugate transpose](https://en.wikipedia.org/wiki/Conjugate_transpose) of $\mathbf {x}$ (conjugate of the transpose, or equivalently transpose of the conjugate).

## General properties

Matrix multiplication shares some properties with usual [multiplication](https://en.wikipedia.org/wiki/Multiplication). However, matrix multiplication is not defined if the number of columns of the first factor differs from the number of rows of the second factor, and it is [non-commutative](https://en.wikipedia.org/wiki/Non-commutative), even when the product remains defined after changing the order of the factors.

### Non-commutativity

An operation is [commutative](https://en.wikipedia.org/wiki/Commutative_property) if, given two elements **A** and **B** such that the product $\mathbf {A} \mathbf {B}$ is defined, then $\mathbf {B} \mathbf {A}$ is also defined, and $\mathbf {A} \mathbf {B} =\mathbf {B} \mathbf {A} .$

If **A** and **B** are matrices of respective sizes $m\times n$ and $p\times q$, then $\mathbf {A} \mathbf {B}$ is defined if $n=p$, and $\mathbf {B} \mathbf {A}$ is defined if $m=q$. Therefore, if one of the products is defined, the other one need not be defined. If $m=q\neq n=p$, the two products are defined, but have different sizes; thus they cannot be equal. Only if $m=q=n=p$, that is, if **A** and **B** are [square matrices](https://en.wikipedia.org/wiki/Square_matrices) of the same size, are both products defined and of the same size. Even in this case, one has in general

$\mathbf {A} \mathbf {B} \neq \mathbf {B} \mathbf {A} .$

For example

${\begin{pmatrix}0&1\\0&0\end{pmatrix}}{\begin{pmatrix}0&0\\1&0\end{pmatrix}}={\begin{pmatrix}1&0\\0&0\end{pmatrix}},$

but

${\begin{pmatrix}0&0\\1&0\end{pmatrix}}{\begin{pmatrix}0&1\\0&0\end{pmatrix}}={\begin{pmatrix}0&0\\0&1\end{pmatrix}}.$

This example may be expanded for showing that, if **A** is a $n\times n$ matrix with entries in a [field](https://en.wikipedia.org/wiki/Field_(mathematics) "Field (mathematics)") F, then $\mathbf {A} \mathbf {B} =\mathbf {B} \mathbf {A}$ for every $n\times n$ matrix **B** with entries in F, [if and only if](https://en.wikipedia.org/wiki/If_and_only_if) $\mathbf {A} =c\,\mathbf {I}$ where $c\in F$, and **I** is the $n\times n$ [identity matrix](https://en.wikipedia.org/wiki/Identity_matrix). If, instead of a field, the entries are supposed to belong to a [ring](https://en.wikipedia.org/wiki/Ring_(mathematics) "Ring (mathematics)"), then one must add the condition that c belongs to the [center](https://en.wikipedia.org/wiki/Center_(ring_theory) "Center (ring theory)") of the ring.

One special case where commutativity does occur is when **D** and **E** are two (square) [diagonal matrices](https://en.wikipedia.org/wiki/Diagonal_matrices) (of the same size); then **DE** = **ED**. Again, if the matrices are over a general ring rather than a field, the corresponding entries in each must also commute with each other for this to hold.

### Distributivity

The matrix product is [distributive](https://en.wikipedia.org/wiki/Distributive_property) with respect to [matrix addition](https://en.wikipedia.org/wiki/Matrix_addition). That is, if **A**, **B**, **C**, **D** are matrices of respective sizes *m* × *n*, *n* × *p*, *n* × *p*, and *p* × *q*, respectively, one has (left distributivity)

$\mathbf {A} (\mathbf {B} +\mathbf {C} )=\mathbf {AB} +\mathbf {AC} ,$

and (right distributivity)

$(\mathbf {B} +\mathbf {C} )\mathbf {D} =\mathbf {BD} +\mathbf {CD} .$

This results from the distributivity for coefficients by

$\sum _{k}a_{ik}(b_{kj}+c_{kj})=\sum _{k}a_{ik}b_{kj}+\sum _{k}a_{ik}c_{kj}$

$\sum _{k}(b_{ik}+c_{ik})d_{kj}=\sum _{k}b_{ik}d_{kj}+\sum _{k}c_{ik}d_{kj}.$

### Product with a scalar

If **A** is a matrix and c a scalar, then the matrices $c\mathbf {A}$ and $\mathbf {A} c$ are obtained by left or right multiplying all entries of **A** by c. If the scalars have the [commutative property](https://en.wikipedia.org/wiki/Commutative_property), then $c\mathbf {A} =\mathbf {A} c.$

If the product $\mathbf {AB}$ is defined (that is, the number of columns of **A** equals the number of rows of **B**), then

$c(\mathbf {AB} )=(c\mathbf {A} )\mathbf {B}$ and $(\mathbf {A} \mathbf {B} )c=\mathbf {A} (\mathbf {B} c).$

If the scalars have the commutative property, then all four matrices are equal. More generally, all four are equal if *c* belongs to the [center](https://en.wikipedia.org/wiki/Center_(ring_theory) "Center (ring theory)") of a [ring](https://en.wikipedia.org/wiki/Ring_(mathematics) "Ring (mathematics)") containing the entries of the matrices, because in this case, *c***X** = **X***c* for all matrices **X**.

These properties result from the [bilinearity](https://en.wikipedia.org/wiki/Bilinearity) of the product of scalars:

$c\left(\sum _{k}a_{ik}b_{kj}\right)=\sum _{k}(ca_{ik})b_{kj}$

$\left(\sum _{k}a_{ik}b_{kj}\right)c=\sum _{k}a_{ik}(b_{kj}c).$

### Transpose

If the scalars have the [commutative property](https://en.wikipedia.org/wiki/Commutative_property), the [transpose](https://en.wikipedia.org/wiki/Transpose) of a product of matrices is the product, in the reverse order, of the transposes of the factors. That is

$(\mathbf {AB} )^{\mathsf {T}}=\mathbf {B} ^{\mathsf {T}}\mathbf {A} ^{\mathsf {T}}$

where <sup>T</sup> denotes the transpose, that is the interchange of rows and columns.

This identity does not hold for noncommutative entries, since the order between the entries of **A** and **B** is reversed, when one expands the definition of the matrix product.

### Complex conjugate

If **A** and **B** have [complex](https://en.wikipedia.org/wiki/Complex_number) entries, then

$(\mathbf {AB} )^{*}=\mathbf {A} ^{*}\mathbf {B} ^{*}$

where <sup>\*</sup> denotes the entry-wise [complex conjugate](https://en.wikipedia.org/wiki/Complex_conjugate) of a matrix.

This results from applying to the definition of matrix product the fact that the conjugate of a sum is the sum of the conjugates of the summands and the conjugate of a product is the product of the conjugates of the factors.

Transposition acts on the indices of the entries, while conjugation acts independently on the entries themselves. It results that, if **A** and **B** have complex entries, one has

$(\mathbf {AB} )^{\dagger }=\mathbf {B} ^{\dagger }\mathbf {A} ^{\dagger },$

where <sup>†</sup> denotes the [conjugate transpose](https://en.wikipedia.org/wiki/Conjugate_transpose) (conjugate of the transpose, or equivalently transpose of the conjugate).

### Associativity

Given three matrices **A**, **B** and **C**, the products (**AB**)**C** and **A**(**BC**) are defined if and only if the number of columns of **A** equals the number of rows of **B**, and the number of columns of **B** equals the number of rows of **C** (in particular, if one of the products is defined, then the other is also defined). In this case, one has the [associative property](https://en.wikipedia.org/wiki/Associative_property)

$(\mathbf {AB} )\mathbf {C} =\mathbf {A} (\mathbf {BC} ).$

As for any associative operation, this allows omitting parentheses, and writing the above products as $\mathbf {ABC} .$

This extends naturally to the product of any number of matrices provided that the dimensions match. That is, if **A**<sub>1</sub>, **A**<sub>2</sub>, ..., **A**<sub>*n*</sub> are matrices such that the number of columns of **A**<sub>*i*</sub> equals the number of rows of **A**<sub>*i* + 1</sub> for *i* = 1, ..., *n* – 1, then the product

$\prod _{i=1}^{n}\mathbf {A} _{i}=\mathbf {A} _{1}\mathbf {A} _{2}\cdots \mathbf {A} _{n}$

is defined and does not depend on the [order of the multiplications](https://en.wikipedia.org/wiki/Order_of_operations), if the order of the matrices is kept fixed.

These properties may be proved by straightforward but complicated [summation](https://en.wikipedia.org/wiki/Summation) manipulations. This result also follows from the fact that matrices represent [linear maps](https://en.wikipedia.org/wiki/Linear_map). Therefore, the associative property of matrices is simply a specific case of the associative property of [function composition](https://en.wikipedia.org/wiki/Function_composition).

#### Computational complexity depends on parenthesization

Although the result of a sequence of matrix products does not depend on the [order of operation](https://en.wikipedia.org/wiki/Order_of_operation) (provided that the order of the matrices is not changed), the [computational complexity](https://en.wikipedia.org/wiki/Computational_complexity) may depend dramatically on this order.

For example, if **A**, **B** and **C** are matrices of respective sizes 10×30, 30×5, 5×60, computing (**AB**)**C** needs 10×30×5 + 10×5×60 = 4,500 multiplications, while computing **A**(**BC**) needs 30×5×60 + 10×30×60 = 27,000 multiplications.

Algorithms have been designed for choosing the best order of products; see [Matrix chain multiplication](https://en.wikipedia.org/wiki/Matrix_chain_multiplication). When the number n of matrices increases, it has been shown that the choice of the best order has a complexity of $O(n\log n).$

#### Application to similarity

Any [invertible matrix](https://en.wikipedia.org/wiki/Invertible_matrix) $\mathbf {P}$ defines a [similarity transformation](https://en.wikipedia.org/wiki/Similar_matrix) (on square matrices of the same size as $\mathbf {P}$)

$S_{\mathbf {P} }(\mathbf {A} )=\mathbf {P} ^{-1}\mathbf {A} \mathbf {P} .$

Similarity transformations map product to products, that is

$S_{\mathbf {P} }(\mathbf {AB} )=S_{\mathbf {P} }(\mathbf {A} )S_{\mathbf {P} }(\mathbf {B} ).$

In fact, one has

$\mathbf {P} ^{-1}(\mathbf {AB} )\mathbf {P} =\mathbf {P} ^{-1}\mathbf {A} (\mathbf {P} \mathbf {P} ^{-1})\mathbf {B} \mathbf {P} =(\mathbf {P} ^{-1}\mathbf {A} \mathbf {P} )(\mathbf {P} ^{-1}\mathbf {B} \mathbf {P} ).$

## Square matrices

Let us denote ${\mathcal {M}}_{n}(R)$ the set of *n*×*n* [square matrices](https://en.wikipedia.org/wiki/Square_matrices) with entries in a [ring](https://en.wikipedia.org/wiki/Ring_(mathematics) "Ring (mathematics)") R, which, in practice, is often a [field](https://en.wikipedia.org/wiki/Field_(mathematics) "Field (mathematics)").

In ${\mathcal {M}}_{n}(R)$, the product is defined for every pair of matrices. This makes ${\mathcal {M}}_{n}(R)$ a [ring](https://en.wikipedia.org/wiki/Ring_(mathematics) "Ring (mathematics)"), which has the [identity matrix](https://en.wikipedia.org/wiki/Identity_matrix) **I** as an [identity element](https://en.wikipedia.org/wiki/Identity_element) (the matrix whose diagonal entries are equal to 1 and all other entries are 0). This ring is also an [associative R-algebra](https://en.wikipedia.org/wiki/Associative_algebra).

If *n* \> 1, many matrices do not have a [multiplicative inverse](https://en.wikipedia.org/wiki/Multiplicative_inverse). For example, a matrix such that all entries of a row (or a column) are 0 does not have an inverse. If it exists, the inverse of a matrix **A** is denoted **A**<sup>−1</sup>, and, thus verifies

$\mathbf {A} \mathbf {A} ^{-1}=\mathbf {A} ^{-1}\mathbf {A} =\mathbf {I} .$

A matrix that has an inverse is an [invertible matrix](https://en.wikipedia.org/wiki/Invertible_matrix). Otherwise, it is a [singular matrix](https://en.wikipedia.org/wiki/Singular_matrix).

A product of matrices is invertible if and only if each factor is invertible. In this case, one has

$(\mathbf {A} \mathbf {B} )^{-1}=\mathbf {B} ^{-1}\mathbf {A} ^{-1}.$

When R is [commutative](https://en.wikipedia.org/wiki/Commutative_ring), and, in particular, when it is a field, the [[Determinant]] of a product is the product of the determinants. As determinants are scalars, and scalars commute, one has thus

$\det(\mathbf {AB} )=\det(\mathbf {BA} )=\det(\mathbf {A} )\det(\mathbf {B} ).$

The other matrix [invariants](https://en.wikipedia.org/wiki/Invariant_(mathematics) "Invariant (mathematics)") do not behave as well with products. Nevertheless, if R is commutative, **AB** and **BA** have the same [trace](https://en.wikipedia.org/wiki/Trace_(linear_algebra) "Trace (linear algebra)"), the same [characteristic polynomial](https://en.wikipedia.org/wiki/Characteristic_polynomial), and the same [eigenvalues](https://en.wikipedia.org/wiki/Eigenvalues) with the same multiplicities. However, the [eigenvectors](https://en.wikipedia.org/wiki/Eigenvector) are generally different if **AB** ≠ **BA**.

### Powers of a matrix

One may raise a square matrix to any [nonnegative integer power](https://en.wikipedia.org/wiki/Exponentiation) multiplying it by itself repeatedly in the same way as for ordinary numbers. That is,

$\mathbf {A} ^{0}=\mathbf {I} ,$

$\mathbf {A} ^{1}=\mathbf {A} ,$

$\mathbf {A} ^{k}=\underbrace {\mathbf {A} \mathbf {A} \cdots \mathbf {A} } _{k{\text{ times}}}.$

Computing the kth power of a matrix needs *k* – 1 times the time of a single matrix multiplication, if it is done with the trivial algorithm (repeated multiplication). As this may be very time consuming, one generally prefers using [exponentiation by squaring](https://en.wikipedia.org/wiki/Exponentiation_by_squaring), which requires less than 2 log<sub>2</sub> *k* matrix multiplications, and is therefore much more efficient.

An easy case for exponentiation is that of a [diagonal matrix](https://en.wikipedia.org/wiki/Diagonal_matrix). Since the product of diagonal matrices amounts to simply multiplying corresponding diagonal elements together, the kth power of a diagonal matrix is obtained by raising the entries to the power k:

${\begin{bmatrix}a_{11}&0&\cdots &0\\0&a_{22}&\cdots &0\\\vdots &\vdots &\ddots &\vdots \\0&0&\cdots &a_{nn}\end{bmatrix}}^{k}={\begin{bmatrix}a_{11}^{k}&0&\cdots &0\\0&a_{22}^{k}&\cdots &0\\\vdots &\vdots &\ddots &\vdots \\0&0&\cdots &a_{nn}^{k}\end{bmatrix}}.$

## Abstract algebra

The definition of matrix product requires that the entries belong to a semiring, and does not require multiplication of elements of the semiring to be [commutative](https://en.wikipedia.org/wiki/Commutative_property). In many applications, the matrix elements belong to a field, although the [tropical semiring](https://en.wikipedia.org/wiki/Tropical_semiring) is also a common choice for graph [shortest path](https://en.wikipedia.org/wiki/Shortest_path) problems. Even in the case of matrices over fields, the product is not commutative in general, although it is [associative](https://en.wikipedia.org/wiki/Associative_property) and is [distributive](https://en.wikipedia.org/wiki/Distributive_property) over [matrix addition](https://en.wikipedia.org/wiki/Matrix_addition). The [identity matrices](https://en.wikipedia.org/wiki/Identity_matrices) (which are the [square matrices](https://en.wikipedia.org/wiki/Square_matrices) whose entries are zero outside of the main diagonal and 1 on the main diagonal) are [identity elements](https://en.wikipedia.org/wiki/Identity_element) of the matrix product. It follows that the *n* × *n* matrices over a [ring](https://en.wikipedia.org/wiki/Ring_(mathematics) "Ring (mathematics)") form a ring, which is noncommutative except if *n* = 1 and the ground ring is commutative.

A square matrix may have a [multiplicative inverse](https://en.wikipedia.org/wiki/Multiplicative_inverse), called an [[Inverse Matrix]]. In the common case where the entries belong to a [commutative ring](https://en.wikipedia.org/wiki/Commutative_ring) R, a matrix has an inverse if and only if its [[Determinant]] has a multiplicative inverse in R. The determinant of a product of square matrices is the product of the determinants of the factors. The *n* × *n* matrices that have an inverse form a [group](https://en.wikipedia.org/wiki/Group_(mathematics) "Group (mathematics)") under matrix multiplication, the [subgroups](https://en.wikipedia.org/wiki/Subgroup) of which are called [matrix groups](https://en.wikipedia.org/wiki/Matrix_group). Many classical groups (including all [finite groups](https://en.wikipedia.org/wiki/Finite_group)) are [isomorphic](https://en.wikipedia.org/wiki/Group_isomorphism) to matrix groups; this is the starting point of the theory of [group representations](https://en.wikipedia.org/wiki/Group_representation).

Matrices are the [morphisms](https://en.wikipedia.org/wiki/Morphisms) of a [category](https://en.wikipedia.org/wiki/Category_(mathematics) "Category (mathematics)"), the [category of matrices](https://en.wikipedia.org/wiki/Category_of_matrices). The objects are the [natural numbers](https://en.wikipedia.org/wiki/Natural_number) that measure the size of matrices, and the composition of morphisms is matrix multiplication. The source of a morphism is the number of columns of the corresponding matrix, and the target is the number of rows.

## Computational complexity

![[media/d8544c03e8bb58a04bc0fdc06c9f4f8bdb43c0c8.png]]
Improvement of estimates of exponent ω over time for the computational complexity of matrix multiplication $O(n^{\omega })$

The matrix multiplication [algorithm](https://en.wikipedia.org/wiki/Algorithm) that results from the definition requires, in the [worst case](https://en.wikipedia.org/wiki/Worst-case_complexity), $n^{3}$ multiplications and $(n-1)n^{2}$ additions of scalars to compute the product of two square *n*×*n* matrices. Its [computational complexity](https://en.wikipedia.org/wiki/Computational_complexity) is therefore $O(n^{3})$, in a [model of computation](https://en.wikipedia.org/wiki/Model_of_computation) for which the scalar operations take constant time.

Since matrix multiplication forms the basis for many algorithms, and many operations on matrices even have the same complexity as matrix multiplication (up to a multiplicative constant), the computational complexity of matrix multiplication appears throughout [numerical linear algebra](https://en.wikipedia.org/wiki/Numerical_linear_algebra) and [theoretical computer science](https://en.wikipedia.org/wiki/Theoretical_computer_science).

## Generalizations

Other types of products of matrices include:

- [Block matrix operations](https://en.wikipedia.org/wiki/Block_matrix#Block_matrix_operations)
- [Cracovian product](https://en.wikipedia.org/wiki/Cracovian_product), defined as **A** ∧ **B** = **B**<sup>T</sup>**A**
- [Frobenius inner product](https://en.wikipedia.org/wiki/Frobenius_inner_product), the [dot product](https://en.wikipedia.org/wiki/Dot_product) of matrices considered as vectors, or, equivalently the sum of the entries of the Hadamard product
- [Hadamard product](https://en.wikipedia.org/wiki/Hadamard_product_(matrices) "Hadamard product (matrices)") of two matrices of the same size, resulting in a matrix of the same size, which is the product entry-by-entry
- [[Kronecker Product]] or [tensor product](https://en.wikipedia.org/wiki/Tensor_product), the generalization to any size of the preceding
- [Khatri–Rao product](https://en.wikipedia.org/wiki/Khatri%E2%80%93Rao_product) and [face-splitting product](https://en.wikipedia.org/wiki/Face-splitting_product)
- [Outer product](https://en.wikipedia.org/wiki/Outer_product), also called [dyadic product](https://en.wikipedia.org/wiki/Dyadic_product) or [tensor product](https://en.wikipedia.org/wiki/Tensor_product) of two column matrices, which is $\mathbf {a} \mathbf {b} ^{\mathsf {T}}$
- [Scalar multiplication](https://en.wikipedia.org/wiki/Scalar_multiplication)

## See also

- [[Matrix Calculus]], for the interaction of matrix multiplication with operations from calculus

## Notes

1.  ^   Nykamp, Duane. ["Multiplying matrices and vectors"](https://mathinsight.org/matrix_vector_multiplication). *Math Insight*. Retrieved September 6, 2020.
2.  O'Connor, John J.; [Robertson, Edmund F.](https://en.wikipedia.org/wiki/Edmund_F._Robertson), ["Jacques Philippe Marie Binet"](https://mathshistory.st-andrews.ac.uk/Biographies/Binet.html), *[MacTutor History of Mathematics Archive](https://en.wikipedia.org/wiki/MacTutor_History_of_Mathematics_Archive)*, [University of St Andrews](https://en.wikipedia.org/wiki/University_of_St_Andrews)
3.  [Lerner, R. G.](https://en.wikipedia.org/wiki/Rita_G._Lerner); Trigg, G. L. (1991). *Encyclopaedia of Physics* (2nd ed.). VHC publishers. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-527-26954-9](https://en.wikipedia.org/wiki/Special:BookSources/978-3-527-26954-9).
4.  Parker, C. B. (1994). [McGraw Hill Encyclopaedia of Physics](https://archive.org/details/mcgrawhillencycl1993park) (2nd ed.). McGraw-Hill. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-07-051400-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-07-051400-3).
5.  Lipschutz, S.; Lipson, M. (2009). *Linear Algebra*. Schaum's Outlines (4th ed.). McGraw Hill (USA). pp. 30–31. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-07-154352-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-07-154352-1).
6.  Riley, K. F.; Hobson, M. P.; Bence, S. J. (2010). [Mathematical methods for physics and engineering](https://archive.org/details/mathematicalmeth00rile). Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-86153-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-86153-3).
7.  Adams, R. A. (1995). *Calculus, A Complete Course* (3rd ed.). Addison Wesley. p. 627. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-201-82823-5](https://en.wikipedia.org/wiki/Special:BookSources/0-201-82823-5).
8.  Horn, Johnson (2013). *Matrix Analysis* (2nd ed.). Cambridge University Press. p. 6. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-54823-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-54823-6).
9.  Peter Stingl (1996). *Mathematik für Fachhochschulen – Technik und Informatik* (in German) (5th ed.). [Munich](https://en.wikipedia.org/wiki/Munich): [Carl Hanser Verlag](https://en.wikipedia.org/wiki/Carl_Hanser_Verlag). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [3-446-18668-9](https://en.wikipedia.org/wiki/Special:BookSources/3-446-18668-9). Here: Exm.5.4.10, p.205-206
10. ^    Weisstein, Eric W. ["Matrix Multiplication"](https://mathworld.wolfram.com/MatrixMultiplication.html). *mathworld.wolfram.com*. Retrieved 2020-09-06.
11. Lipcshutz, S.; Lipson, M. (2009). "2". *Linear Algebra*. Schaum's Outlines (4th ed.). McGraw Hill (USA). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-07-154352-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-07-154352-1).
12. Horn, Johnson (2013). "Chapter 0". *Matrix Analysis* (2nd ed.). Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-54823-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-54823-6).
13. [Hu, T. C.](https://en.wikipedia.org/wiki/T._C._Hu); Shing, M.-T. (1982). ["Computation of Matrix Chain Products, Part I"](https://web.archive.org/web/20160804050127/http://www.cs.ust.hk/mjg_lib/bibs/DPSu/DPSu.Files/0211028.pdf) (PDF). *SIAM Journal on Computing*. **11** (2): 362–373. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.695.2923](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.695.2923). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/0211028](https://doi.org/10.1137%2F0211028). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0097-5397](https://search.worldcat.org/issn/0097-5397). Archived from [the original](http://www.cs.ust.hk/mjg_lib/bibs/DPSu/DPSu.Files/0211028.pdf) (PDF) on 2016-08-04. Retrieved 2024-08-02.
14. [Hu, T. C.](https://en.wikipedia.org/wiki/T._C._Hu); Shing, M.-T. (1984). ["Computation of Matrix Chain Products, Part II"](https://web.archive.org/web/20160804042514/http://www.cs.ust.hk/mjg_lib/bibs/DPSu/DPSu.Files/0213017.pdf) (PDF). *SIAM Journal on Computing*. **13** (2): 228–251. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.695.4875](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.695.4875). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/0213017](https://doi.org/10.1137%2F0213017). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0097-5397](https://search.worldcat.org/issn/0097-5397). Archived from [the original](http://www.cs.ust.hk/mjg_lib/bibs/DPSu/DPSu.Files/0213017.pdf) (PDF) on 2016-08-04. Retrieved 2024-08-02.
15. [Motwani, Rajeev](https://en.wikipedia.org/wiki/Rajeev_Motwani); [Raghavan, Prabhakar](https://en.wikipedia.org/wiki/Prabhakar_Raghavan) (1995). [Randomized Algorithms](https://books.google.com/books?id=QKVY4mDivBEC&pg=PA280). Cambridge University Press. p. 280. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780521474658](https://en.wikipedia.org/wiki/Special:BookSources/9780521474658).
16. Volker Strassen (Aug 1969). ["Gaussian elimination is not optimal"](http://www.digizeitschriften.de/dms/img/?PID=GDZPPN001168215). *Numerische Mathematik*. **13** (4): 354–356. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/BF02165411](https://doi.org/10.1007%2FBF02165411). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [121656251](https://api.semanticscholar.org/CorpusID:121656251).
17. C.-C. Chou and Y.-F. Deng and G. Li and Y. Wang (1995). ["Parallelizing Strassen's Method for Matrix Multiplication on Distributed-Memory MIMD Architectures"](https://core.ac.uk/download/pdf/82778592.pdf) (PDF). *Computers Math. Applic*. **30** (2): 49–69. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/0898-1221(95)00077-C](https://doi.org/10.1016%2F0898-1221%2895%2900077-C).
18. Vassilevska Williams, Virginia; Xu, Yinzhan; Xu, Zixuan; Zhou, Renfei. *New Bounds for Matrix Multiplication: from Alpha to Omega*. Proceedings of the 2024 Annual ACM-SIAM Symposium on Discrete Algorithms (SODA). pp. 3792–3835. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2307.07970](https://arxiv.org/abs/2307.07970). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/1.9781611977912.134](https://doi.org/10.1137%2F1.9781611977912.134).
19. Nadis, Steve (March 7, 2024). ["New Breakthrough Brings Matrix Multiplication Closer to Ideal"](https://www.quantamagazine.org/new-breakthrough-brings-matrix-multiplication-closer-to-ideal-20240307). Retrieved 2024-03-09.
20. that is, in time *n*<sup>2+f(n)</sup>, for some function *f* with *f*(*n*)[→](https://en.wikipedia.org/wiki/Limit_of_a_function)0 as *n*→∞

## References

- Henry Cohn, [Robert Kleinberg](https://en.wikipedia.org/wiki/Robert_Kleinberg), [Balázs Szegedy](https://en.wikipedia.org/wiki/Bal%C3%A1zs_Szegedy), and Chris Umans. Group-theoretic Algorithms for Matrix Multiplication. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[math.GR/0511460](https://arxiv.org/abs/math.GR/0511460). *Proceedings of the 46th Annual Symposium on Foundations of Computer Science*, 23–25 October 2005, Pittsburgh, PA, IEEE Computer Society, pp. 379–388.
- Henry Cohn, Chris Umans. A Group-theoretic Approach to Fast Matrix Multiplication. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[math.GR/0307321](https://arxiv.org/abs/math.GR/0307321). *Proceedings of the 44th Annual IEEE Symposium on Foundations of Computer Science*, 11–14 October 2003, Cambridge, MA, IEEE Computer Society, pp. 438–449.
- Coppersmith, D.; Winograd, S. (1990). ["Matrix multiplication via arithmetic progressions"](https://doi.org/10.1016%2Fs0747-7171%2808%2980013-2). *J. Symbolic Comput*. **9** (3): 251–280. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/s0747-7171(08)80013-2](https://doi.org/10.1016%2Fs0747-7171%2808%2980013-2).
- Horn, Roger A.; Johnson, Charles R. (1991), *Topics in Matrix Analysis*, [Cambridge University Press](https://en.wikipedia.org/wiki/Cambridge_University_Press), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-46713-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-46713-1)
- [Knuth, D.E.](https://en.wikipedia.org/wiki/Donald_Knuth), *[The Art of Computer Programming](https://en.wikipedia.org/wiki/The_Art_of_Computer_Programming) Volume 2: Seminumerical Algorithms*. Addison-Wesley Professional; 3 edition (November 14, 1997). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-201-89684-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-201-89684-8). pp. 501.
- Press, William H.; Flannery, Brian P.; [Teukolsky, Saul A.](https://en.wikipedia.org/wiki/Saul_Teukolsky); Vetterling, William T. (2007), [*Numerical Recipes: The Art of Scientific Computing*](https://en.wikipedia.org/wiki/Numerical_Recipes) (3rd ed.), [Cambridge University Press](https://en.wikipedia.org/wiki/Cambridge_University_Press), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-88068-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-88068-8).
- [Ran Raz](https://en.wikipedia.org/wiki/Ran_Raz). On the complexity of matrix product. In Proceedings of the thirty-fourth annual ACM symposium on Theory of computing. ACM Press, 2002. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1145/509907.509932](https://doi.org/10.1145%2F509907.509932).
- Robinson, Sara, *Toward an Optimal Algorithm for Matrix Multiplication,* SIAM News 38(9), November 2005. [PDF](https://web.archive.org/web/20100331095603/http://www.siam.org/pdf/news/174.pdf)
- Strassen, Volker, *Gaussian Elimination is not Optimal*, Numer. Math. 13, p. 354–356, 1969.
- Styan, George P. H. (1973), ["Hadamard Products and Multivariate Statistical Analysis"](http://dml.cz/bitstream/handle/10338.dmlcz/102190/CzechMathJ_37-1987-4_14.pdf) (PDF), *Linear Algebra and Its Applications*, **6**: 217–240, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/0024-3795(73)90023-2](https://doi.org/10.1016%2F0024-3795%2873%2990023-2)
- Williams, Virginia Vassilevska (2012-05-19). ["Multiplying matrices faster than coppersmith-winograd"](http://dl.acm.org/citation.cfm?id=2213977.2214056). *Proceedings of the 44th symposium on Theory of Computing - STOC '12*. ACM. pp. 887–898. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.297.2680](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.297.2680). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1145/2213977.2214056](https://doi.org/10.1145%2F2213977.2214056). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9781450312455](https://en.wikipedia.org/wiki/Special:BookSources/9781450312455). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [14350287](https://api.semanticscholar.org/CorpusID:14350287).
