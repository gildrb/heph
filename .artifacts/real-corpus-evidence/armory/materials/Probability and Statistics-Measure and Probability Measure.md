[[probability-statistics.base]]

> Source: [Probability measure](https://en.wikipedia.org/wiki/Probability_measure)
> License: Wikipedia content is available under CC BY-SA 4.0.

In [mathematics](https://en.wikipedia.org/wiki/Mathematics), a **probability measure** is a [real-valued function](https://en.wikipedia.org/wiki/Real-valued_function) defined on a set of events in a [σ-algebra](https://en.wikipedia.org/wiki/%CE%A3-algebra) that satisfies [measure](https://en.wikipedia.org/wiki/Measure_(mathematics) "Measure (mathematics)") properties such as *countable additivity*. The difference between a probability measure and the more general notion of measure (which includes concepts like [area](https://en.wikipedia.org/wiki/Area) or [volume](https://en.wikipedia.org/wiki/Volume)) is that a probability measure must assign value 1 to the entire space.

Intuitively, the additivity property says that the probability assigned to the union of two disjoint (mutually exclusive) events by the measure should be the sum of the probabilities of the events; for example, the value assigned to the outcome "1 or 2" in a throw of a die should be the sum of the values assigned to the outcomes "1" and "2".

Probability measures have applications in diverse fields, from physics to finance and biology.

## Definition

![[media/e5427ef722d99092fa3e30c0fe8d07d21294e315.png]]
A <em>probability measure</em> mapping the σ-algebra for $2^{3}$ events to the [unit interval](https://en.wikipedia.org/wiki/Unit_interval).

The requirements for a [set function](https://en.wikipedia.org/wiki/Set_function) $\mu$ to be a probability measure on a [σ-algebra](https://en.wikipedia.org/wiki/%CE%A3-algebra) are that:

- $\mu$ must take values in the [unit interval](https://en.wikipedia.org/wiki/Unit_interval) $[0,1],$ including $0$ on the empty set and $1$ on the entire space.
- $\mu$ must satisfy the *[countable additivity](https://en.wikipedia.org/wiki/Sigma-additive_set_function)* property that for all [countable](https://en.wikipedia.org/wiki/Countable) collections $E_{1},E_{2},\ldots$ of pairwise [disjoint sets](https://en.wikipedia.org/wiki/Disjoint_sets): 

$$
\mu \left(\bigcup _{i\in \mathbb {N} }E_{i}\right)=\sum _{i\in \mathbb {N} }\mu (E_{i}).
$$

For example, given three elements 1, 2 and 3 with probabilities $1/4,1/4$ and $1/2,$ the value assigned to $\{1,3\}$ is $1/4+1/2=3/4,$ as in the diagram on the right.

The [conditional probability](https://en.wikipedia.org/wiki/Conditional_probability) based on the intersection of events defined as: 

$$
\mu (B\mid A)={\frac {\mu (A\cap B)}{\mu (A)}}.
$$

 satisfies the probability function requirements so long as $\mu (A)$ is not zero.

Probability measures are distinct from the more general notion of [fuzzy measures](https://en.wikipedia.org/wiki/Fuzzy_measure_theory) in which there is no requirement that the fuzzy values sum up to $1,$ and the additive property is replaced by an order relation based on [set inclusion](https://en.wikipedia.org/wiki/Set_inclusion).

## Example applications

In many cases, [statistical physics](https://en.wikipedia.org/wiki/Statistical_physics) uses *probability measures*, but not all [measures](https://en.wikipedia.org/wiki/Measure_theory) it uses are probability measures.

*Market measures* which assign probabilities to [financial market](https://en.wikipedia.org/wiki/Financial_market) spaces based on observed market movements are examples of probability measures which are of interest in [mathematical finance](https://en.wikipedia.org/wiki/Mathematical_finance); for example, in the pricing of [financial derivatives](https://en.wikipedia.org/wiki/Financial_derivative). For instance, a [risk-neutral measure](https://en.wikipedia.org/wiki/Risk-neutral_measure) is a probability measure which assumes that the current value of assets is the [expected value](https://en.wikipedia.org/wiki/Expected_value) of the future payoff taken with respect to that same risk neutral measure (i.e. calculated using the corresponding risk neutral density function), and [discounted](https://en.wikipedia.org/wiki/Discounted) at the [risk-free rate](https://en.wikipedia.org/wiki/Risk-free_rate). If there is a unique probability measure that must be used to price assets in a market, then the market is called a [complete market](https://en.wikipedia.org/wiki/Complete_market).

Not all measures that intuitively represent chance or likelihood are probability measures. For instance, although the fundamental concept of a system in [statistical mechanics](https://en.wikipedia.org/wiki/Statistical_mechanics) is a measure space, such measures are not always probability measures. In statistical physics, for sentences of the form "the probability of a system S assuming state A is p," the geometry of the system does not always lead to the definition of a probability measure [under congruence](https://en.wikipedia.org/wiki/Congruence_relation), although it may do so in the case of systems with just one degree of freedom.

Probability measures are also used in [mathematical biology](https://en.wikipedia.org/wiki/Mathematical_biology). For instance, in comparative [sequence analysis](https://en.wikipedia.org/wiki/Sequence_analysis) a probability measure may be defined for the likelihood that a variant may be permissible for an [amino acid](https://en.wikipedia.org/wiki/Amino_acid) in a sequence.

## See also

- [Borel measure](https://en.wikipedia.org/wiki/Borel_measure) – Measure defined on all open sets of a topological space
- [Fuzzy measure](https://en.wikipedia.org/wiki/Fuzzy_measure)
- [Haar measure](https://en.wikipedia.org/wiki/Haar_measure) – Left-invariant (or right-invariant) measure on locally compact topological group
- [Lebesgue measure](https://en.wikipedia.org/wiki/Lebesgue_measure) – Concept of area in any dimension
- [Martingale measure](https://en.wikipedia.org/wiki/Martingale_measure) – Probability measurePages displaying short descriptions of redirect targets
- [Set function](https://en.wikipedia.org/wiki/Set_function) – Function from sets to numbers
- [Probability distribution](https://en.wikipedia.org/wiki/Probability_distribution)

## References

1.  *An introduction to measure-theoretic probability* by George G. Roussas 2004 [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-12-599022-7](https://en.wikipedia.org/wiki/Special:BookSources/0-12-599022-7) [page 47](https://books.google.com/books?id=J8ZRgCNS-wcC&pg=PA47)
2.  Dekking, Frederik Michel; Kraaikamp, Cornelis; Lopuhaä, Hendrik Paul; Meester, Ludolf Erwin (2005). ["A Modern Introduction to Probability and Statistics"](https://link.springer.com/book/10.1007/1-84628-168-7). *Springer Texts in Statistics*. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/1-84628-168-7](https://doi.org/10.1007%2F1-84628-168-7). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-85233-896-1](https://en.wikipedia.org/wiki/Special:BookSources/978-1-85233-896-1). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1431-875X](https://search.worldcat.org/issn/1431-875X).
3.  *Probability, Random Processes, and Ergodic Properties* by Robert M. Gray 2009 [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [1-4419-1089-1](https://en.wikipedia.org/wiki/Special:BookSources/1-4419-1089-1) [page 163](https://books.google.com/books?id=x-VbL8mZWl8C&pg=PA163)
4.  ^   *A course in mathematics for students of physics, Volume 2* by Paul Bamberg, Shlomo Sternberg 1991 [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-40650-1](https://en.wikipedia.org/wiki/Special:BookSources/0-521-40650-1) [page 802](https://books.google.com/books?id=eSmC4qQ0SCAC&pg=PA802)
5.  ^   *The concept of probability in statistical physics* by Yair M. Guttmann 1999 [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-62128-3](https://en.wikipedia.org/wiki/Special:BookSources/0-521-62128-3) [page 149](https://books.google.com/books?id=Q1AUhivGmyUC&pg=PA149)
6.  *Quantitative methods in derivatives pricing* by Domingo Tavella 2002 [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-39447-5](https://en.wikipedia.org/wiki/Special:BookSources/0-471-39447-5) [page 11](https://books.google.com/books?id=dHIMulKy8dYC&pg=PA11)
7.  *Irreversible decisions under uncertainty* by Svetlana I. Boyarchenko, Serge Levendorskiĭ 2007 [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [3-540-73745-6](https://en.wikipedia.org/wiki/Special:BookSources/3-540-73745-6) [page 11](https://books.google.com/books?id=lpsrP5mQG_QC&pg=PA11)
8.  *Mathematical Methods in Biology* by J. David Logan, William R. Wolesensky 2009 [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-470-52587-8](https://en.wikipedia.org/wiki/Special:BookSources/0-470-52587-8) [page 195](https://books.google.com/books?id=6GGyquH8kLcC&pg=PA195)
9.  *Discovering biomolecular mechanisms with computational biology* by Frank Eisenhaber 2006 [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-34527-2](https://en.wikipedia.org/wiki/Special:BookSources/0-387-34527-2) [page 127](https://books.google.com/books?id=Pygg7cIZTwIC&pg=PA127)

## Further reading

- [Billingsley, Patrick](https://en.wikipedia.org/wiki/Patrick_Billingsley) (1995). *Probability and Measure*. John Wiley. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-00710-2](https://en.wikipedia.org/wiki/Special:BookSources/0-471-00710-2).
- Ash, Robert B.; Doléans-Dade, Catherine A. (1999). *Probability & Measure Theory*. Academic Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-12-065202-1](https://en.wikipedia.org/wiki/Special:BookSources/0-12-065202-1).
- [Distinguishing probability measure, function and distribution](https://math.stackexchange.com/q/1073744/29780), Math Stack Exchange

## External links

- ![[media/62933b50408636b28d12e90be87b5b81874d2f90.png]] Media related to [Probability measure](https://commons.wikimedia.org/wiki/Category:Probability_measure) at Wikimedia Commons
