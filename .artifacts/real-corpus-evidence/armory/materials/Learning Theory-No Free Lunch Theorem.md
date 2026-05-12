[[learning-theory.base]]

> Source: [[No Free Lunch Theorem]]
> License: Wikipedia content is available under CC BY-SA 4.0.

In 2005, Wolpert and Macready themselves indicated that the first theorem in their paper "state\[s\] that any two [optimization](https://en.wikipedia.org/wiki/Optimization_(mathematics)) algorithms are equivalent when their performance is averaged across all possible problems".

The "no free lunch" (NFL) theorem is an easily stated and easily understood consequence of theorems Wolpert and Macready actually prove. It is objectively weaker than the proven theorems, and thus does not encapsulate them. Various investigators have extended the work of Wolpert and Macready substantively. In terms of how the NFL theorem is used in the context of the research area, the [no free lunch in search and optimization](https://en.wikipedia.org/wiki/No_free_lunch_in_search_and_optimization) is a field that is dedicated for purposes of mathematically analyzing data for statistical identity, particularly search and optimization.

While some scholars argue that NFL conveys important insight, others argue that NFL is of little relevance to machine learning research.

## Example

Posit a toy universe that exists for exactly two days and each day has one state: sunny or cloudy. The universe has exactly four possible histories:

1.  (sunny, cloudy): the universe is sunny on day 1, and cloudy on day 2
2.  (sunny, sunny)
3.  (cloudy, cloudy)
4.  (cloudy, sunny)

Any prediction strategy that succeeds for history \#2, by predicting sunny on day 2 if it is sunny on day 1, will fail on history \#1, and vice versa. If all histories are equally likely, then any prediction strategy will score the same, with the same accuracy rate of 0.5.

## Origin

Wolpert and Macready give two NFL theorems that are closely related to the folkloric theorem. In their paper, they state:

> We have dubbed the associated results NFL theorems because they demonstrate that if an algorithm performs well on a certain class of problems then it necessarily pays for that with degraded performance on the set of all remaining problems.

The first theorem hypothesizes [objective functions](https://en.wikipedia.org/wiki/Objective_function) that do not change while optimization is in progress, and the second hypothesizes objective functions that may change.

**Theorem**—For any algorithms *a*<sub>1</sub> and *a*<sub>2</sub>, at iteration step *m* 

$$
\sum _{f}P(d_{m}^{y}\mid f,m,a_{1})=\sum _{f}P(d_{m}^{y}\mid f,m,a_{2}),
$$

 where $d_{m}^{y}$ denotes the ordered set of size $m$ of the cost values $y$ associated to input values $x\in X$, $f:X\rightarrow Y$ is the function being optimized and $P(d_{m}^{y}\mid f,m,a)$ is the [conditional probability](https://en.wikipedia.org/wiki/Conditional_probability) of obtaining a given sequence of cost values from algorithm $a$ run $m$ times on function $f$.

The theorem can be equivalently formulated as follows:

**Theorem**—Given a finite set $V$ and a finite set $S$ of [real numbers](https://en.wikipedia.org/wiki/Real_number), assume that $f:V\to S$ is chosen at random according to [uniform distribution](https://en.wikipedia.org/wiki/Discrete_uniform_distribution) on the set $S^{V\!}$ of all possible [functions](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)") from $V$ to $S$. For the problem of optimizing $f$ over the set $V$, then no algorithm performs better than blind search.

Here, *blind search* means that at each step of the algorithm, the element $v\in V$ is chosen at random with uniform [probability distribution](https://en.wikipedia.org/wiki/Probability_distribution) from the elements of $V$ that have not been chosen previously.

In essence, this says that when all functions *f* are equally likely, the probability of observing an arbitrary sequence of *m* values in the course of optimization does not depend upon the algorithm. In the analytic framework of Wolpert and Macready, performance is a function of the sequence of observed values (and not e.g. of wall-clock time), so it follows easily that all algorithms have identically distributed performance when objective functions are drawn uniformly at random, and also that all algorithms have identical mean performance. But identical mean performance of all algorithms does not imply Theorem 1, and thus the folkloric theorem is not equivalent to the original theorem.

Theorem 2 establishes a similar, but "more subtle", NFL result for time-varying objective functions.

## Motivation

The NFL theorems were explicitly *not* motivated by the question of what can be inferred (in the case of NFL for machine learning) or found (in the case of NFL for search) when the "environment is uniform random". Rather uniform randomness was used as a tool, to compare the number of environments for which algorithm A outperforms algorithm B to the number of environments for which B outperforms A. NFL tells us that (appropriately weighted)<sup>\[*[clarification needed](https://en.wikipedia.org/wiki/Wikipedia:Please_clarify)*\]</sup> there are just as many environments in both of those sets.

This is true for many definitions of what precisely an "environment" is. In particular, there are just as many prior distributions (appropriately weighted) in which learning algorithm A beats B (on average) as vice versa.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup> This statement about *sets of priors* is what is most important about NFL, not the fact that any two algorithms perform equally for the single, specific prior distribution that assigns equal probability to all environments.

While the NFL is important to understand the fundamental limitation for a set of problems, it does not state anything about each particular instance of a problem that can arise in practice. That is, the NFL states what is contained in its mathematical statements and it is nothing more than that. For example, it applies to the situations where the algorithm is fixed a priori and a worst-case problem for the fixed algorithm is chosen a posteriori. Therefore, if we have a "good" problem in practice or if we can choose a "good" learning algorithm for a given particular problem instance, then the NFL does not mention any limitation about this particular problem instance. Though the NFL might seem contradictory to results from other papers suggesting generalization of learning algorithms or search heuristics, it is important to understand the difference between the exact [mathematical logic](https://en.wikipedia.org/wiki/Mathematical_logic) of the NFL and its intuitive interpretation.

## Implications

To illustrate one of the counter-intuitive implications of NFL, suppose we fix two [supervised learning](https://en.wikipedia.org/wiki/Supervised_learning) algorithms, C and D. We then sample a target function f to produce a set of input-output pairs, *d*. The question is how should we choose whether to train C or D on *d*, in order to make predictions for what output would be associated with a point lying outside of *d.*

It is common in almost all of science and statistics to answer this question – to choose between C and D – by running cross-validation on *d* with those two algorithms. In other words, to decide whether to generalize from *d* with either C or D*,* we see which of them has better out-of-sample performance when tested within *d*.

Since C and D are fixed, this use of cross-validation to choose between them is itself an algorithm, i.e., a way of generalizing from an arbitrary dataset. Call this algorithm A. (Arguably, A is a simplified model of the scientific method itself.)

We could also use *anti*-cross-validation to make our choice. In other words, we could choose between C and D based on which has *worse* out-of-sample performance within *d*. Again, since C and D are fixed, this use of anti-cross-validation is itself an algorithm. Call that algorithm B.

NFL tells us (loosely speaking) that B must beat A on just as many target functions (and associated datasets *d*) as A beats B. In this very specific sense, the scientific method will lose to the "anti" scientific method just as readily as it wins.

NFL only applies if the target function is chosen from a uniform distribution of all possible functions. If this is not the case, and certain target functions are more likely to be chosen than others, then A may perform better than B overall. The contribution of NFL is that it tells us that choosing an appropriate algorithm requires making assumptions about the kinds of target functions the algorithm is being used for. With no assumptions, no "meta-algorithm", such as the scientific method, performs better than random choice.

While some scholars argue that NFL conveys important insight, others argue that NFL is of little relevance to machine learning research. If [Occam's razor](https://en.wikipedia.org/wiki/Occam%27s_razor) is correct, for example if sequences of lower [Kolmogorov complexity](https://en.wikipedia.org/wiki/Kolmogorov_complexity) are more probable than sequences of higher complexity, then (as is observed in real life) some algorithms, such as cross-validation, perform better on average on practical problems (when compared with random choice or with anti-cross-validation).

However, there are major formal challenges in using arguments based on Kolmogorov complexity to establish properties of the real world, since it is uncomputable, and undefined up to an arbitrary additive constant. Partly in recognition of these challenges, it has recently been argued that there are ways to circumvent the no free lunch theorems without invoking Turing machines, by using "meta-induction". Moreover, the Kolmogorov complexity of machine learning models can be upper bounded through compressions of their data labeling, and it is possible to produce non-vacuous cross-domain generalization bounds via Kolmogorov complexity.

## Notes

1.  ^      Wolpert, D. H.; Macready, W. G. (1997). "No Free Lunch Theorems for Optimization". *IEEE Transactions on Evolutionary Computation*. **1**: 67–82. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.138.6606](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.138.6606). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/4235.585893](https://doi.org/10.1109%2F4235.585893). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [5553697](https://api.semanticscholar.org/CorpusID:5553697).
2.  Wolpert, David (1996), "[The Lack of A Priori Distinctions between Learning Algorithms](https://www.researchgate.net/publication/2755783_The_Lack_of_A_Priori_Distinctions_Between_Learning_Algorithms)", *Neural Computation*, pp. 1341–1390.
3.  Wolpert, D.H.; Macready, W.G. (December 2005). "Coevolutionary Free Lunches". *IEEE Transactions on Evolutionary Computation*. **9** (6): 721–735. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2005ITEC....9..721W](https://ui.adsabs.harvard.edu/abs/2005ITEC....9..721W). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/TEVC.2005.856205](https://doi.org/10.1109%2FTEVC.2005.856205). [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[2060/20050082129](https://hdl.handle.net/2060%2F20050082129). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1089-778X](https://search.worldcat.org/issn/1089-778X).
4.  Wolpert, D. H.; Macready, W. G. (1995). "No Free Lunch Theorems for Search". *Technical Report SFI-TR-95-02-010*. Santa Fe Institute. [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [12890367](https://api.semanticscholar.org/CorpusID:12890367).
5.  ^   Whitley, Darrell; Watson, Jean Paul (2005). Burke, Edmund K.; Kendall, Graham (eds.). [Complexity Theory and the No Free Lunch Theorem](http://link.springer.com/10.1007/0-387-28356-0_11). Boston, MA: Springer US. pp. 317–339. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/0-387-28356-0_11](https://doi.org/10.1007%2F0-387-28356-0_11). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-23460-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-23460-1).
6.  ^   Giraud-Carrier, Christophe, and Foster Provost. "[Toward a justification of meta-learning: Is the no free lunch theorem a show-stopper](https://www.researchgate.net/profile/Christophe_Giraud-Carrier/publication/228671734_Toward_a_justification_of_meta-learning_Is_the_no_free_lunch_theorem_a_show-stopper/links/0fcfd510c5d5b83ec8000000/Toward-a-justification-of-meta-learning-Is-the-no-free-lunch-theorem-a-show-stopper.pdf)." In Proceedings of the ICML-2005 Workshop on Meta-learning, pp. 12–19. 2005.
7.  ^    Goldblum, M., Finzi, M., Keefer, R., and Wilson, AG. "[The No Free Lunch Theorem, Kolmogorov Complexity, and the Role of Inductive Biases in Machine Learning](https://arxiv.org/abs/2304.05366)." *arXiv preprint arXiv:2304.05366* (2023).
8.  Forster, Malcolm R. (1999). "How do Simple Rules 'Fit to Reality' in a Complex World?". *Minds and Machines*. **9** (4): 543–564. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1023/A:1008304819398](https://doi.org/10.1023%2FA%3A1008304819398). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [8802657](https://api.semanticscholar.org/CorpusID:8802657).
9.  Kawaguchi, K., Kaelbling, L.P, and Bengio, Y.(2017) "Generalization in deep learning", [https://arxiv.org/abs/1710.05468](https://arxiv.org/abs/1710.05468)
10. Wolpert, David H. (December 2013). ["Ubiquity symposium: Evolutionary computation and the processes of life: what the no free lunch theorems really mean: how to improve search algorithms"](https://dl.acm.org/doi/10.1145/2555235.2555237). *Ubiquity*. **2013** (December): 1–15. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1145/2555235.2555237](https://doi.org/10.1145%2F2555235.2555237). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1530-2180](https://search.worldcat.org/issn/1530-2180).
11. Lattimore, Tor, and Marcus Hutter. "[No free lunch versus Occam’s razor in supervised learning](https://arxiv.org/abs/1111.3846)." In Algorithmic Probability and Friends. Bayesian Prediction and Artificial Intelligence, pp. 223–235. Springer, Berlin, Heidelberg, 2013.
12. Schurz, G. (2019). *Hume's Problem Solved: The Optimality of Meta-Induction*. MIT Press.
13. Wolpert, D. H. (2023). "The Implications of the No-Free-Lunch Theorems for Meta-induction". *Journal for General Philosophy of Science*. **54** (3): 421–432. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2103.11956](https://arxiv.org/abs/2103.11956). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s10838-022-09609-2](https://doi.org/10.1007%2Fs10838-022-09609-2).

## External links

- [No Free Lunch Theorems](http://www.no-free-lunch.org/)
- [Graphics illustrating the theorem](https://commons.wikimedia.org/wiki/File:No_free_lunch_theorem.svg)
