[[optimization.base]]

> Source: [Quasi-Newton method](https://en.wikipedia.org/wiki/Quasi-Newton_method)
> License: Wikipedia content is available under CC BY-SA 4.0.

In [numerical analysis](https://en.wikipedia.org/wiki/Numerical_analysis), a **quasi-Newton method** is an [iterative numerical method](https://en.wikipedia.org/wiki/Iterative_method) used either to [find zeroes](https://en.wikipedia.org/wiki/Root-finding_algorithm) or to [find local maxima and minima](https://en.wikipedia.org/wiki/Mathematical_optimization) of functions via an iterative [recurrence formula](https://en.wikipedia.org/wiki/Recurrence_formula) much like the one for [Newton's method](https://en.wikipedia.org/wiki/Newton%27s_method), except using approximations of the [derivatives](https://en.wikipedia.org/wiki/Derivative) of the functions in place of exact derivatives. Newton's method requires the [Jacobian matrix](https://en.wikipedia.org/wiki/Jacobian_matrix_and_determinant) of all [partial derivatives](https://en.wikipedia.org/wiki/Partial_derivative) of a multivariate function when used to search for zeros or the [[Hessian Matrix]] when used [for finding extrema](https://en.wikipedia.org/wiki/Newton%27s_method_in_optimization). Quasi-Newton methods, on the other hand, can be used when the Jacobian matrices or Hessian matrices are unavailable or are impractical to compute at every iteration.

Some [iterative methods](https://en.wikipedia.org/wiki/Iterative_method) that reduce to Newton's method, such as [sequential quadratic programming](https://en.wikipedia.org/wiki/Sequential_quadratic_programming), may also be considered quasi-Newton methods.

## Search for zeros: root finding

[Newton's method](https://en.wikipedia.org/wiki/Newton%27s_method) to find zeroes of a function $g$ of multiple variables is given by $x_{n+1}=x_{n}-[J_{g}(x_{n})]^{-1}g(x_{n})$, where $[J_{g}(x_{n})]^{-1}$ is the [left inverse](https://en.wikipedia.org/wiki/Inverse_element#Matrices) of the [[Jacobian Matrix]] $J_{g}(x_{n})$ of $g$ evaluated for $x_{n}$.

Strictly speaking, any method that replaces the exact Jacobian $J_{g}(x_{n})$ with an approximation is a quasi-Newton method. For instance, the chord method (where $J_{g}(x_{n})$ is replaced by $J_{g}(x_{0})$ for all iterations) is a simple example. The methods given below for [optimization](#Search_for_extrema) refer to an important subclass of quasi-Newton methods, [secant methods](https://en.wikipedia.org/wiki/Secant_method).

More recently quasi-Newton methods have been applied to find the solution of multiple coupled systems of equations (e.g. fluid–structure interaction problems or interaction problems in physics). They allow the solution to be found by solving each constituent system separately (which is simpler than the global system) in a cyclic, iterative fashion until the solution of the global system is found.

## Search for extrema: optimization

The search for a minimum or maximum of a scalar-valued function is closely related to the search for the zeroes of the [gradient](https://en.wikipedia.org/wiki/Gradient) of that function. Therefore, quasi-Newton methods can be readily applied to find extrema of a function. In other words, if $g$ is the gradient of $f$, then searching for the zeroes of the vector-valued function $g$ corresponds to the search for the extrema of the scalar-valued function $f$; the Jacobian of $g$ now becomes the Hessian of $f$. The main difference is that [[Hessian Matrix|the Hessian matrix is a symmetric matrix]], unlike the Jacobian when [searching for zeroes](#Search_for_zeroes). Most quasi-Newton methods used in optimization exploit this symmetry.

In [optimization](https://en.wikipedia.org/wiki/Optimization_(mathematics)), **quasi-Newton methods** (a special case of **variable-metric methods**) are algorithms for finding local [maxima and minima](https://en.wikipedia.org/wiki/Maxima_and_minima) of [functions](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)"). Quasi-Newton methods for optimization are based on [Newton's method](https://en.wikipedia.org/wiki/Newton%27s_method_in_optimization) to find the [stationary points](https://en.wikipedia.org/wiki/Stationary_point) of a function, points where the gradient is 0. Newton's method assumes that the function can be locally approximated as a [quadratic](https://en.wikipedia.org/wiki/Quadratic_function) in the region around the optimum, and uses the first and second derivatives to find the stationary point. In higher dimensions, Newton's method uses the gradient and the [[Hessian Matrix]] of second [derivatives](https://en.wikipedia.org/wiki/Derivative) of the function to be minimized.

In quasi-Newton methods the Hessian matrix does not need to be computed. The Hessian is updated by analyzing successive gradient vectors instead. Quasi-Newton methods are a generalization of the [secant method](https://en.wikipedia.org/wiki/Secant_method) to find the root of the first derivative for multidimensional problems. In multiple dimensions the secant equation is [under-determined](https://en.wikipedia.org/wiki/Underdetermined_system), and quasi-Newton methods differ in how they constrain the solution, typically by adding a simple low-rank update to the current estimate of the Hessian.

The first quasi-Newton algorithm was proposed by [William C. Davidon](https://en.wikipedia.org/wiki/William_C._Davidon), a physicist working at [Argonne National Laboratory](https://en.wikipedia.org/wiki/Argonne_National_Laboratory). He developed the first quasi-Newton algorithm in 1959: the [DFP updating formula](https://en.wikipedia.org/wiki/DFP_updating_formula), which was later popularized by Fletcher and Powell in 1963, but is rarely used today. The most common quasi-Newton algorithms are currently the [SR1 formula](https://en.wikipedia.org/wiki/SR1_formula) (for "symmetric rank-one"), the [BHHH](https://en.wikipedia.org/wiki/BHHH) method, the widespread [BFGS method](https://en.wikipedia.org/wiki/BFGS_method) (suggested independently by [Broyden](https://en.wikipedia.org/wiki/Charles_George_Broyden), [Fletcher](https://en.wikipedia.org/wiki/Roger_Fletcher_(mathematician) "Roger Fletcher (mathematician)"), [Goldfarb](https://en.wikipedia.org/wiki/Donald_Goldfarb), and [Shanno](https://en.wikipedia.org/wiki/David_Shanno), in 1970), and its low-memory extension [L-BFGS](https://en.wikipedia.org/wiki/L-BFGS). The Broyden's class is a linear combination of the DFP and BFGS methods.

The SR1 formula does not guarantee the update matrix to maintain [[Positive-Definite Matrix|positive-definiteness]] and can be used for indefinite problems. The [Broyden's method](https://en.wikipedia.org/wiki/Broyden%27s_method) does not require the update matrix to be symmetric and is used to find the root of a general system of equations (rather than the gradient) by updating the [Jacobian](https://en.wikipedia.org/wiki/Jacobian_matrix_and_determinant) (rather than the Hessian).

One of the chief advantages of quasi-Newton methods over [Newton's method](https://en.wikipedia.org/wiki/Newton%27s_method_in_optimization) is that the [[Hessian Matrix]] (or, in the case of quasi-Newton methods, its approximation) $B$ does not need to be inverted. Newton's method, and its derivatives such as [interior point methods](https://en.wikipedia.org/wiki/Interior_point_method), require the Hessian to be inverted, which is typically implemented by solving a [system of linear equations](https://en.wikipedia.org/wiki/System_of_linear_equations) and is often quite costly. In contrast, quasi-Newton methods usually generate an estimate of $B^{-1}$ directly.

As in [Newton's method](https://en.wikipedia.org/wiki/Newton%27s_method_in_optimization), one uses a second-order approximation to find the minimum of a function $f(x)$. The [[Taylor Series]] of $f(x)$ around an iterate is

$f(x_{k}+\Delta x)\approx f(x_{k})+\nabla f(x_{k})^{\mathrm {T} }\,\Delta x+{\frac {1}{2}}\Delta x^{\mathrm {T} }B\,\Delta x,$

where ($\nabla f$) is the [gradient](https://en.wikipedia.org/wiki/Gradient), and $B$ an approximation to the [[Hessian Matrix]]. The gradient of this approximation (with respect to $\Delta x$) is

$\nabla f(x_{k}+\Delta x)\approx \nabla f(x_{k})+B\,\Delta x,$

and setting this gradient to zero (which is the goal of optimization) provides the Newton step:

$\Delta x=-B^{-1}\nabla f(x_{k}).$

The Hessian approximation $B$ is chosen to satisfy

$\nabla f(x_{k}+\Delta x)=\nabla f(x_{k})+B\,\Delta x,$

which is called the *secant equation* (the Taylor series of the gradient itself). In more than one dimension $B$ is [underdetermined](https://en.wikipedia.org/wiki/Underdetermined_system). In one dimension, solving for $B$ and applying the Newton's step with the updated value is equivalent to the [secant method](https://en.wikipedia.org/wiki/Secant_method). The various quasi-Newton methods differ in their choice of the solution to the secant equation (in one dimension, all the variants are equivalent). Most methods (but with exceptions, such as [Broyden's method](https://en.wikipedia.org/wiki/Broyden%27s_method)) seek a symmetric solution ($B^{T}=B$); furthermore, the variants listed below can be motivated by finding an update $B_{k+1}$ that is as close as possible to $B_{k}$ in some [norm](https://en.wikipedia.org/wiki/Norm_(mathematics) "Norm (mathematics)"); that is, $B_{k+1}=\operatorname {argmin} _{B}\|B-B_{k}\|_{V}$, where $V$ is some [[Positive-Definite Matrix]] that defines the norm. An approximate initial value $B_{0}=\beta I$ is often sufficient to achieve rapid convergence, although there is no general strategy to choose $\beta$. Note that $B_{0}$ should be positive-definite. The unknown $x_{k}$ is updated applying the Newton's step calculated using the current approximate Hessian matrix $B_{k}$:

- $\Delta x_{k}=-\alpha _{k}B_{k}^{-1}\nabla f(x_{k})$, with $\alpha$ chosen to satisfy the [Wolfe conditions](https://en.wikipedia.org/wiki/Wolfe_conditions);
- $x_{k+1}=x_{k}+\Delta x_{k}$;
- The gradient computed at the new point $\nabla f(x_{k+1})$, and

$y_{k}=\nabla f(x_{k+1})-\nabla f(x_{k})$

is used to update the approximate Hessian $B_{k+1}$, or directly its inverse $H_{k+1}=B_{k+1}^{-1}$ using the [Sherman–Morrison formula](https://en.wikipedia.org/wiki/Sherman%E2%80%93Morrison_formula).

- A key property of the BFGS and DFP updates is that if $B_{k}$ is positive-definite, and $\alpha _{k}$ is chosen to satisfy the Wolfe conditions, then $B_{k+1}$ is also positive-definite.

The most popular update formulas are:

|  |  |  |
|----|----|----|
| Method | $\displaystyle B_{k+1}=$ | $H_{k+1}=B_{k+1}^{-1}=$ |
| [BFGS](https://en.wikipedia.org/wiki/BFGS_method) | $B_{k}+{\frac {y_{k}y_{k}^{\mathrm {T} }}{y_{k}^{\mathrm {T} }\Delta x_{k}}}-{\frac {B_{k}\Delta x_{k}(B_{k}\Delta x_{k})^{\mathrm {T} }}{\Delta x_{k}^{\mathrm {T} }B_{k}\,\Delta x_{k}}}$ | $\left(I-{\frac {\Delta x_{k}y_{k}^{\mathrm {T} }}{y_{k}^{\mathrm {T} }\Delta x_{k}}}\right)H_{k}\left(I-{\frac {y_{k}\Delta x_{k}^{\mathrm {T} }}{y_{k}^{\mathrm {T} }\Delta x_{k}}}\right)+{\frac {\Delta x_{k}\Delta x_{k}^{\mathrm {T} }}{y_{k}^{\mathrm {T} }\,\Delta x_{k}}}$ |
| [Broyden](https://en.wikipedia.org/wiki/Broyden%27s_method) | $B_{k}+{\frac {y_{k}-B_{k}\Delta x_{k}}{\Delta x_{k}^{\mathrm {T} }\,\Delta x_{k}}}\,\Delta x_{k}^{\mathrm {T} }$ | $H_{k}+{\frac {(\Delta x_{k}-H_{k}y_{k})\Delta x_{k}^{\mathrm {T} }H_{k}}{\Delta x_{k}^{\mathrm {T} }H_{k}\,y_{k}}}$ |
| Broyden family | $(1-\varphi _{k})B_{k+1}^{\text{BFGS}}+\varphi _{k}B_{k+1}^{\text{DFP}},\quad \varphi \in [0,1]$ |  |
| [DFP](https://en.wikipedia.org/wiki/DFP_updating_formula) | $\left(I-{\frac {y_{k}\,\Delta x_{k}^{\mathrm {T} }}{y_{k}^{\mathrm {T} }\,\Delta x_{k}}}\right)B_{k}\left(I-{\frac {\Delta x_{k}y_{k}^{\mathrm {T} }}{y_{k}^{\mathrm {T} }\,\Delta x_{k}}}\right)+{\frac {y_{k}y_{k}^{\mathrm {T} }}{y_{k}^{\mathrm {T} }\,\Delta x_{k}}}$ | $H_{k}+{\frac {\Delta x_{k}\Delta x_{k}^{\mathrm {T} }}{\Delta x_{k}^{\mathrm {T} }\,y_{k}}}-{\frac {H_{k}y_{k}y_{k}^{\mathrm {T} }H_{k}}{y_{k}^{\mathrm {T} }H_{k}y_{k}}}$ |
| [SR1](https://en.wikipedia.org/wiki/SR1_formula) | $B_{k}+{\frac {(y_{k}-B_{k}\,\Delta x_{k})(y_{k}-B_{k}\,\Delta x_{k})^{\mathrm {T} }}{(y_{k}-B_{k}\,\Delta x_{k})^{\mathrm {T} }\,\Delta x_{k}}}$ | $H_{k}+{\frac {(\Delta x_{k}-H_{k}y_{k})(\Delta x_{k}-H_{k}y_{k})^{\mathrm {T} }}{(\Delta x_{k}-H_{k}y_{k})^{\mathrm {T} }y_{k}}}$ |

Other methods are Pearson's method, McCormick's method, the Powell symmetric Broyden (PSB) method and Greenstadt's method. These recursive low-rank matrix updates can also represented as an initial matrix plus a low-rank correction. This is the [Compact quasi-Newton representation](https://en.wikipedia.org/wiki/Compact_quasi-Newton_representation), which is particularly effective for constrained and/or large problems.

## Relationship to matrix inversion

When $f$ is a convex quadratic function with positive-definite Hessian $B$, one would expect the matrices $H_{k}$ generated by a quasi-Newton method to converge to the inverse Hessian $H=B^{-1}$. This is indeed the case for the class of quasi-Newton methods based on least-change updates.

## Regular Quasi-Newton Methods

An attempt to provide an overview of the various approaches to quasi-Newton methods was made in 1985 in the article “Regular Quasi-Newton Methods.” Here, a comprehensive class of these methods was developed, a representation of all rank 1 formulas of the so-called symmetric, novelized Huang class, which includes well-known methods such as the Davidon-Fletcher-Powell (DFP), Broyden-Fletcher-Goldfarb-Shanno (BFGS), and Self-Scaling-Variable-Metric (SSVM) methods. Suggestions for further optimization of the solution behavior of quasi-Newton methods are also given. The following class of “regular” (i.e., preferred for use due to special properties) Quasi-Newton update formulas was constructed:

$H_{i+1}:=B(H_{i},p_{i},q_{i},\theta _{i},r_{i},\rho _{i})$

with

$B(H,p,q,\theta ,r,\rho )=rH+{{\rho \sigma +r\tau \theta } \over \sigma ^{2}}pp^{T}+r{{(\theta -1)} \over \tau }Hqq^{T}H-{{r\theta } \over \sigma }(pq^{T}H+Hqp^{T});$

$H\in \mathbb {R} ^{nxn}$ positive definite; $p,q\in \mathbb {R} ^{n};\epsilon =p^{T}H^{-1}p;$

$\sigma =p^{T}q;\tau =q^{T}Hq;\theta ,r,\rho \in \mathbb {R} ;r>0;\rho \sigma >0;$

$\theta [\epsilon \tau -\sigma ^{2}]>-\sigma ^{2};r\tau [\rho \sigma +\theta (r\tau -\rho \sigma )]\geq 0$.

For approximate, sufficiently accurate beam minimization, positive definite $H_{0}\in \mathbb {R} ^{nxn}$ and arbitrary $x_{0}\in \mathbb {R} ^{n}$, the following applies to these regular methods, which are derived from the above formula:

1\) The methods are quasi-Newton methods.

2\) The matrices $H_{i}$ are positive definite for all iterations. Thus,

$f(x_{i+1})<f(x_{i})$ applies for all iterations.

3\) For all iterations $i\geq 0$, we obtain solutions to the minimization problem.

For exact beam minimization and quadratic objective functions, each of these methods also terminates at the minimum point after at most n iteration steps. In particular, the regular quasi-Newton methods have the good properties of both the extended Greenstadt class and the symmetric, extended Huang class with regard to convergence and stability.

It can be assumed that all particularly powerful quasi-Newton methods are regular.

## Notable implementations

Implementations of quasi-Newton methods are available in many programming languages.

Notable open source implementations include:

- [GNU Octave](https://en.wikipedia.org/wiki/GNU_Octave) uses a form of BFGS in its `fsolve` function, with [trust region](https://en.wikipedia.org/wiki/Trust_region) extensions.
- [GNU Scientific Library](https://en.wikipedia.org/wiki/GNU_Scientific_Library) implements the Broyden-Fletcher-Goldfarb-Shanno ([BFGS](https://en.wikipedia.org/wiki/BFGS)) algorithm.
- [ALGLIB](https://en.wikipedia.org/wiki/ALGLIB) implements (L)BFGS in C++ and C#
- [R](https://en.wikipedia.org/wiki/R_(programming_language) "R (programming language)")'s `optim` general-purpose optimizer routine uses the [BFGS](https://en.wikipedia.org/wiki/BFGS) method by using `method="BFGS"`.
- [Scipy](https://en.wikipedia.org/wiki/Scipy).optimize has fmin_bfgs. In the [SciPy](https://en.wikipedia.org/wiki/SciPy) extension to [Python](https://en.wikipedia.org/wiki/Python_(programming_language) "Python (programming language)"), the `scipy.optimize.minimize` function includes, among other methods, a [BFGS](https://en.wikipedia.org/wiki/BFGS) implementation.

Notable proprietary implementations include:

- [Mathematica](https://en.wikipedia.org/wiki/Mathematica) includes quasi-Newton solvers.
- The [NAG Library](https://en.wikipedia.org/wiki/NAG_Numerical_Library) contains several routines for minimizing or maximizing a function which use quasi-Newton algorithms.
- In MATLAB's [Optimization Toolbox](https://en.wikipedia.org/wiki/Optimization_Toolbox), the `fminunc` function uses (among other methods) the [BFGS](https://en.wikipedia.org/wiki/BFGS) quasi-Newton method. Many of the constrained methods of the Optimization toolbox use [BFGS](https://en.wikipedia.org/wiki/BFGS) and the variant [L-BFGS](https://en.wikipedia.org/wiki/L-BFGS).

## See also

- [BFGS method](https://en.wikipedia.org/wiki/BFGS_method)
  - [L-BFGS](https://en.wikipedia.org/wiki/Limited-memory_BFGS)
  - [OWL-QN](https://en.wikipedia.org/wiki/Orthant-wise_limited-memory_quasi-Newton)
- [Broyden's method](https://en.wikipedia.org/wiki/Broyden%27s_method)
- [DFP updating formula](https://en.wikipedia.org/wiki/DFP_updating_formula)
- [Newton's method](https://en.wikipedia.org/wiki/Newton%27s_method)
- [Newton's method in optimization](https://en.wikipedia.org/wiki/Newton%27s_method_in_optimization)
- [SR1 formula](https://en.wikipedia.org/wiki/SR1_formula)
- [Compact quasi-Newton representation](https://en.wikipedia.org/wiki/Compact_quasi-Newton_representation)

## References

1.  Broyden, C. G. (1972). "Quasi-Newton Methods". In Murray, W. (ed.). *Numerical Methods for Unconstrained Optimization*. London: Academic Press. pp. 87–106. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-12-512250-0](https://en.wikipedia.org/wiki/Special:BookSources/0-12-512250-0).
2.  ^    Haelterman, Rob (2009). ["Analytical study of the Least Squares Quasi-Newton method for interaction problems"](https://lib.ugent.be/catalog/rug01:001333190). *PhD Thesis, Ghent University*. Retrieved 2014-08-14.
3.  Rob Haelterman; Dirk Van Eester; Daan Verleyen (2015). ["Accelerating the solution of a physics model inside a tokamak using the (Inverse) Column Updating Method"](https://doi.org/10.1016%2Fj.cam.2014.11.005). *Journal of Computational and Applied Mathematics*. **279**: 133–144. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.cam.2014.11.005](https://doi.org/10.1016%2Fj.cam.2014.11.005).
4.  ["Introduction to Taylor's theorem for multivariable functions - Math Insight"](https://mathinsight.org/taylors_theorem_multivariable_introduction). *mathinsight.org*. Retrieved November 11, 2021.
5.  Nocedal, Jorge; Wright, Stephen J. (2006). [Numerical Optimization](https://archive.org/details/numericaloptimiz00noce_990). New York: Springer. pp. [142](https://archive.org/details/numericaloptimiz00noce_990/page/n161). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-98793-2](https://en.wikipedia.org/wiki/Special:BookSources/0-387-98793-2).
6.  Robert Mansel Gower; Peter Richtarik (2015). "Randomized Quasi-Newton Updates are Linearly Convergent Matrix Inversion Algorithms". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1602.01768](https://arxiv.org/abs/1602.01768) \[[math.NA](https://arxiv.org/archive/math.NA)\].
7.  Bacharach, Guido; Freiling, Gerhard (1985). *Reguläre Quasi-Newton-Verfahren*. Universität Duisburg.
8.  ["optim function - RDocumentation"](https://www.rdocumentation.org/packages/stats/versions/3.6.2/topics/optim). *www.rdocumentation.org*. Retrieved 2022-02-21.
9.  ["Scipy.optimize.minimize — SciPy v1.7.1 Manual"](http://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html).
10. ["Unconstrained Optimization: Methods for Local Minimization—Wolfram Language Documentation"](https://reference.wolfram.com/language/tutorial/UnconstrainedOptimizationMethodsForLocalMinimization.html.en). *reference.wolfram.com*. Retrieved 2022-02-21.
11. The Numerical Algorithms Group. ["Keyword Index: Quasi-Newton"](http://www.nag.co.uk/numeric/fl/nagdoc_fl23/html/INDEXES/KWIC/quasi-newton.html). *NAG Library Manual, Mark 23*. Retrieved 2012-02-09.
12. The Numerical Algorithms Group. ["E04 – Minimizing or Maximizing a Function"](http://www.nag.co.uk/numeric/fl/nagdoc_fl23/pdf/E04/e04intro.pdf) (PDF). *NAG Library Manual, Mark 23*. Retrieved 2012-02-09.
13. ["Find minimum of unconstrained multivariable function - MATLAB fminunc"](https://web.archive.org/web/20120112061052/http://www.mathworks.com/help/toolbox/optim/ug/fminunc.html). Archived from [the original](http://www.mathworks.com/help/toolbox/optim/ug/fminunc.html) on 2012-01-12. Retrieved 2012-03-07.
14. ["Constrained Nonlinear Optimization Algorithms - MATLAB & Simulink"](https://www.mathworks.com/help/optim/ug/constrained-nonlinear-optimization-algorithms.html). *www.mathworks.com*. Retrieved 2022-02-21.

## Further reading

- Bonnans, J. F.; Gilbert, J. Ch.; [Lemaréchal, C.](https://en.wikipedia.org/wiki/Claude_Lemar%C3%A9chal); [Sagastizábal, C. A.](https://en.wikipedia.org/wiki/Claudia_Sagastiz%C3%A1bal) (2006). *Numerical Optimization : Theoretical and Numerical Aspects* (Second ed.). Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [3-540-35445-X](https://en.wikipedia.org/wiki/Special:BookSources/3-540-35445-X).
- Fletcher, Roger (1987), [Practical methods of optimization](https://archive.org/details/practicalmethods0000flet) (2nd ed.), New York: [John Wiley & Sons](https://en.wikipedia.org/wiki/John_Wiley_%26_Sons), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-91547-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-91547-8).
- Nocedal, Jorge; Wright, Stephen J. (1999). ["Quasi-Newton Methods"](https://books.google.com/books?id=7wDpBwAAQBAJ&pg=PA192). *Numerical Optimization*. New York: Springer. pp. 192–221. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-98793-2](https://en.wikipedia.org/wiki/Special:BookSources/0-387-98793-2).
- Press, W. H.; Teukolsky, S. A.; Vetterling, W. T.; Flannery, B. P. (2007). ["Section 10.9. Quasi-Newton or Variable Metric Methods in Multidimensions"](http://apps.nrbook.com/empanel/index.html#pg=521). *Numerical Recipes: The Art of Scientific Computing* (3rd ed.). New York: Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-88068-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-88068-8).
- Scales, L. E. (1985). [Introduction to Non-Linear Optimization](https://books.google.com/books?id=AEJdDwAAQBAJ&pg=PA84). New York: MacMillan. pp. 84–106. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-333-32552-4](https://en.wikipedia.org/wiki/Special:BookSources/0-333-32552-4).
