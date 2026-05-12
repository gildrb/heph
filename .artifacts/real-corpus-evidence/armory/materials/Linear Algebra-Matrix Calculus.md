[[linear-algebra.base]]

> Source: [[Matrix Calculus]]
> License: Wikipedia content is available under CC BY-SA 4.0.

In [mathematics](https://en.wikipedia.org/wiki/Mathematics), **matrix calculus** is a specialized notation for doing [[Multivariable Calculus]], especially over spaces of [matrices](https://en.wikipedia.org/wiki/Matrix_(mathematics) "Matrix (mathematics)"). It collects the various [partial derivatives](https://en.wikipedia.org/wiki/Partial_derivative) of a single [function](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)") with respect to many [variables](https://en.wikipedia.org/wiki/Variable_(mathematics) "Variable (mathematics)"), and/or of a [multivariate function](https://en.wikipedia.org/wiki/Multivariate_function) with respect to a single variable, into [vectors](https://en.wikipedia.org/wiki/Vector_(mathematics_and_physics) "Vector (mathematics and physics)") and matrices that can be treated as single entities. This greatly simplifies operations such as finding the maximum or minimum of a multivariate function and solving systems of [differential equations](https://en.wikipedia.org/wiki/Differential_equation). The notation used here is commonly used in [statistics](https://en.wikipedia.org/wiki/Statistics) and [engineering](https://en.wikipedia.org/wiki/Engineering), while the [tensor index notation](https://en.wikipedia.org/wiki/Tensor_index_notation) is preferred in [physics](https://en.wikipedia.org/wiki/Physics).

Two competing notational conventions split the field of matrix calculus into two separate groups. The two groups can be distinguished by whether they write the derivative of a [scalar](https://en.wikipedia.org/wiki/Scalar_(mathematics) "Scalar (mathematics)") with respect to a vector as a [column vector or a row vector](https://en.wikipedia.org/wiki/Row_and_column_vectors). Both of these conventions are possible even when the common assumption is made that vectors should be treated as column vectors when combined with matrices (rather than row vectors). A single convention can be somewhat standard throughout a single field that commonly uses matrix calculus (e.g. [econometrics](https://en.wikipedia.org/wiki/Econometrics), statistics, [estimation theory](https://en.wikipedia.org/wiki/Estimation_theory) and [machine learning](https://en.wikipedia.org/wiki/Machine_learning)). However, even within a given field different authors can be found using competing conventions. Authors of both groups often write as though their specific conventions were standard. Serious mistakes can result when combining results from different authors without carefully verifying that compatible notations have been used. Definitions of these two conventions and comparisons between them are collected in the [layout conventions](#Layout_conventions) section.

## Scope

Matrix calculus refers to a number of different notations that use matrices and vectors to collect the derivative of each component of the dependent variable with respect to each component of the independent variable. In general, the independent variable can be a scalar, a vector, or a matrix while the dependent variable can be any of these as well. Each different situation will lead to a different set of rules, or a separate [calculus](https://en.wikipedia.org/wiki/Calculus), using the broader sense of the term. Matrix notation serves as a convenient way to collect the many derivatives in an organized way.

As a first example, consider the [gradient](https://en.wikipedia.org/wiki/Gradient) from [vector calculus](https://en.wikipedia.org/wiki/Vector_calculus). For a scalar function of three independent variables, $f(x_{1},x_{2},x_{3})$, the gradient is given by the vector equation

$\nabla f={\frac {\partial f}{\partial x_{1}}}{\hat {x}}_{1}+{\frac {\partial f}{\partial x_{2}}}{\hat {x}}_{2}+{\frac {\partial f}{\partial x_{3}}}{\hat {x}}_{3},$

where ${\hat {x}}_{i}$ represents a unit vector in the $x_{i}$ direction for $1\leq i\leq 3$. This type of generalized derivative can be seen as the derivative of a scalar, *f*, with respect to a vector, $\mathbf {x}$, and its result can be easily collected in vector form.

$\nabla f=\left({\frac {\partial f}{\partial \mathbf {x} }}\right)^{\mathsf {T}}={\begin{bmatrix}{\dfrac {\partial f}{\partial x_{1}}}&{\dfrac {\partial f}{\partial x_{2}}}&{\dfrac {\partial f}{\partial x_{3}}}\\\end{bmatrix}}^{\textsf {T}}.$

More complicated examples include the derivative of a scalar function with respect to a matrix, known as the [gradient matrix](#Derivatives_with_matrices), which collects the derivative with respect to each matrix element in the corresponding position in the resulting matrix. In that case the scalar must be a function of each of the independent variables in the matrix. As another example, if we have an n-vector of dependent variables, or functions, of m independent variables we might consider the derivative of the dependent vector with respect to the independent vector. The result could be collected in an *m*×*n* matrix consisting of all of the possible derivative combinations.

There are a total of nine possibilities using scalars, vectors, and matrices. Notice that as we consider higher numbers of components in each of the independent and dependent variables we can be left with a very large number of possibilities. The six kinds of derivatives that can be most neatly organized in matrix form are collected in the following table.

|  |  |  |  |
|----|----|----|----|
| Types | Scalar | Vector | Matrix |
| Scalar | ${\frac {\partial y}{\partial x}}$ | ${\frac {\partial \mathbf {y} }{\partial x}}$ | ${\frac {\partial \mathbf {Y} }{\partial x}}$ |
| Vector | ${\frac {\partial y}{\partial \mathbf {x} }}$ | ${\frac {\partial \mathbf {y} }{\partial \mathbf {x} }}$ |  |
| Matrix | ${\frac {\partial y}{\partial \mathbf {X} }}$ |  |  |

Types of matrix derivative {.wikitable style="text-align:center; width:35%;"}

Here, we have used the term "matrix" in its most general sense, recognizing that vectors are simply matrices with one column (and scalars are simply vectors with one row). Moreover, we have used bold letters to indicate vectors and bold capital letters for matrices. This notation is used throughout.

Notice that we could also talk about the derivative of a vector with respect to a matrix, or any of the other unfilled cells in our table. However, these derivatives are most naturally organized in a [tensor](https://en.wikipedia.org/wiki/Tensor) of rank higher than 2, so that they do not fit neatly into a matrix. In the following three sections we will define each one of these derivatives and relate them to other branches of mathematics. See the [layout conventions](#Layout_conventions) section for a more detailed table.

### Relation to other derivatives

The matrix derivative is a convenient notation for keeping track of partial derivatives for doing calculations. The [Fréchet derivative](https://en.wikipedia.org/wiki/Fr%C3%A9chet_derivative) is the standard way in the setting of [functional analysis](https://en.wikipedia.org/wiki/Functional_analysis) to take derivatives with respect to vectors. In the case that a matrix function of a matrix is Fréchet differentiable, the two derivatives will agree up to translation of notations. As is the case in general for [partial derivatives](https://en.wikipedia.org/wiki/Partial_derivative), some formulae may extend under weaker analytic conditions than the existence of the derivative as approximating linear mapping.

### Usages

Matrix calculus is used for deriving optimal stochastic estimators, often involving the use of [[Lagrange Multipliers]]. This includes the derivation of:

- [Kalman filter](https://en.wikipedia.org/wiki/Kalman_filter)
- [Wiener filter](https://en.wikipedia.org/wiki/Wiener_filter)
- [Expectation-maximization algorithm for Gaussian mixture](https://en.wikipedia.org/wiki/Expectation-maximization_algorithm#Gaussian_mixture)
- [[Gradient Descent]]

## Notation

The vector and matrix derivatives presented in the sections to follow take full advantage of [matrix notation](https://en.wikipedia.org/wiki/Matrix_notation), using a single variable to represent a large number of variables. In what follows we will distinguish scalars, vectors and matrices by their typeface. We will let *M*(*n*,*m*) denote the space of [real](https://en.wikipedia.org/wiki/Real_number) *n*×*m* matrices with *n* rows and *m* columns. Such matrices will be denoted using bold capital letters: **A**, **X**, **Y**, etc. An element of *M*(*n*,1), that is, a [column vector](https://en.wikipedia.org/wiki/Column_vector), is denoted with a boldface lowercase letter: **a**, **x**, **y**, etc. An element of *M*(1,1) is a scalar, denoted with lowercase italic typeface: *a*, *t*, *x*, etc. **X**<sup>T</sup> denotes matrix [transpose](https://en.wikipedia.org/wiki/Transpose), tr(**X**) is the [trace](https://en.wikipedia.org/wiki/Trace_(linear_algebra) "Trace (linear algebra)"), and det(**X**) or \|**X**\| is the [[Determinant]]. All functions are assumed to be of [differentiability class](https://en.wikipedia.org/wiki/Differentiability_class) *C*<sup>1</sup> unless otherwise noted. Generally letters from the first half of the alphabet (a, b, c, ...) will be used to denote constants, and from the second half (t, x, y, ...) to denote variables.

**NOTE**: As mentioned above, there are competing notations for laying out systems of [partial derivatives](https://en.wikipedia.org/wiki/Partial_derivative) in vectors and matrices, and no standard appears to be emerging yet. The next two introductory sections use the [numerator layout convention](#Layout_conventions) simply for the purposes of convenience, to avoid overly complicating the discussion. The section after them discusses [layout conventions](#Layout_conventions) in more detail. It is important to realize the following:

1.  Despite the use of the terms "numerator layout" and "denominator layout", there are actually more than two possible notational choices involved. The reason is that the choice of numerator vs. denominator (or in some situations, numerator vs. mixed) can be made independently for scalar-by-vector, vector-by-scalar, vector-by-vector, and scalar-by-matrix derivatives, and a number of authors mix and match their layout choices in various ways.
2.  The choice of numerator layout in the introductory sections below does not imply that this is the "correct" or "superior" choice. There are advantages and disadvantages to the various layout types. Serious mistakes can result from carelessly combining formulas written in different layouts, and converting from one layout to another requires care to avoid errors. As a result, when working with existing formulas the best policy is probably to identify whichever layout is used and maintain consistency with it, rather than attempting to use the same layout in all situations.

### Alternatives

The [tensor index notation](https://en.wikipedia.org/wiki/Tensor_index_notation) with its [Einstein summation](https://en.wikipedia.org/wiki/Einstein_summation) convention is very similar to the matrix calculus, except one writes only a single component at a time. It has the advantage that one can easily manipulate arbitrarily high rank tensors, whereas tensors of rank higher than two are quite unwieldy with matrix notation. All of the work here can be done in this notation without use of the single-variable matrix notation. However, many problems in estimation theory and other areas of applied mathematics would result in too many indices to properly keep track of, pointing in favor of matrix calculus in those areas. Also, Einstein notation can be very useful in proving the identities presented here (see section on [differentiation](https://en.wikipedia.org/wiki/Ricci_calculus#Differentiation)) as an alternative to typical element notation, which can become cumbersome when the explicit sums are carried around. Note that a matrix can be considered a tensor of rank two.

## Derivatives with vectors

Because vectors are matrices with only one column, the simplest matrix derivatives are vector derivatives.

The notations developed here can accommodate the usual operations of [vector calculus](https://en.wikipedia.org/wiki/Vector_calculus) by identifying the space *M*(*n*,1) of n-vectors with the [Euclidean space](https://en.wikipedia.org/wiki/Euclidean_space) **R**<sup>*n*</sup>, and the scalar *M*(1,1) is identified with **R**. The corresponding concept from vector calculus is indicated at the end of each subsection.

**NOTE**: The discussion in this section assumes the [numerator layout convention](#Layout_conventions) for pedagogical purposes. Some authors use different conventions. The section on [layout conventions](#Layout_conventions) discusses this issue in greater detail. The identities given further down are presented in forms that can be used in conjunction with all common layout conventions.

### Vector-by-scalar

The [derivative](https://en.wikipedia.org/wiki/Derivative) of a [vector](https://en.wikipedia.org/wiki/Euclidean_vector) $\mathbf {y} ={\begin{bmatrix}y_{1}&y_{2}&\cdots &y_{m}\end{bmatrix}}^{\mathsf {T}}$, by a [scalar](https://en.wikipedia.org/wiki/Scalar_(mathematics) "Scalar (mathematics)") *x* is written (in [numerator layout notation](#Layout_conventions)) as

${\frac {d\mathbf {y} }{dx}}={\begin{bmatrix}{\frac {dy_{1}}{dx}}\\{\frac {dy_{2}}{dx}}\\\vdots \\{\frac {dy_{m}}{dx}}\\\end{bmatrix}}.$

In [vector calculus](https://en.wikipedia.org/wiki/Vector_calculus) the derivative of a vector **y** with respect to a scalar *x* is known as the **[tangent vector](https://en.wikipedia.org/wiki/Tangent_vector)** of the vector **y**, ${\frac {\partial \mathbf {y} }{\partial x}}$. Notice here that **y**: **R**<sup>1</sup> → **R**<sup>*m*</sup>.

**Example** Simple examples of this include the [velocity](https://en.wikipedia.org/wiki/Velocity) vector in [Euclidean space](https://en.wikipedia.org/wiki/Euclidean_space), which is the [tangent vector](https://en.wikipedia.org/wiki/Tangent_vector) of the [position](https://en.wikipedia.org/wiki/Position_(vector)) vector (considered as a function of time). Also, the [acceleration](https://en.wikipedia.org/wiki/Acceleration) is the tangent vector of the velocity.

### Scalar-by-vector

The [derivative](https://en.wikipedia.org/wiki/Derivative) of a [scalar](https://en.wikipedia.org/wiki/Scalar_(mathematics) "Scalar (mathematics)") *y* by a vector $\mathbf {x} ={\begin{bmatrix}x_{1}&x_{2}&\cdots &x_{n}\end{bmatrix}}$, is written (in [numerator layout notation](#Layout_conventions)) as

${\frac {\partial y}{\partial \mathbf {x} }}={\begin{bmatrix}{\dfrac {\partial y}{\partial x_{1}}}&{\dfrac {\partial y}{\partial x_{2}}}&\cdots &{\dfrac {\partial y}{\partial x_{n}}}\end{bmatrix}}.$

In [vector calculus](https://en.wikipedia.org/wiki/Vector_calculus), the [gradient](https://en.wikipedia.org/wiki/Gradient) of a scalar field **f** : **R**<sup>n</sup> → **R** (whose independent coordinates are the components of **x**) is the transpose of the derivative of a scalar by a vector.

$\nabla f={\begin{bmatrix}{\frac {\partial f}{\partial x_{1}}}\\\vdots \\{\frac {\partial f}{\partial x_{n}}}\end{bmatrix}}=\left({\frac {\partial f}{\partial \mathbf {x} }}\right)^{\mathsf {T}}$

For example, in physics, the [electric field](https://en.wikipedia.org/wiki/Electric_field) is the negative vector [gradient](https://en.wikipedia.org/wiki/Gradient) of the [electric potential](https://en.wikipedia.org/wiki/Electric_potential).

The [directional derivative](https://en.wikipedia.org/wiki/Directional_derivative) of a scalar function *f*(**x**) of the space vector **x** in the direction of the unit vector **u** (represented in this case as a column vector) is defined using the gradient as follows.

$\nabla _{\mathbf {u} }{f}(\mathbf {x} )=\nabla f(\mathbf {x} )\cdot \mathbf {u}$

Using the notation just defined for the derivative of a scalar with respect to a vector we can re-write the directional derivative as $\nabla _{\mathbf {u} }f={\frac {\partial f}{\partial \mathbf {x} }}\mathbf {u} .$ This type of notation will be nice when proving product rules and chain rules that come out looking similar to what we are familiar with for the scalar [derivative](https://en.wikipedia.org/wiki/Derivative).

### Vector-by-vector

Each of the previous two cases can be considered as an application of the derivative of a vector with respect to a vector, using a vector of size one appropriately. Similarly we will find that the derivatives involving matrices will reduce to derivatives involving vectors in a corresponding way.

The derivative of a [vector function](https://en.wikipedia.org/wiki/Vector_function) (a vector whose components are functions) $\mathbf {y} ={\begin{bmatrix}y_{1}&y_{2}&\cdots &y_{m}\end{bmatrix}}^{\mathsf {T}}$, with respect to an input vector, $\mathbf {x} ={\begin{bmatrix}x_{1}&x_{2}&\cdots &x_{n}\end{bmatrix}}^{\mathsf {T}}$, is written (in [numerator layout notation](#Layout_conventions)) as

${\frac {\partial \mathbf {y} }{\partial \mathbf {x} }}={\begin{bmatrix}{\frac {\partial y_{1}}{\partial x_{1}}}&{\frac {\partial y_{1}}{\partial x_{2}}}&\cdots &{\frac {\partial y_{1}}{\partial x_{n}}}\\{\frac {\partial y_{2}}{\partial x_{1}}}&{\frac {\partial y_{2}}{\partial x_{2}}}&\cdots &{\frac {\partial y_{2}}{\partial x_{n}}}\\\vdots &\vdots &\ddots &\vdots \\{\frac {\partial y_{m}}{\partial x_{1}}}&{\frac {\partial y_{m}}{\partial x_{2}}}&\cdots &{\frac {\partial y_{m}}{\partial x_{n}}}\\\end{bmatrix}}.$

In [vector calculus](https://en.wikipedia.org/wiki/Vector_calculus), the derivative of a vector function **y** with respect to a vector **x** whose components represent a space is known as the **[pushforward (or differential)](https://en.wikipedia.org/wiki/Pushforward_(differential) "Pushforward (differential)")**, or the **[[Jacobian Matrix]]**.

The pushforward along a vector function **f** with respect to vector **v** in **R**<sup>*n*</sup> is given by $d\mathbf {f} (\mathbf {v} )={\frac {\partial \mathbf {f} }{\partial \mathbf {v} }}d\mathbf {v} .$

## Derivatives with matrices

There are two types of derivatives with matrices that can be organized into a matrix of the same size. These are the derivative of a matrix by a scalar and the derivative of a scalar by a matrix. These can be useful in minimization problems found in many areas of applied mathematics and have adopted the names **tangent matrix** and **gradient matrix** respectively after their analogs for vectors.

**Note**: The discussion in this section assumes the [numerator layout convention](#Layout_conventions) for pedagogical purposes. Some authors use different conventions. The section on [layout conventions](#Layout_conventions) discusses this issue in greater detail. The identities given further down are presented in forms that can be used in conjunction with all common layout conventions.

### Matrix-by-scalar

The derivative of a matrix function **Y** by a scalar *x* is known as the **tangent matrix** and is given (in [numerator layout notation](#Layout_conventions)) by

${\frac {\partial \mathbf {Y} }{\partial x}}={\begin{bmatrix}{\frac {\partial y_{11}}{\partial x}}&{\frac {\partial y_{12}}{\partial x}}&\cdots &{\frac {\partial y_{1n}}{\partial x}}\\{\frac {\partial y_{21}}{\partial x}}&{\frac {\partial y_{22}}{\partial x}}&\cdots &{\frac {\partial y_{2n}}{\partial x}}\\\vdots &\vdots &\ddots &\vdots \\{\frac {\partial y_{m1}}{\partial x}}&{\frac {\partial y_{m2}}{\partial x}}&\cdots &{\frac {\partial y_{mn}}{\partial x}}\\\end{bmatrix}}.$

### Scalar-by-matrix

The derivative of a scalar function *y*, with respect to a *p*×*q* matrix **X** of independent variables, is given (in [numerator layout notation](#Layout_conventions)) by

${\frac {\partial y}{\partial \mathbf {X} }}={\begin{bmatrix}{\frac {\partial y}{\partial x_{11}}}&{\frac {\partial y}{\partial x_{21}}}&\cdots &{\frac {\partial y}{\partial x_{p1}}}\\{\frac {\partial y}{\partial x_{12}}}&{\frac {\partial y}{\partial x_{22}}}&\cdots &{\frac {\partial y}{\partial x_{p2}}}\\\vdots &\vdots &\ddots &\vdots \\{\frac {\partial y}{\partial x_{1q}}}&{\frac {\partial y}{\partial x_{2q}}}&\cdots &{\frac {\partial y}{\partial x_{pq}}}\\\end{bmatrix}}.$

Important examples of scalar functions of matrices include the [trace](https://en.wikipedia.org/wiki/Trace_(linear_algebra) "Trace (linear algebra)") of a matrix and the [[Determinant]].

In analog with [vector calculus](https://en.wikipedia.org/wiki/Vector_calculus) this derivative is often written as the following.

$\nabla _{\mathbf {X} }y(\mathbf {X} )={\frac {\partial y(\mathbf {X} )}{\partial \mathbf {X} }}$

Also in analog with [vector calculus](https://en.wikipedia.org/wiki/Vector_calculus), the **directional derivative** of a scalar *f*(**X**) of a matrix **X** in the direction of matrix **Y** is given by

$\nabla _{\mathbf {Y} }f=\operatorname {tr} \left({\frac {\partial f}{\partial \mathbf {X} }}\mathbf {Y} \right).$

It is the gradient matrix, in particular, that finds many uses in minimization problems in [estimation theory](https://en.wikipedia.org/wiki/Estimation_theory), particularly in the [derivation](https://en.wikipedia.org/wiki/Kalman_filter#Derivations) of the [Kalman filter](https://en.wikipedia.org/wiki/Kalman_filter) algorithm, which is of great importance in the field.

### Other matrix derivatives

The three types of derivatives that have not been considered are those involving vectors-by-matrices, matrices-by-vectors, and matrices-by-matrices. These are not as widely considered and a notation is not widely agreed upon.

## Layout conventions

This section discusses the similarities and differences between notational conventions that are used in the various fields that take advantage of matrix calculus. Although there are largely two consistent conventions, some authors find it convenient to mix the two conventions in forms that are discussed below. After this section, equations will be listed in both competing forms separately.

The fundamental issue is that the derivative of a vector with respect to a vector, i.e. ${\frac {\partial \mathbf {y} }{\partial \mathbf {x} }}$, is often written in two competing ways. If the numerator **y** is of size *m* and the denominator **x** of size *n*, then the result can be laid out as either an *m*×*n* matrix or *n*×*m* matrix, i.e. the *m* elements of **y** laid out in rows and the *n* elements of **x** laid out in columns, or vice versa. This leads to the following possibilities:

1.  *Numerator layout*, i.e. lay out according to **y** and **x**<sup>T</sup> (i.e. contrarily to **x**). This is sometimes known as the *Jacobian formulation*. This corresponds to the *m*×*n* layout in the previous example, which means that the row number of ${\frac {\partial \mathbf {y} }{\partial \mathbf {x} }}$ equals to the size of the numerator $\mathbf {y}$ and the column number of ${\frac {\partial \mathbf {y} }{\partial \mathbf {x} }}$ equals to the size of **x**<sup>T</sup>.
2.  *Denominator layout*, i.e. lay out according to **y**<sup>T</sup> and **x** (i.e. contrarily to **y**). This is sometimes known as the *Hessian formulation*. Some authors term this layout the *gradient*, in distinction to the *Jacobian* (numerator layout), which is its transpose. (However, *[gradient](https://en.wikipedia.org/wiki/Gradient)* more commonly means the derivative ${\frac {\partial y}{\partial \mathbf {x} }},$ regardless of layout.). This corresponds to the *n×m* layout in the previous example, which means that the row number of ${\frac {\partial \mathbf {y} }{\partial \mathbf {x} }}$ equals to the size of **x** (the denominator).
3.  A third possibility sometimes seen is to insist on writing the derivative as ${\frac {\partial \mathbf {y} }{\partial \mathbf {x} '}},$ (i.e. the derivative is taken with respect to the transpose of **x**) and follow the numerator layout. This makes it possible to claim that the matrix is laid out according to both numerator and denominator. In practice this produces results the same as the numerator layout.

When handling the [gradient](https://en.wikipedia.org/wiki/Gradient) ${\frac {\partial y}{\partial \mathbf {x} }}$ and the opposite case ${\frac {\partial \mathbf {y} }{\partial x}},$ we have the same issues. To be consistent, we should do one of the following:

1.  If we choose numerator layout for ${\frac {\partial \mathbf {y} }{\partial \mathbf {x} }},$ we should lay out the [gradient](https://en.wikipedia.org/wiki/Gradient) ${\frac {\partial y}{\partial \mathbf {x} }}$ as a row vector, and ${\frac {\partial \mathbf {y} }{\partial x}}$ as a column vector.
2.  If we choose denominator layout for ${\frac {\partial \mathbf {y} }{\partial \mathbf {x} }},$ we should lay out the [gradient](https://en.wikipedia.org/wiki/Gradient) ${\frac {\partial y}{\partial \mathbf {x} }}$ as a column vector, and ${\frac {\partial \mathbf {y} }{\partial x}}$ as a row vector.
3.  In the third possibility above, we write ${\frac {\partial y}{\partial \mathbf {x} '}}$ and ${\frac {\partial \mathbf {y} }{\partial x}},$ and use numerator layout.

Not all math textbooks and papers are consistent in this respect throughout. That is, sometimes different conventions are used in different contexts within the same book or paper. For example, some choose denominator layout for gradients (laying them out as column vectors), but numerator layout for the vector-by-vector derivative ${\frac {\partial \mathbf {y} }{\partial \mathbf {x} }}.$

Similarly, when it comes to scalar-by-matrix derivatives ${\frac {\partial y}{\partial \mathbf {X} }}$ and matrix-by-scalar derivatives ${\frac {\partial \mathbf {Y} }{\partial x}},$ then consistent numerator layout lays out according to **Y** and **X**<sup>T</sup>, while consistent denominator layout lays out according to **Y**<sup>T</sup> and **X**. In practice, however, following a denominator layout for ${\frac {\partial \mathbf {Y} }{\partial x}},$ and laying the result out according to **Y**<sup>T</sup>, is rarely seen because it makes for ugly formulas that do not correspond to the scalar formulas. As a result, the following layouts can often be found:

1.  *Consistent numerator layout*, which lays out ${\frac {\partial \mathbf {Y} }{\partial x}}$ according to **Y** and ${\frac {\partial y}{\partial \mathbf {X} }}$ according to **X**<sup>T</sup>.
2.  *Mixed layout*, which lays out ${\frac {\partial \mathbf {Y} }{\partial x}}$ according to **Y** and ${\frac {\partial y}{\partial \mathbf {X} }}$ according to **X**.
3.  Use the notation ${\frac {\partial y}{\partial \mathbf {X} '}},$ with results the same as consistent numerator layout.

In the following formulas, we handle the five possible combinations ${\frac {\partial y}{\partial \mathbf {x} }},{\frac {\partial \mathbf {y} }{\partial x}},{\frac {\partial \mathbf {y} }{\partial \mathbf {x} }},{\frac {\partial y}{\partial \mathbf {X} }}$ and ${\frac {\partial \mathbf {Y} }{\partial x}}$ separately. We also handle cases of scalar-by-scalar derivatives that involve an intermediate vector or matrix. (This can arise, for example, if a multi-dimensional [parametric curve](https://en.wikipedia.org/wiki/Parametric_curve) is defined in terms of a scalar variable, and then a derivative of a scalar function of the curve is taken with respect to the scalar that parameterizes the curve.) For each of the various combinations, we give numerator-layout and denominator-layout results, except in the cases above where denominator layout rarely occurs. In cases involving matrices where it makes sense, we give numerator-layout and mixed-layout results. As noted above, cases where vector and matrix denominators are written in transpose notation are equivalent to numerator layout with the denominators written without the transpose.

Keep in mind that various authors use different combinations of numerator and denominator layouts for different types of derivatives, and there is no guarantee that an author will consistently use either numerator or denominator layout for all types. Match up the formulas below with those quoted in the source to determine the layout used for that particular type of derivative, but be careful not to assume that derivatives of other types necessarily follow the same kind of layout.

When taking derivatives with an aggregate (vector or matrix) denominator in order to find a maximum or minimum of the aggregate, it should be kept in mind that using numerator layout will produce results that are transposed with respect to the aggregate. For example, in attempting to find the [maximum likelihood](https://en.wikipedia.org/wiki/Maximum_likelihood) estimate of a [[Multivariate Normal Distribution]] using matrix calculus, if the domain is a *k*×1 column vector, then the result using the numerator layout will be in the form of a 1×*k* row vector. Thus, either the results should be transposed at the end or the denominator layout (or mixed layout) should be used.

<table class="wikitable">
<caption>Result of differentiating various kinds of aggregates with other kinds of aggregates</caption>

Scalar <em>y</em>
Column vector <strong>y</strong> (size <em>m</em>×1)
Matrix <strong>Y</strong> (size <em>m</em>×<em>n</em>)

Notation
Type
Notation
Type
Notation
Type

&#10;
Scalar <em>x</em>
Numerator
${\frac {\partial y}{\partial x}}$
Scalar
${\frac {\partial \mathbf {y} }{\partial x}}$
Size-m [column vector](https://en.wikipedia.org/wiki/Column_vector)
${\frac {\partial \mathbf {Y} }{\partial x}}$
<em>m</em>×<em>n</em> matrix

Denominator
Size-<em>m</em> [row vector](https://en.wikipedia.org/wiki/Row_vector)

Column vector <strong>x</strong><br />
(size <em>n</em>×<em>1</em>)
Numerator
${\frac {\partial y}{\partial \mathbf {x} }}$
Size-n [row vector](https://en.wikipedia.org/wiki/Row_vector)
${\frac {\partial \mathbf {y} }{\partial \mathbf {x} }}$
<em>m</em>×<em>n</em> matrix
${\frac {\partial \mathbf {Y} }{\partial \mathbf {x} }}$

Denominator
Size-n [column vector](https://en.wikipedia.org/wiki/Column_vector)
<em>n</em>×<em>m</em> matrix

Matrix <strong>X</strong><br />
(size <em>p</em>×<em>q</em>)
Numerator
${\frac {\partial y}{\partial \mathbf {X} }}$
<em>q</em>×<em>p</em> matrix
${\frac {\partial \mathbf {y} }{\partial \mathbf {X} }}$

${\frac {\partial \mathbf {Y} }{\partial \mathbf {X} }}$

Denominator
<em>p</em>×<em>q</em> matrix

</table>

The results of operations will be transposed when switching between numerator-layout and denominator-layout notation.

### Numerator-layout notation

Using numerator-layout notation, we have:

${\begin{aligned}{\frac {\partial y}{\partial \mathbf {x} }}&={\begin{bmatrix}{\frac {\partial y}{\partial x_{1}}}&{\frac {\partial y}{\partial x_{2}}}&\cdots &{\frac {\partial y}{\partial x_{n}}}\end{bmatrix}}.\\{\frac {\partial \mathbf {y} }{\partial x}}&={\begin{bmatrix}{\frac {\partial y_{1}}{\partial x}}\\{\frac {\partial y_{2}}{\partial x}}\\\vdots \\{\frac {\partial y_{m}}{\partial x}}\\\end{bmatrix}}.\\{\frac {\partial \mathbf {y} }{\partial \mathbf {x} }}&={\begin{bmatrix}{\frac {\partial y_{1}}{\partial x_{1}}}&{\frac {\partial y_{1}}{\partial x_{2}}}&\cdots &{\frac {\partial y_{1}}{\partial x_{n}}}\\{\frac {\partial y_{2}}{\partial x_{1}}}&{\frac {\partial y_{2}}{\partial x_{2}}}&\cdots &{\frac {\partial y_{2}}{\partial x_{n}}}\\\vdots &\vdots &\ddots &\vdots \\{\frac {\partial y_{m}}{\partial x_{1}}}&{\frac {\partial y_{m}}{\partial x_{2}}}&\cdots &{\frac {\partial y_{m}}{\partial x_{n}}}\\\end{bmatrix}}.\\{\frac {\partial y}{\partial \mathbf {X} }}&={\begin{bmatrix}{\frac {\partial y}{\partial x_{11}}}&{\frac {\partial y}{\partial x_{21}}}&\cdots &{\frac {\partial y}{\partial x_{p1}}}\\{\frac {\partial y}{\partial x_{12}}}&{\frac {\partial y}{\partial x_{22}}}&\cdots &{\frac {\partial y}{\partial x_{p2}}}\\\vdots &\vdots &\ddots &\vdots \\{\frac {\partial y}{\partial x_{1q}}}&{\frac {\partial y}{\partial x_{2q}}}&\cdots &{\frac {\partial y}{\partial x_{pq}}}\\\end{bmatrix}}.\end{aligned}}$

The following definitions are only provided in numerator-layout notation:

${\begin{aligned}{\frac {\partial \mathbf {Y} }{\partial x}}&={\begin{bmatrix}{\frac {\partial y_{11}}{\partial x}}&{\frac {\partial y_{12}}{\partial x}}&\cdots &{\frac {\partial y_{1n}}{\partial x}}\\{\frac {\partial y_{21}}{\partial x}}&{\frac {\partial y_{22}}{\partial x}}&\cdots &{\frac {\partial y_{2n}}{\partial x}}\\\vdots &\vdots &\ddots &\vdots \\{\frac {\partial y_{m1}}{\partial x}}&{\frac {\partial y_{m2}}{\partial x}}&\cdots &{\frac {\partial y_{mn}}{\partial x}}\\\end{bmatrix}}.\\d\mathbf {X} &={\begin{bmatrix}dx_{11}&dx_{12}&\cdots &dx_{1n}\\dx_{21}&dx_{22}&\cdots &dx_{2n}\\\vdots &\vdots &\ddots &\vdots \\dx_{m1}&dx_{m2}&\cdots &dx_{mn}\\\end{bmatrix}}.\end{aligned}}$

### Denominator-layout notation

Using denominator-layout notation, we have:

${\begin{aligned}{\frac {\partial y}{\partial \mathbf {x} }}&={\begin{bmatrix}{\frac {\partial y}{\partial x_{1}}}\\{\frac {\partial y}{\partial x_{2}}}\\\vdots \\{\frac {\partial y}{\partial x_{n}}}\\\end{bmatrix}}.\\{\frac {\partial \mathbf {y} }{\partial x}}&={\begin{bmatrix}{\frac {\partial y_{1}}{\partial x}}&{\frac {\partial y_{2}}{\partial x}}&\cdots &{\frac {\partial y_{m}}{\partial x}}\end{bmatrix}}.\\{\frac {\partial \mathbf {y} }{\partial \mathbf {x} }}&={\begin{bmatrix}{\frac {\partial y_{1}}{\partial x_{1}}}&{\frac {\partial y_{2}}{\partial x_{1}}}&\cdots &{\frac {\partial y_{m}}{\partial x_{1}}}\\{\frac {\partial y_{1}}{\partial x_{2}}}&{\frac {\partial y_{2}}{\partial x_{2}}}&\cdots &{\frac {\partial y_{m}}{\partial x_{2}}}\\\vdots &\vdots &\ddots &\vdots \\{\frac {\partial y_{1}}{\partial x_{n}}}&{\frac {\partial y_{2}}{\partial x_{n}}}&\cdots &{\frac {\partial y_{m}}{\partial x_{n}}}\\\end{bmatrix}}.\\{\frac {\partial y}{\partial \mathbf {X} }}&={\begin{bmatrix}{\frac {\partial y}{\partial x_{11}}}&{\frac {\partial y}{\partial x_{12}}}&\cdots &{\frac {\partial y}{\partial x_{1q}}}\\{\frac {\partial y}{\partial x_{21}}}&{\frac {\partial y}{\partial x_{22}}}&\cdots &{\frac {\partial y}{\partial x_{2q}}}\\\vdots &\vdots &\ddots &\vdots \\{\frac {\partial y}{\partial x_{p1}}}&{\frac {\partial y}{\partial x_{p2}}}&\cdots &{\frac {\partial y}{\partial x_{pq}}}\\\end{bmatrix}}.\end{aligned}}$

## Identities

As noted above, in general, the results of operations will be transposed when switching between numerator-layout and denominator-layout notation.

To help make sense of all the identities below, keep in mind the most important rules: the [[Chain Rule]], [product rule](https://en.wikipedia.org/wiki/Product_rule) and [sum rule](https://en.wikipedia.org/wiki/Sum_rule_in_differentiation). The sum rule applies universally, and the product rule applies in most of the cases below, provided that the order of matrix products is maintained, since matrix products are not commutative. The chain rule applies in some of the cases, but unfortunately does *not* apply in matrix-by-scalar derivatives or scalar-by-matrix derivatives (in the latter case, mostly involving the [trace](https://en.wikipedia.org/wiki/Trace_(linear_algebra) "Trace (linear algebra)") operator applied to matrices). In the latter case, the product rule can't quite be applied directly, either, but the equivalent can be done with a bit more work using the differential identities.

The following identities adopt the following conventions:

- the scalars, *a*, *b*, *c*, *d*, and *e* are constant in respect of, and the scalars, *u*, and *v* are functions of one of x, **x**, or **X**;
- the vectors, **a**, **b**, **c**, **d**, and **e** are constant in respect of, and the vectors, **u**, and **v** are functions of one of x, **x**, or **X**;
- the matrices, **A**, **B**, **C**, **D**, and **E** are constant in respect of, and the matrices, **U** and **V** are functions of one of x, **x**, or **X**.

### Vector-by-vector identities

This is presented first because all of the operations that apply to vector-by-vector differentiation apply directly to vector-by-scalar or scalar-by-vector differentiation simply by reducing the appropriate vector in the numerator or denominator to a scalar.

<table class="wikitable" style="text-align: center;">
<caption>Identities: vector-by-vector ${\frac {\partial \mathbf {y} }{\partial \mathbf {x} }}$</caption>

Condition
Expression
Numerator layout, i.e. by <strong>y</strong> and <strong>x</strong><sup>T</sup>
Denominator layout, i.e. by <strong>y</strong><sup>T</sup> and <strong>x</strong>

&#10;
<strong>a</strong> is not a function of <strong>x</strong>
${\frac {\partial \mathbf {a} }{\partial \mathbf {x} }}=$
$\mathbf {0}$

${\frac {\partial \mathbf {x} }{\partial \mathbf {x} }}=$
$\mathbf {I}$

<strong>A</strong> is not a function of <strong>x</strong>
${\frac {\partial \mathbf {A} \mathbf {x} }{\partial \mathbf {x} }}=$
$\mathbf {A}$
$\mathbf {A} ^{\top }$

<strong>A</strong> is not a function of <strong>x</strong>
${\frac {\partial \mathbf {x} ^{\top }\mathbf {A} }{\partial \mathbf {x} }}=$
$\mathbf {A} ^{\top }$
$\mathbf {A}$

<em>a</em> is not a function of <strong>x</strong>,<br />
<strong>u</strong> = <strong>u</strong>(<strong>x</strong>)
${\frac {\partial a\mathbf {u} }{\partial \,\mathbf {x} }}=$
$a{\frac {\partial \mathbf {u} }{\partial \mathbf {x} }}$

<em>v</em> = <em>v</em>(<strong>x</strong>),<br />
<strong>a</strong> is not a function of <strong>x</strong>
${\frac {\partial v\mathbf {a} }{\partial \mathbf {x} }}=$
$\mathbf {a} {\frac {\partial v}{\partial \mathbf {x} }}$
${\frac {\partial v}{\partial \mathbf {x} }}\mathbf {a} ^{\top }$

<em>v</em> = <em>v</em>(<strong>x</strong>), <strong>u</strong> = <strong>u</strong>(<strong>x</strong>)
${\frac {\partial v\mathbf {u} }{\partial \mathbf {x} }}=$
$v{\frac {\partial \mathbf {u} }{\partial \mathbf {x} }}+\mathbf {u} {\frac {\partial v}{\partial \mathbf {x} }}$
$v{\frac {\partial \mathbf {u} }{\partial \mathbf {x} }}+{\frac {\partial v}{\partial \mathbf {x} }}\mathbf {u} ^{\top }$

<strong>A</strong> is not a function of <strong>x</strong>,<br />
<strong>u</strong> = <strong>u</strong>(<strong>x</strong>)
${\frac {\partial \mathbf {A} \mathbf {u} }{\partial \mathbf {x} }}=$
$\mathbf {A} {\frac {\partial \mathbf {u} }{\partial \mathbf {x} }}$
${\frac {\partial \mathbf {u} }{\partial \mathbf {x} }}\mathbf {A} ^{\top }$

<strong>u</strong> = <strong>u</strong>(<strong>x</strong>), <strong>v</strong> = <strong>v</strong>(<strong>x</strong>)
${\frac {\partial (\mathbf {u} +\mathbf {v} )}{\partial \mathbf {x} }}=$
${\frac {\partial \mathbf {u} }{\partial \mathbf {x} }}+{\frac {\partial \mathbf {v} }{\partial \mathbf {x} }}$

<strong>u</strong> = <strong>u</strong>(<strong>x</strong>)
${\frac {\partial \mathbf {g} (\mathbf {u} )}{\partial \mathbf {x} }}=$
${\frac {\partial \mathbf {g} (\mathbf {u} )}{\partial \mathbf {u} }}{\frac {\partial \mathbf {u} }{\partial \mathbf {x} }}$
${\frac {\partial \mathbf {u} }{\partial \mathbf {x} }}{\frac {\partial \mathbf {g} (\mathbf {u} )}{\partial \mathbf {u} }}$

<strong>u</strong> = <strong>u</strong>(<strong>x</strong>)
${\frac {\partial \mathbf {f} (\mathbf {g} (\mathbf {u} ))}{\partial \mathbf {x} }}=$
${\frac {\partial \mathbf {f} (\mathbf {g} )}{\partial \mathbf {g} }}{\frac {\partial \mathbf {g} (\mathbf {u} )}{\partial \mathbf {u} }}{\frac {\partial \mathbf {u} }{\partial \mathbf {x} }}$
${\frac {\partial \mathbf {u} }{\partial \mathbf {x} }}{\frac {\partial \mathbf {g} (\mathbf {u} )}{\partial \mathbf {u} }}{\frac {\partial \mathbf {f} (\mathbf {g} )}{\partial \mathbf {g} }}$

</table>

### Scalar-by-vector identities

The fundamental identities are placed above the thick black line.

<table class="wikitable" style="text-align: center;">
<caption>Identities: scalar-by-vector ${\frac {\partial y}{\partial \mathbf {x} }}=\nabla _{\mathbf {x} }y$</caption>

Condition
Expression
Numerator layout,<br />
i.e. by <strong>x</strong><sup>T</sup>; result is row vector
Denominator layout,<br />
i.e. by <strong>x</strong>; result is column vector

&#10;
<em>a</em> is not a function of <strong>x</strong>
${\frac {\partial a}{\partial \mathbf {x} }}=$
$\mathbf {0} ^{\top }$
$\mathbf {0}$

<em>a</em> is not a function of <strong>x</strong>,<br />
<em>u</em> = <em>u</em>(<strong>x</strong>)
${\frac {\partial au}{\partial \mathbf {x} }}=$
$a{\frac {\partial u}{\partial \mathbf {x} }}$

<em>u</em> = <em>u</em>(<strong>x</strong>), <em>v</em> = <em>v</em>(<strong>x</strong>)
${\frac {\partial (u+v)}{\partial \mathbf {x} }}=$
${\frac {\partial u}{\partial \mathbf {x} }}+{\frac {\partial v}{\partial \mathbf {x} }}$

<em>u</em> = <em>u</em>(<strong>x</strong>), <em>v</em> = <em>v</em>(<strong>x</strong>)
${\frac {\partial uv}{\partial \mathbf {x} }}=$
$u{\frac {\partial v}{\partial \mathbf {x} }}+v{\frac {\partial u}{\partial \mathbf {x} }}$

<em>u</em> = <em>u</em>(<strong>x</strong>)
${\frac {\partial g(u)}{\partial \mathbf {x} }}=$
${\frac {\partial g(u)}{\partial u}}{\frac {\partial u}{\partial \mathbf {x} }}$

<em>u</em> = <em>u</em>(<strong>x</strong>)
${\frac {\partial f(g(u))}{\partial \mathbf {x} }}=$
${\frac {\partial f(g)}{\partial g}}{\frac {\partial g(u)}{\partial u}}{\frac {\partial u}{\partial \mathbf {x} }}$

<strong>u</strong> = <strong>u</strong>(<strong>x</strong>), <strong>v</strong> = <strong>v</strong>(<strong>x</strong>)
${\frac {\partial (\mathbf {u} \cdot \mathbf {v} )}{\partial \mathbf {x} }}={\frac {\partial \mathbf {u} ^{\top }\mathbf {v} }{\partial \mathbf {x} }}=$
$\mathbf {u} ^{\top }{\frac {\partial \mathbf {v} }{\partial \mathbf {x} }}+\mathbf {v} ^{\top }{\frac {\partial \mathbf {u} }{\partial \mathbf {x} }}$
<p>${\frac {\partial \mathbf {u} }{\partial \mathbf {x} }},{\frac {\partial \mathbf {v} }{\partial \mathbf {x} }}$ in numerator layout</p>
${\frac {\partial \mathbf {u} }{\partial \mathbf {x} }}\mathbf {v} +{\frac {\partial \mathbf {v} }{\partial \mathbf {x} }}\mathbf {u}$
<p>${\frac {\partial \mathbf {u} }{\partial \mathbf {x} }},{\frac {\partial \mathbf {v} }{\partial \mathbf {x} }}$ in denominator layout</p>

<strong>u</strong> = <strong>u</strong>(<strong>x</strong>), <strong>v</strong> = <strong>v</strong>(<strong>x</strong>),<br />
<strong>A</strong> is not a function of <strong>x</strong>
${\frac {\partial (\mathbf {u} \cdot \mathbf {A} \mathbf {v} )}{\partial \mathbf {x} }}={\frac {\partial \mathbf {u} ^{\top }\mathbf {A} \mathbf {v} }{\partial \mathbf {x} }}=$
$\mathbf {u} ^{\top }\mathbf {A} {\frac {\partial \mathbf {v} }{\partial \mathbf {x} }}+\mathbf {v} ^{\top }\mathbf {A} ^{\top }{\frac {\partial \mathbf {u} }{\partial \mathbf {x} }}$
<p>${\frac {\partial \mathbf {u} }{\partial \mathbf {x} }},{\frac {\partial \mathbf {v} }{\partial \mathbf {x} }}$ in numerator layout</p>
${\frac {\partial \mathbf {u} }{\partial \mathbf {x} }}\mathbf {A} \mathbf {v} +{\frac {\partial \mathbf {v} }{\partial \mathbf {x} }}\mathbf {A} ^{\top }\mathbf {u}$
<p>${\frac {\partial \mathbf {u} }{\partial \mathbf {x} }},{\frac {\partial \mathbf {v} }{\partial \mathbf {x} }}$ in denominator layout</p>

${\frac {\partial ^{2}f}{\partial \mathbf {x} \partial \mathbf {x} ^{\top }}}=$
$\mathbf {H} ^{\top }$
$\mathbf {H}$, the [[Hessian Matrix]]

<strong>a</strong> is not a function of <strong>x</strong>
${\frac {\partial (\mathbf {a} \cdot \mathbf {x} )}{\partial \mathbf {x} }}={\frac {\partial (\mathbf {x} \cdot \mathbf {a} )}{\partial \mathbf {x} }}=$<br />
${\frac {\partial \mathbf {a} ^{\top }\mathbf {x} }{\partial \mathbf {x} }}={\frac {\partial \mathbf {x} ^{\top }\mathbf {a} }{\partial \mathbf {x} }}=$
$\mathbf {a} ^{\top }$
$\mathbf {a}$

<strong>A</strong> is not a function of <strong>x</strong><br />
<strong>b</strong> is not a function of <strong>x</strong>
${\frac {\partial \mathbf {b} ^{\top }\mathbf {A} \mathbf {x} }{\partial \mathbf {x} }}=$
$\mathbf {b} ^{\top }\mathbf {A}$
$\mathbf {A} ^{\top }\mathbf {b}$

<strong>A</strong> is not a function of <strong>x</strong>
${\frac {\partial \mathbf {x} ^{\top }\mathbf {A} \mathbf {x} }{\partial \mathbf {x} }}=$
$\mathbf {x} ^{\top }\left(\mathbf {A} +\mathbf {A} ^{\top }\right)$
$\left(\mathbf {A} +\mathbf {A} ^{\top }\right)\mathbf {x}$

<strong>A</strong> is not a function of <strong>x</strong><br />
<strong>A</strong> is [symmetric](https://en.wikipedia.org/wiki/Symmetric_matrix)
${\frac {\partial \mathbf {x} ^{\top }\mathbf {A} \mathbf {x} }{\partial \mathbf {x} }}=$
$2\mathbf {x} ^{\top }\mathbf {A}$
$2\mathbf {A} \mathbf {x}$

<strong>A</strong> is not a function of <strong>x</strong>
${\frac {\partial ^{2}\mathbf {x} ^{\top }\mathbf {A} \mathbf {x} }{\partial \mathbf {x} \partial \mathbf {x} ^{\top }}}=$
$\mathbf {A} +\mathbf {A} ^{\top }$

<strong>A</strong> is not a function of <strong>x</strong><br />
<strong>A</strong> is [symmetric](https://en.wikipedia.org/wiki/Symmetric_matrix)
${\frac {\partial ^{2}\mathbf {x} ^{\top }\mathbf {A} \mathbf {x} }{\partial \mathbf {x} \partial \mathbf {x} ^{\top }}}=$
$2\mathbf {A}$

${\frac {\partial (\mathbf {x} \cdot \mathbf {x} )}{\partial \mathbf {x} }}={\frac {\partial \mathbf {x} ^{\top }\mathbf {x} }{\partial \mathbf {x} }}={\frac {\partial \left\Vert \mathbf {x} \right\Vert ^{2}}{\partial \mathbf {x} }}=$
$2\mathbf {x} ^{\top }$
$2\mathbf {x}$

<strong>a</strong> is not a function of <strong>x</strong>,<br />
<strong>u</strong> = <strong>u</strong>(<strong>x</strong>)
${\frac {\partial (\mathbf {a} \cdot \mathbf {u} )}{\partial \mathbf {x} }}={\frac {\partial \mathbf {a} ^{\top }\mathbf {u} }{\partial \mathbf {x} }}=$
$\mathbf {a} ^{\top }{\frac {\partial \mathbf {u} }{\partial \mathbf {x} }}$
<p>${\frac {\partial \mathbf {u} }{\partial \mathbf {x} }}$ in numerator layout</p>
${\frac {\partial \mathbf {u} }{\partial \mathbf {x} }}\mathbf {a}$
<p>${\frac {\partial \mathbf {u} }{\partial \mathbf {x} }}$ in denominator layout</p>

<strong>a</strong>, <strong>b</strong> are not functions of <strong>x</strong>
${\frac {\partial \;{\textbf {a}}^{\top }{\textbf {x}}{\textbf {x}}^{\top }{\textbf {b}}}{\partial \;{\textbf {x}}}}=$
${\textbf {x}}^{\top }\left({\textbf {a}}{\textbf {b}}^{\top }+{\textbf {b}}{\textbf {a}}^{\top }\right)$
$\left({\textbf {a}}{\textbf {b}}^{\top }+{\textbf {b}}{\textbf {a}}^{\top }\right){\textbf {x}}$

<strong>A</strong>, <strong>b</strong>, <strong>C</strong>, <strong>D</strong>, <strong>e</strong> are not functions of <strong>x</strong>
${\frac {\partial \;({\textbf {A}}{\textbf {x}}+{\textbf {b}})^{\top }{\textbf {C}}({\textbf {D}}{\textbf {x}}+{\textbf {e}})}{\partial \;{\textbf {x}}}}=$
$({\textbf {D}}{\textbf {x}}+{\textbf {e}})^{\top }{\textbf {C}}^{\top }{\textbf {A}}+({\textbf {A}}{\textbf {x}}+{\textbf {b}})^{\top }{\textbf {C}}{\textbf {D}}$
${\textbf {D}}^{\top }{\textbf {C}}^{\top }({\textbf {A}}{\textbf {x}}+{\textbf {b}})+{\textbf {A}}^{\top }{\textbf {C}}({\textbf {D}}{\textbf {x}}+{\textbf {e}})$

<strong>a</strong> is not a function of <strong>x</strong>
${\frac {\partial \;\|\mathbf {x} -\mathbf {a} \|}{\partial \;\mathbf {x} }}=$
${\frac {(\mathbf {x} -\mathbf {a} )^{\top }}{\|\mathbf {x} -\mathbf {a} \|}}$
${\frac {\mathbf {x} -\mathbf {a} }{\|\mathbf {x} -\mathbf {a} \|}}$

</table>

### Vector-by-scalar identities

<table class="wikitable" style="text-align: center;">
<caption>Identities: vector-by-scalar ${\frac {\partial \mathbf {y} }{\partial x}}$</caption>

Condition
Expression
Numerator layout, i.e. by <strong>y</strong>,<br />
result is column vector
Denominator layout, i.e. by <strong>y</strong><sup>T</sup>,<br />
result is row vector

&#10;
<strong>a</strong> is not a function of <em>x</em>
${\frac {\partial \mathbf {a} }{\partial x}}=$
$\mathbf {0}$

<em>a</em> is not a function of <em>x</em>,<br />
<strong>u</strong> = <strong>u</strong>(<em>x</em>)
${\frac {\partial a\mathbf {u} }{\partial x}}=$
$a{\frac {\partial \mathbf {u} }{\partial x}}$

<strong>A</strong> is not a function of <em>x</em>,<br />
<strong>u</strong> = <strong>u</strong>(<em>x</em>)
${\frac {\partial \mathbf {A} \mathbf {u} }{\partial x}}=$
$\mathbf {A} {\frac {\partial \mathbf {u} }{\partial x}}$
${\frac {\partial \mathbf {u} }{\partial x}}\mathbf {A} ^{\top }$

<strong>u</strong> = <strong>u</strong>(<em>x</em>)
${\frac {\partial \mathbf {u} ^{\top }}{\partial x}}=$
$\left({\frac {\partial \mathbf {u} }{\partial x}}\right)^{\top }$

<strong>u</strong> = <strong>u</strong>(<em>x</em>), <strong>v</strong> = <strong>v</strong>(<em>x</em>)
${\frac {\partial (\mathbf {u} +\mathbf {v} )}{\partial x}}=$
${\frac {\partial \mathbf {u} }{\partial x}}+{\frac {\partial \mathbf {v} }{\partial x}}$

<strong>u</strong> = <strong>u</strong>(<em>x</em>), <strong>v</strong> = <strong>v</strong>(<em>x</em>)
${\frac {\partial (\mathbf {u} ^{\top }\times \mathbf {v} )}{\partial x}}=$
$\left({\frac {\partial \mathbf {u} }{\partial x}}\right)^{\top }\times \mathbf {v} +\mathbf {u} ^{\top }\times {\frac {\partial \mathbf {v} }{\partial x}}$
${\frac {\partial \mathbf {u} }{\partial x}}\times \mathbf {v} +\mathbf {u} ^{\top }\times \left({\frac {\partial \mathbf {v} }{\partial x}}\right)^{\top }$

<strong>u</strong> = <strong>u</strong>(<em>x</em>)
${\frac {\partial \mathbf {g} (\mathbf {u} )}{\partial x}}=$
${\frac {\partial \mathbf {g} (\mathbf {u} )}{\partial \mathbf {u} }}{\frac {\partial \mathbf {u} }{\partial x}}$
${\frac {\partial \mathbf {u} }{\partial x}}{\frac {\partial \mathbf {g} (\mathbf {u} )}{\partial \mathbf {u} }}$

Assumes consistent matrix layout; see below.

<strong>u</strong> = <strong>u</strong>(<em>x</em>)
${\frac {\partial \mathbf {f} (\mathbf {g} (\mathbf {u} ))}{\partial x}}=$
${\frac {\partial \mathbf {f} (\mathbf {g} )}{\partial \mathbf {g} }}{\frac {\partial \mathbf {g} (\mathbf {u} )}{\partial \mathbf {u} }}{\frac {\partial \mathbf {u} }{\partial x}}$
${\frac {\partial \mathbf {u} }{\partial x}}{\frac {\partial \mathbf {g} (\mathbf {u} )}{\partial \mathbf {u} }}{\frac {\partial \mathbf {f} (\mathbf {g} )}{\partial \mathbf {g} }}$

Assumes consistent matrix layout; see below.

<strong>U</strong> = <strong>U</strong>(<em>x</em>), <strong>v</strong> = <strong>v</strong>(<em>x</em>)
${\frac {\partial (\mathbf {U} \times \mathbf {v} )}{\partial x}}=$
${\frac {\partial \mathbf {U} }{\partial x}}\times \mathbf {v} +\mathbf {U} \times {\frac {\partial \mathbf {v} }{\partial x}}$
$\mathbf {v} ^{\top }\times \left({\frac {\partial \mathbf {U} }{\partial x}}\right)+{\frac {\partial \mathbf {v} }{\partial x}}\times \mathbf {U} ^{\top }$

</table>

**NOTE**: The formulas involving the vector-by-vector derivatives ${\frac {\partial \mathbf {g} (\mathbf {u} )}{\partial \mathbf {u} }}$ and ${\frac {\partial \mathbf {f} (\mathbf {g} )}{\partial \mathbf {g} }}$ (whose outputs are matrices) assume the matrices are laid out consistent with the vector layout, i.e. numerator-layout matrix when numerator-layout vector and vice versa; otherwise, transpose the vector-by-vector derivatives.

### Scalar-by-matrix identities

Note that exact equivalents of the scalar [product rule](https://en.wikipedia.org/wiki/Product_rule) and [[Chain Rule]] do not exist when applied to matrix-valued functions of matrices. However, the product rule of this sort does apply to the differential form (see below), and this is the way to derive many of the identities below involving the [trace](https://en.wikipedia.org/wiki/Trace_(linear_algebra) "Trace (linear algebra)") function, combined with the fact that the trace function allows transposing and cyclic permutation, i.e.:

${\begin{aligned}\operatorname {tr} (\mathbf {A} )&=\operatorname {tr} \left(\mathbf {A^{\top }} \right)\\\operatorname {tr} (\mathbf {ABCD} )&=\operatorname {tr} (\mathbf {BCDA} )=\operatorname {tr} (\mathbf {CDAB} )=\operatorname {tr} (\mathbf {DABC} )\end{aligned}}$

For example, to compute ${\frac {\partial \operatorname {tr} (\mathbf {AXBX^{\top }C} )}{\partial \mathbf {X} }}:$ 

$$
{\begin{aligned}d\operatorname {tr} (\mathbf {AXBX^{\top }C} )&=d\operatorname {tr} \left(\mathbf {CAXBX^{\top }} \right)=\operatorname {tr} \left(d\left(\mathbf {CAXBX^{\top }} \right)\right)\\[1ex]&=\operatorname {tr} \left(\mathbf {CAX} d(\mathbf {BX^{\top }} \right)+d\left(\mathbf {CAX} )\mathbf {BX^{\top }} \right)\\[1ex]&=\operatorname {tr} \left(\mathbf {CAX} d\left(\mathbf {BX^{\top }} \right)\right)+\operatorname {tr} \left(d(\mathbf {CAX} )\mathbf {BX^{\top }} \right)\\[1ex]&=\operatorname {tr} \left(\mathbf {CAXB} d\left(\mathbf {X^{\top }} \right)\right)+\operatorname {tr} \left(\mathbf {CA} (d\mathbf {X} )\mathbf {BX^{\top }} \right)\\[1ex]&=\operatorname {tr} \left(\mathbf {CAXB} (d\mathbf {X} )^{\top }\right)+\operatorname {tr} (\mathbf {CA} \left(d\mathbf {X} )\mathbf {BX^{\top }} \right)\\[1ex]&=\operatorname {tr} \left(\left(\mathbf {CAXB} (d\mathbf {X} )^{\top }\right)^{\top }\right)+\operatorname {tr} \left(\mathbf {CA} (d\mathbf {X} )\mathbf {BX^{\top }} \right)\\[1ex]&=\operatorname {tr} \left((d\mathbf {X} )\mathbf {B^{\top }X^{\top }A^{\top }C^{\top }} \right)+\operatorname {tr} \left(\mathbf {CA} (d\mathbf {X} )\mathbf {BX^{\top }} \right)\\[1ex]&=\operatorname {tr} \left(\mathbf {B^{\top }X^{\top }A^{\top }C^{\top }} (d\mathbf {X} )\right)+\operatorname {tr} \left(\mathbf {BX^{\top }} \mathbf {CA} (d\mathbf {X} )\right)\\[1ex]&=\operatorname {tr} \left(\left(\mathbf {B^{\top }X^{\top }A^{\top }C^{\top }} +\mathbf {BX^{\top }} \mathbf {CA} \right)d\mathbf {X} \right)\\[1ex]&=\operatorname {tr} \left(\left(\mathbf {CAXB} +\mathbf {A^{\top }C^{\top }XB^{\top }} \right)^{\top }d\mathbf {X} \right)\end{aligned}}
$$

Therefore,

${\frac {\partial \operatorname {tr} \left(\mathbf {AXBX^{\top }C} \right)}{\partial \mathbf {X} }}=\mathbf {B^{\top }X^{\top }A^{\top }C^{\top }} +\mathbf {BX^{\top }CA} .$ (numerator layout)

${\frac {\partial \operatorname {tr} \left(\mathbf {AXBX^{\top }C} \right)}{\partial \mathbf {X} }}=\mathbf {CAXB} +\mathbf {A^{\top }C^{\top }XB^{\top }} .$ (denominator layout)

(For the last step, see the [Conversion from differential to derivative form](#convert_differential_derivative) section.)

<table class="wikitable" style="text-align: center;">
<caption>Identities: scalar-by-matrix ${\frac {\partial y}{\partial \mathbf {X} }}$</caption>

Condition
Expression
Numerator layout, i.e. by <strong>X</strong><sup>T</sup>
Denominator layout, i.e. by <strong>X</strong>

&#10;
<em>a</em> is not a function of <strong>X</strong>
${\frac {\partial a}{\partial \mathbf {X} }}=$
$\mathbf {0} ^{\top }$
$\mathbf {0}$

<em>a</em> is not a function of <strong>X</strong>, <em>u</em> = <em>u</em>(<strong>X</strong>)
${\frac {\partial au}{\partial \mathbf {X} }}=$
$a{\frac {\partial u}{\partial \mathbf {X} }}$

<em>u</em> = <em>u</em>(<strong>X</strong>), <em>v</em> = <em>v</em>(<strong>X</strong>)
${\frac {\partial (u+v)}{\partial \mathbf {X} }}=$
${\frac {\partial u}{\partial \mathbf {X} }}+{\frac {\partial v}{\partial \mathbf {X} }}$

<em>u</em> = <em>u</em>(<strong>X</strong>), <em>v</em> = <em>v</em>(<strong>X</strong>)
${\frac {\partial uv}{\partial \mathbf {X} }}=$
$u{\frac {\partial v}{\partial \mathbf {X} }}+v{\frac {\partial u}{\partial \mathbf {X} }}$

<em>u</em> = <em>u</em>(<strong>X</strong>)
${\frac {\partial g(u)}{\partial \mathbf {X} }}=$
${\frac {\partial g(u)}{\partial u}}{\frac {\partial u}{\partial \mathbf {X} }}$

<em>u</em> = <em>u</em>(<strong>X</strong>)
${\frac {\partial f(g(u))}{\partial \mathbf {X} }}=$
${\frac {\partial f(g)}{\partial g}}{\frac {\partial g(u)}{\partial u}}{\frac {\partial u}{\partial \mathbf {X} }}$

<strong>U</strong> = <strong>U</strong>(<strong>X</strong>)
    ${\frac {\partial g(\mathbf {U} )}{\partial X_{ij}}}=$
$\operatorname {tr} \left({\frac {\partial g(\mathbf {U} )}{\partial \mathbf {U} }}{\frac {\partial \mathbf {U} }{\partial X_{ij}}}\right)$
$\operatorname {tr} \left(\left({\frac {\partial g(\mathbf {U} )}{\partial \mathbf {U} }}\right)^{\top }{\frac {\partial \mathbf {U} }{\partial X_{ij}}}\right)$

Both forms assume <em>numerator</em> layout for ${\frac {\partial \mathbf {U} }{\partial X_{ij}}},$<br />
&#10;<p>i.e. mixed layout if denominator layout for <strong>X</strong> is being used.</p>

<strong>a</strong> and <strong>b</strong> are not functions of <strong>X</strong>
${\frac {\partial \mathbf {a} ^{\top }\mathbf {X} \mathbf {b} }{\partial \mathbf {X} }}=$
$\mathbf {b} \mathbf {a} ^{\top }$
$\mathbf {a} \mathbf {b} ^{\top }$

<strong>a</strong> and <strong>b</strong> are not functions of <strong>X</strong>
${\frac {\partial \mathbf {a} ^{\top }\mathbf {X} ^{\top }\mathbf {b} }{\partial \mathbf {X} }}=$
$\mathbf {a} \mathbf {b} ^{\top }$
$\mathbf {b} \mathbf {a} ^{\top }$

<strong>a</strong> and <strong>b</strong> are not functions of <strong>X</strong>, f(<strong>v</strong>) is a real-valued differentiable function
${\frac {\partial f(\mathbf {Xa+b} )}{\partial \mathbf {X} }}=$
$\mathbf {a} {\frac {\partial f}{\partial \mathbf {v} }}$
${\frac {\partial f}{\partial \mathbf {v} }}\mathbf {a} ^{\top }$

<strong>a</strong>, <strong>b</strong> and <strong>C</strong> are not functions of <strong>X</strong>
${\frac {\partial (\mathbf {X} \mathbf {a} +\mathbf {b} )^{\top }\mathbf {C} (\mathbf {X} \mathbf {a} +\mathbf {b} )}{\partial \mathbf {X} }}=$
$\left(\left(\mathbf {C} +\mathbf {C} ^{\top }\right)(\mathbf {X} \mathbf {a} +\mathbf {b} )\mathbf {a} ^{\top }\right)^{\top }$
$\left(\mathbf {C} +\mathbf {C} ^{\top }\right)(\mathbf {X} \mathbf {a} +\mathbf {b} )\mathbf {a} ^{\top }$

<strong>a</strong>, <strong>b</strong> and <strong>C</strong> are not functions of <strong>X</strong>
${\frac {\partial (\mathbf {X} \mathbf {a} )^{\top }\mathbf {C} (\mathbf {X} \mathbf {b} )}{\partial \mathbf {X} }}=$
$\left(\mathbf {C} \mathbf {X} \mathbf {b} \mathbf {a} ^{\top }+\mathbf {C} ^{\top }\mathbf {X} \mathbf {a} \mathbf {b} ^{\top }\right)^{\top }$
$\mathbf {C} \mathbf {X} \mathbf {b} \mathbf {a} ^{\top }+\mathbf {C} ^{\top }\mathbf {X} \mathbf {a} \mathbf {b} ^{\top }$

${\frac {\partial \operatorname {tr} (\mathbf {X} )}{\partial \mathbf {X} }}=$
$\mathbf {I}$

<strong>U</strong> = <strong>U</strong>(<strong>X</strong>), <strong>V</strong> = <strong>V</strong>(<strong>X</strong>)
${\frac {\partial \operatorname {tr} (\mathbf {U} +\mathbf {V} )}{\partial \mathbf {X} }}=$
${\frac {\partial \operatorname {tr} (\mathbf {U} )}{\partial \mathbf {X} }}+{\frac {\partial \operatorname {tr} (\mathbf {V} )}{\partial \mathbf {X} }}$

<em>a</em> is not a function of <strong>X</strong>,<br />
<strong>U</strong> = <strong>U</strong>(<strong>X</strong>)
${\frac {\partial \operatorname {tr} (a\mathbf {U} )}{\partial \mathbf {X} }}=$
$a{\frac {\partial \operatorname {tr} (\mathbf {U} )}{\partial \mathbf {X} }}$

<strong>g</strong>(<strong>X</strong>) is any [polynomial](https://en.wikipedia.org/wiki/Polynomial) with scalar coefficients, or any matrix function defined by an infinite polynomial series (e.g. <em>e</em><sup><strong>X</strong></sup>, sin(<strong>X</strong>), cos(<strong>X</strong>), ln(<strong>X</strong>), etc. using a [[Taylor Series]]); <em>g</em>(<em>x</em>) is the equivalent scalar function, <em>g</em>′(<em>x</em>) is its derivative, and <strong>g</strong>′(<strong>X</strong>) is the corresponding matrix function
${\frac {\partial \operatorname {tr} (\mathbf {g(X)} )}{\partial \mathbf {X} }}=$
$\mathbf {g} '(\mathbf {X} )$
$\left(\mathbf {g} '(\mathbf {X} )\right)^{\top }$

<strong>A</strong> is not a function of <strong>X</strong>
    ${\frac {\partial \operatorname {tr} (\mathbf {AX} )}{\partial \mathbf {X} }}={\frac {\partial \operatorname {tr} (\mathbf {XA} )}{\partial \mathbf {X} }}=$
$\mathbf {A}$
$\mathbf {A} ^{\top }$

<strong>A</strong> is not a function of <strong>X</strong>
    ${\frac {\partial \operatorname {tr} \left(\mathbf {AX^{\top }} \right)}{\partial \mathbf {X} }}={\frac {\partial \operatorname {tr} \left(\mathbf {X^{\top }A} \right)}{\partial \mathbf {X} }}=$
$\mathbf {A} ^{\top }$
$\mathbf {A}$

<strong>A</strong> is not a function of <strong>X</strong>
    ${\frac {\partial \operatorname {tr} \left(\mathbf {X^{\top }AX} \right)}{\partial \mathbf {X} }}=$
$\mathbf {X} ^{\top }\left(\mathbf {A} +\mathbf {A} ^{\top }\right)$
$\left(\mathbf {A} +\mathbf {A} ^{\top }\right)\mathbf {X}$

<strong>A</strong> is not a function of <strong>X</strong>
    ${\frac {\partial \operatorname {tr} (\mathbf {X^{-1}A} )}{\partial \mathbf {X} }}=$
$-\mathbf {X} ^{-1}\mathbf {A} \mathbf {X} ^{-1}$
$-\left(\mathbf {X} ^{-1}\right)^{\top }\mathbf {A} ^{\top }\left(\mathbf {X} ^{-1}\right)^{\top }$

<strong>A</strong>, <strong>B</strong> are not functions of <strong>X</strong>
${\frac {\partial \operatorname {tr} (\mathbf {AXB} )}{\partial \mathbf {X} }}={\frac {\partial \operatorname {tr} (\mathbf {BAX} )}{\partial \mathbf {X} }}=$
$\mathbf {BA}$
$\mathbf {A^{\top }B^{\top }}$

<strong>A</strong>, <strong>B</strong>, <strong>C</strong> are not functions of <strong>X</strong>
${\frac {\partial \operatorname {tr} \left(\mathbf {AXBX^{\top }C} \right)}{\partial \mathbf {X} }}=$
$\mathbf {BX^{\top }CA} +\mathbf {B^{\top }X^{\top }A^{\top }C^{\top }}$
$\mathbf {A^{\top }C^{\top }XB^{\top }} +\mathbf {CAXB}$

n is a positive integer
    ${\frac {\partial \operatorname {tr} \left(\mathbf {X} ^{n}\right)}{\partial \mathbf {X} }}=$
$n\mathbf {X} ^{n-1}$
$n\left(\mathbf {X} ^{n-1}\right)^{\top }$

<strong>A</strong> is not a function of <strong>X</strong>,<br />
n is a positive integer
    ${\frac {\partial \operatorname {tr} \left(\mathbf {A} \mathbf {X} ^{n}\right)}{\partial \mathbf {X} }}=$
$\sum _{i=0}^{n-1}\mathbf {X} ^{i}\mathbf {A} \mathbf {X} ^{n-i-1}$
$\sum _{i=0}^{n-1}\left(\mathbf {X} ^{i}\mathbf {A} \mathbf {X} ^{n-i-1}\right)^{\top }$

    ${\frac {\partial \operatorname {tr} \left(e^{\mathbf {X} }\right)}{\partial \mathbf {X} }}=$
$e^{\mathbf {X} }$
$\left(e^{\mathbf {X} }\right)^{\top }$

    ${\frac {\partial \operatorname {tr} (\sin(\mathbf {X} ))}{\partial \mathbf {X} }}=$
$\cos(\mathbf {X} )$
$(\cos(\mathbf {X} ))^{\top }$

    ${\frac {\partial |\mathbf {X} |}{\partial \mathbf {X} }}=$
$\operatorname {cofactor} (X)^{\top }=|\mathbf {X} |\mathbf {X} ^{-1}$
$\operatorname {cofactor} (X)=|\mathbf {X} |\left(\mathbf {X} ^{-1}\right)^{\top }$

<em>a</em> is not a function of <strong>X</strong>
${\frac {\partial \ln |a\mathbf {X} |}{\partial \mathbf {X} }}=$
$\mathbf {X} ^{-1}$
$\left(\mathbf {X} ^{-1}\right)^{\top }$

<strong>A</strong>, <strong>B</strong> are not functions of <strong>X</strong>
     ${\frac {\partial |\mathbf {AXB} |}{\partial \mathbf {X} }}=$
$|\mathbf {AXB} |\mathbf {X} ^{-1}$
$|\mathbf {AXB} |\left(\mathbf {X} ^{-1}\right)^{\top }$

n is a positive integer
    ${\frac {\partial \left|\mathbf {X} ^{n}\right|}{\partial \mathbf {X} }}=$
$n\left|\mathbf {X} ^{n}\right|\mathbf {X} ^{-1}$
$n\left|\mathbf {X} ^{n}\right|\left(\mathbf {X} ^{-1}\right)^{\top }$

(see [pseudo-inverse](https://en.wikipedia.org/wiki/Pseudo-inverse))
      ${\frac {\partial \ln \left|\mathbf {X} ^{\top }\mathbf {X} \right|}{\partial \mathbf {X} }}=$
$2\mathbf {X} ^{+}$
$2\left(\mathbf {X} ^{+}\right)^{\top }$

(see [pseudo-inverse](https://en.wikipedia.org/wiki/Pseudo-inverse))
     ${\frac {\partial \ln \left|\mathbf {X} ^{\top }\mathbf {X} \right|}{\partial \mathbf {X} ^{+}}}=$
$-2\mathbf {X}$
$-2\mathbf {X} ^{\top }$

<strong>A</strong> is not a function of <strong>X</strong>,<br />
<strong>X</strong> is square and invertible
${\frac {\partial \left|\mathbf {X^{\top }} \mathbf {A} \mathbf {X} \right|}{\partial \mathbf {X} }}=$
$2\left|\mathbf {X^{\top }} \mathbf {A} \mathbf {X} \right|\mathbf {X} ^{-1}=2\left|\mathbf {X^{\top }} \right||\mathbf {A} ||\mathbf {X} |\mathbf {X} ^{-1}$
$2\left|\mathbf {X^{\top }} \mathbf {A} \mathbf {X} \right|\left(\mathbf {X} ^{-1}\right)^{\top }$

<strong>A</strong> is not a function of <strong>X</strong>,<br />
<strong>X</strong> is non-square,<br />
<strong>A</strong> is symmetric
${\frac {\partial \left|\mathbf {X^{\top }} \mathbf {A} \mathbf {X} \right|}{\partial \mathbf {X} }}=$
$2\left|\mathbf {X^{\top }} \mathbf {A} \mathbf {X} \right|\left(\mathbf {X^{\top }A^{\top }X} \right)^{-1}\mathbf {X^{\top }A^{\top }}$
$2\left|\mathbf {X^{\top }} \mathbf {A} \mathbf {X} \right|\mathbf {AX} \left(\mathbf {X^{\top }AX} \right)^{-1}$

<strong>A</strong> is not a function of <strong>X</strong>,<br />
<strong>X</strong> is non-square,<br />
<strong>A</strong> is non-symmetric
${\frac {\partial |\mathbf {X^{\top }} \mathbf {A} \mathbf {X} |}{\partial \mathbf {X} }}=$
${\begin{aligned}\left|\mathbf {X^{\top }} \mathbf {A} \mathbf {X} \right|{\Big (}&\left(\mathbf {X^{\top }AX} \right)^{-1}\mathbf {X^{\top }A} +{}\\&\left(\mathbf {X^{\top }A^{\top }X} \right)^{-1}\mathbf {X^{\top }A^{\top }} {\Big )}\end{aligned}}$
${\begin{aligned}\left|\mathbf {X^{\top }} \mathbf {A} \mathbf {X} \right|{\Big (}&\mathbf {AX} \left(\mathbf {X^{\top }AX} \right)^{-1}+{}\\&\mathbf {A^{\top }X} \left(\mathbf {X^{\top }A^{\top }X} \right)^{-1}{\Big )}\end{aligned}}$

</table>

### Matrix-by-scalar identities

<table class="wikitable" style="text-align: center;">
<caption>Identities: matrix-by-scalar ${\frac {\partial \mathbf {Y} }{\partial x}}$</caption>

Condition
Expression
Numerator layout, i.e. by <strong>Y</strong>

&#10;
<strong>U</strong> = <strong>U</strong>(<em>x</em>)
${\frac {\partial a\mathbf {U} }{\partial x}}=$
$a{\frac {\partial \mathbf {U} }{\partial x}}$

<strong>A</strong>, <strong>B</strong> are not functions of <em>x</em>,<br />
<strong>U</strong> = <strong>U</strong>(<em>x</em>)
${\frac {\partial \mathbf {AUB} }{\partial x}}=$
$\mathbf {A} {\frac {\partial \mathbf {U} }{\partial x}}\mathbf {B}$

<strong>U</strong> = <strong>U</strong>(<em>x</em>), <strong>V</strong> = <strong>V</strong>(<em>x</em>)
${\frac {\partial (\mathbf {U} +\mathbf {V} )}{\partial x}}=$
${\frac {\partial \mathbf {U} }{\partial x}}+{\frac {\partial \mathbf {V} }{\partial x}}$

<strong>U</strong> = <strong>U</strong>(<em>x</em>), <strong>V</strong> = <strong>V</strong>(<em>x</em>)
${\frac {\partial (\mathbf {U} \mathbf {V} )}{\partial x}}=$
$\mathbf {U} {\frac {\partial \mathbf {V} }{\partial x}}+{\frac {\partial \mathbf {U} }{\partial x}}\mathbf {V}$

<strong>U</strong> = <strong>U</strong>(<em>x</em>), <strong>V</strong> = <strong>V</strong>(<em>x</em>)
${\frac {\partial (\mathbf {U} \otimes \mathbf {V} )}{\partial x}}=$
$\mathbf {U} \otimes {\frac {\partial \mathbf {V} }{\partial x}}+{\frac {\partial \mathbf {U} }{\partial x}}\otimes \mathbf {V}$

<strong>U</strong> = <strong>U</strong>(<em>x</em>), <strong>V</strong> = <strong>V</strong>(<em>x</em>)
${\frac {\partial (\mathbf {U} \circ \mathbf {V} )}{\partial x}}=$
$\mathbf {U} \circ {\frac {\partial \mathbf {V} }{\partial x}}+{\frac {\partial \mathbf {U} }{\partial x}}\circ \mathbf {V}$

<strong>U</strong> = <strong>U</strong>(<em>x</em>)
${\frac {\partial \mathbf {U} ^{-1}}{\partial x}}=$
$-\mathbf {U} ^{-1}{\frac {\partial \mathbf {U} }{\partial x}}\mathbf {U} ^{-1}$

<strong>U</strong> = <strong>U</strong>(<em>x</em>,<em>y</em>)
${\frac {\partial ^{2}\mathbf {U} ^{-1}}{\partial x\partial y}}=$
$\mathbf {U} ^{-1}\left({\frac {\partial \mathbf {U} }{\partial x}}\mathbf {U} ^{-1}{\frac {\partial \mathbf {U} }{\partial y}}-{\frac {\partial ^{2}\mathbf {U} }{\partial x\partial y}}+{\frac {\partial \mathbf {U} }{\partial y}}\mathbf {U} ^{-1}{\frac {\partial \mathbf {U} }{\partial x}}\right)\mathbf {U} ^{-1}$

<strong>A</strong> is not a function of <em>x</em>, <strong>g</strong>(<strong>X</strong>) is any polynomial with scalar coefficients, or any matrix function defined by an infinite polynomial series (e.g. <em>e</em><sup><strong>X</strong></sup>, sin(<strong>X</strong>), cos(<strong>X</strong>), ln(<strong>X</strong>), etc.); <em>g</em>(<em>x</em>) is the equivalent scalar function, <em>g</em>′(<em>x</em>) is its derivative, and <strong>g</strong>′(<strong>X</strong>) is the corresponding matrix function
${\frac {\partial \,\mathbf {g} (x\mathbf {A} )}{\partial x}}=$
$\mathbf {A} \mathbf {g} '(x\mathbf {A} )=\mathbf {g} '(x\mathbf {A} )\mathbf {A}$

<strong>A</strong> is not a function of <em>x</em>
${\frac {\partial e^{x\mathbf {A} }}{\partial x}}=$
$\mathbf {A} e^{x\mathbf {A} }=e^{x\mathbf {A} }\mathbf {A}$

</table>

### Scalar-by-scalar identities

#### With vectors involved

|  |  |  |
|----|----|----|
| Condition | Expression | Any layout (assumes [dot product](https://en.wikipedia.org/wiki/Dot_product) ignores row vs. column layout) |
| **u** = **u**(*x*) | ${\frac {\partial g(\mathbf {u} )}{\partial x}}=$ | ${\frac {\partial g(\mathbf {u} )}{\partial \mathbf {u} }}\cdot {\frac {\partial \mathbf {u} }{\partial x}}$ |
| **u** = **u**(*x*), **v** = **v**(*x*) | ${\frac {\partial (\mathbf {u} \cdot \mathbf {v} )}{\partial x}}=$ | $\mathbf {u} \cdot {\frac {\partial \mathbf {v} }{\partial x}}+{\frac {\partial \mathbf {u} }{\partial x}}\cdot \mathbf {v}$ |

Identities: scalar-by-scalar, with vectors involved {.wikitable style="text-align: center;"}

#### With matrices involved

<table class="wikitable" style="text-align: center;">
<caption>Identities: scalar-by-scalar, with matrices involved</caption>

Condition
Expression
Consistent numerator layout,<br />
i.e. by <strong>Y</strong> and <strong>X</strong><sup>T</sup>
Mixed layout,<br />
i.e. by <strong>Y</strong> and <strong>X</strong>

&#10;
<strong>U</strong> = <strong>U</strong>(<em>x</em>)
${\frac {\partial |\mathbf {U} |}{\partial x}}=$
$|\mathbf {U} |\operatorname {tr} \left(\mathbf {U} ^{-1}{\frac {\partial \mathbf {U} }{\partial x}}\right)$

<strong>U</strong> = <strong>U</strong>(<em>x</em>)
${\frac {\partial \ln |\mathbf {U} |}{\partial x}}=$
$\operatorname {tr} \left(\mathbf {U} ^{-1}{\frac {\partial \mathbf {U} }{\partial x}}\right)$

<strong>U</strong> = <strong>U</strong>(<em>x</em>)
${\frac {\partial ^{2}|\mathbf {U} |}{\partial x^{2}}}=$
$\left|\mathbf {U} \right|\left[\operatorname {tr} \left(\mathbf {U} ^{-1}{\frac {\partial ^{2}\mathbf {U} }{\partial x^{2}}}\right)+\operatorname {tr} ^{2}\left(\mathbf {U} ^{-1}{\frac {\partial \mathbf {U} }{\partial x}}\right)-\operatorname {tr} \left(\left(\mathbf {U} ^{-1}{\frac {\partial \mathbf {U} }{\partial x}}\right)^{2}\right)\right]$

<strong>U</strong> = <strong>U</strong>(<em>x</em>)
${\frac {\partial g(\mathbf {U} )}{\partial x}}=$
$\operatorname {tr} \left({\frac {\partial g(\mathbf {U} )}{\partial \mathbf {U} }}{\frac {\partial \mathbf {U} }{\partial x}}\right)$
$\operatorname {tr} \left(\left({\frac {\partial g(\mathbf {U} )}{\partial \mathbf {U} }}\right)^{\top }{\frac {\partial \mathbf {U} }{\partial x}}\right)$

<strong>A</strong> is not a function of <em>x</em>, <strong>g</strong>(<strong>X</strong>) is any polynomial with scalar coefficients, or any matrix function defined by an infinite polynomial series (e.g. <em>e</em><sup><strong>X</strong></sup>, sin(<strong>X</strong>), cos(<strong>X</strong>), ln(<strong>X</strong>), etc.); <em>g</em>(<em>x</em>) is the equivalent scalar function, <em>g</em>′(<em>x</em>) is its derivative, and <strong>g</strong>′(<strong>X</strong>) is the corresponding matrix function.
${\frac {\partial \operatorname {tr} (\mathbf {g} (x\mathbf {A} ))}{\partial x}}=$
$\operatorname {tr} \left(\mathbf {A} \mathbf {g} '(x\mathbf {A} )\right)$

<strong>A</strong> is not a function of <em>x</em>
${\frac {\partial \operatorname {tr} \left(e^{x\mathbf {A} }\right)}{\partial x}}=$
$\operatorname {tr} \left(\mathbf {A} e^{x\mathbf {A} }\right)$

</table>

### Identities in differential form

It is often easier to work in differential form and then convert back to normal derivatives. This only works well using the numerator layout. In these rules, *a* is a scalar.

|  |  |
|----|----|
| Expression | Result (numerator layout) |
| $d(\operatorname {tr} (\mathbf {X} ))=$ | $\operatorname {tr} (d\mathbf {X} )$ |
| $d(|\mathbf {X} |)=$ | $|\mathbf {X} |\operatorname {tr} \left(\mathbf {X} ^{-1}d\mathbf {X} \right)=\operatorname {tr} (\operatorname {adj} (\mathbf {X} )d\mathbf {X} )$ |
| $d(\ln |\mathbf {X} |)=$ | $\operatorname {tr} \left(\mathbf {X} ^{-1}d\mathbf {X} \right)$ |

Differential identities: scalar involving matrix {.wikitable style="text-align: center;"}

<table class="wikitable" style="text-align: center;">
<caption>Differential identities: matrix</caption>

Condition
Expression
Result (numerator layout)

&#10;
<strong>A</strong> is not a function of <strong>X</strong>
$d(\mathbf {A} )=$
$0$

<em>a</em> is not a function of <strong>X</strong>
$d(a\mathbf {X} )=$
$a\,d\mathbf {X}$

$d(\mathbf {X} +\mathbf {Y} )=$
$d\mathbf {X} +d\mathbf {Y}$

$d(\mathbf {X} \mathbf {Y} )=$
$(d\mathbf {X} )\mathbf {Y} +\mathbf {X} (d\mathbf {Y} )$

([[Kronecker Product]])
$d(\mathbf {X} \otimes \mathbf {Y} )=$
$(d\mathbf {X} )\otimes \mathbf {Y} +\mathbf {X} \otimes (d\mathbf {Y} )$

([Hadamard product](https://en.wikipedia.org/wiki/Hadamard_product_(matrices)))
$d(\mathbf {X} \circ \mathbf {Y} )=$
$(d\mathbf {X} )\circ \mathbf {Y} +\mathbf {X} \circ (d\mathbf {Y} )$

$d\left(\mathbf {X} ^{\top }\right)=$
$(d\mathbf {X} )^{\top }$

$d\left(\mathbf {X} ^{-1}\right)=$
$-\mathbf {X} ^{-1}\left(d\mathbf {X} \right)\mathbf {X} ^{-1}$

([conjugate transpose](https://en.wikipedia.org/wiki/Conjugate_transpose))
$d\left(\mathbf {X} ^{\mathrm {H} }\right)=$
$(d\mathbf {X} )^{\mathrm {H} }$

n is a positive integer
$d\left(\mathbf {X} ^{n}\right)=$
$\sum _{i=0}^{n-1}\mathbf {X} ^{i}(d\mathbf {X} )\mathbf {X} ^{n-i-1}$

$d\left(e^{\mathbf {X} }\right)=$
$\int _{0}^{1}e^{a\mathbf {X} }(d\mathbf {X} )e^{(1-a)\mathbf {X} }\,da$

$d\left(\log {X}\right)=$
$\int _{0}^{\infty }(\mathbf {X} +z\,\mathbf {I} )^{-1}(d\mathbf {X} )(\mathbf {X} +z\,\mathbf {I} )^{-1}\,dz$

$\mathbf {X} =\sum _{i}\lambda _{i}\mathbf {P} _{i}$ is [diagonalizable](https://en.wikipedia.org/wiki/Eigendecomposition_of_a_matrix)<br />
&#10;<p>$\mathbf {P} _{i}\mathbf {P} _{j}=\delta _{ij}\mathbf {P} _{i}$<br />
<em>f</em> is [differentiable](https://en.wikipedia.org/wiki/Differentiable_function) at every eigenvalue $\lambda _{i}$</p>
$d\left(f(\mathbf {X} )\right)=$
$\sum _{ij}\mathbf {P} _{i}(d\mathbf {X} )\mathbf {P} _{j}{\begin{cases}f'(\lambda _{i})&\lambda _{i}=\lambda _{j}\\{\frac {f(\lambda _{i})-f(\lambda _{j})}{\lambda _{i}-\lambda _{j}}}&\lambda _{i}\neq \lambda _{j}\end{cases}}$

</table>

In the last row, $\delta _{ij}$ is the [Kronecker delta](https://en.wikipedia.org/wiki/Kronecker_delta) and $(\mathbf {P} _{k})_{ij}=(\mathbf {Q} )_{ik}(\mathbf {Q} ^{-1})_{kj}$ is the set of orthogonal projection operators that project onto the k-th eigenvector of **X**. **Q** is the matrix of [eigenvectors](https://en.wikipedia.org/wiki/Eigendecomposition_of_a_matrix#Eigendecomposition_of_a_matrix) of $\mathbf {X} =\mathbf {Q} {\boldsymbol {\Lambda }}\mathbf {Q} ^{-1}$, and $({\boldsymbol {\Lambda }})_{ii}=\lambda _{i}$ are the eigenvalues. The matrix function $f(\mathbf {X} )$ is [defined in terms of the scalar function](https://en.wikipedia.org/wiki/Eigendecomposition_of_a_matrix#Functional_calculus) $f(x)$ for diagonalizable matrices by $f(\mathbf {X} )=\sum _{i}f(\lambda _{i})\mathbf {P} _{i}$ where $\mathbf {X} =\sum _{i}\lambda _{i}\mathbf {P} _{i}$ with $\mathbf {P} _{i}\mathbf {P} _{j}=\delta _{ij}\mathbf {P} _{i}$.

To convert to normal derivative form, first convert it to one of the following canonical forms, and then use these identities:

|  |  |
|----|----|
| Canonical differential form | Equivalent derivative form (numerator layout) |
| $dy=a\,dx$ | ${\frac {dy}{dx}}=a$ |
| $dy=\mathbf {a} ^{\top }d\mathbf {x}$ | ${\frac {dy}{d\mathbf {x} }}=\mathbf {a} ^{\top }$ |
| $dy=\operatorname {tr} (\mathbf {A} \,d\mathbf {X} )$ | ${\frac {dy}{d\mathbf {X} }}=\mathbf {A}$ |
| $d\mathbf {y} =\mathbf {a} \,dx$ | ${\frac {d\mathbf {y} }{dx}}=\mathbf {a}$ |
| $d\mathbf {y} =\mathbf {A} \,d\mathbf {x}$ | ${\frac {d\mathbf {y} }{d\mathbf {x} }}=\mathbf {A}$ |
| $d\mathbf {Y} =\mathbf {A} \,dx$ | ${\frac {d\mathbf {Y} }{dx}}=\mathbf {A}$ |

Conversion from differential to derivative form {.wikitable style="text-align: center;"}

## Applications

Matrix differential calculus is used in statistics and econometrics, particularly for the statistical analysis of [multivariate distributions](https://en.wikipedia.org/wiki/Multivariate_distribution), especially the [[Multivariate Normal Distribution]] and other [elliptical distributions](https://en.wikipedia.org/wiki/Elliptical_distribution).

It is used in [regression analysis](https://en.wikipedia.org/wiki/Regression_analysis) to compute, for example, the [ordinary least squares regression formula](https://en.wikipedia.org/wiki/Linear_least_squares_(mathematics)#The_general_problem) for the case of multiple [explanatory variables](https://en.wikipedia.org/wiki/Explanatory_variable). It is also used in random matrices, statistical moments, local sensitivity and statistical diagnostics. 

## See also

- ![[media/1a9c6ad1ccebbc090fc7cd1c94d2142489246997.png]][Mathematics portal](https://en.wikipedia.org/wiki/Portal:Mathematics)

- [Derivative (generalizations)](https://en.wikipedia.org/wiki/Derivative_(generalizations))
- [Product integral](https://en.wikipedia.org/wiki/Product_integral)
- [Ricci calculus](https://en.wikipedia.org/wiki/Ricci_calculus#Differentiation)
- [Tensor derivative](https://en.wikipedia.org/wiki/Tensor_derivative)

## Notes

1.  ^    Here, $\mathbf {0}$ refers to a [column vector](https://en.wikipedia.org/wiki/Column_vector) of all 0's, of size n, where n is the length of **x**.
2.  ^   Here, $\mathbf {0}$ refers to a matrix of all 0's, of the same shape as **X**.
3.  The constant *a* disappears in the result. This is intentional. In general, 

$$
{\frac {d\ln au}{dx}}={\frac {1}{au}}{\frac {d(au)}{dx}}={\frac {1}{au}}a{\frac {du}{dx}}={\frac {1}{u}}{\frac {du}{dx}}={\frac {d\ln u}{dx}}.
$$

 or, also 

$$
{\frac {d\ln au}{dx}}={\frac {d(\ln a+\ln u)}{dx}}={\frac {d\ln a}{dx}}+{\frac {d\ln u}{dx}}={\frac {d\ln u}{dx}}.
$$

## References

1.  ^      Thomas P., Minka (December 28, 2000). ["Old and New Matrix Algebra Useful for Statistics"](http://research.microsoft.com/en-us/um/people/minka/papers/matrix/). MIT Media Lab note (1997; revised 12/00). Retrieved 5 February 2016.
2.  Felippa, Carlos A. ["Appendix D, Linear Algebra: Determinants, Inverses, Rank"](http://www.colorado.edu/engineering/cas/courses.d/IFEM.d/IFEM.AppD.d/IFEM.AppD.pdf) (PDF). *ASEN 5007: Introduction To Finite Element Methods*. Boulder, Colorado: University of Colorado. Retrieved 5 February 2016. Uses the [[Hessian Matrix|Hessian]] ([transpose](https://en.wikipedia.org/wiki/Transpose) to [Jacobian](https://en.wikipedia.org/wiki/Jacobian_matrix_and_determinant)) definition of vector and matrix derivatives.
3.  ^                  Petersen, Kaare Brandt; Pedersen, Michael Syskind. [The Matrix Cookbook](https://web.archive.org/web/20100302210536/http://www.imm.dtu.dk/pubdb/views/edoc_download.php/3274/pdf/imm3274.pdf) (PDF). Archived from [the original](http://matrixcookbook.com) on 2 March 2010. Retrieved 5 February 2016. This book uses a mixed layout, i.e. by **Y** in ${\frac {\partial \mathbf {Y} }{\partial x}},$ by **X** in ${\frac {\partial y}{\partial \mathbf {X} }}.$
4.  Duchi, John C. ["Properties of the Trace and Matrix Derivatives"](https://web.stanford.edu/~jduchi/projects/matrix_prop.pdf) (PDF). Stanford University. Retrieved 5 February 2016.
5.  See [[Determinant|Determinant § Derivative]] for the derivation.
6.  Giles, Mike B. (2008). "Collected matrix derivative results for forward and reverse mode algorithmic differentiation". In Bischof, Christian H.; Bücker, H. Martin; Hovland, Paul; Naumann, Uwe; Utke, Jean (eds.). *Advances in Automatic Differentiation*. Lecture Notes in Computational Science and Engineering. Vol. 64. Berlin: Springer. pp. 35–44. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-3-540-68942-3_4](https://doi.org/10.1007%2F978-3-540-68942-3_4). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-68935-5](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-68935-5). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [2531677](https://mathscinet.ams.org/mathscinet-getitem?mr=2531677).
7.  [Unpublished memo](https://www.ias.edu/sites/default/files/sns/files/1-matrixlog_tex(1).pdf) by S Adler (IAS) 
8.  [Fang, Kai-Tai](https://en.wikipedia.org/wiki/Kai-Tai_Fang); Zhang, Yao-Ting (1990). *Generalized multivariate analysis*. Science Press (Beijing) and Springer-Verlag (Berlin). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [3-540-17651-9](https://en.wikipedia.org/wiki/Special:BookSources/3-540-17651-9). 9783540176510.
9.  Pan, Jianxin; [Fang, Kaitai](https://en.wikipedia.org/wiki/Kaitai_Fang) (2007). *Growth curve models and statistical diagnostics*. Beijing: Science Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-95053-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-95053-2).
10. Kollo, Tõnu; von Rosen, Dietrich (2005). *Advanced multivariate statistics with matrices*. Dordrecht: Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4020-3418-3](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4020-3418-3).
11. Magnus, Jan; Neudecker, Heinz (2019). *Matrix differential calculus with applications in statistics and econometrics*. New York: John Wiley. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-119-54120-2](https://en.wikipedia.org/wiki/Special:BookSources/978-1-119-54120-2).
12. Liu, Shuangzhe; Leiva, Victor; Zhuang, Dan; Ma, Tiefeng; Figueroa-Zúñiga, Jorge I. (2022). ["Matrix differential calculus with applications in the multivariate linear model and its diagnostics"](https://doi.org/10.1016%2Fj.jmva.2021.104849). *Journal of Multivariate Analysis*. **188** 104849. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.jmva.2021.104849](https://doi.org/10.1016%2Fj.jmva.2021.104849).
13. Liu, Shuangzhe; Trenkler, Götz; Kollo, Tõnu; von Rosen, Dietrich; Baksalary, Oskar Maria (2023). "Professor Heinz Neudecker and matrix differential calculus". *Statistical Papers*. **65** (4): 2605–2639. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s00362-023-01499-w](https://doi.org/10.1007%2Fs00362-023-01499-w). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [263661094](https://api.semanticscholar.org/CorpusID:263661094).

## Further reading

- Abadir, Karim M.; Magnus, Jan R. (2005). *Matrix algebra*. Econometric Exercises. Cambridge: Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-511-64796-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-511-64796-3). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [569411497](https://search.worldcat.org/oclc/569411497).
- Lax, Peter D. (2007). "9. Calculus of Vector- and Matrix-Valued Functions". *Linear algebra and its applications* (2nd ed.). Hoboken, N.J.: Wiley-Interscience. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-75156-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-75156-4).
- Magnus, Jan R. (October 2010). "On the concept of matrix derivative". *Journal of Multivariate Analysis*. **101** (9): 2200–2206. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.jmva.2010.05.005](https://doi.org/10.1016%2Fj.jmva.2010.05.005).. Note that this Wikipedia article has been nearly completely revised from the version criticized in this article.

## External links

### Software

- [MatrixCalculus.org](http://www.matrixcalculus.org/), a website for evaluating matrix calculus expressions symbolically
- [NCAlgebra](https://math.ucsd.edu/~ncalg/), an open-source [Mathematica](https://en.wikipedia.org/wiki/Mathematica) package that has some matrix calculus functionality
- [SymPy](https://en.wikipedia.org/wiki/SymPy) supports symbolic matrix derivatives in its [matrix expression module](https://docs.sympy.org/latest/modules/matrices/expressions.html), as well as symbolic tensor derivatives in its [array expression module](https://docs.sympy.org/latest/modules/tensor/array_expressions.html).
- [Tensorgrad](https://github.com/thomasahle/tensorgrad), an open-source python package for matrix calculus. Supports general symbolic tensor derivatives using [Penrose graphical notation](https://en.wikipedia.org/wiki/Penrose_graphical_notation).

### Information

- [Matrix Reference Manual](https://web.archive.org/web/20120630192238/http://www.psi.toronto.edu/matrix/calculus.html), Mike Brookes, [Imperial College London](https://en.wikipedia.org/wiki/Imperial_College_London).
- [Matrix Differentiation (and some other stuff)](http://www.atmos.washington.edu/~dennis/MatrixCalculus.pdf), Randal J. Barnes, Department of Civil Engineering, University of Minnesota.
- [Notes on Matrix Calculus](http://www4.ncsu.edu/~pfackler/MatCalc.pdf), Paul L. Fackler, [North Carolina State University](https://en.wikipedia.org/wiki/North_Carolina_State_University).
- [Matrix Differential Calculus](https://wiki.inf.ed.ac.uk/twiki/pub/CSTR/ListenSemester1_2006_7/slide.pdf) [Archived](https://web.archive.org/web/20120916044332/https://wiki.inf.ed.ac.uk/twiki/pub/CSTR/ListenSemester1_2006_7/slide.pdf) 2012-09-16 at the [Wayback Machine](https://en.wikipedia.org/wiki/Wayback_Machine) (slide presentation), Zhang Le, [University of Edinburgh](https://en.wikipedia.org/wiki/University_of_Edinburgh).
- [Introduction to Vector and Matrix Differentiation](https://web.archive.org/web/20120526142207/http://www.econ.ku.dk/metrics/Econometrics2_05_II/LectureNotes/matrixdiff.pdf) (notes on matrix differentiation, in the context of [Econometrics](https://en.wikipedia.org/wiki/Econometrics)), Heino Bohn Nielsen.
- [A note on differentiating matrices](http://mpra.ub.uni-muenchen.de/1239/1/MPRA_paper_1239.pdf) (notes on matrix differentiation), Pawel Koval, from Munich Personal RePEc Archive.
- [Vector/Matrix Calculus](http://www.personal.rdg.ac.uk/~sis01xh/teaching/CY4C9/ANN3.pdf) More notes on matrix differentiation.
- [Matrix Identities](http://www.cs.nyu.edu/~roweis/notes/matrixid.pdf) (notes on matrix differentiation), Sam Roweis.
- [Tensor Cookbook](https://tensorcookbook.com/) Matrix Calculus using [Tensor Diagrams](https://en.wikipedia.org/wiki/Penrose_graphical_notation).
