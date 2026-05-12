[[linear-algebra.base]]

> Source: [Rank–nullity theorem](https://en.wikipedia.org/wiki/Rank%E2%80%93nullity_theorem)
> License: Wikipedia content is available under CC BY-SA 4.0.

![[media/7d538a90a8889cc86b96f1fa2457528886c0a90c.png]]
Rank–nullity theorem

The **rank–nullity theorem** is a theorem in [linear algebra](https://en.wikipedia.org/wiki/Linear_algebra), which asserts:

- the number of columns of a matrix *M* is the sum of the [rank](https://en.wikipedia.org/wiki/Rank_(linear_algebra) "Rank (linear algebra)") of *M* and the [nullity](https://en.wikipedia.org/wiki/Nullity_(linear_algebra)) of *M*; and
- the [dimension](https://en.wikipedia.org/wiki/Dimension_(linear_algebra)) of the [domain](https://en.wikipedia.org/wiki/Domain_of_a_function) of a [[Linear Transformation]] f is the sum of the [rank](https://en.wikipedia.org/wiki/Rank_(linear_algebra) "Rank (linear algebra)") of f (the dimension of the [image](https://en.wikipedia.org/wiki/Image_(mathematics) "Image (mathematics)") of f) and the nullity of f (the dimension of the [kernel](https://en.wikipedia.org/wiki/Kernel_(linear_algebra) "Kernel (linear algebra)") of f).

It follows that for linear transformations of [[Vector Space|vector spaces]] of equal finite dimension, either [injectivity](https://en.wikipedia.org/wiki/Injectivity) or [surjectivity](https://en.wikipedia.org/wiki/Surjectivity) implies [bijectivity](https://en.wikipedia.org/wiki/Bijectivity).

## Stating the theorem

### Linear transformations

Let $T:V\to W$ be a linear transformation between two vector spaces where $T$'s domain $V$ is finite dimensional. Then 

$$
\operatorname {rank} (T)~+~\operatorname {nullity} (T)~=~\dim V,
$$

 where $\operatorname {rank} (T)$ is the [rank](https://en.wikipedia.org/wiki/Rank_(linear_algebra) "Rank (linear algebra)") of $T$ (the [dimension](https://en.wikipedia.org/wiki/Dimension_(vector_space) "Dimension (vector space)") of its [image](https://en.wikipedia.org/wiki/Image_(mathematics) "Image (mathematics)")) and $\operatorname {nullity} (T)$ is the [nullity](https://en.wikipedia.org/wiki/Nullity_(linear_algebra)) of $T$ (the dimension of its [kernel](https://en.wikipedia.org/wiki/Kernel_(linear_algebra) "Kernel (linear algebra)")). In other words, 

$$
\dim(\operatorname {Im} T)+\dim(\operatorname {Ker} T)=\dim(\operatorname {Domain} (T)).
$$

 This theorem can be refined via the [splitting lemma](https://en.wikipedia.org/wiki/Splitting_lemma) to be a statement about an [isomorphism](https://en.wikipedia.org/wiki/Isomorphism) of spaces, not just dimensions. Explicitly, since $T$ induces an isomorphism from $V/\operatorname {Ker} (T)$ to $\operatorname {Im} (T),$ the existence of a basis for $V$ that extends any given basis of $\operatorname {Ker} (T)$ implies, via the splitting lemma, that $\operatorname {Im} (T)\oplus \operatorname {Ker} (T)\cong V.$ Taking dimensions, the rank–nullity theorem follows.

### Matrices

Linear maps can be represented with [matrices](https://en.wikipedia.org/wiki/Matrix_(mathematics) "Matrix (mathematics)"). More precisely, an $m\times n$ matrix M represents a linear map $f:F^{n}\to F^{m},$ where $F$ is the underlying [field](https://en.wikipedia.org/wiki/Field_(mathematics) "Field (mathematics)"). So, the dimension of the domain of $f$ is n, the number of columns of M, and the rank–nullity theorem for an $m\times n$ matrix M is 

$$
\operatorname {rank} (M)+\operatorname {nullity} (M)=n.
$$

## Proofs

Here we provide two proofs. The first operates in the general case, using linear maps. The second proof looks at the homogeneous system $\mathbf {Ax} =\mathbf {0} ,$ where $\mathbf {A}$ is a $m\times n$ with [rank](https://en.wikipedia.org/wiki/Rank_(linear_algebra) "Rank (linear algebra)") $r,$ and shows explicitly that there exists a set of $n-r$ [linearly independent](https://en.wikipedia.org/wiki/Linearly_independent) solutions that span the null space of $\mathbf {A}$.

While the theorem requires that the domain of the linear map be finite-dimensional, there is no such assumption on the [codomain](https://en.wikipedia.org/wiki/Codomain). This means that there are linear maps not given by matrices for which the theorem applies. Despite this, the first proof is not actually more general than the second: since the image of the linear map is finite-dimensional, we can represent the map from its domain to its image by a matrix, prove the theorem for that matrix, then compose with the inclusion of the image into the full codomain.

### First proof

Let $V,W$ be vector spaces over some field $F,$ and $T$ defined as in the statement of the theorem with $\dim V=n$.

As $\operatorname {Ker} T\subset V$ is a [subspace](https://en.wikipedia.org/wiki/Linear_subspace), there exists a basis for it. Suppose $\dim \operatorname {Ker} T=k$ and let 

$$
{\mathcal {K}}:=\{v_{1},\ldots ,v_{k}\}\subset \operatorname {Ker} (T)
$$

 be such a basis.

We may now, by the [Steinitz exchange lemma](https://en.wikipedia.org/wiki/Steinitz_exchange_lemma), extend ${\mathcal {K}}$ with $n-k$ linearly independent vectors $w_{1},\ldots ,w_{n-k}$ to form a full basis of $V$.

Let 

$$
{\mathcal {S}}:=\{w_{1},\ldots ,w_{n-k}\}\subset V\setminus \operatorname {Ker} (T)
$$

 such that 

$$
{\mathcal {B}}:={\mathcal {K}}\cup {\mathcal {S}}=\{v_{1},\ldots ,v_{k},w_{1},\ldots ,w_{n-k}\}\subset V
$$

 is a basis for $V$. From this, we know that 

$$
\operatorname {Im} T=\operatorname {Span} T({\mathcal {B}})=\operatorname {Span} \{T(v_{1}),\ldots ,T(v_{k}),T(w_{1}),\ldots ,T(w_{n-k})\}
$$

$=\operatorname {Span} \{T(w_{1}),\ldots ,T(w_{n-k})\}=\operatorname {Span} T({\mathcal {S}}).$

We now claim that $T({\mathcal {S}})$ is a basis for $\operatorname {Im} T$. The above equality already states that $T({\mathcal {S}})$ is a generating set for $\operatorname {Im} T$; it remains to be shown that it is also linearly independent to conclude that it is a basis.

Suppose $T({\mathcal {S}})$ is not linearly independent, and let 

$$
\sum _{j=1}^{n-k}\alpha _{j}T(w_{j})=0_{W}
$$

 for some $\alpha _{j}\in F$.

Thus, owing to the linearity of $T$, it follows that 

$$
T\left(\sum _{j=1}^{n-k}\alpha _{j}w_{j}\right)=0_{W}\implies \left(\sum _{j=1}^{n-k}\alpha _{j}w_{j}\right)\in \operatorname {Ker} T=\operatorname {Span} {\mathcal {K}}\subset V.
$$

 This is a contradiction to ${\mathcal {B}}$ being a basis, unless all $\alpha _{j}$ are equal to zero. This shows that $T({\mathcal {S}})$ is linearly independent, and more specifically that it is a basis for $\operatorname {Im} T$.

To summarize, we have ${\mathcal {K}}$, a basis for $\operatorname {Ker} T$, and $T({\mathcal {S}})$, a basis for $\operatorname {Im} T$.

Finally we may state that 

$$
\operatorname {Rank} (T)+\operatorname {Nullity} (T)=\dim \operatorname {Im} T+\dim \operatorname {Ker} T
$$

$=|T({\mathcal {S}})|+|{\mathcal {K}}|=(n-k)+k=n=\dim V.$

This concludes our proof.

### Second proof

Let $\mathbf {A}$ be an $m\times n$ matrix with $r$ [linearly independent](https://en.wikipedia.org/wiki/Linearly_independent) columns (i.e. $\operatorname {Rank} (\mathbf {A} )=r$). We will show that:

1.  There exists a set of $n-r$ linearly independent solutions to the homogeneous system $\mathbf {Ax} =\mathbf {0}$.
2.  That every other solution is a linear combination of these $n-r$ solutions.

To do this, we will produce an $n\times (n-r)$ matrix $\mathbf {X}$ whose columns form a [basis](https://en.wikipedia.org/wiki/Basis_(linear_algebra) "Basis (linear algebra)") of the null space of $\mathbf {A}$.

[Without loss of generality](https://en.wikipedia.org/wiki/Without_loss_of_generality), assume that the first $r$ columns of $\mathbf {A}$ are linearly independent. So, we can write 

$$
\mathbf {A} ={\begin{pmatrix}\mathbf {A} _{1}&\mathbf {A} _{2}\end{pmatrix}},
$$

 where

- $\mathbf {A} _{1}$ is an $m\times r$ matrix with $r$ linearly independent column vectors, and
- $\mathbf {A} _{2}$ is an $m\times (n-r)$ matrix such that each of its $n-r$ columns is linear combinations of the columns of $\mathbf {A} _{1}$.

This means that $\mathbf {A} _{2}=\mathbf {A} _{1}\mathbf {B}$ for some $r\times (n-r)$ matrix $\mathbf {B}$ (see [rank factorization](https://en.wikipedia.org/wiki/Rank_factorization)) and, hence, 

$$
\mathbf {A} ={\begin{pmatrix}\mathbf {A} _{1}&\mathbf {A} _{1}\mathbf {B} \end{pmatrix}}.
$$

Let 

$$
\mathbf {X} ={\begin{pmatrix}-\mathbf {B} \\\mathbf {I} _{n-r}\end{pmatrix}},
$$

 where $\mathbf {I} _{n-r}$ is the $(n-r)\times (n-r)$ [identity matrix](https://en.wikipedia.org/wiki/Identity_matrix). So, $\mathbf {X}$ is an $n\times (n-r)$ matrix such that 

$$
\mathbf {A} \mathbf {X} ={\begin{pmatrix}\mathbf {A} _{1}&\mathbf {A} _{1}\mathbf {B} \end{pmatrix}}{\begin{pmatrix}-\mathbf {B} \\\mathbf {I} _{n-r}\end{pmatrix}}=-\mathbf {A} _{1}\mathbf {B} +\mathbf {A} _{1}\mathbf {B} =\mathbf {0} _{m\times (n-r)}.
$$

Therefore, each of the $n-r$ columns of $\mathbf {X}$ are particular solutions of $\mathbf {Ax} ={0}_{{F}^{m}}$.

Furthermore, the $n-r$ columns of $\mathbf {X}$ are [linearly independent](https://en.wikipedia.org/wiki/Linearly_independent) because $\mathbf {Xu} =\mathbf {0} _{{F}^{n}}$ will imply $\mathbf {u} =\mathbf {0} _{{F}^{n-r}}$ for $\mathbf {u} \in {F}^{n-r}$: 

$$
\mathbf {X} \mathbf {u} =\mathbf {0} _{{F}^{n}}\implies {\begin{pmatrix}-\mathbf {B} \\\mathbf {I} _{n-r}\end{pmatrix}}\mathbf {u} =\mathbf {0} _{{F}^{n}}\implies {\begin{pmatrix}-\mathbf {B} \mathbf {u} \\\mathbf {u} \end{pmatrix}}={\begin{pmatrix}\mathbf {0} _{{F}^{r}}\\\mathbf {0} _{{F}^{n-r}}\end{pmatrix}}\implies \mathbf {u} =\mathbf {0} _{{F}^{n-r}}.
$$

 Therefore, the column vectors of $\mathbf {X}$ constitute a set of $n-r$ linearly independent solutions for $\mathbf {Ax} =\mathbf {0} _{\mathbb {F} ^{m}}$.

We next prove that *any* solution of $\mathbf {Ax} =\mathbf {0} _{{F}^{m}}$ must be a [linear combination](https://en.wikipedia.org/wiki/Linear_combination) of the columns of $\mathbf {X}$.

For this, let 

$$
\mathbf {u} ={\begin{pmatrix}\mathbf {u} _{1}\\\mathbf {u} _{2}\end{pmatrix}}\in {F}^{n}
$$

be any vector such that $\mathbf {Au} =\mathbf {0} _{{F}^{m}}$. Since the columns of $\mathbf {A} _{1}$ are linearly independent, $\mathbf {A} _{1}\mathbf {x} =\mathbf {0} _{{F}^{m}}$ implies $\mathbf {x} =\mathbf {0} _{{F}^{r}}$.

Therefore, 

$$
{\begin{array}{rcl}\mathbf {A} \mathbf {u} &=&\mathbf {0} _{{F}^{m}}\\\implies {\begin{pmatrix}\mathbf {A} _{1}&\mathbf {A} _{1}\mathbf {B} \end{pmatrix}}{\begin{pmatrix}\mathbf {u} _{1}\\\mathbf {u} _{2}\end{pmatrix}}&=&\mathbf {A} _{1}\mathbf {u} _{1}+\mathbf {A} _{1}\mathbf {B} \mathbf {u} _{2}&=&\mathbf {A} _{1}(\mathbf {u} _{1}+\mathbf {B} \mathbf {u} _{2})&=&\mathbf {0} _{\mathbb {F} ^{m}}\\\implies \mathbf {u} _{1}+\mathbf {B} \mathbf {u} _{2}&=&\mathbf {0} _{{F}^{r}}\\\implies \mathbf {u} _{1}&=&-\mathbf {B} \mathbf {u} _{2}\end{array}}
$$

$$
\implies \mathbf {u} ={\begin{pmatrix}\mathbf {u} _{1}\\\mathbf {u} _{2}\end{pmatrix}}={\begin{pmatrix}-\mathbf {B} \\\mathbf {I} _{n-r}\end{pmatrix}}\mathbf {u} _{2}=\mathbf {X} \mathbf {u} _{2}.
$$

This proves that any vector $\mathbf {u}$ that is a solution of $\mathbf {Ax} =\mathbf {0}$ must be a linear combination of the $n-r$ special solutions given by the columns of $\mathbf {X}$. And we have already seen that the columns of $\mathbf {X}$ are linearly independent. Hence, the columns of $\mathbf {X}$ constitute a basis for the [null space](https://en.wikipedia.org/wiki/Null_space) of $\mathbf {A}$. Therefore, the [nullity](https://en.wikipedia.org/wiki/Kernel_(matrix)) of $\mathbf {A}$ is $n-r$. Since $r$ equals rank of $\mathbf {A}$, it follows that $\operatorname {Rank} (\mathbf {A} )+\operatorname {Nullity} (\mathbf {A} )=n$. This concludes our proof.

## A third fundamental subspace

When $T:V\to W$ is a linear transformation between two finite-dimensional subspaces, with $n=\dim(V)$ and $m=\dim(W)$ (so can be represented by an $m\times n$ matrix $M$), the rank–nullity theorem asserts that if $T$ has rank $r$, then $n-r$ is the dimension of the [null space](https://en.wikipedia.org/wiki/Null_space) of $M$, which represents the [kernel](https://en.wikipedia.org/wiki/Kernel_(linear_algebra) "Kernel (linear algebra)") of $T$. In some texts, a third fundamental subspace associated to $T$ is considered alongside its image and kernel: the [cokernel](https://en.wikipedia.org/wiki/Cokernel) of $T$ is the [quotient space](https://en.wikipedia.org/wiki/Quotient_space_(linear_algebra) "Quotient space (linear algebra)") $W/\operatorname {Im} (T)$, and its dimension is $m-r$. This dimension formula (which might also be rendered $\dim \operatorname {Im} (T)+\dim \operatorname {Coker} (T)=\dim(W)$) together with the rank–nullity theorem is sometimes called the *fundamental theorem of linear algebra*.

## Reformulations and generalizations

This theorem is a statement of the [first isomorphism theorem](https://en.wikipedia.org/wiki/First_isomorphism_theorem) of algebra for the case of vector spaces; it generalizes to the [splitting lemma](https://en.wikipedia.org/wiki/Splitting_lemma).

In more modern language, the theorem can also be phrased as saying that each short exact sequence of vector spaces splits. Explicitly, given that 

$$
0\rightarrow U\rightarrow V\mathbin {\overset {T}{\rightarrow }} R\rightarrow 0
$$

 is a [short exact sequence](https://en.wikipedia.org/wiki/Short_exact_sequence) of vector spaces, then $U\oplus R\cong V$, hence 

$$
\dim(U)+\dim(R)=\dim(V).
$$

 Here $R$ plays the role of $\operatorname {Im} T$ and $U$ is $\operatorname {Ker} T$, i.e. 

$$
0\rightarrow \ker T\mathbin {\hookrightarrow } V\mathbin {\overset {T}{\rightarrow }} \operatorname {im} T\rightarrow 0
$$

In the finite-dimensional case, this formulation is susceptible to a generalization: if 

$$
0\rightarrow V_{1}\rightarrow V_{2}\rightarrow \cdots \rightarrow V_{r}\rightarrow 0
$$

 is an [exact sequence](https://en.wikipedia.org/wiki/Exact_sequence) of finite-dimensional vector spaces, then 

$$
\sum _{i=1}^{r}(-1)^{i}\dim(V_{i})=0.
$$

 The rank–nullity theorem for finite-dimensional vector spaces may also be formulated in terms of the *index* of a linear map. The index of a linear map $T\in \operatorname {Hom} (V,W)$, where $V$ and $W$ are finite-dimensional, is defined by 

$$
\operatorname {index} T=\dim \operatorname {Ker} (T)-\dim \operatorname {Coker} T.
$$

Intuitively, $\dim \operatorname {Ker} T$ is the number of independent solutions $v$ of the equation $Tv=0$, and $\dim \operatorname {Coker} T$ is the number of independent restrictions that have to be put on $w$ to make $Tv=w$ solvable. The rank–nullity theorem for finite-dimensional vector spaces is equivalent to the statement 

$$
\operatorname {index} T=\dim V-\dim W.
$$

We see that we can easily read off the index of the linear map $T$ from the involved spaces, without any need to analyze $T$ in detail. This effect also occurs in a much deeper result: the [Atiyah–Singer index theorem](https://en.wikipedia.org/wiki/Atiyah%E2%80%93Singer_index_theorem) states that the index of certain differential operators can be read off the geometry of the involved spaces.

## Citations

1.  p. 63, §3.22
2.  ^    p. 70, §2.1, Theorem 2.3
3.  p. 52, §2.5.1
4.  p. 71, §4.3
5.  pp. 103-104, §2.4, Theorem 2.20
6.  Banerjee, Sudipto; Roy, Anindya (2014), *Linear Algebra and Matrix Analysis for Statistics*, Texts in Statistical Science (1st ed.), Chapman and Hall/CRC, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1420095388](https://en.wikipedia.org/wiki/Special:BookSources/978-1420095388)
7.  \* [Strang, Gilbert](https://en.wikipedia.org/wiki/Gilbert_Strang). *Linear Algebra and Its Applications*. 3rd ed. Orlando: Saunders, 1988.
8.  Strang, Gilbert (1993), ["The fundamental theorem of linear algebra"](http://www.dm.unibo.it/~regonati/ad0708/strang-FTLA.pdf) (PDF), *American Mathematical Monthly*, **100** (9): 848–855, [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.384.2309](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.384.2309), [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2324660](https://doi.org/10.2307%2F2324660), [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2324660](https://www.jstor.org/stable/2324660)
9.  Zaman, Ragib. ["Dimensions of vector spaces in an exact sequence"](https://math.stackexchange.com/q/255384). *Mathematics Stack Exchange*. Retrieved 27 October 2015.

## References

- [Axler, Sheldon](https://en.wikipedia.org/wiki/Sheldon_Axler) (2015). *Linear Algebra Done Right*. [Undergraduate Texts in Mathematics](https://en.wikipedia.org/wiki/Undergraduate_Texts_in_Mathematics) (3rd ed.). [Springer](https://en.wikipedia.org/wiki/Springer_Science%2BBusiness_Media). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-319-11079-0](https://en.wikipedia.org/wiki/Special:BookSources/978-3-319-11079-0).
- Banerjee, Sudipto; Roy, Anindya (2014), *Linear Algebra and Matrix Analysis for Statistics*, Texts in Statistical Science (1st ed.), Chapman and Hall/CRC, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1420095388](https://en.wikipedia.org/wiki/Special:BookSources/978-1420095388)
- Friedberg, Stephen H.; Insel, Arnold J.; Spence, Lawrence E. (2014). *Linear Algebra* (4th ed.). [Pearson Education](https://en.wikipedia.org/wiki/Pearson_Education). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0130084514](https://en.wikipedia.org/wiki/Special:BookSources/978-0130084514).
- Meyer, Carl D. (2000), [Matrix Analysis and Applied Linear Algebra](http://www.matrixanalysis.com/), [SIAM](https://en.wikipedia.org/wiki/Society_for_Industrial_and_Applied_Mathematics), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-89871-454-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-89871-454-8).
- [Katznelson, Yitzhak](https://en.wikipedia.org/wiki/Yitzhak_Katznelson); Katznelson, Yonatan R. (2008). *A (Terse) Introduction to Linear Algebra*. [American Mathematical Society](https://en.wikipedia.org/wiki/American_Mathematical_Society). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8218-4419-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8218-4419-9).
- Valenza, Robert J. (1993) \[1951\]. *Linear Algebra: An Introduction to Abstract Mathematics*. [Undergraduate Texts in Mathematics](https://en.wikipedia.org/wiki/Undergraduate_Texts_in_Mathematics) (3rd ed.). [Springer](https://en.wikipedia.org/wiki/Springer_Science%2BBusiness_Media). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [3-540-94099-5](https://en.wikipedia.org/wiki/Special:BookSources/3-540-94099-5).

## External links

- Gilbert Strang, [MIT Linear Algebra Lecture on the Four Fundamental Subspaces](https://ocw.mit.edu/courses/mathematics/18-06-linear-algebra-spring-2010/video-lectures/lecture-10-the-four-fundamental-subspaces/), from [MIT OpenCourseWare](https://en.wikipedia.org/wiki/MIT_OpenCourseWare)
