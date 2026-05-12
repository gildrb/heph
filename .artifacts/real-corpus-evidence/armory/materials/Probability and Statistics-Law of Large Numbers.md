[[probability-statistics.base]]

> Source: [[Law of Large Numbers]]
> License: Wikipedia content is available under CC BY-SA 4.0.

![[media/73c39ff2695a9112ed19af0b1fd729c9ebaf543e.png]]
An [illustration](https://en.wikipedia.org/wiki/Illustration) of the law of large numbers using a particular run of rolls of a single [die](https://en.wikipedia.org/wiki/Dice). As the number of rolls in this run increases, the average of the values of all the results approaches 3.5. Although each run would show a distinctive shape over a small number of throws (at the left), over a large number of rolls (to the right) the shapes would be extremely similar.

In [probability theory](https://en.wikipedia.org/wiki/Probability_theory), the **law of large numbers** is a [mathematical law](https://en.wikipedia.org/wiki/Law_(mathematics) "Law (mathematics)") that states that the [average](https://en.wikipedia.org/wiki/Average) of the results obtained from a large number of independent random samples converges to the true value, if it exists. More formally, the law of large numbers states that given a sample of independent and identically distributed values, the sample mean converges to the true [mean](https://en.wikipedia.org/wiki/Mean).

The law of large numbers is important because it guarantees stable long-term results for the averages of some [random](https://en.wikipedia.org/wiki/Randomness) [events](https://en.wikipedia.org/wiki/Event_(probability_theory) "Event (probability theory)"). For example, while a [casino](https://en.wikipedia.org/wiki/Casino) may lose [money](https://en.wikipedia.org/wiki/Money) in a single spin of the [roulette](https://en.wikipedia.org/wiki/Roulette) wheel, its earnings will tend towards a predictable percentage over a large number of spins. Any winning streak by a player will eventually be overcome by the parameters of the game. Importantly, the law applies (as the name indicates) only when a *large number* of observations are considered. There is no principle that a small number of observations will coincide with the expected value or that a streak of one value will immediately be "balanced" by the others (see the [gambler's fallacy](https://en.wikipedia.org/wiki/Gambler%27s_fallacy)).

Throughout its history, many mathematicians have refined this law. Today, the law of large numbers is used in many fields including statistics, probability theory, economics, and insurance.

## Examples

For example, a single roll of a six-sided [dice](https://en.wikipedia.org/wiki/Dice) produces one of the numbers 1, 2, 3, 4, 5, or 6, each with equal [probability](https://en.wikipedia.org/wiki/Probability). Therefore, the [expected value](https://en.wikipedia.org/wiki/Expected_value) of the roll is:

$$
{\frac {1+2+3+4+5+6}{6}}=3.5
$$

According to the law of large numbers, if a large number of six-sided dice are rolled, the average of their values (sometimes called the [sample mean](https://en.wikipedia.org/wiki/Sample_mean)) will approach 3.5, with the precision increasing as more dice are rolled.

It follows from the law of large numbers that the [empirical probability](https://en.wikipedia.org/wiki/Empirical_probability) of success in a series of [Bernoulli trials](https://en.wikipedia.org/wiki/Bernoulli_trial) will converge to the theoretical probability. For a [Bernoulli random variable](https://en.wikipedia.org/wiki/Bernoulli_random_variable), the expected value is the theoretical probability of success, and the average of *n* such variables (assuming they are [independent and identically distributed (i.i.d.)](https://en.wikipedia.org/wiki/Independent_and_identically_distributed_random_variables)) is precisely the relative frequency.

![[media/9749f14b009917e9131226ab84667aac2e40d239.png]]
This image illustrates the convergence of relative frequencies to their theoretical probabilities. The probability of picking a red ball from a sack is 0.4 and black ball is 0.6. The left plot shows the relative frequency of picking a black ball, and the right plot shows the relative frequency of picking a red ball, both over 10,000 trials. As the number of trials increases, the relative frequencies approach their respective theoretical probabilities, demonstrating the law of large numbers.

For example, a [fair coin](https://en.wikipedia.org/wiki/Fair_coin) toss is a Bernoulli trial. When a fair coin is flipped once, the theoretical probability that the outcome will be heads is equal to 1⁄2. Therefore, according to the law of large numbers, the proportion of heads in a "large" number of coin flips "should be" roughly 1⁄2. In particular, the proportion of heads after *n* flips will [almost surely](https://en.wikipedia.org/wiki/Almost_surely) [converge](https://en.wikipedia.org/wiki/Limit_of_a_sequence) to 1⁄2 as *n* approaches infinity.

Although the proportion of heads (and tails) approaches 1⁄2, almost surely the [absolute difference](https://en.wikipedia.org/wiki/Absolute_difference) in the number of heads and tails will become large as the number of flips becomes large. That is, the probability that the absolute difference is a small number approaches zero as the number of flips becomes large. Also, almost surely the ratio of the absolute difference to the number of flips will approach zero. Intuitively, the expected difference grows, but at a slower rate than the number of flips.

Another good example of the law of large numbers is the [[Monte Carlo Method]]. These methods are a broad class of [computational](https://en.wikipedia.org/wiki/Computation) [algorithms](https://en.wikipedia.org/wiki/Algorithm) that rely on repeated [random sampling](https://en.wikipedia.org/wiki/Random_sampling) to obtain numerical results. The larger the number of repetitions, the better the approximation tends to be. The reason that this method is important is mainly that, sometimes, it is difficult or impossible to use other approaches.

## Limitation

The average of the results obtained from a large number of trials may fail to converge in some cases. For instance, the average of *n* results taken from the [Cauchy distribution](https://en.wikipedia.org/wiki/Cauchy_distribution) or some [Pareto distributions](https://en.wikipedia.org/wiki/Pareto_distribution) (α\<1) will not converge as *n* becomes larger; the reason is [heavy tails](https://en.wikipedia.org/wiki/Heavy-tailed_distribution). The Cauchy distribution and the Pareto distribution represent two cases: the Cauchy distribution does not have an expectation, whereas the expectation of the Pareto distribution (*α*\<1) is infinite. One way to generate the Cauchy-distributed example is where the random numbers equal the [tangent](https://en.wikipedia.org/wiki/Tangent) of an angle uniformly distributed between −90° and +90°. The [median](https://en.wikipedia.org/wiki/Median) is zero, but the expected value does not exist, and indeed the average of *n* such variables have the same distribution as one such variable. It does not converge in probability toward zero (or any other value) as *n* goes to infinity.

If the trials embed a [selection bias](https://en.wikipedia.org/wiki/Selection_bias), typical in human economic/rational behaviour, the law of large numbers does not help in solving the bias, even if the number of trials is increased the selection bias remains.

## History

![[media/39fb5acde2f79ea237689532607e9fb612b98dbd.gif]]
[Diffusion](https://en.wikipedia.org/wiki/Molecular_diffusion) is an example of the law of large numbers. Initially, there are [solute](https://en.wikipedia.org/wiki/Solute) molecules on the left side of a barrier (magenta line) and none on the right. The barrier is removed, and the solute diffuses to fill the whole container.

<ul>
<li><em>Top:</em> With a single molecule, the motion appears to be quite random.</li>
<li><em>Middle:</em> With more molecules, there is clearly a trend where the solute fills the container more and more uniformly, but there are also random fluctuations.</li>
<li><em>Bottom:</em> With an enormous number of solute molecules (too many to see), the randomness is essentially gone: The solute appears to move smoothly and systematically from high-concentration areas to low-concentration areas. In realistic situations, chemists can describe diffusion as a deterministic macroscopic phenomenon (see [Fick's laws](https://en.wikipedia.org/wiki/Fick%27s_law)), despite its underlying random nature.</li>
</ul>

The Italian mathematician [Gerolamo Cardano](https://en.wikipedia.org/wiki/Gerolamo_Cardano) (1501–1576) stated without proof that the accuracies of empirical statistics tend to improve with the number of trials. This was then formalized as a law of large numbers. A special form of the law of large numbers (for a binary random variable) was first proved by [Jacob Bernoulli](https://en.wikipedia.org/wiki/Jacob_Bernoulli). It took him over 20 years to develop a sufficiently rigorous mathematical proof which was published in his *[Ars Conjectandi](https://en.wikipedia.org/wiki/Ars_Conjectandi)* (*The Art of Conjecturing*) in 1713. He named this his "golden theorem" but it became generally known as "**Bernoulli's theorem**". This should not be confused with [Bernoulli's principle](https://en.wikipedia.org/wiki/Bernoulli%27s_principle), named after Jacob Bernoulli's nephew [Daniel Bernoulli](https://en.wikipedia.org/wiki/Daniel_Bernoulli). In 1837, [S. D. Poisson](https://en.wikipedia.org/wiki/Sim%C3%A9on_Denis_Poisson) further described it under the name *"la loi des grands nombres"* ("the law of large numbers"). Thereafter, it was known under both names, but the "law of large numbers" is most frequently used.

After Bernoulli and Poisson published their efforts, other mathematicians also contributed to refinement of the law, including [Chebyshev](https://en.wikipedia.org/wiki/Pafnuty_Chebyshev), [Markov](https://en.wikipedia.org/wiki/Andrey_Markov), [Borel](https://en.wikipedia.org/wiki/%C3%89mile_Borel), [Cantelli](https://en.wikipedia.org/wiki/Francesco_Paolo_Cantelli), [Kolmogorov](https://en.wikipedia.org/wiki/Andrey_Kolmogorov) and [Khinchin](https://en.wikipedia.org/wiki/Aleksandr_Khinchin). Markov showed that the law can apply to a random variable that does not have a finite variance under some other weaker assumption, and Khinchin showed in 1929 that if the series consists of independent identically distributed random variables, it suffices that the [expected value](https://en.wikipedia.org/wiki/Expected_value) exists for the weak law of large numbers to be true. These further studies have given rise to two prominent forms of the law of large numbers. One is called the "weak" law and the other the "strong" law, in reference to two different modes of [convergence](https://en.wikipedia.org/wiki/Limit_of_a_sequence) of the cumulative sample means to the expected value; in particular, as explained below, the strong form implies the weak.

## Forms

There are two different versions of the law of large numbers that are described below. They are called the ***strong law** of large numbers* and the ***weak law** of large numbers*. Stated for the case where *X*<sub>1</sub>, *X*<sub>2</sub>, ... is an infinite sequence of [independent and identically distributed (i.i.d.)](https://en.wikipedia.org/wiki/Independent_and_identically_distributed_random_variables) [Lebesgue integrable](https://en.wikipedia.org/wiki/Lebesgue_integration) random variables with expected value E(*X*<sub>1</sub>) = E(*X*<sub>2</sub>) = ... = *μ*, both versions of the law state that the sample average

$$
{\overline {X}}_{n}={\frac {1}{n}}(X_{1}+\cdots +X_{n})
$$

converges to the expected value:

|  |  |  |
|----|----|----|
| 

$$
{\overline {X}}_{n}\to \mu \quad {\textrm {as}}\ n\to \infty .
$$

 |  | 1 |

(Lebesgue integrability of *X<sub>j</sub>* means that the expected value E(*X<sub>j</sub>*) exists according to Lebesgue integration and is finite. It does *not* mean that the associated probability measure is [absolutely continuous](https://en.wikipedia.org/wiki/Absolutely_continuous) with respect to [Lebesgue measure](https://en.wikipedia.org/wiki/Lebesgue_measure).)

Introductory probability texts often additionally assume identical finite [variance](https://en.wikipedia.org/wiki/Variance) $\operatorname {Var} (X_{i})=\sigma ^{2}$ (for all $i$) and no correlation between random variables. In that case, the variance of the average of *n* random variables is

$$
\operatorname {Var} ({\overline {X}}_{n})=\operatorname {Var} ({\tfrac {1}{n}}(X_{1}+\cdots +X_{n}))={\frac {1}{n^{2}}}\operatorname {Var} (X_{1}+\cdots +X_{n})={\frac {n\sigma ^{2}}{n^{2}}}={\frac {\sigma ^{2}}{n}}.
$$

which can be used to shorten and simplify the proofs. This assumption of finite [variance](https://en.wikipedia.org/wiki/Variance) is *not necessary*. Large or infinite variance will make the convergence slower, but the law of large numbers holds anyway.

[Mutual independence](https://en.wikipedia.org/wiki/Independence_(probability_theory)#More_than_two_random_variables "Independence (probability theory)") of the random variables can be replaced by [pairwise independence](https://en.wikipedia.org/wiki/Pairwise_independence) or [exchangeability](https://en.wikipedia.org/wiki/Exchangeable_random_variables) in both versions of the law.

The difference between the strong and the weak version is concerned with the mode of convergence being asserted. For interpretation of these modes, see [Convergence of random variables](https://en.wikipedia.org/wiki/Convergence_of_random_variables).

### Weak law

![[media/5405ceb86c800dc4eb40f0aefe561694127a15c4.png]]

![[media/151bd3cc746cce8b5b402d1a8351eb0147d8841e.gif]]

![[media/5405ceb86c800dc4eb40f0aefe561694127a15c4.png]]

Simulation illustrating the law of large numbers. Each frame, a coin that is red on one side and blue on the other is flipped, and a dot is added in the corresponding column. A pie chart shows the proportion of red and blue so far. Notice that while the proportion varies significantly at first, it approaches 50% as the number of trials increases.

The **weak law of large numbers** (also called [Khinchin](https://en.wikipedia.org/wiki/Aleksandr_Khinchin)'s law) states that given a collection of [independent and identically distributed](https://en.wikipedia.org/wiki/Independent_and_identically_distributed_random_variables) (iid) samples from a random variable with finite mean, the sample mean [converges in probability](https://en.wikipedia.org/wiki/Convergence_in_probability) to the expected value

|  |  |  |
|----|----|----|
| 

$$
{\overline {X}}_{n}\ {\overset {P}{\rightarrow }}\ \mu \qquad {\textrm {when}}\ n\to \infty .
$$

 |  | 2 |

That is, for any positive number *ε*,

$$
\lim _{n\to \infty }\Pr \!\left(\,|{\overline {X}}_{n}-\mu |<\varepsilon \,\right)=1.
$$

Interpreting this result, the weak law states that for any nonzero margin specified (*ε*), no matter how small, with a sufficiently large sample there will be a very high probability that the average of the observations will be close to the expected value; that is, within the margin.

As mentioned earlier, the weak law applies in the case of i.i.d. random variables, but it also applies in some other cases. For example, the variance may be different for each random variable in the series, keeping the expected value constant. If the variances are bounded, then the law applies, as shown by [Chebyshev](https://en.wikipedia.org/wiki/Pafnuty_Chebyshev) as early as 1867. (If the expected values change during the series, then we can simply apply the law to the average deviation from the respective expected values. The law then states that this converges in probability to zero.) In fact, Chebyshev's proof works so long as the variance of the average of the first *n* values goes to zero as *n* goes to infinity. As an example, assume that each random variable in the series follows a [[Gaussian Distribution]] (normal distribution) with mean zero, but with variance equal to $2n/\log(n+1)$, which is not bounded. At each stage, the average will be normally distributed (as the average of a set of normally distributed variables). The variance of the sum is equal to the sum of the variances, which is [asymptotic](https://en.wikipedia.org/wiki/Asymptotic) to $n^{2}/\log n$. The variance of the average is therefore asymptotic to $1/\log n$ and goes to zero.

There are also examples of the weak law applying even though the expected value does not exist.

### Strong law

The **strong law of large numbers** (also called [Kolmogorov](https://en.wikipedia.org/wiki/Andrey_Kolmogorov)'s law) states that the sample average [converges almost surely](https://en.wikipedia.org/wiki/Almost_sure_convergence) to the expected value

|  |  |  |
|----|----|----|
| 

$$
{\overline {X}}_{n}\ {\overset {\text{a.s.}}{\longrightarrow }}\ \mu \qquad {\textrm {when}}\ n\to \infty .
$$

 |  | 3 |

That is,

$$
\Pr \!\left(\lim _{n\to \infty }{\overline {X}}_{n}=\mu \right)=1.
$$

What this means is that, as the number of trials *n* goes to infinity, the probability that the average of the observations converges to the expected value, is equal to one. The modern proof of the strong law is more complex than that of the weak law, and relies on passing to an appropriate sub-sequence.

The strong law of large numbers can itself be seen as a special case of the [pointwise ergodic theorem](https://en.wikipedia.org/wiki/Ergodic_theory#Ergodic_theorems). This view justifies the intuitive interpretation of the expected value (for Lebesgue integration only) of a random variable when sampled repeatedly as the "long-term average".

Law 3 is called the strong law because random variables which converge strongly (almost surely) are guaranteed to converge weakly (in probability). However the weak law is known to hold in certain conditions where the strong law does not hold and then the convergence is only weak (in probability). See [Differences between the weak law and the strong law](#Differences_between_the_weak_law_and_the_strong_law).

The strong law applies to independent identically distributed random variables having an expected value (like the weak law). This was proved by Kolmogorov in 1930. It can also apply in other cases. Kolmogorov also showed, in 1933, that if the variables are independent and identically distributed, then for the average to converge almost surely on *something* (this can be considered another statement of the strong law), it is necessary that they have an expected value (and then of course the average will converge almost surely on that).

If the summands are independent but not identically distributed, then

|  |  |  |
|----|----|----|
| 

$$
{\overline {X}}_{n}-\operatorname {E} {\big [}{\overline {X}}_{n}{\big ]}\ {\overset {\text{a.s.}}{\longrightarrow }}\ 0,
$$

 |  | 2 |

provided that each *X*<sub>*k*</sub> has a finite second moment and

$$
\sum _{k=1}^{\infty }{\frac {1}{k^{2}}}\operatorname {Var} [X_{k}]<\infty .
$$

This statement is known as *Kolmogorov's strong law*, see e.g. , Theorem 2.3.10).

### Differences between the weak law and the strong law

The *weak law* states that for a specified large *n*, the average ${\overline {X}}_{n}$ is likely to be near *μ*. Thus, it leaves open the possibility that $|{\overline {X}}_{n}-\mu |>\varepsilon$ happens an infinite number of times, although at infrequent intervals. (Not necessarily $|{\overline {X}}_{n}-\mu |\neq 0$ for all *n*).

The *strong law* shows that this [almost surely](https://en.wikipedia.org/wiki/Almost_surely) will not occur. I.e., with probability 1 for any *ε* \> 0 the inequality $|{\overline {X}}_{n}-\mu |<\varepsilon$ holds for all large enough *n*.

The strong law does not hold in the following cases, but the weak law does.

1.  Let X be an [exponentially](https://en.wikipedia.org/wiki/Exponential_distribution) distributed random variable with parameter 1. The random variable $\sin(X)e^{X}X^{-1}$ has no expected value according to Lebesgue integration, but using conditional convergence and interpreting the integral as a [Dirichlet integral](https://en.wikipedia.org/wiki/Dirichlet_integral), which is an improper [Riemann integral](https://en.wikipedia.org/wiki/Riemann_integral), we can say: 

$$
E\left({\frac {\sin(X)e^{X}}{X}}\right)=\ \int _{x=0}^{\infty }{\frac {\sin(x)e^{x}}{x}}e^{-x}dx={\frac {\pi }{2}}
$$

2.  Let X be a [geometrically](https://en.wikipedia.org/wiki/Geometric_distribution) distributed random variable with probability 0.5. The random variable $2^{X}(-1)^{X}X^{-1}$ does not have an expected value in the conventional sense because the infinite [series](https://en.wikipedia.org/wiki/Series_(mathematics) "Series (mathematics)") is not absolutely convergent, but using conditional convergence, we can say: 

$$
E\left({\frac {2^{X}(-1)^{X}}{X}}\right)=\ \sum _{x=1}^{\infty }{\frac {2^{x}(-1)^{x}}{x}}2^{-x}=-\ln(2)
$$

3.  If the [[Cumulative Distribution Function]] of a random variable is 

$$
{\begin{cases}1-F(x)&={\frac {e}{2x\ln(x)}},&x\geq e\\F(x)&={\frac {e}{-2x\ln(-x)}},&x\leq -e\end{cases}}
$$

 then it has no expected value, but the weak law is true.
4.  Let *X*<sub>*k*</sub> be plus or minus ${\sqrt {k/\log \log \log k}}$ (starting at sufficiently large *k* so that the denominator is positive) with probability 1⁄2 for each. The variance of *X*<sub>*k*</sub> is then $k/\log \log \log k.$ Kolmogorov's strong law does not apply because the partial sum in his criterion up to *k* = *n* is asymptotic to $\log n/\log \log \log n$ and this is unbounded. If we replace the random variables with Gaussian variables having the same variances, namely ${\sqrt {k/\log \log \log k}}$, then the average at any point will also be normally distributed. The width of the distribution of the average will tend toward zero (standard deviation asymptotic to $1/{\sqrt {2\log \log \log n}}$), but for a given *ε*, there is probability which does not go to zero with *n*, while the average sometime after the *n*th trial will come back up to *ε*. Since the width of the distribution of the average is not zero, it must have a positive lower bound *p*(*ε*), which means there is a probability of at least *p*(*ε*) that the average will attain ε after *n* trials. It will happen with probability *p*(*ε*)/2 before some *m* which depends on *n*. But even after *m*, there is still a probability of at least *p*(*ε*) that it will happen. (This seems to indicate that *p*(*ε*)=1 and the average will attain ε an infinite number of times.)

### Uniform laws of large numbers

There are extensions of the law of large numbers to collections of estimators, where the convergence is uniform over the collection; thus the name *uniform law of large numbers*.

Suppose *f*(*x*,*θ*) is some [function](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)") defined for *θ* ∈ Θ, and continuous in *θ*. Then for any fixed *θ*, the sequence {*f*(*X*<sub>1</sub>,*θ*), *f*(*X*<sub>2</sub>,*θ*), ...} will be a sequence of independent and identically distributed random variables, such that the sample mean of this sequence converges in probability to E\[*f*(*X*,*θ*)\]. This is the *pointwise* (in *θ*) convergence.

A particular example of a **uniform law of large numbers** states the conditions under which the convergence happens *uniformly* in *θ*. If

1.  *Θ* is compact,
2.  *f*(*x*,*θ*) is continuous at each *θ* ∈ Θ for [almost all](https://en.wikipedia.org/wiki/Almost_everywhere) *x*s, and [measurable function](https://en.wikipedia.org/wiki/Measurable_function) of *x* at each *θ*.
3.  there exists a [dominating](https://en.wikipedia.org/wiki/Dominated_convergence_theorem) function *d*(*x*) such that E\[*d*(*X*)\] \< ∞, and 

$$
\left\|f(x,\theta )\right\|\leq d(x)\quad {\text{for all}}\ \theta \in \Theta .
$$

Then E\[*f*(*X*,*θ*)\] is continuous in *θ*, and

$$
\sup _{\theta \in \Theta }\left\|{\frac {1}{n}}\sum _{i=1}^{n}f(X_{i},\theta )-\operatorname {E} [f(X,\theta )]\right\|{\overset {\mathrm {P} }{\rightarrow }}\ 0.
$$

This result is useful to derive consistency of a large class of estimators (see [Extremum estimator](https://en.wikipedia.org/wiki/Extremum_estimator)).

### Borel's law of large numbers

**Borel's law of large numbers**, named after [Émile Borel](https://en.wikipedia.org/wiki/%C3%89mile_Borel), states that if an experiment is repeated a large number of times, independently under identical conditions, then the proportion of times that any specified event is expected to occur approximately equals the probability of the event's occurrence on any particular trial; the larger the number of repetitions, the better the approximation tends to be. More precisely, if *E* denotes the event in question, *p* its probability of occurrence, and *N<sub>n</sub>*(*E*) the number of times *E* occurs in the first *n* trials, then with probability one, 

$$
{\frac {N_{n}(E)}{n}}\to p{\text{ as }}n\to \infty .
$$

This theorem makes rigorous the intuitive notion of probability as the expected long-run relative frequency of an event's occurrence. It is a special case of any of several more general laws of large numbers in probability theory.

## Proof of the weak law

Given *X*<sub>1</sub>, *X*<sub>2</sub>, ... an infinite sequence of [i.i.d.](https://en.wikipedia.org/wiki/I.i.d.) random variables with finite expected value $E(X_{1})=E(X_{2})=\cdots =\mu <\infty$, we are interested in the convergence of the sample average

$$
{\overline {X}}_{n}={\tfrac {1}{n}}(X_{1}+\cdots +X_{n}).
$$

The weak law of large numbers states:

|  |  |  |
|----|----|----|
| 

$$
{\overline {X}}_{n}\ {\overset {P}{\rightarrow }}\ \mu \qquad {\textrm {when}}\ n\to \infty .
$$

 |  | 2 |

### Proof using Chebyshev's inequality assuming finite variance

This proof uses the assumption of finite [variance](https://en.wikipedia.org/wiki/Variance) $\operatorname {Var} (X_{i})=\sigma ^{2}$ (for all $i$). The independence of the random variables implies no correlation between them, and we have that

$$
\operatorname {Var} ({\overline {X}}_{n})=\operatorname {Var} ({\tfrac {1}{n}}(X_{1}+\cdots +X_{n}))={\frac {1}{n^{2}}}\operatorname {Var} (X_{1}+\cdots +X_{n})={\frac {n\sigma ^{2}}{n^{2}}}={\frac {\sigma ^{2}}{n}}.
$$

The common mean μ of the sequence is the mean of the sample average:

$$
E({\overline {X}}_{n})=\mu .
$$

Using [Chebyshev's inequality](https://en.wikipedia.org/wiki/Chebyshev%27s_inequality) on ${\overline {X}}_{n}$ results in

$$
\operatorname {P} (\left|{\overline {X}}_{n}-\mu \right|\geq \varepsilon )\leq {\frac {\sigma ^{2}}{n\varepsilon ^{2}}}.
$$

This may be used to obtain the following:

$$
\operatorname {P} (\left|{\overline {X}}_{n}-\mu \right|<\varepsilon )=1-\operatorname {P} (\left|{\overline {X}}_{n}-\mu \right|\geq \varepsilon )\geq 1-{\frac {\sigma ^{2}}{n\varepsilon ^{2}}}.
$$

As *n* approaches infinity, the expression approaches 1. And by definition of [convergence in probability](https://en.wikipedia.org/wiki/Convergence_in_probability), we have obtained

|  |  |  |
|----|----|----|
| 

$$
{\overline {X}}_{n}\ {\overset {P}{\rightarrow }}\ \mu \qquad {\textrm {when}}\ n\to \infty .
$$

 |  | 2 |

### Proof using convergence of characteristic functions

By [Taylor's theorem](https://en.wikipedia.org/wiki/Taylor%27s_theorem) for [complex functions](https://en.wikipedia.org/wiki/Complex_function), the [characteristic function](https://en.wikipedia.org/wiki/Characteristic_function_(probability_theory) "Characteristic function (probability theory)") of any random variable, *X*, with finite mean μ, can be written as

$$
\varphi _{X}(t)=1+it\mu +o(t),\quad t\rightarrow 0.
$$

All *X*<sub>1</sub>, *X*<sub>2</sub>, ... have the same characteristic function, so we will simply denote this *φ*<sub>*X*</sub>.

Among the basic properties of characteristic functions there are

$$
\varphi _{{\frac {1}{n}}X}(t)=\varphi _{X}({\tfrac {t}{n}})\quad {\text{and}}\quad \varphi _{X+Y}(t)=\varphi _{X}(t)\varphi _{Y}(t)\quad
$$

 if *X* and *Y* are independent.

These rules can be used to calculate the characteristic function of ${\overline {X}}_{n}$ in terms of *φ*<sub>*X*</sub>:

$$
\varphi _{{\overline {X}}_{n}}(t)=\left[\varphi _{X}\left({t \over n}\right)\right]^{n}=\left[1+i\mu {t \over n}+o\left({t \over n}\right)\right]^{n}\,\rightarrow \,e^{it\mu },\quad {\text{as}}\quad n\to \infty .
$$

The limit *e*<sup>*itμ*</sup> is the characteristic function of the constant random variable μ, and hence by the [Lévy continuity theorem](https://en.wikipedia.org/wiki/L%C3%A9vy_continuity_theorem), ${\overline {X}}_{n}$ [converges in distribution](https://en.wikipedia.org/wiki/Convergence_in_distribution) to μ:

$$
{\overline {X}}_{n}\,{\overset {\mathcal {D}}{\rightarrow }}\,\mu \qquad {\text{for}}\qquad n\to \infty .
$$

μ is a constant, which implies that convergence in distribution to μ and convergence in probability to μ are equivalent (see [Convergence of random variables](https://en.wikipedia.org/wiki/Convergence_of_random_variables).) Therefore,

|  |  |  |
|----|----|----|
| 

$$
{\overline {X}}_{n}\ {\overset {P}{\rightarrow }}\ \mu \qquad {\textrm {when}}\ n\to \infty .
$$

 |  | 2 |

This shows that the sample mean converges in probability to the derivative of the characteristic function at the origin, as long as the latter exists.

## Proof of the strong law

We give a relatively simple proof of the strong law under the assumptions that the $X_{i}$ are [iid](https://en.wikipedia.org/wiki/Independent_and_identically_distributed_random_variables), ${\mathbb {E} }[X_{i}]=:\mu <\infty$, $\operatorname {Var} (X_{i})=\sigma ^{2}<\infty$, and ${\mathbb {E} }[X_{i}^{4}]=:\tau <\infty$.

Let us first note that [without loss of generality](https://en.wikipedia.org/wiki/Without_loss_of_generality) we can assume that $\mu =0$ by centering. In this case, the strong law says that

$$
\Pr \!\left(\lim _{n\to \infty }{\overline {X}}_{n}=0\right)=1,
$$

 or 

$$
\Pr \left(\omega :\lim _{n\to \infty }{\frac {S_{n}(\omega )}{n}}=0\right)=1.
$$

 It is equivalent to show that 

$$
\Pr \left(\omega :\lim _{n\to \infty }{\frac {S_{n}(\omega )}{n}}\neq 0\right)=0,
$$

 Note that 

$$
\lim _{n\to \infty }{\frac {S_{n}(\omega )}{n}}\neq 0\iff \exists \epsilon >0,\left|{\frac {S_{n}(\omega )}{n}}\right|\geq \epsilon \ {\mbox{infinitely often}},
$$

 and thus to prove the strong law we need to show that for every $\epsilon >0$, we have 

$$
\Pr \left(\omega :|S_{n}(\omega )|\geq n\epsilon {\mbox{ infinitely often}}\right)=0.
$$

 Define the events $A_{n}=\{\omega :|S_{n}|\geq n\epsilon \}$, and if we can show that 

$$
\sum _{n=1}^{\infty }\Pr(A_{n})<\infty ,
$$

 then the Borel-Cantelli Lemma implies the result. So let us estimate $\Pr(A_{n})$.

We compute 

$$
{\mathbb {E} }[S_{n}^{4}]={\mathbb {E} }\left[\left(\sum _{i=1}^{n}X_{i}\right)^{4}\right]={\mathbb {E} }\left[\sum _{1\leq i,j,k,l\leq n}X_{i}X_{j}X_{k}X_{l}\right].
$$

 We first claim that every term of the form $X_{i}^{3}X_{j},X_{i}^{2}X_{j}X_{k},X_{i}X_{j}X_{k}X_{l}$ where all subscripts are distinct, must have zero expectation. This is because ${\mathbb {E} }[X_{i}^{3}X_{j}]={\mathbb {E} }[X_{i}^{3}]{\mathbb {E} }[X_{j}]$ by independence, and the last term is zero—and similarly for the other terms. Therefore the only terms in the sum with nonzero expectation are ${\mathbb {E} }[X_{i}^{4}]$ and ${\mathbb {E} }[X_{i}^{2}X_{j}^{2}]$. Since the $X_{i}$ are identically distributed, all of these are the same, and moreover ${\mathbb {E} }[X_{i}^{2}X_{j}^{2}]=({\mathbb {E} }[X_{i}^{2}])^{2}$.

There are $n$ terms of the form ${\mathbb {E} }[X_{i}^{4}]$ and $3n(n-1)$ terms of the form $({\mathbb {E} }[X_{i}^{2}])^{2}$, and so 

$$
{\mathbb {E} }[S_{n}^{4}]=n\tau +3n(n-1)\sigma ^{4}.
$$

 Note that the right-hand side is a quadratic polynomial in $n$, and as such there exists a $C>0$ such that ${\mathbb {E} }[S_{n}^{4}]\leq Cn^{2}$ for $n$ sufficiently large. By Markov, 

$$
\Pr(|S_{n}|\geq n\epsilon )\leq {\frac {1}{(n\epsilon )^{4}}}{\mathbb {E} }[S_{n}^{4}]\leq {\frac {C}{\epsilon ^{4}n^{2}}},
$$

 for $n$ sufficiently large, and therefore this series is summable. Since this holds for any $\epsilon >0$, we have established the strong law of large numbers. The proof can be strengthened immensely by dropping all finiteness assumptions on the second and fourth moments. It can also be extended for example to discuss partial sums of distributions without any finite moments. Such proofs use more intricate arguments to prove the same Borel-Cantelli predicate, a strategy attributed to Kolmogorov to conceptually bring the limit inside the probability parentheses.

## Consequences

The law of large numbers provides an expectation of an unknown distribution from a realization of the sequence, but also any feature of the [probability distribution](https://en.wikipedia.org/wiki/Probability_distribution). By applying [Borel's law of large numbers](https://en.wikipedia.org/wiki/Borel%27s_law_of_large_numbers), one could easily obtain the [probability mass function](https://en.wikipedia.org/wiki/Probability_mass_function). For each event in the objective probability mass function, one could approximate the probability of the event's occurrence with the proportion of times that any specified event occurs. The larger the number of repetitions, the better the approximation. As for the continuous case: $C=(a-h,a+h]$, for small positive h. Thus, for large n:

$$
{\frac {N_{n}(C)}{n}}\thickapprox p=P(X\in C)=\int _{a-h}^{a+h}f(x)\,dx\thickapprox 2hf(a)
$$

With this method, one can cover the whole x-axis with a grid (with grid size 2h) and obtain a bar graph which is called a [histogram](https://en.wikipedia.org/wiki/Histogram).

## Applications

One application of the law of large numbers is an important method of approximation known as the [[Monte Carlo Method]], which uses a random sampling of numbers to approximate numerical results. The algorithm to compute an integral of f(x) on an interval \[a, b\] is as follows:

1.  Simulate uniform random variables X<sub>1</sub>, X<sub>2</sub>, …, X<sub>n</sub> which can be done using a software, and use a random number table that gives U<sub>1</sub>, U<sub>2</sub>, …, U<sub>n</sub> independent and identically distributed (i.i.d.) random variables on \[0, 1\]. Then let X<sub>i</sub> = a + (b - a) U<sub>i</sub> for i= 1, 2, …, n. Then X<sub>1</sub>, X<sub>2</sub>, …, X<sub>n</sub> are independent and identically distributed uniform random variables on \[a, b\].
2.  Evaluate f(X<sub>1</sub>), f(X<sub>2</sub>), …, f(X<sub>n</sub>).
3.  Take the average of f(X<sub>1</sub>), f(X<sub>2</sub>), …, f(X<sub>n</sub>) by computing $(b-a){\tfrac {f(X_{1})+f(X_{2})+\dots +f(X_{n})}{n}}$, and then by the strong law of large numbers this converges to $(b-a)\operatorname {E} (f(X_{1}))=(b-a)\int _{a}^{b}f(x){\tfrac {1}{b-a}}\,dx=\int _{a}^{b}f(x){dx}$.

We can find the integral of $f(x)=\cos ^{2}(x){\sqrt {x^{3}+1}}$ on \[-1, 2\]. Using traditional methods to compute this integral is very difficult, so the Monte Carlo method can be used here. Using the above algorithm, we get

$\int _{-1}^{2}f(x)\,dx=0.905$ when n = 25

and

$\int _{-1}^{2}f(x)\,dx=1.028$ when n = 250.

We observe that as n increases, the numerical value also increases. When we get the actual results for the integral we get

$\int _{-1}^{2}f(x)\,dx=1.000194$.

When the LLN was used, the approximation of the integral was closer to its true value, and thus more accurate.

Another example is the integration of $f(x)={\frac {e^{x}-1}{e-1}}$ over \[0, 1\]. Using the Monte Carlo method and the LLN, we can see that as the number of samples increases, the numerical value gets ever closer to 0.4180233.

## See also

- [Asymptotic equipartition property](https://en.wikipedia.org/wiki/Asymptotic_equipartition_property)
- [[Central Limit Theorem]]
- [Infinite monkey theorem](https://en.wikipedia.org/wiki/Infinite_monkey_theorem)
- [Keynes' Treatise on Probability](https://en.wikipedia.org/wiki/A_Treatise_on_Probability)
- [Law of averages](https://en.wikipedia.org/wiki/Law_of_averages)
- [Law of the iterated logarithm](https://en.wikipedia.org/wiki/Law_of_the_iterated_logarithm)
- [Law of truly large numbers](https://en.wikipedia.org/wiki/Law_of_truly_large_numbers)
- [Lindy effect](https://en.wikipedia.org/wiki/Lindy_effect)
- [Regression toward the mean](https://en.wikipedia.org/wiki/Regression_toward_the_mean)
- [Sortition](https://en.wikipedia.org/wiki/Sortition)
- [Strong law of small numbers](https://en.wikipedia.org/wiki/Strong_law_of_small_numbers)

## Notes

1.  ^     Dekking, Michel (2005). [A Modern Introduction to Probability and Statistics](https://archive.org/details/modernintroducti00fmde). Springer. pp. [181](https://archive.org/details/modernintroducti00fmde/page/n191)–190. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9781852338961](https://en.wikipedia.org/wiki/Special:BookSources/9781852338961).
2.  Yao, Kai; Gao, Jinwu (2016). "Law of Large Numbers for Uncertain Random Variables". *IEEE Transactions on Fuzzy Systems*. **24** (3): 615–621. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2016ITFS...24..615Y](https://ui.adsabs.harvard.edu/abs/2016ITFS...24..615Y). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/TFUZZ.2015.2466080](https://doi.org/10.1109%2FTFUZZ.2015.2466080). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1063-6706](https://search.worldcat.org/issn/1063-6706). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [2238905](https://api.semanticscholar.org/CorpusID:2238905).
3.  ^          Sedor, Kelly. ["The Law of Large Numbers and its Applications"](https://www.lakeheadu.ca/sites/default/files/uploads/77/images/Sedor%20Kelly.pdf) (PDF).
4.  Kroese, Dirk P.; Brereton, Tim; Taimre, Thomas; Botev, Zdravko I. (2014). "Why the Monte Carlo method is so important today". *Wiley Interdisciplinary Reviews: Computational Statistics*. **6** (6): 386–392. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1002/wics.1314](https://doi.org/10.1002%2Fwics.1314). [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[1959.4/unsworks_43203](https://hdl.handle.net/1959.4%2Funsworks_43203). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [18521840](https://api.semanticscholar.org/CorpusID:18521840).
5.  Dekking, Michel, ed. (2005). *A modern introduction to probability and statistics: understanding why and how*. Springer texts in statistics. London \[Heidelberg\]: Springer. p. 187. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-85233-896-1](https://en.wikipedia.org/wiki/Special:BookSources/978-1-85233-896-1).
6.  Dekking, Michel (2005). [A Modern Introduction to Probability and Statistics](https://archive.org/details/modernintroducti00fmde). Springer. pp. [92](https://archive.org/details/modernintroducti00fmde/page/n102). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9781852338961](https://en.wikipedia.org/wiki/Special:BookSources/9781852338961).`{{`[`cite book`](https://en.wikipedia.org/wiki/Template:Cite_book)`}}`: CS1 maint: url-status ([link](https://en.wikipedia.org/wiki/Category:CS1_maint:_url-status))
7.  Dekking, Michel (2005). [A Modern Introduction to Probability and Statistics](https://archive.org/details/modernintroducti00fmde). Springer. pp. [63](https://archive.org/details/modernintroducti00fmde/page/n74). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9781852338961](https://en.wikipedia.org/wiki/Special:BookSources/9781852338961).`{{`[`cite book`](https://en.wikipedia.org/wiki/Template:Cite_book)`}}`: CS1 maint: url-status ([link](https://en.wikipedia.org/wiki/Category:CS1_maint:_url-status))
8.  Pitman, E. J. G.; Williams, E. J. (1967). ["Cauchy-Distributed Functions of Cauchy Variates"](https://doi.org/10.1214%2Faoms%2F1177698885). *The Annals of Mathematical Statistics*. **38** (3): 916–918. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/aoms/1177698885](https://doi.org/10.1214%2Faoms%2F1177698885). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0003-4851](https://search.worldcat.org/issn/0003-4851). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2239008](https://www.jstor.org/stable/2239008).
9.  Mlodinow, L. (2008). *The Drunkard's Walk*. New York: Random House. p. 50.
10. Bernoulli, Jakob (1713). "4". *Ars Conjectandi: Usum & Applicationem Praecedentis Doctrinae in Civilibus, Moralibus & Oeconomicis* (in Latin). Translated by Sheynin, Oscar.
11. Poisson names the "law of large numbers" (*la loi des grands nombres*) in: Poisson, S. D. (1837). *Probabilité des jugements en matière criminelle et en matière civile, précédées des règles générales du calcul des probabilitiés* (in French). Paris, France: Bachelier. p. [7](https://archive.org/details/recherchessurla02poisgoog/page/n30). He attempts a two-part proof of the law on pp. 139–143 and pp. 277 ff.
12. Hacking, Ian (1983). "19th-century Cracks in the Concept of Determinism". *Journal of the History of Ideas*. **44** (3): 455–475. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2709176](https://doi.org/10.2307%2F2709176). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2709176](https://www.jstor.org/stable/2709176).
13. Tchebichef, P. (1846). ["Démonstration élémentaire d'une proposition générale de la théorie des probabilités"](https://zenodo.org/record/1448850). *Journal für die reine und angewandte Mathematik* (in French). **1846** (33): 259–267. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1515/crll.1846.33.259](https://doi.org/10.1515%2Fcrll.1846.33.259). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [120850863](https://api.semanticscholar.org/CorpusID:120850863).
14. ^   .
15. ^   [Yuri Prohorov](https://en.wikipedia.org/wiki/Yuri_Vasilyevich_Prokhorov). ["Law of large numbers"](https://www.encyclopediaofmath.org/index.php/Law_of_large_numbers). *Encyclopedia of Mathematics*. EMS Press.
16. Bhattacharya, Rabi; Lin, Lizhen; Patrangenaru, Victor (2016). *A Course in Mathematical Statistics and Large Sample Theory*. Springer Texts in Statistics. New York, NY: Springer New York. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-1-4939-4032-5](https://doi.org/10.1007%2F978-1-4939-4032-5). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4939-4030-1](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4939-4030-1).
17. ^   ["The strong law of large numbers – What's new"](http://terrytao.wordpress.com/2008/06/18/the-strong-law-of-large-numbers/). Terrytao.wordpress.com. 19 June 2008. Retrieved 2012-06-09.
18. Etemadi, N. Z. (1981). ["An elementary proof of the strong law of large numbers"](https://doi.org/10.1007%2FBF01013465). *Wahrscheinlichkeitstheorie Verw Gebiete*. **55** (1): 119–122. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/BF01013465](https://doi.org/10.1007%2FBF01013465). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [122166046](https://api.semanticscholar.org/CorpusID:122166046).
19. Kingman, J. F. C. (April 1978). ["Uses of Exchangeability"](https://doi.org/10.1214%2Faop%2F1176995566). *The Annals of Probability*. **6** (2). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/aop/1176995566](https://doi.org/10.1214%2Faop%2F1176995566). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0091-1798](https://search.worldcat.org/issn/0091-1798).
20. , Chapter 1.4, p. 14
21. , Chapter 17.3, p. 251
22. ^   Yuri Prokhorov. ["Strong law of large numbers"](https://www.encyclopediaofmath.org/index.php/Strong_law_of_large_numbers). *Encyclopedia of Mathematics*.
23. ["What Is the Law of Large Numbers? (Definition) | Built In"](https://builtin.com/data-science/law-of-large-numbers). *builtin.com*. Retrieved 2023-10-20.
24. 25. Lehmann, Erich L.; Romano, Joseph P. (2006-03-30). [Weak law converges to constant](https://books.google.com/books?id=K6t5qn-SEp8C&pg=PA432). Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780387276052](https://en.wikipedia.org/wiki/Special:BookSources/9780387276052).
26. Dguvl Hun Hong; Sung Ho Lee (1998). ["A Note on the Weak Law of Large Numbers for Exchangeable Random Variables"](https://web.archive.org/web/20160701234328/http://www.mathnet.or.kr/mathnet/kms_tex/31810.pdf) (PDF). *Communications of the Korean Mathematical Society*. **13** (2): 385–391. Archived from [the original](http://www.mathnet.or.kr/mathnet/kms_tex/31810.pdf) (PDF) on 2016-07-01. Retrieved 2014-06-28.
27. Mukherjee, Sayan. ["Law of large numbers"](https://web.archive.org/web/20130309032810/http://www.isds.duke.edu/courses/Fall09/sta205/lec/lln.pdf) (PDF). Archived from [the original](http://www.isds.duke.edu/courses/Fall09/sta205/lec/lln.pdf) (PDF) on 2013-03-09. Retrieved 2014-06-28.
28. J. Geyer, Charles. ["Law of large numbers"](http://www.stat.umn.edu/geyer/8112/notes/weaklaw.pdf) (PDF).
29. , Lemma 2.4
30. Jennrich, Robert I. (1969). ["Asymptotic Properties of Non-Linear Least Squares Estimators"](https://doi.org/10.1214%2Faoms%2F1177697731). *The Annals of Mathematical Statistics*. **40** (2): 633–643. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/aoms/1177697731](https://doi.org/10.1214%2Faoms%2F1177697731).
31. Wen, Liu (1991). ["An Analytic Technique to Prove Borel's Strong Law of Large Numbers"](https://www.jstor.org/stable/2323947). *The American Mathematical Monthly*. **98** (2): 146–148. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2323947](https://doi.org/10.2307%2F2323947). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2323947](https://www.jstor.org/stable/2323947).
32. Another proof was given by Etemadi, Nasrollah (1981). ["An elementary proof of the strong law of large numbers"](https://doi.org/10.1007%2FBF01013465). *Zeitschrift für Wahrscheinlichkeitstheorie und verwandte Gebiete*. **55**. Springer: 119–122. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/BF01013465](https://doi.org/10.1007%2FBF01013465). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [122166046](https://api.semanticscholar.org/CorpusID:122166046).
33. For a proof without the added assumption of a finite fourth moment, see Section 22 of Billingsley, Patrick (1979). *Probability and Measure*.
34. ^   Reiter, Detlev (2008), Fehske, H.; Schneider, R.; Weiße, A. (eds.), ["The Monte Carlo Method, an Introduction"](http://link.springer.com/10.1007/978-3-540-74686-7_3), *Computational Many-Particle Physics*, Lecture Notes in Physics, vol. 739, Berlin, Heidelberg: Springer Berlin Heidelberg, pp. 63–78, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-3-540-74686-7_3](https://doi.org/10.1007%2F978-3-540-74686-7_3), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-74685-0](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-74685-0), retrieved 2023-12-08`{{`[`citation`](https://en.wikipedia.org/wiki/Template:Citation)`}}`: CS1 maint: work parameter with ISBN ([link](https://en.wikipedia.org/wiki/Category:CS1_maint:_work_parameter_with_ISBN))

## References

- Grimmett, G. R.; Stirzaker, D. R. (1992). *Probability and Random Processes* (2nd ed.). Oxford: Clarendon Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-19-853665-8](https://en.wikipedia.org/wiki/Special:BookSources/0-19-853665-8).
- Durrett, Richard (1995). *Probability: Theory and Examples* (2nd ed.). Duxbury Press.
- Martin Jacobsen (1992). *Videregående Sandsynlighedsregning* \[*Advanced Probability Theory*\] (in Danish) (3rd ed.). Copenhagen: HCØ-tryk. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [87-91180-71-6](https://en.wikipedia.org/wiki/Special:BookSources/87-91180-71-6).
- Loève, Michel (1977). *Probability theory 1* (4th ed.). Springer.
- Newey, Whitney K.; [McFadden, Daniel](https://en.wikipedia.org/wiki/Daniel_McFadden) (1994). "36". *Large sample estimation and hypothesis testing*. Handbook of econometrics. Vol. IV. Elsevier Science. pp. 2111–2245.
- Ross, Sheldon (2009). *A first course in probability* (8th ed.). Prentice Hall. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-13-603313-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-13-603313-4).
- Sen, P. K; Singer, J. M. (1993). *Large sample methods in statistics*. Chapman & Hall.
- [Seneta, Eugene](https://en.wikipedia.org/wiki/Eugene_Seneta) (2013). "A Tricentenary history of the Law of Large Numbers". *Bernoulli*. **19** (4): 1088–1121. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1309.6488](https://arxiv.org/abs/1309.6488). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3150/12-BEJSP12](https://doi.org/10.3150%2F12-BEJSP12). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [88520834](https://api.semanticscholar.org/CorpusID:88520834).

## External links

- ["Law of large numbers"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society), 2001 \[1994\]
- [Weisstein, Eric W.](https://en.wikipedia.org/wiki/Eric_W._Weisstein) ["Weak Law of Large Numbers"](https://mathworld.wolfram.com/WeakLawofLargeNumbers.html). *[MathWorld](https://en.wikipedia.org/wiki/MathWorld)*.
- [Weisstein, Eric W.](https://en.wikipedia.org/wiki/Eric_W._Weisstein) ["Strong Law of Large Numbers"](https://mathworld.wolfram.com/StrongLawofLargeNumbers.html). *[MathWorld](https://en.wikipedia.org/wiki/MathWorld)*.
- [Animations for the Law of Large Numbers](https://web.archive.org/web/20081110071309/http://animation.yihui.name/prob:law_of_large_numbers) by Yihui Xie using the [R](https://en.wikipedia.org/wiki/R_(programming_language) "R (programming language)") package [animation](https://cran.r-project.org/package=animation)
- [Apple CEO Tim Cook said something that would make statisticians cringe](http://www.businessinsider.com/law-of-large-numbers-tim-cook-2015-2). "We don't believe in such laws as laws of large numbers. This is sort of, uh, old dogma, I think, that was cooked up by somebody \[..\]" said Tim Cook and while: "However, the law of large numbers has nothing to do with large companies, large revenues, or large growth rates. The law of large numbers is a fundamental concept in probability theory and statistics, tying together theoretical probabilities that we can calculate to the actual outcomes of experiments that we empirically perform. *explained [Business Insider](https://en.wikipedia.org/wiki/Business_Insider)*
