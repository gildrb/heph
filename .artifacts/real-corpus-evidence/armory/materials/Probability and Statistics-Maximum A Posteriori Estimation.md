[[probability-statistics.base]]

> Source: [[Maximum A Posteriori Estimation]]
> License: Wikipedia content is available under CC BY-SA 4.0.

An estimation procedure that is often claimed to be part of [Bayesian statistics](https://en.wikipedia.org/wiki/Bayesian_statistics) is the **maximum a posteriori** (**MAP**) **estimate** of an unknown quantity, that equals the [mode](https://en.wikipedia.org/wiki/Mode_(statistics) "Mode (statistics)") of the [posterior](https://en.wikipedia.org/wiki/Posterior_distribution) [[Probability Density Function|density]] with respect to some reference measure, typically the [Lebesgue measure](https://en.wikipedia.org/wiki/Lebesgue_measure). The MAP can be used to obtain a [point estimate](https://en.wikipedia.org/wiki/Point_estimation) of an unobserved quantity on the basis of empirical data. It is closely related to the method of [maximum likelihood](https://en.wikipedia.org/wiki/Maximum_likelihood) (ML) estimation, but employs an augmented [optimization objective](https://en.wikipedia.org/wiki/Optimization_(mathematics)) which incorporates a [prior](https://en.wikipedia.org/wiki/Prior_probability) [[Probability Density Function|density]] over the quantity one wants to estimate. MAP estimation is therefore a [regularization](https://en.wikipedia.org/wiki/Regularization_(mathematics) "Regularization (mathematics)") of maximum likelihood estimation, so is not a well-defined statistic of the Bayesian posterior distribution.

## Description

Assume that we want to estimate an unobserved population parameter $\theta$ on the basis of observations $x$. Let $f$ be the [sampling distribution](https://en.wikipedia.org/wiki/Sampling_distribution) of $x$, so that $f(x\mid \theta )$ is the probability of $x$ when the underlying population parameter is $\theta$. Then the function:

$\theta \mapsto f(x\mid \theta )\!$

is known as the [likelihood function](https://en.wikipedia.org/wiki/Likelihood_function) and the estimate:

${\hat {\theta }}_{\mathrm {MLE} }(x)={\underset {\theta }{\operatorname {arg\,max} }}\ f(x\mid \theta )\!$

is the maximum likelihood estimate of $\theta$.

Now assume that a [prior distribution](https://en.wikipedia.org/wiki/Prior_distribution) $g$ over $\theta$ exists. This allows us to treat $\theta$ as a [random variable](https://en.wikipedia.org/wiki/Random_variable) as in [Bayesian statistics](https://en.wikipedia.org/wiki/Bayesian_statistics). We can calculate the [posterior density](https://en.wikipedia.org/wiki/Posterior_distribution) of $\theta$ using [[Bayes Theorem|Bayes' theorem]]:

$\theta \mapsto f(\theta \mid x)={\frac {f(x\mid \theta )\,g(\theta )}{\displaystyle \int _{\Theta }f(x\mid \vartheta )\,g(\vartheta )\,d\vartheta }}\!$

where $g$ is density function of $\theta$, $\Theta$ is the domain of $g$.

The method of maximum a posteriori estimation then estimates $\theta$ as the [mode](https://en.wikipedia.org/wiki/Mode_(statistics) "Mode (statistics)") of the posterior density of this random variable:

${\begin{aligned}{\hat {\theta }}_{\mathrm {MAP} }(x)&={\underset {\theta }{\operatorname {arg\,max} }}\ f(\theta \mid x)\\&={\underset {\theta }{\operatorname {arg\,max} }}\ {\frac {f(x\mid \theta )\,g(\theta )}{\displaystyle \int _{\Theta }f(x\mid \vartheta )\,g(\vartheta )\,d\vartheta }}\\&={\underset {\theta }{\operatorname {arg\,max} }}\ f(x\mid \theta )\,g(\theta ).\end{aligned}}\!$

The denominator of the posterior density (the [marginal likelihood](https://en.wikipedia.org/wiki/Marginal_likelihood) of the model) is always positive and does not depend on $\theta$ and therefore plays no role in the optimization. Observe that the MAP estimate of $\theta$ coincides with the ML estimate when the prior $g$ is uniform (i.e., $g$ is a [constant function](https://en.wikipedia.org/wiki/Constant_function)), which occurs whenever the prior distribution is taken as the reference measure, as is typical in function-space applications.

When the [loss function](https://en.wikipedia.org/wiki/Loss_function) is of the form

$L(\theta ,a)={\begin{cases}0,&{\text{if }}|a-\theta |<c,\\1,&{\text{otherwise}},\\\end{cases}}$

as $c$ goes to 0, the [Bayes estimator](https://en.wikipedia.org/wiki/Bayes_estimator) approaches the MAP estimator, provided that the distribution of $\theta$ is quasi-concave. But generally a MAP estimator is not a [Bayes estimator](https://en.wikipedia.org/wiki/Bayes_estimator) unless $\theta$ is [discrete](https://en.wikipedia.org/wiki/Discrete_random_variable).

## Computation

MAP estimates can be computed in several ways:

1.  Analytically, when the mode(s) of the posterior density can be given in [closed form](https://en.wikipedia.org/wiki/Closed-form_solution). This is the case when [conjugate priors](https://en.wikipedia.org/wiki/Conjugate_prior) are used.
2.  Via [numerical](https://en.wikipedia.org/wiki/Numerical_analysis) [optimization](https://en.wikipedia.org/wiki/Optimization_(mathematics)) such as the [[Conjugate Gradient Method]] or [Newton's method](https://en.wikipedia.org/wiki/Newton%27s_method_in_optimization). This usually requires first or second [derivatives](https://en.wikipedia.org/wiki/Derivative), which have to be evaluated analytically or numerically.
3.  Via a modification of an [expectation-maximization algorithm](https://en.wikipedia.org/wiki/Expectation-maximization_algorithm). This does not require derivatives of the posterior density.
4.  Via a [[Monte Carlo Method]] using [simulated annealing](https://en.wikipedia.org/wiki/Simulated_annealing)

## Limitations

While only mild conditions are required for MAP estimation to be a limiting case of [Bayes estimation](https://en.wikipedia.org/wiki/Bayes_estimator) (under the 0–1 loss function), it is not representative of Bayesian methods in general. This is because MAP estimates are point estimates, and depend on the arbitrary choice of reference measure, whereas Bayesian methods are characterized by the use of distributions to summarize data and draw inferences: thus, Bayesian methods tend to report the posterior [mean](https://en.wikipedia.org/wiki/Mean) or [median](https://en.wikipedia.org/wiki/Median) instead, together with [credible intervals](https://en.wikipedia.org/wiki/Credible_interval). This is both because these estimators are optimal under squared-error and linear-error loss respectively—which are more representative of typical [loss functions](https://en.wikipedia.org/wiki/Loss_function)—and for a continuous posterior distribution there is no loss function which suggests the MAP is the optimal point estimator. In addition, the posterior density may often not have a simple analytic form: in this case, the distribution can be simulated using [[Markov Chain Monte Carlo]] techniques, while optimization to find the mode(s) of the density may be difficult or impossible.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

![[media/2abdb2a6e36342c74fc983a0b1d655815ac15ea7.png]]
An example of a density of a [bimodal distribution](https://en.wikipedia.org/wiki/Bimodal_distribution) in which the highest mode is uncharacteristic of the majority of the distribution

In many types of models, such as [mixture models](https://en.wikipedia.org/wiki/Mixture_model), the posterior may be [multi-modal](https://en.wikipedia.org/wiki/Bimodal_distribution). In such a case, the usual recommendation is that one should choose the highest mode: this is not always feasible ([global optimization](https://en.wikipedia.org/wiki/Global_optimization) is a difficult problem), nor in some cases even possible (such as when [identifiability](https://en.wikipedia.org/wiki/Identifiability_condition) issues arise). Furthermore, the highest mode may be uncharacteristic of the majority of the posterior, especially in many dimensions.

Finally, unlike ML estimators, the MAP estimate is not invariant under reparameterization. Switching from one parameterization to another involves introducing a [Jacobian](https://en.wikipedia.org/wiki/Jacobian_matrix_and_determinant) that impacts on the location of the maximum. In contrast, Bayesian posterior expectations are invariant under reparameterization.

As an example of the difference between Bayes estimators mentioned above (mean and median estimators) and using a MAP estimate, consider the case where there is a need to classify inputs $x$ as either positive or negative (for example, loans as risky or safe). Suppose there are just three possible hypotheses about the correct method of classification $h_{1}$, $h_{2}$ and $h_{3}$ with posteriors 0.4, 0.3 and 0.3 respectively. Suppose given a new instance, $x$, $h_{1}$ classifies it as positive, whereas the other two classify it as negative. Using the MAP estimate for the correct classifier $h_{1}$, $x$ is classified as positive, whereas the Bayes estimators would average over all hypotheses and classify $x$ as negative.

## Example

Suppose that we are given a sequence $(x_{1},\dots ,x_{n})$ of [IID](https://en.wikipedia.org/wiki/IID) $N(\mu ,\sigma _{v}^{2})$ [random variables](https://en.wikipedia.org/wiki/Random_variable) and a prior distribution of $\mu$ is given by $N(\mu _{0},\sigma _{m}^{2})$. We wish to find the MAP estimate of $\mu$. Note that the normal distribution is its own [conjugate prior](https://en.wikipedia.org/wiki/Conjugate_prior), so we will be able to find a [closed-form solution](https://en.wikipedia.org/wiki/Closed-form_solution) analytically.

The function to be maximized is then given by

$g(\mu )f(x\mid \mu )=\pi (\mu )L(\mu )={\frac {1}{{\sqrt {2\pi }}\sigma _{m}}}\exp \left(-{\frac {1}{2}}\left({\frac {\mu -\mu _{0}}{\sigma _{m}}}\right)^{2}\right)\prod _{j=1}^{n}{\frac {1}{{\sqrt {2\pi }}\sigma _{v}}}\exp \left(-{\frac {1}{2}}\left({\frac {x_{j}-\mu }{\sigma _{v}}}\right)^{2}\right),$

which is equivalent to minimizing the following function of $\mu$:

$\sum _{j=1}^{n}\left({\frac {x_{j}-\mu }{\sigma _{v}}}\right)^{2}+\left({\frac {\mu -\mu _{0}}{\sigma _{m}}}\right)^{2}.$

Thus, we see that the **MAP estimator** for μ is given by

${\hat {\mu }}_{\mathrm {MAP} }={\frac {\sigma _{m}^{2}\,n}{\sigma _{m}^{2}\,n+\sigma _{v}^{2}}}\left({\frac {1}{n}}\sum _{j=1}^{n}x_{j}\right)+{\frac {\sigma _{v}^{2}}{\sigma _{m}^{2}\,n+\sigma _{v}^{2}}}\,\mu _{0}={\frac {\sigma _{m}^{2}\left(\sum _{j=1}^{n}x_{j}\right)+\sigma _{v}^{2}\,\mu _{0}}{\sigma _{m}^{2}\,n+\sigma _{v}^{2}}}.$

which turns out to be a [linear interpolation](https://en.wikipedia.org/wiki/Linear_interpolation) between the prior mean and the sample mean weighted by their respective covariances.

The case of $\sigma _{m}\to \infty$ is called a non-informative prior and leads to an improper [probability distribution](https://en.wikipedia.org/wiki/Probability_distribution); in this case ${\hat {\mu }}_{\mathrm {MAP} }\to {\hat {\mu }}_{\mathrm {MLE} }.$

## References

1.  ^   Bassett, Robert; Deride, Julio (2018-01-30). "Maximum a posteriori estimators as a limit of Bayes estimators". *Mathematical Programming*. **174** (1–2): 129–144. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1611.05917](https://arxiv.org/abs/1611.05917). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s10107-018-1241-0](https://doi.org/10.1007%2Fs10107-018-1241-0). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0025-5610](https://search.worldcat.org/issn/0025-5610).
2.  Murphy, Kevin P. (2012). *Machine learning : a probabilistic perspective*. Cambridge, Massachusetts: MIT Press. pp. 151–152. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-262-01802-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-262-01802-9).
3.  ^   Young, G. A.; Smith, R. L. (2005). [Essentials of Statistical Inference](https://www.cambridge.org/core/books/essentials-of-statistical-inference/7CDE4B08DD68DE7EE0B00F778FC29CCD). Cambridge Series in Statistical and Probabilistic Mathematics. Cambridge: Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-83971-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-83971-6).

- DeGroot, M. (1970). *Optimal Statistical Decisions*. McGraw-Hill. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-07-016242-5](https://en.wikipedia.org/wiki/Special:BookSources/0-07-016242-5).
- Sorenson, Harold W. (1980). *Parameter Estimation: Principles and Problems*. Marcel Dekker. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-8247-6987-2](https://en.wikipedia.org/wiki/Special:BookSources/0-8247-6987-2).
- Hald, Anders (2007). "Gauss's Derivation of the Normal Distribution and the Method of Least Squares, 1809". *A History of Parametric Statistical Inference from Bernoulli to Fisher, 1713–1935*. New York: Springer. pp. 55–61. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-46409-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-46409-1).
