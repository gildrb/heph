[[probability-statistics.base]]

> Source: [Random variable](https://en.wikipedia.org/wiki/Random_variable)
> License: Wikipedia content is available under CC BY-SA 4.0.

A **random variable** (also called **random quantity**, **aleatory variable**, or **stochastic variable**) is a [mathematical](https://en.wikipedia.org/wiki/Mathematics) formalization of a quantity or object which depends on [random](https://en.wikipedia.org/wiki/Randomness) events. The term 'random variable' in its mathematical definition refers to neither randomness nor variability but instead is a mathematical [function](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)") in which

- the [domain](https://en.wikipedia.org/wiki/Domain_of_a_function) is the set of possible [outcomes](https://en.wikipedia.org/wiki/Outcome_(probability) "Outcome (probability)") in a [sample space](https://en.wikipedia.org/wiki/Sample_space) (e.g. the set $\{H,T\}$ which are the possible upper sides of a flipped coin heads $H$ or tails $T$ as the result from tossing a coin); and
- the [range](https://en.wikipedia.org/wiki/Range_of_a_function) is a [measurable space](https://en.wikipedia.org/wiki/Measurable_space) (e.g. corresponding to the domain above, the range might be the set $\{-1,1\}$ if say heads $H$ mapped to −1 and $T$ mapped to 1). Typically, the range of a random variable is a subset of the [real numbers](https://en.wikipedia.org/wiki/Real_number).

![[media/28e054ed787bdb586d6d946ff8f7ec79f9a6e3db.png]]
This graph shows how a random variable is a function from all possible outcomes to real values. It also shows how a random variable is used for defining probability mass functions.

Informally, randomness typically represents some fundamental element of chance, such as in the roll of a [die](https://en.wikipedia.org/wiki/Dice); it may also represent uncertainty, such as [measurement error](https://en.wikipedia.org/wiki/Measurement_error). However, the [interpretation of probability](https://en.wikipedia.org/wiki/Interpretation_of_probability) is philosophically complicated, and even in specific cases is not always straightforward. The purely mathematical analysis of random variables is independent of such interpretational difficulties, and can be based upon a rigorous [axiomatic](https://en.wikipedia.org/wiki/Axiom) setup.

In the formal mathematical language of [measure theory](https://en.wikipedia.org/wiki/Measure_theory), a random variable is defined as a [measurable function](https://en.wikipedia.org/wiki/Measurable_function) from a [probability measure space](https://en.wikipedia.org/wiki/Probability_measure_space) (called the *sample space*) to a [measurable space](https://en.wikipedia.org/wiki/Measurable_space). This allows consideration of the [pushforward measure](https://en.wikipedia.org/wiki/Pushforward_measure), which is called the *distribution* of the random variable; the distribution is thus a [probability measure](https://en.wikipedia.org/wiki/Probability_measure) on the set of all possible values of the random variable. It is possible for two random variables to have identical distributions but to differ in significant ways; for instance, they may be [independent](https://en.wikipedia.org/wiki/Independence_(probability_theory) "Independence (probability theory)").

It is common to consider the special cases of [discrete random variables](https://en.wikipedia.org/wiki/Discrete_random_variable) and [absolutely continuous random variables](https://en.wikipedia.org/wiki/Probability_distribution#Absolutely_continuous_probability_distribution), corresponding to whether a random variable is valued in a countable subset or in an interval of [real numbers](https://en.wikipedia.org/wiki/Real_number). There are other important possibilities, especially in the theory of [stochastic processes](https://en.wikipedia.org/wiki/Stochastic_process), wherein it is natural to consider [random sequences](https://en.wikipedia.org/wiki/Random_sequence) or [random functions](https://en.wikipedia.org/wiki/Random_function). Sometimes a *random variable* is taken to be automatically valued in the real numbers, with more general random quantities instead being called *[random elements](https://en.wikipedia.org/wiki/Random_element)*.

According to [George Mackey](https://en.wikipedia.org/wiki/George_Mackey), [Pafnuty Chebyshev](https://en.wikipedia.org/wiki/Pafnuty_Chebyshev) was the first person "to think systematically in terms of random variables".

## Definition

A **random variable** $X$ is a [measurable function](https://en.wikipedia.org/wiki/Measurable_function) $X\colon \Omega \to E$ from a sample space $\Omega$ as a set of possible [outcomes](https://en.wikipedia.org/wiki/Outcome_(probability) "Outcome (probability)") to a [measurable space](https://en.wikipedia.org/wiki/Measurable_space) $E$. For the measurability of $X$ to be meaningful, the sample space $\Omega$ needs to belong to a [probability triple](https://en.wikipedia.org/wiki/Probability_space) $(\Omega ,{\mathcal {F}},\operatorname {P} )$ (see the [measure-theoretic definition](#Measure-theoretic_definition)). A random variable is often denoted by capital [Roman letters](https://en.wikipedia.org/wiki/Latin_script) such as $X,Y,Z,T$.

The probability that $X$ takes on a value in a measurable set $S\subseteq E$ is written as

$\operatorname {P} (X\in S)=\operatorname {P} (\{\omega \in \Omega \mid X(\omega )\in S\})$.

### Standard case

In many cases, $X$ is [real-valued](https://en.wikipedia.org/wiki/Real_number), i.e. $E=\mathbb {R}$. In some contexts, the term [random element](https://en.wikipedia.org/wiki/Random_element) (see [extensions](#Extensions)) is used to denote a random variable not of this form.

When the [image](https://en.wikipedia.org/wiki/Image_(mathematics) "Image (mathematics)") (or range) of $X$ is finite or [countably](https://en.wikipedia.org/wiki/Countable_set) infinite, the random variable is called a **discrete random variable** and its distribution is a [discrete probability distribution](https://en.wikipedia.org/wiki/Discrete_probability_distribution), i.e. can be described by a [probability mass function](https://en.wikipedia.org/wiki/Probability_mass_function) that assigns a probability to each value in the image of $X$. If the image is uncountably infinite (usually an [interval](https://en.wikipedia.org/wiki/Interval_(mathematics) "Interval (mathematics)")) then $X$ is called a **continuous random variable**. In the special case that it is [absolutely continuous](https://en.wikipedia.org/wiki/Absolutely_continuous), its distribution can be described by a [[Probability Density Function]], which assigns probabilities to intervals; in particular, each individual point must necessarily have probability zero for an absolutely continuous random variable. Not all continuous random variables are absolutely continuous.

Any random variable can be described by its [[Cumulative Distribution Function]], which describes the probability that the random variable will be less than or equal to a certain value.

### Extensions

The term "random variable" in statistics is traditionally limited to the [real-valued](https://en.wikipedia.org/wiki/Real_number) case ($E=\mathbb {R}$). In this case, the structure of the real numbers makes it possible to define quantities such as the [expected value](https://en.wikipedia.org/wiki/Expected_value) and [variance](https://en.wikipedia.org/wiki/Variance) of a random variable, its [[Cumulative Distribution Function]], and the [moments](https://en.wikipedia.org/wiki/Moment_(mathematics) "Moment (mathematics)") of its distribution.

However, the definition above is valid for any [measurable space](https://en.wikipedia.org/wiki/Measurable_space) $E$ of values. Thus one can consider random elements of other sets $E$, such as random [Boolean values](https://en.wikipedia.org/wiki/Boolean-valued_function), [categorical values](https://en.wikipedia.org/wiki/Categorical_variable), [complex numbers](https://en.wikipedia.org/wiki/Covariance_matrix#Complex_random_vectors), [vectors](https://en.wikipedia.org/wiki/Random_vector), [matrices](https://en.wikipedia.org/wiki/Random_matrix), [sequences](https://en.wikipedia.org/wiki/Random_sequence), [trees](https://en.wikipedia.org/wiki/Tree_(graph_theory) "Tree (graph theory)"), [sets](https://en.wikipedia.org/wiki/Random_compact_set), [shapes](https://en.wikipedia.org/wiki/Shape), [[Manifold|manifolds]], and [functions](https://en.wikipedia.org/wiki/Random_function). One may then specifically refer to a *random variable of [type](https://en.wikipedia.org/wiki/Data_type) $E$*, or an *$E$-valued random variable*.

This more general concept of a [random element](https://en.wikipedia.org/wiki/Random_element) is particularly useful in disciplines such as [graph theory](https://en.wikipedia.org/wiki/Graph_theory), [machine learning](https://en.wikipedia.org/wiki/Machine_learning), [natural language processing](https://en.wikipedia.org/wiki/Natural_language_processing), and other fields in [discrete mathematics](https://en.wikipedia.org/wiki/Discrete_mathematics) and [computer science](https://en.wikipedia.org/wiki/Computer_science), where one is often interested in modeling the random variation of non-numerical [data structures](https://en.wikipedia.org/wiki/Data_structure). In some cases, it is nonetheless convenient to represent each element of $E$, using one or more real numbers. In this case, a random element may optionally be represented as a [vector of real-valued random variables](https://en.wikipedia.org/wiki/Random_vector) (all defined on the same underlying probability space $\Omega$, which allows the different random variables to [[Mutual Information|covary]]). For example:

- A random word may be represented as a random integer that serves as an index into the vocabulary of possible words. Alternatively, it can be represented as a random indicator vector, whose length equals the size of the vocabulary, where the only values of positive probability are $(1\ 0\ 0\ 0\ \cdots )$, $(0\ 1\ 0\ 0\ \cdots )$, $(0\ 0\ 1\ 0\ \cdots )$ and the position of the 1 indicates the word.
- A random sentence of given length $N$ may be represented as a vector of $N$ random words.
- A [random graph](https://en.wikipedia.org/wiki/Random_graph) on $N$ given vertices may be represented as a $N\times N$ matrix of random variables, whose values specify the [adjacency matrix](https://en.wikipedia.org/wiki/Adjacency_matrix) of the random graph.
- A [random function](https://en.wikipedia.org/wiki/Random_function) $F$ may be represented as a collection of random variables $F(x)$, giving the function's values at the various points $x$ in the function's domain. The $F(x)$ are ordinary real-valued random variables provided that the function is real-valued. For example, a [stochastic process](https://en.wikipedia.org/wiki/Stochastic_process) is a random function of time, a [random vector](https://en.wikipedia.org/wiki/Random_vector) is a random function of some [index set](https://en.wikipedia.org/wiki/Index_set) such as $1,2,\ldots ,n$, and a [random field](https://en.wikipedia.org/wiki/Random_field) is a random function on any set (typically time, space, or a discrete set).

## Distribution functions

If a random variable $X\colon \Omega \to \mathbb {R}$ defined on the probability space $(\Omega ,{\mathcal {F}},\operatorname {P} )$ is given, we can ask questions like "How likely is it that the value of $X$ is equal to 2?". This is the same as the probability of the event $\{\omega :X(\omega )=2\}\,\!$ which is often written as $P(X=2)\,\!$ or $p_{X}(2)$ for short.

Recording all these probabilities of outputs of a random variable $X$ yields the [probability distribution](https://en.wikipedia.org/wiki/Probability_distribution) of $X$. The probability distribution "forgets" about the particular probability space used to define $X$ and only records the probabilities of various output values of $X$. Such a probability distribution, if $X$ is real-valued, can always be captured by its [[Cumulative Distribution Function]]

$F_{X}(x)=\operatorname {P} (X\leq x)$

and sometimes also using a [[Probability Density Function]], $f_{X}$. In [measure-theoretic](https://en.wikipedia.org/wiki/Measure_theory) terms, we use the random variable $X$ to "push-forward" the measure $P$ on $\Omega$ to a measure $p_{X}$ on $\mathbb {R}$. The measure $p_{X}$ is called the "(probability) distribution of $X$" or the "law of $X$".  The density $f_{X}=dp_{X}/d\mu$, the [Radon–Nikodym derivative](https://en.wikipedia.org/wiki/Radon%E2%80%93Nikodym_derivative) of $p_{X}$ with respect to some reference measure $\mu$ on $\mathbb {R}$ (often, this reference measure is the [Lebesgue measure](https://en.wikipedia.org/wiki/Lebesgue_measure) in the case of continuous random variables, or the [counting measure](https://en.wikipedia.org/wiki/Counting_measure) in the case of discrete random variables). The underlying probability space $\Omega$ is a technical device used to guarantee the existence of random variables, sometimes to construct them, and to define notions such as [correlation and dependence](https://en.wikipedia.org/wiki/Correlation_and_dependence) or [independence](https://en.wikipedia.org/wiki/Independence_(probability_theory) "Independence (probability theory)") based on a [joint distribution](https://en.wikipedia.org/wiki/Joint_distribution) of two or more random variables on the same probability space. In practice, one often disposes of the space $\Omega$ altogether and just puts a measure on $\mathbb {R}$ that assigns measure 1 to the whole real line, i.e., one works with probability distributions instead of random variables. See the article on [quantile functions](https://en.wikipedia.org/wiki/Quantile_function) for fuller development.

## Examples

### Discrete random variable

Consider an experiment where a person is chosen at random. An example of a random variable may be the person's height. Mathematically, the random variable is interpreted as a function which maps the person to their height. Associated with the random variable is a probability distribution that allows the computation of the probability that the height is in any subset of possible values, such as the probability that the height is between 180 and 190 cm, or the probability that the height is either less than 150 or more than 200 cm.

Another random variable may be the person's number of children; this is a discrete random variable with non-negative integer values. It allows the computation of probabilities for individual integer values – the probability mass function (PMF) – or for sets of values, including infinite sets. For example, the event of interest may be "an even number of children". For both finite and infinite event sets, their probabilities can be found by adding up the PMFs of the elements; that is, the probability of an even number of children is the infinite sum $\operatorname {PMF} (0)+\operatorname {PMF} (2)+\operatorname {PMF} (4)+\cdots$.

In examples such as these, the [sample space](https://en.wikipedia.org/wiki/Sample_space) is often suppressed, since it is mathematically hard to describe, and the possible values of the random variables are then treated as a sample space. But when two random variables are measured on the same sample space of outcomes, such as the height and number of children being computed on the same random persons, it is easier to track their relationship if it is acknowledged that both height and number of children come from the same random person, for example so that questions of whether such random variables are correlated or not can be posed.

If $\{a_{n}\},\{b_{n}\}$ are countable sets of real numbers, $b_{n}>0$ and $\textstyle \sum _{n}b_{n}=1$, then $F=\sum _{n}b_{n}\delta _{a_{n}}(x)$ is a discrete distribution function. Here $\delta _{t}(x)=0$ for $x<t$, $\delta _{t}(x)=1$ for $x\geq t$. Taking for instance an enumeration of all rational numbers as $\{a_{n}\}$, one gets a discrete function that is not necessarily a [step function](https://en.wikipedia.org/wiki/Step_function) ([piecewise](https://en.wikipedia.org/wiki/Piecewise) constant).

#### Coin toss

The possible outcomes for one coin toss can be described by the sample space $\Omega =\{{\text{heads}},{\text{tails}}\}$. We can introduce a real-valued random variable $Y$ that models a \$1 payoff for a successful bet on heads as follows: 

$$
Y(\omega )={\begin{cases}1,&{\text{if }}\omega ={\text{heads}},\\[6pt]0,&{\text{if }}\omega ={\text{tails}}.\end{cases}}
$$

If the coin is a [fair coin](https://en.wikipedia.org/wiki/Fair_coin), $Y$ has a [probability mass function](https://en.wikipedia.org/wiki/Probability_mass_function) $f_{Y}$ given by: 

$$
f_{Y}(y)={\begin{cases}{\tfrac {1}{2}},&{\text{if }}y=1,\\[6pt]{\tfrac {1}{2}},&{\text{if }}y=0,\end{cases}}
$$

#### Dice roll

![[media/b30fa29ae9e20df54c2e704f19d40b88b473346b.png]]
If the sample space is the set of possible numbers rolled on two dice, and the random variable of interest is the sum <em>S</em> of the numbers on the two dice, then <em>S</em> is a discrete random variable whose distribution is described by the [probability mass function](https://en.wikipedia.org/wiki/Probability_mass_function) plotted as the height of picture columns here.

A random variable can also be used to describe the process of rolling dice and the possible outcomes. The most obvious representation for the two-dice case is to take the set of pairs of numbers *n*<sub>1</sub> and *n*<sub>2</sub> from {1, 2, 3, 4, 5, 6} (representing the numbers on the two dice) as the sample space. The total number rolled (the sum of the numbers in each pair) is then a random variable *X* given by the function that maps the pair to the sum: 

$$
X((n_{1},n_{2}))=n_{1}+n_{2}
$$

 and (if the dice are [fair](https://en.wikipedia.org/wiki/Fair_die)) has a probability mass function *f*<sub>*X*</sub> given by: 

$$
f_{X}(S)={\frac {\min(S-1,13-S)}{36}},{\text{ for }}S\in \{2,3,4,5,6,7,8,9,10,11,12\}
$$

### Continuous random variable

Formally, a continuous random variable is a random variable whose [[Cumulative Distribution Function]] is [continuous](https://en.wikipedia.org/wiki/Continuous_function) everywhere. There are no "[gaps](https://en.wikipedia.org/wiki/Discontinuity_(mathematics)#Jump_discontinuity)", which would correspond to numbers which have a finite probability of [occurring](https://en.wikipedia.org/wiki/Outcome_(probability) "Outcome (probability)"). Instead, continuous random variables [almost never](https://en.wikipedia.org/wiki/Almost_never) take an exact prescribed value *c* (formally, $\forall c\in \mathbb {R} :\;\Pr(X=c)=0$) but there is a positive probability that its value will lie in particular [intervals](https://en.wikipedia.org/wiki/Interval_(mathematics) "Interval (mathematics)") which can be [arbitrarily small](https://en.wikipedia.org/wiki/Arbitrarily_small). Continuous random variables usually admit [[Probability Density Function|probability density functions]] (PDF), which characterize their CDF and [probability measures](https://en.wikipedia.org/wiki/Probability_measure); such distributions are also called [absolutely continuous](https://en.wikipedia.org/wiki/Absolutely_continuous_random_variable); but some continuous distributions are [singular](https://en.wikipedia.org/wiki/Singular_distribution), or mixes of an absolutely continuous part and a singular part.

An example of a continuous random variable would be one based on a spinner that can choose a horizontal direction. Then the values taken by the random variable are directions. We could represent these directions by North, West, East, South, Southeast, etc. However, it is commonly more convenient to map the sample space to a random variable which takes values which are real numbers. This can be done, for example, by mapping a direction to a bearing in degrees clockwise from North. The random variable then takes values which are real numbers from the interval \[0, 360), with all parts of the range being "equally likely". In this case, ***X*** = the angle spun. Any real number has probability zero of being selected, but a positive probability can be assigned to any *range* of values. For example, the probability of choosing a number in \[0, 180\] is 1/2. Instead of speaking of a probability mass function, we say that the probability *density* of ***X*** is 1/360. The probability of a subset of \[0, 360) can be calculated by multiplying the measure of the set by 1/360. In general, the probability of a set for a given continuous random variable can be calculated by integrating the density over the given set.

More formally, given any [interval](https://en.wikipedia.org/wiki/Interval_(mathematics) "Interval (mathematics)") $I=[a,b]=\{x\in \mathbb {R} :a\leq x\leq b\}$, a random variable $X_{I}\sim \operatorname {U} (I)=\operatorname {U} [a,b]$ is called a "[continuous uniform](https://en.wikipedia.org/wiki/Continuous_uniform_distribution) random variable" (CURV) if the probability that it takes a value in a [subinterval](https://en.wikipedia.org/wiki/Subinterval) depends only on the length of the subinterval. This implies that the probability of $X_{I}$ falling in any subinterval $[c,d]\subseteq [a,b]$ is [proportional](https://en.wikipedia.org/wiki/Proportionality_(mathematics) "Proportionality (mathematics)") to the [length](https://en.wikipedia.org/wiki/Lebesgue_measure) of the subinterval, that is, if *a* ≤ *c* ≤ *d* ≤ *b*, one has 

$$
\Pr \left(X_{I}\in [c,d]\right)={\frac {d-c}{b-a}}
$$

 where the last equality results from the [[Probability Axioms|unitarity axiom]] of probability. The [[Probability Density Function]] of a CURV $X\sim \operatorname {U} [a,b]$ is given by the [indicator function](https://en.wikipedia.org/wiki/Indicator_function) of its interval of [support](https://en.wikipedia.org/wiki/Support_(mathematics) "Support (mathematics)") normalized by the interval's length: 

$$
f_{X}(x)={\begin{cases}\displaystyle {1 \over b-a},&a\leq x\leq b\\0,&{\text{otherwise}}.\end{cases}}
$$

Of particular interest is the uniform distribution on the [unit interval](https://en.wikipedia.org/wiki/Unit_interval) $[0,1]$. Samples of any desired [probability distribution](https://en.wikipedia.org/wiki/Probability_distribution) $\operatorname {D}$ can be generated by calculating the [quantile function](https://en.wikipedia.org/wiki/Quantile_function) of $\operatorname {D}$ on a [randomly-generated number](https://en.wikipedia.org/wiki/Random_number_generation) distributed uniformly on the unit interval. This exploits [[Cumulative Distribution Function|properties of cumulative distribution functions]], which are a unifying framework for all random variables.

### Mixed type

A **mixed random variable** is a random variable whose [[Cumulative Distribution Function]] is neither [discrete](https://en.wikipedia.org/wiki/Discrete_random_variable) nor [everywhere-continuous](https://en.wikipedia.org/wiki/Continuous_function). It can be realized as a mixture of a discrete random variable and a continuous random variable; in which case the CDF will be the weighted average of the CDFs of the component variables.

An example of a random variable of mixed type would be based on an experiment where a coin is flipped and the spinner is spun only if the result of the coin toss is heads. If the result is tails, ***X*** = −1; otherwise ***X*** is the value of the spinner as in the preceding example. There is a probability of 1/2 that this random variable will have the value −1. Other ranges of values would have half the probabilities of the last example.

Most generally, every probability distribution on the real line is a mixture of discrete part, singular part, and an absolutely continuous part; see *[Lebesgue's decomposition theorem § Refinement](https://en.wikipedia.org/wiki/Lebesgue%27s_decomposition_theorem#Refinement)*. The discrete part is concentrated on a countable set, but this set may be dense (like the set of all rational numbers).

## Measure-theoretic definition

The most formal, [axiomatic](https://en.wikipedia.org/wiki/Axiomatic) definition of a random variable involves [measure theory](https://en.wikipedia.org/wiki/Measure_theory). Continuous random variables are defined in terms of [sets](https://en.wikipedia.org/wiki/Set_(mathematics) "Set (mathematics)") of numbers, along with functions that map such sets to probabilities. Because of various difficulties (e.g. the [Banach–Tarski paradox](https://en.wikipedia.org/wiki/Banach%E2%80%93Tarski_paradox)) that arise if such sets are insufficiently constrained, it is necessary to introduce what is termed a [[Sigma Algebra|sigma-algebra]] to constrain the possible sets over which probabilities can be defined. Normally, a particular such sigma-algebra is used, the [Borel σ-algebra](https://en.wikipedia.org/wiki/Borel_%CF%83-algebra), which allows for probabilities to be defined over any sets that can be derived either directly from continuous intervals of numbers or by a finite or [countably infinite](https://en.wikipedia.org/wiki/Countably_infinite) number of [unions](https://en.wikipedia.org/wiki/Union_(set_theory) "Union (set theory)") and/or [intersections](https://en.wikipedia.org/wiki/Intersection_(set_theory) "Intersection (set theory)") of such intervals.

The measure-theoretic definition is as follows.

Let $(\Omega ,{\mathcal {F}},P)$ be a [probability space](https://en.wikipedia.org/wiki/Probability_space) and $(E,{\mathcal {E}})$ a [measurable space](https://en.wikipedia.org/wiki/Measurable_space). Then an **$(E,{\mathcal {E}})$-valued random variable** is a measurable function $X:\Omega \to E$, which means that, for every subset $B\in {\mathcal {E}}$, its [preimage](https://en.wikipedia.org/wiki/Preimage) is ${\mathcal {F}}$-measurable; $X^{-1}(B)\in {\mathcal {F}}$, where $X^{-1}(B)=\{\omega :X(\omega )\in B\}$. This definition enables us to measure any subset $B\in {\mathcal {E}}$ in the target space by looking at its preimage, which by assumption is measurable.

In more intuitive terms, a member of $\Omega$ is a possible outcome, a member of ${\mathcal {F}}$ is a measurable subset of possible outcomes, the function $P$ gives the probability of each such measurable subset, $E$ represents the set of values that the random variable can take (such as the set of real numbers), and a member of ${\mathcal {E}}$ is a "well-behaved" (measurable) subset of $E$ (those for which the probability may be determined). The random variable is then a function from any outcome to a quantity, such that the outcomes leading to any useful subset of quantities for the random variable have a well-defined probability.

When $E$ is a [topological space](https://en.wikipedia.org/wiki/Topological_space), then the most common choice for the [σ-algebra](https://en.wikipedia.org/wiki/%CE%A3-algebra) ${\mathcal {E}}$ is the [Borel σ-algebra](https://en.wikipedia.org/wiki/Borel_%CF%83-algebra) ${\mathcal {B}}(E)$, which is the σ-algebra generated by the collection of all open sets in $E$. In such case the $(E,{\mathcal {E}})$-valued random variable is called an **$E$-valued random variable**. Moreover, when the space $E$ is the real line $\mathbb {R}$, then such a real-valued random variable is called simply a **random variable**. Note that we are not giving $\mathbb {R}$ the usual Lebesgue $\sigma$-algebra, which is the completion of the Borel $\sigma$-algebra. This choice allows for more measurable functions $f:\Omega \to \mathbb {R}$ and makes it easier to check that a function $f:\Omega \to \mathbb {R}$ is measurable, as we only need to check that preimages of open sets are measurable.

### Real-valued random variables

In this case the observation space is the set of real numbers. Recall, $(\Omega ,{\mathcal {F}},P)$ is the probability space. For a real observation space, the function $X\colon \Omega \rightarrow \mathbb {R}$ is a real-valued random variable if

$\{\omega :X(\omega )\leq r\}\in {\mathcal {F}}\qquad \forall r\in \mathbb {R} .$

This definition is a special case of the above because the set $\{(-\infty ,r]:r\in \mathbb {R} \}$ generates the Borel σ-algebra on the set of real numbers, and it suffices to check measurability on any generating set. Here we can prove measurability on this generating set by using the fact that $\{\omega :X(\omega )\leq r\}=X^{-1}((-\infty ,r])$.

## Moments

The probability distribution of a random variable is often characterised by a small number of parameters, which also have a practical interpretation. For example, it is often enough to know what its "average value" is. This is captured by the mathematical concept of [expected value](https://en.wikipedia.org/wiki/Expected_value) of a random variable, denoted $\operatorname {E} [X]$, and also called the **first [moment](https://en.wikipedia.org/wiki/Moment_(mathematics) "Moment (mathematics)").** In general, $\operatorname {E} [f(X)]$ is not equal to $f(\operatorname {E} [X])$. Once the "average value" is known, one could then ask how far from this average value the values of $X$ typically are, a question that is answered by the [variance](https://en.wikipedia.org/wiki/Variance) and [standard deviation](https://en.wikipedia.org/wiki/Standard_deviation) of a random variable. $\operatorname {E} [X]$ can be viewed intuitively as an average obtained from an infinite population, the members of which are particular evaluations of $X$.

Mathematically, this is known as the (generalised) [problem of moments](https://en.wikipedia.org/wiki/Problem_of_moments): for a given class of random variables $X$, find a collection $\{f_{i}\}$ of functions such that the expectation values $\operatorname {E} [f_{i}(X)]$ fully characterise the [distribution](https://en.wikipedia.org/wiki/Probability_distribution) of the random variable $X$.

Moments can only be defined for real-valued functions of random variables (or complex-valued, etc.). If the random variable is itself real-valued, then moments of the variable itself can be taken, which are equivalent to moments of the identity function $f(X)=X$ of the random variable. However, even for non-real-valued random variables, moments can be taken of real-valued functions of those variables. For example, for a [categorical](https://en.wikipedia.org/wiki/Categorical_variable) random variable *X* that can take on the [nominal](https://en.wikipedia.org/wiki/Nominal_data) values "red", "blue" or "green", the real-valued function $[X={\text{green}}]$ can be constructed; this uses the [Iverson bracket](https://en.wikipedia.org/wiki/Iverson_bracket), and has the value 1 if $X$ has the value "green", 0 otherwise. Then, the [expected value](https://en.wikipedia.org/wiki/Expected_value) and other moments of this function can be determined.

## Functions of random variables

A new random variable $Y$ can be defined by [applying](https://en.wikipedia.org/wiki/Function_composition) a real [Borel measurable function](https://en.wikipedia.org/wiki/Measurable_function) $g\colon \mathbb {R} \rightarrow \mathbb {R}$ to the outcomes of a [real-valued](https://en.wikipedia.org/wiki/Real-valued) random variable $X$. That is, $Y=g(X)$. The [[Cumulative Distribution Function]] of $Y$ is then

$F_{Y}(y)=\operatorname {P} (g(X)\leq y).$

If function $g$ is invertible (i.e., $h=g^{-1}$ exists, where $h$ is $g$'s [inverse function](https://en.wikipedia.org/wiki/Inverse_function)) and is either [increasing or decreasing](https://en.wikipedia.org/wiki/Monotonic_function), then the previous relation can be extended to obtain

$F_{Y}(y)=\operatorname {P} (g(X)\leq y)={\begin{cases}\operatorname {P} (X\leq h(y))=F_{X}(h(y)),&{\text{if }}h=g^{-1}{\text{ increasing}},\\\\\operatorname {P} (X\geq h(y))=1-F_{X}(h(y)),&{\text{if }}h=g^{-1}{\text{ decreasing}}.\end{cases}}$

With the same hypotheses of invertibility of $g$, assuming also [differentiability](https://en.wikipedia.org/wiki/Differentiability), the relation between the [[Probability Density Function|probability density functions]] can be found by differentiating both sides of the above expression with respect to $y$, in order to obtain

$f_{Y}(y)=f_{X}{\bigl (}h(y){\bigr )}\left|{\frac {dh(y)}{dy}}\right|.$

If there is no invertibility of $g$ but each $y$ admits at most a countable number of roots (i.e., a finite, or countably infinite, number of $x_{i}$ such that $y=g(x_{i})$) then the previous relation between the [[Probability Density Function|probability density functions]] can be generalized with

$f_{Y}(y)=\sum _{i}f_{X}(g_{i}^{-1}(y))\left|{\frac {dg_{i}^{-1}(y)}{dy}}\right|$

where $x_{i}=g_{i}^{-1}(y)$, according to the [inverse function theorem](https://en.wikipedia.org/wiki/Inverse_function_theorem). The formulas for densities do not demand $g$ to be increasing.

In the measure-theoretic, [[Probability Axioms|axiomatic approach]] to probability, if a random variable $X$ on $\Omega$ and a [Borel measurable function](https://en.wikipedia.org/wiki/Measurable_function) $g\colon \mathbb {R} \rightarrow \mathbb {R}$, then $Y=g(X)$ is also a random variable on $\Omega$, since the composition of measurable functions [is also measurable](https://en.wikipedia.org/wiki/Closure_(mathematics) "Closure (mathematics)"). (However, this is not necessarily true if $g$ is [Lebesgue measurable](https://en.wikipedia.org/wiki/Lebesgue_measurable).<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>) The same procedure that allowed one to go from a probability space $(\Omega ,P)$ to $(\mathbb {R} ,dF_{X})$ can be used to obtain the distribution of $Y$.

### Example 1

Let $X$ be a real-valued, [continuous random variable](https://en.wikipedia.org/wiki/Continuous_random_variable) and let $Y=X^{2}$.

$F_{Y}(y)=\operatorname {P} (X^{2}\leq y).$

If $y<0$, then $P(X^{2}\leq y)=0$, so

$F_{Y}(y)=0\qquad {\hbox{if}}\quad y<0.$

If $y\geq 0$, then

$\operatorname {P} (X^{2}\leq y)=\operatorname {P} (|X|\leq {\sqrt {y}})=\operatorname {P} (-{\sqrt {y}}\leq X\leq {\sqrt {y}}),$

so

$F_{Y}(y)=F_{X}({\sqrt {y}})-F_{X}(-{\sqrt {y}})\qquad {\hbox{if}}\quad y\geq 0.$

### Example 2

Suppose $X$ is a random variable with a cumulative distribution

$F_{X}(x)=P(X\leq x)={\frac {1}{(1+e^{-x})^{\theta }}}$

where $\theta >0$ is a fixed parameter. Consider the random variable $Y=\mathrm {log} (1+e^{-X}).$ Then,

$F_{Y}(y)=P(Y\leq y)=P(\mathrm {log} (1+e^{-X})\leq y)=P(X\geq -\mathrm {log} (e^{y}-1)).\,$

The last expression can be calculated in terms of the cumulative distribution of $X$, so

${\begin{aligned}F_{Y}(y)&=1-F_{X}(-\log(e^{y}-1))\\[5pt]&=1-{\frac {1}{(1+e^{\log(e^{y}-1)})^{\theta }}}\\[5pt]&=1-{\frac {1}{(1+e^{y}-1)^{\theta }}}\\[5pt]&=1-e^{-y\theta },\end{aligned}}$

which is the [[Cumulative Distribution Function]] (CDF) of an [exponential distribution](https://en.wikipedia.org/wiki/Exponential_distribution).

### Example 3

Suppose $X$ is a random variable with a [standard normal distribution](https://en.wikipedia.org/wiki/Standard_normal_distribution), whose density is

$f_{X}(x)={\frac {1}{\sqrt {2\pi }}}e^{-x^{2}/2}.$

Consider the random variable $Y=X^{2}$. We can find the density using the above formula for a change of variables:

$f_{Y}(y)=\sum _{i}f_{X}(g_{i}^{-1}(y))\left|{\frac {dg_{i}^{-1}(y)}{dy}}\right|.$

In this case the change is not [monotonic](https://en.wikipedia.org/wiki/Monotonic_function), because every value of $Y$ has two corresponding values of $X$ (one positive and negative). However, because of symmetry, both halves will transform identically, i.e.,

$f_{Y}(y)=2f_{X}(g^{-1}(y))\left|{\frac {dg^{-1}(y)}{dy}}\right|.$

The inverse transformation is

$x=g^{-1}(y)={\sqrt {y}}$

and its derivative is

${\frac {dg^{-1}(y)}{dy}}={\frac {1}{2{\sqrt {y}}}}.$

Then,

$f_{Y}(y)=2{\frac {1}{\sqrt {2\pi }}}e^{-y/2}{\frac {1}{2{\sqrt {y}}}}={\frac {1}{\sqrt {2\pi y}}}e^{-y/2}.$

This is a [chi-squared distribution](https://en.wikipedia.org/wiki/Chi-squared_distribution) with one [degree of freedom](https://en.wikipedia.org/wiki/Degrees_of_freedom_(statistics) "Degrees of freedom (statistics)").

### Example 4

Suppose $X$ is a random variable with a [normal distribution](https://en.wikipedia.org/wiki/Normal_distribution), whose density is

$f_{X}(x)={\frac {1}{\sqrt {2\pi \sigma ^{2}}}}e^{-(x-\mu )^{2}/(2\sigma ^{2})}.$

Consider the random variable $Y=X^{2}.$ We can find the density using the above formula for a change of variables:

$f_{Y}(y)=\sum _{i}f_{X}(g_{i}^{-1}(y))\left|{\frac {dg_{i}^{-1}(y)}{dy}}\right|.$

In this case the change is not [monotonic](https://en.wikipedia.org/wiki/Monotonic), because every value of $Y$ has two corresponding values of $X$ (one positive and negative). Differently from the previous example, in this case however, there is no symmetry and we have to compute the two distinct terms:

$f_{Y}(y)=f_{X}(g_{1}^{-1}(y))\left|{\frac {dg_{1}^{-1}(y)}{dy}}\right|+f_{X}(g_{2}^{-1}(y))\left|{\frac {dg_{2}^{-1}(y)}{dy}}\right|.$

The inverse transformation is

$x=g_{1,2}^{-1}(y)=\pm {\sqrt {y}}$

and its derivative is

${\frac {dg_{1,2}^{-1}(y)}{dy}}=\pm {\frac {1}{2{\sqrt {y}}}}.$

Then,

$f_{Y}(y)={\frac {1}{\sqrt {2\pi \sigma ^{2}}}}{\frac {1}{2{\sqrt {y}}}}(e^{-({\sqrt {y}}-\mu )^{2}/(2\sigma ^{2})}+e^{-(-{\sqrt {y}}-\mu )^{2}/(2\sigma ^{2})}).$

This is a [noncentral chi-squared distribution](https://en.wikipedia.org/wiki/Noncentral_chi-squared_distribution) with one [degree of freedom](https://en.wikipedia.org/wiki/Degree_of_freedom_(statistics)).

## Some properties

- The probability distribution of the sum of two independent random variables is the **[convolution](https://en.wikipedia.org/wiki/Convolution)** of each of their distributions.
- Probability distributions are not a [[Vector Space]] – they are not closed under [linear combinations](https://en.wikipedia.org/wiki/Linear_combination), as these do not preserve non-negativity or total integral 1—but they are closed under [convex combination](https://en.wikipedia.org/wiki/Convex_combination), thus forming a [convex subset](https://en.wikipedia.org/wiki/Convex_subset) of the space of functions (or measures).

## Equivalence of random variables

There are several different senses in which random variables can be considered to be equivalent. Two random variables can be equal, equal almost surely, or equal in distribution.

In increasing order of strength, the precise definition of these notions of equivalence is given below.

### Equality in distribution

If the sample space is a subset of the real line, random variables *X* and *Y* are *equal in distribution* (denoted $X~{\stackrel {d}{=}}~Y$) if they have the same distribution functions:

$\operatorname {P} (X\leq x)=\operatorname {P} (Y\leq x)\quad {\text{for all }}x.$

To be equal in distribution, random variables need not be defined on the same probability space. Two random variables having equal [[Moment Generating Function|moment generating functions]] have the same distribution. This provides, for example, a useful method of checking equality of certain functions of [independent, identically distributed (IID) random variables](https://en.wikipedia.org/wiki/Independent_and_identically_distributed_random_variables). However, the moment generating function exists only for distributions that have a defined [Laplace transform](https://en.wikipedia.org/wiki/Laplace_transform).

### Almost sure equality

Two random variables *X* and *Y* are *equal [almost surely](https://en.wikipedia.org/wiki/Almost_surely)* (denoted $X\;{\stackrel {\text{a.s.}}{=}}\;Y$) if, and only if, the probability that they are different is [zero](https://en.wikipedia.org/wiki/Null_set):

$\operatorname {P} (X\neq Y)=0.$

For all practical purposes in probability theory, this notion of equivalence is as strong as actual equality. It is associated to the following distance:

$d_{\infty }(X,Y)=\operatorname {ess} \sup _{\omega }|X(\omega )-Y(\omega )|,$

where "ess sup" represents the [essential supremum](https://en.wikipedia.org/wiki/Essential_supremum) in the sense of [measure theory](https://en.wikipedia.org/wiki/Measure_theory).

### Equality

Finally, the two random variables *X* and *Y* are *equal* if they are equal as functions on their measurable space:

$X(\omega )=Y(\omega )\qquad {\hbox{for all }}\omega .$

This notion is typically the least useful in probability theory because in practice and in theory, the underlying [measure space](https://en.wikipedia.org/wiki/Measure_space) of the [experiment](https://en.wikipedia.org/wiki/Experiment_(probability_theory) "Experiment (probability theory)") is rarely explicitly characterized or even characterizable.

### Practical difference between notions of equivalence

Since we rarely explicitly construct the probability space underlying a random variable, the difference between these notions of equivalence is somewhat subtle. Essentially, two random variables considered *in isolation* are "practically equivalent" if they are equal in distribution -- but once we relate them to *other* random variables defined on the same probability space, then they only remain "practically equivalent" if they are equal almost surely.

For example, consider the real random variables *A*, *B*, *C*, and *D* all defined on the same probability space. Suppose that *A* and *B* are equal almost surely ($A\;{\stackrel {\text{a.s.}}{=}}\;B$), but *A* and *C* are only equal in distribution ($A~{\stackrel {d}{=}}~C$). Then $A+D\;{\stackrel {\text{a.s.}}{=}}\;B+D$, but in general $A+D\neq C+D$ (not even in distribution). Similarly, we have that the expectation values $\mathbb {E} (AD)=\mathbb {E} (BD)$, but in general $\mathbb {E} (AD)\neq \mathbb {E} (CD)$. Therefore, two random variables that are equal in distribution (but not equal almost surely) can have different [covariances](https://en.wikipedia.org/wiki/Covariance) with a third random variable.

## Convergence

A significant theme in mathematical statistics consists of obtaining convergence results for certain [sequences](https://en.wikipedia.org/wiki/Sequence) of random variables; for instance the [[Law of Large Numbers]] and the [[Central Limit Theorem]].

There are various senses in which a sequence $X_{n}$ of random variables can converge to a random variable $X$. These are explained in the article on [convergence of random variables](https://en.wikipedia.org/wiki/Convergence_of_random_variables).

## See also

- ![[media/1a9c6ad1ccebbc090fc7cd1c94d2142489246997.png]][Mathematics portal](https://en.wikipedia.org/wiki/Portal:Mathematics)

- [Aleatoricism](https://en.wikipedia.org/wiki/Aleatoricism)
- [Algebra of random variables](https://en.wikipedia.org/wiki/Algebra_of_random_variables)
- [Event (probability theory)](https://en.wikipedia.org/wiki/Event_(probability_theory) "Event (probability theory)")
- [Multivariate random variable](https://en.wikipedia.org/wiki/Multivariate_random_variable)
- [Pairwise independent random variables](https://en.wikipedia.org/wiki/Pairwise_independence)
- [Observable variable](https://en.wikipedia.org/wiki/Observable_variable)
- [Random compact set](https://en.wikipedia.org/wiki/Random_compact_set)
- [Random element](https://en.wikipedia.org/wiki/Random_element)
- [Random function](https://en.wikipedia.org/wiki/Random_function)
- [Random measure](https://en.wikipedia.org/wiki/Random_measure)
- [Random number generator](https://en.wikipedia.org/wiki/Random_number_generator)
- [Random variate](https://en.wikipedia.org/wiki/Random_variate)
- [Random vector](https://en.wikipedia.org/wiki/Random_vector)
- [Randomness](https://en.wikipedia.org/wiki/Randomness)
- [Stochastic process](https://en.wikipedia.org/wiki/Stochastic_process)
- [Relationships among probability distributions](https://en.wikipedia.org/wiki/Relationships_among_probability_distributions)

## References

### Inline citations

1.  Deisenroth, Marc Peter (2020). *Mathematics for machine learning*. A. Aldo Faisal, Cheng Soon Ong. Cambridge, United Kingdom: Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-108-47004-9](https://en.wikipedia.org/wiki/Special:BookSources/978-1-108-47004-9). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [1104219401](https://search.worldcat.org/oclc/1104219401).
2.  Blitzstein, Joe; Hwang, Jessica (2014). *Introduction to Probability*. CRC Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9781466575592](https://en.wikipedia.org/wiki/Special:BookSources/9781466575592).
3.  [Mackey, George](https://en.wikipedia.org/wiki/George_Mackey) (July 1980). ["Harmonic analysis as the exploitation of symmetry – a historical survey"](https://www.ams.org/journals/bull/1980-03-01/S0273-0979-1980-14783-7/S0273-0979-1980-14783-7.pdf) (PDF). *[Bulletin of the American Mathematical Society](https://en.wikipedia.org/wiki/Bulletin_of_the_American_Mathematical_Society)*. New Series. **3** (1).
4.  ["Random Variables"](https://www.mathsisfun.com/data/random-variables.html). *www.mathsisfun.com*. Retrieved 2020-08-21.
5.  Yates, Daniel S.; [Moore, David S.](https://en.wikipedia.org/wiki/David_S._Moore); Starnes, Daren S. (2003). [The Practice of Statistics](https://web.archive.org/web/20050209001108/http://bcs.whfreeman.com/yates2e/) (2nd ed.). New York: [Freeman](https://en.wikipedia.org/wiki/W._H._Freeman_and_Company). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-7167-4773-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-7167-4773-4). Archived from [the original](http://bcs.whfreeman.com/yates2e/) on 2005-02-09.
6.  ["Random Variables"](http://www.stat.yale.edu/Courses/1997-98/101/ranvar.htm). *www.stat.yale.edu*. Retrieved 2020-08-21.
7.  Dekking, Frederik Michel; Kraaikamp, Cornelis; Lopuhaä, Hendrik Paul; Meester, Ludolf Erwin (2005). ["A Modern Introduction to Probability and Statistics"](https://doi.org/10.1007/1-84628-168-7). *Springer Texts in Statistics*. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/1-84628-168-7](https://doi.org/10.1007%2F1-84628-168-7). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-85233-896-1](https://en.wikipedia.org/wiki/Special:BookSources/978-1-85233-896-1). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1431-875X](https://search.worldcat.org/issn/1431-875X).
8.  L. Castañeda; V. Arunachalam & S. Dharmaraja (2012). [Introduction to Probability and Stochastic Processes with Applications](https://books.google.com/books?id=zxXRn-Qmtk8C&pg=PA67). Wiley. p. 67. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9781118344941](https://en.wikipedia.org/wiki/Special:BookSources/9781118344941).
9.  [Billingsley, Patrick](https://en.wikipedia.org/wiki/Patrick_Billingsley) (1995). *Probability and Measure* (3rd ed.). Wiley. p. 187. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9781466575592](https://en.wikipedia.org/wiki/Special:BookSources/9781466575592).
10. ^     [Bertsekas, Dimitri P.](https://en.wikipedia.org/wiki/Dimitri_Bertsekas) (2002). *Introduction to Probability*. Tsitsiklis, John N., Τσιτσικλής, Γιάννης Ν. Belmont, Mass.: Athena Scientific. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [188652940X](https://en.wikipedia.org/wiki/Special:BookSources/188652940X). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [51441829](https://search.worldcat.org/oclc/51441829).
11. Steigerwald, Douglas G. ["Economics 245A – Introduction to Measure Theory"](http://faculty.econ.ucsb.edu/~doug/245a/Lectures/Measure%20Theory.pdf) (PDF). University of California, Santa Barbara. Retrieved April 26, 2013.
12. , page 11)

### Literature

- Fristedt, Bert; Gray, Lawrence (1996). [A modern approach to probability theory](https://books.google.com/books?id=5D5O8xyM-kMC). Boston: Birkhäuser. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [3-7643-3807-5](https://en.wikipedia.org/wiki/Special:BookSources/3-7643-3807-5).
- [Billingsley, Patrick](https://en.wikipedia.org/wiki/Patrick_Billingsley) (1995). [Probability and Measure](https://books.google.com/books?id=QyXqOXyxEeIC). New York: Wiley. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [8126517719](https://en.wikipedia.org/wiki/Special:BookSources/8126517719).
- [Kallenberg, Olav](https://en.wikipedia.org/wiki/Olav_Kallenberg) (1986). [Random Measures](https://books.google.com/books?id=bBnvAAAAMAAJ) (4th ed.). Berlin: [Akademie Verlag](https://en.wikipedia.org/wiki/Akademie_Verlag). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-12-394960-2](https://en.wikipedia.org/wiki/Special:BookSources/0-12-394960-2). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0854102](https://mathscinet.ams.org/mathscinet-getitem?mr=0854102).
- Kallenberg, Olav (2001). [Foundations of Modern Probability](https://books.google.com/books?id=L6fhXh13OyMC) (2nd ed.). Berlin: [Springer Verlag](https://en.wikipedia.org/wiki/Springer_Verlag). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-95313-2](https://en.wikipedia.org/wiki/Special:BookSources/0-387-95313-2).
- [Papoulis, Athanasios](https://en.wikipedia.org/wiki/Athanasios_Papoulis) (1965). [Probability, Random Variables, and Stochastic Processes](http://www.mhhe.com/engcs/electrical/papoulis/) (9th ed.). Tokyo: [McGraw–Hill](https://en.wikipedia.org/wiki/McGraw%E2%80%93Hill). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-07-119981-0](https://en.wikipedia.org/wiki/Special:BookSources/0-07-119981-0).

## External links

- ["Random variable"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society), 2001 \[1994\]
- Zukerman, Moshe (2014), [Introduction to Queueing Theory and Stochastic Teletraffic Models](http://www.ee.cityu.edu.hk/~zukerman/classnotes.pdf) (PDF), [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1307.2968](https://arxiv.org/abs/1307.2968)
- Zukerman, Moshe (2014), [Basic Probability Topics](http://www.ee.cityu.edu.hk/~zukerman/probability.pdf) (PDF)
