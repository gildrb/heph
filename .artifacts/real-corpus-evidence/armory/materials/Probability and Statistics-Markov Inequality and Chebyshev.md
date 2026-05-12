[[probability-statistics.base]]

> Source: [Chebyshev's inequality](https://en.wikipedia.org/wiki/Chebyshev%27s_inequality)
> License: Wikipedia content is available under CC BY-SA 4.0.

In [probability theory](https://en.wikipedia.org/wiki/Probability_theory), **Chebyshev's inequality** (also called the **Bienaymé–Chebyshev inequality**) provides an upper bound on the probability of deviation of a [random variable](https://en.wikipedia.org/wiki/Random_variable) (with finite variance) from its mean. More specifically, the probability that a random variable deviates from its mean by more than $k\sigma$ is at most $1/k^{2}$, where $k$ is any positive constant and $\sigma$ is the [standard deviation](https://en.wikipedia.org/wiki/Standard_deviation) (the square root of the variance).

The rule is often called Chebyshev's theorem, about the range of standard deviations around the mean, in statistics. The inequality has great utility because it can be applied to any probability distribution in which the mean and variance are defined. For example, it can be used to prove the [weak law of large numbers](https://en.wikipedia.org/wiki/Weak_law_of_large_numbers).

Its practical usage is similar to the [68–95–99.7 rule](https://en.wikipedia.org/wiki/68%E2%80%9395%E2%80%9399.7_rule), which applies only to [normal distributions](https://en.wikipedia.org/wiki/Normal_distribution). Chebyshev's inequality is more general, stating that a minimum of just 75% of values must lie within two standard deviations of the mean and 88.88% within three standard deviations for a broad range of different [[Probability Distributions]].

The term *Chebyshev's inequality* may also refer to [Markov's inequality](https://en.wikipedia.org/wiki/Markov%27s_inequality), especially in the context of analysis. They are closely related, and some authors refer to [Markov's inequality](https://en.wikipedia.org/wiki/Markov%27s_inequality) as "Chebyshev's First Inequality," and the similar one referred to on this page as "Chebyshev's Second Inequality."

Chebyshev's inequality is tight in the sense that for each chosen positive constant, there exists a random variable such that the inequality is in fact an equality.

## History

The theorem is named after Russian mathematician [Pafnuty Chebyshev](https://en.wikipedia.org/wiki/Pafnuty_Chebyshev), although it was first formulated by his friend and colleague [Irénée-Jules Bienaymé](https://en.wikipedia.org/wiki/Ir%C3%A9n%C3%A9e-Jules_Bienaym%C3%A9). The theorem was first proved by Bienaymé in 1853 and more generally proved by Chebyshev in 1867. His student [Andrey Markov](https://en.wikipedia.org/wiki/Andrey_Markov) provided another proof in his 1884 Ph.D. thesis.

## Statement

Chebyshev's inequality is usually stated for [random variables](https://en.wikipedia.org/wiki/Random_variable), but can be generalized to a statement about [measure spaces](https://en.wikipedia.org/wiki/Measure_theory).

### Probabilistic statement

Let $X$ (integrable) be a [random variable](https://en.wikipedia.org/wiki/Random_variable) with finite non-zero [variance](https://en.wikipedia.org/wiki/Variance) $\sigma ^{2}$ (and thus finite [expected value](https://en.wikipedia.org/wiki/Expected_value) $\mu$). Then for any [real number](https://en.wikipedia.org/wiki/Real_number) $k>0$,

$\Pr(|X-\mu |\geq k\sigma )\leq {\frac {1}{k^{2}}}.$

Only the case $k>1$ is useful. When $k\leq 1$ the right-hand side $1/k^{2}\geq 1$ and the inequality is trivial as all probabilities are at most 1.

As an example, using $k={\sqrt {2}}$ shows that the probability values lie outside the interval $(\mu -{\sqrt {2}}\sigma ,\mu +{\sqrt {2}}\sigma )$ does not exceed $1/2$. Equivalently, it implies that the probability of values lying within the interval (i.e. its ["coverage"](https://en.wikipedia.org/wiki/Coverage_probability)) is *at least* $1/2$.

For the general case, for any $a>0$,

$\Pr(|X-\mu |\geq a)\leq {\frac {\sigma ^{2}}{a^{2}}}.$

Because it can be applied to completely arbitrary distributions provided they have a known finite mean and variance, the inequality generally gives a poor bound compared to what might be deduced if more aspects are known about the distribution involved.

<table class="wikitable">

$k$
Min. % within $k$ standard<br />
deviations of mean
Max. % beyond $k$ standard<br />
deviations from mean

&#10;
1
0%
100%

√2
50%
50%

1.5
55.55%
44.44%

2
75%
25%

2√2
87.5%
12.5%

3
88.8888%
11.1111%

4
93.75%
6.25%

5
96%
4%

6
97.2222%
2.7778%

7
97.9592%
2.0408%

8
98.4375%
1.5625%

9
98.7654%
1.2346%

10
99%
1%

</table>

### Measure-theoretic statement

Let $(X,\,\Sigma ,\,\mu )$ be a [measure space](https://en.wikipedia.org/wiki/Measure_space), and let $f$ be an [extended real](https://en.wikipedia.org/wiki/Extended_real_number_line)-valued [measurable function](https://en.wikipedia.org/wiki/Measurable_function) defined on $X$. Then for any real number $t>0$ and $0<p<\infty$,

$\mu (\{x\in X\,:\,\,|f(x)|\geq t\})\leq {1 \over t^{p}}\int _{X}|f|^{p}\,d\mu .$

More generally, if $g$ is an extended real-valued measurable function, nonnegative and nondecreasing, with $g(t)\neq 0$ then: <sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

$\mu (\{x\in X\,:\,\,f(x)\geq t\})\leq {1 \over g(t)}\int _{X}g\circ f\,d\mu .$

This statement follows from the [Markov inequality](https://en.wikipedia.org/wiki/Markov_inequality), $\mu (\{x\in X:|F(x)|\geq \varepsilon \})\leq {\frac {1}{\varepsilon }}\int _{X}|F|d\mu$, with $F=g\circ f$ and $\varepsilon =g(t)$, since in this case $\mu (\{x\in X\,:\,\,g\circ f(x)\geq g(t)\})\geq \mu (\{x\in X\,:\,\,f(x)\geq t\})$. The previous statement then follows by defining $g(x)$ as $|x|^{p}$ if $x\geq t$ and $0$ otherwise.

## Example

Suppose we randomly select a journal article from a source with an average of 1000 words per article, with a standard deviation of 200 words. We can then infer that the probability that it has between 600 and 1400 words (i.e. within $k=2$ standard deviations of the mean) must be at least 75%, because there is no more than $1/k^{2}=1/4$ chance to be outside that range, by Chebyshev's inequality. But if we additionally know that the distribution is [normal](https://en.wikipedia.org/wiki/Normal_distribution), we can say there is a 75% chance the word count is between 770 and 1230 (which is an even tighter bound).

## Sharpness of bounds

As shown in the example above, the theorem typically provides rather loose bounds. However, these bounds cannot in general (remaining true for arbitrary distributions) be improved upon. The bounds are sharp for the following example: for any $k\geq 1$,

$X={\begin{cases}-1,&{\text{with probability }}\;\;{\frac {1}{2k^{2}}}\\{\phantom {-}}0,&{\text{with probability }}1-{\frac {1}{k^{2}}}\\+1,&{\text{with probability }}\;\;{\frac {1}{2k^{2}}}\end{cases}}$

For this distribution, the mean is $\mu =0$ and the variance is $\sigma ^{2}={\frac {(-1)^{2}}{2k^{2}}}+0+{\frac {1^{2}}{2k^{2}}}={\frac {1}{k^{2}}}$, so the standard deviation is $\sigma =1/k$ and

$\Pr(|X-\mu |\geq k\sigma )=\Pr(|X|\geq 1)={\frac {1}{k^{2}}}.$

Chebyshev's inequality is an equality for precisely those distributions which are [affine transformations](https://en.wikipedia.org/wiki/Affine_transformation) of this example.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

## Proof

[Markov's inequality](https://en.wikipedia.org/wiki/Markov%27s_inequality) states that for any non-negative real-valued random variable $Y$ and any positive number $a$, we have $\Pr(|Y|\geq a)\leq \mathbb {E} [|Y|]/a$. One way to prove Chebyshev's inequality is to apply Markov's inequality to the random variable $Y=(X-\mu )^{2}$ with $a=(k\sigma )^{2}$:

$\Pr(|X-\mu |\geq k\sigma )=\Pr((X-\mu )^{2}\geq k^{2}\sigma ^{2})\leq {\frac {\mathbb {E} [(X-\mu )^{2}]}{k^{2}\sigma ^{2}}}={\frac {\sigma ^{2}}{k^{2}\sigma ^{2}}}={\frac {1}{k^{2}}}.$

It can also be proved directly using [conditional expectation](https://en.wikipedia.org/wiki/Conditional_expectation):

${\begin{aligned}\sigma ^{2}&=\mathbb {E} {\bigl [}(X-\mu )^{2}{\bigr ]}\\[5pt]&=\mathbb {E} {\Bigl [}(X-\mu )^{2}\;{\Big |}\;k\sigma \leq |X-\mu |{\Bigr ]}\Pr {\bigl [}k\sigma \leq |X-\mu |{\bigr ]}+\mathbb {E} {\Bigl [}(X-\mu )^{2}\;{\Big |}\;k\sigma >|X-\mu |{\Bigr ]}\Pr {\bigl [}k\sigma >|X-\mu |{\bigr ]}\\[5pt]&\geq (k\sigma )^{2}\Pr {\bigl [}k\sigma \leq |X-\mu |{\bigr ]}+0\cdot \Pr {\bigl [}k\sigma >|X-\mu |{\bigr ]}\\[5pt]&=k^{2}\sigma ^{2}\Pr {\bigl [}k\sigma \leq |X-\mu |{\bigr ]}\end{aligned}}$

Chebyshev's inequality then follows by dividing by $k^{2}\sigma ^{2}$. This proof also shows why the bounds are quite loose in typical cases: the conditional expectation on the event where $|X-\mu |<k\sigma$ is thrown away, and the lower bound of $k^{2}\sigma ^{2}$ on the event $|X-\mu |\geq k\sigma$ can be quite poor.

Chebyshev's inequality can also be obtained directly from a simple comparison of areas, starting from the representation of an expected value as the difference of two improper Riemann integrals (at the [drawing](https://en.wikipedia.org/wiki/Expected_value#Uhl2023Bild1) in the [definition of expected value for arbitrary real-valued random variables](https://en.wikipedia.org/wiki/Expected_value#Arbitrary_real-valued_random_variables)).

## Extensions

Several extensions of Chebyshev's inequality have been developed.

### Selberg's inequality

Selberg derived a generalization to arbitrary intervals. Suppose $X$ is a random variable with mean $\mu$ and variance $\sigma ^{2}$. Selberg's inequality states that if $\beta \geq \alpha \geq 0$,

$\Pr(X\in [\mu -\alpha ,\mu +\beta ])\geq {\begin{cases}{\frac {\alpha ^{2}}{\alpha ^{2}+\sigma ^{2}}}&{\text{if }}\alpha (\beta -\alpha )\geq 2\sigma ^{2}\\{\frac {4\alpha \beta -4\sigma ^{2}}{(\alpha +\beta )^{2}}}&{\text{if }}2\alpha \beta \geq 2\sigma ^{2}\geq \alpha (\beta -\alpha )\\0&\sigma ^{2}\geq \alpha \beta \end{cases}}$

When $\alpha =\beta$, this reduces to Chebyshev's inequality. These are known to be the best possible bounds.

### Finite-dimensional vector

Chebyshev's inequality naturally extends to the multivariate setting, where one has $n$ random variables $X_{i}$ with mean $\mu _{i}$ and variance $\sigma _{i}^{2}$. Then the following inequality holds.

$\Pr \left(\sum _{i=1}^{n}(X_{i}-\mu _{i})^{2}\geq k^{2}\sum _{i=1}^{n}\sigma _{i}^{2}\right)\leq {\frac {1}{k^{2}}}$

This is known as the Birnbaum–Raymond–Zuckerman inequality after the authors who proved it for two dimensions. This result can be rewritten in terms of [vectors](https://en.wikipedia.org/wiki/Multivariate_random_variable) $X=(X_{1},X_{2},\ldots )$ with mean $\mu =(\mu _{1},\mu _{2},\ldots )$, standard deviation $\sigma =(\sigma _{1},\sigma _{2},\ldots )$, in the Euclidean norm $||\cdot ||$.

$\Pr(\|X-\mu \|\geq k\|\sigma \|)\leq {\frac {1}{k^{2}}}.$

One can also get a similar [infinite-dimensional Chebyshev's inequality](https://en.wikipedia.org/wiki/Multidimensional_Chebyshev%27s_inequality#Infinite_dimensions). A second related inequality has also been derived by Chen. Let $n$ be the [dimension](https://en.wikipedia.org/wiki/Dimension) of the stochastic vector $X$ and let $\operatorname {E} (X)$ be the mean of $X$. Let $S$ be the [covariance matrix](https://en.wikipedia.org/wiki/Covariance_matrix) and $k>0$. Then

$\Pr \left((X-\operatorname {E} (X))^{T}S^{-1}(X-\operatorname {E} (X))<k\right)\geq 1-{\frac {n}{k}}$

where $Y^{T}$ is the [transpose](https://en.wikipedia.org/wiki/Transpose) of $Y$. The inequality can be written in terms of the [Mahalanobis distance](https://en.wikipedia.org/wiki/Mahalanobis_distance) as

$\Pr \left(d_{S}^{2}(X,\operatorname {E} (X))<k\right)\geq 1-{\frac {n}{k}}$

where the Mahalanobis distance based on $S$ is defined by

$d_{S}(x,y)={\sqrt {(x-y)^{T}S^{-1}(x-y)}}$

Navarro proved that these bounds are sharp, that is, they are the best possible bounds for that regions when we just know the mean and the covariance matrix of $X$.

Stellato et al. showed that this multivariate version of the Chebyshev inequality can be easily derived analytically as a special case of Vandenberghe et al. where the bound is computed by solving a [semidefinite program (SDP).](https://en.wikipedia.org/wiki/Semidefinite_programming)

#### Known correlation

If the variables are independent this inequality can be sharpened.

$\Pr \left(\bigcap _{i=1}^{n}{\frac {|X_{i}-\mu _{i}|}{\sigma _{i}}}\leq k_{i}\right)\geq \prod _{i=1}^{n}\left(1-{\frac {1}{k_{i}^{2}}}\right)$

Berge derived an inequality for two correlated variables $X_{1},X_{2}$. Let $\rho$ be the correlation coefficient between $X_{1}$ and $X_{2}$ and let $\sigma _{i}^{2}$ be the variance of $X_{i}$. Then

$\Pr \left(\bigcap _{i=1}^{2}\left[{\frac {|X_{i}-\mu _{i}|}{\sigma _{i}}}<k\right]\right)\geq 1-{\frac {1+{\sqrt {1-\rho ^{2}}}}{k^{2}}}.$

This result can be sharpened to having different bounds for the two random variables and having asymmetric bounds, as in Selberg's inequality. 

Olkin and Pratt derived an inequality for $n$ correlated variables.

$\Pr \left(\bigcap _{i=1}^{n}{\frac {|X_{i}-\mu _{i}|}{\sigma _{i}}}<k_{i}\right)\geq 1-{\frac {1}{n^{2}}}\left({\sqrt {u}}+{\sqrt {n-1}}{\sqrt {n\sum _{i}{\frac {1}{k_{i}^{2}}}-u}}\right)^{2}$

where the sum is taken over the $n$ variables and

$u=\sum _{i=1}^{n}{\frac {1}{k_{i}^{2}}}+2\sum _{i=1}^{n}\sum _{j<i}{\frac {\rho _{ij}}{k_{i}k_{j}}}$

where $\rho _{ij}$ is the correlation between $X_{i}$ and $X_{j}$.

Olkin and Pratt's inequality was subsequently generalised by Godwin.

### Higher moments

[Mitzenmacher](https://en.wikipedia.org/wiki/Michael_Mitzenmacher) and [Upfal](https://en.wikipedia.org/wiki/Eli_Upfal) note that by applying Markov's inequality to the nonnegative variable $|X-\operatorname {E} (X)|^{n}$, one can get a family of tail bounds

$\Pr \left(|X-\operatorname {E} (X)|\geq k\operatorname {E} (|X-\operatorname {E} (X)|^{n})^{\frac {1}{n}}\right)\leq {\frac {1}{k^{n}}},\qquad k>0,\ n\geq 2.$

For $n=2$ we obtain Chebyshev's inequality. For $k\geq 1,\ n>4$ and assuming that the $n$<sup>th</sup> moment exists, this bound is tighter than Chebyshev's inequality.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup> This strategy, called the [method of moments](https://en.wikipedia.org/wiki/Method_of_moments_(probability_theory) "Method of moments (probability theory)"), is often used to prove tail bounds.

### Exponential moment

A related inequality sometimes known as the exponential Chebyshev's inequality is the inequality

$\Pr(X\geq \varepsilon )\leq e^{-t\varepsilon }\operatorname {E} \left(e^{tX}\right),\qquad t>0.$

Let $K(t)$ be the [cumulant generating function](https://en.wikipedia.org/wiki/Cumulant_generating_function),

$K(t)=\log \left(\operatorname {E} \left(e^{tx}\right)\right).$

Taking the [Legendre–Fenchel transformation](https://en.wikipedia.org/wiki/Legendre%E2%80%93Fenchel_transformation)<sup>\[*[clarification needed](https://en.wikipedia.org/wiki/Wikipedia:Please_clarify)*\]</sup> of $K(t)$ and using the exponential Chebyshev's inequality we have

$-\log(\Pr(X\geq \varepsilon ))\geq \sup _{t}(t\varepsilon -K(t)).$

This inequality may be used to obtain exponential inequalities for unbounded variables.

### Bounded variables

If $\Pr(x)$ has finite support based on the interval $[a,b]$, let $M=\max(|a|,|b|)$, where $|x|$ is the [absolute value](https://en.wikipedia.org/wiki/Absolute_value) of $x$. If the mean of $\Pr(x)$ is zero then for all $k>0$

${\frac {\operatorname {E} (|X|^{r})-k^{r}}{M^{r}}}\leq \Pr(|X|\geq k)\leq {\frac {\operatorname {E} (|X|^{r})}{k^{r}}}.$

The second of these inequalities with $r=2$ is the Chebyshev bound. The first provides a lower bound for the value of $\Pr(x)$.

## Finite samples

### Univariate case

Saw *et al* extended Chebyshev's inequality to cases where the population mean and variance are not known and may not exist, but the sample mean and sample standard deviation from $N$ samples are to be employed to bound the expected value of a new drawing from the same distribution. The following simpler version of this inequality is given by Kabán.

$\Pr(|X-m|\geq ks)\leq {\frac {1}{N+1}}\left\lfloor {\frac {N+1}{N}}\left({\frac {N-1}{k^{2}}}+1\right)\right\rfloor$

where $X$ is a random variable which we have sampled $N$ times, $m$ is the sample mean, $k$ is a constant and $s$ is the sample standard deviation.

This inequality holds even when the population moments do not exist, and when the sample is only [weakly exchangeably](https://en.wikipedia.org/wiki/Exchangeable_random_variables) distributed; this criterion is met for randomised sampling. A table of values for the Saw–Yang–Mo inequality for finite sample sizes ($N<100$) has been determined by Konijn. The table allows the calculation of various confidence intervals for the mean, based on multiples, C, of the standard error of the mean as calculated from the sample. For example, Konijn shows that for $N=59$, the 95 percent [confidence interval](https://en.wikipedia.org/wiki/Confidence_interval) for the mean $m$ is $(m-Cs,m+Cs)$, where $C=4.447\cdot 1.006=4.47$ (this is 2.28 times larger than the value found on the assumption of normality showing the loss on precision resulting from ignorance of the precise nature of the distribution).

An equivalent inequality can be derived in terms of the sample mean instead,

$\Pr(|X-m|\geq km)\leq {\frac {N-1}{N}}{\frac {1}{k^{2}}}{\frac {s^{2}}{m^{2}}}+{\frac {1}{N}}.$

A table of values for the Saw–Yang–Mo inequality for finite sample sizes ($N<100$) has been determined by Konijn.

For fixed $N$ and large $m$ the Saw–Yang–Mo inequality is approximately

$\Pr(|X-m|\geq ks)\leq {\frac {1}{N+1}}.$

Beasley *et al* have suggested a modification of this inequality

$\Pr(|X-m|\geq ks)\leq {\frac {1}{k^{2}(N+1)}}.$

In empirical testing this modification is conservative but appears to have low statistical power. Its theoretical basis currently remains unexplored.

#### Dependence on sample size

The bounds these inequalities give on a finite sample are less tight than those the Chebyshev inequality gives for a distribution. To illustrate this let the sample size $N=100$ and let $k=3$. Chebyshev's inequality states that at most approximately 11.11% of the distribution will lie at least three standard deviations away from the mean. Kabán's version of the inequality for a finite sample states that at most approximately 12.05% of the sample lies outside these limits. The dependence of the confidence intervals on sample size is further illustrated below.

For $N=10$, the 95% confidence interval is approximately ±13.5789 standard deviations.

For $N=100$ the 95% confidence interval is approximately ±4.9595 standard deviations; the 99% confidence interval is approximately ±140.0 standard deviations.

For $N=500$ the 95% confidence interval is approximately ±4.5574 standard deviations; the 99% confidence interval is approximately ±11.1620 standard deviations.

For $N=1000$ the 95% and 99% confidence intervals are approximately ±4.5141 and approximately ±10.5330 standard deviations respectively.

The Chebyshev inequality for the distribution gives 95% and 99% confidence intervals of approximately ±4.472 standard deviations and ±10 standard deviations respectively.

#### Samuelson's inequality

Although Chebyshev's inequality is the best possible bound for an arbitrary distribution, this is not necessarily true for finite samples. [Samuelson's inequality](https://en.wikipedia.org/wiki/Samuelson%27s_inequality) states that all values of a sample must lie within ${\sqrt {N-1}}$ sample standard deviations of the mean.

By comparison, Chebyshev's inequality states that all but a $1/N$ fraction of the sample will lie within ${\sqrt {N}}$ standard deviations of the mean. Since there are $N$ samples, this means that no samples will lie outside ${\sqrt {N}}$ standard deviations of the mean, which is worse than Samuelson's inequality. However, the benefit of Chebyshev's inequality is that it can be applied more generally to get confidence bounds for ranges of standard deviations that do not depend on the number of samples.

#### Semivariances

An alternative method of obtaining sharper bounds is through the use of [semivariances](https://en.wikipedia.org/wiki/Variance#Semivariance) (partial variances). The upper ($\sigma _{+}^{2}$) and lower ($\sigma _{-}^{2}$) semivariances are defined as

$\sigma _{+}^{2}={\frac {\sum _{x>m}(x-m)^{2}}{n-1}},$

$\sigma _{-}^{2}={\frac {\sum _{x<m}(m-x)^{2}}{n-1}},$

where $m$ is the arithmetic mean of the sample and $n$ is the number of elements in the sample.

The variance of the sample is the sum of the two semivariances:

$\sigma ^{2}=\sigma _{+}^{2}+\sigma _{-}^{2}.$

In terms of the lower semivariance Chebyshev's inequality can be written

$\Pr(x\leq m-a\sigma _{-})\leq {\frac {1}{a^{2}}}.$

Putting

$a={\frac {k\sigma }{\sigma _{-}}}.$

Chebyshev's inequality can now be written

$\Pr(x\leq m-k\sigma )\leq {\frac {1}{k^{2}}}{\frac {\sigma _{-}^{2}}{\sigma ^{2}}}.$

A similar result can also be derived for the upper semivariance.

If we put

$\sigma _{u}^{2}=\max(\sigma _{-}^{2},\sigma _{+}^{2}),$

Chebyshev's inequality can be written

$\Pr(|x\leq m-k\sigma |)\leq {\frac {1}{k^{2}}}{\frac {\sigma _{u}^{2}}{\sigma ^{2}}}.$

Because $\sigma _{u}^{2}\leq \sigma ^{2}$, use of the semivariance sharpens the original inequality.

If the distribution is known to be symmetric, then

$\sigma _{+}^{2}=\sigma _{-}^{2}={\frac {1}{2}}\sigma ^{2}$

and

$\Pr(x\leq m-k\sigma )\leq {\frac {1}{2k^{2}}}.$

This result agrees with that derived using standardised variables.

Note  
The inequality with the lower semivariance has been found to be of use in estimating downside risk in finance and agriculture.

### Multivariate case

Stellato et al. simplified the notation and extended the empirical Chebyshev inequality from Saw et al. to the multivariate case. Let $\xi \in \mathbb {R} ^{n_{\xi }}$ be a random variable and let $N\in \mathbb {Z} _{\geq n_{\xi }}$. We draw $N+1$ iid samples of $\xi$ denoted as $\xi ^{(1)},\dots ,\xi ^{(N)},\xi ^{(N+1)}\in \mathbb {R} ^{n_{\xi }}$. Based on the first $N$ samples, we define the empirical mean as $\mu _{N}={\frac {1}{N}}\sum _{i=1}^{N}\xi ^{(i)}$ and the unbiased empirical covariance as $\Sigma _{N}={\frac {1}{N}}\sum _{i=1}^{N}(\xi ^{(i)}-\mu _{N})(\xi ^{(i)}-\mu _{N})^{\top }$. If $\Sigma _{N}$ is nonsingular, then for all $\lambda \in \mathbb {R} _{\geq 0}$ then

${\begin{aligned}&P^{N+1}\left((\xi ^{(N+1)}-\mu _{N})^{\top }\Sigma _{N}^{-1}(\xi ^{(N+1)}-\mu _{N})\geq \lambda ^{2}\right)\\[8pt]\leq {}&\min \left\{1,{\frac {1}{N+1}}\left\lfloor {\frac {n_{\xi }(N+1)(N^{2}-1+N\lambda ^{2})}{N^{2}\lambda ^{2}}}\right\rfloor \right\}.\end{aligned}}$

#### Remarks

In the univariate case, i.e. $n_{\xi }=1$, this inequality corresponds to the one from Saw et al. Moreover, the right-hand side can be simplified by upper bounding the floor function by its argument

$P^{N+1}\left((\xi ^{(N+1)}-\mu _{N})^{\top }\Sigma _{N}^{-1}(\xi ^{(N+1)}-\mu _{N})\geq \lambda ^{2}\right)\leq \min \left\{1,{\frac {n_{\xi }(N^{2}-1+N\lambda ^{2})}{N^{2}\lambda ^{2}}}\right\}.$

As $N\to \infty$, the right-hand side tends to $\min \left\{1,{\frac {n_{\xi }}{\lambda ^{2}}}\right\}$ which corresponds to the [multivariate Chebyshev inequality](#Vector_version) over ellipsoids shaped according to $\Sigma$ and centered in $\mu$.

## Sharpened bounds

Chebyshev's inequality is important because of its applicability to any distribution. As a result of its generality it may not (and usually does not) provide as sharp a bound as alternative methods that can be used if the distribution of the random variable is known. To improve the sharpness of the bounds provided by Chebyshev's inequality a number of methods have been developed; for a review see eg.

### Cantelli's inequality

[Cantelli's inequality](https://en.wikipedia.org/wiki/Cantelli%27s_inequality) due to [Francesco Paolo Cantelli](https://en.wikipedia.org/wiki/Francesco_Paolo_Cantelli) states that for a real random variable ($X$) with mean ($\mu$) and variance ($\sigma ^{2}$)

$\Pr(X-\mu \geq a)\leq {\frac {\sigma ^{2}}{\sigma ^{2}+a^{2}}}$

where $a\geq 0$.

This inequality can be used to prove a one tailed variant of Chebyshev's inequality with $k>0$

$\Pr(X-\mu \geq k\sigma )\leq {\frac {1}{1+k^{2}}}.$

The bound on the one tailed variant is known to be sharp. To see this consider the random variable $X$ that takes the values

$X=1$ with probability ${\frac {\sigma ^{2}}{1+\sigma ^{2}}}$

$X=-\sigma ^{2}$ with probability ${\frac {1}{1+\sigma ^{2}}}.$

Then $\operatorname {E} (X)=0$ and $\operatorname {E} (X^{2})=\sigma ^{2}$ and $\Pr(X<1)=1/(1+\sigma ^{2})$.

#### An application: distance between the mean and the median

The one-sided variant can be used to prove the proposition that for [probability distributions](https://en.wikipedia.org/wiki/Probability_distribution) having an [expected value](https://en.wikipedia.org/wiki/Expected_value) and a [median](https://en.wikipedia.org/wiki/Median), the mean and the median can never differ from each other by more than one [standard deviation](https://en.wikipedia.org/wiki/Standard_deviation). To express this in symbols let $\mu$, $\nu$, and $\sigma$ be respectively the mean, the median, and the standard deviation. Then

$\left|\mu -\nu \right|\leq \sigma .$

There is no need to assume that the variance is finite because this inequality is trivially true if the variance is infinite.

The proof is as follows. Setting $k=1$ in the statement for the one-sided inequality gives:

$\Pr(X-\mu \geq \sigma )\leq {\frac {1}{2}}\implies \Pr(X\geq \mu +\sigma )\leq {\frac {1}{2}}.$

Changing the sign of $X$ and of $\mu$, we get

$\Pr(X\leq \mu -\sigma )\leq {\frac {1}{2}}.$

As the median is by definition any real number $m$ that satisfies the inequalities

$\Pr(X\leq m)\geq {\frac {1}{2}}{\text{ and }}\Pr(X\geq m)\geq {\frac {1}{2}}$

this implies that the median lies within one standard deviation of the mean. A proof using Jensen's inequality also [exists](https://en.wikipedia.org/wiki/Median#Inequality_relating_means_and_medians).

### Bhattacharyya's inequality

Bhattacharyya extended Cantelli's inequality using the third and fourth moments of the distribution.

Let $\mu =0$ and $\sigma ^{2}$ be the variance. Let $\gamma =E[X^{3}]/\sigma ^{3}$ and $\kappa =E[X^{4}]/\sigma ^{4}$.

If $k^{2}-k\gamma -1>0$ then

$\Pr(X>k\sigma )\leq {\frac {\kappa -\gamma ^{2}-1}{(\kappa -\gamma ^{2}-1)(1+k^{2})+(k^{2}-k\gamma -1)}}.$

The necessity of $k^{2}-k\gamma -1>0$ may require $k$ to be reasonably large.

In the case $E[X^{3}]=0$ this simplifies to

$\Pr(X>k\sigma )\leq {\frac {\kappa -1}{\kappa \left(k^{2}+1\right)-2}}\quad {\text{for }}k>1.$

Since ${\frac {\kappa -1}{\kappa \left(k^{2}+1\right)-2}}={\frac {1}{2}}-{\frac {\kappa (k-1)}{2(\kappa -1)}}+O\left((k-1)^{2}\right)$ for $k$ close to 1, this bound improves slightly over Cantelli's bound ${\frac {1}{2}}-{\frac {k-1}{2}}+O\left((k-1)^{2}\right)$ as $\kappa >1$.

wins a factor 2 over Chebyshev's inequality.

### Gauss's inequality

In 1823 [Gauss](https://en.wikipedia.org/wiki/Gauss) showed that for a [distribution with a unique mode](https://en.wikipedia.org/wiki/Unimodal_distribution) at zero,

$\Pr(|X|\geq k)\leq {\frac {4\operatorname {E} (X^{2})}{9k^{2}}}\quad {\text{if}}\quad k^{2}\geq {\frac {4}{3}}\operatorname {E} (X^{2}),$

$\Pr(|X|\geq k)\leq 1-{\frac {k}{{\sqrt {3}}\operatorname {E} (X^{2})}}\quad {\text{if}}\quad k^{2}\leq {\frac {4}{3}}\operatorname {E} (X^{2}).$

### Vysochanskij–Petunin inequality

The Vysochanskij–Petunin inequality generalizes Gauss's inequality, which only holds for deviation from the mode of a unimodal distribution, to deviation from the mean, or more generally, any center. If $X$ is a [unimodal distribution](https://en.wikipedia.org/wiki/Unimodal_distribution) with mean $\mu$ and variance $\sigma ^{2}$, then the inequality states that

$\Pr(|X-\mu |\geq k\sigma )\leq {\frac {4}{9k^{2}}}\quad {\text{if}}\quad k\geq {\sqrt {8/3}}=1.633.$

$\Pr(|X-\mu |\geq k\sigma )\leq {\frac {4}{3k^{2}}}-{\frac {1}{3}}\quad {\text{if}}\quad k\leq {\sqrt {8/3}}.$

For symmetrical unimodal distributions, the median and the mode are equal, so both the Vysochanskij–Petunin inequality and Gauss's inequality apply to the same center. Further, for symmetrical distributions, one-sided bounds can be obtained by noticing that

$\Pr(X-\mu \geq k\sigma )=\Pr(X-\mu \leq -k\sigma )={\frac {1}{2}}\Pr(|X-\mu |\geq k\sigma ).$

The additional fraction of $4/9$ present in these tail bounds lead to better confidence intervals than Chebyshev's inequality. For example, for any symmetrical unimodal distribution, the Vysochanskij–Petunin inequality states that 4/(9 × 3^2) = 4/81 ≈ 4.9% of the distribution lies outside 3 standard deviations of the mode.

### Bounds for specific distributions

DasGupta has shown that if the distribution is known to be normal

$\Pr(|X-\mu |\geq k\sigma )\leq {\frac {1}{3k^{2}}}.$

From DasGupta's inequality it follows that for a normal distribution at least 95% lies within approximately 2.582 standard deviations of the mean. This is less sharp than the true figure (approximately 1.96 standard deviations of the mean).

- DasGupta has determined a set of best possible bounds for a [normal distribution](https://en.wikipedia.org/wiki/Normal_distribution) for this inequality.
- Steliga and Szynal have extended these bounds to the [Pareto distribution](https://en.wikipedia.org/wiki/Pareto_distribution).
- Grechuk et al. developed a general method for deriving the best possible bounds in Chebyshev's inequality for any family of distributions, and any [deviation risk measure](https://en.wikipedia.org/wiki/Deviation_risk_measure) in place of standard deviation. In particular, they derived Chebyshev inequality for distributions with [log-concave](https://en.wikipedia.org/wiki/Logarithmically_concave_function) densities.

## Related inequalities

Several other related inequalities are also known.

### Paley–Zygmund inequality

The Paley–Zygmund inequality gives a lower bound on tail probabilities, as opposed to Chebyshev's inequality which gives an upper bound. Applying it to the square of a random variable, we get

$\Pr(|Z|>\theta {\sqrt {E[Z^{2}]}})\geq {\frac {(1-\theta ^{2})^{2}E[Z^{2}]^{2}}{E[Z^{4}]}}.$

### Haldane's transformation

One use of Chebyshev's inequality in applications is to create confidence intervals for variates with an unknown distribution. [Haldane](https://en.wikipedia.org/wiki/J._B._S._Haldane) noted, using an equation derived by [Kendall](https://en.wikipedia.org/wiki/Maurice_Kendall), that if a variate ($x$) has a zero mean, unit variance and both finite [skewness](https://en.wikipedia.org/wiki/Skewness) ($\gamma$) and [kurtosis](https://en.wikipedia.org/wiki/Kurtosis) ($\kappa$) then the variate can be converted to a normally distributed [standard score](https://en.wikipedia.org/wiki/Standard_score) ($z$):

$z=x-{\frac {\gamma }{6}}(x^{2}-1)+{\frac {x}{72}}[2\gamma ^{2}(4x^{2}-7)-3\kappa (x^{2}-3)]+\cdots$

This transformation may be useful as an alternative to Chebyshev's inequality or as an adjunct to it for deriving confidence intervals for variates with unknown distributions.

While this transformation may be useful for moderately skewed and/or kurtotic distributions, it performs poorly when the distribution is markedly skewed and/or kurtotic.

### He, Zhang and Zhang's inequality

For any collection of n non-negative independent random variables X<sub>i</sub> with expectation 1 

$\Pr \left({\frac {\sum _{i=1}^{n}X_{i}}{n}}-1\geq {\frac {1}{n}}\right)\leq {\frac {7}{8}}.$

## Integral Chebyshev inequality

There is a second (less well known) inequality also named after Chebyshev.

If $f,g:[a,b]\to \mathbb {R}$ are two [monotonic](https://en.wikipedia.org/wiki/Monotonic) [functions](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)") of the same monotonicity, then

${\frac {1}{b-a}}\int _{a}^{b}\!f(x)g(x)\,dx\geq \left[{\frac {1}{b-a}}\int _{a}^{b}\!f(x)\,dx\right]\left[{\frac {1}{b-a}}\int _{a}^{b}\!g(x)\,dx\right].$

If $f$ and $g$ are of opposite monotonicity, then the above inequality works in the reverse way.

**Lemma**—Let $f$ and $g$ be monotonic functions of the same monotonicity on $[a,b]$. Then for any $x,y\in [a,b]$ we have 

$$
(f(x)-f(y))(g(x)-g(y))\geq 0.
$$

**Proof**

Integrate this inequality with respect to $x$ and $y$ over $[a,b]$: 

$$
\int _{a}^{b}\int _{a}^{b}(f(x)-f(y))(g(x)-g(y))\,dx\,dy\geq 0.
$$

Expanding the integrand gives: 

$$
\int _{a}^{b}\int _{a}^{b}\left[f(x)g(x)-f(x)g(y)-f(y)g(x)+f(y)g(y)\right]\,dx\,dy\geq 0.
$$

Separate the double integral into four parts: 

$$
\int _{a}^{b}\int _{a}^{b}f(x)g(x)\,dx\,dy-\int _{a}^{b}\int _{a}^{b}f(x)g(y)\,dx\,dy-\int _{a}^{b}\int _{a}^{b}f(y)g(x)\,dx\,dy+\int _{a}^{b}\int _{a}^{b}f(y)g(y)\,dx\,dy\geq 0.
$$

Since the integration variable in each inner integral is independent, we have:

- $\int _{a}^{b}\int _{a}^{b}f(x)g(x)\,dx\,dy=(b-a)\int _{a}^{b}f(x)g(x)\,dx,$
- $\int _{a}^{b}\int _{a}^{b}f(y)g(y)\,dx\,dy=(b-a)\int _{a}^{b}f(y)g(y)\,dy=(b-a)\int _{a}^{b}f(x)g(x)\,dx,$
- $\int _{a}^{b}\int _{a}^{b}f(x)g(y)\,dx\,dy=\left(\int _{a}^{b}f(x)\,dx\right)\left(\int _{a}^{b}g(y)\,dy\right),$
- $\int _{a}^{b}\int _{a}^{b}f(y)g(x)\,dx\,dy=\left(\int _{a}^{b}f(y)\,dy\right)\left(\int _{a}^{b}g(x)\,dx\right)=\left(\int _{a}^{b}f(x)\,dx\right)\left(\int _{a}^{b}g(x)\,dx\right).$

Let

$$
I=\int _{a}^{b}f(x)g(x)\,dx,\quad F=\int _{a}^{b}f(x)\,dx,\quad G=\int _{a}^{b}g(x)\,dx.
$$

Substitute these into the inequality:

$$
(b-a)I-FG-FG+(b-a)I\geq 0.
$$

Simplify:

$$
2(b-a)I-2FG\geq 0.
$$

Dividing by $2(b-a)$ (noting that $b-a>0$):

$$
I\geq {\frac {FG}{(b-a)}}.
$$

Divide both sides by $b-a$ to obtain:

$$
{\frac {1}{b-a}}\int _{a}^{b}f(x)g(x)\,dx\geq \left({\frac {1}{b-a}}\int _{a}^{b}f(x)\,dx\right)\left({\frac {1}{b-a}}\int _{a}^{b}g(x)\,dx\right).
$$

This completes the proof.

### Other inequalities

There are also a number of other inequalities associated with Chebyshev:

- [Chebyshev's sum inequality](https://en.wikipedia.org/wiki/Chebyshev%27s_sum_inequality)
- [Chebyshev–Markov–Stieltjes inequalities](https://en.wikipedia.org/wiki/Chebyshev%E2%80%93Markov%E2%80%93Stieltjes_inequalities)

## Notes

The [Environmental Protection Agency](https://en.wikipedia.org/wiki/United_States_Environmental_Protection_Agency) has suggested best practices for the use of Chebyshev's inequality for estimating confidence intervals.

## See also

- [Multidimensional Chebyshev's inequality](https://en.wikipedia.org/wiki/Multidimensional_Chebyshev%27s_inequality)
- [Concentration inequality](https://en.wikipedia.org/wiki/Concentration_inequality) – a summary of tail-bounds on random variables.
- [Cornish–Fisher expansion](https://en.wikipedia.org/wiki/Cornish%E2%80%93Fisher_expansion)
- [Eaton's inequality](https://en.wikipedia.org/wiki/Eaton%27s_inequality)
- [Kolmogorov's inequality](https://en.wikipedia.org/wiki/Kolmogorov%27s_inequality)
- [Proof of the weak law of large numbers](https://en.wikipedia.org/wiki/Law_of_large_numbers/Proof) using Chebyshev's inequality
- [Le Cam's theorem](https://en.wikipedia.org/wiki/Le_Cam%27s_theorem)
- [Paley–Zygmund inequality](https://en.wikipedia.org/wiki/Paley%E2%80%93Zygmund_inequality)
- [Vysochanskiï–Petunin inequality](https://en.wikipedia.org/wiki/Vysochanski%C3%AF%E2%80%93Petunin_inequality) — a stronger result applicable to [unimodal probability distributions](https://en.wikipedia.org/wiki/Unimodal_probability_distributions)
- [Lenglart's inequality](https://en.wikipedia.org/wiki/Lenglart%27s_inequality)

## References

1.  Kvanli, Alan H.; Pavur, Robert J.; Keeling, Kellie B. (2006). [Concise Managerial Statistics](https://books.google.com/books?id=h6CQ1J0gwNgC&pg=PT95). [cEngage Learning](https://en.wikipedia.org/wiki/CEngage_Learning). pp. 81–82. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-324-22388-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-324-22388-0).
2.  Chernick, Michael R. (2011). [The Essentials of Biostatistics for Physicians, Nurses, and Clinicians](https://books.google.com/books?id=JP4azqd8ONEC&pg=PA50). [John Wiley & Sons](https://en.wikipedia.org/wiki/John_Wiley_%26_Sons). pp. 49–50. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-470-64185-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-470-64185-9).
3.  ["Error Term of Chebyshev inequality?"](https://math.stackexchange.com/a/776424/352034). *Mathematics Stack Exchange*. Retrieved 2023-12-11.
4.  [Knuth, Donald](https://en.wikipedia.org/wiki/Donald_Knuth) (1997). [The Art of Computer Programming: Fundamental Algorithms, Volume 1](https://web.archive.org/web/20090226183954/http://www-cs-faculty.stanford.edu/~uno/taocp.html) (3rd ed.). Reading, Massachusetts: Addison–Wesley. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-201-89683-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-201-89683-1). Archived from [the original](http://www-cs-faculty.stanford.edu/~uno/taocp.html) on 26 February 2009. Retrieved 1 October 2012.
5.  Bienaymé, I.-J. (1853). ["Considérations àl'appui de la découverte de Laplace"](https://www.biodiversitylibrary.org/item/16564#page/319/mode/1up). *Comptes Rendus de l'Académie des Sciences*. **37**: 309–324.
6.  Tchébychef, P. (1867). ["Des valeurs moyennes"](https://gallica.bnf.fr/ark:/12148/bpt6k16411c/f185.item). *Journal de Mathématiques Pures et Appliquées*. 2. **12**: 177–184.
7.  Routledge, Richard. [Chebyshev's inequality](https://www.britannica.com/science/Chebyshevs-inequality). Encyclopedia Britannica.
8.  Markov A. (1884) On certain applications of algebraic continued fractions, Ph.D. thesis, St. Petersburg
9.  Feller, W., 1968. An introduction to probability theory and its applications, vol. 1. p227 (Wiley, New York).
10. Uhl, Roland (2023). [Charakterisierung des Erwartungswertes am Graphen der Verteilungsfunktion](https://opus4.kobv.de/opus4-fhbrb/files/2986/Uhl2023.pdf) \[*Characterization of the expected value on the graph of the cumulative distribution function*\] (PDF). Technische Hochschule Brandenburg. p. 5. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.25933/opus4-2986](https://doi.org/10.25933%2Fopus4-2986). [Archived](https://web.archive.org/web/20231224025751/https://opus4.kobv.de/opus4-fhbrb/frontdoor/index/index/docId/2986) from the original on 2023-12-24.
11. [Selberg, Henrik L.](https://en.wikipedia.org/wiki/Henrik_Selberg) (1940). "Zwei Ungleichungen zur Ergänzung des Tchebycheffschen Lemmas" \[Two Inequalities Supplementing the Tchebycheff Lemma\]. *Skandinavisk Aktuarietidskrift (Scandinavian Actuarial Journal)* (in German). **1940** (3–4): 121–125. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/03461238.1940.10404804](https://doi.org/10.1080%2F03461238.1940.10404804). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0346-1238](https://search.worldcat.org/issn/0346-1238). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [610399869](https://search.worldcat.org/oclc/610399869).
12. ^   Godwin, H. J. (September 1955). ["On Generalizations of Tchebychef's Inequality"](http://www.tandfonline.com/doi/abs/10.1080/01621459.1955.10501978). *Journal of the American Statistical Association*. **50** (271): 923–945. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/01621459.1955.10501978](https://doi.org/10.1080%2F01621459.1955.10501978). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0162-1459](https://search.worldcat.org/issn/0162-1459).
13. Conlon, J.; Dulá, J. H. ["A geometric derivation and interpretation of Tchebyscheff's Inequality"](http://www.people.vcu.edu/~jdula/WORKINGPAPERS/tcheby.pdf) (PDF). Retrieved 2 October 2012.
14. Birnbaum, Z. W.; Raymond, J.; Zuckerman, H. S. (1947). ["A Generalization of Tshebyshev's Inequality to Two Dimensions"](http://projecteuclid.org/DPubS?service=UI&version=1.0&verb=Display&handle=euclid.aoms/1177730493). *The Annals of Mathematical Statistics*. **18** (1): 70–79. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/aoms/1177730493](https://doi.org/10.1214%2Faoms%2F1177730493). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0003-4851](https://search.worldcat.org/issn/0003-4851). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0019849](https://mathscinet.ams.org/mathscinet-getitem?mr=0019849). [Zbl](https://en.wikipedia.org/wiki/Zbl_(identifier)) [0032.03402](https://zbmath.org/?format=complete&q=an:0032.03402). Retrieved 7 October 2012.
15. Ferentinos, K (1982). "On Tchebycheff type inequalities". *Trabajos Estadıst Investigacion Oper*. **33**: 125–132. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/BF02888707](https://doi.org/10.1007%2FBF02888707). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [123762564](https://api.semanticscholar.org/CorpusID:123762564).
16. Xinjia Chen (2007). "A New Generalization of Chebyshev Inequality for Random Vectors". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[0707.0805v2](https://arxiv.org/abs/0707.0805v2) \[[math.ST](https://arxiv.org/archive/math.ST)\].
17. Jorge Navarro (2014). "Can the bounds in the multivariate Chebyshev inequality be attained?". *Statistics and Probability Letters*. **91**: 1–5. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.spl.2014.03.028](https://doi.org/10.1016%2Fj.spl.2014.03.028).
18. ^   Stellato, Bartolomeo; Parys, Bart P. G. Van; Goulart, Paul J. (2016-05-31). "Multivariate Chebyshev Inequality with Estimated Mean and Variance". *The American Statistician*. **71** (2): 123–127. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1509.08398](https://arxiv.org/abs/1509.08398). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/00031305.2016.1186559](https://doi.org/10.1080%2F00031305.2016.1186559). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0003-1305](https://search.worldcat.org/issn/0003-1305). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [53407286](https://api.semanticscholar.org/CorpusID:53407286).
19. Vandenberghe, L.; Boyd, S.; Comanor, K. (2007-01-01). "Generalized Chebyshev Bounds via Semidefinite Programming". *SIAM Review*. **49** (1): 52–64. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2007SIAMR..49...52V](https://ui.adsabs.harvard.edu/abs/2007SIAMR..49...52V). [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.126.9105](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.126.9105). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/S0036144504440543](https://doi.org/10.1137%2FS0036144504440543). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0036-1445](https://search.worldcat.org/issn/0036-1445).
20. [Kotz, Samuel](https://en.wikipedia.org/wiki/Samuel_Kotz); Balakrishnan, N.; [Johnson, Norman L.](https://en.wikipedia.org/wiki/Norman_Lloyd_Johnson) (2000). [Continuous Multivariate Distributions, Volume 1, Models and Applications](http://www.wiley.com/WileyCDA/WileyTitle/productCd-0471183873.html) (2nd ed.). Boston \[u.a.\]: Houghton Mifflin. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-18387-7](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-18387-7). Retrieved 7 October 2012.
21. Berge, P. O. (1938). "A note on a form of Tchebycheff's theorem for two variables". *Biometrika*. **29** (3/4): 405–406. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2332015](https://doi.org/10.2307%2F2332015). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2332015](https://www.jstor.org/stable/2332015).
22. Lal D. N. (1955) A note on a form of Tchebycheff's inequality for two or more variables. [Sankhya](https://en.wikipedia.org/wiki/Sankhya_(journal) "Sankhya (journal)") 15(3):317–320
23. Isii K. (1959) On a method for generalizations of Tchebycheff's inequality. Ann Inst Stat Math 10: 65–88
24. [Olkin, Ingram](https://en.wikipedia.org/wiki/Ingram_Olkin); [Pratt, John W.](https://en.wikipedia.org/wiki/John_W._Pratt) (1958). ["A Multivariate Tchebycheff Inequality"](https://doi.org/10.1214%2Faoms%2F1177706720). *The Annals of Mathematical Statistics*. **29** (1): 226–234. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/aoms/1177706720](https://doi.org/10.1214%2Faoms%2F1177706720). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0093865](https://mathscinet.ams.org/mathscinet-getitem?mr=0093865). [Zbl](https://en.wikipedia.org/wiki/Zbl_(identifier)) [0085.35204](https://zbmath.org/?format=complete&q=an:0085.35204).
25. Godwin H. J. (1964) Inequalities on distribution functions. New York, Hafner Pub. Co.
26. [Mitzenmacher, Michael](https://en.wikipedia.org/wiki/Michael_Mitzenmacher); [Upfal, Eli](https://en.wikipedia.org/wiki/Eli_Upfal) (January 2005). [Probability and Computing: Randomized Algorithms and Probabilistic Analysis](http://www.cambridge.org/us/knowledge/isbn/item1171566/?site_locale=en_US) (Repr. ed.). Cambridge \[u.a.\]: Cambridge Univ. Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-83540-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-83540-4). Retrieved 6 October 2012.
27. [Section 2.1](http://www.math.utah.edu/~firas/Papers/rassoul-seppalainen-ldp.pdf) [Archived](https://web.archive.org/web/20150430075226/http://www.math.utah.edu/~firas/Papers/rassoul-seppalainen-ldp.pdf) April 30, 2015, at the [Wayback Machine](https://en.wikipedia.org/wiki/Wayback_Machine)
28. Baranoski, Gladimir V. G.; Rokne, Jon G.; Xu, Guangwu (15 May 2001). "Applying the exponential Chebyshev inequality to the nondeterministic computation of form factors". *Journal of Quantitative Spectroscopy and Radiative Transfer*. **69** (4): 199–200. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2001JQSRT..69..447B](https://ui.adsabs.harvard.edu/abs/2001JQSRT..69..447B). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/S0022-4073(00)00095-9](https://doi.org/10.1016%2FS0022-4073%2800%2900095-9). (the references for this article are corrected by Baranoski, Gladimir V. G.; Rokne, Jon G.; Guangwu Xu (15 January 2002). ["Corrigendum to: 'Applying the exponential Chebyshev inequality to the nondeterministic computation of form factors'"](https://doi.org/10.1016%2FS0022-4073%2801%2900171-6). *Journal of Quantitative Spectroscopy and Radiative Transfer*. **72** (2): 199–200. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2002JQSRT..72..199B](https://ui.adsabs.harvard.edu/abs/2002JQSRT..72..199B). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/S0022-4073(01)00171-6](https://doi.org/10.1016%2FS0022-4073%2801%2900171-6).)
29. Dufour (2003) [Properties of moments of random variables](https://www2.cirano.qc.ca/~dufourj/Web_Site/ResE/Dufour_1999_C_TS_Moments.pdf)
30. ^    Saw, John G.; Yang, Mark C. K.; Mo, Tse Chin (1984). "Chebyshev Inequality with Estimated Mean and Variance". *[The American Statistician](https://en.wikipedia.org/wiki/The_American_Statistician)*. **38** (2): 130–2. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2683249](https://doi.org/10.2307%2F2683249). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0003-1305](https://search.worldcat.org/issn/0003-1305). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2683249](https://www.jstor.org/stable/2683249).
31. ^   Kabán, Ata (2012). "Non-parametric detection of meaningless distances in high dimensional data". *[Statistics and Computing](https://en.wikipedia.org/wiki/Statistics_and_Computing)*. **22** (2): 375–85. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s11222-011-9229-0](https://doi.org/10.1007%2Fs11222-011-9229-0). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [6018114](https://api.semanticscholar.org/CorpusID:6018114).
32. ^   Konijn, Hendrik S. (February 1987). "Distribution-Free and Other Prediction Intervals". *[The American Statistician](https://en.wikipedia.org/wiki/The_American_Statistician)*. **41** (1): 11–15. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2684311](https://doi.org/10.2307%2F2684311). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2684311](https://www.jstor.org/stable/2684311).
33. ^   Beasley, T. Mark; Page, Grier P.; Brand, Jaap P. L.; Gadbury, Gary L.; Mountz, John D.; [Allison, David B.](https://en.wikipedia.org/wiki/David_B._Allison) (January 2004). ["Chebyshev's inequality for nonparametric testing with small N and α in microarray research"](https://doi.org/10.1111%2Fj.1467-9876.2004.00428.x). *Journal of the Royal Statistical Society*. C (Applied Statistics). **53** (1): 95–108. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1111/j.1467-9876.2004.00428.x](https://doi.org/10.1111%2Fj.1467-9876.2004.00428.x). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1467-9876](https://search.worldcat.org/issn/1467-9876). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [122678278](https://api.semanticscholar.org/CorpusID:122678278).
34. ^   [Berck, Peter](https://en.wikipedia.org/wiki/Peter_Berck); Hihn, Jairus M. (May 1982). "Using the Semivariance to Estimate Safety-First Rules". *American Journal of Agricultural Economics*. **64** (2): 298–300. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/1241139](https://doi.org/10.2307%2F1241139). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0002-9092](https://search.worldcat.org/issn/0002-9092). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [1241139](https://www.jstor.org/stable/1241139).
35. Nantell, Timothy J.; Price, Barbara (June 1979). "An Analytical Comparison of Variance and Semivariance Capital Market Theories". *[The Journal of Financial and Quantitative Analysis](https://en.wikipedia.org/wiki/The_Journal_of_Financial_and_Quantitative_Analysis)*. **14** (2): 221–42. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2330500](https://doi.org/10.2307%2F2330500). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2330500](https://www.jstor.org/stable/2330500). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [154652959](https://api.semanticscholar.org/CorpusID:154652959).
37. [Savage, I. Richard. "Probability inequalities of the Tchebycheff type." Journal of Research of the National Bureau of Standards-B. Mathematics and Mathematical Physics B 65 (1961): 211-222](https://nvlpubs.nist.gov/nistpubs/jres/65B/jresv65Bn3p211_A1b.pdf)
38. Cantelli F. (1910) Intorno ad un teorema fondamentale della teoria del rischio. Bolletino dell Associazione degli Attuari Italiani
39. Grimmett and Stirzaker, problem 7.11.9. Several proofs of this result can be found in [Chebyshev's Inequalities](http://www.mcdowella.demon.co.uk/Chebyshev.html) [Archived](https://web.archive.org/web/20190224000121/http://www.mcdowella.demon.co.uk/Chebyshev.html) 2019-02-24 at the [Wayback Machine](https://en.wikipedia.org/wiki/Wayback_Machine) by A. G. McDowell.
40. Bhattacharyya, B. B. (1987). "One-sided chebyshev inequality when the first four moments are known". *Communications in Statistics – Theory and Methods*. **16** (9): 2789–91. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/03610928708829540](https://doi.org/10.1080%2F03610928708829540). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0361-0926](https://search.worldcat.org/issn/0361-0926).
41. Gauss C. F. Theoria Combinationis Observationum Erroribus Minimis Obnoxiae. Pars Prior. Pars Posterior. Supplementum. Theory of the Combination of Observations Least Subject to Errors. Part One. Part Two. Supplement. 1995. Translated by G. W. Stewart. Classics in Applied Mathematics Series, Society for Industrial and Applied Mathematics, Philadelphia
42. Pukelsheim, Friedrich (May 1994). ["The Three Sigma Rule"](http://www.tandfonline.com/doi/abs/10.1080/00031305.1994.10476030). *The American Statistician*. **48** (2): 88–91. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/00031305.1994.10476030](https://doi.org/10.1080%2F00031305.1994.10476030). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0003-1305](https://search.worldcat.org/issn/0003-1305). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [122587510](https://api.semanticscholar.org/CorpusID:122587510).
43. ^   DasGupta, A (2000). "Best constants in Chebychev inequalities with various applications". *Metrika*. **5** (1): 185–200. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s184-000-8316-9](https://doi.org/10.1007%2Fs184-000-8316-9). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [121436601](https://api.semanticscholar.org/CorpusID:121436601).
44. Steliga, Katarzyna; Szynal, Dominik (2010). ["On Markov-Type Inequalities"](https://ijpam.eu/contents/2010-58-2/2/2.pdf) (PDF). *International Journal of Pure and Applied Mathematics*. **58** (2): 137–152. [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1311-8080](https://search.worldcat.org/issn/1311-8080). Retrieved 10 October 2012.
45. Grechuk, B., Molyboha, A., Zabarankin, M. (2010). [Chebyshev Inequalities with Law Invariant Deviation Measures](https://www.researchgate.net/publication/231939730_Chebyshev_inequalities_with_law-invariant_deviation_measures), Probability in the Engineering and Informational Sciences, 24(1), 145-170.
46. Godwin H. J. (1964) Inequalities on distribution functions. (Chapter 3) New York, Hafner Pub. Co.
47. [Haldane, J. B.](https://en.wikipedia.org/wiki/J._B._S._Haldane) (1952). "Simple tests for bimodality and bitangentiality". *[Annals of Eugenics](https://en.wikipedia.org/wiki/Annals_of_Eugenics)*. **16** (4): 359–364. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1111/j.1469-1809.1951.tb02488.x](https://doi.org/10.1111%2Fj.1469-1809.1951.tb02488.x). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [14953132](https://pubmed.ncbi.nlm.nih.gov/14953132).
48. [Kendall M. G.](https://en.wikipedia.org/wiki/Maurice_Kendall) (1943) The Advanced Theory of Statistics, 1. London
49. He, Simai; Zhang, Jiawei; Zhang, Shuzhong (2010). "Bounding probability of small deviation: a fourth moment approach". *[Mathematics of Operations Research](https://en.wikipedia.org/wiki/Mathematics_of_Operations_Research)*. **35** (1): 208–232. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1287/moor.1090.0438](https://doi.org/10.1287%2Fmoor.1090.0438). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [11298475](https://api.semanticscholar.org/CorpusID:11298475).
50. Fink, A. M.; Jodeit, Max Jr. (1984). ["On Chebyshev's other inequality"](https://projecteuclid.org/euclid.lnms/1215465617). In Tong, Y. L.; [Gupta, Shanti S.](https://en.wikipedia.org/wiki/Shanti_S._Gupta) (eds.). *Inequalities in Statistics and Probability*. Institute of Mathematical Statistics Lecture Notes - Monograph Series. Vol. 5. pp. 115–120. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/lnms/1215465637](https://doi.org/10.1214%2Flnms%2F1215465637). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-940600-04-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-940600-04-1). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0789242](https://mathscinet.ams.org/mathscinet-getitem?mr=0789242). Retrieved 7 October 2012.
51. Niculescu, Constantin P. (2001). ["An extension of Chebyshev's inequality and its connection with Jensen's inequality"](http://emis.matem.unam.mx/journals/HOA/JIA/Volume6_4/462.html). *Journal of Inequalities and Applications*. **6** (4): 451–462. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.612.7056](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.612.7056). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1155/S1025583401000273](https://doi.org/10.1155%2FS1025583401000273). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1025-5834](https://search.worldcat.org/issn/1025-5834). Retrieved 6 October 2012.
52. ^   Niculescu, Constantin P.; [Pečarić, Josip](https://en.wikipedia.org/wiki/Josip_Pe%C4%8Dari%C4%87) (2010). ["The Equivalence of Chebyshev's Inequality to the Hermite–Hadamard Inequality"](https://www.csm.ro/reviste/Mathematical_Reports/Pdfs/2010/2/Niculescu.pdf) (PDF). *Mathematical Reports*. **12** (62): 145–156. [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1582-3067](https://search.worldcat.org/issn/1582-3067). Retrieved 6 October 2012.
53. Malamud, S. M. (15 February 2001). ["Some complements to the Jensen and Chebyshev inequalities and a problem of W. Walter"](https://www.ams.org/journals/proc/2001-129-09/S0002-9939-01-05849-X/). *Proceedings of the American Mathematical Society*. **129** (9): 2671–2678. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1090/S0002-9939-01-05849-X](https://doi.org/10.1090%2FS0002-9939-01-05849-X). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0002-9939](https://search.worldcat.org/issn/0002-9939). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1838791](https://mathscinet.ams.org/mathscinet-getitem?mr=1838791). Retrieved 7 October 2012.
54. [Calculating Upper Confidence Limits for Exposure Point Concentrations at hazardous Waste Sites](https://nepis.epa.gov/Exe/ZyNET.exe/P100CYCE.TXT?ZyActionD=ZyDocument&Client=EPA&Index=2000+Thru+2005&Docs=&Query=&Time=&EndTime=&SearchMethod=1&TocRestrict=n&Toc=&TocEntry=&QField=&QFieldYear=&QFieldMonth=&QFieldDay=&IntQFieldOp=0&ExtQFieldOp=0&XmlQuery=&File=D%3A%5Czyfiles%5CIndex%20Data%5C00thru05%5CTxt%5C00000029%5CP100CYCE.txt&User=ANONYMOUS&Password=anonymous&SortMethod=h%7C-&MaximumDocuments=1&FuzzyDegree=0&ImageQuality=r75g8/r75g8/x150y150g16/i425&Display=p%7Cf&DefSeekPage=x&SearchBack=ZyActionL&Back=ZyActionS&BackDesc=Results%20page&MaximumPages=1&ZyEntry=1&SeekPage=x&ZyPURL) (Report). Office of Emergency and Remedial Response of the U.S. Environmental Protection Agency. December 2002. Retrieved 5 August 2016.

## Further reading

- A. Papoulis (1991), *Probability, Random Variables, and Stochastic Processes*, 3rd ed. McGraw–Hill. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-07-100870-5](https://en.wikipedia.org/wiki/Special:BookSources/0-07-100870-5). pp. 113–114.
- [G. Grimmett](https://en.wikipedia.org/wiki/Geoffrey_Grimmett) and D. Stirzaker (2001), *Probability and Random Processes*, 3rd ed. Oxford. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-19-857222-0](https://en.wikipedia.org/wiki/Special:BookSources/0-19-857222-0). Section 7.3.

## External links

- ["Chebyshev inequality in probability theory"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society), 2001 \[1994\]
- [Formal proof](https://web.archive.org/web/20131204193123/http://mws.cs.ru.nl/mwiki/random_2.html#T7) in the [Mizar system](https://en.wikipedia.org/wiki/Mizar_system).
