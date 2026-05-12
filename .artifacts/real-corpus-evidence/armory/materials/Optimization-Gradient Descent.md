[[optimization.base]]

> Source: [[Gradient Descent]]
> License: Wikipedia content is available under CC BY-SA 4.0.

Gradient descent in 2D

**Gradient descent** is a method for unconstrained [mathematical optimization](https://en.wikipedia.org/wiki/Mathematical_optimization). It is a [first-order](https://en.wikipedia.org/wiki/Category:First_order_methods) [iterative](https://en.wikipedia.org/wiki/Iterative_algorithm) [algorithm](https://en.wikipedia.org/wiki/Algorithm) for minimizing a [differentiable](https://en.wikipedia.org/wiki/Differentiable_function) [multivariate function](https://en.wikipedia.org/wiki/Multivariate_function).

The idea is to take repeated steps in the opposite direction of the [gradient](https://en.wikipedia.org/wiki/Gradient) (or approximate gradient) of the function at the current point, because this is the direction of steepest descent. Conversely, stepping in the direction of the gradient will lead to a trajectory that maximizes that function; the procedure is then known as *gradient ascent*. It is particularly useful in [machine learning](https://en.wikipedia.org/wiki/Machine_learning) and [artificial intelligence](https://en.wikipedia.org/wiki/Artificial_intelligence) for minimizing the cost or loss function. Gradient descent should not be confused with [local search](https://en.wikipedia.org/wiki/Local_search_(optimization) "Local search (optimization)") algorithms, although both are [iterative methods](https://en.wikipedia.org/wiki/Iterative_method) for [optimization](https://en.wikipedia.org/wiki/Global_optimization).

Gradient descent is generally attributed to [Augustin-Louis Cauchy](https://en.wikipedia.org/wiki/Augustin-Louis_Cauchy), who first suggested it in 1847. [Jacques Hadamard](https://en.wikipedia.org/wiki/Jacques_Hadamard) independently proposed a similar method in 1907. Its convergence properties for non-linear optimization problems were first studied by [Haskell Curry](https://en.wikipedia.org/wiki/Haskell_Curry) in 1944, with the method becoming increasingly well-studied and used in the following decades.

A simple extension of gradient descent, [[Stochastic Gradient Descent]], serves as the most basic algorithm used for training most [deep networks](https://en.wikipedia.org/wiki/Deep_neural_network) today.

## Description

![[media/f8bb1f1fa622c5081e18c5381defae6c0718d24b.png]]
Illustration of gradient descent on a series of [level sets](https://en.wikipedia.org/wiki/Level_set)

Gradient descent is based on the observation that if the [multi-variable function](https://en.wikipedia.org/wiki/Multi-variable_function) $f(\mathbf {x} )$ is [defined](https://en.wikipedia.org/wiki/Defined_and_undefined) and [differentiable](https://en.wikipedia.org/wiki/Differentiable_function) in a neighborhood of a point $\mathbf {a}$, then $f(\mathbf {x} )$ decreases *fastest* if one goes from $\mathbf {a}$ in the direction of the negative [gradient](https://en.wikipedia.org/wiki/Gradient) of $f$ at $\mathbf {a} ,-\nabla f(\mathbf {a} )$. It follows that, if

$\mathbf {a} _{n+1}=\mathbf {a} _{n}-\eta \nabla f(\mathbf {a} _{n})$

for a small enough step size or [learning rate](https://en.wikipedia.org/wiki/Learning_rate) $\eta \in \mathbb {R} _{+}$, then $f(\mathbf {a_{n}} )\geq f(\mathbf {a_{n+1}} )$. In other words, the term $\eta \nabla f(\mathbf {a} )$ is subtracted from $\mathbf {a}$ because we want to move against the gradient, toward the local minimum. With this observation in mind, one starts with a guess $\mathbf {x} _{0}$ for a local minimum of $f$, and considers the sequence $\mathbf {x} _{0},\mathbf {x} _{1},\mathbf {x} _{2},\ldots$ such that

$\mathbf {x} _{n+1}=\mathbf {x} _{n}-\eta _{n}\nabla f(\mathbf {x} _{n}),\ n\geq 0.$

We have a [monotonic](https://en.wikipedia.org/wiki/Monotonic_function) sequence

$f(\mathbf {x} _{0})\geq f(\mathbf {x} _{1})\geq f(\mathbf {x} _{2})\geq \cdots ,$

so the sequence $(\mathbf {x} _{n})$ converges to the desired local minimum. Note that the value of the *step size* $\eta$ is allowed to change at every iteration.

It is possible to guarantee the [convergence](https://en.wikipedia.org/wiki/Convergent_series) to a local minimum under certain assumptions on the function $f$ (for example, $f$ [convex](https://en.wikipedia.org/wiki/Convex_function) and $\nabla f$ [Lipschitz](https://en.wikipedia.org/wiki/Lipschitz_continuity)) and particular choices of $\eta$. Those include the sequence

$\eta _{n}={\frac {\left|\left(\mathbf {x} _{n}-\mathbf {x} _{n-1}\right)^{\top }\left[\nabla f(\mathbf {x} _{n})-\nabla f(\mathbf {x} _{n-1})\right]\right|}{\left\|\nabla f(\mathbf {x} _{n})-\nabla f(\mathbf {x} _{n-1})\right\|^{2}}}$

as in the [Barzilai-Borwein method](https://en.wikipedia.org/wiki/Barzilai-Borwein_method), or a sequence $\eta _{n}$ satisfying the [Wolfe conditions](https://en.wikipedia.org/wiki/Wolfe_conditions) (which can be found by using [[Line Search]]). When the function $f$ is [convex](https://en.wikipedia.org/wiki/Convex_function), all local minima are also global minima, so in this case gradient descent can converge to the global solution.

This process is illustrated in the adjacent picture. Here, $f$ is assumed to be defined on the plane, and that its graph has a [bowl](https://en.wikipedia.org/wiki/Bowl_(vessel)) shape. The blue curves are the [contour lines](https://en.wikipedia.org/wiki/Contour_line), that is, the regions on which the value of $f$ is constant. A red arrow originating at a point shows the direction of the negative gradient at that point. Note that the (negative) gradient at a point is [orthogonal](https://en.wikipedia.org/wiki/Orthogonal) to the contour line going through that point. We see that gradient *descent* leads us to the bottom of the bowl, that is, to the point where the value of the function $f$ is minimal.

### An analogy for understanding gradient descent

![[media/f98189d67cd6685323c2bd5b14a1959e8e524bca.jpg]]
Fog in the mountains

The basic intuition behind gradient descent can be illustrated by a hypothetical scenario. People are stuck in the mountains and are trying to get down (i.e., trying to find the global minimum). There is heavy fog such that visibility is extremely low. Therefore, the path down the mountain is not visible, so they must use local information to find the minimum. They can use the method of gradient descent, which involves looking at the steepness of the hill at their current position, then proceeding in the direction with the steepest descent (i.e., downhill). If they were trying to find the top of the mountain (i.e., the maximum), then they would proceed in the direction of steepest ascent (i.e., uphill). Using this method, they would eventually find their way down the mountain or possibly get stuck in some hole (i.e., local minimum or [saddle point](https://en.wikipedia.org/wiki/Saddle_point)), like a mountain lake. However, assume also that the steepness of the hill is not immediately obvious with simple observation, but rather it requires a sophisticated instrument to measure, which the people happen to have at that moment. It takes quite some time to measure the steepness of the hill with the instrument. Thus, they should minimize their use of the instrument if they want to get down the mountain before sunset. The difficulty then is choosing the frequency at which they should measure the steepness of the hill so as not to go off track.

In this analogy, the people represent the algorithm, and the path taken down the mountain represents the sequence of parameter settings that the algorithm will explore. The steepness of the hill represents the [slope](https://en.wikipedia.org/wiki/Slope) of the function at that point. The instrument used to measure steepness is [differentiation](https://en.wikipedia.org/wiki/Differentiation_(mathematics)). The direction they choose to travel in aligns with the [gradient](https://en.wikipedia.org/wiki/Gradient) of the function at that point. The amount of time they travel before taking another measurement is the step size.

### Choosing the step size and descent direction

Since using a step size $\eta$ that is too small would slow convergence, and a $\eta$ too large would lead to overshoot and divergence, finding a good setting of $\eta$ is an important practical problem. [Philip Wolfe](https://en.wikipedia.org/wiki/Philip_Wolfe_(mathematician) "Philip Wolfe (mathematician)") also advocated using "clever choices of the \[descent\] direction" in practice. While using a direction that deviates from the steepest descent direction may seem counter-intuitive, the idea is that the smaller slope may be compensated for by being sustained over a much longer distance.

To reason about this mathematically, consider a direction $\mathbf {p} _{n}$ and step size $\eta _{n}$ and consider the more general update:

$\mathbf {a} _{n+1}=\mathbf {a} _{n}-\eta _{n}\,\mathbf {p} _{n}$.

Finding good settings of $\mathbf {p} _{n}$ and $\eta _{n}$ requires some thought. First of all, we would like the update direction to point downhill. Mathematically, letting $\theta _{n}$ denote the angle between $-\nabla f(\mathbf {a_{n}} )$ and $\mathbf {p} _{n}$, this requires that $\cos \theta _{n}>0.$ To say more, we need more information about the objective function that we are optimising. Under the fairly weak assumption that $f$ is continuously differentiable, we may prove that:

|  |  |  |
|----|----|----|
| $f(\mathbf {a} _{n+1})\leq f(\mathbf {a} _{n})-\eta _{n}\|\nabla f(\mathbf {a} _{n})\|_{2}\|\mathbf {p} _{n}\|_{2}\left(\cos \theta _{n}-\max _{t\in [0,1]}{\frac {\|\nabla f(\mathbf {a} _{n}-t\eta _{n}\mathbf {p} _{n})-\nabla f(\mathbf {a} _{n})\|_{2}}{\|\nabla f(\mathbf {a} _{n})\|_{2}}}\right)$ |  | 1 |

This inequality implies that the amount by which we can be sure the function $f$ is decreased depends on a trade off between the two terms in square brackets. The first term in square brackets measures the angle between the descent direction and the negative gradient. The second term measures how quickly the gradient changes along the descent direction.

In principle inequality (**[1](#math_1)**) could be optimized over $\mathbf {p} _{n}$ and $\eta _{n}$ to choose an optimal step size and direction. The problem is that evaluating the second term in square brackets requires evaluating $\nabla f(\mathbf {a} _{n}-t\eta _{n}\mathbf {p} _{n})$, and extra gradient evaluations are generally expensive and undesirable. Some ways around this problem are:

- Forgo the benefits of a clever descent direction by setting $\mathbf {p} _{n}=\nabla f(\mathbf {a_{n}} )$, and use [[Line Search]] to find a suitable step-size $\gamma _{n}$, such as one that satisfies the [Wolfe conditions](https://en.wikipedia.org/wiki/Wolfe_conditions). A more economic way of choosing learning rates is [backtracking line search](https://en.wikipedia.org/wiki/Backtracking_line_search), a method that has both good theoretical guarantees and experimental results. Note that one does not need to choose $\mathbf {p} _{n}$ to be the gradient; any direction that has positive inner product with the gradient will result in a reduction of the function value (for a sufficiently small value of $\eta _{n}$).
- Assuming that $f$ is twice-differentiable, use its Hessian $\nabla ^{2}f$ to estimate $\|\nabla f(\mathbf {a} _{n}-t\eta _{n}\mathbf {p} _{n})-\nabla f(\mathbf {a} _{n})\|_{2}\approx \|t\eta _{n}\nabla ^{2}f(\mathbf {a} _{n})\mathbf {p} _{n}\|.$Then choose $\mathbf {p} _{n}$ and $\eta _{n}$ by optimising inequality (**[1](#math_1)**).
- Assuming that $\nabla f$ is [Lipschitz](https://en.wikipedia.org/wiki/Lipschitz_continuity), use its Lipschitz constant $L$ to bound $\|\nabla f(\mathbf {a} _{n}-t\eta _{n}\mathbf {p} _{n})-\nabla f(\mathbf {a} _{n})\|_{2}\leq Lt\eta _{n}\|\mathbf {p} _{n}\|.$ Then choose $\mathbf {p} _{n}$ and $\eta _{n}$ by optimising inequality (**[1](#math_1)**).
- Build a custom model of $\max _{t\in [0,1]}{\frac {\|\nabla f(\mathbf {a} _{n}-t\eta _{n}\mathbf {p} _{n})-\nabla f(\mathbf {a} _{n})\|_{2}}{\|\nabla f(\mathbf {a} _{n})\|_{2}}}$ for $f$. Then choose $\mathbf {p} _{n}$ and $\eta _{n}$ by optimising inequality (**[1](#math_1)**).
- Under stronger assumptions on the function $f$ such as [convexity](https://en.wikipedia.org/wiki/Convex_function), more [advanced techniques](#Fast_gradient_methods) may be possible.

Usually by following one of the recipes above, [convergence](https://en.wikipedia.org/wiki/Convergent_series) to a local minimum can be guaranteed. When the function $f$ is [convex](https://en.wikipedia.org/wiki/Convex_function), all local minima are also global minima, so in this case gradient descent can converge to the global solution.

## Solution of a linear system

![[media/b8e561972ae141f1c45731f44c13a96bb4c97084.png]]
The steepest descent algorithm applied to the [Wiener filter](https://en.wikipedia.org/wiki/Wiener_filter)

Gradient descent can be used to solve a [system of linear equations](https://en.wikipedia.org/wiki/System_of_linear_equations)

$\mathbf {A} \mathbf {x} -\mathbf {b} =0$

reformulated as a quadratic minimization problem. If the system matrix $\mathbf {A}$ is real [symmetric](https://en.wikipedia.org/wiki/Symmetric_matrix) and [[Positive-Definite Matrix|positive-definite]], an objective function is defined as the quadratic function, with minimization of

$f(\mathbf {x} )=\mathbf {x} ^{\top }\mathbf {A} \mathbf {x} -2\mathbf {x} ^{\top }\mathbf {b} ,$

so that

$\nabla f(\mathbf {x} )=2(\mathbf {A} \mathbf {x} -\mathbf {b} ).$

For a general real matrix $\mathbf {A}$, [linear least squares](https://en.wikipedia.org/wiki/Linear_least_squares) define

$f(\mathbf {x} )=\left\|\mathbf {A} \mathbf {x} -\mathbf {b} \right\|^{2}.$

In traditional linear least squares for real $\mathbf {A}$ and $\mathbf {b}$ the [Euclidean norm](https://en.wikipedia.org/wiki/Euclidean_norm) is used, in which case

$\nabla f(\mathbf {x} )=2\mathbf {A} ^{\top }(\mathbf {A} \mathbf {x} -\mathbf {b} ).$

The [[Line Search]] minimization, finding the locally optimal step size $\eta$ on every iteration, can be performed analytically for quadratic functions, and explicit formulas for the locally optimal $\eta$ are known.

For example, for real [symmetric](https://en.wikipedia.org/wiki/Symmetric_matrix) and [[Positive-Definite Matrix|positive-definite]] matrix $\mathbf {A}$, a simple algorithm can be as follows,

${\begin{aligned}&{\text{repeat in the loop:}}\\&\qquad \mathbf {r} :=\mathbf {b} -\mathbf {Ax} \\&\qquad \eta :={\mathbf {r} ^{\top }\mathbf {r} }/{\mathbf {r} ^{\top }\mathbf {Ar} }\\&\qquad \mathbf {x} :=\mathbf {x} +\eta \mathbf {r} \\&\qquad {\hbox{if }}\mathbf {r} ^{\top }\mathbf {r} {\text{ is sufficiently small, then exit loop}}\\&{\text{end repeat loop}}\\&{\text{return }}\mathbf {x} {\text{ as the result}}\end{aligned}}$

To avoid multiplying by $\mathbf {A}$ twice per iteration, we note that $\mathbf {x} :=\mathbf {x} +\eta \mathbf {r}$ implies $\mathbf {r} :=\mathbf {r} -\eta \mathbf {Ar}$, which gives the traditional algorithm,

${\begin{aligned}&\mathbf {r} :=\mathbf {b} -\mathbf {Ax} \\&{\text{repeat in the loop:}}\\&\qquad \eta :={\mathbf {r} ^{\top }\mathbf {r} }/{\mathbf {r} ^{\top }\mathbf {Ar} }\\&\qquad \mathbf {x} :=\mathbf {x} +\eta \mathbf {r} \\&\qquad {\hbox{if }}\mathbf {r} ^{\top }\mathbf {r} {\text{ is sufficiently small, then exit loop}}\\&\qquad \mathbf {r} :=\mathbf {r} -\eta \mathbf {Ar} \\&{\text{end repeat loop}}\\&{\text{return }}\mathbf {x} {\text{ as the result}}\end{aligned}}$

![[media/477bb8cd896b64088ac1c5fcfa755c514226adbb.png]]
Convergence path of steepest descent method for A = [[2, 2], [2, 3]]

The method is rarely used for solving linear equations, with the [[Conjugate Gradient Method]] being one of the most popular alternatives. The number of gradient descent iterations is commonly proportional to the spectral [[Condition Number]] $\kappa (\mathbf {A} )$ of the system matrix $\mathbf {A}$ (the ratio of the maximum to minimum [eigenvalues](https://en.wikipedia.org/wiki/Eigenvalues) of $\mathbf {A} ^{\top }\mathbf {A}$), while the convergence of [[Conjugate Gradient Method]] is typically determined by a square root of the condition number, i.e., is much faster. Both methods can benefit from [preconditioning](https://en.wikipedia.org/wiki/Preconditioner), where gradient descent may require less assumptions on the preconditioner.

### Geometric behavior and residual orthogonality

In steepest descent applied to solving $\mathbf {Ax} =\mathbf {b}$, where $\mathbf {A}$ is symmetric positive-definite, the residual vectors $\mathbf {r} _{k}=\mathbf {b} -\mathbf {A} \mathbf {x} _{k}$ are orthogonal across iterations:

$\langle \mathbf {r} _{k+1},\mathbf {r} _{k}\rangle =0.$

Because each step is taken in the steepest direction, steepest-descent steps alternate between directions aligned with the extreme axes of the elongated level sets. When $\kappa (\mathbf {A} )$ is large, this produces a characteristic zig–zag path. The poor conditioning of $\mathbf {A}$ is the primary cause of the slow convergence, and orthogonality of successive residuals reinforces this alternation.

As shown in the image on the right, steepest descent converges slowly due to the high condition number of $\mathbf {A}$, and the orthogonality of residuals forces each new direction to undo the overshoot from the previous step. The result is a path that zigzags toward the solution. This inefficiency is one reason conjugate gradient or preconditioning methods are preferred.

## Solution of a non-linear system

Gradient descent can also be used to solve a system of [nonlinear equations](https://en.wikipedia.org/wiki/Nonlinear_equation). Below is an example that shows how to use the gradient descent to solve for three unknown variables, *x*<sub>1</sub>, *x*<sub>2</sub>, and *x*<sub>3</sub>. This example shows one iteration of the gradient descent.

Consider the nonlinear system of equations

![[media/da319d54386ec7ef18b3700bbdf3148ecbdcf7a8.gif]]
An animation showing the first 83 iterations of gradient descent applied to this example. Surfaces are [isosurfaces](https://en.wikipedia.org/wiki/Isosurface) of $f(\mathbf {x} ^{(n)})$ at current guess $\mathbf {x} ^{(n)}$, and arrows show the direction of descent. Due to a small and constant step size, the convergence is slow.

${\begin{cases}3x_{1}-\cos(x_{2}x_{3})-{\tfrac {3}{2}}=0\\4x_{1}^{2}-625x_{2}^{2}+2x_{2}-1=0\\\exp(-x_{1}x_{2})+20x_{3}+{\tfrac {10\pi -3}{3}}=0\end{cases}}$

Let us introduce the associated function

$G(\mathbf {x} )={\begin{bmatrix}3x_{1}-\cos(x_{2}x_{3})-{\tfrac {3}{2}}\\4x_{1}^{2}-625x_{2}^{2}+2x_{2}-1\\\exp(-x_{1}x_{2})+20x_{3}+{\tfrac {10\pi -3}{3}}\\\end{bmatrix}},$

where

$\mathbf {x} ={\begin{bmatrix}x_{1}\\x_{2}\\x_{3}\\\end{bmatrix}}.$

One might now define the objective function

${\begin{aligned}f(\mathbf {x} )&={\frac {1}{2}}G^{\top }(\mathbf {x} )G(\mathbf {x} )\\&={\frac {1}{2}}\left[\left(3x_{1}-\cos(x_{2}x_{3})-{\frac {3}{2}}\right)^{2}+\left(4x_{1}^{2}-625x_{2}^{2}+2x_{2}-1\right)^{2}+\right.\\&{}\qquad \left.\left(\exp(-x_{1}x_{2})+20x_{3}+{\frac {10\pi -3}{3}}\right)^{2}\right],\end{aligned}}$

which we will attempt to minimize. As an initial guess, let us use

$\mathbf {x} ^{(0)}=\mathbf {0} ={\begin{bmatrix}0\\0\\0\\\end{bmatrix}}.$

We know that

$\mathbf {x} ^{(1)}=\mathbf {0} -\eta _{0}\nabla f(\mathbf {0} )=\mathbf {0} -\eta _{0}J_{G}(\mathbf {0} )^{\top }G(\mathbf {0} ),$

where the [[Jacobian Matrix]] $J_{G}$ is given by

$J_{G}(\mathbf {x} )={\begin{bmatrix}3&\sin(x_{2}x_{3})x_{3}&\sin(x_{2}x_{3})x_{2}\\8x_{1}&-1250x_{2}+2&0\\-x_{2}\exp {(-x_{1}x_{2})}&-x_{1}\exp(-x_{1}x_{2})&20\\\end{bmatrix}}.$

We calculate:

$J_{G}(\mathbf {0} )={\begin{bmatrix}3&0&0\\0&2&0\\0&0&20\end{bmatrix}},\qquad G(\mathbf {0} )={\begin{bmatrix}-2.5\\-1\\10.472\end{bmatrix}}.$

Thus

$\mathbf {x} ^{(1)}=\mathbf {0} -\eta _{0}{\begin{bmatrix}-7.5\\-2\\209.44\end{bmatrix}},$

and

$f(\mathbf {0} )=0.5\left((-2.5)^{2}+(-1)^{2}+(10.472)^{2}\right)=58.456.$

Now, a suitable $\eta _{0}$ must be found such that

$f\left(\mathbf {x} ^{(1)}\right)\leq f\left(\mathbf {x} ^{(0)}\right)=f(\mathbf {0} ).$

This can be done with any of a variety of [[Line Search]] algorithms. One might also simply guess $\eta _{0}=0.001,$ which gives

$\mathbf {x} ^{(1)}={\begin{bmatrix}0.0075\\0.002\\-0.20944\\\end{bmatrix}}.$

Evaluating the objective function at this value, yields

$f\left(\mathbf {x} ^{(1)}\right)=0.5\left((-2.48)^{2}+(-1.00)^{2}+(6.28)^{2}\right)=23.306.$

The decrease from $f(\mathbf {0} )=58.456$ to the next step's value of

$f\left(\mathbf {x} ^{(1)}\right)=23.306$

is a sizable decrease in the objective function. Further steps would reduce its value further until an approximate solution to the system was found.

## Comments

Gradient descent works in spaces of any number of dimensions, even in infinite-dimensional ones. In the latter case, the search space is typically a [function space](https://en.wikipedia.org/wiki/Function_space), and one calculates the [Fréchet derivative](https://en.wikipedia.org/wiki/Fr%C3%A9chet_derivative) of the functional to be minimized to determine the descent direction.

That gradient descent works in any number of dimensions (finite number at least) can be seen as a consequence of the [Cauchy–Schwarz inequality](https://en.wikipedia.org/wiki/Cauchy%E2%80%93Schwarz_inequality), i.e. the magnitude of the inner (dot) product of two vectors of any dimension is maximized when they are [colinear](https://en.wikipedia.org/wiki/Colinear). In the case of gradient descent, that would be when the vector of independent variable adjustments is proportional to the gradient vector of partial derivatives.

The gradient descent can take many iterations to compute a local minimum with a required [accuracy](https://en.wikipedia.org/wiki/Accuracy), if the [curvature](https://en.wikipedia.org/wiki/Curvature) in different directions is very different for the given function. For such functions, [preconditioning](https://en.wikipedia.org/wiki/Preconditioning), which changes the geometry of the space to shape the function level sets like [concentric circles](https://en.wikipedia.org/wiki/Concentric_circles), cures the slow convergence. Constructing and applying preconditioning can be computationally expensive, however.

The gradient descent can be modified via momentums ([Nesterov](https://en.wikipedia.org/wiki/Nesterov), Polyak, and Frank–Wolfe) and heavy-ball parameters (exponential moving averages and positive-negative momentum). The main examples of such optimizers are Adam, DiffGrad, Yogi, AdaBelief, etc.

Methods based on [Newton's method](https://en.wikipedia.org/wiki/Newton%27s_method_in_optimization) and inversion of the [[Hessian Matrix|Hessian]] using [conjugate gradient](https://en.wikipedia.org/wiki/Conjugate_gradient) techniques can be better alternatives. Generally, such methods converge in fewer iterations, but the cost of each iteration is higher. An example is the [BFGS method](https://en.wikipedia.org/wiki/Broyden%E2%80%93Fletcher%E2%80%93Goldfarb%E2%80%93Shanno_algorithm) which consists in calculating on every step a matrix by which the gradient vector is multiplied to go into a "better" direction, combined with a more sophisticated [[Line Search]] algorithm, to find the "best" value of $\eta .$ For extremely large problems, where the computer-memory issues dominate, a limited-memory method such as [L-BFGS](https://en.wikipedia.org/wiki/Limited-memory_BFGS) should be used instead of BFGS or the steepest descent.

While it is sometimes possible to substitute gradient descent for a [local search](https://en.wikipedia.org/wiki/Local_search_(optimization) "Local search (optimization)") algorithm, gradient descent is not in the same family: although it is an [iterative method](https://en.wikipedia.org/wiki/Iterative_method) for [local optimization](https://en.wikipedia.org/wiki/Global_optimization), it relies on an [objective function's gradient](https://en.wikipedia.org/wiki/Loss_function) rather than an explicit exploration of a [solution space](https://en.wikipedia.org/wiki/Feasible_region).

Gradient descent can be viewed as applying [Euler's method](https://en.wikipedia.org/wiki/Euler%27s_method) for solving [ordinary differential equations](https://en.wikipedia.org/wiki/Ordinary_differential_equations) $x'(t)=-\nabla f(x(t))$ to a [gradient flow](https://en.wikipedia.org/wiki/Gradient_flow). In turn, this equation may be derived as an optimal controller for the control system $x'(t)=u(t)$ with $u(t)$ given in feedback form $u(t)=-\nabla f(x(t))$.

## Modifications

Gradient descent can converge to a local minimum and slow down in a neighborhood of a [saddle point](https://en.wikipedia.org/wiki/Saddle_point). Even for unconstrained quadratic minimization, gradient descent develops a zig–zag pattern of subsequent iterates as iterations progress, resulting in slow convergence. Multiple modifications of gradient descent have been proposed to address these deficiencies.

### Fast gradient methods

### Momentum or *heavy ball* method

Trying to break the zig-zag pattern of gradient descent, the *momentum or heavy ball method* uses a momentum term in analogy to a heavy ball sliding on the surface of values of the function being minimized, or to mass movement in [Newtonian dynamics](https://en.wikipedia.org/wiki/Newtonian_dynamics) through a [viscous](https://en.wikipedia.org/wiki/Viscous) medium in a [conservative force](https://en.wikipedia.org/wiki/Conservative_force) field. Gradient descent with momentum remembers the solution update at each iteration, and determines the next update as a [linear combination](https://en.wikipedia.org/wiki/Linear_combination) of the gradient and the previous update. For unconstrained quadratic minimization, a theoretical convergence rate bound of the heavy ball method is asymptotically the same as that for the optimal [[Conjugate Gradient Method]].

This technique is used in [[Stochastic Gradient Descent]] and as an extension to the [backpropagation](https://en.wikipedia.org/wiki/Backpropagation) algorithms used to train [artificial neural networks](https://en.wikipedia.org/wiki/Artificial_neural_network). In the direction of updating, stochastic gradient descent adds a stochastic property. The weights can be used to calculate the derivatives.

## Extensions

Gradient descent can be extended to handle [constraints](https://en.wikipedia.org/wiki/Constraint_(mathematics) "Constraint (mathematics)") by including a [projection](https://en.wikipedia.org/wiki/Projection_(linear_algebra) "Projection (linear algebra)") onto the set of constraints. This method is only feasible when the projection is efficiently computable on a computer. Under suitable assumptions, this method converges. This method is a specific case of the [forward–backward algorithm](https://en.wikipedia.org/wiki/Forward%E2%80%93backward_algorithm) for monotone inclusions (which includes [convex programming](https://en.wikipedia.org/wiki/Convex_programming) and [variational inequalities](https://en.wikipedia.org/wiki/Variational_inequality)).

Gradient descent is a special case of [mirror descent](https://en.wikipedia.org/wiki/Mirror_descent) using the squared Euclidean distance as the given [Bregman divergence](https://en.wikipedia.org/wiki/Bregman_divergence).

## Theoretical properties

The properties of gradient descent depend on the properties of the objective function and the variant of gradient descent used (for example, if a [[Line Search]] step is used). The assumptions made affect the convergence rate, and other properties, that can be proven for gradient descent. For example, if the objective is assumed to be [strongly convex](https://en.wikipedia.org/wiki/Strongly_convex_function) and [lipschitz smooth](https://en.wikipedia.org/wiki/Lipschitz_continuity), then gradient descent converges linearly with a fixed step size. Looser assumptions lead to either weaker convergence guarantees or require a more sophisticated step size selection.

## Examples

- [Yang–Mills flow](https://en.wikipedia.org/wiki/Yang%E2%80%93Mills_flow)
- [Yang–Mills–Higgs flow](https://en.wikipedia.org/wiki/Yang%E2%80%93Mills%E2%80%93Higgs_flow)
- [Seiberg–Witten flow](https://en.wikipedia.org/wiki/Seiberg%E2%80%93Witten_flow)

## See also

- [Backtracking line search](https://en.wikipedia.org/wiki/Backtracking_line_search)
- [[Conjugate Gradient Method]]
- [[Stochastic Gradient Descent]]
- [Rprop](https://en.wikipedia.org/wiki/Rprop)
- [Delta rule](https://en.wikipedia.org/wiki/Delta_rule)
- [Wolfe conditions](https://en.wikipedia.org/wiki/Wolfe_conditions)
- [Preconditioning](https://en.wikipedia.org/wiki/Preconditioning)
- [Broyden–Fletcher–Goldfarb–Shanno algorithm](https://en.wikipedia.org/wiki/Broyden%E2%80%93Fletcher%E2%80%93Goldfarb%E2%80%93Shanno_algorithm)
- [Davidon–Fletcher–Powell formula](https://en.wikipedia.org/wiki/Davidon%E2%80%93Fletcher%E2%80%93Powell_formula)
- [Nelder–Mead method](https://en.wikipedia.org/wiki/Nelder%E2%80%93Mead_method)
- [Gauss–Newton algorithm](https://en.wikipedia.org/wiki/Gauss%E2%80%93Newton_algorithm)
- [Hill climbing](https://en.wikipedia.org/wiki/Hill_climbing)
- [Quantum annealing](https://en.wikipedia.org/wiki/Quantum_annealing)
- [CLS](https://en.wikipedia.org/wiki/TFNP#CLS) (continuous local search)
- [Neuroevolution](https://en.wikipedia.org/wiki/Neuroevolution)

## References

1.  ^   Boyd, Stephen; Vandenberghe, Lieven (2004-03-08). *Convex Optimization*. Cambridge University Press. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1017/cbo9780511804441](https://doi.org/10.1017%2Fcbo9780511804441). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-83378-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-83378-3).
2.  Lemaréchal, C. (1 January 2012). ["Cauchy and the gradient method"](https://web.archive.org/web/20181229073335/https://www.math.uni-bielefeld.de/documenta/vol-ismp/40_lemarechal-claude.pdf) (PDF). In Grötschel, M. (ed.). *Optimization Stories*. Documenta Mathematica Series. Vol. 6 (1st ed.). EMS Press. pp. 251–254. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.4171/dms/6/27](https://doi.org/10.4171%2Fdms%2F6%2F27). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-936609-58-5](https://en.wikipedia.org/wiki/Special:BookSources/978-3-936609-58-5). Archived from [the original](https://www.math.uni-bielefeld.de/documenta/vol-ismp/40_lemarechal-claude.pdf) (PDF) on 2018-12-29. Retrieved 2020-01-26.
3.  Hadamard, Jacques (1908). "Mémoire sur le problème d'analyse relatif à l'équilibre des plaques élastiques encastrées". *Mémoires présentés par divers savants éstrangers à l'Académie des Sciences de l'Institut de France*. **33**.
4.  Courant, R. (1943). ["Variational methods for the solution of problems of equilibrium and vibrations"](https://doi.org/10.1090%2FS0002-9904-1943-07818-4). *Bulletin of the American Mathematical Society*. **49** (1): 1–23. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1090/S0002-9904-1943-07818-4](https://doi.org/10.1090%2FS0002-9904-1943-07818-4).
5.  Curry, Haskell B. (1944). ["The Method of Steepest Descent for Non-linear Minimization Problems"](https://doi.org/10.1090%2Fqam%2F10667). *Quart. Appl. Math*. **2** (3): 258–261. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1090/qam/10667](https://doi.org/10.1090%2Fqam%2F10667).
7.  ^   Akilov, G. P.; [Kantorovich, L. V.](https://en.wikipedia.org/wiki/Leonid_Kantorovich) (1982). *Functional Analysis* (2nd ed.). Pergamon Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-08-023036-9](https://en.wikipedia.org/wiki/Special:BookSources/0-08-023036-9).
8.  Barzilai, Jonathan; Borwein, Jonathan M. (1988). "Two-Point Step Size Gradient Methods". *IMA Journal of Numerical Analysis*. **8** (1): 141–148. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1093/imanum/8.1.141](https://doi.org/10.1093%2Fimanum%2F8.1.141).
9.  Fletcher, R. (2005). "On the Barzilai–Borwein Method". In Qi, L.; Teo, K.; Yang, X. (eds.). *Optimization and Control with Applications*. Applied Optimization. Vol. 96. Boston: Springer. pp. 235–256. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-387-24254-6](https://en.wikipedia.org/wiki/Special:BookSources/0-387-24254-6).
10. Wolfe, Philip (April 1969). "Convergence Conditions for Ascent Methods". *SIAM Review*. **11** (2): 226–235. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/1011036](https://doi.org/10.1137%2F1011036).
11. Bernstein, Jeremy; Vahdat, Arash; Yue, Yisong; Liu, Ming-Yu (2020-06-12). "On the distance between two neural networks and the stability of learning". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2002.03432](https://arxiv.org/abs/2002.03432) \[[cs.LG](https://arxiv.org/archive/cs.LG)\].
12. Haykin, Simon S. Adaptive filter theory. Pearson Education India, 2008. - p. 108-142, 217-242
13. Saad, Yousef (2003). [Iterative methods for sparse linear systems](https://archive.org/details/iterativemethods0000saad/page/195) (2nd ed.). Philadelphia, Pa.: Society for Industrial and Applied Mathematics. pp. [195](https://archive.org/details/iterativemethods0000saad/page/195). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-89871-534-7](https://en.wikipedia.org/wiki/Special:BookSources/978-0-89871-534-7).
14. ^   Bouwmeester, Henricus; Dougherty, Andrew; Knyazev, Andrew V. (2015). ["Nonsymmetric Preconditioning for Conjugate Gradient and Steepest Descent Methods"](https://doi.org/10.1016%2Fj.procs.2015.05.241). *Procedia Computer Science*. **51**: 276–285. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1212.6680](https://arxiv.org/abs/1212.6680). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.procs.2015.05.241](https://doi.org/10.1016%2Fj.procs.2015.05.241).
15. Holmes, M. (2023). *Introduction to Scientific Computing and Data Analysis, 2nd Ed*. Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-031-22429-4](https://en.wikipedia.org/wiki/Special:BookSources/978-3-031-22429-4).
16. Abdulkadirov, Ruslan; Lyakhov, Pavel; Nagornov, Nikolay (January 2023). ["Survey of Optimization Algorithms in Modern Neural Networks"](https://doi.org/10.3390%2Fmath11112466). *Mathematics*. **11** (11): 2466. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3390/math11112466](https://doi.org/10.3390%2Fmath11112466). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [2227-7390](https://search.worldcat.org/issn/2227-7390).
17. Diakonikolas, Jelena; Jordan, Michael I. (January 2021). ["Generalized Momentum-Based Methods: A Hamiltonian Perspective"](https://epubs.siam.org/doi/10.1137/20M1322716). *SIAM Journal on Optimization*. **31** (1): 915–944. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1906.00436](https://arxiv.org/abs/1906.00436). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/20M1322716](https://doi.org/10.1137%2F20M1322716). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1052-6234](https://search.worldcat.org/issn/1052-6234).
18. Meyer, Gerard G. L. (November 1974). ["Accelerated Frank–Wolfe Algorithms"](http://epubs.siam.org/doi/10.1137/0312050). *SIAM Journal on Control*. **12** (4): 655–663. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/0312050](https://doi.org/10.1137%2F0312050). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0036-1402](https://search.worldcat.org/issn/0036-1402).
19. Kingma, Diederik P.; Ba, Jimmy (2017-01-29), *Adam: A Method for Stochastic Optimization*, [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1412.6980](https://arxiv.org/abs/1412.6980)
20. Xie, Zeke; Yuan, Li; Zhu, Zhanxing; Sugiyama, Masashi (2021-07-01). ["Positive-Negative Momentum: Manipulating Stochastic Gradient Noise to Improve Generalization"](https://proceedings.mlr.press/v139/xie21h.html). *Proceedings of the 38th International Conference on Machine Learning*. PMLR: 11448–11458. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2103.17182](https://arxiv.org/abs/2103.17182).
21. [Press, W. H.](https://en.wikipedia.org/wiki/William_H._Press); [Teukolsky, S. A.](https://en.wikipedia.org/wiki/Saul_Teukolsky); Vetterling, W. T.; [Flannery, B. P.](https://en.wikipedia.org/wiki/Brian_P._Flannery) (1992). [Numerical Recipes in C: The Art of Scientific Computing](https://archive.org/details/numericalrecipes00pres_0) (2nd ed.). New York: [Cambridge University Press](https://en.wikipedia.org/wiki/Cambridge_University_Press). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-43108-5](https://en.wikipedia.org/wiki/Special:BookSources/0-521-43108-5).
22. Strutz, T. (2016). *Data Fitting and Uncertainty: A Practical Introduction to Weighted Least Squares and Beyond* (2nd ed.). Springer Vieweg. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-658-11455-8](https://en.wikipedia.org/wiki/Special:BookSources/978-3-658-11455-8).
23. Ross, I.M. (July 2019). ["An optimal control theory for nonlinear optimization"](https://doi.org/10.1016%2Fj.cam.2018.12.044). *Journal of Computational and Applied Mathematics*. **354**: 39–51. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.cam.2018.12.044](https://doi.org/10.1016%2Fj.cam.2018.12.044). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [127649426](https://api.semanticscholar.org/CorpusID:127649426).
24. [Nesterov, Yurii](https://en.wikipedia.org/wiki/Yurii_Nesterov) (2004). *Introductory Lectures on Convex Optimization: A Basic Course*. Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [1-4020-7553-7](https://en.wikipedia.org/wiki/Special:BookSources/1-4020-7553-7).
25. Vandenberghe, Lieven (2019). ["Fast Gradient Methods"](https://www.seas.ucla.edu/~vandenbe/236C/lectures/fgrad.pdf) (PDF). *Lecture notes for EE236C at UCLA*.
26. Walkington, Noel J. (2023). ["Nesterov's Method for Convex Optimization"](https://epubs.siam.org/doi/10.1137/21M1390037). *SIAM Review*. **65** (2): 539–562. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/21M1390037](https://doi.org/10.1137%2F21M1390037). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0036-1445](https://search.worldcat.org/issn/0036-1445).
27. Kim, D.; Fessler, J. A. (2016). ["Optimized First-order Methods for Smooth Convex Minimization"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5067109). *[Mathematical Programming](https://en.wikipedia.org/wiki/Mathematical_Programming)*. **151** (1–2): 81–107. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1406.5468](https://arxiv.org/abs/1406.5468). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s10107-015-0949-3](https://doi.org/10.1007%2Fs10107-015-0949-3). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [5067109](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5067109). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [27765996](https://pubmed.ncbi.nlm.nih.gov/27765996). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [207055414](https://api.semanticscholar.org/CorpusID:207055414).
28. Drori, Yoel (2017). "The Exact Information-based Complexity of Smooth Convex Minimization". *Journal of Complexity*. **39**: 1–16. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1606.01424](https://arxiv.org/abs/1606.01424). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.jco.2016.11.001](https://doi.org/10.1016%2Fj.jco.2016.11.001). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [205861966](https://api.semanticscholar.org/CorpusID:205861966).
29. Qian, Ning (January 1999). "On the momentum term in gradient descent learning algorithms". *[Neural Networks](https://en.wikipedia.org/wiki/Neural_Networks_(journal) "Neural Networks (journal)")*. **12** (1): 145–151. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.57.5612](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.57.5612). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/S0893-6080(98)00116-6](https://doi.org/10.1016%2FS0893-6080%2898%2900116-6). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [12662723](https://pubmed.ncbi.nlm.nih.gov/12662723). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [2783597](https://api.semanticscholar.org/CorpusID:2783597).
30. ["Momentum and Learning Rate Adaptation"](http://www.willamette.edu/~gorr/classes/cs449/momrate.html). [Willamette University](https://en.wikipedia.org/wiki/Willamette_University). Retrieved 17 October 2014.
31. [Geoffrey Hinton](https://en.wikipedia.org/wiki/Geoffrey_Hinton); Nitish Srivastava; Kevin Swersky. ["The momentum method"](https://www.coursera.org/lecture/neural-networks/the-momentum-method-Oya9a). *[Coursera](https://en.wikipedia.org/wiki/Coursera)*. Retrieved 2 October 2018. Part of a lecture series for the [Coursera](https://en.wikipedia.org/wiki/Coursera) online course [Neural Networks for Machine Learning](https://www.coursera.org/learn/neural-networks) [Archived](https://web.archive.org/web/20161231174321/https://www.coursera.org/learn/neural-networks) 2016-12-31 at the [Wayback Machine](https://en.wikipedia.org/wiki/Wayback_Machine).
32. Combettes, P. L.; Pesquet, J.-C. (2011). "Proximal splitting methods in signal processing". In Bauschke, H. H.; [Burachik, R. S.](https://en.wikipedia.org/wiki/Regina_S._Burachik); Combettes, P. L.; Elser, V.; Luke, D. R.; Wolkowicz, H. (eds.). *Fixed-Point Algorithms for Inverse Problems in Science and Engineering*. New York: Springer. pp. 185–212. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[0912.3522](https://arxiv.org/abs/0912.3522). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4419-9568-1](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4419-9568-1).
33. ["Mirror descent algorithm"](https://tlienart.github.io/posts/2018/10/27-mirror-descent-algorithm/).
34. ^   Bubeck, Sébastien (2015). "Convex Optimization: Algorithms and Complexity". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1405.4980](https://arxiv.org/abs/1405.4980) \[[math.OC](https://arxiv.org/archive/math.OC)\].

## Further reading

- [Boyd, Stephen](https://en.wikipedia.org/wiki/Stephen_P._Boyd); Vandenberghe, Lieven (2004). ["Unconstrained Minimization"](https://web.stanford.edu/~boyd/cvxbook/bv_cvxbook.pdf#page=471) (PDF). *Convex Optimization*. New York: Cambridge University Press. pp. 457–520. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-83378-7](https://en.wikipedia.org/wiki/Special:BookSources/0-521-83378-7).
- Chong, Edwin K. P.; Żak, Stanislaw H. (2013). ["Gradient Methods"](https://books.google.com/books?id=iD5s0iKXHP8C&pg=PA131). *An Introduction to Optimization* (Fourth ed.). Hoboken: Wiley. pp. 131–160. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-118-27901-4](https://en.wikipedia.org/wiki/Special:BookSources/978-1-118-27901-4).
- Himmelblau, David M. (1972). "Unconstrained Minimization Procedures Using Derivatives". *Applied Nonlinear Programming*. New York: McGraw-Hill. pp. 63–132. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-07-028921-2](https://en.wikipedia.org/wiki/Special:BookSources/0-07-028921-2).

## External links

- [Using gradient descent in C++, Boost, Ublas for linear regression](https://codingplayground.blogspot.it/2013/05/learning-linear-regression-with.html)
- [Series of Khan Academy videos discusses gradient ascent](https://www.khanacademy.org/math/multivariable-calculus/multivariable-derivatives/gradient-and-directional-derivatives/v/gradient)
- [Online book teaching gradient descent in deep neural network context](http://neuralnetworksanddeeplearning.com/chap1.html#learning_with_gradient_descent)
- Archived at [Ghostarchive](https://ghostarchive.org/varchive/youtube/20211211/IHZwWFHWa-w) and the [Wayback Machine](https://web.archive.org/web/20171016173155/https://www.youtube.com/watch?v=IHZwWFHWa-w): ["Gradient Descent, How Neural Networks Learn"](https://www.youtube.com/watch?v=IHZwWFHWa-w&list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi&index=2). *3Blue1Brown*. October 16, 2017 – via [YouTube](https://en.wikipedia.org/wiki/YouTube).
- Garrigos, Guillaume; Gower, Robert M. (2023). "Handbook of Convergence Theorems for (Stochastic) Gradient Methods". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2301.11235](https://arxiv.org/abs/2301.11235) \[[math.OC](https://arxiv.org/archive/math.OC)\].
