[[optimization.base]]

> Source: [[Stochastic Gradient Descent]]
> License: Wikipedia content is available under CC BY-SA 4.0.

**Stochastic gradient descent** (often abbreviated **SGD**) is an [iterative](https://en.wikipedia.org/wiki/Iterative_method) method for optimizing an [objective function](https://en.wikipedia.org/wiki/Objective_function) with suitable [smoothness](https://en.wikipedia.org/wiki/Smoothness) properties (e.g. [differentiable](https://en.wikipedia.org/wiki/Differentiable_function) or [subdifferentiable](https://en.wikipedia.org/wiki/Subderivative)). It can be regarded as a [stochastic approximation](https://en.wikipedia.org/wiki/Stochastic_approximation) of [[Gradient Descent]] optimization, since it replaces the actual gradient (calculated from the entire [data set](https://en.wikipedia.org/wiki/Data_set)) by an estimate thereof (calculated from a randomly selected subset of the data). Especially in [high-dimensional](https://en.wikipedia.org/wiki/High-dimensional) optimization problems this reduces the very high [computational burden](https://en.wikipedia.org/wiki/Computational_complexity), achieving faster iterations in exchange for a lower [convergence rate](https://en.wikipedia.org/wiki/Rate_of_convergence).

The basic idea behind stochastic approximation can be traced back to the Robbins–Monro algorithm of the 1950s. Today, stochastic gradient descent has become an important optimization method in [machine learning](https://en.wikipedia.org/wiki/Machine_learning).

## Background

Both [statistical](https://en.wikipedia.org/wiki/Statistics) [estimation](https://en.wikipedia.org/wiki/M-estimation) and [machine learning](https://en.wikipedia.org/wiki/Machine_learning) consider the problem of [minimizing](https://en.wikipedia.org/wiki/Mathematical_optimization) an [objective function](https://en.wikipedia.org/wiki/Objective_function) that has the form of a sum: 

$$
Q(w)={\frac {1}{n}}\sum _{i=1}^{n}Q_{i}(w),
$$

 where the [parameter](https://en.wikipedia.org/wiki/Parametric_statistics) $w$ that minimizes $Q(w)$ is to be [estimated](https://en.wikipedia.org/wiki/Estimator). Each summand function $Q_{i}$ is typically associated with the $i$-th [observation](https://en.wikipedia.org/wiki/Observation_(statistics)) in the [data set](https://en.wikipedia.org/wiki/Data_set) (used for training).

In classical statistics, sum-minimization problems arise in [least squares](https://en.wikipedia.org/wiki/Least_squares) and in [[Maximum Likelihood Estimation|maximum-likelihood estimation]] (for independent observations). The general class of estimators that arise as minimizers of sums are called [M-estimators](https://en.wikipedia.org/wiki/M-estimator). However, in statistics, it has been long recognized that requiring even local minimization is too restrictive for some problems of maximum-likelihood estimation. Therefore, contemporary statistical theorists often consider [stationary points](https://en.wikipedia.org/wiki/Stationary_point) of the [likelihood function](https://en.wikipedia.org/wiki/Likelihood_function) (or zeros of its derivative, the [score function](https://en.wikipedia.org/wiki/Score_(statistics)), and other [estimating equations](https://en.wikipedia.org/wiki/Estimating_equations)).

The sum-minimization problem also arises for [[Empirical Risk Minimization]]. There, $Q_{i}(w)$ is the value of the [loss function](https://en.wikipedia.org/wiki/Loss_function) at $i$-th example, and $Q(w)$ is the empirical risk.

When used to minimize the above function, a standard (or "batch") [[Gradient Descent]] method would perform the following iterations: 

$$
w:=w-\eta \,\nabla Q(w)=w-{\frac {\eta }{n}}\sum _{i=1}^{n}\nabla Q_{i}(w).
$$

 The step size is denoted by $\eta$ (sometimes called the *[learning rate](https://en.wikipedia.org/wiki/Learning_rate)* in machine learning) and here "$:=$" denotes the update of a variable in the algorithm.

In many cases, the summand functions have a simple form that enables inexpensive evaluations of the sum-function and the sum gradient. For example, in statistics, [one-parameter exponential families](https://en.wikipedia.org/wiki/Exponential_families) allow economical function-evaluations and gradient-evaluations.

However, in other cases, evaluating the sum-gradient may require expensive evaluations of the gradients from all summand functions. When the training set is enormous and no simple formulas exist, evaluating the sums of gradients becomes very expensive, because evaluating the gradient requires evaluating all the summand functions' gradients. To economize on the computational cost at every iteration, stochastic gradient descent [samples](https://en.wikipedia.org/wiki/Sampling_(statistics) "Sampling (statistics)") a subset of summand functions at every step. This is very effective in the case of large-scale machine learning problems.

## Iterative method

![[media/cea75bf07750edd1488f245d53cbd18307a51669.png]]
Fluctuations in the total objective function as gradient steps with respect to mini-batches are taken.

In stochastic (or "on-line") gradient descent, the true gradient of $Q(w)$ is approximated by a gradient at a single sample: 

$$
w:=w-\eta \,\nabla Q_{i}(w).
$$

 As the algorithm sweeps through the training set, it performs the above update for each training sample. Several passes can be made over the training set until the algorithm converges. If this is done, the data can be shuffled for each pass to prevent cycles. Typical implementations may use an [adaptive learning rate](https://en.wikipedia.org/wiki/Adaptive_learning_rate) so that the algorithm converges.

In pseudocode, stochastic gradient descent can be presented as :

- Choose an initial vector of parameters $w$ and learning rate $\eta$.
- Repeat until an approximate minimum is obtained:
  - Randomly shuffle samples in the training set.
  - For $i=1,2,...,n$, do:
    - $w:=w-\eta \,\nabla Q_{i}(w).$

A compromise between computing the true gradient and the gradient at a single sample is to compute the gradient against more than one training sample (called a "mini-batch") at each step. This can perform significantly better than "true" stochastic gradient descent described, because the code can make use of [vectorization](https://en.wikipedia.org/wiki/Vectorization_(mathematics) "Vectorization (mathematics)") libraries rather than computing each step separately as was first shown in  where it was called "the bunch-mode back-propagation algorithm". It may also result in smoother convergence, as the gradient computed at each step is averaged over more training samples.

## Linear regression

Suppose we want to fit a straight line ${\hat {y}}=w_{1}+w_{2}x$ to a training set with observations $((x_{1},y_{1}),(x_{2},y_{2})\ldots ,(x_{n},y_{n}))$ and corresponding estimated responses $({\hat {y}}_{1},{\hat {y}}_{2},\ldots ,{\hat {y}}_{n})$ using [least squares](https://en.wikipedia.org/wiki/Least_squares). The objective function to be minimized is 

$$
Q(w)=\sum _{i=1}^{n}Q_{i}(w)=\sum _{i=1}^{n}\left({\hat {y}}_{i}-y_{i}\right)^{2}=\sum _{i=1}^{n}\left(w_{1}+w_{2}x_{i}-y_{i}\right)^{2}.
$$

 The last line in the above pseudocode for this specific problem will become: 

$$
{\begin{bmatrix}w_{1}\\w_{2}\end{bmatrix}}\leftarrow {\begin{bmatrix}w_{1}\\w_{2}\end{bmatrix}}-\eta {\begin{bmatrix}{\frac {\partial }{\partial w_{1}}}(w_{1}+w_{2}x_{i}-y_{i})^{2}\\{\frac {\partial }{\partial w_{2}}}(w_{1}+w_{2}x_{i}-y_{i})^{2}\end{bmatrix}}={\begin{bmatrix}w_{1}\\w_{2}\end{bmatrix}}-\eta {\begin{bmatrix}2(w_{1}+w_{2}x_{i}-y_{i})\\2x_{i}(w_{1}+w_{2}x_{i}-y_{i})\end{bmatrix}}.
$$

Note that in each iteration or update step, the gradient is only evaluated at a single $x_{i}$. This is the key difference between stochastic gradient descent and batched gradient descent.

In general, given a linear regression ${\hat {y}}=\sum _{k\in 1:m}w_{k}x_{k}$ problem, stochastic gradient descent behaves differently when $m<n$ (underparameterized) and $m\geq n$ (overparameterized). In the overparameterized case, stochastic gradient descent converges to $\arg \min _{w:w^{T}x_{k}=y_{k}\forall k\in 1:n}\|w-w_{0}\|$. That is, SGD converges to the interpolation solution with minimum distance from the starting $w_{0}$. This is true even when the learning rate remains constant. In the underparameterized case, SGD does not converge if learning rate remains constant.

## History

[Backpropagation](https://en.wikipedia.org/wiki/Backpropagation) was first described in 1986, with stochastic gradient descent being used to efficiently optimize parameters across neural networks with multiple [hidden layers](https://en.wikipedia.org/wiki/Artificial_neural_network). Soon after, another improvement was developed: mini-batch gradient descent, where small batches of data are substituted for single samples. In 1997, the practical performance benefits from vectorization achievable with such small batches were first explored, paving the way for efficient optimization in machine learning. As of 2023, this mini-batch approach remains the norm for training neural networks, balancing the benefits of stochastic gradient descent with [[Gradient Descent]].

By the 1980s, [momentum](https://en.wikipedia.org/wiki/Momentum_(machine_learning)) had already been introduced, and was added to SGD optimization techniques in 1986. However, these optimization techniques assumed constant [hyperparameters](https://en.wikipedia.org/wiki/Hyperparameter_(machine_learning) "Hyperparameter (machine learning)"), i.e. a fixed learning rate and momentum parameter. In the 2010s, adaptive approaches to applying SGD with a per-parameter learning rate were introduced with AdaGrad (for "Adaptive Gradient") in 2011 and RMSprop (for "Root Mean Square Propagation") in 2012. In 2014, Adam (for "Adaptive Moment Estimation") was published, applying the adaptive approaches of RMSprop to momentum; many improvements and branches of Adam were then developed such as Adadelta, Adagrad, AdamW, and Adamax.

Within machine learning, approaches to optimization in 2023 are dominated by Adam-derived optimizers, [TensorFlow](https://en.wikipedia.org/wiki/TensorFlow) and [PyTorch](https://en.wikipedia.org/wiki/PyTorch), by far the most popular machine learning libraries, as of 2023 largely only include Adam-derived optimizers, as well as predecessors to Adam such as RMSprop and classic SGD. PyTorch also partially supports [limited-memory BFGS](https://en.wikipedia.org/wiki/Limited-memory_BFGS), a line-search method, but only for single-device setups without parameter groups.

## Notable applications

Stochastic gradient descent is a popular algorithm for training a wide range of models in [machine learning](https://en.wikipedia.org/wiki/Machine_learning), including (linear) [support vector machines](https://en.wikipedia.org/wiki/Support_vector_machine), [logistic regression](https://en.wikipedia.org/wiki/Logistic_regression) (see, e.g., [Vowpal Wabbit](https://en.wikipedia.org/wiki/Vowpal_Wabbit)) and [graphical models](https://en.wikipedia.org/wiki/Graphical_model). When combined with the [backpropagation](https://en.wikipedia.org/wiki/Backpropagation) algorithm, it is the *de facto* standard algorithm for training [artificial neural networks](https://en.wikipedia.org/wiki/Artificial_neural_network). Its use has been also reported in the [Geophysics](https://en.wikipedia.org/wiki/Geophysics) community, specifically to applications of Full Waveform Inversion (FWI).

Stochastic gradient descent competes with the [L-BFGS](https://en.wikipedia.org/wiki/Limited-memory_BFGS) algorithm,<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup> which is also widely used. Stochastic gradient descent has been used since at least 1960 for training [linear regression](https://en.wikipedia.org/wiki/Linear_regression) models, originally under the name [ADALINE](https://en.wikipedia.org/wiki/ADALINE).

Another stochastic gradient descent algorithm is the [least mean squares (LMS)](https://en.wikipedia.org/wiki/Least_mean_squares_filter) adaptive filter.

## Extensions and variants

Many improvements on the basic stochastic gradient descent algorithm have been proposed and used. In particular, in machine learning, the need to set a [learning rate](https://en.wikipedia.org/wiki/Learning_rate) (step size) has been recognized as problematic. Setting this parameter too high can cause the algorithm to diverge; setting it too low makes it slow to converge. A conceptually simple extension of stochastic gradient descent makes the learning rate a decreasing function η<sub>t</sub> of the iteration number t, giving a *learning rate schedule*, so that the first iterations cause large changes in the parameters, while the later ones do only fine-tuning. Such schedules have been known since the work of MacQueen on [k-means clustering](https://en.wikipedia.org/wiki/K-means_clustering). Practical guidance on choosing the step size in several variants of SGD is given by Spall.

![[media/670b16bb9511a02b7574bd0d8bd43b7f59500bdb.gif]]
A graph visualizing the behavior of a selected set of optimizers, using a 3D perspective projection of a loss function f(x, y)

![[media/090b969e46d817165ff6d5beb8ae53d4a40373f8.gif]]
A graph visualizing the behavior of a selected set of optimizers

### Implicit updates (ISGD)

As mentioned earlier, classical stochastic gradient descent is generally sensitive to [learning rate](https://en.wikipedia.org/wiki/Learning_rate) η. Fast convergence requires large learning rates but this may induce numerical instability. The problem can be largely solved by considering *implicit updates* whereby the stochastic gradient is evaluated at the next iterate rather than the current one: 

$$
w^{\text{new}}:=w^{\text{old}}-\eta \,\nabla Q_{i}(w^{\text{new}}).
$$

This equation is implicit since $w^{\text{new}}$ appears on both sides of the equation. It is a stochastic form of the [proximal gradient method](https://en.wikipedia.org/wiki/Proximal_gradient_method) since the update can also be written as: 

$$
w^{\text{new}}:=\arg \min _{w}\left\{Q_{i}(w)+{\frac {1}{2\eta }}\left\|w-w^{\text{old}}\right\|^{2}\right\}.
$$

As an example, consider least squares with features $x_{1},\ldots ,x_{n}\in \mathbb {R} ^{p}$ and observations $y_{1},\ldots ,y_{n}\in \mathbb {R}$. We wish to solve: 

$$
\min _{w}\sum _{j=1}^{n}\left(y_{j}-x_{j}'w\right)^{2},
$$

 where $x_{j}'w=x_{j1}w_{1}+x_{j,2}w_{2}+...+x_{j,p}w_{p}$ indicates the inner product. Note that $x$ could have "1" as the first element to include an intercept. Classical stochastic gradient descent proceeds as follows: 

$$
w^{\text{new}}=w^{\text{old}}+\eta \left(y_{i}-x_{i}'w^{\text{old}}\right)x_{i}
$$

where $i$ is uniformly sampled between 1 and $n$. Although theoretical convergence of this procedure happens under relatively mild assumptions, in practice the procedure can be quite unstable. In particular, when $\eta$ is misspecified so that $I-\eta x_{i}x_{i}'$ has large absolute eigenvalues with high probability, the procedure may diverge numerically within a few iterations. In contrast, *implicit stochastic gradient descent* (shortened as ISGD) can be solved in closed-form as: 

$$
w^{\text{new}}=w^{\text{old}}+{\frac {\eta }{1+\eta \left\|x_{i}\right\|^{2}}}\left(y_{i}-x_{i}'w^{\text{old}}\right)x_{i}.
$$

This procedure will remain numerically stable virtually for all $\eta$ as the [learning rate](https://en.wikipedia.org/wiki/Learning_rate) is now normalized. Such comparison between classical and implicit stochastic gradient descent in the least squares problem is very similar to the comparison between [least mean squares (LMS)](https://en.wikipedia.org/wiki/Least_mean_squares_filter) and [normalized least mean squares filter (NLMS)](https://en.wikipedia.org/wiki/Least_mean_squares_filter#Normalized_least_mean_squares_filter_(NLMS) "Least mean squares filter").

Even though a closed-form solution for ISGD is only possible in least squares, the procedure can be efficiently implemented in a wide range of models. Specifically, suppose that $Q_{i}(w)$ depends on $w$ only through a linear combination with features $x_{i}$, so that we can write $\nabla _{w}Q_{i}(w)=-q(x_{i}'w)x_{i}$, where $q()\in \mathbb {R}$ may depend on $x_{i},y_{i}$ as well but not on $w$ except through $x_{i}'w$. Least squares obeys this rule, and so does [logistic regression](https://en.wikipedia.org/wiki/Logistic_regression), and most [generalized linear models](https://en.wikipedia.org/wiki/Generalized_linear_model). For instance, in least squares, $q(x_{i}'w)=y_{i}-x_{i}'w$, and in logistic regression $q(x_{i}'w)=y_{i}-S(x_{i}'w)$, where $S(u)=e^{u}/(1+e^{u})$ is the [logistic function](https://en.wikipedia.org/wiki/Logistic_function). In [Poisson regression](https://en.wikipedia.org/wiki/Poisson_regression), $q(x_{i}'w)=y_{i}-e^{x_{i}'w}$, and so on.

In such settings, ISGD is simply implemented as follows. Let $f(\xi )=\eta q(x_{i}'w^{\text{old}}+\xi \|x_{i}\|^{2})$, where $\xi$ is scalar. Then, ISGD is equivalent to: 

$$
w^{\text{new}}=w^{\text{old}}+\xi ^{\ast }x_{i},~{\text{where}}~\xi ^{\ast }=f(\xi ^{\ast }).
$$

The scaling factor $\xi ^{\ast }\in \mathbb {R}$ can be found through the [bisection method](https://en.wikipedia.org/wiki/Bisection_method) since in most regular models, such as the aforementioned generalized linear models, function $q()$ is decreasing, and thus the search bounds for $\xi ^{\ast }$ are $[\min(0,f(0)),\max(0,f(0))]$.

### Momentum

Further proposals include the *momentum method* or the *heavy ball method*, which in ML context appeared in [Rumelhart](https://en.wikipedia.org/wiki/David_Rumelhart), [Hinton](https://en.wikipedia.org/wiki/Geoffrey_Hinton) and [Williams](https://en.wikipedia.org/wiki/Ronald_J._Williams)' paper on backpropagation learning and borrowed the idea from Soviet mathematician Boris Polyak's 1964 article on solving functional equations. Stochastic gradient descent with momentum remembers the update Δ*w* at each iteration, and determines the next update as a [linear combination](https://en.wikipedia.org/wiki/Linear_combination) of the gradient and the previous update: 

$$
\Delta w:=\alpha \Delta w-\eta \,\nabla Q_{i}(w)
$$

$$
w:=w+\Delta w
$$

 that leads to: 

$$
w:=w-\eta \,\nabla Q_{i}(w)+\alpha \Delta w
$$

where the [parameter](https://en.wikipedia.org/wiki/Parametric_statistics) $w$ which minimizes $Q(w)$ is to be [estimated](https://en.wikipedia.org/wiki/Estimator), $\eta$ is a step size (sometimes called the *[learning rate](https://en.wikipedia.org/wiki/Learning_rate)* in machine learning) and $\alpha$ is an exponential [decay factor](https://en.wikipedia.org/wiki/Learning_rate#Learning_rate_schedule) between 0 and 1 that determines the relative contribution of the current gradient and earlier gradients to the weight change.

The name momentum stems from an analogy to [momentum](https://en.wikipedia.org/wiki/Momentum) in physics: the weight vector $w$, thought of as a particle traveling through parameter space, incurs acceleration from the gradient of the loss ("[force](https://en.wikipedia.org/wiki/Force)"). Unlike in classical stochastic gradient descent, it tends to keep traveling in the same direction, preventing oscillations. Momentum has been used successfully by computer scientists in the training of [artificial neural networks](https://en.wikipedia.org/wiki/Artificial_neural_networks) for several decades. The *momentum method* is closely related to [underdamped Langevin dynamics](https://en.wikipedia.org/wiki/Langevin_dynamics), and may be combined with [simulated annealing](https://en.wikipedia.org/wiki/Simulated_annealing).

In mid-1980s the method was modified by [Yurii Nesterov](https://en.wikipedia.org/wiki/Yurii_Nesterov) to use the gradient predicted at the next point, and the resulting so-called *Nesterov Accelerated Gradient* was sometimes used in ML in the 2010s.

### Averaging

*Averaged stochastic gradient descent*, invented independently by Ruppert and Polyak in the late 1980s, is ordinary stochastic gradient descent that records an average of its parameter vector over time. That is, the update is the same as for ordinary stochastic gradient descent, but the algorithm also keeps track of

$$
{\bar {w}}={\frac {1}{t}}\sum _{i=0}^{t-1}w_{i}.
$$

When optimization is done, this averaged parameter vector takes the place of w.

### AdaGrad

*AdaGrad* (for adaptive [[Gradient Descent|gradient]] algorithm) is a modified stochastic gradient descent algorithm with per-parameter [learning rate](https://en.wikipedia.org/wiki/Learning_rate), first published in 2011. Informally, this increases the learning rate for sparser parameters<sup>\[*[clarification needed](https://en.wikipedia.org/wiki/Wikipedia:Please_clarify)*\]</sup> and decreases the learning rate for ones that are less sparse. This strategy often improves convergence performance over standard stochastic gradient descent in settings where data is sparse and sparse parameters are more informative. Examples of such applications include natural language processing and image recognition.

It still has a base learning rate η, but this is multiplied with the elements of a vector {*G*<sub>*j*,*j*</sub>}  which is the diagonal of the [outer product](https://en.wikipedia.org/wiki/Outer_product) matrix

$$
G=\sum _{\tau =1}^{t}g_{\tau }g_{\tau }^{\mathsf {T}}
$$

where $g_{\tau }=\nabla Q_{i}(w)$, the gradient, at iteration τ. The diagonal is given by

$$
G_{j,j}=\sum _{\tau =1}^{t}g_{\tau ,j}^{2}.
$$

This vector essentially stores a historical sum of gradient squares by dimension and is updated after every iteration. The formula for an update is now 

$$
w:=w-\eta \,\mathrm {diag} (G)^{-{\frac {1}{2}}}\odot g
$$

 or, written as per-parameter updates, 

$$
w_{j}:=w_{j}-{\frac {\eta }{\sqrt {G_{j,j}}}}g_{j}.
$$

 Each {*G*<sub>(*i*,*i*)</sub>}  gives rise to a scaling factor for the learning rate that applies to a single parameter *w*<sub>*i*</sub>. Since the denominator in this factor, ${\sqrt {G_{i}}}={\sqrt {\sum _{\tau =1}^{t}g_{\tau }^{2}}}$ is the [*ℓ*<sub>2</sub> norm](https://en.wikipedia.org/wiki/Norm_(mathematics)#Euclidean_norm "Norm (mathematics)") of previous derivatives, extreme parameter updates get dampened, while parameters that get few or small updates receive higher learning rates.

While designed for [[Convex Optimization|convex problems]], AdaGrad has been successfully applied to non-convex optimization.

### RMSProp

*RMSProp* (for Root Mean Square Propagation) is a method invented in 2012 by James Martens and [Ilya Sutskever](https://en.wikipedia.org/wiki/Ilya_Sutskever), at the time both PhD students in Geoffrey Hinton's group, in which the [learning rate](https://en.wikipedia.org/wiki/Learning_rate) is, like in Adagrad, adapted for each of the parameters. The idea is to divide the learning rate for a weight by a running average of the magnitudes of recent gradients for that weight. Unusually, it was not published in an article but merely described in a [Coursera](https://en.wikipedia.org/wiki/Coursera) lecture.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>  

So, first the running average is calculated in terms of means square,

$$
v(w,t):=\gamma v(w,t-1)+\left(1-\gamma \right)\left(\nabla Q_{i}(w)\right)^{2}
$$

where, $\gamma$ is the forgetting factor. The concept of storing the historical gradient as sum of squares is borrowed from Adagrad, but "forgetting" is introduced to solve Adagrad's diminishing learning rates in non-convex problems by gradually decreasing the influence of old data.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

And the parameters are updated as,

$$
w:=w-{\frac {\eta }{\sqrt {v(w,t)}}}\nabla Q_{i}(w)
$$

RMSProp has shown good adaptation of learning rate in different applications. RMSProp can be seen as a generalization of [Rprop](https://en.wikipedia.org/wiki/Rprop) and is capable to work with mini-batches as well opposed to only full-batches.

### Adam

*Adam* (short for Adaptive Moment Estimation) is a 2014 update to the *RMSProp* optimizer combining it with the main feature of the *Momentum method*. In this optimization algorithm, running averages with exponential forgetting of both the gradients and the second moments of the gradients are used. Given parameters $w^{(t)}$ and a loss function $L^{(t)}$, where $t$ indexes the current training iteration (indexed at $1$), Adam's parameter update is given by:

$$
m_{w}^{(t)}:=\beta _{1}m_{w}^{(t-1)}+\left(1-\beta _{1}\right)\nabla _{w}L^{(t-1)}
$$

$$
v_{w}^{(t)}:=\beta _{2}v_{w}^{(t-1)}+\left(1-\beta _{2}\right)\left(\nabla _{w}L^{(t-1)}\right)^{2}
$$

$$
{\hat {m}}_{w}^{(t)}={\frac {m_{w}^{(t)}}{1-\beta _{1}^{t}}}
$$

$$
{\hat {v}}_{w}^{(t)}={\frac {v_{w}^{(t)}}{1-\beta _{2}^{t}}}
$$

$$
w^{(t)}:=w^{(t-1)}-\eta {\frac {{\hat {m}}_{w}^{(t)}}{{\sqrt {{\hat {v}}_{w}^{(t)}}}+\varepsilon }}
$$

 where $\varepsilon$ is a small scalar (e.g. $10^{-8}$) used to prevent division by 0, and $\beta _{1}$ (e.g. 0.9) and $\beta _{2}$ (e.g. 0.999) are the forgetting factors for gradients and second moments of gradients, respectively. Squaring and square-rooting is done element-wise.

As the exponential moving averages of the gradient $m_{w}^{(t)}$ and the squared gradient $v_{w}^{(t)}$ are initialized with a vector of 0's, there would be a bias towards zero in the first training iterations. A factor ${\tfrac {1}{1-\beta _{1/2}^{t}}}$ is introduced to compensate this bias and get better estimates ${\hat {m}}_{w}^{(t)}$ and ${\hat {v}}_{w}^{(t)}$.

The initial proof establishing the convergence of Adam was incomplete, and subsequent analysis has revealed that Adam does not converge for all convex objectives. Despite this, *Adam* continues to be used due to its strong performance in practice.

#### Variants

The popularity of *Adam* inspired many variants and enhancements. Some examples include:

- Nesterov-enhanced gradients: *NAdam*, *FASFA*
- varying interpretations of second-order information: *Powerpropagation* and *AdaSqrt*.
- Using [infinity norm](https://en.wikipedia.org/wiki/Uniform_norm): *AdaMax*
- *AMSGrad*, which improves convergence over *Adam* by using maximum of past squared gradients instead of the exponential average. *AdamX* further improves convergence over *AMSGrad*.
- *AdamW*, which improves the [weight decay](https://en.wikipedia.org/wiki/Weight_decay).

### Sign-based stochastic gradient descent

Even though sign-based optimization goes back to the aforementioned *Rprop*, in 2018 researchers tried to simplify Adam by removing the magnitude of the stochastic gradient from being taken into account and only considering its sign. This results in a significantly lower communication cost of transferring gradients from workers to the parameter server. In this sense, it serves to better compress the gradient information, while having comparable convergence to standard SGD.

### Backtracking line search

[Backtracking line search](https://en.wikipedia.org/wiki/Backtracking_line_search) is another variant of gradient descent. All of the below are sourced from the mentioned link. It is based on a condition known as the Armijo–Goldstein condition. Both methods allow learning rates to change at each iteration; however, the manner of the change is different. Backtracking line search uses function evaluations to check Armijo's condition, and in principle the loop in the algorithm for determining the learning rates can be long and unknown in advance. Adaptive SGD does not need a loop in determining learning rates. On the other hand, adaptive SGD does not guarantee the "descent property" – which Backtracking line search enjoys – which is that $f(x_{n+1})\leq f(x_{n})$ for all n. If the gradient of the cost function is globally Lipschitz continuous, with Lipschitz constant L, and learning rate is chosen of the order 1/L, then the standard version of SGD is a special case of backtracking line search.

### Second-order methods

A stochastic analogue of the standard (deterministic) [Newton–Raphson algorithm](https://en.wikipedia.org/wiki/Newton%27s_method_in_optimization) (a "second-order" method) provides an asymptotically optimal or near-optimal form of iterative optimization in the setting of stochastic approximation<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>. A method that uses direct measurements of the [[Hessian Matrix|Hessian matrices]] of the summands in the empirical risk function was developed by Byrd, Hansen, Nocedal, and Singer. However, directly determining the required Hessian matrices for optimization may not be possible in practice. Practical and theoretically sound methods for second-order versions of SGD that do not require direct Hessian information are given by Spall and others. (A less efficient method based on finite differences, instead of simultaneous perturbations, is given by Ruppert.) Another approach to the approximation Hessian matrix is replacing it with the Fisher information matrix, which transforms usual gradient to natural. These methods not requiring direct Hessian information are based on either values of the summands in the above empirical risk function or values of the gradients of the summands (i.e., the SGD inputs). In particular, second-order optimality is asymptotically achievable without direct calculation of the Hessian matrices of the summands in the empirical risk function. When the objective is a [nonlinear least-squares](https://en.wikipedia.org/wiki/Non-linear_least_squares) loss 

$$
Q(w)={\frac {1}{n}}\sum _{i=1}^{n}Q_{i}(w)={\frac {1}{n}}\sum _{i=1}^{n}(m(w;x_{i})-y_{i})^{2},
$$

 where $m(w;x_{i})$ is the predictive model (e.g., a [deep neural network](https://en.wikipedia.org/wiki/Neural_network_(machine_learning) "Neural network (machine learning)")) the objective's structure can be exploited to estimate 2nd order information using gradients only. The resulting methods are simple and often effective

## Approximations in continuous time

For small learning rate $\eta$ stochastic gradient descent $(w_{n})_{n\in \mathbb {N} _{0}}$ can be viewed as a discretization of the [gradient flow](https://en.wikipedia.org/wiki/Gradient_flow) ODE

$$
{\frac {d}{dt}}W_{t}=-\nabla Q(W_{t})
$$

subject to additional stochastic noise. This approximation is only valid on a finite time-horizon in the following sense: assume that all the coefficients $Q_{i}$ are sufficiently smooth. Let $T>0$ and $g:\mathbb {R} ^{d}\to \mathbb {R}$ be a sufficiently smooth test function. Then, there exists a constant $C>0$ such that for all $\eta >0$

$$
\max _{k=0,\dots ,\lfloor T/\eta \rfloor }\left|\mathbb {E} [g(w_{k})]-g(W_{k\eta })\right|\leq C\eta ,
$$

where $\mathbb {E}$ denotes taking the expectation with respect to the random choice of indices in the stochastic gradient descent scheme.

Since this approximation does not capture the random fluctuations around the mean behavior of stochastic gradient descent solutions to [[Stochastic Differential Equations]] (SDEs) have been proposed as limiting objects. More precisely, the solution to the SDE

$$
dW_{t}=-\nabla \left(Q(W_{t})+{\tfrac {1}{4}}\eta |\nabla Q(W_{t})|^{2}\right)dt+{\sqrt {\eta }}\Sigma (W_{t})^{1/2}dB_{t},
$$

for 

$$
\Sigma (w)={\frac {1}{n^{2}}}\left(\sum _{i=1}^{n}Q_{i}(w)-Q(w)\right)\left(\sum _{i=1}^{n}Q_{i}(w)-Q(w)\right)^{T}
$$

 where $dB_{t}$ denotes the [Ito-integral](https://en.wikipedia.org/wiki/Ito_integral) with respect to a [[Brownian Motion]] is a more precise approximation in the sense that there exists a constant $C>0$ such that

$$
\max _{k=0,\dots ,\lfloor T/\eta \rfloor }\left|\mathbb {E} [g(w_{k})]-\mathbb {E} [g(W_{k\eta })]\right|\leq C\eta ^{2}.
$$

However this SDE only approximates the one-point motion of stochastic gradient descent. For an approximation of the [stochastic flow](https://en.wikipedia.org/wiki/Flow_(mathematics) "Flow (mathematics)") one has to consider SDEs with infinite-dimensional noise.

## See also

- [Backtracking line search](https://en.wikipedia.org/wiki/Backtracking_line_search)
- [Broken Neural Scaling Law](https://en.wikipedia.org/wiki/Broken_Neural_Scaling_Law)
- [[Coordinate Descent]] – changes one coordinate at a time, rather than one example
- [Linear classifier](https://en.wikipedia.org/wiki/Linear_classifier)
- [Online machine learning](https://en.wikipedia.org/wiki/Online_machine_learning)
- [Stochastic hill climbing](https://en.wikipedia.org/wiki/Stochastic_hill_climbing)
- [Stochastic variance reduction](https://en.wikipedia.org/wiki/Stochastic_variance_reduction)

## Notes

1.  $\odot$ denotes the [element-wise product](https://en.wikipedia.org/wiki/Hadamard_product_(matrices) "Hadamard product (matrices)").

## References

1.  [Bottou, Léon](https://en.wikipedia.org/wiki/L%C3%A9on_Bottou); Bousquet, Olivier (2012). ["The Tradeoffs of Large Scale Learning"](https://books.google.com/books?id=JPQx7s2L1A8C&pg=PA351). In Sra, Suvrit; Nowozin, Sebastian; Wright, Stephen J. (eds.). *Optimization for Machine Learning*. Cambridge: MIT Press. pp. 351–368. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-262-01646-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-262-01646-9).
2.  ^   [Bottou, Léon](https://en.wikipedia.org/wiki/L%C3%A9on_Bottou) (1998). "Online Algorithms and Stochastic Approximations". [Online Learning and Neural Networks](https://archive.org/details/onlinelearningin0000unse). Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-65263-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-65263-6).
3.  [Ferguson, Thomas S.](https://en.wikipedia.org/wiki/Thomas_S._Ferguson) (1982). "An inconsistent maximum likelihood estimate". *Journal of the American Statistical Association*. **77** (380): 831–834. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/01621459.1982.10477894](https://doi.org/10.1080%2F01621459.1982.10477894). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2287314](https://www.jstor.org/stable/2287314).
4.  [Bottou, Léon](https://en.wikipedia.org/wiki/L%C3%A9on_Bottou); Bousquet, Olivier (2008). [The Tradeoffs of Large Scale Learning](http://leon.bottou.org/papers/bottou-bousquet-2008). [Advances in Neural Information Processing Systems](https://en.wikipedia.org/wiki/Advances_in_Neural_Information_Processing_Systems). Vol. 20. pp. 161–168.
5.  Murphy, Kevin (2021). [Probabilistic Machine Learning: An Introduction](https://probml.github.io/pml-book/book1.html). MIT Press. Retrieved 10 April 2021.
6.  Bilmes, Jeff; [Asanovic, Krste](https://en.wikipedia.org/wiki/Krste_Asanovi%C4%87); Chin, Chee-Whye; Demmel, James (April 1997). "Using PHiPAC to speed error back-propagation learning". *1997 IEEE International Conference on Acoustics, Speech, and Signal Processing*. ICASSP. Munich, Germany: IEEE. pp. 4153–4156 vol.5. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/ICASSP.1997.604861](https://doi.org/10.1109%2FICASSP.1997.604861).
7.  Kiwiel, Krzysztof C. (2001). "Convergence and efficiency of subgradient methods for quasiconvex minimization". *Mathematical Programming, Series A*. **90** (1). Berlin, Heidelberg: Springer: 1–25. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/PL00011414](https://doi.org/10.1007%2FPL00011414). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0025-5610](https://search.worldcat.org/issn/0025-5610). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1819784](https://mathscinet.ams.org/mathscinet-getitem?mr=1819784). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [10043417](https://api.semanticscholar.org/CorpusID:10043417).
8.  [Robbins, Herbert](https://en.wikipedia.org/wiki/Herbert_Robbins); [Siegmund, David O.](https://en.wikipedia.org/wiki/David_O._Siegmund) (1971). "A convergence theorem for non negative almost supermartingales and some applications". In Rustagi, Jagdish S. (ed.). *Optimizing Methods in Statistics*. Academic Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-12-604550-X](https://en.wikipedia.org/wiki/Special:BookSources/0-12-604550-X).
9.  Belkin, Mikhail (May 2021). ["Fit without fear: remarkable mathematical phenomena of deep learning through the prism of interpolation"](https://www.cambridge.org/core/journals/acta-numerica/article/abs/fit-without-fear-remarkable-mathematical-phenomena-of-deep-learning-through-the-prism-of-interpolation/DBAC769EB7F4DBA5C4720932C2826014). *Acta Numerica*. **30**: 203–248. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2105.14368](https://arxiv.org/abs/2105.14368). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1017/S0962492921000039](https://doi.org/10.1017%2FS0962492921000039). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0962-4929](https://search.worldcat.org/issn/0962-4929).
10. [Robbins, H.](https://en.wikipedia.org/wiki/Herbert_Robbins); Monro, S. (1951). ["A Stochastic Approximation Method"](https://doi.org/10.1214%2Faoms%2F1177729586). *The Annals of Mathematical Statistics*. **22** (3): 400. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/aoms/1177729586](https://doi.org/10.1214%2Faoms%2F1177729586).
11. Kiefer, J.; Wolfowitz, J. (1952). ["Stochastic Estimation of the Maximum of a Regression Function"](https://doi.org/10.1214%2Faoms%2F1177729392). *The Annals of Mathematical Statistics*. **23** (3): 462–466. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/aoms/1177729392](https://doi.org/10.1214%2Faoms%2F1177729392).
12. Rosenblatt, F. (1958). "The perceptron: A probabilistic model for information storage and organization in the brain". *Psychological Review*. **65** (6): 386–408. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1037/h0042519](https://doi.org/10.1037%2Fh0042519). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [13602029](https://pubmed.ncbi.nlm.nih.gov/13602029). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [12781225](https://api.semanticscholar.org/CorpusID:12781225).
13. Bilmes, Jeff; [Asanovic, Krste](https://en.wikipedia.org/wiki/Krste_Asanovi%C4%87); Chin, Chee-Whye; Demmel, James (April 1997). "Using PHiPAC to speed error back-propagation learning". *1997 IEEE International Conference on Acoustics, Speech, and Signal Processing*. ICASSP. Munich, Germany: IEEE. pp. 4153–4156 vol.5. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/ICASSP.1997.604861](https://doi.org/10.1109%2FICASSP.1997.604861).
14. Peng, Xinyu; Li, Li; Wang, Fei-Yue (2020). "Accelerating Minibatch Stochastic Gradient Descent Using Typicality Sampling". *IEEE Transactions on Neural Networks and Learning Systems*. **31** (11): 4649–4659. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1903.04192](https://arxiv.org/abs/1903.04192). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2020ITNNL..31.4649P](https://ui.adsabs.harvard.edu/abs/2020ITNNL..31.4649P). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/TNNLS.2019.2957003](https://doi.org/10.1109%2FTNNLS.2019.2957003). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [31899442](https://pubmed.ncbi.nlm.nih.gov/31899442). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [73728964](https://api.semanticscholar.org/CorpusID:73728964).
15. Rumelhart, David E.; Hinton, Geoffrey E.; Williams, Ronald J. (October 1986). ["Learning representations by back-propagating errors"](https://www.nature.com/articles/323533a0). *Nature*. **323** (6088): 533–536. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1986Natur.323..533R](https://ui.adsabs.harvard.edu/abs/1986Natur.323..533R). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1038/323533a0](https://doi.org/10.1038%2F323533a0). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1476-4687](https://search.worldcat.org/issn/1476-4687). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [205001834](https://api.semanticscholar.org/CorpusID:205001834).
16. Duchi, John; Hazan, Elad; Singer, Yoram (2011). ["Adaptive subgradient methods for online learning and stochastic optimization"](http://jmlr.org/papers/volume12/duchi11a/duchi11a.pdf) (PDF). *[JMLR](https://en.wikipedia.org/wiki/Journal_of_Machine_Learning_Research)*. **12**: 2121–2159.
17. [Hinton, Geoffrey](https://en.wikipedia.org/wiki/Geoffrey_Hinton). ["Lecture 6e rmsprop: Divide the gradient by a running average of its recent magnitude"](http://www.cs.toronto.edu/~tijmen/csc321/slides/lecture_slides_lec6.pdf) (PDF). p. 26. Retrieved 19 March 2020.
18. Kingma, Diederik; Ba, Jimmy (2014). "Adam: A Method for Stochastic Optimization". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1412.6980](https://arxiv.org/abs/1412.6980) \[[cs.LG](https://arxiv.org/archive/cs.LG)\].
19. ^   ["torch.optim — PyTorch 2.0 documentation"](https://pytorch.org/docs/stable/optim.html). *pytorch.org*. Retrieved 2023-10-02.
20. Nguyen, Giang; Dlugolinsky, Stefan; Bobák, Martin; Tran, Viet; García, Álvaro; Heredia, Ignacio; Malík, Peter; Hluchý, Ladislav (19 January 2019). ["Machine Learning and Deep Learning frameworks and libraries for large-scale data mining: a survey"](https://link.springer.com/content/pdf/10.1007/s10462-018-09679-z.pdf) (PDF). *Artificial Intelligence Review*. **52**: 77–124. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s10462-018-09679-z](https://doi.org/10.1007%2Fs10462-018-09679-z). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [254236976](https://api.semanticscholar.org/CorpusID:254236976).
21. ["Module: tf.keras.optimizers | TensorFlow v2.14.0"](https://www.tensorflow.org/api_docs/python/tf/keras/optimizers). *TensorFlow*. Retrieved 2023-10-02.
22. Jenny Rose Finkel, Alex Kleeman, Christopher D. Manning (2008). [Efficient, Feature-based, Conditional Random Field Parsing](http://www.aclweb.org/anthology/P08-1109). Proc. Annual Meeting of the ACL.
23. [LeCun, Yann A., et al. "Efficient backprop." Neural networks: Tricks of the trade. Springer Berlin Heidelberg, 2012. 9-48](http://yann.lecun.com/exdb/publis/pdf/lecun-98b.pdf)
24. [Jerome R. Krebs, John E. Anderson, David Hinkley, Ramesh Neelamani, Sunwoong Lee, Anatoly Baumstein, and Martin-Daniel Lacasse, (2009), "Fast full-wavefield seismic inversion using encoded sources," GEOPHYSICS 74: WCC177-WCC188.](https://library.seg.org/doi/abs/10.1190/1.3230502)
25. Avi Pfeffer. ["CS181 Lecture 5 — Perceptrons"](http://www.seas.harvard.edu/courses/cs181/files/lecture05-notes.pdf) (PDF). Harvard University.<sup>\[*[permanent dead link](https://en.wikipedia.org/wiki/Wikipedia:Link_rot)*\]</sup>
26. [Goodfellow, Ian](https://en.wikipedia.org/wiki/Ian_Goodfellow); Bengio, Yoshua; Courville, Aaron (2016). [Deep Learning](https://www.deeplearningbook.org). MIT Press. p. 291. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0262035613](https://en.wikipedia.org/wiki/Special:BookSources/978-0262035613).
27. Cited by Darken, Christian; Moody, John (1990). *Fast adaptive k-means clustering: some empirical results*. Int'l Joint Conf. on Neural Networks (IJCNN). IEEE. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/IJCNN.1990.137720](https://doi.org/10.1109%2FIJCNN.1990.137720).
28. Spall, J. C. (2003). *Introduction to Stochastic Search and Optimization: Estimation, Simulation, and Control*. Hoboken, NJ: Wiley. pp. Sections 4.4, 6.6, and 7.5. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-33052-3](https://en.wikipedia.org/wiki/Special:BookSources/0-471-33052-3).
29. Toulis, Panos; Airoldi, Edoardo (2017). "Asymptotic and finite-sample properties of estimators based on stochastic gradients". *Annals of Statistics*. **45** (4): 1694–1727. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1408.2923](https://arxiv.org/abs/1408.2923). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/16-AOS1506](https://doi.org/10.1214%2F16-AOS1506). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [10279395](https://api.semanticscholar.org/CorpusID:10279395).
30. ^   Rumelhart, David E.; Hinton, Geoffrey E.; Williams, Ronald J. (8 October 1986). "Learning representations by back-propagating errors". *Nature*. **323** (6088): 533–536. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1986Natur.323..533R](https://ui.adsabs.harvard.edu/abs/1986Natur.323..533R). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1038/323533a0](https://doi.org/10.1038%2F323533a0). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [205001834](https://api.semanticscholar.org/CorpusID:205001834).
31. ["Gradient Descent and Momentum: The Heavy Ball Method"](https://boostedml.com/2020/07/gradient-descent-and-momentum-the-heavy-ball-method.html). 13 July 2020.
32. Sutskever, Ilya; Martens, James; Dahl, George; Hinton, Geoffrey E. (June 2013). Sanjoy Dasgupta and David Mcallester (ed.). [On the importance of initialization and momentum in deep learning](http://www.cs.utoronto.ca/~ilya/pubs/2013/1051_2.pdf) (PDF). In Proceedings of the 30th international conference on machine learning (ICML-13). Vol. 28. Atlanta, GA. pp. 1139–1147. Retrieved 14 January 2016.
33. Sutskever, Ilya (2013). [Training recurrent neural networks](http://www.cs.utoronto.ca/~ilya/pubs/ilya_sutskever_phd_thesis.pdf) (PDF) (Ph.D.). University of Toronto. p. 74.
34. ^   Zeiler, Matthew D. (2012). "ADADELTA: An adaptive learning rate method". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1212.5701](https://arxiv.org/abs/1212.5701) \[[cs.LG](https://arxiv.org/archive/cs.LG)\].
35. Borysenko, Oleksandr; Byshkin, Maksym (2021). ["CoolMomentum: A Method for Stochastic Optimization by Langevin Dynamics with Simulated Annealing"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8139967). *Scientific Reports*. **11** (1): 10705. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2005.14605](https://arxiv.org/abs/2005.14605). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2021NatSR..1110705B](https://ui.adsabs.harvard.edu/abs/2021NatSR..1110705B). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1038/s41598-021-90144-3](https://doi.org/10.1038%2Fs41598-021-90144-3). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [8139967](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8139967). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [34021212](https://pubmed.ncbi.nlm.nih.gov/34021212).
36. ["Papers with Code - Nesterov Accelerated Gradient Explained"](https://paperswithcode.com/method/nesterov-accelerated-gradient).
37. Polyak, Boris T.; Juditsky, Anatoli B. (1992). poljud92.pdf (PDF). *SIAM J. Control Optim*. **30** (4): 838–855. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/0330046](https://doi.org/10.1137%2F0330046). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [3548228](https://api.semanticscholar.org/CorpusID:3548228). Archived from poljud92.pdf (PDF) on 2016-01-12. Retrieved 2018-02-14.
38. ^   Duchi, John; Hazan, Elad; Singer, Yoram (2011). ["Adaptive subgradient methods for online learning and stochastic optimization"](http://jmlr.org/papers/volume12/duchi11a/duchi11a.pdf) (PDF). *[JMLR](https://en.wikipedia.org/wiki/Journal_of_Machine_Learning_Research)*. **12**: 2121–2159.
39. Gupta, Maya R.; Bengio, Samy; Weston, Jason (2014). ["Training highly multiclass classifiers"](http://jmlr.org/papers/volume15/gupta14a/gupta14a.pdf) (PDF). *JMLR*. **15** (1): 1461–1492.
40. ^   [Hinton, Geoffrey](https://en.wikipedia.org/wiki/Geoffrey_Hinton). ["Lecture 6e rmsprop: Divide the gradient by a running average of its recent magnitude"](http://www.cs.toronto.edu/~tijmen/csc321/slides/lecture_slides_lec6.pdf) (PDF). p. 26. Retrieved 19 March 2020.
41. ["RMSProp"](https://deepai.org/machine-learning-glossary-and-terms/rmsprop). *DeepAI*. 17 May 2019. Retrieved 2025-06-15. “The RMSProp algorithm was introduced by Geoffrey Hinton in his Coursera class, where he credited its effectiveness in various applications.”
42. Geoffrey Hinton (2016-11-16). [Lecture 6.5 — RMSprop, Adam, Dropout and Batch Normalization](https://www.youtube.com/watch?v=-eyhCTvrEtE&t=36m37s). *YouTube*. University of Toronto. Event occurs at 36:37. Retrieved 2025-06-15.
43. ^   Kingma, Diederik; Ba, Jimmy (2014). "Adam: A Method for Stochastic Optimization". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1412.6980](https://arxiv.org/abs/1412.6980) \[[cs.LG](https://arxiv.org/archive/cs.LG)\].
44. ["4. Beyond Gradient Descent - Fundamentals of Deep Learning [Book]"](https://www.oreilly.com/library/view/fundamentals-of-deep/9781491925607/ch04.html).
45. Reddi, Sashank J.; Kale, Satyen; Kumar, Sanjiv (2018). [On the Convergence of Adam and Beyond](https://openreview.net/forum?id=ryQu7f-RZ). 6th International Conference on Learning Representations (ICLR 2018). [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1904.09237](https://arxiv.org/abs/1904.09237).
46. Rubio, David Martínez (2017). [Convergence Analysis of an Adaptive Method of Gradient Descent](https://damaru2.github.io/convergence_analysis_hypergradient_descent/dissertation_hypergradients.pdf) (PDF) (Master thesis). University of Oxford. Retrieved 5 January 2024.
47. Zhang, Yushun; Chen, Congliang; Shi, Naichen; Sun, Ruoyu; Luo, Zhi-Quan (2022). "Adam Can Converge Without Any Modification On Update Rules". *Advances in Neural Information Processing Systems 35*. Advances in Neural Information Processing Systems 35 (NeurIPS 2022). [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2208.09632](https://arxiv.org/abs/2208.09632).
48. Dozat, T. (2016). "Incorporating Nesterov Momentum into Adam". [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [70293087](https://api.semanticscholar.org/CorpusID:70293087). `{{`[`cite journal`](https://en.wikipedia.org/wiki/Template:Cite_journal)`}}`: Cite journal requires `|journal=` ([help](https://en.wikipedia.org/wiki/Help:CS1_errors#missing_periodical))
49. Naveen, Philip (2022-08-09). ["FASFA: A Novel Next-Generation Backpropagation Optimizer"](https://doi.org/10.36227%2Ftechrxiv.20427852.v1). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.36227/techrxiv.20427852.v1](https://doi.org/10.36227%2Ftechrxiv.20427852.v1). `{{`[`cite journal`](https://en.wikipedia.org/wiki/Template:Cite_journal)`}}`: Cite journal requires `|journal=` ([help](https://en.wikipedia.org/wiki/Help:CS1_errors#missing_periodical))
50. Whye, Schwarz, Jonathan Jayakumar, Siddhant M. Pascanu, Razvan Latham, Peter E. Teh, Yee (2021-10-01). *Powerpropagation: A sparsity inducing weight reparameterisation*. [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [1333722169](https://search.worldcat.org/oclc/1333722169).`{{`[`cite book`](https://en.wikipedia.org/wiki/Template:Cite_book)`}}`: CS1 maint: multiple names: authors list ([link](https://en.wikipedia.org/wiki/Category:CS1_maint:_multiple_names:_authors_list))
51. Hu, Yuzheng; Lin, Licong; Tang, Shange (2019-12-20). "Second-order Information in First-order Optimization Methods". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1912.09926](https://arxiv.org/abs/1912.09926). `{{`[`cite journal`](https://en.wikipedia.org/wiki/Template:Cite_journal)`}}`: Cite journal requires `|journal=` ([help](https://en.wikipedia.org/wiki/Help:CS1_errors#missing_periodical))
52. Reddi, Sashank J.; Kale, Satyen; Kumar, Sanjiv (2018). "On the Convergence of Adam and Beyond". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1904.09237](https://arxiv.org/abs/1904.09237). `{{`[`cite journal`](https://en.wikipedia.org/wiki/Template:Cite_journal)`}}`: Cite journal requires `|journal=` ([help](https://en.wikipedia.org/wiki/Help:CS1_errors#missing_periodical))
53. ["An overview of gradient descent optimization algorithms"](https://www.ruder.io/optimizing-gradient-descent/#amsgrad). 19 January 2016.
54. Tran, Phuong Thi; Phong, Le Trieu (2019). "On the Convergence Proof of AMSGrad and a New Version". *IEEE Access*. **7**: 61706–61716. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1904.03590](https://arxiv.org/abs/1904.03590). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2019IEEEA...761706T](https://ui.adsabs.harvard.edu/abs/2019IEEEA...761706T). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/ACCESS.2019.2916341](https://doi.org/10.1109%2FACCESS.2019.2916341). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [2169-3536](https://search.worldcat.org/issn/2169-3536).
55. Loshchilov, Ilya; Hutter, Frank (4 January 2019). "Decoupled Weight Decay Regularization". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1711.05101](https://arxiv.org/abs/1711.05101). `{{`[`cite journal`](https://en.wikipedia.org/wiki/Template:Cite_journal)`}}`: Cite journal requires `|journal=` ([help](https://en.wikipedia.org/wiki/Help:CS1_errors#missing_periodical))
56. Balles, Lukas; Hennig, Philipp (15 February 2018). ["Dissecting Adam: The Sign, Magnitude and Variance of Stochastic Gradients"](https://openreview.net/forum?id=S1EwLkW0W).
57. ^   ["SignSGD: Compressed Optimisation for Non-Convex Problems"](https://proceedings.mlr.press/v80/bernstein18a.html). 3 July 2018. pp. 560–569.
58. Byrd, R. H.; Hansen, S. L.; Nocedal, J.; Singer, Y. (2016). "A Stochastic Quasi-Newton method for Large-Scale Optimization". *SIAM Journal on Optimization*. **26** (2): 1008–1031. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1401.7020](https://arxiv.org/abs/1401.7020). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/140954362](https://doi.org/10.1137%2F140954362). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [12396034](https://api.semanticscholar.org/CorpusID:12396034).
59. Spall, J. C. (2000). "Adaptive Stochastic Approximation by the Simultaneous Perturbation Method". *IEEE Transactions on Automatic Control*. **45** (10): 1839−1853. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2000ITAC...45.1839S](https://ui.adsabs.harvard.edu/abs/2000ITAC...45.1839S). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/TAC.2000.880982](https://doi.org/10.1109%2FTAC.2000.880982).
60. Spall, J. C. (2009). "Feedback and Weighting Mechanisms for Improving Jacobian Estimates in the Adaptive Simultaneous Perturbation Algorithm". *IEEE Transactions on Automatic Control*. **54** (6): 1216–1229. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2009ITAC...54.1216S](https://ui.adsabs.harvard.edu/abs/2009ITAC...54.1216S). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/TAC.2009.2019793](https://doi.org/10.1109%2FTAC.2009.2019793). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [3564529](https://api.semanticscholar.org/CorpusID:3564529).
61. Bhatnagar, S.; Prasad, H. L.; Prashanth, L. A. (2013). *Stochastic Recursive Algorithms for Optimization: Simultaneous Perturbation Methods*. London: Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4471-4284-3](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4471-4284-3).
62. Ruppert, D. (1985). ["A Newton-Raphson Version of the Multivariate Robbins-Monro Procedure"](https://doi.org/10.1214%2Faos%2F1176346589). *[Annals of Statistics](https://en.wikipedia.org/wiki/Annals_of_Statistics)*. **13** (1): 236–245. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/aos/1176346589](https://doi.org/10.1214%2Faos%2F1176346589).
63. Amari, S. (1998). "Natural gradient works efficiently in learning". *Neural Computation*. **10** (2): 251–276. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1162/089976698300017746](https://doi.org/10.1162%2F089976698300017746). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [207585383](https://api.semanticscholar.org/CorpusID:207585383).
64. Brust, J.J. (2021). "Nonlinear least squares for large-scale machine learning using stochastic Jacobian estimates". *Workshop: Beyond First Order Methods in Machine Learning*. ICML 2021. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2107.05598](https://arxiv.org/abs/2107.05598).
65. Li, Qianxiao; Tai, Cheng; E, Weinan (2019). ["Stochastic Modified Equations and Dynamics of Stochastic Gradient Algorithms I: Mathematical Foundations"](http://jmlr.org/papers/v20/17-526.html). *Journal of Machine Learning Research*. **20** (40): 1–47. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1811.01558](https://arxiv.org/abs/1811.01558). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1533-7928](https://search.worldcat.org/issn/1533-7928).
66. Gess, Benjamin; Kassing, Sebastian; Konarovskyi, Vitalii (14 February 2023). "Stochastic Modified Flows, Mean-Field Limits and Dynamics of Stochastic Gradient Descent". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2302.07125](https://arxiv.org/abs/2302.07125) \[[math.PR](https://arxiv.org/archive/math.PR)\].

## Further reading

- [Bottou, Léon](https://en.wikipedia.org/wiki/L%C3%A9on_Bottou) (2004), ["Stochastic Learning"](http://leon.bottou.org/papers/bottou-mlss-2004), *Advanced Lectures on Machine Learning*, LNAI, vol. 3176, Springer, pp. 146–168, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-23122-6](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-23122-6)
- Buduma, Nikhil; Locascio, Nicholas (2017), ["Beyond Gradient Descent"](https://books.google.com/books?id=80glDwAAQBAJ&pg=PA63), *Fundamentals of Deep Learning : Designing Next-Generation Machine Intelligence Algorithms*, O'Reilly, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9781491925584](https://en.wikipedia.org/wiki/Special:BookSources/9781491925584)
- [LeCun, Yann A.](https://en.wikipedia.org/wiki/Yann_LeCun); Bottou, Léon; Orr, Genevieve B.; [Müller, Klaus-Robert](https://en.wikipedia.org/wiki/Klaus-Robert_M%C3%BCller) (2012), ["Efficient BackProp"](https://books.google.com/books?id=VCKqCAAAQBAJ&pg=PA9), *Neural Networks: Tricks of the Trade*, Springer, pp. 9–48, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-642-35288-1](https://en.wikipedia.org/wiki/Special:BookSources/978-3-642-35288-1)
- Spall, James C. (2003), *Introduction to Stochastic Search and Optimization*, [Wiley](https://en.wikipedia.org/wiki/John_Wiley_%26_Sons), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-33052-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-33052-3)

## External links

- ["Gradient Descent, How Neural Networks Learn"](https://www.youtube.com/watch?v=IHZwWFHWa-w&list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi&index=2). *3Blue1Brown*. October 16, 2017. [Archived](https://ghostarchive.org/varchive/youtube/20211222/IHZwWFHWa-w) from the original on 2021-12-22 – via [YouTube](https://en.wikipedia.org/wiki/YouTube).
- Goh (April 4, 2017). ["Why Momentum Really Works"](https://distill.pub/2017/momentum/). *[Distill](https://en.wikipedia.org/wiki/Distill_(journal) "Distill (journal)")*. **2** (4). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.23915/distill.00006](https://doi.org/10.23915%2Fdistill.00006). Interactive paper explaining momentum.
