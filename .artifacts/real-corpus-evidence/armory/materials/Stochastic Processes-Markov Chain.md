[[stochastic-processes.base]]

> Source: [[Markov Chain]]
> License: Wikipedia content is available under CC BY-SA 4.0.

![[media/9ded2147aa67738cdf74c1f1da32b5ae40b84757.png]]
A diagram representing a two-state Markov process. The numbers are the probability of changing from one state to another state.

In probability theory and statistics, a **Markov chain** or **Markov process** is a [stochastic process](https://en.wikipedia.org/wiki/Stochastic_process) describing a [sequence](https://en.wikipedia.org/wiki/Sequence) of possible events in which the [probability](https://en.wikipedia.org/wiki/Probability) of each event depends only on the state attained in the previous event. Informally, this may be thought of as, "What happens next depends only on the state of affairs *now*." A [countably infinite](https://en.wikipedia.org/wiki/Countably_infinite) sequence, in which the chain moves state at discrete time steps, gives a [discrete-time Markov chain](https://en.wikipedia.org/wiki/Discrete-time_Markov_chain) (DTMC). A [continuous-time](https://en.wikipedia.org/wiki/Continuous-time) process is called a [continuous-time Markov chain](https://en.wikipedia.org/wiki/Continuous-time_Markov_chain) (CTMC). Markov processes are named in honor of the [Russian](https://en.wikipedia.org/wiki/Russia) mathematician [Andrey Markov](https://en.wikipedia.org/wiki/Andrey_Markov).

Markov chains have many applications as [statistical models](https://en.wikipedia.org/wiki/Statistical_model) of real-world processes. They provide the basis for general stochastic simulation methods known as [[Markov Chain Monte Carlo]], which are used for simulating sampling from complex [probability distributions](https://en.wikipedia.org/wiki/Probability_distribution), and have found application in areas including [Bayesian statistics](https://en.wikipedia.org/wiki/Bayesian_statistics), [biology](https://en.wikipedia.org/wiki/Biology), [chemistry](https://en.wikipedia.org/wiki/Chemistry), [economics](https://en.wikipedia.org/wiki/Economics), [finance](https://en.wikipedia.org/wiki/Finance), [information theory](https://en.wikipedia.org/wiki/Information_theory), [physics](https://en.wikipedia.org/wiki/Physics), [signal processing](https://en.wikipedia.org/wiki/Signal_processing), and [speech processing](https://en.wikipedia.org/wiki/Speech_processing).

The adjectives *Markovian* and *Markov* are used to describe something that is related to a Markov process.

## Principles

![[media/9722f5b9f6a8b9db1c8606f2e007e44346c107be.jpg]]
Russian mathematician [Andrey Markov](https://en.wikipedia.org/wiki/Andrey_Markov)

### Definition

A Markov process is a [stochastic process](https://en.wikipedia.org/wiki/Stochastic_process) that satisfies the [Markov property](https://en.wikipedia.org/wiki/Markov_property) (sometimes characterized as "[memorylessness](https://en.wikipedia.org/wiki/Memorylessness)"). In simpler terms, it is a process for which predictions can be made regarding future outcomes based solely on its present state and—most importantly—such predictions are just as good as the ones that could be made knowing the process's full history. In other words, [conditional](https://en.wikipedia.org/wiki/Conditional_probability) on the present state of the system, its future and past states are [independent](https://en.wikipedia.org/wiki/Independence_(probability_theory) "Independence (probability theory)").

A Markov chain is a type of Markov process that has either a discrete [state space](https://en.wikipedia.org/wiki/State_space) or a discrete index set (often representing time), but the precise definition of a Markov chain varies. For example, it is common to define a Markov chain as a Markov process in either [discrete or continuous time](https://en.wikipedia.org/wiki/Continuous_or_discrete_variable) with a countable state space (thus regardless of the nature of time), but it is also common to define a Markov chain as having discrete time in either countable or continuous state space (thus regardless of the state space).

### Types of Markov chains

The system's [state space](https://en.wikipedia.org/wiki/State_space) and time parameter index need to be specified. The following table gives an overview of the different instances of Markov processes for different levels of state space generality for both discrete and continuous time:

|  |  |  |
|----|----|----|
|  | Countable state space | Continuous or general state space |
| Discrete-time | (discrete-time) Markov chain on a countable or finite state space | [Markov chain on a measurable state space](https://en.wikipedia.org/wiki/Markov_chains_on_a_measurable_state_space) (for example, [Harris chain](https://en.wikipedia.org/wiki/Harris_chain)) |
| Continuous-time | Continuous-time Markov process or Markov jump process | Any [continuous stochastic process](https://en.wikipedia.org/wiki/Continuous_stochastic_process) with the Markov property (for example, the [Wiener process](https://en.wikipedia.org/wiki/Wiener_process)) |

Note that there is no definitive agreement in the literature on the use of some of the terms that signify special cases of Markov processes. Usually the term "Markov chain" is reserved for a process with a discrete set of times, that is, a **discrete-time Markov chain (DTMC)**, but a few authors use the term "Markov process" to refer to a **continuous-time Markov chain (CTMC)** without explicit mention. In addition, there are other extensions of Markov processes that are referred to as such but do not necessarily fall within any of these four categories (see [Markov model](https://en.wikipedia.org/wiki/Markov_model)). Moreover, the time index need not necessarily be real-valued; like with the state space, there are conceivable processes that move through index sets with other mathematical constructs. Notice that the general state space continuous-time Markov chain is general to such a degree that it has no designated term.

While the time parameter is usually discrete, the [state space](https://en.wikipedia.org/wiki/State_space) of a Markov chain does not have any generally agreed-on restrictions: the term may refer to a process on an arbitrary state space. However, many applications of Markov chains employ finite or [countably infinite](https://en.wikipedia.org/wiki/Countable_set) state spaces, which have a more straightforward statistical analysis. Besides time-index and state-space parameters, there are many other variations, extensions and generalizations (see [Variations](#Variations)). For simplicity, most of this article concentrates on the discrete-time, discrete state-space case, unless mentioned otherwise.

### Transitions

The changes of state of the system are called transitions. The probabilities associated with various state changes are called transition probabilities. The process is characterized by a state space, a [transition matrix](https://en.wikipedia.org/wiki/Stochastic_matrix) describing the probabilities of particular transitions, and an initial state (or initial distribution) across the state space. By convention, we assume all possible states and transitions have been included in the definition of the process, so there is always a next state, and the process does not terminate.

A discrete-time random process involves a system which is in a certain state at each step, with the state changing randomly between steps. The steps are often thought of as moments in time, but they can equally well refer to physical distance or any other discrete measurement. Formally, the steps are the [integers](https://en.wikipedia.org/wiki/Integers) or [natural numbers](https://en.wikipedia.org/wiki/Natural_numbers), and the random process is a mapping of these to states. The Markov property states that the [conditional probability distribution](https://en.wikipedia.org/wiki/Conditional_probability_distribution) for the system at the next step (and in fact at all future steps) depends only on the current state of the system, and not additionally on the state of the system at previous steps.

Since the system changes randomly, it is generally impossible to predict with certainty the state of a Markov chain at a given point in the future. However, the statistical properties of the system's future can be predicted. In many applications, it is these statistical properties that are important.

## History

[Andrey Markov](https://en.wikipedia.org/wiki/Andrey_Markov) studied Markov processes in the early 20th century, publishing his first paper on the topic in 1906. Markov processes in continuous time were discovered long before his work in the early 20th century in the form of the [Poisson process](https://en.wikipedia.org/wiki/Poisson_point_process). Markov was interested in studying an extension of independent random sequences, motivated by a disagreement with [Pavel Nekrasov](https://en.wikipedia.org/wiki/Pavel_Nekrasov) who claimed independence was necessary for the [weak law of large numbers](https://en.wikipedia.org/wiki/Weak_law_of_large_numbers) to hold. In his first paper on Markov chains, published in 1906, Markov showed that under certain conditions the average outcomes of the Markov chain would converge to a fixed vector of values, so proving a weak law of large numbers without the independence assumption, which had been commonly regarded as a requirement for such mathematical laws to hold. Markov later used Markov chains to study the distribution of vowels in [Eugene Onegin](https://en.wikipedia.org/wiki/Eugene_Onegin), written by [Alexander Pushkin](https://en.wikipedia.org/wiki/Alexander_Pushkin), and proved a [central limit theorem](https://en.wikipedia.org/wiki/Markov_chain_central_limit_theorem) for such chains.

In 1912 [Henri Poincaré](https://en.wikipedia.org/wiki/Henri_Poincar%C3%A9) studied Markov chains on [finite groups](https://en.wikipedia.org/wiki/Finite_group) with an aim to study card shuffling. Other early uses of Markov chains include a diffusion model, introduced by [Paul](https://en.wikipedia.org/wiki/Paul_Ehrenfest) and [Tatyana Ehrenfest](https://en.wikipedia.org/wiki/Tatyana_Ehrenfest) in 1907, and a branching process, introduced by [Francis Galton](https://en.wikipedia.org/wiki/Francis_Galton) and [Henry William Watson](https://en.wikipedia.org/wiki/Henry_William_Watson) in 1873, preceding the work of Markov. After the work of Galton and Watson, it was later revealed that their branching process had been independently discovered and studied around three decades earlier by [Irénée-Jules Bienaymé](https://en.wikipedia.org/wiki/Ir%C3%A9n%C3%A9e-Jules_Bienaym%C3%A9). Starting in 1928, [Maurice Fréchet](https://en.wikipedia.org/wiki/Maurice_Fr%C3%A9chet) became interested in Markov chains, eventually resulting in him publishing in 1938 a detailed study on Markov chains.

[Andrey Kolmogorov](https://en.wikipedia.org/wiki/Andrei_Kolmogorov) developed in a 1931 paper a large part of the early theory of continuous-time Markov processes. Kolmogorov was partly inspired by Louis Bachelier's 1900 work on fluctuations in the stock market as well as [Norbert Wiener](https://en.wikipedia.org/wiki/Norbert_Wiener)'s work on Einstein's model of Brownian movement. He introduced and studied a particular set of Markov processes known as diffusion processes, where he derived a set of differential equations describing the processes. Independent of Kolmogorov's work, [Sydney Chapman](https://en.wikipedia.org/wiki/Sydney_Chapman_(mathematician) "Sydney Chapman (mathematician)") derived in a 1928 paper an equation, now called the [Chapman–Kolmogorov equation](https://en.wikipedia.org/wiki/Chapman%E2%80%93Kolmogorov_equation), in a less mathematically rigorous way than Kolmogorov, while studying Brownian movement. The differential equations are now called the Kolmogorov equations or the Kolmogorov–Chapman equations. Other mathematicians who contributed significantly to the foundations of Markov processes include [William Feller](https://en.wikipedia.org/wiki/William_Feller), starting in 1930s, and then later [Eugene Dynkin](https://en.wikipedia.org/wiki/Eugene_Dynkin), starting in the 1950s.

## Examples

- [Mark V. Shaney](https://en.wikipedia.org/wiki/Mark_V._Shaney) is a third-order Markov chain program, and a [Markov text](https://en.wikipedia.org/wiki/Markov_text) generator. It ingests the sample text (the [Tao Te Ching](https://en.wikipedia.org/wiki/Tao_Te_Ching), or the posts of a [Usenet](https://en.wikipedia.org/wiki/Usenet) group) and creates a massive list of every sequence of three successive words (triplet) which occurs in the text. It then chooses two words at random, and looks for a word which follows those two in one of the triplets in its massive list. If there is more than one, it picks at random (identical triplets count separately, so a sequence which occurs twice is twice as likely to be picked as one which only occurs once). It then adds that word to the generated text. Then, in the same way, it picks a triplet that starts with the second and third words in the generated text, and that gives a fourth word. It adds the fourth word, then repeats with the third and fourth words, and so on.

- [Random walks](https://en.wikipedia.org/wiki/Random_walk) based on integers and the [gambler's ruin](https://en.wikipedia.org/wiki/Gambler%27s_ruin) problem are examples of Markov processes. Some variations of these processes were studied hundreds of years earlier in the context of independent variables. Two important examples of Markov processes are the [Wiener process](https://en.wikipedia.org/wiki/Wiener_process), also known as the [[Brownian Motion]] process, and the [[Poisson Process]], which are considered the most important and central stochastic processes in the theory of stochastic processes. These two processes are Markov processes in continuous time, while random walks on the integers and the gambler's ruin problem are examples of Markov processes in discrete time.
- A famous Markov chain is the so-called "drunkard's walk", a random walk on the [number line](https://en.wikipedia.org/wiki/Number_line) where, at each step, the position may change by +1 or −1 with equal probability. From any position there are two possible transitions, to the next or previous integer. The transition probabilities depend only on the current position, not on the manner in which the position was reached. For example, the transition probabilities from 5 to 4 and 5 to 6 are both 0.5, and all other transition probabilities from 5 are 0. These probabilities are independent of whether the system was previously in 4 or 6.
- A series of independent states (for example, a series of coin flips) satisfies the formal definition of a Markov chain. However, the theory is usually applied only when the probability distribution of the next state depends on the current one.

### A non-Markov example

Suppose that there is a coin purse containing five coins worth 25¢ (quarters), five coins worth 10¢ (dimes) and five coins worth 5¢ (nickels). One by one, coins are randomly drawn from the purse and are set on a table. If $X_{n}$ represents the total value of the coins set on the table after n draws, with $X_{0}=0$, then the sequence $\{X_{n}:n\in \mathbb {N} \}$ is *not* a Markov process.

To see why this is the case, suppose that in the first six draws, all five nickels and a quarter are drawn. Thus $X_{6}=\$0.50$. If we know not just $X_{6}$, but the earlier values as well, then we can determine which coins have been drawn, and we know that the next coin will not be a nickel; so we can determine that $X_{7}\geq \$0.60$ with probability 1. But if we do not know the earlier values, then based only on the value $X_{6}$ we might guess that we had drawn four dimes and two nickels, in which case it would certainly be possible to draw another nickel next. Thus, our guesses about $X_{7}$ are impacted by our knowledge of values prior to $X_{6}$.

However, it is possible to model this scenario as a Markov process. Instead of defining $X_{n}$ to represent the *total value* of the coins on the table, we could define $X_{n}$ to represent the *count* of the various coin types on the table. For instance, $X_{6}=1,0,5$ could be defined to represent the state where there is one quarter, zero dimes, and five nickels on the table after 6 one-by-one draws. This new model could be represented by $6\times 6\times 6=216$ possible states, where each state represents the number of coins of each type (from 0 to 5) that are on the table. (Not all of these states are reachable within 6 draws.)

Suppose that the first draw results in state $X_{1}=0,1,0$. The probability of achieving $X_{2}$ now depends on $X_{1}$; for example, the state $X_{2}=1,0,1$ is not possible. After the second draw, the third draw depends on which coins have so far been drawn, but no longer only on the coins that were drawn for the first state (since probabilistically important information has since been added to the scenario). In this way, the likelihood of the $X_{n}=i,j,k$ state depends exclusively on the outcome of the $X_{n-1}=\ell ,m,p$ state.

## Formal definition

### Discrete-time Markov chain

A discrete-time Markov chain is a sequence of [random variables](https://en.wikipedia.org/wiki/Random_variable) *X*<sub>1</sub>, *X*<sub>2</sub>, *X*<sub>3</sub>, ... with the [Markov property](https://en.wikipedia.org/wiki/Markov_property), namely that the probability of moving to the next state depends only on the present state and not on the previous states:

$\Pr(X_{n+1}=x\mid X_{1}=x_{1},X_{2}=x_{2},\ldots ,X_{n}=x_{n})=\Pr(X_{n+1}=x\mid X_{n}=x_{n}),$ if both [conditional probabilities](https://en.wikipedia.org/wiki/Conditional_probability) are well defined, that is, if $\Pr(X_{1}=x_{1},\ldots ,X_{n}=x_{n})>0.$

The possible values of *X*<sub>*i*</sub> form a [countable set](https://en.wikipedia.org/wiki/Countable_set) *S* called the state space of the chain.

#### Variations

- Time-homogeneous Markov chains are processes where 

$$
\Pr(X_{n+1}=x\mid X_{n}=y)=\Pr(X_{n}=x\mid X_{n-1}=y)
$$

 for all *n*. The probability of the transition is independent of *n*.
- Stationary Markov chains are processes where 

$$
\Pr(X_{0}=x_{0},X_{1}=x_{1},\ldots ,X_{k}=x_{k})=\Pr(X_{n}=x_{0},X_{n+1}=x_{1},\ldots ,X_{n+k}=x_{k})
$$

 for all *n* and *k*. Every stationary chain can be proved to be time-homogeneous by Bayes' rule.

  A necessary and sufficient condition for a time-homogeneous Markov chain to be stationary is that the distribution of $X_{0}$ is a stationary distribution of the Markov chain.
- A Markov chain with memory (or a Markov chain of order *m*) where *m* is finite, is a process satisfying 

$$
{\begin{aligned}{}&\Pr(X_{n}=x_{n}\mid X_{n-1}=x_{n-1},X_{n-2}=x_{n-2},\dots ,X_{1}=x_{1})\\=&\Pr(X_{n}=x_{n}\mid X_{n-1}=x_{n-1},X_{n-2}=x_{n-2},\dots ,X_{n-m}=x_{n-m}){\text{ for }}n>m\end{aligned}}
$$

 In other words, the future state depends on the past *m* states. It is possible to construct a chain $(Y_{n})$ from $(X_{n})$ which has the 'classical' Markov property by taking as state space the ordered *m*-tuples of *X* values, i.e., $Y_{n}=\left(X_{n},X_{n-1},\ldots ,X_{n-m+1}\right)$.

### Finite state space

If the state space is [finite](https://en.wikipedia.org/wiki/Finite_set), the transition probability distribution can be represented by a [matrix](https://en.wikipedia.org/wiki/Matrix_(mathematics) "Matrix (mathematics)"), called the transition matrix, with the (*i*, *j*)th [element](https://en.wikipedia.org/wiki/Element_(mathematics)) of **P** equal to

$p_{ij}=\Pr(X_{n+1}=j\mid X_{n}=i).$

Since each row of **P** sums to one and all elements are non-negative, **P** is a [right stochastic matrix](https://en.wikipedia.org/wiki/Right_stochastic_matrix).

#### Stationary distribution relation to eigenvectors and simplices

A stationary distribution π is a (row) vector, whose entries are non-negative and sum to 1, is unchanged by the operation of transition matrix **P** on it and so is defined by

$\pi \mathbf {P} =\pi .$

By comparing this definition with that of an [eigenvector](https://en.wikipedia.org/wiki/Eigenvector) we see that the two concepts are related and that

$\pi ={\frac {e}{\sum _{i}{e_{i}}}}$

is a normalized ($\sum _{i}\pi _{i}=1$) multiple of a left eigenvector **e** of the transition matrix **P** with an [eigenvalue](https://en.wikipedia.org/wiki/Eigenvalue) of 1. If there is more than one unit eigenvector then a weighted sum of the corresponding stationary states is also a stationary state. But for a Markov chain one is usually more interested in a stationary state that is the limit of the sequence of distributions for some initial distribution.

The values of a stationary distribution $\textstyle \pi _{i}$ are associated with the state space of **P** and its eigenvectors have their relative proportions preserved. Since the components of π are positive and the constraint that their sum is unity can be rewritten as $\sum _{i}1\cdot \pi _{i}=1$ we see that the [dot product](https://en.wikipedia.org/wiki/Dot_product) of π with a vector whose components are all 1 is unity and that π lies on a [simplex](https://en.wikipedia.org/wiki/Standard_simplex).

#### Time-homogeneous Markov chain with a finite state space

If the Markov chain is time-homogeneous, then the transition matrix **P** is the same after each step, so the *k*-step transition probability can be computed as the *k*-th power of the transition matrix, **P**<sup>*k*</sup>.

If the Markov chain is irreducible and aperiodic, then there is a unique stationary distribution π. Additionally, in this case **P**<sup>*k*</sup> converges to a rank-one matrix in which each row is the stationary distribution π:

$\lim _{k\to \infty }\mathbf {P} ^{k}=\mathbf {1} \pi$

where **1** is the column vector with all entries equal to 1. This is stated by the [Perron–Frobenius theorem](https://en.wikipedia.org/wiki/Perron%E2%80%93Frobenius_theorem). If, by whatever means, $\lim _{k\to \infty }\mathbf {P} ^{k}$ is found, then the stationary distribution of the Markov chain in question can be easily determined for any starting distribution, as will be explained below.

For some stochastic matrices **P**, the limit $\lim _{k\to \infty }\mathbf {P} ^{k}$ does not exist while the stationary distribution does, as shown by this example:

$\mathbf {P} ={\begin{pmatrix}0&1\\1&0\end{pmatrix}}\qquad \mathbf {P} ^{2k}=I\qquad \mathbf {P} ^{2k+1}=\mathbf {P}$

${\begin{pmatrix}{\frac {1}{2}}&{\frac {1}{2}}\end{pmatrix}}{\begin{pmatrix}0&1\\1&0\end{pmatrix}}={\begin{pmatrix}{\frac {1}{2}}&{\frac {1}{2}}\end{pmatrix}}$

(This example illustrates a periodic Markov chain.)

Because there are a number of different special cases to consider, the process of finding this limit if it exists can be a lengthy task. However, there are many techniques that can assist in finding this limit. Let **P** be an *n*×*n* matrix, and define $\mathbf {Q} =\lim _{k\to \infty }\mathbf {P} ^{k}.$

It is always true that

$\mathbf {QP} =\mathbf {Q} .$

Subtracting **Q** from both sides and factoring then yields

$\mathbf {Q} (\mathbf {P} -\mathbf {I} _{n})=\mathbf {0} _{n,n},$

where **I**<sub>*n*</sub> is the [identity matrix](https://en.wikipedia.org/wiki/Identity_matrix) of size *n*, and **0**<sub>*n*,*n*</sub> is the [zero matrix](https://en.wikipedia.org/wiki/Zero_matrix) of size *n*×*n*. Multiplying together stochastic matrices always yields another stochastic matrix, so **Q** must be a [stochastic matrix](https://en.wikipedia.org/wiki/Stochastic_matrix) (see the definition above). It is sometimes sufficient to use the matrix equation above and the fact that **Q** is a stochastic matrix to solve for **Q**. Including the fact that the sum of each the rows in **P** is 1, there are *n+1* equations for determining *n* unknowns, so it is computationally easier if on the one hand one selects one row in **Q** and substitutes each of its elements by one, and on the other one substitutes the corresponding element (the one in the same column) in the vector **0**, and next left-multiplies this latter vector by the inverse of transformed former matrix to find **Q**.

Here is one method for doing so: first, define the function *f*(**A**) to return the matrix **A** with its right-most column replaced with all 1's. If \[*f*(**P** − **I**<sub>*n*</sub>)\]<sup>−1</sup> exists then

$\mathbf {Q} =f(\mathbf {0} _{n,n})[f(\mathbf {P} -\mathbf {I} _{n})]^{-1}.$

Explain: The original matrix equation is equivalent to a [system of n×n linear equations](https://en.wikipedia.org/wiki/System_of_linear_equations) in *n*×*n* variables. And there are *n* more linear equations from the fact that **Q** is a right [stochastic matrix](https://en.wikipedia.org/wiki/Stochastic_matrix) whose each row sums to 1. So it needs any *n*×*n* independent linear equations of the (*n*×*n*+*n*) equations to solve for the *n*×*n* variables. In this example, the *n* equations from "**Q** multiplied by the right-most column of (**P**-**I**<sub>*n*</sub>)" have been replaced by the *n* stochastic ones.

One thing to notice is that if **P** has an element **P**<sub>*i*,*i*</sub> on its main diagonal that is equal to 1 and the *i*th row or column is otherwise filled with 0's, then that row or column will remain unchanged in all of the subsequent powers **P**<sup>*k*</sup>. Hence, the *i*th row or column of **Q** will have the 1 and the 0's in the same positions as in **P**.

#### Convergence speed to the stationary distribution

As stated earlier, from the equation ${\boldsymbol {\pi }}={\boldsymbol {\pi }}\mathbf {P} ,$ (if exists) the stationary (or steady state) distribution **π** is a left eigenvector of row [stochastic matrix](https://en.wikipedia.org/wiki/Stochastic_matrix) **P**. Then assuming that **P** is diagonalizable or equivalently that **P** has *n* linearly independent eigenvectors, speed of convergence is elaborated as follows. (For non-diagonalizable, that is, [defective matrices](https://en.wikipedia.org/wiki/Defective_matrix), one may start with the [Jordan normal form](https://en.wikipedia.org/wiki/Jordan_normal_form) of **P** and proceed with a bit more involved set of arguments in a similar way.)

Let **U** be the matrix of eigenvectors (each normalized to having an L2 norm equal to 1) where each column is a left eigenvector of **P** and let **Σ** be the diagonal matrix of left eigenvalues of **P**, that is, **Σ** = diag(*λ*<sub>1</sub>,*λ*<sub>2</sub>,*λ*<sub>3</sub>,...,*λ*<sub>*n*</sub>). Then by [[Eigendecomposition]]

$\mathbf {P} =\mathbf {U\Sigma U} ^{-1}.$

Let the eigenvalues be enumerated such that:

$1=|\lambda _{1}|>|\lambda _{2}|\geq |\lambda _{3}|\geq \cdots \geq |\lambda _{n}|.$

Since **P** is a row stochastic matrix, its largest left eigenvalue is 1. If there is a unique stationary distribution, then the largest eigenvalue and the corresponding eigenvector is unique too (because there is no other **π** which solves the stationary distribution equation above). Let **u**<sub>*i*</sub> be the *i*-th column of **U** matrix, that is, **u**<sub>*i*</sub> is the left eigenvector of **P** corresponding to λ<sub>*i*</sub>. Also let **x** be a length *n* row vector that represents a valid probability distribution; since the eigenvectors **u**<sub>*i*</sub> span $\mathbb {R} ^{n},$ we can write

$\mathbf {x} ^{\mathsf {T}}=\sum _{i=1}^{n}a_{i}\mathbf {u} _{i},\qquad a_{i}\in \mathbb {R} .$

If we multiply **x** with **P** from right and continue this operation with the results, in the end we get the stationary distribution **π**. In other words, **π** = **a**<sub>1</sub> **u**<sub>1</sub> ← **xPP**...**P** = **xP**<sup>*k*</sup> as *k* → ∞. That means

${\begin{aligned}{\boldsymbol {\pi }}^{(k)}&=\mathbf {x} \left(\mathbf {U\Sigma U} ^{-1}\right)\left(\mathbf {U\Sigma U} ^{-1}\right)\cdots \left(\mathbf {U\Sigma U} ^{-1}\right)\\&=\mathbf {xU\Sigma } ^{k}\mathbf {U} ^{-1}\\&=\left(a_{1}\mathbf {u} _{1}^{\mathsf {T}}+a_{2}\mathbf {u} _{2}^{\mathsf {T}}+\cdots +a_{n}\mathbf {u} _{n}^{\mathsf {T}}\right)\mathbf {U\Sigma } ^{k}\mathbf {U} ^{-1}\\&=a_{1}\lambda _{1}^{k}\mathbf {u} _{1}^{\mathsf {T}}+a_{2}\lambda _{2}^{k}\mathbf {u} _{2}^{\mathsf {T}}+\cdots +a_{n}\lambda _{n}^{k}\mathbf {u} _{n}^{\mathsf {T}}&&u_{i}\bot u_{j}{\text{ for }}i\neq j\\&=\lambda _{1}^{k}\left\{a_{1}\mathbf {u} _{1}^{\mathsf {T}}+a_{2}\left({\frac {\lambda _{2}}{\lambda _{1}}}\right)^{k}\mathbf {u} _{2}^{\mathsf {T}}+a_{3}\left({\frac {\lambda _{3}}{\lambda _{1}}}\right)^{k}\mathbf {u} _{3}^{\mathsf {T}}+\cdots +a_{n}\left({\frac {\lambda _{n}}{\lambda _{1}}}\right)^{k}\mathbf {u} _{n}^{\mathsf {T}}\right\}\end{aligned}}$

Since **π** is parallel to **u**<sub>1</sub>(normalized by L2 norm) and **π**<sup>(*k*)</sup> is a probability vector, **π**<sup>(*k*)</sup> approaches to **a**<sub>1</sub> **u**<sub>1</sub> = **π** as *k* → ∞ with a speed in the order of *λ*<sub>2</sub>/*λ*<sub>1</sub> exponentially. This follows because $|\lambda _{2}|\geq \cdots \geq |\lambda _{n}|,$ hence *λ*<sub>2</sub>/*λ*<sub>1</sub> is the dominant term. The smaller the ratio is, the faster the convergence is. Random noise in the state distribution **π** can also speed up this convergence to the stationary distribution.

### Continuous-time Markov chain

A continuous-time Markov chain $(X_{t})_{t\geq 0}$ is defined by a finite or countable state space *S*, a [transition rate matrix](https://en.wikipedia.org/wiki/Transition_rate_matrix) *Q* with dimensions equal to that of the state space and initial probability distribution defined on the state space. For *i* ≠ *j*, the elements *q*<sub>*ij*</sub> are non-negative and describe the rate of the process transitions from state *i* to state *j*. The elements *q*<sub>*ii*</sub> are chosen such that each row of the transition rate matrix sums to zero, while the row-sums of a probability transition matrix in a (discrete) Markov chain are all equal to one.

There are three equivalent definitions of the process.

#### Infinitesimal definition

![[media/9a6be816712e28f47c4712bb59727c5257653368.png]]
The continuous time Markov chain is characterized by the transition rates, the derivatives with respect to time of the transition probabilities between states i and j.

Let $X_{t}$ be the random variable describing the state of the process at time *t*, and assume the process is in a state *i* at time *t*. Then, knowing $X_{t}=i$, $X_{t+h}=j$ is independent of previous values $\left(X_{s}:s<t\right)$, and as *h* → 0 for all *j* and for all *t*, 

$$
\Pr(X(t+h)=j\mid X(t)=i)=\delta _{ij}+q_{ij}h+o(h),
$$

 where $\delta _{ij}$ is the [Kronecker delta](https://en.wikipedia.org/wiki/Kronecker_delta), using the [little-o notation](https://en.wikipedia.org/wiki/Little-o_notation). The $q_{ij}$ can be seen as measuring how quickly the transition from *i* to *j* happens.

#### Jump chain/holding time definition

Define a discrete-time Markov chain *Y*<sub>*n*</sub> to describe the *n*th jump of the process and variables *S*<sub>1</sub>, *S*<sub>2</sub>, *S*<sub>3</sub>, ... to describe holding times in each of the states where *S*<sub>*i*</sub> follows the [exponential distribution](https://en.wikipedia.org/wiki/Exponential_distribution) with rate parameter −*q*<sub>*Y*<sub>*i*</sub>*Y*<sub>*i*</sub></sub>.

#### Transition probability definition

For any value *n* = 0, 1, 2, 3, ... and times indexed up to this value of *n*: *t*<sub>0</sub>, *t*<sub>1</sub>, *t*<sub>2</sub>, ... and all states recorded at these times *i*<sub>0</sub>, *i*<sub>1</sub>, *i*<sub>2</sub>, *i*<sub>3</sub>, ... it holds that

$\Pr(X_{t_{n+1}}=i_{n+1}\mid X_{t_{0}}=i_{0},X_{t_{1}}=i_{1},\ldots ,X_{t_{n}}=i_{n})=p_{i_{n}i_{n+1}}(t_{n+1}-t_{n})$

where *p*<sub>*ij*</sub> is the solution of the [forward equation](https://en.wikipedia.org/wiki/Forward_equation) (a [first-order differential equation](https://en.wikipedia.org/wiki/First-order_differential_equation))

$P'(t)=P(t)Q$

with initial condition P(0) is the [identity matrix](https://en.wikipedia.org/wiki/Identity_matrix).

#### Locally interacting Markov chains

"Locally interacting Markov chains" are Markov chains with an evolution that takes into account the state of other Markov chains. This corresponds to the situation when the state space has a (Cartesian-) product form. See [interacting particle system](https://en.wikipedia.org/wiki/Interacting_particle_system) and [stochastic cellular automata](https://en.wikipedia.org/wiki/Stochastic_cellular_automata) (probabilistic cellular automata). See for instance *Interaction of Markov Processes* or.

### Discrete-time Markov process with general state space

#### Harris chains

Many results for discrete-time Markov chains with finite state space can be generalized to chains with uncountable state space through [Harris chains](https://en.wikipedia.org/wiki/Harris_chain).

The use of Markov chains in [[Markov Chain Monte Carlo]] methods covers cases where the process follows a continuous state space.

### Continuous-time Markov process with general state space

The definition of Markov processes in continuous time with general state space is more technical than the above.

A continuous-time Markov process $X=(X_{t})_{t\geq 0}$ is a [stochastic process](https://en.wikipedia.org/wiki/Stochastic_process) adapted to a [filtration](https://en.wikipedia.org/wiki/Filtration_(probability_theory) "Filtration (probability theory)") $\mathbb {F} =({\mathcal {F}}_{t})_{t\geq 0}$ with values in a [locally compact](https://en.wikipedia.org/wiki/Locally_compact_space) [Polish space](https://en.wikipedia.org/wiki/Polish_space) $(S,{\mathcal {B}}(S))$ (e.g., $(\mathbb {R} ,{\mathcal {B}}(\mathbb {R} ))$). The latter essentially ensures that the conditional expectations of $X_{t}$ are [regular](https://en.wikipedia.org/wiki/Regular_conditional_probability), which, in simple terms, means that they behave "nicely". Then $X$ is called a *Markov process*, if it satisfies the [Markov property](https://en.wikipedia.org/wiki/Markov_property), i.e., for all $t\geq s\geq 0$ and $A\in {\mathcal {B}}(S)$

$P(X_{t}\in A\mid {\mathcal {F}}_{s})=P(X_{t}\in A\mid X_{s})$.

Moreover, $X$ is called *time-homogeneous*, if it satisfies the weak Markov property for all $t,s\geq 0$:

$P(X_{t+s}\in A\mid {\mathcal {F}}_{s})=P(X_{t}\in A\mid X_{0}=x)|_{x=X_{s}}=:P_{t}(X_{s},A)$.

The function $(t,x,A)\mapsto P_{t}(x,A)$ is the so-called *transition function* of $X$ and $(P_{t})_{t\geq 0}$ the *transition semigroup* of the process. Transition functions are generalizations of the transition matrices used in the setting with finite state space.

In a more abstract way, Markov processes can also be defined or constructed the other way around: Let $(P_{t})_{t\geq 0}$ be a transition semigroup, i.e.,

1.  $P_{t}$ is [Markov kernel](https://en.wikipedia.org/wiki/Markov_kernel) for all $t\geq 0$,
2.  $P_{t+s}(x,A)=\int _{S}P_{t}(y,A)P_{s}(x,dy)\quad \forall t,s\geq 0,x\in \mathbb {R} ,A\in {\mathcal {B}}(S)$ (Chapman-Kolmogorov-equation),
3.  $P_{0}(x,\cdot )=\delta _{x}$,

where $\delta _{x}$ is the [Dirac-measure](https://en.wikipedia.org/wiki/Dirac_measure) in $x$, and $X:\Omega \times [0,\infty )\to S$. Then $X$ is a homogeneous Markov process w.r.t. the natural filtration $\mathbb {F} ^{X}=(\sigma (X_{s}:0\leq s\leq t))_{t\geq 0}$, if for all $0\leq t_{1}<...<t_{n}$, $A_{1},...,A_{n}\in {\mathcal {B}}(S)$ the underlying probability measure $P$ satisfies

$P(X_{t_{1}}\in A_{1},...,X_{t_{n}}\in A_{n}\mid X_{0}=x)=\int _{A_{1}}...\int _{A_{n-1}}P_{t_{n}-t_{n-1}}(x_{n-1},A_{n})\cdots P_{t_{1}}(x,dx_{1})$.

Or, if no probability measure $P$ has been specified, the above equation defines a measure $P^{x}:=P(\cdot \mid X_{0}=x)$ on $\sigma (X_{s}:s\geq 0)$ under which the process $X$ started in $x$ is a Markov process by construction.

In other words, Markov processes can be defined either as stochastic processes $X$ on a filtered probability space, or indirectly in terms of a transition semigroup (i.e., the transition probabilities of the process), which induces a probability space under which $X$ has the Markov property.

## Properties

Two states are said to *communicate* with each other if both are reachable from one another by a sequence of transitions that have positive probability. This is an equivalence relation which yields a set of communicating classes. A class is *closed* if the probability of leaving the class is zero. A Markov chain is *irreducible* if there is one communicating class, the state space.

A state *i* has period *k* if *k* is the [greatest common divisor](https://en.wikipedia.org/wiki/Greatest_common_divisor) of the number of transitions by which *i* can be reached, starting from *i*. That is:

$k=\gcd\{n>0:\Pr(X_{n}=i\mid X_{0}=i)>0\}$

The state is *periodic* if $k>1$; otherwise $k=1$ and the state is *aperiodic*.

A state *i* is said to be *transient* if, starting from *i*, there is a non-zero probability that the chain will never return to *i*. It is called *recurrent* (or *persistent*) otherwise. For a recurrent state *i*, the mean *hitting time* is defined as:

$M_{i}=E[T_{i}]=\sum _{n=1}^{\infty }n\cdot f_{ii}^{(n)}$ where $f_{ii}^{(n)}:=\Pr(\min\{m>0:X_{m}=i\}=n\mid X_{0}=i)$.

State *i* is *positive recurrent* if $M_{i}$ is finite and *null recurrent* otherwise. Periodicity, transience, recurrence and positive and null recurrence are class properties — that is, if one state has the property then all states in its communicating class have the property.

A state *i* is called *absorbing* if there are no outgoing transitions from the state.

### Irreducibility

Since periodicity is a class property, if a Markov chain is irreducible, then all its states have the same period. In particular, if one state is aperiodic, then the whole Markov chain is aperiodic.

If a finite Markov chain is irreducible, then all states are positive recurrent, and it has a unique stationary distribution given by $\pi _{i}=1/E[T_{i}]$.

### Ergodicity

A state *i* is said to be *ergodic* if it is aperiodic and positive recurrent. In other words, a state *i* is ergodic if it is recurrent, has a period of 1, and has finite mean recurrence time.

If all states in an irreducible Markov chain are ergodic, then the chain is said to be ergodic. Equivalently, there exists some integer $k$ such that all entries of $M^{k}$ are positive.

It can be shown that a finite state irreducible Markov chain is ergodic if it has an aperiodic state.

A Markov chain with more than one state and just one out-going transition per state is either not irreducible or not aperiodic, hence cannot be ergodic.

#### Terminology

Some authors call any irreducible, positive recurrent Markov chains ergodic, even periodic ones. In fact, merely irreducible Markov chains correspond to [ergodic processes](https://en.wikipedia.org/wiki/Ergodicity), defined according to [ergodic theory](https://en.wikipedia.org/wiki/Ergodic_theory).

Some authors call a matrix *primitive* if there exists some integer $k$ such that all entries of $M^{k}$ are positive. Some authors call it *regular*.

#### Index of primitivity

The *index of primitivity*, or *exponent*, of a regular matrix, is the smallest $k$ such that all entries of $M^{k}$ are positive. The exponent is purely a graph-theoretic property, since it depends only on whether each entry of $M$ is zero or positive, and therefore can be found on a directed graph with $\mathrm {sign} (M)$ as its adjacency matrix.

There are several combinatorial results about the exponent when there are finitely many states. Let $n$ be the number of states, then

- The exponent is $\leq (n-1)^{2}+1$. The only case where it is an equality is when the graph of $M$ goes like $1\to 2\to \dots \to n\to 1{\text{ and }}2$.
- If $M$ has $k\geq 1$ diagonal entries, then its exponent is $\leq 2n-k-1$.
- If $\mathrm {sign} (M)$ is symmetric, then $M^{2}$ has positive diagonal entries, which by previous proposition means its exponent is $\leq 2n-2$.
- (Dulmage-Mendelsohn theorem) The exponent is $\leq n+s(n-2)$ where $s$ is the [girth of the graph](https://en.wikipedia.org/wiki/Girth_(graph_theory) "Girth (graph theory)"). It can be improved to $\leq (d+1)+s(d+1-2)$, where $d$ is the [diameter of the graph](https://en.wikipedia.org/wiki/Diameter_(graph_theory) "Diameter (graph theory)").

### Measure-preserving dynamical system

If a Markov chain has a stationary distribution, then it can be converted to a [measure-preserving dynamical system](https://en.wikipedia.org/wiki/Measure-preserving_dynamical_system): Let the probability space be $\Omega =\Sigma ^{\mathbb {N} }$, where $\Sigma$ is the set of all states for the Markov chain. Let the sigma-algebra on the probability space be generated by the cylinder sets. Let the probability measure be generated by the stationary distribution, and the Markov chain transition. Let $T:\Omega \to \Omega$ be the shift operator: $T(X_{0},X_{1},\dots )=(X_{1},\dots )$. Similarly we can construct such a dynamical system with $\Omega =\Sigma ^{\mathbb {Z} }$ instead.

Since *irreducible* Markov chains with finite state spaces have a unique stationary distribution, the above construction is unambiguous for irreducible Markov chains.

In [ergodic theory](https://en.wikipedia.org/wiki/Ergodic_theory), a measure-preserving dynamical system is called *ergodic* if any measurable subset $S$ such that $T^{-1}(S)=S$ implies $S=\emptyset$ or $\Omega$ (up to a null set).

The terminology is inconsistent. Given a Markov chain with a stationary distribution that is strictly positive on all states, the Markov chain is *irreducible* if its corresponding measure-preserving dynamical system is *ergodic*.

### Markovian representations

In some cases, apparently non-Markovian processes may still have Markovian representations, constructed by expanding the concept of the "current" and "future" states. For example, let *X* be a non-Markovian process. Then define a process *Y*, such that each state of *Y* represents a time-interval of states of *X*. Mathematically, this takes the form:

$Y(t)={\big \{}X(s):s\in [a(t),b(t)]\,{\big \}}.$

If *Y* has the Markov property, then it is a Markovian representation of *X*.

An example of a non-Markovian process with a Markovian representation is an [autoregressive](https://en.wikipedia.org/wiki/Autoregressive_model) [time series](https://en.wikipedia.org/wiki/Time_series) of order greater than one.

### Hitting times

The *hitting time* is the time, starting in a given set of states, until the chain arrives in a given state or set of states. The distribution of such a time period has a phase type distribution. The simplest such distribution is that of a single exponentially distributed transition.

#### Expected hitting times

For a subset of states *A* ⊆ *S*, the vector *k*<sup>*A*</sup> of hitting times (where element $k_{i}^{A}$ represents the [expected value](https://en.wikipedia.org/wiki/Expected_value), starting in state *i* that the chain enters one of the states in the set *A*) is the minimal non-negative solution to

${\begin{aligned}k_{i}^{A}=0&{\text{ for }}i\in A\\-\sum _{j\in S}q_{ij}k_{j}^{A}=1&{\text{ for }}i\notin A.\end{aligned}}$

### Time reversal

For a general Markov process $X$ in continuous time (a CTMC or a process with general state space), the reverse process ${\overleftarrow {X}}=(X_{T-t})_{t\in [0,T]}$ from a fixed time $T>0$ is again a Markov process. This follows directly from the [Markov property](https://en.wikipedia.org/wiki/Markov_property): Informally speaking, the future and the past are independent given the present. Under time-reversal, their roles are just interchanged. However, the reverse process is not time-homogeneous in general. If for some random time $\tau$ (not necessarily a [stopping time](https://en.wikipedia.org/wiki/Stopping_time)) the stopped process $X^{\tau }=(X_{t\land \tau })_{t\geq 0}$ is a time-homogeneous Markov process, then the reverse process ${\overleftarrow {X^{\tau }}}=(X_{\tau -t\land \tau }1_{\{\tau <\infty \}})_{t\geq 0}$ is again time-homogeneous.

If $X$ is a CTMC, then by [Kelly's lemma](https://en.wikipedia.org/wiki/Kelly%27s_lemma) ${\overleftarrow {X}}$ has the same stationary distribution as the forward process.

A chain is said to be *reversible* if the reversed process is the same as the forward process (in distribution). [Kolmogorov's criterion](https://en.wikipedia.org/wiki/Kolmogorov%27s_criterion) states that the necessary and sufficient condition for a Markov chain to be reversible is that the product of transition rates around a closed loop must be the same in both directions.

### Embedded Markov chain

One method of finding the [stationary probability distribution](https://en.wikipedia.org/wiki/Stationary_probability_distribution), π, of an [ergodic](https://en.wikipedia.org/wiki/Ergodic) continuous-time Markov chain, *Q*, is by first finding its **embedded Markov chain (EMC)**. Strictly speaking, the EMC is a regular discrete-time Markov chain, sometimes referred to as a **[jump process](https://en.wikipedia.org/wiki/Jump_process)**. Each element of the one-step transition probability matrix of the EMC, *S*, is denoted by *s*<sub>*ij*</sub>, and represents the [conditional probability](https://en.wikipedia.org/wiki/Conditional_probability) of transitioning from state *i* into state *j*. These conditional probabilities may be found by

$s_{ij}={\begin{cases}{\frac {q_{ij}}{\sum _{k\neq i}q_{ik}}}&{\text{if }}i\neq j\\0&{\text{otherwise}}.\end{cases}}$

From this, *S* may be written as

$S=I-\left(\operatorname {diag} (Q)\right)^{-1}Q$

where *I* is the [identity matrix](https://en.wikipedia.org/wiki/Identity_matrix) and diag(*Q*) is the [diagonal matrix](https://en.wikipedia.org/wiki/Diagonal_matrix) formed by selecting the [main diagonal](https://en.wikipedia.org/wiki/Main_diagonal) from the matrix *Q* and setting all other elements to zero.

To find the stationary probability distribution vector, we must next find $\varphi$ such that

$\varphi S=\varphi ,$

with $\varphi$ being a row vector, such that all elements in $\varphi$ are greater than 0 and [$\|\varphi \|_{1}$](https://en.wikipedia.org/wiki/Norm_(mathematics) "Norm (mathematics)") = 1. From this, π may be found as

$\pi ={-\varphi (\operatorname {diag} (Q))^{-1} \over \left\|\varphi (\operatorname {diag} (Q))^{-1}\right\|_{1}}.$

(*S* may be periodic, even if *Q* is not. Once π is found, it must be normalized to a [unit vector](https://en.wikipedia.org/wiki/Unit_vector).)

Another discrete-time process that may be derived from a continuous-time Markov chain is a δ-skeleton—the (discrete-time) Markov chain formed by observing *X*(*t*) at intervals of δ units of time. The random variables *X*(0), *X*(δ), *X*(2δ), ... give the sequence of states visited by the δ-skeleton.

## Special types of Markov chains

### Markov model

Markov models are used to model changing systems. There are 4 main types of models, that generalize Markov chains depending on whether every sequential state is observable or not, and whether the system is to be adjusted on the basis of observations made:

|  |  |  |
|----|----|----|
|  | System state is fully observable | System state is partially observable |
| System is autonomous | Markov chain | [[Hidden Markov Model]] |
| System is controlled | [Markov decision process](https://en.wikipedia.org/wiki/Markov_decision_process) | [Partially observable Markov decision process](https://en.wikipedia.org/wiki/Partially_observable_Markov_decision_process) |

### Bernoulli scheme

A [Bernoulli scheme](https://en.wikipedia.org/wiki/Bernoulli_scheme) is a special case of a Markov chain where the transition probability matrix has identical rows, which means that the next state is independent of even the current state (in addition to being independent of the past states). A Bernoulli scheme with only two possible states is known as a [Bernoulli process](https://en.wikipedia.org/wiki/Bernoulli_process).

Note, however, by the [Ornstein isomorphism theorem](https://en.wikipedia.org/wiki/Ornstein_isomorphism_theorem), that every aperiodic and irreducible Markov chain is isomorphic to a Bernoulli scheme; thus, one might equally claim that Markov chains are a "special case" of Bernoulli schemes. The isomorphism generally requires a complicated recoding. The isomorphism theorem is even a bit stronger: it states that *any* [stationary stochastic process](https://en.wikipedia.org/wiki/Stationary_stochastic_process) is isomorphic to a Bernoulli scheme; the Markov chain is just one such example.

### Subshift of finite type

## Applications

Markov chains have been employed in a wide range of topics across the natural and social sciences, and in technological applications.

### Physics

Markovian systems appear extensively in [thermodynamics](https://en.wikipedia.org/wiki/Thermodynamics) and [statistical mechanics](https://en.wikipedia.org/wiki/Statistical_mechanics), whenever probabilities are used to represent unknown or unmodelled details of the system, if it can be assumed that the dynamics are time-invariant, and that no relevant history need be considered which is not already included in the state description. For example, a thermodynamic state operates under a probability distribution that is difficult or expensive to acquire. Therefore, Markov Chain Monte Carlo method can be used to draw samples randomly from a black-box to approximate the probability distribution of attributes over a range of objects.

Markov chains are used in [lattice QCD](https://en.wikipedia.org/wiki/Lattice_QCD) simulations.

### Chemistry

${{\text{E}}{}+{}{\underset {\mathrm {Substrate} \atop \mathrm {binding} }{\mathrm {S} {}\mathrel {\longrightleftharpoons } {}\mathrm {E} }}{\overset {\mathrm {Catalytic} \atop \mathrm {step} }{\mathrm {S} {}\mathrel {\longrightarrow } {}\mathrm {E} }}{}+{}\mathrm {P} }$

[Michaelis-Menten kinetics](https://en.wikipedia.org/wiki/Michaelis-Menten_kinetics). The enzyme (E) binds a substrate (S) and produces a product (P). Each reaction is a state transition in a Markov chain.

A reaction network is a chemical system involving multiple reactions and chemical species. The simplest stochastic models of such networks treat the system as a continuous time Markov chain with the state being the number of molecules of each species and with reactions modeled as possible transitions of the chain. Markov chains and continuous-time Markov processes are useful in chemistry when physical systems closely approximate the Markov property. For example, imagine a large number *n* of molecules in solution in state A, each of which can undergo a chemical reaction to state B with a certain average rate. Perhaps the molecule is an enzyme, and the states refer to how it is folded. The state of any single enzyme follows a Markov chain, and since the molecules are essentially independent of each other, the number of molecules in state A or B at a time is *n* times the probability a given molecule is in that state.

The classical model of enzyme activity, [Michaelis–Menten kinetics](https://en.wikipedia.org/wiki/Michaelis%E2%80%93Menten_kinetics), can be viewed as a Markov chain, where at each time step the reaction proceeds in some direction. While Michaelis-Menten is fairly straightforward, far more complicated reaction networks can also be modeled with Markov chains.

An algorithm based on a Markov chain was also used to focus the fragment-based growth of chemicals [in silico](https://en.wikipedia.org/wiki/In_silico) towards a desired class of compounds such as drugs or natural products. As a molecule is grown, a fragment is selected from the nascent molecule as the "current" state. It is not aware of its past (that is, it is not aware of what is already bonded to it). It then transitions to the next state when a fragment is attached to it. The transition probabilities are trained on databases of authentic classes of compounds.

Also, the growth (and composition) of [copolymers](https://en.wikipedia.org/wiki/Copolymer) may be modeled using Markov chains. Based on the reactivity ratios of the monomers that make up the growing polymer chain, the chain's composition may be calculated (for example, whether monomers tend to add in alternating fashion or in long runs of the same monomer). Due to [steric effects](https://en.wikipedia.org/wiki/Steric_effects), second-order Markov effects may also play a role in the growth of some polymer chains.

Similarly, it has been suggested that the crystallization and growth of some epitaxial [superlattice](https://en.wikipedia.org/wiki/Superlattice) oxide materials can be accurately described by Markov chains.

### Biology

Markov chains are used in various areas of biology. Notable examples include:

- [Phylogenetics](https://en.wikipedia.org/wiki/Phylogenetics) and [bioinformatics](https://en.wikipedia.org/wiki/Bioinformatics), where most [models of DNA evolution](https://en.wikipedia.org/wiki/Models_of_DNA_evolution) use continuous-time Markov chains to describe the [nucleotide](https://en.wikipedia.org/wiki/Nucleotide) present at a given site in the [genome](https://en.wikipedia.org/wiki/Genome).
- [Population dynamics](https://en.wikipedia.org/wiki/Population_dynamics), where Markov chains are in particular a central tool in the theoretical study of [matrix population models](https://en.wikipedia.org/wiki/Matrix_population_models).
- [Neurobiology](https://en.wikipedia.org/wiki/Neurobiology), where Markov chains have been used, e.g., to simulate the mammalian neocortex.
- [Systems biology](https://en.wikipedia.org/wiki/Systems_biology), for instance with the modeling of viral infection of single cells.
- [Compartmental models](https://en.wikipedia.org/wiki/Compartmental_models_in_epidemiology) for disease outbreak and epidemic modeling.

### Information theory

Markov chains are used throughout information processing. [Claude Shannon](https://en.wikipedia.org/wiki/Claude_Shannon)'s famous 1948 paper *[A Mathematical Theory of Communication](https://en.wikipedia.org/wiki/A_Mathematical_Theory_of_Communication)*, which in a single step created the field of [information theory](https://en.wikipedia.org/wiki/Information_theory), opens by introducing the concept of [entropy](https://en.wikipedia.org/wiki/Information_entropy) by modeling texts in a natural language (such as English) as generated by an ergodic Markov process, where each letter may depend statistically on previous letters. Such idealized models can capture many of the statistical regularities of systems. Even without describing the full structure of the system perfectly, such signal models can make possible very effective [data compression](https://en.wikipedia.org/wiki/Data_compression) through [entropy encoding](https://en.wikipedia.org/wiki/Entropy_encoding) techniques such as [arithmetic coding](https://en.wikipedia.org/wiki/Arithmetic_coding). They also allow effective [state estimation](https://en.wikipedia.org/wiki/State_estimation) and [pattern recognition](https://en.wikipedia.org/wiki/Pattern_recognition). Markov chains also play an important role in [reinforcement learning](https://en.wikipedia.org/wiki/Reinforcement_learning).

Markov chains are also the basis for hidden Markov models, which are an important tool in such diverse fields as telephone networks (which use the [Viterbi algorithm](https://en.wikipedia.org/wiki/Viterbi_algorithm) for error correction), speech recognition and [bioinformatics](https://en.wikipedia.org/wiki/Bioinformatics) (such as in rearrangements detection).

The [LZMA](https://en.wikipedia.org/wiki/Lempel%E2%80%93Ziv%E2%80%93Markov_chain_algorithm) lossless data compression algorithm combines Markov chains with [Lempel-Ziv compression](https://en.wikipedia.org/wiki/LZ77_and_LZ78) to achieve very high compression ratios.

### Queueing theory

Markov chains are the basis for the analytical treatment of queues ([queueing theory](https://en.wikipedia.org/wiki/Queueing_theory)). [Agner Krarup Erlang](https://en.wikipedia.org/wiki/Agner_Krarup_Erlang) initiated the subject in 1917. This makes them critical for optimizing the performance of telecommunications networks, where messages must often compete for limited resources (such as bandwidth).

Numerous queueing models use continuous-time Markov chains. For example, an [M/M/1 queue](https://en.wikipedia.org/wiki/M/M/1_queue) is a CTMC on the non-negative integers where upward transitions from *i* to *i* + 1 occur at rate *λ* according to a [[Poisson Process]] and describe job arrivals, while transitions from *i* to *i* – 1 (for *i* \> 1) occur at rate *μ* (job service times are exponentially distributed) and describe completed services (departures) from the queue.

### Internet applications

![[media/0a46d54c1950a7dbfb73fb9c3c082ffe6f0f6bec.png]]
A state diagram that represents the PageRank algorithm with a transitional probability of M, or ${\frac {\alpha }{k_{i}}}+{\frac {1-\alpha }{N}}$

The [PageRank](https://en.wikipedia.org/wiki/PageRank) of a webpage as used by [Google](https://en.wikipedia.org/wiki/Google) is defined by a Markov chain. It is the probability to be at page $i$ in the stationary distribution on the following Markov chain on all (known) webpages. If $N$ is the number of known webpages, and a page $i$ has $k_{i}$ outgoing links from it then it has transition probability ${\frac {\alpha }{k_{i}}}+{\frac {1-\alpha }{N}}$ for all pages that are linked to and ${\frac {1-\alpha }{N}}$ for all pages that are not linked to. The parameter $\alpha$ is taken to be about 0.85.

Markov models have also been used to analyze web navigation behavior of users. A user's web link transition on a particular website can be modeled using first- or second-order Markov models and can be used to make predictions regarding future navigation and to personalize the web page for an individual user.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

### Statistics

Markov chain methods have also become very important for generating sequences of random numbers to accurately reflect very complicated desired probability distributions, via a process called [[Markov Chain Monte Carlo]] (MCMC). In recent years this has revolutionized the practicability of [Bayesian inference](https://en.wikipedia.org/wiki/Bayesian_inference) methods, allowing a wide range of [posterior distributions](https://en.wikipedia.org/wiki/Posterior_distribution) to be simulated and their parameters found numerically.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

### Economics and finance

Markov chains are used in finance and economics to model a variety of different phenomena, including the distribution of income, the size distribution of firms, asset prices and market crashes. [D. G. Champernowne](https://en.wikipedia.org/wiki/D._G._Champernowne) built a Markov chain model of the distribution of income in 1953. [Herbert A. Simon](https://en.wikipedia.org/wiki/Herbert_A._Simon) and co-author Charles Bonini used a Markov chain model to derive a stationary Yule distribution of firm sizes. [Louis Bachelier](https://en.wikipedia.org/wiki/Louis_Bachelier) was the first to observe that stock prices followed a random walk. The random walk was later seen as evidence in favor of the [efficient-market hypothesis](https://en.wikipedia.org/wiki/Efficient-market_hypothesis) and random walk models were popular in the literature of the 1960s. Regime-switching models of business cycles were popularized by [James D. Hamilton](https://en.wikipedia.org/wiki/James_D._Hamilton) (1989), who used a Markov chain to model switches between periods of high and low GDP growth (or, alternatively, economic expansions and recessions). A more recent example is the [Markov switching multifractal](https://en.wikipedia.org/wiki/Markov_switching_multifractal) model of [Laurent E. Calvet](https://en.wikipedia.org/wiki/Laurent_E._Calvet) and Adlai J. Fisher, which builds upon the convenience of earlier regime-switching models. It uses an arbitrarily large Markov chain to drive the level of volatility of asset returns.

Dynamic macroeconomics makes heavy use of Markov chains. An example is using Markov chains to exogenously model prices of equity (stock) in a [general equilibrium](https://en.wikipedia.org/wiki/General_equilibrium) setting.

[Credit rating agencies](https://en.wikipedia.org/wiki/Credit_rating_agency) produce annual tables of the transition probabilities for bonds of different credit ratings.

### Social sciences

Markov chains are generally used in describing [path-dependent](https://en.wikipedia.org/wiki/Path-dependent) arguments, where current structural configurations condition future outcomes. An example is the reformulation of the idea, originally due to [Karl Marx](https://en.wikipedia.org/wiki/Karl_Marx)'s *[Das Kapital](https://en.wikipedia.org/wiki/Das_Kapital)*, tying [economic development](https://en.wikipedia.org/wiki/Economic_development) to the rise of [capitalism](https://en.wikipedia.org/wiki/Capitalism). In current research, it is common to use a Markov chain to model how once a country reaches a specific level of economic development, the configuration of structural factors, such as size of the [middle class](https://en.wikipedia.org/wiki/Middle_class), the ratio of urban to rural residence, the rate of [political](https://en.wikipedia.org/wiki/Political) mobilization, etc., will generate a higher probability of transitioning from [authoritarian](https://en.wikipedia.org/wiki/Authoritarian) to [democratic regime](https://en.wikipedia.org/wiki/Democratic_regime).

### Music

Markov chains are employed in [algorithmic music composition](https://en.wikipedia.org/wiki/Algorithmic_composition), particularly in [software](https://en.wikipedia.org/wiki/Software) such as [Csound](https://en.wikipedia.org/wiki/Csound), [Max](https://en.wikipedia.org/wiki/Max_(software) "Max (software)"), and [SuperCollider](https://en.wikipedia.org/wiki/SuperCollider). In a first-order chain, the states of the system become note or pitch values, and a [probability vector](https://en.wikipedia.org/wiki/Probability_vector) for each note is constructed, completing a transition probability matrix (see below). An algorithm is constructed to produce output note values based on the transition matrix weightings, which could be [MIDI](https://en.wikipedia.org/wiki/MIDI) note values, frequency ([Hz](https://en.wikipedia.org/wiki/Hertz)), or any other desirable metric.

|  |  |  |  |
|----|----|----|----|
| Note | A | C♯ | E♭ |
| A | 0.1 | 0.6 | 0.3 |
| C♯ | 0.25 | 0.05 | 0.7 |
| E♭ | 0.7 | 0.3 | 0 |

1st-order matrix {.wikitable style="float: left"}

|       |      |      |      |
|-------|------|------|------|
| Notes | A    | D    | G    |
| AA    | 0.18 | 0.6  | 0.22 |
| AD    | 0.5  | 0.5  | 0    |
| AG    | 0.15 | 0.75 | 0.1  |
| DD    | 0    | 0    | 1    |
| DA    | 0.25 | 0    | 0.75 |
| DG    | 0.9  | 0.1  | 0    |
| GG    | 0.4  | 0.4  | 0.2  |
| GA    | 0.5  | 0.25 | 0.25 |
| GD    | 1    | 0    | 0    |

2nd-order matrix {.wikitable style="float: left; margin-left: 1em"}

A second-order Markov chain can be introduced by considering the current state *and* also the previous state, as indicated in the second table. Higher, *n*th-order chains tend to "group" particular notes together, while 'breaking off' into other patterns and sequences occasionally. These higher-order chains tend to generate results with a sense of [phrasal](https://en.wikipedia.org/wiki/Phrase_(music) "Phrase (music)") structure, rather than the 'aimless wandering' produced by a first-order system.

Markov chains can be used structurally, as in Xenakis's Analogique A and B. Markov chains are also used in systems which use a Markov model to react interactively to music input.

Usually musical systems need to enforce specific control constraints on the finite-length sequences they generate, but control constraints are not compatible with Markov models, since they induce long-range dependencies that violate the Markov hypothesis of limited memory. In order to overcome this limitation, a new approach has been proposed.

### Games and sports

Markov chains can be used to model many games of chance. The children's games [Snakes and Ladders](https://en.wikipedia.org/wiki/Snakes_and_Ladders) and "[Hi Ho! Cherry-O](https://en.wikipedia.org/wiki/Hi_Ho!_Cherry-O)", for example, are represented exactly by Markov chains. At each turn, the player starts in a given state (on a given square) and from there has fixed odds of moving to certain other states (squares).<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

Markov chain models have been used in advanced baseball analysis since 1960, although their use is still rare. Each half-inning of a baseball game fits the Markov chain state when the number of runners and outs are considered. During any at-bat, there are 24 possible combinations of number of outs and position of the runners. Mark Pankin shows that Markov chain models can be used to evaluate runs created for both individual players as well as a team. He also discusses various kinds of strategies and play conditions: how Markov chain models have been used to analyze statistics for game situations such as [bunting](https://en.wikipedia.org/wiki/Bunt_(baseball) "Bunt (baseball)") and [base stealing](https://en.wikipedia.org/wiki/Base_stealing) and differences when playing on grass vs. [AstroTurf](https://en.wikipedia.org/wiki/AstroTurf).

### Markov text generators

Markov processes can also be used to [generate superficially real-looking text](https://en.wikipedia.org/wiki/Natural_language_generation) given a sample document. Markov processes are used in a variety of recreational "[parody generator](https://en.wikipedia.org/wiki/Parody_generator)" software (see [dissociated press](https://en.wikipedia.org/wiki/Dissociated_press), Jeff Harrison, [Mark V. Shaney](https://en.wikipedia.org/wiki/Mark_V._Shaney), and Academias Neutronium). Several open-source text generation libraries using Markov chains exist.

## See also

- [Dynamics of Markovian particles](https://en.wikipedia.org/wiki/Dynamics_of_Markovian_particles)
- [Gauss–Markov process](https://en.wikipedia.org/wiki/Gauss%E2%80%93Markov_process)
- [Markov chain approximation method](https://en.wikipedia.org/wiki/Markov_chain_approximation_method)
- [Markov chain geostatistics](https://en.wikipedia.org/wiki/Markov_chain_geostatistics)
- [Markov chain mixing time](https://en.wikipedia.org/wiki/Markov_chain_mixing_time)
- [Markov chain tree theorem](https://en.wikipedia.org/wiki/Markov_chain_tree_theorem)
- [Markov decision process](https://en.wikipedia.org/wiki/Markov_decision_process)
- [Markov information source](https://en.wikipedia.org/wiki/Markov_information_source)
- [Markov odometer](https://en.wikipedia.org/wiki/Markov_odometer)
- [Markov operator](https://en.wikipedia.org/wiki/Markov_operator)
- [Markov random field](https://en.wikipedia.org/wiki/Markov_random_field)
- [Master equation](https://en.wikipedia.org/wiki/Master_equation)
- [Quantum Markov chain](https://en.wikipedia.org/wiki/Quantum_Markov_chain)
- [Semi-Markov process](https://en.wikipedia.org/wiki/Semi-Markov_process)
- [Stochastic cellular automaton](https://en.wikipedia.org/wiki/Stochastic_cellular_automaton)
- [Telescoping Markov chain](https://en.wikipedia.org/wiki/Telescoping_Markov_chain)
- [Variable-order Markov model](https://en.wikipedia.org/wiki/Variable-order_Markov_model)

## Notes

1.  ^   Sean Meyn; Richard L. Tweedie (2 April 2009). [Markov Chains and Stochastic Stability](https://books.google.com/books?id=Md7RnYEPkJwC). Cambridge University Press. p. 3. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-73182-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-73182-9).
2.  Reuven Y. Rubinstein; Dirk P. Kroese (20 September 2011). [Simulation and the Monte Carlo Method](https://books.google.com/books?id=yWcvT80gQK4C). John Wiley & Sons. p. 225. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-118-21052-9](https://en.wikipedia.org/wiki/Special:BookSources/978-1-118-21052-9).
3.  Dani Gamerman; Hedibert F. Lopes (10 May 2006). [Markov Chain Monte Carlo: Stochastic Simulation for Bayesian Inference, Second Edition](https://books.google.com/books?id=yPvECi_L3bwC). CRC Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-58488-587-0](https://en.wikipedia.org/wiki/Special:BookSources/978-1-58488-587-0).
4.  ["Markovian"](https://www.oed.com/search/dictionary/?q=Markovian). *[Oxford English Dictionary](https://en.wikipedia.org/wiki/Oxford_English_Dictionary)* (Online ed.). Oxford University Press. (Subscription or [participating institution membership](https://www.oed.com/public/login/loggingin#withyourlibrary) required.)
5.  ^   Øksendal, B. K. (Bernt Karsten) (2003). *Stochastic differential equations: an introduction with applications* (6th ed.). Berlin: Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [3-540-04758-1](https://en.wikipedia.org/wiki/Special:BookSources/3-540-04758-1). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [52203046](https://search.worldcat.org/oclc/52203046).
6.  ^   Søren Asmussen (15 May 2003). [Applied Probability and Queues](https://books.google.com/books?id=BeYaTxesKy0C). Springer Science & Business Media. p. 7. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-00211-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-00211-8).
7.  Emanuel Parzen (17 June 2015). [Stochastic Processes](https://books.google.com/books?id=0mB2CQAAQBAJ). Courier Dover Publications. p. 188. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-486-79688-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-486-79688-8).
8.  Samuel Karlin; Howard E. Taylor (2 December 2012). [A First Course in Stochastic Processes](https://books.google.com/books?id=dSDxjX9nmmMC). Academic Press. pp. 29 and 30. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-08-057041-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-08-057041-9).
9.  John Lamperti (1977). [Stochastic processes: a survey of the mathematical theory](https://books.google.com/books?id=Pd4cvgAACAAJ). Springer-Verlag. pp. 106–121. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-90275-1](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-90275-1).
10. Sheldon M. Ross (1996). [Stochastic processes](https://books.google.com/books?id=ImUPAQAAMAAJ). Wiley. pp. 174 and 231. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-12062-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-12062-9).
11. Everitt, B.S. (2002) *The Cambridge Dictionary of Statistics*. CUP. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-81099-X](https://en.wikipedia.org/wiki/Special:BookSources/0-521-81099-X)
12. Parzen, E. (1962) *Stochastic Processes*, Holden-Day. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-8162-6664-6](https://en.wikipedia.org/wiki/Special:BookSources/0-8162-6664-6) (Table 6.1)
13. Dodge, Y. (2003) *The Oxford Dictionary of Statistical Terms*, OUP. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-19-920613-9](https://en.wikipedia.org/wiki/Special:BookSources/0-19-920613-9) (entry for "Markov chain")
14. Dodge, Y. *The Oxford Dictionary of Statistical Terms*, OUP. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-19-920613-9](https://en.wikipedia.org/wiki/Special:BookSources/0-19-920613-9)
15. Meyn, S. Sean P., and Richard L. Tweedie. (2009) *Markov chains and stochastic stability*. Cambridge University Press. (Preface, p. iii)
16. ^      Charles Miller Grinstead; James Laurie Snell (1997). [Introduction to Probability](https://archive.org/details/flooved3489). American Mathematical Soc. pp. [464](https://archive.org/details/flooved3489/page/n473)–466. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8218-0749-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8218-0749-1).
17. ^    Pierre Bremaud (9 March 2013). [Markov Chains: Gibbs Fields, Monte Carlo Simulation, and Queues](https://books.google.com/books?id=jrPVBwAAQBAJ). Springer Science & Business Media. p. ix. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4757-3124-8](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4757-3124-8).
18. ^    Hayes, Brian (2013). "First links in the Markov chain". *American Scientist*. **101** (2): 92–96. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1511/2013.101.92](https://doi.org/10.1511%2F2013.101.92).
19. ^   Sheldon M. Ross (1996). [Stochastic processes](https://books.google.com/books?id=ImUPAQAAMAAJ). Wiley. pp. 235 and 358. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-12062-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-12062-9).
20. Jarrow, Robert; Protter, Philip (2004). "A short history of stochastic integration and mathematical finance: The early years, 1880–1970". *A Festschrift for Herman Rubin*. pp. 75–91. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.114.632](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.114.632). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/lnms/1196285381](https://doi.org/10.1214%2Flnms%2F1196285381). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-940600-61-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-940600-61-4).
21. Guttorp, Peter; Thorarinsdottir, Thordis L. (2012). "What Happened to Discrete Chaos, the Quenouille Process, and the Sharp Markov Property? Some History of Stochastic Point Processes". *International Statistical Review*. **80** (2): 253–268. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1111/j.1751-5823.2012.00181.x](https://doi.org/10.1111%2Fj.1751-5823.2012.00181.x).
22. [Seneta, E.](https://en.wikipedia.org/wiki/Eugene_Seneta) (1996). "Markov and the Birth of Chain Dependence Theory". *International Statistical Review*. **64** (3): 255–257. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/1403785](https://doi.org/10.2307%2F1403785). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [1403785](https://www.jstor.org/stable/1403785).
23. Seneta, E. (1998). "I.J. Bienaymé \[1796–1878\]: Criticality, Inequality, and Internationalization". *International Statistical Review*. **66** (3): 291–292. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/1403518](https://doi.org/10.2307%2F1403518). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [1403518](https://www.jstor.org/stable/1403518).
24. Bru B, Hertz S (2001). "Maurice Fréchet". In [Heyde CC](https://en.wikipedia.org/wiki/Chris_Heyde), Seneta E, Crépel P, Fienberg SE, Gani J (eds.). *Statisticians of the Centuries*. New York, NY: Springer. pp. 331–334. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-1-4613-0179-0_71](https://doi.org/10.1007%2F978-1-4613-0179-0_71). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-95283-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-95283-3).
25. ^    Kendall, D. G.; Batchelor, G. K.; Bingham, N. H.; Hayman, W. K.; Hyland, J. M. E.; Lorentz, G. G.; Moffatt, H. K.; Parry, W.; Razborov, A. A.; Robinson, C. A.; Whittle, P. (1990). "Andrei Nikolaevich Kolmogorov (1903–1987)". *Bulletin of the London Mathematical Society*. **22** (1): 33. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1112/blms/22.1.31](https://doi.org/10.1112%2Fblms%2F22.1.31).
26. ^   Cramér, Harald (1976). ["Half a Century with Probability Theory: Some Personal Recollections"](https://doi.org/10.1214%2Faop%2F1176996025). *The Annals of Probability*. **4** (4): 509–546. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/aop/1176996025](https://doi.org/10.1214%2Faop%2F1176996025).
27. Marc Barbut; Bernard Locker; Laurent Mazliak (23 August 2016). [Paul Lévy and Maurice Fréchet: 50 Years of Correspondence in 107 Letters](https://books.google.com/books?id=lSz_vQAACAAJ). Springer London. p. 5. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4471-7262-8](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4471-7262-8).
28. Valeriy Skorokhod (5 December 2005). [Basic Principles and Applications of Probability Theory](https://books.google.com/books?id=dQkYMjRK3fYC). Springer Science & Business Media. p. 146. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-26312-8](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-26312-8).
29. Bernstein, Jeremy (2005). "Bachelier". *American Journal of Physics*. **73** (5): 395–398. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2005AmJPh..73..395B](https://ui.adsabs.harvard.edu/abs/2005AmJPh..73..395B). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1119/1.1848117](https://doi.org/10.1119%2F1.1848117).
30. William J. Anderson (6 December 2012). [Continuous-Time Markov Chains: An Applications-Oriented Approach](https://books.google.com/books?id=YpHfBwAAQBAJ&pg=PR8). Springer Science & Business Media. p. vii. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4612-3038-0](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4612-3038-0).
31. Kendall, D. G.; Batchelor, G. K.; Bingham, N. H.; Hayman, W. K.; Hyland, J. M. E.; Lorentz, G. G.; Moffatt, H. K.; Parry, W.; Razborov, A. A.; Robinson, C. A.; Whittle, P. (1990). "Andrei Nikolaevich Kolmogorov (1903–1987)". *Bulletin of the London Mathematical Society*. **22** (1): 57. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1112/blms/22.1.31](https://doi.org/10.1112%2Fblms%2F22.1.31).
32. Subramanian, Devika (Fall 2008). ["The curious case of Mark V. Shaney"](https://www.cs.rice.edu/~devika/comp140/Shaney.pdf) (PDF). Computer Science. *Comp 140 course notes, Fall 2008*. William Marsh Rice University. Retrieved 30 November 2024.
33. ^   Ionut Florescu (7 November 2014). [Probability and Stochastic Processes](https://books.google.com/books?id=Z5xEBQAAQBAJ&pg=PR22). John Wiley & Sons. pp. 373 and 374. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-118-59320-2](https://en.wikipedia.org/wiki/Special:BookSources/978-1-118-59320-2).
34. ^   Samuel Karlin; Howard E. Taylor (2 December 2012). [A First Course in Stochastic Processes](https://books.google.com/books?id=dSDxjX9nmmMC). Academic Press. p. 49. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-08-057041-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-08-057041-9).
35. Weiss, George H. (2006). "Random Walks". *Encyclopedia of Statistical Sciences*. p. 1. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1002/0471667196.ess2180.pub2](https://doi.org/10.1002%2F0471667196.ess2180.pub2). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-66719-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-66719-3).
36. Michael F. Shlesinger (1985). [The Wonderful world of stochastics: a tribute to Elliott W. Montroll](https://books.google.com/books?id=p6fvAAAAMAAJ). North-Holland. pp. 8–10. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-444-86937-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-444-86937-1).
37. Emanuel Parzen (17 June 2015). [Stochastic Processes](https://books.google.com/books?id=0mB2CQAAQBAJ). Courier Dover Publications. p. 7, 8. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-486-79688-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-486-79688-8).
38. Joseph L. Doob (1990). [Stochastic processes](https://books.google.com/books?id=7Bu8jgEACAAJ). Wiley. p. 46, 47.
39. Donald L. Snyder; Michael I. Miller (6 December 2012). [Random Point Processes in Time and Space](https://books.google.com/books?id=c_3UBwAAQBAJ). Springer Science & Business Media. p. 32. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4612-3166-0](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4612-3166-0).
40. ^   Serfozo, Richard (2009). *Basics of Applied Stochastic Processes*. Probability and Its Applications. Berlin: Springer. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-3-540-89332-5](https://doi.org/10.1007%2F978-3-540-89332-5). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-89331-8](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-89331-8).
41. ["Chapter 11 "Markov Chains""](https://web.archive.org/web/20170215053623/http://www.dartmouth.edu/~chance/teaching_aids/books_articles/probability_book/Chapter11.pdf) (PDF). Archived from [the original](https://www.dartmouth.edu/~chance/teaching_aids/books_articles/probability_book/Chapter11.pdf) (PDF) on 2017-02-15. Retrieved 2017-06-02.
42. Schmitt, Florian; Rothlauf, Franz (2001). "On the Importance of the Second Largest Eigenvalue on the Convergence Rate of Genetic Algorithms". *Proceedings of the 14th Symposium on Reliable Distributed Systems*. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.28.6191](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.28.6191).
43. Rosenthal, Jeffrey S. (1995). "Convergence Rates for Markov Chains". *SIAM Review*. **37** (3): 387–405. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/1037083](https://doi.org/10.1137%2F1037083). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2132659](https://www.jstor.org/stable/2132659).
44. Franzke, Brandon; Kosko, Bart (1 October 2011). "Noise can speed convergence in Markov chains". *Physical Review E*. **84** (4) 041112. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2011PhRvE..84d1112F](https://ui.adsabs.harvard.edu/abs/2011PhRvE..84d1112F). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1103/PhysRevE.84.041112](https://doi.org/10.1103%2FPhysRevE.84.041112). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [22181092](https://pubmed.ncbi.nlm.nih.gov/22181092).
45. [Norris, J. R.](https://en.wikipedia.org/wiki/James_R._Norris) (1997). "Continuous-time Markov chains I". *Markov Chains*. pp. 60–107. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1017/CBO9780511810633.004](https://doi.org/10.1017%2FCBO9780511810633.004). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-511-81063-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-511-81063-3).
46. Spitzer, Frank (1970). ["Interaction of Markov Processes"](https://doi.org/10.1016%2F0001-8708%2870%2990034-4). *[Advances in Mathematics](https://en.wikipedia.org/wiki/Advances_in_Mathematics)*. **5** (2): 246–290. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1970AdMat...5..246S](https://ui.adsabs.harvard.edu/abs/1970AdMat...5..246S). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/0001-8708(70)90034-4](https://doi.org/10.1016%2F0001-8708%2870%2990034-4).
47. [Dobrushin, R. L.](https://en.wikipedia.org/wiki/Roland_Dobrushin); Kryukov, V.I.; Toom, A. L. (1978). [Stochastic Cellular Systems: Ergodicity, Memory, Morphogenesis](https://books.google.com/books?id=0Wa7AAAAIAAJ&q=locally+interacting+markov+chains+toom+Dobrushin&pg=PA181). Manchester University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-7190-2206-7](https://en.wikipedia.org/wiki/Special:BookSources/978-0-7190-2206-7). Retrieved 2016-03-04.
48. Heyman, Daniel P.; Sobel, Mathew J. (1982). *Stochastic Models in Operations Research, Volume 1*. New York: McGraw-Hill. p. 230. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-07-028631-0](https://en.wikipedia.org/wiki/Special:BookSources/0-07-028631-0).
49. [Peres, Yuval](https://en.wikipedia.org/wiki/Yuval_Peres). ["Show that positive recurrence is a class property"](https://math.stackexchange.com/questions/4572155/show-that-positive-recurrence-is-a-class-property). *Mathematics Stack Exchange*. Retrieved 2024-02-01.
50. [Lalley, Steve](https://en.wikipedia.org/wiki/Steven_Lalley) (2016). ["Markov Chains: Basic Theory"](http://galton.uchicago.edu/~lalley/Courses/312/MarkovChains.pdf) (PDF). Retrieved 22 June 2024.
51. Parzen, Emanuel (1962). *Stochastic Processes*. San Francisco: Holden-Day. p. 145. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-8162-6664-6](https://en.wikipedia.org/wiki/Special:BookSources/0-8162-6664-6). `{{`[`cite book`](https://en.wikipedia.org/wiki/Template:Cite_book)`}}`: ISBN / Date incompatibility ([help](https://en.wikipedia.org/wiki/Help:CS1_errors#invalid_isbn_date))
52. ^   [Shalizi, Cosma](https://en.wikipedia.org/wiki/Cosma_Shalizi) (1 Dec 2023). ["Ergodic Theory"](http://bactra.org/notebooks/ergodic-theory.html). *bactra.org*. Retrieved 2024-02-01.
53. Seneta, E. (Eugene) (1973). [Non-negative matrices; an introduction to theory and applications](http://archive.org/details/nonnegativematri00esen_0). Internet Archive. New York, Wiley. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-470-77605-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-470-77605-6).
54. ["10.3: Regular Markov Chains"](https://math.libretexts.org/Bookshelves/Applied_Mathematics/Applied_Finite_Mathematics_(Sekhon_and_Bloom)/10%3A_Markov_Chains/10.03%3A_Regular_Markov_Chains). *Mathematics LibreTexts*. 2020-03-22. Retrieved 2024-02-01.
55. Seneta, E. (Eugene) (1973). "2.4. Combinatorial properties". [Non-negative matrices; an introduction to theory and applications](http://archive.org/details/nonnegativematri00esen_0). Internet Archive. New York, Wiley. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-470-77605-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-470-77605-6).
56. Shen, Jian (1996-10-15). ["An improvement of the Dulmage-Mendelsohn theorem"](https://doi.org/10.1016%2F0012-365X%2895%2900060-A). *Discrete Mathematics*. **158** (1): 295–297. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/0012-365X(95)00060-A](https://doi.org/10.1016%2F0012-365X%2895%2900060-A).
57. Kallenberg, Olav (2002). *Foundations of modern probability*. Probability and its applications (2. ed., \[Nachdr.\] ed.). New York, NY Berlin Heidelberg: Springer. Proposition 8.6 (page 145). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-95313-7](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-95313-7).
58. Doblinger, G. (September 1998). ["Smoothing of noisy AR signals using an adaptive Kalman filter"](https://publik.tuwien.ac.at/files/pub-et_3285.pdf) (PDF). *9th European Signal Processing Conference (EUSIPCO 1998)*: 781–784.
59. [Norris, J. R.](https://en.wikipedia.org/wiki/James_R._Norris) (1997). "Continuous-time Markov chains II". *Markov Chains*. pp. 108–127. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1017/CBO9780511810633.005](https://doi.org/10.1017%2FCBO9780511810633.005). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-511-81063-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-511-81063-3).
60. Chung, Kai Lai; Walsh, John B. (2006). *Markov Processes, Brownian Motion, and Time Symmetry* (2nd ed.). Springer New York. p. 304. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-28696-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-28696-9).
61. ^     Matthew Nicol and Karl Petersen, (2009) "[Ergodic Theory: Basic Examples and Constructions](https://www.math.uh.edu/~nicol/pdffiles/petersen.pdf)", *Encyclopedia of Complexity and Systems Science*, Springer [https://doi.org/10.1007/978-0-387-30440-3_177](https://doi.org/10.1007/978-0-387-30440-3_177)
62. Fitzpatrick, Richard. ["Thermodynamics and Statistical Mechanics"](https://web.archive.org/web/20161130172856/http://farside.ph.utexas.edu/teaching/sm1/Thermal.pdf) (PDF). Archived from [the original](https://farside.ph.utexas.edu/teaching/sm1/Thermal.pdf) (PDF) on 2016-11-30. Retrieved 2017-06-02.
63. ^   van Ravenzwaaij, Don; Cassey, Pete; Brown, Scott D. (2016-03-11). ["A simple introduction to Markov Chain Monte–Carlo sampling"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5862921). *Psychonomic Bulletin & Review*. **25** (1): 143–154. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3758/s13423-016-1015-8](https://doi.org/10.3758%2Fs13423-016-1015-8). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [5862921](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5862921). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [26968853](https://pubmed.ncbi.nlm.nih.gov/26968853).
64. Gattringer, Christof; Lang, Christian B (2010). [Quantum Chromodynamics on the Lattice](https://www.springer.com/gb/book/9783642018497). Lecture Notes in Physics. Vol. 788. Springer-Verlag Berlin Heidelberg. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-3-642-01850-3](https://doi.org/10.1007%2F978-3-642-01850-3). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-642-01849-7](https://en.wikipedia.org/wiki/Special:BookSources/978-3-642-01849-7).
65. Anderson, David F.; Kurtz, Thomas G. (2011), "Continuous Time Markov Chain Models for Chemical Reaction Networks", *Design and Analysis of Biomolecular Circuits*, Springer New York, pp. 3–42, [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-1-4419-6766-4_1](https://doi.org/10.1007%2F978-1-4419-6766-4_1), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4419-6765-7](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4419-6765-7)`{{`[`citation`](https://en.wikipedia.org/wiki/Template:Citation)`}}`: CS1 maint: work parameter with ISBN ([link](https://en.wikipedia.org/wiki/Category:CS1_maint:_work_parameter_with_ISBN))
66. Du, Chao; Kou, S. C. (September 2012). ["Correlation analysis of enzymatic reaction of a single protein molecule"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3568780). *The Annals of Applied Statistics*. **6** (3): 950–976. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1209.6210](https://arxiv.org/abs/1209.6210). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2012arXiv1209.6210D](https://ui.adsabs.harvard.edu/abs/2012arXiv1209.6210D). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/12-aoas541](https://doi.org/10.1214%2F12-aoas541). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [3568780](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3568780). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [23408514](https://pubmed.ncbi.nlm.nih.gov/23408514).
67. Kutchukian, Peter; Lou, David; Shakhnovich, Eugene (2009). "FOG: Fragment Optimized Growth Algorithm for the de Novo Generation of Molecules occupying Druglike Chemical". *Journal of Chemical Information and Modeling*. **49** (7): 1630–1642. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1021/ci9000458](https://doi.org/10.1021%2Fci9000458). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [19527020](https://pubmed.ncbi.nlm.nih.gov/19527020).
68. Kutchukian, P.S.; Lou, D.; Shakhnovich, Eugene I. (2009-06-15). "FOG: Fragment Optimized Growth Algorithm for the de Novo Generation of Molecules Occupying Druglike Chemical Space". *Journal of Chemical Information and Modeling*. **49** (7): 1630–1642. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1021/ci9000458](https://doi.org/10.1021%2Fci9000458). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [19527020](https://pubmed.ncbi.nlm.nih.gov/19527020).
69. Kopp, V. S.; Kaganer, V. M.; Schwarzkopf, J.; Waidick, F.; Remmele, T.; Kwasniewski, A.; Schmidbauer, M. (2011). "X-ray diffraction from nonperiodic layered structures with correlations: Analytical calculation and experiment on mixed Aurivillius films". *Acta Crystallographica Section A*. **68** (Pt 1): 148–155. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2012AcCrA..68..148K](https://ui.adsabs.harvard.edu/abs/2012AcCrA..68..148K). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1107/S0108767311044874](https://doi.org/10.1107%2FS0108767311044874). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [22186291](https://pubmed.ncbi.nlm.nih.gov/22186291).
70. George, Dileep; Hawkins, Jeff (2009). Friston, Karl J. (ed.). ["Towards a Mathematical Theory of Cortical Micro-circuits"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2749218). *PLOS Comput Biol*. **5** (10) e1000532. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2009PLSCB...5E0532G](https://ui.adsabs.harvard.edu/abs/2009PLSCB...5E0532G). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1371/journal.pcbi.1000532](https://doi.org/10.1371%2Fjournal.pcbi.1000532). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [2749218](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2749218). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [19816557](https://pubmed.ncbi.nlm.nih.gov/19816557).
71. Gupta, Ankur; Rawlings, James B. (April 2014). ["Comparison of Parameter Estimation Methods in Stochastic Chemical Kinetic Models: Examples in Systems Biology"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4946376). *AIChE Journal*. **60** (4): 1253–1268. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2014AIChE..60.1253G](https://ui.adsabs.harvard.edu/abs/2014AIChE..60.1253G). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1002/aic.14409](https://doi.org/10.1002%2Faic.14409). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [4946376](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4946376). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [27429455](https://pubmed.ncbi.nlm.nih.gov/27429455).
72. Thomsen, Samuel W. (2009), "Some evidence concerning the genesis of Shannon's information theory", *Studies in History and Philosophy of Science*, **40** (1): 81–91, [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2009SHPSA..40...81T](https://ui.adsabs.harvard.edu/abs/2009SHPSA..40...81T), [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.shpsa.2008.12.011](https://doi.org/10.1016%2Fj.shpsa.2008.12.011) 
73. Pratas, D; Silva, R; Pinho, A; Ferreira, P (May 18, 2015). ["An alignment-free method to find and visualise rearrangements between pairs of DNA sequences"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4434998). *Scientific Reports*. **5** (10203) 10203. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2015NatSR...510203P](https://ui.adsabs.harvard.edu/abs/2015NatSR...510203P). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1038/srep10203](https://doi.org/10.1038%2Fsrep10203). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [4434998](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4434998). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [25984837](https://pubmed.ncbi.nlm.nih.gov/25984837).
74. O'Connor, John J.; [Robertson, Edmund F.](https://en.wikipedia.org/wiki/Edmund_F._Robertson), ["Markov chain"](https://mathshistory.st-andrews.ac.uk/Biographies/Erlang.html), *[MacTutor History of Mathematics Archive](https://en.wikipedia.org/wiki/MacTutor_History_of_Mathematics_Archive)*, [University of St Andrews](https://en.wikipedia.org/wiki/University_of_St_Andrews)
75. S. P. Meyn, 2007. [Control Techniques for Complex Networks](http://www.meyn.ece.ufl.edu/archive/spm_files/CTCN/MonographTocBib.pdf) [Archived](https://web.archive.org/web/20150513155013/http://www.meyn.ece.ufl.edu/archive/spm_files/CTCN/MonographTocBib.pdf) 2015-05-13 at the [Wayback Machine](https://en.wikipedia.org/wiki/Wayback_Machine), Cambridge University Press, 2007.
76. [U.S. patent 6,285,999](https://patents.google.com/patent/US6285999)
77. Gupta, Brij; Agrawal, Dharma P.; Yamaguchi, Shingo (16 May 2016). [Handbook of Research on Modern Cryptographic Solutions for Computer and Cyber Security](https://books.google.com/books?id=Ctk6DAAAQBAJ&pg=PA448). IGI Global. pp. 448–. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-5225-0106-0](https://en.wikipedia.org/wiki/Special:BookSources/978-1-5225-0106-0).
78. Langville, Amy N.; Meyer, Carl D. (2006). ["A Reordering for the PageRank Problem"](https://web.archive.org/web/20170921211826/http://meyer.math.ncsu.edu/Meyer/PS_Files/ReorderingPageRank.pdf) (PDF). *SIAM Journal on Scientific Computing*. **27** (6): 2112–2113. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2006SJSC...27.2112L](https://ui.adsabs.harvard.edu/abs/2006SJSC...27.2112L). [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.58.8652](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.58.8652). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/040607551](https://doi.org/10.1137%2F040607551). Archived from [the original](http://meyer.math.ncsu.edu/Meyer/PS_Files/ReorderingPageRank.pdf) (PDF) on 2017-09-21. Retrieved 2017-11-07.
79. Page, Lawrence; Brin, Sergey; Motwani, Rajeev; Winograd, Terry (1999). *The PageRank Citation Ranking: Bringing Order to the Web* (Technical report). [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.31.1768](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.31.1768).
80. Champernowne, D (1953). "A model of income distribution". *The Economic Journal*. **63** (250): 318–51. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2227127](https://doi.org/10.2307%2F2227127). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2227127](https://www.jstor.org/stable/2227127).
81. Simon, Herbert; C Bonini (1958). "The size distribution of business firms". *Am. Econ. Rev*. **42**: 425–40.
82. Bachelier, Louis (1900). "Théorie de la spéculation". *Annales Scientifiques de l'École Normale Supérieure*. **3**: 21–86. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.24033/asens.476](https://doi.org/10.24033%2Fasens.476). [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[2027/coo.31924001082803](https://hdl.handle.net/2027%2Fcoo.31924001082803).
83. e.g.Fama, E (1965). "The behavior of stock market prices". *Journal of Business*. **38**.
84. Hamilton, James (1989). "A new approach to the economic analysis of nonstationary time series and the business cycle". *Econometrica*. **57** (2): 357–84. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.397.3582](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.397.3582). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/1912559](https://doi.org/10.2307%2F1912559). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [1912559](https://www.jstor.org/stable/1912559).
85. Calvet, Laurent E.; Fisher, Adlai J. (2001). ["Forecasting Multifractal Volatility"](http://archive.nyu.edu/handle/2451/26894). *[Journal of Econometrics](https://en.wikipedia.org/wiki/Journal_of_Econometrics)*. **105** (1): 27–58. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2001JEcon.105...27C](https://ui.adsabs.harvard.edu/abs/2001JEcon.105...27C). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/S0304-4076(01)00069-0](https://doi.org/10.1016%2FS0304-4076%2801%2900069-0).
86. Calvet, Laurent; Adlai Fisher (2004). "How to Forecast long-run volatility: regime-switching and the estimation of multifractal processes". *Journal of Financial Econometrics*. **2**: 49–83. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.536.8334](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.536.8334). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1093/jjfinec/nbh003](https://doi.org/10.1093%2Fjjfinec%2Fnbh003).
87. Brennan, Michael; Xiab, Yihong. ["Stock Price Volatility and the Equity Premium"](https://web.archive.org/web/20081228200849/http://bbs.cenet.org.cn/uploadImages/200352118122167693.pdf) (PDF). *Department of Finance, the Anderson School of Management, UCLA*. Archived from [the original](http://bbs.cenet.org.cn/uploadImages/200352118122167693.pdf) (PDF) on 2008-12-28.
88. ["A Markov Chain Example in Credit Risk Modelling"](https://web.archive.org/web/20160324112501/http://www.columbia.edu/~ww2040/4106S11/MC_BondRating.pdf) (PDF). *Columbia University*. Archived from [the original](http://www.columbia.edu/~ww2040/4106S11/MC_BondRating.pdf) (PDF) on March 24, 2016.
89. Acemoglu, Daron; Georgy Egorov; Konstantin Sonin (2011). ["Political model of social evolution"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3271566). *Proceedings of the National Academy of Sciences*. **108** (Suppl 4): 21292–21296. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2011PNAS..10821292A](https://ui.adsabs.harvard.edu/abs/2011PNAS..10821292A). [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.225.6090](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.225.6090). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1073/pnas.1019454108](https://doi.org/10.1073%2Fpnas.1019454108). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [3271566](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3271566). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [22198760](https://pubmed.ncbi.nlm.nih.gov/22198760).
90. K McAlpine; E Miranda; S Hoggar (1999). "Making Music with Algorithms: A Case-Study System". *Computer Music Journal*. **23** (2): 19–30. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1162/014892699559733](https://doi.org/10.1162%2F014892699559733).
91. Curtis Roads, ed. (1996). *The Computer Music Tutorial*. MIT Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-262-18158-7](https://en.wikipedia.org/wiki/Special:BookSources/978-0-262-18158-7).
92. Xenakis, Iannis; Kanach, Sharon (1992) *Formalized Music: Mathematics and Thought in Composition*, Pendragon Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [1576470792](https://en.wikipedia.org/wiki/Special:BookSources/1576470792)
93. ["Continuator"](https://web.archive.org/web/20120713235933/http://www.csl.sony.fr/~pachet/). Archived from [the original](http://www.csl.sony.fr/~pachet/) on July 13, 2012.
94. Pachet, F.; Roy, P.; Barbieri, G. (2011) ["Finite-Length Markov Processes with Constraints"](http://www.csl.sony.fr/downloads/papers/2011/pachet-11b.pdf) [Archived](https://web.archive.org/web/20120414183247/http://www.csl.sony.fr/downloads/papers/2011/pachet-11b.pdf) 2012-04-14 at the [Wayback Machine](https://en.wikipedia.org/wiki/Wayback_Machine), *Proceedings of the 22nd International Joint Conference on Artificial Intelligence*, IJCAI, pages 635–642, Barcelona, Spain, July 2011
95. Pankin, Mark D. ["MARKOV CHAIN MODELS: THEORETICAL BACKGROUND"](https://web.archive.org/web/20071209122054/http://www.pankin.com/markov/theory.htm). Archived from the original on 2007-12-09. Retrieved 2007-11-26.
96. Pankin, Mark D. ["BASEBALL AS A MARKOV CHAIN"](https://web.archive.org/web/20010513164045/http://www.pankin.com/markov/intro.htm). Archived from the original on May 13, 2001. Retrieved 2009-04-24.
97. ["Poet's Corner – Fieralingue"](https://web.archive.org/web/20101206043430/http://www.fieralingue.it/modules.php?name=Content&pa=list_pages_categories&cid=111). Archived from [the original](http://www.fieralingue.it/modules.php?name=Content&pa=list_pages_categories&cid=111) on December 6, 2010.
98. Kenner, Hugh; [O'Rourke, Joseph](https://en.wikipedia.org/wiki/Joseph_O%27Rourke_(professor) "Joseph O'Rourke (professor)") (November 1984). "A Travesty Generator for Micros". *BYTE*. **9** (12): 129–131, 449–469.
99. Hartman, Charles (1996). [Virtual Muse: Experiments in Computer Poetry](https://archive.org/details/virtualmuseexper00hart). Hanover, NH: Wesleyan University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8195-2239-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8195-2239-9).

## References

- A. A. Markov (1906) "Rasprostranenie zakona bol'shih chisel na velichiny, zavisyaschie drug ot druga". *Izvestiya Fiziko-matematicheskogo obschestva pri Kazanskom universitete*, 2-ya seriya, tom 15, pp. 135–156.
- A. A. Markov (1971). "Extension of the limit theorems of probability theory to a sum of variables connected in a chain". reprinted in Appendix B of: R. Howard. *Dynamic Probabilistic Systems, volume 1: Markov Chains*. John Wiley and Sons.
- Classical Text in Translation: Markov, A. A. (2006). "An Example of Statistical Investigation of the Text Eugene Onegin Concerning the Connection of Samples in Chains". *Science in Context*. **19** (4). Translated by Link, David: 591–600. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1017/s0269889706001074](https://doi.org/10.1017%2Fs0269889706001074).
- Leo Breiman (1992) \[1968\] *Probability*. Original edition published by Addison-Wesley; reprinted by [Society for Industrial and Applied Mathematics](https://en.wikipedia.org/wiki/Society_for_Industrial_and_Applied_Mathematics) [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-89871-296-3](https://en.wikipedia.org/wiki/Special:BookSources/0-89871-296-3). (See Chapter 7)
- [J. L. Doob](https://en.wikipedia.org/wiki/J._L._Doob) (1953) *Stochastic Processes*. New York: John Wiley and Sons [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-52369-0](https://en.wikipedia.org/wiki/Special:BookSources/0-471-52369-0).
- S. P. Meyn and R. L. Tweedie (1993) *Markov Chains and Stochastic Stability*. London: Springer-Verlag [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-19832-6](https://en.wikipedia.org/wiki/Special:BookSources/0-387-19832-6). online: [MCSS](https://web.archive.org/web/20100619010320/https://netfiles.uiuc.edu/meyn/www/spm_files/book.html) . Second edition to appear, Cambridge University Press, 2009.
- [Dynkin, Eugene Borisovich](https://en.wikipedia.org/wiki/Eugene_Borisovich_Dynkin) (1965). [Markov Processes](https://archive.org/details/markovprocesses0001dynk). Grundlehren der mathematischen Wissenschaften. Vol. I (121). Translated by Fabius, Jaap; Greenberg, Vida Lazarus; Maitra, Ashok Prasad; [Majone, Giandomenico](https://en.wikipedia.org/wiki/Giandomenico_Majone). Berlin: [Springer-Verlag](https://en.wikipedia.org/wiki/Springer-Verlag). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-3-662-00031-1](https://doi.org/10.1007%2F978-3-662-00031-1). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-662-00033-5](https://en.wikipedia.org/wiki/Special:BookSources/978-3-662-00033-5). Title-No. 5104.; [Markov Processes](https://archive.org/details/markovprocesses0002dynk). Grundlehren der mathematischen Wissenschaften. Vol. II (122). 1965. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-3-662-25360-1](https://doi.org/10.1007%2F978-3-662-25360-1). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-662-23320-7](https://en.wikipedia.org/wiki/Special:BookSources/978-3-662-23320-7). Title-No. 5105. (NB. This was originally published in Russian as Марковские процессы (*Markovskiye protsessy*) by [Fizmatgiz](https://en.wikipedia.org/wiki/Fizmatgiz) in 1963 and translated to English with the assistance of the author.)
- S. P. Meyn. *Control Techniques for Complex Networks*. Cambridge University Press, 2007. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-88441-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-88441-9). Appendix contains abridged Meyn & Tweedie. online: [CTCN](https://web.archive.org/web/20100619011046/https://netfiles.uiuc.edu/meyn/www/spm_files/CTCN/CTCN.html)
- Booth, Taylor L. (1967). *Sequential Machines and Automata Theory* (1st ed.). New York, NY: John Wiley and Sons, Inc. Library of Congress Card Catalog Number 67-25924. \] Extensive, wide-ranging book meant for specialists, written for both theoretical computer scientists as well as electrical engineers. With detailed explanations of state minimization techniques, FSMs, Turing machines, Markov processes, and undecidability. Excellent treatment of Markov processes pp. 449ff. Discusses Z-transforms, D transforms in their context.
- Kemeny, John G.; Hazleton Mirkil; J. Laurie Snell; Gerald L. Thompson (1959). [Finite Mathematical Structures](https://archive.org/details/finitemathematic0000keme_h5g0) (1st ed.). Englewood Cliffs, NJ: Prentice-Hall, Inc. Library of Congress Card Catalog Number 59-12841. Classical text. cf Chapter 6 *Finite Markov Chains* pp. 384ff.
- [John G. Kemeny](https://en.wikipedia.org/wiki/John_G._Kemeny) & [J. Laurie Snell](https://en.wikipedia.org/wiki/J._Laurie_Snell) (1960) *Finite Markov Chains*, D. van Nostrand Company [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-442-04328-7](https://en.wikipedia.org/wiki/Special:BookSources/0-442-04328-7)
- E. Nummelin. "General irreducible Markov chains and non-negative operators". Cambridge University Press, 1984, 2004. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-60494-X](https://en.wikipedia.org/wiki/Special:BookSources/0-521-60494-X)
- Seneta, E. *Non-negative matrices and Markov chains*. 2nd rev. ed., 1981, XVI, 288 p., Softcover Springer Series in Statistics. (Originally published by Allen & Unwin Ltd., London, 1973) [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-29765-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-29765-1)
- [Kishor S. Trivedi](https://en.wikipedia.org/wiki/Kishor_S._Trivedi), *Probability and Statistics with Reliability, Queueing, and Computer Science Applications*, John Wiley & Sons, Inc. New York, 2002. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-33341-7](https://en.wikipedia.org/wiki/Special:BookSources/0-471-33341-7).
- K. S. Trivedi and R.A.Sahner, *SHARPE at the age of twenty-two*, vol. 36, no. 4, pp. 52–57, ACM SIGMETRICS Performance Evaluation Review, 2009.
- R. A. Sahner, K. S. Trivedi and A. Puliafito, *Performance and reliability analysis of computer systems: an example-based approach using the SHARPE software package*, Kluwer Academic Publishers, 1996. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-7923-9650-2](https://en.wikipedia.org/wiki/Special:BookSources/0-7923-9650-2).
- G. Bolch, S. Greiner, H. de Meer and K. S. Trivedi, *Queueing Networks and Markov Chains*, John Wiley, 2nd edition, 2006. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-7923-9650-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-7923-9650-5).

## External links

- ["Markov chain"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society), 2001 \[1994\]
- [Markov Chains chapter in American Mathematical Society's introductory probability book](http://www.dartmouth.edu/~chance/teaching_aids/books_articles/probability_book/Chapter11.pdf) [Archived](https://web.archive.org/web/20080522131917/http://www.dartmouth.edu/~chance/teaching_aids/books_articles/probability_book/Chapter11.pdf) 2008-05-22 at the [Wayback Machine](https://en.wikipedia.org/wiki/Wayback_Machine)
- [Introduction to Markov Chains](https://www.youtube.com/watch?v=o-jdJxXL_W4) on [YouTube](https://en.wikipedia.org/wiki/YouTube_video_(identifier))
- [A visual explanation of Markov Chains](http://setosa.io/blog/2014/07/26/markov-chains/index.html)
- [Original paper by A.A Markov (1913): An Example of Statistical Investigation of the Text Eugene Onegin Concerning the Connection of Samples in Chains (translated from Russian)](http://www.alpha60.de/research/markov/DavidLink_AnExampleOfStatistical_MarkovTrans_2007.pdf)
