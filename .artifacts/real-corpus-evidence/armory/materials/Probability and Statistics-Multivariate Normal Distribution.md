[[probability-statistics.base]]

> Source: [[Multivariate Normal Distribution]]
> License: Wikipedia content is available under CC BY-SA 4.0.

<table class="infobox infobox-table ib-prob-dist">

Multivariate normal

&#10;

Probability density function
![[media/095dba173397747187c7df745e33ea9849c60885.png]]

Many sample points from a multivariate normal distribution with ${\boldsymbol {\mu }}=\left[{\begin{smallmatrix}0\\0\end{smallmatrix}}\right]$ and ${\boldsymbol {\Sigma }}=\left[{\begin{smallmatrix}1&3/5\\3/5&2\end{smallmatrix}}\right]$, shown along with the 3-sigma ellipse, the two marginal distributions, and the two 1-d histograms.

Notation
${\mathcal {N}}({\boldsymbol {\mu }},\,{\boldsymbol {\Sigma }})$

[Parameters](https://en.wikipedia.org/wiki/Statistical_parameter)
<em><strong>μ</strong></em> ∈ <strong>R</strong><sup><em>k</em></sup> — [location](https://en.wikipedia.org/wiki/Location_parameter)<br />
<strong>Σ</strong> ∈ <strong>R</strong><sup><em>k</em> × <em>k</em></sup> — [covariance](https://en.wikipedia.org/wiki/Covariance_matrix) ([positive semi-definite matrix](https://en.wikipedia.org/wiki/Positive_semi-definite_matrix))

[Support](https://en.wikipedia.org/wiki/Support_(mathematics))
<em><strong>x</strong></em> ∈ <em><strong>μ</strong></em> + span(<strong>Σ</strong>) ⊆ <strong>R</strong><sup><em>k</em></sup>

[[Probability Density Function|PDF]]
$(2\pi )^{-k/2}\det({\boldsymbol {\Sigma }})^{-1/2}\,\exp \left(-{\frac {1}{2}}(\mathbf {x} -{\boldsymbol {\mu }})^{\mathrm {T} }{\boldsymbol {\Sigma }}^{-1}(\mathbf {x} -{\boldsymbol {\mu }})\right),$<br />
exists only when <strong>Σ</strong> is [[Positive-Definite Matrix|positive-definite]]

[Mean](https://en.wikipedia.org/wiki/Expected_value)
<em><strong>μ</strong></em>

[Mode](https://en.wikipedia.org/wiki/Mode_(statistics))
<em><strong>μ</strong></em>

[Variance](https://en.wikipedia.org/wiki/Covariance_matrix)
<strong>Σ</strong>

[Entropy](https://en.wikipedia.org/wiki/Information_entropy)
${\frac {k}{2}}\log {\mathord {\left(2\pi \mathrm {e} \right)}}+{\frac {1}{2}}\log \det {\mathord {\left({\boldsymbol {\Sigma }}\right)}}$

[[Moment Generating Function|MGF]]
$\exp \!{\Big (}{\boldsymbol {\mu }}^{\mathrm {T} }\mathbf {t} +{\tfrac {1}{2}}\mathbf {t} ^{\mathrm {T} }{\boldsymbol {\Sigma }}\mathbf {t} {\Big )}$

[[Characteristic Function|CF]]
$\exp \!{\Big (}i{\boldsymbol {\mu }}^{\mathrm {T} }\mathbf {t} -{\tfrac {1}{2}}\mathbf {t} ^{\mathrm {T} }{\boldsymbol {\Sigma }}\mathbf {t} {\Big )}$

[[Kullback-Leibler Divergence|Kullback–Leibler divergence]]
<em>See [§ Kullback–Leibler divergence](#Kullback–Leibler_divergence)</em>

</table>

In [probability theory](https://en.wikipedia.org/wiki/Probability_theory) and [statistics](https://en.wikipedia.org/wiki/Statistics), the **multivariate normal distribution**, **multivariate Gaussian distribution**, or **joint normal distribution** is a generalization of the one-dimensional ([univariate](https://en.wikipedia.org/wiki/Univariate)) [normal distribution](https://en.wikipedia.org/wiki/Normal_distribution) to higher [dimensions](https://en.wikipedia.org/wiki/Dimension). One definition is that a [random vector](https://en.wikipedia.org/wiki/Random_vector) is said to be *k*-variate normally distributed if every [linear combination](https://en.wikipedia.org/wiki/Linear_combination) of its *k* components has a univariate normal distribution. Its importance derives mainly from the [[Central Limit Theorem|multivariate central limit theorem]]. The multivariate normal distribution is often used to describe, at least approximately, any set of (possibly) [correlated](https://en.wikipedia.org/wiki/Correlation_(statistics)) real-valued [random variables](https://en.wikipedia.org/wiki/Random_variable), each of which clusters around a mean value.

## Definitions

### Notation and parametrization

The multivariate normal distribution of a *k*-dimensional random vector $\mathbf {X} =(X_{1},\ldots ,X_{k})^{\mathrm {T} }$ can be written in the following notation:

$\mathbf {X} \ \sim \ {\mathcal {N}}({\boldsymbol {\mu }},\,{\boldsymbol {\Sigma }}),$

or to make it explicitly known that $\mathbf {X}$ is *k*-dimensional,

$\mathbf {X} \ \sim \ {\mathcal {N}}_{k}({\boldsymbol {\mu }},\,{\boldsymbol {\Sigma }}),$

with *k*-dimensional [mean vector](https://en.wikipedia.org/wiki/Mean_vector)

${\boldsymbol {\mu }}=\operatorname {E} [\mathbf {X} ]=(\operatorname {E} [X_{1}],\operatorname {E} [X_{2}],\ldots ,\operatorname {E} [X_{k}])^{\mathrm {T} },$

and $k\times k$ [covariance matrix](https://en.wikipedia.org/wiki/Covariance_matrix)

$\Sigma _{i,j}=\operatorname {E} [(X_{i}-\mu _{i})(X_{j}-\mu _{j})]=\operatorname {Cov} [X_{i},X_{j}]$

such that $1\leq i\leq k$ and $1\leq j\leq k$. The [inverse](https://en.wikipedia.org/wiki/Matrix_inverse) of the covariance matrix is called the [precision matrix](https://en.wikipedia.org/wiki/Precision_(statistics) "Precision (statistics)"), denoted by ${\boldsymbol {Q}}={\boldsymbol {\Sigma }}^{-1}$.

### Standard normal random vector

A real [random vector](https://en.wikipedia.org/wiki/Random_vector) $\mathbf {X} =(X_{1},\ldots ,X_{k})^{\mathrm {T} }$ is called a **standard normal random vector** if all of its components $X_{i}$ are independent and each is a zero-mean unit-variance normally distributed random variable, i.e. if $X_{i}\sim \ {\mathcal {N}}(0,1)$ for all $i=1\ldots k$.

### Centered normal random vector

A real random vector $\mathbf {X} =(X_{1},\ldots ,X_{k})^{\mathrm {T} }$ is called a **centered normal random vector** if there exists a $k\times \ell$ matrix ${\boldsymbol {A}}$ such that ${\boldsymbol {A}}\mathbf {Z}$ has the same distribution as $\mathbf {X}$ where $\mathbf {Z}$ is a standard normal random vector with $\ell$ components.

### Normal random vector

A real random vector $\mathbf {X} =(X_{1},\ldots ,X_{k})^{\mathrm {T} }$ is called a **normal random vector** if there exists a random $\ell$-vector $\mathbf {Z}$, which is a standard normal random vector, a $k$-vector ${\boldsymbol {\mu }}$, and a $k\times \ell$ matrix ${\boldsymbol {A}}$, such that $\mathbf {X} ={\boldsymbol {A}}\mathbf {Z} +{\boldsymbol {\mu }}$.

Formally:

$\mathbf {X} \ \sim \ {\mathcal {N}}_{k}({\boldsymbol {\mu }},{\boldsymbol {\Sigma }})\iff {\text{there exist }}{\boldsymbol {\mu }}\in \mathbb {R} ^{k},{\boldsymbol {A}}\in \mathbb {R} ^{k\times \ell }{\text{ such that }}\mathbf {X} ={\boldsymbol {A}}\mathbf {Z} +{\boldsymbol {\mu }}{\text{ and }}\forall n=1,\ldots ,\ell :Z_{n}\sim \ {\mathcal {N}}(0,1),{\text{i.i.d.}}$

Here the [covariance matrix](https://en.wikipedia.org/wiki/Covariance_matrix) is ${\boldsymbol {\Sigma }}={\boldsymbol {A}}{\boldsymbol {A}}^{\mathrm {T} }$.

In the [degenerate](https://en.wikipedia.org/wiki/Degeneracy_(mathematics) "Degeneracy (mathematics)") case where the covariance matrix is [singular](https://en.wikipedia.org/wiki/Singular_matrix), the corresponding distribution has no density; see the [section below](#Degenerate_case) for details. This case arises frequently in [statistics](https://en.wikipedia.org/wiki/Statistics); for example, in the distribution of the vector of [residuals](https://en.wikipedia.org/wiki/Errors_and_residuals_in_statistics) in the [ordinary least squares](https://en.wikipedia.org/wiki/Ordinary_least_squares) regression. The $X_{i}$ are in general *not* independent; they can be seen as the result of applying the matrix ${\boldsymbol {A}}$ to a collection of independent Gaussian variables $\mathbf {Z}$.

### Equivalent definitions

The following definitions are equivalent to the definition given above. A random vector $\mathbf {X} =(X_{1},\ldots ,X_{k})^{\mathrm {T} }$ has a multivariate normal distribution if it satisfies one of the following equivalent conditions.

- Every linear combination $Y=a_{1}X_{1}+\cdots +a_{k}X_{k}$ of its components is [normally distributed](https://en.wikipedia.org/wiki/Normal_distribution). That is, for any constant vector $\mathbf {a} \in \mathbb {R} ^{k}$, the random variable $Y=\mathbf {a} ^{\mathrm {T} }\mathbf {X}$ has a univariate normal distribution, where a univariate normal distribution with zero variance is a point mass on its mean.
- There is a *k*-vector $\mathbf {\mu }$ and a symmetric, [[Positive-Definite Matrix|positive semidefinite]] $k\times k$ matrix ${\boldsymbol {\Sigma }}$, such that the [characteristic function](https://en.wikipedia.org/wiki/Characteristic_function_(probability_theory) "Characteristic function (probability theory)") of $\mathbf {X}$ is 

$$
\varphi _{\mathbf {X} }(\mathbf {u} )=\exp {\Big (}i\mathbf {u} ^{\mathrm {T} }{\boldsymbol {\mu }}-{\tfrac {1}{2}}\mathbf {u} ^{\mathrm {T} }{\boldsymbol {\Sigma }}\mathbf {u} {\Big )}.
$$

The spherical normal distribution can be characterised as the unique distribution where components are independent in any orthogonal coordinate system.

### Density function

![[media/d5921c2fa096cbcce4bdb899186a6e6e72a20366.png]]
Bivariate normal [joint density](https://en.wikipedia.org/wiki/Joint_probability_distribution#Density_function_or_mass_function)

#### Non-degenerate case

The multivariate normal distribution is said to be "non-degenerate" when the symmetric [covariance matrix](https://en.wikipedia.org/wiki/Covariance_matrix) ${\boldsymbol {\Sigma }}$ is [[Positive-Definite Matrix|positive definite]]. In this case the distribution has [[Probability Density Function|density]]

$f_{\mathbf {X} }(x_{1},\ldots ,x_{k})={\frac {\exp \left(-{\frac {1}{2}}\left({\mathbf {x} }-{\boldsymbol {\mu }}\right)^{\mathrm {T} }{\boldsymbol {\Sigma }}^{-1}\left({\mathbf {x} }-{\boldsymbol {\mu }}\right)\right)}{\sqrt {(2\pi )^{k}|{\boldsymbol {\Sigma }}|}}}$

where ${\mathbf {x} }$ is a real *k*-dimensional column vector and $|{\boldsymbol {\Sigma }}|\equiv \det {\boldsymbol {\Sigma }}$ is the [[Determinant]] of ${\boldsymbol {\Sigma }}$, also known as the [generalized variance](https://en.wikipedia.org/wiki/Generalized_variance). The equation above reduces to that of the univariate normal distribution if ${\boldsymbol {\Sigma }}$ is a $1\times 1$ matrix (i.e., a single real number).

The circularly symmetric version of the [complex normal distribution](https://en.wikipedia.org/wiki/Complex_normal_distribution) has a slightly different form.

Each iso-density [locus](https://en.wikipedia.org/wiki/Locus_(mathematics) "Locus (mathematics)") — the locus of points in *k*-dimensional space each of which gives the same particular value of the density — is an [ellipse](https://en.wikipedia.org/wiki/Ellipse) or its higher-dimensional generalization; hence the multivariate normal is a special case of the [elliptical distributions](https://en.wikipedia.org/wiki/Elliptical_distribution).

The quantity ${\sqrt {({\mathbf {x} }-{\boldsymbol {\mu }})^{\mathrm {T} }{\boldsymbol {\Sigma }}^{-1}({\mathbf {x} }-{\boldsymbol {\mu }})}}$ is known as the [Mahalanobis distance](https://en.wikipedia.org/wiki/Mahalanobis_distance), which represents the distance of the test point ${\mathbf {x} }$ from the mean ${\boldsymbol {\mu }}$. The squared Mahalanobis distance $({\mathbf {x} }-{\boldsymbol {\mu }})^{\mathrm {T} }{\boldsymbol {\Sigma }}^{-1}({\mathbf {x} }-{\boldsymbol {\mu }})$ is decomposed into a sum of *k* terms, each term being a product of three meaningful components. Note that in the case when $k=1$, the distribution reduces to a univariate normal distribution and the Mahalanobis distance reduces to the absolute value of the [standard score](https://en.wikipedia.org/wiki/Standard_score). See also [Interval](#Interval) below.

#### Bivariate case

In the 2-dimensional nonsingular case ($k=\operatorname {rank} \left(\Sigma \right)=2$), the [[Probability Density Function]] of a vector ${\text{[XY]}}\prime$ is: 

$$
f(x,y)={\frac {1}{2\pi \sigma _{X}\sigma _{Y}{\sqrt {1-\rho ^{2}}}}}\exp \left(-{\frac {1}{2\left[1-\rho ^{2}\right]}}\left[\left({\frac {x-\mu _{X}}{\sigma _{X}}}\right)^{2}-2\rho \left({\frac {x-\mu _{X}}{\sigma _{X}}}\right)\left({\frac {y-\mu _{Y}}{\sigma _{Y}}}\right)+\left({\frac {y-\mu _{Y}}{\sigma _{Y}}}\right)^{2}\right]\right)
$$

 where $\rho$ is the [correlation](https://en.wikipedia.org/wiki/Pearson_product-moment_correlation_coefficient) between $X$ and $Y$ and where $\sigma _{X}>0$ and $\sigma _{Y}>0$. In this case,

${\boldsymbol {\mu }}={\begin{pmatrix}\mu _{X}\\\mu _{Y}\end{pmatrix}},\quad {\boldsymbol {\Sigma }}={\begin{pmatrix}\sigma _{X}^{2}&\rho \sigma _{X}\sigma _{Y}\\\rho \sigma _{X}\sigma _{Y}&\sigma _{Y}^{2}\end{pmatrix}}.$

In the bivariate case, the first equivalent condition for multivariate reconstruction of normality can be made less restrictive as it is sufficient to verify that a [countably infinite](https://en.wikipedia.org/wiki/Countably_infinite) set of distinct linear combinations of $X$ and $Y$ are normal in order to conclude that the vector of ${\text{[XY]}}\prime$ is bivariate normal.

The bivariate iso-density loci plotted in the $x,y$-plane are [ellipses](https://en.wikipedia.org/wiki/Ellipse), whose [principal axes](https://en.wikipedia.org/wiki/Semi-major_and_semi-minor_axes) are defined by the [eigenvectors](https://en.wikipedia.org/wiki/Eigenvectors) of the covariance matrix ${\boldsymbol {\Sigma }}$ (the major and minor [semidiameters](https://en.wikipedia.org/wiki/Semidiameter) of the ellipse equal the square-root of the ordered eigenvalues).

![[media/7cf00e56e144e550bc6b534e0dbe9670d3b9331e.png]]
Bivariate normal distribution centered at $(1,3)$ with a standard deviation of 3 in roughly the $(0.878,0.478)$ direction and of 1 in the orthogonal direction.

As the absolute value of the correlation parameter $\rho$ increases, these loci are squeezed toward the following line :

$y(x)=\operatorname {sgn} (\rho ){\frac {\sigma _{Y}}{\sigma _{X}}}(x-\mu _{X})+\mu _{Y}.$

This is because this expression, with $\operatorname {sgn} (\rho )$ (where sgn is the [sign function](https://en.wikipedia.org/wiki/Sign_function)) replaced by $\rho$, is the [best linear unbiased prediction](https://en.wikipedia.org/wiki/Best_linear_unbiased_prediction) of $Y$ given a value of $X$.

#### Degenerate case

If the covariance matrix ${\boldsymbol {\Sigma }}$ is not full rank, then the multivariate normal distribution is degenerate and does not have a density. More precisely, it does not have a density with respect to *k*-dimensional [Lebesgue measure](https://en.wikipedia.org/wiki/Lebesgue_measure) (which is the usual measure assumed in calculus-level probability courses). Only random vectors whose distributions are [absolutely continuous](https://en.wikipedia.org/wiki/Absolute_continuity#Absolute_continuity_of_measures) with respect to a measure are said to have densities (with respect to that measure). To talk about densities but avoid dealing with measure-theoretic complications it can be simpler to restrict attention to a subset of $\operatorname {rank} ({\boldsymbol {\Sigma }})$ of the coordinates of $\mathbf {x}$ such that the covariance matrix for this subset is positive definite; then the other coordinates may be thought of as an [affine function](https://en.wikipedia.org/wiki/Affine_function) of these selected coordinates.

To talk about densities meaningfully in singular cases, then, we must select a different base measure. Using the [disintegration theorem](https://en.wikipedia.org/wiki/Disintegration_theorem) we can define a restriction of Lebesgue measure to the $\operatorname {rank} ({\boldsymbol {\Sigma }})$-dimensional affine subspace of $\mathbb {R} ^{k}$ where the Gaussian distribution is supported, i.e. $\left\{{\boldsymbol {\mu }}+{\boldsymbol {\Sigma ^{1/2}}}\mathbf {v} :\mathbf {v} \in \mathbb {R} ^{k}\right\}$. With respect to this measure the distribution has the density of the following motif:

$f(\mathbf {x} )={\frac {\exp \left(-{\frac {1}{2}}\left(\mathbf {x} -{\boldsymbol {\mu }}\right)^{\mathrm {T} }{\boldsymbol {\Sigma }}^{+}\left(\mathbf {x} -{\boldsymbol {\mu }}\right)\right)}{\sqrt {\det \nolimits ^{*}(2\pi {\boldsymbol {\Sigma }})}}}$

where ${\boldsymbol {\Sigma }}^{+}$ is the [generalized inverse](https://en.wikipedia.org/wiki/Generalized_inverse) and $\det \nolimits ^{*}$ is the [pseudo-determinant](https://en.wikipedia.org/wiki/Pseudo-determinant).

### Cumulative distribution function

The notion of [[Cumulative Distribution Function]] (cdf) in dimension 1 can be extended in two ways to the multidimensional case, based on rectangular and ellipsoidal regions.

The first way is to define the cdf $F(\mathbf {x} )$ of a random vector $\mathbf {X}$ as the probability that all components of $\mathbf {X}$ are less than or equal to the corresponding values in the vector $\mathbf {x}$:

$F(\mathbf {x} )=\mathbb {P} (\mathbf {X} \leq \mathbf {x} ),\quad {\text{where }}\mathbf {X} \sim {\mathcal {N}}({\boldsymbol {\mu }},\,{\boldsymbol {\Sigma }}).$

Though there is no closed form for $F(\mathbf {x} )$, there are a number of algorithms that estimate it numerically.

Another way is to define the cdf $F(r)$ as the probability that a sample lies inside the ellipsoid determined by its [Mahalanobis distance](https://en.wikipedia.org/wiki/Mahalanobis_distance) $r$ from the Gaussian, a direct generalization of the standard deviation. In order to compute the values of this function, closed analytic formula exist, as follows.

#### Interval

The [interval](https://en.wikipedia.org/wiki/Interval_estimation) for the multivariate normal distribution yields a region consisting of those vectors **x** satisfying

$({\mathbf {x} }-{\boldsymbol {\mu }})^{\mathrm {T} }{\boldsymbol {\Sigma }}^{-1}({\mathbf {x} }-{\boldsymbol {\mu }})\leq \chi _{k}^{2}(p).$

Here ${\mathbf {x} }$ is a $k$-dimensional vector, ${\boldsymbol {\mu }}$ is the known $k$-dimensional mean vector, ${\boldsymbol {\Sigma }}$ is the known [covariance matrix](https://en.wikipedia.org/wiki/Covariance_matrix) and $\chi _{k}^{2}(p)$ is the [quantile function](https://en.wikipedia.org/wiki/Quantile_function) for probability $p$ of the [chi-squared distribution](https://en.wikipedia.org/wiki/Chi-squared_distribution) with $k$ degrees of freedom. When $k=2,$ the expression defines the interior of an ellipse and the chi-squared distribution simplifies to an [exponential distribution](https://en.wikipedia.org/wiki/Exponential_distribution) with mean equal to two (rate equal to half).

### Complementary cumulative distribution function (tail distribution)

The [[Cumulative Distribution Function|complementary cumulative distribution function]] (ccdf) or the **tail distribution** is defined as ${\overline {F}}(\mathbf {x} )=1-\mathbb {P} \left(\mathbf {X} \leq \mathbf {x} \right)$. When $\mathbf {X} \sim {\mathcal {N}}({\boldsymbol {\mu }},\,{\boldsymbol {\Sigma }})$, then the ccdf can be written as a probability the maximum of dependent Gaussian variables:

${\overline {F}}(\mathbf {x} )=\mathbb {P} \left(\bigcup _{i}\{X_{i}\geq x_{i}\}\right)=\mathbb {P} \left(\max _{i}Y_{i}\geq 0\right),\quad {\text{where }}\mathbf {Y} \sim {\mathcal {N}}\left({\boldsymbol {\mu }}-\mathbf {x} ,\,{\boldsymbol {\Sigma }}\right).$

While no simple closed formula exists for computing the ccdf, the maximum of dependent Gaussian variables can be estimated accurately via the [[Monte Carlo Method]].

## Properties

### Moments

The *k*th-order [moments](https://en.wikipedia.org/wiki/Moment_(mathematics) "Moment (mathematics)") of **x** are given by

$\mu _{1,\ldots ,N}(\mathbf {x} )\mathrel {\stackrel {\mathrm {def} }{=}} \mu _{r_{1},\ldots ,r_{N}}(\mathbf {x} )\mathrel {\stackrel {\mathrm {def} }{=}} \operatorname {E} \left[\prod _{j=1}^{N}X_{j}^{r_{j}}\right]$

where *r*<sub>1</sub> + *r*<sub>2</sub> + ⋯ + *r<sub>N</sub>* = *k*.

The *k*th-order central moments are as follows

1.  If *k* is odd, *μ*<sub>1, ..., *N*</sub>(**x** − ***μ***) = 0.
2.  If *k* is even with *k* = 2*λ*, then<sup>\[*[ambiguous](https://en.wikipedia.org/wiki/Wikipedia:Please_clarify)*\]</sup> 

$$
\mu _{1,\dots ,2\lambda }(\mathbf {x} -{\boldsymbol {\mu }})=\sum \left(\sigma _{ij}\sigma _{k\ell }\cdots \sigma _{XZ}\right)
$$

where the sum is taken over all allocations of the set $\left\{1,\ldots ,2\lambda \right\}$ into *λ* (unordered) pairs. That is, for a *k*th  (= 2*λ* = 6) central moment, one sums the products of *λ* = 3 covariances (the expected value ***μ*** is taken to be 0 in the interests of parsimony):

${\begin{aligned}&\operatorname {E} [X_{1}X_{2}X_{3}X_{4}X_{5}X_{6}]\\[8pt]={}&\operatorname {E} [X_{1}X_{2}]\operatorname {E} [X_{3}X_{4}]\operatorname {E} [X_{5}X_{6}]+\operatorname {E} [X_{1}X_{2}]\operatorname {E} [X_{3}X_{5}]\operatorname {E} [X_{4}X_{6}]+\operatorname {E} [X_{1}X_{2}]\operatorname {E} [X_{3}X_{6}]\operatorname {E} [X_{4}X_{5}]\\[4pt]&{}+\operatorname {E} [X_{1}X_{3}]\operatorname {E} [X_{2}X_{4}]\operatorname {E} [X_{5}X_{6}]+\operatorname {E} [X_{1}X_{3}]\operatorname {E} [X_{2}X_{5}]\operatorname {E} [X_{4}X_{6}]+\operatorname {E} [X_{1}X_{3}]\operatorname {E} [X_{2}X_{6}]\operatorname {E} [X_{4}X_{5}]\\[4pt]&{}+\operatorname {E} [X_{1}X_{4}]\operatorname {E} [X_{2}X_{3}]\operatorname {E} [X_{5}X_{6}]+\operatorname {E} [X_{1}X_{4}]\operatorname {E} [X_{2}X_{5}]\operatorname {E} [X_{3}X_{6}]+\operatorname {E} [X_{1}X_{4}]\operatorname {E} [X_{2}X_{6}]\operatorname {E} [X_{3}X_{5}]\\[4pt]&{}+\operatorname {E} [X_{1}X_{5}]\operatorname {E} [X_{2}X_{3}]\operatorname {E} [X_{4}X_{6}]+\operatorname {E} [X_{1}X_{5}]\operatorname {E} [X_{2}X_{4}]\operatorname {E} [X_{3}X_{6}]+\operatorname {E} [X_{1}X_{5}]\operatorname {E} [X_{2}X_{6}]\operatorname {E} [X_{3}X_{4}]\\[4pt]&{}+\operatorname {E} [X_{1}X_{6}]\operatorname {E} [X_{2}X_{3}]\operatorname {E} [X_{4}X_{5}]+\operatorname {E} [X_{1}X_{6}]\operatorname {E} [X_{2}X_{4}]\operatorname {E} [X_{3}X_{5}]+\operatorname {E} [X_{1}X_{6}]\operatorname {E} [X_{2}X_{5}]\operatorname {E} [X_{3}X_{4}].\end{aligned}}$

This yields ${\tfrac {(2\lambda -1)!}{2^{\lambda -1}(\lambda -1)!}}$ terms in the sum (15 in the above case), each being the product of *λ* (in this case 3) covariances. For fourth order moments (four variables) there are three terms. For sixth-order moments there are 3 × 5 = 15 terms, and for eighth-order moments there are 3 × 5 × 7 = 105 terms.

The covariances are then determined by replacing the terms of the list $[1,\ldots ,2\lambda ]$ by the corresponding terms of the list consisting of *r*<sub>1</sub> ones, then *r*<sub>2</sub> twos, etc.. To illustrate this, examine the following 4th-order central moment case:

${\begin{aligned}\operatorname {E} \left[X_{i}^{4}\right]&=3\sigma _{ii}^{2}\\[4pt]\operatorname {E} \left[X_{i}^{3}X_{j}\right]&=3\sigma _{ii}\sigma _{ij}\\[4pt]\operatorname {E} \left[X_{i}^{2}X_{j}^{2}\right]&=\sigma _{ii}\sigma _{jj}+2\sigma _{ij}^{2}\\[4pt]\operatorname {E} \left[X_{i}^{2}X_{j}X_{k}\right]&=\sigma _{ii}\sigma _{jk}+2\sigma _{ij}\sigma _{ik}\\[4pt]\operatorname {E} \left[X_{i}X_{j}X_{k}X_{n}\right]&=\sigma _{ij}\sigma _{kn}+\sigma _{ik}\sigma _{jn}+\sigma _{in}\sigma _{jk}.\end{aligned}}$

where $\sigma _{ij}$ is the covariance of *X<sub>i</sub>* and *X<sub>j</sub>*. With the above method one first finds the general case for a *k*th moment with *k* different *X* variables, $E\left[X_{i}X_{j}X_{k}X_{n}\right]$, and then one simplifies this accordingly. For example, for $\operatorname {E} [X_{i}^{2}X_{k}X_{n}]$, one lets *X<sub>i</sub>* = *X*<sub>*j*</sub> and one uses the fact that $\sigma _{ii}=\sigma _{i}^{2}$.

### Functions of a normal vector

A [quadratic form](https://en.wikipedia.org/wiki/Quadratic_form) of a normal vector ${\boldsymbol {x}}$, $q({\boldsymbol {x}})={\boldsymbol {x}}'\mathbf {Q_{2}} {\boldsymbol {x}}+{\boldsymbol {q_{1}}}'{\boldsymbol {x}}+q_{0}$ (where $\mathbf {Q_{2}}$ is a matrix, ${\boldsymbol {q_{1}}}$ is a vector, and $q_{0}$ is a scalar), is a [generalized chi-squared](https://en.wikipedia.org/wiki/Generalized_chi-squared_distribution) variable. The direction of a normal vector follows a [projected normal distribution](https://en.wikipedia.org/wiki/Projected_normal_distribution).

If $f({\boldsymbol {x}})$ is a general scalar-valued function of a normal vector, its [[Probability Density Function]], [[Cumulative Distribution Function]], and [inverse cumulative distribution function](https://en.wikipedia.org/wiki/Inverse_cumulative_distribution_function) can be computed with the numerical method of ray-tracing ([Matlab code](https://www.mathworks.com/matlabcentral/fileexchange/84973-integrate-and-classify-normal-distributions)).

#### Likelihood function

If the mean and covariance matrix are known, the log likelihood of an observed vector ${\boldsymbol {x}}$ is simply the log of the [[Probability Density Function]]:

$\ln L({\boldsymbol {x}})=-{\frac {1}{2}}\left[\ln(|{\boldsymbol {\Sigma }}|\,)+({\boldsymbol {x}}-{\boldsymbol {\mu }})'{\boldsymbol {\Sigma }}^{-1}({\boldsymbol {x}}-{\boldsymbol {\mu }})+k\ln(2\pi )\right]$,

The circularly symmetric version of the noncentral complex case, where ${\boldsymbol {z}}$ is a vector of complex numbers, would be

$\ln L({\boldsymbol {z}})=-\ln(|{\boldsymbol {\Sigma }}|\,)-({\boldsymbol {z}}-{\boldsymbol {\mu }})^{\dagger }{\boldsymbol {\Sigma }}^{-1}({\boldsymbol {z}}-{\boldsymbol {\mu }})-k\ln(\pi )$

i.e. with the [conjugate transpose](https://en.wikipedia.org/wiki/Conjugate_transpose) (indicated by $\dagger$) replacing the normal [transpose](https://en.wikipedia.org/wiki/Transpose) (indicated by $'$). This is slightly different than in the real case, because the circularly symmetric version of the [complex normal distribution](https://en.wikipedia.org/wiki/Complex_normal_distribution) has a slightly different form for the [normalization constant](https://en.wikipedia.org/wiki/Normalization_constant).

A similar notation is used for [multiple linear regression](https://en.wikipedia.org/wiki/Multiple_linear_regression).

Since the log likelihood of a normal vector is a [quadratic form](https://en.wikipedia.org/wiki/Quadratic_form) of the normal vector, it is distributed as a [generalized chi-squared](https://en.wikipedia.org/wiki/Generalized_chi-squared_distribution) variable.

### Differential entropy

The [differential entropy](https://en.wikipedia.org/wiki/Differential_entropy) of the multivariate normal distribution is

$$
{\begin{aligned}h\left(f\right)&=-\int _{-\infty }^{\infty }\int _{-\infty }^{\infty }\cdots \int _{-\infty }^{\infty }f(\mathbf {x} )\ln f(\mathbf {x} )\,d\mathbf {x} \\[1ex]&={\frac {1}{2}}\ln \left|2\pi e{\boldsymbol {\Sigma }}\right|={\frac {k}{2}}\left(1+\ln 2\pi \right)+{\frac {1}{2}}\ln \left|{\boldsymbol {\Sigma }}\right|,\end{aligned}}
$$

where the bars denote the [[Determinant|matrix determinant]], *k* is the dimensionality of the vector space, and the result has units of [nats](https://en.wikipedia.org/wiki/Nat_(unit) "Nat (unit)").

### Kullback–Leibler divergence

The [[Kullback-Leibler Divergence|Kullback–Leibler divergence]] from ${\mathcal {N}}_{1}({\boldsymbol {\mu }}_{1},{\boldsymbol {\Sigma }}_{1})$ to ${\mathcal {N}}_{0}({\boldsymbol {\mu }}_{0},{\boldsymbol {\Sigma }}_{0})$, for non-singular matrices Σ<sub>1</sub> and Σ<sub>0</sub>, is:

$D_{\text{KL}}({\mathcal {N}}_{0}\parallel {\mathcal {N}}_{1})={1 \over 2}\left\{\operatorname {tr} \left({\boldsymbol {\Sigma }}_{1}^{-1}{\boldsymbol {\Sigma }}_{0}\right)+\left({\boldsymbol {\mu }}_{1}-{\boldsymbol {\mu }}_{0}\right)^{\rm {T}}{\boldsymbol {\Sigma }}_{1}^{-1}({\boldsymbol {\mu }}_{1}-{\boldsymbol {\mu }}_{0})-k+\ln {|{\boldsymbol {\Sigma }}_{1}| \over |{\boldsymbol {\Sigma }}_{0}|}\right\},$

where $|\cdot |$ denotes the [[Determinant|matrix determinant]], $tr(\cdot )$ is the [trace](https://en.wikipedia.org/wiki/Trace_(linear_algebra) "Trace (linear algebra)"), $\ln(\cdot )$ is the [natural logarithm](https://en.wikipedia.org/wiki/Natural_logarithm) and $k$ is the dimension of the vector space.

The [logarithm](https://en.wikipedia.org/wiki/Logarithm) must be taken to base *[e](https://en.wikipedia.org/wiki/E_(mathematical_constant) "E (mathematical constant)")* since the two terms following the logarithm are themselves base-*e* logarithms of expressions that are either factors of the density function or otherwise arise naturally. The equation therefore gives a result measured in [nats](https://en.wikipedia.org/wiki/Nat_(unit) "Nat (unit)"). Dividing the entire expression above by log<sub>*e*</sub> 2 yields the divergence in [bits](https://en.wikipedia.org/wiki/Bit).

When ${\boldsymbol {\mu }}_{1}={\boldsymbol {\mu }}_{0}$,

$D_{\text{KL}}({\mathcal {N}}_{0}\parallel {\mathcal {N}}_{1})={1 \over 2}\left\{\operatorname {tr} \left({\boldsymbol {\Sigma }}_{1}^{-1}{\boldsymbol {\Sigma }}_{0}\right)-k+\ln {|{\boldsymbol {\Sigma }}_{1}| \over |{\boldsymbol {\Sigma }}_{0}|}\right\}.$

### Mutual information

The [[Mutual Information]] of two multivariate normal distribution is a special case of the [[Kullback-Leibler Divergence|Kullback–Leibler divergence]] in which $P$ is the full $k$ dimensional multivariate distribution and $Q$ is the product of the $k_{1}$ and $k_{2}$ dimensional marginal distributions $X$ and $Y$, such that $k_{1}+k_{2}=k$. The mutual information between $X$ and $Y$ is given by:

$I({\boldsymbol {X}},{\boldsymbol {Y}})={\frac {1}{2}}\ln \left({\frac {\det(\Sigma _{X})\det(\Sigma _{Y})}{\det(\Sigma )}}\right),$

where

$\Sigma ={\begin{bmatrix}\Sigma _{X}&\Sigma _{XY}\\\Sigma _{XY}&\Sigma _{Y}\end{bmatrix}}.$

If $Q$ is product of $k$ one-dimensional normal distributions, then in the notation of the [Kullback–Leibler divergence section](#Kullback–Leibler_divergence) of this article, ${\boldsymbol {\Sigma }}_{1}$ is a [diagonal matrix](https://en.wikipedia.org/wiki/Diagonal_matrix) with the diagonal entries of ${\boldsymbol {\Sigma }}_{0}$, and ${\boldsymbol {\mu }}_{1}={\boldsymbol {\mu }}_{0}$. The resulting formula for mutual information is:

$I({\boldsymbol {X}})=-{1 \over 2}\ln |{\boldsymbol {\rho }}_{0}|,$

where ${\boldsymbol {\rho }}_{0}$ is the [correlation matrix](https://en.wikipedia.org/wiki/Covariance_matrix#Correlation_matrix) constructed from ${\boldsymbol {\Sigma }}_{0}$.

In the bivariate case the expression for the mutual information is:

$I(x;y)=-{1 \over 2}\ln(1-\rho ^{2}).$

### Joint normality

#### Normally distributed and independent

If $X$ and $Y$ are normally distributed and [independent](https://en.wikipedia.org/wiki/Statistical_independence), this implies they are "jointly normally distributed", i.e., the pair $(X,Y)$ must have multivariate normal distribution. However, a pair of jointly normally distributed variables need not be independent (would only be so if uncorrelated, $\rho =0$ ).

#### Two normally distributed random variables need not be jointly bivariate normal

The fact that two random variables $X$ and $Y$ both have a normal distribution does not imply that the pair $(X,Y)$ has a joint normal distribution. A simple example is one in which $X$ has a normal distribution with expected value 0 and variance 1, and $Y=X$ if $|X|>c$ and $Y=-X$ if $|X|<c$, where $c>0$. There are similar counterexamples for more than two random variables. In general, they sum to a [mixture model](https://en.wikipedia.org/wiki/Mixture_model).<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

#### Correlations and independence

In general, random variables may be uncorrelated but statistically dependent. But if a random vector has a multivariate normal distribution then any two or more of its components that are uncorrelated are [independent](https://en.wikipedia.org/wiki/Statistical_independence). This implies that any two or more of its components that are [pairwise independent](https://en.wikipedia.org/wiki/Pairwise_independence) are independent. But, as pointed out just above, it is *not* true that two random variables that are (*separately*, marginally) normally distributed and uncorrelated are independent.

### Conditional distributions

If *N*-dimensional **x** is partitioned as follows

$\mathbf {x} ={\begin{bmatrix}\mathbf {x} _{1}\\\mathbf {x} _{2}\end{bmatrix}}{\text{ with sizes }}{\begin{bmatrix}q\times 1\\(N-q)\times 1\end{bmatrix}}$

and accordingly ***μ*** and **Σ** are partitioned as follows

${\boldsymbol {\mu }}={\begin{bmatrix}{\boldsymbol {\mu }}_{1}\\{\boldsymbol {\mu }}_{2}\end{bmatrix}}{\text{ with sizes }}{\begin{bmatrix}q\times 1\\(N-q)\times 1\end{bmatrix}}$

${\boldsymbol {\Sigma }}={\begin{bmatrix}{\boldsymbol {\Sigma }}_{11}&{\boldsymbol {\Sigma }}_{12}\\{\boldsymbol {\Sigma }}_{21}&{\boldsymbol {\Sigma }}_{22}\end{bmatrix}}{\text{ with sizes }}{\begin{bmatrix}q\times q&q\times (N-q)\\(N-q)\times q&(N-q)\times (N-q)\end{bmatrix}}$

then the distribution of **x**<sub>1</sub> conditional on **x**<sub>2</sub> = **a** is multivariate normal (**x**<sub>1</sub> \| **x**<sub>2</sub> = **a**) ~ *N*(***μ***, **Σ**) where

${\bar {\boldsymbol {\mu }}}={\boldsymbol {\mu }}_{1}+{\boldsymbol {\Sigma }}_{12}{\boldsymbol {\Sigma }}_{22}^{-1}\left(\mathbf {a} -{\boldsymbol {\mu }}_{2}\right)$

and covariance matrix

${\overline {\boldsymbol {\Sigma }}}={\boldsymbol {\Sigma }}_{11}-{\boldsymbol {\Sigma }}_{12}{\boldsymbol {\Sigma }}_{22}^{-1}{\boldsymbol {\Sigma }}_{21}.$

Here ${\boldsymbol {\Sigma }}_{22}^{-1}$ is the [generalized inverse](https://en.wikipedia.org/wiki/Generalized_inverse) of ${\boldsymbol {\Sigma }}_{22}$. The matrix ${\overline {\boldsymbol {\Sigma }}}$ is the [Schur complement](https://en.wikipedia.org/wiki/Schur_complement) of **Σ**<sub>22</sub> in **Σ**. That is, the equation above is equivalent to inverting the overall covariance matrix, dropping the rows and columns corresponding to the variables being conditioned upon, and inverting back to get the conditional covariance matrix.

Note that knowing that **x**<sub>2</sub> = **a** alters the variance, though the new variance does not depend on the specific value of **a**; perhaps more surprisingly, the mean is shifted by ${\boldsymbol {\Sigma }}_{12}{\boldsymbol {\Sigma }}_{22}^{-1}\left(\mathbf {a} -{\boldsymbol {\mu }}_{2}\right)$; compare this with the situation of not knowing the value of **a**, in which case **x**<sub>1</sub> would have distribution ${\mathcal {N}}_{q}\left({\boldsymbol {\mu }}_{1},{\boldsymbol {\Sigma }}_{11}\right)$.

An interesting fact derived in order to prove this result, is that the random vectors $\mathbf {x} _{2}$ and $\mathbf {y} _{1}=\mathbf {x} _{1}-{\boldsymbol {\Sigma }}_{12}{\boldsymbol {\Sigma }}_{22}^{-1}\mathbf {x} _{2}$ are independent.

The matrix **Σ**<sub>12</sub>**Σ**<sub>22</sub><sup>−1</sup> is known as the matrix of [regression](https://en.wikipedia.org/wiki/Regression_analysis) coefficients.

#### Bivariate case

In the bivariate case where **x** is partitioned into $X_{1}$ and $X_{2}$, the conditional distribution of $X_{1}$ given $X_{2}$ is

$X_{1}\mid X_{2}=a\ \sim \ {\mathcal {N}}\left(\mu _{1}+{\frac {\sigma _{1}}{\sigma _{2}}}\rho (a-\mu _{2}),\,(1-\rho ^{2})\sigma _{1}^{2}\right)$

where $\rho ={\frac {\sigma _{12}}{\sigma _{1}\sigma _{2}}}$ is the [correlation coefficient](https://en.wikipedia.org/wiki/Pearson_product-moment_correlation_coefficient) between $X_{1}$ and $X_{2}$.

#### Bivariate conditional expectation

##### In the general case

${\begin{pmatrix}X_{1}\\X_{2}\end{pmatrix}}\sim {\mathcal {N}}\left({\begin{pmatrix}\mu _{1}\\\mu _{2}\end{pmatrix}},{\begin{pmatrix}\sigma _{1}^{2}&\rho \sigma _{1}\sigma _{2}\\\rho \sigma _{1}\sigma _{2}&\sigma _{2}^{2}\end{pmatrix}}\right)$

The conditional expectation of X<sub>1</sub> given X<sub>2</sub> is:

$\operatorname {E} (X_{1}\mid X_{2}=x_{2})=\mu _{1}+\rho {\frac {\sigma _{1}}{\sigma _{2}}}(x_{2}-\mu _{2})$

Proof: the result is obtained by taking the expectation of the conditional distribution $X_{1}\mid X_{2}$ above.

##### In the centered case with unit variances

${\begin{pmatrix}X_{1}\\X_{2}\end{pmatrix}}\sim {\mathcal {N}}\left({\begin{pmatrix}0\\0\end{pmatrix}},{\begin{pmatrix}1&\rho \\\rho &1\end{pmatrix}}\right)$

The conditional expectation of *X*<sub>1</sub> given *X*<sub>2</sub> is

$\operatorname {E} (X_{1}\mid X_{2}=x_{2})=\rho x_{2}$

and the conditional variance is

$\operatorname {var} (X_{1}\mid X_{2}=x_{2})=1-\rho ^{2};$

thus the conditional variance does not depend on *x*<sub>2</sub>.

The conditional expectation of *X*<sub>1</sub> given that *X*<sub>2</sub> is smaller/bigger than *z* is:

$\operatorname {E} (X_{1}\mid X_{2}<z)=-\rho {\varphi (z) \over \Phi (z)},$

$\operatorname {E} (X_{1}\mid X_{2}>z)=\rho {\varphi (z) \over (1-\Phi (z))},$

where the final ratio here is called the [inverse Mills ratio](https://en.wikipedia.org/wiki/Inverse_Mills_ratio).

Proof: the last two results are obtained using the result $\operatorname {E} (X_{1}\mid X_{2}=x_{2})=\rho x_{2}$, so that

$\operatorname {E} (X_{1}\mid X_{2}<z)=\rho E(X_{2}\mid X_{2}<z)$ and then using the properties of the expectation of a [truncated normal distribution](https://en.wikipedia.org/wiki/Truncated_normal_distribution).

### Marginal distributions

To obtain the [marginal distribution](https://en.wikipedia.org/wiki/Marginal_distribution) over a subset of multivariate normal random variables, one only needs to drop the irrelevant variables (the variables that one wants to marginalize out) from the mean vector and the covariance matrix. The proof for this follows from the definitions of multivariate normal distributions and linear algebra.

*Example*

Let **X** = \[*X*<sub>1</sub>, *X*<sub>2</sub>, *X*<sub>3</sub>\] be multivariate normal random variables with mean vector **μ** = \[*μ*<sub>1</sub>, *μ*<sub>2</sub>, *μ*<sub>3</sub>\] and covariance matrix **Σ** (standard parametrization for multivariate normal distributions). Then the joint distribution of **X′** = \[*X*<sub>1</sub>, *X*<sub>3</sub>\] is multivariate normal with mean vector **μ′** = \[*μ*<sub>1</sub>, *μ*<sub>3</sub>\] and covariance matrix ${\boldsymbol {\Sigma }}'={\begin{bmatrix}{\boldsymbol {\Sigma }}_{11}&{\boldsymbol {\Sigma }}_{13}\\{\boldsymbol {\Sigma }}_{31}&{\boldsymbol {\Sigma }}_{33}\end{bmatrix}}$.

### Affine transformation

If **Y** = **c** + **BX** is an [affine transformation](https://en.wikipedia.org/wiki/Affine_transformation) of $\mathbf {X} \ \sim {\mathcal {N}}({\boldsymbol {\mu }},{\boldsymbol {\Sigma }}),$ where **c** is an $M\times 1$ vector of constants and **B** is a constant $M\times N$ matrix, then **Y** has a multivariate normal distribution with expected value **c** + **Bμ** and variance **BΣB**<sup>T</sup> i.e., $\mathbf {Y} \sim {\mathcal {N}}\left(\mathbf {c} +\mathbf {B} {\boldsymbol {\mu }},\mathbf {B} {\boldsymbol {\Sigma }}\mathbf {B} ^{\rm {T}}\right)$. In particular, any subset of the *X<sub>i</sub>* has a marginal distribution that is also multivariate normal. To see this, consider the following example: to extract the subset (*X*<sub>1</sub>, *X*<sub>2</sub>, *X*<sub>4</sub>)<sup>T</sup>, use

$\mathbf {B} ={\begin{bmatrix}1&0&0&0&0&\ldots &0\\0&1&0&0&0&\ldots &0\\0&0&0&1&0&\ldots &0\end{bmatrix}}$

which extracts the desired elements directly.

Another corollary is that the distribution of **Z** = **b** · **X**, where **b** is a constant vector with the same number of elements as **X** and the dot indicates the [dot product](https://en.wikipedia.org/wiki/Dot_product), is univariate Gaussian with $Z\sim {\mathcal {N}}\left(\mathbf {b} \cdot {\boldsymbol {\mu }},\mathbf {b} ^{\rm {T}}{\boldsymbol {\Sigma }}\mathbf {b} \right)$. This result follows by using

$\mathbf {B} ={\begin{bmatrix}b_{1}&b_{2}&\ldots &b_{n}\end{bmatrix}}=\mathbf {b} ^{\rm {T}}.$

Observe how the positive-definiteness of **Σ** implies that the variance of the dot product must be positive.

An affine transformation of **X** such as 2**X** is not the same as the [sum of two independent realisations](https://en.wikipedia.org/wiki/Sum_of_normally_distributed_random_variables) of **X**.

### Geometric interpretation

The equidensity contours of a non-singular multivariate normal distribution are [ellipsoids](https://en.wikipedia.org/wiki/Ellipsoid) (i.e. affine transformations of [hyperspheres](https://en.wikipedia.org/wiki/Hypersphere)) centered at the mean. Hence the multivariate normal distribution is an example of the class of [elliptical distributions](https://en.wikipedia.org/wiki/Elliptical_distribution). The directions of the principal axes of the ellipsoids are given by the eigenvectors of the covariance matrix ${\boldsymbol {\Sigma }}$. The squared relative lengths of the principal axes are given by the corresponding eigenvalues.

If **Σ** = **UΛU**<sup>T</sup> = **UΛ**<sup>1/2</sup>(**UΛ**<sup>1/2</sup>)<sup>T</sup> is an [[Eigendecomposition]] where the columns of **U** are unit eigenvectors and **Λ** is a [diagonal matrix](https://en.wikipedia.org/wiki/Diagonal_matrix) of the eigenvalues, then we have

$\mathbf {X} \ \sim {\mathcal {N}}({\boldsymbol {\mu }},{\boldsymbol {\Sigma }})\iff \mathbf {X} \ \sim {\boldsymbol {\mu }}+\mathbf {U} {\boldsymbol {\Lambda }}^{1/2}{\mathcal {N}}(0,\mathbf {I} )\iff \mathbf {X} \ \sim {\boldsymbol {\mu }}+\mathbf {U} {\mathcal {N}}(0,{\boldsymbol {\Lambda }}).$

Moreover, **U** can be chosen to be a [rotation matrix](https://en.wikipedia.org/wiki/Rotation_matrix), as inverting an axis does not have any effect on *N*(0, **Λ**), but inverting a column changes the sign of **U'**s determinant. The distribution *N*(**μ**, **Σ**) is in effect *N*(0, **I**) scaled by **Λ**<sup>1/2</sup>, rotated by **U** and translated by **μ**.

Conversely, any choice of **μ**, full rank matrix **U**, and positive diagonal entries Λ<sub>*i*</sub> yields a non-singular multivariate normal distribution. If any Λ<sub>*i*</sub> is zero and **U** is square, the resulting covariance matrix **UΛU**<sup>T</sup> is [singular](https://en.wikipedia.org/wiki/Singular_matrix). Geometrically this means that every contour ellipsoid is infinitely thin and has zero volume in *n*-dimensional space, as at least one of the principal axes has length of zero; this is the [degenerate case](https://en.wikipedia.org/wiki/Degenerate_distribution).

"The radius around the true mean in a bivariate normal random variable, re-written in [polar coordinates](https://en.wikipedia.org/wiki/Polar_coordinates) (radius and angle), follows a [Hoyt distribution](https://en.wikipedia.org/wiki/Hoyt_distribution)."

In one dimension the probability of finding a sample of the normal distribution in the interval $\mu \pm \sigma$ is approximately 68.27%, but in higher dimensions the probability of finding a sample in the region of the standard deviation ellipse is lower.

|                |             |
|----------------|-------------|
| Dimensionality | Probability |
| 1              | 0.6827      |
| 2              | 0.3935      |
| 3              | 0.1987      |
| 4              | 0.0902      |
| 5              | 0.0374      |
| 6              | 0.0144      |
| 7              | 0.0052      |
| 8              | 0.0018      |
| 9              | 0.0006      |
| 10             | 0.0002      |

## Statistical inference

### Parameter estimation

The derivation of the [maximum-likelihood](https://en.wikipedia.org/wiki/Maximum_likelihood) [estimator](https://en.wikipedia.org/wiki/Estimator) of the covariance matrix of a multivariate normal distribution is straightforward.

In short, the probability density function (pdf) of a multivariate normal is

$f(\mathbf {x} )={\frac {1}{\sqrt {(2\pi )^{k}|{\boldsymbol {\Sigma }}|}}}\exp \left(-{1 \over 2}(\mathbf {x} -{\boldsymbol {\mu }})^{\rm {T}}{\boldsymbol {\Sigma }}^{-1}({\mathbf {x} }-{\boldsymbol {\mu }})\right)$

and the ML estimator of the covariance matrix from a sample of *n* observations is 

${\widehat {\boldsymbol {\Sigma }}}={1 \over n}\sum _{i=1}^{n}({\mathbf {x} }_{i}-{\overline {\mathbf {x} }})({\mathbf {x} }_{i}-{\overline {\mathbf {x} }})^{\mathrm {T} }$

which is simply the [sample covariance matrix](https://en.wikipedia.org/wiki/Sample_covariance_matrix). This is a [biased estimator](https://en.wikipedia.org/wiki/Biased_estimator) whose expectation is

$E\left[{\widehat {\boldsymbol {\Sigma }}}\right]={\frac {n-1}{n}}{\boldsymbol {\Sigma }}.$

An unbiased sample covariance is

${\widehat {\boldsymbol {\Sigma }}}={\frac {1}{n-1}}\sum _{i=1}^{n}(\mathbf {x} _{i}-{\overline {\mathbf {x} }})(\mathbf {x} _{i}-{\overline {\mathbf {x} }})^{\rm {T}}={\frac {1}{n-1}}\left[X'\left(I-{\frac {1}{n}}\cdot J\right)X\right]$ (matrix form; $I$ is the $K\times K$ identity matrix, J is a $K\times K$ matrix of ones; the term in parentheses is thus the $K\times K$ centering matrix)

The [Fisher information matrix](https://en.wikipedia.org/wiki/Fisher_information_matrix) for estimating the parameters of a multivariate normal distribution has a closed form expression. This can be used, for example, to compute the [Cramér–Rao bound](https://en.wikipedia.org/wiki/Cram%C3%A9r%E2%80%93Rao_bound) for parameter estimation in this setting. See [[Fisher Information]] for more details.

### Bayesian inference

In [Bayesian statistics](https://en.wikipedia.org/wiki/Bayesian_statistics), the [conjugate prior](https://en.wikipedia.org/wiki/Conjugate_prior) of the mean vector is another multivariate normal distribution, and the conjugate prior of the covariance matrix is an [inverse-Wishart distribution](https://en.wikipedia.org/wiki/Inverse-Wishart_distribution) ${\mathcal {W}}^{-1}$ . Suppose then that *n* observations have been made

$\mathbf {X} =\{\mathbf {x} _{1},\dots ,\mathbf {x} _{n}\}\sim {\mathcal {N}}({\boldsymbol {\mu }},{\boldsymbol {\Sigma }})$

and that a conjugate prior has been assigned, where

$p({\boldsymbol {\mu }},{\boldsymbol {\Sigma }})=p({\boldsymbol {\mu }}\mid {\boldsymbol {\Sigma }})\ p({\boldsymbol {\Sigma }}),$

where

$p({\boldsymbol {\mu }}\mid {\boldsymbol {\Sigma }})\sim {\mathcal {N}}({\boldsymbol {\mu }}_{0},m^{-1}{\boldsymbol {\Sigma }}),$

and

$p({\boldsymbol {\Sigma }})\sim {\mathcal {W}}^{-1}({\boldsymbol {\Psi }},n_{0}).$

Then

${\begin{array}{rcl}p({\boldsymbol {\mu }}\mid {\boldsymbol {\Sigma }},\mathbf {X} )&\sim &{\mathcal {N}}\left({\frac {n{\bar {\mathbf {x} }}+m{\boldsymbol {\mu }}_{0}}{n+m}},{\frac {1}{n+m}}{\boldsymbol {\Sigma }}\right),\\p({\boldsymbol {\Sigma }}\mid \mathbf {X} )&\sim &{\mathcal {W}}^{-1}\left({\boldsymbol {\Psi }}+n\mathbf {S} +{\frac {nm}{n+m}}({\bar {\mathbf {x} }}-{\boldsymbol {\mu }}_{0})({\bar {\mathbf {x} }}-{\boldsymbol {\mu }}_{0})',n+n_{0}\right),\end{array}}$

where

${\begin{aligned}{\bar {\mathbf {x} }}&={\frac {1}{n}}\sum _{i=1}^{n}\mathbf {x} _{i},\\\mathbf {S} &={\frac {1}{n}}\sum _{i=1}^{n}(\mathbf {x} _{i}-{\bar {\mathbf {x} }})(\mathbf {x} _{i}-{\bar {\mathbf {x} }})'.\end{aligned}}$

### Multivariate normality tests

Multivariate normality tests check a given set of data for similarity to the multivariate [normal distribution](https://en.wikipedia.org/wiki/Normal_distribution). The [null hypothesis](https://en.wikipedia.org/wiki/Null_hypothesis) is that the [data set](https://en.wikipedia.org/wiki/Data_set) is similar to the normal distribution, therefore a sufficiently small [*p*-value](https://en.wikipedia.org/wiki/P-value) indicates non-normal data. Multivariate normality tests include the Cox–Small test and Smith and Jain's adaptation of the Friedman–Rafsky test created by [Larry Rafsky](https://en.wikipedia.org/wiki/Larry_rafsky) and [Jerome Friedman](https://en.wikipedia.org/wiki/Jerome_H._Friedman).

#### Mardia's test

**Mardia's test** is based on multivariate extensions of [skewness](https://en.wikipedia.org/wiki/Skewness) and [kurtosis](https://en.wikipedia.org/wiki/Kurtosis) measures. For a sample {**x**<sub>1</sub>, ..., **x**<sub>*n*</sub>} of *k*-dimensional vectors we compute

${\begin{aligned}&{\widehat {\boldsymbol {\Sigma }}}={1 \over n}\sum _{j=1}^{n}\left(\mathbf {x} _{j}-{\bar {\mathbf {x} }}\right)\left(\mathbf {x} _{j}-{\bar {\mathbf {x} }}\right)^{\mathrm {T} }\\&A={1 \over 6n}\sum _{i=1}^{n}\sum _{j=1}^{n}\left[(\mathbf {x} _{i}-{\bar {\mathbf {x} }})^{\mathrm {T} }\;{\widehat {\boldsymbol {\Sigma }}}^{-1}(\mathbf {x} _{j}-{\bar {\mathbf {x} }})\right]^{3}\\&B={\sqrt {\frac {n}{8k(k+2)}}}\left\{{1 \over n}\sum _{i=1}^{n}\left[(\mathbf {x} _{i}-{\bar {\mathbf {x} }})^{\mathrm {T} }\;{\widehat {\boldsymbol {\Sigma }}}^{-1}(\mathbf {x} _{i}-{\bar {\mathbf {x} }})\right]^{2}-k(k+2)\right\}\end{aligned}}$

Under the null hypothesis of multivariate normality, the statistic *A* will have approximately a [chi-squared distribution](https://en.wikipedia.org/wiki/Chi-squared_distribution) with 1/6⋅*k*(*k* + 1)(*k* + 2) degrees of freedom, and *B* will be approximately [standard normal](https://en.wikipedia.org/wiki/Standard_normal) *N*(0,1).

Mardia's kurtosis statistic is skewed and converges very slowly to the limiting normal distribution. For medium size samples $(50\leq n<400)$, the parameters of the asymptotic distribution of the kurtosis statistic are modified For small sample tests ($n<50$) empirical critical values are used. Tables of critical values for both statistics are given by Rencher for *k* = 2, 3, 4.

Mardia's tests are affine invariant but not consistent. For example, the multivariate skewness test is not consistent against symmetric non-normal alternatives.

#### BHEP test

The **BHEP test** computes the norm of the difference between the empirical [characteristic function](https://en.wikipedia.org/wiki/Characteristic_function_(probability_theory) "Characteristic function (probability theory)") and the theoretical characteristic function of the normal distribution. Calculation of the norm is performed in the [L<sup>2</sup>(*μ*)](https://en.wikipedia.org/wiki/Lp_space) space of square-integrable functions with respect to the Gaussian weighting function $\mu _{\beta }(\mathbf {t} )=(2\pi \beta ^{2})^{-k/2}e^{-|\mathbf {t} |^{2}/(2\beta ^{2})}$. The test statistic is

${\begin{aligned}T_{\beta }&=\int _{\mathbb {R} ^{k}}\left|{1 \over n}\sum _{j=1}^{n}e^{i\mathbf {t} ^{\mathrm {T} }{\widehat {\boldsymbol {\Sigma }}}^{-1/2}(\mathbf {x} _{j}-{\bar {\mathbf {x} )}}}-e^{-|\mathbf {t} |^{2}/2}\right|^{2}\;{\boldsymbol {\mu }}_{\beta }(\mathbf {t} )\,d\mathbf {t} \\&={1 \over n^{2}}\sum _{i,j=1}^{n}e^{-{\beta ^{2} \over 2}(\mathbf {x} _{i}-\mathbf {x} _{j})^{\mathrm {T} }{\widehat {\boldsymbol {\Sigma }}}^{-1}(\mathbf {x} _{i}-\mathbf {x} _{j})}-{\frac {2}{n(1+\beta ^{2})^{k/2}}}\sum _{i=1}^{n}e^{-{\frac {\beta ^{2}}{2(1+\beta ^{2})}}(\mathbf {x} _{i}-{\bar {\mathbf {x} }})^{\mathrm {T} }{\widehat {\boldsymbol {\Sigma }}}^{-1}(\mathbf {x} _{i}-{\bar {\mathbf {x} }})}+{\frac {1}{(1+2\beta ^{2})^{k/2}}}\end{aligned}}$

The limiting distribution of this test statistic is a weighted sum of chi-squared random variables.

A detailed survey of these and other test procedures is available.

## Computational methods

### Drawing values from the distribution

A widely used method for drawing (sampling) a random vector **x** from the *N*-dimensional multivariate normal distribution with mean vector **μ** and [covariance matrix](https://en.wikipedia.org/wiki/Covariance_matrix) **Σ** works as follows:

1.  Find any real matrix **A** such that **AA**<sup>T</sup> = **Σ**. When **Σ** is positive-definite, the [[Cholesky Decomposition]] is typically used because it is widely available, computationally efficient, and well known. If a rank-revealing (pivoted) Cholesky decomposition such as LAPACK's dpstrf() is available, it can be used in the general positive-semidefinite case as well. A slower general alternative is to use the matrix **A** = **UΛ**<sup>1/2</sup> obtained from a [spectral decomposition](https://en.wikipedia.org/wiki/Eigendecomposition_of_a_matrix#Real_symmetric_matrices) **Σ** = **UΛU**<sup>−1</sup> of **Σ**.
2.  Let **z** = (*z*<sub>1</sub>, ..., *z<sub>N</sub>*)<sup>T</sup> be a vector whose components are *N* [independent](https://en.wikipedia.org/wiki/Statistical_independence) [standard normal](https://en.wikipedia.org/wiki/Normal_distribution) variates (which can be generated, for example, by using the [Box–Muller transform](https://en.wikipedia.org/wiki/Box%E2%80%93Muller_transform)).
3.  Let **x** be **μ** + **Az**. This has the desired distribution due to the affine transformation property.

## See also

- [Chi distribution](https://en.wikipedia.org/wiki/Chi_distribution), the [[Probability Density Function|pdf]] of the [2-norm](https://en.wikipedia.org/wiki/Norm_(mathematics)#p-norm "Norm (mathematics)") ([Euclidean norm](https://en.wikipedia.org/wiki/Euclidean_norm) or [vector length](https://en.wikipedia.org/wiki/Vector_length)) of a multivariate normally distributed vector (uncorrelated and zero centered).
  - [Rayleigh distribution](https://en.wikipedia.org/wiki/Rayleigh_distribution), the pdf of the vector length of a bivariate normally distributed vector (uncorrelated and zero centered)
  - [Rice distribution](https://en.wikipedia.org/wiki/Rice_distribution), the pdf of the vector length of a bivariate normally distributed vector (uncorrelated and non-centered)
  - [Hoyt distribution](https://en.wikipedia.org/wiki/Hoyt_distribution), the pdf of the vector length of a bivariate normally distributed vector (correlated and centered)
- [Complex normal distribution](https://en.wikipedia.org/wiki/Complex_normal_distribution), an application of bivariate normal distribution
- [Copula](https://en.wikipedia.org/wiki/Gaussian_copula), for the definition of the Gaussian or normal copula model.
- [Multivariate t-distribution](https://en.wikipedia.org/wiki/Multivariate_t-distribution), which is another widely used spherically symmetric multivariate distribution.
- [Multivariate stable distribution](https://en.wikipedia.org/wiki/Multivariate_stable_distribution) extension of the multivariate normal distribution, when the index (exponent in the characteristic function) is between zero and two.
- [Mahalanobis distance](https://en.wikipedia.org/wiki/Mahalanobis_distance)
- [Wishart distribution](https://en.wikipedia.org/wiki/Wishart_distribution)
- [Matrix normal distribution](https://en.wikipedia.org/wiki/Matrix_normal_distribution)

## References

1.  ^    Lapidoth, Amos (2009). *A Foundation in Digital Communication*. Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-19395-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-19395-5).
2.  Gut, Allan (2009). *An Intermediate Course in Probability*. Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-441-90161-3](https://en.wikipedia.org/wiki/Special:BookSources/978-1-441-90161-3).
3.  Kac, M. (1939). "On a characterization of the normal distribution". *American Journal of Mathematics*. **61** (3): 726–728. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2371328](https://doi.org/10.2307%2F2371328). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2371328](https://www.jstor.org/stable/2371328).
4.  Sinz, Fabian; Gerwinn, Sebastian; Bethge, Matthias (2009). ["Characterization of the p-generalized normal distribution"](https://doi.org/10.1016%2Fj.jmva.2008.07.006). *Journal of Multivariate Analysis*. **100** (5): 817–820. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.jmva.2008.07.006](https://doi.org/10.1016%2Fj.jmva.2008.07.006).
5.  Simon J.D. Prince(June 2012). [Computer Vision: Models, Learning, and Inference](http://www.computervisionmodels.com/) [Archived](https://web.archive.org/web/20201028120753/http://computervisionmodels.com/) 2020-10-28 at the [Wayback Machine](https://en.wikipedia.org/wiki/Wayback_Machine). Cambridge University Press. 3.7:"Multivariate normal distribution".
6.  Kim, M. G. (2000). "Multivariate outliers and decompositions of Mahalanobis distance". *Communications in Statistics – Theory and Methods*. **29** (7): 1511–1526. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/03610920008832559](https://doi.org/10.1080%2F03610920008832559).
7.  Hamedani, G. G.; Tata, M. N. (1975). "On the determination of the bivariate normal distribution from distributions of linear combinations of the variables". *The American Mathematical Monthly*. **82** (9): 913–915. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2318494](https://doi.org/10.2307%2F2318494). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2318494](https://www.jstor.org/stable/2318494).
8.  Wyatt, John (November 26, 2008). ["Linear least mean-squared error estimation"](https://web.archive.org/web/20151010114443/http://web.mit.edu/6.041/www/LECTURE/lec22.pdf) (PDF). *Lecture notes course on applied probability*. Archived from [the original](http://web.mit.edu/6.041/www/LECTURE/lec22.pdf) (PDF) on October 10, 2015. Retrieved 23 January 2012.
9.  ["linear algebra - Mapping between affine coordinate function"](https://math.stackexchange.com/q/2727720). *Mathematics Stack Exchange*. Retrieved 2022-06-24.
10. [Rao, C. R.](https://en.wikipedia.org/wiki/C._R._Rao) (1973). *Linear Statistical Inference and Its Applications*. New York: Wiley. pp. 527–528. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-70823-2](https://en.wikipedia.org/wiki/Special:BookSources/0-471-70823-2).
11. ^   Botev, Z. I. (2016). "The normal law under linear restrictions: simulation and estimation via minimax tilting". *Journal of the Royal Statistical Society, Series B*. **79**: 125–148. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1603.04166](https://arxiv.org/abs/1603.04166). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2016arXiv160304166B](https://ui.adsabs.harvard.edu/abs/2016arXiv160304166B). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1111/rssb.12162](https://doi.org/10.1111%2Frssb.12162). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [88515228](https://api.semanticscholar.org/CorpusID:88515228).
12. Genz, Alan (2009). [Computation of Multivariate Normal and t Probabilities](https://www.springer.com/statistics/computational+statistics/book/978-3-642-01688-2). Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-642-01689-9](https://en.wikipedia.org/wiki/Special:BookSources/978-3-642-01689-9).
13. ^   [Bensimhoun Michael, N-Dimensional Cumulative Function, And Other Useful Facts About Gaussians and Normal Densities (2006)](https://upload.wikimedia.org/wikipedia/commons/a/a2/Cumulative_function_n_dimensional_Gaussians_12.2013.pdf)
14. Siotani, Minoru (1964). ["Tolerance regions for a multivariate normal population"](http://www.ism.ac.jp/editsec/aism/pdf/016_1_0135.pdf) (PDF). *Annals of the Institute of Statistical Mathematics*. **16** (1): 135–153. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/BF02868568](https://doi.org/10.1007%2FBF02868568). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [123269490](https://api.semanticscholar.org/CorpusID:123269490).
15. ^   Botev, Z. I.; Mandjes, M.; Ridder, A. (6–9 December 2015). "Tail distribution of the maximum of correlated Gaussian random variables". *2015 Winter Simulation Conference (WSC)*. Huntington Beach, Calif., USA: IEEE. pp. 633–642. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/WSC.2015.7408202](https://doi.org/10.1109%2FWSC.2015.7408202). [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[10419/130486](https://hdl.handle.net/10419%2F130486). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4673-9743-8](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4673-9743-8).
16. Adler, R. J.; Blanchet, J.; Liu, J. (7–10 Dec 2008). "Efficient simulation for tail probabilities of Gaussian random fields". *2008 Winter Simulation Conference (WSC)*. Miami, Fla., USA: IEEE. pp. 328–336. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/WSC.2008.4736085](https://doi.org/10.1109%2FWSC.2008.4736085). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4244-2707-9](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4244-2707-9).
17. Hernandez-Stumpfhauser, Daniel; Breidt, F. Jay; van der Woerd, Mark J. (2017). ["The General Projected Normal Distribution of Arbitrary Dimension: Modeling and Bayesian Inference"](https://doi.org/10.1214%2F15-BA989). *Bayesian Analysis*. **12** (1): 113–133. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/15-BA989](https://doi.org/10.1214%2F15-BA989).
18. Tong, T. (2010) [Multiple Linear Regression : MLE and Its Distributional Results](http://amath.colorado.edu/courses/7400/2010Spr/lecture9.pdf) [Archived](https://www.webcitation.org/6HPbX5thy?url=http://amath.colorado.edu/courses/7400/2010Spr/lecture9.pdf) 2013-06-16 at [WebCite](https://en.wikipedia.org/wiki/WebCite), Lecture Notes
19. Gokhale, DV; Ahmed, NA; Res, BC; Piscataway, NJ (May 1989). "Entropy Expressions and Their Estimators for Multivariate Distributions". *IEEE Transactions on Information Theory*. **35** (3): 688–692. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/18.30996](https://doi.org/10.1109%2F18.30996).
20. Duchi, J. [Derivations for Linear Algebra and Optimization](https://web.archive.org/web/20200725234322/http://stanford.edu/~jduchi/projects/general_notes.pdf#page=13) (PDF) (Thesis). p. 13. Archived from [the original](https://stanford.edu/~jduchi/projects/general_notes.pdf#page=13) (PDF) on 2020-07-25. Retrieved 2020-08-12.
21. [Proof: Mutual information of the multivariate normal distribution](https://statproofbook.github.io/P/mvn-mi.html)
22. MacKay, David J. C. (2003-10-06). *Information Theory, Inference and Learning Algorithms* (Illustrated ed.). Cambridge: Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-64298-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-64298-9).
23. Holt, W.; Nguyen, D. (2023). [Essential Aspects of Bayesian Data Imputation](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4494314) (Thesis). [SSRN](https://en.wikipedia.org/wiki/SSRN_(identifier)) [4494314](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4494314).
24. Eaton, Morris L. (1983). *Multivariate Statistics: a Vector Space Approach*. John Wiley and Sons. pp. 116–117. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-02776-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-02776-8).
25. Jensen, J (2000). *Statistics for Petroleum Engineers and Geoscientists*. Amsterdam: Elsevier. p. 207. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-444-50552-0](https://en.wikipedia.org/wiki/Special:BookSources/0-444-50552-0).
26. Maddala, G. S. (1983). *Limited Dependent and Qualitative Variables in Econometrics*. Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-33825-5](https://en.wikipedia.org/wiki/Special:BookSources/0-521-33825-5).
27. An algebraic computation of the marginal distribution is shown here [http://fourier.eng.hmc.edu/e161/lectures/gaussianprocess/node7.html](http://fourier.eng.hmc.edu/e161/lectures/gaussianprocess/node7.html) [Archived](https://web.archive.org/web/20100117200722/http://fourier.eng.hmc.edu/e161/lectures/gaussianprocess/node7.html) 2010-01-17 at the [Wayback Machine](https://en.wikipedia.org/wiki/Wayback_Machine). A much shorter proof is outlined here [https://math.stackexchange.com/a/3832137](https://math.stackexchange.com/a/3832137)
28. Nikolaus Hansen (2016). ["The CMA Evolution Strategy: A Tutorial"](https://web.archive.org/web/20100331114258/http://www.lri.fr/~hansen/cmatutorial.pdf) (PDF). [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1604.00772](https://arxiv.org/abs/1604.00772). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2016arXiv160400772H](https://ui.adsabs.harvard.edu/abs/2016arXiv160400772H). Archived from [the original](http://www.lri.fr/~hansen/cmatutorial.pdf) (PDF) on 2010-03-31. Retrieved 2012-01-07.
29. Daniel Wollschlaeger. ["The Hoyt Distribution (Documentation for R package 'shotGroups' version 0.6.2)"](http://finzi.psych.upenn.edu/usr/share/doc/library/shotGroups/html/hoyt.html).<sup>\[*[permanent dead link](https://en.wikipedia.org/wiki/Wikipedia:Link_rot)*\]</sup>
30. Wang, Bin; Shi, Wenzhong; Miao, Zelang (2015-03-13). Rocchini, Duccio (ed.). ["Confidence Analysis of Standard Deviational Ellipse and Its Extension into Higher Dimensional Euclidean Space"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4358977). *PLOS ONE*. **10** (3) e0118537. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2015PLoSO..1018537W](https://ui.adsabs.harvard.edu/abs/2015PLoSO..1018537W). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1371/journal.pone.0118537](https://doi.org/10.1371%2Fjournal.pone.0118537). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1932-6203](https://search.worldcat.org/issn/1932-6203). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [4358977](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4358977). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [25769048](https://pubmed.ncbi.nlm.nih.gov/25769048).
31. ^   Holt, W.; Nguyen, D. (2023). [Introduction to Bayesian Data Imputation](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4494314) (Thesis). [SSRN](https://en.wikipedia.org/wiki/SSRN_(identifier)) [4494314](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4494314).
32. Cox, D. R.; Small, N. J. H. (1978). "Testing multivariate normality". *Biometrika*. **65** (2): 263. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1093/biomet/65.2.263](https://doi.org/10.1093%2Fbiomet%2F65.2.263).
33. Smith, S. P.; Jain, A. K. (1988). "A test to determine the multivariate normality of a data set". *IEEE Transactions on Pattern Analysis and Machine Intelligence*. **10** (5): 757. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/34.6789](https://doi.org/10.1109%2F34.6789).
34. Friedman, J. H.; Rafsky, L. C. (1979). ["Multivariate Generalizations of the Wald–Wolfowitz and Smirnov Two-Sample Tests"](https://doi.org/10.1214%2Faos%2F1176344722). *The Annals of Statistics*. **7** (4): 697. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/aos/1176344722](https://doi.org/10.1214%2Faos%2F1176344722).
35. Mardia, K. V. (1970). "Measures of multivariate skewness and kurtosis with applications". *Biometrika*. **57** (3): 519–530. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1093/biomet/57.3.519](https://doi.org/10.1093%2Fbiomet%2F57.3.519).
36. Rencher (1995), pages 112–113.
37. Rencher (1995), pages 493–495.
38. Baringhaus, L.; Henze, N. (1991). ["Limit distributions for measures of multivariate skewness and kurtosis based on projections"](https://doi.org/10.1016%2F0047-259X%2891%2990031-V). *Journal of Multivariate Analysis*. **38**: 51–69. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/0047-259X(91)90031-V](https://doi.org/10.1016%2F0047-259X%2891%2990031-V).
39. ^   Baringhaus, L.; Henze, N. (1988). "A consistent test for multivariate normality based on the empirical characteristic function". *Metrika*. **35** (1): 339–348. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/BF02613322](https://doi.org/10.1007%2FBF02613322). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [122362448](https://api.semanticscholar.org/CorpusID:122362448).
40. Henze, Norbert (2002). "Invariant tests for multivariate normality: a critical review". *Statistical Papers*. **43** (4): 467–506. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s00362-002-0119-6](https://doi.org/10.1007%2Fs00362-002-0119-6). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [122934510](https://api.semanticscholar.org/CorpusID:122934510).
41. Gentle, J. E. (2009). [Computational Statistics](https://cds.cern.ch/record/1639470). Statistics and Computing. New York: Springer. pp. 315–316. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-0-387-98144-4](https://doi.org/10.1007%2F978-0-387-98144-4). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-98143-7](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-98143-7).

### Literature

- Rencher, A.C. (1995). *Methods of Multivariate Analysis*. New York: Wiley.
- Tong, Y. L. (1990). *The multivariate normal distribution*. Springer Series in Statistics. New York: Springer-Verlag. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-1-4613-9655-0](https://doi.org/10.1007%2F978-1-4613-9655-0). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4613-9657-4](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4613-9657-4). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [120348131](https://api.semanticscholar.org/CorpusID:120348131).
