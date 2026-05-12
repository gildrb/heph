[[numerical-methods.base]]

> Source: [Iterative method](https://en.wikipedia.org/wiki/Iterative_method)
> License: Wikipedia content is available under CC BY-SA 4.0.

In [computational mathematics](https://en.wikipedia.org/wiki/Computational_mathematics), an **iterative method** is a [mathematical procedure](https://en.wikipedia.org/wiki/Algorithm) that uses an initial value to generate a sequence of improving approximate solutions for a class of problems, in which the *i*-th approximation (called an "iterate") is derived from the previous ones.

A specific implementation with [termination](https://en.wikipedia.org/wiki/Algorithm#Termination) criteria for a given iterative method like [[Gradient Descent]], [hill climbing](https://en.wikipedia.org/wiki/Hill_climbing), [Newton's method](https://en.wikipedia.org/wiki/Newton%27s_method), or [quasi-Newton methods](https://en.wikipedia.org/wiki/Quasi-Newton_method) like [BFGS](https://en.wikipedia.org/wiki/Broyden%E2%80%93Fletcher%E2%80%93Goldfarb%E2%80%93Shanno_algorithm), is an [algorithm](https://en.wikipedia.org/wiki/Algorithm) of an iterative method or a **method of successive approximation**. An iterative method is called *[convergent](https://en.wikipedia.org/wiki/Convergent_series)* if the corresponding sequence converges for given initial approximations. A mathematically rigorous convergence analysis of an iterative method is usually performed; however, [heuristic](https://en.wikipedia.org/wiki/Heuristic)-based iterative methods are also common.

In contrast, **direct methods** attempt to solve the problem by a finite sequence of operations. In the absence of [rounding errors](https://en.wikipedia.org/wiki/Rounding_error), direct methods would deliver an exact solution (for example, solving a linear system of equations $A\mathbf {x} =\mathbf {b}$ by [Gaussian elimination](https://en.wikipedia.org/wiki/Gaussian_elimination)). Iterative methods are often the only choice for [nonlinear equations](https://en.wikipedia.org/wiki/Nonlinear_equation). However, iterative methods are often useful even for linear problems involving many variables (sometimes on the order of millions), where direct methods would be prohibitively expensive (and in some cases impossible) even with the best available computing power.

## Attractive fixed points

If an equation can be put into the form *f*(*x*) = *x*, and a solution **x** is an attractive [fixed point](https://en.wikipedia.org/wiki/Fixed_point_(mathematics) "Fixed point (mathematics)") of the function *f*, then one may begin with a point *x*<sub>1</sub> in the [basin of attraction](https://en.wikipedia.org/wiki/Basin_of_attraction) of **x**, and let *x*<sub>*n*+1</sub> = *f*(*x*<sub>*n*</sub>) for *n* ≥ 1, and the sequence {*x*<sub>*n*</sub>}<sub>*n* ≥ 1</sub> will converge to the solution **x**. Here *x*<sub>*n*</sub> is the *n*th approximation or iteration of *x* and *x*<sub>*n*+1</sub> is the next or *n* + 1 iteration of *x*. Alternately, superscripts in parentheses are often used in numerical methods, so as not to interfere with subscripts with other meanings. (For example, *x*<sup>(*n*+1)</sup> = *f*(*x*<sup>(*n*)</sup>).) If the function *f* is [continuously differentiable](https://en.wikipedia.org/wiki/Continuously_differentiable), a sufficient condition for convergence is that the [spectral radius](https://en.wikipedia.org/wiki/Spectral_radius) of the derivative is strictly bounded by one in a neighborhood of the fixed point. If this condition holds at the fixed point, then a sufficiently small neighborhood (basin of attraction) must exist.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

## Linear systems

In the case of a [system of linear equations](https://en.wikipedia.org/wiki/System_of_linear_equations), the two main classes of iterative methods are the **stationary iterative methods**, and the more general [Krylov subspace](https://en.wikipedia.org/wiki/Krylov_subspace) methods.

### Stationary iterative methods

#### Introduction

Stationary iterative methods solve a linear system with an [operator](https://en.wikipedia.org/wiki/Operator_(mathematics) "Operator (mathematics)") approximating the original one; and based on a measurement of the error in the result ([the residual](https://en.wikipedia.org/wiki/Residual_(numerical_analysis) "Residual (numerical analysis)")), form a "correction equation" for which this process is repeated. While these methods are simple to derive, implement, and analyze, convergence is only guaranteed for a limited class of matrices.

#### Definition

An *iterative method* is defined by 

$$
\mathbf {x} ^{k+1}:=\Psi (\mathbf {x} ^{k}),\quad k\geq 0
$$

 and for a given linear system $A\mathbf {x} =\mathbf {b}$ with exact solution $\mathbf {x} ^{*}$ the *error* by 

$$
\mathbf {e} ^{k}:=\mathbf {x} ^{k}-\mathbf {x} ^{*},\quad k\geq 0.
$$

 An iterative method is called *linear* if there exists a matrix $C\in \mathbb {R} ^{n\times n}$ such that 

$$
\mathbf {e} ^{k+1}=C\mathbf {e} ^{k}\quad \forall k\geq 0
$$

 and this matrix is called the *iteration matrix*. An iterative method with a given iteration matrix $C$ is called *convergent* if the following holds 

$$
\lim _{k\to \infty }C^{k}=0.
$$

An important theorem states that for a given iterative method and its iteration matrix $C$ it is convergent if and only if its [spectral radius](https://en.wikipedia.org/wiki/Spectral_radius) $\rho (C)$ is smaller than unity, that is, 

$$
\rho (C)<1.
$$

The basic iterative methods work by [splitting](https://en.wikipedia.org/wiki/Matrix_splitting) the matrix $A$ into 

$$
A=M-N
$$

 and here the matrix $M$ should be easily [invertible](https://en.wikipedia.org/wiki/Invertible_matrix). The iterative methods are now defined as 

$$
M\mathbf {x} ^{k+1}=N\mathbf {x} ^{k}+\mathbf {b} ,\quad k\geq 0,
$$

 or, equivalently, 

$$
\mathbf {x} ^{k+1}=\mathbf {x} ^{k}+M^{-1}\left(\mathbf {b} -A\mathbf {x} ^{k}\right),\quad k\geq 0.
$$

 From this follows that the iteration matrix is given by 

$$
C=I-M^{-1}A=M^{-1}N.
$$

#### Examples

Basic examples of stationary iterative methods use a splitting of the matrix $A$ such as 

$$
A=D+L+U\,,\quad D:=\operatorname {diag} ((a_{ii})_{i})
$$

 where $D$ is only the diagonal part of $A$, and $L$ is the strict lower [triangular part](https://en.wikipedia.org/wiki/Triangular_matrix) of $A$. Respectively, $U$ is the strict upper triangular part of $A$.

- [Richardson method](https://en.wikipedia.org/wiki/Modified_Richardson_iteration): 

$$
M:={\frac {1}{\omega }}I\quad (\omega \neq 0)
$$

- [Jacobi method](https://en.wikipedia.org/wiki/Jacobi_method): 

$$
M:=D
$$

- [Damped Jacobi method](https://en.wikipedia.org/wiki/Jacobi_method#Weighted_Jacobi_method): 

$$
M:={\frac {1}{\omega }}D\quad (\omega \neq 0)
$$

- [Gauss–Seidel method](https://en.wikipedia.org/wiki/Gauss%E2%80%93Seidel_method): 

$$
M:=D+L
$$

- [Successive over-relaxation method](https://en.wikipedia.org/wiki/Successive_over-relaxation) (SOR): 

$$
M:={\frac {1}{\omega }}D+L\quad (\omega \neq 0)
$$

- [Symmetric successive over-relaxation](https://en.wikipedia.org/wiki/Symmetric_successive_over-relaxation) (SSOR): 

$$
M:={\frac {1}{\omega \left(2-\omega \right)}}\left(D+\omega L\right)D^{-1}\left(D+\omega U\right)\quad (\omega \not \in \{0,2\})
$$

Linear stationary iterative methods are also called [relaxation methods](https://en.wikipedia.org/wiki/Relaxation_(iterative_method) "Relaxation (iterative method)").

### Krylov subspace methods

Krylov subspace methods work by forming a [basis](https://en.wikipedia.org/wiki/Basis_(linear_algebra) "Basis (linear algebra)") of the sequence of successive matrix powers times the initial residual (the **Krylov sequence**). The approximations to the solution are then formed by minimizing the residual over the subspace formed. The prototypical method in this class is the [[Conjugate Gradient Method]] (CG) which assumes that the system matrix $A$ is [symmetric](https://en.wikipedia.org/wiki/Symmetric_matrix) [[Positive-Definite Matrix|positive-definite]]. For symmetric (and possibly indefinite) $A$ one works with the [minimal residual method](https://en.wikipedia.org/wiki/Minimal_residual_method) (MINRES). In the case of non-symmetric matrices, methods such as the [generalized minimal residual method](https://en.wikipedia.org/wiki/Generalized_minimal_residual_method) (GMRES) and the [biconjugate gradient method](https://en.wikipedia.org/wiki/Biconjugate_gradient_method) (BiCG) have been derived.

#### Convergence of Krylov subspace methods

Since these methods form a basis, it is evident that the method converges in *N* iterations, where *N* is the system size. However, in the presence of rounding errors this statement does not hold; moreover, in practice *N* can be very large, and the iterative process reaches sufficient accuracy already far earlier. The analysis of these methods is hard, depending on a complicated function of the [spectrum](https://en.wikipedia.org/wiki/Spectrum_of_an_operator) of the operator.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

### Preconditioners

The approximating operator that appears in stationary iterative methods can also be incorporated in Krylov subspace methods such as [GMRES](https://en.wikipedia.org/wiki/GMRES) (alternatively, [preconditioned](https://en.wikipedia.org/wiki/Preconditioning) Krylov methods can be considered as accelerations of stationary iterative methods), where they become transformations of the original operator to a presumably better conditioned one. The construction of preconditioners is a large research area.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

## Methods of successive approximation

Mathematical methods relating to successive approximation include:

- [Babylonian method](https://en.wikipedia.org/wiki/Babylonian_method), for finding square roots of numbers
- [Fixed-point iteration](https://en.wikipedia.org/wiki/Fixed-point_iteration)
- Means of finding zeros of functions:
  - [Halley's method](https://en.wikipedia.org/wiki/Halley%27s_method)
  - [Newton's method](https://en.wikipedia.org/wiki/Newton%27s_method)
- Differential-equation matters:
  - [Picard–Lindelöf theorem](https://en.wikipedia.org/wiki/Picard%E2%80%93Lindel%C3%B6f_theorem), on existence of solutions of differential equations
  - [Runge–Kutta methods](https://en.wikipedia.org/wiki/Runge%E2%80%93Kutta_methods), for numerical solution of differential equations

### History

[Jamshīd al-Kāshī](https://en.wikipedia.org/wiki/Jamsh%C4%ABd_al-K%C4%81sh%C4%AB) used iterative methods to calculate the sine of 1° and π in *The Treatise of Chord and Sine* to high precision. An early iterative method for [solving a linear system](https://en.wikipedia.org/wiki/Gauss%E2%80%93Seidel_method) appeared in a letter of [Gauss](https://en.wikipedia.org/wiki/Carl_Friedrich_Gauss) to a student of his. He proposed solving a 4-by-4 system of equations by repeatedly solving the component in which the residual was the largest <sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>.

The theory of stationary iterative methods was solidly established with the work of [D.M. Young](https://en.wikipedia.org/wiki/D.M._Young) starting in the 1950s. The conjugate gradient method was also invented in the 1950s, with independent developments by [Cornelius Lanczos](https://en.wikipedia.org/wiki/Cornelius_Lanczos), [Magnus Hestenes](https://en.wikipedia.org/wiki/Magnus_Hestenes) and [Eduard Stiefel](https://en.wikipedia.org/wiki/Eduard_Stiefel), but its nature and applicability were misunderstood at the time. Only in the 1970s was it realized that conjugacy based methods work very well for [partial differential equations](https://en.wikipedia.org/wiki/Partial_differential_equation), especially the elliptic type.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

## See also

- ![[media/1a9c6ad1ccebbc090fc7cd1c94d2142489246997.png]][Mathematics portal](https://en.wikipedia.org/wiki/Portal:Mathematics)

- [Closed-form expression](https://en.wikipedia.org/wiki/Closed-form_expression)
- [Iterative refinement](https://en.wikipedia.org/wiki/Iterative_refinement)
- [Kaczmarz method](https://en.wikipedia.org/wiki/Kaczmarz_method)
- [Non-linear least squares](https://en.wikipedia.org/wiki/Non-linear_least_squares)
- [Numerical analysis](https://en.wikipedia.org/wiki/Numerical_analysis)
- [Root-finding algorithm](https://en.wikipedia.org/wiki/Root-finding_algorithm)

## References

1.  Amritkar, Amit; de Sturler, Eric; Świrydowicz, Katarzyna; Tafti, Danesh; Ahuja, Kapil (2015). "Recycling Krylov subspaces for CFD applications and a new hybrid recycling solver". *Journal of Computational Physics*. **303**: 222. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1501.03358](https://arxiv.org/abs/1501.03358). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2015JCoPh.303..222A](https://ui.adsabs.harvard.edu/abs/2015JCoPh.303..222A). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.jcp.2015.09.040](https://doi.org/10.1016%2Fj.jcp.2015.09.040).
2.  Charles George Broyden and Maria Terasa Vespucci: *Krylov Solvers for Linear Algebraic Systems: Krylov Solvers*, Elsevier, ISBN 0-444-51474-0, (2004).
3.  ["Babylonian mathematics"](https://mathshistory.st-andrews.ac.uk/HistTopics/Babylonian_mathematics/). *Babylonian mathematics*. December 1, 2000.
4.  day, Mahlon (November 2, 1960). *Fixed-point theorems for compact convex sets*. Mahlon M day.

## External links

- [Templates for the Solution of Linear Systems](http://www.netlib.org/linalg/html_templates/Templates.html)
- [Y. Saad: Iterative Methods for Sparse Linear Systems, 1st edition, PWS 1996](http://www-users.cs.umn.edu/~saad/books.html)
