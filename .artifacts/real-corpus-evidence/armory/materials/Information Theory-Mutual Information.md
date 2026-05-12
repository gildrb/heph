[[information-theory.base]]

> Source: [[Mutual Information]]
> License: Wikipedia content is available under CC BY-SA 4.0.

![[media/44216235a7b36a15835f484726cc0a0755bb61f7.png]]
[Venn diagram](https://en.wikipedia.org/wiki/Venn_diagram) showing additive and subtractive relationships of various information measures associated with correlated variables $X$ and $Y$. The area contained by either circle is the [joint entropy](https://en.wikipedia.org/wiki/Joint_entropy) $\mathrm {H} (X,Y)$. The circle on the left (red and violet) is the [[Entropy|individual entropy]] $\mathrm {H} (X)$, with the red being the [conditional entropy](https://en.wikipedia.org/wiki/Conditional_entropy) $\mathrm {H} (X\mid Y)$. The circle on the right (blue and violet) is $\mathrm {H} (Y)$, with the blue being $\mathrm {H} (Y\mid X)$. The violet is the mutual information $\operatorname {I} (X;Y)$.

In [probability theory](https://en.wikipedia.org/wiki/Probability_theory) and [information theory](https://en.wikipedia.org/wiki/Information_theory), the **mutual information** (**MI**) of two [random variables](https://en.wikipedia.org/wiki/Random_variable) is a measure of the mutual [dependence](https://en.wikipedia.org/wiki/Statistical_dependence) between the two variables. More specifically, it quantifies the "[amount of information](https://en.wikipedia.org/wiki/Information_content)" (in [units](https://en.wikipedia.org/wiki/Units_of_information) such as [shannons](https://en.wikipedia.org/wiki/Shannon_(unit) "Shannon (unit)") ([bits](https://en.wikipedia.org/wiki/Bit)), [nats](https://en.wikipedia.org/wiki/Nat_(unit) "Nat (unit)") or [hartleys](https://en.wikipedia.org/wiki/Hartley_(unit) "Hartley (unit)")) obtained about one random variable by observing the other random variable. The concept of mutual information is intimately linked to that of [entropy](https://en.wikipedia.org/wiki/Entropy_(information_theory) "Entropy (information theory)") of a random variable, a fundamental notion in information theory that quantifies the expected "amount of information" held in a random variable.

Not limited to real-valued random variables and linear dependence like the [correlation coefficient](https://en.wikipedia.org/wiki/Pearson_correlation_coefficient), MI is more general and determines how different the [joint distribution](https://en.wikipedia.org/wiki/Joint_distribution) of the pair $(X,Y)$ is from the product of the marginal distributions of $X$ and $Y$. MI is the [expected value](https://en.wikipedia.org/wiki/Expected_value) of the [pointwise mutual information](https://en.wikipedia.org/wiki/Pointwise_mutual_information) (PMI).

The quantity was defined and analyzed by [Claude Shannon](https://en.wikipedia.org/wiki/Claude_Shannon) in his landmark paper "[A Mathematical Theory of Communication](https://en.wikipedia.org/wiki/A_Mathematical_Theory_of_Communication)", although he did not call it "mutual information". This term was coined later by [Robert Fano](https://en.wikipedia.org/wiki/Robert_Fano). Mutual Information is also known as [information gain](https://en.wikipedia.org/wiki/Information_gain).

## Definition

Let $(X,Y)$ be a pair of [random variables](https://en.wikipedia.org/wiki/Random_variable) with values over the space ${\mathcal {X}}\times {\mathcal {Y}}$. If their joint distribution is $P_{(X,Y)}$ and the marginal distributions are $P_{X}$ and $P_{Y}$, the mutual information is defined as

$I(X;Y)=D_{\mathrm {KL} }(P_{(X,Y)}\parallel P_{X}\otimes P_{Y})$

where $D_{\mathrm {KL} }$ is the [[Kullback-Leibler Divergence|Kullback–Leibler divergence]], and $P_{X}\otimes P_{Y}$ is the [outer product](https://en.wikipedia.org/wiki/Outer_product) distribution which assigns probability $P_{X}(x)\cdot P_{Y}(y)$ to each $(x,y)$.

Expressed in terms of the [entropy](https://en.wikipedia.org/wiki/Entropy_(information_theory) "Entropy (information theory)") $H(\cdot )$ and the [conditional entropy](https://en.wikipedia.org/wiki/Conditional_entropy) $H(\cdot |\cdot )$ of the random variables $X$ and $Y$, one also has (see [relation to conditional and joint entropy](#Relation_to_conditional_and_joint_entropy)):

$I(X;Y)=H(X)-H(X|Y)=H(Y)-H(Y|X)$

Notice, as per property of the [[Kullback-Leibler Divergence|Kullback–Leibler divergence]], that $I(X;Y)$ is equal to zero precisely when the joint distribution coincides with the product of the marginals, i.e. when $X$ and $Y$ are independent (and hence observing $Y$ tells you nothing about $X$). $I(X;Y)$ is non-negative. It is a measure of the price for encoding $(X,Y)$ as a pair of independent random variables when in reality they are not.

If the [natural logarithm](https://en.wikipedia.org/wiki/Natural_logarithm) is used, the unit of mutual information is the [nat](https://en.wikipedia.org/wiki/Nat_(unit) "Nat (unit)"). If the [log base](https://en.wikipedia.org/wiki/Logarithm) 2 is used, the unit of mutual information is the [shannon](https://en.wikipedia.org/wiki/Shannon_(unit) "Shannon (unit)"), also known as the bit. If the [log base](https://en.wikipedia.org/wiki/Logarithm) 10 is used, the unit of mutual information is the [hartley](https://en.wikipedia.org/wiki/Hartley_(unit) "Hartley (unit)"), also known as the ban or the dit.

### In terms of PMFs for discrete distributions

The mutual information of two jointly discrete random variables $X$ and $Y$ is calculated as a double sum:

$\operatorname {I} (X;Y)=\sum _{y\in {\mathcal {Y}}}\sum _{x\in {\mathcal {X}}}{P_{(X,Y)}(x,y)\log \left({\frac {P_{(X,Y)}(x,y)}{P_{X}(x)\,P_{Y}(y)}}\right)}$,

where $P_{(X,Y)}$ is the [joint probability mass function](https://en.wikipedia.org/wiki/Joint_distribution) of $X$ and $Y$, and $P_{X}$ and $P_{Y}$ are the [marginal probability](https://en.wikipedia.org/wiki/Marginal_probability) mass functions of $X$ and $Y$ respectively.

### In terms of PDFs for continuous distributions

In the case of jointly continuous random variables, the double sum is replaced by a [double integral](https://en.wikipedia.org/wiki/Double_integral):

$\operatorname {I} (X;Y)=\int _{\mathcal {Y}}\int _{\mathcal {X}}{P_{(X,Y)}(x,y)\log {\left({\frac {P_{(X,Y)}(x,y)}{P_{X}(x)\,P_{Y}(y)}}\right)}}\;dx\,dy$,

where $P_{(X,Y)}$ is now the joint probability *density* function of $X$ and $Y$, and $P_{X}$ and $P_{Y}$ are the marginal probability density functions of $X$ and $Y$ respectively.

## Motivation

Intuitively, mutual information measures the information that $X$ and $Y$ share: It measures how much knowing one of these variables reduces uncertainty about the other. For example, if $X$ and $Y$ are independent, then knowing $X$ does not give any information about $Y$ and vice versa, so their mutual information is zero. At the other extreme, if $X$ is a deterministic function of $Y$ and $Y$ is a deterministic function of $X$ then all information conveyed by $X$ is shared with $Y$: knowing $X$ determines the value of $Y$ and vice versa. As a result, the mutual information is the same as the uncertainty contained in $Y$ (or $X$) alone, namely the [entropy](https://en.wikipedia.org/wiki/Information_entropy) of $Y$ (or $X$). A very special case of this is when $X$ and $Y$ are the same random variable.

Mutual information is a measure of the inherent dependence expressed in the [joint distribution](https://en.wikipedia.org/wiki/Joint_distribution) of $X$ and $Y$ relative to the marginal distribution of $X$ and $Y$ under the assumption of independence. Mutual information therefore measures dependence in the following sense: $\operatorname {I} (X;Y)=0$ [if and only if](https://en.wikipedia.org/wiki/If_and_only_if) $X$ and $Y$ are independent random variables. This is easy to see in one direction: if $X$ and $Y$ are independent, then $p_{(X,Y)}(x,y)=p_{X}(x)\cdot p_{Y}(y)$, and therefore:

$\log {\left({\frac {p_{(X,Y)}(x,y)}{p_{X}(x)\,p_{Y}(y)}}\right)}=\log 1=0$.

Moreover, mutual information is nonnegative (i.e. $\operatorname {I} (X;Y)\geq 0$ see below) and [symmetric](https://en.wikipedia.org/wiki/Symmetric_function) (i.e. $\operatorname {I} (X;Y)=\operatorname {I} (Y;X)$ see below).

## Properties

### Nonnegativity

Using [Jensen's inequality](https://en.wikipedia.org/wiki/Jensen%27s_inequality) on the definition of mutual information we can show that $\operatorname {I} (X;Y)$ is non-negative, i.e.

$\operatorname {I} (X;Y)\geq 0$

### Symmetry

$\operatorname {I} (X;Y)=\operatorname {I} (Y;X)$

The proof is given considering the relationship with entropy, as shown below.

### Supermodularity under independence

If $C$ is independent of $(A,B)$, then

$\operatorname {I} (Y;A,B,C)-\operatorname {I} (Y;A,B)\geq \operatorname {I} (Y;A,C)-\operatorname {I} (Y;A)$.

### Relation to conditional and joint entropy

Mutual information can be equivalently expressed as:

${\begin{aligned}\operatorname {I} (X;Y)&{}\equiv \mathrm {H} (X)-\mathrm {H} (X\mid Y)\\&{}\equiv \mathrm {H} (Y)-\mathrm {H} (Y\mid X)\\&{}\equiv \mathrm {H} (X)+\mathrm {H} (Y)-\mathrm {H} (X,Y)\\&{}\equiv \mathrm {H} (X,Y)-\mathrm {H} (X\mid Y)-\mathrm {H} (Y\mid X)\end{aligned}}$

where $\mathrm {H} (X)$ and $\mathrm {H} (Y)$ are the marginal [entropies](https://en.wikipedia.org/wiki/Information_entropy), $\mathrm {H} (X\mid Y)$ and $\mathrm {H} (Y\mid X)$ are the [conditional entropies](https://en.wikipedia.org/wiki/Conditional_entropy), and $\mathrm {H} (X,Y)$ is the [joint entropy](https://en.wikipedia.org/wiki/Joint_entropy) of $X$ and $Y$.

Notice the analogy to the union, difference, and intersection of two sets: in this respect, all the formulas given above are apparent from the Venn diagram reported at the beginning of the article.

In terms of a communication channel in which the output $Y$ is a noisy version of the input $X$, these relations are summarised in the figure:

![[media/e7da76d283d60a9d10bab742e8c39658db8a8631.png]]
The relationships between information theoretic quantities

Because $\operatorname {I} (X;Y)$ is non-negative, consequently, $\mathrm {H} (X)\geq \mathrm {H} (X\mid Y)$. Here we give the detailed deduction of $\operatorname {I} (X;Y)=\mathrm {H} (Y)-\mathrm {H} (Y\mid X)$ for the case of jointly discrete random variables:

${\begin{aligned}\operatorname {I} (X;Y)&{}=\sum _{x\in {\mathcal {X}},y\in {\mathcal {Y}}}p_{(X,Y)}(x,y)\log {\frac {p_{(X,Y)}(x,y)}{p_{X}(x)p_{Y}(y)}}\\&{}=\sum _{x\in {\mathcal {X}},y\in {\mathcal {Y}}}p_{(X,Y)}(x,y)\log {\frac {p_{(X,Y)}(x,y)}{p_{X}(x)}}-\sum _{x\in {\mathcal {X}},y\in {\mathcal {Y}}}p_{(X,Y)}(x,y)\log p_{Y}(y)\\&{}=\sum _{x\in {\mathcal {X}},y\in {\mathcal {Y}}}p_{X}(x)p_{Y\mid X=x}(y)\log p_{Y\mid X=x}(y)-\sum _{x\in {\mathcal {X}},y\in {\mathcal {Y}}}p_{(X,Y)}(x,y)\log p_{Y}(y)\\&{}=\sum _{x\in {\mathcal {X}}}p_{X}(x)\left(\sum _{y\in {\mathcal {Y}}}p_{Y\mid X=x}(y)\log p_{Y\mid X=x}(y)\right)-\sum _{y\in {\mathcal {Y}}}\left(\sum _{x\in {\mathcal {X}}}p_{(X,Y)}(x,y)\right)\log p_{Y}(y)\\&{}=-\sum _{x\in {\mathcal {X}}}p_{X}(x)\mathrm {H} (Y\mid X=x)-\sum _{y\in {\mathcal {Y}}}p_{Y}(y)\log p_{Y}(y)\\&{}=-\mathrm {H} (Y\mid X)+\mathrm {H} (Y)\\&{}=\mathrm {H} (Y)-\mathrm {H} (Y\mid X).\\\end{aligned}}$

The proofs of the other identities above are similar. The proof of the general case (not just discrete) is similar, with integrals replacing sums.

Intuitively, if entropy $\mathrm {H} (Y)$ is regarded as a measure of uncertainty about a random variable, then $\mathrm {H} (Y\mid X)$ is a measure of what $X$ does *not* say about $Y$. This is "the amount of uncertainty remaining about $Y$ after $X$ is known", and thus the right side of the second of these equalities can be read as "the amount of uncertainty in $Y$, minus the amount of uncertainty in $Y$ which remains after $X$ is known", which is equivalent to "the amount of uncertainty in $Y$ which is removed by knowing $X$". This corroborates the intuitive meaning of mutual information as the amount of information (that is, reduction in uncertainty) that knowing either variable provides about the other.

Note that in the discrete case $\mathrm {H} (Y\mid Y)=0$ and therefore $\mathrm {H} (Y)=\operatorname {I} (Y;Y)$. Thus $\operatorname {I} (Y;Y)\geq \operatorname {I} (X;Y)$, and one can formulate the basic principle that a variable contains at least as much information about itself as any other variable can provide.

### Relation to Kullback–Leibler divergence

For jointly discrete or jointly continuous pairs $(X,Y)$, mutual information is the [[Kullback-Leibler Divergence|Kullback–Leibler divergence]] from the product of the [marginal distributions](https://en.wikipedia.org/wiki/Marginal_distribution), $p_{X}\cdot p_{Y}$, of the [joint distribution](https://en.wikipedia.org/wiki/Joint_distribution) $p_{(X,Y)}$, that is,

$\operatorname {I} (X;Y)=D_{\text{KL}}\left(p_{(X,Y)}\parallel p_{X}p_{Y}\right)$

Furthermore, let $p_{(X,Y)}(x,y)=p_{X\mid Y=y}(x)*p_{Y}(y)$ be the conditional mass or density function. Then, we have the identity

$\operatorname {I} (X;Y)=\mathbb {E} _{Y}\left[D_{\text{KL}}\!\left(p_{X\mid Y}\parallel p_{X}\right)\right]$

The proof for jointly discrete random variables is as follows:

${\begin{aligned}\operatorname {I} (X;Y)&=\sum _{y\in {\mathcal {Y}}}\sum _{x\in {\mathcal {X}}}{p_{(X,Y)}(x,y)\log \left({\frac {p_{(X,Y)}(x,y)}{p_{X}(x)\,p_{Y}(y)}}\right)}\\&=\sum _{y\in {\mathcal {Y}}}\sum _{x\in {\mathcal {X}}}p_{X\mid Y=y}(x)p_{Y}(y)\log {\frac {p_{X\mid Y=y}(x)p_{Y}(y)}{p_{X}(x)p_{Y}(y)}}\\&=\sum _{y\in {\mathcal {Y}}}p_{Y}(y)\sum _{x\in {\mathcal {X}}}p_{X\mid Y=y}(x)\log {\frac {p_{X\mid Y=y}(x)}{p_{X}(x)}}\\&=\sum _{y\in {\mathcal {Y}}}p_{Y}(y)\;D_{\text{KL}}\!\left(p_{X\mid Y=y}\parallel p_{X}\right)\\&=\mathbb {E} _{Y}\left[D_{\text{KL}}\!\left(p_{X\mid Y}\parallel p_{X}\right)\right].\end{aligned}}$

Similarly this identity can be established for jointly continuous random variables.

Note that here the Kullback–Leibler divergence involves integration over the values of the random variable $X$ only, and the expression $D_{\text{KL}}(p_{X\mid Y}\parallel p_{X})$ still denotes a random variable because $Y$ is random. Thus mutual information can also be understood as the [expectation](https://en.wikipedia.org/wiki/Expected_value) over $Y$ of the Kullback–Leibler divergence of the [conditional distribution](https://en.wikipedia.org/wiki/Conditional_distribution) $p_{X\mid Y}$ of $X$ given $Y$ from the [univariate distribution](https://en.wikipedia.org/wiki/Univariate_distribution) $p_{X}$ of $X$: the more different the distributions $p_{X\mid Y}$ and $p_{X}$ are on average, the greater the [[Kullback-Leibler Divergence|information gain]].

### Bayesian estimation of mutual information

If samples from a joint distribution are available, a Bayesian approach can be used to estimate the mutual information of that distribution. The first work to do this, which also showed how to do Bayesian estimation of many other information-theoretic properties besides mutual information, was. Subsequent researchers have rederived  and extended  this analysis. See  for a recent paper based on a prior specifically tailored to estimation of mutual information per se. Besides, recently an estimation method accounting for continuous and multivariate outputs, $Y$, was proposed in .

### Independence assumptions

The Kullback-Leibler divergence formulation of the mutual information is predicated on that one is interested in comparing $p(x,y)$ to the fully factorized [outer product](https://en.wikipedia.org/wiki/Outer_product) $p(x)\cdot p(y)$. In many problems, such as [non-negative matrix factorization](https://en.wikipedia.org/wiki/Non-negative_matrix_factorization), one is interested in less extreme factorizations; specifically, one wishes to compare $p(x,y)$ to a low-rank matrix approximation in some unknown variable $w$; that is, to what degree one might have

$p(x,y)\approx \sum _{w}p^{\prime }(x,w)p^{\prime \prime }(w,y)$

Alternately, one might be interested in knowing how much more information $p(x,y)$ carries over its factorization. In such a case, the excess information that the full distribution $p(x,y)$ carries over the matrix factorization is given by the Kullback-Leibler divergence

$\operatorname {I} _{LRMA}=\sum _{y\in {\mathcal {Y}}}\sum _{x\in {\mathcal {X}}}{p(x,y)\log {\left({\frac {p(x,y)}{\sum _{w}p^{\prime }(x,w)p^{\prime \prime }(w,y)}}\right)}},$

The conventional definition of the mutual information is recovered in the extreme case that the process $W$ has only one value for $w$.

## Variations

Several variations on mutual information have been proposed to suit various needs. Among these are normalized variants and generalizations to more than two variables.

### Metric

Many applications require a [metric](https://en.wikipedia.org/wiki/Metric_(mathematics)), that is, a distance measure between pairs of points. The quantity

${\begin{aligned}d(X,Y)&=\mathrm {H} (X,Y)-\operatorname {I} (X;Y)\\&=\mathrm {H} (X)+\mathrm {H} (Y)-2\operatorname {I} (X;Y)\\&=\mathrm {H} (X\mid Y)+\mathrm {H} (Y\mid X)\\&=2\mathrm {H} (X,Y)-\mathrm {H} (X)-\mathrm {H} (Y)\end{aligned}}$

satisfies the properties of a metric ([triangle inequality](https://en.wikipedia.org/wiki/Triangle_inequality), [non-negativity](https://en.wikipedia.org/wiki/Non-negative), [indiscernability](https://en.wikipedia.org/wiki/Identity_of_indiscernibles) and symmetry), where equality $X=Y$ is understood to mean that $X$ can be completely determined from $Y$.

This distance metric is also known as the [variation of information](https://en.wikipedia.org/wiki/Variation_of_information).

If $X,Y$ are discrete random variables then all the entropy terms are non-negative, so $0\leq d(X,Y)\leq \mathrm {H} (X,Y)$ and one can define a normalized distance

$D(X,Y)={\frac {d(X,Y)}{\mathrm {H} (X,Y)}}\leq 1.$

Plugging in the definitions shows that

$D(X,Y)=1-{\frac {\operatorname {I} (X;Y)}{\mathrm {H} (X,Y)}}.$

This is known as the Rajski Distance. In a set-theoretic interpretation of information (see the figure for [Conditional entropy](https://en.wikipedia.org/wiki/Conditional_entropy)), this is effectively the [Jaccard distance](https://en.wikipedia.org/wiki/Jaccard_index) between $X$ and $Y$.

Finally,

$D^{\prime }(X,Y)=1-{\frac {\operatorname {I} (X;Y)}{\max \left\{\mathrm {H} (X),\mathrm {H} (Y)\right\}}}$

is also a metric.

### Conditional mutual information

Sometimes it is useful to express the mutual information of two random variables conditioned on a third.

$\operatorname {I} (X;Y|Z)=\mathbb {E} _{Z}[D_{\mathrm {KL} }(P_{(X,Y)|Z}\|P_{X|Z}\otimes P_{Y|Z})]$

For jointly [discrete random variables](https://en.wikipedia.org/wiki/Discrete_random_variable) this takes the form

$\operatorname {I} (X;Y|Z)=\sum _{z\in {\mathcal {Z}}}\sum _{y\in {\mathcal {Y}}}\sum _{x\in {\mathcal {X}}}{p_{Z}(z)\,p_{X,Y|Z}(x,y|z)\log \left[{\frac {p_{X,Y|Z}(x,y|z)}{p_{X|Z}\,(x|z)p_{Y|Z}(y|z)}}\right]},$

which can be simplified as

$\operatorname {I} (X;Y|Z)=\sum _{z\in {\mathcal {Z}}}\sum _{y\in {\mathcal {Y}}}\sum _{x\in {\mathcal {X}}}p_{X,Y,Z}(x,y,z)\log {\frac {p_{X,Y,Z}(x,y,z)p_{Z}(z)}{p_{X,Z}(x,z)p_{Y,Z}(y,z)}}.$

For jointly [continuous random variables](https://en.wikipedia.org/wiki/Continuous_random_variable) this takes the form

$\operatorname {I} (X;Y|Z)=\int _{\mathcal {Z}}\int _{\mathcal {Y}}\int _{\mathcal {X}}{p_{Z}(z)\,p_{X,Y|Z}(x,y|z)\log \left[{\frac {p_{X,Y|Z}(x,y|z)}{p_{X|Z}\,(x|z)p_{Y|Z}(y|z)}}\right]}dxdydz,$

which can be simplified as

$\operatorname {I} (X;Y|Z)=\int _{\mathcal {Z}}\int _{\mathcal {Y}}\int _{\mathcal {X}}p_{X,Y,Z}(x,y,z)\log {\frac {p_{X,Y,Z}(x,y,z)p_{Z}(z)}{p_{X,Z}(x,z)p_{Y,Z}(y,z)}}dxdydz.$

Conditioning on a third random variable may either increase or decrease the mutual information, but it is always true that

$\operatorname {I} (X;Y|Z)\geq 0$

for discrete, jointly distributed random variables $X,Y,Z$. This result has been used as a basic building block for proving other [inequalities in information theory](https://en.wikipedia.org/wiki/Inequalities_in_information_theory).

### Interaction information

Several generalizations of mutual information to more than two random variables have been proposed, such as [total correlation](https://en.wikipedia.org/wiki/Total_correlation) (or multi-information) and [dual total correlation](https://en.wikipedia.org/wiki/Dual_total_correlation). The expression and study of multivariate higher-degree mutual information was achieved in two seemingly independent works: McGill (1954) who called these functions "[interaction information](https://en.wikipedia.org/wiki/Interaction_information)", and Hu Kuo Ting (1962). Interaction information is defined for one variable as follows:

$\operatorname {I} (X_{1})=\mathrm {H} (X_{1})$

and for $n>1,$

$\operatorname {I} (X_{1};\,...\,;X_{n})=\operatorname {I} (X_{1};\,...\,;X_{n-1})-\operatorname {I} (X_{1};\,...\,;X_{n-1}\mid X_{n}).$

Some authors reverse the order of the terms on the right-hand side of the preceding equation, which changes the sign when the number of random variables is odd. (And in this case, the single-variable expression becomes the negative of the entropy.) Note that

$I(X_{1};\ldots ;X_{n-1}\mid X_{n})=\mathbb {E} _{X_{n}}[D_{\mathrm {KL} }(P_{(X_{1},\ldots ,X_{n-1})\mid X_{n}}\|P_{X_{1}\mid X_{n}}\otimes \cdots \otimes P_{X_{n-1}\mid X_{n}})].$

#### Multivariate statistical independence

The multivariate mutual information functions generalize the [pairwise independence](https://en.wikipedia.org/wiki/Pairwise_independence) case that states that $X_{1},X_{2}$ if and only if $I(X_{1};X_{2})=0$, to arbitrary numerous variable. n variables are mutually independent if and only if the $2^{n}-n-1$ mutual information functions vanish $I(X_{1};\ldots ;X_{k})=0$ with $n\geq k\geq 2$ (theorem 2). In this sense, the $I(X_{1};\ldots ;X_{k})=0$ can be used as a refined statistical independence criterion.

#### Applications

For 3 variables, Brenner et al. applied multivariate mutual information to [neural coding](https://en.wikipedia.org/wiki/Neural_coding) and called its negativity "synergy" and Watkinson et al. applied it to genetic expression. For arbitrary k variables, Tapia et al. applied multivariate mutual information to [gene expression](https://en.wikipedia.org/wiki/Gene_expression). It can be zero, positive, or negative. The positivity corresponds to relations generalizing the pairwise correlations, nullity corresponds to a refined notion of independence, and negativity detects high dimensional "emergent" relations and clustered datapoints ).

One high-dimensional generalization scheme which maximizes the mutual information between the joint distribution and other target variables is found to be useful in [feature selection](https://en.wikipedia.org/wiki/Feature_selection).

Mutual information is also used in the area of signal processing as a [measure of similarity](https://en.wikipedia.org/wiki/Similarity_measure) between two signals. For example, FMI metric is an image fusion performance measure that makes use of mutual information in order to measure the amount of information that the fused image contains about the source images. The [Matlab](https://en.wikipedia.org/wiki/Matlab) code for this metric can be found at. A python package for computing all multivariate mutual informations, [conditional mutual information](https://en.wikipedia.org/wiki/Conditional_mutual_information), joint entropies, total correlations, information distance in a dataset of n variables is available.

### Directed information

[Directed information](https://en.wikipedia.org/wiki/Directed_information), $\operatorname {I} \left(X^{n}\to Y^{n}\right)$, measures the amount of information that flows from the process $X^{n}$ to $Y^{n}$, where $X^{n}$ denotes the vector $X_{1},X_{2},...,X_{n}$ and $Y^{n}$ denotes $Y_{1},Y_{2},...,Y_{n}$. The term *directed information* was coined by [James Massey](https://en.wikipedia.org/wiki/James_Massey) and is defined as

$\operatorname {I} \left(X^{n}\to Y^{n}\right)=\sum _{i=1}^{n}\operatorname {I} \left(X^{i};Y_{i}\mid Y^{i-1}\right)$.

Note that if $n=1$, the directed information becomes the mutual information. Directed information has many applications in problems where [causality](https://en.wikipedia.org/wiki/Causality) plays an important role, such as [capacity of channel](https://en.wikipedia.org/wiki/Channel_capacity) with feedback.

### Normalized variants

Normalized variants of the mutual information are provided by the *coefficients of constraint*, [uncertainty coefficient](https://en.wikipedia.org/wiki/Uncertainty_coefficient) or proficiency:

$C_{XY}={\frac {\operatorname {I} (X;Y)}{\mathrm {H} (Y)}}~~~~{\mbox{and}}~~~~C_{YX}={\frac {\operatorname {I} (X;Y)}{\mathrm {H} (X)}}.$

The two coefficients have a value ranging in \[0, 1\], but are not necessarily equal. This measure is not symmetric. If one desires a symmetric measure, one may consider the following *[redundancy](https://en.wikipedia.org/wiki/Redundancy_(information_theory) "Redundancy (information theory)")* measure:

$R={\frac {\operatorname {I} (X;Y)}{\mathrm {H} (X)+\mathrm {H} (Y)}}$

which attains a minimum of zero when the variables are independent and a maximum value of

$R_{\max }={\frac {\min \left\{\mathrm {H} (X),\mathrm {H} (Y)\right\}}{\mathrm {H} (X)+\mathrm {H} (Y)}}$

when one variable becomes completely redundant with the knowledge of the other. See also *[Redundancy (information theory)](https://en.wikipedia.org/wiki/Redundancy_(information_theory) "Redundancy (information theory)")*.

Another symmetrical measure is the *symmetric uncertainty* (), given by

$U(X,Y)=2R=2{\frac {\operatorname {I} (X;Y)}{\mathrm {H} (X)+\mathrm {H} (Y)}}$

which represents the [harmonic mean](https://en.wikipedia.org/wiki/Harmonic_mean) of the two uncertainty coefficients $C_{XY},C_{YX}$.

If we consider mutual information as a special case of the [total correlation](https://en.wikipedia.org/wiki/Total_correlation) or [dual total correlation](https://en.wikipedia.org/wiki/Dual_total_correlation), the normalized versions are respectively,

${\frac {\operatorname {I} (X;Y)}{\min \left[\mathrm {H} (X),\mathrm {H} (Y)\right]}}$ and ${\frac {\operatorname {I} (X;Y)}{\mathrm {H} (X,Y)}}\;.$

This normalized version is also known as **Information Quality Ratio (IQR)** and quantifies the amount of information of a variable based on another variable against total uncertainty:

$IQR(X,Y)=\operatorname {E} [\operatorname {I} (X;Y)]={\frac {\operatorname {I} (X;Y)}{\mathrm {H} (X,Y)}}={\frac {\sum _{x\in X}\sum _{y\in Y}p(x,y)\log {p(x)p(y)}}{\sum _{x\in X}\sum _{y\in Y}p(x,y)\log {p(x,y)}}}-1$

There exists a normalization which derives from first thinking of mutual information as an analogue to [covariance](https://en.wikipedia.org/wiki/Covariance) (thus [Shannon entropy](https://en.wikipedia.org/wiki/Entropy_(information_theory) "Entropy (information theory)") is analogous to [variance](https://en.wikipedia.org/wiki/Variance)). Then the normalized mutual information is calculated akin to the [Pearson correlation coefficient](https://en.wikipedia.org/wiki/Pearson_product-moment_correlation_coefficient),

${\frac {\operatorname {I} (X;Y)}{\sqrt {\mathrm {H} (X)\mathrm {H} (Y)}}}\;.$

A naive normalization may lead to biased interpretation and introduce spurious dependences.

### Weighted variants

In the traditional formulation of the mutual information,

$\operatorname {I} (X;Y)=\sum _{y\in Y}\sum _{x\in X}p(x,y)\log {\frac {p(x,y)}{p(x)\,p(y)}},$

each *event* or *object* specified by $(x,y)$ is weighted by the corresponding probability $p(x,y)$. This assumes that all objects or events are equivalent *apart from* their probability of occurrence. However, in some applications it may be the case that certain objects or events are more *significant* than others, or that certain patterns of association are more semantically important than others.

For example, the deterministic mapping $\{(1,1),(2,2),(3,3)\}$ may be viewed as stronger than the deterministic mapping $\{(1,3),(2,1),(3,2)\}$, although these relationships would yield the same mutual information. This is because the mutual information is not sensitive at all to any inherent ordering in the variable values (, , ), and is therefore not sensitive at all to the **form** of the relational mapping between the associated variables. If it is desired that the former relation—showing agreement on all variable values—be judged stronger than the later relation, then it is possible to use the following *weighted mutual information* ().

$\operatorname {I} (X;Y)=\sum _{y\in Y}\sum _{x\in X}w(x,y)p(x,y)\log {\frac {p(x,y)}{p(x)\,p(y)}},$

which places a weight $w(x,y)$ on the probability of each variable value co-occurrence, $p(x,y)$. This allows that certain probabilities may carry more or less significance than others, thereby allowing the quantification of relevant *holistic* or *[Prägnanz](https://en.wikipedia.org/wiki/Pr%C3%A4gnanz)* factors. In the above example, using larger relative weights for $w(1,1)$, $w(2,2)$, and $w(3,3)$ would have the effect of assessing greater *informativeness* for the relation $\{(1,1),(2,2),(3,3)\}$ than for the relation $\{(1,3),(2,1),(3,2)\}$, which may be desirable in some cases of pattern recognition, and the like. This weighted mutual information is a form of weighted KL-Divergence, which is known to take negative values for some inputs, and there are examples where the weighted mutual information also takes negative values.

### Adjusted mutual information

A probability distribution can be viewed as a [partition of a set](https://en.wikipedia.org/wiki/Partition_of_a_set). One may then ask: if a set were partitioned randomly, what would the distribution of probabilities be? What would the expectation value of the mutual information be? The [adjusted mutual information](https://en.wikipedia.org/wiki/Adjusted_mutual_information) or AMI subtracts the expectation value of the MI, so that the AMI is zero when two different distributions are random, and one when two distributions are identical. The AMI is defined in analogy to the [adjusted Rand index](https://en.wikipedia.org/wiki/Adjusted_Rand_index) of two different partitions of a set.

### Absolute mutual information

Using the ideas of [Kolmogorov complexity](https://en.wikipedia.org/wiki/Kolmogorov_complexity), one can consider the mutual information of two sequences independent of any probability distribution:

$\operatorname {I} _{K}(X;Y)=K(X)-K(X\mid Y).$

To establish that this quantity is symmetric up to a logarithmic factor ($\operatorname {I} _{K}(X;Y)\approx \operatorname {I} _{K}(Y;X)$) one requires the [chain rule for Kolmogorov complexity](https://en.wikipedia.org/wiki/Chain_rule_for_Kolmogorov_complexity) (). Approximations of this quantity via [compression](https://en.wikipedia.org/wiki/Data_compression) can be used to define a [distance measure](https://en.wikipedia.org/wiki/Metric_(mathematics)) to perform a [hierarchical clustering](https://en.wikipedia.org/wiki/Hierarchical_clustering) of sequences without having any [domain knowledge](https://en.wikipedia.org/wiki/Domain_knowledge) of the sequences ().

### Linear correlation

Unlike correlation coefficients, such as the [product moment correlation coefficient](https://en.wikipedia.org/wiki/Product_moment_correlation_coefficient), mutual information contains information about all dependence—linear and nonlinear—and not just linear dependence as the correlation coefficient measures. However, in the narrow case that the joint distribution for $X$ and $Y$ is a [bivariate normal distribution](https://en.wikipedia.org/wiki/Bivariate_normal_distribution) (implying in particular that both marginal distributions are normally distributed), there is an exact relationship between $\operatorname {I}$ and the correlation coefficient $\rho$ ().

$\operatorname {I} =-{\frac {1}{2}}\log \left(1-\rho ^{2}\right)$

The equation above can be derived as follows for a bivariate Gaussian:

${\begin{aligned}{\begin{pmatrix}X_{1}\\X_{2}\end{pmatrix}}&\sim {\mathcal {N}}\left({\begin{pmatrix}\mu _{1}\\\mu _{2}\end{pmatrix}},\Sigma \right),\qquad \Sigma ={\begin{pmatrix}\sigma _{1}^{2}&\rho \sigma _{1}\sigma _{2}\\\rho \sigma _{1}\sigma _{2}&\sigma _{2}^{2}\end{pmatrix}}\\\mathrm {H} (X_{i})&={\frac {1}{2}}\log \left(2\pi e\sigma _{i}^{2}\right)={\frac {1}{2}}+{\frac {1}{2}}\log(2\pi )+\log \left(\sigma _{i}\right),\quad i\in \{1,2\}\\\mathrm {H} (X_{1},X_{2})&={\frac {1}{2}}\log \left[(2\pi e)^{2}|\Sigma |\right]=1+\log(2\pi )+\log \left(\sigma _{1}\sigma _{2}\right)+{\frac {1}{2}}\log \left(1-\rho ^{2}\right)\\\end{aligned}}$

Therefore,

$\operatorname {I} \left(X_{1};X_{2}\right)=\mathrm {H} \left(X_{1}\right)+\mathrm {H} \left(X_{2}\right)-\mathrm {H} \left(X_{1},X_{2}\right)=-{\frac {1}{2}}\log \left(1-\rho ^{2}\right)$

### For discrete data

When $X$ and $Y$ are limited to be in a discrete number of states, observation data is summarized in a [contingency table](https://en.wikipedia.org/wiki/Contingency_table), with row variable $X$ (or $i$) and column variable $Y$ (or $j$). Mutual information is one of the measures of [association](https://en.wikipedia.org/wiki/Association_(statistics)) or [correlation](https://en.wikipedia.org/wiki/Correlation_and_dependence) between the row and column variables.

Other measures of association include [Pearson's chi-squared test](https://en.wikipedia.org/wiki/Pearson%27s_chi-squared_test) statistics, [G-test](https://en.wikipedia.org/wiki/G-test) statistics, etc. In fact, with the same log base, mutual information will be equal to the [G-test](https://en.wikipedia.org/wiki/G-test) log-likelihood statistic divided by $2N$, where $N$ is the sample size.

## Applications

In many applications, one wants to maximize mutual information (thus increasing dependencies), which is often equivalent to minimizing [conditional entropy](https://en.wikipedia.org/wiki/Conditional_entropy). Examples include:

- In [search engine technology](https://en.wikipedia.org/wiki/Search_engine_technology), mutual information between phrases and contexts is used as a feature for [k-means clustering](https://en.wikipedia.org/wiki/K-means_clustering) to discover semantic clusters (concepts). For example, the mutual information of a bigram might be calculated as:

$MI(x,y)=\log {\frac {P_{X,Y}(x,y)}{P_{X}(x)P_{Y}(y)}}\approx \log {\frac {\frac {f_{XY}}{B}}{{\frac {f_{X}}{U}}{\frac {f_{Y}}{U}}}}$

where $f_{XY}$ is the number of times the bigram xy appears in the corpus, $f_{X}$ is the number of times the unigram x appears in the corpus, B is the total number of bigrams, and U is the total number of unigrams.

- In [telecommunications](https://en.wikipedia.org/wiki/Telecommunications), the [channel capacity](https://en.wikipedia.org/wiki/Channel_capacity) is equal to the mutual information, maximized over all input distributions.
- [RNA secondary structure](https://en.wikipedia.org/wiki/Nucleic_acid_secondary_structure) prediction from a [multiple sequence alignment](https://en.wikipedia.org/wiki/Multiple_sequence_alignment).
- [Phylogenetic profiling](https://en.wikipedia.org/wiki/Phylogenetic_profiling) prediction from pairwise present and disappearance of functionally link [genes](https://en.wikipedia.org/wiki/Gene).
- Mutual information has been used as a criterion for [feature selection](https://en.wikipedia.org/wiki/Feature_selection) and feature transformations in [machine learning](https://en.wikipedia.org/wiki/Machine_learning). It can be used to characterize both the relevance and redundancy of variables, such as the [minimum redundancy feature selection](https://en.wikipedia.org/wiki/Minimum_redundancy_feature_selection).
- Mutual information is used in determining the similarity of two different [clusterings](https://en.wikipedia.org/wiki/Cluster_analysis) of a dataset. As such, it provides some advantages over the traditional [Rand index](https://en.wikipedia.org/wiki/Rand_index).
- Mutual information of words is often used as a significance function for the computation of [collocations](https://en.wikipedia.org/wiki/Collocation) in [corpus linguistics](https://en.wikipedia.org/wiki/Corpus_linguistics). This has the added complexity that no word-instance is an instance to two different words; rather, one counts instances where 2 words occur adjacent or in close proximity; this slightly complicates the calculation, since the expected probability of one word occurring within $N$ words of another, goes up with $N$
- Mutual information is used in [medical imaging](https://en.wikipedia.org/wiki/Medical_imaging) for [image registration](https://en.wikipedia.org/wiki/Image_registration). Given a reference image (for example, a brain scan), and a second image which needs to be put into the same [coordinate system](https://en.wikipedia.org/wiki/Coordinate_system) as the reference image, this image is deformed until the mutual information between it and the reference image is maximized.
- Detection of [phase synchronization](https://en.wikipedia.org/wiki/Phase_synchronization) in [time series](https://en.wikipedia.org/wiki/Time_series) analysis.
- In the [infomax](https://en.wikipedia.org/wiki/Infomax) method for neural-net and other machine learning, including the infomax-based [Independent component analysis](https://en.wikipedia.org/wiki/Independent_component_analysis) algorithm
- Average mutual information in [delay embedding theorem](https://en.wikipedia.org/wiki/Delay_embedding_theorem) is used for determining the *embedding delay* parameter.
- Mutual information between [genes](https://en.wikipedia.org/wiki/Genes) in [expression microarray](https://en.wikipedia.org/wiki/Microarray) data is used by the ARACNE algorithm for reconstruction of [gene networks](https://en.wikipedia.org/wiki/Gene_regulatory_network).
- In [statistical mechanics](https://en.wikipedia.org/wiki/Statistical_mechanics), [Loschmidt's paradox](https://en.wikipedia.org/wiki/Loschmidt%27s_paradox) may be expressed in terms of mutual information. Loschmidt noted that it must be impossible to determine a physical law which lacks [time reversal symmetry](https://en.wikipedia.org/wiki/Time_reversal_symmetry) (e.g. the [second law of thermodynamics](https://en.wikipedia.org/wiki/Second_law_of_thermodynamics)) only from physical laws which have this symmetry. He pointed out that the [H-theorem](https://en.wikipedia.org/wiki/H-theorem) of [Boltzmann](https://en.wikipedia.org/wiki/Boltzmann) made the assumption that the velocities of particles in a gas were permanently uncorrelated, which removed the time symmetry inherent in the H-theorem. It can be shown that if a system is described by a probability density in [phase space](https://en.wikipedia.org/wiki/Phase_space), then [Liouville's theorem](https://en.wikipedia.org/wiki/Liouville%27s_theorem_(Hamiltonian) "Liouville's theorem (Hamiltonian)") implies that the joint information (negative of the joint entropy) of the distribution remains constant in time. The joint information is equal to the mutual information plus the sum of all the marginal information (negative of the marginal entropies) for each particle coordinate. Boltzmann's assumption amounts to ignoring the mutual information in the calculation of entropy, which yields the thermodynamic entropy (divided by the Boltzmann constant).
- In [stochastic processes](https://en.wikipedia.org/wiki/Stochastic_process) coupled to changing environments, mutual information can be used to disentangle internal and effective environmental dependencies. This is particularly useful when a physical system undergoes changes in the parameters describing its dynamics, e.g., changes in temperature.
- The mutual information is used to learn the structure of [Bayesian networks](https://en.wikipedia.org/wiki/Bayesian_network)/[dynamic Bayesian networks](https://en.wikipedia.org/wiki/Dynamic_Bayesian_network), which is thought to explain the causal relationship between random variables, as exemplified by the GlobalMIT toolkit: learning the globally optimal dynamic Bayesian network with the Mutual Information Test criterion.
- The mutual information is used to quantify information transmitted during the updating procedure in the [[Gibbs Sampling]] algorithm.
- Popular cost function in [decision tree learning](https://en.wikipedia.org/wiki/Decision_tree_learning).
- The mutual information is used in [cosmology](https://en.wikipedia.org/wiki/Cosmology) to test the influence of large-scale environments on galaxy properties in the [Galaxy Zoo](https://en.wikipedia.org/wiki/Galaxy_Zoo).
- The mutual information was used in [Solar Physics](https://en.wikipedia.org/wiki/Solar_Physics) to derive the solar [differential rotation](https://en.wikipedia.org/wiki/Differential_rotation) profile, a travel-time deviation map for sunspots, and a time–distance diagram from quiet-Sun measurements
- Used in Invariant Information Clustering to automatically train neural network classifiers and image segmenters given no labelled data.
- In [stochastic dynamical systems with multiple timescales](https://en.wikipedia.org/wiki/Multiscale_modeling), mutual information has been shown to capture the functional couplings between different temporal scales. Importantly, it was shown that physical interactions may or may not give rise to mutual information, depending on the typical timescale of their dynamics.

## See also

- [Data differencing](https://en.wikipedia.org/wiki/Data_differencing)
- [Pointwise mutual information](https://en.wikipedia.org/wiki/Pointwise_mutual_information)
- [Quantum mutual information](https://en.wikipedia.org/wiki/Quantum_mutual_information)
- [Specific-information](https://en.wikipedia.org/wiki/Specific-information)

## Notes

1.  Cover, Thomas M.; Thomas, Joy A. (2005). [Elements of information theory](http://www.cs.columbia.edu/~vh/courses/LexicalSemantics/Association/Cover&Thomas-Ch2.pdf) (PDF). John Wiley & Sons, Ltd. pp. 13–55. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-74882-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-74882-3).
2.  Kreer, J. G. (1957). "A question of terminology". *IRE Transactions on Information Theory*. **3** (3): 208. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/TIT.1957.1057418](https://doi.org/10.1109%2FTIT.1957.1057418).
3.  ^    Cover, T.M.; Thomas, J.A. (1991). [Elements of Information Theory](https://archive.org/details/elementsofinform0000cove) (Wiley ed.). John Wiley & Sons. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-24195-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-24195-9).
4.  Janssen, Joseph; Guan, Vincent; Robeva, Elina (2023). ["Ultra-marginal Feature Importance: Learning from Data with Causal Guarantees"](https://proceedings.mlr.press/v206/janssen23a.html). *International Conference on Artificial Intelligence and Statistics*: 10782–10814. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2204.09938](https://arxiv.org/abs/2204.09938).
5.  Wolpert, D.H.; Wolf, D.R. (1995). "Estimating functions of probability distributions from a finite set of samples". *Physical Review E*. **52** (6): 6841–6854. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1995PhRvE..52.6841W](https://ui.adsabs.harvard.edu/abs/1995PhRvE..52.6841W). [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.55.7122](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.55.7122). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1103/PhysRevE.52.6841](https://doi.org/10.1103%2FPhysRevE.52.6841). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [9964199](https://pubmed.ncbi.nlm.nih.gov/9964199). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [9795679](https://api.semanticscholar.org/CorpusID:9795679).
6.  Hutter, M. (2001). "Distribution of Mutual Information". *Advances in Neural Information Processing Systems*.
7.  Archer, E.; Park, I.M.; Pillow, J. (2013). ["Bayesian and Quasi-Bayesian Estimators for Mutual Information from Discrete Data"](https://doi.org/10.3390%2Fe15051738). *Entropy*. **15** (12): 1738–1755. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2013Entrp..15.1738A](https://ui.adsabs.harvard.edu/abs/2013Entrp..15.1738A). [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.294.4690](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.294.4690). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3390/e15051738](https://doi.org/10.3390%2Fe15051738).
8.  Wolpert, D.H; DeDeo, S. (2013). ["Estimating Functions of Distributions Defined over Spaces of Unknown Size"](https://doi.org/10.3390%2Fe15114668). *Entropy*. **15** (12): 4668–4699. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1311.4548](https://arxiv.org/abs/1311.4548). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2013Entrp..15.4668W](https://ui.adsabs.harvard.edu/abs/2013Entrp..15.4668W). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3390/e15114668](https://doi.org/10.3390%2Fe15114668). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [2737117](https://api.semanticscholar.org/CorpusID:2737117).
9.  Tomasz Jetka; Karol Nienaltowski; Tomasz Winarski; Slawomir Blonski; Michal Komorowski (2019). "Information-theoretic analysis of multivariate single-cell signaling responses". *[PLOS Computational Biology](https://en.wikipedia.org/wiki/PLOS_Computational_Biology)*. **15** (7) e1007132. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1808.05581](https://arxiv.org/abs/1808.05581). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2019PLSCB..15E7132J](https://ui.adsabs.harvard.edu/abs/2019PLSCB..15E7132J). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1371/journal.pcbi.1007132](https://doi.org/10.1371%2Fjournal.pcbi.1007132). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [6655862](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6655862). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [31299056](https://pubmed.ncbi.nlm.nih.gov/31299056).
10. Rajski, C. (1961). "A metric space of discrete probability distributions". *Information and Control*. **4** (4): 371–377. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/S0019-9958(61)80055-7](https://doi.org/10.1016%2FS0019-9958%2861%2980055-7).
11. Rajski, C. (1961). "A metric space of discrete probability distributions". *Information and Control*. **4** (4): 371–377. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/S0019-9958(61)80055-7](https://doi.org/10.1016%2FS0019-9958%2861%2980055-7).
12. McGill, W. (1954). "Multivariate information transmission". *Psychometrika*. **19** (1): 97–116. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/BF02289159](https://doi.org/10.1007%2FBF02289159). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [126431489](https://api.semanticscholar.org/CorpusID:126431489).
13. ^   Hu, K.T. (1962). "On the Amount of Information". *Theory Probab. Appl*. **7** (4): 439–447. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/1107041](https://doi.org/10.1137%2F1107041).
14. ^   Baudot, P.; Tapia, M.; Bennequin, D.; Goaillard, J.M. (2019). ["Topological Information Data Analysis"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7515398). *Entropy*. **21** (9). 869. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1907.04242](https://arxiv.org/abs/1907.04242). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2019Entrp..21..869B](https://ui.adsabs.harvard.edu/abs/2019Entrp..21..869B). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3390/e21090869](https://doi.org/10.3390%2Fe21090869). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [7515398](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7515398). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [195848308](https://api.semanticscholar.org/CorpusID:195848308).
15. Brenner, N.; Strong, S.; Koberle, R.; Bialek, W. (2000). "Synergy in a Neural Code". *Neural Comput*. **12** (7): 1531–1552. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1162/089976600300015259](https://doi.org/10.1162%2F089976600300015259). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [10935917](https://pubmed.ncbi.nlm.nih.gov/10935917). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [600528](https://api.semanticscholar.org/CorpusID:600528).
16. Watkinson, J.; Liang, K.; Wang, X.; Zheng, T.; Anastassiou, D. (2009). "Inference of Regulatory Gene Interactions from Expression Data Using Three-Way Mutual Information". *Chall. Syst. Biol. Ann. N. Y. Acad. Sci*. **1158** (1): 302–313. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2009NYASA1158..302W](https://ui.adsabs.harvard.edu/abs/2009NYASA1158..302W). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1111/j.1749-6632.2008.03757.x](https://doi.org/10.1111%2Fj.1749-6632.2008.03757.x). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [19348651](https://pubmed.ncbi.nlm.nih.gov/19348651). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [8846229](https://api.semanticscholar.org/CorpusID:8846229).
17. ^   Tapia, M.; Baudot, P.; Formizano-Treziny, C.; Dufour, M.; Goaillard, J.M. (2018). ["Neurotransmitter identity and electrophysiological phenotype are genetically coupled in midbrain dopaminergic neurons"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6134142). *Sci. Rep*. **8** (1): 13637. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2018NatSR...813637T](https://ui.adsabs.harvard.edu/abs/2018NatSR...813637T). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1038/s41598-018-31765-z](https://doi.org/10.1038%2Fs41598-018-31765-z). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [6134142](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6134142). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [30206240](https://pubmed.ncbi.nlm.nih.gov/30206240).
18. Christopher D. Manning; Prabhakar Raghavan; Hinrich Schütze (2008). *An Introduction to Information Retrieval*. [Cambridge University Press](https://en.wikipedia.org/wiki/Cambridge_University_Press). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-86571-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-86571-5).
19. Haghighat, M. B. A.; Aghagolzadeh, A.; Seyedarabi, H. (2011). "A non-reference image fusion metric based on mutual information of image features". *Computers & Electrical Engineering*. **37** (5): 744–756. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.compeleceng.2011.07.012](https://doi.org/10.1016%2Fj.compeleceng.2011.07.012). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [7738541](https://api.semanticscholar.org/CorpusID:7738541).
20. ["Feature Mutual Information (FMI) metric for non-reference image fusion - File Exchange - MATLAB Central"](http://www.mathworks.com/matlabcentral/fileexchange/45926-feature-mutual-information-fmi-image-fusion-metric). *www.mathworks.com*. Retrieved 4 April 2018.
21. ["InfoTopo: Topological Information Data Analysis. Deep statistical unsupervised and supervised learning - File Exchange - Github"](https://infotopo.readthedocs.io/en/latest/index.html). *github.com/pierrebaudot/infotopopy/*. Retrieved 26 September 2020.
22. Massey, James (1990). "Causality, Feedback And Directed Informatio". *Proc. 1990 Intl. Symp. on Info. Th. and its Applications, Waikiki, Hawaii, Nov. 27-30, 1990*. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.36.5688](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.36.5688).
23. Permuter, Haim Henry; Weissman, Tsachy; Goldsmith, Andrea J. (February 2009). "Finite State Channels With Time-Invariant Deterministic Feedback". *IEEE Transactions on Information Theory*. **55** (2): 644–662. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[cs/0608070](https://arxiv.org/abs/cs/0608070). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/TIT.2008.2009849](https://doi.org/10.1109%2FTIT.2008.2009849). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [13178](https://api.semanticscholar.org/CorpusID:13178).
24. .
25. ^   Press, WH; Teukolsky, SA; Vetterling, WT; Flannery, BP (2007). ["Section 14.7.3. Conditional Entropy and Mutual Information"](https://web.archive.org/web/20110811154417/http://apps.nrbook.com/empanel/index.html#pg=758). *Numerical Recipes: The Art of Scientific Computing* (3rd ed.). New York: Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-88068-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-88068-8). Archived from [the original](http://apps.nrbook.com/empanel/index.html#pg=758) on 2011-08-11. Retrieved 2011-08-13.
26. White, Jim; Steingold, Sam; Fournelle, Connie. [Performance Metrics for Group-Detection Algorithms](https://web.archive.org/web/20160705074827/http://www.interfacesymposia.org/I04/I2004Proceedings/WhiteJim/WhiteJim.paper.pdf) (PDF). Interface 2004. Archived from the original on 2016-07-05. Retrieved 2014-02-19.
27. Wijaya, Dedy Rahman; Sarno, Riyanarto; Zulaika, Enny (2017). "Information Quality Ratio as a novel metric for mother wavelet selection". *Chemometrics and Intelligent Laboratory Systems*. **160**: 59–71. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.chemolab.2016.11.012](https://doi.org/10.1016%2Fj.chemolab.2016.11.012).
28. Strehl, Alexander; Ghosh, Joydeep (2003). ["Cluster Ensembles – A Knowledge Reuse Framework for Combining Multiple Partitions"](http://www.jmlr.org/papers/volume3/strehl02a/strehl02a.pdf) (PDF). *The Journal of Machine Learning Research*. **3**: 583–617. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1162/153244303321897735](https://doi.org/10.1162%2F153244303321897735).
29. Jerdee, M., Kirkley, A. & Newman, M. Normalized mutual information is a biased measure for classification and community detection. *Nat Commun* (2025). [https://doi.org/10.1038/s41467-025-66150-8](https://doi.org/10.1038/s41467-025-66150-8) 
30. Kvålseth, T. O. (1991). "The relative useful information measure: some comments". *Information Sciences*. **56** (1): 35–38. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/0020-0255(91)90022-m](https://doi.org/10.1016%2F0020-0255%2891%2990022-m).
31. Pocock, A. (2012). [Feature Selection Via Joint Likelihood](http://www.cs.man.ac.uk/~gbrown/publications/pocockPhDthesis.pdf) (PDF) (Thesis).
32. ^   [Parsing a Natural Language Using Mutual Information Statistics](http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.78.4178&rep=rep1&type=pdf) by David M. Magerman and Mitchell P. Marcus
33. [Hugh Everett](https://en.wikipedia.org/wiki/Hugh_Everett) [Theory of the Universal Wavefunction](https://www.pbs.org/wgbh/nova/manyworlds/pdf/dissertation.pdf), Thesis, Princeton University, (1956, 1973), pp 1–140 (page 30)
34. [Everett, Hugh](https://en.wikipedia.org/wiki/Hugh_Everett) (1957). ["Relative State Formulation of Quantum Mechanics"](https://web.archive.org/web/20111027191052/http://www.univer.omsk.su/omsk/Sci/Everett/paper1957.html). *Reviews of Modern Physics*. **29** (3): 454–462. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1957RvMP...29..454E](https://ui.adsabs.harvard.edu/abs/1957RvMP...29..454E). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1103/revmodphys.29.454](https://doi.org/10.1103%2Frevmodphys.29.454). Archived from [the original](http://www.univer.omsk.su/omsk/Sci/Everett/paper1957.html) on 2011-10-27. Retrieved 2012-07-16.
35. Nicoletti, Giorgio; Busiello, Daniel Maria (2021-11-22). ["Mutual Information Disentangles Interactions from Changing Environments"](https://link.aps.org/doi/10.1103/PhysRevLett.127.228301). *Physical Review Letters*. **127** (22) 228301. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2107.08985](https://arxiv.org/abs/2107.08985). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2021PhRvL.127v8301N](https://ui.adsabs.harvard.edu/abs/2021PhRvL.127v8301N). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1103/PhysRevLett.127.228301](https://doi.org/10.1103%2FPhysRevLett.127.228301). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [34889638](https://pubmed.ncbi.nlm.nih.gov/34889638). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [236087228](https://api.semanticscholar.org/CorpusID:236087228).
36. Nicoletti, Giorgio; Busiello, Daniel Maria (2022-07-29). ["Mutual information in changing environments: Nonlinear interactions, out-of-equilibrium systems, and continuously varying diffusivities"](https://link.aps.org/doi/10.1103/PhysRevE.106.014153). *Physical Review E*. **106** (1) 014153. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2204.01644](https://arxiv.org/abs/2204.01644). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2022PhRvE.106a4153N](https://ui.adsabs.harvard.edu/abs/2022PhRvE.106a4153N). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1103/PhysRevE.106.014153](https://doi.org/10.1103%2FPhysRevE.106.014153). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [35974654](https://pubmed.ncbi.nlm.nih.gov/35974654).
37. [GlobalMIT](https://code.google.com/p/globalmit) at [Google Code](https://en.wikipedia.org/wiki/Google_Code)
38. Lee, Se Yoon (2021). "Gibbs sampler and coordinate ascent variational inference: A set-theoretical review". *Communications in Statistics - Theory and Methods*. **51** (6): 1549–1568. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2008.01006](https://arxiv.org/abs/2008.01006). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/03610926.2021.1921214](https://doi.org/10.1080%2F03610926.2021.1921214). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [220935477](https://api.semanticscholar.org/CorpusID:220935477).
39. Keys, Dustin; Kholikov, Shukur; Pevtsov, Alexei A. (February 2015). "Application of Mutual Information Methods in Time Distance Helioseismology". *Solar Physics*. **290** (3): 659–671. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1501.05597](https://arxiv.org/abs/1501.05597). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2015SoPh..290..659K](https://ui.adsabs.harvard.edu/abs/2015SoPh..290..659K). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s11207-015-0650-y](https://doi.org/10.1007%2Fs11207-015-0650-y). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [118472242](https://api.semanticscholar.org/CorpusID:118472242).
40. [Invariant Information Clustering for Unsupervised Image Classification and Segmentation](https://arxiv.org/abs/1807.06653) by Xu Ji, Joao Henriques and Andrea Vedaldi
41. Nicoletti, Giorgio; Busiello, Daniel Maria (2024-04-08). ["Information Propagation in Multilayer Systems with Higher-Order Interactions across Timescales"](https://link.aps.org/doi/10.1103/PhysRevX.14.021007). *Physical Review X*. **14** (2) 021007. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2312.06246](https://arxiv.org/abs/2312.06246). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2024PhRvX..14b1007N](https://ui.adsabs.harvard.edu/abs/2024PhRvX..14b1007N). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1103/PhysRevX.14.021007](https://doi.org/10.1103%2FPhysRevX.14.021007).

## References

- Baudot, P.; Tapia, M.; Bennequin, D.; Goaillard, J.M. (2019). ["Topological Information Data Analysis"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7515398). *Entropy*. **21** (9). 869. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1907.04242](https://arxiv.org/abs/1907.04242). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2019Entrp..21..869B](https://ui.adsabs.harvard.edu/abs/2019Entrp..21..869B). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3390/e21090869](https://doi.org/10.3390%2Fe21090869). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [7515398](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7515398). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [195848308](https://api.semanticscholar.org/CorpusID:195848308).
- Cilibrasi, R.; Vitányi, Paul (2005). ["Clustering by compression"](http://www.cwi.nl/~paulv/papers/cluster.pdf) (PDF). *IEEE Transactions on Information Theory*. **51** (4): 1523–1545. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[cs/0312044](https://arxiv.org/abs/cs/0312044). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/TIT.2005.844059](https://doi.org/10.1109%2FTIT.2005.844059). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [911](https://api.semanticscholar.org/CorpusID:911).
- Cronbach, L. J. (1954). "On the non-rational application of information measures in psychology". In [Quastler, Henry](https://en.wikipedia.org/wiki/Henry_Quastler) (ed.). *Information Theory in Psychology: Problems and Methods*. Glencoe, Illinois: Free Press. pp. 14–30.
- Coombs, C. H.; Dawes, R. M.; Tversky, A. (1970). *Mathematical Psychology: An Elementary Introduction*. Englewood Cliffs, New Jersey: Prentice-Hall.
- Church, Kenneth Ward; Hanks, Patrick (1989). ["Word association norms, mutual information, and lexicography"](https://doi.org/10.3115%2F981623.981633). *Proceedings of the 27th Annual Meeting of the Association for Computational Linguistics*. **16** (1): 76–83. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3115/981623.981633](https://doi.org/10.3115%2F981623.981633).
- Gel'fand, I.M.; Yaglom, A.M. (1957). "Calculation of amount of information about a random function contained in another such function". *American Mathematical Society Translations*. Series 2. **12**: 199–246. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1090/trans2/012/09](https://doi.org/10.1090%2Ftrans2%2F012%2F09). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8218-1712-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8218-1712-4). `{{`[`cite journal`](https://en.wikipedia.org/wiki/Template:Cite_journal)`}}`: ISBN / Date incompatibility ([help](https://en.wikipedia.org/wiki/Help:CS1_errors#invalid_isbn_date)) English translation of original in *Uspekhi Matematicheskikh Nauk* **12** (1): 3-52.
- Guiasu, Silviu (1977). *Information Theory with Applications*. McGraw-Hill, New York. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-07-025109-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-07-025109-0).
- Li, Ming; Vitányi, Paul (February 1997). *An introduction to Kolmogorov complexity and its applications*. New York: [Springer-Verlag](https://en.wikipedia.org/wiki/Springer-Verlag). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-94868-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-94868-3).
- Lockhead, G. R. (1970). "Identification and the form of multidimensional discrimination space". *Journal of Experimental Psychology*. **85** (1): 1–10. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1037/h0029508](https://doi.org/10.1037%2Fh0029508). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [5458322](https://pubmed.ncbi.nlm.nih.gov/5458322).
- David J. C. MacKay. *[Information Theory, Inference, and Learning Algorithms](http://www.inference.phy.cam.ac.uk/mackay/itila/book.html)* Cambridge: Cambridge University Press, 2003. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-64298-1](https://en.wikipedia.org/wiki/Special:BookSources/0-521-64298-1) (available free online)
- Haghighat, M. B. A.; Aghagolzadeh, A.; Seyedarabi, H. (2011). "A non-reference image fusion metric based on mutual information of image features". *Computers & Electrical Engineering*. **37** (5): 744–756. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.compeleceng.2011.07.012](https://doi.org/10.1016%2Fj.compeleceng.2011.07.012). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [7738541](https://api.semanticscholar.org/CorpusID:7738541).
- [Athanasios Papoulis](https://en.wikipedia.org/wiki/Athanasios_Papoulis). *Probability, Random Variables, and Stochastic Processes*, second edition. New York: McGraw-Hill, 1984. *(See Chapter 15.)*
- Witten, Ian H. & Frank, Eibe (2005). [Data Mining: Practical Machine Learning Tools and Techniques](http://www.cs.waikato.ac.nz/~ml/weka/book.html). Morgan Kaufmann, Amsterdam. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-12-374856-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-12-374856-0).
- Peng, H.C.; Long, F. & Ding, C. (2005). ["Feature selection based on mutual information: criteria of max-dependency, max-relevance, and min-redundancy"](http://research.janelia.org/peng/proj/mRMR/index.htm). *IEEE Transactions on Pattern Analysis and Machine Intelligence*. **27** (8): 1226–1238. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.63.5765](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.63.5765). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/tpami.2005.159](https://doi.org/10.1109%2Ftpami.2005.159). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [16119262](https://pubmed.ncbi.nlm.nih.gov/16119262). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [206764015](https://api.semanticscholar.org/CorpusID:206764015).
- Andre S. Ribeiro; Stuart A. Kauffman; Jason Lloyd-Price; Bjorn Samuelsson & Joshua Socolar (2008). "Mutual Information in Random Boolean models of regulatory networks". *Physical Review E*. **77** (1) 011901. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[0707.3642](https://arxiv.org/abs/0707.3642). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2008PhRvE..77a1901R](https://ui.adsabs.harvard.edu/abs/2008PhRvE..77a1901R). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1103/physreve.77.011901](https://doi.org/10.1103%2Fphysreve.77.011901). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [18351870](https://pubmed.ncbi.nlm.nih.gov/18351870). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [15232112](https://api.semanticscholar.org/CorpusID:15232112).
- Wells, W.M. III; Viola, P.; Atsumi, H.; Nakajima, S.; Kikinis, R. (1996). ["Multi-modal volume registration by maximization of mutual information"](https://web.archive.org/web/20080906201633/http://www.ai.mit.edu/people/sw/papers/mia.pdf) (PDF). *Medical Image Analysis*. **1** (1): 35–51. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/S1361-8415(01)80004-9](https://doi.org/10.1016%2FS1361-8415%2801%2980004-9). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [9873920](https://pubmed.ncbi.nlm.nih.gov/9873920). Archived from [the original](http://www.ai.mit.edu/people/sw/papers/mia.pdf) (PDF) on 2008-09-06. Retrieved 2010-08-05.
- Pandey, Biswajit; Sarkar, Suman (2017). ["How much a galaxy knows about its large-scale environment?: An information theoretic perspective"](https://doi.org/10.1093%2Fmnrasl%2Fslw250). *Monthly Notices of the Royal Astronomical Society Letters*. **467** (1): L6. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1611.00283](https://arxiv.org/abs/1611.00283). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2017MNRAS.467L...6P](https://ui.adsabs.harvard.edu/abs/2017MNRAS.467L...6P). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1093/mnrasl/slw250](https://doi.org/10.1093%2Fmnrasl%2Fslw250). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [119095496](https://api.semanticscholar.org/CorpusID:119095496).

- Janssen, Joseph; Guan, Vincent; Robeva, Elina (2023). ["Ultra-marginal Feature Importance: Learning from Data with Causal Guarantees"](https://proceedings.mlr.press/v206/janssen23a.html). *International Conference on Artificial Intelligence and Statistics*: 10782–10814. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2204.09938](https://arxiv.org/abs/2204.09938).
