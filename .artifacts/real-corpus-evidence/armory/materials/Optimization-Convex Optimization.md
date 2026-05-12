[[optimization.base]]

> Source: [[Convex Optimization]]
> License: Wikipedia content is available under CC BY-SA 4.0.

**Convex optimization** is a subfield of [mathematical optimization](https://en.wikipedia.org/wiki/Mathematical_optimization) that studies the problem of minimizing [convex functions](https://en.wikipedia.org/wiki/Convex_function) over [convex sets](https://en.wikipedia.org/wiki/Convex_set) (or, equivalently, maximizing [concave functions](https://en.wikipedia.org/wiki/Concave_functions) over convex sets). Many classes of convex optimization problems admit polynomial-time algorithms, whereas mathematical optimization is in general [NP-hard](https://en.wikipedia.org/wiki/NP-hard).

## Definition

### Abstract form

A convex optimization problem is defined by two ingredients:

- The *objective function*, which is a real-valued [convex function](https://en.wikipedia.org/wiki/Convex_function) of *n* variables, $f:{\mathcal {D}}\subseteq \mathbb {R} ^{n}\to \mathbb {R}$;
- The *feasible set*, which is a [convex subset](https://en.wikipedia.org/wiki/Convex_subset) $C\subseteq \mathbb {R} ^{n}$.

The goal of the problem is to find some $\mathbf {x^{\ast }} \in C$ attaining

$\inf\{f(\mathbf {x} ):\mathbf {x} \in C\}$.

In general, there are three options regarding the existence of a solution:

- If such a point *x*\* exists, it is referred to as an *optimal point* or *solution*; the set of all optimal points is called the *optimal set*; and the problem is called *solvable*.
- If $f$ is unbounded below over $C$, or the infimum is not attained, then the optimization problem is said to be *unbounded*.
- Otherwise, if $C$ is the empty set, then the problem is said to be *infeasible*.

### Standard form

A convex optimization problem is in *standard form* if it is written as

${\begin{aligned}&{\underset {\mathbf {x} }{\operatorname {minimize} }}&&f(\mathbf {x} )\\&\operatorname {subject\ to} &&g_{i}(\mathbf {x} )\leq 0,\quad i=1,\dots ,m\\&&&h_{i}(\mathbf {x} )=0,\quad i=1,\dots ,p,\end{aligned}}$

where:

- $\mathbf {x} \in \mathbb {R} ^{n}$ is the vector of optimization variables;
- The objective function $f:{\mathcal {D}}\subseteq \mathbb {R} ^{n}\to \mathbb {R}$ is a [convex function](https://en.wikipedia.org/wiki/Convex_function);
- The inequality constraint functions $g_{i}:\mathbb {R} ^{n}\to \mathbb {R}$, $i=1,\ldots ,m$, are convex functions;
- The equality constraint functions $h_{i}:\mathbb {R} ^{n}\to \mathbb {R}$, $i=1,\ldots ,p$, are [affine transformations](https://en.wikipedia.org/wiki/Affine_transformation), that is, of the form: $h_{i}(\mathbf {x} )=\mathbf {a_{i}} \cdot \mathbf {x} -b_{i}$, where $\mathbf {a_{i}}$ is a vector and $b_{i}$ is a scalar.

The feasible set $C$ of the optimization problem consists of all points $\mathbf {x} \in {\mathcal {D}}$ satisfying the inequality and the equality constraints. This set is convex because ${\mathcal {D}}$ is convex, the [sublevel sets](https://en.wikipedia.org/wiki/Sublevel_set) of convex functions are convex, affine sets are convex, and the intersection of convex sets is convex.

Many optimization problems can be equivalently formulated in this standard form. For example, the problem of maximizing a [concave function](https://en.wikipedia.org/wiki/Concave_function) $f$ can be re-formulated equivalently as the problem of minimizing the convex function $-f$. The problem of maximizing a concave function over a convex set is commonly called a convex optimization problem.

### Epigraph form (standard form with linear objective)

In the standard form it is possible to assume, without loss of generality, that the objective function *f* is a [linear function](https://en.wikipedia.org/wiki/Linear_function). This is because any program with a general objective can be transformed into a program with a linear objective by adding a single variable t and a single [constraint](https://en.wikipedia.org/wiki/Constraint_(mathematics) "Constraint (mathematics)"), as follows:

${\begin{aligned}&{\underset {\mathbf {x} ,t}{\operatorname {minimize} }}&&t\\&\operatorname {subject\ to} &&f(\mathbf {x} )-t\leq 0\\&&&g_{i}(\mathbf {x} )\leq 0,\quad i=1,\dots ,m\\&&&h_{i}(\mathbf {x} )=0,\quad i=1,\dots ,p,\end{aligned}}$

### Conic form

Every convex program can be presented in a *conic form*, which means minimizing a linear objective over the intersection of an affine plane and a convex cone:

${\begin{aligned}&{\underset {\mathbf {x} }{\operatorname {minimize} }}&&c^{T}x\\&\operatorname {subject\ to} &&x\in (b+L)\cap K\end{aligned}}$

where K is a closed [pointed convex cone](https://en.wikipedia.org/wiki/Convex_cone), L is a [linear subspace](https://en.wikipedia.org/wiki/Linear_subspace) of R*<sup>n</sup>*, and b is a vector in R*<sup>n</sup>*. A linear program in standard form is the special case in which K is the nonnegative orthant of R*<sup>n</sup>*.

### Eliminating linear equality constraints

It is possible to convert a convex program in standard form, to a convex program with no equality constraints. Denote the equality constraints *h<sub>i</sub>*(*x*)=0 as *Ax*=*b*, where *A* has *n* columns. If *Ax*=*b* is infeasible, then of course the original problem is infeasible. Otherwise, it has some solution *x*<sub>0</sub> , and the set of all solutions can be presented as: *Fz*+*x*<sub>0</sub>, where *z* is in *R<sup>k</sup>*, *k*=*n*-rank(*A*), and *F* is an *n*-by-*k* matrix. Substituting *x* = *Fz*+*x*<sub>0</sub> in the original problem gives:

> ${\begin{aligned}&{\underset {\mathbf {x} }{\operatorname {minimize} }}&&f(\mathbf {F\mathbf {z} +\mathbf {x} _{0}} )\\&\operatorname {subject\ to} &&g_{i}(\mathbf {F\mathbf {z} +\mathbf {x} _{0}} )\leq 0,\quad i=1,\dots ,m\\\end{aligned}}$

where the variables are **z**. Note that there are rank(*A*) fewer variables. This means that, in principle, one can restrict attention to convex optimization problems without equality constraints. In practice, however, it is often preferred to retain the equality constraints, since they might make some algorithms more efficient, and also make the problem easier to understand and analyze.

## Special cases

The following problem classes are all convex optimization problems, or can be reduced to convex optimization problems via simple transformations:

![[media/4838dafb2deda959263bcab585c82b69f58a9bfd.png]]
A hierarchy of convex optimization problems. (LP: [linear programming](https://en.wikipedia.org/wiki/Linear_programming), QP: [quadratic programming](https://en.wikipedia.org/wiki/Quadratic_programming), SOCP [second-order cone program](https://en.wikipedia.org/wiki/Second-order_cone_programming), SDP: [semidefinite programming](https://en.wikipedia.org/wiki/Semidefinite_programming), CP: [conic optimization](https://en.wikipedia.org/wiki/Conic_optimization).)

- [Linear programming](https://en.wikipedia.org/wiki/Linear_programming) problems are the simplest convex programs. In LP, the objective and constraint functions are all linear.
- [Quadratic programming](https://en.wikipedia.org/wiki/Quadratic_programming) are the next-simplest. In QP, the constraints are all linear, but the objective may be a convex quadratic function.
- [Second order cone programming](https://en.wikipedia.org/wiki/Second_order_cone_programming) are more general.
- [Semidefinite programming](https://en.wikipedia.org/wiki/Semidefinite_programming) are more general.
- [Conic optimization](https://en.wikipedia.org/wiki/Conic_optimization) are even more general - see figure to the right,

Other special cases include;

- [Least squares](https://en.wikipedia.org/wiki/Least_squares)
- [Quadratic minimization with convex quadratic constraints](https://en.wikipedia.org/wiki/Quadratically_constrained_quadratic_programming)
- [Geometric programming](https://en.wikipedia.org/wiki/Geometric_programming)
- [Entropy maximization](https://en.wikipedia.org/wiki/Entropy_maximization) with appropriate constraints.

## Properties

The following are useful properties of convex optimization problems:

- every point that is [local minimum](https://en.wikipedia.org/wiki/Local_minimum) is also a [global minimum](https://en.wikipedia.org/wiki/Global_minimum);
- the optimal set is convex;
- if the objective function is *strictly* convex, then the problem has at most one optimal point.

These results are used by the theory of convex minimization along with geometric notions from [functional analysis](https://en.wikipedia.org/wiki/Functional_analysis) (in Hilbert spaces) such as the [Hilbert projection theorem](https://en.wikipedia.org/wiki/Hilbert_projection_theorem), the [separating hyperplane theorem](https://en.wikipedia.org/wiki/Separating_hyperplane_theorem), and [Farkas' lemma](https://en.wikipedia.org/wiki/Farkas%27_lemma).<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

## Algorithms

### Unconstrained and equality-constrained problems

The convex programs easiest to solve are the *unconstrained* problems, or the problems with only equality constraints. As the equality constraints are all linear, they can be eliminated with [linear algebra](https://en.wikipedia.org/wiki/Linear_algebra) and integrated into the objective, thus converting an equality-constrained problem into an unconstrained one.

In the class of unconstrained (or equality-constrained) problems, the simplest ones are those in which the objective is [quadratic](https://en.wikipedia.org/wiki/Quadratic_programming). For these problems, the [[KKT Conditions]] (which are necessary for optimality) are all linear, so they can be solved analytically.

For unconstrained (or equality-constrained) problems with a general convex objective that is twice-differentiable, [Newton's method](https://en.wikipedia.org/wiki/Newton%27s_method_in_optimization) can be used. It can be seen as reducing a general unconstrained convex problem, to a sequence of quadratic problems.Newton's method can be combined with [[Line Search]] for an appropriate step size, and it can be mathematically proven to converge quickly.

Other efficient algorithms for unconstrained minimization are [[Gradient Descent]] (a special case of [steepest descent](https://en.wikipedia.org/wiki/Method_of_steepest_descent)).

### General problems

The more challenging problems are those with inequality constraints. A common way to solve them is to reduce them to unconstrained problems by adding a [barrier function](https://en.wikipedia.org/wiki/Barrier_function), enforcing the inequality constraints, to the objective function. Such methods are called [interior point methods](https://en.wikipedia.org/wiki/Interior_point_methods).They have to be initialized by finding a feasible interior point using by so-called *phase I* methods, which either find a feasible point or show that none exist. Phase I methods generally consist of reducing the search in question to a simpler convex optimization problem.

Convex optimization problems can also be solved by the following contemporary methods:

- [Bundle methods](https://en.wikipedia.org/wiki/Subgradient_method#Subgradient-projection_&_bundle_methods) (Wolfe, Lemaréchal, Kiwiel), and
- [Subgradient projection](https://en.wikipedia.org/wiki/Subgradient_method#Subgradient-projection_&_bundle_methods) methods (Polyak),
- [Interior-point methods](https://en.wikipedia.org/wiki/Interior-point_methods), which make use of [self-concordant](https://en.wikipedia.org/wiki/Self-concordant_function) barrier functions  and self-regular barrier functions.
- [Cutting-plane methods](https://en.wikipedia.org/wiki/Cutting-plane_methods)
- [Ellipsoid method](https://en.wikipedia.org/wiki/Ellipsoid_method)
- [Subgradient method](https://en.wikipedia.org/wiki/Subgradient_method)
- [Dual subgradients and the drift-plus-penalty method](https://en.wikipedia.org/wiki/Drift_plus_penalty)

Subgradient methods can be implemented simply and so are widely used. Dual subgradient methods are subgradient methods applied to a [dual problem](https://en.wikipedia.org/wiki/Duality_(optimization) "Duality (optimization)"). The [drift-plus-penalty](https://en.wikipedia.org/wiki/Drift_plus_penalty) method is similar to the dual subgradient method, but takes a time average of the primal variables.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

## Lagrange multipliers

Consider a convex minimization problem given in standard form by a cost function $f(x)$ and inequality constraints $g_{i}(x)\leq 0$ for $1\leq i\leq m$. Then the domain ${\mathcal {X}}$ is:

${\mathcal {X}}=\left\{x\in X\vert g_{1}(x),\ldots ,g_{m}(x)\leq 0\right\}.$

The Lagrangian function for the problem is

$L(x,\lambda _{0},\lambda _{1},\ldots ,\lambda _{m})=\lambda _{0}f(x)+\lambda _{1}g_{1}(x)+\cdots +\lambda _{m}g_{m}(x).$

For each point $x$ in $X$ that minimizes $f$ over $X$, there exist real numbers $\lambda _{0},\lambda _{1},\ldots ,\lambda _{m},$ called [[Lagrange Multipliers]], that satisfy these conditions simultaneously:

1.  $x$ minimizes $L(y,\lambda _{0},\lambda _{1},\ldots ,\lambda _{m})$ over all $y\in X,$
2.  $\lambda _{0},\lambda _{1},\ldots ,\lambda _{m}\geq 0,$ with at least one $\lambda _{k}>0,$
3.  $\lambda _{1}g_{1}(x)=\cdots =\lambda _{m}g_{m}(x)=0$ (complementary slackness).

If there exists a "strictly feasible point", that is, a point $z$ satisfying

$g_{1}(z),\ldots ,g_{m}(z)<0,$

then the statement above can be strengthened to require that $\lambda _{0}=1$.

Conversely, if some $x$ in $X$ satisfies (1)–(3) for [scalars](https://en.wikipedia.org/wiki/Scalar_(mathematics) "Scalar (mathematics)") $\lambda _{0},\ldots ,\lambda _{m}$ with $\lambda _{0}=1$ then $x$ is certain to minimize $f$ over $X$.

## Software

There is a large software ecosystem for convex optimization. This ecosystem has two main categories: *solvers* on the one hand and *modeling tools* (or *interfaces*) on the other hand.

Solvers implement the algorithms themselves and are usually written in C. They require users to specify optimization problems in very specific formats which may not be natural from a modeling perspective. Modeling tools are separate pieces of software that let the user specify an optimization in higher-level syntax. They manage all transformations to and from the user's high-level model and the solver's input/output format.

Below are two tables. The first shows modelling tools (such as CVXPY and JuMP.jl) and the second shows solvers (such as SCS and MOSEK). They are by no means exhaustive.

<table class="wikitable sortable">

Program
Language
Description
[FOSS](https://en.wikipedia.org/wiki/Free_and_open-source_software)?
<abbr title="Reference(s)">Ref.</abbr>

&#10;
CVX
[MATLAB](https://en.wikipedia.org/wiki/MATLAB)
Interfaces with SeDuMi and SDPT3 solvers; designed to only express convex optimization problems.
Yes


CVXPY
Python

Yes


Convex.jl
[Julia](https://en.wikipedia.org/wiki/Julia_(programming_language))
Disciplined convex programming, supports many solvers.
Yes


CVXR
[R](https://en.wikipedia.org/wiki/R_(programming_language))

Yes


GAMS

Modeling system for linear, nonlinear, mixed integer linear/nonlinear, and second-order cone programming problems.
No


GloptiPoly
MATLAB,
<p>Octave</p>
Modeling system for polynomial optimization.
Yes


JuMP.jl
[Julia](https://en.wikipedia.org/wiki/Julia_(programming_language))
Supports many solvers. Also supports integer and nonlinear optimization, and some nonconvex optimization.
Yes


ROME

Yes


SOSTOOLS

Yes


SparsePOP

Modeling system for polynomial optimization. Uses the SDPA or SeDuMi solvers.
Yes


YALMIP
MATLAB, Octave
Interfaces with CPLEX, GUROBI, MOSEK, SDPT3, SEDUMI, CSDP, SDPA, PENNON solvers; also supports integer and nonlinear optimization, and some nonconvex optimization. Can perform [robust optimization](https://en.wikipedia.org/wiki/Robust_optimization) with uncertainty in LP/SOCP/SDP constraints.
Yes


</table>

|  |  |  |  |  |
|----|----|----|----|----|
| Program | Language | Description | [FOSS](https://en.wikipedia.org/wiki/Free_and_open-source_software)? | Ref. |
| AIMMS |  | Can do robust optimization on linear programming (with MOSEK to solve second-order cone programming) and [mixed integer linear programming](https://en.wikipedia.org/wiki/Mixed_integer_linear_programming). Modeling package for LP + SDP and robust versions. | No |  |
| CPLEX |  | Supports primal-dual methods for LP + SOCP. Can solve LP, QP, SOCP, and mixed integer linear programming problems. | No |  |
| CSDP | [C](https://en.wikipedia.org/wiki/C_(programming_language) "C (programming language)") | Supports primal-dual methods for LP + SDP. Interfaces available for MATLAB, [R](https://en.wikipedia.org/wiki/R_(programming_language) "R (programming language)"), and Python. Parallel version available. SDP solver. | Yes |  |
| [CVXOPT](https://cvxopt.org/) | Python | Supports primal-dual methods for LP + SOCP + SDP. Uses Nesterov-Todd scaling. Interfaces to MOSEK and DSDP. | Yes |  |
| MOSEK |  | Supports primal-dual methods for LP + SOCP. | No |  |
| SeDuMi | MATLAB, Octave, [MEX](https://en.wikipedia.org/wiki/MEX_file) | Solves LP + SOCP + SDP. Supports primal-dual methods for LP + SOCP + SDP. | Yes |  |
| SDPA | [C++](https://en.wikipedia.org/wiki/C%2B%2B) | Solves LP + SDP. Supports primal-dual methods for LP + SDP. Parallelized and extended precision versions are available. | Yes |  |
| SDPT3 | MATLAB, Octave, MEX | Solves LP + SOCP + SDP. Supports primal-dual methods for LP + SOCP + SDP. | Yes |  |
| ConicBundle |  | Supports general-purpose codes for LP + SOCP + SDP. Uses a bundle method. Special support for SDP and SOCP constraints. | Yes |  |
| DSDP |  | Supports general-purpose codes for LP + SDP. Uses a dual interior point method. | Yes |  |
| LOQO |  | Supports general-purpose codes for SOCP, which it treats as a nonlinear programming problem. | No |  |
| PENNON |  | Supports general-purpose codes. Uses an augmented Lagrangian method, especially for problems with SDP constraints. | No |  |
| SDPLR |  | Supports general-purpose codes. Uses low-rank factorization with an augmented Lagrangian method. | Yes |  |

## Applications

Convex optimization can be used to model problems in a wide range of disciplines, such as automatic [control systems](https://en.wikipedia.org/wiki/Control_systems), estimation and [signal processing](https://en.wikipedia.org/wiki/Signal_processing), communications and networks, electronic [circuit design](https://en.wikipedia.org/wiki/Circuit_design), data analysis and modeling, [finance](https://en.wikipedia.org/wiki/Finance), [statistics](https://en.wikipedia.org/wiki/Statistics) ([optimal experimental design](https://en.wikipedia.org/wiki/Optimal_design)), and [structural optimization](https://en.wikipedia.org/wiki/Structural_optimization), where the approximation concept has proven to be efficient. Convex optimization can be used to model problems in the following fields:

- [Portfolio optimization](https://en.wikipedia.org/wiki/Portfolio_optimization).
- Worst-case risk analysis.
- Optimal advertising.
- Variations of [statistical regression](https://en.wikipedia.org/wiki/Regression_analysis) (including [regularization](https://en.wikipedia.org/wiki/Regularization_(mathematics) "Regularization (mathematics)") and [quantile regression](https://en.wikipedia.org/wiki/Quantile_regression)).
- Model fitting (particularly [multiclass classification](https://en.wikipedia.org/wiki/Multiclass_classification)).
- [Electricity generation](https://en.wikipedia.org/wiki/Electricity_generation) optimization.
- [Combinatorial optimization](https://en.wikipedia.org/wiki/Combinatorial_optimization).
- Non-probabilistic modelling of [uncertainty](https://en.wikipedia.org/wiki/Uncertainty).
- Localization using wireless signals 

## Extensions

## See also

- [Duality](https://en.wikipedia.org/wiki/Duality_(optimization) "Duality (optimization)")
- [Karush–Kuhn–Tucker conditions](https://en.wikipedia.org/wiki/Karush%E2%80%93Kuhn%E2%80%93Tucker_conditions)
- [Optimization problem](https://en.wikipedia.org/wiki/Optimization_problem)
- [Proximal gradient method](https://en.wikipedia.org/wiki/Proximal_gradient_method)
- [Algorithmic problems on convex sets](https://en.wikipedia.org/wiki/Algorithmic_problems_on_convex_sets)

## Notes

1.  ^   
2.  Murty, Katta; Kabadi, Santosh (1987). "Some NP-complete problems in quadratic and nonlinear programming". *Mathematical Programming*. **39** (2): 117–129. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1987MatPr..39..117M](https://ui.adsabs.harvard.edu/abs/1987MatPr..39..117M). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/BF02592948](https://doi.org/10.1007%2FBF02592948). [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[2027.42/6740](https://hdl.handle.net/2027.42%2F6740). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [30500771](https://api.semanticscholar.org/CorpusID:30500771).
3.  Sahni, S. "Computationally related problems," in SIAM Journal on Computing, 3, 262--279, 1974.
4.  Pardalos, Panos M.; Vavasis, Stephen A. (1991). ["Quadratic programming with one negative eigenvalue is NP-hard"](https://link.springer.com/article/10.1007/BF00120662). *Journal of Global Optimization*. **1**: 15–22. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/BF00120662](https://doi.org/10.1007%2FBF00120662).
5.  Hiriart-Urruty, Jean-Baptiste; Lemaréchal, Claude (1996). [Convex analysis and minimization algorithms: Fundamentals](https://books.google.com/books?id=Gdl4Jc3RVjcC&q=lemarechal+convex+analysis+and+minimization). Springer. p. 291. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9783540568506](https://en.wikipedia.org/wiki/Special:BookSources/9783540568506).
6.  Ben-Tal, Aharon; Nemirovskiĭ, Arkadiĭ Semenovich (2001). [Lectures on modern convex optimization: analysis, algorithms, and engineering applications](https://books.google.com/books?id=M3MqpEJ3jzQC&q=Lectures+on+Modern+Convex+Optimization:+Analysis,+Algorithms,). pp. 335–336. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780898714913](https://en.wikipedia.org/wiki/Special:BookSources/9780898714913).
7.  ^             Boyd, Stephen; Vandenberghe, Lieven (2004). [Convex Optimization](https://web.stanford.edu/~boyd/cvxbook/bv_cvxbook.pdf) (PDF). [Cambridge University Press](https://en.wikipedia.org/wiki/Cambridge_University_Press). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-83378-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-83378-3). Retrieved 12 Apr 2021.
8.  ["Optimization Problem Types - Convex Optimization"](https://www.solver.com/convex-optimization). 9 January 2011.
9.  ^   Arkadi Nemirovsky (2004). [Interior point polynomial-time methods in convex programming](https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=8c3cb6395a35cb504019f87f447d65cb6cf1cdf0).
10. Agrawal, Akshay; Verschueren, Robin; Diamond, Steven; Boyd, Stephen (2018). ["A rewriting system for convex optimization problems"](https://web.stanford.edu/~boyd/papers/pdf/cvxpy_rewriting.pdf) (PDF). *Control and Decision*. **5** (1): 42–60. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1709.04494](https://arxiv.org/abs/1709.04494). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/23307706.2017.1397554](https://doi.org/10.1080%2F23307706.2017.1397554). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [67856259](https://api.semanticscholar.org/CorpusID:67856259).
11. Rockafellar, R. Tyrrell (1993). ["Lagrange multipliers and optimality"](http://web.williams.edu/Mathematics/sjmiller/public_html/105Sp10/handouts/Rockafellar_LagrangeMultAndOptimality.pdf) (PDF). *SIAM Review*. **35** (2): 183–238. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1993SIAMR..35..183R](https://ui.adsabs.harvard.edu/abs/1993SIAMR..35..183R). [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.161.7209](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.161.7209). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/1035044](https://doi.org/10.1137%2F1035044).
12. For methods for convex minimization, see the volumes by Hiriart-Urruty and Lemaréchal (bundle) and the textbooks by [Ruszczyński](https://en.wikipedia.org/wiki/Andrzej_Piotr_Ruszczy%C5%84ski), [Bertsekas](https://en.wikipedia.org/wiki/Dimitri_Bertsekas), and Boyd and Vandenberghe (interior point).
13. Nesterov, Yurii; Arkadii, Nemirovskii (1995). *Interior-Point Polynomial Algorithms in Convex Programming*. Society for Industrial and Applied Mathematics. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0898715156](https://en.wikipedia.org/wiki/Special:BookSources/978-0898715156).
14. Peng, Jiming; Roos, Cornelis; Terlaky, Tamás (2002). "Self-regular functions and new search directions for linear and semidefinite optimization". *Mathematical Programming*. **93** (1): 129–171. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s101070200296](https://doi.org/10.1007%2Fs101070200296). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0025-5610](https://search.worldcat.org/issn/0025-5610). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [28882966](https://api.semanticscholar.org/CorpusID:28882966).
15. ["Numerical Optimization"](https://link.springer.com/book/10.1007/978-0-387-40065-5). *Springer Series in Operations Research and Financial Engineering*. 2006. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-0-387-40065-5](https://doi.org/10.1007%2F978-0-387-40065-5). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-30303-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-30303-1).
16. Beavis, Brian; Dobbs, Ian M. (1990). ["Static Optimization"](https://books.google.com/books?id=L7HMACFgnXMC&pg=PA40). *Optimization and Stability Theory for Economic Analysis*. New York: Cambridge University Press. p. 40. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-33605-8](https://en.wikipedia.org/wiki/Special:BookSources/0-521-33605-8).
17. ^                     Borchers, Brian. ["An Overview Of Software For Convex Optimization"](https://web.archive.org/web/20170918180026/http://infohost.nmt.edu/~borchers/presentation.pdf) (PDF). Archived from [the original](http://infohost.nmt.edu/~borchers/presentation.pdf) (PDF) on 2017-09-18. Retrieved 12 Apr 2021.
18. ["Welcome to CVXPY 1.1 — CVXPY 1.1.11 documentation"](https://www.cvxpy.org/). *www.cvxpy.org*. Retrieved 2021-04-12.
19. Udell, Madeleine; Mohan, Karanveer; Zeng, David; Hong, Jenny; Diamond, Steven; Boyd, Stephen (2014-10-17). "Convex Optimization in Julia". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1410.4821](https://arxiv.org/abs/1410.4821) \[[math.OC](https://arxiv.org/archive/math.OC)\].
20. ["Disciplined Convex Optimiation - CVXR"](https://www.cvxgrp.org/CVXR/). *www.cvxgrp.org*. Retrieved 2021-06-17.
21. Lubin, Miles; Dowson, Oscar; Dias Garcia, Joaquim; Huchette, Joey; Legat, Benoît; Vielma, Juan Pablo (2023). "JuMP 1.0: Recent improvements to a modeling language for mathematical optimization". *Mathematical Programming Computation*. **15** (3): 581–589. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2206.03866](https://arxiv.org/abs/2206.03866). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s12532-023-00239-3](https://doi.org/10.1007%2Fs12532-023-00239-3).
22. Christensen/Klarbring, chpt. 4.
23. Schmit, L.A.; Fleury, C. 1980: *Structural synthesis by combining approximation concepts and dual methods*. J. Amer. Inst. Aeronaut. Astronaut 18, 1252-1260
24. ^      Boyd, Stephen; Diamond, Stephen; Zhang, Junzi; Agrawal, Akshay. ["Convex Optimization Applications"](https://web.stanford.edu/~boyd/papers/pdf/cvx_applications.pdf) (PDF). [Archived](https://web.archive.org/web/20151001185038/http://web.stanford.edu/~boyd/papers/pdf/cvx_applications.pdf) (PDF) from the original on 2015-10-01. Retrieved 12 Apr 2021.
25. ^    Malick, Jérôme (2011-09-28). ["Convex optimization: applications, formulations, relaxations"](https://www-ljk.imag.fr//membres/Jerome.Malick/Talks/11-INRIA.pdf) (PDF). [Archived](https://web.archive.org/web/20210412044738/https://www-ljk.imag.fr//membres/Jerome.Malick/Talks/11-INRIA.pdf) (PDF) from the original on 2021-04-12. Retrieved 12 Apr 2021.
26. Ben Haim Y. and Elishakoff I., Convex Models of Uncertainty in Applied Mechanics, Elsevier Science Publishers, Amsterdam, 1990
27. [Ahmad Bazzi](https://en.wikipedia.org/wiki/Ahmad_Bazzi), Dirk TM Slock, and Lisa Meilhac. "Online angle of arrival estimation in the presence of mutual coupling." 2016 IEEE Statistical Signal Processing Workshop (SSP). IEEE, 2016.

## References

- Bertsekas, Dimitri P.; Nedic, Angelia; Ozdaglar, Asuman (2003). *Convex Analysis and Optimization*. Belmont, MA.: Athena Scientific. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-886529-45-8](https://en.wikipedia.org/wiki/Special:BookSources/978-1-886529-45-8).
- [Bertsekas, Dimitri P.](https://en.wikipedia.org/wiki/Dimitri_P._Bertsekas) (2009). *Convex Optimization Theory*. Belmont, MA.: Athena Scientific. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-886529-31-1](https://en.wikipedia.org/wiki/Special:BookSources/978-1-886529-31-1).
- [Bertsekas, Dimitri P.](https://en.wikipedia.org/wiki/Dimitri_P._Bertsekas) (2015). *Convex Optimization Algorithms*. Belmont, MA.: Athena Scientific. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-886529-28-1](https://en.wikipedia.org/wiki/Special:BookSources/978-1-886529-28-1).
- Borwein, Jonathan; Lewis, Adrian (2000). [Convex Analysis and Nonlinear Optimization: Theory and Examples, Second Edition](https://carma.newcastle.edu.au/resources/jon/Preprints/Books/CaNo2/cano2f.pdf) (PDF). Springer. Retrieved 12 Apr 2021.
- Christensen, Peter W.; Anders Klarbring (2008). [An introduction to structural optimization](https://books.google.com/books?id=80IeN__MYI8C). Vol. 153. Springer Science & Business Media. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9781402086663](https://en.wikipedia.org/wiki/Special:BookSources/9781402086663).

- Hiriart-Urruty, Jean-Baptiste, and [Lemaréchal, Claude](https://en.wikipedia.org/wiki/Claude_Lemar%C3%A9chal). (2004). *Fundamentals of Convex analysis*. Berlin: Springer.
- Hiriart-Urruty, Jean-Baptiste; [Lemaréchal, Claude](https://en.wikipedia.org/wiki/Claude_Lemar%C3%A9chal) (1993). *Convex analysis and minimization algorithms, Volume I: Fundamentals*. Grundlehren der Mathematischen Wissenschaften \[Fundamental Principles of Mathematical Sciences\]. Vol. 305. Berlin: Springer-Verlag. pp. xviii+417. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-56850-6](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-56850-6). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1261420](https://mathscinet.ams.org/mathscinet-getitem?mr=1261420).
- Hiriart-Urruty, Jean-Baptiste; [Lemaréchal, Claude](https://en.wikipedia.org/wiki/Claude_Lemar%C3%A9chal) (1993). *Convex analysis and minimization algorithms, Volume II: Advanced theory and bundle methods*. Grundlehren der Mathematischen Wissenschaften \[Fundamental Principles of Mathematical Sciences\]. Vol. 306. Berlin: Springer-Verlag. pp. xviii+346. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-56852-0](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-56852-0). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1295240](https://mathscinet.ams.org/mathscinet-getitem?mr=1295240).
- Kiwiel, Krzysztof C. (1985). [Methods of Descent for Nondifferentiable Optimization](https://archive.org/details/methodsofdescent0000kiwi). Lecture Notes in Mathematics. New York: Springer-Verlag. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-15642-0](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-15642-0).
- [Lemaréchal, Claude](https://en.wikipedia.org/wiki/Claude_Lemar%C3%A9chal) (2001). "Lagrangian relaxation". In Michael Jünger and Denis Naddef (ed.). *Computational combinatorial optimization: Papers from the Spring School held in Schloß Dagstuhl, May 15–19, 2000*. Lecture Notes in Computer Science. Vol. 2241. Berlin: Springer-Verlag. pp. 112–156. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/3-540-45586-8_4](https://doi.org/10.1007%2F3-540-45586-8_4). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-42877-0](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-42877-0). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1900016](https://mathscinet.ams.org/mathscinet-getitem?mr=1900016). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [9048698](https://api.semanticscholar.org/CorpusID:9048698).
- Nesterov, Yurii; Nemirovskii, Arkadii (1994). *Interior Point Polynomial Methods in Convex Programming*. SIAM.
- Nesterov, Yurii. (2004). *[Introductory Lectures on Convex Optimization](https://books.google.com/books?id=2-ElBQAAQBAJ&dq=%22Introductory+Lectures+on+Convex+Optimization%22&pg=PA1)*, Kluwer Academic Publishers
- [Rockafellar, R. T.](https://en.wikipedia.org/wiki/R._Tyrrell_Rockafellar) (1970). *Convex analysis*. Princeton: Princeton University Press.

- [Ruszczyński, Andrzej](https://en.wikipedia.org/wiki/Andrzej_Piotr_Ruszczy%C5%84ski) (2006). *Nonlinear Optimization*. Princeton University Press.
- Schmit, L.A.; Fleury, C. 1980: *Structural synthesis by combining approximation concepts and dual methods*. J. Amer. Inst. Aeronaut. Astronaut 18, 1252-1260

## External links

- [EE364a: Convex Optimization I](https://web.stanford.edu/class/ee364a/) and [EE364b: Convex Optimization II](https://web.stanford.edu/class/ee364b/), Stanford course homepages
- [6.253: Convex Analysis and Optimization](https://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-253-convex-analysis-and-optimization-spring-2012/lecture-notes/), an MIT OCW course homepage
- Brian Borchers, [An overview of software for convex optimization](https://web.archive.org/web/20170918180026/http://infohost.nmt.edu/~borchers/presentation.pdf)
- [Convex Optimization Book by Lieven Vandenberghe and Stephen P. Boyd](https://web.stanford.edu/~boyd/cvxbook/bv_cvxbook.pdf)
