[[probability-statistics.base]]

> Source: [[Exponential Family]]
> License: Wikipedia content is available under CC BY-SA 4.0.

In [probability](https://en.wikipedia.org/wiki/Theory_of_probability) and [statistics](https://en.wikipedia.org/wiki/Statistics), an **exponential family** is a [parametric](https://en.wikipedia.org/wiki/Parametric_model) set of [probability distributions](https://en.wikipedia.org/wiki/Probability_distribution) of a certain form, specified below. This special form is chosen for mathematical convenience, including the enabling of the user to calculate expectations, covariances using differentiation based on some useful algebraic properties, as well as for generality, as exponential families are in a sense very natural sets of distributions to consider. The term **exponential class** is sometimes used in place of "exponential family", or the older term **Koopman–Darmois family**. Sometimes loosely referred to as *the* exponential family, this class of distributions is distinct because they all possess a variety of desirable properties, most importantly the existence of a [sufficient statistic](https://en.wikipedia.org/wiki/Sufficient_statistic).

The concept of exponential families is credited to [E. J. G. Pitman](https://en.wikipedia.org/wiki/E._J._G._Pitman), [G. Darmois](https://en.wikipedia.org/wiki/Georges_Darmois), and [B. O. Koopman](https://en.wikipedia.org/wiki/Bernard_Koopman) in 1935–1936. Exponential families of distributions provide a general framework for selecting a possible alternative parameterisation of a [parametric family](https://en.wikipedia.org/wiki/Parametric_family) of distributions, in terms of natural parameters, and for defining useful [sample statistics](https://en.wikipedia.org/wiki/Sample_statistic), called the natural sufficient statistics of the family.

## Nomenclature difficulty

The terms "distribution" and "family" are often used loosely: Specifically, *an* exponential family is a *set* of distributions, where the specific distribution varies with the parameter; however, a parametric *family* of distributions is often referred to as "*a* distribution" (like "the normal distribution", meaning "the family of normal distributions"), and the set of all exponential families is sometimes loosely referred to as "the" exponential family.

## Definition

Most of the commonly used distributions form an exponential family or subset of an exponential family, listed in the subsection below. The subsections following it are a sequence of increasingly more general mathematical definitions of an exponential family. A casual reader may wish to restrict attention to the first and simplest definition, which corresponds to a single-parameter family of [discrete](https://en.wikipedia.org/wiki/Discrete_probability_distribution) or [continuous](https://en.wikipedia.org/wiki/Continuous_probability_distribution) probability distributions.

### Examples of exponential family distributions

Exponential families include many of the most common distributions. Among many others, exponential families includes the following:

- [normal](https://en.wikipedia.org/wiki/Normal_distribution)
- [exponential](https://en.wikipedia.org/wiki/Exponential_distribution)
- [gamma](https://en.wikipedia.org/wiki/Gamma_distribution)
- [chi-squared](https://en.wikipedia.org/wiki/Chi-squared_distribution)
- [beta](https://en.wikipedia.org/wiki/Beta_distribution)
- [Dirichlet](https://en.wikipedia.org/wiki/Dirichlet_distribution)
- [Bernoulli](https://en.wikipedia.org/wiki/Bernoulli_distribution)
- [categorical](https://en.wikipedia.org/wiki/Categorical_distribution)
- [Poisson](https://en.wikipedia.org/wiki/Poisson_distribution)
- [Wishart](https://en.wikipedia.org/wiki/Wishart_distribution)
- [inverse Wishart](https://en.wikipedia.org/wiki/Inverse_Wishart_distribution)
- [geometric](https://en.wikipedia.org/wiki/Geometric_distribution)

A number of common distributions are exponential families, but only when certain parameters are fixed and known. For example:

- [binomial](https://en.wikipedia.org/wiki/Binomial_distribution) (with fixed number of trials)
- [multinomial](https://en.wikipedia.org/wiki/Multinomial_distribution) (with fixed number of trials)
- [negative binomial](https://en.wikipedia.org/wiki/Negative_binomial_distribution) (with fixed number of failures)

Note that in each case, the parameters which must be fixed are those that set a limit on the range of values that can possibly be observed.

Examples of common distributions that are *not* exponential families are [Student's t](https://en.wikipedia.org/wiki/Student%27s_t_distribution), most [mixture distributions](https://en.wikipedia.org/wiki/Mixture_distribution), and even the family of [uniform distributions](https://en.wikipedia.org/wiki/Uniform_distribution_(continuous)) when the bounds are not fixed. See the section below on [examples](#Examples) for more discussion.

### Scalar parameter

The value of $\theta$ is called the *parameter* of the family.

A single-parameter exponential family is a set of probability distributions whose [[Probability Density Function]] (or [probability mass function](https://en.wikipedia.org/wiki/Probability_mass_function), for the case of a [discrete distribution](https://en.wikipedia.org/wiki/Discrete_distribution)) can be expressed in the form

$$
f_{X}{\left(x\,{\big |}\,\theta \right)}=h(x)\,\exp \left[\eta (\theta )\cdot T(x)-A(\theta )\right]
$$

where *T*(*x*), *h*(*x*), *η*(*θ*), and *A*(*θ*) are known functions. The function *h*(*x*) must be non-negative.

An alternative, equivalent form often given is

$$
f_{X}{\left(x\ {\big |}\ \theta \right)}=h(x)\,g(\theta )\,\exp \left[\eta (\theta )\cdot T(x)\right]
$$

or equivalently

$$
f_{X}{\left(x\ {\big |}\ \theta \right)}=\exp \left[\eta (\theta )\cdot T(x)-A(\theta )+B(x)\right].
$$

In terms of [log probability](https://en.wikipedia.org/wiki/Log_probability), 

$$
\log(f_{X}{\left(x\ {\big |}\ \theta \right)})=\eta (\theta )\cdot T(x)-A(\theta )+B(x).
$$

Note that $g(\theta )=e^{-A(\theta )}$ and $h(x)=e^{B(x)}$.

#### Support must be independent of θ

Importantly, the [support](https://en.wikipedia.org/wiki/Support_of_a_distribution#In_probability_and_measure_theory) of $f_{X}{\left(x{\big |}\theta \right)}$ (all the possible $x$ values for which $f_{X}\!\left(x{\big |}\theta \right)$ is greater than $0$) is required to *not* depend on $\theta ~.$ This requirement can be used to exclude a parametric family distribution from being an exponential family.

For example: The [Pareto distribution](https://en.wikipedia.org/wiki/Pareto_distribution) has a pdf which is defined for $x\geq x_{\mathsf {m}}$ (the minimum value, $x_{m}\ ,$ being the scale parameter) and its support, therefore, has a lower limit of $x_{\mathsf {m}}~.$ Since the support of $f_{\alpha ,x_{m}}\!(x)$ is dependent on the value of the parameter, the family of [Pareto distributions](https://en.wikipedia.org/wiki/Pareto_distribution) does not form an exponential family of distributions (at least when $x_{m}$ is unknown).

Another example: [Bernoulli-type](https://en.wikipedia.org/wiki/Bernoulli_trial) distributions – [binomial](https://en.wikipedia.org/wiki/Binomial_distribution), [negative binomial](https://en.wikipedia.org/wiki/Negative_binomial_distribution), [geometric distribution](https://en.wikipedia.org/wiki/Geometric_distribution), and similar – can only be included in the exponential class if the number of [Bernoulli trials](https://en.wikipedia.org/wiki/Bernoulli_trial), n, is treated as a fixed constant – excluded from the free parameter(s) $\theta$ – since the allowed number of trials sets the limits for the number of "successes" or "failures" that can be observed in a set of trials.

#### Vector valued x and θ

Often $x$ is a vector of measurements, in which case $T(x)$ may be a function from the space of possible values of $x$ to the real numbers.

More generally, $\eta (\theta )$ and $T(x)$ can each be vector-valued such that $\eta (\theta )\cdot T(x)$ is real-valued. However, see the discussion below on [vector parameters](#Vector_parameter), regarding the *curved* exponential family.

#### Canonical formulation

If $\eta (\theta )=\theta \ ,$ then the exponential family is said to be in *[canonical form](https://en.wikipedia.org/wiki/Canonical_form)*. By defining a transformed parameter $\eta =\eta (\theta )\ ,$ it is always possible to convert an exponential family to canonical form. The canonical form is non-unique, since $\eta (\theta )$ can be multiplied by any nonzero constant, provided that *T*(*x*) is multiplied by that constant's reciprocal, or a constant *c* can be added to $\eta (\theta )$ and *h*(*x*) multiplied by $\exp \left[{-c}\cdot T(x)\,\right]$ to offset it. In the special case that $\eta (\theta )=\theta$ and *T*(*x*) = *x*, then the family is called a *[natural exponential family](https://en.wikipedia.org/wiki/Natural_exponential_family)*.

Even when $x$ is a scalar, and there is only a single parameter, the functions $\eta (\theta )$ and $T(x)$ can still be vectors, as described below.

The function $A(\theta )\ ,$ or equivalently $g(\theta )\ ,$ is automatically determined once the other functions have been chosen, since it must assume a form that causes the distribution to be [normalized](https://en.wikipedia.org/wiki/Normalizing_constant) (sum or integrate to one over the entire domain). Furthermore, both of these functions can always be written as functions of $\eta \ ,$ even when $\eta (\theta )$ is not a [one-to-one](https://en.wikipedia.org/wiki/Bijection) function, i.e. two or more different values of $\theta$ map to the same value of $\eta (\theta )\ ,$ and hence $\eta (\theta )$ cannot be inverted. In such a case, all values of $\theta$ mapping to the same $\eta (\theta )$ will also have the same value for $A(\theta )$ and $g(\theta )~.$

### Factorization of the variables involved

What is important to note, and what characterizes all exponential family variants, is that the parameter(s) and the observation variable(s) must [factorize](https://en.wikipedia.org/wiki/Factorize) (can be separated into products each of which involves only one type of variable), either directly or within either part (the base or exponent) of an [exponentiation](https://en.wikipedia.org/wiki/Exponentiation) operation. Generally, this means that all of the factors constituting the density or mass function must be of one of the following forms:

$$
{\begin{aligned}f(x),&&c^{f(x)},&&{[f(x)]}^{c},&&{[f(x)]}^{g(\theta )},&&{[f(x)]}^{h(x)g(\theta )},\\g(\theta ),&&c^{g(\theta )},&&{[g(\theta )]}^{c},&&{[g(\theta )]}^{f(x)},&&~~{\mathsf {or}}~~{[g(\theta )]}^{h(x)j(\theta )},\end{aligned}}
$$

where *f* and *h* are arbitrary functions of x, the observed statistical variable; *g* and *j* are arbitrary functions of $\theta ,$ the fixed parameters defining the shape of the distribution; and *c* is any arbitrary constant expression (i.e. a number or an expression that does not change with either x or $\theta$).

There are further restrictions on how many such factors can occur. For example, the two expressions:

$$
{[f(x)g(\theta )]}^{h(x)j(\theta )},\qquad {[f(x)]}^{h(x)j(\theta )}{[g(\theta )]}^{h(x)j(\theta )},
$$

are the same, i.e. a product of two "allowed" factors. However, when rewritten into the factorized form,

$$
{\begin{aligned}{\left[f(x)g(\theta )\right]}^{h(x)j(\theta )}&={\left[f(x)\right]}^{h(x)j(\theta )}{\left[g(\theta )\right]}^{h(x)j(\theta )}\\[4pt]&=\exp \left\{{[h(x)\log f(x)]j(\theta )+h(x)[j(\theta )\log g(\theta )]}\right\},\end{aligned}}
$$

it can be seen that it cannot be expressed in the required form. (However, a form of this sort is a member of a *curved exponential family*, which allows multiple factorized terms in the exponent.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>)

To see why an expression of the form

$$
{[f(x)]}^{g(\theta )}
$$

qualifies, 

$$
{[f(x)]}^{g(\theta )}=e^{g(\theta )\log f(x)}
$$

and hence factorizes inside of the exponent. Similarly,

$$
{[f(x)]}^{h(x)g(\theta )}=e^{h(x)g(\theta )\log f(x)}=e^{[h(x)\log f(x)]g(\theta )}
$$

and again factorizes inside of the exponent.

A factor consisting of a sum where both types of variables are involved (e.g. a factor of the form $1+f(x)g(\theta )$) cannot be factorized in this fashion (except in some cases where occurring directly in an exponent); this is why, for example, the [Cauchy distribution](https://en.wikipedia.org/wiki/Cauchy_distribution) and [Student's t distribution](https://en.wikipedia.org/wiki/Student%27s_t_distribution) are not exponential families.

### Vector parameter

The definition in terms of one *real-number* parameter can be extended to one *real-vector* parameter

$$
{\boldsymbol {\theta }}\equiv {\begin{bmatrix}\theta _{1}&\theta _{2}&\cdots &\theta _{s}\end{bmatrix}}^{\mathsf {T}}.
$$

A family of distributions is said to belong to a vector exponential family if the probability density function (or probability mass function, for discrete distributions) can be written as

$$
f_{X}(x\mid {\boldsymbol {\theta }})=h(x)\,\exp \left(\sum _{i=1}^{s}\eta _{i}({\boldsymbol {\theta }})T_{i}(x)-A({\boldsymbol {\theta }})\right)~,
$$

or in a more compact form,

$$
f_{X}(x\mid {\boldsymbol {\theta }})=h(x)\,\exp \left[{\boldsymbol {\eta }}({\boldsymbol {\theta }})\cdot \mathbf {T} (x)-A({\boldsymbol {\theta }})\right]
$$

This form writes the sum as a [dot product](https://en.wikipedia.org/wiki/Dot_product) of vector-valued functions ${\boldsymbol {\eta }}({\boldsymbol {\theta }})$ and *T*(*x*).

An alternative, equivalent form often seen is

$$
f_{X}(x\mid {\boldsymbol {\theta }})=h(x)\,g({\boldsymbol {\theta }})\,\exp \left[{\boldsymbol {\eta }}({\boldsymbol {\theta }})\cdot \mathbf {T} (x)\right]
$$

As in the scalar valued case, the exponential family is said to be in *canonical form* if

$$
\eta _{i}({\boldsymbol {\theta }})=\theta _{i}~,\quad \forall i\,.
$$

A vector exponential family is said to be *curved* if the dimension of

$$
{\boldsymbol {\theta }}\equiv {\begin{bmatrix}\theta _{1}&\theta _{2}&\cdots &\theta _{d}\end{bmatrix}}^{\mathsf {T}}
$$

is less than the dimension of the vector

$$
{\boldsymbol {\eta }}({\boldsymbol {\theta }})\equiv {\begin{bmatrix}\eta _{1}{\!({\boldsymbol {\theta }})}&\eta _{2}{\!({\boldsymbol {\theta }})}&\cdots &\eta _{s}{\!({\boldsymbol {\theta }})}\end{bmatrix}}^{\mathsf {T}}~.
$$

That is, if the *dimension*, d, of the parameter vector is less than the *number of functions*, s, of the parameter vector in the above representation of the probability density function. Most common distributions in the exponential family are *not* curved, and many algorithms designed to work with any exponential family implicitly or explicitly assume that the distribution is not curved.

Just as in the case of a scalar-valued parameter, the function $A({\boldsymbol {\theta }})$ or equivalently $g({\boldsymbol {\theta }})$ is automatically determined by the normalization constraint, once the other functions have been chosen. Even if ${\boldsymbol {\eta }}({\boldsymbol {\theta }})$ is not one-to-one, functions $A({\boldsymbol {\eta }})$ and $g({\boldsymbol {\eta }})$ can be defined by requiring that the distribution is normalized for each value of the natural parameter ${\boldsymbol {\eta }}$. This yields the *canonical form*

$$
f_{X}(x\mid {\boldsymbol {\eta }})=h(x)\exp \left[{\boldsymbol {\eta }}\cdot \mathbf {T} (x)-A({\boldsymbol {\eta }})\right],
$$

or equivalently

$$
f_{X}(x\mid {\boldsymbol {\eta }})=h(x)g({\boldsymbol {\eta }})\exp \left[{\boldsymbol {\eta }}\cdot \mathbf {T} (x)\right].
$$

The above forms may sometimes be seen with ${\boldsymbol {\eta }}^{\mathsf {T}}\mathbf {T} (x)$ in place of ${\boldsymbol {\eta }}\cdot \mathbf {T} (x)\,$. These are exactly equivalent formulations, merely using different notation for the [dot product](https://en.wikipedia.org/wiki/Dot_product).

### Vector parameter, vector variable

The vector-parameter form over a single scalar-valued random variable can be trivially expanded to cover a joint distribution over a vector of random variables. The resulting distribution is simply the same as the above distribution for a scalar-valued random variable with each occurrence of the scalar x replaced by the vector

$$
\mathbf {x} ={\begin{bmatrix}x_{1}&x_{2}&\cdots &x_{k}\end{bmatrix}}^{\mathsf {T}}.
$$

The dimensions k of the random variable need not match the dimension d of the parameter vector, nor (in the case of a curved exponential function) the dimension s of the natural parameter ${\boldsymbol {\eta }}$ and [sufficient statistic](https://en.wikipedia.org/wiki/Sufficient_statistic) **T**(**x**) .

The distribution in this case is written as

$$
f_{X}{\left(\mathbf {x} \mid {\boldsymbol {\theta }}\right)}=h(\mathbf {x} )\,\exp \!\left[\sum _{i=1}^{s}\eta _{i}({\boldsymbol {\theta }})T_{i}(\mathbf {x} )-A({\boldsymbol {\theta }})\right]
$$

Or more compactly as

$$
f_{X}{\left(\mathbf {x} \mid {\boldsymbol {\theta }}\right)}=h(\mathbf {x} )\,\exp \left[{\boldsymbol {\eta }}({\boldsymbol {\theta }})\cdot \mathbf {T} (\mathbf {x} )-A({\boldsymbol {\theta }})\right]
$$

Or alternatively as

$$
f_{X}{\left(\mathbf {x} \mid {\boldsymbol {\theta }}\right)}=g({\boldsymbol {\theta }})\,h(\mathbf {x} )\,\exp \left[{\boldsymbol {\eta }}({\boldsymbol {\theta }})\cdot \mathbf {T} (\mathbf {x} )\right]
$$

### Measure-theoretic formulation

We use [[Cumulative Distribution Function|cumulative distribution functions]] (CDF) in order to encompass both discrete and continuous distributions.

Suppose H is a non-decreasing function of a real variable. Then [Lebesgue–Stieltjes integrals](https://en.wikipedia.org/wiki/Lebesgue%E2%80%93Stieltjes_integral) with respect to $dH(\mathbf {x} )$ are integrals with respect to the *reference measure* of the exponential family generated by H .

Any member of that exponential family has cumulative distribution function

$$
dF{\left(\mathbf {x} \mid {\boldsymbol {\theta }}\right)}=\exp \left[{\boldsymbol {\eta }}(\theta )\cdot \mathbf {T} (\mathbf {x} )-A({\boldsymbol {\theta }})\right]~dH(\mathbf {x} )\,.
$$

*H*(*x*) is a [Lebesgue–Stieltjes integrator](https://en.wikipedia.org/wiki/Lebesgue%E2%80%93Stieltjes_integral) for the reference measure. When the reference measure is finite, it can be normalized and H is actually the [[Cumulative Distribution Function]] of a probability distribution. If F is absolutely continuous with a density $f(x)$ with respect to a reference measure $dx$ (typically [Lebesgue measure](https://en.wikipedia.org/wiki/Lebesgue_measure)), one can write $dF(x)=f(x)\,dx$. In this case, H is also absolutely continuous and can be written $dH(x)=h(x)\,dx$ so the formulas reduce to that of the previous paragraphs. If F is discrete, then H is a [step function](https://en.wikipedia.org/wiki/Step_function) (with steps on the [support](https://en.wikipedia.org/wiki/Support_(mathematics) "Support (mathematics)") of F).

Alternatively, we can write the probability measure directly as

$$
P\left(d\mathbf {x} \mid {\boldsymbol {\theta }}\right)=\exp \left[{\boldsymbol {\eta }}(\theta )\cdot \mathbf {T} (\mathbf {x} )-A({\boldsymbol {\theta }})\right]~\mu (d\mathbf {x} )\,.
$$

for some reference measure $\mu \,$.

## Interpretation

In the definitions above, the functions *T*(*x*), *η*(*θ*), and *A*(*η*) were arbitrary. However, these functions have important interpretations in the resulting probability distribution.

- *T*(*x*) is a *[sufficient statistic](https://en.wikipedia.org/wiki/Sufficiency_(statistics))* of the distribution. For exponential families, the sufficient statistic is a function of the data that holds all information the data x provides with regard to the unknown parameter values. This means that, for any data sets $x$ and $y$, the likelihood ratio is the same, that is ${\frac {f(x;\theta _{1})}{f(x;\theta _{2})}}={\frac {f(y;\theta _{1})}{f(y;\theta _{2})}}$ if *T*(*x*) = *T*(*y*). This is true even if x and y are not equal to each other. The dimension of *T*(*x*) equals the number of parameters of θ and encompasses all of the information regarding the data related to the parameter θ. The sufficient statistic of a set of [independent identically distributed](https://en.wikipedia.org/wiki/Independent_identically_distributed) data observations is simply the sum of individual sufficient statistics, and encapsulates all the information needed to describe the [posterior distribution](https://en.wikipedia.org/wiki/Posterior_distribution) of the parameters, given the data (and hence to derive any desired estimate of the parameters). (This important property is discussed further [below](#Classical_estimation:_sufficiency).)
- η is called the *natural parameter*. The set of values of η for which the function $f_{X}(x;\eta )$ is integrable is called the *natural parameter space*. It can be shown that the natural parameter space is always [convex](https://en.wikipedia.org/wiki/Convex_set).
- *A*(*η*) is called the *log-[partition function](https://en.wikipedia.org/wiki/Partition_function_(mathematics) "Partition function (mathematics)")* because it is the [logarithm](https://en.wikipedia.org/wiki/Logarithm) of a [normalization factor](https://en.wikipedia.org/wiki/Normalization_factor), without which $f_{X}(x;\theta )$ would not be a probability distribution: 

$$
A(\eta )=\log \left(\int _{X}h(x)\,\exp \left[\eta (\theta )\cdot T(x)\right]\,dx\right)
$$

The function A is important in its own right, because the [mean](https://en.wikipedia.org/wiki/Mean), [variance](https://en.wikipedia.org/wiki/Variance) and other [moments](https://en.wikipedia.org/wiki/Moment_(mathematics) "Moment (mathematics)") of the sufficient statistic *T*(*x*) can be derived simply by differentiating *A*(*η*). For example, because log(*x*) is one of the components of the sufficient statistic of the [gamma distribution](https://en.wikipedia.org/wiki/Gamma_distribution), $\operatorname {\mathcal {E}} [\log x]$ can be easily determined for this distribution using *A*(*η*). Technically, this is true because 

$$
K{\left(u\mid \eta \right)}=A(\eta +u)-A(\eta )\,,
$$

 is the [cumulant generating function](https://en.wikipedia.org/wiki/Cumulant_generating_function) of the sufficient statistic.

## Properties

Exponential families have a large number of properties that make them extremely useful for statistical analysis. In many cases, it can be shown that *only* exponential families have these properties. Examples:

- Exponential families are the only families with [sufficient statistics](https://en.wikipedia.org/wiki/Sufficient_statistic) that can summarize arbitrary amounts of [independent identically distributed](https://en.wikipedia.org/wiki/Independent_identically_distributed) data using a fixed number of values. ([Pitman](https://en.wikipedia.org/wiki/E._J._G._Pitman)–[Koopman](https://en.wikipedia.org/wiki/Bernard_Koopman)–[Darmois](https://en.wikipedia.org/wiki/Georges_Darmois) theorem)
- Exponential families have [conjugate priors](https://en.wikipedia.org/wiki/Conjugate_prior), an important property in [Bayesian statistics](https://en.wikipedia.org/wiki/Bayesian_statistics).
- The [posterior predictive distribution](https://en.wikipedia.org/wiki/Posterior_predictive_distribution) of an exponential-family random variable with a conjugate prior can always be written in closed form (provided that the [normalizing factor](https://en.wikipedia.org/wiki/Normalizing_factor) of the exponential-family distribution can itself be written in closed form).
- In the mean-field approximation in [variational Bayes](https://en.wikipedia.org/wiki/Variational_Bayes) (used for approximating the [posterior distribution](https://en.wikipedia.org/wiki/Posterior_distribution) in large [Bayesian networks](https://en.wikipedia.org/wiki/Bayesian_network)), the best approximating posterior distribution of an exponential-family node (a node is a random variable in the context of Bayesian networks) with a conjugate prior is in the same family as the node.

Given an exponential family defined by $f_{X}{\!(x\mid \theta )}=h(x)\exp \left[\theta \cdot T(x)-A(\theta )\right]$, where $\Theta$ is the parameter space, such that $\theta \in \Theta \subset \mathbb {R} ^{k}$. Then

- If $\Theta$ has nonempty interior in $\mathbb {R} ^{k}$, then given any [IID samples](https://en.wikipedia.org/wiki/Independent_and_identically_distributed_random_variables) $X_{1},...,X_{n}\sim f_{X}$, the statistic $T(X_{1},\dots ,X_{n}):=\sum _{i=1}^{n}T(X_{i})$ is a complete statistic for $\theta$.
- $T$ is a minimal statistic for $\theta$ [if and only if](https://en.wikipedia.org/wiki/If_and_only_if) for all $\theta _{1},\theta _{2}\in \Theta$, and $x_{1},x_{2}$ in the support of $X$, if $(\theta _{1}-\theta _{2})\cdot [T(x_{1})-T(x_{2})]=0$, then $\theta _{1}=\theta _{2}$ or $x_{1}=x_{2}$.

## Examples

It is critical, when considering the examples in this section, to remember the discussion above about what it means to say that a "distribution" is an exponential family, and in particular to keep in mind that the set of parameters that are allowed to vary is critical in determining whether a "distribution" is or is not an exponential family.

The [normal](https://en.wikipedia.org/wiki/Normal_distribution), [exponential](https://en.wikipedia.org/wiki/Exponential_distribution), [log-normal](https://en.wikipedia.org/wiki/Log-normal_distribution), [gamma](https://en.wikipedia.org/wiki/Gamma_distribution), [chi-squared](https://en.wikipedia.org/wiki/Chi-squared_distribution), [beta](https://en.wikipedia.org/wiki/Beta_distribution), [Dirichlet](https://en.wikipedia.org/wiki/Dirichlet_distribution), [Bernoulli](https://en.wikipedia.org/wiki/Bernoulli_distribution), [categorical](https://en.wikipedia.org/wiki/Categorical_distribution), [Poisson](https://en.wikipedia.org/wiki/Poisson_distribution), [geometric](https://en.wikipedia.org/wiki/Geometric_distribution), [inverse Gaussian](https://en.wikipedia.org/wiki/Inverse_Gaussian_distribution), [ALAAM](https://en.wikipedia.org/wiki/Autologistic_actor_attribute_models), [von Mises](https://en.wikipedia.org/wiki/Von_Mises_distribution), and [von Mises-Fisher](https://en.wikipedia.org/wiki/Von_Mises-Fisher_distribution) distributions are all exponential families.

Some distributions are exponential families only if some of their parameters are held fixed. The family of [Pareto distributions](https://en.wikipedia.org/wiki/Pareto_distribution) with a fixed minimum bound *x*<sub>m</sub> form an exponential family. The families of [binomial](https://en.wikipedia.org/wiki/Binomial_distribution) and [multinomial](https://en.wikipedia.org/wiki/Multinomial_distribution) distributions with fixed number of trials *n* but unknown probability parameter(s) are exponential families. The family of [negative binomial distributions](https://en.wikipedia.org/wiki/Negative_binomial_distribution) with fixed number of failures (a.k.a. stopping-time parameter) *r* is an exponential family. However, when any of the above-mentioned fixed parameters are allowed to vary, the resulting family is not an exponential family.

As mentioned above, as a general rule, the [support](https://en.wikipedia.org/wiki/Support_(mathematics) "Support (mathematics)") of an exponential family must remain the same across all parameter settings in the family. This is why the above cases (e.g. binomial with varying number of trials, Pareto with varying minimum bound) are not exponential families — in all of the cases, the parameter in question affects the support (particularly, changing the minimum or maximum possible value). For similar reasons, neither the [discrete uniform distribution](https://en.wikipedia.org/wiki/Discrete_uniform_distribution) nor [continuous uniform distribution](https://en.wikipedia.org/wiki/Continuous_uniform_distribution) are exponential families as one or both bounds vary.

The [Weibull distribution](https://en.wikipedia.org/wiki/Weibull_distribution) with fixed shape parameter *k* is an exponential family. Unlike in the previous examples, the shape parameter does not affect the support; the fact that allowing it to vary makes the Weibull non-exponential is due rather to the particular form of the Weibull's [[Probability Density Function]] (*k* appears in the exponent of an exponent).

In general, distributions that result from a finite or infinite [mixture](https://en.wikipedia.org/wiki/Mixture_distribution) of other distributions, e.g. [mixture model](https://en.wikipedia.org/wiki/Mixture_model) densities and [compound probability distributions](https://en.wikipedia.org/wiki/Compound_probability_distribution), are *not* exponential families. Examples are typical Gaussian [mixture models](https://en.wikipedia.org/wiki/Mixture_model) as well as many [heavy-tailed distributions](https://en.wikipedia.org/wiki/Heavy-tailed_distribution) that result from [compounding](https://en.wikipedia.org/wiki/Compound_probability_distribution) (i.e. infinitely mixing) a distribution with a [prior distribution](https://en.wikipedia.org/wiki/Prior_distribution) over one of its parameters, e.g. the [Student's *t*-distribution](https://en.wikipedia.org/wiki/Student%27s_t-distribution) (compounding a [normal distribution](https://en.wikipedia.org/wiki/Normal_distribution) over a [gamma-distributed](https://en.wikipedia.org/wiki/Gamma_distribution) precision prior), and the [beta-binomial](https://en.wikipedia.org/wiki/Beta-binomial_distribution) and [Dirichlet-multinomial](https://en.wikipedia.org/wiki/Dirichlet-multinomial_distribution) distributions. Other examples of distributions that are not exponential families are the [F-distribution](https://en.wikipedia.org/wiki/F-distribution), [Cauchy distribution](https://en.wikipedia.org/wiki/Cauchy_distribution), [hypergeometric distribution](https://en.wikipedia.org/wiki/Hypergeometric_distribution) and [logistic distribution](https://en.wikipedia.org/wiki/Logistic_distribution).

Following are some detailed examples of the representation of some useful distribution as exponential families.

### Normal distribution: unknown mean, known variance

As a first example, consider a random variable distributed normally with unknown mean μ and *known* variance *σ*<sup>2</sup>. The probability density function is then

$$
f_{\sigma }(x;\mu )={\frac {1}{\sqrt {2\pi \sigma ^{2}}}}e^{-(x-\mu )^{2}/2\sigma ^{2}}.
$$

This is a single-parameter exponential family, as can be seen by setting

$$
{\begin{aligned}T_{\sigma }(x)&={\frac {x}{\sigma }},&h_{\sigma }(x)&={\frac {1}{\sqrt {2\pi \sigma ^{2}}}}e^{-x^{2}/2\sigma ^{2}},\\[4pt]A_{\sigma }(\mu )&={\frac {\mu ^{2}}{2\sigma ^{2}}},&\eta _{\sigma }(\mu )&={\frac {\mu }{\sigma }}.\end{aligned}}
$$

If *σ* = 1 this is in canonical form, as then *η*(*μ*) = *μ*.

### Normal distribution: unknown mean and unknown variance

Next, consider the case of a normal distribution with unknown mean and unknown variance. The probability density function is then

$$
f(y;\mu ,\sigma ^{2})={\frac {1}{\sqrt {2\pi \sigma ^{2}}}}e^{-(y-\mu )^{2}/2\sigma ^{2}}.
$$

This is an exponential family which can be written in canonical form by defining

$$
{\begin{aligned}h(y)&={\frac {1}{\sqrt {2\pi }}},&{\boldsymbol {\eta }}&=\left[{\frac {\mu }{\sigma ^{2}}},~-{\frac {1}{2\sigma ^{2}}}\right],\\T(y)&=\left(y,y^{2}\right)^{\mathsf {T}},&A({\boldsymbol {\eta }})&={\frac {\mu ^{2}}{2\sigma ^{2}}}+\log |\sigma |=-{\frac {\eta _{1}^{2}}{4\eta _{2}}}+{\frac {1}{2}}\log \left|{\frac {1}{2\eta _{2}}}\right|\end{aligned}}
$$

### Binomial distribution

As an example of a discrete exponential family, consider the [binomial distribution](https://en.wikipedia.org/wiki/Binomial_distribution) with *known* number of trials n. The [probability mass function](https://en.wikipedia.org/wiki/Probability_mass_function) for this distribution is 

$$
f(x)={\binom {n}{x}}p^{x}{\left(1-p\right)}^{n-x},\quad x\in \{0,1,2,\ldots ,n\}.
$$

 This can equivalently be written as 

$$
f(x)={\binom {n}{x}}\exp \left[x\log \left({\frac {p}{1-p}}\right)+n\log(1-p)\right],
$$

 which shows that the binomial distribution is an exponential family, whose natural parameter is 

$$
\eta =\log {\frac {p}{1-p}}.
$$

 This function of *p* is known as [logit](https://en.wikipedia.org/wiki/Logit).

## Table of distributions

The following table shows how to rewrite a number of common distributions as exponential-family distributions with natural parameters. Refer to the flashcards for main exponential families.

For a scalar variable and scalar parameter, the form is as follows:

$$
f_{X}(x\mid \theta )=h(x)\exp \left[\eta ({\theta })T(x)-A(\eta )\right]
$$

For a scalar variable and vector parameter:

$$
{\begin{aligned}f_{X}(x\mid {\boldsymbol {\theta }})&=h(x)\,\exp \left[{\boldsymbol {\eta }}({\boldsymbol {\theta }})\cdot \mathbf {T} (x)-A({\boldsymbol {\eta }})\right]\\[4pt]f_{X}(x\mid {\boldsymbol {\theta }})&=h(x)\,g({\boldsymbol {\theta }})\,\exp \left[{\boldsymbol {\eta }}({\boldsymbol {\theta }})\cdot \mathbf {T} (x)\right]\end{aligned}}
$$

For a vector variable and vector parameter:

$$
f_{X}(\mathbf {x} \mid {\boldsymbol {\theta }})=h(\mathbf {x} )\,\exp \left[{\boldsymbol {\eta }}({\boldsymbol {\theta }})\cdot \mathbf {T} (\mathbf {x} )-A({\boldsymbol {\eta }})\right]
$$

The above formulas choose the functional form of the exponential-family with a log-partition function $A({\boldsymbol {\eta }})$. The reason for this is so that the [moments of the sufficient statistics](#Moments_and_cumulants_of_the_sufficient_statistic) can be calculated easily, simply by differentiating this function. Alternative forms involve either parameterizing this function in terms of the normal parameter ${\boldsymbol {\theta }}$ instead of the natural parameter, and/or using a factor $g({\boldsymbol {\eta }})$ outside of the exponential. The relation between the latter and the former is: 

$$
{\begin{aligned}A({\boldsymbol {\eta }})&=-\log g({\boldsymbol {\eta }}),\\[2pt]g({\boldsymbol {\eta }})&=e^{-A({\boldsymbol {\eta }})}\end{aligned}}
$$

 To convert between the representations involving the two types of parameter, use the formulas below for writing one type of parameter in terms of the other.

<table class="wikitable">

Distribution
Parameter(s) <strong>θ</strong>
Natural parameter(s) <strong>η</strong>
Inverse parameter mapping
Base measure <em>h</em>(<em>x</em>)
Sufficient statistic <em>T</em>(<em>x</em>)
Log-partition <em>A</em>(<em>η</em>)
Log-partition <em>A</em>(<em>θ</em>)

&#10;
[Bernoulli distribution](https://en.wikipedia.org/wiki/Bernoulli_distribution)
$p$
$\log {\frac {p}{1-p}}$<br />
This is the [logit function](https://en.wikipedia.org/wiki/Logit_function).
${\frac {1}{1+e^{-\eta }}}={\frac {e^{\eta }}{1+e^{\eta }}}$<br />
This is the [logistic function](https://en.wikipedia.org/wiki/Logistic_function).
$1$
$x$
$\log(1+e^{\eta })$
$-\log(1-p)$

[binomial distribution](https://en.wikipedia.org/wiki/Binomial_distribution)<br />
with known number of trials $n$
$p$
$\log {\frac {p}{1-p}}$
${\frac {1}{1+e^{-\eta }}}={\frac {e^{\eta }}{1+e^{\eta }}}$
${\binom {n}{x}}$
$x$
$n\log(1+e^{\eta })$
$-n\log(1-p)$

[Poisson distribution](https://en.wikipedia.org/wiki/Poisson_distribution)
$\lambda$
$\log \lambda$
$e^{\eta }$
${\frac {1}{x!}}$
$x$
$e^{\eta }$
$\lambda$

[negative binomial distribution](https://en.wikipedia.org/wiki/Negative_binomial_distribution)<br />
with known number of failures $r$
$p$
$\log(1-p)$
$1-e^{\eta }$
${\binom {x{+}r{-}1}{x}}$
$x$
$-r\log(1-e^{\eta })$
$-r\log(p)$

[exponential distribution](https://en.wikipedia.org/wiki/Exponential_distribution)
$\lambda$
$-\lambda$
$-\eta$
$1$
$x$
$-\log(-\eta )$
$-\log \lambda$

[Pareto distribution](https://en.wikipedia.org/wiki/Pareto_distribution)<br />
with known minimum value $x_{m}$
$\alpha$
$-\alpha -1$
$-1-\eta$
$1$
$\log x$
${\begin{aligned}&-\log(-1-\eta )\\&+(1+\eta )\log x_{\mathrm {m} }\end{aligned}}$
$-\log \left(\alpha x_{\mathrm {m} }^{\alpha }\right)$

[Weibull distribution](https://en.wikipedia.org/wiki/Weibull_distribution)<br />
with known shape k
$\lambda$
$-{\frac {1}{\lambda ^{k}}}$
$(-\eta )^{-1/k}$
$x^{k-1}$
$x^{k}$
$\log \left(-{\frac {1}{\eta k}}\right)$
$\log {\frac {\lambda ^{k}}{k}}$

[Laplace distribution](https://en.wikipedia.org/wiki/Laplace_distribution)<br />
with known mean $\mu$
$b$
$-{\frac {1}{b}}$
$-{\frac {1}{\eta }}$
$1$
$|x-\mu |$
$\log \left(-{\frac {2}{\eta }}\right)$
$\log 2b$

[chi-squared distribution](https://en.wikipedia.org/wiki/Chi-squared_distribution)
$\nu$
${\frac {\nu }{2}}-1$
$2(\eta +1)$
$e^{-x/2}$
$\log x$
${\begin{aligned}&\log \Gamma (\eta +1)\\&+(\eta +1)\log 2\end{aligned}}$
${\begin{aligned}&\log \Gamma {\left({\tfrac {\nu }{2}}\right)}\\&+{\tfrac {\nu }{2}}\log 2\end{aligned}}$

[normal distribution](https://en.wikipedia.org/wiki/Normal_distribution)<br />
known variance
$\mu$
${\frac {\mu }{\sigma }}$
$\sigma \eta$
${\frac {e^{-x^{2}/(2\sigma ^{2})}}{{\sqrt {2\pi }}\sigma }}$
${\frac {x}{\sigma }}$
${\frac {\eta ^{2}}{2}}$
${\frac {\mu ^{2}}{2\sigma ^{2}}}$

[continuous Bernoulli distribution](https://en.wikipedia.org/wiki/Continuous_Bernoulli_distribution)
$\lambda$
$\log {\frac {\lambda }{1-\lambda }}$
${\frac {e^{\eta }}{1+e^{\eta }}}$
$1$
$x$
$\log {\frac {e^{\eta }-1}{\eta }}$
${\begin{aligned}&\log \left({\tfrac {1-2\lambda }{1-\lambda }}\right)\\[1ex]{}-{}&\log ^{2}\left({\tfrac {1}{\lambda }}-1\right)\end{aligned}}$
<p><br />
where log<sup>2</sup> refers to the [iterated logarithm](https://en.wikipedia.org/wiki/Iterated_logarithm)</p>

[normal distribution](https://en.wikipedia.org/wiki/Normal_distribution)
$\mu ,\ \sigma ^{2}$
${\begin{bmatrix}{\dfrac {\mu }{\sigma ^{2}}}\\[1ex]-{\dfrac {1}{2\sigma ^{2}}}\end{bmatrix}}$
${\begin{bmatrix}-{\dfrac {\eta _{1}}{2\eta _{2}}}\\[1ex]-{\dfrac {1}{2\eta _{2}}}\end{bmatrix}}$
${\frac {1}{\sqrt {2\pi }}}$
${\begin{bmatrix}x\\x^{2}\end{bmatrix}}$
$-{\frac {\eta _{1}^{2}}{4\eta _{2}}}-{\frac {1}{2}}\log(-2\eta _{2})$
${\frac {\mu ^{2}}{2\sigma ^{2}}}+\log \sigma$

[log-normal distribution](https://en.wikipedia.org/wiki/Log-normal_distribution)
$\mu ,\ \sigma ^{2}$
${\begin{bmatrix}{\dfrac {\mu }{\sigma ^{2}}}\\[1ex]-{\dfrac {1}{2\sigma ^{2}}}\end{bmatrix}}$
${\begin{bmatrix}-{\dfrac {\eta _{1}}{2\eta _{2}}}\\[1ex]-{\dfrac {1}{2\eta _{2}}}\end{bmatrix}}$
${\frac {1}{{\sqrt {2\pi }}x}}$
${\begin{bmatrix}\log x\\(\log x)^{2}\end{bmatrix}}$
$-{\frac {\eta _{1}^{2}}{4\eta _{2}}}-{\frac {1}{2}}\log(-2\eta _{2})$
${\frac {\mu ^{2}}{2\sigma ^{2}}}+\log \sigma$

[inverse Gaussian distribution](https://en.wikipedia.org/wiki/Inverse_Gaussian_distribution)
$\mu ,\ \lambda$
${\begin{bmatrix}-{\dfrac {\lambda }{2\mu ^{2}}}\\[15pt]-{\dfrac {\lambda }{2}}\end{bmatrix}}$
${\begin{bmatrix}{\sqrt {\dfrac {\eta _{2}}{\eta _{1}}}}\\[15pt]-2\eta _{2}\end{bmatrix}}$
${\frac {1}{{\sqrt {2\pi }}x^{3/2}}}$
${\begin{bmatrix}x\\[5pt]{\dfrac {1}{x}}\end{bmatrix}}$
$-2{\sqrt {\eta _{1}\eta _{2}}}-{\tfrac {1}{2}}\log(-2\eta _{2})$
$-{\tfrac {\lambda }{\mu }}-{\tfrac {1}{2}}\log \lambda$

[gamma distribution](https://en.wikipedia.org/wiki/Gamma_distribution)
$\alpha ,\ \beta$
${\begin{bmatrix}\alpha -1\\-\beta \end{bmatrix}}$
${\begin{bmatrix}\eta _{1}+1\\-\eta _{2}\end{bmatrix}}$
$1$
${\begin{bmatrix}\log x\\x\end{bmatrix}}$
${\begin{aligned}&\log \Gamma (\eta _{1}+1)\\{}-{}&(\eta _{1}+1)\log(-\eta _{2})\end{aligned}}$
$\log {\frac {\Gamma (\alpha )}{\beta ^{\alpha }}}$

$k,\ \theta$
${\begin{bmatrix}k-1\\[5pt]-{\dfrac {1}{\theta }}\end{bmatrix}}$
${\begin{bmatrix}\eta _{1}+1\\[5pt]-{\dfrac {1}{\eta _{2}}}\end{bmatrix}}$
$\log \left(\theta ^{k}\Gamma (k)\right)$

[inverse gamma distribution](https://en.wikipedia.org/wiki/Inverse_gamma_distribution)
$\alpha ,\ \beta$
${\begin{bmatrix}-\alpha -1\\-\beta \end{bmatrix}}$
${\begin{bmatrix}-\eta _{1}-1\\-\eta _{2}\end{bmatrix}}$
$1$
${\begin{bmatrix}\log x\\{\frac {1}{x}}\end{bmatrix}}$
${\begin{aligned}&\log \Gamma (-\eta _{1}-1)\\+&\left(\eta _{1}+1\right)\log(-\eta _{2})\end{aligned}}$
$\log {\frac {\Gamma (\alpha )}{\beta ^{\alpha }}}$

[generalized inverse Gaussian distribution](https://en.wikipedia.org/wiki/Generalized_inverse_Gaussian_distribution)
$p,\ a,\ b$
${\begin{bmatrix}p-1\\-a/2\\-b/2\end{bmatrix}}$
${\begin{bmatrix}\eta _{1}+1\\-2\eta _{2}\\-2\eta _{3}\end{bmatrix}}$
$1$
${\begin{bmatrix}\log x\\x\\{\frac {1}{x}}\end{bmatrix}}$
${\begin{aligned}&\log 2K_{\eta _{1}+1}{\!\left({\sqrt {4\eta _{2}\eta _{3}}}\right)}\\[2pt]{}-{}&{\frac {\eta _{1}+1}{2}}\log {\frac {\eta _{2}}{\eta _{3}}}\end{aligned}}$
${\begin{aligned}&\log 2K_{p}({\sqrt {ab}})\\[2pt]&{}-{\frac {p}{2}}\log {\frac {a}{b}}\end{aligned}}$

[scaled inverse chi-squared distribution](https://en.wikipedia.org/wiki/Scaled_inverse_chi-squared_distribution)
$\nu ,\ \sigma ^{2}$
${\begin{bmatrix}-{\dfrac {\nu }{2}}-1\\[10pt]-{\dfrac {\nu \sigma ^{2}}{2}}\end{bmatrix}}$
${\begin{bmatrix}-2(\eta _{1}+1)\\[10pt]{\dfrac {\eta _{2}}{\eta _{1}+1}}\end{bmatrix}}$
$1$
${\begin{bmatrix}\log x\\{\frac {1}{x}}\end{bmatrix}}$
${\begin{aligned}&\log \Gamma (-\eta _{1}-1)\\[2pt]+&\left(\eta _{1}+1\right)\log(-\eta _{2})\end{aligned}}$
${\begin{aligned}&\log \Gamma {\left({\frac {\nu }{2}}\right)}\\[2pt]{}-{}&{\frac {\nu }{2}}\log {\frac {\nu \sigma ^{2}}{2}}\end{aligned}}$

[beta distribution](https://en.wikipedia.org/wiki/Beta_distribution)<br />
(variant 1)
$\alpha ,\ \beta$
${\begin{bmatrix}\alpha \\\beta \end{bmatrix}}$
${\begin{bmatrix}\eta _{1}\\\eta _{2}\end{bmatrix}}$
${\frac {1}{x(1-x)}}$
${\begin{bmatrix}\log x\\\log(1{-}x)\end{bmatrix}}$
$\log {\frac {\Gamma (\eta _{1})\,\Gamma (\eta _{2})}{\Gamma (\eta _{1}+\eta _{2})}}$
$\log {\frac {\Gamma (\alpha )\,\Gamma (\beta )}{\Gamma (\alpha +\beta )}}$

[beta distribution](https://en.wikipedia.org/wiki/Beta_distribution)<br />
(variant 2)
$\alpha ,\ \beta$
${\begin{bmatrix}\alpha -1\\\beta -1\end{bmatrix}}$
${\begin{bmatrix}\eta _{1}+1\\\eta _{2}+1\end{bmatrix}}$
$1$
${\begin{bmatrix}\log x\\\log(1{-}x)\end{bmatrix}}$
$\log {\frac {\Gamma (\eta _{1}+1)\,\Gamma (\eta _{2}+1)}{\Gamma (\eta _{1}+\eta _{2}+2)}}$
$\log {\frac {\Gamma (\alpha )\,\Gamma (\beta )}{\Gamma (\alpha +\beta )}}$

[[Multivariate Normal Distribution]]
${\boldsymbol {\mu }},\ {\boldsymbol {\Sigma }}$
${\begin{bmatrix}{\boldsymbol {\Sigma }}^{-1}{\boldsymbol {\mu }}\\[5pt]-{\frac {1}{2}}{\boldsymbol {\Sigma }}^{-1}\end{bmatrix}}$
${\begin{bmatrix}-{\frac {1}{2}}{\boldsymbol {\eta }}_{2}^{-1}{\boldsymbol {\eta }}_{1}\\[5pt]-{\frac {1}{2}}{\boldsymbol {\eta }}_{2}^{-1}\end{bmatrix}}$
$(2\pi )^{-{\frac {k}{2}}}$
${\begin{bmatrix}\mathbf {x} \\[5pt]\mathbf {x} \mathbf {x} ^{\mathsf {T}}\end{bmatrix}}$
${\begin{aligned}&-{\tfrac {1}{4}}{\boldsymbol {\eta }}_{1}^{\mathsf {T}}{\boldsymbol {\eta }}_{2}^{-1}{\boldsymbol {\eta }}_{1}\\&-{\tfrac {1}{2}}\log \left|-2{\boldsymbol {\eta }}_{2}\right|\end{aligned}}$
${\begin{aligned}&{\tfrac {1}{2}}{\boldsymbol {\mu }}^{\mathsf {T}}{\boldsymbol {\Sigma }}^{-1}{\boldsymbol {\mu }}\\+&{\tfrac {1}{2}}\log \left|{\boldsymbol {\Sigma }}\right|\end{aligned}}$

[categorical distribution](https://en.wikipedia.org/wiki/Categorical_distribution)<br />
(variant 1)
$p_{1},\ \ldots ,\,p_{k}$<br />
where $\sum \limits _{i=1}^{k}p_{i}=1$
${\begin{bmatrix}\log p_{1}\\\vdots \\\log p_{k}\end{bmatrix}}$
${\begin{bmatrix}e^{\eta _{1}}\\\vdots \\e^{\eta _{k}}\end{bmatrix}}$<br />
where $\sum \limits _{i=1}^{k}e^{\eta _{i}}=1$
$1$
${\begin{bmatrix}[x=1]\\\vdots \\{[x=k]}\end{bmatrix}}$$[x=i]$ is the [Iverson bracket](https://en.wikipedia.org/wiki/Iverson_bracket)
$0$
$0$

[categorical distribution](https://en.wikipedia.org/wiki/Categorical_distribution)<br />
(variant 2)
$p_{1},\ \ldots ,\,p_{k}$<br />
where $\sum \limits _{i=1}^{k}p_{i}=1$
${\begin{bmatrix}\log p_{1}+C\\\vdots \\\log p_{k}+C\end{bmatrix}}$
${\frac {1}{C}}{\begin{bmatrix}e^{\eta _{1}}\\\vdots \\e^{\eta _{k}}\end{bmatrix}}$where $C=\sum \limits _{i=1}^{k}e^{\eta _{i}}$
$1$
${\begin{bmatrix}[x=1]\\\vdots \\{[x=k]}\end{bmatrix}}$$[x=i]$ is the [Iverson bracket](https://en.wikipedia.org/wiki/Iverson_bracket)
$0$
$0$

[categorical distribution](https://en.wikipedia.org/wiki/Categorical_distribution)<br />
(variant 3)
$p_{1},\ \ldots ,\,p_{k}$<br />
where $p_{k}=1-\sum \limits _{i=1}^{k-1}p_{i}$
${\begin{bmatrix}\log {\dfrac {p_{1}}{p_{k}}}\\[10pt]\vdots \\[5pt]\log {\dfrac {p_{k-1}}{p_{k}}}\\[15pt]0\end{bmatrix}}$
<p>This is the inverse [softmax function](https://en.wikipedia.org/wiki/Softmax_function), a generalization of the [logit function](https://en.wikipedia.org/wiki/Logit_function).</p>
${\frac {1}{C_{1}}}{\begin{bmatrix}e^{\eta _{1}}\\[5pt]\vdots \\[5pt]e^{\eta _{k}}\end{bmatrix}}=$
<p><br />
${\frac {1}{C_{2}}}{\begin{bmatrix}e^{\eta _{1}}\\[5pt]\vdots \\[5pt]e^{\eta _{k-1}}\\[5pt]1\end{bmatrix}}$<br />
where $C_{1}=\sum \limits _{i=1}^{k}e^{\eta _{i}}$ and $C_{2}=1+\sum \limits _{i=1}^{k-1}e^{\eta _{i}}$.</p>
<p>This is the [softmax function](https://en.wikipedia.org/wiki/Softmax_function), a generalization of the [logistic function](https://en.wikipedia.org/wiki/Logistic_function).</p>
$1$
${\begin{bmatrix}[x=1]\\\vdots \\{[x=k]}\end{bmatrix}}$$[x=i]$ is the [Iverson bracket](https://en.wikipedia.org/wiki/Iverson_bracket)
${\begin{aligned}&\textstyle \log \left(\sum \limits _{i=1}^{k}e^{\eta _{i}}\right)\\={}&\textstyle \log \left(1+\sum \limits _{i=1}^{k-1}e^{\eta _{i}}\right)\end{aligned}}$
$-\log p_{k}$

[multinomial distribution](https://en.wikipedia.org/wiki/Multinomial_distribution)<br />
(variant 1)<br />
with known number of trials n
$p_{1},\ \ldots ,\,p_{k}$<br />
where $\sum \limits _{i=1}^{k}p_{i}=1$
${\begin{bmatrix}\log p_{1}\\\vdots \\\log p_{k}\end{bmatrix}}$
${\begin{bmatrix}e^{\eta _{1}}\\\vdots \\e^{\eta _{k}}\end{bmatrix}}$<br />
where $\sum \limits _{i=1}^{k}e^{\eta _{i}}=1$
${\frac {n!}{\prod \limits _{i=1}^{k}x_{i}!}}$
${\begin{bmatrix}x_{1}\\\vdots \\x_{k}\end{bmatrix}}$
$0$
$0$

[multinomial distribution](https://en.wikipedia.org/wiki/Multinomial_distribution)<br />
(variant 2)<br />
with known number of trials $n$
$p_{1},\ \ldots ,\,p_{k}$<br />
where $\sum \limits _{i=1}^{k}p_{i}=1$
${\begin{bmatrix}\log p_{1}+C\\\vdots \\\log p_{k}+C\end{bmatrix}}$
${\frac {1}{C}}{\begin{bmatrix}e^{\eta _{1}}\\\vdots \\e^{\eta _{k}}\end{bmatrix}}$<br />
&#10;<p>where $C=\sum \limits _{i=1}^{k}e^{\eta _{i}}$</p>
${\frac {n!}{\prod \limits _{i=1}^{k}x_{i}!}}$
${\begin{bmatrix}x_{1}\\\vdots \\x_{k}\end{bmatrix}}$
$0$
$0$

[multinomial distribution](https://en.wikipedia.org/wiki/Multinomial_distribution)<br />
(variant 3)<br />
with known number of trials $n$
$p_{1},\ \ldots ,\,p_{k}$<br />
where $p_{k}=1-\sum \limits _{i=1}^{k-1}p_{i}$
${\begin{bmatrix}\log {\dfrac {p_{1}}{p_{k}}}\\[10pt]\vdots \\[5pt]\log {\dfrac {p_{k-1}}{p_{k}}}\\[15pt]0\end{bmatrix}}$
${\frac {1}{C_{1}}}{\begin{bmatrix}e^{\eta _{1}}\\[10pt]\vdots \\[5pt]e^{\eta _{k}}\end{bmatrix}}=$<br />
&#10;<p>${\frac {1}{C_{2}}}{\begin{bmatrix}e^{\eta _{1}}\\[5pt]\vdots \\[5pt]e^{\eta _{k-1}}\\[5pt]1\end{bmatrix}}$</p>
<p>where $C_{1}=\sum \limits _{i=1}^{k}e^{\eta _{i}}$ and $C_{2}=1+\sum \limits _{i=1}^{k-1}e^{\eta _{i}}$</p>
${\frac {n!}{\prod \limits _{i=1}^{k}x_{i}!}}$
${\begin{bmatrix}x_{1}\\\vdots \\x_{k}\end{bmatrix}}$
${\begin{aligned}&\textstyle n\log \left(\sum \limits _{i=1}^{k}e^{\eta _{i}}\right)\\[4pt]={}&\textstyle n\log \left(1+\sum \limits _{i=1}^{k-1}e^{\eta _{i}}\right)\end{aligned}}$
$-n\log p_{k}$

[Dirichlet distribution](https://en.wikipedia.org/wiki/Dirichlet_distribution)<br />
(variant 1)
$\alpha _{1},\ \ldots ,\,\alpha _{k}$
${\begin{bmatrix}\alpha _{1}\\\vdots \\\alpha _{k}\end{bmatrix}}$
${\begin{bmatrix}\eta _{1}\\\vdots \\\eta _{k}\end{bmatrix}}$
${\frac {1}{\prod \limits _{i=1}^{k}x_{i}}}$
${\begin{bmatrix}\log x_{1}\\\vdots \\\log x_{k}\end{bmatrix}}$
${\begin{aligned}\textstyle \sum \limits _{i=1}^{k}\log \Gamma (\eta _{i})\\\textstyle -\log \Gamma {\left(\sum \limits _{i=1}^{k}\eta _{i}\right)}\end{aligned}}$
${\begin{aligned}&\textstyle \sum \limits _{i=1}^{k}\log \Gamma (\alpha _{i})\\{}-{}&\textstyle \log \Gamma {\left(\sum \limits _{i=1}^{k}\alpha _{i}\right)}\end{aligned}}$

[Dirichlet distribution](https://en.wikipedia.org/wiki/Dirichlet_distribution)<br />
(variant 2)
$\alpha _{1},\ \ldots ,\,\alpha _{k}$
${\begin{bmatrix}\alpha _{1}-1\\\vdots \\\alpha _{k}-1\end{bmatrix}}$
${\begin{bmatrix}\eta _{1}+1\\\vdots \\\eta _{k}+1\end{bmatrix}}$
$1$
${\begin{bmatrix}\log x_{1}\\\vdots \\\log x_{k}\end{bmatrix}}$
${\begin{aligned}&\textstyle \sum \limits _{i=1}^{k}\log \Gamma (\eta _{i}+1)\\{}-{}&\textstyle \log \Gamma {\left(\sum \limits _{i=1}^{k}(\eta _{i}+1)\right)}\end{aligned}}$
${\begin{aligned}&\textstyle \sum \limits _{i=1}^{k}\log \Gamma (\alpha _{i})\\{}-{}&\textstyle \log \Gamma {\left(\sum \limits _{i=1}^{k}\alpha _{i}\right)}\end{aligned}}$

[Wishart distribution](https://en.wikipedia.org/wiki/Wishart_distribution)
$\mathbf {V} ,\ n$
${\begin{bmatrix}-{\frac {1}{2}}\mathbf {V} ^{-1}\\[5pt]{\dfrac {n{-}p{-}1}{2}}\end{bmatrix}}$
${\begin{bmatrix}-{\frac {1}{2}}{\boldsymbol {\eta }}_{1}^{-1}\\[5pt]2\eta _{2}{+}p{+}1\end{bmatrix}}$
$1$
${\begin{bmatrix}\mathbf {X} \\\log |\mathbf {X} |\end{bmatrix}}$
${\begin{aligned}&-\left[\eta _{2}+{\tfrac {p+1}{2}}\right]\log \left|-{\boldsymbol {\eta }}_{1}\right|\\&+\log \Gamma _{p}{\left(\eta _{2}+{\tfrac {p+1}{2}}\right)}\\[1ex]=&-{\tfrac {n}{2}}\log \left|-{\boldsymbol {\eta }}_{1}\right|\\&+\log \Gamma _{p}{\left({\tfrac {n}{2}}\right)}\\[1ex]={}&\left[\eta _{2}+{\tfrac {p+1}{2}}\right]\log \left(2^{p}\left|\mathbf {V} \right|\right)\\&+\log \Gamma _{p}{\left(\eta _{2}+{\tfrac {p+1}{2}}\right)}\end{aligned}}$
<p><br />
Three variants with different parameterizations are given, to facilitate computing moments of the sufficient statistics.</p>
${\begin{aligned}&{\frac {n}{2}}\log \left(2^{p}\left|\mathbf {V} \right|\right)\\[2pt]&+\log \Gamma _{p}{\left({\frac {n}{2}}\right)}\end{aligned}}$

<strong>Note</strong>: Uses the fact that $\operatorname {tr} (\mathbf {A} ^{\mathsf {T}}\mathbf {B} )=\operatorname {vec} (\mathbf {A} )\cdot \operatorname {vec} (\mathbf {B} ),$ i.e. the [trace](https://en.wikipedia.org/wiki/Trace_(linear_algebra)) of a [matrix product](https://en.wikipedia.org/wiki/Matrix_product) is much like a [dot product](https://en.wikipedia.org/wiki/Dot_product). The matrix parameters are assumed to be [vectorized](https://en.wikipedia.org/wiki/Vectorization_(mathematics)) (laid out in a vector) when inserted into the exponential form. Also, $\mathbf {V}$ and $\mathbf {X}$ are symmetric, so e.g. $\mathbf {V} ^{\mathsf {T}}=\mathbf {V} \ .$

[inverse Wishart distribution](https://en.wikipedia.org/wiki/Inverse_Wishart_distribution)
$\mathbf {\Psi } ,\,m$
$-{\frac {1}{2}}{\begin{bmatrix}{\boldsymbol {\Psi }}\\[5pt]m{+}p{+}1\end{bmatrix}}$
$-{\begin{bmatrix}2{\boldsymbol {\eta }}_{1}\\[5pt]2\eta _{2}{+}p{+}1\end{bmatrix}}$
$1$
${\begin{bmatrix}\mathbf {X} ^{-1}\\\log |\mathbf {X} |\end{bmatrix}}$
${\begin{aligned}&\left[\eta _{2}+{\tfrac {p+1}{2}}\right]\log \left|-{\boldsymbol {\eta }}_{1}\right|\\&+\log \Gamma _{p}{\left(-\eta _{2}-{\tfrac {p+1}{2}}\right)}\\[1ex]=&-{\tfrac {m}{2}}\log \left|-{\boldsymbol {\eta }}_{1}\right|\\&+\log \Gamma _{p}{\left({\tfrac {m}{2}}\right)}\\[1ex]=&-\left[\eta _{2}+{\tfrac {p+1}{2}}\right]\log {\tfrac {2^{p}}{\left|{\boldsymbol {\Psi }}\right|}}\\&+\log \Gamma _{p}{\left(-\eta _{2}-{\tfrac {p+1}{2}}\right)}\end{aligned}}$
${\begin{aligned}{\frac {m}{2}}\log {\frac {2^{p}}{|{\boldsymbol {\Psi }}|}}\\[4pt]+\log \Gamma _{p}{\left({\frac {m}{2}}\right)}\end{aligned}}$

[normal-gamma distribution](https://en.wikipedia.org/wiki/Normal-gamma_distribution)
$\alpha ,\ \beta ,\ \mu ,\ \lambda$
${\begin{bmatrix}\alpha -{\frac {1}{2}}\\-\beta -{\dfrac {\lambda \mu ^{2}}{2}}\\\lambda \mu \\-{\dfrac {\lambda }{2}}\end{bmatrix}}$
${\begin{bmatrix}\eta _{1}+{\frac {1}{2}}\\-\eta _{2}+{\dfrac {\eta _{3}^{2}}{4\eta _{4}}}\\-{\dfrac {\eta _{3}}{2\eta _{4}}}\\-2\eta _{4}\end{bmatrix}}$
${\dfrac {1}{\sqrt {2\pi }}}$
${\begin{bmatrix}\log \tau \\\tau \\\tau x\\\tau x^{2}\end{bmatrix}}$
${\begin{aligned}&\log \Gamma {\left(\eta _{1}+{\tfrac {1}{2}}\right)}\\[2pt]-{}&{\tfrac {1}{2}}\log \left(-2\eta _{4}\right)\\[2pt]-{}&\left(\eta _{1}+{\tfrac {1}{2}}\right)\log \left({\tfrac {\eta _{3}^{2}}{4\eta _{4}}}-\eta _{2}\right)\end{aligned}}$
${\begin{aligned}&\log \Gamma {\left(\alpha \right)}\\[2pt]&-\alpha \log \beta \\[2pt]&-{\tfrac {1}{2}}\log \lambda \end{aligned}}$

</table>

1.  ^    The [Iverson bracket](https://en.wikipedia.org/wiki/Iverson_bracket) is a generalization of the discrete delta-function: If the bracketed expression is true, the bracket has value 1; if the enclosed statement is false, the Iverson bracket is zero. There are many variant notations, e.g. wavey brackets: ⧙*a*=*b*⧘ is equivalent to the \[*a*=*b*\] notation used above.

The three variants of the [categorical distribution](https://en.wikipedia.org/wiki/Categorical_distribution) and [multinomial distribution](https://en.wikipedia.org/wiki/Multinomial_distribution) are due to the fact that the parameters $p_{i}$ are constrained, such that

$$
\sum _{i=1}^{k}p_{i}=1\,.
$$

Thus, there are only $k-1$ independent parameters.

- Variant 1 uses $k$ natural parameters with a simple relation between the standard and natural parameters; however, only $k-1$ of the natural parameters are independent, and the set of $k$ natural parameters is [nonidentifiable](https://en.wikipedia.org/wiki/Nonidentifiable). The constraint on the usual parameters translates to a similar constraint on the natural parameters.
- Variant 2 demonstrates the fact that the entire set of natural parameters is nonidentifiable: Adding any constant value to the natural parameters has no effect on the resulting distribution. However, by using the constraint on the natural parameters, the formula for the normal parameters in terms of the natural parameters can be written in a way that is independent on the constant that is added.
- Variant 3 shows how to make the parameters identifiable in a convenient way by setting $C=-\log p_{k}\ .$ This effectively "pivots" around $p_{k}$ and causes the last natural parameter to have the constant value of 0. All the remaining formulas are written in a way that does not access $p_{k}$, so that effectively the model has only $k-1$ parameters, both of the usual and natural kind.

Variants 1 and 2 are not actually standard exponential families at all. Rather they are *curved exponential families*, i.e. there are $k-1$ independent parameters embedded in a $k$-dimensional parameter space. Many of the standard results for exponential families do not apply to curved exponential families. An example is the log-partition function $A(x)$, which has the value of 0 in the curved cases. In standard exponential families, the derivatives of this function correspond to the moments (more technically, the [cumulants](https://en.wikipedia.org/wiki/Cumulant)) of the sufficient statistics, e.g. the mean and variance. However, a value of 0 suggests that the mean and variance of all the sufficient statistics are uniformly 0, whereas in fact the mean of the $i$th sufficient statistic should be $p_{i}$. (This does emerge correctly when using the form of $A(x)$ shown in variant 3.)

## Moments and cumulants of the sufficient statistic

### Normalization of the distribution

We start with the normalization of the probability distribution. In general, any non-negative function *f*(*x*) that serves as the [kernel](https://en.wikipedia.org/wiki/Kernel_(statistics) "Kernel (statistics)") of a probability distribution (the part encoding all dependence on *x*) can be made into a proper distribution by [normalizing](https://en.wikipedia.org/wiki/Normalization_factor): i.e.

$$
p(x)={\frac {1}{Z}}f(x)
$$

where

$$
Z=\int _{x}f(x)\,dx.
$$

The factor *Z* is sometimes termed the *normalizer* or *[partition function](https://en.wikipedia.org/wiki/Partition_function_(mathematics) "Partition function (mathematics)")*, based on an analogy to [statistical physics](https://en.wikipedia.org/wiki/Statistical_physics).

In the case of an exponential family where 

$$
p(x;{\boldsymbol {\eta }})=g({\boldsymbol {\eta }})h(x)e^{{\boldsymbol {\eta }}\cdot \mathbf {T} (x)},
$$

the kernel is 

$$
K(x)=h(x)e^{{\boldsymbol {\eta }}\cdot \mathbf {T} (x)}
$$

 and the partition function is 

$$
Z=\int _{x}h(x)e^{{\boldsymbol {\eta }}\cdot \mathbf {T} (x)}\,dx.
$$

Since the distribution must be normalized, we have

$$
{\begin{aligned}1&=\int _{x}g({\boldsymbol {\eta }})h(x)e^{{\boldsymbol {\eta }}\cdot \mathbf {T} (x)}\,dx\\&=g({\boldsymbol {\eta }})\int _{x}h(x)e^{{\boldsymbol {\eta }}\cdot \mathbf {T} (x)}\,dx\\[1ex]&=g({\boldsymbol {\eta }})Z.\end{aligned}}
$$

In other words, 

$$
g({\boldsymbol {\eta }})={\frac {1}{Z}}
$$

 or equivalently 

$$
A({\boldsymbol {\eta }})=-\log g({\boldsymbol {\eta }})=\log Z.
$$

This justifies calling *A* the *log-normalizer* or *log-partition function*.

### Moment-generating function of the sufficient statistic

Now, the [[Moment Generating Function|moment-generating function]] of *T*(*x*) is

$$
{\begin{aligned}M_{T}(u)&\equiv \operatorname {E} \left[\exp \left(u^{\mathsf {T}}T(x)\right)\mid \eta \right]\\&=\int _{x}h(x)\,\exp \left[(\eta +u)^{\mathsf {T}}T(x)-A(\eta )\right]\,dx\\[1ex]&=e^{A(\eta +u)-A(\eta )}\end{aligned}}
$$

proving the earlier statement that

$$
K(u\mid \eta )=A(\eta +u)-A(\eta )
$$

is the [cumulant generating function](https://en.wikipedia.org/wiki/Cumulant_generating_function) for *T*.

An important subclass of exponential families are the [natural exponential families](https://en.wikipedia.org/wiki/Natural_exponential_family), which have a similar form for the moment-generating function for the distribution of x.

#### Differential identities for cumulants

In particular, using the properties of the cumulant generating function,

$$
\operatorname {E} (T_{j})={\frac {\partial A(\eta )}{\partial \eta _{j}}}
$$

and

$$
\operatorname {cov} \left(T_{i},\,T_{j}\right)={\frac {\partial ^{2}A(\eta )}{\partial \eta _{i}\,\partial \eta _{j}}}.
$$

The first two raw moments and all mixed second moments can be recovered from these two identities. Higher-order moments and cumulants are obtained by higher derivatives. This technique is often useful when *T* is a complicated function of the data, whose moments are difficult to calculate by integration.

Another way to see this that does not rely on the theory of [cumulants](https://en.wikipedia.org/wiki/Cumulant) is to begin from the fact that the distribution of an exponential family must be normalized, and differentiate. We illustrate using the simple case of a one-dimensional parameter, but an analogous derivation holds more generally.

In the one-dimensional case, we have 

$$
p(x)=g(\eta )h(x)e^{\eta T(x)}.
$$

This must be normalized, so

$$
1=\int _{x}p(x)\,dx=\int _{x}g(\eta )h(x)e^{\eta T(x)}\,dx=g(\eta )\int _{x}h(x)e^{\eta T(x)}\,dx.
$$

Take the [derivative](https://en.wikipedia.org/wiki/Derivative) of both sides with respect to η:

$$
{\begin{aligned}0&=g(\eta ){\frac {d}{d\eta }}\int _{x}h(x)e^{\eta T(x)}\,dx+g'(\eta )\int _{x}h(x)e^{\eta T(x)}\,dx\\[1ex]&=g(\eta )\int _{x}h(x)\left({\frac {d}{d\eta }}e^{\eta T(x)}\right)\,dx+g'(\eta )\int _{x}h(x)e^{\eta T(x)}\,dx\\[1ex]&=g(\eta )\int _{x}h(x)e^{\eta T(x)}T(x)\,dx+g'(\eta )\int _{x}h(x)e^{\eta T(x)}\,dx\\[1ex]&=\int _{x}T(x)g(\eta )h(x)e^{\eta T(x)}\,dx+{\frac {g'(\eta )}{g(\eta )}}\int _{x}g(\eta )h(x)e^{\eta T(x)}\,dx\\[1ex]&=\int _{x}T(x)p(x)\,dx+{\frac {g'(\eta )}{g(\eta )}}\int _{x}p(x)\,dx\\[1ex]&=\operatorname {E} [T(x)]+{\frac {g'(\eta )}{g(\eta )}}\\[1ex]&=\operatorname {E} [T(x)]+{\frac {d}{d\eta }}\log g(\eta )\end{aligned}}
$$

Therefore, 

$$
\operatorname {E} [T(x)]=-{\frac {d}{d\eta }}\log g(\eta )={\frac {d}{d\eta }}A(\eta ).
$$

#### Example 1

As an introductory example, consider the [gamma distribution](https://en.wikipedia.org/wiki/Gamma_distribution), whose distribution is defined by

$$
p(x)={\frac {\beta ^{\alpha }}{\Gamma (\alpha )}}x^{\alpha -1}e^{-\beta x}.
$$

Referring to the above table, we can see that the natural parameter is given by

$$
{\begin{aligned}\eta _{1}&=\alpha -1,\\\eta _{2}&=-\beta ,\end{aligned}}
$$

the reverse substitutions are

$$
{\begin{aligned}\alpha &=\eta _{1}+1,\\\beta &=-\eta _{2},\end{aligned}}
$$

the sufficient statistics are (log *x*, x), and the log-partition function is

$$
A(\eta _{1},\eta _{2})=\log \Gamma (\eta _{1}+1)-(\eta _{1}+1)\log(-\eta _{2}).
$$

We can find the mean of the sufficient statistics as follows. First, for *η*<sub>1</sub>:

$$
{\begin{aligned}\operatorname {E} [\log x]&={\frac {\partial }{\partial \eta _{1}}}A(\eta _{1},\eta _{2})\\[0.5ex]&={\frac {\partial }{\partial \eta _{1}}}\left[\log \Gamma (\eta _{1}+1)-(\eta _{1}+1)\log(-\eta _{2})\right]\\[1ex]&=\psi (\eta _{1}+1)-\log(-\eta _{2})\\[1ex]&=\psi (\alpha )-\log \beta ,\end{aligned}}
$$

Where $\psi (x)$ is the [digamma function](https://en.wikipedia.org/wiki/Digamma_function) (derivative of log gamma), and we used the reverse substitutions in the last step.

Now, for *η*<sub>2</sub>:

$$
{\begin{aligned}\operatorname {E} [x]&={\frac {\partial }{\partial \eta _{2}}}A(\eta _{1},\eta _{2})\\[1ex]&={\frac {\partial }{\partial \eta _{2}}}\left[\log \Gamma (\eta _{1}+1)-(\eta _{1}+1)\log(-\eta _{2})\right]\\[1ex]&=-(\eta _{1}+1){\frac {1}{-\eta _{2}}}(-1)={\frac {\eta _{1}+1}{-\eta _{2}}}={\frac {\alpha }{\beta }},\end{aligned}}
$$

again making the reverse substitution in the last step.

To compute the variance of x, we just differentiate again:

$$
{\begin{aligned}\operatorname {Var} (x)&={\frac {\partial ^{2}}{\partial \eta _{2}^{2}}}A{\left(\eta _{1},\eta _{2}\right)}={\frac {\partial }{\partial \eta _{2}}}{\frac {\eta _{1}+1}{-\eta _{2}}}\\[1ex]&={\frac {\eta _{1}+1}{\eta _{2}^{2}}}={\frac {\alpha }{\beta ^{2}}}.\end{aligned}}
$$

All of these calculations can be done using integration, making use of various properties of the [gamma function](https://en.wikipedia.org/wiki/Gamma_function), but this requires significantly more work.

#### Example 2

As another example consider a real valued random variable X with density

$$
p_{\theta }(x)={\frac {\theta e^{-x}}{\left(1+e^{-x}\right)^{\theta +1}}}
$$

indexed by shape parameter $\theta \in (0,\infty )$ (this is called the [skew-logistic distribution](https://en.wikipedia.org/wiki/Skew-logistic_distribution)). The density can be rewritten as

$$
{\frac {e^{-x}}{1+e^{-x}}}\exp[-\theta \log \left(1+e^{-x})+\log(\theta )\right]
$$

Notice this is an exponential family with natural parameter

$$
\eta =-\theta ,
$$

sufficient statistic

$$
T=\log \left(1+e^{-x}\right),
$$

and log-partition function

$$
A(\eta )=-\log(\theta )=-\log(-\eta )
$$

So using the first identity,

$$
\operatorname {E} \left[\log \left(1+e^{-X}\right)\right]=\operatorname {E} (T)={\frac {\partial A(\eta )}{\partial \eta }}={\frac {\partial }{\partial \eta }}[-\log(-\eta )]={\frac {1}{-\eta }}={\frac {1}{\theta }},
$$

and using the second identity

$$
\operatorname {var} \left[\log \left(1+e^{-X}\right)\right]={\frac {\partial ^{2}A(\eta )}{\partial \eta ^{2}}}={\frac {\partial }{\partial \eta }}\left[{\frac {1}{-\eta }}\right]={\frac {1}{{\left(-\eta \right)}^{2}}}={\frac {1}{\theta ^{2}}}.
$$

This example illustrates a case where using this method is very simple, but the direct calculation would be nearly impossible.

#### Example 3

The final example is one where integration would be extremely difficult. This is the case of the [Wishart distribution](https://en.wikipedia.org/wiki/Wishart_distribution), which is defined over matrices. Even taking derivatives is a bit tricky, as it involves [[Matrix Calculus]], but the respective identities are listed in that article.

From the above table, we can see that the natural parameter is given by

$$
{\begin{aligned}{\boldsymbol {\eta }}_{1}&=-{\tfrac {1}{2}}\mathbf {V} ^{-1},\\\eta _{2}&={\hphantom {-}}{\tfrac {1}{2}}\left(n-p-1\right),\end{aligned}}
$$

the reverse substitutions are

$$
{\begin{aligned}\mathbf {V} &=-{\tfrac {1}{2}}{\boldsymbol {\eta }}_{1}^{-1},\\n&=2\eta _{2}+p+1,\end{aligned}}
$$

and the sufficient statistics are $(\mathbf {X} ,\log |\mathbf {X} |).$

The log-partition function is written in various forms in the table, to facilitate differentiation and back-substitution. We use the following forms:

$$
{\begin{aligned}A({\boldsymbol {\eta }}_{1},n)&=-{\frac {n}{2}}\log \left|-{\boldsymbol {\eta }}_{1}\right|+\log \Gamma _{p}{\left({\frac {n}{2}}\right)},\\[1ex]A(\mathbf {V} ,\eta _{2})&=\left(\eta _{2}+{\frac {p+1}{2}}\right)\log \left(2^{p}\left|\mathbf {V} \right|\right)+\log \Gamma _{p}{\left(\eta _{2}+{\frac {p+1}{2}}\right)}.\end{aligned}}
$$

Expectation of **X** (associated with ***η***<sub>1</sub>)

To differentiate with respect to ***η***<sub>1</sub>, we need the following [[Matrix Calculus]] identity:

$$
{\frac {\partial \log |a\mathbf {X} |}{\partial \mathbf {X} }}=(\mathbf {X} ^{-1})^{\mathsf {T}}
$$

Then:

$$
{\begin{aligned}\operatorname {E} [\mathbf {X} ]&={\frac {\partial }{\partial {\boldsymbol {\eta }}_{1}}}A\left({\boldsymbol {\eta }}_{1},\ldots \right)\\[1ex]&={\frac {\partial }{\partial {\boldsymbol {\eta }}_{1}}}\left[-{\frac {n}{2}}\log \left|-{\boldsymbol {\eta }}_{1}\right|+\log \Gamma _{p}{\left({\frac {n}{2}}\right)}\right]\\[1ex]&=-{\frac {n}{2}}({\boldsymbol {\eta }}_{1}^{-1})^{\mathsf {T}}\\[1ex]&={\frac {n}{2}}(-{\boldsymbol {\eta }}_{1}^{-1})^{\mathsf {T}}\\[1ex]&=n(\mathbf {V} )^{\mathsf {T}}\\[1ex]&=n\mathbf {V} \end{aligned}}
$$

The last line uses the fact that **V** is symmetric, and therefore it is the same when transposed.

Expectation of log \|**X**\| (associated with *η*<sub>2</sub>)

Now, for *η*<sub>2</sub>, we first need to expand the part of the log-partition function that involves the [multivariate gamma function](https://en.wikipedia.org/wiki/Multivariate_gamma_function):

$$
{\begin{aligned}\log \Gamma _{p}(a)&=\log \left(\pi ^{\frac {p(p-1)}{4}}\prod _{j=1}^{p}\Gamma {\left(a+{\frac {1-j}{2}}\right)}\right)\\&={\frac {p(p-1)}{4}}\log \pi +\sum _{j=1}^{p}\log \Gamma {\left(a+{\frac {1-j}{2}}\right)}\end{aligned}}
$$

We also need the [digamma function](https://en.wikipedia.org/wiki/Digamma_function):

$$
\psi (x)={\frac {d}{dx}}\log \Gamma (x).
$$

Then:

$$
{\begin{aligned}\operatorname {E} [\log |\mathbf {X} |]&={\frac {\partial }{\partial \eta _{2}}}A\left(\ldots ,\eta _{2}\right)\\[1ex]&={\frac {\partial }{\partial \eta _{2}}}\left[-\left(\eta _{2}+{\frac {p+1}{2}}\right)\log \left(2^{p}\left|\mathbf {V} \right|\right)+\log \Gamma _{p}{\left(\eta _{2}+{\frac {p+1}{2}}\right)}\right]\\[1ex]&={\frac {\partial }{\partial \eta _{2}}}\left[\left(\eta _{2}+{\frac {p+1}{2}}\right)\log \left(2^{p}\left|\mathbf {V} \right|\right)\right]+{\frac {\partial }{\partial \eta _{2}}}\left[{\frac {p(p-1)}{4}}\log \pi \right]\\&{\hphantom {=}}+{\frac {\partial }{\partial \eta _{2}}}\sum _{j=1}^{p}\log \Gamma {\left(\eta _{2}+{\frac {p+1}{2}}+{\frac {1-j}{2}}\right)}\\[1ex]&=p\log 2+\log |\mathbf {V} |+\sum _{j=1}^{p}\psi {\left(\eta _{2}+{\frac {p+1}{2}}+{\frac {1-j}{2}}\right)}\\[1ex]&=p\log 2+\log |\mathbf {V} |+\sum _{j=1}^{p}\psi {\left({\frac {n-p-1}{2}}+{\frac {p+1}{2}}+{\frac {1-j}{2}}\right)}\\[1ex]&=p\log 2+\log |\mathbf {V} |+\sum _{j=1}^{p}\psi {\left({\frac {n+1-j}{2}}\right)}\end{aligned}}
$$

This latter formula is listed in the [Wishart distribution](https://en.wikipedia.org/wiki/Wishart_distribution#Log-expectation) article. Both of these expectations are needed when deriving the [variational Bayes](https://en.wikipedia.org/wiki/Variational_Bayes) update equations in a [Bayes network](https://en.wikipedia.org/wiki/Bayes_network) involving a Wishart distribution (which is the [conjugate prior](https://en.wikipedia.org/wiki/Conjugate_prior) of the [[Multivariate Normal Distribution]]).

Computing these formulas using integration would be much more difficult. The first one, for example, would require matrix integration.

## Entropy

### Relative entropy

The [relative entropy](https://en.wikipedia.org/wiki/Relative_entropy) ([[Kullback-Leibler Divergence|Kullback–Leibler divergence]], KL divergence) of two distributions in an exponential family has a simple expression as the [Bregman divergence](https://en.wikipedia.org/wiki/Bregman_divergence) between the natural parameters with respect to the log-normalizer. The relative entropy is defined in terms of an integral, while the Bregman divergence is defined in terms of a derivative and inner product, and thus is easier to calculate and has a [closed-form expression](https://en.wikipedia.org/wiki/Closed-form_expression) (assuming the derivative has a closed-form expression). Further, the Bregman divergence in terms of the natural parameters and the log-normalizer equals the Bregman divergence of the dual parameters (expectation parameters), in the opposite order, for the [convex conjugate](https://en.wikipedia.org/wiki/Convex_conjugate) function.

Fixing an exponential family with log-normalizer $A$ (with convex conjugate $A^{*}$), writing $P_{A,\theta }$ for the distribution in this family corresponding a fixed value of the natural parameter $\theta$ (writing $\theta '$ for another value, and with $\eta ,\eta '$ for the corresponding dual expectation/moment parameters), writing KL for the KL divergence, and $B_{A}$ for the Bregman divergence, the divergences are related as: 

$$
\operatorname {KL} (P_{A,\theta }\parallel P_{A,\theta '})=B_{A}(\theta '\parallel \theta )=B_{A^{*}}(\eta \parallel \eta ').
$$

The KL divergence is conventionally written with respect to the *first* parameter, while the Bregman divergence is conventionally written with respect to the *second* parameter, and thus this can be read as "the relative entropy is equal to the Bregman divergence defined by the log-normalizer on the swapped natural parameters", or equivalently as "equal to the Bregman divergence defined by the dual to the log-normalizer on the expectation parameters".

### Maximum-entropy derivation

Exponential families arise naturally as the answer to the following question: what is the [maximum-entropy](https://en.wikipedia.org/wiki/Principle_of_maximum_entropy) distribution consistent with given constraints on expected values?

The [information entropy](https://en.wikipedia.org/wiki/Information_entropy) of a probability distribution *dF*(*x*) can only be computed with respect to some other probability distribution (or, more generally, a positive measure), and both [measures](https://en.wikipedia.org/wiki/Measure_(mathematics) "Measure (mathematics)") must be mutually [absolutely continuous](https://en.wikipedia.org/wiki/Absolutely_continuous). Accordingly, we need to pick a *reference measure* *dH*(*x*) with the same support as *dF*(*x*).

The entropy of *dF*(*x*) relative to *dH*(*x*) is

$$
S[dF\mid dH]=-\int {\frac {dF}{dH}}\log {\frac {dF}{dH}}\,dH
$$

or

$$
S[dF\mid dH]=\int \log {\frac {dH}{dF}}\,dF
$$

where *dF*/*dH* and *dH*/*dF* are [Radon–Nikodym derivatives](https://en.wikipedia.org/wiki/Radon%E2%80%93Nikodym_derivative). The ordinary definition of entropy for a discrete distribution supported on a set *I*, namely

$$
S=-\sum _{i\in I}p_{i}\log p_{i}
$$

*assumes*, though this is seldom pointed out, that *dH* is chosen to be the [counting measure](https://en.wikipedia.org/wiki/Counting_measure) on *I*.

Consider now a collection of observable quantities (random variables) *T<sub>i</sub>*. The probability distribution *dF* whose entropy with respect to *dH* is greatest, subject to the conditions that the expected value of *T*<sub>*i*</sub> be equal to *t<sub>i</sub>*, is an exponential family with *dH* as reference measure and (*T*<sub>1</sub>, ..., *T<sub>n</sub>*) as sufficient statistic.

The derivation is a simple [variational calculation](https://en.wikipedia.org/wiki/Calculus_of_variations) using [[Lagrange Multipliers]]. Normalization is imposed by letting *T*<sub>0</sub> = 1 be one of the constraints. The natural parameters of the distribution are the Lagrange multipliers, and the normalization factor is the Lagrange multiplier associated to *T*<sub>0</sub>.

For examples of such derivations, see [Maximum entropy probability distribution](https://en.wikipedia.org/wiki/Maximum_entropy_probability_distribution).

## Role in statistics

### Classical estimation: sufficiency

According to the **[Pitman](https://en.wikipedia.org/wiki/E._J._G._Pitman)–[Koopman](https://en.wikipedia.org/wiki/Bernard_Koopman)–[Darmois](https://en.wikipedia.org/wiki/Georges_Darmois) theorem**, among families of probability distributions whose domain does not vary with the parameter being estimated, only in exponential families is there a [sufficient statistic](https://en.wikipedia.org/wiki/Sufficient_statistic) whose dimension remains bounded as sample size increases.

Less tersely, suppose *X<sub>k</sub>*, (where *k* = 1, 2, 3, ... *n*) are [independent](https://en.wikipedia.org/wiki/Statistical_independence), identically distributed random variables. Only if their distribution is one of the *exponential family* of distributions is there a [sufficient statistic](https://en.wikipedia.org/wiki/Sufficient_statistic) ***T***(*X*<sub>1</sub>, ..., *X<sub>n</sub>*) whose [number](https://en.wikipedia.org/wiki/Dimension) of [scalar components](https://en.wikipedia.org/wiki/Random_variable#Introduction) does not increase as the sample size *n* increases; the statistic ***T*** may be a [vector](https://en.wikipedia.org/wiki/Multivariate_random_variable) or a [single scalar number](https://en.wikipedia.org/wiki/Random_variable#Introduction), but whatever it is, its [size](https://en.wikipedia.org/wiki/Dimension) will neither grow nor shrink when more data are obtained.

As a counterexample if these conditions are relaxed, the family of [uniform distributions](https://en.wikipedia.org/wiki/Uniform_distribution_(disambiguation)) (either [discrete](https://en.wikipedia.org/wiki/Discrete_uniform_distribution) or [continuous](https://en.wikipedia.org/wiki/Uniform_distribution_(continuous)), with either or both bounds unknown) has a sufficient statistic, namely the sample maximum, sample minimum, and sample size, but does not form an exponential family, as the domain varies with the parameters.

### Bayesian estimation: conjugate distributions

Exponential families are also important in [Bayesian statistics](https://en.wikipedia.org/wiki/Bayesian_statistics). In Bayesian statistics a [prior distribution](https://en.wikipedia.org/wiki/Prior_distribution) is multiplied by a [likelihood function](https://en.wikipedia.org/wiki/Likelihood_function) and then normalised to produce a [posterior distribution](https://en.wikipedia.org/wiki/Posterior_distribution). In the case of a likelihood which belongs to an exponential family there exists a [conjugate prior](https://en.wikipedia.org/wiki/Conjugate_prior), which is often also in an exponential family. A conjugate prior π for the parameter ${\boldsymbol {\eta }}$ of an exponential family

$$
f(x\mid {\boldsymbol {\eta }})=h(x)\,\exp \left[{\boldsymbol {\eta }}^{\mathsf {T}}\mathbf {T} (x)-A({\boldsymbol {\eta }})\right]
$$

is given by

$$
p_{\pi }({\boldsymbol {\eta }}\mid {\boldsymbol {\chi }},\nu )=f({\boldsymbol {\chi }},\nu )\,\exp \left[{\boldsymbol {\eta }}^{\mathsf {T}}{\boldsymbol {\chi }}-\nu A({\boldsymbol {\eta }})\right],
$$

or equivalently

$$
p_{\pi }({\boldsymbol {\eta }}\mid {\boldsymbol {\chi }},\nu )=f({\boldsymbol {\chi }},\nu )\,g({\boldsymbol {\eta }})^{\nu }\,\exp \left({\boldsymbol {\eta }}^{\mathsf {T}}{\boldsymbol {\chi }}\right),\qquad {\boldsymbol {\chi }}\in \mathbb {R} ^{s}
$$

where *s* is the dimension of ${\boldsymbol {\eta }}$ and $\nu >0$ and ${\boldsymbol {\chi }}$ are [hyperparameters](https://en.wikipedia.org/wiki/Hyperparameter_(Bayesian_statistics) "Hyperparameter (Bayesian statistics)") (parameters controlling parameters). $\nu$ corresponds to the effective number of observations that the prior distribution contributes, and ${\boldsymbol {\chi }}$ corresponds to the total amount that these pseudo-observations contribute to the [sufficient statistic](https://en.wikipedia.org/wiki/Sufficient_statistic) over all observations and pseudo-observations. $f({\boldsymbol {\chi }},\nu )$ is a [normalization constant](https://en.wikipedia.org/wiki/Normalization_constant) that is automatically determined by the remaining functions and serves to ensure that the given function is a [[Probability Density Function]] (i.e. it is [normalized](https://en.wikipedia.org/wiki/Normalization_(statistics) "Normalization (statistics)")). $A({\boldsymbol {\eta }})$ and equivalently $g({\boldsymbol {\eta }})$ are the same functions as in the definition of the distribution over which π is the conjugate prior.

A conjugate prior is one which, when combined with the likelihood and normalised, produces a posterior distribution which is of the same type as the prior. For example, if one is estimating the success probability of a binomial distribution, then if one chooses to use a beta distribution as one's prior, the posterior is another beta distribution. This makes the computation of the posterior particularly simple. Similarly, if one is estimating the parameter of a [Poisson distribution](https://en.wikipedia.org/wiki/Poisson_distribution) the use of a gamma prior will lead to another gamma posterior. Conjugate priors are often very flexible and can be very convenient. However, if one's belief about the likely value of the theta parameter of a binomial is represented by (say) a bimodal (two-humped) prior distribution, then this cannot be represented by a beta distribution. It can however be represented by using a [mixture density](https://en.wikipedia.org/wiki/Mixture_density) as the prior, here a combination of two beta distributions; this is a form of [hyperprior](https://en.wikipedia.org/wiki/Hyperprior).

An arbitrary likelihood will not belong to an exponential family, and thus in general no conjugate prior exists. The posterior will then have to be computed by numerical methods.

To show that the above prior distribution is a conjugate prior, we can derive the posterior.

First, assume that the probability of a single observation follows an exponential family, parameterized using its natural parameter:

$$
p_{F}(x\mid {\boldsymbol {\eta }})=h(x)\,g({\boldsymbol {\eta }})\,\exp \left[{\boldsymbol {\eta }}^{\mathsf {T}}\mathbf {T} (x)\right]
$$

Then, for data $\mathbf {X} =(x_{1},\ldots ,x_{n})$, the likelihood is computed as follows:

$$
p(\mathbf {X} \mid {\boldsymbol {\eta }})=\left(\prod _{i=1}^{n}h(x_{i})\right)g({\boldsymbol {\eta }})^{n}\exp \left({\boldsymbol {\eta }}^{\mathsf {T}}\sum _{i=1}^{n}\mathbf {T} (x_{i})\right)
$$

Then, for the above conjugate prior:

$$
{\begin{aligned}p_{\pi }({\boldsymbol {\eta }}\mid {\boldsymbol {\chi }},\nu )&=f({\boldsymbol {\chi }},\nu )g({\boldsymbol {\eta }})^{\nu }\exp({\boldsymbol {\eta }}^{\mathsf {T}}{\boldsymbol {\chi }})\propto g({\boldsymbol {\eta }})^{\nu }\exp({\boldsymbol {\eta }}^{\mathsf {T}}{\boldsymbol {\chi }})\end{aligned}}
$$

We can then compute the posterior as follows:

$$
{\begin{aligned}p({\boldsymbol {\eta }}\mid \mathbf {X} ,{\boldsymbol {\chi }},\nu )&\propto p(\mathbf {X} \mid {\boldsymbol {\eta }})p_{\pi }({\boldsymbol {\eta }}\mid {\boldsymbol {\chi }},\nu )\\&=\left(\prod _{i=1}^{n}h(x_{i})\right)g({\boldsymbol {\eta }})^{n}\exp \left({\boldsymbol {\eta }}^{\mathsf {T}}\sum _{i=1}^{n}\mathbf {T} (x_{i})\right)f({\boldsymbol {\chi }},\nu )g({\boldsymbol {\eta }})^{\nu }\exp({\boldsymbol {\eta }}^{\mathsf {T}}{\boldsymbol {\chi }})\\&\propto g({\boldsymbol {\eta }})^{n}\exp \left({\boldsymbol {\eta }}^{\mathsf {T}}\sum _{i=1}^{n}\mathbf {T} (x_{i})\right)g({\boldsymbol {\eta }})^{\nu }\exp({\boldsymbol {\eta }}^{\mathsf {T}}{\boldsymbol {\chi }})\\&=g({\boldsymbol {\eta }})^{\nu +n}\exp \left({\boldsymbol {\eta }}^{\mathsf {T}}\left({\boldsymbol {\chi }}+\sum _{i=1}^{n}\mathbf {T} (x_{i})\right)\right)\end{aligned}}
$$

The last line is the [kernel](https://en.wikipedia.org/wiki/Kernel_(statistics) "Kernel (statistics)") of the posterior distribution, i.e.

$$
p({\boldsymbol {\eta }}\mid \mathbf {X} ,{\boldsymbol {\chi }},\nu )=p_{\pi }\left({\boldsymbol {\eta }}\left|~{\boldsymbol {\chi }}+\sum _{i=1}^{n}\mathbf {T} (x_{i}),\nu +n\right.\right)
$$

This shows that the posterior has the same form as the prior.

The data **X** enters into this equation *only* in the expression

$$
\mathbf {T} (\mathbf {X} )=\sum _{i=1}^{n}\mathbf {T} (x_{i}),
$$

which is termed the [sufficient statistic](https://en.wikipedia.org/wiki/Sufficient_statistic) of the data. That is, the value of the sufficient statistic is sufficient to completely determine the posterior distribution. The actual data points themselves are not needed, and all sets of data points with the same sufficient statistic will have the same distribution. This is important because the dimension of the sufficient statistic does not grow with the data size — it has only as many components as the components of ${\boldsymbol {\eta }}$ (equivalently, the number of parameters of the distribution of a single data point).

The update equations are as follows:

$$
{\begin{aligned}{\boldsymbol {\chi }}'&={\boldsymbol {\chi }}+\mathbf {T} (\mathbf {X} )\\&={\boldsymbol {\chi }}+\sum _{i=1}^{n}\mathbf {T} (x_{i})\\\nu '&=\nu +n\end{aligned}}
$$

This shows that the update equations can be written simply in terms of the number of data points and the [sufficient statistic](https://en.wikipedia.org/wiki/Sufficient_statistic) of the data. This can be seen clearly in the various examples of update equations shown in the [conjugate prior](https://en.wikipedia.org/wiki/Conjugate_prior) page. Because of the way that the sufficient statistic is computed, it necessarily involves sums of components of the data (in some cases disguised as products or other forms — a product can be written in terms of a sum of [logarithms](https://en.wikipedia.org/wiki/Logarithm)). The cases where the update equations for particular distributions don't exactly match the above forms are cases where the conjugate prior has been expressed using a different [parameterization](https://en.wikipedia.org/wiki/Parametrization_(geometry) "Parametrization (geometry)") than the one that produces a conjugate prior of the above form — often specifically because the above form is defined over the natural parameter ${\boldsymbol {\eta }}$ while conjugate priors are usually defined over the actual parameter ${\boldsymbol {\theta }}.$

### Unbiased estimation

If the likelihood $z|\eta \sim e^{\eta z}f_{1}(\eta )f_{0}(z)$ is an exponential family, then the unbiased estimator of $\eta$ is $-{\frac {d}{dz}}\ln f_{0}(z)$.

### Hypothesis testing: uniformly most powerful tests

A one-parameter exponential family has a monotone non-decreasing likelihood ratio in the [sufficient statistic](https://en.wikipedia.org/wiki/Sufficiency_(statistics)) *T*(*x*), provided that *η*(*θ*) is non-decreasing. As a consequence, there exists a [uniformly most powerful test](https://en.wikipedia.org/wiki/Uniformly_most_powerful_test) for [[Hypothesis Testing|testing the hypothesis]] *H*<sub>0</sub>: *θ* ≥ *θ*<sub>0</sub> *vs*. *H*<sub>1</sub>: *θ* \< *θ*<sub>0</sub>.

### Generalized linear models

Exponential families form the basis for the distribution functions used in [generalized linear models](https://en.wikipedia.org/wiki/Generalized_linear_model) (GLM), a class of model that encompasses many of the commonly used regression models in statistics. Examples include [logistic regression](https://en.wikipedia.org/wiki/Logistic_regression) using the binomial family and [Poisson regression](https://en.wikipedia.org/wiki/Poisson_regression).

## See also

- [Exponential dispersion model](https://en.wikipedia.org/wiki/Exponential_dispersion_model)
- [Gibbs measure](https://en.wikipedia.org/wiki/Gibbs_measure)
- [Modified half-normal distribution](https://en.wikipedia.org/wiki/Modified_half-normal_distribution)
- [Natural exponential family](https://en.wikipedia.org/wiki/Natural_exponential_family)

## Footnotes

1.  For example, the family of normal distributions includes the standard normal distribution *N*(0, 1) with mean 0 and variance 1, as well as other normal distributions with different mean and variance.
2.  ["Partition function"](https://en.wikipedia.org/wiki/Partition_function_(mathematics) "Partition function (mathematics)") is often used in statistics as a synonym of "normalization factor".
3.  These distributions are often not themselves exponential families. Common examples of non-exponential families arising from exponential ones are the [Student's *t*-distribution](https://en.wikipedia.org/wiki/Student%27s_t-distribution), [beta-binomial distribution](https://en.wikipedia.org/wiki/Beta-binomial_distribution) and [Dirichlet-multinomial distribution](https://en.wikipedia.org/wiki/Dirichlet-multinomial_distribution).

## References

### Citations

1.  Kupperman, M. (1958). ["Probabilities of hypotheses and information-statistics in sampling from exponential-class populations"](https://doi.org/10.1214%2Faoms%2F1177706633). *[Annals of Mathematical Statistics](https://en.wikipedia.org/wiki/Annals_of_Mathematical_Statistics)*. **9** (2): 571–575. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/aoms/1177706633](https://doi.org/10.1214%2Faoms%2F1177706633). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2237349](https://www.jstor.org/stable/2237349).
2.  Andersen, Erling (September 1970). "Sufficiency and Exponential Families for Discrete Sample Spaces". *[Journal of the American Statistical Association](https://en.wikipedia.org/wiki/Journal_of_the_American_Statistical_Association)*. **65** (331). Journal of the American Statistical Association: 1248–1255. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2284291](https://doi.org/10.2307%2F2284291). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2284291](https://www.jstor.org/stable/2284291). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0268992](https://mathscinet.ams.org/mathscinet-getitem?mr=0268992).
3.  [Pitman, E.](https://en.wikipedia.org/wiki/E._J._G._Pitman); Wishart, J. (1936). "Sufficient statistics and intrinsic accuracy". *[Mathematical Proceedings of the Cambridge Philosophical Society](https://en.wikipedia.org/wiki/Mathematical_Proceedings_of_the_Cambridge_Philosophical_Society)*. **32** (4): 567–579. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1936PCPS...32..567P](https://ui.adsabs.harvard.edu/abs/1936PCPS...32..567P). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1017/S0305004100019307](https://doi.org/10.1017%2FS0305004100019307). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [120708376](https://api.semanticscholar.org/CorpusID:120708376).
4.  Darmois, G. (1935). "Sur les lois de probabilites a estimation exhaustive". *C. R. Acad. Sci. Paris* (in French). **200**: 1265–1266.
5.  [Koopman, B.](https://en.wikipedia.org/wiki/Bernard_Koopman) (1936). ["On distribution admitting a sufficient statistic"](https://doi.org/10.2307%2F1989758). *[Transactions of the American Mathematical Society](https://en.wikipedia.org/wiki/Transactions_of_the_American_Mathematical_Society)*. **39** (3). [American Mathematical Society](https://en.wikipedia.org/wiki/American_Mathematical_Society): 399–409. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/1989758](https://doi.org/10.2307%2F1989758). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [1989758](https://www.jstor.org/stable/1989758). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1501854](https://mathscinet.ams.org/mathscinet-getitem?mr=1501854).
6.  ["General Exponential Families"](https://www.randomservices.org/random/special/GeneralExponential.html). *www.randomservices.org*. Retrieved 2022-08-30.
7.  Abramovich & Ritov (2013). *Statistical Theory: A concise introduction*. Chapman & Hall. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1439851845](https://en.wikipedia.org/wiki/Special:BookSources/978-1439851845).
8.  Blei, David. ["Variational Inference"](https://www.cs.princeton.edu/courses/archive/fall11/cos597C/lectures/variational-inference-i.pdf) (PDF). Princeton U.
9.  Casella, George (2002). *Statistical inference*. Roger L. Berger (2nd ed.). Australia: Thomson Learning. Theorem 6.2.25. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-534-24312-6](https://en.wikipedia.org/wiki/Special:BookSources/0-534-24312-6). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [46538638](https://search.worldcat.org/oclc/46538638).
10. Brown, Lawrence D. (1986). *Fundamentals of statistical exponential families : with applications in statistical decision theory*. Hayward, Calif.: Institute of Mathematical Statistics. Theorem 2.12. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-940600-10-2](https://en.wikipedia.org/wiki/Special:BookSources/0-940600-10-2). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [15986663](https://search.worldcat.org/oclc/15986663).
11. Keener, Robert W. (2010). *Theoretical statistics : topics for a core course*. New York. pp. 47, Example 3.12. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-93839-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-93839-4). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [676700036](https://search.worldcat.org/oclc/676700036).`{{`[`cite book`](https://en.wikipedia.org/wiki/Template:Cite_book)`}}`: CS1 maint: location missing publisher ([link](https://en.wikipedia.org/wiki/Category:CS1_maint:_location_missing_publisher))
12. Nielsen, Frank; Garcia, Vincent (2009). "Statistical exponential families: A digest with flash cards". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[0911.4863](https://arxiv.org/abs/0911.4863) \[[cs.LG](https://arxiv.org/archive/cs.LG)\].
13. van Garderen, Kees Jan (1997). "Curved Exponential Models in Econometrics". *[Econometric Theory](https://en.wikipedia.org/wiki/Econometric_Theory)*. **13** (6): 771–790. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1017/S0266466600006253](https://doi.org/10.1017%2FS0266466600006253). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [122742807](https://api.semanticscholar.org/CorpusID:122742807).
14. , 4. Bregman Divergences and Relative Entropy of Exponential Families.
15. , 9.1 Convex duality and exponential families.
16. Efron, Bradley (December 2011). ["Tweedie's Formula and Selection Bias"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3325056). *Journal of the American Statistical Association*. **106** (496): 1602–1614. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1198/jasa.2011.tm11181](https://doi.org/10.1198%2Fjasa.2011.tm11181). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0162-1459](https://search.worldcat.org/issn/0162-1459). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [3325056](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3325056). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [22505788](https://pubmed.ncbi.nlm.nih.gov/22505788).

### Sources

- [Barndorff-Nielsen, Ole](https://en.wikipedia.org/wiki/Ole_Barndorff-Nielsen) (1978). *Information and exponential families in statistical theory*. Wiley Series in Probability and Mathematical Statistics. Chichester: John Wiley & Sons, Ltd. pp. ix+238 pp. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-99545-2](https://en.wikipedia.org/wiki/Special:BookSources/0-471-99545-2). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0489333](https://mathscinet.ams.org/mathscinet-getitem?mr=0489333).
  - Reprinted as Barndorff-Nielsen, Ole (2014). *Information and exponential families in statistical theory*. John Wiley & Sons, Ltd. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1002/9781118857281](https://doi.org/10.1002%2F9781118857281). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-111885750-2](https://en.wikipedia.org/wiki/Special:BookSources/978-111885750-2).
- Nielsen, Frank; Garcia, Vincent (2009). "Statistical exponential families: A digest with flash cards". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[0911.4863](https://arxiv.org/abs/0911.4863). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2009arXiv0911.4863N](https://ui.adsabs.harvard.edu/abs/2009arXiv0911.4863N).
- Nielsen, Frank; Nock, Richard (2010). [Entropies and cross-entropies of exponential families](https://web.archive.org/web/20190331194854/https://www.lix.polytechnique.fr/~nielsen/EntropyEF-ICIP2010.pdf) (PDF). IEEE International Conference on Image Processing. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/ICIP.2010.5652054](https://doi.org/10.1109%2FICIP.2010.5652054). Archived from [the original](https://www.lix.polytechnique.fr/~nielsen/EntropyEF-ICIP2010.pdf) (PDF) on 2019-03-31.

## Further reading

- Fahrmeir, Ludwig; Tutz, G. (1994). *Multivariate Statistical Modelling based on Generalized Linear Models*. Springer. pp. 18–22, 345–349. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-94233-5](https://en.wikipedia.org/wiki/Special:BookSources/0-387-94233-5).
- Keener, Robert W. (2006). *Theoretical Statistics: Topics for a Core Course*. Springer. pp. 27–28, 32–33. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-93838-7](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-93838-7).
- Lehmann, E. L.; Casella, G. (1998). *Theory of Point Estimation* (2nd ed.). sec. 1.5. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-98502-6](https://en.wikipedia.org/wiki/Special:BookSources/0-387-98502-6).

## External links

- [A primer on the exponential family of distributions](http://www.casact.org/pubs/dpp/dpp04/04dpp117.pdf)
- [Exponential family of distributions](http://jeff560.tripod.com/e.html) on the [Earliest known uses of some of the words of mathematics](http://jeff560.tripod.com/mathword.html)
- [jMEF: A Java library for exponential families](https://vincentfpgarcia.github.com/jMEF/) [Deprecated link](https://en.wikipedia.org/wiki/Wikipedia:Archive.today_guidance) archived 2013-04-11 at [archive.today](https://en.wikipedia.org/wiki/Archive.today)
- [Graphical Models, Exponential Families, and Variational Inference](https://people.eecs.berkeley.edu/~wainwrig/Papers/WaiJor08_FTML.pdf) by Wainwright and Jordan (2008)
