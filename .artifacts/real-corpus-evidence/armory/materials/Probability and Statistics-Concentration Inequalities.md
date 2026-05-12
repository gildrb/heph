[[probability-statistics.base]]

> Source: [Concentration inequality](https://en.wikipedia.org/wiki/Concentration_inequality)
> License: Wikipedia content is available under CC BY-SA 4.0.

In [probability theory](https://en.wikipedia.org/wiki/Probability_theory), **concentration inequalities** provide mathematical bounds on the probability of a [random variable](https://en.wikipedia.org/wiki/Random_variable) deviating from some value (typically, its [expected value](https://en.wikipedia.org/wiki/Expected_value)). The deviation or other function of the random variable can be thought of as a secondary random variable. The simplest example of the concentration of such a secondary random variable is the CDF of the first random variable which concentrates the probability to unity. If an analytic form of the CDF is available this provides a concentration **equality** that provides the exact probability of concentration. It is precisely when the CDF is difficult to calculate or even the exact form of the first random variable is unknown that the applicable concentration inequalities provide useful insight.

Another almost universal example of a secondary random variable is the [[Law of Large Numbers]] of classical probability theory which states that sums of independent random variables, under mild conditions, concentrate around their expectation with a high probability. Such sums are the most basic examples of random variables concentrated around their [mean](https://en.wikipedia.org/wiki/Mean).

Concentration inequalities can be sorted according to how much information about the random variable is needed in order to use them.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

## Markov's inequality

Let $X$ be a random variable that is non-negative ([almost surely](https://en.wikipedia.org/wiki/Almost_surely)). Then, for every constant $a>0$,

$\Pr(X\geq a)\leq {\frac {\operatorname {E} (X)}{a}}.$

Note the following extension to Markov's inequality: if $\Phi$ is a strictly increasing and non-negative function, then

$\Pr(X\geq a)=\Pr(\Phi (X)\geq \Phi (a))\leq {\frac {\operatorname {E} (\Phi (X))}{\Phi (a)}}.$

## Chebyshev's inequality

Chebyshev's inequality requires the following information on a random variable $X$:

- The expected value $\operatorname {E} [X]$ is finite.
- The [variance](https://en.wikipedia.org/wiki/Variance) $\operatorname {Var} [X]=\operatorname {E} [(X-\operatorname {E} [X])^{2}]$ is finite.

Then, for every constant $a>0$,

$\Pr(|X-\operatorname {E} [X]|\geq a)\leq {\frac {\operatorname {Var} [X]}{a^{2}}},$

or equivalently,

$\Pr(|X-\operatorname {E} [X]|\geq a\cdot \operatorname {Std} [X])\leq {\frac {1}{a^{2}}},$

where $\operatorname {Std} [X]$ is the [standard deviation](https://en.wikipedia.org/wiki/Standard_deviation) of $X$.

Chebyshev's inequality can be seen as a special case of the generalized Markov's inequality applied to the random variable $|X-\operatorname {E} [X]|$ with $\Phi (x)=x^{2}$.

## Vysochanskij–Petunin inequality

Let *X* be a random variable with unimodal distribution, mean *μ* and finite, non-zero variance *σ*<sup>2</sup>. Then, for any $\lambda >{\sqrt {\frac {8}{3}}}=1.63299\ldots ,$

$\Pr(\left|X-\mu \right|\geq \lambda \sigma )\leq {\frac {4}{9\lambda ^{2}}}.$

(For a relatively elementary proof see e.g.).

### One-sided Vysochanskij–Petunin inequality

For a unimodal random variable $X$ and $r\geq 0$, the one-sided Vysochanskij–Petunin inequality holds as follows:

$\Pr(X-E[X]\geq r)\leq {\begin{cases}{\dfrac {4}{9}}{\dfrac {\operatorname {Var} (X)}{r^{2}+\operatorname {Var} (X)}}&{\text{for }}r^{2}\geq {\dfrac {5}{3}}\operatorname {Var} (X),\\[5pt]{\dfrac {4}{3}}{\dfrac {\operatorname {Var} (X)}{r^{2}+\operatorname {Var} (X)}}-{\dfrac {1}{3}}&{\text{otherwise.}}\end{cases}}$

## Paley–Zygmund inequality

In contrast to most commonly used concentration inequalities, the Paley-Zygmund inequality provides a *lower* bound on the deviation probability.

## Cantelli's inequality

## Gauss's inequality

## Chernoff bounds

The generic Chernoff bound requires the [[Moment Generating Function]] of $X$, defined as $M_{X}(t):=\operatorname {E} \!\left[e^{tX}\right].$ It always exists, but may be infinite. From Markov's inequality, for every $t>0$:

$\Pr(X\geq a)\leq {\frac {\operatorname {E} [e^{tX}]}{e^{ta}}},$

and for every $t<0$:

$\Pr(X\leq a)\leq {\frac {\operatorname {E} [e^{tX}]}{e^{ta}}}.$

There are various Chernoff bounds for different distributions and different values of the parameter $t$. See  for a compilation of more concentration inequalities.

## Mill's inequality

Let $Z\sim N(0,\sigma ^{2})$. Then for every $t>0$ we have that:

$$
\operatorname {P} (|Z|>t)\leq {\sqrt {\frac {2}{\pi }}}{\frac {\sigma }{t}}\exp(-{\frac {t^{2}}{2\sigma ^{2}}}).
$$

## Bounds on sums of independent bounded variables

Let $X_{1},X_{2},\dots ,X_{n}$ be independent random variables such that, for all *i*:

$a_{i}\leq X_{i}\leq b_{i}$ [almost surely](https://en.wikipedia.org/wiki/Almost_surely).

$c_{i}:=b_{i}-a_{i}$

$\forall i:c_{i}\leq C$

Let $S_{n}$ be their sum, $E_{n}$ its [expected value](https://en.wikipedia.org/wiki/Expected_value) and $V_{n}$ its variance:

$S_{n}:=\sum _{i=1}^{n}X_{i}$

$E_{n}:=\operatorname {E} [S_{n}]=\sum _{i=1}^{n}\operatorname {E} [X_{i}]$

$V_{n}:=\operatorname {Var} [S_{n}]=\sum _{i=1}^{n}\operatorname {Var} [X_{i}]$

It is often interesting to bound the difference between the sum and its expected value. Several inequalities can be used.

1\. [Hoeffding's inequality](https://en.wikipedia.org/wiki/Hoeffding%27s_inequality) says that:

$\Pr \left[|S_{n}-E_{n}|>t\right]\leq 2\exp \left(-{\frac {2t^{2}}{\sum _{i=1}^{n}c_{i}^{2}}}\right)\leq 2\exp \left(-{\frac {2t^{2}}{nC^{2}}}\right)$

2\. The random variable $S_{n}-E_{n}$ is a special case of a [martingale](https://en.wikipedia.org/wiki/Martingale_(probability_theory) "Martingale (probability theory)"), and $S_{0}-E_{0}=0$. Hence, the general form of [Azuma's inequality](https://en.wikipedia.org/wiki/Azuma%27s_inequality) can also be used and it yields a similar bound:

$\Pr \left[|S_{n}-E_{n}|>t\right]<2\exp \left(-{\frac {2t^{2}}{\sum _{i=1}^{n}c_{i}^{2}}}\right)<2\exp \left(-{\frac {2t^{2}}{nC^{2}}}\right)$

This is a generalization of Hoeffding's since it can handle other types of martingales, as well as [supermartingales](https://en.wikipedia.org/wiki/Supermartingale) and [submartingales](https://en.wikipedia.org/wiki/Submartingale). See Fan et al. (2015). Note that if the simpler form of Azuma's inequality is used, the exponent in the bound is worse by a factor of 4.

3\. The sum function, $S_{n}=f(X_{1},\dots ,X_{n})$, is a special case of a function of *n* variables. This function changes in a bounded way: if variable *i* is changed, the value of *f* changes by at most $b_{i}-a_{i}<C$. Hence, [McDiarmid's inequality](https://en.wikipedia.org/wiki/McDiarmid%27s_inequality) can also be used and it yields a similar bound:

$\Pr \left[|S_{n}-E_{n}|>t\right]<2\exp \left(-{\frac {2t^{2}}{\sum _{i=1}^{n}c_{i}^{2}}}\right)<2\exp \left(-{\frac {2t^{2}}{nC^{2}}}\right)$

This is a different generalization of Hoeffding's since it can handle other functions besides the sum function, as long as they change in a bounded way.

4\. [Bennett's inequality](https://en.wikipedia.org/wiki/Bennett%27s_inequality) offers some improvement over Hoeffding's when the variances of the summands are small compared to their almost-sure bounds *C*. It says that:

$\Pr \left[|S_{n}-E_{n}|>t\right]\leq 2\exp \left[-{\frac {V_{n}}{C^{2}}}h\left({\frac {Ct}{V_{n}}}\right)\right],$ where $h(u)=(1+u)\log(1+u)-u$

5\. The first of [Bernstein's inequalities](https://en.wikipedia.org/wiki/Bernstein_inequalities_(probability_theory) "Bernstein inequalities (probability theory)") says that:

$\Pr \left[|S_{n}-E_{n}|>t\right]<2\exp \left(-{\frac {t^{2}/2}{V_{n}+C\cdot t/3}}\right)$

This is a generalization of Hoeffding's since it can handle random variables with not only almost-sure bound but both almost-sure bound and variance bound.

6\. Chernoff bounds have a particularly simple form in the case of sum of independent variables, since $\operatorname {E} [e^{t\cdot S_{n}}]=\prod _{i=1}^{n}{\operatorname {E} [e^{t\cdot X_{i}}]}$.

For example, suppose the variables $X_{i}$ satisfy $X_{i}\geq E(X_{i})-a_{i}-M$, for $1\leq i\leq n$. Then we have lower tail inequality:

$\Pr[S_{n}-E_{n}<-\lambda ]\leq \exp \left(-{\frac {\lambda ^{2}}{2(V_{n}+\sum _{i=1}^{n}a_{i}^{2}+M\lambda /3)}}\right)$

If $X_{i}$ satisfies $X_{i}\leq E(X_{i})+a_{i}+M$, we have upper tail inequality:

$\Pr[S_{n}-E_{n}>\lambda ]\leq \exp \left(-{\frac {\lambda ^{2}}{2(V_{n}+\sum _{i=1}^{n}a_{i}^{2}+M\lambda /3)}}\right)$

If $X_{i}$ are i.i.d., $|X_{i}|\leq 1$ and $\sigma ^{2}$ is the variance of $X_{i}$, a typical version of Chernoff inequality is:

$\Pr[|S_{n}|\geq k\sigma ]\leq 2e^{-k^{2}/4n}{\text{ for }}0\leq k\leq 2\sigma .$

7\. Similar bounds can be found in: [Rademacher distribution#Bounds on sums](https://en.wikipedia.org/wiki/Rademacher_distribution#Bounds_on_sums)

## Efron–Stein inequality

The Efron–Stein inequality (or influence inequality, or MG bound on variance) bounds the variance of a general function.

Suppose that $X_{1}\dots X_{n}$, $X_{1}'\dots X_{n}'$ are independent with $X_{i}'$ and $X_{i}$ having the same distribution for all $i$.

Let $X=(X_{1},\dots ,X_{n}),X^{(i)}=(X_{1},\dots ,X_{i-1},X_{i}',X_{i+1},\dots ,X_{n}).$ Then

$\mathrm {Var} (f(X))\leq {\frac {1}{2}}\sum _{i=1}^{n}E[(f(X)-f(X^{(i)}))^{2}].$

A proof may be found in e.g.,.

## Bretagnolle–Huber–Carol inequality

[Bretagnolle–Huber–Carol Inequality](https://en.wikipedia.org/wiki/Bretagnolle%E2%80%93Huber_inequality) bounds the difference between a vector of [multinomially distributed random variables](https://en.wikipedia.org/wiki/Multinomial_distribution) and a vector of expected values. A simple proof appears in (Appendix Section).

If a random vector $(Z_{1},Z_{2},Z_{3},\ldots ,Z_{n})$ is multinomially distributed with parameters $(p_{1},p_{2},\ldots ,p_{n})$ and satisfies $Z_{1}+Z_{2}+\dots +Z_{n}=M,$ then

$\Pr \left(\sum _{i=1}^{n}|Z_{i}-Mp_{i}|\geq 2M\varepsilon \right)\leq 2^{n}e^{-2M\varepsilon ^{2}}.$

This inequality is used to bound the [total variation distance](https://en.wikipedia.org/wiki/Total_variation_distance_of_probability_measures).

## Mason and van Zwet inequality

The Mason and van Zwet inequality for multinomial random vectors concerns a slight modification of the classical chi-square statistic.

Let the random vector $(N_{1},\ldots ,N_{k})$ be multinomially distributed with parameters $n$ and $(p_{1},\ldots ,p_{k})$ such that $p_{i}>0$ for $i<k.$ Then for every $C>0$ and $\delta >0$ there exist constants $a,b,c>0,$ such that for all $n\geq 1$ and $\lambda ,p_{1},\ldots ,p_{k-1}$ satisfying $\lambda >Cn\min\{p_{i}|1\leq i\leq k-1\}$ and $\sum _{i=1}^{k-1}p_{i}\leq 1-\delta ,$ we have

$\Pr \left(\sum _{i=1}^{k-1}{\frac {(N_{i}-np_{i})^{2}}{np_{i}}}>\lambda \right)\leq ae^{bk-c\lambda }.$

## Dvoretzky–Kiefer–Wolfowitz inequality

The Dvoretzky–Kiefer–Wolfowitz inequality bounds the difference between the real and the empirical [[Cumulative Distribution Function]].

Given a natural number $n$, let $X_{1},X_{2},\dots ,X_{n}$ be real-valued [independent and identically distributed](https://en.wikipedia.org/wiki/Independent_and_identically_distributed) [random variables](https://en.wikipedia.org/wiki/Random_variable) with [[Cumulative Distribution Function]] *F*(·). Let $F_{n}$ denote the associated [empirical distribution function](https://en.wikipedia.org/wiki/Empirical_distribution_function) defined by

$F_{n}(x)={\frac {1}{n}}\sum _{i=1}^{n}\mathbf {1} _{\{X_{i}\leq x\}},\qquad x\in \mathbb {R} .$

So $F(x)$ is the probability that a *single* random variable $X$ is smaller than $x$, and $F_{n}(x)$ is the *average number* of random variables that are smaller than $x$.

Then

$\Pr \left(\sup _{x\in \mathbb {R} }{\bigl (}F_{n}(x)-F(x){\bigr )}>\varepsilon \right)\leq e^{-2n\varepsilon ^{2}}{\text{ for every }}\varepsilon \geq {\sqrt {{\tfrac {1}{2n}}\ln 2}}.$

## Anti-concentration inequalities

**Anti-concentration inequalities**, on the other hand, provide an *upper bound* on how much a random variable can concentrate, either on a specific value or range of values. A concrete example is that if you flip a fair coin $n$ times, the probability that any given number of heads appears will be less than ${\frac {1}{\sqrt {n}}}$. This idea can be greatly generalized. For example, a result of Rao and Yehudayoff implies that for any $\beta ,\delta >0$ there exists some $C>0$ such that, for any $k$, the following is true for at least $2^{n(1-\delta )}$ values of $x\in \{\pm 1\}^{n}$:

$\Pr \left(\langle x,Y\rangle =k\right)\leq {\frac {C}{\sqrt {n}}},$

where $Y$ is drawn uniformly from $\{\pm 1\}^{n}$.

Such inequalities are of importance in several fields, including [communication complexity](https://en.wikipedia.org/wiki/Communication_complexity) (*e.g.*, in proofs of the [gap Hamming problem](https://en.wikipedia.org/wiki/Gap-Hamming_problem)) and [graph theory](https://en.wikipedia.org/wiki/Graph_theory).

An interesting anti-concentration inequality for weighted sums of independent [Rademacher](https://en.wikipedia.org/wiki/Rademacher_distribution) random variables can be obtained using the [Paley–Zygmund](https://en.wikipedia.org/wiki/Paley%E2%80%93Zygmund_inequality) and the [Khintchine](https://en.wikipedia.org/wiki/Khintchine_inequality) inequalities.

## References

1.  [Pukelsheim, F., 1994. The Three Sigma Rule. The American Statistician, 48(2), pp. 88–91](https://www.jstor.org/stable/pdf/2684253.pdf)
2.  Mercadier, Mathieu; Strobel, Frank (2021-11-16). ["A one-sided Vysochanskii–Petunin inequality with financial applications"](https://www.sciencedirect.com/science/article/pii/S0377221721001545). *European Journal of Operational Research*. **295** (1): 374–377. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.ejor.2021.02.041](https://doi.org/10.1016%2Fj.ejor.2021.02.041). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0377-2217](https://search.worldcat.org/issn/0377-2217).
3.  [Mitzenmacher, Michael](https://en.wikipedia.org/wiki/Michael_Mitzenmacher); [Upfal, Eli](https://en.wikipedia.org/wiki/Eli_Upfal) (2005). [Probability and Computing: Randomized Algorithms and Probabilistic Analysis](https://books.google.com/books?id=0bAYl6d7hvkC). Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-83540-2](https://en.wikipedia.org/wiki/Special:BookSources/0-521-83540-2).
4.  Slagle, N.P. (2012). "One Hundred Statistics and Probability Inequalities". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2102.07234](https://arxiv.org/abs/2102.07234).
5.  Addison Hu. ["Mill's Inequality"](http://huisaddison.com/blog/mills-inequality.html). *Addison Hu*. Retrieved 2025-05-14.
6.  Fan, X.; Grama, I.; Liu, Q. (2015). ["Exponential inequalities for martingales with applications"](http://projecteuclid.org/euclid.ejp/1465067107). *Electronic Journal of Probability*. **20**. Electron. J. Probab. 20: 1–22. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1311.6273](https://arxiv.org/abs/1311.6273). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/EJP.v20-3496](https://doi.org/10.1214%2FEJP.v20-3496).
7.  [Chung, Fan](https://en.wikipedia.org/wiki/Fan_Chung); Lu, Linyuan (2010). ["Old and new concentration inequalities"](http://www.math.ucsd.edu/~fan/complex/ch2.pdf) (PDF). *Complex Graphs and Networks*. [American Mathematical Society](https://en.wikipedia.org/wiki/American_Mathematical_Society). Retrieved August 14, 2018.
8.  Boucheron, Stéphane; Lugosi, Gábor; Bousquet, Olivier (2004). "Concentration inequalities". *Advanced Lectures on Machine Learning: ML Summer Schools 2003, Canberra, Australia, February 2–14, 2003, Tübingen, Germany, August 4–16, 2003, Revised Lectures*. Springer: 208–240.
9.  Bretagnolle, Jean; Huber-Carol, Catherine (1978). "Lois empiriques et distance de Prokhorov". [Séminaire de Probabilités XII](http://www.numdam.org/item/SPS_1978__12__332_0/). Lecture Notes in Mathematics. Vol. 649. pp. 332–341. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/BFb0064609](https://doi.org/10.1007%2FBFb0064609). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-08761-8](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-08761-8).
10. [van der Vaart, A.W.](https://en.wikipedia.org/wiki/Aad_van_der_Vaart); [Wellner, J.A.](https://en.wikipedia.org/wiki/Jon_A._Wellner) (1996). *Weak convergence and empirical processes: With applications to statistics*. Springer Science & Business Media.
11. Yuto Ushioda; Masato Tanaka; Tomomi Matsui (2022). ["Monte Carlo Methods for the Shapley–Shubik Power Index"](https://doi.org/10.3390%2Fg13030044). *Games*. **13** (3): 44. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2101.02841](https://arxiv.org/abs/2101.02841). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3390/g13030044](https://doi.org/10.3390%2Fg13030044).
12. Mason, David M.; [Willem R. Van Zwet](https://en.wikipedia.org/wiki/Willem_van_Zwet) (1987). ["A Refinement of the KMT Inequality for the Uniform Empirical Process"](https://doi.org/10.1214%2Faop%2F1176992070). *The Annals of Probability*. **15** (3): 871–884. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/aop/1176992070](https://doi.org/10.1214%2Faop%2F1176992070).
13. Rao, Anup; Yehudayoff, Amir (2018). ["Anti-concentration in most directions"](https://eccc.weizmann.ac.il/report/2018/194/). Electronic Colloquium on Computational Complexity.
14. Sherstov, Alexander A. (2012). ["The Communication Complexity of Gap Hamming Distance"](https://theoryofcomputing.org/articles/v008a008/). [Theory of Computing](https://en.wikipedia.org/wiki/Theory_of_Computing).
15. Matthew Kwan; [Benny Sudakov](https://en.wikipedia.org/wiki/Benny_Sudakov); Tuan Tran (2018). "Anticoncentration for subgraph statistics". *Journal of the London Mathematical Society*. **99** (3): 757–777. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1807.05202](https://arxiv.org/abs/1807.05202). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2018arXiv180705202K](https://ui.adsabs.harvard.edu/abs/2018arXiv180705202K). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1112/jlms.12192](https://doi.org/10.1112%2Fjlms.12192). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [54065186](https://api.semanticscholar.org/CorpusID:54065186).
16. Veraar, Mark (2009). "On Khintchine inequalities with a weight". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[0909.2586v1](https://arxiv.org/abs/0909.2586v1) \[[math.PR](https://arxiv.org/archive/math.PR)\].

## External links

- Karthik Sridharan, "[A Gentle Introduction to Concentration Inequalities](https://www.cs.cornell.edu/~sridharan/concentration.pdf)"  —[Cornell University](https://en.wikipedia.org/wiki/Cornell_University)
