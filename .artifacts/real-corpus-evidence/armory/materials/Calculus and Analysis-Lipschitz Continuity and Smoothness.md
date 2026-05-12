[[calculus-analysis.base]]

> Source: [Lipschitz continuity](https://en.wikipedia.org/wiki/Lipschitz_continuity)
> License: Wikipedia content is available under CC BY-SA 4.0.

![[media/1a585ff42248bb834623fa96471bdd9f8a8c7cf5.gif]]
For a Lipschitz continuous function, there exists a double cone (white) whose origin can be moved along the graph so that the whole graph always stays outside the double cone

In [mathematical analysis](https://en.wikipedia.org/wiki/Mathematical_analysis), **Lipschitz continuity**, named after [German](https://en.wikipedia.org/wiki/Germany) [mathematician](https://en.wikipedia.org/wiki/Mathematician) [Rudolf Lipschitz](https://en.wikipedia.org/wiki/Rudolf_Lipschitz), is a strong form of [uniform continuity](https://en.wikipedia.org/wiki/Uniform_continuity) for [functions](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)"). Intuitively, a Lipschitz [continuous function](https://en.wikipedia.org/wiki/Continuous_function) is limited in how fast it can change: there exists a real number such that, for every pair of points on the graph of this function, the [absolute value](https://en.wikipedia.org/wiki/Absolute_value) of the slope of the line connecting them is not greater than this real number; the smallest such bound is called the *Lipschitz constant* of the function (and is related to the *[modulus of uniform continuity](https://en.wikipedia.org/wiki/Modulus_of_continuity)*). For instance, every function that is defined on an interval and has a bounded first derivative is Lipschitz continuous.

In the theory of [differential equations](https://en.wikipedia.org/wiki/Differential_equation), Lipschitz continuity is the central condition of the [Picard–Lindelöf theorem](https://en.wikipedia.org/wiki/Picard%E2%80%93Lindel%C3%B6f_theorem) which guarantees the existence and uniqueness of the solution to an [initial value problem](https://en.wikipedia.org/wiki/Initial_value_problem). A special type of Lipschitz continuity, called [contraction](https://en.wikipedia.org/wiki/Contraction_mapping), is used in the [Banach fixed-point theorem](https://en.wikipedia.org/wiki/Banach_fixed-point_theorem).

We have the following chain of strict inclusions for functions over a [closed and bounded](https://en.wikipedia.org/wiki/Compactness) non-trivial interval of the real line:

**[Continuously differentiable](https://en.wikipedia.org/wiki/Continuously_differentiable)** ⊂ **Lipschitz continuous** ⊂ $\alpha$**-[Hölder continuous](https://en.wikipedia.org/wiki/H%C3%B6lder_continuous)**,

where $0<\alpha \leq 1$. We also have

**Lipschitz continuous** ⊂ **[absolutely continuous](https://en.wikipedia.org/wiki/Absolutely_continuous)** ⊂ **[uniformly continuous](https://en.wikipedia.org/wiki/Uniformly_continuous)** ⊂ **[continuous](https://en.wikipedia.org/wiki/Continuous_function)**.

## Definitions

Given two [metric spaces](https://en.wikipedia.org/wiki/Metric_space) (*X*, *d*<sub>*X*</sub>) and (*Y*, *d*<sub>*Y*</sub>), where *d*<sub>*X*</sub> denotes the [metric](https://en.wikipedia.org/wiki/Metric_(mathematics)) on the set *X* and *d*<sub>*Y*</sub> is the metric on set *Y*, a function *f* : *X* → *Y* is called **Lipschitz continuous** if there exists a real constant *K* ≥ 0 such that, for all *x*<sub>1</sub> and *x*<sub>2</sub> in *X*,

$d_{Y}(f(x_{1}),f(x_{2}))\leq Kd_{X}(x_{1},x_{2}).$

Any such *K* is referred to as a **Lipschitz constant** for the function *f,* and *f* may also be referred to as **K-Lipschitz**. The smallest constant is sometimes called **the (best) Lipschitz constant** of *f* or the **dilation** of *f*. If *K* = 1 the function is called a **[short map](https://en.wikipedia.org/wiki/Short_map)**, and if 0 ≤ *K* \< 1 and *f* maps a metric space to itself, the function is called a **[contraction](https://en.wikipedia.org/wiki/Contraction_mapping)**.

In particular, a [real-valued function](https://en.wikipedia.org/wiki/Real-valued_function) *f* : **R** → **R** is called Lipschitz continuous if there exists a positive real constant K such that, for all real *x*<sub>1</sub> and *x*<sub>2</sub>,

$|f(x_{1})-f(x_{2})|\leq K|x_{1}-x_{2}|.$

In this case, *Y* is the set of [real numbers](https://en.wikipedia.org/wiki/Real_number) **R** with the standard metric *d*<sub>*Y*</sub>(*y<sub>1</sub>*, *y<sub>2</sub>*) = \|*y<sub>1</sub>* − *y<sub>2</sub>*\|, and *X* is a subset of **R**.

In general, the inequality is (trivially) satisfied if *x*<sub>1</sub> = *x*<sub>2</sub>. Otherwise, one can equivalently define a function to be Lipschitz continuous [if and only if](https://en.wikipedia.org/wiki/If_and_only_if) there exists a constant *K* ≥ 0 such that, for all *x*<sub>1</sub> ≠ *x*<sub>2</sub>,

${\frac {d_{Y}(f(x_{1}),f(x_{2}))}{d_{X}(x_{1},x_{2})}}\leq K.$

For real-valued functions of several real variables, this holds if and only if the absolute value of the slopes of all secant lines are bounded by *K*. The set of lines of slope *K* passing through a point on the graph of the function forms a circular cone, and a function is Lipschitz if and only if the graph of the function everywhere lies completely outside of this cone (see figure).

A function is called **locally Lipschitz continuous** if for every *x* in *X* there exists a [neighborhood](https://en.wikipedia.org/wiki/Neighborhood_(mathematics)) *U* of *x* such that *f* restricted to *U* is Lipschitz continuous. Equivalently, if *X* is a [locally compact](https://en.wikipedia.org/wiki/Locally_compact) metric space, then *f* is locally Lipschitz if and only if it is Lipschitz continuous on every compact subset of *X*. In spaces that are not locally compact, this is a necessary but not a sufficient condition.

More generally, a function *f* defined on *X* is said to be **Hölder continuous** or to satisfy a **[Hölder condition](https://en.wikipedia.org/wiki/H%C3%B6lder_condition)** of order α \> 0 on *X* if there exists a constant *M* ≥ 0 such that

$d_{Y}(f(x_{1}),f(x_{2}))\leq Md_{X}(x_{1},x_{2})^{\alpha }$

for all *x*<sub>1</sub> and *x*<sub>2</sub> in *X*. Sometimes a Hölder condition of order α is also called a **uniform Lipschitz condition of order** α \> 0.

For a real number *K* ≥ 1, if

${\frac {1}{K}}d_{X}(x_{1},x_{2})\leq d_{Y}(f(x_{1}),f(x_{2}))\leq Kd_{X}(x_{1},x_{2})\quad {\text{ for all }}x_{1},x_{2}\in X,$

then *f* is called ***K*-bilipschitz** (also written ***K*-bi-Lipschitz**). We say *f* is **bilipschitz** or **bi-Lipschitz** to mean there exists such a *K*. A bilipschitz mapping is [injective](https://en.wikipedia.org/wiki/Injective_function), and is in fact a [homeomorphism](https://en.wikipedia.org/wiki/Homeomorphism) onto its image. A bilipschitz function is the same thing as an injective Lipschitz function whose [inverse function](https://en.wikipedia.org/wiki/Inverse_function) is also Lipschitz.

## Examples

Lipschitz continuous functions that are everywhere differentiable  

- The function $f(x)={\sqrt {x^{2}+5}}$ defined for all real numbers is Lipschitz continuous with the Lipschitz constant *K* = 1, because it is everywhere [differentiable](https://en.wikipedia.org/wiki/Differentiable_function) and the absolute value of the derivative is bounded above by 1. See the first property listed below under "[Properties](#Properties)".
- Likewise, the [sine](https://en.wikipedia.org/wiki/Sine) function is Lipschitz continuous because its derivative, the cosine function, is bounded above by 1 in absolute value.

Lipschitz continuous functions that are not everywhere differentiable  

- The function $f(x)=|x|$ defined on the reals is Lipschitz continuous with the Lipschitz constant equal to 1, by the [reverse triangle inequality](https://en.wikipedia.org/wiki/Reverse_triangle_inequality). More generally, a [norm](https://en.wikipedia.org/wiki/Norm_(mathematics) "Norm (mathematics)") on a vector space is Lipschitz continuous with respect to the associated metric, with the Lipschitz constant equal to 1.

Lipschitz continuous functions that are everywhere differentiable but not continuously differentiable  

- The function $f(x)\;=\;{\begin{cases}x^{2}\sin(1/x)&{\text{if }}x\neq 0\\0&{\text{if }}x=0\end{cases}}$, whose derivative exists but has an essential discontinuity at $x=0$.

Continuous functions that are not (globally) Lipschitz continuous  

- The function *f*(*x*) = √*x* defined on \[0, 1\] is *not* Lipschitz continuous. This function becomes infinitely steep as *x* approaches 0 since its derivative becomes infinite. However, it is uniformly continuous, and both [Hölder continuous](https://en.wikipedia.org/wiki/H%C3%B6lder_continuity) of class *C*<sup>0, α</sup> for α ≤ 1/2 and also [absolutely continuous](https://en.wikipedia.org/wiki/Absolutely_continuous) on \[0, 1\] (both of which imply the former).

Differentiable functions that are not (locally) Lipschitz continuous  

- The function *f* defined by *f*(0) = 0 and *f*(*x*) = *x*<sup>3/2</sup>sin(1/*x*) for 0\<*x*≤1 gives an example of a function that is differentiable on a compact set while not locally Lipschitz because its derivative function is not bounded. See also the first property below.

Analytic functions that are not (globally) Lipschitz continuous  

- The [exponential function](https://en.wikipedia.org/wiki/Exponential_function) becomes arbitrarily steep as *x* → ∞, and therefore is *not* globally Lipschitz continuous, despite being an [analytic function](https://en.wikipedia.org/wiki/Analytic_function).
- The function *f*(*x*) = *x*<sup>2</sup> with domain all real numbers is *not* Lipschitz continuous. This function becomes arbitrarily steep as *x* approaches infinity. It is however locally Lipschitz continuous.

## Properties

- An everywhere differentiable function *g* : **R** → **R** is Lipschitz continuous (with *K* = sup \|*g*′(*x*)\|) if and only if it has a bounded [first derivative](https://en.wikipedia.org/wiki/First_derivative); one direction follows from the [mean value theorem](https://en.wikipedia.org/wiki/Mean_value_theorem). In particular, any continuously differentiable function is locally Lipschitz, as continuous functions are locally bounded so its gradient is locally bounded as well.
- A Lipschitz function *g* : **R** → **R** is [absolutely continuous](https://en.wikipedia.org/wiki/Absolutely_continuous) and therefore is differentiable [almost everywhere](https://en.wikipedia.org/wiki/Almost_everywhere), that is, differentiable at every point outside a set of [Lebesgue measure](https://en.wikipedia.org/wiki/Lebesgue_measure) zero. Its derivative is [essentially bounded](https://en.wikipedia.org/wiki/Essentially_bounded) in magnitude by the Lipschitz constant, and for *a* \< *b*, the difference *g*(*b*) − *g*(*a*) is equal to the integral of the derivative *g*′ on the interval \[*a*, *b*\].
  - Conversely, if *f* : *I* → **R** is absolutely continuous and thus differentiable almost everywhere, and satisfies \|*f′*(*x*)\| ≤ *K* for almost all *x* in *I*, then *f* is Lipschitz continuous with Lipschitz constant at most *K*.
  - More generally, [Rademacher's theorem](https://en.wikipedia.org/wiki/Rademacher%27s_theorem) extends the differentiability result to Lipschitz mappings between Euclidean spaces: a Lipschitz map *f* : *U* → **R**<sup>*m*</sup>, where *U* is an open set in **R**<sup>*n*</sup>, is [almost everywhere](https://en.wikipedia.org/wiki/Almost_everywhere) [differentiable](https://en.wikipedia.org/wiki/Derivative). Moreover, if *K* is the best Lipschitz constant of *f*, then $\|Df(x)\|\leq K$ whenever the [total derivative](https://en.wikipedia.org/wiki/Total_derivative) *Df* exists.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>
- For a differentiable Lipschitz map $f:U\to \mathbb {R} ^{m}$ the inequality $\|Df\|_{L^{\infty }(U)}\leq K$ holds for the best Lipschitz constant $K$ of $f$. If the domain $U$ is convex then in fact $\|Df\|_{L^{\infty }(U)}=K$.<sup>\[*[further explanation needed](https://en.wikipedia.org/wiki/Wikipedia:Please_clarify)*\]</sup>
- Suppose that {*f<sub>n</sub>*} is a sequence of Lipschitz continuous mappings between two metric spaces, and that all *f<sub>n</sub>* have Lipschitz constant bounded by some *K*. If *f<sub>n</sub>* converges to a mapping *f* [uniformly](https://en.wikipedia.org/wiki/Uniform_convergence), then *f* is also Lipschitz, with Lipschitz constant bounded by the same *K*. In particular, this implies that the set of real-valued functions on a compact metric space with a particular bound for the Lipschitz constant is a closed and convex subset of the [Banach space](https://en.wikipedia.org/wiki/Banach_space) of continuous functions. This result does not hold for sequences in which the functions may have *unbounded* Lipschitz constants, however. In fact, the space of all Lipschitz functions on a compact metric space is a subalgebra of the Banach space of continuous functions, and thus dense in it, an elementary consequence of the [Stone–Weierstrass theorem](https://en.wikipedia.org/wiki/Stone%E2%80%93Weierstrass_theorem) (or as a consequence of [Weierstrass approximation theorem](https://en.wikipedia.org/wiki/Weierstrass_approximation_theorem), because every polynomial is locally Lipschitz continuous).
- Every Lipschitz continuous map is [uniformly continuous](https://en.wikipedia.org/wiki/Uniformly_continuous), and hence [continuous](https://en.wikipedia.org/wiki/Continuous_function). More generally, a set of functions with bounded Lipschitz constant forms an [equicontinuous](https://en.wikipedia.org/wiki/Equicontinuous) set. The [Arzelà–Ascoli theorem](https://en.wikipedia.org/wiki/Arzel%C3%A0%E2%80%93Ascoli_theorem) implies that if {*f<sub>n</sub>*} is a [uniformly bounded](https://en.wikipedia.org/wiki/Uniformly_bounded) sequence of functions with bounded Lipschitz constant, then it has a convergent subsequence. By the result of the previous paragraph, the limit function is also Lipschitz, with the same bound for the Lipschitz constant. In particular the set of all real-valued Lipschitz functions on a compact metric space *X* having Lipschitz constant ≤ *K*  is a [locally compact](https://en.wikipedia.org/wiki/Locally_compact_space) convex subset of the Banach space *C*(*X*).
- For a family of Lipschitz continuous functions *f*<sub>α</sub> with common constant, the function $\sup _{\alpha }f_{\alpha }$ (and $\inf _{\alpha }f_{\alpha }$) is Lipschitz continuous as well, with the same Lipschitz constant, provided it assumes a finite value at least at a point.
- If *U* is a subset of the metric space *M* and *f* : *U* → **R** is a Lipschitz continuous function, there always exist Lipschitz continuous maps *M* → **R** that extend *f* and have the same Lipschitz constant as *f* (see also [Kirszbraun theorem](https://en.wikipedia.org/wiki/Kirszbraun_theorem)). An extension is provided by

${\tilde {f}}(x):=\inf _{u\in U}\{f(u)+k\,d(x,u)\},$

where *k* is a Lipschitz constant for *f* on *U*.

## Lipschitz manifolds

A **Lipschitz structure** on a [topological manifold](https://en.wikipedia.org/wiki/Topological_manifold) is defined using an [atlas of charts](https://en.wikipedia.org/wiki/Atlas_(topology) "Atlas (topology)") whose transition maps are bilipschitz; this is possible because bilipschitz maps form a [pseudogroup](https://en.wikipedia.org/wiki/Pseudogroup). Such a structure allows one to define locally Lipschitz maps between such manifolds, similarly to how one defines smooth maps between [smooth manifolds](https://en.wikipedia.org/wiki/Smooth_manifold): if M and N are Lipschitz manifolds, then a function $f:M\to N$ is **locally Lipschitz** if and only if for every pair of coordinate charts $\phi :U\to M$ and $\psi :V\to N$, where U and V are open sets in the corresponding Euclidean spaces, the composition 

$$
\psi ^{-1}\circ f\circ \phi :U\cap (f\circ \phi )^{-1}(\psi (V))\to V
$$

 is locally Lipschitz. This definition does not rely on defining a metric on M or N.

This structure is intermediate between that of a [piecewise-linear manifold](https://en.wikipedia.org/wiki/Piecewise-linear_manifold) and a [topological manifold](https://en.wikipedia.org/wiki/Topological_manifold): a PL structure gives rise to a unique Lipschitz structure. While Lipschitz manifolds are closely related to topological manifolds, [Rademacher's theorem](https://en.wikipedia.org/wiki/Rademacher%27s_theorem) allows one to do analysis, yielding various applications.

## One-sided Lipschitz

Let *F*(*x*) be an [upper semi-continuous](https://en.wikipedia.org/wiki/Semi-continuity) function of *x*, and that *F*(*x*) is a closed, convex set for all *x*. Then *F* is one-sided Lipschitz if

$(x_{1}-x_{2})^{T}(F(x_{1})-F(x_{2}))\leq C\Vert x_{1}-x_{2}\Vert ^{2}$

for some *C* and for all *x*<sub>1</sub> and *x*<sub>2</sub>.

It is possible that the function *F* could have a very large Lipschitz constant but a moderately sized, or even negative, one-sided Lipschitz constant. For example, the function

${\begin{cases}F:\mathbf {R} ^{2}\to \mathbf {R} ,\\F(x,y)=-50(y-\cos(x))\end{cases}}$

has Lipschitz constant *K* = 50 and a one-sided Lipschitz constant *C* = 0. An example which is one-sided Lipschitz but not Lipschitz continuous is *F*(*x*) = *e*<sup>−*x*</sup>, with *C* = 0.

## See also

- [Contraction mapping](https://en.wikipedia.org/wiki/Contraction_mapping) – Function reducing distance between all points
- [Dini continuity](https://en.wikipedia.org/wiki/Dini_continuity)
- [Modulus of continuity](https://en.wikipedia.org/wiki/Modulus_of_continuity)
- [Quasi-isometry](https://en.wikipedia.org/wiki/Quasi-isometry)
- [Johnson–Lindenstrauss lemma](https://en.wikipedia.org/wiki/Johnson%E2%80%93Lindenstrauss_lemma) – For any integer $n\geq 0$, any finite subset *X*⊆***R**<sup>n</sup>*, and any real number $0<\epsilon <1$, there exists a (1+ε)-bi-Lipschitz function $f:\mathbb {R} ^{n}\to \mathbb {R} ^{d},$ where $d=\lceil 15(\ln |X|)/\varepsilon ^{2}\rceil .$

## References

1.  Sohrab, H. H. (2003). [Basic Real Analysis](https://books.google.com/books?id=gBPI_oYZoMMC&pg=PA142). Vol. 231. Birkhäuser. p. 142. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-8176-4211-0](https://en.wikipedia.org/wiki/Special:BookSources/0-8176-4211-0).
2.  Thomson, Brian S.; Bruckner, Judith B.; Bruckner, Andrew M. (2001). [Elementary Real Analysis](https://books.google.com/books?id=6l_E9OTFaK0C&pg=PA623). Prentice-Hall. p. 623. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-13-019075-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-13-019075-8).
3.  Searcóid, Mícheál Ó (2006), ["Lipschitz Functions"](https://books.google.com/books?id=aP37I4QWFRcC&pg=PA154), *Metric Spaces*, Springer undergraduate mathematics series, Berlin, New York: [Springer-Verlag](https://en.wikipedia.org/wiki/Springer-Verlag), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-84628-369-7](https://en.wikipedia.org/wiki/Special:BookSources/978-1-84628-369-7)
4.  Benyamini, Yoav; Lindenstrauss, Joram (2000). *Geometric Nonlinear Functional Analysis*. American Mathematical Society. p. 11. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-8218-0835-4](https://en.wikipedia.org/wiki/Special:BookSources/0-8218-0835-4).
5.  Burago, Dmitri; Burago, Yuri; Ivanov, Sergei (2001). *A Course in Metric Geometry*. American Mathematical Society. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-8218-2129-6](https://en.wikipedia.org/wiki/Special:BookSources/0-8218-2129-6).
6.  [Gromov, Mikhael](https://en.wikipedia.org/wiki/Mikhael_Gromov_(mathematician) "Mikhael Gromov (mathematician)") (1999). "Quantitative Homotopy Theory". In Rossi, Hugo (ed.). *Prospects in Mathematics: Invited Talks on the Occasion of the 250th Anniversary of Princeton University, March 17-21, 1996, Princeton University*. American Mathematical Society. p. 46. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-8218-0975-X](https://en.wikipedia.org/wiki/Special:BookSources/0-8218-0975-X).
7.  Robbin, Joel W., [Continuity and Uniform Continuity](http://www.math.wisc.edu/~robbin/521dir/cont.pdf) (PDF)
8.  ^   [Rosenberg, Jonathan](https://en.wikipedia.org/wiki/Jonathan_Rosenberg_(mathematician) "Jonathan Rosenberg (mathematician)") (1988). ["Applications of analysis on Lipschitz manifolds"](https://projecteuclid.org/proceedings/proceedings-of-the-centre-for-mathematics-and-its-applications/Miniconference-on-Harmonic-Analysis-and-Operator-Algebras/Chapter/Applications-of-analysis-on-Lipschitz-manifolds/pcma/1416336222). *Miniconferences on harmonic analysis and operator algebras (Canberra, 1987)*. Canberra: [Australian National University](https://en.wikipedia.org/wiki/Australian_National_University). pp. 269–283. [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0954004](https://mathscinet.ams.org/mathscinet-getitem?mr=0954004)
9.  ["Topology of manifolds"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society), 2001 \[1994\]
10. Donchev, Tzanko; Farkhi, Elza (1998). "Stability and Euler Approximation of One-sided Lipschitz Differential Inclusions". *SIAM Journal on Control and Optimization*. **36** (2): 780–796. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/S0363012995293694](https://doi.org/10.1137%2FS0363012995293694).
