[[linear-algebra.base]]

> Source: [[Singular Value Decomposition]]
> License: Wikipedia content is available under CC BY-SA 4.0.

![[media/c89e14cc73603d65d99ef06df00e94444753cbe1.png]]
Illustration of the singular value decomposition <strong>UΣV</strong><sup>⁎</sup> of a real 2 × 2 matrix <strong>M</strong>.

<ul>
<li><strong>Top:</strong> The action of <strong>M</strong>, indicated by its effect on the unit disc D and the two canonical unit vectors <em>e</em><sub>1</sub> and <em>e</em><sub>2</sub>.</li>
<li><strong>Left:</strong> The action of <strong>V</strong><sup>⁎</sup>, a rotation, on <em>D</em>, <em>e</em><sub>1</sub>, and <em>e</em><sub>2</sub>.</li>
<li><strong>Bottom:</strong> The action of <strong>Σ</strong>, a scaling by the singular values <em>σ</em><sub>1</sub> horizontally and <em>σ</em><sub>2</sub> vertically.</li>
<li><strong>Right:</strong> The action of <strong>U</strong>, another rotation.</li>
</ul>

In [linear algebra](https://en.wikipedia.org/wiki/Linear_algebra), the **singular value decomposition** (**SVD**) is a [factorization](https://en.wikipedia.org/wiki/Matrix_decomposition) of a [real](https://en.wikipedia.org/wiki/Real_number) or [complex](https://en.wikipedia.org/wiki/Complex_number) [matrix](https://en.wikipedia.org/wiki/Matrix_(mathematics) "Matrix (mathematics)") into a rotation, followed by a rescaling followed by another rotation. It generalizes the [[Eigendecomposition]] of a square [normal matrix](https://en.wikipedia.org/wiki/Normal_matrix) with an orthonormal eigenbasis to any $m\times n$ matrix. It is related to the [polar decomposition](https://en.wikipedia.org/wiki/Polar_decomposition#Matrix_polar_decomposition).

Specifically, the singular value decomposition of an $m\times n$ complex matrix $\mathbf {M}$ is a factorization of the form $\mathbf {M} =\mathbf {U\Sigma V^{*}} ,$ where $\mathbf {U}$ is an $m\times m$ complex [unitary matrix](https://en.wikipedia.org/wiki/Unitary_matrix), $\mathbf {\Sigma }$ is an $m\times n$ [rectangular diagonal matrix](https://en.wikipedia.org/wiki/Rectangular_diagonal_matrix) with non-negative real numbers on the diagonal, $\mathbf {V}$ is an $n\times n$ complex unitary matrix, and $\mathbf {V} ^{*}$ is the [conjugate transpose](https://en.wikipedia.org/wiki/Conjugate_transpose) of $\mathbf {V}$. Such decomposition always exists for any complex matrix. If $\mathbf {M}$ is real, then $\mathbf {U}$ and $\mathbf {V}$ can be guaranteed to be real [orthogonal](https://en.wikipedia.org/wiki/Orthogonal_matrix) matrices; in such contexts, the SVD is often denoted $\mathbf {U} \mathbf {\Sigma } \mathbf {V} ^{\mathrm {T} }.$

The diagonal entries $\sigma _{i}=\Sigma _{ii}$ of $\mathbf {\Sigma }$ are uniquely determined by $\mathbf {M}$ and are known as the [singular values](https://en.wikipedia.org/wiki/Singular_value) of $\mathbf {M}$. The number of non-zero singular values is equal to the [rank](https://en.wikipedia.org/wiki/Rank_of_a_matrix) of $\mathbf {M}$. The columns of $\mathbf {U}$ and the columns of $\mathbf {V}$ are called left-singular vectors and right-singular vectors of $\mathbf {M}$, respectively. They form two sets of [orthonormal bases](https://en.wikipedia.org/wiki/Orthonormal_basis) $\mathbf {u} _{1},\ldots ,\mathbf {u} _{m}$ and $\mathbf {v} _{1},\ldots ,\mathbf {v} _{n},$ and if they are sorted so that the singular values $\sigma _{i}$ with value zero are all in the highest-numbered columns (or rows), the singular value decomposition can be written as 

$$
\mathbf {M} =\sum _{i=1}^{r}\sigma _{i}\mathbf {u} _{i}\mathbf {v} _{i}^{*},
$$

 where $r\leq \min\{m,n\}$ is the rank of $\mathbf {M} .$

The SVD is not unique. However, it is always possible to choose the decomposition such that the singular values $\Sigma _{ii}$ are in descending order. In this case, $\mathbf {\Sigma }$ (but not $\mathbf {U}$ and $\mathbf {V}$) is uniquely determined by $\mathbf {M} .$

The term sometimes refers to the **compact SVD**, a similar decomposition $\mathbf {M} =\mathbf {U\Sigma V} ^{*}$ in which $\mathbf {\Sigma }$ is square diagonal of size $r\times r,$ where $r\leq \min\{m,n\}$ is the rank of $\mathbf {M} ,$ and has only the non-zero singular values. In this variant, $\mathbf {U}$ is an $m\times r$ [semi-unitary matrix](https://en.wikipedia.org/wiki/Semi-orthogonal_matrix) and $\mathbf {V}$ is an $n\times r$ [semi-unitary matrix](https://en.wikipedia.org/wiki/Semi-orthogonal_matrix), such that $\mathbf {U} ^{*}\mathbf {U} =\mathbf {V} ^{*}\mathbf {V} =\mathbf {I} _{r}.$

Mathematical applications of the SVD include computing the [[Moore-Penrose Pseudoinverse|pseudoinverse]], matrix approximation, and determining the rank, [range](https://en.wikipedia.org/wiki/Range_of_a_matrix), and [null space](https://en.wikipedia.org/wiki/Kernel_(matrix)) of a matrix. The SVD is also extremely useful in many areas of science, [engineering](https://en.wikipedia.org/wiki/Engineering), and [statistics](https://en.wikipedia.org/wiki/Statistics), such as [signal processing](https://en.wikipedia.org/wiki/Signal_processing), [least squares](https://en.wikipedia.org/wiki/Least_squares) fitting of data, and [process control](https://en.wikipedia.org/wiki/Process_control).

## Intuitive interpretations

![[media/2d751cac833f140ae8b3ba8696e49a53fe691bd3.gif]]
Animated illustration of the SVD of a 2D, real [shearing matrix](https://en.wikipedia.org/wiki/Shear_mapping) <strong>M</strong>. First, we see the [unit disc](https://en.wikipedia.org/wiki/Unit_disc) in blue together with the two [canonical unit vectors](https://en.wikipedia.org/wiki/Standard_basis). We then see the actions of <strong>M</strong>, which distorts the disk to an [ellipse](https://en.wikipedia.org/wiki/Ellipse). The SVD decomposes <strong>M</strong> into three simple transformations: an initial [rotation](https://en.wikipedia.org/wiki/Rotation_matrix) <strong>V</strong><sup>⁎</sup>, a [scaling](https://en.wikipedia.org/wiki/Scaling_matrix) $\mathbf {\Sigma }$ along the coordinate axes, and a final rotation <strong>U</strong>. The lengths <em>σ</em><sub>1</sub> and <em>σ</em><sub>2</sub> of the [semi-axes](https://en.wikipedia.org/wiki/Ellipse#Elements_of_an_ellipse) of the ellipse are the [singular values](https://en.wikipedia.org/wiki/Singular_value) of <strong>M</strong>, namely Σ<sub>1,1</sub> and Σ<sub>2,2</sub>.

![[media/5f920adccef2e524b6a4c1f57874635765159b1f.png]]
Visualization of the matrix multiplications in singular value decomposition

### Rotation, coordinate scaling, and reflection

In the special case when $\mathbf {M}$ is an $m\times m$ real [square matrix](https://en.wikipedia.org/wiki/Square_matrix), the matrices $\mathbf {U}$ and $\mathbf {V} ^{*}$ can be chosen to be real $m\times m$ matrices too. In that case, "unitary" is the same as "[orthogonal](https://en.wikipedia.org/wiki/Orthogonal_matrix)". Then, interpreting both unitary matrices as well as the diagonal matrix, summarized here as $\mathbf {A} ,$ as a [[Linear Transformation]] $\mathbf {x} \mapsto \mathbf {Ax}$ of the space $\mathbf {R} ^{m},$ the matrices $\mathbf {U}$ and $\mathbf {V} ^{*}$ represent [rotations](https://en.wikipedia.org/wiki/Rotation_(geometry)) or [reflection](https://en.wikipedia.org/wiki/Reflection_(geometry)) of the space, while $\mathbf {\Sigma }$ represents the [scaling](https://en.wikipedia.org/wiki/Scaling_matrix) of each coordinate $\mathbf {x} _{i}$ by the factor $\sigma _{i}.$ Thus the SVD decomposition breaks down any linear transformation of $\mathbf {R} ^{m}$ into a [composition](https://en.wikipedia.org/wiki/Function_composition) of three geometrical [transformations](https://en.wikipedia.org/wiki/Transformation_(geometry)): a rotation or reflection ($\mathbf {V} ^{*}$), followed by a coordinate-by-coordinate [scaling](https://en.wikipedia.org/wiki/Scaling_(geometry) "Scaling (geometry)") ($\mathbf {\Sigma }$), followed by another rotation or reflection ($\mathbf {U}$).

In particular, if $\mathbf {M}$ has a positive determinant, then $\mathbf {U}$ and $\mathbf {V} ^{*}$ can be chosen to be both rotations with reflections, or both rotations without reflections.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup> If the determinant is negative, exactly one of them will have a reflection. If the determinant is zero, each can be independently chosen to be of either type.

If the matrix $\mathbf {M}$ is real but not square, namely $m\times n$ with $m\neq n,$ it can be interpreted as a linear transformation from $\mathbf {R} ^{n}$ to $\mathbf {R} ^{m}.$ Then $\mathbf {U}$ and $\mathbf {V} ^{*}$ can be chosen to be rotations/reflections of $\mathbf {R} ^{m}$ and $\mathbf {R} ^{n},$ respectively; and $\mathbf {\Sigma } ,$ besides scaling the first $\min\{m,n\}$ coordinates, also extends the vector with zeros, i.e. removes trailing coordinates, so as to turn $\mathbf {R} ^{n}$ into $\mathbf {R} ^{m}.$

### Singular values as semiaxes of an ellipse or ellipsoid

As shown in the figure, the [singular values](https://en.wikipedia.org/wiki/Singular_values) can be interpreted as the magnitude of the semiaxes of an [ellipse](https://en.wikipedia.org/wiki/Ellipse) in 2D. This concept can be generalized to $n$-dimensional [Euclidean space](https://en.wikipedia.org/wiki/Euclidean_space), with the singular values of any $n\times n$ [square matrix](https://en.wikipedia.org/wiki/Square_matrix) being viewed as the magnitude of the semiaxis of an $n$-dimensional [ellipsoid](https://en.wikipedia.org/wiki/Ellipsoid). Similarly, the singular values of any $m\times n$ matrix can be viewed as the magnitude of the semiaxis of an $n$-dimensional [ellipsoid](https://en.wikipedia.org/wiki/Ellipsoid) in $m$-dimensional space, for example as an ellipse in a (tilted) 2D plane in a 3D space. Singular values encode magnitude of the semiaxis, while singular vectors encode direction. See [below](#Geometric_meaning) for further details.

### The columns of U and V are orthonormal bases

Since $\mathbf {U}$ and $\mathbf {V} ^{*}$ are unitary, the columns of each of them form a set of [orthonormal vectors](https://en.wikipedia.org/wiki/Orthonormal_vectors), which can be regarded as [basis vectors](https://en.wikipedia.org/wiki/Basis_vectors). The matrix $\mathbf {M}$ maps the basis vector $\mathbf {V} _{i}$ to the stretched unit vector $\sigma _{i}\mathbf {U} _{i}.$ By the definition of a unitary matrix, the same is true for their conjugate transposes $\mathbf {U} ^{*}$ and $\mathbf {V} ,$ except the geometric interpretation of the singular values as stretches is lost. In short, the columns of $\mathbf {U} ,$ $\mathbf {U} ^{*},$ $\mathbf {V} ,$ and $\mathbf {V} ^{*}$ are [orthonormal bases](https://en.wikipedia.org/wiki/Orthonormal_basis). When $\mathbf {M}$ is a [positive-semidefinite](https://en.wikipedia.org/wiki/Definite_matrix) [Hermitian matrix](https://en.wikipedia.org/wiki/Hermitian_matrix), $\mathbf {U}$ and $\mathbf {V}$ are both equal to the unitary matrix used to diagonalize $\mathbf {M} .$ However, when $\mathbf {M}$ is not positive-semidefinite and Hermitian but still [diagonalizable](https://en.wikipedia.org/wiki/Diagonalizable), its [[Eigendecomposition]] and singular value decomposition are distinct.

### Relation to the four fundamental subspaces

- The first $r$ columns of $\mathbf {U}$ are a basis of the [column space](https://en.wikipedia.org/wiki/Column_space) of $\mathbf {M}$.
- The last $m-r$ columns of $\mathbf {U}$ are a basis of the [null space](https://en.wikipedia.org/wiki/Null_space) of $\mathbf {M} ^{*}$.
- The first $r$ columns of $\mathbf {V}$ are a basis of the column space of $\mathbf {M} ^{*}$ (the [row space](https://en.wikipedia.org/wiki/Row_space) of $\mathbf {M}$ in the real case).
- The last $n-r$ columns of $\mathbf {V}$ are a basis of the null space of $\mathbf {M}$.

### Geometric meaning

Because $\mathbf {U}$ and $\mathbf {V}$ are unitary, we know that the columns $\mathbf {U} _{1},\ldots ,\mathbf {U} _{m}$ of $\mathbf {U}$ yield an [orthonormal basis](https://en.wikipedia.org/wiki/Orthonormal_basis) of $K^{m}$ and the columns $\mathbf {V} _{1},\ldots ,\mathbf {V} _{n}$ of $\mathbf {V}$ yield an orthonormal basis of $K^{n}$ (with respect to the standard [scalar products](https://en.wikipedia.org/wiki/Scalar_product) on these spaces).

The [[Linear Transformation]] 

$$
T:\left\{{\begin{aligned}K^{n}&\to K^{m}\\x&\mapsto \mathbf {M} x\end{aligned}}\right.
$$

 has a particularly simple description with respect to these orthonormal bases: we have 

$$
T(\mathbf {V} _{i})=\sigma _{i}\mathbf {U} _{i},\qquad i=1,\ldots ,\min(m,n),
$$

 where $\sigma _{i}$ is the $i$-th diagonal entry of $\mathbf {\Sigma } ,$ and $T(\mathbf {V} _{i})=0$ for $i>\min(m,n).$

The geometric content of the SVD theorem can thus be summarized as follows: for every linear map $T:K^{n}\to K^{m}$ one can find orthonormal bases of $K^{n}$ and $K^{m}$ such that $T$ maps the $i$-th basis vector of $K^{n}$ to a non-negative multiple of the $i$-th basis vector of $K^{m},$ and sends the leftover basis vectors to zero. With respect to these bases, the map $T$ is therefore represented by a diagonal matrix with non-negative real diagonal entries.

To get a more visual flavor of singular values and SVD factorization – at least when working on real vector spaces – consider the sphere $S$ of radius one in $\mathbf {R} ^{n}.$ The linear map $T$ maps this sphere onto an [ellipsoid](https://en.wikipedia.org/wiki/Ellipsoid) in $\mathbf {R} ^{m}.$ Non-zero singular values are simply the lengths of the [semi-axes](https://en.wikipedia.org/wiki/Semi-minor_axis) of this ellipsoid. Especially when $n=m,$ and all the singular values are distinct and non-zero, the SVD of the linear map $T$ can be easily analyzed as a succession of three consecutive moves: consider the ellipsoid $T(S)$ and specifically its axes; then consider the directions in $\mathbf {R} ^{n}$ sent by $T$ onto these axes. These directions happen to be mutually orthogonal. Apply first an isometry $\mathbf {V} ^{*}$ sending these directions to the coordinate axes of $\mathbf {R} ^{n}.$ On a second move, apply an [endomorphism](https://en.wikipedia.org/wiki/Endomorphism) $\mathbf {D}$ diagonalized along the coordinate axes and stretching or shrinking in each direction, using the semi-axes lengths of $T(S)$ as stretching coefficients. The composition $\mathbf {D} \circ \mathbf {V} ^{*}$ then sends the unit-sphere onto an ellipsoid isometric to $T(S).$ To define the third and last move, apply an isometry $\mathbf {U}$ to this ellipsoid to obtain $T(S).$ As can be easily checked, the composition $\mathbf {U} \circ \mathbf {D} \circ \mathbf {V} ^{*}$ coincides with $T.$

## Example

Consider the $4\times 5$ matrix 

$$
\mathbf {M} ={\begin{bmatrix}1&0&0&0&2\\0&0&3&0&0\\0&0&0&0&0\\0&2&0&0&0\end{bmatrix}}
$$

A singular value decomposition of this matrix is given by $\mathbf {U} \mathbf {\Sigma } \mathbf {V} ^{*}$

$$
{\begin{aligned}\mathbf {U} &={\begin{bmatrix}\color {Green}0&\color {Blue}-1&\color {Cyan}0&\color {Emerald}0\\\color {Green}-1&\color {Blue}0&\color {Cyan}0&\color {Emerald}0\\\color {Green}0&\color {Blue}0&\color {Cyan}0&\color {Emerald}-1\\\color {Green}0&\color {Blue}0&\color {Cyan}-1&\color {Emerald}0\end{bmatrix}}\\[6pt]\mathbf {\Sigma } &={\begin{bmatrix}3&0&0&0&\color {Gray}{\mathit {0}}\\0&{\sqrt {5}}&0&0&\color {Gray}{\mathit {0}}\\0&0&2&0&\color {Gray}{\mathit {0}}\\0&0&0&\color {Red}\mathbf {0} &\color {Gray}{\mathit {0}}\end{bmatrix}}\\[6pt]\mathbf {V} ^{*}&={\begin{bmatrix}\color {Violet}0&\color {Violet}0&\color {Violet}-1&\color {Violet}0&\color {Violet}0\\\color {Plum}-{\sqrt {0.2}}&\color {Plum}0&\color {Plum}0&\color {Plum}0&\color {Plum}-{\sqrt {0.8}}\\\color {Magenta}0&\color {Magenta}-1&\color {Magenta}0&\color {Magenta}0&\color {Magenta}0\\\color {Orchid}0&\color {Orchid}0&\color {Orchid}0&\color {Orchid}1&\color {Orchid}0\\\color {Purple}-{\sqrt {0.8}}&\color {Purple}0&\color {Purple}0&\color {Purple}0&\color {Purple}{\sqrt {0.2}}\end{bmatrix}}\end{aligned}}
$$

The scaling matrix $\mathbf {\Sigma }$ is zero outside of the diagonal (grey italics) and one diagonal element is zero (red bold, light blue bold in dark mode). Furthermore, because the matrices $\mathbf {U}$ and $\mathbf {V} ^{*}$ are [unitary](https://en.wikipedia.org/wiki/Unitary_matrix), multiplying by their respective conjugate transposes yields [identity matrices](https://en.wikipedia.org/wiki/Identity_matrix), as shown below. In this case, because $\mathbf {U}$ and $\mathbf {V} ^{*}$ are real valued, each is an [orthogonal matrix](https://en.wikipedia.org/wiki/Orthogonal_matrix).

$$
{\begin{aligned}\mathbf {U} \mathbf {U} ^{*}&={\begin{bmatrix}1&0&0&0\\0&1&0&0\\0&0&1&0\\0&0&0&1\end{bmatrix}}=\mathbf {I} _{4}\\[6pt]\mathbf {V} \mathbf {V} ^{*}&={\begin{bmatrix}1&0&0&0&0\\0&1&0&0&0\\0&0&1&0&0\\0&0&0&1&0\\0&0&0&0&1\end{bmatrix}}=\mathbf {I} _{5}\end{aligned}}
$$

This particular singular value decomposition is not unique. For instance, we can keep $\mathbf {U}$ and $\mathbf {\Sigma }$ the same, but change the last two rows of $\mathbf {V} ^{*}$ such that 

$$
\mathbf {V} ^{*}={\begin{bmatrix}\color {Violet}0&\color {Violet}0&\color {Violet}-1&\color {Violet}0&\color {Violet}0\\\color {Plum}-{\sqrt {0.2}}&\color {Plum}0&\color {Plum}0&\color {Plum}0&\color {Plum}-{\sqrt {0.8}}\\\color {Magenta}0&\color {Magenta}-1&\color {Magenta}0&\color {Magenta}0&\color {Magenta}0\\\color {Orchid}{\sqrt {0.4}}&\color {Orchid}0&\color {Orchid}0&\color {Orchid}{\sqrt {0.5}}&\color {Orchid}-{\sqrt {0.1}}\\\color {Purple}-{\sqrt {0.4}}&\color {Purple}0&\color {Purple}0&\color {Purple}{\sqrt {0.5}}&\color {Purple}{\sqrt {0.1}}\end{bmatrix}}
$$

and get an equally valid singular value decomposition. As the matrix $\mathbf {M}$ has rank 3, it has only 3 nonzero singular values. In taking the product $\mathbf {U} \mathbf {\Sigma } \mathbf {V} ^{*}$, the final column of $\mathbf {U}$ and the final two rows of $\mathbf {V^{*}}$ are multiplied by zero, so have no effect on the matrix product, and can be replaced by any unit vectors which are orthogonal to the first three and to each-other.

The [compact SVD](#Compact_SVD), $\mathbf {M} =\mathbf {U} _{r}\mathbf {\Sigma } _{r}\mathbf {V} _{r}^{*}$, eliminates these superfluous rows, columns, and singular values: 

$$
{\begin{aligned}\mathbf {U} _{r}&={\begin{bmatrix}\color {Green}0&\color {Blue}-1&\color {Cyan}0\\\color {Green}-1&\color {Blue}0&\color {Cyan}0\\\color {Green}0&\color {Blue}0&\color {Cyan}0\\\color {Green}0&\color {Blue}0&\color {Cyan}-1\end{bmatrix}}\\[6pt]\mathbf {\Sigma } _{r}&={\begin{bmatrix}3&0&0\\0&{\sqrt {5}}&0\\0&0&2\end{bmatrix}}\\[6pt]\mathbf {V} _{r}^{*}&={\begin{bmatrix}\color {Violet}0&\color {Violet}0&\color {Violet}-1&\color {Violet}0&\color {Violet}0\\\color {Plum}-{\sqrt {0.2}}&\color {Plum}0&\color {Plum}0&\color {Plum}0&\color {Plum}-{\sqrt {0.8}}\\\color {Magenta}0&\color {Magenta}-1&\color {Magenta}0&\color {Magenta}0&\color {Magenta}0\end{bmatrix}}\end{aligned}}
$$

## SVD and spectral decomposition

### Singular values, singular vectors, and their relation to the SVD

A non-negative real number $\sigma$ is a **[singular value](https://en.wikipedia.org/wiki/Singular_value)** for $\mathbf {M}$ if and only if there exist [unit vectors](https://en.wikipedia.org/wiki/Unit_vector) $\mathbf {u}$ in $K^{m}$ and $\mathbf {v}$ in $K^{n}$ such that 

$$
{\begin{aligned}\mathbf {Mv} &=\sigma \mathbf {u} ,\\[3mu]\mathbf {M} ^{*}\mathbf {u} &=\sigma \mathbf {v} .\end{aligned}}
$$

The vectors $\mathbf {u}$ and $\mathbf {v}$ are called **left-singular** and **right-singular vectors** for $\sigma ,$ respectively.

In any singular value decomposition 

$$
\mathbf {M} =\mathbf {U} \mathbf {\Sigma } \mathbf {V} ^{*}
$$

 the diagonal entries of $\mathbf {\Sigma }$ are equal to the singular values of $\mathbf {M} .$ The first $p=\min(m,n)$ columns of $\mathbf {U}$ and $\mathbf {V}$ are, respectively, left- and right-singular vectors for the corresponding singular values. Consequently, the above theorem implies that:

- An $m\times n$ matrix $\mathbf {M}$ has at most $p$ distinct singular values.
- It is always possible to find a [unitary basis](https://en.wikipedia.org/wiki/Orthogonal_basis) $\mathbf {U}$ for $K^{m}$ with a subset of basis vectors spanning the left-singular vectors of each singular value of $\mathbf {M} .$
- It is always possible to find a unitary basis $\mathbf {V}$ for $K^{n}$ with a subset of basis vectors spanning the right-singular vectors of each singular value of $\mathbf {M} .$

A singular value for which we can find two left (or right) singular vectors that are linearly independent is called *degenerate*. If $\mathbf {u} _{1}$ and $\mathbf {u} _{2}$ are two left-singular vectors which both correspond to the singular value σ, then any normalized linear combination of the two vectors is also a left-singular vector corresponding to the singular value σ. The similar statement is true for right-singular vectors. The number of independent left and right-singular vectors coincides, and these singular vectors appear in the same columns of $\mathbf {U}$ and $\mathbf {V}$ corresponding to diagonal elements of $\mathbf {\Sigma }$ all with the same value $\sigma .$

As an exception, the left and right-singular vectors of singular value 0 comprise all unit vectors in the [cokernel](https://en.wikipedia.org/wiki/Cokernel) and [kernel](https://en.wikipedia.org/wiki/Kernel_(linear_algebra) "Kernel (linear algebra)"), respectively, of $\mathbf {M} ,$ which by the [rank–nullity theorem](https://en.wikipedia.org/wiki/Rank%E2%80%93nullity_theorem) cannot be the same dimension if $m\neq n.$ Even if all singular values are nonzero, if $m>n$ then the cokernel is nontrivial, in which case $\mathbf {U}$ is padded with $m-n$ orthogonal vectors from the cokernel. Conversely, if $m<n,$ then $\mathbf {V}$ is padded by $n-m$ orthogonal vectors from the kernel. However, if the singular value of $0$ exists, the extra columns of $\mathbf {U}$ or $\mathbf {V}$ already appear as left or right-singular vectors.

Non-degenerate singular values always have unique left- and right-singular vectors, up to multiplication by a unit-phase factor $e^{i\varphi }$ (for the real case up to a sign). Consequently, if all singular values of a square matrix $\mathbf {M}$ are non-degenerate and non-zero, then its singular value decomposition is unique, up to multiplication of a column of $\mathbf {U}$ by a unit-phase factor and simultaneous multiplication of the corresponding column of $\mathbf {V}$ by the same unit-phase factor. In general, the SVD is unique up to arbitrary unitary transformations applied uniformly to the column vectors of both $\mathbf {U}$ and $\mathbf {V}$ spanning the subspaces of each singular value, and up to arbitrary unitary transformations on vectors of $\mathbf {U}$ and $\mathbf {V}$ spanning the kernel and cokernel, respectively, of $\mathbf {M} .$

### Relation to eigenvalue decomposition

The singular value decomposition is very general in the sense that it can be applied to any $m\times n$ matrix, whereas [eigenvalue decomposition](https://en.wikipedia.org/wiki/Eigenvalue_decomposition) can only be applied to square [diagonalizable matrices](https://en.wikipedia.org/wiki/Diagonalizable_matrix). Nevertheless, the two decompositions are related.

If $\mathbf {M}$ has SVD $\mathbf {M} =\mathbf {U} \mathbf {\Sigma } \mathbf {V} ^{*},$ the following two relations hold: 

$$
{\begin{aligned}\mathbf {M} ^{*}\mathbf {M} &=\mathbf {V} \mathbf {\Sigma } ^{*}\mathbf {U} ^{*}\,\mathbf {U} \mathbf {\Sigma } \mathbf {V} ^{*}=\mathbf {V} (\mathbf {\Sigma } ^{*}\mathbf {\Sigma } )\mathbf {V} ^{*},\\[3mu]\mathbf {M} \mathbf {M} ^{*}&=\mathbf {U} \mathbf {\Sigma } \mathbf {V} ^{*}\,\mathbf {V} \mathbf {\Sigma } ^{*}\mathbf {U} ^{*}=\mathbf {U} (\mathbf {\Sigma } \mathbf {\Sigma } ^{*})\mathbf {U} ^{*}.\end{aligned}}
$$

The right-hand sides of these relations describe the eigenvalue decompositions of the left-hand sides. Consequently:

- The columns of $\mathbf {V}$ (referred to as right-singular vectors) are [eigenvectors](https://en.wikipedia.org/wiki/Eigenvectors) of $\mathbf {M} ^{*}\mathbf {M} .$
- The columns of $\mathbf {U}$ (referred to as left-singular vectors) are eigenvectors of $\mathbf {M} \mathbf {M} ^{*}.$
- The non-zero elements of $\mathbf {\Sigma }$ (non-zero singular values) are the square roots of the non-zero [eigenvalues](https://en.wikipedia.org/wiki/Eigenvalues) of $\mathbf {M} ^{*}\mathbf {M}$ or $\mathbf {M} \mathbf {M} ^{*}.$

In the special case of $\mathbf {M}$ being a [normal matrix](https://en.wikipedia.org/wiki/Normal_matrix), and thus also square, the [[Spectral Theorem]] ensures that it can be [unitarily](https://en.wikipedia.org/wiki/Unitary_transform) [diagonalized](https://en.wikipedia.org/wiki/Diagonalizable_matrix) using a basis of [eigenvectors](https://en.wikipedia.org/wiki/Eigenvector), and thus decomposed as $\mathbf {M} =\mathbf {U} \mathbf {D} \mathbf {U} ^{*}$ for some unitary matrix $\mathbf {U}$ and diagonal matrix $\mathbf {D}$ with complex elements $\sigma _{i}$ along the diagonal. When $\mathbf {M}$ is [[Positive-Definite Matrix|positive semi-definite]], $\sigma _{i}$ will be non-negative real numbers so that the decomposition $\mathbf {M} =\mathbf {U} \mathbf {D} \mathbf {U} ^{*}$ is also a singular value decomposition. Otherwise, it can be recast as an SVD by moving the phase $e^{i\varphi }$ of each $\sigma _{i}$ to either its corresponding $\mathbf {V} _{i}$ or $\mathbf {U} _{i}.$ The natural connection of the SVD to non-normal matrices is through the [polar decomposition](https://en.wikipedia.org/wiki/Polar_decomposition) theorem: $\mathbf {M} =\mathbf {S} \mathbf {R} ,$ where $\mathbf {S} =\mathbf {U} \mathbf {\Sigma } \mathbf {U} ^{*}$ is positive semidefinite and normal, and $\mathbf {R} =\mathbf {U} \mathbf {V} ^{*}$ is unitary.

Thus, except for positive semi-definite matrices, the eigenvalue decomposition and SVD of $\mathbf {M} ,$ while related, differ: the eigenvalue decomposition is $\mathbf {M} =\mathbf {U} \mathbf {D} \mathbf {U} ^{-1},$ where $\mathbf {U}$ is not necessarily unitary and $\mathbf {D}$ is not necessarily positive semi-definite, while the SVD is $\mathbf {M} =\mathbf {U} \mathbf {\Sigma } \mathbf {V} ^{*},$ where $\mathbf {\Sigma }$ is diagonal and positive semi-definite, and $\mathbf {U}$ and $\mathbf {V}$ are unitary matrices that are not necessarily related except through the matrix $\mathbf {M} .$ While only [non-defective](https://en.wikipedia.org/wiki/Defective_matrix) square matrices have an eigenvalue decomposition, any $m\times n$ matrix has a SVD.

## Applications of the SVD

### Pseudoinverse

The singular value decomposition can be used for computing the [[Moore-Penrose Pseudoinverse|pseudoinverse]] of a matrix. The pseudoinverse of the matrix $\mathbf {M}$ with singular value decomposition $\mathbf {M} =\mathbf {U} \mathbf {\Sigma } \mathbf {V} ^{*}$ is 

$$
\mathbf {M} ^{+}=\mathbf {V} {\boldsymbol {\Sigma }}^{+}\mathbf {U} ^{\ast },
$$

 where ${\boldsymbol {\Sigma }}^{+}$ is the pseudoinverse of ${\boldsymbol {\Sigma }}$, which is formed by replacing every non-zero diagonal entry by its [reciprocal](https://en.wikipedia.org/wiki/Multiplicative_inverse) and transposing the resulting matrix. The pseudoinverse is one way to solve [linear least squares](https://en.wikipedia.org/wiki/Linear_least_squares_(mathematics)) problems.

### Solving homogeneous linear equations

A set of [homogeneous linear equations](https://en.wikipedia.org/wiki/Homogeneous_linear_equation) can be written as $\mathbf {A} \mathbf {x} =\mathbf {0}$ for a matrix $\mathbf {A}$, vector $\mathbf {x}$, and [zero vector](https://en.wikipedia.org/wiki/Zero_vector) $\mathbf {0}$. A typical situation is that $\mathbf {A}$ is known and a non-zero $\mathbf {x}$ is to be determined which satisfies the equation. Such an $\mathbf {x}$ belongs to $\mathbf {A}$'s [null space](https://en.wikipedia.org/wiki/Kernel_(matrix)) and is sometimes called a (right) null vector of $\mathbf {A} .$ The vector $\mathbf {x}$ can be characterized as a right-singular vector corresponding to a singular value of $\mathbf {A}$ that is zero. This observation means that if $\mathbf {A}$ is a [square matrix](https://en.wikipedia.org/wiki/Square_matrix) and has no vanishing singular value, the equation has no non-zero $\mathbf {x}$ as a solution. It also means that if there are several vanishing singular values, any linear combination of the corresponding right-singular vectors is a valid solution. Analogously to the definition of a (right) null vector, a non-zero $\mathbf {x}$ satisfying $\mathbf {x} ^{*}\mathbf {A} =\mathbf {0}$ with $\mathbf {x} ^{*}$ denoting the conjugate transpose of $\mathbf {x}$ is called a left null vector of $\mathbf {A} .$

### Total least squares minimization

A [total least squares](https://en.wikipedia.org/wiki/Total_least_squares) problem seeks the vector $\mathbf {x}$ that minimizes the [2-norm](https://en.wikipedia.org/wiki/Vector_norm#p-norm) of a vector $\mathbf {A} \mathbf {x}$ under the constraint $\|\mathbf {x} \|=1.$ The solution turns out to be the right-singular vector of $\mathbf {A}$ corresponding to the smallest singular value.

### Range, null space and rank

Another application of the SVD is that it provides an explicit representation of the [range](https://en.wikipedia.org/wiki/Column_space) and [null space](https://en.wikipedia.org/wiki/Null_space) of a matrix $\mathbf {M} .$ The right-singular vectors corresponding to vanishing singular values of $\mathbf {M}$ span the null space of $\mathbf {M}$ and the left-singular vectors corresponding to the non-zero singular values of $\mathbf {M}$ span the range of $\mathbf {M} .$ For example, in the above [example](#Example) the null space is spanned by the last row of $\mathbf {V} ^{*}$ and the range is spanned by the first three columns of $\mathbf {U} .$

As a consequence, the [rank](https://en.wikipedia.org/wiki/Rank_of_a_matrix) of $\mathbf {M}$ equals the number of non-zero singular values which is the same as the number of non-zero diagonal elements in $\mathbf {\Sigma }$. In [numerical linear algebra](https://en.wikipedia.org/wiki/Numerical_linear_algebra) the singular values can be used to determine the *effective rank* of a matrix, as [rounding error](https://en.wikipedia.org/wiki/Rounding_error) may lead to small but non-zero singular values in a rank deficient matrix. Singular values beyond a significant gap are assumed to be numerically equivalent to zero.

### Low-rank matrix approximation

Some practical applications need to solve the problem of [approximating](https://en.wikipedia.org/wiki/Low-rank_approximation) a matrix $\mathbf {M}$ with another matrix ${\tilde {\mathbf {M} }}$, said to be [truncated](#Truncated_SVD), which has a specific rank $r$. In the case that the approximation is based on minimizing the [Frobenius norm](https://en.wikipedia.org/wiki/Frobenius_norm) of the difference between $\mathbf {M}$ and ${\tilde {\mathbf {M} }}$ under the constraint that $\operatorname {rank} {\bigl (}{\tilde {\mathbf {M} }}{\bigr )}=r,$ it turns out that the solution is given by the SVD of $\mathbf {M} ,$ namely 

$$
{\tilde {\mathbf {M} }}=\mathbf {U} {\tilde {\mathbf {\Sigma } }}\mathbf {V} ^{*},
$$

 where ${\tilde {\mathbf {\Sigma } }}$ is the same matrix as $\mathbf {\Sigma }$ except that it contains only the $r$ largest singular values (the other singular values are replaced by zero). This is known as the **[Eckart–Young theorem](https://en.wikipedia.org/wiki/Low-rank_approximation)**, as it was proved by those two authors in 1936.

### Image compression

![[media/ef212be4d8cdc82b9fa7a7ed942beaf9b5e39f3a.jpg]]
Singular-value decomposition (SVD) image compression of a 1996 Chevrolet Corvette photograph. The original RGB image (upper-left) is compared with rank 1, 10, and 100 reconstructions.

One practical consequence of the low-rank approximation given by SVD is that a [greyscale image](https://en.wikipedia.org/wiki/Greyscale_image) represented as an $m\times n$ matrix $\mathbf {A}$, can be efficiently represented by keeping the first $k$ singular values and corresponding vectors. The truncated decomposition

$\mathbf {A} _{k}=\sum _{j=1}^{k}\sigma _{j}\mathbf {u} _{j}\mathbf {v} _{j}^{T}$ gives an image with the best 2-norm error out of all rank k approximations. Thus, the task becomes finding an approximation that balances retaining perceptual fidelity with the number of vectors required to reconstruct the image. Storing $\mathbf {A} _{k}$ requires only $k(n+m+1)$ floating-point numbers compared to $nm$ integers. This same idea extends to color images by applying this operation to each channel or stacking the channels into one matrix.

Since the singular values of most natural images decay quickly, most of their variance is often captured by a small $k$. For a 1528 × 1225 greyscale image, we can achieve a relative error of $.7\%$ with as little as $k=100$. In practice, however, computing the SVD can be too computationally expensive and the resulting compression is typically less storage efficient than a specialized algorithm such as [JPEG](https://en.wikipedia.org/wiki/JPEG).

### Separable models

The SVD can be thought of as decomposing a matrix into a weighted, ordered sum of separable matrices. By separable, we mean that a matrix $\mathbf {A}$ can be written as an [outer product](https://en.wikipedia.org/wiki/Outer_product) of two vectors $\mathbf {A} =\mathbf {u} \otimes \mathbf {v} ,$ or, in coordinates, $A_{ij}=u_{i}v_{j}.$ Specifically, the matrix $\mathbf {M}$ can be decomposed as,

$$
\mathbf {M} =\sum _{i}\mathbf {A} _{i}=\sum _{i}\sigma _{i}\mathbf {U} _{i}\otimes \mathbf {V} _{i}.
$$

Here $\mathbf {U} _{i}$ and $\mathbf {V} _{i}$ are the $i$-th columns of the corresponding SVD matrices, $\sigma _{i}$ are the ordered singular values, and each $\mathbf {A} _{i}$ is separable. The SVD can be used to find the decomposition of an image processing filter into separable horizontal and vertical filters. Note that the number of non-zero $\sigma _{i}$ is exactly the rank of the matrix.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup> Separable models often arise in biological systems, and the SVD factorization is useful to analyze such systems. For example, some visual area V1 simple cells' receptive fields can be well described by a [Gabor filter](https://en.wikipedia.org/wiki/Gabor_filter) in the space domain multiplied by a modulation function in the time domain. Thus, given a linear filter evaluated through, for example, [reverse correlation](https://en.wikipedia.org/wiki/Spike-triggered_average), one can rearrange the two spatial dimensions into one dimension, thus yielding a two-dimensional filter (space, time) which can be decomposed through SVD. The first column of $\mathbf {U}$ in the SVD factorization is then a Gabor while the first column of $\mathbf {V}$ represents the time modulation (or vice versa). One may then define an index of separability

$$
\alpha ={\frac {\sigma _{1}^{2}}{\sum _{i}\sigma _{i}^{2}}},
$$

which is the fraction of the power in the matrix M which is accounted for by the first separable matrix in the decomposition.

### Nearest orthogonal matrix

It is possible to use the SVD of a square matrix $\mathbf {A}$ to determine the [orthogonal matrix](https://en.wikipedia.org/wiki/Orthogonal_matrix) $\mathbf {Q}$ closest to $\mathbf {A} .$ The closeness of fit is measured by the [Frobenius norm](https://en.wikipedia.org/wiki/Frobenius_norm) of $\mathbf {Q} -\mathbf {A} .$ The solution is the product $\mathbf {U} \mathbf {V} ^{*}.$ This intuitively makes sense because an orthogonal matrix would have the decomposition $\mathbf {U} \mathbf {I} \mathbf {V} ^{*}$ where $\mathbf {I}$ is the identity matrix, so that if $\mathbf {A} =\mathbf {U} \mathbf {\Sigma } \mathbf {V} ^{*}$ then the product $\mathbf {A} =\mathbf {U} \mathbf {V} ^{*}$ amounts to replacing the singular values with ones. Equivalently, the solution is the unitary matrix $\mathbf {R} =\mathbf {U} \mathbf {V} ^{*}$ of the Polar Decomposition $\mathbf {M} =\mathbf {R} \mathbf {P} =\mathbf {P} '\mathbf {R}$ in either order of stretch and rotation, as described above.

A similar problem, with interesting applications in [shape analysis](https://en.wikipedia.org/wiki/Shape_analysis_(digital_geometry) "Shape analysis (digital geometry)"), is the [orthogonal Procrustes problem](https://en.wikipedia.org/wiki/Orthogonal_Procrustes_problem), which consists of finding an orthogonal matrix $\mathbf {Q}$ which most closely maps $\mathbf {A}$ to $\mathbf {B} .$ Specifically, 

$$
\mathbf {Q} ={\underset {\Omega }{\operatorname {argmin} }}\|\mathbf {A} {\boldsymbol {\Omega }}-\mathbf {B} \|_{F}\quad {\text{subject to}}\quad {\boldsymbol {\Omega }}^{\operatorname {T} }{\boldsymbol {\Omega }}=\mathbf {I} ,
$$

 where $\|\cdot \|_{F}$ denotes the Frobenius norm.

This problem is equivalent to finding the nearest orthogonal matrix to a given matrix $\mathbf {M} =\mathbf {A} ^{\operatorname {T} }\mathbf {B}$.

### The Kabsch algorithm

The [Kabsch algorithm](https://en.wikipedia.org/wiki/Kabsch_algorithm) (called [Wahba's problem](https://en.wikipedia.org/wiki/Wahba%27s_problem) in other fields) uses SVD to compute the optimal rotation (with respect to least-squares minimization) that will align a set of points with a corresponding set of points. It is used, among other applications, to compare the structures of molecules.

### Principal Component Analysis

The SVD can be used to construct the principal components in [[Principal Component Analysis]] as follows:

Let $\mathbf {X} \in \mathbb {R} ^{N\times p}$ be a data matrix where each of the $N$ rows is a (feature-wise) mean-centered observation, each of dimension $p$.

The SVD of $\mathbf {X}$ is: 

$$
\mathbf {X} =\mathbf {V} {\boldsymbol {\Sigma }}\mathbf {U} ^{\ast }
$$

We see that $\mathbf {V} {\boldsymbol {\Sigma }}$ contains the scores of the rows of $\mathbf {X}$ (i.e. each observation), and $\mathbf {U}$ is the matrix whose columns are principal component loading vectors.

### Signal processing

The SVD and pseudoinverse have been successfully applied to [signal processing](https://en.wikipedia.org/wiki/Signal_processing), [image processing](https://en.wikipedia.org/wiki/Image_processing) and [big data](https://en.wikipedia.org/wiki/Big_data) (e.g., in genomic signal processing).

### Other examples

The SVD is also applied extensively to the study of linear [inverse problems](https://en.wikipedia.org/wiki/Inverse_problem) and is useful in the analysis of regularization methods such as that of [Tikhonov](https://en.wikipedia.org/wiki/Tikhonov_regularization). It is widely used in statistics, where it is related to [[Principal Component Analysis]] and to [correspondence analysis](https://en.wikipedia.org/wiki/Correspondence_analysis), and in [signal processing](https://en.wikipedia.org/wiki/Signal_processing) and [pattern recognition](https://en.wikipedia.org/wiki/Pattern_recognition). It is also used in output-only [modal analysis](https://en.wikipedia.org/wiki/Modal_analysis), where the non-scaled [mode shapes](https://en.wikipedia.org/wiki/Mode_shape) can be determined from the singular vectors. Yet another usage is [latent semantic indexing](https://en.wikipedia.org/wiki/Latent_semantic_indexing) in natural-language text processing.

In general numerical computation involving linear or linearized systems, there is a universal constant that characterizes the regularity or singularity of a problem, which is the system's "condition number" $\kappa :=\sigma _{\text{max}}/\sigma _{\text{min}}$. It often controls the error rate or convergence rate of a given computational scheme on such systems.

The SVD also plays a crucial role in the field of [quantum information](https://en.wikipedia.org/wiki/Quantum_information), in a form often referred to as the [Schmidt decomposition](https://en.wikipedia.org/wiki/Schmidt_decomposition). Through it, states of two quantum systems are naturally decomposed, providing a necessary and sufficient condition for them to be [entangled](https://en.wikipedia.org/wiki/Quantum_entanglement): if the rank of the $\mathbf {\Sigma }$ matrix is larger than one.

One application of SVD to rather large matrices is in [numerical weather prediction](https://en.wikipedia.org/wiki/Numerical_weather_prediction), where [Lanczos methods](https://en.wikipedia.org/wiki/Lanczos_algorithm) are used to estimate the most linearly quickly growing few perturbations to the central numerical weather prediction over a given initial forward time period; i.e., the singular vectors corresponding to the largest singular values of the linearized propagator for the global weather over that time interval. The output singular vectors in this case are entire weather systems. These perturbations are then run through the full nonlinear model to generate an [ensemble forecast](https://en.wikipedia.org/wiki/Ensemble_forecasting), giving a handle on some of the uncertainty that should be allowed for around the current central prediction.

SVD has also been applied to reduced order modelling. The aim of reduced order modelling is to reduce the number of degrees of freedom in a [complex system](https://en.wikipedia.org/wiki/Complex_system) which is to be modeled. SVD was coupled with [radial basis functions](https://en.wikipedia.org/wiki/Radial_basis_functions) to interpolate solutions to three-dimensional unsteady flow problems.

Interestingly, SVD has been used to improve gravitational waveform modeling by the ground-based gravitational-wave interferometer aLIGO. SVD can help to increase the accuracy and speed of waveform generation to support gravitational-waves searches and update two different waveform models.

Singular value decomposition is used in [recommender systems](https://en.wikipedia.org/wiki/Recommender_systems) to predict people's item ratings. Distributed algorithms have been developed for the purpose of calculating the SVD on clusters of commodity machines.

Low-rank SVD has been applied for hotspot detection from spatiotemporal data with application to disease [outbreak](https://en.wikipedia.org/wiki/Outbreak) detection. A combination of SVD and [higher-order SVD](https://en.wikipedia.org/wiki/Higher-order_singular_value_decomposition) also has been applied for real time event detection from complex data streams (multivariate data with space and time dimensions) in [disease surveillance](https://en.wikipedia.org/wiki/Disease_surveillance).

In [astrodynamics](https://en.wikipedia.org/wiki/Astrodynamics), the SVD and its variants are used as an option to determine suitable maneuver directions for transfer trajectory design and [orbital station-keeping](https://en.wikipedia.org/wiki/Orbital_station-keeping).

The SVD can be used to measure the similarity between real-valued matrices. By measuring the angles between the singular vectors, the inherent two-dimensional structure of matrices is accounted for. This method was shown to outperform [cosine similarity](https://en.wikipedia.org/wiki/Cosine_similarity) and [Frobenius norm](https://en.wikipedia.org/wiki/Frobenius_norm) in most cases, including brain activity measurements from [neuroscience](https://en.wikipedia.org/wiki/Neuroscience) experiments.

## Proof of existence

An eigenvalue $\lambda$ of a matrix $\mathbf {M}$ is characterized by the algebraic relation $\mathbf {M} \mathbf {u} =\lambda \mathbf {u} .$ When $\mathbf {M}$ is [Hermitian](https://en.wikipedia.org/wiki/Hermitian_matrix), a variational characterization is also available. Let $\mathbf {M}$ be a real $n\times n$ [symmetric matrix](https://en.wikipedia.org/wiki/Symmetric_matrix). Define

$$
f:\left\{{\begin{aligned}\mathbb {R} ^{n}&\to \mathbb {R} \\\mathbf {x} &\mapsto \mathbf {x} ^{\operatorname {T} }\mathbf {M} \mathbf {x} \end{aligned}}\right.
$$

By the [extreme value theorem](https://en.wikipedia.org/wiki/Extreme_value_theorem), this continuous function attains a maximum at some $\mathbf {u}$ when restricted to the unit sphere $\{\|\mathbf {x} \|=1\}.$ By the [[Lagrange Multipliers]] theorem, $\mathbf {u}$ necessarily satisfies 

$$
\nabla \mathbf {u} ^{\operatorname {T} }\mathbf {M} \mathbf {u} -\lambda \cdot \nabla \mathbf {u} ^{\operatorname {T} }\mathbf {u} =\mathbf {0}
$$

 for some real number $\lambda .$ The nabla symbol, $\nabla$, is the [del](https://en.wikipedia.org/wiki/Del) operator (differentiation with respect to $\mathbf {x}$). Using the symmetry of $\mathbf {M}$ we obtain 

$$
\nabla \mathbf {x} ^{\operatorname {T} }\mathbf {M} \mathbf {x} -\lambda \cdot \nabla \mathbf {x} ^{\operatorname {T} }\mathbf {x} =2(\mathbf {M} -\lambda \mathbf {I} )\mathbf {x} .
$$

Therefore $\mathbf {M} \mathbf {u} =\lambda \mathbf {u} ,$ so $\mathbf {u}$ is a unit length eigenvector of $\mathbf {M} .$ For every unit length eigenvector $\mathbf {v}$ of $\mathbf {M}$ its eigenvalue is $f(\mathbf {v} ),$ so $\lambda$ is the largest eigenvalue of $\mathbf {M} .$ The same calculation performed on the orthogonal complement of $\mathbf {u}$ gives the next largest eigenvalue and so on. The complex Hermitian case is similar; there $f(\mathbf {x} )=\mathbf {x} ^{*}\mathbf {M} \mathbf {x}$ is a real-valued function of $2n$ real variables.

Singular values are similar in that they can be described algebraically or from variational principles. Although, unlike the eigenvalue case, Hermiticity, or symmetry, of $\mathbf {M}$ is no longer required.

This section gives these two arguments for existence of singular value decomposition.

### Based on the spectral theorem

Let $\mathbf {M}$ be an $m\times n$ complex matrix. Since $\mathbf {M} ^{*}\mathbf {M}$ is positive semi-definite and Hermitian, by the [[Spectral Theorem]], there exists an $n\times n$ unitary matrix $\mathbf {V}$ such that 

$$
\mathbf {V} ^{*}\mathbf {M} ^{*}\mathbf {M} \mathbf {V} ={\bar {\mathbf {D} }}={\begin{bmatrix}\mathbf {D} &0\\0&0\end{bmatrix}},
$$

 where $\mathbf {D}$ is diagonal and positive definite, of dimension $\ell \times \ell$, with $\ell$ the number of non-zero eigenvalues of $\mathbf {M} ^{*}\mathbf {M}$ (which can be shown to verify $\ell \leq \min(n,m)$). Note that $\mathbf {V}$ is here by definition a matrix whose $i$-th column is the $i$-th eigenvector of $\mathbf {M} ^{*}\mathbf {M}$, corresponding to the eigenvalue ${\bar {\mathbf {D} }}_{ii}$. Moreover, the $j$-th column of $\mathbf {V}$, for $j>\ell$, is an eigenvector of $\mathbf {M} ^{*}\mathbf {M}$ with eigenvalue ${\bar {\mathbf {D} }}_{jj}=0$. This can be expressed by writing $\mathbf {V}$ as $\mathbf {V} ={\begin{bmatrix}\mathbf {V} _{1}&\mathbf {V} _{2}\end{bmatrix}}$, where the columns of $\mathbf {V} _{1}$ and $\mathbf {V} _{2}$ therefore contain the eigenvectors of $\mathbf {M} ^{*}\mathbf {M}$ corresponding to non-zero and zero eigenvalues, respectively. Using this rewriting of $\mathbf {V}$, the equation becomes: 

$$
{\begin{bmatrix}\mathbf {V} _{1}^{*}\\\mathbf {V} _{2}^{*}\end{bmatrix}}\mathbf {M} ^{*}\mathbf {M} \,{\begin{bmatrix}\mathbf {V} _{1}&\!\!\mathbf {V} _{2}\end{bmatrix}}={\begin{bmatrix}\mathbf {V} _{1}^{*}\mathbf {M} ^{*}\mathbf {M} \mathbf {V} _{1}&\mathbf {V} _{1}^{*}\mathbf {M} ^{*}\mathbf {M} \mathbf {V} _{2}\\\mathbf {V} _{2}^{*}\mathbf {M} ^{*}\mathbf {M} \mathbf {V} _{1}&\mathbf {V} _{2}^{*}\mathbf {M} ^{*}\mathbf {M} \mathbf {V} _{2}\end{bmatrix}}={\begin{bmatrix}\mathbf {D} &0\\0&0\end{bmatrix}}.
$$

This implies that 

$$
\mathbf {V} _{1}^{*}\mathbf {M} ^{*}\mathbf {M} \mathbf {V} _{1}=\mathbf {D} ,\quad \mathbf {V} _{2}^{*}\mathbf {M} ^{*}\mathbf {M} \mathbf {V} _{2}=\mathbf {0} .
$$

Moreover, the second equation implies $\mathbf {M} \mathbf {V} _{2}=\mathbf {0}$. Finally, the unitary-ness of $\mathbf {V}$ translates, in terms of $\mathbf {V} _{1}$ and $\mathbf {V} _{2}$, into the following conditions: 

$$
{\begin{aligned}\mathbf {V} _{1}^{*}\mathbf {V} _{1}&=\mathbf {I} _{1},\\\mathbf {V} _{2}^{*}\mathbf {V} _{2}&=\mathbf {I} _{2},\\\mathbf {V} _{1}\mathbf {V} _{1}^{*}+\mathbf {V} _{2}\mathbf {V} _{2}^{*}&=\mathbf {I} _{12},\end{aligned}}
$$

 where the subscripts on the identity matrices are used to remark that they are of different dimensions.

Let us now define 

$$
\mathbf {U} _{1}=\mathbf {M} \mathbf {V} _{1}\mathbf {D} ^{-{\frac {1}{2}}}.
$$

Then, 

$$
\mathbf {U} _{1}\mathbf {D} ^{\frac {1}{2}}\mathbf {V} _{1}^{*}=\mathbf {M} \mathbf {V} _{1}\mathbf {D} ^{-{\frac {1}{2}}}\mathbf {D} ^{\frac {1}{2}}\mathbf {V} _{1}^{*}=\mathbf {M} (\mathbf {I} -\mathbf {V} _{2}\mathbf {V} _{2}^{*})=\mathbf {M} -(\mathbf {M} \mathbf {V} _{2})\mathbf {V} _{2}^{*}=\mathbf {M} ,
$$

since $\mathbf {M} \mathbf {V} _{2}=\mathbf {0} .$ This can be also seen as immediate consequence of the fact that $\mathbf {M} \mathbf {V} _{1}\mathbf {V} _{1}^{*}=\mathbf {M}$. This is equivalent to the observation that if $\{{\boldsymbol {v}}_{i}\}_{i=1}^{\ell }$ is the set of eigenvectors of $\mathbf {M} ^{*}\mathbf {M}$ corresponding to non-vanishing eigenvalues $\{\lambda _{i}\}_{i=1}^{\ell }$, then $\{\mathbf {M} {\boldsymbol {v}}_{i}\}_{i=1}^{\ell }$ is a set of orthogonal vectors, and ${\bigl \{}\lambda _{i}^{-1/2}\mathbf {M} {\boldsymbol {v}}_{i}{\bigr \}}{\vphantom {|}}_{i=1}^{\ell }$ is a (generally not complete) set of *orthonormal* vectors. This matches with the matrix formalism used above denoting with $\mathbf {V} _{1}$ the matrix whose columns are $\{{\boldsymbol {v}}_{i}\}_{i=1}^{\ell }$, with $\mathbf {V} _{2}$ the matrix whose columns are the eigenvectors of $\mathbf {M} ^{*}\mathbf {M}$ with vanishing eigenvalue, and $\mathbf {U} _{1}$ the matrix whose columns are the vectors ${\bigl \{}\lambda _{i}^{-1/2}\mathbf {M} {\boldsymbol {v}}_{i}{\bigr \}}{\vphantom {|}}_{i=1}^{\ell }$.

We see that this is almost the desired result, except that $\mathbf {U} _{1}$ and $\mathbf {V} _{1}$ are in general not unitary, since they might not be square. However, we do know that the number of rows of $\mathbf {U} _{1}$ is no smaller than the number of columns, since the dimensions of $\mathbf {D}$ is no greater than $m$ and $n$. Also, since 

$$
\mathbf {U} _{1}^{*}\mathbf {U} _{1}=\mathbf {D} ^{-{\frac {1}{2}}}\mathbf {V} _{1}^{*}\mathbf {M} ^{*}\mathbf {M} \mathbf {V} _{1}\mathbf {D} ^{-{\frac {1}{2}}}=\mathbf {D} ^{-{\frac {1}{2}}}\mathbf {D} \mathbf {D} ^{-{\frac {1}{2}}}=\mathbf {I_{1}} ,
$$

 the columns in $\mathbf {U} _{1}$ are orthonormal and can be extended to an orthonormal basis. This means that we can choose $\mathbf {U} _{2}$ such that $\mathbf {U} ={\begin{bmatrix}\mathbf {U} _{1}&\mathbf {U} _{2}\end{bmatrix}}$ is unitary.

For $\mathbf {V} _{1}$ we already have $\mathbf {V} _{2}$ to make it unitary. Now, define 

$$
\mathbf {\Sigma } ={\begin{bmatrix}{\begin{bmatrix}\mathbf {D} ^{\frac {1}{2}}&0\\0&0\end{bmatrix}}\\0\end{bmatrix}},
$$

where extra zero rows are added **or removed** to make the number of zero rows equal the number of columns of $\mathbf {U} _{2},$ and hence the overall dimensions of $\mathbf {\Sigma }$ equal to $m\times n$. Then 

$$
{\begin{bmatrix}\mathbf {U} _{1}&\mathbf {U} _{2}\end{bmatrix}}{\begin{bmatrix}{\begin{bmatrix}\mathbf {} D^{\frac {1}{2}}&0\\0&0\end{bmatrix}}\\0\end{bmatrix}}{\begin{bmatrix}\mathbf {V} _{1}&\mathbf {V} _{2}\end{bmatrix}}^{*}={\begin{bmatrix}\mathbf {U} _{1}&\mathbf {U} _{2}\end{bmatrix}}{\begin{bmatrix}\mathbf {D} ^{\frac {1}{2}}\mathbf {V} _{1}^{*}\\0\end{bmatrix}}=\mathbf {U} _{1}\mathbf {D} ^{\frac {1}{2}}\mathbf {V} _{1}^{*}=\mathbf {M} ,
$$

 which is the desired result: 

$$
\mathbf {M} =\mathbf {U} \mathbf {\Sigma } \mathbf {V} ^{*}.
$$

Notice the argument could begin with diagonalizing $\mathbf {M} \mathbf {M} ^{*}$ rather than $\mathbf {M} ^{*}\mathbf {M}$ (This shows directly that $\mathbf {M} \mathbf {M} ^{*}$ and $\mathbf {M} ^{*}\mathbf {M}$ have the same non-zero eigenvalues).

### Based on variational characterization

The singular values can also be characterized as the maxima of $\mathbf {u} ^{\mathrm {T} }\mathbf {M} \mathbf {v} ,$ considered as a function of $\mathbf {u}$ and $\mathbf {v} ,$ over particular subspaces. The singular vectors are the values of $\mathbf {u}$ and $\mathbf {v}$ where these maxima are attained.

Let $\mathbf {M}$ denote an $m\times n$ matrix with real entries. Let $S^{k-1}$ be the unit $(k-1)$-sphere in $\mathbb {R} ^{k}$, and define $\sigma (\mathbf {u} ,\mathbf {v} )=\mathbf {u} ^{\operatorname {T} }\mathbf {M} \mathbf {v} ,$ $\mathbf {u} \in S^{m-1},$ $\mathbf {v} \in S^{n-1}.$

Consider the function $\sigma$ restricted to $S^{m-1}\times S^{n-1}.$ Since both $S^{m-1}$ and $S^{n-1}$ are [compact](https://en.wikipedia.org/wiki/Compact_space) sets, their [product](https://en.wikipedia.org/wiki/Product_topology) is also compact. Furthermore, since $\sigma$ is continuous, it attains a largest value for at least one pair of vectors $\mathbf {u}$ in $S^{m-1}$ and $\mathbf {v}$ in $S^{n-1}.$ This largest value is denoted $\sigma _{1}$ and the corresponding vectors are denoted $\mathbf {u} _{1}$ and $\mathbf {v} _{1}.$ Since $\sigma _{1}$ is the largest value of $\sigma (\mathbf {u} ,\mathbf {v} )$ it must be non-negative. If it were negative, changing the sign of either $\mathbf {u} _{1}$ or $\mathbf {v} _{1}$ would make it positive and therefore larger.

**Statement**—$\mathbf {u} _{1}$ and $\mathbf {v} _{1}$ are left and right-singular vectors of $\mathbf {M}$ with corresponding singular value $\sigma _{1}.$

**Proof**

Similar to the eigenvalues case, by assumption the two vectors satisfy the Lagrange multiplier equation: 

$$
\nabla \sigma =\nabla \mathbf {u} ^{\operatorname {T} }\mathbf {M} \mathbf {v} -\lambda _{1}\cdot \nabla \mathbf {u} ^{\operatorname {T} }\mathbf {u} -\lambda _{2}\cdot \nabla \mathbf {v} ^{\operatorname {T} }\mathbf {v}
$$

After some algebra, this becomes 

$$
{\begin{aligned}\mathbf {M} \mathbf {v} _{1}&=2\lambda _{1}\mathbf {u} _{1}+0,\\\mathbf {M} ^{\operatorname {T} }\mathbf {u} _{1}&=0+2\lambda _{2}\mathbf {v} _{1}.\end{aligned}}
$$

Multiplying the first equation from left by $\mathbf {u} _{1}^{\textrm {T}}$ and the second equation from left by $\mathbf {v} _{1}^{\textrm {T}}$ and taking $\|\mathbf {u} \|=\|\mathbf {v} \|=1$ into account gives 

$$
\sigma _{1}=2\lambda _{1}=2\lambda _{2}.
$$

Plugging this into the pair of equations above, we have 

$$
{\begin{aligned}\mathbf {M} \mathbf {v} _{1}&=\sigma _{1}\mathbf {u} _{1},\\\mathbf {M} ^{\operatorname {T} }\mathbf {u} _{1}&=\sigma _{1}\mathbf {v} _{1}.\end{aligned}}
$$

This proves the statement.

More singular vectors and singular values can be found by maximizing $\sigma (\mathbf {u} ,\mathbf {v} )$ over normalized $\mathbf {u}$ and $\mathbf {v}$ which are orthogonal to $\mathbf {u} _{1}$ and $\mathbf {v} _{1},$ respectively.

The passage from real to complex is similar to the eigenvalue case.

## Calculating the SVD

### One-sided Jacobi algorithm

One-sided Jacobi algorithm is an iterative algorithm, where a matrix is iteratively transformed into a matrix with orthogonal columns. The elementary iteration is given as a [Jacobi rotation](https://en.wikipedia.org/wiki/Jacobi_rotation), 

$$
M\leftarrow MJ(p,q,\theta ),
$$

 where the angle $\theta$ of the Jacobi rotation matrix $J(p,q,\theta )$ is chosen such that after the rotation the columns with numbers $p$ and $q$ become orthogonal. The indices $(p,q)$ are swept cyclically, $(p=1\dots m,q=p+1\dots m)$, where $m$ is the number of columns.

After the algorithm has converged, the singular value decomposition $M=USV^{T}$ is recovered as follows: the matrix $V$ is the accumulation of Jacobi rotation matrices, the matrix $U$ is given by [normalising](https://en.wikipedia.org/wiki/Norm_(mathematics) "Norm (mathematics)") the columns of the transformed matrix $M$, and the singular values are given as the norms of the columns of the transformed matrix $M$.

### Two-sided Jacobi algorithm

Two-sided Jacobi SVD algorithm—a generalization of the [Jacobi eigenvalue algorithm](https://en.wikipedia.org/wiki/Jacobi_eigenvalue_algorithm)—is an iterative algorithm where a square matrix is iteratively transformed into a diagonal matrix. If the matrix is not square the [[QR Decomposition]] is performed first and then the algorithm is applied to the $R$ matrix. The elementary iteration zeroes a pair of off-diagonal elements by first applying a [Givens rotation](https://en.wikipedia.org/wiki/Givens_rotation) to symmetrize the pair of elements and then applying a [Jacobi transformation](https://en.wikipedia.org/wiki/Jacobi_transformation) to zero them, 

$$
M\leftarrow J^{T}GMJ
$$

 where $G$ is the Givens rotation matrix with the angle chosen such that the given pair of off-diagonal elements become equal after the rotation, and where $J$ is the Jacobi transformation matrix that zeroes these off-diagonal elements. The iterations proceeds exactly as in the Jacobi eigenvalue algorithm: by cyclic sweeps over all off-diagonal elements.

After the algorithm has converged the resulting diagonal matrix contains the singular values. The matrices $U$ and $V$ are accumulated as follows: 

$$
{\begin{aligned}U&\leftarrow UG^{T}J,\\V&\leftarrow VJ.\end{aligned}}
$$

### Numerical approach

The singular value decomposition can be computed using the following observations:

- The left-singular vectors of $\mathbf {M}$ are a set of [orthonormal](https://en.wikipedia.org/wiki/Orthonormal) [eigenvectors](https://en.wikipedia.org/wiki/Eigenvectors) of $\mathbf {M} \mathbf {M} ^{*}$.
- The right-singular vectors of $\mathbf {M}$ are a set of orthonormal eigenvectors of $\mathbf {M} ^{*}\mathbf {M}$.
- The non-zero singular values of $\mathbf {M}$ (found on the diagonal entries of $\mathbf {\Sigma }$) are the square roots of the non-zero [eigenvalues](https://en.wikipedia.org/wiki/Eigenvalues) of both $\mathbf {M} ^{*}\mathbf {M}$ and $\mathbf {M} \mathbf {M} ^{*}$.

The SVD of a matrix $\mathbf {M}$ is typically computed by a two-step procedure. In the first step, the matrix is reduced to a [bidiagonal matrix](https://en.wikipedia.org/wiki/Bidiagonal_matrix). This takes [order](https://en.wikipedia.org/wiki/Big_O_notation) $O(mn^{2})$ floating-point operations (flop), assuming that $m\geq n.$ The second step is to compute the SVD of the bidiagonal matrix. This step can only be done with an [iterative method](https://en.wikipedia.org/wiki/Iterative_method) (as with [eigenvalue algorithms](https://en.wikipedia.org/wiki/Eigenvalue_algorithm)). However, in practice it suffices to compute the SVD up to a certain precision, like the [machine epsilon](https://en.wikipedia.org/wiki/Machine_epsilon). If this precision is considered constant, then the second step takes $O(n)$ iterations, each costing $O(n)$ flops. Thus, the first step is more expensive, and the overall cost is $O(mn^{2})$ flops.

The first step can be done using [Householder reflections](https://en.wikipedia.org/wiki/Householder_reflection) for a cost of $4mn^{2}-4n^{3}/3$ flops, assuming that only the singular values are needed and not the singular vectors. If $m$ is much larger than $n$ then it is advantageous to first reduce the matrix $\mathbf {M}$ to a triangular matrix with the [[QR Decomposition]] and then use Householder reflections to further reduce the matrix to bidiagonal form; the combined cost is $2mn^{2}+2n^{3}$ flops.

The second step can be done by a variant of the [QR algorithm](https://en.wikipedia.org/wiki/QR_algorithm) for the computation of eigenvalues, which was first described by Golub and Kahan in 1965. The [LAPACK](https://en.wikipedia.org/wiki/LAPACK) subroutine `DBDSQR` implements this iterative method, with some modifications to cover the case where the singular values are very small. Together with a first step using Householder reflections and, if appropriate, QR decomposition, this forms the `DGESVD` routine for the computation of the singular value decomposition.

There is an alternative way that does not explicitly use the eigenvalue decomposition. Usually the singular value problem of a matrix $\mathbf {M}$ is converted into an equivalent symmetric eigenvalue problem such as $\mathbf {M} \mathbf {M} ^{*},$ $\mathbf {M} ^{*}\mathbf {M} ,$ or

$$
{\begin{bmatrix}\mathbf {0} &\mathbf {M} \\\mathbf {M} ^{*}&\mathbf {0} \end{bmatrix}}.
$$

The approaches that use eigenvalue decompositions are based on the [QR algorithm](https://en.wikipedia.org/wiki/QR_algorithm), which is well-developed to be stable and fast. Note that the singular values are real and right- and left- singular vectors are not required to form similarity transformations. One can iteratively alternate between the [[QR Decomposition]] and the [LQ decomposition](https://en.wikipedia.org/wiki/LQ_decomposition) to find the real diagonal [Hermitian matrices](https://en.wikipedia.org/wiki/Hermitian_matrix). The [[QR Decomposition]] gives $\mathbf {M} \Rightarrow \mathbf {Q} \mathbf {R}$ and the [LQ decomposition](https://en.wikipedia.org/wiki/LQ_decomposition) of $\mathbf {R}$ gives $\mathbf {R} \Rightarrow \mathbf {L} \mathbf {P} ^{*}.$ Thus, at every iteration, we have $\mathbf {M} \Rightarrow \mathbf {Q} \mathbf {L} \mathbf {P} ^{*},$ update $\mathbf {M} \Leftarrow \mathbf {L}$ and repeat the orthogonalizations. Eventually,<sup>\[*[clarification needed](https://en.wikipedia.org/wiki/Wikipedia:Please_clarify)*\]</sup> this iteration between [[QR Decomposition]] and [LQ decomposition](https://en.wikipedia.org/wiki/LQ_decomposition) produces left- and right- unitary singular matrices. This approach cannot readily be accelerated, as the QR algorithm can with spectral shifts or deflation. This is because the shift method is not easily defined without using similarity transformations. However, this iterative approach is very simple to implement, so is a good choice when speed does not matter. This method also provides insight into how purely orthogonal/unitary transformations can obtain the SVD.

### Analytic result of 2 × 2 SVD

The singular values of a $2\times 2$ matrix can be found analytically. Let the matrix be $\mathbf {M} =z_{0}\mathbf {I} +z_{1}\sigma _{1}+z_{2}\sigma _{2}+z_{3}\sigma _{3}$

where $z_{i}\in \mathbb {C}$ are complex numbers that parameterize the matrix, $\mathbf {I}$ is the identity matrix, and $\sigma _{i}$ denote the [Pauli matrices](https://en.wikipedia.org/wiki/Pauli_matrices). Then its two singular values are given by

$$
{\begin{aligned}\sigma _{\pm }&={\sqrt {|z_{0}|^{2}+|z_{1}|^{2}+|z_{2}|^{2}+|z_{3}|^{2}\pm {\sqrt {{\bigl (}|z_{0}|^{2}+|z_{1}|^{2}+|z_{2}|^{2}+|z_{3}|^{2}{\bigr )}^{2}-|z_{0}^{2}-z_{1}^{2}-z_{2}^{2}-z_{3}^{2}|^{2}}}}}\\&={\sqrt {|z_{0}|^{2}+|z_{1}|^{2}+|z_{2}|^{2}+|z_{3}|^{2}\pm 2{\sqrt {(\operatorname {Re} z_{0}z_{1}^{*})^{2}+(\operatorname {Re} z_{0}z_{2}^{*})^{2}+(\operatorname {Re} z_{0}z_{3}^{*})^{2}+(\operatorname {Im} z_{1}z_{2}^{*})^{2}+(\operatorname {Im} z_{2}z_{3}^{*})^{2}+(\operatorname {Im} z_{3}z_{1}^{*})^{2}}}}}\end{aligned}}
$$

## Reduced SVDs

![[media/ecbb7884e3d2be3693cc4946afb3a5b5cc151314.png]]
Visualization of Reduced SVD variants. From top to bottom: 1: Full SVD, 2: Thin SVD (remove columns of <strong>U</strong> not corresponding to rows of <strong>V</strong><sup>*</sup>), 3: Compact SVD (remove vanishing singular values and corresponding columns/rows in <strong>U</strong> and <strong>V</strong><sup>*</sup>), 4: Truncated SVD (keep only largest t singular values and corresponding columns/rows in <strong>U</strong> and <strong>V</strong><sup>*</sup>)

In applications it is quite unusual for the full SVD, including a full unitary decomposition of the null-space of the matrix, to be required. Instead, it is often sufficient (as well as faster, and more economical for storage) to compute a reduced version of the SVD. The following can be distinguished for an $m\times n$ matrix $\mathbf {M}$ of rank $r$:

### Thin SVD

The thin, or economy-sized, SVD of a matrix $\mathbf {M}$ is given by

$$
\mathbf {M} =\mathbf {U} _{k}\mathbf {\Sigma } _{k}\mathbf {V} _{k}^{*},
$$

where $k=\min(m,n),$ the matrices $\mathbf {U} _{k}$ and $\mathbf {V} _{k}$ contain only the first $k$ columns of $\mathbf {U}$ and $\mathbf {V} ,$ and $\mathbf {\Sigma } _{k}$ contains only the first $k$ singular values from $\mathbf {\Sigma } .$ The matrix $\mathbf {U} _{k}$ is thus $m\times k,$ $\mathbf {\Sigma } _{k}$ is $k\times k$ diagonal, and $\mathbf {V} _{k}^{*}$ is $k\times n.$

The thin SVD uses significantly less space and computation time if $k\ll \max(m,n).$ The first stage in its calculation will usually be a [[QR Decomposition]] of $\mathbf {M} ,$ which can make for a significantly quicker calculation in this case.

### Compact SVD

The compact SVD of a matrix $\mathbf {M}$ is given by

$$
\mathbf {M} =\mathbf {U} _{r}\mathbf {\Sigma } _{r}\mathbf {V} _{r}^{*}.
$$

Only the $r$ column vectors of $\mathbf {U}$ and $r$ row vectors of $\mathbf {V} ^{*}$ corresponding to the non-zero singular values $\mathbf {\Sigma } _{r}$ are calculated. The remaining vectors of $\mathbf {U}$ and $\mathbf {V} ^{*}$ are not calculated. This is quicker and more economical than the thin SVD if $r\ll \min(m,n).$ The matrix $\mathbf {U} _{r}$ is thus $m\times r,$ $\mathbf {\Sigma } _{r}$ is $r\times r$ diagonal, and $\mathbf {V} _{r}^{*}$ is $r\times n.$

### Truncated SVD

In many applications the number $r$ of the non-zero singular values is large making even the Compact SVD impractical to compute. In such cases, the smallest singular values may need to be truncated to compute only $t\ll r$ non-zero singular values. The truncated SVD is no longer an exact decomposition of the original matrix $\mathbf {M} ,$ but rather provides the optimal [low-rank matrix approximation](#Low-rank_matrix_approximation) ${\tilde {\mathbf {M} }}$ by any matrix of a fixed rank $t$

$$
{\tilde {\mathbf {M} }}=\mathbf {U} _{t}\mathbf {\Sigma } _{t}\mathbf {V} _{t}^{*},
$$

where matrix $\mathbf {U} _{t}$ is $m\times t,$ $\mathbf {\Sigma } _{t}$ is $t\times t$ diagonal, and $\mathbf {V} _{t}^{*}$ is $t\times n.$ Only the $t$ column vectors of $\mathbf {U}$ and $t$ row vectors of $\mathbf {V} ^{*}$ corresponding to the $t$ largest singular values $\mathbf {\Sigma } _{t}$ are calculated. This can be much quicker and more economical than the compact SVD if $t\ll r,$ but requires a completely different toolset of numerical solvers.

In applications that require an approximation to the [Moore–Penrose inverse](https://en.wikipedia.org/wiki/Moore%E2%80%93Penrose_inverse) of the matrix $\mathbf {M} ,$ the smallest singular values of $\mathbf {M}$ are of interest, which are more challenging to compute compared to the largest ones.

Truncated SVD is employed in [latent semantic indexing](https://en.wikipedia.org/wiki/Latent_semantic_indexing).

## Norms

### Ky Fan norms

The sum of the $k$ largest singular values of $\mathbf {M}$ is a [matrix norm](https://en.wikipedia.org/wiki/Matrix_norm), the [Ky Fan](https://en.wikipedia.org/wiki/Ky_Fan) $k$-norm of $\mathbf {M} .$

The first of the Ky Fan norms, the Ky Fan 1-norm, is the same as the [operator norm](https://en.wikipedia.org/wiki/Operator_norm) of $\mathbf {M}$ as a linear operator with respect to the Euclidean norms of $K^{m}$ and $K^{n}.$ In other words, the Ky Fan 1-norm is the operator norm induced by the standard $\ell ^{2}$ Euclidean inner product. For this reason, it is also called the operator 2-norm. One can easily verify the relationship between the Ky Fan 1-norm and singular values. It is true in general, for a bounded operator $\mathbf {M}$ on (possibly infinite-dimensional) Hilbert spaces

$$
\|\mathbf {M} \|=\|\mathbf {M} ^{*}\mathbf {M} \|^{\frac {1}{2}}
$$

But, in the matrix case, $(\mathbf {M} ^{*}\mathbf {M} )^{1/2}$ is a [normal matrix](https://en.wikipedia.org/wiki/Normal_matrix), so $\|\mathbf {M} ^{*}\mathbf {M} \|^{1/2}$ is the largest eigenvalue of $(\mathbf {M} ^{*}\mathbf {M} )^{1/2},$ i.e. the largest singular value of $\mathbf {M} .$

The last of the Ky Fan norms, the sum of all singular values, is the [trace norm](https://en.wikipedia.org/wiki/Trace_class) (also known as the 'nuclear norm'), defined by $\|\mathbf {M} \|=\operatorname {Tr} (\mathbf {M} ^{*}\mathbf {M} )^{1/2}$ (the eigenvalues of $\mathbf {M} ^{*}\mathbf {M}$ are the squares of the singular values).

### Hilbert–Schmidt norm

The singular values are related to another norm on the space of operators. Consider the [Hilbert–Schmidt](https://en.wikipedia.org/wiki/Hilbert%E2%80%93Schmidt_operator) inner product on the $n\times n$ matrices, defined by

$$
\langle \mathbf {M} ,\mathbf {N} \rangle =\operatorname {tr} \left(\mathbf {N} ^{*}\mathbf {M} \right).
$$

So the induced norm is

$$
\|\mathbf {M} \|={\sqrt {\langle \mathbf {M} ,\mathbf {M} \rangle }}={\sqrt {\operatorname {tr} \left(\mathbf {M} ^{*}\mathbf {M} \right)}}.
$$

Since the trace is invariant under unitary equivalence, this shows

$$
\|\mathbf {M} \|={\sqrt {{\vphantom {\bigg |}}\sum _{i}\sigma _{i}^{2}}}
$$

where $\sigma _{i}$ are the singular values of $\mathbf {M} .$ This is called the **[Frobenius norm](https://en.wikipedia.org/wiki/Frobenius_norm)**, **Schatten 2-norm**, or **Hilbert–Schmidt norm** of $\mathbf {M} .$ Direct calculation shows that the Frobenius norm of $\mathbf {M} =(m_{ij})$ coincides with:

$$
{\sqrt {{\vphantom {\bigg |}}\sum _{ij}|m_{ij}|^{2}}}.
$$

In addition, the Frobenius norm and the trace norm (the nuclear norm) are special cases of the [Schatten norm](https://en.wikipedia.org/wiki/Schatten_norm).

## Variations and generalizations

### Scale-invariant SVD

The singular values of a matrix $\mathbf {A}$ are uniquely defined and are invariant with respect to left and/or right unitary transformations of $\mathbf {A} .$ In other words, the singular values of $\mathbf {U} \mathbf {A} \mathbf {V} ,$ for unitary matrices $\mathbf {U}$ and $\mathbf {V} ,$ are equal to the singular values of $\mathbf {A} .$ This is an important property for applications in which it is necessary to preserve Euclidean distances and invariance with respect to rotations.

The Scale-Invariant SVD, or SI-SVD, is analogous to the conventional SVD except that its uniquely-determined singular values are invariant with respect to diagonal transformations of $\mathbf {A} .$ In other words, the singular values of $\mathbf {D} \mathbf {A} \mathbf {E} ,$ for invertible diagonal matrices $\mathbf {D}$ and $\mathbf {E} ,$ are equal to the singular values of $\mathbf {A} .$ This is an important property for applications for which invariance to the choice of units on variables (e.g., metric versus imperial units) is needed.

### Bounded operators on Hilbert spaces

The factorization $\mathbf {M} =\mathbf {U} \mathbf {\Sigma } \mathbf {V} ^{*}$ can be extended to a [bounded operator](https://en.wikipedia.org/wiki/Bounded_operator) $\mathbf {M}$ on a separable Hilbert space $H.$ Namely, for any bounded operator $\mathbf {M} ,$ there exist a [partial isometry](https://en.wikipedia.org/wiki/Partial_isometry) $\mathbf {U} ,$ a unitary $\mathbf {V} ,$ a measure space $(X,\mu ),$ and a non-negative measurable $f$ such that

$$
\mathbf {M} =\mathbf {U} T_{f}\mathbf {V} ^{*}
$$

where $T_{f}$ is the [multiplication by $f$](https://en.wikipedia.org/wiki/Multiplication_operator) on $L^{2}(X,\mu ).$

This can be shown by mimicking the linear algebraic argument for the matrix case above. $\mathbf {V} T_{f}\mathbf {V} ^{*}$ is the unique positive square root of $\mathbf {M} ^{*}\mathbf {M} ,$ as given by the [Borel functional calculus](https://en.wikipedia.org/wiki/Borel_functional_calculus) for [self-adjoint operators](https://en.wikipedia.org/wiki/Self-adjoint_operator). The reason why $\mathbf {U}$ need not be unitary is that, unlike the finite-dimensional case, given an isometry $U_{1}$ with nontrivial kernel, a suitable $U_{2}$ may not be found such that

$$
{\begin{bmatrix}U_{1}\\U_{2}\end{bmatrix}}
$$

is a unitary operator.

As for matrices, the singular value factorization is equivalent to the [polar decomposition](https://en.wikipedia.org/wiki/Polar_decomposition) for operators: we can simply write

$$
\mathbf {M} =\mathbf {U} \mathbf {V} ^{*}\cdot \mathbf {V} T_{f}\mathbf {V} ^{*}
$$

and notice that $\mathbf {U} \mathbf {V} ^{*}$ is still a partial isometry while $\mathbf {V} T_{f}\mathbf {V} ^{*}$ is positive.

### Singular values and compact operators

The notion of singular values and left/right-singular vectors can be extended to [compact operator on Hilbert space](https://en.wikipedia.org/wiki/Compact_operator_on_Hilbert_space) as they have a discrete spectrum. If $T$ is compact, every non-zero $\lambda$ in its spectrum is an eigenvalue. Furthermore, a compact self-adjoint operator can be diagonalized by its eigenvectors. If $\mathbf {M}$ is compact, so is $\mathbf {M} ^{*}\mathbf {M}$. Applying the diagonalization result, the unitary image of its positive square root $T_{f}$ has a set of orthonormal eigenvectors $\{e_{i}\}$ corresponding to strictly positive eigenvalues $\{\sigma _{i}\}$. For any $\psi$ in $H,$

$$
\mathbf {M} \psi =\mathbf {U} T_{f}\mathbf {V} ^{*}\psi =\sum _{i}\left\langle \mathbf {U} T_{f}\mathbf {V} ^{*}\psi ,\mathbf {U} e_{i}\right\rangle \mathbf {U} e_{i}=\sum _{i}\sigma _{i}\left\langle \psi ,\mathbf {V} e_{i}\right\rangle \mathbf {U} e_{i},
$$

where the series converges in the norm topology on $H.$ Notice how this resembles the expression from the finite-dimensional case. $\sigma _{i}$ are called the singular values of $\mathbf {M} .$ $\{\mathbf {U} e_{i}\}$ (resp. $\{\mathbf {V} e_{i}\}$) can be considered the left-singular (resp. right-singular) vectors of $\mathbf {M} .$

Compact operators on a Hilbert space are the closure of [finite-rank operators](https://en.wikipedia.org/wiki/Finite-rank_operator) in the uniform operator topology. The above series expression gives an explicit such representation. An immediate consequence of this is:

**Theorem.** $\mathbf {M}$ is compact if and only if $\mathbf {M} ^{*}\mathbf {M}$ is compact.

## History

The singular value decomposition was originally developed by [differential geometers](https://en.wikipedia.org/wiki/Differential_geometry), who wished to determine whether a real [bilinear form](https://en.wikipedia.org/wiki/Bilinear_form) could be made equal to another by independent orthogonal transformations of the two spaces it acts on. [Eugenio Beltrami](https://en.wikipedia.org/wiki/Eugenio_Beltrami) and [Camille Jordan](https://en.wikipedia.org/wiki/Camille_Jordan) discovered independently, in 1873 and 1874 respectively, that the singular values of the bilinear forms, represented as a matrix, form a [complete set](https://en.wikipedia.org/wiki/Complete_set_of_invariants) of [invariants](https://en.wikipedia.org/wiki/Invariant_(mathematics) "Invariant (mathematics)") for bilinear forms under orthogonal substitutions. [James Joseph Sylvester](https://en.wikipedia.org/wiki/James_Joseph_Sylvester) also arrived at the singular value decomposition for real square matrices in 1889, apparently independently of both Beltrami and Jordan. Sylvester called the singular values the *canonical multipliers* of the matrix $\mathbf {A} .$ The fourth mathematician to discover the singular value decomposition independently is [Autonne](https://en.wikipedia.org/wiki/L%C3%A9on_Autonne) in 1915, who arrived at it via the [polar decomposition](https://en.wikipedia.org/wiki/Polar_decomposition). The first proof of the singular value decomposition for rectangular and complex matrices seems to be by [Carl Eckart](https://en.wikipedia.org/wiki/Carl_Eckart) and [Gale J. Young](https://en.wikipedia.org/wiki/Gale_J._Young) in 1936; they saw it as a generalization of the [principal axis](https://en.wikipedia.org/wiki/Principal_axis_theorem) transformation for [Hermitian matrices](https://en.wikipedia.org/wiki/Hermitian_matrix).

In 1907, [Erhard Schmidt](https://en.wikipedia.org/wiki/Erhard_Schmidt) defined an analog of singular values for [integral operators](https://en.wikipedia.org/wiki/Integral_operator) (which are compact, under some weak technical assumptions); it seems he was unaware of the parallel work on singular values of finite matrices. This theory was further developed by [Émile Picard](https://en.wikipedia.org/wiki/%C3%89mile_Picard) in 1910, who is the first to call the numbers $\sigma _{k}$ *singular values* (or in French, *valeurs singulières*).

Practical methods for computing the SVD date back to [Kogbetliantz](https://en.wikipedia.org/wiki/Ervand_Kogbetliantz) in 1954–1955 and [Hestenes](https://en.wikipedia.org/wiki/Magnus_Hestenes) in 1958, resembling closely the [Jacobi eigenvalue algorithm](https://en.wikipedia.org/wiki/Jacobi_eigenvalue_algorithm), which uses plane rotations or [Givens rotations](https://en.wikipedia.org/wiki/Givens_rotation). However, these were replaced by the method of [Gene Golub](https://en.wikipedia.org/wiki/Gene_H._Golub) and [William Kahan](https://en.wikipedia.org/wiki/William_Kahan) published in 1965, which uses [Householder transformations](https://en.wikipedia.org/wiki/Householder_transformation) or reflections. In 1970, Golub and [Christian Reinsch](https://en.wikipedia.org/wiki/Christian_Reinsch) published a variant of the Golub/Kahan algorithm that is still the one most-used today.

## See also

- [Autoencoder](https://en.wikipedia.org/wiki/Autoencoder)
- [Canonical correlation](https://en.wikipedia.org/wiki/Canonical_correlation)
- [Canonical form](https://en.wikipedia.org/wiki/Canonical_form)
- [Correspondence analysis](https://en.wikipedia.org/wiki/Correspondence_analysis) (CA)
- [Curse of dimensionality](https://en.wikipedia.org/wiki/Curse_of_dimensionality)
- [Digital signal processing](https://en.wikipedia.org/wiki/Digital_signal_processing)
- [Dimensionality reduction](https://en.wikipedia.org/wiki/Dimensionality_reduction)
- [Eigendecomposition of a matrix](https://en.wikipedia.org/wiki/Eigendecomposition_of_a_matrix)
- [Empirical orthogonal functions](https://en.wikipedia.org/wiki/Empirical_orthogonal_functions) (EOFs)
- [Fourier analysis](https://en.wikipedia.org/wiki/Fourier_analysis)
- [Generalized singular value decomposition](https://en.wikipedia.org/wiki/Generalized_singular_value_decomposition)
- [Inequalities about singular values](https://en.wikipedia.org/wiki/Singular_value#Inequalities_about_singular_values)
- [K-SVD](https://en.wikipedia.org/wiki/K-SVD)
- [Latent semantic analysis](https://en.wikipedia.org/wiki/Latent_semantic_analysis)
- [Latent semantic indexing](https://en.wikipedia.org/wiki/Latent_semantic_indexing)
- [Linear least squares](https://en.wikipedia.org/wiki/Linear_least_squares_(mathematics))
- [List of Fourier-related transforms](https://en.wikipedia.org/wiki/List_of_Fourier-related_transforms)
- [Locality-sensitive hashing](https://en.wikipedia.org/wiki/Locality-sensitive_hashing)
- [Low-rank approximation](https://en.wikipedia.org/wiki/Low-rank_approximation)
- [Matrix decomposition](https://en.wikipedia.org/wiki/Matrix_decomposition)
- [Multilinear principal component analysis](https://en.wikipedia.org/wiki/Multilinear_principal_component_analysis) (MPCA)
- [Nearest neighbor search](https://en.wikipedia.org/wiki/Nearest_neighbor_search)
- [Non-linear iterative partial least squares](https://en.wikipedia.org/wiki/Non-linear_iterative_partial_least_squares)
- [Polar decomposition](https://en.wikipedia.org/wiki/Polar_decomposition)
- [[Principal Component Analysis]] (PCA)
- [Schmidt decomposition](https://en.wikipedia.org/wiki/Schmidt_decomposition)
- [Smith normal form](https://en.wikipedia.org/wiki/Smith_normal_form)
- [Singular value](https://en.wikipedia.org/wiki/Singular_value)
- [Time series](https://en.wikipedia.org/wiki/Time_series)
- [Two-dimensional singular-value decomposition](https://en.wikipedia.org/wiki/Two-dimensional_singular-value_decomposition) (2DSVD)
- [von Neumann's trace inequality](https://en.wikipedia.org/wiki/Von_Neumann%27s_trace_inequality)
- [Wavelet compression](https://en.wikipedia.org/wiki/Wavelet_compression)

## Notes

1.  Although, it was later found to have been known to earlier authors; see .
2.  To see this, we just have to notice that $\operatorname {Tr} (\mathbf {V} _{2}^{*}\mathbf {M} ^{*}\mathbf {M} \mathbf {V} _{2})=\|\mathbf {M} \mathbf {V} _{2}\|^{2},$ and remember that $\|A\|=0\Leftrightarrow A=0$.

## Footnotes

1.  Holmes, Mark (2023). *Introduction to Scientific Computing and Data Analysis, 2nd Ed*. Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-031-22429-4](https://en.wikipedia.org/wiki/Special:BookSources/978-3-031-22429-4).
2.  DeAngelis, G. C.; Ohzawa, I.; Freeman, R. D. (October 1995). "Receptive-field dynamics in the central visual pathways". *Trends Neurosci*. **18** (10): 451–8. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/0166-2236(95)94496-R](https://doi.org/10.1016%2F0166-2236%2895%2994496-R). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [8545912](https://pubmed.ncbi.nlm.nih.gov/8545912).
3.  Depireux, D. A.; Simon, J. Z.; Klein, D. J.; Shamma, S. A. (March 2001). "Spectro-temporal response field characterization with dynamic ripples in ferret primary auditory cortex". *J. Neurophysiol*. **85** (3): 1220–34. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1152/jn.2001.85.3.1220](https://doi.org/10.1152%2Fjn.2001.85.3.1220). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [11247991](https://pubmed.ncbi.nlm.nih.gov/11247991).
4.  [The Singular Value Decomposition in Symmetric (Lowdin) Orthogonalization and Data Compression](https://people.wou.edu/~beavers/Talks/Willamette1106.pdf)
5.  , §12.4.
6.  ^   , pp. 535–536.
7.  Sahidullah, Md.; Kinnunen, Tomi (March 2016). ["Local spectral variability features for speaker verification"](https://erepo.uef.fi/handle/123456789/4375). *Digital Signal Processing*. **50**: 1–11. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.dsp.2015.10.011](https://doi.org/10.1016%2Fj.dsp.2015.10.011).
8.  Mademlis, Ioannis; Tefas, Anastasios; Pitas, Ioannis (2018). "Regularized SVD-Based Video Frame Saliency for Unsupervised Activity Video Summarization". *2018 IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP)*. IEEE. pp. 2691–2695. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/ICASSP.2018.8462274](https://doi.org/10.1109%2FICASSP.2018.8462274). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-5386-4658-8](https://en.wikipedia.org/wiki/Special:BookSources/978-1-5386-4658-8).
9.  Alter, O.; Brown, P. O.; Botstein, D. (September 2000). ["Singular Value Decomposition for Genome-Wide Expression Data Processing and Modeling"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC27718). *PNAS*. **97** (18): 10101–10106. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1073/pnas.97.18.10101](https://doi.org/10.1073%2Fpnas.97.18.10101). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [27718](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC27718). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [10963673](https://pubmed.ncbi.nlm.nih.gov/10963673).
10. Alter, O.; Golub, G. H. (November 2004). ["Integrative Analysis of Genome-Scale Data by Using Pseudoinverse Projection Predicts Novel Correlation Between DNA Replication and RNA Transcription"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC534520). *PNAS*. **101** (47): 16577–16582. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1073/pnas.0406767101](https://doi.org/10.1073%2Fpnas.0406767101). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [534520](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC534520). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [15545604](https://pubmed.ncbi.nlm.nih.gov/15545604).
11. Alter, O.; Golub, G. H. (August 2006). ["Singular Value Decomposition of Genome-Scale mRNA Lengths Distribution Reveals Asymmetry in RNA Gel Electrophoresis Band Broadening"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1524674). *PNAS*. **103** (32): 11828–11833. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1073/pnas.0604756103](https://doi.org/10.1073%2Fpnas.0604756103). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [1524674](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1524674). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [16877539](https://pubmed.ncbi.nlm.nih.gov/16877539).
12. Bertagnolli, N. M.; Drake, J. A.; Tennessen, J. M.; Alter, O. (November 2013). ["SVD Identifies Transcript Length Distribution Functions from DNA Microarray Data and Reveals Evolutionary Forces Globally Affecting GBM Metabolism"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3839928). *PLOS ONE*. **8** (11) e78913. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1371/journal.pone.0078913](https://doi.org/10.1371%2Fjournal.pone.0078913). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [3839928](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3839928). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [24282503](https://pubmed.ncbi.nlm.nih.gov/24282503). [Highlight](http://www.alterlab.org/research/highlights/pone.0078913_Highlight.pdf).
13. Edelman, Alan (1992). ["On the distribution of a scaled condition number"](http://math.mit.edu/~edelman/publications/distribution_of_a_scaled.pdf) (PDF). *Math. Comp*. **58** (197): 185–190. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1090/S0025-5718-1992-1106966-2](https://doi.org/10.1090%2FS0025-5718-1992-1106966-2).
14. Shen, Jianhong (Jackie) (2001). ["On the singular values of Gaussian random matrices"](https://doi.org/10.1016%2FS0024-3795%2800%2900322-0). *Linear Alg. Appl*. **326** (1–3): 1–14. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/S0024-3795(00)00322-0](https://doi.org/10.1016%2FS0024-3795%2800%2900322-0).
15. Walton, S.; Hassan, O.; Morgan, K. (2013). ["Reduced order modelling for unsteady fluid flow using proper orthogonal decomposition and radial basis functions"](https://doi.org/10.1016%2Fj.apm.2013.04.025). *Applied Mathematical Modelling*. **37** (20–21): 8930–8945. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.apm.2013.04.025](https://doi.org/10.1016%2Fj.apm.2013.04.025).
16. Setyawati, Y.; Ohme, F.; Khan, S. (2019). "Enhancing gravitational waveform model through dynamic calibration". *Physical Review D*. **99** (2) 024010. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1810.07060](https://arxiv.org/abs/1810.07060). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1103/PhysRevD.99.024010](https://doi.org/10.1103%2FPhysRevD.99.024010).
17. Sarwar, Badrul; Karypis, George; [Konstan, Joseph A.](https://en.wikipedia.org/wiki/Joseph_A._Konstan) & [Riedl, John T.](https://en.wikipedia.org/wiki/John_T._Riedl) (2000). [Application of Dimensionality Reduction in Recommender System – A Case Study](https://apps.dtic.mil/sti/citations/tr/ADA439541) (Technical report 00-043). [University of Minnesota](https://en.wikipedia.org/wiki/University_of_Minnesota). [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[11299/215429](https://hdl.handle.net/11299%2F215429).
18. Bosagh Zadeh, Reza; Carlsson, Gunnar (2013). "Dimension Independent Matrix Square Using MapReduce". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1304.1467](https://arxiv.org/abs/1304.1467) \[[cs.DS](https://arxiv.org/archive/cs.DS)\].
19. Fanaee Tork, Hadi; Gama, João (September 2014). "Eigenspace method for spatiotemporal hotspot detection". *Expert Systems*. **32** (3): 454–464. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1406.3506](https://arxiv.org/abs/1406.3506). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1111/exsy.12088](https://doi.org/10.1111%2Fexsy.12088).
20. Fanaee Tork, Hadi; Gama, João (May 2015). "EigenEvent: An Algorithm for Event Detection from Complex Data Streams in Syndromic Surveillance". *Intelligent Data Analysis*. **19** (3): 597–616. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1406.3496](https://arxiv.org/abs/1406.3496). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3233/IDA-150734](https://doi.org/10.3233%2FIDA-150734).
21. Muralidharan, Vivek; Howell, Kathleen (2023). "Stretching directions in cislunar space: Applications for departures and transfer design". *Astrodynamics*. **7** (2): 153–178. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s42064-022-0147-z](https://doi.org/10.1007%2Fs42064-022-0147-z).
22. Muralidharan, Vivek; Howell, Kathleen (2022). "Leveraging stretching directions for stationkeeping in Earth-Moon halo orbits". *[Advances in Space Research](https://en.wikipedia.org/wiki/Advances_in_Space_Research)*. **69** (1): 620–646. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.asr.2021.10.028](https://doi.org/10.1016%2Fj.asr.2021.10.028).
23. Albers, Jasper; Kurth, Anno; Gutzen, Robin; Morales-Gregorio, Aitor; Denker, Michael; Gruen, Sonja; van Albada, Sacha; Diesmann, Markus (2025). "Assessing the Similarity of Real Matrices with Arbitrary Shape". *PRX Life*. **3** (2) 023005. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2403.17687](https://arxiv.org/abs/2403.17687). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1103/PRXLife.3.023005](https://doi.org/10.1103%2FPRXLife.3.023005).
24. Rijk, P.P.M. de (1989). "A one-sided Jacobi algorithm for computing the singular value decomposition on a vector computer". *SIAM J. Sci. Stat. Comput*. **10** (2): 359–371. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/0910023](https://doi.org/10.1137%2F0910023).
25. ^    , Lecture 31.
26. ^   .
27. , ['DBDSQR' source](http://www.netlib.org/lapack/double/dbdsqr.f).
28. .
29. , ['DGESVD' source](http://www.netlib.org/lapack/double/dgesvd.f).
30. .
31. , §8.6.3.
32. [mathworks.co.kr/matlabcentral/fileexchange/12674-simple-svd](http://www.mathworks.co.kr/matlabcentral/fileexchange/12674-simple-svd)
33. Demmel, James (2000). ["Decompositions"](http://www.netlib.org/utk/people/JackDongarra/etemplates/node43.html). [Templates for the Solution of Algebraic Eigenvalue Problems](https://www.cs.ucdavis.edu/~bai/ET/contents.html). By Bai, Zhaojun; Demmel, James; Dongarra, Jack J.; Ruhe, Axel; van der Vorst, Henk A. Society for Industrial and Applied Mathematics. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/1.9780898719581](https://doi.org/10.1137%2F1.9780898719581). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-89871-471-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-89871-471-5).
34. Chicco, D; Masseroli, M (2015). "Software suite for gene and protein annotation prediction and similarity search". *IEEE/ACM Transactions on Computational Biology and Bioinformatics*. **12** (4): 837–843. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/TCBB.2014.2382127](https://doi.org/10.1109%2FTCBB.2014.2382127). [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[11311/959408](https://hdl.handle.net/11311%2F959408). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [26357324](https://pubmed.ncbi.nlm.nih.gov/26357324).
35. Fan, Ky. (1951). ["Maximum properties and inequalities for the eigenvalues of completely continuous operators"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1063464). *Proceedings of the National Academy of Sciences of the United States of America*. **37** (11): 760–766. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1073/pnas.37.11.760](https://doi.org/10.1073%2Fpnas.37.11.760). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [1063464](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1063464). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [16578416](https://pubmed.ncbi.nlm.nih.gov/16578416).
36. [Uhlmann, Jeffrey](https://en.wikipedia.org/wiki/Jeffrey_Uhlmann) (2018). [A Generalized Matrix Inverse that is Consistent with Respect to Diagonal Transformations](https://web.archive.org/web/20190617095052id_/http://faculty.missouri.edu/uhlmannj/UC-SIMAX-Final.pdf) (PDF). SIAM Journal on Matrix Analysis. Vol. 239. pp. 781–800. Archived from [the original](http://faculty.missouri.edu/uhlmannj/UC-SIMAX-Final.pdf) (PDF) on 17 June 2019.
37. [Eckart, C.](https://en.wikipedia.org/wiki/Carl_Eckart); Young, G. (1936). "The approximation of one matrix by another of lower rank". *[Psychometrika](https://en.wikipedia.org/wiki/Psychometrika)*. **1** (3): 211–8. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/BF02288367](https://doi.org/10.1007%2FBF02288367).
38. [Hestenes, M. R.](https://en.wikipedia.org/wiki/Magnus_Hestenes) (1958). "Inversion of Matrices by Biorthogonalization and Related Results". *Journal of the Society for Industrial and Applied Mathematics*. **6** (1): 51–90. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/0106005](https://doi.org/10.1137%2F0106005). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2098862](https://www.jstor.org/stable/2098862). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0092215](https://mathscinet.ams.org/mathscinet-getitem?mr=0092215).
39. .

## References

- Anderson, E.; Bai, Z.; Bischof, C.; Blackford, S.; Demmel, J.; Dongarra, J.; Du Croz, J.; Greenbaum, A.; Hammarling, S.; McKenney, A.; Sorensen, D. (1999). ["LAPACK Users' Guide"](https://www.netlib.org/lapack/lug/) (Third ed.). Philadelphia: [Society for Industrial and Applied Mathematics](https://en.wikipedia.org/wiki/Society_for_Industrial_and_Applied_Mathematics) – via Netlib.org.
- Banerjee, Sudipto; Roy, Anindya (2014). *Linear Algebra and Matrix Analysis for Statistics*. Texts in Statistical Science (1st ed.). Chapman and Hall/CRC. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4200-9538-8](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4200-9538-8).
- Bisgard, James (2021). *Analysis and Linear Algebra: The Singular Value Decomposition and Applications*. Student Mathematical Library (1st ed.). AMS. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4704-6332-8](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4704-6332-8).
- Chicco, D; Masseroli, M (2015). "Software suite for gene and protein annotation prediction and similarity search". *IEEE/ACM Transactions on Computational Biology and Bioinformatics*. **12** (4): 837–843. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/TCBB.2014.2382127](https://doi.org/10.1109%2FTCBB.2014.2382127). [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[11311/959408](https://hdl.handle.net/11311%2F959408). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [26357324](https://pubmed.ncbi.nlm.nih.gov/26357324).
- [Demmel, James](https://en.wikipedia.org/wiki/James_Demmel); [Kahan, William](https://en.wikipedia.org/wiki/William_Kahan) (1990). "Accurate singular values of bidiagonal matrices". *SIAM Journal on Scientific and Statistical Computing*. **11** (5): 873–912. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.48.3740](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.48.3740). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/0911052](https://doi.org/10.1137%2F0911052).
- [Golub, Gene H.](https://en.wikipedia.org/wiki/Gene_H._Golub); [Kahan, William](https://en.wikipedia.org/wiki/William_Kahan) (1965). "Calculating the singular values and pseudo-inverse of a matrix". *Journal of the Society for Industrial and Applied Mathematics, Series B: Numerical Analysis*. **2** (2): 205–224. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/0702016](https://doi.org/10.1137%2F0702016). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2949777](https://www.jstor.org/stable/2949777).
- [Golub, G. H.](https://en.wikipedia.org/wiki/Gene_H._Golub); [Reinsch, C.](https://en.wikipedia.org/wiki/Christian_Reinsch) (1970). "Singular value decomposition and least squares solutions". *Numerische Mathematik*. **14** (5): 403–420. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/BF02163027](https://doi.org/10.1007%2FBF02163027). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1553974](https://mathscinet.ams.org/mathscinet-getitem?mr=1553974).
- [Golub, Gene H.](https://en.wikipedia.org/wiki/Gene_H._Golub); [Van Loan, Charles F.](https://en.wikipedia.org/wiki/Charles_F._Van_Loan) (1996). *Matrix Computations* (3rd ed.). Johns Hopkins. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8018-5414-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8018-5414-9).
- GSL Team (2007). ["§14.4 Singular Value Decomposition"](https://www.gnu.org/software/gsl/manual/html_node/Singular-Value-Decomposition.html). *GNU Scientific Library. Reference Manual*.
- Halldor, Bjornsson; Venegas, Silvia A. (1997). [A manual for EOF and SVD analyses of climate data](http://brunnur.vedur.is/pub/halldor/TEXT/eofsvd.html) (Report). Montréal, Québec: McGill University. CCGCR Report No. 97-1.
- Hansen, P. C. (1987). "The truncated SVD as a method for regularization". *BIT*. **27** (4): 534–553. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/BF01937276](https://doi.org/10.1007%2FBF01937276).
- Hastie, Trevor; Tibshirani, Robert; Friedman, Jerome (2009). *The Elements of Statistical Learning* (2nd ed.). New York: Springer. pp. 535–536. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-84857-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-84857-0).
- Horn, Roger A.; Johnson, Charles R. (1985). "Section 7.3". *Matrix Analysis*. Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-38632-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-38632-6).
- Horn, Roger A.; Johnson, Charles R. (1991). ["Chapter 3"](https://archive.org/details/topicsinmatrixan0000horn). *Topics in Matrix Analysis*. Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-46713-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-46713-1).
- Press, W. H.; Teukolsky, S. A.; Vetterling, W. T.; Flannery, B. P. (2007). ["Section 2.6"](http://apps.nrbook.com/empanel/index.html?pg=65). *Numerical Recipes: The Art of Scientific Computing* (3rd ed.). New York: Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-88068-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-88068-8).
- Samet, H. (2006). [Foundations of Multidimensional and Metric Data Structures](https://archive.org/details/foundationsofmul00same). Morgan Kaufmann. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-12-369446-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-12-369446-1).
- Strang, G. (1998). "Section 6.7". *Introduction to Linear Algebra* (3rd ed.). Wellesley-Cambridge Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-9614088-5-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-9614088-5-5).
- Stewart, G. W. (1993). "On the Early History of the Singular Value Decomposition". *SIAM Review*. **35** (4): 551–566. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.23.1831](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.23.1831). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/1035134](https://doi.org/10.1137%2F1035134). [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[1903/566](https://hdl.handle.net/1903%2F566). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2132388](https://www.jstor.org/stable/2132388).
- [Trefethen, Lloyd N.](https://en.wikipedia.org/wiki/Lloyd_N._Trefethen); Bau, David III (1997). *Numerical Linear Algebra*. Philadelphia: Society for Industrial and Applied Mathematics. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-89871-361-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-89871-361-9).
- Wall, Michael E.; Rechtsteiner, Andreas; [Rocha, Luis M.](https://en.wikipedia.org/wiki/Luis_M._Rocha) (2003). ["Singular value decomposition and principal component analysis"](http://public.lanl.gov/mewall/kluwer2002.html). In Berrar, D. P.; Dubitzky, W.; Granzow, M. (eds.). *A Practical Approach to Microarray Data Analysis*. Norwell, Massachusetts: Kluwer. pp. 91–109.

## External links

- [Online SVD calculator](http://engineerjs.com/doc/ejs/engine/linalg-1/_svd.html)
