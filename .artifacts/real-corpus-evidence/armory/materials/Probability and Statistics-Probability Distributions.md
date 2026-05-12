[[probability-statistics.base]]

> Source: [Probability distribution](https://en.wikipedia.org/wiki/Probability_distribution)
> License: Wikipedia content is available under CC BY-SA 4.0.

In [probability theory](https://en.wikipedia.org/wiki/Probability_theory) and [statistics](https://en.wikipedia.org/wiki/Statistics), a **probability distribution** is a [function](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)") that gives the probabilities of occurrence of possible **events** for an [experiment](https://en.wikipedia.org/wiki/Experiment_(probability_theory) "Experiment (probability theory)"). It is a mathematical description of a [random](https://en.wikipedia.org/wiki/Randomness) phenomenon in terms of its [sample space](https://en.wikipedia.org/wiki/Sample_space) and the [probabilities](https://en.wikipedia.org/wiki/Probability) of [events](https://en.wikipedia.org/wiki/Event_(probability_theory) "Event (probability theory)") ([subsets](https://en.wikipedia.org/wiki/Subset) of the sample space).

Each [random variable](https://en.wikipedia.org/wiki/Random_variable) has a probability distribution. For instance, if X is used to denote the outcome of a [coin toss](https://en.wikipedia.org/wiki/Coin_flipping) ("the experiment"), then the probability distribution of X would take the value 0.5 (1 in 2 or 1/2) for *X* = heads, and 0.5 for *X* = tails (assuming that [the coin is fair](https://en.wikipedia.org/wiki/Fair_coin)). More commonly, probability distributions are used to compare the relative occurrence of many different random values.

In practice, probability distributions are often described using [[Cumulative Distribution Function|cumulative distribution functions]], [probability mass functions](https://en.wikipedia.org/wiki/Probability_mass_function) or [[Probability Density Function|probability density functions]]. In probability theory, probability distributions are represented by [probability measures](https://en.wikipedia.org/wiki/Probability_measures), and the term probability distribution is often used in reference to probability measures associated with random variables. [Probability distributions of particular importance](https://en.wikipedia.org/wiki/List_of_probability_distributions) are given specific names.

## Introduction

A probability distribution is a mathematical description of the probabilities of events, subsets of the [sample space](https://en.wikipedia.org/wiki/Sample_space). The sample space, often represented in notation by $\ \Omega \ ,$ is the [set](https://en.wikipedia.org/wiki/Set_(mathematics) "Set (mathematics)") of all possible [outcomes](https://en.wikipedia.org/wiki/Outcome_(probability) "Outcome (probability)") of a random phenomenon being observed. The sample space may be any set: a set of [real numbers](https://en.wikipedia.org/wiki/Real_numbers), a set of descriptive labels, a set of [vectors](https://en.wikipedia.org/wiki/Vector_(mathematics)), a set of arbitrary non-numerical values, etc. For example, the sample space of a coin flip could be Ω = {"heads", "tails"}.

To define probability distributions for the specific case of [[Random Variables]] (so the sample space can be seen as a numeric set), it is common to distinguish between **discrete** and **continuous** [random variables](https://en.wikipedia.org/wiki/Random_variable). In the discrete case, it is sufficient to specify a [probability mass function](https://en.wikipedia.org/wiki/Probability_mass_function) $p$ assigning a probability to each possible outcome (e.g. when throwing a fair [die](https://en.wikipedia.org/wiki/Dice), each of the six digits “1” to “6”, corresponding to the number of dots on the die, has probability ${\tfrac {1}{6}}).$ The probability of an [event](https://en.wikipedia.org/wiki/Event_(probability_theory) "Event (probability theory)") is then defined to be the sum of the probabilities of all outcomes that satisfy the event; for example, the probability of the event "the die rolls an even value" is 

$$
p({\text{“}}2{\text{”}})+p({\text{“}}4{\text{”}})+p({\text{“}}6{\text{”}})={\frac {1}{6}}+{\frac {1}{6}}+{\frac {1}{6}}={\frac {1}{2}}.
$$

 In contrast, when a random variable takes values from a continuum then by convention, any individual outcome is assigned probability zero. For such continuous random variables, only events that include infinitely many outcomes such as intervals have probability greater than 0.

For example, consider measuring the weight of a piece of ham in the supermarket, and assume the scale can provide arbitrarily many digits of precision. Then, the probability that it weighs *exactly* 500 [g](https://en.wikipedia.org/wiki/Gram) must be zero because no matter how high the level of precision chosen, it cannot be assumed that there are no non-zero decimal digits in the remaining omitted digits ignored by the precision level.

However, for the same use case, it is possible to meet quality control requirements such as that a package of "500 g" of ham must weigh between 490 g and 510 g with at least 98% probability. This is possible because this measurement does not require as much precision from the underlying equipment.

![[media/4a41c11c7c234abb91c5c291c0b656c43b5522e5.png]]
Figure 1: The left graph shows a probability density function. The right graph shows the cumulative distribution function. The value at <strong>a</strong> in the cumulative distribution equals the area under the probability density curve up to the point <strong>a</strong>.

Continuous probability distributions can be described by means of the [[Cumulative Distribution Function]], which describes the probability that the random variable is no larger than a given value (i.e., *P*(*X* ≤ *x*) for some x. The cumulative distribution function is the area under the [[Probability Density Function]] from -∞ to x, as shown in figure 1.

Most continuous probability distributions encountered in practice are not only continuous but also [absolutely continuous](https://en.wikipedia.org/wiki/Absolutely_continuous). Such distributions can be described by their [[Probability Density Function]]. Informally, the probability density $f$ of a random variable $X$ describes the [infinitesimal](https://en.wikipedia.org/wiki/Infinitesimal) probability that $X$ takes any value $x$ — that is $P(x\leq X<x+\Delta x)\approx f(x)\,\Delta x$ as $\Delta x>0$ becomes arbitrarily small. The probability that $X$ lies in a given interval can be computed rigorously by [integrating](https://en.wikipedia.org/wiki/Integration_(mathematics)) the probability density function over that interval.

## General probability definition

Let $(\Omega ,{\mathcal {F}},P)$ be a [probability space](https://en.wikipedia.org/wiki/Probability_space), $(E,{\mathcal {E}})$ be a [measurable space](https://en.wikipedia.org/wiki/Measurable_space), and $X:\Omega \to E$ be a $(E,{\mathcal {E}})$-valued random variable. Then the probability distribution of $X$ is the [pushforward measure](https://en.wikipedia.org/wiki/Pushforward_measure) of the probability measure $P$ onto $(E,{\mathcal {E}})$ induced by $X$. Explicitly, this pushforward measure on $(E,{\mathcal {E}})$ is given by 

$$
X_{*}(P)(B)=P\left(X^{-1}(B)\right)
$$

 for $B\in {\mathcal {E}}.$

Any probability distribution is a [probability measure](https://en.wikipedia.org/wiki/Probability_measure) on $(E,{\mathcal {E}})$ (in general different from $P$, unless $X$ happens to be the identity map).

A probability distribution can be described in various forms, such as by a probability mass function or a cumulative distribution function. One of the most general descriptions, which applies for absolutely continuous and discrete variables, is by means of a probability function $P\colon {\mathcal {A}}\to \mathbb {R}$ whose input space ${\mathcal {A}}$ is a [σ-algebra](https://en.wikipedia.org/wiki/%CE%A3-algebra), and gives a [real number](https://en.wikipedia.org/wiki/Real_number) probability as its output, particularly, a number in $[0,1]\subseteq \mathbb {R}$.

The probability function $P$ can take as argument subsets of the sample space itself, as in the coin toss example, where the function $P$ was defined so that *P*(heads) = 0.5 and *P*(tails) = 0.5. However, because of the widespread use of [[Random Variables]], which transform the sample space into a set of numbers (e.g., $\mathbb {R}$, $\mathbb {N}$), it is more common to study probability distributions whose argument are subsets of these particular kinds of sets (number sets), and all probability distributions discussed in this article are of this type. It is common to denote as $P(X\in E)$ the probability that a certain value of the variable $X$ belongs to a certain event $E$.

The above probability function only characterizes a probability distribution if it satisfies all the [Kolmogorov axioms](https://en.wikipedia.org/wiki/Kolmogorov_axioms), that is:

1.  $P(X\in E)\geq 0\;\forall E\in {\mathcal {A}}$, so the probability is non-negative
2.  $P(X\in E)\leq 1\;\forall E\in {\mathcal {A}}$, so no probability exceeds $1$
3.  $P(X\in \bigcup _{i}E_{i})=\sum _{i}P(X\in E_{i})$ for any countable disjoint family of sets $\{E_{i}\}$

The concept of probability function is made more rigorous by defining it as the element of a [probability space](https://en.wikipedia.org/wiki/Probability_space) $(X,{\mathcal {A}},P)$, where $X$ is the set of possible outcomes, ${\mathcal {A}}$ is the set of all subsets $E\subset X$ whose probability can be measured, and $P$ is the probability function, or probability measure, that assigns a probability to each of these measurable subsets $E\in {\mathcal {A}}$.

Probability distributions usually belong to one of two classes.

A **discrete probability distribution** is applicable to the scenarios where the set of possible outcomes is [discrete](https://en.wikipedia.org/wiki/Discrete_probability_distribution) (e.g. a coin toss, a roll of a die) and the probabilities are encoded by a discrete list of the probabilities of the outcomes; in this case probabilities are described by a [probability mass function](https://en.wikipedia.org/wiki/Probability_mass_function), and the probability distribution is given by a sum of the probability mass function.

An **absolutely continuous probability distribution** is applicable to scenarios where the set of possible outcomes can take on values in a continuous range (e.g. real numbers), such as the temperature on a given day. In the absolutely continuous case, probabilities are described by a [[Probability Density Function]], and the probability distribution is by definition the integral of the probability density function. The [normal distribution](https://en.wikipedia.org/wiki/Normal_distribution) is a commonly encountered absolutely continuous probability distribution. More complex experiments, such as those involving [stochastic processes](https://en.wikipedia.org/wiki/Stochastic_processes) defined in [continuous time](https://en.wikipedia.org/wiki/Continuous_time), may demand the use of more general [probability measures](https://en.wikipedia.org/wiki/Probability_measure).

A probability distribution whose sample space is one-dimensional (for example real numbers, list of labels, ordered labels or binary) is called [univariate](https://en.wikipedia.org/wiki/Univariate_distribution), while a distribution whose sample space is a [[Vector Space]] of dimension 2 or more is called [multivariate](https://en.wikipedia.org/wiki/Multivariate_distribution). A univariate distribution gives the probabilities of a single [random variable](https://en.wikipedia.org/wiki/Random_variable) taking on various different values; a multivariate distribution (a [joint probability distribution](https://en.wikipedia.org/wiki/Joint_probability_distribution)) gives the probabilities of a [random vector](https://en.wikipedia.org/wiki/Random_vector) – a list of two or more random variables – taking on various combinations of values. Important and commonly encountered univariate probability distributions include the [binomial distribution](https://en.wikipedia.org/wiki/Binomial_distribution), the [hypergeometric distribution](https://en.wikipedia.org/wiki/Hypergeometric_distribution), and the [normal distribution](https://en.wikipedia.org/wiki/Normal_distribution). A commonly encountered multivariate distribution is the [[Multivariate Normal Distribution]].

Besides the probability function, the cumulative distribution function, the probability mass function and the probability density function, the [[Moment Generating Function]] and the [characteristic function](https://en.wikipedia.org/wiki/Characteristic_function_(probability_theory) "Characteristic function (probability theory)") also serve to identify a probability distribution, as they uniquely determine an underlying cumulative distribution function.

![[media/97790f3455cd90760382c01cde114c65f76e224d.png]]
Figure 2: The [[Probability Density Function]] (pdf) of the [normal distribution](https://en.wikipedia.org/wiki/Normal_distribution), also called Gaussian or "bell curve", the most important absolutely continuous random distribution. As notated on the figure, the probabilities of intervals of values correspond to the area under the curve.

## Terminology

Some key concepts and terms, widely used in the literature on the topic of probability distributions, are listed below.

### Basic terms

- *[Random variable](https://en.wikipedia.org/wiki/Random_variable)*: takes values from a sample space; probabilities describe which values and set of values are more likely taken.
- *[Event](https://en.wikipedia.org/wiki/Event_(probability_theory) "Event (probability theory)")*: set of possible values (outcomes) of a random variable that occurs with a certain probability.
- *[Probability function](https://en.wikipedia.org/wiki/Probability_measure)* or *probability measure*: describes the probability $P(X\in E)$ that the event $E,$ occurs.
- *[[Cumulative Distribution Function]]*: function evaluating the [probability](https://en.wikipedia.org/wiki/Probability) that $X$ will take a value less than or equal to $x$ for a random variable (only for real-valued random variables).
- *[Quantile function](https://en.wikipedia.org/wiki/Quantile_function)*: the inverse of the cumulative distribution function. Gives $x$ such that, with probability $q$, $X$ will not exceed $x$.

### Discrete probability distributions

- **Discrete probability distribution**: for many random variables with finitely or countably infinitely many values.
- *[Probability mass function](https://en.wikipedia.org/wiki/Probability_mass_function)* (*pmf*): function that gives the probability that a discrete random variable is equal to some value.
- *[Frequency distribution](https://en.wikipedia.org/wiki/Frequency_distribution)*: a table that displays the frequency of various outcomes *in a sample*.
- *[Relative frequency](https://en.wikipedia.org/wiki/Relative_frequency) distribution*: a [frequency distribution](https://en.wikipedia.org/wiki/Frequency_distribution) where each value has been divided (normalized) by a number of outcomes in a [sample](https://en.wikipedia.org/wiki/Sample_(statistics)) (i.e. sample size).
- *[Categorical distribution](https://en.wikipedia.org/wiki/Categorical_distribution)*: for discrete random variables with a finite set of values.

### Absolutely continuous probability distributions

- **Absolutely continuous probability distribution**: for many random variables with uncountably many values.
- *[[Probability Density Function]]* (*pdf*) or *probability density*: function whose value at any given sample (or point) in the [sample space](https://en.wikipedia.org/wiki/Sample_space) (the set of possible values taken by the random variable) can be interpreted as providing a *relative likelihood* that the value of the random variable would equal that sample.

### Related terms

- [*Support*](https://en.wikipedia.org/wiki/Support_(mathematics) "Support (mathematics)"): set of values that can be assumed with non-zero probability (or probability density in the case of a continuous distribution) by the random variable. For a random variable $X$, it is sometimes denoted as $R_{X}$.
- **Tail**: the regions close to the bounds of the random variable, if the pmf or pdf are relatively low therein. Usually has the form $X>a$, $X<b$ or a union thereof.
- **Head**: the region where the pmf or pdf is relatively high. Usually has the form $a<X<b$.
- *[Expected value](https://en.wikipedia.org/wiki/Expected_value)* or *mean*: the [weighted average](https://en.wikipedia.org/wiki/Weighted_average) of the possible values, using their probabilities as their weights; or the continuous analog thereof.
- *[Median](https://en.wikipedia.org/wiki/Median)*: the value such that the set of values less than the median, and the set greater than the median, each have probabilities no greater than one-half.
- [*Mode*](https://en.wikipedia.org/wiki/Mode_(statistics) "Mode (statistics)"): for a discrete random variable, the value with highest probability; for an absolutely continuous random variable, a location at which the probability density function has a local peak.
- *[Quantile](https://en.wikipedia.org/wiki/Quantile)*: the q-quantile is the value $x$ such that $P(X<x)=q$.
- *[Variance](https://en.wikipedia.org/wiki/Variance)*: the second moment of the pmf or pdf about the mean; an important measure of the [dispersion](https://en.wikipedia.org/wiki/Statistical_dispersion) of the distribution.
- *[Standard deviation](https://en.wikipedia.org/wiki/Standard_deviation)*: the square root of the variance, and hence another measure of dispersion.
- [*Symmetry*](https://en.wikipedia.org/wiki/Symmetric_probability_distribution): a property of some distributions in which the portion of the distribution to the left of a specific value (usually the median) is a mirror image of the portion to its right.
- *[Skewness](https://en.wikipedia.org/wiki/Skewness)*: a measure of the extent to which a pmf or pdf "leans" to one side of its mean. The third [standardized moment](https://en.wikipedia.org/wiki/Standardized_moment) of the distribution.
- *[Kurtosis](https://en.wikipedia.org/wiki/Kurtosis)*: a measure of the "fatness" of the tails of a pmf or pdf. The fourth standardized moment of the distribution.

## Cumulative distribution function

In the special case of a real-valued random variable, the probability distribution can equivalently be represented by a cumulative distribution function instead of a probability measure. The cumulative distribution function of a random variable $X$ with regard to a probability distribution $p$ is defined as 

$$
F(x)=P(X\leq x).
$$

The cumulative distribution function of any real-valued random variable has the properties:

- 
- $F(x)$ is non-decreasing;
- 
- $F(x)$ is [right-continuous](https://en.wikipedia.org/wiki/Right-continuous);
- 
- $0\leq F(x)\leq 1$;
- 
- $\lim _{x\to -\infty }F(x)=0$ and $\lim _{x\to \infty }F(x)=1$; and
- 
- $\Pr(a<X\leq b)=F(b)-F(a)$.

Conversely, any function $F:\mathbb {R} \to \mathbb {R}$ that satisfies the first four of the properties above is the cumulative distribution function of some probability distribution on the real numbers.

Any probability distribution can be decomposed as the [mixture](https://en.wikipedia.org/wiki/Mixture_distribution) of a [discrete](https://en.wikipedia.org/wiki/Discrete_probability_distribution), an [absolutely continuous](https://en.wikipedia.org/wiki/Absolutely_continuous_probability_distribution) and a [singular continuous distribution](https://en.wikipedia.org/wiki/Singular_distribution), and thus any cumulative distribution function admits a decomposition as the [convex sum](https://en.wikipedia.org/wiki/Convex_sum) of the three according cumulative distribution functions.

## Discrete probability distribution

![[media/b30fa29ae9e20df54c2e704f19d40b88b473346b.png]]
Figure 3: The [probability mass function](https://en.wikipedia.org/wiki/Probability_mass_function) (pmf) $p(S)$ specifies the probability distribution for the sum $S$ of counts from two [dice](https://en.wikipedia.org/wiki/Dice). For example, the figure shows that $p(11)=2/36=1/18$. The pmf allows the computation of probabilities of events such as $P(X>9)=1/12+1/18+1/36=1/6$, and all other probabilities in the distribution.

![[media/9a9f60d67bd3c642f4564597a5c023e862f723e9.png]]
Figure 4: The probability mass function of a discrete probability distribution. The probabilities of the [singletons](https://en.wikipedia.org/wiki/Singleton_(mathematics)) {1}, {3}, and {7} are respectively 0.2, 0.5, 0.3. A set not containing any of these points has probability zero.

![[media/ecb6c175f2ed9f1796161dd29e426d5d1893e2a4.png]]
Figure 5: The [[Cumulative Distribution Function|cdf]] of a discrete probability distribution, ...

![[media/e6897dce89fed311bba447e70e067700a4ea8ac0.png]]
Figure 6: ... of a continuous probability distribution, ...

![[media/8667ec4175d50764decfbe2690e50aaf1314a12e.png]]
Figure 7: ... of a distribution which has both a continuous part and a discrete part

A **discrete probability distribution** is the probability distribution of a random variable that can take on only a countable number of values ([almost surely](https://en.wikipedia.org/wiki/Almost_surely)) which means that the probability of any event $E$ can be expressed as a (finite or [countably infinite](https://en.wikipedia.org/wiki/Series_(mathematics) "Series (mathematics)")) sum: 

$$
P(X\in E)=\sum _{\omega \in A\cap E}P(X=\omega ),
$$

 where $A$ is a countable set with $P(X\in A)=1$. Thus the discrete random variables (i.e. random variables whose probability distribution is discrete) are exactly those with a [probability mass function](https://en.wikipedia.org/wiki/Probability_mass_function) $p(x)=P(X=x)$. In the case where the range of values is countably infinite, these values have to decline to zero fast enough for the probabilities to add up to 1. For example, if $p(n)={\tfrac {1}{2^{n}}}$ for $n=1,2,...$, the sum of probabilities would be $1/2+1/4+1/8+\dots =1$.

Well-known discrete probability distributions used in statistical modeling include the [Poisson distribution](https://en.wikipedia.org/wiki/Poisson_distribution), the [Bernoulli distribution](https://en.wikipedia.org/wiki/Bernoulli_distribution), the [binomial distribution](https://en.wikipedia.org/wiki/Binomial_distribution), the [geometric distribution](https://en.wikipedia.org/wiki/Geometric_distribution), the [negative binomial distribution](https://en.wikipedia.org/wiki/Negative_binomial_distribution) and [categorical distribution](https://en.wikipedia.org/wiki/Categorical_distribution). When a [sample](https://en.wikipedia.org/wiki/Sample_(statistics)) (a set of observations) is drawn from a larger population, the sample points have an [empirical distribution](https://en.wikipedia.org/wiki/Empirical_distribution_function) that is discrete, and which provides information about the population distribution. Additionally, the [discrete uniform distribution](https://en.wikipedia.org/wiki/Uniform_distribution_(discrete)) is commonly used in computer programs that make equal-probability random selections between a number of choices.

### Cumulative distribution function

A real-valued discrete random variable can equivalently be defined as a random variable whose cumulative distribution function increases only by [jump discontinuities](https://en.wikipedia.org/wiki/Jump_discontinuity)—that is, its cdf increases only where it "jumps" to a higher value, and is constant in intervals without jumps. The points where jumps occur are precisely the values which the random variable may take. Thus the cumulative distribution function has the form 

$$
F(x)=P(X\leq x)=\sum _{\omega \leq x}p(\omega ).
$$

 The points where the cdf jumps always form a countable set; this may be any countable set and thus may even be dense in the real numbers.

### Dirac delta representation

A discrete probability distribution is often represented with [Dirac measures](https://en.wikipedia.org/wiki/Dirac_measure), also called one-point distributions (see below), the probability distributions of [deterministic random variables](https://en.wikipedia.org/wiki/Degenerate_distribution). For any outcome $\omega$, let $\delta _{\omega }$ be the Dirac measure concentrated at $\omega$. Given a discrete probability distribution, there is a countable set $A$ with $P(X\in A)=1$ and a probability mass function $p$. If $E$ is any event, then 

$$
P(X\in E)=\sum _{\omega \in A}p(\omega )\delta _{\omega }(E),
$$

 or in short, 

$$
P_{X}=\sum _{\omega \in A}p(\omega )\delta _{\omega }.
$$

Similarly, discrete distributions can be represented with the [Dirac delta function](https://en.wikipedia.org/wiki/Dirac_delta_function) as a [generalized](https://en.wikipedia.org/wiki/Generalized_function) [[Probability Density Function]] $f$, where 

$$
f(x)=\sum _{\omega \in A}p(\omega )\delta (x-\omega ),
$$

 which means 

$$
P(X\in E)=\int _{E}f(x)\,dx=\sum _{\omega \in A}p(\omega )\int _{E}\delta (x-\omega )=\sum _{\omega \in A\cap E}p(\omega )
$$

 for any event $E.$

### Indicator-function representation

For a discrete random variable $X$, let $u_{0},u_{1},\dots$ be the values it can take with non-zero probability. Denote 

$$
\Omega _{i}=X^{-1}(u_{i})=\{\omega :X(\omega )=u_{i}\},\,i=0,1,2,\dots
$$

 These are [disjoint sets](https://en.wikipedia.org/wiki/Disjoint_set), and for such sets 

$$
P\left(\bigcup _{i}\Omega _{i}\right)=\sum _{i}P(\Omega _{i})=\sum _{i}P(X=u_{i})=1.
$$

 It follows that the probability that $X$ takes any value except for $u_{0},u_{1},\dots$ is zero, and thus one can write $X$ as 

$$
X(\omega )=\sum _{i}u_{i}1_{\Omega _{i}}(\omega )
$$

 except on a set of probability zero, where $1_{A}$ is the indicator function of $A$. This may serve as an alternative definition of discrete random variables.

### One-point distribution

A special case is the discrete distribution of a random variable that can take on only one fixed value, in other words, a Dirac measure. Expressed formally, the random variable $X$ has a one-point distribution if it has a possible outcome $x$ such that $P(X{=}x)=1.$ All other possible outcomes then have probability 0. Its cumulative distribution function jumps immediately from 0 before $x$ to 1 at $x$. It is closely related to a deterministic distribution, which cannot take on any other value, while a one-point distribution can take other values, though only with probability 0. For most practical purposes the two notions are equivalent.

## Absolutely continuous probability distribution

An **absolutely continuous probability distribution** is a probability distribution on the real numbers with uncountably many possible values, such as a whole interval in the real line, and where the probability of any event can be expressed as an integral. More precisely, a real random variable $X$ has an [absolutely continuous](https://en.wikipedia.org/wiki/Absolutely_continuous) probability distribution if there is a function $f:\mathbb {R} \to [0,\infty ]$ such that for each interval $I=[a,b]\subset \mathbb {R}$ the probability of $X$ belonging to $I$ is given by the integral of $f$ over $I$: 

$$
P\left(a\leq X\leq b\right)=\int _{a}^{b}f(x)\,dx.
$$

 This is the definition of a [[Probability Density Function]], so that absolutely continuous probability distributions are exactly those with a probability density function. In particular, the probability for $X$ to take any single value $a$ (that is, $a\leq X\leq a$) is zero, because an [integral](https://en.wikipedia.org/wiki/Integral) with coinciding upper and lower limits is always equal to zero. If the interval $[a,b]$ is replaced by any measurable set $A$, the according equality still holds: 

$$
P(X\in A)=\int _{A}f(x)\,dx.
$$

An **absolutely continuous random variable** is a random variable whose probability distribution is absolutely continuous.

There are many examples of absolutely continuous probability distributions: [normal](https://en.wikipedia.org/wiki/Normal_distribution), [uniform](https://en.wikipedia.org/wiki/Uniform_distribution_(continuous)), [chi-squared](https://en.wikipedia.org/wiki/Chi-squared_distribution), and [others](https://en.wikipedia.org/wiki/List_of_probability_distributions#Absolutely_continuous_distributions).

### Cumulative distribution function

Absolutely continuous probability distributions as defined above are precisely those with an [absolutely continuous](https://en.wikipedia.org/wiki/Absolute_continuity) cumulative distribution function. In this case, the cumulative distribution function $F$ has the form 

$$
F(x)=P(X\leq x)=\int _{-\infty }^{x}f(t)\,dt
$$

 where $f$ is a density of the random variable $X$ with regard to the distribution $P$.

*Note on terminology:* Absolutely continuous distributions ought to be distinguished from **continuous distributions**, which are those having a continuous cumulative distribution function. Every absolutely continuous distribution is a continuous distribution but the inverse is not true, there exist [singular distributions](https://en.wikipedia.org/wiki/Singular_distribution), which are neither absolutely continuous nor discrete nor a mixture of those, and do not have a density. An example is given by the [Cantor distribution](https://en.wikipedia.org/wiki/Cantor_distribution). Some authors however use the term "continuous distribution" to denote all distributions whose cumulative distribution function is [absolutely continuous](https://en.wikipedia.org/wiki/Absolutely_continuous_function), i.e. refer to absolutely continuous distributions as continuous distributions.

For a more general definition of density functions and the equivalent absolutely continuous measures see [absolutely continuous measure](https://en.wikipedia.org/wiki/Absolutely_continuous_measure).

## Kolmogorov definition

In the [measure-theoretic](https://en.wikipedia.org/wiki/Measure_theory) formalization of [probability theory](https://en.wikipedia.org/wiki/Probability_theory), a [random variable](https://en.wikipedia.org/wiki/Random_variable) is defined as a [measurable function](https://en.wikipedia.org/wiki/Measurable_function) $X$ from a [probability space](https://en.wikipedia.org/wiki/Probability_space) $(\Omega ,{\mathcal {F}},\mathbb {P} )$ to a [measurable space](https://en.wikipedia.org/wiki/Measurable_space) $({\mathcal {X}},{\mathcal {A}})$. Given that probabilities of events of the form $\{\omega \in \Omega \mid X(\omega )\in A\}$ satisfy [[Probability Axioms|Kolmogorov's probability axioms]], the **probability distribution of $X$** is the [image measure](https://en.wikipedia.org/wiki/Pushforward_measure) $X_{*}\mathbb {P}$ of $X$ , which is a [probability measure](https://en.wikipedia.org/wiki/Probability_measure) on $({\mathcal {X}},{\mathcal {A}})$ satisfying $X_{*}\mathbb {P} =\mathbb {P} X^{-1}$.

## Other kinds of distributions

![[media/7c571f52a96ef47045e86d771bebf3627bb0c7a1.png]]
Figure 8: One solution for the [Rabinovich–Fabrikant equations](https://en.wikipedia.org/wiki/Rabinovich%E2%80%93Fabrikant_equations). What is the probability of observing a state on a certain place of the support (i.e., the red subset)?

Absolutely continuous and discrete distributions with support on $\mathbb {R} ^{k}$ or $\mathbb {N} ^{k}$ are extremely useful to model a myriad of phenomena, since most practical distributions are supported on relatively simple subsets, such as [hypercubes](https://en.wikipedia.org/wiki/Hypercubes) or [balls](https://en.wikipedia.org/wiki/Ball_(mathematics) "Ball (mathematics)"). However, this is not always the case, and there exist phenomena with supports that are actually complicated curves $\gamma :[a,b]\rightarrow \mathbb {R} ^{n}$ within some space $\mathbb {R} ^{n}$ or similar. In these cases, the probability distribution is supported on the image of such curve, and is likely to be determined empirically, rather than finding a closed formula for it.

One example is shown in the figure to the right, which displays the evolution of a [system of differential equations](https://en.wikipedia.org/wiki/System_of_differential_equations) (commonly known as the [Rabinovich–Fabrikant equations](https://en.wikipedia.org/wiki/Rabinovich%E2%80%93Fabrikant_equations)) that can be used to model the behaviour of [Langmuir waves](https://en.wikipedia.org/wiki/Langmuir_waves) in [plasma](https://en.wikipedia.org/wiki/Plasma_(physics) "Plasma (physics)"). When this phenomenon is studied, the observed states from the subset are as indicated in red. So one could ask what is the probability of observing a state in a certain position of the red subset; if such a probability exists, it is called the probability measure of the system.

This kind of complicated support appears quite frequently in [dynamical systems](https://en.wikipedia.org/wiki/Dynamical_systems). It is not simple to establish that the system has a probability measure, and the main problem is the following. Let $t_{1}\ll t_{2}\ll t_{3}$ be instants in time and $O$ a subset of the support; if the probability measure exists for the system, one would expect the frequency of observing states inside set $O$ would be equal in interval $[t_{1},t_{2}]$ and $[t_{2},t_{3}]$, which might not happen; for example, it could oscillate similar to a sine, $\sin(t)$, whose limit when $t\rightarrow \infty$ does not converge. Formally, the measure exists only if the limit of the relative frequency converges when the system is observed into the infinite future. The branch of dynamical systems that studies the existence of a probability measure is [ergodic theory](https://en.wikipedia.org/wiki/Ergodic_theory).

Note that even in these cases, the probability distribution, if it exists, might still be termed "absolutely continuous" or "discrete" depending on whether the support is uncountable or countable, respectively.

## Lebesgue decomposition

The [Lebesgue decomposition theorem](https://en.wikipedia.org/wiki/Lebesgue_decomposition_theorem) states that any probability distribution on the real line can be uniquely decomposed into a mixture of three fundamental types: $F=\alpha F_{\text{discrete}}+\beta F_{\text{ac}}+\gamma F_{\text{singular}}$ where coefficients $\alpha ,\beta ,\gamma \in [0,1]$ sum to 1. The three components are:

- **[Discrete](https://en.wikipedia.org/wiki/Discrete_probability_distribution):** The probability is concentrated on a countable set of values (points). The cumulative distribution function (CDF) is a step function.
- **[Absolutely continuous](https://en.wikipedia.org/wiki/Absolutely_continuous_probability_distribution):** The distribution has a [[Probability Density Function]] $f(x)$ such that $F(x)=\int _{-\infty }^{x}f(t)\,dt$. The set of values with non-zero probability density has [Lebesgue measure](https://en.wikipedia.org/wiki/Lebesgue_measure) greater than zero.
- **[Singular continuous](https://en.wikipedia.org/wiki/Singular_distribution):** The CDF is continuous everywhere, but its derivative is zero [almost everywhere](https://en.wikipedia.org/wiki/Almost_everywhere) (with respect to Lebesgue measure). The probability is concentrated on a set of measure zero (e.g., the [Cantor set](https://en.wikipedia.org/wiki/Cantor_set)). A classic example is the [Cantor distribution](https://en.wikipedia.org/wiki/Cantor_distribution).

Most standard distributions in statistical applications are either purely discrete ($\alpha =1$) or purely absolutely continuous ($\beta =1$). Singular distributions rarely appear in applied statistics but are important in the theory of [stochastic processes](https://en.wikipedia.org/wiki/Stochastic_processes) and [fractals](https://en.wikipedia.org/wiki/Fractal).

## Random number generation

Most algorithms are based on a [pseudorandom number generator](https://en.wikipedia.org/wiki/Pseudorandom_number_generator) that produces numbers $X$ that are uniformly distributed in the [half-open interval](https://en.wikipedia.org/wiki/Half-open_interval) \[0, 1). These [random variates](https://en.wikipedia.org/wiki/Random_variate) $X$ are then transformed via some algorithm to create a new random variate having the required probability distribution. With this source of uniform pseudo-randomness, realizations of any random variable can be generated.

For example, suppose U has a uniform distribution between 0 and 1. To construct a random Bernoulli variable for some 0 \< p \< 1, define 

$$
X={\begin{cases}1&{\text{if }}U<p\\0&{\text{if }}U\geq p.\end{cases}}
$$

 We thus have 

$$
P(X=1)=P(U<p)=p,\quad P(X=0)=P(U\geq p)=1-p.
$$

 Therefore, the random variable X has a Bernoulli distribution with parameter p.

This method can be adapted to generate real-valued random variables with any distribution: for be any cumulative distribution function F, let *F*<sup>inv</sup> be the generalized left inverse of $F,$ also known in this context as the *[quantile function](https://en.wikipedia.org/wiki/Quantile_function)* or *inverse distribution function*: 

$$
F^{\mathrm {inv} }(p)=\inf\{x\in \mathbb {R} :p\leq F(x)\}.
$$

 Then, *F*<sup>inv</sup>(*p*) ≤ *x* if and only if *p* ≤ *F*(*x*). As a result, if U is uniformly distributed on \[0, 1\], then the cumulative distribution function of *X* = *F*<sup>inv</sup>(*U*) is F.

For example, suppose we want to generate a random variable having an exponential distribution with parameter $\lambda$ — that is, with cumulative distribution function $F:x\mapsto 1-e^{-\lambda x}.$ 

$$
{\begin{aligned}F(x)=u&\Leftrightarrow 1-e^{-\lambda x}=u\\[2pt]&\Leftrightarrow e^{-\lambda x}=1-u\\[2pt]&\Leftrightarrow -\lambda x=\ln(1-u)\\[2pt]&\Leftrightarrow x={\frac {-1}{\lambda }}\ln(1-u)\end{aligned}}
$$

 so $F^{\mathrm {inv} }(u)=-{\tfrac {1}{\lambda }}\ln(1-u)$, and if U has a uniform distribution on \[0, 1) then $X=-{\tfrac {1}{\lambda }}\ln(1-U)$ has an exponential distribution with parameter $\lambda .$

Although from a theoretical point of view this method always works, in practice the inverse distribution function is unknown and/or cannot be computed efficiently. In this case, other methods (such as the [[Monte Carlo Method]]) are used.

## Common probability distributions and their applications

The concept of the probability distribution and the random variables which they describe underlies the mathematical discipline of probability theory, and the science of statistics. There is spread or variability in almost any value that can be measured in a population (e.g. height of people, durability of a metal, sales growth, traffic flow, etc.); almost all measurements are made with some intrinsic error; in physics, many processes are described probabilistically, from the [kinetic properties of gases](https://en.wikipedia.org/wiki/Kinetic_theory_of_gases) to the [quantum mechanical](https://en.wikipedia.org/wiki/Quantum_mechanical) description of [fundamental particles](https://en.wikipedia.org/wiki/Fundamental_particles). For these and many other reasons, simple [numbers](https://en.wikipedia.org/wiki/Number) are often inadequate for describing a quantity, while probability distributions are often more appropriate.

The following is a list of some of the most common probability distributions, grouped by the type of process that they are related to. For a more complete list, see [list of probability distributions](https://en.wikipedia.org/wiki/List_of_probability_distributions), which groups by the nature of the outcome being considered (discrete, absolutely continuous, multivariate, etc.)

All of the univariate distributions below are singly peaked; that is, it is assumed that the values cluster around a single point. In practice, actually observed quantities may cluster around multiple values. Such quantities can be modeled using a [mixture distribution](https://en.wikipedia.org/wiki/Mixture_distribution).

### Linear growth (e.g. errors, offsets)

- [Normal distribution](https://en.wikipedia.org/wiki/Normal_distribution) (Gaussian distribution), for a single such quantity; the most commonly used absolutely continuous distribution

### Exponential growth (e.g. prices, incomes, populations)

- [Log-normal distribution](https://en.wikipedia.org/wiki/Log-normal_distribution), for a single such quantity whose log is [normally](https://en.wikipedia.org/wiki/Normal_distribution) distributed
- [Pareto distribution](https://en.wikipedia.org/wiki/Pareto_distribution), for a single such quantity whose log is [exponentially](https://en.wikipedia.org/wiki/Exponential_distribution) distributed; the prototypical [power law](https://en.wikipedia.org/wiki/Power_law) distribution

### Uniformly distributed quantities

- [Discrete uniform distribution](https://en.wikipedia.org/wiki/Discrete_uniform_distribution), for a finite set of values (e.g. the outcome of a fair dice)
- [Continuous uniform distribution](https://en.wikipedia.org/wiki/Continuous_uniform_distribution), for absolutely continuously distributed values

### Bernoulli trials (yes/no events, with a given probability)

- Basic distributions:
  - [Bernoulli distribution](https://en.wikipedia.org/wiki/Bernoulli_distribution), for the outcome of a single Bernoulli trial (e.g. success/failure, yes/no)
  - [Binomial distribution](https://en.wikipedia.org/wiki/Binomial_distribution), for the number of "positive occurrences" (e.g. successes, yes votes, etc.) given a fixed total number of [independent](https://en.wikipedia.org/wiki/Independent_(statistics)) occurrences
  - [Negative binomial distribution](https://en.wikipedia.org/wiki/Negative_binomial_distribution), for binomial-type observations but where the quantity of interest is the number of failures before a given number of successes occurs
  - [Geometric distribution](https://en.wikipedia.org/wiki/Geometric_distribution), for binomial-type observations but where the quantity of interest is the number of failures before the first success; a special case of the [negative binomial distribution](https://en.wikipedia.org/wiki/Negative_binomial_distribution)
- Related to sampling schemes over a finite population:
  - [Hypergeometric distribution](https://en.wikipedia.org/wiki/Hypergeometric_distribution), for the number of "positive occurrences" (e.g. successes, yes votes, etc.) given a fixed number of total occurrences, using [sampling without replacement](https://en.wikipedia.org/wiki/Sampling_without_replacement)
  - [Beta-binomial distribution](https://en.wikipedia.org/wiki/Beta-binomial_distribution), for the number of "positive occurrences" (e.g. successes, yes votes, etc.) given a fixed number of total occurrences, sampling using a [Pólya urn model](https://en.wikipedia.org/wiki/P%C3%B3lya_urn_model) (in some sense, the "opposite" of [sampling without replacement](https://en.wikipedia.org/wiki/Sampling_without_replacement))

### Categorical outcomes (events with K possible outcomes)

- [Categorical distribution](https://en.wikipedia.org/wiki/Categorical_distribution), for a single categorical outcome (e.g. yes/no/maybe in a survey); a generalization of the [Bernoulli distribution](https://en.wikipedia.org/wiki/Bernoulli_distribution)
- [Multinomial distribution](https://en.wikipedia.org/wiki/Multinomial_distribution), for the number of each type of categorical outcome, given a fixed number of total outcomes; a generalization of the [binomial distribution](https://en.wikipedia.org/wiki/Binomial_distribution)
- [Multivariate hypergeometric distribution](https://en.wikipedia.org/wiki/Multivariate_hypergeometric_distribution), similar to the [multinomial distribution](https://en.wikipedia.org/wiki/Multinomial_distribution), but using [sampling without replacement](https://en.wikipedia.org/wiki/Sampling_without_replacement); a generalization of the [hypergeometric distribution](https://en.wikipedia.org/wiki/Hypergeometric_distribution)

### Poisson process (events that occur independently with a given rate)

- [Poisson distribution](https://en.wikipedia.org/wiki/Poisson_distribution), for the number of occurrences of a Poisson-type event in a given period of time
- [Exponential distribution](https://en.wikipedia.org/wiki/Exponential_distribution), for the time before the next Poisson-type event occurs
- [Gamma distribution](https://en.wikipedia.org/wiki/Gamma_distribution), for the time before the next k Poisson-type events occur

### Absolute values of vectors with normally distributed components

- [Rayleigh distribution](https://en.wikipedia.org/wiki/Rayleigh_distribution), for the distribution of vector magnitudes with Gaussian distributed orthogonal components. Rayleigh distributions are found in RF signals with Gaussian real and imaginary components.
- [Rice distribution](https://en.wikipedia.org/wiki/Rice_distribution), a generalization of the Rayleigh distributions for where there is a stationary background signal component. Found in [Rician fading](https://en.wikipedia.org/wiki/Rician_fading) of radio signals due to multipath propagation and in MR images with noise corruption on non-zero NMR signals.

### Normally distributed quantities operated with sum of squares

- [Chi-squared distribution](https://en.wikipedia.org/wiki/Chi-squared_distribution), the distribution of a sum of squared [standard normal](https://en.wikipedia.org/wiki/Standard_normal) variables; useful e.g. for inference regarding the [sample variance](https://en.wikipedia.org/wiki/Sample_variance) of normally distributed samples (see [chi-squared test](https://en.wikipedia.org/wiki/Chi-squared_test))
- [Student's t distribution](https://en.wikipedia.org/wiki/Student%27s_t_distribution), the distribution of the ratio of a [standard normal](https://en.wikipedia.org/wiki/Standard_normal) variable and the square root of a scaled [chi squared](https://en.wikipedia.org/wiki/Chi_squared_distribution) variable; useful for inference regarding the [mean](https://en.wikipedia.org/wiki/Mean) of normally distributed samples with unknown variance (see [Student's t-test](https://en.wikipedia.org/wiki/Student%27s_t-test))
- [F-distribution](https://en.wikipedia.org/wiki/F-distribution), the distribution of the ratio of two scaled [chi squared](https://en.wikipedia.org/wiki/Chi_squared_distribution) variables; useful e.g. for inferences that involve comparing variances or involving [R-squared](https://en.wikipedia.org/wiki/R-squared) (the squared [correlation coefficient](https://en.wikipedia.org/wiki/Pearson_product-moment_correlation_coefficient))

### As conjugate prior distributions in Bayesian inference

- [Beta distribution](https://en.wikipedia.org/wiki/Beta_distribution), for a single probability (real number between 0 and 1); conjugate to the [Bernoulli distribution](https://en.wikipedia.org/wiki/Bernoulli_distribution) and [binomial distribution](https://en.wikipedia.org/wiki/Binomial_distribution)
- [Gamma distribution](https://en.wikipedia.org/wiki/Gamma_distribution), for a non-negative scaling parameter; conjugate to the rate parameter of a [Poisson distribution](https://en.wikipedia.org/wiki/Poisson_distribution) or [exponential distribution](https://en.wikipedia.org/wiki/Exponential_distribution), the [precision](https://en.wikipedia.org/wiki/Precision_(statistics) "Precision (statistics)") (inverse [variance](https://en.wikipedia.org/wiki/Variance)) of a [normal distribution](https://en.wikipedia.org/wiki/Normal_distribution), etc.
- [Dirichlet distribution](https://en.wikipedia.org/wiki/Dirichlet_distribution), for a vector of probabilities that must sum to 1; conjugate to the [categorical distribution](https://en.wikipedia.org/wiki/Categorical_distribution) and [multinomial distribution](https://en.wikipedia.org/wiki/Multinomial_distribution); generalization of the [beta distribution](https://en.wikipedia.org/wiki/Beta_distribution)
- [Wishart distribution](https://en.wikipedia.org/wiki/Wishart_distribution), for a symmetric [non-negative definite](https://en.wikipedia.org/wiki/Non-negative_definite) matrix; conjugate to the inverse of the [covariance matrix](https://en.wikipedia.org/wiki/Covariance_matrix) of a [[Multivariate Normal Distribution]]; generalization of the [gamma distribution](https://en.wikipedia.org/wiki/Gamma_distribution)

### Some specialized applications of probability distributions

- The [cache language models](https://en.wikipedia.org/wiki/Cache_language_model) and other [statistical language models](https://en.wikipedia.org/wiki/Statistical_Language_Model) used in [natural language processing](https://en.wikipedia.org/wiki/Natural_language_processing) to assign probabilities to the occurrence of particular words and word sequences do so by means of probability distributions.
- In quantum mechanics, the probability density of finding the particle at a given point is proportional to the square of the magnitude of the particle's [wavefunction](https://en.wikipedia.org/wiki/Wavefunction) at that point (see [Born rule](https://en.wikipedia.org/wiki/Born_rule)). Therefore, the probability distribution function of the position of a particle is described by $P_{a\leq x\leq b}(t)=\int _{a}^{b}dx\,|\Psi (x,t)|^{2}$, probability that the particle's position *x* will be in the interval *a* ≤ *x* ≤ *b* in dimension one, and a similar [triple integral](https://en.wikipedia.org/wiki/Triple_integral) in dimension three. This is a key principle of quantum mechanics.
- Probabilistic load flow in [power-flow study](https://en.wikipedia.org/wiki/Power-flow_study) explains the uncertainties of input variables as probability distribution and provides the power flow calculation also in term of probability distribution.
- Prediction of natural phenomena occurrences based on previous [frequency distributions](https://en.wikipedia.org/wiki/Frequency_distribution) such as [tropical cyclones](https://en.wikipedia.org/wiki/Tropical_cyclone), hail, time in between events, etc.

## Fitting

[Probability distribution fitting](https://en.wikipedia.org/wiki/Probability_distribution_fitting) or simply distribution fitting is the fitting of a probability distribution to a series of data concerning the repeated measurement of a variable phenomenon. The aim of distribution fitting is to [predict](https://en.wikipedia.org/wiki/Prediction) the [probability](https://en.wikipedia.org/wiki/Probability) or to [forecast](https://en.wikipedia.org/wiki/Forecasting) the [frequency](https://en.wikipedia.org/wiki/Frequency_(statistics) "Frequency (statistics)") of occurrence of the magnitude of the phenomenon in a certain interval.

There are many probability distributions (see [list of probability distributions](https://en.wikipedia.org/wiki/List_of_probability_distributions)) of which some can be fitted more closely to the observed frequency of the data than others, depending on the characteristics of the phenomenon and of the distribution. The distribution giving a close fit is supposed to lead to good predictions. In distribution fitting, therefore, one needs to select a distribution that suits the data well.

## Convergence

A fundamental concept in probability theory is the [convergence](https://en.wikipedia.org/wiki/Convergence_of_random_variables#Convergence_in_distribution) of sequences of probability distributions. A sequence of probability distributions $(P_{n})$ is said to converge **weakly** (or **in distribution**) to a probability distribution $P$ if $\lim _{n\to \infty }P_{n}(A)=P(A)$ for every set $A$ whose boundary has $P$-probability 0.

Equivalently, using [[Cumulative Distribution Function|cumulative distribution functions]], the sequence $F_{n}$ converges to $F$ if $\lim _{n\to \infty }F_{n}(x)=F(x)$ for every $x$ at which $F$ is continuous.

This concept is essential for the [[Central Limit Theorem]], which states that the probability distribution of the standardized sum of independent and identically distributed random variables converges to the [standard normal distribution](https://en.wikipedia.org/wiki/Normal_distribution), regardless of the underlying distribution of the individual variables.

## See also

- ![[media/1a9c6ad1ccebbc090fc7cd1c94d2142489246997.png]][Mathematics portal](https://en.wikipedia.org/wiki/Portal:Mathematics)

- [Conditional probability distribution](https://en.wikipedia.org/wiki/Conditional_probability_distribution)
- [Empirical probability distribution](https://en.wikipedia.org/wiki/Empirical_probability)
- [Histogram](https://en.wikipedia.org/wiki/Histogram)
- [Joint probability distribution](https://en.wikipedia.org/wiki/Joint_probability_distribution)
- [Probability measure](https://en.wikipedia.org/wiki/Probability_measure)
- [Quasiprobability distribution](https://en.wikipedia.org/wiki/Quasiprobability_distribution)
- [Riemann–Stieltjes integral application to probability theory](https://en.wikipedia.org/wiki/Riemann%E2%80%93Stieltjes_integral#Application_to_probability_theory)

### Lists

- [List of probability distributions](https://en.wikipedia.org/wiki/List_of_probability_distributions)
- [List of statistical topics](https://en.wikipedia.org/wiki/List_of_statistical_topics)

## References

### Citations

1.  ^   Everitt, Brian (2006). *The Cambridge Dictionary of Statistics* (3rd ed.). Cambridge, UK: Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-511-24688-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-511-24688-3). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [161828328](https://search.worldcat.org/oclc/161828328).
2.  Ash, Robert B. (2008). *Basic probability theory* (Dover ed.). Mineola, N.Y.: Dover Publications. pp. 66–69. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-486-46628-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-486-46628-6). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [190785258](https://search.worldcat.org/oclc/190785258).
3.  ^   Evans, Michael; [Rosenthal, Jeffrey S.](https://en.wikipedia.org/wiki/Jeff_Rosenthal) (2010). *Probability and statistics: the science of uncertainty* (2nd ed.). New York: W.H. Freeman and Co. p. 38. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4292-2462-8](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4292-2462-8). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [473463742](https://search.worldcat.org/oclc/473463742).
4.  Durrett, Rick (2019). [Probability: Theory and Examples](https://sites.math.duke.edu/~rtd/PTE/PTE5_011119.pdf) (PDF) (5th ed.). Cambridge University Press. pp. 10–14. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1108473682](https://en.wikipedia.org/wiki/Special:BookSources/978-1108473682). Retrieved 22 December 2025.
5.  ^      [Ross, Sheldon M.](https://en.wikipedia.org/wiki/Sheldon_M._Ross) (2010). *A First Course in Probability*. Pearson. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780136079095](https://en.wikipedia.org/wiki/Special:BookSources/9780136079095).
6.  ^   Dekking, Michel (1946–) (2005). *A Modern Introduction to Probability and Statistics : Understanding why and how*. London, UK: Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-85233-896-1](https://en.wikipedia.org/wiki/Special:BookSources/978-1-85233-896-1). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [262680588](https://search.worldcat.org/oclc/262680588).`{{`[`cite book`](https://en.wikipedia.org/wiki/Template:Cite_book)`}}`: CS1 maint: numeric names: authors list ([link](https://en.wikipedia.org/wiki/Category:CS1_maint:_numeric_names:_authors_list))
7.  ^   ["1.3.6.1. What is a Probability Distribution"](https://www.itl.nist.gov/div898/handbook/eda/section3/eda361.htm). *www.itl.nist.gov*. Retrieved 2020-09-10.
8.  Billingsley, Patrick (1995). *Probability and Measure* (3rd ed.). New York: Wiley. pp. 183–184. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-00710-2](https://en.wikipedia.org/wiki/Special:BookSources/0-471-00710-2).
9.  Walpole, R.E.; Myers, R.H.; Myers, S.L.; Ye, K. (1999). *Probability and statistics for engineers*. Prentice Hall.
10. ^   [DeGroot, Morris H.](https://en.wikipedia.org/wiki/Morris_H._DeGroot); Schervish, Mark J. (2002). *Probability and Statistics*. Addison-Wesley.
11. [Billingsley, Patrick](https://en.wikipedia.org/wiki/Patrick_Billingsley) (1986). *Probability and Measure*. Wiley. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780471804789](https://en.wikipedia.org/wiki/Special:BookSources/9780471804789).
12. Shephard, N.G. (1991). ["From characteristic function to distribution function: a simple framework for the theory"](https://ora.ox.ac.uk/objects/uuid:a4c3ad11-74fe-458c-8d58-6f74511a476c). *Econometric Theory*. **7** (4): 519–529. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1017/S0266466600004746](https://doi.org/10.1017%2FS0266466600004746). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [14668369](https://api.semanticscholar.org/CorpusID:14668369).
13. Chapters 1 and 2 of 
14. ^   More information and examples can be found in the articles [Heavy-tailed distribution](https://en.wikipedia.org/wiki/Heavy-tailed_distribution), [Long-tailed distribution](https://en.wikipedia.org/wiki/Long-tailed_distribution), [fat-tailed distribution](https://en.wikipedia.org/wiki/Fat-tailed_distribution)
15. [Erhan, Çınlar](https://en.wikipedia.org/wiki/Erhan_%C3%87%C4%B1nlar) (2011). *Probability and stochastics*. New York: Springer. p. 57. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780387878584](https://en.wikipedia.org/wiki/Special:BookSources/9780387878584).
16. see [Lebesgue's decomposition theorem](https://en.wikipedia.org/wiki/Lebesgue%27s_decomposition_theorem)
17. [Erhan, Çınlar](https://en.wikipedia.org/wiki/Erhan_%C3%87%C4%B1nlar) (2011). *Probability and stochastics*. New York: Springer. p. 51. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780387878591](https://en.wikipedia.org/wiki/Special:BookSources/9780387878591). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [710149819](https://search.worldcat.org/oclc/710149819).
18. Cohn, Donald L. (1993). *Measure theory*. Birkhäuser.
19. Khuri, André I. (March 2004). "Applications of Dirac's delta function in statistics". *International Journal of Mathematical Education in Science and Technology*. **35** (2): 185–195. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2004IJMES..35..185K](https://ui.adsabs.harvard.edu/abs/2004IJMES..35..185K). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/00207390310001638313](https://doi.org/10.1080%2F00207390310001638313). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0020-739X](https://search.worldcat.org/issn/0020-739X). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [122501973](https://api.semanticscholar.org/CorpusID:122501973).
20. Fisz, Marek (1963). *Probability Theory and Mathematical Statistics* (3rd ed.). John Wiley & Sons. p. 129. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-26250-1](https://en.wikipedia.org/wiki/Special:BookSources/0-471-26250-1). `{{`[`cite book`](https://en.wikipedia.org/wiki/Template:Cite_book)`}}`: ISBN / Date incompatibility ([help](https://en.wikipedia.org/wiki/Help:CS1_errors#invalid_isbn_date))
21. [Rosenthal, Jeffrey](https://en.wikipedia.org/wiki/Jeff_Rosenthal) (2000). *A First Look at Rigorous Probability Theory*. World Scientific.
22. Chapter 3.2 of 
23. Bourne, Murray. ["11. Probability Distributions - Concepts"](https://www.intmath.com/counting-probability/11-probability-distributions-concepts.php). *www.intmath.com*. Retrieved 2020-09-10.
24. [Stroock, Daniel W.](https://en.wikipedia.org/wiki/Daniel_W._Stroock) (1999). *Probability Theory, An Analytic View* (Rev. ed.). Cambridge \[England\]: Cambridge University Press. p. 11. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0521663496](https://en.wikipedia.org/wiki/Special:BookSources/978-0521663496). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [43953136](https://search.worldcat.org/oclc/43953136).
25. [Kolmogorov, Andrey](https://en.wikipedia.org/wiki/Andrey_Kolmogorov) (1950) \[1933\]. *Foundations of the Theory of Probability*. New York, USA: Chelsea Publishing Company. pp. 21–24.
26. Joyce, David (2014). ["Axioms of Probability"](https://mathcs.clarku.edu/~djoyce/ma217/axioms.pdf) (PDF). *Clark University*. Retrieved December 5, 2019.
27. ^   Alligood, Kathleen T.; Sauer, T.D.; Yorke, J.A. (1996). *Chaos: an introduction to dynamical systems*. Springer.
28. Rabinovich, M.I.; Fabrikant, A.L. (1979). "Stochastic self-modulation of waves in nonequilibrium media". *J. Exp. Theor. Phys*. **77**: 617–629. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1979JETP...50..311R](https://ui.adsabs.harvard.edu/abs/1979JETP...50..311R).
29. Section 1.9 of Ross, S.M.; Peköz, E.A. (2007). [A second course in probability](http://people.bu.edu/pekoz/A_Second_Course_in_Probability-Ross-Pekoz.pdf) (PDF).
30. Walters, Peter (2000). *An Introduction to Ergodic Theory*. Springer.
31. Billingsley, Patrick (1995). *Probability and Measure* (3rd ed.). Wiley. pp. 181–182. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-00710-2](https://en.wikipedia.org/wiki/Special:BookSources/0-471-00710-2).
32. ^    Dekking, Frederik Michel; Kraaikamp, Cornelis; Lopuhaä, Hendrik Paul; Meester, Ludolf Erwin (2005), "Why probability and statistics?", *A Modern Introduction to Probability and Statistics*, Springer London, pp. 1–11, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/1-84628-168-7_1](https://doi.org/10.1007%2F1-84628-168-7_1), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-85233-896-1](https://en.wikipedia.org/wiki/Special:BookSources/978-1-85233-896-1)`{{`[`citation`](https://en.wikipedia.org/wiki/Template:Citation)`}}`: CS1 maint: work parameter with ISBN ([link](https://en.wikipedia.org/wiki/Category:CS1_maint:_work_parameter_with_ISBN))
33. [Bishop, Christopher M.](https://en.wikipedia.org/wiki/Christopher_Bishop) (2006). *Pattern recognition and machine learning*. New York: Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-31073-8](https://en.wikipedia.org/wiki/Special:BookSources/0-387-31073-8). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [71008143](https://search.worldcat.org/oclc/71008143).
34. [Chang, Raymond](https://en.wikipedia.org/wiki/Raymond_Chang_(chemist) "Raymond Chang (chemist)"); Thoman, John W. (2014). *Physical Chemistry for the Chemical Sciences*. \[Mill Valley, California\]: University Science Books. pp. 403–406. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-68015-835-9](https://en.wikipedia.org/wiki/Special:BookSources/978-1-68015-835-9). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [927509011](https://search.worldcat.org/oclc/927509011).
35. Chen, P.; Chen, Z.; [Bak-Jensen, B.](https://en.wikipedia.org/wiki/Birgitte_Bak-Jensen) (April 2008). "Probabilistic load flow: A review". *2008 Third International Conference on Electric Utility Deregulation and Restructuring and Power Technologies*. pp. 1586–1591. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/drpt.2008.4523658](https://doi.org/10.1109%2Fdrpt.2008.4523658). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-7-900714-13-8](https://en.wikipedia.org/wiki/Special:BookSources/978-7-900714-13-8). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [18669309](https://api.semanticscholar.org/CorpusID:18669309).
36. Maity, Rajib (2018-04-30). *Statistical methods in hydrology and hydroclimatology*. Singapore. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-981-10-8779-0](https://en.wikipedia.org/wiki/Special:BookSources/978-981-10-8779-0). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [1038418263](https://search.worldcat.org/oclc/1038418263).`{{`[`cite book`](https://en.wikipedia.org/wiki/Template:Cite_book)`}}`: CS1 maint: location missing publisher ([link](https://en.wikipedia.org/wiki/Category:CS1_maint:_location_missing_publisher))
37. Van der Vaart, A. W. (1998). *Asymptotic Statistics*. Cambridge University Press. pp. 2–3. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-78450-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-78450-4).
38. Billingsley, Patrick (1995). *Probability and Measure* (3rd ed.). Wiley. p. 357. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-00710-2](https://en.wikipedia.org/wiki/Special:BookSources/0-471-00710-2).

### Sources

- Vapnik, Vladimir Naumovich (1998). *Statistical Learning Theory*. John Wiley and Sons.

## External links

- ["Probability distribution"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society), 2001 \[1994\]
- [Field Guide to Continuous Probability Distributions](http://threeplusone.com/FieldGuide.pdf), Gavin E. Crooks.
- [Distinguishing probability measure, function and distribution](https://math.stackexchange.com/q/1073744/29780), Math Stack Exchange
