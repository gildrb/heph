[[linear-algebra.base]]

> Source: [[Linear Independence]]
> License: Wikipedia content is available under CC BY-SA 4.0.

![[media/a45f29da20b9b92922d75c1a2ad83260e1d7663c.png]]
Linearly independent vectors in $\mathbb {R} ^{3}$

![[media/02ed74b73d6bb89bd5f5f4b4960c5f435ca31df2.png]]
Linearly dependent vectors in a plane in $\mathbb {R} ^{3}$

In [linear algebra](https://en.wikipedia.org/wiki/Linear_algebra), a [set](https://en.wikipedia.org/wiki/Set_(mathematics) "Set (mathematics)") of [vectors](https://en.wikipedia.org/wiki/Vector_(mathematics_and_physics) "Vector (mathematics and physics)") is said to be **linearly independent** if there exists no vector in the set that is equal to a [linear combination](https://en.wikipedia.org/wiki/Linear_combination) of the other vectors in the set. If such a vector exists, then the vectors are said to be **linearly dependent**. Linear independence is part of the definition of [linear basis](https://en.wikipedia.org/wiki/Basis_(linear_algebra) "Basis (linear algebra)").

A vector space can be of finite dimension or infinite dimension depending on the maximum number of linearly independent vectors. The definition of linear dependence and the ability to determine whether a subset of vectors in a vector space is linearly dependent are central to determining the dimension of a vector space.

## Definition

A sequence of vectors $\mathbf {v} _{1},\mathbf {v} _{2},\dots ,\mathbf {v} _{k}$ from a [[Vector Space]] V is said to be *linearly dependent*, if there exist [scalars](https://en.wikipedia.org/wiki/Scalar_(mathematics) "Scalar (mathematics)") $a_{1},a_{2},\dots ,a_{k},$ not all zero, such that

$a_{1}\mathbf {v} _{1}+a_{2}\mathbf {v} _{2}+\cdots +a_{k}\mathbf {v} _{k}=\mathbf {0} ,$

where $\mathbf {0}$ denotes the zero vector.

If $k=1$, this implies that a single vector is linear dependent if and only if it is the zero vector.

If $k>1$, this implies that at least one of the scalars is nonzero, say $a_{1}\neq 0$, and the above equation is able to be written as

$\mathbf {v} _{1}={\frac {-a_{2}}{a_{1}}}\mathbf {v} _{2}+\cdots +{\frac {-a_{k}}{a_{1}}}\mathbf {v} _{k}.$

Thus, a set of vectors is linearly dependent if and only if one of them is zero or a [linear combination](https://en.wikipedia.org/wiki/Linear_combination) of the others.

A sequence of vectors $\mathbf {v} _{1},\mathbf {v} _{2},\dots ,\mathbf {v} _{n}$ is said to be *linearly independent* if it is not linearly dependent, that is, if the equation

$a_{1}\mathbf {v} _{1}+a_{2}\mathbf {v} _{2}+\cdots +a_{n}\mathbf {v} _{n}=\mathbf {0} ,$

can only be satisfied by $a_{i}=0$ for $i=1,\dots ,n.$ This implies that no vector in the sequence can be represented as a linear combination of the remaining vectors in the sequence. In other words, a sequence of vectors is linearly independent if the only representation of $\mathbf {0}$ as a linear combination of its vectors is the trivial representation in which all the scalars $a_{i}$ are zero. Even more concisely, a sequence of vectors is linearly independent if and only if $\mathbf {0}$ can be represented as a linear combination of its vectors in a unique way.

If a sequence of vectors contains the same vector twice, it is necessarily dependent. The linear dependency of a sequence of vectors does not depend of the order of the terms in the sequence. This allows defining linear independence for a finite set of vectors: A finite set of vectors is *linearly independent* if the sequence obtained by ordering them is linearly independent. In other words, one has the following result that is often useful.

A sequence of vectors is linearly independent if and only if it does not contain the same vector twice and the set of its vectors is linearly independent.

### Infinite case

An infinite set of vectors is *linearly independent* if every finite [subset](https://en.wikipedia.org/wiki/Subset) is linearly independent. This definition applies also to finite sets of vectors, since a finite set is a finite subset of itself, and every subset of a linearly independent set is also linearly independent.

Conversely, an infinite set of vectors is *linearly dependent* if it contains a finite subset that is linearly dependent, or equivalently, if some vector in the set is a linear combination of other vectors in the set.

An [indexed family](https://en.wikipedia.org/wiki/Indexed_family) of vectors is *linearly independent* if it does not contain the same vector twice, and if the set of its vectors is linearly independent. Otherwise, the family is said to be *linearly dependent*.

A set of vectors which is linearly independent and [spans](https://en.wikipedia.org/wiki/Linear_span) some vector space, forms a [basis](https://en.wikipedia.org/wiki/Basis_(linear_algebra) "Basis (linear algebra)") for that vector space. For example, the vector space of all [polynomials](https://en.wikipedia.org/wiki/Polynomial) in x over the reals has the (infinite) subset {1, *x*, *x*<sup>2</sup>, ...} as a basis.

### Definition via span

Let $V$ be a vector space. A set $X\subseteq V$ is *linearly independent* if and only if $X$ is a [minimal element](https://en.wikipedia.org/wiki/Maximal_and_minimal_elements) of

$\{Y\subseteq V\mid X\subseteq \operatorname {Span} (Y)\}$

by the [inclusion order](https://en.wikipedia.org/wiki/Inclusion_order). In contrast, $X$ is *linearly dependent* if it has a proper subset whose span is a superset of $X$.

## Geometric examples

![[media/6e2993fc71ad3475d2d55c3cbce1df610932b049.png]]

- ${\vec {u}}$ and ${\vec {v}}$ are independent and define the [plane](https://en.wikipedia.org/wiki/Plane_(geometry)) P.
- ${\vec {u}}$, ${\vec {v}}$ and ${\vec {w}}$ are dependent because all three are contained in the same plane.
- ${\vec {u}}$ and ${\vec {j}}$ are dependent because they are parallel to each other.
- ${\vec {u}}$ , ${\vec {v}}$ and ${\vec {k}}$ are independent because ${\vec {u}}$ and ${\vec {v}}$ are independent of each other and ${\vec {k}}$ is not a linear combination of them or, equivalently, because they do not belong to a common plane. The three vectors define a three-dimensional space.
- The vectors ${\vec {o}}$ (null vector, whose components are equal to zero) and ${\vec {k}}$ are dependent since ${\vec {o}}=0{\vec {k}}$.

### Geographic location

A person describing the location of a certain place might say, "It is 3 miles north and 4 miles east of here." This is sufficient information to describe the location, because the geographic coordinate system may be considered as a 2-dimensional vector space (ignoring altitude and the curvature of the Earth's surface). The person might add, "The place is 5 miles northeast of here." This last statement is *true*, but it is not necessary to find the location.

In this example the "3 miles north" vector and the "4 miles east" vector are linearly independent. That is to say, the north vector cannot be described in terms of the east vector, and vice versa. The third "5 miles northeast" vector is a [linear combination](https://en.wikipedia.org/wiki/Linear_combination) of the other two vectors, and it makes the set of vectors *linearly dependent*, that is, one of the three vectors is unnecessary to define a specific location on a plane.

Also note that if altitude is not ignored, it becomes necessary to add a third vector to the linearly independent set. In general, n linearly independent vectors are required to describe all locations in n-dimensional space.

## Evaluating linear independence

### The zero vector

If one or more vectors from a given sequence of vectors $\mathbf {v} _{1},\dots ,\mathbf {v} _{k}$ is the zero vector $\mathbf {0}$ then the vectors $\mathbf {v} _{1},\dots ,\mathbf {v} _{k}$ are necessarily linearly dependent (and consequently, they are not linearly independent). To see why, suppose that $i$ is an index (i.e. an element of $\{1,\ldots ,k\}$) such that $\mathbf {v} _{i}=\mathbf {0} .$ Then let $a_{i}:=1$ (alternatively, letting $a_{i}$ be equal to any other non-zero scalar will also work) and then let all other scalars be $0$ (explicitly, this means that for any index $j$ other than $i$ (i.e. for $j\neq i$), let $a_{j}:=0$ so that consequently $a_{j}\mathbf {v} _{j}=0\mathbf {v} _{j}=\mathbf {0}$). Simplifying $a_{1}\mathbf {v} _{1}+\cdots +a_{k}\mathbf {v} _{k}$ gives:

$a_{1}\mathbf {v} _{1}+\cdots +a_{k}\mathbf {v} _{k}=\mathbf {0} +\cdots +\mathbf {0} +a_{i}\mathbf {v} _{i}+\mathbf {0} +\cdots +\mathbf {0} =a_{i}\mathbf {v} _{i}=a_{i}\mathbf {0} =\mathbf {0} .$

Because not all scalars are zero (in particular, $a_{i}\neq 0$), this proves that the vectors $\mathbf {v} _{1},\dots ,\mathbf {v} _{k}$ are linearly dependent.

As a consequence, the zero vector can not possibly belong to any collection of vectors that is linearly *in*dependent.

Now consider the special case where the sequence of $\mathbf {v} _{1},\dots ,\mathbf {v} _{k}$ has length $1$ (i.e. the case where $k=1$). A collection of vectors that consists of exactly one vector is linearly dependent if and only if that vector is zero. Explicitly, if $\mathbf {v} _{1}$ is any vector then the sequence $\mathbf {v} _{1}$ (which is a sequence of length $1$) is linearly dependent if and only if $\mathbf {v} _{1}=\mathbf {0}$; alternatively, the collection $\mathbf {v} _{1}$ is linearly independent if and only if $\mathbf {v} _{1}\neq \mathbf {0} .$

### Linear dependence and independence of two vectors

This example considers the special case where there are exactly two vector $\mathbf {u}$ and $\mathbf {v}$ from some real or complex vector space. The vectors $\mathbf {u}$ and $\mathbf {v}$ are linearly dependent [if and only if](https://en.wikipedia.org/wiki/If_and_only_if) at least one of the following is true:

1.  $\mathbf {u}$ is a scalar multiple of $\mathbf {v}$ (explicitly, this means that there exists a scalar $c$ such that $\mathbf {u} =c\mathbf {v}$) or
2.  $\mathbf {v}$ is a scalar multiple of $\mathbf {u}$ (explicitly, this means that there exists a scalar $c$ such that $\mathbf {v} =c\mathbf {u}$).

If $\mathbf {u} =\mathbf {0}$ then by setting $c:=0$ we have $c\mathbf {v} =0\mathbf {v} =\mathbf {0} =\mathbf {u}$ (this equality holds no matter what the value of $\mathbf {v}$ is), which shows that (1) is true in this particular case. Similarly, if $\mathbf {v} =\mathbf {0}$ then (2) is true because $\mathbf {v} =0\mathbf {u} .$ If $\mathbf {u} =\mathbf {v}$ (for instance, if they are both equal to the zero vector $\mathbf {0}$) then *both* (1) and (2) are true (by using $c:=1$ for both).

If $\mathbf {u} =c\mathbf {v}$ then $\mathbf {u} \neq \mathbf {0}$ is only possible if $c\neq 0$ *and* $\mathbf {v} \neq \mathbf {0}$; in this case, it is possible to multiply both sides by ${\frac {1}{c}}$ to conclude $\mathbf {v} ={\frac {1}{c}}\mathbf {u} .$ This shows that if $\mathbf {u} \neq \mathbf {0}$ and $\mathbf {v} \neq \mathbf {0}$ then (1) is true if and only if (2) is true; that is, in this particular case either both (1) and (2) are true (and the vectors are linearly dependent) or else both (1) and (2) are false (and the vectors are linearly *in*dependent). If $\mathbf {u} =c\mathbf {v}$ but instead $\mathbf {u} =\mathbf {0}$ then at least one of $c$ and $\mathbf {v}$ must be zero. Moreover, if exactly one of $\mathbf {u}$ and $\mathbf {v}$ is $\mathbf {0}$ (while the other is non-zero) then exactly one of (1) and (2) is true (with the other being false).

The vectors $\mathbf {u}$ and $\mathbf {v}$ are linearly *in*dependent if and only if $\mathbf {u}$ is not a scalar multiple of $\mathbf {v}$ *and* $\mathbf {v}$ is not a scalar multiple of $\mathbf {u}$.

### Vectors in R<sup>2</sup>

**Three vectors:** Consider the set of vectors $\mathbf {v} _{1}=(1,1),$ $\mathbf {v} _{2}=(-3,2),$ and $\mathbf {v} _{3}=(2,4),$ then the condition for linear dependence seeks a set of non-zero scalars, such that

$a_{1}{\begin{bmatrix}1\\1\end{bmatrix}}+a_{2}{\begin{bmatrix}-3\\2\end{bmatrix}}+a_{3}{\begin{bmatrix}2\\4\end{bmatrix}}={\begin{bmatrix}0\\0\end{bmatrix}},$

or

${\begin{bmatrix}1&-3&2\\1&2&4\end{bmatrix}}{\begin{bmatrix}a_{1}\\a_{2}\\a_{3}\end{bmatrix}}={\begin{bmatrix}0\\0\end{bmatrix}}.$

[Row reduce](https://en.wikipedia.org/wiki/Row_reduction) this matrix equation by subtracting the first row from the second to obtain,

${\begin{bmatrix}1&-3&2\\0&5&2\end{bmatrix}}{\begin{bmatrix}a_{1}\\a_{2}\\a_{3}\end{bmatrix}}={\begin{bmatrix}0\\0\end{bmatrix}}.$

Continue the row reduction by (i) dividing the second row by 5, and then (ii) multiplying by 3 and adding to the first row, that is

${\begin{bmatrix}1&0&16/5\\0&1&2/5\end{bmatrix}}{\begin{bmatrix}a_{1}\\a_{2}\\a_{3}\end{bmatrix}}={\begin{bmatrix}0\\0\end{bmatrix}}.$

Rearranging this equation allows us to obtain

${\begin{bmatrix}1&0\\0&1\end{bmatrix}}{\begin{bmatrix}a_{1}\\a_{2}\end{bmatrix}}={\begin{bmatrix}a_{1}\\a_{2}\end{bmatrix}}=-a_{3}{\begin{bmatrix}16/5\\2/5\end{bmatrix}}.$

which shows that non-zero *a*<sub>*i*</sub> exist such that $\mathbf {v} _{3}=(2,4)$ can be defined in terms of $\mathbf {v} _{1}=(1,1)$ and $\mathbf {v} _{2}=(-3,2).$ Thus, the three vectors are linearly dependent.

**Two vectors:** Now consider the linear dependence of the two vectors $\mathbf {v} _{1}=(1,1)$ and $\mathbf {v} _{2}=(-3,2),$ and check,

$a_{1}{\begin{bmatrix}1\\1\end{bmatrix}}+a_{2}{\begin{bmatrix}-3\\2\end{bmatrix}}={\begin{bmatrix}0\\0\end{bmatrix}},$

or

${\begin{bmatrix}1&-3\\1&2\end{bmatrix}}{\begin{bmatrix}a_{1}\\a_{2}\end{bmatrix}}={\begin{bmatrix}0\\0\end{bmatrix}}.$

The same row reduction presented above yields,

${\begin{bmatrix}1&0\\0&1\end{bmatrix}}{\begin{bmatrix}a_{1}\\a_{2}\end{bmatrix}}={\begin{bmatrix}0\\0\end{bmatrix}}.$

This shows that $a_{i}=0,$ which means that the vectors $\mathbf {v} _{1}=(1,1)$ and $\mathbf {v} _{2}=(-3,2)$ are linearly independent.

### Vectors in R<sup>4</sup>

In order to determine if the three vectors in $\mathbb {R} ^{4},$

$\mathbf {v} _{1}={\begin{bmatrix}1\\4\\2\\-3\end{bmatrix}},\mathbf {v} _{2}={\begin{bmatrix}7\\10\\-4\\-1\end{bmatrix}},\mathbf {v} _{3}={\begin{bmatrix}-2\\1\\5\\-4\end{bmatrix}}.$

are linearly dependent, form the matrix equation,

${\begin{bmatrix}1&7&-2\\4&10&1\\2&-4&5\\-3&-1&-4\end{bmatrix}}{\begin{bmatrix}a_{1}\\a_{2}\\a_{3}\end{bmatrix}}={\begin{bmatrix}0\\0\\0\\0\end{bmatrix}}.$

Row reduce this equation to obtain,

${\begin{bmatrix}1&7&-2\\0&-18&9\\0&0&0\\0&0&0\end{bmatrix}}{\begin{bmatrix}a_{1}\\a_{2}\\a_{3}\end{bmatrix}}={\begin{bmatrix}0\\0\\0\\0\end{bmatrix}}.$

Rearrange to solve for v<sub>3</sub> and obtain,

${\begin{bmatrix}1&7\\0&-18\end{bmatrix}}{\begin{bmatrix}a_{1}\\a_{2}\end{bmatrix}}=-a_{3}{\begin{bmatrix}-2\\9\end{bmatrix}}.$

This equation is easily solved to define non-zero *a*<sub>i</sub>,

$a_{1}=-3a_{3}/2,a_{2}=a_{3}/2,$

where $a_{3}$ can be chosen arbitrarily. Thus, the vectors $\mathbf {v} _{1},\mathbf {v} _{2},$ and $\mathbf {v} _{3}$ are linearly dependent.

### Alternative method using determinants

An alternative method relies on the fact that $n$ vectors in $\mathbb {R} ^{n}$ are linearly **independent** [if and only if](https://en.wikipedia.org/wiki/If_and_only_if) the [[Determinant]] of the [matrix](https://en.wikipedia.org/wiki/Matrix_(mathematics) "Matrix (mathematics)") formed by taking the vectors as its columns is non-zero.

In this case, the matrix formed by the vectors is

$A={\begin{bmatrix}1&-3\\1&2\end{bmatrix}}.$

We may write a linear combination of the columns as

$A\Lambda ={\begin{bmatrix}1&-3\\1&2\end{bmatrix}}{\begin{bmatrix}\lambda _{1}\\\lambda _{2}\end{bmatrix}}.$

We are interested in whether *A*Λ = **0** for some nonzero vector Λ. This depends on the determinant of $A$, which is

$\det A=1\cdot 2-1\cdot (-3)=5\neq 0.$

Since the [[Determinant]] is non-zero, the vectors $(1,1)$ and $(-3,2)$ are linearly independent.

Otherwise, suppose we have $m$ vectors of $n$ coordinates, with $m<n.$ Then *A* is an *n*×*m* matrix and Λ is a column vector with $m$ entries, and we are again interested in *A*Λ = **0**. As we saw previously, this is equivalent to a list of $n$ equations. Consider the first $m$ rows of $A$, the first $m$ equations; any solution of the full list of equations must also be true of the reduced list. In fact, if ⟨*i*<sub>1</sub>,...,*i*<sub>*m*</sub>⟩ is any list of $m$ rows, then the equation must be true for those rows.

$A_{\langle i_{1},\dots ,i_{m}\rangle }\Lambda =\mathbf {0} .$

Furthermore, the reverse is true. That is, we can test whether the $m$ vectors are linearly dependent by testing whether

$\det A_{\langle i_{1},\dots ,i_{m}\rangle }=0$

for all possible lists of $m$ rows. (In case $m=n$, this requires only one determinant, as above. If $m>n$, then it is a theorem that the vectors must be linearly dependent.) This fact is valuable for theory; in practical calculations more efficient methods are available.

### More vectors than dimensions

If there are more vectors than dimensions, the vectors are linearly dependent. This is illustrated in the example above of three vectors in $\mathbb {R} ^{2}.$

## Natural basis vectors

Let $V=\mathbb {R} ^{n}$ and consider the following elements in $V$, known as the [natural basis](https://en.wikipedia.org/wiki/Standard_basis) vectors:

${\begin{matrix}\mathbf {e} _{1}&=&(1,0,0,\ldots ,0)\\\mathbf {e} _{2}&=&(0,1,0,\ldots ,0)\\&\vdots \\\mathbf {e} _{n}&=&(0,0,0,\ldots ,1).\end{matrix}}$

Then $\mathbf {e} _{1},\mathbf {e} _{2},\ldots ,\mathbf {e} _{n}$ are linearly independent.

**Proof**

Suppose that $a_{1},a_{2},\ldots ,a_{n}$ are real numbers such that

$a_{1}\mathbf {e} _{1}+a_{2}\mathbf {e} _{2}+\cdots +a_{n}\mathbf {e} _{n}=\mathbf {0} .$

Since

$a_{1}\mathbf {e} _{1}+a_{2}\mathbf {e} _{2}+\cdots +a_{n}\mathbf {e} _{n}=\left(a_{1},a_{2},\ldots ,a_{n}\right),$

then $a_{i}=0$ for all $i=1,\ldots ,n.$

## Linear independence of functions

Let $V$ be the [[Vector Space]] of all differentiable [functions](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)") of a real variable $t$. Then the functions $e^{t}$ and $e^{2t}$ in $V$ are linearly independent.

### Proof

Suppose $a$ and $b$ are two real numbers such that

$ae^{t}+be^{2t}=0$

Take the first derivative of the above equation:

$ae^{t}+2be^{2t}=0$

for *all* values of $t.$ We need to show that $a=0$ and $b=0.$ In order to do this, we subtract the first equation from the second, giving $be^{2t}=0$. Since $e^{2t}$ is not zero for some $t$, $b=0.$ It follows that $a=0$ too. Therefore, according to the definition of linear independence, $e^{t}$ and $e^{2t}$ are linearly independent.

## Space of linear dependencies

A **linear dependency** or [linear relation](https://en.wikipedia.org/wiki/Linear_relation) among vectors **v**<sub>1</sub>, ..., **v**<sub>*n*</sub> is a [tuple](https://en.wikipedia.org/wiki/Tuple) (*a*<sub>1</sub>, ..., *a*<sub>*n*</sub>) with n [scalar](https://en.wikipedia.org/wiki/Scalar_(mathematics) "Scalar (mathematics)") components such that

$a_{1}\mathbf {v} _{1}+\cdots +a_{n}\mathbf {v} _{n}=\mathbf {0} .$

If such a linear dependence exists with at least a nonzero component, then the n vectors are linearly dependent. Linear dependencies among **v**<sub>1</sub>, ..., **v**<sub>*n*</sub> form a vector space.

If the vectors are expressed by their coordinates, then the linear dependencies are the solutions of a homogeneous [system of linear equations](https://en.wikipedia.org/wiki/System_of_linear_equations), with the coordinates of the vectors as coefficients. A [basis](https://en.wikipedia.org/wiki/Basis_(linear_algebra) "Basis (linear algebra)") of the vector space of linear dependencies can therefore be computed by [Gaussian elimination](https://en.wikipedia.org/wiki/Gaussian_elimination).

## Generalizations

### Affine independence

A set of vectors is said to be **affinely dependent** if at least one of the vectors in the set can be defined as an [affine combination](https://en.wikipedia.org/wiki/Affine_combination) of the others. Otherwise, the set is called **affinely independent**. Any affine combination is a linear combination; therefore every affinely dependent set is linearly dependent. Contrapositively, every linearly independent set is affinely independent. Note that an affinely independent set is not necessarily linearly independent.

Consider a set of $m$ vectors $\mathbf {v} _{1},\ldots ,\mathbf {v} _{m}$ of size $n$ each, and consider the set of $m$ augmented vectors $\left(\left[{\begin{smallmatrix}1\\\mathbf {v} _{1}\end{smallmatrix}}\right],\ldots ,\left[{\begin{smallmatrix}1\\\mathbf {v} _{m}\end{smallmatrix}}\right]\right)$ of size $n+1$ each. The original vectors are affinely independent if and only if the augmented vectors are linearly independent.

### Linearly independent vector subspaces

Two vector subspaces $M$ and $N$ of a vector space $X$ are said to be *linearly independent* if $M\cap N=\{0\}.$ More generally, a collection $M_{1},\ldots ,M_{d}$ of subspaces of $X$ are said to be *linearly independent* if $M_{i}\cap \sum _{k\neq i}M_{k}=\{0\}$ for every index $i,$ where $\sum _{k\neq i}M_{k}={\Big \{}m_{1}+\cdots +m_{i-1}+m_{i+1}+\cdots +m_{d}:m_{k}\in M_{k}{\text{ for all }}k{\Big \}}=\operatorname {span} \bigcup _{k\in \{1,\ldots ,i-1,i+1,\ldots ,d\}}M_{k}.$ The vector space $X$ is said to be a *[direct sum](https://en.wikipedia.org/wiki/Direct_sum)* of $M_{1},\ldots ,M_{d}$ if these subspaces are linearly independent and $M_{1}+\cdots +M_{d}=X.$

## See also

- [Matroid](https://en.wikipedia.org/wiki/Matroid) – Abstraction of linear independence of vectors

## References

1.  [G. E. Shilov](https://en.wikipedia.org/wiki/Georgiy_Shilov), *[Linear Algebra](https://books.google.com/books?id=5U6loPxlvQkC&q=dependent+OR+independent+OR+dependence+OR+independence)* (Trans. R. A. Silverman), Dover Publications, New York, 1977.
2.  Friedberg, Stephen; Insel, Arnold; Spence, Lawrence (2003). *Linear Algebra*. Pearson, 4th Edition. pp. 48–49. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0130084514](https://en.wikipedia.org/wiki/Special:BookSources/0130084514).
3.  [Lovász, László](https://en.wikipedia.org/wiki/L%C3%A1szl%C3%B3_Lov%C3%A1sz); [Plummer, M. D.](https://en.wikipedia.org/wiki/Michael_D._Plummer) (1986), *Matching Theory*, Annals of Discrete Mathematics, vol. 29, North-Holland, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-444-87916-1](https://en.wikipedia.org/wiki/Special:BookSources/0-444-87916-1), [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0859549](https://mathscinet.ams.org/mathscinet-getitem?mr=0859549)
4.  ^   Bachman, George; Narici, Lawrence (2000). *Functional Analysis* (Second ed.). Mineola, New York: Dover Publications. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0486402512](https://en.wikipedia.org/wiki/Special:BookSources/978-0486402512). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [829157984](https://search.worldcat.org/oclc/829157984). pp. 3–7

## External links

- ["Linear independence"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society), 2001 \[1994\]
- [Linearly Dependent Functions](http://mathworld.wolfram.com/LinearlyDependentFunctions.html) at WolframMathWorld.
- [Tutorial and interactive program](http://people.revoledu.com/kardi/tutorial/LinearAlgebra/LinearlyIndependent.html) on Linear Independence.
- [Introduction to Linear Independence](https://www.khanacademy.org/math/linear-algebra/vectors_and_spaces/linear_independence/v/linear-algebra-introduction-to-linear-independence) at KhanAcademy.
