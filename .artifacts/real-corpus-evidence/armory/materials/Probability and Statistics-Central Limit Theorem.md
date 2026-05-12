[[probability-statistics.base]]

> Source: [[Central Limit Theorem]]
> License: Wikipedia content is available under CC BY-SA 4.0.

<table class="infobox vcard">
<caption>Central Limit Theorem</caption>

![[media/e96889139166451ad5454d64302441b4d71be693.png]]

Type
[Theorem](https://en.wikipedia.org/wiki/Theorem)

Field
[Probability theory](https://en.wikipedia.org/wiki/Probability_theory)

Statement
The scaled sum of a sequence of [i.i.d. random variables](https://en.wikipedia.org/wiki/Independent_and_identically_distributed_random_variables) with finite positive [variance](https://en.wikipedia.org/wiki/Variance) converges in distribution to the [normal distribution](https://en.wikipedia.org/wiki/Normal_distribution).

Generalizations
[Lindeberg's CLT](https://en.wikipedia.org/wiki/Lindeberg%27s_condition)

</table>

In [probability theory](https://en.wikipedia.org/wiki/Probability_theory), the **central limit theorem** (**CLT**) states that, under appropriate conditions, the [distribution](https://en.wikipedia.org/wiki/Probability_distribution) of a normalized version of the sample mean converges to a [standard normal distribution](https://en.wikipedia.org/wiki/Normal_distribution#Standard_normal_distribution). This holds even if the original variables themselves are not [normally distributed](https://en.wikipedia.org/wiki/Normal_distribution). There are several versions of the CLT, each applying in the context of different conditions.

The theorem is a key concept in probability theory because it implies that probabilistic and statistical methods that work for normal distributions can be applicable to many problems involving other types of distributions.

This theorem has seen many changes during the formal development of probability theory. Previous versions of the theorem date back to 1811, but in its modern form it was only precisely stated in the 1920s.

In [statistics](https://en.wikipedia.org/wiki/Statistics), the CLT can be stated as: let $X_{1},X_{2},\dots ,X_{n}$ denote a [statistical sample](https://en.wikipedia.org/wiki/Sampling_(statistics) "Sampling (statistics)") of size $n$ from a population with [expected value](https://en.wikipedia.org/wiki/Expected_value) (average) $\mu$ and finite positive [variance](https://en.wikipedia.org/wiki/Variance) $\sigma ^{2}$, and let ${\bar {X}}_{n}$ denote the sample mean (which is itself a [random variable](https://en.wikipedia.org/wiki/Random_variable)). Then the [limit as $n\to \infty$ of the distribution](https://en.wikipedia.org/wiki/Convergence_of_random_variables#Convergence_in_distribution) of $({\bar {X}}_{n}-\mu ){\sqrt {n}}$ is a normal distribution with mean $0$ and variance $\sigma ^{2}$.

In other words, suppose that a large sample of [observations](https://en.wikipedia.org/wiki/Random_variate) is obtained, each observation being randomly produced in a way that does not depend on the values of the other observations, and the average ([arithmetic mean](https://en.wikipedia.org/wiki/Arithmetic_mean)) of the observed values is computed. If this procedure is performed many times, resulting in a collection of observed averages, the central limit theorem says that if the sample size is large enough, the [probability distribution](https://en.wikipedia.org/wiki/Probability_distribution) of these averages will closely approximate a normal distribution.

The central limit theorem has several variants. In its common form, the random variables must be [independent and identically distributed](https://en.wikipedia.org/wiki/Independent_and_identically_distributed) (i.i.d.). This requirement can be weakened; convergence of the mean to the normal distribution also occurs for non-identical distributions or for non-independent observations if they comply with certain conditions.

The earliest version of this theorem, that the normal distribution may be used as an approximation to the [binomial distribution](https://en.wikipedia.org/wiki/Binomial_distribution), is the [de Moivre–Laplace theorem](https://en.wikipedia.org/wiki/De_Moivre%E2%80%93Laplace_theorem).

## Independent sequences

![[media/54e5c78d727f04e7184a9138b6b9a6102dab7c70.png]]
Whatever the form of the population distribution, the sampling distribution tends to a Gaussian, and its dispersion is given by the central limit theorem.

### Classical CLT

Let $\{X_{1},\ldots ,X_{n}}\$ be a sequence of [i.i.d. random variables](https://en.wikipedia.org/wiki/Independent_and_identically_distributed_random_variables) having a distribution with [expected value](https://en.wikipedia.org/wiki/Expected_value) given by $\mu$ and finite [variance](https://en.wikipedia.org/wiki/Variance) given by $\sigma ^{2}.$ Suppose we are interested in the [sample average](https://en.wikipedia.org/wiki/Sample_mean)

$$
{\bar {X}}_{n}\equiv {\frac {X_{1}+\cdots +X_{n}}{n}}.
$$

By the [[Law of Large Numbers]], the sample average [converges almost surely](https://en.wikipedia.org/wiki/Almost_sure_convergence) (and therefore also [converges in probability](https://en.wikipedia.org/wiki/Convergence_in_probability)) to the expected value $\mu$ as $n\to \infty .$

The classical central limit theorem describes the size and the distributional form of the [stochastic](https://en.wiktionary.org/wiki/stochastic) fluctuations around the deterministic number $\mu$ during this convergence. More precisely, it states that as $n$ gets larger, the distribution of the normalized mean ${\sqrt {n}}({\bar {X}}_{n}-\mu )$, i.e. the difference between the sample average ${\bar {X}}_{n}$ and its limit $\mu ,$ scaled by the factor ${\sqrt {n}}$, approaches the [normal distribution](https://en.wikipedia.org/wiki/Normal_distribution) with mean $0$ and variance $\sigma ^{2}.$ For large enough $n,$ the distribution of ${\bar {X}}_{n}$ gets arbitrarily close to the normal distribution with mean $\mu$ and variance $\sigma ^{2}/n.$

The usefulness of the theorem is that the distribution of ${\sqrt {n}}({\bar {X}}_{n}-\mu )$ approaches normality regardless of the shape of the distribution of the individual $X_{i}.$ Formally, the theorem can be stated as follows:

**Lindeberg–Lévy CLT**—Suppose $X_{1},X_{2},X_{3}\ldots$ is a sequence of [i.i.d.](https://en.wikipedia.org/wiki/Independent_and_identically_distributed) random variables with $\operatorname {E} [X_{i}]=\mu$ and $\operatorname {Var} [X_{i}]=\sigma ^{2}<\infty .$ Then, as $n$ approaches infinity, the random variables ${\sqrt {n}}({\bar {X}}_{n}-\mu )$ [converge in distribution](https://en.wikipedia.org/wiki/Convergence_in_distribution) to a [normal](https://en.wikipedia.org/wiki/Normal_distribution) ${\mathcal {N}}(0,\sigma ^{2})$:

$$
{\sqrt {n}}\left({\bar {X}}_{n}-\mu \right)\mathrel {\overset {d}{\longrightarrow }} {\mathcal {N}}\left(0,\sigma ^{2}\right).
$$

In the case $\sigma >0,$ convergence in distribution means that the [[Cumulative Distribution Function|cumulative distribution functions]] of ${\sqrt {n}}({\bar {X}}_{n}-\mu )$ converge pointwise to the cdf of the ${\mathcal {N}}(0,\sigma ^{2})$ distribution: for every real number $z,$

$$
\lim _{n\to \infty }\mathbb {P} \left[{\sqrt {n}}({\bar {X}}_{n}-\mu )\leq z\right]=\lim _{n\to \infty }\mathbb {P} \left[{\frac {{\sqrt {n}}({\bar {X}}_{n}-\mu )}{\sigma }}\leq {\frac {z}{\sigma }}\right]=\Phi \left({\frac {z}{\sigma }}\right),
$$

where $\Phi (z)$ is the standard normal cdf evaluated at $z.$ The convergence is uniform in $z$ in the sense that

$$
\lim _{n\to \infty }\;\sup _{z\in \mathbb {R} }\;\left|\mathbb {P} \left[{\sqrt {n}}({\bar {X}}_{n}-\mu )\leq z\right]-\Phi \left({\frac {z}{\sigma }}\right)\right|=0~,
$$

where $\sup$ denotes the least upper bound (or [supremum](https://en.wikipedia.org/wiki/Supremum)) of the set.

### Lyapunov CLT

In this variant of the central limit theorem the random variables $X_{i}$ have to be independent, but not necessarily identically distributed. The theorem also requires that random variables $\left|X_{i}\right|$ have [moments](https://en.wikipedia.org/wiki/Moment_(mathematics) "Moment (mathematics)") of some order $(2+\delta )$, and that the rate of growth of these moments is limited by the Lyapunov condition given below.

**Lyapunov CLT**—Suppose $\{X_{1},\ldots ,X_{n},\ldots \}$ is a sequence of independent random variables, each with finite expected value $\mu _{i}$ and variance $\sigma _{i}^{2}$. Define

$$
s_{n}^{2}=\sum _{i=1}^{n}\sigma _{i}^{2}.
$$

If for some $\delta >0$, *Lyapunov’s condition*

$$
\lim _{n\to \infty }\;{\frac {1}{s_{n}^{2+\delta }}}\,\sum _{i=1}^{n}\operatorname {E} \left[\left|X_{i}-\mu _{i}\right|^{2+\delta }\right]=0
$$

is satisfied, then a sum of ${\frac {X_{i}-\mu _{i}}{s_{n}}}$ converges in distribution to a standard normal random variable, as $n$ goes to infinity:

$$
{\frac {1}{s_{n}}}\,\sum _{i=1}^{n}\left(X_{i}-\mu _{i}\right)\mathrel {\overset {d}{\longrightarrow }} {\mathcal {N}}(0,1).
$$

In practice it is usually easiest to check Lyapunov's condition for $\delta =1$.

If a sequence of random variables satisfies Lyapunov's condition, then it also satisfies Lindeberg's condition. The converse implication, however, does not hold.

### Lindeberg (-Feller) CLT

In the same setting and with the same notation as above, the Lyapunov condition can be replaced with the following weaker one (from [Lindeberg](https://en.wikipedia.org/wiki/Jarl_Waldemar_Lindeberg) in 1920).

Suppose that for every $\varepsilon >0$,

$$
\lim _{n\to \infty }{\frac {1}{s_{n}^{2}}}\sum _{i=1}^{n}\operatorname {E} \left[(X_{i}-\mu _{i})^{2}\cdot \mathbf {1} _{\left\{\left|X_{i}-\mu _{i}\right|>\varepsilon s_{n}\right\}}\right]=0
$$

where $\mathbf {1} _{\{\ldots \}}$ is the [indicator function](https://en.wikipedia.org/wiki/Indicator_function). Then the distribution of the standardized sums

$$
{\frac {1}{s_{n}}}\sum _{i=1}^{n}\left(X_{i}-\mu _{i}\right)
$$

converges towards the standard normal distribution ${\mathcal {N}}(0,1)$.

### CLT for the sum of a random number of random variables

Rather than summing an integer number $n$ of random variables and taking $n\to \infty$, the sum can be of a random number $N$ of random variables, with conditions on $N$. For example, the following theorem is Corollary 4 of Robbins (1948). It assumes that $N$ is asymptotically normal (Robbins also developed other conditions that lead to the same result).

**Robbins CLT**—Let $\{X_{i},i\geq 1\}$ be independent, identically distributed random variables with $E(X_{i})=\mu$ and ${\text{Var}}(X_{i})=\sigma ^{2}$, and let $\{N_{n},n\geq 1\}$ be a sequence of non-negative integer-valued random variables that are independent of $\{X_{i},i\geq 1\}$. Assume for each $n=1,2,\dots$ that $E(N_{n}^{2})<\infty$ and

$$
{\frac {N_{n}-E(N_{n})}{\sqrt {{\text{Var}}(N_{n})}}}\xrightarrow {\quad d\quad } {\mathcal {N}}(0,1)
$$

where $\xrightarrow {\,d\,}$ denotes convergence in distribution and ${\mathcal {N}}(0,1)$ is the normal distribution with mean 0, variance 1. Then

$$
{\frac {\sum _{i=1}^{N_{n}}X_{i}-\mu E(N_{n})}{\sqrt {\sigma ^{2}E(N_{n})+\mu ^{2}{\text{Var}}(N_{n})}}}\xrightarrow {\quad d\quad } {\mathcal {N}}(0,1)
$$

### Multidimensional CLT

Proofs that use characteristic functions can be extended to cases where each individual $\mathbf {X} _{i}$ is a [random vector](https://en.wikipedia.org/wiki/Random_vector) in $\mathbb {R} ^{k}$, with mean vector ${\boldsymbol {\mu }}=\operatorname {E} [\mathbf {X} _{i}]$ and [covariance matrix](https://en.wikipedia.org/wiki/Covariance_matrix) $\mathbf {\Sigma }$ (among the components of the vector), and these random vectors are independent and identically distributed. The multidimensional central limit theorem states that when scaled, sums converge to a [[Multivariate Normal Distribution]]. Summation of these vectors is done component-wise.

For $i=1,2,3,\ldots ,$ let

$$
\mathbf {X} _{i}={\begin{bmatrix}X_{i}^{(1)}\\\vdots \\X_{i}^{(k)}\end{bmatrix}}
$$

be independent random vectors. The sum of the random vectors $\mathbf {X} _{1},\ldots ,\mathbf {X} _{n}$ is

$$
\sum _{i=1}^{n}\mathbf {X} _{i}={\begin{bmatrix}X_{1}^{(1)}\\\vdots \\X_{1}^{(k)}\end{bmatrix}}+{\begin{bmatrix}X_{2}^{(1)}\\\vdots \\X_{2}^{(k)}\end{bmatrix}}+\cdots +{\begin{bmatrix}X_{n}^{(1)}\\\vdots \\X_{n}^{(k)}\end{bmatrix}}={\begin{bmatrix}\sum _{i=1}^{n}X_{i}^{(1)}\\\vdots \\\sum _{i=1}^{n}X_{i}^{(k)}\end{bmatrix}}
$$

and their average is

$$
\mathbf {{\bar {X}}_{n}} ={\begin{bmatrix}{\bar {X}}_{i}^{(1)}\\\vdots \\{\bar {X}}_{i}^{(k)}\end{bmatrix}}={\frac {1}{n}}\sum _{i=1}^{n}\mathbf {X} _{i}.
$$

Therefore,

$$
{\frac {1}{\sqrt {n}}}\sum _{i=1}^{n}\left[\mathbf {X} _{i}-\operatorname {E} \left(\mathbf {X} _{i}\right)\right]={\frac {1}{\sqrt {n}}}\sum _{i=1}^{n}(\mathbf {X} _{i}-{\boldsymbol {\mu }})={\sqrt {n}}\left({\overline {\mathbf {X} }}_{n}-{\boldsymbol {\mu }}\right).
$$

The multivariate central limit theorem states that

$$
{\sqrt {n}}\left({\overline {\mathbf {X} }}_{n}-{\boldsymbol {\mu }}\right)\mathrel {\overset {d}{\longrightarrow }} {\mathcal {N}}_{k}(0,{\boldsymbol {\Sigma }}),
$$

 where the [covariance matrix](https://en.wikipedia.org/wiki/Covariance_matrix) ${\boldsymbol {\Sigma }}$ is equal to 

$$
{\boldsymbol {\Sigma }}={\begin{bmatrix}{\operatorname {Var} \left(X_{1}^{(1)}\right)}&\operatorname {Cov} \left(X_{1}^{(1)},X_{1}^{(2)}\right)&\operatorname {Cov} \left(X_{1}^{(1)},X_{1}^{(3)}\right)&\cdots &\operatorname {Cov} \left(X_{1}^{(1)},X_{1}^{(k)}\right)\\\operatorname {Cov} \left(X_{1}^{(2)},X_{1}^{(1)}\right)&\operatorname {Var} \left(X_{1}^{(2)}\right)&\operatorname {Cov} \left(X_{1}^{(2)},X_{1}^{(3)}\right)&\cdots &\operatorname {Cov} \left(X_{1}^{(2)},X_{1}^{(k)}\right)\\\operatorname {Cov} \left(X_{1}^{(3)},X_{1}^{(1)}\right)&\operatorname {Cov} \left(X_{1}^{(3)},X_{1}^{(2)}\right)&\operatorname {Var} \left(X_{1}^{(3)}\right)&\cdots &\operatorname {Cov} \left(X_{1}^{(3)},X_{1}^{(k)}\right)\\\vdots &\vdots &\vdots &\ddots &\vdots \\\operatorname {Cov} \left(X_{1}^{(k)},X_{1}^{(1)}\right)&\operatorname {Cov} \left(X_{1}^{(k)},X_{1}^{(2)}\right)&\operatorname {Cov} \left(X_{1}^{(k)},X_{1}^{(3)}\right)&\cdots &\operatorname {Var} \left(X_{1}^{(k)}\right)\\\end{bmatrix}}~.
$$

The multivariate central limit theorem can be proved using the [Cramér–Wold theorem](https://en.wikipedia.org/wiki/Cram%C3%A9r%E2%80%93Wold_theorem).

The rate of convergence is given by the following [Berry–Esseen](https://en.wikipedia.org/wiki/Berry%E2%80%93Esseen_theorem) type result:

**Theorem**—Let $X_{1},\dots ,X_{n},\dots$ be independent $\mathbb {R} ^{d}$-valued random vectors, each having mean zero. Write $S=\sum _{i=1}^{n}X_{i}$ and assume $\Sigma =\operatorname {Cov} [S]$ is invertible. Let $Z\sim {\mathcal {N}}(0,\Sigma )$ be a $d$-dimensional Gaussian with the same mean and same covariance matrix as $S$. Then for all convex sets $U\subseteq \mathbb {R} ^{d}$,

$$
\left|\mathbb {P} [S\in U]-\mathbb {P} [Z\in U]\right|\leq C\,d^{1/4}\gamma ~,
$$

 where $C$ is a universal constant, $\gamma =\sum _{i=1}^{n}\operatorname {E} \left[\left\|\Sigma ^{-1/2}X_{i}\right\|_{2}^{3}\right]$, and $\|\cdot \|_{2}$ denotes the Euclidean norm on $\mathbb {R} ^{d}$.

It is unknown whether the factor $d^{1/4}$ is necessary.

## The generalized central limit theorem

The generalized central limit theorem (GCLT) was an effort of multiple mathematicians ([Sergei Bernstein](https://en.wikipedia.org/wiki/Sergei_Bernstein), [Jarl Waldemar Lindeberg](https://en.wikipedia.org/wiki/Jarl_Waldemar_Lindeberg), [Paul Lévy](https://en.wikipedia.org/wiki/Paul_L%C3%A9vy_(mathematician) "Paul Lévy (mathematician)"), [William Feller](https://en.wikipedia.org/wiki/William_Feller), [Andrey Kolmogorov](https://en.wikipedia.org/wiki/Andrey_Kolmogorov), and others) over the period from 1920 to 1937. The first published complete proof of the GCLT was in 1937 by Paul Lévy in French. An English language version of the complete proof of the GCLT is available in the translation of [Boris Vladimirovich Gnedenko](https://en.wikipedia.org/wiki/Boris_Vladimirovich_Gnedenko) and Kolmogorov's 1954 book.

The statement of the GCLT is as follows:

**Statement of GCLT**—A non-degenerate random variable Z is [α-stable](https://en.wikipedia.org/wiki/Stable_distribution) for some 0 \< *α* ≤ 2 if and only if there is an independent, identically distributed sequence of random variables *X*<sub>1</sub>, *X*<sub>2</sub>, *X*<sub>3</sub>, ..., and constants *a*<sub>*n*</sub> \> 0, *b*<sub>*n*</sub> ∈ ℝ with 

$$
a_{n}(X_{1}+\dots +X_{n})-b_{n}\to Z.
$$

 Here, '→' means the sequence of random variable sums converges in distribution; i.e., the corresponding distributions satisfy *F*<sub>*n*</sub>(*y*) → *F*(*y*) at all continuity points of F.

In other words, if sums of independent, identically distributed random variables converge in distribution to some Z, then Z must be a [stable distribution](https://en.wikipedia.org/wiki/Stable_distribution).

## Dependent processes

### CLT under weak dependence

A useful generalization of a sequence of independent, identically distributed random variables is a [mixing](https://en.wikipedia.org/wiki/Mixing_(mathematics) "Mixing (mathematics)") random process in discrete time; "mixing" means, roughly, that random variables temporally far apart from one another are nearly independent. Several kinds of mixing are used in ergodic theory and probability theory. See especially [strong mixing](https://en.wikipedia.org/wiki/Mixing_(mathematics)#Mixing_in_stochastic_processes "Mixing (mathematics)") (also called α-mixing) defined by $\alpha (n)\to 0$ where $\alpha (n)$ is so-called [strong mixing coefficient](https://en.wikipedia.org/wiki/Mixing_(mathematics)#Mixing_in_stochastic_processes "Mixing (mathematics)").

A simplified formulation of the central limit theorem under strong mixing is:

**Theorem**—Suppose that $\{X_{1},\ldots ,X_{n},\ldots \}$ is stationary and $\alpha$-mixing with $\alpha _{n}=O\left(n^{-5}\right)$ and that $\operatorname {E} [X_{n}]=0$ and $\operatorname {E} [X_{n}^{12}]<\infty$. Denote $S_{n}=X_{1}+\cdots +X_{n}$, then the limit

$$
\sigma ^{2}=\lim _{n\rightarrow \infty }{\frac {\operatorname {E} \left(S_{n}^{2}\right)}{n}}
$$

exists, and if $\sigma \neq 0$ then ${\frac {S_{n}}{\sigma {\sqrt {n}}}}$ converges in distribution to ${\mathcal {N}}(0,1)$.

In fact,

$$
\sigma ^{2}=\operatorname {E} \left(X_{1}^{2}\right)+2\sum _{k=1}^{\infty }\operatorname {E} \left(X_{1}X_{1+k}\right),
$$

where the series converges absolutely.

The assumption $\sigma \neq 0$ cannot be omitted, since the asymptotic normality fails for $X_{n}=Y_{n}-Y_{n-1}$ where $Y_{n}$ are another [stationary sequence](https://en.wikipedia.org/wiki/Stationary_sequence).

There is a stronger version of the theorem: the assumption $\operatorname {E} \left[X_{n}^{12}\right]<\infty$ is replaced with $\operatorname {E} \left[{\left|X_{n}\right|}^{2+\delta }\right]<\infty$, and the assumption $\alpha _{n}=O\left(n^{-5}\right)$ is replaced with

$$
\sum _{n}\alpha _{n}^{\frac {\delta }{2(2+\delta )}}<\infty .
$$

Existence of such $\delta >0$ ensures the conclusion. For encyclopedic treatment of limit theorems under mixing conditions see ().

### Martingale difference CLT

**Theorem**—Let a [martingale](https://en.wikipedia.org/wiki/Martingale_(probability_theory) "Martingale (probability theory)") $M_{n}$ satisfy

- ${\frac {1}{n}}\sum _{k=1}^{n}\operatorname {E} \left[\left(M_{k}-M_{k-1}\right)^{2}\mid M_{1},\dots ,M_{k-1}\right]\to 1$ in probability as *n* → ∞,
- for every *ε* \> 0, ${\frac {1}{n}}\sum _{k=1}^{n}{\operatorname {E} \left[\left(M_{k}-M_{k-1}\right)^{2}\mathbf {1} \left[|M_{k}-M_{k-1}|>\varepsilon {\sqrt {n}}\right]\right]}\to 0$ as *n* → ∞,

then ${\frac {M_{n}}{\sqrt {n}}}$ converges in distribution to ${\mathcal {N}}(0,1)$ as $n\to \infty$.

## Remarks

### Proof of classical CLT

The central limit theorem has a proof using [characteristic functions](https://en.wikipedia.org/wiki/Characteristic_function_(probability_theory) "Characteristic function (probability theory)"). It is similar to the proof of the (weak) [law of large numbers](https://en.wikipedia.org/wiki/Proof_of_the_law_of_large_numbers).

Assume $\{X_{1},\ldots ,X_{n},\ldots \}$ are independent and identically distributed random variables, each with mean $\mu$ and finite variance $\sigma ^{2}$. The sum $X_{1}+\cdots +X_{n}$ has [mean](https://en.wikipedia.org/wiki/Linearity_of_expectation) $n\mu$ and [variance](https://en.wikipedia.org/wiki/Variance#Sum_of_uncorrelated_variables_(Bienaymé_formula) "Variance") $n\sigma ^{2}$. Consider the random variable

$$
Z_{n}={\frac {X_{1}+\cdots +X_{n}-n\mu }{\sqrt {n\sigma ^{2}}}}=\sum _{i=1}^{n}{\frac {X_{i}-\mu }{\sqrt {n\sigma ^{2}}}}=\sum _{i=1}^{n}{\frac {1}{\sqrt {n}}}Y_{i},
$$

where in the last step we defined the new random variables $Y_{i}={\frac {X_{i}-\mu }{\sigma }}$, each with zero mean and unit variance ($\operatorname {var} (Y)=1$). The [characteristic function](https://en.wikipedia.org/wiki/Characteristic_function_(probability_theory) "Characteristic function (probability theory)") of $Z_{n}$ is given by

$$
{\begin{aligned}\varphi _{Z_{n}}\!(t)=\varphi _{\sum _{i=1}^{n}{{\frac {1}{\sqrt {n}}}Y_{i}}}\!(t)\ &=\ \varphi _{Y_{1}}\!\!\left({\frac {t}{\sqrt {n}}}\right)\varphi _{Y_{2}}\!\!\left({\frac {t}{\sqrt {n}}}\right)\cdots \varphi _{Y_{n}}\!\!\left({\frac {t}{\sqrt {n}}}\right)\\[1ex]&=\ \left[\varphi _{Y_{1}}\!\!\left({\frac {t}{\sqrt {n}}}\right)\right]^{n},\end{aligned}}
$$

where in the last step we used the fact that all of the $Y_{i}$ are identically distributed. The characteristic function of $Y_{1}$ is, by [Taylor's theorem](https://en.wikipedia.org/wiki/Taylor%27s_theorem), 

$$
\varphi _{Y_{1}}\!\left({\frac {t}{\sqrt {n}}}\right)=1-{\frac {t^{2}}{2n}}+o\!\left({\frac {t^{2}}{n}}\right),\quad \left({\frac {t}{\sqrt {n}}}\right)\to 0
$$

where $o(t^{2}/n)$ is "[little o notation](https://en.wikipedia.org/wiki/Little-o_notation)" for some function of $t$ that goes to zero more rapidly than $t^{2}/n$. By the limit of the [exponential function](https://en.wikipedia.org/wiki/Exponential_function) ($e^{x}=\lim _{n\to \infty }\left(1+{\frac {x}{n}}\right)^{n}$), the characteristic function of $Z_{n}$ equals

$$
\varphi _{Z_{n}}(t)=\left(1-{\frac {t^{2}}{2n}}+o\left({\frac {t^{2}}{n}}\right)\right)^{n}\rightarrow e^{-{\frac {1}{2}}t^{2}},\quad n\to \infty .
$$

All of the higher order terms vanish in the limit $n\to \infty$. The right hand side equals the characteristic function of a standard normal distribution ${\mathcal {N}}(0,1)$, which implies through [Lévy's continuity theorem](https://en.wikipedia.org/wiki/L%C3%A9vy_continuity_theorem) that the distribution of $Z_{n}$ will approach ${\mathcal {N}}(0,1)$ as $n\to \infty$. Therefore, the [sample average](https://en.wikipedia.org/wiki/Sample_mean)

$$
{\bar {X}}_{n}={\frac {X_{1}+\cdots +X_{n}}{n}}
$$

is such that

$$
{\frac {\sqrt {n}}{\sigma }}\left({\bar {X}}_{n}-\mu \right)=Z_{n}
$$

converges to the normal distribution ${\mathcal {N}}(0,1)$, from which the central limit theorem follows.

### Convergence to the limit

The central limit theorem gives only an [asymptotic distribution](https://en.wikipedia.org/wiki/Asymptotic_distribution). As an approximation for a finite number of observations, it provides a reasonable approximation only when close to the peak of the normal distribution; it requires a very large number of observations to stretch into the tails.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

The convergence in the central limit theorem is [uniform](https://en.wikipedia.org/wiki/Uniform_convergence) because the limiting cumulative distribution function is continuous. If the third central [moment](https://en.wikipedia.org/wiki/Moment_(mathematics) "Moment (mathematics)") $\operatorname {E} \left[(X_{1}-\mu )^{3}\right]$ exists and is finite, then the speed of convergence is at least on the order of $1/{\sqrt {n}}$ (see [Berry–Esseen theorem](https://en.wikipedia.org/wiki/Berry%E2%80%93Esseen_theorem)). [Stein's method](https://en.wikipedia.org/wiki/Stein%27s_method) can be used not only to prove the central limit theorem, but also to provide bounds on the rates of convergence for selected metrics.

The convergence to the normal distribution is monotonic, in the sense that the [entropy](https://en.wikipedia.org/wiki/Information_entropy) of $Z_{n}$ increases [monotonically](https://en.wikipedia.org/wiki/Monotonic_function) to that of the normal distribution.

The central limit theorem applies in particular to sums of independent and identically distributed [discrete random variables](https://en.wikipedia.org/wiki/Discrete_random_variable). A sum of [discrete random variables](https://en.wikipedia.org/wiki/Discrete_random_variable) is still a [discrete random variable](https://en.wikipedia.org/wiki/Discrete_random_variable), so that we are confronted with a sequence of [discrete random variables](https://en.wikipedia.org/wiki/Discrete_random_variable) whose cumulative probability distribution function converges towards a cumulative probability distribution function corresponding to a continuous variable (namely that of the [normal distribution](https://en.wikipedia.org/wiki/Normal_distribution)). This means that if we build a [histogram](https://en.wikipedia.org/wiki/Histogram) of the realizations of the sum of n independent identical discrete variables, the piecewise-linear curve that joins the centers of the upper faces of the rectangles forming the histogram converges toward a Gaussian curve as n approaches infinity; this relation is known as [de Moivre–Laplace theorem](https://en.wikipedia.org/wiki/De_Moivre%E2%80%93Laplace_theorem). The [binomial distribution](https://en.wikipedia.org/wiki/Binomial_distribution) article details such an application of the central limit theorem in the simple case of a discrete variable taking only two possible values.

### Common misconceptions

Studies have shown that the central limit theorem is subject to several common but serious misconceptions, some of which appear in widely used textbooks. These include:

- The misconceived belief that the theorem applies to random sampling of any variable, rather than to the mean values (or sums) of [iid](https://en.wikipedia.org/wiki/Iid) random variables extracted from a population by repeated sampling. That is, the theorem assumes the random sampling produces a [sampling distribution](https://en.wikipedia.org/wiki/Sampling_distribution) formed from different values of means (or sums) of such random variables.
- The misconceived belief that the theorem ensures that random sampling leads to the emergence of a normal distribution for sufficiently large samples of any random variable, regardless of the population distribution. In reality, such sampling asymptotically reproduces the properties of the population, an intuitive result underpinned by the [Glivenko–Cantelli theorem](https://en.wikipedia.org/wiki/Glivenko%E2%80%93Cantelli_theorem).
- The misconceived belief that the theorem leads to a good approximation of a normal distribution for sample sizes greater than around 30, allowing reliable inferences regardless of the nature of the population. In reality, this empirical rule of thumb has no valid justification, and can lead to seriously flawed inferences. See [Z-test](https://en.wikipedia.org/wiki/Z-test) for where the approximation holds.

### Relation to the law of large numbers

The [[Law of Large Numbers]] as well as the central limit theorem are partial solutions to a general problem: "What is the limiting behavior of S<sub>n</sub> as n approaches infinity?" In mathematical analysis, [asymptotic series](https://en.wikipedia.org/wiki/Asymptotic_series) are one of the most popular tools employed to approach such questions.

Suppose we have an asymptotic expansion of $f(n)$:

$$
f(n)=a_{1}\varphi _{1}(n)+a_{2}\varphi _{2}(n)+O{\big (}\varphi _{3}(n){\big )}\qquad (n\to \infty ).
$$

Dividing both parts by *φ*<sub>1</sub>(*n*) and taking the limit will produce *a*<sub>1</sub>, the coefficient of the highest-order term in the expansion, which represents the rate at which *f*(*n*) changes in its leading term.

$$
\lim _{n\to \infty }{\frac {f(n)}{\varphi _{1}(n)}}=a_{1}.
$$

Informally, one can say: "*f*(*n*) grows approximately as *a*<sub>1</sub>*φ*<sub>1</sub>(*n*)". Taking the difference between *f*(*n*) and its approximation and then dividing by the next term in the expansion, we arrive at a more refined statement about *f*(*n*):

$$
\lim _{n\to \infty }{\frac {f(n)-a_{1}\varphi _{1}(n)}{\varphi _{2}(n)}}=a_{2}.
$$

Here one can say that the difference between the function and its approximation grows approximately as *a*<sub>2</sub>*φ*<sub>2</sub>(*n*). The idea is that dividing the function by appropriate normalizing functions, and looking at the limiting behavior of the result, can tell us much about the limiting behavior of the original function itself.

Informally, something along these lines happens when the sum, S<sub>n</sub>, of independent identically distributed random variables, *X*<sub>1</sub>, ..., *X<sub>n</sub>*, is studied in classical probability theory.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup> If each X<sub>i</sub> has finite mean μ, then by the law of large numbers, *S<sub>n</sub>*/*n* → *μ*. If in addition each X<sub>i</sub> has finite variance *σ*<sup>2</sup>, then by the central limit theorem,

$$
{\frac {S_{n}-n\mu }{\sqrt {n}}}\to \xi ,
$$

where ξ is distributed as *N*(0,*σ*<sup>2</sup>). This provides values of the first two constants in the informal expansion

$$
S_{n}\approx \mu n+\xi {\sqrt {n}}.
$$

In the case where the X<sub>i</sub> do not have finite mean or variance, convergence of the shifted and rescaled sum can also occur with different centering and scaling factors:

$$
{\frac {S_{n}-a_{n}}{b_{n}}}\rightarrow \Xi ,
$$

or informally

$$
S_{n}\approx a_{n}+\Xi b_{n}.
$$

Distributions Ξ which can arise in this way are called *[stable](https://en.wikipedia.org/wiki/Stable_distribution)*. Clearly, the normal distribution is stable, but there are also other stable distributions, such as the [Cauchy distribution](https://en.wikipedia.org/wiki/Cauchy_distribution), for which the mean or variance are not defined. The scaling factor b<sub>n</sub> may be proportional to n<sup>c</sup>, for any *c* ≥ 1/2; it may also be multiplied by a [slowly varying function](https://en.wikipedia.org/wiki/Slowly_varying_function) of n.

The [law of the iterated logarithm](https://en.wikipedia.org/wiki/Law_of_the_iterated_logarithm) specifies what is happening "in between" the [[Law of Large Numbers]] and the central limit theorem. Specifically it says that the normalizing function √*n* log log *n*, intermediate in size between n of the law of large numbers and √*n* of the central limit theorem, provides a non-trivial limiting behavior.

### Alternative statements of the theorem

#### Density functions

The [[Probability Density Function|density]] of the sum of two or more independent variables is the [convolution](https://en.wikipedia.org/wiki/Convolution) of their densities (if these densities exist). Thus the central limit theorem can be interpreted as a statement about the properties of density functions under convolution: the convolution of a number of density functions tends to the normal density as the number of density functions increases without bound. These theorems require stronger hypotheses than the forms of the central limit theorem given above. Theorems of this type are often called local limit theorems. See Petrov for a particular local limit theorem for sums of [independent and identically distributed random variables](https://en.wikipedia.org/wiki/Independent_and_identically_distributed_random_variables).

#### Characteristic functions

Since the [characteristic function](https://en.wikipedia.org/wiki/Characteristic_function_(probability_theory) "Characteristic function (probability theory)") of a convolution is the product of the characteristic functions of the densities involved, the central limit theorem has yet another restatement: the product of the characteristic functions of a number of density functions becomes close to the characteristic function of the normal density as the number of density functions increases without bound, under the conditions stated above. Specifically, an appropriate scaling factor needs to be applied to the argument of the characteristic function.

An equivalent statement can be made about [Fourier transforms](https://en.wikipedia.org/wiki/Fourier_transform), since the characteristic function is essentially a Fourier transform.

### Calculating the variance

Let S<sub>n</sub> be the sum of n random variables. Many central limit theorems provide conditions such that S<sub>n</sub>/√Var(S<sub>n</sub>) converges in distribution to *N*(0,1) (the normal distribution with mean 0, variance 1) as n → ∞. In some cases, it is possible to find a constant *σ*<sup>2</sup> and function f(n) such that S<sub>n</sub>/(σ√n⋅f(n)) converges in distribution to *N*(0,1) as n→ ∞.

**Lemma**—Suppose $X_{1},X_{2},\dots$ is a sequence of real-valued and strictly stationary random variables with $\operatorname {E} (X_{i})=0$ for all $i$, $g:[0,1]\to \mathbb {R}$, and $S_{n}=\sum _{i=1}^{n}g\left({\tfrac {i}{n}}\right)X_{i}$. Construct

$$
\sigma ^{2}=\operatorname {E} (X_{1}^{2})+2\sum _{i=1}^{\infty }\operatorname {E} (X_{1}X_{1+i})
$$

1.  If $\sum _{i=1}^{\infty }\operatorname {E} (X_{1}X_{1+i})$ is absolutely convergent, $\left|\int _{0}^{1}g(x)g'(x)\,dx\right|<\infty$, and $0<\int _{0}^{1}(g(x))^{2}dx<\infty$ then $\mathrm {Var} (S_{n})/(n\gamma _{n})\to \sigma ^{2}$ as $n\to \infty$ where $\gamma _{n}={\frac {1}{n}}\sum _{i=1}^{n}\left(g\left({\tfrac {i}{n}}\right)\right)^{2}$.
2.  If in addition $\sigma >0$ and $S_{n}/{\sqrt {\mathrm {Var} (S_{n})}}$ converges in distribution to ${\mathcal {N}}(0,1)$ as $n\to \infty$ then $S_{n}/(\sigma {\sqrt {n\gamma _{n}}})$ also converges in distribution to ${\mathcal {N}}(0,1)$ as $n\to \infty$.

## Extensions

### Products of positive random variables

The [logarithm](https://en.wikipedia.org/wiki/Logarithm) of a product is simply the sum of the logarithms of the factors. Therefore, when the logarithm of a product of random variables that take only positive values approaches a normal distribution, the product itself approaches a [log-normal distribution](https://en.wikipedia.org/wiki/Log-normal_distribution). Many physical quantities (especially mass or length, which are a matter of scale and cannot be negative) are the products of different [random](https://en.wikipedia.org/wiki/Random) factors, so they follow a log-normal distribution. This multiplicative version of the central limit theorem is sometimes called [Gibrat's law](https://en.wikipedia.org/wiki/Gibrat%27s_law).

Whereas the central limit theorem for sums of random variables requires the condition of finite variance, the corresponding theorem for products requires the corresponding condition that the density function be square-integrable.

## Beyond the classical framework

Asymptotic normality, that is, [convergence](https://en.wikipedia.org/wiki/Convergence_in_distribution) to the normal distribution after appropriate shift and rescaling, is a phenomenon much more general than the classical framework treated above, namely, sums of independent random variables (or vectors). New frameworks are revealed from time to time; no single unifying framework is available for now.

### Convex body

**Theorem**—There exists a sequence *ε<sub>n</sub>* ↓ 0 for which the following holds. Let *n* ≥ 1, and let random variables *X*<sub>1</sub>, ..., *X<sub>n</sub>* have a [log-concave](https://en.wikipedia.org/wiki/Logarithmically_concave_function) [joint density](https://en.wikipedia.org/wiki/Joint_density_function) f such that *f*(*x*<sub>1</sub>, ..., *x<sub>n</sub>*) = *f*(\|*x*<sub>1</sub>\|, ..., \|*x<sub>n</sub>*\|) for all *x*<sub>1</sub>, ..., *x<sub>n</sub>*, and E(*X*<sup>2</sup>  
<sub>*k*</sub>) = 1 for all *k* = 1, ..., *n*. Then the distribution of

$$
{\frac {X_{1}+\cdots +X_{n}}{\sqrt {n}}}
$$

is ε<sub>n</sub>-close to ${\mathcal {N}}(0,1)$ in the [total variation distance](https://en.wikipedia.org/wiki/Total_variation_distance_of_probability_measures).

These two ε<sub>n</sub>-close distributions have densities (in fact, log-concave densities), thus, the total variance distance between them is the integral of the absolute value of the difference between the densities. Convergence in total variation is stronger than weak convergence.

An important example of a log-concave density is a function constant inside a given convex body and vanishing outside; it corresponds to the uniform distribution on the convex body, which explains the term "central limit theorem for convex bodies".

Another example: *f*(*x*<sub>1</sub>, ..., *x<sub>n</sub>*) = const · exp(−(\|*x*<sub>1</sub>\|<sup>*α*</sup> + ⋯ + \|*x<sub>n</sub>*\|<sup>*α*</sup>)<sup>*β*</sup>) where *α* \> 1 and *αβ* \> 1. If *β* = 1 then *f*(*x*<sub>1</sub>, ..., *x<sub>n</sub>*) factorizes into const · exp (−\|*x*<sub>1</sub>\|<sup>*α*</sup>) … exp(−\|*x<sub>n</sub>*\|<sup>*α*</sup>),  which means *X*<sub>1</sub>, ..., *X<sub>n</sub>* are independent. In general, however, they are dependent.

The condition *f*(*x*<sub>1</sub>, ..., *x<sub>n</sub>*) = *f*(\|*x*<sub>1</sub>\|, ..., \|*x<sub>n</sub>*\|) ensures that *X*<sub>1</sub>, ..., *X<sub>n</sub>* are of zero mean and [uncorrelated](https://en.wikipedia.org/wiki/Uncorrelated);<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup> still, they need not be independent, nor even [pairwise independent](https://en.wikipedia.org/wiki/Pairwise_independence).<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup> By the way, pairwise independence cannot replace independence in the classical central limit theorem.

Here is a [Berry–Esseen](https://en.wikipedia.org/wiki/Berry%E2%80%93Esseen_theorem) type result.

**Theorem**—Let *X*<sub>1</sub>, ..., *X<sub>n</sub>* satisfy the assumptions of the previous theorem, then

$$
\left|\mathbb {P} \left(a\leq {\frac {X_{1}+\cdots +X_{n}}{\sqrt {n}}}\leq b\right)-{\frac {1}{\sqrt {2\pi }}}\int _{a}^{b}e^{-{\frac {1}{2}}t^{2}}\,dt\right|\leq {\frac {C}{n}}
$$

for all *a* \< *b*; here C is a [universal (absolute) constant](https://en.wikipedia.org/wiki/Mathematical_constant). Moreover, for every *c*<sub>1</sub>, ..., *c<sub>n</sub>* ∈ **R** such that *c*<sup>2</sup>  
<sub>1</sub> + ⋯ + *c*<sup>2</sup>  
<sub>*n*</sub> = 1,

$$
\left|\mathbb {P} \left(a\leq c_{1}X_{1}+\cdots +c_{n}X_{n}\leq b\right)-{\frac {1}{\sqrt {2\pi }}}\int _{a}^{b}e^{-{\frac {1}{2}}t^{2}}\,dt\right|\leq C\left(c_{1}^{4}+\dots +c_{n}^{4}\right).
$$

The distribution of *X*<sub>1</sub> + ⋯ + *X<sub>n</sub>*/√*n* need not be approximately normal (in fact, it can be uniform). However, the distribution of *c*<sub>1</sub>*X*<sub>1</sub> + ⋯ + *c<sub>n</sub>X<sub>n</sub>* is close to ${\mathcal {N}}(0,1)$ (in the total variation distance) for most vectors (*c*<sub>1</sub>, ..., *c<sub>n</sub>*) according to the uniform distribution on the sphere *c*<sup>2</sup>  
<sub>1</sub> + ⋯ + *c*<sup>2</sup>  
<sub>*n*</sub> = 1.

### Lacunary trigonometric series

**Theorem ([Salem](https://en.wikipedia.org/wiki/Rapha%C3%ABl_Salem)–[Zygmund](https://en.wikipedia.org/wiki/Antoni_Zygmund))**—Let U be a random variable distributed uniformly on (0,2π), and *X<sub>k</sub>* = *r<sub>k</sub>* cos(*n<sub>k</sub>U* + *a<sub>k</sub>*), where

- n<sub>k</sub> satisfy the lacunarity condition: there exists *q* \> 1 such that *n*<sub>*k* + 1</sub> ≥ *qn*<sub>*k*</sub> for all k,
- r<sub>k</sub> are such that  

$$
r_{1}^{2}+r_{2}^{2}+\cdots =\infty \quad {\text{ and }}\quad {\frac {r_{k}^{2}}{r_{1}^{2}+\cdots +r_{k}^{2}}}\to 0,
$$

- 0 ≤ *a*<sub>*k*</sub> \< 2π.

Then

$$
{\frac {X_{1}+\cdots +X_{k}}{\sqrt {r_{1}^{2}+\cdots +r_{k}^{2}}}}
$$

converges in distribution to ${\mathcal {N}}{\big (}0,{\frac {1}{2}}{\big )}$.

### Gaussian polytopes

**Theorem**—Let *A*<sub>1</sub>, ..., *A*<sub>*n*</sub> be independent random points on the plane **R**<sup>2</sup> each having the two-dimensional standard normal distribution. Let K<sub>n</sub> be the [convex hull](https://en.wikipedia.org/wiki/Convex_hull) of these points, and X<sub>n</sub> the area of K<sub>n</sub> Then

$$
{\frac {X_{n}-\operatorname {E} (X_{n})}{\sqrt {\operatorname {Var} (X_{n})}}}
$$

 converges in distribution to ${\mathcal {N}}(0,1)$ as n tends to infinity.

The same also holds in all dimensions greater than 2.

The [polytope](https://en.wikipedia.org/wiki/Convex_polytope) K<sub>n</sub> is called a Gaussian [random polytope](https://en.wikipedia.org/wiki/Random_polytope).

A similar result holds for the number of vertices (of the Gaussian polytope), the number of edges, and in fact, faces of all dimensions.

### Linear functions of orthogonal matrices

A linear function of a matrix **M** is a linear combination of its elements (with given coefficients), **M** ↦ tr(**AM**) where **A** is the matrix of the coefficients; see [Trace (linear algebra)#Inner product](https://en.wikipedia.org/wiki/Trace_(linear_algebra)#Inner_product "Trace (linear algebra)").

A random [orthogonal matrix](https://en.wikipedia.org/wiki/Orthogonal_matrix) is said to be distributed uniformly, if its distribution is the normalized [Haar measure](https://en.wikipedia.org/wiki/Haar_measure) on the [orthogonal group](https://en.wikipedia.org/wiki/Orthogonal_group) O(*n*,**R**); see [Rotation matrix#Uniform random rotation matrices](https://en.wikipedia.org/wiki/Rotation_matrix#Uniform_random_rotation_matrices).

**Theorem**—Let **M** be a random orthogonal *n* × *n* matrix distributed uniformly, and **A** a fixed *n* × *n* matrix such that tr(**AA**\*) = *n*, and let *X* = tr(**AM**). Then the distribution of X is close to ${\mathcal {N}}(0,1)$ in the total variation metric up to<sup>\[*[clarification needed](https://en.wikipedia.org/wiki/Wikipedia:Please_clarify)*\]</sup> 2√3/*n* − 1.

### Subsequences

**Theorem**—Let random variables *X*<sub>1</sub>, *X*<sub>2</sub>, ... ∈ *L*<sub>2</sub>(Ω) be such that *X<sub>n</sub>* → 0 [weakly](https://en.wikipedia.org/wiki/Weak_convergence_(Hilbert_space) "Weak convergence (Hilbert space)") in *L*<sub>2</sub>(Ω) and *X*  
<sub>*n*</sub> → 1 weakly in *L*<sub>1</sub>(Ω). Then there exist integers *n*<sub>1</sub> \< *n*<sub>2</sub> \< ⋯ such that

$$
{\frac {X_{n_{1}}+\cdots +X_{n_{k}}}{\sqrt {k}}}
$$

converges in distribution to ${\mathcal {N}}(0,1)$ as k tends to infinity.

### Random walk on a crystal lattice

The central limit theorem may be established for the simple [random walk](https://en.wikipedia.org/wiki/Random_walk) on a crystal lattice (an infinite-fold abelian covering graph over a finite graph), and is used for design of crystal structures.

## Applications and examples

A simple example of the central limit theorem is rolling many identical, unbiased dice. The distribution of the sum (or average) of the rolled numbers will be well approximated by a normal distribution. Since real-world quantities are often the balanced sum of many unobserved random events, the central limit theorem also provides a partial explanation for the prevalence of the normal probability distribution. It also justifies the approximation of large-sample [statistics](https://en.wikipedia.org/wiki/Statistic) to the normal distribution in controlled experiments.

![[media/6e79512750131fd6d2b9b389940eda5b42349dfd.png]]

Comparison of probability density functions *p*(*k*) for the sum of n fair 6-sided dice to show their convergence to a normal distribution with increasing n, in accordance to the central limit theorem. In the bottom-right graph, smoothed profiles of the previous graphs are rescaled, superimposed and compared with a normal distribution (black curve).

![[media/ec834f205903d14537d16cd39aed43f40dbd1ce8.jpg]]

This figure demonstrates the central limit theorem. The sample means are generated using a random number generator, which draws numbers between 0 and 100 from a uniform probability distribution. It illustrates that increasing sample sizes result in the 500 measured sample means being more closely distributed about the population mean (50 in this case). It also compares the observed distributions with the distributions that would be expected for a normalized Gaussian distribution, and shows the [chi-squared](https://en.wikipedia.org/wiki/Pearson%27s_chi-squared_test) values that quantify the goodness of the fit (the fit is good if the reduced [chi-squared](https://en.wikipedia.org/wiki/Pearson%27s_chi-squared_test) value is less than or approximately equal to one). The input into the normalized Gaussian function is the mean of sample means (~50) and the mean sample standard deviation divided by the square root of the sample size (~28.87/√*n*), which is called the standard deviation of the mean (since it refers to the spread of sample means).

![[media/1499f37e514673faad78b068552f4c44e74f7331.png]]
Another simulation using the binomial distribution. Random 0s and 1s were generated, and then their means calculated for sample sizes ranging from 1 to 2048. Note that as the sample size increases the tails become thinner and the distribution becomes more concentrated around the mean.

### Regression

[Regression analysis](https://en.wikipedia.org/wiki/Regression_analysis), and in particular [ordinary least squares](https://en.wikipedia.org/wiki/Ordinary_least_squares), specifies that a [dependent variable](https://en.wikipedia.org/wiki/Dependent_variable) depends according to some function upon one or more [independent variables](https://en.wikipedia.org/wiki/Independent_variable), with an additive [error term](https://en.wikipedia.org/wiki/Errors_and_residuals_in_statistics). Various types of statistical inference on the regression assume that the error term is normally distributed. This assumption can be justified by assuming that the error term is actually the sum of many independent error terms; even if the individual error terms are not normally distributed, by the central limit theorem their sum can be well approximated by a normal distribution.

### Other illustrations

Given its importance to statistics, a number of papers and computer packages are available that demonstrate the convergence involved in the central limit theorem.

## History

Dutch mathematician [Henk Tijms](https://en.wikipedia.org/wiki/Henk_Tijms) writes:

> The central limit theorem has an interesting history. The first version of this theorem was postulated by the French-born mathematician [Abraham de Moivre](https://en.wikipedia.org/wiki/Abraham_de_Moivre) who, in a remarkable article published in 1733, used the normal distribution to approximate the distribution of the number of heads resulting from many tosses of a fair coin. This finding was far ahead of its time, and was nearly forgotten until the famous French mathematician [Pierre-Simon Laplace](https://en.wikipedia.org/wiki/Pierre-Simon_Laplace) rescued it from obscurity in his monumental work *Théorie analytique des probabilités*, which was published in 1812. Laplace expanded De Moivre's finding by approximating the binomial distribution with the normal distribution. But as with De Moivre, Laplace's finding received little attention in his own time. It was not until the nineteenth century was at an end that the importance of the central limit theorem was discerned, when, in 1901, Russian mathematician [Aleksandr Lyapunov](https://en.wikipedia.org/wiki/Aleksandr_Lyapunov) defined it in general terms and proved precisely how it worked mathematically. Nowadays, the central limit theorem is considered to be the unofficial sovereign of probability theory.

Sir [Francis Galton](https://en.wikipedia.org/wiki/Francis_Galton) described the Central Limit Theorem in this way:

> I know of scarcely anything so apt to impress the imagination as the wonderful form of cosmic order expressed by the "Law of Frequency of Error". The law would have been personified by the Greeks and deified, if they had known of it. It reigns with serenity and in complete self-effacement, amidst the wildest confusion. The huger the mob, and the greater the apparent anarchy, the more perfect is its sway. It is the supreme law of Unreason. Whenever a large sample of chaotic elements are taken in hand and marshalled in the order of their magnitude, an unsuspected and most beautiful form of regularity proves to have been latent all along.

The actual term "central limit theorem" (in German: "zentraler Grenzwertsatz") was first used by [George Pólya](https://en.wikipedia.org/wiki/George_P%C3%B3lya) in 1920 in the title of a paper. Pólya referred to the theorem as "central" due to its importance in probability theory. According to Le Cam, the French school of probability interprets the word *central* in the sense that "it describes the behaviour of the centre of the distribution as opposed to its tails". The abstract of the paper *On the central limit theorem of calculus of probability and the problem of moments* by Pólya in 1920 translates as follows.

> The occurrence of the Gaussian probability density 1 = *e*<sup>−*x*<sup>2</sup></sup> in repeated experiments, in errors of measurements, which result in the combination of very many and very small elementary errors, in diffusion processes etc., can be explained, as is well-known, by the very same limit theorem, which plays a central role in the calculus of probability. The actual discoverer of this limit theorem is to be named Laplace; it is likely that its rigorous proof was first given by Tschebyscheff and its sharpest formulation can be found, as far as I am aware of, in an article by [Liapounoff](https://en.wikipedia.org/wiki/Aleksandr_Lyapunov). ...

A thorough account of the theorem's history, detailing Laplace's foundational work, as well as [Cauchy](https://en.wikipedia.org/wiki/Augustin-Louis_Cauchy)'s, [Bessel](https://en.wikipedia.org/wiki/Friedrich_Bessel)'s and [Poisson](https://en.wikipedia.org/wiki/Sim%C3%A9on_Denis_Poisson)'s contributions, is provided by Hald. Two historical accounts, one covering the development from Laplace to Cauchy, the second the contributions by [von Mises](https://en.wikipedia.org/wiki/Richard_von_Mises), [Pólya](https://en.wikipedia.org/wiki/George_P%C3%B3lya), [Lindeberg](https://en.wikipedia.org/wiki/Jarl_Waldemar_Lindeberg), [Lévy](https://en.wikipedia.org/wiki/Paul_L%C3%A9vy_(mathematician) "Paul Lévy (mathematician)"), and [Cramér](https://en.wikipedia.org/wiki/Harald_Cram%C3%A9r) during the 1920s, are given by Hans Fischer. Le Cam describes a period around 1935. Bernstein presents a historical discussion focusing on the work of [Pafnuty Chebyshev](https://en.wikipedia.org/wiki/Pafnuty_Chebyshev) and his students [Andrey Markov](https://en.wikipedia.org/wiki/Andrey_Markov) and [Aleksandr Lyapunov](https://en.wikipedia.org/wiki/Aleksandr_Lyapunov) that led to the first proofs of the CLT in a general setting.

A curious footnote to the history of the Central Limit Theorem is that a proof of a result similar to the 1922 Lindeberg CLT was the subject of [Alan Turing](https://en.wikipedia.org/wiki/Alan_Turing)'s 1934 Fellowship Dissertation for [King's College](https://en.wikipedia.org/wiki/King%27s_College,_Cambridge) at the [University of Cambridge](https://en.wikipedia.org/wiki/University_of_Cambridge). Only after submitting the work did Turing learn it had already been proved. Consequently, Turing's dissertation was not published.

## See also

- [Asymptotic equipartition property](https://en.wikipedia.org/wiki/Asymptotic_equipartition_property)
- [Asymptotic distribution](https://en.wikipedia.org/wiki/Asymptotic_distribution)
- [Bates distribution](https://en.wikipedia.org/wiki/Bates_distribution)
- [Benford's law](https://en.wikipedia.org/wiki/Benford%27s_law) – result of extension of CLT to product of random variables.
- [Berry–Esseen theorem](https://en.wikipedia.org/wiki/Berry%E2%80%93Esseen_theorem)
- [Central limit theorem for directional statistics](https://en.wikipedia.org/wiki/Central_limit_theorem_for_directional_statistics) – Central limit theorem applied to the case of directional statistics
- [Delta method](https://en.wikipedia.org/wiki/Delta_method) – to compute the limit distribution of a function of a random variable.
- [Erdős–Kac theorem](https://en.wikipedia.org/wiki/Erd%C5%91s%E2%80%93Kac_theorem) – connects the number of prime factors of an integer with the normal probability distribution
- [Fisher–Tippett–Gnedenko theorem](https://en.wikipedia.org/wiki/Fisher%E2%80%93Tippett%E2%80%93Gnedenko_theorem) – limit theorem for extremum values (such as max{*X<sub>n</sub>*})
- [Irwin–Hall distribution](https://en.wikipedia.org/wiki/Irwin%E2%80%93Hall_distribution)
- [Markov chain central limit theorem](https://en.wikipedia.org/wiki/Markov_chain_central_limit_theorem)
- [Normal distribution](https://en.wikipedia.org/wiki/Normal_distribution)
- [Tweedie convergence theorem](https://en.wikipedia.org/wiki/Tweedie_distribution) – a theorem that can be considered to bridge between the central limit theorem and the [Poisson convergence theorem](https://en.wikipedia.org/wiki/Poisson_convergence_theorem)
- [Donsker's theorem](https://en.wikipedia.org/wiki/Donsker%27s_theorem)

## Notes

2.  Montgomery, Douglas C.; Runger, George C. (2014). *Applied Statistics and Probability for Engineers* (6th ed.). Wiley. p. 241. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9781118539712](https://en.wikipedia.org/wiki/Special:BookSources/9781118539712).
3.  Rouaud, Mathieu (2013). [Probability, Statistics and Estimation](http://www.incertitudes.fr/book.pdf) (PDF). p. 10. [Archived](https://ghostarchive.org/archive/20221009/http://www.incertitudes.fr/book.pdf) (PDF) from the original on 2022-10-09.
4.  , p. 357.
5.  , p. 199, Theorem 30.13.
6.  , p. 362.
7.  Robbins, Herbert (1948). ["The asymptotic distribution of the sum of a random number of random variables"](https://projecteuclid.org/journals/bulletin-of-the-american-mathematical-society/volume-54/issue-12/The-asymptotic-distribution-of-the-sum-of-a-random-number/bams/1183513324.full). *Bull. Amer. Math. Soc*. **54** (12): 1151–1161. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1090/S0002-9904-1948-09142-X](https://doi.org/10.1090%2FS0002-9904-1948-09142-X).
8.  Chen, Louis H.Y.; Goldstein, Larry; Shao, Qi-Man (2011). *Normal Approximation by Stein's Method*. Berlin Heidelberg: Springer-Verlag. pp. 270–271.
9.  ^   van der Vaart, A.W. (1998). *Asymptotic statistics*. New York, NY: Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-49603-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-49603-2). [LCCN](https://en.wikipedia.org/wiki/LCCN_(identifier)) [98015176](https://lccn.loc.gov/98015176).
10. [O’Donnell, Ryan](https://en.wikipedia.org/wiki/Ryan_O%27Donnell_(computer_scientist) "Ryan O'Donnell (computer scientist)") (2014). ["Theorem 5.38"](https://web.archive.org/web/20190408054104/http://www.contrib.andrew.cmu.edu/~ryanod/?p=866). Archived from [the original](http://www.contrib.andrew.cmu.edu/~ryanod/?p=866) on 2019-04-08. Retrieved 2017-10-18.
11. Bentkus, V. (2005). "A Lyapunov-type bound in $\mathbb {R} ^{d}$". *Theory Probab. Appl*. **49** (2): 311–323. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/S0040585X97981123](https://doi.org/10.1137%2FS0040585X97981123).
12. Le Cam, L. (February 1986). "The Central Limit Theorem around 1935". *Statistical Science*. **1** (1): 78–91. [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2245503](https://www.jstor.org/stable/2245503).
13. Lévy, Paul (1937). *Theorie de l'addition des variables aleatoires* \[*Combination theory of unpredictable variables*\] (in French). Paris: Gauthier-Villars.
14. Gnedenko, Boris Vladimirovich; Kologorov, Andreĭ Nikolaevich; Doob, Joseph L.; Hsu, Pao-Lu (1968). *Limit distributions for sums of independent random variables*. Reading, MA: Addison-wesley.
15. Nolan, John P. (2020). [Univariate stable distributions, Models for Heavy Tailed Data](https://doi.org/10.1007/978-3-030-52915-4). Springer Series in Operations Research and Financial Engineering. Switzerland: Springer. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-3-030-52915-4](https://doi.org/10.1007%2F978-3-030-52915-4). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-030-52914-7](https://en.wikipedia.org/wiki/Special:BookSources/978-3-030-52914-7). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [226648987](https://api.semanticscholar.org/CorpusID:226648987).
16. , Theorem 27.4.
17. **,_Theorem_7.8_17-0)** , Sect. 7.7(c), Theorem 7.8.
18. , Sect. 7.7, Theorem 7.4.
19. , Theorem 35.12.
20. Lemons, Don (2003). [An Introduction to Stochastic Processes in Physics](https://jhupbooks.press.jhu.edu/content/introduction-stochastic-processes-physics). Johns Hopkins University Press. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.56021/9780801868665](https://doi.org/10.56021%2F9780801868665). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780801876387](https://en.wikipedia.org/wiki/Special:BookSources/9780801876387). Retrieved 2016-08-11.
21. [Stein, C.](https://en.wikipedia.org/wiki/Charles_Stein_(statistician)) (1972). ["A bound for the error in the normal approximation to the distribution of a sum of dependent random variables"](https://projecteuclid.org/euclid.bsmsp/1200514239). *Proceedings of the Sixth Berkeley Symposium on Mathematical Statistics and Probability*. **6** (2): 583–602. [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0402873](https://mathscinet.ams.org/mathscinet-getitem?mr=0402873). [Zbl](https://en.wikipedia.org/wiki/Zbl_(identifier)) [0278.60026](https://zbmath.org/?format=complete&q=an:0278.60026).
22. Chen, L. H. Y.; Goldstein, L.; Shao, Q. M. (2011). *Normal approximation by Stein's method*. Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-642-15006-7](https://en.wikipedia.org/wiki/Special:BookSources/978-3-642-15006-7).
23. [Artstein, S.](https://en.wikipedia.org/wiki/Shiri_Artstein); [Ball, K.](https://en.wikipedia.org/wiki/Keith_Martin_Ball); [Barthe, F.](https://en.wikipedia.org/wiki/Franck_Barthe); [Naor, A.](https://en.wikipedia.org/wiki/Assaf_Naor) (2004). ["Solution of Shannon's Problem on the Monotonicity of Entropy"](https://doi.org/10.1090%2FS0894-0347-04-00459-X). *Journal of the American Mathematical Society*. **17** (4): 975–982. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1090/S0894-0347-04-00459-X](https://doi.org/10.1090%2FS0894-0347-04-00459-X).
24. Brewer, J. K. (1985). "Behavioral statistics textbooks: Source of myths and misconceptions?". *Journal of Educational Statistics*. **10** (3): 252–268. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3102/10769986010003252](https://doi.org/10.3102%2F10769986010003252). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [119611584](https://api.semanticscholar.org/CorpusID:119611584).
25. Yu, C.; Behrens, J.; Spencer, A. Identification of Misconception in the Central Limit Theorem and Related Concepts, *American Educational Research Association* lecture 19 April 1995
26. Sotos, A. E. C.; Vanhoof, S.; Van den Noortgate, W.; Onghena, P. (2007). ["Students' misconceptions of statistical inference: A review of the empirical evidence from research on statistics education"](https://lirias.kuleuven.be/handle/123456789/136347). *Educational Research Review*. **2** (2): 98–113. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.edurev.2007.04.001](https://doi.org/10.1016%2Fj.edurev.2007.04.001).
27. ["Sampling distribution of the sample mean"](https://web.archive.org/web/20230602200310/https://www.khanacademy.org/math/statistics-probability/sampling-distributions-library/sample-means/v/sampling-distribution-of-the-sample-mean). *Khan Academy*. 2 June 2023. Archived from [the original](https://www.khanacademy.org/math/statistics-probability/sampling-distributions-library/sample-means/v/sampling-distribution-of-the-sample-mean) (video) on 2023-06-02. Retrieved 2023-10-08.
28. Rosenthal, Jeffrey Seth (2000). *A First Look at Rigorous Probability Theory*. World Scientific. Theorem 5.3.4, p. 47. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [981-02-4322-7](https://en.wikipedia.org/wiki/Special:BookSources/981-02-4322-7).
29. Johnson, Oliver Thomas (2004). *Information Theory and the Central Limit Theorem*. Imperial College Press. p. 88. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [1-86094-473-6](https://en.wikipedia.org/wiki/Special:BookSources/1-86094-473-6).
30. Uchaikin, Vladimir V.; Zolotarev, V.M. (1999). *Chance and Stability: Stable distributions and their applications*. VSP. pp. 61–62. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [90-6764-301-7](https://en.wikipedia.org/wiki/Special:BookSources/90-6764-301-7).
31. Borodin, A. N.; Ibragimov, I. A.; Sudakov, V. N. (1995). *Limit Theorems for Functionals of Random Walks*. AMS Bookstore. Theorem 1.1, p. 8. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-8218-0438-3](https://en.wikipedia.org/wiki/Special:BookSources/0-8218-0438-3).
32. Petrov, V. V. (1976). [Sums of Independent Random Variables](https://books.google.com/books?id=zSDqCAAAQBAJ). New York-Heidelberg: Springer-Verlag. ch. 7. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9783642658099](https://en.wikipedia.org/wiki/Special:BookSources/9783642658099).
33. Hew, Patrick Chisan (2017). "Asymptotic distribution of rewards accumulated by alternating renewal processes". *Statistics and Probability Letters*. **129**: 355–359. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.spl.2017.06.027](https://doi.org/10.1016%2Fj.spl.2017.06.027).
34. Rempala, G.; Wesolowski, J. (2002). ["Asymptotics of products of sums and U-statistics"](https://projecteuclid.org/journals/electronic-communications-in-probability/volume-7/issue-none/Asymptotics-for-Products-of-Sums-and-U-statistics/10.1214/ECP.v7-1046.pdf) (PDF). *Electronic Communications in Probability*. **7**: 47–54. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/ecp.v7-1046](https://doi.org/10.1214%2Fecp.v7-1046).
35. , Theorem 1.2.
36. , Section 2.4, Example 4.5.
37. , Theorem 1.
38. , Theorem 1.1.
39. [Zygmund, Antoni](https://en.wikipedia.org/wiki/Antoni_Zygmund) (2003) \[1959\]. [*Trigonometric Series*](https://en.wikipedia.org/wiki/Trigonometric_Series). Cambridge University Press. vol. II, sect. XVI.5, Theorem 5-5. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-89053-5](https://en.wikipedia.org/wiki/Special:BookSources/0-521-89053-5).
40. , Theorem 2.1.13.
41. , Theorem 1.1.
42. , Theorem 1.2.
43. [Meckes, Elizabeth](https://en.wikipedia.org/wiki/Elizabeth_Meckes) (2008). "Linear functions on the classical matrix groups". *Transactions of the American Mathematical Society*. **360** (10): 5355–5366. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[math/0509441](https://arxiv.org/abs/math/0509441). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1090/S0002-9947-08-04444-9](https://doi.org/10.1090%2FS0002-9947-08-04444-9). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [11981408](https://api.semanticscholar.org/CorpusID:11981408).
44. , Sect. 1.5.
45. Kotani, M.; [Sunada, Toshikazu](https://en.wikipedia.org/wiki/Toshikazu_Sunada) (2003). *Spectral geometry of crystal lattices*. Vol. 338. Contemporary Math. pp. 271–305. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8218-4269-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8218-4269-0).
46. [Sunada, Toshikazu](https://en.wikipedia.org/wiki/Toshikazu_Sunada) (2012). *Topological Crystallography – With a View Towards Discrete Geometric Analysis*. Surveys and Tutorials in the Applied Mathematical Sciences. Vol. 6. Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-4-431-54177-6](https://en.wikipedia.org/wiki/Special:BookSources/978-4-431-54177-6).
47. Marasinghe, M.; Meeker, W.; Cook, D.; Shin, T. S. (August 1994). *Using graphics and simulation to teach statistical concepts*. Annual meeting of the American Statistician Association, Toronto, Canada.
48. Henk, Tijms (2004). *Understanding Probability: Chance Rules in Everyday Life*. Cambridge: Cambridge University Press. p. 169. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-54036-4](https://en.wikipedia.org/wiki/Special:BookSources/0-521-54036-4).
49. Galton, F. (1889). [Natural Inheritance](https://galton.org/cgi-bin/searchImages/galton/search/books/natural-inheritance/pages/natural-inheritance_0073.htm). p. 66.
50. ^   [Pólya, George](https://en.wikipedia.org/wiki/George_P%C3%B3lya) (1920). ["Über den zentralen Grenzwertsatz der Wahrscheinlichkeitsrechnung und das Momentenproblem"](https://www-gdz.sub.uni-goettingen.de/cgi-bin/digbib.cgi?PPN266833020_0008) \[On the central limit theorem of probability calculation and the problem of moments\]. *[Mathematische Zeitschrift](https://en.wikipedia.org/wiki/Mathematische_Zeitschrift)* (in German). **8** (3–4): 171–181. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/BF01206525](https://doi.org/10.1007%2FBF01206525). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [123063388](https://api.semanticscholar.org/CorpusID:123063388).
51. ^    [Le Cam, Lucien](https://en.wikipedia.org/wiki/Lucien_Le_Cam) (1986). ["The central limit theorem around 1935"](http://projecteuclid.org/euclid.ss/1177013818). *Statistical Science*. **1** (1): 78–91. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/ss/1177013818](https://doi.org/10.1214%2Fss%2F1177013818).
52. Hald, Andreas (22 April 1998). [A History of Mathematical Statistics from 1750 to 1930](http://www.gbv.de/dms/goettingen/229762905.pdf) (PDF). Wiley. chapter 17. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0471179122](https://en.wikipedia.org/wiki/Special:BookSources/978-0471179122). [Archived](https://ghostarchive.org/archive/20221009/http://www.gbv.de/dms/goettingen/229762905.pdf) (PDF) from the original on 2022-10-09.
53. , Chapter 2; Chapter 5.2.
54. [Bernstein, S. N.](https://en.wikipedia.org/wiki/Sergei_Natanovich_Bernstein) (1945). "On the work of P. L. Chebyshev in Probability Theory". In Bernstein., S. N. (ed.). *Nauchnoe Nasledie P. L. Chebysheva. Vypusk Pervyi: Matematika* \[*The Scientific Legacy of P. L. Chebyshev. Part I: Mathematics*\] (in Russian). Moscow & Leningrad: Academiya Nauk SSSR. p. 174.
55. Zabell, S. L. (1995). "Alan Turing and the Central Limit Theorem". *American Mathematical Monthly*. **102** (6): 483–494. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/00029890.1995.12004608](https://doi.org/10.1080%2F00029890.1995.12004608).
56. Jørgensen, Bent (1997). *The Theory of Dispersion Models*. Chapman & Hall. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0412997112](https://en.wikipedia.org/wiki/Special:BookSources/978-0412997112).

## References

- [Bárány, Imre](https://en.wikipedia.org/wiki/Imre_B%C3%A1r%C3%A1ny); Vu, Van (2007). "Central limit theorems for Gaussian polytopes". *Annals of Probability*. **35** (4). Institute of Mathematical Statistics: 1593–1621. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[math/0610192](https://arxiv.org/abs/math/0610192). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/009117906000000791](https://doi.org/10.1214%2F009117906000000791). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [9128253](https://api.semanticscholar.org/CorpusID:9128253).
- Bauer, Heinz (2001). *Measure and Integration Theory*. Berlin: de Gruyter. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [3110167190](https://en.wikipedia.org/wiki/Special:BookSources/3110167190).
- Billingsley, Patrick (1995). *Probability and Measure* (3rd ed.). John Wiley & Sons. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-00710-2](https://en.wikipedia.org/wiki/Special:BookSources/0-471-00710-2).
- Bradley, Richard (2005). "Basic Properties of Strong Mixing Conditions. A Survey and Some Open Questions". *Probability Surveys*. **2**: 107–144. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[math/0511078](https://arxiv.org/abs/math/0511078). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2005math.....11078B](https://ui.adsabs.harvard.edu/abs/2005math.....11078B). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/154957805100000104](https://doi.org/10.1214%2F154957805100000104). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [8395267](https://api.semanticscholar.org/CorpusID:8395267).
- Bradley, Richard (2007). *Introduction to Strong Mixing Conditions* (1st ed.). Heber City, UT: Kendrick Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-9740427-9-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-9740427-9-4).
- Dinov, Ivo; Christou, Nicolas; Sanchez, Juana (2008). ["Central Limit Theorem: New SOCR Applet and Demonstration Activity"](https://web.archive.org/web/20160303185802/http://www.amstat.org/publications/jse/v16n2/dinov.html). *Journal of Statistics Education*. **16** (2). ASA: 1–15. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/10691898.2008.11889560](https://doi.org/10.1080%2F10691898.2008.11889560). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [3152447](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3152447). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [21833159](https://pubmed.ncbi.nlm.nih.gov/21833159). Archived from [the original](http://www.amstat.org/publications/jse/v16n2/dinov.html) on 2016-03-03. Retrieved 2008-08-23.
- [Durrett, Richard](https://en.wikipedia.org/wiki/Rick_Durrett) (2004). *Probability: theory and examples* (3rd ed.). Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0521765390](https://en.wikipedia.org/wiki/Special:BookSources/0521765390).
- Fischer, Hans (2011). [A History of the Central Limit Theorem: From Classical to Modern Probability Theory](http://www.medicine.mcgill.ca/epidemiology/hanley/bios601/GaussianModel/HistoryCentralLimitTheorem.pdf) (PDF). Sources and Studies in the History of Mathematics and Physical Sciences. New York: Springer. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-0-387-87857-7](https://doi.org/10.1007%2F978-0-387-87857-7). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-87856-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-87856-0). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [2743162](https://mathscinet.ams.org/mathscinet-getitem?mr=2743162). [Zbl](https://en.wikipedia.org/wiki/Zbl_(identifier)) [1226.60004](https://zbmath.org/?format=complete&q=an:1226.60004). [Archived](https://web.archive.org/web/20171031171033/http://www.medicine.mcgill.ca/epidemiology/hanley/bios601/GaussianModel/HistoryCentralLimitTheorem.pdf) (PDF) from the original on 2017-10-31.
- Gaposhkin, V. F. (1966). "Lacunary series and independent functions". *Russian Mathematical Surveys*. **21** (6): 1–82. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1966RuMaS..21....1G](https://ui.adsabs.harvard.edu/abs/1966RuMaS..21....1G). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1070/RM1966v021n06ABEH001196](https://doi.org/10.1070%2FRM1966v021n06ABEH001196). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [250833638](https://api.semanticscholar.org/CorpusID:250833638)..
- Klartag, Bo'az (2007). "A central limit theorem for convex sets". *Inventiones Mathematicae*. **168** (1): 91–131. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[math/0605014](https://arxiv.org/abs/math/0605014). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2007InMat.168...91K](https://ui.adsabs.harvard.edu/abs/2007InMat.168...91K). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s00222-006-0028-8](https://doi.org/10.1007%2Fs00222-006-0028-8). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [119169773](https://api.semanticscholar.org/CorpusID:119169773).
- Klartag, Bo'az (2008). "A Berry–Esseen type inequality for convex bodies with an unconditional basis". *Probability Theory and Related Fields*. **145** (1–2): 1–33. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[0705.0832](https://arxiv.org/abs/0705.0832). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s00440-008-0158-6](https://doi.org/10.1007%2Fs00440-008-0158-6). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [10163322](https://api.semanticscholar.org/CorpusID:10163322).

## External links

- [Central Limit Theorem](https://www.khanacademy.org/math/probability/statistics-inferential/sampling_distribution/v/central-limit-theorem) at Khan Academy
- ["Central limit theorem"](https://www.encyclopediaofmath.org/). *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*. [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society). 2001 \[1994\].
- [Weisstein, Eric W.](https://en.wikipedia.org/wiki/Eric_W._Weisstein) ["Central Limit Theorem"](https://mathworld.wolfram.com/CentralLimitTheorem.html). *[MathWorld](https://en.wikipedia.org/wiki/MathWorld)*.
- [A music video demonstrating the central limit theorem with a Galton board](https://www.mctague.org/carl/blog/2021/04/23/central-limit-theorem/) by Carl McTague
