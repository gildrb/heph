[[information-theory.base]]

> Source: [[Jensen-Shannon Divergence|Jensen–Shannon divergence]]
> License: Wikipedia content is available under CC BY-SA 4.0.

In [probability theory](https://en.wikipedia.org/wiki/Probability_theory) and [statistics](https://en.wikipedia.org/wiki/Statistics), the **Jensen–Shannon divergence**, named after [Johan Jensen](https://en.wikipedia.org/wiki/Johan_Jensen_(mathematician) "Johan Jensen (mathematician)") and [Claude Shannon](https://en.wikipedia.org/wiki/Claude_Shannon), is a method of measuring the similarity between two [probability distributions](https://en.wikipedia.org/wiki/Probability_distribution). It is also known as **information radius** (**IRad**) or **total divergence to the average**. It is based on the [[Kullback-Leibler Divergence|Kullback–Leibler divergence]], with some notable (and useful) differences, including that it is symmetric and it always has a finite value. The square root of the Jensen–Shannon divergence is a [metric](https://en.wikipedia.org/wiki/Metric_(mathematics)) often referred to as Jensen–Shannon distance. The similarity between the distributions is greater when the Jensen-Shannon distance is closer to zero.

## Definition

Consider the set $M_{+}^{1}(A)$ of probability distributions where $A$ is a set provided with some [[Sigma Algebra|σ-algebra]] of measurable subsets. In particular we can take $A$ to be a finite or [countable set](https://en.wikipedia.org/wiki/Countable_set) with all subsets being measurable.

The Jensen–Shannon divergence (JSD) is a symmetrized and smoothed version of the [[Kullback-Leibler Divergence|Kullback–Leibler divergence]] $D(P\parallel Q)$. It is defined by

${\rm {JSD}}(P\parallel Q)={\frac {1}{2}}D(P\parallel M)+{\frac {1}{2}}D(Q\parallel M),$

where $M={\frac {1}{2}}(P+Q)$ is a [mixture distribution](https://en.wikipedia.org/wiki/Mixture_distribution) of $P$ and $Q$.

The geometric Jensen–Shannon divergence (or G-Jensen–Shannon divergence) yields a closed-form formula for divergence between two Gaussian distributions by taking the geometric mean.

A more general definition, allowing for the comparison of more than two probability distributions, is:

${\begin{aligned}{\rm {JSD}}_{\pi _{1},\ldots ,\pi _{n}}(P_{1},P_{2},\ldots ,P_{n})&=\sum _{i}\pi _{i}D(P_{i}\parallel M)\\&=H\left(M\right)-\sum _{i=1}^{n}\pi _{i}H(P_{i})\end{aligned}}$

where

${\begin{aligned}M&:=\sum _{i=1}^{n}\pi _{i}P_{i}\end{aligned}}$

and $\pi _{1},\ldots ,\pi _{n}$ are weights that are selected for the probability distributions $P_{1},P_{2},\ldots ,P_{n}$, and $H(P)$ is the [Shannon entropy](https://en.wikipedia.org/wiki/Shannon_entropy) for distribution $P$. For the two-distribution case described above,

$P_{1}=P,P_{2}=Q,\pi _{1}=\pi _{2}={\frac {1}{2}}.\$

Hence, for those distributions $P,Q$

$JSD=H(M)-{\frac {1}{2}}{\bigg (}H(P)+H(Q){\bigg )}$

## Bounds

The Jensen–Shannon divergence is bounded by 1 for two discrete probability distributions, given that one uses the base 2 logarithm:

$0\leq {\rm {JSD}}(P\parallel Q)\leq 1$.

With this normalization, it is a lower bound on the [total variation distance](https://en.wikipedia.org/wiki/Total_variation_distance) between P and Q:

${\rm {JSD}}(P\parallel Q)\leq {\frac {1}{2}}\|P-Q\|_{1}={\frac {1}{2}}\sum _{\omega \in \Omega }|P(\omega )-Q(\omega )|$.

With base-e logarithm, which is commonly used in statistical thermodynamics, the upper bound is $\ln(2)$. In general, the bound in base b is $\log _{b}(2)$:

$0\leq {\rm {JSD}}(P\parallel Q)\leq \log _{b}(2)$.

A more general bound, the Jensen–Shannon divergence is bounded by $\log _{b}(n)$ for more than two probability distributions:

$0\leq {\rm {JSD}}_{\pi _{1},\ldots ,\pi _{n}}(P_{1},P_{2},\ldots ,P_{n})\leq \log _{b}(n)$.

## Relation to mutual information

The Jensen–Shannon divergence is the [[Mutual Information]] between a random variable $X$ associated to a [mixture distribution](https://en.wikipedia.org/wiki/Mixture_distribution) between $P$ and $Q$ and the binary indicator variable $Z$ that is used to switch between $P$ and $Q$ to produce the mixture. Let $X$ be some abstract function on the underlying set of events that discriminates well between events, and choose the value of $X$ according to $P$ if $Z=0$ and according to $Q$ if $Z=1$, where $Z$ is equiprobable. That is, we are choosing $X$ according to the probability measure $M=(P+Q)/2$, and its distribution is the mixture distribution. We compute

${\begin{aligned}I(X;Z)&=H(X)-H(X|Z)\\&=-\sum M\log M+{\frac {1}{2}}\left[\sum P\log P+\sum Q\log Q\right]\\&=-\sum {\frac {P}{2}}\log M-\sum {\frac {Q}{2}}\log M+{\frac {1}{2}}\left[\sum P\log P+\sum Q\log Q\right]\\&={\frac {1}{2}}\sum P\left(\log P-\log M\right)+{\frac {1}{2}}\sum Q\left(\log Q-\log M\right)\\&={\rm {JSD}}(P\parallel Q)\end{aligned}}$

It follows from the above result that the Jensen–Shannon divergence is bounded by 0 and 1 because mutual information is non-negative and bounded by $H(Z)=1$ in base 2 logarithm.

One can apply the same principle to a joint distribution and the product of its two [marginal distribution](https://en.wikipedia.org/wiki/Marginal_distribution) (in analogy to Kullback–Leibler divergence and mutual information) and to measure how reliably one can decide if a given response comes from the joint distribution or the product distribution—subject to the assumption that these are the only two possibilities.

## Quantum Jensen–Shannon divergence

The generalization of probability distributions on [density matrices](https://en.wikipedia.org/wiki/Density_matrices) allows to define quantum Jensen–Shannon divergence (QJSD). It is defined for a set of [density matrices](https://en.wikipedia.org/wiki/Density_matrices) $(\rho _{1},\ldots ,\rho _{n})$ and a probability distribution $\pi =(\pi _{1},\ldots ,\pi _{n})$ as

${\rm {QJSD}}(\rho _{1},\ldots ,\rho _{n})=S\left(\sum _{i=1}^{n}\pi _{i}\rho _{i}\right)-\sum _{i=1}^{n}\pi _{i}S(\rho _{i})$

where $S(\rho )$ is the [von Neumann entropy](https://en.wikipedia.org/wiki/Von_Neumann_entropy) of $\rho$. This quantity was introduced in [quantum information](https://en.wikipedia.org/wiki/Quantum_information) theory, where it is called the Holevo information: it gives the upper bound for amount of classical information encoded by the quantum states $(\rho _{1},\ldots ,\rho _{n})$ under the prior distribution $\pi$ (see [Holevo's theorem](https://en.wikipedia.org/wiki/Holevo%27s_theorem)). Quantum Jensen–Shannon divergence for $\pi =\left({\frac {1}{2}},{\frac {1}{2}}\right)$ and two density matrices is a symmetric function, everywhere defined, bounded and equal to zero only if two [density matrices](https://en.wikipedia.org/wiki/Density_matrices) are the same. It is a square of a metric for [pure states](https://en.wikipedia.org/wiki/Pure_states), and it was recently shown that this metric property holds for mixed states as well. The [Bures metric](https://en.wikipedia.org/wiki/Bures_metric) is closely related to the quantum JS divergence; it is the quantum analog of the [Fisher information metric](https://en.wikipedia.org/wiki/Fisher_information_metric).

## Jensen–Shannon centroid

The centroid C\* of a [finite set](https://en.wikipedia.org/wiki/Finite_set) of probability distributions can be defined as the minimizer of the average sum of the Jensen-Shannon divergences between a probability distribution and the prescribed set of distributions: 

$$
C^{*}=\arg \min _{Q}\sum _{i=1}^{n}{\rm {JSD}}(P_{i}\parallel Q)
$$

 An efficient algorithm (CCCP) based on difference of convex functions is reported to calculate the Jensen-Shannon centroid of a set of discrete distributions (histograms).

## Applications

The Jensen–Shannon divergence has been applied in [bioinformatics](https://en.wikipedia.org/wiki/Bioinformatics) and [genome comparison](https://en.wikipedia.org/wiki/Genome_comparison), in protein surface comparison, in the social sciences, in the quantitative study of history, in fire experiments, and in machine learning.

## Notes

1.  Frank Nielsen (2021). ["On a variational definition for the Jensen-Shannon symmetrization of distances based on the information radius"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7514974). *Entropy*. **23** (4). MDPI: 464. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2019Entrp..21..485N](https://ui.adsabs.harvard.edu/abs/2019Entrp..21..485N). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3390/e21050485](https://doi.org/10.3390%2Fe21050485). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [7514974](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7514974). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [33267199](https://pubmed.ncbi.nlm.nih.gov/33267199).
2.  Hinrich Schütze; Christopher D. Manning (1999). [Foundations of Statistical Natural Language Processing](https://nlp.stanford.edu/fsnlp/). Cambridge, Mass: MIT Press. p. 304. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-262-13360-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-262-13360-9).
3.  Dagan, Ido; [Lee, Lillian](https://en.wikipedia.org/wiki/Lillian_Lee_(computer_scientist) "Lillian Lee (computer scientist)"); Pereira, Fernando C. N. (1997). ["Similarity-based methods for word sense disambiguation"](https://aclanthology.org/P97-1008/). In Cohen, Philip R.; Wahlster, Wolfgang (eds.). *35th Annual Meeting of the Association for Computational Linguistics and 8th Conference of the European Chapter of the Association for Computational Linguistics, Proceedings of the Conference, 7–12 July 1997, Universidad Nacional de Educación a Distancia (UNED), Madrid, Spain*. Morgan Kaufmann Publishers / ACL. pp. 56–63. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[cmp-lg/9708010](https://arxiv.org/abs/cmp-lg/9708010). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3115/976909.979625](https://doi.org/10.3115%2F976909.979625).
4.  Endres, D. M.; J. E. Schindelin (2003). ["A new metric for probability distributions"](https://research-repository.st-andrews.ac.uk/bitstream/10023/1591/1/Endres2003-IEEETransInfTheory49-NewMetric.pdf) (PDF). *IEEE Trans. Inf. Theory*. **49** (7): 1858–1860. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2003ITIT...49.1858E](https://ui.adsabs.harvard.edu/abs/2003ITIT...49.1858E). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/TIT.2003.813506](https://doi.org/10.1109%2FTIT.2003.813506). [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[10023/1591](https://hdl.handle.net/10023%2F1591). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [14437777](https://api.semanticscholar.org/CorpusID:14437777).
5.  Ôsterreicher, F.; I. Vajda (2003). "A new class of metric divergences on probability spaces and its statistical applications". *Ann. Inst. Statist. Math*. **55** (3): 639–653. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/BF02517812](https://doi.org/10.1007%2FBF02517812). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [13085920](https://api.semanticscholar.org/CorpusID:13085920).
6.  Fuglede, B.; Topsoe, F. (2004). ["Jensen-Shannon divergence and Hilbert space embedding"](https://www.math.ku.dk/~topsoe/ISIT2004JSD.pdf) (PDF). *Proceedings of the International Symposium on Information Theory, 2004*. IEEE. p. 30. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/ISIT.2004.1365067](https://doi.org/10.1109%2FISIT.2004.1365067). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-7803-8280-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-7803-8280-0). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [7891037](https://api.semanticscholar.org/CorpusID:7891037).
7.  Frank Nielsen (2019). ["On the Jensen-Shannon symmetrization of distances relying on abstract means"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7514974). *Entropy*. **21** (5). MDPI: 485. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1904.04017](https://arxiv.org/abs/1904.04017). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2019Entrp..21..485N](https://ui.adsabs.harvard.edu/abs/2019Entrp..21..485N). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3390/e21050485](https://doi.org/10.3390%2Fe21050485). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [7514974](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7514974). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [33267199](https://pubmed.ncbi.nlm.nih.gov/33267199).
8.  ^   Lin, J. (1991). ["Divergence measures based on the shannon entropy"](https://www.cise.ufl.edu/~anand/sp06/jensen-shannon.pdf) (PDF). *IEEE Transactions on Information Theory*. **37** (1): 145–151. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.127.9167](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.127.9167). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/18.61115](https://doi.org/10.1109%2F18.61115). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [12121632](https://api.semanticscholar.org/CorpusID:12121632).
9.  Schneidman, Elad; Bialek, W; Berry, M.J. II (2003). ["Synergy, Redundancy, and Independence in Population Codes"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6740962). *Journal of Neuroscience*. **23** (37): 11539–11553. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1523/JNEUROSCI.23-37-11539.2003](https://doi.org/10.1523%2FJNEUROSCI.23-37-11539.2003). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [6740962](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6740962). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [14684857](https://pubmed.ncbi.nlm.nih.gov/14684857).
10. Majtey, A.; Lamberti, P.; Prato, D. (2005). "Jensen-Shannon divergence as a measure of distinguishability between mixed quantum states". *Physical Review A*. **72** (5) 052310. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[quant-ph/0508138](https://arxiv.org/abs/quant-ph/0508138). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2005PhRvA..72e2310M](https://ui.adsabs.harvard.edu/abs/2005PhRvA..72e2310M). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1103/PhysRevA.72.052310](https://doi.org/10.1103%2FPhysRevA.72.052310). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [32062112](https://api.semanticscholar.org/CorpusID:32062112).
11. Briët, Jop; Harremoës, Peter (2009). "Properties of classical and quantum Jensen-Shannon divergence". *Physical Review A*. **79** (5) 052311. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[0806.4472](https://arxiv.org/abs/0806.4472). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2009PhRvA..79e2311B](https://ui.adsabs.harvard.edu/abs/2009PhRvA..79e2311B). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1103/PhysRevA.79.052311](https://doi.org/10.1103%2FPhysRevA.79.052311).
12. [Holevo, A. S.](https://en.wikipedia.org/wiki/Alexander_Holevo) (1973), "Bounds for the quantity of information transmitted by a quantum communication channel", *Problemy Peredachi Informatsii* (in Russian), **9**: 3–11. English translation: *Probl. Inf. Transm*., **9**: 177–183 (1975) [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0456936](https://mathscinet.ams.org/mathscinet-getitem?mr=0456936)
13. Braunstein, Samuel; Caves, Carlton (1994). "Statistical distance and the geometry of quantum states". *Physical Review Letters*. **72** (22): 3439–3443. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1994PhRvL..72.3439B](https://ui.adsabs.harvard.edu/abs/1994PhRvL..72.3439B). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1103/PhysRevLett.72.3439](https://doi.org/10.1103%2FPhysRevLett.72.3439). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [10056200](https://pubmed.ncbi.nlm.nih.gov/10056200).
14. Virosztek, Dániel (2021). "The metric property of the quantum Jensen-Shannon divergence". *[Advances in Mathematics](https://en.wikipedia.org/wiki/Advances_in_Mathematics)*. **380** 107595. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1910.10447](https://arxiv.org/abs/1910.10447). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.aim.2021.107595](https://doi.org/10.1016%2Fj.aim.2021.107595). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [204837864](https://api.semanticscholar.org/CorpusID:204837864).
15. Sra, Suvrit (2019). "Metrics Induced by Quantum Jensen-Shannon-Renyí and Related Divergences". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1911.02643](https://arxiv.org/abs/1911.02643) \[[cs.IT](https://arxiv.org/archive/cs.IT)\].
16. Frank Nielsen (2021). ["On a generalization of the Jensen-Shannon divergence and the Jensen--Shannon centroid"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7516653). *Entropy*. **22** (2). MDPI: 221. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3390/e22020221](https://doi.org/10.3390%2Fe22020221). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [7516653](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7516653). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [33285995](https://pubmed.ncbi.nlm.nih.gov/33285995).
17. Sims, GE; Jun, SR; Wu, GA; Kim, SH (2009). ["Alignment-free genome comparison with feature frequency profiles (FFP) and optimal resolutions"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2634796). *[Proceedings of the National Academy of Sciences of the United States of America](https://en.wikipedia.org/wiki/Proceedings_of_the_National_Academy_of_Sciences_of_the_United_States_of_America)*. **106** (8): 2677–82. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2009PNAS..106.2677S](https://ui.adsabs.harvard.edu/abs/2009PNAS..106.2677S). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1073/pnas.0813249106](https://doi.org/10.1073%2Fpnas.0813249106). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [2634796](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2634796). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [19188606](https://pubmed.ncbi.nlm.nih.gov/19188606).
18. Itzkovitz, S; Hodis, E; Segal, E (2010). ["Overlapping codes within protein-coding sequences"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2963821). *Genome Research*. **20** (11): 1582–9. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1101/gr.105072.110](https://doi.org/10.1101%2Fgr.105072.110). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [2963821](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2963821). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [20841429](https://pubmed.ncbi.nlm.nih.gov/20841429).
19. Ofran, Y; Rost, B (2003). "Analysing six types of protein-protein interfaces". *Journal of Molecular Biology*. **325** (2): 377–87. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.6.9207](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.6.9207). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/s0022-2836(02)01223-8](https://doi.org/10.1016%2Fs0022-2836%2802%2901223-8). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [12488102](https://pubmed.ncbi.nlm.nih.gov/12488102).
20. DeDeo, Simon; Hawkins, Robert X. D.; Klingenstein, Sara; Hitchcock, Tim (2013). ["Bootstrap Methods for the Empirical Study of Decision-Making and Information Flows in Social Systems"](https://doi.org/10.3390%2Fe15062246). *Entropy*. **15** (6): 2246–2276. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1302.0907](https://arxiv.org/abs/1302.0907). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2013Entrp..15.2246D](https://ui.adsabs.harvard.edu/abs/2013Entrp..15.2246D). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3390/e15062246](https://doi.org/10.3390%2Fe15062246).
21. Klingenstein, Sara; Hitchcock, Tim; DeDeo, Simon (2014). ["The civilizing process in London's Old Bailey"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4084475). *[Proceedings of the National Academy of Sciences of the United States of America](https://en.wikipedia.org/wiki/Proceedings_of_the_National_Academy_of_Sciences_of_the_United_States_of_America)*. **111** (26): 9419–9424. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2014PNAS..111.9419K](https://ui.adsabs.harvard.edu/abs/2014PNAS..111.9419K). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1073/pnas.1405984111](https://doi.org/10.1073%2Fpnas.1405984111). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [4084475](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4084475). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [24979792](https://pubmed.ncbi.nlm.nih.gov/24979792).
22. Flavia-Corina Mitroi-Symeonidis; Ion Anghel; Nicuşor Minculete (2020). ["Parametric Jensen-Shannon statistical complexity and its applications on full-scale compartment fire data"](https://doi.org/10.3390%2Fsym12010022). *Symmetry*. **12** (1): 22. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3390/sym12010022](https://doi.org/10.3390%2Fsym12010022).
23. Goodfellow, Ian J.; Pouget-Abadie, Jean; Mirza, Mehdi; Xu, Bing; Warde-Farley, David; Ozair, Sherjil; Courville, Aaron; [Bengio, Yoshua](https://en.wikipedia.org/wiki/Yoshua_Bengio) (2014). *Generative Adversarial Networks*. [NIPS](https://en.wikipedia.org/wiki/Advances_in_Neural_Information_Processing_Systems). [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1406.2661](https://arxiv.org/abs/1406.2661). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2014arXiv1406.2661G](https://ui.adsabs.harvard.edu/abs/2014arXiv1406.2661G).

## External links

- [Ruby gem for calculating JS divergence](https://github.com/evansenter/diverge)
- [Python function for calculating JS distance](https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.distance.jensenshannon.html#scipy.spatial.distance.jensenshannon), ([SciPy](https://en.wikipedia.org/wiki/SciPy))
- [THOTH: a python package for the efficient estimation of information-theoretic quantities from empirical data](https://sites.santafe.edu/~simon/page7/page7.html)
- [statcomp R library for calculating complexity measures including Jensen-Shannon Divergence](https://cran.r-project.org/web/packages/statcomp/)
