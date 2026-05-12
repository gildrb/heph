[[learning-theory.base]]

> Source: [[Bias Variance Tradeoff|Bias–variance tradeoff]]
> License: Wikipedia content is available under CC BY-SA 4.0.

![[media/88289d92afe72199ccccf4d89bfde503e4e08f40.png]]
Bias and variance as function of model complexity

In [statistics](https://en.wikipedia.org/wiki/Statistics) and [machine learning](https://en.wikipedia.org/wiki/Machine_learning), the **bias–variance tradeoff** describes the relationship between a model's complexity, the accuracy of its predictions, and how well it can make predictions on previously unseen data that were not used to train the model. In general, as the number of tunable parameters in a model increases, it becomes more flexible, and can better fit a training data set. That is, the model has lower error or lower [bias](https://en.wikipedia.org/wiki/Bias_of_an_estimator). However, for more flexible models, there will tend to be greater **variance** to the model fit each time we take a set of [samples](https://en.wikipedia.org/wiki/Sample_(statistics)) to create a new training data set. It is said that there is greater [variance](https://en.wikipedia.org/wiki/Variance) in the model's [estimated](https://en.wikipedia.org/wiki/Estimation_theory) [parameters](https://en.wikipedia.org/wiki/Statistical_parameter).

The **bias–variance dilemma** or **bias–variance problem** is the conflict in trying to simultaneously minimize these two sources of [error](https://en.wikipedia.org/wiki/Errors_and_residuals_in_statistics) that prevent [supervised learning](https://en.wikipedia.org/wiki/Supervised_learning) algorithms from generalizing beyond their [training set](https://en.wikipedia.org/wiki/Training_set):

- The [*bias*](https://en.wikipedia.org/wiki/Bias_of_an_estimator) error is an error from erroneous assumptions in the learning [algorithm](https://en.wikipedia.org/wiki/Algorithm). High bias can cause an algorithm to miss the relevant relations between features and target outputs ([underfitting](https://en.wikipedia.org/wiki/Overfitting#Underfitting)).
- The *[variance](https://en.wikipedia.org/wiki/Variance)* is an error from sensitivity to small fluctuations in the training set. High variance may result from an algorithm modeling the random [noise](https://en.wikipedia.org/wiki/Noise_(signal_processing) "Noise (signal processing)") in the training data ([overfitting](https://en.wikipedia.org/wiki/Overfitting)).

The **bias–variance decomposition** is a way of analyzing a learning algorithm's [expected](https://en.wikipedia.org/wiki/Expected_value) [[Generalization Error]] with respect to a particular problem as a sum of three terms, the bias, variance, and a quantity called the *irreducible error*, resulting from noise in the problem itself.

![[media/92908b891d7e4594cdbd2301147df62b62ee9fab.png]]

Function and noisy data

![[media/f2146108ae50ecc9c16c2621d651c61fc7200a82.png]]

Spread=5

![[media/6f5015b07411129aa1e5ee472b8ef4449dda4984.png]]

Spread=1

![[media/d3dd2f5df8f17e7936f51b751e2bbf3170371b42.png]]

Spread=0.1

A function (red) is approximated using [radial basis functions](https://en.wikipedia.org/wiki/Radial_basis_functions) (blue). Several trials are shown in each graph. For each trial, a few noisy data points are provided as a training set (top). For a wide spread (image 2) the bias is high: the RBFs cannot fully approximate the function (especially the central dip), but the variance between different trials is low. As spread decreases (image 3 and 4) the bias decreases: the blue curves more closely approximate the red. However, depending on the noise in different trials the variance between trials increases. In the lowermost image the approximated values for x=0 varies wildly depending on where the data points were located.

## Motivation

- 

  ![[media/416839faf8db98e9cd71748af088429f0c37f19d.png]]

  High bias, low variance

- 

  ![[media/ed04e8632c75d9862dfea82747de3d5d5959975d.png]]

  High bias, high variance

- 

  ![[media/23861fca77a2191a08fb218dab1ff7bd26bd391f.png]]

  Low bias, low variance

- 

  ![[media/7c49fd5f48546bb3320d9ddc5af56b42ab7ed89d.png]]

  Low bias, high variance

The bias–variance tradeoff is a central problem in supervised learning. Ideally, one wants to [choose a model](https://en.wikipedia.org/wiki/Model_selection) that both accurately captures the regularities in its training data, but also [generalizes](https://en.wikipedia.org/wiki/Generalization) well to unseen data. Unfortunately, it is typically impossible to do both simultaneously. High-variance learning methods may be able to represent their training set well but are at risk of overfitting to noisy or unrepresentative training data. In contrast, algorithms with high bias typically produce simpler models that may fail to capture important regularities (i.e. underfit) in the data.

It is an often made [fallacy](https://en.wikipedia.org/wiki/Affirming_the_consequent) to assume that complex models must have high variance. High variance models are "complex" in some sense, but the reverse need not be true. In addition, one has to be careful how to define complexity. In particular, the number of parameters used to describe the model is a poor measure of complexity. This is illustrated by an example adapted from: The model $f_{a,b}(x)=a\sin(bx)$ has only two parameters ($a,b$) but it can interpolate any number of points by oscillating with a high enough frequency, resulting in both a high bias and high variance.

An analogy can be made to the relationship between [accuracy and precision](https://en.wikipedia.org/wiki/Accuracy_and_precision). Accuracy is one way of quantifying bias and can intuitively be improved by selecting from only [local](https://en.wikipedia.org/wiki/Sample_space) information. Consequently, a sample will appear accurate (i.e. have low bias) under the aforementioned selection conditions, but may result in underfitting. In other words, [test data](https://en.wikipedia.org/wiki/Training,_validation,_and_test_data_sets) may not agree as closely with training data, which would indicate imprecision and therefore inflated variance. A graphical example would be a straight line fit to data exhibiting quadratic behavior overall. Precision is a description of variance and generally can only be improved by selecting information from a comparatively larger space. The option to select many data points over a broad sample space is the ideal condition for any analysis. However, intrinsic constraints (whether physical, theoretical, computational, etc.) will always play a limiting role. The limiting case where only a finite number of data points are selected over a broad sample space may result in improved precision and lower variance overall, but may also result in an overreliance on the training data (overfitting). This means that test data would also not agree as closely with the training data, but in this case the reason is inaccuracy or high bias. To borrow from the previous example, the graphical representation would appear as a high-order polynomial fit to the same data exhibiting quadratic behavior. Note that error in each case is measured the same way, but the reason ascribed to the error is different depending on the balance between bias and variance. To mitigate how much information is used from neighboring observations, a model can be [smoothed](https://en.wikipedia.org/wiki/Smoothing) via explicit [regularization](https://en.wikipedia.org/wiki/Regularization_(mathematics) "Regularization (mathematics)"), such as [shrinkage](https://en.wikipedia.org/wiki/Shrinkage_(statistics) "Shrinkage (statistics)").

## Bias–variance decomposition of mean squared error

![[media/858abe1c44112129a1d84b4c8e439db0dcbc7f69.png]]
Bias–variance decomposition in the case of mean squared loss. The green dots are samples of test label $y$ at a fixed test feature $x$. Their variance around the mean $\mathbb {E} _{y\sim p(\cdot |x)}[y]$ is the irreducible error $\sigma ^{2}$. The red dots are test label predictions $f(x|D)$ as the training set $D$ is randomly sampled. Their variance around the mean $\mathbb {E} _{D}[f(x|D)]$ is the variance $\operatorname {Var} _{D}{\big [}f(x|D){\big ]}$. The difference between the red dash and the green dash is the bias $\operatorname {Bias} _{D}{\big [}f(x|D){\big ]}$. The bias–variance decomposition is then visually clear: the mean squared error between the red dots and the green dots is the sum of the three components.

Suppose that we have a training set consisting of a set of points $x_{1},\dots ,x_{n}$ and real-valued labels $y_{i}$ associated with the points $x_{i}$. We assume that the data is generated by a function $f(x)$ such as $y=f(x)+\varepsilon$, where the noise, $\varepsilon$, has zero mean and unit variance $\sigma ^{2}$. That is, $y_{i}=f(x_{i})+\varepsilon _{i}$, where $\varepsilon _{i}$ is a noise sample.

We want to find a function ${\hat {f}}\!(x;D)$, that approximates the true function $f(x)$ as well as possible, by means of some learning algorithm based on a training dataset (sample) $D=\{(x_{1},y_{1})\dots ,(x_{n},y_{n})\}$. We make "as well as possible" precise by measuring the [mean squared error](https://en.wikipedia.org/wiki/Mean_squared_error) between $y$ and ${\hat {f}}\!(x;D)$: we want $(y-{\hat {f}}\!(x;D))^{2}$ to be minimal, both for $x_{1},\dots ,x_{n}$ *and for points outside of our sample*. Of course, we cannot hope to do so perfectly, since the $y_{i}$ contain noise $\varepsilon$; this means we must be prepared to accept an *irreducible error* in any function we come up with.

Finding an ${\hat {f}}$ that generalizes to points outside of the training set can be done with any of the countless algorithms used for supervised learning. It turns out that whichever function ${\hat {f}}$ we select, we can decompose its [expected](https://en.wikipedia.org/wiki/Expected_value) error on an unseen sample $x$ (i.e. conditional on $x$) as follows:

$$
\mathbb {E} _{D,\varepsilon }{\Big [}{\big (}y-{\hat {f}}\!(x;D){\big )}^{2}{\Big ]}={\Big (}\operatorname {Bias} _{D}{\big [}{\hat {f}}\!(x;D){\big ]}{\Big )}^{2}+\operatorname {Var} _{D}{\big [}{\hat {f}}\!(x;D){\big ]}+\sigma ^{2}
$$

where 

$$
{\begin{aligned}\operatorname {Bias} _{D}{\big [}{\hat {f}}\!(x;D){\big ]}&\triangleq \mathbb {E} _{D}{\big [}{\hat {f}}\!(x;D)-f(x){\big ]}\\&=\mathbb {E} _{D}{\big [}{\hat {f}}\!(x;D){\big ]}\,-\,f(x)\\&=\mathbb {E} _{D}{\big [}{\hat {f}}\!(x;D){\big ]}\,-\,\mathbb {E} _{y|x}{\big [}y(x){\big ]}\end{aligned}}
$$

and

$$
\operatorname {Var} _{D}{\big [}{\hat {f}}\!(x;D){\big ]}\triangleq \mathbb {E} _{D}\left[\left(\mathbb {E} _{D}[{\hat {f}}\!(x;D)]-{\hat {f}}\!(x;D)\right)^{2}\right]
$$

and

$$
\sigma ^{2}=\operatorname {E} _{y}{\Big [}{\big (}y-\underbrace {f(x)} _{E_{y|x}[y]}{\big )}^{2}{\Big ]}
$$

The expectation ranges over different choices of the training set $D=\{(x_{1},y_{1})\dots ,(x_{n},y_{n})\}$, all sampled from the same joint distribution $P(x,y)$ which can for example be done via [bootstrapping](https://en.wikipedia.org/wiki/Bootstrapping_(statistics) "Bootstrapping (statistics)"). The three terms represent:

- the square of the *bias* of the learning method, which can be thought of as the error caused by the simplifying assumptions built into the method. E.g., when approximating a non-linear function $f(x)$ using a learning method for [linear models](https://en.wikipedia.org/wiki/Linear_model), there will be error in the estimates ${\hat {f}}\!(x)$ due to this assumption;
- the *variance* of the learning method, or, intuitively, how much the learning method ${\hat {f}}\!(x)$ will move around its mean;
- the irreducible error $\sigma ^{2}$.

Since all three terms are non-negative, the irreducible error forms a lower bound on the expected error on unseen samples.

The more complex the model ${\hat {f}}\!(x)$ is, the more data points it will capture, and the lower the bias will be. However, complexity will make the model "move" more to capture the data points, and hence its variance will be larger.

### Derivation

The derivation of the bias–variance decomposition for squared error proceeds as follows. For convenience, we drop the $D$ subscript in the following lines, such that ${\hat {f}}\!(x;D)={\hat {f}}\!(x)$.

Let us write the mean-squared error of our model:

$$
{\begin{aligned}{\text{MSE}}(x)&\triangleq \mathbb {E} {\Big [}{\big (}y-{\hat {f}}\!(x){\big )}^{2}{\Big ]}\\&=\mathbb {E} {\Big [}{\big (}f(x)+\varepsilon -{\hat {f}}\!(x){\big )}^{2}{\Big ]}&&{\text{since }}y\triangleq f(x)+\varepsilon \\&=\mathbb {E} {\Big [}{\big (}f(x)-{\hat {f}}\!(x){\big )}^{2}{\Big ]}\,+\,2\ \mathbb {E} {\Big [}{\big (}f(x)-{\hat {f}}\!(x){\big )}\varepsilon {\Big ]}\,+\,\mathbb {E} [\varepsilon ^{2}]\end{aligned}}
$$

We can show that the second term of this equation is null:

$$
{\begin{aligned}\mathbb {E} {\Big [}{\big (}f(x)-{\hat {f}}\!(x){\big )}\varepsilon {\Big ]}&=\mathbb {E} {\big [}f(x)-{\hat {f}}\!(x){\big ]}\ \mathbb {E} {\big [}\varepsilon {\big ]}&&{\text{since }}\varepsilon {\text{ is independent from }}x\\&=0&&{\text{since }}\mathbb {E} {\big [}\varepsilon {\big ]}=0\end{aligned}}
$$

Moreover, the third term of this equation is nothing but $\sigma ^{2}$, the variance of $\varepsilon$.

Let us now expand the remaining term:

$$
{\begin{aligned}&\operatorname {\mathbb {E} } \left[\left(f(x)-{\hat {f}}\!(x)\right)^{2}\right]\\[1ex]&=\operatorname {\mathbb {E} } \left[\left(f(x)-\operatorname {\mathbb {E} } [{\hat {f}}\!(x)]+\operatorname {\mathbb {E} } [{\hat {f}}\!(x)]-{\hat {f}}\!(x)\right)^{2}\right]\\[1ex]&={\color {Blue}\operatorname {\mathbb {E} } \left[\left(f(x)-\operatorname {\mathbb {E} } [{\hat {f}}\!(x)]\right)^{2}\right]}\,+\,\operatorname {\mathbb {E} } \left[\left(\operatorname {\mathbb {E} } [{\hat {f}}\!(x)]-{\hat {f}}\!(x)\right)^{2}\right]\\&\quad \,+\,2\ {\color {PineGreen}\operatorname {\mathbb {E} } \left[\left(f(x)-\operatorname {\mathbb {E} } [{\hat {f}}\!(x)]\right)\left(\operatorname {\mathbb {E} } [{\hat {f}}\!(x)]-{\hat {f}}\!(x)\right)\right]}\end{aligned}}
$$

We show that:

$$
{\begin{aligned}{\color {Blue}\mathbb {E} {\Big [}{\big (}f(x)-\mathbb {E} {\big [}{\hat {f}}(x){\big ]}{\big )}^{2}{\Big ]}}&=\mathbb {E} {\big [}f(x)^{2}{\big ]}\,-\,2\ \mathbb {E} {\Big [}f(x)\ \mathbb {E} {\big [}{\hat {f}}(x){\big ]}{\Big ]}\,+\,\mathbb {E} {\Big [}\mathbb {E} {\big [}{\hat {f}}(x){\big ]}^{2}{\Big ]}\\&=f(x)^{2}\,-\,2\ f(x)\ \mathbb {E} {\big [}{\hat {f}}(x){\big ]}\,+\,\mathbb {E} {\big [}{\hat {f}}(x){\big ]}^{2}\\&={\Big (}f(x)-\mathbb {E} {\big [}{\hat {f}}(x){\big ]}{\Big )}^{2}\end{aligned}}
$$

This last series of equalities comes from the fact that $f(x)$ is not a random variable, but a fixed, deterministic function of $x$. Therefore, $\operatorname {\mathbb {E} } \left[f(x)\right]=f(x)$. Similarly $\operatorname {\mathbb {E} } \left[f(x)^{2}\right]=f(x)^{2}$, and $\operatorname {\mathbb {E} } \left[f(x)\,\operatorname {\mathbb {E} } [{\hat {f}}\!(x)]\right]=f(x)\,\operatorname {\mathbb {E} } \left[\operatorname {\mathbb {E} } [{\hat {f}}\!(x)]\right]=f(x)\operatorname {\mathbb {E} } [{\hat {f}}\!(x)]$. Using the same reasoning, we can expand the second term and show that it is null:

$$
{\begin{aligned}&{\color {PineGreen}\operatorname {\mathbb {E} } \left[\left(f(x)-\operatorname {\mathbb {E} } [{\hat {f}}\!(x)]\right)\left(\operatorname {\mathbb {E} } [{\hat {f}}\!(x)]-{\hat {f}}\!(x)\right)\right]}\\&=\operatorname {\mathbb {E} } \left[f(x)\,\operatorname {\mathbb {E} } [{\hat {f}}\!(x)]\,-\,f(x){\hat {f}}\!(x)\,-\,\operatorname {\mathbb {E} } [{\hat {f}}\!(x)]^{2}+\operatorname {\mathbb {E} } [{\hat {f}}\!(x)]\,{\hat {f}}\!(x)\right]\\&=f(x)\,\operatorname {\mathbb {E} } [{\hat {f}}\!(x)]\,-\,f(x)\,\operatorname {\mathbb {E} } [{\hat {f}}\!(x)]\,-\,\operatorname {\mathbb {E} } [{\hat {f}}\!(x)]^{2}\,+\,\operatorname {\mathbb {E} } [{\hat {f}}\!(x)]^{2}\\&=0\end{aligned}}
$$

Eventually, we plug our derivations back into the original equation, and identify each term:

$$
{\begin{aligned}{\text{MSE}}(x)&=\left(f(x)-\operatorname {\mathbb {E} } [{\hat {f}}\!(x)]\right)^{2}+\operatorname {\mathbb {E} } \left[\left(\operatorname {\mathbb {E} } [{\hat {f}}\!(x)]-{\hat {f}}\!(x)\right)^{2}\right]+\sigma ^{2}\\&=\operatorname {Bias} \left[{\hat {f}}\!(x)\right]^{2}+\,\operatorname {Var} \left[{\hat {f}}\!(x)\right]\,+\,\sigma ^{2}\end{aligned}}
$$

Finally, the MSE loss function (or negative log-likelihood) is obtained by taking the expectation value over $x\sim P$: 

$$
{\text{MSE}}=\operatorname {\mathbb {E} } _{x}\left[{\text{MSE}}(x)\right]=\operatorname {\mathbb {E} } _{x}\left\{\operatorname {Bias} _{D}\!\left[{\hat {f}}\!(x;D)\right]^{2}+\operatorname {Var} _{D}\left[{\hat {f}}\!(x;D)\right]\right\}+\sigma ^{2}.
$$

## Approaches

[Dimensionality reduction](https://en.wikipedia.org/wiki/Dimensionality_reduction) and [feature selection](https://en.wikipedia.org/wiki/Feature_selection) can decrease variance by simplifying models. Similarly, a larger training set tends to decrease variance. Adding features (predictors) tends to decrease bias, at the expense of introducing additional variance. Learning algorithms typically have some tunable parameters that control bias and variance; for example,

- [linear](https://en.wikipedia.org/wiki/Linear_model) and [Generalized linear](https://en.wikipedia.org/wiki/Generalized_linear_model) models can be [regularized](https://en.wikipedia.org/wiki/Regularization_(mathematics) "Regularization (mathematics)") to decrease their variance at the cost of increasing their bias.
- In [artificial neural networks](https://en.wikipedia.org/wiki/Artificial_neural_network), the variance increases and the bias decreases as the number of hidden units increase, although this classical assumption has been the subject of recent debate. Like in GLMs, regularization is typically applied.
- In [k-nearest neighbor](https://en.wikipedia.org/wiki/K-nearest_neighbor) models, a high value of k leads to high bias and low variance (see below).
- In [instance-based learning](https://en.wikipedia.org/wiki/Instance-based_learning), regularization can be achieved varying the mixture of [prototypes](https://en.wikipedia.org/wiki/Prototype) and exemplars.
- In [decision trees](https://en.wikipedia.org/wiki/Decision_tree), the depth of the tree determines the variance. Decision trees are commonly pruned to control variance.

One way of resolving the trade-off is to use [mixture models](https://en.wikipedia.org/wiki/Mixture_models) and [ensemble learning](https://en.wikipedia.org/wiki/Ensemble_learning). For example, [boosting](https://en.wikipedia.org/wiki/Boosting_(machine_learning) "Boosting (machine learning)") combines many "weak" (high bias) models in an ensemble that has lower bias than the individual models, while [bagging](https://en.wikipedia.org/wiki/Bootstrap_aggregating) combines "strong" learners in a way that reduces their variance.

[Model validation](https://en.wikipedia.org/wiki/Model_validation) methods such as [cross-validation (statistics)](https://en.wikipedia.org/wiki/Cross-validation_(statistics) "Cross-validation (statistics)") can be used to tune models so as to optimize the trade-off.

### *k*-nearest neighbors

In the case of [k-nearest neighbors regression](https://en.wikipedia.org/wiki/K-nearest_neighbors_algorithm), when the expectation is taken over the possible labeling of a fixed training set, a [closed-form expression](https://en.wikipedia.org/wiki/Closed-form_expression) exists that relates the bias–variance decomposition to the parameter k:

$$
\operatorname {\mathbb {E} } \left[\left(y-{\hat {f}}\!(x)\right)^{2}\mid X=x\right]=\left(f(x)-{\frac {1}{k}}\sum _{i=1}^{k}f(N_{i}(x))\right)^{2}+{\frac {\sigma ^{2}}{k}}+\sigma ^{2}
$$

where $N_{1}(x),\dots ,N_{k}(x)$ are the k nearest neighbors of x in the training set. The bias (first term) is a monotone rising function of k, while the variance (second term) drops off as k is increased. In fact, under "reasonable assumptions" the bias of the first-nearest neighbor (1-NN) estimator vanishes entirely as the size of the training set approaches infinity.

## Applications

### In regression

The bias–variance decomposition forms the conceptual basis for regression [regularization](https://en.wikipedia.org/wiki/Regularization_(mathematics) "Regularization (mathematics)") methods such as [LASSO](https://en.wikipedia.org/wiki/Lasso_(statistics) "Lasso (statistics)") and [ridge regression](https://en.wikipedia.org/wiki/Ridge_regression). Regularization methods introduce bias into the regression solution that can reduce variance considerably relative to the [ordinary least squares (OLS)](https://en.wikipedia.org/wiki/Ordinary_least_squares) solution. Although the OLS solution provides non-biased regression estimates, the lower variance solutions produced by regularization techniques provide superior MSE performance.

### In classification

The bias–variance decomposition was originally formulated for least-squares regression. For the case of [classification](https://en.wikipedia.org/wiki/Statistical_classification) under the [0-1 loss](https://en.wikipedia.org/wiki/0-1_loss) (misclassification rate), it is possible to find a similar decomposition, with the caveat that the variance term becomes dependent on the target label. Alternatively, if the classification problem can be phrased as [probabilistic classification](https://en.wikipedia.org/wiki/Probabilistic_classification), then the expected cross-entropy can instead be decomposed to give bias and variance terms with the same semantics but taking a different form.

It has been argued that as training data increases, the variance of learned models will tend to decrease, and hence that as training data quantity increases, error is minimised by methods that learn models with lesser bias, and that conversely, for smaller training data quantities it is ever more important to minimise variance.

### In reinforcement learning

Even though the bias–variance decomposition does not directly apply in [reinforcement learning](https://en.wikipedia.org/wiki/Reinforcement_learning), a similar tradeoff can also characterize generalization. When an agent has limited information on its environment, the suboptimality of an RL algorithm can be decomposed into the sum of two terms: a term related to an asymptotic bias and a term due to overfitting. The asymptotic bias is directly related to the learning algorithm (independently of the quantity of data) while the overfitting term comes from the fact that the amount of data is limited.

### In Monte Carlo methods

While in traditional Monte Carlo methods the bias is typically zero, modern approaches, such as [[Markov Chain Monte Carlo]] are only asymptotically unbiased, at best. Convergence diagnostics can be used to control bias via [burn-in](https://en.wikipedia.org/wiki/Burn-in) removal, but due to a limited computational budget, a bias–variance trade-off arises, leading to a wide-range of approaches, in which a controlled bias is accepted, if this allows to dramatically reduce the variance, and hence the overall estimation error.

### In human learning

While widely discussed in the context of machine learning, the bias–variance dilemma has been examined in the context of [human cognition](https://en.wikipedia.org/wiki/Cognitive_science), most notably by [Gerd Gigerenzer](https://en.wikipedia.org/wiki/Gerd_Gigerenzer) and co-workers in the context of learned heuristics. They have argued (see references below) that the human brain resolves the dilemma in the case of the typically sparse, poorly-characterized training-sets provided by experience by adopting high-bias/low variance heuristics. This reflects the fact that a zero-bias approach has poor generalizability to new situations, and also unreasonably presumes precise knowledge of the true state of the world. The resulting heuristics are relatively simple, but produce better inferences in a wider variety of situations.

[Geman](https://en.wikipedia.org/wiki/Stuart_Geman) et al. argue that the bias–variance dilemma implies that abilities such as generic [object recognition](https://en.wikipedia.org/wiki/Object_recognition) cannot be learned from scratch, but require a certain degree of "hard wiring" that is later tuned by experience. This is because model-free approaches to inference require impractically large training sets if they are to avoid high variance.

## See also

- [Accuracy and precision](https://en.wikipedia.org/wiki/Accuracy_and_precision)
- [Bias of an estimator](https://en.wikipedia.org/wiki/Bias_of_an_estimator)
- [Double descent](https://en.wikipedia.org/wiki/Double_descent)
- [Gauss–Markov theorem](https://en.wikipedia.org/wiki/Gauss%E2%80%93Markov_theorem)
- [Hyperparameter optimization](https://en.wikipedia.org/wiki/Hyperparameter_optimization)
- [Law of total variance](https://en.wikipedia.org/wiki/Law_of_total_variance)
- [Minimum-variance unbiased estimator](https://en.wikipedia.org/wiki/Minimum-variance_unbiased_estimator)
- [Model selection](https://en.wikipedia.org/wiki/Model_selection)
- [Regression model validation](https://en.wikipedia.org/wiki/Regression_model_validation)
- [Supervised learning](https://en.wikipedia.org/wiki/Supervised_learning)
- [Cramér–Rao bound](https://en.wikipedia.org/wiki/Cram%C3%A9r%E2%80%93Rao_bound)
- [Prediction interval](https://en.wikipedia.org/wiki/Prediction_interval)

## References

1.  Kohavi, Ron; Wolpert, David H. (1996). "Bias Plus Variance Decomposition for Zero-One Loss Functions". *ICML*. **96**.
2.  Luxburg, Ulrike V.; Schölkopf, B. (2011). "Statistical learning theory: Models, concepts, and results". *Handbook of the History of Logic*. **10**: Section 2.4.
3.  Neal, Brady (2019). "On the Bias–Variance Tradeoff: Textbooks Need an Update". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1912.08286](https://arxiv.org/abs/1912.08286) \[[cs.LG](https://arxiv.org/archive/cs.LG)\].
4.  ^   Neal, Brady; Mittal, Sarthak; Baratin, Aristide; Tantia, Vinayak; Scicluna, Matthew; Lacoste-Julien, Simon; Mitliagkas, Ioannis (2018). "A Modern Take on the Bias–Variance Tradeoff in Neural Networks". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1810.08591](https://arxiv.org/abs/1810.08591) \[[cs.LG](https://arxiv.org/archive/cs.LG)\].
5.  Neal, Brady; Mittal, Sarthak; Baratin, Aristide; Tantia, Vinayak; Scicluna, Matthew; Lacoste-Julien, Simon; Mitliagkas, Ioannis (2019). [A Modern Take on the Bias–Variance Tradeoff in Neural Networks](https://openreview.net/forum?id=HkgmzhC5F7). International Conference on Learning Representations (ICLR) 2019.
6.  Vapnik, Vladimir (2000). [The nature of statistical learning theory](https://dx.doi.org/10.1007/978-1-4757-3264-1). New York: Springer-Verlag. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-1-4757-3264-1](https://doi.org/10.1007%2F978-1-4757-3264-1). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4757-3264-1](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4757-3264-1). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [7138354](https://api.semanticscholar.org/CorpusID:7138354).
7.  ^    James, Gareth; [Witten, Daniela](https://en.wikipedia.org/wiki/Daniela_Witten); [Hastie, Trevor](https://en.wikipedia.org/wiki/Trevor_Hastie); [Tibshirani, Robert](https://en.wikipedia.org/wiki/Robert_Tibshirani) (2013). [An Introduction to Statistical Learning](http://www-bcf.usc.edu/~gareth/ISL/). Springer.
8.  ^   Hastie, Trevor; Tibshirani, Robert; [Friedman, Jerome H.](https://en.wikipedia.org/wiki/Jerome_H._Friedman) (2009). [The Elements of Statistical Learning](https://web.archive.org/web/20150126123924/http://statweb.stanford.edu/~tibs/ElemStatLearn/). Archived from [the original](http://statweb.stanford.edu/~tibs/ElemStatLearn/) on 2015-01-26. Retrieved 2014-08-20.
9.  [Vijayakumar, Sethu](https://en.wikipedia.org/wiki/Sethu_Vijayakumar) (2007). ["The Bias–Variance Tradeoff"](http://www.inf.ed.ac.uk/teaching/courses/mlsc/Notes/Lecture4/BiasVariance.pdf) (PDF). [University of Edinburgh](https://en.wikipedia.org/wiki/University_of_Edinburgh). Retrieved 19 August 2014.
10. Shakhnarovich, Greg (2011). ["Notes on derivation of bias–variance decomposition in linear regression"](https://web.archive.org/web/20140821063842/http://ttic.uchicago.edu/~gregory/courses/wis-ml2012/lectures/biasVarDecom.pdf) (PDF). Archived from [the original](http://ttic.uchicago.edu/~gregory/courses/wis-ml2012/lectures/biasVarDecom.pdf) (PDF) on 21 August 2014. Retrieved 20 August 2014.
11. Belsley, David (1991). *Conditioning diagnostics : collinearity and weak data in regression*. New York (NY): Wiley. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0471528890](https://en.wikipedia.org/wiki/Special:BookSources/978-0471528890).
12. ^    [Geman, Stuart](https://en.wikipedia.org/wiki/Stuart_Geman); Bienenstock, Élie; Doursat, René (1992). ["Neural networks and the bias/variance dilemma"](http://web.mit.edu/6.435/www/Geman92.pdf) (PDF). *Neural Computation*. **4**: 1–58. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1162/neco.1992.4.1.1](https://doi.org/10.1162%2Fneco.1992.4.1.1). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [14215320](https://api.semanticscholar.org/CorpusID:14215320).
13. Gagliardi, Francesco (May 2011). ["Instance-based classifiers applied to medical databases: diagnosis and knowledge extraction"](https://www.researchgate.net/publication/51173579). *Artificial Intelligence in Medicine*. **52** (3): 123–139. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.artmed.2011.04.002](https://doi.org/10.1016%2Fj.artmed.2011.04.002). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [21621400](https://pubmed.ncbi.nlm.nih.gov/21621400).
14. Ting, Jo-Anne; Vijaykumar, Sethu; Schaal, Stefan (2011). "Locally Weighted Regression for Control". In Sammut, Claude; Webb, Geoffrey I. (eds.). [Encyclopedia of Machine Learning](http://homepages.inf.ed.ac.uk/svijayak/publications/ting-EMLDM2016.pdf) (PDF). Springer. p. 615. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2010eoml.book.....S](https://ui.adsabs.harvard.edu/abs/2010eoml.book.....S).
15. Fortmann-Roe, Scott (2012). ["Understanding the Bias–Variance Tradeoff"](http://scott.fortmann-roe.com/docs/BiasVariance.html).
16. [Domingos, Pedro](https://en.wikipedia.org/wiki/Pedro_Domingos) (2000). [A unified bias–variance decomposition](http://homes.cs.washington.edu/~pedrod/bvd.pdf) (PDF). ICML.
17. Valentini, Giorgio; [Dietterich, Thomas G.](https://en.wikipedia.org/wiki/Thomas_G._Dietterich) (2004). ["Bias–variance analysis of support vector machines for the development of SVM-based ensemble methods"](http://www.jmlr.org/papers/volume5/valentini04a/valentini04a.pdf) (PDF). *[Journal of Machine Learning Research](https://en.wikipedia.org/wiki/Journal_of_Machine_Learning_Research)*. **5**: 725–775.
18. Brain, Damian; [Webb, Geoffrey](https://en.wikipedia.org/wiki/Geoff_Webb) (2002). [The Need for Low Bias Algorithms in Classification Learning From Large Data Sets](http://i.giwebb.com/wp-content/papercite-data/pdf/brainwebb02.pdf) (PDF). Proceedings of the Sixth European Conference on Principles of Data Mining and Knowledge Discovery (PKDD 2002).
19. Francois-Lavet, Vincent; Rabusseau, Guillaume; Pineau, Joelle; Ernst, Damien; Fonteneau, Raphael (2019). ["On Overfitting and Asymptotic Bias in Batch Reinforcement Learning with Partial Observability"](https://jair.org/index.php/jair/article/view/11478). *Journal of Artificial Intelligence Research*. **65**: 1–30. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1709.07796](https://arxiv.org/abs/1709.07796). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1613/jair.1.11478](https://doi.org/10.1613%2Fjair.1.11478).
20. Zlochin, M.; Baram, Y. (2001). ["The Bias–Variance Dilemma of the Monte Carlo Method"](https://doi.org/10.1007/3-540-44668-0_20). In Dorffner, G.; Bischof, H.; Hornik, K. (eds.). *Artificial Neural Networks — ICANN 2001*. Lecture Notes in Computer Science. Vol. 2130. Springer. pp. 257–264. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/3-540-44668-0_20](https://doi.org/10.1007%2F3-540-44668-0_20). Retrieved 17 November 2024.
21. South, Leah F.; Riabiz, Marina; Teymur, Onur; Oates, Chris J. (March 1, 2022). ["Postprocessing of MCMC"](https://ssrn.com/abstract=4065369). *Annual Review of Statistics and Its Application*. **9** (1): 529–555. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2103.16048](https://arxiv.org/abs/2103.16048). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2022AnRSA...9..529S](https://ui.adsabs.harvard.edu/abs/2022AnRSA...9..529S). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1146/annurev-statistics-040220-091727](https://doi.org/10.1146%2Fannurev-statistics-040220-091727). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [7616193](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7616193). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [39006247](https://pubmed.ncbi.nlm.nih.gov/39006247). Retrieved 17 November 2024.
22. Nemeth, C.; Fearnhead, P. (2021). ["Stochastic Gradient Markov Chain Monte Carlo"](https://doi.org/10.1080/01621459.2020.1847120). *Journal of the American Statistical Association*. **116** (533): 433–450. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1907.06986](https://arxiv.org/abs/1907.06986). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/01621459.2020.1847120](https://doi.org/10.1080%2F01621459.2020.1847120). Retrieved 17 November 2024.
23. Vazquez, M.A.; Míguez, J. (2017). ["Importance sampling with transformed weights"](https://doi.org/10.1049/el.2016.3462). *Electronics Letters*. **53** (12): 783–785. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1702.01987](https://arxiv.org/abs/1702.01987). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2017ElL....53..783V](https://ui.adsabs.harvard.edu/abs/2017ElL....53..783V). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1049/el.2016.3462](https://doi.org/10.1049%2Fel.2016.3462). Retrieved 17 November 2024.
24. Korba, A.; Portier, F. (2022). ["Adaptive Importance Sampling meets Mirror Descent: A Bias–Variance Tradeoff"](https://proceedings.mlr.press/v151/korba22a.html). *Proceedings of The 25th International Conference on Artificial Intelligence and Statistics*. Proceedings of Machine Learning Research. Vol. 151. pp. 11503–11527. Retrieved 17 November 2024.
25. [Gigerenzer, Gerd](https://en.wikipedia.org/wiki/Gerd_Gigerenzer); Brighton, Henry (2009). "Homo Heuristicus: Why Biased Minds Make Better Inferences". *Topics in Cognitive Science*. **1** (1): 107–143. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1111/j.1756-8765.2008.01006.x](https://doi.org/10.1111%2Fj.1756-8765.2008.01006.x). [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[11858/00-001M-0000-0024-F678-0](https://hdl.handle.net/11858%2F00-001M-0000-0024-F678-0). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [25164802](https://pubmed.ncbi.nlm.nih.gov/25164802).

## External links

- [MLU-Explain: The Bias Variance Tradeoff](https://mlu-explain.github.io/bias-variance/) — An interactive visualization of the bias–variance tradeoff in LOESS Regression and K-Nearest Neighbors.
