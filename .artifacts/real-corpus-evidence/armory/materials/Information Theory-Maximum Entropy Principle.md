[[information-theory.base]]

> Source: [Principle of maximum entropy](https://en.wikipedia.org/wiki/Principle_of_maximum_entropy)
> License: Wikipedia content is available under CC BY-SA 4.0.

The **principle of maximum entropy** states that, among all probability distributions consistent with a given set of constraints (such as normalization or specified expectation values), the distribution that maximizes [Shannon entropy](https://en.wikipedia.org/wiki/Entropy_(information_theory) "Entropy (information theory)") should be selected. This yields the least committal distribution compatible with the known constraints, introducing no structure beyond what is logically implied by the available information.

The justification is that entropy measures the expected information content (or log-surprise) of outcomes relative to a specified reference measure. Maximizing entropy ensures that no additional structure is imposed beyond the stated constraints. Any lower-entropy alternative would encode extra regularity not required by those constraints and would therefore amount to introducing unsupported information.

It is important that entropy be defined relative to a specified measure or prior. In discrete cases, Shannon entropy is defined relative to the counting measure (or an explicitly specified prior weighting). In continuous cases, [differential entropy](https://en.wikipedia.org/wiki/Differential_entropy) depends on the choice of coordinates and is not invariant under reparameterization. For this reason, the principled continuous formulation maximizes relative entropy (equivalently, minimizes [[Kullback-Leibler Divergence|Kullback–Leibler divergence]]) with respect to a specified reference measure or prior density m(x), typically by maximizing

$-\int p(x)\,\log {\frac {p(x)}{m(x)}}\,dx$

subject to the given constraints. This formulation is invariant under change of variables and makes explicit the role of the underlying prior measure.

## History

The principle was first expounded by [E. T. Jaynes](https://en.wikipedia.org/wiki/E._T._Jaynes) in two papers in 1957, where he emphasized a natural correspondence between [statistical mechanics](https://en.wikipedia.org/wiki/Statistical_mechanics) and [information theory](https://en.wikipedia.org/wiki/Information_theory). In particular, Jaynes argued that the Gibbsian method of statistical mechanics is sound by also arguing that the [[Entropy]] of statistical mechanics and the [information entropy](https://en.wikipedia.org/wiki/Information_entropy) of [information theory](https://en.wikipedia.org/wiki/Information_theory) are the same concept. Consequently, [statistical mechanics](https://en.wikipedia.org/wiki/Statistical_mechanics) should be considered a particular application of a general tool of logical [inference](https://en.wikipedia.org/wiki/Inference) and information theory.

## Overview

In most practical cases, the stated prior data or testable information is given by a set of [conserved quantities](https://en.wikipedia.org/wiki/Conserved_quantities) (average values of some moment functions), associated with the [probability distribution](https://en.wikipedia.org/wiki/Probability_distribution) in question. This is the way the maximum entropy principle is most often used in [statistical thermodynamics](https://en.wikipedia.org/wiki/Statistical_thermodynamics). Another possibility is to prescribe some [symmetries](https://en.wikipedia.org/wiki/Symmetries) of the probability distribution. The equivalence between [conserved quantities](https://en.wikipedia.org/wiki/Conserved_quantities) and corresponding [symmetry groups](https://en.wikipedia.org/wiki/Symmetry_group) implies a similar equivalence for these two ways of specifying the testable information in the maximum entropy method.

The maximum entropy principle is also needed to guarantee the uniqueness and consistency of probability assignments obtained by different methods, [statistical mechanics](https://en.wikipedia.org/wiki/Statistical_mechanics) and [logical inference](https://en.wikipedia.org/wiki/Logical_inference) in particular.

The maximum entropy principle makes explicit our freedom in using different forms of [prior data](https://en.wikipedia.org/wiki/Prior_probability). As a special case, a uniform [prior probability](https://en.wikipedia.org/wiki/Prior_probability) density (Laplace's [principle of indifference](https://en.wikipedia.org/wiki/Principle_of_indifference), sometimes called the principle of insufficient reason), may be adopted. Thus, the maximum entropy principle is not merely an alternative way to view the usual methods of inference of classical statistics, but represents a significant conceptual generalization of those methods.

However these statements do not imply that thermodynamical systems need not be shown to be [ergodic](https://en.wikipedia.org/wiki/Ergodic) to justify treatment as a [statistical ensemble](https://en.wikipedia.org/wiki/Statistical_ensemble).

In ordinary language, the principle of maximum entropy can be said to express a claim of epistemic modesty, or of maximum ignorance. The selected distribution is the one that makes the least claim to being informed beyond the stated prior data, that is to say the one that admits the most ignorance beyond the stated prior data.

## Testable information

The principle of maximum entropy is useful explicitly only when applied to *testable information*. Testable information is a statement about a probability distribution whose truth or falsity is well-defined. For example, the statements

the [expectation](https://en.wikipedia.org/wiki/Expected_value) of the variable $x$ is 2.87

and 

$$
p_{2}+p_{3}>0.6
$$

(where $p_{2}$ and $p_{3}$ are probabilities of events) are statements of testable information.

Given testable information, the maximum entropy procedure consists of seeking the [probability distribution](https://en.wikipedia.org/wiki/Probability_distribution) which maximizes [information entropy](https://en.wikipedia.org/wiki/Information_entropy), subject to the constraints of the information. This constrained optimization problem is typically solved using the method of [Lagrange multipliers](https://en.wikipedia.org/wiki/Lagrange_multiplier).

Entropy maximization with no testable information respects the universal "constraint" that the sum of the probabilities is one. Under this constraint, the maximum entropy discrete probability distribution is the [uniform distribution](https://en.wikipedia.org/wiki/Uniform_distribution_(discrete)),

$$
p_{i}={\frac {1}{n}}\ {\rm {for\ all}}\ i\in \{\,1,\dots ,n\,\}.
$$

## Applications

The principle of maximum entropy is commonly applied in two ways to inferential problems:

### Prior probabilities

The principle of maximum entropy is often used to obtain [prior probability distributions](https://en.wikipedia.org/wiki/Prior_probability) for [Bayesian inference](https://en.wikipedia.org/wiki/Bayesian_inference). Jaynes was a strong advocate of this approach, claiming the maximum entropy distribution represented the least informative distribution. A large amount of literature is now dedicated to the elicitation of maximum entropy priors and links with [channel coding](https://en.wikipedia.org/wiki/Channel_coding).

### Posterior probabilities

### Maximum entropy models

Alternatively, the principle is often invoked for model specification: in this case the observed data itself is assumed to be the testable information. Such models are widely used in [natural language processing](https://en.wikipedia.org/wiki/Natural_language_processing). An example of such a model is [logistic regression](https://en.wikipedia.org/wiki/Logistic_regression), which corresponds to the [maximum entropy classifier](https://en.wikipedia.org/wiki/Maximum_entropy_classifier) for independent observations.

The maximum entropy principle has also been applied in economics and resource allocation. For example, the [Boltzmann fair division](https://en.wikipedia.org/wiki/Boltzmann_fair_division) model uses the maximum entropy (Boltzmann) distribution to allocate resources or income among individuals, providing a probabilistic approach to distributive justice.

### Probability density estimation

One of the main applications of the maximum entropy principle is in discrete and continuous [density estimation](https://en.wikipedia.org/wiki/Density_estimation). Similar to [support vector machine](https://en.wikipedia.org/wiki/Support_vector_machine) estimators, the maximum entropy principle may require the solution to a [quadratic programming](https://en.wikipedia.org/wiki/Quadratic_programming) problem, and thus provide a sparse mixture model as the optimal density estimator. One important advantage of the method is its ability to incorporate prior information in the density estimation.

## General solution for the maximum entropy distribution with linear constraints

### Discrete case

We have some testable information *I* about a quantity *x* taking values in {*x<sub>1</sub>*, *x<sub>2</sub>*,..., *x<sub>n</sub>*}. We assume this information has the form of *m* constraints on the expectations of the functions *f<sub>k</sub>*; that is, we require our probability distribution to satisfy the moment inequality/equality constraints:

$$
\sum _{i=1}^{n}\Pr(x_{i})f_{k}(x_{i})\geq F_{k}\qquad k=1,\ldots ,m.
$$

where the $F_{k}$ are observables. We also require the probability density to sum to one, which may be viewed as a primitive constraint on the identity function and an observable equal to 1 giving the constraint

$$
\sum _{i=1}^{n}\Pr(x_{i})=1.
$$

The probability distribution with maximum information entropy subject to these inequality/equality constraints is of the form:

$$
\Pr(x_{i})={\frac {1}{Z(\lambda _{1},\ldots ,\lambda _{m})}}\exp \left[\lambda _{1}f_{1}(x_{i})+\cdots +\lambda _{m}f_{m}(x_{i})\right],
$$

for some $\lambda _{1},\ldots ,\lambda _{m}$. It is sometimes called the [Gibbs distribution](https://en.wikipedia.org/wiki/Gibbs_distribution). The normalization constant is determined by:

$$
Z(\lambda _{1},\ldots ,\lambda _{m})=\sum _{i=1}^{n}\exp \left[\lambda _{1}f_{1}(x_{i})+\cdots +\lambda _{m}f_{m}(x_{i})\right],
$$

and is conventionally called the [partition function](https://en.wikipedia.org/wiki/Partition_function_(mathematics) "Partition function (mathematics)"). (The [Pitman–Koopman theorem](https://en.wikipedia.org/wiki/Pitman%E2%80%93Koopman_theorem) states that the necessary and sufficient condition for a [sampling distribution](https://en.wikipedia.org/wiki/Sampling_distribution) to admit [sufficient statistics](https://en.wikipedia.org/wiki/Sufficiency_(statistics)) of bounded dimension is that it have the general form of a maximum entropy distribution.)

The *λ*<sub>*k*</sub> parameters are Lagrange multipliers. In the case of equality constraints their values are determined from the solution of the nonlinear equations

$$
F_{k}={\frac {\partial }{\partial \lambda _{k}}}\log Z(\lambda _{1},\ldots ,\lambda _{m}).
$$

In the case of inequality constraints, the Lagrange multipliers are determined from the solution of a [[Convex Optimization]] program with linear constraints. In both cases, there is no [closed form solution](https://en.wikipedia.org/wiki/Closed_form_solution), and the computation of the Lagrange multipliers usually requires [numerical methods](https://en.wikipedia.org/wiki/Numerical_analysis).

### Continuous case

For [continuous distributions](https://en.wikipedia.org/wiki/Continuous_distribution), the Shannon entropy cannot be used, as it is only defined for discrete probability spaces. Instead [Edwin Jaynes](https://en.wikipedia.org/wiki/E._T._Jaynes) (1963, 1968, 2003) gave the following formula, which is closely related to the [relative entropy](https://en.wikipedia.org/wiki/Relative_entropy) (see also [differential entropy](https://en.wikipedia.org/wiki/Differential_entropy)).

$$
H_{c}=-\int p(x)\log {\frac {p(x)}{q(x)}}\,dx
$$

where *q*(*x*), which Jaynes called the "[invariant measure](https://en.wikipedia.org/wiki/Invariant_measure)", is proportional to the [limiting density of discrete points](https://en.wikipedia.org/wiki/Limiting_density_of_discrete_points). For now, we shall assume that *q* is known; we will discuss it further after the solution equations are given.

A closely related quantity, the relative entropy, is usually defined as the [[Kullback-Leibler Divergence|Kullback–Leibler divergence]] of *p* from *q* (although it is sometimes, confusingly, defined as the negative of this). The inference principle of minimizing this, due to Kullback, is known as the [[Kullback-Leibler Divergence|Principle of Minimum Discrimination Information]].

We have some testable information *I* about a quantity *x* which takes values in some [interval](https://en.wikipedia.org/wiki/Interval_(mathematics) "Interval (mathematics)") of the [real numbers](https://en.wikipedia.org/wiki/Real_numbers) (all integrals below are over this interval). We assume this information has the form of *m* constraints on the expectations of the functions *f<sub>k</sub>*, i.e. we require our probability density function to satisfy the inequality (or purely equality) moment constraints:

$$
\int p(x)f_{k}(x)\,dx\geq F_{k}\qquad k=1,\dotsc ,m.
$$

where the $F_{k}$ are observables. We also require the probability density to integrate to one, which may be viewed as a primitive constraint on the identity function and an observable equal to 1 giving the constraint

$$
\int p(x)\,dx=1.
$$

The probability density function with maximum *H<sub>c</sub>* subject to these constraints is:

$$
p(x)={\frac {q(x)\exp \left[\lambda _{1}f_{1}(x)+\dotsb +\lambda _{m}f_{m}(x)\right]}{Z(\lambda _{1},\dotsc ,\lambda _{m})}}
$$

with the [partition function](https://en.wikipedia.org/wiki/Partition_function_(mathematics) "Partition function (mathematics)") determined by

$$
Z(\lambda _{1},\dotsc ,\lambda _{m})=\int q(x)\exp \left[\lambda _{1}f_{1}(x)+\dotsb +\lambda _{m}f_{m}(x)\right]\,dx.
$$

As in the discrete case, in the case where all moment constraints are equalities, the values of the $\lambda _{k}$ parameters are determined by the system of nonlinear equations:

$$
F_{k}={\frac {\partial }{\partial \lambda _{k}}}\log Z(\lambda _{1},\dotsc ,\lambda _{m}).
$$

In the case with inequality moment constraints the Lagrange multipliers are determined from the solution of a [[Convex Optimization]] program.

The invariant measure function *q*(*x*) can be best understood by supposing that *x* is known to take values only in the [bounded interval](https://en.wikipedia.org/wiki/Bounded_interval) (*a*, *b*), and that no other information is given. Then the maximum entropy probability density function is

$$
p(x)=A\cdot q(x),\qquad a<x<b
$$

where *A* is a normalization constant. The invariant measure function is actually the prior density function encoding 'lack of relevant information'. It cannot be determined by the principle of maximum entropy, and must be determined by some other logical method, such as the [principle of transformation groups](https://en.wikipedia.org/wiki/Principle_of_transformation_groups) or [marginalization theory](https://en.wikipedia.org/wiki/Marginalization_(probability)).

### Examples

For several examples of maximum entropy distributions, see the article on [maximum entropy probability distributions](https://en.wikipedia.org/wiki/Maximum_entropy_probability_distribution).

## Justifications for the principle of maximum entropy

Proponents of the principle of maximum entropy justify its use in assigning probabilities in several ways, including the following two arguments. These arguments take the use of [Bayesian probability](https://en.wikipedia.org/wiki/Bayesian_probability) as given, and are thus subject to the same postulates.

### Information entropy as a measure of 'uninformativeness'

Consider a **discrete probability distribution** among $m$ mutually exclusive [propositions](https://en.wikipedia.org/wiki/Proposition). The most informative distribution would occur when one of the propositions was known to be true. In that case, the information entropy would be equal to zero. The least informative distribution would occur when there is no reason to favor any one of the propositions over the others. In that case, the only reasonable probability distribution would be uniform, and then the information entropy would be equal to its maximum possible value, $\log m$. The information entropy can therefore be seen as a numerical measure which describes how uninformative a particular probability distribution is, ranging from zero (completely informative) to $\log m$ (completely uninformative).

By choosing to use the distribution with the maximum entropy allowed by our information, the argument goes, we are choosing the most uninformative distribution possible. To choose a distribution with lower entropy would be to assume information we do not possess. Thus the maximum entropy distribution is the only reasonable distribution. The [dependence of the solution](http://projecteuclid.org/euclid.ba/1340370710) on the dominating measure represented by $m(x)$ is however a source of criticisms of the approach since this dominating measure is in fact arbitrary.

### The Wallis derivation

Suppose an individual wishes to make a probability assignment among $m$ [mutually exclusive](https://en.wikipedia.org/wiki/Mutually_exclusive) propositions. They have some testable information, but are not sure how to go about including this information in their probability assessment. They therefore conceive of the following random experiment. They will distribute $N$ quanta of probability (each worth $1/N$) at random among the $m$ possibilities. (One might imagine that they will throw $N$ balls into $m$ buckets while blindfolded. In order to be as fair as possible, each throw is to be independent of any other, and every bucket is to be the same size.) Once the experiment is done, they will check if the probability assignment thus obtained is consistent with their information. (For this step to be successful, the information must be a constraint given by an [open set](https://en.wikipedia.org/wiki/Open_set) in the space of probability measures). If it is inconsistent, they will reject it and try again. If it is consistent, their assessment will be

$$
p_{i}={\frac {n_{i}}{N}}
$$

where $p_{i}$ is the probability of the $i$<sup>th</sup> proposition, while *n<sub>i</sub>* is the number of quanta that were assigned to the $i$<sup>th</sup> proposition (i.e. the number of balls that ended up in bucket $i$).

Now, in order to reduce the 'graininess' of the probability assignment, it will be necessary to use quite a large number of quanta of probability. Rather than actually carry out, and possibly have to repeat, the rather long random experiment, the protagonist decides to simply calculate and use the most probable result. The probability of any particular result is the [multinomial distribution](https://en.wikipedia.org/wiki/Multinomial_distribution),

$$
Pr(\mathbf {p} )=W\cdot m^{-N}
$$

where

$$
W={\frac {N!}{n_{1}!\,n_{2}!\,\dotsb \,n_{m}!}}
$$

is sometimes known as the multiplicity of the outcome.

The most probable result is the one which maximizes the multiplicity $W$. Rather than maximizing $W$ directly, the protagonist could equivalently maximize any monotonic increasing function of $W$. They decide to maximize

$$
{\begin{aligned}{\frac {1}{N}}\log W&={\frac {1}{N}}\log {\frac {N!}{n_{1}!\,n_{2}!\,\dotsb \,n_{m}!}}\\[6pt]&={\frac {1}{N}}\log {\frac {N!}{(Np_{1})!\,(Np_{2})!\,\dotsb \,(Np_{m})!}}\\[6pt]&={\frac {1}{N}}\left(\log N!-\sum _{i=1}^{m}\log((Np_{i})!)\right).\end{aligned}}
$$

At this point, in order to simplify the expression, the protagonist takes the limit as $N\to \infty$, i.e. as the probability levels go from grainy discrete values to smooth continuous values. Using [Stirling's approximation](https://en.wikipedia.org/wiki/Stirling%27s_approximation), they find

$$
{\begin{aligned}\lim _{N\to \infty }\left({\frac {1}{N}}\log W\right)&={\frac {1}{N}}\left(N\log N-\sum _{i=1}^{m}Np_{i}\log(Np_{i})\right)\\[6pt]&=\log N-\sum _{i=1}^{m}p_{i}\log(Np_{i})\\[6pt]&=\log N-\log N\sum _{i=1}^{m}p_{i}-\sum _{i=1}^{m}p_{i}\log p_{i}\\[6pt]&=\left(1-\sum _{i=1}^{m}p_{i}\right)\log N-\sum _{i=1}^{m}p_{i}\log p_{i}\\[6pt]&=-\sum _{i=1}^{m}p_{i}\log p_{i}\\[6pt]&=H(\mathbf {p} ).\end{aligned}}
$$

All that remains for the protagonist to do is to maximize entropy under the constraints of their testable information. They have found that the maximum entropy distribution is the most probable of all "fair" random distributions, in the limit as the probability levels go from discrete to continuous.

### Compatibility with Bayes' theorem

Jaynes stated Bayes' theorem was a way to calculate a probability, while maximum entropy was a way to assign a prior probability distribution.

It is however, possible in concept to solve for a posterior distribution directly from a stated prior distribution using the [[Cross-Entropy|principle of minimum cross-entropy]] (or the Principle of Maximum Entropy being a special case of using a [uniform distribution](https://en.wikipedia.org/wiki/Uniform_distribution_(discrete)) as the given prior), independently of any Bayesian considerations by treating the problem formally as a constrained optimisation problem, the Entropy functional being the objective function. For the case of given average values as testable information (averaged over the sought after probability distribution), the sought after distribution is formally the [Gibbs (or Boltzmann) distribution](https://en.wikipedia.org/wiki/Gibbs_measure) the parameters of which must be solved for in order to achieve minimum cross entropy and satisfy the given testable information.

## Relevance to physics

The principle of maximum entropy bears a relation to a key assumption of [kinetic theory of gases](https://en.wikipedia.org/wiki/Kinetic_theory_of_gases) known as [molecular chaos](https://en.wikipedia.org/wiki/Molecular_chaos) or *Stosszahlansatz*. This asserts that the distribution function characterizing particles entering a collision can be factorized. Though this statement can be understood as a strictly physical hypothesis, it can also be interpreted as a heuristic hypothesis regarding the most probable configuration of particles before colliding.

## See also

- [Akaike information criterion](https://en.wikipedia.org/wiki/Akaike_information_criterion)
- [Dissipation](https://en.wikipedia.org/wiki/Dissipation)
- [Info-metrics](https://en.wikipedia.org/wiki/Info-metrics)
- [Maximum entropy classifier](https://en.wikipedia.org/wiki/Maximum_entropy_classifier)
- [Maximum entropy probability distribution](https://en.wikipedia.org/wiki/Maximum_entropy_probability_distribution)
- [Maximum entropy spectral estimation](https://en.wikipedia.org/wiki/Maximum_entropy_spectral_estimation)
- [Maximum entropy thermodynamics](https://en.wikipedia.org/wiki/Maximum_entropy_thermodynamics)
- [Principle of maximum caliber](https://en.wikipedia.org/wiki/Principle_of_maximum_caliber)
- [Thermodynamic equilibrium](https://en.wikipedia.org/wiki/Thermodynamic_equilibrium)
- [Molecular chaos](https://en.wikipedia.org/wiki/Molecular_chaos)
- [Boltzmann fair division](https://en.wikipedia.org/wiki/Boltzmann_fair_division)

## Notes

1.  [Jaynes, E. T.](https://en.wikipedia.org/wiki/Edwin_Thompson_Jaynes) (1957). ["Information Theory and Statistical Mechanics"](http://bayes.wustl.edu/etj/articles/theory.1.pdf) (PDF). *Physical Review*. Series II. **106** (4): 620–630. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1957PhRv..106..620J](https://ui.adsabs.harvard.edu/abs/1957PhRv..106..620J). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1103/PhysRev.106.620](https://doi.org/10.1103%2FPhysRev.106.620). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0087305](https://mathscinet.ams.org/mathscinet-getitem?mr=0087305).
2.  [Jaynes, E. T.](https://en.wikipedia.org/wiki/Edwin_Thompson_Jaynes) (1957). ["Information Theory and Statistical Mechanics II"](http://bayes.wustl.edu/etj/articles/theory.2.pdf) (PDF). *Physical Review*. Series II. **108** (2): 171–190. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1957PhRv..108..171J](https://ui.adsabs.harvard.edu/abs/1957PhRv..108..171J). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1103/PhysRev.108.171](https://doi.org/10.1103%2FPhysRev.108.171). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0096414](https://mathscinet.ams.org/mathscinet-getitem?mr=0096414).
3.  Sivia, Devinderjit; Skilling, John (2006-06-02). [Data Analysis: A Bayesian Tutorial](https://books.google.com/books?id=Kxx8CwAAQBAJ&dq=data+analysis+a+bayesian+tutorial&pg=PR9). OUP Oxford. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-19-154670-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-19-154670-9).
4.  [Jaynes, E. T.](https://en.wikipedia.org/wiki/Edwin_Thompson_Jaynes) (1968). ["Prior Probabilities"](http://bayes.wustl.edu/etj/articles/brandeis.pdf) (PDF). *IEEE Transactions on Systems Science and Cybernetics*. **4** (3): 227–241. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/TSSC.1968.300117](https://doi.org/10.1109%2FTSSC.1968.300117).
5.  Clarke, B. (2006). "Information optimality and Bayesian modelling". *[Journal of Econometrics](https://en.wikipedia.org/wiki/Journal_of_Econometrics)*. **138** (2): 405–429. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.jeconom.2006.05.003](https://doi.org/10.1016%2Fj.jeconom.2006.05.003).
6.  Soofi, E.S. (2000). "Principal Information Theoretic Approaches". *[Journal of the American Statistical Association](https://en.wikipedia.org/wiki/Journal_of_the_American_Statistical_Association)*. **95** (452): 1349–1353. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2669786](https://doi.org/10.2307%2F2669786). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2669786](https://www.jstor.org/stable/2669786). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [1825292](https://mathscinet.ams.org/mathscinet-getitem?mr=1825292).
7.  Bousquet, N. (2008). "Eliciting vague but proper maximal entropy priors in Bayesian experiments". *Statistical Papers*. **51** (3): 613–628. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s00362-008-0149-9](https://doi.org/10.1007%2Fs00362-008-0149-9). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [119657859](https://api.semanticscholar.org/CorpusID:119657859).
8.  Palmieri, Francesco A. N.; Ciuonzo, Domenico (2013-04-01). "Objective priors from maximum entropy in data classification". *Information Fusion*. **14** (2): 186–198. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.387.4515](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.387.4515). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.inffus.2012.01.012](https://doi.org/10.1016%2Fj.inffus.2012.01.012).
9.  [Skyrms, B](https://en.wikipedia.org/wiki/Brian_Skyrms) (1987). "Updating, supposing and MAXENT". *Theory and Decision*. **22** (3): 225–46. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/BF00134086](https://doi.org/10.1007%2FBF00134086). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [121847242](https://api.semanticscholar.org/CorpusID:121847242).
10. Park, J.-W., Kim, J. U., Ghim, C.-M., & Kim, C. U. (2022). The Boltzmann Fair Division for Distributive Justice. *Scientific Reports*, 12(1), 16179. [https://doi.org/10.1038/s41598-022-19792-3](https://doi.org/10.1038/s41598-022-19792-3) Park, J.-W., & Kim, C. U. (2021). Getting to a Feasible Income Equality. *PLOS ONE*, 16(3), e0249204. [https://doi.org/10.1371/journal.pone.0249204](https://doi.org/10.1371/journal.pone.0249204) Park, J.-W., Kim, C. U., & Isard, W. (2012). Permit Allocation in Emissions Trading Using the Boltzmann Distribution. *Physica A*, 391, 4883–4890. [https://doi.org/10.1016/j.physa.2012.05.006](https://doi.org/10.1016/j.physa.2012.05.006)
11. ^    Botev, Z. I.; Kroese, D. P. (2008). "Non-asymptotic Bandwidth Selection for Density Estimation of Discrete Data". *Methodology and Computing in Applied Probability*. **10** (3): 435. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s11009-007-9057-z](https://doi.org/10.1007%2Fs11009-007-9057-z). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [122047337](https://api.semanticscholar.org/CorpusID:122047337).
12. ^   Botev, Z. I.; Kroese, D. P. (2011). ["The Generalized Cross Entropy Method, with Applications to Probability Density Estimation"](http://espace.library.uq.edu.au/view/UQ:200564/UQ200564_preprint.pdf) (PDF). *Methodology and Computing in Applied Probability*. **13** (1): 1–27. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s11009-009-9133-7](https://doi.org/10.1007%2Fs11009-009-9133-7). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [18155189](https://api.semanticscholar.org/CorpusID:18155189).
13. Kesavan, H. K.; Kapur, J. N. (1990). "Maximum Entropy and Minimum Cross-Entropy Principles". In Fougère, P. F. (ed.). [Maximum Entropy and Bayesian Methods](https://archive.org/details/maximumentropyba00jayn_552). pp. [419](https://archive.org/details/maximumentropyba00jayn_552/page/n418)–432. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-94-009-0683-9_29](https://doi.org/10.1007%2F978-94-009-0683-9_29). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-94-010-6792-8](https://en.wikipedia.org/wiki/Special:BookSources/978-94-010-6792-8).
14. Jaynes, E.T. (1968). ["Prior Probabilities"](https://ieeexplore.ieee.org/document/4082152). *IEEE Trans. Syst. Sci. Cybern*. **4**: 227–241. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/TSSC.1968.300117](https://doi.org/10.1109%2FTSSC.1968.300117).
15. Druilhet, Pierre; Marin, Jean-Michel (2007). ["Invariant {HPD} credible sets and {MAP} estimators"](https://projecteuclid.org/euclid.ba/1340370710). *Bayesian Anal*. **2**: 681–691. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/07-BA227](https://doi.org/10.1214%2F07-BA227).
16. Jaynes, E. T. (2003) *Probability Theory: The Logic of Science*, Cambridge University Press, p. 351-355. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0521592710](https://en.wikipedia.org/wiki/Special:BookSources/978-0521592710)
17. Jaynes, E. T. (1988) ["The Relation of Bayesian and Maximum Entropy Methods"](http://bayes.wustl.edu/etj/articles/relationship.pdf), in *Maximum-Entropy and Bayesian Methods in Science and Engineering (Vol. 1)*, Kluwer Academic Publishers, p. 25-29.
18. Chliamovitch, G.; Malaspinas, O.; Chopard, B. (2017). ["Kinetic theory beyond the Stosszahlansatz"](https://doi.org/10.3390%2Fe19080381). *Entropy*. **19** (8): 381. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2017Entrp..19..381C](https://ui.adsabs.harvard.edu/abs/2017Entrp..19..381C). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3390/e19080381](https://doi.org/10.3390%2Fe19080381).

## References

- Bajkova, A. T. (1992). "The generalization of maximum entropy method for reconstruction of complex functions". *Astronomical and Astrophysical Transactions*. **1** (4): 313–320. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1992A&AT....1..313B](https://ui.adsabs.harvard.edu/abs/1992A&AT....1..313B). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/10556799208230532](https://doi.org/10.1080%2F10556799208230532).
- Fornalski, K.W.; Parzych, G.; Pylak, M.; Satuła, D.; Dobrzyński, L. (2010). ["Application of Bayesian reasoning and the Maximum Entropy Method to some reconstruction problems"](http://przyrbwn.icm.edu.pl/APP/PDF/117/a117z602.pdf) (PDF). *Acta Physica Polonica A*. **117** (6): 892–899. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2010AcPPA.117..892F](https://ui.adsabs.harvard.edu/abs/2010AcPPA.117..892F). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.12693/APhysPolA.117.892](https://doi.org/10.12693%2FAPhysPolA.117.892).
- Giffin, A. and Caticha, A., 2007, [Updating Probabilities with Data and Moments](https://arxiv.org/abs/0708.1593)
- Guiasu, S.; Shenitzer, A. (1985). "The principle of maximum entropy". *The Mathematical Intelligencer*. **7** (1): 42–48. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/bf03023004](https://doi.org/10.1007%2Fbf03023004). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [53059968](https://api.semanticscholar.org/CorpusID:53059968).
- Harremoës, P.; Topsøe (2001). ["Maximum entropy fundamentals"](https://doi.org/10.3390%2Fe3030191). *Entropy*. **3** (3): 191–226. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2001Entrp...3..191H](https://ui.adsabs.harvard.edu/abs/2001Entrp...3..191H). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3390/e3030191](https://doi.org/10.3390%2Fe3030191).
- [Jaynes, E. T.](https://en.wikipedia.org/wiki/Edwin_Thompson_Jaynes) (1963). ["Information Theory and Statistical Mechanics"](http://bayes.wustl.edu/etj/node1.html). In Ford, K. (ed.). *Statistical Physics*. New York: Benjamin. p. 181.
- Jaynes, E. T., 1986 (new version online 1996), "[Monkeys, kangaroos and N](http://bayes.wustl.edu/etj/articles/cmonkeys.pdf)", in *Maximum-Entropy and Bayesian Methods in Applied Statistics*, J. H. Justice (ed.), Cambridge University Press, Cambridge, p. 26.
- Kapur, J. N.; and [Kesavan, H. K.](https://en.wikipedia.org/wiki/H._K._Kesavan), 1992, *Entropy Optimization Principles with Applications*, Boston: Academic Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-12-397670-7](https://en.wikipedia.org/wiki/Special:BookSources/0-12-397670-7)
- Kitamura, Y., 2006, [Empirical Likelihood Methods in Econometrics: Theory and Practice](http://cowles.yale.edu/sites/default/files/files/pub/d15/d1569.pdf), Cowles Foundation Discussion Papers 1569, Cowles Foundation, Yale University.
- Lazar, N (2003). "Bayesian empirical likelihood". *Biometrika*. **90** (2): 319–326. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1093/biomet/90.2.319](https://doi.org/10.1093%2Fbiomet%2F90.2.319).
- Owen, A. B., 2001, *Empirical Likelihood*, Chapman and Hall/CRC. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [1-58-488071-6](https://en.wikipedia.org/wiki/Special:BookSources/1-58-488071-6).
- Schennach, S. M. (2005). "Bayesian exponentially tilted empirical likelihood". *Biometrika*. **92** (1): 31–46. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1093/biomet/92.1.31](https://doi.org/10.1093%2Fbiomet%2F92.1.31).
- Uffink, Jos (1995). ["Can the Maximum Entropy Principle be explained as a consistency requirement?"](https://web.archive.org/web/20060603144738/http://www.phys.uu.nl/~wwwgrnsl/jos/mepabst/mep.pdf) (PDF). *Studies in History and Philosophy of Modern Physics*. **26B** (3): 223–261. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1995SHPMP..26..223U](https://ui.adsabs.harvard.edu/abs/1995SHPMP..26..223U). [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.27.6392](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.27.6392). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/1355-2198(95)00015-1](https://doi.org/10.1016%2F1355-2198%2895%2900015-1). [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[1874/2649](https://hdl.handle.net/1874%2F2649). Archived from [the original](http://www.phys.uu.nl/~wwwgrnsl/jos/mepabst/mep.pdf) (PDF) on 2006-06-03.

## Further reading

- Boyd, Stephen; Lieven Vandenberghe (2004). [Convex Optimization](https://web.stanford.edu/~boyd/cvxbook/bv_cvxbook.pdf#page=376) (PDF). [Cambridge University Press](https://en.wikipedia.org/wiki/Cambridge_University_Press). p. 362. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-83378-7](https://en.wikipedia.org/wiki/Special:BookSources/0-521-83378-7). Retrieved 2008-08-24.
- Ratnaparkhi A. (1997) ["A simple introduction to maximum entropy models for natural language processing"](http://repository.upenn.edu/cgi/viewcontent.cgi?article=1083&context=ircs_reports) Technical Report 97-08, Institute for Research in Cognitive Science, University of Pennsylvania. An easy-to-read introduction to maximum entropy methods in the context of natural language processing.
- Tang, A.; Jackson, D.; Hobbs, J.; Chen, W.; Smith, J. L.; Patel, H.; Prieto, A.; Petrusca, D.; Grivich, M. I.; Sher, A.; Hottowy, P.; Dabrowski, W.; Litke, A. M.; Beggs, J. M. (2008). ["A Maximum Entropy Model Applied to Spatial and Temporal Correlations from Cortical Networks in Vitro"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6670549). *Journal of Neuroscience*. **28** (2): 505–518. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1523/JNEUROSCI.3359-07.2008](https://doi.org/10.1523%2FJNEUROSCI.3359-07.2008). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [6670549](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6670549). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [18184793](https://pubmed.ncbi.nlm.nih.gov/18184793). Open access article containing pointers to various papers and software implementations of Maximum Entropy Model on the net.
