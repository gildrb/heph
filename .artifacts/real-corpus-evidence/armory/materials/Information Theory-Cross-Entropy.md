[[information-theory.base]]

> Source: [[Cross-Entropy]]
> License: Wikipedia content is available under CC BY-SA 4.0.

In [information theory](https://en.wikipedia.org/wiki/Information_theory), the **cross-entropy** between two [probability distributions](https://en.wikipedia.org/wiki/Probability_distribution) $p$ and $q$, over the same underlying set of events, measures the average number of [bits](https://en.wikipedia.org/wiki/Bit) needed to identify an event drawn from the set when the coding scheme used for the set is optimized for an estimated probability distribution $q$, rather than the true distribution $p$.

## Definition

The cross-entropy of the distribution $q$ relative to a distribution $p$ over a given set is defined as follows:

$$
H(p,q)=-\operatorname {E} _{p}[\log q],
$$

where $\operatorname {E} _{p}[\cdot ]$ is the [expected value](https://en.wikipedia.org/wiki/Expected_value) operator with respect to the distribution $p$.

The definition may be formulated using the [[Kullback-Leibler Divergence|Kullback–Leibler divergence]] $D_{\mathrm {KL} }(p\parallel q)$, divergence of $p$ from $q$ (also known as the *relative entropy* of $p$ with respect to $q$).

$$
H(p,q)=H(p)+D_{\mathrm {KL} }(p\parallel q),
$$

where $H(p)$ is the [entropy](https://en.wikipedia.org/wiki/Information_entropy) of $p$.

For [discrete](https://en.wikipedia.org/wiki/Discrete_random_variable) probability distributions $p$ and $q$ with the same [support](https://en.wikipedia.org/wiki/Support_(mathematics) "Support (mathematics)") ${\mathcal {X}}$, this means

$H(p,q)=-\sum _{x\in {\mathcal {X}}}p(x)\,\log q(x).$   (Eq. 1)

The situation for [continuous](https://en.wikipedia.org/wiki/Continuous_random_variable) distributions is analogous. We have to assume that $p$ and $q$ are [absolutely continuous](https://en.wikipedia.org/wiki/Absolutely_continuous) with respect to some reference [measure](https://en.wikipedia.org/wiki/Measure_(mathematics) "Measure (mathematics)") $r$ (usually $r$ is a [Lebesgue measure](https://en.wikipedia.org/wiki/Lebesgue_measure) on a [Borel](https://en.wikipedia.org/wiki/Borel_set) [[Sigma Algebra|σ-algebra]]). Let $P$ and $Q$ be [[Probability Density Function|probability density functions]] of $p$ and $q$ with respect to $r$. Then

$$
-\int _{\mathcal {X}}P(x)\,\log Q(x)\,\mathrm {d} x=\operatorname {E} _{p}[-\log Q],
$$

and therefore

$H(p,q)=-\int _{\mathcal {X}}P(x)\,\log Q(x)\,\mathrm {d} x.$   (Eq. 2)

NB: The notation $H(p,q)$ is also used for a different concept, the [joint entropy](https://en.wikipedia.org/wiki/Joint_entropy) of $p$ and $q$.

## Motivation

In [information theory](https://en.wikipedia.org/wiki/Information_theory), the [Kraft–McMillan theorem](https://en.wikipedia.org/wiki/Kraft%27s_inequality) establishes that any directly decodable coding scheme for coding a message to identify one value $x_{i}$ out of a set of possibilities $\{x_{1},\ldots ,x_{n}\}$ can be seen as representing an implicit probability distribution $q(x_{i})=\left({\frac {1}{2}}\right)^{\ell _{i}}$ over $\{x_{1},\ldots ,x_{n}\}$, where $\ell _{i}$ is the length of the code for $x_{i}$ in bits. Therefore, cross-entropy can be interpreted as the expected message-length per datum when a wrong distribution $q$ is assumed while the data actually follows a distribution $p$. That is why the expectation is taken over the true probability distribution $p$ and not $q.$ Indeed the expected message-length under the true distribution $p$ is

$$
{\begin{aligned}\operatorname {E} _{p}[\ell ]&=-\operatorname {E} _{p}\left[{\frac {\ln {q(x)}}{\ln(2)}}\right]\\[1ex]&=-\operatorname {E} _{p}\left[\log _{2}{q(x)}\right]\\[1ex]&=-\sum _{x_{i}}p(x_{i})\,\log _{2}q(x_{i})\\[1ex]&=-\sum _{x}p(x)\,\log _{2}q(x)=H(p,q).\end{aligned}}
$$

## Estimation

There are many situations where cross-entropy needs to be measured but the distribution of $p$ is unknown. An example is [language modeling](https://en.wikipedia.org/wiki/Language_model), where a model is created based on a training set $T$, and then its cross-entropy is measured on a test set to assess how accurate the model is in predicting the test data. In this example, $p$ is the true distribution of words in any corpus, and $q$ is the distribution of words as predicted by the model. Since the true distribution is unknown, cross-entropy cannot be directly calculated. In these cases, an estimate of cross-entropy is calculated using the following formula:

$$
H(T,q)=-\sum _{i=1}^{N}{\frac {1}{N}}\log _{2}q(x_{i})
$$

where $N$ is the size of the test set, and $q(x)$ is the probability of event $x$ estimated from the training set. In other words, $q(x_{i})$ is the probability estimate of the model that the i-th word of the text is $x_{i}$. The sum is averaged over the $N$ words of the test. This is a [[Monte Carlo Method|Monte Carlo estimate]] of the true cross-entropy, where the test set is treated as samples from $p(x)$.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

## Relation to maximum likelihood

The cross entropy arises in classification problems when introducing a logarithm in the guise of the [log-likelihood](https://en.wikipedia.org/wiki/Likelihood_function#Log-likelihood) function.

This section concerns the estimation of the probabilities of different discrete outcomes. To this end, denote a parametrized family of distributions by $q_{\theta }$, with $\theta$ subject to the optimization effort. Consider a given finite sequence of $N$ values $x_{i}$ from a training set, obtained from [conditionally independent](https://en.wikipedia.org/wiki/Conditionally_independent) sampling. The likelihood assigned to any considered parameter $\theta$ of the model is then given by the product over all probabilities $q_{\theta }(X=x_{i})$. Repeated occurrences are possible, leading to equal factors in the product. If the count of occurrences of the value equal to $x$ is denoted by $\#x$, then the frequency of that value equals $\#x/N$. If $p(X=x)$ is the underlying probability distribution, for large $N$ we expect $p(X=x)\approx \#x/N$, by [[Law of Large Numbers|the law of large numbers]].

Writing our likelihood function as the product of observations from the distribution $q_{\theta }$: 

$$
{\begin{aligned}{\mathcal {L}}(\theta ;{\mathbf {x} })&=\prod _{i}q_{\theta }(X=x_{i})=\prod _{x}q_{\theta }(X=x)^{\#x}\\&\approx \prod _{x}q_{\theta }(X=x)^{N\cdot p(X=x)}=\exp \log \left[\prod _{x}q_{\theta }(X=x)^{N\cdot p(X=x)}\right]\\&=\exp \left(\sum _{x}N\cdot p(X=x)\log q_{\theta }(X=x)^{}\right),\end{aligned}}
$$

 where we have used the [calculation rules for the logarithm](https://en.wikipedia.org/wiki/List_of_logarithmic_identities) in the final line. Notice how the exponent equals $-H(p,q_{\theta })$. Taking the logarithm of both sides gives: 

$$
\log {\mathcal {L}}(\theta ;{\mathbf {x} })=-N\cdot H(p,q_{\theta }).
$$

 Since the logarithm is a [monotonically increasing function](https://en.wikipedia.org/wiki/Monotonic_function), the maximizing value of $\theta$ is unaffected by this final step. Similarly, the maximizing value of $\theta$ is unaffected by the factor of $N$. So we observe that the [[Maximum Likelihood Estimation|likelihood maximization]] amounts to minimization of the cross-entropy.

## Cross-entropy minimization

Cross-entropy minimization is frequently used in optimization and rare-event probability estimation. When comparing a distribution $q$ against a fixed reference distribution $p$, cross-entropy and [[Kullback-Leibler Divergence|KL divergence]] are identical up to an additive constant (since $p$ is fixed): According to the [Gibbs' inequality](https://en.wikipedia.org/wiki/Gibbs%27_inequality), both take on their minimal values when $p=q$, which is $0$ for KL divergence, and $\mathrm {H} (p)$ for cross-entropy. In the engineering literature, the principle of minimizing KL divergence (Kullback's "[[Kullback-Leibler Divergence|Principle of Minimum Discrimination Information]]") is often called the **Principle of Minimum Cross-Entropy** (MCE), or **Minxent**.

However, as discussed in the article *[[Kullback-Leibler Divergence|Kullback–Leibler divergence]]*, sometimes the distribution $q$ is the fixed prior reference distribution, and the distribution $p$ is optimized to be as close to $q$ as possible, subject to some constraint. In this case the two minimizations are *not* equivalent. This has led to some ambiguity in the literature, with some authors attempting to resolve the inconsistency by restating cross-entropy to be $D_{\mathrm {KL} }(p\parallel q)$, rather than $H(p,q)$. In fact, cross-entropy is another name for [relative entropy](https://en.wikipedia.org/wiki/Relative_entropy); see Cover and Thomas and Good. On the other hand, $H(p,q)$ does not agree with the literature and can be misleading.

## Cross-entropy loss function and logistic regression

Cross-entropy can be used to define a loss function in [machine learning](https://en.wikipedia.org/wiki/Machine_learning) and [optimization](https://en.wikipedia.org/wiki/Optimization). Mao, Mohri, and Zhong (2023) give an extensive analysis of the properties of the family of cross-entropy loss functions in machine learning, including theoretical learning guarantees and extensions to [adversarial learning](https://en.wikipedia.org/wiki/Adversarial_machine_learning). The true probability $p_{i}$ is the true label, and the given distribution $q_{i}$ is the predicted value of the current model. This is also known as the **log loss** (or **logarithmic loss** or **[logistic loss](https://en.wikipedia.org/wiki/Logistic_loss)**); the terms "log loss" and "cross-entropy loss" are used interchangeably.

More specifically, consider a [binary regression](https://en.wikipedia.org/wiki/Binary_regression) model which can be used to classify observations into two possible classes (often simply labelled $0$ and $1$). The output of the model for a given observation, given a vector of input features $x$, can be interpreted as a probability, which serves as the basis for classifying the observation. In [logistic regression](https://en.wikipedia.org/wiki/Logistic_regression), the probability is modeled using the [logistic function](https://en.wikipedia.org/wiki/Logistic_function) $g(z)=1/(1+e^{-z})$ where $z$ is some function of the input vector $x$, commonly just a linear function. The probability of the output $y=1$ is given by 

$$
q_{y=1}={\hat {y}}\equiv g(\mathbf {w} \cdot \mathbf {x} )={\frac {1}{1+e^{-\mathbf {w} \cdot \mathbf {x} }}},
$$

 where the vector of weights $\mathbf {w}$ is optimized through some appropriate algorithm such as [[Gradient Descent]]. Similarly, the complementary probability of finding the output $y=0$ is simply given by 

$$
q_{y=0}=1-{\hat {y}}.
$$

Having set up our notation, $p\in \{y,1-y\}$ and $q\in \{{\hat {y}},1-{\hat {y}}\}$, we can use cross-entropy to get a measure of dissimilarity between $p$ and $q$: 

$$
{\begin{aligned}H(p,q)&=-\sum _{m}p_{m}\log q_{m}=-y\log {\hat {y}}-(1-y)\log(1-{\hat {y}}).\end{aligned}}
$$

![[media/17a990126c9c33aa1a86cf5d62ec0c4915c62159.png]]
Plot shows different loss functions that can be used to train a binary classifier. Only the case where the target output is 1 is shown. It is observed that the loss is zero when the target is equal to the output and increases as the output becomes increasingly incorrect.

Logistic regression typically optimizes the log loss for all the observations on which it is trained, which is the same as optimizing the average cross-entropy in the sample. Other loss functions that penalize errors differently can be also used for training, resulting in models with different final test accuracy. For example, suppose we have $N$ samples with each sample indexed by $n=1,\dots ,N$. The *average* of the loss function is then given by

$$
{\begin{aligned}J(\mathbf {w} )&={\frac {1}{N}}\sum _{i=1}^{N}H(p_{i},q_{i})\\&=-{\frac {1}{N}}\sum _{i=1}^{N}\ \left[y_{i}\log {\hat {y}}_{i}+(1-y_{i})\log(1-{\hat {y}}_{i})\right],\end{aligned}}
$$

where ${\hat {y}}_{i}\equiv g(\mathbf {w} \cdot \mathbf {x} _{i})=1/(1+e^{-\mathbf {w} \cdot \mathbf {x} _{i}})$, with $g(z)$ as the logistic function as before.

## Relation to linear regression

The gradient of the cross-entropy loss for logistic regression is equal to the gradient of the squared-error loss for [linear regression](https://en.wikipedia.org/wiki/Linear_regression) (up to a constant factor). To see this, define

$$
X\equiv {\begin{pmatrix}1&x_{11}&\dots &x_{1p}\\1&x_{21}&\cdots &x_{2p}\\\vdots &\vdots &&\vdots \\1&x_{N1}&\cdots &x_{Np}\\\end{pmatrix}}\in \mathbb {R} ^{N\times (p+1)},
$$

$$
{\hat {y_{i}}}=g(\mathbf {w} \cdot X^{i})={\frac {1}{1+\exp(-w_{0}-w_{1}x_{i1}-\dots -w_{p}x_{ip})}},
$$

$$
L(\mathbf {w} )\equiv -\sum _{i=1}^{N}\left[y_{i}\ln {\hat {y}}_{i}+(1-y_{i})\ln(1-{\hat {y}}_{i})\right].
$$

Then we have the result

$$
\nabla _{\mathbf {w} }L(\mathbf {w} )=X^{\mathsf {T}}({\hat {\mathbf {y} }}-\mathbf {y} ).
$$

**Proof:** For any ${\hat {y}}_{i}$ we have

$$
{\frac {\partial }{\partial w_{0}}}\ln {\hat {y}}_{i}={\frac {\partial }{\partial w_{0}}}\ln {\frac {1}{1+e^{-w_{0}+k_{0}}}}={\frac {e^{-w_{0}+k_{0}}}{1+e^{-w_{0}+k_{0}}}}=1-{\hat {y}}_{i},
$$

$$
{\frac {\partial }{\partial w_{0}}}\ln(1-{\hat {y}}_{i})={\frac {\partial }{\partial w_{0}}}\ln \left(1-{\frac {1}{1+e^{-w_{0}+k_{0}}}}\right)={\frac {-1}{1+e^{-w_{0}+k_{0}}}}=-{\hat {y}}_{i}
$$

 and thus 

$$
{\begin{aligned}{\frac {\partial L}{\partial w_{0}}}&=-\sum _{i=1}^{N}[y_{i}(1-{\hat {y}}_{i})-(1-y_{i}){\hat {y}}_{i}]=-\sum _{i=1}^{N}[y_{i}-{\hat {y}}_{i}]=\sum _{i=1}^{N}X_{i0}({\hat {y}}_{i}-y_{i}).\end{aligned}}
$$

Similarly, for any ${\hat {y}}_{i}$ and $j=1,\dots ,p$ we have 

$$
{\frac {\partial }{\partial w_{j}}}\ln {\hat {y}}_{i}={\frac {\partial }{\partial w_{j}}}\ln {\frac {1}{1+e^{-w_{j}x_{ij}+k_{j}}}}={\frac {x_{ij}e^{-w_{j}x_{ij}+k_{j}}}{1+e^{-w_{j}x_{ij}+k_{j}}}}=x_{ij}(1-{\hat {y}}_{i}),
$$

$$
{\frac {\partial }{\partial w_{j}}}\ln(1-{\hat {y}}_{i})={\frac {\partial }{\partial w_{j}}}\ln \left[1-{\frac {1}{1+e^{-w_{j}x_{ij}+k_{j}}}}\right]={\frac {-x_{ij}}{1+e^{-w_{j}x_{ij}+k_{j}}}}=-x_{ij}{\hat {y}}_{i}
$$

 and thus 

$$
{\begin{aligned}{\frac {\partial L}{\partial w_{j}}}&=-\sum _{i=1}^{N}x_{ij}[y_{i}(1-{\hat {y}}_{i})-(1-y_{i}){\hat {y}}_{i}]=\sum _{i=1}^{N}X_{ij}({\hat {y}}_{i}-y_{i}).\end{aligned}}
$$

Put together, we obtain the desired result. Note that here we used the natural logarithm $ln$ instead of $log$ (canonically $log_{2}$) in the loss function $L$. This merely changes the result by a factor of $log(e)$ though. Moreover, for all $i$ we reused $k_{0}:=-\sum _{l=1}^{p}w_{l}x_{il}$ and $k_{j}:=-w_{0}-\sum _{l\neq j}w_{l}x_{il}$ as constants w.r.t. each $w_{j}$.

## Amended cross-entropy

It may be beneficial to train an ensemble of models that have diversity, such that when they are combined, their predictive accuracy is augmented. Assuming a simple ensemble of $K$ classifiers is assembled via averaging the outputs, then the amended cross-entropy is given by 

$$
e^{k}=H(p,q^{k})-{\frac {\lambda }{K}}\sum _{j\neq k}H(q^{j},q^{k})
$$

 where $e^{k}$ is the cost function of the $k^{th}$ classifier, $q^{k}$ is the output probability of the $k^{th}$ classifier, $p$ is the true probability to be estimated, and $\lambda$ is a parameter between 0 and 1 that defines the 'diversity' that we would like to establish among the ensemble. When $\lambda =0$ we want each classifier to do its best regardless of the ensemble and when $\lambda =1$ we would like the classifier to be as diverse as possible.

## See also

- [Cross-entropy method](https://en.wikipedia.org/wiki/Cross-entropy_method)
- [Logistic regression](https://en.wikipedia.org/wiki/Logistic_regression)
- [Conditional entropy](https://en.wikipedia.org/wiki/Conditional_entropy)
- [Kullback–Leibler distance](https://en.wikipedia.org/wiki/Kullback%E2%80%93Leibler_distance)
- [[Maximum Likelihood Estimation|Maximum-likelihood estimation]]
- [[Mutual Information]]
- [Perplexity](https://en.wikipedia.org/wiki/Perplexity)

## References

1.  Thomas M. Cover, Joy A. Thomas, Elements of Information Theory, 2nd Edition, Wiley, p. 80
2.  I. J. Good, Maximum entropy for hypothesis formulation, especially for multidimensional contingency tables, Ann. of Math. Statistics, 1963
3.  Anqi Mao, Mehryar Mohri, Yutao Zhong. Cross-entropy loss functions: Theoretical analysis and applications. ICML 2023. [https://arxiv.org/pdf/2304.07288.pdf](https://arxiv.org/pdf/2304.07288.pdf)
4.  *The Mathematics of Information Coding, Extraction and Distribution*, by George Cybenko, Dianne P. O'Leary, Jorma Rissanen, 1999, [p. 82](https://books.google.com/books?id=jDrp4QEGioMC&dq=%22logarithmic+loss%22+%22log+loss%22&pg=PA82)
5.  *Probability for Machine Learning: Discover How To Harness Uncertainty With Python*, Jason Brownlee, 2019, p. 220: "Logistic loss refers to the loss function commonly used to optimize a logistic regression model. It may also be referred to as logarithmic loss (which is confusing) or simply log loss."
6.  ["sklearn.metrics.log_loss"](https://scikit-learn.org/1.7/modules/generated/sklearn.metrics.log_loss.html). *API Reference — scikit-learn 1.7.1 documentation*.
7.  Noel, Mathew; Banerjee, Arindam; D, Geraldine Bessie Amali; Muthiah-Nakarajan, Venkataraman (March 17, 2023). "Alternate loss functions for classification and robust regression can improve the accuracy of artificial neural networks". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2303.09935](https://arxiv.org/abs/2303.09935) \[[cs.NE](https://arxiv.org/archive/cs.NE)\].
8.  Shoham, Ron; Permuter, Haim H. (2019). "Amended Cross-Entropy Cost: An Approach for Encouraging Diversity in Classification Ensemble (Brief Announcement)". In Dolev, Shlomi; Hendler, Danny; Lodha, Sachin; Yung, Moti (eds.). *Cyber Security Cryptography and Machine Learning – Third International Symposium, CSCML 2019, Beer-Sheva, Israel, June 27–28, 2019, Proceedings*. Lecture Notes in Computer Science. Vol. 11527. Springer. pp. 202–207. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-3-030-20951-3_18](https://doi.org/10.1007%2F978-3-030-20951-3_18). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-030-20950-6](https://en.wikipedia.org/wiki/Special:BookSources/978-3-030-20950-6).
9.  Shoham, Ron; Permuter, Haim (2020). "Amended Cross Entropy Cost: Framework For Explicit Diversity Encouragement". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2007.08140](https://arxiv.org/abs/2007.08140) \[[cs.LG](https://arxiv.org/archive/cs.LG)\].

## Further reading

- de Boer, Kroese, D.P., Mannor, S. and Rubinstein, R.Y. (2005). [A tutorial on the cross-entropy method](https://link.springer.com/article/10.1007/s10479-005-5724-z). *Annals of Operations Research* 134 (1), 19–67.
