[[geometry-manifolds.base]]

> Source: [Mathematical optimization](https://en.wikipedia.org/wiki/Mathematical_optimization)
> License: Wikipedia content is available under CC BY-SA 4.0.

![[media/4ca55d4e34104612c298ce3f310d1af9c04bc227.png]]
Graph of a surface given by <em>z</em> = f(<em>x</em>, <em>y</em>) = −(<em>x</em>² + <em>y</em>²) + 4. The global [maximum](https://en.wikipedia.org/wiki/Maximum_(mathematics)) at (<em>x, y, z</em>) = (0, 0, 4) is indicated by a blue dot.

![[media/81b19ff377a657db97555165d314d5052d352176.gif]]
Nelder-Mead minimum search of [Simionescu's function](https://en.wikipedia.org/wiki/Test_functions_for_optimization). Simplex vertices are ordered by their values, with 1 having the lowest ($f(x)$ best) value.

**Mathematical optimization** (alternatively spelled *optimisation*) or **mathematical programming** is the selection of a best element, with regard to some criteria, from some set of available alternatives. It is generally divided into two subfields: [discrete optimization](https://en.wikipedia.org/wiki/Discrete_optimization) and [continuous optimization](https://en.wikipedia.org/wiki/Continuous_optimization). Optimization problems arise in all quantitative disciplines from [computer science](https://en.wikipedia.org/wiki/Computer_science) and [engineering](https://en.wikipedia.org/wiki/Engineering) to [operations research](https://en.wikipedia.org/wiki/Operations_research) and [economics](https://en.wikipedia.org/wiki/Economics), and the development of solution methods has been of interest in [mathematics](https://en.wikipedia.org/wiki/Mathematics) for centuries.

In the more general approach, an [optimization problem](https://en.wikipedia.org/wiki/Optimization_problem) consists of [maximizing or minimizing](https://en.wikipedia.org/wiki/Maxima_and_minima) a [real function](https://en.wikipedia.org/wiki/Function_of_a_real_variable) by systematically choosing [input](https://en.wikipedia.org/wiki/Argument_of_a_function) values from within an allowed set and computing the [value](https://en.wikipedia.org/wiki/Value_(mathematics) "Value (mathematics)") of the function. The generalization of optimization theory and techniques to other formulations constitutes a large area of [applied mathematics](https://en.wikipedia.org/wiki/Applied_mathematics).

## Optimization problems

Optimization problems can be divided into two categories, depending on whether the [variables](https://en.wikipedia.org/wiki/Variable_(mathematics) "Variable (mathematics)") are [continuous](https://en.wikipedia.org/wiki/Continuous_variable) or [discrete](https://en.wikipedia.org/wiki/Discrete_variable):

- An optimization problem with discrete variables is known as a *[discrete optimization](https://en.wikipedia.org/wiki/Discrete_optimization)*, in which an [object](https://en.wikipedia.org/wiki/Mathematical_object) such as an [integer](https://en.wikipedia.org/wiki/Integer), [permutation](https://en.wikipedia.org/wiki/Permutation) or [graph](https://en.wikipedia.org/wiki/Graph_(discrete_mathematics) "Graph (discrete mathematics)") must be found from a [countable set](https://en.wikipedia.org/wiki/Countable_set).
- A problem with continuous variables is known as a *[continuous optimization](https://en.wikipedia.org/wiki/Continuous_optimization)*, in which optimal arguments from a continuous set must be found. They can include [[Constrained Optimization|constrained problems]] and multimodal problems.

An optimization problem can be represented in the following way:

*Given:* a [function](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)") $f:A\rightarrow \mathbb {R}$ from some [set](https://en.wikipedia.org/wiki/Set_(mathematics) "Set (mathematics)") A to the [real numbers](https://en.wikipedia.org/wiki/Real_number)

*Sought:* an element **x**<sub>0</sub> ∈ *A* such that *f*(**x**<sub>0</sub>) ≤ *f*(**x**) for all **x** ∈ *A* ("minimization") or such that *f*(**x**<sub>0</sub>) ≥ *f*(**x**) for all **x** ∈ *A* ("maximization").

Such a formulation is called an **[optimization problem](https://en.wikipedia.org/wiki/Optimization_problem)** or a **mathematical programming problem** (a term not directly related to [computer programming](https://en.wikipedia.org/wiki/Computer_programming), but still in use for example in [linear programming](https://en.wikipedia.org/wiki/Linear_programming) – see [History](#History) below). Many real-world and theoretical problems may be modeled in this general framework.

Since the following is valid:

$f(\mathbf {x} _{0})\geq f(\mathbf {x} )\Leftrightarrow -f(\mathbf {x} _{0})\leq -f(\mathbf {x} ),$

it suffices to solve only minimization problems. However, the opposite perspective of considering only maximization problems would be valid, too.

Problems formulated using this technique in the fields of [physics](https://en.wikipedia.org/wiki/Physics) may refer to the technique as *[energy](https://en.wikipedia.org/wiki/Energy) minimization*, speaking of the value of the function f as representing the energy of the [system](https://en.wikipedia.org/wiki/System) being [modeled](https://en.wikipedia.org/wiki/Mathematical_model). In [machine learning](https://en.wikipedia.org/wiki/Machine_learning), it is always necessary to continuously evaluate the quality of a data model by using a [cost function](https://en.wikipedia.org/wiki/Loss_function) where a minimum implies a set of possibly optimal parameters with an optimal (lowest) error.

Typically, A is some [subset](https://en.wikipedia.org/wiki/Subset) of the [Euclidean space](https://en.wikipedia.org/wiki/Euclidean_space) $\mathbb {R} ^{n}$, often specified by a set of *[constraints](https://en.wikipedia.org/wiki/Constraint_(mathematics) "Constraint (mathematics)")*, equalities or inequalities that the members of A have to satisfy. The [domain](https://en.wikipedia.org/wiki/Domain_of_a_function) A of f is called the *search space* or the *choice set*, while the elements of A are called *[candidate solutions](https://en.wikipedia.org/wiki/Candidate_solution)* or *feasible solutions*.

The function f is variously called an *objective function*, *criterion function*, *[loss function](https://en.wikipedia.org/wiki/Loss_function)*, *cost function* (minimization), *utility function* or *fitness function* (maximization), or, in certain fields, an *energy function* or *energy [functional](https://en.wikipedia.org/wiki/Functional_(mathematics) "Functional (mathematics)")*. A feasible solution that minimizes (or maximizes) the objective function is called an *optimal solution*.

In mathematics, conventional optimization problems are usually stated in terms of minimization.

A *local minimum* **x**\* is defined as an element for which there exists some *δ* \> 0 such that

$\forall \mathbf {x} \in A\;{\text{where}}\;\left\Vert \mathbf {x} -\mathbf {x} ^{\ast }\right\Vert \leq \delta ,\,$

the expression *f*(**x**\*) ≤ *f*(**x**) holds;

that is to say, on some region around **x**\* all of the function values are greater than or equal to the value at that element. Local maxima are defined similarly.

While a local minimum is at least as good as any nearby elements, a [global minimum](https://en.wikipedia.org/wiki/Global_minimum) is at least as good as every feasible element. Generally, unless the objective function is [convex](https://en.wikipedia.org/wiki/Convex_function) in a minimization problem, there may be several local minima. In a [[Convex Optimization|convex problem]], if there is a local minimum that is interior (not on the edge of the set of feasible elements), it is also the global minimum, but a nonconvex problem may have more than one local minimum not all of which need be global minima.

A large number of algorithms proposed for solving the nonconvex problems – including the majority of commercially available solvers – are not capable of making a distinction between locally optimal solutions and globally optimal solutions, and will treat the former as actual solutions to the original problem. [Global optimization](https://en.wikipedia.org/wiki/Global_optimization) is the branch of [applied mathematics](https://en.wikipedia.org/wiki/Applied_mathematics) and [numerical analysis](https://en.wikipedia.org/wiki/Numerical_analysis) that is concerned with the development of deterministic algorithms that are capable of guaranteeing convergence in finite time to the actual optimal solution of a nonconvex problem.

## Notation

Optimization problems are often expressed with special notation. Here are some examples:

### Minimum and maximum value of a function

Consider the following notation:

$\min _{x\in \mathbb {R} }\;\left(x^{2}+1\right)$

This denotes the minimum [value](https://en.wikipedia.org/wiki/Value_(mathematics) "Value (mathematics)") of the objective function *x*<sup>2</sup> + 1, when choosing x from the set of [real numbers](https://en.wikipedia.org/wiki/Real_number) $\mathbb {R}$. The minimum value in this case is 1, occurring at *x* = 0.

Similarly, the notation

$\max _{x\in \mathbb {R} }\;2x$

asks for the maximum value of the objective function 2*x*, where x may be any real number. In this case, there is no such maximum as the objective function is unbounded, so the answer is "[infinity](https://en.wikipedia.org/wiki/Infinity)" or "[undefined](https://en.wikipedia.org/wiki/Undefined_(mathematics) "Undefined (mathematics)")".

### Optimal input arguments

Consider the following notation:

${\underset {x\in (-\infty ,-1]}{\operatorname {arg\,min} }}\;x^{2}+1,$

or equivalently

${\underset {x}{\operatorname {arg\,min} }}\;x^{2}+1,\;{\text{subject to:}}\;x\in (-\infty ,-1].$

This represents the value (or values) of the [argument](https://en.wikipedia.org/wiki/Argument_of_a_function) x in the [interval](https://en.wikipedia.org/wiki/Interval_(mathematics) "Interval (mathematics)") (−∞,−1\] that minimizes (or minimize) the objective function *x*<sup>2</sup> + 1 (the actual minimum value of that function is not what the problem asks for). In this case, the answer is *x* = −1, since *x* = 0 is infeasible, that is, it does not belong to the [feasible set](https://en.wikipedia.org/wiki/Feasible_set).

Similarly,

${\underset {x\in [-5,5],\;y\in \mathbb {R} }{\operatorname {arg\,max} }}\;x\cos y,$

or equivalently

${\underset {x,\;y}{\operatorname {arg\,max} }}\;x\cos y,\;{\text{subject to:}}\;x\in [-5,5],\;y\in \mathbb {R} ,$

represents the {*x*, *y*} pair (or pairs) that maximizes (or maximize) the value of the objective function *x* cos *y*, with the added constraint that x lie in the interval \[−5,5\] (again, the actual maximum value of the expression does not matter). In this case, the solutions are the pairs of the form {5, 2*k*π} and {−5, (2*k* + 1)π}, where k ranges over all [integers](https://en.wikipedia.org/wiki/Integer).

Operators arg min and arg max are sometimes also written as argmin and argmax, and stand for *argument of the minimum* and *argument of the maximum*.

## History

[Fermat](https://en.wikipedia.org/wiki/Pierre_de_Fermat) and [Lagrange](https://en.wikipedia.org/wiki/Joseph-Louis_Lagrange) found calculus-based formulae for identifying optima, while [Newton](https://en.wikipedia.org/wiki/Isaac_Newton) and [Gauss](https://en.wikipedia.org/wiki/Carl_Friedrich_Gauss) proposed iterative methods for moving towards an optimum.

The term "[linear programming](https://en.wikipedia.org/wiki/Linear_programming)" for certain optimization cases was due to [George B. Dantzig](https://en.wikipedia.org/wiki/George_Dantzig), although much of the theory had been introduced by [Leonid Kantorovich](https://en.wikipedia.org/wiki/Leonid_Kantorovich) in 1939. (*Programming* in this context does not refer to [computer programming](https://en.wikipedia.org/wiki/Computer_programming), but comes from the use of *program* by the [United States](https://en.wikipedia.org/wiki/United_States) military to refer to proposed training and [logistics](https://en.wikipedia.org/wiki/Logistics) schedules, which were the problems Dantzig studied at that time.) Dantzig published the [Simplex algorithm](https://en.wikipedia.org/wiki/Simplex_algorithm) in 1947, and also [John von Neumann](https://en.wikipedia.org/wiki/John_von_Neumann) and other researchers worked on the theoretical aspects of linear programming (like the theory of [duality](https://en.wikipedia.org/wiki/Linear_programming#Duality)) around the same time.

Other notable researchers in mathematical optimization include the following:

- [Richard Bellman](https://en.wikipedia.org/wiki/Richard_Bellman)
- [Dimitri Bertsekas](https://en.wikipedia.org/wiki/Dimitri_Bertsekas)
- [Michel Bierlaire](https://en.wikipedia.org/wiki/Michel_Bierlaire)
- [Stephen P. Boyd](https://en.wikipedia.org/wiki/Stephen_P._Boyd)
- [Roger Fletcher](https://en.wikipedia.org/wiki/Roger_Fletcher_(mathematician) "Roger Fletcher (mathematician)")
- [Martin Grötschel](https://en.wikipedia.org/wiki/Martin_Gr%C3%B6tschel)
- [Ronald A. Howard](https://en.wikipedia.org/wiki/Ronald_A._Howard)
- [Fritz John](https://en.wikipedia.org/wiki/Fritz_John)
- [Narendra Karmarkar](https://en.wikipedia.org/wiki/Narendra_Karmarkar)
- [William Karush](https://en.wikipedia.org/wiki/William_Karush)
- [Leonid Khachiyan](https://en.wikipedia.org/wiki/Leonid_Khachiyan)
- [Bernard Koopman](https://en.wikipedia.org/wiki/Bernard_Koopman)
- [Harold Kuhn](https://en.wikipedia.org/wiki/Harold_Kuhn)
- [László Lovász](https://en.wikipedia.org/wiki/L%C3%A1szl%C3%B3_Lov%C3%A1sz)
- [David Luenberger](https://en.wikipedia.org/wiki/David_Luenberger)
- [Arkadi Nemirovski](https://en.wikipedia.org/wiki/Arkadi_Nemirovski)
- [Yurii Nesterov](https://en.wikipedia.org/wiki/Yurii_Nesterov)
- [Lev Pontryagin](https://en.wikipedia.org/wiki/Lev_Pontryagin)
- [R. Tyrrell Rockafellar](https://en.wikipedia.org/wiki/R._Tyrrell_Rockafellar)
- [Naum Z. Shor](https://en.wikipedia.org/wiki/Naum_Z._Shor)
- [Albert Tucker](https://en.wikipedia.org/wiki/Albert_W._Tucker)

## Major subfields

- [Convex programming](https://en.wikipedia.org/wiki/Convex_programming) studies the case when the objective function is [convex](https://en.wikipedia.org/wiki/Convex_function) (minimization) or [concave](https://en.wikipedia.org/wiki/Concave_function) (maximization) and the constraint set is [convex](https://en.wikipedia.org/wiki/Convex_set). This can be viewed as a particular case of nonlinear programming or as generalization of linear or convex quadratic programming.
  - [Linear programming](https://en.wikipedia.org/wiki/Linear_programming) (LP), a type of convex programming, studies the case in which the objective function *f* is linear and the constraints are specified using only linear equalities and inequalities. Such a constraint set is called a [polyhedron](https://en.wikipedia.org/wiki/Polyhedron) or a [polytope](https://en.wikipedia.org/wiki/Polytope) if it is [bounded](https://en.wikipedia.org/wiki/Bounded_set).
  - [Second-order cone programming](https://en.wikipedia.org/wiki/Second-order_cone_programming) (SOCP) is a convex program, and includes certain types of quadratic programs.
  - [Semidefinite programming](https://en.wikipedia.org/wiki/Semidefinite_programming) (SDP) is a subfield of convex optimization where the underlying variables are [semidefinite](https://en.wikipedia.org/wiki/Semidefinite) [matrices](https://en.wikipedia.org/wiki/Matrix_(mathematics) "Matrix (mathematics)"). It is a generalization of linear and convex quadratic programming.
  - [Conic programming](https://en.wikipedia.org/wiki/Conic_programming) is a general form of convex programming. LP, SOCP and SDP can all be viewed as conic programs with the appropriate type of cone.
  - [Geometric programming](https://en.wikipedia.org/wiki/Geometric_programming) is a technique whereby objective and inequality constraints expressed as [posynomials](https://en.wikipedia.org/wiki/Posynomials) and equality constraints as [monomials](https://en.wikipedia.org/wiki/Monomials) can be transformed into a convex program.
- [Integer programming](https://en.wikipedia.org/wiki/Integer_programming) studies linear programs in which some or all variables are constrained to take on [integer](https://en.wikipedia.org/wiki/Integer) values. This is not convex, and in general much more difficult than regular linear programming.
- [Quadratic programming](https://en.wikipedia.org/wiki/Quadratic_programming) allows the objective function to have quadratic terms, while the feasible set must be specified with linear equalities and inequalities. For specific forms of the quadratic term, this is a type of convex programming.
- [Fractional programming](https://en.wikipedia.org/wiki/Fractional_programming) studies optimization of ratios of two nonlinear functions. The special class of concave fractional programs can be transformed to a convex optimization problem.
- [Nonlinear programming](https://en.wikipedia.org/wiki/Nonlinear_programming) studies the general case in which the objective function or the constraints or both contain nonlinear parts. This may or may not be a convex program. In general, whether the program is convex affects the difficulty of solving it.
- [Stochastic programming](https://en.wikipedia.org/wiki/Stochastic_programming) studies the case in which some of the constraints or parameters depend on [random variables](https://en.wikipedia.org/wiki/Random_variable).
- [Robust optimization](https://en.wikipedia.org/wiki/Robust_optimization) is, like stochastic programming, an attempt to capture uncertainty in the data underlying the optimization problem. Robust optimization aims to find solutions that are valid under all possible realizations of the uncertainties defined by an uncertainty set.
- [Combinatorial optimization](https://en.wikipedia.org/wiki/Combinatorial_optimization) is concerned with problems where the set of feasible solutions is discrete or can be reduced to a [discrete](https://en.wikipedia.org/wiki/Discrete_mathematics) one.
- [Stochastic optimization](https://en.wikipedia.org/wiki/Stochastic_optimization) is used with random (noisy) function measurements or random inputs in the search process.
- [Infinite-dimensional optimization](https://en.wikipedia.org/wiki/Infinite-dimensional_optimization) studies the case when the set of feasible solutions is a subset of an infinite-[dimensional](https://en.wikipedia.org/wiki/Dimension) space, such as a space of functions.
- [Heuristics](https://en.wikipedia.org/wiki/Heuristic_(computer_science) "Heuristic (computer science)") and [metaheuristics](https://en.wikipedia.org/wiki/Metaheuristic) make few or no assumptions about the problem being optimized. Usually, heuristics do not guarantee that any optimal solution need be found. On the other hand, heuristics are used to find approximate solutions for many complicated optimization problems.
- [Constraint satisfaction](https://en.wikipedia.org/wiki/Constraint_satisfaction) studies the case in which the objective function *f* is constant (this is used in [artificial intelligence](https://en.wikipedia.org/wiki/Artificial_intelligence), particularly in [automated reasoning](https://en.wikipedia.org/wiki/Automated_reasoning)).
  - [Constraint programming](https://en.wikipedia.org/wiki/Constraint_programming) is a programming paradigm wherein relations between variables are stated in the form of constraints.
- Disjunctive programming is used where at least one constraint must be satisfied but not all. It is of particular use in scheduling.
- [Space mapping](https://en.wikipedia.org/wiki/Space_mapping) is a concept for modeling and optimization of an engineering system to high-fidelity (fine) model accuracy exploiting a suitable physically meaningful coarse or [surrogate model](https://en.wikipedia.org/wiki/Surrogate_model).

In a number of subfields, the techniques are designed primarily for optimization in dynamic contexts (that is, decision making over time):

- [Calculus of variations](https://en.wikipedia.org/wiki/Calculus_of_variations) is concerned with finding the best way to achieve some goal, such as finding a surface whose boundary is a specific curve, but with the least possible area.
- [Optimal control](https://en.wikipedia.org/wiki/Optimal_control) theory is a generalization of the calculus of variations which introduces control policies.
- [Dynamic programming](https://en.wikipedia.org/wiki/Dynamic_programming) is the approach to solve the [stochastic optimization](https://en.wikipedia.org/wiki/Stochastic_optimization) problem with stochastic, randomness, and unknown model parameters. It studies the case in which the optimization strategy is based on splitting the problem into smaller subproblems. The equation that describes the relationship between these subproblems is called the [Bellman equation](https://en.wikipedia.org/wiki/Bellman_equation).
- [Mathematical programming with equilibrium constraints](https://en.wikipedia.org/wiki/Mathematical_programming_with_equilibrium_constraints) is where the constraints include [variational inequalities](https://en.wikipedia.org/wiki/Variational_inequalities) or [complementarities](https://en.wikipedia.org/wiki/Complementarity_theory).

### Multi-objective optimization

Adding more than one objective to an optimization problem adds complexity. For example, to optimize a structural design, one would desire a design that is both light and rigid. When two objectives conflict, a trade-off must be created. There may be one lightest design, one stiffest design, and an infinite number of designs that are some compromise of weight and rigidity. The set of trade-off designs that improve upon one criterion at the expense of another is known as the [Pareto set](https://en.wikipedia.org/wiki/Pareto_set). The curve created plotting weight against stiffness of the best designs is known as the [Pareto frontier](https://en.wikipedia.org/wiki/Pareto_frontier).

A design is judged to be "Pareto optimal" (equivalently, "Pareto efficient" or in the Pareto set) if it is not dominated by any other design: If it is worse than another design in some respects and no better in any respect, then it is dominated and is not Pareto optimal.

The choice among "Pareto optimal" solutions to determine the "favorite solution" is delegated to the decision maker. In other words, defining the problem as multi-objective optimization signals that some information is missing: desirable objectives are given but combinations of them are not rated relative to each other. In some cases, the missing information can be derived by interactive sessions with the decision maker.

Multi-objective optimization problems have been generalized further into [vector optimization](https://en.wikipedia.org/wiki/Vector_optimization) problems where the (partial) ordering is no longer given by the Pareto ordering.

### Multi-modal or global optimization

Optimization problems are often multi-modal; that is, they possess multiple good solutions. They could all be globally good (same cost function value) or there could be a mix of globally good and locally good solutions. Obtaining all (or at least some of) the multiple solutions is the goal of a multi-modal optimizer.

Classical optimization techniques due to their iterative approach do not perform satisfactorily when they are used to obtain multiple solutions, since it is not guaranteed that different solutions will be obtained even with different starting points in multiple runs of the algorithm.

Common approaches to [global optimization](https://en.wikipedia.org/wiki/Global_optimization) problems, where multiple local extrema may be present include [evolutionary algorithms](https://en.wikipedia.org/wiki/Evolutionary_algorithm), [Bayesian optimization](https://en.wikipedia.org/wiki/Bayesian_optimization) and [simulated annealing](https://en.wikipedia.org/wiki/Simulated_annealing).

## Classification of critical points and extrema

### Feasibility problem

The *[satisfiability problem](https://en.wikipedia.org/wiki/Satisfiability_problem)*, also called the *feasibility problem*, is just the problem of finding any [feasible solution](https://en.wikipedia.org/wiki/Feasible_solution) at all without regard to objective value. This can be regarded as the special case of mathematical optimization where the objective value is the same for every solution, and thus any solution is optimal.

Many optimization algorithms need to start from a feasible point. One way to obtain such a point is to [relax](https://en.wikipedia.org/wiki/Relaxation_(approximation) "Relaxation (approximation)") the feasibility conditions using a [slack variable](https://en.wikipedia.org/wiki/Slack_variable); with enough slack, any starting point is feasible. Then, minimize that slack variable until the slack is null or negative.

### Existence

The [extreme value theorem](https://en.wikipedia.org/wiki/Extreme_value_theorem) of [Karl Weierstrass](https://en.wikipedia.org/wiki/Karl_Weierstrass) states that a continuous real-valued function on a compact set attains its maximum and minimum value. More generally, a lower semi-continuous function on a compact set attains its minimum; an upper semi-continuous function on a compact set attains its maximum point or view.

### Necessary conditions for optimality

[One of Fermat's theorems](https://en.wikipedia.org/wiki/Fermat%27s_theorem_(stationary_points)) states that optima of unconstrained problems are found at [stationary points](https://en.wikipedia.org/wiki/Stationary_point), where the first derivative or the gradient of the objective function is zero (see [first derivative test](https://en.wikipedia.org/wiki/First_derivative_test)). More generally, they may be found at [critical points](https://en.wikipedia.org/wiki/Critical_point_(mathematics) "Critical point (mathematics)"), where the first derivative or gradient of the objective function is zero or is undefined, or on the boundary of the choice set. An equation (or set of equations) stating that the first derivative(s) equal(s) zero at an interior optimum is called a 'first-order condition' or a set of first-order conditions.

Optima of equality-constrained problems can be found by the [Lagrange multiplier](https://en.wikipedia.org/wiki/Lagrange_multiplier) method. The optima of problems with equality and/or inequality constraints can be found using the '[Karush–Kuhn–Tucker conditions](https://en.wikipedia.org/wiki/Karush%E2%80%93Kuhn%E2%80%93Tucker_conditions)'.

### Sufficient conditions for optimality

While the first derivative test identifies points that might be extrema, this test does not distinguish a point that is a minimum from one that is a maximum or one that is neither. When the objective function is twice differentiable, these cases can be distinguished by checking the second derivative or the matrix of second derivatives (called the [[Hessian Matrix]]) in unconstrained problems, or the matrix of second derivatives of the objective function and the constraints called the [[Hessian Matrix|bordered Hessian]] in constrained problems. The conditions that distinguish maxima, or minima, from other stationary points are called 'second-order conditions' (see '[Second derivative test](https://en.wikipedia.org/wiki/Second_derivative_test)'). If a candidate solution satisfies the first-order conditions, then the satisfaction of the second-order conditions as well is sufficient to establish at least local optimality.

### Sensitivity and continuity of optima

The [envelope theorem](https://en.wikipedia.org/wiki/Envelope_theorem) describes how the value of an optimal solution changes when an underlying [parameter](https://en.wikipedia.org/wiki/Parameter) changes. The process of computing this change is called [comparative statics](https://en.wikipedia.org/wiki/Comparative_statics).

The [maximum theorem](https://en.wikipedia.org/wiki/Maximum_theorem) of [Claude Berge](https://en.wikipedia.org/wiki/Claude_Berge) (1963) describes the continuity of an optimal solution as a function of underlying parameters.

### Calculus of optimization

For unconstrained problems with twice-differentiable functions, some [critical points](https://en.wikipedia.org/wiki/Critical_point_(mathematics) "Critical point (mathematics)") can be found by finding the points where the [gradient](https://en.wikipedia.org/wiki/Gradient) of the objective function is zero (that is, the stationary points). More generally, a zero [subgradient](https://en.wikipedia.org/wiki/Subgradient) certifies that a local minimum has been found for [[Convex Optimization|minimization problems with convex]] [functions](https://en.wikipedia.org/wiki/Convex_function) and other [locally](https://en.wikipedia.org/wiki/Rademacher%27s_theorem) [Lipschitz functions](https://en.wikipedia.org/wiki/Lipschitz_function), which meet in loss function minimization of the neural network. The positive-negative momentum estimation lets to avoid the local minimum and converges at the objective function global minimum.

Further, critical points can be classified using the [[Positive-Definite Matrix|definiteness]] of the [[Hessian Matrix]]: If the Hessian is *positive* definite at a critical point, then the point is a local minimum; if the Hessian matrix is negative definite, then the point is a local maximum; finally, if indefinite, then the point is some kind of [saddle point](https://en.wikipedia.org/wiki/Saddle_point).

Constrained problems can often be transformed into unconstrained problems with the help of [Lagrange multipliers](https://en.wikipedia.org/wiki/Lagrange_multiplier). [Lagrangian relaxation](https://en.wikipedia.org/wiki/Lagrangian_relaxation) can also provide approximate solutions to difficult constrained problems.

When the objective function is a [convex function](https://en.wikipedia.org/wiki/Convex_function), then any local minimum will also be a global minimum. There exist efficient numerical techniques for minimizing convex functions, such as [interior-point methods](https://en.wikipedia.org/wiki/Interior-point_method).

### Global convergence

More generally, if the objective function is not a quadratic function, then many optimization methods use other methods to ensure that some subsequence of iterations converges to an optimal solution. The first and still popular method for ensuring convergence relies on [[Line Search|line searches]], which optimize a function along one dimension. A second and increasingly popular method for ensuring convergence uses [trust regions](https://en.wikipedia.org/wiki/Trust_region). Both line searches and trust regions are used in modern methods of [non-differentiable optimization](https://en.wikipedia.org/wiki/Subgradient_method). Usually, a global optimizer is much slower than advanced local optimizers (such as [BFGS](https://en.wikipedia.org/wiki/BFGS_method)), so often an efficient global optimizer can be constructed by starting the local optimizer from different starting points.

## Computational optimization techniques

To solve problems, researchers may use [algorithms](https://en.wikipedia.org/wiki/Algorithm) that terminate in a finite number of steps, or [iterative methods](https://en.wikipedia.org/wiki/Iterative_method) that converge to a solution (on some specified class of problems), or [heuristics](https://en.wikipedia.org/wiki/Heuristic_algorithm) that may provide approximate solutions to some problems (although their iterates need not converge).

### Optimization algorithms

- [Simplex algorithm](https://en.wikipedia.org/wiki/Simplex_algorithm) of [George Dantzig](https://en.wikipedia.org/wiki/George_Dantzig), designed for [linear programming](https://en.wikipedia.org/wiki/Linear_programming)
- Extensions of the simplex algorithm, designed for [quadratic programming](https://en.wikipedia.org/wiki/Quadratic_programming) and for [linear-fractional programming](https://en.wikipedia.org/wiki/Linear-fractional_programming)
- Variants of the simplex algorithm that are especially suited for [network optimization](https://en.wikipedia.org/wiki/Flow_network)
- [Combinatorial algorithms](https://en.wikipedia.org/wiki/Combinatorial_optimization)
- [Quantum optimization algorithms](https://en.wikipedia.org/wiki/Quantum_optimization_algorithms)

### Iterative methods

The [iterative methods](https://en.wikipedia.org/wiki/Iterative_methods) used to solve problems of [nonlinear programming](https://en.wikipedia.org/wiki/Nonlinear_programming) differ according to whether they [evaluate](https://en.wikipedia.org/wiki/Subroutine) [[Hessian Matrix|Hessians]], gradients, or only function values. While evaluating Hessians (H) and gradients (G) improves the rate of convergence, for functions for which these quantities exist and vary sufficiently smoothly, such evaluations increase the [computational complexity](https://en.wikipedia.org/wiki/Computational_complexity_theory) (or computational cost) of each iteration. In some cases, the computational complexity may be excessively high.

One major criterion for optimizers is just the number of required function evaluations as this often is already a large computational effort, usually much more effort than within the optimizer itself, which mainly has to operate over the N variables. The derivatives provide detailed information for such optimizers, but are even harder to calculate, e.g. approximating the gradient takes at least N+1 function evaluations. For approximations of the 2nd derivatives (collected in the Hessian matrix), the number of function evaluations is in the order of N². Newton's method requires the 2nd-order derivatives, so for each iteration, the number of function calls is in the order of N², but for a simpler pure gradient optimizer it is only N. However, gradient optimizers need usually more iterations than Newton's algorithm. Which one is best with respect to the number of function calls depends on the problem itself.

- Methods that evaluate Hessians (or approximate Hessians, using [finite differences](https://en.wikipedia.org/wiki/Finite_difference)):
  - [Newton's method](https://en.wikipedia.org/wiki/Newton%27s_method_in_optimization)
  - [Sequential quadratic programming](https://en.wikipedia.org/wiki/Sequential_quadratic_programming): A Newton-based method for small-medium scale *constrained* problems. Some versions can handle large-dimensional problems.
  - [Interior point methods](https://en.wikipedia.org/wiki/Interior_point_methods): This is a large class of methods for constrained optimization, some of which use only (sub)gradient information and others of which require the evaluation of Hessians.
- Methods that evaluate gradients, or approximate gradients in some way (or even subgradients):
  - [[Coordinate Descent]] methods: Algorithms which update a single coordinate in each iteration
  - [[Conjugate Gradient Method|Conjugate gradient methods]]: [Iterative methods](https://en.wikipedia.org/wiki/Iterative_method) for large problems. (In theory, these methods terminate in a finite number of steps with quadratic objective functions, but this finite termination is not observed in practice on finite–precision computers.)
  - [[Gradient Descent]] (alternatively, "steepest descent" or "steepest ascent"): A (slow) method of historical and theoretical interest, which has had renewed interest for finding approximate solutions of enormous problems.
  - [Subgradient methods](https://en.wikipedia.org/wiki/Subgradient_method): An iterative method for large [locally](https://en.wikipedia.org/wiki/Rademacher%27s_theorem) [Lipschitz functions](https://en.wikipedia.org/wiki/Lipschitz_continuity) using [generalized gradients](https://en.wikipedia.org/wiki/Subgradient). Following Boris T. Polyak, subgradient–projection methods are similar to conjugate–gradient methods.
  - Bundle method of descent: An iterative method for small–medium-sized problems with locally Lipschitz functions, particularly for [[Convex Optimization|convex minimization]] problems (similar to conjugate gradient methods).
  - [Ellipsoid method](https://en.wikipedia.org/wiki/Ellipsoid_method): An iterative method for small problems with [quasiconvex](https://en.wikipedia.org/wiki/Quasiconvex_function) objective functions and of great theoretical interest, particularly in establishing the polynomial time complexity of some combinatorial optimization problems. It has similarities with Quasi-Newton methods.
  - [Conditional gradient method (Frank–Wolfe)](https://en.wikipedia.org/wiki/Frank%E2%80%93Wolfe_algorithm) for approximate minimization of specially structured problems with [linear constraints](https://en.wikipedia.org/wiki/Linear_constraints), especially with traffic networks. For general unconstrained problems, this method reduces to the gradient method, which is regarded as obsolete (for almost all problems).
  - [Quasi-Newton methods](https://en.wikipedia.org/wiki/Quasi-Newton_method): Iterative methods for medium-large problems (e.g. N\<1000).
  - [Simultaneous perturbation stochastic approximation](https://en.wikipedia.org/wiki/Simultaneous_perturbation_stochastic_approximation) (SPSA) method for stochastic optimization; uses random (efficient) gradient approximation.
- Methods that evaluate only function values: If a problem is continuously differentiable, then gradients can be approximated using finite differences, in which case a gradient-based method can be used.
  - [Interpolation](https://en.wikipedia.org/wiki/Interpolation) methods
  - [Pattern search](https://en.wikipedia.org/wiki/Pattern_search_(optimization) "Pattern search (optimization)") methods, which have better convergence properties than the [Nelder–Mead heuristic (with simplices)](https://en.wikipedia.org/wiki/Nelder%E2%80%93Mead_method), which is listed below.
  - [Mirror descent](https://en.wikipedia.org/wiki/Mirror_descent)

### Heuristics

Besides (finitely terminating) [algorithms](https://en.wikipedia.org/wiki/Algorithm) and (convergent) [iterative methods](https://en.wikipedia.org/wiki/Iterative_method), there are [heuristics](https://en.wikipedia.org/wiki/Heuristic_algorithm). A heuristic is any algorithm which is not guaranteed (mathematically) to find the solution, but which is nevertheless useful in certain practical situations. List of some well-known heuristics:

- [Differential evolution](https://en.wikipedia.org/wiki/Differential_evolution)
- [Dynamic relaxation](https://en.wikipedia.org/wiki/Dynamic_relaxation)
- [Evolutionary algorithms](https://en.wikipedia.org/wiki/Evolutionary_algorithms)
- [Genetic algorithms](https://en.wikipedia.org/wiki/Genetic_algorithms)
- [Hill climbing](https://en.wikipedia.org/wiki/Hill_climbing) with random restart
- [Memetic algorithm](https://en.wikipedia.org/wiki/Memetic_algorithm)
- [Nelder–Mead simplicial heuristic](https://en.wikipedia.org/wiki/Nelder%E2%80%93Mead_method): A popular heuristic for approximate minimization (without calling gradients)
- [Particle swarm optimization](https://en.wikipedia.org/wiki/Particle_swarm_optimization)
- [Simulated annealing](https://en.wikipedia.org/wiki/Simulated_annealing)
- [Stochastic tunneling](https://en.wikipedia.org/wiki/Stochastic_tunneling)
- [Tabu search](https://en.wikipedia.org/wiki/Tabu_search)

## Applications

### Mechanics

Problems in [rigid body dynamics](https://en.wikipedia.org/wiki/Rigid_body_dynamics) (in particular articulated rigid body dynamics) often require mathematical programming techniques, since you can view rigid body dynamics as attempting to solve an [ordinary differential equation](https://en.wikipedia.org/wiki/Ordinary_differential_equation) on a constraint manifold; the constraints are various nonlinear geometric constraints such as "these two points must always coincide", "this surface must not penetrate any other", or "this point must always lie somewhere on this curve". Also, the problem of computing contact forces can be done by solving a [linear complementarity problem](https://en.wikipedia.org/wiki/Linear_complementarity_problem), which can also be viewed as a QP (quadratic programming) problem.

Many design problems can also be expressed as optimization programs. This application is called design optimization. One subset is the [engineering optimization](https://en.wikipedia.org/wiki/Engineering_optimization), and another recent and growing subset of this field is [multidisciplinary design optimization](https://en.wikipedia.org/wiki/Multidisciplinary_design_optimization), which, while useful in many problems, has in particular been applied to [aerospace engineering](https://en.wikipedia.org/wiki/Aerospace_engineering) problems.

This approach may be applied in cosmology and astrophysics.

### Economics and finance

[Economics](https://en.wikipedia.org/wiki/Economics) is closely enough linked to optimization of [agents](https://en.wikipedia.org/wiki/Agent_(economics) "Agent (economics)") that an influential definition relatedly describes economics *qua* science as the "study of human behavior as a relationship between ends and [scarce](https://en.wikipedia.org/wiki/Scarce) means" with alternative uses. Modern optimization theory includes traditional optimization theory but also overlaps with [game theory](https://en.wikipedia.org/wiki/Game_theory) and the study of economic [equilibria](https://en.wikipedia.org/wiki/Equilibrium_(economics)). The *[Journal of Economic Literature](https://en.wikipedia.org/wiki/Journal_of_Economic_Literature)* [codes](https://en.wikipedia.org/wiki/JEL_classification_codes) classify mathematical programming, optimization techniques, and related topics under [JEL:C61-C63](https://en.wikipedia.org/wiki/JEL_classification_codes#Mathematical_and_quantitative_methods_JEL:_C_Subcategories).

In microeconomics, the [utility maximization problem](https://en.wikipedia.org/wiki/Utility_maximization_problem) and its [dual problem](https://en.wikipedia.org/wiki/Dual_problem), the [expenditure minimization problem](https://en.wikipedia.org/wiki/Expenditure_minimization_problem), are economic optimization problems. Insofar as they behave consistently, [consumers](https://en.wikipedia.org/wiki/Consumer) are assumed to maximize their [utility](https://en.wikipedia.org/wiki/Utility), while [firms](https://en.wikipedia.org/wiki/Firm) are usually assumed to maximize their [profit](https://en.wikipedia.org/wiki/Profit_(economics) "Profit (economics)"). Also, agents are often modeled as being [risk-averse](https://en.wikipedia.org/wiki/Risk_aversion), thereby preferring to avoid risk. [Asset prices](https://en.wikipedia.org/wiki/Asset_pricing) are also modeled using optimization theory, though the underlying mathematics relies on optimizing [stochastic processes](https://en.wikipedia.org/wiki/Stochastic_process) rather than on static optimization. [International trade theory](https://en.wikipedia.org/wiki/International_trade_theory) also uses optimization to explain trade patterns between nations. The optimization of [portfolios](https://en.wikipedia.org/wiki/Portfolio_(finance) "Portfolio (finance)") is an example of multi-objective optimization in economics.

Since the 1970s, economists have modeled dynamic decisions over time using [control theory](https://en.wikipedia.org/wiki/Control_theory). For example, dynamic [search models](https://en.wikipedia.org/wiki/Search_theory) are used to study [labor-market behavior](https://en.wikipedia.org/wiki/Labor_economics). A crucial distinction is between deterministic and stochastic models. [Macroeconomists](https://en.wikipedia.org/wiki/Macroeconomics) build [dynamic stochastic general equilibrium (DSGE)](https://en.wikipedia.org/wiki/Dynamic_stochastic_general_equilibrium) models that describe the dynamics of the whole economy as the result of the interdependent optimizing decisions of workers, consumers, investors, and governments.

### Electrical engineering

Some common applications of optimization techniques in [electrical engineering](https://en.wikipedia.org/wiki/Electrical_engineering) include [active filter](https://en.wikipedia.org/wiki/Active_filter) design, stray field reduction in superconducting magnetic energy storage systems, [space mapping](https://en.wikipedia.org/wiki/Space_mapping) design of [microwave](https://en.wikipedia.org/wiki/Microwave) structures, handset antennas, electromagnetics-based design. Electromagnetically validated design optimization of microwave components and antennas has made extensive use of an appropriate physics-based or empirical [surrogate model](https://en.wikipedia.org/wiki/Surrogate_model) and [space mapping](https://en.wikipedia.org/wiki/Space_mapping) methodologies since the discovery of [space mapping](https://en.wikipedia.org/wiki/Space_mapping) in 1993. Optimization techniques are also used in [power-flow analysis](https://en.wikipedia.org/wiki/Power-flow_analysis).

### Civil engineering

Optimization has been widely used in civil engineering. [Construction management](https://en.wikipedia.org/wiki/Construction_management) and [transportation engineering](https://en.wikipedia.org/wiki/Transportation_engineering) are among the main branches of civil engineering that heavily rely on optimization. The most common civil engineering problems that are solved by optimization are cut and fill of roads, life-cycle analysis of structures and infrastructures, [resource leveling](https://en.wikipedia.org/wiki/Resource_leveling), [water resource allocation](https://en.wikipedia.org/wiki/Hydrological_optimization), [traffic](https://en.wikipedia.org/wiki/Traffic) management and schedule optimization.

### Operations research

Another field that uses optimization techniques extensively is [operations research](https://en.wikipedia.org/wiki/Operations_research). Operations research also uses stochastic modeling and simulation to support improved decision-making. Increasingly, operations research uses [stochastic programming](https://en.wikipedia.org/wiki/Stochastic_programming) to model dynamic decisions that adapt to events; such problems can be solved with large-scale optimization and [stochastic optimization](https://en.wikipedia.org/wiki/Stochastic_optimization) methods.

### Control engineering

Mathematical optimization is used in much modern controller design. High-level controllers such as [model predictive control](https://en.wikipedia.org/wiki/Model_predictive_control) (MPC) or real-time optimization (RTO) employ mathematical optimization. These algorithms run online and repeatedly determine values for decision variables, such as choke openings in a process plant, by iteratively solving a mathematical optimization problem including constraints and a model of the system to be controlled.

### Geophysics

Optimization techniques are regularly used in [geophysical](https://en.wikipedia.org/wiki/Geophysics) parameter estimation problems. Given a set of geophysical measurements, e.g. [seismic recordings](https://en.wikipedia.org/wiki/Seismology), it is common to solve for the [physical properties](https://en.wikipedia.org/wiki/Mineral_physics) and [geometrical shapes](https://en.wikipedia.org/wiki/Structure_of_the_earth) of the underlying rocks and fluids. The majority of problems in geophysics are nonlinear with both deterministic and stochastic methods being widely used.

### Molecular modeling

Nonlinear optimization methods are widely used in [conformational analysis](https://en.wikipedia.org/wiki/Conformational_analysis).

### Computational systems biology

Optimization techniques are used in many facets of computational systems biology such as model building, optimal experimental design, metabolic engineering, and synthetic biology. [Linear programming](https://en.wikipedia.org/wiki/Linear_programming) has been applied to calculate the maximal possible yields of fermentation products, and to infer gene regulatory networks from multiple microarray datasets as well as transcriptional regulatory networks from high-throughput data. [Nonlinear programming](https://en.wikipedia.org/wiki/Nonlinear_programming) has been used to analyze energy metabolism and has been applied to metabolic engineering and parameter estimation in biochemical pathways.

### Machine learning

## Solvers

## See also

- [Brachistochrone curve](https://en.wikipedia.org/wiki/Brachistochrone_curve)
- [Curve fitting](https://en.wikipedia.org/wiki/Curve_fitting)
- [Deterministic global optimization](https://en.wikipedia.org/wiki/Deterministic_global_optimization)
- [Goal programming](https://en.wikipedia.org/wiki/Goal_programming)
- [Important publications in optimization](https://en.wikipedia.org/wiki/List_of_publications_in_mathematics#Optimization)
- [Least squares](https://en.wikipedia.org/wiki/Least_squares)
- [Mathematical Optimization Society](https://en.wikipedia.org/wiki/Mathematical_Optimization_Society) (formerly Mathematical Programming Society)
- [Mathematical optimization algorithms](https://en.wikipedia.org/wiki/Category:Optimization_algorithms_and_methods)
- [Mathematical optimization software](https://en.wikipedia.org/wiki/Category:Mathematical_optimization_software)
- [Process optimization](https://en.wikipedia.org/wiki/Process_optimization)
- [Simulation-based optimization](https://en.wikipedia.org/wiki/Simulation-based_optimization)
- [Test functions for optimization](https://en.wikipedia.org/wiki/Test_functions_for_optimization)
- [Vehicle routing problem](https://en.wikipedia.org/wiki/Vehicle_routing_problem)

## Notes

1.  "[The Nature of Mathematical Programming](http://glossary.computing.society.informs.org/index.php?page=nature.html) [Archived](https://web.archive.org/web/20140305080324/http://glossary.computing.society.informs.org/index.php?page=nature.html) 2014-03-05 at the [Wayback Machine](https://en.wikipedia.org/wiki/Wayback_Machine)," *Mathematical Programming Glossary*, INFORMS Computing Society.
2.  ["Mathematical Programming: An Overview"](https://web.mit.edu/15.053/www/AppliedMathematicalProgramming.pdf) (PDF). Retrieved 26 April 2024.
3.  Martins, Joaquim R. R. A.; Ning, Andrew (2021-10-01). [Engineering Design Optimization](https://www.researchgate.net/publication/352413464). Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1108833417](https://en.wikipedia.org/wiki/Special:BookSources/978-1108833417).
4.  Du, D. Z.; Pardalos, P. M.; Wu, W. (2008). "History of Optimization". In [Floudas, C.](https://en.wikipedia.org/wiki/Christodoulos_Floudas); Pardalos, P. (eds.). *Encyclopedia of Optimization*. Boston: Springer. pp. 1538–1542.
5.  Hartmann, Alexander K; Rieger, Heiko (2002). *Optimization algorithms in physics*. Citeseer.
6.  Erwin Diewert, W. (2017), ["Cost Functions"](https://link.springer.com/referenceworkentry/10.1057/978-1-349-95121-5_659-2), *The New Palgrave Dictionary of Economics*, London: Palgrave Macmillan UK, pp. 1–12, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1057/978-1-349-95121-5_659-2](https://doi.org/10.1057%2F978-1-349-95121-5_659-2), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-349-95121-5](https://en.wikipedia.org/wiki/Special:BookSources/978-1-349-95121-5), retrieved 2024-08-18`{{`[`citation`](https://en.wikipedia.org/wiki/Template:Citation)`}}`: CS1 maint: work parameter with ISBN ([link](https://en.wikipedia.org/wiki/Category:CS1_maint:_work_parameter_with_ISBN))
7.  Bixby, Robert E (2012). ["A brief history of linear and mixed-integer programming computation"](https://doi.org/10.4171%2Fdms%2F6%2F16). *Documenta Mathematica*. Documenta Mathematica Series. **2012**: 107–121. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.4171/dms/6/16](https://doi.org/10.4171%2Fdms%2F6%2F16). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-936609-58-5](https://en.wikipedia.org/wiki/Special:BookSources/978-3-936609-58-5).
8.  Abdulkadirov, R.; Lyakhov, P.; Bergerman, M.; Reznikov, D. (February 2024). ["Satellite image recognition using ensemble neural networks and difference gradient positive-negative momentum"](https://linkinghub.elsevier.com/retrieve/pii/S0960077923013346). *Chaos, Solitons & Fractals*. **179** 114432. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2024CSF...17914432A](https://ui.adsabs.harvard.edu/abs/2024CSF...17914432A). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.chaos.2023.114432](https://doi.org/10.1016%2Fj.chaos.2023.114432).
9.  Vereshchagin, A.F. (1989). "Modelling and control of motion of manipulation robots". *Soviet Journal of Computer and Systems Sciences*. **27** (5): 29–38.
10. Haggag, S.; Desokey, F.; Ramadan, M. (2017). "A cosmological inflationary model using optimal control". *Gravitation and Cosmology*. **23** (3): 236–239. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2017GrCo...23..236H](https://ui.adsabs.harvard.edu/abs/2017GrCo...23..236H). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1134/S0202289317030069](https://doi.org/10.1134%2FS0202289317030069). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1995-0721](https://search.worldcat.org/issn/1995-0721). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [125980981](https://api.semanticscholar.org/CorpusID:125980981).
11. [Lionel Robbins](https://en.wikipedia.org/wiki/Lionel_Robbins) (1935, 2nd ed.) *[An Essay on the Nature and Significance of Economic Science](https://en.wikipedia.org/wiki/An_Essay_on_the_Nature_and_Significance_of_Economic_Science#Major_propositions)*, Macmillan, p. 16.
12. [Dorfman, Robert](https://en.wikipedia.org/wiki/Robert_Dorfman) (1969). "An Economic Interpretation of Optimal Control Theory". *[American Economic Review](https://en.wikipedia.org/wiki/American_Economic_Review)*. **59** (5): 817–831. [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [1810679](https://www.jstor.org/stable/1810679).
13. [Sargent, Thomas J.](https://en.wikipedia.org/wiki/Thomas_J._Sargent) (1987). ["Search"](https://books.google.com/books?id=nVuyXF8ibeIC&pg=PA57). *Dynamic Macroeconomic Theory*. Harvard University Press. pp. 57–91. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780674043084](https://en.wikipedia.org/wiki/Special:BookSources/9780674043084).
14. A.G. Malliaris (2008). "stochastic optimal control," *The New Palgrave Dictionary of Economics*, 2nd Edition. [Abstract](http://www.dictionaryofeconomics.com/article?id=pde2008_S000269&edition=&field=keyword&q=Taylor's%20th&topicid=&result_number=1) [Archived](https://web.archive.org/web/20171018182459/http://www.dictionaryofeconomics.com/article?id=pde2008_S000269&edition=&field=keyword&q=Taylor%27s%20th&topicid=&result_number=1) 2017-10-18 at the [Wayback Machine](https://en.wikipedia.org/wiki/Wayback_Machine).
15. [Rotemberg, Julio](https://en.wikipedia.org/wiki/Julio_Rotemberg); [Woodford, Michael](https://en.wikipedia.org/wiki/Michael_Woodford_(economist)) (1997). ["An Optimization-based Econometric Framework for the Evaluation of Monetary Policy"](http://www.nber.org/chapters/c11041.pdf) (PDF). *NBER Macroeconomics Annual*. **12**: 297–346. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/3585236](https://doi.org/10.2307%2F3585236). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [3585236](https://www.jstor.org/stable/3585236).
16. From *[The New Palgrave Dictionary of Economics](https://en.wikipedia.org/wiki/The_New_Palgrave_Dictionary_of_Economics)* (2008), 2nd Edition with Abstract links:  
    • "[numerical optimization methods in economics](http://www.dictionaryofeconomics.com/article?id=pde2008_N000148&edition=current&q=optimization&topicid=&result_number=1)" by Karl Schmedders  
    • "[convex programming](http://www.dictionaryofeconomics.com/article?id=pde2008_C000348&edition=current&q=optimization&topicid=&result_number=4)" by [Lawrence E. Blume](https://en.wikipedia.org/wiki/Lawrence_E._Blume)  
    • "[Arrow–Debreu model of general equilibrium](http://www.dictionaryofeconomics.com/article?id=pde2008_A000133&edition=current&q=optimization&topicid=&result_number=20)" by [John Geanakoplos](https://en.wikipedia.org/wiki/John_Geanakoplos).
17. De, Bishnu Prasad; Kar, R.; Mandal, D.; Ghoshal, S.P. (2014-09-27). "Optimal selection of components value for analog active filter design using simplex particle swarm optimization". *International Journal of Machine Learning and Cybernetics*. **6** (4): 621–636. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s13042-014-0299-0](https://doi.org/10.1007%2Fs13042-014-0299-0). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1868-8071](https://search.worldcat.org/issn/1868-8071). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [13071135](https://api.semanticscholar.org/CorpusID:13071135).
18. Koziel, Slawomir; Bandler, John W. (January 2008). "Space Mapping With Multiple Coarse Models for Optimization of Microwave Components". *IEEE Microwave and Wireless Components Letters*. **18** (1): 1–3. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2008IMWCL..18L1969K](https://ui.adsabs.harvard.edu/abs/2008IMWCL..18L1969K). [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.147.5407](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.147.5407). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/LMWC.2007.911969](https://doi.org/10.1109%2FLMWC.2007.911969). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [11086218](https://api.semanticscholar.org/CorpusID:11086218).
19. Tu, Sheng; Cheng, Qingsha S.; Zhang, Yifan; Bandler, John W.; [Nikolova, Natalia K.](https://en.wikipedia.org/wiki/Natalia_K._Nikolova) (July 2013). ["Space Mapping Optimization of Handset Antennas Exploiting Thin-Wire Models"](https://doi.org/10.1109%2FTAP.2013.2254695). *IEEE Transactions on Antennas and Propagation*. **61** (7): 3797–3807. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2013ITAP...61.3797T](https://ui.adsabs.harvard.edu/abs/2013ITAP...61.3797T). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/TAP.2013.2254695](https://doi.org/10.1109%2FTAP.2013.2254695).
20. N. Friedrich, [“Space mapping outpaces EM optimization in handset-antenna design,”](http://mwrf.com/software/space-mapping-outpaces-em-optimization-handset-antenna-design) microwaves&rf, August 30, 2013.
21. Cervantes-González, Juan C.; Rayas-Sánchez, José E.; López, Carlos A.; Camacho-Pérez, José R.; Brito-Brito, Zabdiel; Chávez-Hurtado, José L. (February 2016). ["Space mapping optimization of handset antennas considering EM effects of mobile phone components and human body"](https://doi.org/10.1002%2Fmmce.20945). *[International Journal of RF and Microwave Computer-Aided Engineering](https://en.wikipedia.org/wiki/International_Journal_of_RF_and_Microwave_Computer-Aided_Engineering)*. **26** (2): 121–128. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1002/mmce.20945](https://doi.org/10.1002%2Fmmce.20945). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [110195165](https://api.semanticscholar.org/CorpusID:110195165).
22. Bandler, J.W.; Biernacki, R.M.; Chen, Shao Hua; Grobelny, P.A.; Hemmers, R.H. (1994). "Space mapping technique for electromagnetic optimization". *IEEE Transactions on Microwave Theory and Techniques*. **42** (12): 2536–2544. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1994ITMTT..42.2536B](https://ui.adsabs.harvard.edu/abs/1994ITMTT..42.2536B). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/22.339794](https://doi.org/10.1109%2F22.339794).
23. Bandler, J.W.; Biernacki, R.M.; Shao Hua Chen; Hemmers, R.H.; Madsen, K. (1995). "Electromagnetic optimization exploiting aggressive space mapping". *IEEE Transactions on Microwave Theory and Techniques*. **43** (12): 2874–2882. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1995ITMTT..43.2874B](https://ui.adsabs.harvard.edu/abs/1995ITMTT..43.2874B). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/22.475649](https://doi.org/10.1109%2F22.475649).
24. *Convex relaxation of optimal power flow: A tutorial*. 2013 iREP Symposium on Bulk Power System Dynamics and Control. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/IREP.2013.6629391](https://doi.org/10.1109%2FIREP.2013.6629391).
25. Piryonesi, Sayed Madeh; Tavakolan, Mehdi (9 January 2017). ["A mathematical programming model for solving cost-safety optimization (CSO) problems in the maintenance of structures"](https://doi.org/10.1007%2Fs12205-017-0531-z). *KSCE Journal of Civil Engineering*. **21** (6): 2226–2234. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2017KSJCE..21.2226P](https://ui.adsabs.harvard.edu/abs/2017KSJCE..21.2226P). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s12205-017-0531-z](https://doi.org/10.1007%2Fs12205-017-0531-z). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [113616284](https://api.semanticscholar.org/CorpusID:113616284).
26. Hegazy, Tarek (June 1999). "Optimization of Resource Allocation and Leveling Using Genetic Algorithms". *Journal of Construction Engineering and Management*. **125** (3): 167–175. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1061/(ASCE)0733-9364(1999)125:3(167)](https://doi.org/10.1061%2F%28ASCE%290733-9364%281999%29125%3A3%28167%29).
27. Piryonesi, S. Madeh; Nasseri, Mehran; Ramezani, Abdollah (9 July 2018). "Piryonesi, S. M., Nasseri, M., & Ramezani, A. (2018). Resource leveling in construction projects with activity splitting and resource constraints: a simulated annealing optimization". *Canadian Journal of Civil Engineering*. **46**: 81–86. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1139/cjce-2017-0670](https://doi.org/10.1139%2Fcjce-2017-0670). [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[1807/93364](https://hdl.handle.net/1807%2F93364). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [116480238](https://api.semanticscholar.org/CorpusID:116480238).
28. Herty, M.; Klar, A. (2003-01-01). ["Modeling, Simulation, and Optimization of Traffic Flow Networks"](https://epubs.siam.org/doi/10.1137/S106482750241459X). *SIAM Journal on Scientific Computing*. **25** (3): 1066–1087. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2003SJSC...25.1066H](https://ui.adsabs.harvard.edu/abs/2003SJSC...25.1066H). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/S106482750241459X](https://doi.org/10.1137%2FS106482750241459X). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1064-8275](https://search.worldcat.org/issn/1064-8275).
29. ["New force on the political scene: the Seophonisten"](https://web.archive.org/web/20141218090504/http://www.seophonist-wahl.de/). Archived from [the original](http://www.seophonist-wahl.de/) on 18 December 2014. Retrieved 14 September 2013.
30. ^   Papoutsakis, Eleftherios Terry (February 1984). "Equations and calculations for fermentations of butyric acid bacteria". *Biotechnology and Bioengineering*. **26** (2): 174–187. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1984BiotB..26..174P](https://ui.adsabs.harvard.edu/abs/1984BiotB..26..174P). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1002/bit.260260210](https://doi.org/10.1002%2Fbit.260260210). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0006-3592](https://search.worldcat.org/issn/0006-3592). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [18551704](https://pubmed.ncbi.nlm.nih.gov/18551704). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [25023799](https://api.semanticscholar.org/CorpusID:25023799).
31. Wang, Yong; Joshi, Trupti; Zhang, Xiang-Sun; Xu, Dong; Chen, Luonan (2006-07-24). "Inferring gene regulatory networks from multiple microarray datasets". *Bioinformatics*. **22** (19): 2413–2420. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1093/bioinformatics/btl396](https://doi.org/10.1093%2Fbioinformatics%2Fbtl396). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1460-2059](https://search.worldcat.org/issn/1460-2059). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [16864593](https://pubmed.ncbi.nlm.nih.gov/16864593).
32. Wang, Rui-Sheng; Wang, Yong; Zhang, Xiang-Sun; Chen, Luonan (2007-09-22). ["Inferring transcriptional regulatory networks from high-throughput data"](https://doi.org/10.1093%2Fbioinformatics%2Fbtm465). *Bioinformatics*. **23** (22): 3056–3064. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1093/bioinformatics/btm465](https://doi.org/10.1093%2Fbioinformatics%2Fbtm465). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1460-2059](https://search.worldcat.org/issn/1460-2059). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [17890736](https://pubmed.ncbi.nlm.nih.gov/17890736).
33. Vo, Thuy D.; Paul Lee, W.N.; Palsson, Bernhard O. (May 2007). "Systems analysis of energy metabolism elucidates the affected respiratory chain complex in Leigh's syndrome". *Molecular Genetics and Metabolism*. **91** (1): 15–22. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.ymgme.2007.01.012](https://doi.org/10.1016%2Fj.ymgme.2007.01.012). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1096-7192](https://search.worldcat.org/issn/1096-7192). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [17336115](https://pubmed.ncbi.nlm.nih.gov/17336115).
34. [Mendes, P.](https://en.wikipedia.org/wiki/Pedro_Pedrosa_Mendes); Kell, D. (1998). ["Non-linear optimization of biochemical pathways: applications to metabolic engineering and parameter estimation"](https://doi.org/10.1093%2Fbioinformatics%2F14.10.869). *Bioinformatics*. **14** (10): 869–883. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1093/bioinformatics/14.10.869](https://doi.org/10.1093%2Fbioinformatics%2F14.10.869). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1367-4803](https://search.worldcat.org/issn/1367-4803). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [9927716](https://pubmed.ncbi.nlm.nih.gov/9927716).

## Further reading

- [Boyd, Stephen P.](https://en.wikipedia.org/wiki/Stephen_P._Boyd); Vandenberghe, Lieven (2004). [Convex Optimization](https://web.stanford.edu/~boyd/cvxbook/). Cambridge: Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-83378-7](https://en.wikipedia.org/wiki/Special:BookSources/0-521-83378-7).
- Gill, P. E.; Murray, W.; [Wright, M. H.](https://en.wikipedia.org/wiki/Margaret_H._Wright) (1982). *Practical Optimization*. London: Academic Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-12-283952-8](https://en.wikipedia.org/wiki/Special:BookSources/0-12-283952-8).
- [Lee, Jon](https://en.wikipedia.org/wiki/Jon_Lee_(mathematician) "Jon Lee (mathematician)") (2004). *A First Course in Combinatorial Optimization*. Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-01012-8](https://en.wikipedia.org/wiki/Special:BookSources/0-521-01012-8).
- [Nocedal, Jorge](https://en.wikipedia.org/wiki/Jorge_Nocedal); Wright, Stephen J. (2006). [Numerical Optimization](http://www.ece.northwestern.edu/~nocedal/book/num-opt.html) (2nd ed.). Berlin: Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-30303-0](https://en.wikipedia.org/wiki/Special:BookSources/0-387-30303-0).
- G.L. Nemhauser, A.H.G. Rinnooy Kan and M.J. Todd (eds.): *Optimization*, Elsevier, (1989).
- Stanislav Walukiewicz：*Integer Programming*, Springer，ISBN 978-9048140688, (1990).
- R. Fletcher: *Practical Methods of Optimization*, 2nd Ed., Wiley, (2000).
- Panos M. Pardalos：*Approximation and Complexity in Numerical Optimization: Continuous and Discrete Problems*, Springer，ISBN 978-1-44194829-8, (2000).
- Xiaoqi Yang, K. L. Teo, Lou Caccetta (Eds.)：*Optimization Methods and Applications*，Springer, ISBN 978-0-79236866-3, (2001).
- Panos M. Pardalos, and Mauricio G. C. Resende(Eds.)：*Handbook of Applied Optimization*、Oxford Univ Pr on Demand, ISBN 978-0-19512594-8, (2002).
- Wil Michiels, Emile Aarts, and Jan Korst: *Theoretical Aspects of Local Search*, Springer, ISBN 978-3-64207148-5, (2006).
- Der-San Chen, Robert G. Batson, and Yu Dang： *Applied Integer Programming: Modeling and Solution*，Wiley，ISBN 978-0-47037306-4, (2010).
- [Mykel J. Kochenderfer and Tim A. Wheeler: Algorithms for Optimization, The MIT Press, ISBN 978-0-26203942-0, (2019).](https://algorithmsbook.com/optimization/)
- Vladislav Bukshtynov: *Optimization: Success in Practice*, CRC Press (Taylor & Francis), ISBN 978-1-03222947-8, (2023) .
- Rosario Toscano: *Solving Optimization Problems with the Heuristic Kalman Algorithm: New Stochastic Methods*, Springer, ISBN 978-3-031-52458-5 (2024).
- Immanuel M. Bomze, Tibor Csendes, Reiner Horst and Panos M. Pardalos: *Developments in Global Optimization*, Kluwer Academic, ISBN 978-1-4419-4768-0 (2010).

## External links

- ["Decision Tree for Optimization Software"](http://plato.asu.edu/guide.html). Links to optimization source codes
- ["Global optimization"](https://web.archive.org/web/20220129065120/https://www.mat.univie.ac.at/~neum/glopt.html). Archived from [the original](https://www.mat.univie.ac.at/~neum/glopt.html) on 2022-01-29. Retrieved 2019-05-18.
- ["EE364a: Convex Optimization I"](https://see.stanford.edu/Course/EE364A). *Course from Stanford University*.
- Varoquaux, Gaël. ["Mathematical Optimization: Finding Minima of Functions"](https://scipy-lectures.org/advanced/mathematical_optimization/index.html).
