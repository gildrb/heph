[[linear-algebra.base]]

> Source: [[Kronecker Product]]
> License: Wikipedia content is available under CC BY-SA 4.0.

In [mathematics](https://en.wikipedia.org/wiki/Mathematics), the **Kronecker product**, sometimes denoted by ⊗, is an [operation](https://en.wikipedia.org/wiki/Operation_(mathematics) "Operation (mathematics)") on two [matrices](https://en.wikipedia.org/wiki/Matrix_(mathematics) "Matrix (mathematics)") of arbitrary size resulting in a [block matrix](https://en.wikipedia.org/wiki/Block_matrix). It is a specialization of the [tensor product](https://en.wikipedia.org/wiki/Tensor_product) (which is denoted by the same symbol) from vectors to matrices and gives the matrix of the [tensor product](https://en.wikipedia.org/wiki/Tensor_product) linear map with respect to a standard choice of [basis](https://en.wikipedia.org/wiki/Basis_(linear_algebra) "Basis (linear algebra)"). The Kronecker product is to be distinguished from the usual [[Matrix Multiplication]], which is an entirely different operation. The Kronecker product is also sometimes called **matrix direct product**.

## Definition

If **A** is an *m* × *n* matrix and **B** is a *p* × *q* matrix, then the Kronecker product **A** ⊗ **B** is the *pm* × *qn* block matrix:

$\mathbf {A} \otimes \mathbf {B} ={\begin{bmatrix}a_{11}\mathbf {B} &\cdots &a_{1n}\mathbf {B} \\\vdots &\ddots &\vdots \\a_{m1}\mathbf {B} &\cdots &a_{mn}\mathbf {B} \end{bmatrix}},$

more explicitly:

${\mathbf {A} \otimes \mathbf {B} }={\begin{bmatrix}a_{11}b_{11}&a_{11}b_{12}&\cdots &a_{11}b_{1q}&\cdots &\cdots &a_{1n}b_{11}&a_{1n}b_{12}&\cdots &a_{1n}b_{1q}\\a_{11}b_{21}&a_{11}b_{22}&\cdots &a_{11}b_{2q}&\cdots &\cdots &a_{1n}b_{21}&a_{1n}b_{22}&\cdots &a_{1n}b_{2q}\\\vdots &\vdots &\ddots &\vdots &&&\vdots &\vdots &\ddots &\vdots \\a_{11}b_{p1}&a_{11}b_{p2}&\cdots &a_{11}b_{pq}&\cdots &\cdots &a_{1n}b_{p1}&a_{1n}b_{p2}&\cdots &a_{1n}b_{pq}\\\vdots &\vdots &&\vdots &\ddots &&\vdots &\vdots &&\vdots \\\vdots &\vdots &&\vdots &&\ddots &\vdots &\vdots &&\vdots \\a_{m1}b_{11}&a_{m1}b_{12}&\cdots &a_{m1}b_{1q}&\cdots &\cdots &a_{mn}b_{11}&a_{mn}b_{12}&\cdots &a_{mn}b_{1q}\\a_{m1}b_{21}&a_{m1}b_{22}&\cdots &a_{m1}b_{2q}&\cdots &\cdots &a_{mn}b_{21}&a_{mn}b_{22}&\cdots &a_{mn}b_{2q}\\\vdots &\vdots &\ddots &\vdots &&&\vdots &\vdots &\ddots &\vdots \\a_{m1}b_{p1}&a_{m1}b_{p2}&\cdots &a_{m1}b_{pq}&\cdots &\cdots &a_{mn}b_{p1}&a_{mn}b_{p2}&\cdots &a_{mn}b_{pq}\end{bmatrix}}.$

Using $/\!/$ and $\%$ to denote [truncating integer division](https://en.wikipedia.org/wiki/Truncating_integer_division) and [remainder](https://en.wikipedia.org/wiki/Remainder), respectively, and numbering the matrix elements starting from 0, one obtains

$(A\otimes B)_{pr+v,qs+w}=a_{rs}b_{vw}$

$(A\otimes B)_{i,j}=a_{i/\!/p,j/\!/q}b_{i\%p,j\%q}.$

For the usual numbering starting from 1, one obtains

$(A\otimes B)_{p(r-1)+v,q(s-1)+w}=a_{rs}b_{vw}$

$(A\otimes B)_{i,j}=a_{\lceil i/p\rceil ,\lceil j/q\rceil }b_{(i-1)\%p+1,(j-1)\%q+1}.$

If **A** and **B** represent [linear transformations](https://en.wikipedia.org/wiki/Linear_transformations) **V**<sub>1</sub> → **W**<sub>1</sub> and **V**<sub>2</sub> → **W**<sub>2</sub>, respectively, then the [tensor product](https://en.wikipedia.org/wiki/Tensor_product) of the two maps is a map **V**<sub>1</sub> ⊗ **V**<sub>2</sub> → **W**<sub>1</sub> ⊗ **W**<sub>2</sub> represented by **A** ⊗ **B**.

### Examples

${\begin{bmatrix}1&2\\3&4\\\end{bmatrix}}\otimes {\begin{bmatrix}0&5\\6&7\\\end{bmatrix}}={\begin{bmatrix}1{\begin{bmatrix}0&5\\6&7\\\end{bmatrix}}&2{\begin{bmatrix}0&5\\6&7\\\end{bmatrix}}\\3{\begin{bmatrix}0&5\\6&7\\\end{bmatrix}}&4{\begin{bmatrix}0&5\\6&7\\\end{bmatrix}}\\\end{bmatrix}}=\left[{\begin{array}{cc|cc}1\times 0&1\times 5&2\times 0&2\times 5\\1\times 6&1\times 7&2\times 6&2\times 7\\\hline 3\times 0&3\times 5&4\times 0&4\times 5\\3\times 6&3\times 7&4\times 6&4\times 7\\\end{array}}\right]=\left[{\begin{array}{cc|cc}0&5&0&10\\6&7&12&14\\\hline 0&15&0&20\\18&21&24&28\end{array}}\right].$

Similarly:

${\begin{bmatrix}1&-4&7\\-2&3&3\end{bmatrix}}\otimes {\begin{bmatrix}8&-9&-6&5\\1&-3&-4&7\\2&8&-8&-3\\1&2&-5&-1\end{bmatrix}}=\left[{\begin{array}{cccc|cccc|cccc}8&-9&-6&5&-32&36&24&-20&56&-63&-42&35\\1&-3&-4&7&-4&12&16&-28&7&-21&-28&49\\2&8&-8&-3&-8&-32&32&12&14&56&-56&-21\\1&2&-5&-1&-4&-8&20&4&7&14&-35&-7\\\hline -16&18&12&-10&24&-27&-18&15&24&-27&-18&15\\-2&6&8&-14&3&-9&-12&21&3&-9&-12&21\\-4&-16&16&6&6&24&-24&-9&6&24&-24&-9\\-2&-4&10&2&3&6&-15&-3&3&6&-15&-3\end{array}}\right]$

## Properties

### Relations to other matrix operations

1.  **[Bilinearity](https://en.wikipedia.org/wiki/Bilinearity) and [associativity](https://en.wikipedia.org/wiki/Associativity):**

    The Kronecker product is a special case of the [tensor product](https://en.wikipedia.org/wiki/Tensor_product), so it is [bilinear](https://en.wikipedia.org/wiki/Bilinear_operator) and [associative](https://en.wikipedia.org/wiki/Associativity):

    ${\begin{aligned}\mathbf {A} \otimes (\mathbf {B} +\mathbf {C} )&=\mathbf {A} \otimes \mathbf {B} +\mathbf {A} \otimes \mathbf {C} ,\\(\mathbf {B} +\mathbf {C} )\otimes \mathbf {A} &=\mathbf {B} \otimes \mathbf {A} +\mathbf {C} \otimes \mathbf {A} ,\\(k\mathbf {A} )\otimes \mathbf {B} &=\mathbf {A} \otimes (k\mathbf {B} )=k(\mathbf {A} \otimes \mathbf {B} ),\\(\mathbf {A} \otimes \mathbf {B} )\otimes \mathbf {C} &=\mathbf {A} \otimes (\mathbf {B} \otimes \mathbf {C} ),\\\mathbf {A} \otimes \mathbf {0} &=\mathbf {0} \otimes \mathbf {A} =\mathbf {0} ,\end{aligned}}$

    where **A**, **B** and **C** are matrices, **0** is a zero matrix, and *k* is a scalar.

2.  **Non-[commutative](https://en.wikipedia.org/wiki/Commutative_operation):**

    In general, **A** ⊗ **B** and **B** ⊗ **A** are different matrices. However, **A** ⊗ **B** and **B** ⊗ **A** are permutation equivalent, meaning that there exist [permutation matrices](https://en.wikipedia.org/wiki/Permutation_matrix) **P** and **Q** such that

    $\mathbf {B} \otimes \mathbf {A} =\mathbf {P} \,\left(\mathbf {A} \otimes \mathbf {B} \right)\,\mathbf {Q} .$

    If **A** and **B** are square, then **A** ⊗ **B** and **B** ⊗ **A** are even permutation [similar](https://en.wikipedia.org/wiki/Similar_matrix), meaning that we can take **P** = **Q**<sup>T</sup>.

    The matrices **P** and **Q** are perfect shuffle matrices, called the "commutation" matrix. The Commutation matrix **S**<sub>*p*, *q*</sub> can be constructed by taking slices of the **I**<sub>*r*</sub> identity matrix, where $r=pq$.

    $\mathbf {S} _{p,q}={\begin{bmatrix}\mathbf {I} _{r}(1:q:r,:)\\\mathbf {I} _{r}(2:q:r,:)\\\vdots \\\mathbf {I} _{r}(q:q:r,:)\end{bmatrix}}$

    [MATLAB](https://en.wikipedia.org/wiki/MATLAB) colon notation is used here to indicate submatrices, and **I**<sub>*r*</sub> is the *r* × *r* identity matrix. If $\mathbf {A} \in \mathbb {R} ^{m_{1}\times n_{1}}$ and $\mathbf {B} \in \mathbb {R} ^{m_{2}\times n_{2}}$, then

    $\mathbf {B} \otimes \mathbf {A} =\mathbf {S} _{m_{1},m_{2}}(\mathbf {A} \otimes \mathbf {B} )\mathbf {S} _{n_{1},n_{2}}^{\textsf {T}}$

3.  **The mixed-product property:**

    If **A**, **B**, **C** and **D** are matrices of such size that one can form the [matrix products](https://en.wikipedia.org/wiki/Matrix_product) **AC** and **BD**, then

    $(\mathbf {A} \otimes \mathbf {B} )(\mathbf {C} \otimes \mathbf {D} )=(\mathbf {AC} )\otimes (\mathbf {BD} ).$

    This is called the *mixed-product property*, because it mixes the ordinary matrix product and the Kronecker product.

    As an immediate consequence (again, taking $\mathbf {A} \in \mathbb {R} ^{m_{1}\times n_{1}}$ and $\mathbf {B} \in \mathbb {R} ^{m_{2}\times n_{2}}$),

    $\mathbf {A} \otimes \mathbf {B} =(\mathbf {I} _{m_{1}}\otimes \mathbf {B} )(\mathbf {A} \otimes \mathbf {I} _{n_{2}})=(\mathbf {A} \otimes \mathbf {I} _{m_{2}})(\mathbf {I} _{n_{1}}\otimes \mathbf {B} ).$

    In particular, using the *transpose* property from below, this means that if

    $\mathbf {A} =\mathbf {Q} \otimes \mathbf {U}$

    and **Q** and **U** are [orthogonal](https://en.wikipedia.org/wiki/Orthogonal_matrix) (or [unitary](https://en.wikipedia.org/wiki/Unitary_matrix)), then **A** is also orthogonal (resp., unitary).

    The mixed Kronecker matrix-vector product can be written as:

    $\left(\mathbf {A} \otimes \mathbf {B} \right)\operatorname {vec} \left(\mathbf {V} \right)=\operatorname {vec} (\mathbf {B} \mathbf {V} \mathbf {A} ^{T})$

    where $\operatorname {vec} (\mathbf {V} )$ is the [vectorization](https://en.wikipedia.org/wiki/Vectorization_(mathematics) "Vectorization (mathematics)") operator applied on $\mathbf {V}$ (formed by reshaping the matrix).

4.  **[Commutator property](https://en.wikipedia.org/wiki/Commutator#Ring_theory):**

    If $\mathbf {A}$ and $\mathbf {C}$ are square matrices of the dimension $m$, and $\mathbf {B}$ and $\mathbf {D}$ are square matrices of the dimension $n$, then the commutator

    $[\mathbf {A} \otimes \mathbf {B} ,\mathbf {C} \otimes \mathbf {D} ]=[\mathbf {A} ,\mathbf {C} ]\otimes (\mathbf {B} \mathbf {D} )+(\mathbf {C} \mathbf {A} )\otimes [\mathbf {B} ,\mathbf {D} ]$,

    or

    $[\mathbf {A} \otimes \mathbf {B} ,\mathbf {C} \otimes \mathbf {D} ]=[\mathbf {A} ,\mathbf {C} ]\otimes (\mathbf {D} \mathbf {B} )+(\mathbf {A} \mathbf {C} )\otimes [\mathbf {B} ,\mathbf {D} ]$.

5.  **[Hadamard product](https://en.wikipedia.org/wiki/Hadamard_product_(matrices) "Hadamard product (matrices)") (element-wise multiplication):**

    The mixed-product property also works for the element-wise product. If **A** and **C** are matrices of the same size, **B** and **D** are matrices of the same size, then

    $(\mathbf {A} \otimes \mathbf {B} )\circ (\mathbf {C} \otimes \mathbf {D} )=(\mathbf {A} \circ \mathbf {C} )\otimes (\mathbf {B} \circ \mathbf {D} ).$

6.  **The inverse of a Kronecker product:**

    It follows that **A** ⊗ **B** is [invertible](https://en.wikipedia.org/wiki/Invertible_matrix) [if and only if](https://en.wikipedia.org/wiki/If_and_only_if) both **A** and **B** are invertible, in which case the inverse is given by

    $(\mathbf {A} \otimes \mathbf {B} )^{-1}=\mathbf {A} ^{-1}\otimes \mathbf {B} ^{-1}.$

    The invertible product property holds for the [[Moore-Penrose Pseudoinverse|Moore–Penrose pseudoinverse]] as well, that is

    $(\mathbf {A} \otimes \mathbf {B} )^{+}=\mathbf {A} ^{+}\otimes \mathbf {B} ^{+}.$

    **Mat**<sub>*F*</sub> is a concrete [skeleton category](https://en.wikipedia.org/wiki/Skeleton_(category_theory) "Skeleton (category theory)") for the [equivalent category](https://en.wikipedia.org/wiki/Equivalence_of_categories) **FinVect**<sub>*F*</sub> of finite dimensional vector spaces over *F*, whose objects are such finite dimensional vector spaces *V*, arrows are *F*-linear maps *L* : *V* → *W*, and identity arrows are the identity maps of the spaces. The equivalence of categories amounts to simultaneously [choosing a basis](https://en.wikipedia.org/wiki/Axiom_of_choice) in every finite-dimensional vector space *V* over *F*; matrices' elements represent these mappings with respect to the chosen bases; and likewise the Kronecker product is the representation of the [tensor product](https://en.wikipedia.org/wiki/Tensor_product) in the chosen bases.

7.  **[Transpose](https://en.wikipedia.org/wiki/Transpose):**

    Transposition and [conjugate transposition](https://en.wikipedia.org/wiki/Conjugate_transpose) are distributive over the Kronecker product:

    $(\mathbf {A} \otimes \mathbf {B} )^{\textsf {T}}=\mathbf {A} ^{\textsf {T}}\otimes \mathbf {B} ^{\textsf {T}}$ and $(\mathbf {A} \otimes \mathbf {B} )^{*}=\mathbf {A} ^{*}\otimes \mathbf {B} ^{*}.$

8.  **[[Determinant]]:**

    Let **A** be an *n* × *n* matrix and let **B** be an *m* × *m* matrix. Then

    $\left|\mathbf {A} \otimes \mathbf {B} \right|=\left|\mathbf {A} \right|^{m}\left|\mathbf {B} \right|^{n}.$

    The exponent in \|**A**\| is the order of **B** and the exponent in \|**B**\| is the order of **A**.

9.  **Kronecker sum and [exponentiation](https://en.wikipedia.org/wiki/Matrix_exponential):**

    If **A** is *n* × *n*, **B** is *m* × *m*, and **I**<sub>*k*</sub> denotes the *k* × *k* [identity matrix](https://en.wikipedia.org/wiki/Identity_matrix) then we can define what is sometimes called the **Kronecker sum**, ⊕, by

    $\mathbf {A} \,{\overline {\oplus }}\,\mathbf {B} =\mathbf {A} \otimes \mathbf {I} _{m}+\mathbf {I} _{n}\otimes \mathbf {B} .$

    This is *different* from the [*direct sum*](https://en.wikipedia.org/wiki/Matrix_addition#Direct_sum) of two matrices. This operation is related to the tensor product on [Lie algebras](https://en.wikipedia.org/wiki/Lie_algebra), as detailed below ([\#Abstract properties](#Abstract_properties)) in the point "Relation to the abstract [tensor product](https://en.wikipedia.org/wiki/Tensor_product)".

    We have the following formula for the [matrix exponential](https://en.wikipedia.org/wiki/Matrix_exponential), which is useful in some numerical evaluations.

    $\exp({\mathbf {N} \,{\overline {\oplus }}\,\mathbf {M} })=\exp(\mathbf {N} )\otimes \exp(\mathbf {M} )$

    Kronecker sums appear naturally in [physics](https://en.wikipedia.org/wiki/Physics) when considering ensembles of non-interacting [systems](https://en.wikipedia.org/wiki/Physical_system).<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

    If *H<sup>r</sup>* is the Hamiltonian of the *r*th such system. Then the total Hamiltonian of the ensemble is

    $H_{\operatorname {Tot} }={\overline {\bigoplus _{r}}}H^{r}.$

10. **[Vectorization](https://en.wikipedia.org/wiki/Vectorization_(mathematics) "Vectorization (mathematics)") of a Kronecker product:**

    Let $A$ be an $m\times n$ matrix and $B$ a $p\times q$ matrix. When the order of the Kronecker product and vectorization is interchanged, the two operations can be linked linearly through a function that involves the [commutation matrix](https://en.wikipedia.org/wiki/Commutation_matrix), $K_{qm}$. That is, $\operatorname {vec} (\operatorname {Kron} (A,B))$ and $\operatorname {Kron} (\operatorname {vec} A,\operatorname {vec} B)$ have the following relationship:

    $\operatorname {vec} (A\otimes B)=(I_{n}\otimes K_{qm}\otimes I_{p})(\operatorname {vec} A\otimes \operatorname {vec} B).$

    Furthermore, the above relation can be rearranged in terms of either $\operatorname {vec} A$ or $\operatorname {vec} B$ as follows:

    $\operatorname {vec} (A\otimes B)=(I_{n}\otimes G)\operatorname {vec} A=(H\otimes I_{p})\operatorname {vec} B,$

    where

    $G=(K_{qm}\otimes I_{p})(I_{m}\otimes \operatorname {vec} B){\text{ and }}H=(I_{n}\otimes K_{qm})(\operatorname {vec} A\otimes I_{q}).$

11. **[Outer Product](https://en.wikipedia.org/wiki/Outer_Product):**

    If $x\in \mathbb {R} ^{n}$ and $y\in \mathbb {R} ^{m}$ are arbitrary vectors, then the outer product between $x$ and $y$ is defined as $xy^{T}$. The Kronecker product is related to the outer product by: $y\otimes x=\operatorname {vec} (xy^{T})$.

### Abstract properties

1.  **[Spectrum](https://en.wikipedia.org/wiki/Spectrum_(functional_analysis) "Spectrum (functional analysis)"):**

    Suppose that **A** and **B** are square matrices of size *n* and *m* respectively. Let *λ*<sub>1</sub>, ..., *λ*<sub>*n*</sub> be the [eigenvalues](https://en.wikipedia.org/wiki/Eigenvalue) of **A** and *μ*<sub>1</sub>, ..., *μ*<sub>*m*</sub> be those of **B** (listed according to [multiplicity](https://en.wikipedia.org/wiki/Multiplicity_(mathematics) "Multiplicity (mathematics)")). Then the [eigenvalues](https://en.wikipedia.org/wiki/Eigenvalues) of **A** ⊗ **B** are

    $\lambda _{i}\mu _{j},\qquad i=1,\ldots ,n,\,j=1,\ldots ,m.$

    It follows that the [trace](https://en.wikipedia.org/wiki/Trace_(matrix)) and [[Determinant]] of a Kronecker product are given by

    $\operatorname {tr} (\mathbf {A} \otimes \mathbf {B} )=\operatorname {tr} \mathbf {A} \,\operatorname {tr} \mathbf {B} \quad {\text{and}}\quad \det(\mathbf {A} \otimes \mathbf {B} )=(\det \mathbf {A} )^{m}(\det \mathbf {B} )^{n}.$

2.  **[[Singular Value Decomposition|Singular values]]:**

    If **A** and **B** are rectangular matrices, then one can consider their [[Singular Value Decomposition|singular values]]. Suppose that **A** has *r*<sub>**A**</sub> nonzero singular values, namely

    $\sigma _{\mathbf {A} ,i},\qquad i=1,\ldots ,r_{\mathbf {A} }.$

    Similarly, denote the nonzero singular values of **B** by

    $\sigma _{\mathbf {B} ,i},\qquad i=1,\ldots ,r_{\mathbf {B} }.$

    Then the Kronecker product **A** ⊗ **B** has *r*<sub>**A**</sub>*r*<sub>**B**</sub> nonzero singular values, namely

    $\sigma _{\mathbf {A} ,i}\sigma _{\mathbf {B} ,j},\qquad i=1,\ldots ,r_{\mathbf {A} },\,j=1,\ldots ,r_{\mathbf {B} }.$

    Since the [rank of a matrix](https://en.wikipedia.org/wiki/Rank_of_a_matrix) equals the number of nonzero singular values, we find that

    $\operatorname {rank} (\mathbf {A} \otimes \mathbf {B} )=\operatorname {rank} \mathbf {A} \,\operatorname {rank} \mathbf {B} .$

3.  **Relation to the abstract [tensor product](https://en.wikipedia.org/wiki/Tensor_product):**

    The Kronecker product of matrices corresponds to the abstract tensor product of linear maps. Specifically, if the vector spaces *V*, *W*, *X*, and *Y* have bases {*v*<sub>1</sub>, ..., *v*<sub>*m*</sub>}, {*w*<sub>1</sub>, ..., *w*<sub>*n*</sub>}, {*x*<sub>1</sub>, ..., *x*<sub>*d*</sub>}, and {*y*<sub>1</sub>, ..., *y*<sub>*e*</sub>}, respectively, and if the matrices *A* and *B* represent the linear transformations *S* : *V* → *X* and *T* : *W* → *Y*, respectively in the appropriate bases, then the matrix *A* ⊗ *B* represents the tensor product of the two maps, *S* ⊗ *T* : *V* ⊗ *W* → *X* ⊗ *Y* with respect to the basis {*v*<sub>1</sub> ⊗ *w*<sub>1</sub>, *v*<sub>1</sub> ⊗ *w*<sub>2</sub>, ..., *v*<sub>2</sub> ⊗ *w*<sub>1</sub>, ..., *v*<sub>*m*</sub> ⊗ *w*<sub>*n*</sub>} of *V* ⊗ *W* and the similarly defined basis of *X* ⊗ *Y* with the property that *A* ⊗ *B*(*v*<sub>*i*</sub> ⊗ *w*<sub>*j*</sub>) = (*Av*<sub>*i*</sub>) ⊗ (*Bw*<sub>*j*</sub>), where *i* and *j* are integers in the proper range.

    When *V* and *W* are [Lie algebras](https://en.wikipedia.org/wiki/Lie_algebra), and *S* : *V* → *V* and *T* : *W* → *W* are [Lie algebra homomorphisms](https://en.wikipedia.org/wiki/Lie_algebra_homomorphism), the Kronecker sum of *A* and *B* represents the induced Lie algebra homomorphisms *V* ⊗ *W* → *V* ⊗ *W*.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

4.  **Relation to [products of graphs](https://en.wikipedia.org/wiki/Graph_product):**

    The Kronecker product of the [adjacency matrices](https://en.wikipedia.org/wiki/Adjacency_matrix) of two [graphs](https://en.wikipedia.org/wiki/Graph_(discrete_mathematics) "Graph (discrete mathematics)") is the adjacency matrix of the [tensor product graph](https://en.wikipedia.org/wiki/Tensor_product_of_graphs). The [Kronecker sum](#Kronecker_sum_and_exponentiation) of the adjacency matrices of two [graphs](https://en.wikipedia.org/wiki/Graph_(discrete_mathematics) "Graph (discrete mathematics)") is the adjacency matrix of the [Cartesian product graph](https://en.wikipedia.org/wiki/Cartesian_product_of_graphs).

## Matrix equations

The Kronecker product can be used to get a convenient representation for some matrix equations. Consider for instance the equation **AXB** = **C**, where **A**, **B** and **C** are given matrices and the matrix **X** is the unknown. We can use the "vec trick" to rewrite this equation as

$\left(\mathbf {B} ^{\textsf {T}}\otimes \mathbf {A} \right)\,\operatorname {vec} (\mathbf {X} )=\operatorname {vec} (\mathbf {AXB} )=\operatorname {vec} (\mathbf {C} ).$

Here, vec(**X**) denotes the [vectorization](https://en.wikipedia.org/wiki/Vectorization_(mathematics) "Vectorization (mathematics)") of the matrix **X**, formed by stacking the columns of **X** into a single [column vector](https://en.wikipedia.org/wiki/Column_vector).

It now follows from the properties of the Kronecker product that the equation **AXB** = **C** has a unique solution, if and only if **A** and **B** are invertible (, Lemma 4.3.1).

If **X** and **C** are row-ordered into the column vectors **u** and **v**, respectively, then (, 2.8 Block Matrices and Kronecker Products)

$\mathbf {v} =\left(\mathbf {A} \otimes \mathbf {B} ^{\textsf {T}}\right)\mathbf {u} .$

The reason is that

$\mathbf {v} =\operatorname {vec} \left((\mathbf {AXB} )^{\textsf {T}}\right)=\operatorname {vec} \left(\mathbf {B} ^{\textsf {T}}\mathbf {X} ^{\textsf {T}}\mathbf {A} ^{\textsf {T}}\right)=\left(\mathbf {A} \otimes \mathbf {B} ^{\textsf {T}}\right)\operatorname {vec} \left(\mathbf {X^{\textsf {T}}} \right)=\left(\mathbf {A} \otimes \mathbf {B} ^{\textsf {T}}\right)\mathbf {u} .$

### Applications

For an example of the application of this formula, see the article on the [Lyapunov equation](https://en.wikipedia.org/wiki/Lyapunov_equation). This formula also comes in handy in showing that the [matrix normal distribution](https://en.wikipedia.org/wiki/Matrix_normal_distribution) is a special case of the [[Multivariate Normal Distribution]]. This formula is also useful for representing 2D [image processing](https://en.wikipedia.org/wiki/Image_processing) operations in matrix-vector form.

Another example is when a matrix can be factored as a Kronecker product, then matrix multiplication can be performed faster by using the above formula. This can be applied recursively, as done in the [radix-2 FFT](https://en.wikipedia.org/wiki/Cooley%E2%80%93Tukey_FFT_algorithm#The_radix-2_DIT_case) and the [Fast Walsh–Hadamard transform](https://en.wikipedia.org/wiki/Fast_Walsh%E2%80%93Hadamard_transform). Splitting a known matrix into the Kronecker product of two smaller matrices is known as the "nearest Kronecker product" problem, and can be solved exactly by using the [[Singular Value Decomposition|SVD]]. To split a matrix into the Kronecker product of more than two matrices, in an optimal fashion, is a difficult problem and the subject of ongoing research; some authors cast it as a tensor decomposition problem.

In conjunction with the [least squares method](https://en.wikipedia.org/wiki/Least_squares), the Kronecker product can be used as an accurate solution to the [hand–eye calibration problem](https://en.wikipedia.org/wiki/Hand%E2%80%93eye_calibration_problem).

## Related matrix operations 

Two related matrix operations are the **Tracy–Singh** and **[Khatri–Rao products](https://en.wikipedia.org/wiki/Khatri%E2%80%93Rao_product)**, which operate on [partitioned matrices](https://en.wikipedia.org/wiki/Block_matrix). Let the *m* × *n* matrix **A** be partitioned into the *m*<sub>*i*</sub> × *n*<sub>*j*</sub> blocks **A**<sub>*ij*</sub> and *p* × *q* matrix **B** into the *p<sub>k</sub>* × *q<sub>ℓ</sub>* blocks **B**<sub>*kl*</sub>, with of course Σ*<sub>i</sub> m<sub>i</sub>* = *m*, Σ*<sub>j</sub> n<sub>j</sub>* = *n*, Σ*<sub>k</sub> p<sub>k</sub>* = *p* and Σ*<sub>ℓ</sub> q<sub>ℓ</sub>* = *q*.

### Tracy–Singh product

The **Tracy–Singh product** is defined as

$\mathbf {A} \circ \mathbf {B} =\left(\mathbf {A} _{ij}\circ \mathbf {B} \right)_{ij}=\left(\left(\mathbf {A} _{ij}\otimes \mathbf {B} _{kl}\right)_{kl}\right)_{ij}$

which means that the (*ij*)-th subblock of the *mp* × *nq* product **A** $\circ$ **B** is the *m<sub>i</sub> p* × *n<sub>j</sub> q* matrix **A**<sub>*ij*</sub> $\circ$ **B**, of which the (*kℓ*)-th subblock equals the *m<sub>i</sub> p<sub>k</sub>* × *n<sub>j</sub> q<sub>ℓ</sub>* matrix **A**<sub>*ij*</sub> ⊗ **B**<sub>*kℓ*</sub>. Essentially the Tracy–Singh product is the pairwise Kronecker product for each pair of partitions in the two matrices.

For example, if **A** and **B** both are 2 × 2 partitioned matrices e.g.:

$\mathbf {A} =\left[{\begin{array}{c | c}\mathbf {A} _{11}&\mathbf {A} _{12}\\\hline \mathbf {A} _{21}&\mathbf {A} _{22}\end{array}}\right]=\left[{\begin{array}{c c | c}1&2&3\\4&5&6\\\hline 7&8&9\end{array}}\right],\quad \mathbf {B} =\left[{\begin{array}{c | c}\mathbf {B} _{11}&\mathbf {B} _{12}\\\hline \mathbf {B} _{21}&\mathbf {B} _{22}\end{array}}\right]=\left[{\begin{array}{c | c c}1&4&7\\\hline 2&5&8\\3&6&9\end{array}}\right],$

we get:

${\begin{aligned}\mathbf {A} \circ \mathbf {B} ={}&\left[{\begin{array}{c | c}\mathbf {A} _{11}\circ \mathbf {B} &\mathbf {A} _{12}\circ \mathbf {B} \\\hline \mathbf {A} _{21}\circ \mathbf {B} &\mathbf {A} _{22}\circ \mathbf {B} \end{array}}\right]\\={}&\left[{\begin{array}{c | c | c | c}\mathbf {A} _{11}\otimes \mathbf {B} _{11}&\mathbf {A} _{11}\otimes \mathbf {B} _{12}&\mathbf {A} _{12}\otimes \mathbf {B} _{11}&\mathbf {A} _{12}\otimes \mathbf {B} _{12}\\\hline \mathbf {A} _{11}\otimes \mathbf {B} _{21}&\mathbf {A} _{11}\otimes \mathbf {B} _{22}&\mathbf {A} _{12}\otimes \mathbf {B} _{21}&\mathbf {A} _{12}\otimes \mathbf {B} _{22}\\\hline \mathbf {A} _{21}\otimes \mathbf {B} _{11}&\mathbf {A} _{21}\otimes \mathbf {B} _{12}&\mathbf {A} _{22}\otimes \mathbf {B} _{11}&\mathbf {A} _{22}\otimes \mathbf {B} _{12}\\\hline \mathbf {A} _{21}\otimes \mathbf {B} _{21}&\mathbf {A} _{21}\otimes \mathbf {B} _{22}&\mathbf {A} _{22}\otimes \mathbf {B} _{21}&\mathbf {A} _{22}\otimes \mathbf {B} _{22}\end{array}}\right]\\={}&\left[{\begin{array}{c c | c c c c | c | c c}1&2&4&7&8&14&3&12&21\\4&5&16&28&20&35&6&24&42\\\hline 2&4&5&8&10&16&6&15&24\\3&6&6&9&12&18&9&18&27\\8&10&20&32&25&40&12&30&48\\12&15&24&36&30&45&18&36&54\\\hline 7&8&28&49&32&56&9&36&63\\\hline 14&16&35&56&40&64&18&45&72\\21&24&42&63&48&72&27&54&81\end{array}}\right].\end{aligned}}$

### Khatri–Rao product

- Block Kronecker product
- Column-wise Khatri–Rao product

### Face-splitting product

Mixed-products properties

$\mathbf {A} \otimes (\mathbf {B} \bullet \mathbf {C} )=(\mathbf {A} \otimes \mathbf {B} )\bullet \mathbf {C} ,$

where $\bullet$ denotes the [Face-splitting product](https://en.wikipedia.org/wiki/Khatri%E2%80%93Rao_product#Face-splitting_product).

$(\mathbf {A} \bullet \mathbf {B} )(\mathbf {C} \otimes \mathbf {D} )=(\mathbf {A} \mathbf {C} )\bullet (\mathbf {B} \mathbf {D} ),$

Similarly:

$(\mathbf {A} \bullet \mathbf {L} )(\mathbf {B} \otimes \mathbf {M} )\cdots (\mathbf {C} \otimes \mathbf {S} )=(\mathbf {A} \mathbf {B} \cdots \mathbf {C} )\bullet (\mathbf {L} \mathbf {M} \cdots \mathbf {S} ),$

$\mathbf {c} ^{\textsf {T}}\bullet \mathbf {d} ^{\textsf {T}}=\mathbf {c} ^{\textsf {T}}\otimes \mathbf {d} ^{\textsf {T}},$

where $\mathbf {c}$ and $\mathbf {d}$ are [vectors](https://en.wikipedia.org/wiki/Vector_(mathematics_and_physics) "Vector (mathematics and physics)"),

$(\mathbf {A} \bullet \mathbf {B} )(\mathbf {c} \otimes \mathbf {d} )=(\mathbf {A} \mathbf {c} )\circ (\mathbf {B} \mathbf {d} ),$

where $\mathbf {c}$ and $\mathbf {d}$ are [vectors](https://en.wikipedia.org/wiki/Vector_(mathematics_and_physics) "Vector (mathematics and physics)"), and $\circ$ denotes the [Hadamard product](https://en.wikipedia.org/wiki/Hadamard_product_(matrices) "Hadamard product (matrices)").

Similarly:

$(\mathbf {A} \bullet \mathbf {B} )(\mathbf {M} \mathbf {N} \mathbf {c} \otimes \mathbf {Q} \mathbf {P} \mathbf {d} )=(\mathbf {A} \mathbf {M} \mathbf {N} \mathbf {c} )\circ (\mathbf {B} \mathbf {Q} \mathbf {P} \mathbf {d} ),$

${\mathcal {F}}(C^{(1)}x\star C^{(2)}y)=({\mathcal {F}}C^{(1)}\bullet {\mathcal {F}}C^{(2)})(x\otimes y)={\mathcal {F}}C^{(1)}x\circ {\mathcal {F}}C^{(2)}y,$

where $\star$ is vector [convolution](https://en.wikipedia.org/wiki/Convolution) and ${\mathcal {F}}$ is the [Fourier transform matrix](https://en.wikipedia.org/wiki/DFT_matrix) (this result is an evolving of [count sketch](https://en.wikipedia.org/wiki/Count_sketch) properties),

$(\mathbf {A} \bullet \mathbf {L} )(\mathbf {B} \otimes \mathbf {M} )\cdots (\mathbf {C} \otimes \mathbf {S} )(\mathbf {K} \ast \mathbf {T} )=(\mathbf {A} \mathbf {B} \cdot \mathbf {C} \mathbf {K} )\circ (\mathbf {L} \mathbf {M} \cdots \mathbf {S} \mathbf {T} ),$

where $\ast$ denotes the [column-wise Khatri–Rao product](https://en.wikipedia.org/wiki/Khatri%E2%80%93Rao_product#Column-wise_Khatri–Rao_product).

Similarly:

$(\mathbf {A} \bullet \mathbf {L} )(\mathbf {B} \otimes \mathbf {M} )\cdots (\mathbf {C} \otimes \mathbf {S} )(c\otimes d)=(\mathbf {A} \mathbf {B} \cdots \mathbf {C} \mathbf {c} )\circ (\mathbf {L} \mathbf {M} \cdots \mathbf {S} \mathbf {d} ),$

$(\mathbf {A} \bullet \mathbf {L} )(\mathbf {B} \otimes \mathbf {M} )\cdots (\mathbf {C} \otimes \mathbf {S} )(\mathbf {P} \mathbf {c} \otimes \mathbf {Q} \mathbf {d} )=(\mathbf {A} \mathbf {B} \cdots \mathbf {C} \mathbf {P} \mathbf {c} )\circ (\mathbf {L} \mathbf {M} \cdots \mathbf {S} \mathbf {Q} \mathbf {d} ),$

where $\mathbf {c}$ and $\mathbf {d}$ are [vectors](https://en.wikipedia.org/wiki/Vector_(mathematics_and_physics) "Vector (mathematics and physics)").

## See also

- [Generalized linear array model](https://en.wikipedia.org/wiki/Generalized_linear_array_model)
- [Hadamard product (matrices)](https://en.wikipedia.org/wiki/Hadamard_product_(matrices) "Hadamard product (matrices)")
- [Kronecker coefficient](https://en.wikipedia.org/wiki/Kronecker_coefficient)

## Notes

1.  Weisstein, Eric W. ["Kronecker product"](https://mathworld.wolfram.com/KroneckerProduct.html). *mathworld.wolfram.com*. Retrieved 2020-09-06.
2.  Zehfuss, G. (1858). ["Ueber eine gewisse Determinante"](http://resolver.sub.uni-goettingen.de/purl?PPN599415665_0003). *Zeitschrift für Mathematik und Physik*. **3**: 298–301.
3.  Henderson, Harold V.; Pukelsheim, Friedrich; Searle, Shayle R. (1983). ["On the history of the kronecker product"](https://doi.org/10.1080/03081088308817548). *Linear and Multilinear Algebra*. **14** (2): 113–120. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/03081088308817548](https://doi.org/10.1080%2F03081088308817548). [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[1813/32834](https://hdl.handle.net/1813%2F32834). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0308-1087](https://search.worldcat.org/issn/0308-1087).
4.  Sayed, Ali H. (2022-12-22). [Inference and Learning from Data: Foundations](https://books.google.com/books?id=VNWbEAAAQBAJ&dq=maximum+norm&pg=PA41). Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-009-21812-2](https://en.wikipedia.org/wiki/Special:BookSources/978-1-009-21812-2).
5.  Henderson, H.V.; Searle, S.R. (1980). ["The vec-permutation matrix, the vec operator and Kronecker products: A review"](https://ecommons.cornell.edu/bitstream/1813/32747/1/BU-645-M.pdf) (PDF). *Linear and Multilinear Algebra*. **9** (4): 271–288. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/03081088108817379](https://doi.org/10.1080%2F03081088108817379). [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[1813/32747](https://hdl.handle.net/1813%2F32747).
6.  Van Loan, Charles F. (2000). ["The ubiquitous Kronecker product"](https://doi.org/10.1016%2Fs0377-0427%2800%2900393-9). *[Journal of Computational and Applied Mathematics](https://en.wikipedia.org/wiki/Journal_of_Computational_and_Applied_Mathematics)*. **123** (1–2): 85–100. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2000JCoAM.123...85L](https://ui.adsabs.harvard.edu/abs/2000JCoAM.123...85L). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/s0377-0427(00)00393-9](https://doi.org/10.1016%2Fs0377-0427%2800%2900393-9).
7.  ^    Liu, Shuangzhe; Trenkler, Götz; Kollo, Tõnu; von Rosen, Dietrich; Baksalary, Oskar Maria (2023). "Professor Heinz Neudecker and matrix differential calculus". *Statistical Papers*. **65** (4): 2605–2639. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s00362-023-01499-w](https://doi.org/10.1007%2Fs00362-023-01499-w).
8.  [Langville, Amy N.](https://en.wikipedia.org/wiki/Amy_Langville); Stewart, William J. (1 June 2004). ["The Kronecker product and stochastic automata networks"](https://doi.org/10.1016%2Fj.cam.2003.10.010). *Journal of Computational and Applied Mathematics*. **167** (2): 429–447. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2004JCoAM.167..429L](https://ui.adsabs.harvard.edu/abs/2004JCoAM.167..429L). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.cam.2003.10.010](https://doi.org/10.1016%2Fj.cam.2003.10.010).
9.  Macedo, Hugo Daniel; Oliveira, José Nuno (2013). "Typing linear algebra: A biproduct-oriented approach". *[Science of Computer Programming](https://en.wikipedia.org/wiki/Science_of_Computer_Programming)*. **78** (11): 2160–2191. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1312.4818](https://arxiv.org/abs/1312.4818). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2013arXiv1312.4818M](https://ui.adsabs.harvard.edu/abs/2013arXiv1312.4818M). [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.747.2083](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.747.2083). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.scico.2012.07.012](https://doi.org/10.1016%2Fj.scico.2012.07.012). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [9846072](https://api.semanticscholar.org/CorpusID:9846072).
10. Brewer, J.W. (1969). "A note on Kronecker matrix products and matrix equation systems". *[SIAM Journal on Applied Mathematics](https://en.wikipedia.org/wiki/SIAM_Journal_on_Applied_Mathematics)*. **17** (3): 603–606. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/0117057](https://doi.org/10.1137%2F0117057).
11. Dummit, David S.; Foote, Richard M. (1999). *Abstract Algebra* (2 ed.). New York: John Wiley and Sons. pp. 401–402. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-36857-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-36857-1).
12. See Knuth, D.E. ["Pre-Fascicle 0a: Introduction to Combinatorial Algorithms"](https://web.archive.org/web/20190513215832/http://www-cs-faculty.stanford.edu/~knuth/fasc0a.ps.gz) (zeroth printing, revision 2 ed.). answer to Exercise 96. Archived from [the original](http://www-cs-faculty.stanford.edu/~knuth/fasc0a.ps.gz) on 2019-05-13. Retrieved 2007-10-24, to appear as part of Knuth, D.E. *[The Art of Computer Programming](https://en.wikipedia.org/wiki/The_Art_of_Computer_Programming)*. Vol. 4A.
13. Van Loan, C.; Pitsianis, N. (1992). *Approximation with Kronecker Products*. Ithaca, NY: Cornell University Press.
14. King Keung Wu; Yam, Yeung; Meng, Helen; Mesbahi, Mehran (2016). "Kronecker product approximation with multiple factor matrices via the tensor product algorithm". *2016 IEEE International Conference on Systems, Man, and Cybernetics (SMC)*. pp. 004277–004282. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/SMC.2016.7844903](https://doi.org/10.1109%2FSMC.2016.7844903). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-5090-1897-0](https://en.wikipedia.org/wiki/Special:BookSources/978-1-5090-1897-0). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [30695585](https://api.semanticscholar.org/CorpusID:30695585).
15. Dantas, Cássio F.; Cohen, Jérémy E.; Gribonval, Rémi (2018). ["Learning Fast Dictionaries for Sparse Representations Using Low-Rank Tensor Decompositions"](https://hal.inria.fr/hal-01709343v2/document). [Latent Variable Analysis and Signal Separation](https://hal.inria.fr/hal-01709343/file/notes%20%281%29.pdf) (PDF). Lecture Notes in Computer Science. Vol. 10891. pp. 456–466. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-3-319-93764-9_42](https://doi.org/10.1007%2F978-3-319-93764-9_42). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-319-93763-2](https://en.wikipedia.org/wiki/Special:BookSources/978-3-319-93763-2). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [46963798](https://api.semanticscholar.org/CorpusID:46963798).
16. Li, Algo; et al. (4 September 2010). ["Simultaneous robot-world and hand-eye calibration using dual-quaternions and Kronecker product"](https://web.archive.org/web/20200209164546/https://pdfs.semanticscholar.org/225d/e4ea2d3f18b7743bfeabf925fa603fc47bcb.pdf) (PDF). *International Journal of the Physical Sciences*. **5** (10): 1530–1536. [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [7446157](https://api.semanticscholar.org/CorpusID:7446157). Archived from [the original](https://pdfs.semanticscholar.org/225d/e4ea2d3f18b7743bfeabf925fa603fc47bcb.pdf) (PDF) on 9 February 2020.
17. Tracy, D.S.; Singh, R.P. (1972). "A new matrix product and its applications in matrix differentiation". *[Statistica Neerlandica](https://en.wikipedia.org/wiki/Statistica_Neerlandica)*. **26** (4): 143–157. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1111/j.1467-9574.1972.tb00199.x](https://doi.org/10.1111%2Fj.1467-9574.1972.tb00199.x).
18. Liu, Shuangzhe (1999). ["Matrix Results on the Khatri–Rao and Tracy–Singh Products"](https://doi.org/10.1016%2FS0024-3795%2898%2910209-4). *Linear Algebra and Its Applications*. **289** (1–3): 267–277. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/S0024-3795(98)10209-4](https://doi.org/10.1016%2FS0024-3795%2898%2910209-4).
19. Liu, Shuangzhe; Trenkler, Götz (2008). "Hadamard, Khatri-Rao, Kronecker and other matrix products". *International Journal of Information and Systems Sciences*. **4** (1): 160–177.
20. Slyusar, V.I. (1998) \[27 December 1996\]. ["End products in matrices in radar applications"](http://slyusar.kiev.ua/en/IZV_1998_3.pdf) (PDF). *[Radioelectronics and Communications Systems](https://en.wikipedia.org/wiki/Radioelectronics_and_Communications_Systems)*. **41** (3): 50–53.
21. ^    Slyusar, Vadym (1999). ["New matrix operations for DSP"](https://www.researchgate.net/publication/342918804) (self-published lecture). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.13140/RG.2.2.31620.76164/1](https://doi.org/10.13140%2FRG.2.2.31620.76164%2F1) – via [ResearchGate](https://en.wikipedia.org/wiki/ResearchGate).
22. ^    Slyusar, V.I. (March 13, 1998). ["A Family of Face Products of Matrices and its Properties"](http://slyusar.kiev.ua/FACE.pdf) (PDF). *Cybernetics and Systems Analysis C/C of Kibernetika I Sistemnyi Analiz. 1999*. **35** (3): 379–384. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/BF02733426](https://doi.org/10.1007%2FBF02733426). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [119661450](https://api.semanticscholar.org/CorpusID:119661450).
23. Slyusar, V.I. (1997-09-15). [New operations of matrices product for applications of radars](http://slyusar.kiev.ua/DIPED_1997.pdf) (PDF). Direct and Inverse Problems of Electromagnetic and Acoustic Wave Theory (DIPED-97), Lviv. pp. 73–74.
24. Ahle, Thomas Dybdahl; Knudsen, Jakob Bæk Tejs (2019-09-03). "Almost optimal tensor sketch". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1909.01821](https://arxiv.org/abs/1909.01821) \[[cs.DS](https://arxiv.org/archive/cs.DS)\].
25. Ninh, Pham; [Pagh, Rasmus](https://en.wikipedia.org/wiki/Rasmus_Pagh) (2013). *Fast and scalable polynomial kernels via explicit feature maps*. SIGKDD international conference on Knowledge discovery and data mining. Association for Computing Machinery. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.718.2766](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.718.2766). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1145/2487575.2487591](https://doi.org/10.1145%2F2487575.2487591).

## References

- [Horn, Roger A.](https://en.wikipedia.org/wiki/Roger_Horn); [Johnson, Charles R.](https://en.wikipedia.org/wiki/Charles_Royal_Johnson) (1991). [Topics in Matrix Analysis](https://books.google.com/books?id=LeuNXB2bl5EC&q=%22Kronecker+product%22). Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-46713-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-46713-1).
- Jain, Anil K. (1989). [Fundamentals of Digital Image Processing](https://books.google.com/books?id=GANSAAAAMAAJ&q=%22Kronecker+product%22). Prentice Hall. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1989fdip.book.....J](https://ui.adsabs.harvard.edu/abs/1989fdip.book.....J). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-13-336165-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-13-336165-0).
- Steeb, Willi-Hans (1997). *Matrix Calculus and Kronecker Product with Applications and C++ Programs*. World Scientific Publishing. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-981-02-3241-2](https://en.wikipedia.org/wiki/Special:BookSources/978-981-02-3241-2).
- Steeb, Willi-Hans (2006). [Problems and Solutions in Introductory and Advanced Matrix Calculus](https://books.google.com/books?id=CSDbVU1Eg3UC&q=%22Kronecker+product%22). World Scientific Publishing. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-981-256-916-5](https://en.wikipedia.org/wiki/Special:BookSources/978-981-256-916-5).
- Liu, Shuangzhe; Trenkler, Götz (2008). "Hadamard, Khatri-Rao, Kronecker and other matrix products". *International Journal of Information and Systems Sciences*. **4**: 160–177.

## External links

- ["Tensor product"](https://www.encyclopediaofmath.org/). *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*. [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society). 2001 \[1994\].
- ["Kronecker product"](https://planetmath.org/KroneckerProduct). *[PlanetMath](https://en.wikipedia.org/wiki/PlanetMath)*.
- ["Kronecker product"](http://mathworld.wolfram.com/KroneckerProduct.html). *MathWorld*.
- ["New Kronecker product problems"](https://web.archive.org/web/20211104202500/https://issc.uj.ac.za/downloads/problems/newkronecker.pdf) (PDF). Archived from [the original](http://issc.uj.ac.za/downloads/problems/newkronecker.pdf) (PDF) on 2021-11-04. Retrieved 2009-08-19.
- ["Earliest uses"](http://jeff560.tripod.com/k.html). The entry on the Kronecker, Zehfuss, or Direct Product of matrices has historical information.
- [calculate Kronecker product of two matrices](https://sourceforge.net/projects/kronecker/). *[SourceForge](https://en.wikipedia.org/wiki/SourceForge)* (generic C++ and Fortran 90 source code). 2015-06-27.
- ["Kronecker product"](http://rosettacode.org/wiki/Kronecker_product). *RosettaCode.org*. 31 December 2020. Retrieved 2021-01-13. Software source in more than 40 languages.
