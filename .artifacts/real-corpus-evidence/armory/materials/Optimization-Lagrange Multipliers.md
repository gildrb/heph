[[optimization.base]]

> Source: [Lagrange multiplier](https://en.wikipedia.org/wiki/Lagrange_multiplier)
> License: Wikipedia content is available under CC BY-SA 4.0.

In [mathematical optimization](https://en.wikipedia.org/wiki/Mathematical_optimization), the **method of Lagrange multipliers** is a strategy for finding the local [maxima and minima](https://en.wikipedia.org/wiki/Maxima_and_minima) of a [function](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)") subject to [equation constraints](https://en.wikipedia.org/wiki/Constraint_(mathematics) "Constraint (mathematics)") (i.e., subject to the condition that one or more [equations](https://en.wikipedia.org/wiki/Equation) have to be satisfied exactly by the chosen values of the [variables](https://en.wikipedia.org/wiki/Variable_(mathematics) "Variable (mathematics)")). It is named after the mathematician [Joseph-Louis Lagrange](https://en.wikipedia.org/wiki/Joseph-Louis_Lagrange).

## Summary and rationale

The basic idea is to convert a constrained problem into a form such that the [derivative test](https://en.wikipedia.org/wiki/Derivative_test) of an unconstrained problem can still be applied. The relationship between the gradient of the function and gradients of the constraints rather naturally leads to a reformulation of the original problem, known as the **Lagrangian function** or Lagrangian. In the general case, the Lagrangian is defined as

$$
{\mathcal {L}}(x,\lambda )\equiv f(x)+\langle \lambda ,g(x)\rangle
$$

for functions $f,g$; the notation $\langle \cdot ,\cdot \rangle$ denotes an [inner product](https://en.wikipedia.org/wiki/Inner_product). The value $\lambda$ is called the **Lagrange multiplier**.

In simple cases, where the inner product is defined as the [dot product](https://en.wikipedia.org/wiki/Dot_product), the Lagrangian is

$$
{\mathcal {L}}(x,\lambda )\equiv f(x)+\lambda \cdot g(x)
$$

The method can be summarized as follows: in order to find the maximum or minimum of a function $f$ subject to the equality constraint $g(x)=0$, find the [stationary points](https://en.wikipedia.org/wiki/Stationary_point) of ${\mathcal {L}}$ considered as a function of $x$ and the Lagrange multiplier $\lambda ~$. This means that all [partial derivatives](https://en.wikipedia.org/wiki/Partial_derivative) should be zero, including the partial derivative with respect to $\lambda ~$.

${\frac {\partial {\mathcal {L}}}{\partial x}}=0$   and   ${\frac {\ \partial {\mathcal {L}}\ }{\partial \lambda }}=0\ ;$

or equivalently

${\frac {\partial f(x)}{\partial x}}+\lambda \cdot {\frac {\partial g(x)}{\partial x}}=0$   and  $g(x)=0~.$

The solution corresponding to the original [[Constrained Optimization]] is always a [saddle point](https://en.wikipedia.org/wiki/Saddle_point) of the Lagrangian function, which can be identified among the stationary points from the [definiteness](https://en.wikipedia.org/wiki/Definiteness_of_a_matrix) of the [bordered Hessian matrix](https://en.wikipedia.org/wiki/Bordered_Hessian).

The great advantage of this method is that it allows the optimization to be solved without explicit [parameterization](https://en.wikipedia.org/wiki/Parametrization_(geometry) "Parametrization (geometry)") in terms of the constraints. As a result, the method of Lagrange multipliers is widely used to solve challenging constrained optimization problems. Further, the method of Lagrange multipliers is generalized by the [Karush–Kuhn–Tucker conditions](https://en.wikipedia.org/wiki/Karush%E2%80%93Kuhn%E2%80%93Tucker_conditions), which can also take into account inequality constraints of the form $h(\mathbf {x} )\leq c$ for a given constant $c$.

## Statement

The following is known as the Lagrange multiplier theorem.

Let $f\colon \mathbb {R} ^{n}\to \mathbb {R}$ be the [objective function](https://en.wikipedia.org/wiki/Objective_function) and let $g\colon \mathbb {R} ^{n}\to \mathbb {R} ^{c}$ be the constraints function, both belonging to $C^{1}$ (that is, having continuous first derivatives). Consider the following constrained optimization problem:

$$
{\begin{aligned}&{\text{maximize }}f(x)\\&{\text{subject to: }}g(x)=0\end{aligned}}
$$

Let $x_{\star }$ be an optimal solution to the above optimization problem such that, for the matrix of partial derivatives ${\Bigl [}\operatorname {D} g(x_{\star }){\Bigr ]}_{j,k}={\frac {\ \partial g_{j}\ }{\partial x_{k}}}$, $\operatorname {rank} (\operatorname {D} g(x_{\star }))=c\leq n$: Then there exists a unique Lagrange multiplier $\lambda _{\star }\in \mathbb {R} ^{c}$ such that $\operatorname {D} f(x_{\star })=\lambda _{\star }^{\mathsf {T}}\operatorname {D} g(x_{\star })~.$ (In this equation, $\lambda _{\star }$ is a column vector, so its transpose $\lambda _{\star }^{\mathsf {T}}$ is a row vector. Alternatively, we can redefine the Lagrange multiplier directly as a row vector and thus avoid the transposition.)

The Lagrange multiplier theorem states that at any local maximum (or minimum) of the function evaluated under the equality constraints, if constraint qualification applies (explained below), then the [gradient](https://en.wikipedia.org/wiki/Gradient) of the function (at that point) can be expressed as a [linear combination](https://en.wikipedia.org/wiki/Linear_combination) of the gradients of the constraints (at that point), with the Lagrange multipliers acting as [coefficients](https://en.wikipedia.org/wiki/Coefficient). This is equivalent to saying that any direction perpendicular to all gradients of the constraints is also perpendicular to the gradient of the function. Or still, saying that the [directional derivative](https://en.wikipedia.org/wiki/Directional_derivative) of the function is 0 in every feasible direction.

## Single constraint

![[media/872ca5c2829c37bc50efcd7279bac07132f6c466.png]]
Figure 1: The red curve shows the constraint <em>g</em>(<em>x</em>, <em>y</em>) = <em>c</em>. The blue curves are contours of <em>f</em>(<em>x</em>, <em>y</em>). The point where the red constraint tangentially touches a blue contour is the maximum of <em>f</em>(<em>x</em>, <em>y</em>) along the constraint, since  <em>d</em><sub>1</sub> &gt; <em>d</em><sub>2</sub> .

For the case of only one constraint and only two choice variables (as exemplified in Figure 1), consider the [optimization problem](https://en.wikipedia.org/wiki/Optimization_problem) 

$$
{\begin{aligned}{\underset {x,y}{\text{maximize}}}\quad &f(x,y)\\{\text{subject to}}\quad &g(x,y)=0.\end{aligned}}
$$

 (Sometimes an additive constant is shown separately rather than being included in $g$, in which case the constraint is written $g(x,y)=c,$ as in Figure 1.) We assume that both $f$ and $g$ have continuous first [partial derivatives](https://en.wikipedia.org/wiki/Partial_derivative). We introduce a new variable ($\lambda$) called a **Lagrange multiplier** (or **Lagrange undetermined multiplier**) and study the **Lagrange function** (or **Lagrangian** or **Lagrangian expression**) defined by 

$$
{\mathcal {L}}(x,y,\lambda )=f(x,y)+\lambda \cdot g(x,y),
$$

 where the $\lambda$ term may be either added or subtracted. If $f(x_{0},y_{0})$ is a maximum of $f(x,y)$ for the original constrained problem and $\nabla g(x_{0},y_{0})\neq 0,$ then there exists $\lambda _{0}$ such that ($x_{0},y_{0},\lambda _{0}$) is a *[stationary point](https://en.wikipedia.org/wiki/Stationary_point)* for the Lagrange function (stationary points are those points where the first partial derivatives of ${\mathcal {L}}$ are zero). The assumption $\nabla g\neq 0$ is called constraint qualification. However, not all stationary points yield a solution of the original problem, as the method of Lagrange multipliers yields only a [necessary condition](https://en.wikipedia.org/wiki/Necessary_condition) for optimality in constrained problems. Sufficient conditions for a minimum or maximum [also exist](https://en.wikipedia.org/wiki/Bordered_Hessian), but if a particular [candidate solution](https://en.wikipedia.org/wiki/Candidate_solution) satisfies the sufficient conditions, it is only guaranteed that that solution is the best one *locally* – that is, it is better than any permissible nearby points. The *global* optimum can be found by comparing the values of the original objective function at the points satisfying the necessary and locally sufficient conditions.

The method of Lagrange multipliers relies on the intuition that at a maximum, *f*(*x*, *y*) cannot be increasing in the direction of any such neighboring point that also has *g* = 0. If it were, we could walk along *g* = 0 to get higher, meaning that the starting point wasn't actually the maximum. Viewed in this way, it is an exact analogue to testing if the derivative of an unconstrained function is 0, that is, we are verifying that the directional derivative is 0 in any relevant (viable) direction.

We can visualize [contours](https://en.wikipedia.org/wiki/Contour_line) of f given by *f*(*x*, *y*) = *d* for various values of d, and the contour of g given by *g*(*x*, *y*) = *c*.

Suppose we walk along the contour line with *g* = *c* . We are interested in finding points where f almost does not change as we walk, since these points might be maxima.

There are two ways this could happen:

1.  We could touch a contour line of f, since by definition f does not change as we walk along its contour lines. This would mean that the tangents to the contour lines of f and g are parallel here.
2.  We have reached a "level" part of f, meaning that f does not change in any direction.

To check the first possibility (we touch a contour line of f), notice that since the [gradient](https://en.wikipedia.org/wiki/Gradient) of a function is perpendicular to the contour lines, the tangents to the contour lines of f and g are parallel if and only if the gradients of f and g are parallel. Thus we want points (*x*, *y*) where   *g*(*x*, *y*) = *c*  and 

$$
\nabla _{x,y}f=\lambda \,\nabla _{x,y}g,
$$

 for some $\lambda$ where 

$$
\nabla _{x,y}f=\left({\frac {\partial f}{\partial x}},{\frac {\partial f}{\partial y}}\right),\qquad \nabla _{x,y}g=\left({\frac {\partial g}{\partial x}},{\frac {\partial g}{\partial y}}\right)
$$

 are the respective gradients. The constant $\lambda$ is required because although the two gradient vectors are parallel, the magnitudes of the gradient vectors are generally not equal. This constant is called the Lagrange multiplier. (In some conventions $\lambda$ is preceded by a minus sign).

Notice that this method also solves the second possibility, that f is level: if f is level, then its gradient is zero, and setting $\lambda =0$ is a solution regardless of $\nabla _{x,y}g$.

To incorporate these conditions into one equation, we introduce an auxiliary function 

$$
{\mathcal {L}}(x,y,\lambda )\equiv f(x,y)+\lambda \cdot g(x,y)\,,
$$

 and solve 

$$
\nabla _{x,y,\lambda }{\mathcal {L}}(x,y,\lambda )=0~.
$$

Note that this amounts to solving three equations in three unknowns. This is the method of Lagrange multipliers.

Note that $\ \nabla _{\lambda }{\mathcal {L}}(x,y,\lambda )=0\$ implies $\ g(x,y)=0\ ,$ as the partial derivative of ${\mathcal {L}}$ with respect to $\lambda$ is $\ g(x,y)~.$

To summarize 

$$
\nabla _{x,y,\lambda }{\mathcal {L}}(x,y,\lambda )=0\iff {\begin{cases}\nabla _{x,y}f(x,y)=-\lambda \,\nabla _{x,y}g(x,y)\\g(x,y)=0\end{cases}}
$$

The method generalizes readily to functions on $n$ variables 

$$
\nabla _{x_{1},\dots ,x_{n},\lambda }{\mathcal {L}}(x_{1},\dots ,x_{n},\lambda )=0
$$

 which amounts to solving *n* + 1 equations in *n* + 1 unknowns.

The constrained extrema of f are *[critical points](https://en.wikipedia.org/wiki/Critical_point_(mathematics) "Critical point (mathematics)")* of the Lagrangian ${\mathcal {L}}$, but they are not necessarily *local extrema* of ${\mathcal {L}}$ (see [§ Example 2](#Example_2) below).

One may [reformulate the Lagrangian](https://en.wikipedia.org/wiki/Hamiltonian_mechanics#As_a_reformulation_of_Lagrangian_mechanics) as a [Hamiltonian](https://en.wikipedia.org/wiki/Hamiltonian_(control_theory) "Hamiltonian (control theory)"), in which case the solutions are local minima for the Hamiltonian. This is done in [optimal control](https://en.wikipedia.org/wiki/Optimal_control) theory, in the form of [Pontryagin's maximum principle](https://en.wikipedia.org/wiki/Pontryagin%27s_maximum_principle).

The fact that solutions of the method of Lagrange multipliers are not necessarily extrema of the Lagrangian, also poses difficulties for numerical optimization. This can be addressed by minimizing the *magnitude* of the gradient of the Lagrangian, as these minima are the same as the zeros of the magnitude, as illustrated in [Example 5: Numerical optimization](#Example_5).

## Multiple constraints

![[media/57e68002c3ab3d16bdae676f7d4c545aac9ca5cd.png]]
Figure 2: A paraboloid constrained along two intersecting lines.

![[media/0d8202c234901d877c6a36e3254bb1cbb8ca3c1f.png]]
Figure 3: Contour map of Figure 2.

The method of Lagrange multipliers can be extended to solve problems with multiple constraints using a similar argument. Consider a [paraboloid](https://en.wikipedia.org/wiki/Paraboloid) subject to two line constraints that intersect at a single point. As the only feasible solution, this point is obviously a constrained extremum. However, the [level set](https://en.wikipedia.org/wiki/Level_set) of $f$ is clearly not parallel to either constraint at the intersection point (see Figure 3); instead, it is a linear combination of the two constraints' gradients. In the case of multiple constraints, that will be what we seek in general: The method of Lagrange seeks points not at which the gradient of $f$ is a multiple of any single constraint's gradient necessarily, but in which it is a linear combination of all the constraints' gradients.

Concretely, suppose we have $M$ constraints and are walking along the set of points satisfying $g_{i}(\mathbf {x} )=0,i=1,\dots ,M\,.$ Every point $\mathbf {x}$ on the contour of a given constraint function $g_{i}$ has a space of allowable directions: the space of vectors perpendicular to $\nabla g_{i}(\mathbf {x} )\,.$ The set of directions that are allowed by all constraints is thus the space of directions perpendicular to all of the constraints' gradients. Denote this space of allowable moves by $\ A\$ and denote the span of the constraints' gradients by $S\,.$ Then $A=S^{\perp }\,,$ the space of vectors perpendicular to every element of $S\,.$

We are still interested in finding points where $f$ does not change as we walk, since these points might be (constrained) extrema. We therefore seek $\mathbf {x}$ such that any allowable direction of movement away from $\mathbf {x}$ is perpendicular to $\nabla f(\mathbf {x} )$ (otherwise we could increase $f$ by moving along that allowable direction). In other words, $\nabla f(\mathbf {x} )\in A^{\perp }=S\,.$ Thus there are scalars $\lambda _{1},\lambda _{2},\ \dots ,\lambda _{M}$ such that 

$$
\nabla f(\mathbf {x} )=\sum _{k=1}^{M}\lambda _{k}\,\nabla g_{k}(\mathbf {x} )\quad \iff \quad \nabla f(\mathbf {x} )-\sum _{k=1}^{M}{\lambda _{k}\nabla g_{k}(\mathbf {x} )}=0~.
$$

These scalars are the Lagrange multipliers. We now have $M$ of them, one for every constraint.

As before, we introduce an auxiliary function 

$$
{\mathcal {L}}\left(x_{1},\ldots ,x_{n},\lambda _{1},\ldots ,\lambda _{M}\right)=f\left(x_{1},\ldots ,x_{n}\right)-\sum \limits _{k=1}^{M}{\lambda _{k}g_{k}\left(x_{1},\ldots ,x_{n}\right)}\
$$

 and solve 

$$
\nabla _{x_{1},\ldots ,x_{n},\lambda _{1},\ldots ,\lambda _{M}}{\mathcal {L}}(x_{1},\ldots ,x_{n},\lambda _{1},\ldots ,\lambda _{M})=0\iff {\begin{cases}\nabla f(\mathbf {x} )-\sum _{k=1}^{M}{\lambda _{k}\,\nabla g_{k}(\mathbf {x} )}=0\\g_{1}(\mathbf {x} )=\cdots =g_{M}(\mathbf {x} )=0\end{cases}}
$$

 which amounts to solving $n+M$ equations in $\ n+M\$ unknowns.

The constraint qualification assumption when there are multiple constraints is that the constraint gradients at the relevant point are linearly independent.

## Modern formulation via differentiable manifolds

The problem of finding the local maxima and minima subject to constraints can be generalized to finding local maxima and minima on a [differentiable manifold](https://en.wikipedia.org/wiki/Differentiable_manifold) $\ M~.$ In what follows, it is not necessary that $M$ be a Euclidean space, or even a [Riemannian manifold](https://en.wikipedia.org/wiki/Riemannian_manifold). All appearances of the gradient $\ \nabla \$ (which depends on a choice of Riemannian metric) can be replaced with the [exterior derivative](https://en.wikipedia.org/wiki/Exterior_derivative) $\ \operatorname {d} ~.$

### Single constraint

Let $\ M\$ be a [smooth manifold](https://en.wikipedia.org/wiki/Smooth_manifold) of dimension $\ m~.$ Suppose that we wish to find the stationary points $\ x\$ of a smooth function $\ f:M\to \mathbb {R} \$ when restricted to the submanifold $\ N\$ defined by $\ g(x)=0\ ,$ where $\ g:M\to \mathbb {R} \$ is a smooth function for which 0 is a [regular value](https://en.wikipedia.org/wiki/Regular_value).

Let $\ \operatorname {d} f\$ and $\ \operatorname {d} g\$ be the [exterior derivatives](https://en.wikipedia.org/wiki/Exterior_derivative) of $\ f\$ and $\ g\$. Stationarity for the restriction $\ f|_{N}\$ at $\ x\in N\$ means $\ \operatorname {d} (f|_{N})_{x}=0~.$ Equivalently, the kernel $\ \ker(\operatorname {d} f_{x})\$ contains $\ T_{x}N=\ker(\operatorname {d} g_{x})~.$ In other words, $\ \operatorname {d} f_{x}\$ and $\ \operatorname {d} g_{x}\$ are proportional 1-forms. For this it is necessary and sufficient that the following system of $\ {\tfrac {1}{2}}m(m-1)\$ equations holds: 

$$
\operatorname {d} f_{x}\wedge \operatorname {d} g_{x}=0\in \Lambda ^{2}(T_{x}^{\ast }M)
$$

 where $\ \wedge \$ denotes the [exterior product](https://en.wikipedia.org/wiki/Exterior_algebra). The stationary points $\ x\$ are the solutions of the above system of equations plus the constraint $\ g(x)=0~.$ Note that the $\ {\tfrac {1}{2}}m(m-1)\$ equations are not independent, since the left-hand side of the equation belongs to the subvariety of $\ \Lambda ^{2}(T_{x}^{\ast }M)\$ consisting of [decomposable elements](https://en.wikipedia.org/wiki/Exterior_algebra).

In this formulation, it is not necessary to explicitly find the Lagrange multiplier, a number $\ \lambda \$ such that $\ \operatorname {d} f_{x}=\lambda \cdot \operatorname {d} g_{x}~.$

### Multiple constraints

Let $\ M\$ and $\ f\$ be as in the above section regarding the case of a single constraint. Rather than the function $g$ described there, now consider a smooth function $\ G:M\to \mathbb {R} ^{p}(p>1)\ ,$ with component functions $\ g_{i}:M\to \mathbb {R} \ ,$ for which $0\in \mathbb {R} ^{p}$ is a [regular value](https://en.wikipedia.org/wiki/Regular_value). Let $N$ be the submanifold of $\ M\$ defined by $\ G(x)=0~.$

$\ x\$ is a stationary point of $f|_{N}$ if and only if $\ \ker(\operatorname {d} f_{x})\$ contains $\ \ker(\operatorname {d} G_{x})~.$ For convenience let $\ L_{x}=\operatorname {d} f_{x}\$ and $\ K_{x}=\operatorname {d} G_{x}\ ,$ where $\ \operatorname {d} G$ denotes the tangent map or Jacobian $\ TM\to T\mathbb {R} ^{p}~$ ($\ T_{x}\mathbb {R} ^{p}$ can be canonically identified with $\ \mathbb {R} ^{p}$). The subspace $\ker(K_{x})$ has dimension smaller than that of $\ker(L_{x})$, namely $\ \dim(\ker(L_{x}))=n-1\$ and $\ \dim(\ker(K_{x}))=n-p~.$ $\ker(K_{x})$ belongs to $\ \ker(L_{x})\$ if and only if $L_{x}\in T_{x}^{\ast }M$ belongs to the image of $\ K_{x}^{\ast }:\mathbb {R} ^{p\ast }\to T_{x}^{\ast }M~.$ Computationally speaking, the condition is that $L_{x}$ belongs to the row space of the matrix of $\ K_{x}\ ,$ or equivalently the column space of the matrix of $K_{x}^{\ast }$ (the transpose). If $\ \omega _{x}\in \Lambda ^{p}(T_{x}^{\ast }M)\$ denotes the exterior product of the columns of the matrix of $\ K_{x}^{\ast }\ ,$ the stationary condition for $\ f|_{N}\$ at $\ x\$ becomes 

$$
L_{x}\wedge \omega _{x}=0\in \Lambda ^{p+1}\left(T_{x}^{\ast }M\right)
$$

 Once again, in this formulation it is not necessary to explicitly find the Lagrange multipliers, the numbers $\ \lambda _{1},\ldots ,\lambda _{p}\$ such that 

$$
\ \operatorname {d} f_{x}=\sum _{i=1}^{p}\lambda _{i}\operatorname {d} (g_{i})_{x}~.
$$

## Interpretation of the Lagrange multipliers

In this section, we modify the constraint equations from the form $g_{i}({\bf {x}})=0$ to the form $\ g_{i}({\bf {x}})=c_{i}\ ,$ where the $\ c_{i}\$ are m real constants that are considered to be additional arguments of the Lagrangian expression ${\mathcal {L}}$.

Often the Lagrange multipliers have an interpretation as some quantity of interest. For example, by parametrising the constraint's contour line, that is, if the Lagrangian expression is 

$$
{\begin{aligned}&{\mathcal {L}}(x_{1},x_{2},\ldots ;\lambda _{1},\lambda _{2},\ldots ;c_{1},c_{2},\ldots )\\[4pt]={}&f(x_{1},x_{2},\ldots )+\lambda _{1}(c_{1}-g_{1}(x_{1},x_{2},\ldots ))+\lambda _{2}(c_{2}-g_{2}(x_{1},x_{2},\dots ))+\cdots \end{aligned}}
$$

 then 

$$
\ {\frac {\partial {\mathcal {L}}}{\partial c_{k}}}=\lambda _{k}~.
$$

So, *λ<sub>k</sub>* is the rate of change of the quantity being optimized as a function of the constraint parameter. As examples, in [Lagrangian mechanics](https://en.wikipedia.org/wiki/Lagrangian_mechanics) the equations of motion are derived by finding stationary points of the [action](https://en.wikipedia.org/wiki/Action_(physics) "Action (physics)"), the time integral of the difference between kinetic and potential energy. Thus, the force on a particle due to a scalar potential, *F* = −∇*V*, can be interpreted as a Lagrange multiplier determining the change in action (transfer of potential to kinetic energy) following a variation in the particle's constrained trajectory. In control theory this is formulated instead as [costate equations](https://en.wikipedia.org/wiki/Costate_equations).

Moreover, by the [envelope theorem](https://en.wikipedia.org/wiki/Envelope_theorem) the optimal value of a Lagrange multiplier has an interpretation as the marginal effect of the corresponding constraint constant upon the optimal attainable value of the original objective function: If we denote values at the optimum with a star ($\star$), then it can be shown that 

$$
{\frac {\ \operatorname {d} f\left(\ x_{1\star }(c_{1},c_{2},\dots ),\ x_{2\star }(c_{1},c_{2},\dots ),\ \dots \ \right)\ }{\operatorname {d} c_{k}}}=\lambda _{\star k}~.
$$

For example, in economics the optimal profit to a player is calculated subject to a constrained space of actions, where a Lagrange multiplier is the change in the optimal value of the objective function (profit) due to the relaxation of a given constraint (e.g. through a change in income); in such a context $\ \lambda _{\star k}\$ is the [marginal cost](https://en.wikipedia.org/wiki/Marginal_cost) of the constraint, and is referred to as the [shadow price](https://en.wikipedia.org/wiki/Shadow_price).

## Sufficient conditions

Sufficient conditions for a constrained local maximum or minimum can be stated in terms of a sequence of principal minors (determinants of upper-left-justified sub-matrices) of the bordered [[Hessian Matrix]] of second derivatives of the Lagrangian expression.

## Examples

### Example 1

![[media/d1331ea38fe78ecac8a80beab3ab3f92a7c5be3a.png]]
Illustration of the constrained optimization problem <strong>1</strong>

Suppose we wish to maximize $\ f(x,y)=x+y\$ subject to the constraint $\ x^{2}+y^{2}=1~.$ The [feasible set](https://en.wikipedia.org/wiki/Candidate_solution) is the unit circle, and the [level sets](https://en.wikipedia.org/wiki/Level_set) of f are diagonal lines (with slope −1), so we can see graphically that the maximum occurs at $\ \left({\tfrac {1}{\sqrt {2}}},{\tfrac {1}{\sqrt {2}}}\right)\ ,$ and that the minimum occurs at $\ \left(-{\tfrac {1}{\sqrt {2}}},-{\tfrac {1}{\sqrt {2}}}\right)~.$

For the method of Lagrange multipliers, the constraint is 

$$
g(x,y)=x^{2}+y^{2}-1=0\ ,
$$

 hence the Lagrangian function, 

$$
{\begin{aligned}{\mathcal {L}}(x,y,\lambda )&=f(x,y)+\lambda \cdot g(x,y)\\[4pt]&=x+y+\lambda (x^{2}+y^{2}-1)\ ,\end{aligned}}
$$

 is a function that is equivalent to $\ f(x,y)\$ when $\ g(x,y)\$ is set to 0.

Now we can calculate the gradient: 

$$
{\begin{aligned}\nabla _{x,y,\lambda }{\mathcal {L}}(x,y,\lambda )&=\left({\frac {\partial {\mathcal {L}}}{\partial x}},{\frac {\partial {\mathcal {L}}}{\partial y}},{\frac {\partial {\mathcal {L}}}{\partial \lambda }}\right)\\[4pt]&=\left(1+2\lambda x,1+2\lambda y,x^{2}+y^{2}-1\right)\ \color {gray}{,}\end{aligned}}
$$

 and therefore: 

$$
\nabla _{x,y,\lambda }{\mathcal {L}}(x,y,\lambda )=0\quad \Leftrightarrow \quad {\begin{cases}1+2\lambda x=0\\1+2\lambda y=0\\x^{2}+y^{2}-1=0\end{cases}}
$$

Notice that the last equation is the original constraint.

The first two equations yield 

$$
x=y=-{\frac {1}{2\lambda }},\qquad \lambda \neq 0~.
$$

 By substituting into the last equation we have: 

$$
{\frac {1}{4\lambda ^{2}}}+{\frac {1}{4\lambda ^{2}}}-1=0\ ,
$$

 so 

$$
\lambda =\pm {\frac {1}{\sqrt {2\ }}}\ ,
$$

 which implies that the stationary points of ${\mathcal {L}}$ are 

$$
\left({\tfrac {\sqrt {2\ }}{2}},{\tfrac {\sqrt {2\ }}{2}},-{\tfrac {1}{\sqrt {2\ }}}\right),\qquad \left(-{\tfrac {\sqrt {2\ }}{2}},-{\tfrac {\sqrt {2\ }}{2}},{\tfrac {1}{\sqrt {2\ }}}\right)~.
$$

Evaluating the objective function f at these points yields 

$$
f\left({\tfrac {\sqrt {2\ }}{2}},{\tfrac {\sqrt {2\ }}{2}}\right)={\sqrt {2\ }}\ ,\qquad f\left(-{\tfrac {\sqrt {2\ }}{2}},-{\tfrac {\sqrt {2\ }}{2}}\right)=-{\sqrt {2\ }}~.
$$

Thus the constrained maximum is $\ {\sqrt {2\ }}\$ and the constrained minimum is $-{\sqrt {2}}$.

### Example 2

![[media/11acf76673e9fdd42e2cfa4fcd0ce38a30b8b91e.png]]
Illustration of the constrained optimization problem <strong>2</strong>

Now we modify the objective function of Example **1** so that we minimize $\ f(x,y)=(x+y)^{2}\$ instead of $\ f(x,y)=x+y\ ,$ again along the circle $\ g(x,y)=x^{2}+y^{2}-1=0~.$ Now the level sets of $f$ are still lines of slope −1, and the points on the circle tangent to these level sets are again $\ ({\sqrt {2}}/2,{\sqrt {2}}/2)\$ and $\ (-{\sqrt {2}}/2,-{\sqrt {2}}/2)~.$ These tangency points are maxima of $\ f~.$

On the other hand, the minima occur on the level set for $\ f=0\$ (since by its construction $\ f\$ cannot take negative values), at $\ ({\sqrt {2}}/2,-{\sqrt {2}}/2)\$ and $\ (-{\sqrt {2}}/2,{\sqrt {2}}/2)\ ,$ where the level curves of $\ f\$ are not tangent to the constraint. The condition that $\ \nabla _{x,y,\lambda }\left(f(x,y)+\lambda \cdot g(x,y)\right)=0\$ correctly identifies all four points as extrema; the minima are characterized in by $\ \lambda =0\$ and the maxima by $\ \lambda =-2~.$

### Example 3

![[media/a69f415445696ad7a7649d6a079e7ad82ab668bf.png]]
Illustration of constrained optimization problem <strong>3</strong>.

This example deals with more strenuous calculations, but it is still a single constraint problem.

Suppose one wants to find the maximum values of 

$$
f(x,y)=x^{2}y
$$

 with the condition that the $\ x\$- and $\ y\$-coordinates lie on the circle around the origin with radius $\ {\sqrt {3\ }}~.$ That is, subject to the constraint 

$$
g(x,y)=x^{2}+y^{2}-3=0~.
$$

As there is just a single constraint, there is a single multiplier, say $\ \lambda ~.$

The constraint $\ g(x,y)\$ is identically zero on the circle of radius $\ {\sqrt {3\ }}~.$ Any multiple of $\ g(x,y)\$ may be added to $\ g(x,y)\$ leaving $\ g(x,y)\$ unchanged in the region of interest (on the circle where our original constraint is satisfied).

Applying the ordinary Lagrange multiplier method yields 

$$
{\begin{aligned}{\mathcal {L}}(x,y,\lambda )&=f(x,y)+\lambda \cdot g(x,y)\\&=x^{2}y+\lambda (x^{2}+y^{2}-3)\ ,\end{aligned}}
$$

 from which the gradient can be calculated: 

$$
{\begin{aligned}\nabla _{x,y,\lambda }{\mathcal {L}}(x,y,\lambda )&=\left({\frac {\partial {\mathcal {L}}}{\partial x}},{\frac {\partial {\mathcal {L}}}{\partial y}},{\frac {\partial {\mathcal {L}}}{\partial \lambda }}\right)\\&=\left(2xy+2\lambda x,x^{2}+2\lambda y,x^{2}+y^{2}-3\right)~.\end{aligned}}
$$

 And therefore: 

$$
\nabla _{x,y,\lambda }{\mathcal {L}}(x,y,\lambda )=0\quad \iff \quad {\begin{cases}2xy+2\lambda x=0\\x^{2}+2\lambda y=0\\x^{2}+y^{2}-3=0\end{cases}}\quad \iff \quad {\begin{cases}x(y+\lambda )=0&{\text{(i)}}\\x^{2}=-2\lambda y&{\text{(ii)}}\\x^{2}+y^{2}=3&{\text{(iii)}}\end{cases}}
$$

 (iii) is just the original constraint. (i) implies $\ x=0\$ or $\ \lambda =-y~.$ If $x=0$ then $\ y=\pm {\sqrt {3\ }}\$ by (iii) and consequently $\ \lambda =0\$ from (ii). If $\ \lambda =-y\ ,$ substituting this into (ii) yields $\ x^{2}=2y^{2}~.$ Substituting this into (iii) and solving for $\ y\$ gives $\ y=\pm 1~.$ Thus there are six critical points of $\ {\mathcal {L}}\ :$ 

$$
({\sqrt {2\ }},1,-1);\quad (-{\sqrt {2\ }},1,-1);\quad ({\sqrt {2\ }},-1,1);\quad (-{\sqrt {2\ }},-1,1);\quad (0,{\sqrt {3\ }},0);\quad (0,-{\sqrt {3\ }},0)~.
$$

Evaluating the objective at these points, one finds that 

$$
f(\pm {\sqrt {2\ }},1)=2;\quad f(\pm {\sqrt {2\ }},-1)=-2;\quad f(0,\pm {\sqrt {3\ }})=0~.
$$

Therefore, the objective function attains the [global maximum](https://en.wikipedia.org/wiki/Global_maximum) (subject to the constraints) at $\ (\pm {\sqrt {2\ }},1\ )$ and the [global minimum](https://en.wikipedia.org/wiki/Global_minimum) at $\ (\pm {\sqrt {2\ }},-1)~.$ The point $\ (0,{\sqrt {3\ }})\$ is a [local minimum](https://en.wikipedia.org/wiki/Local_minimum) of $\ f\$ and $\ (0,-{\sqrt {3\ }})\$ is a [local maximum](https://en.wikipedia.org/wiki/Local_maximum) of $\ f\ ,$ as may be determined by consideration of the [Hessian matrix](https://en.wikipedia.org/wiki/Hessian_(mathematics)#Bordered_Hessian) of $\ {\mathcal {L}}(x,y,0)~.$

Note that while $\ ({\sqrt {2\ }},1,-1)\$ is a critical point of $\ {\mathcal {L}}\ ,$ it is not a local extremum of $\ {\mathcal {L}}~.$ We have 

$$
{\mathcal {L}}\left({\sqrt {2\ }}+\varepsilon ,1,-1+\delta \right)=2+\delta \left(\varepsilon ^{2}+\left(2{\sqrt {2\ }}\right)\varepsilon \right)~.
$$

Given any neighbourhood of $\ ({\sqrt {2\ }},1,-1)\ ,$ one can choose a small positive $\ \varepsilon \$ and a small $\ \delta \$ of either sign to get $\ {\mathcal {L}}$ values both greater and less than $\ 2~.$ This can also be seen from the Hessian matrix of $\ {\mathcal {L}}\$ evaluated at this point (or indeed at any of the critical points) which is an [indefinite matrix](https://en.wikipedia.org/wiki/Indefinite_matrix). Each of the critical points of $\ {\mathcal {L}}\$ is a [saddle point](https://en.wikipedia.org/wiki/Saddle_point) of $\ {\mathcal {L}}~.$

### Example 4 – Entropy

Suppose we wish to find the [discrete probability distribution](https://en.wikipedia.org/wiki/Probability_distribution#Discrete_probability_distribution) on the points $\ \{p_{1},p_{2},\ldots ,p_{n}\}\$ with maximal [information entropy](https://en.wikipedia.org/wiki/Information_entropy). This is the same as saying that we wish to find the [least structured](https://en.wikipedia.org/wiki/Principle_of_maximum_entropy) probability distribution on the points $\ \{p_{1},p_{2},\cdots ,p_{n}\}~.$ In other words, we wish to maximize the [Shannon entropy](https://en.wikipedia.org/wiki/Shannon_entropy) equation: 

$$
f(p_{1},p_{2},\ldots ,p_{n})=-\sum _{j=1}^{n}p_{j}\log _{2}p_{j}~.
$$

For this to be a probability distribution the sum of the probabilities $\ p_{i}\$ at each point $\ x_{i}\$ must equal 1, so our constraint is: 

$$
g(p_{1},p_{2},\ldots ,p_{n})=\sum _{j=1}^{n}p_{j}=1~.
$$

We use Lagrange multipliers to find the point of maximum entropy, $\ {\vec {p}}^{\,*}\ ,$ across all discrete probability distributions $\ {\vec {p}}\$ on $\ \{x_{1},x_{2},\ldots ,x_{n}\}~.$ We require that: 

$$
\left.{\frac {\partial }{\partial {\vec {p}}}}(f+\lambda (g-1))\right|_{{\vec {p}}={\vec {p}}^{\,*}}=0\ ,
$$

 which gives a system of n equations, $\ k=1,\ \ldots ,n\ ,$ such that: 

$$
\left.{\frac {\partial }{\partial p_{k}}}\left\{-\left(\sum _{j=1}^{n}p_{j}\log _{2}p_{j}\right)+\lambda \left(\sum _{j=1}^{n}p_{j}-1\right)\right\}\right|_{p_{k}=p_{\star k}}=0~.
$$

Carrying out the differentiation of these n equations, we get 

$$
-\left({\frac {1}{\ln 2}}+\log _{2}p_{\star k}\right)+\lambda =0~.
$$

This shows that all $\ p_{\star k}\$ are equal (because they depend on λ only). By using the constraint 

$$
\sum _{j}p_{j}=1\ ,
$$

 we find 

$$
p_{\star k}={\frac {1}{n}}~.
$$

Hence, the uniform distribution is the distribution with the greatest entropy, among distributions on n points.

### Example 5 – Numerical optimization

![[media/8f6370cfd90716707ce9869ac2146d96df5d1671.png]]
Lagrange multipliers cause the critical points to occur at saddle points (Example <strong>5</strong>).

![[media/cb76139572fb9020438d3b3ebe8b0ba8fba2d440.png]]
The magnitude of the gradient can be used to force the critical points to occur at local minima (Example <strong>5</strong>).

The critical points of Lagrangians occur at [saddle points](https://en.wikipedia.org/wiki/Saddle_point), rather than at local maxima (or minima). Unfortunately, many numerical optimization techniques, such as [hill climbing](https://en.wikipedia.org/wiki/Hill_climbing), [[Gradient Descent]], some of the [quasi-Newton methods](https://en.wikipedia.org/wiki/Quasi-Newton_method), among others, are designed to find local maxima (or minima) and not saddle points. For this reason, one must either modify the formulation to ensure that it's a minimization problem (for example, by extremizing the square of the [gradient](https://en.wikipedia.org/wiki/Gradient) of the Lagrangian as below), or else use an optimization technique that finds [stationary points](https://en.wikipedia.org/wiki/Stationary_points) (such as [Newton's method](https://en.wikipedia.org/wiki/Newton%27s_method_in_optimization) without an extremum seeking [[Line Search]]) and not necessarily extrema.

As a simple example, consider the problem of finding the value of x that minimizes $\ f(x)=x^{2}\ ,$ constrained such that $\ x^{2}=1~.$ (This problem is somewhat untypical because there are only two values that satisfy this constraint, but it is useful for illustration purposes because the corresponding unconstrained function can be visualized in three dimensions.)

Using Lagrange multipliers, this problem can be converted into an unconstrained optimization problem: 

$$
{\mathcal {L}}(x,\lambda )=x^{2}+\lambda (x^{2}-1)~.
$$

The two critical points occur at saddle points where *x* = 1 and *x* = −1.

In order to solve this problem with a numerical optimization technique, we must first transform this problem such that the critical points occur at local minima. This is done by computing the magnitude of the gradient of the unconstrained optimization problem.

First, we compute the partial derivative of the unconstrained problem with respect to each variable: 

$$
{\begin{aligned}&{\frac {\partial {\mathcal {L}}}{\partial x}}=2x+2x\lambda \\[5pt]&{\frac {\partial {\mathcal {L}}}{\partial \lambda }}=x^{2}-1~.\end{aligned}}
$$

If the target function is not easily differentiable, the differential with respect to each variable can be approximated as 

$$
{\begin{aligned}{\frac {\ \partial {\mathcal {L}}\ }{\partial x}}\approx {\frac {{\mathcal {L}}(x+\varepsilon ,\lambda )-{\mathcal {L}}(x,\lambda )}{\varepsilon }},\\[5pt]{\frac {\ \partial {\mathcal {L}}\ }{\partial \lambda }}\approx {\frac {{\mathcal {L}}(x,\lambda +\varepsilon )-{\mathcal {L}}(x,\lambda )}{\varepsilon }},\end{aligned}}
$$

 where $\varepsilon$ is a small value.

Next, we compute the magnitude of the gradient, which is the square root of the sum of the squares of the partial derivatives: 

$$
{\begin{aligned}h(x,\lambda )&={\sqrt {(2x+2x\lambda )^{2}+(x^{2}-1)^{2}\ }}\\[4pt]&\approx {\sqrt {\left({\frac {\ {\mathcal {L}}(x+\varepsilon ,\lambda )-{\mathcal {L}}(x,\lambda )\ }{\varepsilon }}\right)^{2}+\left({\frac {\ {\mathcal {L}}(x,\lambda +\varepsilon )-{\mathcal {L}}(x,\lambda )\ }{\varepsilon }}\right)^{2}\ }}~.\end{aligned}}
$$

(Since magnitude is always non-negative, optimizing over the squared-magnitude is equivalent to optimizing over the magnitude. Thus, the "square root" may be omitted from these equations with no expected difference in the results of optimization.)

The critical points of h occur at *x* = 1 and *x* = −1, just as in ${\mathcal {L}}~.$ Unlike the critical points in ${\mathcal {L}}\,,$ however, the critical points in h occur at local minima, so numerical optimization techniques can be used to find them.

## Applications

### Lagrangian Mechanics

In [Lagrangian Mechanics](https://en.wikipedia.org/wiki/Lagrangian_mechanics), the Euler-Lagrange equations can be augmented with Lagrange multipliers as a method to impose physical constraints on systems. This method is not required in general, because an alternative method is to choose a set of linearly independent generalised coordinates such that the constraints are implicitly imposed.

When Lagrange multipliers are used, the constraint equations need to be simultaneously solved with the Euler-Lagrange equations. Hence, the equations become a system of [differential algebraic equations](https://en.wikipedia.org/wiki/Differential-algebraic_system_of_equations) (as opposed to a system of [ordinary differential equations](https://en.wikipedia.org/wiki/Ordinary_differential_equation)).

The method of Lagrange multipliers is useful when it is difficult to write the Lagrangian in terms of a set of linearly independent generalised coordinates. For example, for use in programmatic dynamical systems modelling algorithms, or for use in modelling systems with closed kinematic chains. They are also useful for imposing non-holonomic constraints.

Given a set of holonomic constraint equations $f_{j}(\mathbf {q} ,t)=0$, the Euler-Lagrange equations with Lagrange multipliers can be written as

$$
{\frac {\mathrm {d} }{\mathrm {d} t}}{\frac {\partial L}{\partial {\dot {q}}_{i}}}-{\frac {\partial L}{\partial q_{i}}}+\underbrace {\sum _{j=1}^{C}\lambda _{j}{\frac {\partial f_{j}}{\partial q_{i}}}} _{-\tau _{i,{\text{constraint}}}}=\tau _{i}
$$

The meaning of $\tau _{i,{\text{constraint}}}$ can be interpreted by moving it to the other side of the equation and absorbing it into the generalised force term $\tau _{i}$. In this interpretation, the system has $C$ number of additional degrees of freedom, and there are no additionally imposed constraints, but the constraint forces $\tau _{i,{\text{constraint}}}$ just happen to have the right values such that the constraints hold.

### Control theory

In [optimal control](https://en.wikipedia.org/wiki/Optimal_control) theory, the Lagrange multipliers are interpreted as [costate](https://en.wikipedia.org/wiki/Costate) variables, and Lagrange multipliers are reformulated as the minimization of the [Hamiltonian](https://en.wikipedia.org/wiki/Hamiltonian_(control_theory) "Hamiltonian (control theory)"), in [Pontryagin's maximum principle](https://en.wikipedia.org/wiki/Pontryagin%27s_maximum_principle).

### Nonlinear programming

The Lagrange multiplier method has several generalizations. In [nonlinear programming](https://en.wikipedia.org/wiki/Nonlinear_programming) there are several multiplier rules, e.g. the Carathéodory–John Multiplier Rule and the Convex Multiplier Rule, for inequality constraints.

### Economics

In many models in [mathematical economics](https://en.wikipedia.org/wiki/Mathematical_economics) such as [general equilibrium models](https://en.wikipedia.org/wiki/General_equilibrium_model), consumer behavior is implemented as [utility maximization](https://en.wikipedia.org/wiki/Utility_maximization_problem) and firm behavior as [profit maximization](https://en.wikipedia.org/wiki/Profit_maximization), both entities being subject to constraints such as [budget constraints](https://en.wikipedia.org/wiki/Budget_constraint) and [production constraints](https://en.wikipedia.org/wiki/Production_function). The usual way to determine an optimal solution is achieved by maximizing some function, where the constraints are enforced using Lagrangian multipliers.

### Power systems

Methods based on Lagrange multipliers have applications in [power systems](https://en.wikipedia.org/wiki/Power_systems), e.g. in distributed-energy-resources (DER) placement and load shedding.

### Safe Reinforcement Learning

The method of Lagrange multipliers applies to constrained [Markov decision processes](https://en.wikipedia.org/wiki/Markov_decision_processes). It naturally produces gradient-based primal-dual algorithms in safe reinforcement learning.

### [Normalized solutions](https://en.wikipedia.org/wiki/Normalized_solution_(mathematics) "Normalized solution (mathematics)")

Considering the PDE problems with constraints, i.e., the study of the properties of the normalized solutions, Lagrange multipliers play an important role.

## See also

- [Adjustment of observations](https://en.wikipedia.org/wiki/Adjustment_of_observations)
- [Duality](https://en.wikipedia.org/wiki/Duality_(optimization) "Duality (optimization)")
- [Gittins index](https://en.wikipedia.org/wiki/Gittins_index)
- [Karush–Kuhn–Tucker conditions](https://en.wikipedia.org/wiki/Karush%E2%80%93Kuhn%E2%80%93Tucker_conditions): generalization of the method of Lagrange multipliers
- [Lagrange multipliers on Banach spaces](https://en.wikipedia.org/wiki/Lagrange_multipliers_on_Banach_spaces): another generalization of the method of Lagrange multipliers
- [Lagrange multiplier test](https://en.wikipedia.org/wiki/Lagrange_multiplier_test) in maximum likelihood estimation
- [Lagrangian relaxation](https://en.wikipedia.org/wiki/Lagrangian_relaxation)

## References

1.  Hoffmann, Laurence D.; Bradley, Gerald L. (2004). *Calculus for Business, Economics, and the Social and Life Sciences* (8th ed.). McGraw Hill Higher Education. pp. 575–588. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-07-242432-X](https://en.wikipedia.org/wiki/Special:BookSources/0-07-242432-X).
2.  Beavis, Brian; Dobbs, Ian M. (1990). ["Static Optimization"](https://books.google.com/books?id=L7HMACFgnXMC&pg=PA40). *Optimization and Stability Theory for Economic Analysis*. New York: Cambridge University Press. p. 40. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-33605-8](https://en.wikipedia.org/wiki/Special:BookSources/0-521-33605-8).
3.  [Protter, Murray H.](https://en.wikipedia.org/wiki/Murray_H._Protter); [Morrey, Charles B. Jr.](https://en.wikipedia.org/wiki/Charles_B._Morrey_Jr.) (1985). *Intermediate Calculus* (2nd ed.). New York, NY: Springer. p. 267. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-96058-9](https://en.wikipedia.org/wiki/Special:BookSources/0-387-96058-9).
4.  ^    Walsh, G.R. (1975). ["Saddle-point Property of Lagrangian Function"](https://books.google.com/books?id=K0EZAQAAIAAJ&pg=PA39). *Methods of Optimization*. New York, NY: John Wiley & Sons. pp. 39–44. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-91922-5](https://en.wikipedia.org/wiki/Special:BookSources/0-471-91922-5).
5.  Kalman, Dan (2009). "Leveling with Lagrange: An alternate view of constrained optimization". *[Mathematics Magazine](https://en.wikipedia.org/wiki/Mathematics_Magazine)*. **82** (3): 186–196. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/0025570X.2009.11953617](https://doi.org/10.1080%2F0025570X.2009.11953617). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [27765899](https://www.jstor.org/stable/27765899). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [121070192](https://api.semanticscholar.org/CorpusID:121070192).
6.  ^   Silberberg, Eugene; Suen, Wing (2001). *The Structure of Economics: A Mathematical Analysis* (Third ed.). Boston: Irwin McGraw-Hill. pp. 134–141. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-07-234352-4](https://en.wikipedia.org/wiki/Special:BookSources/0-07-234352-4).
7.  de la Fuente, Angel (2000). [Mathematical Methods and Models for Economists](https://archive.org/details/mathematicalmeth00fuen). Cambridge: Cambridge University Press. p. [285](https://archive.org/details/mathematicalmeth00fuen/page/n288). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1017/CBO9780511810756](https://doi.org/10.1017%2FCBO9780511810756). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-58512-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-58512-5).
8.  [Luenberger, David G.](https://en.wikipedia.org/wiki/David_Luenberger) (1969). *Optimization by Vector Space Methods*. New York: John Wiley & Sons. pp. 188–189.
9.  [Bertsekas, Dimitri P.](https://en.wikipedia.org/wiki/Dimitri_P._Bertsekas) (1999). *Nonlinear Programming* (Second ed.). Cambridge, MA: Athena Scientific. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [1-886529-00-0](https://en.wikipedia.org/wiki/Special:BookSources/1-886529-00-0).
10. Vapnyarskii, I.B. (2001) \[1994\], ["Lagrange multipliers"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society).
11. Lasdon, Leon S. (2002) \[1970\]. *Optimization Theory for Large Systems* (reprint ed.). Mineola, New York, NY: Dover. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-486-41999-1](https://en.wikipedia.org/wiki/Special:BookSources/0-486-41999-1). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1888251](https://mathscinet.ams.org/mathscinet-getitem?mr=1888251).
12. Hiriart-Urruty, Jean-Baptiste; [Lemaréchal, Claude](https://en.wikipedia.org/wiki/Claude_Lemar%C3%A9chal) (1993). "Chapter XII: Abstract duality for practitioners". *Convex analysis and minimization algorithms*. Grundlehren der Mathematischen Wissenschaften \[Fundamental Principles of Mathematical Sciences\]. Vol. 306. Berlin, DE: Springer-Verlag. pp. 136–193 (and Bibliographical comments pp. 334–335). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [3-540-56852-2](https://en.wikipedia.org/wiki/Special:BookSources/3-540-56852-2). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1295240](https://mathscinet.ams.org/mathscinet-getitem?mr=1295240). Volume II: Advanced theory and bundle methods.
13. [Lemaréchal, Claude](https://en.wikipedia.org/wiki/Claude_Lemar%C3%A9chal) (15–19 May 2000). "Lagrangian relaxation". In Jünger, Michael; Naddef, Denis (eds.). *Computational combinatorial optimization: Papers from the Spring School held in Schloß Dagstuhl*. Spring School held in Schloß Dagstuhl, May 15–19, 2000. Lecture Notes in Computer Science. Vol. 2241. Berlin, DE: Springer-Verlag (published 2001). pp. 112–156. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/3-540-45586-8_4](https://doi.org/10.1007%2F3-540-45586-8_4). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [3-540-42877-1](https://en.wikipedia.org/wiki/Special:BookSources/3-540-42877-1). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1900016](https://mathscinet.ams.org/mathscinet-getitem?mr=1900016). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [9048698](https://api.semanticscholar.org/CorpusID:9048698).
14. Lafontaine, Jacques (2015). [An Introduction to Differential Manifolds](https://books.google.com/books?id=KNhJCgAAQBAJ&pg=PA70). Springer. p. 70. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-319-20735-3](https://en.wikipedia.org/wiki/Special:BookSources/978-3-319-20735-3).
15. [Dixit, Avinash K.](https://en.wikipedia.org/wiki/Avinash_Dixit) (1990). ["Shadow Prices"](https://books.google.com/books?id=dHrsHz0VocUC&pg=PA40). *Optimization in Economic Theory* (2nd ed.). New York: Oxford University Press. pp. 40–54. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-19-877210-6](https://en.wikipedia.org/wiki/Special:BookSources/0-19-877210-6).
16. [Chiang, Alpha C.](https://en.wikipedia.org/wiki/Alpha_Chiang) (1984). [Fundamental Methods of Mathematical Economics](https://archive.org/details/fundamentalmetho0000chia_h4v2) (Third ed.). McGraw-Hill. p. [386](https://archive.org/details/fundamentalmetho0000chia_h4v2/page/386). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-07-010813-7](https://en.wikipedia.org/wiki/Special:BookSources/0-07-010813-7).
17. [Heath, Michael T.](https://en.wikipedia.org/wiki/Michael_Heath_(computer_scientist) "Michael Heath (computer scientist)") (2005). [Scientific Computing: An introductory survey](https://books.google.com/books?id=gwBrMAEACAAJ). McGraw-Hill. p. 203. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-07-124489-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-07-124489-3).
19. ^    Brenan, K. E.; Campbell, S. L.; Petzold, L. R. (1995). *Numerical Solution of Initial-Value Problems in Differential-Algebraic Equations*. Society for Industrial and Applied Mathematics. pp. 4–5. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/1.9781611971224](https://doi.org/10.1137%2F1.9781611971224).
20. ^   Roy, Featherstone (2008). *Rigid Body Dynamics Algorithms*. Springer New York. pp. 42–45, 141–143. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-1-4899-7560-7](https://doi.org/10.1007%2F978-1-4899-7560-7).
21. Pourciau, Bruce H. (1980). ["Modern multiplier rules"](http://www.maa.org/programs/maa-awards/writing-awards/modern-multiplier-rules). *[American Mathematical Monthly](https://en.wikipedia.org/wiki/American_Mathematical_Monthly)*. **87** (6): 433–452. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2320250](https://doi.org/10.2307%2F2320250). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2320250](https://www.jstor.org/stable/2320250).
22. [Kamien, M. I.](https://en.wikipedia.org/wiki/Morton_Kamien); [Schwartz, N. L.](https://en.wikipedia.org/wiki/Nancy_Schwartz) (1991). [Dynamic Optimization: The Calculus of Variations and Optimal Control in Economics and Management](https://books.google.com/books?id=0IoGUn8wjDQC) (Second ed.). New York: Elsevier. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-444-01609-0](https://en.wikipedia.org/wiki/Special:BookSources/0-444-01609-0).
23. Glötzl, Erhard; Glötzl, Florentin; Richters, Oliver (2019). "From constrained optimization to constrained dynamics: extending analogies between economics and mechanics". *Journal of Economic Interaction and Coordination*. **14** (3): 623–642. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s11403-019-00252-7](https://doi.org/10.1007%2Fs11403-019-00252-7). [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[10419/171974](https://hdl.handle.net/10419%2F171974).
24. Baxley, John V.; Moorhouse, John C. (1984). "Lagrange Multiplier Problems in Economics". *The American Mathematical Monthly*. **91** (7): 404–412. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/00029890.1984.11971446](https://doi.org/10.1080%2F00029890.1984.11971446)..
25. Janová, Jitka (2011). "Applications of a constrained mechanics methodology in economics". *European Journal of Physics*. **32** (6): 1443–1463. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1106.3455](https://arxiv.org/abs/1106.3455). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2011EJPh...32.1443J](https://ui.adsabs.harvard.edu/abs/2011EJPh...32.1443J). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1088/0143-0807/32/6/001](https://doi.org/10.1088%2F0143-0807%2F32%2F6%2F001).
26. Gautam, Mukesh; Bhusal, Narayan; Benidris, Mohammed (2020). *A sensitivity-based approach to adaptive under-frequency load shedding*. 2020 IEEE Texas Power and Energy Conference (TPEC). [Institute of Electronic and Electrical Engineers](https://en.wikipedia.org/wiki/Institute_of_Electronic_and_Electrical_Engineers). pp. 1–5. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/TPEC48276.2020.9042569](https://doi.org/10.1109%2FTPEC48276.2020.9042569).
27. Altman, Eitan (2021). *Constrained Markov Decision Processes*. [Routledge](https://en.wikipedia.org/wiki/Routledge).
28. Ding, Dongsheng; Zhang, Kaiqing; Jovanovic, Mihailo; Basar, Tamer (2020). *Natural policy gradient primal-dual method for constrained Markov decision processes*. Advances in Neural Information Processing Systems.

## Further reading

- Beavis, Brian; Dobbs, Ian M. (1990). ["Static Optimization"](https://books.google.com/books?id=L7HMACFgnXMC&pg=PA32). *Optimization and Stability Theory for Economic Analysis*. New York, NY: Cambridge University Press. pp. 32–72. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-33605-8](https://en.wikipedia.org/wiki/Special:BookSources/0-521-33605-8).
- [Bertsekas, Dimitri P.](https://en.wikipedia.org/wiki/Dimitri_Bertsekas) (1982). *Constrained optimization and Lagrange multiplier methods*. New York, NY: Academic Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-12-093480-9](https://en.wikipedia.org/wiki/Special:BookSources/0-12-093480-9).
- Beveridge, Gordon S.G.; Schechter, Robert S. (1970). ["Lagrangian multipliers"](https://books.google.com/books?id=TfhVXlWtOPQC&pg=PA244). *Optimization: Theory and Practice*. New York, NY: McGraw-Hill. pp. 244–259. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-07-005128-3](https://en.wikipedia.org/wiki/Special:BookSources/0-07-005128-3).
- Binger, Brian R.; Hoffman, Elizabeth (1998). "Constrained optimization". *Microeconomics with Calculus* (2nd ed.). Reading: Addison-Wesley. pp. 56–91. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-321-01225-9](https://en.wikipedia.org/wiki/Special:BookSources/0-321-01225-9).
- Carter, Michael (2001). ["Equality constraints"](https://books.google.com/books?id=KysvrGGfzq0C&pg=PA516). *Foundations of Mathematical Economics*. Cambridge, MA: MIT Press. pp. 516–549. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-262-53192-5](https://en.wikipedia.org/wiki/Special:BookSources/0-262-53192-5).
- [Hestenes, Magnus R.](https://en.wikipedia.org/wiki/Magnus_Hestenes) (1966). "Minima of functions subject to equality constraints". *Calculus of Variations and Optimal Control Theory*. New York, NY: Wiley. pp. 29–34.
- Wylie, C. Ray; Barrett, Louis C. (1995). "The extrema of integrals under constraint". *Advanced Engineering Mathematics* (Sixth ed.). New York, NY: McGraw-Hill. pp. 1096–1103. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-07-072206-4](https://en.wikipedia.org/wiki/Special:BookSources/0-07-072206-4).

## External links

### Exposition

- Steuard. ["Conceptual introduction"](http://www.slimy.com/~steuard/teaching/tutorials/Lagrange.html). *slimy.com*. — plus a brief discussion of Lagrange multipliers in the [calculus of variations](https://en.wikipedia.org/wiki/Calculus_of_variations) as used in physics.
- Carpenter, Kenneth H. ["Lagrange multipliers for quadratic forms with linear constraints"](https://ece.k-state.edu/people/faculty/carpenter/documents/lagrange.pdf) (PDF). [Kansas State University](https://en.wikipedia.org/wiki/Kansas_State_University).

### Additional text and interactive applets

- Resnik. ["Simple explanation with an example of governments using taxes as Lagrange multipliers"](https://web.archive.org/web/20150904222638/http://www.umiacs.umd.edu/~resnik/ling848_fa2004/lagrange.html). *umiacs.umd.edu*. [University of Maryland](https://en.wikipedia.org/wiki/University_of_Maryland). Archived from [the original](http://www.umiacs.umd.edu/~resnik/ling848_fa2004/lagrange.html) on 4 September 2015. Retrieved 28 February 2007.
- Klein, Dan. ["Lagrange multipliers without permanent scarring] Explanation with focus on the intuition"](https://nlp.cs.berkeley.edu/tutorials/lagrange-multipliers.pdf) (PDF). *nlp.cs.berkeley.edu*. [University of California, Berkeley](https://en.wikipedia.org/wiki/University_of_California,_Berkeley).
- Sathyanarayana, Shashi. ["Geometric representation of method of Lagrange multipliers"](http://demonstrations.wolfram.com/GeometricRepresentationOfMethodOfLagrangeMultipliers). *wolfram.com* (*Mathematica* demonstration). [Wolfram Research](https://en.wikipedia.org/wiki/Wolfram_Research). “Needs Internet Explorer / Firefox / Safari.” — Provides compelling insight in 2 dimensions that at a minimizing point, the direction of steepest descent must be perpendicular to the tangent of the constraint curve at that point.
- ["Lagrange multipliers – two variables"](https://ocw.mit.edu/ans7870/18/18.02/f07/tools/LagrangeMultipliersTwoVariables.html). *MIT Open Courseware (ocw.mit.edu)* (Applet). [Massachusetts Institute of Technology](https://en.wikipedia.org/wiki/Massachusetts_Institute_of_Technology).
- ["Lagrange multipliers"](https://ocw.mit.edu/courses/mathematics/18-02-multivariable-calculus-fall-2007/video-lectures/lecture-13-lagrange-multipliers/). *MIT Open Courseware (ocw.mit.edu)* (video lecture). Mathematics 18-02: Multivariable calculus. [Massachusetts Institute of Technology](https://en.wikipedia.org/wiki/Massachusetts_Institute_of_Technology). Fall 2007.
- Bertsekas. ["Details on Lagrange multipliers"](http://www.athenasc.com/NLP_Slides.pdf) (PDF). *athenasc.com* (slides / course lecture). Non-Linear Programming. — Course slides accompanying text on nonlinear optimization
- Wyatt, John (7 April 2004) \[19 November 2002\]. ["Legrange multipliers, constrained optimization, and the maximum entropy principle"](https://www-mtl.mit.edu/Courses/6.050/2004/unit9/wyatt.apr.7.pdf) (PDF). *www-mtl.mit.edu*. Elec E & C S / Mech E 6.050 – Information, entropy, and computation. — Geometric idea behind Lagrange multipliers
- ["Using Lagrange multipliers in optimization"](https://matlab.cheme.cmu.edu/2011/12/24/using-lagrange-multipliers-in-optimization/). *matlab.cheme.cmu.edu* (MATLAB example). Pittsburgh, PA: Carnegie Mellon University. 24 December 2011.
