[[probability-statistics.base]]

> Source: [[Maximum Likelihood Estimation]]
> License: Wikipedia content is available under CC BY-SA 4.0.

In [statistics](https://en.wikipedia.org/wiki/Statistics), **maximum likelihood estimation** (**MLE**) is a method of [estimating](https://en.wikipedia.org/wiki/Estimation_theory) the [parameters](https://en.wikipedia.org/wiki/Statistical_parameter) of an assumed [probability distribution](https://en.wikipedia.org/wiki/Probability_distribution), given some observed data. This is achieved by [maximizing](https://en.wikipedia.org/wiki/Mathematical_optimization) a [likelihood function](https://en.wikipedia.org/wiki/Likelihood_function) so that, under the assumed [statistical model](https://en.wikipedia.org/wiki/Statistical_model), the [observed data](https://en.wikipedia.org/wiki/Realization_(probability) "Realization (probability)") is most probable. The [point](https://en.wikipedia.org/wiki/Point_estimate) in the [parameter space](https://en.wikipedia.org/wiki/Parameter_space) that maximizes the likelihood function is called the maximum likelihood estimate. The logic of maximum likelihood is both intuitive and flexible, and as such the method has become a dominant means of [statistical inference](https://en.wikipedia.org/wiki/Statistical_inference).

If the likelihood function is [differentiable](https://en.wikipedia.org/wiki/Differentiable_function), the [derivative test](https://en.wikipedia.org/wiki/Derivative_test) for finding maxima can be applied. In some cases, the first-order conditions of the likelihood function can be solved analytically; for instance, the [ordinary least squares](https://en.wikipedia.org/wiki/Ordinary_least_squares) estimator for a [linear regression](https://en.wikipedia.org/wiki/Linear_regression) model maximizes the likelihood when the random errors are assumed to have [normal](https://en.wikipedia.org/wiki/Normal_distribution) distributions with the same variance.

From the perspective of [Bayesian inference](https://en.wikipedia.org/wiki/Bayesian_inference), MLE is generally equivalent to [[Maximum A Posteriori Estimation|maximum a posteriori (MAP) estimation]] with a [prior distribution](https://en.wikipedia.org/wiki/Prior_probability) that is [uniform](https://en.wikipedia.org/wiki/Uniform_distribution_(continuous)) in the region of interest. In [frequentist inference](https://en.wikipedia.org/wiki/Frequentist_inference), MLE is a special case of an [extremum estimator](https://en.wikipedia.org/wiki/Extremum_estimator), with the objective function being the likelihood.

## Principles

We model a set of observations as a random [sample](https://en.wikipedia.org/wiki/Sample_(statistics)) from an unknown [joint probability distribution](https://en.wikipedia.org/wiki/Joint_probability_distribution) which is expressed in terms of a set of [parameters](https://en.wikipedia.org/wiki/Statistical_parameters). The goal of maximum likelihood estimation is to determine the parameters for which the observed data have the highest joint probability. We write the parameters governing the joint distribution as a vector $\;\theta =\left[\theta _{1},\,\theta _{2},\,\ldots ,\,\theta _{k}\right]^{\mathsf {T}}\;$ so that this distribution falls within a [parametric family](https://en.wikipedia.org/wiki/Parametric_family) $\;\{f(\cdot \,;\theta )\mid \theta \in \Theta \}\;,$ where $\,\Theta \,$ is called the *[parameter space](https://en.wikipedia.org/wiki/Parameter_space)*, a finite-dimensional subset of [Euclidean space](https://en.wikipedia.org/wiki/Euclidean_space). Evaluating the joint density at the observed data sample $\;\mathbf {y} =(y_{1},y_{2},\ldots ,y_{n})\;$ gives a real-valued function, 

$$
{\mathcal {L}}_{n}(\theta )={\mathcal {L}}_{n}(\theta ;\mathbf {y} )=f_{n}(\mathbf {y} ;\theta )\;,
$$

 which is called the [likelihood function](https://en.wikipedia.org/wiki/Likelihood_function). For [independent random variables](https://en.wikipedia.org/wiki/Independence_(probability_theory) "Independence (probability theory)"), $f_{n}(\mathbf {y} ;\theta )$ will be the product of univariate [[Probability Density Function|density functions]]: 

$$
f_{n}(\mathbf {y} ;\theta )=\prod _{k=1}^{n}\,f_{k}^{\mathsf {univar}}(y_{k};\theta )~.
$$

The goal of maximum likelihood estimation is to find the values of the model parameters that maximize the likelihood function over the parameter space, that is: 

$$
{\hat {\theta }}={\underset {\theta \in \Theta }{\operatorname {arg\;max} }}\,{\mathcal {L}}_{n}(\theta \,;\mathbf {y} )~.
$$

Intuitively, this selects the parameter values that make the observed data most probable. The specific value $~{\hat {\theta }}={\hat {\theta }}_{n}(\mathbf {y} )\in \Theta ~$ that maximizes the likelihood function $\,{\mathcal {L}}_{n}\,$ is called the maximum likelihood estimate. Further, if the function $\;{\hat {\theta }}_{n}:\mathbb {R} ^{n}\to \Theta \;$ so defined is [measurable](https://en.wikipedia.org/wiki/Measurable_function), then it is called the maximum likelihood [estimator](https://en.wikipedia.org/wiki/Estimator). It is generally a function defined over the [sample space](https://en.wikipedia.org/wiki/Sample_space), i.e. taking a given sample as its argument. A [sufficient but not necessary](https://en.wikipedia.org/wiki/Necessity_and_sufficiency) condition for its existence is for the likelihood function to be [continuous](https://en.wikipedia.org/wiki/Continuous_function) over a parameter space $\,\Theta \,$ that is [compact](https://en.wikipedia.org/wiki/Compact_space). For an [open](https://en.wikipedia.org/wiki/Open_set) $\,\Theta \,$ the likelihood function may increase without ever reaching a supremum value.

In practice, it is often convenient to work with the [natural logarithm](https://en.wikipedia.org/wiki/Natural_logarithm) of the likelihood function, called the [log-likelihood](https://en.wikipedia.org/wiki/Log-likelihood): 

$$
\ell (\theta \,;\mathbf {y} )=\ln {\mathcal {L}}_{n}(\theta \,;\mathbf {y} )~.
$$

 Since the logarithm is a [monotonic function](https://en.wikipedia.org/wiki/Monotonic_function), the maximum of $\;\ell (\theta \,;\mathbf {y} )\;$ occurs at the same value of $\theta$ as does the maximum of $\,{\mathcal {L}}_{n}~.$ If $\ell (\theta \,;\mathbf {y} )$ is [differentiable](https://en.wikipedia.org/wiki/Differentiable_function) in $\,\Theta \,,$ [necessary conditions](https://en.wikipedia.org/wiki/Derivative_test) for the occurrence of a maximum (or a minimum) are 

$$
{\frac {\partial \ell }{\partial \theta _{1}}}=0,\quad {\frac {\partial \ell }{\partial \theta _{2}}}=0,\quad \ldots ,\quad {\frac {\partial \ell }{\partial \theta _{k}}}=0~,
$$

 known as the likelihood equations. For some models, these equations can be explicitly solved for $\,{\widehat {\theta \,}}\,,$ but in general no closed-form solution to the maximization problem is known or available, and an MLE can only be found via [numerical optimization](https://en.wikipedia.org/wiki/Mathematical_optimization). Another problem is that in finite samples, there may exist multiple [roots](https://en.wikipedia.org/wiki/Zero_of_a_function) for the likelihood equations. Whether the identified root $\,{\widehat {\theta \,}}\,$ of the likelihood equations is indeed a (local) maximum depends on whether the matrix of second-order partial and cross-partial derivatives, the so-called [[Hessian Matrix]]

$$
\mathbf {H} \left({\widehat {\theta \,}}\right)={\begin{bmatrix}\left.{\frac {\partial ^{2}\ell }{\partial \theta _{1}^{2}}}\right|_{\theta ={\widehat {\theta \,}}}&\left.{\frac {\partial ^{2}\ell }{\partial \theta _{1}\,\partial \theta _{2}}}\right|_{\theta ={\widehat {\theta \,}}}&\dots &\left.{\frac {\partial ^{2}\ell }{\partial \theta _{1}\,\partial \theta _{k}}}\right|_{\theta ={\widehat {\theta \,}}}\\\left.{\frac {\partial ^{2}\ell }{\partial \theta _{2}\,\partial \theta _{1}}}\right|_{\theta ={\widehat {\theta \,}}}&\left.{\frac {\partial ^{2}\ell }{\partial \theta _{2}^{2}}}\right|_{\theta ={\widehat {\theta \,}}}&\dots &\left.{\frac {\partial ^{2}\ell }{\partial \theta _{2}\,\partial \theta _{k}}}\right|_{\theta ={\widehat {\theta \,}}}\\\vdots &\vdots &\ddots &\vdots \\\left.{\frac {\partial ^{2}\ell }{\partial \theta _{k}\,\partial \theta _{1}}}\right|_{\theta ={\widehat {\theta \,}}}&\left.{\frac {\partial ^{2}\ell }{\partial \theta _{k}\,\partial \theta _{2}}}\right|_{\theta ={\widehat {\theta \,}}}&\dots &\left.{\frac {\partial ^{2}\ell }{\partial \theta _{k}^{2}}}\right|_{\theta ={\widehat {\theta \,}}}\end{bmatrix}}~,
$$

is [negative semi-definite](https://en.wikipedia.org/wiki/Negative_semi-definite) at ${\widehat {\theta \,}}$, as this indicates local [concavity](https://en.wikipedia.org/wiki/Concave_function). Conveniently, most common [probability distributions](https://en.wikipedia.org/wiki/Probability_distribution) – in particular the [[Exponential Family]] – are [logarithmically concave](https://en.wikipedia.org/wiki/Logarithmically_concave_function).

### Restricted parameter space

While the domain of the likelihood function—the [parameter space](https://en.wikipedia.org/wiki/Parameter_space)—is generally a finite-dimensional subset of [Euclidean space](https://en.wikipedia.org/wiki/Euclidean_space), additional [restrictions](https://en.wikipedia.org/wiki/Restriction_(mathematics) "Restriction (mathematics)") sometimes need to be incorporated into the estimation process. The parameter space can be expressed as 

$$
\Theta =\left\{\theta :\theta \in \mathbb {R} ^{k},\;h(\theta )=0\right\}~,
$$

where $\;h(\theta )=\left[h_{1}(\theta ),h_{2}(\theta ),\ldots ,h_{r}(\theta )\right]\;$ is a [vector-valued function](https://en.wikipedia.org/wiki/Vector-valued_function) mapping $\,\mathbb {R} ^{k}\,$ into $\;\mathbb {R} ^{r}~.$ Estimating the true parameter $\theta$ belonging to $\Theta$ then, as a practical matter, means to find the maximum of the likelihood function subject to the [constraint](https://en.wikipedia.org/wiki/Constraint_(mathematics) "Constraint (mathematics)") $~h(\theta )=0~.$

Theoretically, the most natural approach to this [[Constrained Optimization]] problem is the method of substitution, that is "filling out" the restrictions $\;h_{1},h_{2},\ldots ,h_{r}\;$ to a set $\;h_{1},h_{2},\ldots ,h_{r},h_{r+1},\ldots ,h_{k}\;$ in such a way that $\;h^{\ast }=\left[h_{1},h_{2},\ldots ,h_{k}\right]\;$ is a [one-to-one function](https://en.wikipedia.org/wiki/One-to-one_function) from $\mathbb {R} ^{k}$ to itself, and reparameterize the likelihood function by setting $\;\phi _{i}=h_{i}(\theta _{1},\theta _{2},\ldots ,\theta _{k})~.$ Because of the equivariance of the maximum likelihood estimator, the properties of the MLE apply to the restricted estimates also. For instance, in a [[Multivariate Normal Distribution]] the [covariance matrix](https://en.wikipedia.org/wiki/Covariance_matrix) $\,\Sigma \,$ must be [[Positive-Definite Matrix|positive-definite]]; this restriction can be imposed by replacing $\;\Sigma =\Gamma ^{\mathsf {T}}\Gamma \;,$ where $\Gamma$ is a real [upper triangular matrix](https://en.wikipedia.org/wiki/Upper_triangular_matrix) and $\Gamma ^{\mathsf {T}}$ is its [transpose](https://en.wikipedia.org/wiki/Transpose).

In practice, restrictions are usually imposed using the method of Lagrange which, given the constraints as defined above, leads to the *restricted likelihood equations* 

$$
{\frac {\partial \ell }{\partial \theta }}-{\frac {\partial h(\theta )^{\mathsf {T}}}{\partial \theta }}\lambda =0
$$

 and $h(\theta )=0\;,$

where $~\lambda =\left[\lambda _{1},\lambda _{2},\ldots ,\lambda _{r}\right]^{\mathsf {T}}~$ is a column-vector of [Lagrange multipliers](https://en.wikipedia.org/wiki/Lagrange_multiplier) and $\;{\frac {\partial h(\theta )^{\mathsf {T}}}{\partial \theta }}\;$ is the k × r [[Jacobian Matrix]] of partial derivatives. Naturally, if the constraints are not binding at the maximum, the Lagrange multipliers should be zero. This in turn allows for a statistical test of the "validity" of the constraint, known as the [Lagrange multiplier test](https://en.wikipedia.org/wiki/Lagrange_multiplier_test).

### Nonparametric maximum likelihood estimation

Nonparametric maximum likelihood estimation can be performed using the [empirical likelihood](https://en.wikipedia.org/wiki/Empirical_likelihood).

## Properties

A maximum likelihood estimator is an [extremum estimator](https://en.wikipedia.org/wiki/Extremum_estimator) obtained by maximizing, as a function of *θ*, the [objective function](https://en.wikipedia.org/wiki/Objective_function) ${\widehat {\ell \,}}(\theta \,;x)$. If the data are [independent and identically distributed](https://en.wikipedia.org/wiki/Independent_and_identically_distributed), then we have 

$$
{\widehat {\ell \,}}(\theta \,;x)=\sum _{i=1}^{n}\ln f(x_{i}\mid \theta ),
$$

 this being the sample analogue of the expected log-likelihood $\ell (\theta )=\operatorname {\mathbb {E} } [\,\ln f(x_{i}\mid \theta )\,]$, where this expectation is taken with respect to the true density.

Maximum-likelihood estimators have no optimum properties for finite samples, in the sense that (when evaluated on finite samples) other estimators may have greater concentration around the true parameter-value. However, like other estimation methods, maximum likelihood estimation possesses a number of attractive [limiting properties](https://en.wikipedia.org/wiki/Asymptotic_theory_(statistics) "Asymptotic theory (statistics)"): As the sample size increases to infinity, sequences of maximum likelihood estimators have these properties:

- [Consistency](https://en.wikipedia.org/wiki/Consistency_of_an_estimator): the sequence of MLEs converges in probability to the value being estimated.
- [Equivariance](https://en.wikipedia.org/wiki/Invariant_estimator): If ${\hat {\theta }}$ is the maximum likelihood estimator for $\theta$, and if $g(\theta )$ is a bijective transform of $\theta$, then the maximum likelihood estimator for $\alpha =g(\theta )$ is ${\hat {\alpha }}=g({\hat {\theta }})$. The equivariance property can be generalized to non-bijective transforms, although it applies in that case on the maximum of an induced likelihood function which is not the true likelihood in general.
- [Efficiency](https://en.wikipedia.org/wiki/Efficient_estimator), i.e. it achieves the [Cramér–Rao lower bound](https://en.wikipedia.org/wiki/Cram%C3%A9r%E2%80%93Rao_lower_bound) when the sample size tends to infinity. This means that no consistent estimator has lower asymptotic [mean squared error](https://en.wikipedia.org/wiki/Mean_squared_error) than the MLE (or other estimators attaining this bound), which also means that MLE has [asymptotic normality](https://en.wikipedia.org/wiki/Local_asymptotic_normality).
- Second-order efficiency after correction for bias.

### Consistency

Under the conditions outlined below, the maximum likelihood estimator is [consistent](https://en.wikipedia.org/wiki/Consistent_estimator). The consistency means that if the data were generated by $f(\cdot \,;\theta _{0})$ and we have a sufficiently large number of observations *n*, then it is possible to find the value of *θ*<sub>0</sub> with arbitrary precision. In mathematical terms this means that as *n* goes to infinity the estimator ${\widehat {\theta \,}}$ [converges in probability](https://en.wikipedia.org/wiki/Convergence_in_probability) to its true value:

$$
{\widehat {\theta \,}}_{\mathrm {mle} }\ \xrightarrow {\text{p}} \ \theta _{0}.
$$

Under slightly stronger conditions, the estimator converges [almost surely](https://en.wikipedia.org/wiki/Almost_sure_convergence) (or *strongly*):

$$
{\widehat {\theta \,}}_{\mathrm {mle} }\ \xrightarrow {\text{a.s.}} \ \theta _{0}.
$$

In practical applications, data is never generated by $f(\cdot \,;\theta _{0})$. Rather, $f(\cdot \,;\theta _{0})$ is a model, often in idealized form, of the process generated by the data. It is a common aphorism in statistics that *[all models are wrong](https://en.wikipedia.org/wiki/All_models_are_wrong)*. Thus, true consistency does not occur in practical applications. Nevertheless, consistency is often considered to be a desirable property for an estimator to have.

To establish consistency, the following conditions are sufficient.

1.  [Identification](https://en.wikipedia.org/wiki/Identifiability) of the model:

$$
\theta \neq \theta _{0}\quad \Leftrightarrow \quad f(\cdot \mid \theta )\neq f(\cdot \mid \theta _{0}).
$$

 In other words, different parameter values *θ* correspond to different distributions within the model. If this condition did not hold, there would be some value *θ*<sub>1</sub> such that *θ*<sub>0</sub> and *θ*<sub>1</sub> generate an identical distribution of the observable data. Then we would not be able to distinguish between these two parameters even with an infinite amount of data—these parameters would have been [observationally equivalent](https://en.wikipedia.org/wiki/Observational_equivalence).  

    The identification condition is absolutely necessary for the ML estimator to be consistent. When this condition holds, the limiting likelihood function *ℓ*(*θ*\|·) has unique global maximum at *θ*<sub>0</sub>.

2.  Compactness: the parameter space Θ of the model is [compact](https://en.wikipedia.org/wiki/Compact_set).

    ![[media/13260d099d3b3cb68eaf583eca3e84e8b8d5dabb.png]]

    The identification condition establishes that the log-likelihood has a unique global maximum. Compactness implies that the likelihood cannot approach the maximum value arbitrarily close at some other point (as demonstrated for example in the picture on the right).

    Compactness is only a sufficient condition and not a necessary condition. Compactness can be replaced by some other conditions, such as:

    - both [concavity](https://en.wikipedia.org/wiki/Concave_function) of the log-likelihood function and compactness of some (nonempty) upper [level sets](https://en.wikipedia.org/wiki/Level_set) of the log-likelihood function, or
    - existence of a compact [neighborhood](https://en.wikipedia.org/wiki/Neighbourhood_(mathematics) "Neighbourhood (mathematics)") N of θ<sub>0</sub> such that outside of N the log-likelihood function is less than the maximum by at least some ε \> 0.

3.  Continuity: the function ln *f*(*x* \| *θ*) is continuous in θ for almost all values of x:

$$
\operatorname {\mathbb {P} } {\Bigl [}\;\ln f(x\mid \theta )\;\in \;C^{0}(\Theta )\;{\Bigr ]}=1.
$$

    The continuity here can be replaced with a slightly weaker condition of [upper semi-continuity](https://en.wikipedia.org/wiki/Upper_semi-continuous).

4.  Dominance: there exists *D*(*x*) integrable with respect to the distribution *f*(*x* \| *θ*<sub>0</sub>) such that 

$$
{\Bigl |}\ln f(x\mid \theta ){\Bigr |}<D(x)\quad {\text{ for all }}\theta \in \Theta .
$$

 By the [uniform law of large numbers](https://en.wikipedia.org/wiki/Uniform_law_of_large_numbers), the dominance condition together with continuity establish the uniform convergence in probability of the log-likelihood: 

$$
\sup _{\theta \in \Theta }\left|{\widehat {\ell \,}}(\theta \mid x)-\ell (\theta )\,\right|\ \xrightarrow {\text{p}} \ 0.
$$

The dominance condition can be employed in the case of [i.i.d.](https://en.wikipedia.org/wiki/I.i.d.) observations. In the non-i.i.d. case, the uniform convergence in probability can be checked by showing that the sequence ${\widehat {\ell \,}}(\theta \mid x)$ is [stochastically equicontinuous](https://en.wikipedia.org/wiki/Stochastic_equicontinuity).

If one wants to demonstrate that the ML estimator ${\widehat {\theta \,}}$ converges to *θ*<sub>0</sub> [almost surely](https://en.wikipedia.org/wiki/Almost_sure_convergence), then a stronger condition of uniform convergence almost surely has to be imposed: 

$$
\sup _{\theta \in \Theta }\left\|\;{\widehat {\ell \,}}(\theta \mid x)-\ell (\theta )\;\right\|\ \xrightarrow {\text{a.s.}} \ 0.
$$

Additionally, if (as assumed above) the data were generated by $f(\cdot \,;\theta _{0})$, then under certain conditions, it can also be shown that the maximum likelihood estimator [converges in distribution](https://en.wikipedia.org/wiki/Convergence_in_distribution) to a normal distribution. Specifically, 

$$
{\sqrt {n}}\left({\widehat {\theta \,}}_{\mathrm {mle} }-\theta _{0}\right)\ \xrightarrow {d} \ {\mathcal {N}}\left(0,\,I^{-1}\right)
$$

 where *I* is the [[Fisher Information|Fisher information matrix]].

### Functional invariance

The maximum likelihood estimator selects the parameter value which gives the observed data the largest possible probability (or probability density, in the continuous case). If the parameter consists of a number of components, then we define their separate maximum likelihood estimators, as the corresponding component of the MLE of the complete parameter. Consistent with this, if ${\widehat {\theta \,}}$ is the MLE for $\theta$, and if $g(\theta )$ is any transformation of $\theta$, then the MLE for $\alpha =g(\theta )$ is by definition

$$
{\widehat {\alpha }}=g(\,{\widehat {\theta \,}}\,).\,
$$

It maximizes the so-called [profile likelihood](https://en.wikipedia.org/wiki/Likelihood_function#Profile_likelihood):

$$
{\bar {L}}(\alpha )=\sup _{\theta :\alpha =g(\theta )}L(\theta ).\,
$$

The MLE is also equivariant with respect to certain transformations of the data. If $y=g(x)$ where $g$ is one to one and does not depend on the parameters to be estimated, then the density functions satisfy

$$
f_{Y}(y)=f_{X}(g^{-1}(y))\,|(g^{-1}(y))^{\prime }|
$$

and hence the likelihood functions for $X$ and $Y$ differ only by a factor that does not depend on the model parameters.

For example, the MLE parameters of the log-normal distribution are the same as those of the normal distribution fitted to the logarithm of the data. In fact, in the log-normal case if $X\sim {\mathcal {N}}(0,1)$, then $Y=g(X)=e^{X}$ follows a [log-normal distribution](https://en.wikipedia.org/wiki/Log-normal_distribution). The density of Y follows with $f_{X}$ standard [Normal](https://en.wikipedia.org/wiki/Normal_distribution) and $g^{-1}(y)=\log(y)$, $|(g^{-1}(y))^{\prime }|={\frac {1}{y}}$ for $y>0$.

### Efficiency

As assumed above, if the data were generated by $~f(\cdot \,;\theta _{0})~,$ then under certain conditions, it can also be shown that the maximum likelihood estimator [converges in distribution](https://en.wikipedia.org/wiki/Convergence_in_distribution) to a normal distribution. It is √*n* -consistent and asymptotically efficient, meaning that it reaches the [Cramér–Rao bound](https://en.wikipedia.org/wiki/Cram%C3%A9r%E2%80%93Rao_bound). Specifically,

$$
{\sqrt {n\,}}\,\left({\widehat {\theta \,}}_{\text{mle}}-\theta _{0}\right)\ \ \xrightarrow {d} \ \ {\mathcal {N}}\left(0,\ {\mathcal {I}}^{-1}\right)~,
$$

 where $~{\mathcal {I}}~$ is the [Fisher information matrix](https://en.wikipedia.org/wiki/Fisher_information_matrix): 

$$
{\mathcal {I}}_{jk}=\operatorname {\mathbb {E} } \,{\biggl [}\;-{\frac {\partial ^{2}\ln f_{\theta _{0}}(X_{t})}{\partial \theta _{j}\,\partial \theta _{k}}}\;{\biggr ]}~.
$$

In particular, it means that the [bias](https://en.wikipedia.org/wiki/Bias_of_an_estimator) of the maximum likelihood estimator is equal to zero up to the order 1/√n .

### Second-order efficiency after correction for bias

However, when we consider the higher-order terms in the [expansion](https://en.wikipedia.org/wiki/Edgeworth_expansion) of the distribution of this estimator, it turns out that *θ*<sub>mle</sub> has bias of order 1⁄n. This bias is equal to (componentwise)

$$
b_{h}\;\equiv \;\operatorname {\mathbb {E} } {\biggl [}\;\left({\widehat {\theta }}_{\mathrm {mle} }-\theta _{0}\right)_{h}\;{\biggr ]}\;=\;{\frac {1}{\,n\,}}\,\sum _{i,j,k=1}^{m}\;{\mathcal {I}}^{hi}\;{\mathcal {I}}^{jk}\left({\frac {1}{\,2\,}}\,K_{ijk}\;+\;J_{j,ik}\right)
$$

where ${\mathcal {I}}^{jk}$ (with superscripts) denotes the (*j,k*)-th component of the *inverse* Fisher information matrix ${\mathcal {I}}^{-1}$, and

$$
{\frac {1}{\,2\,}}\,K_{ijk}\;+\;J_{j,ik}\;=\;\operatorname {\mathbb {E} } \,{\biggl [}\;{\frac {1}{2}}{\frac {\partial ^{3}\ln f_{\theta _{0}}(X_{t})}{\partial \theta _{i}\;\partial \theta _{j}\;\partial \theta _{k}}}+{\frac {\;\partial \ln f_{\theta _{0}}(X_{t})\;}{\partial \theta _{j}}}\,{\frac {\;\partial ^{2}\ln f_{\theta _{0}}(X_{t})\;}{\partial \theta _{i}\,\partial \theta _{k}}}\;{\biggr ]}~.
$$

Using these formulae it is possible to estimate the second-order bias of the maximum likelihood estimator, and *correct* for that bias by subtracting it: 

$$
{\widehat {\theta \,}}_{\text{mle}}^{*}={\widehat {\theta \,}}_{\text{mle}}-{\widehat {b\,}}~.
$$

 This estimator is unbiased up to the terms of order 1/ n , and is called the **bias-corrected maximum likelihood estimator**.

This bias-corrected estimator is *second-order efficient* (at least within the curved exponential family), meaning that it has minimal mean squared error among all second-order bias-corrected estimators, up to the terms of the order 1/ n<sup>2</sup>  . It is possible to continue this process, that is to derive the third-order bias-correction term, and so on. However, the maximum likelihood estimator is *not* third-order efficient.

### Relation to Bayesian inference

A maximum likelihood estimator coincides with the [most probable](https://en.wikipedia.org/wiki/Maximum_a_posteriori) [Bayesian estimator](https://en.wikipedia.org/wiki/Bayesian_estimator) given a [uniform](https://en.wikipedia.org/wiki/Uniform_distribution_(continuous)) [prior distribution](https://en.wikipedia.org/wiki/Prior_probability) on the [parameters](https://en.wikipedia.org/wiki/Parameter_space). Indeed, the [maximum a posteriori estimate](https://en.wikipedia.org/wiki/Maximum_a_posteriori_estimate) is the parameter θ that maximizes the probability of θ given the data, given by Bayes' theorem:

$$
\operatorname {\mathbb {P} } (\theta \mid x_{1},x_{2},\ldots ,x_{n})={\frac {f(x_{1},x_{2},\ldots ,x_{n}\mid \theta )\operatorname {\mathbb {P} } (\theta )}{\operatorname {\mathbb {P} } (x_{1},x_{2},\ldots ,x_{n})}}
$$

where $\operatorname {\mathbb {P} } (\theta )$ is the prior distribution for the parameter θ and where $\operatorname {\mathbb {P} } (x_{1},x_{2},\ldots ,x_{n})$ is the probability of the data averaged over all parameters. Since the denominator is independent of θ, the Bayesian estimator is obtained by maximizing $f(x_{1},x_{2},\ldots ,x_{n}\mid \theta )\operatorname {\mathbb {P} } (\theta )$ with respect to θ. If we further assume that the prior $\operatorname {\mathbb {P} } (\theta )$ is a uniform distribution, the Bayesian estimator is obtained by maximizing the likelihood function $f(x_{1},x_{2},\ldots ,x_{n}\mid \theta )$. Thus the Bayesian estimator coincides with the maximum likelihood estimator for a uniform prior distribution $\operatorname {\mathbb {P} } (\theta )$.

#### Application of maximum-likelihood estimation in Bayes decision theory

In many practical applications in [machine learning](https://en.wikipedia.org/wiki/Machine_learning), maximum-likelihood estimation is used as the model for parameter estimation.

The Bayesian Decision theory is about designing a classifier that minimizes total expected risk, especially, when the costs (the loss function) associated with different decisions are equal, the classifier is minimizing the error over the whole distribution.

Thus, the Bayes Decision Rule is stated as

"decide $\;w_{1}\;$ if $~\operatorname {\mathbb {P} } (w_{1}|x)\;>\;\operatorname {\mathbb {P} } (w_{2}|x)~;~$ otherwise decide $\;w_{2}\;$"

where $\;w_{1}\,,w_{2}\;$ are predictions of different classes. From a perspective of minimizing error, it can also be stated as 

$$
w={\underset {w}{\operatorname {arg\;max} }}\;\int _{-\infty }^{\infty }\operatorname {\mathbb {P} } ({\text{ error}}\mid x)\operatorname {\mathbb {P} } (x)\,\operatorname {d} x~
$$

 where 

$$
\operatorname {\mathbb {P} } ({\text{ error}}\mid x)=\operatorname {\mathbb {P} } (w_{1}\mid x)~
$$

 if we decide $\;w_{2}\;$ and $\;\operatorname {\mathbb {P} } ({\text{ error}}\mid x)=\operatorname {\mathbb {P} } (w_{2}\mid x)\;$ if we decide $\;w_{1}\;.$

By applying [[Bayes Theorem|Bayes' theorem]] 

$$
\operatorname {\mathbb {P} } (w_{i}\mid x)={\frac {\operatorname {\mathbb {P} } (x\mid w_{i})\operatorname {\mathbb {P} } (w_{i})}{\operatorname {\mathbb {P} } (x)}},
$$

 and if we further assume the zero-or-one loss function, which is a same loss for all errors, the Bayes Decision rule can be reformulated as: 

$$
h_{\text{Bayes}}={\underset {w}{\operatorname {arg\;max} }}\,{\bigl [}\,\operatorname {\mathbb {P} } (x\mid w)\,\operatorname {\mathbb {P} } (w)\,{\bigr ]}\;,
$$

 where $h_{\text{Bayes}}$ is the prediction and $\;\operatorname {\mathbb {P} } (w)\;$ is the [prior probability](https://en.wikipedia.org/wiki/Prior_probability).

### Relation to minimizing Kullback–Leibler divergence and cross entropy

Finding ${\hat {\theta }}$ that maximizes the likelihood is asymptotically equivalent to finding the ${\hat {\theta }}$ that defines a probability distribution ($Q_{\hat {\theta }}$) that has a minimal distance, in terms of [[Kullback-Leibler Divergence|Kullback–Leibler divergence]], to the real probability distribution from which our data were generated (i.e., generated by $P_{\theta _{0}}$). In an ideal world, P and Q are the same (and the only thing unknown is $\theta$ that defines P), but even if they are not and the model we use is misspecified, still the MLE will give us the "closest" distribution (within the restriction of a model Q that depends on ${\hat {\theta }}$) to the real distribution $P_{\theta _{0}}$.

<table class="wikitable mw-collapsible mw-collapsed" role="presentation">

<strong>Proof.</strong>

<p>For simplicity of notation, let's assume that P=Q. Let there be <em>n</em> [i.i.d](https://en.wikipedia.org/wiki/I.i.d) data samples $\mathbf {y} =(y_{1},y_{2},\ldots ,y_{n})$ from some probability $y\sim P_{\theta _{0}}$, that we try to estimate by finding ${\hat {\theta }}$ that will maximize the likelihood using $P_{\theta }$, then: 

$$
{\begin{aligned}{\hat {\theta }}&={\underset {\theta }{\operatorname {arg\,max} }}\,L_{P_{\theta }}(\mathbf {y} )={\underset {\theta }{\operatorname {arg\,max} }}\,P_{\theta }(\mathbf {y} )={\underset {\theta }{\operatorname {arg\,max} }}\,P(\mathbf {y} \mid \theta )\\&={\underset {\theta }{\operatorname {arg\,max} }}\,\prod _{i=1}^{n}P(y_{i}\mid \theta )={\underset {\theta }{\operatorname {arg\,max} }}\,\sum _{i=1}^{n}\log P(y_{i}\mid \theta )\\&={\underset {\theta }{\operatorname {arg\,max} }}\,\left(\sum _{i=1}^{n}\log P(y_{i}\mid \theta )-\sum _{i=1}^{n}\log P(y_{i}\mid \theta _{0})\right)={\underset {\theta }{\operatorname {arg\,max} }}\,\sum _{i=1}^{n}\left(\log P(y_{i}\mid \theta )-\log P(y_{i}\mid \theta _{0})\right)\\&={\underset {\theta }{\operatorname {arg\,max} }}\,\sum _{i=1}^{n}\log {\frac {P(y_{i}\mid \theta )}{P(y_{i}\mid \theta _{0})}}={\underset {\theta }{\operatorname {arg\,min} }}\,\sum _{i=1}^{n}\log {\frac {P(y_{i}\mid \theta _{0})}{P(y_{i}\mid \theta )}}={\underset {\theta }{\operatorname {arg\,min} }}\,{\frac {1}{n}}\sum _{i=1}^{n}\log {\frac {P(y_{i}\mid \theta _{0})}{P(y_{i}\mid \theta )}}\\&={\underset {\theta }{\operatorname {arg\,min} }}\,{\frac {1}{n}}\sum _{i=1}^{n}h_{\theta }(y_{i})\quad {\underset {n\to \infty }{\longrightarrow }}\quad {\underset {\theta }{\operatorname {arg\,min} }}\,E[h_{\theta }(y)]\\&={\underset {\theta }{\operatorname {arg\,min} }}\,\int P_{\theta _{0}}(y)h_{\theta }(y)dy={\underset {\theta }{\operatorname {arg\,min} }}\,\int P_{\theta _{0}}(y)\log {\frac {P(y\mid \theta _{0})}{P(y\mid \theta )}}dy\\&={\underset {\theta }{\operatorname {arg\,min} }}\,D_{\text{KL}}(P_{\theta _{0}}\parallel P_{\theta })\end{aligned}}
$$

</p>
<p>Where $h_{\theta }(x)=\log {\frac {P(x\mid \theta _{0})}{P(x\mid \theta )}}$. Using <em>h</em> helps see how we are using the [[Law of Large Numbers]] to move from the average of <em>h</em>(<em>x</em>) to the [expectancy](https://en.wikipedia.org/wiki/Expected_value) of it using the [law of the unconscious statistician](https://en.wikipedia.org/wiki/Law_of_the_unconscious_statistician). The first several transitions have to do with laws of [logarithm](https://en.wikipedia.org/wiki/Logarithm) and that finding ${\hat {\theta }}$ that maximizes some function will also be the one that maximizes some monotonic transformation of that function (i.e.: adding/multiplying by a constant).</p>
<p>Since [[Kullback-Leibler Divergence|cross entropy]] is just [[Entropy|Shannon's entropy]] plus KL divergence, and since the entropy of $P_{\theta _{0}}$ is constant, then the MLE is also asymptotically minimizing cross entropy.</p>

</table>

### Prediction bias

Maximum likelihood estimates of parameters can be substituted into expressions for the [[Probability Density Function]], [[Cumulative Distribution Function]], or [quantile function](https://en.wikipedia.org/wiki/Quantile_function), to generate predictions of probabilities or quantiles of out-of-sample events. This method for predicting probabilities is recommended in statistics text-books and actuarial textbooks, and is widely used in the scientific literature. However, maximum likelihood prediction fails to propagate the uncertainty around the maximum likelihood parameter estimates into the prediction. As a result, the predicted probabilities are not well [calibrated](https://en.wikipedia.org/wiki/Calibration_(statistics)#In_probability_prediction_and_forecasting "Calibration (statistics)"), and should not be expected to correspond to the frequencies of out-of-sample events. In particular, tail exceedance probabilities and tail exceedance quantiles are typically underestimated, sometimes dramatically. The underestimation is largest when there is little training data, many parameters being estimated, and for the far tail. For cases where this prediction bias is a problem, Bayesian predictions can provide a solution if the prior is chosen so as to reduce or eliminate the bias.

## Examples

### Discrete uniform distribution

Consider a case where *n* tickets numbered from 1 to *n* are placed in a box and one is selected at random (*see [uniform distribution](https://en.wikipedia.org/wiki/Uniform_distribution_(discrete))*); thus, the sample size is 1. If *n* is unknown, then the maximum likelihood estimator ${\widehat {n}}$ of *n* is the number *m* on the drawn ticket. (The likelihood is 0 for *n* \< *m*, 1⁄*n* for *n* ≥ *m*, and this is greatest when *n* = *m*. Note that the maximum likelihood estimate of *n* occurs at the lower extreme of possible values {*m*, *m* + 1, ...}, rather than somewhere in the "middle" of the range of possible values, which would result in less bias.) The [expected value](https://en.wikipedia.org/wiki/Expected_value) of the number *m* on the drawn ticket, and therefore the expected value of ${\widehat {n}}$, is (*n* + 1)/2. As a result, with a sample size of 1, the maximum likelihood estimator for *n* will systematically underestimate *n* by (*n* − 1)/2.

### Discrete distribution, finite parameter space

Suppose one wishes to determine just how biased an [unfair coin](https://en.wikipedia.org/wiki/Unfair_coin) is. Call the probability of tossing a '[head](https://en.wikipedia.org/wiki/Obverse_and_reverse)' *p*. The goal then becomes to determine *p*.

Suppose the coin is tossed 80 times: i.e. the sample might be something like *x*<sub>1</sub> = H, *x*<sub>2</sub> = T, ..., *x*<sub>80</sub> = T, and the count of the number of [heads](https://en.wikipedia.org/wiki/Obverse_and_reverse) "H" is observed.

The probability of tossing [tails](https://en.wikipedia.org/wiki/Obverse_and_reverse) is 1 − *p* (so here *p* is *θ* above). Suppose the outcome is 49 heads and 31 [tails](https://en.wikipedia.org/wiki/Obverse_and_reverse), and suppose the coin was taken from a box containing three coins: one which gives heads with probability *p* = 1⁄3, one which gives heads with probability *p* = 1⁄2 and another which gives heads with probability *p* = 2⁄3. The coins have lost their labels, so which one it was is unknown. Using maximum likelihood estimation, the coin that has the largest likelihood can be found, given the data that were observed. By using the [probability mass function](https://en.wikipedia.org/wiki/Probability_mass_function) of the [binomial distribution](https://en.wikipedia.org/wiki/Binomial_distribution) with sample size equal to 80, number successes equal to 49 but for different values of *p* (the "probability of success"), the likelihood function (defined below) takes one of three values:

$$
{\begin{aligned}\operatorname {\mathbb {P} } {\bigl [}\;\mathrm {H} =49\mid p={\tfrac {1}{3}}\;{\bigr ]}&={\binom {80}{49}}({\tfrac {1}{3}})^{49}(1-{\tfrac {1}{3}})^{31}\approx 0.000,\\[6pt]\operatorname {\mathbb {P} } {\bigl [}\;\mathrm {H} =49\mid p={\tfrac {1}{2}}\;{\bigr ]}&={\binom {80}{49}}({\tfrac {1}{2}})^{49}(1-{\tfrac {1}{2}})^{31}\approx 0.012,\\[6pt]\operatorname {\mathbb {P} } {\bigl [}\;\mathrm {H} =49\mid p={\tfrac {2}{3}}\;{\bigr ]}&={\binom {80}{49}}({\tfrac {2}{3}})^{49}(1-{\tfrac {2}{3}})^{31}\approx 0.054~.\end{aligned}}
$$

The likelihood is maximized when p = 2⁄3, and so this is the *maximum likelihood estimate* for p.

### Discrete distribution, continuous parameter space

Now suppose that there was only one coin but its p could have been any value  0 ≤ p ≤ 1 . The likelihood function to be maximised is 

$$
L(p)=f_{D}(\mathrm {H} =49\mid p)={\binom {80}{49}}p^{49}(1-p)^{31}~,
$$

and the maximisation is over all possible values 0 ≤ p ≤ 1 .

![[media/3cbcc1e8e5a104d097c2f6f7c959904d0120980f.png]]
Likelihood function for proportion value of a binomial process (n = 10)

One way to maximize this function is by [differentiating](https://en.wikipedia.org/wiki/Derivative) with respect to p and setting to zero:

$$
{\begin{aligned}0&={\frac {\partial }{\partial p}}\left({\binom {80}{49}}p^{49}(1-p)^{31}\right)~,\\[8pt]0&=49p^{48}(1-p)^{31}-31p^{49}(1-p)^{30}\\[8pt]&=p^{48}(1-p)^{30}\left[49(1-p)-31p\right]\\[8pt]&=p^{48}(1-p)^{30}\left[49-80p\right]~.\end{aligned}}
$$

This is a product of three terms. The first term is 0 when p = 0. The second is 0 when p = 1. The third is zero when p = 49⁄80. The solution that maximizes the likelihood is clearly p = 49⁄80 (since p = 0 and p = 1 result in a likelihood of 0). Thus the *maximum likelihood estimator* for p is 49⁄80.

This result is easily generalized by substituting a letter such as s in the place of 49 to represent the observed number of 'successes' of our [Bernoulli trials](https://en.wikipedia.org/wiki/Bernoulli_trial), and a letter such as n in the place of 80 to represent the number of Bernoulli trials. Exactly the same calculation yields s⁄n which is the maximum likelihood estimator for any sequence of n Bernoulli trials resulting in s 'successes'.

### Continuous distribution, continuous parameter space

For the [normal distribution](https://en.wikipedia.org/wiki/Normal_distribution) ${\mathcal {N}}(\mu ,\sigma ^{2})$ which has [[Probability Density Function]]

$$
f(x\mid \mu ,\sigma ^{2})={\frac {1}{{\sqrt {2\pi \sigma ^{2}}}\ }}\exp \left(-{\frac {(x-\mu )^{2}}{2\sigma ^{2}}}\right),
$$

the corresponding [[Probability Density Function]] for a sample of n [independent identically distributed](https://en.wikipedia.org/wiki/Independent_identically_distributed) normal random variables (the likelihood) is

$$
f(x_{1},\ldots ,x_{n}\mid \mu ,\sigma ^{2})=\prod _{i=1}^{n}f(x_{i}\mid \mu ,\sigma ^{2})=\left({\frac {1}{2\pi \sigma ^{2}}}\right)^{n/2}\exp \left(-{\frac {\sum _{i=1}^{n}(x_{i}-\mu )^{2}}{2\sigma ^{2}}}\right).
$$

This family of distributions has two parameters: *θ* = (*μ*, *σ*); so we maximize the likelihood, ${\mathcal {L}}(\mu ,\sigma ^{2})=f(x_{1},\ldots ,x_{n}\mid \mu ,\sigma ^{2})$, over both parameters simultaneously, or if possible, individually.

Since the [logarithm](https://en.wikipedia.org/wiki/Natural_logarithm) function itself is a [continuous](https://en.wikipedia.org/wiki/Continuous_function) [strictly increasing](https://en.wikipedia.org/wiki/Strictly_increasing) function over the [range](https://en.wikipedia.org/wiki/Range_(statistics) "Range (statistics)") of the likelihood, the values which maximize the likelihood will also maximize its logarithm (the log-likelihood itself is not necessarily strictly increasing). The log-likelihood can be written as follows:

$$
\log \left({\mathcal {L}}(\mu ,\sigma ^{2})\right)=-{\frac {n}{2}}\log(2\pi \sigma ^{2})-{\frac {1}{2\sigma ^{2}}}\sum _{i=1}^{n}\left(x_{i}-\mu \right)^{2}
$$

(Note: the log-likelihood is closely related to [information entropy](https://en.wikipedia.org/wiki/Information_entropy) and [[Fisher Information]].)

We now compute the derivatives of this log-likelihood as follows.

$$
{\begin{aligned}0&={\frac {\partial }{\partial \mu }}\log \left({\mathcal {L}}(\mu ,\sigma ^{2})\right)=0-{\frac {-2n({\bar {x}}-\mu )}{2\sigma ^{2}}}.\end{aligned}}
$$

 where ${\bar {x}}$ is the [sample mean](https://en.wikipedia.org/wiki/Sample_mean). This is solved by

$$
{\widehat {\mu }}={\bar {x}}=\sum _{i=1}^{n}{\frac {\,x_{i}\,}{n}}.
$$

This is indeed the maximum of the function, since it is the only turning point in μ and the second derivative is strictly less than zero. Its [expected value](https://en.wikipedia.org/wiki/Expected_value) is equal to the parameter μ of the given distribution,

$$
\operatorname {\mathbb {E} } {\bigl [}\;{\widehat {\mu }}\;{\bigr ]}=\mu ,\,
$$

which means that the maximum likelihood estimator ${\widehat {\mu }}$ is unbiased.

Similarly we differentiate the log-likelihood with respect to σ and equate to zero:

$$
{\begin{aligned}0&={\frac {\partial }{\partial \sigma }}\log {\Bigl (}{\mathcal {L}}(\mu ,\sigma ^{2}){\Bigr )}=-{\frac {\,n\,}{\sigma }}+{\frac {1}{\sigma ^{3}}}\sum _{i=1}^{n}(\,x_{i}-\mu \,)^{2}.\end{aligned}}
$$

which is solved by

$$
{\widehat {\sigma }}^{2}={\frac {1}{n}}\sum _{i=1}^{n}(x_{i}-\mu )^{2}.
$$

Inserting the estimate $\mu ={\widehat {\mu }}$ we obtain

$$
{\widehat {\sigma }}^{2}={\frac {1}{n}}\sum _{i=1}^{n}(x_{i}-{\bar {x}})^{2}={\frac {1}{n}}\sum _{i=1}^{n}x_{i}^{2}-{\frac {1}{n^{2}}}\sum _{i=1}^{n}\sum _{j=1}^{n}x_{i}x_{j}.
$$

To calculate its expected value, it is convenient to rewrite the expression in terms of zero-mean random variables ([statistical error](https://en.wikipedia.org/wiki/Statistical_error)) $\delta _{i}\equiv \mu -x_{i}$. Expressing the estimate in these variables yields

$$
{\widehat {\sigma }}^{2}={\frac {1}{n}}\sum _{i=1}^{n}(\mu -\delta _{i})^{2}-{\frac {1}{n^{2}}}\sum _{i=1}^{n}\sum _{j=1}^{n}(\mu -\delta _{i})(\mu -\delta _{j}).
$$

Simplifying the expression above, utilizing the facts that $\operatorname {\mathbb {E} } {\bigl [}\;\delta _{i}\;{\bigr ]}=0$ and $\operatorname {E} {\bigl [}\;\delta _{i}^{2}\;{\bigr ]}=\sigma ^{2}$, allows us to obtain

$$
\operatorname {\mathbb {E} } {\bigl [}\;{\widehat {\sigma }}^{2}\;{\bigr ]}={\frac {\,n-1\,}{n}}\sigma ^{2}.
$$

This means that the estimator ${\widehat {\sigma }}^{2}$ is biased for $\sigma ^{2}$. It can also be shown that ${\widehat {\sigma }}$ is biased for $\sigma$, but that both ${\widehat {\sigma }}^{2}$ and ${\widehat {\sigma }}$ are consistent.

Formally we say that the *maximum likelihood estimator* for $\theta =(\mu ,\sigma ^{2})$ is

$$
{\widehat {\theta \,}}=\left({\widehat {\mu }},{\widehat {\sigma }}^{2}\right).
$$

In this case the MLEs could be obtained individually. In general this may not be the case, and the MLEs would have to be obtained simultaneously.

The normal log-likelihood at its maximum takes a particularly simple form:

$$
\log {\Bigl (}{\mathcal {L}}({\widehat {\mu }},{\widehat {\sigma }}){\Bigr )}={\frac {\,-n\;\;}{2}}{\bigl (}\,\log(2\pi {\widehat {\sigma }}^{2})+1\,{\bigr )}
$$

This maximum log-likelihood can be shown to be the same for more general [least squares](https://en.wikipedia.org/wiki/Least_squares), even for [non-linear least squares](https://en.wikipedia.org/wiki/Non-linear_least_squares). This is often used in determining likelihood-based approximate [confidence intervals](https://en.wikipedia.org/wiki/Confidence_interval) and [confidence regions](https://en.wikipedia.org/wiki/Confidence_region), which are generally more accurate than those using the asymptotic normality discussed above.

## Non-independent variables

It may be the case that variables are correlated, or more generally, not independent. Two random variables $y_{1}$ and $y_{2}$ are independent only if their joint probability density function is the product of the individual probability density functions, i.e.

$$
f(y_{1},y_{2})=f(y_{1})f(y_{2})\,
$$

Suppose one constructs an order-*n* Gaussian vector out of random variables $(y_{1},\ldots ,y_{n})$, where each variable has means given by $(\mu _{1},\ldots ,\mu _{n})$. Furthermore, let the [covariance matrix](https://en.wikipedia.org/wiki/Covariance_matrix) be denoted by ${\mathit {\Sigma }}$. The joint probability density function of these *n* random variables then follows a [[Multivariate Normal Distribution]] given by:

$$
f(y_{1},\ldots ,y_{n})={\frac {1}{(2\pi )^{n/2}{\sqrt {\det({\mathit {\Sigma }})}}}}\exp \left(-{\frac {1}{2}}\left[y_{1}-\mu _{1},\ldots ,y_{n}-\mu _{n}\right]{\mathit {\Sigma }}^{-1}\left[y_{1}-\mu _{1},\ldots ,y_{n}-\mu _{n}\right]^{\mathrm {T} }\right)
$$

In the [bivariate](https://en.wikipedia.org/wiki/Bivariate_analysis) case, the joint probability density function is given by:

$$
f(y_{1},y_{2})={\frac {1}{2\pi \sigma _{1}\sigma _{2}{\sqrt {1-\rho ^{2}}}}}\exp \left[-{\frac {1}{2(1-\rho ^{2})}}\left({\frac {(y_{1}-\mu _{1})^{2}}{\sigma _{1}^{2}}}-{\frac {2\rho (y_{1}-\mu _{1})(y_{2}-\mu _{2})}{\sigma _{1}\sigma _{2}}}+{\frac {(y_{2}-\mu _{2})^{2}}{\sigma _{2}^{2}}}\right)\right]
$$

In this and other cases where a joint density function exists, the likelihood function is defined as above, in the section "[principles](https://en.wikipedia.org/wiki/Maximum_likelihood#Principles)," using this density.

### Example

$X_{1},\ X_{2},\ldots ,\ X_{m}$ are counts in cells / boxes 1 up to m; each box has a different probability (think of the boxes being bigger or smaller) and we fix the number of balls that fall to be $n$:$x_{1}+x_{2}+\cdots +x_{m}=n$. The probability of each box is $p_{i}$, with a constraint: $p_{1}+p_{2}+\cdots +p_{m}=1$. This is a case in which the $X_{i}$ *s* are not independent, the joint probability of a vector $x_{1},\ x_{2},\ldots ,x_{m}$ is called the multinomial and has the form:

$$
f(x_{1},x_{2},\ldots ,x_{m}\mid p_{1},p_{2},\ldots ,p_{m})={\frac {n!}{\prod x_{i}!}}\prod p_{i}^{x_{i}}={\binom {n}{x_{1},x_{2},\ldots ,x_{m}}}p_{1}^{x_{1}}p_{2}^{x_{2}}\cdots p_{m}^{x_{m}}
$$

Each box taken separately against all the other boxes is a binomial and this is an extension thereof.

The log-likelihood of this is:

$$
\ell (p_{1},p_{2},\ldots ,p_{m})=\log n!-\sum _{i=1}^{m}\log x_{i}!+\sum _{i=1}^{m}x_{i}\log p_{i}
$$

The constraint has to be taken into account and use the Lagrange multipliers:

$$
L(p_{1},p_{2},\ldots ,p_{m},\lambda )=\ell (p_{1},p_{2},\ldots ,p_{m})+\lambda \left(1-\sum _{i=1}^{m}p_{i}\right)
$$

By posing all the derivatives to be 0, the most natural estimate is derived

$$
{\hat {p}}_{i}={\frac {x_{i}}{n}}
$$

Maximizing log likelihood, with and without constraints, can be an unsolvable problem in closed form, then we have to use iterative procedures.

## Iterative procedures

Except for special cases, the likelihood equations 

$$
{\frac {\partial \ell (\theta ;\mathbf {y} )}{\partial \theta }}=0
$$

cannot be solved explicitly for an estimator ${\widehat {\theta }}={\widehat {\theta }}(\mathbf {y} )$. Instead, they need to be solved [iteratively](https://en.wikipedia.org/wiki/Iterative_method): starting from an initial guess of $\theta$ (say ${\widehat {\theta }}_{1}$), one seeks to obtain a convergent sequence $\left\{{\widehat {\theta }}_{r}\right\}$. Many methods for this kind of [optimization problem](https://en.wikipedia.org/wiki/Optimization_problem) are available, but the most commonly used ones are algorithms based on an updating formula of the form 

$$
{\widehat {\theta }}_{r+1}={\widehat {\theta }}_{r}+\eta _{r}\mathbf {d} _{r}\left({\widehat {\theta }}\right)
$$

where the vector $\mathbf {d} _{r}\left({\widehat {\theta }}\right)$ indicates the [descent direction](https://en.wikipedia.org/wiki/Descent_direction) of the `r`th "step," and the scalar $\eta _{r}$ captures the "step length," also known as the [learning rate](https://en.wikipedia.org/wiki/Learning_rate).

### [[Gradient Descent]] method

(Note: here it is a maximization problem, so the sign before gradient is flipped)

$$
\eta _{r}\in \mathbb {R} ^{+}
$$

 that is small enough for convergence and $\mathbf {d} _{r}\left({\widehat {\theta }}\right)=\nabla \ell \left({\widehat {\theta }}_{r};\mathbf {y} \right)$

Gradient descent method requires to calculate the gradient at the *r*-th iteration, but no need to calculate the inverse of second-order derivative, i.e., the Hessian matrix. Therefore, it is computationally faster than Newton[–](https://en.wikipedia.org/wiki/Newton%27s_method)Raphson method.

### [Newton–Raphson method](https://en.wikipedia.org/wiki/Newton%27s_method)

$$
\eta _{r}=1
$$

 and $\mathbf {d} _{r}\left({\widehat {\theta }}\right)=-\mathbf {H} _{r}^{-1}\left({\widehat {\theta }}\right)\mathbf {s} _{r}\left({\widehat {\theta }}\right)$

where $\mathbf {s} _{r}({\widehat {\theta }})$ is the [score](https://en.wikipedia.org/wiki/Score_(statistics)) and $\mathbf {H} _{r}^{-1}\left({\widehat {\theta }}\right)$ is the [inverse](https://en.wikipedia.org/wiki/Invertible_matrix) of the [[Hessian Matrix]] of the log-likelihood function, both evaluated the `r`th iteration. But because the calculation of the Hessian matrix is [computationally costly](https://en.wikipedia.org/wiki/Computational_complexity), numerous alternatives have been proposed. The popular [Berndt–Hall–Hall–Hausman algorithm](https://en.wikipedia.org/wiki/Berndt%E2%80%93Hall%E2%80%93Hall%E2%80%93Hausman_algorithm) approximates the Hessian with the [outer product](https://en.wikipedia.org/wiki/Outer_product) of the expected gradient, such that

$$
\mathbf {d} _{r}\left({\widehat {\theta }}\right)=-\left[{\frac {1}{n}}\sum _{t=1}^{n}{\frac {\partial \ell (\theta ;\mathbf {y} )}{\partial \theta }}\left({\frac {\partial \ell (\theta ;\mathbf {y} )}{\partial \theta }}\right)^{\mathsf {T}}\right]^{-1}\mathbf {s} _{r}\left({\widehat {\theta }}\right)
$$

### [Quasi-Newton methods](https://en.wikipedia.org/wiki/Quasi-Newton_method)

Other quasi-Newton methods use more elaborate secant updates to give approximation of Hessian matrix.

#### [Davidon–Fletcher–Powell formula](https://en.wikipedia.org/wiki/Davidon%E2%80%93Fletcher%E2%80%93Powell_formula)

DFP formula finds a solution that is symmetric, positive-definite and closest to the current approximate value of second-order derivative: 

$$
\mathbf {H} _{k+1}=\left(I-\gamma _{k}y_{k}s_{k}^{\mathsf {T}}\right)\mathbf {H} _{k}\left(I-\gamma _{k}s_{k}y_{k}^{\mathsf {T}}\right)+\gamma _{k}y_{k}y_{k}^{\mathsf {T}},
$$

where

$$
y_{k}=\nabla \ell (x_{k}+s_{k})-\nabla \ell (x_{k}),
$$

$$
\gamma _{k}={\frac {1}{y_{k}^{\mathsf {T}}s_{k}}},
$$

$$
s_{k}=x_{k+1}-x_{k}.
$$

#### [Broyden–Fletcher–Goldfarb–Shanno algorithm](https://en.wikipedia.org/wiki/Broyden%E2%80%93Fletcher%E2%80%93Goldfarb%E2%80%93Shanno_algorithm)

BFGS also gives a solution that is symmetric and positive-definite:

$$
B_{k+1}=B_{k}+{\frac {y_{k}y_{k}^{\mathsf {T}}}{y_{k}^{\mathsf {T}}s_{k}}}-{\frac {B_{k}s_{k}s_{k}^{\mathsf {T}}B_{k}^{\mathsf {T}}}{s_{k}^{\mathsf {T}}B_{k}s_{k}}}\ ,
$$

where

$$
y_{k}=\nabla \ell (x_{k}+s_{k})-\nabla \ell (x_{k}),
$$

$$
s_{k}=x_{k+1}-x_{k}.
$$

BFGS method is not guaranteed to converge unless the function has a quadratic [Taylor expansion](https://en.wikipedia.org/wiki/Taylor_expansion) near an optimum. However, BFGS can have acceptable performance even for non-smooth optimization instances

#### [Fisher's scoring](https://en.wikipedia.org/wiki/Scoring_algorithm)

Another popular method is to replace the Hessian with the [Fisher information matrix](https://en.wikipedia.org/wiki/Fisher_information_matrix), ${\mathcal {I}}(\theta )=\operatorname {\mathbb {E} } \left[\mathbf {H} _{r}\left({\widehat {\theta }}\right)\right]$, giving us the Fisher scoring algorithm. This procedure is standard in the estimation of many methods, such as [generalized linear models](https://en.wikipedia.org/wiki/Generalized_linear_models).

Although popular, quasi-Newton methods may converge to a [stationary point](https://en.wikipedia.org/wiki/Stationary_point) that is not necessarily a local or global maximum, but rather a local minimum or a [saddle point](https://en.wikipedia.org/wiki/Saddle_point). Therefore, it is important to assess the validity of the obtained solution to the likelihood equations, by verifying that the Hessian, evaluated at the solution, is both [negative definite](https://en.wikipedia.org/wiki/Negative_definite) and [well-conditioned](https://en.wikipedia.org/wiki/Well-conditioned).

## History

![[media/d3542fb5bb3d974083751f93e6073b1fe786d4d9.jpg]]
[Ronald Fisher](https://en.wikipedia.org/wiki/Ronald_Fisher) in 1913

Early users of maximum likelihood include [Carl Friedrich Gauss](https://en.wikipedia.org/wiki/Carl_Friedrich_Gauss), [Pierre-Simon Laplace](https://en.wikipedia.org/wiki/Pierre-Simon_Laplace), [Thorvald N. Thiele](https://en.wikipedia.org/wiki/Thorvald_N._Thiele), and [Francis Ysidro Edgeworth](https://en.wikipedia.org/wiki/Francis_Ysidro_Edgeworth). It was [Ronald Fisher](https://en.wikipedia.org/wiki/Ronald_Fisher) however, between 1912 and 1922, who single-handedly created the modern version of the method.

Maximum-likelihood estimation finally transcended [heuristic](https://en.wikipedia.org/wiki/Heuristic) justification in a proof published by [Samuel S. Wilks](https://en.wikipedia.org/wiki/Samuel_S._Wilks) in 1938, now called [Wilks' theorem](https://en.wikipedia.org/wiki/Wilks%27_theorem). The theorem shows that the error in the logarithm of likelihood values for estimates from multiple independent observations is asymptotically [*χ*<sup> 2</sup>-distributed](https://en.wikipedia.org/wiki/Chi-squared_distribution), which enables convenient determination of a [confidence region](https://en.wikipedia.org/wiki/Confidence_region) around any estimate of the parameters. The only difficult part of Wilks' proof depends on the expected value of the [[Fisher Information]] matrix, which is provided by a theorem proven by Fisher. Wilks continued to improve on the generality of the theorem throughout his life, with his most general proof published in 1962.

Reviews of the development of maximum likelihood estimation have been provided by a number of authors.

## See also

- ![[media/1a9c6ad1ccebbc090fc7cd1c94d2142489246997.png]][Mathematics portal](https://en.wikipedia.org/wiki/Portal:Mathematics)

### Related concepts

- [Akaike information criterion](https://en.wikipedia.org/wiki/Akaike_information_criterion): a criterion to compare statistical models, based on MLE
- [Extremum estimator](https://en.wikipedia.org/wiki/Extremum_estimator): a more general class of estimators to which MLE belongs
- [[Fisher Information]]: information matrix, its relationship to covariance matrix of ML estimates
- [Mean squared error](https://en.wikipedia.org/wiki/Mean_squared_error): a measure of how 'good' an estimator of a distributional parameter is (be it the maximum likelihood estimator or some other estimator)
- [RANSAC](https://en.wikipedia.org/wiki/RANSAC): a method to estimate parameters of a mathematical model given data that contains [outliers](https://en.wikipedia.org/wiki/Outliers)
- [Rao–Blackwell theorem](https://en.wikipedia.org/wiki/Rao%E2%80%93Blackwell_theorem): yields a process for finding the best possible unbiased estimator (in the sense of having minimal [mean squared error](https://en.wikipedia.org/wiki/Mean_squared_error)); the MLE is often a good starting place for the process
- [Wilks' theorem](https://en.wikipedia.org/wiki/Likelihood-ratio_test#Asymptotic_distribution:_Wilks'_theorem): provides a means of estimating the size and shape of the region of roughly equally-probable estimates for the population's parameter values, using the information from a single sample, using a [chi-squared distribution](https://en.wikipedia.org/wiki/Chi-squared_distribution)

### Other estimation methods

- [Generalized method of moments](https://en.wikipedia.org/wiki/Generalized_method_of_moments): methods related to the likelihood equation in maximum likelihood estimation
- [M-estimator](https://en.wikipedia.org/wiki/M-estimator): an approach used in robust statistics
- [Maximum a posteriori](https://en.wikipedia.org/wiki/Maximum_a_posteriori) (MAP) estimator: for a contrast in the way to calculate estimators when prior knowledge is postulated
- [Maximum spacing estimation](https://en.wikipedia.org/wiki/Maximum_spacing_estimation): a related method that is more robust in many situations
- [Maximum entropy estimation](https://en.wikipedia.org/wiki/Principle_of_maximum_entropy)
- [Method of moments (statistics)](https://en.wikipedia.org/wiki/Method_of_moments_(statistics) "Method of moments (statistics)"): another popular method for finding parameters of distributions
- [Method of support](https://en.wikipedia.org/wiki/Method_of_support), a variation of the maximum likelihood technique
- [Minimum-distance estimation](https://en.wikipedia.org/wiki/Minimum-distance_estimation)
- [Partial likelihood methods for panel data](https://en.wikipedia.org/wiki/Partial_likelihood_methods_for_panel_data)
- [Quasi-maximum likelihood](https://en.wikipedia.org/wiki/Quasi-maximum_likelihood) estimator: an MLE estimator that is misspecified, but still consistent
- [Restricted maximum likelihood](https://en.wikipedia.org/wiki/Restricted_maximum_likelihood): a variation using a likelihood function calculated from a transformed set of data

## References

1.  Rossi, Richard J. (2018). *Mathematical Statistics: An Introduction to Likelihood Based Inference*. New York: John Wiley & Sons. p. 227. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-118-77104-4](https://en.wikipedia.org/wiki/Special:BookSources/978-1-118-77104-4).
2.  [Hendry, David F.](https://en.wikipedia.org/wiki/David_Forbes_Hendry); Nielsen, Bent (2007). *Econometric Modeling: A Likelihood Approach*. Princeton: Princeton University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-691-13128-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-691-13128-3).
3.  Chambers, Raymond L.; Steel, David G.; Wang, Suojin; Welsh, Alan (2012). *Maximum Likelihood Estimation for Sample Surveys*. Boca Raton: CRC Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-58488-632-7](https://en.wikipedia.org/wiki/Special:BookSources/978-1-58488-632-7).
4.  [Ward, Michael Don](https://en.wikipedia.org/wiki/Michael_D._Ward); Ahlquist, John S. (2018). *Maximum Likelihood for Social Science: Strategies for Analysis*. New York: Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-107-18582-1](https://en.wikipedia.org/wiki/Special:BookSources/978-1-107-18582-1).
5.  Press, W.H.; Flannery, B.P.; Teukolsky, S.A.; Vetterling, W.T. (1992). ["Least Squares as a Maximum Likelihood Estimator"](https://books.google.com/books?id=gn_4mpdN9WkC&pg=PA651). *Numerical Recipes in FORTRAN: The Art of Scientific Computing* (2nd ed.). Cambridge: Cambridge University Press. pp. 651–655. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-43064-X](https://en.wikipedia.org/wiki/Special:BookSources/0-521-43064-X).
6.  Myung, I.J. (2003). "Tutorial on maximum likelihood Estimation". *[Journal of Mathematical Psychology](https://en.wikipedia.org/wiki/Journal_of_Mathematical_Psychology)*. **47** (1): 90–100. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/S0022-2496(02)00028-7](https://doi.org/10.1016%2FS0022-2496%2802%2900028-7).
7.  Gourieroux, Christian; Monfort, Alain (1995). [Statistics and Econometrics Models](https://archive.org/details/statisticseconom00gour_434). Cambridge University Press. p. [161](https://archive.org/details/statisticseconom00gour_434/page/n172). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-40551-3](https://en.wikipedia.org/wiki/Special:BookSources/0-521-40551-3).
8.  [Kane, Edward J.](https://en.wikipedia.org/wiki/Edward_Kane) (1968). [Economic Statistics and Econometrics](https://archive.org/details/economicstatisti00kane). New York, NY: Harper & Row. p. [179](https://archive.org/details/economicstatisti00kane/page/n200).
9.  Small, Christoper G.; Wang, Jinfang (2003). ["Working with roots"](https://books.google.com/books?id=hMrwQVllY5AC&pg=PA74). *Numerical Methods for Nonlinear Estimating Equations*. Oxford University Press. pp. 74–124. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-19-850688-0](https://en.wikipedia.org/wiki/Special:BookSources/0-19-850688-0).
10. Kass, Robert E.; Vos, Paul W. (1997). [Geometrical Foundations of Asymptotic Inference](https://books.google.com/books?id=e43EAIfUPCwC&pg=PA14). New York, NY: John Wiley & Sons. p. 14. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-82668-5](https://en.wikipedia.org/wiki/Special:BookSources/0-471-82668-5).
11. Papadopoulos, Alecos (25 September 2013). ["Why we always put log() before the joint pdf when we use MLE (Maximum likelihood Estimation)?"](https://stats.stackexchange.com/q/70975). *[Stack Exchange](https://en.wikipedia.org/wiki/Stack_Exchange)*.
12. ^   Silvey, S. D. (1975). [Statistical Inference](https://books.google.com/books?id=qIKLejbVMf4C&pg=PA79). London, UK: Chapman and Hall. p. 79. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-412-13820-4](https://en.wikipedia.org/wiki/Special:BookSources/0-412-13820-4).
13. Olive, David (2004). ["Does the MLE maximize the likelihood?"](http://lagrange.math.siu.edu/Olive/simle.pdf) (PDF). *Southern Illinois University*.
14. Schwallie, Daniel P. (1985). "Positive definite maximum likelihood covariance estimators". *Economics Letters*. **17** (1–2): 115–117. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/0165-1765(85)90139-9](https://doi.org/10.1016%2F0165-1765%2885%2990139-9).
15. Magnus, Jan R. (2017). *Introduction to the Theory of Econometrics*. Amsterdam: VU University Press. pp. 64–65. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-90-8659-766-6](https://en.wikipedia.org/wiki/Special:BookSources/978-90-8659-766-6).
16. , p. 206)
17. By Theorem 2.5 in Newey, Whitney K.; [McFadden, Daniel](https://en.wikipedia.org/wiki/Daniel_McFadden) (1994). "Chapter 36: Large sample estimation and hypothesis testing". In Engle, Robert; McFadden, Dan (eds.). *Handbook of Econometrics, Vol.4*. Elsevier Science. pp. 2111–2245. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-444-88766-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-444-88766-5).
18. ^   By Theorem 3.3 in Newey, Whitney K.; [McFadden, Daniel](https://en.wikipedia.org/wiki/Daniel_McFadden) (1994). "Chapter 36: Large sample estimation and hypothesis testing". In Engle, Robert; McFadden, Dan (eds.). *Handbook of Econometrics, Vol.4*. Elsevier Science. pp. 2111–2245. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-444-88766-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-444-88766-5).
19. Zacks, Shelemyahu (1971). *The Theory of Statistical Inference*. New York: John Wiley & Sons. p. 223. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-98103-6](https://en.wikipedia.org/wiki/Special:BookSources/0-471-98103-6).
20. See formula 20 in [Cox, David R.](https://en.wikipedia.org/wiki/David_R._Cox); [Snell, E. Joyce](https://en.wikipedia.org/wiki/Joyce_Snell) (1968). "A general definition of residuals". *[Journal of the Royal Statistical Society, Series B](https://en.wikipedia.org/wiki/Journal_of_the_Royal_Statistical_Society,_Series_B)*. **30** (2): 248–275. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1111/j.2517-6161.1968.tb00724.x](https://doi.org/10.1111%2Fj.2517-6161.1968.tb00724.x). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2984505](https://www.jstor.org/stable/2984505).
21. Kano, Yutaka (1996). ["Third-order efficiency implies fourth-order efficiency"](https://doi.org/10.14490%2Fjjss1995.26.101). *Journal of the Japan Statistical Society*. **26**: 101–117. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.14490/jjss1995.26.101](https://doi.org/10.14490%2Fjjss1995.26.101).
22. Christensen, Henrikt I. ["Pattern Recognition"](https://www.cc.gatech.edu/~hic/CS7616/pdf/lecture2.pdf) (PDF) (lecture). Bayesian Decision Theory - CS 7616. Georgia Tech.
23. cmplx96 ([https://stats.stackexchange.com/users/177679/cmplx96](https://stats.stackexchange.com/users/177679/cmplx96)), Kullback–Leibler divergence, URL (version: 2017-11-18): [https://stats.stackexchange.com/q/314472](https://stats.stackexchange.com/q/314472) (at the youtube video, look at minutes 13 to 25)
24. [Introduction to Statistical Inference | Stanford (Lecture 16 — MLE under model misspecification)](https://web.stanford.edu/class/stats200/Lecture16.pdf)
25. Sycorax says Reinstate Monica ([https://stats.stackexchange.com/users/22311/sycorax-says-reinstate-monica](https://stats.stackexchange.com/users/22311/sycorax-says-reinstate-monica)), the relationship between maximizing the likelihood and minimizing the cross-entropy, URL (version: 2019-11-06): [https://stats.stackexchange.com/q/364237](https://stats.stackexchange.com/q/364237)
26. Coles, Stuart (2001). [An Introduction to Statistical Modeling of Extreme Values](https://link.springer.com/book/10.1007/978-1-4471-3675-0). Springer Series in Statistics. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-1-4471-3675-0](https://doi.org/10.1007%2F978-1-4471-3675-0). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-84996-874-4](https://en.wikipedia.org/wiki/Special:BookSources/978-1-84996-874-4). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0172-7397](https://search.worldcat.org/issn/0172-7397).
27. [Statistical Analysis of Extreme Values](https://link.springer.com/book/10.1007/978-3-7643-7399-3). 2007. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-3-7643-7399-3](https://doi.org/10.1007%2F978-3-7643-7399-3). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-7643-7230-9](https://en.wikipedia.org/wiki/Special:BookSources/978-3-7643-7230-9).
28. Embrechts, Paul; Klüppelberg, Claudia; Mikosch, Thomas (1997). [Modelling Extremal Events](https://link.springer.com/book/10.1007/978-3-642-33483-2). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-3-642-33483-2](https://doi.org/10.1007%2F978-3-642-33483-2). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-642-08242-9](https://en.wikipedia.org/wiki/Special:BookSources/978-3-642-08242-9).
29. [Loss Models](https://onlinelibrary.wiley.com/doi/book/10.1002/9781118787106?msockid=02e737d36c826f7c12702591688261a5). Wiley Series in Probability and Statistics. 2013. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1002/9781118787106](https://doi.org/10.1002%2F9781118787106). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-118-34356-2](https://en.wikipedia.org/wiki/Special:BookSources/978-1-118-34356-2).
30. Gerrard, R.; Tsanakas, A. (2011). ["Failure Probability Under Parameter Uncertainty"](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1539-6924.2010.01549.x). *Risk Analysis*. **31** (5): 727–744. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2011RiskA..31..727G](https://ui.adsabs.harvard.edu/abs/2011RiskA..31..727G). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1111/j.1539-6924.2010.01549.x](https://doi.org/10.1111%2Fj.1539-6924.2010.01549.x). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1539-6924](https://search.worldcat.org/issn/1539-6924). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [21175720](https://pubmed.ncbi.nlm.nih.gov/21175720).
31. Jewson, Stephen; Sweeting, Trevor; Jewson, Lynne (2025-02-20). ["Reducing reliability bias in assessments of extreme weather risk using calibrating priors"](https://ascmo.copernicus.org/articles/11/1/2025/). *Advances in Statistical Climatology, Meteorology and Oceanography*. **11** (1): 1–22. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2025ASCMO..11....1J](https://ui.adsabs.harvard.edu/abs/2025ASCMO..11....1J). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.5194/ascmo-11-1-2025](https://doi.org/10.5194%2Fascmo-11-1-2025). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [2364-3579](https://search.worldcat.org/issn/2364-3579).
32. Severini, Thomas A.; Mukerjee, Rahul; Ghosh, Malay (2002-12-01). ["On an exact probability matching property of right-invariant priors"](https://doi.org/10.1093/biomet/89.4.952). *Biometrika*. **89** (4): 952–957. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1093/biomet/89.4.952](https://doi.org/10.1093%2Fbiomet%2F89.4.952). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0006-3444](https://search.worldcat.org/issn/0006-3444).
33. Gerrard, R.; Tsanakas, A. (2011). ["Failure Probability Under Parameter Uncertainty"](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1539-6924.2010.01549.x). *Risk Analysis*. **31** (5): 727–744. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2011RiskA..31..727G](https://ui.adsabs.harvard.edu/abs/2011RiskA..31..727G). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1111/j.1539-6924.2010.01549.x](https://doi.org/10.1111%2Fj.1539-6924.2010.01549.x). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1539-6924](https://search.worldcat.org/issn/1539-6924). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [21175720](https://pubmed.ncbi.nlm.nih.gov/21175720).
34. Jewson, Stephen; Sweeting, Trevor; Jewson, Lynne (2025-02-20). ["Reducing reliability bias in assessments of extreme weather risk using calibrating priors"](https://ascmo.copernicus.org/articles/11/1/2025/). *Advances in Statistical Climatology, Meteorology and Oceanography*. **11** (1): 1–22. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2025ASCMO..11....1J](https://ui.adsabs.harvard.edu/abs/2025ASCMO..11....1J). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.5194/ascmo-11-1-2025](https://doi.org/10.5194%2Fascmo-11-1-2025). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [2364-3579](https://search.worldcat.org/issn/2364-3579).
35. Fletcher, R. (1987). [Practical Methods of Optimization](https://archive.org/details/practicalmethods0000flet) (Second ed.). New York, NY: John Wiley & Sons. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-91547-5](https://en.wikipedia.org/wiki/Special:BookSources/0-471-91547-5).
36. [Nocedal, Jorge](https://en.wikipedia.org/wiki/Jorge_Nocedal); Wright, Stephen J. (2006). *Numerical Optimization* (Second ed.). New York, NY: Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-30303-0](https://en.wikipedia.org/wiki/Special:BookSources/0-387-30303-0).
37. Daganzo, Carlos (1979). *Multinomial Probit: The Theory and its Application to Demand Forecasting*. New York: Academic Press. pp. 61–78. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-12-201150-3](https://en.wikipedia.org/wiki/Special:BookSources/0-12-201150-3).
38. Gould, William; Pitblado, Jeffrey; Poi, Brian (2010). *Maximum Likelihood Estimation with Stata* (Fourth ed.). College Station: Stata Press. pp. 13–20. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-59718-078-8](https://en.wikipedia.org/wiki/Special:BookSources/978-1-59718-078-8).
39. Murphy, Kevin P. (2012). [Machine Learning: A Probabilistic Perspective](https://books.google.com/books?id=NZP6AQAAQBAJ&pg=PA247). Cambridge: MIT Press. p. 247. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-262-01802-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-262-01802-9).
40. [Amemiya, Takeshi](https://en.wikipedia.org/wiki/Takeshi_Amemiya) (1985). [Advanced Econometrics](https://archive.org/details/advancedeconomet00amem/page/137). Cambridge: Harvard University Press. pp. [137–138](https://archive.org/details/advancedeconomet00amem/page/137). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-674-00560-0](https://en.wikipedia.org/wiki/Special:BookSources/0-674-00560-0).
41. [Sargan, Denis](https://en.wikipedia.org/wiki/Denis_Sargan) (1988). "Methods of Numerical Optimization". *Lecture Notes on Advanced Econometric Theory*. Oxford: Basil Blackwell. pp. 161–169. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-631-14956-2](https://en.wikipedia.org/wiki/Special:BookSources/0-631-14956-2).
42. See theorem 10.1 in Avriel, Mordecai (1976). [Nonlinear Programming: Analysis and Methods](https://books.google.com/books?id=byF4Xb1QbvMC&pg=PA293). Englewood Cliffs, NJ: Prentice-Hall. pp. 293–294. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-486-43227-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-486-43227-4).
43. Gill, Philip E.; Murray, Walter; [Wright, Margaret H.](https://en.wikipedia.org/wiki/Margaret_H._Wright) (1981). [Practical Optimization](https://archive.org/details/practicaloptimiz00gill). London, UK: Academic Press. pp. [312](https://archive.org/details/practicaloptimiz00gill/page/n329)–313. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-12-283950-1](https://en.wikipedia.org/wiki/Special:BookSources/0-12-283950-1).
44. [Edgeworth, Francis Y.](https://en.wikipedia.org/wiki/Francis_Ysidro_Edgeworth) (Sep 1908). ["On the probable errors of frequency-constants"](https://zenodo.org/record/1449468). *Journal of the Royal Statistical Society*. **71** (3): 499–512. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2339293](https://doi.org/10.2307%2F2339293). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2339293](https://www.jstor.org/stable/2339293).
45. [Edgeworth, Francis Y.](https://en.wikipedia.org/wiki/Francis_Ysidro_Edgeworth) (Dec 1908). ["On the probable errors of frequency-constants"](https://zenodo.org/record/1449468). *Journal of the Royal Statistical Society*. **71** (4): 651–678. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2339378](https://doi.org/10.2307%2F2339378). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2339378](https://www.jstor.org/stable/2339378).
46. [Pfanzagl, Johann](https://en.wikipedia.org/wiki/Johann_Pfanzagl) (1994). *Parametric Statistical Theory*. [Walter de Gruyter](https://en.wikipedia.org/wiki/Walter_de_Gruyter). pp. 207–208. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1515/9783110889765](https://doi.org/10.1515%2F9783110889765). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-11-013863-4](https://en.wikipedia.org/wiki/Special:BookSources/978-3-11-013863-4). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1291393](https://mathscinet.ams.org/mathscinet-getitem?mr=1291393).
47. [Hald, Anders](https://en.wikipedia.org/wiki/Anders_Hald) (1999). ["On the History of Maximum Likelihood in Relation to Inverse Probability and Least Squares"](https://www.jstor.org/stable/2676741). *Statistical Science*. **14** (2): 214–222. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/ss/1009212248](https://doi.org/10.1214%2Fss%2F1009212248). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0883-4237](https://search.worldcat.org/issn/0883-4237). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2676741](https://www.jstor.org/stable/2676741).
48. Wilks, S.S. (1938). ["The large-sample distribution of the likelihood ratio for testing composite hypotheses"](https://doi.org/10.1214%2Faoms%2F1177732360). *[Annals of Mathematical Statistics](https://en.wikipedia.org/wiki/Annals_of_Mathematical_Statistics)*. **9**: 60–62. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/aoms/1177732360](https://doi.org/10.1214%2Faoms%2F1177732360).
49. Owen, Art B. (2001). *Empirical Likelihood*. London, UK; Boca Raton, FL: Chapman & Hall; CRC Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-58488-071-4](https://en.wikipedia.org/wiki/Special:BookSources/978-1-58488-071-4).
50. [Wilks, Samuel S.](https://en.wikipedia.org/wiki/Samuel_S._Wilks) (1962). *Mathematical Statistics*. New York, NY: John Wiley & Sons. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-94650-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-94650-2). `{{`[`cite book`](https://en.wikipedia.org/wiki/Template:Cite_book)`}}`: ISBN / Date incompatibility ([help](https://en.wikipedia.org/wiki/Help:CS1_errors#invalid_isbn_date))
51. [Savage, Leonard J.](https://en.wikipedia.org/wiki/Leonard_J._Savage) (1976). ["On rereading R.A. Fisher"](https://doi.org/10.1214%2Faos%2F1176343456). *The Annals of Statistics*. **4** (3): 441–500. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/aos/1176343456](https://doi.org/10.1214%2Faos%2F1176343456). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2958221](https://www.jstor.org/stable/2958221).
52. Pratt, John W. (1976). ["F. Y. Edgeworth and R. A. Fisher on the efficiency of maximum likelihood estimation"](https://doi.org/10.1214%2Faos%2F1176343457). *The Annals of Statistics*. **4** (3): 501–514. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/aos/1176343457](https://doi.org/10.1214%2Faos%2F1176343457). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2958222](https://www.jstor.org/stable/2958222).
53. [Stigler, Stephen M.](https://en.wikipedia.org/wiki/Stephen_M._Stigler) (1978). "Francis Ysidro Edgeworth, statistician". *Journal of the Royal Statistical Society, Series A*. **141** (3): 287–322. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2344804](https://doi.org/10.2307%2F2344804). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2344804](https://www.jstor.org/stable/2344804).
54. Stigler, Stephen M. (1986). [The history of statistics: the measurement of uncertainty before 1900](https://archive.org/details/historyofstatist00stig). Harvard University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-674-40340-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-674-40340-6).
55. Stigler, Stephen M. (1999). *Statistics on the table: the history of statistical concepts and methods*. Harvard University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-674-83601-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-674-83601-3).
56. [Hald, Anders](https://en.wikipedia.org/wiki/Anders_Hald) (1998). *A history of mathematical statistics from 1750 to 1930*. New York, NY: Wiley. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-17912-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-17912-2).
57. Hald, Anders (1999). ["On the history of maximum likelihood in relation to inverse probability and least squares"](http://projecteuclid.org/download/pdf_1/euclid.ss/1009212248). *Statistical Science*. **14** (2): 214–222. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/ss/1009212248](https://doi.org/10.1214%2Fss%2F1009212248). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2676741](https://www.jstor.org/stable/2676741).
58. Aldrich, John (1997). ["R.A. Fisher and the making of maximum likelihood 1912–1922"](https://doi.org/10.1214%2Fss%2F1030037906). *Statistical Science*. **12** (3): 162–176. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/ss/1030037906](https://doi.org/10.1214%2Fss%2F1030037906). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1617519](https://mathscinet.ams.org/mathscinet-getitem?mr=1617519).

## Further reading

- [Cramer, J.S.](https://en.wikipedia.org/wiki/Mars_Cramer) (1986). [Econometric Applications of Maximum Likelihood Methods](https://archive.org/details/econometricappli0000cram). New York, NY: Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-25317-9](https://en.wikipedia.org/wiki/Special:BookSources/0-521-25317-9).
- Eliason, Scott R. (1993). *Maximum Likelihood Estimation: Logic and Practice*. Newbury Park: Sage. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-8039-4107-2](https://en.wikipedia.org/wiki/Special:BookSources/0-8039-4107-2).
- [King, Gary](https://en.wikipedia.org/wiki/Gary_King_(political_scientist) "Gary King (political scientist)") (1989). *Unifying Political Methodology: the Likehood Theory of Statistical Inference*. Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-36697-6](https://en.wikipedia.org/wiki/Special:BookSources/0-521-36697-6).
- [Le Cam, Lucien](https://en.wikipedia.org/wiki/Lucien_Le_Cam) (1990). "Maximum likelihood: An Introduction". *ISI Review*. **58** (2): 153–171. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/1403464](https://doi.org/10.2307%2F1403464). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [1403464](https://www.jstor.org/stable/1403464).
- Magnus, Jan R. (2017). "Maximum Likelihood". *Introduction to the Theory of Econometrics*. Amsterdam, NL: VU University Press. pp. 53–68. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-90-8659-766-6](https://en.wikipedia.org/wiki/Special:BookSources/978-90-8659-766-6).
- Millar, Russell B. (2011). *Maximum Likelihood Estimation and Inference*. Hoboken, NJ: Wiley. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-470-09482-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-470-09482-2).
- [Pickles, Andrew](https://en.wikipedia.org/wiki/Andrew_Pickles) (1986). [An Introduction to Likelihood Analysis](https://archive.org/details/introductiontoli0000pick). Norwich: W. H. Hutchins & Sons. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-86094-190-6](https://en.wikipedia.org/wiki/Special:BookSources/0-86094-190-6).
- Severini, Thomas A. (2000). *Likelihood Methods in Statistics*. New York, NY: Oxford University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-19-850650-3](https://en.wikipedia.org/wiki/Special:BookSources/0-19-850650-3).
- [Ward, Michael D.](https://en.wikipedia.org/wiki/Michael_D._Ward); Ahlquist, John S. (2018). *Maximum Likelihood for Social Science: Strategies for Analysis*. Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-316-63682-4](https://en.wikipedia.org/wiki/Special:BookSources/978-1-316-63682-4).

## External links

- Tilevik, Andreas (2022). [Maximum likelihood vs least squares in linear regression](https://www.youtube.com/watch?v=bhTIpGtWtzQ) (video)
- ["Maximum-likelihood method"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society), 2001 \[1994\]
- Purcell, S. ["Maximum Likelihood Estimation"](https://web.archive.org/web/20191027165903/http://statgen.iop.kcl.ac.uk/bgim/mle/sslike_1.html). Archived from [the original](http://statgen.iop.kcl.ac.uk/bgim/mle/sslike_1.html) on 2019-10-27. Retrieved 2007-04-24.
- [Sargent, Thomas](https://en.wikipedia.org/wiki/Thomas_J._Sargent); Stachurski, John. ["Maximum Likelihood Estimation"](https://intro.quantecon.org/mle.html). *Quantitative Economics with [Python](https://en.wikipedia.org/wiki/Python_(programming_language) "Python (programming language)")*.
- Toomet, Ott; Henningsen, Arne (2019-05-19). ["maxLik: A package for maximum likelihood estimation in R"](https://cran.r-project.org/package=maxLik).
- Lesser, Lawrence M. (2007). ["'MLE' song lyrics"](http://www.math.utep.edu/Faculty/lesser/MLE.html). Mathematical Sciences / College of Science. *University of Texas*. El Paso, TX. Retrieved 2021-03-06.
