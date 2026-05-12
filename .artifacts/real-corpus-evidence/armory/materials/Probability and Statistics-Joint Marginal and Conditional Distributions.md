[[probability-statistics.base]]

> Source: [Joint probability distribution](https://en.wikipedia.org/wiki/Joint_probability_distribution)
> License: Wikipedia content is available under CC BY-SA 4.0.

![[media/587fdfcec94071c288a97b740c3ae7d3bfbd51ec.png]]

$X$

$Y$

$p(X)$

$p(Y)$

![[media/587fdfcec94071c288a97b740c3ae7d3bfbd51ec.png]]

Many sample observations (black) are shown from a joint probability distribution. The marginal densities are shown as well (in blue and in red).

Given [random variables](https://en.wikipedia.org/wiki/Random_variable) $X,Y,\ldots$, that are defined on the same [probability space](https://en.wikipedia.org/wiki/Probability_space), the **multivariate** or **joint probability distribution** for $X,Y,\ldots$ is a [probability distribution](https://en.wikipedia.org/wiki/Probability_distribution) that gives the probability that each of $X,Y,\ldots$ falls in any particular range or discrete set of values specified for that variable. In the case of only two random variables, this is called a [bivariate distribution](https://en.wikipedia.org/wiki/Bivariate_distribution), but the concept generalizes to any number of random variables.

The joint probability distribution can be expressed in terms of a joint [[Cumulative Distribution Function]] and either in terms of a joint [[Probability Density Function]] (in the case of [continuous variables](https://en.wikipedia.org/wiki/Continuous_variable)) or joint [probability mass function](https://en.wikipedia.org/wiki/Probability_mass_function) (in the case of [discrete](https://en.wikipedia.org/wiki/Discrete_probability_distribution) variables). These in turn can be used to find two other types of distributions: the [marginal distribution](https://en.wikipedia.org/wiki/Marginal_density) giving the probabilities for any one of the variables with no reference to any specific ranges of values for the other variables, and the [conditional probability distribution](https://en.wikipedia.org/wiki/Conditional_probability_distribution) giving the probabilities for any subset of the variables conditional on particular values of the remaining variables.

## Examples

### Draws from an urn

Each of two urns contains twice as many red balls as blue balls, and no others, and one ball is randomly selected from each urn, with the two draws independent of each other. Let $A$ and $B$ be discrete random variables associated with the outcomes of the draw from the first urn and second urn respectively. The probability of drawing a red ball from either of the urns is 2/3, and the probability of drawing a blue ball is 1/3. The joint probability distribution is presented in the following table:

|  |  |  |  |
|----|----|----|----|
|  | A=Red | A=Blue | P(B) |
| B=Red | (2/3)(2/3) = 4/9 | (1/3)(2/3) = 2/9 | 4/9 + 2/9 = 2/3 |
| B=Blue | (2/3)(1/3) = 2/9 | (1/3)(1/3) = 1/9 | 2/9 + 1/9 = 1/3 |
| P(A) | 4/9 + 2/9 = 2/3 | 2/9 + 1/9 = 1/3 |  |

Each of the four inner cells shows the probability of a particular combination of results from the two draws; these probabilities are the joint distribution. In any one cell the probability of a particular combination occurring is (since the draws are independent) the product of the probability of the specified result for A and the probability of the specified result for B. The probabilities in these four cells sum to 1, as with all probability distributions.

Moreover, the final row and the final column give the [marginal probability distribution](https://en.wikipedia.org/wiki/Marginal_probability_distribution) for A and the marginal probability distribution for B respectively. For example, for A the first of these cells gives the sum of the probabilities for A being red, regardless of which possibility for B in the column above the cell occurs, as 2/3. Thus the marginal probability distribution for $A$ gives $A$'s probabilities *unconditional* on $B$, in a margin of the table.

### Coin flips

Consider the flip of two [fair coins](https://en.wikipedia.org/wiki/Fair_coin); let $A$ and $B$ be discrete random variables associated with the outcomes of the first and second coin flips respectively. Each coin flip is a [Bernoulli trial](https://en.wikipedia.org/wiki/Bernoulli_trial) and has a [Bernoulli distribution](https://en.wikipedia.org/wiki/Bernoulli_distribution). If a coin displays "heads" then the associated random variable takes the value 1, and it takes the value 0 otherwise. The probability of each of these outcomes is 1/2, so the marginal (unconditional) density functions are

$$
{\begin{aligned}P(A)&=1/2\quad {\text{for}}\quad A\in \{0,1\};\\P(B)&=1/2\quad {\text{for}}\quad B\in \{0,1\}.\end{aligned}}
$$

The joint probability mass function of $A$ and $B$ defines probabilities for each pair of outcomes. All possible outcomes are 

$$
(A,B)\in \{(0,0),(0,1),(1,0),(1,1)\}.
$$

 Since each outcome is equally likely the joint probability mass function becomes 

$$
P(A,B)=1/4\quad {\text{for}}\quad A,B\in \{0,1\}.
$$

Since the coin flips are independent, the joint probability mass function is the product of the marginals: 

$$
P(A,B)=P(A)P(B)\quad {\text{for}}\quad A,B\in \{0,1\}.
$$

### Rolling a die

Consider the roll of a fair [die](https://en.wikipedia.org/wiki/Dice) and let $A=1$ if the number is even (i.e. 2, 4, or 6) and $A=0$ otherwise. Furthermore, let $B=1$ if the number is prime (i.e. 2, 3, or 5) and $B=0$ otherwise.

|     |     |     |     |     |     |     |
|-----|-----|-----|-----|-----|-----|-----|
|     | 1   | 2   | 3   | 4   | 5   | 6   |
| A   | 0   | 1   | 0   | 1   | 0   | 1   |
| B   | 0   | 1   | 1   | 0   | 1   | 0   |

Then, the joint distribution of $A$ and $B$, expressed as a probability mass function, is 

$$
{\begin{aligned}\mathrm {P} (A=0,B=0)&=P\{1\}={\frac {1}{6}},&\mathrm {P} (A=1,B=0)&=P\{4,6\}={\frac {2}{6}},\\\mathrm {P} (A=0,B=1)&=P\{3,5\}={\frac {2}{6}},&\mathrm {P} (A=1,B=1)&=P\{2\}={\frac {1}{6}}.\end{aligned}}
$$

These probabilities necessarily sum to 1, since the probability of *some* combination of $A$ and $B$ occurring is 1.

## Marginal probability distribution

If more than one random variable is defined in a random experiment, it is important to distinguish between the joint probability distribution of X and Y and the probability distribution of each variable individually. The individual probability distribution of a random variable is referred to as its marginal probability distribution. In general, the marginal probability distribution of X can be determined from the joint probability distribution of X and other random variables.

If the joint probability density function of random variable X and Y is $f_{X,Y}(x,y)$ , the marginal probability density function of X and Y, which defines the [marginal distribution](https://en.wikipedia.org/wiki/Marginal_distribution), is given by:

$$
{\begin{aligned}f_{X}(x)&=\int f_{X,Y}(x,y)\;dy\\f_{Y}(y)&=\int f_{X,Y}(x,y)\;dx\end{aligned}}
$$

where the first integral is over all points in the range of (X,Y) for which X=x and the second integral is over all points in the range of (X,Y) for which Y=y.

## Joint cumulative distribution function

For a pair of random variables $X,Y$, the joint cumulative distribution function (CDF) $F_{X,Y}$ is given by

$F_{X,Y}(x,y)=\operatorname {P} (X\leq x,Y\leq y)$   (Eq.1)

where the right-hand side represents the [probability](https://en.wikipedia.org/wiki/Probability) that the random variable $X$ takes on a value less than or equal to $x$ **and** that $Y$ takes on a value less than or equal to $y$.

For $N$ random variables $X_{1},\ldots ,X_{N}$, the joint CDF $F_{X_{1},\ldots ,X_{N}}$ is given by

$F_{X_{1},\ldots ,X_{N}}(x_{1},\ldots ,x_{N})=\operatorname {P} (X_{1}\leq x_{1},\ldots ,X_{N}\leq x_{N})$   (Eq.2)

Interpreting the $N$ random variables as a [random vector](https://en.wikipedia.org/wiki/Random_vector) $\mathbf {X} =(X_{1},\ldots ,X_{N})^{T}$ yields a shorter notation:

$$
F_{\mathbf {X} }(\mathbf {x} )=\operatorname {P} (X_{1}\leq x_{1},\ldots ,X_{N}\leq x_{N})
$$

## Joint density function or mass function

### Discrete case

The joint [probability mass function](https://en.wikipedia.org/wiki/Probability_mass_function) of two [discrete random variables](https://en.wikipedia.org/wiki/Discrete_random_variable) $X,Y$ is:

$p_{X,Y}(x,y)=\mathrm {P} (X=x\ \mathrm {and} \ Y=y)$   (Eq.3)

or written in terms of conditional distributions 

$$
p_{X,Y}(x,y)=\mathrm {P} (Y=y\mid X=x)\cdot \mathrm {P} (X=x)=\mathrm {P} (X=x\mid Y=y)\cdot \mathrm {P} (Y=y)
$$

 where $\mathrm {P} (Y=y\mid X=x)$ is the [probability](https://en.wikipedia.org/wiki/Conditional_probability) of $Y=y$ given that $X=x$.

The generalization of the preceding two-variable case is the joint probability distribution of $n$ discrete random variables $X_{1},X_{2},\dots ,X_{n}$ which is:

$p_{X_{1},\ldots ,X_{n}}(x_{1},\ldots ,x_{n})=\mathrm {P} (X_{1}=x_{1}{\text{ and }}\dots {\text{ and }}X_{n}=x_{n})$   (Eq.4)

or equivalently

$$
{\begin{aligned}p_{X_{1},\ldots ,X_{n}}(x_{1},\ldots ,x_{n})={}&\mathrm {P} (X_{1}=x_{1})\\&\cdot \mathrm {P} (X_{2}=x_{2}\mid X_{1}=x_{1})\\&\cdot \mathrm {P} (X_{3}=x_{3}\mid X_{1}=x_{1},X_{2}=x_{2})\\&\cdots \\&\cdot \mathrm {P} (X_{n}=x_{n}\mid X_{1}=x_{1},X_{2}=x_{2},\dots ,X_{n-1}=x_{n-1}).\end{aligned}}
$$

This identity is known as the [chain rule of probability](https://en.wikipedia.org/wiki/Chain_rule_(probability) "Chain rule (probability)").

Since these are probabilities, in the two-variable case

$$
\sum _{i}\sum _{j}\mathrm {P} (X=x_{i}\ \mathrm {and} \ Y=y_{j})=1,\,
$$

 which generalizes for $n\,$ discrete random variables $X_{1},X_{2},\dots ,X_{n}$ to

$$
\sum _{i}\sum _{j}\dots \sum _{k}\mathrm {P} (X_{1}=x_{1i},X_{2}=x_{2j},\dots ,X_{n}=x_{nk})=1.\;
$$

### Continuous case

The **joint [[Probability Density Function]]** $f_{X,Y}(x,y)$ for two [continuous random variables](https://en.wikipedia.org/wiki/Continuous_random_variable) is defined as the derivative of the joint cumulative distribution function (see **[Eq.1](#math_Eq.1)**):

$f_{X,Y}(x,y)={\frac {\partial ^{2}F_{X,Y}(x,y)}{\partial x\partial y}}$   (Eq.5)

This is equal to: 

$$
f_{X,Y}(x,y)=f_{Y\mid X}(y\mid x)f_{X}(x)=f_{X\mid Y}(x\mid y)f_{Y}(y)
$$

where $f_{Y\mid X}(y\mid x)$ and $f_{X\mid Y}(x\mid y)$ are the [conditional distributions](https://en.wikipedia.org/wiki/Conditional_distribution) of $Y$ given $X=x$ and of $X$ given $Y=y$ respectively, and $f_{X}(x)$ and $f_{Y}(y)$ are the [marginal distributions](https://en.wikipedia.org/wiki/Marginal_distribution) for $X$ and $Y$ respectively.

The definition extends naturally to more than two random variables:

$f_{X_{1},\ldots ,X_{n}}(x_{1},\ldots ,x_{n})={\frac {\partial ^{n}F_{X_{1},\ldots ,X_{n}}(x_{1},\ldots ,x_{n})}{\partial x_{1}\ldots \partial x_{n}}}$   (Eq.6)

Again, since these are probability distributions, one has 

$$
\int _{x}\int _{y}f_{X,Y}(x,y)\;dy\;dx=1
$$

 respectively 

$$
\int _{x_{1}}\ldots \int _{x_{n}}f_{X_{1},\ldots ,X_{n}}(x_{1},\ldots ,x_{n})\;dx_{n}\ldots \;dx_{1}=1
$$

### Mixed case

The "mixed joint density" may be defined where one or more random variables are continuous and the other random variables are discrete. With one variable of each type 

$$
f_{X,Y}(x,y)=f_{X\mid Y}(x\mid y)\mathrm {P} (Y=y)=\mathrm {P} (Y=y\mid X=x)f_{X}(x).
$$

 One example of a situation in which one may wish to find the cumulative distribution of one random variable which is continuous and another random variable which is discrete arises when one wishes to use a [logistic regression](https://en.wikipedia.org/wiki/Logistic_regression) in predicting the probability of a binary outcome Y conditional on the value of a continuously distributed outcome $X$. One *must* use the "mixed" joint density when finding the cumulative distribution of this binary outcome because the input variables $(X,Y)$ were initially defined in such a way that one could not collectively assign it either a probability density function or a probability mass function. Formally, $f_{X,Y}(x,y)$ is the probability density function of $(X,Y)$ with respect to the [product measure](https://en.wikipedia.org/wiki/Product_measure) on the respective [supports](https://en.wikipedia.org/wiki/Support_(measure_theory) "Support (measure theory)") of $X$ and $Y$. Either of these two decompositions can then be used to recover the joint cumulative distribution function: 

$$
F_{X,Y}(x,y)=\sum _{t\leq y}\int _{-\infty }^{x}f_{X,Y}(s,t)\;ds.
$$

 The definition generalizes to a mixture of arbitrary numbers of discrete and continuous random variables.

## Additional properties

### Joint distribution for independent variables

In general two random variables $X$ and $Y$ are [independent](https://en.wikipedia.org/wiki/Statistical_independence) if and only if the joint cumulative distribution function satisfies 

$$
F_{X,Y}(x,y)=F_{X}(x)\cdot F_{Y}(y)
$$

Two discrete random variables $X$ and $Y$ are independent if and only if the joint probability mass function satisfies 

$$
P(X=x\ {\text{and}}\ Y=y)=P(X=x)\cdot P(Y=y)
$$

 for all $x$ and $y$.

While the number of independent random events grows, the related joint probability value decreases rapidly to zero, according to a negative exponential law.

Similarly, two absolutely continuous random variables are independent if and only if 

$$
f_{X,Y}(x,y)=f_{X}(x)\cdot f_{Y}(y)
$$

 for all $x$ and $y$. This means that acquiring any information about the value of one or more of the random variables leads to a conditional distribution of any other variable that is identical to its unconditional (marginal) distribution; thus no variable provides any information about any other variable.

### Joint distribution for conditionally dependent variables

If a subset $A$ of the variables $X_{1},\cdots ,X_{n}$ is [conditionally dependent](https://en.wikipedia.org/wiki/Conditional_dependence) given another subset $B$ of these variables, then the probability mass function of the joint distribution is $\mathrm {P} (X_{1},\ldots ,X_{n})$. $\mathrm {P} (X_{1},\ldots ,X_{n})$ is equal to $P(B)\cdot P(A\mid B)$. Therefore, it can be efficiently represented by the lower-dimensional probability distributions $P(B)$ and $P(A\mid B)$. Such conditional independence relations can be represented with a [Bayesian network](https://en.wikipedia.org/wiki/Bayesian_network) or [copula functions](https://en.wikipedia.org/wiki/Copula_(probability_theory)).

### Covariance

When two or more random variables are defined on a probability space, it is useful to describe how they vary together; that is, it is useful to measure the relationship between the variables. A common measure of the relationship between two random variables is the covariance. Covariance is a measure of linear relationship between the random variables. If the relationship between the random variables is nonlinear, the covariance might not be sensitive to the relationship, which means, it does not relate the correlation between two variables.

The covariance between the random variables $X$ and $Y$ is 

$$
\operatorname {cov} (X,Y)=\sigma _{XY}=\operatorname {E} \left[(X-\mu _{x})(Y-\mu _{y})\right]=\operatorname {E} (XY)-\mu _{x}\mu _{y}.
$$

### Correlation

There is another measure of the relationship between two random variables that is often easier to interpret than the covariance.

The correlation just scales the covariance by the product of the standard deviation of each variable. Consequently, the correlation is a dimensionless quantity that can be used to compare the linear relationships between pairs of variables in different units. If the points in the joint probability distribution of X and Y that receive positive probability tend to fall along a line of positive (or negative) slope, ρ<sub>XY</sub> is near +1 (or −1). If ρ<sub>XY</sub> equals +1 or −1, it can be shown that the points in the joint probability distribution that receive positive probability fall exactly along a straight line. Two random variables with nonzero correlation are said to be correlated. Similar to covariance, the correlation is a measure of the linear relationship between random variables.

The correlation coefficient between the random variables $X$ and $Y$ is 

$$
\rho _{XY}={\frac {\operatorname {cov} (X,Y)}{\sqrt {V(X)V(Y)}}}={\frac {\sigma _{XY}}{\sigma _{X}\sigma _{Y}}}.
$$

## Important named distributions

Named joint distributions that arise frequently in statistics include the [[Multivariate Normal Distribution]], the [multivariate stable distribution](https://en.wikipedia.org/wiki/Multivariate_stable_distribution), the [multinomial distribution](https://en.wikipedia.org/wiki/Multinomial_distribution), the [negative multinomial distribution](https://en.wikipedia.org/wiki/Negative_multinomial_distribution), the [multivariate hypergeometric distribution](https://en.wikipedia.org/wiki/Multivariate_hypergeometric_distribution), and the [elliptical distribution](https://en.wikipedia.org/wiki/Elliptical_distribution).

## See also

- [Bayesian programming](https://en.wikipedia.org/wiki/Bayesian_programming)
- [Chow–Liu tree](https://en.wikipedia.org/wiki/Chow%E2%80%93Liu_tree)
- [Conditional probability](https://en.wikipedia.org/wiki/Conditional_probability)
- [Copula (probability theory)](https://en.wikipedia.org/wiki/Copula_(probability_theory))
- [Disintegration theorem](https://en.wikipedia.org/wiki/Disintegration_theorem)
- [Multivariate statistics](https://en.wikipedia.org/wiki/Multivariate_statistics)
- [Statistical interference](https://en.wikipedia.org/wiki/Statistical_interference)
- [Pairwise independent distribution](https://en.wikipedia.org/wiki/Pairwise_independence)

## References

1.  [Feller, William](https://en.wikipedia.org/wiki/William_Feller) (1968). *An Introduction to Probability Theory and its Applications*. Vol. 1 (3rd ed.). pp. 217–218. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0471257080](https://en.wikipedia.org/wiki/Special:BookSources/978-0471257080).
2.  ^   Montgomery, Douglas C.; Runger, George C. (19 November 2013). *Applied Statistics and Probability for Engineers* (Sixth ed.). Hoboken, NJ: [Wiley](https://en.wikipedia.org/wiki/Wiley_(publisher) "Wiley (publisher)"). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-118-53971-2](https://en.wikipedia.org/wiki/Special:BookSources/978-1-118-53971-2). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [861273897](https://search.worldcat.org/oclc/861273897).
3.  Park, Kun Il (2018). *Fundamentals of Probability and Stochastic Processes with Applications to Communications*. Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-319-68074-3](https://en.wikipedia.org/wiki/Special:BookSources/978-3-319-68074-3).

## External links

- ["Joint distribution"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society), 2001 \[1994\]
- ["Multi-dimensional distribution"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society), 2001 \[1994\]
- *A modern introduction to probability and statistics : understanding why and how*. Dekking, Michel, 1946-. London: Springer. 2005. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-85233-896-1](https://en.wikipedia.org/wiki/Special:BookSources/978-1-85233-896-1). [OCLC](https://en.wikipedia.org/wiki/OCLC) 262680588.
- ["Joint continuous density function"](https://planetmath.org/JointContinuousDensityFunction). *[PlanetMath](https://en.wikipedia.org/wiki/PlanetMath)*.
- [Mathworld: Joint Distribution Function](http://mathworld.wolfram.com/JointDistributionFunction.html)
