[[optimization.base]]

> Source: [Karush–Kuhn–Tucker conditions](https://en.wikipedia.org/wiki/Karush%E2%80%93Kuhn%E2%80%93Tucker_conditions)
> License: Wikipedia content is available under CC BY-SA 4.0.

In [mathematical optimization](https://en.wikipedia.org/wiki/Mathematical_optimization), the **Karush–Kuhn–Tucker** (**KKT**) **conditions**, also known as the **Kuhn–Tucker conditions**, are [first derivative tests](https://en.wikipedia.org/wiki/First-order_condition) (sometimes called first-order [necessary conditions](https://en.wikipedia.org/wiki/Necessary_and_sufficient_conditions)) for a solution in [nonlinear programming](https://en.wikipedia.org/wiki/Nonlinear_programming) to be [optimal](https://en.wikipedia.org/wiki/Optimization_(mathematics)), provided that some [regularity conditions](#Regularity_conditions_(or_constraint_qualifications)) are satisfied.

Allowing inequality constraints, the KKT approach to nonlinear programming generalizes the method of [[Lagrange Multipliers]], which allows only equality constraints. Similar to the Lagrange approach, the [[Constrained Optimization|constrained maximization]] (minimization) problem is rewritten as a Lagrange function whose optimal point is a [global maximum](https://en.wikipedia.org/wiki/Global_maximum) or minimum over the domain of the choice variables and a global minimum (maximum) over the multipliers. The Karush–Kuhn–Tucker theorem is sometimes referred to as the [saddle-point](https://en.wikipedia.org/wiki/Saddle_point) theorem.

The KKT conditions were originally named after [Harold W. Kuhn](https://en.wikipedia.org/wiki/Harold_W._Kuhn) and [Albert W. Tucker](https://en.wikipedia.org/wiki/Albert_W._Tucker), who first published the conditions in 1951. Later scholars discovered that the necessary conditions for this problem had been stated in an unpublished master's thesis by [William Karush](https://en.wikipedia.org/wiki/William_Karush) in 1939.

## Nonlinear optimization problem

Consider the following nonlinear optimization problem in [standard form](https://en.wikipedia.org/wiki/Optimization_problem#Continuous_optimization_problem):

minimize $f(\mathbf {x} )$

subject to

$g_{i}(\mathbf {x} )\leq 0,$

$h_{j}(\mathbf {x} )=0.$

where $\mathbf {x} \in \mathbf {X}$ is the optimization variable chosen from a [convex subset](https://en.wikipedia.org/wiki/Convex_set) of $\mathbb {R} ^{n}$, $f$ is the [objective](https://en.wikipedia.org/wiki/Objective_function) or [utility](https://en.wikipedia.org/wiki/Utility) function, $g_{i}\ (i=1,\ldots ,m)$ are the inequality [constraint](https://en.wikipedia.org/wiki/Constraint_(mathematics) "Constraint (mathematics)") functions and $h_{j}\ (j=1,\ldots ,\ell )$ are the equality [constraint](https://en.wikipedia.org/wiki/Constraint_(mathematics) "Constraint (mathematics)") functions. The numbers of inequalities and equalities are denoted by $m$ and $\ell$ respectively. Corresponding to the [[Constrained Optimization]] problem one can form the [Lagrangian function](https://en.wikipedia.org/wiki/Lagrangian_function)

$$
{\mathcal {L}}(\mathbf {x} ,\mathbf {\mu } ,\mathbf {\lambda } )=f(\mathbf {x} )+\mathbf {\mu } ^{\top }\mathbf {g} (\mathbf {x} )+\mathbf {\lambda } ^{\top }\mathbf {h} (\mathbf {x} )=L(\mathbf {x} ,\mathbf {\alpha } )=f(\mathbf {x} )+\mathbf {\alpha } ^{\top }{\begin{pmatrix}\mathbf {g} (\mathbf {x} )\\\mathbf {h} (\mathbf {x} )\end{pmatrix}}
$$

where

$$
\mathbf {g} \left(\mathbf {x} \right)={\begin{bmatrix}g_{1}\left(\mathbf {x} \right)\\\vdots \\g_{i}\left(\mathbf {x} \right)\\\vdots \\g_{m}\left(\mathbf {x} \right)\end{bmatrix}},\quad \mathbf {h} \left(\mathbf {x} \right)={\begin{bmatrix}h_{1}\left(\mathbf {x} \right)\\\vdots \\h_{j}\left(\mathbf {x} \right)\\\vdots \\h_{\ell }\left(\mathbf {x} \right)\end{bmatrix}},\quad \mathbf {\mu } ={\begin{bmatrix}\mu _{1}\\\vdots \\\mu _{i}\\\vdots \\\mu _{m}\\\end{bmatrix}},\quad \mathbf {\lambda } ={\begin{bmatrix}\lambda _{1}\\\vdots \\\lambda _{j}\\\vdots \\\lambda _{\ell }\end{bmatrix}}\quad {\text{and}}\quad \mathbf {\alpha } ={\begin{bmatrix}\mu \\\lambda \end{bmatrix}}.
$$

 The **Karush–Kuhn–Tucker theorem** then states the following.

**Theorem**—(sufficiency) If $(\mathbf {x} ^{\ast },\mathbf {\alpha } ^{\ast })$ is a [saddle point](https://en.wikipedia.org/wiki/Saddle_point) of $L(\mathbf {x} ,\mathbf {\alpha } )$ in $\mathbf {x} \in \mathbf {X}$, $\mathbf {\mu } \geq \mathbf {0}$, then $\mathbf {x} ^{\ast }$ is an optimal vector for the above optimization problem.

(necessity) Suppose that $f(\mathbf {x} )$ and $g_{i}(\mathbf {x} )$, $i=1,\ldots ,m$, are [convex](https://en.wikipedia.org/wiki/Convex_function) in $\mathbf {X}$ and that there exists $\mathbf {x} _{0}\in \operatorname {relint} (\mathbf {X} )$ such that $\mathbf {g} (\mathbf {x} _{0})<\mathbf {0}$ (i.e., [Slater's condition](https://en.wikipedia.org/wiki/Slater%27s_condition) holds). Then with an optimal vector $\mathbf {x} ^{\ast }$ for the above optimization problem there is associated a vector $\mathbf {\alpha } ^{\ast }={\begin{bmatrix}\mu ^{*}\\\lambda ^{*}\end{bmatrix}}$ satisfying $\mathbf {\mu } ^{*}\geq \mathbf {0}$ such that $(\mathbf {x} ^{\ast },\mathbf {\alpha } ^{\ast })$ is a saddle point of $L(\mathbf {x} ,\mathbf {\alpha } )$.

Since the idea of this approach is to find a [supporting hyperplane](https://en.wikipedia.org/wiki/Supporting_hyperplane) on the feasible set $\mathbf {\Gamma } =\left\{\mathbf {x} \in \mathbf {X} :g_{i}(\mathbf {x} )\leq 0,i=1,\ldots ,m\right\}$, the proof of the Karush–Kuhn–Tucker theorem makes use of the [hyperplane separation theorem](https://en.wikipedia.org/wiki/Hyperplane_separation_theorem).

The system of equations and inequalities corresponding to the KKT conditions is usually not solved directly, except in the few special cases where a [closed-form](https://en.wikipedia.org/wiki/Closed-form_expression) solution can be derived analytically. In general, many optimization algorithms can be interpreted as methods for [numerically solving](https://en.wikipedia.org/wiki/Numerical_analysis) the KKT system of equations and inequalities.

## Necessary conditions

Suppose that the [objective function](https://en.wikipedia.org/wiki/Objective_function) $f\colon \mathbb {R} ^{n}\rightarrow \mathbb {R}$ and the constraint functions $g_{i}\colon \mathbb {R} ^{n}\rightarrow \mathbb {R}$ and $h_{j}\colon \mathbb {R} ^{n}\rightarrow \mathbb {R}$ have [subderivatives](https://en.wikipedia.org/wiki/Subderivative) at a point $x^{*}\in \mathbb {R} ^{n}$. If $x^{*}$ is a [local optimum](https://en.wikipedia.org/wiki/Local_optimum) and the optimization problem satisfies some regularity conditions (see below), then there exist constants $\mu _{i}\ (i=1,\ldots ,m)$ and $\lambda _{j}\ (j=1,\ldots ,\ell )$, called KKT multipliers, such that the following four groups of conditions hold:

![[media/fae042ca10ec27c2608ebba47742e9a87514062e.png]]
Inequality constraint diagram for optimization problems

Stationarity  
For minimizing $f(x)$: $\partial f(x^{*})+\sum _{j=1}^{\ell }\lambda _{j}\partial h_{j}(x^{*})+\sum _{i=1}^{m}\mu _{i}\partial g_{i}(x^{*})\ni \mathbf {0}$

For maximizing $f(x)$: $-\partial f(x^{*})+\sum _{j=1}^{\ell }\lambda _{j}\partial h_{j}(x^{*})+\sum _{i=1}^{m}\mu _{i}\partial g_{i}(x^{*})\ni \mathbf {0}$

Primal feasibility  
$h_{j}(x^{*})=0,{\text{ for }}j=1,\ldots ,\ell \,\!$

$g_{i}(x^{*})\leq 0,{\text{ for }}i=1,\ldots ,m$

Dual feasibility  
$\mu _{i}\geq 0,{\text{ for }}i=1,\ldots ,m$

Complementary slackness  
$\sum _{i=1}^{m}\mu _{i}g_{i}(x^{*})=0.$

The last condition is sometimes written in the equivalent form: $\mu _{i}g_{i}(x^{*})=0,{\text{ for }}i=1,\ldots ,m.$

In the particular case $m=0$, i.e., when there are no inequality constraints, the KKT conditions turn into the Lagrange conditions, and the KKT multipliers are called [[Lagrange Multipliers]].

### Interpretation: KKT conditions as balancing constraint-forces in state space

The primal problem can be interpreted as moving a particle in the space of $x$, and subjecting it to three kinds of force fields:

- $f$ is a potential field that the particle is minimizing. The force generated by $f$ is $-\partial f$.
- $g_{i}$ are one-sided constraint surfaces. The particle is allowed to move inside $g_{i}\leq 0$, but whenever it touches $g_{i}=0$, it is pushed inwards.
- $h_{j}$ are two-sided constraint surfaces. The particle is allowed to move only on the surface $h_{j}$.

Primal stationarity states that the "force" of $\partial f(x^{*})$ is exactly balanced by a linear sum of forces $\partial h_{j}(x^{*})$ and $\partial g_{i}(x^{*})$.

Dual feasibility additionally states that all the $\partial g_{i}(x^{*})$ forces must be one-sided, pointing inwards into the [feasible set](https://en.wikipedia.org/wiki/Feasible_region) for $x$.

Complementary slackness states that if $g_{i}(x^{*})<0$, then the force coming from $\partial g_{i}(x^{*})$ must be zero i.e., $\mu _{i}(x^{*})=0$, since the particle is not on the boundary, the one-sided constraint force cannot activate.

### Matrix representation

The necessary conditions can be written with [Jacobian matrices](https://en.wikipedia.org/wiki/Jacobian_matrix_and_determinant) of the constraint functions. Let $\mathbf {g} (x):\,\!\mathbb {R} ^{n}\rightarrow \mathbb {R} ^{m}$ be defined as $\mathbf {g} (x)=\left(g_{1}(x),\ldots ,g_{m}(x)\right)^{\top }$ and let $\mathbf {h} (x):\,\!\mathbb {R} ^{n}\rightarrow \mathbb {R} ^{\ell }$ be defined as $\mathbf {h} (x)=\left(h_{1}(x),\ldots ,h_{\ell }(x)\right)^{\top }$. Let ${\boldsymbol {\mu }}=\left(\mu _{1},\ldots ,\mu _{m}\right)^{\top }$ and ${\boldsymbol {\lambda }}=\left(\lambda _{1},\ldots ,\lambda _{\ell }\right)^{\top }$. Then the necessary conditions can be written as:

Stationarity  
For maximizing $f(x)$: $\partial f(x^{*})-D\mathbf {g} (x^{*})^{\top }{\boldsymbol {\mu }}-D\mathbf {h} (x^{*})^{\top }{\boldsymbol {\lambda }}=\mathbf {0}$

For minimizing $f(x)$: $\partial f(x^{*})+D\mathbf {g} (x^{*})^{\top }{\boldsymbol {\mu }}+D\mathbf {h} (x^{*})^{\top }{\boldsymbol {\lambda }}=\mathbf {0}$

Primal feasibility  
$\mathbf {g} (x^{*})\leq \mathbf {0}$

$\mathbf {h} (x^{*})=\mathbf {0}$

Dual feasibility  
${\boldsymbol {\mu }}\geq \mathbf {0}$

Complementary slackness  
${\boldsymbol {\mu }}^{\top }\mathbf {g} (x^{*})=0.$

## Regularity conditions (or constraint qualifications)

One can ask whether a minimizer point $x^{*}$ of the original, constrained optimization problem (assuming one exists) has to satisfy the above KKT conditions. This is similar to asking under what conditions the minimizer $x^{*}$ of a function $f(x)$ in an unconstrained problem has to satisfy the condition $\nabla f(x^{*})=0$. For the constrained case, the situation is more complicated, and one can state a variety of (increasingly complicated) "regularity" conditions under which a constrained minimizer also satisfies the KKT conditions. Some common examples for conditions that guarantee this are tabulated in the following, with the LICQ the most frequently used one:

|  |  |  |
|----|----|----|
| Constraint | Acronym | Statement |
| Linearity constraint qualification | LCQ | If $g_{i}$ and $h_{j}$ are [affine functions](https://en.wikipedia.org/wiki/Affine_function), then no other condition is needed. |
| Linear independence constraint qualification | LICQ | The gradients of the active inequality constraints and the gradients of the equality constraints are [[Linear Independence|linearly independent]] at $x^{*}$. |
| Mangasarian–Fromovitz constraint qualification | MFCQ | The gradients of the equality constraints are linearly independent at $x^{*}$ and there exists a vector $d\in \mathbb {R} ^{n}$ such that $\nabla g_{i}(x^{*})^{\top }d<0$ for all active inequality constraints and $\nabla h_{j}(x^{*})^{\top }d=0$ for all equality constraints. |
| [Constant rank constraint qualification](https://en.wikipedia.org/wiki/Constant_rank_theorem) | CRCQ | For each subset of the gradients of the active inequality constraints and the gradients of the equality constraints the rank at a vicinity of $x^{*}$ is constant. |
| Constant positive linear dependence constraint qualification | CPLD | For each subset of gradients of active inequality constraints and gradients of equality constraints, if the subset of vectors is linearly dependent at $x^{*}$ with non-negative scalars associated with the inequality constraints, then it remains linearly dependent in a neighborhood of $x^{*}$. |
| Quasi-normality constraint qualification | QNCQ | If the gradients of the active inequality constraints and the gradients of the equality constraints are linearly dependent at $x^{*}$ with associated multipliers $\lambda _{j}$ for equalities and $\mu _{i}\geq 0$ for inequalities, then there is no sequence $x_{k}\to x^{*}$ such that $\lambda _{j}\neq 0\Rightarrow \lambda _{j}h_{j}(x_{k})>0$ and $\mu _{i}\neq 0\Rightarrow \mu _{i}g_{i}(x_{k})>0.$ |
| [Slater's condition](https://en.wikipedia.org/wiki/Slater_condition) | SC | For a [[Convex Optimization|convex problem]] (i.e., assuming minimization, $f,g_{i}$ are convex and $h_{j}$ is affine), there exists a point $x$ such that $h_{j}(x)=0$ and $g_{i}(x)<0.$ |

The strict implications can be shown

LICQ ⇒ MFCQ ⇒ CPLD ⇒ QNCQ

and

LICQ ⇒ CRCQ ⇒ CPLD ⇒ QNCQ

In practice weaker constraint qualifications are preferred since they apply to a broader selection of problems.

## Sufficient conditions

In some cases, the necessary conditions are also sufficient for optimality. In general, the necessary conditions are not sufficient for optimality and additional information is required, such as the Second Order Sufficient Conditions (SOSC). For smooth functions, SOSC involve the second derivatives, which explains its name.

The necessary conditions are sufficient for optimality if the objective function $f$ of a maximization problem is a differentiable [concave function](https://en.wikipedia.org/wiki/Concave_function), the inequality constraints $g_{j}$ are differentiable [convex functions](https://en.wikipedia.org/wiki/Convex_function), the equality constraints $h_{i}$ are [affine functions](https://en.wikipedia.org/wiki/Affine_function), and [Slater's condition](https://en.wikipedia.org/wiki/Slater%27s_condition) holds. Similarly, if the objective function $f$ of a minimization problem is a differentiable [convex function](https://en.wikipedia.org/wiki/Convex_function), the necessary conditions are also sufficient for optimality.

It was shown by Martin in 1985 that the broader class of functions in which KKT conditions guarantees global optimality are the so-called Type 1 **[invex functions](https://en.wikipedia.org/wiki/Invex_function)**.

### Second-order sufficient conditions

For smooth, [non-linear optimization](https://en.wikipedia.org/wiki/Nonlinear_programming) problems, a second order sufficient condition is given as follows.

The solution $x^{*},\lambda ^{*},\mu ^{*}$ found in the above section is a constrained local minimum if for the Lagrangian,

$L(x,\lambda ,\mu )=f(x)+\sum _{i=1}^{m}\mu _{i}g_{i}(x)+\sum _{j=1}^{\ell }\lambda _{j}h_{j}(x)$

then,

$s^{T}\nabla _{xx}^{2}L(x^{*},\lambda ^{*},\mu ^{*})s\geq 0$

where $s\neq 0$ is a vector satisfying the following,

$\left[\nabla _{x}g_{i}(x^{*}),\nabla _{x}h_{j}(x^{*})\right]^{T}s=0_{\mathbb {R} ^{2}}$

where only those active inequality constraints $g_{i}(x)$ corresponding to strict complementarity (i.e. where $\mu _{i}>0$) are applied. The solution is a strict constrained local minimum in the case the inequality is also strict.

If $s^{T}\nabla _{xx}^{2}L(x^{*},\lambda ^{*},\mu ^{*})s=0$, the third order Taylor expansion of the Lagrangian should be used to verify if $x^{*}$ is a local minimum. The minimization of $f(x_{1},x_{2})=(x_{2}-x_{1}^{2})(x_{2}-3x_{1}^{2})$ is a good counter-example, see also [Peano surface](https://en.wikipedia.org/wiki/Peano_surface).

## Economics

Often in [mathematical economics](https://en.wikipedia.org/wiki/Mathematical_economics) the KKT approach is used in theoretical models in order to obtain qualitative results. For example, consider a firm that maximizes its sales revenue subject to a minimum profit constraint. Letting $Q$ be the quantity of output produced (to be chosen), $R(Q)$ be sales revenue with a positive first derivative and with a zero value at zero output, $C(Q)$ be production costs with a positive first derivative and with a non-negative value at zero output, and $G_{\min }$ be the positive minimal acceptable level of [profit](https://en.wikipedia.org/wiki/Profit_(economics) "Profit (economics)"), then the problem is a meaningful one if the revenue function levels off so it eventually is less steep than the cost function. The problem expressed in the previously given minimization form is

Minimize $-R(Q)$

subject to

$G_{\min }\leq R(Q)-C(Q)$

$Q\geq 0,$

and the KKT conditions are

${\begin{aligned}&\left({\frac {{\text{d}}R}{{\text{d}}Q}}\right)(1+\mu )-\mu \left({\frac {{\text{d}}C}{{\text{d}}Q}}\right)\leq 0,\\[5pt]&Q\geq 0,\\[5pt]&Q\left[\left({\frac {{\text{d}}R}{{\text{d}}Q}}\right)(1+\mu )-\mu \left({\frac {{\text{d}}C}{{\text{d}}Q}}\right)\right]=0,\\[5pt]&R(Q)-C(Q)-G_{\min }\geq 0,\\[5pt]&\mu \geq 0,\\[5pt]&\mu [R(Q)-C(Q)-G_{\min }]=0.\end{aligned}}$

Since $Q=0$ would violate the minimum profit constraint, we have $Q>0$ and hence the third condition implies that the first condition holds with equality. Solving that equality gives

${\frac {{\text{d}}R}{{\text{d}}Q}}={\frac {\mu }{1+\mu }}\left({\frac {{\text{d}}C}{{\text{d}}Q}}\right).$

Because it was given that ${\text{d}}R/{\text{d}}Q$ and ${\text{d}}C/{\text{d}}Q$ are strictly positive, this inequality along with the non-negativity condition on $\mu$ guarantees that $\mu$ is positive and so the revenue-maximizing firm operates at a level of output at which [marginal revenue](https://en.wikipedia.org/wiki/Marginal_revenue) ${\text{d}}R/{\text{d}}Q$ is less than [marginal cost](https://en.wikipedia.org/wiki/Marginal_cost) ${\text{d}}C/{\text{d}}Q$ — a result that is of interest because it contrasts with the behavior of a [profit maximizing](https://en.wikipedia.org/wiki/Profit_maximization) firm, which operates at a level at which they are equal.

## Value function

If we reconsider the optimization problem as a maximization problem with constant inequality constraints:

${\text{Maximize }}\;f(x)$

${\text{subject to }}\$

$g_{i}(x)\leq a_{i},h_{j}(x)=0.$

The [value function](https://en.wikipedia.org/wiki/Value_function) is defined as

$V(a_{1},\ldots ,a_{n})=\sup \limits _{x}f(x)$

${\text{subject to }}\$

$g_{i}(x)\leq a_{i},h_{j}(x)=0$

$j\in \{1,\ldots ,\ell \},i\in \{1,\ldots ,m\},$

so the domain of $V$ is $\{a\in \mathbb {R} ^{m}\mid {\text{for some }}x\in X,g_{i}(x)\leq a_{i},i\in \{1,\ldots ,m\}\}.$

Given this definition, each coefficient $\mu _{i}$ is the rate at which the value function increases as $a_{i}$ increases. Thus if each $a_{i}$ is interpreted as a resource constraint, the coefficients tell you how much increasing a resource will increase the optimum value of our function $f$. This interpretation is especially important in economics and is used, for instance, in [utility maximization problems](https://en.wikipedia.org/wiki/Utility_maximization_problem).

## Generalizations

With an extra multiplier $\mu _{0}\geq 0$, which may be zero (as long as $(\mu _{0},\mu ,\lambda )\neq 0$), in front of $\nabla f(x^{*})$ the KKT stationarity conditions turn into

${\begin{aligned}&\mu _{0}\,\nabla f(x^{*})+\sum _{i=1}^{m}\mu _{i}\,\nabla g_{i}(x^{*})+\sum _{j=1}^{\ell }\lambda _{j}\,\nabla h_{j}(x^{*})=0,\\[4pt]&\mu _{j}g_{i}(x^{*})=0,\quad i=1,\dots ,m,\end{aligned}}$

which are called the [Fritz John conditions](https://en.wikipedia.org/wiki/Fritz_John_conditions). This optimality conditions holds without constraint qualifications and it is equivalent to the optimality condition *KKT or (not-MFCQ)*.

The KKT conditions belong to a wider class of the first-order necessary conditions (FONC), which allow for non-smooth functions using [subderivatives](https://en.wikipedia.org/wiki/Subderivative).

## See also

- [Farkas' lemma](https://en.wikipedia.org/wiki/Farkas%27_lemma)
- [Lagrange multiplier](https://en.wikipedia.org/wiki/Lagrange_multiplier)
- The [Big M method](https://en.wikipedia.org/wiki/Big_M_method), for linear problems, which extends the [simplex algorithm](https://en.wikipedia.org/wiki/Simplex_algorithm) to problems that contain "greater-than" constraints.
- [Interior-point method](https://en.wikipedia.org/wiki/Interior-point_method), a method to solve the KKT conditions.
- [Slack variable](https://en.wikipedia.org/wiki/Slack_variable)
- [Slater's condition](https://en.wikipedia.org/wiki/Slater%27s_condition)

## References

1.  Tabak, Daniel; Kuo, Benjamin C. (1971). *Optimal Control by Mathematical Programming*. Englewood Cliffs, NJ: Prentice-Hall. pp. 19–20. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-13-638106-5](https://en.wikipedia.org/wiki/Special:BookSources/0-13-638106-5).
2.  [Kuhn, H. W.](https://en.wikipedia.org/wiki/Harold_W._Kuhn); [Tucker, A. W.](https://en.wikipedia.org/wiki/Albert_W._Tucker) (1951). ["Nonlinear programming"](http://projecteuclid.org/euclid.bsmsp/1200500249). *Proceedings of 2nd Berkeley Symposium*. Berkeley: University of California Press. pp. 481–492. [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0047303](https://mathscinet.ams.org/mathscinet-getitem?mr=0047303).
3.  W. Karush (1939). [Minima of Functions of Several Variables with Inequalities as Side Constraints](http://pi.lib.uchicago.edu/1001/cat/bib/4111654) (M.Sc. thesis). Dept. of Mathematics, Univ. of Chicago, Chicago, Illinois.
4.  [Kjeldsen, Tinne Hoff](https://en.wikipedia.org/wiki/Tinne_Hoff_Kjeldsen) (2000). ["A contextualized historical analysis of the Kuhn-Tucker theorem in nonlinear programming: the impact of World War II"](https://doi.org/10.1006%2Fhmat.2000.2289). *Historia Math*. **27** (4): 331–361. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1006/hmat.2000.2289](https://doi.org/10.1006%2Fhmat.2000.2289). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1800317](https://mathscinet.ams.org/mathscinet-getitem?mr=1800317).
5.  Walsh, G. R. (1975). ["Saddle-point Property of Lagrangian Function"](https://books.google.com/books?id=K0EZAQAAIAAJ&pg=PA39). *Methods of Optimization*. New York: John Wiley & Sons. pp. 39–44. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-91922-5](https://en.wikipedia.org/wiki/Special:BookSources/0-471-91922-5).
6.  Kemp, Murray C.; Kimura, Yoshio (1978). [Introduction to Mathematical Economics](https://archive.org/details/introductiontoma0000kemp/page/38). New York: Springer. pp. [38–44](https://archive.org/details/introductiontoma0000kemp/page/38). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-90304-6](https://en.wikipedia.org/wiki/Special:BookSources/0-387-90304-6).
7.  Boyd, Stephen; Vandenberghe, Lieven (2004). *Convex Optimization*. Cambridge: [Cambridge University Press](https://en.wikipedia.org/wiki/Cambridge_University_Press). p. 244. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-83378-7](https://en.wikipedia.org/wiki/Special:BookSources/0-521-83378-7). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [2061575](https://mathscinet.ams.org/mathscinet-getitem?mr=2061575).
8.  [Ruszczyński, Andrzej](https://en.wikipedia.org/wiki/Andrzej_Piotr_Ruszczy%C5%84ski) (2006). *Nonlinear Optimization*. Princeton, NJ: [Princeton University Press](https://en.wikipedia.org/wiki/Princeton_University_Press). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0691119151](https://en.wikipedia.org/wiki/Special:BookSources/978-0691119151). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [2199043](https://mathscinet.ams.org/mathscinet-getitem?mr=2199043).
9.  [Dimitri Bertsekas](https://en.wikipedia.org/wiki/Dimitri_Bertsekas) (1999). *Nonlinear Programming* (2 ed.). Athena Scientific. pp. 329–330. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9781886529007](https://en.wikipedia.org/wiki/Special:BookSources/9781886529007).
10. Boyd, Stephen; Vandenberghe, Lieven (2004). *Convex Optimization*. Cambridge: [Cambridge University Press](https://en.wikipedia.org/wiki/Cambridge_University_Press). p. 244. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-83378-7](https://en.wikipedia.org/wiki/Special:BookSources/0-521-83378-7). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [2061575](https://mathscinet.ams.org/mathscinet-getitem?mr=2061575).
11. Martin, D. H. (1985). "The Essence of Invexity". *J. Optim. Theory Appl*. **47** (1): 65–76. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/BF00941316](https://doi.org/10.1007%2FBF00941316). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [122906371](https://api.semanticscholar.org/CorpusID:122906371).
12. Hanson, M. A. (1999). ["Invexity and the Kuhn-Tucker Theorem"](https://doi.org/10.1006%2Fjmaa.1999.6484). *J. Math. Anal. Appl*. **236** (2): 594–604. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1006/jmaa.1999.6484](https://doi.org/10.1006%2Fjmaa.1999.6484).
13. Chiang, Alpha C. *Fundamental Methods of Mathematical Economics*, 3rd edition, 1984, pp. 750–752.

## Further reading

- Andreani, R.; Martínez, J. M.; Schuverdt, M. L. (2005). "On the relation between constant positive linear dependence condition and quasinormality constraint qualification". *Journal of Optimization Theory and Applications*. **125** (2): 473–485. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s10957-004-1861-9](https://doi.org/10.1007%2Fs10957-004-1861-9). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [122212394](https://api.semanticscholar.org/CorpusID:122212394).
- Avriel, Mordecai (2003). *Nonlinear Programming: Analysis and Methods*. Dover. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-486-43227-0](https://en.wikipedia.org/wiki/Special:BookSources/0-486-43227-0).
- Boltyanski, V.; Martini, H.; Soltan, V. (1998). ["The Kuhn–Tucker Theorem"](https://books.google.com/books?id=YD7UBwAAQBAJ&pg=PA78). *Geometric Methods and Optimization Problems*. New York: Springer. pp. 78–92. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-7923-5454-0](https://en.wikipedia.org/wiki/Special:BookSources/0-7923-5454-0).
- Boyd, S.; Vandenberghe, L. (2004). ["Optimality Conditions"](https://web.stanford.edu/~boyd/cvxbook/bv_cvxbook.pdf#page=255) (PDF). *Convex Optimization*. Cambridge University Press. pp. 241–249. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-83378-7](https://en.wikipedia.org/wiki/Special:BookSources/0-521-83378-7).
- Kemp, Murray C.; Kimura, Yoshio (1978). [Introduction to Mathematical Economics](https://archive.org/details/introductiontoma0000kemp/page/38). New York: Springer. pp. [38–73](https://archive.org/details/introductiontoma0000kemp/page/38). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-90304-6](https://en.wikipedia.org/wiki/Special:BookSources/0-387-90304-6).
- Rau, Nicholas (1981). "Lagrange Multipliers". *Matrices and Mathematical Programming*. London: Macmillan. pp. 156–174. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-333-27768-6](https://en.wikipedia.org/wiki/Special:BookSources/0-333-27768-6).
- Nocedal, J.; Wright, S. J. (2006). *Numerical Optimization*. New York: Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-30303-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-30303-1).
- Sundaram, Rangarajan K. (1996). ["Inequality Constraints and the Theorem of Kuhn and Tucker"](https://books.google.com/books?id=yAfug81P-8YC&pg=PA145). *A First Course in Optimization Theory*. New York: Cambridge University Press. pp. 145–171. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-49770-1](https://en.wikipedia.org/wiki/Special:BookSources/0-521-49770-1).

## External links

- [Examples and Tutorials on the KKT Conditions](http://apmonitor.com/me575/index.php/Main/KuhnTucker)
