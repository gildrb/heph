[[linear-algebra.base]]

> Source: [[Eigenvalues and Eigenvectors]]
> License: Wikipedia content is available under CC BY-SA 4.0.

In [linear algebra](https://en.wikipedia.org/wiki/Linear_algebra), an **eigenvector** ([/ˈaɪɡən-/](https://en.wikipedia.org/wiki/Help:IPA/English) [*EYE-gən-*](https://en.wikipedia.org/wiki/Help:Pronunciation_respelling_key)) or **characteristic vector** is a (nonzero) [vector](https://en.wikipedia.org/wiki/Vector_(mathematics_and_physics) "Vector (mathematics and physics)") that has its [direction](https://en.wikipedia.org/wiki/Direction_(geometry) "Direction (geometry)") unchanged (or reversed) by a given [linear transformation](https://en.wikipedia.org/wiki/Linear_map). More precisely, an eigenvector $\mathbf {v}$ of a linear transformation $T$ is [scaled by a constant factor](https://en.wikipedia.org/wiki/Scalar_multiplication) $\lambda$ when the linear transformation is applied to it: $T\mathbf {v} =\lambda \mathbf {v}$. The corresponding **eigenvalue**, **characteristic value**, or **characteristic root** is the multiplying factor $\lambda$ (possibly a [negative](https://en.wikipedia.org/wiki/Negative_number) or [complex](https://en.wikipedia.org/wiki/Complex_number) number).

[Geometrically, vectors](https://en.wikipedia.org/wiki/Euclidean_vector) are multi-[dimensional](https://en.wikipedia.org/wiki/Dimension) quantities with magnitude and direction, often pictured as arrows. A linear transformation [rotates](https://en.wikipedia.org/wiki/Rotation_(mathematics) "Rotation (mathematics)"), [stretches](https://en.wikipedia.org/wiki/Scaling_(geometry) "Scaling (geometry)"), or [shears](https://en.wikipedia.org/wiki/Shear_mapping) the vectors upon which it acts. A linear transformation's eigenvectors are those vectors that are only stretched or shrunk, with neither rotation nor shear. The corresponding eigenvalue is the factor by which an eigenvector is stretched or shrunk. If the eigenvalue is negative, the eigenvector's direction is reversed.

The eigenvectors and eigenvalues of a linear transformation serve to characterize it, and so they play important roles in all areas where linear algebra is applied, from [geology](https://en.wikipedia.org/wiki/Geology) to [quantum mechanics](https://en.wikipedia.org/wiki/Quantum_mechanics). In particular, it is often the case that a system is represented by a linear transformation whose outputs are fed as inputs to the same transformation ([feedback](https://en.wikipedia.org/wiki/Feedback)). In such an application, the largest eigenvalue is of particular importance, because it governs the long-term behavior of the system after many applications of the linear transformation, and the associated eigenvector is the [steady state](https://en.wikipedia.org/wiki/Steady_state) of the system.

## Matrices

For an $n{\times }n$ matrix A and a nonzero $n$-vector $\mathbf {v}$, if multiplying A by $\mathbf {v}$ (denoted $A\mathbf {v}$) simply scales $\mathbf {v}$ by a factor λ, where λ is a [scalar](https://en.wikipedia.org/wiki/Scalar_(mathematics) "Scalar (mathematics)"), then $\mathbf {v}$ is called an eigenvector of A, and λ is the corresponding eigenvalue. This relationship can be expressed as: $A\mathbf {v} =\lambda \mathbf {v}$.

Given an [*n*-dimensional vector space](https://en.wikipedia.org/wiki/Dimension_(vector_space) "Dimension (vector space)") and a choice of [basis](https://en.wikipedia.org/wiki/Basis_(linear_algebra) "Basis (linear algebra)"), there is a direct correspondence between linear transformations from the vector space into itself and *n*-by-*n* [square matrices](https://en.wikipedia.org/wiki/Square_matrix). Hence, in a finite-dimensional vector space, it is equivalent to define eigenvalues and eigenvectors using either the language of linear transformations, or the language of [matrices](https://en.wikipedia.org/wiki/Matrix_(mathematics) "Matrix (mathematics)").

## Overview

Eigenvalues and eigenvectors feature prominently in the analysis of linear transformations. The prefix *[eigen-](https://en.wiktionary.org/wiki/eigen-)* is adopted from the [German](https://en.wikipedia.org/wiki/German_language) [eigen](https://en.wiktionary.org/wiki/eigen#German) ([cognate](https://en.wikipedia.org/wiki/Cognate) with the [English](https://en.wikipedia.org/wiki/English_language) word *[own](https://en.wiktionary.org/wiki/own#English)*) for 'proper', 'characteristic', 'own'. Originally used to study [principal axes](https://en.wikipedia.org/wiki/Principal_axis_(mechanics)) of the rotational motion of [rigid bodies](https://en.wikipedia.org/wiki/Rigid_body), eigenvalues and eigenvectors have a wide range of applications, for example in [stability analysis](https://en.wikipedia.org/wiki/Stability_theory), [vibration analysis](https://en.wikipedia.org/wiki/Vibration_analysis#eigenvalue_problem), [atomic orbitals](https://en.wikipedia.org/wiki/Atomic_orbital), [facial recognition](https://en.wikipedia.org/wiki/Eigenface), and [matrix diagonalization](https://en.wikipedia.org/wiki/Eigendecomposition_of_a_matrix).

In essence, an eigenvector **v** of a linear transformation T is a nonzero vector that, when T is applied to it, does not change direction. Applying T to the eigenvector only scales the eigenvector by the scalar value λ, called an eigenvalue. This condition can be written as the equation 

$$
T(\mathbf {v} )=\lambda \mathbf {v} ,
$$

 referred to as the **eigenvalue equation** or **eigenequation**. In general, λ may be any [scalar](https://en.wikipedia.org/wiki/Scalar_(mathematics) "Scalar (mathematics)"). For example, λ may be negative, in which case the eigenvector reverses direction as part of the scaling, or it may be zero or [complex](https://en.wikipedia.org/wiki/Complex_number).

![[media/133410110a2be4cef92b5c82a44d948f73ae3cbc.png]]
In this [shear mapping](https://en.wikipedia.org/wiki/Shear_mapping) the red arrow changes direction, but the blue arrow does not. The blue arrow is an eigenvector of this shear mapping because it does not change direction, and since its length is unchanged, its eigenvalue is 1.

![[media/cfad6a09dbe253916d95c2620c5ee0497ea9f4eb.gif]]
A 2 × 2 real and symmetric matrix representing a stretching and shearing of the plane. The eigenvectors of the matrix (red lines) are the two special directions such that every point on them will just slide on them.

The example here, based on the [Mona Lisa](https://en.wikipedia.org/wiki/Mona_Lisa), provides a simple illustration. Each point on the painting can be represented as a vector pointing from the center of the painting to that point. The linear transformation in this example is called a [shear mapping](https://en.wikipedia.org/wiki/Shear_mapping). Points in the top half are moved to the right, and points in the bottom half are moved to the left, proportional to how far they are from the horizontal axis that goes through the middle of the painting. The vectors pointing to each point in the original image are therefore tilted right or left, and made longer or shorter by the transformation. Points *along* the horizontal axis do not move at all when this transformation is applied. Therefore, any vector that points directly to the right or left with no vertical component is an eigenvector of this transformation, because the mapping does not change its direction. Moreover, these eigenvectors all have an eigenvalue equal to one, because the mapping does not change their length either.

Linear transformations can take many different forms, mapping vectors in a variety of vector spaces, so the eigenvectors can also take many forms. For example, the linear transformation could be a [differential operator](https://en.wikipedia.org/wiki/Differential_operator) like ${\tfrac {d}{dx}}$, in which case the eigenvectors are functions called [eigenfunctions](https://en.wikipedia.org/wiki/Eigenfunction) that are scaled by that differential operator, such as 

$$
{\frac {d}{dx}}e^{\lambda x}=\lambda e^{\lambda x}.
$$

 Alternatively, the linear transformation could take the form of an n × n matrix, in which case the eigenvectors are n × 1 matrices. If the linear transformation is expressed in the form of an *n* × *n* matrix A, then the eigenvalue equation for a linear transformation above can be rewritten as the matrix multiplication 

$$
A\mathbf {v} =\lambda \mathbf {v} ,
$$

 where the eigenvector v is an n × 1 matrix. For a matrix, eigenvalues and eigenvectors can be used to [decompose the matrix](https://en.wikipedia.org/wiki/Matrix_decomposition)—for example by [diagonalizing](https://en.wikipedia.org/wiki/Diagonalizable_matrix) it.

Eigenvalues and eigenvectors give rise to many closely related mathematical concepts, and the prefix *eigen-* is applied liberally when naming them:

- The set of all eigenvectors of a linear transformation, each paired with its corresponding eigenvalue, is called the **eigensystem** of that transformation.
- The set of all eigenvectors of T corresponding to the same eigenvalue, together with the zero vector, is called an **eigenspace**, or the **characteristic space** of T associated with that eigenvalue.
- If a set of eigenvectors of T forms a [basis](https://en.wikipedia.org/wiki/Basis_(linear_algebra) "Basis (linear algebra)") of the domain of T, then this basis is called an **eigenbasis**.

## History

Eigenvalues are often introduced in the context of [linear algebra](https://en.wikipedia.org/wiki/Linear_algebra) or [matrix theory](https://en.wikipedia.org/wiki/Matrix_(mathematics) "Matrix (mathematics)"). Historically, however, they arose in the study of [quadratic forms](https://en.wikipedia.org/wiki/Quadratic_form) and [differential equations](https://en.wikipedia.org/wiki/Differential_equation).

In the 18th century, [Leonhard Euler](https://en.wikipedia.org/wiki/Leonhard_Euler) studied the rotational motion of a [rigid body](https://en.wikipedia.org/wiki/Rigid_body), and discovered the importance of the [principal axes](https://en.wikipedia.org/wiki/Moment_of_inertia#Principal_axes). [Joseph-Louis Lagrange](https://en.wikipedia.org/wiki/Joseph-Louis_Lagrange) realized that the principal axes are the eigenvectors of the inertia matrix.

In the early 19th century, [Augustin-Louis Cauchy](https://en.wikipedia.org/wiki/Augustin-Louis_Cauchy) saw how their work could be used to classify the [quadric surfaces](https://en.wikipedia.org/wiki/Quadric), and generalized it to arbitrary dimensions. Cauchy also coined the term *racine caractéristique* (characteristic root), for what is now called *eigenvalue*; his term survives in *[characteristic equation](https://en.wikipedia.org/wiki/Characteristic_polynomial)*.

Later, [Joseph Fourier](https://en.wikipedia.org/wiki/Joseph_Fourier) used the work of Lagrange and [Pierre-Simon Laplace](https://en.wikipedia.org/wiki/Pierre-Simon_Laplace) to solve the [heat equation](https://en.wikipedia.org/wiki/Heat_equation) by [separation of variables](https://en.wikipedia.org/wiki/Separation_of_variables) in his 1822 treatise *[The Analytic Theory of Heat (Théorie analytique de la chaleur)](https://en.wikipedia.org/wiki/Joseph_Fourier#The_Analytic_Theory_of_Heat)*. [Charles-François Sturm](https://en.wikipedia.org/wiki/Charles-Fran%C3%A7ois_Sturm) elaborated on Fourier's ideas further, and brought them to the attention of Cauchy, who combined them with his own ideas and arrived at the fact that real [symmetric matrices](https://en.wikipedia.org/wiki/Symmetric_matrix) have real eigenvalues. This was extended by [Charles Hermite](https://en.wikipedia.org/wiki/Charles_Hermite) in 1855 to what are now called [Hermitian matrices](https://en.wikipedia.org/wiki/Hermitian_matrix).

Around the same time, [Francesco Brioschi](https://en.wikipedia.org/wiki/Francesco_Brioschi) proved that the eigenvalues of [orthogonal matrices](https://en.wikipedia.org/wiki/Orthogonal_matrix) lie on the [unit circle](https://en.wikipedia.org/wiki/Unit_circle), and [Alfred Clebsch](https://en.wikipedia.org/wiki/Alfred_Clebsch) found the corresponding result for [skew-symmetric matrices](https://en.wikipedia.org/wiki/Skew-symmetric_matrix). Finally, [Karl Weierstrass](https://en.wikipedia.org/wiki/Karl_Weierstrass) clarified an important aspect in the [stability theory](https://en.wikipedia.org/wiki/Stability_theory) started by Laplace, by realizing that [defective matrices](https://en.wikipedia.org/wiki/Defective_matrix) can cause instability.

In the meantime, [Joseph Liouville](https://en.wikipedia.org/wiki/Joseph_Liouville) studied eigenvalue problems similar to those of Sturm; the discipline that grew out of their work is now called *[Sturm–Liouville theory](https://en.wikipedia.org/wiki/Sturm%E2%80%93Liouville_theory)*. [Schwarz](https://en.wikipedia.org/wiki/Hermann_Schwarz) studied the first eigenvalue of [Laplace's equation](https://en.wikipedia.org/wiki/Laplace%27s_equation) on general domains towards the end of the 19th century, while [Poincaré](https://en.wikipedia.org/wiki/Henri_Poincar%C3%A9) studied [Poisson's equation](https://en.wikipedia.org/wiki/Poisson%27s_equation) a few years later.

At the start of the 20th century, [David Hilbert](https://en.wikipedia.org/wiki/David_Hilbert) studied the eigenvalues of [integral operators](https://en.wikipedia.org/wiki/Integral_operator) by viewing the operators as infinite matrices. He was the first to use the [German](https://en.wikipedia.org/wiki/German_language) word *eigen*, which means "own", to denote eigenvalues and eigenvectors in 1904, though he may have been following a related usage by [Hermann von Helmholtz](https://en.wikipedia.org/wiki/Hermann_von_Helmholtz). For some time, the standard term in English was "proper value", but the more distinctive term "eigenvalue" is the standard today.

The first numerical algorithm for computing eigenvalues and eigenvectors appeared in 1929, when [Richard von Mises](https://en.wikipedia.org/wiki/Richard_von_Mises) published the [power method](https://en.wikipedia.org/wiki/Power_method). One of the most popular methods today, the [QR algorithm](https://en.wikipedia.org/wiki/QR_algorithm), was proposed independently by [John G. F. Francis](https://en.wikipedia.org/wiki/John_G._F._Francis) and [Vera Kublanovskaya](https://en.wikipedia.org/wiki/Vera_Kublanovskaya) in 1961.

## Eigenvalues and eigenvectors of matrices

Eigenvalues and eigenvectors are often introduced to students in the context of linear algebra courses focused on matrices. Furthermore, linear transformations over a finite-dimensional vector space can be represented using matrices, which is especially common in numerical and computational applications.

![[media/04a28b1ce0974e19cf8255fa7b5c899bc2a91fd5.png]]
Matrix A acts by stretching the vector <strong>x</strong>, not changing its direction, so <strong>x</strong> is an eigenvector of A.

Consider n-dimensional vectors that are formed as a list of n scalars, such as the three-dimensional vectors 

$$
\mathbf {x} ={\begin{bmatrix}1\\-3\\4\end{bmatrix}}\quad {\mbox{and}}\quad \mathbf {y} ={\begin{bmatrix}-20\\60\\-80\end{bmatrix}}.
$$

These vectors are said to be [scalar multiples](https://en.wikipedia.org/wiki/Scalar_multiplication) of each other, or [parallel](https://en.wikipedia.org/wiki/Parallel_(geometry) "Parallel (geometry)") or [collinear](https://en.wikipedia.org/wiki/Collinearity), if there is a scalar λ such that 

$$
\mathbf {x} =\lambda \mathbf {y} .
$$

In this case, $\lambda =-{\frac {1}{20}}$.

Now consider the linear transformation of n-dimensional vectors defined by an n-by-n matrix A, 

$$
A\mathbf {v} =\mathbf {w} ,
$$

 or 

$$
{\begin{bmatrix}A_{11}&A_{12}&\cdots &A_{1n}\\A_{21}&A_{22}&\cdots &A_{2n}\\\vdots &\vdots &\ddots &\vdots \\A_{n1}&A_{n2}&\cdots &A_{nn}\\\end{bmatrix}}{\begin{bmatrix}v_{1}\\v_{2}\\\vdots \\v_{n}\end{bmatrix}}={\begin{bmatrix}w_{1}\\w_{2}\\\vdots \\w_{n}\end{bmatrix}}
$$

 where, for each row, 

$$
w_{i}=A_{i1}v_{1}+A_{i2}v_{2}+\cdots +A_{in}v_{n}=\sum _{j=1}^{n}A_{ij}v_{j}.
$$

If it occurs that v and w are scalar multiples, that is if

|  |  |  |
|----|----|----|
| $A\mathbf {v} =\mathbf {w} =\lambda \mathbf {v} ,$ |  | 1 |

then **v** is an **eigenvector** of the linear transformation A and the scale factor λ is the **eigenvalue** corresponding to that eigenvector. Equation (**[1](#math_1)**) is the **eigenvalue equation** for the matrix A.

Equation (**[1](#math_1)**) can be stated equivalently as

|  |  |  |
|----|----|----|
| $\left(A-\lambda I\right)\mathbf {v} =\mathbf {0} ,$ |  | 2 |

where I is the n-by-n [identity matrix](https://en.wikipedia.org/wiki/Identity_matrix) and **0** is the zero vector.

### Eigenvalues and the characteristic polynomial

Equation (**[2](#math_2)**) has a nonzero solution v [if and only if](https://en.wikipedia.org/wiki/If_and_only_if) the [[Determinant]] of the matrix (*A* − *λI*) is zero. Therefore, the eigenvalues of A are values of λ that satisfy the equation

|  |  |  |
|----|----|----|
| $\det(A-\lambda I)=0$ |  | 3 |

Using the [Leibniz formula for determinants](https://en.wikipedia.org/wiki/Leibniz_formula_for_determinants), the left-hand side of equation (**[3](#math_3)**) is a [polynomial](https://en.wikipedia.org/wiki/Polynomial) function of the variable λ and the [degree](https://en.wikipedia.org/wiki/Degree_of_a_polynomial) of this polynomial is n, the order of the matrix A. Its [coefficients](https://en.wikipedia.org/wiki/Coefficient) depend on the entries of A, except that its term of degree n is always (−1)<sup>*n*</sup>*λ*<sup>*n*</sup>. This polynomial is called the *characteristic polynomial* of A. Equation (**[3](#math_3)**) is called the *characteristic equation* or the *secular equation* of A.

The characteristic polynomial of an n-by-n matrix A, being a polynomial of degree n, has at most n [complex number](https://en.wikipedia.org/wiki/Complex_number) roots, which can be found by factoring the characteristic polynomial, or numerically by root finding. The characteristic polynomial can be [factored](https://en.wikipedia.org/wiki/Factorization) into the product of n linear terms,

|  |  |  |
|----|----|----|
| $\det(A-\lambda I)=(\lambda _{1}-\lambda )(\lambda _{2}-\lambda )\cdots (\lambda _{n}-\lambda ),$ |  | 4 |

where the complex numbers *λ*<sub>1</sub>, *λ*<sub>2</sub>, ... , *λ*<sub>*n*</sub>, each of which is an eigenvalue, may not all be distinct. (The number of times an eigenvalue appears is known as its [algebraic multiplicity](#Algebraic_multiplicity).)

As a brief example, which is described in more detail in the examples section later, consider the matrix 

$$
A={\begin{bmatrix}2&1\\1&2\end{bmatrix}}.
$$

Taking the determinant of (*A* − *λI*), the characteristic polynomial of A is 

$$
\det(A-\lambda I)={\begin{vmatrix}2-\lambda &1\\1&2-\lambda \end{vmatrix}}=3-4\lambda +\lambda ^{2}.
$$

Setting the characteristic polynomial equal to zero, it has roots at *λ* = 1 and *λ* = 3, which are the two eigenvalues of A. The eigenvectors corresponding to each eigenvalue λ can be found by solving for the components of **v** in the equation (*A* − *λI*)**v** = **0**. In this example, the eigenvectors are any nonzero scalar multiples of 

$$
\mathbf {v} _{\lambda =1}={\begin{bmatrix}1\\-1\end{bmatrix}},\quad \mathbf {v} _{\lambda =3}={\begin{bmatrix}1\\1\end{bmatrix}}.
$$

If the entries of the matrix A are all real numbers, then the coefficients of the characteristic polynomial will also be real numbers, but the eigenvalues may still have nonzero imaginary parts. The entries of the corresponding eigenvectors therefore may also have nonzero imaginary parts. Similarly, the eigenvalues may be [irrational numbers](https://en.wikipedia.org/wiki/Irrational_number) even if all the entries of A are [rational numbers](https://en.wikipedia.org/wiki/Rational_number) or even if they are all integers. However, if the entries of A are all [algebraic numbers](https://en.wikipedia.org/wiki/Algebraic_number), which include the rationals, the eigenvalues must also be algebraic numbers.

The non-real roots of a real polynomial with real coefficients can be grouped into pairs of [complex conjugates](https://en.wikipedia.org/wiki/Complex_conjugate), namely with the two members of each pair having imaginary parts that differ only in sign and the same real part. If the degree is odd, then by the [intermediate value theorem](https://en.wikipedia.org/wiki/Intermediate_value_theorem) at least one of the roots is real. Therefore, any [real matrix](https://en.wikipedia.org/wiki/Real_matrix) with odd order has at least one real eigenvalue, whereas a real matrix with even order may not have any real eigenvalues. The eigenvectors associated with these complex eigenvalues are also complex and also appear in complex conjugate pairs.

### Spectrum of a matrix

The **[spectrum](https://en.wikipedia.org/wiki/Spectrum_of_a_matrix)** of a matrix is the list of eigenvalues, repeated according to multiplicity; in an alternative notation the set of eigenvalues with their multiplicities.

An important quantity associated with the spectrum is the maximum absolute value of any eigenvalue. This is known as the [spectral radius](https://en.wikipedia.org/wiki/Spectral_radius#Matrices) of the matrix.

### Algebraic multiplicity

Let *λ*<sub>*i*</sub> be an eigenvalue of an n-by-n matrix A. The **algebraic multiplicity** *μ*<sub>*A*</sub>(*λ*<sub>*i*</sub>) of the eigenvalue is its [multiplicity as a root](https://en.wikipedia.org/wiki/Multiple_roots_of_a_polynomial) of the characteristic polynomial, that is, the largest integer k such that (*λ* − *λ*<sub>*i*</sub>)<sup>*k*</sup> [evenly divides](https://en.wikipedia.org/wiki/Polynomial_division) that polynomial.

Suppose a matrix A has dimension n and *d* ≤ *n* distinct eigenvalues. Whereas equation (**[4](#math_4)**) factors the characteristic polynomial of A into the product of n linear terms with some terms potentially repeating, the characteristic polynomial can also be written as the product of d terms each corresponding to a distinct eigenvalue and raised to the power of the algebraic multiplicity, 

$$
\det(A-\lambda I)=(\lambda _{1}-\lambda )^{\mu _{A}(\lambda _{1})}(\lambda _{2}-\lambda )^{\mu _{A}(\lambda _{2})}\cdots (\lambda _{d}-\lambda )^{\mu _{A}(\lambda _{d})}.
$$

If *d* = *n* then the right-hand side is the product of n linear terms, and this is the same as equation (**[4](#math_4)**). The size of each eigenvalue's algebraic multiplicity is related to the dimension n as 

$$
{\begin{aligned}1&\leq \mu _{A}(\lambda _{i})\leq n,\\\mu _{A}&=\sum _{i=1}^{d}\mu _{A}\left(\lambda _{i}\right)=n.\end{aligned}}
$$

If *μ*<sub>*A*</sub>(*λ*<sub>*i*</sub>) = 1, then λ<sub>i</sub> is said to be a *simple eigenvalue*. If *μ*<sub>*A*</sub>(*λ*<sub>*i*</sub>) equals the geometric multiplicity of λ<sub>i</sub>, *γ*<sub>*A*</sub>(*λ*<sub>*i*</sub>), defined in the next section, then λ<sub>i</sub> is said to be a *semisimple eigenvalue*.

### Eigenspaces, geometric multiplicity, and the eigenbasis for matrices

Given a particular eigenvalue λ of the n × n matrix A, define the [set](https://en.wikipedia.org/wiki/Set_(mathematics) "Set (mathematics)") E to be all vectors **v** that satisfy equation (**[2](#math_2)**), 

$$
E=\left\{\mathbf {v} :\left(A-\lambda I\right)\mathbf {v} =\mathbf {0} \right\}.
$$

On one hand, this set is precisely the [kernel](https://en.wikipedia.org/wiki/Kernel_(linear_algebra) "Kernel (linear algebra)") or nullspace of the matrix *A* − *λI*. On the other hand, by definition, any nonzero vector that satisfies this condition is an eigenvector of A associated with λ. So, the set E is the [union](https://en.wikipedia.org/wiki/Union_(set_theory) "Union (set theory)") of the zero vector with the set of all eigenvectors of A associated with λ, and E equals the nullspace of *A* − *λI*. The space E is called the **eigenspace** or **characteristic space** of A associated with λ. In general λ is a complex number and the eigenvectors are complex n × 1 matrices (column vectors). Because every nullspace is a [linear subspace](https://en.wikipedia.org/wiki/Linear_subspace) of the domain, E is a linear subspace of $\mathbb {C} ^{n}$.

Because the eigenspace E is a linear subspace, it is [closed](https://en.wikipedia.org/wiki/Closure_(mathematics) "Closure (mathematics)") under addition. That is, if two vectors **u** and **v** belong to the set E, written **u**, **v** ∈ *E*, then **u** + **v** ∈ *E* or equivalently *A*(**u** + **v**) = *λ*(**u** + **v**). This can be checked using the [distributive property](https://en.wikipedia.org/wiki/Distributive_property) of matrix multiplication. Similarly, because E is a linear subspace, it is closed under scalar multiplication. That is, if **v** ∈ *E* and α is a complex number, *α***v** ∈ *E* or equivalently *A*(*α***v**) = *λ*(*α***v**). This can be checked by noting that multiplication of complex matrices by complex numbers is [commutative](https://en.wikipedia.org/wiki/Commutative_property). As long as **u** + **v** and *α***v** are not zero, they are also eigenvectors of A associated with λ.

The dimension of the eigenspace E associated with λ, or equivalently the maximum number of linearly independent eigenvectors associated with λ, is referred to as the eigenvalue's **geometric multiplicity** $\gamma _{A}(\lambda )$. Because E is also the nullspace of *A* − *λI*, the geometric multiplicity of λ is the dimension of the nullspace of *A* − *λI*, also called the *nullity* of *A* − *λI*. This quantity is related to the size and rank of *A* − *λI* by the equation 

$$
\gamma _{A}(\lambda )=n-\operatorname {rank} (A-\lambda I).
$$

Because of the definition of eigenvalues and eigenvectors, an eigenvalue's geometric multiplicity must be at least one, that is, each eigenvalue has at least one associated eigenvector. Furthermore, an eigenvalue's geometric multiplicity cannot exceed its algebraic multiplicity. Additionally, recall that an eigenvalue's algebraic multiplicity cannot exceed n. 

$$
1\leq \gamma _{A}(\lambda )\leq \mu _{A}(\lambda )\leq n
$$

To prove the inequality $\gamma _{A}(\lambda )\leq \mu _{A}(\lambda )$, let *B* = *A* − *λI*, where λ is a fixed complex number, and the eigenspace associated with λ is the nullspace of B. Let the dimension of that eigenspace be $k=\gamma _{A}(\lambda )$. This means that the last k rows of the echelon form of B are zero. Thus, there is an invertible matrix E coming from Gauss-Jordan reduction, such that 

$$
EB={\begin{bmatrix}*&*\\\mathbf {0} _{k\times (n-k)}&\mathbf {0} _{k\times k}\end{bmatrix}}.
$$

 Therefore the last k rows of *EB* − *tE* are (−*t*) times the last k rows of E. Therefore the polynomial t<sup>k</sup> evenly divides the polynomial det(*EB* − *tE*), because of basic properties of determinants (homogeneity). On the other hand, det(*EB* − *tE*) = det *E* det(*B* − *tI*) = *p<sub>A</sub>*(*t* + *λ*) det *E*, so (*t* − *λ*)<sup>*k*</sup> divides *p<sub>A</sub>*(*t*), and so the algebraic multiplicity of λ is at least k.

Suppose A has *d* ≤ *n* distinct eigenvalues *λ*<sub>1</sub>, ... , *λ*<sub>*d*</sub>, where the geometric multiplicity of λ<sub>i</sub> is *γ<sub>A</sub>*(*λ<sub>i</sub>*). The total geometric multiplicity of A, 

$$
\gamma _{A}=\sum _{i=1}^{d}\gamma _{A}(\lambda _{i}),\quad d\leq \gamma _{A}\leq n,
$$

is the dimension of the [sum](https://en.wikipedia.org/wiki/Linear_subspace#Sum) of all the eigenspaces of A's eigenvalues, or equivalently the maximum number of linearly independent eigenvectors of A. If $\gamma _{A}=n$, then

- The direct sum of the eigenspaces of all of A's eigenvalues is the entire vector space $\mathbb {C} ^{n}$.
- A basis of $\mathbb {C} ^{n}$ can be formed from n linearly independent eigenvectors of A; such a basis is called an **eigenbasis**
- Any vector in $\mathbb {C} ^{n}$ can be written as a linear combination of eigenvectors of A.

### Additional properties

Let A be an arbitrary n × n matrix of complex numbers with eigenvalues *λ*<sub>1</sub>, ... , *λ<sub>n</sub>*. Each eigenvalue appears *μ<sub>A</sub>*( *λ<sub>i</sub>* ) times in this list, where *μ<sub>A</sub>*(*λ<sub>i</sub>*) is the eigenvalue's algebraic multiplicity. The following are properties of this matrix and its eigenvalues:

- The [trace](https://en.wikipedia.org/wiki/Trace_(linear_algebra) "Trace (linear algebra)") of A, defined as the sum of its diagonal elements, is also the sum of all eigenvalues, 

$$
\operatorname {tr} (A)=\sum _{i=1}^{n}a_{ii}=\sum _{i=1}^{n}\lambda _{i}=\lambda _{1}+\lambda _{2}+\cdots +\lambda _{n}.
$$

- The [[Determinant]] of A is the product of all its eigenvalues, 

$$
\det(A)=\prod _{i=1}^{n}\lambda _{i}=\lambda _{1}\lambda _{2}\cdots \lambda _{n}.
$$

- The eigenvalues of the kth power of A; i.e., the eigenvalues of A<sup>k</sup>, for any positive integer k, are *λ* *k*  
  1 , ... , *λ* *k*  
  *n* .
- The matrix A is [invertible](https://en.wikipedia.org/wiki/Invertible_matrix) if and only if every eigenvalue is nonzero.
- If A is invertible, then the eigenvalues of *A*<sup>−1</sup> are ${\frac {1}{\lambda _{1}}},\ldots ,{\frac {1}{\lambda _{n}}}$ and each eigenvalue's geometric multiplicity coincides. Moreover, since the characteristic polynomial of the inverse is the [reciprocal polynomial](https://en.wikipedia.org/wiki/Reciprocal_polynomial) of the original up to a scalar factor, the eigenvalues share the same algebraic multiplicity.
- If A is equal to its [conjugate transpose](https://en.wikipedia.org/wiki/Conjugate_transpose) *A*<sup>∗</sup>, or equivalently if A is [Hermitian](https://en.wikipedia.org/wiki/Hermitian_matrix), then every eigenvalue is real. The same is true of any [symmetric](https://en.wikipedia.org/wiki/Symmetric_matrix) real matrix.
- If A is not only Hermitian but also [[Positive-Definite Matrix|positive-definite]], positive-semidefinite, negative-definite, or negative-semidefinite, then every eigenvalue is positive, non-negative, negative, or non-positive, respectively.
- If A is [unitary](https://en.wikipedia.org/wiki/Unitary_matrix), every eigenvalue has absolute value \|*λ<sub>i</sub>*\| = 1.
- If A is a n × n matrix and {*λ*<sub>1</sub>, ... , *λ<sub>k</sub>*} are its eigenvalues, then the eigenvalues of matrix *I* + *A* (where I is the identity matrix) are {*λ*<sub>1</sub> + 1, ... , *λ*<sub>*k*</sub> + 1}. Moreover, if $\alpha \in \mathbb {C}$, the eigenvalues of *αI* + *A* are {*λ*<sub>1</sub> + *α*, ... , *λ*<sub>*k*</sub> + *α*}. More generally, for a polynomial P the eigenvalues of matrix *P*(*A*) are {*P*(*λ*<sub>1</sub>), ... , *P*(*λ*<sub>*k*</sub>)}.

### Left and right eigenvectors

Many disciplines traditionally represent vectors as matrices with a single column rather than as matrices with a single row. For that reason, the word "eigenvector" in the context of matrices almost always refers to a **right eigenvector**, namely a *column* vector that *right* multiplies the n × n matrix A in the defining equation, equation (**[1](#math_1)**), 

$$
A\mathbf {v} =\lambda \mathbf {v} .
$$

The eigenvalue and eigenvector problem can also be defined for *row* vectors that *left* multiply matrix A. In this formulation, the defining equation is 

$$
\mathbf {u} A=\kappa \mathbf {u} ,
$$

where κ is a scalar and **u** is a 1 × n matrix. Any row vector **u** satisfying this equation is called a **left eigenvector** of A and κ is its associated eigenvalue. Taking the transpose of this equation, 

$$
A^{\textsf {T}}\mathbf {u} ^{\textsf {T}}=\kappa \mathbf {u} ^{\textsf {T}}.
$$

Comparing this equation to equation (**[1](#math_1)**), it follows immediately that a left eigenvector of A is the same as the transpose of a right eigenvector of *A*<sup>T</sup>, with the same eigenvalue. Furthermore, since the characteristic polynomial of *A*<sup>T</sup> is the same as the characteristic polynomial of A, the left and right eigenvectors of A are associated with the same eigenvalues.

### Diagonalization and the eigendecomposition

Suppose the eigenvectors of A form a basis, or equivalently A has n linearly independent eigenvectors **v**<sub>1</sub>, **v**<sub>2</sub>, ..., **v**<sub>*n*</sub> with associated eigenvalues *λ*<sub>1</sub>, *λ*<sub>2</sub>, ..., *λ*<sub>*n*</sub>. The eigenvalues need not be distinct. Define a [square matrix](https://en.wikipedia.org/wiki/Square_matrix) Q whose columns are the n linearly independent eigenvectors of A, 

$$
Q={\begin{bmatrix}\mathbf {v} _{1}&\mathbf {v} _{2}&\cdots &\mathbf {v} _{n}\end{bmatrix}}.
$$

Since each column of Q is an eigenvector of A, right multiplying A by Q scales each column of Q by its associated eigenvalue, 

$$
AQ={\begin{bmatrix}\lambda _{1}\mathbf {v} _{1}&\lambda _{2}\mathbf {v} _{2}&\cdots &\lambda _{n}\mathbf {v} _{n}\end{bmatrix}}.
$$

With this in mind, define a diagonal matrix Λ where each diagonal element Λ<sub>*ii*</sub> is the eigenvalue associated with the ith column of Q. Then 

$$
AQ=Q\Lambda .
$$

Because the columns of Q are linearly independent, Q is invertible. Right multiplying both sides of the equation by *Q*<sup>−1</sup>, 

$$
A=Q\Lambda Q^{-1},
$$

 or by instead left multiplying both sides by *Q*<sup>−1</sup>, 

$$
Q^{-1}AQ=\Lambda .
$$

A can therefore be decomposed into a matrix composed of its eigenvectors, a diagonal matrix with its eigenvalues along the diagonal, and the inverse of the matrix of eigenvectors. This is called the [[Eigendecomposition]] and it is a [similarity transformation](https://en.wikipedia.org/wiki/Matrix_similarity). Such a matrix A is said to be *similar* to the diagonal matrix Λ or *[diagonalizable](https://en.wikipedia.org/wiki/Diagonalizable)*. The matrix Q is the change of basis matrix of the similarity transformation. Essentially, the matrices A and Λ represent the same linear transformation expressed in two different bases. The eigenvectors are used as the basis when representing the linear transformation as Λ.

Conversely, suppose a matrix A is diagonalizable. Let P be a non-singular square matrix such that *P*<sup>−1</sup>*AP* is some diagonal matrix D. Left multiplying both by P, *AP* = *PD*. Each column of P must therefore be an eigenvector of A whose eigenvalue is the corresponding diagonal element of D. Since the columns of P must be linearly independent for P to be invertible, there exist n linearly independent eigenvectors of A. It then follows that the eigenvectors of A form a basis if and only if A is diagonalizable.

A matrix that is not diagonalizable is said to be [defective](https://en.wikipedia.org/wiki/Defective_matrix). For defective matrices, the notion of eigenvectors generalizes to [generalized eigenvectors](https://en.wikipedia.org/wiki/Generalized_eigenvector) and the diagonal matrix of eigenvalues generalizes to the [Jordan normal form](https://en.wikipedia.org/wiki/Jordan_normal_form). Over an algebraically closed field, any matrix A has a Jordan normal form and therefore admits a basis of generalized eigenvectors and a decomposition into [generalized eigenspaces](https://en.wikipedia.org/wiki/Generalized_eigenspace).

### Variational characterization

In the [Hermitian](https://en.wikipedia.org/wiki/Hermitian_matrix) case, eigenvalues can be given a variational characterization. The largest eigenvalue of H is the maximum value of the [quadratic form](https://en.wikipedia.org/wiki/Quadratic_form) **x**<sup>T</sup>*H***x**/**x**<sup>T</sup>**x**. A value of **x** that realizes that maximum is an eigenvector.

### Matrix examples

#### Two-dimensional matrix example

![[media/74cd0f5cd9ea4488de511c5db4af2efa1e5d5346.gif]]
The transformation matrix <em>A</em> = <sup></sup> <sub></sub>⎡⎣<sup>2</sup><br />
<sub>1</sub> <sup>1</sup><br />
<sub>2</sub>⎤⎦<sup></sup> <sub></sub>  preserves the direction of magenta vectors parallel to <strong>v</strong><sub><em>λ</em>=1</sub> = [1 −1]<sup>T</sup> and blue vectors parallel to <strong>v</strong><sub><em>λ</em>=3</sub> = [1 1]<sup>T</sup>. The red vectors are not parallel to either eigenvector, so, their directions are changed by the transformation. The lengths of the magenta vectors are unchanged after the transformation (due to their eigenvalue of 1), while blue vectors are three times the length of the original (due to their eigenvalue of 3). See also: [An extended version, showing all four quadrants](https://en.wikipedia.org/wiki/File:Eigenvectors-extended.gif).

Consider the matrix 

$$
A={\begin{bmatrix}2&1\\1&2\end{bmatrix}}.
$$

The figure on the right shows the effect of this transformation on point coordinates in the plane. The eigenvectors v of this transformation satisfy equation (**[1](#math_1)**), and the values of λ for which the determinant of the matrix (*A* − *λI*) equals zero are the eigenvalues.

Taking the determinant to find characteristic polynomial of A, 

$$
{\begin{aligned}\det(A-\lambda I)&=\left|{\begin{bmatrix}2&1\\1&2\end{bmatrix}}-\lambda {\begin{bmatrix}1&0\\0&1\end{bmatrix}}\right|={\begin{vmatrix}2-\lambda &1\\1&2-\lambda \end{vmatrix}}\\[6pt]&=3-4\lambda +\lambda ^{2}\\[6pt]&=(\lambda -3)(\lambda -1).\end{aligned}}
$$

Setting the characteristic polynomial equal to zero, it has roots at *λ* = 1 and *λ* = 3, which are the two eigenvalues of A.

For *λ* = 1, equation (**[2](#math_2)**) becomes, 

$$
{\begin{aligned}(A-I)\mathbf {v} _{\lambda =1}&={\begin{bmatrix}1&1\\1&1\end{bmatrix}}{\begin{bmatrix}v_{1}\\v_{2}\end{bmatrix}}={\begin{bmatrix}0\\0\end{bmatrix}}\\1v_{1}+1v_{2}&=0\end{aligned}}
$$

Any nonzero vector with *v*<sub>1</sub> = −*v*<sub>2</sub> solves this equation. Therefore, 

$$
\mathbf {v} _{\lambda =1}={\begin{bmatrix}v_{1}\\-v_{1}\end{bmatrix}}={\begin{bmatrix}1\\-1\end{bmatrix}}
$$

 is an eigenvector of A corresponding to *λ* = 1, as is any scalar multiple of this vector.

For *λ* = 3, equation (**[2](#math_2)**) becomes 

$$
{\begin{aligned}(A-3I)\mathbf {v} _{\lambda =3}&={\begin{bmatrix}-1&{\hphantom {-}}1\\{\hphantom {-}}1&-1\end{bmatrix}}{\begin{bmatrix}v_{1}\\v_{2}\end{bmatrix}}={\begin{bmatrix}0\\0\end{bmatrix}}\\-1v_{1}+1v_{2}&=0;\\1v_{1}-1v_{2}&=0\end{aligned}}
$$

Any nonzero vector with *v*<sub>1</sub> = *v*<sub>2</sub> solves this equation. Therefore, 

$$
\mathbf {v} _{\lambda =3}={\begin{bmatrix}v_{1}\\v_{1}\end{bmatrix}}={\begin{bmatrix}1\\1\end{bmatrix}}
$$

 is an eigenvector of A corresponding to *λ* = 3, as is any scalar multiple of this vector.

Thus, the vectors **v**<sub>*λ*=1</sub> and **v**<sub>*λ*=3</sub> are eigenvectors of A associated with the eigenvalues *λ* = 1 and *λ* = 3, respectively.

#### Three-dimensional matrix example

Consider the matrix 

$$
A={\begin{bmatrix}2&0&0\\0&3&4\\0&4&9\end{bmatrix}}.
$$

The characteristic polynomial of A is 

$$
{\begin{aligned}\det(A-\lambda I)&=\left|{\begin{bmatrix}2&0&0\\0&3&4\\0&4&9\end{bmatrix}}-\lambda {\begin{bmatrix}1&0&0\\0&1&0\\0&0&1\end{bmatrix}}\right|={\begin{vmatrix}2-\lambda &0&0\\0&3-\lambda &4\\0&4&9-\lambda \end{vmatrix}},\\[6pt]&=(2-\lambda ){\bigl [}(3-\lambda )(9-\lambda )-16{\bigr ]}=-\lambda ^{3}+14\lambda ^{2}-35\lambda +22.\end{aligned}}
$$

The roots of the characteristic polynomial are 2, 1, and 11, which are the only three eigenvalues of A. These eigenvalues correspond to the eigenvectors \[1 0 0\]<sup>T</sup>, \[0 −2 1\]<sup>T</sup>, and \[0 1 2\]<sup>T</sup>, or any nonzero multiple thereof.

#### Three-dimensional matrix example with complex eigenvalues

Consider the [cyclic permutation matrix](https://en.wikipedia.org/wiki/Permutation_matrix) 

$$
A={\begin{bmatrix}0&1&0\\0&0&1\\1&0&0\end{bmatrix}}.
$$

This matrix shifts the coordinates of the vector up by one position and moves the first coordinate to the bottom. Its characteristic polynomial is 1 − *λ*<sup>3</sup>, whose roots are 

$$
{\begin{aligned}\lambda _{1}&=1\\\lambda _{2}&=-{\frac {1}{2}}+i{\frac {\sqrt {3}}{2}}\\\lambda _{3}&=\lambda _{2}^{*}=-{\frac {1}{2}}-i{\frac {\sqrt {3}}{2}}\end{aligned}}
$$

 where i is an [imaginary unit](https://en.wikipedia.org/wiki/Imaginary_unit) with *i*<sup>2</sup> = −1.

For the real eigenvalue *λ*<sub>1</sub> = 1, any vector with three equal nonzero entries is an eigenvector. For example, 

$$
A{\begin{bmatrix}5\\5\\5\end{bmatrix}}={\begin{bmatrix}5\\5\\5\end{bmatrix}}=1\cdot {\begin{bmatrix}5\\5\\5\end{bmatrix}}.
$$

For the complex conjugate pair of imaginary eigenvalues, 

$$
\lambda _{2}\lambda _{3}=1,\quad \lambda _{2}^{2}=\lambda _{3},\quad \lambda _{3}^{2}=\lambda _{2}.
$$

Then 

$$
A{\begin{bmatrix}1\\\lambda _{2}\\\lambda _{3}\end{bmatrix}}={\begin{bmatrix}\lambda _{2}\\\lambda _{3}\\1\end{bmatrix}}=\lambda _{2}\cdot {\begin{bmatrix}1\\\lambda _{2}\\\lambda _{3}\end{bmatrix}},
$$

 and 

$$
A{\begin{bmatrix}1\\\lambda _{3}\\\lambda _{2}\end{bmatrix}}={\begin{bmatrix}\lambda _{3}\\\lambda _{2}\\1\end{bmatrix}}=\lambda _{3}\cdot {\begin{bmatrix}1\\\lambda _{3}\\\lambda _{2}\end{bmatrix}}.
$$

Therefore, the other two eigenvectors of A are complex and are **v**<sub>*λ*<sub>2</sub></sub> = \[1 *λ*<sub>2</sub> *λ*<sub>3</sub>\]<sup>T</sup> and **v**<sub>*λ*<sub>3</sub></sub> = \[1 *λ*<sub>3</sub> *λ*<sub>2</sub>\]<sup>T</sup> with eigenvalues *λ*<sub>2</sub> and *λ*<sub>3</sub>, respectively. The two complex eigenvectors also appear in a complex conjugate pair, 

$$
\mathbf {v} _{\lambda _{2}}=\mathbf {v} _{\lambda _{3}}^{*}.
$$

#### Diagonal matrix example

Matrices with entries only along the main diagonal are called *[diagonal matrices](https://en.wikipedia.org/wiki/Diagonal_matrices)*. The eigenvalues of a diagonal matrix are the diagonal elements themselves. Consider the matrix 

$$
A={\begin{bmatrix}1&0&0\\0&2&0\\0&0&3\end{bmatrix}}.
$$

The characteristic polynomial of A is 

$$
\det(A-\lambda I)=(1-\lambda )(2-\lambda )(3-\lambda ),
$$

 which has the roots *λ*<sub>1</sub> = 1, *λ*<sub>2</sub> = 2, and *λ*<sub>3</sub> = 3. These roots are the diagonal elements as well as the eigenvalues of A.

Each diagonal element corresponds to an eigenvector whose only nonzero component is in the same row as that diagonal element. In the example, the eigenvalues correspond to the eigenvectors, 

$$
\mathbf {v} _{\lambda _{1}}={\begin{bmatrix}1\\0\\0\end{bmatrix}},\quad \mathbf {v} _{\lambda _{2}}={\begin{bmatrix}0\\1\\0\end{bmatrix}},\quad \mathbf {v} _{\lambda _{3}}={\begin{bmatrix}0\\0\\1\end{bmatrix}},
$$

 respectively, as well as scalar multiples of these vectors.

#### Triangular matrix example

A matrix whose elements above the main diagonal are all zero is called a *lower [triangular matrix](https://en.wikipedia.org/wiki/Triangular_matrix)*, while a matrix whose elements below the main diagonal are all zero is called an *upper triangular matrix*. As with diagonal matrices, the eigenvalues of triangular matrices are the elements of the main diagonal.

Consider the lower triangular matrix, 

$$
A={\begin{bmatrix}1&0&0\\1&2&0\\2&3&3\end{bmatrix}}.
$$

The characteristic polynomial of A is 

$$
\det(A-\lambda I)=(1-\lambda )(2-\lambda )(3-\lambda ),
$$

 which has the roots *λ*<sub>1</sub> = 1, *λ*<sub>2</sub> = 2, and *λ*<sub>3</sub> = 3. These roots are the diagonal elements as well as the eigenvalues of A.

These eigenvalues correspond to the eigenvectors, 

$$
\mathbf {v} _{\lambda _{1}}={\begin{bmatrix}1\\-1\\{\frac {1}{2}}\end{bmatrix}},\quad \mathbf {v} _{\lambda _{2}}={\begin{bmatrix}0\\1\\-3\end{bmatrix}},\quad \mathbf {v} _{\lambda _{3}}={\begin{bmatrix}0\\0\\1\end{bmatrix}},
$$

 respectively, as well as scalar multiples of these vectors.

#### Matrix with repeated eigenvalues example

As in the previous example, the lower triangular matrix 

$$
A={\begin{bmatrix}2&0&0&0\\1&2&0&0\\0&1&3&0\\0&0&1&3\end{bmatrix}},
$$

 has a characteristic polynomial that is the product of its diagonal elements, 

$$
\det(A-\lambda I)={\begin{vmatrix}2-\lambda &0&0&0\\1&2-\lambda &0&0\\0&1&3-\lambda &0\\0&0&1&3-\lambda \end{vmatrix}}=(2-\lambda )^{2}(3-\lambda )^{2}.
$$

The roots of this polynomial, and hence the eigenvalues, are 2 and 3. The *algebraic multiplicity* of each eigenvalue is 2; in other words they are both double roots. The sum of the algebraic multiplicities of all distinct eigenvalues is *μ*<sub>*A*</sub> = 4 = *n*, the order of the characteristic polynomial and the dimension of A.

On the other hand, the *geometric multiplicity* of the eigenvalue 2 is only 1, because its eigenspace is spanned by just one vector \[0 1 −1 1\]<sup>T</sup> and is therefore 1-dimensional. Similarly, the geometric multiplicity of the eigenvalue 3 is 1 because its eigenspace is spanned by just one vector \[0 0 0 1\]<sup>T</sup>. The total geometric multiplicity *γ*<sub>*A*</sub> is 2, which is the smallest it could be for a matrix with two distinct eigenvalues. Geometric multiplicities are defined in a later section.

### Eigenvector-eigenvalue identity

For a [Hermitian matrix](https://en.wikipedia.org/wiki/Hermitian_matrix) A, the norm squared of the *α*-th component of a normalized eigenvector can be calculated using only the matrix eigenvalues and the eigenvalues of the corresponding [minor matrix](https://en.wikipedia.org/wiki/Minor_(linear_algebra) "Minor (linear algebra)"), 

$$
|v_{i\alpha }|^{2}={\frac {\prod _{k}{(\lambda _{i}(A)-\lambda _{k}(A_{\alpha }))}}{\prod _{k\neq i}{(\lambda _{i}(A)-\lambda _{k}(A))}}},
$$

 where $A_{\alpha }$ is the [submatrix](https://en.wikipedia.org/wiki/Submatrix) formed by removing the *α*-th row and column from the original matrix. This identity also extends to [diagonalizable matrices](https://en.wikipedia.org/wiki/Diagonalizable_matrix), and has been rediscovered many times in the literature.

## Eigenvalues and eigenfunctions of differential operators

The definitions of eigenvalue and eigenvectors of a linear transformation T remains valid even if the underlying vector space is an infinite-dimensional [Hilbert](https://en.wikipedia.org/wiki/Hilbert_space) or [Banach space](https://en.wikipedia.org/wiki/Banach_space). A widely used class of linear transformations acting on infinite-dimensional spaces are the [differential operators](https://en.wikipedia.org/wiki/Differential_operator) on [function spaces](https://en.wikipedia.org/wiki/Function_space). Let D be a linear differential operator on the space $C^{\infty }(\mathbb {R} )$ of [infinitely differentiable](https://en.wikipedia.org/wiki/Infinitely_differentiable) real functions of a real argument t. The eigenvalue equation for D is the [differential equation](https://en.wikipedia.org/wiki/Differential_equation) 

$$
Df(t)=\lambda f(t)
$$

The functions that satisfy this equation are eigenvectors of D and are commonly called **eigenfunctions**.

### Derivative operator example

Consider the derivative operator ${\tfrac {d}{dt}}$ with eigenvalue equation 

$$
{\frac {d}{dt}}f(t)=\lambda f(t).
$$

This differential equation can be solved by multiplying both sides by *dt*/*f*(*t*) and [integrating](https://en.wikipedia.org/wiki/Integration_(calculus)). Its solution, the [exponential function](https://en.wikipedia.org/wiki/Exponential_function) 

$$
f(t)=f(0)e^{\lambda t},
$$

 is the eigenfunction of the derivative operator. In this case the eigenfunction is itself a function of its associated eigenvalue. In particular, for *λ* = 0 the eigenfunction *f*(*t*) is a constant.

## General definition

The concept of eigenvalues and eigenvectors extends naturally to arbitrary [linear transformations](https://en.wikipedia.org/wiki/Linear_map) on arbitrary vector spaces. Let V be any vector space over some [field](https://en.wikipedia.org/wiki/Field_(algebra)) K of [scalars](https://en.wikipedia.org/wiki/Scalar_(mathematics) "Scalar (mathematics)"), and let T be a linear transformation mapping V into V, 

$$
T:V\to V.
$$

We say that a nonzero vector **v** ∈ *V* is an **eigenvector** of T if and only if there exists a scalar *λ* ∈ *K* such that

|  |  |  |
|----|----|----|
| $T(\mathbf {v} )=\lambda \mathbf {v} .$ |  | 5 |

This equation is called the eigenvalue equation for T, and the scalar λ is the **eigenvalue** of T corresponding to the eigenvector **v**. *T*(**v**) is the result of applying the transformation T to the vector **v**, while *λ***v** is the product of the scalar λ with **v**.

### Eigenspaces, geometric multiplicity, and the eigenbasis

Given an eigenvalue λ, consider the set 

$$
E=\left\{\mathbf {v} :T(\mathbf {v} )=\lambda \mathbf {v} \right\},
$$

 which is the union of the zero vector with the set of all eigenvectors associated with λ. E is called the **eigenspace** or **characteristic space** of T associated with λ. It is the kernel of the linear transformation *T* − *λI*.

By definition of a linear transformation, 

$$
{\begin{aligned}T(\mathbf {x} +\mathbf {y} )&=T(\mathbf {x} )+T(\mathbf {y} ),\\T(\alpha \mathbf {x} )&=\alpha T(\mathbf {x} ),\end{aligned}}
$$

 for **x**, **y** ∈ *V* and *α* ∈ *K*. Therefore, if **u** and **v** are eigenvectors of T associated with eigenvalue λ, namely **u**, **v** ∈ *E*, then 

$$
{\begin{aligned}T(\mathbf {u} +\mathbf {v} )&=\lambda (\mathbf {u} +\mathbf {v} ),\\T(\alpha \mathbf {v} )&=\lambda (\alpha \mathbf {v} ).\end{aligned}}
$$

So, both **u** + **v** and *α***v** are either zero or eigenvectors of T associated with λ, namely **u** + **v**, *α***v** ∈ *E*, and E is closed under addition and scalar multiplication. The eigenspace E associated with λ is therefore a linear subspace of V. If that subspace has dimension 1, it is sometimes called an **eigenline**.

The **geometric multiplicity** *γ*<sub>*T*</sub>(*λ*) of an eigenvalue λ is the dimension of the eigenspace associated with λ, i.e., the maximum number of linearly independent eigenvectors associated with that eigenvalue. By the definition of eigenvalues and eigenvectors, *γ*<sub>*T*</sub>(*λ*) ≥ 1 because every eigenvalue has at least one eigenvector.

The eigenspaces of T always form a [direct sum](https://en.wikipedia.org/wiki/Direct_sum). As a consequence, eigenvectors of *different* eigenvalues are always linearly independent. Therefore, the sum of the dimensions of the eigenspaces cannot exceed the dimension n of the vector space on which T operates, and there cannot be more than n distinct eigenvalues.

Any subspace spanned by eigenvectors of T is an [invariant subspace](https://en.wikipedia.org/wiki/Invariant_subspace) of T, and the restriction of T to such a subspace is diagonalizable. Moreover, if the entire vector space V can be spanned by the eigenvectors of T, or equivalently if the direct sum of the eigenspaces associated with all the eigenvalues of T is the entire vector space V, then a basis of V called an **eigenbasis** can be formed from linearly independent eigenvectors of T. When T admits an eigenbasis, T is diagonalizable.

### Spectral theory

If λ is an eigenvalue of T, then the operator (*T* − *λI*) is not [one-to-one](https://en.wikipedia.org/wiki/One_to_one_correspondence), and therefore its inverse (*T* − *λI*)<sup>−1</sup> does not exist. The converse is true for finite-dimensional vector spaces, but not for infinite-dimensional vector spaces. In general, the operator (*T* − *λI*) may not have an inverse even if λ is not an eigenvalue.

For this reason, in [functional analysis](https://en.wikipedia.org/wiki/Functional_analysis) eigenvalues can be generalized to the [spectrum of a linear operator](https://en.wikipedia.org/wiki/Spectrum_(functional_analysis) "Spectrum (functional analysis)") T as the set of all scalars λ for which the operator (*T* − *λI*) has no [bounded](https://en.wikipedia.org/wiki/Bounded_operator) inverse. The spectrum of an operator always contains all its eigenvalues but is not limited to them.

### Associative algebras and representation theory

One can generalize the algebraic object that is acting on the vector space, replacing a single operator acting on a vector space with an [algebra representation](https://en.wikipedia.org/wiki/Algebra_representation) – an [associative algebra](https://en.wikipedia.org/wiki/Associative_algebra) acting on a [module](https://en.wikipedia.org/wiki/Module_(mathematics) "Module (mathematics)"). The study of such actions is the field of [representation theory](https://en.wikipedia.org/wiki/Representation_theory).

The [representation-theoretical concept of weight](https://en.wikipedia.org/wiki/Weight_(representation_theory) "Weight (representation theory)") is an analog of eigenvalues, while *weight vectors* and *weight spaces* are the analogs of eigenvectors and eigenspaces, respectively.

[Hecke eigensheaf](https://en.wikipedia.org/wiki/Hecke_eigensheaf) is a tensor-multiple of itself and is considered in [Langlands correspondence](https://en.wikipedia.org/wiki/Langlands_correspondence).

## Dynamic equations

The simplest [difference equations](https://en.wikipedia.org/wiki/Difference_equation) have the form 

$$
x_{t}=a_{1}x_{t-1}+a_{2}x_{t-2}+\cdots +a_{k}x_{t-k}.
$$

The solution of this equation for x in terms of t is found by using its characteristic equation 

$$
\lambda ^{k}-a_{1}\lambda ^{k-1}-a_{2}\lambda ^{k-2}-\cdots -a_{k-1}\lambda -a_{k}=0,
$$

which can be found by stacking into matrix form a set of equations consisting of the above difference equation and the *k* – 1 equations *x*<sub>*t*–1</sub> = *x*<sub>*t*–1</sub>, ..., *x*<sub>*t*–*k*+1</sub> = *x*<sub>*t*–*k*+1</sub>, giving a k-dimensional system of the first order in the stacked variable vector \[*x*<sub>*t*</sub>  ⋅⋅⋅  *x*<sub>*t*–*k*+1</sub>\] in terms of its once-lagged value, and taking the characteristic equation of this system's matrix. This equation gives k characteristic roots *λ*<sub>1</sub>, ... , *λ*<sub>*k*</sub>, for use in the solution equation 

$$
x_{t}=c_{1}\lambda _{1}^{t}+\cdots +c_{k}\lambda _{k}^{t}.
$$

A similar procedure is used for solving a [differential equation](https://en.wikipedia.org/wiki/Differential_equation) of the form 

$$
{\frac {d^{k}x}{dt^{k}}}+a_{k-1}{\frac {d^{k-1}x}{dt^{k-1}}}+\cdots +a_{1}{\frac {dx}{dt}}+a_{0}x=0.
$$

## Calculation

The calculation of eigenvalues and eigenvectors is a topic where theory, as presented in elementary linear algebra textbooks, is often very far from practice.

### Classical method

The classical method is to first find the eigenvalues, and then calculate the eigenvectors for each eigenvalue. It is in several ways poorly suited for non-exact arithmetics such as [floating-point](https://en.wikipedia.org/wiki/Floating-point).

#### Eigenvalues

The eigenvalues of a matrix A can be determined by finding the roots of the characteristic polynomial. This is easy for 2 × 2 matrices, but the difficulty increases rapidly with the size of the matrix.

In theory, the coefficients of the characteristic polynomial can be computed exactly, since they are sums of products of matrix elements; and there are algorithms that can find all the roots of a polynomial of arbitrary degree to any required [accuracy](https://en.wikipedia.org/wiki/Accuracy). However, this approach is not viable in practice because the coefficients would be contaminated by unavoidable [round-off errors](https://en.wikipedia.org/wiki/Round-off_error), and the roots of a polynomial can be an extremely sensitive function of the coefficients (as exemplified by [Wilkinson's polynomial](https://en.wikipedia.org/wiki/Wilkinson%27s_polynomial)). Even for matrices whose elements are integers the calculation becomes nontrivial, because the sums are very long; the constant term is the [[Determinant]], which for an n × n matrix is a sum of *n*! different products.

Explicit [algebraic formulas](https://en.wikipedia.org/wiki/Algebraic_solution) for the roots of a polynomial exist only if the degree n is 4 or less. According to the [Abel–Ruffini theorem](https://en.wikipedia.org/wiki/Abel%E2%80%93Ruffini_theorem) there is no general, explicit and exact algebraic formula for the roots of a polynomial with degree 5 or more. (Generality matters because any polynomial with degree n is the characteristic polynomial of some [companion matrix](https://en.wikipedia.org/wiki/Companion_matrix) of order n.) Therefore, for matrices of order 5 or more, the eigenvalues and eigenvectors cannot be obtained by an explicit algebraic formula, and must therefore be computed by approximate [numerical methods](https://en.wikipedia.org/wiki/Numerical_method). Even the [exact formula](https://en.wikipedia.org/wiki/Cubic_function#General_solution_to_the_cubic_equation_with_real_coefficients) for the roots of a degree 3 polynomial is numerically impractical.

#### Eigenvectors

Once the (exact) value of an eigenvalue is known, the corresponding eigenvectors can be found by finding nonzero solutions of the eigenvalue equation, that becomes a [system of linear equations](https://en.wikipedia.org/wiki/Linear_system) with known coefficients. For example, once it is known that 6 is an eigenvalue of the matrix 

$$
A={\begin{bmatrix}4&1\\6&3\end{bmatrix}}
$$

 we can find its eigenvectors by solving the equation *Av* = 6*v*, that is 

$$
{\begin{bmatrix}4&1\\6&3\end{bmatrix}}{\begin{bmatrix}x\\y\end{bmatrix}}=6\cdot {\begin{bmatrix}x\\y\end{bmatrix}}
$$

This matrix equation is equivalent to two [linear equations](https://en.wikipedia.org/wiki/Linear_equation) 

$$
\left\{{\begin{aligned}4x+{\hphantom {3}}y&=6x\\6x+3y&=6y\end{aligned}}\right.
$$

 that is, 

$$
\left\{{\begin{aligned}-2x+{\hphantom {3}}y&=0\\6x-3y&=0\end{aligned}}\right.
$$

Both equations reduce to the single linear equation *y* = 2*x*. Therefore, any vector of the form \[*a*  2*a*\]<sup>T</sup>, for any nonzero real number a, is an eigenvector of A with eigenvalue *λ* = 6.

The matrix A above has another eigenvalue *λ* = 1. A similar calculation shows that the corresponding eigenvectors are the nonzero solutions of 3*x* + *y* = 0, that is, any vector of the form \[*b*  −3*b*\]<sup>T</sup>, for any nonzero real number b.

### Simple iterative methods

The converse approach, of first seeking the eigenvectors and then determining each eigenvalue from its eigenvector, turns out to be far more tractable for computers. The easiest algorithm here consists of picking an arbitrary starting vector and then repeatedly multiplying it with the matrix (optionally normalizing the vector to keep its elements of reasonable size); this makes the vector converge towards an eigenvector. [A variation](https://en.wikipedia.org/wiki/Inverse_iteration) is to instead multiply the vector by (*A* − *μI*)<sup>−1</sup>; this causes it to converge to an eigenvector of the eigenvalue closest to $\mu \in \mathbb {C}$.

If **v** is (a good approximation of) an eigenvector of A, then the corresponding eigenvalue can be computed as 

$$
\lambda ={\frac {\mathbf {v} ^{*}A\mathbf {v} }{\mathbf {v} ^{*}\mathbf {v} }}
$$

 where **v**<sup>∗</sup> denotes the [conjugate transpose](https://en.wikipedia.org/wiki/Conjugate_transpose) of **v**.

### Modern methods

Efficient, accurate methods to compute eigenvalues and eigenvectors of arbitrary matrices were not known until the [QR algorithm](https://en.wikipedia.org/wiki/QR_algorithm) was designed in 1961. Combining the [Householder transformation](https://en.wikipedia.org/wiki/Householder_transformation) with the LU decomposition results in an algorithm with better convergence than the QR algorithm.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup> For large [Hermitian](https://en.wikipedia.org/wiki/Hermitian_matrix) [sparse matrices](https://en.wikipedia.org/wiki/Sparse_matrix), the [Lanczos algorithm](https://en.wikipedia.org/wiki/Lanczos_algorithm) is one example of an efficient [iterative method](https://en.wikipedia.org/wiki/Iterative_method) to compute eigenvalues and eigenvectors, among several other possibilities.

Most numeric methods that compute the eigenvalues of a matrix also determine a set of corresponding eigenvectors as a by-product of the computation, although sometimes implementors choose to discard the eigenvector information as soon as it is no longer needed.

## Applications

### Geometric transformations

Eigenvectors and eigenvalues can be useful for understanding linear transformations of geometric shapes. The following table presents some example transformations in the plane along with their 2 × 2 matrices, eigenvalues, and eigenvectors.

<table class="wikitable" style="text-align:center; margin:1em auto 1em auto;">
<caption>Eigenvalues of geometric transformations</caption>

[Scaling](https://en.wikipedia.org/wiki/Scaling_(geometry))
Unequal scaling
[Rotation](https://en.wikipedia.org/wiki/Rotation_(geometry))
[Horizontal shear](https://en.wikipedia.org/wiki/Shear_mapping)
[Hyperbolic rotation](https://en.wikipedia.org/wiki/Hyperbolic_rotation)

&#10;
Illustration
![[media/c70b163ff739bfda6289d95a9fd06d0a004ace28.png]]
![[media/ff37dd6b287f7de9b23e45f9e61bc72f185e904f.png]]
![[media/5aa3ef474204d8bbdb95569eff4555dbe9fb5b10.png]]
<figure class="mw-halign-center" typeof="mw:File">
![[media/78edb0c23cb15eefc248f0260adb6c82980e582d.png]]
</figure>
![[media/e7f8d8bc56bb74fc3ae249f06f67b84c855a4c5b.png]]

Matrix
${\begin{bmatrix}k&0\\0&k\end{bmatrix}}$
${\begin{bmatrix}k_{1}&0\\0&k_{2}\end{bmatrix}}$
${\begin{bmatrix}\cos \theta &-\sin \theta \\\sin \theta &\cos \theta \end{bmatrix}}$
${\begin{bmatrix}1&k\\0&1\end{bmatrix}}$
${\begin{bmatrix}\cosh \varphi &\sinh \varphi \\\sinh \varphi &\cosh \varphi \end{bmatrix}}$

Characteristic<br />
polynomial
$\ (\lambda -k)^{2}$
$(\lambda -k_{1})(\lambda -k_{2})$
$\lambda ^{2}-2\cos(\theta )\lambda +1$
$\ (\lambda -1)^{2}$
$\lambda ^{2}-2\cosh(\varphi )\lambda +1$

Eigenvalues, $\lambda _{i}$
$\lambda _{1}=\lambda _{2}=k$
${\begin{aligned}\lambda _{1}&=k_{1}\\\lambda _{2}&=k_{2}\end{aligned}}$
${\begin{aligned}\lambda _{1}&=e^{i\theta }\\&=\cos \theta +i\sin \theta \\\lambda _{2}&=e^{-i\theta }\\&=\cos \theta -i\sin \theta \end{aligned}}$
$\lambda _{1}=\lambda _{2}=1$
${\begin{aligned}\lambda _{1}&=e^{\varphi }\\&=\cosh \varphi +\sinh \varphi \\\lambda _{2}&=e^{-\varphi }\\&=\cosh \varphi -\sinh \varphi \end{aligned}}$

Algebraic <abbr title="multiplicity">mult.</abbr>,<br />
$\mu _{i}=\mu (\lambda _{i})$
$\mu _{1}=2$
${\begin{aligned}\mu _{1}&=1\\\mu _{2}&=1\end{aligned}}$
${\begin{aligned}\mu _{1}&=1\\\mu _{2}&=1\end{aligned}}$
$\mu _{1}=2$
${\begin{aligned}\mu _{1}&=1\\\mu _{2}&=1\end{aligned}}$

Geometric <abbr title="multiplicity">mult.</abbr>,<br />
$\gamma _{i}=\gamma (\lambda _{i})$
$\gamma _{1}=2$
${\begin{aligned}\gamma _{1}&=1\\\gamma _{2}&=1\end{aligned}}$
${\begin{aligned}\gamma _{1}&=1\\\gamma _{2}&=1\end{aligned}}$
$\gamma _{1}=1$
${\begin{aligned}\gamma _{1}&=1\\\gamma _{2}&=1\end{aligned}}$

Eigenvectors
All nonzero vectors
${\begin{aligned}\mathbf {u} _{1}&={\begin{bmatrix}1\\0\end{bmatrix}}\\\mathbf {u} _{2}&={\begin{bmatrix}0\\1\end{bmatrix}}\end{aligned}}$
${\begin{aligned}\mathbf {u} _{1}&={\begin{bmatrix}1\\-i\end{bmatrix}}\\\mathbf {u} _{2}&={\begin{bmatrix}1\\+i\end{bmatrix}}\end{aligned}}$
$\mathbf {u} _{1}={\begin{bmatrix}1\\0\end{bmatrix}}$
${\begin{aligned}\mathbf {u} _{1}&={\begin{bmatrix}1\\1\end{bmatrix}}\\\mathbf {u} _{2}&={\begin{bmatrix}1\\-1\end{bmatrix}}\end{aligned}}$

</table>

The characteristic equation for a rotation is a [quadratic equation](https://en.wikipedia.org/wiki/Quadratic_equation) with [discriminant](https://en.wikipedia.org/wiki/Discriminant) *D* = −4(sin *θ*)<sup>2</sup>, which is a negative number whenever θ is not an integer multiple of π (180°). Therefore, except for these special cases, the two eigenvalues are complex numbers, cos *θ* ± *i*sin *θ*; and all eigenvectors have non-real entries. Indeed, except for those special cases, a rotation changes the direction of every nonzero vector in the plane.

A linear transformation that takes a square to a rectangle of the same area (a [squeeze mapping](https://en.wikipedia.org/wiki/Squeeze_mapping)) has reciprocal eigenvalues.

### Principal component analysis

![[media/7cf00e56e144e550bc6b534e0dbe9670d3b9331e.png]]
PCA of the [multivariate Gaussian distribution](https://en.wikipedia.org/wiki/Multivariate_Gaussian_distribution) centered at (1, 3) with a standard deviation of 3 in roughly the (0.878, 0.478) direction and of 1 in the orthogonal direction. The vectors shown are unit eigenvectors of the (symmetric, positive-semidefinite) [covariance matrix](https://en.wikipedia.org/wiki/Covariance_matrix) scaled by the square root of the corresponding eigenvalue. Just as in the one-dimensional case, the square root is taken because the [standard deviation](https://en.wikipedia.org/wiki/Standard_deviation) is more readily visualized than the [variance](https://en.wikipedia.org/wiki/Variance).

The [eigendecomposition](https://en.wikipedia.org/wiki/Eigendecomposition_of_a_matrix#Real_symmetric_matrices) of a [symmetric](https://en.wikipedia.org/wiki/Symmetric_matrix) [positive semidefinite](https://en.wikipedia.org/wiki/Positive_semidefinite_matrix) (PSD) [matrix](https://en.wikipedia.org/wiki/Positive_semidefinite_matrix) yields an [orthogonal basis](https://en.wikipedia.org/wiki/Orthogonal_basis) of eigenvectors, each of which has a nonnegative eigenvalue. The orthogonal decomposition of a PSD matrix is used in [multivariate analysis](https://en.wikipedia.org/wiki/Multivariate_statistics), where the [sample](https://en.wikipedia.org/wiki/Sample_variance) [covariance matrices](https://en.wikipedia.org/wiki/Covariance_matrix) are PSD. This orthogonal decomposition is called [[Principal Component Analysis]] (PCA) in statistics. PCA studies [linear relations](https://en.wikipedia.org/wiki/Linear_relation) among variables. PCA is performed on the [covariance matrix](https://en.wikipedia.org/wiki/Covariance_matrix) or the [correlation matrix](https://en.wikipedia.org/wiki/Correlation_matrix) (in which each variable is scaled to have its [sample variance](https://en.wikipedia.org/wiki/Sample_variance) equal to one). For the covariance or correlation matrix, the eigenvectors correspond to [[Principal Component Analysis|principal components]] and the eigenvalues to the [variance explained](https://en.wikipedia.org/wiki/Explained_variance) by the principal components. Principal component analysis of the correlation matrix provides an [orthogonal basis](https://en.wikipedia.org/wiki/Orthogonal_basis) for the space of the observed data: In this basis, the largest eigenvalues correspond to the principal components that are associated with most of the covariability among a number of observed data.

Principal component analysis is used as a means of [dimensionality reduction](https://en.wikipedia.org/wiki/Dimensionality_reduction) in the study of large [data sets](https://en.wikipedia.org/wiki/Data_set), such as those encountered in [bioinformatics](https://en.wikipedia.org/wiki/Bioinformatics). In [Q methodology](https://en.wikipedia.org/wiki/Q_methodology), the eigenvalues of the correlation matrix determine the Q-methodologist's judgment of *practical* significance (which differs from the [statistical significance](https://en.wikipedia.org/wiki/Statistical_significance) of [[Hypothesis Testing]]; cf. [criteria for determining the number of factors](https://en.wikipedia.org/wiki/Scree%27s_test)). More generally, principal component analysis can be used as a method of [factor analysis](https://en.wikipedia.org/wiki/Factor_analysis) in [structural equation modeling](https://en.wikipedia.org/wiki/Structural_equation_model).

### Graphs

In [[Spectral Graph Theory]], an eigenvalue of a [graph](https://en.wikipedia.org/wiki/Graph_theory) is defined as an eigenvalue of the graph's [adjacency matrix](https://en.wikipedia.org/wiki/Adjacency_matrix) A, or (increasingly) of the graph's [[Laplacian Matrix]] due to its [discrete Laplace operator](https://en.wikipedia.org/wiki/Discrete_Laplace_operator), which is either *D* − *A* (sometimes called the *combinatorial Laplacian*) or *I* − *D*<sup>−1/2</sup>*AD*<sup>−1/2</sup> (sometimes called the *normalized Laplacian*), where D is a diagonal matrix with D<sub>ii</sub> equal to the degree of vertex v<sub>i</sub>, and in *D*<sup>−1/2</sup>, the *i*-th diagonal entry is $1/{\sqrt {\deg(v_{i})}}$. The k-th principal eigenvector of a graph is defined as either the eigenvector corresponding to the k-th largest or k-th smallest eigenvalue of the Laplacian. The first principal eigenvector of the graph is also referred to merely as the principal eigenvector.

The principal eigenvector is used to measure the [centrality](https://en.wikipedia.org/wiki/Eigenvector_centrality) of its vertices. An example is [Google](https://en.wikipedia.org/wiki/Google)'s [PageRank](https://en.wikipedia.org/wiki/PageRank) algorithm. The principal eigenvector of a modified [adjacency matrix](https://en.wikipedia.org/wiki/Adjacency_matrix) of the World Wide Web graph gives the page ranks as its components. This vector corresponds to the [[Stationary Distribution]] of the [[Markov Chain]] represented by the row-normalized adjacency matrix; however, the adjacency matrix must first be modified to ensure a stationary distribution exists. The second smallest eigenvector can be used to partition the graph into clusters, via [spectral clustering](https://en.wikipedia.org/wiki/Spectral_clustering). Other methods are also available for clustering.

### Markov chains

A [[Markov Chain]] is represented by a matrix whose entries are the [transition probabilities](https://en.wikipedia.org/wiki/Transition_probabilities) between states of a system. In particular the entries are non-negative, and every row of the matrix sums to one, being the sum of probabilities of transitions from one state to some other state of the system. The [Perron–Frobenius theorem](https://en.wikipedia.org/wiki/Perron%E2%80%93Frobenius_theorem) gives sufficient conditions for a Markov chain to have a unique dominant eigenvalue, which governs the convergence of the system to a steady state.

### Vibration analysis

![[media/d760016356ab7210668dbcb59c1bd9f6123df3fe.gif]]
Mode shape of a tuning fork at eigenfrequency 440.09 Hz

Eigenvalue problems occur naturally in the vibration analysis of mechanical structures with many [degrees of freedom](https://en.wikipedia.org/wiki/Degrees_of_freedom_(mechanics) "Degrees of freedom (mechanics)"). The eigenvalues are the [natural frequencies](https://en.wikipedia.org/wiki/Natural_frequency) (or **eigenfrequencies**) of vibration, and the eigenvectors are the shapes of these vibrational modes. In particular, undamped vibration is governed by 

$$
m{\ddot {x}}+kx=0
$$

 or 

$$
m{\ddot {x}}=-kx
$$

That is, acceleration is proportional to position (i.e., we expect x to be sinusoidal in time).

In n dimensions, m becomes a [mass matrix](https://en.wikipedia.org/wiki/Mass_matrix) and k a [stiffness matrix](https://en.wikipedia.org/wiki/Stiffness_matrix). Admissible solutions are then a linear combination of solutions to the [generalized eigenvalue problem](https://en.wikipedia.org/wiki/Generalized_eigenvalue_problem) 

$$
kx=\omega ^{2}mx
$$

 where *ω*<sup>2</sup> is the eigenvalue and ω is the (imaginary) [angular frequency](https://en.wikipedia.org/wiki/Angular_frequency). The principal [vibration modes](https://en.wikipedia.org/wiki/Vibration_mode) are different from the principal compliance modes, which are the eigenvectors of k alone. Furthermore, [damped vibration](https://en.wikipedia.org/wiki/Damped_vibration), governed by 

$$
m{\ddot {x}}+c{\dot {x}}+kx=0
$$

 leads to a so-called [quadratic eigenvalue problem](https://en.wikipedia.org/wiki/Quadratic_eigenvalue_problem), 

$$
\left(\omega ^{2}m+\omega c+k\right)x=0.
$$

This can be reduced to a generalized eigenvalue problem by [algebraic manipulation](https://en.wikipedia.org/wiki/Quadratic_eigenvalue_problem#Methods_of_Solution) at the cost of solving a larger system.

The orthogonality properties of the eigenvectors allows decoupling of the [differential equations](https://en.wikipedia.org/wiki/Differential_equation) so that the system can be represented as linear summation of the eigenvectors. The eigenvalue problem of complex structures is often solved using [finite element analysis](https://en.wikipedia.org/wiki/Finite_element_analysis), but neatly generalize the solution to scalar-valued vibration problems.

### Tensor of moment of inertia

In [mechanics](https://en.wikipedia.org/wiki/Mechanics), the eigenvectors of the [moment of inertia tensor](https://en.wikipedia.org/wiki/Inertia_tensor) define the [principal axes](https://en.wikipedia.org/wiki/Principal_axis_(mechanics)) of a [rigid body](https://en.wikipedia.org/wiki/Rigid_body). The [tensor](https://en.wikipedia.org/wiki/Tensor) of moment of [inertia](https://en.wikipedia.org/wiki/Inertia) is a key quantity required to determine the rotation of a rigid body around its [center of mass](https://en.wikipedia.org/wiki/Center_of_mass).

### Stress tensor

In [solid mechanics](https://en.wikipedia.org/wiki/Solid_mechanics), the [stress](https://en.wikipedia.org/wiki/Stress_(mechanics) "Stress (mechanics)") tensor is symmetric and so can be decomposed into a [diagonal](https://en.wikipedia.org/wiki/Diagonal) tensor with the eigenvalues on the diagonal and eigenvectors as a basis. Because it is diagonal, in this orientation, the stress tensor has no [shear](https://en.wikipedia.org/wiki/Shear_(mathematics)) components; the components it does have are the principal components.

### Schrödinger equation

![[media/3ec6940af55a7dee1a64f7f8c5960800274dd800.png]]
The [wavefunctions](https://en.wikipedia.org/wiki/Wavefunction) associated with the [bound states](https://en.wikipedia.org/wiki/Bound_state) of an [electron](https://en.wikipedia.org/wiki/Electron) in a [hydrogen atom](https://en.wikipedia.org/wiki/Hydrogen_atom) can be seen as the eigenvectors of the [hydrogen atom Hamiltonian](https://en.wikipedia.org/wiki/Hydrogen_atom) as well as of the [angular momentum operator](https://en.wikipedia.org/wiki/Angular_momentum_operator). They are associated with eigenvalues interpreted as their energies (increasing downward: <em>n</em> = 1, 2, 3, ...) and [angular momentum](https://en.wikipedia.org/wiki/Angular_momentum) (increasing across: s, p, d, ...). The illustration shows the square of the absolute value of the wavefunctions. Brighter areas correspond to higher [[Probability Density Function|probability density]] for a position [measurement](https://en.wikipedia.org/wiki/Measurement_in_quantum_mechanics). The center of each figure is the [atomic nucleus](https://en.wikipedia.org/wiki/Atomic_nucleus), a [proton](https://en.wikipedia.org/wiki/Proton).

An example of an eigenvalue equation where the transformation T is represented in terms of a differential operator is the time-independent [Schrödinger equation](https://en.wikipedia.org/wiki/Schr%C3%B6dinger_equation) in [quantum mechanics](https://en.wikipedia.org/wiki/Quantum_mechanics): 

$$
H\psi _{E}=E\psi _{E}\,
$$

 where the [Hamiltonian](https://en.wikipedia.org/wiki/Hamiltonian_(quantum_mechanics) "Hamiltonian (quantum mechanics)") H is a second-order [differential operator](https://en.wikipedia.org/wiki/Differential_operator), and the [wavefunction](https://en.wikipedia.org/wiki/Wavefunction) ψ<sub>E</sub> is one of its eigenfunctions corresponding to the eigenvalue E, interpreted as its [energy](https://en.wikipedia.org/wiki/Energy).

However, in the case where one is interested only in the [bound state](https://en.wikipedia.org/wiki/Bound_state) solutions of the Schrödinger equation, one looks for ψ<sub>E</sub> within the space of [square integrable](https://en.wikipedia.org/wiki/Square-integrable_function) functions. Since this space is a [Hilbert space](https://en.wikipedia.org/wiki/Hilbert_space) with a well-defined [scalar product](https://en.wikipedia.org/wiki/Scalar_product), one can introduce a [basis set](https://en.wikipedia.org/wiki/Basis_(linear_algebra) "Basis (linear algebra)") in which ψ<sub>E</sub> and H can be represented as a one-dimensional array (i.e., a vector) and a matrix respectively. This allows one to represent the Schrödinger equation in a matrix form.

The [bra–ket notation](https://en.wikipedia.org/wiki/Bra%E2%80%93ket_notation) is often used in this context. A vector, which represents a state of the system, in the Hilbert space of square integrable functions is represented by \|Ψ<sub>*E*</sub>⟩. In this notation, the Schrödinger equation is: 

$$
H|\Psi _{E}\rangle =E|\Psi _{E}\rangle
$$

 where \|Ψ<sub>*E*</sub>⟩ is an **eigenstate** of H, and E represents the eigenvalue. H is an [observable](https://en.wikipedia.org/wiki/Observable) [self-adjoint operator](https://en.wikipedia.org/wiki/Self-adjoint_operator), the infinite-dimensional analog of Hermitian matrices. As in the matrix case, in the equation above *H*\|Ψ<sub>*E*</sub>⟩ is understood to be the vector obtained by application of the transformation H to \|Ψ<sub>*E*</sub>⟩.

### Wave transport

### Molecular orbitals

In [quantum mechanics](https://en.wikipedia.org/wiki/Quantum_mechanics), and in particular in [atomic](https://en.wikipedia.org/wiki/Atomic_physics) and [molecular physics](https://en.wikipedia.org/wiki/Molecular_physics), within the [Hartree–Fock](https://en.wikipedia.org/wiki/Hartree%E2%80%93Fock) theory, the [atomic](https://en.wikipedia.org/wiki/Atomic_orbital) and [molecular orbitals](https://en.wikipedia.org/wiki/Molecular_orbital) can be defined by the eigenvectors of the [Fock operator](https://en.wikipedia.org/wiki/Fock_operator). The corresponding eigenvalues are interpreted as [ionization potentials](https://en.wikipedia.org/wiki/Ionization_potential) via [Koopmans' theorem](https://en.wikipedia.org/wiki/Koopmans%27_theorem). In this case, the term eigenvector is used in a somewhat more general meaning, since the Fock operator is explicitly dependent on the orbitals and their eigenvalues. Thus, if one wants to underline this aspect, one speaks of nonlinear eigenvalue problems. Such equations are usually solved by an [iteration](https://en.wikipedia.org/wiki/Iteration) procedure, called in this case [self-consistent field](https://en.wikipedia.org/wiki/Self-consistent_field) method. In [quantum chemistry](https://en.wikipedia.org/wiki/Quantum_chemistry), one often represents the Hartree–Fock equation in a non-[orthogonal](https://en.wikipedia.org/wiki/Orthogonal) [basis set](https://en.wikipedia.org/wiki/Basis_set_(chemistry) "Basis set (chemistry)"). This particular representation is a [generalized eigenvalue problem](https://en.wikipedia.org/wiki/Generalized_eigenvalue_problem) called [Roothaan equations](https://en.wikipedia.org/wiki/Roothaan_equations).

### Geology and glaciology

In [geology](https://en.wikipedia.org/wiki/Geology), especially in the study of [glacial till](https://en.wikipedia.org/wiki/Glacial_till), eigenvectors and eigenvalues are used as a method by which a mass of information of a [clast's](https://en.wikipedia.org/wiki/Clastic_rock) [fabric](https://en.wikipedia.org/wiki/Fabric_(geology) "Fabric (geology)") can be summarized in a 3-D space by six numbers. In the field, a geologist may collect such data for hundreds or thousands of clasts in a soil sample, which can be compared graphically or as a [stereographic projection](https://en.wikipedia.org/wiki/Stereographic_projection). Graphically, many geologists use a Tri-Plot (Sneed and Folk) diagram,. A stereographic projection projects 3-dimensional spaces onto a two-dimensional plane. A type of stereographic projection is Wulff Net, which is commonly used in [crystallography](https://en.wikipedia.org/wiki/Crystallography) to create [stereograms](https://en.wikipedia.org/wiki/Stereograms).

The output for the orientation tensor is in the three orthogonal (perpendicular) axes of space. The three eigenvectors are ordered **v**<sub>1</sub>, **v**<sub>2</sub>, **v**<sub>3</sub> by their eigenvalues *E*<sub>1</sub> ≥ *E*<sub>2</sub> ≥ *E*<sub>3</sub>; **v**<sub>1</sub> then is the primary orientation/dip of clast, **v**<sub>2</sub> is the secondary and **v**<sub>3</sub> is the tertiary, in terms of strength. The clast orientation is defined as the direction of the eigenvector, on a [compass rose](https://en.wikipedia.org/wiki/Compass_rose) of [360°](https://en.wikipedia.org/wiki/Turn_(geometry)). Dip is measured as the eigenvalue, the modulus of the tensor: this is valued from 0° (no dip) to 90° (vertical). The relative values of *E*<sub>1</sub>, *E*<sub>2</sub>, and *E*<sub>3</sub> are dictated by the nature of the sediment's fabric. If *E*<sub>1</sub> = *E*<sub>2</sub> = *E*<sub>3</sub>, the fabric is said to be isotropic. If *E*<sub>1</sub> = *E*<sub>2</sub> \> *E*<sub>3</sub>, the fabric is said to be planar. If *E*<sub>1</sub> \> *E*<sub>2</sub> \> *E*<sub>3</sub>, the fabric is said to be linear.

### Basic reproduction number

The basic reproduction number (*R*<sub>0</sub>) is a fundamental number in the study of how infectious diseases spread. If one infectious person is put into a population of completely susceptible people, then *R*<sub>0</sub> is the average number of people that one typical infectious person will infect. The generation time of an infection is the time, t<sub>G</sub>, from one person becoming infected to the next person becoming infected. In a heterogeneous population, the next generation matrix defines how many people in the population will become infected after time t<sub>G</sub> has passed. The value *R*<sub>0</sub> is then the largest eigenvalue of the next generation matrix.

### Eigenfaces

![[media/799c1e9d21c06b63709898eed7bda56f3c3ebeab.png]]
[Eigenfaces](https://en.wikipedia.org/wiki/Eigenface) as examples of eigenvectors

In [image processing](https://en.wikipedia.org/wiki/Image_processing), processed images of faces can be seen as vectors whose components are the [brightnesses](https://en.wikipedia.org/wiki/Brightness) of each [pixel](https://en.wikipedia.org/wiki/Pixel). The dimension of this vector space is the number of pixels. The eigenvectors of the [covariance matrix](https://en.wikipedia.org/wiki/Covariance_matrix) associated with a large set of normalized pictures of faces are called **[eigenfaces](https://en.wikipedia.org/wiki/Eigenface)**; this is an example of [[Principal Component Analysis]]. They are very useful for expressing any face image as a [linear combination](https://en.wikipedia.org/wiki/Linear_combination) of some of them. In the [facial recognition](https://en.wikipedia.org/wiki/Facial_recognition_system) branch of [biometrics](https://en.wikipedia.org/wiki/Biometrics), eigenfaces provide a means of applying [data compression](https://en.wikipedia.org/wiki/Data_compression) to faces for [identification](https://en.wikipedia.org/wiki/Recognition_of_human_individuals) purposes. Research related to eigen vision systems determining hand gestures has also been made.

Similar to this concept, **eigenvoices** represent the general direction of variability in human pronunciations of a particular utterance, such as a word in a language. Based on a linear combination of such eigenvoices, a new voice pronunciation of the word can be constructed. These concepts have been found useful in automatic speech recognition systems for speaker adaptation.

## See also

- [Antieigenvalue theory](https://en.wikipedia.org/wiki/Antieigenvalue_theory)
- [Eigenoperator](https://en.wikipedia.org/wiki/Eigenoperator)
- [Eigenplane](https://en.wikipedia.org/wiki/Eigenplane)
- [Eigenmoments](https://en.wikipedia.org/wiki/Eigenmoments)
- [Eigenvalue algorithm](https://en.wikipedia.org/wiki/Eigenvalue_algorithm)
- [Quantum states](https://en.wikipedia.org/wiki/Quantum_states)
- [Jordan normal form](https://en.wikipedia.org/wiki/Jordan_normal_form)
- [List of numerical-analysis software](https://en.wikipedia.org/wiki/List_of_numerical-analysis_software)
- [Nonlinear eigenproblem](https://en.wikipedia.org/wiki/Nonlinear_eigenproblem)
- [Normal eigenvalue](https://en.wikipedia.org/wiki/Normal_eigenvalue)
- [Quadratic eigenvalue problem](https://en.wikipedia.org/wiki/Quadratic_eigenvalue_problem)
- [Singular value](https://en.wikipedia.org/wiki/Singular_value)
- [Spectrum of a matrix](https://en.wikipedia.org/wiki/Spectrum_of_a_matrix)

## Notes

1.  Note: 
    - In 1751, Leonhard Euler proved that any body has a principal axis of rotation: Leonhard Euler (presented: October 1751; published: 1760) ["Du mouvement d'un corps solide quelconque lorsqu'il tourne autour d'un axe mobile"](https://archive.org/stream/histoiredelacad07unkngoog#page/n196/mode/2up) (On the movement of any solid body while it rotates around a moving axis), *Histoire de l'Académie royale des sciences et des belles lettres de Berlin*, pp. 176–227. [On p. 212](https://archive.org/stream/histoiredelacad07unkngoog#page/n232/mode/2up), Euler proves that any body contains a principal axis of rotation: *"Théorem. 44. De quelque figure que soit le corps, on y peut toujours assigner un tel axe, qui passe par son centre de gravité, autour duquel le corps peut tourner librement & d'un mouvement uniforme."* (Theorem. 44. Whatever be the shape of the body, one can always assign to it such an axis, which passes through its center of gravity, around which it can rotate freely and with a uniform motion.)
    - In 1755, [Johann Andreas Segner](https://en.wikipedia.org/wiki/Johann_Andreas_Segner) proved that any body has three principal axes of rotation: Johann Andreas Segner, *Specimen theoriae turbinum* \[Essay on the theory of tops (i.e., rotating bodies)\] ( Halle ("Halae"), (Germany): Gebauer, 1755). ([https://books.google.com/books?id=29](https://books.google.com/books?id=29) p. xxviiii \[29\]), Segner derives a third-degree equation in *t*, which proves that a body has three principal axes of rotation. He then states (on the same page): *"Non autem repugnat tres esse eiusmodi positiones plani HM, quia in aequatione cubica radices tres esse possunt, et tres tangentis t valores."* (However, it is not inconsistent \[that there\] be three such positions of the plane HM, because in cubic equations, \[there\] can be three roots, and three values of the tangent t.)
    - The relevant passage of Segner's work was discussed briefly by [Arthur Cayley](https://en.wikipedia.org/wiki/Arthur_Cayley). See: A. Cayley (1862) "Report on the progress of the solution of certain special problems of dynamics," *Report of the Thirty-second meeting of the British Association for the Advancement of Science; held at Cambridge in October 1862*, **32**: 184–252; see especially [pp. 225–226.](https://books.google.com/books?id=S_RJAAAAcAAJ&pg=PA225)
2.  , pp. 807–808 Augustin Cauchy (1839) "Mémoire sur l'intégration des équations linéaires" (Memoir on the integration of linear equations), *Comptes rendus*, **8**: 827–830, 845–865, 889–907, 931–937. [From p. 827:](https://gallica.bnf.fr/ark:/12148/bpt6k2967c/f833.item.r=.zoom) *"On sait d'ailleurs qu'en suivant la méthode de Lagrange, on obtient pour valeur générale de la variable prinicipale une fonction dans laquelle entrent avec la variable principale les racines d'une certaine équation que j'appellerai l'*équation caractéristique*, le degré de cette équation étant précisément l'order de l'équation différentielle qu'il s'agit d'intégrer."* (One knows, moreover, that by following Lagrange's method, one obtains for the general value of the principal variable a function in which there appear, together with the principal variable, the roots of a certain equation that I will call the "characteristic equation", the degree of this equation being precisely the order of the differential equation that must be integrated.)
3.  See: 
    - David Hilbert (1904) ["Grundzüge einer allgemeinen Theorie der linearen Integralgleichungen. (Erste Mitteilung)"](https://digizeitschriften.de/dms/img/?PPN=PPN252457811_1904&DMDID=dmdlog11&LOGID=log11&PHYSID=phys57#navi) (Fundamentals of a general theory of linear integral equations. (First report)), *Nachrichten von der Gesellschaft der Wissenschaften zu Göttingen, Mathematisch-Physikalische Klasse* (News of the Philosophical Society at Göttingen, mathematical-physical section), pp. 49–91. [From p. 51:](https://digizeitschriften.de/dms/img/?PPN=PPN252457811_1904&DMDID=dmdlog11&LOGID=log11&PHYSID=phys57#navi) *"Insbesondere in dieser ersten Mitteilung gelange ich zu Formeln, die die Entwickelung einer willkürlichen Funktion nach gewissen ausgezeichneten Funktionen, die ich 'Eigenfunktionen' nenne, liefern: ..."* (In particular, in this first report I arrive at formulas that provide the \[series\] development of an arbitrary function in terms of some distinctive functions, which I call *eigenfunctions*: ... ) Later on the same page: *"Dieser Erfolg ist wesentlich durch den Umstand bedingt, daß ich nicht, wie es bisher geschah, in erster Linie auf den Beweis für die Existenz der Eigenwerte ausgehe, ... "* (This success is mainly attributable to the fact that I do not, as it has happened until now, first of all aim at a proof of the existence of eigenvalues...)
    - For the origin and evolution of the terms eigenvalue, characteristic value, etc., see: [Earliest Known Uses of Some of the Words of Mathematics (E)](https://jeff560.tripod.com/e.html)
4.  For a proof of this lemma, see , p. 186, Theorem 8.2; , p. 109; , p. 364; and , p. 469, Theorem EDELI.
5.  By doing [Gaussian elimination](https://en.wikipedia.org/wiki/Gaussian_elimination) over [formal power series](https://en.wikipedia.org/wiki/Formal_power_series) truncated to n terms it is possible to get away with O(*n*<sup>4</sup>) operations, but that does not take [combinatorial explosion](https://en.wikipedia.org/wiki/Combinatorial_explosion) into account.

### Citations

1.  , p. 401.
2.  Strang, Gilbert. "6: Eigenvalues and Eigenvectors". [Introduction to Linear Algebra](https://math.mit.edu/~gs/linearalgebra/ila5/linearalgebra5_6-1.pdf) (PDF) (5 ed.). Wellesley-Cambridge Press.
3.  ^   , pp. 228, 229.
4.  ^   , p. 38.
5.  .
6.  ^   ["Eigenvector and Eigenvalue"](https://mathsisfun.com/algebra/eigenvalue.html). *www.mathsisfun.com*. Retrieved 19 August 2020.
7.  , p. 536.
8.  .
9.  ^    , p. 107.
10. , §2.
11. ^     , §3.
12. , p. 673.
13. ^   , pp. 807–808.
14. , pp. 715–716.
15. , pp. 706–707.
16. , p. 1063, p..
17. .
18. , pp. 265–271.
19. .
20. , §7.3.
21. , §7.3.
22. Cornell University Department of Mathematics (2016) [Lower-Level Courses for Freshmen and Sophomores](https://math.cornell.edu/m/Courses/Catalog/lowerlevel) [Archived](https://web.archive.org/web/20180407035031/http://www.math.cornell.edu/m/Courses/Catalog/lowerlevel) 7 April 2018 at the [Wayback Machine](https://en.wikipedia.org/wiki/Wayback_Machine). Accessed on 2016-03-27.
23. University of Michigan Mathematics (2016) [Math Course Catalogue](https://lsa.umich.edu/UMICH/math/Home/Undergrad/Ugrad_Courses.pdf) [Archived](https://web.archive.org/web/20151101101339/https://lsa.umich.edu/UMICH/math/Home/Undergrad/Ugrad_Courses.pdf) 2015-11-01 at the [Wayback Machine](https://en.wikipedia.org/wiki/Wayback_Machine). Accessed on 2016-03-27.
24. , p. 38.
25. , p. 358.
26. ^   , p. 316.
27. , pp. 305, 307.
28. ^   , p. 307.
29. , p. 272.
30. , pp. 115–116.
31. , p. 290.
32. , p. 116.
33. .
34. ^   .
35. .
36. .
37. , Section 14.3.5a.
38. , p. 217.
39. , p. 186 §8.
40. , p. 107; , p. 109.
41. , p. 111.
42. , p. 107; , p. 316; , p. 189 §8.
43. ^     .
44. , pp. 2309–2311.
45. ^   , p. 15005.
46. .
47. , pp. 1473–1477.
48. , pp. 114–150.
49. , p. 243.
50. Busche, Christian; Schiller, Beate. ["Endogene Geologie - Ruhr-Universität Bochum"](https://ruhr-uni-bochum.de/hardrock/downloads.html). *www.ruhr-uni-bochum.de*.
51. , pp. 103–107.
52. , pp. 365–382.
53. .
54. .

## Sources

- Aldrich, John (2006), ["Eigenvalue, eigenfunction, eigenvector, and related terms"](https://jeff560.tripod.com/e.html), in Miller, Jeff (ed.), *Earliest Known Uses of Some of the Words of Mathematics*
- Anton, Howard (1987), *Elementary Linear Algebra* (5th ed.), New York: [Wiley](https://en.wikipedia.org/wiki/John_Wiley_%26_Sons), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-84819-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-84819-6)
- Beauregard, Raymond A.; Fraleigh, John B. (1973), [A First Course In Linear Algebra: with Optional Introduction to Groups, Rings, and Fields](https://archive.org/details/firstcourseinlin0000beau), Boston: [Houghton Mifflin Co.](https://en.wikipedia.org/wiki/Houghton_Mifflin_Co.), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-395-14017-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-395-14017-8)
- Beezer, Robert A. (2006), [A first course in linear algebra](https://web.archive.org/web/20240829123652/http://linear.ups.edu/), Free online book under GNU licence, University of Puget Sound, archived from [the original](https://linear.ups.edu/) on 29 August 2024, retrieved 26 November 2023
- Bender, Nicholas; Yamilov, Alexey; Yilmaz, Hasan; Cao, Hui (14 October 2020). ["Fluctuations and Correlations of Transmission Eigenchannels in Diffusive Media"](https://journals.aps.org/prl/pdf/10.1103/PhysRevLett.125.165901). *Physical Review Letters*. **125** (16) 165901. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2004.12167](https://arxiv.org/abs/2004.12167). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2020PhRvL.125p5901B](https://ui.adsabs.harvard.edu/abs/2020PhRvL.125p5901B). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1103/physrevlett.125.165901](https://doi.org/10.1103%2Fphysrevlett.125.165901). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0031-9007](https://search.worldcat.org/issn/0031-9007). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [33124845](https://pubmed.ncbi.nlm.nih.gov/33124845). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [216553547](https://api.semanticscholar.org/CorpusID:216553547).
- Benn, D.; Evans, D. (2004), *A Practical Guide to the study of Glacial Sediments*, London: Arnold, pp. 103–107
- Betteridge, Harold T. (1965), *The New Cassell's German Dictionary*, New York: [Funk & Wagnall](https://en.wikipedia.org/wiki/Funk_%26_Wagnall), [LCCN](https://en.wikipedia.org/wiki/LCCN_(identifier)) [58-7924](https://lccn.loc.gov/58-7924)
- Burden, Richard L.; Faires, J. Douglas (1993), [Numerical Analysis](https://archive.org/details/numericalanalysi00burd) (5th ed.), Boston: Prindle, Weber and Schmidt, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-534-93219-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-534-93219-0)
- Denton, Peter B.; Parke, Stephen J.; Tao, Terence; Zhang, Xining (January 2022). ["Eigenvectors from Eigenvalues: A Survey of a Basic Identity in Linear Algebra"](https://ams.org/journals/bull/2022-59-01/S0273-0979-2021-01722-8/S0273-0979-2021-01722-8.pdf) (PDF). *Bulletin of the American Mathematical Society*. **59** (1): 31–58. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1908.03795](https://arxiv.org/abs/1908.03795). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1090/bull/1722](https://doi.org/10.1090%2Fbull%2F1722). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [213918682](https://api.semanticscholar.org/CorpusID:213918682). [Archived](https://web.archive.org/web/20220119071933/https://ams.org/journals/bull/2022-59-01/S0273-0979-2021-01722-8/S0273-0979-2021-01722-8.pdf) (PDF) from the original on 19 January 2022.
- Diekmann, O; Heesterbeek, JA; Metz, JA (1990), ["On the definition and the computation of the basic reproduction ratio R0 in models for infectious diseases in heterogeneous populations"](https://ir.cwi.nl/pub/2026), *Journal of Mathematical Biology*, **28** (4): 365–382, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/BF00178324](https://doi.org/10.1007%2FBF00178324), [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[1874/8051](https://hdl.handle.net/1874%2F8051), [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [2117040](https://pubmed.ncbi.nlm.nih.gov/2117040), [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [22275430](https://api.semanticscholar.org/CorpusID:22275430)
- Fraleigh, John B. (1976), *A First Course In Abstract Algebra* (2nd ed.), Reading: [Addison-Wesley](https://en.wikipedia.org/wiki/Addison-Wesley), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-201-01984-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-201-01984-1)
- Francis, J. G. F. (1961), "The QR Transformation, I (part 1)", *[The Computer Journal](https://en.wikipedia.org/wiki/The_Computer_Journal)*, vol. 4, no. 3, pp. 265–271, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1093/comjnl/4.3.265](https://doi.org/10.1093%2Fcomjnl%2F4.3.265)
- Francis, J. G. F. (1962), "The QR Transformation, II (part 2)", *The Computer Journal*, **4** (4): 332–345, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1093/comjnl/4.4.332](https://doi.org/10.1093%2Fcomjnl%2F4.4.332)
- Friedberg, Stephen H.; Insel, Arnold J.; Spence, Lawrence E. (1989), *Linear algebra* (2nd ed.), Englewood Cliffs, NJ: Prentice Hall, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-13-537102-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-13-537102-2)
- [Golub, Gene H.](https://en.wikipedia.org/wiki/Gene_H._Golub); [Van Loan, Charles F.](https://en.wikipedia.org/wiki/Charles_F._Van_Loan) (1996), *Matrix computations* (3rd ed.), Baltimore, MD: Johns Hopkins University Press, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8018-5414-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8018-5414-9)
- Graham, D.; Midgley, N. (2000), "Graphical representation of particle shape using triangular diagrams: an Excel spreadsheet method", *[Earth Surface Processes and Landforms](https://en.wikipedia.org/wiki/Earth_Surface_Processes_and_Landforms)*, **25** (13): 1473–1477, [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2000ESPL...25.1473G](https://ui.adsabs.harvard.edu/abs/2000ESPL...25.1473G), [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1002/1096-9837(200012)25:13<1473::AID-ESP158>3.0.CO;2-C](https://doi.org/10.1002%2F1096-9837%28200012%2925%3A13%3C1473%3A%3AAID-ESP158%3E3.0.CO%3B2-C), [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [128825838](https://api.semanticscholar.org/CorpusID:128825838)
- Hawkins, T. (1975), "Cauchy and the spectral theory of matrices", *Historia Mathematica*, **2**: 1–29, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/0315-0860(75)90032-4](https://doi.org/10.1016%2F0315-0860%2875%2990032-4)
- Heesterbeek, J. A. P.; Diekmann, Odo (2000), *Mathematical epidemiology of infectious diseases*, Wiley series in mathematical and computational biology, West Sussex, England: John Wiley & Sons
- Hefferon, Jim (2001), [Linear Algebra](https://web.archive.org/web/20231004154906/https://joshua.smcvt.edu/linearalgebra/), Colchester, VT: Online book, St Michael's College, archived from [the original](https://joshua.smcvt.edu/linearalgebra/) on 4 October 2023, retrieved 26 November 2023
- Herstein, I. N. (1964), *Topics In Algebra*, Waltham: Blaisdell Publishing Company, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-114-54101-6](https://en.wikipedia.org/wiki/Special:BookSources/978-1-114-54101-6) `{{`[`citation`](https://en.wikipedia.org/wiki/Template:Citation)`}}`: ISBN / Date incompatibility ([help](https://en.wikipedia.org/wiki/Help:CS1_errors#invalid_isbn_date))
- Kline, Morris (1972), *Mathematical thought from ancient to modern times*, Oxford University Press, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-19-501496-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-19-501496-9)
- Knox-Robinson, C.; Gardoll, Stephen J. (1998), "GIS-stereoplot: an interactive stereonet plotting module for ArcView 3.0 geographic information system", *Computers & Geosciences*, **24** (3): 243, [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1998CG.....24..243K](https://ui.adsabs.harvard.edu/abs/1998CG.....24..243K), [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/S0098-3004(97)00122-2](https://doi.org/10.1016%2FS0098-3004%2897%2900122-2)
- Korn, Granino A.; [Korn, Theresa M.](https://en.wikipedia.org/wiki/Theresa_M._Korn) (2000), "Mathematical Handbook for Scientists and Engineers: Definitions, Theorems, and Formulas for Reference and Review", *New York: McGraw-Hill* (2nd Revised ed.), [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1968mhse.book.....K](https://ui.adsabs.harvard.edu/abs/1968mhse.book.....K), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-486-41147-7](https://en.wikipedia.org/wiki/Special:BookSources/978-0-486-41147-7)`{{`[`citation`](https://en.wikipedia.org/wiki/Template:Citation)`}}`: CS1 maint: work parameter with ISBN ([link](https://en.wikipedia.org/wiki/Category:CS1_maint:_work_parameter_with_ISBN))
- Krivoruchenko, M. I.; Simkovic, F. (2024), "Neutrino mixing matrix in terms of neutrino mass matrix and its Frobenius covariants", *Physics of Particles and Nuclei Letters*, **1** (21): 1–4, [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2306.10638](https://arxiv.org/abs/2306.10638), [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2024PPNL...21....1K](https://ui.adsabs.harvard.edu/abs/2024PPNL...21....1K), [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1134/S1547477124010072](https://doi.org/10.1134%2FS1547477124010072)
- Kublanovskaya, Vera N. (1962), "On some algorithms for the solution of the complete eigenvalue problem", *USSR Computational Mathematics and Mathematical Physics*, **1** (3): 637–657, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/0041-5553(63)90168-X](https://doi.org/10.1016%2F0041-5553%2863%2990168-X)
- Lipschutz, Seymour; Lipson, Marc (12 August 2002). [Schaum's Easy Outline of Linear Algebra](https://books.google.com/books?id=pkESXAcIiCQC&pg=PA111). McGraw Hill Professional. p. 111. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-07-139880-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-07-139880-0).
- Meyer, Carl D. (2000), *Matrix analysis and applied linear algebra*, Philadelphia: Society for Industrial and Applied Mathematics (SIAM), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-89871-454-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-89871-454-8)
- Nering, Evar D. (1970), *Linear Algebra and Matrix Theory* (2nd ed.), New York: [Wiley](https://en.wikipedia.org/wiki/John_Wiley_%26_Sons), [LCCN](https://en.wikipedia.org/wiki/LCCN_(identifier)) [76091646](https://lccn.loc.gov/76091646)
- Press, William H.; [Teukolsky, Saul A.](https://en.wikipedia.org/wiki/Saul_Teukolsky); Vetterling, William T.; Flannery, Brian P. (2007), *Numerical Recipes: The Art of Scientific Computing* (3rd ed.), Cambridge University Press, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-88068-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-88068-8)
- Roman, Steven (2008), *Advanced linear algebra* (3rd ed.), New York: Springer Science + Business Media, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-72828-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-72828-5)
- Rotter, Stefan; Gigan, Sylvain (2 March 2017). ["Light fields in complex media: Mesoscopic scattering meets wave control"](https://link.aps.org/doi/10.1103/RevModPhys.89.015005). *Reviews of Modern Physics*. **89** (1) 015005. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1702.05395](https://arxiv.org/abs/1702.05395). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2017RvMP...89a5005R](https://ui.adsabs.harvard.edu/abs/2017RvMP...89a5005R). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1103/RevModPhys.89.015005](https://doi.org/10.1103%2FRevModPhys.89.015005). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [119330480](https://api.semanticscholar.org/CorpusID:119330480).
- [Shilov, Georgi E.](https://en.wikipedia.org/wiki/Georgiy_Shilov) (1977), *Linear algebra*, Translated and edited by Richard A. Silverman, New York: Dover Publications, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-486-63518-7](https://en.wikipedia.org/wiki/Special:BookSources/978-0-486-63518-7)
- Sneed, E. D.; Folk, R. L. (1958), "Pebbles in the lower Colorado River, Texas, a study of particle morphogenesis", *Journal of Geology*, **66** (2): 114–150, [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1958JG.....66..114S](https://ui.adsabs.harvard.edu/abs/1958JG.....66..114S), [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1086/626490](https://doi.org/10.1086%2F626490), [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [129658242](https://api.semanticscholar.org/CorpusID:129658242)
- Trefethen, Lloyd N.; Bau, David (1997), *Numerical Linear Algebra*, SIAM
- Van Mieghem, Piet (18 January 2014). "Graph eigenvectors, fundamental weights and centrality metrics for nodes in networks". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1401.4580](https://arxiv.org/abs/1401.4580) \[[math.SP](https://arxiv.org/archive/math.SP)\].
- Vellekoop, I. M.; Mosk, A. P. (15 August 2007). ["Focusing coherent light through opaque strongly scattering media"](https://osapublishing.org/ol/abstract.cfm?uri=ol-32-16-2309). *Optics Letters*. **32** (16): 2309–2311. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2007OptL...32.2309V](https://ui.adsabs.harvard.edu/abs/2007OptL...32.2309V). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1364/OL.32.002309](https://doi.org/10.1364%2FOL.32.002309). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1539-4794](https://search.worldcat.org/issn/1539-4794). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [17700768](https://pubmed.ncbi.nlm.nih.gov/17700768). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [45359403](https://api.semanticscholar.org/CorpusID:45359403).
- Weisstein, Eric W. ["Eigenvector"](https://mathworld.wolfram.com/Eigenvector.html). *mathworld.wolfram.com*. Retrieved 4 August 2019.
- Weisstein, Eric W. (n.d.). ["Eigenvalue"](https://mathworld.wolfram.com/Eigenvalue.html#:~:text=Eigenvalues%20are%20a%20special%20set,Marcus%20and%20Minc%201988,%20p.). *mathworld.wolfram.com*. Retrieved 19 August 2020.
- Wolchover, Natalie (13 November 2019). ["Neutrinos Lead to Unexpected Discovery in Basic Math"](https://quantamagazine.org/neutrinos-lead-to-unexpected-discovery-in-basic-math-20191113/). *Quanta Magazine*. Retrieved 27 November 2019.
- Xirouhakis, A.; Votsis, G.; Delopoulus, A. (1999). Tzafestas, Spyros G. (ed.). [Estimation of 3D motion and structure of human faces](http://link.springer.com/10.1007/978-94-011-4840-5_30). Dordrecht: National Technical University of Athens. pp. 333–344. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-94-011-4840-5_30](https://doi.org/10.1007%2F978-94-011-4840-5_30). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4020-0393-6](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4020-0393-6).
- Van Mieghem, P. (2024). ["Eigenvector components of symmetric, graph-related matrices"](https://doi.org/10.1016%2Fj.laa.2024.03.035). *Linear Algebra and Its Applications*. **692**: 91–134. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.laa.2024.03.035](https://doi.org/10.1016%2Fj.laa.2024.03.035).

## Further reading

- [Golub, Gene H.](https://en.wikipedia.org/wiki/Gene_H._Golub); [van der Vorst, Henk A.](https://en.wikipedia.org/wiki/Henk_van_der_Vorst) (2000), ["Eigenvalue Computation in the 20th Century"](https://dspace.library.uu.nl/bitstream/1874/2663/1/eighistory.pdf) (PDF), *Journal of Computational and Applied Mathematics*, **123** (1–2): 35–65, [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2000JCoAM.123...35G](https://ui.adsabs.harvard.edu/abs/2000JCoAM.123...35G), [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/S0377-0427(00)00413-1](https://doi.org/10.1016%2FS0377-0427%2800%2900413-1), [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[1874/2663](https://hdl.handle.net/1874%2F2663)
- Hill, Roger (2009). ["λ – Eigenvalues"](https://sixtysymbols.com/videos/eigenvalues.htm). *Sixty Symbols*. [Brady Haran](https://en.wikipedia.org/wiki/Brady_Haran) for the [University of Nottingham](https://en.wikipedia.org/wiki/University_of_Nottingham).
- Kuttler, Kenneth (2017), [An introduction to linear algebra](https://web.archive.org/web/20231217154253/https://math.byu.edu/~klkuttle/Linearalgebra.pdf) (PDF), Brigham Young University, archived from [the original](https://math.byu.edu/~klkuttle/Linearalgebra.pdf) (PDF) on 17 December 2023, retrieved 26 November 2023
- [Strang, Gilbert](https://en.wikipedia.org/wiki/Gilbert_Strang) (1993), *Introduction to linear algebra*, Wellesley, MA: Wellesley-Cambridge Press, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-9614088-5-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-9614088-5-5)
- Strang, Gilbert (2006), *Linear algebra and its applications*, Belmont, CA: Thomson, Brooks/Cole, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-03-010567-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-03-010567-8)

## External links

- [What are Eigen Values?](https://physlink.com/education/AskExperts/ae520.cfm) – non-technical introduction from PhysLink.com's "Ask the Experts"
- [Eigen Values and Eigen Vectors Numerical Examples](https://people.revoledu.com/kardi/tutorial/LinearAlgebra/EigenValueEigenVector.html) – Tutorial and Interactive Program from Revoledu.
- [Introduction to Eigen Vectors and Eigen Values](https://web.archive.org/web/20100325112901/https://khanexercises.appspot.com/video?v=PhfbEr2btGQ) – lecture from Khan Academy
- [Eigenvectors and eigenvalues | Essence of linear algebra, chapter 10](https://youtube.com/watch?v=PFDu9oVAE-g&list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab&index=14) – A visual explanation with [3Blue1Brown](https://en.wikipedia.org/wiki/3Blue1Brown)
- [Matrix Eigenvectors Calculator](https://symbolab.com/solver/matrix-eigenvectors-calculator) from Symbolab (Click on the bottom right button of the 2×12 grid to select a matrix size. Select an $n\times n$ size (for a square matrix), then fill out the entries numerically and click on the Go button. It can accept complex numbers as well.)

![[media/0b4e0c4f7e001cdcd02966251f71a5d02cf33fbb.png]] Wikiversity uses introductory physics to introduce [Eigenvalues and eigenvectors](https://en.wikiversity.org/wiki/Physics/A/Eigenvalues_for_beginners)

### Theory

- [Computation of Eigenvalues](https://sosmath.com/matrix/eigen1/eigen1.html)
- [Numerical solution of eigenvalue problems](https://cs.utk.edu/~dongarra/etemplates/index.html) Edited by Zhaojun Bai, [James Demmel](https://en.wikipedia.org/wiki/James_Demmel), Jack Dongarra, Axel Ruhe, and [Henk van der Vorst](https://en.wikipedia.org/wiki/Henk_van_der_Vorst)
