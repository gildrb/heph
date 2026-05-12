[[calculus-analysis.base]]

> Source: [Change of variables](https://en.wikipedia.org/wiki/Change_of_variables)
> License: Wikipedia content is available under CC BY-SA 4.0.

In [mathematics](https://en.wikipedia.org/wiki/Mathematics), a **change of variables** is a basic technique used to simplify problems in which the original [variables](https://en.wikipedia.org/wiki/Variable_(mathematics) "Variable (mathematics)") are replaced with [functions](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)") of other variables. The intent is that when expressed in new variables, the problem may become simpler, or equivalent to a better understood problem.

Change of variables is an operation that is related to [substitution](https://en.wikipedia.org/wiki/Substitution_(algebra)). However these are different operations, as can be seen when considering [differentiation](https://en.wikipedia.org/wiki/Derivative) ([[Chain Rule]]) or [integration](https://en.wikipedia.org/wiki/Integral) ([integration by substitution](https://en.wikipedia.org/wiki/Integration_by_substitution)).

A very simple example of a useful variable change can be seen in the problem of finding the roots of the sixth-degree polynomial:

$x^{6}-9x^{3}+8=0.$

Sixth-degree polynomial equations are generally impossible to solve in terms of radicals (see [Abel–Ruffini theorem](https://en.wikipedia.org/wiki/Abel%E2%80%93Ruffini_theorem)). This particular equation, however, may be written

$(x^{3})^{2}-9(x^{3})+8=0$

(this is a simple case of a [polynomial decomposition](https://en.wikipedia.org/wiki/Polynomial_decomposition)). Thus the equation may be simplified by defining a new variable $u=x^{3}$. Substituting *x* by ${\sqrt[{3}]{u}}$ into the polynomial gives

$u^{2}-9u+8=0,$

which is just a [quadratic equation](https://en.wikipedia.org/wiki/Quadratic_equation) with the two solutions:

$u=1\quad {\text{and}}\quad u=8.$

The solutions in terms of the original variable are obtained by substituting *x*<sup>3</sup> back in for *u*, which gives

$x^{3}=1\quad {\text{and}}\quad x^{3}=8.$

Then, assuming that one is interested only in [real](https://en.wikipedia.org/wiki/Real_number) solutions, the solutions of the original equation are

$x=(1)^{1/3}=1\quad {\text{and}}\quad x=(8)^{1/3}=2.$

## Simple example

Consider the system of equations

$xy+x+y=71$

$x^{2}y+xy^{2}=880$

where $x$ and $y$ are positive integers with $x>y$. (Source: 1991 [AIME](https://en.wikipedia.org/wiki/American_Invitational_Mathematics_Examination))

Solving this normally is not very difficult, but it may get a little tedious. However, we can rewrite the second equation as $xy(x+y)=880$. Making the substitutions $s=x+y$ and $t=xy$ reduces the system to $s+t=71,st=880$. Solving this gives $(s,t)=(16,55)$ and $(s,t)=(55,16)$. Back-substituting the first ordered pair gives us $x+y=16,xy=55,x>y$, which gives the solution $(x,y)=(11,5).$ Back-substituting the second ordered pair gives us $x+y=55,xy=16,x>y$, which gives no solutions. Hence the solution that solves the system is $(x,y)=(11,5)$.

## Formal introduction

Let $A$, $B$ be [smooth manifolds](https://en.wikipedia.org/wiki/Smooth_manifold) and let $\Phi :A\rightarrow B$ be a $C^{r}$-[diffeomorphism](https://en.wikipedia.org/wiki/Diffeomorphism) between them, that is: $\Phi$ is a $r$ times continuously differentiable, [bijective](https://en.wikipedia.org/wiki/Bijective) map from $A$ to $B$ with $r$ times continuously differentiable inverse from $B$ to $A$. Here $r$ may be any natural number (or zero), $\infty$ ([smooth](https://en.wikipedia.org/wiki/Smooth_function)) or $\omega$ ([analytic](https://en.wikipedia.org/wiki/Analytic_function)).

The map $\Phi$ is called a *regular coordinate transformation* or *regular variable substitution*, where *regular* refers to the $C^{r}$-ness of $\Phi$. Usually one will write $x=\Phi (y)$ to indicate the replacement of the variable $x$ by the variable $y$ by substituting the value of $\Phi$ in $y$ for every occurrence of $x$.

## Other examples

### Coordinate transformation

Some systems can be more easily solved when switching to [polar coordinates](https://en.wikipedia.org/wiki/Polar_coordinates). Consider for example the equation

$U(x,y):=(x^{2}+y^{2}){\sqrt {1-{\frac {x^{2}}{x^{2}+y^{2}}}}}=0.$

This may be a potential energy function for some physical problem. If one does not immediately see a solution, one might try the substitution

$\displaystyle (x,y)=\Phi (r,\theta )$ given by $\displaystyle \Phi (r,\theta )=(r\cos(\theta ),r\sin(\theta )).$

Note that if $\theta$ runs outside a $2\pi$-length interval, for example, $[0,2\pi ]$, the map $\Phi$ is no longer bijective. Therefore, $\Phi$ should be limited to, for example $(0,\infty ]\times [0,2\pi )$. Notice how $r=0$ is excluded, for $\Phi$ is not bijective in the origin ($\theta$ can take any value, the point will be mapped to (0, 0)). Then, replacing all occurrences of the original variables by the new [expressions](https://en.wikipedia.org/wiki/Expression_(mathematics) "Expression (mathematics)") prescribed by $\Phi$ and using the identity $\sin ^{2}x+\cos ^{2}x=1$, we get

$V(r,\theta )=r^{2}{\sqrt {1-{\frac {r^{2}\cos ^{2}\theta }{r^{2}}}}}=r^{2}{\sqrt {1-\cos ^{2}\theta }}=r^{2}\left|\sin \theta \right|.$

Now the solutions can be readily found: $\sin(\theta )=0$, so $\theta =0$ or $\theta =\pi$. Applying the inverse of $\Phi$ shows that this is equivalent to $y=0$ while $x\not =0$. Indeed, we see that for $y=0$ the function vanishes, except for the origin.

Note that, had we allowed $r=0$, the origin would also have been a solution, though it is not a solution to the original problem. Here the bijectivity of $\Phi$ is crucial. The function is always positive (for $x,y\in \mathbb {R}$), hence the absolute values.

### Differentiation

The [[Chain Rule]] is used to simplify complicated differentiation. For example, consider the problem of calculating the derivative

${\frac {d}{dx}}\sin(x^{2}).$

Let $y=\sin u$ with $u=x^{2}.$ Then:

${\begin{aligned}{\frac {d}{dx}}\sin(x^{2})&={\frac {dy}{dx}}\\[6pt]&={\frac {dy}{du}}{\frac {du}{dx}}&&{\text{This part is the chain rule.}}\\[6pt]&=\left({\frac {d}{du}}\sin u\right)\left({\frac {d}{dx}}x^{2}\right)\\[6pt]&=(\cos u)(2x)\\&=\left(\cos(x^{2})\right)(2x)\\&=2x\cos(x^{2})\end{aligned}}$

### Integration

Difficult integrals may often be evaluated by changing variables; this is enabled by the [substitution rule](https://en.wikipedia.org/wiki/Substitution_rule) and is analogous to the use of the chain rule above. Difficult integrals may also be solved by simplifying the integral using a change of variables given by the corresponding [Jacobian matrix and determinant](https://en.wikipedia.org/wiki/Jacobian_matrix_and_determinant). Using the Jacobian determinant and the corresponding change of variable that it gives is the basis of coordinate systems such as polar, cylindrical, and spherical coordinate systems.

#### Change of variables formula in terms of Lebesgue measure

The following theorem allows us to relate integrals with respect to Lebesgue measure to an equivalent integral with respect to the pullback measure under a parameterization G. The proof is due to approximations of the Jordan content.

> Suppose that $\Omega$ is an open subset of $\mathbb {R} ^{n}$ and $G:\Omega \to \mathbb {R} ^{n}$ is a $C^{1}$ diffeomorphism.
>
> - If $f$ is a Lebesgue measurable function on $G(\Omega )$, then $f\circ G$ is Lebesgue measurable on $\Omega$. If $f\geq 0$ or $f\in L^{1}(G(\Omega ),m),$ then $\int _{G(\Omega )}f(x)dx=\int _{\Omega }f\circ G(x)|{\text{det}}D_{x}G|dx$.
> - If $E\subset \Omega$ and $E$ is Lebesgue measurable, then $G(E)$ is Lebesgue measurable, then $m(G(E))=\int _{E}|{\text{det}}D_{x}G|dx$.

As a corollary of this theorem, we may compute the Radon–Nikodym derivatives of both the pullback and pushforward measures of $m$ under $T$.

##### Pullback measure and transformation formula

The pullback measure in terms of a transformation $T$ is defined as $T^{*}\mu :=\mu (T(A))$. The change of variables formula for pullback measures is

$\int _{T(\Omega )}gd\mu =\int _{\Omega }g\circ TdT^{*}\mu$.

**Pushforward measure and transformation formula**

The pushforward measure in terms of a transformation $T$, is defined as $T_{*}\mu :=\mu (T^{-1}(A))$. The change of variables formula for pushforward measures is

$\int _{\Omega }g\circ Td\mu =\int _{T(\Omega )}gdT_{*}\mu$.

As a corollary of the change of variables formula for Lebesgue measure, we have that

- Radon-Nikodym derivative of the pullback with respect to Lebesgue measure: ${\frac {dT^{*}m}{dm}}(x)=|{\text{det}}D_{x}T|$
- Radon-Nikodym derivative of the pushforward with respect to Lebesgue measure: ${\frac {dT_{*}m}{dm}}(x)=|{\text{det}}D_{x}T^{-1}|$

From which we may obtain

- The change of variables formula for pullback measure: $\int _{T(\Omega )}gdm=\int _{\Omega }g\circ TdT^{*}m=\int _{\Omega }g\circ T|{\text{det}}D_{x}T|dm(x)$
- The change of variables formula for pushforward measure:$\int _{\Omega }gdm=\int _{T(\Omega )}g\circ T^{-1}dT_{*}m=\int _{T(\Omega )}g\circ T^{-1}|{\text{det}}D_{x}T^{-1}|dm(x)$

### Differential equations

Variable changes for differentiation and integration are taught in elementary [calculus](https://en.wikipedia.org/wiki/Calculus) and the steps are rarely carried out in full.

The very broad use of variable changes is apparent when considering differential equations, where the independent variables may be changed using the [[Chain Rule]] or the dependent variables are changed resulting in some differentiation to be carried out. Exotic changes, such as the mingling of dependent and independent variables in [point](https://en.wikipedia.org/wiki/Point_transformation) and [contact transformations](https://en.wikipedia.org/wiki/Contact_transformation), can be very complicated but allow much freedom.

Very often, a general form for a change is substituted into a problem and parameters picked along the way to best simplify the problem.

### Scaling and shifting

Probably the simplest change is the scaling and shifting of variables, that is replacing them with new variables that are "stretched" and "moved" by constant amounts. This is very common in practical applications to get physical parameters out of problems. For an *n*<sup>th</sup> order derivative, the change simply results in

${\frac {d^{n}y}{dx^{n}}}={\frac {y_{\text{scale}}}{x_{\text{scale}}^{n}}}{\frac {d^{n}{\hat {y}}}{d{\hat {x}}^{n}}}$

where

$x={\hat {x}}x_{\text{scale}}+x_{\text{shift}}$

$y={\hat {y}}y_{\text{scale}}+y_{\text{shift}}.$

This may be shown readily through the [[Chain Rule]] and linearity of differentiation. This change is very common in practical applications to get physical parameters out of problems, for example, the [boundary value problem](https://en.wikipedia.org/wiki/Boundary_value_problem)

$\mu {\frac {d^{2}u}{dy^{2}}}={\frac {dp}{dx}}\quad ;\quad u(0)=u(L)=0$

describes parallel fluid flow between flat solid walls separated by a distance δ; μ is the [viscosity](https://en.wikipedia.org/wiki/Viscosity) and $dp/dx$ the [pressure gradient](https://en.wikipedia.org/wiki/Pressure_gradient), both constants. By scaling the variables the problem becomes

${\frac {d^{2}{\hat {u}}}{d{\hat {y}}^{2}}}=1\quad ;\quad {\hat {u}}(0)={\hat {u}}(1)=0$

where

$y={\hat {y}}L\qquad {\text{and}}\qquad u={\hat {u}}{\frac {L^{2}}{\mu }}{\frac {dp}{dx}}.$

Scaling is useful for many reasons. It simplifies analysis both by reducing the number of parameters and by simply making the problem neater. Proper scaling may *normalize* variables, that is make them have a sensible unitless range such as 0 to 1. Finally, if a problem mandates numeric solution, the fewer the parameters the smaller the number of computations.

### Momentum vs. velocity

Consider a system of equations

${\begin{aligned}m{\dot {v}}&=-{\frac {\partial H}{\partial x}}\\[5pt]m{\dot {x}}&={\frac {\partial H}{\partial v}}\end{aligned}}$

for a given function $H(x,v)$. The mass can be eliminated by the (trivial) substitution $\Phi (p)=1/m\cdot p$. Clearly this is a bijective map from $\mathbb {R}$ to $\mathbb {R}$. Under the substitution $v=\Phi (p)$ the system becomes

${\begin{aligned}{\dot {p}}&=-{\frac {\partial H}{\partial x}}\\[5pt]{\dot {x}}&={\frac {\partial H}{\partial p}}\end{aligned}}$

### Lagrangian mechanics

Given a force field $\varphi (t,x,v)$, [Newton](https://en.wikipedia.org/wiki/Isaac_Newton)'s [equations of motion](https://en.wikipedia.org/wiki/Equations_of_motion) are

$m{\ddot {x}}=\varphi (t,x,v).$

Lagrange examined how these equations of motion change under an arbitrary substitution of variables $x=\Psi (t,y)$, $v={\frac {\partial \Psi (t,y)}{\partial t}}+{\frac {\partial \Psi (t,y)}{\partial y}}\cdot w.$

He found that the equations

${\frac {\partial {L}}{\partial y}}={\frac {\mathrm {d} }{\mathrm {d} t}}{\frac {\partial {L}}{\partial {w}}}$

are equivalent to Newton's equations for the function $L=T-V$, where *T* is the kinetic, and *V* the potential energy.

In fact, when the substitution is chosen well (exploiting for example symmetries and constraints of the system) these equations are much easier to solve than Newton's equations in Cartesian coordinates.

## See also

- [Change of variables (PDE)](https://en.wikipedia.org/wiki/Change_of_variables_(PDE) "Change of variables (PDE)")
- [[Probability Density Function|Change of variables for probability densities]]
- [Substitution property of equality](https://en.wikipedia.org/wiki/Substitution_property_of_equality)
- [Universal instantiation](https://en.wikipedia.org/wiki/Universal_instantiation)

## References

1.  [Kaplan, Wilfred](https://en.wikipedia.org/wiki/Wilfred_Kaplan) (1973). "Change of Variables in Integrals". *Advanced Calculus* (Second ed.). Reading: Addison-Wesley. pp. 269–275.
2.  Folland, G. B. (1999). *Real analysis : modern techniques and their applications* (2nd ed.). New York: Wiley. pp. 74–75. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-31716-0](https://en.wikipedia.org/wiki/Special:BookSources/0-471-31716-0). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [39849337](https://search.worldcat.org/oclc/39849337).
