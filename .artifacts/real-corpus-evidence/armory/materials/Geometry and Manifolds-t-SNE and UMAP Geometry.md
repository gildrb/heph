[[geometry-manifolds.base]]

> Source: [T-distributed stochastic neighbor embedding](https://en.wikipedia.org/wiki/T-distributed_stochastic_neighbor_embedding)
> License: Wikipedia content is available under CC BY-SA 4.0.

![[media/e3b8cacd314dd0ef38a0c28f29acaf198e921914.png]]
t-SNE visualisation of [word embeddings](https://en.wikipedia.org/wiki/Word_embedding) generated using 19th century literature

![[media/f0a5278d71faded24d3e2b72516ee41adfbc5d79.png]]
t-SNE embeddings of [MNIST](https://en.wikipedia.org/wiki/MNIST) dataset

**t-distributed stochastic neighbor embedding** (**t-SNE**) is a [statistical](https://en.wikipedia.org/wiki/Statistical) method for visualizing high-dimensional data by giving each datapoint a location in a two or three-dimensional map. It is based on Stochastic Neighbor Embedding originally developed by [Geoffrey Hinton](https://en.wikipedia.org/wiki/Geoffrey_Hinton) and Sam Roweis, where Laurens van der Maaten and Hinton proposed the [*t*-distributed](https://en.wikipedia.org/wiki/Student%27s_t-distribution) variant. It is a [nonlinear dimensionality reduction](https://en.wikipedia.org/wiki/Nonlinear_dimensionality_reduction) technique for embedding high-dimensional data for visualization in a low-dimensional space of two or three dimensions. Specifically, it models each high-dimensional object by a two- or three-dimensional point in such a way that similar objects are modeled by nearby points and dissimilar objects are modeled by distant points with high probability.

The t-SNE algorithm comprises two main stages. First, t-SNE constructs a [probability distribution](https://en.wikipedia.org/wiki/Probability_distribution) over pairs of high-dimensional objects in such a way that similar objects are assigned a higher probability while dissimilar points are assigned a lower probability. Second, t-SNE defines a similar probability distribution over the points in the low-dimensional map, and it minimizes the [[Kullback-Leibler Divergence|Kullback–Leibler divergence]] (KL divergence) between the two distributions with respect to the locations of the points in the map. While the original algorithm uses the [Euclidean distance](https://en.wikipedia.org/wiki/Euclidean_distance) between objects as the base of its similarity metric, this can be changed as appropriate. A [Riemannian](https://en.wikipedia.org/wiki/Riemannian_metric) variant is [UMAP](https://en.wikipedia.org/wiki/Uniform_manifold_approximation_and_projection).

t-SNE has been used for visualization in a wide range of applications, including [genomics](https://en.wikipedia.org/wiki/Genomics), [computer security](https://en.wikipedia.org/wiki/Computer_security) research, [natural language processing](https://en.wikipedia.org/wiki/Natural_language_processing), [music analysis](https://en.wikipedia.org/wiki/Music_analysis), [cancer research](https://en.wikipedia.org/wiki/Cancer_research), [bioinformatics](https://en.wikipedia.org/wiki/Bioinformatics), geological domain interpretation, and biomedical signal processing.

For a data set with $n$ elements, t-SNE runs in $O(n^{2})$ time and requires $O(n^{2})$ space.

## Details

Given a set of $N$ high-dimensional objects $\mathbf {x} _{1},\dots ,\mathbf {x} _{N}$, t-SNE first computes probabilities $p_{ij}$ that are proportional to the similarity of objects $\mathbf {x} _{i}$ and $\mathbf {x} _{j}$, as follows.

For $i\neq j$, define

$p_{j\mid i}={\frac {\exp(-\lVert \mathbf {x} _{i}-\mathbf {x} _{j}\rVert ^{2}/2\sigma _{i}^{2})}{\sum _{k\neq i}\exp(-\lVert \mathbf {x} _{i}-\mathbf {x} _{k}\rVert ^{2}/2\sigma _{i}^{2})}}$

and set $p_{i\mid i}=0$. Note the above denominator ensures $\sum _{j}p_{j\mid i}=1$ for all $i$.

As van der Maaten and Hinton explained: "The similarity of datapoint $x_{j}$ to datapoint $x_{i}$ is the conditional probability, $p_{j|i}$, that $x_{i}$ would pick $x_{j}$ as its neighbor if neighbors were picked in proportion to their probability density under a Gaussian centered at $x_{i}$."

Now define

$p_{ij}={\frac {p_{j\mid i}+p_{i\mid j}}{2N}}$

This is motivated because $p_{i}$ and $p_{j}$ from the N samples are estimated as 1/N, so the conditional probability can be written as $p_{i\mid j}=Np_{ij}$ and $p_{j\mid i}=Np_{ji}$ . Since $p_{ij}=p_{ji}$, you can obtain previous formula.

Also note that $p_{ii}=0$ and $\sum _{i,j}p_{ij}=1$.

The bandwidth of the [Gaussian kernels](https://en.wikipedia.org/wiki/Gaussian_kernel) $\sigma _{i}$ is set in such a way that the [entropy](https://en.wikipedia.org/wiki/Entropy_(information_theory) "Entropy (information theory)") of the conditional distribution equals a predefined entropy using the [bisection method](https://en.wikipedia.org/wiki/Bisection_method). As a result, the bandwidth is adapted to the [density](https://en.wikipedia.org/wiki/Density) of the data: smaller values of $\sigma _{i}$ are used in denser parts of the data space. The entropy increases with the [perplexity](https://en.wikipedia.org/wiki/Perplexity) of this distribution $P_{i}$; this relation is seen as

$Perp(P_{i})=2^{H(P_{i})}$

where $H(P_{i})$ is the Shannon entropy $H(P_{i})=-\sum _{j}p_{j|i}\log _{2}p_{j|i}.$

The perplexity is a hand-chosen parameter of t-SNE, and as the authors state, "perplexity can be interpreted as a smooth measure of the effective number of neighbors. The performance of SNE is fairly robust to changes in the perplexity, and typical values are between 5 and 50.".

Since the Gaussian kernel uses the [Euclidean distance](https://en.wikipedia.org/wiki/Euclidean_distance) $\lVert x_{i}-x_{j}\rVert$, it is affected by the [curse of dimensionality](https://en.wikipedia.org/wiki/Curse_of_dimensionality), and in high dimensional data when distances lose the ability to discriminate, the $p_{ij}$ become too similar (asymptotically, they would converge to a constant). It has been proposed to adjust the distances with a power transform, based on the [intrinsic dimension](https://en.wikipedia.org/wiki/Intrinsic_dimension) of each point, to alleviate this.

t-SNE aims to learn a $d$-dimensional map $\mathbf {y} _{1},\dots ,\mathbf {y} _{N}$ (with $\mathbf {y} _{i}\in \mathbb {R} ^{d}$ and $d$ typically chosen as 2 or 3) that reflects the similarities $p_{ij}$ as well as possible. To this end, it measures similarities $q_{ij}$ between two points in the map $\mathbf {y} _{i}$ and $\mathbf {y} _{j}$, using a very similar approach. Specifically, for $i\neq j$, define $q_{ij}$ as

$q_{ij}={\frac {(1+\lVert \mathbf {y} _{i}-\mathbf {y} _{j}\rVert ^{2})^{-1}}{\sum _{k}\sum _{l\neq k}(1+\lVert \mathbf {y} _{k}-\mathbf {y} _{l}\rVert ^{2})^{-1}}}$

and set $q_{ii}=0$. Herein a heavy-tailed [Student t-distribution](https://en.wikipedia.org/wiki/Student_t-distribution) (with one-degree of freedom, which is the same as a [Cauchy distribution](https://en.wikipedia.org/wiki/Cauchy_distribution)) is used to measure similarities between low-dimensional points in order to allow dissimilar objects to be modeled far apart in the map.

The locations of the points $\mathbf {y} _{i}$ in the map are determined by minimizing the (non-symmetric) [[Kullback-Leibler Divergence|Kullback–Leibler divergence]] of the distribution $P$ from the distribution $Q$, that is:

$\mathrm {KL} \left(P\parallel Q\right)=\sum _{i\neq j}p_{ij}\log {\frac {p_{ij}}{q_{ij}}}$

The minimization of the Kullback–Leibler divergence with respect to the points $\mathbf {y} _{i}$ is performed using [[Gradient Descent]]. The result of this optimization is a map that reflects the similarities between the high-dimensional inputs.

## Output

While t-SNE plots often seem to display [clusters](https://en.wikipedia.org/wiki/Cluster_analysis), the visual clusters can be strongly influenced by the chosen parameterization (especially the perplexity) and so a good understanding of the parameters for t-SNE is needed. Such "clusters" can be shown to even appear in structured data with no clear clustering, and so may be false findings. Similarly, the size of clusters produced by t-SNE is not informative, and neither is the distance between clusters. Thus, interactive exploration may be needed to choose parameters and validate results. It has been shown that t-SNE can often recover well-separated clusters, and with special parameter choices, approximates a simple form of [spectral clustering](https://en.wikipedia.org/wiki/Spectral_clustering).

## Software

- A C++ implementation of Barnes-Hut is available on the [github account](https://github.com/lvdmaaten/bhtsne) of one of the original authors.
- The R package [Rtsne](https://CRAN.R-project.org/package=Rtsne) implements t-SNE in [R](https://en.wikipedia.org/wiki/R_(programming_language) "R (programming language)").
- [ELKI](https://en.wikipedia.org/wiki/ELKI) contains tSNE, also with Barnes-Hut approximation
- [scikit-learn](https://en.wikipedia.org/wiki/Scikit-learn), a popular machine learning library in Python implements t-SNE with both exact solutions and the Barnes-Hut approximation.
- Tensorboard, the visualization kit associated with [TensorFlow](https://en.wikipedia.org/wiki/TensorFlow), also implements t-SNE ([online version](https://projector.tensorflow.org/))
- The [Julia](https://en.wikipedia.org/wiki/Julia_(programming_language) "Julia (programming language)") package [TSne](https://juliapackages.com/p/tsne) implements t-SNE

## References

1.  Hinton, Geoffrey; Roweis, Sam (January 2002). [Stochastic neighbor embedding](https://papers.nips.cc/paper_files/paper/2002/file/6150ccc6069bea6b5716254057a194ef-Paper.pdf) (PDF). [Neural Information Processing Systems](https://en.wikipedia.org/wiki/Neural_Information_Processing_Systems).
2.  ^    van der Maaten, L.J.P.; Hinton, G.E. (Nov 2008). ["Visualizing Data Using t-SNE"](https://jmlr.org/papers/volume9/vandermaaten08a/vandermaaten08a.pdf) (PDF). *Journal of Machine Learning Research*. **9**: 2579–2605.
3.  Gashi, I.; Stankovic, V.; Leita, C.; Thonnard, O. (2009). "An Experimental Study of Diversity with Off-the-shelf AntiVirus Engines". *Proceedings of the IEEE International Symposium on Network Computing and Applications*: 4–11.
4.  Hamel, P.; Eck, D. (2010). "Learning Features from Music Audio with Deep Belief Networks". *Proceedings of the International Society for Music Information Retrieval Conference*: 339–344.
5.  Jamieson, A.R.; Giger, M.L.; Drukker, K.; Lui, H.; Yuan, Y.; Bhooshan, N. (2010). ["Exploring Nonlinear Feature Space Dimension Reduction and Data Representation in Breast CADx with Laplacian Eigenmaps and t-SNE"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2807447). *Medical Physics*. **37** (1): 339–351. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1118/1.3267037](https://doi.org/10.1118%2F1.3267037). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [2807447](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2807447). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [20175497](https://pubmed.ncbi.nlm.nih.gov/20175497).
6.  Wallach, I.; Liliean, R. (2009). ["The Protein-Small-Molecule Database, A Non-Redundant Structural Resource for the Analysis of Protein-Ligand Binding"](https://doi.org/10.1093%2Fbioinformatics%2Fbtp035). *Bioinformatics*. **25** (5): 615–620. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1093/bioinformatics/btp035](https://doi.org/10.1093%2Fbioinformatics%2Fbtp035). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [19153135](https://pubmed.ncbi.nlm.nih.gov/19153135).
7.  Balamurali, Mehala; Silversides, Katherine L.; Melkumyan, Arman (2019-04-01). ["A comparison of t-SNE, SOM and SPADE for identifying material type domains in geological data"](https://www.sciencedirect.com/science/article/pii/S0098300418306010). *Computers & Geosciences*. **125**: 78–89. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2019CG....125...78B](https://ui.adsabs.harvard.edu/abs/2019CG....125...78B). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.cageo.2019.01.011](https://doi.org/10.1016%2Fj.cageo.2019.01.011). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0098-3004](https://search.worldcat.org/issn/0098-3004). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [67926902](https://api.semanticscholar.org/CorpusID:67926902).
8.  Balamurali, Mehala; Melkumyan, Arman (2016). ["t-SNE Based Visualisation and Clustering of Geological Domain"](https://link.springer.com/chapter/10.1007/978-3-319-46681-1_67). In Hirose, Akira; Ozawa, Seiichi; Doya, Kenji; Ikeda, Kazushi; Lee, Minho; Liu, Derong (eds.). *Neural Information Processing*. Lecture Notes in Computer Science. Vol. 9950. Cham: Springer International Publishing. pp. 565–572. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-3-319-46681-1_67](https://doi.org/10.1007%2F978-3-319-46681-1_67). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-319-46681-1](https://en.wikipedia.org/wiki/Special:BookSources/978-3-319-46681-1).
9.  Leung, Raymond; Balamurali, Mehala; Melkumyan, Arman (2021-01-01). ["Sample Truncation Strategies for Outlier Removal in Geochemical Data: The MCD Robust Distance Approach Versus t-SNE Ensemble Clustering"](https://doi.org/10.1007/s11004-019-09839-z). *Mathematical Geosciences*. **53** (1): 105–130. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2021MatGe..53..105L](https://ui.adsabs.harvard.edu/abs/2021MatGe..53..105L). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s11004-019-09839-z](https://doi.org/10.1007%2Fs11004-019-09839-z). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1874-8953](https://search.worldcat.org/issn/1874-8953). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [208329378](https://api.semanticscholar.org/CorpusID:208329378).
10. Birjandtalab, J.; Pouyan, M. B.; Nourani, M. (2016-02-01). "Nonlinear dimension reduction for EEG-based epileptic seizure detection". *2016 IEEE-EMBS International Conference on Biomedical and Health Informatics (BHI)*. pp. 595–598. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/BHI.2016.7455968](https://doi.org/10.1109%2FBHI.2016.7455968). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-5090-2455-1](https://en.wikipedia.org/wiki/Special:BookSources/978-1-5090-2455-1). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [8074617](https://api.semanticscholar.org/CorpusID:8074617).
11. Pezzotti, Nicola (2015). "Approximated and User Steerable tSNE for Progressive Visual Analytics". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1512.01655](https://arxiv.org/abs/1512.01655) \[[cs.CV](https://arxiv.org/archive/cs.CV)\].
12. Schubert, Erich; Gertz, Michael (2017-10-04). *Intrinsic t-Stochastic Neighbor Embedding for Visualization and Outlier Detection*. SISAP 2017 – 10th International Conference on Similarity Search and Applications. pp. 188–203. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-3-319-68474-1_13](https://doi.org/10.1007%2F978-3-319-68474-1_13).
13. ["K-means clustering on the output of t-SNE"](https://stats.stackexchange.com/a/264647). *Cross Validated*. Retrieved 2018-04-16.
14. Wattenberg, Martin; Viégas, Fernanda; Johnson, Ian (2016-10-13). ["How to Use t-SNE Effectively"](https://distill.pub/2016/misread-tsne). *Distill*. **1** (10): e2. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.23915/distill.00002](https://doi.org/10.23915%2Fdistill.00002). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [2476-0757](https://search.worldcat.org/issn/2476-0757).
15. Pezzotti, Nicola; Lelieveldt, Boudewijn P. F.; Maaten, Laurens van der; Hollt, Thomas; Eisemann, Elmar; Vilanova, Anna (2017-07-01). "Approximated and User Steerable tSNE for Progressive Visual Analytics". *IEEE Transactions on Visualization and Computer Graphics*. **23** (7): 1739–1752. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1512.01655](https://arxiv.org/abs/1512.01655). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2017ITVCG..23.1739P](https://ui.adsabs.harvard.edu/abs/2017ITVCG..23.1739P). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/tvcg.2016.2570755](https://doi.org/10.1109%2Ftvcg.2016.2570755). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1077-2626](https://search.worldcat.org/issn/1077-2626). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [28113434](https://pubmed.ncbi.nlm.nih.gov/28113434). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [353336](https://api.semanticscholar.org/CorpusID:353336).
16. Wattenberg, Martin; Viégas, Fernanda; Johnson, Ian (2016-10-13). ["How to Use t-SNE Effectively"](https://distill.pub/2016/misread-tsne/). *Distill*. **1** (10). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.23915/distill.00002](https://doi.org/10.23915%2Fdistill.00002). Retrieved 4 December 2017.
17. Linderman, George C.; Steinerberger, Stefan (2017-06-08). "Clustering with t-SNE, provably". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1706.02582](https://arxiv.org/abs/1706.02582) \[[cs.LG](https://arxiv.org/archive/cs.LG)\].

## External links

- Wattenberg, Martin; Viégas, Fernanda; Johnson, Ian (2016-10-13). ["How to Use t-SNE Effectively"](https://distill.pub/2016/misread-tsne/). *Distill*. **1** (10): e2. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.23915/distill.00002](https://doi.org/10.23915%2Fdistill.00002). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [2476-0757](https://search.worldcat.org/issn/2476-0757).. Interactive demonstration and tutorial.
- [Visualizing Data Using t-SNE](https://www.youtube.com/watch?v=RJVL80Gg3lA), Google Tech Talk about t-SNE
- [Implementations of t-SNE in various languages](https://lvdmaaten.github.io/tsne/), A link collection maintained by Laurens van der Maaten
