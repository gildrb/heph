[[ai-math.base]]

> Source: [Probability theory](https://en.wikipedia.org/wiki/Probability_theory)
> License: Wikipedia content is available under CC BY-SA 4.0.

**Probability theory** or **probability calculus** is the branch of [mathematics](https://en.wikipedia.org/wiki/Mathematics) concerned with [probability](https://en.wikipedia.org/wiki/Probability). Although there are several different [probability interpretations](https://en.wikipedia.org/wiki/Probability_interpretations), probability theory treats the concept in a rigorous mathematical manner by expressing it through a set of [axioms](https://en.wikipedia.org/wiki/Axioms_of_probability). Typically these axioms formalise probability in terms of a [probability space](https://en.wikipedia.org/wiki/Probability_space), which assigns a [measure](https://en.wikipedia.org/wiki/Measure_(mathematics) "Measure (mathematics)") taking values between 0 and 1, termed the [probability measure](https://en.wikipedia.org/wiki/Probability_measure), to a set of outcomes called the [sample space](https://en.wikipedia.org/wiki/Sample_space). Any specified subset of the sample space is called an [event](https://en.wikipedia.org/wiki/Event_(probability_theory) "Event (probability theory)").

Central subjects in probability theory include discrete and continuous [random variables](https://en.wikipedia.org/wiki/Random_variable), [[Probability Distributions]], and [stochastic processes](https://en.wikipedia.org/wiki/Stochastic_process) (which provide mathematical abstractions of [non-deterministic](https://en.wikipedia.org/wiki/Determinism) or uncertain processes or measured [quantities](https://en.wikipedia.org/wiki/Quantity) that may either be single occurrences or evolve over time in a random fashion). Although it is not possible to perfectly predict random events, much can be said about their behavior. Two major results in probability theory describing such behaviour are the [[Law of Large Numbers]] and the [[Central Limit Theorem]].

As a mathematical foundation for [statistics](https://en.wikipedia.org/wiki/Statistics), probability theory is essential to many human activities that involve quantitative analysis of data. Methods of probability theory also apply to descriptions of complex systems given only partial knowledge of their state, as in [statistical mechanics](https://en.wikipedia.org/wiki/Statistical_mechanics) or [sequential estimation](https://en.wikipedia.org/wiki/Sequential_estimation). A great discovery of twentieth-century [physics](https://en.wikipedia.org/wiki/Physics) was the probabilistic nature of physical phenomena at atomic scales, described in [quantum mechanics](https://en.wikipedia.org/wiki/Quantum_mechanics).

## History of probability

The modern mathematical theory of [probability](https://en.wikipedia.org/wiki/Probability) has its roots in attempts to analyze [games of chance](https://en.wikipedia.org/wiki/Game_of_chance) by [Gerolamo Cardano](https://en.wikipedia.org/wiki/Gerolamo_Cardano) in the sixteenth century, and by [Pierre de Fermat](https://en.wikipedia.org/wiki/Pierre_de_Fermat) and [Blaise Pascal](https://en.wikipedia.org/wiki/Blaise_Pascal) in the seventeenth century (for example the "[problem of points](https://en.wikipedia.org/wiki/Problem_of_points)"). [Christiaan Huygens](https://en.wikipedia.org/wiki/Christiaan_Huygens) published a book on the subject in 1657. In the 19th century, what is considered the [classical definition of probability](https://en.wikipedia.org/wiki/Classical_definition_of_probability) was completed by [Pierre Laplace](https://en.wikipedia.org/wiki/Pierre-Simon_Laplace).

Initially, probability theory mainly considered *discrete* events, and its methods were mainly [combinatorial](https://en.wikipedia.org/wiki/Combinatorics). Eventually, [analytical](https://en.wikipedia.org/wiki/Mathematical_analysis) considerations compelled the incorporation of *continuous* variables into the theory.

This culminated in modern probability theory, on foundations laid by [Andrey Nikolaevich Kolmogorov](https://en.wikipedia.org/wiki/Andrey_Nikolaevich_Kolmogorov). Kolmogorov combined the notion of [sample space](https://en.wikipedia.org/wiki/Sample_space), introduced by [Richard von Mises](https://en.wikipedia.org/wiki/Richard_von_Mises), and [measure theory](https://en.wikipedia.org/wiki/Measure_theory) and presented his [axiom system](https://en.wikipedia.org/wiki/Kolmogorov_axioms) for probability theory in 1933. This became the mostly undisputed [axiomatic basis](https://en.wikipedia.org/wiki/Axiom_system) for modern probability theory; but, alternatives exist, such as the adoption of finite rather than countable additivity by [Bruno de Finetti](https://en.wikipedia.org/wiki/Bruno_de_Finetti).

## Treatment

Most introductions to probability theory treat discrete probability distributions and continuous probability distributions separately. The measure theory-based treatment of probability covers the discrete, continuous, a mix of the two, and more.

### Motivation

Consider an [experiment](https://en.wikipedia.org/wiki/Experiment_(probability_theory) "Experiment (probability theory)") that can produce a number of outcomes. The set of all outcomes is called the *[sample space](https://en.wikipedia.org/wiki/Sample_space)* of the experiment. The *[power set](https://en.wikipedia.org/wiki/Power_set)* of the sample space (or equivalently, the event space) is formed by considering all different collections of possible results. For example, rolling an honest die produces one of six possible results. One collection of possible results corresponds to getting an odd number. Thus, the subset {1,3,5} is an element of the power set of the sample space of dice rolls. These collections are called *events*. In this case, {1,3,5} is the event that the die falls on some odd number. If the results that actually occur fall in a given event, that event is said to have occurred.

Probability is a [way of assigning](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)") every "event" a value between zero and one, with the requirement that the event made up of all possible results (in our example, the event {1,2,3,4,5,6}) be assigned a value of one. To qualify as a [probability distribution](https://en.wikipedia.org/wiki/Probability_distribution), the assignment of values must satisfy the requirement that if you look at a collection of mutually exclusive events (events that contain no common results, e.g., the events {1,6}, {3}, and {2,4} are all mutually exclusive), the probability that any of these events occurs is given by the sum of the probabilities of the events.

The probability that any one of the events {1,6}, {3}, or {2,4} will occur is 5/6. This is the same as saying that the probability of event {1,2,3,4,6} is 5/6. This event encompasses the possibility of any number except five being rolled. The mutually exclusive event {5} has a probability of 1/6, and the event {1,2,3,4,5,6} has a probability of 1, that is, absolute certainty.

When doing calculations using the outcomes of an experiment, it is necessary that all those [elementary events](https://en.wikipedia.org/wiki/Elementary_event) have a number assigned to them. This is done using a [random variable](https://en.wikipedia.org/wiki/Random_variable). A random variable is a function that assigns to each elementary event in the sample space a [real number](https://en.wikipedia.org/wiki/Real_number). This function is usually denoted by a capital letter. In the case of a die, the assignment of a number to certain elementary events can be done using the [identity function](https://en.wikipedia.org/wiki/Identity_function). This does not always work. For example, when [flipping a coin](https://en.wikipedia.org/wiki/Coin_flipping) the two possible outcomes are "heads" and "tails". In this example, the random variable *X* could assign to the outcome "heads" the number "0" ($X({\text{heads}})=0$) and to the outcome "tails" the number "1" ($X({\text{tails}})=1$).

### Discrete probability distributions

![[media/e97f8755596038dfb5b98d5b7d1e9eb7f9944574.png]]
The [Poisson distribution](https://en.wikipedia.org/wiki/Poisson_distribution), a discrete probability distribution

*Discrete probability theory* deals with events that occur in [countable](https://en.wikipedia.org/wiki/Countable) sample spaces.

Examples: Throwing [dice](https://en.wikipedia.org/wiki/Dice), experiments with [decks of cards](https://en.wikipedia.org/wiki/Deck_of_cards), [random walk](https://en.wikipedia.org/wiki/Random_walk), and tossing [coins](https://en.wikipedia.org/wiki/Coin).

*Classical definition*: Initially the probability of an event to occur was defined as the number of cases favorable for the event, over the number of total outcomes possible in an equiprobable sample space: see [Classical definition of probability](https://en.wikipedia.org/wiki/Classical_definition_of_probability).

For example, if the event is "occurrence of an even number when a dice is rolled", the probability is given by ${\tfrac {3}{6}}={\tfrac {1}{2}}$, since 3 faces out of the 6 have even numbers and each face has the same probability of appearing.

*Modern definition*: The modern definition starts with a [finite or countable set](https://en.wikipedia.org/wiki/Countable_set) called the [sample space](https://en.wikipedia.org/wiki/Sample_space), which relates to the set of all *possible outcomes* in classical sense, denoted by $\Omega$. It is then assumed that for each element $x\in \Omega \,$, an intrinsic "probability" value $f(x)\,$ is attached, which satisfies the following properties:

1.  $f(x)\in [0,1]{\mbox{ for all }}x\in \Omega \,;$
2.  $\sum _{x\in \Omega }f(x)=1\,.$

That is, the probability function *f*(*x*) lies between zero and one for every value of *x* in the sample space *Ω*, and the sum of *f*(*x*) over all values *x* in the sample space *Ω* is equal to 1. An *[event](https://en.wikipedia.org/wiki/Event_(probability_theory) "Event (probability theory)")* is defined as any [subset](https://en.wikipedia.org/wiki/Subset) $E\,$ of the sample space $\Omega \,$. The *probability* of the event $E\,$ is defined as

$\mathbb {P} (E)=\sum _{x\in E}f(x)\,.$

So, the probability of the entire sample space is 1, and the probability of the null event is 0.

The function $f(x)\,$ mapping a point in the sample space to the "probability" value is called a *probability mass function* abbreviated as *pmf*.

### Continuous probability distributions

![[media/08491050929a48f183caf3a31c127a71de6a345a.jpg]]
The [normal distribution](https://en.wikipedia.org/wiki/Normal_distribution), a continuous probability distribution

*Continuous probability theory* deals with events that occur in a continuous sample space.

*Classical definition*: The classical definition breaks down when confronted with the continuous case. See [Bertrand's paradox](https://en.wikipedia.org/wiki/Bertrand%27s_paradox_(probability)).

*Modern definition*: If the sample space of a random variable *X* is the set of [real numbers](https://en.wikipedia.org/wiki/Real_numbers) ($\mathbb {R}$) or a subset thereof, then a function called the *[[Cumulative Distribution Function]]* (*CDF*) $F\,$ exists, defined by $F(x)=\mathbb {P} (X\leq x)\,$. That is, *F*(*x*) returns the probability that *X* will be less than or equal to *x*.

The CDF necessarily satisfies the following properties.

1.  $F\,$ is a [monotonically non-decreasing](https://en.wikipedia.org/wiki/Monotonic_function), [right-continuous](https://en.wikipedia.org/wiki/Right-continuous) function;
2.  $\lim _{x\rightarrow -\infty }F(x)=0\,;$
3.  $\lim _{x\rightarrow \infty }F(x)=1\,.$

The random variable $X$ is said to have a continuous probability distribution if the corresponding CDF $F$ is continuous. If $F\,$ is [absolutely continuous](https://en.wikipedia.org/wiki/Absolutely_continuous), then its derivative exists almost everywhere and integrating the derivative gives us the CDF back again. In this case, the random variable *X* is said to have a *[[Probability Density Function]]* (*PDF*) or simply *density* $f(x)={\frac {dF(x)}{dx}}\,.$

For a set $E\subseteq \mathbb {R}$, the probability of the random variable *X* being in $E\,$ is

$\mathbb {P} (X\in E)=\int _{x\in E}dF(x)\,.$

In case the PDF exists, this can be written as

$\mathbb {P} (X\in E)=\int _{x\in E}f(x)\,dx\,.$

Whereas the *PDF* exists only for continuous random variables, the *CDF* exists for all random variables (including discrete random variables) that take values in $\mathbb {R} \,.$

These concepts can be generalized for [multidimensional](https://en.wikipedia.org/wiki/Dimension) cases on $\mathbb {R} ^{n}$ and other continuous sample spaces.

### Measure-theoretic probability theory

The utility of the measure-theoretic treatment of probability is that it unifies the discrete and the continuous cases, and makes the difference a question of which measure is used. Furthermore, it covers distributions that are neither discrete nor continuous nor mixtures of the two.

An example of such distributions could be a mix of discrete and continuous distributions—for example, a random variable that is 0 with probability 1/2, and takes a random value from a normal distribution with probability 1/2. It can still be studied to some extent by considering it to have a PDF of $(\delta [x]+\varphi (x))/2$, where $\delta [x]$ is the [Dirac delta function](https://en.wikipedia.org/wiki/Dirac_delta_function).

Other distributions may not even be a mix, for example, the [Cantor distribution](https://en.wikipedia.org/wiki/Cantor_distribution) has no positive probability for any single point, neither does it have a density. The modern approach to probability theory solves these problems using [measure theory](https://en.wikipedia.org/wiki/Measure_theory) to define the [probability space](https://en.wikipedia.org/wiki/Probability_space):

Given any set $\Omega \,$ (also called *sample space*) and a [[Sigma Algebra|σ-algebra]] ${\mathcal {F}}\,$ on it, a [measure](https://en.wikipedia.org/wiki/Measure_(mathematics) "Measure (mathematics)") $\mathbb {P}$ defined on ${\mathcal {F}}\,$ is called a *probability measure* if $\mathbb {P} (\Omega )=1.\,$

If ${\mathcal {F}}\,$ is the [Borel σ-algebra](https://en.wikipedia.org/wiki/Borel_algebra) on the set of real numbers, then there is a unique probability measure on ${\mathcal {F}}\,$ for any CDF, and vice versa. The measure corresponding to a CDF is said to be *induced* by the CDF. This measure coincides with the pmf for discrete variables and PDF for continuous variables, making the measure-theoretic approach free of fallacies.

The *probability* of a set $E\,$ in the σ-algebra ${\mathcal {F}}\,$ is defined as

$\mathbb {P} (E)=\int _{\omega \in E}\mu _{F}(d\omega )\,$

where the integration is with respect to the measure $\mu _{F}\,$ induced by $F\,.$

Along with providing better understanding and unification of discrete and continuous probabilities, measure-theoretic treatment also allows us to work on probabilities outside $\mathbb {R} ^{n}$, as in the theory of [stochastic processes](https://en.wikipedia.org/wiki/Stochastic_process). For example, to study [[Brownian Motion]], probability is defined on a space of functions.

When it is convenient to work with a dominating measure, the [Radon–Nikodym theorem](https://en.wikipedia.org/wiki/Radon%E2%80%93Nikodym_theorem) is used to define a density as the Radon–Nikodym derivative of the probability distribution of interest with respect to this dominating measure. Discrete densities are usually defined as this derivative with respect to a [counting measure](https://en.wikipedia.org/wiki/Counting_measure) over the set of all possible outcomes. Densities for [absolutely continuous](https://en.wikipedia.org/wiki/Absolutely_continuous) distributions are usually defined as this derivative with respect to the [Lebesgue measure](https://en.wikipedia.org/wiki/Lebesgue_measure). If a theorem can be proved in this general setting, it holds for both discrete and continuous distributions as well as others; separate proofs are not required for discrete and continuous distributions.

## Classical probability distributions

Certain random variables occur very often in probability theory because they well describe many natural or physical processes. Their distributions, therefore, have gained *special importance* in probability theory. Some fundamental *discrete distributions* are the [discrete uniform](https://en.wikipedia.org/wiki/Uniform_distribution_(discrete)), [Bernoulli](https://en.wikipedia.org/wiki/Bernoulli_distribution), [binomial](https://en.wikipedia.org/wiki/Binomial_distribution), [negative binomial](https://en.wikipedia.org/wiki/Negative_binomial_distribution), [Poisson](https://en.wikipedia.org/wiki/Poisson_distribution) and [geometric distributions](https://en.wikipedia.org/wiki/Geometric_distribution). Important *continuous distributions* include the [continuous uniform](https://en.wikipedia.org/wiki/Uniform_distribution_(continuous)), [normal](https://en.wikipedia.org/wiki/Normal_distribution), [exponential](https://en.wikipedia.org/wiki/Exponential_distribution), [gamma](https://en.wikipedia.org/wiki/Gamma_distribution) and [beta distributions](https://en.wikipedia.org/wiki/Beta_distribution).

## Convergence of random variables

In probability theory, there are several notions of convergence for [random variables](https://en.wikipedia.org/wiki/Random_variable). They are listed below in the order of strength, i.e., any subsequent notion of convergence in the list implies convergence according to all of the preceding notions.

Weak convergence  
A sequence of random variables $X_{1},X_{2},\dots ,\,$ converges *weakly* to the random variable $X\,$ if their respective CDF converges$F_{1},F_{2},\dots \,$ converges to the CDF $F\,$ of $X\,$, wherever $F\,$ is [continuous](https://en.wikipedia.org/wiki/Continuous_function). Weak convergence is also called *convergence in distribution*.

Most common shorthand notation: $\displaystyle X_{n}\,\xrightarrow {\mathcal {D}} \,X$

Convergence in probability  
The sequence of random variables $X_{1},X_{2},\dots \,$ is said to converge towards the random variable $X\,$ *in probability* if $\lim _{n\rightarrow \infty }\mathbb {P} \left(\left|X_{n}-X\right|\geq \varepsilon \right)=0$ for every ε \> 0.

Most common shorthand notation: $\displaystyle X_{n}\,\xrightarrow {\mathbb {P} } \,X$

Strong convergence  
The sequence of random variables $X_{1},X_{2},\dots \,$ is said to converge towards the random variable $X\,$ *strongly* if $\mathbb {P} (\lim _{n\rightarrow \infty }X_{n}=X)=1$. Strong convergence is also known as *almost sure convergence*.

Most common shorthand notation: $\displaystyle X_{n}\,\xrightarrow {\mathrm {a.s.} } \,X$

As the names indicate, weak convergence is weaker than strong convergence. In fact, strong convergence implies convergence in probability, and convergence in probability implies weak convergence. The reverse statements are not always true.

### Law of large numbers

Common intuition suggests that if a fair coin is tossed many times, then *roughly* half of the time it will turn up *heads*, and the other half it will turn up *tails*. Furthermore, the more often the coin is tossed, the more likely it should be that the ratio of the number of *heads* to the number of *tails* will approach unity. Modern probability theory provides a formal version of this intuitive idea, known as the *law of large numbers*. This law is remarkable because it is not assumed in the foundations of probability theory, but instead emerges from these foundations as a theorem. Since it links theoretically derived probabilities to their actual frequency of occurrence in the real world, the law of large numbers is considered as a pillar in the history of statistical theory and has had widespread influence.

The *law of large numbers* (LLN) states that the sample average

${\overline {X}}_{n}={\frac {1}{n}}{\sum _{k=1}^{n}X_{k}}$

of a [sequence](https://en.wikipedia.org/wiki/Sequence) of [independent and identically distributed random variables](https://en.wikipedia.org/wiki/Independent_and_identically_distributed_random_variables) $X_{k}$ converges towards their common [expectation](https://en.wikipedia.org/wiki/Expected_value) (expected value) $\mu$, provided that the expectation of $|X_{k}|$ is finite.

It is in the different forms of [convergence of random variables](https://en.wikipedia.org/wiki/Convergence_of_random_variables) that separates the *weak* and the *strong* law of large numbers

Weak law: $\displaystyle {\overline {X}}_{n}\,\xrightarrow {\mathbb {P} } \,\mu$ for $n\to \infty$

Strong law: $\displaystyle {\overline {X}}_{n}\,\xrightarrow {\mathrm {a.\,s.} } \,\mu$ for $n\to \infty .$

It follows from the LLN that if an event of probability *p* is observed repeatedly during independent experiments, the ratio of the observed frequency of that event to the total number of repetitions converges towards *p*.

For example, if $Y_{1},Y_{2},...\,$ are independent [Bernoulli random variables](https://en.wikipedia.org/wiki/Bernoulli_distribution) taking values 1 with probability *p* and 0 with probability 1-*p*, then ${\textrm {E}}(Y_{i})=p$ for all *i*, so that ${\bar {Y}}_{n}$ converges to *p* [almost surely](https://en.wikipedia.org/wiki/Almost_surely).

### Central limit theorem

The central limit theorem (CLT) explains the ubiquitous occurrence of the [normal distribution](https://en.wikipedia.org/wiki/Normal_distribution) in nature, and this theorem, according to David Williams, "is one of the great results of mathematics."

The theorem states that the [average](https://en.wikipedia.org/wiki/Average) of many independent and identically distributed random variables with finite variance tends towards a normal distribution *irrespective* of the distribution followed by the original random variables. Formally, let $X_{1},X_{2},\dots \,$ be independent random variables with [mean](https://en.wikipedia.org/wiki/Mean) $\mu$ and [variance](https://en.wikipedia.org/wiki/Variance) $\sigma ^{2}>0.\,$ Then the sequence of random variables

$Z_{n}={\frac {\sum _{i=1}^{n}(X_{i}-\mu )}{\sigma {\sqrt {n}}}}\,$

converges in distribution to a [standard normal](https://en.wikipedia.org/wiki/Standard_normal) random variable.

For some classes of random variables, the classic central limit theorem works rather fast, as illustrated in the [Berry–Esseen theorem](https://en.wikipedia.org/wiki/Berry%E2%80%93Esseen_theorem). For example, the distributions with finite first, second, and third moment from the [[Exponential Family]]; on the other hand, for some random variables of the [heavy tail](https://en.wikipedia.org/wiki/Heavy_tail) and [fat tail](https://en.wikipedia.org/wiki/Fat_tail) variety, it works very slowly or may not work at all: in such cases one may use the [Generalized Central Limit Theorem](https://en.wikipedia.org/wiki/Stable_distribution#A_generalized_central_limit_theorem) (GCLT).

## See also

- ![[media/1a9c6ad1ccebbc090fc7cd1c94d2142489246997.png]][Mathematics portal](https://en.wikipedia.org/wiki/Portal:Mathematics)

- [Mathematical Statistics](https://en.wikipedia.org/wiki/Mathematical_Statistics) – Branch of statisticsPages displaying short descriptions of redirect targets
- [Expected value](https://en.wikipedia.org/wiki/Expected_value) – Average value of a random variable
- [Variance](https://en.wikipedia.org/wiki/Variance) – Statistical measure of how far values spread from their average
- [Fuzzy logic](https://en.wikipedia.org/wiki/Fuzzy_logic) – System for reasoning about vagueness
- [Fuzzy measure theory](https://en.wikipedia.org/wiki/Fuzzy_measure_theory)
- [Glossary of probability and statistics](https://en.wikipedia.org/wiki/Glossary_of_probability_and_statistics)
- [Likelihood function](https://en.wikipedia.org/wiki/Likelihood_function) – Function related to statistics and probability theory
- [Notation in probability](https://en.wikipedia.org/wiki/Notation_in_probability)
- [Predictive modelling](https://en.wikipedia.org/wiki/Predictive_modelling) – Form of modelling that uses statistics to predict outcomes
- [Probabilistic logic](https://en.wikipedia.org/wiki/Probabilistic_logic) – Applications of logic under uncertainty
- [Probabilistic proofs of non-probabilistic theorems](https://en.wikipedia.org/wiki/Probabilistic_proofs_of_non-probabilistic_theorems)
- [Probability distribution](https://en.wikipedia.org/wiki/Probability_distribution) – Mathematical function for the probability a given outcome occurs in an experiment
- [[Probability Axioms]] – Foundations of probability theory
- [Probability interpretations](https://en.wikipedia.org/wiki/Probability_interpretations) – Philosophical interpretation of the axioms of probability
- [Probability space](https://en.wikipedia.org/wiki/Probability_space) – Mathematical concept
- [Statistical independence](https://en.wikipedia.org/wiki/Statistical_independence) – When the occurrence of one event does not affect the likelihood of anotherPages displaying short descriptions of redirect targets
- [Statistical physics](https://en.wikipedia.org/wiki/Statistical_physics) – Physics of many interacting particlesPages displaying short descriptions of redirect targets
- [Subjective logic](https://en.wikipedia.org/wiki/Subjective_logic) – Type of probabilistic logic
- [Pairwise independence§Probability of the union of pairwise independent events](https://en.wikipedia.org/wiki/Pairwise_independence#Probability_of_the_union_of_pairwise_independent_events) – Set of random variables of which any two are independent

### Lists

- [Catalog of articles in probability theory](https://en.wikipedia.org/wiki/Catalog_of_articles_in_probability_theory)
- [List of probability topics](https://en.wikipedia.org/wiki/List_of_probability_topics)
- [List of publications in statistics](https://en.wikipedia.org/wiki/List_of_publications_in_statistics)
- [List of statistical topics](https://en.wikipedia.org/wiki/List_of_statistical_topics)

## References

### Citations

1.  [Inferring From Data](http://home.ubalt.edu/ntsbarsh/stat-data/Topics.htm)
2.  ["Quantum Logic and Probability Theory"](https://plato.stanford.edu/entries/qt-quantlog/). *The Stanford Encyclopedia of Philosophy*. 10 August 2021.
3.  LIGHTNER, JAMES E. (1991). ["A Brief Look at the History of Probability and Statistics"](https://www.jstor.org/stable/27967334). *The Mathematics Teacher*. **84** (8): 623–630. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.5951/MT.84.8.0623](https://doi.org/10.5951%2FMT.84.8.0623). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0025-5769](https://search.worldcat.org/issn/0025-5769). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [27967334](https://www.jstor.org/stable/27967334).
4.  Grinstead, Charles Miller; James Laurie Snell. "Introduction". *Introduction to Probability*. pp. vii.
5.  Daston, Lorraine J. (1980). ["Probabilistic Expectation and Rationality in Classical Probability Theory"](https://dx.doi.org/10.1016/0315-0860%2880%2990025-7). *Historia Mathematica*. **7** (3): 234–260. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/0315-0860(80)90025-7](https://doi.org/10.1016%2F0315-0860%2880%2990025-7).
6.  [""The origins and legacy of Kolmogorov's Grundbegriffe", by Glenn Shafer and Vladimir Vovk"](http://www.probabilityandfinance.com/articles/04.pdf) (PDF). Retrieved 2012-02-12.
7.  Ross, Sheldon (2010). [A First Course in Probability](https://books.google.com/books?id=Bc1FAQAAIAAJ&pg=PA26) (8th ed.). Pearson Prentice Hall. pp. 26–27. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-13-603313-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-13-603313-4). Retrieved 2016-02-28.
8.  Bain, Lee J.; Engelhardt, Max (1992). *Introduction to Probability and Mathematical Statistics* (2nd ed.). [Belmont, California](https://en.wikipedia.org/wiki/Belmont,_California): Brooks/Cole. p. 53. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-534-38020-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-534-38020-5).
9.  ["Leithner & Co Pty Ltd - Value Investing, Risk and Risk Management - Part I"](https://web.archive.org/web/20140126113323/http://www.leithner.com.au/circulars/circular17.htm). Leithner.com.au. 2000-09-15. Archived from [the original](http://www.leithner.com.au/circulars/circular17.htm) on 2014-01-26. Retrieved 2012-02-12.
10. Dekking, Michel (2005). "Chapter 13: The law of large numbers". [A modern introduction to probability and statistics : understanding why and how](http://archive.org/details/modernintroducti00fmde). Library Genesis. London : Springer. pp. 180–194. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-85233-896-1](https://en.wikipedia.org/wiki/Special:BookSources/978-1-85233-896-1).`{{`[`cite book`](https://en.wikipedia.org/wiki/Template:Cite_book)`}}`: CS1 maint: publisher location ([link](https://en.wikipedia.org/wiki/Category:CS1_maint:_publisher_location))
11. [David Williams](https://en.wikipedia.org/wiki/David_Williams_(mathematician) "David Williams (mathematician)"), "Probability with martingales", Cambridge 1991/2008

### Sources

- [Pierre Simon de Laplace](https://en.wikipedia.org/wiki/Pierre_Simon_de_Laplace) (1812). *Analytical Theory of Probability*.

The first major treatise blending calculus with probability theory, originally in French: *Théorie Analytique des Probabilités*.

- [A. Kolmogoroff](https://en.wikipedia.org/wiki/Andrey_Kolmogorov) (1933). *Grundbegriffe der Wahrscheinlichkeitsrechnung*. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-3-642-49888-6](https://doi.org/10.1007%2F978-3-642-49888-6). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-642-49888-6](https://en.wikipedia.org/wiki/Special:BookSources/978-3-642-49888-6). `{{`[`cite book`](https://en.wikipedia.org/wiki/Template:Cite_book)`}}`: ISBN / Date incompatibility ([help](https://en.wikipedia.org/wiki/Help:CS1_errors#invalid_isbn_date))

An English translation by Nathan Morrison appeared under the title *Foundations of the Theory of Probability* (Chelsea, New York) in 1950, with a second edition in 1956.

- [Patrick Billingsley](https://en.wikipedia.org/wiki/Patrick_Billingsley) (1979). *Probability and Measure*. New York, Toronto, London: John Wiley and Sons.
- [Olav Kallenberg](https://en.wikipedia.org/wiki/Olav_Kallenberg); *Foundations of Modern Probability,* 2nd ed. Springer Series in Statistics. (2002). 650 pp. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-95313-2](https://en.wikipedia.org/wiki/Special:BookSources/0-387-95313-2)
- [Henk Tijms](https://en.wikipedia.org/wiki/Henk_Tijms) (2004). *Understanding Probability*. Cambridge Univ. Press.

A lively introduction to probability theory for the beginner.

- Olav Kallenberg; *Probabilistic Symmetries and Invariance Principles*. Springer -Verlag, New York (2005). 510 pp. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-25115-4](https://en.wikipedia.org/wiki/Special:BookSources/0-387-25115-4)
- [Durrett, Rick](https://en.wikipedia.org/wiki/Rick_Durrett) (2019). [Probability: Theory and Examples, 5th edition](https://www.cambridge.org/de/academic/subjects/statistics-probability/probability-theory-and-stochastic-processes/probability-theory-and-examples-5th-edition?format=HB&isbn=9781108473682). [UK](https://en.wikipedia.org/wiki/UK): [Cambridge University Press](https://en.wikipedia.org/wiki/Cambridge_University_Press). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9781108473682](https://en.wikipedia.org/wiki/Special:BookSources/9781108473682).
- Gut, Allan (2005). *Probability: A Graduate Course*. Springer-Verlag. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-22833-0](https://en.wikipedia.org/wiki/Special:BookSources/0-387-22833-0).
