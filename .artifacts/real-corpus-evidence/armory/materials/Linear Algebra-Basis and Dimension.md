[[linear-algebra.base]]

> Source: [Dimension (vector space)](https://en.wikipedia.org/wiki/Dimension_(vector_space))
> License: Wikipedia content is available under CC BY-SA 4.0.

![[media/151e04d5ee7fff618055a3b283f288d58ffd3b64.png]]
A diagram of dimensions 1, 2, 3, and 4

In [mathematics](https://en.wikipedia.org/wiki/Mathematics), the **dimension** of a [[Vector Space]] *V* is the [cardinality](https://en.wikipedia.org/wiki/Cardinality) (i.e., the number of vectors) of a [basis](https://en.wikipedia.org/wiki/Basis_(linear_algebra) "Basis (linear algebra)") of *V* over its base [field](https://en.wikipedia.org/wiki/Field_(mathematics) "Field (mathematics)"). It is sometimes called **Hamel dimension** (after [Georg Hamel](https://en.wikipedia.org/wiki/Georg_Hamel)) or **algebraic dimension** to distinguish it from other types of [dimension](https://en.wikipedia.org/wiki/Dimension).

For every vector space there exists a basis, and all bases of a vector space have equal cardinality; as a result, the dimension of a vector space is uniquely defined. We say $V$ is finite-dimensional if the dimension of $V$ is [finite](https://en.wiktionary.org/wiki/finite), and **infinite-dimensional** if its dimension is [infinite](https://en.wikipedia.org/wiki/Infinity).

The dimension of the vector space $V$ over the field $F$ can be written as $\dim _{F}(V)$ or as $[V:F],$ read "dimension of $V$ over $F$". When $F$ can be inferred from context, $\dim(V)$ is typically written.

## Examples

The vector space $\mathbb {R} ^{3}$ has 

$$
\left\{{\begin{pmatrix}1\\0\\0\end{pmatrix}},{\begin{pmatrix}0\\1\\0\end{pmatrix}},{\begin{pmatrix}0\\0\\1\end{pmatrix}}\right\}
$$

 as a [standard basis](https://en.wikipedia.org/wiki/Standard_basis), and therefore $\dim _{\mathbb {R} }(\mathbb {R} ^{3})=3.$ More generally, $\dim _{\mathbb {R} }(\mathbb {R} ^{n})=n,$ and even more generally, $\dim _{F}(F^{n})=n$ for any [field](https://en.wikipedia.org/wiki/Field_(mathematics) "Field (mathematics)") $F.$

The [complex numbers](https://en.wikipedia.org/wiki/Complex_number) $\mathbb {C}$ are both a real and complex vector space; we have $\dim _{\mathbb {R} }(\mathbb {C} )=2$ and $\dim _{\mathbb {C} }(\mathbb {C} )=1.$ So the dimension depends on the base field.

The only vector space with dimension $0$ is $\{0\},$ the vector space consisting only of its zero element.

## Properties

If $W$ is a [linear subspace](https://en.wikipedia.org/wiki/Linear_subspace) of $V$ then $\dim(W)\leq \dim(V).$

To show that two finite-dimensional vector spaces are equal, the following criterion can be used: if $V$ is a finite-dimensional vector space and $W$ is a linear subspace of $V$ with $\dim(W)=\dim(V),$ then $W=V.$

The space $\mathbb {R} ^{n}$ has the standard basis $\left\{e_{1},\ldots ,e_{n}\right\},$ where $e_{i}$ is the $i$-th column of the corresponding [identity matrix](https://en.wikipedia.org/wiki/Identity_matrix). Therefore, $\mathbb {R} ^{n}$ has dimension $n.$

Any two finite dimensional vector spaces over $F$ with the same dimension are [isomorphic](https://en.wikipedia.org/wiki/Isomorphic). Any [bijective](https://en.wikipedia.org/wiki/Bijective) map between their bases can be uniquely extended to a bijective linear map between the vector spaces. If $B$ is some set, a vector space with dimension $|B|$ over $F$ can be constructed as follows: take the set $F(B)$ of all functions $f:B\to F$ such that $f(b)=0$ for all but finitely many $b$ in $B.$ These functions can be added and multiplied with elements of $F$ to obtain the desired $F$-vector space.

An important result about dimensions is given by the [rank–nullity theorem](https://en.wikipedia.org/wiki/Rank%E2%80%93nullity_theorem) for [linear maps](https://en.wikipedia.org/wiki/Linear_map).

If $F/K$ is a [field extension](https://en.wikipedia.org/wiki/Field_extension), then $F$ is in particular a vector space over $K.$ Furthermore, every $F$-vector space $V$ is also a $K$-vector space. The dimensions are related by the formula 

$$
\dim _{K}(V)=\dim _{K}(F)\dim _{F}(V).
$$

 In particular, every complex vector space of dimension $n$ is a real vector space of dimension $2n.$

Some formulae relate the dimension of a vector space with the [cardinality](https://en.wikipedia.org/wiki/Cardinality) of the base field and the cardinality of the space itself. If $V$ is a vector space over a field $F$ and if the dimension of $V$ is denoted by $\dim V,$ then:

If dim $V$ is finite then $|V|=|F|^{\dim V}.$

If dim $V$ is infinite then $|V|=\max(|F|,\dim V).$

## Generalizations

A vector space can be seen as a particular case of a [matroid](https://en.wikipedia.org/wiki/Matroid), and in the latter there is a well-defined notion of dimension. The [length of a module](https://en.wikipedia.org/wiki/Length_of_a_module) and the [rank of an abelian group](https://en.wikipedia.org/wiki/Rank_of_an_abelian_group) both have several properties similar to the dimension of vector spaces.

The [Krull dimension](https://en.wikipedia.org/wiki/Krull_dimension) of a commutative [ring](https://en.wikipedia.org/wiki/Ring_(algebra)), named after [Wolfgang Krull](https://en.wikipedia.org/wiki/Wolfgang_Krull) (1899–1971), is defined to be the maximal number of strict inclusions in an increasing chain of [prime ideals](https://en.wikipedia.org/wiki/Prime_ideal) in the ring.

### Trace

The dimension of a vector space may alternatively be characterized as the [trace](https://en.wikipedia.org/wiki/Trace_(linear_algebra) "Trace (linear algebra)") of the [identity operator](https://en.wikipedia.org/wiki/Identity_operator). For instance, $\operatorname {tr} \ \operatorname {id} _{\mathbb {R} ^{2}}=\operatorname {tr} \left({\begin{smallmatrix}1&0\\0&1\end{smallmatrix}}\right)=1+1=2.$ This appears to be a [circular definition](https://en.wikipedia.org/wiki/Circular_definition), but it allows useful generalizations.

Firstly, it allows for a definition of a notion of dimension when one has a trace but no natural sense of basis. For example, one may have an [algebra](https://en.wikipedia.org/wiki/Algebra_over_a_field) $A$ with maps $\eta :K\to A$ (the inclusion of scalars, called the *unit*) and a map $\epsilon :A\to K$ (corresponding to trace, called the *[counit](https://en.wikipedia.org/wiki/Counit)*). The composition $\epsilon \circ \eta :K\to K$ is a scalar (being a linear operator on a 1-dimensional space) corresponds to "trace of identity", and gives a notion of dimension for an abstract algebra. In practice, in [bialgebras](https://en.wikipedia.org/wiki/Bialgebra), this map is required to be the identity, which can be obtained by normalizing the counit by dividing by dimension ($\epsilon :=\textstyle {\frac {1}{n}}\operatorname {tr}$), so in these cases the normalizing constant corresponds to dimension.

Alternatively, it may be possible to take the trace of operators on an infinite-dimensional space; in this case a (finite) trace is defined, even though no (finite) dimension exists, and gives a notion of "dimension of the operator". These fall under the rubric of "[trace class](https://en.wikipedia.org/wiki/Trace_class) operators" on a [Hilbert space](https://en.wikipedia.org/wiki/Hilbert_space), or more generally [nuclear operators](https://en.wikipedia.org/wiki/Nuclear_operator) on a [Banach space](https://en.wikipedia.org/wiki/Banach_space).

A subtler generalization is to consider the trace of a *family* of operators as a kind of "twisted" dimension. This occurs significantly in [representation theory](https://en.wikipedia.org/wiki/Representation_theory), where the [character](https://en.wikipedia.org/wiki/Character_(mathematics) "Character (mathematics)") of a representation is the trace of the representation, hence a scalar-valued function on a [group](https://en.wikipedia.org/wiki/Group_(mathematics) "Group (mathematics)") $\chi :G\to K,$ whose value on the identity $1\in G$ is the dimension of the representation, as a representation sends the identity in the group to the identity matrix: $\chi (1_{G})=\operatorname {tr} \ I_{V}=\dim V.$ The other values $\chi (g)$ of the character can be viewed as "twisted" dimensions, and find analogs or generalizations of statements about dimensions to statements about characters or representations. A sophisticated example of this occurs in the theory of [monstrous moonshine](https://en.wikipedia.org/wiki/Monstrous_moonshine): the [$j$-invariant](https://en.wikipedia.org/wiki/J-invariant) is the [graded dimension](https://en.wikipedia.org/wiki/Graded_dimension) of an infinite-dimensional graded representation of the [monster group](https://en.wikipedia.org/wiki/Monster_group), and replacing the dimension with the character gives the [McKay–Thompson series](https://en.wikipedia.org/wiki/McKay%E2%80%93Thompson_series) for each element of the Monster group.

## See also

- [Fractal dimension](https://en.wikipedia.org/wiki/Fractal_dimension) – Ratio providing a statistical index of complexity variation with scale
- [Krull dimension](https://en.wikipedia.org/wiki/Krull_dimension) – In mathematics, dimension of a ring
- [Matroid rank](https://en.wikipedia.org/wiki/Matroid_rank) – Maximum size of an independent set of the matroid
- [Rank (linear algebra)](https://en.wikipedia.org/wiki/Rank_(linear_algebra) "Rank (linear algebra)") – Dimension of the column space of a matrix
- [Topological dimension](https://en.wikipedia.org/wiki/Topological_dimension) – Topologically invariant definition of the dimension of a spacePages displaying short descriptions of redirect targets, also called Lebesgue covering dimension

## Notes

1.  if one assumes the [axiom of choice](https://en.wikipedia.org/wiki/Axiom_of_choice)
2.  see [dimension theorem for vector spaces](https://en.wikipedia.org/wiki/Dimension_theorem_for_vector_spaces)

## References

1.  Itzkov, Mikhail (2009). [Tensor Algebra and Tensor Analysis for Engineers: With Applications to Continuum Mechanics](https://books.google.com/books?id=8FVk_KRY7zwC&pg=PA4). Springer. p. 4. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-93906-1](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-93906-1).
2.  p. 44, §2.36
3.  Gannon, Terry (2006), *Moonshine beyond the Monster: The Bridge Connecting Algebra, Modular Forms and Physics*, Cambridge University Press, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-83531-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-83531-2)

## Sources

- [Axler, Sheldon](https://en.wikipedia.org/wiki/Sheldon_Axler) (2015). *Linear Algebra Done Right*. [Undergraduate Texts in Mathematics](https://en.wikipedia.org/wiki/Undergraduate_Texts_in_Mathematics) (3rd ed.). [Springer](https://en.wikipedia.org/wiki/Springer_Science%2BBusiness_Media). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-319-11079-0](https://en.wikipedia.org/wiki/Special:BookSources/978-3-319-11079-0).

## External links

- [MIT Linear Algebra Lecture on Independence, Basis, and Dimension by Gilbert Strang](http://ocw.mit.edu/courses/mathematics/18-06-linear-algebra-spring-2010/video-lectures/lecture-9-independence-basis-and-dimension/) at MIT OpenCourseWare
