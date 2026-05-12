[[probability-statistics.base]]

> Source: [[Moment Generating Function|Moment-generating function]]
> License: Wikipedia content is available under CC BY-SA 4.0.

In [probability theory](https://en.wikipedia.org/wiki/Probability_theory) and [statistics](https://en.wikipedia.org/wiki/Statistics), the **moment-generating function** of a real-valued [random variable](https://en.wikipedia.org/wiki/Random_variable) is an alternative specification of its [probability distribution](https://en.wikipedia.org/wiki/Probability_distribution). Thus, it provides the basis of an alternative route to analytical results compared with working directly with [[Probability Density Function|probability density functions]] or [[Cumulative Distribution Function|cumulative distribution functions]]. There are particularly simple results for the moment-generating functions of distributions defined by the weighted sums of random variables. However, not all random variables have moment-generating functions.

As its name implies, the moment-[generating function](https://en.wikipedia.org/wiki/Generating_function) can be used to compute a distribution’s [moments](https://en.wikipedia.org/wiki/Moment_(mathematics) "Moment (mathematics)"): the n-th moment about 0 is the n-th derivative of the moment-generating function, evaluated at 0.

In addition to univariate real-valued distributions, moment-generating functions can also be defined for vector- or matrix-valued random variables, and can even be extended to more general cases.

The moment-generating function of a real-valued distribution does not always exist, unlike the [characteristic function](https://en.wikipedia.org/wiki/Characteristic_function_(probability_theory) "Characteristic function (probability theory)"). There are relations between the behavior of the moment-generating function of a distribution and properties of the distribution, such as the existence of moments.

## Definition

Let $X$ be a [random variable](https://en.wikipedia.org/wiki/Random_variable) with [[Cumulative Distribution Function|CDF]] $F_{X}$. The moment generating function (mgf) of $X$ (or $F_{X}$), denoted by $M_{X}(t)$, is

$$
M_{X}(t)=\operatorname {E} \left[e^{tX}\right]
$$

provided this [expectation](https://en.wikipedia.org/wiki/Expected_value) exists for $t$ in some open [neighborhood](https://en.wikipedia.org/wiki/Neighborhood_(mathematics)) of 0. That is, there is an $h>0$ such that for all $t$ satisfying $-h<t<h$, $\operatorname {E} \left[e^{tX}\right]$ exists. If the expectation does not exist in an open neighborhood of 0, we say that the moment generating function does not exist.

In other words, the moment-generating function of X is the [expectation](https://en.wikipedia.org/wiki/Expected_value) of the random variable $e^{tX}$. More generally, when $\mathbf {X} =(X_{1},\ldots ,X_{n})^{\mathrm {T} }$, an $n$-dimensional [random vector](https://en.wikipedia.org/wiki/Random_vector), and $\mathbf {t}$ is a fixed vector, one uses $\mathbf {t} \cdot \mathbf {X} =\mathbf {t} ^{\mathrm {T} }\mathbf {X}$ instead of $tX$: 

$$
M_{\mathbf {X} }(\mathbf {t} ):=\operatorname {E} \left[e^{\mathbf {t} ^{\mathrm {T} }\mathbf {X} }\right].
$$

$M_{X}(0)$ always exists and is equal to 1. However, a key problem with moment-generating functions is that moments and the moment-generating function may not exist, as the integrals need not converge absolutely. By contrast, the [characteristic function](https://en.wikipedia.org/wiki/Characteristic_function_(probability_theory) "Characteristic function (probability theory)") or Fourier transform always exists (because it is the integral of a bounded function on a space of finite [measure](https://en.wikipedia.org/wiki/Measure_(mathematics) "Measure (mathematics)")), and for some purposes may be used instead.

The moment-generating function is so named because it can be used to find the moments of the distribution. The series expansion of $e^{tX}$ is

$$
e^{tX}=1+tX+{\frac {t^{2}X^{2}}{2!}}+{\frac {t^{3}X^{3}}{3!}}+\cdots +{\frac {t^{n}X^{n}}{n!}}+\cdots .
$$

Hence, 

$$
{\begin{aligned}M_{X}(t)&=\operatorname {E} [e^{tX}]\\[1ex]&=1+t\operatorname {E} [X]+{\frac {t^{2}\operatorname {E} [X^{2}]}{2!}}+{\frac {t^{3}\operatorname {E} [X^{3}]}{3!}}+\cdots +{\frac {t^{n}\operatorname {E} [X^{n}]}{n!}}+\cdots \\[1ex]&=1+tm_{1}+{\frac {t^{2}m_{2}}{2!}}+{\frac {t^{3}m_{3}}{3!}}+\cdots +{\frac {t^{n}m_{n}}{n!}}+\cdots ,\end{aligned}}
$$

where $m_{n}$ is the $n$-th [moment](https://en.wikipedia.org/wiki/Moment_(mathematics) "Moment (mathematics)"). Differentiating $M_{X}(t)$ $i$ times with respect to $t$ and setting $t=0$, we obtain the $i$-th moment about the origin, $m_{i}$.

If $X$ is a continuous random variable, the following relation between its moment-generating function $M_{X}(t)$ and the [two-sided Laplace transform](https://en.wikipedia.org/wiki/Two-sided_Laplace_transform) of its probability density function $f_{X}(x)$ holds:

$$
M_{X}(t)={\mathcal {L}}\{f_{X}\}(-t),
$$

since the PDF's two-sided Laplace transform is given as

$$
{\mathcal {L}}\{f_{X}\}(s)=\int _{-\infty }^{\infty }e^{-sx}f_{X}(x)\,dx,
$$

and the moment-generating function's definition expands (by the [law of the unconscious statistician](https://en.wikipedia.org/wiki/Law_of_the_unconscious_statistician)) to 

$$
M_{X}(t)=\operatorname {E} \left[e^{tX}\right]=\int _{-\infty }^{\infty }e^{tx}f_{X}(x)\,dx.
$$

## Examples

Here are some examples of the moment-generating function and the characteristic function for comparison. It can be seen that the characteristic function is a [Wick rotation](https://en.wikipedia.org/wiki/Wick_rotation) of the moment-generating function $M_{X}(t)$ when the latter exists.

<table class="wikitable" style="padding-left:1.5em;">

Distribution
Moment-generating function $M_{X}(t)$
Characteristic function $\varphi (t)$

&#10;
[Degenerate](https://en.wikipedia.org/wiki/Degenerate_distribution) $\delta _{a}$
$e^{ta}$
$e^{ita}$

[Bernoulli](https://en.wikipedia.org/wiki/Bernoulli_distribution) $P(X=1)=p$
$1-p+pe^{t}$
$1-p+pe^{it}$

[Binomial](https://en.wikipedia.org/wiki/Binomial_distribution) $B(n,p)$
$\left(1-p+pe^{t}\right)^{n}$
$\left(1-p+pe^{it}\right)^{n}$

[Geometric](https://en.wikipedia.org/wiki/Geometric_distribution) $(1-p)^{k}\,p$
${\frac {p}{1-(1-p)e^{t}}},~t<-\ln(1-p)$
${\frac {p}{1-(1-p)\,e^{it}}}$

[Negative binomial](https://en.wikipedia.org/wiki/Negative_binomial_distribution) $\operatorname {NB} (r,p)$
$\left({\frac {p}{1-e^{t}+pe^{t}}}\right)^{r},~t<-\ln(1-p)$
$\left({\frac {p}{1-e^{it}+pe^{it}}}\right)^{r}$

[Poisson](https://en.wikipedia.org/wiki/Poisson_distribution) $\operatorname {Pois} (\lambda )$
$e^{\lambda (e^{t}-1)}$
$e^{\lambda (e^{it}-1)}$

[Uniform (continuous)](https://en.wikipedia.org/wiki/Uniform_distribution_(continuous)) $\operatorname {U} (a,b)$
${\frac {e^{tb}-e^{ta}}{t(b-a)}}$
${\frac {e^{itb}-e^{ita}}{it(b-a)}}$

[Uniform (discrete)](https://en.wikipedia.org/wiki/Discrete_uniform_distribution) $\operatorname {DU} (a,b)$
${\frac {e^{at}-e^{(b+1)t}}{(b-a+1)(1-e^{t})}}$
${\frac {e^{ait}-e^{(b+1)it}}{(b-a+1)(1-e^{it})}}$

[Laplace](https://en.wikipedia.org/wiki/Laplace_distribution) $L(\mu ,b)$
${\frac {e^{t\mu }}{1-b^{2}t^{2}}},~|t|<1/b$
${\frac {e^{it\mu }}{1+b^{2}t^{2}}}$

[Normal](https://en.wikipedia.org/wiki/Normal_distribution) $N(\mu ,\sigma ^{2})$
$e^{t\mu +\sigma ^{2}t^{2}/2}$
$e^{it\mu -\sigma ^{2}t^{2}/2}$

[Chi-squared](https://en.wikipedia.org/wiki/Chi-squared_distribution) $\chi _{k}^{2}$
${\left(1-2t\right)}^{-k/2},~t<1/2$
${\left(1-2it\right)}^{-{k}/{2}}$

[Noncentral chi-squared](https://en.wikipedia.org/wiki/Noncentral_chi-squared_distribution) $\chi _{k}^{2}(\lambda )$
$e^{\lambda t/(1-2t)}{\left(1-2t\right)}^{-k/2}$
$e^{i\lambda t/(1-2it)}{\left(1-2it\right)}^{-k/2}$

[Gamma](https://en.wikipedia.org/wiki/Gamma_distribution) $\Gamma (k,{\tfrac {1}{\theta }})$
${\left(1-t\theta \right)}^{-k},~t<{\tfrac {1}{\theta }}$
${\left(1-it\theta \right)}^{-k}$

[Exponential](https://en.wikipedia.org/wiki/Exponential_distribution) $\operatorname {Exp} (\lambda )$
$\left(1-t\lambda ^{-1}\right)^{-1},~t<\lambda$
$\left(1-it\lambda ^{-1}\right)^{-1}$

[Beta](https://en.wikipedia.org/wiki/Beta_distribution)
$1+\sum _{k=1}^{\infty }\left(\prod _{r=0}^{k-1}{\frac {\alpha +r}{\alpha +\beta +r}}\right){\frac {t^{k}}{k!}}$
${}_{1}F_{1}(\alpha ;\alpha +\beta ;i\,t)\!$<br />
(see [Confluent hypergeometric function](https://en.wikipedia.org/wiki/Confluent_hypergeometric_function))

[[Multivariate Normal Distribution|Multivariate normal]] $N(\mathbf {\mu } ,\mathbf {\Sigma } )$
$\exp \left[\mathbf {t} ^{\mathrm {T} }\left({\boldsymbol {\mu }}+{\tfrac {1}{2}}{\boldsymbol {\Sigma }}\mathbf {t} \right)\right]$
$\exp \left[\mathbf {t} ^{\mathrm {T} }\left(i{\boldsymbol {\mu }}-{\tfrac {1}{2}}{\boldsymbol {\Sigma }}\mathbf {t} \right)\right]$

[Cauchy](https://en.wikipedia.org/wiki/Cauchy_distribution) $\operatorname {Cauchy} (\mu ,\theta )$
[Does not exist](https://en.wikipedia.org/wiki/Indeterminate_form)
$e^{it\mu -\theta |t|}$

[Multivariate Cauchy](https://en.wikipedia.org/wiki/Multivariate_Cauchy_distribution)
<p>$\operatorname {MultiCauchy} (\mu ,\Sigma )$</p>
Does not exist
$\exp \left(i\mathbf {t} ^{\mathrm {T} }{\boldsymbol {\mu }}-{\sqrt {\mathbf {t} ^{\mathrm {T} }{\boldsymbol {\Sigma }}\mathbf {t} }}\right)$

</table>

## Calculation

The moment-generating function is the expectation of a function of the random variable, it can be written as:

- For a discrete [probability mass function](https://en.wikipedia.org/wiki/Probability_mass_function), $M_{X}(t)=\sum _{i=0}^{\infty }e^{tx_{i}}\,p_{i}$
- For a continuous [[Probability Density Function]], $M_{X}(t)=\int _{-\infty }^{\infty }e^{tx}f(x)\,dx$
- In the general case: $M_{X}(t)=\int _{-\infty }^{\infty }e^{tx}\,dF(x)$, using the [Riemann–Stieltjes integral](https://en.wikipedia.org/wiki/Riemann%E2%80%93Stieltjes_integral), and where $F$ is the [[Cumulative Distribution Function]]. This is simply the [Laplace-Stieltjes transform](https://en.wikipedia.org/wiki/Laplace-Stieltjes_transform) of $F$, but with the sign of the argument reversed.

Note that for the case where $X$ has a continuous [[Probability Density Function]] $f(x)$, $M_{X}(-t)$ is the [two-sided Laplace transform](https://en.wikipedia.org/wiki/Two-sided_Laplace_transform) of $f(x)$.

$$
{\begin{aligned}M_{X}(t)&=\int _{-\infty }^{\infty }e^{tx}f(x)\,dx\\[1ex]&=\int _{-\infty }^{\infty }\left(1+tx+{\frac {t^{2}x^{2}}{2!}}+\cdots +{\frac {t^{n}x^{n}}{n!}}+\cdots \right)f(x)\,dx\\[1ex]&=1+tm_{1}+{\frac {t^{2}m_{2}}{2!}}+\cdots +{\frac {t^{n}m_{n}}{n!}}+\cdots ,\end{aligned}}
$$

where $m_{n}$ is the $n$th [moment](https://en.wikipedia.org/wiki/Moment_(mathematics) "Moment (mathematics)").

### Linear transformations of random variables

If random variable $X$ has moment generating function $M_{X}(t)$, then $\alpha X+\beta$ has moment generating function $M_{\alpha X+\beta }(t)=e^{\beta t}M_{X}(\alpha t)$

$$
M_{\alpha X+\beta }(t)=\operatorname {E} \left[e^{(\alpha X+\beta )t}\right]=e^{\beta t}\operatorname {E} \left[e^{\alpha Xt}\right]=e^{\beta t}M_{X}(\alpha t)
$$

### Linear combination of independent random variables

If $S_{n}=\sum _{i=1}^{n}a_{i}X_{i}$, where the *X*<sub>*i*</sub> are independent random variables and the *a*<sub>*i*</sub> are constants, then the probability density function for *S*<sub>*n*</sub> is the [convolution](https://en.wikipedia.org/wiki/Convolution) of the probability density functions of each of the *X*<sub>*i*</sub>, and the moment-generating function for *S*<sub>*n*</sub> is given by

$$
M_{S_{n}}(t)=M_{X_{1}}(a_{1}t)M_{X_{2}}(a_{2}t)\cdots M_{X_{n}}(a_{n}t)\,.
$$

### Vector-valued random variables

For [vector-valued random variables](https://en.wikipedia.org/wiki/Random_vector) $\mathbf {X}$ with [real](https://en.wikipedia.org/wiki/Real_number) components, the moment-generating function is given by

$$
M_{X}(\mathbf {t} )=\operatorname {E} \left[e^{\langle \mathbf {t} ,\mathbf {X} \rangle }\right]
$$

where $\mathbf {t}$ is a vector and $\langle \cdot ,\cdot \rangle$ is the [dot product](https://en.wikipedia.org/wiki/Dot_product).

## Important properties

Moment generating functions are positive and [log-convex](https://en.wikipedia.org/wiki/Logarithmically_convex_function),<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup> with *M*(0) = 1.

An important property of the moment-generating function is that it uniquely determines the distribution. In other words, if $X$ and $Y$ are two random variables and for all values of t,

$$
M_{X}(t)=M_{Y}(t),
$$

 then 

$$
F_{X}(x)=F_{Y}(x)
$$

for all values of x (or equivalently X and Y have the same distribution). This statement is not equivalent to the statement "if two distributions have the same moments, then they are identical at all points." This is because in some cases, the moments exist and yet the moment-generating function does not, because the limit

$$
\lim _{n\to \infty }\sum _{i=0}^{n}{\frac {t^{i}m_{i}}{i!}}
$$

may not exist. The [log-normal distribution](https://en.wikipedia.org/wiki/Log-normal_distribution) is an example of when this occurs: its moments are $\operatorname {E} [X^{n}]=e^{n\mu +n^{2}\sigma ^{2}/2}$ and are all finite but its moment generating function $\operatorname {E} \left[e^{tX}\right]$ is not defined for any positive t as the integral diverges and so not in a neighbourhood of 0; there are other distributions with the same moments.

### Calculations of moments

The moment-generating function is so called because if it exists on an open interval around *t* = 0, then it is the [exponential generating function](https://en.wikipedia.org/wiki/Exponential_generating_function) of the [moments](https://en.wikipedia.org/wiki/Moment_(mathematics) "Moment (mathematics)") of the [probability distribution](https://en.wikipedia.org/wiki/Probability_distribution):

$$
m_{n}=\operatorname {E} \left[X^{n}\right]=M_{X}^{(n)}(0)=\left.{\frac {d^{n}M_{X}}{dt^{n}}}\right|_{t=0}.
$$

That is, with n being a nonnegative integer, the n-th moment about 0 is the n-th derivative of the moment generating function, evaluated at *t* = 0.

## Other properties

[Jensen's inequality](https://en.wikipedia.org/wiki/Jensen%27s_inequality) provides a simple lower bound on the moment-generating function: 

$$
M_{X}(t)\geq e^{\mu t},
$$

 where $\mu$ is the mean of X.

The moment-generating function can be used in conjunction with [Markov's inequality](https://en.wikipedia.org/wiki/Markov%27s_inequality) to bound the upper tail of a real random variable X. This statement is also called the [Chernoff bound](https://en.wikipedia.org/wiki/Chernoff_bound). Since $x\mapsto e^{xt}$ is monotonically increasing for $t>0$, we have 

$$
\Pr(X\geq a)=\Pr(e^{tX}\geq e^{ta})\leq e^{-at}\operatorname {E} \left[e^{tX}\right]=e^{-at}M_{X}(t)
$$

 for any $t>0$ and any a, provided $M_{X}(t)$ exists. For example, when X is a standard normal distribution and $a>0$, we can choose $t=a$ and recall that $M_{X}(t)=e^{t^{2}/2}$. This gives $\Pr(X\geq a)\leq e^{-a^{2}/2}$, which is within a factor of 1+*a* of the exact value.

Various lemmas, such as [Hoeffding's lemma](https://en.wikipedia.org/wiki/Hoeffding%27s_lemma) or [Bennett's inequality](https://en.wikipedia.org/wiki/Bennett%27s_inequality) provide bounds on the moment-generating function in the case of a zero-mean, bounded random variable.

When $X$ is non-negative, the moment generating function gives a simple, useful bound on the moments: 

$$
\operatorname {E} [X^{m}]\leq \left({\frac {m}{te}}\right)^{m}M_{X}(t),
$$

 For any $X,m\geq 0$ and $t>0$.

This follows from the inequality $1+x\leq e^{x}$ into which we can substitute $x'=tx/m-1$ implies $tx/m\leq e^{tx/m-1}$ for any $x,t,m\in \mathbb {R}$. Now, if $t>0$ and $x,m\geq 0$, this can be rearranged to $x^{m}\leq (m/(te))^{m}e^{tx}$. Taking the expectation on both sides gives the bound on $\operatorname {E} [X^{m}]$ in terms of $\operatorname {E} [e^{tX}]$.

As an example, consider $X\sim {\text{Chi-Squared}}$ with $k$ degrees of freedom. Then from the [examples](#Examples) $M_{X}(t)=(1-2t)^{-k/2}$. Picking $t=m/(2m+k)$ and substituting into the bound: 

$$
\operatorname {E} [X^{m}]\leq {\left(1+2m/k\right)}^{k/2}e^{-m}{\left(k+2m\right)}^{m}.
$$

 We know that [in this case](https://en.wikipedia.org/wiki/Chi-square_distribution#Noncentral_moments) the correct bound is $\operatorname {E} [X^{m}]\leq 2^{m}\Gamma (m+k/2)/\Gamma (k/2)$. To compare the bounds, we can consider the asymptotics for large $k$. Here the moment-generating function bound is $k^{m}(1+m^{2}/k+O(1/k^{2}))$, where the real bound is $k^{m}(1+(m^{2}-m)/k+O(1/k^{2}))$. The moment-generating function bound is thus very strong in this case.

## Relation to other functions

Related to the moment-generating function are a number of other [transforms](https://en.wikipedia.org/wiki/Integral_transform) that are common in probability theory:

[Characteristic function](https://en.wikipedia.org/wiki/Characteristic_function_(probability_theory) "Characteristic function (probability theory)")  
The [characteristic function](https://en.wikipedia.org/wiki/Characteristic_function_(probability_theory) "Characteristic function (probability theory)") $\varphi _{X}(t)$ is related to the moment-generating function via $\varphi _{X}(t)=M_{iX}(t)=M_{X}(it):$ the characteristic function is the moment-generating function of *iX* or the moment generating function of *X* evaluated on the imaginary axis. This function can also be viewed as the [Fourier transform](https://en.wikipedia.org/wiki/Fourier_transform) of the [[Probability Density Function]], which can therefore be deduced from it by inverse Fourier transform.

[Cumulant-generating function](https://en.wikipedia.org/wiki/Cumulant-generating_function)  
The [cumulant-generating function](https://en.wikipedia.org/wiki/Cumulant-generating_function) is defined as the logarithm of the moment-generating function; some instead define the cumulant-generating function as the logarithm of the [characteristic function](https://en.wikipedia.org/wiki/Characteristic_function_(probability_theory) "Characteristic function (probability theory)"), while others call this latter the *second* cumulant-generating function.

[Probability-generating function](https://en.wikipedia.org/wiki/Probability-generating_function)  
The [probability-generating function](https://en.wikipedia.org/wiki/Probability-generating_function) is defined as $G(z)=\operatorname {E} \left[z^{X}\right].$ This immediately implies that $G(e^{t})=\operatorname {E} \left[e^{tX}\right]=M_{X}(t).$

## See also

- [Characteristic function (probability theory)](https://en.wikipedia.org/wiki/Characteristic_function_(probability_theory) "Characteristic function (probability theory)")
- [Factorial moment generating function](https://en.wikipedia.org/wiki/Factorial_moment_generating_function)
- [Rate function](https://en.wikipedia.org/wiki/Rate_function)
- [Hamburger moment problem](https://en.wikipedia.org/wiki/Hamburger_moment_problem)

## References

### Citations

1.  [Casella, George](https://en.wikipedia.org/wiki/George_Casella); [Berger, Roger L.](https://en.wikipedia.org/wiki/Roger_Lee_Berger) (1990). *Statistical Inference*. Wadsworth & Brooks/Cole. p. 61. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-534-11958-1](https://en.wikipedia.org/wiki/Special:BookSources/0-534-11958-1).
2.  [Bulmer, M. G.](https://en.wikipedia.org/wiki/Michael_Bulmer) (1979). *Principles of Statistics*. Dover. pp. 75–79. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-486-63760-3](https://en.wikipedia.org/wiki/Special:BookSources/0-486-63760-3).
3.  Kotz et al.<sup>\[*[full citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citing_sources#What_information_to_include)*\]</sup> p. 37 using 1 as the number of degree of freedom to recover the Cauchy distribution
4.  [Heyde, CC.](https://en.wikipedia.org/wiki/Chris_Heyde) (1963), "On a Property of the Lognormal Distribution", *Journal of the Royal Statistical Society, Series B*, vol. 25, no. 2, pp. 392–393, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-1-4419-5823-5_6](https://doi.org/10.1007%2F978-1-4419-5823-5_6), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4419-5822-8](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4419-5822-8) `{{`[`citation`](https://en.wikipedia.org/wiki/Template:Citation)`}}`: ISBN / Date incompatibility ([help](https://en.wikipedia.org/wiki/Help:CS1_errors#invalid_isbn_date))CS1 maint: work parameter with ISBN ([link](https://en.wikipedia.org/wiki/Category:CS1_maint:_work_parameter_with_ISBN))

### Sources

- Casella, George; Berger, Roger (2002). *Statistical Inference* (2nd ed.). Thomson Learning. pp. 59–68. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-534-24312-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-534-24312-8).

