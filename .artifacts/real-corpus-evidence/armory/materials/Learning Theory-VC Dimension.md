[[learning-theory.base]]

> Source: [Vapnik–Chervonenkis dimension](https://en.wikipedia.org/wiki/Vapnik%E2%80%93Chervonenkis_dimension)
> License: Wikipedia content is available under CC BY-SA 4.0.

In [Vapnik–Chervonenkis theory](https://en.wikipedia.org/wiki/Vapnik%E2%80%93Chervonenkis_theory), the **Vapnik–Chervonenkis (VC) dimension** is a measure of the size (capacity, complexity, expressive power, richness, or flexibility) of a class of sets. The notion can be extended to classes of binary functions. It is defined as the [cardinality](https://en.wikipedia.org/wiki/Cardinality) of the largest set of points that the function class can [shatter](https://en.wikipedia.org/wiki/Shattering_(machine_learning))—that is, for which all possible binary labelings can be realized by some function in the class. It was originally defined by [Vladimir Vapnik](https://en.wikipedia.org/wiki/Vladimir_Vapnik) and [Alexey Chervonenkis](https://en.wikipedia.org/wiki/Alexey_Chervonenkis).

Informally, the capacity of a classification model is related to how complicated it can be. For example, consider the [thresholding](https://en.wikipedia.org/wiki/Heaviside_step_function) of a high-[degree](https://en.wikipedia.org/wiki/Degree_of_a_polynomial) [polynomial](https://en.wikipedia.org/wiki/Polynomial): if the polynomial evaluates above zero, that point is classified as positive, otherwise as negative. A high-degree polynomial can be wiggly, so that it can fit a given set of training points well. Such a polynomial has a high capacity. A much simpler alternative is to threshold a linear function. This function may not fit the training set well, because it has a low capacity. This notion of capacity is made rigorous below.

## Definitions

### VC dimension of a set-family

Let ${\mathcal {C}}=\{C\}_{C\in {\mathcal {C}}}$ be a [family of sets](https://en.wikipedia.org/wiki/Set_family) (also called set family, collection of sets or set of sets) and $X$ a set. Their *intersection* is defined as the following set family:

${\mathcal {C}}\cap X:=\{C\cap X\mid C\in {\mathcal {C}}\}.$

Here typically $X$ and each $C\in {\mathcal {C}}$ are subsets of a big "universe" of possibilities $U$ where intersection takes place.

We say that a set $X$ is *[shattered](https://en.wikipedia.org/wiki/Shattered_set)* by ${\mathcal {C}}$ if ${\mathcal {P}}(X)={\mathcal {C}}\cap X$ i.e. the set of intersections contains (hence is equal to) all the subsets of $X$. For finite sets $X$ this is equivalent to

$|{\mathcal {C}}\cap X|=2^{|X|}.$

The *VC dimension* $D$ of ${\mathcal {C}}$ is the [cardinality](https://en.wikipedia.org/wiki/Cardinality) of the largest set that is shattered by ${\mathcal {C}}$. If arbitrarily large sets can be shattered, the VC dimension of ${\mathcal {C}}$ is $\infty$.

### VC dimension of a classification model

A [binary classification](https://en.wikipedia.org/wiki/Binary_classification) model $f$ with some parameter vector $\theta$ is said to *[shatter](https://en.wikipedia.org/wiki/Shattered_set)* a set of [generally positioned](https://en.wikipedia.org/wiki/General_position) data points $(x_{1},x_{2},\ldots ,x_{n})$ if, for every assignment of labels to those points, there exists a $\theta$ such that the model $f$ makes no errors when evaluating that set of data points<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>.

The VC dimension of a model $f$ is the maximum number of points that can be arranged so that $f$ shatters them. More formally, it is the maximum cardinal $D$ such that there exists a generally positioned data point set of [cardinality](https://en.wikipedia.org/wiki/Cardinality) $D$ that can be shattered by $f$.

## Examples

1.  $f$ is a constant classifier (with no parameters); Its VC dimension is 0 since it cannot shatter even a single point. In general, the VC dimension of a finite classification model, which can return at most $2^{d}$ different classifiers, is at most $d$ (this is an upper bound on the VC dimension; the [Sauer–Shelah lemma](https://en.wikipedia.org/wiki/Sauer%E2%80%93Shelah_lemma) gives a lower bound on the dimension).
2.  $f$ is a single-parametric threshold classifier on real numbers; i.e., for a certain threshold $\theta$, the classifier $f_{\theta }$ returns 1 if the input number is larger than $\theta$ and 0 otherwise. The VC dimension of $f$ is 1 because: (a) It can shatter a single point. For every point $x$, a classifier $f_{\theta }$ labels it as 0 if $\theta >x$ and labels it as 1 if $\theta <x$. (b) It cannot shatter all the sets with two points. For every set of two numbers, if the smaller is labeled 1, then the larger must also be labeled 1, so not all labelings are possible.
3.  $f$ is a single-parametric interval classifier on real numbers; i.e., for a certain parameter $\theta$, the classifier $f_{\theta }$ returns 1 if the input number is in the interval $[\theta ,\theta +4]$ and 0 otherwise. The VC dimension of $f$ is 2 because: (a) It can shatter some sets of two points. E.g., for every set $\{x,x+2\}$, a classifier $f_{\theta }$ labels it as (0,0) if $\theta <x-4$ or if $\theta >x+2$, as (1,0) if $\theta \in [x-4,x-2)$, as (1,1) if $\theta \in [x-2,x]$, and as (0,1) if $\theta \in (x,x+2]$. (b) It cannot shatter any set of three points. For every set of three numbers, if the smallest and the largest are labeled 1, then the middle one must also be labeled 1, so not all labelings are possible.
4.  $f$ is a [straight line](https://en.wikipedia.org/wiki/Linear_classifier) as a classification model on points in a two-dimensional plane (this is the model used by a [perceptron](https://en.wikipedia.org/wiki/Perceptron)). The line should separate positive data points from negative data points. There exist sets of 3 points that can indeed be shattered using this model (any 3 points that are not collinear can be shattered). However, no set of 4 points can be shattered: by [Radon's theorem](https://en.wikipedia.org/wiki/Radon%27s_theorem), any four points can be partitioned into two subsets with intersecting [convex hulls](https://en.wikipedia.org/wiki/Convex_hull), so it is not possible to separate one of these two subsets from the other. Thus, the VC dimension of this particular classifier is 3. It is important to remember that while one can choose any arrangement of points, the arrangement of those points cannot change when attempting to shatter for some label assignment. Note, only 3 of the 2<sup>3</sup> = 8 possible label assignments are shown for the three points.
5.  $f$ is a single-parametric [sine](https://en.wikipedia.org/wiki/Sine) classifier, i.e., for a certain parameter $\theta$, the classifier $f_{\theta }$ returns 1 if the input number $x$ has $\sin(\theta x)>0$ and 0 otherwise. The VC dimension of $f$ is infinite, since it can shatter any finite subset of the set $\{2^{-m}\mid m\in \mathbb {N} \}$.

<table data-border="0" data-cellpadding="4" data-cellspacing="0">

![[media/ff1290231e560d67db03456007f261b2f50db443.png]]
![[media/8188bba7a773756eb255931973ba8ac24e156c34.png]]
![[media/57c9d0d8b11bd37f8bc44ce8a47826094ee60fcb.png]]
![[media/db3cbd11863d91607d69264c490c245b001aaf64.png]]

3 points shattered
4 points impossible

</table>

## Uses

### In statistical learning theory

The VC dimension can predict a [probabilistic](https://en.wikipedia.org/wiki/Probabilistic) [upper bound](https://en.wikipedia.org/wiki/Upper_bound) on the test error of a classification model. Vapnik proved that the probability of the test error (i.e., risk with 0–1 [loss function](https://en.wikipedia.org/wiki/Loss_function)) distancing from an upper bound (on data that is drawn [i.i.d.](https://en.wikipedia.org/wiki/Independent_identically-distributed_random_variables) from the same distribution as the training set) is given by:

$\Pr \left({\text{test error}}\leqslant {\text{training error}}+{\sqrt {{\frac {1}{N}}\left[D\left(\log \left({\tfrac {2N}{D}}\right)+1\right)-\log \left({\tfrac {\eta }{4}}\right)\right]}}\,\right)=1-\eta ,$

where $D$ is the VC dimension of the classification model, $0<\eta \leqslant 1$, and $N$ is the size of the training set (restriction: this formula is valid when $D\ll N$. When $D$ is larger, the test-error may be much higher than the training-error. This is due to [overfitting](https://en.wikipedia.org/wiki/Overfitting)).

The VC dimension also appears in [sample-complexity bounds](https://en.wikipedia.org/wiki/Sample-complexity_bounds). A space of binary functions with VC dimension $D$ can be learned with:

$N=\Theta \left({\frac {D+\ln {1 \over \delta }}{\varepsilon ^{2}}}\right)$

samples, where $\varepsilon$ is the learning error and $\delta$ is the failure probability. Thus, the sample-complexity is a linear function of the VC dimension of the hypothesis space.

### In [computational geometry](https://en.wikipedia.org/wiki/Computational_geometry)

The VC dimension is one of the critical parameters in the size of [ε-nets](https://en.wikipedia.org/wiki/E-net_(computational_geometry)), which determines the complexity of approximation algorithms based on them; range sets without finite VC dimension may not have finite ε-nets at all.

## Bounds

1.  
2.  The VC dimension of the dual set-family of ${\mathcal {C}}$ is strictly less than $2^{\operatorname {vc} ({\mathcal {C}})+1}$, and this is best possible.
3.  The VC dimension of a finite set-family ${\mathcal {C}}$ is at most $\log _{2}|{\mathcal {C}}|$. This is because $|{\mathcal {C}}\cap X|\leq |X|$ by definition.
4.  Given a set-family ${\mathcal {C}}$, define ${\mathcal {C}}_{s}$ as a set-family that contains all intersections of $s$ elements of ${\mathcal {C}}$. Then: 

$$
\operatorname {VCDim} ({\mathcal {C}}_{s})\leq \operatorname {VCDim} ({\mathcal {C}})\cdot (2s\log _{2}(3s))
$$

5.  Given a set-family ${\mathcal {C}}$ and an element $C_{0}\in {\mathcal {C}}$, define ${\mathcal {C}}\,\Delta C_{0}:=\{C\,\Delta C_{0}\mid C\in H\}$ where $\Delta$ denotes [symmetric set difference](https://en.wikipedia.org/wiki/Symmetric_set_difference). Then: 

$$
\operatorname {VCDim} ({\mathcal {C}}\,\Delta C_{0})=\operatorname {VCDim} ({\mathcal {C}})
$$

## Examples of VC Classes

### VC dimension of a finite projective plane

A [finite projective plane](https://en.wikipedia.org/wiki/Finite_projective_plane) of order *n* is a collection of *n*<sup>2</sup> + *n* + 1 sets (called "lines") over *n*<sup>2</sup> + *n* + 1 elements (called "points"), for which:

- Each line contains exactly *n* + 1 points.
- Each line intersects every other line in exactly one point.
- Each point is contained in exactly *n* + 1 lines.
- Each point is in exactly one line in common with every other point.
- At least four points do not lie in a common line.

The VC dimension of a finite projective plane is 2.

*Proof*: (a) For each pair of distinct points, there is one line that contains both of them, lines that contain only one of them, and lines that contain none of them, so every set of size 2 is shattered. (b) For any triple of three distinct points, if there is a line *x* that contain all three, then there is no line *y* that contains exactly two (since then *x* and *y* would intersect in two points, which is contrary to the definition of a projective plane). Hence, no set of size 3 is shattered.

### VC dimension of a boosting classifier

Suppose we have a base class $B$ of simple classifiers, whose VC dimension is $D$.

We can construct a more powerful classifier by combining several different classifiers from $B$; this technique is called [boosting](https://en.wikipedia.org/wiki/Boosting_(machine_learning) "Boosting (machine learning)"). Formally, given $T$ classifiers $h_{1},\ldots ,h_{T}\in B$ and a weight vector $w\in \mathbb {R} ^{T}$, we can define the following classifier:

$f(x)=\operatorname {sign} \left(\sum _{t=1}^{T}w_{t}\cdot h_{t}(x)\right)$

The VC dimension of the set of all such classifiers (for all selections of $T$ classifiers from $B$ and a weight-vector from $\mathbb {R} ^{T}$), assuming $T,D\geq 3$, is at most:

$T\cdot (D+1)\cdot (3\log(T\cdot (D+1))+2)$

### VC dimension of a neural network

A [neural network](https://en.wikipedia.org/wiki/Neural_network) is described by a [directed acyclic graph](https://en.wikipedia.org/wiki/Directed_acyclic_graph) *G*(*V*,*E*), where:

- *V* is the set of nodes. Each node is a simple computation cell.
- *E* is the set of edges, Each edge has a weight.
- The input to the network is represented by the sources of the graph – the nodes with no incoming edges.
- The output of the network is represented by the sinks of the graph – the nodes with no outgoing edges.
- Each intermediate node gets as input a weighted sum of the outputs of the nodes at its incoming edges, where the weights are the weights on the edges.
- Each intermediate node outputs a certain increasing function of its input, such as the [sign function](https://en.wikipedia.org/wiki/Sign_function) or the [sigmoid function](https://en.wikipedia.org/wiki/Sigmoid_function). This function is called the *activation function*.

The VC dimension of a neural network is bounded as follows:

- If the [activation function](https://en.wikipedia.org/wiki/Activation_function) is the sign function and the weights are general, then the VC dimension is at most $O(|E|\cdot \log(|E|))$.
- If the activation function is the sigmoid function and the weights are general, then the VC dimension is at least $\Omega (|E|^{2})$ and at most $O(|E|^{2}\cdot |V|^{2})$.
- If the weights come from a finite family (e.g. the weights are real numbers that can be represented by at most 32 bits in a computer), then, for both activation functions, the VC dimension is at most $O(|E|)$.

## Generalizations

The VC dimension is defined for spaces of binary functions (functions to {0,1}). Several generalizations have been suggested for spaces of non-binary functions.

- For real-valued functions (e.g., functions to a real interval, \[0,1\]), the Graph dimension  or Pollard's pseudo-dimension can be used.
- The [[Rademacher Complexity]] provides similar bounds to the VC, and can sometimes provide more insight than VC dimension calculations into such statistical methods such as those using [kernels](https://en.wikipedia.org/wiki/Kernel_methods)<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>.
- The Memory Capacity (sometimes Memory Equivalent Capacity) gives a lower bound capacity, rather than an upper bound (see for example: [Artificial neural network#Capacity](https://en.wikipedia.org/wiki/Artificial_neural_network#Capacity)) and therefore indicates the point of potential overfitting.

## See also

- [Growth function](https://en.wikipedia.org/wiki/Growth_function)
- [Sauer–Shelah lemma](https://en.wikipedia.org/wiki/Sauer%E2%80%93Shelah_lemma), a bound on the number of sets in a set system in terms of the VC dimension.

## Footnotes

1.  Vapnik, V. N.; Chervonenkis, A. Ya. (1971). "On the Uniform Convergence of Relative Frequencies of Events to Their Probabilities". *Theory of Probability & Its Applications*. **16** (2): 264. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/1116025](https://doi.org/10.1137%2F1116025). This is an English translation, by B. Seckler, of the Russian paper: "On the Uniform Convergence of Relative Frequencies of Events to Their Probabilities". *Dokl. Akad. Nauk*. **181** (4): 781. 1968. The translation was reproduced as: Vapnik, V. N.; Chervonenkis, A. Ya. (2015). "On the Uniform Convergence of Relative Frequencies of Events to Their Probabilities". *Measures of Complexity*. p. 11. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-3-319-21852-6_3](https://doi.org/10.1007%2F978-3-319-21852-6_3). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-319-21851-9](https://en.wikipedia.org/wiki/Special:BookSources/978-3-319-21851-9).
2.  ^     [Mohri, Mehryar](https://en.wikipedia.org/wiki/Mehryar_Mohri); Rostamizadeh, Afshin; Talwalkar, Ameet (2012). *Foundations of Machine Learning*. US, Massachusetts: MIT Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780262018258](https://en.wikipedia.org/wiki/Special:BookSources/9780262018258).
3.  .
4.  ^    Shalev-Shwartz, Shai; Ben-David, Shai (2014). *Understanding Machine Learning – from Theory to Algorithms*. Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9781107057135](https://en.wikipedia.org/wiki/Special:BookSources/9781107057135).
5.  Alon, N.; Haussler, D.; Welzl, E. (1987). "Partitioning and geometric embedding of range spaces of finite Vapnik-Chervonenkis dimension". *Proceedings of the third annual symposium on Computational geometry – SCG '87*. p. 331. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1145/41958.41994](https://doi.org/10.1145%2F41958.41994). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0897912310](https://en.wikipedia.org/wiki/Special:BookSources/978-0897912310). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [7394360](https://api.semanticscholar.org/CorpusID:7394360).
6.  ^   .
7.  .
8.  .
9.  .
10. .
11. .

## References

- Moore, Andrew. ["VC dimension tutorial"](https://autonlab.org/assets/tutorials/vcdim08.pdf) (PDF).
- Vapnik, Vladimir (2000). *The nature of statistical learning theory*. Springer.
- Blumer, A.; Ehrenfeucht, A.; Haussler, D.; [Warmuth, M. K.](https://en.wikipedia.org/wiki/Manfred_K._Warmuth) (1989). ["Learnability and the Vapnik–Chervonenkis dimension"](http://l2r.cs.uiuc.edu/~danr/Teaching/CS446-16/Papers/p929-blumer.pdf) (PDF). *Journal of the ACM*. **36** (4): 929–865. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1145/76359.76371](https://doi.org/10.1145%2F76359.76371). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [1138467](https://api.semanticscholar.org/CorpusID:1138467).
- Burges, Christopher. ["Tutorial on SVMs for Pattern Recognition"](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/svmtutorial.pdf) (PDF). *[Microsoft](https://en.wikipedia.org/wiki/Microsoft)*. (containing information also for VC dimension)
- [Chazelle, Bernard](https://en.wikipedia.org/wiki/Bernard_Chazelle). ["The Discrepancy Method"](http://www.cs.princeton.edu/~chazelle/book.html).
- Natarajan, B.K. (1989). ["On Learning sets and functions"](https://doi.org/10.1007%2FBF00114804). *Machine Learning*. **4**: 67–97. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/BF00114804](https://doi.org/10.1007%2FBF00114804).
- Ben-David, Shai; Cesa-Bianchi, Nicolò; Long, Philip M. (1992). "Characterizations of learnability for classes of {O, …, *n*}-valued functions". *Proceedings of the fifth annual workshop on Computational learning theory – COLT '92*. p. 333. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1145/130385.130423](https://doi.org/10.1145%2F130385.130423). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [089791497X](https://en.wikipedia.org/wiki/Special:BookSources/089791497X).
- Brukhim, Nataly; Carmon, Daniel; Dinur, Irit; Moran, Shay; Yehudayoff, Amir (2022). "A Characterization of Multiclass Learnability". *2022 IEEE 63rd Annual Symposium on Foundations of Computer Science (FOCS)*. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2203.01550](https://arxiv.org/abs/2203.01550).
- Pollard, D. (1984). *Convergence of Stochastic Processes*. Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9781461252542](https://en.wikipedia.org/wiki/Special:BookSources/9781461252542).
- Anthony, Martin; Bartlett, Peter L. (2009). *Neural Network Learning: Theoretical Foundations*. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780521118620](https://en.wikipedia.org/wiki/Special:BookSources/9780521118620).
- [Morgenstern, Jamie H.](https://en.wikipedia.org/wiki/Jamie_Morgenstern); Roughgarden, Tim (2015). [On the Pseudo-Dimension of Nearly Optimal Auctions](http://papers.nips.cc/paper/5766-on-the-pseudo-dimension-of-nearly-optimal-auctions). NIPS. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1506.03684](https://arxiv.org/abs/1506.03684). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2015arXiv150603684M](https://ui.adsabs.harvard.edu/abs/2015arXiv150603684M).
- Karpinski, Marek; Macintyre, Angus (February 1997). ["Polynomial Bounds for VC Dimension of Sigmoidal and General Pfaffian Neural Networks"](https://ora.ox.ac.uk/objects/uuid:a14465ce-11d9-4f89-aeec-fcf0bea603ed). *Journal of Computer and System Sciences*. **54** (1): 169–176. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1006/jcss.1997.1477](https://doi.org/10.1006%2Fjcss.1997.1477).
