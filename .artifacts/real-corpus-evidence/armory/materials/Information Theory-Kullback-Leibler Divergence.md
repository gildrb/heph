[[information-theory.base]]

> Source: [[Kullback-Leibler Divergence|Kullback–Leibler divergence]]
> License: Wikipedia content is available under CC BY-SA 4.0.

In [mathematical statistics](https://en.wikipedia.org/wiki/Mathematical_statistics), the **Kullback–Leibler** (**KL**) **divergence** (also called **relative entropy** and **I-divergence**), denoted $D_{\text{KL}}(P\parallel Q)$, is a type of [statistical distance](https://en.wikipedia.org/wiki/Statistical_distance): a measure of how much an approximating [probability distribution](https://en.wikipedia.org/wiki/Probability_distribution) Q is different from a true probability distribution P. Mathematically, it is defined as

$$
D_{\text{KL}}(P\parallel Q)=\sum _{x\in {\mathcal {X}}}P(x)\,\log {\frac {P(x)}{Q(x)}}{\text{.}}
$$

A simple [interpretation](#Interpretations) of the KL divergence of P from Q is the [expected](https://en.wikipedia.org/wiki/Expected_value) excess [surprisal](https://en.wikipedia.org/wiki/Surprisal) from using the approximation Q instead of P when the actual is P. While it is a measure of how different two distributions are and is thus a distance in some sense, it is not actually a [metric](https://en.wikipedia.org/wiki/Metric_(mathematics)), which is the most familiar and formal type of distance. In particular, it is not symmetric in the two distributions (in contrast to [variation of information](https://en.wikipedia.org/wiki/Variation_of_information)), and does not satisfy the [triangle inequality](https://en.wikipedia.org/wiki/Triangle_inequality). Instead, in terms of [information geometry](https://en.wikipedia.org/wiki/Information_geometry), it is a type of [divergence](https://en.wikipedia.org/wiki/Divergence_(statistics) "Divergence (statistics)"), a generalization of [squared distance](https://en.wikipedia.org/wiki/Squared_Euclidean_distance), and for certain classes of distributions (notably an [[Exponential Family]]), it satisfies a generalized [Pythagorean theorem](https://en.wikipedia.org/wiki/Pythagorean_theorem) (which applies to squared distances).

KL divergence is always a non-negative [real number](https://en.wikipedia.org/wiki/Real_number), with value 0 if and only if the two distributions in question are identical. It has diverse applications, both theoretical, such as characterizing the relative [(Shannon) entropy](https://en.wikipedia.org/wiki/Entropy_(information_theory) "Entropy (information theory)") in information systems, randomness in continuous [time-series](https://en.wikipedia.org/wiki/Time_series), and information gain when comparing statistical models of [inference](https://en.wikipedia.org/wiki/Inference); and practical, such as applied statistics, [fluid mechanics](https://en.wikipedia.org/wiki/Fluid_mechanics), [neuroscience](https://en.wikipedia.org/wiki/Neuroscience), [bioinformatics](https://en.wikipedia.org/wiki/Bioinformatics), and [machine learning](https://en.wikipedia.org/wiki/Machine_learning).

## Introduction and context

Consider two probability distributions, a true P and an approximating Q. Often, P represents the data, the observations, or a measured probability distribution and distribution Q represents instead a theory, a model, a description, or another approximation of P. However, sometimes the true distribution P represents a model and the approximating distribution Q represents (simulated) data that are intended to match the true distribution. The Kullback–Leibler divergence $D_{\text{KL}}(P\parallel Q)$ is then interpreted as the average difference of the number of bits required for encoding samples of P using a [code](https://en.wikipedia.org/wiki/Entropy_coding) optimized for Q rather than one optimized for P.

Note that the roles of P and Q can be reversed in some situations where that is easier to compute and the goal is to minimize $D_{\text{KL}}(P\parallel Q)$, such as with the [expectation–maximization algorithm (EM)](https://en.wikipedia.org/wiki/Expectation%E2%80%93maximization_algorithm) and [evidence lower bound (ELBO)](https://en.wikipedia.org/wiki/Evidence_lower_bound) computations. This role-reversal approach exploits that $D_{\text{KL}}(P\parallel Q)=0$ if and only if $D_{\text{KL}}(Q\parallel P)=0$ and that, in many cases, reducing one has the effect of reducing the other.

## Etymology

The relative entropy was introduced by [Solomon Kullback](https://en.wikipedia.org/wiki/Solomon_Kullback) and [Richard Leibler](https://en.wikipedia.org/wiki/Richard_Leibler) in  as "the mean information for discrimination between $H_{1}$ and $H_{2}$ per observation from $\mu _{1}$", where one is comparing two probability measures $\mu _{1},\mu _{2}$, and $H_{1},H_{2}$ are the hypotheses that one is selecting from measure $\mu _{1},\mu _{2}$ (respectively). They denoted this by $I(1:2)$, and defined the "'divergence' between $\mu _{1}$ and $\mu _{2}$" as the symmetrized quantity $J(1,2)=I(1:2)+I(2:1)$, which had already been defined and used by [Harold Jeffreys](https://en.wikipedia.org/wiki/Harold_Jeffreys) in 1948. In , the symmetrized form is again referred to as the "divergence", and the relative entropies in each direction are referred to as a "directed divergences" between two distributions; Kullback preferred the term **discrimination information**. The term "divergence" is in contrast to a distance (metric), since the symmetrized divergence does not satisfy the triangle inequality. Numerous references to earlier uses of the symmetrized divergence and to other [statistical distances](https://en.wikipedia.org/wiki/Statistical_distance) are given in , pp. 6–7, §1.3 Divergence). The asymmetric "directed divergence" has come to be known as the Kullback–Leibler divergence, while the symmetrized "divergence" is now referred to as the **Jeffreys divergence**.

## Definition

For [discrete probability distributions](https://en.wikipedia.org/wiki/Discrete_probability_distribution) P and Q defined on the same [sample space](https://en.wikipedia.org/wiki/Sample_space), ${\mathcal {X}}$, the relative entropy from Q to P is defined to be

$$
D_{\text{KL}}(P\parallel Q)=\sum _{x\in {\mathcal {X}}}P(x)\,\log {\frac {P(x)}{Q(x)}}{\text{,}}
$$

which is equivalent to

$$
D_{\text{KL}}(P\parallel Q)=\left(-\sum _{x\in {\mathcal {X}}}P(x)\,\log Q(x)\right)-\left(-\sum _{x\in {\mathcal {X}}}P(x)\,\log P(x)\right){\text{.}}
$$

In other words, it is the [[Expectation]] of the logarithmic difference between the probabilities P and Q, where the expectation is taken using the probabilities P.

Relative entropy is only defined in this way if, for all x, $Q(x)=0$ implies $P(x)=0$ ([absolute continuity](https://en.wikipedia.org/wiki/Absolute_continuity)). Otherwise, it is often defined as $+\infty$, but the value $\ +\infty \$ is possible even if $Q(x)\neq 0$ everywhere, provided that ${\mathcal {X}}$ is infinite in extent. Analogous comments apply to the continuous and general measure cases defined below.

Whenever $P(x)$ is zero the contribution of the corresponding term is interpreted as zero because

$$
\lim _{x\to 0^{+}}x\,\log(x)=0{\text{.}}
$$

For distributions P and Q of a [continuous random variable](https://en.wikipedia.org/wiki/Continuous_random_variable), relative entropy is defined to be the integral

$$
D_{\text{KL}}(P\parallel Q)=\int _{-\infty }^{\infty }p(x)\,\log {\frac {p(x)}{q(x)}}\,dx{\text{.}}
$$

where p and q denote the [[Probability Density Function|probability density functions]] of P and Q.

More generally, if P and Q are probability [measures](https://en.wikipedia.org/wiki/Measure_(mathematics) "Measure (mathematics)") on a [measurable space](https://en.wikipedia.org/wiki/Measurable_space) ${\mathcal {X}}\,,$ and P is [absolutely continuous](https://en.wikipedia.org/wiki/Absolutely_continuous_measure) with respect to Q, then the relative entropy from Q to P is defined as

$$
D_{\text{KL}}(P\parallel Q)=\int _{x\in {\mathcal {X}}}\log {\frac {dP(x)}{dQ(x)}}\,dP(x){\text{,}}
$$

where ${\frac {dP(x)}{dQ(x)}}$ is the [Radon–Nikodym derivative](https://en.wikipedia.org/wiki/Radon%E2%80%93Nikodym_derivative) of P with respect to Q, i.e. the unique Q almost everywhere defined function r on ${\mathcal {X}}$ such that $dP(x)=r(x)dQ(x)$ which exists because P is absolutely continuous with respect to Q. Also we assume the expression on the right-hand side exists. Equivalently (by the [[Chain Rule]]), this can be written as

$$
D_{\text{KL}}(P\parallel Q)=\int _{x\in {\mathcal {X}}}{\frac {dP(x)}{dQ(x)}}\ \log {\frac {dP(x)}{dQ(x)}}\ dQ(x){\text{,}}
$$

which is the [entropy](https://en.wikipedia.org/wiki/Entropy_(information_theory) "Entropy (information theory)") of P relative to Q. Continuing in this case, if $\mu$ is any measure on ${\mathcal {X}}$ for which densities p and q with $dP(x)=p(x)d\mu (x)$ and $dQ(x)=q(x)d\mu (x)$ exist (meaning that P and Q are both absolutely continuous with respect to $\mu$), then the relative entropy from Q to P is given as

$$
D_{\text{KL}}(P\parallel Q)=\int _{x\in {\mathcal {X}}}p(x)\,\log {\frac {p(x)}{q(x)}}\ d\mu (x){\text{.}}
$$

Note that such a measure $\mu$ for which densities can be defined always exists, since one can take $\mu ={\frac {1}{2}}\left(P+Q\right)$ although in practice it will usually be one that applies in the context such as [counting measure](https://en.wikipedia.org/wiki/Counting_measure) for discrete distributions, or [Lebesgue measure](https://en.wikipedia.org/wiki/Lebesgue_measure) or a convenient variant thereof such as [Gaussian measure](https://en.wikipedia.org/wiki/Gaussian_measure) or the uniform measure on the [sphere](https://en.wikipedia.org/wiki/Sphere), [Haar measure](https://en.wikipedia.org/wiki/Haar_measure) on a [Lie group](https://en.wikipedia.org/wiki/Lie_group) etc. for continuous distributions. The logarithms in these formulae are usually taken to [base](https://en.wikipedia.org/wiki/Base_of_a_logarithm) 2 if information is measured in units of [bits](https://en.wikipedia.org/wiki/Bit), or to base e if information is measured in [nats](https://en.wikipedia.org/wiki/Nat_(unit) "Nat (unit)"). Most formulas involving relative entropy hold regardless of the base of the logarithm.

Various conventions exist for referring to $D_{\text{KL}}(P\parallel Q)$ in words. Often it is referred to as the divergence *between* P and Q, but this fails to convey the fundamental asymmetry in the relation. Sometimes, as in this article, it may be described as the divergence of P *from* Q or as the divergence *from* Q *to* P. This reflects the [asymmetry](https://en.wikipedia.org/wiki/Asymmetry) in [Bayesian inference](https://en.wikipedia.org/wiki/Bayesian_inference), which starts *from* a [prior distribution](https://en.wikipedia.org/wiki/Prior_distribution) Q and updates *to* the [posterior](https://en.wikipedia.org/wiki/Posterior_distribution) P. Another common way to refer to $D_{\text{KL}}(P\parallel Q)$ is as the relative entropy of P *with respect to* Q or the information gain from P over Q.

## Basic example

Kullback gives the following example (Table 2.1, Example 2.1). Let P and Q be the distributions shown in the table and figure. P is the distribution on the left side of the figure, a [binomial distribution](https://en.wikipedia.org/wiki/Binomial_distribution) with $N=2$ and $p=0.4$. Q is the distribution on the right side of the figure, a [discrete uniform distribution](https://en.wikipedia.org/wiki/Discrete_uniform_distribution) with the three possible outcomes `x` = 0, 1, 2 (i.e. ${\mathcal {X}}=\{0,1,2\}$), each with probability $p=1/3$.

![[media/79c923c5cd33aeeefc1bb23ca351b44e401ccd93.png]]
Two distributions to illustrate relative entropy

<table class="wikitable" style="text-align: center;">

x

Distribution

0
1
2

$P(x)$
9/25
12/25
4/25

$Q(x)$
1/3
1/3
1/3

</table>

Relative entropies $D_{\text{KL}}(P\parallel Q)$ and $D_{\text{KL}}(Q\parallel P)$ are calculated as follows. This example uses the [natural log](https://en.wikipedia.org/wiki/Natural_logarithm) with base [e](https://en.wikipedia.org/wiki/E_(mathematical_constant) "E (mathematical constant)"), designated ln to get results in [nats](https://en.wikipedia.org/wiki/Nat_(unit) "Nat (unit)") (see [units of information](https://en.wikipedia.org/wiki/Units_of_information)):

$$
{\begin{aligned}D_{\text{KL}}(P\parallel Q)&=\sum _{x\in {\mathcal {X}}}P(x)\,\ln {\frac {P(x)}{Q(x)}}\\&={\frac {9}{25}}\ln {\frac {9/25}{1/3}}+{\frac {12}{25}}\ln {\frac {12/25}{1/3}}+{\frac {4}{25}}\ln {\frac {4/25}{1/3}}\\&={\frac {1}{25}}\left(32\ln 2+55\ln 3-50\ln 5\right)\\&\approx 0.0852996{\text{,}}\end{aligned}}
$$

$$
{\begin{aligned}D_{\text{KL}}(Q\parallel P)&=\sum _{x\in {\mathcal {X}}}Q(x)\,\ln {\frac {Q(x)}{P(x)}}\\&={\frac {1}{3}}\,\ln {\frac {1/3}{9/25}}+{\frac {1}{3}}\,\ln {\frac {1/3}{12/25}}+{\frac {1}{3}}\,\ln {\frac {1/3}{4/25}}\\&={\frac {1}{3}}\left(-4\ln 2-6\ln 3+6\ln 5\right)\\&\approx 0.097455{\text{.}}\end{aligned}}
$$

## Interpretations

### Statistics

In the field of statistics, the [Neyman–Pearson lemma](https://en.wikipedia.org/wiki/Neyman%E2%80%93Pearson_lemma) states that the most powerful way to distinguish between the two distributions P and Q based on an observation Y (drawn from one of them) is through the log of the ratio of their likelihoods: $\log P(Y)-\log Q(Y)$. The KL divergence is the expected value of this statistic if Y is actually drawn from P. Kullback motivated the statistic as an expected log likelihood ratio.

### Coding

In the context of [coding theory](https://en.wikipedia.org/wiki/Coding_theory), $D_{\text{KL}}(P\parallel Q)$ can be constructed by measuring the expected number of extra [bits](https://en.wikipedia.org/wiki/Bit) required to [code](https://en.wikipedia.org/wiki/Huffman_coding) samples from P using a code optimized for Q rather than the code optimized for P.

### Inference

In the context of [machine learning](https://en.wikipedia.org/wiki/Machine_learning), $D_{\text{KL}}(P\parallel Q)$ is often called the [information gain](https://en.wikipedia.org/wiki/Information_gain_in_decision_trees) achieved if P would be used instead of Q which is currently used. By analogy with information theory, it is called the *relative entropy* of P with respect to Q.

Expressed in the language of [Bayesian inference](https://en.wikipedia.org/wiki/Bayesian_inference), $D_{\text{KL}}(P\parallel Q)$ is a measure of the information gained by revising one's beliefs from the [prior probability distribution](https://en.wikipedia.org/wiki/Prior_probability_distribution) Q to the [posterior probability distribution](https://en.wikipedia.org/wiki/Posterior_distribution) P. In other words, it is the amount of information lost when Q is used to approximate P.

### Information geometry

In applications, P typically represents the "true" distribution of data, observations, or a precisely calculated theoretical distribution, while Q typically represents a theory, model, description, or [approximation](https://en.wikipedia.org/wiki/Approximation) of P. In order to find a distribution Q that is closest to P, we can minimize the KL divergence and compute an [information projection](https://en.wikipedia.org/wiki/Information_projection).

While it is a [statistical distance](https://en.wikipedia.org/wiki/Statistical_distance), it is not a [metric](https://en.wikipedia.org/wiki/Metric_(mathematics)), the most familiar type of distance, but instead it is a [divergence](https://en.wikipedia.org/wiki/Divergence_(statistics) "Divergence (statistics)"). While metrics are symmetric and generalize *linear* distance, satisfying the [triangle inequality](https://en.wikipedia.org/wiki/Triangle_inequality), divergences are asymmetric and generalize *squared* distance, in some cases satisfying a generalized [Pythagorean theorem](https://en.wikipedia.org/wiki/Pythagorean_theorem). In general $D_{\text{KL}}(P\parallel Q)$ does not equal $D_{\text{KL}}(Q\parallel P)$, and the asymmetry is an important part of the geometry. The [infinitesimal](https://en.wikipedia.org/wiki/Infinitesimal_generator_(stochastic_processes) "Infinitesimal generator (stochastic processes)") form of relative entropy, specifically its [[Hessian Matrix|Hessian]], gives a [metric tensor](https://en.wikipedia.org/wiki/Metric_tensor) that equals the [Fisher information metric](https://en.wikipedia.org/wiki/Fisher_information_metric); see [§ Fisher information metric](#Fisher_information_metric). Fisher information metric on the certain probability distribution let determine the natural gradient for information-geometric optimization algorithms. Its quantum version is Fubini-study metric. Relative entropy satisfies a generalized Pythagorean theorem for [exponential families](https://en.wikipedia.org/wiki/Exponential_families) (geometrically interpreted as [dually flat manifolds](https://en.wikipedia.org/wiki/Dually_flat_manifold)), and this allows one to minimize relative entropy by geometric means, for example by [information projection](https://en.wikipedia.org/wiki/Information_projection) and in [[Maximum Likelihood Estimation]].

The relative entropy is the [Bregman divergence](https://en.wikipedia.org/wiki/Bregman_divergence) generated by the negative entropy, but it is also of the form of an [f-divergence](https://en.wikipedia.org/wiki/F-divergence). For probabilities over a finite [alphabet](https://en.wikipedia.org/wiki/Alphabet_(formal_languages) "Alphabet (formal languages)"), it is unique in being a member of both of these classes of [statistical divergences](https://en.wikipedia.org/wiki/Statistical_divergence). The application of Bregman divergence can be found in mirror descent.

### Finance (game theory)

Consider a growth-optimizing investor in a fair game with mutually exclusive outcomes (e.g. a "horse race" in which the official odds add up to one). The rate of return expected by such an investor is equal to the relative entropy between the investor's believed probabilities and the official odds. This is a special case of a much more general connection between financial returns and divergence measures.

Financial risks are connected to $D_{\text{KL}}$ via information geometry. Investors' views, the prevailing market view, and risky scenarios form triangles on the relevant manifold of probability distributions. The shape of the triangles determines key financial risks (both qualitatively and quantitatively). For instance, obtuse triangles in which investors' views and risk scenarios appear on "opposite sides" relative to the market describe negative risks, acute triangles describe positive exposure, and the right-angled situation in the middle corresponds to zero risk. Extending this concept, relative entropy can be hypothetically utilised to identify the behaviour of informed investors, if one takes this to be represented by the magnitude and deviations away from the prior expectations of fund flows, for example.

## Motivation

![[media/96184c0ba92040e3a7bbe76596715c9e659415f1.png]]
Illustration of the relative entropy for two [normal distributions](https://en.wikipedia.org/wiki/Normal_distribution). The typical asymmetry is clearly visible.

In information theory, the [Kraft–McMillan theorem](https://en.wikipedia.org/wiki/Kraft%E2%80%93McMillan_inequality) establishes that any directly decodable coding scheme for coding a message to identify one value $x_{i}$ out of a set of possibilities X can be seen as representing an implicit probability distribution $q(x_{i})=2^{-\ell _{i}}$ over X, where $\ell _{i}$ is the length of the code for $x_{i}$ in bits. Therefore, relative entropy can be interpreted as the expected extra message-length per datum that must be communicated if a code that is optimal for a given (wrong) distribution Q is used, compared to using a code based on the true distribution P: it is the *excess* entropy.

$$
{\begin{aligned}D_{\text{KL}}(P\parallel Q)&=\sum _{x\in {\mathcal {X}}}p(x)\log {\frac {1}{q(x)}}-\sum _{x\in {\mathcal {X}}}p(x)\log {\frac {1}{p(x)}}\\[5pt]&=\mathrm {H} (P,Q)-\mathrm {H} (P)\end{aligned}}
$$

where $\mathrm {H} (P,Q)$ is the [[Cross-Entropy|cross entropy]] of Q relative to P and $\mathrm {H} (P)$ is the [entropy](https://en.wikipedia.org/wiki/Information_entropy) of P (which is the same as the cross-entropy of P with itself).

The relative entropy $D_{\text{KL}}(P\parallel Q)$ can be thought of geometrically as a [statistical distance](https://en.wikipedia.org/wiki/Statistical_distance), a measure of how far the distribution Q is from the distribution P. Geometrically it is a [divergence](https://en.wikipedia.org/wiki/Divergence_(statistics) "Divergence (statistics)"): an asymmetric, generalized form of squared distance. The cross-entropy $H(P,Q)$ is itself such a measurement (formally a [loss function](https://en.wikipedia.org/wiki/Loss_function)), but it cannot be thought of as a distance, since $H(P,P)=:H(P)$ is not zero. This can be fixed by subtracting $H(P)$ to make $D_{\text{KL}}(P\parallel Q)$ agree more closely with our notion of distance, as the *excess* loss. The resulting function is asymmetric, and while this can be symmetrized (see [§ Symmetrised divergence](#Symmetrised_divergence)), the asymmetric form is more useful. See [§ Interpretations](#Interpretations) for more on the geometric interpretation.

Relative entropy relates to "[rate function](https://en.wikipedia.org/wiki/Rate_function)" in the theory of [large deviations](https://en.wikipedia.org/wiki/Large_deviations).

Arthur Hobson proved that relative entropy is the only measure of difference between probability distributions that satisfies some desired properties, which are the canonical extension to those appearing in a commonly used [characterization of entropy](https://en.wikipedia.org/wiki/Entropy_(information_theory)#Characterization "Entropy (information theory)"). Consequently, [[Mutual Information]] is the only measure of mutual dependence that obeys certain related conditions, since it can be defined [[Mutual Information|in terms of Kullback–Leibler divergence]].

## Properties

- Relative entropy is always [non-negative](https://en.wikipedia.org/wiki/Non-negative), 

$$
D_{\text{KL}}(P\parallel Q)\geq 0,
$$

 a result known as [Gibbs' inequality](https://en.wikipedia.org/wiki/Gibbs%27_inequality), with $D_{\text{KL}}(P\parallel Q)$ equals zero [if and only if](https://en.wikipedia.org/wiki/If_and_only_if) $P=Q$ as measures.

In particular, if $P(dx)=p(x)\mu (dx)$ and $Q(dx)=q(x)\mu (dx)$, then $p(x)=q(x)$ $\mu$-[almost everywhere](https://en.wikipedia.org/wiki/Almost_everywhere). The entropy $\mathrm {H} (P)$ thus sets a minimum value for the cross-entropy $\mathrm {H} (P,Q)$, the [expected](https://en.wikipedia.org/wiki/Expected_value) number of [bits](https://en.wikipedia.org/wiki/Bit) required when using a code based on Q rather than P; and the Kullback–Leibler divergence therefore represents the expected number of extra bits that must be transmitted to identify a value x drawn from X, if a code is used corresponding to the probability distribution Q, rather than the "true" distribution P.

- No upper-bound exists for the general case. However, it is shown that if P and Q are two discrete probability distributions built by distributing the same discrete quantity, then the maximum value of $D_{\text{KL}}(P\parallel Q)$ can be calculated.
- Relative entropy remains well-defined for continuous distributions, and furthermore is invariant under [parameter transformations](https://en.wikipedia.org/wiki/Change_of_variables). For example, if a transformation is made from variable x to variable $y(x)$, then, since $P(dx)=p(x)\,dx={\tilde {p}}(y)\,dy={\tilde {p}}(y(x))\left|{\tfrac {dy}{dx}}(x)\right|\,dx$ and $Q(dx)=q(x)\,dx={\tilde {q}}(y)\,dy={\tilde {q}}(y)\left|{\tfrac {dy}{dx}}(x)\right|dx$ where $\left|{\tfrac {dy}{dx}}(x)\right|$ is the absolute value of the derivative or more generally of the [Jacobian](https://en.wikipedia.org/wiki/Jacobian), the relative entropy may be rewritten: 

$$
{\begin{aligned}D_{\text{KL}}(P\parallel Q)&=\int _{x_{a}}^{x_{b}}p(x)\,\log {\frac {p(x)}{q(x)}}\,dx\\[6pt]&=\int _{x_{a}}^{x_{b}}{\tilde {p}}(y(x))\left|{\frac {dy}{dx}}\right|\log {\frac {{\tilde {p}}(y(x))\,\left|{\frac {dy}{dx}}\right|}{{\tilde {q}}(y(x))\,\left|{\frac {dy}{dx}}\right|}}\,dx\\&=\int _{y_{a}}^{y_{b}}{\tilde {p}}(y)\,\log {\frac {{\tilde {p}}(y)}{{\tilde {q}}(y)}}\,dy\end{aligned}}
$$

 where $y_{a}=y(x_{a})$ and $y_{b}=y(x_{b})$. Although it was assumed that the transformation was continuous, this need not be the case. This also shows that the relative entropy produces a [dimensionally consistent](https://en.wikipedia.org/wiki/Dimensional_analysis) quantity, since if x is a dimensioned variable, $p(x)$ and $q(x)$ are also dimensioned, since e.g. $P(dx)=p(x)\,dx$ is dimensionless. The argument of the logarithmic term is and remains dimensionless, as it must. It can therefore be seen as in some ways a more fundamental quantity than some other properties in information theory (such as [self-information](https://en.wikipedia.org/wiki/Self-information) or [Shannon entropy](https://en.wikipedia.org/wiki/Shannon_entropy)), which can become undefined or negative for non-discrete probabilities.
- Relative entropy is [additive](https://en.wikipedia.org/wiki/Additive_map) for [independent distributions](https://en.wikipedia.org/wiki/Independent_random_variables) in much the same way as Shannon entropy. If $P_{1},P_{2}$ are independent distributions, and $P(dx,dy)=P_{1}(dx)P_{2}(dy)$, and likewise $Q(dx,dy)=Q_{1}(dx)Q_{2}(dy)$ for independent distributions $Q_{1},Q_{2}$ then 

$$
D_{\text{KL}}(P\parallel Q)=D_{\text{KL}}(P_{1}\parallel Q_{1})+D_{\text{KL}}(P_{2}\parallel Q_{2}).
$$

- Relative entropy $D_{\text{KL}}(P\parallel Q)$ is [convex](https://en.wikipedia.org/wiki/Convex_function) in the pair of [probability measures](https://en.wikipedia.org/wiki/Probability_measure) $(P,Q)$, i.e. if $(P_{1},Q_{1})$ and $(P_{2},Q_{2})$ are two pairs of probability measures then 

$$
D_{\text{KL}}(\lambda P_{1}+(1-\lambda )P_{2}\parallel \lambda Q_{1}+(1-\lambda )Q_{2})\leq \lambda D_{\text{KL}}(P_{1}\parallel Q_{1})+(1-\lambda )D_{\text{KL}}(P_{2}\parallel Q_{2}){\text{ for }}0\leq \lambda \leq 1.
$$

- $D_{\text{KL}}(P\parallel Q)$ may be Taylor expanded about its minimum (i.e. $P=Q$) as 

$$
D_{\text{KL}}(P\parallel Q)=\sum _{n=2}^{\infty }{\frac {1}{n(n-1)}}\sum _{x\in {\mathcal {X}}}{\frac {(Q(x)-P(x))^{n}}{Q(x)^{n-1}}}
$$

 which converges if and only if $P\leq 2Q$ [almost surely](https://en.wikipedia.org/wiki/Almost_surely) w.r.t $Q$.

\[Proof\]

Denote $f(\alpha ):=D_{\text{KL}}((1-\alpha )Q+\alpha P\parallel Q)$ and note that $D_{\text{KL}}(P\parallel Q)=f(1)$. The first derivative of $f$ may be derived and evaluated as follows 

$$
{\begin{aligned}f'(\alpha )&=\sum _{x\in {\mathcal {X}}}(P(x)-Q(x))\left(\log \left({\frac {(1-\alpha )Q(x)+\alpha P(x)}{Q(x)}}\right)+1\right)\\&=\sum _{x\in {\mathcal {X}}}(P(x)-Q(x))\log \left({\frac {(1-\alpha )Q(x)+\alpha P(x)}{Q(x)}}\right)\\f'(0)&=0\end{aligned}}
$$

 Further derivatives may be derived and evaluated as follows 

$$
{\begin{aligned}f''(\alpha )&=\sum _{x\in {\mathcal {X}}}{\frac {(P(x)-Q(x))^{2}}{(1-\alpha )Q(x)+\alpha P(x)}}\\f''(0)&=\sum _{x\in {\mathcal {X}}}{\frac {(P(x)-Q(x))^{2}}{Q(x)}}\\f^{(n)}(\alpha )&=(-1)^{n}(n-2)!\sum _{x\in {\mathcal {X}}}{\frac {(P(x)-Q(x))^{n}}{\left((1-\alpha )Q(x)+\alpha P(x)\right)^{n-1}}}\\f^{(n)}(0)&=(-1)^{n}(n-2)!\sum _{x\in {\mathcal {X}}}{\frac {(P(x)-Q(x))^{n}}{Q(x)^{n-1}}}\end{aligned}}
$$

 Hence solving for $D_{\text{KL}}(P\parallel Q)$ via the Taylor expansion of $f$ about $0$ evaluated at $\alpha =1$ yields 

$$
{\begin{aligned}D_{\text{KL}}(P\parallel Q)&=\sum _{n=0}^{\infty }{\frac {f^{(n)}(0)}{n!}}\\&=\sum _{n=2}^{\infty }{\frac {1}{n(n-1)}}\sum _{x\in {\mathcal {X}}}{\frac {(Q(x)-P(x))^{n}}{Q(x)^{n-1}}}\end{aligned}}
$$

 $P\leq 2Q$ a.s. is a sufficient condition for convergence of the series by the following absolute convergence argument 

$$
{\begin{aligned}\sum _{n=2}^{\infty }\left\vert {\frac {1}{n(n-1)}}\sum _{x\in {\mathcal {X}}}{\frac {(Q(x)-P(x))^{n}}{Q(x)^{n-1}}}\right\vert &=\sum _{n=2}^{\infty }{\frac {1}{n(n-1)}}\sum _{x\in {\mathcal {X}}}\left\vert Q(x)-P(x)\right\vert \left\vert 1-{\frac {P(x)}{Q(x)}}\right\vert ^{n-1}\\&\leq \sum _{n=2}^{\infty }{\frac {1}{n(n-1)}}\sum _{x\in {\mathcal {X}}}\left\vert Q(x)-P(x)\right\vert \\&\leq \sum _{n=2}^{\infty }{\frac {1}{n(n-1)}}\\&=1\end{aligned}}
$$

 $P\leq 2Q$ a.s. is also a necessary condition for convergence of the series by the following proof by contradiction. Assume that $P>2Q$ with measure strictly greater than $0$. It then follows that there must exist some values $\varepsilon >0$, $\rho >0$, and $U<\infty$ such that $P\geq 2Q+\varepsilon$ and $Q\leq U$ with measure $\rho$. The previous proof of sufficiency demonstrated that the measure $1-\rho$ component of the series where $P\leq 2Q$ is bounded, so we need only concern ourselves with the behavior of the measure $\rho$ component of the series where $P\geq 2Q+\varepsilon$. The absolute value of the $n$th term of this component of the series is then lower bounded by ${\frac {1}{n(n-1)}}\rho \left(1+{\frac {\varepsilon }{U}}\right)^{n}$, which is unbounded as $n\to \infty$, so the series diverges.

## Duality formula for variational inference

The following result, due to Donsker and Varadhan, is known as **Donsker and Varadhan's variational formula**.

**Theorem \[Duality Formula for Variational Inference\]**—Let $\Theta$ be a set endowed with an appropriate $\sigma$-field ${\mathcal {F}}$, and two probability measures P and Q, which formulate two [probability spaces](https://en.wikipedia.org/wiki/Probability_spaces) $(\Theta ,{\mathcal {F}},P)$ and $(\Theta ,{\mathcal {F}},Q)$, with $Q\ll P$. ($Q\ll P$ indicates that Q is absolutely continuous with respect to P.) Let h be a real-valued integrable [random variable](https://en.wikipedia.org/wiki/Random_variable) on $(\Theta ,{\mathcal {F}},P)$. Then the following equality holds

$$
\log E_{P}[\exp h]=\operatorname {sup} _{Q\ll P}\{E_{Q}[h]-D_{\text{KL}}(Q\parallel P)\}{\text{.}}
$$

Further, the supremum on the right-hand side is attained if and only if it holds

$$
{\frac {Q(d\theta )}{P(d\theta )}}={\frac {\exp h(\theta )}{E_{P}[\exp h]}}{\text{,}}
$$

almost surely with respect to probability measure P, where ${\frac {Q(d\theta )}{P(d\theta )}}$ denotes the Radon-Nikodym derivative of Q with respect to P.

**Proof**

For a short proof assuming integrability of $\exp(h)$ with respect to P, let $Q^{*}$ have P-density ${\frac {\exp h(\theta )}{E_{P}[\exp h]}}$, i.e. $Q^{*}(d\theta )={\frac {\exp h(\theta )}{E_{P}[\exp h]}}P(d\theta )$ Then

$$
D_{\text{KL}}(Q\parallel Q^{*})-D_{\text{KL}}(Q\parallel P)=-E_{Q}[h]+\log E_{P}[\exp h]{\text{.}}
$$

Therefore,

$$
E_{Q}[h]-D_{\text{KL}}(Q\parallel P)=\log E_{P}[\exp h]-D_{\text{KL}}(Q\parallel Q^{*})\leq \log E_{P}[\exp h]{\text{,}}
$$

where the last inequality follows from $D_{\text{KL}}(Q\parallel Q^{*})\geq 0$, for which equality occurs if and only if $Q=Q^{*}$. The conclusion follows.

## Examples

### Multivariate normal distributions

Suppose that we have two [[Multivariate Normal Distribution|multivariate normal distributions]], with means $\mu _{0},\mu _{1}$ and with (non-singular) [covariance matrices](https://en.wikipedia.org/wiki/Covariance_matrix) $\Sigma _{0},\Sigma _{1}.$ If the two distributions have the same dimension, k, then the relative entropy between the distributions is as follows:

$$
D_{\text{KL}}\left({\mathcal {N}}_{0}\parallel {\mathcal {N}}_{1}\right)={\frac {1}{2}}\left[\operatorname {tr} \left(\Sigma _{1}^{-1}\Sigma _{0}\right)-k+\left(\mu _{1}-\mu _{0}\right)^{\mathsf {T}}\Sigma _{1}^{-1}\left(\mu _{1}-\mu _{0}\right)+\ln {\frac {\det \Sigma _{1}}{\det \Sigma _{0}}}\right]{\text{.}}
$$

The [logarithm](https://en.wikipedia.org/wiki/Logarithm) in the last term must be taken to base [e](https://en.wikipedia.org/wiki/E_(mathematical_constant) "E (mathematical constant)") since all terms apart from the last are base-e logarithms of expressions that are either factors of the density function or otherwise arise naturally. The equation therefore gives a result measured in [nats](https://en.wikipedia.org/wiki/Nat_(unit) "Nat (unit)"). Dividing the entire expression above by $\ln(2)$ yields the divergence in [bits](https://en.wikipedia.org/wiki/Bit).

In a numerical implementation, it is helpful to express the result in terms of the Cholesky decompositions $L_{0},L_{1}$ such that $\Sigma _{0}=L_{0}L_{0}^{T}$ and $\Sigma _{1}=L_{1}L_{1}^{T}$. Then with M and y solutions to the triangular linear systems $L_{1}M=L_{0}$, and $L_{1}y=\mu _{1}-\mu _{0}$,

$$
D_{\text{KL}}\left({\mathcal {N}}_{0}\parallel {\mathcal {N}}_{1}\right)={\frac {1}{2}}\left(\sum _{i,j=1}^{k}{\left(M_{ij}\right)}^{2}-k+|y|^{2}+2\sum _{i=1}^{k}\ln {\frac {(L_{1})_{ii}}{(L_{0})_{ii}}}\right){\text{.}}
$$

A special case, and a common quantity in [variational inference](https://en.wikipedia.org/wiki/Variational_inference), is the relative entropy between a diagonal multivariate normal, and a standard normal distribution (with zero mean and unit variance):

$$
D_{\text{KL}}\left({\mathcal {N}}\left(\left(\mu _{1},\ldots ,\mu _{k}\right)^{\mathsf {T}},\operatorname {diag} \left(\sigma _{1}^{2},\ldots ,\sigma _{k}^{2}\right)\right)\parallel {\mathcal {N}}\left(\mathbf {0} ,\mathbf {I} \right)\right)={\frac {1}{2}}\sum _{i=1}^{k}\left[\sigma _{i}^{2}+\mu _{i}^{2}-1-\ln \left(\sigma _{i}^{2}\right)\right]{\text{.}}
$$

For two univariate normal distributions **p** and **q** the above simplifies to 

$$
D_{\text{KL}}\left({\mathcal {p}}\parallel {\mathcal {q}}\right)=\log {\frac {\sigma _{1}}{\sigma _{0}}}+{\frac {\sigma _{0}^{2}+{\left(\mu _{0}-\mu _{1}\right)}^{2}}{2\sigma _{1}^{2}}}-{\frac {1}{2}}
$$

In the case of co-centered normal distributions with $k=\sigma _{1}/\sigma _{0}$, this simplifies to:

$$
D_{\text{KL}}\left({\mathcal {p}}\parallel {\mathcal {q}}\right)=\log _{2}k+(k^{-2}-1)/2/\ln(2)\mathrm {bits}
$$

### Uniform distributions

Consider two uniform distributions, with the support of $p=[A,B]$ enclosed within $q=[C,D]$ ($C\leq A<B\leq D$). Then the information gain is:

$$
D_{\text{KL}}\left({\mathcal {p}}\parallel {\mathcal {q}}\right)=\log {\frac {D-C}{B-A}}
$$

Intuitively, the information gain to a k times narrower uniform distribution contains $\log _{2}k$ bits. This connects with the use of bits in computing, where $\log _{2}k$ bits would be needed to identify one element of a k long stream.

### Exponential family

The [[Exponential Family]] of distribution is given by

$$
p_{X}(x|\theta )=h(x)\exp \left(\theta ^{\mathsf {T}}T(x)-A(\theta )\right)
$$

where $h(x)$ is reference measure, $T(x)$ is [sufficient statistics](https://en.wikipedia.org/wiki/Sufficient_statistic), $\theta$ is canonical natural parameters, and $A(\theta )$ is the log-partition function.

The KL divergence between two distributions $p(x|\theta _{1})$ and $p(x|\theta _{2})$ is given by

$$
D_{\text{KL}}(\theta _{1}\parallel \theta _{2})={\left(\theta _{1}-\theta _{2}\right)}^{\mathsf {T}}\mu _{1}-A(\theta _{1})+A(\theta _{2})
$$

where $\mu _{1}=E_{\theta _{1}}[T(X)]=\nabla A(\theta _{1})$ is the mean parameter of $p(x|\theta _{1})$.

For example, for the [Poisson distribution](https://en.wikipedia.org/wiki/Poisson_distribution) with mean $\lambda$, the sufficient statistics $T(x)=x$, the natural parameter $\theta =\log \lambda$, and log partition function $A(\theta )=e^{\theta }$. As such, the divergence between two Poisson distributions with means $\lambda _{1}$ and $\lambda _{2}$ is

$$
D_{\text{KL}}(\lambda _{1}\parallel \lambda _{2})=\lambda _{1}\log {\frac {\lambda _{1}}{\lambda _{2}}}-\lambda _{1}+\lambda _{2}{\text{.}}
$$

As another example, for a normal distribution with unit variance $N(\mu ,1)$, the sufficient statistics $T(x)=x$, the natural parameter $\theta =\mu$, and log partition function $A(\theta )=\mu ^{2}/2$. Thus, the divergence between two normal distributions $N(\mu _{1},1)$ and $N(\mu _{2},1)$ is

$$
D_{\text{KL}}(\mu _{1}\parallel \mu _{2})=\left(\mu _{1}-\mu _{2}\right)\mu _{1}-{\frac {\mu _{1}^{2}}{2}}+{\frac {\mu _{2}^{2}}{2}}={\frac {{\left(\mu _{2}-\mu _{1}\right)}^{2}}{2}}{\text{.}}
$$

As final example, the divergence between a normal distribution with unit variance $N(\mu ,1)$ and a Poisson distribution with mean $\lambda$ is

$$
D_{\text{KL}}(\mu \parallel \lambda )=(\mu -\log \lambda )\mu -{\frac {\mu ^{2}}{2}}+\lambda {\text{.}}
$$

## Relation to metrics

While relative entropy is a [statistical distance](https://en.wikipedia.org/wiki/Statistical_distance), it is not a [metric](https://en.wikipedia.org/wiki/Metric_(mathematics)) on the space of probability distributions, but instead it is a [divergence](https://en.wikipedia.org/wiki/Divergence_(statistics) "Divergence (statistics)"). While metrics are symmetric and generalize *linear* distance, satisfying the [triangle inequality](https://en.wikipedia.org/wiki/Triangle_inequality), divergences are asymmetric in general and generalize *squared* distance, in some cases satisfying a generalized [Pythagorean theorem](https://en.wikipedia.org/wiki/Pythagorean_theorem). In general $D_{\text{KL}}(P\parallel Q)$ does not equal $D_{\text{KL}}(Q\parallel P)$, and while this can be symmetrized (see [§ Symmetrised divergence](#Symmetrised_divergence)), the asymmetry is an important part of the geometry.

It generates a [topology](https://en.wikipedia.org/wiki/Topology#Topologies_on_sets) on the space of [probability distributions](https://en.wikipedia.org/wiki/Probability_distribution). More concretely, if $\{P_{1},P_{2},\ldots \}$ is a sequence of distributions such that

$$
\lim _{n\to \infty }D_{\text{KL}}(P_{n}\parallel Q)=0{\text{,}}
$$

then it is said that

$$
P_{n}\xrightarrow {D} \,Q{\text{.}}
$$

[Pinsker's inequality](https://en.wikipedia.org/wiki/Pinsker%27s_inequality) entails that

$$
P_{n}\xrightarrow {D} P\Rightarrow P_{n}\xrightarrow {TV} P{\text{,}}
$$

where the latter stands for the usual convergence in [total variation](https://en.wikipedia.org/wiki/Total_variation).

### Fisher information metric

Relative entropy is directly related to the [Fisher information metric](https://en.wikipedia.org/wiki/Fisher_information_metric). This can be made explicit as follows. Assume that the probability distributions P and Q are both parameterized by some (possibly multi-dimensional) parameter $\theta$. Consider then two close by values of $P=P(\theta )$ and $Q=P(\theta _{0})$ so that the parameter $\theta$ differs by only a small amount from the parameter value $\theta _{0}$. Specifically, up to first order one has (using the [Einstein summation convention](https://en.wikipedia.org/wiki/Einstein_summation_convention)) 

$$
P(\theta )=P(\theta _{0})+\Delta \theta _{j}\,P_{j}(\theta _{0})+\cdots
$$

with $\Delta \theta _{j}=(\theta -\theta _{0})_{j}$ a small change of $\theta$ in the j direction, and $P_{j}\left(\theta _{0}\right)={\frac {\partial P}{\partial \theta _{j}}}(\theta _{0})$ the corresponding rate of change in the probability distribution. Since relative entropy has an absolute minimum 0 for $P=Q$, i.e. $\theta =\theta _{0}$, it changes only to *second* order in the small parameters $\Delta \theta _{j}$. More formally, as for any minimum, the first derivatives of the divergence vanish

$$
\left.{\frac {\partial }{\partial \theta _{j}}}\right|_{\theta =\theta _{0}}D_{\text{KL}}(P(\theta )\parallel P(\theta _{0}))=0,
$$

and by the [[Taylor Series|Taylor expansion]] one has up to second order

$$
D_{\text{KL}}(P(\theta )\parallel P(\theta _{0}))={\frac {1}{2}}\,\Delta \theta _{j}\,\Delta \theta _{k}\,g_{jk}(\theta _{0})+\cdots
$$

where the [[Hessian Matrix]] of the divergence

$$
g_{jk}(\theta _{0})=\left.{\frac {\partial ^{2}}{\partial \theta _{j}\,\partial \theta _{k}}}\right|_{\theta =\theta _{0}}D_{\text{KL}}(P(\theta )\parallel P(\theta _{0}))
$$

must be [[Positive-Definite Matrix|positive semi-definite]]. Letting $\theta _{0}$ vary (and dropping the subindex 0) the Hessian $g_{jk}(\theta )$ defines a (possibly degenerate) [Riemannian metric](https://en.wikipedia.org/wiki/Riemannian_metric) on the θ [parameter space](https://en.wikipedia.org/wiki/Parameter_space), called the Fisher information metric.

#### Fisher information metric theorem

There is an associated theorem. When $p_{(x,\rho )}$ satisfies the following regularity conditions:

$$
{\frac {\partial \log(p)}{\partial \rho }},{\frac {\partial ^{2}\log(p)}{\partial \rho ^{2}}},{\frac {\partial ^{3}\log(p)}{\partial \rho ^{3}}}
$$

 exist, 

$$
{\begin{aligned}\left|{\frac {\partial p}{\partial \rho }}\right|&<F(x):\int _{x=0}^{\infty }F(x)\,dx<\infty ,\\\left|{\frac {\partial ^{2}p}{\partial \rho ^{2}}}\right|&<G(x):\int _{x=0}^{\infty }G(x)\,dx<\infty \\\left|{\frac {\partial ^{3}\log(p)}{\partial \rho ^{3}}}\right|&<H(x):\int _{x=0}^{\infty }p(x,0)H(x)\,dx<\xi <\infty \end{aligned}}
$$

where ξ is independent of ρ 

$$
\left.\int _{x=0}^{\infty }{\frac {\partial p(x,\rho )}{\partial \rho }}\right|_{\rho =0}\,dx=\left.\int _{x=0}^{\infty }{\frac {\partial ^{2}p(x,\rho )}{\partial \rho ^{2}}}\right|_{\rho =0}\,dx=0
$$

then: 

$$
{\mathcal {D}}(p(x,0)\parallel p(x,\rho ))={\frac {c\rho ^{2}}{2}}+{\mathcal {O}}\left(\rho ^{3}\right){\text{ as }}\rho \to 0{\text{.}}
$$

### Variation of information

Another information-theoretic metric is [variation of information](https://en.wikipedia.org/wiki/Variation_of_information), which is roughly a symmetrization of [conditional entropy](https://en.wikipedia.org/wiki/Conditional_entropy). It is a metric on the set of [partitions](https://en.wikipedia.org/wiki/Partition_of_a_set) of a discrete [probability space](https://en.wikipedia.org/wiki/Probability_space).

### MAUVE Metric

MAUVE is a measure of the statistical gap between two text distributions, such as the difference between text generated by a model and human-written text. This measure is computed using Kullback–Leibler divergences between the two distributions in a quantized embedding space of a foundation model.

## Relation to other quantities of information theory

Many of the other quantities of information theory can be interpreted as applications of relative entropy to specific cases.

### Self-information

The [self-information](https://en.wikipedia.org/wiki/Self-information), also known as the [information content](https://en.wikipedia.org/wiki/Information_content) of a signal, random variable, or [event](https://en.wikipedia.org/wiki/Event_(probability_theory) "Event (probability theory)") is defined as the negative logarithm of the [probability](https://en.wikipedia.org/wiki/Probability) of the given outcome occurring.

When applied to a [discrete random variable](https://en.wikipedia.org/wiki/Discrete_random_variable), the self-information can be represented as<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

$$
\operatorname {\operatorname {I} } (m)=D_{\text{KL}}\left(\delta _{\text{im}}\parallel \{p_{i}\}\right),
$$

is the relative entropy of the probability distribution $P(i)$ from a [Kronecker delta](https://en.wikipedia.org/wiki/Kronecker_delta) representing certainty that $i=m$ — i.e. the number of extra bits that must be transmitted to identify i if only the probability distribution $P(i)$ is available to the receiver, not the fact that $i=m$.

### Mutual information

The [[Mutual Information]],

$$
{\begin{aligned}\operatorname {I} (X;Y)&=D_{\text{KL}}(P_{X,Y}\parallel P_{X}\cdot P_{Y})\\&=\operatorname {E} _{X}[D_{\text{KL}}^{Y}(P_{Y\mid X}\parallel P_{Y})]\\&=\operatorname {E} _{Y}[D_{\text{KL}}^{X}(P_{X\mid Y}\parallel P_{X})]\end{aligned}}
$$

is the relative entropy of the [joint probability distribution](https://en.wikipedia.org/wiki/Joint_probability_distribution) $P_{X,Y}(x,y)$ from the product $(P_{X}\cdot P_{Y})(x,y)=P_{X}(x)P_{Y}(y)$ of the two [marginal probability distributions](https://en.wikipedia.org/wiki/Marginal_probability_distribution) — i.e. the expected number of extra bits that must be transmitted to identify X and Y if they are coded using only their marginal distributions instead of the joint distribution.

### Shannon entropy

The [Shannon entropy](https://en.wikipedia.org/wiki/Shannon_entropy),

$$
{\begin{aligned}\mathrm {H} (X)&=\operatorname {E} \left[\operatorname {I} _{X}(x)\right]\\&=\log N-D_{\text{KL}}{\left(p_{X}(x)\parallel P_{U}(X)\right)}\end{aligned}}
$$

is the number of bits which would have to be transmitted to identify X from N equally likely possibilities, *less* the relative entropy of the uniform distribution on the [random variates](https://en.wikipedia.org/wiki/Random_variate) of X, $P_{U}(X)$, from the true distribution $P(X)$ — i.e. *less* the expected number of bits saved, which would have had to be sent if the value of X were coded according to the uniform distribution $P_{U}(X)$ rather than the true distribution $P(X)$. This definition of Shannon entropy forms the basis of [E.T. Jaynes](https://en.wikipedia.org/wiki/E.T._Jaynes)'s alternative generalization to continuous distributions, the [limiting density of discrete points](https://en.wikipedia.org/wiki/Limiting_density_of_discrete_points) (as opposed to the usual [differential entropy](https://en.wikipedia.org/wiki/Differential_entropy)), which defines the continuous entropy as 

$$
\lim _{N\to \infty }H_{N}(X)=\log N-\int p(x)\log {\frac {p(x)}{m(x)}}\,dx{\text{,}}
$$

 which is equivalent to: 

$$
\log(N)-D_{\text{KL}}(p(x)||m(x))
$$

### Conditional entropy

The [conditional entropy](https://en.wikipedia.org/wiki/Conditional_entropy),

$$
{\begin{aligned}\mathrm {H} (X\mid Y)&=\log N-D_{\text{KL}}(P(X,Y)\parallel P_{U}(X)P(Y))\\[5pt]&=\log N-D_{\text{KL}}(P(X,Y)\parallel P(X)P(Y))-D_{\text{KL}}(P(X)\parallel P_{U}(X))\\[5pt]&=\mathrm {H} (X)-\operatorname {I} (X;Y)\\[5pt]&=\log N-\operatorname {E} _{Y}\left[D_{\text{KL}}\left(P\left(X\mid Y\right)\parallel P_{U}(X)\right)\right]\end{aligned}}
$$

is the number of bits which would have to be transmitted to identify X from N equally likely possibilities, *less* the relative entropy of the true joint distribution $P(X,Y)$ from the product distribution $P_{U}(X)P(Y)$ from — i.e. *less* the expected number of bits saved which would have had to be sent if the value of X were coded according to the uniform distribution $P_{U}(X)$ rather than the conditional distribution $P(X|Y)$ of X given Y.

### Cross entropy

When we have a set of possible events, coming from the distribution p, we can encode them (with a [lossless data compression](https://en.wikipedia.org/wiki/Lossless_compression)) using [entropy encoding](https://en.wikipedia.org/wiki/Entropy_encoding). This compresses the data by replacing each fixed-length input symbol with a corresponding unique, variable-length, [prefix-free code](https://en.wikipedia.org/wiki/Prefix-free_code) (e.g.: the events (A, B, C) with probabilities p = (1/2, 1/4, 1/4) can be encoded as the bits (0, 10, 11)). If we know the distribution p in advance, we can devise an encoding that would be optimal (e.g.: using [Huffman coding](https://en.wikipedia.org/wiki/Huffman_coding)). Meaning the messages we encode will have the shortest length on average (assuming the encoded events are sampled from p), which will be equal to [Shannon's Entropy](https://en.wikipedia.org/wiki/Shannon%27s_entropy) of p (denoted as $\mathrm {H} (p)$). However, if we use a different probability distribution (q) when creating the entropy encoding scheme, then a larger number of [bits](https://en.wikipedia.org/wiki/Bit) will be used (on average) to identify an event from a set of possibilities. This new (larger) number is measured by the [[Cross-Entropy|cross entropy]] between p and q.

The [[Cross-Entropy|cross entropy]] between two [probability distributions](https://en.wikipedia.org/wiki/Probability_distribution) (p and q) measures the average number of [bits](https://en.wikipedia.org/wiki/Bit) needed to identify an event from a set of possibilities, if a coding scheme is used based on a given probability distribution q, rather than the "true" distribution p. The cross entropy for two distributions p and q over the same [probability space](https://en.wikipedia.org/wiki/Probability_space) is thus defined as follows.

$$
\mathrm {H} (p,q)=\operatorname {E} _{p}[-\log q]=\mathrm {H} (p)+D_{\text{KL}}(p\parallel q)
$$

For explicit derivation of this, see the [Motivation](#Motivation) section above.

Under this scenario, relative entropies (kl-divergence) can be interpreted as the extra number of bits, on average, that are needed (beyond $\mathrm {H} (p)$) for encoding the events because of using q for constructing the encoding scheme instead of p.

## Bayesian updating

In [Bayesian statistics](https://en.wikipedia.org/wiki/Bayesian_statistics), relative entropy can be used as a measure of the information gain in moving from a [prior distribution](https://en.wikipedia.org/wiki/Prior_distribution) to a [posterior distribution](https://en.wikipedia.org/wiki/Posterior_distribution): $p(x)\to p(x\mid I)$. If some new fact $Y=y$ is discovered, it can be used to update the posterior distribution for X from $p(x\mid I)$ to a new posterior distribution $p(x\mid y,I)$ using [[Bayes Theorem|Bayes' theorem]]:

$$
p(x\mid y,I)={\frac {p(y\mid x,I)p(x\mid I)}{p(y\mid I)}}
$$

This distribution has a new [entropy](https://en.wikipedia.org/wiki/Entropy_in_thermodynamics_and_information_theory):

$$
\mathrm {H} {\big (}p(x\mid y,I){\big )}=-\sum _{x}p(x\mid y,I)\log p(x\mid y,I){\text{,}}
$$

which may be less than or greater than the original entropy $\mathrm {H} (p(x\mid I))$. However, from the standpoint of the new probability distribution one can estimate that to have used the original code based on $p(x\mid I)$ instead of a new code based on $p(x\mid y,I)$ would have added an expected number of bits:

$$
D_{\text{KL}}{\big (}p(x\mid y,I)\parallel p(x\mid I){\big )}=\sum _{x}p(x\mid y,I)\log {\frac {p(x\mid y,I)}{p(x\mid I)}}
$$

to the message length. This therefore represents the amount of useful information, or information gain, about X, that has been learned by discovering $Y=y$.

If a further piece of data, $Y_{2}=y_{2}$, subsequently comes in, the probability distribution for x can be updated further, to give a new best guess $p(x\mid y_{1},y_{2},I)$. If one reinvestigates the information gain for using $p(x\mid y_{1},I)$ rather than $p(x\mid I)$, it turns out that it may be either greater or less than previously estimated:

$$
\sum _{x}p(x\mid y_{1},y_{2},I)\log {\frac {p(x\mid y_{1},y_{2},I)}{p(x\mid I)}}
$$

 may be ≤ or \> than $\sum _{x}p(x\mid y_{1},I)\log {\frac {p(x\mid y_{1},I)}{p(x\mid I)}}$

and so the combined information gain does *not* obey the triangle inequality:

$$
D_{\text{KL}}{\big (}p(x\mid y_{1},y_{2},I)\parallel p(x\mid I){\big )}
$$

 may be \<, = or \> than $D_{\text{KL}}{\big (}p(x\mid y_{1},y_{2},I)\parallel p(x\mid y_{1},I){\big )}+D_{\text{KL}}{\big (}p(x\mid y_{1},I)\parallel p(x\mid I){\big )}$

All one can say is that on *average*, averaging using $p(y_{2}\mid y_{1},x,I)$, the two sides will average out.

### Bayesian experimental design

A common goal in [Bayesian experimental design](https://en.wikipedia.org/wiki/Bayesian_experimental_design) is to maximise the expected relative entropy between the prior and the posterior. When posteriors are approximated to be Gaussian distributions, a design maximising the expected relative entropy is called [Bayes d-optimal](https://en.wikipedia.org/wiki/D-optimal_design).

## Discrimination information

Relative entropy $D_{\text{KL}}{\bigl (}p(x\mid H_{1})\parallel p(x\mid H_{0}){\bigr )}$ can also be interpreted as the expected **discrimination information** for $H_{1}$ over $H_{0}$: the mean information per sample for discriminating in favor of a hypothesis $H_{1}$ against a hypothesis $H_{0}$, when hypothesis $H_{1}$ is true. Another name for this quantity, given to it by [I. J. Good](https://en.wikipedia.org/wiki/I._J._Good), is the expected weight of evidence for $H_{1}$ over $H_{0}$ to be expected from each sample.

The expected weight of evidence for $H_{1}$ over $H_{0}$ is **not** the same as the information gain expected per sample about the probability distribution $p(H)$ of the hypotheses,

$$
D_{\text{KL}}(p(x\mid H_{1})\parallel p(x\mid H_{0}))\neq IG=D_{\text{KL}}(p(H\mid x)\parallel p(H\mid I)){\text{.}}
$$

Either of the two quantities can be used as a [utility function](https://en.wikipedia.org/wiki/Utility_function) in Bayesian experimental design, to choose an optimal next question to investigate: but they will in general lead to rather different experimental strategies.

On the entropy scale of *information gain* there is very little difference between near certainty and absolute certainty—coding according to a near certainty requires hardly any more bits than coding according to an absolute certainty. On the other hand, on the [logit](https://en.wikipedia.org/wiki/Logit) scale implied by weight of evidence, the difference between the two is enormous – infinite perhaps; this might reflect the difference between being almost sure (on a probabilistic level) that, say, the [Riemann hypothesis](https://en.wikipedia.org/wiki/Riemann_hypothesis) is correct, compared to being certain that it is correct because one has a [mathematical proof](https://en.wikipedia.org/wiki/Mathematical_proof). These two different scales of [loss function](https://en.wikipedia.org/wiki/Loss_function) for uncertainty are *both* useful, according to how well each reflects the particular circumstances of the problem in question.

### Principle of minimum discrimination information

The idea of relative entropy as discrimination information led Kullback to propose the Principle of Minimum Discrimination Information (**MDI**): given new facts, a new distribution f should be chosen which is as hard to discriminate from the original distribution $f_{0}$ as possible; so that the new data produces as small an information gain $D_{\text{KL}}(f\parallel f_{0})$ as possible.

For example, if one had a prior distribution $p(x,a)$ over x and a, and subsequently learnt the true distribution of a was $u(a)$, then the relative entropy between the new joint distribution for x and a, $q(x\mid a)u(a)$, and the earlier prior distribution would be:

$$
D_{\text{KL}}(q(x\mid a)u(a)\parallel p(x,a))=\operatorname {E} _{u(a)}\left\{D_{\text{KL}}(q(x\mid a)\parallel p(x\mid a))\right\}+D_{\text{KL}}(u(a)\parallel p(a)),
$$

i.e. the sum of the relative entropy of $p(a)$ the prior distribution for a from the updated distribution $u(a)$, plus the expected value (using the probability distribution $u(a)$) of the relative entropy of the prior conditional distribution $p(x\mid a)$ from the new conditional distribution $q(x\mid a)$. (Note that often the later expected value is called the *conditional relative entropy* (or *conditional Kullback–Leibler divergence*) and denoted by $D_{\text{KL}}(q(x\mid a)\parallel p(x\mid a))$) This is minimized if $q(x\mid a)=p(x\mid a)$ over the whole support of $u(a)$; and we note that this result incorporates Bayes' theorem, if the new distribution $u(a)$ is in fact a δ function representing certainty that a has one particular value.

MDI can be seen as an extension of [Laplace](https://en.wikipedia.org/wiki/Laplace)'s [Principle of Insufficient Reason](https://en.wikipedia.org/wiki/Principle_of_Insufficient_Reason), and the [Principle of Maximum Entropy](https://en.wikipedia.org/wiki/Principle_of_Maximum_Entropy) of [E.T. Jaynes](https://en.wikipedia.org/wiki/E.T._Jaynes). In particular, it is the natural extension of the principle of maximum entropy from discrete to continuous distributions, for which Shannon entropy ceases to be so useful (see *[differential entropy](https://en.wikipedia.org/wiki/Differential_entropy)*), but the relative entropy continues to be just as relevant.

In the engineering literature, MDI is sometimes called the **Principle of Minimum Cross-Entropy** (MCE) or **Minxent** for short. Minimising relative entropy from m to p with respect to m is equivalent to minimizing the cross-entropy of p and m, since

$$
\mathrm {H} (p,m)=\mathrm {H} (p)+D_{\text{KL}}(p\parallel m),
$$

which is appropriate if one is trying to choose an adequate approximation to p. However, this is just as often *not* the task one is trying to achieve. Instead, just as often it is m that is some fixed prior reference measure, and p that one is attempting to optimise by minimising $D_{\text{KL}}(p\parallel m)$ subject to some constraint. This has led to some ambiguity in the literature, with some authors attempting to resolve the inconsistency by redefining cross-entropy to be $D_{\text{KL}}(p\parallel m)$, rather than $\mathrm {H} (p,m)$ <sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>.

## Relationship to available work

![[media/c721445f48a98be0b0d2df7403d5adc61f4f9ad5.png]]
Pressure versus volume plot of available work from a mole of argon gas relative to ambient, calculated as $T_{o}$ times the Kullback–Leibler divergence

[Surprisals](https://en.wikipedia.org/wiki/Surprisal) add where probabilities multiply. The surprisal for an event of probability p is defined as $s=-k\ln p$. If k is $\left\{1,1/\ln 2,1.38\times 10^{-23}\right\}$ then surprisal is in $\{$nats, bits, or $J/K\}$ so that, for instance, there are N bits of surprisal for landing all "heads" on a toss of N coins.

Best-guess states (e.g. for atoms in a gas) are inferred by maximizing the *average surprisal* S ([[Entropy]]) for a given set of control parameters (like pressure P or volume V). This constrained [entropy maximization](https://en.wikipedia.org/wiki/Entropy_maximization), both classically and quantum mechanically, minimizes [Gibbs](https://en.wikipedia.org/wiki/Josiah_Willard_Gibbs) availability in entropy units $A\equiv -k\ln Z$ where Z is a constrained multiplicity or [partition function](https://en.wikipedia.org/wiki/Partition_function_(mathematics) "Partition function (mathematics)").

When temperature T is fixed, free energy ($T\times A$) is also minimized. Thus if $T,V$ and number of molecules N are constant, the [Helmholtz free energy](https://en.wikipedia.org/wiki/Helmholtz_free_energy) $F\equiv U-TS$ (where U is energy and S is entropy) is minimized as a system "equilibrates." If T and P are held constant (say during processes in your body), the [Gibbs free energy](https://en.wikipedia.org/wiki/Gibbs_free_energy) $G=U+PV-TS$ is minimized instead. The change in free energy under these conditions is a measure of available [work](https://en.wikipedia.org/wiki/Work_(thermodynamics) "Work (thermodynamics)") that might be done in the process. Thus available work for an ideal gas at constant temperature $T_{o}$ and pressure $P_{o}$ is $W=\Delta G=NkT_{o}\Theta (V/V_{o})$ where $V_{o}=NkT_{o}/P_{o}$ and $\Theta (x)=x-1-\ln x\geq 0$ (see also [Gibbs inequality](https://en.wikipedia.org/wiki/Gibbs_inequality)).

More generally the [work available](https://en.wikipedia.org/wiki/Exergy) relative to some ambient is obtained by multiplying ambient temperature $T_{o}$ by relative entropy or *net surprisal* $\Delta I\geq 0,$ defined as the average value of $k\ln(p/p_{o})$ where $p_{o}$ is the probability of a given state under ambient conditions. For instance, the work available in equilibrating a monatomic ideal gas to ambient values of $V_{o}$ and $T_{o}$ is thus $W=T_{o}\Delta I$, where relative entropy

$$
\Delta I=Nk\left[\Theta {\left({\frac {V}{V_{o}}}\right)}+{\frac {3}{2}}\Theta {\left({\frac {T}{T_{o}}}\right)}\right].
$$

The resulting contours of constant relative entropy, shown at right for a mole of Argon at standard temperature and pressure, for example put limits on the conversion of hot to cold as in flame-powered air-conditioning or in the unpowered device to convert boiling-water to ice-water discussed here. Thus relative entropy measures thermodynamic availability in bits.

## Quantum information theory

For [density matrices](https://en.wikipedia.org/wiki/Density_matrix) P and Q on a [Hilbert space](https://en.wikipedia.org/wiki/Hilbert_space), the [quantum relative entropy](https://en.wikipedia.org/wiki/Quantum_relative_entropy) from Q to P is defined to be

$$
D_{\text{KL}}(P\parallel Q)=\operatorname {Tr} (P(\log P-\log Q)).
$$

In [quantum information science](https://en.wikipedia.org/wiki/Quantum_information_science) the minimum of $D_{\text{KL}}(P\parallel Q)$ over all separable states Q can also be used as a measure of [entanglement](https://en.wikipedia.org/wiki/Quantum_entanglement) in the state P.

## Relationship between models and reality

Just as relative entropy of "actual from ambient" measures thermodynamic availability, relative entropy of "reality from a model" is also useful even if the only clues we have about reality are some experimental measurements. In the former case relative entropy describes *distance to equilibrium* or (when multiplied by ambient temperature) the amount of *available work*, while in the latter case it tells you about surprises that reality has up its sleeve or, in other words, *how much the model has yet to learn*.

Although this tool for evaluating models against systems that are accessible experimentally may be applied in any field, its application to selecting a [statistical model](https://en.wikipedia.org/wiki/Statistical_model) via [Akaike information criterion](https://en.wikipedia.org/wiki/Akaike_information_criterion) are particularly well described in papers and a book by Burnham and Anderson. In a nutshell the relative entropy of reality from a model may be estimated, to within a constant additive term, by a function of the deviations observed between data and the model's predictions (like the [mean squared deviation](https://en.wikipedia.org/wiki/Mean_squared_deviation)) . Estimates of such divergence for models that share the same additive term can in turn be used to select among models.

When trying to fit parametrized models to data there are various estimators which attempt to minimize relative entropy, such as [maximum likelihood](https://en.wikipedia.org/wiki/Maximum_likelihood) and [maximum spacing](https://en.wikipedia.org/wiki/Maximum_spacing_estimation) estimators.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

## Symmetrised divergence

 also considered the symmetrized function:

$$
D_{\text{KL}}(P\parallel Q)+D_{\text{KL}}(Q\parallel P)
$$

which they referred to as the "divergence", though today the "KL divergence" refers to the asymmetric function (see [§ Etymology](#Etymology) for the evolution of the term). This function is symmetric and nonnegative, and had already been defined and used by [Harold Jeffreys](https://en.wikipedia.org/wiki/Harold_Jeffreys) in 1948; it is accordingly called the **Jeffreys divergence**.

This quantity has sometimes been used for [feature selection](https://en.wikipedia.org/wiki/Feature_selection) in [classification](https://en.wikipedia.org/wiki/Statistical_classification) problems, where P and Q are the conditional [[Probability Density Function|Probability density functions]] of a feature under two different classes. In the Banking and Finance industries, this quantity is referred to as **Population Stability Index** (**PSI**), and is used to assess distributional shifts in model features through time.

An alternative is given via the $\lambda$-divergence,

$$
D_{\lambda }(P\parallel Q)=\lambda D_{\text{KL}}(P\parallel \lambda P+(1-\lambda )Q)+(1-\lambda )D_{\text{KL}}(Q\parallel \lambda P+(1-\lambda )Q){\text{,}}
$$

which can be interpreted as the expected information gain about X from discovering which probability distribution X is drawn from, P or Q, if they currently have probabilities $\lambda$ and $1-\lambda$ respectively.<sup>\[*[clarification needed](https://en.wikipedia.org/wiki/Wikipedia:Please_clarify)*\]</sup> <sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

The value $\lambda =0.5$ gives the [[Jensen-Shannon Divergence|Jensen–Shannon divergence]], defined by

$$
D_{\text{JS}}={\tfrac {1}{2}}D_{\text{KL}}(P\parallel M)+{\tfrac {1}{2}}D_{\text{KL}}(Q\parallel M)
$$

where M is the average of the two distributions,

$$
M={\tfrac {1}{2}}\left(P+Q\right){\text{.}}
$$

We can also interpret $D_{\text{JS}}$ as the capacity of a noisy information channel with two inputs giving the output distributions P and Q. The Jensen–Shannon divergence, like all f-divergences, is *locally* proportional to the [Fisher information metric](https://en.wikipedia.org/wiki/Fisher_information_metric). It is similar to the [Hellinger metric](https://en.wikipedia.org/wiki/Hellinger_metric) (in the sense that it induces the same affine connection on a [statistical manifold](https://en.wikipedia.org/wiki/Statistical_manifold)).

Furthermore, the Jensen–Shannon divergence can be generalized using abstract statistical M-mixtures relying on an abstract mean M.

## Relationship to other probability-distance measures

There are many other important measures of [probability distance](https://en.wikipedia.org/wiki/Statistical_distance). Some of these are particularly connected with relative entropy. For example:

- The [total-variation distance](https://en.wikipedia.org/wiki/Total-variation_distance_of_probability_measures), $\delta (p,q)$. This is connected to the divergence through [Pinsker's inequality](https://en.wikipedia.org/wiki/Pinsker%27s_inequality): 

$$
\delta (P,Q)\leq {\sqrt {{\tfrac {1}{2}}D_{\text{KL}}(P\parallel Q)}}.
$$

 Pinsker's inequality is vacuous for any distributions where $D_{\mathrm {KL} }(P\parallel Q)>2$, since the total variation distance is at most 1. For such distributions, an alternative bound can be used, due to [Bretagnolle and Huber](https://en.wikipedia.org/wiki/Bretagnolle%E2%80%93Huber_inequality) (see, also, Tsybakov): 

$$
\delta (P,Q)\leq {\sqrt {1-e^{-D_{\mathrm {KL} }(P\parallel Q)}}}.
$$

- The family of [Rényi divergences](https://en.wikipedia.org/wiki/R%C3%A9nyi_divergence) generalize relative entropy. Depending on the value of a certain parameter, $\alpha$, various inequalities may be deduced.

Other notable measures of distance include the [Hellinger distance](https://en.wikipedia.org/wiki/Hellinger_distance), *histogram intersection*, *[Chi-squared statistic](https://en.wikipedia.org/wiki/Chi-squared_test)*, *quadratic form distance*, *[match distance](https://en.wikipedia.org/wiki/Matching_distance)*, *[Kolmogorov–Smirnov distance](https://en.wikipedia.org/wiki/Kolmogorov%E2%80%93Smirnov_test)*, and *[earth mover's distance](https://en.wikipedia.org/wiki/Earth_mover%27s_distance)*.

## Data differencing

Just as *absolute* entropy serves as theoretical background for [data *compression*](https://en.wikipedia.org/wiki/Data_compression), *relative* entropy serves as theoretical background for [data *differencing*](https://en.wikipedia.org/wiki/Data_differencing) – the absolute entropy of a set of data in this sense being the data required to reconstruct it (minimum compressed size), while the relative entropy of a target set of data, given a source set of data, is the data required to reconstruct the target *given* the source (minimum size of a [patch](https://en.wikipedia.org/wiki/Patch_(computing) "Patch (computing)")).

## See also

- [Akaike information criterion](https://en.wikipedia.org/wiki/Akaike_information_criterion)
- [Bayesian information criterion](https://en.wikipedia.org/wiki/Bayesian_information_criterion)
- [Bregman divergence](https://en.wikipedia.org/wiki/Bregman_divergence)
- [[Cross-Entropy]]
- [Deviance information criterion](https://en.wikipedia.org/wiki/Deviance_information_criterion)
- [Entropic value at risk](https://en.wikipedia.org/wiki/Entropic_value_at_risk)
- [Entropy power inequality](https://en.wikipedia.org/wiki/Entropy_power_inequality)
- [Hellinger distance](https://en.wikipedia.org/wiki/Hellinger_distance)
- [Information gain in decision trees](https://en.wikipedia.org/wiki/Information_gain_in_decision_trees)
- [Information gain ratio](https://en.wikipedia.org/wiki/Information_gain_ratio)
- [Information theory and measure theory](https://en.wikipedia.org/wiki/Information_theory_and_measure_theory)
- [[Jensen-Shannon Divergence|Jensen–Shannon divergence]]
- [Quantum relative entropy](https://en.wikipedia.org/wiki/Quantum_relative_entropy)
- [Solomon Kullback](https://en.wikipedia.org/wiki/Solomon_Kullback) and [Richard Leibler](https://en.wikipedia.org/wiki/Richard_Leibler)
- [Bhattacharyya distance](https://en.wikipedia.org/wiki/Bhattacharyya_distance)

## References

1.  ^   Csiszar, I (February 1975). ["I-Divergence Geometry of Probability Distributions and Minimization Problems"](https://doi.org/10.1214%2Faop%2F1176996454). *Ann. Probab*. **3** (1): 146–158. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/aop/1176996454](https://doi.org/10.1214%2Faop%2F1176996454).
2.  [Kullback, S.](https://en.wikipedia.org/wiki/Solomon_Kullback); [Leibler, R.A.](https://en.wikipedia.org/wiki/Richard_Leibler) (1951). ["On information and sufficiency"](https://doi.org/10.1214%2Faoms%2F1177729694). *[Annals of Mathematical Statistics](https://en.wikipedia.org/wiki/Annals_of_Mathematical_Statistics)*. **22** (1): 79–86. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/aoms/1177729694](https://doi.org/10.1214%2Faoms%2F1177729694). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2236703](https://www.jstor.org/stable/2236703). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0039968](https://mathscinet.ams.org/mathscinet-getitem?mr=0039968).
3.  ^     .
4.  ^      , p. 11.
5.  ^   , p. 28.
6.  ^   , p. 80.
7.  ^   , p. 158.
8.  , p. 7.
9.  [Kullback, S.](https://en.wikipedia.org/wiki/Solomon_Kullback) (1987). "Letter to the Editor: The Kullback–Leibler distance". *[The American Statistician](https://en.wikipedia.org/wiki/The_American_Statistician)*. **41** (4): 340–341. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/00031305.1987.10475510](https://doi.org/10.1080%2F00031305.1987.10475510). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2684769](https://www.jstor.org/stable/2684769).
10. , p. 6.
11. MacKay, David J.C. (2003). [Information Theory, Inference, and Learning Algorithms](https://books.google.com/books?id=AKuMj4PN_EMC) (1st ed.). Cambridge University Press. p. 34. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-64298-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-64298-9) – via Google Books.
12. ["What's the maximum value of Kullback-Leibler (KL) divergence?"](https://stats.stackexchange.com/q/351947). Machine learning. *Statistics Stack Exchange (stats.stackexchange.com)*. Cross validated.
13. ["In what situations is the integral equal to infinity?"](https://math.stackexchange.com/q/20961). Integration. *Mathematics Stack Exchange (math.stackexchange.com)*.
14. Bishop, Christopher M. *Pattern recognition and machine learning*. p. 55. [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [1334664824](https://search.worldcat.org/oclc/1334664824).
15. , p. 5.
16. Burnham, K. P.; Anderson, D. R. (2002). [Model Selection and Multi-Model Inference](https://archive.org/details/modelselectionmu0000burn) (2nd ed.). Springer. p. [51](https://archive.org/details/modelselectionmu0000burn/page/51). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-95364-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-95364-9).
17. Abdulkadirov, Ruslan; Lyakhov, Pavel; Nagornov, Nikolay (January 2023). ["Survey of Optimization Algorithms in Modern Neural Networks"](https://doi.org/10.3390%2Fmath11112466). *Mathematics*. **11** (11): 2466. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3390/math11112466](https://doi.org/10.3390%2Fmath11112466). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [2227-7390](https://search.worldcat.org/issn/2227-7390).
18. Matassa, Marco (December 2021). ["Fubini-Study metrics and Levi-Civita connections on quantum projective spaces"](https://doi.org/10.1016%2Fj.aim.2021.108101). *[Advances in Mathematics](https://en.wikipedia.org/wiki/Advances_in_Mathematics)*. **393** 108101. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2010.03291](https://arxiv.org/abs/2010.03291). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.aim.2021.108101](https://doi.org/10.1016%2Fj.aim.2021.108101). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0001-8708](https://search.worldcat.org/issn/0001-8708).
19. Lan, Guanghui (March 2023). ["Policy mirror descent for reinforcement learning: linear convergence, new sampling complexity, and generalized problem classes"](https://link.springer.com/article/10.1007/s10107-022-01816-5). *Mathematical Programming*. **198** (1): 1059–1106. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2102.00135](https://arxiv.org/abs/2102.00135). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s10107-022-01816-5](https://doi.org/10.1007%2Fs10107-022-01816-5). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1436-4646](https://search.worldcat.org/issn/1436-4646).
20. Kelly, J. L. Jr. (1956). "A New Interpretation of Information Rate". *Bell Syst. Tech. J*. **2** (4): 917–926. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1002/j.1538-7305.1956.tb03809.x](https://doi.org/10.1002%2Fj.1538-7305.1956.tb03809.x).
21. Soklakov, A. N. (2020). ["Economics of Disagreement—Financial Intuition for the Rényi Divergence"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7517462). *Entropy*. **22** (8): 860. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1811.08308](https://arxiv.org/abs/1811.08308). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2020Entrp..22..860S](https://ui.adsabs.harvard.edu/abs/2020Entrp..22..860S). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3390/e22080860](https://doi.org/10.3390%2Fe22080860). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [7517462](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7517462). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [33286632](https://pubmed.ncbi.nlm.nih.gov/33286632).
22. Soklakov, A. N. (2023). "Information Geometry of Risks and Returns". *Risk*. **June**. [SSRN](https://en.wikipedia.org/wiki/SSRN_(identifier)) [4134885](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4134885).
23. Henide, Karim (30 September 2024). "Flow Rider: Tradable Ecosystems' Relative Entropy of Flows As a Determinant of Relative Value". *The Journal of Investing*. **33** (6): 34–58. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3905/joi.2024.1.321](https://doi.org/10.3905%2Fjoi.2024.1.321).
24. Sanov, I.N. (1957). "On the probability of large deviations of random magnitudes". *Mat. Sbornik*. **42** (84): 11–44.
25. Novak S.Y. (2011), *Extreme Value Methods with Applications to Finance* ch. 14.5 ([Chapman & Hall](https://en.wikipedia.org/wiki/Chapman_%26_Hall)). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4398-3574-6](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4398-3574-6).
26. Hobson, Arthur (1971). *Concepts in statistical mechanics*. New York: Gordon and Breach. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-677-03240-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-677-03240-5).
28. See the section "differential entropy – 4" in [Relative Entropy](http://videolectures.net/nips09_verdu_re/) video lecture by [Sergio Verdú](https://en.wikipedia.org/wiki/Sergio_Verd%C3%BA) [NIPS](https://en.wikipedia.org/wiki/Conference_on_Neural_Information_Processing_Systems) 2009
29. Donsker, Monroe D.; Varadhan, SR Srinivasa (1983). "Asymptotic evaluation of certain Markov process expectations for large time. IV". *Communications on Pure and Applied Mathematics*. **36** (2): 183–212. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1002/cpa.3160360204](https://doi.org/10.1002%2Fcpa.3160360204).
30. Duchi J. ["Derivations for Linear Algebra and Optimization"](https://web.stanford.edu/~jduchi/projects/general_notes.pdf) (PDF). p. 13.
31. Belov, Dmitry I.; Armstrong, Ronald D. (2011-04-15). "Distributions of the Kullback-Leibler divergence with applications". *British Journal of Mathematical and Statistical Psychology*. **64** (2): 291–309. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1348/000711010x522227](https://doi.org/10.1348%2F000711010x522227). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0007-1102](https://search.worldcat.org/issn/0007-1102). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [21492134](https://pubmed.ncbi.nlm.nih.gov/21492134).
32. ^   Buchner, Johannes (2022-04-29). *An intuition for physicists: information gain from experiments*. [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [1363563215](https://search.worldcat.org/oclc/1363563215).
33. Nielsen, Frank; Garcia, Vincent (2011). "Statistical exponential families: A digest with flash cards". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[0911.4863](https://arxiv.org/abs/0911.4863) \[[cs.LG](https://arxiv.org/archive/cs.LG)\].
34. ^   Cover, Thomas M.; Thomas, Joy A. (1991), *Elements of Information Theory*, [John Wiley & Sons](https://en.wikipedia.org/wiki/John_Wiley_%26_Sons), p. 22
35. Chaloner, K.; Verdinelli, I. (1995). ["Bayesian experimental design: a review"](https://doi.org/10.1214%2Fss%2F1177009939). *[Statistical Science](https://en.wikipedia.org/wiki/Statistical_Science)*. **10** (3): 273–304. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/ss/1177009939](https://doi.org/10.1214%2Fss%2F1177009939). [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[11299/199630](https://hdl.handle.net/11299%2F199630).
36. Press, W.H.; Teukolsky, S.A.; Vetterling, W.T.; Flannery, B.P. (2007). ["Section 14.7.2. Kullback–Leibler Distance"](http://apps.nrbook.com/empanel/index.html#pg=756). [*Numerical Recipes: The Art of Scientific Computing*](https://en.wikipedia.org/wiki/Numerical_Recipes) (3rd ed.). Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-88068-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-88068-8).
37. Tribus, Myron (1959). [Thermostatics and Thermodynamics: An Introduction to Energy, Information and States of Matter, with Engineering Applications](https://books.google.com/books?id=eyrYrQEACAAJ). Van Nostrand.
38. Jaynes, E. T. (1957). ["Information theory and statistical mechanics"](http://bayes.wustl.edu/etj/articles/theory.1.pdf) (PDF). *Physical Review*. **106** (4): 620–630. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1957PhRv..106..620J](https://ui.adsabs.harvard.edu/abs/1957PhRv..106..620J). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1103/physrev.106.620](https://doi.org/10.1103%2Fphysrev.106.620). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [17870175](https://api.semanticscholar.org/CorpusID:17870175).
39. Jaynes, E. T. (1957). ["Information theory and statistical mechanics II"](http://bayes.wustl.edu/etj/articles/theory.2.pdf) (PDF). *Physical Review*. **108** (2): 171–190. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1957PhRv..108..171J](https://ui.adsabs.harvard.edu/abs/1957PhRv..108..171J). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1103/physrev.108.171](https://doi.org/10.1103%2Fphysrev.108.171).
40. Gibbs, Josiah Willard (1871). [A Method of Geometrical Representation of the Thermodynamic Properties of Substances by Means of Surfaces](https://books.google.com/books?id=6ijzXwAACAAJ). The Academy. footnote page 52.
41. Tribus, M.; McIrvine, E. C. (1971). "Energy and information". *Scientific American*. **224** (3): 179–186. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1971SciAm.225c.179T](https://ui.adsabs.harvard.edu/abs/1971SciAm.225c.179T). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1038/scientificamerican0971-179](https://doi.org/10.1038%2Fscientificamerican0971-179).
42. Fraundorf, P. (2007). ["Thermal roots of correlation-based complexity"](http://www3.interscience.wiley.com/cgi-bin/abstract/117861985/ABSTRACT). *Complexity*. **13** (3): 18–26. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1103.2481](https://arxiv.org/abs/1103.2481). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2008Cmplx..13c..18F](https://ui.adsabs.harvard.edu/abs/2008Cmplx..13c..18F). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1002/cplx.20195](https://doi.org/10.1002%2Fcplx.20195). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [20794688](https://api.semanticscholar.org/CorpusID:20794688). `{{`[`cite journal`](https://en.wikipedia.org/wiki/Template:Cite_journal)`}}`: `|archive-url=` is malformed: timestamp ([help](https://en.wikipedia.org/wiki/Help:CS1_errors#archive_url))
43. Burnham, K.P.; Anderson, D.R. (2001). ["Kullback–Leibler information as a basis for strong inference in ecological studies"](https://doi.org/10.1071%2FWR99107). *Wildlife Research*. **28** (2): 111–119. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1071/WR99107](https://doi.org/10.1071%2FWR99107).
44. Burnham, Kenneth P. (December 2010). *Model selection and multimodel inference: a practical information-theoretic approach*. Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4419-2973-0](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4419-2973-0). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [878132909](https://search.worldcat.org/oclc/878132909).
45. Nielsen, Frank (2019). ["On the Jensen–Shannon Symmetrization of Distances Relying on Abstract Means"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7514974). *[[Entropy]]*. **21** (5): 485. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1904.04017](https://arxiv.org/abs/1904.04017). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2019Entrp..21..485N](https://ui.adsabs.harvard.edu/abs/2019Entrp..21..485N). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3390/e21050485](https://doi.org/10.3390%2Fe21050485). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [7514974](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7514974). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [33267199](https://pubmed.ncbi.nlm.nih.gov/33267199).
46. Nielsen, Frank (2020). ["On a Generalization of the Jensen–Shannon Divergence and the Jensen–Shannon Centroid"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7516653). *[[Entropy]]*. **22** (2): 221. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1912.00610](https://arxiv.org/abs/1912.00610). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2020Entrp..22..221N](https://ui.adsabs.harvard.edu/abs/2020Entrp..22..221N). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3390/e22020221](https://doi.org/10.3390%2Fe22020221). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [7516653](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7516653). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [33285995](https://pubmed.ncbi.nlm.nih.gov/33285995).
47. Bretagnolle, J.; Huber, C. (1978), "Estimation des densités : Risque minimax", *Séminaire de Probabilités XII*, Lecture Notes in Mathematics (in French), vol. 649, Berlin, Heidelberg: Springer Berlin Heidelberg, pp. 342–363, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/bfb0064610](https://doi.org/10.1007%2Fbfb0064610), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-08761-8](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-08761-8), [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [122597694](https://api.semanticscholar.org/CorpusID:122597694) Lemma 2.1
48. B.), Tsybakov, A. B. (Alexandre (2010). *Introduction to nonparametric estimation*. Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4419-2709-5](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4419-2709-5). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [757859245](https://search.worldcat.org/oclc/757859245).`{{`[`cite book`](https://en.wikipedia.org/wiki/Template:Cite_book)`}}`: CS1 maint: multiple names: authors list ([link](https://en.wikipedia.org/wiki/Category:CS1_maint:_multiple_names:_authors_list)) Equation 2.25.
49. Rubner, Y.; Tomasi, C.; [Guibas, L. J.](https://en.wikipedia.org/wiki/Leonidas_J._Guibas) (2000). "The earth mover's distance as a metric for image retrieval". *[International Journal of Computer Vision](https://en.wikipedia.org/wiki/International_Journal_of_Computer_Vision)*. **40** (2): 99–121. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1023/A:1026543900054](https://doi.org/10.1023%2FA%3A1026543900054). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [14106275](https://api.semanticscholar.org/CorpusID:14106275).

- [Amari, Shun-ichi](https://en.wikipedia.org/wiki/Shun%27ichi_Amari) (2016). *Information Geometry and Its Applications*. Applied Mathematical Sciences. Vol. 194. Springer Japan. pp. XIII, 374. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-4-431-55978-8](https://doi.org/10.1007%2F978-4-431-55978-8). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-4-431-55977-1](https://en.wikipedia.org/wiki/Special:BookSources/978-4-431-55977-1).
- Kullback, Solomon (1959), *Information Theory and Statistics*, [John Wiley & Sons](https://en.wikipedia.org/wiki/John_Wiley_%26_Sons). Republished by [Dover Publications](https://en.wikipedia.org/wiki/Dover_Publications) in 1968; reprinted in 1978: [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-8446-5625-9](https://en.wikipedia.org/wiki/Special:BookSources/0-8446-5625-9).
- Jeffreys, Harold (1948). *Theory of Probability* (Second ed.). Oxford University Press.

## External links

- [Information Theoretical Estimators Toolbox](https://bitbucket.org/szzoli/ite/)
- [Ruby gem for calculating Kullback–Leibler divergence](https://github.com/evansenter/diverge)
- [Jon Shlens' tutorial on Kullback–Leibler divergence and likelihood theory](https://arxiv.org/abs/1404.2000)
- [Matlab code for calculating Kullback–Leibler divergence for discrete distributions](http://www.mathworks.com/matlabcentral/fileexchange/loadFile.do?objectId=13089&objectType=file) [Archived](https://web.archive.org/web/20070929155435/http://www.mathworks.com/matlabcentral/fileexchange/loadFile.do?objectId=13089&objectType=file) 2007-09-29 at the [Wayback Machine](https://en.wikipedia.org/wiki/Wayback_Machine)
- [Sergio Verdú](https://en.wikipedia.org/wiki/Sergio_Verd%C3%BA), [Relative Entropy](http://videolectures.net/nips09_verdu_re/), [NIPS](https://en.wikipedia.org/wiki/Conference_on_Neural_Information_Processing_Systems) 2009. One-hour video lecture.
- [A modern summary of info-theoretic divergence measures](https://arxiv.org/abs/math/0604246)
