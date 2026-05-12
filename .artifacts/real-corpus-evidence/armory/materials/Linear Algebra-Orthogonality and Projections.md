[[linear-algebra.base]]

> Source: [Projection (linear algebra)](https://en.wikipedia.org/wiki/Projection_(linear_algebra))
> License: Wikipedia content is available under CC BY-SA 4.0.

![[media/ded9a58e1852ad2a92c5620e2acb55a93e574c28.png]]
The transformation <em>P</em> is the orthogonal projection [onto](https://en.wikipedia.org/wiki/Surjective_function) the [line](https://en.wikipedia.org/wiki/Line_(geometry)) <em>m</em>.

In [linear algebra](https://en.wikipedia.org/wiki/Linear_algebra) and [functional analysis](https://en.wikipedia.org/wiki/Functional_analysis), a **projection** is a [[Linear Transformation]] $P$ from a [[Vector Space]] to itself (an [endomorphism](https://en.wikipedia.org/wiki/Endomorphism)) such that $P\circ P=P$. That is, whenever $P$ is applied twice to any vector, it gives the same result as if it were applied once (i.e. $P$ is [idempotent](https://en.wikipedia.org/wiki/Idempotent)). It leaves its [image](https://en.wikipedia.org/wiki/Image_(mathematics) "Image (mathematics)") unchanged. This definition of "projection" formalizes and generalizes the idea of [graphical projection](https://en.wikipedia.org/wiki/Graphical_projection). One can also consider the effect of a projection on a geometrical object by examining the effect of the projection on [points](https://en.wikipedia.org/wiki/Point_(geometry) "Point (geometry)") in the object.

## Definitions

A **projection** on a vector space $V$ is a linear operator $P\colon V\to V$ such that $P^{2}=P$.

When $V$ has an [inner product](https://en.wikipedia.org/wiki/Inner_product) and is [complete](https://en.wikipedia.org/wiki/Complete_metric_space), i.e. when $V$ is a [Hilbert space](https://en.wikipedia.org/wiki/Hilbert_space), the concept of [orthogonality](https://en.wikipedia.org/wiki/Orthogonality) can be used. A projection $P$ on a Hilbert space $V$ is called an **orthogonal projection** if it satisfies $\langle P\mathbf {x} ,\mathbf {y} \rangle =\langle \mathbf {x} ,P\mathbf {y} \rangle$ for all $\mathbf {x} ,\mathbf {y} \in V$. A projection on a Hilbert space that is not orthogonal is called an **oblique projection**.

### Projection matrix

- A [square matrix](https://en.wikipedia.org/wiki/Square_matrix) $P$ is called a **projection matrix** if it is equal to its square, i.e. if $P^{2}=P$.
- A square matrix $P$ is called an **orthogonal projection matrix** if $P^{2}=P=P^{\mathrm {T} }$ for a [real](https://en.wikipedia.org/wiki/Real_number) [matrix](https://en.wikipedia.org/wiki/Matrix_(mathematics) "Matrix (mathematics)"), and respectively $P^{2}=P=P^{*}$ for a [complex](https://en.wikipedia.org/wiki/Complex_number) matrix, where $P^{\mathrm {T} }$ denotes the [transpose](https://en.wikipedia.org/wiki/Transpose) of $P$ and $P^{*}$ denotes the adjoint or [Hermitian transpose](https://en.wikipedia.org/wiki/Hermitian_transpose) of $P$.
- A projection matrix that is not an orthogonal projection matrix is called an **oblique projection matrix**.

The [eigenvalues](https://en.wikipedia.org/wiki/Eigenvalue) of a projection matrix must be 0 or 1.

## Examples

### Orthogonal projection

For example, the function which maps the point $(x,y,z)$ in three-dimensional space $\mathbb {R} ^{3}$ to the point $(x,y,0)$ is an orthogonal projection onto the *xy*-plane. This function is represented by the matrix 

$$
P={\begin{bmatrix}1&0&0\\0&1&0\\0&0&0\end{bmatrix}}.
$$

The action of this matrix on an arbitrary [vector](https://en.wikipedia.org/wiki/Euclidean_vector) is 

$$
P{\begin{bmatrix}x\\y\\z\end{bmatrix}}={\begin{bmatrix}x\\y\\0\end{bmatrix}}.
$$

To see that $P$ is indeed a projection, i.e., $P=P^{2}$, we compute 

$$
P^{2}{\begin{bmatrix}x\\y\\z\end{bmatrix}}=P{\begin{bmatrix}x\\y\\0\end{bmatrix}}={\begin{bmatrix}x\\y\\0\end{bmatrix}}=P{\begin{bmatrix}x\\y\\z\end{bmatrix}}.
$$

Observing that $P^{\mathrm {T} }=P$ shows that the projection is an orthogonal projection.

### Oblique projection

A simple example of a non-orthogonal (oblique) projection is 

$$
P={\begin{bmatrix}0&0\\\alpha &1\end{bmatrix}}.
$$

Via [[Matrix Multiplication]], one sees that 

$$
P^{2}={\begin{bmatrix}0&0\\\alpha &1\end{bmatrix}}{\begin{bmatrix}0&0\\\alpha &1\end{bmatrix}}={\begin{bmatrix}0&0\\\alpha &1\end{bmatrix}}=P.
$$

 showing that $P$ is indeed a projection.

The projection $P$ is orthogonal [if and only if](https://en.wikipedia.org/wiki/If_and_only_if) $\alpha =0$ because only then $P^{\mathrm {T} }=P.$

## Properties and classification

![[media/76071232b027a8be37252dbbf8240b20fcd91174.png]]
The transformation <em>T</em> is the projection along <em>k</em> onto <em>m</em>. The range of <em>T</em> is <em>m</em> and the kernel is <em>k</em>.

### Idempotence

By definition, a projection $P$ is [idempotent](https://en.wikipedia.org/wiki/Idempotent) (i.e. $P^{2}=P$).

### Open map

Every projection is an [open map](https://en.wikipedia.org/wiki/Open_map) onto its image, meaning that it maps each [open set](https://en.wikipedia.org/wiki/Open_set) in the [domain](https://en.wikipedia.org/wiki/Domain_of_a_function) to an open set in the [subspace topology](https://en.wikipedia.org/wiki/Subspace_topology) of the [image](https://en.wikipedia.org/wiki/Image_(mathematics) "Image (mathematics)").<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup> That is, for any vector $\mathbf {x}$ and any ball $B_{\mathbf {x} }$ (with positive radius) centered on $\mathbf {x}$, there exists a ball $B_{P\mathbf {x} }$ (with positive radius) centered on $P\mathbf {x}$ that is wholly contained in the image $P(B_{\mathbf {x} })$.

### Complementarity of image and kernel

Let $W$ be a finite-dimensional vector space and $P$ be a projection on $W$. Suppose the [subspaces](https://en.wikipedia.org/wiki/Linear_subspace) $U$ and $V$ are the [image](https://en.wikipedia.org/wiki/Image_(mathematics) "Image (mathematics)") and [kernel](https://en.wikipedia.org/wiki/Kernel_(linear_algebra) "Kernel (linear algebra)") of $P$ respectively. Then $P$ has the following properties:

1.  $P$ is the [identity operator](https://en.wikipedia.org/wiki/Identity_operator) $I$ on $U$: 

$$
\forall \mathbf {x} \in U:P\mathbf {x} =\mathbf {x} .
$$

2.  We have a [direct sum](https://en.wikipedia.org/wiki/Direct_sum_of_vector_spaces) $W=U\oplus V$. Every vector $\mathbf {x} \in W$ may be decomposed uniquely as $\mathbf {x} =\mathbf {u} +\mathbf {v}$ with $\mathbf {u} =P\mathbf {x}$ and $\mathbf {v} =\mathbf {x} -P\mathbf {x} =\left(I-P\right)\mathbf {x}$, and where $\mathbf {u} \in U,\mathbf {v} \in V.$

The image and kernel of a projection are *complementary*, as are $P$ and $Q=I-P$. The operator $Q$ is also a projection as the image and kernel of $P$ become the kernel and image of $Q$ and vice versa. We say $P$ is a projection along $V$ onto $U$ (kernel/image) and $Q$ is a projection along $U$ onto $V$.

### Spectrum

In infinite-dimensional vector spaces, the [spectrum](https://en.wikipedia.org/wiki/Spectrum_(functional_analysis) "Spectrum (functional analysis)") of a projection is contained in $\{0,1\}$ as 

$$
(\lambda I-P)^{-1}={\frac {1}{\lambda }}I+{\frac {1}{\lambda (\lambda -1)}}P.
$$

 Only 0 or 1 can be an [eigenvalue](https://en.wikipedia.org/wiki/Eigenvalue) of a projection. This implies that an orthogonal projection $P$ is always a [positive semi-definite matrix](https://en.wikipedia.org/wiki/Positive_semi-definite_matrix). In general, the corresponding [eigenspaces](https://en.wikipedia.org/wiki/Eigenspace) are (respectively) the kernel and range of the projection. Decomposition of a vector space into direct sums is not unique. Therefore, given a subspace $V$, there may be many projections whose range (or kernel) is $V$.

If a projection is nontrivial it has [minimal polynomial](https://en.wikipedia.org/wiki/Minimal_polynomial_(linear_algebra) "Minimal polynomial (linear algebra)") $x^{2}-x=x(x-1)$, which factors into distinct linear factors, and thus $P$ is [diagonalizable](https://en.wikipedia.org/wiki/Diagonalizable).

### Product of projections

The product of projections is not in general a projection, even if they are orthogonal. If two projections [commute](https://en.wikipedia.org/wiki/Commuting_matrices) then their product is a projection, but the [converse](https://en.wikipedia.org/wiki/Converse_(logic) "Converse (logic)") is false: the product of two non-commuting projections may or may not be a projection.

If two orthogonal projections commute then their product is an orthogonal projection. If the product of two orthogonal projections is an orthogonal projection, then the two orthogonal projections commute (more generally: two self-adjoint [endomorphisms](https://en.wikipedia.org/wiki/Endomorphism) commute if and only if their product is self-adjoint).

### Orthogonal projections

When the vector space $W$ has an [inner product](https://en.wikipedia.org/wiki/Inner_product) and is complete (is a [Hilbert space](https://en.wikipedia.org/wiki/Hilbert_space)) the concept of [orthogonality](https://en.wikipedia.org/wiki/Orthogonality) can be used. An **orthogonal projection** is a projection for which the range $U$ and the kernel $V$ are [orthogonal subspaces](https://en.wikipedia.org/wiki/Orthogonality). Thus, for every $\mathbf {x}$ and $\mathbf {y}$ in $W$, $\langle P\mathbf {x} ,(\mathbf {y} -P\mathbf {y} )\rangle =\langle (\mathbf {x} -P\mathbf {x} ),P\mathbf {y} \rangle =0$. Equivalently: 

$$
\langle \mathbf {x} ,P\mathbf {y} \rangle =\langle P\mathbf {x} ,P\mathbf {y} \rangle =\langle P\mathbf {x} ,\mathbf {y} \rangle .
$$

A projection is orthogonal if and only if it is [self-adjoint](https://en.wikipedia.org/wiki/Self-adjoint_operator). Using the self-adjoint and idempotent properties of $P$, for any $\mathbf {x}$ and $\mathbf {y}$ in $W$ we have $P\mathbf {x} \in U$, $\mathbf {y} -P\mathbf {y} \in V$, and 

$$
\langle P\mathbf {x} ,\mathbf {y} -P\mathbf {y} \rangle =\langle \mathbf {x} ,\left(P-P^{2}\right)\mathbf {y} \rangle =0
$$

 where $\langle \cdot ,\cdot \rangle$ is the inner product associated with $W$. Therefore, $P$ and $I-P$ are orthogonal projections. The other direction, namely that if $P$ is orthogonal then it is self-adjoint, follows from the implication from $\langle (\mathbf {x} -P\mathbf {x} ),P\mathbf {y} \rangle =\langle P\mathbf {x} ,(\mathbf {y} -P\mathbf {y} )\rangle =0$ to 

$$
\langle \mathbf {x} ,P\mathbf {y} \rangle =\langle P\mathbf {x} ,P\mathbf {y} \rangle =\langle P\mathbf {x} ,\mathbf {y} \rangle =\langle \mathbf {x} ,P^{*}\mathbf {y} \rangle
$$

 for every $x$ and $y$ in $W$; thus $P=P^{*}$.

The existence of an orthogonal projection onto a closed subspace follows from the [Hilbert projection theorem](https://en.wikipedia.org/wiki/Hilbert_projection_theorem).

#### Properties and special cases

An orthogonal projection is a [bounded operator](https://en.wikipedia.org/wiki/Bounded_operator). This is because for every $\mathbf {v}$ in the vector space we have, by the [Cauchy–Schwarz inequality](https://en.wikipedia.org/wiki/Cauchy%E2%80%93Schwarz_inequality): 

$$
\left\|P\mathbf {v} \right\|^{2}=\langle P\mathbf {v} ,P\mathbf {v} \rangle =\langle P\mathbf {v} ,\mathbf {v} \rangle \leq \left\|P\mathbf {v} \right\|\cdot \left\|\mathbf {v} \right\|
$$

 Thus $\left\|P\mathbf {v} \right\|\leq \left\|\mathbf {v} \right\|$.

For finite-dimensional complex or real vector spaces, the [standard inner product](https://en.wikipedia.org/wiki/Standard_inner_product) can be substituted for $\langle \cdot ,\cdot \rangle$.

##### Formulas

A simple case occurs when the orthogonal projection is onto a line. If $\mathbf {u}$ is a [unit vector](https://en.wikipedia.org/wiki/Unit_vector) on the line, then the projection is given by the [outer product](https://en.wikipedia.org/wiki/Outer_product) 

$$
P_{\mathbf {u} }=\mathbf {u} \mathbf {u} ^{\mathsf {T}}.
$$

 (If $\mathbf {u}$ is complex-valued, the transpose in the above equation is replaced by a Hermitian transpose). This operator leaves **u** invariant, and it annihilates all vectors orthogonal to $\mathbf {u}$, proving that it is indeed the orthogonal projection onto the line containing **u**. A simple way to see this is to consider an arbitrary vector $\mathbf {x}$ as the sum of a component on the line (i.e. the projected vector we seek) and another perpendicular to it, $\mathbf {x} =\mathbf {x} _{\parallel }+\mathbf {x} _{\perp }$. Applying projection, we get 

$$
P_{\mathbf {u} }\mathbf {x} =\mathbf {u} \mathbf {u} ^{\mathsf {T}}\mathbf {x} _{\parallel }+\mathbf {u} \mathbf {u} ^{\mathsf {T}}\mathbf {x} _{\perp }=\mathbf {u} \left(\operatorname {sgn} \left(\mathbf {u} ^{\mathsf {T}}\mathbf {x} _{\parallel }\right)\left\|\mathbf {x} _{\parallel }\right\|\right)+\mathbf {u} \cdot \mathbf {0} =\mathbf {x} _{\parallel }
$$

 by the properties of the [dot product](https://en.wikipedia.org/wiki/Dot_product) of parallel and perpendicular vectors.

This formula can be generalized to orthogonal projections on a subspace of arbitrary [dimension](https://en.wikipedia.org/wiki/Dimension_(vector_space) "Dimension (vector space)"). Let $\mathbf {u} _{1},\ldots ,\mathbf {u} _{k}$ be an [orthonormal basis](https://en.wikipedia.org/wiki/Orthonormal_basis) of the subspace $U$, with the assumption that the integer $k\geq 1$, and let $A$ denote the $n\times k$ matrix whose columns are $\mathbf {u} _{1},\ldots ,\mathbf {u} _{k}$, i.e., $A={\begin{bmatrix}\mathbf {u} _{1}&\cdots &\mathbf {u} _{k}\end{bmatrix}}$. Then the projection is given by: 

$$
P_{A}=AA^{\mathsf {T}}
$$

 which can be rewritten as 

$$
P_{A}=\sum _{i}\langle \mathbf {u} _{i},\cdot \rangle \mathbf {u} _{i}.
$$

The matrix $A^{\mathsf {T}}$ is the [partial isometry](https://en.wikipedia.org/wiki/Partial_isometry) that vanishes on the [orthogonal complement](https://en.wikipedia.org/wiki/Orthogonal_complement) of $U$, and $A$ is the isometry that embeds $U$ into the underlying vector space. The range of $P_{A}$ is therefore the *final space* of $A$. It is also clear that $AA^{\mathsf {T}}$ is the identity operator on $U$.

The orthonormality condition can also be dropped. If $\mathbf {u} _{1},\ldots ,\mathbf {u} _{k}$ is a (not necessarily orthonormal) [basis](https://en.wikipedia.org/wiki/Basis_(linear_algebra) "Basis (linear algebra)") with $k\geq 1$, and $A$ is the matrix with these vectors as columns, then the projection is: 

$$
P_{A}=A\left(A^{\mathsf {T}}A\right)^{-1}A^{\mathsf {T}}.
$$

The matrix $A$ still embeds $U$ into the underlying vector space but is no longer an isometry in general. The matrix $\left(A^{\mathsf {T}}A\right)^{-1}$ is a "normalizing factor" that recovers the norm. For example, the [rank](https://en.wikipedia.org/wiki/Rank_of_a_linear_operator)-1 operator $\mathbf {u} \mathbf {u} ^{\mathsf {T}}$ is not a projection if $\left\|\mathbf {u} \right\|\neq 1.$ After dividing by $\mathbf {u} ^{\mathsf {T}}\mathbf {u} =\left\|\mathbf {u} \right\|^{2},$ we obtain the projection $\mathbf {u} \left(\mathbf {u} ^{\mathsf {T}}\mathbf {u} \right)^{-1}\mathbf {u} ^{\mathsf {T}}$ onto the subspace spanned by $u$.

In the general case, we can have an arbitrary [positive definite](https://en.wikipedia.org/wiki/Positive_definite) matrix $D$ defining an inner product $\langle x,y\rangle _{D}=y^{\dagger }Dx$, and the projection $P_{A}$ is given by $P_{A}x=\operatorname {argmin} _{y\in \operatorname {range} (A)}\left\|x-y\right\|_{D}^{2}$. Then 

$$
P_{A}=A\left(A^{\mathsf {T}}DA\right)^{-1}A^{\mathsf {T}}D.
$$

When the range space of the projection is generated by a [frame](https://en.wikipedia.org/wiki/Frame_of_a_vector_space) (i.e. the number of generators is greater than its dimension), the formula for the projection takes the form: $P_{A}=AA^{+}$. Here $A^{+}$ stands for the [[Moore-Penrose Pseudoinverse|Moore–Penrose pseudoinverse]]. This is just one of many ways to construct the projection operator.

If ${\begin{bmatrix}A&B\end{bmatrix}}$ is a non-singular matrix and $A^{\mathsf {T}}B=0$ (i.e., $B$ is the [null space](https://en.wikipedia.org/wiki/Null_space) matrix of $A$), the following holds: 

$$
{\begin{aligned}I&={\begin{bmatrix}A&B\end{bmatrix}}{\begin{bmatrix}A&B\end{bmatrix}}^{-1}{\begin{bmatrix}A^{\mathsf {T}}\\B^{\mathsf {T}}\end{bmatrix}}^{-1}{\begin{bmatrix}A^{\mathsf {T}}\\B^{\mathsf {T}}\end{bmatrix}}\\&={\begin{bmatrix}A&B\end{bmatrix}}\left({\begin{bmatrix}A^{\mathsf {T}}\\B^{\mathsf {T}}\end{bmatrix}}{\begin{bmatrix}A&B\end{bmatrix}}\right)^{-1}{\begin{bmatrix}A^{\mathsf {T}}\\B^{\mathsf {T}}\end{bmatrix}}\\&={\begin{bmatrix}A&B\end{bmatrix}}{\begin{bmatrix}A^{\mathsf {T}}A&O\\O&B^{\mathsf {T}}B\end{bmatrix}}^{-1}{\begin{bmatrix}A^{\mathsf {T}}\\B^{\mathsf {T}}\end{bmatrix}}\\[4pt]&=A\left(A^{\mathsf {T}}A\right)^{-1}A^{\mathsf {T}}+B\left(B^{\mathsf {T}}B\right)^{-1}B^{\mathsf {T}}\end{aligned}}
$$

If the orthogonal condition is enhanced to $A^{\mathsf {T}}WB=A^{\mathsf {T}}W^{\mathsf {T}}B=0$ with $W$ non-singular, the following holds: 

$$
I={\begin{bmatrix}A&B\end{bmatrix}}{\begin{bmatrix}\left(A^{\mathsf {T}}WA\right)^{-1}A^{\mathsf {T}}\\\left(B^{\mathsf {T}}WB\right)^{-1}B^{\mathsf {T}}\end{bmatrix}}W.
$$

All these formulas also hold for complex inner product spaces, provided that the [conjugate transpose](https://en.wikipedia.org/wiki/Conjugate_transpose) is used instead of the transpose. Further details on sums of projectors can be found in Banerjee and Roy (2014). Also see Banerjee (2004) for application of sums of projectors in basic [spherical trigonometry](https://en.wikipedia.org/wiki/Spherical_trigonometry).

### Oblique projections

The term *oblique projections* is sometimes used to refer to non-orthogonal projections. These projections are also used to represent spatial figures in two-dimensional drawings (see [oblique projection](https://en.wikipedia.org/wiki/Oblique_projection)), though not as frequently as orthogonal projections. Whereas calculating the fitted value of an [ordinary least squares](https://en.wikipedia.org/wiki/Ordinary_least_squares) regression requires an orthogonal projection, calculating the fitted value of an [instrumental variables regression](https://en.wikipedia.org/wiki/Instrumental_variable) requires an oblique projection.

A projection is defined by its kernel and the basis vectors used to characterize its range (which is a complement of the kernel). When these basis vectors are orthogonal to the kernel, then the projection is an orthogonal projection. When these basis vectors are not orthogonal to the kernel, the projection is an oblique projection, or just a projection.

#### A matrix representation formula for a nonzero projection operator

Let $P\colon V\to V$ be a linear operator such that $P^{2}=P$ and assume that $P$ is not the zero operator. Let the vectors $\mathbf {u} _{1},\ldots ,\mathbf {u} _{k}$ form a basis for the range of $P$, and assemble these vectors in the $n\times k$ matrix $A$. Then $k\geq 1$, otherwise $k=0$ and $P$ is the zero operator. The range and the kernel are complementary spaces, so the kernel has dimension $n-k$. It follows that the [orthogonal complement](https://en.wikipedia.org/wiki/Orthogonal_complement) of the kernel has dimension $k$. Let $\mathbf {v} _{1},\ldots ,\mathbf {v} _{k}$ form a basis for the orthogonal complement of the kernel of the projection, and assemble these vectors in the matrix $B$. Then the projection $P$ (with the condition $k\geq 1$) is given by 

$$
P=A\left(B^{\mathsf {T}}A\right)^{-1}B^{\mathsf {T}}.
$$

This expression generalizes the formula for orthogonal projections given above. A standard proof of this expression is the following. For any vector $\mathbf {x}$ in the vector space $V$, we can decompose $\mathbf {x} =\mathbf {x} _{1}+\mathbf {x} _{2}$, where vector $\mathbf {x} _{1}=P(\mathbf {x} )$ is in the image of $P$, and vector $\mathbf {x} _{2}=\mathbf {x} -P(\mathbf {x} ).$ So $P(\mathbf {x} _{2})=P(\mathbf {x} )-P^{2}(\mathbf {x} )=\mathbf {0}$, and then $\mathbf {x} _{2}$ is in the kernel of $P$, which is the null space of $A.$ In other words, the vector $\mathbf {x} _{1}$ is in the column space of $A,$ so $\mathbf {x} _{1}=A\mathbf {w}$ for some $k$ dimension vector $\mathbf {w}$ and the vector $\mathbf {x} _{2}$ satisfies $B^{\mathsf {T}}\mathbf {x} _{2}=\mathbf {0}$ by the construction of $B$. Put these conditions together, and we find a vector $\mathbf {w}$ so that $B^{\mathsf {T}}(\mathbf {x} -A\mathbf {w} )=\mathbf {0}$. Since matrices $A$ and $B$ are of full rank $k$ by their construction, the $k\times k$-matrix $B^{\mathsf {T}}A$ is invertible. So the equation $B^{\mathsf {T}}(\mathbf {x} -A\mathbf {w} )=\mathbf {0}$ gives the vector $\mathbf {w} =(B^{\mathsf {T}}A)^{-1}B^{\mathsf {T}}\mathbf {x} .$ In this way, $P\mathbf {x} =\mathbf {x} _{1}=A\mathbf {w} =A(B^{\mathsf {T}}A)^{-1}B^{\mathsf {T}}\mathbf {x}$ for any vector $\mathbf {x} \in V$ and hence $P=A(B^{\mathsf {T}}A)^{-1}B^{\mathsf {T}}$.

In the case that $P$ is an orthogonal projection, we can take $A=B$, and it follows that $P=A\left(A^{\mathsf {T}}A\right)^{-1}A^{\mathsf {T}}$. By using this formula, one can easily check that $P=P^{\mathsf {T}}$. In general, if the vector space is over complex number field, one then uses the [Hermitian transpose](https://en.wikipedia.org/wiki/Hermitian_transpose) $A^{*}$ and has the formula $P=A\left(A^{*}A\right)^{-1}A^{*}$. Recall that one can express the [Moore–Penrose inverse](https://en.wikipedia.org/wiki/Moore%E2%80%93Penrose_inverse) of the matrix $A$ by $A^{+}=(A^{*}A)^{-1}A^{*}$ since $A$ has full column rank, so $P=AA^{+}$.

#### Singular values

$I-P$ is also an oblique projection. The singular values of $P$ and $I-P$ can be computed by an [orthonormal basis](https://en.wikipedia.org/wiki/Orthonormal_basis) of $A$. Let $Q_{A}$ be an orthonormal basis of $A$ and let $Q_{A}^{\perp }$ be the [orthogonal complement](https://en.wikipedia.org/wiki/Orthogonal_complement) of $Q_{A}$. Denote the singular values of the matrix $Q_{A}^{T}A(B^{T}A)^{-1}B^{T}Q_{A}^{\perp }$ by the positive values $\gamma _{1}\geq \gamma _{2}\geq \ldots \geq \gamma _{k}$. With this, the singular values for $P$ are: 

$$
\sigma _{i}={\begin{cases}{\sqrt {1+\gamma _{i}^{2}}}&1\leq i\leq k\\0&{\text{otherwise}}\end{cases}}
$$

 and the singular values for $I-P$ are 

$$
\sigma _{i}={\begin{cases}{\sqrt {1+\gamma _{i}^{2}}}&1\leq i\leq k\\1&k+1\leq i\leq n-k\\0&{\text{otherwise}}\end{cases}}
$$

 This implies that the largest singular values of $P$ and $I-P$ are equal, and thus that the [matrix norm](https://en.wikipedia.org/wiki/Matrix_norm) of the oblique projections are the same. However, the [[Condition Number]] satisfies the relation $\kappa (I-P)={\frac {\sigma _{1}}{1}}\geq {\frac {\sigma _{1}}{\sigma _{k}}}=\kappa (P)$, and is therefore not necessarily equal.

### Finding projection with an inner product

Let $V$ be a vector space (in this case a plane) spanned by orthogonal vectors $\mathbf {u} _{1},\mathbf {u} _{2},\dots ,\mathbf {u} _{p}$. Let $y$ be a vector. One can define a projection of $\mathbf {y}$ onto $V$ as 

$$
\operatorname {proj} _{V}\mathbf {y} ={\frac {\mathbf {y} \cdot \mathbf {u} ^{i}}{\mathbf {u} ^{i}\cdot \mathbf {u} ^{i}}}\mathbf {u} ^{i}
$$

 where repeated indices are summed over ([Einstein sum notation](https://en.wikipedia.org/wiki/Einstein_notation)). The vector $\mathbf {y}$ can be written as an orthogonal sum such that $\mathbf {y} =\operatorname {proj} _{V}\mathbf {y} +\mathbf {z}$. $\operatorname {proj} _{V}\mathbf {y}$ is sometimes denoted as ${\hat {\mathbf {y} }}$. There is a theorem in linear algebra that states that this $\mathbf {z}$ is the smallest distance (the *[orthogonal distance](https://en.wikipedia.org/wiki/Orthogonal_distance)*) from $\mathbf {y}$ to $V$ and is commonly used in areas such as [machine learning](https://en.wikipedia.org/wiki/Machine_learning).

![[media/0219b2ee7948760c1800fb1e12ac2efce916ea56.png]]
<em>y</em> is being projected onto the vector space <em>V</em>.

## Canonical forms

Any projection $P=P^{2}$ on a vector space of dimension $d$ over a [field](https://en.wikipedia.org/wiki/Field_(mathematics) "Field (mathematics)") is a [diagonalizable matrix](https://en.wikipedia.org/wiki/Diagonalizable_matrix), since its [minimal polynomial](https://en.wikipedia.org/wiki/Minimal_polynomial_(linear_algebra) "Minimal polynomial (linear algebra)") divides $x^{2}-x$, which splits into distinct linear factors. Thus there exists a basis in which $P$ has the form

$P=I_{r}\oplus 0_{d-r}$

where $r$ is the [rank](https://en.wikipedia.org/wiki/Rank_of_a_linear_transformation) of $P$. Here $I_{r}$ is the [identity matrix](https://en.wikipedia.org/wiki/Identity_matrix) of size $r$, $0_{d-r}$ is the [zero matrix](https://en.wikipedia.org/wiki/Zero_matrix) of size $d-r$, and $\oplus$ is the [direct sum](https://en.wikipedia.org/wiki/Matrix_addition#Direct_sum) operator. If the vector space is complex and equipped with an [inner product](https://en.wikipedia.org/wiki/Inner_product), then there is an *orthonormal* basis in which the matrix of *P* is

$P={\begin{bmatrix}1&\sigma _{1}\\0&0\end{bmatrix}}\oplus \cdots \oplus {\begin{bmatrix}1&\sigma _{k}\\0&0\end{bmatrix}}\oplus I_{m}\oplus 0_{s}.$

where $\sigma _{1}\geq \sigma _{2}\geq \dots \geq \sigma _{k}>0$. The [integers](https://en.wikipedia.org/wiki/Integer) $k,s,m$ and the real numbers $\sigma _{i}$ are uniquely determined. $2k+s+m=d$. The factor $I_{m}\oplus 0_{s}$ corresponds to the maximal invariant subspace on which $P$ acts as an *orthogonal* projection (so that *P* itself is orthogonal if and only if $k=0$) and the $\sigma _{i}$-blocks correspond to the *oblique* components.

## Projections on normed vector spaces

When the underlying vector space $X$ is a (not necessarily finite-dimensional) [normed vector space](https://en.wikipedia.org/wiki/Normed_vector_space), analytic questions, irrelevant in the finite-dimensional case, need to be considered. Assume now $X$ is a [Banach space](https://en.wikipedia.org/wiki/Banach_space).

Many of the algebraic results discussed above survive the passage to this context. A given direct sum decomposition of $X$ into complementary subspaces still specifies a projection, and vice versa. If $X$ is the direct sum $X=U\oplus V$, then the operator defined by $P(u+v)=u$ is still a projection with range $U$ and kernel $V$. It is also clear that $P^{2}=P$. Conversely, if $P$ is projection on $X$, i.e. $P^{2}=P$, then it is easily verified that $(1-P)^{2}=(1-P)$. In other words, $1-P$ is also a projection. The relation $P^{2}=P$ implies $1=P+(1-P)$ and $X$ is the direct sum $\operatorname {rg} (P)\oplus \operatorname {rg} (1-P)$.

However, in contrast to the finite-dimensional case, projections need not be [continuous](https://en.wikipedia.org/wiki/Bounded_linear_operator) in general. If a subspace $U$ of $X$ is not closed in the norm topology, then the projection onto $U$ is not continuous. In other words, the range of a continuous projection $P$ must be a closed subspace. Furthermore, the kernel of a continuous projection (in fact, a continuous linear operator in general) is closed. Thus a *continuous* projection $P$ gives a decomposition of $X$ into two complementary *closed* subspaces: $X=\operatorname {rg} (P)\oplus \ker(P)=\ker(1-P)\oplus \ker(P)$.

The converse holds also, with an additional assumption. Suppose $U$ is a closed subspace of $X$. If there exists a closed subspace $V$ such that *X* = *U* ⊕ *V*, then the projection $P$ with range $U$ and kernel $V$ is continuous. This follows from the [closed graph theorem](https://en.wikipedia.org/wiki/Closed_graph_theorem). Suppose *x<sub>n</sub>* → *x* and *Px<sub>n</sub>* → *y*. One needs to show that $Px=y$. Since $U$ is closed and {*Px<sub>n</sub>*} ⊂ *U*, *y* lies in $U$, i.e. *Py* = *y*. Also, *x<sub>n</sub>* − *Px<sub>n</sub>* = (*I* − *P*)*x<sub>n</sub>* → *x* − *y*. Because $V$ is closed and {(*I* − *P*)*x<sub>n</sub>*} ⊂ *V*, we have $x-y\in V$, i.e. $P(x-y)=Px-Py=Px-y=0$, which proves the claim.

The above argument makes use of the assumption that both $U$ and $V$ are closed. In general, given a closed subspace $U$, there need not exist a complementary closed subspace $V$, although for [Hilbert spaces](https://en.wikipedia.org/wiki/Hilbert_space) this can always be done by taking the [orthogonal complement](https://en.wikipedia.org/wiki/Orthogonal_complement). For Banach spaces, a one-dimensional subspace always has a closed complementary subspace. This is an immediate consequence of [Hahn–Banach theorem](https://en.wikipedia.org/wiki/Hahn%E2%80%93Banach_theorem). Let $U$ be the linear span of $u$. By Hahn–Banach, there exists a bounded [linear functional](https://en.wikipedia.org/wiki/Linear_functional) $\varphi$ such that *φ*(*u*) = 1. The operator $P(x)=\varphi (x)u$ satisfies $P^{2}=P$, i.e. it is a projection. Boundedness of $\varphi$ implies continuity of $P$ and therefore $\ker(P)=\operatorname {rg} (I-P)$ is a closed complementary subspace of $U$.

## Applications and further considerations

Projections (orthogonal and otherwise) play a major role in [algorithms](https://en.wikipedia.org/wiki/Algorithm) for certain linear algebra problems:

- [[QR Decomposition]] (see [Householder transformation](https://en.wikipedia.org/wiki/Householder_transformation) and [Gram–Schmidt decomposition](https://en.wikipedia.org/wiki/Gram%E2%80%93Schmidt_decomposition));
- [[Singular Value Decomposition]]
- Reduction to [Hessenberg](https://en.wikipedia.org/wiki/Hessenberg_matrix) form (the first step in many [eigenvalue algorithms](https://en.wikipedia.org/wiki/Eigenvalue_algorithm))
- [Linear regression](https://en.wikipedia.org/wiki/Linear_regression)
- Projective elements of matrix algebras are used in the construction of certain K-groups in [Operator K-theory](https://en.wikipedia.org/wiki/Operator_K-theory)

As stated above, projections are a special case of idempotents. Analytically, orthogonal projections are non-commutative generalizations of [characteristic functions](https://en.wikipedia.org/wiki/Indicator_function). Idempotents are used in classifying, for instance, [semisimple algebras](https://en.wikipedia.org/wiki/Semisimple_algebra), while [measure theory](https://en.wikipedia.org/wiki/Measure_theory) begins with considering characteristic functions of [measurable sets](https://en.wikipedia.org/wiki/Measurable_set). Therefore, as one can imagine, projections are very often encountered in the context of [operator algebras](https://en.wikipedia.org/wiki/Operator_algebra). In particular, a [von Neumann algebra](https://en.wikipedia.org/wiki/Von_Neumann_algebra) is generated by its complete [lattice](https://en.wikipedia.org/wiki/Lattice_(order) "Lattice (order)") of projections.

## Generalizations

More generally, given a map between normed vector spaces $T\colon V\to W,$ one can analogously ask for this map to be an isometry on the orthogonal complement of the kernel: that $(\ker T)^{\perp }\to W$ be an isometry (compare [Partial isometry](https://en.wikipedia.org/wiki/Partial_isometry)); in particular it must be [onto](https://en.wikipedia.org/wiki/Surjective_function). The case of an orthogonal projection is when *W* is a subspace of *V.* In [[Riemannian Geometry]], this is used in the definition of a [Riemannian submersion](https://en.wikipedia.org/wiki/Riemannian_submersion).

## See also

- [Centering matrix](https://en.wikipedia.org/wiki/Centering_matrix), which is an example of a projection matrix.
- [Dykstra's projection algorithm](https://en.wikipedia.org/wiki/Dykstra%27s_projection_algorithm) to compute the projection onto an intersection of sets
- [Invariant subspace](https://en.wikipedia.org/wiki/Invariant_subspace)
- [Least-squares spectral analysis](https://en.wikipedia.org/wiki/Least-squares_spectral_analysis)
- [Orthogonalization](https://en.wikipedia.org/wiki/Orthogonalization)
- [Properties of trace](https://en.wikipedia.org/wiki/Trace_(linear_algebra)#Properties "Trace (linear algebra)")

## Notes

1.  Meyer, pp 386+387
2.  ^   Horn, Roger A.; Johnson, Charles R. (2013). *Matrix Analysis, second edition*. Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780521839402](https://en.wikipedia.org/wiki/Special:BookSources/9780521839402).
3.  Meyer, p. 433
4.  Meyer, p. 431
5.  Meyer, equation (5.13.4)
6.  Banerjee, Sudipto; Roy, Anindya (2014), [Linear Algebra and Matrix Analysis for Statistics](https://books.google.com/books?id=iIOhAwAAQBAJ&q=projection), Texts in Statistical Science (1st ed.), Chapman and Hall/CRC, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1420095388](https://en.wikipedia.org/wiki/Special:BookSources/978-1420095388)
7.  Meyer, equation (5.13.3)
8.  See also [Linear least squares (mathematics) § Properties of the least-squares estimators](https://en.wikipedia.org/wiki/Linear_least_squares_(mathematics)#Properties_of_the_least-squares_estimators).
9.  Banerjee, Sudipto; Roy, Anindya (2014), [Linear Algebra and Matrix Analysis for Statistics](https://books.google.com/books?id=iIOhAwAAQBAJ&q=projection), Texts in Statistical Science (1st ed.), Chapman and Hall/CRC, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1420095388](https://en.wikipedia.org/wiki/Special:BookSources/978-1420095388)
10. Banerjee, Sudipto (2004), "Revisiting Spherical Trigonometry with Orthogonal Projectors", *The College Mathematics Journal*, **35** (5): 375–381, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/07468342.2004.11922099](https://doi.org/10.1080%2F07468342.2004.11922099), [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [122277398](https://api.semanticscholar.org/CorpusID:122277398)
11. Banerjee, Sudipto; Roy, Anindya (2014), [Linear Algebra and Matrix Analysis for Statistics](https://books.google.com/books?id=iIOhAwAAQBAJ&q=projection), Texts in Statistical Science (1st ed.), Chapman and Hall/CRC, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1420095388](https://en.wikipedia.org/wiki/Special:BookSources/978-1420095388)
12. Meyer, equation (7.10.39)
13. Brust, J. J.; Marcia, R. F.; Petra, C. G. (2020), "Computationally Efficient Decompositions of Oblique Projection Matrices", *SIAM Journal on Matrix Analysis and Applications*, **41** (2): 852–870, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/19M1288115](https://doi.org/10.1137%2F19M1288115), [OSTI](https://en.wikipedia.org/wiki/OSTI_(identifier)) [1680061](https://www.osti.gov/biblio/1680061), [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [219921214](https://api.semanticscholar.org/CorpusID:219921214)
14. Doković, D. Ž. (August 1991). "Unitary similarity of projectors". *[Aequationes Mathematicae](https://en.wikipedia.org/wiki/Aequationes_Mathematicae)*. **42** (1): 220–224. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/BF01818492](https://doi.org/10.1007%2FBF01818492). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [122704926](https://api.semanticscholar.org/CorpusID:122704926).

## References

- Banerjee, Sudipto; Roy, Anindya (2014), *Linear Algebra and Matrix Analysis for Statistics*, Texts in Statistical Science (1st ed.), Chapman and Hall/CRC, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1420095388](https://en.wikipedia.org/wiki/Special:BookSources/978-1420095388)
- Dunford, N.; Schwartz, J. T. (1958). *Linear Operators, Part I: General Theory*. Interscience.
- Meyer, Carl D. (2000). [Matrix Analysis and Applied Linear Algebra](http://www.matrixanalysis.com/). Society for Industrial and Applied Mathematics. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-89871-454-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-89871-454-8).
- Brezinski, Claude: *Projection Methods for Systems of Equations*, North-Holland, ISBN 0-444-82777-3 (1997).

## External links

- [MIT Linear Algebra Lecture on Projection Matrices](https://www.youtube.com/watch?v=osh80YCg_GM&feature=PlayList&p=38823D6325151CED&index=16) on [YouTube](https://en.wikipedia.org/wiki/YouTube_video_(identifier)), from MIT OpenCourseWare
- [Linear Algebra 15d: The Projection Transformation](https://www.youtube.com/watch?v=qxxo-a9snhw&list=PLlXfTHzgMRUIqYrutsFXCOmiqKUgOgGJ5&index=3) on [YouTube](https://en.wikipedia.org/wiki/YouTube_video_(identifier)), by [Pavel Grinfeld](https://en.wikipedia.org/wiki/Pavel_Grinfeld).
- [Planar Geometric Projections Tutorial](https://www.cs.mtsu.edu/~jhankins/pages/planeview3D/tutorial.html) – a simple-to-follow tutorial explaining the different types of planar geometric projections.
