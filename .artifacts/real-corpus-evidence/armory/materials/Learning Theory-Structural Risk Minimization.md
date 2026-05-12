[[learning-theory.base]]

> Source: [[Structural Risk Minimization]]
> License: Wikipedia content is available under CC BY-SA 4.0.

**Structural risk minimization (SRM)** is an inductive principle of use in [machine learning](https://en.wikipedia.org/wiki/Machine_learning). Commonly in machine learning, a generalized model must be selected from a finite data set, with the consequent problem of [overfitting](https://en.wikipedia.org/wiki/Overfitting) – the model becoming too strongly tailored to the particularities of the training set and generalizing poorly to new data. The SRM principle addresses this problem by balancing the model's complexity against its success at fitting the training data. This principle was first set out in a 1974 book by [Vladimir Vapnik](https://en.wikipedia.org/wiki/Vladimir_Vapnik) and [Alexey Chervonenkis](https://en.wikipedia.org/wiki/Alexey_Chervonenkis) and uses the [[VC Dimension]].

In practical terms, Structural Risk Minimization is implemented by minimizing $E_{train}+\beta H(W)$, where $E_{train}$ is the train error, the function $H(W)$ is called a regularization function, and $\beta$ is a constant. $H(W)$ is chosen such that it takes large values on parameters $W$ that belong to high-capacity subsets of the parameter space. Minimizing $H(W)$ in effect limits the capacity of the accessible subsets of the parameter space, thereby controlling the trade-off between minimizing the training error and minimizing the expected gap between the training error and test error.

The SRM problem can be formulated in terms of data. Given n data points consisting of data x and labels y, the objective $J(\theta )$ is often expressed in the following manner:

$J(\theta )={\frac {1}{2n}}\sum _{i=1}^{n}(h_{\theta }(x^{i})-y^{i})^{2}+{\frac {\lambda }{2}}\sum _{j=1}^{d}\theta _{j}^{2}$

The first term is the mean squared error (MSE) term between the value of the learned model, $h_{\theta }$, and the given labels $y$. This term is the training error, $E_{train}$, that was discussed earlier. The second term, places a prior over the weights, to favor sparsity and penalize larger weights. The trade-off coefficient, $\lambda$, is a hyperparameter that places more or less importance on the regularization term. Larger $\lambda$ encourages sparser weights at the expense of a more optimal MSE, and smaller $\lambda$ relaxes regularization allowing the model to fit to data. Note that as $\lambda \to \infty$ the weights become zero, and as $\lambda \to 0$, the model typically suffers from overfitting.

## See also

- [Vapnik–Chervonenkis theory](https://en.wikipedia.org/wiki/Vapnik%E2%80%93Chervonenkis_theory)
- [Support vector machines](https://en.wikipedia.org/wiki/Support_vector_machines)
- [Model selection](https://en.wikipedia.org/wiki/Model_selection)
- [Occam Learning](https://en.wikipedia.org/wiki/Occam_Learning)
- [[Empirical Risk Minimization]]
- [Ridge regression](https://en.wikipedia.org/wiki/Ridge_regression)
- [Regularization (mathematics)](https://en.wikipedia.org/wiki/Regularization_(mathematics) "Regularization (mathematics)")

## References

1.  Vapnik, V. N.; Chervonenkis, A. Ya. (1974). *Teoriya raspoznavaniya obrazov* \[*Theory of Pattern Recognition*\] (in Russian). Nauka, Moscow.
2.  LeCun, Yann. ["Gradient-Based Learning Applied to Document Recognition"](http://vision.stanford.edu/cs598_spring07/papers/Lecun98.pdf) (PDF).

## External links

- [Structural risk minimization](http://www.svms.org/srm/) at the support vector machines website.
