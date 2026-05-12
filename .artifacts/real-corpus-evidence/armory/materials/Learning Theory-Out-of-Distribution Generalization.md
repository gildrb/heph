[[learning-theory.base]]

> Source: [Domain adaptation](https://en.wikipedia.org/wiki/Domain_adaptation)
> License: Wikipedia content is available under CC BY-SA 4.0.

![[media/4a99af70e6693dc6bef06697a0efc53c42b5af98.png]]
Taxonomy of transfer learning based on Pan &amp; Yang (2010). Domain adaptation falls under transductive transfer learning (same task, different domain, no target labels).

**Domain adaptation** is a field associated with [machine learning](https://en.wikipedia.org/wiki/Machine_learning) and [transfer learning](https://en.wikipedia.org/wiki/Inductive_transfer). It addresses the challenge of training a model on one data distribution (the **source domain**) and applying it to a related but different data distribution (the **target domain**).

A common example is [spam filtering](https://en.wikipedia.org/wiki/Anti-spam_techniques), where a model trained on emails from one user (source domain) is adapted to handle emails for another user with significantly different patterns (target domain).

Domain adaptation techniques can also leverage unrelated data sources to improve learning. When multiple source distributions are involved, the problem extends to **multi-source domain adaptation**.

Domain adaptation is a specific type of transfer learning. According to the taxonomy laid out by Pan and Yang (2010), it falls into the category of **transductive transfer learning**. In this setting, the source and target tasks are the same (e.g., both are object recognition), but the domains differ (different marginal distributions). This distinguishes it from *inductive transfer learning* (where labeled data is available for the target task) and *unsupervised transfer learning* (where labels are unavailable in both domains).

## Classification of domain adaptation problems

Domain adaptation setups are classified in two different ways: according to the distribution shift between the domains, and according to the available data from the target domain.

### Distribution shifts

Common distribution shifts are classified as follows:

- **Covariate Shift** occurs when the input distributions of the source and destination change, but the relationship between inputs and labels remains unchanged. The above-mentioned spam filtering example typically falls in this category. Namely, the distributions (patterns) of emails may differ between the domains, but emails labeled as spam in the one domain should similarly be labeled in another.
- **Prior Shift (Label Shift)** occurs when the label distribution differs between the source and target datasets, while the conditional distribution of features given labels remains the same. An example is a classifier of hair color in images from Italy (source domain) and Norway (target domain). The proportions of hair colors (labels) differ, but images within classes like blond and black-haired populations remain consistent across domains. A classifier for the Norway population can exploit this prior knowledge of class proportions to improve its estimates.
- **Concept Shift (Conditional Shift)** refers to changes in the relationship between features and labels, even if the input distribution remains the same. For instance, in medical diagnosis, the same symptoms (inputs) may indicate entirely different diseases (labels) in different populations (domains).

### Data available during training

Domain adaptation problems typically assume that some data from the target domain is available during training. Problems can be classified according to the type of this available data:

- **Unsupervised**: [Unlabeled data](https://en.wikipedia.org/wiki/Unlabeled_data) from the target domain is available, but no labeled data. In the above-mentioned example of spam filtering, this corresponds to the case where emails from the target domain (user) are available, but they are not labeled as spam. Domain adaptation methods can benefit from such unlabeled data, by comparing its distribution (patterns) with the labeled source domain data.
- **Semi-supervised**: Most data that is available from the target domain is unlabelled, but some labeled data is also available. In the above-mentioned case of spam [filter design](https://en.wikipedia.org/wiki/Filter_design), this corresponds to the case that the target user has labeled some emails as being spam or not.
- **Supervised**: All data that is available from the target domain is labeled. In this case, domain adaptation reduces to refinement of the source domain predictor. In the above-mentioned example classification of hair-color from images, this could correspond to the refinement of a network already trained on a large dataset of labeled images from Italy, using newly available labeled images from Norway.

## Formalization

Let $X$ be the input space (or description space) and let $Y$ be the output space (or label space). The objective of a machine learning algorithm is to learn a [mathematical model](https://en.wikipedia.org/wiki/Mathematical_model) (a hypothesis) $h:X\to Y$ able to attach a label from $Y$ to an example from $X$. This model is learned from a learning sample $S=\{(x_{i},y_{i})\in (X\times Y)\}_{i=1}^{m}$.

Usually in [supervised learning](https://en.wikipedia.org/wiki/Supervised_learning) (without domain adaptation), we suppose that the examples $(x_{i},y_{i})\in S$ are drawn i.i.d. from a distribution $D_{S}$ of support $X\times Y$ (unknown and fixed). The objective is then to learn $h$ (from $S$) such that it commits the least error possible for labelling new examples coming from the distribution $D_{S}$.

The main difference between supervised learning and domain adaptation is that in the latter situation we study two different (but related) distributions $D_{S}$ and $D_{T}$ on $X\times Y$<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>. The domain adaptation task then consists of the transfer of knowledge from the source domain $D_{S}$ to the target one $D_{T}$. The goal is then to learn $h$ (from labeled or unlabelled samples coming from the two domains) such that it commits as little error as possible on the target domain $D_{T}$<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>.

The major issue is the following: if a model is learned from a source domain, what is its capacity to correctly label data coming from the target domain?

## Four algorithmic principles

### Reweighting algorithms

The objective is to reweight the source labeled sample such that it "looks like" the target sample (in terms of the error measure considered).

### Iterative algorithms

A method for adapting consists in iteratively "auto-labeling" the target examples. The principle is simple:

1.  a model $h$ is learned from the labeled examples;
2.  $h$ automatically labels some target examples;
3.  a new model is learned from the new labeled examples.

Note that there exist other iterative approaches, but they usually need target labeled examples.

### Search of a common representation space

The goal is to find or construct a common representation space for the two domains. The objective is to obtain a space in which the domains are close to each other while keeping good performances on the source labeling task. This can be achieved through the use of [Adversarial machine learning](https://en.wikipedia.org/wiki/Adversarial_machine_learning) techniques where feature representations from samples in different domains are encouraged to be indistinguishable.

### Hierarchical Bayesian Model

The goal is to construct a [Bayesian hierarchical model](https://en.wikipedia.org/wiki/Bayesian_hierarchical_model) $p(n)$, which is essentially a factorization model for counts $n$, to derive domain-dependent latent representations allowing both domain-specific and globally shared latent factors.

## Software packages

Several compilations of domain adaptation and transfer learning algorithms have been implemented over the past decades:

- SKADA (Python)
- ADAPT (Python)
- TLlib  (Python)
- Domain-Adaptation-Toolbox  ([MATLAB](https://en.wikipedia.org/wiki/MATLAB))

## References

1.  Crammer, Koby; Kearns, Michael; Wortman, Jeniifer (2008). ["Learning from Multiple Sources"](http://www.jmlr.org/papers/volume9/crammer08a/crammer08a.pdf) (PDF). *Journal of Machine Learning Research*. **9**: 1757–1774.
2.  Pan, Sinno Jialin; Yang, Qiang (2010). "A Survey on Transfer Learning". *IEEE Transactions on Knowledge and Data Engineering*. **22** (10): 1345–1359. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/TKDE.2009.191](https://doi.org/10.1109%2FTKDE.2009.191).
3.  Kouw, Wouter M.; Loog, Marco (2019-01-14), *An introduction to domain adaptation and transfer learning*, [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1812.11806](https://arxiv.org/abs/1812.11806)
4.  Farahani, Abolfazl; Voghoei, Sahar; Rasheed, Khaled; Arabnia, Hamid R. (2020-10-07), *A Brief Review of Domain Adaptation*, [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2010.03978](https://arxiv.org/abs/2010.03978)
5.  Stanford Online (2023-04-11). [Stanford CS330 Deep Multi-Task & Meta Learning - Domain Adaptation l 2022 I Lecture 13](https://www.youtube.com/watch?v=Uk6MU_PLDMs). Retrieved 2024-12-23 – via YouTube.
6.  Farahani, Abolfazl; Voghoei, Sahar; Rasheed, Khaled; Arabnia, Hamid R. (2020-10-07), *A Brief Review of Domain Adaptation*, [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2010.03978](https://arxiv.org/abs/2010.03978)
7.  Huang, Jiayuan; Smola, Alexander J.; Gretton, Arthur; Borgwardt, Karster M.; Schölkopf, Bernhard (2006). ["Correcting Sample Selection Bias by Unlabeled Data"](http://papers.nips.cc/paper/3075-correcting-sample-selection-bias-by-unlabeled-data.pdf) (PDF). *Conference on Neural Information Processing Systems (NIPS)*. pp. 601–608.
8.  Shimodaira, Hidetoshi (2000). ["Improving predictive inference under covariate shift by weighting the log-likelihood function"](https://www.researchgate.net/publication/230710850). *Journal of Statistical Planning and Inference*. **90** (2): 227–244. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/S0378-3758(00)00115-4](https://doi.org/10.1016%2FS0378-3758%2800%2900115-4). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [9238949](https://api.semanticscholar.org/CorpusID:9238949).
9.  Gallego, A.J.; Calvo-Zaragoza, J.; Fisher, R.B. (2020). ["Incremental Unsupervised Domain-Adversarial Training of Neural Networks"](https://www.pure.ed.ac.uk/ws/files/172035660/Incremental_Unsupervised_GALLEGO_DOA18092020_AFV.pdf) (PDF). *IEEE Transactions on Neural Networks and Learning Systems*. **PP** (11): 4864–4878. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2001.04129](https://arxiv.org/abs/2001.04129). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/TNNLS.2020.3025954](https://doi.org/10.1109%2FTNNLS.2020.3025954). [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[20.500.11820/72ba0443-8a7d-4cdd-8212-38682d4f0730](https://hdl.handle.net/20.500.11820%2F72ba0443-8a7d-4cdd-8212-38682d4f0730). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [33027004](https://pubmed.ncbi.nlm.nih.gov/33027004). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [210164756](https://api.semanticscholar.org/CorpusID:210164756).
10. Arief-Ang, I.B.; Salim, F.D.; Hamilton, M. (2017-11-08). [DA-HOC: semi-supervised domain adaptation for room occupancy prediction using CO2 sensor data](https://dl.acm.org/citation.cfm?id=3137146). 4th ACM International Conference on Systems for Energy-Efficient Built Environments (BuildSys). Delft, Netherlands. pp. 1–10. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1145/3137133.3137146](https://doi.org/10.1145%2F3137133.3137146). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4503-5544-5](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4503-5544-5).
11. Arief-Ang, I.B.; Hamilton, M.; Salim, F.D. (2018-12-01). "A Scalable Room Occupancy Prediction with Transferable Time Series Decomposition of CO2 Sensor Data". *ACM Transactions on Sensor Networks*. **14** (3–4): 21:1–21:28. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1145/3217214](https://doi.org/10.1145%2F3217214). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [54066723](https://api.semanticscholar.org/CorpusID:54066723).
12. Ganin, Yaroslav; Ustinova, Evgeniya; Ajakan, Hana; Germain, Pascal; Larochelle, Hugo; Laviolette, François; Marchand, Mario; Lempitsky, Victor (2016). ["Domain-Adversarial Training of Neural Networks"](http://jmlr.org/papers/volume17/15-239/15-239.pdf) (PDF). *Journal of Machine Learning Research*. **17**: 1–35.
13. Hajiramezanali, Ehsan; Siamak Zamani Dadaneh; Karbalayghareh, Alireza; Zhou, Mingyuan; Qian, Xiaoning (2017). "Addressing Appearance Change in Outdoor Robotics with Adversarial Domain Adaptation". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1703.01461](https://arxiv.org/abs/1703.01461) \[[cs.RO](https://arxiv.org/archive/cs.RO)\].
14. Hajiramezanali, Ehsan; Siamak Zamani Dadaneh; Karbalayghareh, Alireza; Zhou, Mingyuan; Qian, Xiaoning (2018). "Bayesian multi-domain learning for cancer subtype discovery from next-generation sequencing count data". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1810.09433](https://arxiv.org/abs/1810.09433) \[[stat.ML](https://arxiv.org/archive/stat.ML)\].
15. Gnassounou, Théo and Kachaiev, Oleksii and Flamary, Rémi and Collas, Antoine and Lalou, Yanis and de Mathelin, Antoine and Gramfort, Alexandre and Bueno, Ruben and Michel, Florent and Mellot, Apolline and Loison, Virginie and Odonnat, Ambroise and Moreau, Thomas (2024) ["SKADA : Scikit Adaptation"](https://github.com/scikit-adaptation/skada)
16. de Mathelin, Antoine and Deheeger, François and Richard, Guillaume and Mougeot, Mathilde and Vayatis, Nicolas (2020) ["ADAPT: Awesome Domain Adaptation Python Toolbox"](https://github.com/adapt-python/adapt)
17. Mingsheng Long Junguang Jiang, Bo Fu. (2020) ["Transfer-learning-library"](https://github.com/thuml/Transfer-Learning-Library)
18. Ke Yan. (2016) ["Domain adaptation toolbox"](https://github.com/viggin/domain-adaptation-toolbox)
