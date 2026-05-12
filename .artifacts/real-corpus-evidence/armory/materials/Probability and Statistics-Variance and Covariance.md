[[probability-statistics.base]]

> Source: [Covariance matrix](https://en.wikipedia.org/wiki/Covariance_matrix)
> License: Wikipedia content is available under CC BY-SA 4.0.

![[media/13f6b0440059995320f1ecb0425b66da06fc6c09.png]]
A [bivariate Gaussian probability density function](https://en.wikipedia.org/wiki/Bivariate_Gaussian_distribution) centered at (0, 0), with covariance matrix given by ${\begin{bmatrix}1&0.5\\0.5&1\end{bmatrix}}$

![[media/08da5af60a802a8d2d0f2d36f901e45e34e1a118.png]]
Sample points from a [bivariate Gaussian distribution](https://en.wikipedia.org/wiki/Bivariate_Gaussian_distribution) with a standard deviation of 3 in roughly the lower left–upper right direction and of 1 in the orthogonal direction. Because the <em>x</em> and <em>y</em> components co-vary, the variances of $x$ and $y$ do not fully describe the distribution. A $2\times 2$ covariance matrix is needed; the directions of the arrows correspond to the [eigenvectors](https://en.wikipedia.org/wiki/Eigenvector) of this covariance matrix and their lengths to the square roots of the [eigenvalues](https://en.wikipedia.org/wiki/Eigenvalues).

In [probability theory](https://en.wikipedia.org/wiki/Probability_theory) and [statistics](https://en.wikipedia.org/wiki/Statistics), a **covariance matrix** (also known as **auto-covariance matrix**, **dispersion matrix**, **variance matrix**, or **variance–covariance matrix**) is a square [matrix](https://en.wikipedia.org/wiki/Matrix_(mathematics) "Matrix (mathematics)") giving the [covariance](https://en.wikipedia.org/wiki/Covariance) between each pair of elements of a given [random vector](https://en.wikipedia.org/wiki/Random_vector).

Intuitively, the covariance matrix generalizes the notion of variance to multiple dimensions. As an example, the variation in a collection of random points in two-dimensional space cannot be characterized fully by a single number, nor would the variances in the $x$ and $y$ directions contain all of the necessary information; a $2\times 2$ matrix would be necessary to fully characterize the two-dimensional variation.

Any [covariance](https://en.wikipedia.org/wiki/Covariance) matrix is [symmetric](https://en.wikipedia.org/wiki/Symmetric_matrix) and [positive semi-definite](https://en.wikipedia.org/wiki/Positive_semi-definite_matrix) and its main diagonal contains [variances](https://en.wikipedia.org/wiki/Variance) (i.e., the covariance of each element with itself).

The covariance matrix of a random vector $\mathbf {X}$ is typically denoted by $\operatorname {K} _{\mathbf {X} \mathbf {X} }$, $\Sigma$ or $S$.

## Definition

Throughout this article, boldfaced unsubscripted $\mathbf {X}$ and $\mathbf {Y}$ are used to refer to random vectors, and Roman subscripted $X_{i}$ and $Y_{i}$ are used to refer to scalar random variables.

If the entries in the [column vector](https://en.wikipedia.org/wiki/Column_vector) 

$$
\mathbf {X} =(X_{1},X_{2},\dots ,X_{n})^{\mathsf {T}}
$$

 are [random variables](https://en.wikipedia.org/wiki/Random_variable), each with finite [variance](https://en.wikipedia.org/wiki/Variance) and [expected value](https://en.wikipedia.org/wiki/Expected_value), then the covariance matrix $\operatorname {K} _{\mathbf {X} \mathbf {X} }$ is the matrix whose $(i,j)$ entry is the [covariance](https://en.wikipedia.org/wiki/Covariance) 

$$
\operatorname {K} _{X_{i}X_{j}}=\operatorname {cov} [X_{i},X_{j}]=\operatorname {E} [(X_{i}-\operatorname {E} [X_{i}])(X_{j}-\operatorname {E} [X_{j}])]
$$

 where the operator $\operatorname {E}$ denotes the expected value (mean) of its argument.

### Conflicting nomenclatures and notations

Nomenclatures differ. Some statisticians, following the probabilist [William Feller](https://en.wikipedia.org/wiki/William_Feller) in his two-volume book *An Introduction to Probability Theory and Its Applications*, call the matrix $\operatorname {K} _{\mathbf {X} \mathbf {X} }$ the **variance** of the random vector $\mathbf {X}$, because it is the natural generalization to higher dimensions of the 1-dimensional variance. Others call it the **covariance matrix**, because it is the matrix of covariances between the scalar components of the vector $\mathbf {X}$. 

$$
\operatorname {var} (\mathbf {X} )=\operatorname {cov} (\mathbf {X} ,\mathbf {X} )=\operatorname {E} \left[(\mathbf {X} -\operatorname {E} [\mathbf {X} ])(\mathbf {X} -\operatorname {E} [\mathbf {X} ])^{\mathsf {T}}\right].
$$

Both forms are quite standard, and there is no ambiguity between them. The matrix $\operatorname {K} _{\mathbf {X} \mathbf {X} }$ is also often called the **variance-covariance matrix**, since the diagonal terms are in fact variances.

By comparison, the notation for the [cross-covariance matrix](https://en.wikipedia.org/wiki/Cross-covariance_matrix) *between* two vectors is 

$$
\operatorname {cov} (\mathbf {X} ,\mathbf {Y} )=\operatorname {K} _{\mathbf {X} \mathbf {Y} }=\operatorname {E} \left[(\mathbf {X} -\operatorname {E} [\mathbf {X} ])(\mathbf {Y} -\operatorname {E} [\mathbf {Y} ])^{\mathsf {T}}\right].
$$

## Properties

### Relation to the autocorrelation matrix

The auto-covariance matrix $\operatorname {K} _{\mathbf {X} \mathbf {X} }$ is related to the [autocorrelation matrix](https://en.wikipedia.org/wiki/Autocorrelation_matrix) $\operatorname {R} _{\mathbf {X} \mathbf {X} }$ by 

$$
\operatorname {K} _{\mathbf {X} \mathbf {X} }=\operatorname {E} [(\mathbf {X} -\operatorname {E} [\mathbf {X} ])(\mathbf {X} -\operatorname {E} [\mathbf {X} ])^{\mathsf {T}}]=\operatorname {R} _{\mathbf {X} \mathbf {X} }-\operatorname {E} [\mathbf {X} ]\operatorname {E} [\mathbf {X} ]^{\mathsf {T}}
$$

 where the autocorrelation matrix is defined as $\operatorname {R} _{\mathbf {X} \mathbf {X} }=\operatorname {E} [\mathbf {X} \mathbf {X} ^{\mathsf {T}}]$.

### Relation to the correlation matrix

An entity closely related to the covariance matrix is the matrix of [Pearson product-moment correlation coefficients](https://en.wikipedia.org/wiki/Pearson_product-moment_correlation_coefficient) between each of the random variables in the random vector $\mathbf {X}$, which can be written as 

$$
\operatorname {corr} (\mathbf {X} )={\big (}\operatorname {diag} (\operatorname {K} _{\mathbf {X} \mathbf {X} }){\big )}^{-{\frac {1}{2}}}\,\operatorname {K} _{\mathbf {X} \mathbf {X} }\,{\big (}\operatorname {diag} (\operatorname {K} _{\mathbf {X} \mathbf {X} }){\big )}^{-{\frac {1}{2}}},
$$

 where $\operatorname {diag} (\operatorname {K} _{\mathbf {X} \mathbf {X} })$ is the matrix of the diagonal elements of $\operatorname {K} _{\mathbf {X} \mathbf {X} }$ (i.e., a [diagonal matrix](https://en.wikipedia.org/wiki/Diagonal_matrix) of the variances of $X_{i}$ for $i=1,\dots ,n$).

Equivalently, the correlation matrix can be seen as the covariance matrix of the [standardized random variables](https://en.wikipedia.org/wiki/Standardized_variable) $X_{i}/\sigma (X_{i})$ for $i=1,\dots ,n$. 

$$
\operatorname {corr} (\mathbf {X} )={\begin{bmatrix}1&{\frac {\operatorname {E} [(X_{1}-\mu _{1})(X_{2}-\mu _{2})]}{\sigma (X_{1})\sigma (X_{2})}}&\cdots &{\frac {\operatorname {E} [(X_{1}-\mu _{1})(X_{n}-\mu _{n})]}{\sigma (X_{1})\sigma (X_{n})}}\\\\{\frac {\operatorname {E} [(X_{2}-\mu _{2})(X_{1}-\mu _{1})]}{\sigma (X_{2})\sigma (X_{1})}}&1&\cdots &{\frac {\operatorname {E} [(X_{2}-\mu _{2})(X_{n}-\mu _{n})]}{\sigma (X_{2})\sigma (X_{n})}}\\\\\vdots &\vdots &\ddots &\vdots \\\\{\frac {\operatorname {E} [(X_{n}-\mu _{n})(X_{1}-\mu _{1})]}{\sigma (X_{n})\sigma (X_{1})}}&{\frac {\operatorname {E} [(X_{n}-\mu _{n})(X_{2}-\mu _{2})]}{\sigma (X_{n})\sigma (X_{2})}}&\cdots &1\end{bmatrix}}.
$$

Each element on the principal diagonal of a correlation matrix is the correlation of a random variable with itself, which always equals 1. Each [off-diagonal element](https://en.wikipedia.org/wiki/Off-diagonal_element) is between −1 and +1 inclusive.

### Inverse of the covariance matrix

The [inverse of this matrix](https://en.wikipedia.org/wiki/Invertible_matrix), $\operatorname {K} _{\mathbf {X} \mathbf {X} }^{-1}$, if it exists, is the inverse covariance matrix (or inverse concentration matrix<sup>\[*[dubious](https://en.wikipedia.org/wiki/Wikipedia:Accuracy_dispute#Disputed_statement) – [discuss](https://en.wikipedia.org/wiki/Talk:Covariance_matrix#Dubious)*\]</sup>), also known as the *[precision matrix](https://en.wikipedia.org/wiki/Precision_matrix)* (or *concentration matrix*).

Just as the covariance matrix can be written as the rescaling of a correlation matrix by the marginal variances: 

$$
\operatorname {cov} (\mathbf {X} )={\begin{bmatrix}\sigma _{x_{1}}&&&0\\&\sigma _{x_{2}}&&\\&&\ddots &\\0&&&\sigma _{x_{n}}\end{bmatrix}}
$$

$$
\times {\begin{bmatrix}1&\rho _{x_{1},x_{2}}&\cdots &\rho _{x_{1},x_{n}}\\\rho _{x_{2},x_{1}}&1&\cdots &\rho _{x_{2},x_{n}}\\\vdots &\vdots &\ddots &\vdots \\\rho _{x_{n},x_{1}}&\rho _{x_{n},x_{2}}&\cdots &1\end{bmatrix}}
$$

$$
\times {\begin{bmatrix}\sigma _{x_{1}}&&&0\\&\sigma _{x_{2}}&&\\&&\ddots &\\0&&&\sigma _{x_{n}}\end{bmatrix}}
$$

So, using the idea of [partial correlation](https://en.wikipedia.org/wiki/Partial_correlation), and partial variance, the inverse covariance matrix can be expressed analogously: 

$$
\operatorname {cov} (\mathbf {X} )^{-1}={\begin{bmatrix}{\frac {1}{\sigma _{x_{1}\mid x_{2}\dots }}}&&&0\\&{\frac {1}{\sigma _{x_{2}\mid x_{1},x_{3}\dots }}}\\&&\ddots \\0&&&{\frac {1}{\sigma _{x_{n}\mid x_{1}\dots x_{n-1}}}}\end{bmatrix}}
$$

$$
\times {\begin{bmatrix}1&-\rho _{x_{1},x_{2}\mid x_{3}\dots }&\cdots &-\rho _{x_{1},x_{n}\mid x_{2}\dots x_{n-1}}\\-\rho _{x_{2},x_{1}\mid x_{3}\dots }&1&\cdots &-\rho _{x_{2},x_{n}\mid x_{1},x_{3}\dots x_{n-1}}\\\vdots &\vdots &\ddots &\vdots \\-\rho _{x_{n},x_{1}\mid x_{2}\dots x_{n-1}}&-\rho _{x_{n},x_{2}\mid x_{1},x_{3}\dots x_{n-1}}&\cdots &1\end{bmatrix}}
$$

$$
\times {\begin{bmatrix}{\frac {1}{\sigma _{x_{1}\mid x_{2}\dots }}}&&&0\\&{\frac {1}{\sigma _{x_{2}\mid x_{1},x_{3}\dots }}}\\&&\ddots \\0&&&{\frac {1}{\sigma _{x_{n}\mid x_{1}\dots x_{n-1}}}}\end{bmatrix}}
$$

This duality motivates a number of other dualities between marginalizing and conditioning for Gaussian random variables.

### Basic properties

For $\operatorname {K} _{\mathbf {X} \mathbf {X} }=\operatorname {var} (\mathbf {X} )=\operatorname {E} \left[\left(\mathbf {X} -\operatorname {E} [\mathbf {X} ]\right)\left(\mathbf {X} -\operatorname {E} [\mathbf {X} ]\right)^{\mathsf {T}}\right]$ and ${\boldsymbol {\mu }}_{\mathbf {X} }=\operatorname {E} [{\textbf {X}}]$, where $\mathbf {X} =(X_{1},\ldots ,X_{n})^{\mathsf {T}}$ is an $n$-dimensional random variable, the following basic properties apply:

1.  $\operatorname {K} _{\mathbf {X} \mathbf {X} }=\operatorname {E} (\mathbf {XX^{\mathsf {T}}} )-{\boldsymbol {\mu }}_{\mathbf {X} }{\boldsymbol {\mu }}_{\mathbf {X} }^{\mathsf {T}}$
2.  $\operatorname {K} _{\mathbf {X} \mathbf {X} }\,$ is [positive-semidefinite](https://en.wikipedia.org/wiki/Positive-semidefinite_matrix), i.e. $\mathbf {a} ^{T}\operatorname {K} _{\mathbf {X} \mathbf {X} }\mathbf {a} \geq 0\quad {\text{for all }}\mathbf {a} \in \mathbb {R} ^{n}$

*Proof*

Indeed, from the property 4 it follows that under linear transformation of random variable $\mathbf {X}$ with covariation matrix $\mathbf {\Sigma _{X}} =\mathrm {cov} (\mathbf {X} )$ by linear operator $\mathbf {A}$ s.a. $\mathbf {Y} =\mathbf {A} \mathbf {X}$, the covariation matrix is transformed as

$\mathbf {\Sigma _{Y}} =\mathrm {cov} \left(\mathbf {Y} \right)=\mathbf {A\,\Sigma _{X}\,A} ^{\top }$.

As according to the property 3 matrix $\mathbf {\Sigma _{X}}$ is symmetric, it can be diagonalized by a linear orthogonal transformation, i.e. there exists such orthogonal matrix $\mathbf {A}$ (meanwhile $\mathbf {A} ^{\top }=\mathbf {A} ^{-1}$), that

$\mathbf {A\,\Sigma _{X}\,A} ^{\top }=\mathbf {A\,\Sigma _{X}\,A} ^{-1}={\mbox{diag}}(\sigma _{1},\ldots ,\sigma _{n}),$

and $\sigma _{1},\ldots ,\sigma _{n}$ are eigenvalues of $\mathbf {\Sigma _{X}}$. But this means that this matrix is a covariation matrix for a random variable $\mathbf {Y} =\mathbf {A} \mathbf {X}$, and the main diagonal of $\mathbf {\Sigma _{Y}} =\mathrm {cov} \left(\mathbf {Y} \right)$ consists of variances of elements of $\mathbf {Y}$ vector. As variance is always non-negative, we conclude that $\sigma _{i}\geq 0$ for any $i$. But this means that matrix $\mathbf {\Sigma _{X}}$ is positive-semidefinite.

1.  
2.  $\operatorname {K} _{\mathbf {X} \mathbf {X} }\,$ is [symmetric](https://en.wikipedia.org/wiki/Symmetric_matrix), i.e. $\operatorname {K} _{\mathbf {X} \mathbf {X} }^{\mathsf {T}}=\operatorname {K} _{\mathbf {X} \mathbf {X} }$
3.  For any constant (i.e. non-random) $m\times n$ matrix $\mathbf {A}$ and constant $m\times 1$ vector $\mathbf {a}$, one has $\operatorname {var} (\mathbf {AX} +\mathbf {a} )=\mathbf {A} \,\operatorname {var} (\mathbf {X} )\,\mathbf {A} ^{\mathsf {T}}$
4.  If $\mathbf {Y}$ is another random vector with the same dimension as $\mathbf {X}$, then $\operatorname {var} (\mathbf {X} +\mathbf {Y} )=\operatorname {var} (\mathbf {X} )+\operatorname {cov} (\mathbf {X} ,\mathbf {Y} )+\operatorname {cov} (\mathbf {Y} ,\mathbf {X} )+\operatorname {var} (\mathbf {Y} )$ where $\operatorname {cov} (\mathbf {X} ,\mathbf {Y} )$ is the [cross-covariance matrix](https://en.wikipedia.org/wiki/Cross-covariance_matrix) of $\mathbf {X}$ and $\mathbf {Y}$.

### Block matrices

The joint mean ${\boldsymbol {\mu }}$ and [joint covariance matrix](https://en.wikipedia.org/wiki/Cross-covariance_matrix) ${\boldsymbol {\Sigma }}$ of $\mathbf {X}$ and $\mathbf {Y}$ can be written in block form 

$$
{\boldsymbol {\mu }}={\begin{bmatrix}{\boldsymbol {\mu }}_{X}\\{\boldsymbol {\mu }}_{Y}\end{bmatrix}},\qquad {\boldsymbol {\Sigma }}={\begin{bmatrix}\operatorname {K} _{\mathbf {XX} }&\operatorname {K} _{\mathbf {XY} }\\\operatorname {K} _{\mathbf {YX} }&\operatorname {K} _{\mathbf {YY} }\end{bmatrix}}
$$

 where $\operatorname {K} _{\mathbf {XX} }=\operatorname {var} (\mathbf {X} )$, $\operatorname {K} _{\mathbf {YY} }=\operatorname {var} (\mathbf {Y} )$ and $\operatorname {K} _{\mathbf {XY} }=\operatorname {K} _{\mathbf {YX} }^{\mathsf {T}}=\operatorname {cov} (\mathbf {X} ,\mathbf {Y} )$.

$\operatorname {K} _{\mathbf {XX} }$ and $\operatorname {K} _{\mathbf {YY} }$ can be identified as the variance matrices of the [marginal distributions](https://en.wikipedia.org/wiki/Marginal_distribution) for $\mathbf {X}$ and $\mathbf {Y}$ respectively.

If $\mathbf {X}$ and $\mathbf {Y}$ are [[Multivariate Normal Distribution|jointly normally distributed]], 

$$
\mathbf {X} ,\mathbf {Y} \sim \ {\mathcal {N}}({\boldsymbol {\mu }},\operatorname {\boldsymbol {\Sigma }} ),
$$

 then the [conditional distribution](https://en.wikipedia.org/wiki/Conditional_distribution) for $\mathbf {Y}$ given $\mathbf {X}$ is given by 

$$
\mathbf {Y} \mid \mathbf {X} \sim \ {\mathcal {N}}({\boldsymbol {\mu }}_{\mathbf {Y|X} },\operatorname {K} _{\mathbf {Y|X} }),
$$

 defined by [conditional mean](https://en.wikipedia.org/wiki/Conditional_mean) 

$$
{\boldsymbol {\mu }}_{\mathbf {Y} |\mathbf {X} }={\boldsymbol {\mu }}_{\mathbf {Y} }+\operatorname {K} _{\mathbf {YX} }\operatorname {K} _{\mathbf {XX} }^{-1}\left(\mathbf {X} -{\boldsymbol {\mu }}_{\mathbf {X} }\right)
$$

 and [conditional variance](https://en.wikipedia.org/wiki/Conditional_variance) 

$$
\operatorname {K} _{\mathbf {Y|X} }=\operatorname {K} _{\mathbf {YY} }-\operatorname {K} _{\mathbf {YX} }\operatorname {K} _{\mathbf {XX} }^{-1}\operatorname {K} _{\mathbf {XY} }.
$$

The matrix $\operatorname {K} _{\mathbf {YX} }\operatorname {K} _{\mathbf {XX} }^{-1}$ is known as the matrix of [regression](https://en.wikipedia.org/wiki/Regression_analysis) coefficients, while in linear algebra $\operatorname {K} _{\mathbf {Y|X} }$ is the [Schur complement](https://en.wikipedia.org/wiki/Schur_complement) of $\operatorname {K} _{\mathbf {XX} }$ in ${\boldsymbol {\Sigma }}$.

The matrix of regression coefficients may often be given in transpose form, $\operatorname {K} _{\mathbf {XX} }^{-1}\operatorname {K} _{\mathbf {XY} }$, suitable for post-multiplying a row vector of explanatory variables $\mathbf {X} ^{\mathsf {T}}$ rather than pre-multiplying a column vector $\mathbf {X}$. In this form they correspond to the coefficients obtained by inverting the matrix of the [normal equations](https://en.wikipedia.org/wiki/Normal_equations) of [ordinary least squares](https://en.wikipedia.org/wiki/Ordinary_least_squares) (OLS).

## Partial covariance matrix

A covariance matrix with all non-zero elements tells us that all the individual random variables are interrelated. This means that the variables are not only directly correlated, but also correlated via other variables indirectly. Often such indirect, [common-mode](https://en.wikipedia.org/wiki/Common-mode_interference) correlations are trivial and uninteresting. They can be suppressed by calculating the partial covariance matrix, that is the part of covariance matrix that shows only the interesting part of correlations.

If two vectors of random variables $\mathbf {X}$ and $\mathbf {Y}$ are correlated via another vector $\mathbf {I}$, the latter correlations are suppressed in a matrix 

$$
\operatorname {K} _{\mathbf {XY\mid I} }=\operatorname {pcov} (\mathbf {X} ,\mathbf {Y} \mid \mathbf {I} )=\operatorname {cov} (\mathbf {X} ,\mathbf {Y} )-\operatorname {cov} (\mathbf {X} ,\mathbf {I} )\operatorname {cov} (\mathbf {I} ,\mathbf {I} )^{-1}\operatorname {cov} (\mathbf {I} ,\mathbf {Y} ).
$$

 The partial covariance matrix $\operatorname {K} _{\mathbf {XY\mid I} }$ is effectively the simple covariance matrix $\operatorname {K} _{\mathbf {XY} }$ as if the uninteresting random variables $\mathbf {I}$ were held constant.

## Standard deviation matrix

The standard deviation matrix $\mathbf {S}$ is the extension of the standard deviation to multiple dimensions. It is the symmetric [square root](https://en.wikipedia.org/wiki/Square_root_of_a_matrix) of the covariance matrix $\mathbf {\Sigma }$.

## Covariance matrix as a parameter of a distribution

If a column vector $\mathbf {X}$ of $n$ possibly correlated random variables is [[Multivariate Normal Distribution|jointly normally distributed]], or more generally [elliptically distributed](https://en.wikipedia.org/wiki/Elliptical_distribution), then its [[Probability Density Function]] $\operatorname {f} (\mathbf {X} )$ can be expressed in terms of the covariance matrix ${\boldsymbol {\Sigma }}$ as follows 

$$
\operatorname {f} (\mathbf {X} )=(2\pi )^{-n/2}|{\boldsymbol {\Sigma }}|^{-1/2}\exp \left(-{\tfrac {1}{2}}\mathbf {(X-\mu )^{\mathsf {T}}\Sigma ^{-1}(X-\mu )} \right),
$$

 where ${\boldsymbol {\mu }}=\operatorname {E} [\mathbf {X} ]$ and $|{\boldsymbol {\Sigma }}|$ is the [[Determinant]] of ${\boldsymbol {\Sigma }}$, the so-called *[generalized variance](https://en.wikipedia.org/wiki/Generalized_variance)*.

## Covariance matrix as a linear operator

Applied to one vector, the covariance matrix maps a linear combination **c** of the random variables **X** onto a vector of covariances with those variables: $\mathbf {c} ^{\mathsf {T}}\Sigma =\operatorname {cov} (\mathbf {c} ^{\mathsf {T}}\mathbf {X} ,\mathbf {X} )$. Treated as a [bilinear form](https://en.wikipedia.org/wiki/Bilinear_form), it yields the covariance between the two linear combinations: $\mathbf {d} ^{\mathsf {T}}{\boldsymbol {\Sigma }}\mathbf {c} =\operatorname {cov} (\mathbf {d} ^{\mathsf {T}}\mathbf {X} ,\mathbf {c} ^{\mathsf {T}}\mathbf {X} )$. The variance of a linear combination is then $\mathbf {c} ^{\mathsf {T}}{\boldsymbol {\Sigma }}\mathbf {c}$, its covariance with itself.

Similarly, the (pseudo-)inverse covariance matrix provides an inner product $\langle c-\mu |\Sigma ^{+}|c-\mu \rangle$, which induces the [Mahalanobis distance](https://en.wikipedia.org/wiki/Mahalanobis_distance), a measure of the "unlikelihood" of *c*.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

## Admissibility

From basic property 4. above, let $\mathbf {b}$ be a $(p\times 1)$ real-valued vector, then 

$$
\operatorname {var} (\mathbf {b} ^{\mathsf {T}}\mathbf {X} )=\mathbf {b} ^{\mathsf {T}}\operatorname {var} (\mathbf {X} )\mathbf {b} ,\,
$$

 which must always be nonnegative, since it is the [variance](https://en.wikipedia.org/wiki/Variance#Properties) of a real-valued random variable, so a covariance matrix is always a [positive-semidefinite matrix](https://en.wikipedia.org/wiki/Positive-semidefinite_matrix).

The above argument can be expanded as follows:

$$
{\begin{aligned}&w^{\mathsf {T}}\operatorname {E} \left[(\mathbf {X} -\operatorname {E} [\mathbf {X} ])(\mathbf {X} -\operatorname {E} [\mathbf {X} ])^{\mathsf {T}}\right]w=\operatorname {E} \left[w^{\mathsf {T}}(\mathbf {X} -\operatorname {E} [\mathbf {X} ])(\mathbf {X} -\operatorname {E} [\mathbf {X} ])^{\mathsf {T}}w\right]\\&=\operatorname {E} {\big [}{\big (}w^{\mathsf {T}}(\mathbf {X} -\operatorname {E} [\mathbf {X} ]){\big )}^{2}{\big ]}\geq 0,\end{aligned}}
$$

where the last inequality follows from the observation that $w^{\mathsf {T}}(\mathbf {X} -\operatorname {E} [\mathbf {X} ])$ is a scalar.

Conversely, every symmetric positive semi-definite matrix is a covariance matrix. To see this, suppose $M$ is a $p\times p$ symmetric positive-semidefinite matrix. From the finite-dimensional case of the [[Spectral Theorem]], it follows that $M$ has a nonnegative symmetric [square root](https://en.wikipedia.org/wiki/Square_root_of_a_matrix), which can be denoted by **M**<sup>1/2</sup>. Let $\mathbf {X}$ be any $p\times 1$ column vector-valued random variable whose covariance matrix is the $p\times p$ identity matrix. Then 

$$
\operatorname {var} (\mathbf {M} ^{1/2}\mathbf {X} )=\mathbf {M} ^{1/2}\,\operatorname {var} (\mathbf {X} )\,\mathbf {M} ^{1/2}=\mathbf {M} .
$$

## Complex random vectors

The [variance](https://en.wikipedia.org/wiki/Variance#Generalizations) of a [complex](https://en.wikipedia.org/wiki/Complex_number) *scalar-valued* random variable with expected value $\mu$ is conventionally defined using [complex conjugation](https://en.wikipedia.org/wiki/Complex_conjugation): 

$$
\operatorname {var} (Z)=\operatorname {E} \left[(Z-\mu _{Z}){\overline {(Z-\mu _{Z})}}\right],
$$

 where the complex conjugate of a complex number $z$ is denoted ${\overline {z}}$; thus the variance of a complex random variable is a real number.

If $\mathbf {Z} =(Z_{1},\ldots ,Z_{n})^{\mathsf {T}}$ is a column vector of complex-valued random variables, then the [conjugate transpose](https://en.wikipedia.org/wiki/Conjugate_transpose) $\mathbf {Z} ^{\mathsf {H}}$ is formed by *both* transposing and conjugating. In the following expression, the product of a vector with its conjugate transpose results in a square matrix called the **covariance matrix**, as its expectation: 

$$
\operatorname {K} _{\mathbf {Z} \mathbf {Z} }=\operatorname {cov} [\mathbf {Z} ,\mathbf {Z} ]=\operatorname {E} \left[(\mathbf {Z} -{\boldsymbol {\mu }}_{\mathbf {Z} })(\mathbf {Z} -{\boldsymbol {\mu }}_{\mathbf {Z} })^{\mathsf {H}}\right],
$$

 The matrix so obtained will be [Hermitian](https://en.wikipedia.org/wiki/Hermitian_matrix) [positive-semidefinite](https://en.wikipedia.org/wiki/Positive-semidefinite_matrix), with real numbers in the main diagonal and complex numbers off-diagonal.

Properties

- The covariance matrix is a [Hermitian matrix](https://en.wikipedia.org/wiki/Hermitian_matrix), i.e. $\operatorname {K} _{\mathbf {Z} \mathbf {Z} }^{\mathsf {H}}=\operatorname {K} _{\mathbf {Z} \mathbf {Z} }$.
- The diagonal elements of the covariance matrix are real.

### Pseudo-covariance matrix

For complex random vectors, another kind of second central moment, the **pseudo-covariance matrix** (also called **relation matrix**) is defined as follows: 

$$
\operatorname {J} _{\mathbf {Z} \mathbf {Z} }=\operatorname {cov} [\mathbf {Z} ,{\overline {\mathbf {Z} }}]=\operatorname {E} \left[(\mathbf {Z} -{\boldsymbol {\mu }}_{\mathbf {Z} })(\mathbf {Z} -{\boldsymbol {\mu }}_{\mathbf {Z} })^{\mathsf {T}}\right]
$$

In contrast to the covariance matrix defined above, Hermitian transposition gets replaced by transposition in the definition. Its diagonal elements may be complex valued; it is a [complex symmetric matrix](https://en.wikipedia.org/wiki/Complex_symmetric_matrix).

## Estimation

If $\mathbf {M} _{\mathbf {X} }$ and $\mathbf {M} _{\mathbf {Y} }$ are centered [data matrices](https://en.wikipedia.org/wiki/Data_matrix_(multivariate_statistics)) of dimension $p\times n$ and $q\times n$ respectively, i.e. with *n* columns of observations of *p* and *q* rows of variables, from which the row means have been subtracted, then, if the row means were estimated from the data, sample covariance matrices $\mathbf {Q} _{\mathbf {XX} }$ and $\mathbf {Q} _{\mathbf {XY} }$ can be defined to be 

$$
\mathbf {Q} _{\mathbf {XX} }={\frac {1}{n-1}}\mathbf {M} _{\mathbf {X} }\mathbf {M} _{\mathbf {X} }^{\mathsf {T}},\qquad \mathbf {Q} _{\mathbf {XY} }={\frac {1}{n-1}}\mathbf {M} _{\mathbf {X} }\mathbf {M} _{\mathbf {Y} }^{\mathsf {T}}
$$

 or, if the row means were known a priori, 

$$
\mathbf {Q} _{\mathbf {XX} }={\frac {1}{n}}\mathbf {M} _{\mathbf {X} }\mathbf {M} _{\mathbf {X} }^{\mathsf {T}},\qquad \mathbf {Q} _{\mathbf {XY} }={\frac {1}{n}}\mathbf {M} _{\mathbf {X} }\mathbf {M} _{\mathbf {Y} }^{\mathsf {T}}.
$$

These empirical sample covariance matrices are the most straightforward and most often used estimators for the covariance matrices, but other estimators also exist, including regularised or shrinkage estimators, which may have better properties.

## Applications

The covariance matrix is a useful tool in many different areas. From it a [transformation matrix](https://en.wikipedia.org/wiki/Transformation_matrix) can be derived, called a [whitening transformation](https://en.wikipedia.org/wiki/Whitening_transformation), that allows one to completely decorrelate the data  or, from a different point of view, to find an optimal basis for representing the data in a compact way<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup> (see [Rayleigh quotient](https://en.wikipedia.org/wiki/Rayleigh_quotient) for a formal proof and additional properties of covariance matrices). This is called [[Principal Component Analysis]] (PCA) and the [Karhunen–Loève transform](https://en.wikipedia.org/wiki/Karhunen%E2%80%93Lo%C3%A8ve_transform) (KL-transform).

The covariance matrix plays a key role in [financial economics](https://en.wikipedia.org/wiki/Financial_economics), especially in [portfolio theory](https://en.wikipedia.org/wiki/Modern_portfolio_theory) and its [mutual fund separation theorem](https://en.wikipedia.org/wiki/Mutual_fund_separation_theorem) and in the [capital asset pricing model](https://en.wikipedia.org/wiki/Capital_asset_pricing_model). The matrix of covariances among various assets' returns is used to determine, under certain assumptions, the relative amounts of different assets that investors should (in a [normative analysis](https://en.wikipedia.org/wiki/Normative_economics)) or are predicted to (in a [positive analysis](https://en.wikipedia.org/wiki/Positive_economics)) choose to hold in a context of [diversification](https://en.wikipedia.org/wiki/Diversification_(finance) "Diversification (finance)").

### Use in optimization

The [evolution strategy](https://en.wikipedia.org/wiki/Evolution_strategy), a particular family of Randomized Search Heuristics, fundamentally relies on a covariance matrix in its mechanism. The characteristic mutation operator draws the update step from a multivariate normal distribution using an evolving covariance matrix. There is a formal proof that the [evolution strategy](https://en.wikipedia.org/wiki/Evolution_strategy)'s covariance matrix adapts to the inverse of the [[Hessian Matrix]] of the search landscape, [up to](https://en.wikipedia.org/wiki/Up_to) a scalar factor and small random fluctuations (proven for a single-parent strategy and a static model, as the population size increases, relying on the quadratic approximation). Intuitively, this result is supported by the rationale that the optimal covariance distribution can offer mutation steps whose equidensity probability contours match the level sets of the landscape, and so they maximize the progress rate.

### Covariance mapping

In **covariance mapping** the values of the $\operatorname {cov} (\mathbf {X} ,\mathbf {Y} )$ or $\operatorname {pcov} (\mathbf {X} ,\mathbf {Y} \mid \mathbf {I} )$ matrix are plotted as a 2-dimensional map. When vectors $\mathbf {X}$ and $\mathbf {Y}$ are discrete [random functions](https://en.wikipedia.org/wiki/Random_function), the map shows statistical relations between different regions of the random functions. Statistically independent regions of the functions show up on the map as zero-level flatland, while positive or negative correlations show up, respectively, as hills or valleys.

In practice the column vectors $\mathbf {X} ,\mathbf {Y}$, and $\mathbf {I}$ are acquired experimentally as rows of $n$ samples, e.g. 

$$
\left[\mathbf {X} _{1},\mathbf {X} _{2},\dots ,\mathbf {X} _{n}\right]={\begin{bmatrix}X_{1}(t_{1})&X_{2}(t_{1})&\cdots &X_{n}(t_{1})\\\\X_{1}(t_{2})&X_{2}(t_{2})&\cdots &X_{n}(t_{2})\\\\\vdots &\vdots &\ddots &\vdots \\\\X_{1}(t_{m})&X_{2}(t_{m})&\cdots &X_{n}(t_{m})\end{bmatrix}},
$$

 where $X_{j}(t_{i})$ is the *i*-th discrete value in sample *j* of the random function $X(t)$. The expected values needed in the covariance formula are estimated using the [sample mean](https://en.wikipedia.org/wiki/Sample_mean), e.g. 

$$
\langle \mathbf {X} \rangle ={\frac {1}{n}}\sum _{j=1}^{n}\mathbf {X} _{j}
$$

 and the covariance matrix is estimated by the [sample covariance](https://en.wikipedia.org/wiki/Sample_covariance) matrix 

$$
\operatorname {cov} (\mathbf {X} ,\mathbf {Y} )\approx \langle \mathbf {XY^{\mathsf {T}}} \rangle -\langle \mathbf {X} \rangle \langle \mathbf {Y} ^{\mathsf {T}}\rangle ,
$$

 where the angular brackets denote sample averaging as before except that the [Bessel's correction](https://en.wikipedia.org/wiki/Bessel%27s_correction) should be made to avoid [bias](https://en.wikipedia.org/wiki/Bias_of_an_estimator). Using this estimation the partial covariance matrix can be calculated as 

$$
\operatorname {pcov} (\mathbf {X} ,\mathbf {Y} \mid \mathbf {I} )=\operatorname {cov} (\mathbf {X} ,\mathbf {Y} )-\operatorname {cov} (\mathbf {X} ,\mathbf {I} )\left(\operatorname {cov} (\mathbf {I} ,\mathbf {I} )\backslash \operatorname {cov} (\mathbf {I} ,\mathbf {Y} )\right),
$$

 where the backslash denotes the [left matrix division](https://en.wikipedia.org/wiki/Division_(mathematics)#Left_and_right_division "Division (mathematics)") operator, which bypasses the requirement to invert a matrix and is available in some computational packages such as [Matlab](https://en.wikipedia.org/wiki/Matlab).

![[media/7b7492eb5ecf5657b1e00dd29f75c9d61ffd94c8.png]]
<strong>Figure 1: Construction of a partial covariance map of N<sub>2</sub> molecules undergoing Coulomb explosion induced by a free-electron laser.</strong> Panels <strong>a</strong> and <strong>b</strong> map the two terms of the covariance matrix, which is shown in panel <strong>c</strong>. Panel <strong>d</strong> maps common-mode correlations via intensity fluctuations of the laser. Panel <strong>e</strong> maps the partial covariance matrix that is corrected for the intensity fluctuations. Panel <strong>f</strong> shows that 10% overcorrection improves the map and makes ion-ion correlations clearly visible. Owing to momentum conservation these correlations appear as lines approximately perpendicular to the autocorrelation line (and to the periodic modulations which are caused by detector ringing).

Fig. 1 illustrates how a partial covariance map is constructed on an example of an experiment performed at the [FLASH](https://en.wikipedia.org/wiki/DESY#FLASH) [free-electron laser](https://en.wikipedia.org/wiki/Free-electron_laser) in Hamburg. The random function $X(t)$ is the [time-of-flight](https://en.wikipedia.org/wiki/Time-of-flight_mass_spectrometry) spectrum of ions from a [Coulomb explosion](https://en.wikipedia.org/wiki/Coulomb_explosion) of nitrogen molecules multiply ionised by a laser pulse. Since only a few hundreds of molecules are ionised at each laser pulse, the single-shot spectra are highly fluctuating. However, collecting typically $m=10^{4}$ such spectra, $\mathbf {X} _{j}(t)$, and averaging them over $j$ produces a smooth spectrum $\langle \mathbf {X} (t)\rangle$, which is shown in red at the bottom of Fig. 1. The average spectrum $\langle \mathbf {X} \rangle$ reveals several nitrogen ions in a form of peaks broadened by their kinetic energy, but to find the correlations between the ionisation stages and the ion momenta requires calculating a covariance map.

In the example of Fig. 1 spectra $\mathbf {X} _{j}(t)$ and $\mathbf {Y} _{j}(t)$ are the same, except that the range of the time-of-flight $t$ differs. Panel **a** shows $\langle \mathbf {XY^{\mathsf {T}}} \rangle$, panel **b** shows $\langle \mathbf {X} \rangle \langle \mathbf {Y} ^{\mathsf {T}}\rangle$ and panel **c** shows their difference, which is $\operatorname {cov} (\mathbf {X} ,\mathbf {Y} )$ (note a change in the colour scale). Unfortunately, this map is overwhelmed by uninteresting, common-mode correlations induced by laser intensity fluctuating from shot to shot. To suppress such correlations the laser intensity $I_{j}$ is recorded at every shot, put into $\mathbf {I}$ and $\operatorname {pcov} (\mathbf {X} ,\mathbf {Y} \mid \mathbf {I} )$ is calculated as panels **d** and **e** show. The suppression of the uninteresting correlations is, however, imperfect because there are other sources of common-mode fluctuations than the laser intensity and in principle all these sources should be monitored in vector $\mathbf {I}$. Yet in practice it is often sufficient to overcompensate the partial covariance correction as panel **f** shows, where interesting correlations of ion momenta are now clearly visible as straight lines centred on ionisation stages of atomic nitrogen.

### Two-dimensional infrared spectroscopy

Two-dimensional infrared spectroscopy employs [correlation analysis](https://en.wikipedia.org/wiki/Two-dimensional_correlation_analysis) to obtain 2D spectra of the [condensed phase](https://en.wikipedia.org/wiki/Condensed_matter_physics). There are two versions of this analysis: [synchronous](https://en.wikipedia.org/wiki/Two-dimensional_correlation_analysis#Calculation_of_the_synchronous_spectrum) and [asynchronous](https://en.wikipedia.org/wiki/Two-dimensional_correlation_analysis#Calculation_of_the_asynchronous_spectrum). Mathematically, the former is expressed in terms of the sample covariance matrix and the technique is equivalent to covariance mapping.

## See also

- [Covariance function](https://en.wikipedia.org/wiki/Covariance_function)
- [Eigenvalue decomposition](https://en.wikipedia.org/wiki/Eigenvalue_decomposition)
- [Gramian matrix](https://en.wikipedia.org/wiki/Gramian_matrix)
- [Lewandowski-Kurowicka-Joe distribution](https://en.wikipedia.org/wiki/Lewandowski-Kurowicka-Joe_distribution)
- [Multivariate statistics](https://en.wikipedia.org/wiki/Multivariate_statistics)
- [Principal components](https://en.wikipedia.org/wiki/Principal_components)
- [Quadratic form (statistics)](https://en.wikipedia.org/wiki/Quadratic_form_(statistics) "Quadratic form (statistics)")

## References

1.  ^    Park, Kun Il (2018). *Fundamentals of Probability and Stochastic Processes with Applications to Communications*. Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-319-68074-3](https://en.wikipedia.org/wiki/Special:BookSources/978-3-319-68074-3).
2.  William Feller (1971). [An introduction to probability theory and its applications](https://books.google.com/books?id=K7kdAQAAMAAJ). Wiley. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-25709-7](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-25709-7). Retrieved 10 August 2012.
3.  Wasserman, Larry (2004). [All of Statistics: A Concise Course in Statistical Inference](https://archive.org/details/springer_10.1007-978-0-387-21736-9). Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-40272-1](https://en.wikipedia.org/wiki/Special:BookSources/0-387-40272-1).
4.  Taboga, Marco (2010). ["Lectures on probability theory and mathematical statistics"](http://www.statlect.com/varian2.htm).
5.  Eaton, Morris L. (1983). *Multivariate Statistics: a Vector Space Approach*. John Wiley and Sons. pp. 116–117. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-02776-6](https://en.wikipedia.org/wiki/Special:BookSources/0-471-02776-6).
6.  ^   W J Krzanowski "Principles of Multivariate Analysis" (Oxford University Press, New York, 1988), Chap. 14.4; K V Mardia, J T Kent and J M Bibby "Multivariate Analysis (Academic Press, London, 1997), Chap. 6.5.3; T W Anderson "An Introduction to Multivariate Statistical Analysis" (Wiley, New York, 2003), 3rd ed., Chaps. 2.5.1 and 4.3.1.
7.  Lapidoth, Amos (2009). *A Foundation in Digital Communication*. Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-19395-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-19395-5).
8.  Brookes, Mike. ["The Matrix Reference Manual"](http://www.ee.ic.ac.uk/hp/staff/dmb/matrix/expect.html).
9.  Kessy, Agnan; Strimmer, Korbinian; Lewin, Alex (2018). ["Optimal Whitening and Decorrelation"](https://www.tandfonline.com/doi/full/10.1080/00031305.2016.1277159). *The American Statistician*. **72** (4). Taylor & Francis: 309–314. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1512.00809](https://arxiv.org/abs/1512.00809). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/00031305.2016.1277159](https://doi.org/10.1080%2F00031305.2016.1277159). 
10. Shir, O.M.; A. Yehudayoff (2020). ["On the covariance-Hessian relation in evolution strategies"](https://doi.org/10.1016%2Fj.tcs.2019.09.002). *Theoretical Computer Science*. **801**. Elsevier: 157–174. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1806.03674](https://arxiv.org/abs/1806.03674). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.tcs.2019.09.002](https://doi.org/10.1016%2Fj.tcs.2019.09.002).
11. L J Frasinski "Covariance mapping techniques" *J. Phys. B: At. Mol. Opt. Phys.* **49** 152004 (2016), [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1088/0953-4075/49/15/152004](https://doi.org/10.1088%2F0953-4075%2F49%2F15%2F152004)
12. ^   O Kornilov, M Eckstein, M Rosenblatt, C P Schulz, K Motomura, A Rouzée, J Klei, L Foucar, M Siano, A Lübcke, F. Schapper, P Johnsson, D M P Holland, T Schlatholter, T Marchenko, S Düsterer, K Ueda, M J J Vrakking and L J Frasinski "Coulomb explosion of diatomic molecules in intense XUV fields mapped by partial covariance" *J. Phys. B: At. Mol. Opt. Phys.* **46** 164028 (2013), [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1088/0953-4075/46/16/164028](https://doi.org/10.1088%2F0953-4075%2F46%2F16%2F164028)
13. Noda, I. (1993). "Generalized two-dimensional correlation method applicable to infrared, Raman, and other types of spectroscopy". *Appl. Spectrosc*. **47** (9): 1329–36. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1993ApSpe..47.1329N](https://ui.adsabs.harvard.edu/abs/1993ApSpe..47.1329N). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1366/0003702934067694](https://doi.org/10.1366%2F0003702934067694).

## Further reading

- ["Covariance matrix"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society), 2001 \[1994\]
- "[Covariance Matrix Explained With Pictures](https://thekalmanfilter.com/covariance-matrix-explained/)", an easy way to visualize covariance matrices!
- [Weisstein, Eric W.](https://en.wikipedia.org/wiki/Eric_W._Weisstein) ["Covariance Matrix"](https://mathworld.wolfram.com/CovarianceMatrix.html). *[MathWorld](https://en.wikipedia.org/wiki/MathWorld)*.
- van Kampen, N. G. (1981). [Stochastic processes in physics and chemistry](https://archive.org/details/stochasticproces0000kamp). New York: North-Holland. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-444-86200-5](https://en.wikipedia.org/wiki/Special:BookSources/0-444-86200-5).
