[[numerical-methods.base]]

> Source: [[Condition Number]]
> License: Wikipedia content is available under CC BY-SA 4.0.

In [numerical analysis](https://en.wikipedia.org/wiki/Numerical_analysis), the **condition number** of a [function](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)") measures how much the output value of the function can change for a small change in the input argument. This is used to measure how [sensitive](https://en.wikipedia.org/wiki/Sensitivity_analysis) a function is to changes or errors in the input, and how much error in the output results from an error in the input. Very frequently, one is solving the inverse problem: given $f(x)=y,$ one is solving for *x,* and thus the condition number of the (local) inverse must be used.

The condition number is derived from the theory of [propagation of uncertainty](https://en.wikipedia.org/wiki/Propagation_of_uncertainty), and is formally defined as the value of the [asymptotic](https://en.wikipedia.org/wiki/Asymptotic_analysis) worst-case relative change in output for a relative change in input. The "function" is the solution of a problem and the "arguments" are the data in the problem. The condition number is frequently applied to questions in [linear algebra](https://en.wikipedia.org/wiki/Linear_algebra), in which case the derivative is straightforward but the error could be in many different directions, and is thus computed from the geometry of the matrix. More generally, condition numbers can be defined for non-linear functions in several variables.

A problem with a low condition number is said to be ***well-conditioned***, while a problem with a high condition number is said to be ***ill-conditioned***. In non-mathematical terms, an ill-conditioned problem is one where, for a small change in the inputs (the [independent variables](https://en.wikipedia.org/wiki/Independent_variables)) there is a large change in the answer or [dependent variable](https://en.wikipedia.org/wiki/Dependent_variable). This means that the correct solution/answer to the equation becomes hard to find. The condition number is a property of the problem. Paired with the problem are any number of algorithms that can be used to solve the problem, that is, to calculate the solution. Some algorithms have a property called *[[Numerical Stability|backward stability]]*; in general, a backward stable algorithm can be expected to accurately solve well-conditioned problems. Numerical analysis textbooks give formulas for the condition numbers of problems and identify known backward stable algorithms.

As a rule of thumb, if the condition number $\kappa (A)=10^{k}$, then up to $k$ digits of accuracy may be lost on top of what would be lost to the numerical method due to loss of precision from arithmetic methods. However, the condition number does not give the exact value of the maximum inaccuracy that may occur in the algorithm. It generally just bounds it with an estimate (whose computed value depends on the choice of the norm to measure the inaccuracy).

## Matrices

For example, the condition number associated with the [linear equation](https://en.wikipedia.org/wiki/Linear_equation) *Ax* = *b* gives a bound on how inaccurate the solution *x* will be after approximation. Note that this is before the effects of [round-off error](https://en.wikipedia.org/wiki/Round-off_error) are taken into account; conditioning is a property of the [matrix](https://en.wikipedia.org/wiki/Matrix_(mathematics) "Matrix (mathematics)"), not the [algorithm](https://en.wikipedia.org/wiki/Algorithm) or [floating-point](https://en.wikipedia.org/wiki/Floating-point) accuracy of the computer used to solve the corresponding system. In particular, one should think of the condition number as being (very roughly) the rate at which the solution *x* will change with respect to a change in *b*. Thus, if the condition number is large, even a small error in *b* may cause a large error in *x*. On the other hand, if the condition number is small, then the error in *x* will not be much bigger than the error in *b*.

The condition number is defined more precisely to be the maximum ratio of the [relative error](https://en.wikipedia.org/wiki/Relative_error) in *x* to the relative error in *b*.

Let *e* be the error in *b*. Assuming that *A* is a [nonsingular](https://en.wikipedia.org/wiki/Nonsingular_matrix) matrix, the error in the solution *A*<sup>−1</sup>*b* is *A*<sup>−1</sup>*e*. The ratio of the relative error in the solution to the relative error in *b* is

${\frac {\left\|A^{-1}e\right\|}{\left\|A^{-1}b\right\|}}/{\frac {\|e\|}{\|b\|}}={\frac {\left\|A^{-1}e\right\|}{\|e\|}}{\frac {\|b\|}{\left\|A^{-1}b\right\|}}.$

The maximum value (for nonzero *b* and *e*) is then seen to be the product of the two [operator norms](https://en.wikipedia.org/wiki/Operator_norm) as follows:

${\begin{aligned}\max _{e,b\neq 0}\left\{{\frac {\left\|A^{-1}e\right\|}{\|e\|}}{\frac {\|b\|}{\left\|A^{-1}b\right\|}}\right\}&=\max _{e\neq 0}\left\{{\frac {\left\|A^{-1}e\right\|}{\|e\|}}\right\}\,\max _{b\neq 0}\left\{{\frac {\|b\|}{\left\|A^{-1}b\right\|}}\right\}\\&=\max _{e\neq 0}\left\{{\frac {\left\|A^{-1}e\right\|}{\|e\|}}\right\}\,\max _{x\neq 0}\left\{{\frac {\|Ax\|}{\|x\|}}\right\}\\&=\left\|A^{-1}\right\|\,\|A\|.\end{aligned}}$

The same definition is used for any consistent [norm](https://en.wikipedia.org/wiki/Matrix_norm), i.e. one that satisfies

$\kappa (A)=\left\|A^{-1}\right\|\,\left\|A\right\|\geq \left\|A^{-1}A\right\|=1.$

When the condition number is exactly one (which can only happen if *A* is a scalar multiple of a [linear isometry](https://en.wikipedia.org/wiki/Isometry#Linear_isometry)), then a solution algorithm can find (in principle, meaning if the algorithm introduces no errors of its own) an approximation of the solution whose precision is no worse than that of the data.

However, it does not mean that the algorithm will converge rapidly to this solution, just that it will not diverge arbitrarily because of inaccuracy on the source data (backward error), provided that the forward error introduced by the algorithm does not diverge as well because of accumulating intermediate rounding errors.<sup>\[*[clarification needed](https://en.wikipedia.org/wiki/Wikipedia:Please_clarify)*\]</sup>

The condition number may also be infinite, but this implies that the problem is [ill-posed](https://en.wikipedia.org/wiki/Well-posed_problem) (does not possess a unique, well-defined solution for each choice of data; that is, the matrix is not [invertible](https://en.wikipedia.org/wiki/Invertible_matrix)), and no algorithm can be expected to reliably find a solution.

The definition of the condition number depends on the choice of [norm](https://en.wikipedia.org/wiki/Norm_(mathematics) "Norm (mathematics)"), as can be illustrated by two examples.

If $\|\cdot \|$ is the [matrix norm induced by the (vector) Euclidean norm](https://en.wikipedia.org/wiki/Matrix_norm#Matrix_norms_induced_by_vector_norms) (sometimes known as the *L*<sup>2</sup> norm and typically denoted as $\|\cdot \|_{2}$), then

$\kappa (A)={\frac {\sigma _{\text{max}}(A)}{\sigma _{\text{min}}(A)}},$

where $\sigma _{\text{max}}(A)$ and $\sigma _{\text{min}}(A)$ are maximal and minimal [singular values](https://en.wikipedia.org/wiki/Singular_value) of $A$ respectively. Hence:

- If $A$ is [normal](https://en.wikipedia.org/wiki/Normal_matrix), then 

$$
\kappa (A)={\frac {\max\{\left|\lambda (A)\right|\}}{\min\{\left|\lambda (A)\right|\}}},
$$

 where $\lambda _{\text{max}}(A)$ and $\lambda _{\text{min}}(A)$ are maximal and minimal (by moduli) [eigenvalues](https://en.wikipedia.org/wiki/Eigenvalue) of $A$ respectively.
- If $A$ is [unitary](https://en.wikipedia.org/wiki/Unitary_matrix), then $\kappa (A)=1.$

The condition number with respect to *L*<sup>2</sup> arises so often in [numerical linear algebra](https://en.wikipedia.org/wiki/Numerical_linear_algebra) that it is given a name, the **condition number of a matrix**.

If $\|\cdot \|$ is the [matrix norm induced by the $L^{\infty }$ (vector) norm](https://en.wikipedia.org/wiki/Matrix_norm#Matrix_norms_induced_by_vector_norms) and $A$ is [lower triangular](https://en.wikipedia.org/wiki/Triangular_matrix) non-singular (i.e. $a_{ii}\neq 0$ for all $i$), then

$\kappa (A)\geq {\frac {\max _{i}{\big (}|a_{ii}|{\big )}}{\min _{i}{\big (}|a_{ii}|{\big )}}}$

recalling that the eigenvalues of any triangular matrix are simply the diagonal entries.

The condition number computed with this norm is generally larger than the condition number computed relative to the [Euclidean norm](https://en.wikipedia.org/wiki/Euclidean_norm), but it can be evaluated more easily (and this is often the only practicably computable condition number, when the problem to solve involves a *non-linear algebra*<sup>\[*[clarification needed](https://en.wikipedia.org/wiki/Wikipedia:Please_clarify)*\]</sup>, for example when approximating irrational and [transcendental](https://en.wikipedia.org/wiki/Transcendental_function) functions or numbers with numerical methods).

If the condition number is not significantly larger than one, the matrix is [well-conditioned](https://en.wikipedia.org/wiki/Well-conditioned), which means that its inverse can be computed with good accuracy. If the condition number is very large, then the matrix is said to be [ill-conditioned](https://en.wikipedia.org/wiki/Ill-conditioned). Practically, such a matrix is almost singular, and the computation of its inverse, or solution of a linear system of equations is prone to large numerical errors.

A matrix that is not invertible is often said to have a condition number equal to infinity. Alternatively, it can be defined as $\kappa (A)=\|A\|\|A^{\dagger }\|$, where $A^{\dagger }$ is the Moore-Penrose [pseudoinverse](https://en.wikipedia.org/wiki/Pseudoinverse). For square matrices, this unfortunately makes the condition number discontinuous, but it is a useful definition for rectangular matrices, which are never invertible but are still used to define systems of equations.

## Nonlinear

Condition numbers can also be defined for nonlinear functions, and can be computed using [calculus](https://en.wikipedia.org/wiki/Calculus). The condition number varies with the point; in some cases one can use the maximum (or [supremum](https://en.wikipedia.org/wiki/Supremum)) condition number over the [domain](https://en.wikipedia.org/wiki/Domain_of_a_function) of the function or domain of the question as an overall condition number, while in other cases the condition number at a particular point is of more interest.

### One variable

The *absolute* condition number of a [differentiable function](https://en.wikipedia.org/wiki/Differentiable_function) $f$ in one variable is the [absolute value](https://en.wikipedia.org/wiki/Absolute_value) of the [derivative](https://en.wikipedia.org/wiki/Derivative) of the function:

$\left|f'(x)\right|$

The *relative* condition number of $f$ as a function is $\left|xf'/f\right|$. Evaluated at a point $x$, this is

$\left|{\frac {xf'(x)}{f(x)}}\right|=\left|{\frac {(\log f)'}{(\log x)'}}\right|.$

Note that this is the absolute value of the [elasticity](https://en.wikipedia.org/wiki/Elasticity_(economics) "Elasticity (economics)") of a function in economics.

Most elegantly, this can be understood as (the absolute value of) the ratio of the [logarithmic derivative](https://en.wikipedia.org/wiki/Logarithmic_derivative) of $f$, which is $(\log f)'=f'/f$, and the logarithmic derivative of $x$, which is $(\log x)'=x'/x=1/x$, yielding a ratio of $xf'/f$. This is because the logarithmic derivative is the [infinitesimal](https://en.wikipedia.org/wiki/Infinitesimal_calculus) rate of relative change in a function: it is the derivative $f'$ scaled by the value of $f$. Note that if a function has a [zero](https://en.wikipedia.org/wiki/Zero_of_a_function) at a point, its condition number at the point is infinite, as infinitesimal changes in the input can change the output from zero to positive or negative, yielding a ratio with zero in the denominator, hence infinite relative change.

More directly, given a small change $\Delta x$ in $x$, the relative change in $x$ is $[(x+\Delta x)-x]/x=(\Delta x)/x$, while the relative change in $f(x)$ is $[f(x+\Delta x)-f(x)]/f(x)$. Taking the ratio yields

${\frac {[f(x+\Delta x)-f(x)]/f(x)}{(\Delta x)/x}}={\frac {x}{f(x)}}{\frac {f(x+\Delta x)-f(x)}{(x+\Delta x)-x}}={\frac {x}{f(x)}}{\frac {f(x+\Delta x)-f(x)}{\Delta x}}.$

The last term is the [difference quotient](https://en.wikipedia.org/wiki/Difference_quotient) (the slope of the [secant line](https://en.wikipedia.org/wiki/Secant_line)), and taking the [limit](https://en.wikipedia.org/wiki/Limit_(mathematics) "Limit (mathematics)") yields the derivative.

Condition numbers of common [elementary functions](https://en.wikipedia.org/wiki/Elementary_function) are particularly important in computing [significant figures](https://en.wikipedia.org/wiki/Significant_figures) and can be computed immediately from the derivative. A few important ones are given below:

|  |  |  |
|----|----|----|
| Name | Symbol | Relative condition number |
| Addition / subtraction | $x+a$ | $\left|{\frac {x}{x+a}}\right|$ |
| Scalar multiplication | $ax$ | $1$ |
| Division | $1/x$ | $1$ |
| [Polynomial](https://en.wikipedia.org/wiki/Polynomial) | $x^{n}$ | $|n|$ |
| [Exponential function](https://en.wikipedia.org/wiki/Exponential_function) | $e^{x}$ | $|x|$ |
| [Natural logarithm](https://en.wikipedia.org/wiki/Natural_logarithm) function | $\ln(x)$ | $\left|{\frac {1}{\ln(x)}}\right|$ |
| Sine function | $\sin(x)$ | $|x\cot(x)|$ |
| Cosine function | $\cos(x)$ | $|x\tan(x)|$ |
| Tangent function | $\tan(x)$ | $|x(\tan(x)+\cot(x))|$ |
| Inverse sine function | $\arcsin(x)$ | ${\frac {x}{{\sqrt {1-x^{2}}}\arcsin(x)}}$ |
| Inverse cosine function | $\arccos(x)$ | ${\frac {|x|}{{\sqrt {1-x^{2}}}\arccos(x)}}$ |
| Inverse tangent function | $\arctan(x)$ | ${\frac {x}{(1+x^{2})\arctan(x)}}$ |

### Several variables

Condition numbers can be defined for any function $f$ mapping its data from some [domain](https://en.wikipedia.org/wiki/Domain_of_a_function) (e.g. an $m$-tuple of [real numbers](https://en.wikipedia.org/wiki/Real_number) $x$) into some [codomain](https://en.wikipedia.org/wiki/Codomain) (e.g. an $n$-tuple of real numbers $f(x)$), where both the domain and codomain are [Banach spaces](https://en.wikipedia.org/wiki/Banach_space). They express how sensitive that function is to small changes (or small errors) in its arguments. This is crucial in assessing the sensitivity and potential accuracy difficulties of numerous computational problems, for example, [polynomial root finding](https://en.wikipedia.org/wiki/Root-finding_algorithms#Roots_of_polynomials) or computing [eigenvalues](https://en.wikipedia.org/wiki/Eigenvalue).

The condition number of $f$ at a point $x$ (specifically, its **relative condition number**) is then defined to be the maximum ratio of the fractional change in $f(x)$ to any fractional change in $x$, in the limit where the change $\delta x$ in $x$ becomes infinitesimally small:

$\lim _{\varepsilon \to 0^{+}}\sup _{\|\delta x\|\leq \varepsilon }\left[\left.{\frac {\left\|f(x+\delta x)-f(x)\right\|}{\|f(x)\|}}\right/{\frac {\|\delta x\|}{\|x\|}}\right],$

where $\|\cdot \|$ is a [norm](https://en.wikipedia.org/wiki/Norm_(mathematics) "Norm (mathematics)") on the domain/codomain of $f$.

If $f$ is differentiable, this is equivalent to:

${\frac {\|J(x)\|}{\|f(x)\|/\|x\|}},$

where $J(x)$ denotes the [[Jacobian Matrix]] of [partial derivatives](https://en.wikipedia.org/wiki/Partial_derivative) of $f$ at $x$, and $\|J(x)\|$ is the [induced norm](https://en.wikipedia.org/wiki/Induced_norm) on the matrix.

## See also

- [Numerical methods for linear least squares](https://en.wikipedia.org/wiki/Numerical_methods_for_linear_least_squares)
- [[Numerical Stability]]
- [Preconditioner](https://en.wikipedia.org/wiki/Preconditioner)
- [Hilbert matrix](https://en.wikipedia.org/wiki/Hilbert_matrix)
- [Ill-posed problem](https://en.wikipedia.org/wiki/Ill-posed_problem)
- [Singular value](https://en.wikipedia.org/wiki/Singular_value)
- [Wilson matrix](https://en.wikipedia.org/wiki/Wilson_matrix)

## References

1.  Belsley, David A.; [Kuh, Edwin](https://en.wikipedia.org/wiki/Edwin_Kuh); Welsch, Roy E. (1980). ["The Condition Number"](https://books.google.com/books?id=GECBEUJVNe0C&pg=PA100). *Regression Diagnostics: Identifying Influential Data and Sources of Collinearity*. New York: John Wiley & Sons. pp. 100–104. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-05856-4](https://en.wikipedia.org/wiki/Special:BookSources/0-471-05856-4).
2.  [Pesaran, M. Hashem](https://en.wikipedia.org/wiki/M._Hashem_Pesaran) (2015). ["The Multicollinearity Problem"](https://books.google.com/books?id=7RokCwAAQBAJ&pg=PA70). *Time Series and Panel Data Econometrics*. New York: Oxford University Press. pp. 67–72 \[p. 70\]. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-19-875998-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-19-875998-0).
3.  Cheney; Kincaid (2008). [Numerical Mathematics and Computing](https://books.google.com/books?id=ZUfVZELlrMEC&pg=PA321). Cengage Learning. p. 321. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-495-11475-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-495-11475-8).
4.  ^    Trefethen, L. N.; Bau, D. (1997). [Numerical Linear Algebra](https://books.google.com/books?id=JaPtxOytY7kC&q=978-0898713619). SIAM. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-89871-361-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-89871-361-9).

## Further reading

- [Demmel, James](https://en.wikipedia.org/wiki/James_Demmel) (1990). "Nearest Defective Matrices and the Geometry of Ill-conditioning". In Cox, M. G.; Hammarling, S. (eds.). *Reliable Numerical Computation*. Oxford: Clarendon Press. pp. 35–55. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-19-853564-3](https://en.wikipedia.org/wiki/Special:BookSources/0-19-853564-3).
- Ludwig, Oswaldo (2025). "The Condition Number as a Scale-Invariant Proxy for Information Encoding in Neural Units". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2506.16289](https://arxiv.org/abs/2506.16289) \[[stat.ML](https://arxiv.org/archive/stat.ML)\].

## External links

- [Condition Number of a Matrix](https://web.archive.org/web/20070121001740/http://numericalmethods.eng.usf.edu/mws/gen/04sle/mws_gen_sle_spe_adequacy.pdf) at *Holistic Numerical Methods Institute*
- [MATLAB library function to determine condition number](http://www.mathworks.in/help/techdoc/ref/cond.html)
- [Condition number – Encyclopedia of Mathematics](https://www.encyclopediaofmath.org/index.php/Condition_number)
- [Who Invented the Matrix Condition Number? by Nick Higham](https://nhigham.com/2019/01/23/who-invented-the-matrix-condition-number/)
