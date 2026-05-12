[[calculus-analysis.base]]

> Source: [Partial derivative](https://en.wikipedia.org/wiki/Partial_derivative)
> License: Wikipedia content is available under CC BY-SA 4.0.

In [mathematics](https://en.wikipedia.org/wiki/Mathematics), a **partial derivative** of a [function of several variables](https://en.wikipedia.org/wiki/Function_(mathematics)#MULTIVARIATE_FUNCTION "Function (mathematics)") is its [derivative](https://en.wikipedia.org/wiki/Derivative) with respect to one of those variables, with the others held constant (as opposed to the [total derivative](https://en.wikipedia.org/wiki/Total_derivative), in which all variables are allowed to vary). Partial derivatives are used in [vector calculus](https://en.wikipedia.org/wiki/Vector_calculus) and [differential geometry](https://en.wikipedia.org/wiki/Differential_geometry).

The partial derivative of a function $f(x,y,\dots )$ with respect to the variable $x$ is variously denoted by

$f_{x}$, $f'_{x}$, $\partial _{x}f$, $\ D_{x}f$, $D_{\mathbf {e} _{1}}f$ $D_{1}f$, ${\frac {\partial }{\partial x}}f$, or ${\frac {\partial f}{\partial x}}$.

It can be thought of as the rate of change of the function in the $x$-direction.

Sometimes, for $z=f(x,y,\ldots )$, the partial derivative of $z$ with respect to $x$ is denoted as ${\tfrac {\partial z}{\partial x}}.$ Since a partial derivative generally has the same arguments as the original function, its functional dependence is sometimes explicitly signified by the notation, such as in:

$$
f'_{x}(x,y,\ldots ),{\frac {\partial f}{\partial x}}(x,y,\ldots ).
$$

The symbol used to denote partial derivatives is [∂](https://en.wikipedia.org/wiki/%E2%88%82). One of the first known uses of this symbol in mathematics is by [Marquis de Condorcet](https://en.wikipedia.org/wiki/Marquis_de_Condorcet) from 1770, who used it for [partial differences](https://en.wikipedia.org/wiki/Partial_difference_equation). The modern partial derivative notation was created by [Adrien-Marie Legendre](https://en.wikipedia.org/wiki/Adrien-Marie_Legendre) (1786), although he later abandoned it; [Carl Gustav Jacob Jacobi](https://en.wikipedia.org/wiki/Carl_Gustav_Jacob_Jacobi) reintroduced the symbol in 1841.

## Definition

Like ordinary derivatives, the partial derivative is defined as a [limit](https://en.wikipedia.org/wiki/Limit_of_a_function). Let U be an [open subset](https://en.wikipedia.org/wiki/Open_set) of $\mathbb {R} ^{n}$ and $f:U\to \mathbb {R}$ a function. The partial derivative of f at the point $\mathbf {a} =(a_{1},\ldots ,a_{n})\in U$ with respect to the i-th variable *x*<sub>*i*</sub> is defined as

$$
{\begin{aligned}{\frac {\partial }{\partial x_{i}}}f(\mathbf {a} )&=\lim _{h\to 0}{\frac {f(a_{1},\ldots ,a_{i-1},a_{i}+h,a_{i+1}\,\ldots ,a_{n})\ -f(a_{1},\ldots ,a_{i},\dots ,a_{n})}{h}}\\&=\lim _{h\to 0}{\frac {f(\mathbf {a} +h\mathbf {e} _{i})-f(\mathbf {a} )}{h}}\end{aligned}}
$$

where $\mathbf {e_{i}}$ is the [unit vector](https://en.wikipedia.org/wiki/Unit_vector) of i-th variable *x*<sub>*i*</sub>. In fact, the last equality shows that the partial derivative is just the [directional derivative](https://en.wikipedia.org/wiki/Directional_derivative) where the direction is the $i$-th [standard basis](https://en.wikipedia.org/wiki/Standard_basis) vector.

Even if all partial derivatives $\partial f/\partial x_{i}(a)$ exist at a given point a, the function need not be [continuous](https://en.wikipedia.org/wiki/Continuous_function) there. However, if all partial derivatives exist in a [neighborhood](https://en.wikipedia.org/wiki/Neighborhood_(topology)) of a and are continuous there, then f is [totally differentiable](https://en.wikipedia.org/wiki/Total_derivative) in that neighborhood and the total derivative is continuous. In this case, it is said that f is a *C*<sup>1</sup> function. This can be used to generalize for vector valued functions, $f:U\to \mathbb {R} ^{m}$, by carefully using a component-wise argument.

The partial derivative ${\frac {\partial f}{\partial x}}$ is itself a function defined on U and can be partially-differentiated again. If the direction of derivative is *not* repeated, it is called a ***mixed partial derivative***. If all mixed second order partial derivatives are continuous at a point (or on a set), f is termed a *C*<sup>2</sup> function at that point (or on that set); in this case, the partial derivatives can be exchanged by [Clairaut's theorem](https://en.wikipedia.org/wiki/Symmetry_of_second_derivatives#Schwarz's_theorem):

$$
{\frac {\partial ^{2}f}{\partial x_{i}\partial x_{j}}}={\frac {\partial ^{2}f}{\partial x_{j}\partial x_{i}}}.
$$

## Notation

For the following examples, let f be a function in x, y, and z.

First-order partial derivatives:

$$
{\frac {\partial f}{\partial x}}=f'_{x}=\partial _{x}f.
$$

Second-order partial derivatives:

$$
{\frac {\partial ^{2}f}{\partial x^{2}}}=f''_{xx}=\partial _{xx}f=\partial _{x}^{2}f.
$$

Second-order [mixed derivatives](https://en.wikipedia.org/wiki/Mixed_derivatives):

$$
{\frac {\partial ^{2}f}{\partial y\,\partial x}}={\frac {\partial }{\partial y}}\left({\frac {\partial f}{\partial x}}\right)=(f'_{x})'_{y}=f''_{xy}=\partial _{yx}f=\partial _{y}\partial _{x}f.
$$

Higher-order partial and mixed derivatives:

$$
{\frac {\partial ^{i+j+k}f}{\partial x^{i}\partial y^{j}\partial z^{k}}}=f^{(i,j,k)}=\partial _{x}^{i}\partial _{y}^{j}\partial _{z}^{k}f.
$$

When dealing with functions of multiple variables, some of these variables may be related to each other, thus it may be necessary to specify explicitly which variables are being held constant to avoid ambiguity. In fields such as [statistical mechanics](https://en.wikipedia.org/wiki/Statistical_mechanics), the partial derivative of f with respect to x, holding y and z constant, is often expressed as

$$
\left({\frac {\partial f}{\partial x}}\right)_{y,z}.
$$

Conventionally, for clarity and simplicity of notation, the partial derivative *function* and the *value* of the function at a specific point are [conflated](https://en.wikipedia.org/wiki/Abuse_of_notation) by including the function arguments when the partial derivative symbol (Leibniz notation) is used. Thus, an expression like

$$
{\frac {\partial f(x,y,z)}{\partial x}}
$$

is used for the function, while

$$
{\frac {\partial f(u,v,w)}{\partial u}}
$$

might be used for the value of the function at the point $(x,y,z)=(u,v,w)$. However, this convention breaks down when we want to evaluate the partial derivative at a point like $(x,y,z)=(17,u+v,v^{2})$. In such a case, evaluation of the function must be expressed in an unwieldy manner as

$$
{\frac {\partial f(x,y,z)}{\partial x}}(17,u+v,v^{2})
$$

or

$$
\left.{\frac {\partial f(x,y,z)}{\partial x}}\right|_{(x,y,z)=(17,u+v,v^{2})}
$$

in order to use the Leibniz notation. Thus, in these cases, it may be preferable to use the Euler differential operator notation with $D_{i}$ as the partial derivative symbol with respect to the i-th variable. For instance, one would write $D_{1}f(17,u+v,v^{2})$ for the example described above, while the expression $D_{1}f$ represents the partial derivative *function* with respect to the first variable.

For higher order partial derivatives, the partial derivative (function) of $D_{i}f$ with respect to the j-th variable is denoted $D_{j}(D_{i}f)=D_{i,j}f$. That is, $D_{j}\circ D_{i}=D_{i,j}$, so that the variables are listed in the order in which the derivatives are taken, and thus, in reverse order of how the composition of operators is usually notated. Of course, [Clairaut's theorem](https://en.wikipedia.org/wiki/Clairaut%27s_theorem_on_equality_of_mixed_partials) implies that $D_{i,j}=D_{j,i}$ as long as comparatively mild regularity conditions on f are satisfied.

## Gradient

An important example of a function of several variables is the case of a [scalar-valued function](https://en.wikipedia.org/wiki/Scalar-valued_function) $f(x_{1},\ldots ,x_{n})$ on a domain in Euclidean space $\mathbb {R} ^{n}$ (e.g., on $\mathbb {R} ^{2}$ or $\mathbb {R} ^{3}$). In this case f has a partial derivative $\partial f/\partial x_{j}$ with respect to each variable *x*<sub>*j*</sub>. At the point a, these partial derivatives define the vector

$$
\nabla f(a)=\left({\frac {\partial f}{\partial x_{1}}}(a),\ldots ,{\frac {\partial f}{\partial x_{n}}}(a)\right).
$$

This vector is called the *[gradient](https://en.wikipedia.org/wiki/Gradient)* of f at a. If f is differentiable at every point in some domain, then the gradient is a vector-valued function ∇*f* which takes the point a to the vector ∇*f*(*a*). Consequently, the gradient produces a [vector field](https://en.wikipedia.org/wiki/Vector_field).

A common [abuse of notation](https://en.wikipedia.org/wiki/Abuse_of_notation) is to define the [del operator](https://en.wikipedia.org/wiki/Del_operator) (∇) as follows in three-dimensional [Euclidean space](https://en.wikipedia.org/wiki/Euclidean_space) $\mathbb {R} ^{3}$ with [unit vectors](https://en.wikipedia.org/wiki/Unit_vectors) ${\hat {\mathbf {i} }},{\hat {\mathbf {j} }},{\hat {\mathbf {k} }}$:

$$
\nabla =\left[{\frac {\partial }{\partial x}}\right]{\hat {\mathbf {i} }}+\left[{\frac {\partial }{\partial y}}\right]{\hat {\mathbf {j} }}+\left[{\frac {\partial }{\partial z}}\right]{\hat {\mathbf {k} }}
$$

Or, more generally, for n-dimensional Euclidean space $\mathbb {R} ^{n}$ with coordinates $x_{1},\ldots ,x_{n}$ and unit vectors ${\hat {\mathbf {e} }}_{1},\ldots ,{\hat {\mathbf {e} }}_{n}$:

$$
\nabla =\sum _{j=1}^{n}\left[{\frac {\partial }{\partial x_{j}}}\right]{\hat {\mathbf {e} }}_{j}=\left[{\frac {\partial }{\partial x_{1}}}\right]{\hat {\mathbf {e} }}_{1}+\left[{\frac {\partial }{\partial x_{2}}}\right]{\hat {\mathbf {e} }}_{2}+\dots +\left[{\frac {\partial }{\partial x_{n}}}\right]{\hat {\mathbf {e} }}_{n}
$$

## Directional derivative

![[media/87ea57383772deb1d1c9e545f4acc05165ec9424.png]]
A [contour plot](https://en.wikipedia.org/wiki/Contour_plot) of $f(x,y)=x^{2}+y^{2}$, showing the gradient vector in black, and the unit vector $\mathbf {u}$ scaled by the directional derivative in the direction of $\mathbf {u}$ in orange. The gradient vector is longer because the gradient points in the direction of greatest rate of increase of a function.

The *directional derivative* of a [scalar function](https://en.wikipedia.org/wiki/Scalar_function) 

$$
f(\mathbf {x} )=f(x_{1},x_{2},\ldots ,x_{n})
$$

 along a vector 

$$
\mathbf {v} =(v_{1},\ldots ,v_{n})
$$

 is the [function](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)") $\nabla _{\mathbf {v} }{f}$ defined by the [limit](https://en.wikipedia.org/wiki/Limit_(mathematics) "Limit (mathematics)") 

$$
\nabla _{\mathbf {v} }{f}(\mathbf {x} )=\lim _{h\to 0}{\frac {f(\mathbf {x} +h\mathbf {v} )-f(\mathbf {x} )}{h||\mathbf {v} ||}}=\left.{\frac {1}{||\mathbf {v} ||}}{\frac {\mathrm {d} }{\mathrm {d} t}}f(\mathbf {x} +t\mathbf {v} )\right|_{t=0}.
$$

This definition is valid in a broad range of contexts, for example, where the [norm](https://en.wikipedia.org/wiki/Euclidean_norm) of a vector (and hence a unit vector) is defined.

## Example

Suppose that f is a function of more than one variable. For instance,

$$
z=f(x,y)=x^{2}+xy+y^{2}.
$$

![[media/660698b66c782552d8afb3e91232a118ed44e99b.png]]

A graph of *z* = *x*<sup>2</sup> + *xy* + *y*<sup>2</sup>. For the partial derivative at (1, 1) that leaves y constant, the corresponding [tangent](https://en.wikipedia.org/wiki/Tangent) line is parallel to the xz-plane.

![[media/4a581c778fa688e9b53ebddae02b1390bc760ad8.png]]

A slice of the graph above showing the function in the xz-plane at *y* = 1. The two axes are shown here with different scales. The slope of the tangent line is 3.

The [graph](https://en.wikipedia.org/wiki/Graph_of_a_function) of this function defines a [surface](https://en.wikipedia.org/wiki/Surface_(topology) "Surface (topology)") in [Euclidean space](https://en.wikipedia.org/wiki/Euclidean_space). To every point on this surface, there are an infinite number of [tangent lines](https://en.wikipedia.org/wiki/Tangent_line). Partial differentiation is the act of choosing one of these lines and finding its [slope](https://en.wikipedia.org/wiki/Slope). Usually, the lines of most interest are those that are parallel to the xz-plane, and those that are parallel to the yz-plane (which result from holding either y or x constant, respectively).

To find the slope of the line tangent to the function at *P*(1, 1) and parallel to the xz-plane, we treat y as a constant. The graph and this plane are shown on the right. Below, we see how the function looks on the plane *y* = 1. By finding the [derivative](https://en.wikipedia.org/wiki/Derivative) of the equation while assuming that y is a constant, we find that the slope of f at the point (*x*, *y*) is:

$$
{\frac {\partial z}{\partial x}}=2x+y.
$$

So at (1, 1), by substitution, the slope is 3. Therefore,

$$
{\frac {\partial z}{\partial x}}=3
$$

at the point (1, 1). That is, the partial derivative of z with respect to x at (1, 1) is 3, as shown in the graph.

The function f can be reinterpreted as a family of functions of one variable indexed by the other variables:

$$
f(x,y)=f_{y}(x)=x^{2}+xy+y^{2}.
$$

In other words, every value of y defines a function, denoted *f<sub>y</sub>*, which is a function of one variable x. That is,

$$
f_{y}(x)=x^{2}+xy+y^{2}.
$$

In this section the subscript notation *f<sub>y</sub>* denotes a function contingent on a fixed value of y, and not a partial derivative.

Once a value of y is chosen, say a, then *f*(*x*,*y*) determines a function *f<sub>a</sub>* which traces a curve *x*<sup>2</sup> + *ax* + *a*<sup>2</sup> on the xz-plane:

$$
f_{a}(x)=x^{2}+ax+a^{2}.
$$

In this expression, a is a *constant*, not a *variable*, so *f<sub>a</sub>* is a function of only one real variable, that being x. Consequently, the definition of the derivative for a function of one variable applies:

$$
f_{a}'(x)=2x+a.
$$

The above procedure can be performed for any choice of a. Assembling the derivatives together into a function gives a function which describes the variation of f in the x direction:

$$
{\frac {\partial f}{\partial x}}(x,y)=2x+y.
$$

This is the partial derivative of f with respect to x. Here '∂' is a rounded 'd' called the *[partial derivative symbol](https://en.wikipedia.org/wiki/Partial_derivative_symbol)*; to distinguish it from the letter 'd', '∂' is sometimes pronounced "partial".

## Higher order partial derivatives

Second and higher order partial derivatives are defined analogously to the higher order derivatives of univariate functions. For the function $f(x,y,...)$ the "own" second partial derivative with respect to x is simply the partial derivative of the partial derivative (both with respect to x):

$$
{\frac {\partial ^{2}f}{\partial x^{2}}}\equiv \partial {\frac {\partial f/\partial x}{\partial x}}\equiv {\frac {\partial f_{x}}{\partial x}}\equiv f_{xx}.
$$

The cross partial derivative with respect to x and y is obtained by taking the partial derivative of f with respect to x, and then taking the partial derivative of the result with respect to y, to obtain

$$
{\frac {\partial ^{2}f}{\partial y\,\partial x}}\equiv \partial {\frac {\partial f/\partial x}{\partial y}}\equiv {\frac {\partial f_{x}}{\partial y}}\equiv f_{xy}.
$$

[Schwarz's theorem](https://en.wikipedia.org/wiki/Schwarz_theorem) states that if the second derivatives are continuous, the expression for the cross partial derivative is unaffected by which variable the partial derivative is taken with respect to first and which is taken second. That is,

$$
{\frac {\partial ^{2}f}{\partial x\,\partial y}}={\frac {\partial ^{2}f}{\partial y\,\partial x}}
$$

or equivalently $f_{yx}=f_{xy}.$

Own and cross partial derivatives appear in the [[Hessian Matrix]] which is used in the [second order conditions](https://en.wikipedia.org/wiki/Second_order_condition) in [optimization](https://en.wikipedia.org/wiki/Optimization) problems. The higher order partial derivatives can be obtained by successive differentiation

## Antiderivative analogue

There is a concept for partial derivatives that is analogous to [antiderivatives](https://en.wikipedia.org/wiki/Antiderivative) for regular derivatives. Given a partial derivative, it allows for the partial recovery of the original function.

Consider the example of

$$
{\frac {\partial z}{\partial x}}=2x+y.
$$

The so-called partial integral can be taken with respect to x (treating y as constant, in a similar manner to partial differentiation):

$$
z=\int {\frac {\partial z}{\partial x}}\,dx=x^{2}+xy+g(y).
$$

Here, the [constant of integration](https://en.wikipedia.org/wiki/Constant_of_integration) is no longer a constant, but instead a function of all the variables of the original function except x. The reason for this is that all the other variables are treated as constant when taking the partial derivative, so any function which does not involve x will disappear when taking the partial derivative, and we have to account for this when we take the antiderivative. The most general way to represent this is to have the constant represent an unknown function of all the other variables.

Thus the set of functions $x^{2}+xy+g(y)$, where g is any one-argument function, represents the entire set of functions in variables *x*, *y* that could have produced the x-partial derivative $2x+y$.

If all the partial derivatives of a function are known (for example, with the [gradient](https://en.wikipedia.org/wiki/Gradient)), then the antiderivatives can be matched via the above process to reconstruct the original function up to a constant. Unlike in the single-variable case, however, not every set of functions can be the set of all (first) partial derivatives of a single function. In other words, not every vector field is [conservative](https://en.wikipedia.org/wiki/Conservative_vector_field).

## Applications

### Geometry

![[media/8a732d14c138bf1fedcb1e77571e17af2fdb418c.png]]
The volume of a cone depends on height and radius

The [volume](https://en.wikipedia.org/wiki/Volume) V of a [cone](https://en.wikipedia.org/wiki/Cone_(geometry)) depends on the cone's [height](https://en.wikipedia.org/wiki/Height) h and its [radius](https://en.wikipedia.org/wiki/Radius) r according to the formula

$$
V(r,h)={\frac {\pi r^{2}h}{3}}.
$$

The partial derivative of V with respect to r is

$$
{\frac {\partial V}{\partial r}}={\frac {2\pi rh}{3}},
$$

which represents the rate with which a cone's volume changes if its radius is varied and its height is kept constant. The partial derivative with respect to h equals ${\frac {1}{3}}\pi r^{2}$, which represents the rate with which the volume changes if its height is varied and its radius is kept constant.

By contrast, the [*total* derivative](https://en.wikipedia.org/wiki/Total_derivative) of V with respect to r and h are respectively

$$
{\begin{aligned}{\frac {dV}{dr}}&=\overbrace {\frac {2\pi rh}{3}} ^{\frac {\partial V}{\partial r}}+\overbrace {\frac {\pi r^{2}}{3}} ^{\frac {\partial V}{\partial h}}{\frac {dh}{dr}}\,,\\{\frac {dV}{dh}}&=\overbrace {\frac {\pi r^{2}}{3}} ^{\frac {\partial V}{\partial h}}+\overbrace {\frac {2\pi rh}{3}} ^{\frac {\partial V}{\partial r}}{\frac {dr}{dh}}\,.\end{aligned}}
$$

The difference between the total and partial derivative is the elimination of indirect dependencies between variables in partial derivatives.

If (for some arbitrary reason) the cone's proportions have to stay the same, and the height and radius are in a fixed ratio k,

$$
k={\frac {h}{r}}={\frac {dh}{dr}}.
$$

This gives the total derivative with respect to r,

$$
{\frac {dV}{dr}}={\frac {2\pi rh}{3}}+{\frac {\pi r^{2}}{3}}k\,,
$$

which simplifies to

$$
{\frac {dV}{dr}}=k\pi r^{2},
$$

Similarly, the total derivative with respect to h is

$$
{\frac {dV}{dh}}=\pi r^{2}.
$$

The total derivative with respect to *both* r and h of the volume intended as scalar function of these two variables is given by the [gradient](https://en.wikipedia.org/wiki/Gradient) vector

$$
\nabla V=\left({\frac {\partial V}{\partial r}},{\frac {\partial V}{\partial h}}\right)=\left({\frac {2}{3}}\pi rh,{\frac {1}{3}}\pi r^{2}\right).
$$

### Optimization

Partial derivatives appear in any calculus-based [optimization](https://en.wikipedia.org/wiki/Optimization) problem with more than one choice variable. For example, in [economics](https://en.wikipedia.org/wiki/Economics) a firm may wish to maximize [profit](https://en.wikipedia.org/wiki/Profit_(economics) "Profit (economics)") π(*x*, *y*) with respect to the choice of the quantities x and y of two different types of output. The [first order conditions](https://en.wikipedia.org/wiki/First_order_condition) for this optimization are π<sub>*x*</sub> = 0 = π<sub>*y*</sub>. Since both partial derivatives π<sub>*x*</sub> and π<sub>*y*</sub> will generally themselves be functions of both arguments x and y, these two first order conditions form a [system of two equations in two unknowns](https://en.wikipedia.org/wiki/System_of_equations).

### Thermodynamics, quantum mechanics and mathematical physics

Partial derivatives appear in thermodynamic equations like [Gibbs-Duhem equation](https://en.wikipedia.org/wiki/Gibbs-Duhem_equation), in quantum mechanics as in [Schrödinger wave equation](https://en.wikipedia.org/wiki/Schr%C3%B6dinger_equation), as well as in other equations from [mathematical physics](https://en.wikipedia.org/wiki/Mathematical_physics). The variables being held constant in partial derivatives here can be ratios of simple variables like [mole fractions](https://en.wikipedia.org/wiki/Mole_fraction) *x<sub>i</sub>* in the following example involving the Gibbs energies in a ternary mixture system:

$$
{\bar {G_{2}}}=G+(1-x_{2})\left({\frac {\partial G}{\partial x_{2}}}\right)_{\frac {x_{1}}{x_{3}}}
$$

Express [mole fractions](https://en.wikipedia.org/wiki/Mole_fraction) of a component as functions of other components' mole fraction and binary mole ratios:

${\begin{aligned}x_{1}&={\frac {1-x_{2}}{1+{\frac {x_{3}}{x_{1}}}}}\\x_{3}&={\frac {1-x_{2}}{1+{\frac {x_{1}}{x_{3}}}}}\end{aligned}}$

Differential quotients can be formed at constant ratios like those above:

$$
{\begin{aligned}\left({\frac {\partial x_{1}}{\partial x_{2}}}\right)_{\frac {x_{1}}{x_{3}}}&=-{\frac {x_{1}}{1-x_{2}}}\\\left({\frac {\partial x_{3}}{\partial x_{2}}}\right)_{\frac {x_{1}}{x_{3}}}&=-{\frac {x_{3}}{1-x_{2}}}\end{aligned}}
$$

Ratios X, Y, Z of mole fractions can be written for ternary and multicomponent systems:

$$
{\begin{aligned}X&={\frac {x_{3}}{x_{1}+x_{3}}}\\Y&={\frac {x_{3}}{x_{2}+x_{3}}}\\Z&={\frac {x_{2}}{x_{1}+x_{2}}}\end{aligned}}
$$

which can be used for solving [partial differential equations](https://en.wikipedia.org/wiki/Partial_differential_equation) like:

$$
\left({\frac {\partial \mu _{2}}{\partial n_{1}}}\right)_{n_{2},n_{3}}=\left({\frac {\partial \mu _{1}}{\partial n_{2}}}\right)_{n_{1},n_{3}}
$$

This equality can be rearranged to have differential quotient of mole fractions on one side.

### Image resizing

Partial derivatives are key to target-aware image resizing algorithms. Widely known as [seam carving](https://en.wikipedia.org/wiki/Seam_carving), these algorithms require each [pixel](https://en.wikipedia.org/wiki/Pixel) in an image to be assigned a numerical 'energy' to describe their dissimilarity against orthogonal adjacent pixels. The [algorithm](https://en.wikipedia.org/wiki/Algorithm) then progressively removes rows or columns with the lowest energy. The formula established to determine a pixel's energy (magnitude of [gradient](https://en.wikipedia.org/wiki/Gradient) at a pixel) depends heavily on the constructs of partial derivatives.

### Economics

Partial derivatives play a prominent role in [economics](https://en.wikipedia.org/wiki/Economics), in which most functions describing economic behaviour posit that the behaviour depends on more than one variable. For example, a societal [consumption function](https://en.wikipedia.org/wiki/Consumption_function) may describe the amount spent on consumer goods as depending on both income and wealth; the [marginal propensity to consume](https://en.wikipedia.org/wiki/Marginal_propensity_to_consume) is then the partial derivative of the consumption function with respect to income.

## See also

- [d'Alembert operator](https://en.wikipedia.org/wiki/D%27Alembert_operator)
- [[Chain Rule]]
- [Curl (mathematics)](https://en.wikipedia.org/wiki/Curl_(mathematics) "Curl (mathematics)")
- [Divergence](https://en.wikipedia.org/wiki/Divergence)
- [Exterior derivative](https://en.wikipedia.org/wiki/Exterior_derivative)
- [Iterated integral](https://en.wikipedia.org/wiki/Iterated_integral)
- [Jacobian matrix and determinant](https://en.wikipedia.org/wiki/Jacobian_matrix_and_determinant)
- [Laplace operator](https://en.wikipedia.org/wiki/Laplace_operator)
- [[Multivariable Calculus]]
- [Symmetry of second derivatives](https://en.wikipedia.org/wiki/Symmetry_of_second_derivatives)
- [Triple product rule](https://en.wikipedia.org/wiki/Triple_product_rule), also known as the cyclic chain rule.

## Notes

1.  Cajori, Florian (1952), [A History of Mathematical Notations](https://archive.org/details/AHistoryOfMathematicalNotationVolII/page/n153/mode/2up), vol. 2 (3 ed.), The Open Court Publishing Company, 596
2.  Miller, Jeff (n.d.). ["Earliest Uses of Symbols of Calculus"](https://mathshistory.st-andrews.ac.uk/Miller/mathsym/calculus/). In O'Connor, John J.; [Robertson, Edmund F.](https://en.wikipedia.org/wiki/Edmund_F._Robertson) (eds.). *[MacTutor History of Mathematics archive](https://en.wikipedia.org/wiki/MacTutor_History_of_Mathematics_archive)*. [University of St Andrews](https://en.wikipedia.org/wiki/University_of_St_Andrews). Retrieved 2023-06-15.
3.  Spivak, M. (1965). [Calculus on Manifolds](https://archive.org/details/SpivakM.CalculusOnManifoldsPerseus2006Reprint). New York: W. A. Benjamin. p. 44. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780805390216](https://en.wikipedia.org/wiki/Special:BookSources/9780805390216).
4.  R. Wrede; M.R. Spiegel (2010). *Advanced Calculus* (3rd ed.). Schaum's Outline Series. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-07-162366-7](https://en.wikipedia.org/wiki/Special:BookSources/978-0-07-162366-7).
5.  The applicability extends to functions over spaces without a [metric](https://en.wikipedia.org/wiki/Metric_(mathematics)) and to [differentiable manifolds](https://en.wikipedia.org/wiki/Differentiable_manifold), such as in [general relativity](https://en.wikipedia.org/wiki/General_relativity).
6.  This can also be expressed as the [adjointness](https://en.wikipedia.org/wiki/Adjoint_functors) between the [product space](https://en.wikipedia.org/wiki/Product_topology) and [function space](https://en.wikipedia.org/wiki/Function_space) constructions.
7.  [Chiang, Alpha C.](https://en.wikipedia.org/wiki/Alpha_Chiang) (1984). *Fundamental Methods of Mathematical Economics* (3rd ed.). McGraw-Hill.

## External links

- ["Partial derivative"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society), 2001 \[1994\]
- [Partial Derivatives](http://mathworld.wolfram.com/PartialDerivative.html) at [MathWorld](https://en.wikipedia.org/wiki/MathWorld)

