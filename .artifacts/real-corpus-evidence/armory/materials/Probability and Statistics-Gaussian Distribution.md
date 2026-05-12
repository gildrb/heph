[[probability-statistics.base]]

> Source: [Normal distribution](https://en.wikipedia.org/wiki/Normal_distribution)
> License: Wikipedia content is available under CC BY-SA 4.0.

<table class="infobox infobox-table ib-prob-dist">

Normal distribution

&#10;

Probability density function
![[media/f3e7ded74af72f1c3d8432a16c9b52ef982f6d93.png]]

The red curve is the [standard normal distribution](#Standard_normal_distribution).

Cumulative distribution function
![[media/4f7b5e652396d6ccc83141cda1723c44bc147378.png]]

Notation
${\mathcal {N}}(\mu ,\sigma ^{2})$

[Parameters](https://en.wikipedia.org/wiki/Statistical_parameter)
$\mu \in \mathbb {R}$ = [mean](https://en.wikipedia.org/wiki/Mean) ([location](https://en.wikipedia.org/wiki/Location_parameter))<br />
$\sigma ^{2}\in \mathbb {R} _{>0}$ = [variance](https://en.wikipedia.org/wiki/Variance) (squared [scale](https://en.wikipedia.org/wiki/Scale_parameter))

[Support](https://en.wikipedia.org/wiki/Support_(mathematics))
$x\in \mathbb {R}$

[[Probability Density Function|PDF]]
${\frac {1}{\sqrt {2\pi \sigma ^{2}}}}e^{-{\frac {(x-\mu )^{2}}{2\sigma ^{2}}}}$

[[Cumulative Distribution Function|CDF]]
$\Phi \left({\frac {x-\mu }{\sigma }}\right)={\frac {1}{2}}\left[1+\operatorname {erf} \left({\frac {x-\mu }{\sigma {\sqrt {2}}}}\right)\right]$

[Quantile](https://en.wikipedia.org/wiki/Quantile_function)
$\mu +\sigma {\sqrt {2}}\operatorname {erf} ^{-1}(2p-1)$

[Mean](https://en.wikipedia.org/wiki/Expected_value)
$\mu$

[Median](https://en.wikipedia.org/wiki/Median)
$\mu$

[Mode](https://en.wikipedia.org/wiki/Mode_(statistics))
$\mu$

[Variance](https://en.wikipedia.org/wiki/Variance)
$\sigma ^{2}$

[MAD](https://en.wikipedia.org/wiki/Median_absolute_deviation)
$\sigma {\sqrt {2}}\,\operatorname {erf} ^{-1}(1/2)$

[AAD](https://en.wikipedia.org/wiki/Mean_absolute_deviation)
$\sigma {\sqrt {2/\pi }}$

[Skewness](https://en.wikipedia.org/wiki/Skewness)
$0$

[Excess kurtosis](https://en.wikipedia.org/wiki/Excess_kurtosis)
$0$

[Entropy](https://en.wikipedia.org/wiki/Information_entropy)
${\tfrac {1}{2}}\log(2\pi e\sigma ^{2})$

[[Moment Generating Function|MGF]]
$\exp(\mu t+\sigma ^{2}t^{2}/2)$

[[Characteristic Function|CF]]
$\exp(i\mu t-\sigma ^{2}t^{2}/2)$

[[Fisher Information]]
<p>${\mathcal {I}}(\mu ,\sigma )={\begin{pmatrix}1/\sigma ^{2}&0\\0&2/\sigma ^{2}\end{pmatrix}}$</p>
${\mathcal {I}}(\mu ,\sigma ^{2})={\begin{pmatrix}1/\sigma ^{2}&0\\0&1/(2\sigma ^{4})\end{pmatrix}}$

[[Kullback-Leibler Divergence|Kullback–Leibler divergence]]
${1 \over 2}\left\{\left({\frac {\sigma _{0}}{\sigma _{1}}}\right)^{2}+{\frac {(\mu _{1}-\mu _{0})^{2}}{\sigma _{1}^{2}}}-1+\ln {\sigma _{1}^{2} \over \sigma _{0}^{2}}\right\}$

[Expected shortfall](https://en.wikipedia.org/wiki/Expected_shortfall)
$\mu +\sigma {\frac {{\frac {1}{\sqrt {2\pi }}}e^{\frac {-\left(q_{p}\left({\frac {X-\mu }{\sigma }}\right)\right)^{2}}{2}}}{1-p}}$

</table>

In [probability theory](https://en.wikipedia.org/wiki/Probability_theory) and [statistics](https://en.wikipedia.org/wiki/Statistics), a **normal distribution** or **Gaussian distribution** is a type of [continuous probability distribution](https://en.wikipedia.org/wiki/Continuous_probability_distribution) for a [real-valued](https://en.wikipedia.org/wiki/Real_number) [random variable](https://en.wikipedia.org/wiki/Random_variable). The general form of its [[Probability Density Function]] is 

$$
f(x)={\frac {1}{\sqrt {2\pi \sigma ^{2}}}}\exp {\left(-{\frac {(x-\mu )^{2}}{2\sigma ^{2}}}\right)}\,.
$$

 The parameter $\mu$ is the [mean](https://en.wikipedia.org/wiki/Mean#Mean_of_a_probability_distribution) or [expectation](https://en.wikipedia.org/wiki/Expected_value) of the distribution (and also its [median](https://en.wikipedia.org/wiki/Median) and [mode](https://en.wikipedia.org/wiki/Mode_(statistics) "Mode (statistics)")), while the parameter $\sigma ^{2}$ is the [variance](https://en.wikipedia.org/wiki/Variance). The [standard deviation](https://en.wikipedia.org/wiki/Standard_deviation) of the distribution is the positive value $\sigma$ (sigma). A random variable with a Gaussian distribution is said to be **normally distributed** and is called a **normal deviate**.

Normal distributions are important in [statistics](https://en.wikipedia.org/wiki/Statistics) and are often used in the [natural](https://en.wikipedia.org/wiki/Natural_science) and [social sciences](https://en.wikipedia.org/wiki/Social_science) to represent real-valued [random variables](https://en.wikipedia.org/wiki/Random_variable) whose distributions are not known. Their importance is partly due to the [[Central Limit Theorem]]. It states that the average of many [statistically independent](https://en.wikipedia.org/wiki/Statistically_independent) samples (observations) of a random variable with finite mean and variance is itself a random variable—whose distribution [converges](https://en.wikipedia.org/wiki/Convergence_in_distribution) to a normal distribution as the number of samples increases. Therefore, physical quantities that are expected to be the sum of many independent processes, such as [measurement errors](https://en.wikipedia.org/wiki/Measurement_error), often have distributions that are nearly normal.

Moreover, Gaussian distributions have some unique properties that are valuable in analytic studies. For instance, any [linear combination](https://en.wikipedia.org/wiki/Linear_combination) of a fixed collection of independent normal deviates is a normal deviate. Many results and methods, such as [propagation of uncertainty](https://en.wikipedia.org/wiki/Propagation_of_uncertainty) and [least squares](https://en.wikipedia.org/wiki/Least_squares) parameter fitting, can be derived analytically in explicit form when the relevant variables are normally distributed.

A normal distribution is sometimes informally called a **bell curve**. However, many other distributions are [bell-shaped](https://en.wikipedia.org/wiki/Bell-shaped_function) (such as the [Cauchy](https://en.wikipedia.org/wiki/Cauchy_distribution), [Student's t](https://en.wikipedia.org/wiki/Student%27s_t-distribution), and [logistic](https://en.wikipedia.org/wiki/Logistic_distribution) distributions). (For other names, see *[Naming](#Naming)*.)

The [univariate probability distribution](https://en.wikipedia.org/wiki/Univariate_distribution) is generalized for [vectors](https://en.wikipedia.org/wiki/Vector_(mathematics_and_physics) "Vector (mathematics and physics)") in the [[Multivariate Normal Distribution]] and for matrices in the [matrix normal distribution](https://en.wikipedia.org/wiki/Matrix_normal_distribution).

## Definitions

### Standard normal distribution

The simplest case of a normal distribution is known as the **standard normal distribution** or **unit normal distribution**. This is a special case when $\mu =0$ and $\sigma ^{2}=1$, and it is described by this [[Probability Density Function]] (or density): 

$$
\varphi (z)={\frac {e^{-z^{2}/2}}{\sqrt {2\pi }}}\,.
$$

 The variable $z$ has a mean of 0 and a variance and standard deviation of 1. The density $\varphi (z)$ has its peak value ${\frac {1}{\sqrt {2\pi }}}$ at $z=0$ and [inflection points](https://en.wikipedia.org/wiki/Inflection_point) at $z=+1$ and $z=-1$.

Although the density above is most commonly known as the *standard normal,* a few authors have used that term to describe other versions of the normal distribution. [Carl Friedrich Gauss](https://en.wikipedia.org/wiki/Carl_Friedrich_Gauss), for example, once defined the standard normal as $\varphi (z)={\frac {e^{-z^{2}}}{\sqrt {\pi }}},$ which has a variance of ${\frac {1}{2}}$, and [Stephen Stigler](https://en.wikipedia.org/wiki/Stephen_Stigler) once defined the standard normal as $\varphi (z)=e^{-\pi z^{2}},$ which has a simple functional form and a variance of $\sigma ^{2}={\frac {1}{2\pi }}.$

### General normal distribution

If $Z$ is a [standard normal deviate](https://en.wikipedia.org/wiki/Standard_normal_deviate), then $X=\sigma Z+\mu$ will have a normal distribution with expected value $\mu$ and standard deviation $\sigma$. This is equivalent to saying that the standard normal distribution $Z$ can be scaled/stretched by a factor of $\sigma$ and shifted by $\mu$ to yield a different normal distribution, called $X$.

Conversely, if $X$ is a normal deviate with parameters $\mu$ and $\sigma ^{2}$, then this $X$ distribution can be re-scaled and shifted via the formula $Z=(X-\mu )/\sigma$ to convert it to the standard normal distribution. This variate is also called the standardized form of $X$.

In particular, the probability density function for $X$ can be written in terms of the standard normal distribution $\varphi$ (with zero mean and unit variance): 

$$
f(x\mid \mu ,\sigma ^{2})={\frac {1}{\sigma }}\varphi \left({\frac {x-\mu }{\sigma }}\right)\,.
$$

 The probability density must be scaled by $1/\sigma$ so that the [integral](https://en.wikipedia.org/wiki/Integral) is still 1.

### Notation

The probability density of the standard Gaussian distribution (standard normal distribution, with zero mean and unit variance) is often denoted with the Greek letter $\phi$ ([phi](https://en.wikipedia.org/wiki/Phi)). The variant form of the Greek letter phi, $\varphi$, is also used quite often.

The normal distribution is often referred to as $N(\mu ,\sigma ^{2})$ or ${\mathcal {N}}(\mu ,\sigma ^{2})$. Thus when a random variable $X$ is normally distributed with mean $\mu$ and standard deviation $\sigma$, one may write

$$
X\sim {\mathcal {N}}(\mu ,\sigma ^{2}).
$$

### Alternative parameterizations

Some authors advocate using the [precision](https://en.wikipedia.org/wiki/Precision_(statistics) "Precision (statistics)") $\tau$ as the parameter defining the width of the distribution, instead of the standard deviation $\sigma$ or the variance $\sigma ^{2}$. The precision is normally defined as the reciprocal of the variance, $1/\sigma ^{2}$. The formula for the distribution then becomes 

$$
f(x)={\sqrt {\frac {\tau }{2\pi }}}e^{-\tau (x-\mu )^{2}/2}.
$$

This choice is claimed to have advantages in numerical computations when $\sigma$ is very close to zero, and simplifies formulas in some contexts, such as in the [Bayesian inference](https://en.wikipedia.org/wiki/Bayesian_statistics) of variables with [[Multivariate Normal Distribution]].

Alternatively, the reciprocal of the standard deviation $\tau '=1/\sigma$ might be defined as the *precision*, in which case the expression of the normal distribution becomes 

$$
f(x)={\frac {\tau '}{\sqrt {2\pi }}}e^{-(\tau ')^{2}(x-\mu )^{2}/2}.
$$

According to Stigler, this formulation is advantageous because of a much simpler and easier-to-remember formula, and simple approximate formulas for the [quantiles](https://en.wikipedia.org/wiki/Quantile) of the distribution.

Normal distributions form an [[Exponential Family]] with [natural parameters](https://en.wikipedia.org/wiki/Natural_parameter) $\textstyle \theta _{1}={\frac {\mu }{\sigma ^{2}}}$ and $\textstyle \theta _{2}=-{\frac {1}{2\sigma ^{2}}}$, and natural statistics x and *x*<sup>2</sup>. The dual expectation parameters for normal distribution are *η*<sub>1</sub> = *μ* and *η*<sub>2</sub> = *μ*<sup>2</sup> + *σ*<sup>2</sup>.

### Cumulative distribution function

The [[Cumulative Distribution Function]] (CDF) of the standard normal distribution, usually denoted with the capital Greek letter $\Phi$, is the integral 

$$
\Phi (x)={\frac {1}{\sqrt {2\pi }}}\int _{-\infty }^{x}e^{-t^{2}/2}\,dt\,.
$$

The related [error function](https://en.wikipedia.org/wiki/Error_function) $\operatorname {erf} (x)$ gives the probability of a random variable, with normal distribution of mean 0 and variance 1/2, falling in the range $[-x,x]$. That is: 

$$
\operatorname {erf} (x)={\frac {1}{\sqrt {\pi }}}\int _{-x}^{x}e^{-t^{2}}\,dt={\frac {2}{\sqrt {\pi }}}\int _{0}^{x}e^{-t^{2}}\,dt\,.
$$

These integrals cannot be expressed in terms of elementary functions, and are often said to be [special functions](https://en.wikipedia.org/wiki/Special_function). However, many numerical approximations are known; see [below](#Numerical_approximations_for_the_normal_cumulative_distribution_function_and_normal_quantile_function) for more.

The two functions are closely related, namely 

$$
\Phi (x)={\frac {1}{2}}\left[1+\operatorname {erf} \left({\frac {x}{\sqrt {2}}}\right)\right].
$$

For a generic normal distribution with density $f$, mean $\mu$ and variance $\sigma ^{2}$, the cumulative distribution function is 

$$
F(x)=\Phi {\left({\frac {x-\mu }{\sigma }}\right)}={\frac {1}{2}}\left[1+\operatorname {erf} \left({\frac {x-\mu }{\sigma {\sqrt {2}}}}\right)\right].
$$

The probability that x lies between a and b with a \< b is therefore

$$
\operatorname {P} (a<x\leq b)={\frac {1}{2}}\left[\operatorname {erf} \left({\frac {b-\mu }{\sigma {\sqrt {2}}}}\right)-\operatorname {erf} \left({\frac {a-\mu }{\sigma {\sqrt {2}}}}\right)\right]
$$

The complement of the standard normal cumulative distribution function, $Q(x)=1-\Phi (x)$, is often called the [Q-function](https://en.wikipedia.org/wiki/Q-function), especially in engineering texts. It gives the probability that the value of a standard normal random variable $X$ will exceed $x$: $P(X>x)$. Other definitions of the $Q$-function, all of which are simple transformations of $\Phi$, are also used occasionally.

The [graph](https://en.wikipedia.org/wiki/Graph_of_a_function) of the standard normal cumulative distribution function $\Phi$ has 2-fold [rotational symmetry](https://en.wikipedia.org/wiki/Rotational_symmetry) around the point (0,1/2); that is, $\Phi (-x)=1-\Phi (x)$. Its [antiderivative](https://en.wikipedia.org/wiki/Antiderivative) (indefinite integral) can be expressed as follows: 

$$
\int \Phi (x)\,dx=x\Phi (x)+\varphi (x)+C.
$$

An [asymptotic expansion](https://en.wikipedia.org/wiki/Asymptotic_expansion) of the cumulative distribution function for large x can be derived using [integration by parts](https://en.wikipedia.org/wiki/Integration_by_parts): 

$$
\Phi (x)={\frac {1}{2}}+{\frac {1}{\sqrt {2\pi }}}e^{-x^{2}/2}\sum _{n=0}^{\infty }{\frac {1}{(2n+1)!!}}x^{2n+1}\,.
$$

 where $!!$ denotes the [double factorial](https://en.wikipedia.org/wiki/Double_factorial). For more, see [Error function § Asymptotic expansion](https://en.wikipedia.org/wiki/Error_function#Asymptotic_expansion).

#### Taylor series representation

The [[Taylor Series]] for the normal distribution $\varphi$ can be derived by substituting $-{\tfrac {1}{2}}x^{2}$ into the [Taylor series for the exponential function](https://en.wikipedia.org/wiki/Exponential_function#Power_series): 

$$
\varphi (x)={\frac {1}{\sqrt {2\pi }}}\sum _{n=0}^{\infty }{\frac {(-1)^{n}}{n!\,2^{n}}}x^{2n}
$$

 As with the series for the exponential function, this series converges everywhere on the real line $\mathbb {R}$ (and more generally throughout the complex plane $\mathbb {C}$).

This series can be integrated term by term to obtain the Taylor series for the cumulative distribution function $\Phi$, which also converges throughout the complex plane: 

$$
\Phi (x)={\frac {1}{2}}+{\frac {1}{\sqrt {2\pi }}}\sum _{n=0}^{\infty }{\frac {(-1)^{n}}{n!\,2^{n}(2n+1)}}x^{2n+1}.
$$

 The constant ${\frac {1}{2}}=\Phi (0)$ is determined by symmetry of $\varphi$ (i.e. $\varphi (-x)=\varphi (x)$). With an [expectation value](https://en.wikipedia.org/wiki/Expectation_value) $\mu \in \mathbb {R}$ and the [variance](https://en.wikipedia.org/wiki/Variance) $\sigma ^{2}>0$ the linear transformation $F(x)=\Phi \left({\frac {x-\mu }{\sigma }}\right)$ provides the [[Taylor Series]] of $F$ for an arbitrary normal distribution:

$F(x)={\frac {1}{2}}+{\frac {1}{\sqrt {2\pi \sigma ^{2}}}}\cdot \sum _{n=0}^{\infty }{\frac {(-1)^{n}}{n!\cdot (2\cdot \sigma ^{2})^{n}\cdot (2n+1)}}\cdot (x-\mu )^{2n+1}$

With the [identity theorem](https://en.wikipedia.org/wiki/Identity_theorem) the Taylor series is unique on the complex numbers $\mathbb {C}$.

#### Recursive computation with Taylor series

The recurrence relation for [Hermite polynomials](https://en.wikipedia.org/wiki/Hermite_polynomials) He<sub>*n*</sub>(*x*) may be used to efficiently construct the [[Taylor Series]] expansion about any point *x*<sub>0</sub>: 

$$
\Phi (x)=\sum _{n=0}^{\infty }{\frac {\Phi ^{(n)}(x_{0})}{n!}}(x-x_{0})^{n}\,,
$$

 where: 

$$
{\begin{aligned}\Phi ^{(0)}(x_{0})&={\frac {1}{\sqrt {2\pi }}}\int _{-\infty }^{x_{0}}e^{-t^{2}/2}\,dt\\\Phi ^{(1)}(x_{0})&={\frac {1}{\sqrt {2\pi }}}e^{-x_{0}^{2}/2}\\\Phi ^{(n)}(x_{0})&=-\left(x_{0}\Phi ^{(n-1)}(x_{0})+(n-2)\Phi ^{(n-2)}(x_{0})\right),&n\geq 2\,.\end{aligned}}
$$

#### Standard deviation and coverage

![[media/168085eb5a8a96fe7a4a173e58ed0181e09fee3e.png]]
For the normal distribution, the values less than one standard deviation from the mean account for 68.27% of the set; while two standard deviations from the mean account for 95.45%; and three standard deviations account for 99.73%.

About 68% of values drawn from a normal distribution are within one standard deviation σ from the mean; about 95% of the values lie within two standard deviations; and about 99.7% are within three standard deviations. This is known as the [68–95–99.7 (empirical) rule](https://en.wikipedia.org/wiki/68%E2%80%9395%E2%80%9399.7_rule), or the *3-sigma rule*.

More precisely, the probability that a normal deviate lies in the range between $\mu -n\sigma$ and $\mu +n\sigma$ is given by 

$$
F(\mu +n\sigma )-F(\mu -n\sigma )=\Phi (n)-\Phi (-n)=\operatorname {erf} \left({\frac {n}{\sqrt {2}}}\right).
$$

 To 12 significant digits, the values for $n=1,2,\ldots ,6$ are:

<table class="wikitable" style="text-align:center;margin-left:24pt">

$n$
$p=F(\mu +n\sigma )-F(\mu -n\sigma )$
$1-p$
${\text{or }}1{\text{ in }}(1-p)$
[OEIS](https://en.wikipedia.org/wiki/OEIS)

&#10;
1
0.682689492137
0.317310507863
<table data-cellpadding="0" data-cellspacing="0" style="width: 16em;">

3
.15148718753

</table>
[OEIS](https://en.wikipedia.org/wiki/On-Line_Encyclopedia_of_Integer_Sequences): [A178647](https://oeis.org/A178647)

2
0.954499736104
0.045500263896
<table data-cellpadding="0" data-cellspacing="0" style="width: 16em;">

21
.9778945080

</table>
[OEIS](https://en.wikipedia.org/wiki/On-Line_Encyclopedia_of_Integer_Sequences): [A110894](https://oeis.org/A110894)

3
0.997300203937
0.002699796063
<table data-cellpadding="0" data-cellspacing="0" style="width: 16em;">

370
.398347345

</table>
[OEIS](https://en.wikipedia.org/wiki/On-Line_Encyclopedia_of_Integer_Sequences): [A270712](https://oeis.org/A270712)

4
0.999936657516
0.000063342484
<table data-cellpadding="0" data-cellspacing="0" style="width: 16em;">

15787
.1927673

</table>

5
0.999999426697
0.000000573303
<table data-cellpadding="0" data-cellspacing="0" style="width: 16em;">

1744277
.89362

</table>

6
0.999999998027
0.000000001973
<table data-cellpadding="0" data-cellspacing="0" style="width: 16em;">

506797345
.897

</table>

</table>

For large $n$, one can use the approximation 

$$
1-p\approx {\frac {\sqrt {2}}{n{\sqrt {\pi e^{n^{2}}}}}}
$$

#### Quantile function

The [quantile function](https://en.wikipedia.org/wiki/Quantile_function) of a distribution is the inverse of the cumulative distribution function. The quantile function of the standard normal distribution is called the [probit function](https://en.wikipedia.org/wiki/Probit_function), and can be expressed in terms of the inverse [error function](https://en.wikipedia.org/wiki/Error_function): 

$$
\Phi ^{-1}(p)={\sqrt {2}}\operatorname {erf} ^{-1}(2p-1),\quad p\in (0,1).
$$

 For a normal random variable with mean $\mu$ and variance $\sigma ^{2}$, the quantile function is 

$$
F^{-1}(p)=\mu +\sigma \Phi ^{-1}(p)=\mu +\sigma {\sqrt {2}}\operatorname {erf} ^{-1}(2p-1),\quad p\in (0,1).
$$

 The [quantile](https://en.wikipedia.org/wiki/Quantile) $\Phi ^{-1}(p)$ of the standard normal distribution is commonly denoted as $z_{p}$. These values are used in [[Hypothesis Testing]], construction of [confidence intervals](https://en.wikipedia.org/wiki/Confidence_interval) and [Q–Q plots](https://en.wikipedia.org/wiki/Q%E2%80%93Q_plot). A normal random variable $X$ will exceed $\mu +z_{p}\sigma$ with probability $1-p$, and will lie outside the interval $\mu \pm z_{p}\sigma$ with probability $2(1-p)$. In particular, the quantile $z_{0.975}$ is [1.96](https://en.wikipedia.org/wiki/1.96); therefore a normal random variable will lie outside the interval $\mu \pm 1.96\sigma$ in only 5% of cases.

The following table gives the quantile $z_{p}$ such that $X$ will lie in the range $\mu \pm z_{p}\sigma$ with a specified probability $p$. These values are useful to determine [tolerance interval](https://en.wikipedia.org/wiki/Tolerance_interval) for [sample averages](https://en.wikipedia.org/wiki/Sample_mean_and_sample_covariance#Sample_mean) and other statistical [estimators](https://en.wikipedia.org/wiki/Estimator) with normal (or [asymptotically](https://en.wikipedia.org/wiki/Asymptotic) normal) distributions. The following table shows ${\sqrt {2}}\operatorname {erf} ^{-1}(p)=\Phi ^{-1}\left({\frac {p+1}{2}}\right)$, not $\Phi ^{-1}(p)$ as defined above.

<table class="wikitable" style="text-align:left;margin-left:24pt;border:none;">

$p$
$z_{p}$
 
$p$
$z_{p}$

0.80
1.281551565545
0.999
3.290526731492

0.90
1.644853626951
0.9999
3.890591886413

0.95
1.959963984540
0.99999
4.417173413469

0.98
2.326347874041
0.999999
4.891638475699

0.99
2.575829303549
0.9999999
5.326723886384

0.995
2.807033768344
0.99999999
5.730728868236

0.998
3.090232306168
0.999999999
6.109410204869

</table>

For small $p$, the quantile function has the useful [asymptotic expansion](https://en.wikipedia.org/wiki/Asymptotic_expansion) $\Phi ^{-1}(p)=-{\sqrt {\ln {\frac {1}{p^{2}}}-\ln \ln {\frac {1}{p^{2}}}-\ln(2\pi )}}+{\mathcal {o}}(1).$<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

#### Using Newton's method for the quantile function

Any of the described approaches for computing the cumulative distribution function $\Phi (x)$ can be used with [Newton's method](https://en.wikipedia.org/wiki/Newton%27s_method) to find the value of $x$ for which $\Phi (x)=q$ for some desired quantile $q$. Starting with an initial, approximately correct guess $x_{0}$, increasingly better approximations $x_{1}$, $x_{2}$, ... can be calculated iteratively with 

$$
x_{n}=x_{n-1}-{\frac {\Phi (x_{n-1})-q}{\varphi (x_{n-1})}}\,.
$$

## Properties

The normal distribution is the only distribution whose [cumulants](https://en.wikipedia.org/wiki/Cumulant) beyond the first two (i.e., other than the mean and [variance](https://en.wikipedia.org/wiki/Variance)) are zero. It is also the continuous distribution with the [maximum entropy](https://en.wikipedia.org/wiki/Maximum_entropy_probability_distribution) for a specified mean and variance. Geary has shown, assuming that the mean and variance are finite, that the normal distribution is the only distribution where the mean and variance calculated from a set of independent draws are independent of each other.

The normal distribution is a subclass of the [elliptical distributions](https://en.wikipedia.org/wiki/Elliptical_distribution). The normal distribution is [symmetric](https://en.wikipedia.org/wiki/Symmetric_distribution) about its mean, and is non-zero over the entire real line. As such it may not be a suitable model for variables that are inherently positive or strongly skewed, such as the [weight](https://en.wikipedia.org/wiki/Weight) of a person or the price of a [share of stock](https://en.wikipedia.org/wiki/Share_(finance) "Share (finance)"). Such variables may be better described by other distributions, such as the [log-normal distribution](https://en.wikipedia.org/wiki/Log-normal_distribution) or the [Pareto distribution](https://en.wikipedia.org/wiki/Pareto_distribution).

The value of the normal density is practically zero when the value $x$ lies more than a few [standard deviations](https://en.wikipedia.org/wiki/Standard_deviation) away from the mean (e.g., a spread of three standard deviations covers all but 0.27% of the total distribution). Therefore, it may not be an appropriate model when one expects a significant fraction of [outliers](https://en.wikipedia.org/wiki/Outlier)—values that lie many standard deviations away from the mean—and least squares and other [statistical inference](https://en.wikipedia.org/wiki/Statistical_inference) methods that are optimal for normally distributed variables often become highly unreliable when applied to such data. In those cases, a more [heavy-tailed](https://en.wikipedia.org/wiki/Heavy-tailed) distribution should be assumed and appropriate [robust statistical inference](https://en.wikipedia.org/wiki/Robust_statistics) methods applied.

The Gaussian distribution belongs to the family of [stable distributions](https://en.wikipedia.org/wiki/Stable_distribution) which are the attractors of sums of [independent, identically distributed](https://en.wikipedia.org/wiki/Independent,_identically_distributed) distributions whether or not the mean or variance is finite. Except for the Gaussian which is a limiting case, all stable distributions have heavy tails and infinite variance. It is one of the few distributions that are stable and that have probability density functions that can be expressed analytically, the others being the [Cauchy distribution](https://en.wikipedia.org/wiki/Cauchy_distribution) and the [Lévy distribution](https://en.wikipedia.org/wiki/L%C3%A9vy_distribution).

### Symmetries and derivatives

The normal distribution with density $f(x)$ (mean $\mu$ and variance $\sigma ^{2}>0$) has the following properties:

- It is symmetric around the point $x=\mu ,$ which is at the same time the [mode](https://en.wikipedia.org/wiki/Mode_(statistics) "Mode (statistics)"), the [median](https://en.wikipedia.org/wiki/Median) and the [mean](https://en.wikipedia.org/wiki/Mean) of the distribution.
- It is [unimodal](https://en.wikipedia.org/wiki/Unimodal): its first [derivative](https://en.wikipedia.org/wiki/Derivative) is positive for $x<\mu ,$ negative for $x>\mu ,$ and zero only at $x=\mu .$
- The area bounded by the curve and the $x$-axis is unity (i.e. equal to one).
- Its first derivative is $f'(x)=-{\frac {x-\mu }{\sigma ^{2}}}f(x).$
- Its second derivative is $f''(x)={\frac {(x-\mu )^{2}-\sigma ^{2}}{\sigma ^{4}}}f(x).$
- Its density has two [inflection points](https://en.wikipedia.org/wiki/Inflection_point) (where the second derivative of $f$ is zero and changes sign), located one standard deviation away from the mean, namely at $x=\mu -\sigma$ and $x=\mu +\sigma .$
- Its density is [log-concave](https://en.wikipedia.org/wiki/Logarithmically_concave_function).
- Its density is infinitely [differentiable](https://en.wikipedia.org/wiki/Differentiable), indeed [supersmooth](https://en.wikipedia.org/wiki/Supersmooth) of order 2.

Furthermore, the density $\varphi$ of the standard normal distribution (i.e. $\mu =0$ and $\sigma =1$) also has the following properties:

- Its first derivative is $\varphi '(x)=-x\varphi (x).$
- Its second derivative is $\varphi ''(x)=(x^{2}-1)\varphi (x)$
- More generally, its nth derivative is $\varphi ^{(n)}(x)=(-1)^{n}\operatorname {He} _{n}(x)\varphi (x),$ where $\operatorname {He} _{n}(x)$ is the nth (probabilist) [Hermite polynomial](https://en.wikipedia.org/wiki/Hermite_polynomial).
- The probability that a normally distributed variable $X$ with known $\mu$ and $\sigma ^{2}$ is in a particular set, can be calculated given that the fraction $Z=(X-\mu )/\sigma$ has a standard normal distribution.

### Moments

The plain and absolute [moments](https://en.wikipedia.org/wiki/Moment_(mathematics) "Moment (mathematics)") of a variable $X$ are the expected values of $X^{p}$ and $|X|^{p}$, respectively. If the expected value $\mu$ of $X$ is zero, these parameters are called *central moments;* otherwise, these parameters are called *non-central moments.* Usually we are interested only in moments with integer order $p$.

If $X$ has a normal distribution, the non-central moments exist and are finite for any $p$ whose real part is greater than −1. For any non-negative integer $p$, the plain central moments are: 

$$
\operatorname {E} \left[(X-\mu )^{p}\right]={\begin{cases}0&{\text{if }}p{\text{ is odd,}}\\\sigma ^{p}(p-1)!!&{\text{if }}p{\text{ is even.}}\end{cases}}
$$

 Here $n!!$ denotes the [double factorial](https://en.wikipedia.org/wiki/Double_factorial), that is, the product of all numbers from $n$ to 1 that have the same parity as $n.$

The central absolute moments coincide with plain moments for all even orders, but are nonzero for odd orders. For any non-negative integer $p,$

$$
{\begin{aligned}\operatorname {E} \left[|X-\mu |^{p}\right]&=\sigma ^{p}(p-1)!!\cdot {\begin{cases}{\sqrt {\frac {2}{\pi }}}&{\text{if }}p{\text{ is odd}}\\1&{\text{if }}p{\text{ is even}}\end{cases}}\\[8pt]&=\sigma ^{p}\cdot {\frac {2^{p/2}\Gamma \left({\frac {p+1}{2}}\right)}{\sqrt {\pi }}}.\end{aligned}}
$$

 The last formula is valid also for any non-integer $p>-1.$ When the mean $\mu \neq 0,$ the plain and absolute moments can be expressed in terms of [confluent hypergeometric functions](https://en.wikipedia.org/wiki/Confluent_hypergeometric_function) ${}_{1}F_{1}$ and $U.$ 

$$
{\begin{aligned}\operatorname {E} \left[X^{p}\right]&=\sigma ^{p}\cdot {\left(-i{\sqrt {2}}\right)}^{p}\,U{\left(-{\frac {p}{2}},{\frac {1}{2}},-{\frac {\mu ^{2}}{2\sigma ^{2}}}\right)},\\\operatorname {E} \left[|X|^{p}\right]&=\sigma ^{p}\cdot 2^{p/2}{\frac {\Gamma {\left({\frac {1+p}{2}}\right)}}{\sqrt {\pi }}}\,{}_{1}F_{1}{\left(-{\frac {p}{2}},{\frac {1}{2}},-{\frac {\mu ^{2}}{2\sigma ^{2}}}\right)}.\end{aligned}}
$$

These expressions remain valid even when $p>-1$ is not an integer. See also [generalized Hermite polynomials](https://en.wikipedia.org/wiki/Hermite_polynomials#%22Negative_variance%22).

|  |  |  |
|----|----|----|
| Order | Non-central moment, $\operatorname {E} \left[X^{p}\right]$ | Central moment, $\operatorname {E} \left[(X-\mu )^{p}\right]$ |
| 0 | $1$ | $1$ |
| 1 | $\mu$ | $0$ |
| 2 | $\mu ^{2}+\sigma ^{2}$ | $\sigma ^{2}$ |
| 3 | $\mu ^{3}+3\mu \sigma ^{2}$ | $0$ |
| 4 | $\mu ^{4}+6\mu ^{2}\sigma ^{2}+3\sigma ^{4}$ | $3\sigma ^{4}$ |
| 5 | $\mu ^{5}+10\mu ^{3}\sigma ^{2}+15\mu \sigma ^{4}$ | $0$ |
| 6 | $\mu ^{6}+15\mu ^{4}\sigma ^{2}+45\mu ^{2}\sigma ^{4}+15\sigma ^{6}$ | $15\sigma ^{6}$ |
| 7 | $\mu ^{7}+21\mu ^{5}\sigma ^{2}+105\mu ^{3}\sigma ^{4}+105\mu \sigma ^{6}$ | $0$ |
| 8 | $\mu ^{8}+28\mu ^{6}\sigma ^{2}+210\mu ^{4}\sigma ^{4}+420\mu ^{2}\sigma ^{6}+105\sigma ^{8}$ | $105\sigma ^{8}$ |

The expectation of $X$ conditioned on the event that $X$ lies in an interval $[a,b]$ is given by 

$$
\operatorname {E} \left[X\mid a<X<b\right]=\mu -\sigma ^{2}{\frac {f(b)-f(a)}{F(b)-F(a)}}\,,
$$

 where $f$ and $F$ respectively are the density and the cumulative distribution function of $X$. For $b=\infty$ this is known as the [inverse Mills ratio](https://en.wikipedia.org/wiki/Inverse_Mills_ratio). Note that above, density $f$ of $X$ is used instead of standard normal density as in inverse Mills ratio, so here we have $\sigma ^{2}$ instead of $\sigma$.

### Fourier transform and characteristic function

The [Fourier transform](https://en.wikipedia.org/wiki/Fourier_transform) of a normal density $f$ with mean $\mu$ and variance $\sigma ^{2}$ is

$$
{\hat {f}}(t)=\int _{-\infty }^{\infty }f(x)e^{-itx}\,dx=e^{-i\mu t}e^{-{\frac {1}{2}}\sigma ^{2}t^{2}}\,,
$$

where $i$ is the [imaginary unit](https://en.wikipedia.org/wiki/Imaginary_unit). If the mean $\mu =0$, the first factor is 1, and the Fourier transform is, apart from a constant factor, a normal density on the [frequency domain](https://en.wikipedia.org/wiki/Frequency_domain), with mean 0 and variance $1/\sigma ^{2}$. In particular, the standard normal distribution $\varphi$ is an [eigenfunction](https://en.wikipedia.org/wiki/Fourier_transform#Eigenfunctions) of the Fourier transform.

In probability theory, the Fourier transform of the probability distribution of a real-valued random variable $X$ is closely connected to the [characteristic function](https://en.wikipedia.org/wiki/Characteristic_function_(probability_theory) "Characteristic function (probability theory)") $\varphi _{X}(t)$ of that variable, which is defined as the [expected value](https://en.wikipedia.org/wiki/Expected_value) of $e^{itX}$, as a function of the real variable $t$ (the [frequency](https://en.wikipedia.org/wiki/Frequency) parameter of the Fourier transform). This definition can be analytically extended to a complex-value variable $t$. The relation between both is: 

$$
\varphi _{X}(t)={\hat {f}}(-t)\,.
$$

The real and imaginary parts of ${\hat {f}}(t)=\operatorname {E} [e^{-itx}]=e^{-i\mu t}e^{-{\frac {1}{2}}\sigma ^{2}t^{2}}$ give: 

$$
\operatorname {E} [\cos(tx)]=\cos(\mu t)e^{-{\frac {1}{2}}\sigma ^{2}t^{2}}
$$

 and 

$$
\operatorname {E} [\sin(tx)]=\sin(\mu t)e^{-{\frac {1}{2}}\sigma ^{2}t^{2}}.
$$

Similarly, 

$$
\operatorname {E} [\cosh(tx)]=\cosh(\mu t)e^{{\frac {1}{2}}\sigma ^{2}t^{2}}
$$

 and 

$$
\operatorname {E} [\sinh(tx)]=\sinh(\mu t)e^{{\frac {1}{2}}\sigma ^{2}t^{2}}.
$$

These formulas evaluated at $t=1$ give the expected value of these basic trigonometric and hyperbolic functions over a Gaussian random variable $X\sim N(\mu ,\sigma ^{2})$, which also could be seen as consequences of the [Isserlis's theorem](https://en.wikipedia.org/wiki/Isserlis%27s_theorem).

### Moment- and cumulant-generating functions

The [[Moment Generating Function]] of a real random variable $X$ is the expected value of $e^{tX}$, as a function of the real parameter $t$. For a normal distribution with density $f$, mean $\mu$ and variance $\sigma ^{2}$, the moment generating function exists and is equal to

$$
M(t)=\operatorname {E} \left[e^{tX}\right]={\hat {f}}(it)=e^{\mu t}e^{\sigma ^{2}t^{2}/2}\,.
$$

 For any $k$, the coefficient of $t^{k}/k!$ in the moment generating function (expressed as an [exponential power series](https://en.wikipedia.org/wiki/Generating_function#Exponential_generating_function_(EGF) "Generating function") in $t$) is the normal distribution's expected value $\operatorname {E} [X^{k}]$.

The [cumulant generating function](https://en.wikipedia.org/wiki/Cumulant_generating_function) is the logarithm of the moment generating function, namely 

$$
g(t)=\ln M(t)=\mu t+{\tfrac {1}{2}}\sigma ^{2}t^{2}\,.
$$

The coefficients of this exponential power series define the cumulants, but because this is a quadratic polynomial in $t$, only the first two [cumulants](https://en.wikipedia.org/wiki/Cumulant) are nonzero, namely the mean $\mu$ and the variance $\sigma ^{2}$.

Some authors prefer to instead work with the [characteristic function](https://en.wikipedia.org/wiki/Characteristic_function_(probability_theory) "Characteristic function (probability theory)") E\[*e*<sup>*itX*</sup>\] = *e*<sup>*iμt* − *σ*<sup>2</sup>*t*<sup>2</sup>/2</sup> and ln E\[*e*<sup>*itX*</sup>\] = *iμt* − 1/2*σ*<sup>2</sup>*t*<sup>2</sup>.

### Stein operator and class

Within [Stein's method](https://en.wikipedia.org/wiki/Stein%27s_method) the Stein operator and class of a random variable $X\sim {\mathcal {N}}(\mu ,\sigma ^{2})$ are ${\mathcal {A}}f(x)=\sigma ^{2}f'(x)-(x-\mu )f(x)$ and ${\mathcal {F}}$ the class of all absolutely continuous functions $\textstyle f:\mathbb {R} \to \mathbb {R}$ such that $\operatorname {E} [\vert f'(X)\vert ]<\infty$.

### Zero-variance limit

In the [limit](https://en.wikipedia.org/wiki/Limit_(mathematics) "Limit (mathematics)") when $\sigma ^{2}$ approaches zero, the probability density $f$ approaches zero everywhere except at $\mu$, where it approaches $\infty$, while its integral remains equal to 1. An extension of the normal distribution to the case with zero variance can be defined using the [Dirac delta measure](https://en.wikipedia.org/wiki/Dirac_measure) $\delta _{\mu }$, although the resulting random variables are not [absolutely continuous](https://en.wikipedia.org/wiki/Absolutely_continuous_random_variable) and thus do not have [[Probability Density Function|probability density functions]]. The cumulative distribution function of such a random variable is then the [Heaviside step function](https://en.wikipedia.org/wiki/Heaviside_step_function) translated by the mean $\mu$, namely 

$$
F(x)={\begin{cases}0&{\text{if }}x<\mu \\1&{\text{if }}x\geq \mu .\end{cases}}
$$

### Maximum entropy

Of all probability distributions over the reals with a specified finite mean $\mu$ and finite variance $\sigma ^{2}$, the normal distribution $N(\mu ,\sigma ^{2})$ is the one with [maximum entropy](https://en.wikipedia.org/wiki/Maximum_entropy_probability_distribution). To see this, let $X$ be a [continuous random variable](https://en.wikipedia.org/wiki/Continuous_random_variable) with [probability density](https://en.wikipedia.org/wiki/Probability_density) $f(x)$. The entropy of $X$ is defined as 

$$
H(X)=-\int _{-\infty }^{\infty }f(x)\ln f(x)\,dx\,,
$$

 where $f(x)\log f(x)$ is understood to be zero whenever $f(x)=0$. This functional can be maximized, subject to the constraints that the distribution is properly normalized and has a specified mean and variance, by using [variational calculus](https://en.wikipedia.org/wiki/Variational_calculus). A function with three [[Lagrange Multipliers]] is defined: 

$$
L=-\int _{-\infty }^{\infty }f(x)\ln f(x)\,dx-\lambda _{0}\left(1-\int _{-\infty }^{\infty }f(x)\,dx\right)-\lambda _{1}\left(\mu -\int _{-\infty }^{\infty }f(x)x\,dx\right)-\lambda _{2}\left(\sigma ^{2}-\int _{-\infty }^{\infty }f(x)(x-\mu )^{2}\,dx\right)\,.
$$

At maximum entropy, a small variation $\delta f(x)$ about $f(x)$ will produce a variation $\delta L$ about $L$ which is equal to 0: 

$$
0=\delta L=\int _{-\infty }^{\infty }\delta f(x)\left(-\ln f(x)-1+\lambda _{0}+\lambda _{1}x+\lambda _{2}(x-\mu )^{2}\right)\,dx\,.
$$

Since this must hold for any small $\delta f(x)$, the factor multiplying $\delta f(x)$ must be zero, and solving for $f(x)$ yields: 

$$
f(x)=\exp \left(-1+\lambda _{0}+\lambda _{1}x+\lambda _{2}(x-\mu )^{2}\right)\,.
$$

The Lagrange constraints that $f(x)$ is properly normalized and has the specified mean and variance are satisfied if and only if $\lambda _{0}$, $\lambda _{1}$, and $\lambda _{2}$ are chosen so that 

$$
f(x)={\frac {1}{\sqrt {2\pi \sigma ^{2}}}}e^{-{\frac {(x-\mu )^{2}}{2\sigma ^{2}}}}\,.
$$

 The entropy of a normal distribution $X\sim N(\mu ,\sigma ^{2})$ is equal to 

$$
H(X)={\tfrac {1}{2}}(1+\ln 2\sigma ^{2}\pi )\,,
$$

 which is independent of the mean $\mu$.

### Other properties

1.  If the characteristic function $\phi _{X}$ of some random variable $X$ is of the form $\phi _{X}(t)=\exp Q(t)$ in a neighborhood of zero, where $Q(t)$ is a [polynomial](https://en.wikipedia.org/wiki/Polynomial), then the **Marcinkiewicz theorem** (named after [Józef Marcinkiewicz](https://en.wikipedia.org/wiki/J%C3%B3zef_Marcinkiewicz)) asserts that $Q$ can be at most a quadratic polynomial, and therefore $X$ is a normal random variable. The consequence of this result is that the normal distribution is the only distribution with a finite number (two) of non-zero [cumulants](https://en.wikipedia.org/wiki/Cumulant).
2.  If $X$ and $Y$ are [jointly normal](https://en.wikipedia.org/wiki/Jointly_normal) and [uncorrelated](https://en.wikipedia.org/wiki/Uncorrelated), then they are [independent](https://en.wikipedia.org/wiki/Independence_(probability_theory) "Independence (probability theory)"). The requirement that $X$ and $Y$ should be *jointly* normal is essential; without it the property does not hold. For non-normal random variables uncorrelatedness does not imply independence.
3.  The [[Kullback-Leibler Divergence|Kullback–Leibler divergence]] of one normal distribution $X_{1}\sim N(\mu _{1},\sigma _{1}^{2})$ from another $X_{2}\sim N(\mu _{2},\sigma _{2}^{2})$ is given by: 

$$
D_{\mathrm {KL} }(X_{1}\parallel X_{2})={\frac {(\mu _{1}-\mu _{2})^{2}}{2\sigma _{2}^{2}}}+{\frac {1}{2}}\left({\frac {\sigma _{1}^{2}}{\sigma _{2}^{2}}}-1-\ln {\frac {\sigma _{1}^{2}}{\sigma _{2}^{2}}}\right)
$$

 The [Hellinger distance](https://en.wikipedia.org/wiki/Hellinger_distance) between the same distributions is equal to 

$$
H^{2}(X_{1},X_{2})=1-{\sqrt {\frac {2\sigma _{1}\sigma _{2}}{\sigma _{1}^{2}+\sigma _{2}^{2}}}}\exp \left(-{\frac {1}{4}}{\frac {(\mu _{1}-\mu _{2})^{2}}{\sigma _{1}^{2}+\sigma _{2}^{2}}}\right)
$$

4.  The [Fisher information matrix](https://en.wikipedia.org/wiki/Fisher_information_matrix) for a normal distribution w.r.t. $\mu$ and $\sigma ^{2}$ is diagonal and takes the form 

$$
{\mathcal {I}}(\mu ,\sigma ^{2})={\begin{pmatrix}{\frac {1}{\sigma ^{2}}}&0\\0&{\frac {1}{2\sigma ^{4}}}\end{pmatrix}}
$$

5.  The [conjugate prior](https://en.wikipedia.org/wiki/Conjugate_prior) of the mean of a normal distribution is another normal distribution. Specifically, if $x_{1},\ldots ,x_{n}$ are iid $\sim N(\mu ,\sigma ^{2})$ and the prior is $\mu \sim N(\mu _{0},\sigma _{0}^{2})$, then the posterior distribution for the estimator of $\mu$ will be 

$$
\mu \mid x_{1},\ldots ,x_{n}\sim {\mathcal {N}}\left({\frac {{\frac {\sigma ^{2}}{n}}\mu _{0}+\sigma _{0}^{2}{\bar {x}}}{{\frac {\sigma ^{2}}{n}}+\sigma _{0}^{2}}},\left({\frac {n}{\sigma ^{2}}}+{\frac {1}{\sigma _{0}^{2}}}\right)^{-1}\right)
$$

6.  The family of normal distributions not only forms an [[Exponential Family]] (EF), but in fact forms a [natural exponential family](https://en.wikipedia.org/wiki/Natural_exponential_family) (NEF) with quadratic [variance function](https://en.wikipedia.org/wiki/Variance_function) ([NEF-QVF](https://en.wikipedia.org/wiki/NEF-QVF)). Many properties of normal distributions generalize to properties of NEF-QVF distributions, NEF distributions, or EF distributions generally. NEF-QVF distributions comprises 6 families, including Poisson, Gamma, binomial, and negative binomial distributions, while many of the common families studied in probability and statistics are NEF or EF.
7.  In [information geometry](https://en.wikipedia.org/wiki/Information_geometry), the family of normal distributions forms a [statistical manifold](https://en.wikipedia.org/wiki/Statistical_manifold) with [constant curvature](https://en.wikipedia.org/wiki/Constant_curvature) $-1$. The same family is [flat](https://en.wikipedia.org/wiki/Flat_manifold) with respect to the (±1)-connections $\nabla ^{(e)}$ and $\nabla ^{(m)}$.
8.  If $X_{1},\dots ,X_{n}$ are distributed according to $N(0,\sigma ^{2})$, then $E[\max _{i}X_{i}]\leq \sigma {\sqrt {2\ln n}}$. Note that there is no assumption of independence.

## Related distributions

### Central limit theorem

![[media/a875a0772904acc980f21c038229ccc92a8eafc1.gif]]
As the number of discrete events increases, the function begins to resemble a normal distribution.

![[media/9d596e5bd5f050b8d709da54bd998e92bb8e7daf.png]]
Comparison of probability density functions, <em>p</em>(<em>k</em>) for the sum of n fair 6-sided dice to show their convergence to a normal distribution with increasing na, in accordance to the central limit theorem. In the bottom-right graph, smoothed profiles of the previous graphs are rescaled, superimposed and compared with a normal distribution (black curve).

The central limit theorem states that under certain (fairly common) conditions, the sum of many random variables will have an approximately normal distribution. More specifically, where $X_{1},\ldots ,X_{n}$ are [independent and identically distributed](https://en.wikipedia.org/wiki/Independent_and_identically_distributed) random variables with the same arbitrary distribution, zero mean, and variance $\sigma ^{2}$ and $Z$ is their mean scaled by ${\sqrt {n}}$ 

$$
Z={\sqrt {n}}\left({\frac {1}{n}}\sum _{i=1}^{n}X_{i}\right)
$$

 Then, as $n$ increases, the probability distribution of $Z$ will tend to the normal distribution with zero mean and variance $\sigma ^{2}$.

The theorem can be extended to variables $(X_{i})$ that are not independent and/or not identically distributed if certain constraints are placed on the degree of dependence and the moments of the distributions.

Many [test statistics](https://en.wikipedia.org/wiki/Test_statistic), [scores](https://en.wikipedia.org/wiki/Score_(statistics)), and [estimators](https://en.wikipedia.org/wiki/Estimator) encountered in practice contain sums of certain random variables in them, and even more estimators can be represented as sums of random variables through the use of [influence functions](https://en.wikipedia.org/wiki/Influence_function_(statistics)). The central limit theorem implies that those statistical parameters will have asymptotically normal distributions.

The central limit theorem also implies that certain distributions can be approximated by the normal distribution, for example:

- The [binomial distribution](https://en.wikipedia.org/wiki/Binomial_distribution) $B(n,p)$ is [approximately normal](https://en.wikipedia.org/wiki/De_Moivre%E2%80%93Laplace_theorem) with mean $np$ and variance $np(1-p)$ for large $n$ and for $p$ not too close to 0 or 1.
- The [Poisson distribution](https://en.wikipedia.org/wiki/Poisson_distribution) with parameter $\lambda$ is approximately normal with mean $\lambda$ and variance $\lambda$, for large values of $\lambda$.
- The [chi-squared distribution](https://en.wikipedia.org/wiki/Chi-squared_distribution) $\chi ^{2}(k)$ is approximately normal with mean $k$ and variance $2k$, for large $k$.
- The [Student's t-distribution](https://en.wikipedia.org/wiki/Student%27s_t-distribution) $t(\nu )$ is approximately normal with mean 0 and variance 1 when $\nu$ is large.

Whether these approximations are sufficiently accurate depends on the purpose for which they are needed, and the rate of convergence to the normal distribution. It is typically the case that such approximations are less accurate in the tails of the distribution.

A general upper bound for the approximation error in the central limit theorem is given by the [Berry–Esseen theorem](https://en.wikipedia.org/wiki/Berry%E2%80%93Esseen_theorem), improvements of the approximation are given by the [Edgeworth expansions](https://en.wikipedia.org/wiki/Edgeworth_expansion).

This theorem can also be used to justify modeling the sum of many uniform noise sources as [Gaussian noise](https://en.wikipedia.org/wiki/Gaussian_noise). See [AWGN](https://en.wikipedia.org/wiki/AWGN).

### Operations and functions of normal variables

#### Operations on a single normal variable

If $X$ is distributed normally with mean $\mu$ and variance $\sigma ^{2}$, then

- $aX+b$, for any real numbers $a$ and $b$, is also normally distributed, with mean $a\mu +b$ and variance $a^{2}\sigma ^{2}$. That is, the family of normal distributions is closed under [linear transformations](https://en.wikipedia.org/wiki/Linear_transformations).
- The exponential of $X$ is distributed [log-normally](https://en.wikipedia.org/wiki/Log-normal_distribution): $e^{X}\sim \ln(N(\mu ,\sigma ^{2}))$.
- The standard [sigmoid](https://en.wikipedia.org/wiki/Logistic_function) of $X$ is [logit-normally distributed](https://en.wikipedia.org/wiki/Logit-normal_distribution): $\sigma (X)\sim P({\mathcal {N}}(\mu ,\,\sigma ^{2}))$.
- The absolute value of $X$ has [folded normal distribution](https://en.wikipedia.org/wiki/Folded_normal_distribution): ${\left|X\right|\sim N_{f}(\mu ,\sigma ^{2})}$. If $\mu =0$ this is known as the [half-normal distribution](https://en.wikipedia.org/wiki/Half-normal_distribution).
- The absolute value of normalized residuals, $|X-\mu |/\sigma$, has [chi distribution](https://en.wikipedia.org/wiki/Chi_distribution) with one degree of freedom: $|X-\mu |/\sigma \sim \chi _{1}$.
- The square of $X/\sigma$ has the [noncentral chi-squared distribution](https://en.wikipedia.org/wiki/Noncentral_chi-squared_distribution) with one degree of freedom: $X^{2}/\sigma ^{2}\sim \chi _{1}^{2}(\mu ^{2}/\sigma ^{2})$. If $\mu =0$, the distribution is called simply [chi-squared](https://en.wikipedia.org/wiki/Chi-squared_distribution).
- The log-likelihood of a normal variable $x$ is simply the log of its [[Probability Density Function]]: 

$$
\ln p(x)=-{\frac {1}{2}}\left({\frac {x-\mu }{\sigma }}\right)^{2}-\ln \left(\sigma {\sqrt {2\pi }}\right).
$$

 Since this is a scaled and shifted square of a standard normal variable, it is distributed as a scaled and shifted [chi-squared](https://en.wikipedia.org/wiki/Chi-squared_distribution) variable.
- The distribution of the variable $X$ restricted to an interval $[a,b]$ is called the [truncated normal distribution](https://en.wikipedia.org/wiki/Truncated_normal_distribution).
- $(X-\mu )^{-2}$ has a [Lévy distribution](https://en.wikipedia.org/wiki/L%C3%A9vy_distribution) with location 0 and scale $\sigma ^{-2}$.

##### Operations on two independent normal variables

- If $X_{1}$ and $X_{2}$ are two [independent](https://en.wikipedia.org/wiki/Independence_(probability_theory) "Independence (probability theory)") normal random variables, with means $\mu _{1}$, $\mu _{2}$ and variances $\sigma _{1}^{2}$, $\sigma _{2}^{2}$, then their sum $X_{1}+X_{2}$ will also be normally distributed,<sup>[\[proof\]](https://en.wikipedia.org/wiki/Sum_of_normally_distributed_random_variables "Sum of normally distributed random variables")</sup> with mean $\mu _{1}+\mu _{2}$ and variance $\sigma _{1}^{2}+\sigma _{2}^{2}$.
- In particular, if $X$ and $Y$ are independent normal deviates with zero mean and variance $\sigma ^{2}$, then $X+Y$ and $X-Y$ are also independent and normally distributed, with zero mean and variance $2\sigma ^{2}$. This is a special case of the [polarization identity](https://en.wikipedia.org/wiki/Polarization_identity).
- If $X_{1}$, $X_{2}$ are two independent normal deviates with mean $\mu$ and variance $\sigma ^{2}$, and $a$, $b$ are arbitrary real numbers, then the variable 

$$
X_{3}={\frac {aX_{1}+bX_{2}-(a+b)\mu }{\sqrt {a^{2}+b^{2}}}}+\mu
$$

 is also normally distributed with mean $\mu$ and variance $\sigma ^{2}$. It follows that the normal distribution is [stable](https://en.wikipedia.org/wiki/Stable_distribution) (with exponent $\alpha =2$).
- If $X_{k}\sim {\mathcal {N}}(m_{k},\sigma _{k}^{2})$, $k\in \{0,1\}$ are normal distributions, then their normalized [geometric mean](https://en.wikipedia.org/wiki/Geometric_mean) ${\frac {1}{\int _{\mathbb {R} ^{n}}X_{0}^{\alpha }(x)X_{1}^{1-\alpha }(x)\,{\text{d}}x}}X_{0}^{\alpha }X_{1}^{1-\alpha }$ is a normal distribution ${\mathcal {N}}(m_{\alpha },\sigma _{\alpha }^{2})$ with $m_{\alpha }={\frac {\alpha m_{0}\sigma _{1}^{2}+(1-\alpha )m_{1}\sigma _{0}^{2}}{\alpha \sigma _{1}^{2}+(1-\alpha )\sigma _{0}^{2}}}$ and $\sigma _{\alpha }^{2}={\frac {\sigma _{0}^{2}\sigma _{1}^{2}}{\alpha \sigma _{1}^{2}+(1-\alpha )\sigma _{0}^{2}}}$.

##### Operations on two independent standard normal variables

If $X_{1}$ and $X_{2}$ are two independent standard normal random variables with mean 0 and variance 1, then

- Their sum and difference is distributed normally with mean zero and variance two: $X_{1}\pm X_{2}\sim {\mathcal {N}}(0,2)$.
- Their product $Z=X_{1}X_{2}$ follows the [product distribution](https://en.wikipedia.org/wiki/Product_distribution#Independent_central-normal_distributions) with density function $f_{Z}(z)=\pi ^{-1}K_{0}(|z|)$ where $K_{0}$ is the [modified Bessel function of the second kind](https://en.wikipedia.org/wiki/Macdonald_function). This distribution is symmetric around zero, unbounded at $z=0$, and has the [characteristic function](https://en.wikipedia.org/wiki/Characteristic_function_(probability_theory) "Characteristic function (probability theory)") $\phi _{Z}(t)=(1+t^{2})^{-1/2}$.
- Their ratio follows the standard [Cauchy distribution](https://en.wikipedia.org/wiki/Cauchy_distribution): $X_{1}/X_{2}\sim \operatorname {Cauchy} (0,1)$.
- Their Euclidean norm ${\sqrt {X_{1}^{2}+X_{2}^{2}}}$ has the [Rayleigh distribution](https://en.wikipedia.org/wiki/Rayleigh_distribution).

#### Operations on multiple independent normal variables

- Any [linear combination](https://en.wikipedia.org/wiki/Linear_combination) of independent normal deviates is a normal deviate.
- If $X_{1},X_{2},\ldots ,X_{n}$ are independent standard normal random variables, then the sum of their squares has the [chi-squared distribution](https://en.wikipedia.org/wiki/Chi-squared_distribution) with $n$ degrees of freedom 

$$
X_{1}^{2}+\cdots +X_{n}^{2}\sim \chi _{n}^{2}.
$$

- If $X_{1},X_{2},\ldots ,X_{n}$ are independent normally distributed random variables with means $\mu$ and variances $\sigma ^{2}$, then their [sample mean](https://en.wikipedia.org/wiki/Sample_mean) is independent from the sample [standard deviation](https://en.wikipedia.org/wiki/Standard_deviation), which can be demonstrated using [Basu's theorem](https://en.wikipedia.org/wiki/Basu%27s_theorem) or [Cochran's theorem](https://en.wikipedia.org/wiki/Cochran%27s_theorem). The ratio of these two quantities will have the [Student's t-distribution](https://en.wikipedia.org/wiki/Student%27s_t-distribution) with $n-1$ degrees of freedom: 

$$
t={\frac {{\overline {X}}-\mu }{S/{\sqrt {n}}}}={\frac {{\frac {1}{n}}(X_{1}+\cdots +X_{n})-\mu }{\sqrt {{\frac {1}{n(n-1)}}\left[(X_{1}-{\overline {X}})^{2}+\cdots +(X_{n}-{\overline {X}})^{2}\right]}}}\sim t_{n-1}.
$$

- If $X_{1},X_{2},\ldots ,X_{n}$, $Y_{1},Y_{2},\ldots ,Y_{m}$ are independent standard normal random variables, then the ratio of their normalized sums of squares will have the [F-distribution](https://en.wikipedia.org/wiki/F-distribution) with (*n*, *m*) degrees of freedom: 

$$
F={\frac {\left(X_{1}^{2}+X_{2}^{2}+\cdots +X_{n}^{2}\right)/n}{\left(Y_{1}^{2}+Y_{2}^{2}+\cdots +Y_{m}^{2}\right)/m}}\sim F_{n,m}.
$$

#### Operations on multiple correlated normal variables

- A [quadratic form](https://en.wikipedia.org/wiki/Quadratic_form) of a normal vector, i.e. a quadratic function $q=\sum x_{i}^{2}+\sum x_{j}+c$ of multiple independent or correlated normal variables, is a [generalized chi-square](https://en.wikipedia.org/wiki/Generalized_chi-square_distribution) variable.

### Operations on the density function

The [split normal distribution](https://en.wikipedia.org/wiki/Split_normal_distribution) is most directly defined in terms of joining scaled sections of the density functions of different normal distributions and rescaling the density to integrate to one. The [truncated normal distribution](https://en.wikipedia.org/wiki/Truncated_normal_distribution) results from rescaling a section of a single density function.

### Infinite divisibility and Cramér's theorem

For any positive integer n, any normal distribution with mean $\mu$ and variance $\sigma ^{2}$ is the distribution of the sum of n independent normal deviates, each with mean ${\frac {\mu }{n}}$ and variance ${\frac {\sigma ^{2}}{n}}$. This property is called [infinite divisibility](https://en.wikipedia.org/wiki/Infinite_divisibility_(probability) "Infinite divisibility (probability)").

Conversely, if $X_{1}$ and $X_{2}$ are independent random variables and their sum $X_{1}+X_{2}$ has a normal distribution, then both $X_{1}$ and $X_{2}$ must be normal deviates.

This result is known as [Cramér's decomposition theorem](https://en.wikipedia.org/wiki/Cram%C3%A9r%27s_decomposition_theorem), and is equivalent to saying that the [convolution](https://en.wikipedia.org/wiki/Convolution) of two distributions is normal if and only if both are normal. Cramér's theorem implies that a linear combination of independent non-Gaussian variables will never have an exactly normal distribution, although it may approach it arbitrarily closely.

### The Kac–Bernstein theorem

The [Kac–Bernstein theorem](https://en.wikipedia.org/wiki/Kac%E2%80%93Bernstein_theorem) states that if $X$ and $Y$ are independent and $X+Y$ and $X-Y$ are also independent, then both X and Y must necessarily have normal distributions.

More generally, if $X_{1},\ldots ,X_{n}$ are independent random variables, then two distinct linear combinations $\sum {a_{k}X_{k}}$ and $\sum {b_{k}X_{k}}$will be independent if and only if all $X_{k}$ are normal and $\sum {a_{k}b_{k}\sigma _{k}^{2}=0}$, where $\sigma _{k}^{2}$ denotes the variance of $X_{k}$.

### Extensions

The notion of normal distribution, being one of the most important distributions in probability theory, has been extended far beyond the standard framework of the univariate (that is one-dimensional) case (Case 1). All these extensions are also called *normal* or *Gaussian* laws, so a certain ambiguity in names exists.

- The [[Multivariate Normal Distribution]] describes the Gaussian law in the k-dimensional [Euclidean space](https://en.wikipedia.org/wiki/Euclidean_space). A vector *X* ∈ **R**<sup>*k*</sup> is multivariate-normally distributed if any linear combination of its components Σ<sup>*k*</sup>  
  <sub>*j*=1</sub>*a*<sub>*j*</sub> *X*<sub>*j*</sub> has a (univariate) normal distribution. The variance of X is a *k* × *k* symmetric positive-definite matrix V. The multivariate normal distribution is a special case of the [elliptical distributions](https://en.wikipedia.org/wiki/Elliptical_distribution). As such, its iso-density loci in the *k* = 2 case are [ellipses](https://en.wikipedia.org/wiki/Ellipse) and in the case of arbitrary k are [ellipsoids](https://en.wikipedia.org/wiki/Ellipsoid).
- [Rectified Gaussian distribution](https://en.wikipedia.org/wiki/Rectified_Gaussian_distribution) a rectified version of normal distribution with all the negative elements reset to 0.
- [Complex normal distribution](https://en.wikipedia.org/wiki/Complex_normal_distribution) deals with the complex normal vectors. A complex vector *X* ∈ **C**<sup>*k*</sup> is said to be normal if both its real and imaginary components jointly possess a 2*k*-dimensional multivariate normal distribution. The variance-covariance structure of X is described by two matrices: the *variance* matrix Γ, and the *relation* matrix C.
- [Matrix normal distribution](https://en.wikipedia.org/wiki/Matrix_normal_distribution) describes the case of normally distributed matrices.
- [Gaussian processes](https://en.wikipedia.org/wiki/Gaussian_process) are the normally distributed [stochastic processes](https://en.wikipedia.org/wiki/Stochastic_process). These can be viewed as elements of some infinite-dimensional [Hilbert space](https://en.wikipedia.org/wiki/Hilbert_space) H, and thus are the analogues of multivariate normal vectors for the case *k* = ∞. A random element *h* ∈ *H* is said to be normal if for any constant *a* ∈ *H* the [scalar product](https://en.wikipedia.org/wiki/Scalar_product) (*a*, *h*) has a (univariate) normal distribution. The variance structure of such Gaussian random element can be described in terms of the linear *covariance operator* *K*: *H* → *H*. Several Gaussian processes became popular enough to have their own names:
  - [Brownian motion](https://en.wikipedia.org/wiki/Wiener_process);
  - [Brownian bridge](https://en.wikipedia.org/wiki/Brownian_bridge); and
  - [Ornstein–Uhlenbeck process](https://en.wikipedia.org/wiki/Ornstein%E2%80%93Uhlenbeck_process).
- [Gaussian q-distribution](https://en.wikipedia.org/wiki/Gaussian_q-distribution) is an abstract mathematical construction that represents a [q-analogue](https://en.wikipedia.org/wiki/Q-analogue) of the normal distribution.
- the [q-Gaussian](https://en.wikipedia.org/wiki/Q-Gaussian) is an analogue of the Gaussian distribution, in the sense that it maximises the [Tsallis entropy](https://en.wikipedia.org/wiki/Tsallis_entropy), and is one type of [Tsallis distribution](https://en.wikipedia.org/wiki/Tsallis_distribution). This distribution is different from the [Gaussian q-distribution](https://en.wikipedia.org/wiki/Gaussian_q-distribution) above.
- The [Kaniadakis κ-Gaussian distribution](https://en.wikipedia.org/wiki/Kaniadakis_Gaussian_distribution) is a generalization of the Gaussian distribution which arises from the [Kaniadakis statistics](https://en.wikipedia.org/wiki/Kaniadakis_statistics), being one of the [Kaniadakis distributions](https://en.wikipedia.org/wiki/Kaniadakis_distribution).

A random variable X has a two-piece normal distribution if it has a distribution 

$$
f_{X}(x)={\begin{cases}N(\mu ,\sigma _{1}^{2}),&{\text{ if }}x\leq \mu \\N(\mu ,\sigma _{2}^{2}),&{\text{ if }}x\geq \mu \end{cases}}
$$

 where μ is the mean and *σ*2  
1  and *σ*2  
2  are the variances of the distribution to the left and right of the mean respectively.

The mean E(*X*), variance V(*X*), and third central moment T(*X*) of this distribution have been determined 

$$
{\begin{aligned}\operatorname {E} (X)&=\mu +{\sqrt {\frac {2}{\pi }}}(\sigma _{2}-\sigma _{1}),\\\operatorname {V} (X)&=\left(1-{\frac {2}{\pi }}\right)(\sigma _{2}-\sigma _{1})^{2}+\sigma _{1}\sigma _{2},\\\operatorname {T} (X)&={\sqrt {\frac {2}{\pi }}}(\sigma _{2}-\sigma _{1})\left[\left({\frac {4}{\pi }}-1\right)(\sigma _{2}-\sigma _{1})^{2}+\sigma _{1}\sigma _{2}\right].\end{aligned}}
$$

One of the main practical uses of the Gaussian law is to model the empirical distributions of many different random variables encountered in practice. In such case a possible extension would be a richer family of distributions, having more than two parameters and therefore being able to fit the empirical distribution more accurately. The examples of such extensions are:

- [Pearson distribution](https://en.wikipedia.org/wiki/Pearson_distribution) — a four-parameter family of probability distributions that extend the normal law to include different skewness and kurtosis values.
- The [generalized normal distribution](https://en.wikipedia.org/wiki/Generalized_normal_distribution), also known as the exponential power distribution, allows for distribution tails with thicker or thinner asymptotic behaviors.

## Statistical inference

### Estimation of parameters

It is often the case that we do not know the parameters of the normal distribution, but instead want to [estimate](https://en.wikipedia.org/wiki/Estimation_theory) them. That is, having a sample $(x_{1},\ldots ,x_{n})$ from a normal ${\mathcal {N}}(\mu ,\sigma ^{2})$ population we would like to learn the approximate values of parameters $\mu$ and $\sigma ^{2}$. The standard approach to this problem is the [maximum likelihood](https://en.wikipedia.org/wiki/Maximum_likelihood) method, which requires maximization of the *[log-likelihood function](https://en.wikipedia.org/wiki/Log-likelihood_function)*: 

$$
\ln {\mathcal {L}}(\mu ,\sigma ^{2})=\sum _{i=1}^{n}\ln f(x_{i}\mid \mu ,\sigma ^{2})=-{\frac {n}{2}}\ln(2\pi )-{\frac {n}{2}}\ln \sigma ^{2}-{\frac {1}{2\sigma ^{2}}}\sum _{i=1}^{n}(x_{i}-\mu )^{2}.
$$

 Taking derivatives with respect to $\mu$ and $\sigma ^{2}$ and solving the resulting system of first order conditions yields the *maximum likelihood estimates*: 

$$
{\hat {\mu }}={\overline {x}}\equiv {\frac {1}{n}}\sum _{i=1}^{n}x_{i},\qquad {\hat {\sigma }}^{2}={\frac {1}{n}}\sum _{i=1}^{n}(x_{i}-{\overline {x}})^{2}.
$$

Then $\ln {\mathcal {L}}({\hat {\mu }},{\hat {\sigma }}^{2})$ is as follows: 

$$
\ln {\mathcal {L}}({\hat {\mu }},{\hat {\sigma }}^{2})=(-n/2)[\ln(2\pi {\hat {\sigma }}^{2})+1]
$$

#### Sample mean

Estimator $\textstyle {\hat {\mu }}$ is called the *[sample mean](https://en.wikipedia.org/wiki/Sample_mean)*, since it is the arithmetic mean of all observations. The statistic $\textstyle {\overline {x}}$ is [complete](https://en.wikipedia.org/wiki/Complete_statistic) and [sufficient](https://en.wikipedia.org/wiki/Sufficient_statistic) for $\mu$, and therefore by the [Lehmann–Scheffé theorem](https://en.wikipedia.org/wiki/Lehmann%E2%80%93Scheff%C3%A9_theorem), $\textstyle {\hat {\mu }}$ is the [uniformly minimum variance unbiased](https://en.wikipedia.org/wiki/Uniformly_minimum_variance_unbiased) (UMVU) estimator. In finite samples it is distributed normally: 

$$
{\hat {\mu }}\sim {\mathcal {N}}(\mu ,\sigma ^{2}/n).
$$

 The variance of this estimator is equal to the *μμ*-element of the inverse [Fisher information matrix](https://en.wikipedia.org/wiki/Fisher_information_matrix) $\textstyle {\mathcal {I}}^{-1}$. This implies that the estimator is [finite-sample efficient](https://en.wikipedia.org/wiki/Efficient_estimator). Of practical importance is the [standard error](https://en.wikipedia.org/wiki/Standard_error) of $\textstyle {\hat {\mu }}$ being proportional to $\textstyle 1/{\sqrt {n}}$, that is, if one wishes to decrease the standard error by a factor of 10, one must increase the number of points in the sample by a factor of 100. This fact is widely used in determining sample sizes for opinion polls and the number of trials in [Monte Carlo simulations](https://en.wikipedia.org/wiki/Monte_Carlo_simulation).

From the standpoint of the [asymptotic theory](https://en.wikipedia.org/wiki/Asymptotic_theory_(statistics) "Asymptotic theory (statistics)"), $\textstyle {\hat {\mu }}$ is [consistent](https://en.wikipedia.org/wiki/Consistent_estimator), that is, it [converges in probability](https://en.wikipedia.org/wiki/Converges_in_probability) to $\mu$ as $n\rightarrow \infty$. The estimator is also [asymptotically normal](https://en.wikipedia.org/wiki/Asymptotic_normality), which is a simple corollary of it being normal in finite samples: 

$$
{\sqrt {n}}({\hat {\mu }}-\mu )\,\xrightarrow {d} \,{\mathcal {N}}(0,\sigma ^{2}).
$$

#### Sample variance

The estimator $\textstyle {\hat {\sigma }}^{2}$ is called the *[sample variance](https://en.wikipedia.org/wiki/Sample_variance)*, since it is the variance of the sample ($(x_{1},\ldots ,x_{n})$). In practice, another estimator is often used instead of the $\textstyle {\hat {\sigma }}^{2}$. This other estimator is denoted $s^{2}$, and is also called the *sample variance*, which represents a certain ambiguity in terminology; its square root $s$ is called the *sample standard deviation*. The estimator $s^{2}$ differs from $\textstyle {\hat {\sigma }}^{2}$ by having (*n* − 1) instead of n in the denominator (the so-called [Bessel's correction](https://en.wikipedia.org/wiki/Bessel%27s_correction)): 

$$
s^{2}={\frac {n}{n-1}}{\hat {\sigma }}^{2}={\frac {1}{n-1}}\sum _{i=1}^{n}(x_{i}-{\overline {x}})^{2}.
$$

 The difference between $s^{2}$ and $\textstyle {\hat {\sigma }}^{2}$ becomes negligibly small for large n's. In finite samples however, the motivation behind the use of $s^{2}$ is that it is an [unbiased estimator](https://en.wikipedia.org/wiki/Unbiased_estimator) of the underlying parameter $\sigma ^{2}$, whereas $\textstyle {\hat {\sigma }}^{2}$ is biased. Also, by the Lehmann–Scheffé theorem the estimator $s^{2}$ is uniformly minimum variance unbiased ([UMVU](https://en.wikipedia.org/wiki/UMVU)), which makes it the "best" estimator among all unbiased ones. However it can be shown that the biased estimator $\textstyle {\hat {\sigma }}^{2}$ is better than the $s^{2}$ in terms of the [mean squared error](https://en.wikipedia.org/wiki/Mean_squared_error) (MSE) criterion. In finite samples both $s^{2}$ and $\textstyle {\hat {\sigma }}^{2}$ have scaled [chi-squared distribution](https://en.wikipedia.org/wiki/Chi-squared_distribution) with (*n* − 1) degrees of freedom: 

$$
s^{2}\sim {\frac {\sigma ^{2}}{n-1}}\cdot \chi _{n-1}^{2},\qquad {\hat {\sigma }}^{2}\sim {\frac {\sigma ^{2}}{n}}\cdot \chi _{n-1}^{2}.
$$

 The first of these expressions shows that the variance of $s^{2}$ is equal to $2\sigma ^{4}/(n-1)$, which is slightly greater than the *σσ*-element of the inverse Fisher information matrix $\textstyle {\mathcal {I}}^{-1}$, which is $2\sigma ^{4}/n$. Thus, $s^{2}$ is not an efficient estimator for $\sigma ^{2}$, and moreover, since $s^{2}$ is UMVU, we can conclude that the finite-sample efficient estimator for $\sigma ^{2}$ does not exist.

Applying the asymptotic theory, both estimators $s^{2}$ and $\textstyle {\hat {\sigma }}^{2}$ are consistent, that is they converge in probability to $\sigma ^{2}$ as the sample size $n\rightarrow \infty$. The two estimators are also both asymptotically normal: 

$$
{\sqrt {n}}({\hat {\sigma }}^{2}-\sigma ^{2})\simeq {\sqrt {n}}(s^{2}-\sigma ^{2})\,\xrightarrow {d} \,{\mathcal {N}}(0,2\sigma ^{4}).
$$

 In particular, both estimators are asymptotically efficient for $\sigma ^{2}$.

### Confidence intervals

By [Cochran's theorem](https://en.wikipedia.org/wiki/Cochran%27s_theorem), for normal distributions the sample mean $\textstyle {\hat {\mu }}$ and the sample variance *s*<sup>2</sup> are [independent](https://en.wikipedia.org/wiki/Independence_(probability_theory) "Independence (probability theory)"), which means there can be no gain in considering their [joint distribution](https://en.wikipedia.org/wiki/Joint_distribution). There is also a converse theorem: if in a sample the sample mean and sample variance are independent, then the sample must have come from the normal distribution. The independence between $\textstyle {\hat {\mu }}$ and s can be employed to construct the so-called *t-statistic*: 

$$
t={\frac {{\hat {\mu }}-\mu }{s/{\sqrt {n}}}}={\frac {{\overline {x}}-\mu }{\sqrt {{\frac {1}{n(n-1)}}\sum (x_{i}-{\overline {x}})^{2}}}}\sim t_{n-1}
$$

 This quantity t has the [Student's t-distribution](https://en.wikipedia.org/wiki/Student%27s_t-distribution) with (*n* − 1) degrees of freedom, and it is an [ancillary statistic](https://en.wikipedia.org/wiki/Ancillary_statistic) (independent of the value of the parameters). Inverting the distribution of this t-statistics will allow us to construct the [confidence interval](https://en.wikipedia.org/wiki/Confidence_interval) for μ; similarly, inverting the *χ*<sup>2</sup> distribution of the statistic *s*<sup>2</sup> will give us the confidence interval for *σ*<sup>2</sup>: 

$$
\mu \in \left[{\hat {\mu }}-t_{n-1,1-\alpha /2}{\frac {s}{\sqrt {n}}},\,{\hat {\mu }}+t_{n-1,1-\alpha /2}{\frac {s}{\sqrt {n}}}\right]
$$

$$
\sigma ^{2}\in \left[{\frac {n-1}{\chi _{n-1,1-\alpha /2}^{2}}}s^{2},\,{\frac {n-1}{\chi _{n-1,\alpha /2}^{2}}}s^{2}\right]
$$

 where *t*<sub>*k*,*p*</sub> and χ 2  
*k,p*  are the pth [quantiles](https://en.wikipedia.org/wiki/Quantile) of the t- and *χ*<sup>2</sup>-distributions respectively. These confidence intervals are of the *[confidence level](https://en.wikipedia.org/wiki/Confidence_level)* 1 − *α*, meaning that the true values μ and *σ*<sup>2</sup> fall outside of these intervals with probability (or [significance level](https://en.wikipedia.org/wiki/Significance_level)) α. In practice people usually take *α* = 5%, resulting in the 95% confidence intervals. The confidence interval for σ can be found by taking the square root of the interval bounds for *σ*<sup>2</sup>.

Approximate formulas can be derived from the asymptotic distributions of $\textstyle {\hat {\mu }}$ and *s*<sup>2</sup>: 

$$
\mu \in \left[{\hat {\mu }}-{\frac {|z_{\alpha /2}|}{\sqrt {n}}}s,\,{\hat {\mu }}+{\frac {|z_{\alpha /2}|}{\sqrt {n}}}s\right]
$$

$$
\sigma ^{2}\in \left[s^{2}-{\sqrt {2}}{\frac {|z_{\alpha /2}|}{\sqrt {n}}}s^{2},\,s^{2}+{\sqrt {2}}{\frac {|z_{\alpha /2}|}{\sqrt {n}}}s^{2}\right]
$$

 The approximate formulas become valid for large values of n, and are more convenient for the manual calculation since the standard normal quantiles *z*<sub>*α*/2</sub> do not depend on n. In particular, the most popular value of *α* = 5%, results in \|*z*<sub>0.025</sub>\| = [1.96](https://en.wikipedia.org/wiki/1.96).

### Normality tests

Normality tests assess the likelihood that the given data set {*x*<sub>1</sub>, ..., *x*<sub>*n*</sub>} comes from a normal distribution. Typically the [null hypothesis](https://en.wikipedia.org/wiki/Null_hypothesis) *H*<sub>0</sub> is that the observations are distributed normally with unspecified mean μ and variance *σ*<sup>2</sup>, versus the alternative *H*<sub>*a*</sub> that the distribution is arbitrary. Many tests (over 40) have been devised for this problem. The more prominent of them are outlined below:

**Diagnostic plots** are more intuitively appealing but subjective at the same time, as they rely on informal human judgement to accept or reject the null hypothesis.

- [Q–Q plot](https://en.wikipedia.org/wiki/Q%E2%80%93Q_plot), also known as [normal probability plot](https://en.wikipedia.org/wiki/Normal_probability_plot) or [rankit](https://en.wikipedia.org/wiki/Rankit) plot—is a plot of the sorted values from the data set against the expected values of the corresponding quantiles from the standard normal distribution. That is, it is a plot of point of the form (*Φ*<sup>−1</sup>(*p*<sub>*k*</sub>), *x*<sub>(*k*)</sub>), where plotting points *p*<sub>*k*</sub> are equal to *p*<sub>*k*</sub> = (*k* − *α*)/(*n* + 1 − 2*α*) and α is an adjustment constant, which can be anything between 0 and 1. If the null hypothesis is true, the plotted points should approximately lie on a straight line.
- [P–P plot](https://en.wikipedia.org/wiki/P%E2%80%93P_plot) – similar to the Q–Q plot, but used much less frequently. This method consists of plotting the points (*Φ*(*z*<sub>(*k*)</sub>), *p*<sub>*k*</sub>), where $\textstyle z_{(k)}=(x_{(k)}-{\hat {\mu }})/{\hat {\sigma }}$. For normally distributed data this plot should lie on a straight line between (0, 0) and (1, 1).

**Goodness-of-fit tests**:

*Moment-based tests*:

- [D'Agostino's K-squared test](https://en.wikipedia.org/wiki/D%27Agostino%27s_K-squared_test)
- [Jarque–Bera test](https://en.wikipedia.org/wiki/Jarque%E2%80%93Bera_test)
- [Shapiro–Wilk test](https://en.wikipedia.org/wiki/Shapiro%E2%80%93Wilk_test): This is based on the line in the Q–Q plot having the slope of σ. The test compares the least squares estimate of that slope with the value of the sample variance, and rejects the null hypothesis if these two quantities differ significantly.

*Tests based on the empirical distribution function*:

- [Anderson–Darling test](https://en.wikipedia.org/wiki/Anderson%E2%80%93Darling_test)
- [Lilliefors test](https://en.wikipedia.org/wiki/Lilliefors_test) (an adaptation of the [Kolmogorov–Smirnov test](https://en.wikipedia.org/wiki/Kolmogorov%E2%80%93Smirnov_test))

### Bayesian analysis of the normal distribution

Bayesian analysis of normally distributed data is complicated by the many different possibilities that may be considered:

- Either the mean, or the variance, or neither, may be considered a fixed quantity.
- When the variance is unknown, analysis may be done directly in terms of the variance, or in terms of the [precision](https://en.wikipedia.org/wiki/Precision_(statistics) "Precision (statistics)"), the reciprocal of the variance. The reason for expressing the formulas in terms of precision is that the analysis of most cases is simplified.
- Both univariate and [[Multivariate Normal Distribution|multivariate]] cases need to be considered.
- Either [conjugate](https://en.wikipedia.org/wiki/Conjugate_prior) or [improper](https://en.wikipedia.org/wiki/Improper_prior) [prior distributions](https://en.wikipedia.org/wiki/Prior_distribution) may be placed on the unknown variables.
- An additional set of cases occurs in [Bayesian linear regression](https://en.wikipedia.org/wiki/Bayesian_linear_regression), where in the basic model the data is assumed to be normally distributed, and normal priors are placed on the [regression coefficients](https://en.wikipedia.org/wiki/Regression_coefficient). The resulting analysis is similar to the basic cases of [independent identically distributed](https://en.wikipedia.org/wiki/Independent_identically_distributed) data.

The formulas for the non-linear-regression cases are summarized in the [conjugate prior](https://en.wikipedia.org/wiki/Conjugate_prior) article.

#### Sum of two quadratics

##### Scalar form

The following auxiliary formula is useful for simplifying the [posterior](https://en.wikipedia.org/wiki/Posterior_distribution) update equations, which otherwise become fairly tedious.

$$
a(x-y)^{2}+b(x-z)^{2}=(a+b)\left(x-{\frac {ay+bz}{a+b}}\right)^{2}+{\frac {ab}{a+b}}(y-z)^{2}
$$

This equation rewrites the sum of two quadratics in x by expanding the squares, grouping the terms in x, and [completing the square](https://en.wikipedia.org/wiki/Completing_the_square). Note the following about the complex constant factors attached to some of the terms:

1.  The factor ${\frac {ay+bz}{a+b}}$ has the form of a [weighted average](https://en.wikipedia.org/wiki/Weighted_average) of y and z.
2.  ${\frac {ab}{a+b}}={\frac {1}{{\frac {1}{a}}+{\frac {1}{b}}}}=(a^{-1}+b^{-1})^{-1}.$ This shows that this factor can be thought of as resulting from a situation where the [reciprocals](https://en.wikipedia.org/wiki/Multiplicative_inverse) of quantities a and b add directly, so to combine a and b themselves, it is necessary to reciprocate, add, and reciprocate the result again to get back into the original units. This is exactly the sort of operation performed by the [harmonic mean](https://en.wikipedia.org/wiki/Harmonic_mean), so it is not surprising that ${\frac {ab}{a+b}}$ is one-half the [harmonic mean](https://en.wikipedia.org/wiki/Harmonic_mean) of a and b.

##### Vector form

A similar formula can be written for the sum of two vector quadratics: If **x**, **y**, **z** are vectors of length k, and **A** and **B** are [symmetric](https://en.wikipedia.org/wiki/Symmetric_matrix), [invertible matrices](https://en.wikipedia.org/wiki/Invertible_matrices) of size $k\times k$, then

$$
{\begin{aligned}&(\mathbf {y} -\mathbf {x} )'\mathbf {A} (\mathbf {y} -\mathbf {x} )+(\mathbf {x} -\mathbf {z} )'\mathbf {B} (\mathbf {x} -\mathbf {z} )\\={}&(\mathbf {x} -\mathbf {c} )'(\mathbf {A} +\mathbf {B} )(\mathbf {x} -\mathbf {c} )+(\mathbf {y} -\mathbf {z} )'(\mathbf {A} ^{-1}+\mathbf {B} ^{-1})^{-1}(\mathbf {y} -\mathbf {z} )\end{aligned}}
$$

 where 

$$
\mathbf {c} =(\mathbf {A} +\mathbf {B} )^{-1}(\mathbf {A} \mathbf {y} +\mathbf {B} \mathbf {z} )
$$

The form **x**′ **A** **x** is called a [quadratic form](https://en.wikipedia.org/wiki/Quadratic_form) and is a [scalar](https://en.wikipedia.org/wiki/Scalar_(mathematics) "Scalar (mathematics)"): 

$$
\mathbf {x} '\mathbf {A} \mathbf {x} =\sum _{i,j}a_{ij}x_{i}x_{j}
$$

 In other words, it sums up all possible combinations of products of pairs of elements from **x**, with a separate coefficient for each. In addition, since $x_{i}x_{j}=x_{j}x_{i}$, only the sum $a_{ij}+a_{ji}$ matters for any off-diagonal elements of **A**, and there is no loss of generality in assuming that **A** is [symmetric](https://en.wikipedia.org/wiki/Symmetric_matrix). Furthermore, if **A** is symmetric, then the form $\mathbf {x} '\mathbf {A} \mathbf {y} =\mathbf {y} '\mathbf {A} \mathbf {x} .$

#### Sum of differences from the mean

Another useful formula is as follows: 

$$
\sum _{i=1}^{n}(x_{i}-\mu )^{2}=\sum _{i=1}^{n}(x_{i}-{\bar {x}})^{2}+n({\bar {x}}-\mu )^{2}
$$

 where ${\bar {x}}={\frac {1}{n}}\sum _{i=1}^{n}x_{i}.$

### With known variance

For a set of [i.i.d.](https://en.wikipedia.org/wiki/I.i.d.) normally distributed data points **X** of size n where each individual point x follows $x\sim {\mathcal {N}}(\mu ,\sigma ^{2})$ with known [variance](https://en.wikipedia.org/wiki/Variance) *σ*<sup>2</sup>, the [conjugate prior](https://en.wikipedia.org/wiki/Conjugate_prior) distribution is also normally distributed.

This can be shown more easily by rewriting the variance as the [precision](https://en.wikipedia.org/wiki/Precision_(statistics) "Precision (statistics)"), i.e. using *τ* = 1/*σ*<sup>2</sup>. Then if $x\sim {\mathcal {N}}(\mu ,1/\tau )$ and $\mu \sim {\mathcal {N}}(\mu _{0},1/\tau _{0}),$ we proceed as follows.

First, the [likelihood function](https://en.wikipedia.org/wiki/Likelihood_function) is (using the formula above for the sum of differences from the mean): 

$$
{\begin{aligned}p(\mathbf {X} \mid \mu ,\tau )&=\prod _{i=1}^{n}{\sqrt {\frac {\tau }{2\pi }}}\exp \left(-{\frac {1}{2}}\tau (x_{i}-\mu )^{2}\right)\\&=\left({\frac {\tau }{2\pi }}\right)^{n/2}\exp \left(-{\frac {1}{2}}\tau \sum _{i=1}^{n}(x_{i}-\mu )^{2}\right)\\&=\left({\frac {\tau }{2\pi }}\right)^{n/2}\exp \left[-{\frac {1}{2}}\tau \left(\sum _{i=1}^{n}(x_{i}-{\bar {x}})^{2}+n({\bar {x}}-\mu )^{2}\right)\right].\end{aligned}}
$$

Then, we proceed as follows: 

$$
{\begin{aligned}p(\mu \mid \mathbf {X} )&\propto p(\mathbf {X} \mid \mu )p(\mu )\\&=\left({\frac {\tau }{2\pi }}\right)^{n/2}\exp \left[-{\frac {1}{2}}\tau \left(\sum _{i=1}^{n}(x_{i}-{\bar {x}})^{2}+n({\bar {x}}-\mu )^{2}\right)\right]{\sqrt {\frac {\tau _{0}}{2\pi }}}\exp \left(-{\frac {1}{2}}\tau _{0}(\mu -\mu _{0})^{2}\right)\\&\propto \exp \left(-{\frac {1}{2}}\left(\tau \left(\sum _{i=1}^{n}(x_{i}-{\bar {x}})^{2}+n({\bar {x}}-\mu )^{2}\right)+\tau _{0}(\mu -\mu _{0})^{2}\right)\right)\\&\propto \exp \left(-{\frac {1}{2}}\left(n\tau ({\bar {x}}-\mu )^{2}+\tau _{0}(\mu -\mu _{0})^{2}\right)\right)\\&=\exp \left(-{\frac {1}{2}}(n\tau +\tau _{0})\left(\mu -{\dfrac {n\tau {\bar {x}}+\tau _{0}\mu _{0}}{n\tau +\tau _{0}}}\right)^{2}+{\frac {n\tau \tau _{0}}{n\tau +\tau _{0}}}({\bar {x}}-\mu _{0})^{2}\right)\\&\propto \exp \left(-{\frac {1}{2}}(n\tau +\tau _{0})\left(\mu -{\dfrac {n\tau {\bar {x}}+\tau _{0}\mu _{0}}{n\tau +\tau _{0}}}\right)^{2}\right)\end{aligned}}
$$

In the above derivation, we used the formula above for the sum of two quadratics and eliminated all constant factors not involving μ. The result is the [kernel](https://en.wikipedia.org/wiki/Kernel_(statistics) "Kernel (statistics)") of a normal distribution, with mean ${\frac {n\tau {\bar {x}}+\tau _{0}\mu _{0}}{n\tau +\tau _{0}}}$ and precision $n\tau +\tau _{0}$, i.e. 

$$
p(\mu \mid \mathbf {X} )\sim {\mathcal {N}}\left({\frac {n\tau {\bar {x}}+\tau _{0}\mu _{0}}{n\tau +\tau _{0}}},{\frac {1}{n\tau +\tau _{0}}}\right)
$$

This can be written as a set of Bayesian update equations for the posterior parameters in terms of the prior parameters: 

$$
{\begin{aligned}\tau _{0}'&=\tau _{0}+n\tau \\[5pt]\mu _{0}'&={\frac {n\tau {\bar {x}}+\tau _{0}\mu _{0}}{n\tau +\tau _{0}}}\\[5pt]{\bar {x}}&={\frac {1}{n}}\sum _{i=1}^{n}x_{i}\end{aligned}}
$$

That is, to combine n data points with total precision of *nτ* (or equivalently, total variance of *n*/*σ*<sup>2</sup>) and mean of values ${\bar {x}}$, derive a new total precision simply by adding the total precision of the data to the prior total precision, and form a new mean through a *precision-weighted average*, i.e. a [weighted average](https://en.wikipedia.org/wiki/Weighted_average) of the data mean and the prior mean, each weighted by the associated total precision. This makes logical sense if the precision is thought of as indicating the certainty of the observations: In the distribution of the posterior mean, each of the input components is weighted by its certainty, and the certainty of this distribution is the sum of the individual certainties. (For the intuition of this, compare the expression "the whole is (or is not) greater than the sum of its parts". In addition, consider that the knowledge of the posterior comes from a combination of the knowledge of the prior and likelihood, so it makes sense that we are more certain of it than of either of its components.)

The above formula reveals why it is more convenient to do [Bayesian analysis](https://en.wikipedia.org/wiki/Bayesian_analysis) of [conjugate priors](https://en.wikipedia.org/wiki/Conjugate_prior) for the normal distribution in terms of the precision. The posterior precision is simply the sum of the prior and likelihood precisions, and the posterior mean is computed through a precision-weighted average, as described above. The same formulas can be written in terms of variance by reciprocating all the precisions, yielding the more ugly formulas 

$$
{\begin{aligned}{\sigma _{0}^{2}}'&={\frac {1}{{\frac {n}{\sigma ^{2}}}+{\frac {1}{\sigma _{0}^{2}}}}}\\[5pt]\mu _{0}'&={\frac {{\frac {n{\bar {x}}}{\sigma ^{2}}}+{\frac {\mu _{0}}{\sigma _{0}^{2}}}}{{\frac {n}{\sigma ^{2}}}+{\frac {1}{\sigma _{0}^{2}}}}}\\[5pt]{\bar {x}}&={\frac {1}{n}}\sum _{i=1}^{n}x_{i}\end{aligned}}
$$

#### With known mean

For a set of [i.i.d.](https://en.wikipedia.org/wiki/I.i.d.) normally distributed data points **X** of size n where each individual point x follows $x\sim {\mathcal {N}}(\mu ,\sigma ^{2})$ with known mean μ, the [conjugate prior](https://en.wikipedia.org/wiki/Conjugate_prior) of the [variance](https://en.wikipedia.org/wiki/Variance) has an [inverse gamma distribution](https://en.wikipedia.org/wiki/Inverse_gamma_distribution) or a [scaled inverse chi-squared distribution](https://en.wikipedia.org/wiki/Scaled_inverse_chi-squared_distribution). The two are equivalent except for having different [parameterizations](https://en.wikipedia.org/wiki/Parameter). Although the inverse gamma is more commonly used, we use the scaled inverse chi-squared for the sake of convenience. The prior for *σ*<sup>2</sup> is as follows: 

$$
p(\sigma ^{2}\mid \nu _{0},\sigma _{0}^{2})={\frac {(\sigma _{0}^{2}{\frac {\nu _{0}}{2}})^{\nu _{0}/2}}{\Gamma \left({\frac {\nu _{0}}{2}}\right)}}~{\frac {\exp \left[{\frac {-\nu _{0}\sigma _{0}^{2}}{2\sigma ^{2}}}\right]}{(\sigma ^{2})^{1+{\frac {\nu _{0}}{2}}}}}\propto {\frac {\exp \left[{\frac {-\nu _{0}\sigma _{0}^{2}}{2\sigma ^{2}}}\right]}{(\sigma ^{2})^{1+{\frac {\nu _{0}}{2}}}}}
$$

The [likelihood function](https://en.wikipedia.org/wiki/Likelihood_function) from above, written in terms of the variance, is: 

$$
{\begin{aligned}p(\mathbf {X} \mid \mu ,\sigma ^{2})&=\left({\frac {1}{2\pi \sigma ^{2}}}\right)^{n/2}\exp \left[-{\frac {1}{2\sigma ^{2}}}\sum _{i=1}^{n}(x_{i}-\mu )^{2}\right]\\&=\left({\frac {1}{2\pi \sigma ^{2}}}\right)^{n/2}\exp \left[-{\frac {S}{2\sigma ^{2}}}\right]\end{aligned}}
$$

 where 

$$
S=\sum _{i=1}^{n}(x_{i}-\mu )^{2}.
$$

Then: 

$$
{\begin{aligned}p(\sigma ^{2}\mid \mathbf {X} )&\propto p(\mathbf {X} \mid \sigma ^{2})p(\sigma ^{2})\\&=\left({\frac {1}{2\pi \sigma ^{2}}}\right)^{n/2}\exp \left[-{\frac {S}{2\sigma ^{2}}}\right]{\frac {(\sigma _{0}^{2}{\frac {\nu _{0}}{2}})^{\frac {\nu _{0}}{2}}}{\Gamma \left({\frac {\nu _{0}}{2}}\right)}}~{\frac {\exp \left[{\frac {-\nu _{0}\sigma _{0}^{2}}{2\sigma ^{2}}}\right]}{(\sigma ^{2})^{1+{\frac {\nu _{0}}{2}}}}}\\&\propto \left({\frac {1}{\sigma ^{2}}}\right)^{n/2}{\frac {1}{(\sigma ^{2})^{1+{\frac {\nu _{0}}{2}}}}}\exp \left[-{\frac {S}{2\sigma ^{2}}}+{\frac {-\nu _{0}\sigma _{0}^{2}}{2\sigma ^{2}}}\right]\\&={\frac {1}{(\sigma ^{2})^{1+{\frac {\nu _{0}+n}{2}}}}}\exp \left[-{\frac {\nu _{0}\sigma _{0}^{2}+S}{2\sigma ^{2}}}\right]\end{aligned}}
$$

The above is also a scaled inverse chi-squared distribution where 

$$
{\begin{aligned}\nu _{0}'&=\nu _{0}+n\\\nu _{0}'{\sigma _{0}^{2}}'&=\nu _{0}\sigma _{0}^{2}+\sum _{i=1}^{n}(x_{i}-\mu )^{2}\end{aligned}}
$$

 or equivalently 

$$
{\begin{aligned}\nu _{0}'&=\nu _{0}+n\\{\sigma _{0}^{2}}'&={\frac {\nu _{0}\sigma _{0}^{2}+\sum _{i=1}^{n}(x_{i}-\mu )^{2}}{\nu _{0}+n}}\end{aligned}}
$$

Reparameterizing in terms of an [inverse gamma distribution](https://en.wikipedia.org/wiki/Inverse_gamma_distribution), the result is: 

$$
{\begin{aligned}\alpha '&=\alpha +{\frac {n}{2}}\\\beta '&=\beta +{\frac {\sum _{i=1}^{n}(x_{i}-\mu )^{2}}{2}}\end{aligned}}
$$

#### With unknown mean and unknown variance

For a set of [i.i.d.](https://en.wikipedia.org/wiki/I.i.d.) normally distributed data points **X** of size n where each individual point x follows $x\sim {\mathcal {N}}(\mu ,\sigma ^{2})$ with unknown mean μ and unknown [variance](https://en.wikipedia.org/wiki/Variance) *σ*<sup>2</sup>, a combined (multivariate) [conjugate prior](https://en.wikipedia.org/wiki/Conjugate_prior) is placed over the mean and variance, consisting of a [normal-inverse-gamma distribution](https://en.wikipedia.org/wiki/Normal-inverse-gamma_distribution). Logically, this originates as follows:

1.  From the analysis of the case with unknown mean but known variance, we see that the update equations involve [sufficient statistics](https://en.wikipedia.org/wiki/Sufficient_statistic) computed from the data consisting of the mean of the data points and the total variance of the data points, computed in turn from the known variance divided by the number of data points.
2.  From the analysis of the case with unknown variance but known mean, we see that the update equations involve sufficient statistics over the data consisting of the number of data points and [sum of squared deviations](https://en.wikipedia.org/wiki/Sum_of_squared_deviations).
3.  Keep in mind that the posterior update values serve as the prior distribution when further data is handled. Thus, we should logically think of our priors in terms of the sufficient statistics just described, with the same semantics kept in mind as much as possible.
4.  To handle the case where both mean and variance are unknown, we could place independent priors over the mean and variance, with fixed estimates of the average mean, total variance, number of data points used to compute the variance prior, and sum of squared deviations. Note however that in reality, the total variance of the mean depends on the unknown variance, and the sum of squared deviations that goes into the variance prior (appears to) depend on the unknown mean. In practice, the latter dependence is relatively unimportant: Shifting the actual mean shifts the generated points by an equal amount, and on average the squared deviations will remain the same. This is not the case, however, with the total variance of the mean: As the unknown variance increases, the total variance of the mean will increase proportionately, and we would like to capture this dependence.
5.  This suggests that we create a *conditional prior* of the mean on the unknown variance, with a hyperparameter specifying the mean of the [pseudo-observations](https://en.wikipedia.org/wiki/Pseudo-observation) associated with the prior, and another parameter specifying the number of pseudo-observations. This number serves as a scaling parameter on the variance, making it possible to control the overall variance of the mean relative to the actual variance parameter. The prior for the variance also has two hyperparameters, one specifying the sum of squared deviations of the pseudo-observations associated with the prior, and another specifying once again the number of pseudo-observations. Each of the priors has a hyperparameter specifying the number of pseudo-observations, and in each case this controls the relative variance of that prior. These are given as two separate hyperparameters so that the variance (aka the confidence) of the two priors can be controlled separately.
6.  This leads immediately to the [normal-inverse-gamma distribution](https://en.wikipedia.org/wiki/Normal-inverse-gamma_distribution), which is the product of the two distributions just defined, with [conjugate priors](https://en.wikipedia.org/wiki/Conjugate_prior) used (an [inverse gamma distribution](https://en.wikipedia.org/wiki/Inverse_gamma_distribution) over the variance, and a normal distribution over the mean, *conditional* on the variance) and with the same four parameters just defined.

The priors are normally defined as follows: 

$$
{\begin{aligned}p(\mu \mid \sigma ^{2};\mu _{0},n_{0})&\sim {\mathcal {N}}(\mu _{0},\sigma ^{2}/n_{0})\\p(\sigma ^{2};\nu _{0},\sigma _{0}^{2})&\sim I\chi ^{2}(\nu _{0},\sigma _{0}^{2})=IG(\nu _{0}/2,\nu _{0}\sigma _{0}^{2}/2)\end{aligned}}
$$

The update equations can be derived, and look as follows: 

$$
{\begin{aligned}{\bar {x}}&={\frac {1}{n}}\sum _{i=1}^{n}x_{i}\\\mu _{0}'&={\frac {n_{0}\mu _{0}+n{\bar {x}}}{n_{0}+n}}\\n_{0}'&=n_{0}+n\\\nu _{0}'&=\nu _{0}+n\\\nu _{0}'{\sigma _{0}^{2}}'&=\nu _{0}\sigma _{0}^{2}+\sum _{i=1}^{n}(x_{i}-{\bar {x}})^{2}+{\frac {n_{0}n}{n_{0}+n}}(\mu _{0}-{\bar {x}})^{2}\end{aligned}}
$$

The respective numbers of pseudo-observations add the number of actual observations to them. The new mean hyperparameter is once again a weighted average, this time weighted by the relative numbers of observations. Finally, the update for $\nu _{0}'{\sigma _{0}^{2}}'$ is similar to the case with known mean, but in this case the sum of squared deviations is taken with respect to the observed data mean rather than the true mean, and as a result a new interaction term needs to be added to take care of the additional error source stemming from the deviation between prior and data mean.

## Occurrence and applications

The occurrence of normal distribution in practical problems can be loosely classified into four categories:

1.  Exactly normal distributions;
2.  Approximately normal laws, for example when such approximation is justified by the [[Central Limit Theorem]]; and
3.  Distributions modeled as normal – the normal distribution being the distribution with [maximum entropy](https://en.wikipedia.org/wiki/Principle_of_maximum_entropy) for a given mean and variance.
4.  Regression problems – the normal distribution being found after systematic effects have been modeled sufficiently well.

### Exact normality

![[media/133ffe354d0e4f5a55855726addeda9a2189da1d.png]]
The ground state of a [quantum harmonic oscillator](https://en.wikipedia.org/wiki/Quantum_harmonic_oscillator) has the Gaussian distribution.

A normal distribution occurs in some [physical theories](https://en.wikipedia.org/wiki/Physical_theory):

- The [velocity distribution](https://en.wikipedia.org/wiki/Maxwell%E2%80%93Boltzmann_distribution#Distribution_for_the_velocity_vector) of independently moving and perfectly elastic spheres, which is a consequence of [Maxwell's Dynamical Theory of Gases, Part I (1860)](https://en.wikipedia.org/wiki/Maxwell%27s_theorem).
- The [ground state](https://en.wikipedia.org/wiki/Ground_state) [wave function](https://en.wikipedia.org/wiki/Wave_function) in [position space](https://en.wikipedia.org/wiki/Position_and_momentum_spaces#Quantum_mechanics) of the [quantum harmonic oscillator](https://en.wikipedia.org/wiki/Quantum_harmonic_oscillator).
- The position of a particle that experiences [diffusion](https://en.wikipedia.org/wiki/Diffusion).<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup> If initially the particle is located at a specific point (that is its probability distribution is the [Dirac delta function](https://en.wikipedia.org/wiki/Dirac_delta_function)), then after time t its location is described by a normal distribution with variance t, which satisfies the [diffusion equation](https://en.wikipedia.org/wiki/Diffusion_equation) ${\frac {\partial }{\partial t}}f(x,t)={\frac {1}{2}}{\frac {\partial ^{2}}{\partial x^{2}}}f(x,t)$. If the initial location is given by a certain density function $g(x)$, then the density at time t is the [convolution](https://en.wikipedia.org/wiki/Convolution) of g and the normal probability density function.

### Approximate normality

*Approximately* normal distributions occur in many situations, as explained by the [[Central Limit Theorem]]. When the outcome is produced by many small effects acting *additively and independently*, its distribution will be close to normal. The normal approximation will not be valid if the effects act multiplicatively (instead of additively), or if there is a single external influence that has a considerably larger magnitude than the rest of the effects.

- In counting problems, where the central limit theorem includes a discrete-to-continuum approximation and where [infinitely divisible](https://en.wikipedia.org/wiki/Infinitely_divisible) and [decomposable](https://en.wikipedia.org/wiki/Indecomposable_distribution) distributions are involved, such as
  - [Binomial random variables](https://en.wikipedia.org/wiki/Binomial_distribution), associated with binary response variables;
  - [Poisson random variables](https://en.wikipedia.org/wiki/Poisson_random_variables), associated with rare events;
- [Thermal radiation](https://en.wikipedia.org/wiki/Thermal_radiation) has a [Bose–Einstein](https://en.wikipedia.org/wiki/Bose%E2%80%93Einstein_statistics) distribution on very short time scales, and a normal distribution on longer timescales due to the central limit theorem.

### Assumed normality

![[media/79becd2d683a1681dfd0f8984ed8b5bb76b2dde0.png]]
Histogram of sepal widths for <em>Iris versicolor</em> from Fisher's [Iris flower data set](https://en.wikipedia.org/wiki/Iris_flower_data_set), with superimposed best-fitting normal distribution

> I can only recognize the occurrence of the normal curve – the Laplacian curve of errors – as a very abnormal phenomenon. It is roughly approximated to in certain distributions; for this reason, and on account for its beautiful simplicity, we may, perhaps, use it as a first approximation, particularly in theoretical investigations.

— 

There are statistical methods to empirically test that assumption; see the above [Normality tests](#Normality_tests) section.

- In [biology](https://en.wikipedia.org/wiki/Biology), the *logarithm* of various variables tend to have a normal distribution, that is, they tend to have a [log-normal distribution](https://en.wikipedia.org/wiki/Log-normal_distribution) (after separation on male/female subpopulations), with examples including:
  - Measures of size of living tissue (length, height, skin area, weight);
  - The *length* of *inert* appendages (hair, claws, nails, teeth) of biological specimens, *in the direction of growth*; presumably the thickness of tree bark also falls under this category;
  - Certain physiological measurements, such as blood pressure of adult humans.
- In finance, in particular the [Black–Scholes model](https://en.wikipedia.org/wiki/Black%E2%80%93Scholes_model), changes in the *logarithm* of exchange rates, price indices, and stock market indices are assumed normal (these variables behave like [compound interest](https://en.wikipedia.org/wiki/Compound_interest), not like simple interest, and so are multiplicative). Some mathematicians such as [Benoit Mandelbrot](https://en.wikipedia.org/wiki/Benoit_Mandelbrot) have argued that [log-Levy distributions](https://en.wikipedia.org/wiki/Levy_skew_alpha-stable_distribution), which possess [heavy tails](https://en.wikipedia.org/wiki/Heavy_tails), would be a more appropriate model, in particular for the analysis for [stock market crashes](https://en.wikipedia.org/wiki/Stock_market_crash). The use of the assumption of normal distribution occurring in financial models has also been criticized by [Nassim Nicholas Taleb](https://en.wikipedia.org/wiki/Nassim_Nicholas_Taleb) in his works.
- [Measurement errors](https://en.wikipedia.org/wiki/Propagation_of_uncertainty) in physical experiments are often modeled by a normal distribution. This use of a normal distribution does not imply that one is assuming the measurement errors are normally distributed, rather using the normal distribution produces the most conservative predictions possible given only knowledge about the mean and variance of the errors.
- In [standardized testing](https://en.wikipedia.org/wiki/Standardized_testing_(statistics)), results can be made to have a normal distribution by either selecting the number and difficulty of questions (as in the [IQ test](https://en.wikipedia.org/wiki/Intelligence_quotient)) or transforming the raw test scores into output scores by fitting them to the normal distribution. For example, the [SAT](https://en.wikipedia.org/wiki/SAT)'s traditional range of 200–800 is based on a normal distribution with a mean of 500 and a standard deviation of 100.

![[media/0b67b8aee4c43b34026c0f9ed932c06c784da8a2.png]]
Fitted cumulative normal distribution to October rainfalls, see [distribution fitting](https://en.wikipedia.org/wiki/Distribution_fitting)

- Many scores are derived from the normal distribution, including [percentile ranks](https://en.wikipedia.org/wiki/Percentile_rank) (percentiles or quantiles), [normal curve equivalents](https://en.wikipedia.org/wiki/Normal_curve_equivalent), [stanines](https://en.wikipedia.org/wiki/Stanine), [z-scores](https://en.wikipedia.org/wiki/Z-scores), and T-scores. Additionally, some [behavioral statistical](https://en.wikipedia.org/wiki/Psychological_statistics) procedures assume that scores are normally distributed; for example, [t-tests](https://en.wikipedia.org/wiki/T-tests) and [ANOVAs](https://en.wikipedia.org/wiki/Analysis_of_variance). [Bell curve grading](https://en.wikipedia.org/wiki/Bell_curve_grading) assigns relative grades based on a normal distribution of scores.
- In [hydrology](https://en.wikipedia.org/wiki/Hydrology) the distribution of long duration river discharge or rainfall, e.g. monthly and yearly totals, is often thought to be practically normal according to the [[Central Limit Theorem]]. The plot on the right illustrates an example of fitting the normal distribution to ranked October rainfalls showing the 90% [confidence belt](https://en.wikipedia.org/wiki/Confidence_belt) based on the [binomial distribution](https://en.wikipedia.org/wiki/Binomial_distribution). The rainfall data are represented by [plotting positions](https://en.wikipedia.org/wiki/Plotting_position) as part of the [cumulative frequency analysis](https://en.wikipedia.org/wiki/Cumulative_frequency_analysis).

### Methodological problems and peer review

[John Ioannidis](https://en.wikipedia.org/wiki/John_Ioannidis) [argued](https://en.wikipedia.org/wiki/Why_Most_Published_Research_Findings_Are_False) that using normally distributed standard deviations as standards for validating research findings leave [falsifiable predictions](https://en.wikipedia.org/wiki/Falsifiability) about phenomena that are not normally distributed untested. This includes, for example, phenomena that only appear when all necessary conditions are present and one cannot be a substitute for another in an addition-like way and phenomena that are not randomly distributed. Ioannidis argues that standard deviation-centered validation gives a false appearance of validity to hypotheses and theories where some but not all falsifiable predictions are normally distributed since the portion of falsifiable predictions that there is evidence against may and in some cases are in the non-normally distributed parts of the range of falsifiable predictions, as well as baselessly dismissing hypotheses for which none of the falsifiable predictions are normally distributed as if they were unfalsifiable when in fact they do make falsifiable predictions. It is argued by Ioannidis that many cases of mutually exclusive theories being accepted as validated by research journals are caused by failure of the journals to take in empirical falsifications of non-normally distributed predictions, and not because mutually exclusive theories are true, which they cannot be, although two mutually exclusive theories can both be wrong and a third one correct.

## Computational methods

### Generating values from normal distribution

![[media/c0acc3d430ee5001fded62659010afbe6e9628df.jpg]]
The [bean machine](https://en.wikipedia.org/wiki/Bean_machine), a device invented by [Francis Galton](https://en.wikipedia.org/wiki/Francis_Galton), can be called the first generator of normal random variables. This machine consists of a vertical board with interleaved rows of pins. Small balls are dropped from the top and then bounce randomly left or right as they hit the pins. The balls are collected into bins at the bottom and settle down into a pattern resembling the Gaussian curve.

In computer simulations, especially in applications of the [[Monte Carlo Method|Monte-Carlo method]], it is often desirable to generate values that are normally distributed. The algorithms listed below all generate the standard normal deviates, since a *N*(*μ*, *σ*<sup>2</sup>) can be generated as *X* = *μ* + *σZ*, where Z is standard normal. All these algorithms rely on the availability of a [random number generator](https://en.wikipedia.org/wiki/Random_number_generator) U capable of producing [uniform](https://en.wikipedia.org/wiki/Uniform_distribution_(continuous)) random variates.

- The most straightforward method is based on the [probability integral transform](https://en.wikipedia.org/wiki/Probability_integral_transform) property: if U is distributed uniformly on (0,1), then *Φ*<sup>−1</sup>(*U*) will have the standard normal distribution. The drawback of this method is that it relies on calculation of the [probit function](https://en.wikipedia.org/wiki/Probit_function) Φ<sup>−1</sup>, which cannot be done analytically. Some approximate methods are described in  and in the [erf](https://en.wikipedia.org/wiki/Error_function) article. Wichura gives a fast algorithm for computing this function to 16 decimal places, which is used by [R](https://en.wikipedia.org/wiki/R_programming_language) to compute random variates of the normal distribution.
- [An easy-to-program approximate approach](https://en.wikipedia.org/wiki/Irwin%E2%80%93Hall_distribution#Approximating_a_Normal_distribution) that relies on the [[Central Limit Theorem]] is as follows: generate 12 uniform *U*(0,1) deviates, add them all up, and subtract 6 – the resulting random variable will have approximately standard normal distribution. In truth, the distribution will be [Irwin–Hall](https://en.wikipedia.org/wiki/Irwin%E2%80%93Hall_distribution), which is a 12-section eleventh-order polynomial approximation to the normal distribution. This random deviate will have a limited range of (−6, 6). Note that in a true normal distribution, only 0.00034% of all samples will fall outside ±6*σ*.
- The [Box–Muller method](https://en.wikipedia.org/wiki/Box%E2%80%93Muller_method) uses two independent random numbers U and V distributed [uniformly](https://en.wikipedia.org/wiki/Uniform_distribution_(continuous)) on (0,1). Then the two random variables X and Y 

$$
X={\sqrt {-2\ln U}}\,\cos(2\pi V),\qquad Y={\sqrt {-2\ln U}}\,\sin(2\pi V).
$$

 will both have the standard normal distribution, and will be [independent](https://en.wikipedia.org/wiki/Independence_(probability_theory) "Independence (probability theory)"). This formulation arises because for a [bivariate normal](https://en.wikipedia.org/wiki/Bivariate_normal) random vector (*X*, *Y*) the squared norm *X*<sup>2</sup> + *Y*<sup>2</sup> will have the [chi-squared distribution](https://en.wikipedia.org/wiki/Chi-squared_distribution) with two degrees of freedom, which is an easily generated [exponential random variable](https://en.wikipedia.org/wiki/Exponential_random_variable) corresponding to the quantity −2 ln(*U*) in these equations; and the angle is distributed uniformly around the circle, chosen by the random variable V.
- The [Marsaglia polar method](https://en.wikipedia.org/wiki/Marsaglia_polar_method) is a modification of the Box–Muller method which does not require computation of the sine and cosine functions. In this method, U and V are drawn from the uniform (−1,1) distribution, and then *S* = *U*<sup>2</sup> + *V*<sup>2</sup> is computed. If S is greater or equal to 1, then the method starts over, otherwise the two quantities 

$$
X=U{\sqrt {\frac {-2\ln S}{S}}},\qquad Y=V{\sqrt {\frac {-2\ln S}{S}}}
$$

 are returned. Again, X and Y are independent, standard normal random variables.
- The Ratio method is a rejection method. The algorithm proceeds as follows:
  - Generate two independent uniform deviates U and V;
  - Compute *X* = √8/*e* (*V* − 0.5)/*U*;
  - Optional: if *X*<sup>2</sup> ≤ 5 − 4*e*<sup>1/4</sup>*U* then accept X and terminate algorithm;
  - Optional: if *X*<sup>2</sup> ≥ 4*e*<sup>−1.35</sup>/*U* + 1.4 then reject X and start over from step 1;
  - If *X*<sup>2</sup> ≤ −4 ln *U* then accept X, otherwise start over the algorithm.

  The two optional steps allow the evaluation of the logarithm in the last step to be avoided in most cases. These steps can be greatly improved so that the logarithm is rarely evaluated.
- The [ziggurat algorithm](https://en.wikipedia.org/wiki/Ziggurat_algorithm) is faster than the Box–Muller transform and still exact. In about 97% of all cases it uses only two random numbers, one random integer and one random uniform, one multiplication and an if-test. Only in 3% of the cases, where the combination of those two falls outside the "core of the ziggurat" (a kind of rejection sampling using logarithms), do exponentials and more uniform random numbers have to be employed.
- Integer arithmetic can be used to sample from the standard normal distribution. This method is exact in the sense that it satisfies the conditions of *ideal approximation*; i.e., it is equivalent to sampling a real number from the standard normal distribution and rounding this to the nearest representable floating point number.
- There is also some investigation into the connection between the fast [Hadamard transform](https://en.wikipedia.org/wiki/Hadamard_transform) and the normal distribution, since the transform employs just addition and subtraction and by the central limit theorem random numbers from almost any distribution will be transformed into the normal distribution. In this regard a series of Hadamard transforms can be combined with random permutations to turn arbitrary data sets into a normally distributed data.

### Numerical approximations for the normal cumulative distribution function and normal quantile function

The standard normal [[Cumulative Distribution Function]] is widely used in scientific and statistical computing.

The values *Φ*(*x*) may be approximated very accurately by a variety of methods, such as [numerical integration](https://en.wikipedia.org/wiki/Numerical_integration), [[Taylor Series]], [asymptotic series](https://en.wikipedia.org/wiki/Asymptotic_series) and [continued fractions](https://en.wikipedia.org/wiki/Gauss%27s_continued_fraction#Of_Kummer's_confluent_hypergeometric_function). Different approximations are used depending on the desired level of accuracy.

-  give the approximation for *Φ*(*x*) for *x* \> 0 with the absolute error \|*ε*(*x*)\| \< 7.5·10<sup>−8</sup> (algorithm [26.2.17](https://secure.math.ubc.ca/~cbm/aands/page_932.htm)): 

$$
\Phi (x)=1-\varphi (x)\left(b_{1}t+b_{2}t^{2}+b_{3}t^{3}+b_{4}t^{4}+b_{5}t^{5}\right)+\varepsilon (x),\qquad t={\frac {1}{1+b_{0}x}},
$$

 where *ϕ*(*x*) is the standard normal probability density function, and *b*<sub>0</sub> = 0.2316419, *b*<sub>1</sub> = 0.319381530, *b*<sub>2</sub> = −0.356563782, *b*<sub>3</sub> = 1.781477937, *b*<sub>4</sub> = −1.821255978, *b*<sub>5</sub> = 1.330274429.
-  lists dozens of approximations by means of rational functions, with or without exponentials, for the erfc() function, where erfc(x) = 1 - erf(x). His algorithms vary in the degree of complexity and the resulting precision, with a maximum absolute precision of 24 digits. An algorithm by  combines Hart's algorithm 5666 with a [continued fraction](https://en.wikipedia.org/wiki/Continued_fraction) approximation in the tail to provide a fast computation algorithm with 16-digit precision.
- , after recalling the Hart68 solution is not suited for erf, gave a solution for both erf and erfc, with maximal relative error bound, via [Rational Chebyshev Approximation](https://en.wikipedia.org/wiki/Rational_function).
-  suggested a simple algorithm based on the Taylor series expansion 

$$
\Phi (x)={\frac {1}{2}}+\varphi (x)\left(x+{\frac {x^{3}}{3}}+{\frac {x^{5}}{3\cdot 5}}+{\frac {x^{7}}{3\cdot 5\cdot 7}}+{\frac {x^{9}}{3\cdot 5\cdot 7\cdot 9}}+\cdots \right)
$$

 for calculating *Φ*(*x*) with arbitrary precision. The drawback of this algorithm is comparatively slow calculation time (for example it takes over 300 iterations to calculate the function with 16 digits of precision when *x* = 10).
- The [GNU Scientific Library](https://en.wikipedia.org/wiki/GNU_Scientific_Library) calculates values of the standard normal cumulative distribution function using Hart's algorithms and approximations with [Chebyshev polynomials](https://en.wikipedia.org/wiki/Chebyshev_polynomial).
-  proposes the following approximation of $1-\Phi$ with a maximum relative error less than $2^{-53}$ $\left(\approx 1.1\times 10^{-16}\right)$ in absolute value: for $x\geq 0$${\begin{aligned}1-\Phi \left(x\right)&=\left({\frac {0.39894228040143268}{x+2.92678600515804815}}\right)\left({\frac {x^{2}+8.42742300458043240x+18.38871225773938487}{x^{2}+5.81582518933527391x+8.97280659046817350}}\right)\\&\left({\frac {x^{2}+7.30756258553673541x+18.25323235347346525}{x^{2}+5.70347935898051437x+10.27157061171363079}}\right)\left({\frac {x^{2}+5.66479518878470765x+18.61193318971775795}{x^{2}+5.51862483025707963x+12.72323261907760928}}\right)\\&\left({\frac {x^{2}+4.91396098895240075x+24.14804072812762821}{x^{2}+5.26184239579604207x+16.88639562007936908}}\right)\left({\frac {x^{2}+3.83362947800146179x+11.61511226260603247}{x^{2}+4.92081346632882033x+24.12333774572479110}}\right)e^{-{\frac {x^{2}}{2}}}\end{aligned}}$ and for $x<0$,

$$
1-\Phi \left(x\right)=1-\left(1-\Phi \left(-x\right)\right)
$$

Shore (1982) introduced simple approximations that may be incorporated in stochastic optimization models of engineering and operations research, like reliability engineering and inventory analysis. Denoting *p* = *Φ*(*z*), the simplest approximation for the quantile function is: 

$$
z=\Phi ^{-1}(p)=5.5556\left[1-\left({\frac {1-p}{p}}\right)^{0.1186}\right],\qquad p\geq 1/2
$$

This approximation delivers for z a maximum absolute error of 0.026 (for 0.5 ≤ *p* ≤ 0.9999, corresponding to 0 ≤ *z* ≤ 3.719). For *p* \< 1/2 replace p by 1 − *p* and change sign. Another approximation, somewhat less accurate, is the single-parameter approximation: 

$$
z=-0.4115\left\{{\frac {1-p}{p}}+\log \left[{\frac {1-p}{p}}\right]-1\right\},\qquad p\geq 1/2
$$

The latter had served to derive a simple approximation for the loss integral of the normal distribution, defined by 

$$
{\begin{aligned}L(z)&=\int _{z}^{\infty }(u-z)\varphi (u)\,du=\int _{z}^{\infty }[1-\Phi (u)]\,du\\[5pt]L(z)&\approx {\begin{cases}0.4115\left({\dfrac {p}{1-p}}\right)-z,&p<1/2,\\\\0.4115\left({\dfrac {1-p}{p}}\right),&p\geq 1/2.\end{cases}}\\[5pt]{\text{or, equivalently,}}\\L(z)&\approx {\begin{cases}0.4115\left\{1-\log \left[{\frac {p}{1-p}}\right]\right\},&p<1/2,\\\\0.4115{\dfrac {1-p}{p}},&p\geq 1/2.\end{cases}}\end{aligned}}
$$

This approximation is particularly accurate for the right far-tail (maximum error of 10<sup>−3</sup> for *z* ≥ 1.4). Highly accurate approximations for the cumulative distribution function, based on [Response Modeling Methodology](https://en.wikipedia.org/wiki/Response_Modeling_Methodology) (RMM, Shore, 2011, 2012), are shown in Shore (2005).

Some more approximations can be found at: [Error function#Approximation with elementary functions](https://en.wikipedia.org/wiki/Error_function#Approximation_with_elementary_functions). In particular, small *relative* error on the whole domain for the cumulative distribution function $\Phi$ and the quantile function $\Phi ^{-1}$ as well, is achieved via an explicitly invertible formula by Sergei Winitzki in 2008.

## History

### Development

Some authors attribute the discovery of the normal distribution to [de Moivre](https://en.wikipedia.org/wiki/De_Moivre), who in 1738 published in the second edition of his *[The Doctrine of Chances](https://en.wikipedia.org/wiki/The_Doctrine_of_Chances)* the study of the coefficients in the [binomial expansion](https://en.wikipedia.org/wiki/Binomial_expansion) of (*a* + *b*)<sup>*n*</sup>. De Moivre proved that the middle term in this expansion has the approximate magnitude of $2^{n}/{\sqrt {2\pi n}}$, and that "If m or 1/2*n* be a Quantity infinitely great, then the Logarithm of the Ratio, which a Term distant from the middle by the Interval ℓ, has to the middle Term, is $-{\frac {2\ell \ell }{n}}$." Although this theorem can be interpreted as the first obscure expression for the normal probability law, [Stigler](https://en.wikipedia.org/wiki/Stephen_Stigler) points out that de Moivre himself did not interpret his results as anything more than the approximate rule for the binomial coefficients, and in particular de Moivre lacked the concept of the probability density function.

![[media/db4fb50e56aaa0a7d7c39bc3fd63f0c987d293f5.jpg]]
In 1809, [Carl Friedrich Gauss](https://en.wikipedia.org/wiki/Carl_Friedrich_Gauss) showed that the normal distribution provides a way to rationalize the [method of least squares](https://en.wikipedia.org/wiki/Method_of_least_squares).

In 1823 [Gauss](https://en.wikipedia.org/wiki/Gauss) published his monograph "*Theoria combinationis observationum erroribus minimis obnoxiae*" where among other things he introduces several important statistical concepts, such as the [method of least squares](https://en.wikipedia.org/wiki/Method_of_least_squares), the [method of maximum likelihood](https://en.wikipedia.org/wiki/Method_of_maximum_likelihood), and the *normal distribution*. Gauss used M, *M*′, *M*″, ... to denote the measurements of some unknown quantity V, and sought the most probable estimator of that quantity: the one that maximizes the probability *φ*(*M* − *V*) · *φ*(*M*′ − *V*) · *φ*(*M*″ − *V*) · ... of obtaining the observed experimental results. In his notation φΔ is the probability density function of the measurement errors of magnitude Δ. Not knowing what the function φ is, Gauss requires that his method should reduce to the well-known answer: the arithmetic mean of the measured values. Starting from these principles, Gauss demonstrates that the only law that rationalizes the choice of arithmetic mean as an estimator of the location parameter, is the normal law of errors: 

$$
\varphi {\mathit {\Delta }}={\frac {h}{\surd \pi }}\,e^{-\mathrm {hh} \Delta \Delta },
$$

 where h is "the measure of the precision of the observations". Using this normal law as a generic model for errors in the experiments, Gauss formulates what is now known as the [non-linear](https://en.wikipedia.org/wiki/Non-linear_least_squares) [weighted least squares](https://en.wikipedia.org/wiki/Weighted_least_squares) method.

![[media/e97ecabb3d2d5f602e56fa6d7eda9dd8fb616ee4.jpg]]
[Pierre-Simon Laplace](https://en.wikipedia.org/wiki/Pierre-Simon_Laplace) proved the [[Central Limit Theorem]] in 1810, consolidating the importance of the normal distribution in statistics.

Although Gauss was the first to suggest the normal distribution law, [Laplace](https://en.wikipedia.org/wiki/Laplace) made significant contributions. It was Laplace who first posed the problem of aggregating several observations in 1774, although his own solution led to the [Laplacian distribution](https://en.wikipedia.org/wiki/Laplacian_distribution). It was Laplace who first calculated the value of the [integral ∫ *e*<sup>−*t*<sup>2</sup></sup> *dt* = √π](https://en.wikipedia.org/wiki/Gaussian_integral) in 1782, providing the normalization constant for the normal distribution. For this accomplishment, Gauss acknowledged the priority of Laplace. Finally, it was Laplace who in 1810 proved and presented to the academy the fundamental [[Central Limit Theorem]], which emphasized the theoretical importance of the normal distribution.

It is of interest to note that in 1809 an Irish-American mathematician [Robert Adrain](https://en.wikipedia.org/wiki/Robert_Adrain) published two insightful but flawed derivations of the normal probability law, simultaneously and independently from Gauss. His works remained largely unnoticed by the scientific community, until in 1871 they were exhumed by [Abbe](https://en.wikipedia.org/wiki/Cleveland_Abbe).

In the middle of the 19th century [Maxwell](https://en.wikipedia.org/wiki/James_Clerk_Maxwell) demonstrated that the normal distribution is not just a convenient mathematical tool, but may also occur in natural phenomena: The number of particles whose velocity, resolved in a certain direction, lies between x and *x* + *dx* is 

$$
\operatorname {N} {\frac {1}{\alpha \;{\sqrt {\pi }}}}\;e^{-{\frac {x^{2}}{\alpha ^{2}}}}\,dx
$$

### Naming

Today, the concept is usually known in English as the **normal distribution** or **Gaussian distribution**. Other less common names include Gauss distribution, Laplace–Gauss distribution, the law of error, the law of facility of errors, Laplace's second law, and Gaussian law.

Gauss himself apparently coined the term with reference to the "normal equations" involved in its applications, with normal having its technical meaning of orthogonal rather than usual. However, by the end of the 19th century some authors had started using the name *normal distribution*, where the word "normal" was used as an adjective – the term now being seen as a reflection of this distribution being seen as typical, common – and thus normal. [Peirce](https://en.wikipedia.org/wiki/Charles_Sanders_Peirce) (one of those authors) once defined "normal" thus: "... the 'normal' is not the average (or any other kind of mean) of what actually occurs, but of what *would*, in the long run, occur under certain circumstances." Around the turn of the 20th century [Pearson](https://en.wikipedia.org/wiki/Karl_Pearson) popularized the term *normal* as a designation for this distribution.

> Many years ago I called the Laplace–Gaussian curve the *normal* curve, which name, while it avoids an international question of priority, has the disadvantage of leading people to believe that all other distributions of frequency are in one sense or another 'abnormal'.

— 

Also, it was Pearson who first wrote the distribution in terms of the standard deviation σ as in modern notation. Soon after this, in year 1915, [Fisher](https://en.wikipedia.org/wiki/Ronald_Fisher) added the location parameter to the formula for normal distribution, expressing it in the way it is written nowadays: 

$$
df={\frac {1}{\sqrt {2\sigma ^{2}\pi }}}e^{-(x-m)^{2}/(2\sigma ^{2})}\,dx.
$$

The term *standard normal distribution*, which denotes the normal distribution with zero mean and unit variance came into general use around the 1950s, appearing in the popular textbooks by P. G. Hoel (1947) *Introduction to Mathematical Statistics* and [Alexander M. Mood](https://en.wikipedia.org/wiki/Alexander_M._Mood) (1950) *Introduction to the Theory of Statistics*.

## See also

- ![[media/1a9c6ad1ccebbc090fc7cd1c94d2142489246997.png]][Mathematics portal](https://en.wikipedia.org/wiki/Portal:Mathematics)

- [Bates distribution](https://en.wikipedia.org/wiki/Bates_distribution) – similar to the Irwin–Hall distribution, but rescaled back into the 0 to 1 range
- [Behrens–Fisher problem](https://en.wikipedia.org/wiki/Behrens%E2%80%93Fisher_problem) – the long-standing problem of testing whether two normal samples with different variances have same means;
- [Bhattacharyya distance](https://en.wikipedia.org/wiki/Bhattacharyya_distance) – method used to separate mixtures of normal distributions
- [Erdős–Kac theorem](https://en.wikipedia.org/wiki/Erd%C5%91s%E2%80%93Kac_theorem) – on the occurrence of the normal distribution in [number theory](https://en.wikipedia.org/wiki/Number_theory)
- [Full width at half maximum](https://en.wikipedia.org/wiki/Full_width_at_half_maximum)
- [Gaussian blur](https://en.wikipedia.org/wiki/Gaussian_blur) – [convolution](https://en.wikipedia.org/wiki/Convolution), which uses the normal distribution as a kernel
- [Gaussian function](https://en.wikipedia.org/wiki/Gaussian_function)
- [Modified half-normal distribution](https://en.wikipedia.org/wiki/Modified_half-normal_distribution) with the pdf on $(0,\infty )$ is given as $f(x)={\frac {2\beta ^{\alpha /2}x^{\alpha -1}\exp(-\beta x^{2}+\gamma x)}{\Psi \left({\frac {\alpha }{2}},{\frac {\gamma }{\sqrt {\beta }}}\right)}}$, where $\Psi (\alpha ,z)={}_{1}\Psi _{1}\left({\begin{matrix}\left(\alpha ,{\frac {1}{2}}\right)\\(1,0)\end{matrix}};z\right)$ denotes the [Fox–Wright Psi function](https://en.wikipedia.org/wiki/Fox%E2%80%93Wright_Psi_function).
- [Normally distributed and uncorrelated does not imply independent](https://en.wikipedia.org/wiki/Normally_distributed_and_uncorrelated_does_not_imply_independent)
- [Ratio normal distribution](https://en.wikipedia.org/wiki/Ratio_normal_distribution)
- [Reciprocal normal distribution](https://en.wikipedia.org/wiki/Reciprocal_normal_distribution)
- [Standard normal table](https://en.wikipedia.org/wiki/Standard_normal_table)
- [Stein's lemma](https://en.wikipedia.org/wiki/Stein%27s_lemma)
- [Sub-Gaussian distribution](https://en.wikipedia.org/wiki/Sub-Gaussian_distribution)
- [Sum of normally distributed random variables](https://en.wikipedia.org/wiki/Sum_of_normally_distributed_random_variables)
- [Tweedie distribution](https://en.wikipedia.org/wiki/Tweedie_distribution) – The normal distribution is a member of the family of Tweedie [exponential dispersion models](https://en.wikipedia.org/wiki/Exponential_dispersion_model).
- [Wrapped normal distribution](https://en.wikipedia.org/wiki/Wrapped_normal_distribution) – the normal distribution applied to a circular domain
- [Z-test](https://en.wikipedia.org/wiki/Z-test) – using the normal distribution

## Notes

1.  For example, this algorithm is given in the article [Bc programming language](https://en.wikipedia.org/wiki/Bc_programming_language#A_translated_C_function).
2.  De Moivre first published his findings in 1733, in a pamphlet *Approximatio ad Summam Terminorum Binomii* (*a* + *b*)<sup>*n*</sup> *in Seriem Expansi* that was designated for private circulation only. But it was not until the year 1738 that he made his results publicly available. The original pamphlet was reprinted several times, see for example .
3.  "It has been customary certainly to regard as an axiom the hypothesis that if any quantity has been determined by several direct observations, made under the same circumstances and with equal care, the arithmetical mean of the observed values affords the most probable value, if not rigorously, yet very nearly at least, so that it is always most safe to adhere to it." — , section 177) 
4.  "My custom of terming the curve the Gauss–Laplacian or *normal* curve saves us from proportioning the merit of discovery between the two great astronomer mathematicians." quote from , p. 189) 
5.  Besides those specifically referenced here, such use is encountered in the works of [Peirce](https://en.wikipedia.org/wiki/Charles_Sanders_Peirce), [Galton](https://en.wikipedia.org/wiki/Galton) (, chapter V)) and [Lexis](https://en.wikipedia.org/wiki/Wilhelm_Lexis) (, ) c. 1875.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup> 

## References

### Citations

1.  Norton, Matthew; Khokhlov, Valentyn; Uryasev, Stan (2019). ["Calculating CVaR and bPOE for common probability distributions with application to portfolio optimization and density estimation"](https://web.archive.org/web/20230331230821/http://uryasev.ams.stonybrook.edu/wp-content/uploads/2019/10/Norton2019_CVaR_bPOE.pdf) (PDF). *Annals of Operations Research*. **299** (1–2). Springer: 1281–1315. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1811.11301](https://arxiv.org/abs/1811.11301). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s10479-019-03373-1](https://doi.org/10.1007%2Fs10479-019-03373-1). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [254231768](https://api.semanticscholar.org/CorpusID:254231768). Archived from [the original](http://uryasev.ams.stonybrook.edu/wp-content/uploads/2019/10/Norton2019_CVaR_bPOE.pdf) (PDF) on March 31, 2023. Retrieved February 27, 2023.
2.  Tsokos, Chris; Wooten, Rebecca (January 1, 2016). Tsokos, Chris; Wooten, Rebecca (eds.). [The Joy of Finite Mathematics](https://linkinghub.elsevier.com/retrieve/pii/B9780128029671000073). Boston: Academic Press. pp. 231–263. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/b978-0-12-802967-1.00007-3](https://doi.org/10.1016%2Fb978-0-12-802967-1.00007-3). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-12-802967-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-12-802967-1).
3.  Harris, Frank E. (January 1, 2014). Harris, Frank E. (ed.). [Mathematics for Physical Science and Engineering](https://linkinghub.elsevier.com/retrieve/pii/B9780128010006000183). Boston: Academic Press. pp. 663–709. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/b978-0-12-801000-6.00018-3](https://doi.org/10.1016%2Fb978-0-12-801000-6.00018-3). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-12-801000-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-12-801000-6).
4.  , [p. 31](https://archive.org/details/in.ernet.dli.2015.263186/page/n39/mode/2up?q=%22normal+distribution%22)) and , [p. 109](https://archive.org/details/introductiontoth0000alex/page/108/mode/2up?q=%22normal+distribution%22)) give this definition with slightly different notation.
5.  [Normal Distribution](http://www.encyclopedia.com/topic/Normal_Distribution.aspx#3), Gale Encyclopedia of Psychology
6.  , p. 102)
7.  Lyon, A. (2014). [Why are Normal Distributions Normal?](https://aidanlyon.com/normal_distributions.pdf), The British Journal for the Philosophy of Science.
8.  Jorge, Nocedal; Stephan, J. Wright (2006). *Numerical Optimization* (2nd ed.). Springer. p. 249. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0387-30303-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0387-30303-1).
9.  ^   ["Normal Distribution"](https://www.mathsisfun.com/data/standard-normal-distribution.html). *www.mathsisfun.com*. Retrieved August 15, 2020.
10. ["bell curve"](https://www.merriam-webster.com/dictionary/bell%20curve). *Merriam-Webster.com Dictionary*. Retrieved May 25, 2025.
11. , [p. 112](https://archive.org/details/introductiontoth0000alex/page/112/mode/2up?q=%22standard+normal+distribution%22)) explicitly defines the *standard normal distribution*. In contrast,  explicitly defines the *standard normal curve* [(p. 33)](https://archive.org/details/in.ernet.dli.2015.263186/page/n41/mode/2up?q=%22standard+normal+curve%22) and introduces the term *standard normal distribution* [(p. 69)](https://archive.org/details/in.ernet.dli.2015.263186/page/n77/mode/2up?q=%22standard+normal+distribution%22).
12. 13. , item 7)
14. , p. 110)
15. , p. 121)
16. Park, Kun Il (2018). *Fundamentals of Probability and Stochastic Processes with Applications to Communications*. Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-319-68074-3](https://en.wikipedia.org/wiki/Special:BookSources/978-3-319-68074-3).
17. Scott, Clayton; Nowak, Robert (August 7, 2003). ["The Q-function"](http://cnx.org/content/m11537/1.2/). *Connexions*.
18. Barak, Ohad (April 6, 2006). ["Q Function and Error Function"](https://web.archive.org/web/20090325160012/http://www.eng.tau.ac.il/~jo/academic/Q.pdf) (PDF). Tel Aviv University. Archived from [the original](http://www.eng.tau.ac.il/~jo/academic/Q.pdf) (PDF) on March 25, 2009.
19. [Weisstein, Eric W.](https://en.wikipedia.org/wiki/Eric_W._Weisstein) ["Normal Distribution Function"](https://mathworld.wolfram.com/NormalDistributionFunction.html). *[MathWorld](https://en.wikipedia.org/wiki/MathWorld)*.
20. [Abramowitz, Milton](https://en.wikipedia.org/wiki/Milton_Abramowitz); [Stegun, Irene Ann](https://en.wikipedia.org/wiki/Irene_Stegun), eds. (1983) \[June 1964\]. ["Chapter 26, eqn 26.2.12"](http://www.math.ubc.ca/~cbm/aands/page_932.htm). [*Handbook of Mathematical Functions with Formulas, Graphs, and Mathematical Tables*](https://en.wikipedia.org/wiki/Abramowitz_and_Stegun). Applied Mathematics Series. Vol. 55 (Ninth reprint with additional corrections of tenth original printing with corrections (December 1972); first ed.). Washington D.C.; New York: United States Department of Commerce, National Bureau of Standards; Dover Publications. p. 932. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-486-61272-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-486-61272-0). [LCCN](https://en.wikipedia.org/wiki/LCCN_(identifier)) [64-60036](https://lccn.loc.gov/64-60036). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0167642](https://mathscinet.ams.org/mathscinet-getitem?mr=0167642). [LCCN](https://en.wikipedia.org/wiki/LCCN_(identifier)) [65-12253](https://www.loc.gov/item/65012253).
21. Fischer, W., Lieb. W. (2012) A Course in Complex Analysis, From Basic Results to Advanced Topics - Teubner Vieweg 
22. Vaart, A. W. van der (October 13, 1998). [Asymptotic Statistics](https://dx.doi.org/10.1017/cbo9780511802256). Cambridge University Press. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1017/cbo9780511802256](https://doi.org/10.1017%2Fcbo9780511802256). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-511-80225-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-511-80225-6).
23. ^   , p. 254.
24. Park, Sung Y.; Bera, Anil K. (2009). ["Maximum Entropy Autoregressive Conditional Heteroskedasticity Model"](https://web.archive.org/web/20160307144515/http://wise.xmu.edu.cn/uploadfiles/paper-masterdownload/2009519932327055475115776.pdf) (PDF). *Journal of Econometrics*. **150** (2): 219–230. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2009JEcon.150..219P](https://ui.adsabs.harvard.edu/abs/2009JEcon.150..219P). [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.511.9750](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.511.9750). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.jeconom.2008.12.014](https://doi.org/10.1016%2Fj.jeconom.2008.12.014). Archived from [the original](http://www.wise.xmu.edu.cn/Master/Download/..%5C..%5CUploadFiles%5Cpaper-masterdownload%5C2009519932327055475115776.pdf) (PDF) on March 7, 2016. Retrieved June 2, 2011.
25. Geary RC(1936) The distribution of the "Student's ratio for the non-normal samples". Supplement to the Journal of the Royal Statistical Society 3 (2): 178–184
26. [Lukacs, Eugene](https://en.wikipedia.org/wiki/Eugene_Lukacs) (March 1942). ["A Characterization of the Normal Distribution"](https://archive.org/details/dli.ernet.4125/page/91). *[Annals of Mathematical Statistics](https://en.wikipedia.org/wiki/Annals_of_Mathematical_Statistics)*. **13** (1): 91–93. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/AOMS/1177731647](https://doi.org/10.1214%2FAOMS%2F1177731647). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0003-4851](https://search.worldcat.org/issn/0003-4851). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2236166](https://www.jstor.org/stable/2236166). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0006626](https://mathscinet.ams.org/mathscinet-getitem?mr=0006626). [Zbl](https://en.wikipedia.org/wiki/Zbl_(identifier)) [0060.28509](https://zbmath.org/?format=complete&q=an:0060.28509). [Wikidata](https://en.wikipedia.org/wiki/WDQ_(identifier)) [Q55897617](https://www.wikidata.org/wiki/Q55897617).
27. ^    , \[2.1.4\])
28. , p. 1258)
29. , \[2.1.8\])
30. Papoulis, Athanasios. *Probability, Random Variables and Stochastic Processes* (4th ed.). p. 148.
31. Winkelbauer, Andreas (2012). "Moments and Absolute Moments of the Normal Distribution". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1209.4340](https://arxiv.org/abs/1209.4340) \[[math.ST](https://arxiv.org/archive/math.ST)\].
32. , p. 23)
33. , p. 24)
34. Williams, David (2001). [Weighing the odds : a course in probability and statistics](https://archive.org/details/weighingoddscour00will) (Reprinted. ed.). Cambridge \[u.a.\]: Cambridge Univ. Press. pp. [197](https://archive.org/details/weighingoddscour00will/page/n219)–199. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-00618-7](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-00618-7).
35. José M. Bernardo; Adrian F. M. Smith (2000). [Bayesian theory](https://archive.org/details/bayesiantheory00bern_963) (Reprint ed.). Chichester \[u.a.\]: Wiley. pp. [209](https://archive.org/details/bayesiantheory00bern_963/page/n224), 366. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-49464-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-49464-5).
36. O'Hagan, A. (1994) *Kendall's Advanced Theory of statistics, Vol 2B, Bayesian Inference*, Edward Arnold. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-340-52922-9](https://en.wikipedia.org/wiki/Special:BookSources/0-340-52922-9) (Section 5.40)
37. ^   , p. 35)
38. [UIUC, Lecture 21. The Multivariate Normal Distribution](http://www.math.uiuc.edu/~r-ash/Stat/StatLec21-25.pdf), 21.6:"Individually Gaussian Versus Jointly Gaussian".
39. Edward L. Melnick and Aaron Tenenbein, "Misspecifications of the Normal Distribution", *[The American Statistician](https://en.wikipedia.org/wiki/The_American_Statistician)*, volume 36, number 4 November 1982, pages 372–373
40. ["Kullback Leibler (KL) Distance of Two Normal (Gaussian) Probability Distributions"](http://www.allisons.org/ll/MML/KL/Normal/). *Allisons.org*. December 5, 2007. Retrieved March 3, 2017.
41. Jordan, Michael I. (February 8, 2010). ["Stat260: Bayesian Modeling and Inference: The Conjugate Prior for the Normal Distribution"](http://www.cs.berkeley.edu/~jordan/courses/260-spring10/lectures/lecture5.pdf) (PDF).
42. 43. ["Expectation of the maximum of gaussian random variables"](https://math.stackexchange.com/a/89147). *Mathematics Stack Exchange*. Retrieved April 7, 2024.
44. ["Normal Approximation to Poisson Distribution"](http://www.stat.ucla.edu/~dinov/courses_students.dir/Applets.dir/NormalApprox2PoissonApplet.html). *Stat.ucla.edu*. Retrieved March 3, 2017.
45. , p. 27)
46. Weisstein, Eric W. ["Normal Product Distribution"](http://mathworld.wolfram.com/NormalProductDistribution.html). *MathWorld*. wolfram.com.
47. Lukacs, Eugene (1942). ["A Characterization of the Normal Distribution"](https://doi.org/10.1214%2Faoms%2F1177731647). *[The Annals of Mathematical Statistics](https://en.wikipedia.org/wiki/The_Annals_of_Mathematical_Statistics)*. **13** (1): 91–3. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/aoms/1177731647](https://doi.org/10.1214%2Faoms%2F1177731647). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0003-4851](https://search.worldcat.org/issn/0003-4851). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2236166](https://www.jstor.org/stable/2236166).
48. Basu, D.; Laha, R. G. (1954). "On Some Characterizations of the Normal Distribution". *[Sankhyā](https://en.wikipedia.org/wiki/Sankhy%C4%81_(journal))*. **13** (4): 359–62. [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0036-4452](https://search.worldcat.org/issn/0036-4452). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [25048183](https://www.jstor.org/stable/25048183).
49. Lehmann, E. L. (1997). *Testing Statistical Hypotheses* (2nd ed.). Springer. p. 199. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-94919-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-94919-2).
50. , \[2.3.6\])
51. , Theorem 3.5)
52. ^   
53. Quine, M.P. (1993). ["On three characterisations of the normal distribution"](http://www.math.uni.wroc.pl/~pms/publicationsArticle.php?nr=14.2&nrA=8&ppB=257&ppE=263). *Probability and Mathematical Statistics*. **14** (2): 257–263.
54. John, S (1982). "The three parameter two-piece normal family of distributions and its fitting". *Communications in Statistics – Theory and Methods*. **11** (8): 879–885. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/03610928208828279](https://doi.org/10.1080%2F03610928208828279).
55. ^   , p. 127)
56. , p. 130)
57. , p. 133)
58. ^   , p. 23.
59. , p. 1.
60. Larkoski, Andrew J. (2023). [Quantum Mechanics: A Mathematical Introduction](https://books.google.com/books?id=iKmnEAAAQBAJ&dq=normal%20distribution&pg=PA120). United Kingdom: Cambridge University Press. pp. 120–121. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-009-12222-1](https://en.wikipedia.org/wiki/Special:BookSources/978-1-009-12222-1). Retrieved May 30, 2025.
61. 62. Jaynes, Edwin T. (2003). [Probability Theory: The Logic of Science](https://books.google.com/books?id=tTN4HuUNXjgC&pg=PA592). Cambridge University Press. pp. 592–593. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780521592710](https://en.wikipedia.org/wiki/Special:BookSources/9780521592710).
63. Oosterbaan, Roland J. (1994). ["Chapter 6: Frequency and Regression Analysis of Hydrologic Data"](http://www.waterlog.info/pdf/freqtxt.pdf) (PDF). In Ritzema, Henk P. (ed.). *Drainage Principles and Applications, Publication 16* (second revised ed.). Wageningen, The Netherlands: International Institute for Land Reclamation and Improvement (ILRI). pp. 175–224. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-90-70754-33-4](https://en.wikipedia.org/wiki/Special:BookSources/978-90-70754-33-4).
64. Why Most Published Research Findings Are False, John P. A. Ioannidis, 2005
65. Wichura, Michael J. (1988). "Algorithm AS241: The Percentage Points of the Normal Distribution". *Applied Statistics*. **37** (3): 477–84. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2347330](https://doi.org/10.2307%2F2347330). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2347330](https://www.jstor.org/stable/2347330).
66. , Equation (26.48))
67. 68. 69. 70. 71. 72. , section 2)
73. 74. , p. 85)
75. , p. 74)
76. De Moivre, Abraham (1733), Corollary I – see , p. 77)
77. , [p. 76](https://archive.org/details/historyofstatist00stig/page/76/mode/2up?q=%22de+moivre%22))
78. , section 177)
79. , section 179)
80. , Problem III)
81. , p. 189)
82. , section 177)
83. , p. 144)
84. , p. 243)
85. , p. 244)
86. Jaynes, Edwin J.; *Probability Theory: The Logic of Science*, [Ch. 7](http://www-biba.inrialpes.fr/Jaynes/cc07s.pdf).
87. Peirce, Charles S. (c. 1909 MS), *[Collected Papers](https://en.wikipedia.org/wiki/Charles_Sanders_Peirce_bibliography#CP)* v. 6, paragraph 327.
88. .
89. ["Earliest Uses... (Entry Standard Normal Curve)"](http://jeff560.tripod.com/s.html).
90. introduces the terms *standard normal curve* [(p. 33)](https://archive.org/details/in.ernet.dli.2015.263186/page/n41/mode/2up?q=%22standard+normal+curve%22) and *standard normal distribution* [(p. 69)](https://archive.org/details/in.ernet.dli.2015.263186/page/n77/mode/2up?q=%22standard+normal+distribution%22).
91. explicitly defines the *standard normal distribution* [(p. 112)](https://archive.org/details/introductiontoth0000alex/page/112/mode/2up?q=%22standard+normal+distribution%22).
92. Sun, Jingchao; Kong, Maiying; Pal, Subhadip (June 22, 2021). ["The Modified-Half-Normal distribution: Properties and an efficient sampling scheme"](https://www.tandfonline.com/doi/abs/10.1080/03610926.2021.1934700?journalCode=lsta20). *Communications in Statistics – Theory and Methods*. **52** (5): 1591–1613. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/03610926.2021.1934700](https://doi.org/10.1080%2F03610926.2021.1934700). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0361-0926](https://search.worldcat.org/issn/0361-0926). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [237919587](https://api.semanticscholar.org/CorpusID:237919587).

### Sources

- Aldrich, John; Miller, Jeff. ["Earliest Uses of Symbols in Probability and Statistics"](http://jeff560.tripod.com/stat.html).
- Aldrich, John; Miller, Jeff. ["Earliest Known Uses of Some of the Words of Mathematics"](http://jeff560.tripod.com/mathword.html). In particular, the entries for ["bell-shaped and bell curve"](http://jeff560.tripod.com/b.html), ["normal (distribution)"](http://jeff560.tripod.com/n.html), ["Gaussian"](http://jeff560.tripod.com/g.html), and ["Error, law of error, theory of errors, etc."](http://jeff560.tripod.com/e.html).
- [Amari, Shun'ichi](https://en.wikipedia.org/wiki/Shun%27ichi_Amari); Nagaoka, Hiroshi (2000). *Methods of Information Geometry*. Oxford University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8218-0531-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8218-0531-2).
- [Bernardo, José M.](https://en.wikipedia.org/wiki/Jos%C3%A9-Miguel_Bernardo); [Smith, Adrian F. M.](https://en.wikipedia.org/wiki/Adrian_Smith_(statistician) "Adrian Smith (statistician)") (2000). *Bayesian Theory*. Wiley. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-49464-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-49464-5).
- Bryc, Wlodzimierz (1995). [The Normal Distribution: Characterizations with Applications](https://books.google.com/books?id=tyXjBwAAQBAJ). Springer-Verlag. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-97990-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-97990-8).
- [Casella, George](https://en.wikipedia.org/wiki/George_Casella); [Berger, Roger L.](https://en.wikipedia.org/wiki/Roger_Lee_Berger) (2001). *Statistical Inference* (2nd ed.). Duxbury. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-534-24312-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-534-24312-8).
- Cody, William J. (1969). ["Rational Chebyshev Approximations for the Error Function"](https://en.wikipedia.org/wiki/Error_function#cite_note-5). *Mathematics of Computation*. **23** (107): 631–638. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1969MaCom..23..631C](https://ui.adsabs.harvard.edu/abs/1969MaCom..23..631C). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1090/S0025-5718-1969-0247736-4](https://doi.org/10.1090%2FS0025-5718-1969-0247736-4).
- [Cover, Thomas M.](https://en.wikipedia.org/wiki/Thomas_M._Cover); [Thomas, Joy A.](https://en.wikipedia.org/wiki/Joy_A._Thomas) (2006). [Elements of Information Theory](https://books.google.com/books?id=VWq5GG6ycxMC). John Wiley and Sons. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780471241959](https://en.wikipedia.org/wiki/Special:BookSources/9780471241959).
- Dia, Yaya D. (2023). ["Approximate Incomplete Integrals, Application to Complementary Error Function"](https://ssrn.com/abstract=4487559). *SSRN*. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2139/ssrn.4487559](https://doi.org/10.2139%2Fssrn.4487559). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [259689086](https://api.semanticscholar.org/CorpusID:259689086).
- [de Moivre, Abraham](https://en.wikipedia.org/wiki/Abraham_de_Moivre) (2000) \[First published 1738\]. [*The Doctrine of Chances*](https://en.wikipedia.org/wiki/The_Doctrine_of_Chances). American Mathematical Society. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8218-2103-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8218-2103-9).
- Du, Y.; Fan, B.; Wei, B. (2022). "An improved exact sampling algorithm for the standard normal distribution". *Computational Statistics*. **37** (2): 721–737. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2008.03855](https://arxiv.org/abs/2008.03855). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s00180-021-01136-w](https://doi.org/10.1007%2Fs00180-021-01136-w).
- Fan, Jianqing (1991). ["On the optimal rates of convergence for nonparametric deconvolution problems"](https://doi.org/10.1214%2Faos%2F1176348248). *The Annals of Statistics*. **19** (3): 1257–1272. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/aos/1176348248](https://doi.org/10.1214%2Faos%2F1176348248). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2241949](https://www.jstor.org/stable/2241949).
- [Galton, Francis](https://en.wikipedia.org/wiki/Francis_Galton) (1889). [Natural Inheritance](http://galton.org/books/natural-inheritance/pdf/galton-nat-inh-1up-clean.pdf) (PDF). London, UK: Richard Clay and Sons.
- [Galambos, Janos](https://en.wikipedia.org/wiki/Janos_Galambos); Simonelli, Italo (2004). [Products of Random Variables: Applications to Problems of Physics and to Arithmetical Functions](https://archive.org/details/productsofrandom00gala). Marcel Dekker, Inc. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8247-5402-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8247-5402-0).
- [Gauss, Carolo Friderico](https://en.wikipedia.org/wiki/Carl_Friedrich_Gauss) (1809). [Theoria motvs corporvm coelestivm in sectionibvs conicis Solem ambientivm](https://archive.org/details/theoriamotuscor00gausgoog) \[*Theory of the Motion of the Heavenly Bodies Moving about the Sun in Conic Sections*\] (in Latin). Hambvrgi, Svmtibvs F. Perthes et I. H. Besser. [English translation](https://books.google.com/books?id=1TIAAAAAQAAJ).
- [Gould, Stephen Jay](https://en.wikipedia.org/wiki/Stephen_Jay_Gould) (1981). [*The Mismeasure of Man*](https://en.wikipedia.org/wiki/The_Mismeasure_of_Man) (first ed.). W. W. Norton. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-393-01489-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-393-01489-1).
- Halperin, Max; Hartley, Herman O.; Hoel, Paul G. (1965). "Recommended Standards for Statistical Symbols and Notation. COPSS Committee on Symbols and Notation". *The American Statistician*. **19** (3): 12–14. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2681417](https://doi.org/10.2307%2F2681417). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2681417](https://www.jstor.org/stable/2681417).
- Hart, John F.; et al. (1968). *Computer Approximations*. New York, NY: John Wiley & Sons, Inc. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-88275-642-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-88275-642-4).
- ["Normal Distribution"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society), 2001 \[1994\]
- [Herrnstein, Richard J.](https://en.wikipedia.org/wiki/Richard_J._Herrnstein); [Murray, Charles](https://en.wikipedia.org/wiki/Charles_Murray_(political_scientist) "Charles Murray (political scientist)") (1994). [*The Bell Curve: Intelligence and Class Structure in American Life*](https://en.wikipedia.org/wiki/The_Bell_Curve). [Free Press](https://en.wikipedia.org/wiki/Free_Press_(publisher) "Free Press (publisher)"). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-02-914673-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-02-914673-6).
- Hoel, Paul G. (1947). [Introduction To Mathematical Statistics](https://archive.org/details/in.ernet.dli.2015.263186/page/n1/mode/2up). New York: Wiley.
- [Huxley, Julian S.](https://en.wikipedia.org/wiki/Julian_S._Huxley) (1972) \[First published 1932\]. *Problems of Relative Growth*. London. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-486-61114-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-486-61114-3). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [476909537](https://search.worldcat.org/oclc/476909537).
- [Johnson, Norman L.](https://en.wikipedia.org/wiki/Norman_Lloyd_Johnson); [Kotz, Samuel](https://en.wikipedia.org/wiki/Samuel_Kotz); Balakrishnan, Narayanaswamy (1994). *Continuous Univariate Distributions, Volume 1*. Wiley. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-58495-7](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-58495-7).
- Johnson, Norman L.; Kotz, Samuel; Balakrishnan, Narayanaswamy (1995). *Continuous Univariate Distributions, Volume 2*. Wiley. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-58494-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-58494-0).
- Karney, C. F. F. (2016). "Sampling exactly from the normal distribution". *ACM Transactions on Mathematical Software*. **42** (1): 3:1–14. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1303.6257](https://arxiv.org/abs/1303.6257). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1145/2710016](https://doi.org/10.1145%2F2710016). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [14252035](https://api.semanticscholar.org/CorpusID:14252035).
- Kinderman, Albert J.; Monahan, John F. (1977). ["Computer Generation of Random Variables Using the Ratio of Uniform Deviates"](https://doi.org/10.1145%2F355744.355750). *ACM Transactions on Mathematical Software*. **3** (3): 257–260. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1145/355744.355750](https://doi.org/10.1145%2F355744.355750). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [12884505](https://api.semanticscholar.org/CorpusID:12884505).
- Krishnamoorthy, Kalimuthu (2006). *Handbook of Statistical Distributions with Applications*. Chapman & Hall/CRC. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-58488-635-8](https://en.wikipedia.org/wiki/Special:BookSources/978-1-58488-635-8).
- [Kruskal, William H.](https://en.wikipedia.org/wiki/William_H._Kruskal); Stigler, Stephen M. (1997). Spencer, Bruce D. (ed.). *Normative Terminology: 'Normal' in Statistics and Elsewhere*. Statistics and Public Policy. Oxford University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-19-852341-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-19-852341-3).
- [Laplace, Pierre-Simon de](https://en.wikipedia.org/wiki/Pierre-Simon_Laplace) (1774). ["Mémoire sur la probabilité des causes par les événements"](http://gallica.bnf.fr/ark:/12148/bpt6k77596b/f32). *Mémoires de l'Académie Royale des Sciences de Paris (Savants étrangers), Tome 6*: 621–656. Translated by Stephen M. Stigler in *Statistical Science* **1** (3), 1986: [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2245476](https://www.jstor.org/stable/2245476).
- Laplace, Pierre-Simon (1812). [Théorie analytique des probabilités](https://archive.org/details/thorieanalytiqu00laplgoog) \[*[Analytical theory of probabilities](https://en.wikipedia.org/wiki/Analytical_theory_of_probabilities)*\]. Paris, Ve. Courcier.
- [Le Cam, Lucien](https://en.wikipedia.org/wiki/Lucien_Le_Cam); [Lo Yang, Grace](https://en.wikipedia.org/wiki/Grace_Yang) (2000). *Asymptotics in Statistics: Some Basic Concepts* (second ed.). Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-95036-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-95036-5).
- Leva, Joseph L. (1992). ["A fast normal random number generator"](https://web.archive.org/web/20100716035328/http://saluc.engr.uconn.edu/refs/crypto/rng/leva92afast.pdf) (PDF). *ACM Transactions on Mathematical Software*. **18** (4): 449–453. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.544.5806](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.544.5806). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1145/138351.138364](https://doi.org/10.1145%2F138351.138364). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [15802663](https://api.semanticscholar.org/CorpusID:15802663). Archived from [the original](http://saluc.engr.uconn.edu/refs/crypto/rng/leva92afast.pdf) (PDF) on July 16, 2010.
- [Lexis, Wilhelm](https://en.wikipedia.org/wiki/Wilhelm_Lexis) (1878). "Sur la durée normale de la vie humaine et sur la théorie de la stabilité des rapports statistiques". *Annales de Démographie Internationale*. **II**. Paris: 447–462.
- Lukacs, Eugene; King, Edgar P. (1954). ["A Property of Normal Distribution"](https://doi.org/10.1214%2Faoms%2F1177728796). *The Annals of Mathematical Statistics*. **25** (2): 389–394. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/aoms/1177728796](https://doi.org/10.1214%2Faoms%2F1177728796). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2236741](https://www.jstor.org/stable/2236741).
- McPherson, Glen (1990). [Statistics in Scientific Investigation: Its Basis, Application and Interpretation](https://archive.org/details/statisticsinscie0000mcph). Springer-Verlag. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-97137-7](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-97137-7).
- [Marsaglia, George](https://en.wikipedia.org/wiki/George_Marsaglia); Tsang, Wai Wan (2000). ["The Ziggurat Method for Generating Random Variables"](https://doi.org/10.18637%2Fjss.v005.i08). *Journal of Statistical Software*. **5** (8). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.18637/jss.v005.i08](https://doi.org/10.18637%2Fjss.v005.i08).
- Marsaglia, George (2004). ["Evaluating the Normal Distribution"](https://doi.org/10.18637%2Fjss.v011.i04). *Journal of Statistical Software*. **11** (4). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.18637/jss.v011.i04](https://doi.org/10.18637%2Fjss.v011.i04).
- [Maxwell, James Clerk](https://en.wikipedia.org/wiki/James_Clerk_Maxwell) (1860). ["V. Illustrations of the dynamical theory of gases. — Part I: On the motions and collisions of perfectly elastic spheres"](https://books.google.com/books?id=-YU7AQAAMAAJ&pg=PA19). *Philosophical Magazine*. Series 4. **19** (124): 19–32. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1860LEDPM..19...19M](https://ui.adsabs.harvard.edu/abs/1860LEDPM..19...19M). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/14786446008642818](https://doi.org/10.1080%2F14786446008642818).
- Monahan, J. F. (1985). ["Accuracy in random number generation"](https://doi.org/10.1090%2FS0025-5718-1985-0804945-X). *Mathematics of Computation*. **45** (172): 559–568. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1090/S0025-5718-1985-0804945-X](https://doi.org/10.1090%2FS0025-5718-1985-0804945-X).
- [Mood, Alexander McFarlane](https://en.wikipedia.org/wiki/Alexander_M._Mood) (1950). [Introduction to the Theory of Statistics](https://archive.org/details/introductiontoth0000alex/page/n5/mode/2up). New York: McGraw-Hill.
- Patel, Jagdish K.; Read, Campbell B. (1996). *Handbook of the Normal Distribution* (2nd ed.). CRC Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8247-9342-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8247-9342-5).
- [Pearson, Karl](https://en.wikipedia.org/wiki/Karl_Pearson) (1901). ["On Lines and Planes of Closest Fit to Systems of Points in Space"](http://stat.smmu.edu.cn/history/pearson1901.pdf) (PDF). *[Philosophical Magazine](https://en.wikipedia.org/wiki/Philosophical_Magazine)*. 6. **2** (11): 559–572. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/14786440109462720](https://doi.org/10.1080%2F14786440109462720). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [125037489](https://api.semanticscholar.org/CorpusID:125037489).
- [Pearson, Karl](https://en.wikipedia.org/wiki/Karl_Pearson) (1905). ["'Das Fehlergesetz und seine Verallgemeinerungen durch Fechner und Pearson'. A rejoinder"](https://zenodo.org/record/1449456). *Biometrika*. **4** (1): 169–212. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2331536](https://doi.org/10.2307%2F2331536). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2331536](https://www.jstor.org/stable/2331536).
- Pearson, Karl (1920). ["Notes on the History of Correlation"](https://zenodo.org/record/1431597). *Biometrika*. **13** (1): 25–45. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1093/biomet/13.1.25](https://doi.org/10.1093%2Fbiomet%2F13.1.25). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2331722](https://www.jstor.org/stable/2331722).
- Rohrbasser, Jean-Marc; Véron, Jacques (2003). ["Wilhelm Lexis: The Normal Length of Life as an Expression of the "Nature of Things""](http://www.persee.fr/web/revues/home/prescript/article/pop_1634-2941_2003_num_58_3_18444). *Population*. **58** (3): 303–322. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3917/pope.303.0303](https://doi.org/10.3917%2Fpope.303.0303).
- Shore, H (1982). "Simple Approximations for the Inverse Cumulative Function, the Density Function and the Loss Integral of the Normal Distribution". *Journal of the Royal Statistical Society. Series C (Applied Statistics)*. **31** (2): 108–114. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2347972](https://doi.org/10.2307%2F2347972). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2347972](https://www.jstor.org/stable/2347972).
- Shore, H (2005). "Accurate RMM-Based Approximations for the CDF of the Normal Distribution". *Communications in Statistics – Theory and Methods*. **34** (3): 507–513. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1081/sta-200052102](https://doi.org/10.1081%2Fsta-200052102). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [122148043](https://api.semanticscholar.org/CorpusID:122148043).
- Shore, H (2011). "Response Modeling Methodology". *WIREs Comput Stat*. **3** (4): 357–372. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1002/wics.151](https://doi.org/10.1002%2Fwics.151). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [62021374](https://api.semanticscholar.org/CorpusID:62021374).
- Shore, H (2012). "Estimating Response Modeling Methodology Models". *WIREs Comput Stat*. **4** (3): 323–333. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1002/wics.1199](https://doi.org/10.1002%2Fwics.1199). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [122366147](https://api.semanticscholar.org/CorpusID:122366147).
- [Stigler, Stephen M.](https://en.wikipedia.org/wiki/Stephen_Stigler) (1978). ["Mathematical Statistics in the Early States"](https://doi.org/10.1214%2Faos%2F1176344123). *The Annals of Statistics*. **6** (2): 239–265. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/aos/1176344123](https://doi.org/10.1214%2Faos%2F1176344123). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2958876](https://www.jstor.org/stable/2958876).
- Stigler, Stephen M. (1982). "A Modest Proposal: A New Standard for the Normal". *The American Statistician*. **36** (2): 137–138. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2684031](https://doi.org/10.2307%2F2684031). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2684031](https://www.jstor.org/stable/2684031).
- Stigler, Stephen M. (1986). [The History of Statistics: The Measurement of Uncertainty before 1900](https://archive.org/details/historyofstatist00stig). Harvard University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-674-40340-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-674-40340-6).
- Stigler, Stephen M. (1999). *Statistics on the Table*. Harvard University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-674-83601-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-674-83601-3).
- Walker, Helen M. (1985). ["De Moivre on the Law of Normal Probability"](http://www.york.ac.uk/depts/maths/histstat/demoivre.pdf) (PDF). In Smith, David Eugene (ed.). *A Source Book in Mathematics*. Dover. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-486-64690-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-486-64690-9).
- [Wallace, C. S.](https://en.wikipedia.org/wiki/Chris_Wallace_(computer_scientist) "Chris Wallace (computer scientist)") (1996). ["Fast pseudo-random generators for normal and exponential variates"](https://doi.org/10.1145%2F225545.225554). *ACM Transactions on Mathematical Software*. **22** (1): 119–127. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1145/225545.225554](https://doi.org/10.1145%2F225545.225554). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [18514848](https://api.semanticscholar.org/CorpusID:18514848).
- [Weisstein, Eric W.](https://en.wikipedia.org/wiki/Eric_W._Weisstein) ["Normal Distribution"](http://mathworld.wolfram.com/NormalDistribution.html). [MathWorld](https://en.wikipedia.org/wiki/MathWorld).
- West, Graeme (2009). ["Better Approximations to Cumulative Normal Functions"](https://web.archive.org/web/20120229202051/https://wilmott.com/pdfs/090721_west.pdf) (PDF). *Wilmott Magazine*: 70–76. Archived from [the original](https://wilmott.com/pdfs/090721_west.pdf) (PDF) on February 29, 2012.
- Zelen, Marvin; Severo, Norman C. (1972) \[First published 1964\]. [Probability Functions (chapter 26)](http://www.math.sfu.ca/~cbm/aands/page_931.htm). *[Handbook of mathematical functions with formulas, graphs, and mathematical tables](https://en.wikipedia.org/wiki/Abramowitz_and_Stegun)*, by [Abramowitz, M.](https://en.wikipedia.org/wiki/Milton_Abramowitz); and [Stegun, I. A.](https://en.wikipedia.org/wiki/Irene_A._Stegun): National Bureau of Standards. New York, NY: Dover. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-486-61272-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-486-61272-0).

## External links

- ["Normal distribution"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society), 2001 \[1994\]
- [Normal distribution calculator](https://www.hackmath.net/en/calculator/normal-distribution)
