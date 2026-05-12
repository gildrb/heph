[[learning-theory.base]]

> Source: [[Generalization Error]]
> License: Wikipedia content is available under CC BY-SA 4.0.

For [supervised learning](https://en.wikipedia.org/wiki/Supervised_learning) applications in [machine learning](https://en.wikipedia.org/wiki/Machine_learning) and [[Statistical Learning Theory]], **generalization error** (also known as the **out-of-sample error** or the **risk**) is a measure of how accurately an [algorithm](https://en.wikipedia.org/wiki/Algorithm) is able to predict outcomes for previously unseen data. As learning algorithms are evaluated on finite samples, the evaluation of a learning algorithm may be sensitive to [sampling error](https://en.wikipedia.org/wiki/Sampling_error). As a result, measurements of prediction error on the current data may not provide much information about the algorithm's predictive ability on new, unseen data. The generalization error can be minimized by avoiding [overfitting](https://en.wikipedia.org/wiki/Overfitting) in the learning algorithm. The performance of machine learning algorithms is commonly visualized by [learning curve](https://en.wikipedia.org/wiki/Learning_curve_(machine_learning) "Learning curve (machine learning)") plots that show estimates of the generalization error throughout the learning process.

## Definition

In a learning problem, the goal is to develop a function $f_{n}({\vec {x}})$ that predicts output values $y$ for each input datum ${\vec {x}}$. The subscript $n$ indicates that the function $f_{n}$ is developed based on a data set of $n$ data points. The **generalization error** or **expected loss** or **risk** $I[f]$ of a particular function $f$ over all possible values of ${\vec {x}}$ and $y$ is the [expected value](https://en.wikipedia.org/wiki/Expected_value) of the [loss function](https://en.wikipedia.org/wiki/Loss_function) $V(f)$:

$I[f]=\int _{X\times Y}V(f({\vec {x}}),y)\rho ({\vec {x}},y)d{\vec {x}}dy,$

where $\rho ({\vec {x}},y)$ is the unknown [joint probability distribution](https://en.wikipedia.org/wiki/Joint_probability_distribution) for ${\vec {x}}$ and $y$.

Without knowing the joint probability distribution $\rho$, it is impossible to compute $I[f]$. Instead, we can compute the error on sample data, which is called **empirical error** (or **empirical risk**). Given $n$ data points, the empirical error of a candidate function $f$ is:

$I_{n}[f]={\frac {1}{n}}\sum _{i=1}^{n}V(f({\vec {x}}_{i}),y_{i})$

An algorithm is said to generalize if:

$\lim _{n\rightarrow \infty }I[f]-I_{n}[f]=0$

Of particular importance is the **generalization error** $I[f_{n}]$ of the data-dependent function $f_{n}$ that is found by a learning algorithm based on the sample. Again, for an unknown probability distribution, $I[f_{n}]$ cannot be computed. Instead, the aim of many problems in statistical learning theory is to bound or characterize the difference of the generalization error and the empirical error in probability:

$P_{G}=P(I[f_{n}]-I_{n}[f_{n}]\leq \epsilon )\geq 1-\delta _{n}$

That is, the goal is to characterize the probability $1-\delta _{n}$ that the generalization error is less than the empirical error plus some error bound $\epsilon$ (generally dependent on $\delta$ and $n$). For many types of algorithms, it has been shown that an algorithm has generalization bounds if it meets certain [stability](https://en.wikipedia.org/wiki/Stability_(learning_theory) "Stability (learning theory)") criteria. Specifically, if an algorithm is symmetric (the order of inputs does not affect the result), has bounded loss and meets two stability conditions, it will generalize. The first stability condition, [leave-one-out cross-validation](https://en.wikipedia.org/wiki/Leave-one-out_cross-validation) stability, says that to be stable, the prediction error for each data point when leave-one-out cross validation is used must converge to zero as $n\rightarrow \infty$. The second condition, expected-to-leave-one-out error stability (also known as hypothesis stability if operating in the [$L_{1}$ norm](https://en.wikipedia.org/wiki/L1_norm)) is met if the prediction on a left-out datapoint does not change when a single data point is removed from the training dataset.

These conditions can be formalized as:

### Leave-one-out cross-validation Stability

An algorithm $L$ has $CVloo$ stability if for each $n$, there exists a $\beta _{CV}^{(n)}$ and $\delta _{CV}^{(n)}$ such that:

$\forall i\in \{1,...,n\},\mathbb {P} _{S}\{|V(f_{S^{i}},z_{i})-V(f_{S},z_{i})|\leq \beta _{CV}^{(n)}\}\geq 1-\delta _{CV}^{(n)}$

and $\beta _{CV}^{(n)}$ and $\delta _{CV}^{(n)}$ go to zero as $n$ goes to infinity.

### Expected-leave-one-out error Stability

An algorithm $L$ has $Eloo_{err}$ stability if for each $n$ there exists a $\beta _{EL}^{m}$ and a $\delta _{EL}^{m}$ such that:

$\forall i\in \{1,...,n\},\mathbb {P} _{S}\left\{\left|I[f_{S}]-{\frac {1}{n}}\sum _{i=1}^{N}V\left(f_{S^{i}},z_{i}\right)\right|\leq \beta _{EL}^{(n)}\right\}\geq 1-\delta _{EL}^{(n)}$

with $\beta _{EL}^{(n)}$ and $\delta _{EL}^{(n)}$ going to zero for $n\rightarrow \infty$.

For leave-one-out stability in the $L_{1}$ norm, this is the same as hypothesis stability:

$\mathbb {E} _{S,z}[|V(f_{S},z)-V(f_{S^{i}},z)|]\leq \beta _{H}^{(n)}$

with $\beta _{H}^{(n)}$ going to zero as $n$ goes to infinity.

### Algorithms with proven stability

A number of algorithms have been proven to be stable and as a result have bounds on their generalization error. A list of these algorithms and the papers that proved stability is available [here](https://en.wikipedia.org/wiki/Stability_(learning_theory)#Algorithms_that_are_stable "Stability (learning theory)").

## Relation to overfitting

![[media/2bd4f7e43c2ec658d5b1ef11a02890d045571eeb.png]]
This figure illustrates the relationship between overfitting and the generalization error <em>I</em>[<em>f<sub>n</sub></em>] - <em>I<sub>S</sub></em>[<em>f<sub>n</sub></em>]. Data points were generated from the relationship <em>y</em> = <em>x</em> with white noise added to the <em>y</em> values. In the left column, a set of training points is shown in blue. A seventh order polynomial function was fit to the training data. In the right column, the function is tested on data sampled from the underlying joint probability distribution of <em>x</em> and <em>y</em>. In the top row, the function is fit on a sample dataset of 10 datapoints. In the bottom row, the function is fit on a sample dataset of 100 datapoints. As we can see, for small sample sizes and complex functions, the error on the training set is small but error on the underlying distribution of data is large and we have overfit the data. As a result, generalization error is large. As the number of sample points increases, the prediction error on training and test data converges and generalization error goes to 0.

The concepts of generalization error and overfitting are closely related. Overfitting occurs when the learned function $f_{S}$ becomes sensitive to the noise in the sample. As a result, the function will perform well on the training set but not perform well on other data from the joint probability distribution of $x$ and $y$. Thus, the more overfitting occurs, the larger the generalization error.

The amount of overfitting can be tested using [cross-validation](https://en.wikipedia.org/wiki/Cross-validation_(statistics) "Cross-validation (statistics)") methods, that split the sample into simulated training samples and testing samples. The model is then trained on a training sample and evaluated on the testing sample. The testing sample is previously unseen by the algorithm and so represents a random sample from the joint probability distribution of $x$ and $y$. This test sample allows us to approximate the expected error and as a result approximate a particular form of the generalization error.

Many algorithms exist to prevent overfitting. The minimization algorithm can penalize more complex functions (known as Tikhonov [regularization](https://en.wikipedia.org/wiki/Regularization_(mathematics) "Regularization (mathematics)")), or the hypothesis space can be constrained, either explicitly in the form of the functions or by adding constraints to the minimization function (Ivanov regularization).

The approach to finding a function that does not overfit is at odds with the goal of finding a function that is sufficiently complex to capture the particular characteristics of the data. This is known as the [[Bias Variance Tradeoff|bias–variance tradeoff]]. Keeping a function simple to avoid overfitting may introduce a bias in the resulting predictions, while allowing it to be more complex leads to overfitting and a higher variance in the predictions. It is impossible to minimize both simultaneously.

## References

1.  ^   Mohri, M., Rostamizadeh A., Talwakar A., (2018) *Foundations of Machine learning*, 2nd ed., Boston: MIT Press
2.  Y S. Abu-Mostafa, M.Magdon-Ismail, and H.-T. Lin (2012) Learning from Data, AMLBook Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1600490064](https://en.wikipedia.org/wiki/Special:BookSources/978-1600490064)
3.  ^    Mukherjee, S.; Niyogi, P.; Poggio, T.; Rifkin., R. M. (2006). ["Learning theory: stability is sufficient for generalization and necessary and sufficient for consistency of empirical risk minimization"](http://cbcl.mit.edu/publications/ps/mukherjee-ACM-06.pdf) (PDF). *Adv. Comput. Math*. **25** (1–3): 161–193. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s10444-004-7634-z](https://doi.org/10.1007%2Fs10444-004-7634-z). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [2240256](https://api.semanticscholar.org/CorpusID:2240256).

## Further reading

- Olivier, Bousquet; Luxburg, Ulrike; Rätsch, Gunnar, eds. (2004). [Advanced Lectures on Machine Learning](https://link.springer.com/book/10.1007/b100712). Lecture Notes in Computer Science. Vol. 3176. pp. 169–207. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/b100712](https://doi.org/10.1007%2Fb100712). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-23122-6](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-23122-6). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [431437](https://api.semanticscholar.org/CorpusID:431437). Retrieved 10 December 2022.
- Bousquet, Olivier; Elisseeff, Andr´e (1 March 2002). ["Stability and Generalization"](https://dl.acm.org/doi/pdf/10.1162/153244302760200704). *The Journal of Machine Learning Research*. **2**: 499–526. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1162/153244302760200704](https://doi.org/10.1162%2F153244302760200704). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [1157797](https://api.semanticscholar.org/CorpusID:1157797). Retrieved 10 December 2022.
- Mohri, M., Rostamizadeh A., Talwakar A., (2018) *Foundations of Machine learning*, 2nd ed., Boston: MIT Press.
- Moody, J.E. (1992), "[The Effective Number of Parameters: An Analysis of Generalization and Regularization in Nonlinear Learning Systems](http://papers.nips.cc/paper/530-the-effective-number-of-parameters-an-analysis-of-generalization-and-regularization-in-nonlinear-learning-systems.pdf) [Archived](https://web.archive.org/web/20160910143237/http://papers.nips.cc/paper/530-the-effective-number-of-parameters-an-analysis-of-generalization-and-regularization-in-nonlinear-learning-systems.pdf) 2016-09-10 at the [Wayback Machine](https://en.wikipedia.org/wiki/Wayback_Machine)", in Moody, J.E., Hanson, S.J., and Lippmann, R.P., *Advances in Neural Information Processing Systems* 4, 847–854.
- White, H. (1992b), *Artificial Neural Networks: Approximation and Learning Theory*, Blackwell.
