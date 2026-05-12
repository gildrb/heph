[[linear-algebra.base]]

> Source: [Linear map](https://en.wikipedia.org/wiki/Linear_map)
> License: Wikipedia content is available under CC BY-SA 4.0.

In [mathematics](https://en.wikipedia.org/wiki/Mathematics), and more specifically in [linear algebra](https://en.wikipedia.org/wiki/Linear_algebra), a **linear map** (or **linear mapping**) is a particular kind of [function](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)") between [[Vector Space|vector spaces]], which respects the basic operations of [vector addition](https://en.wikipedia.org/wiki/Vector_addition) and [scalar multiplication](https://en.wikipedia.org/wiki/Scalar_multiplication). A standard example of a linear map is an $m\times n$ matrix, which takes vectors in $n$-dimensions into vectors in $m$-dimensions in a way that is compatible with addition of vectors, and multiplication of vectors by [scalars](https://en.wikipedia.org/wiki/Scalar_(mathematics) "Scalar (mathematics)").

A linear map is a [homomorphism](https://en.wikipedia.org/wiki/Homomorphism) of vector spaces. Thus, a linear map $T:V\to W$ satisfies $T(ax+by)=aTx+bTy$, where $a$ and $b$ are scalars, and $x$ and $y$ are vectors (elements of the vector space $V$). A linear mapping always maps the [origin](https://en.wikipedia.org/wiki/Origin_(geometry)) of $V$ to the origin of $W$, and [linear subspaces](https://en.wikipedia.org/wiki/Linear_subspace) of $V$ onto linear subspaces in $W$ (possibly of a lower [dimension](https://en.wikipedia.org/wiki/Dimension_(vector_space) "Dimension (vector space)")); for example, it maps a [plane](https://en.wikipedia.org/wiki/Plane_(geometry)) through the origin in $V$ to either a plane through the origin in $W$, a [line](https://en.wikipedia.org/wiki/Line_(geometry) "Line (geometry)") through the origin in $W$, or just the origin in $W$. Linear maps can often be represented as [matrices](https://en.wikipedia.org/wiki/Matrix_(mathematics) "Matrix (mathematics)"), and simple examples include [rotation and reflection linear transformations](https://en.wikipedia.org/wiki/Rotations_and_reflections_in_two_dimensions).

## Definition and first consequences

Let $V$ and $W$ be vector spaces over the same [field](https://en.wikipedia.org/wiki/Field_(mathematics) "Field (mathematics)") $K$, such as the [real](https://en.wikipedia.org/wiki/Real_number) or [complex numbers](https://en.wikipedia.org/wiki/Complex_numbers). A [function](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)") $f:V\to W$ is said to be a *linear map* if for any two vectors $\mathbf {u} ,\mathbf {v} \in V$ and any scalar $c\in K$ the following two conditions are satisfied:

- [Additivity](https://en.wikipedia.org/wiki/Additive_map) / operation of addition 

$$
f(\mathbf {u} +\mathbf {v} )=f(\mathbf {u} )+f(\mathbf {v} )
$$

- [Homogeneity](https://en.wikipedia.org/wiki/Homogeneous_function) of degree 1 / operation of scalar multiplication 

$$
f(c\mathbf {u} )=cf(\mathbf {u} )
$$

Thus, a linear map is said to be *operation preserving*. In other words, it does not matter whether the linear map is applied before (the right sides of the above examples) or after (the left sides of the examples) the operations of addition and scalar multiplication.

By [the associativity of the addition operation](https://en.wikipedia.org/wiki/Addition#Associativity) denoted as +, for any vectors $\mathbf {u} _{1},\ldots ,\mathbf {u} _{n}\in V$ and scalars $c_{1},\ldots ,c_{n}\in K$, the following equality holds: 

$$
f(c_{1}\mathbf {u} _{1}+\cdots +c_{n}\mathbf {u} _{n})=c_{1}f(\mathbf {u} _{1})+\cdots +c_{n}f(\mathbf {u} _{n}).
$$

 Thus a linear map is one which preserves [linear combinations](https://en.wikipedia.org/wiki/Linear_combination).

Denoting the zero elements of the vector spaces $V$ and $W$ by $\mathbf {0} _{V}$ and $\mathbf {0} _{W}$ respectively, it follows that $f(\mathbf {0} _{V})=\mathbf {0} _{W}$. Let $c=0$ and $\mathbf {v} \in V$ in the equation for homogeneity of degree 1: 

$$
f(\mathbf {0} _{V})=f(0\mathbf {v} )=0f(\mathbf {v} )=\mathbf {0} _{W}.
$$

A linear map $V\to K$ with $K$ viewed as a one-dimensional vector space over itself is called a [linear functional](https://en.wikipedia.org/wiki/Linear_functional).

These statements generalize to any left-module ${}_{R}M$ over a ring $R$ without modification, and to any right-module upon reversing of the scalar multiplication.

## Examples

- The unique map of the form $T:\{{\vec {0}}\}\to \{{\vec {0}}\}$ is linear.
- A prototypical example that gives linear maps their name is a function $f:\mathbb {R} \to \mathbb {R} :x\mapsto cx$, of which the [graph](https://en.wikipedia.org/wiki/Graph_of_a_function) is a line through the origin.
  ![[media/454598c6eefd8463a5727b55a54492f1b89c6f3f.png]]
  Examples of linear transformations used in computer graphics
- More generally, any [homothety](https://en.wikipedia.org/wiki/Homothety) $\mathbf {v} \mapsto c\mathbf {v}$ centered in the origin of a vector space is a linear map (here c is a scalar).
- The zero map $\mathbf {x} \mapsto \mathbf {0}$ between two vector spaces (over the same [field](https://en.wikipedia.org/wiki/Field_(mathematics) "Field (mathematics)")) is linear.
- The [identity map](https://en.wikipedia.org/wiki/Identity_function) on any module is a linear operator.
- For real numbers, the map $x\mapsto x^{2}$ is not linear.
- For real numbers, the map $x\mapsto x+1$ is not linear (but is an [affine transformation](https://en.wikipedia.org/wiki/Affine_transformation)).
- If $A$ is a $m\times n$ [real matrix](https://en.wikipedia.org/wiki/Real_matrix), then $A$ defines a linear map from $\mathbb {R} ^{n}$ to $\mathbb {R} ^{m}$ by sending a [column vector](https://en.wikipedia.org/wiki/Column_vector) $\mathbf {x} \in \mathbb {R} ^{n}$ to the column vector $A\mathbf {x} \in \mathbb {R} ^{m}$. Conversely, any linear map between [finite-dimensional](https://en.wikipedia.org/wiki/Finite-dimensional) vector spaces can be represented in this manner; see *[§ Matrices](#Matrices)*, below.
- If $f:V\to W$ is an [isometry](https://en.wikipedia.org/wiki/Isometry) between real [normed spaces](https://en.wikipedia.org/wiki/Normed_space) such that $f(0)=0$ then $f$ is a linear map. This result is not necessarily true for complex normed space.
- [Differentiation](https://en.wikipedia.org/wiki/Derivative) defines a linear map from the space of all differentiable functions to the space of all functions. It also defines a [linear operator](https://en.wikipedia.org/wiki/Linear_operator) on the space of all [smooth functions](https://en.wikipedia.org/wiki/Smooth_function) (a linear operator is a [linear endomorphism](https://en.wikipedia.org/wiki/Linear_endomorphism), that is, a linear map with the same [domain](https://en.wikipedia.org/wiki/Domain_of_a_function) and [codomain](https://en.wikipedia.org/wiki/Codomain)). Indeed, 

$$
{\frac {d}{dx}}\left(af(x)+bg(x)\right)=a{\frac {df(x)}{dx}}+b{\frac {dg(x)}{dx}}.
$$

- A definite [integral](https://en.wikipedia.org/wiki/Integral) over some [interval](https://en.wikipedia.org/wiki/Interval_(mathematics) "Interval (mathematics)") I is a linear map from the space of all real-valued integrable functions on I to $\mathbb {R}$. Indeed, 

$$
\int _{u}^{v}\left(af(x)+bg(x)\right)dx=a\int _{u}^{v}f(x)dx+b\int _{u}^{v}g(x)dx.
$$

- An indefinite [integral](https://en.wikipedia.org/wiki/Integral) (or [antiderivative](https://en.wikipedia.org/wiki/Antiderivative)) with a fixed integration starting point defines a linear map from the space of all real-valued integrable functions on $\mathbb {R}$ to the space of all real-valued, differentiable functions on $\mathbb {R}$. Without a fixed starting point, the antiderivative maps to the [quotient space](https://en.wikipedia.org/wiki/Quotient_space_(linear_algebra) "Quotient space (linear algebra)") of the differentiable functions by the linear space of constant functions.
- If $V$ and $W$ are finite-dimensional vector spaces over a field F, of respective dimensions m and n, then the function that maps linear maps $f:V\to W$ to *n* × *m* matrices in the way described in *[§ Matrices](#Matrices)* (below) is a linear map, and even a [linear isomorphism](https://en.wikipedia.org/wiki/Linear_isomorphism).
- The [expected value](https://en.wikipedia.org/wiki/Expected_value) of a [random variable](https://en.wikipedia.org/wiki/Random_variable#Definition) is a linear function of the random variable: for random variables $X$ and $Y$ we have $E[X+Y]=E[X]+E[Y]$ and $E[aX]=aE[X]$. The [conditional expectation](https://en.wikipedia.org/wiki/Conditional_expectation) is as well. But the [variance](https://en.wikipedia.org/wiki/Variance) of a random variable is not linear, because for instance ${\text{Var}}(aX)=a^{2}{\text{Var}}(X)$.

- 

  ![[media/4896219092354f0bd0d0840f5d17abd6bc8618ac.gif]]

  The function $f:\mathbb {R} ^{2}\to \mathbb {R} ^{2}$ with $f(x,y)=(2x,y)$ is a linear map. This function scales the $x$ component of a vector by the factor $2$.

- 

  ![[media/db60f63f5010af29939e0b6e1a094f607b7b430c.gif]]

  The function $f(x,y)=(2x,y)$ is additive: It does not matter whether vectors are first added and then mapped or whether they are mapped and finally added: $f(\mathbf {a} +\mathbf {b} )=f(\mathbf {a} )+f(\mathbf {b} )$

- 

  ![[media/294c45e5118e2d8e447e11d33986f6df5d986f38.gif]]

  The function $f(x,y)=(2x,y)$ is homogeneous: It does not matter whether a vector is first scaled and then mapped or first mapped and then scaled: $f(\lambda \mathbf {a} )=\lambda f(\mathbf {a} )$

### Linear endomorphisms and isomorphisms

If a linear map is a [bijection](https://en.wikipedia.org/wiki/Bijection) then it is called a linear isomorphism. In the case where $V=W$, a linear map is called a **linear endomorphism**. Sometimes the term **linear operator** refers to this case, but the term "linear operator" can have different meanings for different conventions.

### Linear extensions

Often, a linear map is constructed by defining it on a subset of a vector space and then *extending by linearity* to the [linear span](https://en.wikipedia.org/wiki/Linear_span) of the domain. Suppose $X$ and $Y$ are vector spaces and $f:S\to Y$ is a [function](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)") defined on some subset $S\subseteq X$. Then a *linear extension of $f$ to $X,$* if it exists, is a linear map $F:X\to Y$ defined on $X$ that [extends](https://en.wikipedia.org/wiki/Extension_of_a_function) $f$ (meaning that $F(s)=f(s)$ for all $s\in S$) and takes its values from the codomain of $f$. When the subset $S$ is a vector subspace of $X$ then a ($Y$-valued) linear extension of $f$ to all of $X$ is guaranteed to exist if (and only if) $f:S\to Y$ is a linear map. In particular, if $f$ has a linear extension to $\operatorname {span} S,$ then it has a linear extension to all of $X$.

The map $f:S\to Y$ can be extended to a linear map $F:\operatorname {span} S\to Y$ if and only if whenever $n>0$ is an integer, $c_{1},\ldots ,c_{n}$ are scalars, and $s_{1},\ldots ,s_{n}\in S$ are vectors such that $0=c_{1}s_{1}+\cdots +c_{n}s_{n}$, then necessarily $0=c_{1}f\left(s_{1}\right)+\cdots +c_{n}f\left(s_{n}\right)$. If a linear extension of $f:S\to Y$ exists then the linear extension $F:\operatorname {span} S\to Y$ is unique and 

$$
F\left(c_{1}s_{1}+\cdots c_{n}s_{n}\right)=c_{1}f\left(s_{1}\right)+\cdots +c_{n}f\left(s_{n}\right)
$$

 holds for all $n,c_{1},\ldots ,c_{n}$, and $s_{1},\ldots ,s_{n}$ as above. If $S$ is linearly independent then every function $f:S\to Y$ into any vector space has a linear extension to a (linear) map $\operatorname {span} S\to Y$ (the converse is also true).

For example, if $X=\mathbb {R} ^{2}$ and $Y=\mathbb {R}$ then the assignment $(1,0)\to -1$ and $(0,1)\to 2$ can be linearly extended from the linearly independent set of vectors $S:=\{(1,0),(0,1)\}$ to a linear map on $\operatorname {span} \{(1,0),(0,1)\}=\mathbb {R} ^{2}$. The unique linear extension $F:\mathbb {R} ^{2}\to \mathbb {R}$ is the map that sends $(x,y)=x(1,0)+y(0,1)\in \mathbb {R} ^{2}$ to 

$$
F(x,y)=x(-1)+y(2)=-x+2y.
$$

Every (scalar-valued) [linear functional](https://en.wikipedia.org/wiki/Linear_functional) $f$ defined on a [vector subspace](https://en.wikipedia.org/wiki/Vector_subspace) of a real or complex vector space $X$ has a linear extension to all of $X$. Indeed, the [Hahn–Banach dominated extension theorem](https://en.wikipedia.org/wiki/Hahn%E2%80%93Banach_theorem) even guarantees that when this linear functional $f$ is dominated by some given [seminorm](https://en.wikipedia.org/wiki/Seminorm) $p:X\to \mathbb {R}$ (meaning that $|f(m)|\leq p(m)$ holds for all $m$ in the domain of $f$) then there exists a linear extension to $X$ that is also dominated by $p$.

## Matrices

If $V$ and $W$ are [finite-dimensional](https://en.wikipedia.org/wiki/Finite-dimensional) vector spaces and a [basis](https://en.wikipedia.org/wiki/Basis_of_a_vector_space) is defined for each vector space, then every linear map from $V$ to $W$ can be represented by a [matrix](https://en.wikipedia.org/wiki/Matrix_(mathematics) "Matrix (mathematics)"). This is useful because it allows concrete calculations. Matrices yield examples of linear maps: if $A$ is a real $m\times n$ matrix, then $f(\mathbf {x} )=A\mathbf {x}$ describes a linear map $\mathbb {R} ^{n}\to \mathbb {R} ^{m}$ (see [Euclidean space](https://en.wikipedia.org/wiki/Euclidean_space)).

Let $\{\mathbf {v} _{1},\ldots ,\mathbf {v} _{n}\}$ be a basis for $V$. Then every vector $\mathbf {v} \in V$ is uniquely determined by the coefficients $c_{1},\ldots ,c_{n}$ in the field $\mathbb {R}$: 

$$
\mathbf {v} =c_{1}\mathbf {v} _{1}+\cdots +c_{n}\mathbf {v} _{n}.
$$

If $f:V\to W$ is a linear map, 

$$
f(\mathbf {v} )=f(c_{1}\mathbf {v} _{1}+\cdots +c_{n}\mathbf {v} _{n})=c_{1}f(\mathbf {v} _{1})+\cdots +c_{n}f\left(\mathbf {v} _{n}\right),
$$

which implies that the function *f* is entirely determined by the vectors $f(\mathbf {v} _{1}),\ldots ,f(\mathbf {v} _{n})$. Now let $\{\mathbf {w} _{1},\ldots ,\mathbf {w} _{m}\}$ be a basis for $W$. Then we can represent each vector $f(\mathbf {v} _{j})$ as 

$$
f\left(\mathbf {v} _{j}\right)=a_{1j}\mathbf {w} _{1}+\cdots +a_{mj}\mathbf {w} _{m}.
$$

Thus, the function $f$ is entirely determined by the values of $a_{ij}$. If we put these values into an $m\times n$ matrix $M$, then we can conveniently use it to compute the vector output of $f$ for any vector in $V$. To get $M$, every column $j$ of $M$ is a vector 

$$
{\begin{pmatrix}a_{1j}\\\vdots \\a_{mj}\end{pmatrix}}
$$

 corresponding to $f(\mathbf {v} _{j})$ as defined above. To define it more clearly, for some column $j$ that corresponds to the mapping $f(\mathbf {v} _{j})$, 

$$
\mathbf {M} ={\begin{pmatrix}\ \cdots &a_{1j}&\cdots \ \\&\vdots &\\&a_{mj}&\end{pmatrix}}
$$

 where $M$ is the matrix of $f$. In other words, every column $j=1,\ldots ,n$ has a corresponding vector $f(\mathbf {v} _{j})$ whose coordinates $a_{1j},\cdots ,a_{mj}$ are the elements of column $j$. A single linear map may be represented by many matrices. This is because the values of the elements of a matrix depend on the bases chosen.

The matrices of a linear transformation can be represented visually:

1.  Matrix for $T$ relative to $B$: $A$
2.  Matrix for $T$ relative to $B'$: $A'$
3.  Transition matrix from $B'$ to $B$: $P$
4.  Transition matrix from $B$ to $B'$: $P^{-1}$

![[media/2d334e24f82deba090d2140f1c3d58db484bca9f.png]]
The relationship between matrices in a linear transformation

Such that starting in the bottom left corner $\left[\mathbf {v} \right]_{B'}$ and looking for the bottom right corner $\left[T\left(\mathbf {v} \right)\right]_{B'}$, one would left-multiply—that is, $A'\left[\mathbf {v} \right]_{B'}=\left[T\left(\mathbf {v} \right)\right]_{B'}$. The equivalent method would be the "longer" method going clockwise from the same point such that $\left[\mathbf {v} \right]_{B'}$ is left-multiplied with $P^{-1}AP$, or $P^{-1}AP\left[\mathbf {v} \right]_{B'}=\left[T\left(\mathbf {v} \right)\right]_{B'}$.

### Examples in two dimensions

In two-[dimensional](https://en.wikipedia.org/wiki/Dimension) space **R**<sup>2</sup> linear maps are described by 2 × 2 [matrices](https://en.wikipedia.org/wiki/Matrix_(mathematics) "Matrix (mathematics)"). These are some examples:

- [rotation](https://en.wikipedia.org/wiki/Rotation_(mathematics) "Rotation (mathematics)")
  - by 90 degrees counterclockwise: 

$$
\mathbf {A} ={\begin{pmatrix}0&-1\\1&0\end{pmatrix}}
$$

  - by an angle *θ* counterclockwise: 

$$
\mathbf {A} ={\begin{pmatrix}\cos \theta &-\sin \theta \\\sin \theta &\cos \theta \end{pmatrix}}
$$

- [reflection](https://en.wikipedia.org/wiki/Reflection_(mathematics) "Reflection (mathematics)")
  - through the *x* axis: 

$$
\mathbf {A} ={\begin{pmatrix}1&0\\0&-1\end{pmatrix}}
$$

  - through the *y* axis: 

$$
\mathbf {A} ={\begin{pmatrix}-1&0\\0&1\end{pmatrix}}
$$

  - through a line making an angle *θ* with the origin: 

$$
\mathbf {A} ={\begin{pmatrix}\cos 2\theta &\sin 2\theta \\\sin 2\theta &-\cos 2\theta \end{pmatrix}}
$$

- [scaling](https://en.wikipedia.org/wiki/Scaling_(geometry) "Scaling (geometry)") by 2 in all directions: 

$$
\mathbf {A} ={\begin{pmatrix}2&0\\0&2\end{pmatrix}}=2\mathbf {I}
$$

- [horizontal shear mapping](https://en.wikipedia.org/wiki/Shear_mapping): 

$$
\mathbf {A} ={\begin{pmatrix}1&m\\0&1\end{pmatrix}}
$$

- skew of the *y* axis by an angle *θ*: 

$$
\mathbf {A} ={\begin{pmatrix}1&-\sin \theta \\0&\cos \theta \end{pmatrix}}
$$

- [squeeze mapping](https://en.wikipedia.org/wiki/Squeeze_mapping): 

$$
\mathbf {A} ={\begin{pmatrix}k&0\\0&{\frac {1}{k}}\end{pmatrix}}
$$

- [projection](https://en.wikipedia.org/wiki/Projection_(linear_algebra) "Projection (linear algebra)") onto the *y* axis: 

$$
\mathbf {A} ={\begin{pmatrix}0&0\\0&1\end{pmatrix}}.
$$

If a linear map is only composed of rotation, reflection, and/or uniform scaling, then the linear map is a [conformal linear transformation](https://en.wikipedia.org/wiki/Conformal_linear_transformation).

## Vector space of linear maps

The composition of linear maps is linear: if $f:V\to W$ and $g:W\to Z$ are linear, then so is their [composition](https://en.wikipedia.org/wiki/Relation_composition) $g\circ f:V\to Z$. It follows from this that the [class](https://en.wikipedia.org/wiki/Class_(set_theory) "Class (set theory)") of all vector spaces over a given field *K*, together with *K*-linear maps as [morphisms](https://en.wikipedia.org/wiki/Morphism), forms a [category](https://en.wikipedia.org/wiki/Category_(mathematics) "Category (mathematics)").

The [inverse](https://en.wikipedia.org/wiki/Inverse_function) of a linear map, when defined, is again a linear map.

If $f_{1}:V\to W$ and $f_{2}:V\to W$ are linear, then so is their [pointwise](https://en.wikipedia.org/wiki/Pointwise) sum $f_{1}+f_{2}$, which is defined by $(f_{1}+f_{2})(\mathbf {x} )=f_{1}(\mathbf {x} )+f_{2}(\mathbf {x} )$.

If $f:V\to W$ is linear and $\alpha$ is an element of the ground field $K$, then the map $\alpha f$, defined by $(\alpha f)(\mathbf {x} )=\alpha (f(\mathbf {x} ))$, is also linear.

Thus the set ${\mathcal {L}}(V,W)$ of linear maps from $V$ to $W$ itself forms a vector space over $K$, sometimes denoted $\operatorname {Hom} (V,W)$. Furthermore, in the case that $V=W$, this vector space, denoted $\operatorname {End} (V)$, is an [associative algebra](https://en.wikipedia.org/wiki/Associative_algebra) under [composition of maps](https://en.wikipedia.org/wiki/Composition_of_maps), since the composition of two linear maps is again a linear map, and the composition of maps is always associative. This case is discussed in more detail below.

Given again the finite-dimensional case, if bases have been chosen, then the composition of linear maps corresponds to the [[Matrix Multiplication]], the addition of linear maps corresponds to the [matrix addition](https://en.wikipedia.org/wiki/Matrix_addition), and the multiplication of linear maps with scalars corresponds to the multiplication of matrices with scalars.

### Endomorphisms and automorphisms

A linear transformation $f:V\to V$ is an [endomorphism](https://en.wikipedia.org/wiki/Endomorphism) of $V$; the set of all such endomorphisms $\operatorname {End} (V)$ together with addition, composition and scalar multiplication as defined above forms an [associative algebra](https://en.wikipedia.org/wiki/Associative_algebra) with identity element over the field $K$ (and in particular a [ring](https://en.wikipedia.org/wiki/Ring_(algebra))). The multiplicative identity element of this algebra is the [identity map](https://en.wikipedia.org/wiki/Identity_function) $\operatorname {id} :V\to V$.

An endomorphism of $V$ that is also an [isomorphism](https://en.wikipedia.org/wiki/Isomorphism) is called an [automorphism](https://en.wikipedia.org/wiki/Automorphism) of $V$. The composition of two automorphisms is again an automorphism, and the set of all automorphisms of $V$ forms a [group](https://en.wikipedia.org/wiki/Group_(math)), the [automorphism group](https://en.wikipedia.org/wiki/Automorphism_group) of $V$ which is denoted by $\operatorname {Aut} (V)$ or $\operatorname {GL} (V)$. Since the automorphisms are precisely those [endomorphisms](https://en.wikipedia.org/wiki/Endomorphisms) which possess inverses under composition, $\operatorname {Aut} (V)$ is the group of [units](https://en.wikipedia.org/wiki/Unit_(ring_theory) "Unit (ring theory)") in the ring $\operatorname {End} (V)$.

If $V$ has finite dimension $n$, then $\operatorname {End} (V)$ is [isomorphic](https://en.wikipedia.org/wiki/Isomorphism) to the [associative algebra](https://en.wikipedia.org/wiki/Associative_algebra) of all $n\times n$ matrices with entries in $K$. The automorphism group of $V$ is [isomorphic](https://en.wikipedia.org/wiki/Group_isomorphism) to the [general linear group](https://en.wikipedia.org/wiki/General_linear_group) $\operatorname {GL} (n,K)$ of all $n\times n$ invertible matrices with entries in $K$.

## Kernel, image and the rank–nullity theorem

If $f:V\to W$ is linear, we define the [kernel](https://en.wikipedia.org/wiki/Kernel_(linear_operator)) and the [image](https://en.wikipedia.org/wiki/Image_(mathematics) "Image (mathematics)") or [range](https://en.wikipedia.org/wiki/Range_of_a_function) of $f$ by 

$$
{\begin{aligned}\ker(f)&=\{\,\mathbf {x} \in V:f(\mathbf {x} )=\mathbf {0} \,\}\\\operatorname {im} (f)&=\{\,\mathbf {w} \in W:\mathbf {w} =f(\mathbf {x} ),\mathbf {x} \in V\,\}\end{aligned}}
$$

$\ker(f)$ is a [subspace](https://en.wikipedia.org/wiki/Linear_subspace) of $V$ and $\operatorname {im} (f)$ is a subspace of $W$. The following [dimension](https://en.wikipedia.org/wiki/Dimension) formula is known as the [rank–nullity theorem](https://en.wikipedia.org/wiki/Rank%E2%80%93nullity_theorem): 

$$
\dim(\ker(f))+\dim(\operatorname {im} (f))=\dim(V).
$$

The number $\dim(\operatorname {im} (f))$ is also called the [rank](https://en.wikipedia.org/wiki/Rank_of_a_matrix) of $f$ and written as $\operatorname {rank} (f)$, or sometimes, $\rho (f)$; the number $\dim(\ker(f))$ is called the [nullity](https://en.wikipedia.org/wiki/Kernel_(matrix)#Subspace_properties) of $f$ and written as $\operatorname {null} (f)$ or $\nu (f)$. If $V$ and $W$ are finite-dimensional, bases have been chosen and $f$ is represented by the matrix $A$, then the rank and nullity of $f$ are equal to the rank and nullity of the matrix $A$, respectively.

## Cokernel

A subtler invariant of a linear transformation $f:V\to W$ is the [*co*kernel](https://en.wikipedia.org/wiki/Cokernel), which is defined as 

$$
\operatorname {coker} (f):=W/f(V)=W/\operatorname {im} (f).
$$

This is the *dual* notion to the kernel: just as the kernel is a *sub*space of the *domain,* the co-kernel is a [*quotient* space](https://en.wikipedia.org/wiki/Quotient_space_(linear_algebra) "Quotient space (linear algebra)") of the *target.* Formally, one has the [exact sequence](https://en.wikipedia.org/wiki/Exact_sequence) 

$$
0\to \ker(f)\to V\to W\to \operatorname {coker} (f)\to 0.
$$

These can be interpreted thus: given a linear equation *f*(**v**) = **w** to solve,

- the kernel is the space of *solutions* to the *homogeneous* equation *f*(**v**) = 0, and its dimension is the number of [degrees of freedom](https://en.wikipedia.org/wiki/Degrees_of_freedom) in the space of solutions, if it is not empty;
- the co-kernel is the space of [constraints](https://en.wiktionary.org/wiki/constraint) that the solutions must satisfy, and its dimension is the maximal number of independent constraints.

The dimension of the co-kernel and the dimension of the image (the rank) add up to the dimension of the target space. For finite dimensions, this means that the dimension of the quotient space  *W* / *f*(*V*) is the dimension of the target space minus the dimension of the image.

As a simple example, consider the map *f* : **R**<sup>2</sup> → **R**<sup>2</sup>, given by *f*(*x*, *y*) = (0, *y*). Then for an equation *f*(*x*, *y*) = (*a*, *b*) to have a solution, we must have *a* = 0 (one constraint), and in that case the solution space is (*x*, *b*) or equivalently stated,  (0, *b*) + (*x*, 0), (one degree of freedom). The kernel may be expressed as the subspace (*x*, 0) \< *V*: the value of *x* is the freedom in a solution – while the cokernel may be expressed via the map *W* → **R**, $(a,b)\mapsto (a)$: given a vector (*a*, *b*), the value of *a* is the *obstruction* to there being a solution.

An example illustrating the infinite-dimensional case is afforded by the map *f* : **R**<sup>∞</sup> → **R**<sup>∞</sup>, $\left\{a_{n}\right\}\mapsto \left\{b_{n}\right\}$ with *b*<sub>1</sub> = 0 and *b*<sub>*n* + 1</sub> = *a<sub>n</sub>* for *n* \> 0. Its image consists of all sequences with first element 0, and thus its cokernel consists of the classes of sequences with identical first element. Thus, whereas its kernel has dimension 0 (it maps only the zero sequence to the zero sequence), its co-kernel has dimension 1. Since the domain and the target space are the same, the rank and the dimension of the kernel add up to the same [sum](https://en.wikipedia.org/wiki/Cardinal_number#Cardinal_addition) as the rank and the dimension of the co-kernel ($\aleph _{0}+0=\aleph _{0}+1$), but in the infinite-dimensional case it cannot be inferred that the kernel and the co-kernel of an [endomorphism](https://en.wikipedia.org/wiki/Endomorphism) have the same dimension (0 ≠ 1). The reverse situation obtains for the map *h* : **R**<sup>∞</sup> → **R**<sup>∞</sup>, $\left\{a_{n}\right\}\mapsto \left\{c_{n}\right\}$ with *c<sub>n</sub>* = *a*<sub>*n* + 1</sub>. Its image is the entire target space, and hence its co-kernel has dimension 0, but since it maps all sequences in which only the first element is non-zero to the zero sequence, its kernel has dimension 1.

### Index

For a linear operator with finite-dimensional kernel and co-kernel, one may define *index* as: 

$$
\operatorname {ind} (f):=\dim(\ker(f))-\dim(\operatorname {coker} (f)),
$$

 namely the degrees of freedom minus the number of constraints.

For a transformation between finite-dimensional vector spaces, this is just the difference dim(*V*) − dim(*W*), by rank–nullity. This gives an indication of how many solutions or how many constraints one has: if mapping from a larger space to a smaller one, the map may be onto, and thus will have degrees of freedom even without constraints. Conversely, if mapping from a smaller space to a larger one, the map cannot be onto, and thus one will have constraints even without degrees of freedom.

The index of an operator is precisely the [Euler characteristic](https://en.wikipedia.org/wiki/Euler_characteristic) of the 2-term complex 0 → *V* → *W* → 0. In [operator theory](https://en.wikipedia.org/wiki/Operator_theory), the index of [Fredholm operators](https://en.wikipedia.org/wiki/Fredholm_operator) is an object of study, with a major result being the [Atiyah–Singer index theorem](https://en.wikipedia.org/wiki/Atiyah%E2%80%93Singer_index_theorem).

## Algebraic classifications of linear transformations

No classification of linear maps could be exhaustive. The following incomplete list enumerates some important classifications that do not require any additional structure on the vector space.

Let V and W denote vector spaces over a field F and let *T* : *V* → *W* be a linear map.

### Monomorphism

T is said to be *[injective](https://en.wikipedia.org/wiki/Injective)* or a *[monomorphism](https://en.wikipedia.org/wiki/Monomorphism)* if any of the following equivalent conditions are true:

1.  T is [one-to-one](https://en.wikipedia.org/wiki/Injective) as a map of [sets](https://en.wikipedia.org/wiki/Set_(mathematics) "Set (mathematics)").
2.  ker *T* = {0<sub>*V*</sub>}
3.  dim(ker *T*) = 0
4.  T is [monic](https://en.wikipedia.org/wiki/Monic_morphism) or left-cancellable, which is to say, for any vector space U and any pair of linear maps *R*: *U* → *V* and *S* : *U* → *V*, the equation *TR* = *TS* implies *R* = *S*.
5.  T is [left-invertible](https://en.wikipedia.org/wiki/Inverse_(ring_theory)), which is to say there exists a linear map *S* : *W* → *V* such that *ST* is the [identity map](https://en.wikipedia.org/wiki/Identity_function) on V.

### Epimorphism

T is said to be *[surjective](https://en.wikipedia.org/wiki/Surjective)* or an *[epimorphism](https://en.wikipedia.org/wiki/Epimorphism)* if any of the following equivalent conditions are true:

1.  T is [onto](https://en.wikipedia.org/wiki/Surjective) as a map of sets.
2.  [coker](https://en.wikipedia.org/wiki/Cokernel) *T* = {0<sub>*W*</sub>}
3.  T is [epic](https://en.wikipedia.org/wiki/Epimorphism) or right-cancellable, which is to say, for any vector space U and any pair of linear maps *R* : *W* → *U* and *S* : *W* → *U*, the equation *RT* = *ST* implies *R* = *S*.
4.  T is [right-invertible](https://en.wikipedia.org/wiki/Inverse_(ring_theory)), which is to say there exists a linear map *S* : *W* → *V* such that *TS* is the [identity map](https://en.wikipedia.org/wiki/Identity_function) on W.

### Isomorphism 

T is said to be an *[isomorphism](https://en.wikipedia.org/wiki/Isomorphism)* if it is both left- and right-invertible. This is equivalent to T being both one-to-one and onto (a [bijection](https://en.wikipedia.org/wiki/Bijection) of sets) or also to T being both epic and monic, and so being a [bimorphism](https://en.wikipedia.org/wiki/Bimorphism).

If *T* : *V* → *V* is an endomorphism, then:

- If, for some positive integer n, the nth iterate of T, *T*<sup>*n*</sup>, is identically zero, then T is said to be [nilpotent](https://en.wikipedia.org/wiki/Nilpotent).
- If *T*<sup>2</sup> = *T*, then T is said to be [idempotent](https://en.wikipedia.org/wiki/Idempotent)
- If *T* = *kI*, where k is some scalar, then T is said to be a scaling transformation or scalar multiplication map; see [scalar matrix](https://en.wikipedia.org/wiki/Scalar_matrix).

## Change of basis

Given a linear map which is an [endomorphism](https://en.wikipedia.org/wiki/Endomorphism) whose matrix is *A*, in the basis *B* of the space it transforms vector coordinates \[*u*\] as \[*v*\] = *A*\[*u*\]. As vectors change with the inverse of *B* (vectors coordinates are [contravariant](https://en.wikipedia.org/wiki/Covariance_and_contravariance_of_vectors)) its inverse transformation is \[*v*\] = *B*\[*v*′\].

Substituting this in the first expression 

$$
B\left[v'\right]=AB\left[u'\right]
$$

 hence 

$$
\left[v'\right]=B^{-1}AB\left[u'\right]=A'\left[u'\right].
$$

Therefore, the matrix in the new basis is *A*′ = *B*<sup>−1</sup>*AB*, being *B* the matrix of the given basis.

Therefore, linear maps are said to be 1-co- 1-contra-[variant](https://en.wikipedia.org/wiki/Covariance_and_contravariance_of_vectors) objects, or type (1, 1) [tensors](https://en.wikipedia.org/wiki/Tensor).

## Continuity

A *linear transformation* between [topological vector spaces](https://en.wikipedia.org/wiki/Topological_vector_space), for example [normed spaces](https://en.wikipedia.org/wiki/Normed_space), may be [continuous](https://en.wikipedia.org/wiki/Continuous_function_(topology)). If its domain and codomain are the same, it will then be a [continuous linear operator](https://en.wikipedia.org/wiki/Continuous_linear_operator). A linear operator on a normed linear space is continuous if and only if it is [bounded](https://en.wikipedia.org/wiki/Bounded_operator), for example, when the domain is finite-dimensional. An infinite-dimensional domain may have [discontinuous linear operators](https://en.wikipedia.org/wiki/Discontinuous_linear_operator).

An example of an unbounded, hence discontinuous, linear transformation is differentiation on the space of smooth functions equipped with the supremum norm (a function with small values can have a derivative with large values, while the derivative of 0 is 0). For a specific example, sin(*nx*)/*n* converges to 0, but its derivative cos(*nx*) does not, so differentiation is not continuous at 0 (and by a variation of this argument, it is not continuous anywhere).

## Applications

A specific application of linear maps is for [geometric transformations](https://en.wikipedia.org/wiki/Geometric_transformation), such as those performed in [computer graphics](https://en.wikipedia.org/wiki/Computer_graphics), where the translation, rotation and scaling of 2D or 3D objects is performed by the use of a [transformation matrix](https://en.wikipedia.org/wiki/Transformation_matrix). Linear mappings also are used as a mechanism for describing change: for example in calculus correspond to derivatives; or in relativity, used as a device to keep track of the local transformations of reference frames.

Another application of these transformations is in [compiler optimizations](https://en.wikipedia.org/wiki/Compiler_optimizations) of nested-loop code, and in [parallelizing compiler](https://en.wikipedia.org/wiki/Parallelizing_compiler) techniques.

## See also

- [Additive map](https://en.wikipedia.org/wiki/Additive_map) – Z-module homomorphism
- [Antilinear map](https://en.wikipedia.org/wiki/Antilinear_map) – Conjugate homogeneous additive map
- [Bent function](https://en.wikipedia.org/wiki/Bent_function) – Special type of Boolean function
- [Bounded operator](https://en.wikipedia.org/wiki/Bounded_operator) – Kind of linear transformation
- [Cauchy's functional equation](https://en.wikipedia.org/wiki/Cauchy%27s_functional_equation)
- [Continuous linear operator](https://en.wikipedia.org/wiki/Continuous_linear_operator) – Function between topological vector spaces
- [Linear functional](https://en.wikipedia.org/wiki/Linear_functional) – Linear map from a vector space to its field of scalarsPages displaying short descriptions of redirect targets
- [Linear isometry](https://en.wikipedia.org/wiki/Linear_isometry) – Distance-preserving mathematical transformationPages displaying short descriptions of redirect targets
- [Category of matrices](https://en.wikipedia.org/wiki/Category_of_matrices)
- [Quasilinearization](https://en.wikipedia.org/wiki/Quasilinearization)

## Notes

1.  In the language of [category theory](https://en.wikipedia.org/wiki/Category_theory), linear maps are the [morphisms](https://en.wikipedia.org/wiki/Morphism) of vector spaces. Restricted to the category of finite-dimensional vector spaces, they form a category [equivalent](https://en.wikipedia.org/wiki/Equivalence_of_categories) to [the one of matrices](https://en.wikipedia.org/wiki/Category_of_matrices).
2.  , p. 14  
    Here are some properties of linear mappings $\Lambda :X\to Y$ whose proofs are so easy that we omit them; it is assumed that $A\subset X$ and $B\subset Y$: 

    1.  $\Lambda 0=0.$
    2.  If A is a subspace (or a [convex set](https://en.wikipedia.org/wiki/Convex_set), or a [balanced set](https://en.wikipedia.org/wiki/Balanced_set)) the same is true of $\Lambda (A)$
    3.  If B is a subspace (or a convex set, or a balanced set) the same is true of $\Lambda ^{-1}(B)$
    4.  In particular, the set: 

$$
\Lambda ^{-1}(\{0\})=\{\mathbf {x} \in X:\Lambda \mathbf {x} =0\}={N}(\Lambda )
$$

 is a subspace of X, called the *null space* of $\Lambda$.

3.  , p. 14. Suppose now that X and Y are vector spaces *over the same scalar field*. A mapping $\Lambda :X\to Y$ is said to be *linear* if $\Lambda (\alpha \mathbf {x} +\beta \mathbf {y} )=\alpha \Lambda \mathbf {x} +\beta \Lambda \mathbf {y}$ for all $\mathbf {x} ,\mathbf {y} \in X$ and all scalars $\alpha$ and $\beta$. Note that one often writes $\Lambda \mathbf {x}$, rather than $\Lambda (\mathbf {x} )$, when $\Lambda$ is linear.
4.  , p. 206. A mapping A of a vector space X into a vector space Y is said to be a *linear transformation* if: $A\left(\mathbf {x} _{1}+\mathbf {x} _{2}\right)=A\mathbf {x} _{1}+A\mathbf {x} _{2},\ A(c\mathbf {x} )=cA\mathbf {x}$ for all $\mathbf {x} ,\mathbf {x} _{1},\mathbf {x} _{2}\in X$ and all scalars c. Note that one often writes $A\mathbf {x}$ instead of $A(\mathbf {x} )$ if A is linear.
5.  , p. 14. Linear mappings of X onto its scalar field are called *linear functionals*.
6.  ["terminology - What does 'linear' mean in Linear Algebra?"](https://math.stackexchange.com/questions/62789/what-does-linear-mean-in-linear-algebra). *Mathematics Stack Exchange*. Retrieved 2021-02-17.
7.  , pp. 21–26.
8.  "Linear transformations of V into V are often called *linear operators* on V." , p. 207
9.  ^   , p. 57.
10. ^   , pp. 277–280.
11. , p. 210 Suppose $\left\{\mathbf {x} _{1},\ldots ,\mathbf {x} _{n}\right\}$ and $\left\{\mathbf {y} _{1},\ldots ,\mathbf {y} _{m}\right\}$ are bases of vector spaces X and Y, respectively. Then every $A\in L(X,Y)$ determines a set of numbers $a_{i,j}$ such that 

$$
A\mathbf {x} _{j}=\sum _{i=1}^{m}a_{i,j}\mathbf {y} _{i}\quad (1\leq j\leq n).
$$

 It is convenient to represent these numbers in a rectangular array of m rows and n columns, called an m *by* n *matrix*: 

$$
[A]={\begin{bmatrix}a_{1,1}&a_{1,2}&\ldots &a_{1,n}\\a_{2,1}&a_{2,2}&\ldots &a_{2,n}\\\vdots &\vdots &\ddots &\vdots \\a_{m,1}&a_{m,2}&\ldots &a_{m,n}\end{bmatrix}}
$$

 Observe that the coordinates $a_{i,j}$ of the vector $A\mathbf {x} _{j}$ (with respect to the basis $\{\mathbf {y} _{1},\ldots ,\mathbf {y} _{m}\}$) appear in the *j*<sup>th</sup> column of $[A]$. The vectors $A\mathbf {x} _{j}$ are therefore sometimes called the *column vectors* of $[A]$. With this terminology, the *range* of A *is spanned by the column vectors of $[A]$*.
12. p. 52, § 3.3
13. , p. 19, § 3.1
14. , 0.2.3 Vector spaces associated with a matrix or linear transformation, p. 6
15. ^    p. 52, § 2.5.1
16. ^    p. 90, § 50
17. Nistor, Victor (2001) \[1994\], ["Index theory"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society): "The main question in index theory is to provide index formulas for classes of Fredholm operators ... Index theory has become a subject on its own only after M. F. Atiyah and I. Singer published their index theorems"
18. , p. 15 **1.18 Theorem** *Let $\Lambda$ be a linear functional on a topological vector space X. Assume $\Lambda \mathbf {x} \neq 0$ for some $\mathbf {x} \in X$. Then each of the following four properties implies the other three:* 

    1.  $\Lambda$ is continuous
    2.  The null space $N(\Lambda )$ is closed.
    3.  $N(\Lambda )$ is not dense in X.
    4.  $\Lambda$ is bounded in some neighbourhood V of 0.

1.  One map $F$ is said to [extend](https://en.wikipedia.org/wiki/Extension_of_a_function) another map $f$ if when $f$ is defined at a point $s$, then so is $F$ and $F(s)=f(s).$

## Bibliography

- [Axler, Sheldon Jay](https://en.wikipedia.org/wiki/Sheldon_Axler) (2015). *Linear Algebra Done Right* (3rd ed.). [Springer](https://en.wikipedia.org/wiki/Springer_Science%2BBusiness_Media). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-319-11079-0](https://en.wikipedia.org/wiki/Special:BookSources/978-3-319-11079-0).
- Bronshtein, I. N.; Semendyayev, K. A. (2004). *[Handbook of Mathematics](https://en.wikipedia.org/wiki/Bronshtein_and_Semendyayev)* (4th ed.). New York: Springer-Verlag. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [3-540-43491-7](https://en.wikipedia.org/wiki/Special:BookSources/3-540-43491-7).
- [Halmos, Paul Richard](https://en.wikipedia.org/wiki/Paul_Halmos) (1974) \[1958\]. *Finite-Dimensional Vector Spaces* (2nd ed.). [Springer](https://en.wikipedia.org/wiki/Springer_Science%2BBusiness_Media). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-90093-4](https://en.wikipedia.org/wiki/Special:BookSources/0-387-90093-4).
- Horn, Roger A.; Johnson, Charles R. (2013). *Matrix Analysis* (Second ed.). [Cambridge University Press](https://en.wikipedia.org/wiki/Cambridge_University_Press). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-83940-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-83940-2).
- [Katznelson, Yitzhak](https://en.wikipedia.org/wiki/Yitzhak_Katznelson); Katznelson, Yonatan R. (2008). *A (Terse) Introduction to Linear Algebra*. [American Mathematical Society](https://en.wikipedia.org/wiki/American_Mathematical_Society). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8218-4419-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8218-4419-9).
- Kubrusly, Carlos (2001). *Elements of operator theory*. Boston: Birkhäuser. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4757-3328-0](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4757-3328-0). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [754555941](https://search.worldcat.org/oclc/754555941).
- [Lang, Serge](https://en.wikipedia.org/wiki/Serge_Lang) (1987), *Linear Algebra* (Third ed.), New York: [Springer-Verlag](https://en.wikipedia.org/wiki/Springer-Verlag), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-96412-6](https://en.wikipedia.org/wiki/Special:BookSources/0-387-96412-6)
- [Rudin, Walter](https://en.wikipedia.org/wiki/Walter_Rudin) (1973). [Functional Analysis](https://archive.org/details/functionalanalys00rudi). International Series in Pure and Applied Mathematics. Vol. 25 (First ed.). New York, NY: [McGraw-Hill Science/Engineering/Math](https://en.wikipedia.org/wiki/McGraw-Hill_Science/Engineering/Math). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780070542259](https://en.wikipedia.org/wiki/Special:BookSources/9780070542259).
- [Rudin, Walter](https://en.wikipedia.org/wiki/Walter_Rudin) (1976). [Principles of Mathematical Analysis](https://archive.org/details/PrinciplesOfMathematicalAnalysis). Walter Rudin Student Series in Advanced Mathematics (3rd ed.). New York: McGraw–Hill. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-07-054235-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-07-054235-8).
- [Rudin, Walter](https://en.wikipedia.org/wiki/Walter_Rudin) (1991). [Functional Analysis](https://archive.org/details/functionalanalys00rudi). International Series in Pure and Applied Mathematics. Vol. 8 (Second ed.). New York, NY: [McGraw-Hill Science/Engineering/Math](https://en.wikipedia.org/wiki/McGraw-Hill_Science/Engineering/Math). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-07-054236-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-07-054236-5). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [21163277](https://search.worldcat.org/oclc/21163277).
- [Schaefer, Helmut H.](https://en.wikipedia.org/wiki/Helmut_H._Schaefer); Wolff, Manfred P. (1999). *Topological Vector Spaces*. [GTM](https://en.wikipedia.org/wiki/Graduate_Texts_in_Mathematics). Vol. 8 (Second ed.). New York, NY: Springer New York Imprint Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4612-7155-0](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4612-7155-0). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [840278135](https://search.worldcat.org/oclc/840278135).
- [Schechter, Eric](https://en.wikipedia.org/wiki/Eric_Schechter) (1996). *Handbook of Analysis and Its Foundations*. San Diego, CA: Academic Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-12-622760-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-12-622760-4). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [175294365](https://search.worldcat.org/oclc/175294365).
- Swartz, Charles (1992). *An introduction to Functional Analysis*. New York: M. Dekker. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8247-8643-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8247-8643-4). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [24909067](https://search.worldcat.org/oclc/24909067).
- [Tu, Loring W.](https://en.wikipedia.org/wiki/Loring_W._Tu) (2011). [*An Introduction to Manifolds*](https://en.wikipedia.org/wiki/An_Introduction_to_Manifolds) (2nd ed.). [Springer](https://en.wikipedia.org/wiki/Springer_Science%2BBusiness_Media). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8218-4419-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8218-4419-9).
- [Wilansky, Albert](https://en.wikipedia.org/wiki/Albert_Wilansky) (2013). *Modern Methods in Topological Vector Spaces*. Mineola, New York: Dover Publications, Inc. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-486-49353-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-486-49353-4). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [849801114](https://search.worldcat.org/oclc/849801114).
