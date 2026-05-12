[[calculus-analysis.base]]

> Source: [Directional derivative](https://en.wikipedia.org/wiki/Directional_derivative)
> License: Wikipedia content is available under CC BY-SA 4.0.

In [[Multivariable Calculus]], the **directional derivative** measures the rate at which a function changes in a particular direction at a given point.\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]

The directional derivative of a multivariable [differentiable scalar function](https://en.wikipedia.org/wiki/Differentiable_function) along a given [vector](https://en.wikipedia.org/wiki/Vector_(mathematics)) **v** at a given point **x** represents the instantaneous rate of change of the function in the direction **v** through **x**.

Many mathematical texts assume that the directional vector is [normalized](https://en.wikipedia.org/wiki/Unit_vector) (a unit vector), meaning that its magnitude is equivalent to one. This is by convention and not required for proper calculation. In order to adjust a formula for the directional derivative to work for any vector, one must divide the expression by the magnitude of the vector. Normalized vectors are denoted with a [circumflex](https://en.wikipedia.org/wiki/Circumflex) (hat) symbol: $\mathbf {\widehat {}}$.

The directional derivative of a [scalar function](https://en.wikipedia.org/wiki/Scalar_field) *f* with respect to a vector **v** (denoted as $\mathbf {\hat {v}}$ when [normalized](https://en.wikipedia.org/wiki/Unit_vector)) at a point (e.g., position) (**x**,f(**x**)) may be denoted by any of the following: 

$$
{\begin{aligned}\nabla _{\mathbf {v} }{f}(\mathbf {x} )&=f'_{\mathbf {v} }(\mathbf {x} )\\&=D_{\mathbf {v} }f(\mathbf {x} )\\&=Df(\mathbf {x} )(\mathbf {v} )\\&=\partial _{\mathbf {v} }f(\mathbf {x} )\\&={\frac {\partial f(\mathbf {x} )}{\partial \mathbf {v} }}\\&=\mathbf {\hat {v}} \cdot {\nabla f(\mathbf {x} )}\\&=\mathbf {\hat {v}} \cdot {\frac {\partial f(\mathbf {x} )}{\partial \mathbf {x} }}.\\\end{aligned}}
$$

It therefore generalizes the notion of a [partial derivative](https://en.wikipedia.org/wiki/Partial_derivative), in which the rate of change is taken along one of the [curvilinear](https://en.wikipedia.org/wiki/Curvilinear_coordinates) [coordinate curves](https://en.wikipedia.org/wiki/Coordinate_curves), all other coordinates being constant. The directional derivative is a special case of the [Gateaux derivative](https://en.wikipedia.org/wiki/Gateaux_derivative).

## Definition

![[media/87ea57383772deb1d1c9e545f4acc05165ec9424.png]]
A [contour plot](https://en.wikipedia.org/wiki/Contour_plot) of $f(x,y)=x^{2}+y^{2}$, showing the gradient vector in black, and the unit vector $\mathbf {u}$ scaled by the directional derivative in the direction of $\mathbf {u}$ in orange. The gradient vector is longer because the gradient points in the direction of greatest rate of increase of a function.

The *directional derivative* of a [scalar function](https://en.wikipedia.org/wiki/Scalar_function) 

$$
f(\mathbf {x} )=f(x_{1},x_{2},\ldots ,x_{n})
$$

 along a vector 

$$
\mathbf {v} =(v_{1},\ldots ,v_{n})
$$

 is the [function](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)") $\nabla _{\mathbf {v} }{f}$ defined by the [limit](https://en.wikipedia.org/wiki/Limit_(mathematics) "Limit (mathematics)") 

$$
\nabla _{\mathbf {v} }{f}(\mathbf {x} )=\lim _{h\to 0}{\frac {f(\mathbf {x} +h\mathbf {v} )-f(\mathbf {x} )}{h||\mathbf {v} ||}}=\left.{\frac {1}{||\mathbf {v} ||}}{\frac {\mathrm {d} }{\mathrm {d} t}}f(\mathbf {x} +t\mathbf {v} )\right|_{t=0}.
$$

This definition is valid in a broad range of contexts, for example, where the [norm](https://en.wikipedia.org/wiki/Euclidean_norm) of a vector (and hence a unit vector) is defined.

### For differentiable functions

If the function *f* is [differentiable](https://en.wikipedia.org/wiki/Differentiable_function#Differentiability_in_higher_dimensions) at **x**, then the directional derivative exists along any vector **v** at **x**, and one has

$$
\nabla _{\mathbf {v} }{f}(\mathbf {x} )=\nabla f(\mathbf {x} )\cdot {\frac {\mathbf {v} }{||\mathbf {v} ||}}
$$

where the $\nabla$ on the right denotes the *[gradient](https://en.wikipedia.org/wiki/Gradient)* and $\cdot$ is the [dot product](https://en.wikipedia.org/wiki/Dot_product).

It can be derived by using the property that all directional derivatives at a point make up a single tangent plane which can be defined using partial derivatives. This can be used to find a formula for the gradient vector and an alternative formula for the directional derivative, the latter of which can be rewritten as shown above for convenience.

It also follows from defining a path $h(t)=x+tv$ and using the definition of the derivative as a limit which can be calculated along this path to get: 

$$
{\begin{aligned}0&=\lim _{t\to 0}{\frac {f(x+t{\hat {v}})-f(x)-t\nabla f(x)\cdot {\hat {v}}}{t}}\\&=\lim _{t\to 0}{\frac {f(x+t{\hat {v}})-f(x)}{t}}-\nabla f(x)\cdot {\hat {v}}\\&=\nabla _{v}f(x)-\nabla f(x)\cdot {\hat {v}}.\\&\nabla f(x)\cdot {\hat {v}}=\nabla _{v}f(x)\end{aligned}}
$$

### Using only direction of vector

![[media/a5fd0cefb4a4c1108a28124c092425032fb08481.png]]
The angle <em>α</em> between the tangent <em>A</em> and the horizontal will be maximum if the cutting plane contains the direction of the gradient <em>A</em>.

In a [Euclidean space](https://en.wikipedia.org/wiki/Euclidean_space), some authors define the directional derivative to be with respect to an arbitrary nonzero vector **v** after [normalization](https://en.wikipedia.org/wiki/Normalized_vector), thus being independent of its magnitude and depending only on its direction.

This definition gives the rate of increase of *f* per unit of distance moved in the direction given by **v**. In this case, one has 

$$
\nabla _{\mathbf {v} }{f}(\mathbf {x} )=\lim _{h\to 0}{\frac {f(\mathbf {x} +h\mathbf {v} )-f(\mathbf {x} )}{h}},
$$

 or in case *f* is differentiable at **x**, 

$$
\nabla _{\mathbf {v} }{f}(\mathbf {x} )=\nabla f(\mathbf {x} )\cdot \mathbf {v} .
$$

### Restriction to a unit vector

In the context of a function on a [Euclidean space](https://en.wikipedia.org/wiki/Euclidean_space), some texts restrict the vector **v** to being a [unit vector](https://en.wikipedia.org/wiki/Unit_vector) for convention. Both of the above equations remain true, though redundant, when a vector is normalized.

## Properties

Many of the familiar properties of the ordinary [derivative](https://en.wikipedia.org/wiki/Derivative) hold for the directional derivative. These include, for any functions *f* and *g* defined in a [neighborhood](https://en.wikipedia.org/wiki/Neighborhood_(mathematics)) of, and [differentiable](https://en.wikipedia.org/wiki/Total_derivative) at, **p**:

1. **[sum rule](https://en.wikipedia.org/wiki/Sum_rule_in_differentiation)**: 

$$
\nabla _{\mathbf {v} }(f+g)=\nabla _{\mathbf {v} }f+\nabla _{\mathbf {v} }g.
$$

2. **[constant factor rule](https://en.wikipedia.org/wiki/Constant_factor_rule_in_differentiation)**: For any constant *c*, 

$$
\nabla _{\mathbf {v} }(cf)=c\nabla _{\mathbf {v} }f.
$$

3. **[product rule](https://en.wikipedia.org/wiki/Product_rule)** (or **Leibniz's rule**): 

$$
\nabla _{\mathbf {v} }(fg)=g\nabla _{\mathbf {v} }f+f\nabla _{\mathbf {v} }g.
$$

4. **[[Chain Rule]]**: If *g* is differentiable at **p** and *h* is differentiable at *g*(**p**), then 

$$
\nabla _{\mathbf {v} }(h\circ g)(\mathbf {p} )=h'(g(\mathbf {p} ))\nabla _{\mathbf {v} }g(\mathbf {p} ).
$$

## In differential geometry

Let *M* be a [differentiable manifold](https://en.wikipedia.org/wiki/Differentiable_manifold) and **p** a point of *M*. Suppose that *f* is a function defined in a neighborhood of **p**, and [differentiable](https://en.wikipedia.org/wiki/Total_derivative) at **p**. If **v** is a [tangent vector](https://en.wikipedia.org/wiki/Tangent_vector) to *M* at **p**, then the **directional derivative** of *f* along **v**, denoted variously as *df*(**v**) (see [Exterior derivative](https://en.wikipedia.org/wiki/Exterior_derivative)), $\nabla _{\mathbf {v} }f(\mathbf {p} )$ (see [Covariant derivative](https://en.wikipedia.org/wiki/Covariant_derivative)), $L_{\mathbf {v} }f(\mathbf {p} )$ (see [Lie derivative](https://en.wikipedia.org/wiki/Lie_derivative)), or ${\mathbf {v} }_{\mathbf {p} }(f)$ (see [[Tangent Space|Tangent space § Definition via derivations]]), can be defined as follows. Let *γ* : \[−1, 1\] → *M* be a differentiable curve with *γ*(0) = **p** and *γ*′(0) = **v**. Then the directional derivative is defined by 

$$
\nabla _{\mathbf {v} }f(\mathbf {p} )=\left.{\frac {d}{d\tau }}f\circ \gamma (\tau )\right|_{\tau =0}.
$$

 This definition can be proven independent of the choice of *γ*, provided *γ* is selected in the prescribed manner so that *γ*(0) = **p** and *γ*′(0) = **v**.

### The Lie derivative

The [Lie derivative](https://en.wikipedia.org/wiki/Lie_derivative) of a vector field $W^{\mu }(x)$ along a vector field $V^{\mu }(x)$ is given by the difference of two directional derivatives (with vanishing torsion): 

$$
{\mathcal {L}}_{V}W^{\mu }=(V\cdot \nabla )W^{\mu }-(W\cdot \nabla )V^{\mu }.
$$

 In particular, for a scalar field $\phi (x)$, the Lie derivative reduces to the standard directional derivative: 

$$
{\mathcal {L}}_{V}\phi =(V\cdot \nabla )\phi .
$$

### The Riemann tensor

Directional derivatives are often used in introductory derivations of the [Riemann curvature tensor](https://en.wikipedia.org/wiki/Riemann_curvature_tensor). Consider a curved rectangle with an infinitesimal vector $\delta$ along one edge and $\delta '$ along the other. We translate a covector $S$ along $\delta$ then $\delta '$ and then subtract the translation along $\delta '$ and then $\delta$. Instead of building the directional derivative using partial derivatives, we use the [covariant derivative](https://en.wikipedia.org/wiki/Covariant_derivative). The translation operator for $\delta$ is thus 

$$
1+\sum _{\nu }\delta ^{\nu }D_{\nu }=1+\delta \cdot D,
$$

 and for $\delta '$, 

$$
1+\sum _{\mu }\delta '^{\mu }D_{\mu }=1+\delta '\cdot D.
$$

 The difference between the two paths is then 

$$
(1+\delta '\cdot D)(1+\delta \cdot D)S^{\rho }-(1+\delta \cdot D)(1+\delta '\cdot D)S^{\rho }=\sum _{\mu ,\nu }\delta '^{\mu }\delta ^{\nu }[D_{\mu },D_{\nu }]S_{\rho }.
$$

 It can be argued that the noncommutativity of the covariant derivatives measures the curvature of the manifold: 

$$
[D_{\mu },D_{\nu }]S_{\rho }=\pm \sum _{\sigma }R^{\sigma }{}_{\rho \mu \nu }S_{\sigma },
$$

 where $R$ is the Riemann curvature tensor and the sign depends on the [sign convention](https://en.wikipedia.org/wiki/Sign_convention) of the author.

## In group theory

### Translations

In the [Poincaré algebra](https://en.wikipedia.org/wiki/Poincar%C3%A9_algebra), we can define an infinitesimal translation operator **P** as 

$$
\mathbf {P} =i\nabla .
$$

 (the *i* ensures that **P** is a [self-adjoint operator](https://en.wikipedia.org/wiki/Self-adjoint_operator)) For a finite displacement **λ**, the [unitary](https://en.wikipedia.org/wiki/Unitary_operator) [Hilbert space](https://en.wikipedia.org/wiki/Hilbert_space) [representation](https://en.wikipedia.org/wiki/Group_representation) for translations is 

$$
U({\boldsymbol {\lambda }})=\exp \left(-i{\boldsymbol {\lambda }}\cdot \mathbf {P} \right).
$$

 By using the above definition of the infinitesimal translation operator, we see that the finite translation operator is an exponentiated directional derivative: 

$$
U({\boldsymbol {\lambda }})=\exp \left({\boldsymbol {\lambda }}\cdot \nabla \right).
$$

 This is a translation operator in the sense that it acts on multivariable functions *f*(**x**) as 

$$
U({\boldsymbol {\lambda }})f(\mathbf {x} )=\exp \left({\boldsymbol {\lambda }}\cdot \nabla \right)f(\mathbf {x} )=f(\mathbf {x} +{\boldsymbol {\lambda }}).
$$

**Proof of the last equation**

In standard single-variable calculus, the derivative of a smooth function *f*(*x*) is defined by (for small *ε*) 

$$
{\frac {df}{dx}}={\frac {f(x+\varepsilon )-f(x)}{\varepsilon }}.
$$

 This can be rearranged to find *f*(*x*+*ε*): 

$$
f(x+\varepsilon )=f(x)+\varepsilon \,{\frac {df}{dx}}=\left(1+\varepsilon \,{\frac {d}{dx}}\right)f(x).
$$

 It follows that $[1+\varepsilon \,(d/dx)]$ is a translation operator. This is instantly generalized to multivariable functions *f*(**x**) 

$$
f(\mathbf {x} +{\boldsymbol {\varepsilon }})=\left(1+{\boldsymbol {\varepsilon }}\cdot \nabla \right)f(\mathbf {x} ).
$$

 Here ${\boldsymbol {\varepsilon }}\cdot \nabla$ is the directional derivative along the infinitesimal displacement ***ε***. We have found the infinitesimal version of the translation operator: 

$$
U({\boldsymbol {\varepsilon }})=1+{\boldsymbol {\varepsilon }}\cdot \nabla .
$$

 It is evident that the group multiplication law *U*(*g*)*U*(*f*)=*U*(*gf*) takes the form 

$$
U(\mathbf {a} )U(\mathbf {b} )=U(\mathbf {a+b} ).
$$

 So suppose that we take the finite displacement ***λ*** and divide it into *N* parts (*N*→∞ is implied everywhere), so that ***λ***/*N*=***ε***. In other words, 

$$
{\boldsymbol {\lambda }}=N{\boldsymbol {\varepsilon }}.
$$

 Then by applying *U*(***ε***) *N* times, we can construct *U*(***λ***): 

$$
[U({\boldsymbol {\varepsilon }})]^{N}=U(N{\boldsymbol {\varepsilon }})=U({\boldsymbol {\lambda }}).
$$

 We can now plug in our above expression for U(**ε**): 

$$
[U({\boldsymbol {\varepsilon }})]^{N}=\left[1+{\boldsymbol {\varepsilon }}\cdot \nabla \right]^{N}=\left[1+{\frac {{\boldsymbol {\lambda }}\cdot \nabla }{N}}\right]^{N}.
$$

 Using the identity 

$$
\exp(x)=\left[1+{\frac {x}{N}}\right]^{N},
$$

 we have 

$$
U({\boldsymbol {\lambda }})=\exp \left({\boldsymbol {\lambda }}\cdot \nabla \right).
$$

 And since *U*(***ε***)*f*(**x**) = *f*(**x**+***ε***) we have 

$$
[U({\boldsymbol {\varepsilon }})]^{N}f(\mathbf {x} )=f(\mathbf {x} +N{\boldsymbol {\varepsilon }})=f(\mathbf {x} +{\boldsymbol {\lambda }})=U({\boldsymbol {\lambda }})f(\mathbf {x} )=\exp \left({\boldsymbol {\lambda }}\cdot \nabla \right)f(\mathbf {x} ),
$$

 Q.E.D.

As a technical note, this procedure is only possible because the translation group forms an [Abelian](https://en.wikipedia.org/wiki/Abelian_group) [subgroup](https://en.wikipedia.org/wiki/Subgroup) ([Cartan subalgebra](https://en.wikipedia.org/wiki/Cartan_subalgebra)) in the Poincaré algebra. In particular, the group multiplication law *U*(**a**)*U*(**b**) = *U*(**a**+**b**) should not be taken for granted. We also note that Poincaré is a connected [Lie group](https://en.wikipedia.org/wiki/Lie_group). It is a group of transformations *T*(*ξ*) that are described by a continuous set of real parameters $\xi ^{a}$. The group multiplication law takes the form 

$$
T({\bar {\xi }})T(\xi )=T(f({\bar {\xi }},\xi )).
$$

 Taking $\xi ^{a}=0$ as the coordinates of the identity, we must have 

$$
f^{a}(\xi ,0)=f^{a}(0,\xi )=\xi ^{a}.
$$

 The actual operators on the Hilbert space are represented by unitary operators *U*(*T*(*ξ*)). In the above notation we suppressed the *T*; we now write *U*(**λ**) as *U*(**P**(**λ**)). For a small neighborhood around the identity, the [power series](https://en.wikipedia.org/wiki/Power_series) representation 

$$
U(T(\xi ))=1+i\sum _{a}\xi ^{a}t_{a}+{\frac {1}{2}}\sum _{b,c}\xi ^{b}\xi ^{c}t_{bc}+\cdots
$$

 is quite good. Suppose that U(T(ξ)) form a non-projective representation, i.e., 

$$
U(T({\bar {\xi }}))U(T(\xi ))=U(T(f({\bar {\xi }},\xi ))).
$$

 The expansion of f to second power is 

$$
f^{a}({\bar {\xi }},\xi )=\xi ^{a}+{\bar {\xi }}^{a}+\sum _{b,c}f^{abc}{\bar {\xi }}^{b}\xi ^{c}.
$$

 After expanding the representation multiplication equation and equating coefficients, we have the nontrivial condition 

$$
t_{bc}=-t_{b}t_{c}-i\sum _{a}f^{abc}t_{a}.
$$

 Since $t_{ab}$ is by definition symmetric in its indices, we have the standard [Lie algebra](https://en.wikipedia.org/wiki/Lie_algebra) commutator: 

$$
[t_{b},t_{c}]=i\sum _{a}(-f^{abc}+f^{acb})t_{a}=i\sum _{a}C^{abc}t_{a},
$$

 with *C* the [structure constant](https://en.wikipedia.org/wiki/Structure_constant). The generators for translations are partial derivative operators, which commute: 

$$
\left[{\frac {\partial }{\partial x^{b}}},{\frac {\partial }{\partial x^{c}}}\right]=0.
$$

 This implies that the structure constants vanish and thus the quadratic coefficients in the f expansion vanish as well. This means that *f* is simply additive: 

$$
f_{\text{abelian}}^{a}({\bar {\xi }},\xi )=\xi ^{a}+{\bar {\xi }}^{a},
$$

 and thus for abelian groups, 

$$
U(T({\bar {\xi }}))U(T(\xi ))=U(T({\bar {\xi }}+\xi )).
$$

 Q.E.D.

### Rotations

The [rotation operator](https://en.wikipedia.org/wiki/Rotation_operator_(quantum_mechanics) "Rotation operator (quantum mechanics)") also contains a directional derivative. The rotation operator for an angle ***θ***, i.e. by an amount *θ* = \|***θ***\| about an axis parallel to ${\hat {\theta }}={\boldsymbol {\theta }}/\theta$ is 

$$
U(R(\mathbf {\theta } ))=\exp(-i\mathbf {\theta } \cdot \mathbf {L} ).
$$

 Here **L** is the vector operator that generates [SO(3)](https://en.wikipedia.org/wiki/SO(3)): 

$$
\mathbf {L} ={\begin{pmatrix}0&0&0\\0&0&1\\0&-1&0\end{pmatrix}}\mathbf {i} +{\begin{pmatrix}0&0&-1\\0&0&0\\1&0&0\end{pmatrix}}\mathbf {j} +{\begin{pmatrix}0&1&0\\-1&0&0\\0&0&0\end{pmatrix}}\mathbf {k} .
$$

 It may be shown geometrically that an infinitesimal right-handed rotation changes the position vector **x** by 

$$
\mathbf {x} \rightarrow \mathbf {x} -\delta {\boldsymbol {\theta }}\times \mathbf {x} .
$$

 So we would expect under infinitesimal rotation: 

$$
U(R(\delta {\boldsymbol {\theta }}))f(\mathbf {x} )=f(\mathbf {x} -\delta {\boldsymbol {\theta }}\times \mathbf {x} )=f(\mathbf {x} )-(\delta {\boldsymbol {\theta }}\times \mathbf {x} )\cdot \nabla f.
$$

 It follows that 

$$
U(R(\delta \mathbf {\theta } ))=1-(\delta \mathbf {\theta } \times \mathbf {x} )\cdot \nabla .
$$

 Following the same exponentiation procedure as above, we arrive at the rotation operator in the position basis, which is an exponentiated directional derivative: 

$$
U(R(\mathbf {\theta } ))=\exp(-(\mathbf {\theta } \times \mathbf {x} )\cdot \nabla ).
$$

## Normal derivative

A **normal derivative** is a directional derivative taken in the direction normal (that is, [orthogonal](https://en.wikipedia.org/wiki/Orthogonal)) to some surface in space, or more generally along a [normal vector](https://en.wikipedia.org/wiki/Normal_vector) field orthogonal to some [hypersurface](https://en.wikipedia.org/wiki/Hypersurface). See for example [Neumann boundary condition](https://en.wikipedia.org/wiki/Neumann_boundary_condition). If the normal direction is denoted by $\mathbf {n}$, then the normal derivative of a function *f* is sometimes denoted as ${\frac {\partial f}{\partial \mathbf {n} }}$. In other notations, 

$$
{\frac {\partial f}{\partial \mathbf {n} }}=\nabla f(\mathbf {x} )\cdot \mathbf {n} =\nabla _{\mathbf {n} }{f}(\mathbf {x} )={\frac {\partial f}{\partial \mathbf {x} }}\cdot \mathbf {n} =Df(\mathbf {x} )[\mathbf {n} ].
$$

## In the continuum mechanics of solids

Several important results in continuum mechanics require the derivatives of vectors with respect to vectors and of [tensors](https://en.wikipedia.org/wiki/Tensors) with respect to vectors and tensors. The **directional directive** provides a systematic way of finding these derivatives.

The definitions of directional derivatives for various situations are given below. It is assumed that the functions are sufficiently smooth that derivatives can be taken.

### Derivatives of scalar valued functions of vectors

Let *f*(v) be a real valued function of the vector v. Then the derivative of *f*(v) with respect to v (or at v) is the vector defined through its [dot product](https://en.wikipedia.org/wiki/Dot_product) with any vector u being

$$
{\frac {\partial f}{\partial \mathbf {v} }}\cdot \mathbf {u} =Df(\mathbf {v} )[\mathbf {u} ]=\left[{\frac {d}{d\alpha }}~f(\mathbf {v} +\alpha ~\mathbf {u} )\right]_{\alpha =0}
$$

for all vectors u. The above dot product yields a scalar, and if u is a [unit vector](https://en.wikipedia.org/wiki/Unit_vector) gives the directional derivative of *f* at v, in the u direction.

Properties:

1. If $f(\mathbf {v} )=f_{1}(\mathbf {v} )+f_{2}(\mathbf {v} )$ then 

$$
{\frac {\partial f}{\partial \mathbf {v} }}\cdot \mathbf {u} =\left({\frac {\partial f_{1}}{\partial \mathbf {v} }}+{\frac {\partial f_{2}}{\partial \mathbf {v} }}\right)\cdot \mathbf {u}
$$

2. If $f(\mathbf {v} )=f_{1}(\mathbf {v} )~f_{2}(\mathbf {v} )$ then 

$$
{\frac {\partial f}{\partial \mathbf {v} }}\cdot \mathbf {u} =\left({\frac {\partial f_{1}}{\partial \mathbf {v} }}\cdot \mathbf {u} \right)~f_{2}(\mathbf {v} )+f_{1}(\mathbf {v} )~\left({\frac {\partial f_{2}}{\partial \mathbf {v} }}\cdot \mathbf {u} \right)
$$

3. If $f(\mathbf {v} )=f_{1}(f_{2}(\mathbf {v} ))$ then 

$$
{\frac {\partial f}{\partial \mathbf {v} }}\cdot \mathbf {u} ={\frac {\partial f_{1}}{\partial f_{2}}}~{\frac {\partial f_{2}}{\partial \mathbf {v} }}\cdot \mathbf {u}
$$

### Derivatives of vector valued functions of vectors

Let f(v) be a vector valued function of the vector v. Then the derivative of f(v) with respect to v (or at v) is the second order tensor defined through its dot product with any vector u being

$$
{\frac {\partial \mathbf {f} }{\partial \mathbf {v} }}\cdot \mathbf {u} =D\mathbf {f} (\mathbf {v} )[\mathbf {u} ]=\left[{\frac {d}{d\alpha }}~\mathbf {f} (\mathbf {v} +\alpha ~\mathbf {u} )\right]_{\alpha =0}
$$

for all vectors u. The above dot product yields a vector, and if u is a unit vector gives the direction derivative of f at v, in the directional u.

Properties:

1. If $\mathbf {f} (\mathbf {v} )=\mathbf {f} _{1}(\mathbf {v} )+\mathbf {f} _{2}(\mathbf {v} )$ then 

$$
{\frac {\partial \mathbf {f} }{\partial \mathbf {v} }}\cdot \mathbf {u} =\left({\frac {\partial \mathbf {f} _{1}}{\partial \mathbf {v} }}+{\frac {\partial \mathbf {f} _{2}}{\partial \mathbf {v} }}\right)\cdot \mathbf {u}
$$

2. If $\mathbf {f} (\mathbf {v} )=\mathbf {f} _{1}(\mathbf {v} )\times \mathbf {f} _{2}(\mathbf {v} )$ then 

$$
{\frac {\partial \mathbf {f} }{\partial \mathbf {v} }}\cdot \mathbf {u} =\left({\frac {\partial \mathbf {f} _{1}}{\partial \mathbf {v} }}\cdot \mathbf {u} \right)\times \mathbf {f} _{2}(\mathbf {v} )+\mathbf {f} _{1}(\mathbf {v} )\times \left({\frac {\partial \mathbf {f} _{2}}{\partial \mathbf {v} }}\cdot \mathbf {u} \right)
$$

3. If $\mathbf {f} (\mathbf {v} )=\mathbf {f} _{1}(\mathbf {f} _{2}(\mathbf {v} ))$ then 

$$
{\frac {\partial \mathbf {f} }{\partial \mathbf {v} }}\cdot \mathbf {u} ={\frac {\partial \mathbf {f} _{1}}{\partial \mathbf {f} _{2}}}\cdot \left({\frac {\partial \mathbf {f} _{2}}{\partial \mathbf {v} }}\cdot \mathbf {u} \right)
$$

### Derivatives of scalar valued functions of second-order tensors

Let $f({\boldsymbol {S}})$ be a real valued function of the second order tensor ${\boldsymbol {S}}$. Then the derivative of $f({\boldsymbol {S}})$ with respect to ${\boldsymbol {S}}$ (or at ${\boldsymbol {S}}$) in the direction ${\boldsymbol {T}}$ is the second order tensor defined as 

$$
{\frac {\partial f}{\partial {\boldsymbol {S}}}}:{\boldsymbol {T}}=Df({\boldsymbol {S}})[{\boldsymbol {T}}]=\left[{\frac {d}{d\alpha }}~f({\boldsymbol {S}}+\alpha ~{\boldsymbol {T}})\right]_{\alpha =0}
$$

 for all second order tensors ${\boldsymbol {T}}$.

Properties:

1. If $f({\boldsymbol {S}})=f_{1}({\boldsymbol {S}})+f_{2}({\boldsymbol {S}})$ then 

$$
{\frac {\partial f}{\partial {\boldsymbol {S}}}}:{\boldsymbol {T}}=\left({\frac {\partial f_{1}}{\partial {\boldsymbol {S}}}}+{\frac {\partial f_{2}}{\partial {\boldsymbol {S}}}}\right):{\boldsymbol {T}}
$$

2. If $f({\boldsymbol {S}})=f_{1}({\boldsymbol {S}})~f_{2}({\boldsymbol {S}})$ then 

$$
{\frac {\partial f}{\partial {\boldsymbol {S}}}}:{\boldsymbol {T}}=\left({\frac {\partial f_{1}}{\partial {\boldsymbol {S}}}}:{\boldsymbol {T}}\right)~f_{2}({\boldsymbol {S}})+f_{1}({\boldsymbol {S}})~\left({\frac {\partial f_{2}}{\partial {\boldsymbol {S}}}}:{\boldsymbol {T}}\right)
$$

3. If $f({\boldsymbol {S}})=f_{1}(f_{2}({\boldsymbol {S}}))$ then 

$$
{\frac {\partial f}{\partial {\boldsymbol {S}}}}:{\boldsymbol {T}}={\frac {\partial f_{1}}{\partial f_{2}}}~\left({\frac {\partial f_{2}}{\partial {\boldsymbol {S}}}}:{\boldsymbol {T}}\right)
$$

### Derivatives of tensor valued functions of second-order tensors

Let ${\boldsymbol {F}}({\boldsymbol {S}})$ be a second order tensor valued function of the second order tensor ${\boldsymbol {S}}$. Then the derivative of ${\boldsymbol {F}}({\boldsymbol {S}})$ with respect to ${\boldsymbol {S}}$ (or at ${\boldsymbol {S}}$) in the direction ${\boldsymbol {T}}$ is the fourth order tensor defined as 

$$
{\frac {\partial {\boldsymbol {F}}}{\partial {\boldsymbol {S}}}}:{\boldsymbol {T}}=D{\boldsymbol {F}}({\boldsymbol {S}})[{\boldsymbol {T}}]=\left[{\frac {d}{d\alpha }}~{\boldsymbol {F}}({\boldsymbol {S}}+\alpha ~{\boldsymbol {T}})\right]_{\alpha =0}
$$

 for all second order tensors ${\boldsymbol {T}}$.

Properties:

1. If ${\boldsymbol {F}}({\boldsymbol {S}})={\boldsymbol {F}}_{1}({\boldsymbol {S}})+{\boldsymbol {F}}_{2}({\boldsymbol {S}})$ then 

$$
{\frac {\partial {\boldsymbol {F}}}{\partial {\boldsymbol {S}}}}:{\boldsymbol {T}}=\left({\frac {\partial {\boldsymbol {F}}_{1}}{\partial {\boldsymbol {S}}}}+{\frac {\partial {\boldsymbol {F}}_{2}}{\partial {\boldsymbol {S}}}}\right):{\boldsymbol {T}}
$$

2. If ${\boldsymbol {F}}({\boldsymbol {S}})={\boldsymbol {F}}_{1}({\boldsymbol {S}})\cdot {\boldsymbol {F}}_{2}({\boldsymbol {S}})$ then 

$$
{\frac {\partial {\boldsymbol {F}}}{\partial {\boldsymbol {S}}}}:{\boldsymbol {T}}=\left({\frac {\partial {\boldsymbol {F}}_{1}}{\partial {\boldsymbol {S}}}}:{\boldsymbol {T}}\right)\cdot {\boldsymbol {F}}_{2}({\boldsymbol {S}})+{\boldsymbol {F}}_{1}({\boldsymbol {S}})\cdot \left({\frac {\partial {\boldsymbol {F}}_{2}}{\partial {\boldsymbol {S}}}}:{\boldsymbol {T}}\right)
$$

3. If ${\boldsymbol {F}}({\boldsymbol {S}})={\boldsymbol {F}}_{1}({\boldsymbol {F}}_{2}({\boldsymbol {S}}))$ then 

$$
{\frac {\partial {\boldsymbol {F}}}{\partial {\boldsymbol {S}}}}:{\boldsymbol {T}}={\frac {\partial {\boldsymbol {F}}_{1}}{\partial {\boldsymbol {F}}_{2}}}:\left({\frac {\partial {\boldsymbol {F}}_{2}}{\partial {\boldsymbol {S}}}}:{\boldsymbol {T}}\right)
$$

4. If $f({\boldsymbol {S}})=f_{1}({\boldsymbol {F}}_{2}({\boldsymbol {S}}))$ then 

$$
{\frac {\partial f}{\partial {\boldsymbol {S}}}}:{\boldsymbol {T}}={\frac {\partial f_{1}}{\partial {\boldsymbol {F}}_{2}}}:\left({\frac {\partial {\boldsymbol {F}}_{2}}{\partial {\boldsymbol {S}}}}:{\boldsymbol {T}}\right)
$$

## See also

- [Del in cylindrical and spherical coordinates](https://en.wikipedia.org/wiki/Del_in_cylindrical_and_spherical_coordinates) – Mathematical gradient operator in certain coordinate systems
- [Differential form](https://en.wikipedia.org/wiki/Differential_form) – Expression that may be integrated over a region
- [Ehresmann connection](https://en.wikipedia.org/wiki/Ehresmann_connection) – Differential geometry construct on fiber bundles
- [Fréchet derivative](https://en.wikipedia.org/wiki/Fr%C3%A9chet_derivative) – Derivative defined on normed spaces
- [Gateaux derivative](https://en.wikipedia.org/wiki/Gateaux_derivative) – Generalization of the concept of directional derivative
- [Generalizations of the derivative](https://en.wikipedia.org/wiki/Generalizations_of_the_derivative) – Fundamental construction of differential calculus
- [Semi-differentiability](https://en.wikipedia.org/wiki/Semi-differentiability) – Property of a mathematical function
- [Hadamard derivative](https://en.wikipedia.org/wiki/Hadamard_derivative)
- [Lie derivative](https://en.wikipedia.org/wiki/Lie_derivative) – Type of derivative in differential geometry
- [Material derivative](https://en.wikipedia.org/wiki/Material_derivative) – Time rate of change of some physical quantity of a material element in a velocity field
- [Structure tensor](https://en.wikipedia.org/wiki/Structure_tensor) – Tensor related to gradients
- [Tensor derivative (continuum mechanics)](https://en.wikipedia.org/wiki/Tensor_derivative_(continuum_mechanics) "Tensor derivative (continuum mechanics)")
- [Total derivative](https://en.wikipedia.org/wiki/Total_derivative) – Type of derivative in mathematics

## Notes

1. R. Wrede; M.R. Spiegel (2010). *Advanced Calculus* (3rd ed.). Schaum's Outline Series. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-07-162366-7](https://en.wikipedia.org/wiki/Special:BookSources/978-0-07-162366-7).
2. The applicability extends to functions over spaces without a [metric](https://en.wikipedia.org/wiki/Metric_(mathematics)) and to [differentiable manifolds](https://en.wikipedia.org/wiki/Differentiable_manifold), such as in [general relativity](https://en.wikipedia.org/wiki/General_relativity).
3. If the dot product is undefined, the [gradient](https://en.wikipedia.org/wiki/Gradient) is also undefined; however, for differentiable *f*, the directional derivative is still defined, and a similar relation exists with the exterior derivative.
4. Thomas, George B. Jr.; and Finney, Ross L. (1979) *Calculus and Analytic Geometry*, Addison-Wesley Publ. Co., fifth edition, p. 593.
5. This typically assumes a [Euclidean space](https://en.wikipedia.org/wiki/Euclidean_space) – for example, a function of several variables typically has no definition of the magnitude of a vector, and hence of a unit vector.
6. [Hughes Hallett, Deborah](https://en.wikipedia.org/wiki/Deborah_Hughes_Hallett); [McCallum, William G.](https://en.wikipedia.org/wiki/William_G._McCallum); [Gleason, Andrew M.](https://en.wikipedia.org/wiki/Andrew_M._Gleason) (2012-01-01). *Calculus : Single and multivariable*. John wiley. p. 780. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780470888612](https://en.wikipedia.org/wiki/Special:BookSources/9780470888612). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [828768012](https://search.worldcat.org/oclc/828768012).
7. [Zee, A.](https://en.wikipedia.org/wiki/Anthony_Zee) (2013). [*Einstein Gravity in a Nutshell*](https://en.wikipedia.org/wiki/Einstein_Gravity_in_a_Nutshell). Princeton: Princeton University Press. p. 341. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780691145587](https://en.wikipedia.org/wiki/Special:BookSources/9780691145587).
8. Weinberg, Steven (1999). [The quantum theory of fields](https://archive.org/details/quantumtheoryoff00stev) (Reprinted (with corr.). ed.). Cambridge \[u.a.\]: Cambridge Univ. Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780521550017](https://en.wikipedia.org/wiki/Special:BookSources/9780521550017).
9. Zee, A. (2013). *Einstein gravity in a nutshell*. Princeton: Princeton University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780691145587](https://en.wikipedia.org/wiki/Special:BookSources/9780691145587).
10. Cahill, Kevin Cahill (2013). *Physical mathematics* (Repr. ed.). Cambridge: Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1107005211](https://en.wikipedia.org/wiki/Special:BookSources/978-1107005211).
11. Larson, Ron; Edwards, Bruce H. (2010). *Calculus of a single variable* (9th ed.). Belmont: Brooks/Cole. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780547209982](https://en.wikipedia.org/wiki/Special:BookSources/9780547209982).
12. Shankar, R. (1994). *Principles of quantum mechanics* (2nd ed.). New York: Kluwer Academic / Plenum. p. 318. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780306447907](https://en.wikipedia.org/wiki/Special:BookSources/9780306447907).
13. J. E. Marsden and T. J. R. Hughes, 2000, *Mathematical Foundations of Elasticity*, Dover.

## References

- Hildebrand, F. B. (1976). *Advanced Calculus for Applications*. Prentice Hall. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-13-011189-9](https://en.wikipedia.org/wiki/Special:BookSources/0-13-011189-9).
- K.F. Riley; M.P. Hobson; S.J. Bence (2010). [Mathematical methods for physics and engineering](https://archive.org/details/mathematicalmeth00rile). Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-86153-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-86153-3).
- Shapiro, A. (1990). "On concepts of directional differentiability". *Journal of Optimization Theory and Applications*. **66** (3): 477–487. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/BF00940933](https://doi.org/10.1007%2FBF00940933). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [120253580](https://api.semanticscholar.org/CorpusID:120253580).

## External links

![[media/62933b50408636b28d12e90be87b5b81874d2f90.png]] Media related to [Directional derivative](https://commons.wikimedia.org/wiki/Category:Directional_derivative) at Wikimedia Commons

- [Directional derivatives](http://mathworld.wolfram.com/DirectionalDerivative.html) at [MathWorld](https://en.wikipedia.org/wiki/MathWorld).
- [Directional derivative](https://planetmath.org/directionalderivative) at [PlanetMath](https://en.wikipedia.org/wiki/PlanetMath).
