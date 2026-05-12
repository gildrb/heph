[[optimization.base]]

> Source: [[Line Search]]
> License: Wikipedia content is available under CC BY-SA 4.0.

In [optimization](https://en.wikipedia.org/wiki/Optimization_(mathematics)), **line search** is a basic [iterative](https://en.wikipedia.org/wiki/Iteration) approach to find a [local minimum](https://en.wikipedia.org/wiki/Maxima_and_minima) $\mathbf {x} ^{*}$ of an [objective function](https://en.wikipedia.org/wiki/Objective_function) $f:\mathbb {R} ^{n}\to \mathbb {R}$. It first finds a [descent direction](https://en.wikipedia.org/wiki/Descent_direction) along which the objective function $f$ will be reduced, and then computes a step size that determines how far $\mathbf {x}$ should move along that direction. The descent direction can be computed by various methods, such as [[Gradient Descent]] or [quasi-Newton method](https://en.wikipedia.org/wiki/Quasi-Newton_method). The step size can be determined either exactly or inexactly.

## One-dimensional line search

Suppose *f* is a one-dimensional function, $f:\mathbb {R} \to \mathbb {R}$, and assume that it is [unimodal](https://en.wikipedia.org/wiki/Unimodal), that is, contains exactly one local minimum *x*\* in a given interval \[*a*,*z*\]. This means that *f* is strictly decreasing in \[a,x\*\] and strictly increasing in \[x\*,*z*\]. There are several ways to find an (approximate) minimum point in this case.

### Zero-order methods

Zero-order methods use only function evaluations (i.e., a [value oracle](https://en.wikipedia.org/wiki/Value_oracle)) - not derivatives:

- [Ternary search](https://en.wikipedia.org/wiki/Ternary_search): pick some two points *b,c* such that *a*\<*b*\<*c*\<*z*. If f(*b*)≤f(*c*), then x\* must be in \[*a*,*c*\]; if f(*b*)≥f(*c*), then x\* must be in \[*b*,*z*\]. In both cases, we can replace the search interval with a smaller one. If we pick *b*,*c* very close to the interval center, then the interval shrinks by ~1/2 at each iteration, but we need two function evaluations per iteration. Therefore, the method has [linear convergence](https://en.wikipedia.org/wiki/Linear_convergence) with rate ${\sqrt {0.5}}\approx 0.71$. If we pick b,c such that the partition a,b,c,z has three equal-length intervals, then the interval shrinks by 2/3 at each iteration, so the method has [linear convergence](https://en.wikipedia.org/wiki/Linear_convergence) with rate ${\sqrt {2/3}}\approx 0.82$.
- Fibonacci search: This is a variant of ternary search in which the points *b*,*c* are selected based on the [Fibonacci sequence](https://en.wikipedia.org/wiki/Fibonacci_sequence). At each iteration, only one function evaluation is needed, since the other point was already an endpoint of a previous interval. Therefore, the method has linear convergence with rate $1/\varphi \approx 0.618$ .
- [Golden-section search](https://en.wikipedia.org/wiki/Golden-section_search): This is a variant in which the points *b*,*c* are selected based on the [golden ratio](https://en.wikipedia.org/wiki/Golden_ratio). Again, only one function evaluation is needed in each iteration, and the method has linear convergence with rate $1/\varphi \approx 0.618$ . This ratio is optimal among the zero-order methods.

Zero-order methods are very general - they do not assume differentiability or even continuity.

### First-order methods

First-order methods assume that *f* is continuously differentiable, and that we can evaluate not only *f* but also its derivative.

- The [bisection method](https://en.wikipedia.org/wiki/Bisection_method) computes the derivative of *f* at the center of the interval, *c*: if f'(c)=0, then this is the minimum point; if f'(*c*)\>0, then the minimum must be in \[*a*,*c*\]; if f'(*c*)\<0, then the minimum must be in \[*c*,*z*\]. This method has linear convergence with rate 0.5.

### Curve-fitting methods

Curve-fitting methods try to attain [superlinear convergence](https://en.wikipedia.org/wiki/Superlinear_convergence) by assuming that *f* has some analytic form, e.g. a polynomial of finite degree. At each iteration, there is a set of "working points" in which we know the value of *f* (and possibly also its derivative). Based on these points, we can compute a polynomial that fits the known values, and find its minimum analytically. The minimum point becomes a new working point, and we proceed to the next iteration:

- [Newton's method](https://en.wikipedia.org/wiki/Newton%27s_method_in_optimization) is a special case of a curve-fitting method, in which the curve is a degree-two polynomial, constructed using the first and second derivatives of *f*. If the method is started close enough to a non-degenerate local minimum (= with a positive second derivative), then it has [quadratic convergence](https://en.wikipedia.org/wiki/Quadratic_convergence).
- [Regula falsi](https://en.wikipedia.org/wiki/Regula_falsi) is another method that fits the function to a degree-two polynomial, but it uses the first derivative at two points, rather than the first and second derivative at the same point. If the method is started close enough to a non-degenerate local minimum, then it has superlinear convergence of order $\varphi \approx 1.618$.
- *Cubic fit* fits to a degree-three polynomial, using both the function values and its derivative at the last two points. If the method is started close enough to a non-degenerate local minimum, then it has [quadratic convergence](https://en.wikipedia.org/wiki/Quadratic_convergence).

Curve-fitting methods have superlinear convergence when started close enough to the local minimum, but might diverge otherwise. *Safeguarded curve-fitting methods* simultaneously execute a linear-convergence method in parallel to the curve-fitting method. They check in each iteration whether the point found by the curve-fitting method is close enough to the interval maintained by safeguard method; if it is not, then the safeguard method is used to compute the next iterate.

## Multi-dimensional line search

In general, we have a multi-dimensional [objective function](https://en.wikipedia.org/wiki/Objective_function) $f:\mathbb {R} ^{n}\to \mathbb {R}$. The line-search method first finds a [descent direction](https://en.wikipedia.org/wiki/Descent_direction) along which the objective function $f$ will be reduced, and then computes a step size that determines how far $\mathbf {x}$ should move along that direction. The descent direction can be computed by various methods, such as [[Gradient Descent]] or [quasi-Newton method](https://en.wikipedia.org/wiki/Quasi-Newton_method). The step size can be determined either exactly or inexactly. Here is an example gradient method that uses a line search in step 5:

1.  Set iteration counter $k=0$ and make an initial guess $\mathbf {x} _{0}$ for the minimum. Pick $\epsilon$ a tolerance.
2.  Loop:
    1.  Compute a [descent direction](https://en.wikipedia.org/wiki/Descent_direction) $\mathbf {p} _{k}$.
    2.  Define a one-dimensional function $h(\alpha _{k})=f(\mathbf {x} _{k}+\alpha _{k}\mathbf {p} _{k})$, representing the function value on the descent direction given the step-size.
    3.  Find an $\displaystyle \alpha _{k}$ that minimizes $h$ over $\alpha _{k}\in \mathbb {R} _{+}$.
    4.  Update $\mathbf {x} _{k+1}=\mathbf {x} _{k}+\alpha _{k}\mathbf {p} _{k}$, and $k=k+1$
3.  Until $\|\nabla f(\mathbf {x} _{k+1})\|<\epsilon$

At the line search step (2.3), the algorithm may minimize *h* *exactly*, by solving $h'(\alpha _{k})=0$, or *approximately*, by using one of the one-dimensional line-search methods mentioned above. It can also be solved *loosely*, by asking for a sufficient decrease in *h* that does not necessarily approximate the optimum. One example of the former is [[Conjugate Gradient Method]]. The latter is called inexact line search and may be performed in a number of ways, such as a [backtracking line search](https://en.wikipedia.org/wiki/Backtracking_line_search) or using the [Wolfe conditions](https://en.wikipedia.org/wiki/Wolfe_conditions).

## Overcoming local minima

Like other optimization methods, line search may be combined with [simulated annealing](https://en.wikipedia.org/wiki/Simulated_annealing) to allow it to jump over some [local minima](https://en.wikipedia.org/wiki/Local_minimum).

## See also

- [Trust region](https://en.wikipedia.org/wiki/Trust_region) - a dual approach for finding a local minimum: it first computes a step size, and then determines the descent direction.
- [Grid search](https://en.wikipedia.org/wiki/Grid_search)
- [Learning rate](https://en.wikipedia.org/wiki/Learning_rate)
- [Pattern search (optimization)](https://en.wikipedia.org/wiki/Pattern_search_(optimization) "Pattern search (optimization)")
- [Secant method](https://en.wikipedia.org/wiki/Secant_method)

## References

1.  ^      Nemirovsky and Ben-Tal (2023). ["Optimization III: Convex Optimization"](http://www2.isye.gatech.edu/~nemirovs/OPTIIILN2023Spring.pdf) (PDF).

## Further reading

- Dennis, J. E. Jr.; Schnabel, Robert B. (1983). "Globally Convergent Modifications of Newton's Method". *Numerical Methods for Unconstrained Optimization and Nonlinear Equations*. Englewood Cliffs: Prentice-Hall. pp. 111–154. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-13-627216-9](https://en.wikipedia.org/wiki/Special:BookSources/0-13-627216-9).
- Nocedal, Jorge; Wright, Stephen J. (1999). "Line Search Methods". *Numerical Optimization*. New York: Springer. pp. 34–63. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-98793-2](https://en.wikipedia.org/wiki/Special:BookSources/0-387-98793-2).
- Sun, Wenyu; Yuan, Ya-Xiang (2006). "Line Search". *Optimization Theory and Methods: Nonlinear Programming*. New York: Springer. pp. 71–117. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-24975-3](https://en.wikipedia.org/wiki/Special:BookSources/0-387-24975-3).
