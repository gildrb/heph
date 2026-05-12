[[optimization.base]]

> Source: [Learning rate](https://en.wikipedia.org/wiki/Learning_rate)
> License: Wikipedia content is available under CC BY-SA 4.0.

In [machine learning](https://en.wikipedia.org/wiki/Machine_learning) and [statistics](https://en.wikipedia.org/wiki/Statistics), the **learning rate** is a [tuning parameter](https://en.wikipedia.org/wiki/Hyperparameter_(machine_learning) "Hyperparameter (machine learning)") in an [optimization algorithm](https://en.wikipedia.org/wiki/Mathematical_optimization) that determines the step size at each iteration while moving toward a minimum of a [loss function](https://en.wikipedia.org/wiki/Loss_function). Since it influences to what extent newly acquired information overrides old information, it metaphorically represents the speed at which a machine learning model "learns". In the [adaptive control](https://en.wikipedia.org/wiki/Adaptive_control) literature, the learning rate is commonly referred to as **gain**.

In setting a learning rate, there is a trade-off between the rate of convergence and [overshooting](https://en.wikipedia.org/wiki/Overshoot_(signal) "Overshoot (signal)"). While the [descent direction](https://en.wikipedia.org/wiki/Descent_direction) is usually determined from the [[Gradient Descent|gradient]] of the loss function, the learning rate determines how big a step is taken in that direction. Too high a learning rate will make the learning jump over minima, but too low a learning rate will either take too long to converge or get stuck in an undesirable local minimum.

In order to achieve faster convergence, prevent oscillations and getting stuck in undesirable local minima the learning rate is often varied during training either in accordance to a learning rate schedule or by using an adaptive learning rate. The learning rate and its adjustments may also differ per parameter, in which case it is a [diagonal matrix](https://en.wikipedia.org/wiki/Diagonal_matrix) that can be interpreted as an approximation to the [inverse](https://en.wikipedia.org/wiki/Invertible_matrix) of the [[Hessian Matrix]] in [Newton's method](https://en.wikipedia.org/wiki/Newton%27s_method_in_optimization). The learning rate is related to the step length determined by inexact [[Line Search]] in [quasi-Newton methods](https://en.wikipedia.org/wiki/Quasi-Newton_method) and related optimization algorithms.

## Learning rate schedule

Initial rate can be left as system default or can be selected using a range of techniques. A learning rate schedule changes the learning rate during learning and is most often changed between epochs/iterations. This is mainly done with two parameters: **decay** and **momentum**. There are many different learning rate schedules but the most common are **time-based, step-based** and **exponential**.

**Decay** serves to settle the learning in a nice place and avoid oscillations, a situation that may arise when too high a constant learning rate makes the learning jump back and forth over a minimum, and is controlled by a hyperparameter.

**Momentum** is analogous to a ball rolling down a hill; we want the ball to settle at the lowest point of the hill (corresponding to the lowest error). Momentum both speeds up the learning (increasing the learning rate) when the error cost gradient is heading in the same direction for a long time and also avoids local minima by 'rolling over' small bumps. Momentum is controlled by a hyperparameter analogous to a ball's mass which must be chosen manually—too high and the ball will roll over minima which we wish to find, too low and it will not fulfil its purpose. [[Stochastic Gradient Descent|The formula for factoring in the momentum]] is more complex than for decay but is most often built in with deep learning libraries such as [Keras](https://en.wikipedia.org/wiki/Keras).

**Time-based** learning schedules alter the learning rate depending on the learning rate of the previous time iteration. Factoring in the decay the mathematical formula for the learning rate is:

$\eta _{n+1}={\frac {\eta _{0}}{1+dn}}$

where $\eta$ is the learning rate, $\eta _{0}$ is the original learning rate, $d$ is a decay parameter and $n$ is the iteration step.

**Step-based** learning schedules changes the learning rate according to some predefined steps. The decay application formula is here defined as:

$\eta _{n}=\eta _{0}d^{\left\lfloor {\frac {1+n}{r}}\right\rfloor }$

where $\eta _{n}$ is the learning rate at iteration $n$, $\eta _{0}$ is the initial learning rate, $d$ is how much the learning rate should change at each drop (0.5 corresponds to a halving) and $r$ corresponds to the *drop rate*, or how often the rate should be dropped (10 corresponds to a drop every 10 iterations). The *[floor](https://en.wikipedia.org/wiki/Floor_and_ceiling_functions)* function ($\lfloor \dots \rfloor$) here drops the value of its input to 0 for all values smaller than 1.

**Exponential** learning schedules are similar to step-based, but instead of steps, a decreasing exponential function is used. The mathematical formula for factoring in the decay is:

$\eta _{n}=\eta _{0}e^{-dn}$

where $d$ is a decay parameter.

## Adaptive learning rate

The issue with learning rate schedules is that they all depend on hyperparameters that must be manually chosen for each given learning session and may vary greatly depending on the problem at hand or the model used. To combat this, there are many different types of [adaptive](https://en.wikipedia.org/wiki/Adaptive_algorithm) gradient descent algorithms such as [[Stochastic Gradient Descent|Adagrad]], Adadelta, [[Stochastic Gradient Descent|RMSprop]], and [[Stochastic Gradient Descent|Adam]] which are generally built into deep learning libraries such as [Keras](https://en.wikipedia.org/wiki/Keras).

## See also

- [Hyperparameter (machine learning)](https://en.wikipedia.org/wiki/Hyperparameter_(machine_learning) "Hyperparameter (machine learning)")
- [Hyperparameter optimization](https://en.wikipedia.org/wiki/Hyperparameter_optimization)
- [[Stochastic Gradient Descent]]
- [Variable metric methods](https://en.wikipedia.org/wiki/Variable_metric_methods)
- [Overfitting](https://en.wikipedia.org/wiki/Overfitting)
- [Backpropagation](https://en.wikipedia.org/wiki/Backpropagation)
- [AutoML](https://en.wikipedia.org/wiki/AutoML)
- [Model selection](https://en.wikipedia.org/wiki/Model_selection)
- [Self-tuning](https://en.wikipedia.org/wiki/Self-tuning)

## References

1.  Murphy, Kevin P. (2012). [Machine Learning: A Probabilistic Perspective](https://books.google.com/books?id=NZP6AQAAQBAJ&pg=PA247). Cambridge: MIT Press. p. 247. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-262-01802-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-262-01802-9).
2.  Delyon, Bernard (2000). "Stochastic Approximation with Decreasing Gain: Convergence and Asymptotic Theory". *Unpublished Lecture Notes*. Université de Rennes. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.29.4428](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.29.4428).
3.  Buduma, Nikhil; Locascio, Nicholas (2017). *Fundamentals of Deep Learning : Designing Next-Generation Machine Intelligence Algorithms*. O'Reilly. p. 21. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4919-2558-4](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4919-2558-4).
4.  ^   Patterson, Josh; Gibson, Adam (2017). "Understanding Learning Rates". *Deep Learning : A Practitioner's Approach*. O'Reilly. pp. 258–263. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4919-1425-0](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4919-1425-0).
5.  Ruder, Sebastian (2017). "An Overview of Gradient Descent Optimization Algorithms". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1609.04747](https://arxiv.org/abs/1609.04747) \[[cs.LG](https://arxiv.org/archive/cs.LG)\].
6.  Nesterov, Y. (2004). [Introductory Lectures on Convex Optimization: A Basic Course](https://books.google.com/books?id=2-ElBQAAQBAJ&pg=PA25). Boston: Kluwer. p. 25. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [1-4020-7553-7](https://en.wikipedia.org/wiki/Special:BookSources/1-4020-7553-7).
7.  Dixon, L. C. W. (1972). "The Choice of Step Length, a Crucial Factor in the Performance of Variable Metric Algorithms". *Numerical Methods for Non-linear Optimization*. London: Academic Press. pp. 149–170. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-12-455650-7](https://en.wikipedia.org/wiki/Special:BookSources/0-12-455650-7).
8.  Smith, Leslie N. (4 April 2017). "Cyclical Learning Rates for Training Neural Networks". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1506.01186](https://arxiv.org/abs/1506.01186) \[[cs.CV](https://arxiv.org/archive/cs.CV)\].
9.  Murphy, Kevin (2021). [Probabilistic Machine Learning: An Introduction](https://probml.github.io/pml-book/book1.html). MIT Press. Retrieved 10 April 2021.
10. Brownlee, Jason (22 January 2019). ["How to Configure the Learning Rate When Training Deep Learning Neural Networks"](https://machinelearningmastery.com/learning-rate-for-deep-learning-neural-networks/). *Machine Learning Mastery*. Retrieved 4 January 2021.

## Further reading

- Géron, Aurélien (2017). ["Gradient Descent"](https://books.google.com/books?id=khpYDgAAQBAJ&pg=PA113). *Hands-On Machine Learning with Scikit-Learn and TensorFlow*. O'Reilly. pp. 113–124. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4919-6229-9](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4919-6229-9).
- Plagianakos, V. P.; Magoulas, G. D.; Vrahatis, M. N. (2001). ["Learning Rate Adaptation in Stochastic Gradient Descent"](https://books.google.com/books?id=YW4KBwAAQBAJ&pg=PA433). *Advances in Convex Analysis and Global Optimization*. Kluwer. pp. 433–444. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-7923-6942-4](https://en.wikipedia.org/wiki/Special:BookSources/0-7923-6942-4).

## External links

- de Freitas, Nando (February 12, 2015). ["Optimization"](https://www.youtube.com/watch?v=0qUAb94CpOw&list=PLE6Wd9FR--EfW8dtjAuPoTuPcqmOV53Fu&index=9). *Deep Learning Lecture 6*. University of Oxford – via [YouTube](https://en.wikipedia.org/wiki/YouTube).
