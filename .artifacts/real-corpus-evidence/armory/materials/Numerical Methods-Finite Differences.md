[[numerical-methods.base]]

> Source: [Finite difference](https://en.wikipedia.org/wiki/Finite_difference)
> License: Wikipedia content is available under CC BY-SA 4.0.

A **finite difference** is a mathematical expression of the form *f*(*x* + *b*) − *f*(*x* + *a*). Finite differences (or the associated [difference quotients](https://en.wikipedia.org/wiki/Difference_quotient)) are often used as approximations of derivatives, such as in [numerical differentiation](https://en.wikipedia.org/wiki/Numerical_differentiation).

The [difference operator](https://en.wikipedia.org/wiki/Difference_operator), commonly denoted $\Delta$, is the [operator](https://en.wikipedia.org/wiki/Operator_(mathematics) "Operator (mathematics)") that maps a function f to the function $\Delta [f]$ defined by 

$$
\Delta [f](x)=f(x+1)-f(x).
$$

 A [difference equation](https://en.wikipedia.org/wiki/Difference_equation) is a [functional equation](https://en.wikipedia.org/wiki/Functional_equation) that involves the finite difference operator in the same way as a [differential equation](https://en.wikipedia.org/wiki/Differential_equation) involves [derivatives](https://en.wikipedia.org/wiki/Derivative). There are many similarities between difference equations and differential equations. Certain [recurrence relations](https://en.wikipedia.org/wiki/Recurrence_relation#Relationship_to_difference_equations_narrowly_defined) can be written as difference equations by replacing iteration notation with finite differences.

In [numerical analysis](https://en.wikipedia.org/wiki/Numerical_analysis), finite differences are widely used for [approximating derivatives](#Relation_with_derivatives), and the term "finite difference" is often used as an abbreviation of "finite difference approximation of derivatives".

## Basic types

![[media/c94f415158b6b8ac6f717ea72aa534bcae2b5ae6.png]]
The three types of the finite differences. The central difference about x gives the best approximation of the derivative of the function at x.

Three basic types are commonly considered: *forward*, *backward*, and *central* finite differences.

A forward difference, denoted $\Delta _{h}[f]$ of a [function](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)") f is a function defined as 

$$
\Delta _{h}[f](x)=f(x+h)-f(x).
$$

Depending on the application, the spacing h may be variable or constant. When not specified, the default value for h is 1; that is, 

$$
\Delta [f](x)=\Delta _{1}[f](x)=f(x+1)-f(x).
$$

A **backward difference** uses the function values at x and *x* − *h*, instead of the values at *x* + *h* and x: 

$$
\nabla _{h}[f](x)=f(x)-f(x-h)=\Delta _{h}[f](x-h).
$$

Finally, the **central difference** is given by 

$$
\delta _{h}[f](x)=f(x+{\tfrac {h}{2}})-f(x-{\tfrac {h}{2}})=\Delta _{\tfrac {h}{2}}[f](x)+\nabla _{\tfrac {h}{2}}[f](x).
$$

## Relation with derivatives

 The approximation of [derivatives](https://en.wikipedia.org/wiki/Derivative) by finite differences plays a central role in [finite difference methods](https://en.wikipedia.org/wiki/Finite_difference_method) for the [numerical](https://en.wikipedia.org/wiki/Numerical_analysis) solution of [differential equations](https://en.wikipedia.org/wiki/Differential_equation), especially [boundary value problems](https://en.wikipedia.org/wiki/Boundary_value_problem).

The [derivative](https://en.wikipedia.org/wiki/Derivative) of a function f at a point x is defined by the [limit](https://en.wikipedia.org/wiki/Limit_of_a_function) 

$$
f'(x)=\lim _{h\to 0}{\frac {f(x+h)-f(x)}{h}}.
$$

If h has a fixed (non-zero) value instead of approaching zero, then the right-hand side of the above equation would be written 

$$
{\frac {f(x+h)-f(x)}{h}}={\frac {\Delta _{h}[f](x)}{h}}.
$$

Hence, the forward difference divided by h approximates the derivative when h is small. The error in this approximation can be derived from [Taylor's theorem](https://en.wikipedia.org/wiki/Taylor%27s_theorem). Assuming that f is twice differentiable, we have 

$$
{\frac {\Delta _{h}[f](x)}{h}}-f'(x)=o(h)\to 0\quad {\text{as }}h\to 0.
$$

The same formula holds for the backward difference: 

$$
{\frac {\nabla _{h}[f](x)}{h}}-f'(x)=o(h)\to 0\quad {\text{as }}h\to 0.
$$

However, the central (also called centered) difference yields a more accurate approximation. If f is three times differentiable, 

$$
{\frac {\delta _{h}[f](x)}{h}}-f'(x)=o\left(h^{2}\right).
$$

The main problem<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup> with the central difference method, however, is that oscillating functions can yield zero derivative. If *f*(*nh*) = 1 for n odd, and *f*(*nh*) = 2 for n even, then *f*′(*nh*) = 0 if it is calculated with the [central difference scheme](https://en.wikipedia.org/wiki/Central_difference_scheme). This is particularly troublesome if the domain of f is discrete. See also [Symmetric derivative](https://en.wikipedia.org/wiki/Symmetric_derivative).

Authors for whom finite differences mean finite difference approximations define the forward/backward/central differences as the quotients given in this section (instead of employing the definitions given in the previous section).

## Higher-order differences

In an analogous way, one can obtain finite difference approximations to higher order derivatives and differential operators. For example, by using the above central difference formula for *f* ′(*x* + *h*/2) and *f* ′(*x* − *h*/2) and applying a central difference formula for the derivative of *f* ′ at x, we obtain the central difference approximation of the second derivative of   f :

Second-order central  

$$
f''(x)\approx {\frac {\delta _{h}^{2}[f](x)}{h^{2}}}={\frac {{\frac {f(x+h)-f(x)}{h}}-{\frac {f(x)-f(x-h)}{h}}}{h}}={\frac {f(x+h)-2f(x)+f(x-h)}{h^{2}}}~.
$$

Similarly we can apply other differencing formulas in a recursive manner.

Second-order forward  

$$
f''(x)\approx {\frac {\Delta _{h}^{2}[f](x)}{h^{2}}}={\frac {{\frac {f(x+2h)-f(x+h)}{h}}-{\frac {f(x+h)-f(x)}{h}}}{h}}={\frac {f(x+2h)-2f(x+h)+f(x)}{h^{2}}}~.
$$

Second-order backward  

$$
f''(x)\approx {\frac {\nabla _{h}^{2}[f](x)}{h^{2}}}={\frac {{\frac {f(x)-f(x-h)}{h}}-{\frac {f(x-h)-f(x-2h)}{h}}}{h}}={\frac {f(x)-2f(x-h)+f(x-2h)}{h^{2}}}~.
$$

More generally, the **n-th order forward, backward, and central** differences are given by, respectively,

Forward  

$$
\Delta _{h}^{n}[f](x)=\sum _{j=0}^{n}(-1)^{n-j}{\binom {n}{j}}f{\bigl (}x+jh{\bigr )},
$$

Backward  

$$
\nabla _{h}^{n}[f](x)=\sum _{j=0}^{n}(-1)^{j}{\binom {n}{j}}f(x-jh),
$$

Central  

$$
\delta _{h}^{n}[f](x)=\sum _{j=0}^{n}(-1)^{j}{\binom {n}{j}}f\left(x+\left({\frac {n}{2}}-j\right)h\right)~.
$$

These equations use [binomial coefficients](https://en.wikipedia.org/wiki/Binomial_coefficient) after the summation sign shown as $\ {\binom {n}{j}}~.$ Each row of [Pascal's triangle](https://en.wikipedia.org/wiki/Pascal%27s_triangle) provides the coefficient for each value of   j .

Note that the central difference will, for odd n, have h multiplied by non-integers. This is often a problem because it amounts to changing the interval of discretization. The problem may be remedied substituting the average of $\delta ^{n}[f](x-{\tfrac {h}{2}})$ and $\delta ^{n}[f](x+{\tfrac {h}{2}}).$

Forward differences applied to a [sequence](https://en.wikipedia.org/wiki/Sequence) are sometimes called the [binomial transform](https://en.wikipedia.org/wiki/Binomial_transform) of the sequence, and have a number of interesting combinatorial properties. Forward differences may be evaluated using the [Nörlund–Rice integral](https://en.wikipedia.org/wiki/N%C3%B6rlund%E2%80%93Rice_integral). The integral representation for these types of series is interesting, because the integral can often be evaluated using [asymptotic expansion](https://en.wikipedia.org/wiki/Asymptotic_expansion) or [saddle-point](https://en.wikipedia.org/wiki/Saddle-point) techniques; by contrast, the forward difference series can be extremely hard to evaluate numerically, because the binomial coefficients grow rapidly for large n.

The relationship of these higher-order differences with the respective derivatives is straightforward, 

$$
{\frac {\mathrm {d} ^{n}f}{(\mathrm {d} x)^{n}}}(x)={\frac {\Delta _{h}^{n}[f](x)}{h^{n}}}+{\mathcal {o}}(h)={\frac {\nabla _{h}^{n}[f](x)}{h^{n}}}+{\mathcal {o}}(h)={\frac {\delta _{h}^{n}[f](x)}{h^{n}}}+{\mathcal {o}}\!\left(h^{2}\right).
$$

Higher-order differences can also be used to construct better approximations. As mentioned above, the first-order difference approximates the first-order derivative up to a term of order h. However, the combination 

$$
{\frac {\Delta _{h}[f](x)-{\frac {1}{2}}\Delta _{h}^{2}[f](x)}{h}}=-{\frac {f(x+2h)-4f(x+h)+3f(x)}{2h}}
$$

 approximates *f* ′(*x*) up to a term of order *h*<sup>2</sup>. This can be proven by expanding the above expression in [[Taylor Series]], or by using the calculus of finite differences, explained below.

If necessary, the finite difference can be centered about any point by mixing forward, backward, and central differences.

Sometimes, the low order derivatives of a function may be analytically known, but high order derivatives are not. In these cases, the high order derivatives can be approximated by finite difference of low order derivatives, which is often more accurate and numerically more stable than finite difference of the function *f* (*x*) itself. This is sometimes called seminumerical differentiation. For example, when the first order derivative *f* ′(*x*) is available but the second order derivative *f* ′′(*x*) is not, the latter can be approximated by second-order central difference of *f* ′(*x*): 

$$
f''(x)\approx {\frac {f'(x+h)-f'(x-h)}{2h}}~.
$$

## Polynomials

For a given [polynomial](https://en.wikipedia.org/wiki/Polynomial) of degree *n* ≥ 1, expressed in the function *P*(*x*), with real numbers *a* ≠ 0 and *b* and *lower order terms* (if any) marked as l.o.t.: 

$$
P(x)=ax^{n}+\;bx^{n-1}+~l.o.t.
$$

After *n* pairwise differences, the following result can be achieved, where *h* ≠ 0 is a [real number](https://en.wikipedia.org/wiki/Real_number) marking the arithmetic difference: 

$$
\Delta _{h}^{n}[P](x)=ah^{n}n!
$$

Only the coefficient of the highest-order term remains. As this result is constant with respect to *x*, any further pairwise differences will have the value 0.

### Inductive proof

#### Base case

Let *Q*(*x*) be a polynomial of degree 1: 

$$
\Delta _{h}[Q](x)=Q(x+h)-Q(x)=[a(x+h)+b]-[ax+b]=ah=ah^{1}1!
$$

This proves it for the base case.

#### Inductive step

Let *R*(*x*) be a polynomial of degree *m* − 1 where *m* ≥ 2 and the coefficient of the highest-order term be *a* ≠ 0. Assuming the following holds true for all polynomials of degree *m* − 1: 

$$
\Delta _{h}^{m-1}[R](x)=ah^{m-1}(m-1)!
$$

Let *S*(*x*) be a polynomial of degree *m*. With one pairwise difference: 

$$
\Delta _{h}[S](x)=[a(x+h)^{m}+b(x+h)^{m-1}+{\text{l.o.t.}}]-[ax^{m}+bx^{m-1}+{\text{l.o.t.}}]=ahmx^{m-1}+{\text{l.o.t.}}=T(x)
$$

As *ahm* ≠ 0, this results in a polynomial *T*(*x*) of degree *m* − 1, with *ahm* as the coefficient of the highest-order term. Given the assumption above and *m* − 1 pairwise differences (resulting in a total of *m* pairwise differences for *S*(*x*)), it can be found that: 

$$
\Delta _{h}^{m-1}[T](x)=ahm\cdot h^{m-1}(m-1)!=ah^{m}m!
$$

This completes the proof.

### Application

This identity can be used to find the lowest-degree polynomial that intercepts a number of points (*x*, *y*) where the difference on the *x*-axis from one point to the next is a constant *h* ≠ 0. For example, given the following points:

|     |      |
|-----|------|
| *x* | *y*  |
| 1   | 4    |
| 4   | 109  |
| 7   | 772  |
| 10  | 2641 |
| 13  | 6364 |

We can use a differences table, where for all cells to the right of the first *y*, the following relation to the cells in the column immediately to the left exists for a cell (*a* + 1, *b* + 1), with the top-leftmost cell being at coordinate (0, 0): 

$$
(a+1,b+1)=(a,b+1)-(a,b)
$$

To find the first term, the following table can be used:

|  |  |  |  |  |
|----|----|----|----|----|
| *x* | *y* | Δ*y* | Δ<sup>2</sup>*y* | Δ<sup>3</sup>*y* |
| 1 | 4 |  |  |  |
| 4 | 109 | 105 |  |  |
| 7 | 772 | 663 | 558 |  |
| 10 | 2641 | 1869 | 1206 | 648 |
| 13 | 6364 | 3723 | 1854 | 648 |

This arrives at a constant 648. The arithmetic difference is *h* = 3, as established above. Given the number of pairwise differences needed to reach the constant, it can be surmised this is a polynomial of degree 3. Thus, using the identity above: 

$$
648=a\cdot 3^{3}\cdot 3!=a\cdot 27\cdot 6=a\cdot 162
$$

Solving for *a*, it can be found to have the value 4. Thus, the first term of the polynomial is 4*x*<sup>3</sup>.

Then, subtracting out the first term, which lowers the polynomial's degree, and finding the finite difference again:

|  |  |  |  |
|----|----|----|----|
| x | y | Δ*y* | Δ<sup>2</sup>*y* |
| 1 | 4 − 4(1)<sup>3</sup> = 4 − 4 = 0 |  |  |
| 4 | 109 − 4(4)<sup>3</sup> = 109 − 256 = −147 | −147 |  |
| 7 | 772 − 4(7)<sup>3</sup> = 772 − 1372 = −600 | −453 | −306 |
| 10 | 2641 − 4(10)<sup>3</sup> = 2641 − 4000 = −1359 | −759 | −306 |
| 13 | 6364 − 4(13)<sup>3</sup> = 6364 − 8788 = −2424 | −1065 | −306 |

Here, the constant is achieved after only two pairwise differences, thus the following result: 

$$
-306=a\cdot 3^{2}\cdot 2!=a\cdot 18
$$

Solving for *a*, which is −17, the polynomial's second term is −17*x*<sup>2</sup>.

Moving on to the next term, by subtracting out the second term:

|  |  |  |
|----|----|----|
| *x* | *y* | Δ*y* |
| 1 | 0 − (−17(1)<sup>2</sup>) = 0 + 17 = 17 |  |
| 4 | −147 − (−17(4)<sup>2</sup>) = −147 + 272 = 125 | 108 |
| 7 | −600 − (−17(7)<sup>2</sup>) = −600 + 833 = 233  | 108 |
| 10 | −1359 − (−17(10)<sup>2</sup>) = −1359 + 1700 = 341  | 108 |
| 13 | −2424 − (−17(13)<sup>2</sup>) = −2424 + 2873 = 449  | 108 |

Thus the constant is achieved after only one pairwise difference: 

$$
108=a\cdot 3^{1}\cdot 1!=a\cdot 3
$$

It can be found that *a* = 36 and thus the third term of the polynomial is **36*x***. Subtracting out the third term:

|  |  |
|----|----|
| *x* | *y* |
| 1 | 17 − 36(1) = 17 − 36 = −19 |
| 4 | 125 − 36(4) = 125 − 144 = −19 |
| 7 | 233 − 36(7) = 233 − 252 = −19 |
| 10 | 341 − 36(10) = 341 − 360 = −19 |
| 13 | 449 − 36(13) = 449 − 468 = −19 |

Without any pairwise differences, it is found that the 4th and final term of the polynomial is the constant −19. Thus, the lowest-degree polynomial intercepting all the points in the first table is found: 

$$
4x^{3}-17x^{2}+36x-19
$$

## Arbitrarily sized kernels

Using [linear algebra](https://en.wikipedia.org/wiki/Linear_algebra) one can construct finite difference approximations which utilize an arbitrary number of points to the left and a (possibly different) number of points to the right of the evaluation point, for any order derivative. This involves solving a linear system such that the [Taylor expansion](https://en.wikipedia.org/wiki/Taylor_expansion) of the sum of those points around the evaluation point best approximates the Taylor expansion of the desired derivative. Such formulas can be represented graphically on a hexagonal or diamond-shaped grid. This is useful for differentiating a function on a grid, where, as one approaches the edge of the grid, one must sample fewer and fewer points on one side. Finite difference approximations for non-standard (and even non-integer) stencils given an arbitrary stencil and a desired derivative order may be constructed.

### Properties

- For all positive k and n 

$$
\Delta _{kh}^{n}\left(f,x\right)=\sum \limits _{j_{1}=0}^{k-1}\sum \limits _{j_{2}=0}^{k-1}\cdots \sum \limits _{j_{n}=0}^{k-1}\Delta _{h}^{n}\left(f,x+j_{1}h+j_{2}h+\cdots +j_{n}h\right).
$$

- [Leibniz rule](https://en.wikipedia.org/wiki/Leibniz_rule_(generalized_product_rule)): 

$$
\Delta _{h}^{n}\left(fg,x\right)=\sum \limits _{k=0}^{n}{\binom {n}{k}}\Delta _{h}^{k}\left(f,x\right)\cdot \Delta _{h}^{n-k}\left(g,x+kh\right).
$$

## In differential equations

An important application of finite differences is in [numerical analysis](https://en.wikipedia.org/wiki/Numerical_analysis), especially in [numerical differential equations](https://en.wikipedia.org/wiki/Numerical_partial_differential_equations), which aim at the numerical solution of [ordinary](https://en.wikipedia.org/wiki/Ordinary_differential_equation) and [partial differential equations](https://en.wikipedia.org/wiki/Partial_differential_equation). The idea is to replace the derivatives appearing in the differential equation by finite differences that approximate them. The resulting methods are called [finite difference methods](https://en.wikipedia.org/wiki/Finite_difference_method).

Common applications of the finite difference method are in computational science and engineering disciplines, such as [thermal engineering](https://en.wikipedia.org/wiki/Thermal_engineering), [fluid mechanics](https://en.wikipedia.org/wiki/Fluid_mechanics), etc.

## Newton's series

The **[Newton series](https://en.wikipedia.org/wiki/Newton_polynomial)** consists of the terms of the **Newton forward difference equation**, named after [Isaac Newton](https://en.wikipedia.org/wiki/Isaac_Newton); in essence, it is the **Gregory–Newton interpolation formula** (named after [Isaac Newton](https://en.wikipedia.org/wiki/Isaac_Newton) and [James Gregory](https://en.wikipedia.org/wiki/James_Gregory_(mathematician) "James Gregory (mathematician)")), first published in his *[Principia Mathematica](https://en.wikipedia.org/wiki/Philosophi%C3%A6_Naturalis_Principia_Mathematica)* in 1687, namely the discrete analog of the continuous Taylor expansion,

$f(x)=\sum _{k=0}^{\infty }{\frac {\Delta ^{k}[f](a)}{k!}}\,(x-a)_{k}=\sum _{k=0}^{\infty }{\binom {x-a}{k}}\,\Delta ^{k}[f](a),$

which holds for any [polynomial](https://en.wikipedia.org/wiki/Polynomial) function f and for many (but not all) [analytic functions](https://en.wikipedia.org/wiki/Analytic_function). (It does not hold when f is [exponential type](https://en.wikipedia.org/wiki/Exponential_type) $\pi$. This is easily seen, as the sine function vanishes at integer multiples of $\pi$; the corresponding Newton series is identically zero, as all finite differences are zero in this case. Yet clearly, the sine function is not zero.) Here, the expression 

$$
{\binom {x}{k}}={\frac {(x)_{k}}{k!}}
$$

 is the [binomial coefficient](https://en.wikipedia.org/wiki/Binomial_coefficient), and 

$$
(x)_{k}=x(x-1)(x-2)\cdots (x-k+1)
$$

 is the "[falling factorial](https://en.wikipedia.org/wiki/Falling_factorial)" or "lower factorial", while the [empty product](https://en.wikipedia.org/wiki/Empty_product) (*x*)<sub>0</sub> is defined to be 1. In this particular case, there is an assumption of unit steps for the changes in the values of *x*, *h* = 1 of the generalization below.

Note the formal correspondence of this result to [Taylor's theorem](https://en.wikipedia.org/wiki/Taylor%27s_theorem). Historically, this, as well as the [Chu–Vandermonde identity](https://en.wikipedia.org/wiki/Chu%E2%80%93Vandermonde_identity), 

$$
(x+y)_{n}=\sum _{k=0}^{n}{\binom {n}{k}}(x)_{n-k}\,(y)_{k},
$$

 (following from it, and corresponding to the [binomial theorem](https://en.wikipedia.org/wiki/Binomial_theorem)), are included in the observations that matured to the system of [umbral calculus](https://en.wikipedia.org/wiki/Umbral_calculus).

Newton series expansions can be superior to Taylor series expansions when applied to discrete quantities like quantum spins (see [Holstein–Primakoff transformation](https://en.wikipedia.org/wiki/Holstein%E2%80%93Primakoff_transformation)), [bosonic operator functions](https://en.wikipedia.org/wiki/Normal_order#Bosonic_operator_functions) or discrete counting statistics.

To illustrate how one may use Newton's formula in actual practice, consider the first few terms of doubling the [Fibonacci sequence](https://en.wikipedia.org/wiki/Fibonacci_sequence) *f* = 2, 2, 4, ... One can find a [polynomial](https://en.wikipedia.org/wiki/Polynomial) that reproduces these values, by first computing a difference table, and then substituting the differences that correspond to *x*<sub>0</sub> (underlined) into the formula as follows, 

$$
{\begin{matrix}{\begin{array}{|c||c|c|c|}\hline x&f=\Delta ^{0}&\Delta ^{1}&\Delta ^{2}\\\hline 1&{\underline {2}}&&\\&&{\underline {0}}&\\2&2&&{\underline {2}}\\&&2&\\3&4&&\\\hline \end{array}}&\quad {\begin{aligned}f(x)&=\Delta ^{0}\cdot 1+\Delta ^{1}\cdot {\dfrac {(x-x_{0})_{1}}{1!}}+\Delta ^{2}\cdot {\dfrac {(x-x_{0})_{2}}{2!}}\quad (x_{0}=1)\\\\&=2\cdot 1+0\cdot {\dfrac {x-1}{1}}+2\cdot {\dfrac {(x-1)(x-2)}{2}}\\\\&=2+(x-1)(x-2)\\\end{aligned}}\end{matrix}}
$$

For the case of nonuniform steps in the values of x, Newton computes the [divided differences](https://en.wikipedia.org/wiki/Divided_differences), 

$$
\Delta _{j,0}=y_{j},\qquad \Delta _{j,k}={\frac {\Delta _{j+1,k-1}-\Delta _{j,k-1}}{x_{j+k}-x_{j}}}\quad \ni \quad \left\{k>0,\;j\leq \max \left(j\right)-k\right\},\qquad \Delta 0_{k}=\Delta _{0,k}
$$

 the series of products, 

$$
{P_{0}}=1,\quad \quad P_{k+1}=P_{k}\cdot \left(\xi -x_{k}\right),
$$

 and the resulting polynomial is the [scalar product](https://en.wikipedia.org/wiki/Scalar_product), 

$$
f(\xi )=\Delta 0\cdot P\left(\xi \right).
$$

In analysis with [p-adic numbers](https://en.wikipedia.org/wiki/P-adic_number), [Mahler's theorem](https://en.wikipedia.org/wiki/Mahler%27s_theorem) states that the assumption that f is a polynomial function can be weakened all the way to the assumption that f is merely continuous.

[Carlson's theorem](https://en.wikipedia.org/wiki/Carlson%27s_theorem) provides necessary and sufficient conditions for a Newton series to be unique, if it exists. However, a Newton series does not, in general, exist.

The Newton series, together with the [Stirling series](https://en.wikipedia.org/wiki/Stirling_series) and the [Selberg series](https://en.wikipedia.org/wiki/Selberg_class), is a special case of the general [difference series](https://en.wikipedia.org/wiki/Difference_series), all of which are defined in terms of suitably scaled forward differences.

In a compressed and slightly more general form and equidistant nodes the formula reads 

$$
f(x)=\sum _{k=0}{\binom {\frac {x-a}{h}}{k}}\sum _{j=0}^{k}(-1)^{k-j}{\binom {k}{j}}f(a+jh).
$$

## Calculus of finite differences

The forward difference can be considered as an [operator](https://en.wikipedia.org/wiki/Operator_(mathematics) "Operator (mathematics)"), called the [difference operator](https://en.wikipedia.org/wiki/Difference_operator), which maps the function f to Δ<sub>*h*</sub>\[*f*\]. This operator amounts to 

$$
\Delta _{h}=\operatorname {T} _{h}-\operatorname {I} ,
$$

 where T<sub>*h*</sub> is the [shift operator](https://en.wikipedia.org/wiki/Shift_operator) with step h, defined by T<sub>*h*</sub>\[*f*\](*x*) = *f*(*x* + *h*), and I is the [identity operator](https://en.wikipedia.org/wiki/Identity_operator).

The finite difference of higher orders can be defined in recursive manner as Δ<sup>*n*</sup>  
<sub>*h*</sub> ≡ Δ<sub>*h*</sub>(Δ<sup>*n* − 1</sup>  
<sub>*h*</sub>). Another equivalent definition is Δ<sup>*n*</sup>  
<sub>*h*</sub> ≡ \[T<sub>*h*</sub> − I\]<sup>*n*</sup>.

The difference operator Δ<sub>*h*</sub> is a [linear operator](https://en.wikipedia.org/wiki/Linear_operator), as such it satisfies Δ<sub>*h*</sub>\[*α f* + *β g*\](*x*) = *α* Δ<sub>*h*</sub>\[*f*\](*x*) + *β* Δ<sub>*h*</sub>\[*g*\](*x*).

It also satisfies a special [Leibniz rule](https://en.wikipedia.org/wiki/Leibniz_rule_(generalized_product_rule)):

$\operatorname {\Delta } _{h}{\bigl (}f(x)g(x){\bigr )}={\bigl (}\operatorname {\Delta } _{h}f(x){\bigr )}g(x+h)+f(x){\bigl (}\operatorname {\Delta } _{h}g(x){\bigr )}~.$

Similar Leibniz rules hold for the backward and central differences.

Formally applying the [[Taylor Series]] with respect to h, yields the operator equation 

$$
\operatorname {\Delta } _{h}=h\operatorname {D} +{\frac {1}{2!}}h^{2}\operatorname {D} ^{2}+{\frac {1}{3!}}h^{3}\operatorname {D} ^{3}+\cdots =e^{h\operatorname {D} }-\operatorname {I} ,
$$

 where D denotes the conventional, continuous derivative operator, mapping f to its derivative *f*′. The expansion is valid when both sides act on [analytic functions](https://en.wikipedia.org/wiki/Analytic_function), for sufficiently small h; in the special case that the series of derivatives terminates (when the function operated on is a finite [polynomial](https://en.wikipedia.org/wiki/Polynomial)) the expression is exact, for *all* finite stepsizes,  h . Thus  T<sub>*h*</sub> = *e*<sup>*h* D</sup>, and formally inverting the exponential yields 

$$
h\operatorname {D} =\ln(1+\Delta _{h})=\Delta _{h}-{\tfrac {1}{2}}\,\Delta _{h}^{2}+{\tfrac {1}{3}}\,\Delta _{h}^{3}-\cdots ~.
$$

 This formula holds in the sense that both operators give the same result when applied to a polynomial.

Even for analytic functions, the series on the right is not guaranteed to converge; it may be an [asymptotic series](https://en.wikipedia.org/wiki/Asymptotic_series). However, it can be used to obtain more accurate approximations for the derivative. For instance, retaining the first two terms of the series yields the second-order approximation to *f* ′(*x*) mentioned at the end of the section *[§ Higher-order differences](#Higher-order_differences)*.

The analogous formulas for the backward and central difference operators are 

$$
h\operatorname {D} =-\ln(1-\nabla _{h})\quad {\text{ and }}\quad h\operatorname {D} =2\operatorname {arsinh} \left({\tfrac {1}{2}}\,\delta _{h}\right)~.
$$

The calculus of finite differences is related to the [umbral calculus](https://en.wikipedia.org/wiki/Umbral_calculus) of combinatorics. This remarkably systematic correspondence is due to the identity of the [commutators](https://en.wikipedia.org/wiki/Commutators) of the umbral quantities to their continuum analogs (*h* → 0 limits),

$\left[{\frac {\Delta _{h}}{h}},x\,\operatorname {T} _{h}^{-1}\right]=[\operatorname {D} ,x]=I.$

A large number of formal differential relations of standard calculus involving functions *f*(*x*) thus *systematically map to umbral finite-difference analogs* involving *f*( *x* T<sup>−1</sup>  
<sub>*h*</sub> ).

For instance, the umbral analog of a monomial x<sup>n</sup> is a generalization of the above falling factorial ([Pochhammer k-symbol](https://en.wikipedia.org/wiki/Pochhammer_k-symbol)), 

$$
(x)_{n}=\left(x\operatorname {T} _{h}^{-1}\right)^{n}=x\left(x-h\right)\left(x-2h\right)\cdots {\bigl (}x-\left(n-1\right)h{\bigr )},
$$

 so that 

$$
{\frac {\Delta _{h}}{h}}(x)_{n}=n(x)_{n-1},
$$

 hence the above Newton interpolation formula (by matching coefficients in the expansion of an arbitrary function *f*(*x*) in such symbols), and so on.

For example, the umbral sine is 

$$
\sin \left(x\operatorname {T} _{h}^{-1}\right)=x-{\frac {(x)_{3}}{3!}}+{\frac {(x)_{5}}{5!}}-{\frac {(x)_{7}}{7!}}+\cdots
$$

As in the [continuum limit](https://en.wikipedia.org/wiki/Continuum_limit), the [eigenfunction](https://en.wikipedia.org/wiki/Eigenfunction) of Δ<sub>*h*</sub>/*h* also happens to be an exponential,

${\frac {\Delta _{h}}{h}}(1+\lambda h)^{\frac {x}{h}}={\frac {\Delta _{h}}{h}}e^{\ln(1+\lambda h){\frac {x}{h}}}=\lambda e^{\ln(1+\lambda h){\frac {x}{h}}},$

and hence *Fourier sums of continuum functions are readily, faithfully mapped to umbral Fourier sums*, i.e., involving the same Fourier coefficients multiplying these umbral basis exponentials. This umbral exponential thus amounts to the exponential [generating function](https://en.wikipedia.org/wiki/Generating_function) of the [Pochhammer symbols](https://en.wikipedia.org/wiki/Pochhammer_symbol).

Thus, for instance, the [Dirac delta function](https://en.wikipedia.org/wiki/Dirac_delta_function) maps to its umbral correspondent, the [cardinal sine function](https://en.wikipedia.org/wiki/Sinc_function) 

$$
\delta (x)\mapsto {\frac {\sin \left[{\frac {\pi }{2}}\left(1+{\frac {x}{h}}\right)\right]}{\pi (x+h)}},
$$

 and so forth. [Difference equations](https://en.wikipedia.org/wiki/Difference_equation) can often be solved with techniques very similar to those for solving [differential equations](https://en.wikipedia.org/wiki/Differential_equation).

The inverse operator of the forward difference operator, so then the umbral integral, is the [indefinite sum](https://en.wikipedia.org/wiki/Indefinite_sum) or antidifference operator.

### Rules for calculus of finite difference operators

Analogous to [rules for finding the derivative](https://en.wikipedia.org/wiki/Differentiation_rules), we have:

- **Constant rule**: If c is a [constant](https://en.wikipedia.org/wiki/Constant_(mathematics) "Constant (mathematics)"), then 

$$
\Delta c=0
$$

- **[Linearity](https://en.wikipedia.org/wiki/Linearity_of_differentiation)**: If a and b are [constants](https://en.wikipedia.org/wiki/Constant_(mathematics) "Constant (mathematics)"), 

$$
\Delta (af+bg)=a\Delta f+b\Delta g
$$

All of the above rules apply equally well to any difference operator as to Δ, including δ and ∇.

- **[Product rule](https://en.wikipedia.org/wiki/Product_rule)**: 

$$
{\begin{aligned}\Delta (fg)&=f\,\Delta g+g\Delta f+\Delta f\Delta g\\[4pt]\nabla (fg)&=f\,\nabla g+g\nabla f-\nabla f\nabla g\end{aligned}}
$$

- **[Quotient rule](https://en.wikipedia.org/wiki/Quotient_rule)**: 

$$
\nabla \left({\frac {f}{g}}\right)=\left.\left(\det {\begin{bmatrix}\nabla f&\nabla g\\f&g\end{bmatrix}}\right)\right/\left(g\cdot \det {\begin{bmatrix}g&\nabla g\\1&1\end{bmatrix}}\right)
$$

 or 

$$
\nabla \left({\frac {f}{g}}\right)={\frac {g\,\nabla f-f\,\nabla g}{g\cdot (g-\nabla g)}}
$$

- **[Summation rules](https://en.wikipedia.org/wiki/Fundamental_theorem_of_calculus)**: 

$$
{\begin{aligned}\sum _{n=a}^{b}\Delta f(n)&=f(b+1)-f(a)\\\sum _{n=a}^{b}\nabla f(n)&=f(b)-f(a-1)\end{aligned}}
$$

See references.

## Generalizations

- A **generalized finite difference** is usually defined as 

$$
\Delta _{h}^{\mu }[f](x)=\sum _{k=0}^{N}\mu _{k}f(x+kh),
$$

 where *μ* = (*μ*<sub>0</sub>, …, *μ<sub>N</sub>*) is its coefficient vector. An **infinite difference** is a further generalization, where the finite sum above is replaced by an [infinite series](https://en.wikipedia.org/wiki/Series_(mathematics) "Series (mathematics)"). Another way of generalization is making coefficients *μ<sub>k</sub>* depend on point x: *μ<sub>k</sub>* = *μ<sub>k</sub>*(*x*), thus considering **weighted finite difference**. Also one may make the step h depend on point x: *h* = *h*(*x*). Such generalizations are useful for constructing different [modulus of continuity](https://en.wikipedia.org/wiki/Modulus_of_continuity).
- The generalized difference can be seen as the polynomial rings *R*\[*T<sub>h</sub>*\]. It leads to difference algebras.
- Difference operator generalizes to [Möbius inversion](https://en.wikipedia.org/wiki/M%C3%B6bius_inversion) over a [partially ordered set](https://en.wikipedia.org/wiki/Partially_ordered_set).
- As a convolution operator: Via the formalism of [incidence algebras](https://en.wikipedia.org/wiki/Incidence_algebra), difference operators and other Möbius inversion can be represented by [convolution](https://en.wikipedia.org/wiki/Convolution) with a function on the poset, called the [Möbius function](https://en.wikipedia.org/wiki/M%C3%B6bius_function_(combinatorics)) μ; for the difference operator, μ is the sequence (1, −1, 0, 0, 0, …).

## Multivariate finite differences

Finite differences can be considered in more than one variable. They are analogous to [partial derivatives](https://en.wikipedia.org/wiki/Partial_derivative) in several variables.

Some partial derivative approximations are: 

$$
{\begin{aligned}f_{x}(x,y)&\approx {\frac {f(x+h,y)-f(x-h,y)}{2h}}\\f_{y}(x,y)&\approx {\frac {f(x,y+k)-f(x,y-k)}{2k}}\\f_{xx}(x,y)&\approx {\frac {f(x+h,y)-2f(x,y)+f(x-h,y)}{h^{2}}}\\f_{yy}(x,y)&\approx {\frac {f(x,y+k)-2f(x,y)+f(x,y-k)}{k^{2}}}\\f_{xy}(x,y)&\approx {\frac {f(x+h,y+k)-f(x+h,y-k)-f(x-h,y+k)+f(x-h,y-k)}{4hk}}.\end{aligned}}
$$

Alternatively, for applications in which the computation of f is the most costly step, and both first and second derivatives must be computed, a more efficient formula for the last case is 

$$
f_{xy}(x,y)\approx {\frac {f(x+h,y+k)-f(x+h,y)-f(x,y+k)+2f(x,y)-f(x-h,y)-f(x,y-k)+f(x-h,y-k)}{2hk}},
$$

 since the only values to compute that are not already needed for the previous four equations are *f*(*x* + *h*, *y* + *k*) and *f*(*x* − *h*, *y* − *k*).

For functions with $N$ variables $f(x_{1},x_{2},\ldots ,x_{N})$, evaluating the full $m$-th order derivative tensor via finite difference requires $O(N^{m})$ calls of the function $f$ (where we have used the [Big O notation](https://en.wikipedia.org/wiki/Big_O_notation) to denote the asymptotic scaling behavior), or $O(N^{m-m'})$ calls of the $m'$-th order derivative of the function $f$ (where $m'<m$). However, for many classes of functions, the $m$-th order derivative tensor is sparse, or its off-diagonal blocks may have low rank. In these cases, algorithms may exist that can numerically estimate the $m$-th order derivative tensor using less than $O(N^{m-m'})$ calls of the $m'$-th order derivative, for example when $m=2$ and $m'=1$; in the latter case it is possible to estimate the [[Hessian Matrix]] using only $O(1)$ [gradients](https://en.wikipedia.org/wiki/Gradient), instead of $O(N)$ gradients as would be required by the conventional finite difference algorithm.

## See also

- [Discrete calculus](https://en.wikipedia.org/wiki/Discrete_calculus)
- [Divided differences](https://en.wikipedia.org/wiki/Divided_differences)
- [Finite-difference time-domain method](https://en.wikipedia.org/wiki/Finite-difference_time-domain_method) (FDTD)
- [Finite volume method](https://en.wikipedia.org/wiki/Finite_volume_method)
- [FTCS scheme](https://en.wikipedia.org/wiki/FTCS_scheme)
- [Gilbreath's conjecture](https://en.wikipedia.org/wiki/Gilbreath%27s_conjecture)
- [Sheffer sequence](https://en.wikipedia.org/wiki/Sheffer_sequence)
- [Summation by parts](https://en.wikipedia.org/wiki/Summation_by_parts)
- [Time scale calculus](https://en.wikipedia.org/wiki/Time_scale_calculus)
- [Upwind differencing scheme for convection](https://en.wikipedia.org/wiki/Upwind_differencing_scheme_for_convection)

## References

1.  ^    Paul Wilmott; Sam Howison; Jeff Dewynne (1995). [The Mathematics of Financial Derivatives: A Student Introduction](https://archive.org/details/mathematicsoffin00wilm/page/137). Cambridge University Press. p. [137](https://archive.org/details/mathematicsoffin00wilm/page/137). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-49789-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-49789-3).
2.  ^    [Peter Olver](https://en.wikipedia.org/wiki/Peter_J._Olver) (2013). *Introduction to Partial Differential Equations*. Springer Science & Business Media. p. 182. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-319-02099-0](https://en.wikipedia.org/wiki/Special:BookSources/978-3-319-02099-0).
3.  ^    M Hanif Chaudhry (2007). *Open-Channel Flow*. Springer. p. 369. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-68648-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-68648-6).
4.  Jordán, op. cit., p. 1 and Milne-Thomson, p. xxi. Milne-Thomson, Louis Melville (2000): *The Calculus of Finite Differences* (Chelsea Pub Co, 2000) [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0821821077](https://en.wikipedia.org/wiki/Special:BookSources/978-0821821077)
5.  Wang, Bo; Luo, Shaohang; Wang, Zikuan; Liu, Wenjian (2025). "O1NumHess: A fast and accurate seminumerical Hessian algorithm using only *O* (1) gradients". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2508.07544](https://arxiv.org/abs/2508.07544) \[[physics.chem-ph](https://arxiv.org/archive/physics.chem-ph)\].
6.  ["Finite differences of polynomials"](https://divisbyzero.com/2018/02/13/finite-differences-of-polynomials/). *divisbyzero.com*. February 13, 2018.
7.  Fraser, Duncan C. (January 1, 1909). ["On the Graphic Delineation of Interpolation Formulæ"](https://archive.org/stream/journal43instuoft#page/236/mode/2up). *Journal of the Institute of Actuaries*. **43** (2): 235–241. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1017/S002026810002494X](https://doi.org/10.1017%2FS002026810002494X). Retrieved April 17, 2017.
8.  [notes](https://commons.wikimedia.org/wiki/File:FDnotes.djvu)
9.  [Finite Difference Coefficients Calculator](http://web.media.mit.edu/~crtaylor/calculator.html)
10. [Burkard Polster](https://en.wikipedia.org/wiki/Burkard_Polster)/Mathologer (2021). [" Why don't they teach Newton's calculus of 'What comes next?' " on YouTube](https://www.youtube.com/watch?v=4AuV93LOPcE&t=964s)
11. Newton, Isaac, (1687). [Principia, Book III, Lemma V, Case 1](https://archive.org/details/bub_gb_KaAIAAAAIAAJ/page/n459)
12. Iaroslav V. Blagouchine (2018). ["Three notes on Ser's and Hasse's representations for the zeta-functions"](http://math.colgate.edu/~integers/sjs3/sjs3.pdf) (PDF). *Integers (Electronic Journal of Combinatorial Number Theory)*. **18A**: 1–45. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1606.02044](https://arxiv.org/abs/1606.02044). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.5281/zenodo.10581385](https://doi.org/10.5281%2Fzenodo.10581385).
13. König, Jürgen; Hucht, Fred (2021). ["Newton series expansion of bosonic operator functions"](https://doi.org/10.21468%2FSciPostPhys.10.1.007). *SciPost Physics*. **10** (1): 007. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2008.11139](https://arxiv.org/abs/2008.11139). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2021ScPP...10....7K](https://ui.adsabs.harvard.edu/abs/2021ScPP...10....7K). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.21468/SciPostPhys.10.1.007](https://doi.org/10.21468%2FSciPostPhys.10.1.007). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [221293056](https://api.semanticscholar.org/CorpusID:221293056).
14. [Richtmeyer, D.](https://en.wikipedia.org/wiki/Robert_D._Richtmyer) and Morton, K.W., (1967). *Difference Methods for Initial Value Problems*, 2nd ed., Wiley, New York.
15. [Boole, George](https://en.wikipedia.org/wiki/George_Boole) (1872). [A Treatise on the Calculus of Finite Differences](https://archive.org/details/cu31924031240934) (2nd ed.). Macmillan and Company – via [Internet Archive](https://en.wikipedia.org/wiki/Internet_Archive). Also, a Dover reprint edition, 1960.
16. Jordan, Charles (1965) \[1939\]. [Calculus of Finite Differences](https://books.google.com/books?id=3RfZOsDAyQsC&pg=PA1). Chelsea Publishing. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8284-0033-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8284-0033-6) – via Google books.
17. [Zachos, C.](https://en.wikipedia.org/wiki/Cosmas_Zachos) (2008). "Umbral deformations on discrete space-time". *International Journal of Modern Physics A*. **23** (13): 200–214. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[0710.2306](https://arxiv.org/abs/0710.2306). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2008IJMPA..23.2005Z](https://ui.adsabs.harvard.edu/abs/2008IJMPA..23.2005Z). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1142/S0217751X08040548](https://doi.org/10.1142%2FS0217751X08040548). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [16797959](https://api.semanticscholar.org/CorpusID:16797959).
18. Curtright, T. L.; Zachos, C. K. (2013). ["Umbral Vade Mecum"](https://doi.org/10.3389%2Ffphy.2013.00015). *Frontiers in Physics*. **1**: 15. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1304.0429](https://arxiv.org/abs/1304.0429). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2013FrP.....1...15C](https://ui.adsabs.harvard.edu/abs/2013FrP.....1...15C). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3389/fphy.2013.00015](https://doi.org/10.3389%2Ffphy.2013.00015). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [14106142](https://api.semanticscholar.org/CorpusID:14106142).
19. Levy, H.; Lessman, F. (1992). *Finite Difference Equations*. Dover. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-486-67260-3](https://en.wikipedia.org/wiki/Special:BookSources/0-486-67260-3).
20. Ames, W.F. (1977). *Numerical Methods for Partial Differential Equations*. New York, NY: Academic Press. Section 1.6. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-12-056760-1](https://en.wikipedia.org/wiki/Special:BookSources/0-12-056760-1).
21. [Hildebrand, F.B.](https://en.wikipedia.org/wiki/Francis_B._Hildebrand) (1968). *Finite-Difference Equations and Simulations*. Englewood Cliffs, NJ: Prentice-Hall. Section 2.2.
22. Flajolet, Philippe; [Sedgewick, Robert](https://en.wikipedia.org/wiki/Robert_Sedgewick_(computer_scientist) "Robert Sedgewick (computer scientist)") (1995). ["Mellin transforms and asymptotics: Finite differences and Rice's integrals"](http://algo.inria.fr/flajolet/Publications/FlSe95.pdf) (PDF). *Theoretical Computer Science*. **144** (1–2): 101–124. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/0304-3975(94)00281-M](https://doi.org/10.1016%2F0304-3975%2894%2900281-M).
23. Wang, Bo; Luo, Shaohang; Wang, Zikuan; Liu, Wenjian (2025). "O1NumHess: A fast and accurate seminumerical Hessian algorithm using only O(1) gradients". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2508.07544](https://arxiv.org/abs/2508.07544) \[[physics.chem-ph](https://arxiv.org/archive/physics.chem-ph)\].

- Richardson, C. H. (1954): *An Introduction to the Calculus of Finite Differences* (Van Nostrand (1954) [online copy](http://babel.hathitrust.org/cgi/pt?id=mdp.39015000982945;view=1up;seq=5)
- Mickens, R. E. (1991): *Difference Equations: Theory and Applications* (Chapman and Hall/CRC) [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0442001360](https://en.wikipedia.org/wiki/Special:BookSources/978-0442001360)

## External links

- ["Finite-difference calculus"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society), 2001 \[1994\]
- [Table of useful finite difference formula generated using Mathematica](http://reference.wolfram.com/mathematica/tutorial/NDSolvePDE.html#c:4)
- D. Gleich (2005), [Finite Calculus: A Tutorial for Solving Nasty Sums](https://web.archive.org/web/20090419132601/http://www.stanford.edu/~dgleich/publications/finite-calculus.pdf)
- [Discrete Second Derivative from Unevenly Spaced Points](http://mathformeremortals.wordpress.com/2013/01/12/a-numerical-second-derivative-from-three-points/)
