[[optimization.base]]

> Source: [Duality (optimization)](https://en.wikipedia.org/wiki/Duality_(optimization))
> License: Wikipedia content is available under CC BY-SA 4.0.

In [mathematical optimization](https://en.wikipedia.org/wiki/Mathematical_optimization) theory, **duality** or the **duality principle** is the principle that [optimization problems](https://en.wikipedia.org/wiki/Optimization_problem) may be viewed from either of two perspectives, the **primal problem** or the **dual problem**. If the primal is a minimization problem then the dual is a maximization problem (and vice versa). Any feasible solution to the primal (minimization) problem is at least as large as any feasible solution to the dual (maximization) problem. Therefore, the solution to the primal is an upper bound to the solution of the dual, and the solution of the dual is a lower bound to the solution of the primal. This fact is called **[weak duality](https://en.wikipedia.org/wiki/Weak_duality)**.

In general, the optimal values of the primal and dual problems need not be equal. Their difference is called the [duality gap](https://en.wikipedia.org/wiki/Duality_gap). For [[Convex Optimization]] problems, the duality gap is zero under a [constraint qualification](https://en.wikipedia.org/wiki/Constraint_qualification) condition. This fact is called **[strong duality](https://en.wikipedia.org/wiki/Strong_duality)**.

## Dual problem

Usually the term "dual problem" refers to the *Lagrangian dual problem* but other dual problems are used – for example, the [Wolfe dual problem](https://en.wikipedia.org/wiki/Wolfe_dual_problem) and the [Fenchel dual problem](https://en.wikipedia.org/wiki/Fenchel%27s_duality_theorem). The Lagrangian dual problem is obtained by forming the [Lagrangian](https://en.wikipedia.org/wiki/Lagrange_multiplier) of a minimization problem by using nonnegative [Lagrange multipliers](https://en.wikipedia.org/wiki/Lagrange_multiplier) to add the constraints to the objective function, and then solving for the primal variable values that minimize the original objective function. This solution gives the primal variables as functions of the Lagrange multipliers, which are called dual variables, so that the new problem is to maximize the objective function with respect to the dual variables under the derived constraints on the dual variables (including at least the nonnegativity constraints).

In general given two [dual pairs](https://en.wikipedia.org/wiki/Dual_pair) of [separated](https://en.wikipedia.org/wiki/Separated_space) [locally convex spaces](https://en.wikipedia.org/wiki/Locally_convex_space) $\left(X,X^{*}\right)$ and $\left(Y,Y^{*}\right)$ and the function $f:X\to \mathbb {R} \cup \{+\infty \}$, we can define the primal problem as finding ${\hat {x}}$ such that $f({\hat {x}})=\inf _{x\in X}f(x).\,$ In other words, if ${\hat {x}}$ exists, $f({\hat {x}})$ is the [minimum](https://en.wikipedia.org/wiki/Minimum) of the function $f$ and the [infimum](https://en.wikipedia.org/wiki/Infimum) (greatest lower bound) of the function is attained.

If there are constraint conditions, these can be built into the function $f$ by letting ${\tilde {f}}=f+I_{\mathrm {constraints} }$ where $I_{\mathrm {constraints} }$ is a suitable function on $X$ that has a minimum 0 on the constraints, and for which one can prove that $\inf _{x\in X}{\tilde {f}}(x)=\inf _{x\ \mathrm {constrained} }f(x)$. The latter condition is trivially, but not always conveniently, satisfied for the [[Characteristic Function]] (i.e. $I_{\mathrm {constraints} }(x)=0$ for $x$ satisfying the constraints and $I_{\mathrm {constraints} }(x)=\infty$ otherwise). Then extend ${\tilde {f}}$ to a [perturbation function](https://en.wikipedia.org/wiki/Perturbation_function) $F:X\times Y\to \mathbb {R} \cup \{+\infty \}$ such that $F(x,0)={\tilde {f}}(x)$.

The [duality gap](https://en.wikipedia.org/wiki/Duality_gap) is the difference of the right and left hand sides of the inequality

$\sup _{y^{*}\in Y^{*}}-F^{*}(0,y^{*})\leq \inf _{x\in X}F(x,0),\,$

where $F^{*}$ is the [convex conjugate](https://en.wikipedia.org/wiki/Convex_conjugate) in both variables and $\sup$ denotes the [supremum](https://en.wikipedia.org/wiki/Supremum) (least upper bound).

### Duality gap

The duality gap is the difference between the values of any primal solutions and any dual solutions. If $d^{*}$ is the optimal dual value and $p^{*}$ is the optimal primal value, then the duality gap is equal to $p^{*}-d^{*}$. This value is always greater than or equal to 0 (for minimization problems). The duality gap is zero if and only if [strong duality](https://en.wikipedia.org/wiki/Strong_duality) holds. Otherwise the gap is strictly positive and [weak duality](https://en.wikipedia.org/wiki/Weak_duality) holds.

In computational optimization, another "duality gap" is often reported, which is the difference in value between any dual solution and the value of a feasible but suboptimal iterate for the primal problem. This alternative "duality gap" quantifies the discrepancy between the value of a current feasible but suboptimal iterate for the primal problem and the value of the dual problem; the value of the dual problem is, under regularity conditions, equal to the value of the *convex relaxation* of the primal problem: The convex relaxation is the problem arising replacing a non-convex feasible set with its closed [convex hull](https://en.wikipedia.org/wiki/Convex_hull) and with replacing a non-convex function with its convex [closure](https://en.wikipedia.org/wiki/Lower_semi-continuous), that is the function that has the [epigraph](https://en.wikipedia.org/wiki/Epigraph_(mathematics) "Epigraph (mathematics)") that is the closed convex hull of the original primal objective function.

## Linear case

[Linear programming](https://en.wikipedia.org/wiki/Linear_programming) problems are [optimization](https://en.wikipedia.org/wiki/Optimization_(mathematics)) problems in which the [objective function](https://en.wikipedia.org/wiki/Objective_function) and the [constraints](https://en.wikipedia.org/wiki/Constraint_(mathematics) "Constraint (mathematics)") are all [linear](https://en.wikipedia.org/wiki/Linear). In the primal problem, the objective function is a [linear combination](https://en.wikipedia.org/wiki/Linear_combination) of *n* variables. There are *m* constraints, each of which places an upper bound on a linear combination of the *n* variables. The goal is to maximize the value of the objective function subject to the constraints. A *solution* is a [vector](https://en.wikipedia.org/wiki/List_(computing)) (a list) of *n* values that achieves the maximum value for the objective function.

In the dual problem, the objective function is a linear combination of the *m* values that are the limits in the *m* constraints from the primal problem. There are *n* dual constraints, each of which places a lower bound on a linear combination of *m* dual variables.

### Relationship between the primal problem and the dual problem

In the linear case, in the primal problem, from each sub-optimal point that satisfies all the constraints, there is a direction or [subspace](https://en.wikipedia.org/wiki/Linear_subspace) of directions to move that increases the objective function. Moving in any such direction is said to remove slack between the [candidate solution](https://en.wikipedia.org/wiki/Candidate_solution) and one or more constraints. An *infeasible* value of the candidate solution is one that exceeds one or more of the constraints.

In the dual problem, the dual vector multiplies the constraints that determine the positions of the constraints in the primal. Varying the dual vector in the dual problem is equivalent to revising the upper bounds in the primal problem. The lowest upper bound is sought. That is, the dual vector is minimized in order to remove slack between the candidate positions of the constraints and the actual optimum. An infeasible value of the dual vector is one that is too low. It sets the candidate positions of one or more of the constraints in a position that excludes the actual optimum.

This intuition is made formal by the equations in [Linear programming: Duality](https://en.wikipedia.org/wiki/Linear_programming#Duality).

## Nonlinear case

In [nonlinear programming](https://en.wikipedia.org/wiki/Nonlinear_programming), the constraints are not necessarily linear. Nonetheless, many of the same principles apply.

To ensure that the global maximum of a non-linear problem can be identified easily, the problem formulation often requires that the functions be convex and have compact lower level sets. This is the significance of the [Karush–Kuhn–Tucker conditions](https://en.wikipedia.org/wiki/Karush%E2%80%93Kuhn%E2%80%93Tucker_conditions). They provide necessary conditions for identifying local optima of non-linear programming problems. There are additional conditions (constraint qualifications) that are necessary so that it will be possible to define the direction to an *optimal* solution. An optimal solution is one that is a [local optimum](https://en.wikipedia.org/wiki/Local_optimum), but possibly not a global optimum.

### Lagrange duality 

**Motivation**

Suppose we want to solve the following [nonlinear programming](https://en.wikipedia.org/wiki/Nonlinear_programming) problem:

> ${\begin{aligned}{\text{minimize }}&f_{0}(x)\\{\text{subject to }}&f_{i}(x)\leq 0,\ i\in \left\{1,\ldots ,m\right\}\\\end{aligned}}$

The problem has constraints; we would like to convert it to a program without constraints. Theoretically, it is possible to do it by minimizing the function $J(x)$, defined as

> $J(x)=f_{0}(x)+\sum _{i}I[f_{i}(x)]$

where $I$ is an infinite [step function](https://en.wikipedia.org/wiki/Step_function): $I[u]=0$ if $u\leq 0$, and $I[u]=\infty$ otherwise. But $J(x)$ is hard to solve as it is not continuous. It is possible to "approximate" $I[u]$ by $\lambda u$, where $\lambda$ is a positive constant. This yields a function known as the Lagrangian:

> $L(x,\lambda )=f_{0}(x)+\sum _{i}\lambda _{i}f_{i}(x)$

Note that, for every $x$,

> $\max _{\lambda \geq 0}L(x,\lambda )=J(x)$.

*Proof*:

- If $x$ satisfies all constraints $f_{i}(x)\leq 0$ , then $L(x,\lambda )$ is maximized when taking $\lambda =0$, and its value is then $f(x)$;
- If $x$ violates some constraint, $f_{i}(x)>0$ for some $i$, then $L(x,\lambda )\to \infty$ when $\lambda _{i}\to \infty$.

Therefore, the original problem is equivalent to:

> $\min _{x}\max _{\lambda \geq 0}L(x,\lambda )$.

By reversing the order of min and max, we get:

> $\max _{\lambda \geq 0}\min _{x}L(x,\lambda )$.

The *dual function* is the inner problem in the above formula:

> $g(\lambda ):=\min _{x}L(x,\lambda )$.

The **Lagrangian dual program** is the program of maximizing g:

> $\max _{\lambda \geq 0}g(\lambda )$.

The optimal solution to the dual program is a lower bound for the optimal solution of the original (primal) program; this is the *weak duality* principle. If the primal problem is convex and bounded from below, and there exists a point in which all nonlinear constraints are strictly satisfied ([Slater's condition](https://en.wikipedia.org/wiki/Slater%27s_condition)), then the optimal solution to the dual program *equals* the optimal solution of the primal program; this is the *strong duality* principle. In this case, we can solve the primal program by finding an optimal solution $\lambda ^{*}$ to the dual program, and then solving:

> $\min _{x}L(x,\lambda ^{*})$.

Note that, to use either the weak or the strong duality principle, we need a way to compute $g(\lambda )$. In general this may be hard, as we need to solve a different minimization problem for every $\lambda$. But for some classes of functions, it is possible to get an explicit formula for $g(\lambda )$. Solving the primal and dual programs together is often easier than solving only one of them. Examples are [linear programming](https://en.wikipedia.org/wiki/Linear_programming) and [quadratic programming](https://en.wikipedia.org/wiki/Quadratic_programming). A better and more general approach to duality is provided by [Fenchel's duality theorem](https://en.wikipedia.org/wiki/Fenchel%27s_duality_theorem).

Another condition in which the min-max and max-min are equal is when the Lagrangian has a [saddle point](https://en.wikipedia.org/wiki/Saddle_point): $(x^{*},\lambda ^{*})$ is a saddle point of the Lagrange function $L$ if and only if $x^{*}$ is an optimal solution to the primal, $\lambda ^{*}$ is an optimal solution to the dual, and the optimal values in the indicated problems are equal to each other.

### The strong Lagrange principle

Given a [nonlinear programming](https://en.wikipedia.org/wiki/Nonlinear_programming) problem in standard form

${\begin{aligned}{\text{minimize }}&f_{0}(x)\\{\text{subject to }}&f_{i}(x)\leq 0,\ i\in \left\{1,\ldots ,m\right\}\\&h_{i}(x)=0,\ i\in \left\{1,\ldots ,p\right\}\end{aligned}}$

with the domain ${\mathcal {D}}\subset \mathbb {R} ^{n}$ having non-empty interior, the *Lagrangian function* ${\mathcal {L}}:\mathbb {R} ^{n}\times \mathbb {R} ^{m}\times \mathbb {R} ^{p}\to \mathbb {R}$ is defined as

${\mathcal {L}}(x,\lambda ,\nu )=f_{0}(x)+\sum _{i=1}^{m}\lambda _{i}f_{i}(x)+\sum _{i=1}^{p}\nu _{i}h_{i}(x).$

The vectors $\lambda$ and $\nu$ are called the *dual variables* or *Lagrange multiplier vectors* associated with the problem. The *Lagrange dual function* $g:\mathbb {R} ^{m}\times \mathbb {R} ^{p}\to \mathbb {R}$ is defined as

$g(\lambda ,\nu )=\inf _{x\in {\mathcal {D}}}{\mathcal {L}}(x,\lambda ,\nu )=\inf _{x\in {\mathcal {D}}}\left\{f_{0}(x)+\sum _{i=1}^{m}\lambda _{i}f_{i}(x)+\sum _{i=1}^{p}\nu _{i}h_{i}(x)\right\}.$

The dual function $g$ is concave, even when the initial problem is not convex, because it is a point-wise infimum of affine functions. The dual function yields lower bounds on the optimal value $p^{*}$ of the initial problem; for any $\lambda \geq 0$ and any $\nu$ we have $g(\lambda ,\nu )\leq p^{*}$.

If a [constraint qualification](https://en.wikipedia.org/wiki/Constraint_qualification) such as [Slater's condition](https://en.wikipedia.org/wiki/Slater%27s_condition) holds and the original problem is convex, then we have [strong duality](https://en.wikipedia.org/wiki/Strong_duality), i.e. $d^{*}=\max _{\lambda \geq 0,\nu }g(\lambda ,\nu )=\inf f_{0}=p^{*}$.

### Convex problems

For a convex minimization problem with inequality constraints,

${\begin{aligned}&{\underset {x}{\operatorname {minimize} }}&&f(x)\\&\operatorname {subject\;to} &&g_{i}(x)\leq 0,\quad i=1,\ldots ,m\end{aligned}}$

the Lagrangian dual problem is

${\begin{aligned}&{\underset {u}{\operatorname {maximize} }}&&\inf _{x}\left(f(x)+\sum _{j=1}^{m}u_{j}g_{j}(x)\right)\\&\operatorname {subject\;to} &&u_{i}\geq 0,\quad i=1,\ldots ,m\end{aligned}}$

where the objective function is the Lagrange dual function. Provided that the functions $f$ and $g_{1},\ldots ,g_{m}$ are continuously differentiable, the infimum occurs where the gradient is equal to zero. The problem

${\begin{aligned}&{\underset {x,u}{\operatorname {maximize} }}&&f(x)+\sum _{j=1}^{m}u_{j}g_{j}(x)\\&\operatorname {subject\;to} &&\nabla f(x)+\sum _{j=1}^{m}u_{j}\,\nabla g_{j}(x)=0\\&&&u_{i}\geq 0,\quad i=1,\ldots ,m\end{aligned}}$

is called the [Wolfe dual problem](https://en.wikipedia.org/wiki/Wolfe_duality). This problem may be difficult to deal with computationally, because the objective function is not concave in the joint variables $(u,x)$. Also, the equality constraint $\nabla f(x)+\sum _{j=1}^{m}u_{j}\,\nabla g_{j}(x)$ is nonlinear in general, so the Wolfe dual problem is typically a nonconvex optimization problem. In any case, [weak duality](https://en.wikipedia.org/wiki/Weak_duality) holds.

## History

According to [George Dantzig](https://en.wikipedia.org/wiki/George_Dantzig), the duality theorem for linear optimization was conjectured by [John von Neumann](https://en.wikipedia.org/wiki/John_von_Neumann) immediately after Dantzig presented the linear programming problem. Von Neumann noted that he was using information from his [game theory](https://en.wikipedia.org/wiki/Game_theory), and conjectured that two person zero sum matrix game was equivalent to linear programming. Rigorous proofs were first published in 1948 by [Albert W. Tucker](https://en.wikipedia.org/wiki/Albert_W._Tucker) and his group. (Dantzig's foreword to Nering and Tucker, 1993)

## Applications

In [support vector machines](https://en.wikipedia.org/wiki/Support_vector_machine) (SVMs), formulating the primal problem of SVMs as the dual problem can be used to implement the [Kernel trick](https://en.wikipedia.org/wiki/Kernel_trick), but the latter has higher time complexity in the historical cases.

## See also

- [Convex duality](https://en.wikipedia.org/wiki/Convex_duality)
- [Duality](https://en.wikipedia.org/wiki/Duality_(mathematics) "Duality (mathematics)")
- [Relaxation (approximation)](https://en.wikipedia.org/wiki/Relaxation_(approximation) "Relaxation (approximation)")

## Notes

1.  Boyd, Stephen P.; Vandenberghe, Lieven (2004). [Convex Optimization](https://web.stanford.edu/~boyd/cvxbook/bv_cvxbook.pdf#page=230) (pdf). Cambridge University Press. p. 216. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-83378-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-83378-3). Retrieved October 15, 2011.
2.  ^   Boţ, Radu Ioan; Wanka, Gert; Grad, Sorin-Mihai (2009). *Duality in Vector Optimization*. Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-642-02885-4](https://en.wikipedia.org/wiki/Special:BookSources/978-3-642-02885-4).
3.  Csetnek, Ernö Robert (2010). *Overcoming the failure of the classical generalized interior-point regularity conditions in convex optimization. Applications of the duality theory to enlargements of maximal monotone operators*. Logos Verlag Berlin GmbH. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-8325-2503-3](https://en.wikipedia.org/wiki/Special:BookSources/978-3-8325-2503-3).
4.  Zălinescu, Constantin (2002). [Convex analysis in general vector spaces](https://archive.org/details/convexanalysisge00zali_934). River Edge, NJ: World Scientific Publishing Co., Inc. pp. [106](https://archive.org/details/convexanalysisge00zali_934/page/n126)–113. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [981-238-067-1](https://en.wikipedia.org/wiki/Special:BookSources/981-238-067-1). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1921556](https://mathscinet.ams.org/mathscinet-getitem?mr=1921556).
5.  Borwein, Jonathan; Zhu, Qiji (2005). *Techniques of Variational Analysis*. Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4419-2026-3](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4419-2026-3).
6.  [Ahuja, Ravindra K.](https://en.wikipedia.org/wiki/Ravindra_K._Ahuja); [Magnanti, Thomas L.](https://en.wikipedia.org/wiki/Thomas_L._Magnanti); [Orlin, James B.](https://en.wikipedia.org/wiki/James_B._Orlin) (1993). *Network Flows: Theory, Algorithms and Applications*. Prentice Hall. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-13-617549-X](https://en.wikipedia.org/wiki/Special:BookSources/0-13-617549-X).
7.  Bertsekas, Dimitri; Nedic, Angelia; Ozdaglar, Asuman (2003). *Convex Analysis and Optimization*. Athena Scientific. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [1-886529-45-0](https://en.wikipedia.org/wiki/Special:BookSources/1-886529-45-0).
8.  Bertsekas, Dimitri P. (1999). *Nonlinear Programming* (2nd ed.). Athena Scientific. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [1-886529-00-0](https://en.wikipedia.org/wiki/Special:BookSources/1-886529-00-0).
9.  Bertsekas, Dimitri P. (2009). *Convex Optimization Theory*. Athena Scientific. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-886529-31-1](https://en.wikipedia.org/wiki/Special:BookSources/978-1-886529-31-1).
10. Bonnans, J. Frédéric; Gilbert, J. Charles; [Lemaréchal, Claude](https://en.wikipedia.org/wiki/Claude_Lemar%C3%A9chal); [Sagastizábal, Claudia A.](https://en.wikipedia.org/wiki/Claudia_Sagastiz%C3%A1bal) (2006). [Numerical optimization: Theoretical and practical aspects](https://www.springer.com/mathematics/applications/book/978-3-540-35445-1). Universitext (Second revised ed. of translation of 1997 French ed.). Berlin: Springer-Verlag. pp. xiv+490. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-3-540-35447-5](https://doi.org/10.1007%2F978-3-540-35447-5). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [3-540-35445-X](https://en.wikipedia.org/wiki/Special:BookSources/3-540-35445-X). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [2265882](https://mathscinet.ams.org/mathscinet-getitem?mr=2265882).
11. Hiriart-Urruty, Jean-Baptiste; Lemaréchal, Claude (1993). *Convex analysis and minimization algorithms, Volume I: Fundamentals*. Grundlehren der Mathematischen Wissenschaften \[Fundamental Principles of Mathematical Sciences\]. Vol. 305. Berlin: Springer-Verlag. pp. xviii+417. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [3-540-56850-6](https://en.wikipedia.org/wiki/Special:BookSources/3-540-56850-6). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1261420](https://mathscinet.ams.org/mathscinet-getitem?mr=1261420).
12. Hiriart-Urruty, Jean-Baptiste; [Lemaréchal, Claude](https://en.wikipedia.org/wiki/Claude_Lemar%C3%A9chal) (1993). "14 Duality for Practitioners". *Convex analysis and minimization algorithms, Volume II: Advanced theory and bundle methods*. Grundlehren der Mathematischen Wissenschaften \[Fundamental Principles of Mathematical Sciences\]. Vol. 306. Berlin: Springer-Verlag. pp. xviii+346. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [3-540-56852-2](https://en.wikipedia.org/wiki/Special:BookSources/3-540-56852-2). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1295240](https://mathscinet.ams.org/mathscinet-getitem?mr=1295240).
13. Lasdon, Leon S. (2002) \[Reprint of the 1970 Macmillan\]. *Optimization theory for large systems*. Mineola, New York: Dover Publications, Inc. pp. xiii+523. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-486-41999-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-486-41999-2). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1888251](https://mathscinet.ams.org/mathscinet-getitem?mr=1888251).
14. [Lemaréchal, Claude](https://en.wikipedia.org/wiki/Claude_Lemar%C3%A9chal) (2001). "Lagrangian relaxation". In Jünger, Michael; Naddef, Denis (eds.). *Computational combinatorial optimization: Papers from the Spring School held in Schloß Dagstuhl, May 15–19, 2000*. Lecture Notes in Computer Science (LNCS). Vol. 2241. Berlin: Springer-Verlag. pp. 112–156. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/3-540-45586-8_4](https://doi.org/10.1007%2F3-540-45586-8_4). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [3-540-42877-1](https://en.wikipedia.org/wiki/Special:BookSources/3-540-42877-1). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1900016](https://mathscinet.ams.org/mathscinet-getitem?mr=1900016). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [9048698](https://api.semanticscholar.org/CorpusID:9048698).
16. Shapiro, Jeremy F. (1979). [Mathematical programming: Structures and algorithms](https://archive.org/details/mathematicalprog0000shap/page/). New York: Wiley-Interscience \[John Wiley & Sons\]. pp. [xvi+388](https://archive.org/details/mathematicalprog0000shap/page/). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-77886-9](https://en.wikipedia.org/wiki/Special:BookSources/0-471-77886-9). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0544669](https://mathscinet.ams.org/mathscinet-getitem?mr=0544669).
17. David Knowles (2010). ["Lagrangian Duality for Dummies"](https://www-cs.stanford.edu/people/davidknowles/lagrangian_duality.pdf) (PDF).
18. ^   Nemirovsky and Ben-Tal (2023). ["Optimization III: Convex Optimization"](https://www2.isye.gatech.edu/~nemirovs/OPTIIILN2023Spring.pdf) (PDF).
19. Geoffrion, Arthur M. (1971). "Duality in Nonlinear Programming: A Simplified Applications-Oriented Development". *SIAM Review*. **13** (1): 1–37. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/1013001](https://doi.org/10.1137%2F1013001). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2028848](https://www.jstor.org/stable/2028848).

## References

### Books

- [Ahuja, Ravindra K.](https://en.wikipedia.org/wiki/Ravindra_K._Ahuja); [Magnanti, Thomas L.](https://en.wikipedia.org/wiki/Thomas_L._Magnanti); [Orlin, James B.](https://en.wikipedia.org/wiki/James_B._Orlin) (1993). *Network Flows: Theory, Algorithms and Applications*. Prentice Hall. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-13-617549-X](https://en.wikipedia.org/wiki/Special:BookSources/0-13-617549-X).
- Bertsekas, Dimitri; Nedic, Angelia; Ozdaglar, Asuman (2003). *Convex Analysis and Optimization*. Athena Scientific. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [1-886529-45-0](https://en.wikipedia.org/wiki/Special:BookSources/1-886529-45-0).
- Bertsekas, Dimitri P. (1999). *Nonlinear Programming* (2nd ed.). Athena Scientific. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [1-886529-00-0](https://en.wikipedia.org/wiki/Special:BookSources/1-886529-00-0).
- Bertsekas, Dimitri P. (2009). *Convex Optimization Theory*. Athena Scientific. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-886529-31-1](https://en.wikipedia.org/wiki/Special:BookSources/978-1-886529-31-1).
- Bonnans, J. Frédéric; Gilbert, J. Charles; [Lemaréchal, Claude](https://en.wikipedia.org/wiki/Claude_Lemar%C3%A9chal); Sagastizábal, Claudia A. (2006). [Numerical optimization: Theoretical and practical aspects](https://www.springer.com/mathematics/applications/book/978-3-540-35445-1). Universitext (Second revised ed. of translation of 1997 French ed.). Berlin: Springer-Verlag. pp. xiv+490. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-3-540-35447-5](https://doi.org/10.1007%2F978-3-540-35447-5). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [3-540-35445-X](https://en.wikipedia.org/wiki/Special:BookSources/3-540-35445-X). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [2265882](https://mathscinet.ams.org/mathscinet-getitem?mr=2265882).
- [Cook, William J.](https://en.wikipedia.org/wiki/William_J._Cook); Cunningham, William H.; [Pulleyblank, William R.](https://en.wikipedia.org/wiki/William_R._Pulleyblank); [Schrijver, Alexander](https://en.wikipedia.org/wiki/Alexander_Schrijver) (November 12, 1997). *Combinatorial Optimization* (1st ed.). John Wiley & Sons. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-55894-X](https://en.wikipedia.org/wiki/Special:BookSources/0-471-55894-X).
- [Dantzig, George B.](https://en.wikipedia.org/wiki/George_Dantzig) (1963). [Linear Programming and Extensions](https://archive.org/details/linearprogrammin00dant). Princeton, NJ: Princeton University Press.
- Hiriart-Urruty, Jean-Baptiste; Lemaréchal, Claude (1993). *Convex analysis and minimization algorithms, Volume I: Fundamentals*. Grundlehren der Mathematischen Wissenschaften \[Fundamental Principles of Mathematical Sciences\]. Vol. 305. Berlin: Springer-Verlag. pp. xviii+417. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [3-540-56850-6](https://en.wikipedia.org/wiki/Special:BookSources/3-540-56850-6). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1261420](https://mathscinet.ams.org/mathscinet-getitem?mr=1261420).
- Hiriart-Urruty, Jean-Baptiste; [Lemaréchal, Claude](https://en.wikipedia.org/wiki/Claude_Lemar%C3%A9chal) (1993). "14 Duality for Practitioners". *Convex analysis and minimization algorithms, Volume II: Advanced theory and bundle methods*. Grundlehren der Mathematischen Wissenschaften \[Fundamental Principles of Mathematical Sciences\]. Vol. 306. Berlin: Springer-Verlag. pp. xviii+346. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [3-540-56852-2](https://en.wikipedia.org/wiki/Special:BookSources/3-540-56852-2). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1295240](https://mathscinet.ams.org/mathscinet-getitem?mr=1295240).
- Lasdon, Leon S. (2002) \[Reprint of the 1970 Macmillan\]. *Optimization theory for large systems*. Mineola, New York: Dover Publications, Inc. pp. xiii+523. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-486-41999-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-486-41999-2). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1888251](https://mathscinet.ams.org/mathscinet-getitem?mr=1888251).
- [Lawler, Eugene](https://en.wikipedia.org/wiki/Eugene_Lawler) (2001). "4.5. Combinatorial Implications of Max-Flow Min-Cut Theorem, 4.6. Linear Programming Interpretation of Max-Flow Min-Cut Theorem". *Combinatorial Optimization: Networks and Matroids*. Dover. pp. 117–120. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-486-41453-1](https://en.wikipedia.org/wiki/Special:BookSources/0-486-41453-1).
- [Lemaréchal, Claude](https://en.wikipedia.org/wiki/Claude_Lemar%C3%A9chal) (2001). "Lagrangian relaxation". In Jünger, Michael; Naddef, Denis (eds.). *Computational combinatorial optimization: Papers from the Spring School held in Schloß Dagstuhl, May 15–19, 2000*. Lecture Notes in Computer Science (LNCS). Vol. 2241. Berlin: Springer-Verlag. pp. 112–156. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/3-540-45586-8_4](https://doi.org/10.1007%2F3-540-45586-8_4). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [3-540-42877-1](https://en.wikipedia.org/wiki/Special:BookSources/3-540-42877-1). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1900016](https://mathscinet.ams.org/mathscinet-getitem?mr=1900016). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [9048698](https://api.semanticscholar.org/CorpusID:9048698).
- Nering, Evar D.; Tucker, Albert W. (1993). [Linear Programming and Related Problems](https://archive.org/details/linearprogramsre0000neri). Boston, MA: Academic Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-12-515440-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-12-515440-6).
- Papadimitriou, Christos H.; Steiglitz, Kenneth (July 1998). *Combinatorial Optimization: Algorithms and Complexity* (Unabridged ed.). Dover. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-486-40258-4](https://en.wikipedia.org/wiki/Special:BookSources/0-486-40258-4).
- [Ruszczyński, Andrzej](https://en.wikipedia.org/wiki/Andrzej_Piotr_Ruszczy%C5%84ski) (2006). *Nonlinear Optimization*. Princeton, NJ: [Princeton University Press](https://en.wikipedia.org/wiki/Princeton_University_Press). pp. xii+454. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-691-11915-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-691-11915-1). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [2199043](https://mathscinet.ams.org/mathscinet-getitem?mr=2199043).

### Articles

- [Everett, Hugh III](https://en.wikipedia.org/wiki/Hugh_Everett) (1963). ["Generalized Lagrange multiplier method for solving problems of optimum allocation of resources"](https://web.archive.org/web/20110724151508/http://or.journal.informs.org/cgi/reprint/11/3/399). *Operations Research*. **11** (3): 399–417. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1287/opre.11.3.399](https://doi.org/10.1287%2Fopre.11.3.399). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [168028](https://www.jstor.org/stable/168028). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0152360](https://mathscinet.ams.org/mathscinet-getitem?mr=0152360). Archived from [the original](http://or.journal.informs.org/cgi/reprint/11/3/399) on 2011-07-24.
- Kiwiel, Krzysztof C.; Larsson, Torbjörn; Lindberg, P. O. (August 2007). ["Lagrangian relaxation via ballstep subgradient methods"](https://web.archive.org/web/20110726180807/http://mor.journal.informs.org/cgi/content/abstract/32/3/669). *[Mathematics of Operations Research](https://en.wikipedia.org/wiki/Mathematics_of_Operations_Research)*. **32** (3): 669–686. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1287/moor.1070.0261](https://doi.org/10.1287%2Fmoor.1070.0261). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [2348241](https://mathscinet.ams.org/mathscinet-getitem?mr=2348241). Archived from [the original](http://mor.journal.informs.org/cgi/content/abstract/32/3/669) on 2011-07-26. Retrieved 2011-05-12.
- [Duality in Linear Programming](http://www.civilized.com/files/duality.pdf) Gary D. Knott
