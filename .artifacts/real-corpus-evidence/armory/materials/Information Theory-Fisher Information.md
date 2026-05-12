[[information-theory.base]]

> Source: [[Fisher Information]]
> License: Wikipedia content is available under CC BY-SA 4.0.

In [mathematical statistics](https://en.wikipedia.org/wiki/Mathematical_statistics), the **Fisher information** is a way of measuring the amount of [information](https://en.wikipedia.org/wiki/Information) that an observable [random variable](https://en.wikipedia.org/wiki/Random_variable) *X* carries about an unknown parameter *θ* of a distribution that models *X*. Formally, it is the [variance](https://en.wikipedia.org/wiki/Variance) of the [score](https://en.wikipedia.org/wiki/Score_(statistics)), or the [expected value](https://en.wikipedia.org/wiki/Expected_value) of the [observed information](https://en.wikipedia.org/wiki/Observed_information).

The role of the Fisher information in the asymptotic theory of [[Maximum Likelihood Estimation|maximum-likelihood estimation]] was emphasized and explored by the statistician [Sir Ronald Fisher](https://en.wikipedia.org/wiki/Ronald_Fisher) (following some initial results by [Francis Ysidro Edgeworth](https://en.wikipedia.org/wiki/Francis_Ysidro_Edgeworth)). The Fisher information matrix is used to calculate the [covariance matrices](https://en.wikipedia.org/wiki/Covariance_matrices) associated with [maximum-likelihood](https://en.wikipedia.org/wiki/Maximum_likelihood) [estimates](https://en.wikipedia.org/wiki/Estimator). It can also be used in the formulation of test statistics, such as the [Wald test](https://en.wikipedia.org/wiki/Wald_test).

In [Bayesian statistics](https://en.wikipedia.org/wiki/Bayesian_statistics), the Fisher information plays a role in the derivation of non-informative [prior distributions](https://en.wikipedia.org/wiki/Prior_distribution) according to [Jeffreys' rule](https://en.wikipedia.org/wiki/Jeffreys_prior). It also appears as the large-sample covariance of the [posterior distribution](https://en.wikipedia.org/wiki/Posterior_distribution), provided that the prior is sufficiently smooth (a result known as [Bernstein–von Mises theorem](https://en.wikipedia.org/wiki/Bernstein%E2%80%93von_Mises_theorem), which was anticipated by [Laplace](https://en.wikipedia.org/wiki/Laplace) for [exponential families](https://en.wikipedia.org/wiki/Exponential_families)). The same result is used when approximating the posterior with [Laplace's approximation](https://en.wikipedia.org/wiki/Laplace%27s_approximation), where the Fisher information appears as the covariance of the fitted Gaussian.

Statistical systems of a scientific nature (physical, biological, etc.) whose likelihood functions obey [shift invariance](https://en.wikipedia.org/wiki/Shift-invariant_system) have been shown to obey maximum Fisher information. The level of the maximum depends upon the nature of the system constraints.

## Definition

The Fisher information is a way of measuring the amount of information that an observable [random variable](https://en.wikipedia.org/wiki/Random_variable) $X$ carries about an unknown [parameter](https://en.wikipedia.org/wiki/Parameter) $\theta$ upon which the probability of $X$ depends. Let $f(X;\theta )$ be the [[Probability Density Function]] (or [probability mass function](https://en.wikipedia.org/wiki/Probability_mass_function)) for $X$ conditioned on the value of $\theta$. It describes the probability that we observe a given outcome of $X$, *given* a known value of $\theta$. If $f$ is sharply peaked with respect to changes in $\theta$, it is easy to indicate the "correct" value of $\theta$ from the data, or equivalently, that the data $X$ provides a lot of information about the parameter $\theta$. If $f$ is flat and spread-out, then it would take many samples of $X$ to estimate the actual "true" value of $\theta$ that *would* be obtained using the entire population being sampled. This suggests studying some kind of variance with respect to $\theta$.

Formally, the [partial derivative](https://en.wikipedia.org/wiki/Partial_derivative) with respect to $\theta$ of the [natural logarithm](https://en.wikipedia.org/wiki/Natural_logarithm) of the [likelihood function](https://en.wikipedia.org/wiki/Likelihood_function) is called the *[score](https://en.wikipedia.org/wiki/Score_(statistics))*. Under certain regularity conditions, if $\theta$ is the true parameter (i.e. $X$ is actually distributed as $f(X;\theta )$), it can be shown that the [expected value](https://en.wikipedia.org/wiki/Expected_value) (the first [moment](https://en.wikipedia.org/wiki/Moment_(mathematics) "Moment (mathematics)")) of the score, evaluated at the true parameter value $\theta$, is 0:

${\begin{aligned}\operatorname {E} \left[\left.{\frac {\partial }{\partial \theta }}\log f(X;\theta )\,\,\right|\,\,\theta \right]={}&\int _{\mathbb {R} }{\frac {{\frac {\partial }{\partial \theta }}f(x;\theta )}{f(x;\theta )}}f(x;\theta )\,dx\\[6pt]={}&{\frac {\partial }{\partial \theta }}\int _{\mathbb {R} }f(x;\theta )\,dx\\[6pt]={}&{\frac {\partial }{\partial \theta }}1\\[6pt]={}&0.\end{aligned}}$

The **Fisher information** is defined to be the [variance](https://en.wikipedia.org/wiki/Variance) of the score:

${\mathcal {I}}(\theta )=\operatorname {E} \left[\left.\left({\frac {\partial }{\partial \theta }}\log f(X;\theta )\right)^{2}\,\,\right|\,\,\theta \right]=\int _{\mathbb {R} }\left({\frac {\partial }{\partial \theta }}\log f(x;\theta )\right)^{2}f(x;\theta )\,dx,$

Note that ${\mathcal {I}}(\theta )\geq 0$. A random variable carrying high Fisher information implies that the absolute value of the score is often high. The Fisher information is not a function of a particular observation, as the random variable *X* has been averaged out.

If log *f*(*x*; *θ*) is twice differentiable with respect to *θ*, and under certain additional regularity conditions, then the Fisher information may also be written as

${\mathcal {I}}(\theta )=-\operatorname {E} \left[\left.{\frac {\partial ^{2}}{\partial \theta ^{2}}}\log f(X;\theta )\,\,\right|\,\,\theta \right],$

<table class="mw-collapsible mw-archivedtalk mw-collapsed" role="presentation" style="color:inherit; background: transparent; text-align: left; border: 1px solid Silver; margin: 0.2em auto auto; width:100%; clear: both; padding: 1px;">

Derivation of the second form

&#10;
<p>Begin by taking the second derivative of $\log f(X;\theta )$:</p>
${\frac {\partial ^{2}}{\partial \theta ^{2}}}\log f(X;\theta )={\frac {{\frac {\partial ^{2}}{\partial \theta ^{2}}}f(X;\theta )}{f(X;\theta )}}-\left({\frac {{\frac {\partial }{\partial \theta }}f(X;\theta )}{f(X;\theta )}}\right)^{2}={\frac {{\frac {\partial ^{2}}{\partial \theta ^{2}}}f(X;\theta )}{f(X;\theta )}}-\left({\frac {\partial }{\partial \theta }}\log f(X;\theta )\right)^{2}$
<p>Now take the expectation value of each term on both sides.</p>
${\begin{aligned}\operatorname {E} \left[\left.{\frac {\partial ^{2}}{\partial \theta ^{2}}}\log f(X;\theta )\,\,\right|\,\,\theta \right]&=\operatorname {E} \left[\left.{\frac {{\frac {\partial ^{2}}{\partial \theta ^{2}}}f(X;\theta )}{f(X;\theta )}}\,\,\right|\,\,\theta \right]-\operatorname {E} \left[\left.\left({\frac {\partial }{\partial \theta }}\log f(X;\theta )\right)^{2}\,\,\right|\,\,\theta \right]\\\operatorname {E} \left[\left.{\frac {\partial ^{2}}{\partial \theta ^{2}}}\log f(X;\theta )\,\,\right|\,\,\theta \right]&=\operatorname {E} \left[\left.{\frac {{\frac {\partial ^{2}}{\partial \theta ^{2}}}f(X;\theta )}{f(X;\theta )}}\,\,\right|\,\,\theta \right]-{\mathcal {I}}(\theta )\\{\mathcal {I}}(\theta )&=-\operatorname {E} \left[\left.{\frac {\partial ^{2}}{\partial \theta ^{2}}}\log f(X;\theta )\,\,\right|\,\,\theta \right]+\operatorname {E} \left[\left.{\frac {{\frac {\partial ^{2}}{\partial \theta ^{2}}}f(X;\theta )}{f(X;\theta )}}\,\,\right|\,\,\theta \right]\end{aligned}}$
<p>Next, we show that the last term is equal to 0.</p>
$\operatorname {E} \left[\left.{\frac {{\frac {\partial ^{2}}{\partial \theta ^{2}}}f(X;\theta )}{f(X;\theta )}}\,\,\right|\,\,\theta \right]=\int _{\mathbb {R} }f(x;\theta ){\frac {{\frac {\partial ^{2}}{\partial \theta ^{2}}}f(x;\theta )}{f(x;\theta )}}\,dx={\frac {\partial ^{2}}{\partial \theta ^{2}}}\int _{\mathbb {R} }f(x;\theta )\,dx={\frac {\partial ^{2}}{\partial \theta ^{2}}}(1)=0$
<p>Therefore,</p>
${\mathcal {I}}(\theta )=-\operatorname {E} \left[\left.{\frac {\partial ^{2}}{\partial \theta ^{2}}}\log f(X;\theta )\,\,\right|\,\,\theta \right]$

</table>

Thus, the Fisher information may be seen as the curvature of the [support curve](https://en.wikipedia.org/wiki/Support_curve) (the graph of the log-likelihood). Near the [maximum likelihood](https://en.wikipedia.org/wiki/Maximum_likelihood) estimate, low Fisher information indicates that the maximum appears to be "blunt", that is, there are many points in the neighborhood that provide a similar log-likelihood. Conversely, a high Fisher information indicates that the maximum is "sharp".

### Regularity conditions

The regularity conditions are as follows:

1.  The partial derivative of *f*(*X*; *θ*) with respect to *θ* exists [almost everywhere](https://en.wikipedia.org/wiki/Almost_everywhere). (It can fail to exist on a null set, as long as this set does not depend on *θ*.)
2.  The integral of *f*(*X*; *θ*) can be differentiated under the integral sign with respect to *θ*.
3.  The [support](https://en.wikipedia.org/wiki/Support_(mathematics) "Support (mathematics)") of *f*(*X*; *θ*) does not depend on *θ*.

If *θ* is a vector then the regularity conditions must hold for every component of *θ*. It is easy to find an example of a density that does not satisfy the regularity conditions: The density of a Uniform(0, *θ*) variable fails to satisfy conditions 1 and 3. In this case, even though the Fisher information can be computed from the definition, it will not have the properties it is typically assumed to have.

### In terms of likelihood

Because the [likelihood](https://en.wikipedia.org/wiki/Likelihood) of *θ* given *X* is always proportional to the probability *f*(*X*; *θ*), their logarithms necessarily differ by a constant that is independent of *θ*, and the derivatives of these logarithms with respect to *θ* are necessarily equal. Thus one can substitute in a log-likelihood *l*(*θ*; *X*) instead of log *f*(*X*; *θ*) in the definitions of Fisher Information.

### Samples of any size

The value *X* can represent a single sample drawn from a single distribution or can represent a collection of samples drawn from a collection of distributions. If there are *n* samples and the corresponding *n* distributions are [statistically independent](https://en.wikipedia.org/wiki/Statistically_independent) then the Fisher information will necessarily be the sum of the single-sample Fisher information values, one for each single sample from its distribution. In particular, if the *n* distributions are [independent and identically distributed](https://en.wikipedia.org/wiki/I.i.d.) then the Fisher information will necessarily be *n* times the Fisher information of a single sample from the common distribution. Stated in other words, the Fisher Information of i.i.d. observations of a sample of size *n* from a population is equal to the product of *n* and the Fisher Information of a single observation from the same population.

### Informal derivation of the Cramér–Rao bound

The [Cramér–Rao bound](https://en.wikipedia.org/wiki/Cram%C3%A9r%E2%80%93Rao_bound) states that the inverse of the Fisher information is a lower bound on the variance of any [unbiased estimator](https://en.wikipedia.org/wiki/Unbiased_estimator) of *θ*.  and  provide the following method of deriving the [Cramér–Rao bound](https://en.wikipedia.org/wiki/Cram%C3%A9r%E2%80%93Rao_bound), a result which describes use of the Fisher information.

Informally, we begin by considering an [unbiased estimator](https://en.wikipedia.org/wiki/Unbiased_estimator) ${\hat {\theta }}(X)$. Mathematically, "unbiased" means that

$\operatorname {E} \left[\left.{\hat {\theta }}(X)-\theta \,\,\right|\,\,\theta \right]=\int \left({\hat {\theta }}(x)-\theta \right)\,f(x;\theta )\,dx=0{\text{ regardless of the value of }}\theta .$

This expression is zero independent of *θ*, so its partial derivative with respect to *θ* must also be zero. By the [product rule](https://en.wikipedia.org/wiki/Product_rule), this partial derivative is also equal to

$0={\frac {\partial }{\partial \theta }}\int \left({\hat {\theta }}(x)-\theta \right)\,f(x;\theta )\,dx=\int \left({\hat {\theta }}(x)-\theta \right){\frac {\partial f}{\partial \theta }}\,dx-\int f\,dx.$

For each *θ*, the likelihood function is a probability density function, and therefore $\int f\,dx=1$. By using the [[Chain Rule]] on the partial derivative of $\log f$ and then dividing and multiplying by $f(x;\theta )$, one can verify that

${\frac {\partial f}{\partial \theta }}=f\,{\frac {\partial \log f}{\partial \theta }}.$

Using these two facts in the above, we get

$\int \left({\hat {\theta }}-\theta \right)f\,{\frac {\partial \log f}{\partial \theta }}\,dx=1.$

Factoring the integrand gives

$\int \left(\left({\hat {\theta }}-\theta \right){\sqrt {f}}\right)\left({\sqrt {f}}\,{\frac {\partial \log f}{\partial \theta }}\right)\,dx=1.$

Squaring the expression in the integral, the [Cauchy–Schwarz inequality](https://en.wikipedia.org/wiki/Cauchy%E2%80%93Schwarz_inequality) yields

$1={\biggl (}\int \left[\left({\hat {\theta }}-\theta \right){\sqrt {f}}\right]\cdot \left[{\sqrt {f}}\,{\frac {\partial \log f}{\partial \theta }}\right]\,dx{\biggr )}^{2}\leq \left[\int \left({\hat {\theta }}-\theta \right)^{2}f\,dx\right]\cdot \left[\int \left({\frac {\partial \log f}{\partial \theta }}\right)^{2}f\,dx\right].$

The second bracketed factor is defined to be the Fisher Information, while the first bracketed factor is the [mean-squared error](https://en.wikipedia.org/wiki/Mean-squared_error) (MSE) of the estimator ${\hat {\theta }}$. Since the estimator is unbiased, its MSE equals its variance. By rearranging, the inequality tells us that

$\operatorname {Var} ({\hat {\theta }})\geq {\frac {1}{{\mathcal {I}}\left(\theta \right)}}.$

In other words, the precision to which we can estimate *θ* is fundamentally limited by the Fisher information of the likelihood function.

Alternatively, the same conclusion can be obtained directly from the [Cauchy–Schwarz inequality for random variables](https://en.wikipedia.org/wiki/Cauchy%E2%80%93Schwarz_inequality), $|\operatorname {Cov} (A,B)|^{2}\leq \operatorname {Var} (A)\operatorname {Var} (B)$, applied to the random variables ${\hat {\theta }}(X)$ and $\partial _{\theta }\log f(X;\theta )$, and observing that for unbiased estimators we have

$$
\operatorname {Cov} [{\hat {\theta }}(X),\partial _{\theta }\log f(X;\theta )]=\int {\hat {\theta }}(x)\,\partial _{\theta }f(x;\theta )\,dx=\partial _{\theta }\operatorname {E} [{\hat {\theta }}]=1.
$$

## Examples

### Single-parameter Bernoulli experiment

A [Bernoulli trial](https://en.wikipedia.org/wiki/Bernoulli_trial) is a random variable with two possible outcomes, 0 and 1, with 1 having a probability of *θ*. The outcome can be thought of as determined by the toss of a biased coin, with the probability of heads (1) being *θ* and the probability of tails (0) being 1 − *θ*.

Let *X* be a Bernoulli trial of one sample from the distribution. The Fisher information contained in *X* may be calculated to be:

${\begin{aligned}{\mathcal {I}}(\theta )&=-\operatorname {E} \left[\left.{\frac {\partial ^{2}}{\partial \theta ^{2}}}\log \left(\theta ^{X}(1-\theta )^{1-X}\right)\right|\theta \right]\\[5pt]&=-\operatorname {E} \left[\left.{\frac {\partial ^{2}}{\partial \theta ^{2}}}\left(X\log \theta +(1-X)\log(1-\theta )\right)\,\,\right|\,\,\theta \right]\\[5pt]&=\operatorname {E} \left[\left.{\frac {X}{\theta ^{2}}}+{\frac {1-X}{(1-\theta )^{2}}}\,\,\right|\,\,\theta \right]\\[5pt]&={\frac {\theta }{\theta ^{2}}}+{\frac {1-\theta }{(1-\theta )^{2}}}\\[5pt]&={\frac {1}{\theta (1-\theta )}}.\end{aligned}}$

Because Fisher information is additive, the Fisher information contained in *n* independent [Bernoulli trials](https://en.wikipedia.org/wiki/Bernoulli_trial) is therefore

${\mathcal {I}}(\theta )={\frac {n}{\theta (1-\theta )}}.$

If $x_{i}$ is one of the $2^{n}$ possible outcomes of *n* independent Bernoulli trials and $x_{ij}$ is the *j* th outcome of the *i* th trial, then the probability of $x_{i}$ is given by

$p(x_{i},\theta )=\prod _{j=0}^{n}\theta ^{x_{ij}}(1-\theta )^{x_{ij}}$

The sample mean of the *i* th trial is $\mu _{i}=(1/n)\sum _{j=1}^{n}x_{ij}$. The expected value of the sample mean (over the [sampling distribution](https://en.wikipedia.org/wiki/Sampling_distribution)) is

$E(\mu )=\sum _{x_{i}}\mu _{i}\,p(x_{i},\theta )=\theta ,$

where the sum is over all $2^{n}$ possible trial outcomes. The expected value of the square of the sample mean is

$E(\mu ^{2})=\sum _{x_{i}}\mu _{i}^{2}\,p(x_{i},\theta )={\frac {(1+(n-1)\theta )\theta }{n}}$

so the variance in the value of the mean is

$E(\mu ^{2})-E(\mu )^{2}={\frac {\theta (1-\theta )}{n}}$

It is seen that the Fisher information is the reciprocal of the [variance](https://en.wikipedia.org/wiki/Variance) of the mean number of successes in *n* [Bernoulli trials](https://en.wikipedia.org/wiki/Bernoulli_trial). This is generally true. In this case, the Cramér–Rao bound is an equality.

### Estimate *θ* from *X* ~ Bern (√*θ*)

As another toy example consider a random variable $X$ with possible outcomes 0 and 1, with probabilities $p_{0}=1-{\sqrt {\theta }}$ and $p_{1}={\sqrt {\theta }}$, respectively, for some $\theta \in [0,1]$. Our goal is estimating $\theta$ from observations of $X$.

The Fisher information reads in this case

$$
{\begin{aligned}{\mathcal {I}}(\theta )&=\mathrm {E} \left[\left({\frac {\partial }{\partial \theta }}\log f(X;\theta )\right)^{2}{\Bigg |}\,\theta \right]\\&=(1-{\sqrt {\theta }})\left({\frac {-1}{2{\sqrt {\theta }}(1-{\sqrt {\theta }})}}\right)^{2}+{\sqrt {\theta }}\left({\frac {1}{2\theta }}\right)^{2}\\&={\frac {1}{4\theta }}\left({\frac {1}{1-{\sqrt {\theta }}}}+{\frac {1}{\sqrt {\theta }}}\right)\end{aligned}}.
$$

This expression can also be derived directly from the change of reparametrization formula given below. More generally, for any sufficiently regular function $f$ such that $f(\theta )\in [0,1]$, the Fisher information to retrieve $\theta$ from $X\sim \operatorname {Bern} (f(\theta ))$ is similarly computed to be

$$
{\mathcal {I}}(\theta )=f'(\theta )^{2}\left({\frac {1}{1-f(\theta )}}+{\frac {1}{f(\theta )}}\right).
$$

## Matrix form

When there are *N* parameters, so that *θ* is an *N* × 1 [vector](https://en.wikipedia.org/wiki/Column_vector) $\theta ={\begin{bmatrix}\theta _{1}&\theta _{2}&\dots &\theta _{N}\end{bmatrix}}^{\textsf {T}},$ the Fisher information takes the form of an *N* × *N* [matrix](https://en.wikipedia.org/wiki/Matrix_(mathematics) "Matrix (mathematics)"). This matrix is called the **Fisher information matrix** (FIM) and has typical element

${\bigl [}{\mathcal {I}}(\theta ){\bigr ]}_{i,j}=\operatorname {E} \left[\left.\left({\frac {\partial }{\partial \theta _{i}}}\log f(X;\theta )\right)\left({\frac {\partial }{\partial \theta _{j}}}\log f(X;\theta )\right)\,\,\right|\,\,\theta \right].$

The FIM is a *N* × *N* [positive semidefinite matrix](https://en.wikipedia.org/wiki/Positive_semidefinite_matrix). If it is positive definite, then it defines a [Riemannian metric](https://en.wikipedia.org/wiki/Riemannian_metric) on the *N*-[dimensional](https://en.wikipedia.org/wiki/Dimension) [parameter space](https://en.wikipedia.org/wiki/Parameter_space). The topic [information geometry](https://en.wikipedia.org/wiki/Information_geometry) uses this to connect Fisher information to [differential geometry](https://en.wikipedia.org/wiki/Differential_geometry), and in that context, this metric is known as the [Fisher information metric](https://en.wikipedia.org/wiki/Fisher_information_metric).

Under certain regularity conditions, the Fisher information matrix may also be written as

${\bigl [}{\mathcal {I}}(\theta ){\bigr ]}_{i,j}=-\operatorname {E} \left[\left.{\frac {\partial ^{2}}{\partial \theta _{i}\,\partial \theta _{j}}}\log f(X;\theta )\,\,\right|\,\,\theta \right]\,.$

The result is interesting in several ways:

- It is equal to minus the *expected* [[Hessian Matrix|Hessian]] of the [relative entropy](https://en.wikipedia.org/wiki/Relative_entropy).
- It can be used as a Riemannian metric for defining Fisher-Rao geometry when it is positive-definite.
- It can be understood as a metric induced from the [Euclidean metric](https://en.wikipedia.org/wiki/Euclidean_metric), after appropriate change of variable.
- In its complex-valued form, it is the [Fubini–Study metric](https://en.wikipedia.org/wiki/Fubini%E2%80%93Study_metric).
- It is the key part of the proof of [Wilks' theorem](https://en.wikipedia.org/wiki/Wilks%27_theorem), which allows confidence region estimates for [[Maximum Likelihood Estimation]] (for those conditions for which it applies) without needing the [Likelihood Principle](https://en.wikipedia.org/wiki/Likelihood_Principle).
- In cases where the analytical calculations of the FIM above are difficult, it is possible to form an average of easy [[Monte Carlo Method|Monte Carlo]] estimates of the [[Hessian Matrix|Hessian]] of the negative log-likelihood function as an estimate of the FIM. The estimates may be based on values of the negative log-likelihood function or the gradient of the negative log-likelihood function; no analytical calculation of the Hessian of the negative log-likelihood function is needed.

### Information orthogonal parameters

We say that two parameter component vectors *θ<sub>1</sub>* and *θ<sub>2</sub>* are information orthogonal if the Fisher information matrix is block diagonal, with these components in separate blocks. Orthogonal parameters are easy to deal with in the sense that their [maximum likelihood estimates](https://en.wikipedia.org/wiki/Maximum_likelihood) are asymptotically uncorrelated. When considering how to analyse a statistical model, the modeller is advised to invest some time searching for an orthogonal parametrization of the model, in particular when the parameter of interest is one-dimensional, but the [nuisance parameter](https://en.wikipedia.org/wiki/Nuisance_parameter) can have any dimension.

### Singular statistical model

If the Fisher information matrix is positive definite for all θ, then the corresponding [statistical model](https://en.wikipedia.org/wiki/Statistical_model) is said to be *regular*; otherwise, the statistical model is said to be *singular*. Examples of singular statistical models include the following: normal [mixtures](https://en.wikipedia.org/wiki/Mixture_model), binomial mixtures, multinomial mixtures, [Bayesian networks](https://en.wikipedia.org/wiki/Bayesian_network), [neural networks](https://en.wikipedia.org/wiki/Neural_network_(machine_learning) "Neural network (machine learning)"), [radial basis functions](https://en.wikipedia.org/wiki/Radial_basis_function), [[Hidden Markov Model|hidden Markov models]], [stochastic context-free grammars](https://en.wikipedia.org/wiki/Stochastic_context-free_grammar), reduced rank regressions, [Boltzmann machines](https://en.wikipedia.org/wiki/Boltzmann_machine).

In [machine learning](https://en.wikipedia.org/wiki/Machine_learning), if a statistical model is devised so that it extracts hidden structure from a random phenomenon, then it naturally becomes singular.

### Multivariate normal distribution

The FIM for a *N*-variate [[Multivariate Normal Distribution]], $\,X\sim N\left(\mu (\theta ),\,\Sigma (\theta )\right)$ has a special form. Let the *K*-dimensional vector of parameters be $\theta ={\begin{bmatrix}\theta _{1}&\dots &\theta _{K}\end{bmatrix}}^{\textsf {T}}$ and the vector of normal random variables be $X={\begin{bmatrix}X_{1}&\dots &X_{N}\end{bmatrix}}^{\textsf {T}}$. Assume that the mean values of these random variables are $\,\mu (\theta )={\begin{bmatrix}\mu _{1}(\theta )&\dots &\mu _{N}(\theta )\end{bmatrix}}^{\textsf {T}}$, and let $\,\Sigma (\theta )$ be the [covariance matrix](https://en.wikipedia.org/wiki/Covariance_matrix). Then, for $1\leq m,\,n\leq K$, the (*m*, *n*) entry of the FIM is:

${\mathcal {I}}_{m,n}={\frac {\partial \mu ^{\textsf {T}}}{\partial \theta _{m}}}\Sigma ^{-1}{\frac {\partial \mu }{\partial \theta _{n}}}+{\frac {1}{2}}\operatorname {tr} \left(\Sigma ^{-1}{\frac {\partial \Sigma }{\partial \theta _{m}}}\Sigma ^{-1}{\frac {\partial \Sigma }{\partial \theta _{n}}}\right),$

where $(\cdot )^{\textsf {T}}$ denotes the [transpose](https://en.wikipedia.org/wiki/Transpose) of a vector, $\operatorname {tr} (\cdot )$ denotes the [trace](https://en.wikipedia.org/wiki/Trace_(matrix)) of a [square matrix](https://en.wikipedia.org/wiki/Square_matrix), and:

${\begin{aligned}{\frac {\partial \mu }{\partial \theta _{m}}}&={\begin{bmatrix}{\dfrac {\partial \mu _{1}}{\partial \theta _{m}}}&{\dfrac {\partial \mu _{2}}{\partial \theta _{m}}}&\cdots &{\dfrac {\partial \mu _{N}}{\partial \theta _{m}}}\end{bmatrix}}^{\textsf {T}};\\[8pt]{\dfrac {\partial \Sigma }{\partial \theta _{m}}}&={\begin{bmatrix}{\dfrac {\partial \Sigma _{1,1}}{\partial \theta _{m}}}&{\dfrac {\partial \Sigma _{1,2}}{\partial \theta _{m}}}&\cdots &{\dfrac {\partial \Sigma _{1,N}}{\partial \theta _{m}}}\\[5pt]{\dfrac {\partial \Sigma _{2,1}}{\partial \theta _{m}}}&{\dfrac {\partial \Sigma _{2,2}}{\partial \theta _{m}}}&\cdots &{\dfrac {\partial \Sigma _{2,N}}{\partial \theta _{m}}}\\\vdots &\vdots &\ddots &\vdots \\{\dfrac {\partial \Sigma _{N,1}}{\partial \theta _{m}}}&{\dfrac {\partial \Sigma _{N,2}}{\partial \theta _{m}}}&\cdots &{\dfrac {\partial \Sigma _{N,N}}{\partial \theta _{m}}}\end{bmatrix}}.\end{aligned}}$

Note that a special, but very common, case is the one where $\Sigma (\theta )=\Sigma$, a constant. Then

${\mathcal {I}}_{m,n}={\frac {\partial \mu ^{\textsf {T}}}{\partial \theta _{m}}}\Sigma ^{-1}{\frac {\partial \mu }{\partial \theta _{n}}}.\$

In this case the Fisher information matrix may be identified with the coefficient matrix of the [normal equations](https://en.wikipedia.org/wiki/Normal_equations) of [least squares](https://en.wikipedia.org/wiki/Least_squares) [estimation theory](https://en.wikipedia.org/wiki/Estimation_theory).

Another special case occurs when the mean and covariance depend on two different vector parameters, say, *β* and *θ*. This is especially popular in the analysis of spatial data, which often uses a linear model with correlated residuals. In this case,

${\mathcal {I}}(\beta ,\theta )=\operatorname {diag} \left({\mathcal {I}}(\beta ),{\mathcal {I}}(\theta )\right)$

where

${\begin{aligned}{\mathcal {I}}{(\beta )_{m,n}}&={\frac {\partial \mu ^{\textsf {T}}}{\partial \beta _{m}}}\Sigma ^{-1}{\frac {\partial \mu }{\partial \beta _{n}}},\\[5pt]{\mathcal {I}}{(\theta )_{m,n}}&={\frac {1}{2}}\operatorname {tr} \left(\Sigma ^{-1}{\frac {\partial \Sigma }{\partial \theta _{m}}}{\Sigma ^{-1}}{\frac {\partial \Sigma }{\partial \theta _{n}}}\right)\end{aligned}}$

## Properties

### Chain rule

Similar to the [entropy](https://en.wikipedia.org/wiki/Entropy_(information_theory)#Further_properties "Entropy (information theory)") or [[Mutual Information]], the Fisher information also possesses a **chain rule** decomposition. In particular, if *X* and *Y* are jointly distributed random variables, it follows that:

${\mathcal {I}}_{X,Y}(\theta )={\mathcal {I}}_{X}(\theta )+{\mathcal {I}}_{Y\mid X}(\theta ),$

where ${\mathcal {I}}_{Y\mid X}(\theta )=\operatorname {E} _{X}\left[{\mathcal {I}}_{Y\mid X=x}(\theta )\right]$ and ${\mathcal {I}}_{Y\mid X=x}(\theta )$ is the Fisher information of *Y* relative to $\theta$ calculated with respect to the conditional density of *Y* given a specific value *X* = *x*.

As a special case, if the two random variables are [independent](https://en.wikipedia.org/wiki/Statistical_independence), the information yielded by the two random variables is the sum of the information from each random variable separately:

${\mathcal {I}}_{X,Y}(\theta )={\mathcal {I}}_{X}(\theta )+{\mathcal {I}}_{Y}(\theta ).$

Consequently, the information in a random sample of *n* [independent and identically distributed](https://en.wikipedia.org/wiki/Independent_and_identically_distributed_random_variables) observations is *n* times the information in a sample of size 1.

### *f*-divergence

Given a convex function $f:[0,\infty )\to (-\infty ,\infty ]$ that $f(x)$ is finite for all $x>0$, $f(1)=0$, and $f(0)=\lim _{t\to 0^{+}}f(t)$, (which could be infinite), it defines an *f*-divergence $D_{f}$. Then if $f$ is strictly convex at $1$, then locally at $\theta \in \Theta$, the Fisher information matrix is a metric, in the sense that

$$
(\delta \theta )^{T}I(\theta )(\delta \theta )={\frac {1}{f''(1)}}D_{f}(P_{\theta +\delta \theta }\parallel P_{\theta })
$$

where $P_{\theta }$ is the distribution parametrized by $\theta$. That is, it's the distribution with pdf $f(x;\theta )$.

In this form, it is clear that the Fisher information matrix is a Riemannian metric, and varies correctly under a change of variables. (see section on [Reparameterization](#Reparameterization).)

### Sufficient statistic

The information provided by a [sufficient statistic](https://en.wikipedia.org/wiki/Sufficiency_(statistics)) is the same as that of the sample *X*. This may be seen by using [Neyman's factorization criterion](https://en.wikipedia.org/wiki/Sufficient_statistic#Fisher–Neyman_factorization_theorem) for a sufficient statistic. If *T*(*X*) is sufficient for *θ*, then

$f(X;\theta )=g(T(X),\theta )h(X)$

for some functions *g* and *h*. The independence of *h*(*X*) from *θ* implies

${\frac {\partial }{\partial \theta }}\log \left[f(X;\theta )\right]={\frac {\partial }{\partial \theta }}\log \left[g(T(X);\theta )\right],$

and the equality of information then follows from the definition of Fisher information. More generally, if *T = t*(*X*) is a [statistic](https://en.wikipedia.org/wiki/Statistic), then

${\mathcal {I}}_{T}(\theta )\leq {\mathcal {I}}_{X}(\theta )$

with equality [if and only if](https://en.wikipedia.org/wiki/If_and_only_if) *T* is a [sufficient statistic](https://en.wikipedia.org/wiki/Sufficient_statistic).

### Reparameterization

The Fisher information depends on the parametrization of the problem. If *θ* and *η* are two scalar parametrizations of an estimation problem, and *θ* is a [continuously differentiable](https://en.wikipedia.org/wiki/Continuously_differentiable) function of *η*, then

${\mathcal {I}}_{\eta }(\eta )={\mathcal {I}}_{\theta }(\theta (\eta ))\left({\frac {d\theta }{d\eta }}\right)^{2}$

where ${\mathcal {I}}_{\eta }$ and ${\mathcal {I}}_{\theta }$ are the Fisher information measures of *η* and *θ*, respectively.

In the vector case, suppose ${\boldsymbol {\theta }}$ and ${\boldsymbol {\eta }}$ are *k*-vectors which parametrize an estimation problem, and suppose that ${\boldsymbol {\theta }}$ is a continuously differentiable function of ${\boldsymbol {\eta }}$, then,

${\mathcal {I}}_{\boldsymbol {\eta }}({\boldsymbol {\eta }})={\boldsymbol {J}}^{\textsf {T}}{\mathcal {I}}_{\boldsymbol {\theta }}({\boldsymbol {\theta }}({\boldsymbol {\eta }})){\boldsymbol {J}}$

where the (*i*, *j*)th element of the *k* × *k* [[Jacobian Matrix]] ${\boldsymbol {J}}$ is defined by

$J_{ij}={\frac {\partial \theta _{i}}{\partial \eta _{j}}},$

and where ${\boldsymbol {J}}^{\textsf {T}}$ is the matrix transpose of ${\boldsymbol {J}}.$

In [information geometry](https://en.wikipedia.org/wiki/Information_geometry), this is seen as a change of coordinates on a [Riemannian manifold](https://en.wikipedia.org/wiki/Riemannian_manifold), and the intrinsic properties of curvature are unchanged under different parametrizations. In general, the Fisher information matrix provides a Riemannian metric (more precisely, the Fisher–Rao metric) for the manifold of thermodynamic states, and can be used as an information-geometric complexity measure for a classification of [phase transitions](https://en.wikipedia.org/wiki/Phase_transitions), e.g., the scalar curvature of the thermodynamic metric tensor diverges at (and only at) a phase transition point.

In the thermodynamic context, the Fisher information matrix is directly related to the rate of change in the corresponding [order parameters](https://en.wikipedia.org/wiki/Order_parameter#Order_parameters). In particular, such relations identify second-order phase transitions via divergences of individual elements of the Fisher information matrix.

### Isoperimetric inequality

The Fisher information matrix plays a role in an inequality like the [isoperimetric inequality](https://en.wikipedia.org/wiki/Isoperimetric_inequality). Of all probability distributions with a given entropy, the one whose Fisher information matrix has the smallest trace is the Gaussian distribution. This is like how, of all bounded sets with a given volume, the sphere has the smallest surface area.

The proof involves taking a multivariate random variable $X$ with density function $f$ and adding a location parameter to form a family of densities $\{f(x-\theta )\mid \theta \in \mathbb {R} ^{n}\}$. Then, by analogy with the [Minkowski–Steiner formula](https://en.wikipedia.org/wiki/Minkowski%E2%80%93Steiner_formula), the "surface area" of $X$ is defined to be

$S(X)=\lim _{\varepsilon \to 0}{\frac {e^{H(X+Z_{\varepsilon })}-e^{H(X)}}{\varepsilon }}$

where $Z_{\varepsilon }$ is a Gaussian variable with covariance matrix $\varepsilon I$. The name "surface area" is apt because the entropy power $e^{H(X)}$ is the volume of the "effective support set", so $S(X)$ is the "derivative" of the volume of the effective support set, much like the Minkowski-Steiner formula. The remainder of the proof uses the [entropy power inequality](https://en.wikipedia.org/wiki/Entropy_power_inequality), which is like the [Brunn–Minkowski inequality](https://en.wikipedia.org/wiki/Brunn%E2%80%93Minkowski_theorem). The trace of the Fisher information matrix is found to be a factor of $S(X)$.

## Applications

### Optimal design of experiments

Fisher information is widely used in [optimal experimental design](https://en.wikipedia.org/wiki/Optimal_design). Because of the reciprocity of estimator-variance and Fisher information, *minimizing* the *variance* corresponds to *maximizing* the *information*.

When the [linear](https://en.wikipedia.org/wiki/Linear_model) (or [linearized](https://en.wikipedia.org/wiki/Nonlinear_regression)) [statistical model](https://en.wikipedia.org/wiki/Statistical_model) has several [parameters](https://en.wikipedia.org/wiki/Parameter), the [mean](https://en.wikipedia.org/wiki/Expected_value) of the parameter estimator is a [vector](https://en.wikipedia.org/wiki/Column_vector) and its [variance](https://en.wikipedia.org/wiki/Covariance_matrix) is a [matrix](https://en.wikipedia.org/wiki/Matrix_(mathematics) "Matrix (mathematics)"). The inverse of the variance matrix is called the "information matrix". Because the variance of the estimator of a parameter vector is a matrix, the problem of "minimizing the variance" is complicated. Using [statistical theory](https://en.wikipedia.org/wiki/Statistical_theory), statisticians compress the information-matrix using real-valued [summary statistics](https://en.wikipedia.org/wiki/Summary_statistics); being real-valued functions, these "information criteria" can be maximized.

Traditionally, statisticians have evaluated estimators and designs by considering some [summary statistic](https://en.wikipedia.org/wiki/Summary_statistics) of the covariance matrix (of an unbiased estimator), usually with positive real values (like the [[Determinant]] or [matrix trace](https://en.wikipedia.org/wiki/Matrix_trace)). Working with positive real numbers brings several advantages: If the estimator of a single parameter has a positive variance, then the variance and the Fisher information are both positive real numbers; hence they are members of the convex cone of nonnegative real numbers (whose nonzero members have reciprocals in this same cone).

For several parameters, the covariance matrices and information matrices are elements of the convex cone of [nonnegative-definite](https://en.wikipedia.org/wiki/Nonnegative-definite_matrix) symmetric matrices in a [partially](https://en.wikipedia.org/wiki/Partial_order) [ordered vector space](https://en.wikipedia.org/wiki/Ordered_vector_space), under the [Loewner](https://en.wikipedia.org/wiki/Loewner_order) (Löwner) order. This cone is closed under matrix addition and inversion, as well as under the multiplication of positive real numbers and matrices. An exposition of matrix theory and Loewner order appears in Pukelsheim.

The traditional optimality criteria are the information matrix's invariants, in the sense of [invariant theory](https://en.wikipedia.org/wiki/Invariant_theory); algebraically, the traditional optimality criteria are [functionals](https://en.wikipedia.org/wiki/Functional_(mathematics) "Functional (mathematics)") of the [eigenvalues](https://en.wikipedia.org/wiki/Eigenvalue) of the (Fisher) information matrix (see [optimal design](https://en.wikipedia.org/wiki/Optimal_design)).

### Jeffreys prior in Bayesian statistics

In [Bayesian statistics](https://en.wikipedia.org/wiki/Bayesian_statistics), the Fisher information is used to calculate the [Jeffreys prior](https://en.wikipedia.org/wiki/Jeffreys_prior), which is a standard, non-informative prior for continuous distribution parameters.

### Computational neuroscience

The Fisher information has been used to find bounds on the accuracy of [neural codes](https://en.wikipedia.org/wiki/Neural_coding). In that case, *X* is typically the joint responses of many neurons representing a low dimensional variable *θ* (such as a [stimulus](https://en.wikipedia.org/wiki/Stimulus_(physiology) "Stimulus (physiology)") parameter). In particular the role of correlations in the noise of the neural responses has been studied.

### Epidemiology

Fisher information was used to study how informative different data sources are for estimation of the [reproduction number](https://en.wikipedia.org/wiki/Reproduction_number) of SARS-CoV-2.

### Machine learning

The Fisher information is used in machine learning techniques such as [elastic weight consolidation](https://en.wikipedia.org/wiki/Elastic_weight_consolidation), which reduces [catastrophic forgetting](https://en.wikipedia.org/wiki/Catastrophic_interference) in [artificial neural networks](https://en.wikipedia.org/wiki/Artificial_neural_networks).

Fisher information can be used as an alternative to the Hessian of the loss function in second-order gradient descent network training.

### Color discrimination

Using a [Fisher information metric](https://en.wikipedia.org/wiki/Fisher_information_metric), da Fonseca et. al  investigated the degree to which [MacAdam ellipses](https://en.wikipedia.org/wiki/MacAdam_ellipse) (color discrimination ellipses) can be derived from the [response functions](https://en.wikipedia.org/wiki/LMS_color_space) of the retinal photoreceptors.

## Relation to relative entropy

Fisher information is related to [relative entropy](https://en.wikipedia.org/wiki/Relative_entropy). The relative entropy, or [[Kullback-Leibler Divergence|Kullback–Leibler divergence]], between two distributions $p$ and $q$ can be written as

$KL(p:q)=\int p(x)\log {\frac {p(x)}{q(x)}}\,dx.$

Now, consider a family of probability distributions $f(x;\theta )$ parametrized by $\theta \in \Theta$. Then the [[Kullback-Leibler Divergence|Kullback–Leibler divergence]], between two distributions in the family can be written as

$D(\theta ,\theta ')=KL(p({}\cdot {};\theta ):p({}\cdot {};\theta '))=\int f(x;\theta )\log {\frac {f(x;\theta )}{f(x;\theta ')}}\,dx.$

If $\theta$ is fixed, then the relative entropy between two distributions of the same family is minimized at $\theta '=\theta$. For $\theta '$ close to $\theta$, one may expand the previous expression in a series up to second order:

$D(\theta ,\theta ')={\frac {1}{2}}(\theta '-\theta )^{\textsf {T}}\left({\frac {\partial ^{2}}{\partial \theta '_{i}\,\partial \theta '_{j}}}D(\theta ,\theta ')\right)_{\theta '=\theta }(\theta '-\theta )+o\left((\theta '-\theta )^{2}\right)$

But the second order derivative can be written as

$\left({\frac {\partial ^{2}}{\partial \theta '_{i}\,\partial \theta '_{j}}}D(\theta ,\theta ')\right)_{\theta '=\theta }=-\int f(x;\theta )\left({\frac {\partial ^{2}}{\partial \theta '_{i}\,\partial \theta '_{j}}}\log(f(x;\theta '))\right)_{\theta '=\theta }\,dx=[{\mathcal {I}}(\theta )]_{i,j}.$

Thus the Fisher information represents the [curvature](https://en.wikipedia.org/wiki/Curvature) of the relative entropy of a conditional distribution with respect to its parameters.

## History

The Fisher information was discussed by several early statisticians, notably [F. Y. Edgeworth](https://en.wikipedia.org/wiki/Francis_Ysidro_Edgeworth). For example, Savage says: "In it \[Fisher information\], he \[Fisher\] was to some extent anticipated (Edgeworth 1908–9 esp. 502, 507–8, 662, 677–8, 82–5 and references he \[Edgeworth\] cites including Pearson and Filon 1898 \[. . .\])." There are a number of early historical sources and a number of reviews of this early work.

## See also

- [Efficiency (statistics)](https://en.wikipedia.org/wiki/Efficiency_(statistics) "Efficiency (statistics)")
- [Observed information](https://en.wikipedia.org/wiki/Observed_information)
- [Fisher information metric](https://en.wikipedia.org/wiki/Fisher_information_metric)
- [Formation matrix](https://en.wikipedia.org/wiki/Formation_matrix)
- [Information geometry](https://en.wikipedia.org/wiki/Information_geometry)
- [Jeffreys prior](https://en.wikipedia.org/wiki/Jeffreys_prior)
- [Cramér–Rao bound](https://en.wikipedia.org/wiki/Cram%C3%A9r%E2%80%93Rao_bound)
- [Minimum Fisher information](https://en.wikipedia.org/wiki/Minimum_Fisher_information)
- [Quantum Fisher information](https://en.wikipedia.org/wiki/Quantum_Fisher_information)
- [White information matrix test](https://en.wikipedia.org/wiki/White_information_matrix_test)

Other measures employed in [information theory](https://en.wikipedia.org/wiki/Information_theory):

- [Entropy (information theory)](https://en.wikipedia.org/wiki/Entropy_(information_theory) "Entropy (information theory)")
- [[Kullback-Leibler Divergence|Kullback–Leibler divergence]]
- [Self-information](https://en.wikipedia.org/wiki/Self-information)

## Notes

1.  Robert, Christian (2007). "Noninformative prior distributions". *The Bayesian Choice* (2nd ed.). Springer. pp. 127–141. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-71598-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-71598-8).
2.  [Le Cam, Lucien](https://en.wikipedia.org/wiki/Lucien_Le_Cam) (1986). *Asymptotic Methods in Statistical Decision Theory*. New York: Springer. pp. 618–621. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-96307-3](https://en.wikipedia.org/wiki/Special:BookSources/0-387-96307-3).
3.  Kass, Robert E.; Tierney, Luke; Kadane, Joseph B. (1990). "The Validity of Posterior Expansions Based on Laplace's Method". In Geisser, S.; Hodges, J. S.; Press, S. J.; Zellner, A. (eds.). *Bayesian and Likelihood Methods in Statistics and Econometrics*. Elsevier. pp. 473–488. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-444-88376-2](https://en.wikipedia.org/wiki/Special:BookSources/0-444-88376-2).
4.  .
5.  Suba Rao. ["Lectures on statistical inference"](https://web.archive.org/web/20200926091124/http://www.stat.tamu.edu/~suhasini/teaching613/inference.pdf) (PDF). Archived from [the original](http://www.stat.tamu.edu/~suhasini/teaching613/inference.pdf) (PDF) on 2020-09-26. Retrieved 2013-04-12.
6.  .
7.  **,_Lemma_5.3,_p.116_7-0)** , eq. (2.5.16), Lemma 5.3, p.116.
8.  Schervish, Mark J. (1995). *Theory of Statistics*. New York, NY: Springer New York. p. 111. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4612-4250-5](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4612-4250-5). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [852790658](https://search.worldcat.org/oclc/852790658).
9.  .
10. .
11. Nielsen, Frank (2023). ["A Simple Approximation Method for the Fisher–Rao Distance between Multivariate Normal Distributions"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10137715). *Entropy*. **25** (4): 654. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2302.08175](https://arxiv.org/abs/2302.08175). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2023Entrp..25..654N](https://ui.adsabs.harvard.edu/abs/2023Entrp..25..654N). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3390/e25040654](https://doi.org/10.3390%2Fe25040654). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [10137715](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10137715). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [37190442](https://pubmed.ncbi.nlm.nih.gov/37190442).
12. Nielsen, Frank (2013). "Cramér-Rao Lower Bound and Information Geometry". *Connected at Infinity II*. Texts and Readings in Mathematics. Vol. 67. pp. 18–37. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1301.3578](https://arxiv.org/abs/1301.3578). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-93-86279-56-9_2](https://doi.org/10.1007%2F978-93-86279-56-9_2). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-93-80250-51-9](https://en.wikipedia.org/wiki/Special:BookSources/978-93-80250-51-9). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [16759683](https://api.semanticscholar.org/CorpusID:16759683).
13. Spall, J. C. (2005). "Monte Carlo Computation of the Fisher Information Matrix in Nonstandard Settings". *Journal of Computational and Graphical Statistics*. **14** (4): 889–909. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1198/106186005X78800](https://doi.org/10.1198%2F106186005X78800). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [16090098](https://api.semanticscholar.org/CorpusID:16090098).
14. Spall, J. C. (2008), "Improved Methods for Monte Carlo Estimation of the Fisher Information Matrix," *Proceedings of the American Control Conference*, Seattle, WA, 11–13 June 2008, pp. 2395–2400. [https://doi.org/10.1109/ACC.2008.4586850](https://doi.org/10.1109/ACC.2008.4586850)
15. Das, S.; Spall, J. C.; Ghanem, R. (2010). "Efficient Monte Carlo Computation of Fisher Information Matrix Using Prior Information". *Computational Statistics and Data Analysis*. **54** (2): 272–289. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.csda.2009.09.018](https://doi.org/10.1016%2Fj.csda.2009.09.018).
16. Barndorff-Nielsen, O. E.; Cox, D. R. (1994). *Inference and Asymptotics*. Chapman & Hall. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-412-49440-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-412-49440-6).
17. Cox, D. R.; Reid, N. (1987). "Parameter orthogonality and approximate conditional inference (with discussion)". *J. Royal Statistical Soc. B*. **49**: 1–39. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1111/j.2517-6161.1987.tb01422.x](https://doi.org/10.1111%2Fj.2517-6161.1987.tb01422.x).
18. Watanabe, S. (2008), Accardi, L.; Freudenberg, W.; Ohya, M. (eds.), "Algebraic geometrical method in singular statistical estimation", *Quantum Bio-Informatics*, [World Scientific](https://en.wikipedia.org/wiki/World_Scientific): 325–336, [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2008qbi..conf..325W](https://ui.adsabs.harvard.edu/abs/2008qbi..conf..325W), [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1142/9789812793171_0024](https://doi.org/10.1142%2F9789812793171_0024), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-981-279-316-4](https://en.wikipedia.org/wiki/Special:BookSources/978-981-279-316-4)`{{`[`citation`](https://en.wikipedia.org/wiki/Template:Citation)`}}`: CS1 maint: work parameter with ISBN ([link](https://en.wikipedia.org/wiki/Category:CS1_maint:_work_parameter_with_ISBN)).
19. Watanabe, S (2013). "A Widely Applicable Bayesian Information Criterion". *[Journal of Machine Learning Research](https://en.wikipedia.org/wiki/Journal_of_Machine_Learning_Research)*. **14**: 867–897.
20. Malagò, Luigi; Pistone, Giovanni (2015). "Information Geometry of the Gaussian Distribution in View of Stochastic Optimization". *Proceedings of the 2015 ACM Conference on Foundations of Genetic Algorithms XIII*. pp. 150–162. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1145/2725494.2725510](https://doi.org/10.1145%2F2725494.2725510). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4503-3434-1](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4503-3434-1). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [693896](https://api.semanticscholar.org/CorpusID:693896).
21. Mardia, K. V.; Marshall, R. J. (1984). "Maximum likelihood estimation of models for residual covariance in spatial regression". *[Biometrika](https://en.wikipedia.org/wiki/Biometrika)*. **71** (1): 135–46. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1093/biomet/71.1.135](https://doi.org/10.1093%2Fbiomet%2F71.1.135).
22. Zamir, R. (1998). "A proof of the Fisher information inequality via a data processing argument". *[IEEE Transactions on Information Theory](https://en.wikipedia.org/wiki/IEEE_Transactions_on_Information_Theory)*. **44** (3): 1246–1250. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.49.6628](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.49.6628). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/18.669301](https://doi.org/10.1109%2F18.669301).
23. Polyanskiy, Yury (2017). ["Lecture notes on information theory, chapter 29, ECE563 (UIUC)"](https://people.lids.mit.edu/yp/homepage/data/LN_stats.pdf) (PDF). *Lecture notes on information theory*. [Archived](https://web.archive.org/web/20220524014051/https://people.lids.mit.edu/yp/homepage/data/LN_stats.pdf) (PDF) from the original on 2022-05-24. Retrieved 2022-05-24.
24. Schervish, Mark J. (1995). *Theory of Statistics*. Springer-Verlag. p. 113.
25. **_25-0)** , eq. (2.5.11).
26. **_26-0)** , eq. (2.6.16).
27. Janke, W.; Johnston, D. A.; Kenna, R. (2004). "Information Geometry and Phase Transitions". *Physica A*. **336** (1–2): 181. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[cond-mat/0401092](https://arxiv.org/abs/cond-mat/0401092). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2004PhyA..336..181J](https://ui.adsabs.harvard.edu/abs/2004PhyA..336..181J). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.physa.2004.01.023](https://doi.org/10.1016%2Fj.physa.2004.01.023). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [119085942](https://api.semanticscholar.org/CorpusID:119085942).
28. Prokopenko, M.; Lizier, Joseph T.; Lizier, J. T.; Obst, O.; Wang, X. R. (2011). "Relating Fisher information to order parameters". *Physical Review E*. **84** (4) 041116. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2011PhRvE..84d1116P](https://ui.adsabs.harvard.edu/abs/2011PhRvE..84d1116P). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1103/PhysRevE.84.041116](https://doi.org/10.1103%2FPhysRevE.84.041116). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [22181096](https://pubmed.ncbi.nlm.nih.gov/22181096). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [18366894](https://api.semanticscholar.org/CorpusID:18366894).
29. Costa, M.; Cover, T. (Nov 1984). "On the similarity of the entropy power inequality and the Brunn-Minkowski inequality". *IEEE Transactions on Information Theory*. **30** (6): 837–839. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/TIT.1984.1056983](https://doi.org/10.1109%2FTIT.1984.1056983). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1557-9654](https://search.worldcat.org/issn/1557-9654).
30. Cover, Thomas M. (2006). *Elements of information theory*. Joy A. Thomas (2nd ed.). Hoboken, N.J.: Wiley-Interscience. p. 256. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-24195-4](https://en.wikipedia.org/wiki/Special:BookSources/0-471-24195-4). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [59879802](https://search.worldcat.org/oclc/59879802).
31. Pukelsheim, Friedrich (1993). *Optimal Design of Experiments*. New York: Wiley. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-61971-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-61971-0).
32. Bernardo, Jose M.; Smith, Adrian F. M. (1994). *Bayesian Theory*. New York: John Wiley & Sons. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-92416-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-92416-6).
33. Abbott, Larry F.; Dayan, Peter (1999). "The effect of correlated variability on the accuracy of a population code". *Neural Computation*. **11** (1): 91–101. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1162/089976699300016827](https://doi.org/10.1162%2F089976699300016827). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [9950724](https://pubmed.ncbi.nlm.nih.gov/9950724). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [2958438](https://api.semanticscholar.org/CorpusID:2958438).
34. Parag, K.V.; Donnelly, C.A.; Zarebski, A.E. (2022). ["Quantifying the information in noisy epidemic curves"](https://doi.org/10.1038%2Fs43588-022-00313-1). *Nature Computational Science*. **2** (9): 584–594. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1038/s43588-022-00313-1](https://doi.org/10.1038%2Fs43588-022-00313-1). [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[10044/1/100205](https://hdl.handle.net/10044%2F1%2F100205). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [38177483](https://pubmed.ncbi.nlm.nih.gov/38177483). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [248811793](https://api.semanticscholar.org/CorpusID:248811793).
35. Kirkpatrick, James; Pascanu, Razvan; Rabinowitz, Neil; Veness, Joel; Desjardins, Guillaume; Rusu, Andrei A.; Milan, Kieran; Quan, John; Ramalho, Tiago (2017-03-28). ["Overcoming catastrophic forgetting in neural networks"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5380101). *Proceedings of the National Academy of Sciences*. **114** (13): 3521–3526. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1612.00796](https://arxiv.org/abs/1612.00796). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2017PNAS..114.3521K](https://ui.adsabs.harvard.edu/abs/2017PNAS..114.3521K). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1073/pnas.1611835114](https://doi.org/10.1073%2Fpnas.1611835114). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0027-8424](https://search.worldcat.org/issn/0027-8424). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [5380101](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5380101). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [28292907](https://pubmed.ncbi.nlm.nih.gov/28292907).
36. Martens, James (August 2020). "New Insights and Perspectives on the Natural Gradient Method". *Journal of Machine Learning Research* (21). [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1412.1193](https://arxiv.org/abs/1412.1193).
37. da Fonseca, Maria; Samengo, In'es (1 December 2016). "Derivation of human chromatic discrimination ability from an information-theoretical notion of distance in color space". *Neural Computation*. **28** (12): 2628–2655. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1611.07272](https://arxiv.org/abs/1611.07272). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1162/NECO_a_00903](https://doi.org/10.1162%2FNECO_a_00903). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [27764598](https://pubmed.ncbi.nlm.nih.gov/27764598).
38. [Gourieroux & Montfort (1995), page 87](https://books.google.com/books?id=gqI-pAP2JZ8C&pg=PA87)
39. .
40. , p. 156.
41. ; .
42. .
43. ; ; .
44. ; .

## References

- [Cramér, Harald](https://en.wikipedia.org/wiki/Harald_Cram%C3%A9r) (1946). *Mathematical methods of statistics*. Princeton mathematical series. Princeton: Princeton University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-691-08004-6](https://en.wikipedia.org/wiki/Special:BookSources/0-691-08004-6). `{{`[`cite book`](https://en.wikipedia.org/wiki/Template:Cite_book)`}}`: ISBN / Date incompatibility ([help](https://en.wikipedia.org/wiki/Help:CS1_errors#invalid_isbn_date))
- [Edgeworth, F. Y.](https://en.wikipedia.org/wiki/Francis_Ysidro_Edgeworth) (Jun 1908). ["On the Probable Errors of Frequency-Constants"](https://zenodo.org/record/1449470). *[Journal of the Royal Statistical Society](https://en.wikipedia.org/wiki/Journal_of_the_Royal_Statistical_Society)*. **71** (2): 381–397. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2339461](https://doi.org/10.2307%2F2339461). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2339461](https://www.jstor.org/stable/2339461).
- [Edgeworth, F. Y.](https://en.wikipedia.org/wiki/Francis_Ysidro_Edgeworth) (Sep 1908). ["On the Probable Errors of Frequency-Constants (Contd.)"](https://zenodo.org/record/1449468). *[Journal of the Royal Statistical Society](https://en.wikipedia.org/wiki/Journal_of_the_Royal_Statistical_Society)*. **71** (3): 499–512. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2339293](https://doi.org/10.2307%2F2339293). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2339293](https://www.jstor.org/stable/2339293).
- [Edgeworth, F. Y.](https://en.wikipedia.org/wiki/Francis_Ysidro_Edgeworth) (Dec 1908). ["On the Probable Errors of Frequency-Constants (Contd.)"](https://zenodo.org/record/1449468). *[Journal of the Royal Statistical Society](https://en.wikipedia.org/wiki/Journal_of_the_Royal_Statistical_Society)*. **71** (4): 651–678. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2339378](https://doi.org/10.2307%2F2339378). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2339378](https://www.jstor.org/stable/2339378).
- [Fisher, R. A.](https://en.wikipedia.org/wiki/Ronald_Fisher) (1922-01-01). ["On the mathematical foundations of theoretical statistics"](https://doi.org/10.1098%2Frsta.1922.0009). *Philosophical Transactions of the Royal Society of London, Series A*. **222** (594–604): 309–368. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1922RSPTA.222..309F](https://ui.adsabs.harvard.edu/abs/1922RSPTA.222..309F). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1098/rsta.1922.0009](https://doi.org/10.1098%2Frsta.1922.0009). [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[2440/15172](https://hdl.handle.net/2440%2F15172).
- [Frieden, B. R.](https://en.wikipedia.org/wiki/B._Roy_Frieden) (2004). *Science from Fisher Information: A Unification*. Cambridge Univ. Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-00911-1](https://en.wikipedia.org/wiki/Special:BookSources/0-521-00911-1).
- Frieden, B. Roy; Gatenby, Robert A. (2013). ["Principle of maximum Fisher information from Hardy's axioms applied to statistical systems"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4010149). *Physical Review E*. **88** (4) 042144. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1405.0007](https://arxiv.org/abs/1405.0007). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2013PhRvE..88d2144F](https://ui.adsabs.harvard.edu/abs/2013PhRvE..88d2144F). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1103/PhysRevE.88.042144](https://doi.org/10.1103%2FPhysRevE.88.042144). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [4010149](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4010149). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [24229152](https://pubmed.ncbi.nlm.nih.gov/24229152).
- Hald, A. (May 1999). ["On the History of Maximum Likelihood in Relation to Inverse Probability and Least Squares"](https://doi.org/10.1214%2Fss%2F1009212248). *[Statistical Science](https://en.wikipedia.org/wiki/Statistical_Science)*. **14** (2): 214–222. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/ss/1009212248](https://doi.org/10.1214%2Fss%2F1009212248). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2676741](https://www.jstor.org/stable/2676741).
- Hald, A. (1998). *A History of Mathematical Statistics from 1750 to 1930*. New York: Wiley. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-17912-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-17912-2).
- [Lehmann, E. L.](https://en.wikipedia.org/wiki/Erich_Leo_Lehmann); Casella, G. (1998). *Theory of Point Estimation* (2nd ed.). Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-98502-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-98502-2).
- [Le Cam, Lucien](https://en.wikipedia.org/wiki/Lucien_Le_Cam) (1986). *Asymptotic Methods in Statistical Decision Theory*. Springer-Verlag. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-96307-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-96307-5).
- Pratt, John W. (May 1976). ["F. Y. Edgeworth and R. A. Fisher on the Efficiency of Maximum Likelihood Estimation"](https://doi.org/10.1214%2Faos%2F1176343457). *[Annals of Statistics](https://en.wikipedia.org/wiki/Annals_of_Statistics)*. **4** (3): 501–514. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/aos/1176343457](https://doi.org/10.1214%2Faos%2F1176343457). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2958222](https://www.jstor.org/stable/2958222).
- [Rao, C. Radhakrishna](https://en.wikipedia.org/wiki/C._R._Rao) (1945). "Information and the Accuracy Attainable in the Estimation of Statistical Parameters". *Breakthroughs in Statistics*. Springer Series in Statistics. Vol. 37. pp. 81–91. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-1-4612-0919-5_16](https://doi.org/10.1007%2F978-1-4612-0919-5_16). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-94037-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-94037-3). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [117034671](https://api.semanticscholar.org/CorpusID:117034671). `{{`[`cite book`](https://en.wikipedia.org/wiki/Template:Cite_book)`}}`: ISBN / Date incompatibility ([help](https://en.wikipedia.org/wiki/Help:CS1_errors#invalid_isbn_date)); `|journal=` ignored ([help](https://en.wikipedia.org/wiki/Help:CS1_errors#periodical_ignored))
- [Savage, L. J.](https://en.wikipedia.org/wiki/Leonard_J._Savage) (May 1976). ["On Rereading R. A. Fisher"](https://doi.org/10.1214%2Faos%2F1176343456). *[Annals of Statistics](https://en.wikipedia.org/wiki/Annals_of_Statistics)*. **4** (3): 441–500. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/aos/1176343456](https://doi.org/10.1214%2Faos%2F1176343456). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2958221](https://www.jstor.org/stable/2958221).
- Schervish, Mark J. (1995). *Theory of Statistics*. New York: Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-94546-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-94546-0).
- [Stigler, S. M.](https://en.wikipedia.org/wiki/Stephen_Stigler) (1986). [The History of Statistics: The Measurement of Uncertainty before 1900](https://archive.org/details/historyofstatist00stig). Harvard University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-674-40340-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-674-40340-6).<sup>\[*[page needed](https://en.wikipedia.org/wiki/Wikipedia:Citing_sources)*\]</sup>
- [Stigler, S. M.](https://en.wikipedia.org/wiki/Stephen_Stigler) (1978). ["Francis Ysidro Edgeworth, Statistician"](https://en.wikipedia.org/wiki/Francis_Ysidro_Edgeworth). *Journal of the Royal Statistical Society, Series A*. **141** (3): 287–322. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2344804](https://doi.org/10.2307%2F2344804). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2344804](https://www.jstor.org/stable/2344804).
- [Stigler, S. M.](https://en.wikipedia.org/wiki/Stephen_Stigler) (1999). *Statistics on the Table: The History of Statistical Concepts and Methods*. Harvard University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-674-83601-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-674-83601-3). <sup>\[*[page needed](https://en.wikipedia.org/wiki/Wikipedia:Citing_sources)*\]</sup>
- [Van Trees, H. L.](https://en.wikipedia.org/wiki/Harry_L._Van_Trees) (1968). *Detection, Estimation, and Modulation Theory, Part I*. New York: Wiley. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-09517-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-09517-0).
