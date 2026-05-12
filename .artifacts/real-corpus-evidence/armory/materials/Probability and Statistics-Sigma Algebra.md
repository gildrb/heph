[[probability-statistics.base]]

> Source: [Σ-algebra](https://en.wikipedia.org/wiki/%CE%A3-algebra)
> License: Wikipedia content is available under CC BY-SA 4.0.

In [mathematical analysis](https://en.wikipedia.org/wiki/Mathematical_analysis) and in [probability theory](https://en.wikipedia.org/wiki/Probability_theory), a **σ-algebra** ("sigma algebra") is part of the formalism for defining [sets that can be measured](https://en.wikipedia.org/wiki/Measurable_set). In [calculus](https://en.wikipedia.org/wiki/Calculus) and [analysis](https://en.wikipedia.org/wiki/Mathematical_analysis), for example, σ-algebras are used to define the concept of sets with [area](https://en.wikipedia.org/wiki/Area) or [volume](https://en.wikipedia.org/wiki/Volume). In probability theory, they are used to define events for which a probability can be defined. In this way, σ-algebras help to formalize the notion of *size*.

In formal terms, a σ-algebra (also **σ-field**, where the σ comes from the [German](https://en.wikipedia.org/wiki/German_language) "Summe", meaning "sum") on a [set](https://en.wikipedia.org/wiki/Set_(mathematics) "Set (mathematics)") $X$ is a nonempty collection $\Sigma$ of [subsets](https://en.wikipedia.org/wiki/Subsets) of *$X$* [closed](https://en.wikipedia.org/wiki/Closure_(mathematics) "Closure (mathematics)") under [complement](https://en.wikipedia.org/wiki/Complement_(set_theory) "Complement (set theory)"), countable [unions](https://en.wikipedia.org/wiki/Union_(set_theory) "Union (set theory)"), and countable [intersections](https://en.wikipedia.org/wiki/Intersection_(set_theory) "Intersection (set theory)"). The ordered pair $(X,\Sigma )$ is called a [measurable space](https://en.wikipedia.org/wiki/Measurable_space).

The set $X$ is understood to be an [ambient space](https://en.wikipedia.org/wiki/Ambient_space) (such as the 2D plane or the set of outcomes when rolling a six-sided die {1,2,3,4,5,6}), and the collection $\Sigma$ is a choice of subsets declared to have a well-defined size. The closure requirements for σ-algebras are designed to capture our intuitive ideas about how sizes combine: if there is a well-defined probability that an event occurs, there should be a well-defined probability that it does not occur (closure under complements); if several sets have a well-defined size, so should their combination (countable unions); if several events have a well-defined probability of occurring, so should the event where they all occur simultaneously (countable intersections).

The definition of σ-algebra resembles other mathematical structures such as a [topology](https://en.wikipedia.org/wiki/Topological_space) (which is required to be closed under all unions but only finite intersections, and which doesn't necessarily contain all complements of its sets) or a [set algebra](https://en.wikipedia.org/wiki/Set_algebra) (which is closed only under *finite* unions and intersections).

## Examples of σ-algebras

If $X=\{a,b,c,d\}$ one possible σ-algebra on $X$ is $\Sigma =\{\varnothing ,\{a,b\},\{c,d\},\{a,b,c,d\}\},$ where $\varnothing$ is the [empty set](https://en.wikipedia.org/wiki/Empty_set). In general, a finite algebra is always a σ-algebra.

If $\{A_{1},A_{2},A_{3},\ldots \},$ is a countable [partition](https://en.wikipedia.org/wiki/Partition_of_a_set) of $X$ then the collection of all unions of sets in the partition (including the empty set) is a σ-algebra.

A more useful example is the set of subsets of the [real line](https://en.wikipedia.org/wiki/Real_line) formed by starting with all [open intervals](https://en.wikipedia.org/wiki/Open_interval) and adding in all countable unions, countable intersections, and relative complements and continuing this process (by [transfinite iteration](https://en.wikipedia.org/wiki/Transfinite_iteration) through all [countable ordinals](https://en.wikipedia.org/wiki/Countable_ordinal)) until the relevant closure properties are achieved (a construction known as the [Borel hierarchy](https://en.wikipedia.org/wiki/Borel_hierarchy)).

## Motivation

There are at least three key motivators for σ-algebras: defining measures, manipulating limits of sets, and managing partial information characterized by sets.

### Measure

A [measure](https://en.wikipedia.org/wiki/Measure_(mathematics) "Measure (mathematics)") on $X$ is a [function](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)") that assigns a non-negative [real number](https://en.wikipedia.org/wiki/Real_number) to subsets of $X;$ this can be thought of as making precise a notion of "size" or "volume" for sets. We want the size of the union of disjoint sets to be the sum of their individual sizes, even for an infinite sequence of [disjoint sets](https://en.wikipedia.org/wiki/Disjoint_sets).

One would like to assign a size to *every* subset of $X,$ but in many natural settings, this is not possible. For example, the [axiom of choice](https://en.wikipedia.org/wiki/Axiom_of_choice) implies that when the size under consideration is the ordinary notion of length for subsets of the real line, then there exist sets for which no size exists, for example, the [Vitali sets](https://en.wikipedia.org/wiki/Vitali_set). For this reason, one considers instead a smaller collection of privileged subsets of $X.$ These subsets will be called the measurable sets. They are closed under operations that one would expect for measurable sets, that is, the complement of a measurable set is a measurable set and the countable union of measurable sets is a measurable set. Non-empty collections of sets with these properties are called σ-algebras.

### Limits of sets

Many uses of measure, such as the probability concept of [almost sure convergence](https://en.wikipedia.org/wiki/Convergence_of_random_variables), involve [limits of sequences of sets](https://en.wikipedia.org/wiki/Set-theoretic_limit). For this, closure under countable unions and intersections is paramount. Set limits are defined as follows on σ-algebras.

- The *[limit supremum](https://en.wikipedia.org/wiki/Limit_supremum)* or *outer limit* of a sequence $A_{1},A_{2},A_{3},\ldots$ of subsets of $X$ is 

$$
\limsup _{n\to \infty }A_{n}=\bigcap _{n=1}^{\infty }\bigcup _{m=n}^{\infty }A_{m}=\bigcap _{n=1}^{\infty }A_{n}\cup A_{n+1}\cup \cdots .
$$

 It consists of all points $x$ that are in infinitely many of these sets (or equivalently, that are in [*cofinally* many](https://en.wikipedia.org/wiki/Cofinal_(mathematics) "Cofinal (mathematics)") of them). That is, $x\in \limsup _{n\to \infty }A_{n}$ if and only if there exists an infinite [subsequence](https://en.wikipedia.org/wiki/Subsequence) $A_{n_{1}},A_{n_{2}},\ldots$ (where $n_{1}<n_{2}<\cdots$) of sets that all contain $x;$ that is, such that $x\in A_{n_{1}}\cap A_{n_{2}}\cap \cdots .$
- The *[limit infimum](https://en.wikipedia.org/wiki/Limit_infimum)* or *inner limit* of a sequence $A_{1},A_{2},A_{3},\ldots$ of subsets of $X$ is 

$$
\liminf _{n\to \infty }A_{n}=\bigcup _{n=1}^{\infty }\bigcap _{m=n}^{\infty }A_{m}=\bigcup _{n=1}^{\infty }A_{n}\cap A_{n+1}\cap \cdots .
$$

 It consists of all points that are in all but finitely many of these sets (or equivalently, that are *eventually* in all of them). That is, $x\in \liminf _{n\to \infty }A_{n}$ if and only if there exists an index $N\in \mathbb {N}$ such that $A_{N},A_{N+1},\ldots$ all contain $x;$ that is, such that $x\in A_{N}\cap A_{N+1}\cap \cdots .$

The inner limit is always a subset of the outer limit: 

$$
\liminf _{n\to \infty }A_{n}~\subseteq ~\limsup _{n\to \infty }A_{n}.
$$

 If these two sets are equal then their limit $\lim _{n\to \infty }A_{n}$ exists and is equal to this common set: 

$$
\lim _{n\to \infty }A_{n}:=\liminf _{n\to \infty }A_{n}=\limsup _{n\to \infty }A_{n}.
$$

### Sub σ-algebras

In much of probability, especially when [conditional expectation](https://en.wikipedia.org/wiki/Conditional_expectation) is involved, one is concerned with sets that represent only part of all the possible information that can be observed. This partial information can be characterized with a smaller σ-algebra which is a subset of the principal σ-algebra; it consists of the collection of subsets relevant only to and determined only by the partial information. Formally, if $\Sigma ,\Sigma '$ are σ-algebras on $X$, then $\Sigma '$ is a sub σ-algebra of $\Sigma$ if $\Sigma '\subseteq \Sigma$.

The [Bernoulli process](https://en.wikipedia.org/wiki/Bernoulli_process) provides a simple example. This consists of a sequence of random coin flips, coming up Heads ($H$) or Tails ($T$), of unbounded length. The [sample space](https://en.wikipedia.org/wiki/Sample_space) Ω consists of all possible infinite sequences of $H$ or $T:$ 

$$
\Omega =\{H,T\}^{\infty }=\{(x_{1},x_{2},x_{3},\dots ):x_{i}\in \{H,T\},i\geq 1\}.
$$

The full sigma algebra can be generated from an ascending sequence of subalgebras, by considering the information that might be obtained after observing some or all of the first $n$ coin flips. This sequence of subalgebras is given by 

$$
{\mathcal {G}}_{n}=\{A\times \Omega :A\subseteq \{H,T\}^{n}\}
$$

 Each of these is finer than the last, and so can be ordered as a [filtration](https://en.wikipedia.org/wiki/Filtration_(probability_theory) "Filtration (probability theory)")

$$
{\mathcal {G}}_{0}\subseteq {\mathcal {G}}_{1}\subseteq {\mathcal {G}}_{2}\subseteq \cdots \subseteq {\mathcal {G}}_{\infty }
$$

The first subalgebra ${\mathcal {G}}_{0}=\{\varnothing ,\Omega \}$ is the trivial algebra: it has only two elements in it, the empty set and the total space. The second subalgebra ${\mathcal {G}}_{1}$ has four elements: the two in ${\mathcal {G}}_{0}$ plus two more: sequences that start with $H$ and sequences that start with $T$. Each subalgebra is finer than the last. The $n$'th subalgebra contains $2^{n+1}$ elements: it divides the total space $\Omega$ into all of the possible sequences that might have been observed after $n$ flips, including the possible non-observation of some of the flips.

The limiting algebra ${\mathcal {G}}_{\infty }$ is the smallest σ-algebra containing all the others. It is the algebra generated by the [product topology](https://en.wikipedia.org/wiki/Product_topology) or [weak topology](https://en.wikipedia.org/wiki/Weak_topology) on the product space $\{H,T\}^{\infty }.$

## Definition and properties

### Definition

Let $X$ be some set, and let $P(X)$ represent its [power set](https://en.wikipedia.org/wiki/Power_set), the set of all subsets of $X$. Then a subset $\Sigma \subseteq P(X)$ is called a **σ-algebra** if it satisfies the following three properties:

1.  $X$ is in $\Sigma$.
2.  $\Sigma$ is *closed under complementation*: If some set $A$ is in $\Sigma ,$ then so is its [complement](https://en.wikipedia.org/wiki/Complement_(set_theory) "Complement (set theory)"), $X\setminus A.$
3.  $\Sigma$ is *closed under countable unions*: If $A_{1},A_{2},A_{3},\ldots$ are in $\Sigma ,$ then so is $A=A_{1}\cup A_{2}\cup A_{3}\cup \cdots .$

From these properties, it follows that the σ-algebra is also closed under countable [intersections](https://en.wikipedia.org/wiki/Intersection_(set_theory) "Intersection (set theory)") (by applying [De Morgan's laws](https://en.wikipedia.org/wiki/De_Morgan%27s_laws)).

It also follows that the [empty set](https://en.wikipedia.org/wiki/Empty_set) $\varnothing$ is in $\Sigma ,$ since by **(1)** $X$ is in $\Sigma$ and **(2)** asserts that its complement, the empty set, is also in $\Sigma .$ Moreover, since $\{X,\varnothing \}$ satisfies all 3 conditions, it follows that $\{X,\varnothing \}$ is the smallest possible σ-algebra on $X.$ The largest possible σ-algebra on $X$ is $P(X).$

Elements of the σ-algebra are called [measurable sets](https://en.wikipedia.org/wiki/Measurable_set). An ordered pair $(X,\Sigma ),$ where $X$ is a set and $\Sigma$ is a σ-algebra over $X,$ is called a **measurable space**. A function between two measurable spaces is called a [measurable function](https://en.wikipedia.org/wiki/Measurable_function) if the [preimage](https://en.wikipedia.org/wiki/Preimage) of every measurable set is measurable. The collection of measurable spaces forms a [category](https://en.wikipedia.org/wiki/Category_(mathematics) "Category (mathematics)"), with the [measurable functions](https://en.wikipedia.org/wiki/Measurable_function) as [morphisms](https://en.wikipedia.org/wiki/Morphism). [Measures](https://en.wikipedia.org/wiki/Measure_(mathematics) "Measure (mathematics)") are defined as certain types of functions from a σ-algebra to $[0,\infty ].$

A σ-algebra is both a [π-system](https://en.wikipedia.org/wiki/Pi-system) and a [Dynkin system](https://en.wikipedia.org/wiki/Dynkin_system) (λ-system). The converse is true as well, by Dynkin's theorem (see below).

### Dynkin's π-λ theorem

This theorem (or the related [monotone class theorem](https://en.wikipedia.org/wiki/Monotone_class_theorem)) is an essential tool for proving many results about properties of specific σ-algebras. It capitalizes on the nature of two simpler classes of sets, namely the following.

- A [π-system](https://en.wikipedia.org/wiki/Pi-system) $P$ is a collection of subsets of $X$ that is closed under finitely many intersections, and
- A [Dynkin system](https://en.wikipedia.org/wiki/Dynkin_system) (or λ-system) $D$ is a collection of subsets of $X$ that contains $X$ and is closed under complement and under countable unions of *disjoint* subsets.

Dynkin's π-λ theorem says, if $P$ is a π-system and $D$ is a Dynkin system that contains $P,$ then the σ-algebra $\sigma (P)$ [[Sigma Algebra|generated]] by $P$ is contained in $D.$ Since certain π-systems are relatively simple classes, it may not be hard to verify that all sets in $P$ enjoy the property under consideration while, on the other hand, showing that the collection $D$ of all subsets with the property is a Dynkin system can also be straightforward. Dynkin's π-λ Theorem then implies that all sets in $\sigma (P)$ enjoy the property, avoiding the task of checking it for an arbitrary set in $\sigma (P).$

One of the most fundamental uses of the π-λ theorem is to show equivalence of separately defined measures or integrals. For example, it is used to equate a probability for a random variable $X$ with the [Lebesgue-Stieltjes integral](https://en.wikipedia.org/wiki/Lebesgue-Stieltjes_integral) typically associated with computing the probability: 

$$
\mathbb {P} (X\in A)=\int _{A}\,F(dx)
$$

 for all $A$ in the Borel σ-algebra on $\mathbb {R} ,$ where $F(x)$ is the [[Cumulative Distribution Function]] for $X,$ defined on $\mathbb {R} ,$ while $\mathbb {P}$ is a [probability measure](https://en.wikipedia.org/wiki/Probability_measure), defined on a σ-algebra $\Sigma$ of subsets of some [sample space](https://en.wikipedia.org/wiki/Sample_space) $\Omega .$

### Combining σ-algebras

Suppose $\textstyle \left\{\Sigma _{\alpha }:\alpha \in {\mathcal {A}}\right\}$ is a collection of σ-algebras on a space $X.$

**Meet**

The intersection of a collection of σ-algebras is a σ-algebra. To emphasize its character as a σ-algebra, it often is denoted by: 

$$
\bigwedge _{\alpha \in {\mathcal {A}}}\Sigma _{\alpha }.
$$

**Sketch of Proof:** Let $\Sigma ^{*}$ denote the intersection. Since $X$ is in every $\Sigma _{\alpha },\Sigma ^{*}$ is not empty. Closure under complement and countable unions for every $\Sigma _{\alpha }$ implies the same must be true for $\Sigma ^{*}.$ Therefore, $\Sigma ^{*}$ is a σ-algebra.

**Join**

The union of a collection of σ-algebras is not generally a σ-algebra, or even an algebra, but it [[Sigma Algebra|generates]] a σ-algebra known as the join which typically is denoted 

$$
\bigvee _{\alpha \in {\mathcal {A}}}\Sigma _{\alpha }=\sigma \left(\bigcup _{\alpha \in {\mathcal {A}}}\Sigma _{\alpha }\right).
$$

 A π-system that generates the join is 

$$
{\mathcal {P}}=\left\{\bigcap _{i=1}^{n}A_{i}:A_{i}\in \Sigma _{\alpha _{i}},\alpha _{i}\in {\mathcal {A}},\ n\geq 1\right\}.
$$

 **Sketch of Proof:** By the case $n=1,$ it is seen that each $\Sigma _{\alpha }\subset {\mathcal {P}},$ so 

$$
\bigcup _{\alpha \in {\mathcal {A}}}\Sigma _{\alpha }\subseteq {\mathcal {P}}.
$$

 This implies 

$$
\sigma \left(\bigcup _{\alpha \in {\mathcal {A}}}\Sigma _{\alpha }\right)\subseteq \sigma ({\mathcal {P}})
$$

 by the definition of a σ-algebra [[Sigma Algebra|generated]] by a collection of subsets. On the other hand, 

$$
{\mathcal {P}}\subseteq \sigma \left(\bigcup _{\alpha \in {\mathcal {A}}}\Sigma _{\alpha }\right)
$$

 which, by Dynkin's π-λ theorem, implies 

$$
\sigma ({\mathcal {P}})\subseteq \sigma \left(\bigcup _{\alpha \in {\mathcal {A}}}\Sigma _{\alpha }\right).
$$

### σ-algebras for subspaces

Suppose $Y$ is a subset of $X$ and let $(X,\Sigma )$ be a measurable space.

- The collection $\{Y\cap B:B\in \Sigma \}$ is a σ-algebra of subsets of $Y.$
- Suppose $(Y,\Lambda )$ is a measurable space. The collection $\{A\subseteq X:A\cap Y\in \Lambda \}$ is a σ-algebra of subsets of $X.$

### Relation to σ-ring

A *σ*-algebra $\Sigma$ is just a [*σ*-ring](https://en.wikipedia.org/wiki/Sigma-ring) that contains the universal set $X.$ A *σ*-ring need not be a *σ*-algebra, as for example measurable subsets of zero Lebesgue measure in the real line are a *σ*-ring, but not a *σ*-algebra since the real line has infinite measure and thus cannot be obtained by their countable union. If, instead of zero measure, one takes measurable subsets of finite Lebesgue measure, those are a [ring](https://en.wikipedia.org/wiki/Ring_of_sets) but not a *σ*-ring, since the real line can be obtained by their countable union yet its measure is not finite.

### Typographic note

*σ*-algebras are sometimes denoted using [calligraphic](https://en.wikipedia.org/wiki/Calligraphic) capital letters, or the [Fraktur typeface](https://en.wikipedia.org/wiki/Fraktur_(typeface)). Thus $(X,\Sigma )$ may be denoted as $(X,\,{\mathcal {F}})$ or $(X,\,{\mathfrak {F}}).$

## Particular cases and examples

### Separable σ-algebras

A **separable $\sigma$-algebra** (or **separable $\sigma$-field**) is a $\sigma$-algebra ${\mathcal {F}}$ that is a [separable space](https://en.wikipedia.org/wiki/Separable_space) when considered as a [metric space](https://en.wikipedia.org/wiki/Metric_space) with [metric](https://en.wikipedia.org/wiki/Metric_(mathematics)) $\rho (A,B)=\mu (A\mathbin {\triangle } B)$ for $A,B\in {\mathcal {F}}$ and a given finite [measure](https://en.wikipedia.org/wiki/Measure_(mathematics) "Measure (mathematics)") $\mu$ (and with $\triangle$ being the [symmetric difference](https://en.wikipedia.org/wiki/Symmetric_difference) operator). Any $\sigma$-algebra generated by a [countable](https://en.wikipedia.org/wiki/Countable) collection of [sets](https://en.wikipedia.org/wiki/Set_(mathematics) "Set (mathematics)") is separable, but the converse need not hold. For example, the Lebesgue $\sigma$-algebra is separable (since every Lebesgue measurable set is equivalent to some Borel set) but not countably generated (since its cardinality is higher than continuum).

A separable measure space has a natural [pseudometric](https://en.wikipedia.org/wiki/Pseudometric_space) that renders it [separable](https://en.wikipedia.org/wiki/Separable_space) as a [pseudometric space](https://en.wikipedia.org/wiki/Pseudometric_space). The distance between two sets is defined as the measure of the [symmetric difference](https://en.wikipedia.org/wiki/Symmetric_difference) of the two sets. The symmetric difference of two distinct sets can have measure zero; hence the pseudometric as defined above need not be a true metric. However, if sets whose symmetric difference has measure zero are identified into a single [equivalence class](https://en.wikipedia.org/wiki/Equivalence_class), the resulting [quotient set](https://en.wikipedia.org/wiki/Equivalence_class) can be properly metrized by the induced metric. If the measure space is separable, it can be shown that the corresponding metric space is, too.

### Simple set-based examples

Let $X$ be any set.

- The family consisting only of the empty set and the set $X,$ called the minimal or **trivial σ-algebra** over $X.$
- The [power set](https://en.wikipedia.org/wiki/Power_set) of $X,$ called the **discrete σ-algebra**.
- The collection $\{\varnothing ,A,X\setminus A,X\}$ is a simple σ-algebra generated by the subset $A.$
- The collection of subsets of $X$ which are countable or whose complements are countable is a σ-algebra (which is distinct from the power set of $X$ if and only if $X$ is uncountable). This is the σ-algebra generated by the [singletons](https://en.wikipedia.org/wiki/Singleton_(mathematics) "Singleton (mathematics)") of $X.$ Note: "countable" includes finite or empty.
- The collection of all unions of sets in a countable [partition](https://en.wikipedia.org/wiki/Partition_of_a_set) of $X$ is a σ-algebra.

### Stopping time sigma-algebras

A [stopping time](https://en.wikipedia.org/wiki/Stopping_time) $\tau$ can define a $\sigma$-algebra ${\mathcal {F}}_{\tau },$ the so-called [stopping time sigma-algebra](https://en.wikipedia.org/wiki/Filtration_(mathematics)#Relation_to_stopping_times:_stopping_time_sigma-algebras "Filtration (mathematics)"), which in a [filtered probability space](https://en.wikipedia.org/wiki/Filtration_(mathematics)#Measure_theory "Filtration (mathematics)") describes the information up to the random time $\tau$ in the sense that, if the filtered probability space is interpreted as a random experiment, the maximum information that can be found out about the experiment from arbitrarily often repeating it until the time $\tau$ is ${\mathcal {F}}_{\tau }.$

## σ-algebras generated by families of sets

### σ-algebra generated by an arbitrary family

Let $F$ be an arbitrary family of subsets of $X.$ Then there exists a unique smallest σ-algebra which contains every set in $F$ (even though $F$ may or may not itself be a σ-algebra). It is, in fact, the intersection of all σ-algebras containing $F.$ (See intersections of σ-algebras above.) This σ-algebra is denoted $\sigma (F)$ and is called **the σ-algebra generated by $F.$**

If $F$ is empty, then $\sigma (\varnothing )=\{\varnothing ,X\}.$ Otherwise $\sigma (F)$ consists of all the subsets of $X$ that can be made from elements of $F$ by a countable number of complement, union and intersection operations.

For a simple example, consider the set $X=\{1,2,3\}.$ Then the σ-algebra generated by the single subset $\{1\}$ is $\sigma (\{1\})=\{\varnothing ,\{1\},\{2,3\},\{1,2,3\}\}.$ By an [abuse of notation](https://en.wikipedia.org/wiki/Abuse_of_notation), when a collection of subsets contains only one element, $A,$ $\sigma (A)$ may be written instead of $\sigma (\{A\});$ in the prior example $\sigma (\{1\})$ instead of $\sigma (\{\{1\}\}).$ Indeed, using $\sigma \left(A_{1},A_{2},\ldots \right)$ to mean $\sigma \left(\left\{A_{1},A_{2},\ldots \right\}\right)$ is also quite common.

There are many families of subsets that generate useful σ-algebras. Some of these are presented here.

### σ-algebra generated by a function

If $f$ is a function from a set $X$ to a set $Y$ and $B$ is a $\sigma$-algebra of subsets of $Y,$ then the $\sigma$**-algebra generated by the function** $f,$ denoted by $\sigma (f),$ is the collection of all inverse images $f^{-1}(S)$ of the sets $S$ in $B.$ That is, 

$$
\sigma (f)=\left\{f^{-1}(S)\,:\,S\in B\right\}.
$$

A function $f$ from a set $X$ to a set $Y$ is [measurable](https://en.wikipedia.org/wiki/Measurable_function) with respect to a σ-algebra $\Sigma$ of subsets of $X$ if and only if $\sigma (f)$ is a subset of $\Sigma .$

One common situation, and understood by default if $B$ is not specified explicitly, is when $Y$ is a [metric](https://en.wikipedia.org/wiki/Metric_space) or [topological space](https://en.wikipedia.org/wiki/Topological_space) and $B$ is the collection of [Borel sets](https://en.wikipedia.org/wiki/Borel_set) on $Y.$

If $f$ is a function from $X$ to $\mathbb {R} ^{n}$ then $\sigma (f)$ is generated by the family of subsets which are inverse images of intervals/rectangles in $\mathbb {R} ^{n}:$ 

$$
\sigma (f)=\sigma \left(\left\{f^{-1}(\left[a_{1},b_{1}\right]\times \cdots \times \left[a_{n},b_{n}\right]):a_{i},b_{i}\in \mathbb {R} \right\}\right).
$$

A useful property is the following. Assume $f$ is a measurable map from $\left(X,\Sigma _{X}\right)$ to $\left(S,\Sigma _{S}\right)$ and $g$ is a measurable map from $\left(X,\Sigma _{X}\right)$ to $\left(T,\Sigma _{T}\right).$ If there exists a measurable map $h$ from $\left(T,\Sigma _{T}\right)$ to $\left(S,\Sigma _{S}\right)$ such that $f(x)=h(g(x))$ for all $x,$ then $\sigma (f)\subseteq \sigma (g).$ If $S$ is finite or countably infinite or, more generally, $\left(S,\Sigma _{S}\right)$ is a [standard Borel space](https://en.wikipedia.org/wiki/Standard_Borel_space) (for example, a separable complete metric space with its associated Borel sets), then the converse is also true. Examples of standard Borel spaces include $\mathbb {R} ^{n}$ with its Borel sets and $\mathbb {R} ^{\infty }$ with the cylinder σ-algebra described below.

### Borel and Lebesgue σ-algebras

An important example is the [Borel algebra](https://en.wikipedia.org/wiki/Borel_algebra) over any [topological space](https://en.wikipedia.org/wiki/Topological_space): the σ-algebra generated by the [open sets](https://en.wikipedia.org/wiki/Open_set) (or, equivalently, by the [closed sets](https://en.wikipedia.org/wiki/Closed_set)). This σ-algebra is not, in general, the whole power set. For a non-trivial example that is not a Borel set, see the [Vitali set](https://en.wikipedia.org/wiki/Vitali_set) or [Non-Borel sets](https://en.wikipedia.org/wiki/Borel_set#Non-Borel_sets).

On the [Euclidean space](https://en.wikipedia.org/wiki/Euclidean_space) $\mathbb {R} ^{n},$ another σ-algebra is of importance: that of all [Lebesgue measurable](https://en.wikipedia.org/wiki/Lebesgue_measure) sets. This σ-algebra contains more sets than the Borel σ-algebra on $\mathbb {R} ^{n}$ and is preferred in [integration](https://en.wikipedia.org/wiki/Integral) theory, as it gives a [complete measure space](https://en.wikipedia.org/wiki/Complete_measure).

### Product σ-algebra

Let $\left(X_{1},\Sigma _{1}\right)$ and $\left(X_{2},\Sigma _{2}\right)$ be two measurable spaces. The σ-algebra for the corresponding [product space](https://en.wikipedia.org/wiki/Product_space) $X_{1}\times X_{2}$ is called the **product σ-algebra** and is defined by 

$$
\Sigma _{1}\times \Sigma _{2}=\sigma \left(\left\{B_{1}\times B_{2}:B_{1}\in \Sigma _{1},B_{2}\in \Sigma _{2}\right\}\right).
$$

Observe that $\{B_{1}\times B_{2}:B_{1}\in \Sigma _{1},B_{2}\in \Sigma _{2}\}$ is a π-system.

The Borel σ-algebra for $\mathbb {R} ^{n}$ is generated by half-infinite rectangles and by finite rectangles. For example, 

$$
{\mathcal {B}}(\mathbb {R} ^{n})=\sigma \left(\left\{(-\infty ,b_{1}]\times \cdots \times (-\infty ,b_{n}]:b_{i}\in \mathbb {R} \right\}\right)=\sigma \left(\left\{\left(a_{1},b_{1}\right]\times \cdots \times \left(a_{n},b_{n}\right]:a_{i},b_{i}\in \mathbb {R} \right\}\right).
$$

For each of these two examples, the generating family is a π-system.

### σ-algebra generated by cylinder sets

Suppose 

$$
X\subseteq \mathbb {R} ^{\mathbb {T} }=\{f:f(t)\in \mathbb {R} ,\ t\in \mathbb {T} \}
$$

is a set of real-valued functions. Let ${\mathcal {B}}(\mathbb {R} )$ denote the Borel subsets of $\mathbb {R} .$ A [cylinder subset](https://en.wikipedia.org/wiki/Cylinder_set) of $X$ is a finitely restricted set defined as 

$$
C_{t_{1},\dots ,t_{n}}(B_{1},\dots ,B_{n})=\left\{f\in X:f(t_{i})\in B_{i},1\leq i\leq n\right\}.
$$

Each 

$$
\left\{C_{t_{1},\dots ,t_{n}}\left(B_{1},\dots ,B_{n}\right):B_{i}\in {\mathcal {B}}(\mathbb {R} ),1\leq i\leq n\right\}
$$

 is a π-system that generates a σ-algebra $\textstyle \Sigma _{t_{1},\dots ,t_{n}}.$ Then the family of subsets 

$$
{\mathcal {F}}_{X}=\bigcup _{n=1}^{\infty }\bigcup _{t_{i}\in \mathbb {T} ,i\leq n}\Sigma _{t_{1},\dots ,t_{n}}
$$

 is an algebra that generates the **[cylinder σ-algebra](https://en.wikipedia.org/wiki/Cylinder_%CF%83-algebra)** for $X.$ This σ-algebra is a subalgebra of the Borel σ-algebra determined by the [product topology](https://en.wikipedia.org/wiki/Product_topology) of $\mathbb {R} ^{\mathbb {T} }$ restricted to $X.$

An important special case is when $\mathbb {T}$ is the set of natural numbers and $X$ is a set of real-valued sequences. In this case, it suffices to consider the cylinder sets 

$$
C_{n}\left(B_{1},\dots ,B_{n}\right)=\left(B_{1}\times \cdots \times B_{n}\times \mathbb {R} ^{\infty }\right)\cap X=\left\{\left(x_{1},x_{2},\ldots ,x_{n},x_{n+1},\ldots \right)\in X:x_{i}\in B_{i},1\leq i\leq n\right\},
$$

 for which 

$$
\Sigma _{n}=\sigma \left(\{C_{n}\left(B_{1},\dots ,B_{n}\right):B_{i}\in {\mathcal {B}}(\mathbb {R} ),1\leq i\leq n\}\right)
$$

 is a non-decreasing sequence of σ-algebras.

### Ball σ-algebra

The ball σ-algebra is the smallest σ-algebra containing all the open (and/or closed) balls. This is never larger than the [Borel σ-algebra](https://en.wikipedia.org/wiki/Borel_set). Note that the two σ-algebra are equal for separable spaces. For some nonseparable spaces, some maps are ball measurable even though they are not Borel measurable, making use of the ball σ-algebra useful in the analysis of such maps.

### σ-algebra generated by random variable or vector

Suppose $(\Omega ,\Sigma ,\mathbb {P} )$ is a [probability space](https://en.wikipedia.org/wiki/Probability_space). If $\textstyle Y:\Omega \to \mathbb {R} ^{n}$ is measurable with respect to the Borel σ-algebra on $\mathbb {R} ^{n}$ then $Y$ is called a **[random variable](https://en.wikipedia.org/wiki/Random_variable)** ($n=1$) or **random vector** ($n>1$). The σ-algebra generated by $Y$ is 

$$
\sigma (Y)=\left\{Y^{-1}(A):A\in {\mathcal {B}}\left(\mathbb {R} ^{n}\right)\right\}.
$$

### σ-algebra generated by a stochastic process

Suppose $(\Omega ,\Sigma ,\mathbb {P} )$ is a [probability space](https://en.wikipedia.org/wiki/Probability_space) and $\mathbb {R} ^{\mathbb {T} }$ is the set of real-valued functions on $\mathbb {T} .$ If $\textstyle Y:\Omega \to X\subseteq \mathbb {R} ^{\mathbb {T} }$ is measurable with respect to the cylinder σ-algebra $\sigma \left({\mathcal {F}}_{X}\right)$ (see above) for $X$ then $Y$ is called a **[stochastic process](https://en.wikipedia.org/wiki/Stochastic_process)** or **random process**. The σ-algebra generated by $Y$ is 

$$
\sigma (Y)=\left\{Y^{-1}(A):A\in \sigma \left({\mathcal {F}}_{X}\right)\right\}=\sigma \left(\left\{Y^{-1}(A):A\in {\mathcal {F}}_{X}\right\}\right),
$$

 the σ-algebra generated by the inverse images of cylinder sets.

## See also

- [Measurable function](https://en.wikipedia.org/wiki/Measurable_function) – Kind of mathematical function
- [Sample space](https://en.wikipedia.org/wiki/Sample_space) – Set of all possible outcomes or results of a statistical trial or experiment
- [Sigma-additive set function](https://en.wikipedia.org/wiki/Sigma-additive_set_function) – Mapping function
- [Sigma-ring](https://en.wikipedia.org/wiki/Sigma-ring) – Family of sets closed under countable unions

<table class="wikitable collapsible floatright collapsed" style="float:right; margin-top:0; padding-top:0; text-align:center;">

[Families ${\mathcal {F}}$ of sets](https://en.wikipedia.org/wiki/Family_of_sets) over $\Omega$

<ul>
<li>[v](https://en.wikipedia.org/wiki/Template:Families_of_sets)</li>
<li>[t](https://en.wikipedia.org/wiki/Template_talk:Families_of_sets)</li>
<li>[e](https://en.wikipedia.org/wiki/Special:EditPage/Template:Families_of_sets)</li>
</ul>

&#10;
Is necessarily true of ${\mathcal {F}}\colon$<br />
or, is ${\mathcal {F}}$ [closed under:](https://en.wikipedia.org/wiki/Closure_(mathematics))
[Directed
by $\,\supseteq$](https://en.wikipedia.org/wiki/Directed_set)
$A\cap B$
$A\cup B$
$B\setminus A$
$\Omega \setminus A$
$A_{1}\cap A_{2}\cap \cdots$
$A_{1}\cup A_{2}\cup \cdots$
$\Omega \in {\mathcal {F}}$
$\varnothing \in {\mathcal {F}}$
[F.I.P.](https://en.wikipedia.org/wiki/Finite_intersection_property)

[π-system](https://en.wikipedia.org/wiki/Pi-system)
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]

[Semiring](https://en.wikipedia.org/wiki/Ring_of_sets#semiring)
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
Never

[Semialgebra (Semifield)](https://en.wikipedia.org/wiki/Ring_of_sets#semialgebra)
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
Never

[Monotone class](https://en.wikipedia.org/wiki/Monotone_class)
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
only if $A_{i}\searrow$
only if $A_{i}\nearrow$
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]

[𝜆-system (Dynkin System)](https://en.wikipedia.org/wiki/Dynkin_system)
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
only if<br />
$A\subseteq B$
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
only if $A_{i}\nearrow$ or<br />
they are [disjoint](https://en.wikipedia.org/wiki/Disjoint_sets)
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
Never

[Ring (Order theory)](https://en.wikipedia.org/wiki/Ring_of_sets)
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]

[Ring (Measure theory)](https://en.wikipedia.org/wiki/Ring_of_sets)
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
Never

[δ-Ring](https://en.wikipedia.org/wiki/Delta-ring)
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
Never

[𝜎-Ring](https://en.wikipedia.org/wiki/Sigma-ring)
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
Never

[Algebra (Field)](https://en.wikipedia.org/wiki/Field_of_sets)
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
Never

𝜎-Algebra (𝜎-Field)
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
Never

[Filter](https://en.wikipedia.org/wiki/Filter_on_a_set)
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]

[Proper filter](https://en.wikipedia.org/wiki/Proper_filter_on_a_set)
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
Never
Never
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
Never
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]

[Prefilter (Filter base)](https://en.wikipedia.org/wiki/Prefilter)
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]

[Filter subbase](https://en.wikipedia.org/wiki/Filter_subbase)
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]

[Open Topology](https://en.wikipedia.org/wiki/Topology_(structure))
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/0112ab587eec208d3b0c081339cd6e9bbcec3593.png]]<br />
(even arbitrary $\cup$)
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
Never

[Closed Topology](https://en.wikipedia.org/wiki/Topology_(structure))
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/0112ab587eec208d3b0c081339cd6e9bbcec3593.png]]<br />
(even arbitrary $\cap$)
![[media/9fd2808e502d2b40ac39fc058487158ac8bbbdd7.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
![[media/b937e4e1990f8681f5f99ea4b0ef92a41dd310fa.png]]
Never

Is necessarily true of ${\mathcal {F}}\colon$<br />
or, is ${\mathcal {F}}$ [closed under:](https://en.wikipedia.org/wiki/Closure_(mathematics))
[directed
downward](https://en.wikipedia.org/wiki/Directed_downward)
finite<br />
intersections
finite<br />
unions
relative<br />
complements
complements<br />
in $\Omega$
countable<br />
intersections
countable<br />
unions
contains $\Omega$
contains $\varnothing$
[Finite
Intersection
Property](https://en.wikipedia.org/wiki/Finite_intersection_property)

<p>Additionally, a <strong><em>[semiring](https://en.wikipedia.org/wiki/Ring_of_sets#semiring)</em></strong> is a [π-system](https://en.wikipedia.org/wiki/Pi-system) where every complement $B\setminus A$ is equal to a finite [disjoint union](https://en.wikipedia.org/wiki/Disjoint_union) of sets in ${\mathcal {F}}.$<br />
A <strong><em>[semialgebra](https://en.wikipedia.org/wiki/Ring_of_sets#semialgebra)</em></strong> is a semiring where every complement $\Omega \setminus A$ is equal to a finite [disjoint union](https://en.wikipedia.org/wiki/Disjoint_union) of sets in ${\mathcal {F}}.$<br />
$A,B,A_{1},A_{2},\ldots$ are arbitrary elements of ${\mathcal {F}}$ and it is assumed that ${\mathcal {F}}\neq \varnothing .$<br />
</p>

</table>

## References

1.  Elstrodt, J. (2018). Maß- Und Integrationstheorie. Springer Spektrum Berlin, Heidelberg. [https://doi.org/10.1007/978-3-662-57939-8](https://doi.org/10.1007/978-3-662-57939-8)
2.  [Rudin, Walter](https://en.wikipedia.org/wiki/Walter_Rudin) (1987). *Real & Complex Analysis*. [McGraw-Hill](https://en.wikipedia.org/wiki/McGraw-Hill). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-07-054234-1](https://en.wikipedia.org/wiki/Special:BookSources/0-07-054234-1).
3.  Vestrup, Eric M. (2009). *The Theory of Measures and Integration*. John Wiley & Sons. p. 12. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-470-31795-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-470-31795-2).
4.  Džamonja, Mirna; [Kunen, Kenneth](https://en.wikipedia.org/wiki/Kenneth_Kunen) (1995). ["Properties of the class of measure separable compact spaces"](https://archive.uea.ac.uk/~h020/fundamenta.pdf) (PDF). *[Fundamenta Mathematicae](https://en.wikipedia.org/wiki/Fundamenta_Mathematicae)*: 262. “If $\mu$ is a Borel measure on $X,$ the measure algebra of $(X,\mu )$ is the Boolean algebra of all Borel sets modulo $\mu$-null sets. If $\mu$ is finite, then such a measure algebra is also a metric space, with the distance between the two sets being the measure of their symmetric difference. Then, we say that $\mu$ is *separable* [if and only if](https://en.wikipedia.org/wiki/If_and_only_if) this metric space is separable as a topological space.”
5.  **_5-0)** Fischer, Tom (2013). ["On simple representations of stopping times and stopping time sigma-algebras"](https://dx.doi.org/10.1016/j.spl.2012.09.024). *Statistics and Probability Letters*. **83** (1): 345–349. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1112.1603](https://arxiv.org/abs/1112.1603). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.spl.2012.09.024](https://doi.org/10.1016%2Fj.spl.2012.09.024).
6.  [Kallenberg, Olav](https://en.wikipedia.org/wiki/Olav_Kallenberg) (2001). *Foundations of Modern Probability* (2nd ed.). [Springer](https://en.wikipedia.org/wiki/Springer_Publishing). p. 7. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-95313-2](https://en.wikipedia.org/wiki/Special:BookSources/0-387-95313-2).
7.  van der Vaart, A. W., & Wellner, J. A. (1996). Weak Convergence and Empirical Processes. In Springer Series in Statistics. Springer New York. [https://doi.org/10.1007/978-1-4757-2545-2](https://doi.org/10.1007/978-1-4757-2545-2)

## External links

- ["Algebra of sets"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society), 2001 \[1994\]
- [Sigma Algebra](https://planetmath.org/alphabetical.html) from PlanetMath.
