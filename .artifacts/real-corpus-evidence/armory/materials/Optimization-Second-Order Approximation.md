[[optimization.base]]

> Source: [[Taylor Series]]
> License: Wikipedia content is available under CC BY-SA 4.0.

![[media/6dc2705fff79c2cca9ccfe83fd8bdd3093fb0aba.png]]
As the degree of the Taylor polynomial rises, it approaches the correct function. This image shows sin <em>x</em> and its Taylor approximations by polynomials of degree <strong>1</strong>, <strong>3</strong>, <strong>5</strong>, <strong>7</strong>, <strong>9</strong>, <strong>11</strong>, and <strong>13</strong> at <em>x</em> = 0.

In [mathematical analysis](https://en.wikipedia.org/wiki/Mathematical_analysis), the **Taylor series** or **Taylor expansion** of a [function](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)") is an [infinite sum](https://en.wikipedia.org/wiki/Series_(mathematics) "Series (mathematics)") of terms that are expressed in terms of the function's [derivatives](https://en.wikipedia.org/wiki/Derivative) at a single point. For most common functions, the function and the sum of its Taylor series are equal near this point. Taylor series are named after [Brook Taylor](https://en.wikipedia.org/wiki/Brook_Taylor), who introduced them in 1715. A Taylor series is also called a **Maclaurin series** when 0 is the point where the derivatives are considered, after [Colin Maclaurin](https://en.wikipedia.org/wiki/Colin_Maclaurin), who made extensive use of this special case of Taylor series in the 18th century.

The [partial sum](https://en.wikipedia.org/wiki/Partial_sum) formed by the first *n* + 1 terms of a Taylor series is a [polynomial](https://en.wikipedia.org/wiki/Polynomial) of degree n that is called the nth **Taylor polynomial** of the function. Taylor polynomials are approximations of a function, which become generally more accurate as n increases. [Taylor's theorem](https://en.wikipedia.org/wiki/Taylor%27s_theorem) gives quantitative estimates on the error introduced by the use of such approximations. If the Taylor series of a function is [convergent](https://en.wikipedia.org/wiki/Convergence_(mathematics)), its sum is the [limit](https://en.wikipedia.org/wiki/Limit_of_a_sequence) of the [infinite sequence](https://en.wikipedia.org/wiki/Infinite_sequence) of the Taylor polynomials. A function may differ from the sum of its Taylor series, even if its Taylor series is convergent. A function is [analytic](https://en.wikipedia.org/wiki/Analytic_function) at a point x if it is equal to the sum of its Taylor series in some [open interval](https://en.wikipedia.org/wiki/Open_interval) (or [open disk](https://en.wikipedia.org/wiki/Disk_(mathematics) "Disk (mathematics)") in the [complex plane](https://en.wikipedia.org/wiki/Complex_plane)) containing x. This implies that the function is analytic at every point of the interval (or disk).

## Definition

The Taylor series of a [real](https://en.wikipedia.org/wiki/Real-valued_function) or [complex-valued function](https://en.wikipedia.org/wiki/Complex-valued_function) *f* (*x*), that is [infinitely differentiable](https://en.wikipedia.org/wiki/Infinitely_differentiable_function) at a [real](https://en.wikipedia.org/wiki/Real_number) or [complex number](https://en.wikipedia.org/wiki/Complex_number) *a*, is the [power series](https://en.wikipedia.org/wiki/Power_series) 

$$
f(a)+{\frac {f'(a)}{1!}}(x-a)+{\frac {f''(a)}{2!}}(x-a)^{2}+\cdots =\sum _{n=0}^{\infty }{\frac {f^{(n)}(a)}{n!}}(x-a)^{n}.
$$

 Here, *n*! denotes the [factorial](https://en.wikipedia.org/wiki/Factorial) of n. The function *f*<sup>(*n*)</sup>(*a*) denotes the nth [derivative](https://en.wikipedia.org/wiki/Derivative) of f evaluated at the point a. The derivative of order zero of f is defined to be f itself and (*x* − *a*)<sup>0</sup> and 0! [are both defined to be 1](https://en.wikipedia.org/wiki/Empty_product). This series can be written by using [sigma notation](https://en.wikipedia.org/wiki/Sigma_notation), as in the right side formula. With *a* = 0, the Maclaurin series takes the form: 

$$
f(0)+{\frac {f'(0)}{1!}}x+{\frac {f''(0)}{2!}}x^{2}+\cdots =\sum _{n=0}^{\infty }{\frac {f^{(n)}(0)}{n!}}x^{n}.
$$

## List of Maclaurin series of some common functions

Several important Maclaurin series expansions follow. All these expansions are valid for complex arguments x.

### Exponential function

![[media/8dd95dfaf4df1855cd98cc1aea085cf63494a6ed.gif]]
The [exponential function](https://en.wikipedia.org/wiki/Exponential_function) <em>e</em><sup><em>x</em></sup> (in blue), and the sum of the first <em>n</em> + 1 terms of its Taylor series at 0 (in red).

The [exponential function](https://en.wikipedia.org/wiki/Exponential_function) $e^{x}$ (with base [e](https://en.wikipedia.org/wiki/E_(mathematics))) has Maclaurin series

$$
e^{x}=\sum _{n=0}^{\infty }{\frac {x^{n}}{n!}}=1+x+{\frac {x^{2}}{2!}}+{\frac {x^{3}}{3!}}+\cdots .
$$

 It converges for all x.

The exponential [generating function](https://en.wikipedia.org/wiki/Generating_function) of the [Bell numbers](https://en.wikipedia.org/wiki/Bell_number) is the exponential function of the predecessor of the exponential function:

$$
\exp(\exp {x}-1)=\sum _{n=0}^{\infty }{\frac {B_{n}}{n!}}x^{n}
$$

### Natural logarithm

The [natural logarithm](https://en.wikipedia.org/wiki/Natural_logarithm) (with base [e](https://en.wikipedia.org/wiki/E_(mathematics))) has Maclaurin series

$$
{\begin{aligned}\ln(1-x)&=-\sum _{n=1}^{\infty }{\frac {x^{n}}{n}}=-x-{\frac {x^{2}}{2}}-{\frac {x^{3}}{3}}-\cdots ,\\\ln(1+x)&=\sum _{n=1}^{\infty }(-1)^{n+1}{\frac {x^{n}}{n}}=x-{\frac {x^{2}}{2}}+{\frac {x^{3}}{3}}-\cdots .\end{aligned}}
$$

The last series is known as [Mercator series](https://en.wikipedia.org/wiki/Mercator_series), named after [Nicholas Mercator](https://en.wikipedia.org/wiki/Nicholas_Mercator) since it was published in his 1668 treatise *Logarithmotechnia*. Both of these series converge for $|x|<1$. In addition, the series for ln(1 − *x*) converges for *x* = −1, and the series for ln(1 + *x*) converges for *x* = 1.

### Geometric series

The [geometric series](https://en.wikipedia.org/wiki/Geometric_series) and its derivatives have Maclaurin series

$$
{\begin{aligned}{\frac {1}{1-x}}&=\sum _{n=0}^{\infty }x^{n}\\{\frac {1}{(1-x)^{2}}}&=\sum _{n=1}^{\infty }nx^{n-1}\\{\frac {1}{(1-x)^{3}}}&=\sum _{n=2}^{\infty }{\frac {(n-1)n}{2}}x^{n-2}.\end{aligned}}
$$

All are convergent for $|x|<1$. These are special cases of the [binomial series](#Binomial_series) given in the next section.

### Binomial series

The [binomial series](https://en.wikipedia.org/wiki/Binomial_series) is the power series

$$
(1+x)^{\alpha }=\sum _{n=0}^{\infty }{\binom {\alpha }{n}}x^{n}
$$

whose coefficients are the generalized [binomial coefficients](https://en.wikipedia.org/wiki/Binomial_coefficient)

$$
{\binom {\alpha }{n}}=\prod _{k=1}^{n}{\frac {\alpha -k+1}{k}}={\frac {\alpha (\alpha -1)\cdots (\alpha -n+1)}{n!}}.
$$

(If *n* = 0, this product is an [empty product](https://en.wikipedia.org/wiki/Empty_product) and has value 1.) It converges for $|x|<1$ for any real or complex number α.

When *α* = −1, this is essentially the infinite geometric series mentioned in the previous section. The special cases *α* = 1/2 and *α* = −1/2 give the [square root](https://en.wikipedia.org/wiki/Square_root) function and its [inverse](https://en.wikipedia.org/wiki/Multiplicative_inverse):

$$
{\begin{aligned}(1+x)^{\frac {1}{2}}&=1+{\frac {1}{2}}x-{\frac {1}{8}}x^{2}+{\frac {1}{16}}x^{3}-{\frac {5}{128}}x^{4}+{\frac {7}{256}}x^{5}-\cdots &=\sum _{n=0}^{\infty }{\frac {(-1)^{n-1}(2n)!}{4^{n}(n!)^{2}(2n-1)}}x^{n},\\(1+x)^{-{\frac {1}{2}}}&=1-{\frac {1}{2}}x+{\frac {3}{8}}x^{2}-{\frac {5}{16}}x^{3}+{\frac {35}{128}}x^{4}-{\frac {63}{256}}x^{5}+\cdots &=\sum _{n=0}^{\infty }{\frac {(-1)^{n}(2n)!}{4^{n}(n!)^{2}}}x^{n}.\end{aligned}}
$$

When only the [linear term](https://en.wikipedia.org/wiki/Linear_approximation) is retained, this simplifies to the [binomial approximation](https://en.wikipedia.org/wiki/Binomial_approximation).

### Trigonometric functions

The usual [trigonometric functions](https://en.wikipedia.org/wiki/Trigonometric_function) and their inverses have the following Maclaurin series:

$$
{\begin{aligned}\sin x&=\sum _{n=0}^{\infty }{\frac {(-1)^{n}}{(2n+1)!}}x^{2n+1}&&=x-{\frac {x^{3}}{3!}}+{\frac {x^{5}}{5!}}-\cdots &&{\text{for all }}x\\[6pt]\cos x&=\sum _{n=0}^{\infty }{\frac {(-1)^{n}}{(2n)!}}x^{2n}&&=1-{\frac {x^{2}}{2!}}+{\frac {x^{4}}{4!}}-\cdots &&{\text{for all }}x\\[6pt]\tan x&=\sum _{n=1}^{\infty }{\frac {B_{2n}(-4)^{n}\left(1-4^{n}\right)}{(2n)!}}x^{2n-1}&&=x+{\frac {x^{3}}{3}}+{\frac {2x^{5}}{15}}+\cdots &&{\text{for }}|x|<{\frac {\pi }{2}}\\[6pt]\sec x&=\sum _{n=0}^{\infty }{\frac {(-1)^{n}E_{2n}}{(2n)!}}x^{2n}&&=1+{\frac {x^{2}}{2}}+{\frac {5x^{4}}{24}}+\cdots &&{\text{for }}|x|<{\frac {\pi }{2}}\\[6pt]\arcsin x&=\sum _{n=0}^{\infty }{\frac {(2n)!}{4^{n}(n!)^{2}(2n+1)}}x^{2n+1}&&=x+{\frac {x^{3}}{6}}+{\frac {3x^{5}}{40}}+\cdots &&{\text{for }}|x|\leq 1\\[6pt]\arccos x&={\frac {\pi }{2}}-\arcsin x&&={\frac {\pi }{2}}-x-{\frac {x^{3}}{6}}-{\frac {3x^{5}}{40}}-\cdots &&{\text{for }}|x|\leq 1\\[6pt]\arctan x&=\sum _{n=0}^{\infty }{\frac {(-1)^{n}}{2n+1}}x^{2n+1}&&=x-{\frac {x^{3}}{3}}+{\frac {x^{5}}{5}}-\cdots &&{\text{for }}|x|\leq 1,\ x\neq \pm i\end{aligned}}
$$

All angles are expressed in [radians](https://en.wikipedia.org/wiki/Radian). The numbers *B<sub>k</sub>* appearing in the expansions of tan *x* are the [Bernoulli numbers](https://en.wikipedia.org/wiki/Bernoulli_numbers). The *E*<sub>*k*</sub> in the expansion of sec *x* are [Euler numbers](https://en.wikipedia.org/wiki/Euler_number).

### Hyperbolic functions

The [hyperbolic functions](https://en.wikipedia.org/wiki/Hyperbolic_function) have Maclaurin series closely related to the series for the corresponding trigonometric functions:

$$
{\begin{aligned}\sinh x&=\sum _{n=0}^{\infty }{\frac {x^{2n+1}}{(2n+1)!}}&&=x+{\frac {x^{3}}{3!}}+{\frac {x^{5}}{5!}}+\cdots &&{\text{for all }}x\\[6pt]\cosh x&=\sum _{n=0}^{\infty }{\frac {x^{2n}}{(2n)!}}&&=1+{\frac {x^{2}}{2!}}+{\frac {x^{4}}{4!}}+\cdots &&{\text{for all }}x\\[6pt]\tanh x&=\sum _{n=1}^{\infty }{\frac {B_{2n}4^{n}\left(4^{n}-1\right)}{(2n)!}}x^{2n-1}&&=x-{\frac {x^{3}}{3}}+{\frac {2x^{5}}{15}}-{\frac {17x^{7}}{315}}+\cdots &&{\text{for }}|x|<{\frac {\pi }{2}}\\[6pt]\operatorname {arsinh} x&=\sum _{n=0}^{\infty }{\frac {(-1)^{n}(2n)!}{4^{n}(n!)^{2}(2n+1)}}x^{2n+1}&&=x-{\frac {x^{3}}{6}}+{\frac {3x^{5}}{40}}-\cdots &&{\text{for }}|x|\leq 1\\[6pt]\operatorname {artanh} x&=\sum _{n=0}^{\infty }{\frac {x^{2n+1}}{2n+1}}&&=x+{\frac {x^{3}}{3}}+{\frac {x^{5}}{5}}+\cdots &&{\text{for }}|x|\leq 1,\ x\neq \pm 1\end{aligned}}
$$

The numbers *B<sub>k</sub>* appearing in the series for tanh *x* are the [Bernoulli numbers](https://en.wikipedia.org/wiki/Bernoulli_numbers).

### Polylogarithmic functions

The [polylogarithms](https://en.wikipedia.org/wiki/Polylogarithm) have these defining identities:

$$
{\begin{aligned}{\text{Li}}_{2}(x)&=\sum _{n=1}^{\infty }{\frac {1}{n^{2}}}x^{n}\\{\text{Li}}_{3}(x)&=\sum _{n=1}^{\infty }{\frac {1}{n^{3}}}x^{n}\end{aligned}}
$$

The [Legendre chi functions](https://en.wikipedia.org/wiki/Legendre_chi_function) are defined as follows:

$$
{\begin{aligned}\chi _{2}(x)&=\sum _{n=0}^{\infty }{\frac {1}{(2n+1)^{2}}}x^{2n+1}\\\chi _{3}(x)&=\sum _{n=0}^{\infty }{\frac {1}{(2n+1)^{3}}}x^{2n+1}\end{aligned}}
$$

And the formulas presented below are called *[inverse tangent integrals](https://en.wikipedia.org/wiki/Inverse_tangent_integral)*:

$$
{\begin{aligned}{\text{Ti}}_{2}(x)&=\sum _{n=0}^{\infty }{\frac {(-1)^{n}}{(2n+1)^{2}}}x^{2n+1}\\{\text{Ti}}_{3}(x)&=\sum _{n=0}^{\infty }{\frac {(-1)^{n}}{(2n+1)^{3}}}x^{2n+1}\end{aligned}}
$$

In [statistical thermodynamics](https://en.wikipedia.org/wiki/Statistical_mechanics) these formulas are of great importance.

### Elliptic functions

The complete [elliptic integrals](https://en.wikipedia.org/wiki/Elliptic_integral) of first kind K and of second kind E can be defined as follows:

$$
{\begin{aligned}{\frac {2}{\pi }}K(x)&=\sum _{n=0}^{\infty }{\frac {[(2n)!]^{2}}{16^{n}(n!)^{4}}}x^{2n}\\{\frac {2}{\pi }}E(x)&=\sum _{n=0}^{\infty }{\frac {[(2n)!]^{2}}{(1-2n)16^{n}(n!)^{4}}}x^{2n}\end{aligned}}
$$

The [Jacobi theta functions](https://en.wikipedia.org/wiki/Theta_function) describe the world of the elliptic modular functions and they have these Taylor series:

$$
{\begin{aligned}\vartheta _{00}(x)&=1+2\sum _{n=1}^{\infty }x^{n^{2}}\\\vartheta _{01}(x)&=1+2\sum _{n=1}^{\infty }(-1)^{n}x^{n^{2}}\end{aligned}}
$$

The regular [partition number sequence](https://en.wikipedia.org/wiki/Partition_function_(number_theory) "Partition function (number theory)") P(n) has this generating function:

$$
\vartheta _{00}(x)^{-1/6}\vartheta _{01}(x)^{-2/3}{\biggl [}{\frac {\vartheta _{00}(x)^{4}-\vartheta _{01}(x)^{4}}{16\,x}}{\biggr ]}^{-1/24}=\sum _{n=0}^{\infty }P(n)x^{n}=\prod _{k=1}^{\infty }{\frac {1}{1-x^{k}}}
$$

The strict partition number sequence Q(n) has the generating function:

$$
\vartheta _{00}(x)^{1/6}\vartheta _{01}(x)^{-1/3}{\biggl [}{\frac {\vartheta _{00}(x)^{4}-\vartheta _{01}(x)^{4}}{16\,x}}{\biggr ]}^{1/24}=\sum _{n=0}^{\infty }Q(n)x^{n}=\prod _{k=1}^{\infty }{\frac {1}{1-x^{2k-1}}}
$$

## Calculation of Taylor series

Several methods exist for the calculation of the Taylor series of a large number of functions. One can attempt to use the definition of the Taylor series, though this often requires generalizing the form of the coefficients according to a readily apparent pattern. Alternatively, one can use manipulations such as substitution, multiplication or division, addition or subtraction of standard Taylor series to construct the Taylor series of a function, by virtue of the Taylor series being a power series. In some cases, one can also derive the Taylor series by repeatedly applying [integration by parts](https://en.wikipedia.org/wiki/Integration_by_parts). Particularly convenient is the use of [computer algebra systems](https://en.wikipedia.org/wiki/Computer_algebra_system) to calculate Taylor series.

### First example

In order to compute the 7th-degree Maclaurin polynomial for the function 

$$
f(x)=\ln(\cos x),\quad x\in {\bigl (}{-{\tfrac {\pi }{2}}},{\tfrac {\pi }{2}}{\bigr )},
$$

 one may first rewrite the function as 

$$
f(x)={\ln }{\bigl (}1+(\cos x-1){\bigr )},
$$

 the composition of two functions $x\mapsto \ln(1+x)$ and $x\mapsto \cos x-1.$ The Taylor series for the natural logarithm is (using [big O notation](https://en.wikipedia.org/wiki/Big_O_notation)) 

$$
\ln(1+x)=x-{\frac {x^{2}}{2}}+{\frac {x^{3}}{3}}+O{\left(x^{4}\right)}
$$

 and for the cosine function 

$$
\cos x-1=-{\frac {x^{2}}{2}}+{\frac {x^{4}}{24}}-{\frac {x^{6}}{720}}+O{\left(x^{8}\right)}.
$$

The first several terms from the second series can be substituted into each term of the first series. Because the first term in the second series has degree 2, three terms of the first series suffice to give a 7th-degree polynomial: 

$$
{\begin{aligned}f(x)&=\ln {\bigl (}1+(\cos x-1){\bigr )}\\&=(\cos x-1)-{\tfrac {1}{2}}(\cos x-1)^{2}+{\tfrac {1}{3}}(\cos x-1)^{3}+O{\left((\cos x-1)^{4}\right)}\\&=-{\frac {x^{2}}{2}}-{\frac {x^{4}}{12}}-{\frac {x^{6}}{45}}+O{\left(x^{8}\right)}.\end{aligned}}
$$

Since the cosine is an [even function](https://en.wikipedia.org/wiki/Even_function), the coefficients for all the odd powers are zero.

### Second example

Given that the Taylor series at 0 of the function $g(x)={\frac {e^{x}}{\cos x}}$. The Taylor series for the exponential function is 

$$
e^{x}=1+x+{\frac {x^{2}}{2!}}+{\frac {x^{3}}{3!}}+{\frac {x^{4}}{4!}}+\cdots ,
$$

 and the series for cosine is 

$$
\cos x=1-{\frac {x^{2}}{2!}}+{\frac {x^{4}}{4!}}-\cdots .
$$

Assume the series for their quotient is 

$$
{\frac {e^{x}}{\cos x}}=c_{0}+c_{1}x+c_{2}x^{2}+c_{3}x^{3}+c_{4}x^{4}+\cdots
$$

 Multiplying both sides by the denominator $\cos x$ and then expanding it as a series yields 

$$
{\begin{aligned}e^{x}&=\left(c_{0}+c_{1}x+c_{2}x^{2}+c_{3}x^{3}+c_{4}x^{4}+\cdots \right)\left(1-{\frac {x^{2}}{2!}}+{\frac {x^{4}}{4!}}-\cdots \right)\\[5mu]&=c_{0}+c_{1}x+\left(c_{2}-{\frac {c_{0}}{2}}\right)x^{2}+\left(c_{3}-{\frac {c_{1}}{2}}\right)x^{3}+\left(c_{4}-{\frac {c_{2}}{2}}+{\frac {c_{0}}{4!}}\right)x^{4}+\cdots \end{aligned}}
$$

Comparing the coefficients of $g(x)\cos x$ with the coefficients of $e^{x},$ 

$$
c_{0}=1,\ \ c_{1}=1,\ \ c_{2}-{\tfrac {1}{2}}c_{0}={\tfrac {1}{2}},\ \ c_{3}-{\tfrac {1}{2}}c_{1}={\tfrac {1}{6}},\ \ c_{4}-{\tfrac {1}{2}}c_{2}+{\tfrac {1}{24}}c_{0}={\tfrac {1}{24}},\ \ldots .
$$

The coefficients $c_{i}$ of the series for $g(x)$ can thus be computed one at a time, amounting to long division of the series for $e^{x}$ and $\cos x$: 

$$
{\frac {e^{x}}{\cos x}}=1+x+x^{2}+{\tfrac {2}{3}}x^{3}+{\tfrac {1}{2}}x^{4}+\cdots .
$$

### Third example

Here we employ a method called "indirect expansion" to expand the given function. This method uses the known Taylor expansion of the exponential function. In order to expand (1 + *x*)*e<sup>x</sup>* as a Taylor series in x, we use the known Taylor series of function *e*<sup>*x*</sup>:

$$
e^{x}=\sum _{n=0}^{\infty }{\frac {x^{n}}{n!}}=1+x+{\frac {x^{2}}{2!}}+{\frac {x^{3}}{3!}}+{\frac {x^{4}}{4!}}+\cdots .
$$

Thus,

$$
{\begin{aligned}(1+x)e^{x}&=e^{x}+xe^{x}=\sum _{n=0}^{\infty }{\frac {x^{n}}{n!}}+\sum _{n=0}^{\infty }{\frac {x^{n+1}}{n!}}=1+\sum _{n=1}^{\infty }{\frac {x^{n}}{n!}}+\sum _{n=0}^{\infty }{\frac {x^{n+1}}{n!}}\\&=1+\sum _{n=1}^{\infty }{\frac {x^{n}}{n!}}+\sum _{n=1}^{\infty }{\frac {x^{n}}{(n-1)!}}=1+\sum _{n=1}^{\infty }\left({\frac {1}{n!}}+{\frac {1}{(n-1)!}}\right)x^{n}\\&=1+\sum _{n=1}^{\infty }{\frac {n+1}{n!}}x^{n}\\&=\sum _{n=0}^{\infty }{\frac {n+1}{n!}}x^{n}.\end{aligned}}
$$

## Approximation error and convergence

### Taylor's theorem

![[media/38a85e80bc0999590a39cd453f80e19c272b0b42.png]]

![[media/dc7ecf69a196ed1192257f23b18533e8187e7632.png]]

Pictured is an accurate approximation of sin *x* around the point *x* = 0. The pink curve is a polynomial of degree seven 

$$
\sin {x}\approx x-{\frac {x^{3}}{3!}}+{\frac {x^{5}}{5!}}-{\frac {x^{7}}{7!}}.
$$

The error in this approximation is no more than \|*x*\|<sup>9</sup> / 9!. For a full cycle centered at the origin (−π \< *x* \< π), the error is less than 0.08215. In particular, for −1 \< *x* \< 1, the error is less than 0.000003.

In contrast, also shown is a picture of the natural logarithm function ln(1 + *x*) and some of its Taylor polynomials around *a* = 0. These approximations converge to the function only in the region −1 \< *x* ≤ 1. Outside of this region, the higher-degree Taylor polynomials are *worse* approximations for the function.

The *error* incurred in approximating a function by its nth-degree Taylor polynomial is called the [remainder](https://en.wikipedia.org/wiki/Residual_(numerical_analysis) "Residual (numerical analysis)") and is denoted by the function *R*<sub>*n*</sub>(*x*). [Taylor's theorem](https://en.wikipedia.org/wiki/Taylor%27s_theorem) can be used to obtain a bound on the [size of the remainder](https://en.wikipedia.org/wiki/Taylor%27s_theorem#Explicit_formulas_for_the_remainder).

In general, Taylor series need not be [convergent](https://en.wikipedia.org/wiki/Convergent_series) at all. In fact, the set of functions with a convergent Taylor series is a [meager set](https://en.wikipedia.org/wiki/Meager_set) in the [Fréchet space](https://en.wikipedia.org/wiki/Fr%C3%A9chet_space) of [smooth functions](https://en.wikipedia.org/wiki/Smooth_functions). Even if the Taylor series of a function f does converge, its limit need not be equal to the value of the function *f* (*x*). For example, the function 

$$
f(x)={\begin{cases}e^{-1/x^{2}}&{\text{if }}x\neq 0\\[3mu]0&{\text{if }}x=0\end{cases}}
$$

 is [infinitely differentiable](https://en.wikipedia.org/wiki/Infinitely_differentiable) at *x* = 0, and has all derivatives zero there. Consequently, the Taylor series of *f* (*x*) about *x* = 0 is identically zero. However, *f* (*x*) is not the zero function, so it does not equal its Taylor series around the origin. Thus, *f* (*x*) is an example of a [non-analytic smooth function](https://en.wikipedia.org/wiki/Non-analytic_smooth_function). This example shows that there are [infinitely differentiable functions](https://en.wikipedia.org/wiki/Infinitely_differentiable_function) *f* (*x*) in [real analysis](https://en.wikipedia.org/wiki/Real_analysis), whose Taylor series are *not* equal to *f* (*x*) even if they converge. By contrast, the [holomorphic functions](https://en.wikipedia.org/wiki/Holomorphic_function) studied in [complex analysis](https://en.wikipedia.org/wiki/Complex_analysis) always possess a convergent Taylor series, and even the Taylor series of a [meromorphic function](https://en.wikipedia.org/wiki/Meromorphic_function), which might have singularities, never converges to a value different from the function itself. The complex function *e*<sup>−1/*z*<sup>2</sup></sup>, however, does not approach 0 when z approaches 0 along the imaginary axis, so it is not [continuous](https://en.wikipedia.org/wiki/Continuous_function) in the complex plane and its Taylor series is undefined at 0.

Every sequence of real or complex numbers can appear more generally as [coefficients](https://en.wikipedia.org/wiki/Coefficient) in the Taylor series of an infinitely differentiable function defined on the real line, a consequence of [Borel's lemma](https://en.wikipedia.org/wiki/Borel%27s_lemma). As a result, the [radius of convergence](https://en.wikipedia.org/wiki/Radius_of_convergence) of a Taylor series can be zero. There are even infinitely differentiable functions defined on the real line whose Taylor series have a radius of convergence 0 everywhere.

A function cannot be written as a Taylor series centred at a [singularity](https://en.wikipedia.org/wiki/Singularity_(mathematics) "Singularity (mathematics)"). In these cases, the function can still be expressed as a series expansion by allowing negative powers of the variable x. Such a series is known as a [Laurent series](https://en.wikipedia.org/wiki/Laurent_series), which generalizes the Taylor series.

### Generalization

The generalization of the Taylor series does converge to the value of the function itself for any [bounded](https://en.wikipedia.org/wiki/Bounded_function) [continuous function](https://en.wikipedia.org/wiki/Continuous_function) on (0,∞), and this can be done by using the calculus of [[Finite Differences]]. Specifically, the following theorem, due to [Einar Hille](https://en.wikipedia.org/wiki/Einar_Hille), that for any *t* \> 0, 

$$
\lim _{h\to 0^{+}}\sum _{n=0}^{\infty }{\frac {t^{n}}{n!}}{\frac {\Delta _{h}^{n}f(a)}{h^{n}}}=f(a+t).
$$

 Here Δ<sup>*n*</sup>  
<sub>*h*</sub> is the nth finite difference operator with step size h. The series is precisely the Taylor series, except that divided differences appear in place of differentiation: the series is formally similar to the [Newton series](https://en.wikipedia.org/wiki/Newton_series). When the function f is analytic at a, the terms in the series converge to the terms of the Taylor series, and in this sense generalizes the usual Taylor series.

In general, for any infinite sequence *a*<sub>*i*</sub>, the following power series identity holds: 

$$
\sum _{n=0}^{\infty }{\frac {u^{n}}{n!}}\Delta ^{n}a_{i}=e^{-u}\sum _{j=0}^{\infty }{\frac {u^{j}}{j!}}a_{i+j}.
$$

 So in particular, 

$$
f(a+t)=\lim _{h\to 0^{+}}e^{-t/h}\sum _{j=0}^{\infty }f(a+jh){\frac {(t/h)^{j}}{j!}}.
$$

The series on the right is the [expected value](https://en.wikipedia.org/wiki/Expected_value) of *f* (*a* + *X*), where X is a [Poisson-distributed](https://en.wikipedia.org/wiki/Poisson_distribution) [random variable](https://en.wikipedia.org/wiki/Random_variable) that takes the value *jh* with probability *e*<sup>−*t*/*h*</sup>·(*t*/*h*)<sup>*j*</sup>/*j*!. Hence, 

$$
f(a+t)=\lim _{h\to 0^{+}}\int _{-\infty }^{\infty }f(a+x)dP_{t/h,h}(x).
$$

The [[Law of Large Numbers]] implies that the identity holds.

## Analytic functions

![[media/c5e65fc3b2395ce1d286ef8c43d38f8cb39c9179.png]]
The function <strong><em>e</em><sup>(−1/<em>x</em><sup>2</sup>)</sup></strong> is not analytic at <em>x</em> = 0: the Taylor series is identically 0, although the function is not.

If *f* (*x*) is given by a convergent power series in an open disk centred at b in the complex plane (or an interval in the real line), it is said to be [analytic](https://en.wikipedia.org/wiki/Analytic_function) in this region. Thus for x in this region, f is given by a convergent power series 

$$
f(x)=\sum _{n=0}^{\infty }a_{n}(x-b)^{n}.
$$

Differentiating by x the above formula n times, then setting *x* = *b* gives 

$$
{\frac {f^{(n)}(b)}{n!}}=a_{n},
$$

 and so the power series expansion agrees with the Taylor series. Thus, a function is analytic in an open disk centered at b if and only if its Taylor series converges to the value of the function at each point of the disk.

If *f* (*x*) is equal to the sum of its Taylor series for all x in the complex plane, it is called [entire](https://en.wikipedia.org/wiki/Entire_function). The polynomials, [exponential function](https://en.wikipedia.org/wiki/Exponential_function) *e*<sup>*x*</sup>, and the [trigonometric functions](https://en.wikipedia.org/wiki/Trigonometric_function) of sine and cosine, are examples of entire functions. Examples of functions that are not entire include the [square root](https://en.wikipedia.org/wiki/Square_root), the [logarithm](https://en.wikipedia.org/wiki/Logarithm), the [trigonometric function](https://en.wikipedia.org/wiki/Trigonometric_function) tangent, and its inverse, [arctan](https://en.wikipedia.org/wiki/Arctan). For these functions, the Taylor series do not [converge](https://en.wikipedia.org/wiki/Convergent_series) if x is far from b. That is, the Taylor series [diverges](https://en.wikipedia.org/wiki/Divergent_series) at x if the distance between x and b is larger than the [radius of convergence](https://en.wikipedia.org/wiki/Radius_of_convergence). The Taylor series can be used to calculate the value of an entire function at every point, provided the value of the function and all its derivatives are known at a single point.

Uses of the Taylor series for analytic functions include:

- The partial sums of the Taylor series (that is, **Taylor polynomial**) of the series can be used as approximations of the function. These approximations are good if sufficiently many terms are included.
- Differentiation and integration of power series can be performed term by term and are hence particularly easy.
- An [analytic function](https://en.wikipedia.org/wiki/Analytic_function) is uniquely extended to a [holomorphic function](https://en.wikipedia.org/wiki/Holomorphic_function) on an open disk in the [complex plane](https://en.wikipedia.org/wiki/Complex_number). This makes the machinery of [complex analysis](https://en.wikipedia.org/wiki/Complex_analysis) available.
- The (truncated) series can be used to compute function values numerically, often by recasting the polynomial into the [Chebyshev form](https://en.wikipedia.org/wiki/Chebyshev_form) and evaluating it with the [Clenshaw algorithm](https://en.wikipedia.org/wiki/Clenshaw_algorithm).
- Algebraic operations can be done readily on the power series representation; for instance, [Euler's formula](https://en.wikipedia.org/wiki/Euler%27s_formula) follows from Taylor series expansions for trigonometric and exponential functions. This result is of fundamental importance in such fields as [harmonic analysis](https://en.wikipedia.org/wiki/Harmonic_analysis).
- Approximations based on the first few terms of a Taylor series can render otherwise intractable problems solvable over a restricted domain. This idea underlies [perturbation theory](https://en.wikipedia.org/wiki/Perturbation_theory), which is widely used in physics. Other physics fields that require approximation using Taylor series are [simple pendulum](https://en.wikipedia.org/wiki/Simple_pendulum), and [geometric optics](https://en.wikipedia.org/wiki/Geometric_optics) using [paraxial approximation](https://en.wikipedia.org/wiki/Paraxial_approximation).

##  Taylor series in multiple variables

The Taylor series may also be generalized to functions of more than one variable with 

$$
{\begin{aligned}T(x_{1},\ldots ,x_{d})&=\sum _{n_{1}=0}^{\infty }\cdots \sum _{n_{d}=0}^{\infty }{\frac {(x_{1}-a_{1})^{n_{1}}\cdots (x_{d}-a_{d})^{n_{d}}}{n_{1}!\cdots n_{d}!}}\,\left({\frac {\partial ^{n_{1}+\cdots +n_{d}}f}{\partial x_{1}^{n_{1}}\cdots \partial x_{d}^{n_{d}}}}\right)(a_{1},\ldots ,a_{d})\\&=f(a_{1},\ldots ,a_{d})+\sum _{j=1}^{d}{\frac {\partial f(a_{1},\ldots ,a_{d})}{\partial x_{j}}}(x_{j}-a_{j})+{\frac {1}{2!}}\sum _{j=1}^{d}\sum _{k=1}^{d}{\frac {\partial ^{2}f(a_{1},\ldots ,a_{d})}{\partial x_{j}\partial x_{k}}}(x_{j}-a_{j})(x_{k}-a_{k})\\&\qquad \qquad +{\frac {1}{3!}}\sum _{j=1}^{d}\sum _{k=1}^{d}\sum _{l=1}^{d}{\frac {\partial ^{3}f(a_{1},\ldots ,a_{d})}{\partial x_{j}\partial x_{k}\partial x_{l}}}(x_{j}-a_{j})(x_{k}-a_{k})(x_{l}-a_{l})+\cdots ,\\&=\sum _{|\alpha |\geq 0}{\frac {(\mathbf {x} -\mathbf {a} )^{\alpha }}{\alpha !}}\left({\mathrm {\partial } ^{\alpha }}f\right)(\mathbf {a} ).\end{aligned}}
$$

 The last expression is the multivariate Taylor series in terms of [multi-index notation](https://en.wikipedia.org/wiki/Multi-index_notation) with a full analogy to the single variable case.

For example, for a function $f(x,y)$ that depends on two variables, x and y, the Taylor series to second order about the point (*a*, *b*) is 

$$
f(a,b)+(x-a)f_{x}(a,b)+(y-b)f_{y}(a,b)+{\frac {1}{2!}}{\Big (}(x-a)^{2}f_{xx}(a,b)+2(x-a)(y-b)f_{xy}(a,b)+(y-b)^{2}f_{yy}(a,b){\Big )}
$$

 where the subscripts denote the respective [partial derivatives](https://en.wikipedia.org/wiki/Partial_derivative).

### Second-order Taylor series in several variables

A second-order Taylor series expansion of a scalar-valued function of more than one variable can be written compactly as 

$$
T(\mathbf {x} )=f(\mathbf {a} )+(\mathbf {x} -\mathbf {a} )^{\mathsf {T}}Df(\mathbf {a} )+{\frac {1}{2!}}(\mathbf {x} -\mathbf {a} )^{\mathsf {T}}\left\{D^{2}f(\mathbf {a} )\right\}(\mathbf {x} -\mathbf {a} )+\cdots ,
$$

 where *D* *f* (**a**) is the [gradient](https://en.wikipedia.org/wiki/Gradient) of f evaluated at **x** = **a** and *D*<sup>2</sup> *f* (**a**) is the [[Hessian Matrix]].

### Example

![[media/01bab1d534c8f56bb2582d958ca1971a9016b2a0.png]]
Second-order Taylor series approximation (in orange) of a function <em>f</em> (<em>x</em>,<em>y</em>) = <em>e<sup>x</sup></em> ln(1 + <em>y</em>) around the origin.

In order to compute a second-order Taylor series expansion around the point (*a*, *b*) = (0, 0) of the function 

$$
f(x,y)=e^{x}\ln(1+y),
$$

 one first computes all the necessary partial derivatives:

$$
{\begin{aligned}f_{x}&=e^{x}\ln(1+y),&f_{y}&={\frac {e^{x}}{1+y}},\\f_{xx}&=e^{x}\ln(1+y),&f_{yy}&=-{\frac {e^{x}}{(1+y)^{2}}},\\f_{xy}&=f_{yx}={\frac {e^{x}}{1+y}}.\end{aligned}}
$$

Evaluating these derivatives at the origin gives the Taylor coefficients

$$
{\begin{aligned}f_{x}(0,0)&=0,&f_{y}(0,0)&=1,\\f_{xx}(0,0)&=0,&f_{yy}(0,0)&=-1,\\f_{xy}(0,0)&=1.\end{aligned}}
$$

Substituting these values in to the general formula 

$$
{\begin{aligned}T(x,y)&=f(a,b)+(x-a)f_{x}(a,b)+(y-b)f_{y}(a,b)\\&\qquad {}+{\frac {1}{2!}}\left((x-a)^{2}f_{xx}(a,b)+2(x-a)(y-b)f_{xy}(a,b)+(y-b)^{2}f_{yy}(a,b)\right)+\cdots \end{aligned}}
$$

produces

$$
{\begin{aligned}T(x,y)&=0+0(x-0)+1(y-0)+{\frac {1}{2}}{\big (}0(x-0)^{2}+2(x-0)(y-0)+(-1)(y-0)^{2}{\big )}+\cdots \\&=y+xy-{\tfrac {1}{2}}y^{2}+\cdots \end{aligned}}
$$

Since ln(1 + *y*) is analytic in \|*y*\| \< 1, we have

$$
e^{x}\ln(1+y)=y+xy-{\tfrac {1}{2}}y^{2}+\cdots ,\qquad |y|<1.
$$

## History

The [ancient Greek philosopher](https://en.wikipedia.org/wiki/Ancient_Greek_philosopher) [Zeno of Elea](https://en.wikipedia.org/wiki/Zeno_of_Elea) considered the problem of summing an infinite series to achieve a finite result, but rejected it as an impossibility; the result was [Zeno's paradox](https://en.wikipedia.org/wiki/Zeno%27s_paradox). Later, [Aristotle](https://en.wikipedia.org/wiki/Aristotle) proposed a philosophical resolution of the paradox, but the mathematical content was apparently unresolved until taken up by [Archimedes](https://en.wikipedia.org/wiki/Archimedes), as it had been prior to Aristotle by the Presocratic Atomist [Democritus](https://en.wikipedia.org/wiki/Democritus). It was through Archimedes's [method of exhaustion](https://en.wikipedia.org/wiki/Method_of_exhaustion) that an infinite number of progressive subdivisions could be performed to achieve a finite result. [Liu Hui](https://en.wikipedia.org/wiki/Liu_Hui) independently employed a similar method a few centuries later.

In the 14th century, the earliest examples of specific Taylor series (but not the general method) were given by the Indian mathematician [Madhava of Sangamagrama](https://en.wikipedia.org/wiki/Madhava_of_Sangamagrama). Though no record of his work survives, writings of his followers in the [Kerala school of astronomy and mathematics](https://en.wikipedia.org/wiki/Kerala_school_of_astronomy_and_mathematics) suggest that he found the Taylor series for the [trigonometric functions](https://en.wikipedia.org/wiki/Trigonometric_function) of [sine](https://en.wikipedia.org/wiki/Sine), [cosine](https://en.wikipedia.org/wiki/Cosine), and [arctangent](https://en.wikipedia.org/wiki/Arctangent); see [Madhava series](https://en.wikipedia.org/wiki/Madhava_series). During the following two centuries, his followers developed further series expansions and rational approximations.

In late 1670, [James Gregory](https://en.wikipedia.org/wiki/James_Gregory_(mathematician) "James Gregory (mathematician)") was shown in a letter from [John Collins](https://en.wikipedia.org/wiki/John_Collins_(mathematician) "John Collins (mathematician)") several Maclaurin series ($\sin x,$ $\cos x,$ $\arcsin x,$ and $x\cot x$) derived by [Isaac Newton](https://en.wikipedia.org/wiki/Isaac_Newton), and told that Newton had developed a general method for expanding functions in series. Newton had in fact used a cumbersome method involving long division of series and term-by-term integration, but Gregory did not know it and set out to discover a general method for himself. In early 1671 Gregory discovered something like the general Maclaurin series and sent a letter to Collins including series for $\arctan x,$ $\tan x,$ $\sec x,$ $\ln \sec x$ (the integral of $\tan$), $\ln \tan {\tfrac {1}{2}}{{\bigl (}{\tfrac {1}{2}}\pi +x{\bigr )}}$ (the [integral of sec](https://en.wikipedia.org/wiki/Integral_of_the_secant_function), the inverse [Gudermannian function](https://en.wikipedia.org/wiki/Gudermannian_function)), $\operatorname {arcsec} {\bigl (}{\sqrt {2}}e^{x}{\bigr )},$ and $2\arctan e^{x}-{\tfrac {1}{2}}\pi$ (the Gudermannian function). However, thinking that he had merely redeveloped a method by Newton, Gregory never described how he obtained these series, and it can only be inferred that he understood the general method by examining scratch work he had scribbled on the back of another letter from 1671.

In 1691–1692, Newton wrote down an explicit statement of the Taylor and Maclaurin series in an unpublished version of his work *De Quadratura Curvarum*. It was the earliest explicit formulation of the general Taylor series. However, this work by Newton was never completed and the relevant sections were omitted from the portions published in 1704 under the title *Tractatus de Quadratura Curvarum*.

It was not until 1715 that a general method for constructing these series for all functions for which they exist was finally published by [Brook Taylor](https://en.wikipedia.org/wiki/Brook_Taylor), after whom the series are now named.

The Maclaurin series was named after [Colin Maclaurin](https://en.wikipedia.org/wiki/Colin_Maclaurin), a Scottish mathematician, who published a special case of the Taylor result in the mid-18th century.

## See also

- ![[media/1a9c6ad1ccebbc090fc7cd1c94d2142489246997.png]][Mathematics portal](https://en.wikipedia.org/wiki/Portal:Mathematics)

- [Asymptotic expansion](https://en.wikipedia.org/wiki/Asymptotic_expansion)
- [Newton polynomial](https://en.wikipedia.org/wiki/Newton_polynomial)
- [Padé approximant](https://en.wikipedia.org/wiki/Pad%C3%A9_approximant) – best approximation by a rational function
- [Puiseux series](https://en.wikipedia.org/wiki/Puiseux_series) – power series with rational exponents
- [Approximation theory](https://en.wikipedia.org/wiki/Approximation_theory)
- [Function approximation](https://en.wikipedia.org/wiki/Function_approximation)

## Notes

1.  , p. [530](https://books.google.com/books?id=OrumDwAAQBAJ&pg=PA530).
2.  , See §8.9..
3.  , p. [69](https://books.google.com/books?id=MtU8uP7XMvoC&pg=PA69).
4.  ^   

    - , p. [252](https://books.google.com/books?id=nsHisqNlsuIC&pg=PA252)
    - , p. [15](https://books.google.com/books?id=MtU8uP7XMvoC&pg=PA15)

5.  .
6.  , p. [14](https://books.google.com/books?id=MtU8uP7XMvoC&pg=PA14).
7.  , p. [15](https://books.google.com/books?id=MtU8uP7XMvoC&pg=PA15).
8.  , p. [75](https://books.google.com/books?id=MtU8uP7XMvoC&pg=PA75), [81](https://books.google.com/books?id=MtU8uP7XMvoC&pg=PA81).
9.  , p. [75](https://books.google.com/books?id=MtU8uP7XMvoC&pg=PA75).
10. ^   , p. [85](https://books.google.com/books?id=MtU8uP7XMvoC&pg=PA85).
11. , p. 489.
12. , p. [43–44](http://books.google.com/books?id=DLfxd7StGw8C&pg=PA43).
13. , p. [750](http://books.google.com/books?id=eafiBQAAQBAJ&pg=PA750).
14. , p. [558](https://books.google.com/books?id=z6mNEQAAQBAJ&pg=PT558).
15. , p. 418, See Exercise 13.
16. , p. [708](https://books.google.com/books?id=w4T3DwAAQBAJ&pg=PA708).
17. - , p. 230–232
    - , pp. 300–327

18. , p. 230–232.
19. ^    , p. 231.
20. , p. [139](https://books.google.com/books?id=LIXBHcUrx-cC&pg=PA139).
21. , p. [102](http://books.google.com/books?id=5K9i2YwgTjYC&pg=PA102).
22. , p. [6](http://books.google.com/books?id=-rvSBQAAQBAJ&pg=PA6).
23. , p. [258](http://books.google.com/books?id=6wtw2c5Cj0QC&pg=PA258).
24. - , p. [187](http://books.google.com/books?id=sJbVsRYbeMoC&pg=PA187)
    - , p. [227](https://books.google.com/books?id=ZkF-EQAAQBAJ&pg=PA227)

25. - , See Eqq. 1.1.7 and 1.1.7′
    - , p. 59–63

26. , p. 33.
27. , p. [35](https://archive.org/details/mathematicalthou00klin/page/n437)–37.
28. , p. [202–203](https://archive.org/details/historyofmathema00boye/page/202).
29. .
30. , p. [417–442](https://books.google.com/books?id=AEe9DwAAQBAJ&pg=PA417).
31. - , pp. 168–174
    - 
    - 

32. - , p. [289](https://books.google.com/books?id=ilrlBwAAQBAJ&pg=PA289)
    - , p. 48

33. .
34. - , p. 21–23, see Prop. VII, Thm. 3, Cor. 2. See , pp. 329–332 for English translation, and  for re-translation.
    - 

35. , p. [748](http://books.google.com/books?id=eafiBQAAQBAJ&pg=PA748).

## References

- [Abramowitz, Milton](https://en.wikipedia.org/wiki/Milton_Abramowitz); [Stegun, Irene A.](https://en.wikipedia.org/wiki/Irene_Stegun) (1970). *[Handbook of Mathematical Functions with Formulas, Graphs, and Mathematical Tables](https://en.wikipedia.org/wiki/Abramowitz_and_Stegun)*. New York: [Dover Publications](https://en.wikipedia.org/wiki/Dover_Publications). Ninth printing.
- Banner, Adrian (2007). [The Calculus Lifesaver: All the Tools You Need to Excel at Calculus](https://books.google.com/books?id=OrumDwAAQBAJ). Princeton University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-691-13088-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-691-13088-0).
- Bilodeau, Gerald; Thie, Paul; Keough, G. E. (2010). *An Introduction to Analysis*. Jones & Bartlett Publisher. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-7637-7492-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-7637-7492-9).
- Boyer, C.; [Merzbach, U.](https://en.wikipedia.org/wiki/Uta_Merzbach) (1991). [A History of Mathematics](https://archive.org/details/historyofmathema00boye) (2nd ed.). John Wiley and Sons. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-09763-2](https://en.wikipedia.org/wiki/Special:BookSources/0-471-09763-2).
- Bressoud, David (2002). "Was Calculus Invented in India?". *The College Mathematics Journal*. **33** (1): 2–13. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/1558972](https://doi.org/10.2307%2F1558972). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [1558972](https://www.jstor.org/stable/1558972).
- Bruce, Ian (2007). ["Methodus Incrementorum Directa & Inversa]"](https://17centurymaths.com/contents/taylorscontents.html). *17centurymaths.com*.
- Campos, Luis Manuel Braga da Costa (2011). [Complex Analysis with Applications to Flows and Fields](https://books.google.com/books?id=z6mNEQAAQBAJ). CRC Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-040-17268-1](https://en.wikipedia.org/wiki/Special:BookSources/978-1-040-17268-1).
- Choudhary, B. (1992). [The Elements of Complex Analysis](https://books.google.com/books?id=5K9i2YwgTjYC). New Age International Limited. Note that this source is reprinted in 2003.
- Dani, S. G. (2012). "Ancient Indian Mathematics – A Conspectus". *Resonance*. **17** (3): 236–246. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s12045-012-0022-y](https://doi.org/10.1007%2Fs12045-012-0022-y). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [120553186](https://api.semanticscholar.org/CorpusID:120553186).
- Edwards, C. Henry (1994). [The Historical Development of the Calculus](https://books.google.com/books?id=ilrlBwAAQBAJ). Springer study edition. Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-94313-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-94313-8).
- Enns, Richard H.; McGuire, George C. (2000). [Nonlinear Physics with Maple for Scientists and Engineers](https://books.google.com/books?id=rxadEAAAQBAJ) (2nd ed.). John Wiley & Sons.
- Feigenbaum, L. (1985). "Brook Taylor and the method of increments". *Archive for History of Exact Sciences*. **34** (1–2): 1–140. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/bf00329903](https://doi.org/10.1007%2Fbf00329903). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [122105736](https://api.semanticscholar.org/CorpusID:122105736).
- [Feller, William](https://en.wikipedia.org/wiki/William_Feller) (2003) \[1971\]. *An introduction to probability theory and its applications*. Vol. 2 (3rd ed.). Wiley. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9789971512989](https://en.wikipedia.org/wiki/Special:BookSources/9789971512989). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [818811840](https://search.worldcat.org/oclc/818811840).
- Greenberg, Michael (1998). [Advanced Engineering Mathematics](https://archive.org/details/advancedengineer0000gree) (2nd ed.). Prentice Hall. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-13-321431-1](https://en.wikipedia.org/wiki/Special:BookSources/0-13-321431-1).
- Grossman, Stanley I. (1984). [Calculus](https://books.google.com/books?id=eafiBQAAQBAJ) (3rd ed.). Academic Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4832-6239-0](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4832-6239-0).
- Gupta, Radha Charan (2019). Ramasubramanian, K. (ed.). *Gaṇitānanda: Selected Works of Radha Charan Gupta on History of Mathematics*. Springer. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-981-13-1229-8_40](https://doi.org/10.1007%2F978-981-13-1229-8_40). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [213756968](https://api.semanticscholar.org/CorpusID:213756968).
- [Hille, Einar](https://en.wikipedia.org/wiki/Einar_Hille); [Phillips, Ralph S.](https://en.wikipedia.org/wiki/Ralph_S._Phillips) (1957). *Functional analysis and semi-groups*. AMS Colloquium Publications. Vol. 31. American Mathematical Society.
- Hofmann, Josef Ehrenfried (1939). "On the Discovery of the Logarithmic Series and Its Development in England up to Cotes". *National Mathematics Magazine*. **14** (1): 33–45. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/3028095](https://doi.org/10.2307%2F3028095). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [3028095](https://www.jstor.org/stable/3028095).
- [Hörmander, Lars](https://en.wikipedia.org/wiki/Lars_H%C3%B6rmander) (2002) \[1990\]. ["A Review of Differential Calculus"](https://link.springer.com/chapter/10.1007/978-3-642-61497-2_2). *The Analysis of Partial Differential Operators I* (2nd ed.). Springer. § 1.1, pp. 5–13. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-3-642-61497-2_2](https://doi.org/10.1007%2F978-3-642-61497-2_2). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-642-61497-2](https://en.wikipedia.org/wiki/Special:BookSources/978-3-642-61497-2).
- Kline, M. (1990). [Mathematical Thought from Ancient to Modern Times](https://archive.org/details/mathematicalthou00klin). New York: Oxford University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-19-506135-7](https://en.wikipedia.org/wiki/Special:BookSources/0-19-506135-7).
- Knapp, Anthony W. (2000). [Basic Real Analysis](https://books.google.com/books?id=DLfxd7StGw8C). Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8176-4441-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8176-4441-3).
- Kolk, Johan A.C.; Duistermaat, J.J. (2010). ["Taylor Expansion in Several Variables"](https://link.springer.com/chapter/10.1007/978-0-8176-4675-2_6). *Distributions: Theory and applications*. Birkhauser. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-0-8176-4675-2_6](https://doi.org/10.1007%2F978-0-8176-4675-2_6). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8176-4672-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8176-4672-1).
- Kreyszig, Erwin (2011). [Advanced Engineering Mathematics](https://books.google.com/books?id=w4T3DwAAQBAJ). [John Wiley & Sons](https://en.wikipedia.org/wiki/John_Wiley_%26_Sons).
- Lindberg, David (2007). *The Beginnings of Western Science* (2nd ed.). University of Chicago Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-226-48205-7](https://en.wikipedia.org/wiki/Special:BookSources/978-0-226-48205-7).
- Malet, Antoni (1993). "James Gregorie on Tangents and the "Taylor" Rule for Series Expansions". *Archive for History of Exact Sciences*. **46** (2): 97–137. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/BF00375656](https://doi.org/10.1007%2FBF00375656). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [41133959](https://www.jstor.org/stable/41133959). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [120101519](https://api.semanticscholar.org/CorpusID:120101519).
- Markushevich, A. I. (1966). [Entire Functions](https://books.google.com/books?id=-rvSBQAAQBAJ). Elsevier. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4832-7490-4](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4832-7490-4).
- [Newton, Isaac](https://en.wikipedia.org/wiki/Isaac_Newton) (1761). *Tractatus de quadratura curvarum: in usum studiosae iuventutis mathematicae explicationibus illustratus*.
- Rowlands, Peter (2017). *Newton and the Great World System*. [World Scientific Publishing](https://en.wikipedia.org/wiki/World_Scientific_Publishing). p. 40. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1142/q0108](https://doi.org/10.1142%2Fq0108). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-78634-372-7](https://en.wikipedia.org/wiki/Special:BookSources/978-1-78634-372-7).
- Roy, Ranjan (1990). ["The Discovery of the Series Formula for π by Leibniz, Gregory and Nilakantha"](https://web.archive.org/web/20230314224252/https://www.maa.org/sites/default/files/images/upload_library/22/Allendoerfer/1991/0025570x.di021167.02p0073q.pdf) (PDF). *Mathematics Magazine*. **63** (5): 291–306. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/0025570X.1990.11977541](https://doi.org/10.1080%2F0025570X.1990.11977541). Archived from [the original](https://www.maa.org/sites/default/files/images/upload_library/22/Allendoerfer/1991/0025570x.di021167.02p0073q.pdf) (PDF) on 2023-03-14. Retrieved 2023-02-18.
- —— (2021) \[2011\]. *Series and Products in the Development of Mathematics*. Vol. 1 (2nd ed.). Cambridge University Press.
- [Rudin, Walter](https://en.wikipedia.org/wiki/Walter_Rudin) (1980). *Real and Complex Analysis*. New Delhi: McGraw-Hill. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-07-099557-5](https://en.wikipedia.org/wiki/Special:BookSources/0-07-099557-5).
- Saha, Swapan K. (2026). [Paradigm of Optical Imaging](https://books.google.com/books?id=ZkF-EQAAQBAJ). CRC Press.
- Sandler, Stanley I. (2011). [An Introduction to Applied Statistical Thermodynamics](http://books.google.com/books?id=6wtw2c5Cj0QC). John Wiley & Sons.
- Silverman, Richard A. (1974). *Complex Analysis with Applications*. Dover Publications.
- Struik, D. J. (1969). [A Source Book in Mathematics 1200–1800](https://books.google.com/books?id=XmRsZhJZGhEC&pg=PR11). Harvard University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-674-82355-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-674-82355-6).
- Taylor, Brook (1715). [Methodus Incrementorum Directa et Inversa](https://archive.org/details/UFIE003454_TO0324_PNI-2529_000000) \[*Direct and Reverse Methods of Incrementation*\] (in Latin). London.
- Thomas, George B. Jr.; Finney, Ross L. (1996). *Calculus and Analytic Geometry* (9th ed.). Addison Wesley. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-201-53174-7](https://en.wikipedia.org/wiki/Special:BookSources/0-201-53174-7).
- Turnbull, Herbert Westren, ed. (1939). *James Gregory; Tercentenary Memorial Volume*. G. Bell & Sons.
- Varberg, Dale E.; Purcell, Edwin J.; Rigdon, Steven E. (2007). *Calculus* (9th ed.). Pearson Prentice Hall. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780131469686](https://en.wikipedia.org/wiki/Special:BookSources/9780131469686).

## External links

- ["Taylor series"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society), 2001 \[1994\]
- [Weisstein, Eric W.](https://en.wikipedia.org/wiki/Eric_W._Weisstein) ["Taylor Series"](https://mathworld.wolfram.com/TaylorSeries.html). *[MathWorld](https://en.wikipedia.org/wiki/MathWorld)*.
