[[information-theory.base]]

> Source: [Information bottleneck method](https://en.wikipedia.org/wiki/Information_bottleneck_method)
> License: Wikipedia content is available under CC BY-SA 4.0.

The **information bottleneck method** is a technique in [information theory](https://en.wikipedia.org/wiki/Information_theory) introduced by [Naftali Tishby](https://en.wikipedia.org/wiki/Naftali_Tishby), Fernando C. Pereira, and [William Bialek](https://en.wikipedia.org/wiki/William_Bialek). It is designed for finding the best tradeoff between [accuracy](https://en.wikipedia.org/wiki/Accuracy) and complexity ([compression](https://en.wikipedia.org/wiki/Data_compression)) when [summarizing](https://en.wikipedia.org/wiki/Random_variable) (e.g. [clustering](https://en.wikipedia.org/wiki/Data_clustering)) a [random variable](https://en.wikipedia.org/wiki/Random_variable) **X**, given a [joint probability distribution](https://en.wikipedia.org/wiki/Joint_probability_distribution) **p(X,Y)** between **X** and an observed relevant variable **Y** - and self-described as providing *"a surprisingly rich framework for discussing a variety of problems in signal processing and learning"*.

Applications include distributional clustering and [dimension reduction](https://en.wikipedia.org/wiki/Dimension_reduction), and more recently it has been suggested as a theoretical foundation for [deep learning](https://en.wikipedia.org/wiki/Deep_learning). It generalized the classical notion of minimal [[Sufficient Statistics]] from [parametric statistics](https://en.wikipedia.org/wiki/Parametric_statistics) to arbitrary distributions, not necessarily of exponential form. It does so by relaxing the sufficiency condition to capture some fraction of the [[Mutual Information]] with the relevant variable **Y**.

The information bottleneck can also be viewed as a [[Rate Distortion Theory|rate distortion]] problem, with a distortion function that measures how well **Y** is predicted from a compressed representation **T** compared to its direct prediction from **X**. This interpretation provides a general iterative algorithm for solving the information bottleneck trade-off and calculating the information curve from the distribution **p(X,Y)**.

Let the compressed representation be given by random variable $T$. The algorithm minimizes the following functional with respect to conditional distribution $p(t|x)$:

$\inf _{p(t|x)}\,\,{\Big (}I(X;T)-\beta I(T;Y){\Big )},$

where $I(X;T)$ and $I(T;Y)$ are the mutual information of $X$ and $T$, and of $T$ and $Y$, respectively, and $\beta$ is a [Lagrange multiplier](https://en.wikipedia.org/wiki/Lagrange_multiplier).

## Learning theory for deep learning

It has been mathematically proven that controlling information bottleneck is one way to control [[Generalization Error]] in deep learning. Namely, the generalization error is proven to scale as ${\tilde {O}}\left({\sqrt {\frac {I(X,T)+1}{n}}}\right)$ where $n$ is the number of training samples, $X$ is the input to a deep neural network, and $T$ is the output of a hidden layer. This generalization bound scale with the degree of information bottleneck, unlike the other generalization bounds that scale with the number of parameters, [[VC Dimension]], [[Rademacher Complexity]], stability or robustness.

## Phase transitions

## Information theory of deep learning

Theory of Information Bottleneck is recently used to study Deep Neural Networks (DNN). Consider $X$ and $Y$ respectively as the input and output layers of a DNN, and let $T$ be any hidden layer of the network. Shwartz-Ziv and Tishby proposed the information bottleneck that expresses the tradeoff between the mutual information measures $I(X,T)$ and $I(T,Y)$. In this case, $I(X,T)$ and $I(T,Y)$ respectively quantify the amount of information that the hidden layer contains about the input and the output. They conjectured that the training process of a DNN consists of two separate phases; 1) an initial fitting phase in which $I(T,Y)$ increases, and 2) a subsequent compression phase in which $I(X,T)$ decreases. Saxe et al. in  countered the claim of Shwartz-Ziv and Tishby, stating that this compression phenomenon in DNNs is not comprehensive, and it depends on the particular [activation function](https://en.wikipedia.org/wiki/Activation_function). In particular, they claimed that the compression does not happen with ReLu activation functions. Shwartz-Ziv and Tishby disputed these claims, arguing that Saxe et al. had not observed compression due to weak estimates of the mutual information. On the other hand, recently Goldfeld et al. have argued that the observed compression is a result of geometric, and not of information-theoretic phenomena, a view that has been shared also in.

## Variational bottleneck

## Gaussian bottleneck

The Gaussian bottleneck, namely, applying the information bottleneck approach to Gaussian variables, leads to solutions related to [canonical correlation](https://en.wikipedia.org/wiki/Canonical_correlation) analysis. Assume $X,Y\,$ are jointly multivariate zero mean normal vectors with covariances $\Sigma _{XX},\,\,\Sigma _{YY}$ and $T\,$ is a compressed version of $X\,$ that must maintain a given value of mutual information with $Y\,$. It can be shown that the optimum $T\,$ is a normal vector consisting of linear combinations of the elements of $X,\,\,T=AX\,$ where matrix $A\,$ has orthogonal rows.

The projection matrix $A\,$ in fact contains $M\,$ rows selected from the weighted left [eigenvectors](https://en.wikipedia.org/wiki/Eigenvectors) of the [[Singular Value Decomposition]] of the matrix (generally asymmetric)

$\Omega =\Sigma _{X|Y}\Sigma _{XX}^{-1}=I-\Sigma _{XY}\Sigma _{YY}^{-1}\Sigma _{XY}^{T}\Sigma _{XX}^{-1}.\,$

Define the singular value decomposition

$\Omega =U\Lambda V^{T}{\text{ with }}\Lambda =\operatorname {Diag} {\big (}\lambda _{1}\leq \lambda _{2}\cdots \lambda _{N}{\big )}\,$

and the critical values

$\beta _{i}^{C}{\underset {\lambda _{i}<1}{=}}(1-\lambda _{i})^{-1}.\,$

then the number $M\,$ of active eigenvectors in the projection, or order of approximation, is given by

$\beta _{M-1}^{C}<\beta \leq \beta _{M}^{C}$

And we finally get

$A=[w_{1}U_{1},\dots ,w_{M}U_{M}]^{T}$

In which the weights are given by

$w_{i}={\sqrt {\left(\beta (1-\lambda _{i})-1\right)/\lambda _{i}r_{i}}}$

where $r_{i}=U_{i}^{T}\Sigma _{XX}U_{i}.\,$

Applying the Gaussian information bottleneck to [time series](https://en.wikipedia.org/wiki/Time_series) (processes), yields solutions related to optimal [predictive coding](https://en.wikipedia.org/wiki/Predictive_coding). This procedure is formally equivalent to **linear** Slow Feature Analysis.

Optimal temporal structures in linear dynamic systems can be revealed in the so-called past-future information bottleneck, an application of the bottleneck method to non-Gaussian sampled data. The concept, as treated by Creutzig, Tishby et al., is not without complication as two independent phases make up in the exercise: firstly estimation of the unknown parent probability densities from which the data samples are drawn and secondly the use of these densities within the information theoretic framework of the bottleneck.

### Density estimation

Since the bottleneck method is framed in probabilistic rather than statistical terms, the underlying probability density at the sample points $X={x_{i}}\,$must be estimated. This is a well known problem with multiple solutions described by [Silverman](https://en.wikipedia.org/wiki/Bernard_Silverman). In the present method, joint sample probabilities are found by use of a [Markov transition matrix](https://en.wikipedia.org/wiki/Stochastic_matrix) method and this has some mathematical synergy with the bottleneck method itself.

The arbitrarily increasing distance metric $f\,$ between all sample pairs and [distance matrix](https://en.wikipedia.org/wiki/Distance_matrix) is $d_{i,j}=f{\Big (}{\Big |}x_{i}-x_{j}{\Big |}{\Big )}$ . Then transition probabilities between sample pairs $P_{i,j}=\exp(-\lambda d_{i,j})\,$ for some $\lambda >0\,$must be computed. Treating samples as states, and a normalised version of $P\,$ as a Markov state transition probability matrix, the vector of probabilities of the 'states' after $t\,$ steps, conditioned on the initial state $p(0)\,$, is $p(t)=P^{t}p(0)\,$. The equilibrium probability vector $p(\infty )\,$ given, in the usual way, by the dominant eigenvector of matrix $P\,$ which is independent of the initialising vector $p(0)\,$. This Markov transition method establishes a probability at the sample points which is claimed to be proportional to the probabilities' densities there.

Other interpretations of the use of the eigenvalues of distance matrix $d\,$ are discussed in Silverman's *Density Estimation for Statistics and Data Analysis*.

### Clusters

In the following soft clustering example, the reference vector $Y\,$ contains sample categories and the joint probability $p(X,Y)\,$ is assumed known. A soft cluster $c_{k}\,$ is defined by its probability distribution over the data samples $x_{i}:\,\,\,p(c_{k}|x_{i})$. Tishby et al. presented the following iterative set of equations to determine the clusters which are ultimately a generalization of the [Blahut-Arimoto algorithm](https://en.wikipedia.org/wiki/Blahut-Arimoto_algorithm), developed in [[Rate Distortion Theory]]. The application of this type of algorithm in neural networks appears to originate in entropy arguments arising in the application of [Gibbs Distributions](https://en.wikipedia.org/wiki/Boltzmann_distribution) in deterministic annealing.

${\begin{cases}p(c|x)=Kp(c)\exp {\Big (}-\beta \,D^{KL}{\Big [}p(y|x)\,||\,p(y|c){\Big ]}{\Big )}\\p(y|c)=\textstyle \sum _{x}p(y|x)p(c|x)p(x){\big /}p(c)\\p(c)=\textstyle \sum _{x}p(c|x)p(x)\\\end{cases}}$

The function of each line of the iteration expands as

**Line 1:** This is a matrix valued set of conditional probabilities

$A_{i,j}=p(c_{i}|x_{j})=Kp(c_{i})\exp {\Big (}-\beta \,D^{KL}{\Big [}p(y|x_{j})\,||\,p(y|c_{i}){\Big ]}{\Big )}$

The [[Kullback-Leibler Divergence|Kullback–Leibler divergence]] $D^{KL}\,$ between the $Y\,$ vectors generated by the sample data $x\,$ and those generated by its reduced information proxy $c\,$ is applied to assess the fidelity of the compressed vector with respect to the reference (or categorical) data $Y\,$ in accordance with the fundamental bottleneck equation. $D^{KL}(a||b)\,$ is the Kullback–Leibler divergence between distributions $a,b\,$

$D^{KL}(a||b)=\sum _{i}p(a_{i})\log {\Big (}{\frac {p(a_{i})}{p(b_{i})}}{\Big )}$

and $K\,$ is a scalar normalization. The weighting by the negative exponent of the distance means that prior cluster probabilities are downweighted in line 1 when the Kullback–Leibler divergence is large, thus successful clusters grow in probability while unsuccessful ones decay.

**Line 2:** Second matrix-valued set of conditional probabilities. By definition

${\begin{aligned}p(y_{i}|c_{k})&=\sum _{j}p(y_{i}|x_{j})p(x_{j}|c_{k})\\&=\sum _{j}p(y_{i}|x_{j})p(x_{j},c_{k}){\big /}p(c_{k})\\&=\sum _{j}p(y_{i}|x_{j})p(c_{k}|x_{j})p(x_{j}){\big /}p(c_{k})\\\end{aligned}}$

where the Bayes identities $p(a,b)=p(a|b)p(b)=p(b|a)p(a)\,$ are used.

**Line 3:** this line finds the [marginal distribution](https://en.wikipedia.org/wiki/Marginal_distribution) of the clusters $c\,$

${\begin{aligned}p(c_{i})&=\sum _{j}p(c_{i},x_{j})&=\sum _{j}p(c_{i}|x_{j})p(x_{j})\end{aligned}}$

This is a standard result.

Further inputs to the algorithm are the marginal sample distribution $p(x)\,$ which has already been determined by the dominant eigenvector of $P\,$ and the matrix valued Kullback–Leibler divergence function

$D_{i,j}^{KL}=D^{KL}{\Big [}p(y|x_{j})\,||\,p(y|c_{i}){\Big ]}{\Big )}$

derived from the sample spacings and transition probabilities.

The matrix $p(y_{i}|c_{j})\,$ can be initialized randomly or with a reasonable guess, while matrix $p(c_{i}|x_{j})\,$ needs no prior values. Although the algorithm converges, multiple minima may exist that would need to be resolved.

## Defining decision contours

To categorize a new sample $x'\,$ external to the training set $X\,$, the previous distance metric finds the transition probabilities between $x'\,$ and all samples in $X:\,\,$, ${\tilde {p}}(x_{i})=p(x_{i}|x')=\mathrm {K} \exp {\Big (}-\lambda f{\big (}{\Big |}x_{i}-x'{\Big |}{\big )}{\Big )}$ with $\mathrm {K} \,$ a normalization. Secondly apply the last two lines of the 3-line algorithm to get cluster and conditional category probabilities.

${\begin{aligned}&{\tilde {p}}(c_{i})=p(c_{i}|x')=\sum _{j}p(c_{i}|x_{j})p(x_{j}|x')=\sum _{j}p(c_{i}|x_{j}){\tilde {p}}(x_{j})\\&p(y_{i}|c_{j})=\sum _{k}p(y_{i}|x_{k})p(c_{j}|x_{k})p(x_{k}|x')/p(c_{j}|x')=\sum _{k}p(y_{i}|x_{k})p(c_{j}|x_{k}){\tilde {p}}(x_{k})/{\tilde {p}}(c_{j})\\\end{aligned}}$

Finally

$p(y_{i}|x')=\sum _{j}p(y_{i}|c_{j})p(c_{j}|x'))=\sum _{j}p(y_{i}|c_{j}){\tilde {p}}(c_{j})\,$

Parameter $\beta \,$ must be kept under close supervision since, as it is increased from zero, increasing numbers of features, in the category probability space, snap into focus at certain critical thresholds.

### An example

The following case examines clustering in a four quadrant multiplier with random inputs $u,v\,$ and two categories of output, $\pm 1\,$, generated by $y=\operatorname {sign} (uv)\,$. This function has two spatially separated clusters for each category and so demonstrates that the method can handle such distributions.

20 samples are taken, uniformly distributed on the square $[-1,1]^{2}\,$ . The number of clusters used beyond the number of categories, two in this case, has little effect on performance and the results are shown for two clusters using parameters $\lambda =3,\,\beta =2.5$.

The distance function is $d_{i,j}={\Big |}x_{i}-x_{j}{\Big |}^{2}$ where $x_{i}=(u_{i},v_{i})^{T}\,$ while the conditional distribution $p(y|x)\,$ is a 2 × 20 matrix

${\begin{aligned}&Pr(y_{i}=1)=1{\text{ if }}\operatorname {sign} (u_{i}v_{i})=1\,\\&Pr(y_{i}=-1)=1{\text{ if }}\operatorname {sign} (u_{i}v_{i})=-1\,\end{aligned}}$

and zero elsewhere.

The summation in line 2 incorporates only two values representing the training values of +1 or −1, but nevertheless works well. The figure shows the locations of the twenty samples with '0' representing *Y* = 1 and 'x' representing *Y* = −1. The contour at the unity likelihood ratio level is shown,

$L={\frac {\Pr(1)}{\Pr(-1)}}=1$

as a new sample $x'\,$is scanned over the square. Theoretically the contour should align with the $u=0\,$ and $v=0\,$ coordinates but for such small sample numbers they have instead followed the spurious clusterings of the sample points.

![[media/cb95f38910826ad78d93fdc248789896243c1178.jpg]]
Decision contours

### Neural network/fuzzy logic analogies

This algorithm is somewhat analogous to a neural network with a single hidden layer. The internal nodes are represented by the clusters $c_{j}\,$ and the first and second layers of network weights are the conditional probabilities $p(c_{j}|x_{i})\,$ and $p(y_{k}|c_{j})\,$ respectively. However, unlike a standard neural network, the algorithm relies entirely on probabilities as inputs rather than the sample values themselves, while internal and output values are all conditional probability density distributions. Nonlinear functions are encapsulated in distance metric $f(.)\,$ (or *influence functions/radial basis functions*) and transition probabilities instead of [sigmoid functions](https://en.wikipedia.org/wiki/Sigmoid_function).

The Blahut-Arimoto three-line algorithm converges rapidly, often in tens of iterations, and by varying $\beta \,$, $\lambda \,$ and $f\,$ and the cardinality of the clusters, various levels of focus on features can be achieved.

The statistical soft clustering definition $p(c_{i}|x_{j})\,$ has some overlap with the verbal fuzzy membership concept of [fuzzy logic](https://en.wikipedia.org/wiki/Fuzzy_logic).

## Extensions

An interesting extension is the case of information bottleneck with side information. Here information is maximized about one target variable and minimized about another, learning a representation that is informative about selected aspects of data. Formally

$\min _{p(t|x)}\,\,I(X;T)-\beta ^{+}I(T;Y^{+})+\beta ^{-}I(T;Y^{-})$

## Bibliography

- Weiss, Y. (1999), "Segmentation using eigenvectors: a unifying view", [Proceedings IEEE International Conference on Computer Vision](https://www.cs.huji.ac.il/~yweiss/iccv99.pdf) (PDF), pp. 975–982
- P. Harremoës and N. Tishby ["The Information Bottleneck Revisited or How to Choose a Good Distortion Measure". In proceedings of the International Symposium on Information Theory (ISIT) 2007](http://www.cs.huji.ac.il/labs/learning/Papers/flaske2.pdf)

## References

1.  ^    [Tishby, Naftali](https://en.wikipedia.org/wiki/Naftali_Tishby); Pereira, Fernando C.; [Bialek, William](https://en.wikipedia.org/wiki/William_Bialek) (September 1999). [The Information Bottleneck Method](http://www.cs.huji.ac.il/labs/learning/Papers/allerton.pdf) (PDF). The 37th annual Allerton Conference on Communication, Control, and Computing. pp. 368–377.
2.  Kenji Kawaguchi, Zhun Deng, Xu Ji, Jiaoyang Huang.["How Does Information Bottleneck Help Deep Learning?"](https://proceedings.mlr.press/v202/kawaguchi23a.html) Proceedings of the 40th International Conference on Machine Learning, PMLR 202:16049-16096, 2023.
3.  ^   Shwartz-Ziv, Ravid; Tishby, Naftali (2017). "Opening the black box of deep neural networks via information". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1703.00810](https://arxiv.org/abs/1703.00810) \[[cs.LG](https://arxiv.org/archive/cs.LG)\].
4.  Andrew M, Saxe; et al. (2018). ["On the information bottleneck theory of deep learning"](https://openreview.net/pdf?id=ry_WPG-A-). *ICLR 2018 Conference Blind Submission*. **2019** (12): 124020. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2019JSMTE..12.4020S](https://ui.adsabs.harvard.edu/abs/2019JSMTE..12.4020S). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1088/1742-5468/ab3985](https://doi.org/10.1088%2F1742-5468%2Fab3985). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [49584497](https://api.semanticscholar.org/CorpusID:49584497).
5.  Goldfeld, Ziv; et al. (2019). ["Estimating Information Flow in Deep Neural Networks"](http://proceedings.mlr.press/v97/goldfeld19a.html). *Icml 2019*: 2299–2308. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1810.05728](https://arxiv.org/abs/1810.05728).
6.  Geiger, Bernhard C. (2022). "On Information Plane Analyses of Neural Network Classifiers—A Review". *IEEE Transactions on Neural Networks and Learning Systems*. **33** (12): 7039–7051. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2003.09671](https://arxiv.org/abs/2003.09671). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2022ITNNL..33.7039G](https://ui.adsabs.harvard.edu/abs/2022ITNNL..33.7039G). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/TNNLS.2021.3089037](https://doi.org/10.1109%2FTNNLS.2021.3089037). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [34191733](https://pubmed.ncbi.nlm.nih.gov/34191733). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [214611728](https://api.semanticscholar.org/CorpusID:214611728).
7.  Chechik, Gal; Globerson, Amir; Tishby, Naftali; Weiss, Yair (1 January 2005). Dayan, Peter (ed.). ["Information Bottleneck for Gaussian Variables"](http://www.jmlr.org/papers/volume6/chechik05a/chechik05a.pdf) (PDF). *Journal of Machine Learning Research* (6) (published 1 May 2005): 165–188.
8.  [Creutzig, Felix](https://en.wikipedia.org/wiki/Felix_Creutzig); Sprekeler, Henning (2007-12-17). "Predictive Coding and the Slowness Principle: An Information-Theoretic Approach". *Neural Computation*. **20** (4): 1026–1041. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.169.6917](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.169.6917). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1162/neco.2008.01-07-455](https://doi.org/10.1162%2Fneco.2008.01-07-455). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0899-7667](https://search.worldcat.org/issn/0899-7667). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [18085988](https://pubmed.ncbi.nlm.nih.gov/18085988). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [2138951](https://api.semanticscholar.org/CorpusID:2138951).
9.  Creutzig, Felix; Globerson, Amir; Tishby, Naftali (2009-04-27). "Past-future information bottleneck in dynamical systems". *Physical Review E*. **79** (4) 041925. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2009PhRvE..79d1925C](https://ui.adsabs.harvard.edu/abs/2009PhRvE..79d1925C). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1103/PhysRevE.79.041925](https://doi.org/10.1103%2FPhysRevE.79.041925). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [19518274](https://pubmed.ncbi.nlm.nih.gov/19518274).
10. ^   [Silverman, Bernie](https://en.wikipedia.org/wiki/Bernie_Silverman) (1986). [Density Estimation for Statistics and Data Analysis](https://archive.org/details/densityestimatio00silv_0). Monographs on Statistics and Applied Probability. Chapman & Hall. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1986desd.book.....S](https://ui.adsabs.harvard.edu/abs/1986desd.book.....S). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-412-24620-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-412-24620-3).
11. Slonim, Noam; Tishby, Naftali (2000-01-01). "Document clustering using word clusters via the information bottleneck method". *Proceedings of the 23rd annual international ACM SIGIR conference on Research and development in information retrieval*. SIGIR '00. New York, NY, USA: ACM. pp. 208–215. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.21.3062](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.21.3062). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1145/345508.345578](https://doi.org/10.1145%2F345508.345578). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-58113-226-7](https://en.wikipedia.org/wiki/Special:BookSources/978-1-58113-226-7). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [1373541](https://api.semanticscholar.org/CorpusID:1373541).
12. D. J. Miller, A. V. Rao, K. Rose, A. Gersho: "An Information-theoretic Learning Algorithm for Neural Network Classification". NIPS 1995: pp. 591–597
13. [Tishby, Naftali](https://en.wikipedia.org/wiki/Naftali_Tishby); Slonim, N. [Data clustering by Markovian Relaxation and the Information Bottleneck Method](https://papers.nips.cc/paper/1896-data-clustering-by-markovian-relaxation-and-the-information-bottleneck-method.pdf) (PDF). Neural Information Processing Systems (NIPS) 2000. pp. 640–646.
14. Chechik, Gal; Tishby, Naftali (2002). ["Extracting Relevant Structures with Side Information"](http://papers.nips.cc/paper/2223-extracting-relevant-structures-with-side-information.pdf) (PDF). *Advances in Neural Information Processing Systems*: 857–864.
