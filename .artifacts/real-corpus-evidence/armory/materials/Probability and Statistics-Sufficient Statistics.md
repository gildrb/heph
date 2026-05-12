[[probability-statistics.base]]

> Source: [Sufficient statistic](https://en.wikipedia.org/wiki/Sufficient_statistic)
> License: Wikipedia content is available under CC BY-SA 4.0.

In [statistics](https://en.wikipedia.org/wiki/Statistics), **sufficiency** is a property of a [statistic](https://en.wikipedia.org/wiki/Statistic) computed on a [sample dataset](https://en.wikipedia.org/wiki/Sample_(statistics)) in relation to a parametric model of the dataset. A sufficient statistic for a model parameter contains all of the information that the dataset provides about that parameter. It is closely related to the concepts of an [ancillary statistic](https://en.wikipedia.org/wiki/Ancillary_statistic) which contains no information about the model parameters, and of a [complete statistic](https://en.wikipedia.org/wiki/Complete_statistic) which only contains information about the parameters and no ancillary information.

A related concept is that of **linear sufficiency**, which is weaker than *sufficiency* but can be applied in some cases where there is no sufficient statistic, although it is restricted to linear estimators. The [Kolmogorov structure function](https://en.wikipedia.org/wiki/Kolmogorov_structure_function) deals with individual finite data; the related notion there is the algorithmic sufficient statistic.

The concept is due to [Sir Ronald Fisher](https://en.wikipedia.org/wiki/Ronald_Fisher) in 1920. [Stephen Stigler](https://en.wikipedia.org/wiki/Stephen_Stigler) noted in 1973 that the concept of sufficiency had fallen out of favor in [descriptive statistics](https://en.wikipedia.org/wiki/Descriptive_statistics) because of the strong dependence on an assumption of the distributional form (see [Pitman–Koopman–Darmois theorem](#Exponential_family) below), but remained very important in theoretical work.

## Background

Roughly, given a set $\mathbf {X}$ of [independent identically distributed](https://en.wikipedia.org/wiki/Independent_identically_distributed) data conditioned on an unknown parameter $\theta$, a sufficient statistic is a function $T(\mathbf {X} )$ whose value contains all the information needed to compute any estimate of the parameter (e.g. a [maximum likelihood](https://en.wikipedia.org/wiki/Maximum_likelihood) estimate). Due to the factorization theorem ([see below](#Fisher–Neyman_factorization_theorem)), for a sufficient statistic $T(\mathbf {X} )$, the probability density can be written as $f_{\mathbf {X} }(x;\theta )=h(x)\,g(\theta ,T(x))$. From this factorization, it can easily be seen that the maximum likelihood estimate of $\theta$ will interact with $\mathbf {X}$ only through $T(\mathbf {X} )$. Typically, the sufficient statistic is a simple function of the data, e.g. the sum of all the data points.

More generally, the "unknown parameter" may represent a [vector](https://en.wikipedia.org/wiki/Euclidean_vector) of unknown quantities or may represent everything about the model that is unknown or not fully specified. In such a case, the sufficient statistic may be a set of functions, called a *jointly sufficient statistic*. Typically, there are as many functions as there are parameters. For example, for a [[Gaussian Distribution]] with unknown [mean](https://en.wikipedia.org/wiki/Mean) and [variance](https://en.wikipedia.org/wiki/Variance), the jointly sufficient statistic, from which maximum likelihood estimates of both parameters can be estimated, consists of two functions, the sum of all data points and the sum of all squared data points (or equivalently, the [sample mean](https://en.wikipedia.org/wiki/Sample_mean) and [sample variance](https://en.wikipedia.org/wiki/Sample_variance)).

In other words, **the [joint probability distribution](https://en.wikipedia.org/wiki/Joint_probability_distribution) of the data is conditionally independent of the parameter given the value of the sufficient statistic for the parameter**. Both the statistic and the underlying parameter can be vectors.

## Mathematical definition

A statistic *t* = *T*(*X*) is **sufficient for underlying parameter *θ*** precisely if the [conditional probability distribution](https://en.wikipedia.org/wiki/Conditional_probability_distribution) of the data *X*, given the statistic *t* = *T*(*X*), does not depend on the parameter *θ*.

Alternatively, one can say the statistic *T*(*X*) is sufficient for *θ* if, for all prior distributions on *θ*, the [[Mutual Information]] between *θ* and *T(X)* equals the mutual information between *θ* and *X*. In other words, the [data processing inequality](https://en.wikipedia.org/wiki/Data_processing_inequality) becomes an equality:

$I{\bigl (}\theta ;T(X){\bigr )}=I(\theta ;X)$

### Example

As an example, the sample mean is sufficient for the (unknown) mean *μ* of a [normal distribution](https://en.wikipedia.org/wiki/Normal_distribution) with known variance. Once the sample mean is known, no further information about *μ* can be obtained from the sample itself. On the other hand, for an arbitrary distribution the [median](https://en.wikipedia.org/wiki/Median) is not sufficient for the mean: even if the median of the sample is known, knowing the sample itself would provide further information about the population mean. For example, if the observations that are less than the median are only slightly less, but observations exceeding the median exceed it by a large amount, then this would have a bearing on one's inference about the population mean.

## Fisher–Neyman factorization theorem

*[Fisher's](https://en.wikipedia.org/wiki/Ronald_Fisher) factorization theorem* or *factorization criterion* provides a convenient **characterization** of a sufficient statistic. If the [[Probability Density Function]] is ƒ<sub>*θ*</sub>(*x*), then *T* is sufficient for *θ* [if and only if](https://en.wikipedia.org/wiki/If_and_only_if) nonnegative functions *g* and *h* can be found such that

$f(x;\theta )=h(x)\,g(\theta ,T(x)),$

i.e., the density ƒ can be factored into a product such that one factor, *h*, does not depend on *θ* and the other factor, which does depend on *θ*, depends on *x* only through *T*(*x*). A general proof of this was given by Halmos and Savage and the theorem is sometimes referred to as the Halmos–Savage factorization theorem. The proofs below handle special cases, but an alternative general proof along the same lines can be given. In many simple cases the probability density function is fully specified by $\theta$ and $T(x)$, and $h(x)=1$ (see [Examples](#Examples)).

It is easy to see that if *F*(*t*) is a one-to-one function and *T* is a sufficient statistic, then *F*(*T*) is a sufficient statistic. In particular we can multiply a sufficient statistic by a nonzero constant and get another sufficient statistic.

### Likelihood principle interpretation

An implication of the theorem is that when using likelihood-based inference, two sets of data yielding the same value for the sufficient statistic *T*(*X*) will always yield the same inferences about *θ*. By the factorization criterion, the likelihood's dependence on *θ* is only in conjunction with *T*(*X*). As this is the same in both cases, the dependence on *θ* will be the same as well, leading to identical inferences.

### Proof

Due to Hogg and Craig. Let $X_{1},X_{2},\ldots ,X_{n}$, denote a random sample from a distribution having the [[Probability Density Function|pdf]] *f*(*x*, *θ*) for *ι* \< *θ* \< *δ*. Let *Y*<sub>1</sub> = *u*<sub>1</sub>(*X*<sub>1</sub>, *X*<sub>2</sub>, ..., *X*<sub>*n*</sub>) be a statistic whose pdf is *g*<sub>1</sub>(*y*<sub>1</sub>; *θ*). What we want to prove is that *Y*<sub>1</sub> = *u*<sub>1</sub>(*X*<sub>1</sub>, *X*<sub>2</sub>, ..., *X*<sub>*n*</sub>) is a sufficient statistic for *θ* if and only if, for some function *H*,

$\prod _{i=1}^{n}f(x_{i};\theta )=g_{1}\left[u_{1}(x_{1},x_{2},\dots ,x_{n});\theta \right]H(x_{1},x_{2},\dots ,x_{n}).$

First, suppose that

$\prod _{i=1}^{n}f(x_{i};\theta )=g_{1}\left[u_{1}(x_{1},x_{2},\dots ,x_{n});\theta \right]H(x_{1},x_{2},\dots ,x_{n}).$

We shall make the transformation *y*<sub>*i*</sub> = *u*<sub>i</sub>(*x*<sub>1</sub>, *x*<sub>2</sub>, ..., *x*<sub>*n*</sub>), for *i* = 1, ..., *n*, having inverse functions *x*<sub>*i*</sub> = *w*<sub>*i*</sub>(*y*<sub>1</sub>, *y*<sub>2</sub>, ..., *y*<sub>*n*</sub>), for *i* = 1, ..., *n*, and [Jacobian](https://en.wikipedia.org/wiki/Jacobian_matrix_and_determinant) $J=\left[w_{i}/y_{j}\right]$. Thus,

$\prod _{i=1}^{n}f\left[w_{i}(y_{1},y_{2},\dots ,y_{n});\theta \right]=|J|g_{1}(y_{1};\theta )H\left[w_{1}(y_{1},y_{2},\dots ,y_{n}),\dots ,w_{n}(y_{1},y_{2},\dots ,y_{n})\right].$

The left-hand member is the joint pdf *g*(*y*<sub>1</sub>, *y*<sub>2</sub>, ..., *y*<sub>*n*</sub>; θ) of *Y*<sub>1</sub> = *u*<sub>1</sub>(*X*<sub>1</sub>, ..., *X*<sub>*n*</sub>), ..., *Y*<sub>*n*</sub> = *u*<sub>*n*</sub>(*X*<sub>1</sub>, ..., *X*<sub>*n*</sub>). In the right-hand member, $g_{1}(y_{1};\theta )$ is the pdf of $Y_{1}$, so that $H[w_{1},\dots ,w_{n}]|J|$ is the quotient of $g(y_{1},\dots ,y_{n};\theta )$ and $g_{1}(y_{1};\theta )$; that is, it is the conditional pdf $h(y_{2},\dots ,y_{n}\mid y_{1};\theta )$ of $Y_{2},\dots ,Y_{n}$ given $Y_{1}=y_{1}$.

But $H(x_{1},x_{2},\dots ,x_{n})$, and thus $H\left[w_{1}(y_{1},\dots ,y_{n}),\dots ,w_{n}(y_{1},\dots ,y_{n}))\right]$, was given not to depend upon $\theta$. Since $\theta$ was not introduced in the transformation and accordingly not in the Jacobian $J$, it follows that $h(y_{2},\dots ,y_{n}\mid y_{1};\theta )$ does not depend upon $\theta$ and that $Y_{1}$ is a sufficient statistics for $\theta$.

The converse is proven by taking:

$g(y_{1},\dots ,y_{n};\theta )=g_{1}(y_{1};\theta )h(y_{2},\dots ,y_{n}\mid y_{1}),$

where $h(y_{2},\dots ,y_{n}\mid y_{1})$ does not depend upon $\theta$ because $Y_{2}...Y_{n}$ depend only upon $X_{1}...X_{n}$, which are independent on $\Theta$ when conditioned by $Y_{1}$, a sufficient statistics by hypothesis. Now divide both members by the absolute value of the non-vanishing Jacobian $J$, and replace $y_{1},\dots ,y_{n}$ by the functions $u_{1}(x_{1},\dots ,x_{n}),\dots ,u_{n}(x_{1},\dots ,x_{n})$ in $x_{1},\dots ,x_{n}$. This yields

${\frac {g\left[u_{1}(x_{1},\dots ,x_{n}),\dots ,u_{n}(x_{1},\dots ,x_{n});\theta \right]}{|J^{*}|}}=g_{1}\left[u_{1}(x_{1},\dots ,x_{n});\theta \right]{\frac {h(u_{2},\dots ,u_{n}\mid u_{1})}{|J^{*}|}}$

where $J^{*}$ is the Jacobian with $y_{1},\dots ,y_{n}$ replaced by their value in terms $x_{1},\dots ,x_{n}$. The left-hand member is necessarily the joint pdf $f(x_{1};\theta )\cdots f(x_{n};\theta )$ of $X_{1},\dots ,X_{n}$. Since $h(y_{2},\dots ,y_{n}\mid y_{1})$, and thus $h(u_{2},\dots ,u_{n}\mid u_{1})$, does not depend upon $\theta$, then

$H(x_{1},\dots ,x_{n})={\frac {h(u_{2},\dots ,u_{n}\mid u_{1})}{|J^{*}|}}$

is a function that does not depend upon $\theta$.

### Another proof

A simpler more illustrative proof is as follows, although it applies only in the discrete case.

We use the shorthand notation to denote the joint probability density of $(X,T(X))$ by $f_{\theta }(x,t)$. Since $T$ is a deterministic function of $X$, we have $f_{\theta }(x,t)=f_{\theta }(x)$, as long as $t=T(x)$ and zero otherwise. Therefore:

${\begin{aligned}f_{\theta }(x)&=f_{\theta }(x,t)\\[5pt]&=f_{\theta }(x\mid t)f_{\theta }(t)\\[5pt]&=f(x\mid t)f_{\theta }(t)\end{aligned}}$

with the last equality being true by the definition of sufficient statistics. Thus $f_{\theta }(x)=a(x)b_{\theta }(t)$ with $a(x)=f_{X\mid t}(x)$ and $b_{\theta }(t)=f_{\theta }(t)$.

Conversely, if $f_{\theta }(x)=a(x)b_{\theta }(t)$, we have

${\begin{aligned}f_{\theta }(t)&=\sum _{x:T(x)=t}f_{\theta }(x,t)\\[5pt]&=\sum _{x:T(x)=t}f_{\theta }(x)\\[5pt]&=\sum _{x:T(x)=t}a(x)b_{\theta }(t)\\[5pt]&=\left(\sum _{x:T(x)=t}a(x)\right)b_{\theta }(t).\end{aligned}}$

With the first equality by the [[Probability Density Function|definition of pdf for multiple variables]], the second by the remark above, the third by hypothesis, and the fourth because the summation is not over $t$.

Let $f_{X\mid t}(x)$ denote the conditional probability density of $X$ given $T(X)$. Then we can derive an explicit expression for this:

${\begin{aligned}f_{X\mid t}(x)&={\frac {f_{\theta }(x,t)}{f_{\theta }(t)}}\\[5pt]&={\frac {f_{\theta }(x)}{f_{\theta }(t)}}\\[5pt]&={\frac {a(x)b_{\theta }(t)}{\left(\sum _{x:T(x)=t}a(x)\right)b_{\theta }(t)}}\\[5pt]&={\frac {a(x)}{\sum _{x:T(x)=t}a(x)}}.\end{aligned}}$

With the first equality by definition of conditional probability density, the second by the remark above, the third by the equality proven above, and the fourth by simplification. This expression does not depend on $\theta$ and thus $T$ is a sufficient statistic.

## Minimal sufficiency

A sufficient statistic is **minimal sufficient** if it can be represented as a function of any other sufficient statistic. In other words, *S*(*X*) is **minimal sufficient** if and only if

1.  *S*(*X*) is sufficient, and
2.  if *T*(*X*) is sufficient, then there exists a function *f* such that *S*(*X*) = *f*(*T*(*X*)).

Intuitively, a minimal sufficient statistic *most efficiently* captures all possible information about the parameter *θ*.

A useful characterization of minimal sufficiency is that when the density *f*<sub>*θ*</sub> exists, *S*(*X*) is **minimal sufficient** if

${\frac {f_{\theta }(x)}{f_{\theta }(y)}}$ is independent of *θ* :$\Longleftrightarrow$ *S*(*x*) = *S*(*y*)

This follows as a consequence from [Fisher's factorization theorem](#Fisher–Neyman_factorization_theorem) stated above.

A case in which there is no minimal sufficient statistic was shown by Bahadur, 1954. However, under mild conditions, a minimal sufficient statistic does always exist. In particular, in Euclidean space, these conditions always hold if the random variables (associated with $P_{\theta }$ ) are all discrete or are all continuous.

If there exists a minimal sufficient statistic, and this is usually the case, then every [complete](https://en.wikipedia.org/wiki/Completeness_(statistics) "Completeness (statistics)") sufficient statistic is necessarily minimal sufficient (note that this statement does not exclude a pathological case in which a complete sufficient exists while there is no minimal sufficient statistic). While it is hard to find cases in which a minimal sufficient statistic does not exist, it is not so hard to find cases in which there is no complete sufficient statistic.

The collection of likelihood ratios $\left\{{\frac {L(X\mid \theta _{i})}{L(X\mid \theta _{0})}}\right\}$ for $i=1,...,k$, is a minimal sufficient statistic if the parameter space is discrete $\left\{\theta _{0},...,\theta _{k}\right\}$.

## Examples

### Bernoulli distribution

If *X*<sub>1</sub>, ...., *X*<sub>*n*</sub> are independent [Bernoulli-distributed](https://en.wikipedia.org/wiki/Bernoulli_trial) random variables with expected value *p*, then the sum *T*(*X*) = *X*<sub>1</sub> + ... + *X*<sub>*n*</sub> is a sufficient statistic for *p* (here 'success' corresponds to *X*<sub>*i*</sub> = 1 and 'failure' to *X*<sub>*i*</sub> = 0; so *T* is the total number of successes)

This is seen by considering the joint probability distribution:

$\Pr\{X=x\}=\Pr\{X_{1}=x_{1},X_{2}=x_{2},\ldots ,X_{n}=x_{n}\}.$

Because the observations are independent, this can be written as

$p^{x_{1}}(1-p)^{1-x_{1}}p^{x_{2}}(1-p)^{1-x_{2}}\cdots p^{x_{n}}(1-p)^{1-x_{n}}$

and, collecting powers of *p* and 1 − *p*, gives

$p^{\sum x_{i}}(1-p)^{n-\sum x_{i}}=p^{T(x)}(1-p)^{n-T(x)}$

which satisfies the factorization criterion, with *h*(*x*) = 1 being just a constant.

Note the crucial feature: the unknown parameter *p* interacts with the data *x* only via the statistic *T*(*x*) = Σ *x*<sub>*i*</sub>.

As a concrete application, this gives a procedure for distinguishing a [fair coin from a biased coin](https://en.wikipedia.org/wiki/Fair_coin#Fair_results_from_a_biased_coin).

### Uniform distribution

If *X*<sub>1</sub>, ...., *X*<sub>*n*</sub> are independent and [uniformly distributed](https://en.wikipedia.org/wiki/Uniform_distribution_(continuous)) on the interval \[0,*θ*\], then *T*(*X*) = max(*X*<sub>1</sub>, ..., *X*<sub>*n*</sub>) is sufficient for θ — the [sample maximum](https://en.wikipedia.org/wiki/Sample_maximum) is a sufficient statistic for the population maximum.

To see this, consider the joint [[Probability Density Function]] of *X*  (*X*<sub>1</sub>,...,*X*<sub>*n*</sub>). Because the observations are independent, the pdf can be written as a product of individual densities

${\begin{aligned}f_{\theta }(x_{1},\ldots ,x_{n})&={\frac {1}{\theta }}\mathbf {1} _{\{0\leq x_{1}\leq \theta \}}\cdots {\frac {1}{\theta }}\mathbf {1} _{\{0\leq x_{n}\leq \theta \}}\\[5pt]&={\frac {1}{\theta ^{n}}}\mathbf {1} _{\{0\leq \min\{x_{i}\}\}}\mathbf {1} _{\{\max\{x_{i}\}\leq \theta \}}\end{aligned}}$

where **1**<sub>{*...*}</sub> is the [indicator function](https://en.wikipedia.org/wiki/Indicator_function). Thus the density takes form required by the Fisher–Neyman factorization theorem, where *h*(*x*) = **1**<sub>{min{*x<sub>i</sub>*}≥0}</sub>, and the rest of the expression is a function of only *θ* and *T*(*x*) = max{*x<sub>i</sub>*}.

In fact, the [minimum-variance unbiased estimator](https://en.wikipedia.org/wiki/Minimum-variance_unbiased_estimator) (MVUE) for *θ* is

${\frac {n+1}{n}}T(X).$

This is the sample maximum, scaled to correct for the [bias](https://en.wikipedia.org/wiki/Bias_of_an_estimator), and is MVUE by the [Lehmann–Scheffé theorem](https://en.wikipedia.org/wiki/Lehmann%E2%80%93Scheff%C3%A9_theorem). Unscaled sample maximum *T*(*X*) is the [maximum likelihood estimator](https://en.wikipedia.org/wiki/Maximum_likelihood_estimator) for *θ*.

### Uniform distribution (with two parameters)

If $X_{1},...,X_{n}$ are independent and [uniformly distributed](https://en.wikipedia.org/wiki/Uniform_distribution_(continuous)) on the interval $[\alpha ,\beta ]$ (where $\alpha$ and $\beta$ are unknown parameters), then $T(X_{1}^{n})=\left(\min _{1\leq i\leq n}X_{i},\max _{1\leq i\leq n}X_{i}\right)$ is a two-dimensional sufficient statistic for $(\alpha \,,\,\beta )$.

To see this, consider the joint [[Probability Density Function]] of $X_{1}^{n}=(X_{1},\ldots ,X_{n})$. Because the observations are independent, the pdf can be written as a product of individual densities, i.e.

${\begin{aligned}f_{X_{1}^{n}}(x_{1}^{n})&=\prod _{i=1}^{n}\left({1 \over \beta -\alpha }\right)\mathbf {1} _{\{\alpha \leq x_{i}\leq \beta \}}=\left({1 \over \beta -\alpha }\right)^{n}\mathbf {1} _{\{\alpha \leq x_{i}\leq \beta ,\,\forall \,i=1,\ldots ,n\}}\\&=\left({1 \over \beta -\alpha }\right)^{n}\mathbf {1} _{\{\alpha \,\leq \,\min _{1\leq i\leq n}X_{i}\}}\mathbf {1} _{\{\max _{1\leq i\leq n}X_{i}\,\leq \,\beta \}}.\end{aligned}}$

The joint density of the sample takes the form required by the Fisher–Neyman factorization theorem, by letting

${\begin{aligned}h(x_{1}^{n})=1,\quad g_{(\alpha ,\beta )}(x_{1}^{n})=\left({1 \over \beta -\alpha }\right)^{n}\mathbf {1} _{\{\alpha \,\leq \,\min _{1\leq i\leq n}X_{i}\}}\mathbf {1} _{\{\max _{1\leq i\leq n}X_{i}\,\leq \,\beta \}}.\end{aligned}}$

Since $h(x_{1}^{n})$ does not depend on the parameter $(\alpha ,\beta )$ and $g_{(\alpha \,,\,\beta )}(x_{1}^{n})$ depends only on $x_{1}^{n}$ through the function $T(X_{1}^{n})=\left(\min _{1\leq i\leq n}X_{i},\max _{1\leq i\leq n}X_{i}\right),$

the Fisher–Neyman factorization theorem implies $T(X_{1}^{n})=\left(\min _{1\leq i\leq n}X_{i},\max _{1\leq i\leq n}X_{i}\right)$ is a sufficient statistic for $(\alpha \,,\,\beta )$.

### Poisson distribution

If *X*<sub>1</sub>, ...., *X*<sub>*n*</sub> are independent and have a [Poisson distribution](https://en.wikipedia.org/wiki/Poisson_distribution) with parameter *λ*, then the sum *T*(*X*) = *X*<sub>1</sub> + ... + *X*<sub>*n*</sub> is a sufficient statistic for *λ*.

To see this, consider the joint probability distribution:

$\Pr(X=x)=P(X_{1}=x_{1},X_{2}=x_{2},\ldots ,X_{n}=x_{n}).$

Because the observations are independent, this can be written as

${e^{-\lambda }\lambda ^{x_{1}} \over x_{1}!}\cdot {e^{-\lambda }\lambda ^{x_{2}} \over x_{2}!}\cdots {e^{-\lambda }\lambda ^{x_{n}} \over x_{n}!}$

which may be written as

$e^{-n\lambda }\lambda ^{(x_{1}+x_{2}+\cdots +x_{n})}\cdot {1 \over x_{1}!x_{2}!\cdots x_{n}!}$

which shows that the factorization criterion is satisfied, where *h*(*x*) is the reciprocal of the product of the factorials. Note the parameter λ interacts with the data only through its sum *T*(*X*).

### Normal distribution

If $X_{1},\ldots ,X_{n}$ are independent and [normally distributed](https://en.wikipedia.org/wiki/Normal_distribution) with expected value $\theta$ (a parameter) and known finite variance $\sigma ^{2},$ then

$T(X_{1}^{n})={\overline {x}}={\frac {1}{n}}\sum _{i=1}^{n}X_{i}$

is a sufficient statistic for $\theta .$

To see this, consider the joint [[Probability Density Function]] of $X_{1}^{n}=(X_{1},\dots ,X_{n})$. Because the observations are independent, the pdf can be written as a product of individual densities, i.e.

${\begin{aligned}f_{X_{1}^{n}}(x_{1}^{n})&=\prod _{i=1}^{n}{\frac {1}{\sqrt {2\pi \sigma ^{2}}}}\exp \left(-{\frac {(x_{i}-\theta )^{2}}{2\sigma ^{2}}}\right)\\[6pt]&=(2\pi \sigma ^{2})^{-{\frac {n}{2}}}\exp \left(-\sum _{i=1}^{n}{\frac {(x_{i}-\theta )^{2}}{2\sigma ^{2}}}\right)\\[6pt]&=(2\pi \sigma ^{2})^{-{\frac {n}{2}}}\exp \left(-\sum _{i=1}^{n}{\frac {\left(\left(x_{i}-{\overline {x}}\right)-\left(\theta -{\overline {x}}\right)\right)^{2}}{2\sigma ^{2}}}\right)\\[6pt]&=(2\pi \sigma ^{2})^{-{\frac {n}{2}}}\exp \left(-{1 \over 2\sigma ^{2}}\left(\sum _{i=1}^{n}(x_{i}-{\overline {x}})^{2}+\sum _{i=1}^{n}(\theta -{\overline {x}})^{2}-2\sum _{i=1}^{n}(x_{i}-{\overline {x}})(\theta -{\overline {x}})\right)\right)\\[6pt]&=(2\pi \sigma ^{2})^{-{\frac {n}{2}}}\exp \left(-{1 \over 2\sigma ^{2}}\left(\sum _{i=1}^{n}(x_{i}-{\overline {x}})^{2}+n(\theta -{\overline {x}})^{2}\right)\right)&&\sum _{i=1}^{n}(x_{i}-{\overline {x}})(\theta -{\overline {x}})=0\\[6pt]&=(2\pi \sigma ^{2})^{-{\frac {n}{2}}}\exp \left(-{1 \over 2\sigma ^{2}}\sum _{i=1}^{n}(x_{i}-{\overline {x}})^{2}\right)\exp \left(-{\frac {n}{2\sigma ^{2}}}(\theta -{\overline {x}})^{2}\right)\end{aligned}}$

The joint density of the sample takes the form required by the Fisher–Neyman factorization theorem, by letting

${\begin{aligned}h(x_{1}^{n})&=(2\pi \sigma ^{2})^{-{\frac {n}{2}}}\exp \left(-{1 \over 2\sigma ^{2}}\sum _{i=1}^{n}(x_{i}-{\overline {x}})^{2}\right)\\[6pt]g_{\theta }(x_{1}^{n})&=\exp \left(-{\frac {n}{2\sigma ^{2}}}(\theta -{\overline {x}})^{2}\right)\end{aligned}}$

Since $h(x_{1}^{n})$ does not depend on the parameter $\theta$ and $g_{\theta }(x_{1}^{n})$ depends only on $x_{1}^{n}$ through the function

$T(X_{1}^{n})={\overline {x}}={\frac {1}{n}}\sum _{i=1}^{n}X_{i},$

the Fisher–Neyman factorization theorem implies $T(X_{1}^{n})$ is a sufficient statistic for $\theta$.

If $\sigma ^{2}$ is unknown and since $s^{2}={\frac {1}{n-1}}\sum _{i=1}^{n}\left(x_{i}-{\overline {x}}\right)^{2}$, the above likelihood can be rewritten as

${\begin{aligned}f_{X_{1}^{n}}(x_{1}^{n})=(2\pi \sigma ^{2})^{-n/2}\exp \left(-{\frac {n-1}{2\sigma ^{2}}}s^{2}\right)\exp \left(-{\frac {n}{2\sigma ^{2}}}(\theta -{\overline {x}})^{2}\right).\end{aligned}}$

The Fisher–Neyman factorization theorem still holds and implies that $({\overline {x}},s^{2})$ is a joint sufficient statistic for $(\theta ,\sigma ^{2})$.

### Exponential distribution

If $X_{1},\dots ,X_{n}$ are independent and [exponentially distributed](https://en.wikipedia.org/wiki/Exponential_distribution) with expected value *θ* (an unknown real-valued positive parameter), then $T(X_{1}^{n})=\sum _{i=1}^{n}X_{i}$ is a sufficient statistic for θ.

To see this, consider the joint [[Probability Density Function]] of $X_{1}^{n}=(X_{1},\dots ,X_{n})$. Because the observations are independent, the pdf can be written as a product of individual densities, i.e.

${\begin{aligned}f_{X_{1}^{n}}(x_{1}^{n})&=\prod _{i=1}^{n}{1 \over \theta }\,e^{{-1 \over \theta }x_{i}}={1 \over \theta ^{n}}\,e^{{-1 \over \theta }\sum _{i=1}^{n}x_{i}}.\end{aligned}}$

The joint density of the sample takes the form required by the Fisher–Neyman factorization theorem, by letting

${\begin{aligned}h(x_{1}^{n})=1,\,\,\,g_{\theta }(x_{1}^{n})={1 \over \theta ^{n}}\,e^{{-1 \over \theta }\sum _{i=1}^{n}x_{i}}.\end{aligned}}$

Since $h(x_{1}^{n})$ does not depend on the parameter $\theta$ and $g_{\theta }(x_{1}^{n})$ depends only on $x_{1}^{n}$ through the function $T(X_{1}^{n})=\sum _{i=1}^{n}X_{i}$

the Fisher–Neyman factorization theorem implies $T(X_{1}^{n})=\sum _{i=1}^{n}X_{i}$ is a sufficient statistic for $\theta$.

### Gamma distribution

If $X_{1},\dots ,X_{n}$ are independent and distributed as a [$\Gamma (\alpha \,,\,\beta )$](https://en.wikipedia.org/wiki/Gamma_distribution), where $\alpha$ and $\beta$ are unknown parameters of a [Gamma distribution](https://en.wikipedia.org/wiki/Gamma_distribution), then $T(X_{1}^{n})=\left(\prod _{i=1}^{n}{X_{i}},\sum _{i=1}^{n}X_{i}\right)$ is a two-dimensional sufficient statistic for $(\alpha ,\beta )$.

To see this, consider the joint [[Probability Density Function]] of $X_{1}^{n}=(X_{1},\dots ,X_{n})$. Because the observations are independent, the pdf can be written as a product of individual densities, i.e.

${\begin{aligned}f_{X_{1}^{n}}(x_{1}^{n})&=\prod _{i=1}^{n}\left({1 \over \Gamma (\alpha )\beta ^{\alpha }}\right)x_{i}^{\alpha -1}e^{(-1/\beta )x_{i}}\\[5pt]&=\left({1 \over \Gamma (\alpha )\beta ^{\alpha }}\right)^{n}\left(\prod _{i=1}^{n}x_{i}\right)^{\alpha -1}e^{{-1 \over \beta }\sum _{i=1}^{n}x_{i}}.\end{aligned}}$

The joint density of the sample takes the form required by the Fisher–Neyman factorization theorem, by letting

${\begin{aligned}h(x_{1}^{n})=1,\,\,\,g_{(\alpha \,,\,\beta )}(x_{1}^{n})=\left({1 \over \Gamma (\alpha )\beta ^{\alpha }}\right)^{n}\left(\prod _{i=1}^{n}x_{i}\right)^{\alpha -1}e^{{-1 \over \beta }\sum _{i=1}^{n}x_{i}}.\end{aligned}}$

Since $h(x_{1}^{n})$ does not depend on the parameter $(\alpha \,,\,\beta )$ and $g_{(\alpha \,,\,\beta )}(x_{1}^{n})$ depends only on $x_{1}^{n}$ through the function $T(x_{1}^{n})=\left(\prod _{i=1}^{n}x_{i},\sum _{i=1}^{n}x_{i}\right),$

the Fisher–Neyman factorization theorem implies $T(X_{1}^{n})=\left(\prod _{i=1}^{n}X_{i},\sum _{i=1}^{n}X_{i}\right)$ is a sufficient statistic for $(\alpha \,,\,\beta ).$

## Rao–Blackwell theorem

**Sufficiency** finds a useful application in the [Rao–Blackwell theorem](https://en.wikipedia.org/wiki/Rao%E2%80%93Blackwell_theorem), which states that if *g*(*X*) is any kind of estimator of *θ*, then typically the [conditional expectation](https://en.wikipedia.org/wiki/Conditional_expectation) of *g*(*X*) given sufficient statistic *T*(*X*) is a better (in the sense of having lower [variance](https://en.wikipedia.org/wiki/Variance)) estimator of *θ*, and is never worse. Sometimes one can very easily construct a very crude estimator *g*(*X*), and then evaluate that conditional expected value to get an estimator that is in various senses optimal.

## Exponential family

According to the **Pitman–Koopman–Darmois theorem,** among families of probability distributions whose domain does not vary with the parameter being estimated, only in [[Exponential Family|exponential families]] is there a sufficient statistic whose dimension remains bounded as sample size increases. Intuitively, this states that nonexponential families of distributions on the real line require [nonparametric statistics](https://en.wikipedia.org/wiki/Nonparametric_statistics) to fully capture the information in the data.

Less tersely, suppose $X_{n},n=1,2,3,\dots$ are [independent identically distributed](https://en.wikipedia.org/wiki/Independent_identically_distributed) **real** random variables whose distribution is known to be in some family of probability distributions, parametrized by $\theta$, satisfying certain technical regularity conditions, then that family is an *exponential* family if and only if there is a $\mathbb {R} ^{m}$-valued sufficient statistic $T(X_{1},\dots ,X_{n})$ whose number of scalar components $m$ does not increase as the sample size *n* increases.

This theorem shows that the existence of a finite-dimensional, real-vector-valued sufficient statistics sharply restricts the possible forms of a family of distributions on the **real line**.

When the parameters or the random variables are no longer real-valued, the situation is more complex.

## Other types of sufficiency

### Bayesian sufficiency

An alternative formulation of the condition that a statistic be sufficient, set in a Bayesian context, involves the posterior distributions obtained by using the full data-set and by using only a statistic. Thus the requirement is that, for almost every *x*,

$\Pr(\theta \mid X=x)=\Pr(\theta \mid T(X)=t(x)).$

More generally, without assuming a parametric model, we can say that the statistics *T* is *predictive sufficient* if

$\Pr(X'=x'\mid X=x)=\Pr(X'=x'\mid T(X)=t(x)).$

It turns out that this "Bayesian sufficiency" is a consequence of the formulation above, however they are not directly equivalent in the infinite-dimensional case. A range of theoretical results for sufficiency in a Bayesian context is available.

### Linear sufficiency

A concept called "linear sufficiency" can be formulated in a Bayesian context, and more generally. First define the best linear predictor of a vector *Y* based on *X* as ${\hat {E}}[Y\mid X]$. Then a linear statistic *T*(*x*) is linear sufficient if

${\hat {E}}[\theta \mid X]={\hat {E}}[\theta \mid T(X)].$

## See also

- [Completeness](https://en.wikipedia.org/wiki/Completeness_(statistics) "Completeness (statistics)") of a statistic
- [Basu's theorem](https://en.wikipedia.org/wiki/Basu%27s_theorem) on independence of complete sufficient and ancillary statistics
- [Lehmann–Scheffé theorem](https://en.wikipedia.org/wiki/Lehmann%E2%80%93Scheff%C3%A9_theorem): a complete sufficient estimator is the best estimator of its expectation
- [Rao–Blackwell theorem](https://en.wikipedia.org/wiki/Rao%E2%80%93Blackwell_theorem)
- [Chentsov's theorem](https://en.wikipedia.org/wiki/Chentsov%27s_theorem)
- [Sufficient dimension reduction](https://en.wikipedia.org/wiki/Sufficient_dimension_reduction)
- [Ancillary statistic](https://en.wikipedia.org/wiki/Ancillary_statistic)

## Notes

1.  Dodge, Y. (2003) — entry for linear sufficiency
2.  [Fisher, R.A.](https://en.wikipedia.org/wiki/Ronald_Fisher) (1922). ["On the mathematical foundations of theoretical statistics"](http://digital.library.adelaide.edu.au/dspace/handle/2440/15172). *Philosophical Transactions of the Royal Society A*. **222** (594–604): 309–368. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1922RSPTA.222..309F](https://ui.adsabs.harvard.edu/abs/1922RSPTA.222..309F). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1098/rsta.1922.0009](https://doi.org/10.1098%2Frsta.1922.0009). [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[2440/15172](https://hdl.handle.net/2440%2F15172). [JFM](https://en.wikipedia.org/wiki/JFM_(identifier)) [48.1280.02](https://zbmath.org/?format=complete&q=an:48.1280.02). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [91208](https://www.jstor.org/stable/91208).
3.  [Stigler, Stephen](https://en.wikipedia.org/wiki/Stephen_Stigler) (December 1973). "Studies in the History of Probability and Statistics. XXXII: Laplace, Fisher and the Discovery of the Concept of Sufficiency". *Biometrika*. **60** (3): 439–445. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1093/biomet/60.3.439](https://doi.org/10.1093%2Fbiomet%2F60.3.439). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2334992](https://www.jstor.org/stable/2334992). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0326872](https://mathscinet.ams.org/mathscinet-getitem?mr=0326872).
4.  [Casella, George](https://en.wikipedia.org/wiki/George_Casella); [Berger, Roger L.](https://en.wikipedia.org/wiki/Roger_Lee_Berger) (2002). *Statistical Inference, 2nd ed*. Duxbury Press.
5.  Cover, Thomas M. (2006). *Elements of Information Theory*. Joy A. Thomas (2nd ed.). Hoboken, N.J.: Wiley-Interscience. p. 36. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-24195-4](https://en.wikipedia.org/wiki/Special:BookSources/0-471-24195-4). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [59879802](https://search.worldcat.org/oclc/59879802).
6.  Halmos, P. R.; Savage, L. J. (1949). ["Application of the Radon-Nikodym Theorem to the Theory of Sufficient Statistics"](https://projecteuclid.org/euclid.aoms/1177730032). *The Annals of Mathematical Statistics*. **20** (2): 225–241. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/aoms/1177730032](https://doi.org/10.1214%2Faoms%2F1177730032). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0003-4851](https://search.worldcat.org/issn/0003-4851).
7.  ["Factorization theorem - Encyclopedia of Mathematics"](https://encyclopediaofmath.org/wiki/Factorization_theorem). *encyclopediaofmath.org*. Retrieved 2022-09-07.
8.  Taraldsen, G. (2022). "The Factorization Theorem for Sufficiency". *Preprint*. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.13140/RG.2.2.15068.87687](https://doi.org/10.13140%2FRG.2.2.15068.87687).
9.  Hogg, Robert V.; Craig, Allen T. (1995). *Introduction to Mathematical Statistics*. Prentice Hall. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-02-355722-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-02-355722-4).
10. ["The Fisher–Neyman Factorization Theorem"](http://cnx.org/content/m11480/1.6/).. Webpage at Connexions (cnx.org)
11. Dodge (2003) — entry for minimal sufficient statistics
12. Lehmann and Casella (1998), *Theory of Point Estimation*, 2nd Edition, Springer, p 37
13. Lehmann and Casella (1998), *Theory of Point Estimation*, 2nd Edition, Springer, page 42
14. Tikochinsky, Y.; Tishby, N. Z.; Levine, R. D. (1984-11-01). ["Alternative approach to maximum-entropy inference"](https://dx.doi.org/10.1103/physreva.30.2638). *Physical Review A*. **30** (5): 2638–2644. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1984PhRvA..30.2638T](https://ui.adsabs.harvard.edu/abs/1984PhRvA..30.2638T). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1103/physreva.30.2638](https://doi.org/10.1103%2Fphysreva.30.2638). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0556-2791](https://search.worldcat.org/issn/0556-2791).
15. Andersen, Erling Bernhard (September 1970). ["Sufficiency and Exponential Families for Discrete Sample Spaces"](https://dx.doi.org/10.1080/01621459.1970.10481160). *Journal of the American Statistical Association*. **65** (331): 1248–1255. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/01621459.1970.10481160](https://doi.org/10.1080%2F01621459.1970.10481160). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0162-1459](https://search.worldcat.org/issn/0162-1459).
16. [Bernardo, J.M.](https://en.wikipedia.org/wiki/Jos%C3%A9-Miguel_Bernardo); [Smith, A.F.M.](https://en.wikipedia.org/wiki/Adrian_Smith_(academic)) (1994). "Section 5.1.4". *Bayesian Theory*. Wiley. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-92416-4](https://en.wikipedia.org/wiki/Special:BookSources/0-471-92416-4).
17. [Blackwell, D.](https://en.wikipedia.org/wiki/David_Blackwell); Ramamoorthi, R. V. (1982). ["A Bayes but not classically sufficient statistic"](https://doi.org/10.1214%2Faos%2F1176345895). *[Annals of Statistics](https://en.wikipedia.org/wiki/Annals_of_Statistics)*. **10** (3): 1025–1026. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/aos/1176345895](https://doi.org/10.1214%2Faos%2F1176345895). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0663456](https://mathscinet.ams.org/mathscinet-getitem?mr=0663456). [Zbl](https://en.wikipedia.org/wiki/Zbl_(identifier)) [0485.62004](https://zbmath.org/?format=complete&q=an:0485.62004).
18. Nogales, A.G.; Oyola, J.A.; Perez, P. (2000). ["On conditional independence and the relationship between sufficiency and invariance under the Bayesian point of view"](https://dialnet.unirioja.es/servlet/oaiart?codigo=118597). *Statistics & Probability Letters*. **46** (1): 75–84. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/S0167-7152(99)00089-9](https://doi.org/10.1016%2FS0167-7152%2899%2900089-9). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1731351](https://mathscinet.ams.org/mathscinet-getitem?mr=1731351). [Zbl](https://en.wikipedia.org/wiki/Zbl_(identifier)) [0964.62003](https://zbmath.org/?format=complete&q=an:0964.62003).
19. Goldstein, M.; O'Hagan, A. (1996). "Bayes Linear Sufficiency and Systems of Expert Posterior Assessments". *[Journal of the Royal Statistical Society](https://en.wikipedia.org/wiki/Journal_of_the_Royal_Statistical_Society)*. Series B. **58** (2): 301–316. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1111/j.2517-6161.1996.tb02083.x](https://doi.org/10.1111%2Fj.2517-6161.1996.tb02083.x). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2345978](https://www.jstor.org/stable/2345978).
20. Godambe, V. P. (1966). "A New Approach to Sampling from Finite Populations. II Distribution-Free Sufficiency". *[Journal of the Royal Statistical Society](https://en.wikipedia.org/wiki/Journal_of_the_Royal_Statistical_Society)*. Series B. **28** (2): 320–328. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1111/j.2517-6161.1966.tb00645.x](https://doi.org/10.1111%2Fj.2517-6161.1966.tb00645.x). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2984375](https://www.jstor.org/stable/2984375).
21. Witting, T. (1987). ["The linear Markov property in credibility theory"](https://doi.org/10.2143%2Fast.17.1.2014984). *ASTIN Bulletin*. **17** (1): 71–84. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2143/ast.17.1.2014984](https://doi.org/10.2143%2Fast.17.1.2014984). [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[20.500.11850/422507](https://hdl.handle.net/20.500.11850%2F422507).

## References

- Kholevo, A.S. (2001) \[1994\], ["Sufficient statistic"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society)
- Lehmann, E. L.; Casella, G. (1998). *Theory of Point Estimation* (2nd ed.). Springer. Chapter 4. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-98502-6](https://en.wikipedia.org/wiki/Special:BookSources/0-387-98502-6).
- Dodge, Y. (2003) *The Oxford Dictionary of Statistical Terms*, OUP. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-19-920613-9](https://en.wikipedia.org/wiki/Special:BookSources/0-19-920613-9)
