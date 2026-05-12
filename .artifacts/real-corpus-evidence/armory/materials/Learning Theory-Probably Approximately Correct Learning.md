[[learning-theory.base]]

> Source: [[Probably Approximately Correct Learning]]
> License: Wikipedia content is available under CC BY-SA 4.0.

In [computational learning theory](https://en.wikipedia.org/wiki/Computational_learning_theory), **probably approximately correct** (**PAC**) **learning** is a framework for mathematical analysis of [machine learning](https://en.wikipedia.org/wiki/Machine_learning). It was proposed in 1984 by [Leslie Valiant](https://en.wikipedia.org/wiki/Leslie_Valiant).

In this framework, the learner receives samples and must select a generalization function (called the *hypothesis*) from a certain class of possible functions. The goal is that, with high probability (the "probably" part), the selected function will have low [[Generalization Error]] (the "approximately correct" part). The learner must be able to learn the concept given any arbitrary approximation ratio, probability of success, or [distribution of the samples](https://en.wikipedia.org/wiki/Empirical_distribution_function).

The model was later extended to treat noise (misclassified samples).

An important innovation of the PAC framework is the introduction of [computational complexity theory](https://en.wikipedia.org/wiki/Computational_complexity_theory) concepts to machine learning. In particular, the learner is expected to find efficient functions (time and space requirements bounded to a [polynomial](https://en.wikipedia.org/wiki/Polynomial) of the example size), and the learner itself must implement an efficient procedure (requiring an example count bounded to a polynomial of the concept size, modified by the approximation and [likelihood](https://en.wikipedia.org/wiki/Likelihood) bounds).

## Definitions and terminology

In order to give the definition for something that is PAC-learnable, we first have to introduce some terminology.

For the following definitions, two examples will be used. The first is the problem of [character recognition](https://en.wikipedia.org/wiki/Character_recognition) given an array of $n$ bits encoding a binary-valued image. The other example is the problem of finding an interval that will correctly classify points within the interval as positive and the points outside of the range as negative.

Let $X$ be a set called the *instance space* or the encoding of all the samples. In the character recognition problem, the instance space is $X=\{0,1\}^{n}$. In the interval problem the instance space, $X$, is the set of all bounded intervals in $\mathbb {R}$, where $\mathbb {R}$ denotes the set of all [real numbers](https://en.wikipedia.org/wiki/Real_numbers).

A *concept* is a subset $c\subset X$. One concept is the set of all patterns of bits in $X=\{0,1\}^{n}$ that encode a picture of the letter "P". An example concept from the second example is the set of open intervals, $\{(a,b)\mid 0\leq a\leq \pi /2,\pi \leq b\leq {\sqrt {13}}\}$, each of which contains only the positive points. A *[concept class](https://en.wikipedia.org/wiki/Concept_class)* $C$ is a collection of concepts over $X$. This could be the set of all subsets of the array of bits that are [skeletonized](https://en.wikipedia.org/wiki/Morphological_skeleton) [4-connected](https://en.wikipedia.org/wiki/Pixel_connectivity#4-connected) (width of the font is 1).

Let $\operatorname {EX} (c,D)$ be a procedure that draws an example, $x$, using a probability distribution $D$ and gives the correct label $c(x)$, that is 1 if $x\in c$ and 0 otherwise.

Now, given $0<\epsilon ,\delta <1$, assume there is an algorithm $A$ and a polynomial $p$ in $1/\epsilon ,1/\delta$ (and other relevant parameters of the class $C$) such that, given a sample of size $p$ drawn according to $\operatorname {EX} (c,D)$, then, with probability of at least $1-\delta$, $A$ outputs a hypothesis $h\in C$ that has an average error less than or equal to $\epsilon$ on $X$ with the same distribution $D$. Further if the above statement for algorithm $A$ is true for every concept $c\in C$ and for every distribution $D$ over $X$, and for all $0<\epsilon ,\delta <1$ then $C$ is (efficiently) **PAC learnable** (or *distribution-free PAC learnable*). We can also say that $A$ is a **PAC learning algorithm** for $C$.

## Equivalence

Under some regularity conditions these conditions are equivalent: 

1.  The concept class *C* is PAC learnable.
2.  The [[VC Dimension]] of *C* is finite.
3.  *C* is a uniformly [Glivenko-Cantelli class](https://en.wikipedia.org/wiki/Glivenko%E2%80%93Cantelli_theorem#Glivenko–Cantelli_class).<sup>\[*[clarification needed](https://en.wikipedia.org/wiki/Wikipedia:Please_clarify)*\]</sup>

## See also

- [Data mining](https://en.wikipedia.org/wiki/Data_mining)
- [Error tolerance (PAC learning)](https://en.wikipedia.org/wiki/Error_tolerance_(PAC_learning) "Error tolerance (PAC learning)")
- [Occam learning](https://en.wikipedia.org/wiki/Occam_learning)
- [Sample complexity](https://en.wikipedia.org/wiki/Sample_complexity)

## References

1.  L. Valiant. *[A theory of the learnable.](http://web.mit.edu/6.435/www/Valiant84.pdf)* Communications of the ACM, 27, 1984.
2.  Kearns and Vazirani, pg. 1-12,
3.  Blumer, Anselm; Ehrenfeucht, Andrzej; David, Haussler; Manfred, Warmuth (October 1989). ["Learnability and the Vapnik-Chervonenkis Dimension"](https://doi.org/10.1145%2F76359.76371). *Journal of the Association for Computing Machinery*. **36** (4): 929–965. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1145/76359.76371](https://doi.org/10.1145%2F76359.76371). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [1138467](https://api.semanticscholar.org/CorpusID:1138467).

## Further reading

- M. Kearns, U. Vazirani. *[An Introduction to Computational Learning Theory](https://books.google.com/books?id=vCA01wY6iywC).* MIT Press, 1994. A textbook.
- M. Mohri, A. Rostamizadeh, and A. Talwalkar. *Foundations of Machine Learning*. MIT Press, 2018. Chapter 2 contains a detailed treatment of PAC-learnability. [Readable through open access from the publisher.](https://mitpress.ublish.com/ebook/foundations-of-machine-learning--2-preview/7093/9)
- D. Haussler. [Overview of the Probably Approximately Correct (PAC) Learning Framework](http://www.cs.iastate.edu/~honavar/pac.pdf). An introduction to the topic.
- L. Valiant. [Probably Approximately Correct.](https://web.archive.org/web/20170228150047/http://www.probablyapproximatelycorrect.com/) Basic Books, 2013. In which Valiant argues that PAC learning describes how organisms evolve and learn.
- Littlestone, N.; Warmuth, M. K. (June 10, 1986). ["Relating Data Compression and Learnability"](https://web.archive.org/web/20170809095748/https://users.soe.ucsc.edu/~manfred/pubs/lrnk-olivier.pdf) (PDF). Archived from [the original](http://www.cse.ucsc.edu/~manfred/pubs/T1.pdf) (PDF) on 2017-08-09.
- Moran, Shay; Yehudayoff, Amir (2015). "Sample compression schemes for VC classes". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1503.06960](https://arxiv.org/abs/1503.06960) \[[cs.LG](https://arxiv.org/archive/cs.LG)\].

## External links

- [Interactive explanation of PAC learning](https://www.cs.brandeis.edu/~dylan/pac_learning/)
