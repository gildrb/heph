[[calculus-analysis.base]]

> Source: [[Multivariable Calculus]]
> License: Wikipedia content is available under CC BY-SA 4.0.

**Multivariable calculus** (also known as **multivariate calculus**) is the extension of [calculus](https://en.wikipedia.org/wiki/Calculus) in one [variable](https://en.wikipedia.org/wiki/Variable_(mathematics) "Variable (mathematics)") to [functions of several variables](https://en.wikipedia.org/wiki/Function_of_several_real_variables): the [differentiation](https://en.wikipedia.org/wiki/Differential_calculus) and [integration](https://en.wikipedia.org/wiki/Integral) of functions involving multiple variables (*[multivariate](https://en.wikipedia.org/wiki/Multivariate_(mathematics))*), rather than just one.

Multivariable calculus may be thought of as an elementary part of [calculus on Euclidean space](https://en.wikipedia.org/wiki/Calculus_on_Euclidean_space). The special case of calculus in three dimensional space is often called *[vector calculus](https://en.wikipedia.org/wiki/Vector_calculus)*.

## Introduction

In single-variable calculus, operations like differentiation and integration are made to functions of a single variable. In multivariate calculus, it is required to generalize these to multiple variables, and the [domain](https://en.wikipedia.org/wiki/Domain_of_a_function) is therefore multi-dimensional. Care is therefore required in these generalizations, because of two key differences between 1D and higher dimensional spaces:

1.  There are infinite ways to approach a single point in higher dimensions, as opposed to two (from the positive and negative direction) in 1D;
2.  There are multiple extended objects associated with the dimension; for example, a 1D function is represented as a curve on the 2D [Cartesian plane](https://en.wikipedia.org/wiki/Cartesian_plane), but a [scalar](https://en.wikipedia.org/wiki/Scalar_(mathematics) "Scalar (mathematics)")-valued function of two variables is a surface in 3D, while curves can also live in 3D space.

The consequence of the first difference is the difference in the definition of the limits and continuity. Directional [limits](https://en.wikipedia.org/wiki/Limit_of_a_function) and [derivatives](https://en.wikipedia.org/wiki/Directional_derivative) define the limit and differential along a 1D parametrized curve, reducing the problem to the 1D case. Further higher-dimensional objects can be constructed from these operators.

The consequence of the second difference is the existence of multiple types of integration, including [line integrals](https://en.wikipedia.org/wiki/Line_integral), [surface integrals](https://en.wikipedia.org/wiki/Surface_integral) and [volume integrals](https://en.wikipedia.org/wiki/Volume_integral). Due to the non-uniqueness of these integrals, an [antiderivative](https://en.wikipedia.org/wiki/Antiderivative) or [indefinite integral](https://en.wikipedia.org/wiki/Indefinite_integral) cannot be properly defined.

## Limits

A study of [limits](https://en.wikipedia.org/wiki/Limit_of_a_function) and [continuity](https://en.wikipedia.org/wiki/Continuous_function) in multivariable calculus yields many counterintuitive results not demonstrated by single-variable functions.

A limit along a path may be defined by considering a parametrised path $s(t):\mathbb {R} \to \mathbb {R} ^{n}$ in n-dimensional Euclidean space. Any function $f({\overrightarrow {x}}):\mathbb {R} ^{n}\to \mathbb {R} ^{m}$ can then be projected on the path as a 1D function $f(s(t))$. The limit of $f$ to the point $s(t_{0})$ along the path $s(t)$ can hence be defined as

|  |  |  |
|----|----|----|
| $\lim _{{\overrightarrow {x}}\to s(t_{0})}f({\overrightarrow {x}})=\lim _{t\to t_{0}}f(s(t))$ |  | 1 |

Note that the value of this limit can be dependent on the form of $s(t)$, i.e. the path chosen, not just the point which the limit approaches. For example, consider the function

$f(x,y)={\frac {x^{2}y}{x^{4}+y^{2}}}.$

If the point $(0,0)$ is approached through the line $y=kx$, or in parametric form:

![[media/a14b54e6cf13e5fbebdaf7712df710f446659a23.png]]
Plot of the function <em>f</em>(<em>x</em>, <em>y</em>) = (<em>x</em>²y)/(<em>x</em><sup>4</sup> + <em>y</em><sup>2</sup>)

|  |  |  |
|----|----|----|
| $x(t)=t,\,y(t)=kt$ |  | 2 |

Then the limit along the path will be:

|  |  |  |
|----|----|----|
| $\lim _{t\to 0}f(x(t),y(t))=\lim _{t\to 0}{\frac {kt^{3}}{t^{4}+k^{2}t^{2}}}=0$ |  | 3 |

On the other hand, if the path $y=\pm x^{2}$ (or parametrically, $x(t)=t,\,y(t)=\pm t^{2}$) is chosen, then the limit becomes:

|  |  |  |
|----|----|----|
| $\lim _{t\to 0}f(x(t),y(t))=\lim _{t\to 0}{\frac {\pm t^{4}}{t^{4}+t^{4}}}=\pm {\frac {1}{2}}$ |  | 4 |

Since taking different paths towards the same point yields different values, a general limit at the point $(0,0)$ cannot be defined for the function.

A general limit can be defined if the limits to a point along all possible paths converge to the same value, i.e. we say for a function $f:\mathbb {R} ^{n}\to \mathbb {R} ^{m}$ that the limit of $f$ to some point $x_{0}\in \mathbb {R} ^{n}$ is L, if and only if

|  |  |  |
|----|----|----|
| $\lim _{t\to t_{0}}f(s(t))=L$ |  | 5 |

for all continuous functions $s(t):\mathbb {R} \to \mathbb {R} ^{n}$ such that $s(t_{0})=x_{0}$.

### Continuity

From the concept of limit along a path, we can then derive the definition for multivariate continuity in the same manner, that is: we say for a function $f:\mathbb {R} ^{n}\to \mathbb {R} ^{m}$ that $f$ is continuous at the point $x_{0}$, if and only if

|  |  |  |
|----|----|----|
| $\lim _{t\to t_{0}}f(s(t))=f(x_{0})$ |  | 5 |

for all continuous functions $s(t):\mathbb {R} \to \mathbb {R} ^{n}$ such that $s(t_{0})=x_{0}$.

As with limits, being continuous along *one* path $s(t)$ does not imply multivariate continuity.

Continuity in each argument not being sufficient for multivariate continuity can also be seen from the following example. For example, for a real-valued function $f:\mathbb {R} ^{2}\to \mathbb {R}$ with two real-valued parameters, $f(x,y)$, continuity of $f$ in $x$ for fixed $y$ and continuity of $f$ in $y$ for fixed $x$ does not imply continuity of $f$.

Consider

$f(x,y)={\begin{cases}{\frac {y}{x}}-y&{\text{if}}\quad 0\leq y<x\leq 1\\{\frac {x}{y}}-x&{\text{if}}\quad 0\leq x<y\leq 1\\1-x&{\text{if}}\quad 0<x=y\\0&{\text{everywhere else}}.\end{cases}}$

It is easy to verify that this function is zero by definition on the boundary and outside of the quadrangle $(0,1)\times (0,1)$. Furthermore, the functions defined for constant $x$ and $y$ and $0\leq a\leq 1$ by

$g_{a}(x)=f(x,a)\quad$ and $\quad h_{a}(y)=f(a,y)\quad$

are continuous. Specifically,

$g_{0}(x)=f(x,0)=h_{0}(0,y)=f(0,y)=0$ for all x and y. Therefore, $f(0,0)=0$ and moreover, along the coordinate axes, $\lim _{x\to 0}f(x,0)=0$ and $\lim _{y\to 0}f(0,y)=0$. Therefore the function is continuous along both individual arguments.

However, consider the parametric path $x(t)=t,\,y(t)=t$. The parametric function becomes

|  |  |  |
|----|----|----|
| $f(x(t),y(t))={\begin{cases}1-t&{\text{if}}\quad t>0\\0&{\text{everywhere else}}.\end{cases}}$ |  | 6 |

Therefore,

|  |  |  |
|----|----|----|
| $\lim _{t\to 0^{+}}f(x(t),y(t))=1\neq f(0,0)=0$ |  | 7 |

It is hence clear that the function is not multivariate continuous, despite being continuous in both coordinates.

### Theorems regarding multivariate limits and continuity

- All properties of linearity and superposition from single-variable calculus carry over to multivariate calculus.
- **Composition**: If $f:\mathbb {R} ^{n}\to \mathbb {R} ^{m}$ and $g:\mathbb {R} ^{m}\to \mathbb {R} ^{p}$ are both multivariate continuous functions at the points $x_{0}\in \mathbb {R} ^{n}$ and $f(x_{0})\in \mathbb {R} ^{m}$ respectively, then $g\circ f:\mathbb {R} ^{n}\to \mathbb {R} ^{p}$ is also a multivariate continuous function at the point $x_{0}$.
- **Multiplication**: If $f:\mathbb {R} ^{n}\to \mathbb {R}$ and $g:\mathbb {R} ^{n}\to \mathbb {R}$ are both continuous functions at the point $x_{0}\in \mathbb {R} ^{n}$, then $fg:\mathbb {R} ^{n}\to \mathbb {R}$ is continuous at $x_{0}$, and $f/g:\mathbb {R} ^{n}\to \mathbb {R}$ is also continuous at $x_{0}$ provided that $g(x_{0})\neq 0$.
- If $f:\mathbb {R} ^{n}\to \mathbb {R}$ is a continuous function at point $x_{0}\in \mathbb {R} ^{n}$, then $|f|$ is also continuous at the same point.
- If $f:\mathbb {R} ^{n}\to \mathbb {R} ^{m}$ is [Lipschitz continuous](https://en.wikipedia.org/wiki/Lipschitz_continuous) (with the appropriate normed spaces as needed) in the neighbourhood of the point $x_{0}\in \mathbb {R} ^{n}$, then $f$ is multivariate continuous at $x_{0}$.

<table class="mw-collapsible mw-archivedtalk" role="presentation" style="color:inherit; background: transparent; text-align: left; border: 1px solid Silver; margin: 0.2em auto auto; width:100%; clear: both; padding: 1px;">

Proof

&#10;
<p>From the Lipschitz continuity condition for $f$ we have</p>
<table class="numblk" role="presentation" style="margin-left: 1.6em;">

$|f(s(t))-f(s(t_{0}))|\leq K|s(t)-s(t_{0})|$

8

</table>
<p>where $K$ is the Lipschitz constant. Note also that, as $s(t)$ is continuous at $t_{0}$, for every $\delta >0$ there exists a $\epsilon >0$ such that $|s(t)-s(t_{0})|<\delta$ $\forall |t-t_{0}|<\epsilon$.</p>
<p>Hence, for every $\alpha >0$, choose $\delta ={\frac {\alpha }{K}}$; there exists an $\epsilon >0$ such that for all $t$ satisfying $|t-t_{0}|<\epsilon$, $|s(t)-s(t_{0})|<\delta$, and $|f(s(t))-f(s(t_{0}))|\leq K|s(t)-s(t_{0})|<K\delta =\alpha$. Hence $\lim _{t\to t_{0}}f(s(t))$ converges to $f(s(t_{0}))$ regardless of the precise form of $s(t)$.</p>

</table>

## Differentiation

### Directional derivative

The derivative of a single-variable function is defined as

|  |  |  |
|----|----|----|
| ${\frac {df}{dx}}=\lim _{h\to 0}{\frac {f(x+h)-f(x)}{h}}$ |  | 9 |

Using the extension of limits discussed above, one can then extend the definition of the derivative to a scalar-valued function $f:\mathbb {R} ^{n}\to \mathbb {R}$ along some path $s(t):\mathbb {R} \to \mathbb {R} ^{n}$:

|  |  |  |
|----|----|----|
| $\left.{\frac {df}{dx}}\right|_{s(t),t=t_{0}}=\lim _{h\to 0}{\frac {f(s(t_{0}+h))-f(s(t_{0}))}{|s(t_{0}+h)-s(t_{0})|}}$ |  | 10 |

Unlike limits, for which the value depends on the exact form of the path $s(t)$, it can be shown that the derivative along the path depends only on the tangent vector of the path at $s(t_{0})$, i.e. $s'(t_{0})$, provided that $f$ is [Lipschitz continuous](https://en.wikipedia.org/wiki/Lipschitz_continuous) at $s(t_{0})$, and that the limit exists for at least one such path.

<table class="mw-collapsible mw-archivedtalk" role="presentation" style="color:inherit; background: transparent; text-align: left; border: 1px solid Silver; margin: 0.2em auto auto; width:100%; clear: both; padding: 1px;">

Proof

&#10;
<p>For $s(t)$ continuous up to the first derivative (this statement is well defined as $s$ is a function of one variable), we can write the [Taylor expansion](https://en.wikipedia.org/wiki/Taylor_expansion) of $s$ around $t_{0}$ using [Taylor's theorem](https://en.wikipedia.org/wiki/Taylor%27s_theorem) to construct the remainder:</p>
<table class="numblk" role="presentation" style="margin-left: 1.6em;">

$s(t)=s(t_{0})+s'(\tau )(t-t_{0})$

11

</table>
<p>where $\tau \in [t_{0},t]$.</p>
<p>Substituting this into <strong>[10](#math_10)</strong>,</p>
<table class="numblk" role="presentation" style="margin-left: 1.6em;">

$\left.{\frac {df}{dx}}\right|_{s(t),t=t_{0}}=\lim _{h\to 0}{\frac {f(s(t_{0})+s'(\tau )h)-f(s(t_{0}))}{|s'(\tau )h|}}$

12

</table>
<p>where $\tau (h)\in [t_{0},t_{0}+h]$.</p>
<p>Lipschitz continuity gives us $|f(x)-f(y)|\leq K|x-y|$ for some finite $K$, $\forall x,y\in \mathbb {R} ^{n}$. It follows that $|f(x+O(h))-f(x)|\sim O(h)$.</p>
<p>Note also that given the continuity of $s'(t)$, $s'(\tau )=s'(t_{0})+O(h)$ as $h\to 0$.</p>
<p>Substituting these two conditions into <strong>[12](#math_12)</strong>,</p>
<table class="numblk" role="presentation" style="margin-left: 1.6em;">

$\left.{\frac {df}{dx}}\right|_{s(t),t=t_{0}}=\lim _{h\to 0}{\frac {f(s(t_{0})+s'(t_{0})h)-f(s(t_{0}))+O(h^{2})}{|s'(t_{0})h|+O(h^{2})}}$

13

</table>
<p>whose limit depends only on $s'(t_{0})$ as the dominant term.</p>

</table>

It is therefore possible to generalize the definition of the directional derivative as follows: The directional derivative of a scalar-valued function $f:\mathbb {R} ^{n}\to \mathbb {R}$ along the unit vector ${\hat {\mathbf {u}}}$ at some point $x_{0}\in \mathbb {R} ^{n}$ is

|  |  |  |
|----|----|----|
| $\nabla _{\hat {\mathbf {u}}}f(x_{0})=\lim _{t\to 0}{\frac {f(x_{0}+{\hat {\mathbf {u}}}t)-f(x_{0})}{t}}$ |  | 14 |

or, when expressed in terms of ordinary differentiation,

|  |  |  |
|----|----|----|
| $\nabla _{\hat {\mathbf {u}}}f(x_{0})=\left.{\frac {df(x_{0}+{\hat {\mathbf {u}}}t)}{dt}}\right|_{t=0}$ |  | 15 |

which is a well defined expression because $f(x_{0}+{\hat {\mathbf {u}}}t)$ is a scalar function with one variable in $t$.

It is not possible to define a unique scalar derivative without a direction; it is clear for example that $\nabla _{\hat {\mathbf {u}}}f(x_{0})=-\nabla _{-{\hat {\mathbf {u}}}}f(x_{0})$. It is also possible for directional derivatives to exist for some directions but not for others.

### Partial derivative

The partial derivative generalizes the notion of the derivative to higher dimensions. A partial derivative of a multivariable function is a [derivative](https://en.wikipedia.org/wiki/Derivative) with respect to one variable with all other variables held constant.

A partial derivative may be thought of as the directional derivative of the function along a coordinate axis.

Partial derivatives may be combined in interesting ways to create more complicated expressions of the derivative. In [vector calculus](https://en.wikipedia.org/wiki/Vector_calculus), the [del](https://en.wikipedia.org/wiki/Del) operator ($\nabla$) is used to define the concepts of [gradient](https://en.wikipedia.org/wiki/Gradient), [divergence](https://en.wikipedia.org/wiki/Divergence), and [curl](https://en.wikipedia.org/wiki/Curl_(mathematics) "Curl (mathematics)") in terms of partial derivatives. A matrix of partial derivatives, the **[Jacobian](https://en.wikipedia.org/wiki/Jacobian_matrix_and_determinant)** matrix, may be used to represent the derivative of a function between two spaces of arbitrary dimension. The derivative can thus be understood as a [[Linear Transformation]] which directly varies from point to point in the domain of the function.

[Differential equations](https://en.wikipedia.org/wiki/Differential_equations) containing partial derivatives are called [partial differential equations](https://en.wikipedia.org/wiki/Partial_differential_equations) or PDEs. These equations are generally more difficult to solve than [ordinary differential equations](https://en.wikipedia.org/wiki/Ordinary_differential_equations), which contain derivatives with respect to only one variable.

## Multiple integration

The multiple integral extends the concept of the [integral](https://en.wikipedia.org/wiki/Integral) to functions of any number of variables. Double and triple integrals may be used to calculate areas and volumes of regions in the plane and in space. [Fubini's theorem](https://en.wikipedia.org/wiki/Fubini%27s_theorem) guarantees that a multiple integral may be evaluated as a *repeated integral* or *iterated integral* as long as the integrand is continuous throughout the domain of integration.

The [surface integral](https://en.wikipedia.org/wiki/Surface_integral) and the [line integral](https://en.wikipedia.org/wiki/Line_integral) are used to integrate over curved [[Manifold|manifolds]] such as [surfaces](https://en.wikipedia.org/wiki/Surface_(mathematics) "Surface (mathematics)") and [curves](https://en.wikipedia.org/wiki/Curve).

### Fundamental theorem of calculus in multiple dimensions

In single-variable calculus, the [fundamental theorem of calculus](https://en.wikipedia.org/wiki/Fundamental_theorem_of_calculus) establishes a link between the derivative and the integral. The link between the derivative and the integral in multivariable calculus is embodied by the integral theorems of vector calculus:

- [Gradient theorem](https://en.wikipedia.org/wiki/Gradient_theorem)
- [Stokes' theorem](https://en.wikipedia.org/wiki/Stokes%27_theorem#Special_cases)
- [Divergence theorem](https://en.wikipedia.org/wiki/Divergence_theorem)
- [Green's theorem](https://en.wikipedia.org/wiki/Green%27s_theorem).

In a more advanced study of multivariable calculus, it is seen that these four theorems are specific incarnations of a more general theorem, the [generalized Stokes' theorem](https://en.wikipedia.org/wiki/Generalized_Stokes_theorem), which applies to the integration of [differential forms](https://en.wikipedia.org/wiki/Differential_forms) over [manifolds](https://en.wikipedia.org/wiki/Differentiable_manifold).

## Applications and uses

Techniques of multivariable calculus are used to study many objects of interest in the material world. In particular,

<table class="wikitable" style="text-align:center">

Type of functions
Applicable techniques

&#10;
[Curves](https://en.wikipedia.org/wiki/Curve)
![[media/d62cde508acdac66dbd922b7c8e28101890383e9.png]]
$f:\mathbb {R} \to \mathbb {R} ^{n}$<br />
for $n>1$
Lengths of curves, [line integrals](https://en.wikipedia.org/wiki/Line_integral), and [curvature](https://en.wikipedia.org/wiki/Curvature).

[Surfaces](https://en.wikipedia.org/wiki/Surface_(mathematics))
![[media/78f8d664eeb242b8b3741b36b081d372e8337098.png]]
$f:\mathbb {R} ^{2}\to \mathbb {R} ^{n}$<br />
for $n>2$
[Areas](https://en.wikipedia.org/wiki/Area) of surfaces, [surface integrals](https://en.wikipedia.org/wiki/Surface_integral), [flux](https://en.wikipedia.org/wiki/Flux) through surfaces, and curvature.

[Scalar fields](https://en.wikipedia.org/wiki/Scalar_fields)
![[media/3d52a8256ee3271c179bfcffc5c802ae67a2a0d4.png]]
$f:\mathbb {R} ^{n}\to \mathbb {R}$
Maxima and minima, [[Lagrange Multipliers]], [directional derivatives](https://en.wikipedia.org/wiki/Directional_derivative), [level sets](https://en.wikipedia.org/wiki/Level_set).

[Vector fields](https://en.wikipedia.org/wiki/Vector_fields)
![[media/0045dcfb38a7884de1e1f2fff2eac2aa28ce4f49.png]]
$f:\mathbb {R} ^{m}\to \mathbb {R} ^{n}$
Any of the operations of [vector calculus](https://en.wikipedia.org/wiki/Vector_calculus) including [gradient](https://en.wikipedia.org/wiki/Gradient), [divergence](https://en.wikipedia.org/wiki/Divergence), and [curl](https://en.wikipedia.org/wiki/Curl_(mathematics)).

</table>

Multivariable calculus can be applied to analyze [deterministic systems](https://en.wikipedia.org/wiki/Deterministic_system) that have multiple [degrees of freedom](https://en.wikipedia.org/wiki/Degrees_of_freedom_(physics_and_chemistry) "Degrees of freedom (physics and chemistry)"). Functions with [independent variables](https://en.wikipedia.org/wiki/Independent_variable) corresponding to each of the degrees of freedom are often used to model these systems, and multivariable calculus provides tools for characterizing the [system dynamics](https://en.wikipedia.org/wiki/System_dynamics).

Multivariate calculus is used in the [optimal control](https://en.wikipedia.org/wiki/Optimal_control) of [continuous time](https://en.wikipedia.org/wiki/Continuous_time) [dynamic systems](https://en.wikipedia.org/wiki/Dynamic_systems). It is used in [regression analysis](https://en.wikipedia.org/wiki/Regression_analysis) to derive formulas for estimating relationships among various sets of [empirical data](https://en.wikipedia.org/wiki/Empirical_data).

Multivariable calculus is used in many fields of [natural](https://en.wikipedia.org/wiki/Natural_science) and [social science](https://en.wikipedia.org/wiki/Social_science) and [engineering](https://en.wikipedia.org/wiki/Engineering) to model and study high-dimensional systems that exhibit deterministic behavior. In [economics](https://en.wikipedia.org/wiki/Economics), for example, [consumer choice](https://en.wikipedia.org/wiki/Consumer_choice) over a variety of goods, and [producer choice](https://en.wikipedia.org/wiki/Profit_maximization) over various inputs to use and outputs to produce, are modeled with multivariate calculus.

Non-deterministic, or [stochastic](https://en.wikipedia.org/wiki/Stochastic_process) systems can be studied using a different kind of mathematics, such as [stochastic calculus](https://en.wikipedia.org/wiki/Stochastic_calculus).

## See also

- [List of multivariable calculus topics](https://en.wikipedia.org/wiki/List_of_multivariable_calculus_topics)
- [Multivariate statistics](https://en.wikipedia.org/wiki/Multivariate_statistics)

## References

1.  ^        [Richard Courant](https://en.wikipedia.org/wiki/Richard_Courant); [Fritz John](https://en.wikipedia.org/wiki/Fritz_John) (14 December 1999). *Introduction to Calculus and Analysis Volume II/2*. Springer Science & Business Media. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-66570-0](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-66570-0).
2.  Spivak, Michael (1965). [Calculus on Manifolds](https://archive.org/details/SpivakM.CalculusOnManifolds_201703). New York: W. A. Benjamin, Inc. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780805390216](https://en.wikipedia.org/wiki/Special:BookSources/9780805390216).

## External links

- [UC Berkeley video lectures on Multivariable Calculus, Fall 2009, Professor Edward Frenkel](https://www.youtube.com/watch?v=cw6pHhjhKmk)
- [MIT video lectures on Multivariable Calculus, Fall 2007](https://www.youtube.com/playlist?list=PL4C4C8A7D06566F38)
- [Multivariable Calculus](http://www.math.gatech.edu/~cain/notes/calculus.html): A free online textbook by George Cain and James Herod
- [Multivariable Calculus Online](https://math.etsu.edu/Multicalc/): A free online textbook by Jeff Knisley
- [Multivariable Calculus – A Very Quick Review](http://www.ecs.umass.edu/mie/faculty/perot/mie440/Multivariable%20Calculus.pdf), Prof. Blair Perot, University of Massachusetts Amherst
- [Multivariable Calculus](http://www.stat.rice.edu/~dobelman/notes_papers/math/calculus.MV.pdf), Online text by Dr. Jerry Shurman
