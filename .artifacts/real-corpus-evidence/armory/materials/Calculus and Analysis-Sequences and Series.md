[[calculus-analysis.base]]

> Source: [Sequence](https://en.wikipedia.org/wiki/Sequence)
> License: Wikipedia content is available under CC BY-SA 4.0.

![[media/c636200db87580d66a47f13c0bb165df9c3e82af.png]]
A part of an infinite sequence of [real numbers](https://en.wikipedia.org/wiki/Real_number) (in blue), indexed by a natural number $n$. This sequence is neither increasing, decreasing, convergent, nor [Cauchy](https://en.wikipedia.org/wiki/Cauchy_sequence). It is, however, bounded (by red dashed lines).

In mathematics, a **sequence** is a collection of [objects](https://en.wikipedia.org/wiki/Mathematical_object) possibly with repetition, that come in a specified order. Like a [set](https://en.wikipedia.org/wiki/Set_(mathematics) "Set (mathematics)"), it contains [members](https://en.wikipedia.org/wiki/Element_(mathematics)) (also called *elements*, or *terms*). Unlike a set, the same elements can appear multiple times at different positions in a sequence, and unlike a set, the order does matter. The notion of a sequence can be generalized to an [indexed family](https://en.wikipedia.org/wiki/Indexed_family), defined as a function from an *arbitrary* index set.

For example, (M, A, R, Y) is a sequence of letters with the letter "M" first and "Y" last. This sequence differs from (A, R, M, Y). Also, the sequence (1, 1, 2, 3, 5, 8), which contains the number 1 at two different positions, is a valid sequence. Sequences can be *[finite](https://en.wikipedia.org/wiki/Finiteness)*, as in these examples, or *infinite*, such as the sequence of [even](https://en.wikipedia.org/wiki/Even_and_odd_numbers) [positive integers](https://en.wikipedia.org/wiki/Positive_integer) (2, 4, 6, ...).

The *length* of a finite sequence is defined as the number of elements in the sequence. The position of an element in a sequence is its *rank* or *index*; it is the natural number for which the element is the [image](https://en.wikipedia.org/wiki/Image_(mathematics) "Image (mathematics)"). The first element has index 0 or 1, depending on the context or a specific convention. In [mathematical analysis](https://en.wikipedia.org/wiki/Mathematical_analysis), a sequence is often denoted by letters in the form of $a_{n}$, $b_{n}$ and $c_{n}$, where the subscript *n* refers to the *n*th element of the sequence; for example, the *n*th element of the [Fibonacci sequence](https://en.wikipedia.org/wiki/Fibonacci_sequence) *$F$* is generally denoted as *$F_{n}$*.

In [computing](https://en.wikipedia.org/wiki/Computing) and [computer science](https://en.wikipedia.org/wiki/Computer_science), finite sequences are usually called *[strings](https://en.wikipedia.org/wiki/String_(computer_science) "String (computer science)")*, *[words](https://en.wikipedia.org/wiki/Word_(formal_language_theory))* or *[lists](https://en.wikipedia.org/wiki/List_(computer_science)),* with the specific technical term chosen depending on the type of object the sequence enumerates and the different ways to represent the sequence in [computer memory](https://en.wikipedia.org/wiki/Computer_memory). Infinite sequences are called *[streams](https://en.wikipedia.org/wiki/Stream_(computing) "Stream (computing)")*.

The empty sequence ( ) is included in most notions of sequence. It may be excluded depending on the context.

## Examples and notation

A sequence can be thought of as a list of elements with a particular order. Sequences are useful in a number of mathematical disciplines for studying [functions](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)"), [spaces](https://en.wikipedia.org/wiki/Space_(mathematics) "Space (mathematics)"), and other mathematical structures using the [convergence](#Limits_and_convergence) properties of sequences. In particular, sequences are the basis for [series](https://en.wikipedia.org/wiki/Series_(mathematics) "Series (mathematics)"), which are important in [differential equations](https://en.wikipedia.org/wiki/Differential_equations) and [analysis](https://en.wikipedia.org/wiki/Analysis_(mathematics)). Sequences are also of interest in their own right, and can be studied as patterns or puzzles, such as in the study of [prime numbers](https://en.wikipedia.org/wiki/Prime_number).

There are a number of ways to denote a sequence, some of which are more useful for specific types of sequences. One way to specify a sequence is to list all its elements. For example, the first four odd numbers form the sequence (1, 3, 5, 7). This notation is used for infinite sequences as well. For instance, the infinite sequence of positive odd integers is written as (1, 3, 5, 7, ...). Because notating sequences with [ellipsis](https://en.wikipedia.org/wiki/Ellipsis) leads to ambiguity, listing is most useful for customary infinite sequences which can be easily recognized from their first few elements. Other ways of denoting a sequence are discussed after the examples.

### Examples

![[media/dc50f6a4f4b01f1e7f2c048af2f672a5ef6c98a8.png]]
A [tiling](https://en.wikipedia.org/wiki/Tessellation) with squares whose sides are successive Fibonacci numbers in length.

The [prime numbers](https://en.wikipedia.org/wiki/Prime_number) are the [natural numbers](https://en.wikipedia.org/wiki/Natural_numbers) greater than 1 that have no [divisors](https://en.wikipedia.org/wiki/Divisor) but 1 and themselves. Taking these in their natural order gives the sequence (2, 3, 5, 7, 11, 13, 17, ...). The prime numbers are widely used in [mathematics](https://en.wikipedia.org/wiki/Mathematics), particularly in [number theory](https://en.wikipedia.org/wiki/Number_theory) where many results related to them exist.

The [Fibonacci numbers](https://en.wikipedia.org/wiki/Fibonacci_numbers) comprise the integer sequence in which each element is the sum of the previous two elements. The first two elements are either 0 and 1 or 1 and 1 so that the sequence is (0, 1, 1, 2, 3, 5, 8, 13, 21, 34, ...).

Other examples of sequences include those made up of [rational numbers](https://en.wikipedia.org/wiki/Rational_numbers), [real numbers](https://en.wikipedia.org/wiki/Real_number) and [complex numbers](https://en.wikipedia.org/wiki/Complex_numbers). The sequence (.9, .99, .999, .9999, ...), for instance, approaches the number 1. In fact, every real number can be written as the [limit](https://en.wikipedia.org/wiki/Limit_of_a_sequence) of a sequence of rational numbers (e.g. via its [decimal expansion](https://en.wikipedia.org/wiki/Decimal_expansion), also see *[completeness of the real numbers](https://en.wikipedia.org/wiki/Completeness_of_the_real_numbers)*). As another example, [π](https://en.wikipedia.org/wiki/Pi) is the limit of the sequence (3, 3.1, 3.14, 3.141, 3.1415, ...), which is increasing. A related sequence is the sequence of decimal digits of π, that is, (3, 1, 4, 1, 5, 9, ...). Unlike the preceding sequence, this sequence does not have any pattern that is easily discernible by inspection.

Other examples are sequences of [functions](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)"), whose elements are functions instead of numbers.

The [On-Line Encyclopedia of Integer Sequences](https://en.wikipedia.org/wiki/On-Line_Encyclopedia_of_Integer_Sequences) comprises a large list of examples of integer sequences.

### Indexing

Other notations can be useful for sequences whose pattern cannot be easily guessed or for sequences that do not have a pattern such as the digits of [π](https://en.wikipedia.org/wiki/Pi). One such notation is to write down a general formula for computing the *n*th term as a function of *n*, enclose it in parentheses, and include a subscript indicating the set of values that *n* can take. For example, in this notation the sequence of even numbers could be written as $(2n)_{n\in \mathbb {N} }$. The sequence of squares could be written as $(n^{2})_{n\in \mathbb {N} }$. The variable *n* is called an [index](https://en.wikipedia.org/wiki/Indexed_family), and the set of values that it can take is called the [index set](https://en.wikipedia.org/wiki/Index_set).

It is often useful to combine this notation with the technique of treating the elements of a sequence as individual variables. This yields expressions like $(a_{n})_{n\in \mathbb {N} }$, which denotes a sequence whose *n*th element is given by the variable $a_{n}$. For example:

${\begin{aligned}a_{1}&=1{\text{st element of }}(a_{n})_{n\in \mathbb {N} }\\a_{2}&=2{\text{nd element }}\\a_{3}&=3{\text{rd element }}\\&\;\;\vdots \\a_{n-1}&=(n-1){\text{th element}}\\a_{n}&=n{\text{th element}}\\a_{n+1}&=(n+1){\text{th element}}\\&\;\;\vdots \end{aligned}}$

One can consider multiple sequences at the same time by using different variables; e.g. $(b_{n})_{n\in \mathbb {N} }$ could be a different sequence than $(a_{n})_{n\in \mathbb {N} }$. One can even consider a sequence of sequences: $((a_{m,n})_{n\in \mathbb {N} })_{m\in \mathbb {N} }$ denotes a sequence whose *m*th term is the sequence $(a_{m,n})_{n\in \mathbb {N} }$.

An alternative to writing the domain of a sequence in the subscript is to indicate the range of values that the index can take by listing its highest and lowest legal values. For example, the notation $(k^{2}){\vphantom {)}}_{k=1}^{10}$ denotes the ten-term sequence of squares $(1,4,9,\ldots ,100)$. The limits $\infty$ and $-\infty$ are allowed, but they do not represent valid values for the index, only the [supremum](https://en.wikipedia.org/wiki/Supremum) or [infimum](https://en.wikipedia.org/wiki/Infimum) of such values, respectively. For example, the sequence ${(a_{n})}_{n=1}^{\infty }$ is the same as the sequence $(a_{n})_{n\in \mathbb {N} }$, and does not contain an additional term "at infinity". The sequence ${(a_{n})}_{n=-\infty }^{\infty }$ is a **bi-infinite sequence**, and can also be written as $(\ldots ,a_{-1},a_{0},a_{1},a_{2},\ldots )$.

In cases where the set of indexing numbers is understood, the subscripts and superscripts are often left off. That is, one simply writes $(a_{k})$ for an arbitrary sequence. Often, the index *k* is understood to run from 1 to ∞. However, sequences are frequently indexed starting from zero, as in

${(a_{k})}_{k=0}^{\infty }=(a_{0},a_{1},a_{2},\ldots ).$

In some cases, the elements of the sequence are related naturally to a sequence of integers whose pattern can be easily inferred. In these cases, the index set may be implied by a listing of the first few abstract elements. For instance, the sequence of squares of [odd numbers](https://en.wikipedia.org/wiki/Odd_number) could be denoted in any of the following ways.

- $(1,9,25,\ldots )$
- $(a_{1},a_{3},a_{5},\ldots ),\qquad a_{k}=k^{2}$
- ${(a_{2k-1})}_{k=1}^{\infty },\qquad a_{k}=k^{2}$
- ${(a_{k})}_{k=1}^{\infty },\qquad a_{k}=(2k-1)^{2}$
- ${\bigl (}(2k-1)^{2}{\bigr )}_{k=1}^{\infty }$

Moreover, the subscripts and superscripts could have been left off in the third, fourth, and fifth notations, if the indexing set was understood to be the [natural numbers](https://en.wikipedia.org/wiki/Natural_numbers). In the second and third bullets, there is a well-defined sequence ${(a_{k})}_{k=1}^{\infty }$, but it is not the same as the sequence denoted by the expression.

### Defining a sequence by recursion

Sequences whose elements are related to the previous elements in a straightforward way are often defined using [recursion](https://en.wikipedia.org/wiki/Recursive_definition). This is in contrast to the definition of sequences of elements as functions of their positions.

To define a sequence by recursion, one needs a rule, called *recurrence relation* to construct each element in terms of the ones before it. In addition, enough initial elements must be provided so that all subsequent elements of the sequence can be computed by successive applications of the recurrence relation.

The [Fibonacci sequence](https://en.wikipedia.org/wiki/Fibonacci_sequence) is a simple classical example, defined by the recurrence relation

$a_{n}=a_{n-1}+a_{n-2},$

with initial terms $a_{0}=0$ and $a_{1}=1$. From this, a simple computation shows that the first ten terms of this sequence are 0, 1, 1, 2, 3, 5, 8, 13, 21, and 34.

A complicated example of a sequence defined by a recurrence relation is [Recamán's sequence](https://en.wikipedia.org/wiki/Recam%C3%A1n%27s_sequence), defined by the recurrence relation

${\begin{cases}a_{n}=a_{n-1}-n,\quad {\text{if the result is positive and not already in the previous terms,}}\\a_{n}=a_{n-1}+n,\quad {\text{otherwise}},\end{cases}}$

with initial term $a_{0}=0.$

A *linear recurrence with constant coefficients* is a recurrence relation of the form

$a_{n}=c_{0}+c_{1}a_{n-1}+\dots +c_{k}a_{n-k},$

where $c_{0},\dots ,c_{k}$ are [constants](https://en.wikipedia.org/wiki/Constant_(mathematics) "Constant (mathematics)"). There is a general method for expressing the general term $a_{n}$ of such a sequence as a function of n; see [Linear recurrence](https://en.wikipedia.org/wiki/Linear_recurrence). In the case of the Fibonacci sequence, one has $c_{0}=0,c_{1}=c_{2}=1,$ and the resulting function of n is given by [Binet's formula](https://en.wikipedia.org/wiki/Binet%27s_formula).

A [holonomic sequence](https://en.wikipedia.org/wiki/Holonomic_sequence) is a sequence defined by a recurrence relation of the form

$a_{n}=c_{1}a_{n-1}+\dots +c_{k}a_{n-k},$

where $c_{1},\dots ,c_{k}$ are [polynomials](https://en.wikipedia.org/wiki/Polynomial) in n. For most holonomic sequences, there is no explicit formula for expressing $a_{n}$ as a function of n. Nevertheless, holonomic sequences play an important role in various areas of mathematics. For example, many [special functions](https://en.wikipedia.org/wiki/Special_functions) have a [[Taylor Series]] whose sequence of coefficients is holonomic. The use of the recurrence relation allows a fast computation of values of such special functions.

Not all sequences can be specified by a recurrence relation. An example is the sequence of [prime numbers](https://en.wikipedia.org/wiki/Prime_number) in their natural order (2, 3, 5, 7, 11, 13, 17, ...).

## Formal definition and basic properties

### Definition

Formally, a sequence can be defined as a [function](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)") whose [domain](https://en.wikipedia.org/wiki/Domain_of_a_function) is an [interval](https://en.wikipedia.org/wiki/Interval_(mathematics) "Interval (mathematics)") of [integers](https://en.wikipedia.org/wiki/Integers). The elements of the domain are the positions or indices of the elements in the sequence, while the values taken by the function are the elements of the sequence. The interval can be finite or infinite; thus, this definition covers several different uses of the word "sequence", including one-sided infinite sequences, bi-infinite sequences, and finite sequences (see below for definitions of these kinds of sequences). In some contexts, the [codomain](https://en.wikipedia.org/wiki/Codomain) of the sequence (the possible values of the terms) is fixed by context, for example by requiring it to be the set $\mathbb {R}$ of real numbers, the set $\mathbb {C}$ of complex numbers, or a [topological space](https://en.wikipedia.org/wiki/Topological_space).

Although sequences are a type of function, they are usually distinguished notationally from functions in that the input is written as a subscript rather than in parentheses, that is, *a<sub>n</sub>* rather than *a*(*n*). There are terminological differences as well: the value of a sequence at the lowest input (often 1) is called the "first element" of the sequence, the value at the second smallest input (often 2) is called the "second element", etc. Also, while a function abstracted from its input is usually denoted by a single letter (such as *f*), a sequence abstracted from its input is usually written by a notation such as $(a_{n})_{n\in A}$, or just as $(a_{n}).$ Here *A* is the domain, or index set, of the sequence.

### Finite and infinite

The **length** of a sequence is defined as the number of terms in the sequence.

A sequence of a finite length is a **finite sequence**. A finite sequence of length *n* is also called an [n-tuple](https://en.wikipedia.org/wiki/N-tuple). Finite sequences include the **empty sequence**, denoted ( ), that has no elements.

 Normally, the term *infinite sequence* refers to a sequence that is infinite in one direction, and finite in the other; such a sequence has a first element, but no final element, and are called **singly infinite sequence** or a **one-sided infinite sequence** when disambiguation is needed. In contrast, a sequence that is infinite in both directions—i.e. that has neither a first nor a final element—is called a **bi-infinite sequence**, **two-way infinite sequence**, or **doubly infinite sequence**. A function from $\mathbb {Z}$ the set of *all* [integers](https://en.wikipedia.org/wiki/Integers), into a set, for example the sequence of all even integers ( ..., −4, −2, 0, 2, 4, 6, 8, ... ), is bi-infinite. This sequence could be denoted ${(2n)}_{n=-\infty }^{\infty }$.

### Increasing and decreasing

A sequence is said to be *monotonically increasing* if each term is greater than or equal to the one before it. For example, the sequence ${(a_{n})}_{n=1}^{\infty }$ is monotonically increasing if and only if $a_{n+1}\geq a_{n}$ for all $n\in \mathbf {N} .$ If each consecutive term is strictly greater than (\>) the previous term then the sequence is called **strictly monotonically increasing**. A sequence is **monotonically decreasing** if each consecutive term is less than or equal to the previous one, and is **strictly monotonically decreasing** if each is strictly less than the previous. If a sequence is either increasing or decreasing it is called a **monotone** sequence. This is a special case of the more general notion of a [monotonic function](https://en.wikipedia.org/wiki/Monotonic_function).

The terms **nondecreasing** and **nonincreasing** are often used in place of *increasing* and *decreasing* in order to avoid any possible confusion with *strictly increasing* and *strictly decreasing*, respectively.

### Bounded

If the sequence of real numbers (*a<sub>n</sub>*) is such that all the terms are less than some real number *M*, then the sequence is said to be **bounded from above**. In other words, this means that there exists *M* such that for all *n*, *a<sub>n</sub>* ≤ *M*. Any such *M* is called an *upper bound*. Likewise, if, for some real *m*, *a<sub>n</sub>* ≥ *m* for all *n* greater than some *N*, then the sequence is **bounded from below** and any such *m* is called a *lower bound*. If a sequence is both bounded from above and bounded from below, then the sequence is said to be **bounded**.

### Subsequences

A **[subsequence](https://en.wikipedia.org/wiki/Subsequence)** of a given sequence is a sequence formed from the given sequence by deleting some of the elements without disturbing the relative positions of the remaining elements. For instance, the sequence of positive even integers (2, 4, 6, ...) is a subsequence of the positive integers (1, 2, 3, ...). The positions of some elements change when other elements are deleted. However, the relative positions are preserved.

Formally, a subsequence of the sequence $(a_{n})_{n\in \mathbb {N} }$ is any sequence of the form $(a_{n_{k}})_{k\in \mathbb {N} }$, where $(n_{k})_{k\in \mathbb {N} }$ is a strictly increasing sequence of positive integers.

### Other types of sequences

Some other types of sequences that are easy to define include:

- An **[integer sequence](https://en.wikipedia.org/wiki/Integer_sequence)** is a sequence whose terms are integers.
- A **[polynomial sequence](https://en.wikipedia.org/wiki/Polynomial_sequence)** is a sequence whose terms are polynomials.
- A positive integer sequence is sometimes called **multiplicative**, if *a*<sub>*nm*</sub> = *a*<sub>*n*</sub> *a*<sub>*m*</sub> for all pairs *n*, *m* such that *n* and *m* are [coprime](https://en.wikipedia.org/wiki/Coprime). In other instances, sequences are often called *multiplicative*, if *a*<sub>*n*</sub> = *na*<sub>1</sub> for all *n*. Moreover, a *multiplicative* Fibonacci sequence satisfies the recursion relation *a*<sub>*n*</sub> = *a*<sub>*n*−1</sub> *a*<sub>*n*−2</sub>.
- A [binary sequence](https://en.wikipedia.org/wiki/Binary_sequence) is a sequence whose terms have one of two discrete values, e.g. [base 2](https://en.wikipedia.org/wiki/Base_2) values (0,1,1,0, ...), a series of coin tosses (Heads/Tails) H,T,H,H,T, ..., the answers to a set of True or False questions (T, F, T, T, ...), and so on.

## Limits and convergence

![[media/eb91c0d98f0490821adb9e2b75d9a7f5c1ee1934.png]]
The plot of a convergent sequence (<em>a<sub>n</sub></em>) is shown in blue. From the graph we can see that the sequence is converging to the limit zero as <em>n</em> increases.

An important property of a sequence is *convergence*. If a sequence converges, it converges to a particular value known as the *limit*. If a sequence converges to some limit, then it is **convergent**. A sequence that does not converge is **divergent**.

Informally, a sequence has a limit if the elements of the sequence become closer and closer to some value $L$ (called the limit of the sequence), and they become and remain *arbitrarily* close to $L$, meaning that given a real number $d$ greater than zero, all but a finite number of the elements of the sequence have a distance from $L$ less than $d$.

For example, the sequence $a_{n}={\frac {n+1}{2n^{2}}}$ shown to the right converges to the value 0. On the other hand, the sequences $b_{n}=n^{3}$ (which begins 1, 8, 27, ...) and $c_{n}=(-1)^{n}$ (which begins −1, 1, −1, 1, ...) are both divergent.

If a sequence converges, then the value it converges to is unique. This value is called the **limit** of the sequence. The limit of a convergent sequence $(a_{n})$ is normally denoted $\lim _{n\to \infty }a_{n}$. If $(a_{n})$ is a divergent sequence, then the expression $\lim _{n\to \infty }a_{n}$ is meaningless.

### Formal definition of convergence

A sequence of real numbers $(a_{n})$ **converges to** a real number $L$ if, for all $\varepsilon >0$, there exists a natural number $N$ such that for all $n\geq N$ we have

$|a_{n}-L|<\varepsilon .$

If $(a_{n})$ is a sequence of complex numbers rather than a sequence of real numbers, this last formula can still be used to define convergence, with the provision that $|\cdot |$ denotes the complex modulus, i.e. $|z|={\sqrt {z^{*}z}}$. If $(a_{n})$ is a sequence of points in a [metric space](https://en.wikipedia.org/wiki/Metric_space), then the formula can be used to define convergence, if the expression $|a_{n}-L|$ is replaced by the expression $\operatorname {dist} (a_{n},L)$, which denotes the [distance](https://en.wikipedia.org/wiki/Metric_(mathematics)) between $a_{n}$ and $L$.

### Applications and important results

If $(a_{n})$ and $(b_{n})$ are convergent sequences, then the following limits exist, and can be computed as follows:

- $\lim _{n\to \infty }(a_{n}\pm b_{n})=\lim _{n\to \infty }a_{n}\pm \lim _{n\to \infty }b_{n}$
- $\lim _{n\to \infty }ca_{n}=c\lim _{n\to \infty }a_{n}$ for all real numbers $c$
- $\lim _{n\to \infty }(a_{n}b_{n})={\bigl (}\lim _{n\to \infty }a_{n}{\bigr )}{\bigl (}\lim _{n\to \infty }b_{n}{\bigr )}$
- $\lim _{n\to \infty }{\frac {a_{n}}{b_{n}}}={\bigl (}\lim \limits _{n\to \infty }a_{n}{\bigr )}{\big /}{\bigl (}\lim \limits _{n\to \infty }b_{n}{\bigr )}$, provided that $\lim _{n\to \infty }b_{n}\neq 0$
- $\lim _{n\to \infty }a_{n}^{p}={\bigl (}\lim _{n\to \infty }a_{n}{\bigr )}^{p}$ for all $p>0$ and $a_{n}>0$

Moreover:

- If $a_{n}\leq b_{n}$ for all $n$ greater than some $N$, then $\lim _{n\to \infty }a_{n}\leq \lim _{n\to \infty }b_{n}$.
- ([Squeeze theorem](https://en.wikipedia.org/wiki/Squeeze_theorem))  
  If $(c_{n})$ is a sequence such that $a_{n}\leq c_{n}\leq b_{n}$ for all $n>N$ and $\lim _{n\to \infty }a_{n}=\lim _{n\to \infty }b_{n}=L$,  
  then $(c_{n})$ is convergent, and $\lim _{n\to \infty }c_{n}=L$.
- If a sequence is [bounded](#Bounded) and [monotonic](#Increasing_and_decreasing) then it is convergent.
- A sequence is convergent if and only if all of its subsequences are convergent.

### Cauchy sequences

![[media/1cb4176e0c11aeeecf9d2cb29f03f408d09eac8e.png]]
The plot of a Cauchy sequence (<em>X<sub>n</sub></em>), shown in blue, as <em>X<sub>n</sub></em> versus <em>n</em>. In the graph the sequence appears to be converging to a limit as the distance between consecutive terms in the sequence gets smaller as <em>n</em> increases. In the [real numbers](https://en.wikipedia.org/wiki/Real_number) every Cauchy sequence converges to some limit.

A Cauchy sequence is a sequence whose terms become arbitrarily close together as n gets very large. The notion of a Cauchy sequence is important in the study of sequences in [metric spaces](https://en.wikipedia.org/wiki/Metric_spaces), and, in particular, in [real analysis](https://en.wikipedia.org/wiki/Real_analysis). One particularly important result in real analysis is *Cauchy characterization of convergence for sequences*:

A sequence of real numbers is convergent (in the reals) if and only if it is Cauchy.

In contrast, there are Cauchy sequences of [rational numbers](https://en.wikipedia.org/wiki/Rational_numbers) that are not convergent in the rationals, e.g. the sequence defined by $x_{1}=1$ and $x_{n+1}={\tfrac {1}{2}}{\bigl (}x_{n}+{\tfrac {2}{x_{n}}}{\bigr )}$ is Cauchy, but has no rational limit (cf. [Cauchy sequence § Non-example: rational numbers](https://en.wikipedia.org/wiki/Cauchy_sequence#Non-example:_rational_numbers)). More generally, any sequence of rational numbers that converges to an [irrational number](https://en.wikipedia.org/wiki/Irrational_number) is Cauchy, but not convergent when interpreted as a sequence in the set of rational numbers.

Metric spaces that satisfy the Cauchy characterization of convergence for sequences are called [complete metric spaces](https://en.wikipedia.org/wiki/Complete_metric_space) and are particularly nice for analysis.

### Infinite limits

In calculus, it is common to define notation for sequences which do not converge in the sense discussed above, but which instead become and remain arbitrarily large, or become and remain arbitrarily negative. If $a_{n}$ becomes arbitrarily large as $n\to \infty$, we write

$\lim _{n\to \infty }a_{n}=\infty .$

In this case we say that the sequence **diverges**, or that it **converges to infinity**. An example of such a sequence is *a*<sub>*n*</sub> = *n*.

If $a_{n}$ becomes arbitrarily negative (i.e. negative and large in magnitude) as $n\to \infty$, we write

$\lim _{n\to \infty }a_{n}=-\infty$

and say that the sequence **diverges** or **converges to negative infinity**.

## Series

A **series** is, informally speaking, the sum of the terms of a sequence. That is, it is an expression of the form $\sum _{n=1}^{\infty }a_{n}$ or $a_{1}+a_{2}+\cdots$, where $(a_{n})$ is a sequence of real or complex numbers. The **partial sums** of a series are the expressions resulting from replacing the infinity symbol with a finite number, i.e. the *N*th partial sum of the series $\sum _{n=1}^{\infty }a_{n}$ is the number

$S_{N}=\sum _{n=1}^{N}a_{n}=a_{1}+a_{2}+\cdots +a_{N}.$

The partial sums themselves form a sequence $(S_{N})_{N\in \mathbb {N} }$, which is called the **sequence of partial sums** of the series $\sum _{n=1}^{\infty }a_{n}$. If the sequence of partial sums converges, then we say that the series $\sum _{n=1}^{\infty }a_{n}$ is **convergent**, and the limit $\lim _{N\to \infty }S_{N}$ is called the **value** of the series. The same notation is used to denote a series and its value, i.e. we write $\sum _{n=1}^{\infty }a_{n}=\lim _{N\to \infty }S_{N}$.

## Use in other fields of mathematics

### Topology

Sequences play an important role in topology, especially in the study of [metric spaces](https://en.wikipedia.org/wiki/Metric_spaces). For instance:

- A [metric space](https://en.wikipedia.org/wiki/Metric_space) is [compact](https://en.wikipedia.org/wiki/Compact_space) exactly when it is [sequentially compact](https://en.wikipedia.org/wiki/Sequential_compactness).
- A function from a metric space to another metric space is [continuous](https://en.wikipedia.org/wiki/Continuous_function) exactly when it takes convergent sequences to convergent sequences.
- A metric space is a [connected space](https://en.wikipedia.org/wiki/Connected_space) if and only if, whenever the space is partitioned into two sets, one of the two sets contains a sequence converging to a point in the other set.
- A [topological space](https://en.wikipedia.org/wiki/Topological_space) is [separable](https://en.wikipedia.org/wiki/Separable_space) exactly when there is a dense sequence of points.

Sequences can be generalized to [nets](https://en.wikipedia.org/wiki/Net_(mathematics) "Net (mathematics)") or [filters](https://en.wikipedia.org/wiki/Filter_on_a_set). These generalizations allow one to extend some of the above theorems to spaces without metrics.

#### Product topology

The [topological product](https://en.wikipedia.org/wiki/Product_topology) of a sequence of topological spaces is the [cartesian product](https://en.wikipedia.org/wiki/Cartesian_product) of those spaces, equipped with a [natural topology](https://en.wikipedia.org/wiki/Natural_topology) called the [product topology](https://en.wikipedia.org/wiki/Product_topology).

More formally, given a sequence of spaces $(X_{i})_{i\in \mathbb {N} }$, the product space

$X:=\prod _{i\in \mathbb {N} }X_{i},$

is defined as the set of all sequences $(x_{i})_{i\in \mathbb {N} }$ such that for each *i*, $x_{i}$ is an element of $X_{i}$. The **[canonical projections](https://en.wikipedia.org/wiki/Projection_(set_theory) "Projection (set theory)")** are the maps *p<sub>i</sub>* : *X* → *X<sub>i</sub>* defined by the equation $p_{i}((x_{j})_{j\in \mathbb {N} })=x_{i}$. Then the **product topology** on *X* is defined to be the [coarsest topology](https://en.wikipedia.org/wiki/Coarsest_topology) (i.e. the topology with the fewest open sets) for which all the projections *p<sub>i</sub>* are [continuous](https://en.wikipedia.org/wiki/Continuous_(topology)). The product topology is sometimes called the **Tychonoff topology**.

### Analysis

When discussing sequences in [analysis](https://en.wikipedia.org/wiki/Mathematical_analysis), one will generally consider sequences of the form

$(x_{1},x_{2},x_{3},\dots ){\text{ or }}(x_{0},x_{1},x_{2},\dots )$

which is to say, infinite sequences of elements indexed by [natural numbers](https://en.wikipedia.org/wiki/Natural_number).

A sequence may start with an index different from 1 or 0. For example, the sequence defined by *x<sub>n</sub>* = 1/[log](https://en.wikipedia.org/wiki/Logarithm)(*n*) would be defined only for *n* ≥ 2. When talking about such infinite sequences, it is usually sufficient (and does not change much for most considerations) to assume that the members of the sequence are defined at least for all indices [large enough](https://en.wikipedia.org/wiki/Large_enough), that is, greater than some given *N*.

The most elementary type of sequences are numerical ones, that is, sequences of [real](https://en.wikipedia.org/wiki/Real_number) or [complex](https://en.wikipedia.org/wiki/Complex_number) numbers. This type can be generalized to sequences of elements of some [[Vector Space]]. In analysis, the vector spaces considered are often [function spaces](https://en.wikipedia.org/wiki/Function_space). Even more generally, one can study sequences with elements in some [topological space](https://en.wikipedia.org/wiki/Topological_space).

#### Sequence spaces

A [sequence space](https://en.wikipedia.org/wiki/Sequence_space) is a [[Vector Space]] whose elements are infinite sequences of [real](https://en.wikipedia.org/wiki/Real_number) or [complex](https://en.wikipedia.org/wiki/Complex_number) numbers. Equivalently, it is a [function space](https://en.wikipedia.org/wiki/Function_space) whose elements are functions from the [natural numbers](https://en.wikipedia.org/wiki/Natural_numbers) to the [field](https://en.wikipedia.org/wiki/Field_(mathematics) "Field (mathematics)") *K*, where *K* is either the field of real numbers or the field of complex numbers. The set of all such functions is naturally identified with the set of all possible infinite sequences with elements in *K*, and can be turned into a [[Vector Space]] under the operations of [pointwise addition](https://en.wikipedia.org/wiki/Pointwise_addition) of functions and pointwise scalar multiplication. All sequence spaces are [linear subspaces](https://en.wikipedia.org/wiki/Linear_subspace) of this space. Sequence spaces are typically equipped with a [norm](https://en.wikipedia.org/wiki/Norm_(mathematics) "Norm (mathematics)"), or at least the structure of a [topological vector space](https://en.wikipedia.org/wiki/Topological_vector_space).

The most important sequences spaces in analysis are the ℓ<sup>*p*</sup> spaces, consisting of the *p*-power summable sequences, with the *p*-norm. These are special cases of [L<sup>*p*</sup> spaces](https://en.wikipedia.org/wiki/Lp_space) for the [counting measure](https://en.wikipedia.org/wiki/Counting_measure) on the set of natural numbers. Other important classes of sequences like convergent sequences or [null sequences](https://en.wikipedia.org/wiki/Sequence_space#c,_c0_and_c00) form sequence spaces, respectively denoted *c* and *c*<sub>0</sub>, with the sup norm. Any sequence space can also be equipped with the [topology](https://en.wikipedia.org/wiki/Topology) of [pointwise convergence](https://en.wikipedia.org/wiki/Pointwise_convergence), under which it becomes a special kind of [Fréchet space](https://en.wikipedia.org/wiki/Fr%C3%A9chet_space) called an [FK-space](https://en.wikipedia.org/wiki/FK-space).

### Linear algebra

Sequences over a [field](https://en.wikipedia.org/wiki/Field_(mathematics) "Field (mathematics)") may also be viewed as [vectors](https://en.wikipedia.org/wiki/Vector_(geometric)) in a [[Vector Space]]. Specifically, the set of *F*-valued sequences (where *F* is a field) is a [function space](https://en.wikipedia.org/wiki/Function_space) (in fact, a [product space](https://en.wikipedia.org/wiki/Product_space)) of *F*-valued functions over the set of natural numbers.

### Abstract algebra

Abstract algebra employs several types of sequences, including sequences of mathematical objects such as groups or rings.

#### Free monoid

If *A* is a set, the [free monoid](https://en.wikipedia.org/wiki/Free_monoid) over *A* (denoted *A*<sup>\*</sup>, also called [Kleene star](https://en.wikipedia.org/wiki/Kleene_star) of *A*) is a [monoid](https://en.wikipedia.org/wiki/Monoid) containing all the finite sequences (or strings) of zero or more elements of *A*, with the binary operation of concatenation. The [free semigroup](https://en.wikipedia.org/wiki/Free_semigroup) *A*<sup>+</sup> is the subsemigroup of *A*<sup>\*</sup> containing all elements except the empty sequence.

#### Exact sequences

In the context of [group theory](https://en.wikipedia.org/wiki/Group_theory), a sequence

$G_{0}\;{\overset {f_{1}}{\longrightarrow }}\;G_{1}\;{\overset {f_{2}}{\longrightarrow }}\;G_{2}\;{\overset {f_{3}}{\longrightarrow }}\;\cdots \;{\overset {f_{n}}{\longrightarrow }}\;G_{n}$

of [groups](https://en.wikipedia.org/wiki/Group_(mathematics) "Group (mathematics)") and [group homomorphisms](https://en.wikipedia.org/wiki/Group_homomorphism) is called **exact**, if the [image](https://en.wikipedia.org/wiki/Image_(mathematics) "Image (mathematics)") (or [range](https://en.wikipedia.org/wiki/Range_of_a_function)) of each homomorphism is equal to the [kernel](https://en.wikipedia.org/wiki/Kernel_(algebra) "Kernel (algebra)") of the next:

$\mathrm {im} (f_{k})=\mathrm {ker} (f_{k+1})$

The sequence of groups and homomorphisms may be either finite or infinite.

A similar definition can be made for certain other [algebraic structures](https://en.wikipedia.org/wiki/Algebraic_structure). For example, one could have an exact sequence of [[Vector Space|vector spaces]] and [linear maps](https://en.wikipedia.org/wiki/Linear_map), or of [modules](https://en.wikipedia.org/wiki/Module_(mathematics) "Module (mathematics)") and [module homomorphisms](https://en.wikipedia.org/wiki/Module_homomorphism).

#### Spectral sequences

In [homological algebra](https://en.wikipedia.org/wiki/Homological_algebra) and [algebraic topology](https://en.wikipedia.org/wiki/Algebraic_topology), a **spectral sequence** is a means of computing homology groups by taking successive approximations. Spectral sequences are a generalization of [exact sequences](https://en.wikipedia.org/wiki/Exact_sequence), and since their introduction by [Jean Leray](https://en.wikipedia.org/wiki/Jean_Leray) (), they have become an important research tool, particularly in [homotopy theory](https://en.wikipedia.org/wiki/Homotopy_theory).

### Set theory

An [ordinal-indexed sequence](https://en.wikipedia.org/wiki/Order_topology#Ordinal-indexed_sequences) is a generalization of a sequence. If α is a [limit ordinal](https://en.wikipedia.org/wiki/Limit_ordinal) and *X* is a set, an α-indexed sequence of elements of *X* is a function from α to *X*. In this terminology an ω-indexed sequence is an ordinary sequence.

### Computing

In [computer science](https://en.wikipedia.org/wiki/Computer_science), finite sequences are called [lists](https://en.wikipedia.org/wiki/List_(computer_science)). Potentially infinite sequences are called [streams](https://en.wikipedia.org/wiki/Stream_(computer_science)). Finite sequences of characters or digits are called [strings](https://en.wikipedia.org/wiki/String_(computer_science) "String (computer science)").

### Streams

Infinite sequences of [digits](https://en.wikipedia.org/wiki/Numerical_digit) (or [characters](https://en.wikipedia.org/wiki/Character_(computing) "Character (computing)")) drawn from a [finite](https://en.wikipedia.org/wiki/Finite_set) [alphabet](https://en.wikipedia.org/wiki/Alphabet_(computer_science)) are of particular interest in [theoretical computer science](https://en.wikipedia.org/wiki/Theoretical_computer_science). They are often referred to simply as *sequences* or *[streams](https://en.wikipedia.org/wiki/Stream_(computing) "Stream (computing)")*, as opposed to finite *[strings](https://en.wikipedia.org/wiki/String_(computer_science)#Formal_theory "String (computer science)")*. Infinite binary sequences, for instance, are infinite sequences of [bits](https://en.wikipedia.org/wiki/Bit) (characters drawn from the alphabet {0, 1}). The set *C* = {0, 1}<sup>∞</sup> of all infinite binary sequences is sometimes called the [Cantor space](https://en.wikipedia.org/wiki/Cantor_space).

An infinite binary sequence can represent a [formal language](https://en.wikipedia.org/wiki/Formal_language) (a set of strings) by setting the *n* th bit of the sequence to 1 if and only if the *n* th string (in [shortlex order](https://en.wikipedia.org/wiki/Shortlex_order)) is in the language. This representation is useful in the [diagonalization method](https://en.wikipedia.org/wiki/Cantor%27s_diagonal_argument) for proofs.

## See also

- [Enumeration](https://en.wikipedia.org/wiki/Enumeration)
- [On-Line Encyclopedia of Integer Sequences](https://en.wikipedia.org/wiki/On-Line_Encyclopedia_of_Integer_Sequences)
- [Recurrence relation](https://en.wikipedia.org/wiki/Recurrence_relation)
- [Sequence space](https://en.wikipedia.org/wiki/Sequence_space)

Operations

- [Cauchy product](https://en.wikipedia.org/wiki/Cauchy_product)

Examples

- [Discrete-time signal](https://en.wikipedia.org/wiki/Discrete-time_signal)
- [Farey sequence](https://en.wikipedia.org/wiki/Farey_sequence)
- [Fibonacci sequence](https://en.wikipedia.org/wiki/Fibonacci_number)
- [Look-and-say sequence](https://en.wikipedia.org/wiki/Look-and-say_sequence)
- [Thue–Morse sequence](https://en.wikipedia.org/wiki/Thue%E2%80%93Morse_sequence)
- [List of integer sequences](https://en.wikipedia.org/wiki/List_of_integer_sequences)

Types

- [±1-sequence](https://en.wikipedia.org/wiki/%C2%B11-sequence)
- [Arithmetic progression](https://en.wikipedia.org/wiki/Arithmetic_progression)
- [Automatic sequence](https://en.wikipedia.org/wiki/Automatic_sequence)
- [Cauchy sequence](https://en.wikipedia.org/wiki/Cauchy_sequence)
- [Constant-recursive sequence](https://en.wikipedia.org/wiki/Constant-recursive_sequence)
- [Geometric progression](https://en.wikipedia.org/wiki/Geometric_progression)
- [Harmonic progression](https://en.wikipedia.org/wiki/Harmonic_progression_(mathematics) "Harmonic progression (mathematics)")
- [Holonomic sequence](https://en.wikipedia.org/wiki/Holonomic_function)
- [Regular sequence](https://en.wikipedia.org/wiki/K-regular_sequence)
- [Pseudorandom binary sequence](https://en.wikipedia.org/wiki/Pseudorandom_binary_sequence)
- [Random sequence](https://en.wikipedia.org/wiki/Random_sequence)

Related concepts

- [List (computing)](https://en.wikipedia.org/wiki/List_(computing))
- [Net (topology)](https://en.wikipedia.org/wiki/Net_(topology)) (a generalization of sequences)
- [Ordinal-indexed sequence](https://en.wikipedia.org/wiki/Order_topology#Ordinal-indexed_sequences)
- [Recursion (computer science)](https://en.wikipedia.org/wiki/Recursion_(computer_science) "Recursion (computer science)")
- [Set (mathematics)](https://en.wikipedia.org/wiki/Set_(mathematics) "Set (mathematics)")
- [Tuple](https://en.wikipedia.org/wiki/Tuple)
- [Permutation](https://en.wikipedia.org/wiki/Permutation)

## Notes

1.  If the inequalities are replaced by strict inequalities then this is false: There are sequences such that $a_{n}<b_{n}$ for all $n$, but $\lim _{n\to \infty }a_{n}=\lim _{n\to \infty }b_{n}$.

## References

1.  ^   ["Sequences"](https://www.mathsisfun.com/algebra/sequences-series.html). *www.mathsisfun.com*. [Archived](https://web.archive.org/web/20200812220432/https://mathsisfun.com/algebra/sequences-series.html) from the original on 2020-08-12. Retrieved 2020-08-17.
2.  Weisstein, Eric W. ["Sequence"](https://mathworld.wolfram.com/Sequence.html). *mathworld.wolfram.com*. [Archived](https://web.archive.org/web/20200725104417/https://mathworld.wolfram.com/Sequence.html) from the original on 2020-07-25. Retrieved 2020-08-17.
3.  [Index to OEIS](https://oeis.org/wiki/Index_to_OEIS) [Archived](https://web.archive.org/web/20221018125328/https://oeis.org/wiki/Index_to_OEIS) 2022-10-18 at the [Wayback Machine](https://en.wikipedia.org/wiki/Wayback_Machine), On-Line Encyclopedia of Integer Sequences, 2020-12-03
4.  [Sloane, N. J. A.](https://en.wikipedia.org/wiki/Neil_Sloane) (ed.). ["Sequence A005132 (Recamán's sequence)"](https://oeis.org/A005132). *The [On-Line Encyclopedia of Integer Sequences](https://en.wikipedia.org/wiki/On-Line_Encyclopedia_of_Integer_Sequences)*. OEIS Foundation. Retrieved 26 January 2018.
5.  ^    Gaughan, Edward (2009). "1.1 Sequences and Convergence". *Introduction to Analysis*. AMS (2009). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8218-4787-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8218-4787-9).
6.  Edward B. Saff & Arthur David Snider (2003). ["Chapter 2.1"](https://books.google.com/books?id=fVsZAQAAIAAJ&q=saff+%26+Snider). *Fundamentals of Complex Analysis*. Prentice Hall. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-01-390-7874-3](https://en.wikipedia.org/wiki/Special:BookSources/978-01-390-7874-3). [Archived](https://web.archive.org/web/20230323163811/https://books.google.com/books?id=fVsZAQAAIAAJ&q=saff+%26+Snider) from the original on 2023-03-23. Retrieved 2015-11-15.
7.  James R. Munkres (2000). ["Chapters 1&2"](https://books.google.com/books?id=XjoZAQAAIAAJ). *Topology*. Prentice Hall, Incorporated. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-01-318-1629-9](https://en.wikipedia.org/wiki/Special:BookSources/978-01-318-1629-9). [Archived](https://web.archive.org/web/20230323163811/https://books.google.com/books?id=XjoZAQAAIAAJ) from the original on 2023-03-23. Retrieved 2015-11-15.
8.  Lando, Sergei K. (2003-10-21). "7.4 Multiplicative sequences". *Lectures on generating functions*. AMS. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8218-3481-7](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8218-3481-7).
9.  Falcon, Sergio (2003). "Fibonacci's multiplicative sequence". *International Journal of Mathematical Education in Science and Technology*. **34** (2): 310–315. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2003IJMES..34..310F](https://ui.adsabs.harvard.edu/abs/2003IJMES..34..310F). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/0020739031000158362](https://doi.org/10.1080%2F0020739031000158362). [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[10553/49167](https://hdl.handle.net/10553%2F49167). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [121280842](https://api.semanticscholar.org/CorpusID:121280842).
10. Dawikins, Paul. ["Series and Sequences"](http://tutorial.math.lamar.edu/Classes/CalcII/Sequences.aspx). *Paul's Online Math Notes/Calc II (notes)*. [Archived](https://web.archive.org/web/20121130095834/http://tutorial.math.lamar.edu/Classes/CalcII/Sequences.aspx) from the original on 30 November 2012. Retrieved 18 December 2012.
11. Oflazer, Kemal. ["FORMAL LANGUAGES, AUTOMATA AND COMPUTATION: DECIDABILITY"](http://www.andrew.cmu.edu/user/ko/pdfs/lecture-15.pdf) (PDF). *cmu.edu*. Carnegie-Mellon University. [Archived](https://web.archive.org/web/20150529101719/http://www.andrew.cmu.edu/user/ko/pdfs/lecture-15.pdf) (PDF) from the original on 29 May 2015. Retrieved 24 April 2015.

## External links

- ["Sequence"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society), 2001 \[1994\]
- [The On-Line Encyclopedia of Integer Sequences](http://oeis.org/)
- [Journal of Integer Sequences](http://www.cs.uwaterloo.ca/journals/JIS/index.html) (free)
