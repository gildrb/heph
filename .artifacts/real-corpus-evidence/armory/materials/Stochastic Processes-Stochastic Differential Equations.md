[[stochastic-processes.base]]

> Source: [Stochastic differential equation](https://en.wikipedia.org/wiki/Stochastic_differential_equation)
> License: Wikipedia content is available under CC BY-SA 4.0.

SDEs have a random differential that is in the most basic case random [white noise](https://en.wikipedia.org/wiki/White_noise) calculated as the distributional derivative of a [[Brownian Motion]] or more generally a [semimartingale](https://en.wikipedia.org/wiki/Semimartingale). However, other types of random behaviour are possible, such as [jump processes](https://en.wikipedia.org/wiki/Jump_process) like [Lévy processes](https://en.wikipedia.org/wiki/L%C3%A9vy_process) or semimartingales with jumps.

## Background

Stochastic differential equations originated in the theory of [[Brownian Motion]], in the work of [Albert Einstein](https://en.wikipedia.org/wiki/Annus_Mirabilis_Papers#Brownian_motion) and [Marian Smoluchowski](https://en.wikipedia.org/wiki/Marian_Smoluchowski#Work) in 1905, although [Louis Bachelier](https://en.wikipedia.org/wiki/Louis_Bachelier) was the first person credited with modeling Brownian motion in 1900, giving a very early example of a stochastic differential equation now known as [Bachelier model](https://en.wikipedia.org/wiki/Bachelier_model). Some of these early examples were linear stochastic differential equations, also called [Langevin equations](https://en.wikipedia.org/wiki/Langevin_equation) after French physicist [Langevin](https://en.wikipedia.org/wiki/Paul_Langevin), describing the motion of a harmonic oscillator subject to a random force. The mathematical theory of stochastic differential equations was developed in the 1940s through the groundbreaking work of Japanese mathematician [Kiyosi Itô](https://en.wikipedia.org/wiki/Kiyosi_It%C3%B4), who introduced the concept of [stochastic integral](https://en.wikipedia.org/wiki/Stochastic_integral) and initiated the study of nonlinear stochastic differential equations. Another approach was later proposed by Russian physicist [Stratonovich](https://en.wikipedia.org/wiki/Ruslan_L._Stratonovich), leading to a calculus similar to ordinary calculus.

### Terminology

The most common form of SDEs in the literature is an [ordinary differential equation](https://en.wikipedia.org/wiki/Ordinary_differential_equation) with the right hand side perturbed by a term dependent on a [white noise](https://en.wikipedia.org/wiki/White_noise) variable. In most cases, SDEs are understood as continuous time limit of the corresponding [stochastic difference equations](https://en.wikipedia.org/wiki/Stochastic_difference_equation). This understanding of SDEs is ambiguous and must be complemented by a proper mathematical definition of the corresponding integral. Such a mathematical definition was first proposed by [Kiyosi Itô](https://en.wikipedia.org/wiki/Kiyosi_It%C3%B4) in the 1940s, leading to what is known today as the [Itô calculus](https://en.wikipedia.org/wiki/It%C3%B4_calculus). Another construction was later proposed by Russian physicist [Stratonovich](https://en.wikipedia.org/wiki/Ruslan_L._Stratonovich), leading to what is known as the [Stratonovich integral](https://en.wikipedia.org/wiki/Stratonovich_integral). The [Itô integral](https://en.wikipedia.org/wiki/It%C3%B4_integral) and [Stratonovich integral](https://en.wikipedia.org/wiki/Stratonovich_integral) are related, but different, objects and the choice between them depends on the application considered. The [Itô calculus](https://en.wikipedia.org/wiki/It%C3%B4_calculus) is based on the concept of non-anticipativeness or causality, which is natural in applications where the variable is time. The Stratonovich calculus, on the other hand, has rules which resemble ordinary calculus and has intrinsic geometric properties which render it more natural when dealing with geometric problems such as random motion on [manifolds](https://en.wikipedia.org/wiki/Manifolds), although it is possible and in some cases preferable to model random motion on manifolds through Itô SDEs, for example when trying to optimally approximate SDEs on submanifolds.

An alternative view on SDEs is the stochastic flow of diffeomorphisms. This understanding is unambiguous and corresponds to the Stratonovich version of the continuous time limit of stochastic difference equations. Associated with SDEs is the [Smoluchowski equation](https://en.wikipedia.org/wiki/Smoluchowski_equation) or the [Fokker–Planck equation](https://en.wikipedia.org/wiki/Fokker%E2%80%93Planck_equation), an equation describing the time evolution of [[Probability Density Function|probability distribution functions]]. The generalization of the Fokker–Planck evolution to temporal evolution of differential forms is provided by the concept of [stochastic evolution operator](https://en.wikipedia.org/wiki/Supersymmetric_theory_of_stochastic_dynamics#Stochastic_evolution_operator).

In physical science, there is an ambiguity in the usage of the term ["Langevin SDEs"](https://en.wikipedia.org/wiki/Langevin_equation). While Langevin SDEs can be of a [more general form](https://en.wikipedia.org/wiki/Langevin_equation#Generic_Langevin_equation), this term typically refers to a narrow class of SDEs with gradient flow vector fields. This class of SDEs is particularly popular because it is a starting point of the Parisi–Sourlas stochastic quantization procedure, leading to a N=2 supersymmetric model closely related to [supersymmetric quantum mechanics](https://en.wikipedia.org/wiki/Supersymmetric_quantum_mechanics). From the physical point of view, however, this class of SDEs is not very interesting because it never exhibits spontaneous breakdown of topological supersymmetry, i.e., [(overdamped) Langevin SDEs are never chaotic](https://en.wikipedia.org/wiki/Supersymmetric_theory_of_stochastic_dynamics#Spontaneous_supersymmetry_breaking_and_chaos).

### Stochastic calculus

[[Brownian Motion]] or the [Wiener process](https://en.wikipedia.org/wiki/Wiener_process) was discovered to be exceptionally complex mathematically. The [Wiener process](https://en.wikipedia.org/wiki/Wiener_process) is almost surely nowhere differentiable; thus, it requires its own rules of calculus. There are two dominating versions of stochastic calculus, the [Itô stochastic calculus](https://en.wikipedia.org/wiki/It%C3%B4_calculus) and the [Stratonovich stochastic calculus](https://en.wikipedia.org/wiki/Stratonovich_stochastic_calculus). Each of the two has advantages and disadvantages, and newcomers are often confused whether the one is more appropriate than the other in a given situation. Guidelines exist (e.g. Øksendal, 2003) and conveniently, one can readily convert an Itô SDE to an equivalent Stratonovich SDE and back again. Still, one must be careful which calculus to use when the SDE is initially written down.

### Numerical solutions

Numerical methods for solving stochastic differential equations include the [Euler–Maruyama method](https://en.wikipedia.org/wiki/Euler%E2%80%93Maruyama_method), [Milstein method](https://en.wikipedia.org/wiki/Milstein_method), [Runge–Kutta method (SDE)](https://en.wikipedia.org/wiki/Runge%E2%80%93Kutta_method_(SDE) "Runge–Kutta method (SDE)"), Rosenbrock method, and methods based on different representations of iterated stochastic integrals.

## Use in physics

In physics, SDEs have wide applicability ranging from molecular dynamics to neurodynamics and to the dynamics of astrophysical objects. More specifically, SDEs describe all dynamical systems, in which quantum effects are either unimportant or can be taken into account as perturbations. SDEs can be viewed as a generalization of the [dynamical systems theory](https://en.wikipedia.org/wiki/Dynamical_systems_theory) to models with noise. This is an important generalization because real systems cannot be completely isolated from their environments and for this reason always experience external stochastic influence.

There are standard techniques for transforming higher-order equations into several coupled first-order equations by introducing new unknowns. Therefore, the following is the most general class of SDEs:

${\frac {\mathrm {d} x(t)}{\mathrm {d} t}}=F(x(t))+\sum _{\alpha =1}^{n}g_{\alpha }(x(t))\xi ^{\alpha }(t),\,$

where $x\in X$ is the position in the system in its [phase (or state) space](https://en.wikipedia.org/wiki/Phase_space), $X$, assumed to be a differentiable manifold, the $F\in TX$ is a flow vector field representing deterministic law of evolution, and $g_{\alpha }\in TX$ is a set of vector fields that define the coupling of the system to Gaussian white noise, $\xi ^{\alpha }$. If $X$ is a linear space and $g$ are constants, the system is said to be subject to additive noise, otherwise it is said to be subject to multiplicative noise. For additive noise, the Itô and Stratonovich forms of the SDE generate the same solution, and it is not important which definition is used to solve the SDE. For multiplicative noise SDEs the Itô and Stratonovich forms of the SDE are different, and care should be used in mapping between them.

For a fixed configuration of noise, SDE has a unique solution differentiable with respect to the initial condition. Nontriviality of stochastic case shows up when one tries to average various objects of interest over noise configurations. In this sense, an SDE is not a uniquely defined entity when noise is multiplicative and when the SDE is understood as a continuous time limit of a [stochastic difference equation](https://en.wikipedia.org/wiki/Stochastic_difference_equation). In this case, SDE must be complemented by what is known as "interpretations of SDE" such as Itô or a Stratonovich interpretations of SDEs. Nevertheless, when SDE is viewed as a continuous-time stochastic flow of diffeomorphisms, it is a [uniquely defined mathematical object](https://en.wikipedia.org/wiki/Supersymmetric_theory_of_stochastic_dynamics#Resolution_of_Ito–Stratonovich_dilemma_and_operator_ordering_conventions) that corresponds to Stratonovich approach to a continuous time limit of a stochastic difference equation.

In physics, the main method of solution is to find the [probability distribution](https://en.wikipedia.org/wiki/Probability_distribution) function as a function of time using the equivalent [Fokker–Planck equation](https://en.wikipedia.org/wiki/Fokker%E2%80%93Planck_equation) (FPE). The Fokker–Planck equation is a deterministic [partial differential equation](https://en.wikipedia.org/wiki/Partial_differential_equation). It tells how the probability distribution function evolves in time similarly to how the [Schrödinger equation](https://en.wikipedia.org/wiki/Schr%C3%B6dinger_equation) gives the time evolution of the quantum wave function or the [diffusion equation](https://en.wikipedia.org/wiki/Diffusion_equation) gives the time evolution of chemical concentration. Alternatively, numerical solutions can be obtained by [[Monte Carlo Method|Monte Carlo]] simulation. Other techniques include the [path integration](https://en.wikipedia.org/wiki/Path_integral_formulation) that draws on the analogy between statistical physics and [quantum mechanics](https://en.wikipedia.org/wiki/Quantum_mechanics) (for example, the Fokker-Planck equation can be transformed into the [Schrödinger equation](https://en.wikipedia.org/wiki/Schr%C3%B6dinger_equation) by rescaling a few variables) or by writing down [ordinary differential equations](https://en.wikipedia.org/wiki/Ordinary_differential_equations) for the statistical [moments](https://en.wikipedia.org/wiki/Moment_(mathematics) "Moment (mathematics)") of the probability distribution function. <sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

## Use in probability and mathematical finance

The notation used in [probability theory](https://en.wikipedia.org/wiki/Probability_theory) (and in many applications of probability theory, for instance in signal processing with the [filtering problem](https://en.wikipedia.org/wiki/Filtering_problem_(stochastic_processes) "Filtering problem (stochastic processes)") and in [mathematical finance](https://en.wikipedia.org/wiki/Mathematical_finance)) is slightly different. It is also the notation used in publications on [numerical methods](https://en.wikipedia.org/wiki/Numerical_methods) for solving stochastic differential equations. This notation makes the exotic nature of the random function of time $\xi ^{\alpha }$ in the physics formulation more explicit. In strict mathematical terms, $\xi ^{\alpha }$ cannot be chosen as an ordinary function, but only as a [generalized function](https://en.wikipedia.org/wiki/Generalized_function). The mathematical formulation treats this complication with less ambiguity than the physics formulation.

A typical equation is of the form

$\mathrm {d} X_{t}=\mu (X_{t},t)\,\mathrm {d} t+\sigma (X_{t},t)\,\mathrm {d} B_{t},$

where $B$ denotes a [Wiener process](https://en.wikipedia.org/wiki/Wiener_process) (standard Brownian motion). This equation should be interpreted as an informal way of expressing the corresponding [integral equation](https://en.wikipedia.org/wiki/Integral_equation)

$X_{t+s}-X_{t}=\int _{t}^{t+s}\mu (X_{u},u)\mathrm {d} u+\int _{t}^{t+s}\sigma (X_{u},u)\,\mathrm {d} B_{u}.$

The equation above characterizes the behavior of the [continuous time](https://en.wikipedia.org/wiki/Continuous_time) [stochastic process](https://en.wikipedia.org/wiki/Stochastic_process) *X*<sub>*t*</sub> as the sum of an ordinary [Lebesgue integral](https://en.wikipedia.org/wiki/Lebesgue_integral) and an [Itô integral](https://en.wikipedia.org/wiki/It%C3%B4_calculus). A [heuristic](https://en.wikipedia.org/wiki/Heuristic) (but very helpful) interpretation of the stochastic differential equation is that in a small time interval of length *δ* the stochastic process *X*<sub>*t*</sub> changes its value by an amount that is [normally distributed](https://en.wikipedia.org/wiki/Normal_distribution) with [expectation](https://en.wikipedia.org/wiki/Expected_value) *μ*(*X*<sub>*t*</sub>, *t*) *δ* and [variance](https://en.wikipedia.org/wiki/Variance) *σ*(*X*<sub>*t*</sub>, *t*)<sup>2</sup> *δ* and is independent of the past behavior of the process. This is so because the increments of a Wiener process are independent and normally distributed. The function *μ* is referred to as the drift coefficient, while *σ* is called the diffusion coefficient. The stochastic process *X*<sub>*t*</sub> is called a [diffusion process](https://en.wikipedia.org/wiki/Diffusion_process), and satisfies the [Markov property](https://en.wikipedia.org/wiki/Markov_property).

The formal interpretation of an SDE is given in terms of what constitutes a solution to the SDE. There are two main definitions of a solution to an SDE, a strong solution and a weak solution Both require the existence of a process *X*<sub>*t*</sub> that solves the integral equation version of the SDE. The difference between the two lies in the underlying [probability space](https://en.wikipedia.org/wiki/Probability_space) ($\Omega ,\,{\mathcal {F}},\,P$). A weak solution consists of a probability space and a process that satisfies the integral equation, while a strong solution is a process that satisfies the equation and is defined on a given probability space. The [Yamada–Watanabe theorem](https://en.wikipedia.org/wiki/Yamada%E2%80%93Watanabe_theorem) makes a connection between the two.

An important example is the equation for [geometric Brownian motion](https://en.wikipedia.org/wiki/Geometric_Brownian_motion)

$\mathrm {d} X_{t}=\mu X_{t}\,\mathrm {d} t+\sigma X_{t}\,\mathrm {d} B_{t}.$

which is the equation for the dynamics of the price of a [stock](https://en.wikipedia.org/wiki/Stock) in the [Black–Scholes](https://en.wikipedia.org/wiki/Black%E2%80%93Scholes_model) options pricing model of financial mathematics.

Generalizing the geometric Brownian motion, it is also possible to define SDEs admitting strong solutions and whose distribution is a convex combination of densities coming from different geometric Brownian motions or Black Scholes models, obtaining a single SDE whose solutions is distributed as a mixture dynamics of lognormal distributions of different Black Scholes models. This leads to models that can deal with the [volatility smile](https://en.wikipedia.org/wiki/Volatility_smile) in financial mathematics.

The simpler SDE called [arithmetic Brownian motion](https://en.wikipedia.org/wiki/Geometric_Brownian_motion#Arithmetic_Brownian_Motion)

$\mathrm {d} X_{t}=\mu \,\mathrm {d} t+\sigma \,\mathrm {d} B_{t}$

was used by Louis Bachelier as the first model for stock prices in 1900, known today as [Bachelier model](https://en.wikipedia.org/wiki/Bachelier_model).

There are also more general stochastic differential equations where the coefficients *μ* and *σ* depend not only on the present value of the process *X*<sub>*t*</sub>, but also on previous values of the process and possibly on present or previous values of other processes too. In that case the solution process, *X*, is not a Markov process, and it is called an Itô process and not a diffusion process. When the coefficients depends only on present and past values of *X*, the defining equation is called a stochastic delay differential equation.

A generalization of stochastic differential equations with the Fisk-Stratonovich integral to semimartingales with jumps are the SDEs of *Marcus type*. The Marcus integral is an extension of McShane's stochastic calculus.

An application in [stochastic finance](https://en.wikipedia.org/wiki/Stochastic_finance) derives from the usage of the equation for [Ornstein–Uhlenbeck process](https://en.wikipedia.org/wiki/Ornstein%E2%80%93Uhlenbeck_process)

$\mathrm {d} R_{t}=\mu R_{t}\,\mathrm {d} t+\sigma _{t}\,\mathrm {d} B_{t}.$

which is the equation for the dynamics of the return of the price of a [stock](https://en.wikipedia.org/wiki/Stock) under the hypothesis that returns display a [Log-normal distribution](https://en.wikipedia.org/wiki/Log-normal_distribution). Under this hypothesis, the methodologies developed by Marcello Minenna determines prediction interval able to identify abnormal return that could hide [market abuse](https://en.wikipedia.org/wiki/Market_abuse) phenomena.

### SDEs on manifolds

More generally one can extend the theory of stochastic calculus onto [differential manifolds](https://en.wikipedia.org/wiki/Differential_manifold) and for this purpose one uses the Fisk-Stratonovich integral. Consider a manifold $M$, some finite-dimensional vector space $E$, a filtered probability space $(\Omega ,{\mathcal {F}},({\mathcal {F}}_{t})_{t\in \mathbb {R} _{+}},P)$ with $({\mathcal {F}}_{t})_{t\in \mathbb {R} _{+}}$ satisfying the [usual conditions](https://en.wikipedia.org/wiki/Usual_conditions) and let ${\widehat {M}}=M\cup \{\infty \}$ be the [one-point compactification](https://en.wikipedia.org/wiki/One-point_compactification) and $x_{0}$ be ${\mathcal {F}}_{0}$-measurable. A *stochastic differential equation on $M$* written

$\mathrm {d} X=A(X)\circ dZ$

is a pair $(A,Z)$, such that

- $Z$ is a continuous $E$-valued semimartingale,
- $A:M\times E\to TM,(x,e)\mapsto A(x)e$ is a homomorphism of [vector bundles](https://en.wikipedia.org/wiki/Vector_bundle) over $M$.

For each $x\in M$ the map $A(x):E\to T_{x}M$ is linear and $A(\cdot )e\in \Gamma (TM)$ for each $e\in E$.

A solution to the SDE on $M$ with initial condition $X_{0}=x_{0}$ is a continuous $\{{\mathcal {F}}_{t}\}$-adapted $M$-valued process $(X_{t})_{t<\zeta }$ up to life time $\zeta$, s.t. for each test function $f\in C_{c}^{\infty }(M)$ the process $f(X)$ is a real-valued semimartingale and for each stopping time $\tau$ with $0\leq \tau <\zeta$ the equation

$f(X_{\tau })=f(x_{0})+\int _{0}^{\tau }(\mathrm {d} f)_{X}A(X)\circ \mathrm {d} Z$

holds $P$-almost surely, where $(df)_{X}:T_{x}M\to T_{f(x)}M$ is the [differential](https://en.wikipedia.org/wiki/Differential_form) at $X$. It is a *maximal solution* if the life time is maximal, i.e.,

$\{\zeta <\infty \}\subset \left\{\lim \limits _{t\nearrow \zeta }X_{t}=\infty {\text{ in }}{\widehat {M}}\right\}$

$P$-almost surely. It follows from the fact that $f(X)$ for each test function $f\in C_{c}^{\infty }(M)$ is a semimartingale, that $X$ is a *semimartingale on $M$*. Given a maximal solution we can extend the time of $X$ onto full $\mathbb {R} _{+}$ and after a continuation of $f$ on ${\widehat {M}}$ we get

$f(X_{t})=f(X_{0})+\int _{0}^{t}(\mathrm {d} f)_{X}A(X)\circ \mathrm {d} Z,\quad t\geq 0$

up to indistinguishable processes. Although Stratonovich SDEs are the natural choice for SDEs on manifolds, given that they satisfy the chain rule and that their drift and diffusion coefficients behave as vector fields under changes of coordinates, there are cases where Ito calculus on manifolds is preferable. A theory of Ito calculus on manifolds was first developed by [Laurent Schwartz](https://en.wikipedia.org/wiki/Laurent_Schwartz) through the concept of Schwartz morphism, see also the related 2-jet interpretation of Ito SDEs on manifolds based on the jet-bundle. This interpretation is helpful when trying to optimally approximate the solution of an SDE given on a large space with the solutions of an SDE given on a submanifold of that space, in that a Stratonovich based projection does not result to be optimal. This has been applied to the [filtering problem](https://en.wikipedia.org/wiki/Filtering_problem), leading to optimal projection filters.

## As rough paths

Usually the solution of an SDE requires a probabilistic setting, as the integral implicit in the solution is a stochastic integral. If it were possible to deal with the differential equation path by path, one would not need to define a stochastic integral and one could develop a theory independently of probability theory. This points to considering the SDE

$\mathrm {d} X_{t}(\omega )=\mu (X_{t}(\omega ),t)\,\mathrm {d} t+\sigma (X_{t}(\omega ),t)\,\mathrm {d} B_{t}(\omega )$

as a single deterministic differential equation for every $\omega \in \Omega$, where $\Omega$ is the sample space in the given probability space ($\Omega ,\,{\mathcal {F}},\,P$). However, a direct path-wise interpretation of the SDE is not possible, as the Brownian motion paths have unbounded variation and are nowhere differentiable with probability one, so that there is no naive way to give meaning to terms like $\mathrm {d} B_{t}(\omega )$, precluding also a naive path-wise definition of the stochastic integral as an integral against every single $\mathrm {d} B_{t}(\omega )$. However, motivated by the Wong-Zakai result for limits of solutions of SDEs with regular noise and using [rough paths](https://en.wikipedia.org/wiki/Rough_paths) theory, while adding a chosen definition of iterated integrals of Brownian motion, it is possible to define a deterministic rough integral for every single $\omega \in \Omega$ that coincides for example with the Ito integral with probability one for a particular choice of the iterated Brownian integral. Other definitions of the iterated integral lead to deterministic pathwise equivalents of different stochastic integrals, like the Stratonovich integral. This has been used for example in financial mathematics to price options without probability.

## Existence and uniqueness of solutions

As with deterministic ordinary and partial differential equations, it is important to know whether a given SDE has a solution, and whether or not it is unique. The following is a typical existence and uniqueness theorem for Itô SDEs taking values in *n*-[dimensional](https://en.wikipedia.org/wiki/Dimension) [Euclidean space](https://en.wikipedia.org/wiki/Euclidean_space) **R**<sup>*n*</sup> and driven by an *m*-dimensional Brownian motion *B*; the proof may be found in Øksendal (2003, §5.2).

Let *T* \> 0, and let

$\mu :\mathbb {R} ^{n}\times [0,T]\to \mathbb {R} ^{n};$

$\sigma :\mathbb {R} ^{n}\times [0,T]\to \mathbb {R} ^{n\times m};$

be [measurable functions](https://en.wikipedia.org/wiki/Measurable_function) for which there exist constants *C* and *D* such that

${\big |}\mu (x,t){\big |}+{\big |}\sigma (x,t){\big |}\leq C{\big (}1+|x|{\big )};$

${\big |}\mu (x,t)-\mu (y,t){\big |}+{\big |}\sigma (x,t)-\sigma (y,t){\big |}\leq D|x-y|;$

for all *t* ∈ \[0, *T*\] and all *x* and *y* ∈ **R**<sup>*n*</sup>, where

$|\sigma |^{2}=\sum _{i,j=1}^{n}|\sigma _{ij}|^{2}.$

Let *Z* be a random variable that is independent of the *σ*-algebra generated by *B*<sub>*s*</sub>, *s* ≥ 0, and with finite [second moment](https://en.wikipedia.org/wiki/Moment_(mathematics) "Moment (mathematics)"):

$\mathbb {E} {\big [}|Z|^{2}{\big ]}<+\infty .$

Then the stochastic differential equation/initial value problem

$\mathrm {d} X_{t}=\mu (X_{t},t)\,\mathrm {d} t+\sigma (X_{t},t)\,\mathrm {d} B_{t}{\mbox{ for }}t\in [0,T];$

$X_{0}=Z;$

has a P-[almost surely](https://en.wikipedia.org/wiki/Almost_surely) unique *t*-continuous solution (*t*, *ω*) ↦ *X*<sub>*t*</sub>(*ω*) such that *X* is [adapted](https://en.wikipedia.org/wiki/Adapted_process) to the [filtration](https://en.wikipedia.org/wiki/Filtration_(abstract_algebra)) *F*<sub>*t*</sub><sup>*Z*</sup> generated by *Z* and *B*<sub>*s*</sub>, *s* ≤ *t*, and

$\mathbb {E} \left[\int _{0}^{T}|X_{t}|^{2}\,\mathrm {d} t\right]<+\infty .$

### General case: local Lipschitz condition and maximal solutions

The stochastic differential equation above is only a special case of a more general form

$\mathrm {d} Y_{t}=\alpha (t,Y_{t})\mathrm {d} X_{t}$

where

- $X$ is a continuous semimartingale in $\mathbb {R} ^{n}$ and $Y$ is a continuous semimartingale in $\mathbb {R} ^{d}$
- $\alpha :\mathbb {R} _{+}\times U\to \operatorname {Lin} (\mathbb {R} ^{n};\mathbb {R} ^{d})$ is a map from some open nonempty set $U\subset \mathbb {R} ^{d}$, where $\operatorname {Lin} (\mathbb {R} ^{n};\mathbb {R} ^{d})$ is the space of all linear maps from $\mathbb {R} ^{n}$ to $\mathbb {R} ^{d}$.

More generally one can also look at stochastic differential equations on [[Manifold|manifolds]].

Whether the solution of this equation explodes depends on the choice of $\alpha$. Suppose $\alpha$ satisfies some local Lipschitz condition, i.e., for $t\geq 0$ and some compact set $K\subset U$ and some constant $L(t,K)$ the condition

$|\alpha (s,y)-\alpha (s,x)|\leq L(t,K)|y-x|,\quad x,y\in K,\;0\leq s\leq t,$

where $|\cdot |$ is the Euclidean norm. This condition guarantees the existence and uniqueness of a so-called *maximal solution*.

Suppose $\alpha$ is continuous and satisfies the above local Lipschitz condition and let $F:\Omega \to U$ be some initial condition, meaning it is a measurable function with respect to the initial σ-algebra. Let $\zeta :\Omega \to {\overline {\mathbb {R} }}_{+}$ be a [predictable stopping time](https://en.wikipedia.org/wiki/Predictable_stopping_time) with $\zeta >0$ almost surely. A $U$-valued semimartingale $(Y_{t})_{t<\zeta }$ is called a *maximal solution* of

$dY_{t}=\alpha (t,Y_{t})dX_{t},\quad Y_{0}=F$

with *life time* $\zeta$ if

- for one (and hence all) announcing $\zeta _{n}\nearrow \zeta$ the stopped process $Y^{\zeta _{n}}$ is a solution to the *stopped stochastic differential equation*

$\mathrm {d} Y=\alpha (t,Y)\mathrm {d} X^{\zeta _{n}}$

- on the set $\{\zeta <\infty \}$ we have almost surely that $Y_{t}\to \partial U$ with $t\to \zeta$.

$\zeta$ is also a so-called *explosion time*.

## Some explicitly solvable examples

Explicitly solvable SDEs include:

### Linear SDE: General case

$\mathrm {d} X_{t}=(a(t)X_{t}+c(t))\mathrm {d} t+(b(t)X_{t}+d(t))\mathrm {d} W_{t}$

$X_{t}=\Phi _{t,t_{0}}\left(X_{t_{0}}+\int _{t_{0}}^{t}\Phi _{s,t_{0}}^{-1}(c(s)-b(s)d(s))\mathrm {d} s+\int _{t_{0}}^{t}\Phi _{s,t_{0}}^{-1}d(s)\mathrm {d} W_{s}\right)$

where

$\Phi _{t,t_{0}}=\exp \left(\int _{t_{0}}^{t}\left(a(s)-{\frac {b^{2}(s)}{2}}\right)\mathrm {d} s+\int _{t_{0}}^{t}b(s)\mathrm {d} W_{s}\right)$

### Reducible SDEs: Case 1

$\mathrm {d} X_{t}={\frac {1}{2}}f(X_{t})f'(X_{t})\mathrm {d} t+f(X_{t})\mathrm {d} W_{t}$

for a given differentiable function $f$ is equivalent to the Stratonovich SDE

$\mathrm {d} X_{t}=f(X_{t})\circ W_{t}$

which has a general solution

$X_{t}=h^{-1}(W_{t}+h(X_{0}))$

where

$h(x)=\int ^{x}{\frac {\mathrm {d} s}{f(s)}}$

### Reducible SDEs: Case 2

$\mathrm {d} X_{t}=\left(\alpha f(X_{t})+{\frac {1}{2}}f(X_{t})f'(X_{t})\right)\mathrm {d} t+f(X_{t})\mathrm {d} W_{t}$

for a given differentiable function $f$ is equivalent to the Stratonovich SDE

$\mathrm {d} X_{t}=\alpha f(X_{t})\mathrm {d} t+f(X_{t})\circ W_{t}$

which is reducible to

$\mathrm {d} Y_{t}=\alpha \mathrm {d} t+\mathrm {d} W_{t}$

where $Y_{t}=h(X_{t})$ where $h$ is defined as before. Its general solution is

$X_{t}=h^{-1}(\alpha t+W_{t}+h(X_{0}))$

## SDEs and supersymmetry

In supersymmetric theory of SDEs, stochastic dynamics is defined via stochastic evolution operator acting on the [differential forms](https://en.wikipedia.org/wiki/Differential_form) on the [phase](https://en.wikipedia.org/wiki/Phase_space)/[state](https://en.wikipedia.org/wiki/State_space) space of the model. In this formulation of stochastic dynamics, all SDEs possess topological [supersymmetry](https://en.wikipedia.org/wiki/Supersymmetry) which represents the preservation of the continuity of the phase space by continuous time flow. The spontaneous breakdown of this supersymmetry is the mathematical essence of the ubiquitous dynamical phenomenon known across disciplines as [chaos](https://en.wikipedia.org/wiki/Chaos_theory).

## See also

- [Backward stochastic differential equation](https://en.wikipedia.org/wiki/Backward_stochastic_differential_equation)
- [Langevin dynamics](https://en.wikipedia.org/wiki/Langevin_dynamics)
- [Local volatility](https://en.wikipedia.org/wiki/Local_volatility)
- [Stochastic process](https://en.wikipedia.org/wiki/Stochastic_process)
- [Stochastic volatility](https://en.wikipedia.org/wiki/Stochastic_volatility)
- [Stochastic partial differential equations](https://en.wikipedia.org/wiki/Stochastic_partial_differential_equations)
- [Diffusion process](https://en.wikipedia.org/wiki/Diffusion_process)
- [Stochastic difference equation](https://en.wikipedia.org/wiki/Stochastic_difference_equation)
- [Supersymmetric theory of stochastic dynamics](https://en.wikipedia.org/wiki/Supersymmetric_theory_of_stochastic_dynamics)

## References

1.  ^       [Rogers, L.C.G.](https://en.wikipedia.org/wiki/Chris_Rogers_(mathematician) "Chris Rogers (mathematician)"); [Williams, David](https://en.wikipedia.org/wiki/David_Williams_(mathematician) "David Williams (mathematician)") (2000). *Diffusions, Markov Processes and Martingales, Vol 2: Ito Calculus* (2nd ed., Cambridge Mathematical Library ed.). [Cambridge University Press](https://en.wikipedia.org/wiki/Cambridge_University_Press). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1017/CBO9780511805141](https://doi.org/10.1017%2FCBO9780511805141). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-77594-9](https://en.wikipedia.org/wiki/Special:BookSources/0-521-77594-9). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [42874839](https://search.worldcat.org/oclc/42874839).
2.  ^    Musiela, M., and Rutkowski, M. (2004), Martingale Methods in Financial Modelling, 2nd Edition, Springer Verlag, Berlin.
3.  ^        [Øksendal, Bernt K.](https://en.wikipedia.org/wiki/Bernt_%C3%98ksendal) (2003). *Stochastic Differential Equations: An Introduction with Applications*. Berlin: Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [3-540-04758-1](https://en.wikipedia.org/wiki/Special:BookSources/3-540-04758-1).
4.  Kunita, H. (2004). Stochastic Differential Equations Based on Lévy Processes and Stochastic Flows of Diffeomorphisms. In: Rao, M.M. (eds) Real and Stochastic Analysis. Trends in Mathematics. Birkhäuser Boston. [https://doi.org/10.1007/978-1-4612-2054-1_6](https://doi.org/10.1007/978-1-4612-2054-1_6)
5.  Imkeller, Peter; Schmalfuss, Björn (2001). ["The Conjugacy of Stochastic and Random Differential Equations and the Existence of Global Attractors"](https://dx.doi.org/10.1023/a:1016673307045). *Journal of Dynamics and Differential Equations*. **13** (2): 215–249. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1023/a:1016673307045](https://doi.org/10.1023%2Fa%3A1016673307045). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1040-7294](https://search.worldcat.org/issn/1040-7294). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [3120200](https://api.semanticscholar.org/CorpusID:3120200).
6.  ^    Emery, Michel (1989). *Stochastic calculus in manifolds*. Universitext. Springer Berlin, Heidelberg. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-3-642-75051-9](https://doi.org/10.1007%2F978-3-642-75051-9). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-51664-4](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-51664-4).
7.  Brzeźniak, Zdzisław; [Elworthy, K. D.](https://en.wikipedia.org/wiki/K._David_Elworthy) (5 January 2000). "Stochastic differential equations on Banach manifolds". *Methods of Functional Analysis and Topology*. **6** (1): 43–84.
8.  ^   Armstrong J. and [Brigo D.](https://en.wikipedia.org/wiki/Damiano_Brigo) (2018). Intrinsic stochastic differential equations as jets. Proc. R. Soc. A., 474: 20170559, [http://doi.org/10.1098/rspa.2017.0559](https://doi.org/10.1098/rspa.2017.0559)
9.  ^    Armstrong, J., Brigo, D. and Rossi Ferrucci, E. (2019), Optimal approximation of SDEs on submanifolds: the Itô-vector and Itô-jet projections. Proc. London Math. Soc., 119: 176-213. [https://doi.org/10.1112/plms.12226](https://doi.org/10.1112/plms.12226).
10. Parisi, G.; Sourlas, N. (1979). "Random Magnetic Fields, Supersymmetry, and Negative Dimensions". *Physical Review Letters*. **43** (11): 744–745. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1979PhRvL..43..744P](https://ui.adsabs.harvard.edu/abs/1979PhRvL..43..744P). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1103/PhysRevLett.43.744](https://doi.org/10.1103%2FPhysRevLett.43.744).
11. ^   Kloeden, P.E., Platen E. (1992). Numerical Solution of Stochastic Differential Equations. Springer, Berlin, Heidelberg. DOI: [https://doi.org/10.1007/978-3-662-12616-5](https://doi.org/10.1007/978-3-662-12616-5)
12. Artemiev, S.S., Averina, T.A. (1997). Numerical Analysis of Systems of Ordinary and Stochastic Differential Equations. VSP, Utrecht, The Netherlands. DOI: [https://doi.org/10.1515/9783110944662](https://doi.org/10.1515/9783110944662)
13. Kuznetsov, D.F. (2023). Strong approximation of iterated Itô and Stratonovich stochastic integrals: Method of generalized multiple Fourier series. Application to numerical integration of Itô SDEs and semilinear SPDEs. Differ. Uravn. Protsesy Upr., no. 1. DOI: [https://doi.org/10.21638/11701/spbu35.2023.110](https://doi.org/10.21638/11701/spbu35.2023.110)
14. Rybakov, K.A. (2023). Spectral representations of iterated stochastic integrals and their application for modeling nonlinear stochastic dynamics. Mathematics, vol. 11, 4047. DOI: [https://doi.org/10.3390/math11194047](https://doi.org/10.3390/math11194047)
15. Gardiner, C W (2009). *Handbook of Stochastic Methods* (4th ed.). Berlin: Springer-Verlag. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-70712-7](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-70712-7).
16. Slavík, A. (2013). ["Generalized differential equations: Differentiability of solutions with respect to initial conditions and parameters"](https://doi.org/10.1016%2Fj.jmaa.2013.01.027). *Journal of Mathematical Analysis and Applications*. **402** (1): 261–274. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.jmaa.2013.01.027](https://doi.org/10.1016%2Fj.jmaa.2013.01.027).
17. Fengler, M. R. (2005), Semiparametric modeling of implied volatility, Springer Verlag, Berlin. DOI [https://doi.org/10.1007/3-540-30591-2](https://doi.org/10.1007/3-540-30591-2)
18. [Brigo, Damiano](https://en.wikipedia.org/wiki/Damiano_Brigo); [Mercurio, Fabio](https://en.wikipedia.org/wiki/Fabio_Mercurio) (2002). "Lognormal-mixture dynamics and calibration to market volatility smiles". *International Journal of Theoretical and Applied Finance*. **5** (4): 427–446. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1142/S0219024902001511](https://doi.org/10.1142%2FS0219024902001511).
19. Brigo, D, Mercurio, F, Sartorelli, G. (2003). Alternative asset-price dynamics and volatility smile, QUANT FINANC, 2003, Vol: 3, Pages: 173 - 183, [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1469-7688](https://search.worldcat.org/issn/1469-7688)
20. Steven Marcus (1981), "Modeling and approximation of stochastic differential equation driven by semimartigales", *Stochastics*, vol. 4, pp. 223–245
21. ["Detecting Market Abuse"](https://www.risk.net/regulation/1528679/detecting-market-abuse). Risk Magazine. 2 November 2004.
22. ["The detection of Market Abuse on financial markets: a quantitative approach"](https://www.consob.it/documents/1912911/2006254/qdf54en.pdf/d31b160c-9ba5-e08d-d39d-a78bddfc698e). Consob – The Italian Securities and Exchange Commission.
23. Hackenbroch, Wolfgang; Thalmaier, Anton (1994). *Stochastische Analysis: Eine Einführung in die Theorie der stetigen Semimartingale* (in German). Vieweg+Teubner Verlag Wiesbaden. p. 364-365. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-519-02229-9](https://en.wikipedia.org/wiki/Special:BookSources/978-3-519-02229-9).
24. ^   Friz, P. and Hairer, M. (2020). A Course on Rough Paths with an Introduction to Regularity Structures, 2nd ed., Springer-Verlag, Heidelberg, DOI [https://doi.org/10.1007/978-3-030-41556-3](https://doi.org/10.1007/978-3-030-41556-3)
25. Armstrong, J., Bellani, C., Brigo, D. and Cass, T. (2021). Option pricing models without probability: a rough paths approach. Mathematical Finance, vol. 31, pages 1494–1521.
26. Hackenbroch, Wolfgang; Thalmaier, Anton (1994). *Stochastische Analysis: Eine Einführung in die Theorie der stetigen Semimartingale* (in German). Vieweg+Teubner Verlag Wiesbaden. pp. 297–299. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-519-02229-9](https://en.wikipedia.org/wiki/Special:BookSources/978-3-519-02229-9).

## Further reading

- [Evans, Lawrence C.](https://en.wikipedia.org/wiki/Lawrence_C._Evans) (2013). [An Introduction to Stochastic Differential Equations](https://bookstore.ams.org/mbk-82) American Mathematical Society.
- Adomian, George (1983). *Stochastic systems*. Mathematics in Science and Engineering (169). Orlando, FL: Academic Press Inc.
- Adomian, George (1986). [Nonlinear stochastic operator equations](https://archive.org/details/nonlinearstochas0000adom). Orlando, FL: Academic Press Inc. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-12-044375-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-12-044375-8).
- Adomian, George (1989). *Nonlinear stochastic systems theory and applications to physics*. Mathematics and its Applications (46). Dordrecht: Kluwer Academic Publishers Group.
- Calin, Ovidiu (2015). *An Informal Introduction to Stochastic Calculus with Applications*. Singapore: World Scientific Publishing. p. 315. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-981-4678-93-3](https://en.wikipedia.org/wiki/Special:BookSources/978-981-4678-93-3).
- Teugels, J.; Sund, B., eds. (2004). *Encyclopedia of Actuarial Science*. Chichester: Wiley. pp. 523–527.
- [Gardiner, C. W.](https://en.wikipedia.org/wiki/Crispin_Gardiner) (2004). *Handbook of Stochastic Methods: for Physics, Chemistry and the Natural Sciences*. Springer. p. 415.
- Mikosch, Thomas (1998). *Elementary Stochastic Calculus: with Finance in View*. Singapore: World Scientific Publishing. p. 212. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [981-02-3543-7](https://en.wikipedia.org/wiki/Special:BookSources/981-02-3543-7).
- Seifedine Kadry (2007). "A Solution of Linear Stochastic Differential Equation". *Wseas Transactions on Mathematics*. USA: WSEAS TRANSACTIONS on MATHEMATICS, April 2007.: 618. [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1109-2769](https://search.worldcat.org/issn/1109-2769).
- Higham, Desmond J. (January 2001). "An Algorithmic Introduction to Numerical Simulation of Stochastic Differential Equations". *SIAM Review*. **43** (3): 525–546. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2001SIAMR..43..525H](https://ui.adsabs.harvard.edu/abs/2001SIAMR..43..525H). [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.137.6375](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.137.6375). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/S0036144500378302](https://doi.org/10.1137%2FS0036144500378302).
- Higham, Desmond; Kloeden, Peter (2021). *An Introduction to the Numerical Simulation of Stochastic Differential Equations*. Society for Industrial and Applied Mathematics. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-611976-42-7](https://en.wikipedia.org/wiki/Special:BookSources/978-1-611976-42-7).
