[[probability-statistics.base]]

> Source: [[Probability Density Function]]
> License: Wikipedia content is available under CC BY-SA 4.0.

![[media/343a05e9c1636be0e6dc91799388c42ae0eb6dc7.png]]
[Box plot](https://en.wikipedia.org/wiki/Box_plot) and probability density function of a [normal distribution](https://en.wikipedia.org/wiki/Normal_distribution) <em>N</em>(0, <em>σ</em><sup>2</sup>).

![[media/7c7d6ff5270637b34a23f29aeaee1a637940b588.png]]
Geometric visualisation of the [mode](https://en.wikipedia.org/wiki/Mode_(statistics)), [median](https://en.wikipedia.org/wiki/Median_(statistics)) and [mean](https://en.wikipedia.org/wiki/Mean_(statistics)) of an arbitrary unimodal probability density function.

In [probability theory](https://en.wikipedia.org/wiki/Probability_theory), a **probability density function** (**PDF**), **density function**, or **density** of an [absolutely continuous random variable](https://en.wikipedia.org/wiki/Absolutely_continuous_random_variable), is a [function](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)") whose value at any given sample (or point) in the [sample space](https://en.wikipedia.org/wiki/Sample_space) (the set of possible values taken by the random variable) can be interpreted as providing a *[relative likelihood](https://en.wikipedia.org/wiki/Relative_likelihood)* that the value of the random variable would be equal to that sample. Probability density is the probability per unit length, in other words. The *absolute likelihood* for a continuous [random variable](https://en.wikipedia.org/wiki/Random_variable) to take on any particular value is zero, given there is an [infinite set](https://en.wikipedia.org/wiki/Infinite_set) of possible values to begin with. Therefore, the value of the PDF at two different samples can be used to infer, in any particular draw of the random variable, how much more likely it is that the random variable would be close to one sample compared to the other sample.

More precisely, the PDF is used to specify the probability of the [random variable](https://en.wikipedia.org/wiki/Random_variable) falling *within a particular range of values*, as opposed to taking on any one value. This probability is given by the [integral](https://en.wikipedia.org/wiki/Integral) of a continuous variable's PDF over that range, where the integral is the nonnegative area under the density function between the lowest and greatest values of the range. The PDF is nonnegative everywhere, and the area under the entire curve is equal to one, such that the probability of the random variable falling within the set of possible values is 100%.

The terms *probability distribution function* and *probability function* can also denote the probability density function. However, this use is not standard among probabilists and statisticians. In other sources, "probability distribution function" may be used when the [probability distribution](https://en.wikipedia.org/wiki/Probability_distribution) is defined as a function over general sets of values or it may refer to the [[Cumulative Distribution Function]] (CDF), or it may be a [probability mass function](https://en.wikipedia.org/wiki/Probability_mass_function) (PMF) rather than the density. *Density function* itself is also used for the probability mass function, leading to further confusion. In general the PMF is used in the context of [discrete random variables](https://en.wikipedia.org/wiki/Continuous_or_discrete_variable#Discrete_variable) (random variables that take values on a [countable set](https://en.wikipedia.org/wiki/Countable_set)), while the PDF is used in the context of continuous random variables. Both PMF and PDF are fundamental concepts in [statistical inference](https://en.wikipedia.org/wiki/Statistical_inference).

## Example

![[media/d52a3b14a1829e43b048bd65742c3312a7023adb.png]]
Examples of four continuous probability density functions.

Suppose bacteria of a certain species typically live 20 to 30 hours. The probability that a bacterium lives *exactly* 5 hours is equal to zero. A lot of bacteria live for approximately 5 hours, but there is no chance that any given bacterium dies at exactly 5.00... hours. However, the probability that the bacterium dies between 5 hours and 5.01 hours is quantifiable. Suppose the answer is 0.02 (i.e., 2%). Then, the probability that the bacterium dies between 5 hours and 5.001 hours should be about 0.002, since this time interval is one-tenth as long as the previous. The probability that the bacterium dies between 5 hours and 5.0001 hours should be about 0.0002, and so on.

In this example, the ratio (probability of living during an interval) / (duration of the interval) is approximately constant, and equal to 2 per hour (or 2 hour<sup>−1</sup>). For example, there is 0.02 probability of dying in the 0.01-hour interval between 5 and 5.01 hours, and (0.02 probability / 0.01 hours) = 2 hour<sup>−1</sup>. This quantity 2 hour<sup>−1</sup> is called the probability density for dying at around 5 hours. Therefore, the probability that the bacterium dies at 5 hours can be written as (2 hour<sup>−1</sup>) *dt*. This is the probability that the bacterium dies within an infinitesimal window of time around 5 hours, where *dt* is the duration of this window. For example, the probability that it lives longer than 5 hours, but shorter than (5 hours + 1 nanosecond), is (2 hour<sup>−1</sup>)×(1 nanosecond) ≈ 6×10<sup>−13</sup> (using the [unit conversion](https://en.wikipedia.org/wiki/Conversion_of_units) 3.6×10<sup>12</sup> nanoseconds = 1 hour).

There is a probability density function *f* with *f*(5 hours) = 2 hour<sup>−1</sup>. The [integral](https://en.wikipedia.org/wiki/Integral) of *f* over any window of time (not only infinitesimal windows but also large windows) is the probability that the bacterium dies in that window.

## Absolutely continuous univariate distributions

A probability density function is most commonly associated with [absolutely continuous](https://en.wikipedia.org/wiki/Continuous_probability_distribution) [univariate distributions](https://en.wikipedia.org/wiki/Univariate_distribution). A [random variable](https://en.wikipedia.org/wiki/Random_variable) $X$ has density $f_{X}$, where $f_{X}$ is a non-negative [Lebesgue-integrable](https://en.wikipedia.org/wiki/Lebesgue_integration) function, if: 

$$
\Pr[a\leq X\leq b]=\int _{a}^{b}f_{X}(x)\,dx.
$$

Hence, if $F_{X}$ is the [[Cumulative Distribution Function]] of $X$, then: 

$$
F_{X}(x)=\int _{-\infty }^{x}f_{X}(u)\,du,
$$

 and (if $F_{X}$ is differentiable at $x$) 

$$
f_{X}(x)={\frac {d}{dx}}F_{X}(x).
$$

Intuitively, one can think of $f_{X}(x)\,dx$ as being the probability of $X$ falling within the infinitesimal [interval](https://en.wikipedia.org/wiki/Interval_(mathematics) "Interval (mathematics)") $[x,x+dx]$.

## Formal definition

(*This definition may be extended to any probability distribution using the [measure-theoretic](https://en.wikipedia.org/wiki/Measure_theory) [[Probability Axioms|definition of probability]].*)

A [random variable](https://en.wikipedia.org/wiki/Random_variable) $X$ with values in a [measurable space](https://en.wikipedia.org/wiki/Measurable_space) $({\mathcal {X}},{\mathcal {A}})$ (usually $\mathbb {R} ^{n}$ with the [Borel sets](https://en.wikipedia.org/wiki/Borel_set) as measurable subsets) has as [probability distribution](https://en.wikipedia.org/wiki/Probability_distribution#Formal_definition) the [pushforward measure](https://en.wikipedia.org/wiki/Pushforward_measure) *X*<sub>∗</sub>*P* on $({\mathcal {X}},{\mathcal {A}})$: the **density** of $X$ with respect to a reference measure $\mu$ on $({\mathcal {X}},{\mathcal {A}})$ is the [Radon–Nikodym derivative](https://en.wikipedia.org/wiki/Radon%E2%80%93Nikodym_derivative): 

$$
f={\frac {dX_{*}P}{d\mu }}.
$$

That is, *f* is any measurable function with the property that: 

$$
\Pr[X\in A]=\int _{X^{-1}A}\,dP=\int _{A}f\,d\mu
$$

 for any measurable set $A\in {\mathcal {A}}.$

### Discussion

In the [continuous univariate case above](#Absolutely_continuous_univariate_distributions), the reference measure is the [Lebesgue measure](https://en.wikipedia.org/wiki/Lebesgue_measure). The [probability mass function](https://en.wikipedia.org/wiki/Probability_mass_function) of a [discrete random variable](https://en.wikipedia.org/wiki/Discrete_random_variable) is the density with respect to the [counting measure](https://en.wikipedia.org/wiki/Counting_measure) over the sample space (usually the set of [integers](https://en.wikipedia.org/wiki/Integer), or some subset thereof).

It is not possible to define a density with reference to an arbitrary measure (e.g. one can not choose the counting measure as a reference for a continuous random variable). Furthermore, when it does exist, the density is almost unique, meaning that any two such densities coincide [almost everywhere](https://en.wikipedia.org/wiki/Almost_everywhere).

## Further details

Unlike a probability, a probability density function can take on values greater than one; for example, the [continuous uniform distribution](https://en.wikipedia.org/wiki/Continuous_uniform_distribution) on the interval \[0, 1/2\] has probability density *f*(*x*) = 2 for 0 ≤ *x* ≤ 1/2 and *f*(*x*) = 0 elsewhere.

The [standard normal distribution](https://en.wikipedia.org/wiki/Normal_distribution#Standard_normal_distribution) has probability density

$$
f(x)={\frac {1}{\sqrt {2\pi }}}\,e^{-x^{2}/2}.
$$

If a random variable *X* is given and its distribution admits a probability density function *f*, then the [expected value](https://en.wikipedia.org/wiki/Expected_value) of *X* (if the expected value exists) can be calculated as

$$
\operatorname {E} [X]=\int _{-\infty }^{\infty }x\,f(x)\,dx.
$$

Not every probability distribution has a density function: the distributions of [discrete random variables](https://en.wikipedia.org/wiki/Discrete_random_variable) do not; nor does the [Cantor distribution](https://en.wikipedia.org/wiki/Cantor_distribution), even though it has no discrete component, i.e., does not assign positive probability to any individual point.

A distribution has a density function if its [[Cumulative Distribution Function]] *F*(*x*) is [absolutely continuous](https://en.wikipedia.org/wiki/Absolute_continuity). In this case: *F* is [almost everywhere](https://en.wikipedia.org/wiki/Almost_everywhere) [differentiable](https://en.wikipedia.org/wiki/Derivative), and its derivative can be used as probability density:

$$
{\frac {d}{dx}}F(x)=f(x).
$$

If a probability distribution admits a density, then the probability of every one-point set {*a*} is zero; the same holds for finite and countable sets.

Two probability densities *f* and *g* represent the same [probability distribution](https://en.wikipedia.org/wiki/Probability_distribution) precisely if they differ only on a set of [Lebesgue](https://en.wikipedia.org/wiki/Lebesgue_measure) [measure zero](https://en.wikipedia.org/wiki/Measure_zero).

In the field of [statistical physics](https://en.wikipedia.org/wiki/Statistical_physics), a non-formal reformulation of the relation above between the derivative of the cumulative distribution function and the probability density function is generally used as the definition of the probability density function. This alternate definition is the following:

If *dt* is an infinitely small number, the probability that *X* is included within the interval (*t*, *t* + *dt*) is equal to *f*(*t*) *dt*, or: 

$$
\Pr(t<X<t+dt)=f(t)\,dt.
$$

## Link between discrete and continuous distributions

It is possible to represent certain discrete random variables as well as random variables involving both a continuous and a discrete part with a [generalized](https://en.wikipedia.org/wiki/Generalized_function) probability density function using the [Dirac delta function](https://en.wikipedia.org/wiki/Dirac_delta_function). (This is not possible with a probability density function in the sense defined above, it may be done with a [distribution](https://en.wikipedia.org/wiki/Distribution_(mathematics)).) For example, consider a binary discrete [random variable](https://en.wikipedia.org/wiki/Random_variable) having the [Rademacher distribution](https://en.wikipedia.org/wiki/Rademacher_distribution)—that is, taking −1 or 1 for values, with probability 1⁄2 each. The density of probability associated with this variable is: 

$$
f(t)={\frac {1}{2}}(\delta (t+1)+\delta (t-1)).
$$

More generally, if a discrete variable can take n different values among real numbers, then the associated probability density function is: 

$$
f(t)=\sum _{i=1}^{n}p_{i}\,\delta (t-x_{i}),
$$

 where $x_{1},\ldots ,x_{n}$ are the discrete values accessible to the variable and $p_{1},\ldots ,p_{n}$ are the probabilities associated with these values.

This substantially unifies the treatment of discrete and continuous probability distributions. The above expression allows for determining statistical characteristics of such a discrete variable (such as the [mean](https://en.wikipedia.org/wiki/Mean), [variance](https://en.wikipedia.org/wiki/Variance), and [kurtosis](https://en.wikipedia.org/wiki/Kurtosis)), starting from the formulas given for a continuous distribution of the probability.

## Families of densities

It is common for probability density functions (and [probability mass functions](https://en.wikipedia.org/wiki/Probability_mass_function)) to be parametrized—that is, to be characterized by unspecified [parameters](https://en.wikipedia.org/wiki/Parameter). For example, the [normal distribution](https://en.wikipedia.org/wiki/Normal_distribution) is parametrized in terms of the [mean](https://en.wikipedia.org/wiki/Mean) and the [variance](https://en.wikipedia.org/wiki/Variance), denoted by $\mu$ and $\sigma ^{2}$ respectively, giving the family of densities 

$$
f(x;\mu ,\sigma ^{2})={\frac {1}{\sigma {\sqrt {2\pi }}}}e^{-{\frac {1}{2}}\left({\frac {x-\mu }{\sigma }}\right)^{2}}.
$$

 Different values of the parameters describe different distributions of different [random variables](https://en.wikipedia.org/wiki/Random_variable) on the same [sample space](https://en.wikipedia.org/wiki/Sample_space) (the same set of all possible values of the variable); this sample space is the domain of the family of random variables that this family of distributions describes. A given set of parameters describes a single distribution within the family sharing the functional form of the density. From the perspective of a given distribution, the parameters are constants, and terms in a density function that contain only parameters, but not variables, are part of the [normalization factor](https://en.wikipedia.org/wiki/Normalization_factor) of a distribution (the multiplicative factor that ensures that the area under the density—the probability of *something* in the domain occurring— equals 1). This normalization factor is outside the [kernel](https://en.wikipedia.org/wiki/Kernel_(statistics) "Kernel (statistics)") of the distribution.

Since the parameters are constants, reparametrizing a density in terms of different parameters to give a characterization of a different random variable in the family, means simply substituting the new parameter values into the formula in place of the old ones.

## Densities associated with multiple variables

For continuous [random variables](https://en.wikipedia.org/wiki/Random_variable) *X*<sub>1</sub>, ..., *X<sub>n</sub>*, it is also possible to define a probability density function associated to the set as a whole, often called **joint probability density function**. This density function is defined as a function of the n variables, such that, for any domain D in the n-dimensional space of the values of the variables *X*<sub>1</sub>, ..., *X<sub>n</sub>*, the probability that a realisation of the set variables falls inside the domain D is 

$$
\Pr \left(X_{1},\ldots ,X_{n}\in D\right)=\int _{D}f_{X_{1},\ldots ,X_{n}}(x_{1},\ldots ,x_{n})\,dx_{1}\cdots dx_{n}.
$$

If *F*(*x*<sub>1</sub>, ..., *x*<sub>*n*</sub>) = Pr(*X*<sub>1</sub> ≤ *x*<sub>1</sub>, ..., *X*<sub>*n*</sub> ≤ *x*<sub>*n*</sub>) is the [[Cumulative Distribution Function]] of the vector (*X*<sub>1</sub>, ..., *X*<sub>*n*</sub>), then the joint probability density function can be computed as a partial derivative 

$$
f(x)=\left.{\frac {\partial ^{n}F}{\partial x_{1}\cdots \partial x_{n}}}\right|_{x}
$$

### Marginal densities

For *i* = 1, 2, ..., *n*, let *f*<sub>*X*<sub>*i*</sub></sub>(*x*<sub>*i*</sub>) be the probability density function associated with variable *X<sub>i</sub>* alone. This is called the marginal density function, and can be deduced from the probability density associated with the random variables *X*<sub>1</sub>, ..., *X<sub>n</sub>* by integrating over all values of the other *n* − 1 variables: 

$$
f_{X_{i}}(x_{i})=\int f(x_{1},\ldots ,x_{n})\,dx_{1}\cdots dx_{i-1}\,dx_{i+1}\cdots dx_{n}.
$$

### Independence

Continuous random variables *X*<sub>1</sub>, ..., *X<sub>n</sub>* admitting a joint density are all [independent](https://en.wikipedia.org/wiki/Statistical_independence) from each other if 

$$
f_{X_{1},\ldots ,X_{n}}(x_{1},\ldots ,x_{n})=f_{X_{1}}(x_{1})\cdots f_{X_{n}}(x_{n}).
$$

### Corollary

If the joint probability density function of a vector of n random variables can be factored into a product of n functions of one variable 

$$
f_{X_{1},\ldots ,X_{n}}(x_{1},\ldots ,x_{n})=f_{1}(x_{1})\cdots f_{n}(x_{n}),
$$

 (where each *f<sub>i</sub>* is not necessarily a density) then the n variables in the set are all [independent](https://en.wikipedia.org/wiki/Statistical_independence) from each other, and the marginal probability density function of each of them is given by 

$$
f_{X_{i}}(x_{i})={\frac {f_{i}(x_{i})}{\int f_{i}(x)\,dx}}.
$$

### Example

This elementary example illustrates the above definition of multidimensional probability density functions in the simple case of a function of a set of two variables. Let us call ${\vec {R}}$ a 2-dimensional random vector of coordinates (*X*, *Y*): the probability to obtain ${\vec {R}}$ in the quarter plane of positive *x* and *y* is 

$$
\Pr \left(X>0,Y>0\right)=\int _{0}^{\infty }\int _{0}^{\infty }f_{X,Y}(x,y)\,dx\,dy.
$$

## Function of random variables and change of variables in the probability density function

If the probability density function of a random variable (or vector) *X* is given as *f<sub>X</sub>*(*x*), it is possible (but often not necessary; see below) to calculate the probability density function of some variable *Y* = *g*(*X*). This is also called a "change of variable" and is in practice used to generate a random variable of arbitrary shape *f*<sub>*g*(*X*)</sub> = *f<sub>Y</sub>* using a known (for instance, uniform) random number generator.

It is tempting to think that in order to find the expected value E(*g*(*X*)), one must first find the probability density *f*<sub>*g*(*X*)</sub> of the new random variable *Y* = *g*(*X*). However, rather than computing 

$$
\operatorname {E} {\big (}g(X){\big )}=\int _{-\infty }^{\infty }yf_{g(X)}(y)\,dy,
$$

 one may find instead 

$$
\operatorname {E} {\big (}g(X){\big )}=\int _{-\infty }^{\infty }g(x)f_{X}(x)\,dx.
$$

The values of the two integrals are the same in all cases in which both *X* and *g*(*X*) actually have probability density functions. It is not necessary that *g* be a [one-to-one function](https://en.wikipedia.org/wiki/One-to-one_function). In some cases the latter integral is computed much more easily than the former. See [Law of the unconscious statistician](https://en.wikipedia.org/wiki/Law_of_the_unconscious_statistician).

### Scalar to scalar

Let $g:\mathbb {R} \to \mathbb {R}$ be a [monotonic function](https://en.wikipedia.org/wiki/Monotonic_function), then the resulting density function is 

$$
f_{Y}(y)=f_{X}{\big (}g^{-1}(y){\big )}\left|{\frac {d}{dy}}{\big (}g^{-1}(y){\big )}\right|.
$$

Here *g*<sup>−1</sup> denotes the [inverse function](https://en.wikipedia.org/wiki/Inverse_function).

This follows from the fact that the probability contained in a differential area must be invariant under change of variables. That is, 

$$
\left|f_{Y}(y)\,dy\right|=\left|f_{X}(x)\,dx\right|,
$$

 or 

$$
f_{Y}(y)=\left|{\frac {dx}{dy}}\right|f_{X}(x)=\left|{\frac {d}{dy}}(x)\right|f_{X}(x)=\left|{\frac {d}{dy}}{\big (}g^{-1}(y){\big )}\right|f_{X}{\big (}g^{-1}(y){\big )}={\left|\left(g^{-1}\right)'(y)\right|}\cdot f_{X}{\big (}g^{-1}(y){\big )}.
$$

For functions that are not monotonic, the probability density function for y is 

$$
\sum _{k=1}^{n(y)}\left|{\frac {d}{dy}}g_{k}^{-1}(y)\right|\cdot f_{X}{\big (}g_{k}^{-1}(y){\big )},
$$

 where *n*(*y*) is the number of solutions in x for the equation $g(x)=y$, and $g_{k}^{-1}(y)$ are these solutions.

### Vector to vector

Suppose **x** is an n-dimensional random variable with joint density *f*. If ***y*** = *G*(***x***), where *G* is a [bijective](https://en.wikipedia.org/wiki/Bijective), [differentiable function](https://en.wikipedia.org/wiki/Differentiable_function), then ***y*** has density  *p*<sub>***Y***</sub>: 

$$
p_{Y}(\mathbf {y} )=f{\Bigl (}G^{-1}(\mathbf {y} ){\Bigr )}\left|\det \left[\left.{\frac {dG^{-1}(\mathbf {z} )}{d\mathbf {z} }}\right|_{\mathbf {z} =\mathbf {y} }\right]\right|
$$

 with the differential regarded as the [Jacobian](https://en.wikipedia.org/wiki/Jacobian_matrix_and_determinant) of the inverse of *G*(⋅), evaluated at ***y***.

For example, in the 2-dimensional case **x** = (*x*<sub>1</sub>, *x*<sub>2</sub>), suppose the transform *G* is given as *y*<sub>1</sub> = *G*<sub>1</sub>(*x*<sub>1</sub>, *x*<sub>2</sub>), *y*<sub>2</sub> = *G*<sub>2</sub>(*x*<sub>1</sub>, *x*<sub>2</sub>) with inverses *x*<sub>1</sub> = *G*<sub>1</sub><sup>−1</sup>(*y*<sub>1</sub>, *y*<sub>2</sub>), *x*<sub>2</sub> = *G*<sub>2</sub><sup>−1</sup>(*y*<sub>1</sub>, *y*<sub>2</sub>). The joint distribution for **y** = (*y*<sub>1</sub>, y<sub>2</sub>) has density 

$$
p_{Y_{1},Y_{2}}(y_{1},y_{2})=f_{X_{1},X_{2}}{\big (}G_{1}^{-1}(y_{1},y_{2}),G_{2}^{-1}(y_{1},y_{2}){\big )}\left\vert {\frac {\partial G_{1}^{-1}}{\partial y_{1}}}{\frac {\partial G_{2}^{-1}}{\partial y_{2}}}-{\frac {\partial G_{1}^{-1}}{\partial y_{2}}}{\frac {\partial G_{2}^{-1}}{\partial y_{1}}}\right\vert .
$$

### Vector to scalar

Let $V:\mathbb {R} ^{n}\to \mathbb {R}$ be a differentiable function and $X$ be a random vector taking values in $\mathbb {R} ^{n}$, $f_{X}$ be the probability density function of $X$ and $\delta (\cdot )$ be the [Dirac delta](https://en.wikipedia.org/wiki/Dirac_delta) function. It is possible to use the formulas above to determine $f_{Y}$, the probability density function of $Y=V(X)$, which will be given by 

$$
f_{Y}(y)=\int _{\mathbb {R} ^{n}}f_{X}(\mathbf {x} )\delta {\big (}y-V(\mathbf {x} ){\big )}\,d\mathbf {x} .
$$

This result leads to the [law of the unconscious statistician](https://en.wikipedia.org/wiki/Law_of_the_unconscious_statistician): 

$$
{\begin{aligned}\operatorname {E} _{Y}[Y]&=\int _{\mathbb {R} }yf_{Y}(y)\,dy\\&=\int _{\mathbb {R} }y\int _{\mathbb {R} ^{n}}f_{X}(\mathbf {x} )\delta {\big (}y-V(\mathbf {x} ){\big )}\,d\mathbf {x} \,dy\\&=\int _{{\mathbb {R} }^{n}}\int _{\mathbb {R} }yf_{X}(\mathbf {x} )\delta {\big (}y-V(\mathbf {x} ){\big )}\,dy\,d\mathbf {x} \\&=\int _{\mathbb {R} ^{n}}V(\mathbf {x} )f_{X}(\mathbf {x} )\,d\mathbf {x} =\operatorname {E} _{X}[V(X)].\end{aligned}}
$$

*Proof:*

Let $Z$ be a collapsed random variable with probability density function $p_{Z}(z)=\delta (z)$ (i.e., a constant equal to zero). Let the random vector ${\tilde {X}}$ and the transform $H$ be defined as 

$$
H(Z,X)={\begin{bmatrix}Z+V(X)\\X\end{bmatrix}}={\begin{bmatrix}Y\\{\tilde {X}}\end{bmatrix}}.
$$

It is clear that $H$ is a bijective mapping, and the Jacobian of $H^{-1}$ is given by: 

$$
{\frac {dH^{-1}(y,{\tilde {\mathbf {x} }})}{dy\,d{\tilde {\mathbf {x} }}}}={\begin{bmatrix}1&-{\frac {dV({\tilde {\mathbf {x} }})}{d{\tilde {\mathbf {x} }}}}\\\mathbf {0} _{n\times 1}&\mathbf {I} _{n\times n}\end{bmatrix}},
$$

 which is an upper [triangular matrix](https://en.wikipedia.org/wiki/Triangular_matrix) with ones on the [main diagonal](https://en.wikipedia.org/wiki/Main_diagonal), therefore its determinant is 1. Applying the change of variable theorem from the previous section we obtain that 

$$
f_{Y,X}(y,x)=f_{X}(\mathbf {x} )\delta {\big (}y-V(\mathbf {x} ){\big )},
$$

 which if marginalized over $x$ leads to the desired probability density function.

## Sums of independent random variables

The probability density function of the sum of two [independent](https://en.wikipedia.org/wiki/Statistical_independence) random variables *U* and *V*, each of which has a probability density function, is the [convolution](https://en.wikipedia.org/wiki/Convolution) of their separate density functions: 

$$
f_{U+V}(x)=\int _{-\infty }^{\infty }f_{U}(y)f_{V}(x-y)\,dy=\left(f_{U}*f_{V}\right)(x)
$$

It is possible to generalize the previous relation to a sum of N independent random variables, with densities *U*<sub>1</sub>, ..., *U<sub>N</sub>*: 

$$
f_{U_{1}+\cdots +U}(x)=\left(f_{U_{1}}*\cdots *f_{U_{N}}\right)(x)
$$

This can be derived from a two-way change of variables involving *Y* = *U* + *V* and *Z* = *V*, similarly to the example below for the quotient of independent random variables.

## Products and quotients of independent random variables

Given two independent random variables *U* and *V*, each of which has a probability density function, the density of the product *Y* = *UV* and quotient *Y* = *U*/*V* can be computed by a change of variables.

### Example: Quotient distribution

To compute the quotient *Y* = *U*/*V* of two independent random variables *U* and *V*, define the following transformation: 

$$
{\begin{aligned}Y&=U/V\\[1ex]Z&=V\end{aligned}}
$$

Then, the joint density *p*(*y*,*z*) can be computed by a change of variables from *U*,*V* to *Y*,*Z*, and *Y* can be derived by [marginalizing out](https://en.wikipedia.org/wiki/Marginalizing_out) *Z* from the joint density.

The inverse transformation is 

$$
{\begin{aligned}U&=YZ\\V&=Z\end{aligned}}
$$

The [absolute value](https://en.wikipedia.org/wiki/Absolute_value) of the [[Jacobian Matrix]] determinant $J(U,V\mid Y,Z)$ of this transformation is: 

$$
\left|\det {\begin{bmatrix}{\frac {\partial u}{\partial y}}&{\frac {\partial u}{\partial z}}\\{\frac {\partial v}{\partial y}}&{\frac {\partial v}{\partial z}}\end{bmatrix}}\right|=\left|\det {\begin{bmatrix}z&y\\0&1\end{bmatrix}}\right|=|z|.
$$

Thus: 

$$
p(y,z)=p(u,v)\,J(u,v\mid y,z)=p(u)\,p(v)\,J(u,v\mid y,z)=p_{U}(yz)\,p_{V}(z)\,|z|.
$$

And the distribution of *Y* can be computed by [marginalizing out](https://en.wikipedia.org/wiki/Marginalizing_out) *Z*: 

$$
p(y)=\int _{-\infty }^{\infty }p_{U}(yz)\,p_{V}(z)\,|z|\,dz
$$

This method crucially requires that the transformation from *U*,*V* to *Y*,*Z* be [bijective](https://en.wikipedia.org/wiki/Bijective). The above transformation meets this because *Z* can be mapped directly back to *V*, and for a given *V* the quotient *U*/*V* is [monotonic](https://en.wikipedia.org/wiki/Monotonic). This is similarly the case for the sum *U* + *V*, difference *U* − *V* and product *UV*.

Exactly the same method can be used to compute the distribution of other functions of multiple independent random variables.

### Example: Quotient of two standard normals

Given two [standard normal](https://en.wikipedia.org/wiki/Standard_normal_distribution) variables *U* and *V*, the quotient can be computed as follows. First, the variables have the following density functions: 

$$
{\begin{aligned}p(u)&={\frac {1}{\sqrt {2\pi }}}e^{-{u^{2}}/{2}}\\[1ex]p(v)&={\frac {1}{\sqrt {2\pi }}}e^{-{v^{2}}/{2}}\end{aligned}}
$$

We transform as described above: 

$$
{\begin{aligned}Y&=U/V\\[1ex]Z&=V\end{aligned}}
$$

This leads to: 

$$
{\begin{aligned}p(y)&=\int _{-\infty }^{\infty }p_{U}(yz)\,p_{V}(z)\,|z|\,dz\\[5pt]&=\int _{-\infty }^{\infty }{\frac {1}{\sqrt {2\pi }}}e^{-{\frac {1}{2}}y^{2}z^{2}}{\frac {1}{\sqrt {2\pi }}}e^{-{\frac {1}{2}}z^{2}}|z|\,dz\\[5pt]&=\int _{-\infty }^{\infty }{\frac {1}{2\pi }}e^{-{\frac {1}{2}}\left(y^{2}+1\right)z^{2}}|z|\,dz\\[5pt]&=2\int _{0}^{\infty }{\frac {1}{2\pi }}e^{-{\frac {1}{2}}\left(y^{2}+1\right)z^{2}}z\,dz\\[5pt]&=\int _{0}^{\infty }{\frac {1}{\pi }}e^{-\left(y^{2}+1\right)u}\,du&&u={\tfrac {1}{2}}z^{2}\\[5pt]&=\left.-{\frac {1}{\pi \left(y^{2}+1\right)}}e^{-\left(y^{2}+1\right)u}\right|_{u=0}^{\infty }\\[5pt]&={\frac {1}{\pi \left(y^{2}+1\right)}}\end{aligned}}
$$

This is the density of a standard [Cauchy distribution](https://en.wikipedia.org/wiki/Cauchy_distribution).

## See also

- [Density estimation](https://en.wikipedia.org/wiki/Density_estimation) – Estimate of an unobservable underlying probability density function
- [Kernel density estimation](https://en.wikipedia.org/wiki/Kernel_density_estimation) – EstimatorPages displaying short descriptions with no spaces
- [Likelihood function](https://en.wikipedia.org/wiki/Likelihood_function) – Function related to statistics and probability theory
- [List of probability distributions](https://en.wikipedia.org/wiki/List_of_probability_distributions)
- [Probability amplitude](https://en.wikipedia.org/wiki/Probability_amplitude) – Complex number whose squared absolute value is a probability
- [Probability mass function](https://en.wikipedia.org/wiki/Probability_mass_function) – Discrete-variable probability distribution
- [Secondary measure](https://en.wikipedia.org/wiki/Secondary_measure) – Concept in mathematics
- Uses as *position probability density*:
  - [Atomic orbital](https://en.wikipedia.org/wiki/Atomic_orbital) – Function describing an electron in an atom
  - [Home range](https://en.wikipedia.org/wiki/Home_range) – Area in which an animal lives and moves

## References

1.  ["AP Statistics Review - Density Curves and the Normal Distributions"](https://web.archive.org/web/20150402183703/http://apstatsreview.tumblr.com/post/50058615236/density-curves-and-the-normal-distributions). Archived from [the original](https://apstatsreview.tumblr.com/post/50058615236/density-curves-and-the-normal-distributions) on 2 April 2015. Retrieved 16 March 2015.
2.  Grinstead, Charles M.; Snell, J. Laurie (2009). ["Conditional Probability - Discrete Conditional"](https://www.dartmouth.edu/~chance/teaching_aids/books_articles/probability_book/Chapter4.pdf) (PDF). *Grinstead & Snell's Introduction to Probability*. Orange Grove Texts. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1616100469](https://en.wikipedia.org/wiki/Special:BookSources/978-1616100469). [Archived](https://web.archive.org/web/20030425090244/http://www.dartmouth.edu/~chance/teaching_aids/books_articles/probability_book/Chapter4.pdf) (PDF) from the original on 2003-04-25. Retrieved 2019-07-25.
3.  ["probability - Is a uniformly random number over the real line a valid distribution?"](https://stats.stackexchange.com/q/541479). *Cross Validated*. Retrieved 2021-10-06.
4.  Ord, J.K. (1972) *Families of Frequency Distributions*, Griffin. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-85264-137-0](https://en.wikipedia.org/wiki/Special:BookSources/0-85264-137-0) (for example, Table 5.1 and Example 5.4)
5.  Scalas, Enrico (2025). [Introduction to Probability Theory for Economists](https://www.lem.sssup.it/phd/documents/probpisanew.pdf) (PDF). self-published. p. 28. [Archived](https://web.archive.org/web/20241210231824/https://www.lem.sssup.it/phd/documents/probpisanew.pdf) (PDF) from the original on Dec 10, 2024. Retrieved July 30, 2025.
6.  Siegrist, Kyle (5 May 2020). ["Transformations of Random Variables"](https://stats.libretexts.org/Bookshelves/Probability_Theory/Probability_Mathematical_Statistics_and_Stochastic_Processes_%28Siegrist%29/03%3A_Distributions/3.07%3A_Transformations_of_Random_Variables#The_Change_of_Variables_Formula). LibreTexts Statistics. Retrieved 22 December 2023.
7.  Devore, Jay L.; Berk, Kenneth N. (2007). [Modern Mathematical Statistics with Applications](https://books.google.com/books?id=3X7Qca6CcfkC&pg=PA263). Cengage. p. 263. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-534-40473-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-534-40473-4).
8.  David, Stirzaker (2007-01-01). *Elementary Probability*. Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0521534284](https://en.wikipedia.org/wiki/Special:BookSources/978-0521534284). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [851313783](https://search.worldcat.org/oclc/851313783).

## Further reading

- [Billingsley, Patrick](https://en.wikipedia.org/wiki/Patrick_Billingsley) (1979). *Probability and Measure*. New York, Toronto, London: John Wiley and Sons. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-00710-2](https://en.wikipedia.org/wiki/Special:BookSources/0-471-00710-2).
- [Casella, George](https://en.wikipedia.org/wiki/George_Casella); [Berger, Roger L.](https://en.wikipedia.org/wiki/Roger_Lee_Berger) (2002). *Statistical Inference* (Second ed.). Thomson Learning. pp. 34–37. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-534-24312-6](https://en.wikipedia.org/wiki/Special:BookSources/0-534-24312-6).
- Stirzaker, David (2003). [Elementary Probability](https://archive.org/details/elementaryprobab0000stir). Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-42028-8](https://en.wikipedia.org/wiki/Special:BookSources/0-521-42028-8). Chapters 7 to 9 are about continuous variables.

## External links

- Ushakov, N.G. (2001) \[1994\], ["Density of a probability distribution"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society)
- [Weisstein, Eric W.](https://en.wikipedia.org/wiki/Eric_W._Weisstein) ["Probability density function"](https://mathworld.wolfram.com/ProbabilityDensityFunction.html). *[MathWorld](https://en.wikipedia.org/wiki/MathWorld)*.
