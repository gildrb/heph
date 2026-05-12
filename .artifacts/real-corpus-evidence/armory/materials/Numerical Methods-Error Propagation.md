[[numerical-methods.base]]

> Source: [Propagation of uncertainty](https://en.wikipedia.org/wiki/Propagation_of_uncertainty)
> License: Wikipedia content is available under CC BY-SA 4.0.

In [statistics](https://en.wikipedia.org/wiki/Statistics), **propagation of uncertainty** is the effect of [variables](https://en.wikipedia.org/wiki/Variable_(mathematics) "Variable (mathematics)")' [uncertainties](https://en.wikipedia.org/wiki/Uncertainty) on the uncertainty of a [function](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)") based on them. When the variables are the values of experimental measurements they have [uncertainties due to measurement limitations](https://en.wikipedia.org/wiki/Observational_error) (e.g., instrument [precision](https://en.wikipedia.org/wiki/Accuracy_and_precision)) which propagate due to the combination of variables in the function.

The uncertainty *u* can be expressed in a number of ways. It may be defined by the [absolute error](https://en.wikipedia.org/wiki/Absolute_error) Δ*x*. Uncertainties can also be defined by the [relative error](https://en.wikipedia.org/wiki/Relative_error) (Δ*x*)/*x*, which is usually written as a percentage. Most commonly, the uncertainty on a quantity is quantified in terms of the [standard deviation](https://en.wikipedia.org/wiki/Standard_deviation), σ, which is the positive [square root](https://en.wikipedia.org/wiki/Square_root) of the [variance](https://en.wikipedia.org/wiki/Variance). The value of a quantity and its error are then expressed as an interval *x* ± *u*. However, the most general way of characterizing uncertainty is by specifying its [probability distribution](https://en.wikipedia.org/wiki/Probability_distribution). If the [probability distribution](https://en.wikipedia.org/wiki/Probability_distribution) of the variable is known or can be assumed, in theory it is possible to get any of its statistics. In particular, it is possible to derive [confidence limits](https://en.wikipedia.org/wiki/Confidence_limits) to describe the region within which the true value of the variable may be found. For example, the 68% confidence limits for a one-dimensional variable belonging to a [normal distribution](https://en.wikipedia.org/wiki/Normal_distribution) are approximately ± one standard deviation *σ* from the central value *x*, which means that the region *x* ± *σ* will cover the true value in roughly 68% of cases.

If the uncertainties are [correlated](https://en.wikipedia.org/wiki/Correlated) then [covariance](https://en.wikipedia.org/wiki/Covariance) must be taken into account. Correlation can arise from two different sources. First, the *measurement errors* may be correlated. Second, when the underlying values are correlated across a population, the *uncertainties in the group averages* will be correlated.

In a general context where a nonlinear function modifies the uncertain parameters (correlated or not), the standard tools to propagate uncertainty, and infer resulting quantity probability distribution/statistics, are sampling techniques from the [[Monte Carlo Method]] family. For very large datasets or complex functions, the calculation of the error propagation may be very expensive so that a [surrogate model](https://en.wikipedia.org/wiki/Surrogate_model) or a [parallel computing](https://en.wikipedia.org/wiki/Parallel_computing) strategy may be necessary.

In some particular cases, the uncertainty propagation calculation can be done through simplistic algebraic procedures. Some of these scenarios are described below.

## Linear combinations

Let $\{f_{k}(x_{1},x_{2},\dots ,x_{n})\}$ be a set of *m* functions, which are linear combinations of $n$ variables $x_{1},x_{2},\dots ,x_{n}$ with combination coefficients $A_{k1},A_{k2},\dots ,A_{kn},(k=1,\dots ,m)$: 

$$
f_{k}=\sum _{i=1}^{n}A_{ki}x_{i},
$$

 or in matrix notation, 

$$
\mathbf {f} =\mathbf {A} \mathbf {x} .
$$

Also let the [variance–covariance matrix](https://en.wikipedia.org/wiki/Variance%E2%80%93covariance_matrix) of *x* = (*x*<sub>1</sub>, ..., *x*<sub>*n*</sub>) be denoted by ${\boldsymbol {\Sigma }}^{x}$ and let the mean value be denoted by ${\boldsymbol {\mu }}$: 

$$
{\begin{aligned}{\boldsymbol {\Sigma }}^{x}=\operatorname {E} [(\mathbf {x} -{\boldsymbol {\mu }})\otimes (\mathbf {x} -{\boldsymbol {\mu }})]&={\begin{pmatrix}\sigma _{1}^{2}&\sigma _{12}&\sigma _{13}&\cdots \\\sigma _{21}&\sigma _{2}^{2}&\sigma _{23}&\cdots \\\sigma _{31}&\sigma _{32}&\sigma _{3}^{2}&\cdots \\\vdots &\vdots &\vdots &\ddots \end{pmatrix}}\\[1ex]&={\begin{pmatrix}{\Sigma }_{11}^{x}&{\Sigma }_{12}^{x}&{\Sigma }_{13}^{x}&\cdots \\{\Sigma }_{21}^{x}&{\Sigma }_{22}^{x}&{\Sigma }_{23}^{x}&\cdots \\{\Sigma }_{31}^{x}&{\Sigma }_{32}^{x}&{\Sigma }_{33}^{x}&\cdots \\\vdots &\vdots &\vdots &\ddots \end{pmatrix}}.\end{aligned}}
$$

 $\otimes$ is the [outer product](https://en.wikipedia.org/wiki/Outer_product).

Then, the variance–covariance matrix ${\boldsymbol {\Sigma }}^{f}$ of *f* is given by 

$$
{\begin{aligned}{\boldsymbol {\Sigma }}^{f}&=\operatorname {E} \left[(\mathbf {f} -\operatorname {E} [\mathbf {f} ])\otimes (\mathbf {f} -\operatorname {E} [\mathbf {f} ])\right]=\operatorname {E} \left[\mathbf {A} (\mathbf {x} -{\boldsymbol {\mu }})\otimes \mathbf {A} (\mathbf {x} -{\boldsymbol {\mu }})\right]\\[1ex]&=\mathbf {A} \operatorname {E} \left[(\mathbf {x} -{\boldsymbol {\mu }})\otimes (\mathbf {x} -{\boldsymbol {\mu }})\right]\mathbf {A} ^{\mathrm {T} }=\mathbf {A} {\boldsymbol {\Sigma }}^{x}\mathbf {A} ^{\mathrm {T} }.\end{aligned}}
$$

In component notation, the equation 

$$
{\boldsymbol {\Sigma }}^{f}=\mathbf {A} {\boldsymbol {\Sigma }}^{x}\mathbf {A} ^{\mathrm {T} }
$$

 reads 

$$
\Sigma _{ij}^{f}=\sum _{k}^{n}\sum _{l}^{n}A_{ik}{\Sigma }_{kl}^{x}A_{jl}.
$$

This is the most general expression for the propagation of error from one set of variables onto another. When the errors on *x* are uncorrelated, the general expression simplifies to 

$$
\Sigma _{ij}^{f}=\sum _{k}^{n}A_{ik}\Sigma _{k}^{x}A_{jk},
$$

 where $\Sigma _{k}^{x}=\sigma _{x_{k}}^{2}$ is the variance of *k*-th element of the *x* vector. Note that even though the errors on *x* may be uncorrelated, the errors on *f* are in general correlated; in other words, even if ${\boldsymbol {\Sigma }}^{x}$ is a [diagonal matrix](https://en.wikipedia.org/wiki/Diagonal_matrix), ${\boldsymbol {\Sigma }}^{f}$ is in general a full matrix.

The general expressions for a scalar-valued function *f* are a little simpler (here **a** is a [row vector](https://en.wikipedia.org/wiki/Row_and_column_vectors)): 

$$
f=\sum _{i}^{n}a_{i}x_{i}=\mathbf {ax} ,
$$

$$
\sigma _{f}^{2}=\sum _{i}^{n}\sum _{j}^{n}a_{i}\Sigma _{ij}^{x}a_{j}=\mathbf {a} {\boldsymbol {\Sigma }}^{x}\mathbf {a} ^{\mathrm {T} }.
$$

Each covariance term $\sigma _{ij}$ can be expressed in terms of the [correlation coefficient](https://en.wikipedia.org/wiki/Pearson_product-moment_correlation_coefficient) $\rho _{ij}$ by $\sigma _{ij}=\rho _{ij}\sigma _{i}\sigma _{j}$, so that an alternative expression for the variance of *f* is 

$$
\sigma _{f}^{2}=\sum _{i}^{n}a_{i}^{2}\sigma _{i}^{2}+\sum _{i}^{n}\sum _{j(j\neq i)}^{n}a_{i}a_{j}\rho _{ij}\sigma _{i}\sigma _{j}.
$$

In the case that the variables in *x* are uncorrelated, this simplifies further to 

$$
\sigma _{f}^{2}=\sum _{i}^{n}a_{i}^{2}\sigma _{i}^{2}.
$$

In the simple case of identical coefficients and variances, we find 

$$
\sigma _{f}={\sqrt {n}}\,|a|\sigma .
$$

For the arithmetic mean, $a=1/n$, the result is the [standard error of the mean](https://en.wikipedia.org/wiki/Standard_error_of_the_mean): 

$$
\sigma _{f}={\frac {\sigma }{\sqrt {n}}}.
$$

## Non-linear combinations

When *f* is a set of non-linear combination of the variables *x*, an [interval propagation](https://en.wikipedia.org/wiki/Interval_propagation) could be performed in order to compute intervals which contain all consistent values for the variables. In a probabilistic approach, the function *f* must usually be linearised by approximation to a first-order [[Taylor Series]] expansion, though in some cases, exact formulae can be derived that do not depend on the expansion as is the case for the exact variance of products. The Taylor expansion would be: 

$$
f_{k}\approx f_{k}^{0}+\sum _{i}^{n}{\frac {\partial f_{k}}{\partial {x_{i}}}}x_{i}
$$

 where $\partial f_{k}/\partial x_{i}$ denotes the [partial derivative](https://en.wikipedia.org/wiki/Partial_derivative) of *f<sub>k</sub>* with respect to the *i*-th variable, evaluated at the mean value of all components of vector *x*. Or in [matrix notation](https://en.wikipedia.org/wiki/Matrix_notation), 

$$
\mathrm {f} \approx \mathrm {f} ^{0}+\mathrm {J} \mathrm {x} \,
$$

 where J is the [[Jacobian Matrix]]. Since f<sup>0</sup> is a constant it does not contribute to the error on f. Therefore, the propagation of error follows the linear case, above, but replacing the linear coefficients, *A<sub>ki</sub>* and *A<sub>kj</sub>* by the partial derivatives, ${\frac {\partial f_{k}}{\partial x_{i}}}$ and ${\frac {\partial f_{k}}{\partial x_{j}}}$. In matrix notation, 

$$
\mathrm {\Sigma } ^{\mathrm {f} }=\mathrm {J} \mathrm {\Sigma } ^{\mathrm {x} }\mathrm {J} ^{\top }.
$$

That is, the Jacobian of the function is used to transform the rows and columns of the variance-covariance matrix of the argument. Note this is equivalent to the matrix expression for the linear case with $\mathrm {J=A}$.

### Simplification

Neglecting correlations or assuming independent variables yields a common formula among engineers and experimental scientists to calculate error propagation, the variance formula: 

$$
s_{f}={\sqrt {\left({\frac {\partial f}{\partial x}}\right)^{2}s_{x}^{2}+\left({\frac {\partial f}{\partial y}}\right)^{2}s_{y}^{2}+\left({\frac {\partial f}{\partial z}}\right)^{2}s_{z}^{2}+\cdots }}
$$

 where $s_{f}$ represents the standard deviation of the function $f$, $s_{x}$ represents the standard deviation of $x$, $s_{y}$ represents the standard deviation of $y$, and so forth.

This formula is based on the linear characteristics of the gradient of $f$ and therefore it is a good estimation for the standard deviation of $f$ as long as $s_{x},s_{y},s_{z},\ldots$ are small enough. Specifically, the [linear approximation](https://en.wikipedia.org/wiki/Linear_approximation) of $f$ has to be close to $f$ inside a neighbourhood of radius $s_{x},s_{y},s_{z},\ldots$.

### Example

Any non-linear [differentiable function](https://en.wikipedia.org/wiki/Differentiable_function), $f(a,b)$, of two variables, $a$ and $b$, can be expanded as 

$$
f\approx f^{0}+{\frac {\partial f}{\partial a}}a+{\frac {\partial f}{\partial b}}b.
$$

 If we take the variance on both sides and use the formula for the variance of a [linear combination](https://en.wikipedia.org/wiki/Linear_combination) of variables 

$$
\operatorname {Var} (aX+bY)=a^{2}\operatorname {Var} (X)+b^{2}\operatorname {Var} (Y)+2ab\operatorname {Cov} (X,Y),
$$

 then we obtain 

$$
\sigma _{f}^{2}\approx \left|{\frac {\partial f}{\partial a}}\right|^{2}\sigma _{a}^{2}+\left|{\frac {\partial f}{\partial b}}\right|^{2}\sigma _{b}^{2}+2{\frac {\partial f}{\partial a}}{\frac {\partial f}{\partial b}}\sigma _{ab},
$$

 where $\sigma _{f}$ is the standard deviation of the function $f$, $\sigma _{a}$ is the standard deviation of $a$, $\sigma _{b}$ is the standard deviation of $b$ and $\sigma _{ab}=\sigma _{a}\sigma _{b}\rho _{ab}$ is the covariance between $a$ and $b$.

In the particular case that $f=ab$, ${\frac {\partial f}{\partial a}}=b$, ${\frac {\partial f}{\partial b}}=a$. Then 

$$
\sigma _{f}^{2}\approx b^{2}\sigma _{a}^{2}+a^{2}\sigma _{b}^{2}+2ab\,\sigma _{ab}
$$

 or 

$$
\left({\frac {\sigma _{f}}{f}}\right)^{2}\approx \left({\frac {\sigma _{a}}{a}}\right)^{2}+\left({\frac {\sigma _{b}}{b}}\right)^{2}+2\left({\frac {\sigma _{a}}{a}}\right)\left({\frac {\sigma _{b}}{b}}\right)\rho _{ab}
$$

 where $\rho _{ab}$ is the correlation between $a$ and $b$.

When the variables $a$ and $b$ are uncorrelated, $\rho _{ab}=0$. Then 

$$
\left({\frac {\sigma _{f}}{f}}\right)^{2}\approx \left({\frac {\sigma _{a}}{a}}\right)^{2}+\left({\frac {\sigma _{b}}{b}}\right)^{2}.
$$

### Caveats and warnings

Error estimates for non-linear functions are [biased](https://en.wikipedia.org/wiki/Bias_of_an_estimator) on account of using a truncated series expansion. The extent of this bias depends on the nature of the function. For example, the bias on the error calculated for log(1+*x*) increases as *x* increases, since the expansion to *x* is a good approximation only when *x* is near zero.

For highly non-linear functions, there exist five categories of probabilistic approaches for uncertainty propagation; see [Uncertainty quantification](https://en.wikipedia.org/wiki/Uncertainty_quantification#Forward_propagation) for details.

#### Reciprocal and shifted reciprocal

In the special case of the inverse or reciprocal $1/B$, where $B=N(0,1)$ follows a [standard normal distribution](https://en.wikipedia.org/wiki/Standard_normal_distribution), the resulting distribution is a reciprocal standard normal distribution, and there is no definable variance.

However, in the slightly more general case of a shifted reciprocal function $1/(p-B)$ for $B=N(\mu ,\sigma )$ following a general normal distribution, then mean and variance statistics do exist in a [principal value](https://en.wikipedia.org/wiki/Principal_value) sense, if the difference between the pole $p$ and the mean $\mu$ is real-valued.

#### Ratios

Ratios are also problematic; normal approximations exist under certain conditions.

## Example formulae

This table shows the variances and standard deviations of simple functions of the real variables $A,B$ with standard deviations $\sigma _{A},\sigma _{B},$ [covariance](https://en.wikipedia.org/wiki/Covariance_and_correlation) $\sigma _{AB}=\rho _{AB}\sigma _{A}\sigma _{B},$ and correlation $\rho _{AB}.$ The real-valued coefficients $a$ and $b$ are assumed exactly known (deterministic), i.e., $\sigma _{a}=\sigma _{b}=0.$

In the right-hand columns of the table, $A$ and $B$ are [expectation values](https://en.wikipedia.org/wiki/Expected_value), and $f$ is the value of the function calculated at those values.

|  |  |  |
|----|----|----|
| Function | Variance | Standard deviation |
| $f=aA\,$ | $\sigma _{f}^{2}=a^{2}\sigma _{A}^{2}$ | $\sigma _{f}=|a|\sigma _{A}$ |
| $f=A+B$ | $\sigma _{f}^{2}=\sigma _{A}^{2}+\sigma _{B}^{2}+2\sigma _{AB}$ | $\sigma _{f}={\sqrt {\sigma _{A}^{2}+\sigma _{B}^{2}+2\sigma _{AB}}}$ |
| $f=A-B$ | $\sigma _{f}^{2}=\sigma _{A}^{2}+\sigma _{B}^{2}-2\sigma _{AB}$ | $\sigma _{f}={\sqrt {\sigma _{A}^{2}+\sigma _{B}^{2}-2\sigma _{AB}}}$ |
| $f=aA+bB$ | $\sigma _{f}^{2}=a^{2}\sigma _{A}^{2}+b^{2}\sigma _{B}^{2}+2ab\,\sigma _{AB}$ | $\sigma _{f}={\sqrt {a^{2}\sigma _{A}^{2}+b^{2}\sigma _{B}^{2}+2ab\,\sigma _{AB}}}$ |
| $f=aA-bB$ | $\sigma _{f}^{2}=a^{2}\sigma _{A}^{2}+b^{2}\sigma _{B}^{2}-2ab\,\sigma _{AB}$ | $\sigma _{f}={\sqrt {a^{2}\sigma _{A}^{2}+b^{2}\sigma _{B}^{2}-2ab\,\sigma _{AB}}}$ |
| $f=AB$ | $\sigma _{f}^{2}\approx f^{2}\left[\left({\frac {\sigma _{A}}{A}}\right)^{2}+\left({\frac {\sigma _{B}}{B}}\right)^{2}+2{\frac {\sigma _{AB}}{AB}}\right]$ | $\sigma _{f}\approx \left|f\right|{\sqrt {\left({\frac {\sigma _{A}}{A}}\right)^{2}+\left({\frac {\sigma _{B}}{B}}\right)^{2}+2{\frac {\sigma _{AB}}{AB}}}}$ |
| $f={\frac {A}{B}}$ | $\sigma _{f}^{2}\approx f^{2}\left[\left({\frac {\sigma _{A}}{A}}\right)^{2}+\left({\frac {\sigma _{B}}{B}}\right)^{2}-2{\frac {\sigma _{AB}}{AB}}\right]$ | $\sigma _{f}\approx \left|f\right|{\sqrt {\left({\frac {\sigma _{A}}{A}}\right)^{2}+\left({\frac {\sigma _{B}}{B}}\right)^{2}-2{\frac {\sigma _{AB}}{AB}}}}$ |
| $f={\frac {A}{A+B}}$ | $\sigma _{f}^{2}\approx {\frac {f^{2}}{\left(A+B\right)^{2}}}\left({\frac {B^{2}}{A^{2}}}\sigma _{A}^{2}+\sigma _{B}^{2}-2{\frac {B}{A}}\sigma _{AB}\right)$ | $\sigma _{f}\approx \left|{\frac {f}{A+B}}\right|{\sqrt {{\frac {B^{2}}{A^{2}}}\sigma _{A}^{2}+\sigma _{B}^{2}-2{\frac {B}{A}}\sigma _{AB}}}$ |
| $f=aA^{b}$ | $\sigma _{f}^{2}\approx \left({a}{b}{A}^{b-1}{\sigma _{A}}\right)^{2}=\left({\frac {{f}{b}{\sigma _{A}}}{A}}\right)^{2}$ | $\sigma _{f}\approx \left|{a}{b}{A}^{b-1}{\sigma _{A}}\right|=\left|{\frac {{f}{b}{\sigma _{A}}}{A}}\right|$ |
| $f=a\ln(bA)$ | $\sigma _{f}^{2}\approx \left(a{\frac {\sigma _{A}}{A}}\right)^{2}$ | $\sigma _{f}\approx \left|a{\frac {\sigma _{A}}{A}}\right|$ |
| $f=a\log _{10}(bA)$ | $\sigma _{f}^{2}\approx \left(a{\frac {\sigma _{A}}{A\ln(10)}}\right)^{2}$ | $\sigma _{f}\approx \left|a{\frac {\sigma _{A}}{A\ln(10)}}\right|$ |
| $f=ae^{bA}$ | $\sigma _{f}^{2}\approx f^{2}\left(b\sigma _{A}\right)^{2}$ | $\sigma _{f}\approx \left|f\right|\left|\left(b\sigma _{A}\right)\right|$ |
| $f=a^{bA}$ | $\sigma _{f}^{2}\approx f^{2}(b\ln(a)\sigma _{A})^{2}$ | $\sigma _{f}\approx \left|f\right|\left|b\ln(a)\sigma _{A}\right|$ |
| $f=a\sin(bA)$ | $\sigma _{f}^{2}\approx \left[ab\cos(bA)\sigma _{A}\right]^{2}$ | $\sigma _{f}\approx \left|ab\cos(bA)\sigma _{A}\right|$ |
| $f=a\cos \left(bA\right)\,$ | $\sigma _{f}^{2}\approx \left[ab\sin(bA)\sigma _{A}\right]^{2}$ | $\sigma _{f}\approx \left|ab\sin(bA)\sigma _{A}\right|$ |
| $f=a\tan \left(bA\right)\,$ | $\sigma _{f}^{2}\approx \left[ab\sec ^{2}(bA)\sigma _{A}\right]^{2}$ | $\sigma _{f}\approx \left|ab\sec ^{2}(bA)\sigma _{A}\right|$ |
| $f=A^{B}$ | $\sigma _{f}^{2}\approx f^{2}\left[\left({\frac {B}{A}}\sigma _{A}\right)^{2}+\left(\ln(A)\sigma _{B}\right)^{2}+2{\frac {B\ln(A)}{A}}\sigma _{AB}\right]$ | $\sigma _{f}\approx \left|f\right|{\sqrt {\left({\frac {B}{A}}\sigma _{A}\right)^{2}+\left(\ln(A)\sigma _{B}\right)^{2}+2{\frac {B\ln(A)}{A}}\sigma _{AB}}}$ |
| $f={\sqrt {aA^{2}\pm bB^{2}}}$ | $\sigma _{f}^{2}\approx \left({\frac {A}{f}}\right)^{2}a^{2}\sigma _{A}^{2}+\left({\frac {B}{f}}\right)^{2}b^{2}\sigma _{B}^{2}\pm 2ab{\frac {AB}{f^{2}}}\,\sigma _{AB}$ | $\sigma _{f}\approx {\sqrt {\left({\frac {A}{f}}\right)^{2}a^{2}\sigma _{A}^{2}+\left({\frac {B}{f}}\right)^{2}b^{2}\sigma _{B}^{2}\pm 2ab{\frac {AB}{f^{2}}}\,\sigma _{AB}}}$ |

For uncorrelated variables ($\rho _{AB}=0$, $\sigma _{AB}=0$) expressions for more complicated functions can be derived by combining simpler functions. For example, repeated multiplication, assuming no correlation, gives 

$$
f=ABC;\qquad \left({\frac {\sigma _{f}}{f}}\right)^{2}\approx \left({\frac {\sigma _{A}}{A}}\right)^{2}+\left({\frac {\sigma _{B}}{B}}\right)^{2}+\left({\frac {\sigma _{C}}{C}}\right)^{2}.
$$

For the case $f=AB$ we also have Goodman's expression for the exact variance: for the uncorrelated case it is 

$$
\operatorname {V} [XY]=\operatorname {E} [X]^{2}\operatorname {V} [Y]+\operatorname {E} [Y]^{2}\operatorname {V} [X]+\operatorname {V} [X]\operatorname {V} [Y],
$$

 and therefore we have 

$$
\sigma _{f}^{2}=A^{2}\sigma _{B}^{2}+B^{2}\sigma _{A}^{2}+\sigma _{A}^{2}\sigma _{B}^{2}.
$$

 The last term represents a small correction to the usual formula as can be seen by dividing both sides by $f^{2}=A^{2}B^{2}$. 

$$
\left({\frac {\sigma _{f}}{f}}\right)^{2}=\left({\frac {\sigma _{A}}{A}}\right)^{2}+\left({\frac {\sigma _{B}}{B}}\right)^{2}+\left({\frac {\sigma _{A}\sigma _{B}}{AB}}\right)^{2}.
$$

### Effect of correlation on differences

If *A* and *B* are uncorrelated, their difference *A* − *B* will have more variance than either of them. An increasing positive correlation ($\rho _{AB}\to 1$) will decrease the variance of the difference, converging to zero variance for perfectly correlated variables with the [same variance](https://en.wikipedia.org/wiki/Homoscedastic). On the other hand, a negative correlation ($\rho _{AB}\to -1$) will further increase the variance of the difference, compared to the uncorrelated case.

For example, the self-subtraction *f* = *A* − *A* has zero variance $\sigma _{f}^{2}=0$ only if the variate is perfectly [autocorrelated](https://en.wikipedia.org/wiki/Autocorrelation) ($\rho _{A}=1$). If *A* is uncorrelated, $\rho _{A}=0,$ then the output variance is twice the input variance, $\sigma _{f}^{2}=2\sigma _{A}^{2}.$ And if *A* is perfectly anticorrelated, $\rho _{A}=-1,$ then the input variance is quadrupled in the output, $\sigma _{f}^{2}=4\sigma _{A}^{2}$ (notice $1-\rho _{A}=2$ for *f* = *aA* − *aA* in the table above).

## Example calculations

### Inverse tangent function

We can calculate the uncertainty propagation for the inverse tangent function as an example of using partial derivatives to propagate error.

Define 

$$
f(x)=\arctan(x),
$$

 where $\Delta _{x}$ is the absolute uncertainty on our measurement of x. The derivative of *f*(*x*) with respect to x is 

$$
{\frac {df}{dx}}={\frac {1}{1+x^{2}}}.
$$

Therefore, our propagated uncertainty is 

$$
\Delta _{f}\approx {\frac {\Delta _{x}}{1+x^{2}}},
$$

 where $\Delta _{f}$ is the absolute propagated uncertainty.

### Resistance measurement

A practical application is an [experiment](https://en.wikipedia.org/wiki/Experiment) in which one measures [current](https://en.wikipedia.org/wiki/Current_(electricity)), I, and [voltage](https://en.wikipedia.org/wiki/Voltage), V, on a [resistor](https://en.wikipedia.org/wiki/Resistor) in order to determine the [resistance](https://en.wikipedia.org/wiki/Electrical_resistance), R, using [Ohm's law](https://en.wikipedia.org/wiki/Ohm%27s_law), *R* = *V* / *I*.

Given the measured variables with uncertainties, *I* ± *σ*<sub>*I*</sub> and *V* ± *σ*<sub>*V*</sub>, and neglecting their possible correlation, the uncertainty in the computed quantity, *σ*<sub>*R*</sub>, is:

$$
\sigma _{R}\approx {\sqrt {\sigma _{V}^{2}\left({\frac {1}{I}}\right)^{2}+\sigma _{I}^{2}\left({\frac {-V}{I^{2}}}\right)^{2}}}=R{\sqrt {\left({\frac {\sigma _{V}}{V}}\right)^{2}+\left({\frac {\sigma _{I}}{I}}\right)^{2}}}.
$$

## See also

- [Accuracy and precision](https://en.wikipedia.org/wiki/Accuracy_and_precision)
- [[Automatic Differentiation]]
- [Bienaymé's identity](https://en.wikipedia.org/wiki/Bienaym%C3%A9%27s_identity)
- [Delta method](https://en.wikipedia.org/wiki/Delta_method)
- [Dilution of precision (navigation)](https://en.wikipedia.org/wiki/Dilution_of_precision_(navigation))
- [Errors and residuals in statistics](https://en.wikipedia.org/wiki/Errors_and_residuals_in_statistics)
- [Experimental uncertainty analysis](https://en.wikipedia.org/wiki/Experimental_uncertainty_analysis)
- [Interval finite element](https://en.wikipedia.org/wiki/Interval_finite_element)
- [Measurement uncertainty](https://en.wikipedia.org/wiki/Measurement_uncertainty)
- [[Numerical Stability]]
- [Probability bounds analysis](https://en.wikipedia.org/wiki/Probability_bounds_analysis)
- [Uncertainty quantification](https://en.wikipedia.org/wiki/Uncertainty_quantification)
- [Random-fuzzy variable](https://en.wikipedia.org/wiki/Random-fuzzy_variable)
- [Variance § Propagation](https://en.wikipedia.org/wiki/Variance#Propagation)

## References

1.  Kirchner, James. ["Data Analysis Toolkit #5: Uncertainty Analysis and Error Propagation"](http://seismo.berkeley.edu/~kirchner/eps_120/Toolkits/Toolkit_05.pdf) (PDF). *Berkeley Seismology Laboratory*. University of California. Retrieved 22 April 2016.
2.  Kroese, D. P.; Taimre, T.; Botev, Z. I. (2011). *Handbook of Monte Carlo Methods*. John Wiley & Sons.
3.  Ranftl, Sascha; von der Linden, Wolfgang (2021-11-13). ["Bayesian Surrogate Analysis and Uncertainty Propagation"](https://doi.org/10.3390%2Fpsf2021003006). *Physical Sciences Forum*. **3** (1): 6. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2101.04038](https://arxiv.org/abs/2101.04038). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3390/psf2021003006](https://doi.org/10.3390%2Fpsf2021003006). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [2673-9984](https://search.worldcat.org/issn/2673-9984).
4.  Atanassova, E.; Gurov, T.; Karaivanova, A.; Ivanovska, S.; Durchova, M.; Dimitrov, D. (2016). "On the parallelization approaches for Intel MIC architecture". *AIP Conference Proceedings*. **1773** (1): 070001. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2016AIPC.1773g0001A](https://ui.adsabs.harvard.edu/abs/2016AIPC.1773g0001A). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1063/1.4964983](https://doi.org/10.1063%2F1.4964983).
5.  Cunha Jr, A.; Nasser, R.; Sampaio, R.; Lopes, H.; Breitman, K. (2014). "Uncertainty quantification through the Monte Carlo method in a cloud computing setting". *Computer Physics Communications*. **185** (5): 1355–1363. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2105.09512](https://arxiv.org/abs/2105.09512). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2014CoPhC.185.1355C](https://ui.adsabs.harvard.edu/abs/2014CoPhC.185.1355C). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.cpc.2014.01.006](https://doi.org/10.1016%2Fj.cpc.2014.01.006). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [32376269](https://api.semanticscholar.org/CorpusID:32376269).
6.  Lin, Y.; Wang, F.; Liu, B. (2018). "Random number generators for large-scale parallel Monte Carlo simulations on FPGA". *Journal of Computational Physics*. **360**: 93–103. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2018JCoPh.360...93L](https://ui.adsabs.harvard.edu/abs/2018JCoPh.360...93L). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.jcp.2018.01.029](https://doi.org/10.1016%2Fj.jcp.2018.01.029).
7.  ^   [Goodman, Leo](https://en.wikipedia.org/wiki/Leo_Goodman) (1960). "On the Exact Variance of Products". *Journal of the American Statistical Association*. **55** (292): 708–713. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2281592](https://doi.org/10.2307%2F2281592). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2281592](https://www.jstor.org/stable/2281592).
8.  Ochoa1, Benjamin; Belongie, Serge ["Covariance Propagation for Guided Matching"](http://vision.ucsd.edu/sites/default/files/ochoa06.pdf) [Archived](https://web.archive.org/web/20110720080130/http://vision.ucsd.edu/sites/default/files/ochoa06.pdf) 2011-07-20 at the [Wayback Machine](https://en.wikipedia.org/wiki/Wayback_Machine)
9.  Ku, H. H. (October 1966). ["Notes on the use of propagation of error formulas"](http://nistdigitalarchives.contentdm.oclc.org/cdm/compoundobject/collection/p16009coll6/id/99848/rec/1). *Journal of Research of the National Bureau of Standards*. **70C** (4): 262. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.6028/jres.070c.025](https://doi.org/10.6028%2Fjres.070c.025). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0022-4316](https://search.worldcat.org/issn/0022-4316). Retrieved 3 October 2012.
10. Clifford, A. A. (1973). *Multivariate error analysis: a handbook of error propagation and calculation in many-parameter systems*. John Wiley & Sons. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0470160558](https://en.wikipedia.org/wiki/Special:BookSources/978-0470160558).<sup>\[*[page needed](https://en.wikipedia.org/wiki/Wikipedia:Citing_sources)*\]</sup>
11. Soch, Joram (2020-07-07). ["Variance of the linear combination of two random variables"](https://statproofbook.github.io/P/var-lincomb.html). *The Book of Statistical Proofs*. Retrieved 2022-01-29.
12. Lee, S. H.; Chen, W. (2009). "A comparative study of uncertainty propagation methods for black-box-type problems". *Structural and Multidisciplinary Optimization*. **37** (3): 239–253. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s00158-008-0234-7](https://doi.org/10.1007%2Fs00158-008-0234-7). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [119988015](https://api.semanticscholar.org/CorpusID:119988015).
13. Johnson, Norman L.; Kotz, Samuel; Balakrishnan, Narayanaswamy (1994). *Continuous Univariate Distributions, Volume 1*. Wiley. p. 171. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-58495-9](https://en.wikipedia.org/wiki/Special:BookSources/0-471-58495-9).
14. Lecomte, Christophe (May 2013). "Exact statistics of systems with uncertainties: an analytical theory of rank-one stochastic dynamic systems". *Journal of Sound and Vibration*. **332** (11): 2750–2776. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2013JSV...332.2750L](https://ui.adsabs.harvard.edu/abs/2013JSV...332.2750L). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.jsv.2012.12.009](https://doi.org/10.1016%2Fj.jsv.2012.12.009).
15. ["A Summary of Error Propagation"](https://web.archive.org/web/20161213135602/http://ipl.physics.harvard.edu/wp-uploads/2013/03/PS3_Error_Propagation_sp13.pdf) (PDF). p. 2. Archived from [the original](http://ipl.physics.harvard.edu/wp-uploads/2013/03/PS3_Error_Propagation_sp13.pdf) (PDF) on 2016-12-13. Retrieved 2016-04-04.
16. ["Propagation of Uncertainty through Mathematical Operations"](http://web.mit.edu/fluids-modules/www/exper_techniques/2.Propagation_of_Uncertaint.pdf) (PDF). p. 5. Retrieved 2016-04-04.
17. ["Strategies for Variance Estimation"](http://www.sagepub.com/upm-data/6427_Chapter_4__Lee_%28Analyzing%29_I_PDF_6.pdf) (PDF). p. 37. Retrieved 2013-01-18.
18. ^   Harris, Daniel C. (2003), [Quantitative chemical analysis](https://books.google.com/books?id=csTsQr-v0d0C&pg=PA56) (6th ed.), Macmillan, p. 56, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-7167-4464-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-7167-4464-1)
19. ["Error Propagation tutorial"](http://www.foothill.edu/psme/daley/tutorials_files/10.%20Error%20Propagation.pdf) (PDF). *Foothill College*. October 9, 2009. Retrieved 2012-03-01.

## Further reading

- Bevington, Philip R.; Robinson, D. Keith (2002), *Data Reduction and Error Analysis for the Physical Sciences* (3rd ed.), McGraw-Hill, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-07-119926-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-07-119926-1)
- Fornasini, Paolo (2008), [The uncertainty in physical measurements: an introduction to data analysis in the physics laboratory](https://books.google.com/books?id=PBJgvPgf2NkC&pg=PA161), Springer, p. 161, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-78649-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-78649-0)
- Meyer, Stuart L. (1975), *Data Analysis for Scientists and Engineers*, Wiley, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-59995-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-59995-1)
- Peralta, M. (2012), *Propagation Of Errors: How To Mathematically Predict Measurement Errors*, CreateSpace
- Rouaud, M. (2013), [Probability, Statistics and Estimation: Propagation of Uncertainties in Experimental Measurement](http://www.incertitudes.fr/book.pdf) (PDF) (short ed.)
- Taylor, J. R. (1997), *An Introduction to Error Analysis: The Study of Uncertainties in Physical Measurements* (2nd ed.), University Science Books
- Wang, C. M.; Iyer, Hari K. (2005-09-07). "On higher-order corrections for propagating uncertainties". *Metrologia*. **42** (5): 406–410. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2005Metro..42..406W](https://ui.adsabs.harvard.edu/abs/2005Metro..42..406W). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1088/0026-1394/42/5/011](https://doi.org/10.1088%2F0026-1394%2F42%2F5%2F011). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0026-1394](https://search.worldcat.org/issn/0026-1394). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [122841691](https://api.semanticscholar.org/CorpusID:122841691).

## External links

- [Uncertainty Calculator](https://uncertainty.formulaalchemy.com/) Build ISO 17025‑Ready Uncertainty Budgets Without Spreadsheets or Black Boxes
- [A detailed discussion of measurements and the propagation of uncertainty](http://www.av8n.com/physics/uncertainty.htm) explaining the benefits of using error propagation formulas and Monte Carlo simulations instead of simple significance arithmetic
- [GUM](https://www.bipm.org/documents/20126/2071204/JCGM_100_2008_E.pdf/cb0ef43f-baa5-11cf-3f85-4dcd86f77bd6), Guide to the Expression of Uncertainty in Measurement
- [EPFL An Introduction to Error Propagation](http://srl.informatik.uni-freiburg.de/papers/arrasTR98.pdf), Derivation, Meaning and Examples of Cy = Fx Cx Fx'
- [uncertainties package](https://pythonhosted.org/uncertainties/), a program/library for transparently performing calculations with uncertainties (and error correlations).
- [soerp package](https://pypi.org/project/soerp/), a Python program/library for transparently performing \*second-order\* calculations with uncertainties (and error correlations).
- Joint Committee for Guides in Metrology (2011). [JCGM 102: Evaluation of Measurement Data - Supplement 2 to the "Guide to the Expression of Uncertainty in Measurement" - Extension to Any Number of Output Quantities](http://www.bipm.org/utils/common/documents/jcgm/JCGM_102_2011_E.pdf) (PDF) (Technical report). JCGM. Retrieved 13 February 2013.
