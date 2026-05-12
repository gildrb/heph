[[optimization.base]]

> Source: [Newton's method](https://en.wikipedia.org/wiki/Newton%27s_method)
> License: Wikipedia content is available under CC BY-SA 4.0.

![[media/ba9c25a4d6b16202b1f13741f214e6735650c016.png]]
An illustration of Newton's method

In [numerical analysis](https://en.wikipedia.org/wiki/Numerical_analysis), the **Newton–Raphson method**, also known simply as **Newton's method**, named after [Isaac Newton](https://en.wikipedia.org/wiki/Isaac_Newton) and [Joseph Raphson](https://en.wikipedia.org/wiki/Joseph_Raphson), is a [root-finding algorithm](https://en.wikipedia.org/wiki/Root-finding_algorithm) which produces successively better [approximations](https://en.wikipedia.org/wiki/Numerical_analysis) to the [roots](https://en.wikipedia.org/wiki/Root_of_a_function) (or zeroes) of a [real](https://en.wikipedia.org/wiki/Real_number)-valued [function](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)"). The most basic version starts with a [real-valued function](https://en.wikipedia.org/wiki/Real-valued_function) f, its [derivative](https://en.wikipedia.org/wiki/Derivative) f′, and an initial guess `x`<sub>0</sub> for a [root](https://en.wikipedia.org/wiki/Zero_of_a_function) of f. If f satisfies certain assumptions and the initial guess is close, then

$$
x_{1}=x_{0}-{\frac {f(x_{0})}{f'(x_{0})}}
$$

is a better approximation of the root than `x`<sub>0</sub>. Geometrically, (`x`<sub>1</sub>, 0) is the [x-intercept](https://en.wikipedia.org/wiki/X-intercept) of the [tangent](https://en.wikipedia.org/wiki/Tangent) to the [graph](https://en.wikipedia.org/wiki/Graph_of_a_function) of f at (`x`<sub>0</sub>, `f`(`x`<sub>0</sub>)): that is, the improved guess, `x`<sub>1</sub>, is the unique root of the [linear approximation](https://en.wikipedia.org/wiki/Linear_approximation) of f at the initial guess, `x`<sub>0</sub>. The process is repeated as

$$
x_{n+1}=x_{n}-{\frac {f(x_{n})}{f'(x_{n})}}
$$

until a sufficiently precise value is reached. The number of correct digits roughly doubles with each step. This algorithm is first in the class of [Householder's methods](https://en.wikipedia.org/wiki/Householder%27s_method), and was succeeded by [Halley's method](https://en.wikipedia.org/wiki/Halley%27s_method). The method can also be extended to [complex functions](https://en.wikipedia.org/wiki/Complex-valued_function) and to [systems of equations](https://en.wikipedia.org/wiki/Systems_of_equations).

## Description

The purpose of Newton's method is to find a root of a function. The idea is to start with an initial guess near a root, approximate the function by its [tangent line](https://en.wikipedia.org/wiki/Tangent_line) near the guess, and then take the root of the linear approximation as a next guess at the function's root. This will typically be closer to the function's root than the previous guess, and the method can be [iterated](https://en.wikipedia.org/wiki/Iterative_method).

![[media/c67b3ffcdc9fb5a7442fc7ae19680ba700a17964.png]]
<var style="padding-right: 1px;">x</var><sub><var style="padding-right: 1px;">n</var>+1</sub> is a better approximation than <var style="padding-right: 1px;">x</var><sub><var style="padding-right: 1px;">n</var></sub> for the root x of the function f (blue curve).

The best [linear approximation](https://en.wikipedia.org/wiki/Linear_approximation) to an arbitrary [differentiable function](https://en.wikipedia.org/wiki/Differentiable_function) $f(x)$ near the point $x=x_{n}$ is the tangent line to the curve, with equation

$$
f(x)\approx f(x_{n})+f'(x_{n})(x-x_{n}).
$$

The root of this linear function, the place where it intercepts the $x$-axis, can be taken as a closer approximate root $x_{n+1}$:

$$
x_{n+1}=x_{n}-{\frac {f(x_{n})}{f'(x_{n})}}.
$$

![[media/8d8c2b197e3b1ee05e6e97caf755518852dc6c15.gif]]
Iteration typically improves the approximation.

The process can be started with any arbitrary initial guess $x_{0}$, though it will generally require fewer iterations to converge if the guess is close to one of the function's roots. The method will usually converge if $f'(x_{0})\neq 0$. Furthermore, for a root of [multiplicity](https://en.wikipedia.org/wiki/Multiplicity_(mathematics) "Multiplicity (mathematics)") 1, the convergence is at least quadratic (see *[Rate of convergence](https://en.wikipedia.org/wiki/Rate_of_convergence)*) in some sufficiently small [neighbourhood](https://en.wikipedia.org/wiki/Neighbourhood_(mathematics) "Neighbourhood (mathematics)") of the root: the number of correct digits of the approximation roughly doubles with each additional step. More details can be found in *[§ Analysis](#Analysis)* below.

[Householder's methods](https://en.wikipedia.org/wiki/Householder%27s_method) are similar but have higher order for even faster convergence. However, the extra computations required for each step can slow down the overall performance relative to Newton's method, particularly if $f$ or its derivatives are computationally expensive to evaluate.

## History

In the [Old Babylonian](https://en.wikipedia.org/wiki/Babylonian_mathematics) period (19th–16th century BCE), the side of a square of known area could be effectively approximated, and this is conjectured to have been done using a special case of Newton's method, [described algebraically below](#Use_of_Newton's_method_to_compute_square_roots), by iteratively improving an initial estimate; an equivalent method can be found in [Hero of Alexandria](https://en.wikipedia.org/wiki/Hero_of_Alexandria)'s *Metrica* (1st–2nd century CE), so is often called *[Heron's method](https://en.wikipedia.org/wiki/Heron%27s_method)*. [Jamshīd al-Kāshī](https://en.wikipedia.org/wiki/Jamsh%C4%ABd_al-K%C4%81sh%C4%AB) used a method to solve `x`<sup>`P`</sup> − `N` = 0 to find roots of *N*, a method that was algebraically equivalent to Newton's method, and in which a similar method was found in *Trigonometria Britannica*, published by [Henry Briggs](https://en.wikipedia.org/wiki/Henry_Briggs_(mathematician) "Henry Briggs (mathematician)") in 1633. His method first appeared in his 1427 publication *Miftāḥ al-Ḥisāb* (*The Key to Arithmetic*). Al-Kāshī's work was founded on the earlier contributions of the polymath [al-Bīrūnī](https://en.wikipedia.org/wiki/Al-B%C4%ABr%C5%ABn%C4%AB) (973–1048) and the mathematician [Sharaf al-Dīn al-Ṭūsī](https://en.wikipedia.org/wiki/Sharaf_al-D%C4%ABn_al-%E1%B9%AC%C5%ABs%C4%AB) (1135–1213). The contributions of al-Kāshī remained largely unknown to the Western scientific community for centuries, until the work of [François Viète](https://en.wikipedia.org/wiki/Fran%C3%A7ois_Vi%C3%A8te) (1540–1603). In 1600, Viète rediscovered a technique similar to al-Kāshī's in the context of solving scalar polynomial equations of degree six.

The method that laid the groundwork for what is now the modern Newton's method which would be developed by [Joseph Raphson](https://en.wikipedia.org/wiki/Joseph_Raphson) and [Thomas Simpson](https://en.wikipedia.org/wiki/Thomas_Simpson) first appeared in [Isaac Newton](https://en.wikipedia.org/wiki/Isaac_Newton)'s work in *[De analysi per aequationes numero terminorum infinitas](https://en.wikipedia.org/wiki/De_analysi_per_aequationes_numero_terminorum_infinitas)* (written in 1669, published in 1711 by [William Jones](https://en.wikipedia.org/wiki/William_Jones_(mathematician) "William Jones (mathematician)")) and in *De metodis fluxionum et serierum infinitarum* (written in 1671, translated and published as *[Method of Fluxions](https://en.wikipedia.org/wiki/Method_of_Fluxions)* in 1736 by [John Colson](https://en.wikipedia.org/wiki/John_Colson)). However, while Newton gave the basic ideas, his method differs from the modern method given above. He applied the method only to polynomials, starting with an initial root estimate and extracting a sequence of error corrections. He used each correction to rewrite the polynomial in terms of the remaining error, and then solved for a new correction by neglecting higher-degree terms. He did not explicitly connect the method with derivatives or present a general formula. Newton applied this method to both numerical and algebraic problems, producing [[Taylor Series]] in the latter case. Despite this, in the later second and third editions of Newton's 1687 [*Philosophiæ Naturalis Principia Mathematica*](https://en.wikipedia.org/wiki/Philosophi%C3%A6_Naturalis_Principia_Mathematica), he did apply his method in an iterative manner to a nonpolynomial equation, specifically [Kepler's equation](https://en.wikipedia.org/wiki/Kepler%27s_equation), which were the first published uses of Newton's method in this form by him.

Newton may have derived his method from a similar, less precise method by mathematician Viète, however, the two methods are not the same. The essence of Viète's own method can be found in the work of the mathematician [Sharaf al-Din al-Tusi](https://en.wikipedia.org/wiki/Sharaf_al-Din_al-Tusi).

The Japanese mathematician [Seki Kōwa](https://en.wikipedia.org/wiki/Seki_K%C5%8Dwa) used a form of Newton's method in the 1680s to solve single-variable equations, though the connection with [calculus](https://en.wikipedia.org/wiki/Calculus) was missing.

Newton's method was first published in 1685 in *A Treatise of Algebra both Historical and Practical* by [John Wallis](https://en.wikipedia.org/wiki/John_Wallis). In 1690, Raphson published a simplified description in *Analysis aequationum universalis*. Raphson also applied the method only to polynomials, but he avoided Newton's tedious rewriting process by extracting each successive correction from the original polynomial. This allowed him to derive a reusable iterative expression for each problem. Finally, in 1740, Simpson described Newton's method as an iterative method for solving general nonlinear equations using calculus, essentially giving the description above. In the same publication, Simpson also gives the generalization to systems of two equations and notes that Newton's method can be used for solving optimization problems by setting the gradient to zero.

[Arthur Cayley](https://en.wikipedia.org/wiki/Arthur_Cayley) in 1879 in *The Newton–Fourier imaginary problem* was the first to notice the difficulties in generalizing Newton's method to complex roots of polynomials with degree greater than 2 and complex initial values. This opened the way to the study of the [theory of iterations](https://en.wikipedia.org/wiki/Julia_set) of rational functions.

## Practical considerations

Newton's method is a powerful technique—if the derivative of the function at the root is nonzero, then the [convergence](https://en.wikipedia.org/wiki/Rate_of_convergence) is at least quadratic: as the method converges on the root, the difference between the root and the approximation is squared (the number of accurate digits roughly doubles) at each step. However, there are some difficulties with the method.

### Difficulty in calculating the derivative of a function

Newton's method requires that the derivative can be calculated directly. An analytical expression for the derivative may not be easily obtainable or could be expensive to evaluate. In these situations, it may be appropriate to approximate the derivative by using the slope of a line through two nearby points on the function. Using this approximation would result in something like the [secant method](https://en.wikipedia.org/wiki/Secant_method) whose convergence is slower than that of Newton's method.

### Failure of the method to converge to the root

It is important to review the [proof of quadratic convergence](#Proof_of_quadratic_convergence_for_Newton's_iterative_method) of Newton's method before implementing it. Specifically, one should review the assumptions made in the proof. For [situations where the method fails to converge](#Failure_analysis), it is because the assumptions made in this proof are not met.

For example, [in some cases](#Divergence_even_when_initialization_is_close_to_the_root), if the first derivative is not well behaved in the neighborhood of a particular root, then it is possible that Newton's method will fail to converge no matter where the initialization is set. In some cases, Newton's method can be stabilized by using [successive over-relaxation](https://en.wikipedia.org/wiki/Successive_over-relaxation#Other_applications_of_the_method), or the speed of convergence can be increased by using the same method.

In a robust implementation of Newton's method, it is common to place limits on the number of iterations, bound the solution to an interval known to contain the root, and combine the method with a more robust root finding method.

### Slow convergence for roots of multiplicity greater than 1

If the root being sought has [multiplicity](https://en.wikipedia.org/wiki/Multiplicity_(mathematics)#Multiplicity_of_a_root_of_a_polynomial "Multiplicity (mathematics)") greater than one, the convergence rate is merely linear (errors reduced by a constant factor at each step) unless special steps are taken. When there are two or more roots that are close together then it may take many iterations before the iterates get close enough to one of them for the quadratic convergence to be apparent. However, if the multiplicity m of the root is known, the following modified algorithm preserves the quadratic convergence rate:

$$
x_{n+1}=x_{n}-m{\frac {f(x_{n})}{f'(x_{n})}}.
$$

This is equivalent to using [successive over-relaxation](https://en.wikipedia.org/wiki/Successive_over-relaxation#Other_applications_of_the_method). On the other hand, if the multiplicity m of the root is not known, it is possible to estimate m after carrying out one or two iterations, and then use that value to increase the rate of convergence.

If the multiplicity m of the root is finite then `g`(`x`) = `f`(`x`)/`f``′`(`x`) will have a root at the same location with multiplicity 1. Applying Newton's method to find the root of `g`(`x`) recovers quadratic convergence in many cases although it generally involves the second derivative of `f`(`x`). In a particularly simple case, if `f`(`x`) = `x`<sup>`m`</sup> then `g`(`x`) = `x`/`m` and Newton's method finds the root in a single iteration with

$$
x_{n+1}=x_{n}-{\frac {g(x_{n})}{g'(x_{n})}}=x_{n}-{\frac {\;{\frac {x_{n}}{m}}\;}{\frac {1}{m}}}=0\,.
$$

### Slow convergence

The function *f*(*x*) = *x*<sup>2</sup> has a root at 0. Since f is continuously differentiable at its root, the theory guarantees that Newton's method as initialized sufficiently close to the root will converge. However, since the derivative *f* ′ is zero at the root, quadratic convergence is not ensured by the theory. In this particular example, the Newton iteration is given by

$x_{n+1}=x_{n}-{\frac {f(x_{n})}{f'(x_{n})}}={\frac {1}{2}}x_{n}.$

It is visible from this that Newton's method could be initialized anywhere and converge to zero, but at only a linear rate. If initialized at 1, dozens of iterations would be required before ten digits of accuracy are achieved.

The function *f*(*x*) = *x* + *x*<sup>4/3</sup> also has a root at 0, where it is continuously differentiable. Although the first derivative *f* ′ is nonzero at the root, the second derivative *f* ′′ is nonexistent there, so that quadratic convergence cannot be guaranteed. In fact the Newton iteration is given by

$x_{n+1}=x_{n}-{\frac {f(x_{n})}{f'(x_{n})}}={\frac {x_{n}^{4/3}}{3+4x_{n}^{1/3}}}\approx x_{n}\cdot {\frac {x_{n}^{1/3}}{3}}.$

From this, it can be seen that the rate of convergence is superlinear but subquadratic. This can be seen in the following tables, the left of which shows Newton's method applied to the above *f*(*x*) = *x* + *x*<sup>4/3</sup> and the right of which shows Newton's method applied to *f*(*x*) = *x* + *x*<sup>2</sup>. The quadratic convergence in iteration shown on the right is illustrated by the orders of magnitude in the distance from the iterate to the true root (0,1,2,3,5,10,20,39,...) being approximately doubled from row to row. While the convergence on the left is superlinear, the order of magnitude is only multiplied by about 4/3 from row to row (0,1,2,4,5,7,10,13,...).

<table class="wikitable" style="border: none;">

<em>x</em><sub><em>n</em></sub>
<em>x</em> + <em>x</em><sup>4/3</sup><br />
<sub><em>n</em></sub>

<em>x</em><sub><em>n</em></sub>
<em>x</em> + <em>x</em><sup>2</sup><br />
<sub><em>n</em></sub>

1
2
1
2

1.4286 × 10<sup>−1</sup>
2.1754 × 10<sup>−1</sup>
3.3333 × 10<sup>−1</sup>
4.4444 × 10<sup>−1</sup>

1.4669 × 10<sup>−2</sup>
1.8260 × 10<sup>−2</sup>
6.6666 × 10<sup>−2</sup>
7.1111 × 10<sup>−2</sup>

9.0241 × 10<sup>−4</sup>
9.8961 × 10<sup>−4</sup>
3.9216 × 10<sup>−3</sup>
3.9369 × 10<sup>−3</sup>

2.5750 × 10<sup>−5</sup>
2.6511 × 10<sup>−5</sup>
1.5259 × 10<sup>−5</sup>
1.5259 × 10<sup>−5</sup>

2.4386 × 10<sup>−7</sup>
2.4539 × 10<sup>−7</sup>
2.3283 × 10<sup>−10</sup>
2.3283 × 10<sup>−10</sup>

5.0366 × 10<sup>−10</sup>
5.0406 × 10<sup>−10</sup>
5.4210 × 10<sup>−20</sup>
5.4210 × 10<sup>−20</sup>

1.3344 × 10<sup>−13</sup>
1.3344 × 10<sup>−13</sup>
2.9387 × 10<sup>−39</sup>
2.9387 × 10<sup>−39</sup>

</table>

The rate of convergence is distinguished from the number of iterations required to reach a given accuracy. For example, the function *f*(*x*) = *x*<sup>20</sup> − 1 has a root at 1. Since *f* ′(1) ≠ 0 and f is smooth, it is known that any Newton iteration convergent to 1 will converge quadratically. However, if initialized at 0.5, the first few iterates of Newton's method are approximately 26214, 24904, 23658, 22476, decreasing slowly, with only the 200th iterate being 1.0371. The following iterates are 1.0103, 1.00093, 1.0000082, and 1.00000000065, illustrating quadratic convergence. This highlights that quadratic convergence of a Newton iteration does not mean that only few iterates are required; this only applies once the sequence of iterates is sufficiently close to the root.

### Convergence dependent on initialization

The function *f*(*x*) = *x*(1 + *x*<sup>2</sup>)<sup>−1/2</sup> has a root at 0. The Newton iteration is given by

$x_{n+1}=x_{n}-{\frac {f(x_{n})}{f'(x_{n})}}=x_{n}-{\frac {x_{n}(1+x_{n}^{2})^{-1/2}}{(1+x_{n}^{2})^{-3/2}}}=-x_{n}^{3}.$

From this, it can be seen that there are three possible phenomena for a Newton iteration. If initialized strictly between ±1, the Newton iteration will converge (super-)quadratically to 0; if initialized exactly at 1 or −1, the Newton iteration will oscillate endlessly between ±1; if initialized anywhere else, the Newton iteration will diverge. This same trichotomy occurs for *f*(*x*) = arctan *x*.

In cases where the function in question has multiple roots, it can be difficult to control, via choice of initialization, which root (if any) is identified by Newton's method. For example, the function *f*(*x*) = *x*(*x*<sup>2</sup> − 1)(*x* − 3)e<sup>−(*x* − 1)<sup>2</sup>/2</sup> has roots at −1, 0, 1, and 3. If initialized at −1.488, the Newton iteration converges to 0; if initialized at −1.487, it diverges to ∞; if initialized at −1.486, it converges to −1; if initialized at −1.485, it diverges to −∞; if initialized at −1.4843, it converges to 3; if initialized at −1.484, it converges to 1. This kind of subtle dependence on initialization is not uncommon; it is frequently studied in the [complex plane](https://en.wikipedia.org/wiki/Complex_plane) in the form of the [Newton fractal](https://en.wikipedia.org/wiki/Newton_fractal).

### Divergence even when initialization is close to the root

Consider the problem of finding a root of *f*(*x*) = *x*<sup>1/3</sup>. The Newton iteration is

$x_{n+1}=x_{n}-{\frac {f(x_{n})}{f'(x_{n})}}=x_{n}-{\frac {x_{n}^{1/3}}{{\frac {1}{3}}x_{n}^{-2/3}}}=-2x_{n}.$

Unless Newton's method is initialized at the exact root 0, it is seen that the sequence of iterates will fail to converge. For example, even if initialized at the reasonably accurate guess of 0.001, the first several iterates are −0.002, 0.004, −0.008, 0.016, reaching 1048.58, −2097.15, ... by the 20th iterate. This failure of convergence is not contradicted by the analytic theory, since in this case f is not differentiable at its root.

In the above example, failure of convergence is reflected by the failure of *f*(*x*<sub>*n*</sub>) to get closer to zero as n increases, as well as by the fact that successive iterates are growing further and further apart. However, the function *f*(*x*) = *x*<sup>1/3</sup>e<sup>−*x*<sup>2</sup></sup> also has a root at 0. The Newton iteration is given by

$x_{n+1}=x_{n}-{\frac {f(x_{n})}{f'(x_{n})}}=x_{n}\left(1-{\frac {3}{1-6x_{n}^{2}}}\right).$

In this example, where again f is not differentiable at the root, any Newton iteration not starting exactly at the root will diverge, but with both *x*<sub>*n* + 1</sub> − *x*<sub>*n*</sub> and *f*(*x*<sub>*n*</sub>) converging to zero. This is seen in the following table showing the iterates with initialization 1:

|  |  |
|----|----|
| *x*<sub>*n*</sub> | *f*(*x*<sub>*n*</sub>) |
| 1 | 0.36788 |
| 1.6 | 9.0416 × 10<sup>−2</sup> |
| 1.9342 | 2.9556 × 10<sup>−2</sup> |
| 2.2048 | 1.0076 × 10<sup>−2</sup> |
| 2.4396 | 3.5015 × 10<sup>−3</sup> |
| 2.6505 | 1.2307 × 10<sup>−3</sup> |
| 2.8437 | 4.3578 × 10<sup>−4</sup> |
| 3.0232 | 1.5513 × 10<sup>−4</sup> |

Although the convergence of *x*<sub>*n* + 1</sub> − *x*<sub>*n*</sub> in this case is not very rapid, it can be proved from the iteration formula. This example highlights the possibility that a stopping criterion for Newton's method based only on the smallness of *x*<sub>*n* + 1</sub> − *x*<sub>*n*</sub> and *f*(*x*<sub>*n*</sub>) might falsely identify a root.

### Oscillatory behavior

![[media/43d0fdd9cfe2aadc73a83f5a479fee44face8f4b.png]]
The tangent lines of <var style="padding-right: 1px;">x</var><sup>3</sup> − 2<var style="padding-right: 1px;">x</var> + 2 at 0 and 1 intersect the x-axis at 1 and 0 respectively, illustrating why Newton's method oscillates between these values for some starting points.

It is easy to find situations for which Newton's method oscillates endlessly between two distinct values. For example, for Newton's method as applied to a function f to oscillate between 0 and 1, it is only necessary that the tangent line to f at 0 intersects the x-axis at 1 and that the tangent line to f at 1 intersects the x-axis at 0. This is the case, for example, if *f*(*x*) = *x*<sup>3</sup> − 2*x* + 2. For this function, it is even the case that Newton's iteration as initialized sufficiently close to 0 or 1 will *asymptotically* oscillate between these values. For example, Newton's method as initialized at 0.99 yields iterates 0.99, −0.06317, 1.00628, 0.03651, 1.00196, 0.01162, 1.00020, 0.00120, 1.000002, and so on. This behavior is present despite the presence of a root of f approximately equal to −1.76929.

### Undefinedness of Newton's method

In some cases, it is not even possible to perform the Newton iteration. For example, if *f*(*x*) = *x*<sup>2</sup> − 1, then the Newton iteration is defined by

$x_{n+1}=x_{n}-{\frac {f(x_{n})}{f'(x_{n})}}=x_{n}-{\frac {x_{n}^{2}-1}{2x_{n}}}={\frac {x_{n}^{2}+1}{2x_{n}}}.$

So Newton's method cannot be initialized at 0, since this would make *x*<sub>1</sub> undefined. Geometrically, this is because the tangent line to f at 0 is horizontal (i.e. *f* ′(0) = 0), never intersecting the *x*-axis.

Even if the initialization is selected so that the Newton iteration can begin, the same phenomenon can block the iteration from being indefinitely continued.

If f has an incomplete domain, it is possible for Newton's method to send the iterates outside of the domain, so that it is impossible to continue the iteration. For example, the [natural logarithm](https://en.wikipedia.org/wiki/Natural_logarithm) function *f*(*x*) = ln *x* has a root at 1, and is defined only for positive x. Newton's iteration in this case is given by

$x_{n+1}=x_{n}-{\frac {f(x_{n})}{f'(x_{n})}}=x_{n}(1-\ln x_{n}).$

So if the iteration is initialized at e, the next iterate is 0; if the iteration is initialized at a value larger than e, then the next iterate is negative. In either case, the method cannot be continued.

## Analysis

Suppose that the function f has a zero at α, i.e., `f`(`α`) = 0, and f is differentiable in a [neighborhood](https://en.wikipedia.org/wiki/Topological_neighborhood) of α.

If f is continuously differentiable and its derivative is nonzero at α, then there exists a [neighborhood](https://en.wikipedia.org/wiki/Topological_neighborhood) of α such that for all starting values `x`<sub>0</sub> in that neighborhood, the [sequence](https://en.wikipedia.org/wiki/Sequence) (`x`<sub>`n`</sub>) will [converge](https://en.wikipedia.org/wiki/Limit_of_a_sequence) to α.

If f is continuously differentiable, its derivative is nonzero at α, *and* it has a [second derivative](https://en.wikipedia.org/wiki/Second_derivative) at α, then the convergence is quadratic or faster. If the second derivative is not 0 at α then the convergence is merely quadratic. If the third derivative exists and is bounded in a neighborhood of α, then:

$$
\Delta x_{i+1}={\frac {f''(\alpha )}{2f'(\alpha )}}\left(\Delta x_{i}\right)^{2}+O\left(\Delta x_{i}\right)^{3}\,,
$$

where

$$
\Delta x_{i}\triangleq x_{i}-\alpha \,.
$$

If the derivative is 0 at α, then the convergence is usually only linear. Specifically, if f is twice continuously differentiable, `f``′`(`α`) = 0 and `f``″`(`α`) ≠ 0, then there exists a neighborhood of α such that, for all starting values `x`<sub>0</sub> in that neighborhood, the sequence of iterates converges linearly, with [rate](https://en.wikipedia.org/wiki/Rate_of_convergence) 1/2. Alternatively, if `f``′`(`α`) = 0 and `f``′`(`x`) ≠ 0 for `x` ≠ `α`, x in a [neighborhood](https://en.wikipedia.org/wiki/Topological_neighborhood) U of α, α being a zero of [multiplicity](https://en.wikipedia.org/wiki/Multiplicity_(mathematics) "Multiplicity (mathematics)") r, and if `f` ∈ `C`<sup>`r`</sup>(`U`), then there exists a neighborhood of α such that, for all starting values `x`<sub>0</sub> in that neighborhood, the sequence of iterates converges linearly.

However, even linear convergence is not guaranteed in pathological situations.

In practice, these results are local, and the neighborhood of convergence is not known in advance. But there are also some results on global convergence: for instance, given a right neighborhood `U`<sub>+</sub> of α, if f is twice differentiable in `U`<sub>+</sub> and if `f``′` ≠ 0, `f` · `f``″` \> 0 in `U`<sub>+</sub>, then, for each `x`<sub>0</sub> in `U`<sub>+</sub> the sequence `x`<sub>`k`</sub> is monotonically decreasing to α.

### Proof of quadratic convergence for Newton's iterative method

According to [Taylor's theorem](https://en.wikipedia.org/wiki/Taylor%27s_theorem), any function `f`(`x`) which has a continuous second derivative can be represented by an expansion about a point that is close to a root of `f`(`x`). Suppose this root is α. Then the expansion of `f`(`α`) about `x`<sub>`n`</sub> is:

|  |  |  |
|----|----|----|
| $f(\alpha )=f(x_{n})+f'(x_{n})(\alpha -x_{n})+R_{1}\,$ |  | [1](#math_1) |

where the [Lagrange form of the Taylor series expansion remainder](https://en.wikipedia.org/wiki/Lagrange_remainder) is

$$
R_{1}={\frac {1}{2!}}f''(\xi _{n})\left(\alpha -x_{n}\right)^{2}\,,
$$

where `ξ`<sub>`n`</sub> is in between `x`<sub>`n`</sub> and α.

Since α is the root, (**[1](#math_1)**) becomes:

|  |  |  |
|----|----|----|
| $0=f(\alpha )=f(x_{n})+f'(x_{n})(\alpha -x_{n})+{\tfrac {1}{2}}f''(\xi _{n})\left(\alpha -x_{n}\right)^{2}\,$ |  | [2](#math_2) |

Dividing equation (**[2](#math_2)**) by `f``′`(`x`<sub>`n`</sub>) and rearranging gives

|  |  |  |
|----|----|----|
| ${\frac {f(x_{n})}{f'(x_{n})}}+\left(\alpha -x_{n}\right)={\frac {-f''(\xi _{n})}{2f'(x_{n})}}\left(\alpha -x_{n}\right)^{2}$ |  | [3](#math_3) |

Remembering that `x`<sub>`n` + 1</sub> is defined by

|  |  |  |
|----|----|----|
| $x_{n+1}=x_{n}-{\frac {f(x_{n})}{f'(x_{n})}}\,,$ |  | [4](#math_4) |

one finds that

$$
\underbrace {\alpha -x_{n+1}} _{\varepsilon _{n+1}}={\frac {-f''(\xi _{n})}{2f'(x_{n})}}{(\,\underbrace {\alpha -x_{n}} _{\varepsilon _{n}}\,)}^{2}\,.
$$

That is,

|  |  |  |
|----|----|----|
| $\varepsilon _{n+1}={\frac {-f''(\xi _{n})}{2f'(x_{n})}}\cdot \varepsilon _{n}^{2}\,.$ |  | [5](#math_5) |

Taking the absolute value of both sides gives

|  |  |  |
|----|----|----|
| $\left|{\varepsilon _{n+1}}\right|={\frac {\left|f''(\xi _{n})\right|}{2\left|f'(x_{n})\right|}}\cdot \varepsilon _{n}^{2}\,.$ |  | [6](#math_6) |

Equation (**[6](#math_6)**) shows that the [order of convergence](https://en.wikipedia.org/wiki/Order_of_convergence) is at least quadratic if the following conditions are satisfied:

1.  `f``′`(`x`) ≠ 0; for all `x` ∈ `I`, where I is the interval \[`α` − \|`ε`<sub>0</sub>\|, `α` + \|`ε`<sub>0</sub>\|\];
2.  `f``″`(`x`) is continuous, for all `x` ∈ `I`;
3.  `M` \|`ε`<sub>0</sub>\| \< 1

where M is given by

$$
M={\frac {1}{2}}\left(\sup _{x\in I}\vert f''(x)\vert \right)\left(\sup _{x\in I}{\frac {1}{\vert f'(x)\vert }}\right).\,
$$

If these conditions hold,

$$
\vert \varepsilon _{n+1}\vert \leq M\cdot \varepsilon _{n}^{2}\,.
$$

### Fourier conditions

Suppose that *f*(*x*) is a [concave function](https://en.wikipedia.org/wiki/Concave_function) on an interval, which is [strictly increasing](https://en.wikipedia.org/wiki/Strictly_increasing). If it is negative at the left endpoint and positive at the right endpoint, the [intermediate value theorem](https://en.wikipedia.org/wiki/Intermediate_value_theorem) guarantees that there is a zero ζ of f somewhere in the interval. From geometrical principles, it can be seen that the Newton iteration *x*<sub>*i*</sub> starting at the left endpoint is [monotonically increasing](https://en.wikipedia.org/wiki/Monotonic_function) and convergent, necessarily to ζ.

[Joseph Fourier](https://en.wikipedia.org/wiki/Joseph_Fourier) introduced a modification of Newton's method starting at the right endpoint:

$y_{i+1}=y_{i}-{\frac {f(y_{i})}{f'(x_{i})}}.$

This sequence is monotonically decreasing and convergent. By passing to the limit in this definition, it can be seen that the limit of *y*<sub>*i*</sub> must also be the zero ζ.

So, in the case of a concave increasing function with a zero, initialization is largely irrelevant. Newton iteration starting anywhere left of the zero will converge, as will Fourier's modified Newton iteration starting anywhere right of the zero. The accuracy at any step of the iteration can be determined directly from the difference between the location of the iteration from the left and the location of the iteration from the right. If f is twice continuously differentiable, it can be proved using [Taylor's theorem](https://en.wikipedia.org/wiki/Taylor%27s_theorem) that

$\lim _{i\to \infty }{\frac {y_{i+1}-x_{i+1}}{(y_{i}-x_{i})^{2}}}=-{\frac {1}{2}}{\frac {f''(\zeta )}{f'(\zeta )}},$

showing that this difference in locations converges quadratically to zero.

All of the above can be extended to systems of equations in multiple variables, although in that context the relevant concepts of [monotonicity](https://en.wikipedia.org/wiki/Monotonicity) and concavity are more subtle to formulate. In the case of single equations in a single variable, the above monotonic convergence of Newton's method can also be generalized to replace concavity by positivity or negativity conditions on an arbitrary higher-order derivative of f. However, in this generalization, Newton's iteration is modified so as to be based on [Taylor polynomials](https://en.wikipedia.org/wiki/Taylor_polynomial) rather than the [tangent line](https://en.wikipedia.org/wiki/Tangent_line). In the case of concavity, this modification coincides with the standard Newton method.

### Error for n\>1 variables

If we seek the root of a single function $f:\mathbf {R} ^{n}\to \mathbf {R}$ then the error $\epsilon _{n}=x_{n}-\alpha$ is a vector such that its components obey $\epsilon _{k}^{(n+1)}={\frac {1}{2}}(\epsilon ^{(n)})^{T}Q_{k}\epsilon ^{(n)}+O(\|\epsilon ^{(n)}\|^{3})$ where $Q_{k}$ is a quadratic form: $(Q_{k})_{i,j}=\sum _{\ell }((D^{2}f)^{-1})_{i,\ell }{\frac {\partial ^{3}f}{\partial x_{j}\partial x_{k}\partial x_{\ell }}}$ evaluated at the root $\alpha$ (where $D^{2}f$ is the 2nd derivative Hessian matrix).

## Examples

### Use of Newton's method to compute square roots

Newton's method is one of many known [methods of computing square roots](https://en.wikipedia.org/wiki/Methods_of_computing_square_roots). Given a positive number a, the problem of finding a number x such that *x*<sup>2</sup> = *a* is equivalent to finding a root of the function *f*(*x*) = *x*<sup>2</sup> − *a*. The Newton iteration defined by this function is given by

$x_{n+1}=x_{n}-{\frac {f(x_{n})}{f'(x_{n})}}=x_{n}-{\frac {x_{n}^{2}-a}{2x_{n}}}={\frac {1}{2}}\left(x_{n}+{\frac {a}{x_{n}}}\right)$.

This happens to coincide with the ["Babylonian" method of finding square roots](https://en.wikipedia.org/wiki/Methods_of_computing_square_roots#Heron's_method), which consists of replacing an approximate root *x*<sub>*n*</sub> by the [arithmetic mean](https://en.wikipedia.org/wiki/Arithmetic_mean) of `x`<sub>`n`</sub> and `a`⁄`x`<sub>`n`</sub>. By performing this iteration, it is possible to evaluate a square root to any desired accuracy by only using the basic [arithmetic operations](https://en.wikipedia.org/wiki/Arithmetic_operations).

The following three tables show examples of the result of this computation for finding the square root of 612, with the iteration initialized at the values of 1, 10, and −20. Each row in a "*x*<sub>*n*</sub>" column is obtained by applying the preceding formula to the entry above it, for instance

$306.5={\frac {1}{2}}\left(1+{\frac {612}{1}}\right).$

<table class="wikitable" style="border: none;">

<em>x</em><sub><em>n</em></sub>
<em>f</em>(<em>x</em><sub><em>n</em></sub>)

<em>x</em><sub><em>n</em></sub>
<em>f</em>(<em>x</em><sub><em>n</em></sub>)

<em>x</em><sub><em>n</em></sub>
<em>f</em>(<em>x</em><sub><em>n</em></sub>)

1
−611
10
−512
<u>−2</u>0
−212

306.5
9.3330 × 10<sup>4</sup>
35.6
655.36
<u>−2</u>5.3
28.09

154.2483686786
2.3180 × 10<sup>4</sup>
<u>2</u>6.3955056180
84.722
<u>−24.7</u>448616601
0.30818

79.1079978644
5.6461 × 10<sup>3</sup>
<u>24.7</u>906354925
2.5756
<u>−24.73863</u>45374
3.8777 × 10<sup>−5</sup>

43.4221286822
1.2735 × 10<sup>3</sup>
<u>24.7386</u>882941
2.6985 × 10<sup>−3</sup>
<u>−24.7386337537</u>
6.1424 × 10<sup>−13</sup>

<u>2</u>8.7581624288
215.03
<u>24.738633753</u>8
2.9746 × 10<sup>−9</sup>

<u>2</u>5.0195385369
13.977

<u>24.7</u>402106712
7.8024 × 10<sup>−2</sup>

<u>24.738633</u>8040
2.4865 × 10<sup>−6</sup>

<u>24.7386337537</u>
2.5256 × 10<sup>−15</sup>

</table>

The correct digits are underlined. It is seen that with only a few iterations one can obtain a solution accurate to many decimal places. The first table shows that this is true even if the Newton iteration were initialized by the very inaccurate guess of 1.

When computing any nonzero square root, the first derivative of f must be nonzero at the root, and that f is a smooth function. So, even before any computation, it is known that any convergent Newton iteration has a quadratic rate of convergence. This is reflected in the above tables by the fact that once a Newton iterate gets close to the root, the number of correct digits approximately doubles with each iteration.

### Solution of cos(`x`) = `x`<sup>3</sup> using Newton's method

Consider the problem of finding the positive number x with cos (`x`) = `x`<sup>3</sup>. We can rephrase that as finding the zero of `f`(`x`) = cos(`x`) − `x`<sup>3</sup>. We have `f``′`(`x`) = −sin(`x`) − 3`x`<sup>2</sup>. Since cos(`x`) ≤ 1 for all x and `x`<sup>3</sup> \> 1 for `x` \> 1, we know that our solution lies between 0 and 1.

A starting value of 0 will lead to an undefined result which illustrates the importance of using a starting point close to the solution. For example, with an initial guess `x`<sub>0</sub> = 0.5, the sequence given by Newton's method is:

$$
{\begin{matrix}x_{1}&=&x_{0}-{\dfrac {f(x_{0})}{f'(x_{0})}}&=&0.5-{\dfrac {\cos 0.5-0.5^{3}}{-\sin 0.5-3\times 0.5^{2}}}&=&1.112\,141\,637\,097\dots \\x_{2}&=&x_{1}-{\dfrac {f(x_{1})}{f'(x_{1})}}&=&\vdots &=&{\underline {0.}}909\,672\,693\,736\dots \\x_{3}&=&\vdots &=&\vdots &=&{\underline {0.86}}7\,263\,818\,209\dots \\x_{4}&=&\vdots &=&\vdots &=&{\underline {0.865\,47}}7\,135\,298\dots \\x_{5}&=&\vdots &=&\vdots &=&{\underline {0.865\,474\,033\,1}}11\dots \\x_{6}&=&\vdots &=&\vdots &=&{\underline {0.865\,474\,033\,102}}\dots \end{matrix}}
$$

The correct digits are underlined in the above example. In particular, `x`<sub>6</sub> is correct to 12 decimal places. We see that the number of correct digits after the decimal point increases from 2 (for `x`<sub>3</sub>) to 5 and 10, illustrating the quadratic convergence.

## Multidimensional formulations

### Systems of equations

#### k variables, k functions

One may also use Newton's method to solve systems of k equations, which amounts to finding the (simultaneous) zeroes of k continuously differentiable functions $f:\mathbb {R} ^{k}\to \mathbb {R} .$ This is equivalent to finding the zeroes of a single vector-valued function $F:\mathbb {R} ^{k}\to \mathbb {R} ^{k}.$ In the formulation given above, the scalars x<sub>n</sub> are replaced by vectors **x**<sub>`n`</sub> and instead of dividing the function `f`(`x`<sub>`n`</sub>) by its derivative `f``′`(`x`<sub>`n`</sub>) one instead has to left multiply the function `F`(**x**<sub>`n`</sub>) by the inverse of its `k` × `k` [[Jacobian Matrix]] `J`<sub>`F`</sub>(**x**<sub>`n`</sub>). This results in the expression

$$
\mathbf {x} _{n+1}=\mathbf {x} _{n}-J_{F}(\mathbf {x} _{n})^{-1}F(\mathbf {x} _{n}).
$$

or, by solving the [system of linear equations](https://en.wikipedia.org/wiki/System_of_linear_equations)

$$
J_{F}(\mathbf {x} _{n})(\mathbf {x} _{n+1}-\mathbf {x} _{n})=-F(\mathbf {x} _{n})
$$

for the unknown **x**<sub>`n` + 1</sub> − **x**<sub>`n`</sub>.

#### k variables, m equations, with `m` \> `k`

The k-dimensional variant of Newton's method can be used to solve systems of greater than k (nonlinear) equations as well if the algorithm uses the [generalized inverse](https://en.wikipedia.org/wiki/Generalized_inverse) of the non-square [Jacobian](https://en.wikipedia.org/wiki/Jacobian_matrix_and_determinant) matrix `J`<sup>+</sup> = (`J`<sup>T</sup>`J`)<sup>−1</sup>`J`<sup>T</sup> instead of the inverse of J. If the [nonlinear system](https://en.wikipedia.org/wiki/System_of_nonlinear_equations) has no solution, the method attempts to find a solution in the [non-linear least squares](https://en.wikipedia.org/wiki/Non-linear_least_squares) sense. See [Gauss–Newton algorithm](https://en.wikipedia.org/wiki/Gauss%E2%80%93Newton_algorithm) for more information.

#### Example

![[media/0e6bbe750e0e25ee0e28eb3f2c0fb0803c5faf64.png]]
The milk carton to be constructed

A milk carton with a capacity of 2 [pints](https://en.wikipedia.org/wiki/Pint) is to be constructed from a sheet of waxed carboard with a 5mm overlap. The requirement is that the minimum surface area is used for the carton.

Suppose the width, breadth and height of the carton are denoted by $w$, $b$ and $h$ respectively, in millimetres. The total surface area, $A$, is given by

$A=(2b+2w+5)(h+b+10).$

![[media/3615310bdc5687f0d71fa4477de84a23b46de65d.png]]
The milk carton opened up with all measurements shown

Since 2 pints is approximately 1.136 litres, and 1 litre is $1000000mm^{3}$, it also follows that

$hbw=1136000.$

Solving for $w$ gives

$w={\frac {1136000}{hb}}.$

Letting $\mathbf {x} =\left[b,h\right]\in {\mathbb {R} }^{2}$ be the vector of two unknowns, $b$ and $h$, the surface area can then be expressed as

$A(\mathbf {x} )=(h+b+10)\left({\frac {2272000}{hb}}+2b+5\right).$

Minimization of this function entails equating its [partial derivatives](https://en.wikipedia.org/wiki/Partial_Derivative) to zero, which gives

${\frac {\partial A}{\partial b}}={\frac {2272000}{hb}}+2b+5+(h+b+10)\left({\frac {-2272000}{hb^{2}}}+2\right)=0$

and

${\frac {\partial A}{\partial h}}={\frac {2272000}{hb}}+2b+5-(h+b+10)\left({\frac {2272000}{h^{2}b}}\right)=0.$

To simplify notation, let

$f_{1}(\mathbf {x} )={\frac {\partial A}{\partial b}}$

and

$f_{2}(\mathbf {x} )={\frac {\partial A}{\partial h}}.$

The function vector $\mathbf {F} (\mathbf {x} )$ is therefore

$\mathbf {F} (\mathbf {x} )={\begin{bmatrix}{\begin{aligned}~&f_{1}(\mathbf {x} )\\~&f_{2}(\mathbf {x} )\end{aligned}}\end{bmatrix}}~=~{\begin{bmatrix}{\begin{aligned}~&{\frac {2272000}{hb}}+2b+5+(h+b+10)\left({\frac {-2272000}{hb^{2}}}+2\right)\\~&{\frac {2272000}{hb}}+2b+5-(h+b+10)\left({\frac {2272000}{h^{2}b}}\right)\end{aligned}}\end{bmatrix}}$

and Jacobian matrix $\mathbf {J} (\mathbf {x} )$ is

${\begin{aligned}\mathbf {J} (\mathbf {x} )={\begin{bmatrix}~{\frac {\ \partial {f_{1}}\ }{\partial {b}}}\ &~{\frac {\ \partial {f_{1}}\ }{\partial {h}}}~\\~{\frac {\ \partial {f_{2}}\ }{\partial {b}}}\ &~{\frac {\ \partial {f_{2}}\ }{\partial {h}}}~\end{bmatrix}}~=~{\begin{bmatrix}{\begin{aligned}~&{\frac {4544000}{b^{3}}}+{\frac {45440000}{hb^{3}}}+4\ &&{\frac {22720000}{h^{2}b^{2}}}+2\\~&{\frac {22720000}{h^{2}b^{2}}}+2\ &&{\frac {4544000}{h^{3}}}+{\frac {45440000}{bh^{3}}}\end{aligned}}\end{bmatrix}}.\end{aligned}}$

Applying Newton's method with initial guess $\mathbf {x} _{0}=\left[100,100\right]$ and with a stopping criterion of $\|\ \mathbf {x} _{i}-\mathbf {x} _{i-1}\|_{2}<10^{-6}$ gives the following iterations:

|  |  |  |  |
|----|----|----|----|
| Iteration | Solution Vector | Function Vector | $\|\ \mathbf {x} _{i}-\mathbf {x} _{i-1}\|_{2}$ |
| 0 | $\mathbf {x} _{0}=\left[100,100\right]$ | $\mathbf {F} (\mathbf {x} _{0})~=~{\begin{bmatrix}{\begin{aligned}~&\quad 375.08\\~&-44.92\end{aligned}}\end{bmatrix}}$ | \- |
| 1 | $\mathbf {x} _{1}=\left[47.99347513,132.16007766\right]$ | $\mathbf {F} (\mathbf {x} _{1})~=~{\begin{bmatrix}{\begin{aligned}~&-579.72039\\~&-56.19573\end{aligned}}\end{bmatrix}}$ | $16.07552$ |
| 2 | $\mathbf {x} _{2}=\left[60.16520202,142.66110819\right]$ | $\mathbf {F} (\mathbf {x} _{2})~=~{\begin{bmatrix}{\begin{aligned}~&-120.66290\\~&-4.85837\end{aligned}}\end{bmatrix}}$ | $6.48393$ |
| 3 | $\mathbf {x} _{3}=\left[65.34915899,138.76649357\right]$ | $\mathbf {F} (\mathbf {x} _{3})~=~{\begin{bmatrix}{\begin{aligned}~&-6.43007\\~&-0.34509\end{aligned}}\end{bmatrix}}$ | $4.03613\times 10^{-1}$ |
| 4 | $\mathbf {x} _{4}=\left[65.68871009,138.5482994\right]$ | $\mathbf {F} (\mathbf {x} _{4})~=~{\begin{bmatrix}{\begin{aligned}~&\quad 3.13226\times 10^{-1}\\~&-1.20192\times 10^{-3}\end{aligned}}\end{bmatrix}}$ | $2.79029\times 10^{-2}$ |
| 5 | $\mathbf {x} _{5}=\left[65.67075217,138.56965564\right]$ | $\mathbf {F} (\mathbf {x} _{5})~=~{\begin{bmatrix}{\begin{aligned}~&-1.88252\times 10^{-2}\\~&-9.54744\times 10^{-6}\end{aligned}}\end{bmatrix}}$ | $1.63648\times 10^{-3}$ |
| 6 | $\mathbf {x} _{6}=\left[65.67182534,138.56842016\right]$ | $\mathbf {F} (\mathbf {x} _{6})~=~{\begin{bmatrix}{\begin{aligned}~&\quad 1.11786\times 10^{-3}\\~&-3.20764\times 10^{-8}\end{aligned}}\end{bmatrix}}$ | $9.74697\times 10^{-5}$ |
| 7 | $\mathbf {x} _{7}=\left[65.67176157,138.56849388\right]$ | $\mathbf {F} (\mathbf {x} _{7})~=~{\begin{bmatrix}{\begin{aligned}~&-6.64497\times 10^{-5}\\~&-1.14255\times 10^{-10}\end{aligned}}\end{bmatrix}}$ | $5.79292\times 10^{-6}$ |
| 8 | $\mathbf {x} _{8}=\left[65.67176536,138.5684895\right]$ | $\mathbf {F} (\mathbf {x} _{8})~=~{\begin{bmatrix}{\begin{aligned}~&\quad 3.94975\times 10^{-6}\\~&-3.41060\times 10^{-13}\end{aligned}}\end{bmatrix}}$ | $3.44333\times 10^{-7}$ |

To show that $\mathbf {x} _{8}=\left[65.67176536,138.5684895\right]$ minimises $A(\mathbf {x} )$, it suffices to show that its [[Hessian Matrix]] is positive definite. In this case, the Hessian matrix is simply

$\mathbf {J} (\mathbf {x} _{8})\approx {\begin{bmatrix}~20.15939696&~2.27436075~\\~2.27436075&~1.9678865~\end{bmatrix}}.$

The [characteristic polynomial](https://en.wikipedia.org/wiki/Characteristic_polynomial) of this matrix is

$\lambda ^{2}-22.12728346\lambda +34.49868830=0$.

Applying the [quadratic formula](https://en.wikipedia.org/wiki/Quadratic_formula) gives the two eigenvalues as

$\lambda _{1}={\frac {22.12728346+{\sqrt {351.62192}}}{2}}\approx 20.43943$

and

$\lambda _{2}={\frac {22.12728346-{\sqrt {351.62192}}}{2}}\approx 1.68784.$

Since all eigenvalues are positive, $\mathbf {J} (\mathbf {x} _{8})$ is positive definite, and therefore $\mathbf {x} _{8}$ is a minimum.

### Complex functions

![[media/4d2a37854bcd2fd4db9dc49a97dc6d856b2bce6c.png]]
Basins of attraction for <var style="padding-right: 1px;">x</var><sup>5</sup> − 1 = 0; darker means more iterations to converge.

When dealing with [complex functions](https://en.wikipedia.org/wiki/Complex_analysis), Newton's method can be directly applied to find their zeroes. Each zero has a [basin of attraction](https://en.wikipedia.org/wiki/Basin_of_attraction) in the complex plane, the set of all starting values that cause the method to converge to that particular zero. These sets can be mapped as in the image shown. For many complex functions, the boundaries of the basins of attraction are [fractals](https://en.wikipedia.org/wiki/Fractal).

In some cases there are regions in the complex plane which are not in any of these basins of attraction, meaning the iterates do not converge. For example, if one uses a real initial condition to seek a root of `x`<sup>2</sup> + 1, all subsequent iterates will be real numbers and so the iterations cannot converge to either root, since both roots are non-real. In this case [almost all](https://en.wikipedia.org/wiki/Almost_all) real initial conditions lead to [chaotic behavior](https://en.wikipedia.org/wiki/Chaos_theory), while some initial conditions iterate either to infinity or to repeating cycles of any finite length.

Curt McMullen has shown that for any possible purely iterative algorithm similar to Newton's method, the algorithm will diverge on some open regions of the complex plane when applied to some polynomial of degree 4 or higher. However, McMullen gave a generally convergent algorithm for polynomials of degree 3. Also, for any polynomial, Hubbard, Schleicher, and Sutherland gave a method for selecting a set of initial points such that Newton's method will certainly converge at one of them at least.

### In a Banach space

Another generalization is Newton's method to find a root of a [functional](https://en.wikipedia.org/wiki/Functional_(mathematics) "Functional (mathematics)") F defined in a [Banach space](https://en.wikipedia.org/wiki/Banach_space). In this case the formulation is

$$
X_{n+1}=X_{n}-{\bigl (}F'(X_{n}){\bigr )}^{-1}F(X_{n}),\,
$$

where `F``′`(`X`<sub>`n`</sub>) is the [Fréchet derivative](https://en.wikipedia.org/wiki/Fr%C3%A9chet_derivative) computed at `X`<sub>`n`</sub>. One needs the Fréchet derivative to be boundedly invertible at each `X`<sub>`n`</sub> in order for the method to be applicable. A condition for existence of and convergence to a root is given by the [Newton–Kantorovich theorem](https://en.wikipedia.org/wiki/Kantorovich_theorem).

#### Nash–Moser iteration

In the 1950s, [John Nash](https://en.wikipedia.org/wiki/John_Forbes_Nash_Jr.) developed a version of the Newton's method to apply to the problem of constructing [isometric embeddings](https://en.wikipedia.org/wiki/Isometric_embedding) of general [Riemannian manifolds](https://en.wikipedia.org/wiki/Riemannian_manifold) in [Euclidean space](https://en.wikipedia.org/wiki/Euclidean_space). The *loss of derivatives* problem, present in this context, made the standard Newton iteration inapplicable, since it could not be continued indefinitely (much less converge). Nash's solution involved the introduction of [smoothing](https://en.wikipedia.org/wiki/Smoothing) operators into the iteration. He was able to prove the convergence of his smoothed Newton method, for the purpose of proving an [[Implicit Function Theorem]] for isometric embeddings. In the 1960s, [Jürgen Moser](https://en.wikipedia.org/wiki/J%C3%BCrgen_Moser) showed that Nash's methods were flexible enough to apply to problems beyond isometric embedding, particularly in [celestial mechanics](https://en.wikipedia.org/wiki/Celestial_mechanics). Since then, a number of mathematicians, including [Mikhael Gromov](https://en.wikipedia.org/wiki/Mikhael_Gromov_(mathematician) "Mikhael Gromov (mathematician)") and [Richard Hamilton](https://en.wikipedia.org/wiki/Richard_S._Hamilton), have found generalized abstract versions of the Nash–Moser theory. In Hamilton's formulation, the Nash–Moser theorem forms a generalization of the Banach space Newton method which takes place in certain [Fréchet spaces](https://en.wikipedia.org/wiki/Fr%C3%A9chet_space).

## Modifications

### Quasi-Newton methods

When the Jacobian is unavailable or too expensive to compute at every iteration, a [quasi-Newton method](https://en.wikipedia.org/wiki/Quasi-Newton_method) can be used.

### Chebyshev's third-order method

Since higher-order Taylor expansions offer more accurate local approximations of a function f, it is reasonable to ask why Newton’s method relies only on a second-order Taylor approximation. In the 19th century, Russian mathematician Pafnuty Chebyshev explored this idea by developing a variant of Newton’s method that used cubic approximations.

### Over p-adic numbers

In p-adic analysis, the standard method to show a polynomial equation in one variable has a p-adic root is [Hensel's lemma](https://en.wikipedia.org/wiki/Hensel%27s_lemma), which uses the recursion from Newton's method on the p-adic numbers. Because of the more stable behavior of addition and multiplication in the p-adic numbers compared to the real numbers (specifically, the unit ball in the p-adics is a ring), convergence in Hensel's lemma can be guaranteed under much simpler hypotheses than in the classical Newton's method on the real line.

### q-analog

Newton's method can be generalized with the [q-analog](https://en.wikipedia.org/wiki/Q-analog) of the usual derivative.

### Modified Newton methods

#### Maehly's procedure

A nonlinear equation has multiple solutions in general. But if the initial value is not appropriate, Newton's method may not converge to the desired solution or may converge to the same solution found earlier. When we have already found N solutions of $f(x)=0$, then the next root can be found by applying Newton's method to the next equation:

$$
F(x)={\frac {f(x)}{\prod _{i=1}^{N}(x-x_{i})}}=0.
$$

This method is applied to obtain zeros of the [Bessel function](https://en.wikipedia.org/wiki/Bessel_function) of the second kind.

#### Hirano's modified Newton method

Hirano's modified Newton method is a modification conserving the convergence of Newton method and avoiding unstableness. It is developed to solve complex polynomials.

#### Interval Newton's method

Combining Newton's method with [interval arithmetic](https://en.wikipedia.org/wiki/Interval_arithmetic) is very useful in some contexts. This provides a stopping criterion that is more reliable than the usual ones (which are a small value of the function or a small variation of the variable between consecutive iterations). Also, this may detect cases where Newton's method converges theoretically but diverges numerically because of an insufficient [[Floating-Point Arithmetic|floating-point precision]] (this is typically the case for polynomials of large degree, where a very small change of the variable may change dramatically the value of the function; see [Wilkinson's polynomial](https://en.wikipedia.org/wiki/Wilkinson%27s_polynomial)).

Consider `f` → C<sup>1</sup>(`X`), where X is a real interval, and suppose that we have an interval extension F′ of f′, meaning that F′ takes as input an interval `Y` ⊆ `X` and outputs an interval `F``′`(`Y`) such that:

$$
{\begin{aligned}F'([y,y])&=\{f'(y)\}\\[5pt]F'(Y)&\supseteq \{f'(y)\mid y\in Y\}.\end{aligned}}
$$

We also assume that 0 ∉ `F``′`(`X`), so in particular f has at most one root in X. We then define the interval Newton operator by:

$$
N(Y)=m-{\frac {f(m)}{F'(Y)}}=\left\{\left.m-{\frac {f(m)}{z}}~\right|~z\in F'(Y)\right\}
$$

where `m` ∈ `Y`. Note that the hypothesis on F′ implies that `N`(`Y`) is well defined and is an interval (see [interval arithmetic](https://en.wikipedia.org/wiki/Interval_arithmetic) for further details on interval operations). This naturally leads to the following sequence:

$$
{\begin{aligned}X_{0}&=X\\X_{k+1}&=N(X_{k})\cap X_{k}.\end{aligned}}
$$

The [mean value theorem](https://en.wikipedia.org/wiki/Mean_value_theorem) ensures that if there is a root of f in `X`<sub>`k`</sub>, then it is also in `X`<sub>`k` + 1</sub>. Moreover, the hypothesis on F′ ensures that `X`<sub>`k` + 1</sub> is at most half the size of `X`<sub>`k`</sub> when m is the midpoint of Y, so this sequence converges towards \[`x*`, `x*`\], where x\* is the root of f in X.

If `F``′`(`X`) strictly contains 0, the use of extended interval division produces a union of two intervals for `N`(`X`); multiple roots are therefore automatically separated and bounded.

## Applications

### Minimization and maximization problems

Newton's method can be used to find a minimum or maximum of a function `f`(`x`). The derivative is zero at a minimum or maximum, so local minima and maxima can be found by applying Newton's method to the derivative. The iteration becomes:

$$
x_{n+1}=x_{n}-{\frac {f'(x_{n})}{f''(x_{n})}}.
$$

### Multiplicative inverses of numbers and power series

An important application is [Newton–Raphson division](https://en.wikipedia.org/wiki/Division_algorithm#Newton–Raphson_division), which can be used to quickly find the [reciprocal](https://en.wikipedia.org/wiki/Multiplicative_inverse) of a number a, using only multiplication and subtraction, that is to say the number x such that 1/`x` = `a`. We can rephrase that as finding the zero of `f`(`x`) = 1/`x` − `a`. We have `f``′`(`x`) = −1/`x`<sup>2</sup>.

Newton's iteration is

$$
x_{n+1}=x_{n}-{\frac {f(x_{n})}{f'(x_{n})}}=x_{n}+{\frac {{\frac {1}{x_{n}}}-a}{\frac {1}{x_{n}^{2}}}}=x_{n}(2-ax_{n}).
$$

Therefore, Newton's iteration needs only two multiplications and one subtraction.

This method is also very efficient to compute the multiplicative inverse of a [power series](https://en.wikipedia.org/wiki/Power_series).

### Solving transcendental equations

Many [transcendental equations](https://en.wikipedia.org/wiki/Transcendental_equation) can be solved up to an arbitrary precision by using Newton's method. For example, finding the cumulative [[Probability Density Function]], such as a [Normal distribution](https://en.wikipedia.org/wiki/Normal_distribution) to fit a known probability generally involves integral functions with no known means to solve in closed form. However, computing the derivatives needed to solve them numerically with Newton's method is generally known, making numerical solutions possible. For an example, see the numerical solution to the [inverse Normal cumulative distribution](https://en.wikipedia.org/wiki/Normal_distribution#Using_the_Taylor_series_and_Newton's_method_for_the_inverse_function).

### Numerical verification for solutions of nonlinear equations

A numerical verification for solutions of nonlinear equations has been established by using Newton's method multiple times and forming a set of solution candidates.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

## Code

The following is an example of a possible implementation of Newton's method in the [Python](https://en.wikipedia.org/wiki/Python_(programming_language) "Python (programming language)") (version 3.x) programming language for finding a root of a function `f` which has derivative `f_prime`.

The initial guess will be `x`<sub>0</sub> = 1 and the function will be `f`(`x`) = `x`<sup>2</sup> − 2 so that `f``′`(`x`) = 2`x`.

Each new iteration of Newton's method will be denoted by `x1`. We will check during the computation whether the denominator (`y_prime`) becomes too small (smaller than `epsilon`), which would be the case if `f``′`(`x`<sub>`n`</sub>) ≈ 0, since otherwise a large amount of error could be introduced.

    def f(x):             
     return x**2 - 2   # f(x) = x^2 - 2

    def f_prime(x):
     return 2*x        # f'(x) = 2x

    def newtons_method(x0, f, f_prime, tolerance, epsilon, max_iterations):
        """Newton's method

        Args:
          x0:              The initial guess
          f:               The function whose root we are trying to find
          f_prime:         The derivative of the function
          tolerance:       Stop when iterations change by less than this
          epsilon:         Do not divide by a number smaller than this
          max_iterations:  The maximum number of iterations to compute
        """
        for _ in range(max_iterations):
            y = f(x0)
            y_prime = f_prime(x0)

            if abs(y_prime) < epsilon:       # Give up if the denominator is too small
                break

            x1 = x0 - y / y_prime            # Do Newton's computation

            if abs(x1 - x0) <= tolerance:   # Stop when the result is within the desired tolerance
                return x1                   # x1 is a solution within tolerance and maximum number of iterations

            x0 = x1                         # Update x0 to start the process again

        return None                         # Newton's method did not converge

## See also

- [Aitken's delta-squared process](https://en.wikipedia.org/wiki/Aitken%27s_delta-squared_process)
- [Bisection method](https://en.wikipedia.org/wiki/Bisection_method)
- [Euler method](https://en.wikipedia.org/wiki/Euler_method)
- [Fast inverse square root](https://en.wikipedia.org/wiki/Fast_inverse_square_root)
- [Fisher scoring](https://en.wikipedia.org/wiki/Scoring_algorithm#Fisher_scoring)
- [[Gradient Descent]]
- [Integer square root](https://en.wikipedia.org/wiki/Integer_square_root)
- [Kantorovich theorem](https://en.wikipedia.org/wiki/Kantorovich_theorem)
- [Laguerre's method](https://en.wikipedia.org/wiki/Laguerre%27s_method)
- [Methods of computing square roots](https://en.wikipedia.org/wiki/Methods_of_computing_square_roots)
- [Newton's method in optimization](https://en.wikipedia.org/wiki/Newton%27s_method_in_optimization)
- [Richardson extrapolation](https://en.wikipedia.org/wiki/Richardson_extrapolation)
- [Root-finding algorithm](https://en.wikipedia.org/wiki/Root-finding_algorithm)
- [Secant method](https://en.wikipedia.org/wiki/Secant_method)
- [Steffensen's method](https://en.wikipedia.org/wiki/Steffensen%27s_method)
- [Subgradient method](https://en.wikipedia.org/wiki/Subgradient_method)

## Notes

1.  Fowler, David; Robson, Eleanor (1998). ["Square root approximations in Old Babylonian mathematics: YBC 7289 in context"](https://doi.org/10.1006%2Fhmat.1998.2209). *Historia Mathematica*. **25** (4): 366–378. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1006/hmat.1998.2209](https://doi.org/10.1006%2Fhmat.1998.2209).
2.  ^    Ypma, Tjalling J. (1995). ["Historical Development of the Newton-Raphson Method"](https://www.jstor.org/stable/2132904). *SIAM Review*. **37** (4): 531–551. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/1037125](https://doi.org/10.1137%2F1037125). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0036-1445](https://search.worldcat.org/issn/0036-1445). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2132904](https://www.jstor.org/stable/2132904).
3.  ^   Md Sarowar Morshed (2022). "Augmented Newton Method for Optimization: Global Linear Rate and Momentum Interpretation". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2205.11033](https://arxiv.org/abs/2205.11033) \[[math.OC](https://arxiv.org/archive/math.OC)\].
4.  ^   Cajori, Florian (1911). ["Historical Note on the Newton-Raphson Method of Approximation"](https://www.jstor.org/stable/2973939). *The American Mathematical Monthly*. **18** (2): 29–32. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2973939](https://doi.org/10.2307%2F2973939). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0002-9890](https://search.worldcat.org/issn/0002-9890). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2973939](https://www.jstor.org/stable/2973939).
5.  Guicciardini, Niccolò (2009). [Isaac Newton on Mathematical Certainty and Method](https://books.google.com/books?id=uqnuDwAAQBAJ&pg=PA158). Transformations. Cambridge, Mass: [MIT Press](https://en.wikipedia.org/wiki/MIT_Press). pp. 158–159. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-262-01317-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-262-01317-8). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [282968643](https://search.worldcat.org/oclc/282968643).
6.  Ypma, Tjalling J. (1995). ["Historical Development of the Newton-Raphson Method"](https://www.jstor.org/stable/2132904). *SIAM Review*. **37** (4): 531–551. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/1037125](https://doi.org/10.1137%2F1037125). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0036-1445](https://search.worldcat.org/issn/0036-1445). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2132904](https://www.jstor.org/stable/2132904).
7.  ["Takakazu Seki - Biography"](https://mathshistory.st-andrews.ac.uk/Biographies/Seki/#:~:text=In%201685,%20he%20solved%20the,b%20a,b%20are%20integers.). *Maths History*. Retrieved 27 November 2024.
8.  [Wallis, John](https://en.wikipedia.org/wiki/John_Wallis) (1685). [A Treatise of Algebra, both Historical and Practical](http://www.e-rara.ch/zut/content/titleinfo/2507537). Oxford: Richard Davis. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3931/e-rara-8842](https://doi.org/10.3931%2Fe-rara-8842).
9.  [Raphson, Joseph](https://en.wikipedia.org/wiki/Joseph_Raphson) (1697). [Analysis Æequationum Universalis](https://archive.org/details/bub_gb_4nlbAAAAQAAJ) (in Latin) (2nd ed.). London: Thomas Bradyll. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3931/e-rara-13516](https://doi.org/10.3931%2Fe-rara-13516).
10. ["Accelerated and Modified Newton Methods"](https://web.archive.org/web/20190524083302/http://mathfaculty.fullerton.edu/mathews/n2003/NewtonAccelerateMod.html). Archived from [the original](http://mathfaculty.fullerton.edu/mathews/n2003/newtonacceleratemod.html) on 24 May 2019. Retrieved 4 March 2016.
11. ^   J. E. Dennis, Jr. and Robert B. Schnabel. Numerical methods for unconstrained optimization and nonlinear equations. SIAM
12. Anthony Ralston and Philip Rabinowitz. A first course in numerical analysis, second edition
13. Yuri Nesterov. Lectures on convex optimization, second edition. Springer Optimization and its Applications, Volume 137.
14. .
15. ^    Kenneth L. Judd. Numerical methods in economics. MIT Press
16. Ryaben'kii, Victor S.; Tsynkov, Semyon V. (2006), [A Theoretical Introduction to Numerical Analysis](https://books.google.com/books?id=V8gWP031-hEC&pg=PA243), CRC Press, p. 243, [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9781584886075](https://en.wikipedia.org/wiki/Special:BookSources/9781584886075).
17. , Exercise 1.6
18. ^    [Ostrowski, A. M.](https://en.wikipedia.org/wiki/Alexander_Ostrowski) (1973). *Solution of equations in Euclidean and Banach spaces*. Pure and Applied Mathematics. Vol. 9 (Third edition of 1960 original ed.). New York–London: [Academic Press](https://en.wikipedia.org/wiki/Academic_Press). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0359306](https://mathscinet.ams.org/mathscinet-getitem?mr=0359306). [Zbl](https://en.wikipedia.org/wiki/Zbl_(identifier)) [0304.65002](https://zbmath.org/?format=complete&q=an:0304.65002).
19. Ortega and Rheinboldt, Section 13.3
20. [Traub, J. F.](https://en.wikipedia.org/wiki/Joseph_F._Traub) (1964). *Iterative methods for the solution of equations*. Prentice-Hall Series in Automatic Computation. Englewood Cliffs, NJ: [Prentice-Hall, Inc.](https://en.wikipedia.org/wiki/Prentice-Hall,_Inc.) [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0169356](https://mathscinet.ams.org/mathscinet-getitem?mr=0169356). [Zbl](https://en.wikipedia.org/wiki/Zbl_(identifier)) [0121.11204](https://zbmath.org/?format=complete&q=an:0121.11204).
21. [Johnson, Steven G.](https://en.wikipedia.org/wiki/Steven_G._Johnson) (4 February 2015). ["Square Roots via Newton's Method"](https://math.mit.edu/~stevenj/18.335/newton-sqrt.pdf) (PDF). *MIT Course 18.335 – Numerical Methods*. Massachusetts Institute of Technology. Retrieved 5 November 2025.
22. Burden, Burton; Fairs, J. Douglas; Reunolds, Albert C (July 1981). [Numerical Analysis](https://archive.org/details/numericalanaly00burd/) (2nd ed.). Boston, MA, United States: Prindle, Weber & Schmidt. pp. 448–452. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-87150-314-X](https://en.wikipedia.org/wiki/Special:BookSources/0-87150-314-X). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [1036752194](https://search.worldcat.org/oclc/1036752194).
23. Evans, Gwynne A. (1995). [Practical Numerical Analysis](https://archive.org/details/practicalnumeric0000evan/). Chichester: John Wiley & Sons. pp. 30–33. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0471955353](https://en.wikipedia.org/wiki/Special:BookSources/0471955353). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [1319419671](https://search.worldcat.org/oclc/1319419671).
24. Demidovich, Boris Pavlovich; Maron, Isaak Abramovich (1981). [Computational Mathematics](https://archive.org/details/computational-mathematics/mode/2up) (Third ed.). Moscow: MIR Publishers. pp. 460–478. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780828507042](https://en.wikipedia.org/wiki/Special:BookSources/9780828507042).
25. Kiusalaas, Jaan (March 2013). [Numerical Methods in Engineering with Python 3](https://www.cambridge.org/9781107033856) (3rd ed.). New York: Cambridge University Press. pp. 175–176. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-107-03385-6](https://en.wikipedia.org/wiki/Special:BookSources/978-1-107-03385-6).
26. James, Glyn (1993). [Advanced Modern Engineering Mathematics](https://archive.org/details/advancedmodernen0000jame). Wokingham, England: Addison-Wesley. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0201565196](https://en.wikipedia.org/wiki/Special:BookSources/0201565196).
27. [Henrici, Peter](https://en.wikipedia.org/wiki/Peter_Henrici_(mathematician) "Peter Henrici (mathematician)") (1974). *Applied and Computational Complex Analysis*. Vol. 1. Wiley. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780471598923](https://en.wikipedia.org/wiki/Special:BookSources/9780471598923).
28. Strang, Gilbert (January 1991). "A chaotic search for i". *[The College Mathematics Journal](https://en.wikipedia.org/wiki/The_College_Mathematics_Journal)*. **22** (1): 3–12. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2686733](https://doi.org/10.2307%2F2686733). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2686733](https://www.jstor.org/stable/2686733).
29. McMullen, Curt (1987). ["Families of rational maps and iterative root-finding algorithms"](https://dash.harvard.edu/bitstream/handle/1/9876064/McMullen_FamiliesRationalMap.pdf?sequence=1) (PDF). *Annals of Mathematics*. Second Series. **125** (3): 467–493. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/1971408](https://doi.org/10.2307%2F1971408). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [1971408](https://www.jstor.org/stable/1971408).
30. Hubbard, John; Schleicher, Dierk; Sutherland, Scott (October 2001). ["How to find all roots of complex polynomials by Newton's method"](https://dx.doi.org/10.1007/s002220100149). *Inventiones Mathematicae*. **146** (1): 1–33. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2001InMat.146....1H](https://ui.adsabs.harvard.edu/abs/2001InMat.146....1H). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s002220100149](https://doi.org/10.1007%2Fs002220100149). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0020-9910](https://search.worldcat.org/issn/0020-9910). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [12603806](https://api.semanticscholar.org/CorpusID:12603806).
31. Yamamoto, Tetsuro (2001). "Historical Developments in Convergence Analysis for Newton's and Newton-like Methods". In Brezinski, C.; Wuytack, L. (eds.). *Numerical Analysis: Historical Developments in the 20th Century*. North-Holland. pp. 241–263. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-444-50617-9](https://en.wikipedia.org/wiki/Special:BookSources/0-444-50617-9).
32. [Hamilton, Richard S.](https://en.wikipedia.org/wiki/Richard_S._Hamilton) (1982). ["The inverse function theorem of Nash and Moser"](https://doi.org/10.1090%2Fs0273-0979-1982-15004-2). *[Bulletin of the American Mathematical Society](https://en.wikipedia.org/wiki/Bulletin_of_the_American_Mathematical_Society)*. New Series. **7** (1): 65–222. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1090/s0273-0979-1982-15004-2](https://doi.org/10.1090%2Fs0273-0979-1982-15004-2). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0656198](https://mathscinet.ams.org/mathscinet-getitem?mr=0656198). [Zbl](https://en.wikipedia.org/wiki/Zbl_(identifier)) [0499.58003](https://zbmath.org/?format=complete&q=an:0499.58003).
33. [Gromov, Mikhael](https://en.wikipedia.org/wiki/Mikhael_Gromov_(mathematician) "Mikhael Gromov (mathematician)") (1986). *Partial differential relations*. Ergebnisse der Mathematik und ihrer Grenzgebiete (3). Vol. 9. Berlin: [Springer-Verlag](https://en.wikipedia.org/wiki/Springer-Verlag). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-3-662-02267-2](https://doi.org/10.1007%2F978-3-662-02267-2). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [3-540-12177-3](https://en.wikipedia.org/wiki/Special:BookSources/3-540-12177-3). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0864505](https://mathscinet.ams.org/mathscinet-getitem?mr=0864505).
34. Chebyshev, Pafnutii L'vovich; Bernshtein, Sergei Natanovich (1947). *Polnoe sobranie sochinenii*. Izd-vo Akademii nauk SSSR.
35. Ahmadi, Amir Ali; Chaudhry, Abraar; Zhang, Jeffrey (2024). ["Higher-order Newton methods with polynomial work per iteration"](https://linkinghub.elsevier.com/retrieve/pii/S0001870824003232). *[Advances in Mathematics](https://en.wikipedia.org/wiki/Advances_in_Mathematics)*. **452** 109808. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2311.06374](https://arxiv.org/abs/2311.06374). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.aim.2024.109808](https://doi.org/10.1016%2Fj.aim.2024.109808).
36. Hartnett, Kevin (24 March 2025). ["Three Hundred Years Later, a Tool from Isaac Newton Gets an Update"](https://www.quantamagazine.org/three-hundred-years-later-a-tool-from-isaac-newton-gets-an-update-20250324/). *Quanta Magazine*. Retrieved 3 April 2025.
37. Rajković, Predrag M.; Stanković, Miomir S.; Marinković, Slađana D. (2002). ["Mean value theorems in $q$-calculus"](https://www.emis.de/journals/MV/0234/16.html). *Matematicki Vesnik*. **54** (3–4): 171–178.
38. 39. Stoer, Josef; Bulirsch, Roland (1980). [Introduction to numerical analysis](https://archive.org/details/introductiontonu0000stoe/mode/2up). p. 279. [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [1244842246](https://search.worldcat.org/oclc/1244842246).
40. Zhang, Shanjie; Jin, Jianming (1996). *Computation of Special Functions*. Wiley. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780471119630](https://en.wikipedia.org/wiki/Special:BookSources/9780471119630).<sup>\[*[page needed](https://en.wikipedia.org/wiki/Wikipedia:Citing_sources)*\]</sup>
41. Murota, Kazuo (1982). "Global Convergence of a Modified Newton Iteration for Algebraic Equations". *SIAM Journal on Numerical Analysis*. **19** (4): 793–799. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1982SJNA...19..793M](https://ui.adsabs.harvard.edu/abs/1982SJNA...19..793M). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/0719055](https://doi.org/10.1137%2F0719055).
42. Moore, R. E. (1979). *Methods and applications of interval analysis* (Vol. 2). Siam.
43. Hansen, E. (1978). Interval forms of Newtons method. *Computing*, 20(2), 153–163.
44. [Boyd, Stephen](https://en.wikipedia.org/wiki/Stephen_P._Boyd); Vandenberghe, Lieven (2004). *Convex optimization*. Cambridge: [Cambridge University Press](https://en.wikipedia.org/wiki/Cambridge_University_Press). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1017/CBO9780511804441](https://doi.org/10.1017%2FCBO9780511804441). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-83378-7](https://en.wikipedia.org/wiki/Special:BookSources/0-521-83378-7). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [2061575](https://mathscinet.ams.org/mathscinet-getitem?mr=2061575). [Zbl](https://en.wikipedia.org/wiki/Zbl_(identifier)) [1058.90049](https://zbmath.org/?format=complete&q=an:1058.90049).

## References

- Gil, A.; Segura, J.; Temme, N. M. (2007). [Numerical methods for special functions](https://www.researchgate.net/publication/220693008). Society for Industrial and Applied Mathematics. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-89871-634-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-89871-634-4).
- [Süli, Endre](https://en.wikipedia.org/wiki/Endre_S%C3%BCli); Mayers, David (2003). *An Introduction to Numerical Analysis*. Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-00794-1](https://en.wikipedia.org/wiki/Special:BookSources/0-521-00794-1).

## Further reading

- Kendall E. Atkinson: *An Introduction to Numerical Analysis*, John Wiley & Sons Inc., [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-62489-6](https://en.wikipedia.org/wiki/Special:BookSources/0-471-62489-6) (1989).
- Tjalling J. Ypma: "Historical development of the Newton–Raphson method", SIAM Review, vol.37, no.4, (1995), pp. 531–551. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/1037125](https://doi.org/10.1137%2F1037125).
- Bonnans, J. Frédéric; Gilbert, J. Charles; [Lemaréchal, Claude](https://en.wikipedia.org/wiki/Claude_Lemar%C3%A9chal); [Sagastizábal, Claudia A.](https://en.wikipedia.org/wiki/Claudia_Sagastiz%C3%A1bal) (2006). [Numerical optimization: Theoretical and practical aspects](https://www.springer.com/mathematics/applications/book/978-3-540-35445-1). Universitext (Second revised ed. of translation of 1997 French ed.). Berlin: Springer-Verlag. pp. xiv+490. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-3-540-35447-5](https://doi.org/10.1007%2F978-3-540-35447-5). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [3-540-35445-X](https://en.wikipedia.org/wiki/Special:BookSources/3-540-35445-X). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [2265882](https://mathscinet.ams.org/mathscinet-getitem?mr=2265882).
- P. Deuflhard: *Newton Methods for Nonlinear Problems: Affine Invariance and Adaptive Algorithms*, Springer Berlin (Series in Computational Mathematics, Vol. 35) (2004). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [3-540-21099-7](https://en.wikipedia.org/wiki/Special:BookSources/3-540-21099-7).
- C. T. Kelley: *Solving Nonlinear Equations with Newton's Method*, SIAM (Fundamentals of Algorithms, 1) (2003). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-89871-546-6](https://en.wikipedia.org/wiki/Special:BookSources/0-89871-546-6).
- J. M. Ortega, and W. C. Rheinboldt: *Iterative Solution of Nonlinear Equations in Several Variables*, SIAM (Classics in Applied Mathematics) (2000). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-89871-461-3](https://en.wikipedia.org/wiki/Special:BookSources/0-89871-461-3).
- Press, W. H.; Teukolsky, S. A.; Vetterling, W. T.; Flannery, B. P. (2007). ["Chapter 9. Root Finding and Nonlinear Sets of Equations Importance Sampling"](http://apps.nrbook.com/empanel/index.html#pg=442). *Numerical Recipes: The Art of Scientific Computing* (3rd ed.). New York: Cambridge Univ. Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-88068-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-88068-8).. See especially Sections [9.4](http://apps.nrbook.com/empanel/index.html#pg=456), [9.6](http://apps.nrbook.com/empanel/index.html#pg=473), and [9.7](http://apps.nrbook.com/empanel/index.html#pg=477).
- Avriel, Mordecai (1976). **Nonlinear Programming: Analysis and Methods**. Prentice Hall. pp. 216–221. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-13-623603-0](https://en.wikipedia.org/wiki/Special:BookSources/0-13-623603-0).

## External links

- ["Newton method"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society), 2001 \[1994\]
- [Weisstein, Eric W.](https://en.wikipedia.org/wiki/Eric_W._Weisstein) ["Newton's Method"](https://mathworld.wolfram.com/NewtonsMethod.html). *[MathWorld](https://en.wikipedia.org/wiki/MathWorld)*.
- [Newton's method, Citizendium.](http://en.citizendium.org/wiki/Newton%27s_method)
- [Mathews, J., The Accelerated and Modified Newton Methods, Course notes.](https://web.archive.org/web/20190524083302/http://mathfaculty.fullerton.edu/mathews/n2003/NewtonAccelerateMod.html)
- [Wu, X., Roots of Equations, Course notes.](http://www.ece.mcmaster.ca/~xwu/part2.pdf)
