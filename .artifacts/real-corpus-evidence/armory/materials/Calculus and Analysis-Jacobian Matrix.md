[[calculus-analysis.base]]

> Source: [Jacobian matrix and determinant](https://en.wikipedia.org/wiki/Jacobian_matrix_and_determinant)
> License: Wikipedia content is available under CC BY-SA 4.0.

In [vector calculus](https://en.wikipedia.org/wiki/Vector_calculus), the **Jacobian matrix** ([/dʒəˈkoʊbiən/](https://en.wikipedia.org/wiki/Help:IPA/English), [/dʒɪ-, jɪ-/](https://en.wikipedia.org/wiki/Help:IPA/English)) of a [vector-valued function](https://en.wikipedia.org/wiki/Vector-valued_function) of several variables is the [matrix](https://en.wikipedia.org/wiki/Matrix_(mathematics) "Matrix (mathematics)") of all its first-order [partial derivatives](https://en.wikipedia.org/wiki/Partial_derivative). If this matrix is [square](https://en.wikipedia.org/wiki/Square_matrix), that is, if the number of variables equals the number of [components](https://en.wikipedia.org/wiki/Euclidean_vector#Decomposition) of function values, then its [[Determinant]] is called the **Jacobian determinant**. Both the matrix and (if applicable) the determinant are often referred to simply as the **Jacobian**. They are named after [Carl Gustav Jacob Jacobi](https://en.wikipedia.org/wiki/Carl_Gustav_Jacob_Jacobi).

The Jacobian matrix is the natural generalization of the [derivative](https://en.wikipedia.org/wiki/Derivative) and the [differential](https://en.wikipedia.org/wiki/Differential_of_a_function) of a usual function to vector valued functions of several variables. This generalization includes generalizations of the [inverse function theorem](https://en.wikipedia.org/wiki/Inverse_function_theorem) and the [[Implicit Function Theorem]], where the non-nullity of the derivative is replaced by the non-nullity of the Jacobian determinant, and the [multiplicative inverse](https://en.wikipedia.org/wiki/Multiplicative_inverse) of the derivative is replaced by the [inverse](https://en.wikipedia.org/wiki/Inverse_of_a_matrix) of the Jacobian matrix.

The Jacobian determinant is fundamentally used for changes of variables in [multiple integrals](https://en.wikipedia.org/wiki/Multiple_integral).

## Definition

Let $\mathbf {f} :\mathbb {R} ^{n}\to \mathbb {R} ^{m}$ be a function such that each of its first-order partial derivatives exists on $\mathbb {R} ^{n}$. This function takes a point $\mathbf {x} =(x_{1},\ldots ,x_{n})\in \mathbb {R} ^{n}$ as input and produces the vector $\mathbf {f} (\mathbf {x} )=(f_{1}(\mathbf {x} ),\ldots ,f_{m}(\mathbf {x} ))\in \mathbb {R} ^{m}$ as output. Then the Jacobian matrix of **f**, denoted **J<sub>f</sub>**, is the $m\times n$ matrix whose (*i*, *j*) entry is ${\frac {\partial f_{i}}{\partial x_{j}}};$ explicitly 

$$
\mathbf {J_{f}} ={\begin{bmatrix}{\dfrac {\partial \mathbf {f} }{\partial x_{1}}}&\cdots &{\dfrac {\partial \mathbf {f} }{\partial x_{n}}}\end{bmatrix}}={\begin{bmatrix}\nabla ^{\mathsf {T}}f_{1}\\\vdots \\\nabla ^{\mathsf {T}}f_{m}\end{bmatrix}}={\begin{bmatrix}{\dfrac {\partial f_{1}}{\partial x_{1}}}&\cdots &{\dfrac {\partial f_{1}}{\partial x_{n}}}\\\vdots &\ddots &\vdots \\{\dfrac {\partial f_{m}}{\partial x_{1}}}&\cdots &{\dfrac {\partial f_{m}}{\partial x_{n}}}\end{bmatrix}}
$$

where $\nabla ^{\mathsf {T}}f_{i}$ is the transpose (row vector) of the [gradient](https://en.wikipedia.org/wiki/Gradient) of the $i$-th component.

The Jacobian matrix, whose entries are functions of **x**, is denoted in various ways; other common notations include *D***f**, $\nabla \mathbf {f}$, and ${\frac {\partial (f_{1},\ldots ,f_{m})}{\partial (x_{1},\ldots ,x_{n})}}$. Some authors define the Jacobian as the [transpose](https://en.wikipedia.org/wiki/Transpose) of the form given above.

The Jacobian matrix [represents](https://en.wikipedia.org/wiki/Matrix_(mathematics)#Linear_transformations "Matrix (mathematics)") the [differential](https://en.wikipedia.org/wiki/Total_derivative) of **f** at every point where **f** is differentiable. In detail, if **h** is a [displacement vector](https://en.wikipedia.org/wiki/Displacement_vector) represented by a [column matrix](https://en.wikipedia.org/wiki/Column_matrix), the [matrix product](https://en.wikipedia.org/wiki/Matrix_product) **J**(**x**) ⋅ **h** is another displacement vector, that is the best linear approximation of the change of **f** in a [neighborhood](https://en.wikipedia.org/wiki/Neighborhood_(mathematics)) of **x**, if **f**(**x**) is [differentiable](https://en.wikipedia.org/wiki/Differentiable_function) at **x**. This means that the function that maps **y** to **f**(**x**) + **J**(**x**) ⋅ (**y** – **x**) is the best [linear approximation](https://en.wikipedia.org/wiki/Linear_approximation) of **f**(**y**) for all points **y** close to **x**. The [linear map](https://en.wikipedia.org/wiki/Linear_map) **h** → **J**(**x**) ⋅ **h** is known as the *derivative* or the [*differential*](https://en.wikipedia.org/wiki/Total_derivative) of **f** at **x**.

When $m=n$, the Jacobian matrix is square, so its [[Determinant]] is a well-defined function of **x**, known as the **Jacobian determinant** of **f**. It carries important information about the local behavior of **f**. In particular, the function **f** has a differentiable [inverse function](https://en.wikipedia.org/wiki/Inverse_function) in a neighborhood of a point **x** if and only if the Jacobian determinant is nonzero at **x** (see [inverse function theorem](https://en.wikipedia.org/wiki/Inverse_function_theorem) for an explanation of this and [Jacobian conjecture](https://en.wikipedia.org/wiki/Jacobian_conjecture) for a related problem of *global* invertibility). The Jacobian determinant also appears when changing the variables in [multiple integrals](https://en.wikipedia.org/wiki/Multiple_integral) (see [substitution rule for multiple variables](https://en.wikipedia.org/wiki/Integration_by_substitution#Substitution_for_multiple_variables)).

When $m=1$, that is when $f:\mathbb {R} ^{n}\to \mathbb {R}$ is a [scalar-valued function](https://en.wikipedia.org/wiki/Scalar_field), the Jacobian matrix reduces to the [row vector](https://en.wikipedia.org/wiki/Row_vector) $\nabla ^{\mathsf {T}}f$; this row vector of all first-order partial derivatives of $f$ is the transpose of the [gradient](https://en.wikipedia.org/wiki/Gradient) of $f$, i.e. $\mathbf {J} _{f}=\nabla ^{\mathsf {T}}f$. Specializing further, when $m=n=1$, that is when $f:\mathbb {R} \to \mathbb {R}$ is a [scalar-valued function](https://en.wikipedia.org/wiki/Scalar_field) of a single variable, the Jacobian matrix has a single entry; this entry is the derivative of the function $f$.

These concepts are named after the [mathematician](https://en.wikipedia.org/wiki/Mathematician) [Carl Gustav Jacob Jacobi](https://en.wikipedia.org/wiki/Carl_Gustav_Jacob_Jacobi) (1804–1851).

## Jacobian matrix

The Jacobian of a vector-valued function in several variables generalizes the [gradient](https://en.wikipedia.org/wiki/Gradient) of a [scalar](https://en.wikipedia.org/wiki/Scalar_(mathematics) "Scalar (mathematics)")-valued function in several variables, which in turn generalizes the derivative of a scalar-valued function of a single variable. In other words, the Jacobian matrix of a scalar-valued [function of several variables](https://en.wikipedia.org/wiki/Multivariate_function) is (the transpose of) its gradient and the gradient of a scalar-valued function of a single variable is its derivative.

At each point where a function is differentiable, its Jacobian matrix can also be thought of as describing the amount of "stretching", "rotating" or "transforming" that the function imposes locally near that point. For example, if (*x*′, *y*′) = **f**(*x*, *y*) is used to smoothly transform an image, the Jacobian matrix **J**<sub>**f**</sub>(*x*, *y*), describes how the image in the neighborhood of (*x*, *y*) is transformed.

If a function is differentiable at a point, its differential is given in coordinates by the Jacobian matrix. However, a function does not need to be differentiable for its Jacobian matrix to be defined, since only its first-order [partial derivatives](https://en.wikipedia.org/wiki/Partial_derivative) are required to exist.

If **f** is [differentiable](https://en.wikipedia.org/wiki/Derivative) at a point **p** in **R**<sup>*n*</sup>, then its [differential](https://en.wikipedia.org/wiki/Total_derivative#The_total_derivative_as_a_linear_map) is represented by **J**<sub>**f**</sub>(**p**). In this case, the [[Linear Transformation]] represented by **J**<sub>**f**</sub>(**p**) is the best [linear approximation](https://en.wikipedia.org/wiki/Linear_approximation) of **f** near the point **p**, in the sense that

$$
\mathbf {f} (\mathbf {x} )-\mathbf {f} (\mathbf {p} )=\mathbf {J} _{\mathbf {f} }(\mathbf {p} )(\mathbf {x} -\mathbf {p} )+o(\|\mathbf {x} -\mathbf {p} \|)\quad ({\text{as }}\mathbf {x} \to \mathbf {p} ),
$$

where *o*(‖**x** − **p**‖) is a [quantity](https://en.wikipedia.org/wiki/Big_O_notation#Little-o_notation) that approaches zero much faster than the [distance](https://en.wikipedia.org/wiki/Euclidean_distance) between **x** and **p** does as **x** approaches **p**. This approximation specializes to the approximation of a scalar function of a single variable by its [Taylor polynomial](https://en.wikipedia.org/wiki/Taylor_polynomial) of degree one, namely

$$
f(x)-f(p)=f'(p)(x-p)+o(x-p)\quad ({\text{as }}x\to p).
$$

In this sense, the Jacobian may be regarded as a kind of "[first-order derivative](https://en.wikipedia.org/wiki/Derivative)" of a vector-valued function of several variables. In particular, this means that the [gradient](https://en.wikipedia.org/wiki/Gradient) of a scalar-valued function of several variables may too be regarded as its "first-order derivative".

Composable differentiable functions **f** : **R**<sup>*n*</sup> → **R**<sup>*m*</sup> and **g** : **R**<sup>*m*</sup> → **R**<sup>*k*</sup> satisfy the [[Chain Rule]], namely $\mathbf {J} _{\mathbf {g} \circ \mathbf {f} }(\mathbf {x} )=\mathbf {J} _{\mathbf {g} }(\mathbf {f} (\mathbf {x} ))\mathbf {J} _{\mathbf {f} }(\mathbf {x} )$ for **x**  in **R**<sup>*n*</sup>.

The Jacobian of the gradient of a scalar function of several variables has a special name: the [[Hessian Matrix]], which in a sense is the "[second derivative](https://en.wikipedia.org/wiki/Second_derivative)" of the function in question.

## Jacobian determinant

![[media/874028084dcf4439b7e21ec675895405bf663b50.png]]
A nonlinear map $f\colon \mathbb {R} ^{2}\to \mathbb {R} ^{2}$ sends a small square (left, in red) to a distorted parallelogram (right, in red). The Jacobian at a point gives the best linear approximation of the distorted parallelogram near that point (right, in translucent white), and the Jacobian determinant gives the ratio of the area of the approximating parallelogram to that of the original square.

If *m* = *n*, then **f** is a function from **R**<sup>*n*</sup> to itself and the Jacobian matrix is a [square matrix](https://en.wikipedia.org/wiki/Square_matrix). We can then form its [[Determinant]], known as the **Jacobian determinant**. The Jacobian determinant is sometimes simply referred to as "the Jacobian".

The Jacobian determinant at a given point gives important information about the behavior of **f** near that point. For instance, the [continuously differentiable function](https://en.wikipedia.org/wiki/Continuously_differentiable_function) **f** is [invertible](https://en.wikipedia.org/wiki/Invertible) near a point **p** ∈ **R**<sup>*n*</sup> if the Jacobian determinant at **p** is non-zero. This is the [inverse function theorem](https://en.wikipedia.org/wiki/Inverse_function_theorem). Furthermore, if the Jacobian determinant at **p** is [positive](https://en.wikipedia.org/wiki/Positive_number), then **f** preserves [orientation](https://en.wikipedia.org/wiki/Orientation_(vector_space) "Orientation (vector space)") near **p**; if it is [negative](https://en.wikipedia.org/wiki/Negative_number), **f** reverses orientation. The [absolute value](https://en.wikipedia.org/wiki/Absolute_value) of the Jacobian determinant at **p** gives us the factor by which the function **f** expands or shrinks [volumes](https://en.wikipedia.org/wiki/Volume) near **p**; this is why it occurs in the general [substitution rule](https://en.wikipedia.org/wiki/Substitution_rule).

The Jacobian determinant is used when making a [change of variables](https://en.wikipedia.org/wiki/Integration_by_substitution#Substitution_for_multiple_variables) when evaluating a [multiple integral](https://en.wikipedia.org/wiki/Multiple_integral) of a function over a region within its domain. To accommodate for the change of coordinates the magnitude of the Jacobian determinant arises as a multiplicative factor within the integral. This is because the *n*-dimensional *dV* element is in general a [parallelepiped](https://en.wikipedia.org/wiki/Parallelepiped) in the new coordinate system, and the *n*-volume of a parallelepiped is the determinant of its edge vectors.

The Jacobian can also be used to determine the stability of [equilibria](https://en.wikipedia.org/wiki/Equilibrium_point) for [systems of differential equations](https://en.wikipedia.org/wiki/Matrix_differential_equation) by approximating behavior near an equilibrium point.

## Inverse

According to the [inverse function theorem](https://en.wikipedia.org/wiki/Inverse_function_theorem), the [matrix inverse](https://en.wikipedia.org/wiki/Invertible_matrix) of the Jacobian matrix of an [invertible function](https://en.wikipedia.org/wiki/Invertible_function) **f** : **R**<sup>*n*</sup> → **R**<sup>*n*</sup> is the Jacobian matrix of the *inverse* function. That is, the Jacobian matrix of the inverse function at a point **p** is

$$
\mathbf {J} _{\mathbf {f} ^{-1}}(\mathbf {p} )={\mathbf {J} _{\mathbf {f} }^{-1}(\mathbf {f} ^{-1}(\mathbf {p} ))},
$$

and the Jacobian determinant is

$$
\det(\mathbf {J} _{\mathbf {f} ^{-1}}(\mathbf {p} ))={\frac {1}{\det(\mathbf {J} _{\mathbf {f} }(\mathbf {f} ^{-1}(\mathbf {p} )))}}.
$$

If the Jacobian is continuous and nonsingular at the point **p** in **R**<sup>*n*</sup>, then **f** is invertible when restricted to some [neighbourhood](https://en.wikipedia.org/wiki/Neighbourhood_(mathematics) "Neighbourhood (mathematics)") of **p**. In other words, if the Jacobian determinant is not zero at a point, then the function is *locally invertible* near this point.

The (unproved) [Jacobian conjecture](https://en.wikipedia.org/wiki/Jacobian_conjecture) is related to global invertibility in the case of a polynomial function, that is a function defined by *n* [polynomials](https://en.wikipedia.org/wiki/Polynomial) in *n* variables. It asserts that, if the Jacobian determinant is a non-zero constant (or, equivalently, that it does not have any complex zero), then the function is invertible and its inverse is a polynomial function.

## Critical points

If **f** : **R**<sup>*n*</sup> → **R**<sup>*m*</sup> is a [differentiable function](https://en.wikipedia.org/wiki/Differentiable_function), a *critical point* of **f** is a point where the [rank](https://en.wikipedia.org/wiki/Rank_(linear_algebra) "Rank (linear algebra)") of the Jacobian matrix is not maximal. This means that the rank at the critical point is lower than the rank at some neighbour point. In other words, let *k* be the maximal dimension of the [open balls](https://en.wikipedia.org/wiki/Open_ball) contained in the image of **f**; then a point is critical if all [minors](https://en.wikipedia.org/wiki/Minor_(linear_algebra) "Minor (linear algebra)") of rank *k* of **f** are zero.

In the case where *m* = *n* = *k*, a point is critical if the Jacobian determinant is zero.

## Examples

### Example 1

Consider a function **f** : **R**<sup>2</sup> → **R**<sup>3</sup>, with (*x*, *y*) ↦ (*f*<sub>1</sub>(*x*, *y*), *f*<sub>2</sub>(*x*, *y*), *f*<sub>3</sub>(*x*, *y*)), given by

$$
\mathbf {f} \left({\begin{bmatrix}x\\y\end{bmatrix}}\right)={\begin{bmatrix}f_{1}(x,y)\\f_{2}(x,y)\\f_{3}(x,y)\end{bmatrix}}={\begin{bmatrix}x^{2}y\\5x+\sin y\\4y\end{bmatrix}}.
$$

The Jacobian matrix of **f** is

$$
\mathbf {J} _{\mathbf {f} }(x,y)={\begin{bmatrix}{\dfrac {\partial f_{1}}{\partial x}}&{\dfrac {\partial f_{1}}{\partial y}}\\[1em]{\dfrac {\partial f_{2}}{\partial x}}&{\dfrac {\partial f_{2}}{\partial y}}\\[1em]{\dfrac {\partial f_{3}}{\partial x}}&{\dfrac {\partial f_{3}}{\partial y}}\end{bmatrix}}={\begin{bmatrix}2xy&x^{2}\\5&\cos y\\0&4\end{bmatrix}}
$$

### Example 2: polar-Cartesian transformation

The transformation from [polar coordinates](https://en.wikipedia.org/wiki/Polar_coordinate_system) (*r*, *φ*) to [Cartesian coordinates](https://en.wikipedia.org/wiki/Cartesian_coordinate_system) (*x*, *y*), is given by the function **F**: **R**<sup>+</sup> × \[0, 2π) → **R**<sup>2</sup> with components

$$
{\begin{aligned}x&=r\cos \varphi ;\\y&=r\sin \varphi .\end{aligned}}
$$

$$
\mathbf {J} _{\mathbf {F} }(r,\varphi )={\begin{bmatrix}{\frac {\partial x}{\partial r}}&{\frac {\partial x}{\partial \varphi }}\\[0.5ex]{\frac {\partial y}{\partial r}}&{\frac {\partial y}{\partial \varphi }}\end{bmatrix}}={\begin{bmatrix}\cos \varphi &-r\sin \varphi \\\sin \varphi &r\cos \varphi \end{bmatrix}}
$$

The Jacobian determinant is equal to *r*. This can be used to transform integrals between the two coordinate systems:

$$
\iint _{\mathbf {F} (A)}f(x,y)\,dx\,dy=\iint _{A}f(r\cos \varphi ,r\sin \varphi )\,r\,dr\,d\varphi .
$$

### Example 3: spherical-Cartesian transformation

The transformation from [spherical coordinates](https://en.wikipedia.org/wiki/Spherical_coordinate_system) (*ρ*, *φ*, *θ*) to [Cartesian coordinates](https://en.wikipedia.org/wiki/Cartesian_coordinate_system) (*x*, *y*, *z*), is given by the function **F**: **R**<sup>+</sup> × \[0, *π*) × \[0, 2*π*) → **R**<sup>3</sup> with components

$$
{\begin{aligned}x&=\rho \sin \varphi \cos \theta ;\\y&=\rho \sin \varphi \sin \theta ;\\z&=\rho \cos \varphi .\end{aligned}}
$$

The Jacobian matrix for this coordinate change is

$$
\mathbf {J} _{\mathbf {F} }(\rho ,\varphi ,\theta )={\begin{bmatrix}{\dfrac {\partial x}{\partial \rho }}&{\dfrac {\partial x}{\partial \varphi }}&{\dfrac {\partial x}{\partial \theta }}\\[1em]{\dfrac {\partial y}{\partial \rho }}&{\dfrac {\partial y}{\partial \varphi }}&{\dfrac {\partial y}{\partial \theta }}\\[1em]{\dfrac {\partial z}{\partial \rho }}&{\dfrac {\partial z}{\partial \varphi }}&{\dfrac {\partial z}{\partial \theta }}\end{bmatrix}}={\begin{bmatrix}\sin \varphi \cos \theta &\rho \cos \varphi \cos \theta &-\rho \sin \varphi \sin \theta \\\sin \varphi \sin \theta &\rho \cos \varphi \sin \theta &\rho \sin \varphi \cos \theta \\\cos \varphi &-\rho \sin \varphi &0\end{bmatrix}}.
$$

The [[Determinant]] is *ρ*<sup>2</sup> sin *φ*. Since *dV* = *dx* *dy* *dz* is the volume for a rectangular differential volume element (because the volume of a rectangular prism is the product of its sides), we can interpret *dV* = *ρ*<sup>2</sup> sin *φ* *dρ* *dφ* *dθ* as the volume of the spherical [differential volume element](https://en.wikipedia.org/wiki/Differential_volume_element). Unlike rectangular differential volume element's volume, this differential volume element's volume is not a constant, and varies with coordinates (*ρ* and *φ*). It can be used to transform integrals between the two coordinate systems:

$$
\iiint _{\mathbf {F} (U)}f(x,y,z)\,dx\,dy\,dz=\iiint _{U}f(\rho \sin \varphi \cos \theta ,\rho \sin \varphi \sin \theta ,\rho \cos \varphi )\,\rho ^{2}\sin \varphi \,d\rho \,d\varphi \,d\theta .
$$

### Example 4

The Jacobian matrix of the function **F** : **R**<sup>3</sup> → **R**<sup>4</sup> with components

$$
{\begin{aligned}y_{1}&=x_{1}\\y_{2}&=5x_{3}\\y_{3}&=4x_{2}^{2}-2x_{3}\\y_{4}&=x_{3}\sin x_{1}\end{aligned}}
$$

is

$$
\mathbf {J} _{\mathbf {F} }(x_{1},x_{2},x_{3})={\begin{bmatrix}{\dfrac {\partial y_{1}}{\partial x_{1}}}&{\dfrac {\partial y_{1}}{\partial x_{2}}}&{\dfrac {\partial y_{1}}{\partial x_{3}}}\\[1em]{\dfrac {\partial y_{2}}{\partial x_{1}}}&{\dfrac {\partial y_{2}}{\partial x_{2}}}&{\dfrac {\partial y_{2}}{\partial x_{3}}}\\[1em]{\dfrac {\partial y_{3}}{\partial x_{1}}}&{\dfrac {\partial y_{3}}{\partial x_{2}}}&{\dfrac {\partial y_{3}}{\partial x_{3}}}\\[1em]{\dfrac {\partial y_{4}}{\partial x_{1}}}&{\dfrac {\partial y_{4}}{\partial x_{2}}}&{\dfrac {\partial y_{4}}{\partial x_{3}}}\end{bmatrix}}={\begin{bmatrix}1&0&0\\0&0&5\\0&8x_{2}&-2\\x_{3}\cos x_{1}&0&\sin x_{1}\end{bmatrix}}.
$$

This example shows that the Jacobian matrix need not be a square matrix.

### Example 5

The Jacobian determinant of the function **F** : **R**<sup>3</sup> → **R**<sup>3</sup> with components

$$
{\begin{aligned}y_{1}&=5x_{2}\\y_{2}&=4x_{1}^{2}-2\sin(x_{2}x_{3})\\y_{3}&=x_{2}x_{3}\end{aligned}}
$$

is

$$
{\begin{vmatrix}0&5&0\\8x_{1}&-2x_{3}\cos(x_{2}x_{3})&-2x_{2}\cos(x_{2}x_{3})\\0&x_{3}&x_{2}\end{vmatrix}}=-8x_{1}{\begin{vmatrix}5&0\\x_{3}&x_{2}\end{vmatrix}}=-40x_{1}x_{2}.
$$

From this we see that **F** reverses orientation near those points where *x*<sub>1</sub> and *x*<sub>2</sub> have the same sign; the function is [locally](https://en.wikipedia.org/wiki/Locally) invertible everywhere except near points where *x*<sub>1</sub> = 0 or *x*<sub>2</sub> = 0. Intuitively, if one starts with a tiny object around the point (1, 2, 3) and apply **F** to that object, one will get a resulting object with approximately 40 × 1 × 2 = 80 times the volume of the original one, with orientation reversed.

## Other uses

### Dynamical systems

Consider a [dynamical system](https://en.wikipedia.org/wiki/Dynamical_system) of the form ${\dot {\mathbf {x} }}=F(\mathbf {x} )$, where ${\dot {\mathbf {x} }}$ is the (component-wise) derivative of $\mathbf {x}$ with respect to the [evolution parameter](https://en.wikipedia.org/wiki/Evolution_parameter) $t$ (time), and $F\colon \mathbb {R} ^{n}\to \mathbb {R} ^{n}$ is differentiable. If $F(\mathbf {x} _{0})=0$, then $\mathbf {x} _{0}$ is a [stationary point](https://en.wikipedia.org/wiki/Stationary_point) (also called a [steady state](https://en.wikipedia.org/wiki/Steady_state)). By the [Hartman–Grobman theorem](https://en.wikipedia.org/wiki/Hartman%E2%80%93Grobman_theorem), the behavior of the system near a stationary point is related to the [eigenvalues](https://en.wikipedia.org/wiki/Eigenvalue) of $\mathbf {J} _{F}\left(\mathbf {x} _{0}\right)$, the Jacobian of $F$ at the stationary point. Specifically, if the eigenvalues all have real parts that are negative, then the system is stable near the stationary point. If any eigenvalue has a real part that is positive, then the point is unstable. If the largest real part of the eigenvalues is zero, the Jacobian matrix does not allow for an evaluation of the stability.

### Newton's method

A square system of coupled nonlinear equations can be solved iteratively by [Newton's method](https://en.wikipedia.org/wiki/Newton%27s_method#Systems_of_equations). This method uses the Jacobian matrix of the system of equations.

### Regression and least squares fitting

The Jacobian serves as a linearized [design matrix](https://en.wikipedia.org/wiki/Design_matrix) in statistical [regression](https://en.wikipedia.org/wiki/Regression_analysis) and [curve fitting](https://en.wikipedia.org/wiki/Curve_fitting); see [non-linear least squares](https://en.wikipedia.org/wiki/Non-linear_least_squares). The Jacobian is also used in random matrices, moments, local sensitivity and statistical diagnostics.

## See also

- [Center manifold](https://en.wikipedia.org/wiki/Center_manifold)
- [[Hessian Matrix]]
- [Pushforward (differential)](https://en.wikipedia.org/wiki/Pushforward_(differential) "Pushforward (differential)")

## Notes

1.  Differentiability at **x** implies, but is not implied by, the existence of all first-order partial derivatives at **x**, and hence is a stronger condition.

## References

1.  ["Jacobian - Definition of Jacobian in English by Oxford Dictionaries"](https://web.archive.org/web/20171201043633/https://en.oxforddictionaries.com/definition/jacobian). *Oxford Dictionaries - English*. Archived from [the original](https://en.oxforddictionaries.com/definition/jacobian) on 1 December 2017. Retrieved 2 May 2018.
2.  ["the definition of jacobian"](http://www.dictionary.com/browse/jacobian). *Dictionary.com*. [Archived](https://web.archive.org/web/20171201040801/http://www.dictionary.com/browse/jacobian) from the original on 1 December 2017. Retrieved 2 May 2018.
3.  Team, Forvo. ["Jacobian pronunciation: How to pronounce Jacobian in English"](https://forvo.com/word/jacobian/). *forvo.com*. Retrieved 2 May 2018.
4.  W., Weisstein, Eric. ["Jacobian"](http://mathworld.wolfram.com/Jacobian.html). *mathworld.wolfram.com*. [Archived](https://web.archive.org/web/20171103144419/http://mathworld.wolfram.com/Jacobian.html) from the original on 3 November 2017. Retrieved 2 May 2018.`{{`[`cite web`](https://en.wikipedia.org/wiki/Template:Cite_web)`}}`: CS1 maint: multiple names: authors list ([link](https://en.wikipedia.org/wiki/Category:CS1_maint:_multiple_names:_authors_list))
5.  Holder, Allen; Eichholz, Joseph (2019). *An Introduction to computational science*. International Series in Operations Research & Management Science. Cham, Switzerland: Springer. p. 53. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-030-15679-4](https://en.wikipedia.org/wiki/Special:BookSources/978-3-030-15679-4).
6.  Lovett, Stephen (2019-12-16). [Differential Geometry of Manifolds](https://books.google.com/books?id=G1bGDwAAQBAJ). CRC Press. p. 16. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-429-60782-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-429-60782-0).
7.  Joel Hass, Christopher Heil, and Maurice Weir. *Thomas' Calculus Early Transcendentals, 14e*. Pearson, 2018, p. 959.
8.  Arrowsmith, D. K.; Place, C. M. (1992). ["The Linearization Theorem"](https://books.google.com/books?id=8qCcP7KNaZ0C&pg=PA77). *Dynamical Systems: Differential Equations, Maps, and Chaotic Behaviour*. London: Chapman & Hall. pp. 77–81. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-412-39080-9](https://en.wikipedia.org/wiki/Special:BookSources/0-412-39080-9). 
9.  Hirsch, Morris; Smale, Stephen (1974). *Differential Equations, Dynamical Systems and Linear Algebra*. Academic Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-12-349550-4](https://en.wikipedia.org/wiki/Special:BookSources/0-12-349550-4).
10. Liu, Shuangzhe; Leiva, Victor; Zhuang, Dan; Ma, Tiefeng; Figueroa-Zúñiga, Jorge I. (March 2022). ["Matrix differential calculus with applications in the multivariate linear model and its diagnostics"](https://doi.org/10.1016%2Fj.jmva.2021.104849). *Journal of Multivariate Analysis*. **188** 104849. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.jmva.2021.104849](https://doi.org/10.1016%2Fj.jmva.2021.104849).
11. Liu, Shuangzhe; Trenkler, Götz; Kollo, Tõnu; von Rosen, Dietrich; Baksalary, Oskar Maria (2023). "Professor Heinz Neudecker and matrix differential calculus". *Statistical Papers*. **65** (4): 2605–2639. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s00362-023-01499-w](https://doi.org/10.1007%2Fs00362-023-01499-w). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [263661094](https://api.semanticscholar.org/CorpusID:263661094).

## Further reading

- [Gandolfo, Giancarlo](https://en.wikipedia.org/wiki/Giancarlo_Gandolfo) (1996). ["Comparative Statics and the Correspondence Principle"](https://books.google.com/books?id=ZMwXi67nhHQC&pg=PA305). *Economic Dynamics* (Third ed.). Berlin: Springer. pp. 305–330. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [3-540-60988-1](https://en.wikipedia.org/wiki/Special:BookSources/3-540-60988-1).
- [Protter, Murray H.](https://en.wikipedia.org/wiki/Murray_H._Protter); [Morrey, Charles B. Jr.](https://en.wikipedia.org/wiki/Charles_B._Morrey_Jr.) (1985). "Transformations and Jacobians". *Intermediate Calculus* (Second ed.). New York: Springer. pp. 412–420. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-96058-9](https://en.wikipedia.org/wiki/Special:BookSources/0-387-96058-9).

## External links

- ["Jacobian"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society), 2001 \[1994\]
- [Mathworld](http://mathworld.wolfram.com/Jacobian.html) A more technical explanation of Jacobians
