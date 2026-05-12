[[information-theory.base]]

> Source: [[Rate Distortion Theory|Rate–distortion theory]]
> License: Wikipedia content is available under CC BY-SA 4.0.

**Rate–distortion theory** is a major branch of [information theory](https://en.wikipedia.org/wiki/Information_theory) which provides the theoretical foundations for [lossy data compression](https://en.wikipedia.org/wiki/Lossy_data_compression); it addresses the problem of determining the minimal number of bits per symbol, as measured by the rate *R*, that should be communicated over a channel, so that the source (input signal) can be approximately reconstructed at the receiver (output signal) without exceeding an expected distortion *D*.

## Introduction

![[media/5dfd19a9d8c431fb09139716010de4cdba13c0f5.png]]
Rate distortion encoder and decoder. An encoder $f_{n}$ encodes a sequence $X^{n}$. The encoded sequence $Y^{n}$ is then fed to a decoder $g_{n}$ which outputs a sequence ${\hat {X}}^{n}$. We try to minimize the distortion between the original sequence $X^{n}$ and the reconstructed sequence ${\hat {X}}^{n}$.

Rate–distortion theory gives an analytical expression for how much compression can be achieved using lossy compression methods. Many of the existing audio, speech, image, and video compression techniques have transforms, quantization, and bit-rate allocation procedures that capitalize on the general shape of rate–distortion functions.

Rate–distortion theory was created by [Claude Shannon](https://en.wikipedia.org/wiki/Claude_Shannon) in his foundational work on information theory.

In rate–distortion theory, the *rate* is usually understood as the number of [bits](https://en.wikipedia.org/wiki/Bit) per data sample to be stored or transmitted. The notion of *distortion* is a subject of on-going discussion. In the most simple case (which is actually used in most cases), the distortion is defined as the expected value of the square of the difference between input and output signal (i.e., the [mean squared error](https://en.wikipedia.org/wiki/Mean_squared_error)). However, since we know that most [lossy compression](https://en.wikipedia.org/wiki/Lossy_compression) techniques operate on data that will be perceived by human consumers (listening to [music](https://en.wikipedia.org/wiki/Music), watching pictures and video) the distortion measure should preferably be modeled on human [perception](https://en.wikipedia.org/wiki/Perception) and perhaps [aesthetics](https://en.wikipedia.org/wiki/Aesthetics): much like the use of [probability](https://en.wikipedia.org/wiki/Probability) in [lossless compression](https://en.wikipedia.org/wiki/Lossless_compression), distortion measures can ultimately be identified with [loss functions](https://en.wikipedia.org/wiki/Loss_function) as used in Bayesian [estimation](https://en.wikipedia.org/wiki/Estimation_theory) and [decision theory](https://en.wikipedia.org/wiki/Decision_theory). In audio compression, perceptual models (and therefore perceptual distortion measures) are relatively well developed and routinely used in compression techniques such as [MP3](https://en.wikipedia.org/wiki/MP3) or [Vorbis](https://en.wikipedia.org/wiki/Vorbis), but are often not easy to include in rate–distortion theory. In image and video compression, the human perception models are less well developed and inclusion is mostly limited to the [JPEG](https://en.wikipedia.org/wiki/JPEG) and [MPEG](https://en.wikipedia.org/wiki/MPEG) weighting ([quantization](https://en.wikipedia.org/wiki/Quantization_(signal_processing) "Quantization (signal processing)"), [normalization](https://en.wikipedia.org/wiki/Normalization_(image_processing) "Normalization (image processing)")) matrix.

## Distortion functions

Distortion functions measure the cost of representing a symbol $x$ by an approximated symbol ${\hat {x}}$. Typical distortion functions are the Hamming distortion and the Squared-error distortion.

### Hamming distortion

$d(x,{\hat {x}})={\begin{cases}0&{\text{if }}x={\hat {x}}\\1&{\text{if }}x\neq {\hat {x}}\end{cases}}$

### Squared-error distortion

$d(x,{\hat {x}})=\left(x-{\hat {x}}\right)^{2}$

## Rate–distortion functions

The functions that relate the rate and distortion are found as the solution of the following minimization problem:

$\inf _{Q_{Y\mid X}(y\mid x)}I_{Q}(Y;X){\text{ subject to }}D_{Q}\leq D^{*}.$

Here $Q_{Y\mid X}(y\mid x)$, sometimes called a test channel, is the [conditional](https://en.wikipedia.org/wiki/Conditional_probability) [[Probability Density Function]] (PDF) of the communication channel output (compressed signal) $Y$ for a given input (original signal) $X$, and $I_{Q}(Y;X)$ is the **[[Mutual Information]]** between $Y$ and $X$ defined as

$I(Y;X)=H(Y)-H(Y\mid X)\,$

where $H(Y)$ and $H(Y\mid X)$ are the entropy of the output signal *Y* and the [conditional entropy](https://en.wikipedia.org/wiki/Conditional_entropy) of the output signal given the input signal, respectively:

$H(Y)=-\int _{-\infty }^{\infty }P_{Y}(y)\log _{2}(P_{Y}(y))\,dy$

$H(Y\mid X)=-\int _{-\infty }^{\infty }\int _{-\infty }^{\infty }Q_{Y\mid X}(y\mid x)P_{X}(x)\log _{2}(Q_{Y\mid X}(y\mid x))\,dx\,dy.$

The problem can also be formulated as a distortion–rate function, where we find the [infimum](https://en.wikipedia.org/wiki/Infimum_and_supremum) over achievable distortions for given rate constraint. The relevant expression is:

$\inf _{Q_{Y\mid X}(y\mid x)}E[D_{Q}[X,Y]]{\text{ subject to }}I_{Q}(Y;X)\leq R.$

The two formulations lead to functions which are inverses of each other.

The mutual information can be understood as a measure for 'prior' uncertainty the receiver has about the sender's signal (*H*(*Y*)), diminished by the uncertainty that is left after receiving information about the sender's signal ($H(Y\mid X)$). Of course the decrease in uncertainty is due to the communicated amount of information, which is $I\left(Y;X\right)$.

As an example, in case there is *no* communication at all, then $H(Y\mid X)=H(Y)$ and $I(Y;X)=0$. Alternatively, if the communication channel is perfect and the received signal $Y$ is identical to the signal $X$ at the sender, then $H(Y\mid X)=0$ and $I(Y;X)=H(X)=H(Y)$.

In the definition of the rate–distortion function, $D_{Q}$ and $D^{*}$ are the distortion between $X$ and $Y$ for a given $Q_{Y\mid X}(y\mid x)$ and the prescribed maximum distortion, respectively. When we use the [mean squared error](https://en.wikipedia.org/wiki/Mean_squared_error) as distortion measure, we have (for [amplitude](https://en.wikipedia.org/wiki/Amplitude)-[continuous signals](https://en.wikipedia.org/wiki/Continuous_signal)):

$D_{Q}=\int _{-\infty }^{\infty }\int _{-\infty }^{\infty }P_{X,Y}(x,y)(x-y)^{2}\,dx\,dy=\int _{-\infty }^{\infty }\int _{-\infty }^{\infty }Q_{Y\mid X}(y\mid x)P_{X}(x)(x-y)^{2}\,dx\,dy.$

As the above equations show, calculating a rate–distortion function requires the stochastic description of the input $X$ in terms of the PDF $P_{X}(x)$, and then aims at finding the conditional PDF $Q_{Y\mid X}(y\mid x)$ that minimize rate for a given distortion $D^{*}$. These definitions can be formulated measure-theoretically to account for discrete and mixed random variables as well.

An [analytical](https://en.wikipedia.org/wiki/Analytical_expression) solution to this [minimization problem](https://en.wikipedia.org/wiki/Optimization_problem) is often difficult to obtain except in some instances for which we next offer two of the best known examples. The rate–distortion function of any source is known to obey several fundamental properties, the most important ones being that it is a [continuous](https://en.wikipedia.org/wiki/Continuous_function), [monotonically decreasing](https://en.wikipedia.org/wiki/Monotonically_decreasing) [convex](https://en.wikipedia.org/wiki/Convex_function) (U) [function](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)") and thus the shape for the function in the examples is typical (even measured rate–distortion functions in real life tend to have very similar forms).

$R(D)\geq h(X)-h(D)\,$

where *h*(*D*) is the differential entropy of a Gaussian random variable with variance D. This lower bound is extensible to sources with memory and other distortion measures. One important feature of the SLB is that it is asymptotically tight in the low distortion regime for a wide class of sources and in some occasions, it actually coincides with the rate–distortion function. Shannon Lower Bounds can generally be found if the distortion between any two numbers can be expressed as a function of the difference between the value of these two numbers.

The [Blahut–Arimoto algorithm](https://en.wikipedia.org/wiki/Blahut%E2%80%93Arimoto_algorithm), co-invented by [Richard Blahut](https://en.wikipedia.org/wiki/Richard_Blahut), is an elegant iterative technique for numerically obtaining rate–distortion functions of arbitrary finite input/output alphabet sources and much work has been done to extend it to more general problem instances.

The computation of the rate-distortion function requires knowledge of the underlying distribution, which is often unavailable in contemporary applications in data-science and machine learning. However, this challenge can be addressed using deep learning-based estimators of the rate-distortion function. These estimators are typically referred to as 'neural estimators', involving the optimization of a parametrized variational form of the rate distortion objective.

When working with stationary sources with memory, it is necessary to modify the definition of the rate distortion function and it must be understood in the sense of a limit taken over sequences of increasing lengths.

$R(D)=\lim _{n\rightarrow \infty }R_{n}(D)$

where

$R_{n}(D)={\frac {1}{n}}\inf _{Q_{Y^{n}\mid X^{n}}\in {\mathcal {Q}}}I(Y^{n},X^{n})$

and

${\mathcal {Q}}=\{Q_{Y^{n}\mid X^{n}}(Y^{n}\mid X^{n},X_{0}):E[d(X^{n},Y^{n})]\leq D\}$

where superscripts denote a complete sequence up to that time and the subscript 0 indicates initial state.

### Memoryless (independent) Gaussian source with squared-error distortion

If we assume that $X$ is a [Gaussian](https://en.wikipedia.org/wiki/Normal_distribution) random variable with [variance](https://en.wikipedia.org/wiki/Variance) $\sigma ^{2}$, and if we assume that successive samples of the signal $X$ are [stochastically independent](https://en.wikipedia.org/wiki/Stochastically_independent) (or equivalently, the source is *[memoryless](https://en.wikipedia.org/wiki/Memorylessness)*, or the signal is *uncorrelated*), we find the following [analytical expression](https://en.wikipedia.org/wiki/Analytical_expression) for the rate–distortion function:

$R(D)={\begin{cases}{\frac {1}{2}}\log _{2}(\sigma _{x}^{2}/D),&{\text{if }}0\leq D\leq \sigma _{x}^{2}\\0,&{\text{if }}D>\sigma _{x}^{2}.\end{cases}}$   

The following figure shows what this function looks like:

![[media/1decfe76cf73f01f4f3e681d956aa408839858aa.png]]

Rate–distortion theory tell us that 'no compression system exists that performs outside the gray area'. The closer a practical compression system is to the red (lower) bound, the better it performs. As a general rule, this bound can only be attained by increasing the coding block length parameter. Nevertheless, even at unit blocklengths one can often find good (scalar) [quantizers](https://en.wikipedia.org/wiki/Quantization_(signal_processing) "Quantization (signal processing)") that operate at distances from the rate–distortion function that are practically relevant.

This rate–distortion function holds only for Gaussian memoryless sources. It is known that the Gaussian source is the most "difficult" source to encode: for a given mean square error, it requires the greatest number of bits. The performance of a practical compression system working on—say—images, may well be below the $R\left(D\right)$ lower bound shown.

### Memoryless (independent) Bernoulli source with Hamming distortion

The rate-distortion function of a [Bernoulli random variable](https://en.wikipedia.org/wiki/Bernoulli_random_variable) with Hamming distortion is given by:

$R(D)=\left\{{\begin{matrix}H_{b}(p)-H_{b}(D),&0\leq D\leq \min {(p,1-p)}\\0,&D>\min {(p,1-p)}\end{matrix}}\right.$

where $H_{b}$ denotes the [binary entropy function](https://en.wikipedia.org/wiki/Binary_entropy_function).

Plot of the rate-distortion function for $p=0.5$:

![[media/91bf0e0c97a8173647b7b33af826bff768d877d6.png]]

## Connecting rate-distortion theory to channel capacity

Suppose we want to transmit information about a source to the user with a distortion not exceeding *D*. Rate–distortion theory tells us that at least $R(D)$ bits/symbol of information from the source must reach the user. We also know from Shannon's channel coding theorem that if the source entropy is *H* bits/symbol, and the [channel capacity](https://en.wikipedia.org/wiki/Channel_capacity) is *C* (where $C<H$), then $H-C$ bits/symbol will be lost when transmitting this information over the given channel. For the user to have any hope of reconstructing with a maximum distortion *D*, we must impose the requirement that the information lost in transmission does not exceed the maximum tolerable loss of $H-R(D)$ bits/symbol. This means that the channel capacity must be at least as large as $R(D)$.

## See also

- [Blahut–Arimoto algorithm](https://en.wikipedia.org/wiki/Blahut%E2%80%93Arimoto_algorithm) – Class of algorithms in information theory
- [Data compression](https://en.wikipedia.org/wiki/Data_compression) – Compact encoding of digital data
- [Decorrelation](https://en.wikipedia.org/wiki/Decorrelation) – Process of reducing correlation within one or more signals
- [Rate–distortion optimization](https://en.wikipedia.org/wiki/Rate%E2%80%93distortion_optimization)
- [Sphere packing](https://en.wikipedia.org/wiki/Sphere_packing) – Geometrical structure
- [White noise](https://en.wikipedia.org/wiki/White_noise) – Type of signal in signal processing

## References

1.  Blau, Y.; Michaeli, T. (2019). ["Rethinking Lossy Compression: The Rate-Distortion-Perception Tradeoff"](http://proceedings.mlr.press/v97/blau19a/blau19a.pdf) (PDF). *Proceedings of the International Conference on Machine Learning*. PMLR. pp. 675–685. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1901.07821](https://arxiv.org/abs/1901.07821).
2.  Tsur, Dor; Huleihel, Bashar; Permuter, Haim H. (2024). ["On Rate Distortion via Constrained Optimization of Estimated Mutual Information"](https://doi.org/10.1109%2FACCESS.2024.3462853). *IEEE Access*. **12**: 137970–137987. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2024IEEEA..12m7970T](https://ui.adsabs.harvard.edu/abs/2024IEEEA..12m7970T). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/ACCESS.2024.3462853](https://doi.org/10.1109%2FACCESS.2024.3462853). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [2169-3536](https://search.worldcat.org/issn/2169-3536).
3.  , p. 310
4.  Cover, Thomas M.; Thomas, Joy A. (2012) \[2006\]. ["10. Rate Distortion Theory"](https://books.google.com/books?id=VWq5GG6ycxMC&pg=PA301). *Elements of Information Theory* (2nd ed.). Wiley. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-118-58577-1](https://en.wikipedia.org/wiki/Special:BookSources/978-1-118-58577-1).
5.  Berger, Toby (1971). [Rate Distortion Theory: A Mathematical Basis for Data Compression](https://archive.org/details/ratedistortionth0000berg/). Prentice Hall. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-13-753103-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-13-753103-5). [LCCN](https://en.wikipedia.org/wiki/LCCN_(identifier)) [75-148254](https://lccn.loc.gov/75-148254). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [156968](https://search.worldcat.org/oclc/156968).

## External links

- Marzen, Sarah; DeDeo, Simon. ["PyRated: a python package for rate distortion theory"](https://sites.santafe.edu/~simon/styled-13/). “PyRated is a very simple Python package to do the most basic calculation in rate-distortion theory: the determination of the "codebook" and the transmission rate *R*, given a utility function (distortion matrix) and a Lagrange multiplier *beta*.”
- [VcDemo Image and Video Compression Learning Tool](https://web.archive.org/web/20011006065854/http://www-ict.its.tudelft.nl/vcdemo)
