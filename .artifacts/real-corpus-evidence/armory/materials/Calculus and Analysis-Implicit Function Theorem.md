[[calculus-analysis.base]]

> Source: [[Implicit Function Theorem]]
> License: Wikipedia content is available under CC BY-SA 4.0.

In [[Multivariable Calculus]], the **implicit function theorem** is a tool that allows [relations](https://en.wikipedia.org/wiki/Relation_(mathematics)#Definition "Relation (mathematics)") to be converted to [functions of several real variables](https://en.wikipedia.org/wiki/Functions_of_several_real_variables). It does so by representing the relation as the [graph of a function](https://en.wikipedia.org/wiki/Graph_of_a_function). There may not be a single function whose graph can represent the entire relation, but there may be such a function on a restriction of the [domain](https://en.wikipedia.org/wiki/Domain_of_a_relation) of the relation. The implicit function theorem gives a sufficient condition to ensure that there is such a function.

More precisely, given a system of m equations *f<sub>i</sub>* (*x*<sub>1</sub>, ..., *x<sub>n</sub>*, *y*<sub>1</sub>, ..., *y<sub>m</sub>*) = 0, *i* = 1, ..., *m* (often abbreviated into *F*(**x**, **y**) = **0**), the theorem states that, under a mild condition on the [partial derivatives](https://en.wikipedia.org/wiki/Partial_derivative) (with respect to each *y<sub>i</sub>* ) at a point, the m variables *y<sub>i</sub>* are differentiable functions of the *x<sub>j</sub>* in some [neighbourhood](https://en.wikipedia.org/wiki/Neighbourhood_(mathematics) "Neighbourhood (mathematics)") of the point. As these functions generally cannot be expressed in [closed form](https://en.wikipedia.org/wiki/Closed_form_expression), they are *implicitly* defined by the equations, and this motivated the name of the theorem.

In other words, under a mild condition on the partial derivatives, the set of [zeros](https://en.wikipedia.org/wiki/Zero_of_a_function) of a system of equations is [locally](https://en.wikipedia.org/wiki/Local_property) the [graph of a function](https://en.wikipedia.org/wiki/Graph_of_a_function).

## History

[Augustin-Louis Cauchy](https://en.wikipedia.org/wiki/Augustin-Louis_Cauchy) (1789–1857) is credited with the first rigorous form of the implicit function theorem. [Ulisse Dini](https://en.wikipedia.org/wiki/Ulisse_Dini) (1845–1918) generalized the real-variable version of the implicit function theorem to the context of functions of any number of real variables.

## Two variables case

Let $f:\mathbb {R} ^{2}\to \mathbb {R}$ be a continuously differentiable function defining the [implicit equation](https://en.wikipedia.org/wiki/Implicit_equation) of a [curve](https://en.wikipedia.org/wiki/Curve) $f(x,y)=0$. Let $(x_{0},y_{0})$ be a point on the curve, that is, a point such that $f(x_{0},y_{0})=0$. In this simple case, the implicit function theorem can be stated as follows:

**Theorem**—If $f(x,y)$ is a function that is continuously differentiable in a neighbourhood of the point $(x_{0},y_{0})$, and ${\frac {\partial f}{\partial y}}(x_{0},y_{0})\neq 0,$ then there exists a unique differentiable function $\varphi$ such that $y_{0}=\varphi (x_{0})$ and $f(x,\varphi (x))=0$ in a neighbourhood of $x_{0}$.

**Proof.** By differentiating the equation $f(x,\varphi (x))=0$, one gets 

$$
{\frac {\partial f}{\partial x}}(x,\varphi (x))+\varphi '(x)\,{\frac {\partial f}{\partial y}}(x,\varphi (x))=0.
$$

 and thus 

$$
\varphi '(x)=-{\frac {{\frac {\partial f}{\partial x}}(x,\varphi (x))}{{\frac {\partial f}{\partial y}}(x,\varphi (x))}}.
$$

 This gives an [ordinary differential equation](https://en.wikipedia.org/wiki/Ordinary_differential_equation) for $\varphi$, with the initial condition $\varphi (x_{0})=y_{0}$.

Since ${\frac {\partial f}{\partial y}}(x_{0},y_{0})\neq 0,$ the right-hand side of the differential equation is continuous. Hence, the [Peano existence theorem](https://en.wikipedia.org/wiki/Peano_existence_theorem) applies so there is a (possibly non-unique) solution. To see why $\varphi$ is unique, note that the function $g_{x}(y)=f(x,y)$ is strictly [monotone](https://en.wikipedia.org/wiki/Monotonic_function) in a neighbourhood of $x_{0},y_{0}$ (as ${\frac {\partial f}{\partial y}}(x_{0},y_{0})\neq 0$), thus it is [injective](https://en.wikipedia.org/wiki/Injective). If $\varphi ,\phi$ are solutions to the differential equation, then $g_{x}(\varphi (x))=g_{x}(\phi (x))=0$ and by injectivity we get, $\varphi (x)=\phi (x)$.

## First example

![[media/fc1f319b3b0e7f9919cc7b241e5e3a2b13ae0e7d.png]]
The unit circle of implicit equation <em>x</em><sup>2</sup> + <em>y</em><sup>2</sup> – 1 = 0 cannot be represented as the graph of a function. Around the point <strong>A</strong> where the tangent is not vertical, the bolded [circular arc](https://en.wikipedia.org/wiki/Circular_arc) is the graph of some function of x, while around <strong>B</strong>, there is no function of x with the circle as its graph.<br />
This is exactly what the implicit function theorem asserts in this case.

If we define the function *f*(*x*, *y*) = *x*<sup>2</sup> + *y*<sup>2</sup>, then the equation *f*(*x*, *y*) = 1 cuts out the [unit circle](https://en.wikipedia.org/wiki/Unit_circle) as the [level set](https://en.wikipedia.org/wiki/Level_set) {(*x*, *y*) \| *f*(*x*, *y*) = 1}. There is no way to represent the unit circle as the graph of a function of one variable *y* = *g*(*x*) because for each choice of *x* ∈ (−1, 1), there are two choices of *y*, namely $\pm {\sqrt {1-x^{2}}}$.

However, it is possible to represent *part* of the circle as the graph of a function of one variable. If we let $g_{1}(x)={\sqrt {1-x^{2}}}$ for −1 ≤ *x* ≤ 1, then the graph of *y* = *g*<sub>1</sub>(*x*) provides the upper half of the circle. Similarly, if $g_{2}(x)=-{\sqrt {1-x^{2}}}$, then the graph of *y* = *g*<sub>2</sub>(*x*) gives the lower half of the circle.

The purpose of the implicit function theorem is to tell us that functions like *g*<sub>1</sub>(*x*) and *g*<sub>2</sub>(*x*) [almost always](https://en.wikipedia.org/wiki/List_of_mathematical_jargon#almost_all) exist, even in situations where we cannot write down explicit formulas. It guarantees that *g*<sub>1</sub>(*x*) and *g*<sub>2</sub>(*x*) are differentiable, and it even works in situations where we do not have a formula for *f*(*x*, *y*).

## Definitions

Let $f:\mathbb {R} ^{n+m}\to \mathbb {R} ^{m}$ be a [continuously differentiable](https://en.wikipedia.org/wiki/Continuously_differentiable) function. We think of $\mathbb {R} ^{n+m}$ as the [Cartesian product](https://en.wikipedia.org/wiki/Cartesian_product) $\mathbb {R} ^{n}\times \mathbb {R} ^{m},$ and we write a point of this product as $(\mathbf {x} ,\mathbf {y} )=(x_{1},\ldots ,x_{n},y_{1},\ldots y_{m}).$ Starting from the given function $f$, our goal is to construct a function $g:\mathbb {R} ^{n}\to \mathbb {R} ^{m}$ whose graph $({\textbf {x}},g({\textbf {x}}))$ is precisely the set of all $({\textbf {x}},{\textbf {y}})$ such that $f({\textbf {x}},{\textbf {y}})={\textbf {0}}$.

As noted above, this may not always be possible. We will therefore fix a point $({\textbf {a}},{\textbf {b}})=(a_{1},\dots ,a_{n},b_{1},\dots ,b_{m})$ which satisfies $f({\textbf {a}},{\textbf {b}})={\textbf {0}}$, and we will ask for a $g$ that works near the point $({\textbf {a}},{\textbf {b}})$. In other words, we want an [open set](https://en.wikipedia.org/wiki/Open_set) $U\subset \mathbb {R} ^{n}$ containing ${\textbf {a}}$, an open set $V\subset \mathbb {R} ^{m}$ containing ${\textbf {b}}$, and a function $g:U\to V$ such that the graph of $g$ satisfies the relation $f={\textbf {0}}$ on $U\times V$, and that no other points within $U\times V$ do so. In symbols,

$$
\{(\mathbf {x} ,g(\mathbf {x} ))\mid \mathbf {x} \in U\}=\{(\mathbf {x} ,\mathbf {y} )\in U\times V\mid f(\mathbf {x} ,\mathbf {y} )=\mathbf {0} \}.
$$

To state the implicit function theorem, we need the [Jacobian matrix](https://en.wikipedia.org/wiki/Jacobian_matrix_and_determinant) of $f$, which is the matrix of the [partial derivatives](https://en.wikipedia.org/wiki/Partial_derivative) of $f$. Abbreviating $(a_{1},\dots ,a_{n},b_{1},\dots ,b_{m})$ to $({\textbf {a}},{\textbf {b}})$, the Jacobian matrix is

$$
(Df)(\mathbf {a} ,\mathbf {b} )=\left[{\begin{array}{ccc|ccc}{\frac {\partial f_{1}}{\partial x_{1}}}(\mathbf {a} ,\mathbf {b} )&\cdots &{\frac {\partial f_{1}}{\partial x_{n}}}(\mathbf {a} ,\mathbf {b} )&{\frac {\partial f_{1}}{\partial y_{1}}}(\mathbf {a} ,\mathbf {b} )&\cdots &{\frac {\partial f_{1}}{\partial y_{m}}}(\mathbf {a} ,\mathbf {b} )\\\vdots &\ddots &\vdots &\vdots &\ddots &\vdots \\{\frac {\partial f_{m}}{\partial x_{1}}}(\mathbf {a} ,\mathbf {b} )&\cdots &{\frac {\partial f_{m}}{\partial x_{n}}}(\mathbf {a} ,\mathbf {b} )&{\frac {\partial f_{m}}{\partial y_{1}}}(\mathbf {a} ,\mathbf {b} )&\cdots &{\frac {\partial f_{m}}{\partial y_{m}}}(\mathbf {a} ,\mathbf {b} )\end{array}}\right]=\left[{\begin{array}{c|c}X&Y\end{array}}\right]
$$

where $X$ is the matrix of partial derivatives in the variables $x_{i}$ and $Y$ is the matrix of partial derivatives in the variables $y_{j}$. The implicit function theorem says that if $Y$ is an invertible matrix, then there are $U$, $V$, and $g$ as desired. Writing all the hypotheses together gives the following statement.

## Statement of the theorem

Let $f:\mathbb {R} ^{n+m}\to \mathbb {R} ^{m}$ be a [continuously differentiable function](https://en.wikipedia.org/wiki/Continuously_differentiable_function), and let $\mathbb {R} ^{n+m}$ have coordinates $({\textbf {x}},{\textbf {y}})$. Fix a point $({\textbf {a}},{\textbf {b}})=(a_{1},\dots ,a_{n},b_{1},\dots ,b_{m})$ with $f({\textbf {a}},{\textbf {b}})=\mathbf {0}$, where $\mathbf {0} \in \mathbb {R} ^{m}$ is the zero vector. If the [[Jacobian Matrix]] (this is the right-hand panel of the Jacobian matrix shown in the previous section): 

$$
J_{f,\mathbf {y} }(\mathbf {a} ,\mathbf {b} )=\left[{\frac {\partial f_{i}}{\partial y_{j}}}(\mathbf {a} ,\mathbf {b} )\right]
$$

 is [invertible](https://en.wikipedia.org/wiki/Invertible), then there exists an open set $U\subset \mathbb {R} ^{n}$ containing ${\textbf {a}}$ such that there exists a unique function $g:U\to \mathbb {R} ^{m}$ such that $g(\mathbf {a} )=\mathbf {b}$, and $f(\mathbf {x} ,g(\mathbf {x} ))=\mathbf {0} ~{\text{for all}}~\mathbf {x} \in U$. Moreover, $g$ is continuously differentiable and, denoting the left-hand panel of the Jacobian matrix shown in the previous section as: 

$$
J_{f,\mathbf {x} }(\mathbf {a} ,\mathbf {b} )=\left[{\frac {\partial f_{i}}{\partial x_{j}}}(\mathbf {a} ,\mathbf {b} )\right],
$$

 the Jacobian matrix of partial derivatives of $g$ in $U$ is given by the [matrix product](https://en.wikipedia.org/wiki/Matrix_product): 

$$
\left[{\frac {\partial g_{i}}{\partial x_{j}}}(\mathbf {x} )\right]_{m\times n}=-\left[J_{f,\mathbf {y} }(\mathbf {x} ,g(\mathbf {x} ))\right]_{m\times m}^{-1}\,\left[J_{f,\mathbf {x} }(\mathbf {x} ,g(\mathbf {x} ))\right]_{m\times n}
$$

A proof may be found in the [inverse function theorem](https://en.wikipedia.org/wiki/Inverse_function_theorem#Implicit_function_theorem) article. Here, the two-dimensional case is detailed.

### Higher derivatives

If, moreover, $f$ is [analytic](https://en.wikipedia.org/wiki/Analytic_function) or continuously differentiable $k$ times in a neighbourhood of $({\textbf {a}},{\textbf {b}})$, then one may choose $U$ in order that the same holds true for $g$ inside $U$.  In the analytic case, this is called the **analytic implicit function theorem**.

## The circle example

Let us go back to the example of the [unit circle](https://en.wikipedia.org/wiki/Unit_circle). In this case *n* = *m* = 1 and $f(x,y)=x^{2}+y^{2}-1$. The matrix of partial derivatives is just a 1 × 2 matrix, given by 

$$
(Df)(a,b)={\begin{bmatrix}{\dfrac {\partial f}{\partial x}}(a,b)&{\dfrac {\partial f}{\partial y}}(a,b)\end{bmatrix}}={\begin{bmatrix}2a&2b\end{bmatrix}}
$$

Thus, here, the *Y* in the statement of the theorem is just the number 2*b*; the linear map defined by it is invertible [if and only if](https://en.wikipedia.org/wiki/If_and_only_if) *b* ≠ 0. By the implicit function theorem we see that we can locally write the circle in the form *y* = *g*(*x*) for all points where *y* ≠ 0. For (±1, 0) we run into trouble, as noted before. The implicit function theorem may still be applied to these two points, by writing x as a function of y, that is, $x=h(y)$; now the graph of the function will be $\left(h(y),y\right)$, since where *b* = 0 we have *a* = 1, and the conditions to locally express the function in this form are satisfied.

The implicit derivative of *y* with respect to *x*, and that of *x* with respect to *y*, can be found by [totally differentiating](https://en.wikipedia.org/wiki/Differential_of_a_function#Differentials_in_several_variables) the implicit function $x^{2}+y^{2}-1$ and equating to 0: 

$$
2x\,dx+2y\,dy=0,
$$

 giving 

$$
{\frac {dy}{dx}}=-{\frac {x}{y}}
$$

 and 

$$
{\frac {dx}{dy}}=-{\frac {y}{x}}.
$$

## Application: change of coordinates

Suppose we have an m-dimensional space, parametrised by a set of coordinates $(x_{1},\ldots ,x_{m})$. We can introduce a new coordinate system $(x'_{1},\ldots ,x'_{m})$ by supplying m functions $h_{1}\ldots h_{m}$ each being continuously differentiable. These functions allow us to calculate the new coordinates $(x'_{1},\ldots ,x'_{m})$ of a point, given the point's old coordinates $(x_{1},\ldots ,x_{m})$ using $x'_{1}=h_{1}(x_{1},\ldots ,x_{m}),\ldots ,x'_{m}=h_{m}(x_{1},\ldots ,x_{m})$. One might want to verify if the opposite is possible: given coordinates $(x'_{1},\ldots ,x'_{m})$, can we 'go back' and calculate the same point's original coordinates $(x_{1},\ldots ,x_{m})$? The implicit function theorem will provide an answer to this question. The (new and old) coordinates $(x'_{1},\ldots ,x'_{m},x_{1},\ldots ,x_{m})$ are related by *f* = 0, with 

$$
f(x'_{1},\ldots ,x'_{m},x_{1},\ldots ,x_{m})=(h_{1}(x_{1},\ldots ,x_{m})-x'_{1},\ldots ,h_{m}(x_{1},\ldots ,x_{m})-x'_{m}).
$$

 Now the Jacobian matrix of *f* at a certain point (*a*, *b*) \[ where $a=(x'_{1},\ldots ,x'_{m}),b=(x_{1},\ldots ,x_{m})$ \] is given by 

$$
(Df)(a,b)=\left[{\begin{matrix}-1&\cdots &0\\\vdots &\ddots &\vdots \\0&\cdots &-1\end{matrix}}\left|{\begin{matrix}{\frac {\partial h_{1}}{\partial x_{1}}}(b)&\cdots &{\frac {\partial h_{1}}{\partial x_{m}}}(b)\\\vdots &\ddots &\vdots \\{\frac {\partial h_{m}}{\partial x_{1}}}(b)&\cdots &{\frac {\partial h_{m}}{\partial x_{m}}}(b)\\\end{matrix}}\right.\right]=[-I_{m}|J].
$$

 where I<sub>*m*</sub> denotes the *m* × *m* [identity matrix](https://en.wikipedia.org/wiki/Identity_matrix), and J is the *m* × *m* matrix of partial derivatives, evaluated at (*a*, *b*). (In the above, these blocks were denoted by X and Y. As it happens, in this particular application of the theorem, neither matrix depends on *a*.) The implicit function theorem now states that we can locally express $(x_{1},\ldots ,x_{m})$ as a function of $(x'_{1},\ldots ,x'_{m})$ if *J* is invertible. Demanding *J* is invertible is equivalent to det *J* ≠ 0, thus we see that we can go back from the primed to the unprimed coordinates if the determinant of the Jacobian *J* is non-zero. This statement is also known as the [inverse function theorem](https://en.wikipedia.org/wiki/Inverse_function_theorem).

### Example: polar coordinates

As a simple application of the above, consider the plane, parametrised by [polar coordinates](https://en.wikipedia.org/wiki/Polar_coordinates) (*R*, *θ*). We can go to a new coordinate system ([cartesian coordinates](https://en.wikipedia.org/wiki/Cartesian_coordinates)) by defining functions *x*(*R*, *θ*) = *R* cos(*θ*) and *y*(*R*, *θ*) = *R* sin(*θ*). This makes it possible given any point (*R*, *θ*) to find corresponding Cartesian coordinates (*x*, *y*). When can we go back and convert Cartesian into polar coordinates? By the previous example, it is sufficient to have det *J* ≠ 0, with 

$$
J={\begin{bmatrix}{\frac {\partial x(R,\theta )}{\partial R}}&{\frac {\partial x(R,\theta )}{\partial \theta }}\\{\frac {\partial y(R,\theta )}{\partial R}}&{\frac {\partial y(R,\theta )}{\partial \theta }}\\\end{bmatrix}}={\begin{bmatrix}\cos \theta &-R\sin \theta \\\sin \theta &R\cos \theta \end{bmatrix}}.
$$

 Since det *J* = *R*, conversion back to polar coordinates is possible if *R* ≠ 0. So it remains to check the case *R* = 0. It is easy to see that in case *R* = 0, our coordinate transformation is not invertible: at the origin, the value of θ is not well-defined.

## Generalizations

### Banach space version

Based on the [inverse function theorem](https://en.wikipedia.org/wiki/Inverse_function_theorem) in [Banach spaces](https://en.wikipedia.org/wiki/Banach_space), it is possible to extend the implicit function theorem to Banach space valued mappings.

Let *X*, *Y*, *Z* be [Banach spaces](https://en.wikipedia.org/wiki/Banach_space). Let the mapping *f* : *X* × *Y* → *Z* be continuously [Fréchet differentiable](https://en.wikipedia.org/wiki/Fr%C3%A9chet_differentiable). If $(x_{0},y_{0})\in X\times Y$, $f(x_{0},y_{0})=0$, and $y\mapsto Df(x_{0},y_{0})(0,y)$ is a Banach space isomorphism from *Y* onto *Z*, then there exist neighbourhoods *U* of *x*<sub>0</sub> and *V* of *y*<sub>0</sub> and a Fréchet differentiable function *g* : *U* → *V* such that *f*(*x*, *g*(*x*)) = 0 and *f*(*x*, *y*) = 0 if and only if *y* = *g*(*x*), for all $(x,y)\in U\times V$.

### Implicit functions from non-differentiable functions

Various forms of the implicit function theorem exist for the case when the function *f* is not differentiable. It is standard that local strict monotonicity suffices in one dimension. The following more general form was proven by Kumagai based on an observation by Jittorntrum.

Consider a continuous function $f:\mathbb {R} ^{n}\times \mathbb {R} ^{m}\to \mathbb {R} ^{n}$ such that $f(x_{0},y_{0})=0$. If there exist open neighbourhoods $A\subset \mathbb {R} ^{n}$ and $B\subset \mathbb {R} ^{m}$ of *x*<sub>0</sub> and *y*<sub>0</sub>, respectively, such that, for all *y* in *B*, $f(\cdot ,y):A\to \mathbb {R} ^{n}$ is locally one-to-one, then there exist open neighbourhoods $A_{0}\subset \mathbb {R} ^{n}$ and $B_{0}\subset \mathbb {R} ^{m}$ of *x*<sub>0</sub> and *y*<sub>0</sub>, such that, for all $y\in B_{0}$, the equation *f*(*x*, *y*) = 0 has a unique solution 

$$
x=g(y)\in A_{0},
$$

 where *g* is a continuous function from *B*<sub>0</sub> into *A*<sub>0</sub>.

### Collapsing manifolds

Perelman’s collapsing theorem for [3-manifolds](https://en.wikipedia.org/wiki/3-manifold), the capstone of his proof of Thurston's [geometrization conjecture](https://en.wikipedia.org/wiki/Geometrization_conjecture), can be understood as an extension of the implicit function theorem.

## See also

- [Inverse function theorem](https://en.wikipedia.org/wiki/Inverse_function_theorem)
- [Constant rank theorem](https://en.wikipedia.org/wiki/Constant_rank_theorem): Both the implicit function theorem and the inverse function theorem can be seen as special cases of the constant rank theorem.

## Notes

1.  Also called **[Dini](https://en.wikipedia.org/wiki/Ulisse_Dini)'s theorem** by the Pisan school in Italy. In the English-language literature, [Dini's theorem](https://en.wikipedia.org/wiki/Dini%27s_theorem) is a different theorem in mathematical analysis.

## References

1.  [Chiang, Alpha C.](https://en.wikipedia.org/wiki/Alpha_Chiang) (1984). [Fundamental Methods of Mathematical Economics](https://archive.org/details/fundamentalmetho0000chia_b4p1/page/204) (3rd ed.). McGraw-Hill. pp. [204–206](https://archive.org/details/fundamentalmetho0000chia_b4p1/page/204). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-07-010813-7](https://en.wikipedia.org/wiki/Special:BookSources/0-07-010813-7).
2.  Krantz, Steven; Parks, Harold (2003). [The Implicit Function Theorem](https://archive.org/details/implicitfunction0000kran). Modern Birkhauser Classics. Birkhauser. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-8176-4285-4](https://en.wikipedia.org/wiki/Special:BookSources/0-8176-4285-4).
3.  de Oliveira, Oswaldo (2013). "The Implicit and Inverse Function Theorems: Easy Proofs". *Real Anal. Exchange*. **39** (1): 214–216. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1212.2066](https://arxiv.org/abs/1212.2066). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.14321/realanalexch.39.1.0207](https://doi.org/10.14321%2Frealanalexch.39.1.0207). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [118792515](https://api.semanticscholar.org/CorpusID:118792515).
4.  Fritzsche, K.; Grauert, H. (2002). [From Holomorphic Functions to Complex Manifolds](https://books.google.com/books?id=jSeRz36zXIMC&pg=PA34). Springer. p. 34. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780387953953](https://en.wikipedia.org/wiki/Special:BookSources/9780387953953).
5.  [Lang, Serge](https://en.wikipedia.org/wiki/Serge_Lang) (1999). [Fundamentals of Differential Geometry](https://archive.org/details/fundamentalsdiff00lang_678). Graduate Texts in Mathematics. New York: Springer. pp. [15](https://archive.org/details/fundamentalsdiff00lang_678/page/n15)–21. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-98593-X](https://en.wikipedia.org/wiki/Special:BookSources/0-387-98593-X).
6.  Edwards, Charles Henry (1994) \[1973\]. *Advanced Calculus of Several Variables*. Mineola, New York: Dover Publications. pp. 417–418. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-486-68336-2](https://en.wikipedia.org/wiki/Special:BookSources/0-486-68336-2).
7.  Kudryavtsev, Lev Dmitrievich (2001) \[1994\], ["Implicit function"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society)
8.  Jittorntrum, K. (1978). "An Implicit Function Theorem". *Journal of Optimization Theory and Applications*. **25** (4): 575–577. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/BF00933522](https://doi.org/10.1007%2FBF00933522). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [121647783](https://api.semanticscholar.org/CorpusID:121647783).
9.  Kumagai, S. (1980). "An implicit function theorem: Comment". *Journal of Optimization Theory and Applications*. **31** (2): 285–288. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/BF00934117](https://doi.org/10.1007%2FBF00934117). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [119867925](https://api.semanticscholar.org/CorpusID:119867925).
10. Cao, Jianguo; Ge, Jian (2011). "A simple proof of Perelman's collapsing theorem for 3-manifolds". *J. Geom. Anal*. **21** (4): 807–869. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1003.2215](https://arxiv.org/abs/1003.2215). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s12220-010-9169-5](https://doi.org/10.1007%2Fs12220-010-9169-5). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [514106](https://api.semanticscholar.org/CorpusID:514106).

11 Generalized Implicit Function Theorem Journal Of Indonesian Mathematical Society DOI:10.22.342 v3211.1551 License CCBY-NC-ND-4.0 Discusses Implicit function Theorem for X a topological space , Y Banach Space, Z a Topological Vector space

## Further reading

- [Allendoerfer, Carl B.](https://en.wikipedia.org/wiki/Carl_B._Allendoerfer) (1974). "Theorems about Differentiable Functions". *Calculus of Several Variables and Differentiable Manifolds*. New York: Macmillan. pp. 54–88. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-02-301840-2](https://en.wikipedia.org/wiki/Special:BookSources/0-02-301840-2).
- [Binmore, K. G.](https://en.wikipedia.org/wiki/Kenneth_Binmore) (1983). ["Implicit Functions"](https://books.google.com/books?id=K8RfQgAACAAJ&pg=PA198). *Calculus*. New York: Cambridge University Press. pp. 198–211. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-28952-1](https://en.wikipedia.org/wiki/Special:BookSources/0-521-28952-1).
- [Loomis, Lynn H.](https://en.wikipedia.org/wiki/Lynn_Harold_Loomis); [Sternberg, Shlomo](https://en.wikipedia.org/wiki/Shlomo_Sternberg) (1990). [Advanced Calculus](https://archive.org/details/advancedcalculus0000loom) (Revised ed.). Boston: Jones and Bartlett. pp. [164–171](https://archive.org/details/advancedcalculus0000loom/page/164). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-86720-122-3](https://en.wikipedia.org/wiki/Special:BookSources/0-86720-122-3).
- [Protter, Murray H.](https://en.wikipedia.org/wiki/Murray_H._Protter); [Morrey, Charles B. Jr.](https://en.wikipedia.org/wiki/Charles_B._Morrey_Jr.) (1985). ["Implicit Function Theorems. Jacobians"](https://books.google.com/books?id=3lTmBwAAQBAJ&pg=PA390). *Intermediate Calculus* (2nd ed.). New York: Springer. pp. 390–420. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-96058-9](https://en.wikipedia.org/wiki/Special:BookSources/0-387-96058-9).
