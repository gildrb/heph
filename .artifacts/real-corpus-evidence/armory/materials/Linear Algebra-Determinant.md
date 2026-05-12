[[linear-algebra.base]]

> Source: [[Determinant]]
> License: Wikipedia content is available under CC BY-SA 4.0.

In [mathematics](https://en.wikipedia.org/wiki/Mathematics), the **determinant** is a [scalar](https://en.wikipedia.org/wiki/Scalar_(mathematics) "Scalar (mathematics)")-valued [function](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)") of the entries of a [square matrix](https://en.wikipedia.org/wiki/Square_matrix). The determinant of a matrix *A* is commonly denoted det(*A*), det *A*, or \|*A*\|. Its value characterizes some properties of the matrix and the [linear map](https://en.wikipedia.org/wiki/Linear_map) represented, on a given [basis](https://en.wikipedia.org/wiki/Basis_(linear_algebra) "Basis (linear algebra)"), by the matrix. In particular, the determinant is nonzero [if and only if](https://en.wikipedia.org/wiki/If_and_only_if) the matrix is [invertible](https://en.wikipedia.org/wiki/Invertible_matrix) and the corresponding linear map is an [isomorphism](https://en.wikipedia.org/wiki/Linear_isomorphism). However, if the determinant is zero, the matrix is referred to as singular, meaning it does not have an inverse.

The determinant is completely determined by the two following properties: the determinant of a product of matrices is the product of their determinants, and the determinant of a [triangular matrix](https://en.wikipedia.org/wiki/Triangular_matrix) is the product of its diagonal entries.

The determinant of a 2 × 2 matrix is

${\begin{vmatrix}a&b\\c&d\end{vmatrix}}=ad-bc,$

and the determinant of a 3 × 3 matrix is

${\begin{vmatrix}a&b&c\\d&e&f\\g&h&i\end{vmatrix}}=aei+bfg+cdh-ceg-bdi-afh.$

The determinant of an *n* × *n* matrix can be defined in several equivalent ways, the most common being [Leibniz formula](https://en.wikipedia.org/wiki/Leibniz_formula_for_determinants), which expresses the determinant as a sum of $n!$ (the [factorial](https://en.wikipedia.org/wiki/Factorial) of n) signed products of matrix entries. It can be computed by the [Laplace expansion](https://en.wikipedia.org/wiki/Laplace_expansion), which expresses the determinant as a [linear combination](https://en.wikipedia.org/wiki/Linear_combination) of determinants of submatrices, or with [Gaussian elimination](https://en.wikipedia.org/wiki/Gaussian_elimination), which allows computing a [row echelon form](https://en.wikipedia.org/wiki/Row_echelon_form) with the same determinant, equal to the product of the diagonal entries of the row echelon form.

Determinants can also be defined by some of their properties. Namely, the determinant is the unique function defined on the *n* × *n* matrices that has the four following properties:

1.  The determinant of the [identity matrix](https://en.wikipedia.org/wiki/Identity_matrix) is 1.
2.  The exchange of two rows multiplies the determinant by −1.
3.  Multiplying a row by a number multiplies the determinant by this number.
4.  Adding a multiple of one row to another row does not change the determinant.

The above properties relating to rows (properties 2–4) may be replaced by the corresponding statements with respect to columns.

The determinant is invariant under [matrix similarity](https://en.wikipedia.org/wiki/Matrix_similarity). This implies that, given a linear [endomorphism](https://en.wikipedia.org/wiki/Endomorphism) of a [finite-dimensional vector space](https://en.wikipedia.org/wiki/Finite-dimensional_vector_space), the determinant of the matrix that represents it on a [basis](https://en.wikipedia.org/wiki/Basis_(vector_space)) does not depend on the chosen basis. This allows defining the *determinant* of a linear endomorphism, which does not depend on the choice of a [coordinate system](https://en.wikipedia.org/wiki/Coordinate_system).

Determinants occur throughout mathematics. For example, a matrix is often used to represent the [coefficients](https://en.wikipedia.org/wiki/Coefficient) in a [system of linear equations](https://en.wikipedia.org/wiki/System_of_linear_equations), and determinants can be used to solve these equations ([Cramer's rule](https://en.wikipedia.org/wiki/Cramer%27s_rule)), although other methods of solution are computationally much more efficient. Determinants are used for defining the [characteristic polynomial](https://en.wikipedia.org/wiki/Characteristic_polynomial) of a square matrix, whose roots are the [eigenvalues](https://en.wikipedia.org/wiki/Eigenvalue). In [geometry](https://en.wikipedia.org/wiki/Geometry), the signed n-dimensional [volume](https://en.wikipedia.org/wiki/Volume) of a n-dimensional [parallelepiped](https://en.wikipedia.org/wiki/Parallelepiped) is expressed by a determinant, and the determinant of a linear [endomorphism](https://en.wikipedia.org/wiki/Endomorphism) determines how the [orientation](https://en.wikipedia.org/wiki/Orientability) and the n-dimensional volume are transformed under the endomorphism. This is used in [calculus](https://en.wikipedia.org/wiki/Calculus) with [exterior differential forms](https://en.wikipedia.org/wiki/Exterior_differential_form) and the [Jacobian determinant](https://en.wikipedia.org/wiki/Jacobian_determinant), in particular for [changes of variables](https://en.wikipedia.org/wiki/Integration_by_substitution#Substitution_for_multiple_variables) in [multiple integrals](https://en.wikipedia.org/wiki/Multiple_integral).

## Two by two matrices

The determinant of a 2 × 2 matrix ${\begin{pmatrix}a&b\\c&d\end{pmatrix}}$ is denoted either by "det" or by vertical bars around the matrix, and is defined as

$\det {\begin{pmatrix}a&b\\c&d\end{pmatrix}}={\begin{vmatrix}a&b\\c&d\end{vmatrix}}=ad-bc.$

For example,

$\det {\begin{pmatrix}3&7\\1&-4\end{pmatrix}}={\begin{vmatrix}3&7\\1&{-4}\end{vmatrix}}=(3\cdot (-4))-(7\cdot 1)=-19.$

### First properties

The determinant has several key properties that can be proved by direct evaluation of the definition for $2\times 2$-matrices, and that continue to hold for determinants of larger matrices. They are as follows: first, the determinant of the [identity matrix](https://en.wikipedia.org/wiki/Identity_matrix) ${\begin{pmatrix}1&0\\0&1\end{pmatrix}}$ is 1. Second, the determinant is zero if two rows are the same:

${\begin{vmatrix}a&b\\a&b\end{vmatrix}}=ab-ba=0.$

This holds similarly if the two columns are the same. Moreover,

${\begin{vmatrix}a&b+b'\\c&d+d'\end{vmatrix}}=a(d+d')-(b+b')c={\begin{vmatrix}a&b\\c&d\end{vmatrix}}+{\begin{vmatrix}a&b'\\c&d'\end{vmatrix}}.$

Finally, if any column is multiplied by some number $r$ (i.e., all entries in that column are multiplied by that number), the determinant is also multiplied by that number:

${\begin{vmatrix}r\cdot a&b\\r\cdot c&d\end{vmatrix}}=rad-brc=r(ad-bc)=r\cdot {\begin{vmatrix}a&b\\c&d\end{vmatrix}}.$

## Geometric meaning

![[media/e3f34031691eccaf722a3b130e918623b132dbbc.png]]
The area of the parallelogram is the absolute value of the determinant of the matrix formed by the vectors representing the parallelogram's sides.

If the matrix entries are real numbers, the matrix A represents the [linear map](https://en.wikipedia.org/wiki/Linear_map) that maps the [basis vectors](https://en.wikipedia.org/wiki/Basis_vector) to the columns of A. The images of the basis vectors form a [parallelogram](https://en.wikipedia.org/wiki/Parallelogram) that represents the image of the [unit square](https://en.wikipedia.org/wiki/Unit_square) under the mapping. The parallelogram defined by the columns of the above matrix is the one with vertices at (0, 0), (*a*, *c*), (*a* + *b*, *c* + *d*), and (*b*, *d*), as shown in the accompanying diagram.

The absolute value of *ad* − *bc* is the area of the parallelogram, and thus represents the scale factor by which areas are transformed by A.

The absolute value of the determinant together with the sign becomes the [signed area](https://en.wikipedia.org/wiki/Signed_area) of the parallelogram. The signed area is the same as the usual [area](https://en.wikipedia.org/wiki/Area_(geometry)), except that it is negative when the angle from the first to the second vector defining the parallelogram turns in a clockwise direction (which is opposite to the direction one would get for the [identity matrix](https://en.wikipedia.org/wiki/Identity_matrix)).

To show that *ad* − *bc* is the signed area, one may consider a matrix containing two vectors **u** ≡ (*a*, *c*) and **v** ≡ (*b*, *d*) representing the parallelogram's sides. The signed area can be expressed as \|**u**\| \|**v**\| sin *θ* for the angle *θ* between the vectors, which is simply base times height, the length of one vector times the perpendicular component of the other. Due to the [sine](https://en.wikipedia.org/wiki/Sine) this already is the signed area, yet it may be expressed more conveniently using the [cosine](https://en.wikipedia.org/wiki/Cosine) of the complementary angle to a perpendicular vector, e.g. **u**<sup>⊥</sup> = (−*c*, *a*), so that \|**u**<sup>⊥</sup>\| \|**v**\| cos *θ′* becomes the signed area in question, which can be determined by the pattern of the [scalar product](https://en.wikipedia.org/wiki/Scalar_product) to be equal to *ad* − *bc* according to the following equations:

${\text{Signed area}}=|{\boldsymbol {u}}|\,|{\boldsymbol {v}}|\,\sin \,\theta =\left|{\boldsymbol {u}}^{\perp }\right|\,\left|{\boldsymbol {v}}\right|\,\cos \,\theta '={\begin{pmatrix}-c\\a\end{pmatrix}}\cdot {\begin{pmatrix}b\\d\end{pmatrix}}=ad-bc.$

Thus the determinant gives the area scale factor and the orientation induced by the mapping represented by *A*. When the determinant is equal to one, the linear mapping defined by the matrix preserves area and orientation.

![[media/48d309d21e535159be53f1bde3a1dfbcb8ebf2e5.png]]
The volume of this [parallelepiped](https://en.wikipedia.org/wiki/Parallelepiped) is the absolute value of the determinant of the matrix formed by the columns constructed from the vectors r1, r2, and r3.

If an *n* × *n* [real](https://en.wikipedia.org/wiki/Real_number) matrix *A* is written in terms of its column vectors $A=\left[{\begin{array}{c|c|c|c}\mathbf {a} _{1}&\mathbf {a} _{2}&\cdots &\mathbf {a} _{n}\end{array}}\right]$, then

$A{\begin{pmatrix}1\\0\\\vdots \\0\end{pmatrix}}=\mathbf {a} _{1},\quad A{\begin{pmatrix}0\\1\\\vdots \\0\end{pmatrix}}=\mathbf {a} _{2},\quad \ldots ,\quad A{\begin{pmatrix}0\\0\\\vdots \\1\end{pmatrix}}=\mathbf {a} _{n}.$

This means that $A$ maps the unit [*n*-cube](https://en.wikipedia.org/wiki/Hypercube) to the *n*-dimensional [parallelotope](https://en.wikipedia.org/wiki/Parallelepiped#Parallelotope) defined by the vectors $\mathbf {a} _{1},\mathbf {a} _{2},\ldots ,\mathbf {a} _{n},$ the region $P=\left\{c_{1}\mathbf {a} _{1}+\cdots +c_{n}\mathbf {a} _{n}\mid 0\leq c_{i}\leq 1\ \forall i\right\}$ ($\forall$ stands for "for all" as a [logical symbol](https://en.wikipedia.org/wiki/List_of_logic_symbols).)

The determinant gives the [signed](https://en.wikipedia.org/wiki/Orientation_(vector_space) "Orientation (vector space)") *n*-dimensional volume of this parallelotope, $\det(A)=\pm {\text{vol}}(P),$ and hence describes more generally the *n*-dimensional volume scale factor of the [[Linear Transformation]] produced by *A*. (The sign shows whether the transformation preserves or reverses [orientation](https://en.wikipedia.org/wiki/Orientation_(vector_space) "Orientation (vector space)").) In particular, if the determinant is zero, then this parallelotope has volume zero and is not fully *n*-dimensional, which indicates that the dimension of the image of *A* is less than *n*. This [means](https://en.wikipedia.org/wiki/Rank%E2%80%93nullity_theorem) that *A* produces a linear transformation which is neither [onto](https://en.wikipedia.org/wiki/Surjective_function) nor [one-to-one](https://en.wikipedia.org/wiki/Injective_function), and so is not invertible.

## Definition

Let *A* be a [square matrix](https://en.wikipedia.org/wiki/Square_matrix) with *n* rows and *n* columns, so that it can be written as

$A={\begin{bmatrix}a_{1,1}&a_{1,2}&\cdots &a_{1,n}\\a_{2,1}&a_{2,2}&\cdots &a_{2,n}\\\vdots &\vdots &\ddots &\vdots \\a_{n,1}&a_{n,2}&\cdots &a_{n,n}\end{bmatrix}}.$

The entries $a_{1,1}$ etc. are, for many purposes, real or complex numbers. As discussed below, the determinant is also defined for matrices whose entries are in a [commutative ring](https://en.wikipedia.org/wiki/Commutative_ring).

The determinant of *A* is denoted by det(*A*), or it can be denoted directly in terms of the matrix entries by writing enclosing bars instead of brackets:

${\begin{vmatrix}a_{1,1}&a_{1,2}&\cdots &a_{1,n}\\a_{2,1}&a_{2,2}&\cdots &a_{2,n}\\\vdots &\vdots &\ddots &\vdots \\a_{n,1}&a_{n,2}&\cdots &a_{n,n}\end{vmatrix}}.$

There are various equivalent ways to define the determinant of a square matrix *A*, i.e. one with the same number of rows and columns: the determinant can be defined via the [Leibniz formula](https://en.wikipedia.org/wiki/Leibniz_formula_for_determinants), an explicit formula involving sums of products of certain entries of the matrix. The determinant can also be characterized as the unique function depending on the entries of the matrix satisfying certain properties. This approach can also be used to compute determinants by simplifying the matrices in question.

### Leibniz formula

#### 3 × 3 matrices

The *Leibniz formula* for the determinant of a 3 × 3 matrix is the following:

${\begin{vmatrix}a&b&c\\d&e&f\\g&h&i\end{vmatrix}}=aei+bfg+cdh-ceg-bdi-afh.\$

In this expression, each term has one factor from each row, all in different columns, arranged in increasing row order. For example, *bdi* has *b* from the first row second column, *d* from the second row first column, and *i* from the third row third column. The signs are determined by how many transpositions of factors are necessary to arrange the factors in increasing order of their columns (given that the terms are arranged left-to-right in increasing row order): positive for an even number of transpositions and negative for an odd number. For the example of *bdi*, the single transposition of *bd* to *db* gives *dbi,* whose three factors are from the first, second and third columns respectively; this is an odd number of transpositions, so the term appears with negative sign.

![[media/97da440165096393c66f9c675d9780f2f679b301.png]]
[Rule of Sarrus](https://en.wikipedia.org/wiki/Rule_of_Sarrus)

The [rule of Sarrus](https://en.wikipedia.org/wiki/Rule_of_Sarrus) is a mnemonic for the expanded form of this determinant: the sum of the products of three diagonal north-west to south-east lines of matrix elements, minus the sum of the products of three diagonal south-west to north-east lines of elements, when the copies of the first two columns of the matrix are written beside it as in the illustration. This scheme for calculating the determinant of a 3 × 3 matrix does not carry over into higher dimensions.

#### *n* × *n* matrices

Generalizing the above to higher dimensions, the determinant of an $n\times n$ matrix is an expression involving [permutations](https://en.wikipedia.org/wiki/Permutation) and their [signatures](https://en.wikipedia.org/wiki/Signature_(permutation)). A permutation of the set $\{1,2,\dots ,n\}$ is a [bijective function](https://en.wikipedia.org/wiki/Bijection) $\sigma$ from this set to itself, with values $\sigma (1),\sigma (2),\ldots ,\sigma (n)$ exhausting the entire set. The set of all such permutations, called the [symmetric group](https://en.wikipedia.org/wiki/Symmetric_group), is commonly denoted $S_{n}$. The signature $\operatorname {sgn} (\sigma )$ of a permutation $\sigma$ is $+1,$ if the permutation can be obtained with an even number of transpositions (exchanges of two entries); otherwise, it is $-1.$

Given a matrix

$A={\begin{bmatrix}a_{1,1}\ldots a_{1,n}\\\vdots \qquad \vdots \\a_{n,1}\ldots a_{n,n}\end{bmatrix}},$

the Leibniz formula for its determinant is, using [sigma notation](https://en.wikipedia.org/wiki/Sigma_notation) for the sum,

$\det(A)={\begin{vmatrix}a_{1,1}\ldots a_{1,n}\\\vdots \qquad \vdots \\a_{n,1}\ldots a_{n,n}\end{vmatrix}}=\sum _{\sigma \in S_{n}}\operatorname {sgn} (\sigma )a_{1,\sigma (1)}\cdots a_{n,\sigma (n)}.$

Using [pi notation](https://en.wikipedia.org/wiki/Pi_notation) for the product, this can be shortened into

$\det(A)=\sum _{\sigma \in S_{n}}\left(\operatorname {sgn} (\sigma )\prod _{i=1}^{n}a_{i,\sigma (i)}\right)$.

The [Levi-Civita symbol](https://en.wikipedia.org/wiki/Levi-Civita_symbol) $\varepsilon _{i_{1},\ldots ,i_{n}}$ is defined on the n-[tuples](https://en.wikipedia.org/wiki/Tuple) of integers in $\{1,\ldots ,n\}$ as 0 if two of the integers are equal, and otherwise as the signature of the permutation defined by the *n-*tuple of integers. With the Levi-Civita symbol, the Leibniz formula becomes

$\det(A)=\sum _{i_{1},i_{2},\ldots ,i_{n}}\varepsilon _{i_{1}\cdots i_{n}}a_{1,i_{1}}\!\cdots a_{n,i_{n}},$

where the sum is taken over all n-tuples of integers in $\{1,\ldots ,n\}.$ 

## Properties

### Characterization of the determinant

The determinant can be characterized by the following three key properties. To state these, it is convenient to regard an $n\times n$ matrix *A* as being composed of its $n$ columns, so denoted as

$A={\big (}a_{1},\dots ,a_{n}{\big )},$

where the [column vector](https://en.wikipedia.org/wiki/Column_vector) $a_{i}$ (for each *i*) is composed of the entries of the matrix in the *i*-th column.

1.  
2.  $\det \left(I\right)=1$, where $I$ is an [identity matrix](https://en.wikipedia.org/wiki/Identity_matrix).
3.  
4.  The determinant is *[multilinear](https://en.wikipedia.org/wiki/Multilinear_map)*: if the *j*th column of a matrix $A$ is written as a [linear combination](https://en.wikipedia.org/wiki/Linear_combination) $a_{j}=r\cdot v+w$ of two [column vectors](https://en.wikipedia.org/wiki/Column_vector) *v* and *w* and a number *r*, then the determinant of *A* is expressible as a similar linear combination:
    ${\begin{aligned}|A|&={\big |}a_{1},\dots ,a_{j-1},r\cdot v+w,a_{j+1},\dots ,a_{n}|\\&=r\cdot |a_{1},\dots ,v,\dots a_{n}|+|a_{1},\dots ,w,\dots ,a_{n}|\end{aligned}}$
5.  
6.  The determinant is *[alternating](https://en.wikipedia.org/wiki/Alternating_form)*: whenever two columns of a matrix are identical, its determinant is 0:
    $|a_{1},\dots ,v,\dots ,v,\dots ,a_{n}|=0.$

If the determinant is defined using the Leibniz formula as above, these three properties can be proved by direct inspection of that formula. Some authors also approach the determinant directly using these three properties: it can be shown that there is exactly one function that assigns to any $n\times n$ matrix *A* a number that satisfies these three properties. This also shows that this more abstract approach to the determinant yields the same definition as the one using the Leibniz formula.

To see this it suffices to expand the determinant by multi-linearity in the columns into a (huge) linear combination of determinants of matrices in which each column is a [standard basis](https://en.wikipedia.org/wiki/Standard_basis) vector. These determinants are either 0 (if the columns are linearly dependent, by property 3) or else ±1 (by property 1 and 3 - the minus sign appears when the columns are permuted according to an [odd permutation](https://en.wikipedia.org/wiki/Odd_permutation)), so the linear combination gives the expression above in terms of the Levi-Civita symbol. While less technical in appearance, this characterization cannot entirely replace the Leibniz formula in defining the determinant, since without it the existence of an appropriate function is not clear.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

### Immediate consequences

These rules have several further consequences:

- The determinant is a [homogeneous function](https://en.wikipedia.org/wiki/Homogeneous_function), i.e., 

$$
\det(cA)=c^{n}\det(A)
$$

 (for an $n\times n$ matrix $A$).
- Interchanging any pair of columns of a matrix multiplies its determinant by −1. This follows from the determinant being multilinear and alternating (properties 2 and 3 above): 

$$
|a_{1},\dots ,a_{j},\dots a_{i},\dots ,a_{n}|=-|a_{1},\dots ,a_{i},\dots ,a_{j},\dots ,a_{n}|.
$$

 This formula can be applied iteratively when several columns are swapped. For example 

$$
|a_{3},a_{1},a_{2},a_{4}\dots ,a_{n}|=-|a_{1},a_{3},a_{2},a_{4},\dots ,a_{n}|=|a_{1},a_{2},a_{3},a_{4},\dots ,a_{n}|.
$$

 Yet more generally, any permutation of the columns multiplies the determinant by the [sign](https://en.wikipedia.org/wiki/Parity_of_a_permutation) of the permutation.
- If some column can be expressed as a linear combination of the *other* columns (i.e. the columns of the matrix form a [linearly dependent](https://en.wikipedia.org/wiki/Linearly_independent) set), the determinant is 0. As a special case, this includes: if some column is such that all its entries are zero, then the determinant of that matrix is 0.
- Adding a scalar multiple of one column to *another* column does not change the value of the determinant. This is a consequence of multilinearity and being alternative: by multilinearity the determinant changes by a multiple of the determinant of a matrix with two equal columns, which determinant is 0, since the determinant is alternating.
- If $A$ is a [triangular matrix](https://en.wikipedia.org/wiki/Triangular_matrix), i.e. $a_{ij}=0$, whenever $i>j$ or, alternatively, whenever $i<j$, then its determinant equals the product of the diagonal entries: 

$$
\det(A)=a_{11}a_{22}\cdots a_{nn}=\prod _{i=1}^{n}a_{ii}.
$$

 Indeed, such a matrix can be reduced, by appropriately adding multiples of the columns with fewer nonzero entries to those with more entries, to a [diagonal matrix](https://en.wikipedia.org/wiki/Diagonal_matrix) (without changing the determinant). For such a matrix, using the linearity in each column reduces to the identity matrix, in which case the stated formula holds by the very first characterizing property of determinants. Alternatively, this formula can also be deduced from the Leibniz formula, since the only permutation $\sigma$ which gives a non-zero contribution is the identity permutation.

#### Example

These characterizing properties and their consequences listed above are both theoretically significant, but can also be used to compute determinants for concrete matrices. In fact, [Gaussian elimination](https://en.wikipedia.org/wiki/Gaussian_elimination) can be applied to bring any matrix into upper triangular form, and the steps in this algorithm affect the determinant in a controlled way. The following concrete example illustrates the computation of the determinant of the matrix $A$ using that method:

$A={\begin{bmatrix}-2&-1&2\\2&1&4\\-3&3&-1\end{bmatrix}}.$

|  |  |  |  |  |
|----|----|----|----|----|
| Matrix | $B={\begin{bmatrix}-3&-1&2\\3&1&4\\0&3&-1\end{bmatrix}}$ | $C={\begin{bmatrix}-3&5&2\\3&13&4\\0&0&-1\end{bmatrix}}$ | $D={\begin{bmatrix}5&-3&2\\13&3&4\\0&0&-1\end{bmatrix}}$ | $E={\begin{bmatrix}18&-3&2\\0&3&4\\0&0&-1\end{bmatrix}}$ |
| Obtained by | add the second column to the first | add 3 times the third column to the second | swap the first two columns | add $-{\frac {13}{3}}$ times the second column to the first |
| Determinant | $|A|=|B|$ | $|B|=|C|$ | $|D|=-|C|$ | $|E|=|D|$ |

Computation of the determinant of matrix $A$ {.wikitable}

Combining these equalities gives $|A|=-|E|=-(18\cdot 3\cdot (-1))=54.$

### Transpose

The determinant of the [transpose](https://en.wikipedia.org/wiki/Transpose) of $A$ equals the determinant of *A*:

$\det \left(A^{\textsf {T}}\right)=\det(A)$.

This can be proven by inspecting the Leibniz formula. This implies that in all the properties mentioned above, the word "column" can be replaced by "row" throughout. For example, viewing an *n* × *n* matrix as being composed of *n* rows, the determinant is an *n*-linear function.

### Multiplicativity and matrix groups

The determinant is a *multiplicative map*, i.e., for square matrices $A$ and $B$ of equal size, the determinant of a [matrix product](https://en.wikipedia.org/wiki/Matrix_product) equals the product of their determinants:

$\det(AB)=\det(A)\det(B)$

This key fact can be proven by observing that, for a fixed matrix $B$, both sides of the equation are alternating and multilinear as a function depending on the columns of $A$. Moreover, they both take the value $\det B$ when $A$ is the identity matrix. The above-mentioned unique characterization of alternating multilinear maps therefore shows this claim.

A matrix $A$ with entries in a [field](https://en.wikipedia.org/wiki/Field_(mathematics) "Field (mathematics)") is [invertible](https://en.wikipedia.org/wiki/Invertible_matrix) precisely if its determinant is nonzero. This follows from the multiplicativity of the determinant and the formula for the inverse involving the adjugate matrix mentioned below. In this event, the determinant of the inverse matrix is given by

$\det \left(A^{-1}\right)={\frac {1}{\det(A)}}=[\det(A)]^{-1}$.

In particular, products and inverses of matrices with non-zero determinant (respectively, determinant one) still have this property. Thus, the set of such matrices (of fixed size $n$ over a field $K$) forms a group known as the [general linear group](https://en.wikipedia.org/wiki/General_linear_group) $\operatorname {GL} _{n}(K)$ (respectively, a [subgroup](https://en.wikipedia.org/wiki/Subgroup) called the [special linear group](https://en.wikipedia.org/wiki/Special_linear_group) $\operatorname {SL} _{n}(K)\subset \operatorname {GL} _{n}(K)$. More generally, the word "special" indicates the subgroup of another [matrix group](https://en.wikipedia.org/wiki/Matrix_group) of matrices of determinant one. Examples include the [special orthogonal group](https://en.wikipedia.org/wiki/Special_orthogonal_group) (which if *n* is 2 or 3 consists of all [rotation matrices](https://en.wikipedia.org/wiki/Rotation_matrix)), and the [special unitary group](https://en.wikipedia.org/wiki/Special_unitary_group).

Because the determinant respects multiplication and inverses, it is in fact a [group homomorphism](https://en.wikipedia.org/wiki/Group_homomorphism) from $\operatorname {GL} _{n}(K)$ into the multiplicative group $K^{\times }$ of nonzero elements of $K$. This homomorphism is surjective and its kernel is $\operatorname {SL} _{n}(K)$ (the matrices with determinant one). Hence, by the [first isomorphism theorem](https://en.wikipedia.org/wiki/First_isomorphism_theorem), this shows that $\operatorname {SL} _{n}(K)$ is a [normal subgroup](https://en.wikipedia.org/wiki/Normal_subgroup) of $\operatorname {GL} _{n}(K)$, and that the [quotient group](https://en.wikipedia.org/wiki/Quotient_group) $\operatorname {GL} _{n}(K)/\operatorname {SL} _{n}(K)$ is isomorphic to $K^{\times }$.

The [Cauchy–Binet formula](https://en.wikipedia.org/wiki/Cauchy%E2%80%93Binet_formula) is a generalization of that product formula for *rectangular* matrices. This formula can also be recast as a multiplicative formula for [compound matrices](https://en.wikipedia.org/wiki/Compound_matrix) whose entries are the determinants of all quadratic submatrices of a given matrix.

### Laplace expansion

[Laplace expansion](https://en.wikipedia.org/wiki/Laplace_expansion) expresses the determinant of a matrix $A$ [recursively](https://en.wikipedia.org/wiki/Recursion) in terms of determinants of smaller matrices, known as its [minors](https://en.wikipedia.org/wiki/Minor_(matrix)). The minor $M_{i,j}$ is defined to be the determinant of the $(n-1)\times (n-1)$ matrix that results from $A$ by removing the $i$-th row and the $j$-th column. The expression $(-1)^{i+j}M_{i,j}$ is known as a [cofactor](https://en.wikipedia.org/wiki/Cofactor_(linear_algebra)). For every $i$, one has the equality

$\det(A)=\sum _{j=1}^{n}(-1)^{i+j}a_{i,j}M_{i,j},$

which is called the *Laplace expansion along the ith row*. For example, the Laplace expansion along the first row ($i=1$) gives the following formula:

${\begin{vmatrix}a&b&c\\d&e&f\\g&h&i\end{vmatrix}}=a{\begin{vmatrix}e&f\\h&i\end{vmatrix}}-b{\begin{vmatrix}d&f\\g&i\end{vmatrix}}+c{\begin{vmatrix}d&e\\g&h\end{vmatrix}}$

Unwinding the determinants of these $2\times 2$-matrices gives back the Leibniz formula mentioned above. Similarly, the *Laplace expansion along the $j$-th column* is the equality

$\det(A)=\sum _{i=1}^{n}(-1)^{i+j}a_{i,j}M_{i,j}.$

Laplace expansion can be used iteratively for computing determinants, but this approach is inefficient for large matrices. However, it is useful for computing the determinants of highly symmetric matrix such as the [Vandermonde matrix](https://en.wikipedia.org/wiki/Vandermonde_matrix) 

$$
{\begin{vmatrix}1&1&1&\cdots &1\\x_{1}&x_{2}&x_{3}&\cdots &x_{n}\\x_{1}^{2}&x_{2}^{2}&x_{3}^{2}&\cdots &x_{n}^{2}\\\vdots &\vdots &\vdots &\ddots &\vdots \\x_{1}^{n-1}&x_{2}^{n-1}&x_{3}^{n-1}&\cdots &x_{n}^{n-1}\end{vmatrix}}=\prod _{1\leq i<j\leq n}\left(x_{j}-x_{i}\right).
$$

The *n*-term Laplace expansion along a row or column can be [generalized](https://en.wikipedia.org/wiki/Laplace_expansion#Laplace_expansion_of_a_determinant_by_complementary_minors) to write an *n* x *n* determinant as a sum of ${\tbinom {n}{k}}$ [terms](https://en.wikipedia.org/wiki/Binomial_coefficient), each the product of the determinant of a *k* x *k* [submatrix](https://en.wikipedia.org/wiki/Minor_(linear_algebra) "Minor (linear algebra)") and the determinant of the complementary (*n−k*) x (*n−k*) submatrix.

### Adjugate matrix

The [adjugate matrix](https://en.wikipedia.org/wiki/Adjugate_matrix) $\operatorname {adj} (A)$ is the transpose of the matrix of the cofactors, that is,

$(\operatorname {adj} (A))_{i,j}=(-1)^{i+j}M_{ji}.$

For every matrix, one has

$(\det A)I=A\operatorname {adj} A=(\operatorname {adj} A)\,A.$

Thus the adjugate matrix can be used for expressing the inverse of a [nonsingular matrix](https://en.wikipedia.org/wiki/Nonsingular_matrix):

$A^{-1}={\frac {1}{\det A}}\operatorname {adj} A.$

### Block matrices

The formula for the determinant of a $2\times 2$ matrix above continues to hold, under appropriate further assumptions, for a [block matrix](https://en.wikipedia.org/wiki/Block_matrix), i.e., a matrix composed of four submatrices $A,B,C,D$ of dimension $m\times m$, $m\times n$, $n\times m$ and $n\times n$, respectively. The easiest such formula, which can be proven using either the Leibniz formula or a factorization involving the [Schur complement](https://en.wikipedia.org/wiki/Schur_complement), is

$\det {\begin{pmatrix}A&0\\C&D\end{pmatrix}}=\det(A)\det(D)=\det {\begin{pmatrix}A&B\\0&D\end{pmatrix}}.$

If $A$ is [invertible](https://en.wikipedia.org/wiki/Invertible_matrix), then it follows with results from the section on multiplicativity that

${\begin{aligned}\det {\begin{pmatrix}A&B\\C&D\end{pmatrix}}&=\det(A)\det {\begin{pmatrix}A&B\\C&D\end{pmatrix}}\underbrace {\det {\begin{pmatrix}A^{-1}&-A^{-1}B\\0&I_{n}\end{pmatrix}}} _{=\,\det(A^{-1})\,=\,(\det A)^{-1}}\\&=\det(A)\det {\begin{pmatrix}I_{m}&0\\CA^{-1}&D-CA^{-1}B\end{pmatrix}}\\&=\det(A)\det(D-CA^{-1}B),\end{aligned}}$

which simplifies to $\det(A)(D-CA^{-1}B)$ when $D$ is a $1\times 1$ matrix.

A similar result holds when $D$ is invertible, namely

${\begin{aligned}\det {\begin{pmatrix}A&B\\C&D\end{pmatrix}}&=\det(D)\det {\begin{pmatrix}A&B\\C&D\end{pmatrix}}\underbrace {\det {\begin{pmatrix}I_{m}&0\\-D^{-1}C&D^{-1}\end{pmatrix}}} _{=\,\det(D^{-1})\,=\,(\det D)^{-1}}\\&=\det(D)\det {\begin{pmatrix}A-BD^{-1}C&BD^{-1}\\0&I_{n}\end{pmatrix}}\\&=\det(D)\det(A-BD^{-1}C).\end{aligned}}$

Both results can be combined to derive [Sylvester's determinant theorem](https://en.wikipedia.org/wiki/Sylvester%27s_determinant_theorem), which is also stated below.

If the blocks are square matrices of the *same* size further formulas hold. For example, if $C$ and $D$ [commute](https://en.wikipedia.org/wiki/Commutativity) (i.e., $CD=DC$), then

$\det {\begin{pmatrix}A&B\\C&D\end{pmatrix}}=\det(AD-BC).$

This formula has been generalized to matrices composed of more than $2\times 2$ blocks, again under appropriate commutativity conditions among the individual blocks.

For $A=D$ and $B=C$, the following formula holds (even if $A$ and $B$ do not commute).

$\det {\begin{pmatrix}A&B\\B&A\end{pmatrix}}=\det {\begin{pmatrix}A+B&B\\B+A&A\end{pmatrix}}=\det {\begin{pmatrix}A+B&B\\0&A-B\end{pmatrix}}=\det(A+B)\det(A-B).$

It is possible to compute the determinant by the block matrices in a fast way with the use of [fast matrix multiplication algorithms](https://en.wikipedia.org/wiki/Computational_complexity_of_matrix_multiplication) in the time $O({n^{\omega }})$ for $~2.37\leq \omega <3$, by the $LU$ decomposition.

### Sylvester's determinant theorem

[Sylvester's determinant theorem](https://en.wikipedia.org/wiki/Sylvester%27s_determinant_theorem) states that for *A*, an *m* × *n* matrix, and *B*, an *n* × *m* matrix (so that *A* and *B* have dimensions allowing them to be multiplied in either order forming a square matrix):

$\det \left(I_{\mathit {m}}+AB\right)=\det \left(I_{\mathit {n}}+BA\right),$

where *I*<sub>*m*</sub> and *I*<sub>*n*</sub> are the *m* × *m* and *n* × *n* identity matrices, respectively.

From this general result several consequences follow.

1.  For the case of column vector *c* and row vector *r*, each with *m* components, the formula allows quick calculation of the determinant of a matrix that differs from the identity matrix by a matrix of rank 1:
    $\det \left(I_{\mathit {m}}+cr\right)=1+rc.$
2.  More generally, for any invertible *m* × *m* matrix *X*,
    $\det(X+AB)=\det(X)\det \left(I_{\mathit {n}}+BX^{-1}A\right),$
3.  For a column and row vector as above:
    $\det(X+cr)=\det(X)\det \left(1+rX^{-1}c\right)=\det(X)+r\,\operatorname {adj} (X)\,c.$
4.  For square matrices $A$ and $B$ of the same size, the matrices $AB$ and $BA$ have the same characteristic polynomials (hence the same eigenvalues).

A generalization is $\det \left(Z+AWB\right)=\det \left(Z\right)\det \left(W\right)\det \left(W^{-1}+BZ^{-1}A\right)$(see [Matrix determinant lemma](https://en.wikipedia.org/wiki/Matrix_determinant_lemma)), where *Z* is an *m* × *m* invertible matrix and *W* is an *n* × *n* invertible matrix.

### Sum

The determinant of the sum $A+B$ of two square matrices of the same size is not in general expressible in terms of the determinants of *A* and of *B*.

However, for [[Positive-Definite Matrix|positive semidefinite matrices]] $A$, $B$ and $C$ of equal size, 

$$
\det(A+B+C)+\det(C)\geq \det(A+C)+\det(B+C){\text{,}}
$$

 with the corollary 

$$
\det(A+B)\geq \det(A)+\det(B){\text{.}}
$$

[Brunn–Minkowski theorem](https://en.wikipedia.org/wiki/Brunn%E2%80%93Minkowski_theorem) implies that the nth root of determinant is a [concave function](https://en.wikipedia.org/wiki/Concave_function), when restricted to [Hermitian](https://en.wikipedia.org/wiki/Hermitian_matrix) positive-definite $n\times n$ matrices. Therefore, if A and B are Hermitian positive-definite $n\times n$ matrices, one has 

$$
{\sqrt[{n}]{\det(A+B)}}\geq {\sqrt[{n}]{\det(A)}}+{\sqrt[{n}]{\det(B)}},
$$

 since the nth root of the determinant is a [homogeneous function](https://en.wikipedia.org/wiki/Homogeneous_function).

#### Sum identity for 2×2 matrices

For the special case of $2\times 2$ matrices with complex entries, the determinant of the sum can be written in terms of determinants and traces in the following identity:

$\det(A+B)=\det(A)+\det(B)+{\text{tr}}(A){\text{tr}}(B)-{\text{tr}}(AB).$

## Properties of the determinant in relation to other notions

### Eigenvalues and characteristic polynomial

The determinant is closely related to two other central concepts in linear algebra, the [eigenvalues](https://en.wikipedia.org/wiki/Eigenvalue) and the [characteristic polynomial](https://en.wikipedia.org/wiki/Characteristic_polynomial) of a matrix. Let $A$ be an $n\times n$ matrix with [complex](https://en.wikipedia.org/wiki/Complex_number) entries. Then, by the Fundamental Theorem of Algebra, $A$ must have exactly *n* [eigenvalues](https://en.wikipedia.org/wiki/Eigenvectors) $\lambda _{1},\lambda _{2},\ldots ,\lambda _{n}$. (Here it is understood that an eigenvalue with [algebraic multiplicity](https://en.wikipedia.org/wiki/Algebraic_multiplicity) μ occurs μ times in this list.) Then, it turns out the determinant of A is equal to the *product* of these eigenvalues,

$\det(A)=\prod _{i=1}^{n}\lambda _{i}=\lambda _{1}\lambda _{2}\cdots \lambda _{n}.$

The product of all non-zero eigenvalues is referred to as [pseudo-determinant](https://en.wikipedia.org/wiki/Pseudo-determinant).

From this, one immediately sees that the determinant of a matrix $A$ is zero if and only if $0$ is an eigenvalue of $A$. In other words, $A$ is invertible if and only if $0$ is not an eigenvalue of $A$.

The characteristic polynomial is defined as

$\chi _{A}(t)=\det(t\cdot I-A).$

Here, $t$ is the [indeterminate](https://en.wikipedia.org/wiki/Indeterminate_(variable)) of the polynomial and $I$ is the identity matrix of the same size as $A$. By means of this polynomial, determinants can be used to find the [eigenvalues](https://en.wikipedia.org/wiki/Eigenvalue) of the matrix $A$: they are precisely the [roots](https://en.wikipedia.org/wiki/Root_of_a_polynomial) of this polynomial, i.e., those complex numbers $\lambda$ such that

$\chi _{A}(\lambda )=0.$

A [Hermitian matrix](https://en.wikipedia.org/wiki/Hermitian_matrix) is [[Positive-Definite Matrix|positive definite]] if all its eigenvalues are positive. [Sylvester's criterion](https://en.wikipedia.org/wiki/Sylvester%27s_criterion) asserts that this is equivalent to the determinants of the submatrices

$A_{k}:={\begin{bmatrix}a_{1,1}&a_{1,2}&\cdots &a_{1,k}\\a_{2,1}&a_{2,2}&\cdots &a_{2,k}\\\vdots &\vdots &\ddots &\vdots \\a_{k,1}&a_{k,2}&\cdots &a_{k,k}\end{bmatrix}}$

being positive, for all $k$ between $1$ and $n$.

### Trace

The [trace](https://en.wikipedia.org/wiki/Trace_(linear_algebra) "Trace (linear algebra)") tr(*A*) is by definition the sum of the diagonal entries of A and also equals the sum of the eigenvalues. Thus, for complex matrices A,

$\det(\exp(A))=\exp(\operatorname {tr} (A))$

or, for real matrices A,

$\operatorname {tr} (A)=\log(\det(\exp(A))).$

Here exp(A) denotes the [matrix exponential](https://en.wikipedia.org/wiki/Matrix_exponential) of A, because every eigenvalue λ of A corresponds to the eigenvalue exp(λ) of exp(A). In particular, given any [logarithm](https://en.wikipedia.org/wiki/Matrix_logarithm) of A, that is, any matrix L satisfying

$\exp(L)=A$

the determinant of A is given by

$\det(A)=\exp(\operatorname {tr} (L)).$

For example, for *n* = 2, *n* = 3, and *n* = 4, respectively,

${\begin{aligned}\det(A)&={\frac {1}{2}}\left(\left(\operatorname {tr} (A)\right)^{2}-\operatorname {tr} \left(A^{2}\right)\right),\\\det(A)&={\frac {1}{6}}\left(\left(\operatorname {tr} (A)\right)^{3}-3\operatorname {tr} (A)~\operatorname {tr} \left(A^{2}\right)+2\operatorname {tr} \left(A^{3}\right)\right),\\\det(A)&={\frac {1}{24}}\left(\left(\operatorname {tr} (A)\right)^{4}-6\operatorname {tr} \left(A^{2}\right)\left(\operatorname {tr} (A)\right)^{2}+3\left(\operatorname {tr} \left(A^{2}\right)\right)^{2}+8\operatorname {tr} \left(A^{3}\right)~\operatorname {tr} (A)-6\operatorname {tr} \left(A^{4}\right)\right).\end{aligned}}$

cf. [Cayley-Hamilton theorem](https://en.wikipedia.org/wiki/Cayley%E2%80%93Hamilton_theorem#Illustration_for_specific_dimensions_and_practical_applications). Such expressions are deducible from combinatorial arguments, [Newton's identities](https://en.wikipedia.org/wiki/Newton%27s_identities#Computing_coefficients), or the [Faddeev–LeVerrier algorithm](https://en.wikipedia.org/wiki/Faddeev%E2%80%93LeVerrier_algorithm). That is, for generic n, det*A* = (−1)<sup>*n*</sup>*c*<sub>0</sub> the signed constant term of the [characteristic polynomial](https://en.wikipedia.org/wiki/Characteristic_polynomial), determined recursively from

$c_{n}=1;~~~c_{n-m}=-{\frac {1}{m}}\sum _{k=1}^{m}c_{n-m+k}\operatorname {tr} \left(A^{k}\right)~~(1\leq m\leq n)~.$

In the general case, this may also be obtained from

$\det(A)=\sum _{\begin{array}{c}k_{1},k_{2},\ldots ,k_{n}\geq 0\\k_{1}+2k_{2}+\cdots +nk_{n}=n\end{array}}\prod _{l=1}^{n}{\frac {(-1)^{k_{l}+1}}{l^{k_{l}}k_{l}!}}\operatorname {tr} \left(A^{l}\right)^{k_{l}},$

where the sum is taken over the set of all integers *k<sub>l</sub>* ≥ 0 satisfying the equation

$\sum _{l=1}^{n}lk_{l}=n.$

The formula can be expressed in terms of the complete exponential [Bell polynomial](https://en.wikipedia.org/wiki/Bell_polynomial) of *n* arguments *s*<sub>*l*</sub> = −(*l* – 1)! tr(*A*<sup>*l*</sup>) as

$\det(A)={\frac {(-1)^{n}}{n!}}B_{n}(s_{1},s_{2},\ldots ,s_{n}).$

This formula can also be used to find the determinant of a matrix *A<sup>I</sup><sub>J</sub>* with multidimensional indices *I* = (*i*<sub>1</sub>, *i*<sub>2</sub>, ..., *i<sub>r</sub>*) and *J* = (*j*<sub>1</sub>, *j*<sub>2</sub>, ..., *j<sub>r</sub>*). The product and trace of such matrices are defined in a natural way as

$(AB)_{J}^{I}=\sum _{K}A_{K}^{I}B_{J}^{K},\operatorname {tr} (A)=\sum _{I}A_{I}^{I}.$

An important arbitrary dimension n identity can be obtained from the [Mercator series](https://en.wikipedia.org/wiki/Mercator_series) expansion of the logarithm when the expansion converges. If every eigenvalue of *A* is less than 1 in absolute value,

$\det(I+A)=\sum _{k=0}^{\infty }{\frac {1}{k!}}\left(-\sum _{j=1}^{\infty }{\frac {(-1)^{j}}{j}}\operatorname {tr} \left(A^{j}\right)\right)^{k}\,,$

where *I* is the identity matrix. More generally, if

$\sum _{k=0}^{\infty }{\frac {1}{k!}}\left(-\sum _{j=1}^{\infty }{\frac {(-1)^{j}s^{j}}{j}}\operatorname {tr} \left(A^{j}\right)\right)^{k}\,,$

is expanded as a formal [power series](https://en.wikipedia.org/wiki/Power_series) in s then all coefficients of s<sup>m</sup> for *m* \> *n* are zero and the remaining polynomial is det(*I* + *sA*).

### Upper and lower bounds

For a positive definite matrix *A*, the trace operator gives the following tight lower and upper bounds on the log determinant

$\operatorname {tr} \left(I-A^{-1}\right)\leq \log \det(A)\leq \operatorname {tr} (A-I)$

with equality if and only if *A* = *I*. This relationship can be derived via the formula for the [[Kullback-Leibler Divergence|Kullback–Leibler divergence]] between two [multivariate normal](https://en.wikipedia.org/wiki/Multivariate_normal) distributions.

Also,

${\frac {n}{\operatorname {tr} \left(A^{-1}\right)}}\leq \det(A)^{\frac {1}{n}}\leq {\frac {1}{n}}\operatorname {tr} (A)\leq {\sqrt {{\frac {1}{n}}\operatorname {tr} \left(A^{2}\right)}}.$

These inequalities can be proved by expressing the traces and the determinant in terms of the eigenvalues. As such, they represent the well-known fact that the [harmonic mean](https://en.wikipedia.org/wiki/Harmonic_mean) is less than the [geometric mean](https://en.wikipedia.org/wiki/Geometric_mean), which is less than the [arithmetic mean](https://en.wikipedia.org/wiki/Arithmetic_mean), which is, in turn, less than the [root mean square](https://en.wikipedia.org/wiki/Root_mean_square).

### Derivative

The Leibniz formula shows that the determinant of real (or analogously for complex) square matrices is a [polynomial](https://en.wikipedia.org/wiki/Polynomial) function from $\mathbf {R} ^{n\times n}$ to $\mathbf {R}$. In particular, it is everywhere [differentiable](https://en.wikipedia.org/wiki/Differentiable). Its derivative can be expressed using [Jacobi's formula](https://en.wikipedia.org/wiki/Jacobi%27s_formula):

${\frac {d\det(A)}{d\alpha }}=\operatorname {tr} \left(\operatorname {adj} (A){\frac {dA}{d\alpha }}\right).$

where $\operatorname {adj} (A)$ denotes the [adjugate](https://en.wikipedia.org/wiki/Adjugate) of $A$. In particular, if $A$ is invertible, we have

${\frac {d\det(A)}{d\alpha }}=\det(A)\operatorname {tr} \left(A^{-1}{\frac {dA}{d\alpha }}\right).$

Expressed in terms of the entries of $A$, these are

${\frac {\partial \det(A)}{\partial A_{ij}}}=\operatorname {adj} (A)_{ji}=\det(A)\left(A^{-1}\right)_{ji}.$

Yet another equivalent formulation is

$\det(A+\epsilon X)-\det(A)=\operatorname {tr} (\operatorname {adj} (A)X)\epsilon +O\left(\epsilon ^{2}\right)=\det(A)\operatorname {tr} \left(A^{-1}X\right)\epsilon +O\left(\epsilon ^{2}\right)$,

using [big O notation](https://en.wikipedia.org/wiki/Big_O_notation). The special case where $A=I$, the identity matrix, yields

$\det(I+\epsilon X)=1+\operatorname {tr} (X)\epsilon +O\left(\epsilon ^{2}\right).$

This identity is used in describing [Lie algebras](https://en.wikipedia.org/wiki/Lie_algebra) associated to certain matrix [Lie groups](https://en.wikipedia.org/wiki/Lie_group). For example, the special linear group $\operatorname {SL} _{n}$ is defined by the equation $\det A=1$. The above formula shows that its Lie algebra is the [special linear Lie algebra](https://en.wikipedia.org/wiki/Special_linear_Lie_algebra) ${\mathfrak {sl}}_{n}$ consisting of those matrices having trace zero.

Writing a $3\times 3$ matrix as $A={\begin{bmatrix}a&b&c\end{bmatrix}}$ where $a,b,c$ are column vectors of length 3, then the gradient over one of the three vectors may be written as the [cross product](https://en.wikipedia.org/wiki/Cross_product) of the other two:

${\begin{aligned}\nabla _{\mathbf {a} }\det(A)&=\mathbf {b} \times \mathbf {c} \\\nabla _{\mathbf {b} }\det(A)&=\mathbf {c} \times \mathbf {a} \\\nabla _{\mathbf {c} }\det(A)&=\mathbf {a} \times \mathbf {b} .\end{aligned}}$

## History

Historically, determinants were used long before matrices: A determinant was originally defined as a property of a [system of linear equations](https://en.wikipedia.org/wiki/System_of_linear_equations). The determinant "determines" whether the system has a unique solution (which occurs precisely if the determinant is non-zero). In this sense, determinants were first used in the Chinese mathematics textbook *[The Nine Chapters on the Mathematical Art](https://en.wikipedia.org/wiki/The_Nine_Chapters_on_the_Mathematical_Art)* (九章算術, Chinese scholars, around the 3rd century BCE). In Europe, solutions of linear systems of two equations were expressed by [Cardano](https://en.wikipedia.org/wiki/Gerolamo_Cardano) in 1545 by a determinant-like entity.

Determinants proper originated separately from the work of [Seki Takakazu](https://en.wikipedia.org/wiki/Seki_Takakazu) in 1683 in Japan and parallelly of [Leibniz](https://en.wikipedia.org/wiki/Gottfried_Leibniz) in 1693.  stated, without proof, Cramer's rule. Both Cramer and also  were led to determinants by the question of [plane curves](https://en.wikipedia.org/wiki/Plane_curve) passing through a given set of points.

[Vandermonde](https://en.wikipedia.org/wiki/Vandermonde) (1771) first recognized determinants as independent functions.  gave the general method of expanding a determinant in terms of its complementary [minors](https://en.wikipedia.org/wiki/Minor_(matrix)): Vandermonde had already given a special case. Immediately following, [Lagrange](https://en.wikipedia.org/wiki/Joseph_Louis_Lagrange) (1773) treated determinants of the second and third order and applied it to questions of [elimination theory](https://en.wikipedia.org/wiki/Elimination_theory); he proved many special cases of general identities.

[Gauss](https://en.wikipedia.org/wiki/Carl_Friedrich_Gauss) (1801) made the next advance. Like Lagrange, he made much use of determinants in the [theory of numbers](https://en.wikipedia.org/wiki/Theory_of_numbers). He introduced the word "determinant" (Laplace had used "resultant"), though not in the present signification, but rather as applied to the [discriminant](https://en.wikipedia.org/wiki/Discriminant) of a [quadratic form](https://en.wikipedia.org/wiki/Quadratic_form). Gauss also arrived at the notion of reciprocal (inverse) determinants, and came very near the multiplication theorem.<sup>\[*[clarification needed](https://en.wikipedia.org/wiki/Wikipedia:Please_clarify)*\]</sup>

The next contributor of importance is [Binet](https://en.wikipedia.org/wiki/Jacques_Philippe_Marie_Binet) (1811, 1812), who formally stated the theorem relating to the product of two matrices of *m* columns and *n* rows, which for the special case of *m* = *n* reduces to the multiplication theorem. On the same day (November 30, 1812) that Binet presented his paper to the Academy, [Cauchy](https://en.wikipedia.org/wiki/Cauchy) also presented one on the subject. (See [Cauchy–Binet formula](https://en.wikipedia.org/wiki/Cauchy%E2%80%93Binet_formula).) In this he used the word "determinant" in its present sense, summarized and simplified what was then known on the subject, improved the notation, and gave the multiplication theorem with a proof more satisfactory than Binet's. With him begins the theory in its generality.

 used the functional determinant which Sylvester later called the [Jacobian](https://en.wikipedia.org/wiki/Jacobian_matrix_and_determinant). In his memoirs in *[Crelle's Journal](https://en.wikipedia.org/wiki/Crelle%27s_Journal)* for 1841 he specially treats this subject, as well as the class of alternating functions which Sylvester has called *alternants*. About the time of Jacobi's last memoirs, [Sylvester](https://en.wikipedia.org/wiki/James_Joseph_Sylvester) (1839) and [Cayley](https://en.wikipedia.org/wiki/Arthur_Cayley) began their work.  introduced the modern notation for the determinant using vertical bars.

The study of special forms of determinants has been the natural result of the completion of the general theory. Axisymmetric determinants have been studied by [Lebesgue](https://en.wikipedia.org/wiki/Lebesgue), [Hesse](https://en.wikipedia.org/wiki/Otto_Hesse), and Sylvester; [persymmetric](https://en.wikipedia.org/wiki/Persymmetric) determinants by Sylvester and [Hankel](https://en.wikipedia.org/wiki/Hermann_Hankel); [circulants](https://en.wikipedia.org/wiki/Circulant) by [Catalan](https://en.wikipedia.org/wiki/Eug%C3%A8ne_Charles_Catalan), [Spottiswoode](https://en.wikipedia.org/wiki/William_Spottiswoode), [Glaisher](https://en.wikipedia.org/wiki/James_Whitbread_Lee_Glaisher), and Scott; skew determinants and [Pfaffians](https://en.wikipedia.org/wiki/Pfaffian), in connection with the theory of [orthogonal transformation](https://en.wikipedia.org/wiki/Orthogonal_transformation), by Cayley; continuants by Sylvester; [Wronskians](https://en.wikipedia.org/wiki/Wronskian) (so called by [Muir](https://en.wikipedia.org/wiki/Thomas_Muir_(mathematician) "Thomas Muir (mathematician)")) by [Christoffel](https://en.wikipedia.org/wiki/Elwin_Bruno_Christoffel) and [Frobenius](https://en.wikipedia.org/wiki/Ferdinand_Georg_Frobenius); compound determinants by Sylvester, Reiss, and Picquet; Jacobians and [[Hessian Matrix|Hessians]] by Sylvester; and symmetric gauche determinants by [Trudi](https://en.wikipedia.org/wiki/Trudi). Of the textbooks on the subject Spottiswoode's was the first. In America, Hanus (1886), Weld (1893), and Muir/Metzler (1933) published treatises.

## Applications

### Cramer's rule

Determinants can be used to describe the solutions of a [linear system of equations](https://en.wikipedia.org/wiki/Linear_system_of_equations), written in matrix form as $Ax=b$. This equation has a unique solution $x$ if and only if $\det(A)$ is nonzero. In this case, the solution is given by [Cramer's rule](https://en.wikipedia.org/wiki/Cramer%27s_rule):

$x_{i}={\frac {\det(A_{i})}{\det(A)}}\qquad i=1,2,3,\ldots ,n$

where $A_{i}$ is the matrix formed by replacing the $i$-th column of $A$ by the column vector $b$. This follows immediately by column expansion of the determinant, i.e.

$\det(A_{i})=\det {\begin{bmatrix}a_{1}&\ldots &b&\ldots &a_{n}\end{bmatrix}}$

$=\sum _{j=1}^{n}x_{j}\det {\begin{bmatrix}a_{1}&\ldots &a_{i-1}&a_{j}&a_{i+1}&\ldots &a_{n}\end{bmatrix}}=x_{i}\det(A)$

where the vectors $a_{j}$ are the columns of *A*. The rule is also implied by the identity

$A\,\operatorname {adj} (A)=\operatorname {adj} (A)\,A=\det(A)\,I_{n}.$

Cramer's rule can be implemented in $\operatorname {O} (n^{3})$ time, which is comparable to more common methods of solving systems of linear equations, such as [[LU Decomposition|LU]], [[QR Decomposition|QR]], or [[Singular Value Decomposition]].

### Linear independence

Determinants can be used to characterize [[Linear Independence|linearly dependent]] vectors: $\det A$ is zero if and only if the column vectors of the matrix $A$ are linearly dependent. For example, given two linearly independent vectors $v_{1},v_{2}\in \mathbf {R} ^{3}$, a third vector $v_{3}$ lies in the [plane](https://en.wikipedia.org/wiki/Plane_(geometry)) [spanned](https://en.wikipedia.org/wiki/Linear_span) by the former two vectors exactly if the determinant of the $3\times 3$ matrix consisting of the three vectors is zero. The same idea is also used in the theory of [differential equations](https://en.wikipedia.org/wiki/Differential_equation): given functions $f_{1}(x),\dots ,f_{n}(x)$ (supposed to be $n-1$ times [differentiable](https://en.wikipedia.org/wiki/Differentiable_function)), the [Wronskian](https://en.wikipedia.org/wiki/Wronskian) is defined to be

$W(f_{1},\ldots ,f_{n})(x)={\begin{vmatrix}f_{1}(x)&f_{2}(x)&\cdots &f_{n}(x)\\f_{1}'(x)&f_{2}'(x)&\cdots &f_{n}'(x)\\\vdots &\vdots &\ddots &\vdots \\f_{1}^{(n-1)}(x)&f_{2}^{(n-1)}(x)&\cdots &f_{n}^{(n-1)}(x)\end{vmatrix}}.$

It is non-zero (for some $x$) in a specified interval if and only if the given functions and all their derivatives up to order $n-1$ are linearly independent. If it can be shown that the Wronskian is zero everywhere on an interval then, in the case of [analytic functions](https://en.wikipedia.org/wiki/Analytic_function), this implies the given functions are linearly dependent. See [the Wronskian and linear independence](https://en.wikipedia.org/wiki/Wronskian#The_Wronskian_and_linear_independence). Another such use of the determinant is the [resultant](https://en.wikipedia.org/wiki/Resultant), which gives a criterion when two [polynomials](https://en.wikipedia.org/wiki/Polynomial) have a common [root](https://en.wikipedia.org/wiki/Root_of_a_function).

### Cross Product

The computation of a cross product is equivalent to finding the [formal](https://en.wikipedia.org/wiki/Formal_calculation) determinant a specific 3 by 3 matrix. Specifically, for vectors $\mathbf {a} =a_{1}\mathbf {i} +a_{2}\mathbf {j} +a_{3}\mathbf {k}$, and $\mathbf {b} =b_{1}\mathbf {i} +b_{2}\mathbf {j} +b_{3}\mathbf {k}$:

$$
\mathbf {a\times b} =\det {\begin{pmatrix}\mathbf {i} &\mathbf {j} &\mathbf {k} \\a_{1}&a_{2}&a_{3}\\b_{1}&b_{2}&b_{3}\\\end{pmatrix}}
$$

### Orientation of a basis

The determinant can be thought of as assigning a number to every [sequence](https://en.wikipedia.org/wiki/Sequence) of *n* vectors in **R**<sup>*n*</sup>, by using the square matrix whose columns are the given vectors. The determinant will be nonzero if and only if the sequence of vectors is a *basis* for **R**<sup>*n*</sup>. In that case, the sign of the determinant determines whether the [orientation](https://en.wikipedia.org/wiki/Orientation_(vector_space) "Orientation (vector space)") of the basis is consistent with or opposite to the orientation of the [standard basis](https://en.wikipedia.org/wiki/Standard_basis). In the case of an orthogonal basis, the magnitude of the determinant is equal to the *product* of the lengths of the basis vectors. For instance, an [orthogonal matrix](https://en.wikipedia.org/wiki/Orthogonal_matrix) with entries in **R**<sup>*n*</sup> represents an [orthonormal basis](https://en.wikipedia.org/wiki/Orthonormal_basis) in [Euclidean space](https://en.wikipedia.org/wiki/Euclidean_space), and hence has determinant of ±1 (since all the vectors have length 1). The determinant is +1 if and only if the basis has the same orientation. It is −1 if and only if the basis has the opposite orientation.

More generally, if the determinant of *A* is positive, *A* represents an orientation-preserving [[Linear Transformation]] (if *A* is an orthogonal 2 × 2 or 3 × 3 matrix, this is a [rotation](https://en.wikipedia.org/wiki/Rotation_(mathematics) "Rotation (mathematics)")), while if it is negative, *A* switches the orientation of the basis.

### Volume and Jacobian determinant

As pointed out above, the [absolute value](https://en.wikipedia.org/wiki/Absolute_value) of the determinant of real vectors is equal to the volume of the [parallelepiped](https://en.wikipedia.org/wiki/Parallelepiped) spanned by those vectors. As a consequence, if $f:\mathbf {R} ^{n}\to \mathbf {R} ^{n}$ is the linear map given by multiplication with a matrix $A$, and $S\subset \mathbf {R} ^{n}$ is any [measurable](https://en.wikipedia.org/wiki/Lebesgue_measure) [subset](https://en.wikipedia.org/wiki/Subset), then the volume of $f(S)$ is given by $|\det(A)|$ times the volume of $S$. More generally, if the linear map $f:\mathbf {R} ^{n}\to \mathbf {R} ^{m}$ is represented by the $m\times n$ matrix $A$, then the ratio between the $n$-[dimensional](https://en.wikipedia.org/wiki/Dimension) volumes of $f(S)$ and $S$ is given by:

${\frac {\operatorname {volume} (f(S))}{\operatorname {volume} (S)}}={\sqrt {\det \left(A^{\textsf {T}}A\right)}}.$

When $m<n$ this is zero.

By calculating the volume of the [tetrahedron](https://en.wikipedia.org/wiki/Tetrahedron) bounded by four points, they can be used to identify [skew lines](https://en.wikipedia.org/wiki/Skew_line). The volume of any tetrahedron, given its [vertices](https://en.wikipedia.org/wiki/Vertex_(geometry) "Vertex (geometry)") $a,b,c,d$, ${\frac {1}{6}}\cdot |\det(a-b,b-c,c-d)|$, or any other combination of pairs of vertices that form a [spanning tree](https://en.wikipedia.org/wiki/Spanning_tree) over the vertices.

![[media/874028084dcf4439b7e21ec675895405bf663b50.png]]
A nonlinear map $f\colon \mathbf {R} ^{2}\to \mathbf {R} ^{2}$ sends a small square (left, in red) to a distorted parallelogram (right, in red). The Jacobian at a point gives the best linear approximation of the distorted parallelogram near that point (right, in translucent white), and the Jacobian determinant gives the ratio of the area of the approximating parallelogram to that of the original square.

For a general [differentiable function](https://en.wikipedia.org/wiki/Differentiable_function), much of the above carries over by considering the [[Jacobian Matrix]] of *f*. For

$f:\mathbf {R} ^{n}\rightarrow \mathbf {R} ^{n},$

the Jacobian matrix is the *n* × *n* matrix whose entries are given by the [partial derivatives](https://en.wikipedia.org/wiki/Partial_derivative)

$D(f)=\left({\frac {\partial f_{i}}{\partial x_{j}}}\right)_{1\leq i,j\leq n}.$

Its determinant, the [Jacobian determinant](https://en.wikipedia.org/wiki/Jacobian_determinant), appears in the higher-dimensional version of [integration by substitution](https://en.wikipedia.org/wiki/Integration_by_substitution): for suitable functions *f* and an [open subset](https://en.wikipedia.org/wiki/Open_subset) *U* of **R**<sup>*n*</sup> (the domain of *f*), the integral over *f*(*U*) of some other function *φ* : **R**<sup>*n*</sup> → **R**<sup>*m*</sup> is given by

$\int _{f(U)}\phi (\mathbf {v} )\,d\mathbf {v} =\int _{U}\phi (f(\mathbf {u} ))\left|\det(\operatorname {D} f)(\mathbf {u} )\right|\,d\mathbf {u} .$

The Jacobian also occurs in the [inverse function theorem](https://en.wikipedia.org/wiki/Inverse_function_theorem).

When applied to the field of [Cartography](https://en.wikipedia.org/wiki/Cartography), the determinant can be used to measure the rate of expansion of a map near the poles.

### Areas and Collinearity

The determinant provides a convenient way to calculate the area of a triangle in the xy-plane. The area of a triangle whose vertices are $(x_{1},y_{1})$, $(x_{2},y_{2})$ and $(x_{3},y_{3})$ is given by:

$\pm {\frac {1}{2}}\det {\begin{pmatrix}x_{1}&y_{1}&1\\x_{2}&y_{2}&1\\x_{3}&y_{3}&1\end{pmatrix}}$

where the sign $\pm$ is chosen to yield a positive area. An immediate [corollary](https://en.wikipedia.org/wiki/Corollary) of this result is that if the determinant is zero, there is no triangle, which implies the points are [collinear](https://en.wikipedia.org/wiki/Collinear). The determinant, therefore, provides a useful tool to test for collinearity.

## Abstract algebraic aspects 

### Determinant of an endomorphism

The above identities concerning the determinant of products and inverses of matrices imply that [similar matrices](https://en.wikipedia.org/wiki/Matrix_similarity) have the same determinant: two matrices *A* and *B* are similar, if there exists an invertible matrix *X* such that *A* = *X*<sup>−1</sup>*BX*. Indeed, repeatedly applying the above identities yields

$\det(A)=\det(X)^{-1}\det(B)\det(X)=\det(B)\det(X)^{-1}\det(X)=\det(B).$

The determinant is therefore also called a [similarity invariant](https://en.wikipedia.org/wiki/Similarity_invariance). The determinant of a [[Linear Transformation]]

$T:V\to V$

for some finite-dimensional [[Vector Space]] *V* is defined to be the determinant of the matrix describing it, with respect to an arbitrary choice of [basis](https://en.wikipedia.org/wiki/Basis_(linear_algebra) "Basis (linear algebra)") in *V*. By the similarity invariance, this determinant is independent of the choice of the basis for *V* and therefore only depends on the endomorphism *T*.

### Square matrices over commutative rings

The above definition of the determinant using the Leibniz rule works more generally when the entries of the matrix are elements of a [commutative ring](https://en.wikipedia.org/wiki/Commutative_ring) $R$, such as the integers $\mathbf {Z}$, as opposed to the [field](https://en.wikipedia.org/wiki/Field_(mathematics) "Field (mathematics)") of real or complex numbers. Moreover, the characterization of the determinant as the unique alternating multilinear map that satisfies $\det(I)=1$ still holds, as do all the properties that result from that characterization.

A matrix $A\in \operatorname {Mat} _{n\times n}(R)$ is invertible (in the sense that there is an inverse matrix whose entries are in $R$) if and only if its determinant is an [invertible element](https://en.wikipedia.org/wiki/Unit_(ring_theory) "Unit (ring theory)") in $R$. For $R=\mathbf {Z}$, this means that the determinant is +1 or −1. Such a matrix is called [unimodular](https://en.wikipedia.org/wiki/Unimodular_matrix).

The determinant being multiplicative, it defines a [group homomorphism](https://en.wikipedia.org/wiki/Group_homomorphism)

$\operatorname {GL} _{n}(R)\rightarrow R^{\times },$

between the [general linear group](https://en.wikipedia.org/wiki/General_linear_group) (the group of invertible $n\times n$-matrices with entries in $R$) and the [multiplicative group](https://en.wikipedia.org/wiki/Multiplicative_group) of units in $R$. Since it respects the multiplication in both groups, this map is a [group homomorphism](https://en.wikipedia.org/wiki/Group_homomorphism).

![[media/b7e8b379e833efef927012f1f1bccb90341ddbd7.png]]
The determinant is a natural transformation.

Given a [ring homomorphism](https://en.wikipedia.org/wiki/Ring_homomorphism) $f:R\to S$, there is a map $\operatorname {GL} _{n}(f):\operatorname {GL} _{n}(R)\to \operatorname {GL} _{n}(S)$ given by replacing all entries in $R$ by their images under $f$. The determinant respects these maps, i.e., the identity

$f(\det((a_{i,j})))=\det((f(a_{i,j})))$

holds. In other words, the displayed commutative diagram commutes.

For example, the determinant of the [complex conjugate](https://en.wikipedia.org/wiki/Complex_conjugate) of a complex matrix (which is also the determinant of its conjugate transpose) is the complex conjugate of its determinant, and for integer matrices: the reduction modulo $m$ of the determinant of such a matrix is equal to the determinant of the matrix reduced modulo $m$ (the latter determinant being computed using [modular arithmetic](https://en.wikipedia.org/wiki/Modular_arithmetic)). In the language of [category theory](https://en.wikipedia.org/wiki/Category_theory), the determinant is a [natural transformation](https://en.wikipedia.org/wiki/Natural_transformation) between the two functors $\operatorname {GL} _{n}$ and $(-)^{\times }$. Adding yet another layer of abstraction, this is captured by saying that the determinant is a morphism of [algebraic groups](https://en.wikipedia.org/wiki/Algebraic_group), from the general linear group to the [multiplicative group](https://en.wikipedia.org/wiki/Multiplicative_group),

$\det :\operatorname {GL} _{n}\to \mathbb {G} _{m}.$

### Exterior algebra

The determinant of a linear transformation $T:V\to V$ of an $n$-dimensional vector space $V$ or, more generally a [free module](https://en.wikipedia.org/wiki/Free_module) of (finite) [rank](https://en.wikipedia.org/wiki/Rank_of_a_module) $n$ over a commutative ring $R$ can be formulated in a coordinate-free manner by considering the $n$-th [exterior power](https://en.wikipedia.org/wiki/Exterior_algebra) $\bigwedge ^{n}V$ of $V$. The map $T$ induces a linear map

${\begin{aligned}\bigwedge ^{n}T:\bigwedge ^{n}V&\rightarrow \bigwedge ^{n}V\\v_{1}\wedge v_{2}\wedge \dots \wedge v_{n}&\mapsto Tv_{1}\wedge Tv_{2}\wedge \dots \wedge Tv_{n}.\end{aligned}}$

As $\bigwedge ^{n}V$ is one-dimensional, the map $\bigwedge ^{n}T$ is given by multiplying with some scalar, i.e., an element in $R$. Some authors such as () use this fact to *define* the determinant to be the element in $R$ satisfying the following identity (for all $v_{i}\in V$):

$\left(\bigwedge ^{n}T\right)\left(v_{1}\wedge \dots \wedge v_{n}\right)=\det(T)\cdot v_{1}\wedge \dots \wedge v_{n}.$

This definition agrees with the more concrete coordinate-dependent definition. This can be shown using the uniqueness of a multilinear alternating form on $n$-tuples of vectors in $R^{n}$. For this reason, the highest non-zero exterior power $\bigwedge ^{n}V$ (as opposed to the determinant associated to an endomorphism) is sometimes also called the determinant of $V$ and similarly for more involved objects such as [vector bundles](https://en.wikipedia.org/wiki/Vector_bundle) or [chain complexes](https://en.wikipedia.org/wiki/Chain_complex) of vector spaces. Minors of a matrix can also be cast in this setting, by considering lower alternating forms $\bigwedge ^{k}V$ with $k<n$.

## Berezin integral

The conventional definition of the determinant, as a sum over permutations over a product of matrix elements, can be written using the somewhat surprising notation of the [Berezin integral](https://en.wikipedia.org/wiki/Berezin_integral). In this notation, the determinant can be written as

$\int \exp \left[-\theta ^{T}A\eta \right]\,d\theta \,d\eta =\det A$

This holds for any $n\times n$-dimensional matrix $A.$ The symbols $\theta ,\eta$ are two $n$-dimensional vectors of anti-commuting [Grassmann numbers](https://en.wikipedia.org/wiki/Grassmann_number) (aka "[supernumbers](https://en.wikipedia.org/wiki/Supernumber)"), taken from the [Grassmann algebra](https://en.wikipedia.org/wiki/Grassmann_algebra). The $\exp$ here is the [exponential function](https://en.wikipedia.org/wiki/Exponential_function). The integral sign is meant to be understood as the Berezin integral. Despite the use of the integral symbol, this expression is in fact an entirely finite sum.

This unusual-looking expression can be understood as a notational trick that rewrites the conventional expression for the determinant

$\det A=\sum _{\sigma \in S_{n}}\operatorname {sgn} (\sigma )a_{1,\sigma (1)}\cdots a_{n,\sigma (n)}.$

by using some novel notation. The anti-commuting property of the Grassmann numbers captures the sign (signature) of the permutation, while the integral combined with the $\exp$ ensures that all permutations are explored. That is, the [Taylor's series](https://en.wikipedia.org/wiki/Taylor%27s_series) for $\exp$ terminates after exactly $n$ terms, because the square of a Grassmann number is zero, and there are exactly $n$ distinct Grassmann variables. Meanwhile, the integral is defined to vanish, if the corresponding Grassmann number does *not* appear in the integrand. Thus, the integral selects out only those terms in the $\exp$ series that have exactly $n$ distinct variables; all lower-order terms vanish. Thus, the somewhat magical combination of the integral sign, the use of anti-commuting variables, and the Taylor's series for $\exp$ just encodes a finite sum, identical to the conventional summation.

This form is popular in physics, where it is often used as a stand-in for the Jacobian determinant. The appeal is that, notationally, the integral takes the form of a [path integral](https://en.wikipedia.org/wiki/Functional_integration), such as in the [path integral formulation](https://en.wikipedia.org/wiki/Path_integral_formulation) for quantized [Hamiltonian mechanics](https://en.wikipedia.org/wiki/Hamiltonian_mechanics). An example can be found in the theory of [Fadeev–Popov ghosts](https://en.wikipedia.org/wiki/Fadeev%E2%80%93Popov_ghosts); although this theory may seem rather abstruse, it's best to keep in mind that the use of the ghost fields is little more than a notational trick to express a Jacobian determinant.

The [Pfaffian](https://en.wikipedia.org/wiki/Pfaffian) $\mathrm {Pf} \,A$ of a [skew-symmetric matrix](https://en.wikipedia.org/wiki/Skew-symmetric_matrix) $A$ is the square-root of the determinant: that is, $\left(\mathrm {Pf} \,A\right)^{2}=\det A.$ The Berezin integral form for the Pfaffian is even more suggestive; it is

$\int \exp \left[-{\tfrac {1}{2}}\theta ^{T}A\theta \right]\,d\theta =\mathrm {Pf} \,A$

The integrand has exactly the same formal structure as a normal [[Gaussian Distribution]], albeit with Grassman numbers, instead of real numbers. This formal resemblance accounts for the occasional appearance of supernumbers in the theory of [stochastic dynamics](https://en.wikipedia.org/wiki/Stochastic_dynamics) and [stochastic differential equations](https://en.wikipedia.org/wiki/Stochastic_differential_equation).

## Generalizations and related notions

Determinants as treated above admit several variants: the [permanent](https://en.wikipedia.org/wiki/Permanent_(mathematics) "Permanent (mathematics)") of a matrix is defined as the determinant, except that the factors $\operatorname {sgn} (\sigma )$ occurring in Leibniz's rule are omitted. The [immanant](https://en.wikipedia.org/wiki/Immanant_of_a_matrix) generalizes both by introducing a [character](https://en.wikipedia.org/wiki/Character_theory) of the [symmetric group](https://en.wikipedia.org/wiki/Symmetric_group) $S_{n}$ in Leibniz's rule.

### Determinants for finite-dimensional algebras

For any [associative algebra](https://en.wikipedia.org/wiki/Associative_algebra) $A$ that is [finite-dimensional](https://en.wikipedia.org/wiki/Dimension) as a vector space over a field $F$, there is a determinant map 

$\det :A\to F.$

This definition proceeds by establishing the characteristic polynomial independently of the determinant, and defining the determinant as the lowest order term of this polynomial. This general definition recovers the determinant for the [matrix algebra](https://en.wikipedia.org/wiki/Matrix_algebra) $A=\operatorname {Mat} _{n\times n}(F)$, but also includes several further cases including the determinant of a [quaternion](https://en.wikipedia.org/wiki/Quaternion),

$\det(a+ib+jc+kd)=a^{2}+b^{2}+c^{2}+d^{2}$,

the [norm](https://en.wikipedia.org/wiki/Field_norm) $N_{L/F}:L\to F$ of a [field extension](https://en.wikipedia.org/wiki/Field_extension), as well as the [Pfaffian](https://en.wikipedia.org/wiki/Pfaffian) of a skew-symmetric matrix and the [reduced norm](https://en.wikipedia.org/wiki/Reduced_norm) of a [central simple algebra](https://en.wikipedia.org/wiki/Central_simple_algebra).

### Infinite matrices

For matrices with an infinite number of rows and columns, the above definitions of the determinant do not carry over directly. For example, in the Leibniz formula, an infinite sum (all of whose terms are infinite products) would have to be calculated. [Functional analysis](https://en.wikipedia.org/wiki/Functional_analysis) provides different extensions of the determinant for such infinite-dimensional situations, which however only work for particular kinds of operators.

The [Fredholm determinant](https://en.wikipedia.org/wiki/Fredholm_determinant) defines the determinant for operators known as [trace class operators](https://en.wikipedia.org/wiki/Trace_class_operator) by an appropriate generalization of the formula

$\det(I+A)=\exp(\operatorname {tr} (\log(I+A))).$

Another infinite-dimensional notion of determinant is the [functional determinant](https://en.wikipedia.org/wiki/Functional_determinant).

### Operators in von Neumann algebras

For operators in a finite [factor](https://en.wikipedia.org/wiki/Von_Neumann_algebra#Factors), one may define a positive real-valued determinant called the [Fuglede−Kadison determinant](https://en.wikipedia.org/wiki/Fuglede%E2%88%92Kadison_determinant) using the canonical trace. In fact, corresponding to every [tracial state](https://en.wikipedia.org/wiki/State_(functional_analysis)#tracial_state "State (functional analysis)") on a [von Neumann algebra](https://en.wikipedia.org/wiki/Von_Neumann_algebra) there is a notion of Fuglede−Kadison determinant.

### Related notions for non-commutative rings

For matrices over non-commutative rings, multilinearity and alternating properties are incompatible for *n* ≥ 2, so there is no good definition of the determinant in this setting.

For square matrices with entries in a non-commutative ring, there are various difficulties in defining determinants analogously to that for commutative rings. A meaning can be given to the Leibniz formula provided that the order for the product is specified, and similarly for other definitions of the determinant, but non-commutativity then leads to the loss of many fundamental properties of the determinant, such as the multiplicative property or that the determinant is unchanged under transposition of the matrix. Over non-commutative rings, there is no reasonable notion of a multilinear form (existence of a nonzero bilinear form<sup>\[*[clarify](https://en.wikipedia.org/wiki/Wikipedia:Please_clarify)*\]</sup> with a [regular element](https://en.wikipedia.org/wiki/Regular_element_(ring_theory)) of *R* as value on some pair of arguments implies that *R* is commutative). Nevertheless, various notions of non-commutative determinant have been formulated that preserve some of the properties of determinants, notably [quasideterminants](https://en.wikipedia.org/wiki/Quasideterminant) and the [Dieudonné determinant](https://en.wikipedia.org/wiki/Dieudonn%C3%A9_determinant). For some classes of matrices with non-commutative elements, one can define the determinant and prove linear algebra theorems that are very similar to their commutative analogs. Examples include the *q*-determinant on quantum groups, the [Capelli determinant](https://en.wikipedia.org/wiki/Capelli_determinant) on Capelli matrices, and the [Berezinian](https://en.wikipedia.org/wiki/Berezinian) on [supermatrices](https://en.wikipedia.org/wiki/Supermatrices) (i.e., matrices whose entries are elements of $\mathbb {Z} _{2}$-[graded rings](https://en.wikipedia.org/wiki/Graded_ring)). [Manin matrices](https://en.wikipedia.org/wiki/Manin_matrices) form the class closest to matrices with commutative elements.

## Calculation

Determinants are mainly used as a theoretical tool. They are rarely calculated explicitly in [numerical linear algebra](https://en.wikipedia.org/wiki/Numerical_linear_algebra), where for applications such as checking invertibility and finding eigenvalues the determinant has largely been supplanted by other techniques. [Computational geometry](https://en.wikipedia.org/wiki/Computational_geometry), however, does frequently use calculations related to determinants.

While the determinant can be computed directly using the Leibniz rule this approach is extremely inefficient for large matrices, since that formula requires calculating $n!$ ($n$ [factorial](https://en.wikipedia.org/wiki/Factorial)) products for an $n\times n$ matrix. Thus, the number of required operations grows very quickly: it is [of order](https://en.wikipedia.org/wiki/Big_O_notation) $n!$. The Laplace expansion is similarly inefficient. Therefore, more involved techniques have been developed for calculating determinants.

### Gaussian elimination

[Gaussian elimination](https://en.wikipedia.org/wiki/Gaussian_elimination) consists of left multiplying a matrix by [elementary matrices](https://en.wikipedia.org/wiki/Elementary_matrices) for getting a matrix in a [row echelon form](https://en.wikipedia.org/wiki/Row_echelon_form). One can restrict the computation to elementary matrices of determinant 1. In this case, the determinant of the resulting row echelon form equals the determinant of the initial matrix. As a row echelon form is a [triangular matrix](https://en.wikipedia.org/wiki/Triangular_matrix), its determinant is the product of the entries of its diagonal.

So, the determinant can be computed for almost free from the result of a Gaussian elimination.

### Decomposition methods

Some methods compute $\det(A)$ by writing the matrix as a product of matrices whose determinants can be more easily computed. Such techniques are referred to as decomposition methods. Examples include the [[LU Decomposition]], the [[QR Decomposition]] or the [[Cholesky Decomposition]] (for [[Positive-Definite Matrix|positive definite matrices]]). These methods are of order $\operatorname {O} (n^{3})$, which is a significant improvement over $\operatorname {O} (n!)$.

For example, LU decomposition expresses $A$ as a product

$A=PLU.$

of a [permutation matrix](https://en.wikipedia.org/wiki/Permutation_matrix) $P$ (which has exactly a single $1$ in each column, and otherwise zeros), a lower triangular matrix $L$ and an upper triangular matrix $U$. The determinants of the two triangular matrices $L$ and $U$ can be quickly calculated, since they are the products of the respective diagonal entries. The determinant of $P$ is just the sign $\varepsilon$ of the corresponding permutation (which is $+1$ for an even number of permutations and is $-1$ for an odd number of permutations). Once such a LU decomposition is known for $A$, its determinant is readily computed as

$\det(A)=\varepsilon \det(L)\cdot \det(U).$

### Further methods

The order $\operatorname {O} (n^{3})$ reached by decomposition methods has been improved by different methods. If two matrices of order $n$ can be multiplied in time $M(n)$, where $M(n)\geq n^{a}$ for some $a>2$, then there is an algorithm computing the determinant in time $O(M(n))$. This means, for example, that an $\operatorname {O} (n^{2.376})$ algorithm for computing the determinant exists based on the [Coppersmith–Winograd algorithm](https://en.wikipedia.org/wiki/Coppersmith%E2%80%93Winograd_algorithm). This exponent has been further lowered, as of 2016, to 2.373.

If the determinant of *A* and the inverse of *A* have already been computed, the [matrix determinant lemma](https://en.wikipedia.org/wiki/Matrix_determinant_lemma) allows rapid calculation of the determinant of *A* + *uv*<sup>T</sup>, where *u* and *v* are column vectors.

Charles Dodgson (i.e. [Lewis Carroll](https://en.wikipedia.org/wiki/Lewis_Carroll) of *[Alice's Adventures in Wonderland](https://en.wikipedia.org/wiki/Alice%27s_Adventures_in_Wonderland)* fame) invented a method for computing determinants called [Dodgson condensation](https://en.wikipedia.org/wiki/Dodgson_condensation). This method does not always work in its original form.

## See also

- ![[media/1a9c6ad1ccebbc090fc7cd1c94d2142489246997.png]][Mathematics portal](https://en.wikipedia.org/wiki/Portal:Mathematics)

- [Cauchy determinant](https://en.wikipedia.org/wiki/Cauchy_determinant)
- [Cayley–Menger determinant](https://en.wikipedia.org/wiki/Cayley%E2%80%93Menger_determinant)
- [Dieudonné determinant](https://en.wikipedia.org/wiki/Dieudonn%C3%A9_determinant)
- [Slater determinant](https://en.wikipedia.org/wiki/Slater_determinant)
- [Determinantal conjecture](https://en.wikipedia.org/wiki/Determinantal_conjecture)

## Notes

1.  , §VII.1
2.  ["Determinants and Volumes"](https://textbooks.math.gatech.edu/ila/determinants-volumes.html). *textbooks.math.gatech.edu*. Retrieved 16 March 2018.
3.  McConnell (1957). [Applications of Tensor Analysis](https://archive.org/details/applicationoften0000mcco). Dover Publications. pp. [10–17](https://archive.org/details/applicationoften0000mcco/page/10).
4.  , §4.7
5.  [Serge Lang](https://en.wikipedia.org/wiki/Serge_Lang), *Linear Algebra*, 2nd Edition, Addison-Wesley, 1971, pp 173, 191.
6.  , §VI.7, Theorem 7.5
7.  Alternatively, , §III.8, Proposition 1 proves this result using the [functoriality](https://en.wikipedia.org/wiki/Functoriality) of the exterior power.
8.  , §0.8.7
9.  , p. 306
10. , §0.8.2.
11. Silvester, J. R. (2000). ["Determinants of Block Matrices"](https://hal.archives-ouvertes.fr/hal-01509379/document). *Math. Gaz*. **84** (501): 460–467. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/3620776](https://doi.org/10.2307%2F3620776). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [3620776](https://www.jstor.org/stable/3620776). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [41879675](https://api.semanticscholar.org/CorpusID:41879675).
12. Sothanaphan, Nat (January 2017). "Determinants of block matrices with noncommuting blocks". *Linear Algebra and Its Applications*. **512**: 202–218. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1805.06027](https://arxiv.org/abs/1805.06027). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.laa.2016.10.004](https://doi.org/10.1016%2Fj.laa.2016.10.004). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [119272194](https://api.semanticscholar.org/CorpusID:119272194).
13. .
14. Proofs can be found in [http://www.ee.ic.ac.uk/hp/staff/dmb/matrix/proof003.html](http://www.ee.ic.ac.uk/hp/staff/dmb/matrix/proof003.html)
15. Lin, Minghua; Sra, Suvrit (2014). "Completely strong superadditivity of generalized matrix functions". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1410.1958](https://arxiv.org/abs/1410.1958) \[[math.FA](https://arxiv.org/archive/math.FA)\].
16. Paksoy; Turkmen; Zhang (2014). ["Inequalities of Generalized Matrix Functions via Tensor Products"](https://nsuworks.nova.edu/cgi/viewcontent.cgi?article=1062&context=math_facarticles). *Electronic Journal of Linear Algebra*. **27**: 332–341. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.13001/1081-3810.1622](https://doi.org/10.13001%2F1081-3810.1622).
17. Serre, Denis (Oct 18, 2010). ["Concavity of det1/n over HPDn"](https://mathoverflow.net/questions/42594/concavity-of-det1-n-over-hpd-n). *MathOverflow*.
18. , §VIII.2, , Def. 1.2.3
19. , Observation 7.1.2, Theorem 7.2.5
20. A proof can be found in the Appendix B of Kondratyuk, L. A.; Krivoruchenko, M. I. (1992). "Superconducting quark matter in SU(2) color group". *Zeitschrift für Physik A*. **344** (1): 99–115. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1992ZPhyA.344...99K](https://ui.adsabs.harvard.edu/abs/1992ZPhyA.344...99K). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/BF01291027](https://doi.org/10.1007%2FBF01291027). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [120467300](https://api.semanticscholar.org/CorpusID:120467300).
21. , § 0.8.10
22. , §6.6
23. Cajori, F. [A History of Mathematics p. 80](https://archive.org/details/ahistorymathema02cajogoog/page/n94)
24. ^    Campbell, H: "Linear Algebra With Applications", pages 111–112. Appleton Century Crofts, 1971
25. , p. 405
26. A Brief History of Linear Algebra and Matrix Theory at: ["A Brief History of Linear Algebra and Matrix Theory"](https://web.archive.org/web/20120910034016/http://darkwing.uoregon.edu/~vitulli/441.sp04/LinAlgHistory.html). Archived from [the original](http://darkwing.uoregon.edu/~vitulli/441.sp04/LinAlgHistory.html) on 10 September 2012. Retrieved 24 January 2012.
27. , p. 80
28. , p. 59)
29. Muir, Sir Thomas, *The Theory of Determinants in the historical Order of Development* \[London, England: Macmillan and Co., Ltd., 1906\]. [JFM](https://en.wikipedia.org/wiki/JFM_(identifier)) [37.0181.02](https://zbmath.org/?format=complete&q=an:37.0181.02)
30. , §5.2
31. The first use of the word "determinant" in the modern sense appeared in: Cauchy, Augustin-Louis "Memoire sur les fonctions qui ne peuvent obtenir que deux valeurs égales et des signes contraires par suite des transpositions operées entre les variables qu'elles renferment," which was first read at the Institute de France in Paris on November 30, 1812, and which was subsequently published in the *Journal de l'Ecole Polytechnique*, Cahier 17, Tome 10, pages 29–112 (1815).
32. Origins of mathematical terms: [http://jeff560.tripod.com/d.html](http://jeff560.tripod.com/d.html)
33. History of matrices and determinants: [http://www-history.mcs.st-and.ac.uk/history/HistTopics/Matrices_and_determinants.html](http://www-history.mcs.st-and.ac.uk/history/HistTopics/Matrices_and_determinants.html)
34. , p. 494
35. , Vol. II, p. 92, no. 462
36. History of matrix notation: [http://jeff560.tripod.com/matrices.html](http://jeff560.tripod.com/matrices.html)
37. 38. , §VII.3
39. , §IV.8
40. , §VII.6, Theorem 6.10
41. Lay, David (2021). *Linear Algebra and Its Applications 6th Edition*. Pearson. p. 172.
42. Dr. Jeff Cruza. ["Triangle area"](https://xaktly.com/TriangleDeterminant.html).
43. , §11.4
44. , §11.4, Theorem 30
45. , §I.4. See also *[Natural transformation § Determinant](https://en.wikipedia.org/wiki/Natural_transformation#Determinant)*.
46. , §III.8
47. , §5.2, , §III.5
48. 49. In a non-commutative setting left-linearity (compatibility with left-multiplication by scalars) should be distinguished from right-linearity. Assuming linearity in the columns is taken to be left-linearity, one would have, for non-commuting scalars *a*, *b*: 

$$
{\begin{aligned}ab&=ab{\begin{vmatrix}1&0\\0&1\end{vmatrix}}=a{\begin{vmatrix}1&0\\0&b\end{vmatrix}}\\[5mu]&={\begin{vmatrix}a&0\\0&b\end{vmatrix}}=b{\begin{vmatrix}a&0\\0&1\end{vmatrix}}=ba{\begin{vmatrix}1&0\\0&1\end{vmatrix}}=ba,\end{aligned}}
$$

 a contradiction. There is no useful notion of multi-linear functions over a non-commutative ring.
50. Varadarajan, V. S (2004), [Supersymmetry for mathematicians: An introduction](https://books.google.com/books?id=sZ1-G4hQgIIC&q=Berezinian&pg=PA116), American Mathematical Soc., [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8218-3574-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8218-3574-6).
51. "... we mention that the determinant, though a convenient notion theoretically, rarely finds a useful role in numerical algorithms.", see , Lecture 1.
52. , §1.1, §4.3
53. Camarero, Cristóbal (2018-12-05). "Simple, Fast and Practicable Algorithms for Cholesky, LU and QR Decomposition Using Fast Rectangular Matrix Multiplication". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1812.02056](https://arxiv.org/abs/1812.02056) \[[cs.NA](https://arxiv.org/archive/cs.NA)\].
54. 55. , §1.1
56. 57. Fang, Xin Gui; Havas, George (1997). ["On the worst-case complexity of integer Gaussian elimination"](https://web.archive.org/web/20110807042828/http://perso.ens-lyon.fr/gilles.villard/BIBLIOGRAPHIE/PDF/ft_gateway.cfm.pdf) (PDF). *Proceedings of the 1997 international symposium on Symbolic and algebraic computation*. ISSAC '97. Kihei, Maui, Hawaii, United States: ACM. pp. 28–31. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1145/258726.258740](https://doi.org/10.1145%2F258726.258740). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-89791-875-4](https://en.wikipedia.org/wiki/Special:BookSources/0-89791-875-4). Archived from [the original](http://perso.ens-lyon.fr/gilles.villard/BIBLIOGRAPHIE/PDF/ft_gateway.cfm.pdf) (PDF) on 2011-08-07. Retrieved 2011-01-22.
58. , §1.1, 
59. Abeles, Francine F. (2008). ["Dodgson condensation: The historical and mathematical development of an experimental method"](https://www.academia.edu/10352246). *Linear Algebra and Its Applications*. **429** (2–3): 429–438. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.laa.2007.11.022](https://doi.org/10.1016%2Fj.laa.2007.11.022).

## References

- Anton, Howard (2005), *Elementary Linear Algebra (Applications Version)* (9th ed.), Wiley International
- [Axler, Sheldon Jay](https://en.wikipedia.org/wiki/Sheldon_Axler) (2015). *Linear Algebra Done Right* (3rd ed.). [Springer](https://en.wikipedia.org/wiki/Springer_Science%2BBusiness_Media). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-319-11079-0](https://en.wikipedia.org/wiki/Special:BookSources/978-3-319-11079-0).
- Bareiss, Erwin (1968), ["Sylvester's Identity and Multistep Integer-Preserving Gaussian Elimination"](https://www.ams.org/journals/mcom/1968-22-103/S0025-5718-1968-0226829-0/S0025-5718-1968-0226829-0.pdf) (PDF), *Mathematics of Computation*, **22** (102): 565–578, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2004533](https://doi.org/10.2307%2F2004533), [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2004533](https://www.jstor.org/stable/2004533), [archived](https://web.archive.org/web/20121025053848/http://www.ams.org/journals/mcom/1968-22-103/S0025-5718-1968-0226829-0/S0025-5718-1968-0226829-0.pdf) (PDF) from the original on 2012-10-25
- [de Boor, Carl](https://en.wikipedia.org/wiki/Carl_R._de_Boor) (1990), ["An empty exercise"](http://ftp.cs.wisc.edu/Approx/empty.pdf) (PDF), *ACM SIGNUM Newsletter*, **25** (2): 3–7, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1145/122272.122273](https://doi.org/10.1145%2F122272.122273), [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [62780452](https://api.semanticscholar.org/CorpusID:62780452), [archived](https://web.archive.org/web/20060901214854/http://ftp.cs.wisc.edu/Approx/empty.pdf) (PDF) from the original on 2006-09-01
- [Bourbaki, Nicolas](https://en.wikipedia.org/wiki/Nicolas_Bourbaki) (1998), *Algebra I, Chapters 1-3*, Springer, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9783540642435](https://en.wikipedia.org/wiki/Special:BookSources/9783540642435)
- Bunch, James R.; [Hopcroft, John E.](https://en.wikipedia.org/wiki/John_Hopcroft) (1974). ["Triangular Factorization and Inversion by Fast Matrix Multiplication"](https://doi.org/10.1090%2FS0025-5718-1974-0331751-8). *[Mathematics of Computation](https://en.wikipedia.org/wiki/Mathematics_of_Computation)*. **28** (125): 231–236. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1090/S0025-5718-1974-0331751-8](https://doi.org/10.1090%2FS0025-5718-1974-0331751-8). [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[1813/6003](https://hdl.handle.net/1813%2F6003).
- Dummit, David S.; Foote, Richard M. (2004), *Abstract algebra* (3rd ed.), Hoboken, NJ: Wiley, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780471452348](https://en.wikipedia.org/wiki/Special:BookSources/9780471452348), [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [248917264](https://search.worldcat.org/oclc/248917264)
- Fisikopoulos, Vissarion; Peñaranda, Luis (2016), "Faster geometric algorithms via dynamic determinant computation", *[Computational Geometry](https://en.wikipedia.org/wiki/Computational_Geometry_(journal) "Computational Geometry (journal)")*, **54**: 1–16, [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1206.7067](https://arxiv.org/abs/1206.7067), [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.comgeo.2015.12.001](https://doi.org/10.1016%2Fj.comgeo.2015.12.001)
- [Garibaldi, Skip](https://en.wikipedia.org/wiki/Skip_Garibaldi) (2004), "The characteristic polynomial and determinant are not ad hoc constructions", *American Mathematical Monthly*, **111** (9): 761–778, [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[math/0203276](https://arxiv.org/abs/math/0203276), [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/4145188](https://doi.org/10.2307%2F4145188), [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [4145188](https://www.jstor.org/stable/4145188), [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [2104048](https://mathscinet.ams.org/mathscinet-getitem?mr=2104048)
- Habgood, Ken; Arel, Itamar (2012). ["A condensation-based application of Cramer's rule for solving large-scale linear systems"](https://hal.archives-ouvertes.fr/hal-01500199/file/HA.pdf) (PDF). *Journal of Discrete Algorithms*. **10**: 98–109. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.jda.2011.06.007](https://doi.org/10.1016%2Fj.jda.2011.06.007). [Archived](https://web.archive.org/web/20190505060158/https://hal.archives-ouvertes.fr/hal-01500199/file/HA.pdf) (PDF) from the original on 2019-05-05.
- Harris, Frank E. (2014), *Mathematics for Physical Science and Engineering*, Elsevier, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780128010495](https://en.wikipedia.org/wiki/Special:BookSources/9780128010495)
- [Kleiner, Israel](https://en.wikipedia.org/wiki/Israel_Kleiner_(mathematician) "Israel Kleiner (mathematician)") (2007), Kleiner, Israel (ed.), *A History of Abstract Algebra*, Birkhäuser, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-0-8176-4685-1](https://doi.org/10.1007%2F978-0-8176-4685-1), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8176-4684-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8176-4684-4), [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [2347309](https://mathscinet.ams.org/mathscinet-getitem?mr=2347309)
- Kung, Joseph P.S.; Rota, Gian-Carlo; [Yan, Catherine](https://en.wikipedia.org/wiki/Catherine_H._Yan) (2009), *[Combinatorics: The Rota Way](https://en.wikipedia.org/wiki/Combinatorics:_The_Rota_Way)*, Cambridge University Press, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780521883894](https://en.wikipedia.org/wiki/Special:BookSources/9780521883894)
- Lay, David C. (August 22, 2005), *Linear Algebra and Its Applications* (3rd ed.), Addison Wesley, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-321-28713-7](https://en.wikipedia.org/wiki/Special:BookSources/978-0-321-28713-7)
- Lombardi, Henri; Quitté, Claude (2015), *Commutative Algebra: Constructive Methods*, Springer, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9789401799447](https://en.wikipedia.org/wiki/Special:BookSources/9789401799447)
- [Mac Lane, Saunders](https://en.wikipedia.org/wiki/Saunders_Mac_Lane) (1998), [*Categories for the Working Mathematician*](https://en.wikipedia.org/wiki/Categories_for_the_Working_Mathematician), Graduate Texts in Mathematics **5** (2nd ed.), Springer-Verlag, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-98403-8](https://en.wikipedia.org/wiki/Special:BookSources/0-387-98403-8)
- Meyer, Carl D. (February 15, 2001), [Matrix Analysis and Applied Linear Algebra](https://web.archive.org/web/20091031193126/http://matrixanalysis.com/DownloadChapters.html), Society for Industrial and Applied Mathematics (SIAM), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-89871-454-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-89871-454-8), archived from [the original](http://www.matrixanalysis.com/DownloadChapters.html) on 2009-10-31
- [Muir, Thomas](https://en.wikipedia.org/wiki/Thomas_Muir_(mathematician) "Thomas Muir (mathematician)") (1960) \[1933\], *A treatise on the theory of determinants*, Revised and enlarged by William H. Metzler, New York, NY: Dover
- Poole, David (2006), *Linear Algebra: A Modern Introduction* (2nd ed.), Brooks/Cole, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-534-99845-3](https://en.wikipedia.org/wiki/Special:BookSources/0-534-99845-3)
- [G. Baley Price](https://en.wikipedia.org/wiki/G._Baley_Price) (1947) "Some identities in the theory of determinants", [American Mathematical Monthly](https://en.wikipedia.org/wiki/American_Mathematical_Monthly) 54:75–90 [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0019078](https://mathscinet.ams.org/mathscinet-getitem?mr=0019078)
- [Horn, Roger Alan](https://en.wikipedia.org/wiki/Roger_Horn); [Johnson, Charles Royal](https://en.wikipedia.org/wiki/Charles_Royal_Johnson) (2018) \[1985\]. *Matrix Analysis* (2nd ed.). [Cambridge University Press](https://en.wikipedia.org/wiki/Cambridge_University_Press). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-54823-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-54823-6).
- [Lang, Serge](https://en.wikipedia.org/wiki/Serge_Lang) (1985), *Introduction to Linear Algebra*, Undergraduate Texts in Mathematics (2 ed.), Springer, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780387962054](https://en.wikipedia.org/wiki/Special:BookSources/9780387962054)
- Lang, Serge (1987), *Linear Algebra*, Undergraduate Texts in Mathematics (3 ed.), Springer, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780387964126](https://en.wikipedia.org/wiki/Special:BookSources/9780387964126)
- Lang, Serge (2002). *Algebra*. Graduate Texts in Mathematics. New York, NY: Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-95385-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-95385-4).
- Leon, Steven J. (2006), *Linear Algebra With Applications* (7th ed.), Pearson Prentice Hall
- Rote, Günter (2001), ["Division-free algorithms for the determinant and the Pfaffian: algebraic and combinatorial approaches"](https://web.archive.org/web/20070201145100/http://page.inf.fu-berlin.de/~rote/Papers/pdf/Division-free+algorithms.pdf) (PDF), *Computational discrete mathematics*, Lecture Notes in Comput. Sci., vol. 2122, Springer, pp. 119–135, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/3-540-45506-X_9](https://doi.org/10.1007%2F3-540-45506-X_9), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-42775-9](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-42775-9), [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1911585](https://mathscinet.ams.org/mathscinet-getitem?mr=1911585), archived from [the original](https://page.inf.fu-berlin.de/~rote/Papers/pdf/Division-free+algorithms.pdf) (PDF) on 2007-02-01, retrieved 2020-06-04
- [Trefethen, Lloyd](https://en.wikipedia.org/wiki/Nick_Trefethen); Bau III, David (1997), *Numerical Linear Algebra* (1st ed.), Philadelphia: SIAM, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-89871-361-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-89871-361-9)

### Historical references

- [Bourbaki, Nicolas](https://en.wikipedia.org/wiki/Nicolas_Bourbaki) (1994), *Elements of the history of mathematics*, translated by [Meldrum, John](https://en.wikipedia.org/wiki/John_D._P._Meldrum), Springer, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-3-642-61693-8](https://doi.org/10.1007%2F978-3-642-61693-8), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [3-540-19376-6](https://en.wikipedia.org/wiki/Special:BookSources/3-540-19376-6)
- [Cajori, Florian](https://en.wikipedia.org/wiki/Florian_Cajori) (1993), *A history of mathematical notations: Including Vol. I. Notations in elementary mathematics; Vol. II. Notations mainly in higher mathematics, Reprint of the 1928 and 1929 originals*, Dover, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-486-67766-4](https://en.wikipedia.org/wiki/Special:BookSources/0-486-67766-4), [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [3363427](https://mathscinet.ams.org/mathscinet-getitem?mr=3363427)
- [Bézout, Étienne](https://en.wikipedia.org/wiki/%C3%89tienne_B%C3%A9zout) (1779), [Théorie générale des equations algébriques](https://gallica.bnf.fr/ark:/12148/bpt6k106053p.image), Paris
- [Cayley, Arthur](https://en.wikipedia.org/wiki/Arthur_Cayley) (1841), "On a theorem in the geometry of position", *Cambridge Mathematical Journal*, **2**: 267–271
- [Cramer, Gabriel](https://en.wikipedia.org/wiki/Gabriel_Cramer) (1750), *Introduction à l'analyse des lignes courbes algébriques*, Genève: Frères Cramer & Cl. Philibert, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3931/e-rara-4048](https://doi.org/10.3931%2Fe-rara-4048)
- [Eves, Howard](https://en.wikipedia.org/wiki/Howard_Eves) (1990), *An introduction to the history of mathematics* (6 ed.), Saunders College Publishing, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-03-029558-0](https://en.wikipedia.org/wiki/Special:BookSources/0-03-029558-0), [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1104435](https://mathscinet.ams.org/mathscinet-getitem?mr=1104435)
- Grattan-Guinness, I., ed. (2003), *Companion Encyclopedia of the History and Philosophy of the Mathematical Sciences*, vol. 1, [Johns Hopkins University Press](https://en.wikipedia.org/wiki/Johns_Hopkins_University_Press), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780801873966](https://en.wikipedia.org/wiki/Special:BookSources/9780801873966)
- [Jacobi, Carl Gustav Jakob](https://en.wikipedia.org/wiki/Carl_Gustav_Jakob_Jacobi) (1841), ["De Determinantibus functionalibus"](https://www.digizeitschriften.de/dms/img/?PID=GDZPPN002142724&physid=phys325#navi), *Journal für die reine und angewandte Mathematik*, **1841** (22): 320–359, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1515/crll.1841.22.319](https://doi.org/10.1515%2Fcrll.1841.22.319), [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [123637858](https://api.semanticscholar.org/CorpusID:123637858)
- [Laplace, Pierre-Simon, de](https://en.wikipedia.org/wiki/Pierre-Simon_Laplace) (1772), ["Recherches sur le calcul intégral et sur le systéme du monde"](https://gallica.bnf.fr/ark:/12148/bpt6k77596b/f374), *Histoire de l'Académie Royale des Sciences* (seconde partie), Paris: 267–376`{{`[`citation`](https://en.wikipedia.org/wiki/Template:Citation)`}}`: CS1 maint: multiple names: authors list ([link](https://en.wikipedia.org/wiki/Category:CS1_maint:_multiple_names:_authors_list))
- [Robert Forsyth Scott (1880): A Treatise on the Theory of Determinants and Their Applications in Analysis and Geometry, Cambridge University Press](http://www.totoha.net/archiv/scott1880.pdf)
- [E. R. Hedrick: On Three Dimensional Determinants, Annals of Mathematics, Vol.1, No.1/4 (1899-1900), pp.49-67 (19pages). https://doi.org/10.2307/1967268](https://www.jstor.org/stable/1967268) \# Note: This is not the ordinal determinant.

## External links

- Suprunenko, D.A. (2001) \[1994\], ["Determinant"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society)
- [Weisstein, Eric W.](https://en.wikipedia.org/wiki/Eric_W._Weisstein) ["Determinant"](https://mathworld.wolfram.com/Determinant.html). *[MathWorld](https://en.wikipedia.org/wiki/MathWorld)*.
- O'Connor, John J.; [Robertson, Edmund F.](https://en.wikipedia.org/wiki/Edmund_F._Robertson), ["Matrices and determinants"](https://mathshistory.st-andrews.ac.uk/HistTopics/Matrices_and_determinants.html), *[MacTutor History of Mathematics Archive](https://en.wikipedia.org/wiki/MacTutor_History_of_Mathematics_Archive)*, [University of St Andrews](https://en.wikipedia.org/wiki/University_of_St_Andrews)
- [Determinant Interactive Program and Tutorial](http://people.revoledu.com/kardi/tutorial/LinearAlgebra/MatrixDeterminant.html)
- [Linear algebra: determinants.](http://www.umat.feec.vutbr.cz/~novakm/determinanty/en/) [Archived](https://web.archive.org/web/20081204081902/http://www.umat.feec.vutbr.cz/~novakm/determinanty/en/) 2008-12-04 at the [Wayback Machine](https://en.wikipedia.org/wiki/Wayback_Machine) Compute determinants of matrices up to order 6 using Laplace expansion you choose.
- [Determinant Calculator](https://physandmathsolutions.com/Menus/matrix_determinant_calculator.php) Calculator for matrix determinants, up to the 8th order.
- [Matrices and Linear Algebra on the Earliest Uses Pages](http://www.economics.soton.ac.uk/staff/aldrich/matrices.htm)
- [Determinants explained in an easy fashion in the 4th chapter as a part of a Linear Algebra course.](http://algebra.math.ust.hk/course/content.shtml) [Archived](https://web.archive.org/web/20191101200355/http://algebra.math.ust.hk/course/content.shtml) 2019-11-01 at the [Wayback Machine](https://en.wikipedia.org/wiki/Wayback_Machine)
