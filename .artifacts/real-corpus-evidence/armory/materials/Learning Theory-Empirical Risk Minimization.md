[[learning-theory.base]]

> Source: [[Empirical Risk Minimization]]
> License: Wikipedia content is available under CC BY-SA 4.0.

In [[Statistical Learning Theory]], the principle of **empirical risk minimization** defines a family of [learning algorithms](https://en.wikipedia.org/wiki/Machine_learning) based on evaluating performance over a known and fixed dataset. The core idea is based on an application of the [[Law of Large Numbers]]; more specifically, we cannot know exactly how well a predictive algorithm will work in practice (i.e. the "true risk") because we do not know the true distribution of the data, but we can instead [estimate](https://en.wikipedia.org/wiki/Estimation_statistics) and optimize the performance of the algorithm on a known set of training data. The performance over the known set of training data is referred to as the "empirical risk".

## Background

The following situation is a general setting of many [supervised learning](https://en.wikipedia.org/wiki/Supervised_learning) problems. There are two spaces of objects $X$ and $Y$ and we would like to learn a function $\ h:X\to Y$ (often called *hypothesis*) which outputs an object $y\in Y$, given $x\in X$. To do so, there is a *training set* of $n$ examples $\ (x_{1},y_{1}),\ldots ,(x_{n},y_{n})$ where $x_{i}\in X$ is an input and $y_{i}\in Y$ is the corresponding response that is desired from $h(x_{i})$.

To put it more formally, assuming that there is a [joint probability distribution](https://en.wikipedia.org/wiki/Joint_probability_distribution) $P(x,y)$ over $X$ and $Y$, and that the training set consists of $n$ instances $\ (x_{1},y_{1}),\ldots ,(x_{n},y_{n})$ drawn [i.i.d.](https://en.wikipedia.org/wiki/I.i.d.) from $P(x,y)$. The assumption of a joint probability distribution allows for the modelling of uncertainty in predictions (e.g. from noise in data) because $y$ is not a deterministic function of $x$, but rather a [random variable](https://en.wikipedia.org/wiki/Random_variable) with [conditional distribution](https://en.wikipedia.org/wiki/Conditional_distribution) $P(y|x)$ for a fixed $x$.

It is also assumed that there is a non-negative real-valued [loss function](https://en.wikipedia.org/wiki/Loss_function) $L({\hat {y}},y)$ which measures how different the prediction ${\hat {y}}$ of a hypothesis is from the true outcome $y$. For classification tasks, these loss functions can be [scoring rules](https://en.wikipedia.org/wiki/Scoring_rule). The [risk](https://en.wikipedia.org/wiki/Risk_(statistics)) associated with hypothesis $h(x)$ is then defined as the [expectation](https://en.wikipedia.org/wiki/Expected_value) of the loss function:

$R(h)=\mathbf {E} [L(h(x),y)]=\int L(h(x),y)\,dP(x,y).$

A loss function commonly used in theory is the [0-1 loss function](https://en.wikipedia.org/wiki/0-1_loss_function): $L({\hat {y}},y)={\begin{cases}1&{\mbox{ if }}\quad {\hat {y}}\neq y\\0&{\mbox{ if }}\quad {\hat {y}}=y\end{cases}}$.

The ultimate goal of a learning algorithm is to find a hypothesis $h^{*}$ among a fixed class of functions ${\mathcal {H}}$ for which the risk $R(h)$ is minimal:

$h^{*}={\underset {h\in {\mathcal {H}}}{\operatorname {arg\,min} }}\,{R(h)}.$

For classification problems, the [Bayes classifier](https://en.wikipedia.org/wiki/Bayes_classifier) is defined to be the classifier minimizing the risk defined with the 0–1 loss function.

## Formal definition

In general, the risk $R(h)$ cannot be computed because the distribution $P(x,y)$ is unknown to the learning algorithm. However, given a sample of [iid](https://en.wikipedia.org/wiki/Independent_and_identically_distributed_random_variables) training data points, we can compute an [estimate](https://en.wikipedia.org/wiki/Estimate_(statistics)), called the *empirical risk*, by computing the average of the loss function over the training set; more formally, computing the expectation with respect to the [empirical measure](https://en.wikipedia.org/wiki/Empirical_measure):

$\!R_{\text{emp}}(h)={\frac {1}{n}}\sum _{i=1}^{n}L(h(x_{i}),y_{i}).$

The empirical risk minimization principle states that the learning algorithm should choose a hypothesis ${\hat {h}}$ which minimizes the empirical risk over the hypothesis class ${\mathcal {H}}$:

${\hat {h}}={\underset {h\in {\mathcal {H}}}{\operatorname {arg\,min} }}\,R_{\text{emp}}(h).$

Thus, the learning algorithm defined by the empirical risk minimization principle consists in solving the above [optimization](https://en.wikipedia.org/wiki/Mathematical_optimization) problem.

## Properties

Guarantees for the performance of empirical risk minimization depend strongly on the function class selected as well as the distributional assumptions made. In general, distribution-free methods are too coarse, and do not lead to practical bounds. However, they are still useful in deriving asymptotic properties of learning algorithms, such as [consistency](https://en.wikipedia.org/wiki/Consistency_(statistics) "Consistency (statistics)"). In particular, distribution-free bounds on the performance of empirical risk minimization given a fixed function class can be derived using bounds on the [VC complexity](https://en.wikipedia.org/wiki/Vapnik%E2%80%93Chervonenkis_dimension) of the function class.

For simplicity, considering the case of binary classification tasks, it is possible to bound the probability of the selected classifier, $\phi _{n}$ being much worse than the best possible classifier $\phi ^{*}$. Consider the risk $L$ defined over the hypothesis class ${\mathcal {C}}$ with [growth function](https://en.wikipedia.org/wiki/Growth_function) ${\mathcal {S}}({\mathcal {C}},n)$ given a dataset of size $n$. Then, for every $\epsilon >0$:

$$
\mathbb {P} \left(L(\phi _{n})-L(\phi ^{*})>\epsilon \right)\leq {\mathcal {8}}S({\mathcal {C}},n)\exp\{-n\epsilon ^{2}/32\}
$$

Similar results hold for regression tasks. These results are often based on [uniform laws of large numbers](https://en.wikipedia.org/wiki/Uniform_law_of_large_numbers), which control the deviation of the empirical risk from the true risk, uniformly over the hypothesis class.

### Impossibility results

It is also possible to show lower bounds on algorithm performance if no distributional assumptions are made. This is sometimes referred to as the *[[No Free Lunch Theorem]]*. Even though a specific learning algorithm may provide the asymptotically optimal performance for any distribution, the finite sample performance is always poor for at least one data distribution. This means that no classifier can improve on the error for a given sample size for all distributions.

Specifically, let $\epsilon >0$ and consider a sample size $n$ and classification rule $\phi _{n}$, there exists a distribution of $(X,Y)$ with risk $L^{*}=0$ (meaning that perfect prediction is possible) such that: 

$$
\mathbb {E} L_{n}\geq 1/2-\epsilon .
$$

It is further possible to show that the convergence rate of a learning algorithm is poor for some distributions. Specifically, given a sequence of decreasing positive numbers $a_{i}$ converging to zero, it is possible to find a distribution such that:

$$
\mathbb {E} L_{n}\geq a_{i}
$$

for all $n$. This result shows that universally good classification rules do not exist, in the sense that the rule must be low quality for at least one distribution.

### Computational complexity

Empirical risk minimization for a classification problem with a [0-1 loss function](https://en.wikipedia.org/wiki/0-1_loss_function) is known to be an [NP-hard](https://en.wikipedia.org/wiki/NP-hard) problem even for a relatively simple class of functions such as [linear classifiers](https://en.wikipedia.org/wiki/Linear_classifier). Nevertheless, it can be solved efficiently when the minimal empirical risk is zero, i.e., data is [linearly separable](https://en.wikipedia.org/wiki/Linearly_separable).<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

In practice, machine learning algorithms cope with this issue either by employing a [[Convex Optimization|convex approximation]] to the 0–1 loss function (like [hinge loss](https://en.wikipedia.org/wiki/Hinge_loss) for [SVM](https://en.wikipedia.org/wiki/Support_vector_machine)), which is easier to optimize, or by imposing assumptions on the distribution $P(x,y)$ (and thus stop being agnostic learning algorithms to which the above result applies).

In the case of convexification, Zhang's lemma majors<sup>\[*[clarify](https://en.wikipedia.org/wiki/Wikipedia:Please_clarify)*\]</sup> the excess risk of the original problem using the excess risk of the convexified problem. Minimizing the latter using convex optimization also allow to control the former.

## Tilted empirical risk minimization

Tilted empirical risk minimization is a machine learning technique used to modify standard loss functions like squared error, by introducing a tilt parameter. This parameter dynamically adjusts the weight of data points during training, allowing the algorithm to focus on specific regions or characteristics of the data distribution. Tilted empirical risk minimization is particularly useful in scenarios with imbalanced data or when there is a need to emphasize errors in certain parts of the prediction space.

## See also

- [M-estimator](https://en.wikipedia.org/wiki/M-estimator)
- [[Maximum Likelihood Estimation]]

## References

1.  V. Vapnik (1992). [Principles of Risk Minimization for Learning Theory.](https://papers.nips.cc/paper_files/paper/1991/file/ff4d5fbbafdf976cfdc032e3bde78de5-Paper.pdf)
2.  ^   Györfi, László; Kohler, Michael; Krzyzak, Adam; Walk, Harro (2010-12-01). *A Distribution-Free Theory of Nonparametric Regression* (Softcover reprint of the original 1st ed.). New York: Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4419-2998-3](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4419-2998-3).
3.  ^      Devroye, L., Gyorfi, L. & Lugosi, G. A Probabilistic Theory of Pattern Recognition. Discrete Appl Math 73, 192–194 (1997)
4.  Devroye, Luc; Györfi, László; Lugosi, Gábor (1996). ["A Probabilistic Theory of Pattern Recognition"](https://link.springer.com/book/10.1007/978-1-4612-0711-5). *Stochastic Modelling and Applied Probability*. **31**. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-1-4612-0711-5](https://doi.org/10.1007%2F978-1-4612-0711-5). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4612-6877-2](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4612-6877-2). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0172-4568](https://search.worldcat.org/issn/0172-4568).
5.  V. Feldman, V. Guruswami, P. Raghavendra and Yi Wu (2009). [Agnostic Learning of Monomials by Halfspaces is Hard.](https://arxiv.org/abs/1012.0729) (See the paper and references therein)
6.  ["Mathematics of Machine Learning Lecture 9 Notes | Mathematics of Machine Learning | Mathematics"](https://ocw.mit.edu/courses/18-657-mathematics-of-machine-learning-fall-2015/resources/mit18_657f15_l9/). *MIT OpenCourseWare*. Retrieved 2023-10-28.

## Further reading

- [Vapnik, V.](https://en.wikipedia.org/wiki/Vladimir_Vapnik) (2000). *The Nature of Statistical Learning Theory*. Information Science and Statistics. [Springer-Verlag](https://en.wikipedia.org/wiki/Springer-Verlag). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-98780-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-98780-4).
