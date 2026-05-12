[[probability-statistics.base]]

> Source: [Confidence interval](https://en.wikipedia.org/wiki/Confidence_interval)
> License: Wikipedia content is available under CC BY-SA 4.0.

![[media/98215682ea4f862a48c7f191ca154f584a5d3bbc.png]]
Each row of points is a sample from the same normal distribution. The colored lines are 50% confidence intervals for the population mean <em>μ</em>. At the center of each interval is the sample mean ${\bar {x}}$, marked with a diamond. The blue intervals contain <em>μ</em>, and the red ones do not.

According to [frequentist inference](https://en.wikipedia.org/wiki/Frequentist_inference), a **confidence interval** (**CI**) is a range of values which is likely to contain (in repeated sampling) the true value of an unknown [statistical parameter](https://en.wikipedia.org/wiki/Statistical_parameter), such as a population [mean](https://en.wikipedia.org/wiki/Mean). Rather than reporting a single point estimate (e.g. "the average screen time is 3 hours per day"), a confidence interval provides a range, such as 2 to 4 hours, along with a specified **confidence level**, typically 95%.

A 95% confidence level does not imply a 95% probability that the true parameter lies within a particular calculated interval, which is instead associated with the [credible interval](https://en.wikipedia.org/wiki/Credible_interval) in [Bayesian inference](https://en.wikipedia.org/wiki/Bayesian_inference). The confidence level instead reflects the long-run reliability of the method used to generate the interval. In other words, if the same sampling procedure were repeated 100 times from the same population, approximately 95 of the resulting intervals would be expected to contain the true population mean. The frequentist approach sees the true population mean as a fixed unknown constant, while the confidence interval is calculated using data from a random sample. Because the sample is random, the interval endpoints are random variables.

## Definition

Let $X$ be a [random sample](https://en.wikipedia.org/wiki/Random_sample) from a [probability distribution](https://en.wikipedia.org/wiki/Probability_distribution) with [statistical parameter](https://en.wikipedia.org/wiki/Statistical_parameter) $(\theta ,\varphi )$. Here, $\theta$ is the quantity to be estimated, while $\varphi$ includes other parameters (if any) that determine the distribution. A confidence interval for the parameter $\theta$, with confidence level or coefficient $\gamma$, is an interval $(u(X),v(X))$ determined by [random variables](https://en.wikipedia.org/wiki/Random_variable) $u(X)$ and $v(X)$ with the property: 

$$
P(u(X)<\theta <v(X))=\gamma \quad {\text{for all }}(\theta ,\varphi ).
$$

The number $\gamma$, which is typically large (e.g. 0.95), is sometimes given in the form $1-\alpha$ (or as a percentage $100\%\cdot (1-\alpha )$), where $\alpha$ is a small positive number, often 0.05. It means that the interval $(u(X),v(X))$ has a probability $\gamma$ of covering the value of $\theta$ in repeated sampling.

In many applications, confidence intervals that have exactly the required confidence level are hard to construct, but approximate intervals can be computed. The rule for constructing the interval may be accepted if

$$
P(u(X)<\theta <v(X))\approx \ \gamma
$$

to an acceptable level of approximation. Alternatively, some authors simply require that

$$
P(u(X)<\theta <v(X))\geq \ \gamma
$$

 When it is known that the [coverage probability](https://en.wikipedia.org/wiki/Coverage_probability) can be strictly larger than $\gamma$ for some parameter values, the confidence interval is called conservative, i.e., it errs on the safe side; which also means that the interval can be wider than need be.

### Methods of derivation

There are many ways of calculating confidence intervals, and the best method depends on the situation. Two widely applicable methods are [bootstrapping](https://en.wikipedia.org/wiki/Bootstrapping_(statistics)#Deriving_confidence_intervals_from_the_bootstrap_distribution "Bootstrapping (statistics)") and the [[Central Limit Theorem]]. The latter method works only if the sample is large, since it entails calculating the sample mean ${\bar {X}}$ and sample standard deviation $S$ and using the asymptotically standard normal quantity

$$
{\frac {{\bar {X}}-\mu }{S/{\sqrt {n}}}}
$$

where $\mu$ and $n$ are the population mean and the sample size, respectively.

## Example

![[media/9ec9c09a22169833f99fd6da18fea129e87a4a0c.png]]
In this [bar chart](https://en.wikipedia.org/wiki/Bar_chart), the top ends of the brown bars indicate observed means and the red line segments ("[error bars](https://en.wikipedia.org/wiki/Error_bar)") represent the confidence intervals around them. Although the error bars are shown as symmetric around the means, that is not always the case. In most graphs, the error bars do not represent confidence intervals (e.g., they often represent standard errors or standard deviations).

Suppose $X_{1},\ldots ,X_{n}$ is an [independent](https://en.wikipedia.org/wiki/Statistical_independence) sample from a [normally distributed](https://en.wikipedia.org/wiki/Normal_distribution) population with unknown parameters [mean](https://en.wikipedia.org/wiki/Mean) $\mu$ and [variance](https://en.wikipedia.org/wiki/Variance) $\sigma ^{2}.$ Define the [sample mean](https://en.wikipedia.org/wiki/Sample_mean_and_covariance) ${\bar {X}}$ and [unbiased sample variance](https://en.wikipedia.org/wiki/Variance#Unbiased_sample_variance) $S^{2}$ as

$$
{\begin{aligned}{\bar {X}}&={\frac {1}{n}}\left(X_{1}+\cdots +X_{n}\right),\\S^{2}&={\frac {1}{n-1}}\sum _{i=1}^{n}\left(X_{i}-{\bar {X}}\right)^{2}.\end{aligned}}
$$

Then the value

$$
T={\frac {{\bar {X}}-\mu }{S/{\sqrt {n}}}}
$$

has a [Student's *t* distribution](https://en.wikipedia.org/wiki/Student%27s_t-distribution) with $n-1$ degrees of freedom. This value is useful because its distribution does not depend on the values of the unobservable parameters $\mu$ and $\sigma ^{2}$; i.e., it is a [pivotal quantity](https://en.wikipedia.org/wiki/Pivotal_quantity).

Suppose we wanted to calculate a 95% confidence interval for $\mu .$ First, let $c$ be the 97.5th [percentile](https://en.wikipedia.org/wiki/Percentile) of the distribution of $T$. Then there is a 2.5% chance that $T$ will be less than $-c$ and a 2.5% chance that it will be larger than $+c$ (as the *t* distribution is symmetric about 0). In other words,

$$
P_{T}(-c\leq T\leq c)=0.95.
$$

Consequently, by replacing $T$ with ${\frac {{\bar {X}}-\mu }{S/{\sqrt {n}}}}$ and re-arranging terms,

$$
P_{X}{\left({\bar {X}}-{\frac {cS}{\sqrt {n}}}\leq \mu \leq {\bar {X}}+{\frac {cS}{\sqrt {n}}}\right)}=0.95
$$

where $P_{X}$ is the probability measure for the sample $X_{1},\ldots ,X_{n}$.

It means that there is 95% probability with which this condition ${\bar {X}}-{\frac {cS}{\sqrt {n}}}\leq \mu \leq {\bar {X}}+{\frac {cS}{\sqrt {n}}}$ occurs in repeated sampling. After observing a sample, we find values ${\bar {x}}$ for ${\bar {X}}$ and $s$ for $S,$ from which we compute the below interval, and we say it is a 95% confidence interval for the mean.

$$
\left[{\bar {x}}-{\frac {cs}{\sqrt {n}}},{\bar {x}}+{\frac {cs}{\sqrt {n}}}\right].
$$

## Interpretation

Various interpretations of a confidence interval can be given (taking the 95% confidence interval as an example in the following).

- The confidence interval can be expressed in terms of a [long-run frequency](https://en.wikipedia.org/wiki/Frequentist_probability) in [repeated samples](https://en.wikipedia.org/wiki/Replication_(statistics) "Replication (statistics)") (or in [resampling](https://en.wikipedia.org/wiki/Resampling_(statistics) "Resampling (statistics)")): "Were this procedure to be repeated on numerous samples, the proportion of calculated 95% confidence intervals that encompassed the true value of the population parameter would tend toward 95%."
- The confidence interval can be expressed in terms of probability with respect to a single theoretical (yet to be realized) sample: "There is a 95% [probability](https://en.wikipedia.org/wiki/Coverage_probability) that the 95% confidence interval calculated from a given future sample will cover the true value of the population parameter." This essentially reframes the "repeated samples" interpretation as a probability rather than a frequency.
- The confidence interval can be expressed in terms of statistical significance, e.g.: "The 95% confidence interval represents values that are not [statistically significantly](https://en.wikipedia.org/wiki/Statistically_significant) different from the point estimate at the .05 level."

![[media/c8464badbb8dc02ed0e6e08db5d3ea96cbed6db0.png]]
Interpretation of the 95% confidence interval in terms of statistical significance

### Common misunderstandings

![[media/4bd7a198313e566d62bd9739a29f171c50372e93.png]]
A plot of 50 confidence intervals from 50 samples generated from a normal distribution

Confidence intervals and levels are frequently misunderstood, and published studies have shown that even professional scientists often misinterpret them.

Contrary to common misconceptions, a 95% confidence level does *not* mean that:

- for a given realized interval there is a 95% probability that the population parameter lies within the interval;
- 95% of the sample data lie within the confidence interval; or
- there is a 95% probability of the parameter estimate from a repeat of the experiment falling within the confidence interval computed from a given experiment.

For example, suppose a factory produces metal rods, and a random sample of 25 rods gives a 95% confidence interval of 36.8 to 39.0 mm for the population mean length.

- It is incorrect to say that there is a 95% probability that the true population mean lies within this interval: the true mean is fixed, not random. The true mean could be 37 mm, which is within the confidence interval, or 40 mm, which is not; in any case, whether it falls between 36.8 and 39.0 mm is a matter of fact, not probability.
- It is not necessarily true that the lengths of 95% of the sampled rods lie within this interval. In this case, it cannot be true: 95% of 25 is not an integer.
- It is not generally true that there is a 95% probability that the sample mean length (an estimate of the population mean length) in a second sample would fall within this interval. In fact, if the true mean length is far from this specific confidence interval, it could be very unlikely that the next sample mean falls within the interval.

Instead, the 95% confidence level means that if we took 100 such samples, we would expect the true population mean to lie within approximately 95 of the calculated intervals.

### Comparison with [prediction intervals](https://en.wikipedia.org/wiki/Prediction_interval)

A confidence interval is used to estimate a population parameter, such as the mean. For example, the expected value of a fair six-sided die is 3.5. Based on repeated sampling, after computing many 95% confidence intervals, roughly 95% of them will contain 3.5 (and the width of the confidence interval shrinks with sample size).

A prediction interval, on the other hand, provides a range within which a future individual observation is expected to fall with a certain probability. In the case of a single roll of a fair six-sided die, an exact 95% prediction interval does not exist. However, there are exact 95% prediction intervals for rolling a twenty-sided die. One such interval is $[1,19]$, since 95% of the time the roll will result in a 19 or less, and the remaining 5% will result in a 20.

The key distinction is that confidence intervals quantify uncertainty in estimating parameters, while prediction intervals quantify uncertainty in forecasting future observations.

### Comparison with [credible intervals](https://en.wikipedia.org/wiki/Credible_interval)

In many common settings, such as estimating the mean of a normal distribution with known variance, confidence intervals coincide with credible intervals under non-informative priors. In such cases, common misconceptions about confidence intervals (e.g. interpreting them as probability statements about the parameter) may yield practically correct conclusions.

### Examples of how naïve interpretation of confidence intervals can be problematic

#### Confidence procedure for uniform location

![[media/207b78c9e9607cb1b85a6f836aed17eee30f8874.png]]
Ten examples of the 50% Welch and Bayesian intervals are shown in contrasting white and gray rows. The examples are sorted top-to-bottom by decreasing distance between $X_{1}$ and $X_{2}$.

Welch presented an example which clearly shows the difference between the theory of confidence intervals and other theories of interval estimation (including Fisher's [fiducial](https://en.wikipedia.org/wiki/Fiducial_inference) intervals and objective [Bayesian](https://en.wikipedia.org/wiki/Bayesian_inference) intervals). Robinson called this example "\[p\]ossibly the best known counterexample for Neyman's version of confidence interval theory." To Welch, it showed the superiority of confidence interval theory; to critics of the theory, it shows a deficiency. Here we present a simplified version.

Suppose that $X_{1},X_{2}$ are independent observations from a [uniform](https://en.wikipedia.org/wiki/Continuous_uniform_distribution) $(\theta -1/2,\theta +1/2)$ distribution. Then the optimal 50% confidence procedure for $\theta$ is

$$
{\bar {X}}\pm {\begin{cases}{\dfrac {|X_{1}-X_{2}|}{2}}&{\text{if }}|X_{1}-X_{2}|<1/2\\[8pt]{\dfrac {1-|X_{1}-X_{2}|}{2}}&{\text{if }}|X_{1}-X_{2}|\geq 1/2.\end{cases}}
$$

A fiducial or objective Bayesian argument can be used to derive the interval estimate 

$$
{\bar {X}}\pm {\frac {1-|X_{1}-X_{2}|}{4}},
$$

 which is also a 50% confidence procedure. Welch showed that the first confidence procedure dominates the second, according to desiderata from confidence interval theory; for every $\theta _{1}\neq \theta$, the probability that the first procedure contains $\theta _{1}$ is *less than or equal to* the probability that the second procedure contains $\theta _{1}$. The average width of the intervals from the first procedure is less than that of the second. Hence, the first procedure is preferred under classical confidence interval theory.

However, when $|X_{1}-X_{2}|\geq 1/2$, intervals from the first procedure are *guaranteed* to contain the true value $\theta$: Therefore, the nominal 50% confidence coefficient is unrelated to the uncertainty we should have that a specific interval contains the true value. The second procedure does not have this property.

Moreover, when the first procedure generates a very short interval, this indicates that $X_{1},X_{2}$ are very close together and hence only offer the information in a single data point. Yet the first interval will exclude almost all reasonable values of the parameter due to its short width. The second procedure does not have this property.

The two counter-intuitive properties of the first procedure – 100% [coverage](https://en.wikipedia.org/wiki/Coverage_probability) when $X_{1},X_{2}$ are far apart and almost 0% coverage when $X_{1},X_{2}$ are close together – balance out to yield 50% coverage on average. However, despite the first procedure being optimal, its intervals offer neither an assessment of the precision of the estimate nor an assessment of the uncertainty one should have that the interval contains the true value.

This example is used to argue against naïve interpretations of confidence intervals. If a confidence procedure is asserted to have properties beyond that of the nominal coverage (such as relation to precision, or a relationship with Bayesian inference), those properties must be proved; they do not follow from the fact that a procedure is a confidence procedure.

#### Confidence procedure for *ω*<sup>2</sup>

Steiger suggested a number of confidence procedures for common [effect size](https://en.wikipedia.org/wiki/Effect_size#Omega-squared_(ω2) "Effect size") measures in [ANOVA](https://en.wikipedia.org/wiki/Analysis_of_variance). Morey et al. point out that several of these confidence procedures, including the one for *ω*<sup>2</sup>, have the property that as the *F* statistic becomes increasingly small—indicating misfit with all possible values of *ω*<sup>2</sup>—the confidence interval shrinks and can even contain only the single value *ω*<sup>2</sup> = 0; that is, the CI is infinitesimally narrow (this occurs when $p\geq 1-\alpha /2$ for a $100(1-\alpha )\%$ CI).

This behavior is consistent with the relationship between the confidence procedure and [significance testing](https://en.wikipedia.org/wiki/Statistical_hypothesis_testing): as *F* becomes so small that the group means are much closer together than we would expect by chance, a significance test might indicate rejection for most or all values of *ω*<sup>2</sup>. Hence the interval will be very narrow or even empty (or, by a convention suggested by Steiger, containing only 0). However, this does *not* indicate that the estimate of *ω*<sup>2</sup> is very precise. In a sense, it indicates the opposite: that the trustworthiness of the results themselves may be in doubt. This is contrary to the common interpretation of confidence intervals that they reveal the precision of the estimate.

## History

Methods for calculating confidence intervals for the binomial proportion appeared from the 1920s. The main ideas of confidence intervals in general were developed in the early 1930s, and the first thorough and general account was given by [Jerzy Neyman](https://en.wikipedia.org/wiki/Jerzy_Neyman) in 1937.

Neyman described the development of the ideas as follows (reference numbers have been changed):

> \[My work on confidence intervals\] originated about 1930 from a simple question of Waclaw Pytkowski, then my student in Warsaw, engaged in an empirical study in farm economics. The question was: how to characterize non-dogmatically the precision of an estimated regression coefficient? ...
>
> Pytkowski's monograph ... appeared in print in 1932. It so happened that, somewhat earlier, Fisher published his first paper concerned with fiducial distributions and fiducial argument. Quite unexpectedly, while the conceptual framework of fiducial argument is entirely different from that of confidence intervals, the specific solutions of several particular problems coincided. Thus, in the first paper in which I presented the theory of confidence intervals, published in 1934, I recognized Fisher's priority for the idea that interval estimation is possible without any reference to Bayes' theorem and with the solution being independent from probabilities *a priori*. At the same time I mildly suggested that Fisher's approach to the problem involved a minor misunderstanding.

In medical journals, confidence intervals were promoted in the 1970s but only became widely used in the 1980s. By 1988, medical journals were requiring the reporting of confidence intervals.

## Confidence interval for specific distributions

- [Confidence interval for binomial distribution](https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval)
- [Confidence interval for exponent of the power law distribution](https://en.wikipedia.org/wiki/Power_law#Estimating_the_exponent_from_empirical_data)
- [Confidence interval for mean of the exponential distribution](https://en.wikipedia.org/wiki/Exponential_distribution#Confidence_intervals)
- [Confidence interval for mean of the Poisson distribution](https://en.wikipedia.org/wiki/Poisson_distribution#Confidence_interval)
- [Confidence intervals for mean and variance of the normal distribution](https://en.wikipedia.org/wiki/Normal_distribution#Confidence_intervals) (also [here](https://en.wikipedia.org/wiki/Student%27s_t-distribution#Confidence_intervals))
- [Confidence interval for the parameters of a simple linear regression](https://en.wikipedia.org/wiki/Variance_of_the_mean_and_predicted_responses#Confidence_intervals)
- [Confidence interval for the difference of means](https://en.wikipedia.org/wiki/Welch%27s_t-test#Statistical_test) (based on data from a normal distributions, without assuming equal variances)
- [Confidence interval for the difference between two proportions](https://en.wikipedia.org/wiki/Z-test#Comparing_the_proportions_of_two_binomials)

## See also

- [CLs upper limits (particle physics)](https://en.wikipedia.org/wiki/CLs_upper_limits_(particle_physics))
- [68–95–99.7 rule](https://en.wikipedia.org/wiki/68%E2%80%9395%E2%80%9399.7_rule)
- [Confidence band](https://en.wikipedia.org/wiki/Confidence_band), an interval estimate for a curve
- [Confidence distribution](https://en.wikipedia.org/wiki/Confidence_distribution) – Concept in statistics
- [Confidence region](https://en.wikipedia.org/wiki/Confidence_region) – Multi-dimensional version of a confidence interval, a higher dimensional generalization
- [Credence (statistics)](https://en.wikipedia.org/wiki/Credence_(statistics) "Credence (statistics)") – Measure of belief strength used in statistics
- [Credible interval](https://en.wikipedia.org/wiki/Credible_interval), a Bayesian alternative for interval estimation
- [Cumulative distribution function-based nonparametric confidence interval](https://en.wikipedia.org/wiki/CDF-based_nonparametric_confidence_interval) – Class of confidence intervals around statistical functionals of a distribution
- [Error bar](https://en.wikipedia.org/wiki/Error_bar) – Graphical representations of the variability of data
- [Estimation statistics](https://en.wikipedia.org/wiki/Estimation_statistics) – Data analysis approach in frequentist statistics
- [Margin of error](https://en.wikipedia.org/wiki/Margin_of_error), the CI halfwidth
- [p-value](https://en.wikipedia.org/wiki/P-value) – Function of the observed sample results
- [Prediction interval](https://en.wikipedia.org/wiki/Prediction_interval), an interval estimate for a random variable
- [Probable error](https://en.wikipedia.org/wiki/Probable_error)
- [Robust confidence intervals](https://en.wikipedia.org/wiki/Robust_confidence_intervals) – Statistical indicators of the deviation of a samplePages displaying short descriptions of redirect targets

## References

1.  ^    Hazra, Avijit (2017). ["Using the confidence interval confidently"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5723800). *Journal of Thoracic Disease*. **9** (10): 4124–4129. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.21037/jtd.2017.09.14](https://doi.org/10.21037%2Fjtd.2017.09.14). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [5723800](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5723800). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [29268424](https://pubmed.ncbi.nlm.nih.gov/29268424).
2.  ^   Dekking, Frederik Michel; Kraaikamp, Cornelis; Lopuhaä, Hendrik Paul; Meester, Ludolf Erwin (2005). ["A Modern Introduction to Probability and Statistics"](https://link.springer.com/book/10.1007/1-84628-168-7). *Springer Texts in Statistics*. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/1-84628-168-7](https://doi.org/10.1007%2F1-84628-168-7). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-85233-896-1](https://en.wikipedia.org/wiki/Special:BookSources/978-1-85233-896-1). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1431-875X](https://search.worldcat.org/issn/1431-875X).
3.  ["Confidence Intervals"](http://www.stat.yale.edu/Courses/1997-98/101/confint.htm). *Yale Department of Statistics*. Retrieved 2025-04-05.
4.  Roussas, George G. (1997). *A Course in Mathematical Statistics* (2nd ed.). Academic Press. p. 397.
5.  Rees, D.G. (2001). *Essential Statistics*, 4th Edition, Chapman and Hall/CRC. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [1-58488-007-4](https://en.wikipedia.org/wiki/Special:BookSources/1-58488-007-4) (Section 9.5)
6.  Cox D.R., Hinkley D.V. (1974) *Theoretical Statistics*, Chapman & Hall, p49, p209
7.  ^   [Neyman, J.](https://en.wikipedia.org/wiki/Jerzy_Neyman) (1937). ["Outline of a Theory of Statistical Estimation Based on the Classical Theory of Probability"](https://doi.org/10.1098%2Frsta.1937.0005). *[Philosophical Transactions of the Royal Society A](https://en.wikipedia.org/wiki/Philosophical_Transactions_of_the_Royal_Society_A)*. **236** (767): 333–380. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1937RSPTA.236..333N](https://ui.adsabs.harvard.edu/abs/1937RSPTA.236..333N). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1098/rsta.1937.0005](https://doi.org/10.1098%2Frsta.1937.0005). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [91337](https://www.jstor.org/stable/91337).
8.  Cox D.R., Hinkley D.V. (1974) Theoretical Statistics, Chapman & Hall, pp. 214, 225, 233
9.  Hoekstra, R., R. D. Morey, J. N. Rouder, and E-J. Wagenmakers, 2014. Robust misinterpretation of confidence intervals. Psychonomic Bulletin & Review Vol. 21, No. 5, pp. 1157-1164. [1](https://en.wikipedia.org/wiki/1)(http://www.ejwagenmakers.com/inpress/HoekstraEtAlPBR.pdf)
10. ^    Morey, R. D.; Hoekstra, R.; Rouder, J. N.; Lee, M. D.; Wagenmakers, E.-J. (2016). ["The Fallacy of Placing Confidence in Confidence Intervals"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4742505). *Psychonomic Bulletin & Review*. **23** (1): 103–123. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3758/s13423-015-0947-8](https://doi.org/10.3758%2Fs13423-015-0947-8). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [4742505](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4742505). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [26450628](https://pubmed.ncbi.nlm.nih.gov/26450628).
11. ^    Greenland, Sander; Senn, Stephen J.; Rothman, Kenneth J.; Carlin, John B.; Poole, Charles; Goodman, Steven N.; Altman, Douglas G. (April 2016). ["Statistical tests, P values, confidence intervals, and power: a guide to misinterpretations"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4877414). *European Journal of Epidemiology*. **31** (4): 337–350. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s10654-016-0149-3](https://doi.org/10.1007%2Fs10654-016-0149-3). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0393-2990](https://search.worldcat.org/issn/0393-2990). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [4877414](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4877414). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [27209009](https://pubmed.ncbi.nlm.nih.gov/27209009).
12. ^   Tan, Sze Huey; Tan, Say Beng (2010-09-01). ["The Correct Interpretation of Confidence Intervals"](https://doi.org/10.1177%2F201010581001900316). *Proceedings of Singapore Healthcare*. **19** (3): 276–278. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1177/201010581001900316](https://doi.org/10.1177%2F201010581001900316). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [2010-1058](https://search.worldcat.org/issn/2010-1058).
13. Bolstad, William M. (2007). [Introduction to Bayesian statistics](https://www.worldcat.org/title/122338165) (2nd ed.). Hoboken, N.J: John Wiley. pp. 223–236. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-470-14115-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-470-14115-1). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [122338165](https://search.worldcat.org/oclc/122338165).
14. Welch, B. L. (1939). ["On Confidence Limits and Sufficiency, with Particular Reference to Parameters of Location"](https://doi.org/10.1214%2Faoms%2F1177732246). *The Annals of Mathematical Statistics*. **10** (1): 58–69. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/aoms/1177732246](https://doi.org/10.1214%2Faoms%2F1177732246). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2235987](https://www.jstor.org/stable/2235987).
15. Robinson, G. K. (1975). "Some Counterexamples to the Theory of Confidence Intervals". *Biometrika*. **62** (1): 155–161. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2334498](https://doi.org/10.2307%2F2334498). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2334498](https://www.jstor.org/stable/2334498).
16. Pratt, J. W. (1961). "Book Review: Testing Statistical Hypotheses. by E. L. Lehmann". *Journal of the American Statistical Association*. **56** (293): 163–167. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/01621459.1961.10482103](https://doi.org/10.1080%2F01621459.1961.10482103). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2282344](https://www.jstor.org/stable/2282344).
17. Steiger, J. H. (2004). "Beyond the F test: Effect size confidence intervals and tests of close fit in the analysis of variance and contrast analysis". *Psychological Methods*. **9** (2): 164–182. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1037/1082-989x.9.2.164](https://doi.org/10.1037%2F1082-989x.9.2.164). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [15137887](https://pubmed.ncbi.nlm.nih.gov/15137887).
18. Edwin B. Wilson (1927) Probable Inference, the Law of Succession, and Statistical Inference, Journal of the American Statistical Association, 22:158, 209-212, [https://doi.org/10.1080/01621459.1927.10502953](https://doi.org/10.1080/01621459.1927.10502953)
19. C.J. Clopper, E.S. Pearson, The use of confidence or fiducial limits illustrated in the case of the binomial, Biometrika 26(4), 1934, pages 404–413, [https://doi.org/10.1093/biomet/26.4.404](https://doi.org/10.1093/biomet/26.4.404)
20. ^   Neyman, J. (1934). On the Two Different Aspects of the Representative Method: The Method of Stratified Sampling and the Method of Purposive Selection. Journal of the Royal Statistical Society, 97(4), 558–625. [https://doi.org/10.2307/2342192](https://doi.org/10.2307/2342192) (see Note I in the appendix)
21. J. Neyman (1935), Ann. Math. Statist. 6(3): 111-116 (September, 1935). [https://doi.org/10.1214/aoms/1177732585](https://doi.org/10.1214/aoms/1177732585)
22. ^   Neyman, J. (1970). A glance at some of my personal experiences in the process of research. In Scientists at Work: Festschrift in honour of Herman Wold. Edited by T. Dalenius, G. Karlsson, S. Malmquist. Almqvist & Wiksell, Stockholm. [https://worldcat.org/en/title/195948](https://worldcat.org/en/title/195948)
23. Pytkowski, W., The dependence of the income in small farms upon their area, the outlay and the capital invested in cows. (Polish, English summary) Bibliotaka Palawska, 1932.
24. [Fisher, R. A.](https://en.wikipedia.org/wiki/Ronald_Fisher) (1930). "Inverse Probability". *[Mathematical Proceedings of the Cambridge Philosophical Society](https://en.wikipedia.org/wiki/Mathematical_Proceedings_of_the_Cambridge_Philosophical_Society)*. **26** (4): 528–535. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1930PCPS...26..528F](https://ui.adsabs.harvard.edu/abs/1930PCPS...26..528F). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1017/S0305004100016297](https://doi.org/10.1017%2FS0305004100016297). [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[2440/15206](https://hdl.handle.net/2440%2F15206).
25. Altman, Douglas G. (1991). ["Statistics in medical journals: Developments in the 1980s"](https://onlinelibrary.wiley.com/doi/abs/10.1002/sim.4780101206). *Statistics in Medicine*. **10** (12): 1897–1913. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1002/sim.4780101206](https://doi.org/10.1002%2Fsim.4780101206). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1097-0258](https://search.worldcat.org/issn/1097-0258). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [1805317](https://pubmed.ncbi.nlm.nih.gov/1805317).
26. Gardner, Martin J.; Altman, Douglas G. (1988). ["Estimating with confidence"](https://doi.org/10.1136/bmj.296.6631.1210). *British Medical Journal*. **296** (6631): 1210–1211. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1136/bmj.296.6631.1210](https://doi.org/10.1136%2Fbmj.296.6631.1210). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [2545695](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2545695). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [3133015](https://pubmed.ncbi.nlm.nih.gov/3133015).

## Bibliography

- ["Confidence estimation"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society), 2001 \[1994\]
- [Fisher, R.A.](https://en.wikipedia.org/wiki/Ronald_Fisher) (1956) *Statistical Methods and Scientific Inference.* Oliver and Boyd, Edinburgh. (See p. 32.)
- Freund, J.E. (1962) *Mathematical Statistics* Prentice Hall, Englewood Cliffs, NJ. (See pp. 227–228.)
- [Hacking, I.](https://en.wikipedia.org/wiki/Ian_Hacking) (1965) *Logic of Statistical Inference.* Cambridge University Press, Cambridge. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-05165-7](https://en.wikipedia.org/wiki/Special:BookSources/0-521-05165-7)
- Keeping, E.S. (1962) *Introduction to Statistical Inference.* D. Van Nostrand, Princeton, NJ.
- [Kiefer, J.](https://en.wikipedia.org/wiki/Jack_Kiefer_(mathematician)) (1977). "Conditional Confidence Statements and Confidence Estimators (with discussion)". *Journal of the American Statistical Association*. **72** (360a): 789–827. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/01621459.1977.10479956](https://doi.org/10.1080%2F01621459.1977.10479956). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2286460](https://www.jstor.org/stable/2286460).
- Mayo, D. G. (1981) ["In defence of the Neyman–Pearson theory of confidence intervals"](http://www.phil.vt.edu/dmayo/PhilStatistics/In%20Defense%20of%20the%20Neyman-Pearson%20Theory%20of%20Confidence%20Intervals.pdf), *Philosophy of Science*, 48 (2), 269–280. [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [187185](https://www.jstor.org/stable/187185).
- Morey, R. D.; Hoekstra, R.; Rouder, J. N.; Lee, M. D.; Wagenmakers, E.-J. (2016). ["The fallacy of placing confidence in confidence intervals"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4742505). *Psychonomic Bulletin & Review*. **23** (1): 103–123. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3758/s13423-015-0947-8](https://doi.org/10.3758%2Fs13423-015-0947-8). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [4742505](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4742505). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [26450628](https://pubmed.ncbi.nlm.nih.gov/26450628).
- [Neyman, J.](https://en.wikipedia.org/wiki/Jerzy_Neyman) (1937) ["Outline of a Theory of Statistical Estimation Based on the Classical Theory of Probability"](https://www.jstor.org/stable/91337) *Philosophical Transactions of the Royal Society of London A,* **236**, 333–380. (Seminal work)
- Robinson, G.K. (1975). "Some Counterexamples to the Theory of Confidence Intervals". *Biometrika*. **62** (1): 155–161. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1093/biomet/62.1.155](https://doi.org/10.1093%2Fbiomet%2F62.1.155). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2334498](https://www.jstor.org/stable/2334498).
- Savage, L. J. (1962), *The Foundations of Statistical Inference*. Methuen, London.
- Smithson, M. (2003) *Confidence intervals*. Quantitative Applications in the Social Sciences Series, No. 140. Belmont, CA: SAGE Publications. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-7619-2499-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-7619-2499-9).

## External links

- [The Exploratory Software for Confidence Intervals tutorial programs that run under Excel](https://web.archive.org/web/20111122062933/http://www.latrobe.edu.au/psy/esci/)
- Confidence interval calculators for [R-Squares](https://web.archive.org/web/20090703130234/http://www.danielsoper.com/statcalc/calc28.aspx), [Regression Coefficients](https://web.archive.org/web/20090806085113/http://www.danielsoper.com/statcalc/calc26.aspx), and [Regression Intercepts](https://web.archive.org/web/20090404113030/http://www.danielsoper.com/statcalc/calc27.aspx)
- [Weisstein, Eric W.](https://en.wikipedia.org/wiki/Eric_W._Weisstein) ["Confidence Interval"](https://mathworld.wolfram.com/ConfidenceInterval.html). *[MathWorld](https://en.wikipedia.org/wiki/MathWorld)*.
- [CAUSEweb.org](http://www.causeweb.org/) Many resources for teaching statistics including Confidence Intervals.
- [An interactive introduction to Confidence Intervals](http://www.usablestats.com/tutorials/CI)
- *[Confidence Intervals: Confidence Level, Sample Size, and Margin of Error](http://demonstrations.wolfram.com/ConfidenceIntervalsConfidenceLevelSampleSizeAndMarginOfError/)* by Eric Schulz, the [Wolfram Demonstrations Project](https://en.wikipedia.org/wiki/Wolfram_Demonstrations_Project).
- *[Confidence Intervals in Public Health](http://health.utah.gov/opha/IBIShelp/ConfInts.pdf) [Archived](https://web.archive.org/web/20160809093746/http://health.utah.gov/opha/IBIShelp/ConfInts.pdf) 2016-08-09 at the [Wayback Machine](https://en.wikipedia.org/wiki/Wayback_Machine).* Straightforward description with examples and what to do about small sample sizes or rates near 0.
