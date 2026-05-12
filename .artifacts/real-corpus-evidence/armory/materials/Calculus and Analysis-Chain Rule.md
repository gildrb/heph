[[calculus-analysis.base]]

> Source: [[Chain Rule]]
> License: Wikipedia content is available under CC BY-SA 4.0.

In [calculus](https://en.wikipedia.org/wiki/Calculus), the **chain rule** is a [formula](https://en.wikipedia.org/wiki/Formula) that expresses the [derivative](https://en.wikipedia.org/wiki/Derivative) of the [composition](https://en.wikipedia.org/wiki/Function_composition) of two [differentiable functions](https://en.wikipedia.org/wiki/Differentiable_function) z and y in terms of the derivatives of z and y. More precisely, if $h=z\circ y$ is the composition such that $h(x)=z(y(x))$ for every x, then the chain rule is, in [Lagrange's notation](https://en.wikipedia.org/wiki/Lagrange%27s_notation), 

$$
h'(x)=z'(y(x))y'(x).
$$

 or, equivalently, 

$$
h'=(z\circ y)'=(z'\circ y)\cdot y'.
$$

The chain rule may also be expressed in [Leibniz's notation](https://en.wikipedia.org/wiki/Leibniz%27s_notation). If a variable z depends on the variable y, which itself depends on the variable x (that is, y and z are [dependent variables](https://en.wikipedia.org/wiki/Dependent_variable)), then z depends on x as well, via the intermediate variable y. In this case, the chain rule is expressed as 

$$
{\frac {dz}{dx}}={\frac {dz}{dy}}\cdot {\frac {dy}{dx}},
$$

 and 

$$
\left.{\frac {dz}{dx}}\right|_{x}=\left.{\frac {dz}{dy}}\right|_{y(x)}\cdot \left.{\frac {dy}{dx}}\right|_{x},
$$

 for indicating at which points the derivatives have to be evaluated.

In [integration](https://en.wikipedia.org/wiki/Integral), the counterpart to the chain rule is the [substitution rule](https://en.wikipedia.org/wiki/Substitution_rule).

## Intuitive explanation

Intuitively, the chain rule states that knowing the instantaneous rate of change of *z* relative to *y* and that of *y* relative to *x* allows one to calculate the instantaneous rate of change of *z* relative to *x* as the product of the two rates of change.

As put by [George F. Simmons](https://en.wikipedia.org/wiki/George_F._Simmons): "If a car travels twice as fast as a bicycle and the bicycle is four times as fast as a walking man, then the car travels 2 × 4 = 8 times as fast as the man."

The relationship between this example and the chain rule is as follows. Let z, y and x be the (variable) positions of the car, the bicycle, and the walking man, respectively. The rate of change of relative positions of the car and the bicycle is ${\frac {dz}{dy}}=2.$ Similarly, ${\frac {dy}{dx}}=4.$ So, the rate of change of the relative positions of the car and the walking man is 

$$
{\frac {dz}{dx}}={\frac {dz}{dy}}\cdot {\frac {dy}{dx}}=2\cdot 4=8.
$$

The rate of change of positions is the ratio of the speeds, and the speed is the derivative of the position with respect to the time; that is, 

$$
{\frac {dz}{dx}}={\frac {\frac {dz}{dt}}{\frac {dx}{dt}}},
$$

 or, equivalently, 

$$
{\frac {dz}{dt}}={\frac {dz}{dx}}\cdot {\frac {dx}{dt}},
$$

 which is also an application of the chain rule.

## History

The chain rule seems to have first been used by [Gottfried Wilhelm Leibniz](https://en.wikipedia.org/wiki/Gottfried_Wilhelm_Leibniz). He used it to calculate the derivative of ${\sqrt {a+bz+cz^{2}}}$ as the composite of the square root function and the function $a+bz+cz^{2}\!$. He first mentioned it in a 1676 memoir (with a sign error in the calculation). The common notation of the chain rule is due to Leibniz. [Guillaume de l'Hôpital](https://en.wikipedia.org/wiki/Guillaume_de_l%27H%C3%B4pital) used the chain rule implicitly in his *[Analyse des infiniment petits](https://en.wikipedia.org/wiki/Analyse_des_infiniment_petits)*. The chain rule does not appear in any of [Leonhard Euler](https://en.wikipedia.org/wiki/Leonhard_Euler)'s analysis books, even though they were written over a hundred years after Leibniz's discovery. It is believed that the first "modern" version of the chain rule appears in Lagrange's 1797 *Théorie des fonctions analytiques*; it also appears in Cauchy's 1823 *Résumé des Leçons données a L’École Royale Polytechnique sur Le Calcul Infinitesimal*.

## Statement

The simplest form of the chain rule is for real-valued functions of one [real](https://en.wikipedia.org/wiki/Real_number) variable. It states that if *g* is a function that is differentiable at a point *c* (i.e. the derivative *g*′(*c*) exists) and *f* is a function that is differentiable at *g*(*c*), then the composite function $f\circ g$ is differentiable at *c*, and the derivative is 

$$
(f\circ g)'(c)=f'(g(c))\cdot g'(c).
$$

 The rule is sometimes abbreviated as 

$$
(f\circ g)'=(f'\circ g)\cdot g'.
$$

If *y* = *f*(*u*) and *u* = *g*(*x*), then this abbreviated form is written in [Leibniz notation](https://en.wikipedia.org/wiki/Leibniz_notation) as: 

$$
{\frac {dy}{dx}}={\frac {dy}{du}}\cdot {\frac {du}{dx}}.
$$

The points where the derivatives are evaluated may also be stated explicitly: 

$$
\left.{\frac {dy}{dx}}\right|_{x=c}=\left.{\frac {dy}{du}}\right|_{u=g(c)}\cdot \left.{\frac {du}{dx}}\right|_{x=c}.
$$

Carrying the same reasoning further, given *n* functions $f_{1},\ldots ,f_{n}\!$ with the composite function $f_{1}\circ (f_{2}\circ \cdots (f_{n-1}\circ f_{n}))\!$, if each function $f_{i}\!$ is differentiable at its immediate input, then the composite function is also differentiable by the repeated application of Chain Rule, where the derivative is (in Leibniz's notation): 

$$
{\frac {df_{1}}{dx}}={\frac {df_{1}}{df_{2}}}{\frac {df_{2}}{df_{3}}}\cdots {\frac {df_{n}}{dx}}.
$$

## Applications

![[media/384025ccbe71ab8e770c1168f00d90f40a5063fc.png]]
The chain rule in case of composites of more than two functions

### Composites of more than two functions

The chain rule can be applied to composites of more than two functions. To take the derivative of a composite of more than two functions, notice that the composite of f, g, and *h* (in that order) is the composite of f with *g* ∘ *h*. The chain rule states that to compute the derivative of *f* ∘ *g* ∘ *h*, it is sufficient to compute the derivative of *f* and the derivative of *g* ∘ *h*. The derivative of f can be calculated directly, and the derivative of *g* ∘ *h* can be calculated by applying the chain rule again.

For concreteness, consider the function 

$$
y=e^{\sin(x^{2})}.
$$

 This can be decomposed as the composite of three functions: 

$$
{\begin{aligned}y&=f(u)=e^{u},\\u&=g(v)=\sin v,\\v&=h(x)=x^{2}.\end{aligned}}
$$

 So that $y=f(g(h(x)))$.

Their derivatives are: 

$$
{\begin{aligned}{\frac {dy}{du}}&=f'(u)=e^{u},\\{\frac {du}{dv}}&=g'(v)=\cos v,\\{\frac {dv}{dx}}&=h'(x)=2x.\end{aligned}}
$$

The chain rule states that the derivative of their composite at the point *x* = *a* is: 

$$
{\begin{aligned}(f\circ g\circ h)'(a)&=f'((g\circ h)(a))\cdot (g\circ h)'(a)\\&=f'((g\circ h)(a))\cdot g'(h(a))\cdot h'(a)\\&=(f'\circ g\circ h)(a)\cdot (g'\circ h)(a)\cdot h'(a).\end{aligned}}
$$

In [Leibniz's notation](https://en.wikipedia.org/wiki/Leibniz%27s_notation), this is: 

$$
{\frac {dy}{dx}}=\left.{\frac {dy}{du}}\right|_{u=g(h(a))}\cdot \left.{\frac {du}{dv}}\right|_{v=h(a)}\cdot \left.{\frac {dv}{dx}}\right|_{x=a},
$$

 or for short, 

$$
{\frac {dy}{dx}}={\frac {dy}{du}}\cdot {\frac {du}{dv}}\cdot {\frac {dv}{dx}}.
$$

 The derivative function is therefore: 

$$
{\frac {dy}{dx}}=e^{\sin(x^{2})}\cdot \cos(x^{2})\cdot 2x.
$$

Another way of computing this derivative is to view the composite function *f* ∘ *g* ∘ *h* as the composite of *f* ∘ *g* and *h*. Applying the chain rule in this manner would yield: 

$$
{\begin{aligned}(f\circ g\circ h)'(a)&=(f\circ g)'(h(a))\cdot h'(a)\\&=f'(g(h(a)))\cdot g'(h(a))\cdot h'(a).\end{aligned}}
$$

This is the same as what was computed above. This should be expected because (*f* ∘ *g*) ∘ *h* = *f* ∘ (*g* ∘ *h*).

Sometimes, it is necessary to differentiate an arbitrarily long composition of the form $f_{1}\circ f_{2}\circ \cdots \circ f_{n-1}\circ f_{n}\!$. In this case, define 

$$
f_{a\,.\,.\,b}=f_{a}\circ f_{a+1}\circ \cdots \circ f_{b-1}\circ f_{b}
$$

 where $f_{a\,.\,.\,a}=f_{a}$ and $f_{a\,.\,.\,b}(x)=x$ when $b<a$. Then the chain rule takes the form 

$$
{\begin{aligned}Df_{1\,.\,.\,n}&=(Df_{1}\circ f_{2\,.\,.\,n})(Df_{2}\circ f_{3\,.\,.\,n})\cdots (Df_{n-1}\circ f_{n\,.\,.\,n})Df_{n}\\&=\prod _{k=1}^{n}\left[Df_{k}\circ f_{(k+1)\,.\,.\,n}\right]\end{aligned}}
$$

 or, in the Lagrange notation, 

$$
{\begin{aligned}f_{1\,.\,.\,n}'(x)&=f_{1}'\left(f_{2\,.\,.\,n}(x)\right)\;f_{2}'\left(f_{3\,.\,.\,n}(x)\right)\cdots f_{n-1}'\left(f_{n\,.\,.\,n}(x)\right)\;f_{n}'(x)\\[1ex]&=\prod _{k=1}^{n}f_{k}'\left(f_{(k+1\,.\,.\,n)}(x)\right)\end{aligned}}
$$

### Quotient rule

The chain rule can be used to derive some well-known differentiation rules. For example, the quotient rule is a consequence of the chain rule and the [product rule](https://en.wikipedia.org/wiki/Product_rule). To see this, write the function *f*(*x*)/*g*(*x*) as the product *f*(*x*) · 1/*g*(*x*). First apply the product rule: 

$$
{\begin{aligned}{\frac {d}{dx}}\left({\frac {f(x)}{g(x)}}\right)&={\frac {d}{dx}}\left(f(x)\cdot {\frac {1}{g(x)}}\right)\\&=f'(x)\cdot {\frac {1}{g(x)}}+f(x)\cdot {\frac {d}{dx}}\left({\frac {1}{g(x)}}\right).\end{aligned}}
$$

To compute the derivative of 1/*g*(*x*), notice that it is the composite of g with the reciprocal function, that is, the function that sends x to 1/*x*. The derivative of the reciprocal function is $-1/x^{2}\!$. By applying the chain rule, the last expression becomes: 

$$
f'(x)\cdot {\frac {1}{g(x)}}+f(x)\cdot \left(-{\frac {1}{g(x)^{2}}}\cdot g'(x)\right)={\frac {f'(x)g(x)-f(x)g'(x)}{g(x)^{2}}},
$$

 which is the usual formula for the quotient rule.

### Derivatives of inverse functions

Suppose that *y* = *g*(*x*) has an [inverse function](https://en.wikipedia.org/wiki/Inverse_function). Call its inverse function f so that we have *x* = *f*(*y*). There is a formula for the derivative of f in terms of the derivative of g. To see this, note that f and g satisfy the formula 

$$
f(g(x))=x.
$$

And because the functions $f(g(x))$ and x are equal, their derivatives must be equal. The derivative of x is the constant function with value 1, and the derivative of $f(g(x))$ is determined by the chain rule. Therefore, we have that: 

$$
f'(g(x))g'(x)=1.
$$

To express f' as a function of an independent variable y, we substitute $f(y)$ for x wherever it appears. Then we can solve for f'. 

$$
{\begin{aligned}f'(g(f(y)))g'(f(y))&=1\\f'(y)g'(f(y))&=1\\f'(y)={\frac {1}{g'(f(y))}}.\end{aligned}}
$$

For example, consider the function *g*(*x*) = *e**x*. It has an inverse *f*(*y*) = ln *y*. Because *g*′(*x*) = *e**x*, the above formula says that 

$$
{\frac {d}{dy}}\ln y={\frac {1}{e^{\ln y}}}={\frac {1}{y}}.
$$

This formula is true whenever g is differentiable and its inverse f is also differentiable. This formula can fail when one of these conditions is not true. For example, consider *g*(*x*) = *x*3. Its inverse is *f*(*y*) = *y*1/3, which is not differentiable at zero. If we attempt to use the above formula to compute the derivative of f at zero, then we must evaluate 1/*g*′(*f*(0)). Since *f*(0) = 0 and *g*′(0) = 0, we must evaluate 1/0, which is undefined. Therefore, the formula fails in this case. This is not surprising because f is not differentiable at zero.

### Back propagation

The chain rule forms the basis of the [back propagation](https://en.wikipedia.org/wiki/Back_propagation) algorithm, which is used in [[Gradient Descent]] of [neural networks](https://en.wikipedia.org/wiki/Neural_network_(machine_learning) "Neural network (machine learning)") in [deep learning](https://en.wikipedia.org/wiki/Deep_learning) ([artificial intelligence](https://en.wikipedia.org/wiki/Artificial_intelligence)).

## Higher derivatives

[Faà di Bruno's formula](https://en.wikipedia.org/wiki/Fa%C3%A0_di_Bruno%27s_formula) generalizes the chain rule to higher derivatives. Assuming that *y* = *f*(*u*) and *u* = *g*(*x*), then the first few derivatives are: 

$$
{\begin{aligned}{\frac {dy}{dx}}&={\frac {dy}{du}}{\frac {du}{dx}}\\{\frac {d^{2}y}{dx^{2}}}&={\frac {d^{2}y}{du^{2}}}\left({\frac {du}{dx}}\right)^{2}+{\frac {dy}{du}}{\frac {d^{2}u}{dx^{2}}}\\{\frac {d^{3}y}{dx^{3}}}&={\frac {d^{3}y}{du^{3}}}\left({\frac {du}{dx}}\right)^{3}+3\,{\frac {d^{2}y}{du^{2}}}{\frac {du}{dx}}{\frac {d^{2}u}{dx^{2}}}+{\frac {dy}{du}}{\frac {d^{3}u}{dx^{3}}}\\{\frac {d^{4}y}{dx^{4}}}&={\frac {d^{4}y}{du^{4}}}\left({\frac {du}{dx}}\right)^{4}+6\,{\frac {d^{3}y}{du^{3}}}\left({\frac {du}{dx}}\right)^{2}{\frac {d^{2}u}{dx^{2}}}+{\frac {d^{2}y}{du^{2}}}\left(4\,{\frac {du}{dx}}{\frac {d^{3}u}{dx^{3}}}+3\,\left({\frac {d^{2}u}{dx^{2}}}\right)^{2}\right)+{\frac {dy}{du}}{\frac {d^{4}u}{dx^{4}}}.\end{aligned}}
$$

## Proofs

### First proof

One proof of the chain rule begins by defining the derivative of the composite function *f* ∘ *g*, where we take the [limit](https://en.wikipedia.org/wiki/Limit_of_a_function) of the [difference quotient](https://en.wikipedia.org/wiki/Difference_quotient) for *f* ∘ *g* as x approaches a: 

$$
(f\circ g)'(a)=\lim _{x\to a}{\frac {f(g(x))-f(g(a))}{x-a}}.
$$

Assume for the moment that $g(x)\!$ does not equal $g(a)$ for any $x$ near $a$. Then the previous expression is equal to the product of two factors: 

$$
\lim _{x\to a}{\frac {f(g(x))-f(g(a))}{g(x)-g(a)}}\cdot {\frac {g(x)-g(a)}{x-a}}.
$$

If $g$ oscillates near a, then it might happen that no matter how close one gets to a, there is always an even closer x such that *g*(*x*) = *g*(*a*). For example, this happens near *a* = 0 for the [continuous function](https://en.wikipedia.org/wiki/Continuous_function) g defined by *g*(*x*) = 0 for *x* = 0 and *g*(*x*) = *x*2 sin(1/*x*) otherwise. Whenever this happens, the above expression is undefined because it involves [division by zero](https://en.wikipedia.org/wiki/Division_by_zero). To work around this, introduce a function $Q$ as follows: 

$$
Q(y)={\begin{cases}\displaystyle {\frac {f(y)-f(g(a))}{y-g(a)}},&y\neq g(a),\\f'(g(a)),&y=g(a).\end{cases}}
$$

 We will show that the difference quotient for *f* ∘ *g* is always equal to: 

$$
Q(g(x))\cdot {\frac {g(x)-g(a)}{x-a}}.
$$

Whenever *g*(*x*) is not equal to *g*(*a*), this is clear because the factors of *g*(*x*) − *g*(*a*) cancel. When *g*(*x*) equals *g*(*a*), then the difference quotient for *f* ∘ *g* is zero because *f*(*g*(*x*)) equals *f*(*g*(*a*)), and the above product is zero because it equals *f*′(*g*(*a*)) times zero. So the above product is always equal to the difference quotient, and to show that the derivative of *f* ∘ *g* at *a* exists and to determine its value, we need only show that the limit as *x* goes to *a* of the above product exists and determine its value.

To do this, recall that the limit of a product exists if the limits of its factors exist. When this happens, the limit of the product of these two factors will equal the product of the limits of the factors. The two factors are *Q*(*g*(*x*)) and (*g*(*x*) − *g*(*a*)) / (*x* − *a*). The latter is the difference quotient for g at a, and because g is differentiable at a by assumption, its limit as x tends to a exists and equals *g*′(*a*).

As for *Q*(*g*(*x*)), notice that *Q* is defined wherever *f* is. Furthermore, *f* is differentiable at *g*(*a*) by assumption, so *Q* is continuous at *g*(*a*), by definition of the derivative. The function g is continuous at a because it is differentiable at a, and therefore *Q* ∘ *g* is continuous at a. So its limit as *x* goes to *a* exists and equals *Q*(*g*(*a*)), which is *f*′(*g*(*a*)).

This shows that the limits of both factors exist and that they equal *f*′(*g*(*a*)) and *g*′(*a*), respectively. Therefore, the derivative of *f* ∘ *g* at *a* exists and equals *f*′(*g*(*a*))*g*′(*a*).

### Second proof

Another way of proving the chain rule is to measure the error in the linear approximation determined by the derivative. This proof has the advantage that it generalizes to several variables. It relies on the following equivalent definition of differentiability at a point: A function *g* is differentiable at *a* if there exists a real number *g*′(*a*) and a function *ε*(*h*) that tends to zero as *h* tends to zero, and furthermore 

$$
g(a+h)-g(a)=g'(a)h+\varepsilon (h)h.
$$

 Here the left-hand side represents the true difference between the value of *g* at *a* and at *a* + *h*, whereas the right-hand side represents the approximation determined by the derivative plus an error term.

In the situation of the chain rule, such a function *ε* exists because *g* is assumed to be differentiable at *a*. Again by assumption, a similar function also exists for *f* at *g*(*a*). Calling this function *η*, we have 

$$
f(g(a)+k)-f(g(a))=f'(g(a))k+\eta (k)k.
$$

 The above definition imposes no constraints on *η*(0), even though it is assumed that *η*(*k*) tends to zero as *k* tends to zero. If we set *η*(0) = 0, then *η* is continuous at 0.

Proving the theorem requires studying the difference *f*(*g*(*a* + *h*)) − *f*(*g*(*a*)) as *h* tends to zero. The first step is to substitute for *g*(*a* + *h*) using the definition of differentiability of *g* at *a*: 

$$
f(g(a+h))-f(g(a))=f(g(a)+g'(a)h+\varepsilon (h)h)-f(g(a)).
$$

 The next step is to use the definition of differentiability of *f* at *g*(*a*). This requires a term of the form *f*(*g*(*a*) + *k*) for some *k*. In the above equation, the correct *k* varies with *h*. Set *k*<sub>*h*</sub> = *g*′(*a*) *h* + *ε*(*h*) *h* and the right hand side becomes *f*(*g*(*a*) + *k*<sub>*h*</sub>) − *f*(*g*(*a*)). Applying the definition of the derivative gives: 

$$
f(g(a)+k_{h})-f(g(a))=f'(g(a))k_{h}+\eta (k_{h})k_{h}.
$$

 To study the behavior of this expression as *h* tends to zero, expand *k*<sub>*h*</sub>. After regrouping the terms, the right-hand side becomes: 

$$
f'(g(a))g'(a)h+[f'(g(a))\varepsilon (h)+\eta (k_{h})g'(a)+\eta (k_{h})\varepsilon (h)]h.
$$

 Because *ε*(*h*) and *η*(*k*<sub>*h*</sub>) tend to zero as *h* tends to zero, the first two bracketed terms tend to zero as *h* tends to zero. Applying the same theorem on products of limits as in the first proof, the third bracketed term also tends zero. Because the above expression is equal to the difference *f*(*g*(*a* + *h*)) − *f*(*g*(*a*)), by the definition of the derivative *f* ∘ *g* is differentiable at *a* and its derivative is *f*′(*g*(*a*)) *g*′(*a*).

The role of *Q* in the first proof is played by *η* in this proof. They are related by the equation: 

$$
Q(y)=f'(g(a))+\eta (y-g(a)).
$$

 The need to define *Q* at *g*(*a*) is analogous to the need to define *η* at zero.

### Third proof

[Constantin Carathéodory](https://en.wikipedia.org/wiki/Constantin_Carath%C3%A9odory)'s alternative definition of the differentiability of a function can be used to give an elegant proof of the chain rule.

Under this definition, a function f is differentiable at a point a if and only if there is a function q, continuous at a and such that *f*(*x*) − *f*(*a*) = *q*(*x*)(*x* − *a*). There is at most one such function, and if f is differentiable at a then *f* ′(*a*) = *q*(*a*).

Given the assumptions of the chain rule and the fact that differentiable functions and compositions of continuous functions are continuous, we have that there exist functions q, continuous at *g*(*a*), and r, continuous at a, and such that, 

$$
f(g(x))-f(g(a))=q(g(x))(g(x)-g(a))
$$

 and 

$$
g(x)-g(a)=r(x)(x-a).
$$

 Therefore, 

$$
f(g(x))-f(g(a))=q(g(x))r(x)(x-a),
$$

 but the function given by *h*(*x*) = *q*(*g*(*x*))*r*(*x*) is continuous at a, and we get, for this a 

$$
(f(g(a)))'=q(g(a))r(a)=f'(g(a))g'(a).
$$

 A similar approach works for continuously differentiable (vector-)functions of many variables. This method of factoring also allows a unified approach to stronger forms of differentiability, when the derivative is required to be [Lipschitz continuous](https://en.wikipedia.org/wiki/Lipschitz_continuity), [Hölder continuous](https://en.wikipedia.org/wiki/H%C3%B6lder_condition), etc. Differentiation itself can be viewed as the [polynomial remainder theorem](https://en.wikipedia.org/wiki/Polynomial_remainder_theorem) (the little [Bézout](https://en.wikipedia.org/wiki/%C3%89tienne_B%C3%A9zout) theorem, or factor theorem), generalized to an appropriate class of functions.\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]

## Multivariable case

The full generalization of the chain rule to [multi-variable functions](https://en.wikipedia.org/wiki/Multi-variable_function) (such as $f\colon \mathbb {R} ^{m}\to \mathbb {R} ^{n}$) is rather technical. However, it is simpler to write in the case of functions of the form 

$$
f(g_{1}(x),\dots ,g_{k}(x)),
$$

 where $f\colon \mathbb {R} ^{k}\to \mathbb {R}$, and $g_{i}\colon \mathbb {R} \to \mathbb {R}$ for each $i=1,2,\dots ,k.$

As this case occurs often in the study of functions of a single variable, it is worth describing it separately.

### Case of scalar-valued multivariate functions

Let $f\colon \mathbb {R} ^{k}\to \mathbb {R}$, and $g_{i}\colon \mathbb {R} \to \mathbb {R}$ for each $i=1,2,\dots ,k.$ To write the chain rule for the composition of functions 

$$
x\mapsto f(g_{1}(x),\dots ,g_{k}(x)),
$$

 one needs the [partial derivatives](https://en.wikipedia.org/wiki/Partial_derivative) of f with respect to its k arguments. The usual notations for partial derivatives involve names for the arguments of the function. As these arguments are not named in the above formula, it is simpler and clearer to use [*D*-Notation](https://en.wikipedia.org/wiki/Notation_for_differentiation#D-notation), and to denote by 

$$
D_{i}f
$$

 the partial derivative of f with respect to its ith argument, and by 

$$
D_{i}f(z)
$$

 the value of this derivative at z.

With this notation, the chain rule is 

$$
{\frac {d}{dx}}f(g_{1}(x),\dots ,g_{k}(x))=\sum _{i=1}^{k}\left({\frac {d}{dx}}{g_{i}}(x)\right)D_{i}f(g_{1}(x),\dots ,g_{k}(x)).
$$

#### Example: arithmetic operations

If the function f is addition, that is, if 

$$
f(u,v)=u+v,
$$

 then $D_{1}f={\frac {\partial f}{\partial u}}=1$ and $D_{2}f={\frac {\partial f}{\partial v}}=1$. Thus, the chain rule gives 

$$
{\frac {d}{dx}}(g(x)+h(x))=\left({\frac {d}{dx}}g(x)\right)D_{1}f+\left({\frac {d}{dx}}h(x)\right)D_{2}f={\frac {d}{dx}}g(x)+{\frac {d}{dx}}h(x).
$$

For multiplication 

$$
f(u,v)=uv,
$$

 the partials are $D_{1}f=v$ and $D_{2}f=u$. Thus, 

$$
{\frac {d}{dx}}(g(x)h(x))=h(x){\frac {d}{dx}}g(x)+g(x){\frac {d}{dx}}h(x).
$$

The case of exponentiation 

$$
f(u,v)=u^{v}
$$

 is slightly more complicated, as 

$$
D_{1}f=vu^{v-1},
$$

 and, as $u^{v}=e^{v\ln u},$ 

$$
D_{2}f=u^{v}\ln u.
$$

 It follows that 

$$
{\frac {d}{dx}}\left(g(x)^{h(x)}\right)=h(x)g(x)^{h(x)-1}{\frac {d}{dx}}g(x)+g(x)^{h(x)}\ln g(x)\,{\frac {d}{dx}}h(x).
$$

### General rule: Vector-valued multivariate functions

The simplest way for writing the chain rule in the general case is to use the [total derivative](https://en.wikipedia.org/wiki/Total_derivative#The_total_derivative_as_a_linear_map), which is a linear transformation that captures all [directional derivatives](https://en.wikipedia.org/wiki/Directional_derivative) in a single formula. Consider differentiable functions *f* : **R***m* → **R***k* and *g* : **R***n* → **R***m*, and a point **a** in **R***n*. Let *D*<sub>**a**</sub> *g* denote the total derivative of *g* at **a** and *D*<sub>*g*(**a**)</sub> *f* denote the total derivative of *f* at *g*(**a**). These two derivatives are linear transformations **R***n* → **R***m* and **R***m* → **R***k*, respectively, so they can be composed. The chain rule for total derivatives is that their composite is the total derivative of *f* ∘ *g* at **a**: 

$$
D_{\mathbf {a} }(f\circ g)=D_{g(\mathbf {a} )}f\circ D_{\mathbf {a} }g,
$$

 or for short, 

$$
D(f\circ g)=Df\circ Dg.
$$

 The higher-dimensional chain rule can be proved using a technique similar to the second proof given above.

Because the total derivative is a linear transformation, the functions appearing in the formula can be rewritten as matrices. The matrix corresponding to a total derivative is called a [[Jacobian Matrix]], and the composite of two derivatives corresponds to the product of their Jacobian matrices. From this perspective the chain rule therefore says: 

$$
J_{f\circ g}(\mathbf {a} )=J_{f}(g(\mathbf {a} ))J_{g}(\mathbf {a} ),
$$

 or for short, 

$$
J_{f\circ g}=(J_{f}\circ g)J_{g}.
$$

That is, the Jacobian of a composite function is the product of the Jacobians of the composed functions (evaluated at the appropriate points).

The higher-dimensional chain rule is a generalization of the one-dimensional chain rule. If k, m, and n are 1, so that *f* : **R** → **R** and *g* : **R** → **R**, then the Jacobian matrices of *f* and *g* are 1 × 1. Specifically, they are: 

$$
{\begin{aligned}J_{g}(a)&={\begin{pmatrix}g'(a)\end{pmatrix}},\\J_{f}(g(a))&={\begin{pmatrix}f'(g(a))\end{pmatrix}}.\end{aligned}}
$$

 The Jacobian of *f* ∘ *g* is the product of these 1 × 1 matrices, so it is *f*′(*g*(*a*))⋅*g*′(*a*), as expected from the one-dimensional chain rule. In the language of linear transformations, *D*<sub>*a*</sub>(*g*) is the function which scales a vector by a factor of *g*′(*a*) and *D*<sub>*g*(*a*)</sub>(*f*) is the function which scales a vector by a factor of *f*′(*g*(*a*)). The chain rule says that the composite of these two linear transformations is the linear transformation *D*<sub>*a*</sub>(*f* ∘ *g*), and therefore it is the function that scales a vector by *f*′(*g*(*a*))⋅*g*′(*a*).

Another way of writing the chain rule is used when *f* and *g* are expressed in terms of their components as **y** = *f*(**u**) = (*f*<sub>1</sub>(**u**), …, *f*<sub>*k*</sub>(**u**)) and **u** = *g*(**x**) = (*g*<sub>1</sub>(**x**), …, *g*<sub>*m*</sub>(**x**)). In this case, the above rule for Jacobian matrices is usually written as: 

$$
{\frac {\partial (y_{1},\ldots ,y_{k})}{\partial (x_{1},\ldots ,x_{n})}}={\frac {\partial (y_{1},\ldots ,y_{k})}{\partial (u_{1},\ldots ,u_{m})}}{\frac {\partial (u_{1},\ldots ,u_{m})}{\partial (x_{1},\ldots ,x_{n})}}.
$$

The chain rule for total derivatives implies a chain rule for partial derivatives. Recall that when the total derivative exists, the partial derivative in the i-th coordinate direction is found by multiplying the Jacobian matrix by the i-th basis vector. By doing this to the formula above, we find: 

$$
{\frac {\partial (y_{1},\ldots ,y_{k})}{\partial x_{i}}}={\frac {\partial (y_{1},\ldots ,y_{k})}{\partial (u_{1},\ldots ,u_{m})}}{\frac {\partial (u_{1},\ldots ,u_{m})}{\partial x_{i}}}.
$$

 Since the entries of the Jacobian matrix are partial derivatives, we may simplify the above formula to get: 

$$
{\frac {\partial (y_{1},\ldots ,y_{k})}{\partial x_{i}}}=\sum _{\ell =1}^{m}{\frac {\partial (y_{1},\ldots ,y_{k})}{\partial u_{\ell }}}{\frac {\partial u_{\ell }}{\partial x_{i}}}.
$$

 More conceptually, this rule expresses the fact that a change in the *x*<sub>*i*</sub> direction may change all of *g*<sub>1</sub> through *g<sub>m</sub>*, and any of these changes may affect *f*.

In the special case where *k* = 1, so that *f* is a real-valued function, then this formula simplifies even further: 

$$
{\frac {\partial y}{\partial x_{i}}}=\sum _{\ell =1}^{m}{\frac {\partial y}{\partial u_{\ell }}}{\frac {\partial u_{\ell }}{\partial x_{i}}}.
$$

 This can be rewritten as a [dot product](https://en.wikipedia.org/wiki/Dot_product). Recalling that **u** = (*g*<sub>1</sub>, …, *g*<sub>*m*</sub>), the partial derivative ∂**u** / ∂*x*<sub>*i*</sub> is also a vector, and the chain rule says that: 

$$
{\frac {\partial y}{\partial x_{i}}}=\nabla y\cdot {\frac {\partial \mathbf {u} }{\partial x_{i}}}.
$$

#### Example

Given *u*(*x*, *y*) = *x*2 + 2*y* where *x*(*r*, *t*) = *r* sin(*t*) and *y*(*r*,*t*) = sin2(*t*), determine the value of ∂*u* / ∂*r* and ∂*u* / ∂*t* using the chain rule.\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\] 

$$
{\frac {\partial u}{\partial r}}={\frac {\partial u}{\partial x}}{\frac {\partial x}{\partial r}}+{\frac {\partial u}{\partial y}}{\frac {\partial y}{\partial r}}=(2x)(\sin(t))+(2)(0)=2r\sin ^{2}(t),
$$

 and 

$$
{\begin{aligned}{\frac {\partial u}{\partial t}}&={\frac {\partial u}{\partial x}}{\frac {\partial x}{\partial t}}+{\frac {\partial u}{\partial y}}{\frac {\partial y}{\partial t}}\\&=(2x)(r\cos(t))+(2)(2\sin(t)\cos(t))\\&=(2r\sin(t))(r\cos(t))+4\sin(t)\cos(t)\\&=2(r^{2}+2)\sin(t)\cos(t)\\&=(r^{2}+2)\sin(2t).\end{aligned}}
$$

#### Higher derivatives of multivariable functions

Faà di Bruno's formula for higher-order derivatives of single-variable functions generalizes to the multivariable case. If *y* = *f*(**u**) is a function of **u** = *g*(**x**) as above, then the second derivative of *f* ∘ *g* is: 

$$
{\frac {\partial ^{2}y}{\partial x_{i}\partial x_{j}}}=\sum _{k}\left({\frac {\partial y}{\partial u_{k}}}{\frac {\partial ^{2}u_{k}}{\partial x_{i}\partial x_{j}}}\right)+\sum _{k,\ell }\left({\frac {\partial ^{2}y}{\partial u_{k}\partial u_{\ell }}}{\frac {\partial u_{k}}{\partial x_{i}}}{\frac {\partial u_{\ell }}{\partial x_{j}}}\right).
$$

## Further generalizations

All extensions of calculus have a chain rule. In most of these, the formula remains the same, though the meaning of that formula may be vastly different.

One generalization is to [[Manifold|manifolds]]. In this situation, the chain rule represents the fact that the derivative of *f* ∘ *g* is the composite of the derivative of *f* and the derivative of *g*. This theorem is an immediate consequence of the higher dimensional chain rule given above, and it has exactly the same formula.

The chain rule is also valid for [Fréchet derivatives](https://en.wikipedia.org/wiki/Fr%C3%A9chet_derivative) in [Banach spaces](https://en.wikipedia.org/wiki/Banach_space). The same formula holds as before. This case and the previous one admit a simultaneous generalization to [Banach manifolds](https://en.wikipedia.org/wiki/Banach_manifold).

In [differential algebra](https://en.wikipedia.org/wiki/Differential_algebra), the derivative is interpreted as a morphism of modules of [Kähler differentials](https://en.wikipedia.org/wiki/K%C3%A4hler_differential). A [ring homomorphism](https://en.wikipedia.org/wiki/Ring_homomorphism) of [commutative rings](https://en.wikipedia.org/wiki/Commutative_ring) *f* : *R* → *S* determines a morphism of Kähler differentials *Df* : Ω<sub>*R*</sub> → Ω<sub>*S*</sub> which sends an element *dr* to *d*(*f*(*r*)), the exterior differential of *f*(*r*). The formula *D*(*f* ∘ *g*) = *Df* ∘ *Dg* holds in this context as well.

The common feature of these examples is that they are expressions of the idea that the derivative is part of a [functor](https://en.wikipedia.org/wiki/Functor). A functor is an operation on spaces and functions between them. It associates to each space a new space and to each function between two spaces a new function between the corresponding new spaces. In each of the above cases, the functor sends each space to its [tangent bundle](https://en.wikipedia.org/wiki/Tangent_bundle) and it sends each function to its derivative. For example, in the manifold case, the derivative sends a *C**r*-manifold to a *C**r*−1-manifold (its tangent bundle) and a *C**r*-function to its total derivative. There is one requirement for this to be a functor, namely that the derivative of a composite must be the composite of the derivatives. This is exactly the formula *D*(*f* ∘ *g*) = *Df* ∘ *Dg*.

There are also chain rules in [stochastic calculus](https://en.wikipedia.org/wiki/Stochastic_calculus). One of these, [Itō's lemma](https://en.wikipedia.org/wiki/It%C5%8D%27s_lemma), expresses the composite of an Itō process (or more generally a [semimartingale](https://en.wikipedia.org/wiki/Semimartingale)) *dX*<sub>*t*</sub> with a twice-differentiable function *f*. In Itō's lemma, the derivative of the composite function depends not only on *dX*<sub>*t*</sub> and the derivative of *f* but also on the second derivative of *f*. The dependence on the second derivative is a consequence of the non-zero [quadratic variation](https://en.wikipedia.org/wiki/Quadratic_variation) of the stochastic process, which broadly speaking means that the process can move up and down in a very rough way. This variant of the chain rule is not an example of a functor because the two functions being composed are of different types.

## See also

- [[Automatic Differentiation]] – Numerical calculations carrying along derivatives − a computational method that makes heavy use of the chain rule to compute exact numerical derivatives.
- [Differentiation rules](https://en.wikipedia.org/wiki/Differentiation_rules) – Rules for computing derivatives of functions
- [Integration by substitution](https://en.wikipedia.org/wiki/Integration_by_substitution) – Technique in integral evaluation
- [Leibniz integral rule](https://en.wikipedia.org/wiki/Leibniz_integral_rule) – Differentiation under the integral sign formula
- [Product rule](https://en.wikipedia.org/wiki/Product_rule) – Formula for the derivative of a product
- [Quotient rule](https://en.wikipedia.org/wiki/Quotient_rule) – Formula for the derivative of a ratio of functions
- [Triple product rule](https://en.wikipedia.org/wiki/Triple_product_rule) – Relation between relative derivatives of three variables

## References

1. [George F. Simmons](https://en.wikipedia.org/wiki/George_F._Simmons), *Calculus with Analytic Geometry* (1985), p. 93.
2. Simmons, George F. (1996). *Calculus with Analytic Geometry*. McGraw-Hill. p. 115. ISBN 9780070575295. [Internet Archive](https://archive.org/details/GeorgeSimmonsCalculusWithAnalyticGeometry1996McGrawHillScienceEngineeringMath)
3. Child, J. M. (1917). ["THE MANUSCRIPTS OF LEIBNIZ ON HIS DISCOVERY OF THE DIFFERENTIAL CALCULUS. PART II (Continued)"](https://www.jstor.org/stable/27900650). *The Monist*. **27** (3): 411–454. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.5840/monist191727324](https://doi.org/10.5840%2Fmonist191727324). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0026-9662](https://search.worldcat.org/issn/0026-9662). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [27900650](https://www.jstor.org/stable/27900650).
4. ^ Rodríguez, Omar Hernández; López Fernández, Jorge M. (2010). ["A Semiotic Reflection on the Didactics of the Chain Rule"](https://scholarworks.umt.edu/tme/vol7/iss2/10/). *The Mathematics Enthusiast*. **7** (2): 321–332. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.54870/1551-3440.1191](https://doi.org/10.54870%2F1551-3440.1191).
5. [Apostol, Tom](https://en.wikipedia.org/wiki/Tom_Apostol) (1974). *Mathematical analysis* (2nd ed.). Addison Wesley. Theorem 5.5.
6. Landau, L. D., and E. M. Lifshitz. *Mechanics*. Course of Theoretical Physics, Vol. 1. Pergamon Press, 1960, §12.
7. [Goodfellow, Ian](https://en.wikipedia.org/wiki/Ian_Goodfellow); [Bengio, Yoshua](https://en.wikipedia.org/wiki/Yoshua_Bengio); Courville, Aaron (2016), *Deep learning*, MIT, pp=197–217.
8. Kuhn, Stephen (1991). "The Derivative á la Carathéodory". *[The American Mathematical Monthly](https://en.wikipedia.org/wiki/The_American_Mathematical_Monthly)*. **98** (1): 40–44. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2324035](https://doi.org/10.2307%2F2324035). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2324035](https://www.jstor.org/stable/2324035).
9. [Spivak, Michael](https://en.wikipedia.org/wiki/Michael_Spivak) (1965). *[Calculus on Manifolds](https://en.wikipedia.org/wiki/Calculus_on_Manifolds_(book) "Calculus on Manifolds (book)")*. Boston: Addison-Wesley. pp. 19–20. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-8053-9021-9](https://en.wikipedia.org/wiki/Special:BookSources/0-8053-9021-9).
10. [Cheney, Ward](https://en.wikipedia.org/wiki/Elliott_Ward_Cheney_Jr.) (2001). "The Chain Rule and Mean Value Theorems". *Analysis for Applied Mathematics*. New York: Springer. pp. 121–125. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-95279-9](https://en.wikipedia.org/wiki/Special:BookSources/0-387-95279-9).

## Further reading

- Abou-Hayt, Imad; Dahl, Bettina (2025-03-29). ["Using a Realistic Context to Motivate and Teach Engineering Students the Chain Rule"](https://doi.org/10.3390%2Feducsci15040433). *Education Sciences*. **15** (4): 433. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3390/educsci15040433](https://doi.org/10.3390%2Feducsci15040433). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [2227-7102](https://search.worldcat.org/issn/2227-7102).

## External links

- ["Leibniz rule"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society), 2001 \[1994\]
- [Weisstein, Eric W.](https://en.wikipedia.org/wiki/Eric_W._Weisstein) ["Chain Rule"](https://mathworld.wolfram.com/ChainRule.html). *[MathWorld](https://en.wikipedia.org/wiki/MathWorld)*.
