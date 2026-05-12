[[learning-theory.base]]

> Source: [[Rademacher Complexity]]
> License: Wikipedia content is available under CC BY-SA 4.0.

In [computational learning theory](https://en.wikipedia.org/wiki/Computational_learning_theory) ([machine learning](https://en.wikipedia.org/wiki/Machine_learning) and [theory of computation](https://en.wikipedia.org/wiki/Theory_of_computation)), **Rademacher complexity**, named after [Hans Rademacher](https://en.wikipedia.org/wiki/Hans_Rademacher), measures richness of a class of sets with respect to a [probability distribution](https://en.wikipedia.org/wiki/Probability_distribution). The concept can also be extended to real valued functions.

## Definitions

### Rademacher complexity of a set

Given a set $A\subseteq \mathbb {R} ^{m}$, the **Rademacher complexity of** *A* is defined as follows:

$\operatorname {Rad} (A):={\frac {1}{m}}\mathbb {E} _{\sigma }\left[\sup _{a\in A}\sum _{i=1}^{m}\sigma _{i}a_{i}\right]$

where $\sigma _{1},\sigma _{2},\dots ,\sigma _{m}$ are [independent random variables](https://en.wikipedia.org/wiki/Independence_(probability_theory) "Independence (probability theory)") drawn from the [Rademacher distribution](https://en.wikipedia.org/wiki/Rademacher_distribution) i.e. $\Pr(\sigma _{i}=+1)=\Pr(\sigma _{i}=-1)=1/2$ for $i\in \{1,2,\dots ,m\}$, and $a=(a_{1},\ldots ,a_{m})\in A$. Some authors take the absolute value of the sum before taking the supremum, but if $A$ is [symmetric](https://en.wikipedia.org/wiki/Symmetric_set) this makes no difference.

### Rademacher complexity of a function class

Let $S=\{z_{1},z_{2},\dots ,z_{m}\}\subseteq Z$ be a sample of points and consider a function class ${\mathcal {F}}$ of real-valued functions over $Z$. Then, the **empirical Rademacher complexity** of ${\mathcal {F}}$ given $S$ is defined as:

$\operatorname {Rad} _{S}({\mathcal {F}})={\frac {1}{m}}\mathbb {E} _{\sigma }\left[\sup _{f\in {\mathcal {F}}}\left|\sum _{i=1}^{m}\sigma _{i}f(z_{i})\right|\right]$

This can also be written using the previous definition:

$\operatorname {Rad} _{S}({\mathcal {F}})=\operatorname {Rad} ({\mathcal {F}}\circ S)$

where ${\mathcal {F}}\circ S$ denotes [function composition](https://en.wikipedia.org/wiki/Function_composition), i.e.:

${\mathcal {F}}\circ S:=\{(f(z_{1}),\ldots ,f(z_{m}))\mid f\in {\mathcal {F}}\}$

The **worst case empirical Rademacher complexity** is

$$
{\overline {\operatorname {Rad} }}_{m}({\mathcal {F}})=\sup _{S=\{z_{1},\dots ,z_{m}\}}\operatorname {Rad} _{S}({\mathcal {F}})
$$

Let $P$ be a probability distribution over $Z$. The **Rademacher complexity** of the function class ${\mathcal {F}}$ with respect to $P$ for sample size $m$ is:

$\operatorname {Rad} _{P,m}({\mathcal {F}}):=\mathbb {E} _{S\sim P^{m}}\left[\operatorname {Rad} _{S}({\mathcal {F}})\right]$

where the above expectation is taken over an [identically independently distributed](https://en.wikipedia.org/wiki/Identically_independently_distributed) (i.i.d.) sample $S=(z_{1},z_{2},\dots ,z_{m})$ generated according to $P$.

## Intuition

The Rademacher complexity is typically applied on a function class of models that are used for classification, with the goal of measuring their ability to classify points drawn from a [probability space](https://en.wikipedia.org/wiki/Probability_space) under arbitrary labellings. When the function class is rich enough, it contains functions that can appropriately adapt for each arrangement of labels, simulated by the random draw of $\sigma _{i}$ under the expectation, so that this quantity in the sum is maximized.

The Rademacher complexity of a set $A$ can be rewritten as

$$
\operatorname {Rad} (A):={\frac {1}{m}}\mathbb {E} _{\sigma }\left[\sup _{a\in A}\sum _{i=1}^{m}\sigma _{i}a_{i}\right]={\frac {1}{{\sqrt {m}}2^{m}}}\sum _{\sigma \in \{-1/{\sqrt {m}},+1/{\sqrt {m}}\}^{m}}\left[\sup _{a\in A}\langle \sigma ,a\rangle \right].
$$

Each term in the summation is the farthest distance of the set $A$ from the origin, along a unit-length direction $\sigma$. The directions are along the vertices of a [hypercube](https://en.wikipedia.org/wiki/Hypercube). Thus, we can also write it as 

$$
\operatorname {Rad} (A)={\frac {1}{2{\sqrt {m}}}}{\frac {1}{2^{m-1}}}\sum _{\sigma \in \{-1/{\sqrt {m}},+1/{\sqrt {m}}\}^{m}/\{-1,+1\}}\left[\sup _{a\in A}\langle \sigma ,a\rangle -\inf _{a\in A}\langle \sigma ,a\rangle \right]
$$

Here, the set $\{-1/{\sqrt {m}},+1/{\sqrt {m}}\}^{m}/\{-1,+1\}$ denotes half of the vertices of a hypercube, selected so that each diagonal has exactly one vertex selected.

![[media/3d41927a45fa14ef037bd0ea6f6297ffe9f06226.png]]
Width, as illustrated by a [Reuleaux triangle](https://en.wikipedia.org/wiki/Reuleaux_triangle).

In words, this states that $2{\sqrt {m}}\operatorname {Rad} (A)$ is precisely the average width of the set $A$ along all diagonal directions of a hypercube.

## Examples

A singleton set has 0 width in any direction, so it has Rademacher complexity 0.

The set $A=\{(1,1),(1,2)\}\subseteq \mathbb {R} ^{2}$ has average width $1/{\sqrt {2}}$ along the two diagonal directions of the square, so it has Rademacher complexity $1/4$.

The unit cube $[0,1]^{m}$ has constant width ${\sqrt {m}}$ along the diagonal directions, so it has Rademacher complexity $1/2$. Similarly, the unit [cross-polytope](https://en.wikipedia.org/wiki/Cross-polytope) $\{x\in \mathbb {R} ^{m}:\|x\|_{1}\leq 1\}$ has constant width $2/{\sqrt {m}}$ along the diagonal directions, so it has Rademacher complexity $1/m$.

## Using the Rademacher complexity

The Rademacher complexity can be used to derive data-dependent upper-bounds on the [learnability](https://en.wikipedia.org/wiki/Learnability) of function classes. Intuitively, a function-class with smaller Rademacher complexity is easier to learn.

### Bounding the representativeness

In [machine learning](https://en.wikipedia.org/wiki/Machine_learning), it is desired to have a [training set](https://en.wikipedia.org/wiki/Training_set) that represents the true distribution of some sample data $S$. This can be quantified using the notion of **representativeness**. Denote by $P$ the [probability distribution](https://en.wikipedia.org/wiki/Probability_distribution) from which the samples are drawn. Denote by $H$ the set of hypotheses (potential classifiers) and denote by ${\mathcal {F}}$ the corresponding set of error functions, i.e., for every hypothesis $h\in H$, there is a function $f_{h}\in F$, that maps each training sample (features,label) to the error of the classifier $h$ (note in this case hypothesis and classifier are used interchangeably). For example, in the case that $h$ represents a binary classifier, the [error function](https://en.wikipedia.org/wiki/Error_function) is a 0–1 [loss function](https://en.wikipedia.org/wiki/Loss_function), i.e. the error function $f_{h}$ returns 0 if $h$ correctly classifies a sample and 1 else. We omit the index and write $f$ instead of $f_{h}$ when the underlying hypothesis is irrelevant. Define:

$L_{P}(f):=\mathbb {E} _{z\sim P}[f(z)]$ – the expected error of some error function $f\in {\mathcal {F}}$ on the real distribution $P$;

$L_{S}(f):={1 \over m}\sum _{i=1}^{m}f(z_{i})$ – the estimated error of some error function $f\in {\mathcal {F}}$ on the sample $S$.

The representativeness of the sample $S$, with respect to $P$ and ${\mathcal {F}}$, is defined as:

$\operatorname {Rep} _{P}({\mathcal {F}},S):=\sup _{f\in F}(L_{P}(f)-L_{S}(f))$

Smaller representativeness is better, since it provides a way to avoid [overfitting](https://en.wikipedia.org/wiki/Overfitting): it means that the true error of a classifier is not much higher than its estimated error, and so selecting a classifier that has low estimated error will ensure that the true error is also low. Note however that the concept of representativeness is relative and hence can not be compared across distinct samples.

The expected representativeness of a sample can be bounded above by the Rademacher complexity of the function class: If ${\mathcal {F}}$ is a set of functions with range within $[0,1]$, then

$$
\operatorname {Rad} _{P,m}({\mathcal {F}})-{\sqrt {\frac {\ln 2}{2m}}}\leq \mathbb {E} _{S\sim P^{m}}[\operatorname {Rep} _{P}({\mathcal {F}},S)]\leq 2\operatorname {Rad} _{P,m}({\mathcal {F}})
$$

Furthermore, the representativeness is [concentrated](https://en.wikipedia.org/wiki/Concentration_inequality) around its expectation: For any $\epsilon$, with probability $\geq 1-2e^{-2\epsilon ^{2}m}$,

$$
\operatorname {Rep} _{P}({\mathcal {F}},S)\in \mathbb {E} _{S\sim P^{m}}[\operatorname {Rep} _{P}({\mathcal {F}},S)]\pm \epsilon
$$

### Bounding the generalization error

The Rademacher complexity is a theoretical justification for [[Empirical Risk Minimization]].

When the error function is binary (0-1 loss), for every $\delta >0$,

$\sup _{f\in {\mathcal {F}}}(L_{P}(f)-L_{S}(f))\leq 2\operatorname {Rad} _{S}({\mathcal {F}})+4{\sqrt {2\ln(4/\delta ) \over m}}$

with probability at least $1-\delta$.

There exists a constant $c>0$, such that when the error function is squared $\ell ({\hat {y}},y):=({\hat {y}}-y)^{2}$, and the function class ${\mathcal {F}}$ consists of functions with range within $[-1,+1]$, then for any $\delta >0$

$$
L_{P}(f)-L_{S}(f)\leq c\left[L_{S}(f)+(\ln m)^{4}{\overline {\operatorname {Rad} }}_{m}({\mathcal {F}})^{2}+{\frac {\ln(1/\delta )}{m}}\right],\quad \forall f\in {\mathcal {F}}
$$

with probability at least $1-\delta$.

### Oracle inequalities

Let the [Bayes risk](https://en.wikipedia.org/wiki/Bayes_risk) $L^{*}=\inf _{f}L_{P}(f)$, where $f$ can be *any* [measurable function](https://en.wikipedia.org/wiki/Measurable_function).

Let the function class ${\mathcal {F}}$ be split into "complexity classes" ${\mathcal {F}}_{r}$, where $r\in \mathbb {R}$ are levels of complexity. Let $p_{r}$ be real numbers. Let the complexity measure function $p$ be defined such that $p(f):=\min\{p_{r}:f\in {\mathcal {F}}_{r}\}$.

For any dataset $S$, let ${\hat {f}}$ be a minimizer of $L_{S}(f)+p(f)$. If

$$
\sup _{f\in {\mathcal {F}}_{r}}|L_{P}(f)-L_{S}(f)|\leq p_{r},\quad \forall r
$$

then we have the oracle inequality

$$
L({\hat {f}})-L^{*}\leq \inf _{r}\left(\inf _{f\in {\mathcal {F}}_{r}}L(f)-L^{*}+2p_{r}\right)
$$

Define $f_{r}^{*}\in \arg \min _{f\in {\mathcal {F}}_{r}}L(f)$. If we further assume

$$
r\leq s{\text{ implies }}{\mathcal {F}}_{r}\subseteq {\mathcal {F}}_{s}{\text{ and }}p_{r}\leq p_{s}
$$

and 

$$
{\begin{aligned}\forall r,\sup _{f\in {\mathcal {F}}_{r}}\left(L_{P}(f)-L_{P}\left(f_{r}^{*}\right)-2\left(L_{S}(f)-L_{S}\left(f_{r}^{*}\right)\right)\right)&\leq 2p_{r}/7\\\sup _{f\in {\mathcal {F}}_{r}}\left(L_{S}(f)-L_{S}\left(f_{r}^{*}\right)-2\left(L_{P}(f)-L_{P}\left(f_{r}^{*}\right)\right)\right)&\leq 2p_{r}/7\end{aligned}}
$$

then we have the oracle inequality 

$$
L_{P}({\widehat {f}})-L^{*}\leq \inf _{r}\left(\inf _{f\in {\mathcal {F}}_{r}}L_{P}(f)-L^{*}+3p_{r}\right)
$$



## Bounding the Rademacher complexity

Since smaller Rademacher complexity is better, it is useful to have upper bounds on the Rademacher complexity of various function sets. The following rules can be used to upper-bound the Rademacher complexity of a set $A\subset \mathbb {R} ^{m}$.

- If all vectors in $A$ are translated by a constant vector $a_{0}\in \mathbb {R} ^{m}$, then Rad(*A*) does not change.
- If all vectors in $A$ are multiplied by a scalar $c\in \mathbb {R}$, then Rad(*A*) is multiplied by $|c|$.
- $\operatorname {Rad} (A+B)=\operatorname {Rad} (A)+\operatorname {Rad} (B)$.
- (Kakade & Tewari Lemma) If all vectors in $A$ are operated by a [Lipschitz function](https://en.wikipedia.org/wiki/Lipschitz_function), then Rad(*A*) is (at most) multiplied by the [Lipschitz constant](https://en.wikipedia.org/wiki/Lipschitz_constant) of the function. In particular, if all vectors in $A$ are operated by a [contraction mapping](https://en.wikipedia.org/wiki/Contraction_mapping), then Rad(*A*) strictly decreases.
- The Rademacher complexity of the [convex hull](https://en.wikipedia.org/wiki/Convex_hull) of $A$ equals Rad(*A*).
- (Massart Lemma) The Rademacher complexity of a [finite set](https://en.wikipedia.org/wiki/Finite_set) grows logarithmically with the set size. Formally, let $A$ be a set of $N$ vectors in $\mathbb {R} ^{m}$, and let ${\bar {a}}$ be the mean of the vectors in $A$. Then:

$\operatorname {Rad} (A)\leq \max _{a\in A}\|a-{\bar {a}}\|\cdot {{\sqrt {2\log N}} \over m}$

In particular, if $A$ is a set of binary vectors, the norm is at most ${\sqrt {m}}$, so:

$\operatorname {Rad} (A)\leq {\sqrt {2\log N \over m}}$

### Bounds related to the VC dimension

Let $H$ be a [set family](https://en.wikipedia.org/wiki/Set_family) whose [[VC Dimension]] is $d$. It is known that the [growth function](https://en.wikipedia.org/wiki/Growth_function) of $H$ is bounded as:

for all $m>d+1$: $\operatorname {Growth} (H,m)\leq (em/d)^{d}$

This means that, for every set $h$ with at most $m$ elements, $|H\cap h|\leq (em/d)^{d}$. The set-family $H\cap h$ can be considered as a set of binary vectors over $\mathbb {R} ^{m}$. Substituting this in Massart's lemma gives:

$\operatorname {Rad} (H\cap h)\leq {\sqrt {2d\log(em/d) \over m}}$

With more advanced techniques ([Dudley's entropy bound](https://en.wikipedia.org/wiki/Dudley%27s_theorem) and Haussler's upper bound) one can show, for example, that there exists a constant $C$, such that any class of $\{0,1\}$-indicator functions with [Vapnik–Chervonenkis dimension](https://en.wikipedia.org/wiki/Vapnik%E2%80%93Chervonenkis_dimension) $d$ has Rademacher complexity upper-bounded by $C{\sqrt {\frac {d}{m}}}$.

### Bounds related to linear classes

The following bounds are related to linear operations on $S$ – a constant set of $m$ vectors in $\mathbb {R} ^{n}$.

- Define $A_{2}=\{(w\cdot x_{1},\ldots ,w\cdot x_{m})\mid \|w\|_{2}\leq 1\}=$ the set of dot-products of the vectors in $S$ with vectors in the [unit ball](https://en.wikipedia.org/wiki/Unit_ball). Then:

$\operatorname {Rad} (A_{2})\leq {\max _{i}\|x_{i}\|_{2} \over {\sqrt {m}}}$

- Define $A_{1}=\{(w\cdot x_{1},\ldots ,w\cdot x_{m})\mid \|w\|_{1}\leq 1\}=$ the set of dot-products of the vectors in $S$ with vectors in the unit ball of the 1-norm. Then:

$\operatorname {Rad} (A_{1})\leq \max _{i}\|x_{i}\|_{\infty }\cdot {\sqrt {2\log(2n) \over m}}$

### Bounds related to covering numbers

The following bound relates the Rademacher complexity of a set $A$ to its external [covering number](https://en.wikipedia.org/wiki/Covering_number) – the number of balls of a given radius $r$ whose union contains $A$. The bound is attributed to Dudley.

Suppose $A\subset \mathbb {R} ^{m}$ is a set of vectors whose length (norm) is at most $c$. Then, for every integer $M>0$:

$\operatorname {Rad} (A)\leq {c\cdot 2^{-M} \over {\sqrt {m}}}+{6c \over m}\cdot \sum _{i=1}^{M}2^{-i}{\sqrt {\log \left(N_{c\cdot 2^{-i}}^{\text{ext}}(A)\right)}}$

In particular, if $A$ lies in a *d*-dimensional subspace of $\mathbb {R} ^{m}$, then:

$\forall r>0:N_{r}^{\text{ext}}(A)\leq (2c{\sqrt {d}}/r)^{d}$

Substituting this in the previous bound gives the following bound on the Rademacher complexity:

$\operatorname {Rad} (A)\leq {6c \over m}\cdot {\bigg (}{\sqrt {d\log(2{\sqrt {d}})}}+2{\sqrt {d}}{\bigg )}=O{\bigg (}{c{\sqrt {d\log(d)}} \over m}{\bigg )}$

## Gaussian complexity

**Gaussian complexity** is a similar complexity with similar physical meanings, and can be obtained from the Rademacher complexity using the random variables $g_{i}$ instead of $\sigma _{i}$, where $g_{i}$ are [Gaussian](https://en.wikipedia.org/wiki/Normal_distribution) [i.i.d.](https://en.wikipedia.org/wiki/Independent_and_identically_distributed_random_variables) random variables with zero-mean and variance 1, i.e. $g_{i}\sim {\mathcal {N}}(0,1)$. Gaussian and Rademacher complexities are known to be equivalent up to logarithmic factors.

### Equivalence of Rademacher and Gaussian complexity

Given a set $A\subseteq \mathbb {R} ^{n}$ then it holds that:  
${\frac {G(A)}{2{\sqrt {\log {n}}}}}\leq {\text{Rad}}(A)\leq {\sqrt {\frac {\pi }{2}}}G(A)$  
Where $G(A)$ is the Gaussian Complexity of A. As an example, consider the rademacher and gaussian complexities of the L1 ball. The Rademacher complexity is given by exactly 1, whereas the Gaussian complexity is on the order of ${\sqrt {\log d}}$ (which can be shown by applying known properties of suprema of a set of [subgaussian](https://en.wikipedia.org/wiki/Sub-Gaussian_distribution) random variables).

## References

1.  [Balcan, Maria-Florina](https://en.wikipedia.org/wiki/Maria-Florina_Balcan) (November 15–17, 2011). ["Machine Learning Theory – Rademacher Complexity"](https://www.cs.cmu.edu/~ninamf/ML11/lect1117.pdf) (PDF). Retrieved 10 December 2016.
2.  ^        Chapter 26 in Shalev-Shwartz, Shai; Ben-David, Shai (2014). *Understanding Machine Learning – from Theory to Algorithms*. Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9781107057135](https://en.wikipedia.org/wiki/Special:BookSources/9781107057135).
3.  ^   [Mohri, Mehryar](https://en.wikipedia.org/wiki/Mehryar_Mohri); Rostamizadeh, Afshin; Talwalkar, Ameet (2012). *Foundations of Machine Learning*. US, Massachusetts: MIT Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780262018258](https://en.wikipedia.org/wiki/Special:BookSources/9780262018258).
4.  ^     Bartlett, Peter L.; Montanari, Andrea; Rakhlin, Alexander (May 2021). ["Deep learning: a statistical viewpoint"](https://www.cambridge.org/core/journals/acta-numerica/article/deep-learning-a-statistical-viewpoint/7BCB89D860CEDDD5726088FAD64F2A5A). *Acta Numerica*. **30**: 87–201. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2103.09177](https://arxiv.org/abs/2103.09177). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1017/S0962492921000027](https://doi.org/10.1017%2FS0962492921000027). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0962-4929](https://search.worldcat.org/issn/0962-4929).
5.  Bousquet, O. (2004). Introduction to Statistical Learning Theory. *Biological Cybernetics*, *3176*(1), 169–\* [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-3-540-28650-9_8](https://doi.org/10.1007%2F978-3-540-28650-9_8)
6.  ^   Wainwright, Martin (2019). *High-dimensional statistics : a non-asymptotic viewpoint*. Cambridge, United Kingdom. pp. Exercise 5.5. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-108-62777-1](https://en.wikipedia.org/wiki/Special:BookSources/978-1-108-62777-1). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [1089254580](https://search.worldcat.org/oclc/1089254580).`{{`[`cite book`](https://en.wikipedia.org/wiki/Template:Cite_book)`}}`: CS1 maint: location missing publisher ([link](https://en.wikipedia.org/wiki/Category:CS1_maint:_location_missing_publisher))

- Peter L. Bartlett, Shahar Mendelson (2002) *Rademacher and Gaussian Complexities: Risk Bounds and Structural Results*. Journal of Machine Learning Research 3 463–482
- Giorgio Gnecco, Marcello Sanguineti (2008) *Approximation Error Bounds via Rademacher's Complexity*. Applied Mathematical Sciences, Vol. 2, 2008, no. 4, 153–176
