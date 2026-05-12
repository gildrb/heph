[[optimization.base]]

> Source: [Proximal gradient method](https://en.wikipedia.org/wiki/Proximal_gradient_method)
> License: Wikipedia content is available under CC BY-SA 4.0.

**Proximal gradient methods** are a generalized form of projection used to solve non-differentiable [[Convex Optimization]] problems.

A comparison between the iterates of the projected gradient method (in red) and the [Frank-Wolfe method](https://en.wikipedia.org/wiki/Frank%E2%80%93Wolfe_algorithm) (in green).

Many interesting problems can be formulated as convex optimization problems of the form

$\min _{\mathbf {x} \in \mathbb {R} ^{d}}\sum _{i=1}^{n}f_{i}(\mathbf {x} )$

where $f_{i}:\mathbb {R} ^{d}\rightarrow \mathbb {R} ,\ i=1,\dots ,n$ are possibly non-differentiable [convex functions](https://en.wikipedia.org/wiki/Convex_functions). The lack of differentiability rules out conventional smooth optimization techniques like the [[Gradient Descent|steepest descent method]] and the [[Conjugate Gradient Method]], but proximal gradient methods can be used instead.

Proximal gradient methods starts by a splitting step, in which the functions $f_{1},...,f_{n}$ are used individually so as to yield an easily [implementable](https://en.wiktionary.org/wiki/implementable) algorithm. They are called [proximal](https://en.wikipedia.org/wiki/Proximal) because each non-differentiable function among $f_{1},...,f_{n}$ is involved via its [proximity operator](https://en.wikipedia.org/wiki/Proximal_operator). Iterative shrinkage thresholding algorithm, [projected Landweber](https://en.wikipedia.org/wiki/Landweber_iteration), projected gradient, [alternating projections](https://en.wikipedia.org/wiki/Alternating_projection), [alternating-direction method of multipliers](https://en.wikipedia.org/wiki/Alternating_direction_method_of_multipliers#Alternating_direction_method_of_multipliers), alternating split [Bregman](https://en.wikipedia.org/wiki/Bregman_method) are special instances of proximal algorithms.

For the theory of proximal gradient methods from the perspective of and with applications to [[Statistical Learning Theory]], see [proximal gradient methods for learning](https://en.wikipedia.org/wiki/Proximal_gradient_methods_for_learning).

## Projection onto convex sets (POCS)

One of the widely used convex optimization algorithms is [projections onto convex sets](https://en.wikipedia.org/wiki/Projections_onto_convex_sets) (POCS). This algorithm is employed to recover/synthesize a signal satisfying simultaneously several convex constraints. Let $f_{i}$ be the indicator function of non-empty closed convex set $C_{i}$ modeling a constraint. This reduces to convex feasibility problem, which require us to find a solution such that it lies in the intersection of all convex sets $C_{i}$. In POCS method each set $C_{i}$ is incorporated by its [projection operator](https://en.wikipedia.org/wiki/Projection_operator) $P_{C_{i}}$. So in each [iteration](https://en.wikipedia.org/wiki/Iteration) $x$ is updated as

$x_{k+1}=P_{C_{1}}P_{C_{2}}\cdots P_{C_{n}}x_{k}$

However beyond such problems [projection operators](https://en.wikipedia.org/wiki/Projection_operator) are not appropriate and more general operators are required to tackle them. Among the various generalizations of the notion of a convex projection operator that exist, proximal operators are best suited for other purposes.

## Examples

Special instances of Proximal Gradient Methods are

- [Projected Landweber](https://en.wikipedia.org/wiki/Landweber_iteration)
- [Alternating projection](https://en.wikipedia.org/wiki/Alternating_projection)
- [Alternating-direction method of multipliers](https://en.wikipedia.org/wiki/Alternating_direction_method_of_multipliers#Alternating_direction_method_of_multipliers)

## See also

- [Proximal operator](https://en.wikipedia.org/wiki/Proximal_operator)
- [Proximal gradient methods for learning](https://en.wikipedia.org/wiki/Proximal_gradient_methods_for_learning)
- [Frank–Wolfe algorithm](https://en.wikipedia.org/wiki/Frank%E2%80%93Wolfe_algorithm)

## Notes

1.  Daubechies, I; Defrise, M; [De Mol, C](https://en.wikipedia.org/wiki/Christine_De_Mol) (2004). "An iterative thresholding algorithm for linear inverse problems with a sparsity constraint". *Communications on Pure and Applied Mathematics*. **57** (11): 1413–1457. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[math/0307152](https://arxiv.org/abs/math/0307152). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2003math......7152D](https://ui.adsabs.harvard.edu/abs/2003math......7152D). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1002/cpa.20042](https://doi.org/10.1002%2Fcpa.20042).
2.  Details of proximal methods are discussed in Combettes, Patrick L.; Pesquet, Jean-Christophe (2009). "Proximal Splitting Methods in Signal Processing". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[0912.3522](https://arxiv.org/abs/0912.3522) \[[math.OC](https://arxiv.org/archive/math.OC)\].

## References

- [Rockafellar, R. T.](https://en.wikipedia.org/wiki/R._Tyrrell_Rockafellar) (1970). *Convex analysis*. Princeton: Princeton University Press.
- Combettes, Patrick L.; Pesquet, Jean-Christophe (2011). *Fixed-Point Algorithms for Inverse Problems in Science and Engineering*. Vol. 49. pp. 185–212.

## External links

- Stephen Boyd and Lieven Vandenberghe Book, [Convex optimization](https://web.stanford.edu/~boyd/cvxbook/)
- [EE364a: Convex Optimization I](https://web.stanford.edu/class/ee364a/) and [EE364b: Convex Optimization II](https://web.stanford.edu/class/ee364b/), Stanford course homepages
- [EE227A: Lieven Vandenberghe Notes](https://people.eecs.berkeley.edu/~elghaoui/Teaching/EE227A/lecture18.pdf) Lecture 18
- [ProximalOperators.jl](https://github.com/kul-forbes/ProximalOperators.jl): a [Julia](https://en.wikipedia.org/wiki/Julia_(programming_language) "Julia (programming language)") package implementing proximal operators.
- [ProximalAlgorithms.jl](https://github.com/kul-forbes/ProximalAlgorithms.jl): a [Julia](https://en.wikipedia.org/wiki/Julia_(programming_language) "Julia (programming language)") package implementing algorithms based on the proximal operator, including the proximal gradient method.
- [Proximity Operator repository](http://proximity-operator.net/): a collection of proximity operators implemented in [Matlab](https://en.wikipedia.org/wiki/Matlab) and [Python](https://en.wikipedia.org/wiki/Python_(programming_language) "Python (programming language)").
