[[stochastic-processes.base]]

> Source: [[Hidden Markov Model]]
> License: Wikipedia content is available under CC BY-SA 4.0.

A **hidden Markov model** (**HMM**) is a [Markov model](https://en.wikipedia.org/wiki/Markov_model) in which the observations are dependent on a latent (or *hidden*) [Markov process](https://en.wikipedia.org/wiki/Markov_process) (referred to as $X$). An HMM requires that there be an observable process $Y$ whose outcomes depend on the outcomes of $X$ in a known way. Since $X$ cannot be observed directly, the goal is to learn about state of $X$ by observing $Y$. By definition of being a Markov model, an HMM has an additional requirement that the outcome of $Y$ at time $t=t_{0}$ must be "influenced" exclusively by the outcome of $X$ at $t=t_{0}$ and that the outcomes of $X$ and $Y$ at $t<t_{0}$ must be conditionally independent of $Y$ at $t=t_{0}$ given $X$ at time $t=t_{0}$. Estimation of the parameters in an HMM can be performed using [[Maximum Likelihood Estimation]]. For linear chain HMMs, the [Baum–Welch algorithm](https://en.wikipedia.org/wiki/Baum%E2%80%93Welch_algorithm) can be used to estimate parameters.

Hidden Markov models are known for their applications to [thermodynamics](https://en.wikipedia.org/wiki/Thermodynamics), [statistical mechanics](https://en.wikipedia.org/wiki/Statistical_mechanics), [physics](https://en.wikipedia.org/wiki/Physics), [chemistry](https://en.wikipedia.org/wiki/Chemistry), [economics](https://en.wikipedia.org/wiki/Economics), [finance](https://en.wikipedia.org/wiki/Finance), [signal processing](https://en.wikipedia.org/wiki/Signal_processing), [information theory](https://en.wikipedia.org/wiki/Information_theory), [pattern recognition](https://en.wikipedia.org/wiki/Pattern_recognition)—such as [speech recognition](https://en.wikipedia.org/wiki/Speech_recognition), [handwriting recognition](https://en.wikipedia.org/wiki/Handwriting_recognition), [gesture recognition](https://en.wikipedia.org/wiki/Gesture_recognition), [part-of-speech tagging](https://en.wikipedia.org/wiki/Part-of-speech_tagging), musical score following, [partial discharges](https://en.wikipedia.org/wiki/Partial_discharge) and [bioinformatics](https://en.wikipedia.org/wiki/Bioinformatics).

## Definition

Let $X_{n}$ and $Y_{n}$ be discrete-time [stochastic processes](https://en.wikipedia.org/wiki/Stochastic_process) and $n\geq 1$. The pair $(X_{n},Y_{n})$ is a *hidden Markov model* if

- $X_{n}$ is a [Markov process](https://en.wikipedia.org/wiki/Markov_process) whose behavior is not directly observable ("hidden");
- $\operatorname {\mathbf {P} } {\bigl (}Y_{n}\in A\ {\bigl |}\ X_{1}=x_{1},\ldots ,X_{n}=x_{n}{\bigr )}=\operatorname {\mathbf {P} } {\bigl (}Y_{n}\in A\ {\bigl |}\ X_{n}=x_{n}{\bigr )}$,

for every $n\geq 1$, $x_{1},\ldots ,x_{n}$, and every [Borel set](https://en.wikipedia.org/wiki/Borel_set) $A$.

Let $X_{t}$ and $Y_{t}$ be continuous-time stochastic processes. The pair $(X_{t},Y_{t})$ is a *hidden Markov model* if

- $X_{t}$ is a Markov process whose behavior is not directly observable ("hidden");
- $\operatorname {\mathbf {P} } (Y_{t_{0}}\in A\mid \{X_{t}\in B_{t}\}_{t\leq t_{0}})=\operatorname {\mathbf {P} } (Y_{t_{0}}\in A\mid X_{t_{0}}\in B_{t_{0}})$,

for every $t_{0}$, every Borel set $A$, and every family of Borel sets $\{B_{t}\}_{t\leq t_{0}}$.

### Terminology

The states of the process $X_{n}$ (resp. $X_{t})$ are called *hidden states*, and $\operatorname {\mathbf {P} } {\bigl (}Y_{n}\in A\mid X_{n}=x_{n}{\bigr )}$ (resp. $\operatorname {\mathbf {P} } {\bigl (}Y_{t}\in A\mid X_{t}\in B_{t}{\bigr )})$ is called *emission probability* or *output probability*.

## Examples

### Drawing balls from hidden urns

![[media/f85b8e36a494d24bc22895ebd24d8af711345430.png]]
Figure 1. Probabilistic parameters of a hidden Markov model (example)<br />
<em>X</em> — states<br />
<em>y</em> — possible observations<br />
<em>a</em> — state transition probabilities<br />
<em>b</em> — output probabilities

In its discrete form, a hidden Markov process can be visualized as a generalization of the [urn problem](https://en.wikipedia.org/wiki/Urn_problem) with replacement (where each item from the urn is returned to the original urn before the next step).

#### Consider this example

In a room that is not visible to an observer there is a genie. The room contains urns X1, X2, X3, ... each of which contains a known mix of balls, with each ball having a unique label y1, y2, y3, ... . The genie chooses an urn in that room and randomly draws a ball from that urn. It then puts the ball onto a conveyor belt, where the observer can observe the sequence of the balls but not the sequence of urns from which they were drawn.

The genie has some procedure to choose urns:

- The choice of the urn for the *n*-th ball depends only upon a random number and the choice of the urn for the (*n* − 1)-th ball.
- The choice of urn does not directly depend on the urns chosen before this single previous urn.

Therefore, this is called a [Markov process](https://en.wikipedia.org/wiki/Markov_process). It can be described by the upper part of Figure 1.

#### Markov process

The Markov process cannot be observed, only the sequence of labeled balls, thus this arrangement is called a *hidden Markov process*. This is illustrated by the lower part of the diagram shown in Figure 1, where one can see that balls y1, y2, y3, y4 can be drawn at each state. Even if the observer knows the composition of the urns and has just observed a sequence of three balls, *e.g.* y1, y2 and y3 on the conveyor belt, the observer still cannot be *sure* which urn (*i.e.*, at which state) the genie has drawn the third ball from. However, the observer can work out other information, such as the likelihood that the third ball came from each of the urns.

### Weather guessing game

Consider two friends, Alice and Bob, who live far apart from each other and who talk together daily over the telephone about what they did that day. Bob is only interested in three activities: walking in the park, shopping, and cleaning his apartment. The choice of what to do is determined exclusively by the weather on a given day. Alice has no definite information about the weather, but she knows general trends. Based on what Bob tells her he did each day, Alice tries to guess what the weather must have been like.

Alice believes that the weather operates as a discrete [[Markov Chain]]. There are two states, "Rainy" and "Sunny", but she cannot observe them directly, that is, they are *hidden* from her. On each day, there is a certain chance that Bob will perform one of the following activities, depending on the weather: "walk", "shop", or "clean". Since Bob tells Alice about his activities, those are the *observations*. The entire system is that of a hidden Markov model (HMM).

Alice knows the general weather trends in the area, and what Bob likes to do on average. In other words, the parameters of the HMM are known. They can be represented as follows in [Python](https://en.wikipedia.org/wiki/Python_programming_language):

    states = ("Rainy", "Sunny")

    observations = ("walk", "shop", "clean")

    start_probability = {"Rainy": 0.6, "Sunny": 0.4}

    transition_probability = {
        "Rainy": {"Rainy": 0.7, "Sunny": 0.3},
        "Sunny": {"Rainy": 0.4, "Sunny": 0.6},
    }

    emission_probability = {
        "Rainy": {"walk": 0.1, "shop": 0.4, "clean": 0.5},
        "Sunny": {"walk": 0.6, "shop": 0.3, "clean": 0.1},
    }

In this piece of code, `start_probability` represents Alice's belief about which state the HMM is in when Bob first calls her (all she knows is that it tends to be rainy on average). The particular probability distribution used here is not the equilibrium one, which is (given the transition probabilities) approximately `{'Rainy': 0.57, 'Sunny': 0.43}`. The `transition_probability` represents the change of the weather in the underlying Markov chain. In this example, there is only a 30% chance that tomorrow will be sunny if today is rainy. The `emission_probability` represents how likely Bob is to perform a certain activity on each day. If it is rainy, there is a 50% chance that he is cleaning his apartment; if it is sunny, there is a 60% chance that he is outside for a walk.

![[media/ee12ec5e1c977deca25bb4c9b73e7d1272e5c8ed.png]]
Graphical representation of the given HMM

*A similar example is further elaborated in the [Viterbi algorithm](https://en.wikipedia.org/wiki/Viterbi_algorithm#Example) page.*

## Structural architecture

The diagram below shows the general architecture of an instantiated HMM. Each oval shape represents a random variable that can adopt any of a number of values. The random variable *x*(*t*) is the hidden state at time t (with the model from the above diagram, *x*(*t*) ∈ {*x*<sub>1</sub>, *x*<sub>2</sub>, *x*<sub>3</sub>}). The random variable *y*(*t*) is the observation at time t (with *y*(*t*) ∈ {*y*<sub>1</sub>, *y*<sub>2</sub>, *y*<sub>3</sub>, *y*<sub>4</sub>}). The arrows in the diagram (often called a [trellis diagram](https://en.wikipedia.org/wiki/Trellis_(graph) "Trellis (graph)")) denote conditional dependencies.

From the diagram, it is clear that the [conditional probability distribution](https://en.wikipedia.org/wiki/Conditional_probability_distribution) of the hidden variable *x*(*t*) at time t, given the values of the hidden variable x at all times, depends *only* on the value of the hidden variable *x*(*t* − 1); the values at time *t* − 2 and before have no influence. This is called the [Markov property](https://en.wikipedia.org/wiki/Markov_property). Similarly, the value of the observed variable *y*(*t*) depends on only the value of the hidden variable *x*(*t*) (both at time t).

In the standard type of hidden Markov model considered here, the state space of the hidden variables is discrete, while the observations themselves can either be discrete (typically generated from a [categorical distribution](https://en.wikipedia.org/wiki/Categorical_distribution)) or continuous (typically from a [[Gaussian Distribution]]). The parameters of a hidden Markov model are of two types, *transition probabilities* and *emission probabilities* (also known as *output probabilities*). The transition probabilities control the way the hidden state at time t is chosen given the hidden state at time *t* − 1.

The hidden state space is assumed to consist of one of N possible values, modelled as a categorical distribution. (See the section below on extensions for other possibilities.) This means that for each of the N possible states that a hidden variable at time t can be in, there is a transition probability from this state to each of the N possible states of the hidden variable at time *t* + 1, for a total of $N^{2}$ transition probabilities. The set of transition probabilities for transitions from any given state must sum to 1. Thus, the *N* × *N* matrix of transition probabilities is a [Markov matrix](https://en.wikipedia.org/wiki/Stochastic_matrix). Because any transition probability can be determined once the others are known, there are a total of *N*(*N* − 1) transition parameters.

In addition, for each of the N possible states, there is a set of emission probabilities governing the distribution of the observed variable at a particular time given the state of the hidden variable at that time. The size of this set depends on the nature of the observed variable. For example, if the observed variable is discrete with M possible values, governed by a [categorical distribution](https://en.wikipedia.org/wiki/Categorical_distribution), there will be *M* − 1 separate parameters, for a total of *N*(*M* − 1) emission parameters over all hidden states. On the other hand, if the observed variable is an M-dimensional vector distributed according to an arbitrary [multivariate Gaussian distribution](https://en.wikipedia.org/wiki/Multivariate_Gaussian_distribution), there will be M parameters controlling the [means](https://en.wikipedia.org/wiki/Mean) and ${M(M+1)}/2$ parameters controlling the [covariance matrix](https://en.wikipedia.org/wiki/Covariance_matrix), for a total of $N\left(M+{M(M+1)}/{2}\right)={NM(M+3)}/2=O(NM^{2})$ emission parameters. (In such a case, unless the value of M is small, it may be more practical to restrict the nature of the covariances between individual elements of the observation vector, e.g. by assuming that the elements are independent of each other, or less restrictively, are independent of all but a fixed number of adjacent elements.)

![[media/cb80f8a1331b0efb2bbd3756c4c4fd8a71a38be9.png]]
Temporal evolution of a hidden Markov model

## Inference

![[media/332bcc0a9dfea514bf093ff3fe3b6fed88fcd0a8.png]]
The state transition and output probabilities of an HMM are indicated by the line opacity in the upper part of the diagram. Given that the output sequence is observed in the lower part of the diagram, interest occurs in the most likely sequence of states that could have produced it. Based on the arrows that are present in the diagram, the following state sequences are candidates:<br />
5 3 2 5 3 2<br />
4 3 2 5 3 2<br />
3 1 2 5 3 2<br />
The most likely sequence can be found by evaluating the joint probability of both the state sequence and the observations for each case (simply by multiplying the probability values, which here correspond to the opacities of the arrows involved). In general, this type of problem (i.e., finding the most likely explanation for an observation sequence) can be solved efficiently using the [Viterbi algorithm](https://en.wikipedia.org/wiki/Viterbi_algorithm).

Several [inference](https://en.wikipedia.org/wiki/Inference) problems are associated with hidden Markov models, as outlined below.

### Probability of an observed sequence

The task is to compute in a best way, given the parameters of the model, the probability of a particular output sequence. This requires summation over all possible state sequences:

The probability of observing a sequence

$Y=y(0),y(1),\dots ,y(L-1),$

of length *L* is given by

$P(Y)=\sum _{X}P(Y\mid X)P(X),$

where the sum runs over all possible hidden-node sequences

$X=x(0),x(1),\dots ,x(L-1).$

Applying the principle of [dynamic programming](https://en.wikipedia.org/wiki/Dynamic_programming), this problem, too, can be handled efficiently using the [forward algorithm](https://en.wikipedia.org/wiki/Forward_algorithm).

### Probability of the latent variables

A number of related tasks ask about the probability of one or more of the latent variables, given the model's parameters and a sequence of observations $y(1),\dots ,y(t)$.

#### Filtering

The task is to compute, given the model's parameters and a sequence of observations, the distribution over hidden states of the last latent variable at the end of the sequence, i.e. to compute $P(x(t)\mid y(1),\dots ,y(t))$. This task is used when the sequence of latent variables is thought of as the underlying states that a process moves through at a sequence of points in time, with corresponding observations at each point. Then, it is natural to ask about the state of the process at the end.

This problem can be handled efficiently using the [forward algorithm](https://en.wikipedia.org/wiki/Forward_algorithm). An example is when the algorithm is applied to a Hidden Markov Network to determine $\mathrm {P} {\big (}h_{t}\mid v_{1:t}{\big )}$.

#### Smoothing

This is similar to filtering but asks about the distribution of a latent variable somewhere in the middle of a sequence, i.e. to compute $P(x(k)\mid y(1),\dots ,y(t))$ for some $k<t$. From the perspective described above, this can be thought of as the probability distribution over hidden states for a point in time *k* in the past, relative to time *t*.

The [forward-backward algorithm](https://en.wikipedia.org/wiki/Forward-backward_algorithm) is a good method for computing the smoothed values for all hidden state variables.

#### Most likely explanation

The task, unlike the previous two, asks about the [joint probability](https://en.wikipedia.org/wiki/Joint_probability) of the *entire* sequence of hidden states that generated a particular sequence of observations (see illustration on the right). This task is generally applicable when HMM's are applied to different sorts of problems from those for which the tasks of filtering and smoothing are applicable. An example is [part-of-speech tagging](https://en.wikipedia.org/wiki/Part-of-speech_tagging), where the hidden states represent the underlying [parts of speech](https://en.wikipedia.org/wiki/Part-of-speech_tagging) corresponding to an observed sequence of words. In this case, what is of interest is the entire sequence of parts of speech, rather than simply the part of speech for a single word, as filtering or smoothing would compute.

This task requires finding a maximum over all possible state sequences, and can be solved efficiently by the [Viterbi algorithm](https://en.wikipedia.org/wiki/Viterbi_algorithm).

### Statistical significance

For some of the above problems, it may also be interesting to ask about [statistical significance](https://en.wikipedia.org/wiki/Statistical_significance). What is the probability that a sequence drawn from some [null distribution](https://en.wikipedia.org/wiki/Null_distribution) will have an HMM probability (in the case of the forward algorithm) or a maximum state sequence probability (in the case of the Viterbi algorithm) at least as large as that of a particular output sequence? When an HMM is used to evaluate the relevance of a hypothesis for a particular output sequence, the statistical significance indicates the [false positive rate](https://en.wikipedia.org/wiki/False_positive_rate) associated with failing to reject the hypothesis for the output sequence.

## Learning

The parameter learning task in HMMs is to find, given an output sequence or a set of such sequences, the best set of state transition and emission probabilities. The task is usually to derive the [maximum likelihood](https://en.wikipedia.org/wiki/Maximum_likelihood) estimate of the parameters of the HMM given the set of output sequences. No tractable algorithm is known for solving this problem exactly, but a local maximum likelihood can be derived efficiently using the [Baum–Welch algorithm](https://en.wikipedia.org/wiki/Baum%E2%80%93Welch_algorithm) or the Baldi–Chauvin algorithm. The Baum–Welch algorithm is a special case of the [expectation-maximization algorithm](https://en.wikipedia.org/wiki/Expectation-maximization_algorithm).

If the HMMs are used for time series prediction, more sophisticated Bayesian inference methods, like [[Markov Chain Monte Carlo]] (MCMC) sampling are proven to be favorable over finding a single maximum likelihood model both in terms of accuracy and stability. Since MCMC imposes significant computational burden, in cases where computational scalability is also of interest, one may alternatively resort to variational approximations to Bayesian inference, e.g. Indeed, approximate variational inference offers computational efficiency comparable to expectation-maximization, while yielding an accuracy profile only slightly inferior to exact MCMC-type Bayesian inference.

## Applications

![[media/020cf518ab2e8b71982a84526bb5022b80819ce4.png]]
A profile HMM modelling a multiple sequence alignment of proteins in [Pfam](https://en.wikipedia.org/wiki/Pfam)

HMMs can be applied in many fields where the goal is to recover a data sequence that is not immediately observable (but other data that depend on the sequence are). Applications include:

- [Computational finance](https://en.wikipedia.org/wiki/Computational_finance)
- [Single-molecule kinetic analysis](https://en.wikipedia.org/wiki/Single-molecule_experiment)
- [Neuroscience](https://en.wikipedia.org/wiki/Neuroscience)
- [Cryptanalysis](https://en.wikipedia.org/wiki/Cryptanalysis)
- [Speech recognition](https://en.wikipedia.org/wiki/Speech_recognition), including [Siri](https://en.wikipedia.org/wiki/Siri)
- [Speech synthesis](https://en.wikipedia.org/wiki/Speech_synthesis)
- [Part-of-speech tagging](https://en.wikipedia.org/wiki/Part-of-speech_tagging)
- Document separation in scanning solutions
- [Machine translation](https://en.wikipedia.org/wiki/Machine_translation)
- [Partial discharge](https://en.wikipedia.org/wiki/Partial_discharge)
- [Gene prediction](https://en.wikipedia.org/wiki/Gene_prediction)
- [Handwriting recognition](https://en.wikipedia.org/wiki/Handwriting_recognition)
- [Alignment of bio-sequences](https://en.wikipedia.org/wiki/Sequence_alignment)
- [Time series analysis](https://en.wikipedia.org/wiki/Time_series)
- [Activity recognition](https://en.wikipedia.org/wiki/Activity_recognition)
- [Protein folding](https://en.wikipedia.org/wiki/Protein_folding)
- Sequence classification
- [Sequence motif](https://en.wikipedia.org/wiki/Sequence_motif) discovery (DNA and [proteins](https://en.wikipedia.org/wiki/Protein))
- [DNA](https://en.wikipedia.org/wiki/DNA) hybridization kinetics
- [Chromatin](https://en.wikipedia.org/wiki/Chromatin) state discovery
- [Transportation forecasting](https://en.wikipedia.org/wiki/Transportation_forecasting)
- [Solar irradiance](https://en.wikipedia.org/wiki/Solar_irradiance) variability

## History

Hidden Markov models were described in a series of statistical papers by [Leonard E. Baum](https://en.wikipedia.org/wiki/Leonard_E._Baum) and other authors in the second half of the 1960s. One of the first applications of HMMs was [speech recognition](https://en.wikipedia.org/wiki/Speech_recognition), starting in the mid-1970s. From the linguistics point of view, hidden Markov models are equivalent to stochastic regular grammar.

In the second half of the 1980s, HMMs began to be applied to the analysis of biological sequences, in particular [DNA](https://en.wikipedia.org/wiki/DNA). Since then, they have become ubiquitous in the field of [bioinformatics](https://en.wikipedia.org/wiki/Bioinformatics).

## Extensions

### General state spaces

In the hidden Markov models considered above, the state space of the hidden variables is discrete, while the observations themselves can either be discrete (typically generated from a [categorical distribution](https://en.wikipedia.org/wiki/Categorical_distribution)) or continuous (typically from a [[Gaussian Distribution]]). Hidden Markov models can also be generalized to allow continuous state spaces. Examples of such models are those where the Markov process over hidden variables is a [linear dynamical system](https://en.wikipedia.org/wiki/Linear_dynamical_system), with a linear relationship among related variables and where all hidden and observed variables follow a [[Gaussian Distribution]]. In simple cases, such as the linear dynamical system just mentioned, exact inference is tractable (in this case, using the [Kalman filter](https://en.wikipedia.org/wiki/Kalman_filter)); however, in general, exact inference in HMMs with continuous latent variables is infeasible, and approximate methods must be used, such as the [extended Kalman filter](https://en.wikipedia.org/wiki/Extended_Kalman_filter) or the [particle filter](https://en.wikipedia.org/wiki/Particle_filter).

Nowadays, inference in hidden Markov models is performed in [nonparametric](https://en.wikipedia.org/wiki/Nonparametric_statistics) settings, where the dependency structure enables [identifiability](https://en.wikipedia.org/wiki/Identifiability) of the model and the learnability limits are still under exploration.

### Bayesian modeling of the transitions probabilities

Hidden Markov models are [generative models](https://en.wikipedia.org/wiki/Generative_model), in which the [joint distribution](https://en.wikipedia.org/wiki/Joint_distribution) of observations and hidden states, or equivalently both the [prior distribution](https://en.wikipedia.org/wiki/Prior_distribution) of hidden states (the *transition probabilities*) and [conditional distribution](https://en.wikipedia.org/wiki/Conditional_distribution) of observations given states (the *emission probabilities*), is modeled. The above algorithms implicitly assume a [uniform](https://en.wikipedia.org/wiki/Uniform_distribution_(continuous)) prior distribution over the transition probabilities. However, it is also possible to create hidden Markov models with other types of prior distributions. An obvious candidate, given the categorical distribution of the transition probabilities, is the [Dirichlet distribution](https://en.wikipedia.org/wiki/Dirichlet_distribution), which is the [conjugate prior](https://en.wikipedia.org/wiki/Conjugate_prior) distribution of the categorical distribution. Typically, a symmetric Dirichlet distribution is chosen, reflecting ignorance about which states are inherently more likely than others. The single parameter of this distribution (termed the *concentration parameter*) controls the relative density or sparseness of the resulting transition matrix. A choice of 1 yields a uniform distribution. Values greater than 1 produce a dense matrix, in which the transition probabilities between pairs of states are likely to be nearly equal. Values less than 1 result in a sparse matrix in which, for each given source state, only a small number of destination states have non-negligible transition probabilities. It is also possible to use a two-level prior Dirichlet distribution, in which one Dirichlet distribution (the upper distribution) governs the parameters of another Dirichlet distribution (the lower distribution), which in turn governs the transition probabilities. The upper distribution governs the overall distribution of states, determining how likely each state is to occur; its concentration parameter determines the density or sparseness of states. Such a two-level prior distribution, where both concentration parameters are set to produce sparse distributions, might be useful for example in [unsupervised](https://en.wikipedia.org/wiki/Unsupervised_learning) [part-of-speech tagging](https://en.wikipedia.org/wiki/Part-of-speech_tagging), where some parts of speech occur much more commonly than others; learning algorithms that assume a uniform prior distribution generally perform poorly on this task. The parameters of models of this sort, with non-uniform prior distributions, can be learned using [[Gibbs Sampling]] or extended versions of the [expectation-maximization algorithm](https://en.wikipedia.org/wiki/Expectation-maximization_algorithm).

An extension of the previously described hidden Markov models with [Dirichlet](https://en.wikipedia.org/wiki/Dirichlet_distribution) priors uses a [Dirichlet process](https://en.wikipedia.org/wiki/Dirichlet_process) in place of a Dirichlet distribution. This type of model allows for an unknown and potentially infinite number of states. It is common to use a two-level Dirichlet process, similar to the previously described model with two levels of Dirichlet distributions. Such a model is called a *hierarchical Dirichlet process hidden Markov model*, or *HDP-HMM* for short. It was originally described under the name "Infinite Hidden Markov Model" and was further formalized in "Hierarchical Dirichlet Processes".

### Discriminative approach

A different type of extension uses a [discriminative model](https://en.wikipedia.org/wiki/Discriminative_model) in place of the [generative model](https://en.wikipedia.org/wiki/Generative_model) of standard HMMs. This type of model directly models the conditional distribution of the hidden states given the observations, rather than modeling the joint distribution. An example of this model is the so-called *[maximum entropy Markov model](https://en.wikipedia.org/wiki/Maximum_entropy_Markov_model)* (MEMM), which models the conditional distribution of the states using [logistic regression](https://en.wikipedia.org/wiki/Logistic_regression) (also known as a "[maximum entropy](https://en.wikipedia.org/wiki/Maximum_entropy_probability_distribution) model"). The advantage of this type of model is that arbitrary features (i.e. functions) of the observations can be modeled, allowing domain-specific knowledge of the problem at hand to be injected into the model. Models of this sort are not limited to modeling direct dependencies between a hidden state and its associated observation; rather, features of nearby observations, of combinations of the associated observation and nearby observations, or in fact of arbitrary observations at any distance from a given hidden state can be included in the process used to determine the value of a hidden state. Furthermore, there is no need for these features to be [statistically independent](https://en.wikipedia.org/wiki/Statistically_independent) of each other, as would be the case if such features were used in a generative model. Finally, arbitrary features over pairs of adjacent hidden states can be used rather than simple transition probabilities. The disadvantages of such models are: (1) The types of prior distributions that can be placed on hidden states are severely limited; (2) It is not possible to predict the probability of seeing an arbitrary observation. This second limitation is often not an issue in practice, since many common usages of HMM's do not require such predictive probabilities.

A variant of the previously described discriminative model is the linear-chain [conditional random field](https://en.wikipedia.org/wiki/Conditional_random_field). This uses an undirected graphical model (aka [Markov random field](https://en.wikipedia.org/wiki/Markov_random_field)) rather than the directed graphical models of MEMM's and similar models. The advantage of this type of model is that it does not suffer from the so-called *label bias* problem of MEMM's, and thus may make more accurate predictions. The disadvantage is that training can be slower than for MEMM's.

### Other extensions

Yet another variant is the *factorial hidden Markov model*, which allows for a single observation to be conditioned on the corresponding hidden variables of a set of $K$ independent Markov chains, rather than a single Markov chain. It is equivalent to a single HMM, with $N^{K}$ states (assuming there are $N$ states for each chain), and therefore, learning in such a model is difficult: for a sequence of length $T$, a straightforward Viterbi algorithm has complexity $O(N^{2K}\,T)$. To find an exact solution, a junction tree algorithm could be used, but it results in an $O(N^{K+1}\,K\,T)$ complexity. In practice, approximate techniques, such as variational approaches, could be used.

All of the above models can be extended to allow for more distant dependencies among hidden states, e.g. allowing for a given state to be dependent on the previous two or three states rather than a single previous state; i.e. the transition probabilities are extended to encompass sets of three or four adjacent states (or in general $K$ adjacent states). The disadvantage of such models is that dynamic-programming algorithms for training them have an $O(N^{K}\,T)$ running time, for $K$ adjacent states and $T$ total observations (i.e. a length-$T$ Markov chain). This extension has been widely used in [bioinformatics](https://en.wikipedia.org/wiki/Bioinformatics), in the modeling of [DNA sequences](https://en.wikipedia.org/wiki/Nucleic_acid_sequence).

Another recent extension is the *triplet Markov model*, in which an auxiliary underlying process is added to model some data specificities. Many variants of this model have been proposed. One should also mention the interesting link that has been established between the *theory of evidence* and the *triplet Markov models* and which allows to fuse data in Markovian context and to model nonstationary data. Alternative multi-stream data fusion strategies have also been proposed in recent literature, e.g.,

Finally, a different rationale towards addressing the problem of modeling nonstationary data by means of hidden Markov models was suggested in 2012. It consists in employing a small recurrent neural network (RNN), specifically a reservoir network, to capture the evolution of the temporal dynamics in the observed data. This information, encoded in the form of a high-dimensional vector, is used as a conditioning variable of the HMM state transition probabilities. Under such a setup, eventually is obtained a nonstationary HMM, the transition probabilities of which evolve over time in a manner that is inferred from the data, in contrast to some unrealistic ad-hoc model of temporal evolution.

In 2023, two innovative algorithms were introduced for the Hidden Markov Model. These algorithms enable the computation of the posterior distribution of the HMM without the necessity of explicitly modeling the joint distribution, utilizing only the conditional distributions. Unlike traditional methods such as the Forward-Backward and Viterbi algorithms, which require knowledge of the joint law of the HMM and can be computationally intensive to learn, the Discriminative Forward-Backward and Discriminative Viterbi algorithms circumvent the need for the observation's law. This breakthrough allows the HMM to be applied as a discriminative model, offering a more efficient and versatile approach to leveraging Hidden Markov Models in various applications.

The model suitable in the context of longitudinal data is named latent Markov model. The basic version of this model has been extended to include individual covariates, random effects and to model more complex data structures such as multilevel data. A complete overview of the latent Markov models, with special attention to the model assumptions and to their practical use is provided in

## Measure theory

![[media/be8799c852550c4a818a9e752f93d88bcd6a501d.png]]
The hidden part of a hidden Markov model, whose observable states is non-Markovian

Given a Markov transition matrix and an invariant distribution on the states, a probability measure can be imposed on the set of subshifts. For example, consider the Markov chain given on the left on the states $A,B_{1},B_{2}$, with invariant distribution $\pi =(2/7,4/7,1/7)$. By ignoring the distinction between $B_{1},B_{2}$, this space of subshifts is projected on $A,B_{1},B_{2}$ into another space of subshifts on $A,B$, and this projection also projects the probability measure down to a probability measure on the subshifts on $A,B$.

The curious thing is that the probability measure on the subshifts on $A,B$ is not created by a Markov chain on $A,B$, not even multiple orders. Intuitively, this is because if one observes a long sequence of $B^{n}$, then one would become increasingly sure that the $\Pr(A\mid B^{n})\to {\frac {2}{3}}$, meaning that the observable part of the system can be affected by something infinitely in the past.

Conversely, there exists a space of subshifts on 6 symbols, projected to subshifts on 2 symbols, such that any Markov measure on the smaller subshift has a preimage measure that is not Markov of any order (example 2.6).

## See also

- [Andrey Markov](https://en.wikipedia.org/wiki/Andrey_Markov)
- [Baum–Welch algorithm](https://en.wikipedia.org/wiki/Baum%E2%80%93Welch_algorithm)
- [Bayesian inference](https://en.wikipedia.org/wiki/Bayesian_inference)
- [Bayesian programming](https://en.wikipedia.org/wiki/Bayesian_programming)
- [Richard James Boys](https://en.wikipedia.org/wiki/Richard_James_Boys)
- [Conditional random field](https://en.wikipedia.org/wiki/Conditional_random_field)
- [Estimation theory](https://en.wikipedia.org/wiki/Estimation_theory)
- [HH-suite](https://en.wikipedia.org/wiki/HH-suite) (HHpred, HHsearch) free server and software for protein sequence searching
- [HMMER](https://en.wikipedia.org/wiki/HMMER), a free hidden Markov model program for protein sequence analysis
- [Hidden Bernoulli model](https://en.wikipedia.org/wiki/Hidden_Bernoulli_model)
- [Hidden semi-Markov model](https://en.wikipedia.org/wiki/Hidden_semi-Markov_model)
- [Hierarchical hidden Markov model](https://en.wikipedia.org/wiki/Hierarchical_hidden_Markov_model)
- [Layered hidden Markov model](https://en.wikipedia.org/wiki/Layered_hidden_Markov_model)
- [Sequential dynamical system](https://en.wikipedia.org/wiki/Sequential_dynamical_system)
- [Stochastic context-free grammar](https://en.wikipedia.org/wiki/Stochastic_context-free_grammar)
- [Time series](https://en.wikipedia.org/wiki/Time_series) analysis
- [Variable-order Markov model](https://en.wikipedia.org/wiki/Variable-order_Markov_model)
- [Viterbi algorithm](https://en.wikipedia.org/wiki/Viterbi_algorithm)

## References

1.  ["Google Scholar"](https://scholar.google.com/scholar?q=levinson+hidden+markov+model+tutorial&hl=en&as_sdt=0&as_vis=1&oi=scholart).
2.  Thad Starner, Alex Pentland. [Real-Time American Sign Language Visual Recognition From Video Using Hidden Markov Models](http://www.cc.gatech.edu/~thad/p/031_10_SL/real-time-asl-recognition-from%20video-using-hmm-ISCV95.pdf). Master's Thesis, MIT, Feb 1995, Program in Media Arts
3.  B. Pardo and W. Birmingham. [Modeling Form for On-line Following of Musical Performances](http://www.cs.northwestern.edu/~pardo/publications/pardo-birmingham-aaai-05.pdf) [Archived](https://web.archive.org/web/20120206123155/http://www.cs.northwestern.edu/~pardo/publications/pardo-birmingham-aaai-05.pdf) 2012-02-06 at the [Wayback Machine](https://en.wikipedia.org/wiki/Wayback_Machine). AAAI-05 Proc., July 2005.
4.  Satish L, Gururaj BI (April 2003). "[Use of hidden Markov models for partial discharge pattern classification](https://ieeexplore.ieee.org/document/212242/;jsessionid=F905BAE29AD4A7BD5B228B4734549DA2?arnumber=212242)". *[IEEE Transactions on Dielectrics and Electrical Insulation](https://en.wikipedia.org/wiki/IEEE_Transactions_on_Dielectrics_and_Electrical_Insulation)*.
5.  Li, N; Stephens, M (December 2003). ["Modeling linkage disequilibrium and identifying recombination hotspots using single-nucleotide polymorphism data"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1462870). *Genetics*. **165** (4): 2213–33. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1093/genetics/165.4.2213](https://doi.org/10.1093%2Fgenetics%2F165.4.2213). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [1462870](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1462870). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [14704198](https://pubmed.ncbi.nlm.nih.gov/14704198).
6.  Ernst, Jason; Kellis, Manolis (March 2012). ["ChromHMM: automating chromatin-state discovery and characterization"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3577932). *Nature Methods*. **9** (3): 215–216. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1038/nmeth.1906](https://doi.org/10.1038%2Fnmeth.1906). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [3577932](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3577932). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [22373907](https://pubmed.ncbi.nlm.nih.gov/22373907).
7.  [Lawrence R. Rabiner](https://en.wikipedia.org/wiki/Lawrence_Rabiner) (February 1989). ["A tutorial on Hidden Markov Models and selected applications in speech recognition"](http://www.ece.ucsb.edu/Faculty/Rabiner/ece259/Reprints/tutorial%20on%20hmm%20and%20applications.pdf) (PDF). *Proceedings of the IEEE*. **77** (2): 257–286. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.381.3454](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.381.3454). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/5.18626](https://doi.org/10.1109%2F5.18626). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [13618539](https://api.semanticscholar.org/CorpusID:13618539). [1](https://en.wikipedia.org/wiki/1)(https://www.cs.cornell.edu/courses/cs481/2004fa/rabiner.pdf)
8.  Newberg, Lee A. (2009). ["Error statistics of hidden Markov model and hidden Boltzmann model results"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2722652). *BMC Bioinformatics*. **10** 212. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1186/1471-2105-10-212](https://doi.org/10.1186%2F1471-2105-10-212). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [2722652](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2722652). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [19589158](https://pubmed.ncbi.nlm.nih.gov/19589158). [![[media/47082a85cea4c86996941639845d2e97a32f25de.png]]](https://en.wikipedia.org/wiki/Open_access "open access publication – free to read")
9.  Sipos, I. Róbert. *Parallel stratified MCMC sampling of AR-HMMs for stochastic time series prediction*. In: Proceedings, 4th Stochastic Modeling Techniques and Data Analysis International Conference with Demographics Workshop (SMTDA2016), pp. 295-306. Valletta, 2016. [PDF](http://1drv.ms/b/s!ApL_0Av0YGDLglwEOv1aYAGbmQeL)
10. Chatzis, Sotirios P.; Kosmopoulos, Dimitrios I. (2011). ["A variational Bayesian methodology for hidden Markov models utilizing Student's-t mixtures"](https://web.archive.org/web/20110401184517/http://users.iit.demokritos.gr/~dkosmo/downloads/patrec10/vbb10.pdf) (PDF). *Pattern Recognition*. **44** (2): 295–306. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2011PatRe..44..295C](https://ui.adsabs.harvard.edu/abs/2011PatRe..44..295C). [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.629.6275](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.629.6275). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.patcog.2010.09.001](https://doi.org/10.1016%2Fj.patcog.2010.09.001). Archived from [the original](http://users.iit.demokritos.gr/~dkosmo/downloads/patrec10/vbb10.pdf) (PDF) on 2011-04-01. Retrieved 2018-03-11.
11. Sipos, I. Róbert; Ceffer, Attila; Levendovszky, János (2016). "Parallel Optimization of Sparse Portfolios with AR-HMMs". *Computational Economics*. **49** (4): 563–578. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s10614-016-9579-y](https://doi.org/10.1007%2Fs10614-016-9579-y). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [61882456](https://api.semanticscholar.org/CorpusID:61882456).
12. Petropoulos, Anastasios; Chatzis, Sotirios P.; Xanthopoulos, Stylianos (2016). "A novel corporate credit rating system based on Student's-t hidden Markov models". *Expert Systems with Applications*. **53**: 87–105. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.eswa.2016.01.015](https://doi.org/10.1016%2Fj.eswa.2016.01.015).
13. Nicolai, Christopher (2013). "Solving Ion Channel Kinetics with the QuB Software". *Biophysical Reviews and Letters*. **8** (3n04): 191–211. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1142/S1793048013300053](https://doi.org/10.1142%2FS1793048013300053).
14. Higgins, Cameron; Vidaurre, Diego; Kolling, Nils; Liu, Yunzhe; Behrens, Tim; Woolrich, Mark (2022). ["Spatiotemporally Resolved Multivariate Pattern Analysis for M/EEG"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9188977). *Human Brain Mapping*. **43** (10): 3062–3085. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1002/hbm.25835](https://doi.org/10.1002%2Fhbm.25835). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [9188977](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9188977). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [35302683](https://pubmed.ncbi.nlm.nih.gov/35302683).
15. Diomedi, S.; Vaccari, F. E.; Galletti, C.; Hadjidimitrakis, K.; Fattori, P. (2021-10-01). ["Motor-like neural dynamics in two parietal areas during arm reaching"](https://www.sciencedirect.com/science/article/pii/S0301008221001301). *Progress in Neurobiology*. **205** 102116. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.pneurobio.2021.102116](https://doi.org/10.1016%2Fj.pneurobio.2021.102116). [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[11585/834094](https://hdl.handle.net/11585%2F834094). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0301-0082](https://search.worldcat.org/issn/0301-0082). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [34217822](https://pubmed.ncbi.nlm.nih.gov/34217822). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [235703641](https://api.semanticscholar.org/CorpusID:235703641).
16. Domingos, Pedro (2015). [The Master Algorithm: How the Quest for the Ultimate Learning Machine Will Remake Our World](https://archive.org/details/masteralgorithmh0000domi). Basic Books. p. [37](https://archive.org/details/masteralgorithmh0000domi/page/37). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-465-06192-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-465-06192-1).
17. Kundu, Amlan, Yang He, and Paramvir Bahl. "[Recognition of handwritten word: first and second order hidden Markov model based approach](https://www.academia.edu/download/48589949/0031-3203_2889_2990076-920160905-24541-r9o2lm.pdf)<sup>\[*[dead link](https://en.wikipedia.org/wiki/Wikipedia:Link_rot)*\]</sup>." Pattern recognition 22.3 (1989): 283-297.
18. Stigler, J.; Ziegler, F.; Gieseke, A.; Gebhardt, J. C. M.; Rief, M. (2011). ["The Complex Folding Network of Single Calmodulin Molecules"](https://archive.org/details/sim_science_2011-10-28_334_6055/page/512). *[Science](https://en.wikipedia.org/wiki/Science_(journal) "Science (journal)")*. **334** (6055): 512–516. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2011Sci...334..512S](https://ui.adsabs.harvard.edu/abs/2011Sci...334..512S). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1126/science.1207598](https://doi.org/10.1126%2Fscience.1207598). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [22034433](https://pubmed.ncbi.nlm.nih.gov/22034433). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [5502662](https://api.semanticscholar.org/CorpusID:5502662).
19. Blasiak, S.; Rangwala, H. (2011). "A Hidden Markov Model Variant for Sequence Classification". *IJCAI Proceedings-International Joint Conference on Artificial Intelligence*. **22**: 1192.
20. Wong, W.; Stamp, M. (2006). "Hunting for metamorphic engines". *Journal in Computer Virology*. **2** (3): 211–229. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s11416-006-0028-7](https://doi.org/10.1007%2Fs11416-006-0028-7). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [8116065](https://api.semanticscholar.org/CorpusID:8116065).
21. Wong, K. -C.; Chan, T. -M.; Peng, C.; Li, Y.; Zhang, Z. (2013). ["DNA motif elucidation using belief propagation"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3763557). *Nucleic Acids Research*. **41** (16): e153. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1093/nar/gkt574](https://doi.org/10.1093%2Fnar%2Fgkt574). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [3763557](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3763557). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [23814189](https://pubmed.ncbi.nlm.nih.gov/23814189).
22. Shah, Shalin; Dubey, Abhishek K.; Reif, John (2019-05-17). "Improved Optical Multiplexing with Temporal DNA Barcodes". *ACS Synthetic Biology*. **8** (5): 1100–1111. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1021/acssynbio.9b00010](https://doi.org/10.1021%2Facssynbio.9b00010). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [30951289](https://pubmed.ncbi.nlm.nih.gov/30951289). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [96448257](https://api.semanticscholar.org/CorpusID:96448257).
23. Shah, Shalin; Dubey, Abhishek K.; Reif, John (2019-04-10). "Programming Temporal DNA Barcodes for Single-Molecule Fingerprinting". *Nano Letters*. **19** (4): 2668–2673. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2019NanoL..19.2668S](https://ui.adsabs.harvard.edu/abs/2019NanoL..19.2668S). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1021/acs.nanolett.9b00590](https://doi.org/10.1021%2Facs.nanolett.9b00590). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1530-6984](https://search.worldcat.org/issn/1530-6984). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [30896178](https://pubmed.ncbi.nlm.nih.gov/30896178). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [84841635](https://api.semanticscholar.org/CorpusID:84841635).
24. ["ChromHMM: Chromatin state discovery and characterization"](http://compbio.mit.edu/ChromHMM/). *compbio.mit.edu*. Retrieved 2018-08-01.
25. El Zarwi, Feraz (May 2011). "Modeling and Forecasting the Evolution of Preferences over Time: A Hidden Markov Model of Travel Behavior". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1707.09133](https://arxiv.org/abs/1707.09133) \[[stat.AP](https://arxiv.org/archive/stat.AP)\].
26. Morf, H. (Feb 1998). "The stochastic two-state solar irradiance model (STSIM)". *Solar Energy*. **62** (2): 101–112. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1998SoEn...62..101M](https://ui.adsabs.harvard.edu/abs/1998SoEn...62..101M). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/S0038-092X(98)00004-8](https://doi.org/10.1016%2FS0038-092X%2898%2900004-8).
27. Munkhammar, J.; Widén, J. (Aug 2018). "A Markov-chain probability distribution mixture approach to the clear-sky index". *Solar Energy*. **170**: 174–183. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2018SoEn..170..174M](https://ui.adsabs.harvard.edu/abs/2018SoEn..170..174M). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.solener.2018.05.055](https://doi.org/10.1016%2Fj.solener.2018.05.055). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [125867684](https://api.semanticscholar.org/CorpusID:125867684).
28. Munkhammar, J.; Widén, J. (Oct 2018). "An N-state Markov-chain mixture distribution model of the clear-sky index". *Solar Energy*. **173**: 487–495. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2018SoEn..173..487M](https://ui.adsabs.harvard.edu/abs/2018SoEn..173..487M). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.solener.2018.07.056](https://doi.org/10.1016%2Fj.solener.2018.07.056). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [125538244](https://api.semanticscholar.org/CorpusID:125538244).
29. Baum, L. E.; Petrie, T. (1966). ["Statistical Inference for Probabilistic Functions of Finite State Markov Chains"](https://doi.org/10.1214%2Faoms%2F1177699147). *The Annals of Mathematical Statistics*. **37** (6): 1554–1563. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/aoms/1177699147](https://doi.org/10.1214%2Faoms%2F1177699147).
30. Baum, L. E.; Eagon, J. A. (1967). ["An inequality with applications to statistical estimation for probabilistic functions of Markov processes and to a model for ecology"](http://projecteuclid.org/euclid.bams/1183528841). *[Bulletin of the American Mathematical Society](https://en.wikipedia.org/wiki/Bulletin_of_the_American_Mathematical_Society)*. **73** (3): 360. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1090/S0002-9904-1967-11751-8](https://doi.org/10.1090%2FS0002-9904-1967-11751-8). [Zbl](https://en.wikipedia.org/wiki/Zbl_(identifier)) [0157.11101](https://zbmath.org/?format=complete&q=an:0157.11101).
31. Baum, L. E.; Sell, G. R. (1968). ["Growth transformations for functions on manifolds"](https://doi.org/10.2140%2Fpjm.1968.27.211). *Pacific Journal of Mathematics*. **27** (2): 211–227. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2140/pjm.1968.27.211](https://doi.org/10.2140%2Fpjm.1968.27.211).
32. [Baum, L. E.](https://en.wikipedia.org/wiki/Leonard_E._Baum); Petrie, T.; Soules, G.; Weiss, N. (1970). ["A Maximization Technique Occurring in the Statistical Analysis of Probabilistic Functions of Markov Chains"](https://doi.org/10.1214%2Faoms%2F1177697196). *[The Annals of Mathematical Statistics](https://en.wikipedia.org/wiki/The_Annals_of_Mathematical_Statistics)*. **41** (1): 164–171. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/aoms/1177697196](https://doi.org/10.1214%2Faoms%2F1177697196). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2239727](https://www.jstor.org/stable/2239727). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0287613](https://mathscinet.ams.org/mathscinet-getitem?mr=0287613). [Zbl](https://en.wikipedia.org/wiki/Zbl_(identifier)) [0188.49603](https://zbmath.org/?format=complete&q=an:0188.49603).
33. Baum, L.E. (1972). "An Inequality and Associated Maximization Technique in Statistical Estimation of Probabilistic Functions of a Markov Process". *Inequalities*. **3**: 1–8.
34. [Baker, J.](https://en.wikipedia.org/wiki/James_K._Baker) (1975). "The DRAGON system—An overview". *IEEE Transactions on Acoustics, Speech, and Signal Processing*. **23**: 24–29. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/TASSP.1975.1162650](https://doi.org/10.1109%2FTASSP.1975.1162650).
35. Jelinek, F.; Bahl, L.; Mercer, R. (1975). "Design of a linguistic statistical decoder for the recognition of continuous speech". *[IEEE Transactions on Information Theory](https://en.wikipedia.org/wiki/IEEE_Transactions_on_Information_Theory)*. **21** (3): 250. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/TIT.1975.1055384](https://doi.org/10.1109%2FTIT.1975.1055384).
36. [Xuedong Huang](https://en.wikipedia.org/wiki/Xuedong_Huang); M. Jack; Y. Ariki (1990). [Hidden Markov Models for Speech Recognition](https://archive.org/details/hiddenmarkovmode0000huan). Edinburgh University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-7486-0162-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-7486-0162-2).
37. [Xuedong Huang](https://en.wikipedia.org/wiki/Xuedong_Huang); Alex Acero; Hsiao-Wuen Hon (2001). *Spoken Language Processing*. Prentice Hall. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-13-022616-7](https://en.wikipedia.org/wiki/Special:BookSources/978-0-13-022616-7).
38. Carrasco, Rafael C.; Oncina, Jose (1994). ["Learning stochastic regular grammars by means of a state merging method"](https://link.springer.com/chapter/10.1007/3-540-58473-0_144). In Carrasco, Rafael C.; Oncina, Jose (eds.). *Grammatical Inference and Applications*. Lecture Notes in Computer Science. Vol. 862. Berlin, Heidelberg: Springer. pp. 139–152. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/3-540-58473-0_144](https://doi.org/10.1007%2F3-540-58473-0_144). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-48985-6](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-48985-6).
39. M. Bishop and E. Thompson (1986). "Maximum Likelihood Alignment of DNA Sequences". *[Journal of Molecular Biology](https://en.wikipedia.org/wiki/Journal_of_Molecular_Biology)*. **190** (2): 159–165. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/0022-2836(86)90289-5](https://doi.org/10.1016%2F0022-2836%2886%2990289-5). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [3641921](https://pubmed.ncbi.nlm.nih.gov/3641921). (subscription required) [![[media/fac34b201314b94609475134139fa0ead0b26433.png]]](https://en.wikipedia.org/wiki/Paywall "closed access publication – behind paywall")
40. [Durbin, Richard M.](https://en.wikipedia.org/wiki/Richard_M._Durbin); [Eddy, Sean R.](https://en.wikipedia.org/wiki/Sean_Eddy); [Krogh, Anders](https://en.wikipedia.org/wiki/Anders_Krogh); Mitchison, Graeme (1998), [Biological Sequence Analysis: Probabilistic Models of Proteins and Nucleic Acids](http://www.cambridge.org/gb/knowledge/isbn/item1158701) (1st ed.), Cambridge, New York: [Cambridge University Press](https://en.wikipedia.org/wiki/Cambridge_University_Press), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-62971-3](https://en.wikipedia.org/wiki/Special:BookSources/0-521-62971-3), [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [593254083](https://search.worldcat.org/oclc/593254083)
41. Gassiat, E.; Cleynen, A.; Robin, S. (2016-01-01). "Inference in finite state space non parametric Hidden Markov Models and applications". *Statistics and Computing*. **26** (1): 61–71. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s11222-014-9523-8](https://doi.org/10.1007%2Fs11222-014-9523-8). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1573-1375](https://search.worldcat.org/issn/1573-1375).
42. Abraham, Kweku; Gassiat, Elisabeth; Naulet, Zacharie (March 2023). "Fundamental Limits for Learning Hidden Markov Model Parameters". *IEEE Transactions on Information Theory*. **69** (3): 1777–1794. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2106.12936](https://arxiv.org/abs/2106.12936). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2023ITIT...69.1777A](https://ui.adsabs.harvard.edu/abs/2023ITIT...69.1777A). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/TIT.2022.3213429](https://doi.org/10.1109%2FTIT.2022.3213429). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0018-9448](https://search.worldcat.org/issn/0018-9448).
43. Beal, Matthew J., Zoubin Ghahramani, and Carl Edward Rasmussen. "The infinite hidden Markov model." Advances in neural information processing systems 14 (2002): 577-584.
44. Teh, Yee Whye, et al. "Hierarchical dirichlet processes." Journal of the American Statistical Association 101.476 (2006).
45. [Ghahramani, Zoubin](https://en.wikipedia.org/wiki/Zoubin_Ghahramani); [Jordan, Michael I.](https://en.wikipedia.org/wiki/Michael_I._Jordan) (1997). ["Factorial Hidden Markov Models"](https://doi.org/10.1023%2FA%3A1007425814087). *[Machine Learning](https://en.wikipedia.org/wiki/Machine_Learning_(journal) "Machine Learning (journal)")*. **29** (2/3): 245–273. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1023/A:1007425814087](https://doi.org/10.1023%2FA%3A1007425814087).
46. Pieczynski, Wojciech (2002). ["Chaı̂nes de Markov Triplet"](http://www.numdam.org/item/10.1016/S1631-073X(02)02462-7.pdf) (PDF). *Comptes Rendus Mathématique*. **335** (3): 275–278. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/S1631-073X(02)02462-7](https://doi.org/10.1016%2FS1631-073X%2802%2902462-7).
47. Pieczynski, Wojciech (2007). ["Multisensor triplet Markov chains and theory of evidence"](https://doi.org/10.1016%2Fj.ijar.2006.05.001). *International Journal of Approximate Reasoning*. **45**: 1–16. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.ijar.2006.05.001](https://doi.org/10.1016%2Fj.ijar.2006.05.001).
48. [Boudaren et al.](http://asp.eurasipjournals.com/content/pdf/1687-6180-2012-134.pdf) [Archived](https://web.archive.org/web/20140311164443/http://asp.eurasipjournals.com/content/pdf/1687-6180-2012-134.pdf) 2014-03-11 at the [Wayback Machine](https://en.wikipedia.org/wiki/Wayback_Machine), M. Y. Boudaren, E. Monfrini, W. Pieczynski, and A. Aissani, Dempster-Shafer fusion of multisensor signals in nonstationary Markovian context, EURASIP Journal on Advances in Signal Processing, No. 134, 2012.
49. [Lanchantin et al.](https://ieeexplore.ieee.org/xpl/articleDetails.jsp?tp=&arnumber=1468502&contentType=Journals+%26+Magazines&searchField%3DSearch_All%26queryText%3Dlanchantin+pieczynski), P. Lanchantin and W. Pieczynski, Unsupervised restoration of hidden non stationary Markov chain using evidential priors, IEEE Transactions on Signal Processing, Vol. 53, No. 8, pp. 3091-3098, 2005.
50. [Boudaren et al.](https://ieeexplore.ieee.org/xpl/articleDetails.jsp?tp=&arnumber=6244854&contentType=Journals+%26+Magazines&searchField%3DSearch_All%26queryText%3Dboudaren), M. Y. Boudaren, E. Monfrini, and W. Pieczynski, Unsupervised segmentation of random discrete data hidden with switching noise distributions, IEEE Signal Processing Letters, Vol. 19, No. 10, pp. 619-622, October 2012.
51. Sotirios P. Chatzis, Dimitrios Kosmopoulos, ["Visual Workflow Recognition Using a Variational Bayesian Treatment of Multistream Fused Hidden Markov Models,"](https://ieeexplore.ieee.org/document/6164251/) IEEE Transactions on Circuits and Systems for Video Technology, vol. 22, no. 7, pp. 1076-1086, July 2012.
52. Chatzis, Sotirios P.; Demiris, Yiannis (2012). "A Reservoir-Driven Non-Stationary Hidden Markov Model". *Pattern Recognition*. **45** (11): 3985–3996. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2012PatRe..45.3985C](https://ui.adsabs.harvard.edu/abs/2012PatRe..45.3985C). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.patcog.2012.04.018](https://doi.org/10.1016%2Fj.patcog.2012.04.018). [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[10044/1/12611](https://hdl.handle.net/10044%2F1%2F12611).
53. M. Lukosevicius, H. Jaeger (2009) Reservoir computing approaches to recurrent neural network training, Computer Science Review **3**: 127–149.
54. Azeraf, E., Monfrini, E., & Pieczynski, W. (2023). Equivalence between LC-CRF and HMM, and Discriminative Computing of HMM-Based MPM and MAP. Algorithms, 16(3), 173.
55. Azeraf, E., Monfrini, E., Vignon, E., & Pieczynski, W. (2020). Hidden markov chains, entropic forward-backward, and part-of-speech tagging. arXiv preprint arXiv:2005.10629.
56. Azeraf, E., Monfrini, E., & Pieczynski, W. (2022). Deriving discriminative classifiers from generative models. arXiv preprint arXiv:2201.00844.
57. Ng, A., & Jordan, M. (2001). On discriminative vs. generative classifiers: A comparison of logistic regression and naive bayes. Advances in neural information processing systems, 14.
58. Wiggins, L. M. (1973). *Panel Analysis: Latent Probability Models for Attitude and Behaviour Processes*. Amsterdam: Elsevier.
59. Bartolucci, F.; Farcomeni, A.; Pennoni, F. (2013). [Latent Markov models for longitudinal data](https://sites.google.com/site/latentmarkovbook/home). Boca Raton: Chapman and Hall/CRC. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-14-3981-708-7](https://en.wikipedia.org/wiki/Special:BookSources/978-14-3981-708-7).
60. *[Sofic Measures: Characterizations of Hidden Markov Chains by Linear Algebra, Formal Languages, and Symbolic Dynamics](https://web.archive.org/web/20221005013617/https://petersen.web.unc.edu/wp-content/uploads/sites/17054/2018/04/Main.pdf)* - Karl Petersen, Mathematics 210, Spring 2006, University of North Carolina at Chapel Hill
61. ^   Boyle, Mike; Petersen, Karl (2010-01-13), *Hidden Markov processes in the context of symbolic dynamics*, [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[0907.1858](https://arxiv.org/abs/0907.1858)

## External links

### Concepts

- Teif, V. B.; Rippe, K. (2010). "Statistical–mechanical lattice models for protein–DNA binding in chromatin". *J. Phys.: Condens. Matter*. **22** (41) 414105. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1004.5514](https://arxiv.org/abs/1004.5514). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2010JPCM...22O4105T](https://ui.adsabs.harvard.edu/abs/2010JPCM...22O4105T). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1088/0953-8984/22/41/414105](https://doi.org/10.1088%2F0953-8984%2F22%2F41%2F414105). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [21386588](https://pubmed.ncbi.nlm.nih.gov/21386588). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [103345](https://api.semanticscholar.org/CorpusID:103345).
- [A Revealing Introduction to Hidden Markov Models](http://www.cs.sjsu.edu/~stamp/RUA/HMM.pdf) by Mark Stamp, San Jose State University.
- [Fitting HMM's with expectation-maximization – complete derivation](https://web.archive.org/web/20120415032315/http://www.ee.washington.edu/research/guptalab/publications/EMbookChenGupta2010.pdf)
- [A step-by-step tutorial on HMMs](http://www.comp.leeds.ac.uk/roger/HiddenMarkovModels/html_dev/main.html) [Archived](https://web.archive.org/web/20170813231824/http://www.comp.leeds.ac.uk/roger/HiddenMarkovModels/html_dev/main.html) 2017-08-13 at the [Wayback Machine](https://en.wikipedia.org/wiki/Wayback_Machine) *(University of Leeds)*
- [Hidden Markov Models](https://www.cs.brown.edu/research/ai/dynamics/tutorial/Documents/HiddenMarkovModels.html) *(an exposition using basic mathematics)*
- [Hidden Markov Models](http://jedlik.phy.bme.hu/~gerjanos/HMM/node2.html) *(by Narada Warakagoda)*
- Hidden Markov Models: Fundamentals and Applications [Part 1](http://www.eecis.udel.edu/~lliao/cis841s06/hmmtutorialpart1.pdf), [Part 2](http://www.eecis.udel.edu/~lliao/cis841s06/hmmtutorialpart2.pdf) *(by V. Petrushin)*
- Lecture on a Spreadsheet by Jason Eisner, [Video](http://videolectures.net/hltss2010_eisner_plm/video/2/) and [interactive spreadsheet](http://www.cs.jhu.edu/~jason/papers/eisner.hmm.xls)
