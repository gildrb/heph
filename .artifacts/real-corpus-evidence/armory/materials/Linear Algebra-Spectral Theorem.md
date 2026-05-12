[[linear-algebra.base]]

> Source: [[Spectral Theorem]]
> License: Wikipedia content is available under CC BY-SA 4.0.

In [linear algebra](https://en.wikipedia.org/wiki/Linear_algebra) and [functional analysis](https://en.wikipedia.org/wiki/Functional_analysis), a **spectral theorem** is a result about when a [linear operator](https://en.wikipedia.org/wiki/Linear_operator) or [matrix](https://en.wikipedia.org/wiki/Matrix_(mathematics) "Matrix (mathematics)") can be [diagonalized](https://en.wikipedia.org/wiki/Diagonalizable_matrix) (that is, represented as a [diagonal matrix](https://en.wikipedia.org/wiki/Diagonal_matrix) in some basis). This is extremely useful because computations involving a diagonalizable matrix can often be reduced to much simpler computations involving the corresponding diagonal matrix. The concept of diagonalization is relatively straightforward for operators on [finite-dimensional vector spaces](https://en.wikipedia.org/wiki/Finite-dimensional_vector_space) but requires some modification for operators on infinite-dimensional spaces. In general, the spectral theorem identifies a class of [linear operators](https://en.wikipedia.org/wiki/Linear_operator) that can be modeled by [multiplication operators](https://en.wikipedia.org/wiki/Multiplication_operator), which are as simple as one can hope to find. In more abstract language, the spectral theorem is a statement about commutative [C\*-algebras](https://en.wikipedia.org/wiki/C*-algebra). See also [spectral theory](https://en.wikipedia.org/wiki/Spectral_theory) for a historical perspective.

Examples of operators to which the spectral theorem applies are [self-adjoint operators](https://en.wikipedia.org/wiki/Self-adjoint_operator) or more generally [normal operators](https://en.wikipedia.org/wiki/Normal_operator) on [Hilbert spaces](https://en.wikipedia.org/wiki/Hilbert_space).

The spectral theorem also provides a [canonical](https://en.wikipedia.org/wiki/Canonical_form) decomposition, called the **[spectral decomposition](https://en.wikipedia.org/wiki/Eigendecomposition_of_a_matrix)**, of the underlying vector space on which the operator acts.

[Augustin-Louis Cauchy](https://en.wikipedia.org/wiki/Augustin-Louis_Cauchy) proved the spectral theorem for [symmetric matrices](https://en.wikipedia.org/wiki/Symmetric_matrix), i.e., that every real, symmetric matrix is diagonalizable. In addition, Cauchy was the first to be systematic about [[Determinant|determinants]]. The spectral theorem as generalized by [John von Neumann](https://en.wikipedia.org/wiki/John_von_Neumann) is today perhaps the most important result of [operator theory](https://en.wikipedia.org/wiki/Operator_theory).

This article mainly focuses on the simplest kind of spectral theorem, that for a [self-adjoint](https://en.wikipedia.org/wiki/Self-adjoint) operator on a Hilbert space. However, as noted above, the spectral theorem also holds for normal operators on a Hilbert space.

## Finite-dimensional case

### Hermitian maps and Hermitian matrices

We begin by considering a [Hermitian matrix](https://en.wikipedia.org/wiki/Hermitian_matrix) on $\mathbb {C} ^{n}$ (but the following discussion will be adaptable to the more restrictive case of [symmetric matrices](https://en.wikipedia.org/wiki/Symmetric_matrix) on $\mathbb {R} ^{n}$). We consider a [Hermitian map](https://en.wikipedia.org/wiki/Hermitian_operator) *A* on a finite-dimensional [complex](https://en.wikipedia.org/wiki/Complex_number) [inner product space](https://en.wikipedia.org/wiki/Inner_product_space) *V* endowed with a [positive definite](https://en.wikipedia.org/wiki/Definite_bilinear_form) [sesquilinear](https://en.wikipedia.org/wiki/Sesquilinear_form) [inner product](https://en.wikipedia.org/wiki/Inner_product) $\langle \cdot ,\cdot \rangle$. The Hermitian condition on $A$ means that for all *x*, *y* ∈ *V*, 

$$
\langle Ax,y\rangle =\langle x,Ay\rangle .
$$

An equivalent condition is that *A*<sup>\*</sup> = *A*, where *A*<sup>\*</sup> is the [Hermitian conjugate](https://en.wikipedia.org/wiki/Hermitian_conjugate) of *A*. In the case that *A* is identified with a Hermitian matrix, the matrix of *A*<sup>\*</sup> is equal to its [conjugate transpose](https://en.wikipedia.org/wiki/Conjugate_transpose). (If *A* is a [real matrix](https://en.wikipedia.org/wiki/Real_matrix), then this is equivalent to *A*<sup>T</sup> = *A*, that is, *A* is a [symmetric matrix](https://en.wikipedia.org/wiki/Symmetric_matrix).)

This condition implies that all eigenvalues of a Hermitian map are real: To see this, it is enough to apply it to the case when *x* = *y* is an eigenvector. (Recall that an [eigenvector](https://en.wikipedia.org/wiki/Eigenvector) of a linear map *A* is a non-zero vector *v* such that *Av* = *λv* for some scalar *λ*. The value *λ* is the corresponding [eigenvalue](https://en.wikipedia.org/wiki/Eigenvalue). Moreover, the [eigenvalues](https://en.wikipedia.org/wiki/Eigenvalues) are roots of the [characteristic polynomial](https://en.wikipedia.org/wiki/Characteristic_polynomial).)

**Theorem**—If *A* is Hermitian on *V*, then there exists an [orthonormal basis](https://en.wikipedia.org/wiki/Orthonormal_basis) of *V* consisting of eigenvectors of *A*. Each eigenvalue of *A* is real.

We provide a sketch of a proof for the case where the underlying field of scalars is the [complex numbers](https://en.wikipedia.org/wiki/Complex_number).

By the [fundamental theorem of algebra](https://en.wikipedia.org/wiki/Fundamental_theorem_of_algebra), applied to the [characteristic polynomial](https://en.wikipedia.org/wiki/Characteristic_polynomial) of *A*, there is at least one complex eigenvalue *λ*<sub>1</sub> and corresponding eigenvector *v*<sub>1</sub>, which must by definition be non-zero. Then since 

$$
\lambda _{1}\langle v_{1},v_{1}\rangle =\langle A(v_{1}),v_{1}\rangle =\langle v_{1},A(v_{1})\rangle ={\bar {\lambda }}_{1}\langle v_{1},v_{1}\rangle ,
$$

 we find that *λ*<sub>1</sub> is real. Now consider the space ${\mathcal {K}}^{n-1}={\text{span}}(v_{1})^{\perp }$, the [orthogonal complement](https://en.wikipedia.org/wiki/Orthogonal_complement) of *v*<sub>1</sub>. By Hermiticity, ${\mathcal {K}}^{n-1}$ is an [invariant subspace](https://en.wikipedia.org/wiki/Invariant_subspace) of *A*. To see that, consider any $k\in {\mathcal {K}}^{n-1}$ so that $\langle k,v_{1}\rangle =0$ by definition of ${\mathcal {K}}^{n-1}$. To satisfy invariance, we need to check if $A(k)\in {\mathcal {K}}^{n-1}$. This is true because, $\langle A(k),v_{1}\rangle =\langle k,A(v_{1})\rangle =\langle k,\lambda _{1}v_{1}\rangle =0$. Applying the same argument to ${\mathcal {K}}^{n-1}$ shows that *A* has at least one real eigenvalue $\lambda _{2}$ and corresponding eigenvector $v_{2}\in {\mathcal {K}}^{n-1}\perp v_{1}$. This can be used to build another invariant subspace ${\mathcal {K}}^{n-2}={\text{span}}(\{v_{1},v_{2}\})^{\perp }$. Finite induction then finishes the proof.

The matrix representation of *A* in a basis of eigenvectors is diagonal, and by the construction the proof gives a basis of mutually orthogonal eigenvectors; by choosing them to be unit vectors one obtains an orthonormal basis of eigenvectors. *A* can be written as a linear combination of pairwise orthogonal projections, called its **spectral decomposition**. Let 

$$
V_{\lambda }=\{v\in V:Av=\lambda v\}
$$

 be the eigenspace corresponding to an eigenvalue $\lambda$. Note that the definition does not depend on any choice of specific eigenvectors. In general, *V* is the orthogonal direct sum of the spaces $V_{\lambda }$ where the $\lambda$ ranges over the [spectrum](https://en.wikipedia.org/wiki/Spectrum_of_a_matrix) of $A$.

When the matrix being decomposed is Hermitian, the spectral decomposition is a special case of the [Schur decomposition](https://en.wikipedia.org/wiki/Schur_decomposition) (see the proof in case of [normal matrices](#Normal_matrices) below).

### Spectral decomposition and the singular value decomposition

The spectral decomposition is a special case of the [[Singular Value Decomposition]], which states that any matrix $A\in \mathbb {C} ^{m\times n}$ can be expressed as $A=U\Sigma V^{*}$, where $U\in \mathbb {C} ^{m\times m}$ and $V\in \mathbb {C} ^{n\times n}$ are [unitary matrices](https://en.wikipedia.org/wiki/Unitary_matrices) and $\Sigma \in \mathbb {R} ^{m\times n}$ is a diagonal matrix. The diagonal entries of $\Sigma$ are uniquely determined by $A$ and are known as the [singular values](https://en.wikipedia.org/wiki/Singular_values) of $A$. If $A$ is Hermitian, then $A^{*}=A$ and $V\Sigma U^{*}=U\Sigma V^{*}$ which implies $U=V$.

### Normal matrices

The spectral theorem extends to a more general class of matrices. Let *A* be an operator on a finite-dimensional inner product space. *A* is said to be [normal](https://en.wikipedia.org/wiki/Normal_matrix) if *A*<sup>\*</sup>*A* = *AA*<sup>\*</sup>.

One can show that *A* is normal if and only if it is unitarily diagonalizable using the [Schur decomposition](https://en.wikipedia.org/wiki/Schur_decomposition). That is, any matrix can be written as *A* = *UTU*<sup>\*</sup>, where *U* is unitary and *T* is [upper triangular](https://en.wikipedia.org/wiki/Upper_triangular). If *A* is normal, then one sees that *TT*<sup>\*</sup> = *T*<sup>\*</sup>*T*. Therefore, *T* must be diagonal since a normal upper triangular matrix is diagonal (see [normal matrix](https://en.wikipedia.org/wiki/Normal_matrix#Consequences)). The converse is obvious.

In other words, *A* is normal if and only if there exists a [unitary matrix](https://en.wikipedia.org/wiki/Unitary_matrix) *U* such that 

$$
A=UDU^{*},
$$

 where *D* is a [diagonal matrix](https://en.wikipedia.org/wiki/Diagonal_matrix). Then, the entries of the diagonal of *D* are the [eigenvalues](https://en.wikipedia.org/wiki/Eigenvalue) of *A*. The column vectors of *U* are the eigenvectors of *A* and they are orthonormal. Unlike the Hermitian case, the entries of *D* need not be real.

## Compact self-adjoint operators

In the more general setting of Hilbert spaces, which may have an infinite dimension, the statement of the spectral theorem for [compact](https://en.wikipedia.org/wiki/Compact_operator) [self-adjoint operators](https://en.wikipedia.org/wiki/Self-adjoint_operators) is virtually the same as in the finite-dimensional case.

**Theorem**—Suppose *A* is a compact self-adjoint operator on a (real or complex) Hilbert space *V*. Then there is an [orthonormal basis](https://en.wikipedia.org/wiki/Orthonormal_basis) of *V* consisting of eigenvectors of *A*. Each eigenvalue is real.

As for Hermitian matrices, the key point is to prove the existence of at least one nonzero eigenvector. One cannot rely on determinants to show existence of eigenvalues, but one can use a maximization argument analogous to the variational characterization of eigenvalues.

If the compactness assumption is removed, then it is *not* true that every self-adjoint operator has eigenvectors. For example, the multiplication operator $M_{x}$ on $L^{2}([0,1])$ which takes each $\psi (x)\in L^{2}([0,1])$ to $x\psi (x)$ is bounded and self-adjoint, but has no eigenvectors. However, its spectrum, suitably defined, is still equal to $[0,1]$, see [spectrum of bounded operator](https://en.wikipedia.org/wiki/Spectrum_(functional_analysis)#Spectrum_of_a_bounded_operator "Spectrum (functional analysis)").

## Bounded self-adjoint operators

### Possible absence of eigenvectors

The next generalization we consider is that of [bounded self-adjoint operators](https://en.wikipedia.org/wiki/Self-adjoint_operator#Bounded_self-adjoint_operators) on a Hilbert space. Such operators may have no eigenvectors: for instance let *A* be the operator of multiplication by *t* on $L^{2}([0,1])$, that is, 

$$
[Af](t)=tf(t).
$$

This operator does not have any eigenvectors *in* $L^{2}([0,1])$, though it does have eigenvectors in a larger space. Namely the [distribution](https://en.wikipedia.org/wiki/Distribution_(mathematics)) $f(t)=\delta (t-t_{0})$, where $\delta$ is the [Dirac delta function](https://en.wikipedia.org/wiki/Dirac_delta_function), is an eigenvector when construed in an appropriate sense. The Dirac delta function is however not a function in the classical sense and does not lie in the Hilbert space *L*<sup>2</sup>\[0, 1\]. Thus, the delta-functions are "generalized eigenvectors" of $A$ but not eigenvectors in the usual sense.

### Spectral subspaces and projection-valued measures

In the absence of (true) eigenvectors, one can look for a "spectral subspace" consisting of an *almost eigenvector*, i.e, a closed subspace $V_{E}$ of $V$ associated with a [Borel set](https://en.wikipedia.org/wiki/Borel_set) $E\subset \sigma (A)$ in the [spectrum](https://en.wikipedia.org/wiki/Spectrum_(functional_analysis) "Spectrum (functional analysis)") of $A$. This subspace can be thought of as the closed span of generalized eigenvectors for $A$ with eigen*values* in $E$. In the above example, where $[Af](t)=tf(t),\;$ we might consider the subspace of functions supported on a small interval $[a,a+\varepsilon ]$ inside $[0,1]$. This space is invariant under $A$ and for any $f$ in this subspace, $Af$ is very close to $af$. Each subspace, in turn, is encoded by the associated projection operator, and the collection of all the subspaces is then represented by a [projection-valued measure](https://en.wikipedia.org/wiki/Projection-valued_measure).

One formulation of the spectral theorem expresses the operator *A* as an integral of the coordinate function over the operator's spectrum $\sigma (A)$ with respect to a projection-valued measure. 

$$
A=\int _{\sigma (A)}\lambda \,d\pi (\lambda ).
$$

When the self-adjoint operator in question is [compact](https://en.wikipedia.org/wiki/Compact_operator), this version of the spectral theorem reduces to something similar to the finite-dimensional spectral theorem above, except that the operator is expressed as a finite or countably infinite linear combination of projections, that is, the measure consists only of atoms.

### Multiplication operator version

An alternative formulation of the spectral theorem says that every bounded self-adjoint operator is unitarily equivalent to a multiplication operator, a relatively simple type of operator.

****Theorem****—Let $A$ be a bounded self-adjoint operator on a Hilbert space $V$. Then there is a [measure space](https://en.wikipedia.org/wiki/Measure_space) $(X,\Sigma ,\mu )$ and a real-valued [essentially bounded](https://en.wikipedia.org/wiki/Ess_sup) measurable function $\lambda$ on $X$ and a [unitary operator](https://en.wikipedia.org/wiki/Unitary_operator) $U:V\to L^{2}(X,\mu )$ such that 

$$
U^{*}TU=A,
$$

 where $T$ is the [multiplication operator](https://en.wikipedia.org/wiki/Multiplication_operator): 

$$
[Tf](x)=\lambda (x)f(x)
$$

 and $\vert T\vert$ $=\vert \lambda \vert _{\infty }$.

Multiplication operators are a direct generalization of diagonal matrices. A finite-dimensional Hermitian vector space $V$ may be coordinatized as the space of functions $f:B\to \mathbb {C}$ from a basis $B$ to the complex numbers, so that the $B$-coordinates of a vector are the values of the corresponding function $f$. The finite-dimensional spectral theorem for a self-adjoint operator $A:V\to V$ states that there exists an orthonormal basis of eigenvectors $B$, so that the inner product becomes the [dot product](https://en.wikipedia.org/wiki/Dot_product) with respect to the $B$-coordinates: thus $V$ is isomorphic to $L^{2}(B,\mu )$ for the discrete unit measure $\mu$ on $B$. Also $A$ is unitarily equivalent to the multiplication operator $[Tf](v)=\lambda (v)f(v)$, where $\lambda (v)$ is the eigenvalue of $v\in B$: that is, $A$ multiplies each $B$-coordinate by the corresponding eigenvalue $\lambda (v)$, the action of a diagonal matrix. Finally, the [operator norm](https://en.wikipedia.org/wiki/Operator_norm) $|A|=|T|$ is equal to the magnitude of the largest eigenvalue $|\lambda |_{\infty }$.

The spectral theorem is the beginning of the vast research area of functional analysis called [operator theory](https://en.wikipedia.org/wiki/Operator_theory); see also [spectral measure](https://en.wikipedia.org/wiki/Spectral_measure).

There is also an analogous spectral theorem for bounded [normal operators](https://en.wikipedia.org/wiki/Normal_operator) on Hilbert spaces. The only difference in the conclusion is that now *$\lambda$* may be complex-valued.

### Direct integrals

There is also a formulation of the spectral theorem in terms of [direct integrals](https://en.wikipedia.org/wiki/Direct_integral). It is similar to the multiplication-operator formulation, but more canonical.

Let $A$ be a bounded self-adjoint operator and let $\sigma (A)$ be the spectrum of $A$. The direct-integral formulation of the spectral theorem associates two quantities to $A$. First, a measure $\mu$ on $\sigma (A)$, and second, a family of Hilbert spaces $\{H_{\lambda }\},\,\,\lambda \in \sigma (A).$ We then form the direct integral Hilbert space 

$$
\int _{\mathbf {R} }^{\oplus }H_{\lambda }\,d\mu (\lambda ).
$$

 The elements of this space are functions (or "sections") $s(\lambda ),\,\,\lambda \in \sigma (A),$ such that $s(\lambda )\in H_{\lambda }$ for all $\lambda$. The direct-integral version of the spectral theorem may be expressed as follows:

**Theorem**—If $A$ is a bounded self-adjoint operator, then $A$ is unitarily equivalent to the "multiplication by $\lambda$" operator on 

$$
\int _{\mathbf {R} }^{\oplus }H_{\lambda }\,d\mu (\lambda )
$$

 for some measure $\mu$ and some family $\{H_{\lambda }\}$ of Hilbert spaces. The measure $\mu$ is uniquely determined by $A$ up to measure-theoretic equivalence; that is, any two measure associated to the same $A$ have the same sets of measure zero. The dimensions of the Hilbert spaces $H_{\lambda }$ are uniquely determined by $A$ up to a set of $\mu$-measure zero.

The spaces $H_{\lambda }$ can be thought of as something like "eigenspaces" for $A$. Note, however, that unless the one-element set $\lambda$ has positive measure, the space $H_{\lambda }$ is not actually a subspace of the direct integral. Thus, the $H_{\lambda }$'s should be thought of as "generalized eigenspace"—that is, the elements of $H_{\lambda }$ are "eigenvectors" that do not actually belong to the Hilbert space.

Although both the multiplication-operator and direct integral formulations of the spectral theorem express a self-adjoint operator as unitarily equivalent to a multiplication operator, the direct integral approach is more canonical. First, the set over which the direct integral takes place (the spectrum of the operator) is canonical. Second, the function we are multiplying by is canonical in the direct-integral approach: Simply the function $\lambda \mapsto \lambda$.

### Cyclic vectors and simple spectrum

A vector $\varphi$ is called a [cyclic vector](https://en.wikipedia.org/wiki/Cyclic_vector) for $A$ if the vectors $\varphi ,A\varphi ,A^{2}\varphi ,\ldots$ span a dense subspace of the Hilbert space. Suppose $A$ is a bounded self-adjoint operator for which a cyclic vector exists. In that case, there is no distinction between the direct-integral and multiplication-operator formulations of the spectral theorem. Indeed, in that case, there is a measure $\mu$ on the spectrum $\sigma (A)$ of $A$ such that $A$ is unitarily equivalent to the "multiplication by $\lambda$" operator on $L^{2}(\sigma (A),\mu )$. This result represents $A$ simultaneously as a multiplication operator *and* as a direct integral, since $L^{2}(\sigma (A),\mu )$ is just a direct integral in which each Hilbert space $H_{\lambda }$ is just $\mathbb {C}$.

Not every bounded self-adjoint operator admits a cyclic vector; indeed, by the uniqueness in the direct integral decomposition, this can occur only when all the $H_{\lambda }$'s have dimension one. When this happens, we say that $A$ has "simple spectrum" in the sense of [spectral multiplicity theory](https://en.wikipedia.org/wiki/Self-adjoint_operator#Spectral_multiplicity_theory). That is, a bounded self-adjoint operator that admits a cyclic vector should be thought of as the infinite-dimensional generalization of a self-adjoint matrix with distinct eigenvalues (i.e., each eigenvalue has multiplicity one).

Although not every $A$ admits a cyclic vector, it is easy to see that we can decompose the Hilbert space as a direct sum of invariant subspaces on which $A$ has a cyclic vector. This observation is the key to the proofs of the multiplication-operator and direct-integral forms of the spectral theorem.

### Functional calculus

One important application of the spectral theorem (in whatever form) is the idea of defining a [functional calculus](https://en.wikipedia.org/wiki/Functional_calculus). That is, given a function $f$ defined on the spectrum of $A$, we wish to define an operator $f(A)$. If $f$ is simply a positive power, $f(x)=x^{n}$, then $f(A)$ is just the $n$-th power of $A$, $A^{n}$. The interesting cases are where $f$ is a nonpolynomial function such as a square root or an exponential. Either of the versions of the spectral theorem provides such a functional calculus. In the direct-integral version, for example, $f(A)$ acts as the "multiplication by $f$" operator in the direct integral: 

$$
[f(A)s](\lambda )=f(\lambda )s(\lambda ).
$$

 That is to say, each space $H_{\lambda }$ in the direct integral is a (generalized) eigenspace for $f(A)$ with eigenvalue $f(\lambda )$.

## Unbounded self-adjoint operators

Many important linear operators which occur in [analysis](https://en.wikipedia.org/wiki/Mathematical_analysis), such as [differential operators](https://en.wikipedia.org/wiki/Differential_operators), are [unbounded](https://en.wikipedia.org/wiki/Unbounded_operator). There is also a spectral theorem for [self-adjoint operators](https://en.wikipedia.org/wiki/Self-adjoint_operator) that applies in these cases. To give an example, every constant-coefficient differential operator is unitarily equivalent to a multiplication operator. Indeed, the unitary operator that implements this equivalence is the [Fourier transform](https://en.wikipedia.org/wiki/Fourier_transform); the multiplication operator is a type of [Fourier multiplier](https://en.wikipedia.org/wiki/Multiplier_(Fourier_analysis) "Multiplier (Fourier analysis)").

In general, spectral theorem for self-adjoint operators may take several equivalent forms. Notably, all of the formulations given in the previous section for bounded self-adjoint operators—the projection-valued measure version, the multiplication-operator version, and the direct-integral version—continue to hold for unbounded self-adjoint operators, with small technical modifications to deal with domain issues. Specifically, the only reason the multiplication operator $A$ on $L^{2}([0,1])$ is bounded, is due to the choice of domain $[0,1]$. The same operator on, e.g., $L^{2}(\mathbb {R} )$ would be unbounded.

The notion of "generalized eigenvectors" naturally extends to unbounded self-adjoint operators, as they are characterized as [non-normalizable](https://en.wikipedia.org/wiki/Probability_amplitude#Normalization) eigenvectors. Contrary to the case of [almost eigenvectors](#Spectral_subspaces_and_projection-valued_measures), however, the eigenvalues can be real or complex and, even if they are real, do not necessarily belong to the spectrum. Though, for self-adjoint operators there always exist a real subset of "generalized eigenvalues" such that the corresponding set of eigenvectors is [complete](https://en.wikipedia.org/wiki/Total_set).

## See also

- [Hahn-Hellinger theorem](https://en.wikipedia.org/wiki/Hahn-Hellinger_theorem) – Linear operator equal to its own adjointPages displaying short descriptions of redirect targets
- [Spectral theory of compact operators](https://en.wikipedia.org/wiki/Spectral_theory_of_compact_operators)
- [Spectral theory of normal C\*-algebras](https://en.wikipedia.org/wiki/Spectral_theory_of_normal_C*-algebras)
- [Borel functional calculus](https://en.wikipedia.org/wiki/Borel_functional_calculus)
- [Spectral theory](https://en.wikipedia.org/wiki/Spectral_theory)
- [Matrix decomposition](https://en.wikipedia.org/wiki/Matrix_decomposition)
- [Canonical form](https://en.wikipedia.org/wiki/Canonical_form)
- [Jordan decomposition](https://en.wikipedia.org/wiki/Jordan_normal_form), of which the spectral decomposition is a special case.
- [[Singular Value Decomposition]], a generalisation of spectral theorem to arbitrary matrices.
- [Eigendecomposition of a matrix](https://en.wikipedia.org/wiki/Eigendecomposition_of_a_matrix)
- [Wiener–Khinchin theorem](https://en.wikipedia.org/wiki/Wiener%E2%80%93Khinchin_theorem)

## Notes

1.  Hawkins, Thomas (1975). ["Cauchy and the spectral theory of matrices"](https://doi.org/10.1016%2F0315-0860%2875%2990032-4). *Historia Mathematica*. **2**: 1–29. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/0315-0860(75)90032-4](https://doi.org/10.1016%2F0315-0860%2875%2990032-4).
2.  [A Short History of Operator Theory](http://www.mathphysics.com/opthy/OpHistory.html) by [Evans M. Harrell II](https://en.wikipedia.org/wiki/Evans_M._Harrell_II)
3.  Section 6.1
4.  Theorem 7.2.1
5.  Theorem 7.12
6.  Theorem 7.20
7.  Theorem 7.19
8.  Lemma 8.11
9.  E.g.,  Definition 7.13
10. See Section 10.1 of 
11. , pp. 95–97.

## References

- [Sheldon Axler](https://en.wikipedia.org/wiki/Sheldon_Axler), *Linear Algebra Done Right*, Springer Verlag, 1997
- Hall, B.C. (2013), *Quantum Theory for Mathematicians*, Graduate Texts in Mathematics, vol. 267, Springer, [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2013qtm..book.....H](https://ui.adsabs.harvard.edu/abs/2013qtm..book.....H), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1461471158](https://en.wikipedia.org/wiki/Special:BookSources/978-1461471158)
- [Paul Halmos](https://en.wikipedia.org/wiki/Paul_Halmos), ["What Does the Spectral Theorem Say?"](https://www.jstor.org/stable/2313117), *American Mathematical Monthly*, volume 70, number 3 (1963), pages 241–247 [Other link](http://www.math.wsu.edu/faculty/watkins/Math502/pdfiles/spectral.pdf)
- de la Madrid Modino, R. (2001). [Quantum mechanics in rigged Hilbert space language](https://scholar.google.com/scholar?oi=bibs&cluster=2442809273695897641&btnI=1&hl=en) (PhD thesis). Universidad de Valladolid.
- [M. Reed](https://en.wikipedia.org/wiki/Michael_C._Reed) and [B. Simon](https://en.wikipedia.org/wiki/Barry_Simon), *Methods of Mathematical Physics*, vols I–IV, Academic Press 1972.
- [G. Teschl](https://en.wikipedia.org/wiki/Gerald_Teschl), *Mathematical Methods in Quantum Mechanics with Applications to Schrödinger Operators*, [https://www.mat.univie.ac.at/~gerald/ftp/book-schroe/](https://www.mat.univie.ac.at/~gerald/ftp/book-schroe/), American Mathematical Society, 2009.
