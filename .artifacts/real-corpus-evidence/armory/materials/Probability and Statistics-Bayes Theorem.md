[[probability-statistics.base]]

> Source: [[Bayes Theorem|Bayes' theorem]]
> License: Wikipedia content is available under CC BY-SA 4.0.

**Bayes' theorem** (alternatively **Bayes' law** or **Bayes' rule**), named after [Thomas Bayes](https://en.wikipedia.org/wiki/Thomas_Bayes) ([/beɪz/](https://en.wikipedia.org/wiki/Help:IPA/English)), gives a mathematical rule for inverting [conditional probabilities](https://en.wikipedia.org/wiki/Conditional_probability), allowing the probability of a cause to be found given its effect. For example, with Bayes' theorem, the probability that a patient has a disease given that they tested positive for that disease can be found using the probability that the test yields a positive result when the disease is present. The theorem was developed in the 18th century by Bayes and independently by [Pierre-Simon Laplace](https://en.wikipedia.org/wiki/Pierre-Simon_Laplace).

One of Bayes' theorem's many applications is [Bayesian inference](https://en.wikipedia.org/wiki/Bayesian_inference), an approach to [statistical inference](https://en.wikipedia.org/wiki/Statistical_inference), where it is used to invert the probability of [observations](https://en.wikipedia.org/wiki/Realization_(probability) "Realization (probability)") given a model configuration (i.e., the [likelihood function](https://en.wikipedia.org/wiki/Likelihood_function)) to obtain the probability of the model configuration given the observations (i.e., the [posterior probability](https://en.wikipedia.org/wiki/Posterior_probability)).

## History

Bayes' theorem is named after [Thomas Bayes](https://en.wikipedia.org/wiki/Thomas_Bayes), a minister, statistician, and philosopher. Bayes used conditional probability to provide an algorithm (his Proposition 9) that uses evidence to calculate limits on an unknown parameter. His work was published in 1763 as *[An Essay Towards Solving a Problem in the Doctrine of Chances](https://en.wikipedia.org/wiki/An_Essay_Towards_Solving_a_Problem_in_the_Doctrine_of_Chances)*. Bayes studied how to compute a distribution for the probability parameter of a [binomial distribution](https://en.wikipedia.org/wiki/Binomial_distribution) (in modern terminology). After Bayes's death, his family gave his papers to a friend, the minister, philosopher, and mathematician [Richard Price](https://en.wikipedia.org/wiki/Richard_Price).

Price significantly edited the unpublished manuscript for two years before sending it to a friend who read it aloud at the [Royal Society](https://en.wikipedia.org/wiki/Royal_Society) on 23 December 1763. Price edited Bayes's major work "An Essay Towards Solving a Problem in the Doctrine of Chances" (1763), which appeared in *[Philosophical Transactions](https://en.wikipedia.org/wiki/Philosophical_Transactions)*, and contains Bayes' theorem. Price wrote an introduction to the paper that provides some of the philosophical basis of [Bayesian statistics](https://en.wikipedia.org/wiki/Bayesian_statistics) and chose one of the two solutions Bayes offered. In 1765, Price was elected a Fellow of the Royal Society in recognition of his work on Bayes's legacy. On 27 April, a letter sent to his friend [Benjamin Franklin](https://en.wikipedia.org/wiki/Benjamin_Franklin) was read out at the Royal Society, and later published, in which Price applies this work to population and computing 'life-annuities'.

Independently of Bayes, [Pierre-Simon Laplace](https://en.wikipedia.org/wiki/Pierre-Simon_Laplace) used conditional probability to formulate the relation of an updated [posterior probability](https://en.wikipedia.org/wiki/Posterior_probability) from a [prior probability](https://en.wikipedia.org/wiki/Prior_probability), given evidence. He reproduced and extended Bayes's results in 1774, apparently unaware of Bayes's work, and summarized his results in *[Théorie analytique des probabilités](https://en.wikipedia.org/wiki/Th%C3%A9orie_analytique_des_probabilit%C3%A9s)* (1812). The [Bayesian interpretation](https://en.wikipedia.org/wiki/Bayesian_probability) of probability was developed mainly by Laplace.

About 200 years later, [Sir Harold Jeffreys](https://en.wikipedia.org/wiki/Harold_Jeffreys) put Bayes's algorithm and Laplace's formulation on an [axiomatic](https://en.wikipedia.org/wiki/Axiomatic_system) basis, writing in a 1973 book that Bayes' theorem "is to the theory of probability what the [Pythagorean theorem](https://en.wikipedia.org/wiki/Pythagorean_theorem) is to geometry".

[Stephen Stigler](https://en.wikipedia.org/wiki/Stephen_Stigler) used a Bayesian argument to conclude that Bayes' theorem was discovered by [Nicholas Saunderson](https://en.wikipedia.org/wiki/Nicholas_Saunderson), a blind English mathematician, some time before Bayes, but that is disputed. [F. Thomas Bruss](https://en.wikipedia.org/wiki/F._Thomas_Bruss) reviewed Bayes's "An essay towards solving a problem in the doctrine of chances" as communicated by Price. He agreed with Stigler's analysis on many points, but not on the question of priority. Bruss underlined the intuitive part of Bayes's formula and added independent arguments about Bayes's probable motivation for his work. He concluded that, unless the contrary is proven, the name "Bayes' Theorem" or "Bayes' formula" is justifiable.

Martyn Hooper and Sharon McGrayne have argued that Price's contribution was substantial:

> By modern standards, we should refer to the Bayes–Price rule. Price discovered Bayes's work, recognized its importance, corrected it, contributed to the article, and found a use for it. The modern convention of employing Bayes's name alone is unfair but so entrenched that anything else makes little sense.

The "[Bayes factor](https://en.wikipedia.org/wiki/Bayes_factor)" or "likelihood" that appears when writing Bayes' theorem in [odds form](https://en.wikipedia.org/wiki/Odds) appears in the early 1940s work of [Alan Turing](https://en.wikipedia.org/wiki/Alan_Turing), who called it the "factor in favour of a proposition". In 1878, [Charles Sanders Peirce](https://en.wikipedia.org/wiki/Charles_Sanders_Peirce) used the logarithm of this factor as the "weight of evidence" for a proposition.

## Statement of theorem

Bayes' theorem is stated mathematically as the following equation:

$P(A\vert B)={\frac {P(B\vert A)P(A)}{P(B)}}$

where $A$ and $B$ are [events](https://en.wikipedia.org/wiki/Event_(probability_theory) "Event (probability theory)") and $P(B)\neq 0$.

- $P(A\vert B)$ is a [conditional probability](https://en.wikipedia.org/wiki/Conditional_probability): the probability of event $A$ occurring given that $B$ is true. It is also called the [posterior probability](https://en.wikipedia.org/wiki/Posterior_probability) of $A$ given $B$.
- $P(B\vert A)$ is also a conditional probability: the probability of event $B$ occurring given that $A$ is true. It can also be interpreted as the [likelihood](https://en.wikipedia.org/wiki/Likelihood_function) of $A$ given a fixed $B$.
- $P(A)$ and $P(B)$ are the probabilities of observing $A$ and $B$ respectively without any given conditions. $P(A)$, the quantity of interest, is often called 'the prior probability' (prior to new evidence). Technically both $P(A)$ and $P(B)$ could be called prior, unconditioned, or [marginal probabilities](https://en.wikipedia.org/wiki/Marginal_probability).

![[media/ee8dff79615c7753a8784721772a0d1153744fcd.png]]
Visual proof of Bayes' theorem

Bayes' theorem may be derived from the relation between [joint](https://en.wikipedia.org/wiki/Joint_probability_distribution) and conditional probabilities. The joint probability of the events $A$ and $B$ both happening, written $P(A\cap B)$, is equal to the conditional probability of $A$ given $B$ times the probability of $B$:

$$
P(A\cap B)=P(A\vert B)P(B).
$$

Likewise,

$$
P(A\cap B)=P(B\vert A)P(A).
$$

The two products must therefore be equal to each other:

$$
P(A\vert B)P(B)=P(B\vert A)P(A),
$$

and dividing both sides by $P(B)$ gives Bayes' theorem:

$$
P(A\vert B)={\frac {P(B\vert A)P(A)}{P(B)}},{\text{ if }}P(B)\neq 0.
$$

## Examples

### Medical diagnosis

Suppose that a doctor is testing a patient for the presence of a certain disease. The patient either has the disease or does not; the test returns either positive or negative. If the patient does not have the disease but the test returns a positive result, that is a *false positive.* If the patient has the disease and the test returns a positive result, that is a *true positive.* Bayes' theorem gives the means to calculate the probability that the patient has the disease given a positive test result, using quantities that specify how prevalent the disease is in the population and how well the test works. Let $E$ be the event that the patient has the disease. $P(E)$ is the probability that the patient has the disease. Let $F$ be the event that the patient tests positive. The probability that the patient has the disease given that they test positive is thus denoted $P(E|F)$. Bayes' theorem states:

$$
P(E|F)={\frac {P(F|E)P(E)}{P(F|E)P(E)+P(F|\neg E)P(\neg E)}}.
$$

Here, $P(E)$ is the *prevalence rate* of the disease, and $P(F|E)$ is the *true positive rate* or *test sensitivity.*

For example, if all patients with pancreatic cancer have certain symptoms, it does not follow that anyone who has those symptoms has pancreatic cancer. Assuming the incidence rate of pancreatic cancer is 1/100000, while 10/99999 healthy people have the symptoms, the probability that a person who has the symptoms has pancreatic cancer is 9.1%.

Based on incidence rate, the following table presents the corresponding numbers per 100,000 people.

<table class="wikitable">

Symptom

Cancer

Yes
No

Total

&#10;
Yes
1
0
1

No
10
99989
99999

Total
11
99989
100000

</table>

These numbers can then be used to calculate the probability that a patient who has the symptoms has cancer:

${\begin{aligned}P({\text{Cancer}}|{\text{Symptoms}})&={\frac {P({\text{Symptoms}}|{\text{Cancer}})P({\text{Cancer}})}{P({\text{Symptoms}})}}\\&={\frac {P({\text{Symptoms}}|{\text{Cancer}})P({\text{Cancer}})}{P({\text{Symptoms}}|{\text{Cancer}})P({\text{Cancer}})+P({\text{Symptoms}}|{\text{Non-Cancer}})P({\text{Non-Cancer}})}}\\[8pt]&={\frac {1\times 0.00001}{1\times 0.00001+(10/99999)\times 0.99999}}={\frac {1}{11}}\approx 9.1\%\end{aligned}}$

### Drug testing

Suppose a particular test for whether someone has been using a drug (e.g., [Substance D](https://en.wikipedia.org/wiki/A_Scanner_Darkly)) is 99% [sensitive](https://en.wikipedia.org/wiki/Sensitivity_(tests)), meaning the [true positive rate](https://en.wikipedia.org/wiki/True_positive_rate) (TPR) = 0.99. The test then has 99% true positive results (correct identification of drug use) for drug users. The test is also 99% [specific](https://en.wikipedia.org/wiki/Specificity_(tests)), meaning its [true negative rate](https://en.wikipedia.org/wiki/True_negative_rate) (TNR) = 0.99. Therefore, the test correctly identifies 99% of non-use for non-users, but also generates 1% false positives, or [false positive rate](https://en.wikipedia.org/wiki/False_positive_rate) (FPR) = 0.01, for non-users. Assuming 0.3% of people use the drug, Bayes' theorem gives the probability that a random person who tests positive is a drug user:

$$
{\begin{aligned}P({\text{User}}\vert {\text{Positive}})&={\frac {P({\text{Positive}}\vert {\text{User}})P({\text{User}})}{P({\text{Positive}})}}\\&={\frac {P({\text{Positive}}\vert {\text{User}})P({\text{User}})}{P({\text{Positive}}\vert {\text{User}})P({\text{User}})+P({\text{Positive}}\vert {\text{Non-user}})P({\text{Non-user}})}}\\[8pt]&={\frac {0.99\times 0.003}{0.99\times 0.003+0.01\times 0.997}}\approx 23\%.\end{aligned}}
$$

Consequently, even though the drug test is "99% accurate", most of its positive results will be false.

### Bent coins

An urn contains coins of three different types: A, B, and C. Coins of type A are fair and, when flipped, come up heads with probability 0.5. Coins of type B are biased and have probability 0.6 of turning up heads, and type-C coins come up heads with probability 0.9. The urn contains 2 type-A coins, 2 type-B coins and 1 type-C coin. A coin is drawn at random from the urn and flipped. Bayes' theorem gives the probability of a coin being of a given type given that it comes up heads:

$$
P(A|H)={\frac {P(H|A)P(A)}{P(H)}},
$$

and likewise for $P(B|H)$ and $P(C|H)$. The denominator can be found via the [[Law of Total Probability]]:

$$
P(H)=P(H|A)P(A)+P(H|B)P(B)+P(H|C)P(C).
$$

Assuming the coins are drawn from the urn at random, $P(A)=2/5$, $P(B)=2/5$, and $P(C)=1/5$. It follows that $P(H)=0.62$, and

$$
P(A|H)=0.2/0.62\approx 32\%.
$$

## Interpretations

![[media/7d6346392179ef1449504d7913981610edb9e056.png]]
A geometric visualization of Bayes' theorem using astronauts who may be suspicious (with eyebrows) and may be assassins (with daggers)

The interpretation of Bayes' rule depends on the [interpretation of probability](https://en.wikipedia.org/wiki/Probability_interpretations) ascribed to the terms. The two predominant classes of interpretation are described below.

### Bayesian interpretations

In [Bayesian (or epistemological) interpretations](https://en.wikipedia.org/wiki/Bayesian_probability), probability measures a "degree of belief". Bayes' theorem links the degree of belief in a proposition before and after accounting for evidence. For example, suppose it is believed with 50% certainty that a coin is twice as likely to land heads than tails. If the coin is flipped a number of times and the outcomes observed, that degree of belief will probably rise or fall, but might remain the same, depending on the results. For proposition *A* and evidence *B*,

- *P* (*A*), the *prior*, is the initial degree of belief in *A*.
- *P* (*A*\|*B*), the *posterior*, is the degree of belief after incorporating news that *B* is true.
- the quotient *P*(*B*\|*A*)/*P*(*B*) represents the support *B* provides for *A*.

For more on the application of Bayes' theorem under Bayesian interpretations of probability, see [Bayesian inference](https://en.wikipedia.org/wiki/Bayesian_inference).

### Frequentist interpretations

![[media/ff2ba2f316c0b2a16223ea983be7e9bfd0c7e644.png]]
Illustration of frequentist interpretation with [tree diagrams](https://en.wikipedia.org/wiki/Tree_diagram_(probability_theory))

In the [frequentist interpretations](https://en.wikipedia.org/wiki/Frequentist_interpretation_of_probability), probability measures a "proportion of outcomes". For example, suppose an experiment is performed many times. *P*(*A*) is the proportion of outcomes with property *A* (the prior) and *P*(*B*) is the proportion with property *B*. *P*(*B*\|*A*) is the proportion of outcomes with property *B* *out of* outcomes with property *A*, and *P*(*A*\|*B*) is the proportion of those with *A* *out of* those with *B* (the posterior).

The role of Bayes' theorem can be shown with tree diagrams. The two diagrams partition the same outcomes by *A* and *B* in opposite orders, to obtain the inverse probabilities. Bayes' theorem links the different partitionings.

#### Example

![[media/3e27f5411111ad26a1fb4b0831dbdbe6670f27a7.png]]
Tree diagram illustrating the beetle example. <em>R, C, P</em> and ${\overline {P}}$ are the events rare, common, pattern and no pattern. Percentages in parentheses are calculated. Three independent values are given, so it is possible to calculate the inverse tree.

An [entomologist](https://en.wikipedia.org/wiki/Entomology) spots what might, due to the pattern on its back, be a rare [subspecies](https://en.wikipedia.org/wiki/Subspecies) of [beetle](https://en.wikipedia.org/wiki/Beetle). A full 98% of the members of the rare subspecies have the pattern, so *P*(Pattern\|Rare) = 98%. Only 5% of members of the common subspecies have the pattern. The rare subspecies is 0.1% of the total population. How likely is the beetle having the pattern to be rare: what is *P*(Rare\|Pattern)?

Since any beetle is either rare or common, Bayes' theorem can be applied as follows: 

$$
{\begin{aligned}P({\text{Rare}}\vert {\text{Pattern}})&={\frac {P({\text{Pattern}}\vert {\text{Rare}})\,P({\text{Rare}})}{P({\text{Pattern}})}}\\[8pt]&={\tfrac {P({\text{Pattern}}\vert {\text{Rare}})\,P({\text{Rare}})}{P({\text{Pattern}}\vert {\text{Rare}})\,P({\text{Rare}})+P({\text{Pattern}}\vert {\text{Common}})\,P({\text{Common}})}}\\[8pt]&={\frac {0.98\times 0.001}{0.98\times 0.001+0.05\times 0.999}}\\[8pt]&\approx 1.9\%\end{aligned}}
$$

## Forms

### Events

#### Simple form

For events *A* and *B*, provided that *P*(*B*) ≠ 0,

$P(A|B)={\frac {P(B|A)P(A)}{P(B)}}.$

In many applications, for instance in [Bayesian inference](https://en.wikipedia.org/wiki/Bayesian_inference), the event *B* is fixed in the discussion and we wish to consider the effect of its having been observed on our belief in various possible events *A*. In such situations the denominator of the last expression, the probability of the given evidence *B*, is fixed; what we want to vary is *A*. Bayes' theorem shows that the posterior probabilities are [proportional](https://en.wikipedia.org/wiki/Proportionality_(mathematics) "Proportionality (mathematics)") to the numerator, so the last equation becomes:

$P(A|B)\propto P(A)\cdot P(B|A).$

In other words, the posterior is proportional to the prior times the likelihood.

If events *A*<sub>1</sub>, *A*<sub>2</sub>, ..., are mutually exclusive and exhaustive, i.e., one of them is certain to occur but no two can occur together, then:

$$
P(B)=\sum _{i}P(B|A_{i})P(A_{i})
$$

for any event *B.* Substituting this expression for $P(B)$ into the denominator of the earlier equation gives:

$$
P(A_{i}|B)={\frac {P(A_{i})P(B|A_{i})}{\sum _{j}P(A_{i})P(B|A_{i})}}.
$$

#### For two competing hypotheses

<table class="wikitable floatright">
<caption>[Contingency table](https://en.wikipedia.org/wiki/Contingency_table)</caption>

  Background

Proposition

B
$\lnot B$<br />
(not B)
Total

&#10;
A
$P(B|A)\cdot P(A)$<br />
$=P(A|B)\cdot P(B)$
$P(\neg B|A)\cdot P(A)$<br />
$=P(A|\neg B)\cdot P(\neg B)$
$P(A)$

$\neg A$<br />
(not A)
$P(B|\neg A)\cdot P(\neg A)$<br />
$=P(\neg A|B)\cdot P(B)$
$P(\neg B|\neg A)\cdot P(\neg A)$<br />
$=P(\neg A|\neg B)\cdot P(\neg B)$
$P(\neg A)$=<br />
$1-P(A)$

Total
$P(B)$
$P(\neg B)=1-P(B)$
1

</table>

The events $A$ and not-$A$, written $\neg A$, are a mutually exclusive and exhaustive pair. Therefore the previous formula can be applied, and the sum in the denominator will have only two terms:

$P(A|B)={\frac {P(B|A)P(A)}{P(B|A)P(A)+P(B|\neg A)P(\neg A)}}.$

If *A* denotes a proposition and *B* the evidence or background *B*, then

- $P(A)$ is the [prior probability](https://en.wikipedia.org/wiki/Prior_probability), the initial degree of belief in *A*.
- $P(\neg A)$ is the corresponding initial degree of belief that *A* is false, which is $P(\neg A)=1-P(A)$
- $P(B|A)$ is the [conditional probability](https://en.wikipedia.org/wiki/Conditional_probability) or likelihood, the degree of belief in *B* given that *A* is true.
- $P(B|\neg A)$ is the [conditional probability](https://en.wikipedia.org/wiki/Conditional_probability) or likelihood, the degree of belief in *B* given that *A* is false.
- $P(A|B)$ is the [posterior probability](https://en.wikipedia.org/wiki/Posterior_probability), the probability of *A* after taking into account *B*.

### Random variables

![[media/edd64e13ab82ca604d4a462dbee1e49d3d4a22ec.png]]
Bayes' theorem applied to an event space generated by continuous random variables <em>X</em> and <em>Y</em> with known probability distributions. There exists an instance of Bayes' theorem for each point in the [domain](https://en.wikipedia.org/wiki/Domain_of_a_function). In practice, these instances might be parametrized by writing the specified probability densities as a [function](https://en.wikipedia.org/wiki/Function_(Mathematics)) of <em>x</em> and <em>y</em>.

For two continuous [random variables](https://en.wikipedia.org/wiki/Random_variable) *X* and *Y*, Bayes' theorem may be analogously derived from the definition of [conditional density](https://en.wikipedia.org/wiki/Conditional_density):

$f_{X\vert Y=y}(x)={\frac {f_{X,Y}(x,y)}{f_{Y}(y)}}$

$f_{Y\vert X=x}(y)={\frac {f_{X,Y}(x,y)}{f_{X}(x)}}$

Bayes' theorem states:

$f_{X\vert Y=y}(x)={\frac {f_{Y\vert X=x}(y)f_{X}(x)}{f_{Y}(y)}}.$

This holds for values $x$ and $y$ within the [support](https://en.wikipedia.org/wiki/Support_(mathematics) "Support (mathematics)") of *X* and *Y*, ensuring $f_{X}(x)>0$ and $f_{Y}(y)>0$.

#### General case

Let $P_{Y}^{x}$ be the conditional distribution of $Y$ given $X=x$ and let $P_{X}$ be the distribution of $X$. The joint distribution is then $P_{X,Y}(dx,dy)=P_{Y}^{x}(dy)P_{X}(dx)$. The conditional distribution $P_{X}^{y}$ of $X$ given $Y=y$ is then determined by

$$
P_{X}^{y}(A)=E(1_{A}(X)|Y=y)
$$

Existence and uniqueness of the needed [conditional expectation](https://en.wikipedia.org/wiki/Conditional_expectation) is a consequence of the [Radon–Nikodym theorem](https://en.wikipedia.org/wiki/Radon%E2%80%93Nikodym_theorem). [Kolmogorov](https://en.wikipedia.org/wiki/Andrey_Kolmogorov) formulated this in 1933. He underlined the importance of conditional probability, writing, "I wish to call attention to ... the theory of conditional probabilities and conditional expectations". Bayes' theorem determines the posterior distribution from the prior distribution. Uniqueness requires continuity assumptions. Bayes' theorem can be generalized to include improper prior distributions such as the uniform distribution on the real line. Modern [[Markov Chain Monte Carlo]] methods have boosted the importance of Bayes' theorem, including in cases with improper priors.

### Bayes' rule in odds form

Probabilities are sometimes specified in terms of [odds](https://en.wikipedia.org/wiki/Odds). For any proposition $A$, the ratio of the probability that $A$ is true to the probability that $A$ is false is called the odds on $A$. Bayes' theorem can be written using odds as follows. First, apply Bayes' theorem to the probability that $A$ is true given some other proposition $B$:

$$
P(A|B)=P(B){\frac {P(B|A)}{P(A)}}.
$$

Likewise, Bayes' theorem holds for the probability that $A$ is false:

$$
P(\neg A|B)=P(B){\frac {P(B|\neg A)}{P(\neg A)}}.
$$

Dividing these two equations, the probability $P(B)$ drops out:

$$
{\frac {P(A|B)}{P(\neg A|B)}}={\frac {P(A)}{P(\neg A)}}{\frac {P(B|A)}{P(B|\neg A)}}.
$$

Consequently, the odds of $A$ given $B$ are the odds of $A$ multiplied by the ratio $P(B|A)/P(B|\neg A)$, a quantity called the [Bayes factor](https://en.wikipedia.org/wiki/Bayes_factor) or [likelihood ratio](https://en.wikipedia.org/wiki/Likelihood_ratio). In symbols:

$$
O(A|B)=O(A){\frac {P(B|A)}{P(B|\neg A)}}.
$$

This is often summarized by saying that the *posterior odds* are the *prior odds* times the likelihood.

For example,<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup> if a medical test has a [sensitivity](https://en.wikipedia.org/wiki/Sensitivity_and_specificity) of 90% and a [specificity](https://en.wikipedia.org/wiki/Sensitivity_and_specificity) of 91%, then the positive Bayes factor is $\Lambda _{+}=P({\text{True Positive}})/P({\text{False Positive}})=90\%/(100\%-91\%)=10$. If the [prevalence](https://en.wikipedia.org/wiki/Prevalence) of this disease is 9.09% and we take that as the prior probability, then the prior odds is about 1:10. So after receiving a positive test result, the posterior odds of having the disease becomes 1:1, which means that the posterior probability of having the disease is 50%. If a second test is performed in serial testing, and it is also positive, then the posterior odds of having the disease becomes 10:1, which means a posterior probability of about 90.91%. The negative Bayes factor can be calculated to be 91%/(100%-90%) = 9.1, so if the second test is negative, then the posterior odds of having the disease is 1:9.1, which means a posterior probability of about 9.9%.

The example above can also be understood with more solid numbers: assume the patient taking the test is from a group of 1,000 people, 91 of whom have the disease (prevalence of 9.1%). If all 1,000 take the test, 82 of those with the disease will get a true positive result (sensitivity of 90.1%), nine will get a false negative result ([false negative rate](https://en.wikipedia.org/wiki/False_positives_and_false_negatives) of 9.9%), 827 will get a true negative result (specificity of 91.0%), and 82 will get a false positive result (false positive rate of 9.0%). Before taking any test, the patient's odds of having the disease is 91:909. After receiving a positive result, the patient's odds for having the disease is

${\frac {91}{909}}\times {\frac {90.1\%}{9.0\%}}={\frac {91\times 90.1\%}{909\times 9.0\%}}=1:1$

which is consistent with the fact that there are 82 true positives and 82 false positives in the group of 1,000.

## Generalizations

### Bayes' theorem for 3 events

A version of Bayes' theorem for 3 events results from the addition of a third event $C$, with $P(C)>0,$ on which all probabilities are conditioned:

$P(A\vert B\cap C)={\frac {P(B\vert A\cap C)\,P(A\vert C)}{P(B\vert C)}}$

This can be deduced as follows. Using the [chain rule](https://en.wikipedia.org/wiki/Chain_rule_(probability) "Chain rule (probability)")

$P(A\cap B\cap C)=P(A\vert B\cap C)\,P(B\vert C)\,P(C)$

And, on the other hand

$P(A\cap B\cap C)=P(B\cap A\cap C)=P(B\vert A\cap C)\,P(A\vert C)\,P(C)$

The desired result is obtained by identifying both expressions and solving for $P(A\vert B\cap C)$.

### Inference rules

In [subjective interpretations](https://en.wikipedia.org/wiki/Bayesian_probability) of probability theory, an event's probability is regarded as an agent's belief that the event will happen. Bayes' theorem is widely invoked to justify how an agent should update or modify their beliefs after receiving new information. If an agent assigns the probability $P(A)$ to the event $A$, $P(B)$ to the event $B$, and $P(B|A)$ to the event $B$ conditional on $A$, Bayes' theorem gives the value of $P(A|B)$. Suppose that, after the agent has made these probability assignments, event $B$ happens. An agent who follows *Bayesian updating,* also known as updating by *conditionalization,* will change their probability for event $A$ from the old value $P(A)$ to the new value $P'(A)=P(A|B)$. Conditionalization is not the only updating rule that might be considered rational. The issue of which assumptions can be invoked to constrain updating rules remains somewhat controversial.

### Quantum

In [quantum mechanics](https://en.wikipedia.org/wiki/Quantum_mechanics), probability distributions are generalized to [density matrices](https://en.wikipedia.org/wiki/Density_matrix), arrays of [complex numbers](https://en.wikipedia.org/wiki/Complex_number) that describe the preparation of a quantum system. A *quantum Bayes rule* can be formulated that expresses how density matrices are updated as new experimental data about a system is obtained.

## Applications

### Recreational mathematics

Bayes' rule and computing [conditional probabilities](https://en.wikipedia.org/wiki/Conditional_probability) provide a method to solve a number of popular puzzles, such as the [Three Prisoners problem](https://en.wikipedia.org/wiki/Three_Prisoners_problem), the [Monty Hall problem](https://en.wikipedia.org/wiki/Monty_Hall_problem), the [Boy or Girl paradox](https://en.wikipedia.org/wiki/Boy_or_Girl_paradox), and the [two envelopes problem](https://en.wikipedia.org/wiki/Two_envelopes_problem).

### Genetics

In genetics, Bayes' rule can be used to estimate the probability that someone has a specific genotype. Many people seek to assess their chances of being affected by a genetic disease or their likelihood of being a carrier for a recessive gene of interest. A Bayesian analysis can be done based on family history or [genetic testing](https://en.wikipedia.org/wiki/Genetic_testing) to predict whether someone will develop a disease or pass one on to their children. Genetic testing and prediction is common among couples who plan to have children but are concerned that they may both be carriers for a disease, especially in communities with low genetic variance.

|  |  |  |
|----|----|----|
| Hypothesis | Hypothesis 1: Patient is a carrier | Hypothesis 2: Patient is not a carrier |
| Prior Probability | 1/2 | 1/2 |
| Conditional Probability that all four offspring will be unaffected | (1/2) ⋅ (1/2) ⋅ (1/2) ⋅ (1/2) = 1/16 | About 1 |
| Joint Probability | (1/2) ⋅ (1/16) = 1/32 | (1/2) ⋅ 1 = 1/2 |
| Posterior Probability | (1/32) / (1/32 + 1/2) = 1/17 | (1/2) / (1/32 + 1/2) = 16/17 |

Above is an example of a Bayesian analysis table for a female's risk for a disease based on the knowledge that the disease is present in her siblings but not in her parents or any of her four children. Based solely on the status of the subject's siblings and parents, she is equally likely to be a carrier as to be a non-carrier (this likelihood is denoted by the prior hypothesis). The probability that the subject's four sons would all be unaffected is 1/16 (1⁄2⋅1⁄2⋅1⁄2⋅1⁄2) if she is a carrier and about 1 if she is a non-carrier (this is the conditional probability). The joint probability reconciles these two predictions by multiplying them together. The last line (the posterior probability) is calculated by dividing the joint probability for each hypothesis by the sum of both joint probabilities.

Parental genetic testing can detect around 90% of known disease alleles in parents that can lead to carrier or affected status in their children. [Cystic fibrosis](https://en.wikipedia.org/wiki/Cystic_fibrosis) is a heritable disease caused by an [autosomal recessive](https://en.wikipedia.org/wiki/Dominance_(genetics) "Dominance (genetics)") mutation on the [CFTR](https://en.wikipedia.org/wiki/Cystic_fibrosis_transmembrane_conductance_regulator) gene, located on [chromosome 7](https://en.wikipedia.org/wiki/Chromosome_7).

Here is a Bayesian analysis of a female patient with a family history of cystic fibrosis (CF) who has tested negative for CF, demonstrating how the method was used to determine her risk of having a child born with CF: because the patient is unaffected, she is either [homozygous](https://en.wikipedia.org/wiki/Zygosity) for the wild-type allele, or heterozygous. To establish prior probabilities, a [Punnett square](https://en.wikipedia.org/wiki/Punnett_square) is used, based on the knowledge that neither parent was affected by the disease but both could have been carriers:

<table class="wikitable" style="text-align:center;">

Mother

Father

W
<p>Homozygous for the wild-<br />
type allele (a non-carrier)</p>
M
<p>Heterozygous<br />
(a CF carrier)</p>

&#10;
W
<p>Homozygous for the wild-<br />
type allele (a non-carrier)</p>
WW
MW

M
<p>Heterozygous (a CF carrier)</p>
MW
MM
<p>(affected by cystic fibrosis)</p>

</table>

Given that the patient is unaffected, there are only three possibilities. Within these three, there are two scenarios in which the patient carries the mutant allele. Thus the prior probabilities are 2⁄3 and 1⁄3.

Next, the patient undergoes genetic testing and tests negative for cystic fibrosis. This test has a 90% detection rate, so the conditional probabilities of a negative test are 1/10 and 1. Finally, the joint and posterior probabilities are calculated as before.

|  |  |  |
|----|----|----|
| Hypothesis | Hypothesis 1: Patient is a carrier | Hypothesis 2: Patient is not a carrier |
| Prior Probability | 2/3 | 1/3 |
| Conditional Probability of a negative test | 1/10 | 1 |
| Joint Probability | 1/15 | 1/3 |
| Posterior Probability | 1/6 | 5/6 |

After carrying out the same analysis on the patient's male partner (with a negative test result), the chance that their child is affected is the product of the parents' respective posterior probabilities for being carriers times the chance that two carriers will produce an affected offspring (1⁄4).

Bayesian analysis can be done using phenotypic information associated with a genetic condition. When combined with genetic testing, this analysis becomes much more complicated. Cystic fibrosis, for example, can be identified in a fetus with an ultrasound looking for an echogenic bowel, one that appears brighter than normal on a scan. This is not a foolproof test, as an echogenic bowel can be present in a perfectly healthy fetus. Parental genetic testing is very influential in this case, where a phenotypic facet can be overly influential in probability calculation. In the case of a fetus with an echogenic bowel, with a mother who has been tested and is known to be a CF carrier, the posterior probability that the fetus has the disease is very high (0.64). But once the father has tested negative for CF, the posterior probability drops significantly (to 0.16).

Risk factor calculation is a powerful tool in genetic counseling and reproductive planning but cannot be treated as the only important factor. As above, incomplete testing can yield falsely high probability of carrier status, and testing can be financially inaccessible or unfeasible when a parent is not present.

## See also

- ![[media/1a9c6ad1ccebbc090fc7cd1c94d2142489246997.png]][Mathematics portal](https://en.wikipedia.org/wiki/Portal:Mathematics)

- [Bayesian epistemology](https://en.wikipedia.org/wiki/Bayesian_epistemology)
- [Bayesian network](https://en.wikipedia.org/wiki/Bayesian_network)
- [Bayesian persuasion](https://en.wikipedia.org/wiki/Bayesian_persuasion)
- [Inductive probability](https://en.wikipedia.org/wiki/Inductive_probability)
- [QBism](https://en.wikipedia.org/wiki/QBism)
- [Regular conditional probability](https://en.wikipedia.org/wiki/Regular_conditional_probability)
- *[Why Most Published Research Findings Are False](https://en.wikipedia.org/wiki/Why_Most_Published_Research_Findings_Are_False)*, a 2005 essay in [metascience](https://en.wikipedia.org/wiki/Metascience) by John Ioannidis

## Notes

1.  Laplace refined Bayes's theorem over a period of decades: 
    - Laplace announced his independent discovery of Bayes' theorem in: Laplace (1774) "Mémoire sur la probabilité des causes par les événements", "Mémoires de l'Académie royale des Sciences de MI (Savants étrangers)", **4**: 621–656. Reprinted in: Laplace, "Oeuvres complètes" (Paris, France: Gauthier-Villars et fils, 1841), vol. 8, pp. 27–65. Available on-line at: [Gallica](http://gallica.bnf.fr/ark:/12148/bpt6k77596b/f32.image). Bayes' theorem appears on p. 29.
    - Laplace presented a refinement of Bayes' theorem in: Laplace (read: 1783 / published: 1785) "Mémoire sur les approximations des formules qui sont fonctions de très grands nombres", "Mémoires de l'Académie royale des Sciences de Paris", 423–467. Reprinted in: Laplace, "Oeuvres complètes" (Paris, France: Gauthier-Villars et fils, 1844), vol. 10, pp. 295–338. Available on-line at: [Gallica](http://gallica.bnf.fr/ark:/12148/bpt6k775981/f218.image.langEN). Bayes' theorem is stated on page 301.
    - See also: Laplace, "Essai philosophique sur les probabilités" (Paris, France: Mme. Ve. Courcier \[Madame veuve (i.e., widow) Courcier\], 1814), [page 10](https://books.google.com/books?id=rDUJAAAAIAAJ&pg=PA10). English translation: Pierre Simon, Marquis de Laplace with F. W. Truscott and F. L. Emory, trans., "A Philosophical Essay on Probabilities" (New York, New York: John Wiley & Sons, 1902), [p. 15](https://google.com/books?id=WxoPAAAAIAAJ&pg=PA15#v=onepage).

## References

1.  ["Richard Price - Biography"](http://web.archive.org/web/20250821204231/https://mathshistory.st-andrews.ac.uk/Biographies/Price/). *Maths History*. Archived from [the original](https://mathshistory.st-andrews.ac.uk/Biographies/Price/) on 2025-08-21. Retrieved 2025-12-20.
2.  Frame, Paul (2015). [Liberty's Apostle](https://www.uwp.co.uk/book/libertys-apostle-richard-price-his-life-and-times/). Wales: University of Wales Press. p. 44. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1783162161](https://en.wikipedia.org/wiki/Special:BookSources/978-1783162161). Retrieved 23 February 2021.
3.  Allen, Richard (1999). [David Hartley on Human Nature](https://books.google.com/books?id=NCu6HhGlAB8C&pg=PA243). SUNY Press. pp. 243–244. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0791494516](https://en.wikipedia.org/wiki/Special:BookSources/978-0791494516). Retrieved 16 June 2013.
4.  Bayes, Thomas & Price, Richard (1763). ["An Essay towards solving a Problem in the Doctrine of Chance. By the late Rev. Mr. Bayes, communicated by Mr. Price, in a letter to John Canton, A.M.F.R.S."](https://doi.org/10.1098%2Frstl.1763.0053) *Philosophical Transactions of the Royal Society of London*. **53**: 370–418. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1098/rstl.1763.0053](https://doi.org/10.1098%2Frstl.1763.0053).
5.  Holland, J. D. (1968). "An Eighteenth-Century Pioneer Richard Price, D.D., F.R.S. (1723-–791)". *Notes and Records of the Royal Society of London*. **23** (1): 43–64. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1098/rsnr.1968.0009](https://doi.org/10.1098%2Frsnr.1968.0009). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [530851](https://www.jstor.org/stable/530851).
6.  Price, Richard (1991). [Price: Political Writings](https://books.google.com/books?id=xdH-gjy2vzUC&pg=PR23). Cambridge University Press. p. xxiii. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0521409698](https://en.wikipedia.org/wiki/Special:BookSources/978-0521409698). Retrieved 16 June 2013.
7.  , p. 314.
8.  Daston, Lorraine (1988). [Classical Probability in the Enlightenment](https://books.google.com/books?id=oq8XNbKyUewC&pg=PA268). Princeton Univ Press. p. 268. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0691084971](https://en.wikipedia.org/wiki/Special:BookSources/0691084971).
9.  [Stigler, Stephen M.](https://en.wikipedia.org/wiki/Stephen_Stigler) (1986). ["Inverse Probability"](https://books.google.com/books?id=M7yvkERHIIMC&pg=PA99). *The History of Statistics: The Measurement of Uncertainty Before 1900*. Harvard University Press. pp. 99–138. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0674403413](https://en.wikipedia.org/wiki/Special:BookSources/978-0674403413).
10. [Jeffreys, Harold](https://en.wikipedia.org/wiki/Harold_Jeffreys) (1973). [Scientific Inference](https://archive.org/details/scientificinfere0000jeff) (3rd ed.). [Cambridge University Press](https://en.wikipedia.org/wiki/Cambridge_University_Press). p. [31](https://archive.org/details/scientificinfere0000jeff/page/31). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0521180788](https://en.wikipedia.org/wiki/Special:BookSources/978-0521180788).
11. [Stigler, Stephen M.](https://en.wikipedia.org/wiki/Stephen_Stigler) (1983). "Who Discovered Bayes' Theorem?". *The American Statistician*. **37** (4): 290–296. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/00031305.1983.10483122](https://doi.org/10.1080%2F00031305.1983.10483122).
12. de Vaux, Richard; Velleman, Paul; Bock, David (2016). *Stats, Data and Models* (4th ed.). Pearson. pp. 380–381. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0321986498](https://en.wikipedia.org/wiki/Special:BookSources/978-0321986498).
13. Edwards, A. W. F. (1986). "Is the Reference in Hartley (1749) to Bayesian Inference?". *The American Statistician*. **40** (2): 109–110. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/00031305.1986.10475370](https://doi.org/10.1080%2F00031305.1986.10475370).
14. Bruss, F. Thomas (2014). "250 years of "An essay towards solving a problem in the doctrine of chances" communicated by Price to the Royal Society". *Jahresbericht der Deutschen Mathematiker-Vereinigung*. **115** (3): 129–133. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1365/s13291-013-0069-z](https://doi.org/10.1365%2Fs13291-013-0069-z).
15. Hooper, Martyn (2013). ["Richard Price, Bayes' theorem, and God"](https://doi.org/10.1111%2Fj.1740-9713.2013.00638.x). *Significance*. **10** (1): 36–39. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1111/j.1740-9713.2013.00638.x](https://doi.org/10.1111%2Fj.1740-9713.2013.00638.x). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [153704746](https://api.semanticscholar.org/CorpusID:153704746).
16. ^   McGrayne, S. B. (2011). [The Theory That Would Not Die: How Bayes' Rule Cracked the Enigma Code, Hunted Down Russian Submarines & Emerged Triumphant from Two Centuries of Controversy](https://archive.org/details/theorythatwouldn0000mcgr). [Yale University Press](https://en.wikipedia.org/wiki/Yale_University_Press). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0300188226](https://en.wikipedia.org/wiki/Special:BookSources/978-0300188226).
17. [Good, I. J.](https://en.wikipedia.org/wiki/I._J._Good) (1979). "Studies in the History of Probability and Statistics. XXXVII A. M. Turing's statistical work in World War II". *[Biometrika](https://en.wikipedia.org/wiki/Biometrika)*. **66** (2): 393–396. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1093/biomet/66.2.393](https://doi.org/10.1093%2Fbiomet%2F66.2.393). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0548210](https://mathscinet.ams.org/mathscinet-getitem?mr=0548210).
18. Stuart, A.; Ord, K. (1994), *Kendall's Advanced Theory of Statistics: Volume I – Distribution Theory*, [Edward Arnold](https://en.wikipedia.org/wiki/Edward_Arnold_(publisher) "Edward Arnold (publisher)"), §8.7
19. Downey, Allen B. (2012). [Think Bayes: Bayesian Statistics Made Simple](https://open.umn.edu/opentextbooks/textbooks/288). Green Tea Press. pp. 3–4. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9781449370787](https://en.wikipedia.org/wiki/Special:BookSources/9781449370787) – via Open Textbook Library, University of Minnesota.
20. ^   Bernardo, José M.; [Smith, Adrian F. M.](https://en.wikipedia.org/wiki/Adrian_Smith_(statistician) "Adrian Smith (statistician)") (2000) \[1994\]. *Bayesian Theory*. John Wiley & Sons. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-92416-4](https://en.wikipedia.org/wiki/Special:BookSources/0-471-92416-4).
21. Kane, Frank (2017). *Hands-On Data Science and Python Machine Learning*. Packt Publishing. p. 131. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-78728-074-8](https://en.wikipedia.org/wiki/Special:BookSources/978-1-78728-074-8).
22. Orloff, Jeremy; Bloom, Jonathan (2022). ["Reading 11: Bayesian Updating with Discrete Priors"](https://ocw.mit.edu/courses/18-05-introduction-to-probability-and-statistics-spring-2022/resources/mit18_05_s22_class11-prep_pdf/). *18.05: Introduction to Probability and Statistics*. Retrieved 2026-02-28 – via [MIT OpenCourseWare](https://en.wikipedia.org/wiki/MIT_OpenCourseWare).
23. [Diaconis, Persi](https://en.wikipedia.org/wiki/Persi_Diaconis); [Skyrms, Brian](https://en.wikipedia.org/wiki/Brian_Skyrms) (2018). *Ten Great Ideas About Chance*. Princeton University Press. pp. 22–27. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-691-17416-7](https://en.wikipedia.org/wiki/Special:BookSources/978-0-691-17416-7).
24. [Misak, Cheryl](https://en.wikipedia.org/wiki/Cheryl_Misak) (2020). *Frank Ramsey: A Sheer Excess of Powers*. Oxford University Press. pp. 268–269. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-19-875535-7](https://en.wikipedia.org/wiki/Special:BookSources/978-0-19-875535-7).
25. Hájek, Alan (November 16, 2023). ["Interpretations of Probability"](https://plato.stanford.edu/entries/probability-interpret/). In [Zalta, Edward N.](https://en.wikipedia.org/wiki/Edward_N._Zalta) (ed.). *[Stanford Encyclopedia of Philosophy](https://en.wikipedia.org/wiki/Stanford_Encyclopedia_of_Philosophy)*. [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1095-5054](https://search.worldcat.org/issn/1095-5054). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [429049174](https://search.worldcat.org/oclc/429049174).
26. ^     Lee, Peter M. (2012). "Chapter 1". [Bayesian Statistics](https://www.york.ac.uk/depts/maths/histstat/pml1/bayes/book.htm). [Wiley](https://en.wikipedia.org/wiki/John_Wiley_%26_Sons). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-1183-3257-3](https://en.wikipedia.org/wiki/Special:BookSources/978-1-1183-3257-3).
27. ["Bayes' Theorem: Introduction"](https://web.archive.org/web/20040821012342/http://www.trinity.edu/cbrown/bayesweb/). *Trinity University*. Archived from [the original](http://www.trinity.edu/cbrown/bayesweb/) on 21 August 2004. Retrieved 5 August 2014.
28. [Kolmogorov, A.N.](https://en.wikipedia.org/wiki/Andrey_Kolmogorov) (1933) \[1956\]. *Foundations of the Theory of Probability*. Chelsea Publishing Company.
29. Tjur, Tue (1980). [Probability based on Radon measures](http://archive.org/details/probabilitybased0000tjur). New York: Wiley. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-27824-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-27824-5).
30. Taraldsen, Gunnar; Tufto, Jarle; Lindqvist, Bo H. (2021-07-24). ["Improper priors and improper posteriors"](https://doi.org/10.1111%2Fsjos.12550). *Scandinavian Journal of Statistics*. **49** (3): 969–991. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1111/sjos.12550](https://doi.org/10.1111%2Fsjos.12550). [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[11250/2984409](https://hdl.handle.net/11250%2F2984409). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0303-6898](https://search.worldcat.org/issn/0303-6898). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [237736986](https://api.semanticscholar.org/CorpusID:237736986).
31. [Robert, Christian P.](https://en.wikipedia.org/wiki/Christian_Robert); [Casella, George](https://en.wikipedia.org/wiki/George_Casella) (2004). *Monte Carlo Statistical Methods*. Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1475741452](https://en.wikipedia.org/wiki/Special:BookSources/978-1475741452). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [1159112760](https://search.worldcat.org/oclc/1159112760).
32. ^   [Jaynes, E. T.](https://en.wikipedia.org/wiki/Edwin_Thompson_Jaynes) (2003). *Probability Theory: The Logic of Science*. Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-59271-2](https://en.wikipedia.org/wiki/Special:BookSources/0-521-59271-2).
33. [Koller, D.](https://en.wikipedia.org/wiki/Daphne_Koller); [Friedman, N.](https://en.wikipedia.org/wiki/Nir_Friedman) (2009). [Probabilistic Graphical Models](https://web.archive.org/web/20140427083249/http://pgm.stanford.edu/). Massachusetts: MIT Press. p. 1208. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-262-01319-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-262-01319-2). Archived from [the original](http://pgm.stanford.edu/) on 2014-04-27.
34. [Hacking, Ian](https://en.wikipedia.org/wiki/Ian_Hacking) (December 1967). "Slightly More Realistic Personal Probability". *Philosophy of Science*. **34** (4): 316. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1086/288169](https://doi.org/10.1086%2F288169). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [14344339](https://api.semanticscholar.org/CorpusID:14344339).
35. [Diaconis, Persi](https://en.wikipedia.org/wiki/Persi_Diaconis); Zabell, Sandy L. (1982). "Updating subjective probability". *Journal of the American Statistical Association*. **77** (380): 822–830. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/01621459.1982.10477893](https://doi.org/10.1080%2F01621459.1982.10477893).
36. [Fuchs, Christopher A.](https://en.wikipedia.org/wiki/Christopher_A._Fuchs); Schack, Rüdiger (2012). "Bayesian conditioning, the reflection principle, and quantum decoherence". In Ben-Menahem, Yemima; Hemmo, Meir (eds.). *Probability in Physics*. Springer. pp. 233–247. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1103.5950](https://arxiv.org/abs/1103.5950). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-3-642-21329-8_15](https://doi.org/10.1007%2F978-3-642-21329-8_15). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-642-21328-1](https://en.wikipedia.org/wiki/Special:BookSources/978-3-642-21328-1).
37. [van Fraassen, Bas C.](https://en.wikipedia.org/wiki/Bas_van_Fraassen) (September 2023). "Reflection and Conditionalization: Comments on Michael Rescorla". *[Noûs](https://en.wikipedia.org/wiki/No%C3%BBs)*. **57** (3): 539–552. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1111/nous.12416](https://doi.org/10.1111%2Fnous.12416).
38. Leifer, M.; [Spekkens, R. W.](https://en.wikipedia.org/wiki/Robert_Spekkens) (2013-11-27). "Towards a formulation of quantum theory as a causally neutral theory of Bayesian inference". *Physical Review A*. **88** 052130. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1107.5849](https://arxiv.org/abs/1107.5849). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1103/PhysRevA.88.052130](https://doi.org/10.1103%2FPhysRevA.88.052130).
39. van de Wetering, John (2018). "Ordering quantum states and channels based on positive Bayesian evidence". *Journal of Mathematical Physics*. **59** 102201. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1702.01634](https://arxiv.org/abs/1702.01634). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1063/1.5023474](https://doi.org/10.1063%2F1.5023474).
40. Shimojo, Shinsuke; Ichikawa, Shin'Ichi (August 1990). "Intuitive reasoning about probability: Theoretical and experimental analyses of the "problem of three prisoners"". *Cognition*. **36** (2): 205. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/0010-0277(89)90012-7](https://doi.org/10.1016%2F0010-0277%2889%2990012-7). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [2752704](https://pubmed.ncbi.nlm.nih.gov/2752704).
41. [Rosenhouse, Jason](https://en.wikipedia.org/wiki/Jason_Rosenhouse) (2009). "3: Bayesian Monty". *The Monty Hall Problem*. Oxford University Press. pp. 57–88. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-19-536789-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-19-536789-8).
42. Haight, Frank A. (1981). *Applied Probability*. Plenum Press. pp. 60–61. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4615-6469-0](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4615-6469-0).
43. Nalebuff, Barry (1989). ["Puzzles: The Other Person's Envelope is Always Greener"](https://doi.org/10.1257%2Fjep.3.1.171). *Journal of Economic Perspectives*. **3** (1): 171–181. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1257/jep.3.1.171](https://doi.org/10.1257%2Fjep.3.1.171).
44. Kraft, Stephanie A; Duenas, Devan; Wilfond, Benjamin S; [Goddard, Katrina AB](https://en.wikipedia.org/wiki/Katrina_A._B._Goddard) (24 September 2018). ["The evolving landscape of expanded carrier screening: challenges and opportunities"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6752283). *[Genetics in Medicine](https://en.wikipedia.org/wiki/Genetics_in_Medicine)*. **21** (4): 790–797. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1038/s41436-018-0273-4](https://doi.org/10.1038%2Fs41436-018-0273-4). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [6752283](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6752283). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [30245516](https://pubmed.ncbi.nlm.nih.gov/30245516).
45. ^   Ogino, Shuji; Wilson, Robert B; Gold, Bert; Hawley, Pamela; Grody, Wayne W (October 2004). ["Bayesian analysis for cystic fibrosis risks in prenatal and carrier screening"](https://doi.org/10.1097%2F01.GIM.0000139511.83336.8F). *Genetics in Medicine*. **6** (5): 439–449. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1097/01.GIM.0000139511.83336.8F](https://doi.org/10.1097%2F01.GIM.0000139511.83336.8F). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [15371910](https://pubmed.ncbi.nlm.nih.gov/15371910).
46. ["Types of CFTR Mutations"](https://www.cff.org/What-is-CF/Genetics/Types-of-CFTR-Mutations/). *Cystic Fibrosis Foundation*.
47. ["CFTR Gene"](https://ghr.nlm.nih.gov/gene/CFTR#location). *[MedlinePlus](https://en.wikipedia.org/wiki/MedlinePlus)*. U.S. National Library of Medicine, [National Institutes of Health](https://en.wikipedia.org/wiki/National_Institutes_of_Health).

## Bibliography

- ![[media/7183efe34c8004e3513b5dddaf3197fee4504b84.png]] This article incorporates text from a publication now in the [public domain](https://en.wikipedia.org/wiki/Public_domain): Mitchell, John Malcolm (1911). "[Price, Richard](https://en.wikisource.org/wiki/1911_Encyclop%C3%A6dia_Britannica/Price,_Richard)". In [Chisholm, Hugh](https://en.wikipedia.org/wiki/Hugh_Chisholm) (ed.). *[Encyclopædia Britannica](https://en.wikipedia.org/wiki/Encyclop%C3%A6dia_Britannica_Eleventh_Edition)*. Vol. 22 (11th ed.). Cambridge University Press. pp. 314–315.

## Further reading

- Bolstad, William M.; Curran, James M. (2017). "Logic, Probability, and Uncertainty". *Introduction to Bayesian Statistics* (3rd ed.). New York: Wiley. pp. 59–82. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-118-09156-2](https://en.wikipedia.org/wiki/Special:BookSources/978-1-118-09156-2).
- [Joyce, James](https://en.wikipedia.org/wiki/James_M._Joyce) (September 30, 2003). ["Bayes' Theorem"](https://plato.stanford.edu/archives/fall2003/entries/bayes-theorem/). In [Zalta, Edward N.](https://en.wikipedia.org/wiki/Edward_N._Zalta) (ed.). *[Stanford Encyclopedia of Philosophy](https://en.wikipedia.org/wiki/Stanford_Encyclopedia_of_Philosophy)* (Fall 2003 ed.). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1095-5054](https://search.worldcat.org/issn/1095-5054). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [429049174](https://search.worldcat.org/oclc/429049174).
- Schmitt, Samuel A. (1969). "Accumulating Evidence". *Measuring Uncertainty : An Elementary Introduction to Bayesian Statistics*. Reading: Addison-Wesley. pp. 61–99. [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [5013](https://search.worldcat.org/oclc/5013).
- [Stigler, Stephen M.](https://en.wikipedia.org/wiki/Stephen_Stigler) (August 1986). ["Laplace's 1774 Memoir on Inverse Probability"](https://doi.org/10.1214%2Fss%2F1177013620). *[Statistical Science](https://en.wikipedia.org/wiki/Statistical_Science)*. **1** (3): 359–363. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/ss/1177013620](https://doi.org/10.1214%2Fss%2F1177013620).

## External links

- ["The Bayesian Trap"](https://www.youtube.com/watch?v=R13BD8qKeTg). *[Veritasium](https://en.wikipedia.org/wiki/Veritasium)*. April 5, 2017 – via [YouTube](https://en.wikipedia.org/wiki/YouTube).
