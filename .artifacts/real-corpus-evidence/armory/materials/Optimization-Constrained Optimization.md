[[optimization.base]]

> Source: [[Constrained Optimization]]
> License: Wikipedia content is available under CC BY-SA 4.0.

In [mathematical optimization](https://en.wikipedia.org/wiki/Mathematical_optimization), **constrained optimization** (in some contexts called **constraint optimization**) is the process of optimizing an objective function with respect to some [variables](https://en.wikipedia.org/wiki/Variable_(mathematics) "Variable (mathematics)") in the presence of [constraints](https://en.wikipedia.org/wiki/Constraint_(mathematics) "Constraint (mathematics)") on those variables. The objective function is either a [cost function](https://en.wikipedia.org/wiki/Loss_function) or [energy function](https://en.wikipedia.org/wiki/Energy_function), which is to be [minimized](https://en.wikipedia.org/wiki/Maxima_and_minima), or a [reward function](https://en.wikipedia.org/wiki/Reward_function) or [utility function](https://en.wikipedia.org/wiki/Utility_function), which is to be [maximized](https://en.wikipedia.org/wiki/Maximize). Constraints can be either **hard constraints**, which set conditions for the variables that are required to be satisfied, or **soft constraints**, which have some variable values that are penalized in the objective function if, and based on the extent that, the conditions on the variables are not satisfied.

## Relation to constraint-satisfaction problems

The constrained-optimization problem (COP) is a significant generalization of the classic [constraint-satisfaction problem](https://en.wikipedia.org/wiki/Constraint-satisfaction_problem) (CSP) model. COP is a CSP that includes an *objective function* to be optimized. Many algorithms are used to handle the optimization part.

## General form

A general constrained minimization problem may be written as follows:

${\begin{array}{rcll}\min &~&f(\mathbf {x} )&\\\mathrm {subject~to} &~&g_{i}(\mathbf {x} )=c_{i}&{\text{for }}i=1,\ldots ,n\quad {\text{Equality constraints}}\\&~&h_{j}(\mathbf {x} )\geq d_{j}&{\text{for }}j=1,\ldots ,m\quad {\text{Inequality constraints}}\end{array}}$

where $g_{i}(\mathbf {x} )=c_{i}~\mathrm {for~} i=1,\ldots ,n$ and $h_{j}(\mathbf {x} )\geq d_{j}~\mathrm {for~} j=1,\ldots ,m$ are constraints that are required to be satisfied (these are called [hard constraints](https://en.wikipedia.org/wiki/Constraint_(mathematics)#Hard_and_soft_constraints "Constraint (mathematics)")), and $f(\mathbf {x} )$ is the objective function that needs to be optimized subject to the constraints.

In some problems, often called *constraint optimization problems*, the objective function is actually the sum of cost functions, each of which penalizes the extent (if any) to which a [soft constraint](https://en.wikipedia.org/wiki/Constraint_(mathematics)#Hard_and_soft_constraints "Constraint (mathematics)") (a constraint which is preferred but not required to be satisfied) is violated.

## Solution methods

Many constrained optimization algorithms can be adapted to the unconstrained case, often via the use of a [penalty method](https://en.wikipedia.org/wiki/Penalty_method). However, search steps taken by the unconstrained method may be unacceptable for the constrained problem, leading to a lack of convergence. This is referred to as the Maratos effect.

### Equality constraints

####  Substitution method

For very simple problems, say a function of two variables subject to a single equality constraint, it is most practical to apply the method of substitution. The idea is to substitute the constraint into the objective function to create a [composite function](https://en.wikipedia.org/wiki/Function_composition) that incorporates the effect of the constraint. For example, assume the objective is to maximize $f(x,y)=x\cdot y$ subject to $x+y=10$. The constraint implies $y=10-x$, which can be substituted into the objective function to create $p(x)=x(10-x)=10x-x^{2}$. The first-order necessary condition gives ${\frac {\partial p}{\partial x}}=10-2x=0$, which can be solved for $x=5$ and, consequently, $y=10-5=5$.

#### Lagrange multiplier

If the constrained problem has only equality constraints, the method of [[Lagrange Multipliers]] can be used to convert it into an unconstrained problem whose number of variables is the original number of variables plus the original number of equality constraints. Alternatively, if the constraints are all equality constraints and are all linear, they can be solved for some of the variables in terms of the others, and the former can be substituted out of the objective function, leaving an unconstrained problem in a smaller number of variables.

### Inequality constraints

#### Linear programming

If the objective function and all of the hard constraints are linear and some hard constraints are inequalities, then the problem is a [linear programming](https://en.wikipedia.org/wiki/Linear_programming) problem. This can be solved by the [simplex method](https://en.wikipedia.org/wiki/Simplex_method), which usually works in [polynomial time](https://en.wikipedia.org/wiki/Polynomial_time) in the problem size but is not guaranteed to, or by [interior point methods](https://en.wikipedia.org/wiki/Interior_point_method) which are guaranteed to work in polynomial time.

#### Nonlinear programming

If the objective function or some of the constraints are nonlinear, and some constraints are inequalities, then the problem is a [nonlinear programming](https://en.wikipedia.org/wiki/Nonlinear_programming) problem.

#### Quadratic programming

If all the hard constraints are linear and some are inequalities, but the objective function is quadratic, the problem is a [quadratic programming](https://en.wikipedia.org/wiki/Quadratic_programming) problem. It is one type of nonlinear programming. It can still be solved in polynomial time by the [ellipsoid method](https://en.wikipedia.org/wiki/Ellipsoid_method) if the objective function is [convex](https://en.wikipedia.org/wiki/Convex_function); otherwise the problem may be [NP hard](https://en.wikipedia.org/wiki/NP_hard).

#### KKT conditions

Allowing inequality constraints, the [KKT approach](https://en.wikipedia.org/wiki/Karush-Kuhn-Tucker_conditions) to nonlinear programming generalizes the method of Lagrange multipliers. It can be applied under differentiability and convexity.

#### Branch and bound

Constraint optimization can be solved by [branch-and-bound](https://en.wikipedia.org/wiki/Branch-and-bound) algorithms. These are backtracking algorithms storing the cost of the best solution found during execution and using it to avoid part of the search. More precisely, whenever the algorithm encounters a partial solution that cannot be extended to form a solution of better cost than the stored best cost, the algorithm backtracks, instead of trying to extend this solution.

Assuming that cost is to be minimized, the efficiency of these algorithms depends on how the cost that can be obtained from extending a partial solution is evaluated. Indeed, if the algorithm can backtrack from a partial solution, part of the search is skipped. The lower the estimated cost, the better the algorithm, as a lower estimated cost is more likely to be lower than the best cost of solution found so far.

On the other hand, this estimated cost cannot be lower than the effective cost that can be obtained by extending the solution, as otherwise the algorithm could backtrack while a solution better than the best found so far exists. As a result, the algorithm requires an upper bound on the cost that can be obtained from extending a partial solution, and this upper bound should be as small as possible.

A variation of this approach called Hansen's method uses [interval methods](https://en.wikipedia.org/wiki/Interval_arithmetic#History). It inherently implements rectangular constraints.

#### First-choice bounding functions

One way for evaluating this upper bound for a partial solution is to consider each soft constraint separately. For each soft constraint, the maximal possible value for any assignment to the unassigned variables is assumed. The sum of these values is an upper bound because the soft constraints cannot assume a higher value. It is exact because the maximal values of soft constraints may derive from different evaluations: a soft constraint may be maximal for $x=a$ while another constraint is maximal for $x=b$.

##### Russian doll search

This method runs a branch-and-bound algorithm on $n$ problems, where $n$ is the number of variables. Each such problem is the subproblem obtained by dropping a sequence of variables $x_{1},\ldots ,x_{i}$ from the original problem, along with the constraints containing them. After the problem on variables $x_{i+1},\ldots ,x_{n}$ is solved, its optimal cost can be used as an upper bound while solving the other problems,

In particular, the cost estimate of a solution having $x_{i+1},\ldots ,x_{n}$ as unassigned variables is added to the cost that derives from the evaluated variables. Virtually, this corresponds on ignoring the evaluated variables and solving the problem on the unassigned ones, except that the latter problem has already been solved. More precisely, the cost of soft constraints containing both assigned and unassigned variables is estimated as above (or using an arbitrary other method); the cost of soft constraints containing only unassigned variables is instead estimated using the optimal solution of the corresponding problem, which is already known at this point.

There is similarity between the Russian Doll Search method and [dynamic programming](https://en.wikipedia.org/wiki/Dynamic_programming). Like dynamic programming, Russian Doll Search solves sub-problems in order to solve the whole problem. But, whereas Dynamic Programming directly combines the results obtained on sub-problems to get the result of the whole problem, Russian Doll Search only uses them as bounds during its search.

#### Bucket elimination

The [bucket elimination](https://en.wikipedia.org/wiki/Bucket_elimination) algorithm can be adapted for constraint optimization. A given variable can be indeed removed from the problem by replacing all soft constraints containing it with a new soft constraint. The cost of this new constraint is computed assuming a maximal value for every value of the removed variable. Formally, if $x$ is the variable to be removed, $C_{1},\ldots ,C_{n}$ are the soft constraints containing it, and $y_{1},\ldots ,y_{m}$ are their variables except $x$, the new soft constraint is defined by:

$C(y_{1}=a_{1},\ldots ,y_{n}=a_{n})=\max _{a}\sum _{i}C_{i}(x=a,y_{1}=a_{1},\ldots ,y_{n}=a_{n}).$

Bucket elimination works with an (arbitrary) ordering of the variables. Every variable is associated a bucket of constraints; the bucket of a variable contains all constraints having the variable has the highest in the order. Bucket elimination proceed from the last variable to the first. For each variable, all constraints of the bucket are replaced as above to remove the variable. The resulting constraint is then placed in the appropriate bucket.

## See also

- [Constrained least squares](https://en.wikipedia.org/wiki/Constrained_least_squares)
- [Distributed constraint optimization](https://en.wikipedia.org/wiki/Distributed_constraint_optimization)
- [Constraint satisfaction problem](https://en.wikipedia.org/wiki/Constraint_satisfaction_problem) (CSP)
- [Constraint programming](https://en.wikipedia.org/wiki/Constraint_programming)
- [Integer programming](https://en.wikipedia.org/wiki/Integer_programming)
- [Metric projection](https://en.wikipedia.org/wiki/Metric_projection)
- [Penalty method](https://en.wikipedia.org/wiki/Penalty_method)
- [Superiorization](https://en.wikipedia.org/wiki/Superiorization)

## References

1.  Rossi, Francesca; van Beek, Peter; Walsh, Toby (2006-01-01), Rossi, Francesca; van Beek, Peter; Walsh, Toby (eds.), ["Chapter 1 – Introduction"](http://www.sciencedirect.com/science/article/pii/S1574652606800052), *Foundations of Artificial Intelligence*, Handbook of Constraint Programming, vol. 2, Elsevier, pp. 3–12, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/s1574-6526(06)80005-2](https://doi.org/10.1016%2Fs1574-6526%2806%2980005-2), retrieved 2019-10-04
2.  Martins, J. R. R. A.; Ning, A. (2021). [Engineering Design Optimization](https://www.researchgate.net/publication/352413464). Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1108833417](https://en.wikipedia.org/wiki/Special:BookSources/978-1108833417).
3.  Wenyu Sun; Ya-Xiang Yuan (2010). *Optimization Theory and Methods: Nonlinear Programming*, Springer, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1441937650](https://en.wikipedia.org/wiki/Special:BookSources/978-1441937650). p. 541
4.  Prosser, Mike (1993). "Constrained Optimization by Substitution". *Basic Mathematics for Economists*. New York: Routledge. pp. 338–346. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-415-08424-5](https://en.wikipedia.org/wiki/Special:BookSources/0-415-08424-5).
5.  Leader, Jeffery J. (2004). *Numerical Analysis and Scientific Computation*. Addison Wesley. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-201-73499-0](https://en.wikipedia.org/wiki/Special:BookSources/0-201-73499-0).
6.  Verfaillie, Gérard, Michel Lemaître, and Thomas Schiex. "[Russian doll search for solving constraint optimization problems](https://web.archive.org/web/20180616030142/https://pdfs.semanticscholar.org/c83b/19ca9cc73aefb1a9e7b4780ba161b2149a03.pdf)." AAAI/IAAI, Vol. 1. 1996.

## Further reading

- [Bertsekas, Dimitri P.](https://en.wikipedia.org/wiki/Dimitri_Bertsekas) (1982). *Constrained Optimization and Lagrange Multiplier Methods*. New York: Academic Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-12-093480-9](https://en.wikipedia.org/wiki/Special:BookSources/0-12-093480-9).
- Dechter, Rina (2003). [Constraint Processing](https://archive.org/details/constraintproces00rina). Morgan Kaufmann. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [1-55860-890-7](https://en.wikipedia.org/wiki/Special:BookSources/1-55860-890-7).
- Madsen, K.; Nielsen, H.B.; Tingleff, O. (March 2004). [Optimization with Constraints](https://www2.imm.dtu.dk/pubdb/edoc/imm4213.pdf) (PDF) (Technical report) (2nd ed.). IMM/DTU. 4213. Retrieved Sep 6, 2025.
