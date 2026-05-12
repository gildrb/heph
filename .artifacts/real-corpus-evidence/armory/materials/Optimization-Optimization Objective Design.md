[[optimization.base]]

> Source: [Loss function](https://en.wikipedia.org/wiki/Loss_function)
> License: Wikipedia content is available under CC BY-SA 4.0.

In [mathematical optimization](https://en.wikipedia.org/wiki/Mathematical_optimization) and [decision theory](https://en.wikipedia.org/wiki/Decision_theory), a **loss function** or **cost function** (sometimes also called an error function) is a function that maps an [event](https://en.wikipedia.org/wiki/Event_(probability_theory) "Event (probability theory)") or values of one or more variables onto a [real number](https://en.wikipedia.org/wiki/Real_number) intuitively representing some "cost" associated with the event. An [optimization problem](https://en.wikipedia.org/wiki/Optimization_problem) seeks to minimize a loss function. An **objective function** is either a loss function or its opposite (in specific domains, variously called a [reward function](https://en.wikipedia.org/wiki/Reward_function), a [profit function](https://en.wikipedia.org/wiki/Profit_function), a [utility function](https://en.wikipedia.org/wiki/Utility_function), a [fitness function](https://en.wikipedia.org/wiki/Fitness_function), etc.), in which case it is to be maximized. The loss function could include terms from several levels of the hierarchy.

In statistics, typically a loss function is used for [parameter estimation](https://en.wikipedia.org/wiki/Parameter_estimation), and the event in question is some function of the difference between estimated and true values for an instance of data. The concept, as old as [Laplace](https://en.wikipedia.org/wiki/Pierre-Simon_Laplace), was reintroduced in statistics by [Abraham Wald](https://en.wikipedia.org/wiki/Abraham_Wald) in the middle of the 20th century. In the context of [economics](https://en.wikipedia.org/wiki/Economics), for example, this is usually [economic cost](https://en.wikipedia.org/wiki/Economic_cost) or [regret](https://en.wikipedia.org/wiki/Regret_(decision_theory) "Regret (decision theory)"). In [classification](https://en.wikipedia.org/wiki/Statistical_classification), it is the penalty for an incorrect classification of an example. In [actuarial science](https://en.wikipedia.org/wiki/Actuarial_science), it is used in an insurance context to model benefits paid over premiums, particularly since the works of [Harald Cramér](https://en.wikipedia.org/wiki/Harald_Cram%C3%A9r) in the 1920s. In [optimal control](https://en.wikipedia.org/wiki/Optimal_control), the loss is the penalty for failing to achieve a desired value. In [financial risk management](https://en.wikipedia.org/wiki/Financial_risk_management), the function is mapped to a monetary loss.

![[media/436ede84d202c00ecdfcf12d9b9142984401eabe.png]]
Comparison of common loss functions ([MAE](https://en.wikipedia.org/wiki/Mean_absolute_error), SMAE, [Huber loss](https://en.wikipedia.org/wiki/Huber_loss), and log-cosh loss) used for regression

## Examples

### Regret

[Leonard J. Savage](https://en.wikipedia.org/wiki/Leonard_J._Savage) argued that using non-Bayesian methods such as [minimax](https://en.wikipedia.org/wiki/Minimax), the loss function should be based on the idea of *[regret](https://en.wikipedia.org/wiki/Regret_(decision_theory) "Regret (decision theory)")*, i.e., the loss associated with a decision should be the difference between the consequences of the best decision that could have been made under circumstances will be known and the decision that was in fact taken before they were known.

### Quadratic loss function

The use of a [quadratic](https://en.wikipedia.org/wiki/Quadratic_function) loss function is common, for example when using [least squares](https://en.wikipedia.org/wiki/Least_squares) techniques. It is often more mathematically tractable than other loss functions because of the properties of [variances](https://en.wikipedia.org/wiki/Variance), as well as being symmetric: an error above the target causes the same loss as the same magnitude of error below the target. If the target is *t*, then a quadratic loss function is

$\lambda (x)=C(t-x)^{2}\;$

for some constant *C*; the value of the constant makes no difference to a decision, and can be ignored by setting it equal to 1. This is also known as the **squared error loss** (**SEL**).

Many common [statistics](https://en.wikipedia.org/wiki/Statistic), including [t-tests](https://en.wikipedia.org/wiki/T-test), [regression](https://en.wikipedia.org/wiki/Regression_analysis) models, [design of experiments](https://en.wikipedia.org/wiki/Design_of_experiments), and much else, use [least squares](https://en.wikipedia.org/wiki/Least_squares) methods applied using [linear regression](https://en.wikipedia.org/wiki/Linear_regression) theory, which is based on the quadratic loss function.

The quadratic loss function is also used in [linear-quadratic optimal control problems](https://en.wikipedia.org/wiki/Linear-quadratic_regulator). In these problems, even in the absence of uncertainty, it may not be possible to achieve the desired values of all target variables. Often loss is expressed as a [quadratic form](https://en.wikipedia.org/wiki/Quadratic_form) in the deviations of the variables of interest from their desired values; this approach is [tractable](https://en.wikipedia.org/wiki/Closed-form_expression) because it results in linear [first-order conditions](https://en.wikipedia.org/wiki/First-order_condition). In the context of [stochastic control](https://en.wikipedia.org/wiki/Stochastic_control), the expected value of the quadratic form is used. The quadratic loss assigns more importance to outliers than to the true data due to its square nature, so alternatives like the [Huber](https://en.wikipedia.org/wiki/Huber_loss), log-cosh and SMAE<sup>\[*[further explanation needed](https://en.wikipedia.org/wiki/Wikipedia:Please_clarify)*\]</sup> losses are used when the data has many large outliers.

![[media/d94b1f3000881f478833b93918962db5242c249d.png]]
Effect of using different loss functions, when the data has outliers

### 0-1 loss function

In [statistics](https://en.wikipedia.org/wiki/Statistics) and [decision theory](https://en.wikipedia.org/wiki/Decision_theory), a frequently used loss function is the *0-1 loss function*

$L({\hat {y}},y)={\begin{cases}0&{\text{if }}y={\hat {y}}\\1&{\text{if }}y\neq {\hat {y}}\end{cases}}$

In [information theory](https://en.wikipedia.org/wiki/Information_theory), this loss function is known as [[Rate Distortion Theory|Hamming distortion]].

## Constructing loss and objective functions

In many applications, objective functions, including loss functions as a particular case, are determined by the problem formulation. In other situations, the decision maker’s preference must be elicited and represented by a scalar-valued function (called also [utility](https://en.wikipedia.org/wiki/Utility) function) in a form suitable for optimization — the problem that [Ragnar Frisch](https://en.wikipedia.org/wiki/Ragnar_Frisch) has highlighted in his [Nobel Prize](https://en.wikipedia.org/wiki/Nobel_Prize) lecture. The existing methods for constructing objective functions are collected in the proceedings of two dedicated conferences. In particular, [Andranik Tangian](https://en.wikipedia.org/wiki/Andranik_Tangian) showed that the most usable objective functions — quadratic and additive — are determined by a few [indifference](https://en.wikipedia.org/wiki/Principle_of_indifference) points. He used this property in the models for constructing these objective functions from either [ordinal](https://en.wikipedia.org/wiki/Ordinal_utility) or [cardinal](https://en.wikipedia.org/wiki/Cardinal_utility) data that were elicited through computer-assisted interviews with decision makers. Among other things, he constructed objective functions to optimally distribute budgets for 16 Westfalian universities and the European subsidies for equalizing unemployment rates among 271 German regions.

## Expected loss

In some contexts, the value of the loss function itself is a random quantity because it depends on the outcome of a random variable *X*.

### Statistics

Both [frequentist](https://en.wikipedia.org/wiki/Frequentist_probability) and [Bayesian](https://en.wikipedia.org/wiki/Bayesian_probability) statistical theory involve making a decision based on the [expected value](https://en.wikipedia.org/wiki/Expected_value) of the loss function; however, this quantity is defined differently under the two paradigms.

#### Frequentist expected loss

We first define the expected loss in the frequentist context. It is obtained by taking the expected value with respect to the [probability distribution](https://en.wikipedia.org/wiki/Probability_distribution), *P*<sub>*θ*</sub>, of the observed data, *X*. This is also referred to as the **risk function** of the decision rule *δ* and the parameter *θ*. Here the decision rule depends on the outcome of *X*. The risk function is given by:

$R(\theta ,\delta )=\operatorname {E} _{\theta }L{\big (}\theta ,\delta (X){\big )}=\int _{X}L{\big (}\theta ,\delta (x){\big )}\,\mathrm {d} P_{\theta }(x).$

Here, *θ* is a fixed but possibly unknown state of nature, *X* is a vector of observations stochastically drawn from a [population](https://en.wikipedia.org/wiki/Statistical_population), $\operatorname {E} _{\theta }$ is the expectation over all population values of *X*, *dP*<sub>*θ*</sub> is a [probability measure](https://en.wikipedia.org/wiki/Probability_measure) over the event space of *X* (parametrized by *θ*) and the integral is evaluated over the entire [support](https://en.wikipedia.org/wiki/Support_(measure_theory) "Support (measure theory)") of *X*.

#### Bayes Risk

In a Bayesian approach, the expectation is calculated using the [prior distribution](https://en.wikipedia.org/wiki/Prior_distribution) π<sup>\*</sup> of the parameter *θ*:

$\rho (\pi ^{*},a)=\int _{\Theta }\int _{\mathbf {X}}L(\theta ,a({\mathbf {x}}))\,\mathrm {d} P({\mathbf {x}}\vert \theta )\,\mathrm {d} \pi ^{*}(\theta )=\int _{\mathbf {X}}\int _{\Theta }L(\theta ,a({\mathbf {x}}))\,\mathrm {d} \pi ^{*}(\theta \vert {\mathbf {x}})\,\mathrm {d} M({\mathbf {x}})$

where m(x) is known as the *predictive likelihood* wherein θ has been "integrated out," π<sup>\*</sup> (θ \| x) is the posterior distribution, and the order of integration has been changed. One then should choose the action *a<sup>\*</sup>* which minimises this expected loss, which is referred to as *Bayes Risk*. In the latter equation, the integrand inside dx is known as the *Posterior Risk*, and minimising it with respect to decision *a* also minimizes the overall Bayes Risk. This optimal decision, *a<sup>\*</sup>* is known as the *Bayes (decision) Rule* - it minimises the average loss over all possible states of nature θ, over all possible (probability-weighted) data outcomes. One advantage of the Bayesian approach is to that one need only choose the optimal action under the actual observed data to obtain a uniformly optimal one, whereas choosing the actual frequentist optimal decision rule as a function of all possible observations, is a much more difficult problem. Of equal importance though, the Bayes Rule reflects consideration of loss outcomes under different states of nature, θ.

#### Examples in statistics

- For a scalar parameter *θ*, a decision function whose output ${\hat {\theta }}$ is an estimate of *θ*, and a quadratic loss function ([squared error loss](https://en.wikipedia.org/wiki/Squared_error_loss)) 

$$
L(\theta ,{\hat {\theta }})=(\theta -{\hat {\theta }})^{2},
$$

 the risk function becomes the [mean squared error](https://en.wikipedia.org/wiki/Mean_squared_error) of the estimate, 

$$
R(\theta ,{\hat {\theta }})=\operatorname {E} _{\theta }\left[(\theta -{\hat {\theta }})^{2}\right].
$$

An [Estimator](https://en.wikipedia.org/wiki/Estimator) found by minimizing the [Mean squared error](https://en.wikipedia.org/wiki/Mean_squared_error) estimates the [Posterior distribution](https://en.wikipedia.org/wiki/Posterior_distribution)'s mean.
- In [density estimation](https://en.wikipedia.org/wiki/Density_estimation), the unknown parameter is [[Probability Density Function|probability density]] itself. The loss function is typically chosen to be a [norm](https://en.wikipedia.org/wiki/Norm_(mathematics) "Norm (mathematics)") in an appropriate [function space](https://en.wikipedia.org/wiki/Function_space). For example, for [L2 norm](https://en.wikipedia.org/wiki/L2_norm), 

$$
L(f,{\hat {f}})=\|f-{\hat {f}}\|_{2}^{2}\,,
$$

 the risk function becomes the [mean integrated squared error](https://en.wikipedia.org/wiki/Mean_integrated_squared_error) 

$$
R(f,{\hat {f}})=\operatorname {E} \left(\|f-{\hat {f}}\|^{2}\right).\,
$$

### Economic choice under uncertainty

In economics, decision-making under uncertainty is often modelled using the [von Neumann–Morgenstern utility function](https://en.wikipedia.org/wiki/Von_Neumann%E2%80%93Morgenstern_utility_function) of the uncertain variable of interest, such as end-of-period wealth. Since the value of this variable is uncertain, so is the value of the utility function; it is the expected value of utility that is maximized.

## Decision rules

A [decision rule](https://en.wikipedia.org/wiki/Decision_rule) makes a choice using an optimality criterion. Some commonly used criteria are:

- **[Minimax](https://en.wikipedia.org/wiki/Minimax)**: Choose the decision rule with the lowest worst loss — that is, minimize the worst-case (maximum possible) loss: 

$$
{\underset {\delta }{\operatorname {arg\,min} }}\ \max _{\theta \in \Theta }\ R(\theta ,\delta ).
$$

- **[Invariance](https://en.wikipedia.org/wiki/Invariant_estimator)**: Choose the decision rule which satisfies an invariance requirement.
- Choose the decision rule with the lowest average loss (i.e. minimize the [expected value](https://en.wikipedia.org/wiki/Expected_value) of the loss function): 

$$
{\underset {\delta }{\operatorname {arg\,min} }}\operatorname {E} _{\theta \in \Theta }[R(\theta ,\delta )]={\underset {\delta }{\operatorname {arg\,min} }}\ \int _{\theta \in \Theta }R(\theta ,\delta )\,p(\theta )\,d\theta .
$$

## Selecting a loss function

Sound statistical practice requires selecting an estimator consistent with the actual acceptable variation experienced in the context of a particular applied problem. Thus, in the applied use of loss functions, selecting which statistical method to use to model an applied problem depends on knowing the losses that will be experienced from being wrong under the problem's particular circumstances.

A common example involves estimating "[location](https://en.wikipedia.org/wiki/Location_parameter)". Under typical statistical assumptions, the [mean](https://en.wikipedia.org/wiki/Mean) or average is the statistic for estimating location that minimizes the expected loss experienced under the [squared-error](https://en.wikipedia.org/wiki/Least_squares) loss function, while the [median](https://en.wikipedia.org/wiki/Median) is the estimator that minimizes expected loss experienced under the absolute-difference loss function. Still different estimators would be optimal under other, less common circumstances.

In economics, when an agent is [risk neutral](https://en.wikipedia.org/wiki/Risk_neutral), the objective function is simply expressed as the expected value of a monetary quantity, such as profit, income, or end-of-period wealth. For [risk-averse](https://en.wikipedia.org/wiki/Risk_aversion) or [risk-loving](https://en.wikipedia.org/wiki/Risk-loving) agents, loss is measured as the negative of a [utility function](https://en.wikipedia.org/wiki/Utility), and the objective function to be optimized is the expected value of utility.

Other measures of cost are possible, for example [mortality](https://en.wikipedia.org/wiki/Mortality_rate) or [morbidity](https://en.wikipedia.org/wiki/Morbidity) in the field of [public health](https://en.wikipedia.org/wiki/Public_health) or [safety engineering](https://en.wikipedia.org/wiki/Safety_engineering).

For most [optimization algorithms](https://en.wikipedia.org/wiki/Optimization_algorithm), it is desirable to have a loss function that is globally [continuous](https://en.wikipedia.org/wiki/Continuous_function) and [differentiable](https://en.wikipedia.org/wiki/Differentiable_function).

Two very commonly used loss functions are the [squared loss](https://en.wikipedia.org/wiki/Mean_squared_error), $L(a)=a^{2}$, and the [absolute loss](https://en.wikipedia.org/wiki/Absolute_deviation), $L(a)=|a|$. However the absolute loss has the disadvantage that it is not differentiable at $a=0$. The squared loss has the disadvantage that it has the tendency to be dominated by [outliers](https://en.wikipedia.org/wiki/Outlier)—when summing over a set of $a$'s (as in $\sum _{i=1}^{n}L(a_{i})$), the final sum tends to be the result of a few particularly large *a*-values, rather than an expression of the average *a*-value.

The choice of a loss function is not arbitrary. It is very restrictive and sometimes the loss function may be characterized by its desirable properties. Among the choice principles are, for example, the requirement of completeness of the class of symmetric statistics in the case of [i.i.d.](https://en.wikipedia.org/wiki/I.i.d.) observations, the principle of complete information, and some others.

[W. Edwards Deming](https://en.wikipedia.org/wiki/W._Edwards_Deming) and [Nassim Nicholas Taleb](https://en.wikipedia.org/wiki/Nassim_Nicholas_Taleb) argue that empirical reality, not nice mathematical properties, should be the sole basis for selecting loss functions, and real losses often are not mathematically nice and are not differentiable, continuous, symmetric, etc. For example, a person who arrives before a plane gate closure can still make the plane, but a person who arrives after cannot, a discontinuity and asymmetry which makes arriving slightly late much more costly than arriving slightly early. In drug dosing, the cost of too little drug may be lack of efficacy, while the cost of too much may be tolerable toxicity, another example of asymmetry. Traffic, pipes, beams, ecologies, climates, etc. may tolerate increased load or stress with little noticeable change up to a point, then become backed up or break catastrophically. These situations, Deming and Taleb argue, are common in real-life problems, perhaps more common than classical smooth, continuous, symmetric, differentials cases.

## See also

- [Bayesian regret](https://en.wikipedia.org/wiki/Bayesian_regret)
- [Loss functions for classification](https://en.wikipedia.org/wiki/Loss_functions_for_classification)
- [Discounted maximum loss](https://en.wikipedia.org/wiki/Discounted_maximum_loss)
- [Hinge loss](https://en.wikipedia.org/wiki/Hinge_loss)
- [Scoring rule](https://en.wikipedia.org/wiki/Scoring_rule)
- [Statistical risk](https://en.wikipedia.org/wiki/Statistical_risk)

## References

1.  ^   Hastie, Trevor; [Tibshirani, Robert](https://en.wikipedia.org/wiki/Robert_Tibshirani); [Friedman, Jerome H.](https://en.wikipedia.org/wiki/Jerome_H._Friedman) (2001). [The Elements of Statistical Learning](https://web.stanford.edu/~hastie/ElemStatLearn/). Springer. p. 18. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-95284-5](https://en.wikipedia.org/wiki/Special:BookSources/0-387-95284-5).
2.  Wald, A. (1950). [Statistical Decision Functions](https://psycnet.apa.org/record/1951-01400-000). Wiley – via APA Psycnet.
3.  Cramér, H. (1930). *On the mathematical theory of risk*. Centraltryckeriet.
4.  Frisch, Ragnar (1969). "From utopian theory to practical applications: the case of econometrics". [The Nobel Prize–Prize Lecture](https://www.nobelprize.org/prizes/economic-sciences/1969/frisch/lecture/). Retrieved 15 February 2021.
5.  Tangian, Andranik; Gruber, Josef (1997). *Constructing Scalar-Valued Objective Functions. Proceedings of the Third International Conference on Econometric Decision Models: Constructing Scalar-Valued Objective Functions, University of Hagen, held in Katholische Akademie Schwerte September 5–8, 1995*. Lecture Notes in Economics and Mathematical Systems. Vol. 453. Berlin: Springer. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-3-642-48773-6](https://doi.org/10.1007%2F978-3-642-48773-6). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-63061-6](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-63061-6).
6.  Tangian, Andranik; Gruber, Josef (2002). *Constructing and Applying Objective Functions. Proceedings of the Fourth International Conference on Econometric Decision Models Constructing and Applying Objective Functions, University of Hagen, held in Haus Nordhelle, August, 28 — 31, 2000*. Lecture Notes in Economics and Mathematical Systems. Vol. 510. Berlin: Springer. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-3-642-56038-5](https://doi.org/10.1007%2F978-3-642-56038-5). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-42669-1](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-42669-1).
7.  Tangian, Andranik (2002). "Constructing a quasi-concave quadratic objective function from interviewing a decision maker". *European Journal of Operational Research*. **141** (3): 608–640. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/S0377-2217(01)00185-0](https://doi.org/10.1016%2FS0377-2217%2801%2900185-0). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [39623350](https://api.semanticscholar.org/CorpusID:39623350).
8.  Tangian, Andranik (2004). "A model for ordinally constructing additive objective functions". *European Journal of Operational Research*. **159** (2): 476–512. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/S0377-2217(03)00413-2](https://doi.org/10.1016%2FS0377-2217%2803%2900413-2). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [31019036](https://api.semanticscholar.org/CorpusID:31019036).
9.  Tangian, Andranik (2004). "Redistribution of university budgets with respect to the status quo". *European Journal of Operational Research*. **157** (2): 409–428. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/S0377-2217(03)00271-6](https://doi.org/10.1016%2FS0377-2217%2803%2900271-6).
10. Tangian, Andranik (2008). ["Multi-criteria optimization of regional employment policy: A simulation analysis for Germany"](https://onlinelibrary.wiley.com/doi/10.1111/j.1467-940X.2008.00144.x). *Review of Urban and Regional Development*. **20** (2): 103–122. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1111/j.1467-940X.2008.00144.x](https://doi.org/10.1111%2Fj.1467-940X.2008.00144.x).
11. Nikulin, M.S. (2001) \[1994\], ["Risk of a statistical procedure"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society)
12. [Berger, James O.](https://en.wikipedia.org/wiki/James_Berger_(statistician)) (1985). [Statistical decision theory and Bayesian Analysis](https://books.google.com/books?id=oY_x7dE15_AC) (2nd ed.). New York: Springer-Verlag. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1985sdtb.book.....B](https://ui.adsabs.harvard.edu/abs/1985sdtb.book.....B). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-96098-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-96098-2). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0804611](https://mathscinet.ams.org/mathscinet-getitem?mr=0804611).
13. [DeGroot, Morris](https://en.wikipedia.org/wiki/Morris_H._DeGroot) (2004) \[1970\]. *Optimal Statistical Decisions*. Wiley Classics Library. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-68029-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-68029-1). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [2288194](https://mathscinet.ams.org/mathscinet-getitem?mr=2288194).
14. Robert, Christian P. (2007). *The Bayesian Choice*. Springer Texts in Statistics (2nd ed.). New York: Springer. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/0-387-71599-1](https://doi.org/10.1007%2F0-387-71599-1). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-95231-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-95231-4). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1835885](https://mathscinet.ams.org/mathscinet-getitem?mr=1835885).
15. Pfanzagl, J. (1994). *Parametric Statistical Theory*. Berlin: Walter de Gruyter. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-11-013863-4](https://en.wikipedia.org/wiki/Special:BookSources/978-3-11-013863-4).
16. Detailed information on mathematical principles of the loss function choice is given in Chapter 2 of the book Klebanov, B.; Rachev, Svetlozat T.; Fabozzi, Frank J. (2009). *Robust and Non-Robust Models in Statistics*. New York: Nova Scientific Publishers, Inc. (and references there).
17. Deming, W. Edwards (2000). *Out of the Crisis*. The MIT Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780262541152](https://en.wikipedia.org/wiki/Special:BookSources/9780262541152).

## Further reading

- Aretz, Kevin; Bartram, Söhnke M.; Pope, Peter F. (April–June 2011). ["Asymmetric Loss Functions and the Rationality of Expected Stock Returns"](https://mpra.ub.uni-muenchen.de/47343/1/MPRA_paper_47343.pdf) (PDF). *International Journal of Forecasting*. **27** (2): 413–437. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.ijforecast.2009.10.008](https://doi.org/10.1016%2Fj.ijforecast.2009.10.008). [SSRN](https://en.wikipedia.org/wiki/SSRN_(identifier)) [889323](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=889323).
- [Berger, James O.](https://en.wikipedia.org/wiki/James_Berger_(statistician)) (1985). *Statistical decision theory and Bayesian Analysis* (2nd ed.). New York: Springer-Verlag. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1985sdtb.book.....B](https://ui.adsabs.harvard.edu/abs/1985sdtb.book.....B). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-96098-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-96098-2). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0804611](https://mathscinet.ams.org/mathscinet-getitem?mr=0804611).

- Cecchetti, S. (2000). ["Making monetary policy: Objectives and rules"](https://www.researchgate.net/publication/5216117). *Oxford Review of Economic Policy*. **16** (4): 43–59. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1093/oxrep/16.4.43](https://doi.org/10.1093%2Foxrep%2F16.4.43).

- Horowitz, Ann R. (1987). "Loss functions and public policy". *Journal of Macroeconomics*. **9** (4): 489–504. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/0164-0704(87)90016-4](https://doi.org/10.1016%2F0164-0704%2887%2990016-4).

- Waud, Roger N. (1976). "Asymmetric Policymaker Utility Functions and Optimal Policy under Uncertainty". *Econometrica*. **44** (1): 53–66. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/1911380](https://doi.org/10.2307%2F1911380). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [1911380](https://www.jstor.org/stable/1911380).
