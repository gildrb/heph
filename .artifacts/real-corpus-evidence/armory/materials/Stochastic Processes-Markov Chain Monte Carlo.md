[[stochastic-processes.base]]

> Source: [[Markov Chain Monte Carlo]]
> License: Wikipedia content is available under CC BY-SA 4.0.

In [statistics](https://en.wikipedia.org/wiki/Statistics), **Markov chain Monte Carlo** (**MCMC**) is a class of [algorithms](https://en.wikipedia.org/wiki/Algorithm) used to draw samples from a [probability distribution](https://en.wikipedia.org/wiki/Probability_distribution). Given a probability distribution, one can construct a [[Markov Chain]] whose elements' distribution approximates it – that is, the Markov chain's [equilibrium distribution](https://en.wikipedia.org/wiki/Discrete-time_Markov_chain#Stationary_distributions) matches the target distribution. The more steps that are included, the more closely the distribution of the sample matches the actual desired distribution.

Markov chain Monte Carlo methods are used to study probability distributions that are too complex or too high [dimensional](https://en.wikipedia.org/wiki/N-dimensional_space) to study with analytic techniques alone. Various algorithms exist for constructing such Markov chains, including the [[Metropolis Hastings Algorithm|Metropolis–Hastings algorithm]].

## General explanation

![[media/460a0c89bac795309433bf1478d28b80bc66e464.png]]
Convergence of the [[Metropolis Hastings Algorithm|Metropolis–Hastings algorithm]]. Markov chain Monte Carlo attempts to approximate the blue distribution with the orange distribution.

Markov chain Monte Carlo methods create samples from a continuous [random variable](https://en.wikipedia.org/wiki/Random_variable), with [probability density](https://en.wikipedia.org/wiki/Probability_density) proportional to a known function. These samples can be used to evaluate an integral over that variable, as its [expected value](https://en.wikipedia.org/wiki/Expected_value) or [variance](https://en.wikipedia.org/wiki/Variance).

Practically, an [ensemble](https://en.wikipedia.org/wiki/Statistical_ensemble) of chains is generally developed, starting from a set of points arbitrarily chosen and sufficiently distant from each other. These chains are [stochastic processes](https://en.wikipedia.org/wiki/Stochastic_processes) of "walkers" which move around randomly according to an algorithm that looks for places with a reasonably high contribution to the integral to move into next, assigning them higher probabilities.

Random walk Monte Carlo methods are a kind of random [simulation](https://en.wikipedia.org/wiki/Computer_simulation) or [[Monte Carlo Method]]. However, whereas the random samples of the integrand used in a conventional [Monte Carlo integration](https://en.wikipedia.org/wiki/Monte_Carlo_integration) are [statistically independent](https://en.wikipedia.org/wiki/Statistically_independent), those used in MCMC are [autocorrelated](https://en.wikipedia.org/wiki/Autocorrelation). Correlations of samples introduces the need to use the [Markov chain central limit theorem](https://en.wikipedia.org/wiki/Markov_chain_central_limit_theorem) when estimating the error of mean values.

These algorithms create [Markov chains](https://en.wikipedia.org/wiki/Markov_chains) such that they have an [[Markov Chain|equilibrium distribution]] which is proportional to the function given.

## History

The development of MCMC methods is deeply rooted in the early exploration of [[Monte Carlo Method|Monte Carlo]] (MC) techniques in the mid-20th century, particularly in physics. These developments were marked by the [[Metropolis Hastings Algorithm|Metropolis algorithm]] proposed by [Nicholas Metropolis](https://en.wikipedia.org/wiki/Nicholas_Metropolis), [Arianna W. Rosenbluth](https://en.wikipedia.org/wiki/Arianna_W._Rosenbluth), [Marshall Rosenbluth](https://en.wikipedia.org/wiki/Marshall_Rosenbluth), [Augusta H. Teller](https://en.wikipedia.org/wiki/Augusta_H._Teller), and [Edward Teller](https://en.wikipedia.org/wiki/Edward_Teller) in 1953, which was designed to tackle high-dimensional integration problems using early computers. Then in 1970, [W. K. Hastings](https://en.wikipedia.org/wiki/W._K._Hastings) generalized this algorithm and inadvertently introduced the component-wise updating idea, later known as [[Gibbs Sampling]]. Simultaneously, the theoretical foundations for Gibbs sampling were being developed, such as the [Hammersley–Clifford theorem](https://en.wikipedia.org/wiki/Hammersley%E2%80%93Clifford_theorem) from [Julian Besag](https://en.wikipedia.org/wiki/Julian_Besag)'s 1974 paper. Although the seeds of MCMC were sown earlier, including the formal naming of Gibbs sampling in image processing by [Stuart Geman](https://en.wikipedia.org/wiki/Stuart_Geman) and [Donald Geman](https://en.wikipedia.org/wiki/Donald_Geman) (1984) and the [data augmentation](https://en.wikipedia.org/wiki/Data_augmentation) method by Martin A. Tanner and [Wing Hung Wong](https://en.wikipedia.org/wiki/Wing_Hung_Wong) (1987), its "revolution" in mainstream statistics largely followed demonstrations of the universality and ease of implementation of sampling methods (especially Gibbs sampling) for complex statistical (particularly [Bayesian](https://en.wikipedia.org/wiki/Bayesian_inference)) problems, spurred by increasing computational power and software like [BUGS](https://en.wikipedia.org/wiki/WinBUGS). This transformation was accompanied by significant theoretical advancements, such as [Luke Tierney](https://en.wikipedia.org/wiki/Luke_Tierney)'s (1994) rigorous treatment of MCMC convergence, and [Jun S. Liu](https://en.wikipedia.org/wiki/Jun_S._Liu), Wong, and [Augustine Kong](https://en.wikipedia.org/wiki/Augustine_Kong)'s (1994, 1995) analysis of Gibbs sampler structure. Subsequent developments further expanded the MCMC toolkit, including [particle filters](https://en.wikipedia.org/wiki/Particle_filter) ([Sequential Monte Carlo](https://en.wikipedia.org/wiki/Sequential_Monte_Carlo)) for sequential problems, [Perfect sampling](https://en.wikipedia.org/wiki/Coupling_from_the_past) aiming for exact simulation ([Jim Propp](https://en.wikipedia.org/wiki/Jim_Propp) and David B. Wilson, 1996), [RJMCMC](https://en.wikipedia.org/wiki/Reversible-jump_Markov_chain_Monte_Carlo) ([Peter J. Green](https://en.wikipedia.org/wiki/Peter_Green_(statistician) "Peter Green (statistician)"), 1995) for handling variable-dimension models, and deeper investigations into convergence diagnostics and the [[Central Limit Theorem]]. Overall, the evolution of MCMC represents a paradigm shift in statistical computation, enabling the analysis of numerous previously intractable complex models and continually expanding the scope and impact of statistics.

## Mathematical setting

Suppose *(X<sub>n</sub>)* is a [[Markov Chain]] in the general state space ${\mathcal {X}}$ with specific properties. We are interested in the limiting behavior of the partial sums:

$S_{n}(h)={\dfrac {1}{n}}\sum _{i=1}^{n}h(X_{i})$

as *n* goes to infinity. Particularly, we hope to establish the [[Law of Large Numbers]] and the [[Central Limit Theorem]] for MCMC. In the following, we state some definitions and theorems necessary for the important convergence results. In short, we need the existence of [invariant measure](https://en.wikipedia.org/wiki/Invariant_measure) and Harris recurrent to establish the Law of Large Numbers of MCMC (Ergodic Theorem). And we need aperiodicity, irreducibility and extra conditions such as reversibility to ensure the Central Limit Theorem holds in MCMC.

### Irreducibility and aperiodicity

Recall that in the discrete setting, a [[Markov Chain]] is said to be *irreducible* if it is possible to reach any state from any other state in a finite number of steps with positive probability. However, in the continuous setting, point-to-point transitions have zero probability. In this case, **φ-irreducibility** generalizes [irreducibility](https://en.wikipedia.org/wiki/Irreducibility) by using a reference measure φ on the measurable space $({\mathcal {X}},{\mathcal {B}}({\mathcal {X}}))$.

Definition (φ-irreducibility)

Given a measure $\varphi$ defined on $({\mathcal {X}},{\mathcal {B}}({\mathcal {X}}))$, the Markov chain $(X_{n})$ with transition kernel $K(x,y)$ is **φ-irreducible** if, for every $A\in {\mathcal {B}}({\mathcal {X}})$ with $\varphi (A)>0$, there exists $n$ such that $K^{n}(x,A)>0$ for all $x\in {\mathcal {X}}$ (Equivalently, $P_{x}(\tau _{A}<\infty )>0$, here $\tau _{A}=\inf\{n\geq 1;X_{n}\in A\}$ is the first $n$ for which the chain enters the set $A$).

This is a more general definition for [irreducibility](https://en.wikipedia.org/wiki/Irreducibility) of a [[Markov Chain]] in non-discrete state space. In the discrete case, an irreducible Markov chain is said to be *aperiodic* if it has period 1. Formally, the period of a state $\omega \in {\mathcal {X}}$ is defined as:

$d(\omega ):=\mathrm {gcd} \{m\geq 1\,;\,K^{m}(\omega ,\omega )>0\}$

For the general (non-discrete) case, we define aperiodicity in terms of small sets:

Definition (Cycle length and small sets)

A **φ-irreducible** Markov chain $(X_{n})$ has a *cycle of length d* if there exists a small set $C$, an associated integer $M$, and a probability distribution $\nu _{M}$ such that *d* is the [greatest common divisor](https://en.wikipedia.org/wiki/Greatest_common_divisor) of:

$\{m\geq 1\,;\,\exists \,\delta _{m}>0{\text{ such that }}C{\text{ is small for }}\nu _{m}\geq \delta _{m}\nu _{M}\}.$

A set $C$ is called **small** if there exists $m\in \mathbb {N} ^{*}$ and a nonzero measure $\nu _{m}$ such that:

$K^{m}(x,A)\geq \nu _{m}(A),\quad \forall x\in C,\,\forall A\in {\mathcal {B}}({\mathcal {X}}).$

### Harris recurrent

Definition (Harris recurrence)

A set $A$ is **Harris recurrent** if $P_{x}(\eta _{A}=\infty )=1$ for all $x\in A$, where $\eta _{A}=\sum _{n=1}^{\infty }\mathbb {I} _{A}(X_{n})$ is the number of visits of the chain $(X_{n})$ to the set $A$.

The chain $(X_{n})$ is said to be **Harris recurrent** if there exists a measure $\psi$ such that the chain is $\psi$-irreducible and every measurable set $A$ with $\psi (A)>0$ is Harris recurrent.

A useful criterion for verifying Harris recurrence is the following:

Proposition

If for every $A\in {\mathcal {B}}({\mathcal {X}})$, we have $P_{x}(\tau _{A}<\infty )=1$ for every $x\in A$, then $P_{x}(\eta _{A}=\infty )=1$ for all $x\in {\mathcal {X}}$, and the chain $(X_{n})$ is Harris recurrent.

This definition is only needed when the state space ${\mathcal {X}}$ is uncountable. In the countable case, recurrence corresponds to $\mathbb {E} _{x}[\eta _{x}]=\infty$, which is equivalent to $P_{x}(\tau _{x}<\infty )=1$ for all $x\in {\mathcal {X}}$.

Definition (Invariant measure)

A $\sigma$-finite measure $\pi$ is said to be **invariant** for the transition kernel $K(\cdot ,\cdot )$ (and the associated chain) if:

$\pi (B)=\int _{\mathcal {X}}K(x,B)\,\pi (dx),\qquad \forall B\in {\mathcal {B}}({\mathcal {X}}).$

When there exists an *invariant probability measure* for a **ψ-irreducible** (hence recurrent) chain, the chain is said to be **positive recurrent**. Recurrent chains that do not allow for a finite invariant measure are called **null recurrent**.

In applications of Markov Chain Monte Carlo (MCMC), a very useful criterion for Harris recurrence involves the use of bounded harmonic functions.

Definition (Harmonic function)

A measurable function $h$ is said to be **harmonic** for the chain $(X_{n})$ if:

$\mathbb {E} [h(X_{n+1})\mid x_{n}]=h(x_{n})$

These functions are *invariant* under the transition kernel in the functional sense, and they help characterize Harris recurrence.

Proposition

*For a positive Markov chain, if the only bounded harmonic functions are the constant functions, then the chain is Harris recurrent.*

### Law of Large Numbers for MCMC

Theorem (Ergodic Theorem for MCMC)

If $(X_{n})$ has a $\sigma$-finite invariant measure $\pi$, then the following two statements are equivalent:

1.  The Markov chain $(X_{n})$ is **Harris recurrent**.
2.  If $f,g\in L^{1}(\pi )$ with $\int g(x)\,d\pi (x)\neq 0$, then$\lim _{n\to \infty }{\frac {S_{n}(f)}{S_{n}(g)}}={\frac {\int f(x)\,d\pi (x)}{\int g(x)\,d\pi (x)}}.$

This theorem provides a fundamental justification for the use of Markov Chain Monte Carlo (MCMC) methods, and it serves as the counterpart of the [[Law of Large Numbers]] (LLN) in classical Monte Carlo.

An important aspect of this result is that $\pi$ does not need to be a probability measure. Therefore, there can be some type of strong stability even if the chain is null recurrent. Moreover, the Markov chain can be started from arbitrary state.

If $\pi$ is a probability measure, we can let $g\equiv 1$ and get

$\lim _{n\to \infty }S_{n}(f)=\int f(x)\,d\pi (x).$

This is the Ergodic Theorem that we are more familiar with.

### Central Limit Theorem for MCMC

There are several conditions under which the [[Central Limit Theorem]] (CLT) holds for Markov chain Monte Carlo (MCMC) methods. One of the most commonly used is the condition of **reversibility**.

Definition (Reversibility)

A stationary Markov chain $(X_{n})$ is said to be **reversible** if the distribution of $X_{n+1}$ given $X_{n+2}=x$ is the same as the distribution of $X_{n+1}$ given $X_{n}=x$.

This is equivalent to the *detailed balance condition*, which is defined as follows:

Definition ([Detailed balance](https://en.wikipedia.org/wiki/Detailed_balance))

A Markov chain with transition kernel $K$ satisfies the **detailed balance condition** if there exists a function $f$ such that:

$K(y,x)f(y)=K(x,y)f(x)$

for every pair $(x,y)$ in the state space.

Theorem (CLT under reversibility)

If $(X_{n})$ is aperiodic, irreducible, and reversible with invariant distribution $\pi$, then:

${\frac {1}{\sqrt {N}}}\left(\sum _{n=1}^{N}\left(h(X_{n})-\mathbb {E} ^{\pi }[h]\right)\right){\overset {\mathcal {L}}{\longrightarrow }}{\mathcal {N}}(0,\gamma _{h}^{2})$

where

$0<\gamma _{h}^{2}=\mathbb {E} _{\pi }\left[{\bar {h}}^{2}(X_{0})\right]+2\sum _{k=1}^{\infty }\mathbb {E} _{\pi }\left[{\bar {h}}(X_{0}){\bar {h}}(X_{k})\right]<+\infty$

and

${\bar {h}}(\cdot )=h(\cdot )-E[h(\cdot )]$.

Even though reversibility is a restrictive assumption in theory, it is often easily satisfied in practical MCMC algorithms by introducing auxiliary variables or using symmetric proposal mechanisms. There are many other conditions that can be used to establish CLT for MCMC such as geometric ergodicity and the discrete state space.

## Autocorrelation

MCMC methods produce autocorrelated samples, in contrast to standard Monte Carlo techniques that draw independent samples. [Autocorrelation](https://en.wikipedia.org/wiki/Autocorrelation) means successive draws from the Markov chain are statistically dependent, so each new sample adds less fresh information than an independent draw would. As a result, one must account for this correlation when assessing the accuracy of estimates from the chain. In particular, positive autocorrelation in the chain increases the variance of estimators and slows the convergence of sample averages toward the true expectation.

### Autocorrelation and efficiency

The effect of correlation on estimation can be quantified through the [Markov chain central limit theorem](https://en.wikipedia.org/wiki/Markov_chain_central_limit_theorem). For a chain targeting a distribution with variance $\sigma ^{2}$, the variance of the sample mean after $N$ steps is approximately ${\sigma ^{2}}{\big /}N_{\text{eff}}$, where $N_{\text{eff}}$ is an effective sample size smaller than $N$. Equivalently, one can express this as:

$\mathrm {Var} ({\bar {X}}_{N})\approx {\frac {\sigma ^{2}}{N}}\left(1+2\sum _{k=1}^{\infty }\rho _{k}\right)$

where ${\bar {X}}_{N}$ is the sample mean and $\rho _{k}$ is the autocorrelation of the chain at lag $k$, defined as $\rho _{k}={\frac {\mathrm {Cov} (X_{0},X_{k})}{\sqrt {\mathrm {Var} (X_{0})\mathrm {Var} (X_{k})}}}$. The term in parentheses, $1+2\sum _{k=1}^{\infty }\rho _{k}$, is often called the integrated autocorrelation. When the chain has no autocorrelation ($\rho _{k}=0$ for all $k\geq 1$), this factor equals 1, and one recovers the usual $\sigma ^{2}/N$ variance for independent samples. If the chain's samples are highly correlated, the sum of autocorrelations is large, leading to a much bigger variance for ${\bar {X}}_{N}$ than in the independent case.

### Effective sample size (ESS)

The effective sample size $N_{\text{eff}}$ is a useful diagnostic that translates the autocorrelation in a chain into an equivalent number of independent samples. It is defined by the formula:

$N_{\text{eff}}={\frac {N}{1+2\sum _{k=1}^{\infty }\rho _{k}}}$

so that $N_{\text{eff}}$ is the number of independent draws that would yield the same estimation precision as the $N$ dependent draws from the Markov chain. For example, if $1+2\sum _{k=1}^{\infty }\rho _{k}=5$, then $N_{\text{eff}}=N/5$, meaning the chain of length $N$ carries information equivalent to $N/5$ independent samples. In an ideal scenario with no correlation, $\rho _{k}=0$ and thus $N_{\text{eff}}\approx N$. But in a poorly mixing chain with strong autocorrelation, $N_{\text{eff}}$ can be much smaller than $N$. In practice, monitoring the ESS for each parameter is a way to gauge how much correlation is present: a low ESS indicates that many more iterations may be needed to achieve a desired effective sample of independent draws.

### Reducing correlation

While MCMC methods were created to address multi-dimensional problems better than generic Monte Carlo algorithms, when the number of dimensions rises they too tend to suffer the [curse of dimensionality](https://en.wikipedia.org/wiki/Curse_of_dimensionality): regions of higher probability tend to stretch and get lost in an increasing volume of space that contributes little to the integral. One way to address this problem could be shortening the steps of the walker, so that it does not continuously try to exit the highest probability region, though this way the process would be highly autocorrelated and expensive (i.e. many steps would be required for an accurate result). More sophisticated methods such as [Hamiltonian Monte Carlo](https://en.wikipedia.org/wiki/Hamiltonian_Monte_Carlo) and the [Wang and Landau algorithm](https://en.wikipedia.org/wiki/Wang_and_Landau_algorithm) use various ways of reducing this autocorrelation, while managing to keep the process in the regions that give a higher contribution to the integral. These algorithms usually rely on a more complicated theory and are harder to implement, but they usually converge faster.

We outline several general strategies such as reparameterization, adaptive proposal tuning, parameter blocking, and overrelaxation that help reduce correlation and improve sampling efficiency within the standard MCMC framework.

#### Reparameterization

One way to reduce autocorrelation is to reformulate or reparameterize the statistical model so that the posterior geometry leads to more efficient sampling. By changing the coordinate system or using alternative variable definitions, one can often lessen correlations. For example, in [Bayesian hierarchical modeling](https://en.wikipedia.org/wiki/Bayesian_hierarchical_modeling), a non-centered parameterization can be used in place of the standard (centered) formulation to avoid extreme posterior correlations between latent and higher-level parameters. This involves expressing [latent variables](https://en.wikipedia.org/wiki/Latent_variables) in terms of independent auxiliary variables, dramatically improving mixing. Such reparameterization strategies are commonly employed in both [[Gibbs Sampling]] and [[Metropolis Hastings Algorithm|Metropolis–Hastings algorithm]] to enhance convergence and reduce autocorrelation.

#### Proposal tuning and adaptation

Another approach to reducing correlation is to improve the MCMC proposal mechanism. In [[Metropolis Hastings Algorithm|Metropolis–Hastings algorithm]], step size tuning is critical: if the proposed steps are too small, the sampler moves slowly and produces highly correlated samples; if the steps are too large, many proposals are rejected, resulting in repeated values. Adjusting the proposal step size during an initial testing phase helps find a balance where the sampler explores the space efficiently without too many rejections.

Adaptive MCMC methods modify proposal distributions based on the chain's past samples. For instance, the adaptive Metropolis algorithm updates the Gaussian proposal distribution using the full information accumulated from the chain so far, allowing the proposal to adapt over time.

#### Parameter blocking

Parameter blocking is a technique that reduces autocorrelation in MCMC by updating parameters jointly rather than one at a time. When parameters exhibit strong posterior correlations, one-by-one updates can lead to poor mixing and slow exploration of the target distribution. By identifying and sampling blocks of correlated parameters together, the sampler can more effectively traverse high-density regions of the posterior.

Parameter blocking is commonly used in both Gibbs sampling and Metropolis–Hastings algorithms. In blocked Gibbs sampling, entire groups of variables are updated conditionally at each step. In Metropolis–Hastings, multivariate proposals enable joint updates (i.e., updates of multiple parameters at once using a vector-valued proposal distribution, typically a multivariate Gaussian), though they often require careful tuning of the proposal covariance matrix.

#### Overrelaxation

Overrelaxation is a technique to reduce autocorrelation between successive samples by proposing new samples that are negatively correlated with the current state. This helps the chain explore the posterior more efficiently, especially in high-dimensional Gaussian models or when using Gibbs sampling. The basic idea is to reflect the current sample across the conditional mean, producing proposals that retain the correct stationary distribution but with reduced serial dependence. Overrelaxation is particularly effective when combined with Gaussian conditional distributions, where exact reflection or partial overrelaxation can be analytically implemented.

## Examples

### Random walk Monte Carlo methods

- [[Metropolis Hastings Algorithm|Metropolis–Hastings algorithm]]: This method generates a Markov chain using a proposal density for new steps and a method for rejecting some of the proposed moves. It is actually a general framework which includes as special cases the very first and simpler MCMC (Metropolis algorithm) and many more recent variants listed below.
  - [[Gibbs Sampling]]: When target distribution is multi-dimensional, Gibbs sampling algorithm updates each coordinate from its full [conditional distribution](https://en.wikipedia.org/wiki/Conditional_distribution) given other coordinates. Gibbs sampling can be viewed as a special case of Metropolis–Hastings algorithm with acceptance rate uniformly equal to 1. When drawing from the full conditional distributions is not straightforward other samplers-within-Gibbs are used (e.g., see ). Gibbs sampling is popular partly because it does not require any 'tuning'. Algorithm structure of the Gibbs sampling highly resembles that of the coordinate ascent variational inference in that both algorithms utilize the full-conditional distributions in the updating procedure.
  - [Metropolis-adjusted Langevin algorithm](https://en.wikipedia.org/wiki/Metropolis-adjusted_Langevin_algorithm) and other methods that rely on the gradient (and possibly second derivative) of the log target density to propose steps that are more likely to be in the direction of higher probability density.
  - [Hamiltonian (or hybrid) Monte Carlo](https://en.wikipedia.org/wiki/Hamiltonian_Monte_Carlo) (HMC): Tries to avoid random walk behaviour by introducing an auxiliary [momentum](https://en.wikipedia.org/wiki/Momentum) vector and implementing [Hamiltonian dynamics](https://en.wikipedia.org/wiki/Hamiltonian_dynamics), so the potential energy function is the target density. The momentum samples are discarded after sampling. The result of hybrid Monte Carlo is that proposals move across the sample space in larger steps; they are therefore less correlated and converge to the target distribution more rapidly.
  - [Pseudo-marginal Metropolis–Hastings](https://en.wikipedia.org/wiki/Pseudo-marginal_Metropolis%E2%80%93Hastings_algorithm): This method replaces the evaluation of the density of the target distribution with an unbiased estimate and is useful when the target density is not available analytically, e.g. [latent variable models](https://en.wikipedia.org/wiki/Latent_variable_model).
- [Slice sampling](https://en.wikipedia.org/wiki/Slice_sampling): This method depends on the principle that one can sample from a distribution by sampling uniformly from the region under the plot of its density function. It alternates uniform sampling in the vertical direction with uniform sampling from the horizontal 'slice' defined by the current vertical position.
- [Multiple-try Metropolis](https://en.wikipedia.org/wiki/Multiple-try_Metropolis): This method is a variation of the Metropolis–Hastings algorithm that allows multiple trials at each point. By making it possible to take larger steps at each iteration, it helps address the curse of dimensionality.
- [Reversible-jump](https://en.wikipedia.org/wiki/Reversible-jump): This method is a variant of the Metropolis–Hastings algorithm that allows proposals that change the dimensionality of the space. Markov chain Monte Carlo methods that change dimensionality have long been used in [statistical physics](https://en.wikipedia.org/wiki/Statistical_physics) applications, where for some problems a distribution that is a [grand canonical ensemble](https://en.wikipedia.org/wiki/Grand_canonical_ensemble) is used (e.g., when the number of molecules in a box is variable). But the reversible-jump variant is useful when doing Markov chain Monte Carlo or Gibbs sampling over [nonparametric](https://en.wikipedia.org/wiki/Nonparametric) Bayesian models such as those involving the [Dirichlet process](https://en.wikipedia.org/wiki/Dirichlet_process) or [Chinese restaurant process](https://en.wikipedia.org/wiki/Chinese_restaurant_process), where the number of mixing components/clusters/etc. is automatically inferred from the data.

### Interacting particle methods

Interacting MCMC methodologies are a class of [mean-field particle methods](https://en.wikipedia.org/wiki/Mean-field_particle_methods) for obtaining [random samples](https://en.wikipedia.org/wiki/Pseudo-random_number_sampling) from a sequence of probability distributions with an increasing level of sampling complexity. These probabilistic models include path space state models with increasing time horizon, posterior distributions w.r.t. sequence of partial observations, increasing constraint level sets for conditional distributions, decreasing temperature schedules associated with some Boltzmann–Gibbs distributions, and many others. In principle, any Markov chain Monte Carlo sampler can be turned into an interacting Markov chain Monte Carlo sampler. These interacting Markov chain Monte Carlo samplers can be interpreted as a way to run in parallel a sequence of Markov chain Monte Carlo samplers. For instance, interacting [simulated annealing](https://en.wikipedia.org/wiki/Simulated_annealing) algorithms are based on independent Metropolis–Hastings moves interacting sequentially with a selection-resampling type mechanism. In contrast to traditional Markov chain Monte Carlo methods, the precision parameter of this class of interacting Markov chain Monte Carlo samplers is *only* related to the number of interacting Markov chain Monte Carlo samplers. These advanced particle methodologies belong to the class of Feynman–Kac particle models, also called Sequential Monte Carlo or [particle filter](https://en.wikipedia.org/wiki/Particle_filter) methods in [Bayesian inference](https://en.wikipedia.org/wiki/Bayesian_inference) and [signal processing](https://en.wikipedia.org/wiki/Signal_processing) communities. Interacting Markov chain Monte Carlo methods can also be interpreted as a mutation-selection [genetic particle algorithm](https://en.wikipedia.org/wiki/Genetic_algorithm) with Markov chain Monte Carlo mutations.

### Quasi-Monte Carlo

The [quasi-Monte Carlo method](https://en.wikipedia.org/wiki/Quasi-Monte_Carlo_method) is an analog to the normal Monte Carlo method that uses [low-discrepancy sequences](https://en.wikipedia.org/wiki/Low-discrepancy_sequence) instead of random numbers. It yields an integration error that decays faster than that of true random sampling, as quantified by the [Koksma–Hlawka inequality](https://en.wikipedia.org/wiki/Low-discrepancy_sequence#The_Koksma–Hlawka_inequality). Empirically it allows the reduction of both estimation error and convergence time by an order of magnitude. Markov chain quasi-Monte Carlo methods such as the Array–RQMC method combine randomized quasi–Monte Carlo and Markov chain simulation by simulating $n$ chains simultaneously in a way that better approximates the true distribution of the chain than with ordinary MCMC. In empirical experiments, the variance of the average of a function of the state sometimes converges at rate $O(n^{-2})$ or even faster, instead of the $O(n^{-1})$ Monte Carlo rate.

## Applications

MCMC methods are primarily used for calculating [numerical approximations](https://en.wikipedia.org/wiki/Numerical_analysis) of [multi-dimensional integrals](https://en.wikipedia.org/wiki/Multiple_integral), for example in [Bayesian statistics](https://en.wikipedia.org/wiki/Bayesian_statistics), [computational physics](https://en.wikipedia.org/wiki/Computational_physics), [computational biology](https://en.wikipedia.org/wiki/Computational_biology) and [computational linguistics](https://en.wikipedia.org/wiki/Computational_linguistics).

### Bayesian statistics

In Bayesian statistics, Markov chain Monte Carlo methods are typically used to calculate [moments](https://en.wikipedia.org/wiki/Moment_(mathematics) "Moment (mathematics)") and [credible intervals](https://en.wikipedia.org/wiki/Credible_interval) of [posterior probability](https://en.wikipedia.org/wiki/Posterior_probability) distributions. The use of MCMC methods makes it possible to compute large [hierarchical models](https://en.wikipedia.org/wiki/Bayesian_network#Hierarchical_models) that require integrations over hundreds to thousands of unknown parameters.

### Statistical physics

Many contemporary research problems in statistical physics can be addressed by approximate solutions using Monte Carlo simulation, which provides valuable insights into the properties of complex systems. Monte Carlo methods are fundamental in computational physics, astrophysics, physical chemistry, and related disciplines, with broad applications including medical physics, where they are employed to model radiation transport for radiation dosimetry calculations. Instead of exhaustively analyzing all possible system states, the Monte Carlo method randomly examines a subset of them to form a representative sample, and yields accurate approximations of the system's characteristic properties. As the number of sampled states increases, the error can be further reduced to a lower level.

### Complex distribution sampling

![[media/bfa40e1d672f0997e87125c158df2250cd241668.gif]]
A simulation of sampling from a Wikipedia-logo-like distribution via Langevin Dynamics and score matching

Langevin Dynamics are typically used in complex distribution sampling and generative modeling, via an MCMC procedure. Specifically, given the probability density function $p(x)$, we use its log gradient $\nabla _{x}\log p(x)$ as the score function and start from a prior distribution $x_{0}\sim p_{0}$. Then, a chain is built by

$x_{i+1}=x_{i}+\epsilon \nabla _{x}\log p(x)+{\sqrt {2\epsilon }}z_{i},z_{i}\sim {\mathcal {N}}(0,I)$

for $i=0,\dots ,K$. When $\epsilon \rightarrow 0$ and $K\rightarrow \infty$, $x_{K}$ converges to a sample from the target distribution $p(x)$.

For some complex distribution, if we know its probability density function but find it difficult to directly sample from it, we can apply Langevin Dynamics as an alternate. However, in most cases, especially generative modeling, usually we do not know the exact probability density function of the target distribution we wish to sample from, neither the score function $\nabla _{x}\log p(x)$. In this case, score matching methods provide feasible solutions, minimizing the [Fisher information metric](https://en.wikipedia.org/wiki/Fisher_information_metric) between a parameterized score-based model $s_{\theta }(x)$ and the score function without knowing the ground-truth data score. The score function can be estimated on a training dataset by [[Stochastic Gradient Descent]].

In real cases, however, the training data only takes a small region of the target distribution, and the estimated score functions are inaccurate in other low density regions with fewer available data examples. To overcome this challenge, denoising score matching methods purturb the available data examples with noise of different scales, which can improve the coverage of low density regions, and use them as the training dataset for the score-base model. Note that the choice of noise scales is tricky, as too large noise will corrupt the original data, while too small noise will not populate the original data to those low density regions. Thus, carefully crafted noise schedules are applied for higher quality generation.

## Convergence

Usually it is not hard to construct a Markov chain with the desired properties. The more difficult problem is to determine (1) when to start collecting statistics and (2) how many steps are needed to converge to the stationary distribution within an acceptable error. Fortunately, there are a variety of practical diagnostics to empirically assess convergence.

### Total variation distance

Formally, let $\pi$ denote the stationary distribution and $P^{t}(x,\cdot )$ the distribution of the Markov chain after $t$ steps starting from state $x$. Theoretically, convergence can be quantified by measuring the [total variation distance](https://en.wikipedia.org/wiki/Total_variation_distance_of_probability_measures):

$d_{\text{TV}}(P^{t}(x,\cdot ),\pi )=\sup _{A}|P^{t}(x,A)-\pi (A)|$

A chain is said to mix rapidly if $d_{\text{TV}}(P^{t}(x,\cdot ),\pi )\leq \epsilon$ for all $x\in {\mathcal {X}}$ within a small number of steps $t$ under a pre-defined tolerance $\epsilon >0$. In other words, the stationary distribution is reached quickly starting from an arbitrary position, and the minimum such $t$ is known as the [mixing time](https://en.wikipedia.org/wiki/Markov_chain_mixing_time). In practice, however, the total variation distance is generally intractable to compute, especially in high-dimensional problems or when the stationary distribution is only known up to a normalizing constant (as in most Bayesian applications).

### Gelman-Rubin diagnostics

The [Gelman-Rubin statistic](https://en.wikipedia.org/wiki/Gelman-Rubin_statistic), also known as the **potential scale reduction factor (PSRF)**, evaluates MCMC convergence by sampling multiple independent Markov chains and comparing within-chain and between-chain variances. If all chains have converged to the same stationary distribution, the between-chain and within-chain variances should be similar, and thus the PSRF must approach 1. In practice, a value of $<1.1$ is often taken as evidence of convergence. Higher values suggest that the chains are still exploring different parts of the target distribution.

### Geweke diagnostics

The Geweke diagnostic examines whether the distribution of samples in the early part of the Markov chain is statistically indistinguishable from the distribution in a later part. Given a sequence of correlated MCMC samples $\{X_{1},X_{2},\dots ,X_{n}\}$, the diagnostic splits the chain into an early segment consisting of the first $n_{A}$ samples, typically chosen as $n_{A}=0.1n$ (i.e., the first 10% of the chain), and a late segment consisting of the last $n_{B}$ samples, typically chosen as $n_{B}=0.5n$ (i.e., the last 50% of the chain)

Denote the sample means of these segments as:

${\bar {X}}_{A}={\dfrac {1}{n_{A}}}\sum _{i=1}^{n_{A}}X_{i},\;\;\;{\bar {X}}_{B}={\dfrac {1}{n_{B}}}\sum _{i=n-n_{B}+1}^{n}X_{i}$

Since MCMC samples are autocorrelated, a simple comparison of sample means is insufficient. Instead, the difference in means is standardized using an estimator of the spectral density at zero frequency, which accounts for the long-range dependencies in the chain. The test statistic is computed as:

$Z={\dfrac {{\bar {X}}_{A}-{\bar {X}}_{B}}{\sqrt {{\hat {S}}(0)/n_{A}+{\hat {S}}(0)/n_{B}}}}$

where ${\hat {S}}(0)$ is an estimate of the long-run variance (i.e., the spectral density at frequency zero), commonly estimated using [Newey-West estimators](https://en.wikipedia.org/wiki/Newey%E2%80%93West_estimator) or batch means. Under the null hypothesis of convergence, the statistic $Z$ follows an approximately standard normal distribution $Z\sim {\mathcal {N}}(0,1)$.

If $|Z|>1.96$, the null hypothesis is rejected at the 5% significance level, suggesting that the chain has not yet reached stationarity.

### Heidelberger-Welch diagnostics

The Heidelberger-Welch diagnostic is grounded in [spectral analysis](https://en.wikipedia.org/wiki/Spectral_theory) and [[Brownian Motion|Brownian motion theory]], and is particularly useful in the early stages of simulation to determine appropriate burn-in and stopping time. The diagnostic consists of two components, a **stationarity test** that assesses whether the Markov chain has reached a steady-state, and a **half-width test** that determines whether the estimated expectation is within a user-specified precision.

#### Stationary test

Let $\{X_{t}\}_{t=1}^{n}$ be the output of an MCMC simulation for a scalar function $g(X_{t})$, and $g_{1},g_{2},\dots ,g_{n}$ the evaluations of the function $g$ over the chain. Define the standardized cumulative sum process:

$B_{n}(t)={\dfrac {\sum _{i=1}^{{\text{round}}(nt)}g_{i}-{\text{round}}(nt){\bar {g}}_{n}}{\sqrt {n{\hat {S}}(0)}}},\;\;\;t\in [0,1]$

where ${\bar {g}}_{n}={\frac {1}{n}}\sum _{i=1}^{n}g_{i}$ is the sample mean and ${\hat {S}}(0)$ is an estimate of the spectral density at frequency zero.

Under the null hypothesis of convergence, the process $B_{n}(t)$ converges in distribution to a [Brownian bridge](https://en.wikipedia.org/wiki/Brownian_bridge). The following [Cramér-von Mises statistic](https://en.wikipedia.org/wiki/Cram%C3%A9r%E2%80%93von_Mises_criterion) is used to test for stationarity:

$C_{n}=\int _{0}^{1}B_{n}(t)^{2}dt.$

This statistic is compared against known critical values from the Brownian bridge distribution. If the null hypothesis is rejected, the first 10% of the samples are discarded and the test can be repeated on the remaining chain until either stationarity is accepted or 50% of the chain is discarded.

#### Half-Width test (Precision check)

Once stationarity is accepted, the second part of the diagnostic checks whether the Monte Carlo estimator is accurate enough for practical use. Assuming the central limit theorem holds, the confidence interval for the mean $\mathbb {E} _{\pi }[g(X)]$ is given by

${\bar {g}}_{n}\pm t_{\alpha /2,\nu }\cdot {\dfrac {{\hat {\sigma }}_{n}}{\sqrt {n}}}$

where ${\hat {\sigma }}^{2}$ is an estimate of the variance of $g(X)$, $t_{\alpha /2,\nu }$ is the [Student's $t$](https://en.wikipedia.org/wiki/Student%27s_t-test) critical value at confidence level $1-\alpha$ and degrees of freedom $\nu$, $n$ is the number of samples used.

The **half-width** of this interval is defined as

$t_{\alpha /2,\nu }\cdot {\dfrac {{\hat {\sigma }}_{n}}{\sqrt {n}}}$

If the half-width is smaller than a user-defined tolerance (e.g., 0.05), the chain is considered long enough to estimate the expectation reliably. Otherwise, the simulation should be extended.

### Raftery-Lewis diagnostics

The Raftery-Lewis diagnostic is specifically designed to assess how many iterations are needed to estimate quantiles or tail probabilities of the target distribution with a desired accuracy and confidence. Unlike Gelman-Rubin or Geweke diagnostics, which are based on assessing convergence to the entire distribution, the Raftery-Lewis diagnostic is goal-oriented as it provides estimates for the number of samples required to estimate a specific quantile of interest within a desired margin of error.

Let $q$ denote the desired quantile (e.g., 0.025) of a real-valued function $g(X)$: in other words, the goal is to find $u$ such that $P(g(X)\leq u)=q$. Suppose we wish to estimate this quantile such that the estimate falls within margin $\varepsilon$ of the true value with probability $1-\alpha$. That is, we want

$P(|{\hat {q}}-q|<\varepsilon )\geq 1-\alpha$

The diagnostic proceeds by converting the output of the MCMC chain into a binary sequence:

$W_{n}=\mathbb {I} (g(X_{n})\leq u),\;\;\;n=1,2,\dots$

where $I(\cdot )$ is the indicator function. The sequence $\{W_{n}\}$ is treated as a realization from a two-state Markov chain. While this may not be strictly true, it is often a good approximation in practice.

From the empirical transitions in the binary sequence, the Raftery-Lewis method estimates:

- The minimum number of iterations $n_{\text{min}}$ required to achieve the desired precision and confidence for estimating the quantile is obtained based on asymptotic theory for Bernoulli processes:

$n_{\text{min}}={\bigg \{}\Phi ^{-1}{\bigg (}1-{\dfrac {\alpha }{2}}{\bigg )}{\bigg \}}^{2}{\dfrac {q(1-q)}{\varepsilon ^{2}}}$

where $\Phi ^{-1}(\cdot )$ is the standard normal quantile function.

- The burn-in period $n_{\text{burn}}$ is calculated using eigenvalue analysis of the transition matrix to estimate the number of initial iterations needed for the Markov chain to forget its initial state.

## See also

- [Coupling from the past](https://en.wikipedia.org/wiki/Coupling_from_the_past)
- [Integrated nested Laplace approximations](https://en.wikipedia.org/wiki/Integrated_nested_Laplace_approximations)
- [Markov chain central limit theorem](https://en.wikipedia.org/wiki/Markov_chain_central_limit_theorem)
- [Metropolis-adjusted Langevin algorithm](https://en.wikipedia.org/wiki/Metropolis-adjusted_Langevin_algorithm)

## References

### Citations

1.  Robert, Christian; Casella, George (2011). "A short history of Markov chain Monte Carlo: Subjective recollections from incomplete data". *Statistical Science*. **26** (1): 102–115. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[0808.2902](https://arxiv.org/abs/0808.2902). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2011StaSc..26TS351R](https://ui.adsabs.harvard.edu/abs/2011StaSc..26TS351R). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/10-STS351](https://doi.org/10.1214%2F10-STS351).
2.  Robert and Casella (2004), pp. 205–246
3.  Papaspiliopoulos, Omiros; Roberts, Gareth O.; Sköld, Martin (2007). "A general framework for the parametrization of hierarchical models". *Statistical Science*. **22** (1). Institute of Mathematical Statistics: 59–73. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[0708.3797](https://arxiv.org/abs/0708.3797). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2007StaSc..2200014P](https://ui.adsabs.harvard.edu/abs/2007StaSc..2200014P). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/088342307000000014](https://doi.org/10.1214%2F088342307000000014).
4.  Haario, Heikki; Saksman, Eero; Tamminen, Johanna (2001). ["An adaptive Metropolis algorithm"](https://www.researchgate.net/publication/38322292). *Bernoulli*. **7** (2): 223–242. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/3318737](https://doi.org/10.2307%2F3318737). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [3318737](https://www.jstor.org/stable/3318737).
5.  Óli Páll Geirsson, Birgir Hrafnkelsson, and Helgi Sigurðarson (2015). "A Block Gibbs Sampling Scheme for Latent Gaussian Models." arXiv preprint \[arXiv:1506.06285\]([https://arxiv.org/abs/1506.06285](https://arxiv.org/abs/1506.06285)).
6.  Siddhartha Chib and Srikanth Ramamurthy (2009). "Tailored Randomized Block MCMC Methods with Application to DSGE Models." \*Journal of Econometrics\*, 155(1), 19–38. [doi:10.1016/j.jeconom.2009.08.003](https://doi.org/10.1016/j.jeconom.2009.08.003)
7.  Piero Barone, Giovanni Sebastiani, and Jonathan Stander (2002). "Over-relaxation methods and coupled Markov chains for Monte Carlo simulation." *Statistics and Computing*, 12(1), 17–26. [doi:10.1023/A:1013112103963](https://doi.org/10.1023/A:1013112103963)
8.  Geman, Stuart; Geman, Donald (November 1984). "Stochastic Relaxation, Gibbs Distributions, and the Bayesian Restoration of Images". *IEEE Transactions on Pattern Analysis and Machine Intelligence*. PAMI-6 (6): 721–741. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1984ITPAM...6..721G](https://ui.adsabs.harvard.edu/abs/1984ITPAM...6..721G). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/TPAMI.1984.4767596](https://doi.org/10.1109%2FTPAMI.1984.4767596). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0162-8828](https://search.worldcat.org/issn/0162-8828). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [22499653](https://pubmed.ncbi.nlm.nih.gov/22499653). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [5837272](https://api.semanticscholar.org/CorpusID:5837272).
9.  Gilks, W. R.; Wild, P. (1992-01-01). "Adaptive Rejection Sampling for Gibbs Sampling". *Journal of the Royal Statistical Society. Series C (Applied Statistics)*. **41** (2): 337–348. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2347565](https://doi.org/10.2307%2F2347565). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2347565](https://www.jstor.org/stable/2347565).
10. Gilks, W. R.; [Best, N. G.](https://en.wikipedia.org/wiki/Nicky_Best); Tan, K. K. C. (1995-01-01). "Adaptive Rejection Metropolis Sampling within Gibbs Sampling". *Journal of the Royal Statistical Society. Series C (Applied Statistics)*. **44** (4): 455–472. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2986138](https://doi.org/10.2307%2F2986138). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2986138](https://www.jstor.org/stable/2986138).
11. Lee, Se Yoon (2021). "Gibbs sampler and coordinate ascent variational inference: A set-theoretical review". *Communications in Statistics - Theory and Methods*. **51** (6): 1–21. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2008.01006](https://arxiv.org/abs/2008.01006). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/03610926.2021.1921214](https://doi.org/10.1080%2F03610926.2021.1921214). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [220935477](https://api.semanticscholar.org/CorpusID:220935477).
12. See Stramer 1999.
13. See Green 1995.
14. Del Moral, Pierre (2013). [Mean field simulation for Monte Carlo integration](http://www.crcpress.com/product/isbn/9781466504059). Chapman & Hall/CRC Press. p. 626.
15. Del Moral, Pierre (2004). [Feynman–Kac formulae. Genealogical and interacting particle approximations](https://www.springer.com/mathematics/probability/book/978-0-387-20268-6). Springer. p. 575.
16. Del Moral, Pierre; Miclo, Laurent (2000). "Branching and Interacting Particle Systems Approximations of Feynman-Kac Formulae with Applications to Non-Linear Filtering". In Jacques Azéma; Michel Ledoux; Michel Émery; Marc Yor (eds.). [Séminaire de Probabilités XXXIV](http://archive.numdam.org/ARCHIVE/SPS/SPS_2000__34_/SPS_2000__34__1_0/SPS_2000__34__1_0.pdf) (PDF). Lecture Notes in Mathematics. Vol. 1729. pp. 1–145. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/bfb0103798](https://doi.org/10.1007%2Fbfb0103798). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-67314-9](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-67314-9).
17. Del Moral, Pierre (2006). "Sequential Monte Carlo samplers". *Journal of the Royal Statistical Society. Series B (Statistical Methodology)*. **68** (3): 411–436. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[cond-mat/0212648](https://arxiv.org/abs/cond-mat/0212648). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1111/j.1467-9868.2006.00553.x](https://doi.org/10.1111%2Fj.1467-9868.2006.00553.x). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [12074789](https://api.semanticscholar.org/CorpusID:12074789).
18. ^   Papageorgiou, Anargyros; Traub, Joseph (1996). ["Beating Monte Carlo"](https://iiif.library.cmu.edu/file/Traub_box00030_fld00008_bdl0001_doc0001/Traub_box00030_fld00008_bdl0001_doc0001.pdf) (PDF). *Risk*. **9** (6): 63–65.
19. Sobol, Ilya M (1998). "On quasi-monte carlo integrations". *Mathematics and Computers in Simulation*. **47** (2): 103–112. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/s0378-4754(98)00096-2](https://doi.org/10.1016%2Fs0378-4754%2898%2900096-2).
20. Chen, S.; Dick, Josef; Owen, Art B. (2011). ["Consistency of Markov chain quasi-Monte Carlo on continuous state spaces"](https://doi.org/10.1214%2F10-AOS831). *[Annals of Statistics](https://en.wikipedia.org/wiki/Annals_of_Statistics)*. **39** (2): 673–701. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1105.1896](https://arxiv.org/abs/1105.1896). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/10-AOS831](https://doi.org/10.1214%2F10-AOS831).
21. Tribble, Seth D. (2007). *Markov chain Monte Carlo algorithms using completely uniformly distributed driving sequences* (Diss.). Stanford University. [ProQuest](https://en.wikipedia.org/wiki/ProQuest) [304808879](https://www.proquest.com/docview/304808879).
22. L'Ecuyer, P.; Lécot, C.; Tuffin, B. (2008). ["A Randomized Quasi-Monte Carlo Simulation Method for Markov Chains"](https://hal.inria.fr/inria-00070462/file/RR-5545.pdf) (PDF). *[Operations Research](https://en.wikipedia.org/wiki/Operations_Research_(journal) "Operations Research (journal)")*. **56** (4): 958–975. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1287/opre.1080.0556](https://doi.org/10.1287%2Fopre.1080.0556).
23. L'Ecuyer, P.; Munger, D.; Lécot, C.; Tuffin, B. (2018). "Sorting Methods and Convergence Rates for Array-RQMC: Some Empirical Comparisons". *Mathematics and Computers in Simulation*. **143**: 191–201. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.matcom.2016.07.010](https://doi.org/10.1016%2Fj.matcom.2016.07.010).
24. Kasim, M.F.; Bott, A.F.A.; Tzeferacos, P.; Lamb, D.Q.; Gregori, G.; Vinko, S.M. (September 2019). "Retrieving fields from proton radiography without source profiles". *Physical Review E*. **100** (3) 033208. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1905.12934](https://arxiv.org/abs/1905.12934). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2019PhRvE.100c3208K](https://ui.adsabs.harvard.edu/abs/2019PhRvE.100c3208K). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1103/PhysRevE.100.033208](https://doi.org/10.1103%2FPhysRevE.100.033208). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [31639953](https://pubmed.ncbi.nlm.nih.gov/31639953). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [170078861](https://api.semanticscholar.org/CorpusID:170078861).
25. Gupta, Ankur; Rawlings, James B. (April 2014). ["Comparison of Parameter Estimation Methods in Stochastic Chemical Kinetic Models: Examples in Systems Biology"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4946376). *AIChE Journal*. **60** (4): 1253–1268. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2014AIChE..60.1253G](https://ui.adsabs.harvard.edu/abs/2014AIChE..60.1253G). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1002/aic.14409](https://doi.org/10.1002%2Faic.14409). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [4946376](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4946376). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [27429455](https://pubmed.ncbi.nlm.nih.gov/27429455).
26. See Gill 2008.
27. See Robert & Casella 2004.
28. Banerjee, Sudipto; Carlin, Bradley P.; Gelfand, Alan P. (2014-09-12). *Hierarchical Modeling and Analysis for Spatial Data* (Second ed.). CRC Press. p. xix. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4398-1917-3](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4398-1917-3).
29. Jia, Xun; Ziegenhein, Peter; Jiang, Steve B. (2014-02-21). ["GPU-based high-performance computing for radiation therapy"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4003902). *Physics in Medicine and Biology*. **59** (4): R151–182. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2014PMB....59R.151J](https://ui.adsabs.harvard.edu/abs/2014PMB....59R.151J). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1088/0031-9155/59/4/R151](https://doi.org/10.1088%2F0031-9155%2F59%2F4%2FR151). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1361-6560](https://search.worldcat.org/issn/1361-6560). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [4003902](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4003902). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [24486639](https://pubmed.ncbi.nlm.nih.gov/24486639).
30. Rogers, D. W. O. (July 2006). ["REVIEW: Fifty years of Monte Carlo simulations for medical physics"](https://ui.adsabs.harvard.edu/abs/2006PMB....51R.287R/abstract). *Physics in Medicine and Biology*. **51** (13): R287–R301. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2006PMB....51R.287R](https://ui.adsabs.harvard.edu/abs/2006PMB....51R.287R). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1088/0031-9155/51/13/R17](https://doi.org/10.1088%2F0031-9155%2F51%2F13%2FR17). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0031-9155](https://search.worldcat.org/issn/0031-9155). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [16790908](https://pubmed.ncbi.nlm.nih.gov/16790908).
31. Hinton, Geoffrey E. (2002-08-01). ["Training Products of Experts by Minimizing Contrastive Divergence"](https://ieeexplore.ieee.org/document/6789337). *Neural Computation*. **14** (8): 1771–1800. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1162/089976602760128018](https://doi.org/10.1162%2F089976602760128018). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0899-7667](https://search.worldcat.org/issn/0899-7667). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [12180402](https://pubmed.ncbi.nlm.nih.gov/12180402).
32. ^    Song, Yang; Ermon, Stefano (2019-12-08), ["Generative modeling by estimating gradients of the data distribution"](https://dl.acm.org/doi/10.5555/3454287.3455354), *Proceedings of the 33rd International Conference on Neural Information Processing Systems*, no. 1067, Red Hook, NY, USA: Curran Associates Inc., pp. 11918–11930, retrieved 2025-04-28
33. Hyvärinen, Aapo (2005). ["Estimation of Non-Normalized Statistical Models by Score Matching"](https://jmlr.org/papers/v6/hyvarinen05a.html). *Journal of Machine Learning Research*. **6** (24): 695–709. [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1533-7928](https://search.worldcat.org/issn/1533-7928).
34. ^   Vincent, Pascal (July 2011). ["A Connection Between Score Matching and Denoising Autoencoders"](https://ieeexplore.ieee.org/document/6795935). *Neural Computation*. **23** (7): 1661–1674. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2011NeCom..23.1661V](https://ui.adsabs.harvard.edu/abs/2011NeCom..23.1661V). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1162/NECO_a_00142](https://doi.org/10.1162%2FNECO_a_00142). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0899-7667](https://search.worldcat.org/issn/0899-7667). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [21492012](https://pubmed.ncbi.nlm.nih.gov/21492012).
35. ^   Song, Yang; Garg, Sahaj; Shi, Jiaxin; Ermon, Stefano (2020-08-06). ["Sliced Score Matching: A Scalable Approach to Density and Score Estimation"](https://proceedings.mlr.press/v115/song20a). *Proceedings of the 35th Uncertainty in Artificial Intelligence Conference*. PMLR: 574–584.
36. ^   Song, Yang; Ermon, Stefano (2020-12-06). ["Improved techniques for training score-based generative models"](https://dl.acm.org/doi/abs/10.5555/3495724.3496767). *Proceedings of the 34th International Conference on Neural Information Processing Systems*. NIPS '20. Red Hook, NY, USA: Curran Associates Inc.: 12438–12448. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-7138-2954-6](https://en.wikipedia.org/wiki/Special:BookSources/978-1-7138-2954-6).
37. Cowles, M.K.; Carlin, B.P. (1996). "Markov chain Monte Carlo convergence diagnostics: a comparative review". *Journal of the American Statistical Association*. **91** (434): 883–904. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.53.3445](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.53.3445). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/01621459.1996.10476956](https://doi.org/10.1080%2F01621459.1996.10476956).
38. Roy, Vivekananda (2020-03-07). ["Convergence Diagnostics for Markov Chain Monte Carlo"](https://www.annualreviews.org/content/journals/10.1146/annurev-statistics-031219-041300). *Annual Review of Statistics and Its Application*. **7** (1): 387–412. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1909.11827](https://arxiv.org/abs/1909.11827). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2020AnRSA...7..387R](https://ui.adsabs.harvard.edu/abs/2020AnRSA...7..387R). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1146/annurev-statistics-031219-041300](https://doi.org/10.1146%2Fannurev-statistics-031219-041300). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [2326-8298](https://search.worldcat.org/issn/2326-8298).
39. Gelman, A.; Rubin, D.B. (1992). ["Inference from iterative simulation using multiple sequences (with discussion)"](https://www.stat.duke.edu/~scs/Courses/Stat376/Papers/ConvergeDiagnostics/GelmanRubinStatSci1992.pdf) (PDF). *Statistical Science*. **7** (4): 457–511. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1992StaSc...7..457G](https://ui.adsabs.harvard.edu/abs/1992StaSc...7..457G). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/ss/1177011136](https://doi.org/10.1214%2Fss%2F1177011136).
40. Geweke, John (1992-08-13), Bernardo, J M; Berger, J O; Dawid, P; Smith, A F M (eds.), ["Evaluating the Accuracy of Sampling-Based Approaches to the Calculation of Posterior Moments"](https://academic.oup.com/book/54041/chapter/422209572), *Bayesian Statistics 4*, Oxford University PressOxford, pp. 169–194, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1093/oso/9780198522669.003.0010](https://doi.org/10.1093%2Foso%2F9780198522669.003.0010), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-19-852266-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-19-852266-9), retrieved 2025-04-29`{{`[`citation`](https://en.wikipedia.org/wiki/Template:Citation)`}}`: CS1 maint: work parameter with ISBN ([link](https://en.wikipedia.org/wiki/Category:CS1_maint:_work_parameter_with_ISBN))
41. Heidelberger, Philip; Welch, Peter D. (1981-04-01). ["A spectral method for confidence interval generation and run length control in simulations"](https://dl.acm.org/doi/10.1145/358598.358630). *Commun. ACM*. **24** (4): 233–245. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1145/358598.358630](https://doi.org/10.1145%2F358598.358630). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0001-0782](https://search.worldcat.org/issn/0001-0782).
42. Heidelberger, Philip; Welch, Peter D. (1983-12-01). ["Simulation Run Length Control in the Presence of an Initial Transient"](https://pubsonline.informs.org/doi/10.1287/opre.31.6.1109). *Operations Research*. **31** (6): 1109–1144. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1287/opre.31.6.1109](https://doi.org/10.1287%2Fopre.31.6.1109). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0030-364X](https://search.worldcat.org/issn/0030-364X).
43. Raftery, Adrian E.; Lewis, Steven M. (1992-11-01). ["[Practical Markov Chain Monte Carlo]: Comment: One Long Run with Diagnostics: Implementation Strategies for Markov Chain Monte Carlo"](https://projecteuclid.org/journals/statistical-science/volume-7/issue-4/Practical-Markov-Chain-Monte-Carlo--Comment--One-Long/10.1214/ss/1177011143.full). *Statistical Science*. **7** (4). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/ss/1177011143](https://doi.org/10.1214%2Fss%2F1177011143). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0883-4237](https://search.worldcat.org/issn/0883-4237).

### Sources

- Christophe Andrieu, Nando De Freitas, Arnaud Doucet and Michael I. Jordan [An Introduction to MCMC for Machine Learning](https://www.cs.princeton.edu/courses/archive/spr06/cos598C/papers/AndrieuFreitasDoucetJordan2003.pdf), 2003
- Asmussen, Søren; Glynn, Peter W. (2007). *Stochastic Simulation: Algorithms and Analysis*. Stochastic Modelling and Applied Probability. Vol. 57. Springer.
- Atzberger, P. ["An Introduction to Monte-Carlo Methods"](https://web.math.ucsb.edu/~atzberg/pmwiki_intranet/uploads/AtzbergerHomePage/Atzberger_MonteCarlo.pdf) (PDF).
- [Berg, Bernd A.](https://en.wikipedia.org/wiki/Bernd_A._Berg) (2004). *Markov Chain Monte Carlo Simulations and Their Statistical Analysis*. [World Scientific](https://en.wikipedia.org/wiki/World_Scientific).
- Bolstad, William M. (2010). *Understanding Computational Bayesian Statistics*. Wiley. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-470-04609-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-470-04609-8).
- Carlin, Brad; Chib, Siddhartha (1995). ["Bayesian Model Choice via Markov Chain Monte Carlo Methods"](https://wwwf.imperial.ac.uk/~das01/MyWeb/SCBI/Papers/CarlinChib.pdf). *[Journal of the Royal Statistical Society, Series B](https://en.wikipedia.org/wiki/Journal_of_the_Royal_Statistical_Society)*, 57(3), 473–484.
- Casella, George; George, Edward I. (1992). "Explaining the Gibbs sampler". *[The American Statistician](https://en.wikipedia.org/wiki/The_American_Statistician)*. **46** (3): 167–174. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.554.3993](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.554.3993). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2685208](https://doi.org/10.2307%2F2685208). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2685208](https://www.jstor.org/stable/2685208).
- [Chib, Siddhartha](https://en.wikipedia.org/wiki/Siddhartha_Chib); Greenberg, Edward (1995). "Understanding the Metropolis–Hastings Algorithm". *The American Statistician*. **49** (4): 327–335. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/00031305.1995.10476177](https://doi.org/10.1080%2F00031305.1995.10476177). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2684568](https://www.jstor.org/stable/2684568).
- Gelfand, A.E.; Smith, A.F.M. (1990). "Sampling-Based Approaches to Calculating Marginal Densities". *[Journal of the American Statistical Association](https://en.wikipedia.org/wiki/Journal_of_the_American_Statistical_Association)*. **85** (410): 398–409. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.512.2330](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.512.2330). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/01621459.1990.10476213](https://doi.org/10.1080%2F01621459.1990.10476213).
- [Gelman, Andrew](https://en.wikipedia.org/wiki/Andrew_Gelman); Carlin, John B.; Stern, Hal S.; [Rubin, Donald B.](https://en.wikipedia.org/wiki/Donald_B._Rubin) (1995). *Bayesian Data Analysis* (1st ed.). [Chapman and Hall](https://en.wikipedia.org/wiki/Chapman_and_Hall). *(See Chapter 11.)*
- Geman, S.; [Geman, D.](https://en.wikipedia.org/wiki/Donald_Geman) (1984). "Stochastic Relaxation, Gibbs Distributions, and the Bayesian Restoration of Images". *[IEEE Transactions on Pattern Analysis and Machine Intelligence](https://en.wikipedia.org/wiki/IEEE_Transactions_on_Pattern_Analysis_and_Machine_Intelligence)*. **6** (6): 721–741. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1984ITPAM...6..721G](https://ui.adsabs.harvard.edu/abs/1984ITPAM...6..721G). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/TPAMI.1984.4767596](https://doi.org/10.1109%2FTPAMI.1984.4767596). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [22499653](https://pubmed.ncbi.nlm.nih.gov/22499653). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [5837272](https://api.semanticscholar.org/CorpusID:5837272).
- Gilks, W.R.; Richardson, S.; [Spiegelhalter, D.J.](https://en.wikipedia.org/wiki/David_Spiegelhalter) (1996). *Markov Chain Monte Carlo in Practice*. [Chapman and Hall](https://en.wikipedia.org/wiki/Chapman_and_Hall)/CRC.
- Gill, Jeff (2008). *Bayesian methods: a social and behavioral sciences approach* (2nd ed.). [Chapman and Hall](https://en.wikipedia.org/wiki/Chapman_and_Hall)/CRC. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-58488-562-7](https://en.wikipedia.org/wiki/Special:BookSources/978-1-58488-562-7).
- Green, P.J. (1995). "Reversible-jump Markov chain Monte Carlo computation and Bayesian model determination". *[Biometrika](https://en.wikipedia.org/wiki/Biometrika)*. **82** (4): 711–732. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.407.8942](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.407.8942). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1093/biomet/82.4.711](https://doi.org/10.1093%2Fbiomet%2F82.4.711).
- Neal, Radford M. (2003). ["Slice Sampling"](https://doi.org/10.1214%2Faos%2F1056562461). *[Annals of Statistics](https://en.wikipedia.org/wiki/Annals_of_Statistics)*. **31** (3): 705–767. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/aos/1056562461](https://doi.org/10.1214%2Faos%2F1056562461). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [3448413](https://www.jstor.org/stable/3448413).
- Neal, Radford M. (1993). ["Probabilistic Inference Using Markov Chain Monte Carlo Methods"](https://www.cs.utoronto.ca/~radford/review.abstract.html).
- Robert, Christian P.; Casella, G. (2004). [Monte Carlo Statistical Methods](https://archive.org/details/springer_10.1007-978-1-4757-4145-2) (2nd ed.). Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-21239-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-21239-5).
- Rubinstein, R.Y.; [Kroese, D.P.](https://en.wikipedia.org/wiki/Dirk_Kroese) (2007). *Simulation and the Monte Carlo Method* (2nd ed.). [Wiley](https://en.wikipedia.org/wiki/John_Wiley_%26_Sons). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-470-17794-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-470-17794-5).
- Smith, R.L. (1984). "Efficient Monte Carlo Procedures for Generating Points Uniformly Distributed Over Bounded Regions". *[Operations Research](https://en.wikipedia.org/wiki/Operations_Research:_A_Journal_of_the_Institute_for_Operations_Research_and_the_Management_Sciences)*. **32** (6): 1296–1308. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1984OpRes..32.1296S](https://ui.adsabs.harvard.edu/abs/1984OpRes..32.1296S). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1287/opre.32.6.1296](https://doi.org/10.1287%2Fopre.32.6.1296). [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[2027.42/7681](https://hdl.handle.net/2027.42%2F7681).
- Spall, J.C. (April 2003). "Estimation via Markov Chain Monte Carlo". *[IEEE Control Systems Magazine](https://en.wikipedia.org/wiki/IEEE_Control_Systems_Magazine)*. **23** (2): 34–45. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2003ICSys..23b..34S](https://ui.adsabs.harvard.edu/abs/2003ICSys..23b..34S). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/mcs.2003.1188770](https://doi.org/10.1109%2Fmcs.2003.1188770).
- Stramer, O.; Tweedie, R. (1999). "Langevin-Type Models II: Self-Targeting Candidates for MCMC Algorithms". *Methodology and Computing in Applied Probability*. **1** (3): 307–328. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1023/A:1010090512027](https://doi.org/10.1023%2FA%3A1010090512027). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [1512689](https://api.semanticscholar.org/CorpusID:1512689).

## Further reading

- [Diaconis, Persi](https://en.wikipedia.org/wiki/Persi_Diaconis) (April 2009). ["The Markov chain Monte Carlo revolution"](https://www.ams.org/bull/2009-46-02/S0273-0979-08-01238-X/S0273-0979-08-01238-X.pdf) (PDF). *[Bull. Amer. Math. Soc.](https://en.wikipedia.org/wiki/Bull._Amer._Math._Soc.)* **46** (2): 179–205. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1090/s0273-0979-08-01238-x](https://doi.org/10.1090%2Fs0273-0979-08-01238-x). S 0273-0979(08)01238-X.
- [Press, W.H.](https://en.wikipedia.org/wiki/William_H._Press); [Teukolsky, S.A.](https://en.wikipedia.org/wiki/Saul_Teukolsky); Vetterling, W.T.; Flannery, B.P. (2007). ["Section 15.8. Markov Chain Monte Carlo"](http://apps.nrbook.com/empanel/index.html#pg=824). *Numerical Recipes: The Art of Scientific Computing* (3rd ed.). [Cambridge University Press](https://en.wikipedia.org/wiki/Cambridge_University_Press). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-88068-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-88068-8).
- Richey, Matthew (May 2010). ["The Evolution of Markov Chain Monte Carlo Methods"](http://stat.wharton.upenn.edu/~stjensen/stat542/lecture14.mcmchistory.pdf) (PDF). *[The American Mathematical Monthly](https://en.wikipedia.org/wiki/The_American_Mathematical_Monthly)*. **117** (5): 383–413. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.295.4478](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.295.4478). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.4169/000298910x485923](https://doi.org/10.4169%2F000298910x485923). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [13630404](https://api.semanticscholar.org/CorpusID:13630404).
