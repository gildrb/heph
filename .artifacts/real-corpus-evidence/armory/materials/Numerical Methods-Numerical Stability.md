[[numerical-methods.base]]

> Source: [[Numerical Stability]]
> License: Wikipedia content is available under CC BY-SA 4.0.

In the [mathematical](https://en.wikipedia.org/wiki/Mathematics) subfield of [numerical analysis](https://en.wikipedia.org/wiki/Numerical_analysis), **numerical stability** is a generally desirable property of [numerical algorithms](https://en.wikipedia.org/wiki/Numerical_algorithm). The precise definition of stability depends on the context: one important context is [numerical linear algebra](https://en.wikipedia.org/wiki/Numerical_linear_algebra), and another is algorithms for solving ordinary and partial differential equations by discrete approximation.

In numerical linear algebra, the principal concern is instabilities caused by proximity to singularities of various kinds, such as very small or nearly colliding [eigenvalues](https://en.wikipedia.org/wiki/Eigenvalues). On the other hand, in numerical algorithms for differential equations the concern is the growth of round-off errors and/or small fluctuations in initial data which might cause a large deviation of final answer from the exact solution.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

Some numerical algorithms may damp out the small fluctuations (errors) in the input data; others might magnify such errors. Calculations that can be proven not to magnify approximation errors are called *numerically stable*. One of the common tasks of numerical analysis is to try to select algorithms which are *robust* – that is to say, do not produce a wildly different result for a very small change in the input data.

An [opposite](https://en.wikipedia.org/wiki/Opposite_(semantics)) phenomenon is **instability**. Typically, an algorithm involves an approximative method, and in some cases one could prove that the algorithm would approach the right solution in some limit (when using actual real numbers, not floating point numbers). Even in this case, there is no guarantee that it would converge to the correct solution, because the floating-point round-off or truncation errors can be magnified, instead of damped, causing the deviation from the exact solution to grow exponentially.

## Stability in numerical linear algebra

There are different ways to formalize the concept of stability. The following definitions of forward, backward, and mixed stability are often used in [numerical linear algebra](https://en.wikipedia.org/wiki/Numerical_linear_algebra).

![[media/26f7d1f5eb23c5739f230852d28c8e1312d2c185.png]]
Diagram showing the <strong>forward error</strong> Δ<em>y</em> and the <strong>backward error</strong> Δ<em>x</em>, and their relation to the exact solution map f and the numerical solution f*.

Consider the problem to be solved by the numerical algorithm as a [function](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)") f mapping the data x to the solution y. The result of the algorithm, say y\*, will usually deviate from the "true" solution y. The main causes of error are [round-off error](https://en.wikipedia.org/wiki/Round-off_error) and [truncation error](https://en.wikipedia.org/wiki/Truncation_error). The *forward error* of the algorithm is the difference between the result and the "true" solution; in this case, Δ*y* = *y*\* − *y*. The *backward error* is the smallest Δ*x* such that *f* (*x* + Δ*x*) = *y*\*; in other words, the backward error tells us what problem the algorithm actually solved. The forward and backward error are related by the [[Condition Number]]: the forward error is at most as big in magnitude as the condition number multiplied by the magnitude of the backward error.

In many cases, it is more natural to consider the [relative error](https://en.wikipedia.org/wiki/Relative_error) 

$$
{\frac {|\Delta x|}{|x|}}
$$

 instead of the absolute error Δ*x*.

The algorithm is said to be *backward stable* if the backward error is small for all inputs x. Of course, "small" is a relative term and its definition will depend on the context. Often, we want the error to be of the same order as, or perhaps only a few [orders of magnitude](https://en.wikipedia.org/wiki/Orders_of_magnitude) bigger than, the [unit round-off](https://en.wikipedia.org/wiki/Unit_round-off).

![[media/bc50200f8f7468d708624dcf33a440e41bc5af78.png]]
Mixed stability combines the concepts of forward error and backward error.

The usual definition of numerical stability uses a more general concept, called *mixed stability*, which combines the forward error and the backward error. An algorithm is stable in this sense if it solves a nearby problem approximately, i.e., if there exists a Δ*x* such that both Δ*x* is small and *f* (*x* + Δ*x*) − *y*\* is small. Hence, a backward stable algorithm is always stable.

An algorithm is *forward stable* if its forward error divided by the condition number of the problem is small. This means that an algorithm is forward stable if it has a forward error of magnitude similar to some backward stable algorithm.

## Stability in numerical differential equations

The above definitions are particularly relevant in situations where truncation errors are not important. In other contexts, for instance when solving [differential equations](https://en.wikipedia.org/wiki/Differential_equation), a different definition of numerical stability is used.

In [numerical ordinary differential equations](https://en.wikipedia.org/wiki/Numerical_methods_for_ordinary_differential_equations), various concepts of numerical stability exist, for instance [A-stability](https://en.wikipedia.org/wiki/Stiff_equation#A-stability). They are related to some concept of stability in the [dynamical systems](https://en.wikipedia.org/wiki/Dynamical_system) sense, often [Lyapunov stability](https://en.wikipedia.org/wiki/Lyapunov_stability). It is important to use a stable method when solving a [stiff equation](https://en.wikipedia.org/wiki/Stiff_equation).

Yet another definition is used in [numerical partial differential equations](https://en.wikipedia.org/wiki/Numerical_partial_differential_equations). An algorithm for solving a linear evolutionary [partial differential equation](https://en.wikipedia.org/wiki/Partial_differential_equation) is stable if the [total variation](https://en.wikipedia.org/wiki/Total_variation) of the numerical solution at a fixed time remains bounded as the step size goes to zero. The [Lax equivalence theorem](https://en.wikipedia.org/wiki/Lax_equivalence_theorem) states that an algorithm [converges](https://en.wikipedia.org/wiki/Numerical_methods_for_ordinary_differential_equations#Convergence) if it is [consistent](https://en.wikipedia.org/wiki/Numerical_methods_for_ordinary_differential_equations#Consistency_and_order) and [stable](https://en.wikipedia.org/wiki/Numerical_methods_for_ordinary_differential_equations#Stability_and_stiffness) (in this sense). Stability is sometimes achieved by including [numerical diffusion](https://en.wikipedia.org/wiki/Numerical_diffusion). Numerical diffusion is a mathematical term which ensures that roundoff and other errors in the calculation get spread out and do not add up to cause the calculation to "blow up". [Von Neumann stability analysis](https://en.wikipedia.org/wiki/Von_Neumann_stability_analysis) is a commonly used procedure for the stability analysis of [finite difference schemes](https://en.wikipedia.org/wiki/Finite_difference_method) as applied to linear partial differential equations. These results do not hold for nonlinear PDEs, where a general, consistent definition of stability is complicated by many properties absent in linear equations.

## Example

Computing the square root of 2 (which is roughly 1.41421) is a [well-posed problem](https://en.wikipedia.org/wiki/Well-posed_problem). Many algorithms solve this problem by starting with an initial approximation *x*<sub>0</sub> to ${\sqrt {2}}$, for instance *x*<sub>0</sub> = 1.4, and then computing improved guesses *x*<sub>1</sub>, *x*<sub>2</sub>, etc. One such method is the famous [Babylonian method](https://en.wikipedia.org/wiki/Babylonian_method), which is given by *x*<sub>*k*+1</sub> = (*x<sub>k</sub>*+ 2/*x<sub>k</sub>*)/2. Another method, called "method X", is given by *x*<sub>*k*+1</sub> = (*x*<sub>*k*</sub><sup>2</sup> − 2)<sup>2</sup> + *x*<sub>*k*</sub>. A few iterations of each scheme are calculated in table form below, with initial guesses *x*<sub>0</sub> = 1.4 and *x*<sub>0</sub> = 1.42.

|  |  |  |  |
|----|----|----|----|
| Babylonian | Babylonian | Method X | Method X |
| *x*<sub>0</sub> = 1.4 | *x*<sub>0</sub> = 1.42 | *x*<sub>0</sub> = 1.4 | *x*<sub>0</sub> = 1.42 |
| *x*<sub>1</sub> = 1.4142857... | *x*<sub>1</sub> = 1.41422535... | *x*<sub>1</sub> = 1.4016 | *x*<sub>1</sub> = 1.42026896 |
| *x*<sub>2</sub> = 1.414213564... | *x*<sub>2</sub> = 1.41421356242... | *x*<sub>2</sub> = 1.4028614... | *x*<sub>2</sub> = 1.42056... |
|  |  | ... | ... |
|  |  | *x*<sub>1000000</sub> = 1.41421... | *x*<sub>27</sub> = 7280.2284... |

Observe that the Babylonian method converges quickly regardless of the initial guess, whereas Method X converges extremely slowly with initial guess *x*<sub>0</sub> = 1.4 and diverges for initial guess *x*<sub>0</sub> = 1.42. Hence, the Babylonian method is numerically stable, while Method X is numerically unstable.

Numerical stability is affected by the number of the significant digits the machine keeps. If a machine is used that keeps only the four most significant decimal digits, a good example on loss of significance can be given by the two equivalent functions

$f(x)=x\left({\sqrt {x+1}}-{\sqrt {x}}\right)$ and $g(x)={\frac {x}{{\sqrt {x+1}}+{\sqrt {x}}}}.$

Comparing the results of

$f(500)=500\left({\sqrt {501}}-{\sqrt {500}}\right)=500\left(22.38-22.36\right)=500(0.02)=10$

and

${\begin{alignedat}{3}g(500)&={\frac {500}{{\sqrt {501}}+{\sqrt {500}}}}\\&={\frac {500}{22.38+22.36}}\\&={\frac {500}{44.74}}=11.17\end{alignedat}}$

by comparing the two results above, it is clear that [loss of significance](https://en.wikipedia.org/wiki/Loss_of_significance) (caused here by [catastrophic cancellation](https://en.wikipedia.org/wiki/Catastrophic_cancellation) from subtracting approximations to the nearby numbers ${\sqrt {501}}$ and ${\sqrt {500}}$, despite the subtraction being computed exactly) has a huge effect on the results, even though both functions are equivalent, as shown below

${\begin{alignedat}{4}f(x)&=x\left({\sqrt {x+1}}-{\sqrt {x}}\right)\\&=x\left({\sqrt {x+1}}-{\sqrt {x}}\right){\frac {{\sqrt {x+1}}+{\sqrt {x}}}{{\sqrt {x+1}}+{\sqrt {x}}}}\\&=x{\frac {({\sqrt {x+1}})^{2}-({\sqrt {x}})^{2}}{{\sqrt {x+1}}+{\sqrt {x}}}}\\&=x{\frac {x+1-x}{{\sqrt {x+1}}+{\sqrt {x}}}}\\&=x{\frac {1}{{\sqrt {x+1}}+{\sqrt {x}}}}\\&={\frac {x}{{\sqrt {x+1}}+{\sqrt {x}}}}\\&=g(x)\end{alignedat}}$

The desired value, computed using infinite precision, is 11.174755...

## See also

- [Algorithms for calculating variance](https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance)
- [Stability theory](https://en.wikipedia.org/wiki/Stability_theory)
- [Chaos theory](https://en.wikipedia.org/wiki/Chaos_theory)
- [Propagation of uncertainty](https://en.wikipedia.org/wiki/Propagation_of_uncertainty)

## Notes

1.  This is a [fixed point iteration](https://en.wikipedia.org/wiki/Fixed_point_iteration) for the equation $x=(x^{2}-2)^{2}+x=f(x)$, whose solutions include ${\sqrt {2}}$. The iterates always move to the right since $f(x)\geq x$. Hence $x_{1}=1.4<{\sqrt {2}}$ converges and $x_{1}=1.42>{\sqrt {2}}$ diverges.
2.  The example is a modification of one taken from .

## References

1.  Giesela Engeln-Müllges; Frank Uhlig (2 July 1996). [Numerical Algorithms with C](https://books.google.com/books?id=HurESoDQljcC&pg=PA10). M. Schon (Translator), F. Uhlig (Translator) (1 ed.). Springer. p. 10. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-60530-0](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-60530-0).
2.  Mathews, John H.; Fink, Kurtis D. (1999). "Example 1.17". *Numerical Methods Using MATLAB* (3rd ed.). Prentice Hall. p. 28.

- [Nicholas J. Higham](https://en.wikipedia.org/wiki/Nicholas_Higham) (1996). [Accuracy and Stability of Numerical Algorithms](https://archive.org/details/accuracystabilit0000high). Philadelphia: Society of Industrial and Applied Mathematics. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-89871-355-2](https://en.wikipedia.org/wiki/Special:BookSources/0-89871-355-2).
- Richard L. Burden; J. Douglas Faires (2005). *Numerical Analysis* (8th ed.). U.S.: Thomson Brooks/Cole. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-534-39200-8](https://en.wikipedia.org/wiki/Special:BookSources/0-534-39200-8).
- Mesnard, Olivier; Barba, Lorena A. (2017). "Reproducible and Replicable Computational Fluid Dynamics: It's Harder Than You Think". *Computing in Science & Engineering*. **19** (4): 44–55. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1605.04339](https://arxiv.org/abs/1605.04339). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2017CSE....19d..44M](https://ui.adsabs.harvard.edu/abs/2017CSE....19d..44M). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/MCSE.2017.3151254](https://doi.org/10.1109%2FMCSE.2017.3151254). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [11288122](https://api.semanticscholar.org/CorpusID:11288122).
