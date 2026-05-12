[[ai-math.base]]

> Source: [[Statistical Learning Theory]]
> License: Wikipedia content is available under CC BY-SA 4.0.

**Statistical learning theory** is a framework for [machine learning](https://en.wikipedia.org/wiki/Machine_learning) drawing from the fields of [statistics](https://en.wikipedia.org/wiki/Statistics) and [functional analysis](https://en.wikipedia.org/wiki/Functional_analysis). Statistical learning theory deals with the [statistical inference](https://en.wikipedia.org/wiki/Statistical_inference) problem of finding a predictive function based on data. Statistical learning theory has led to successful applications in fields such as [computer vision](https://en.wikipedia.org/wiki/Computer_vision), [speech recognition](https://en.wikipedia.org/wiki/Speech_recognition), and [bioinformatics](https://en.wikipedia.org/wiki/Bioinformatics).

## Introduction

The goals of learning are understanding and prediction. Learning falls into many categories, including [supervised learning](https://en.wikipedia.org/wiki/Supervised_learning), [unsupervised learning](https://en.wikipedia.org/wiki/Unsupervised_learning), [online learning](https://en.wikipedia.org/wiki/Online_machine_learning), and [reinforcement learning](https://en.wikipedia.org/wiki/Reinforcement_learning). From the perspective of statistical learning theory, supervised learning is best understood. Supervised learning involves learning from a [training set](https://en.wikipedia.org/wiki/Training_set) of data. Every point in the training is an input–output pair, where the input maps to an output. The learning problem consists of inferring the function that maps between the input and the output, such that the learned function can be used to predict the output from future input.

Depending on the type of output, supervised learning problems are either problems of [regression](https://en.wikipedia.org/wiki/Regression_analysis) or problems of [classification](https://en.wikipedia.org/wiki/Statistical_classification). If the output takes a continuous range of values, it is a regression problem. Using [Ohm's law](https://en.wikipedia.org/wiki/Ohm%27s_law) as an example, a regression could be performed with voltage as input and current as an output. The regression would find the functional relationship between voltage and current to be $R$, such that 

$$
V=IR
$$

 Classification problems are those for which the output will be an element from a discrete set of labels. Classification is very common for machine learning applications. In [facial recognition](https://en.wikipedia.org/wiki/Facial_recognition_system), for instance, a picture of a person's face would be the input, and the output label would be that person's name. The input would be represented by a large multidimensional vector whose elements represent pixels in the picture.

After learning a function based on the training set data, that function is validated on a test set of data, data that did not appear in the training set.

## Formal description

Take $X$ to be the [[Vector Space]] of all possible inputs, and $Y$ to be the vector space of all possible outputs. Statistical learning theory takes the perspective that there is some unknown [probability distribution](https://en.wikipedia.org/wiki/Probability_distribution) over the product space $Z=X\times Y$, i.e. there exists some unknown $p(z)=p(\mathbf {x} ,y)$. The training set is made up of $n$ samples from this probability distribution, and is notated 

$$
S=\{(\mathbf {x} _{1},y_{1}),\dots ,(\mathbf {x} _{n},y_{n})\}=\{\mathbf {z} _{1},\dots ,\mathbf {z} _{n}\}
$$

 Every $\mathbf {x} _{i}$ is an input vector from the training data, and $y_{i}$ is the output that corresponds to it.

$$
I[f]=\int _{X\times Y}V(f(\mathbf {x} ),y)\,p(\mathbf {x} ,y)\,d\mathbf {x} \,dy
$$

$$
I[f]=\int _{X\times Y}V(f(\mathbf {x} ),y)\,p(\mathbf {x} ,y)\,d\mathbf {x} \,dy
$$

 The target function, the best possible function $f$ that can be chosen, is given by the $f$ that satisfies 

$$
f=\mathop {\operatorname {argmin} } _{h\in {\mathcal {H}}}I[h]
$$

$$
I_{S}[f]={\frac {1}{n}}\sum _{i=1}^{n}V(f(\mathbf {x} _{i}),y_{i})
$$

$$
I_{S}[f]={\frac {1}{n}}\sum _{i=1}^{n}V(f(\mathbf {x} _{i}),y_{i})
$$

 A learning algorithm that chooses the function $f_{S}$ that minimizes the empirical risk is called [[Empirical Risk Minimization]].

## Loss functions

The choice of loss function is a determining factor on the function $f_{S}$ that will be chosen by the learning algorithm. The loss function also affects the convergence rate for an algorithm. It is important for the loss function to be [convex](https://en.wikipedia.org/wiki/Convex_function).

Different loss functions are used depending on whether the problem is one of regression or one of classification.

### Regression

The most common loss function for regression is the square loss function (also known as the [L2-norm](https://en.wikipedia.org/wiki/L2-norm)). This familiar loss function is used in [Ordinary Least Squares regression](https://en.wikipedia.org/wiki/Ordinary_least_squares_regression). The form is: 

$$
V(f(\mathbf {x} ),y)=(y-f(\mathbf {x} ))^{2}
$$

The absolute value loss (also known as the [L1-norm](https://en.wikipedia.org/wiki/L1-norm)) is also sometimes used: 

$$
V(f(\mathbf {x} ),y)=|y-f(\mathbf {x} )|
$$

### Classification

In some sense the 0-1 [indicator function](https://en.wikipedia.org/wiki/Indicator_function) is the most natural loss function for classification. It takes the value 0 if the predicted output is the same as the actual output, and it takes the value 1 if the predicted output is different from the actual output. For binary classification with $Y=\{-1,1\}$, this is: 

$$
V(f(\mathbf {x} ),y)=\theta (-yf(\mathbf {x} ))
$$

 where $\theta$ is the [Heaviside step function](https://en.wikipedia.org/wiki/Heaviside_step_function).

## Regularization

![[media/fe79fbcf4142791723d8c5823053b8b1f2e31b29.jpg]]
This image represents an example of overfitting in machine learning. The red dots represent training set data. The green line represents the true functional relationship, while the blue line shows the learned function, which has been overfitted to the training set data.

In machine learning problems, a major problem that arises is that of [overfitting](https://en.wikipedia.org/wiki/Overfitting). Because learning is a prediction problem, the goal is not to find a function that most closely fits the (previously observed) data, but to find one that will most accurately predict output from future input. [[Empirical Risk Minimization]] runs this risk of overfitting: finding a function that matches the data exactly but does not predict future output well.

Overfitting is symptomatic of unstable solutions; a small perturbation in the training set data would cause a large variation in the learned function. It can be shown that if the stability for the solution can be guaranteed, generalization and consistency are guaranteed as well. [Regularization](https://en.wikipedia.org/wiki/Regularization_(mathematics) "Regularization (mathematics)") can solve the overfitting problem and give the problem stability.

Regularization can be accomplished by restricting the hypothesis space ${\mathcal {H}}$. A common example would be restricting ${\mathcal {H}}$ to linear functions: this can be seen as a reduction to the standard problem of [linear regression](https://en.wikipedia.org/wiki/Linear_regression). ${\mathcal {H}}$ could also be restricted to polynomial of degree $p$, exponentials, or bounded functions on [L1](https://en.wikipedia.org/wiki/Lp_space). Restriction of the hypothesis space avoids overfitting because the form of the potential functions are limited, and so does not allow for the choice of a function that gives empirical risk arbitrarily close to zero.

One example of regularization is [Tikhonov regularization](https://en.wikipedia.org/wiki/Tikhonov_regularization). This consists of minimizing 

$$
{\frac {1}{n}}\sum _{i=1}^{n}V(f(\mathbf {x} _{i}),y_{i})+\gamma \left\|f\right\|_{\mathcal {H}}^{2}
$$

 where $\gamma$ is a fixed and positive parameter, the regularization parameter. Tikhonov regularization ensures existence, uniqueness, and stability of the solution.

## Bounding empirical risk

Consider a binary classifier $f:{\mathcal {X}}\to \{0,1\}$. We can apply [Hoeffding's inequality](https://en.wikipedia.org/wiki/Hoeffding%27s_inequality) to bound the probability that the empirical risk deviates from the true risk to be a [Sub-Gaussian distribution](https://en.wikipedia.org/wiki/Sub-Gaussian_distribution). 

$$
\mathbb {P} (|{\hat {R}}(f)-R(f)|\geq \epsilon )\leq 2e^{-2n\epsilon ^{2}}
$$

 But generally, when we do empirical risk minimization, we are not given a classifier; we must choose it. Therefore, a more useful result is to bound the probability of the supremum of the difference over the whole class. 

$$
\mathbb {P} {\bigg (}\sup _{f\in {\mathcal {F}}}|{\hat {R}}(f)-R(f)|\geq \epsilon {\bigg )}\leq 2S({\mathcal {F}},n)e^{-n\epsilon ^{2}/8}\approx n^{d}e^{-n\epsilon ^{2}/8}
$$

 where $S({\mathcal {F}},n)$ is the [shattering number](https://en.wikipedia.org/wiki/Shattering_number) and $n$ is the number of samples in your dataset. The exponential term comes from Hoeffding but there is an extra cost of taking the supremum over the whole class, which is the shattering number.

## See also

- [Reproducing kernel Hilbert spaces](https://en.wikipedia.org/wiki/Reproducing_kernel_Hilbert_spaces) are a useful choice for ${\mathcal {H}}$.
- [Proximal gradient methods for learning](https://en.wikipedia.org/wiki/Proximal_gradient_methods_for_learning)
- [[Rademacher Complexity]]
- [Vapnik–Chervonenkis dimension](https://en.wikipedia.org/wiki/Vapnik%E2%80%93Chervonenkis_dimension)

## References

1.  [Vapnik, Vladimir N.](https://en.wikipedia.org/wiki/Vladimir_Vapnik) (1995). *The Nature of Statistical Learning Theory*. New York: Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-475-72440-0](https://en.wikipedia.org/wiki/Special:BookSources/978-1-475-72440-0).
2.  [Hastie, Trevor](https://en.wikipedia.org/wiki/Trevor_Hastie); Tibshirani, Robert; Friedman, Jerome H. (2009). *The Elements of Statistical Learning: Data Mining, Inference, and Prediction*. Springer Series in Statistics. New York, NY: Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-84857-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-84857-0).
3.  [Mohri, Mehryar](https://en.wikipedia.org/wiki/Mehryar_Mohri); Rostamizadeh, Afshin; Talwalkar, Ameet (2012). *Foundations of Machine Learning*. US, Massachusetts: MIT Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780262018258](https://en.wikipedia.org/wiki/Special:BookSources/9780262018258).
4.  Tomaso Poggio, Lorenzo Rosasco, et al. *Statistical Learning Theory and Applications*, 2012, [Class 1](https://www.mit.edu/~9.520/spring12/slides/class01/class01.pdf)
5.  Rosasco, Lorenzo; De Vito, Ernesto; Caponnetto, Andrea; Piana, Michele; Verri, Alessandro (2004-05-01). ["Are Loss Functions All the Same?"](https://direct.mit.edu/neco/article/16/5/1063-1076/6828). *Neural Computation*. **16** (5): 1063–1076. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1162/089976604773135104](https://doi.org/10.1162%2F089976604773135104). [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[11380/4590](https://hdl.handle.net/11380%2F4590). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0899-7667](https://search.worldcat.org/issn/0899-7667). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [15070510](https://pubmed.ncbi.nlm.nih.gov/15070510).
6.  Vapnik, V.N. and Chervonenkis, A.Y. 1971. [On the uniform convergence of relative frequencies of events to their probabilities](http://ai2-s2-pdfs.s3.amazonaws.com/a36b/028d024bf358c4af1a5e1dc3ca0aed23b553.pdf). *Theory of Probability and Its Applications* Vol 16, pp 264-280.
7.  Mukherjee, S., Niyogi, P. Poggio, T., and Rifkin, R. 2006. [Learning theory: stability is sufficient for generalization and necessary and sufficient for consistency of empirical risk minimization](https://link.springer.com/article/10.1007/s10444-004-7634-z). *Advances in Computational Mathematics*. Vol 25, pp 161-193.
8.  Tomaso Poggio, Lorenzo Rosasco, et al. *Statistical Learning Theory and Applications*, 2012, [Class 2](https://www.mit.edu/~9.520/spring12/slides/class02/class02.pdf)
