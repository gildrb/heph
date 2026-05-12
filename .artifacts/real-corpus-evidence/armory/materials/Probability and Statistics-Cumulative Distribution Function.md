[[probability-statistics.base]]

> Source: [[Cumulative Distribution Function]]
> License: Wikipedia content is available under CC BY-SA 4.0.

![[media/162bd7b9c54fe8df1d8e59f259e90049258e4f04.png]]
Cumulative distribution function for the [exponential distribution](https://en.wikipedia.org/wiki/Exponential_distribution)

![[media/a61416b7970db3a9122ebbd39c0bbf869751a1b9.png]]
Cumulative distribution function for the [normal distribution](https://en.wikipedia.org/wiki/Normal_distribution)

In [probability theory](https://en.wikipedia.org/wiki/Probability_theory) and [statistics](https://en.wikipedia.org/wiki/Statistics), the **cumulative distribution function** (**CDF**) of a real-valued [random variable](https://en.wikipedia.org/wiki/Random_variable) $X$, or just **distribution function** of $X$, evaluated at $x$, is the [probability](https://en.wikipedia.org/wiki/Probability) that $X$ will take a value less than or equal to $x$.

Every [probability distribution](https://en.wikipedia.org/wiki/Probability_distribution) [supported](https://en.wikipedia.org/wiki/Support_(measure_theory) "Support (measure theory)") on the real numbers, discrete or "mixed" as well as [continuous](https://en.wikipedia.org/wiki/Continuous_variable), is uniquely identified by a [right-continuous](https://en.wikipedia.org/wiki/Right-continuous) [monotone increasing](https://en.wikipedia.org/wiki/Monotonic_function) function (a [càdlàg](https://en.wikipedia.org/wiki/C%C3%A0dl%C3%A0g) function) $F\colon \mathbb {R} \rightarrow [0,1]$ satisfying $\lim _{x\rightarrow -\infty }F(x)=0$ and $\lim _{x\rightarrow \infty }F(x)=1$.

In the case of a scalar [continuous distribution](https://en.wikipedia.org/wiki/Continuous_distribution), it gives the area under the [[Probability Density Function]] from negative infinity to $x$. Cumulative distribution functions are also used to specify the distribution of [multivariate random variables](https://en.wikipedia.org/wiki/Multivariate_random_variable).

## Definition

The cumulative distribution function of a real-valued [random variable](https://en.wikipedia.org/wiki/Random_variable) $X$ is the function given by

$F_{X}(x)=\operatorname {P} (X\leq x)$   (Eq.1)

where the right-hand side represents the [probability](https://en.wikipedia.org/wiki/Probability) that the random variable $X$ takes on a value less than or equal to $x$.

The probability that $X$ lies in the semi-closed [interval](https://en.wikipedia.org/wiki/Interval_(mathematics) "Interval (mathematics)") $(a,b]$, where $a<b$, is therefore

$\operatorname {P} (a<X\leq b)=F_{X}(b)-F_{X}(a)$   (Eq.2)

In the definition above, the "less than or equal to" sign, "≤", is a convention, not a universally used one (e.g. Hungarian literature uses "\<"), but the distinction is important for discrete distributions. The proper use of tables of the [binomial](https://en.wikipedia.org/wiki/Binomial_distribution) and [Poisson distributions](https://en.wikipedia.org/wiki/Poisson_distribution) depends upon this convention. Moreover, important formulas like [Paul Lévy](https://en.wikipedia.org/wiki/Paul_L%C3%A9vy_(mathematician) "Paul Lévy (mathematician)")'s inversion formula for the [characteristic function](https://en.wikipedia.org/wiki/Characteristic_function_(probability_theory)#Inversion_formula "Characteristic function (probability theory)") also rely on the "less than or equal" formulation.

If treating several random variables $X,Y,\ldots$ etc. the corresponding letters are used as subscripts while, if treating only one, the subscript is usually omitted. It is conventional to use a capital $F$ for a cumulative distribution function, in contrast to the lower-case $f$ used for [[Probability Density Function|probability density functions]] and [probability mass functions](https://en.wikipedia.org/wiki/Probability_mass_function). This applies when discussing general distributions: some specific distributions have their own conventional notation, for example the [normal distribution](https://en.wikipedia.org/wiki/Normal_distribution) uses $\Phi$ and $\phi$ instead of $F$ and $f$, respectively.

The probability density function of a continuous random variable can be determined from the cumulative distribution function by differentiating using the [Fundamental Theorem of Calculus](https://en.wikipedia.org/wiki/Fundamental_Theorem_of_Calculus); i.e. given $F(x)$, 

$$
f(x)={\frac {dF(x)}{dx}}
$$

 as long as the derivative exists.

The CDF of a [continuous random variable](https://en.wikipedia.org/wiki/Continuous_random_variable) $X$ can be expressed as the integral of its probability density function $f_{X}$ as follows: 

$$
F_{X}(x)=\int _{-\infty }^{x}f_{X}(t)\,dt.
$$

In the case of a random variable $X$ which has distribution having a discrete component at a value $b$, 

$$
\operatorname {P} (X=b)=F_{X}(b)-\lim _{x\to b^{-}}F_{X}(x).
$$

If $F_{X}$ is continuous at $b$, this equals zero and there is no discrete component at $b$.

## Properties

![[media/7b38c2f6a8ace8ce21d74e8e98aec696f8b629af.png]]
From top to bottom, the cumulative distribution function of a discrete probability distribution, continuous probability distribution, and a distribution which has both a continuous part and a discrete part.

![[media/0bb840ba98085ceaeb04f74732a22b7ac8230315.png]]
Example of a cumulative distribution function with a countably infinite set of discontinuities.

Every cumulative distribution function $F_{X}$ is [non-decreasing](https://en.wikipedia.org/wiki/Monotone_increasing) and [right-continuous](https://en.wikipedia.org/wiki/Right-continuous), which makes it a [càdlàg](https://en.wikipedia.org/wiki/C%C3%A0dl%C3%A0g) function. Furthermore, 

$$
\lim _{x\to -\infty }F_{X}(x)=0,\quad \lim _{x\to +\infty }F_{X}(x)=1.
$$

Every function with these three properties is a CDF, i.e., for every such function, a [random variable](https://en.wikipedia.org/wiki/Random_variable) can be defined such that the function is the cumulative distribution function of that random variable.

If $X$ is a purely [discrete random variable](https://en.wikipedia.org/wiki/Discrete_random_variable), then it attains values $x_{1},x_{2},\ldots$ with probability $p_{i}=p(x_{i})$, and the CDF of $X$ will be [discontinuous](https://en.wikipedia.org/wiki/Discontinuity_(mathematics)) at the points $x_{i}$: 

$$
F_{X}(x)=\operatorname {P} (X\leq x)=\sum _{x_{i}\leq x}\operatorname {P} (X=x_{i})=\sum _{x_{i}\leq x}p(x_{i}).
$$

If the CDF $F_{X}$ of a real valued random variable $X$ is [continuous](https://en.wikipedia.org/wiki/Continuous_function), then $X$ is a [continuous random variable](https://en.wikipedia.org/wiki/Continuous_random_variable); if furthermore $F_{X}$ is [absolutely continuous](https://en.wikipedia.org/wiki/Absolute_continuity), then there exists a [Lebesgue-integrable](https://en.wikipedia.org/wiki/Lebesgue_integral) function $f_{X}(x)$ such that 

$$
F_{X}(b)-F_{X}(a)=\operatorname {P} (a<X\leq b)=\int _{a}^{b}f_{X}(x)\,dx
$$

 for all real numbers $a$ and $b$. The function $f_{X}$ is equal to the [derivative](https://en.wikipedia.org/wiki/Derivative) of $F_{X}$ [almost everywhere](https://en.wikipedia.org/wiki/Almost_everywhere), and it is called the [[Probability Density Function]] of the distribution of $X$.

If $X$ has finite [L1-norm](https://en.wikipedia.org/wiki/L1-norm), that is, the expectation of $|X|$ is finite, then the expectation is given by the [Riemann–Stieltjes integral](https://en.wikipedia.org/wiki/Riemann%E2%80%93Stieltjes_integral) 

$$
\mathbb {E} [X]=\int _{-\infty }^{\infty }t\,dF_{X}(t)
$$

![[media/168b047c966e0aa574a54be8fb394ee6e9ec4dd3.png]]
CDF plot with two red rectangles, illustrating two inequalities

and for any $x\geq 0$, 

$$
x(1-F_{X}(x))\leq \int _{x}^{\infty }t\,dF_{X}(t)
$$

 as well as 

$$
xF_{X}(-x)\leq \int _{-\infty }^{-x}(-t)\,dF_{X}(t)
$$

 as shown in the diagram (consider the areas of the two red rectangles and their extensions to the right or left up to the graph of $F_{X}$).<sup>\[*[clarification needed](https://en.wikipedia.org/wiki/Wikipedia:Please_clarify)*\]</sup> In particular, we have 

$$
\lim _{x\to -\infty }xF_{X}(x)=0,\quad \lim _{x\to +\infty }x(1-F_{X}(x))=0.
$$

 In addition, the (finite) expected value of the real-valued random variable $X$ can be defined on the graph of its cumulative distribution function as illustrated by the [drawing](https://en.wikipedia.org/wiki/Expected_value#Uhl2023Bild1) in the [definition of expected value for arbitrary real-valued random variables](https://en.wikipedia.org/wiki/Expected_value#Arbitrary_real-valued_random_variables).

## Examples

As an example, suppose $X$ is [uniformly distributed](https://en.wikipedia.org/wiki/Uniform_distribution_(continuous)) on the unit interval $[0,1]$.

Then the CDF of $X$ is given by 

$$
F_{X}(x)={\begin{cases}0&:\ x<0\\x&:\ 0\leq x\leq 1\\1&:\ x>1\end{cases}}
$$

Suppose instead that $X$ takes only the discrete values 0 and 1, with equal probability.

Then the CDF of $X$ is given by 

$$
F_{X}(x)={\begin{cases}0&:\ x<0\\1/2&:\ 0\leq x<1\\1&:\ x\geq 1\end{cases}}
$$

Suppose $X$ is [exponential distributed](https://en.wikipedia.org/wiki/Exponential_distribution). Then the CDF of $X$ is given by 

$$
F_{X}(x;\lambda )={\begin{cases}1-e^{-\lambda x}&x\geq 0,\\0&x<0.\end{cases}}
$$

Here *λ* \> 0 is the parameter of the distribution, often called the rate parameter.

Suppose $X$ is [normal distributed](https://en.wikipedia.org/wiki/Normal_distribution). Then the CDF of $X$ is given by 

$$
F(t;\mu ,\sigma )={\frac {1}{\sigma {\sqrt {2\pi }}}}\int _{-\infty }^{t}\exp \left(-{\frac {(x-\mu )^{2}}{2\sigma ^{2}}}\right)\,dx.
$$

Here the parameter $\mu$ is the [mean](https://en.wikipedia.org/wiki/Mean) or expectation of the distribution; and $\sigma$ is its standard deviation.

A table of the CDF of the standard normal distribution is often used in statistical applications, where it is named the [standard normal table](https://en.wikipedia.org/wiki/Standard_normal_table), the **unit normal table**, or the **Z table**.

Suppose $X$ is [binomial distributed](https://en.wikipedia.org/wiki/Binomial_distribution). Then the CDF of $X$ is given by 

$$
F(k;n,p)=\Pr(X\leq k)=\sum _{i=0}^{\lfloor k\rfloor }{n \choose i}p^{i}(1-p)^{n-i}
$$

Here $p$ is the probability of success and the function denotes the discrete probability distribution of the number of successes in a sequence of $n$ independent experiments, and $\lfloor k\rfloor$ is the "floor" under $k$, i.e. the greatest integer less than or equal to $k$.

## Derived functions

### Complementary cumulative distribution function (tail distribution)

Sometimes, it is useful to study the opposite question and ask how often the random variable is *above* a particular level. This is called the complementary cumulative distribution function (**ccdf**) or simply the **tail distribution** or **exceedance**, and is defined as 

$$
{\bar {F}}_{X}(x)=\operatorname {P} (X>x)=1-F_{X}(x).
$$

This has applications in [statistical](https://en.wikipedia.org/wiki/Statistics) [hypothesis testing](https://en.wikipedia.org/wiki/Hypothesis_test), for example, because the one-sided [p-value](https://en.wikipedia.org/wiki/P-value) is the probability of observing a test statistic *at least* as extreme as the one observed. Thus, provided that the [test statistic](https://en.wikipedia.org/wiki/Test_statistic), *T*, has a continuous distribution, the one-sided [p-value](https://en.wikipedia.org/wiki/P-value) is simply given by the ccdf: for an observed value $t$ of the test statistic 

$$
p=\operatorname {P} (T\geq t)=\operatorname {P} (T>t)=1-F_{T}(t).
$$

In [survival analysis](https://en.wikipedia.org/wiki/Survival_analysis), ${\bar {F}}_{X}(x)$ is called the [survival function](https://en.wikipedia.org/wiki/Survival_function) and denoted $S(x)$, while the term *reliability function* is common in [engineering](https://en.wikipedia.org/wiki/Engineering).

Properties

- For a non-negative continuous random variable having an expectation, [Markov's inequality](https://en.wikipedia.org/wiki/Markov%27s_inequality) states that 

$$
{\bar {F}}_{X}(x)\leq {\frac {\operatorname {E} (X)}{x}}.
$$

- As $x\to \infty ,{\bar {F}}_{X}(x)\to 0$, and in fact ${\bar {F}}_{X}(x)=o(1/x)$ provided that $\operatorname {E} (X)$ is finite.  
  Proof:<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>  
  Assuming $X$ has a density function $f_{X}$, for any $c>0$ 

$$
\operatorname {E} (X)=\int _{0}^{\infty }xf_{X}(x)\,dx\geq \int _{0}^{c}xf_{X}(x)\,dx+c\int _{c}^{\infty }f_{X}(x)\,dx
$$

 Then, on recognizing 

$$
{\bar {F}}_{X}(c)=\int _{c}^{\infty }f_{X}(x)\,dx
$$

 and rearranging terms, 

$$
0\leq c{\bar {F}}_{X}(c)\leq \operatorname {E} (X)-\int _{0}^{c}xf_{X}(x)\,dx\to 0{\text{ as }}c\to \infty
$$

 as claimed.
- For a random variable having an expectation, 

$$
\operatorname {E} (X)=\int _{0}^{\infty }{\bar {F}}_{X}(x)\,dx-\int _{-\infty }^{0}F_{X}(x)\,dx
$$

 and for a non-negative random variable the second term is 0.  
  If the random variable can only take non-negative integer values, this is equivalent to 

$$
\operatorname {E} (X)=\sum _{n=0}^{\infty }{\bar {F}}_{X}(n).
$$

### Folded cumulative distribution

![[media/2ecced6c22443f52554073e524b72c79112c841f.png]]
Example of the folded cumulative distribution for a [normal distribution](https://en.wikipedia.org/wiki/Normal_distribution) function with an [expected value](https://en.wikipedia.org/wiki/Expected_value) of 0 and a [standard deviation](https://en.wikipedia.org/wiki/Standard_deviation) of 1.

While the plot of a cumulative distribution $F$ often has an S-like shape, an alternative illustration is the **folded cumulative distribution** or **mountain plot**, which folds the top half of the graph over, that is

$F_{\text{fold}}(x)=F(x)1_{\{F(x)\leq 0.5\}}+(1-F(x))1_{\{F(x)>0.5\}}$

where $1_{\{A\}}$ denotes the [indicator function](https://en.wikipedia.org/wiki/Indicator_function) and the second summand is the [survivor function](https://en.wikipedia.org/wiki/Survivor_function), thus using two scales, one for the upslope and another for the downslope. This form of illustration emphasises the [median](https://en.wikipedia.org/wiki/Median_(statistics)), [dispersion](https://en.wikipedia.org/wiki/Dispersion_(statistics)) (specifically, the [mean absolute deviation](https://en.wikipedia.org/wiki/Mean_absolute_deviation) from the median) and [skewness](https://en.wikipedia.org/wiki/Skewness) of the distribution or of the empirical results.

### Inverse distribution function (quantile function)

If the CDF *F* is strictly increasing and continuous then $F^{-1}(p),p\in [0,1],$ is the unique real number $x$ such that $F(x)=p$. This defines the **inverse distribution function** or [quantile function](https://en.wikipedia.org/wiki/Quantile_function).

Some distributions do not have a unique inverse (for example if $f_{X}(x)=0$ for all $a<x<b$, causing $F_{X}$ to be constant). In this case, one may use the **generalized inverse distribution function**, which is defined as

$F^{-1}(p)=\inf\{x\in \mathbb {R} :F(x)\geq p\},\quad \forall p\in [0,1].$

- Example 1: The median is $F^{-1}(0.5)$.
- Example 2: Put $\tau =F^{-1}(0.95)$. Then we call $\tau$ the 95th percentile.

Some useful properties of the inverse cdf (which are also preserved in the definition of the generalized [inverse distribution](https://en.wikipedia.org/wiki/Inverse_distribution) function) are:

1.  $F^{-1}$ is nondecreasing
2.  $F^{-1}(F(x))\leq x$
3.  $F(F^{-1}(p))\geq p$
4.  $F^{-1}(p)\leq x$ if and only if $p\leq F(x)$
5.  If $Y$ has a $U[0,1]$ distribution then $F^{-1}(Y)$ is distributed as $F$. This is used in [random number generation](https://en.wikipedia.org/wiki/Random_number_generation) using the [inverse transform sampling](https://en.wikipedia.org/wiki/Inverse_transform_sampling)-method.
6.  If $\{X_{\alpha }\}$ is a collection of independent $F$-distributed random variables defined on the same [sample space](https://en.wikipedia.org/wiki/Sample_space), then there exist random variables $Y_{\alpha }$ such that $Y_{\alpha }$ is distributed as $U[0,1]$ and $F^{-1}(Y_{\alpha })=X_{\alpha }$ with probability 1 for all $\alpha$.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

The inverse of the cdf can be used to translate results obtained for the uniform distribution to other distributions.

### Empirical distribution function

The [empirical distribution function](https://en.wikipedia.org/wiki/Empirical_distribution_function) is an estimate of the cumulative distribution function that generated the points in the sample. It converges with probability 1 to that underlying distribution. A number of results exist to quantify the [rate of convergence](https://en.wikipedia.org/wiki/Rate_of_convergence) of the empirical distribution function to the underlying cumulative distribution function.

## Multivariate case

### Definition for two random variables

When dealing simultaneously with more than one random variable the **joint cumulative distribution function** can also be defined. For example, for a pair of random variables $X,Y$, the joint CDF $F_{XY}$ is given by

$F_{X,Y}(x,y)=\operatorname {P} (X\leq x,Y\leq y)$   (Eq.3)

where the right-hand side represents the [probability](https://en.wikipedia.org/wiki/Probability) that the random variable $X$ takes on a value less than or equal to $x$ **and** that $Y$ takes on a value less than or equal to $y$.

Example of joint cumulative distribution function:

For two continuous variables *X* and *Y*: 

$$
\Pr(a<X<b{\text{ and }}c<Y<d)=\int _{a}^{b}\int _{c}^{d}f(x,y)\,dy\,dx;
$$

For two discrete random variables, it is beneficial to generate a table of probabilities and address the cumulative probability for each potential range of *X* and *Y*, and here is the example:

given the joint probability mass function in tabular form, determine the joint cumulative distribution function.

|         |         |         |         |         |
|---------|---------|---------|---------|---------|
|         | *Y* = 2 | *Y* = 4 | *Y* = 6 | *Y* = 8 |
| *X* = 1 | 0       | 0.1     | 0       | 0.1     |
| *X* = 3 | 0       | 0       | 0.2     | 0       |
| *X* = 5 | 0.3     | 0       | 0       | 0.15    |
| *X* = 7 | 0       | 0       | 0.15    | 0       |

Solution: using the given table of probabilities for each potential range of *X* and *Y*, the joint cumulative distribution function may be constructed in tabular form:

|          |          |         |         |         |         |
|----------|----------|---------|---------|---------|---------|
|          | *Y* \< 2 | *Y* ≤ 2 | *Y* ≤ 4 | *Y* ≤ 6 | *Y* ≤ 8 |
| *X* \< 1 | 0        | 0       | 0       | 0       | 0       |
| *X* ≤ 1  | 0        | 0       | 0.1     | 0.1     | 0.2     |
| *X* ≤ 3  | 0        | 0       | 0.1     | 0.3     | 0.4     |
| *X* ≤ 5  | 0        | 0.3     | 0.4     | 0.6     | 0.85    |
| *X* ≤ 7  | 0        | 0.3     | 0.4     | 0.75    | 1       |

### Definition for more than two random variables

For $N$ random variables $X_{1},\ldots ,X_{N}$, the joint CDF $F_{X_{1},\ldots ,X_{N}}$ is given by

$F_{X_{1},\ldots ,X_{N}}(x_{1},\ldots ,x_{N})=\operatorname {P} (X_{1}\leq x_{1},\ldots ,X_{N}\leq x_{N})$   (Eq.4)

Interpreting the $N$ random variables as a [random vector](https://en.wikipedia.org/wiki/Random_vector) $\mathbf {X} =(X_{1},\ldots ,X_{N})^{T}$ yields a shorter notation: 

$$
F_{\mathbf {X} }(\mathbf {x} )=\operatorname {P} (X_{1}\leq x_{1},\ldots ,X_{N}\leq x_{N})
$$

### Properties

Every multivariate CDF is:

1.  Monotonically non-decreasing for each of its variables,
2.  Right-continuous in each of its variables,
3.  $0\leq F_{X_{1}\ldots X_{n}}(x_{1},\ldots ,x_{n})\leq 1,$
4.  $\lim _{x_{1},\ldots ,x_{n}\to +\infty }F_{X_{1}\ldots X_{n}}(x_{1},\ldots ,x_{n})=1$ and $\lim _{x_{i}\to -\infty }F_{X_{1}\ldots X_{n}}(x_{1},\ldots ,x_{n})=0,$ for all i.

Not every function satisfying the above four properties is a multivariate CDF, unlike in the single dimension case. For example, let $F(x,y)=0$ for $x<0$ or $x+y<1$ or $y<0$ and let $F(x,y)=1$ otherwise. It is easy to see that the above conditions are met, and yet $F$ is not a CDF since if it was, then $\operatorname {P} \left({\frac {1}{3}}<X\leq 1,{\frac {1}{3}}<Y\leq 1\right)=-1$ as explained below.

The probability that a point belongs to a [hyperrectangle](https://en.wikipedia.org/wiki/Hyperrectangle) is analogous to the 1-dimensional case: 

$$
F_{X_{1},X_{2}}(a,c)+F_{X_{1},X_{2}}(b,d)-F_{X_{1},X_{2}}(a,d)-F_{X_{1},X_{2}}(b,c)=\operatorname {P} (a<X_{1}\leq b,c<X_{2}\leq d)=\int \cdots
$$

## Complex case

### Complex random variable

The generalization of the cumulative distribution function from real to [complex random variables](https://en.wikipedia.org/wiki/Complex_random_variable#Cumulative_distribution_function) is not obvious because expressions of the form $P(Z\leq 1+2i)$ make no sense. However expressions of the form $P(\Re {(Z)}\leq 1,\Im {(Z)}\leq 3)$ make sense. Therefore, we define the cumulative distribution of a complex random variables via the [joint distribution](https://en.wikipedia.org/wiki/Joint_probability_distribution) of their real and imaginary parts: 

$$
F_{Z}(z)=F_{\Re {(Z)},\Im {(Z)}}(\Re {(z)},\Im {(z)})=P(\Re {(Z)}\leq \Re {(z)},\Im {(Z)}\leq \Im {(z)}).
$$

### Complex random vector

Generalization of **[Eq.4](#math_Eq.4)** yields 

$$
{\begin{aligned}F_{\mathbf {Z} }(\mathbf {z} )&=F_{\Re {(Z_{1})},\Im {(Z_{1})},\ldots ,\Re {(Z_{n})},\Im {(Z_{n})}}(\Re {(z_{1})},\Im {(z_{1})},\ldots ,\Re {(z_{n})},\Im {(z_{n})})\\[1ex]&=\operatorname {P} (\Re {(Z_{1})}\leq \Re {(z_{1})},\Im {(Z_{1})}\leq \Im {(z_{1})},\ldots ,\Re {(Z_{n})}\leq \Re {(z_{n})},\Im {(Z_{n})}\leq \Im {(z_{n})})\end{aligned}}
$$

 as definition for the CDS of a complex random vector $\mathbf {Z} =(Z_{1},\ldots ,Z_{N})^{T}$.

## Use in statistical analysis

The concept of the cumulative distribution function makes an explicit appearance in statistical analysis in two (similar) ways. [Cumulative frequency analysis](https://en.wikipedia.org/wiki/Cumulative_frequency_analysis) is the analysis of the frequency of occurrence of values of a phenomenon less than a reference value. The [empirical distribution function](https://en.wikipedia.org/wiki/Empirical_distribution_function) is a formal direct estimate of the cumulative distribution function for which simple statistical properties can be derived and which can form the basis of various [statistical hypothesis tests](https://en.wikipedia.org/wiki/Statistical_hypothesis_test). Such tests can assess whether there is evidence against a sample of data having arisen from a given distribution, or evidence against two samples of data having arisen from the same (unknown) population distribution.

### Kolmogorov–Smirnov and Kuiper's tests

The [Kolmogorov–Smirnov test](https://en.wikipedia.org/wiki/Kolmogorov%E2%80%93Smirnov_test) is based on cumulative distribution functions and can be used to test to see whether two empirical distributions are different or whether an empirical distribution is different from an ideal distribution. The closely related [Kuiper's test](https://en.wikipedia.org/wiki/Kuiper%27s_test) is useful if the domain of the distribution is cyclic as in day of the week. For instance Kuiper's test might be used to see if the number of tornadoes varies during the year or if sales of a product vary by day of the week or day of the month.

## See also

- [Descriptive statistics](https://en.wikipedia.org/wiki/Descriptive_statistics)
- [Distribution fitting](https://en.wikipedia.org/wiki/Distribution_fitting)
- [Ogive (statistics)](https://en.wikipedia.org/wiki/Ogive_(statistics) "Ogive (statistics)")

## References

1.  Deisenroth, Marc Peter; Faisal, A. Aldo; Ong, Cheng Soon (2020). [Mathematics for Machine Learning](https://github.com/mml-book/mml-book.github.io). Cambridge University Press. p. 181. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9781108455145](https://en.wikipedia.org/wiki/Special:BookSources/9781108455145).
2.  ^       Park, Kun Il (2018). *Fundamentals of Probability and Stochastic Processes with Applications to Communications*. Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-319-68074-3](https://en.wikipedia.org/wiki/Special:BookSources/978-3-319-68074-3).
3.  Montgomery, Douglas C.; Runger, George C. (2003). [Applied Statistics and Probability for Engineers](http://www.um.edu.ar/math/montgomery.pdf) (PDF). John Wiley & Sons, Inc. p. 104. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-20454-4](https://en.wikipedia.org/wiki/Special:BookSources/0-471-20454-4). [Archived](https://web.archive.org/web/20120730233253/http://www.um.edu.ar/math/montgomery.pdf) (PDF) from the original on 2012-07-30.
4.  Zwillinger, Daniel; Kokoska, Stephen (2010). *CRC Standard Probability and Statistics Tables and Formulae*. CRC Press. p. 49. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-58488-059-2](https://en.wikipedia.org/wiki/Special:BookSources/978-1-58488-059-2).
5.  Gentle, J.E. (2009). [Computational Statistics](https://books.google.com/books?id=m4r-KVxpLsAC&pg=PA348). [Springer](https://en.wikipedia.org/wiki/Springer_Science%2BBusiness_Media). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-98145-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-98145-1). Retrieved 2010-08-06.<sup>\[*[page needed](https://en.wikipedia.org/wiki/Wikipedia:Citing_sources)*\]</sup>
6.  [Monti, K. L.](https://en.wikipedia.org/wiki/Katherine_Monti) (1995). "Folded Empirical Distribution Function Curves (Mountain Plots)". *The American Statistician*. **49** (4): 342–345. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2684570](https://doi.org/10.2307%2F2684570). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2684570](https://www.jstor.org/stable/2684570).
7.  Xue, J. H.; Titterington, D. M. (2011). ["The p-folded cumulative distribution function and the mean absolute deviation from the p-quantile"](https://hal.archives-ouvertes.fr/hal-00753950/file/PEER_stage2_10.1016%252Fj.spl.2011.03.014.pdf) (PDF). *Statistics & Probability Letters*. **81** (8): 1179–1182. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.spl.2011.03.014](https://doi.org/10.1016%2Fj.spl.2011.03.014).
8.  Chan, Stanley H. (2021). [Introduction to Probability for Data Science](https://books.google.com/books?id=GR2jzgEACAAJ). Michigan Publishing. p. 18. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-60785-746-4](https://en.wikipedia.org/wiki/Special:BookSources/978-1-60785-746-4).
9.  Hesse, C. (1990). "Rates of convergence for the empirical distribution function and the empirical characteristic function of a broad class of linear processes". *Journal of Multivariate Analysis*. **35** (2): 186–202. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/0047-259X(90)90024-C](https://doi.org/10.1016%2F0047-259X%2890%2990024-C).
10. ["Joint Cumulative Distribution Function (CDF)"](https://math.info/Probability/Joint_CDF/). *math.info*. Retrieved 2019-12-11.
11. ["Archived copy"](https://web.archive.org/web/20160222051842/http://www.math.wustl.edu/~hgan/Prob2014/slides.259-327.pdf) (PDF). *www.math.wustl.edu*. Archived from [the original](http://www.math.wustl.edu/~hgan/Prob2014/slides.259-327.pdf) (PDF) on 22 February 2016. Retrieved 13 January 2022.`{{`[`cite web`](https://en.wikipedia.org/wiki/Template:Cite_web)`}}`: CS1 maint: archived copy as title ([link](https://en.wikipedia.org/wiki/Category:CS1_maint:_archived_copy_as_title))

## External links

- ![[media/62933b50408636b28d12e90be87b5b81874d2f90.png]] Media related to [Cumulative distribution functions](https://commons.wikimedia.org/wiki/Category:Cumulative_distribution_functions) at Wikimedia Commons
