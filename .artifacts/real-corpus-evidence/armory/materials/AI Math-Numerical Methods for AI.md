[[ai-math.base]]

> Source: [Numerical analysis](https://en.wikipedia.org/wiki/Numerical_analysis)
> License: Wikipedia content is available under CC BY-SA 4.0.

![[media/432ed3572b22f96f4e835d9e8a039c29c57cc636.jpg]]
Babylonian clay tablet [YBC 7289](https://en.wikipedia.org/wiki/YBC_7289) (c. 1800–1600 BCE) with annotations. The approximation of the [square root of 2](https://en.wikipedia.org/wiki/Square_root_of_2) is four [sexagesimal](https://en.wikipedia.org/wiki/Sexagesimal) figures, which is about six [decimal](https://en.wikipedia.org/wiki/Decimal) figures. 1 + 24/60 + 51/60<sup>2</sup> + 10/60<sup>3</sup> = 1.41421296...

**Numerical analysis** is the study of [algorithms](https://en.wikipedia.org/wiki/Algorithm) for the problems of [continuous mathematics](https://en.wikipedia.org/wiki/Mathematical_analysis). These algorithms involve [real](https://en.wikipedia.org/wiki/Real_number) or [complex](https://en.wikipedia.org/wiki/Complex_number) variables (in contrast to [discrete mathematics](https://en.wikipedia.org/wiki/Discrete_mathematics)), and typically use numerical [approximation](https://en.wikipedia.org/wiki/Approximation) in addition to [symbolic manipulation](https://en.wikipedia.org/wiki/Symbolic_computation).

Numerical analysis finds application in all fields of engineering and the physical sciences, and in the 21st century also the life and social sciences like economics, medicine, business and even the arts. Current growth in computing power has enabled the use of more complex numerical analysis, providing detailed and realistic mathematical models in science and engineering. Examples of numerical analysis include: [ordinary differential equations](https://en.wikipedia.org/wiki/Ordinary_differential_equation) as found in [celestial mechanics](https://en.wikipedia.org/wiki/Celestial_mechanics) (predicting the motions of planets, stars and galaxies), [numerical linear algebra](https://en.wikipedia.org/wiki/Numerical_linear_algebra) in data analysis, and [stochastic differential equations](https://en.wikipedia.org/wiki/Stochastic_differential_equation) and [[Markov Chain|Markov chains]] for simulating living cells in medicine and biology.

Before modern computers, [numerical methods](https://en.wikipedia.org/wiki/Numerical_method) often relied on hand [interpolation](https://en.wikipedia.org/wiki/Interpolation) formulas, using data from large printed tables. Since the mid-20th century, computers calculate the required functions instead, but many of the same formulas continue to be used in software algorithms.

The numerical point of view goes back to the earliest mathematical writings. A tablet from the [Yale Babylonian Collection](https://en.wikipedia.org/wiki/Yale_Babylonian_Collection) ([YBC 7289](https://en.wikipedia.org/wiki/YBC_7289)), gives a [sexagesimal](https://en.wikipedia.org/wiki/Sexagesimal) numerical approximation of the [square root of 2](https://en.wikipedia.org/wiki/Square_root_of_2), the length of the [diagonal](https://en.wikipedia.org/wiki/Diagonal) in a [unit square](https://en.wikipedia.org/wiki/Unit_square).

Numerical analysis continues this long tradition: rather than giving exact symbolic answers translated into digits and applicable only to real-world measurements, approximate solutions within specified error bounds are used.

## Applications

The overall goal of the field of numerical analysis is the design and analysis of techniques to give approximate but accurate solutions to a wide variety of hard problems, many of which are infeasible to solve symbolically:

- Advanced numerical methods are essential in making [numerical weather prediction](https://en.wikipedia.org/wiki/Numerical_weather_prediction) feasible.
- Computing the trajectory of a spacecraft requires the accurate numerical solution of a system of ordinary differential equations.
- Car companies can improve the crash safety of their vehicles by using computer simulations of car crashes. Such simulations essentially consist of solving [partial differential equations](https://en.wikipedia.org/wiki/Partial_differential_equation) numerically.
- In the financial field, (private investment funds) and other financial institutions use [quantitative finance](https://en.wikipedia.org/wiki/Quantitative_finance) tools from numerical analysis to attempt to calculate the value of [stocks](https://en.wikipedia.org/wiki/Share_capital) and [derivatives](https://en.wikipedia.org/wiki/Derivative_(finance) "Derivative (finance)") more precisely than other market participants.
- Airlines use sophisticated optimization algorithms to decide ticket prices, airplane and crew assignments and fuel needs. Historically, such algorithms were developed within the overlapping field of [operations research](https://en.wikipedia.org/wiki/Operations_research).
- Insurance companies use numerical programs for [actuarial](https://en.wikipedia.org/wiki/Actuary) analysis.

## History

The field of numerical analysis predates the invention of modern computers by many centuries. [Linear interpolation](https://en.wikipedia.org/wiki/Linear_interpolation) was already in use more than 2000 years ago. Many great mathematicians of the past were preoccupied by numerical analysis, as is obvious from the names of important algorithms like [Newton's method](https://en.wikipedia.org/wiki/Newton%27s_method), [Lagrange interpolation polynomial](https://en.wikipedia.org/wiki/Lagrange_polynomial), [Gaussian elimination](https://en.wikipedia.org/wiki/Gaussian_elimination), or [Euler's method](https://en.wikipedia.org/wiki/Euler%27s_method). The origins of modern numerical analysis are often linked to a 1947 paper by [John von Neumann](https://en.wikipedia.org/wiki/John_von_Neumann) and [Herman Goldstine](https://en.wikipedia.org/wiki/Herman_Goldstine), but others consider modern numerical analysis to go back to work by [E. T. Whittaker](https://en.wikipedia.org/wiki/E._T._Whittaker) in 1912.

![[media/098332619f8c12537a43471493244e4df3ef3b16.jpg]]
NIST publication

To facilitate computations by hand, large books were produced with formulas and tables of data such as interpolation points and function coefficients. Using these tables, often calculated out to 16 decimal places or more for some functions, one could look up values to plug into the formulas given and achieve very good numerical estimates of some functions. The canonical work in the field is the [NIST](https://en.wikipedia.org/wiki/NIST) publication edited by [Abramowitz and Stegun](https://en.wikipedia.org/wiki/Abramowitz_and_Stegun), a 1000-plus page book of a very large number of commonly used formulas and functions and their values at many points. The function values are no longer very useful when a computer is available, but the large listing of formulas can still be very handy.

The [mechanical calculator](https://en.wikipedia.org/wiki/Mechanical_calculator) was also developed as a tool for hand computation. These calculators evolved into electronic computers in the 1940s, and it was then found that these computers were also useful for administrative purposes. But the invention of the computer also influenced the field of numerical analysis, since now longer and more complicated calculations could be done.

The [Leslie Fox Prize for Numerical Analysis](https://en.wikipedia.org/wiki/Leslie_Fox_Prize_for_Numerical_Analysis) was initiated in 1985 by the [Institute of Mathematics and its Applications](https://en.wikipedia.org/wiki/Institute_of_Mathematics_and_its_Applications).

## Key concepts

### Direct and iterative methods

Direct methods compute the solution to a problem in a finite number of steps. These methods would give the precise answer if they were performed in [infinite precision arithmetic](https://en.wikipedia.org/wiki/Arbitrary-precision_arithmetic). Examples include [Gaussian elimination](https://en.wikipedia.org/wiki/Gaussian_elimination), the [[QR Decomposition|QR factorization]] method for solving [systems of linear equations](https://en.wikipedia.org/wiki/System_of_linear_equations), and the [simplex method](https://en.wikipedia.org/wiki/Simplex_method) of [linear programming](https://en.wikipedia.org/wiki/Linear_programming). In practice, [[Floating-Point Arithmetic|finite precision]] is used and the result is an approximation of the true solution (assuming [stability](https://en.wikipedia.org/wiki/Numerically_stable)).

In contrast to direct methods, [iterative methods](https://en.wikipedia.org/wiki/Iterative_method) are not expected to terminate in a finite number of steps, even if infinite precision were possible. Starting from an initial guess, iterative methods form successive approximations that [converge](https://en.wikipedia.org/wiki/Limit_of_a_sequence) to the exact solution only in the limit. A convergence test, often involving [the residual](https://en.wikipedia.org/wiki/Residual_(numerical_analysis) "Residual (numerical analysis)"), is specified in order to decide when a sufficiently accurate solution has (hopefully) been found. Even using infinite precision arithmetic these methods would not reach the solution within a finite number of steps (in general). Examples include Newton's method, the [bisection method](https://en.wikipedia.org/wiki/Bisection_method), and [Jacobi iteration](https://en.wikipedia.org/wiki/Jacobi_iteration). In computational matrix algebra, iterative methods are generally needed for large problems.

Iterative methods are more common than direct methods in numerical analysis. Some methods are direct in principle but are usually used as though they were not, e.g. [GMRES](https://en.wikipedia.org/wiki/GMRES) and the [[Conjugate Gradient Method]]. For these methods the number of steps needed to obtain the exact solution is so large that an approximation is accepted in the same manner as for an iterative method.

As an example, consider the problem of solving

3*x*<sup>3</sup> + 4 = 28

for the unknown quantity *x*.

|                   |                            |
|-------------------|----------------------------|
|                   | 3*x*<sup>3</sup> + 4 = 28. |
| *Subtract 4*      | 3*x*<sup>3</sup> = 24.     |
| *Divide by 3*     | *x*<sup>3</sup> =  8.      |
| *Take cube roots* | *x* =  2.                  |

Direct method {style="margin:auto; text-align:right"}

For the iterative method, apply the [bisection method](https://en.wikipedia.org/wiki/Bisection_method) to *f*(*x*) = 3*x*<sup>3</sup> − 24. The initial values are *a* = 0, *b* = 3, *f*(*a*) = −24, *f*(*b*) = 57.

|       |      |        |          |
|-------|------|--------|----------|
| *a*   | *b*  | mid    | *f*(mid) |
| 0     | 3    | 1.5    | −13.875  |
| 1.5   | 3    | 2.25   | 10.17... |
| 1.5   | 2.25 | 1.875  | −4.22... |
| 1.875 | 2.25 | 2.0625 | 2.32...  |

Iterative method {.wikitable style="margin:auto;"}

From this table it can be concluded that the solution is between 1.875 and 2.0625. The algorithm might return any number in that range with an error less than 0.2.

### Conditioning

Ill-conditioned problem: Take the function *f*(*x*) = 1/(*x* − 1). Note that *f*(1.1) = 10 and *f*(1.001) = 1000: a change in *x* of less than 0.1 turns into a change in *f*(*x*) of nearly 1000. Evaluating *f*(*x*) near *x* = 1 is an ill-conditioned problem.

Well-conditioned problem: By contrast, evaluating the same function *f*(*x*) = 1/(*x* − 1) near *x* = 10 is a well-conditioned problem. For instance, *f*(10) = 1/9 ≈ 0.111 and *f*(11) = 0.1: a modest change in *x* leads to a modest change in *f*(*x*).

### Discretization

Furthermore, continuous problems must sometimes be replaced by a discrete problem whose solution is known to approximate that of the continuous problem; this process is called '[discretization](https://en.wikipedia.org/wiki/Discretization)'. For example, the solution of a [differential equation](https://en.wikipedia.org/wiki/Differential_equation) is a [function](https://en.wikipedia.org/wiki/Function_(mathematics) "Function (mathematics)"). This function must be represented by a finite amount of data, for instance by its value at a finite number of points at its domain, even though this domain is a [continuum](https://en.wikipedia.org/wiki/Continuum_(set_theory) "Continuum (set theory)").

## Generation and propagation of errors

The study of errors forms an important part of numerical analysis. There are several ways in which error can be introduced in the solution of the problem.

### Round-off

[Round-off errors](https://en.wikipedia.org/wiki/Round-off_error) arise because it is impossible to represent all [real numbers](https://en.wikipedia.org/wiki/Real_number) exactly on a machine with finite memory (which is what all practical [digital computers](https://en.wikipedia.org/wiki/Digital_computer) are).

### Truncation and discretization error

[Truncation errors](https://en.wikipedia.org/wiki/Truncation_error) are committed when an iterative method is terminated or a mathematical procedure is approximated and the approximate solution differs from the exact solution. Similarly, discretization induces a [discretization error](https://en.wikipedia.org/wiki/Discretization_error) because the solution of the discrete problem does not coincide with the solution of the continuous problem. In the example above to compute the solution of $3x^{3}+4=28$, after ten iterations, the calculated root is roughly 1.99. Therefore, the truncation error is roughly 0.01.

Once an error is generated, it propagates through the calculation. For example, the operation + on a computer is inexact. A calculation of the type $a+b+c+d+e$ is even more inexact.

A truncation error is created when a mathematical procedure is approximated. To integrate a function exactly, an infinite sum of regions must be found, but numerically only a finite sum of regions can be found, and hence the approximation of the exact solution. Similarly, to differentiate a function, the differential element approaches zero, but numerically only a nonzero value of the differential element can be chosen.

### Numerical stability and well-posed problems

An algorithm is called *[numerically stable](https://en.wikipedia.org/wiki/Numerically_stable)* if an error, whatever its cause, does not grow to be much larger during the calculation. This happens if the problem is *[well-conditioned](https://en.wikipedia.org/wiki/Well-conditioned)*, meaning that the solution changes by only a small amount if the problem data are changed by a small amount. To the contrary, if a problem is 'ill-conditioned', then any small error in the data will grow to be a large error. Both the original problem and the algorithm used to solve that problem can be well-conditioned or ill-conditioned, and any combination is possible. So an algorithm that solves a well-conditioned problem may be either numerically stable or numerically unstable. An art of numerical analysis is to find a stable algorithm for solving a well-posed mathematical problem.

## Areas of study

The field of numerical analysis includes many sub-disciplines. Some of the major ones are:

### Computing values of functions

<table class="wikitable" style="float: right; width: 250px; clear: right; margin-left: 1em;">

<p>Interpolation: Observing that the temperature varies from 20 degrees Celsius at 1:00 to 14 degrees at 3:00, a linear interpolation of this data would conclude that it was 17 degrees at 2:00 and 18.5 degrees at 1:30pm.</p>
<p>Extrapolation: If the [gross domestic product](https://en.wikipedia.org/wiki/Gross_domestic_product) of a country has been growing an average of 5% per year and was 100 billion last year, it might be extrapolated that it will be 105 billion this year.</p>
![[media/f11111dc74ad04882c55842f17c08bc2e34ce482.png]]
A line through 20 points
<p>Regression: In linear regression, given <em>n</em> points, a line is computed that passes as close as possible to those <em>n</em> points.</p>
![[media/8664cfc9d3cd8242ae7487abe98625604b7082c2.jpg]]
How much for a glass of lemonade?
<p>Optimization: Suppose lemonade is sold at a [lemonade stand](https://en.wikipedia.org/wiki/Lemonade_stand), at $1.00 per glass, that 197 glasses of lemonade can be sold per day, and that for each increase of $0.01, one less glass of lemonade will be sold per day. If $1.485 could be charged, profit would be maximized, but due to the constraint of having to charge a whole-cent amount, charging $1.48 or $1.49 per glass will both yield the maximum income of $220.52 per day.</p>
![[media/eccbd0502dedeb6b1abec7a534d48d12088ea9b2.png]]
Wind direction in blue, true trajectory in black, Euler method in red
<p>Differential equation: If 100 fans are set up to blow air from one end of the room to the other and then a feather is dropped into the wind, what happens? The feather will follow the air currents, which may be very complex. One approximation is to measure the speed at which the air is blowing near the feather every second, and advance the simulated feather as if it were moving in a straight line at that same speed for one second, before measuring the wind speed again. This is called the [Euler method](https://en.wikipedia.org/wiki/Euler_method) for solving an ordinary differential equation.</p>

</table>

One of the simplest problems is the evaluation of a function at a given point. The most straightforward approach, of just plugging in the number in the formula is sometimes not very efficient. For polynomials, a better approach is using the [Horner scheme](https://en.wikipedia.org/wiki/Horner_scheme), since it reduces the necessary number of multiplications and additions. Generally, it is important to estimate and control [round-off errors](https://en.wikipedia.org/wiki/Round-off_error) arising from the use of [[Floating-Point Arithmetic]].

### Interpolation, extrapolation, and regression

[Interpolation](https://en.wikipedia.org/wiki/Interpolation) solves the following problem: given the value of some unknown function at a number of points, what value does that function have at some other point between the given points?

[Extrapolation](https://en.wikipedia.org/wiki/Extrapolation) is very similar to interpolation, except that now the value of the unknown function at a point which is outside the given points must be found.

[Regression](https://en.wikipedia.org/wiki/Regression_analysis) is also similar, but it takes into account that the data are imprecise. Given some points, and a measurement of the value of some function at these points (with an error), the unknown function can be found. The [least squares](https://en.wikipedia.org/wiki/Numerical_methods_for_linear_least_squares)-method is one way to achieve this.

### Solving equations and systems of equations

Another fundamental problem is computing the solution of some given equation. Two cases are commonly distinguished, depending on whether the equation is linear or not. For instance, the equation $2x+5=3$ is linear while $2x^{2}+5=3$ is not.

Much effort has been put in the development of methods for solving [systems of linear equations](https://en.wikipedia.org/wiki/Systems_of_linear_equations). Standard direct methods, i.e., methods that use some [matrix decomposition](https://en.wikipedia.org/wiki/Matrix_decomposition) are [Gaussian elimination](https://en.wikipedia.org/wiki/Gaussian_elimination), [[LU Decomposition]], [[Cholesky Decomposition]] for [symmetric](https://en.wikipedia.org/wiki/Symmetric_matrix) (or [hermitian](https://en.wikipedia.org/wiki/Hermitian_matrix)) and [[Positive-Definite Matrix]], and [[QR Decomposition]] for non-square matrices. Iterative methods such as the [Jacobi method](https://en.wikipedia.org/wiki/Jacobi_method), [Gauss–Seidel method](https://en.wikipedia.org/wiki/Gauss%E2%80%93Seidel_method), [successive over-relaxation](https://en.wikipedia.org/wiki/Successive_over-relaxation) and [[Conjugate Gradient Method]] are usually preferred for large systems. General iterative methods can be developed using a [matrix splitting](https://en.wikipedia.org/wiki/Matrix_splitting).

[Root-finding algorithms](https://en.wikipedia.org/wiki/Root-finding_algorithm) are used to solve nonlinear equations (they are so named since a root of a function is an argument for which the function yields zero). If the function is [differentiable](https://en.wikipedia.org/wiki/Derivative) and the derivative is known, then Newton's method is a popular choice. [Linearization](https://en.wikipedia.org/wiki/Linearization) is another technique for solving nonlinear equations.

### Solving eigenvalue or singular value problems

Several important problems can be phrased in terms of [eigenvalue decompositions](https://en.wikipedia.org/wiki/Eigenvalue_decomposition) or [[Singular Value Decomposition|singular value decompositions]]. For instance, the [spectral image compression](https://en.wikipedia.org/wiki/Image_compression) algorithm is based on the singular value decomposition. The corresponding tool in statistics is called [[Principal Component Analysis]].

### Optimization

Optimization problems ask for the point at which a given function is maximized (or minimized). Often, the point also has to satisfy some [constraints](https://en.wikipedia.org/wiki/Constraint_(mathematics) "Constraint (mathematics)").

The field of optimization is further split in several subfields, depending on the form of the [objective function](https://en.wikipedia.org/wiki/Objective_function) and the constraint. For instance, [linear programming](https://en.wikipedia.org/wiki/Linear_programming) deals with the case that both the objective function and the constraints are linear. A famous method in linear programming is the [simplex method](https://en.wikipedia.org/wiki/Simplex_algorithm).

The method of [[Lagrange Multipliers]] can be used to reduce optimization problems with constraints to unconstrained optimization problems.

### Evaluating integrals

Numerical integration, in some instances also known as numerical [quadrature](https://en.wikipedia.org/wiki/Quadrature_(mathematics) "Quadrature (mathematics)"), asks for the value of a definite [integral](https://en.wikipedia.org/wiki/Integral). Popular methods use one of the [Newton–Cotes formulas](https://en.wikipedia.org/wiki/Newton%E2%80%93Cotes_formulas) (like the midpoint rule or [Simpson's rule](https://en.wikipedia.org/wiki/Simpson%27s_rule)) or [Gaussian quadrature](https://en.wikipedia.org/wiki/Gaussian_quadrature). These methods rely on a "divide and conquer" strategy, whereby an integral on a relatively large set is broken down into integrals on smaller sets. In higher dimensions, where these methods become prohibitively expensive in terms of computational effort, one may use [[Monte Carlo Method|Monte Carlo]] or [quasi-Monte Carlo methods](https://en.wikipedia.org/wiki/Quasi-Monte_Carlo_method) (see [Monte Carlo integration](https://en.wikipedia.org/wiki/Monte_Carlo_integration)), or, in modestly large dimensions, the method of [sparse grids](https://en.wikipedia.org/wiki/Sparse_grid).

### Differential equations

Numerical analysis is also concerned with computing (in an approximate way) the solution of [differential equations](https://en.wikipedia.org/wiki/Differential_equations), both [ordinary differential equations](https://en.wikipedia.org/wiki/Ordinary_differential_equations) and [partial differential equations](https://en.wikipedia.org/wiki/Partial_differential_equations).

Partial differential equations are solved by first discretizing the equation, bringing it into a finite-dimensional subspace. This can be done by a [finite element method](https://en.wikipedia.org/wiki/Finite_element_method), a [finite difference](https://en.wikipedia.org/wiki/Finite_difference) method, or (particularly in engineering) a [finite volume method](https://en.wikipedia.org/wiki/Finite_volume_method). The theoretical justification of these methods often involves theorems from [functional analysis](https://en.wikipedia.org/wiki/Functional_analysis). This reduces the problem to the solution of an algebraic equation.

## Software

Since the late twentieth century, most algorithms are implemented in a variety of programming languages. The [Netlib](https://en.wikipedia.org/wiki/Netlib) repository contains various collections of software routines for numerical problems, mostly in [Fortran](https://en.wikipedia.org/wiki/Fortran) and [C](https://en.wikipedia.org/wiki/C_(programming_language) "C (programming language)"). Commercial products implementing many different numerical algorithms include the [IMSL](https://en.wikipedia.org/wiki/IMSL_Numerical_Libraries) and [NAG](https://en.wikipedia.org/wiki/Numerical_Algorithms_Group) libraries; a [free-software](https://en.wikipedia.org/wiki/Free_software) alternative is the [GNU Scientific Library](https://en.wikipedia.org/wiki/GNU_Scientific_Library).

Over the years the [Royal Statistical Society](https://en.wikipedia.org/wiki/Royal_Statistical_Society) published numerous algorithms in its [Applied Statistics](https://en.wikipedia.org/wiki/Journal_of_the_Royal_Statistical_Society,_Series_C_(Applied_Statistics)) (code for these "AS" functions is [here](https://jblevins.org/mirror/amiller/#apstat)); [ACM](https://en.wikipedia.org/wiki/Association_for_Computing_Machinery) similarly, in its *[Transactions on Mathematical Software](https://en.wikipedia.org/wiki/Transactions_on_Mathematical_Software)* ("TOMS" code is [here](https://jblevins.org/mirror/amiller/#toms)). The [Naval Surface Warfare Center](https://en.wikipedia.org/wiki/Naval_Surface_Warfare_Center) several times published its [Library of Mathematics Subroutines](https://apps.dtic.mil/sti/pdfs/ADA476840.pdf) (code [here](https://jblevins.org/mirror/amiller/#nswc)).

There are several popular numerical computing applications such as [MATLAB](https://en.wikipedia.org/wiki/MATLAB), [TK Solver](https://en.wikipedia.org/wiki/TK_Solver), [S-PLUS](https://en.wikipedia.org/wiki/S-PLUS), and [IDL](https://en.wikipedia.org/wiki/IDL_(programming_language) "IDL (programming language)") as well as free and open-source alternatives such as [FreeMat](https://en.wikipedia.org/wiki/FreeMat), [Scilab](https://en.wikipedia.org/wiki/Scilab), [GNU Octave](https://en.wikipedia.org/wiki/GNU_Octave) (similar to Matlab), and [IT++](https://en.wikipedia.org/wiki/IT%2B%2B) (a C++ library). There are also programming languages such as [R](https://en.wikipedia.org/wiki/R_(programming_language) "R (programming language)") (similar to S-PLUS), [Julia](https://en.wikipedia.org/wiki/Julia_(programming_language) "Julia (programming language)"), and [Python](https://en.wikipedia.org/wiki/Python_(programming_language) "Python (programming language)") with libraries such as [NumPy](https://en.wikipedia.org/wiki/NumPy), [SciPy](https://en.wikipedia.org/wiki/SciPy) and [SymPy](https://en.wikipedia.org/wiki/SymPy). Performance varies widely: while vector and matrix operations are usually fast, scalar loops may vary in speed by more than an order of magnitude.

Many [computer algebra systems](https://en.wikipedia.org/wiki/Computer_algebra_system) such as [Mathematica](https://en.wikipedia.org/wiki/Mathematica) also benefit from the availability of [arbitrary-precision arithmetic](https://en.wikipedia.org/wiki/Arbitrary-precision_arithmetic) which can provide more accurate results.

Also, any [spreadsheet](https://en.wikipedia.org/wiki/Spreadsheet) [software](https://en.wikipedia.org/wiki/Software) can be used to solve simple problems relating to numerical analysis. [Excel](https://en.wikipedia.org/wiki/Microsoft_Excel), for example, has hundreds of [available functions](https://en.wikipedia.org/wiki/Microsoft_Excel#Functions), including for matrices, which may be used in conjunction with its [built in "solver"](https://en.wikipedia.org/wiki/Microsoft_Excel#Add-ins).

## See also

- [Category:Numerical analysts](https://en.wikipedia.org/wiki/Category:Numerical_analysts)
- [Analysis of algorithms](https://en.wikipedia.org/wiki/Analysis_of_algorithms)
- [Approximation theory](https://en.wikipedia.org/wiki/Approximation_theory)
- [Computational science](https://en.wikipedia.org/wiki/Computational_science)
- [Computational physics](https://en.wikipedia.org/wiki/Computational_physics)
- [Gordon Bell Prize](https://en.wikipedia.org/wiki/Gordon_Bell_Prize)
- [Interval arithmetic](https://en.wikipedia.org/wiki/Interval_arithmetic)
- [List of numerical analysis topics](https://en.wikipedia.org/wiki/List_of_numerical_analysis_topics)
- [Local linearization method](https://en.wikipedia.org/wiki/Local_linearization_method)
- [Numerical differentiation](https://en.wikipedia.org/wiki/Numerical_differentiation)
- [Numerical Recipes](https://en.wikipedia.org/wiki/Numerical_Recipes)
- [Probabilistic numerics](https://en.wikipedia.org/wiki/Probabilistic_numerics)
- [Symbolic-numeric computation](https://en.wikipedia.org/wiki/Symbolic-numeric_computation)
- [Validated numerics](https://en.wikipedia.org/wiki/Validated_numerics)

## Notes

## References

### Citations

1.  ["Photograph, illustration, and description of the root(2) tablet from the Yale Babylonian Collection"](https://web.archive.org/web/20120813054036/http://it.stlawu.edu/%7Edmelvill/mesomath/tablets/YBC7289.html). Archived from [the original](http://it.stlawu.edu/%7Edmelvill/mesomath/tablets/YBC7289.html) on 13 August 2012. Retrieved 2 October 2006.
2.  Trefethen, Lloyd N. ["The Definition of Numerical Analysis"](https://worrydream.com/refs/Trefethen_1992_-_The_Definition_of_Numerical_Analysis.pdf) (PDF). *Bulletin of the Institute for Mathematics and Applications*.
3.  Demmel, James W. (1997). *Applied Numerical Linear Algebra*. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/1.9781611971446](https://doi.org/10.1137%2F1.9781611971446). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-89871-389-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-89871-389-3).<sup>\[*[page needed](https://en.wikipedia.org/wiki/Wikipedia:Citing_sources)*\]</sup>
4.  Ciarlet, P.G.; Miara, B.; Thomas, J.M. (1989). *Introduction to numerical linear algebra and optimization*. Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-32788-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-32788-6). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [877155729](https://search.worldcat.org/oclc/877155729).<sup>\[*[page needed](https://en.wikipedia.org/wiki/Wikipedia:Citing_sources)*\]</sup>
5.  Trefethen, Lloyd; Bau III, David (1997). [Numerical Linear Algebra](https://books.google.com/books?id=4Mou5YpRD_kC&pg=PR7). SIAM. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-89871-361-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-89871-361-9).
6.  ^    Brezinski, C.; Wuytack, L. (2012). [Numerical analysis: Historical developments in the 20th century](https://books.google.com/books?id=dt3Z1yu2VxwC&pg=PP6). Elsevier. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-444-59858-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-444-59858-5).
7.  Stephen Blyth. ["An Introduction to Quantitative Finance"](https://books.google.com/books?id=SXbcAAAAQBAJ). 2013. page VII.
8.  ^    Watson, G.A. (2010). ["The history and development of numerical analysis in Scotland: a personal perspective"](https://core.ac.uk/download/pdf/206717434.pdf) (PDF). *The Birth of Numerical Analysis*. World Scientific. pp. 161–177. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9789814469456](https://en.wikipedia.org/wiki/Special:BookSources/9789814469456).
9.  [Bultheel, Adhemar](https://en.wikipedia.org/wiki/Adhemar_Bultheel); Cools, Ronald, eds. (2010). [The Birth of Numerical Analysis](https://books.google.com/books?id=pKZpDQAAQBAJ&pg=PR17). Vol. 10. World Scientific. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-981-283-625-0](https://en.wikipedia.org/wiki/Special:BookSources/978-981-283-625-0).
10. Saad, Y. (2003). [Iterative methods for sparse linear systems](https://books.google.com/books?id=qtzmkzzqFmcC&pg=PR5). SIAM. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-89871-534-7](https://en.wikipedia.org/wiki/Special:BookSources/978-0-89871-534-7).
11. Hageman, L.A.; Young, D.M. (2012). [Applied iterative methods](https://books.google.com/books?id=se3YdgFgz4YC&pg=PR4) (2nd ed.). Courier Corporation. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8284-0312-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8284-0312-2).
12. Traub, J.F. (1982). [Iterative methods for the solution of equations](https://books.google.com/books?id=se3YdgFgz4YC&pg=PR4) (2nd ed.). American Mathematical Society. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8284-0312-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8284-0312-2). 
13. Greenbaum, A. (1997). [Iterative methods for solving linear systems](https://books.google.com/books?id=QpVpvE4gWZwC&pg=PP6). SIAM. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-89871-396-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-89871-396-1).
14. ^    
15. Brezinski, C.; Zaglia, M.R. (2013). [Extrapolation methods: theory and practice](https://books.google.com/books?id=WGviBQAAQBAJ&pg=PR7). Elsevier. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-08-050622-7](https://en.wikipedia.org/wiki/Special:BookSources/978-0-08-050622-7).
16. Hestenes, Magnus R.; Stiefel, Eduard (December 1952). ["Methods of Conjugate Gradients for Solving Linear Systems"](https://nvlpubs.nist.gov/nistpubs/jres/049/jresv49n6p409_A1b.pdf) (PDF). *Journal of Research of the National Bureau of Standards*. **49** (6): 409–. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.6028/jres.049.044](https://doi.org/10.6028%2Fjres.049.044).
17. Ezquerro Fernández, J.A.; Hernández Verón, M.Á. (2017). [Newton's method: An updated approach of Kantorovich's theory](https://books.google.com/books?id=A3orDwAAQBAJ&pg=PR11). Birkhäuser. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-319-55976-6](https://en.wikipedia.org/wiki/Special:BookSources/978-3-319-55976-6).
18. Deuflhard, Peter (2006). [Newton Methods for Nonlinear Problems. Affine Invariance and Adaptive Algorithms](https://books.google.com/books?id=l20xK__HG_kC&pg=PP1). Computational Mathematics. Vol. 35 (2nd ed.). Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-21099-3](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-21099-3).
19. Ogden, C.J.; Huff, T. (1997). ["The Singular Value Decomposition and Its Applications in Image Compression"](https://web.archive.org/web/20060925193348/http://online.redwoods.cc.ca.us/instruct/darnold/laproj/Fall97/Tammie/tammie.pdf) (PDF). *Math 45*. College of the Redwoods. Archived from [the original](http://online.redwoods.cc.ca.us/instruct/darnold/laproj/Fall97/Tammie/tammie.pdf) (PDF) on 25 September 2006.
20. Davis, P.J.; Rabinowitz, P. (2007). [Methods of numerical integration](https://books.google.com/books?id=gGCKdqka0HAC&pg=PR5). Courier Corporation. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-486-45339-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-486-45339-2).
21. Weisstein, Eric W. ["Gaussian Quadrature"](https://mathworld.wolfram.com/GaussianQuadrature.html). *[MathWorld](https://en.wikipedia.org/wiki/MathWorld)*.
22. Geweke, John (1996). ["15. Monte carlo simulation and numerical integration"](https://www.sciencedirect.com/science/article/pii/S1574002196010179)). *Handbook of Computational Economics*. Vol. 1. Elsevier. pp. 731–800. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/S1574-0021(96)01017-9](https://doi.org/10.1016%2FS1574-0021%2896%2901017-9). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780444898579](https://en.wikipedia.org/wiki/Special:BookSources/9780444898579).
23. Iserles, A. (2009). [A first course in the numerical analysis of differential equations](https://books.google.com/books?id=M0tkw4oUucoC&pg=PR5) (2nd ed.). Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-73490-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-73490-5).
24. Ames, W.F. (2014). [Numerical methods for partial differential equations](https://books.google.com/books?id=KmjiBQAAQBAJ&pg=PP7) (3rd ed.). Academic Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-08-057130-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-08-057130-0).
25. Johnson, C. (2012). [Numerical solution of partial differential equations by the finite element method](https://books.google.com/books?id=0IFCAwAAQBAJ&pg=PA2). Courier Corporation. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-486-46900-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-486-46900-3).
26. Brenner, S.; Scott, R. (2013). [The mathematical theory of finite element methods](https://books.google.com/books?id=ServBwAAQBAJ&pg=PR11) (2nd ed.). Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4757-3658-8](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4757-3658-8).
27. Strang, G.; Fix, G.J. (2018) \[1973\]. [An analysis of the finite element method](https://archive.org/details/analysisoffinite0000stra) (2nd ed.). Wellesley-Cambridge Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780980232783](https://en.wikipedia.org/wiki/Special:BookSources/9780980232783). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [1145780513](https://search.worldcat.org/oclc/1145780513).
28. Strikwerda, J.C. (2004). [Finite difference schemes and partial differential equations](https://books.google.com/books?id=mbdt5XT25AsC&pg=PP5) (2nd ed.). SIAM. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-89871-793-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-89871-793-8).
29. LeVeque, Randall (2002). [Finite Volume Methods for Hyperbolic Problems](https://books.google.com/books?id=mfAfAwAAQBAJ&pg=PT6). Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-139-43418-8](https://en.wikipedia.org/wiki/Special:BookSources/978-1-139-43418-8).
30. Quarteroni, A.; Saleri, F.; Gervasio, P. (2014). [Scientific computing with MATLAB and Octave](https://books.google.com/books?id=_0m9BAAAQBAJ&pg=PR11) (4th ed.). Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-642-45367-0](https://en.wikipedia.org/wiki/Special:BookSources/978-3-642-45367-0).
31. Gander, W.; Hrebicek, J., eds. (2011). [Solving problems in scientific computing using Maple and Matlab®](https://books.google.com/books?id=di2qCAAAQBAJ&pg=PR14). Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-642-18873-2](https://en.wikipedia.org/wiki/Special:BookSources/978-3-642-18873-2).
32. Barnes, B.; Fulford, G.R. (2011). *Mathematical modelling with case studies: a differential equations approach using Maple and MATLAB* (2nd ed.). CRC Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4200-8350-7](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4200-8350-7). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [1058138488](https://search.worldcat.org/oclc/1058138488).
33. Gumley, L.E. (2001). [Practical IDL programming](https://books.google.com/books?id=1d-tNpm_x4gC&pg=PR9). Elsevier. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-08-051444-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-08-051444-4).
34. Bunks, C.; Chancelier, J.P.; Delebecque, F.; Goursat, M.; Nikoukhah, R.; Steer, S. (2012). *Engineering and scientific computing with Scilab*. Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4612-7204-5](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4612-7204-5).
35. Thanki, R.M.; Kothari, A.M. (2019). [Digital image processing using SCILAB](https://books.google.com/books?id=VydaDwAAQBAJ&pg=PR9). Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-319-89533-8](https://en.wikipedia.org/wiki/Special:BookSources/978-3-319-89533-8).
36. Ihaka, R.; Gentleman, R. (1996). ["R: a language for data analysis and graphics"](https://www.stat.auckland.ac.nz/~ihaka/downloads/R-paper.pdf) (PDF). *Journal of Computational and Graphical Statistics*. **5** (3): 299–314. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/10618600.1996.10474713](https://doi.org/10.1080%2F10618600.1996.10474713). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [60206680](https://api.semanticscholar.org/CorpusID:60206680).
37. Bezanson, Jeff; Edelman, Alan; Karpinski, Stefan; Shah, Viral B. (1 January 2017). ["Julia: A Fresh Approach to Numerical Computing"](https://epubs.siam.org/doi/abs/10.1137/141000671). *SIAM Review*. **59** (1): 65–98. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1411.1607](https://arxiv.org/abs/1411.1607). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/141000671](https://doi.org/10.1137%2F141000671). [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[1721.1/110125](https://hdl.handle.net/1721.1%2F110125). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0036-1445](https://search.worldcat.org/issn/0036-1445). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [13026838](https://api.semanticscholar.org/CorpusID:13026838).
38. Jones, E., Oliphant, T., & Peterson, P. (2001). SciPy: Open source scientific tools for Python.
39. Bressert, E. (2012). *SciPy and NumPy: an overview for developers*. O'Reilly. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9781306810395](https://en.wikipedia.org/wiki/Special:BookSources/9781306810395).
40. Blanco-Silva, F.J. (2013). *Learning SciPy for numerical and scientific computing*. Packt. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9781782161639](https://en.wikipedia.org/wiki/Special:BookSources/9781782161639).
41. [Speed comparison of various number crunching packages](http://www.sciviews.org/benchmark/) [Archived](https://web.archive.org/web/20061005024002/http://www.sciviews.org/benchmark/) 5 October 2006 at the [Wayback Machine](https://en.wikipedia.org/wiki/Wayback_Machine)
42. [Comparison of mathematical programs for data analysis](http://www.scientificweb.com/ncrunch/ncrunch5.pdf) [Archived](http://arquivo.pt/wayback/20160518062220/http://www.scientificweb.com/ncrunch/ncrunch5.pdf) 18 May 2016 at the Portuguese Web Archive Stefan Steinhaus, ScientificWeb.com
43. Maeder, R.E. (1997). [Programming in mathematica](https://archive.org/details/programminginmat0000maed_l2m6) (3rd ed.). Addison-Wesley. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780201854497](https://en.wikipedia.org/wiki/Special:BookSources/9780201854497). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [1311056676](https://search.worldcat.org/oclc/1311056676).
44. Wolfram, Stephen (1999). [The MATHEMATICA® book, version 4](https://books.google.com/books?id=Xny77v_QPkEC&pg=PR19). [Cambridge University Press](https://en.wikipedia.org/wiki/Cambridge_University_Press). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-57955-004-2](https://en.wikipedia.org/wiki/Special:BookSources/978-1-57955-004-2).
45. Shaw, William T.; Tigg, Jason (1994). *Applied Mathematica: Getting Started, Getting it Done*. Addison-Wesley Publishing Company. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-201-54217-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-201-54217-2).<sup>\[*[page needed](https://en.wikipedia.org/wiki/Wikipedia:Citing_sources)*\]</sup>
46. Marasco, A.; Romano, A. (2001). [Scientific Computing with Mathematica: Mathematical Problems for Ordinary Differential Equations](https://books.google.com/books?id=iFRqemnmMqUC&pg=PR7). Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8176-4205-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8176-4205-1).

### Sources

- [Golub, Gene H.](https://en.wikipedia.org/wiki/Gene_H._Golub); [Charles F. Van Loan](https://en.wikipedia.org/wiki/Charles_F._Van_Loan) (1986). *Matrix Computations* (3rd ed.). Johns Hopkins University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-8018-5413-X](https://en.wikipedia.org/wiki/Special:BookSources/0-8018-5413-X).
- Ralston Anthony; Rabinowitz Philips (2001). *A First Course in Numerical Analysis* (2nd ed.). Dover publications. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0486414546](https://en.wikipedia.org/wiki/Special:BookSources/978-0486414546).
- [Higham, Nicholas J.](https://en.wikipedia.org/wiki/Nicholas_Higham) (2002) \[1996\]. [Accuracy and Stability of Numerical Algorithms](https://archive.org/details/accuracystabilit0000high). Society for Industrial and Applied Mathematics. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-89871-355-2](https://en.wikipedia.org/wiki/Special:BookSources/0-89871-355-2).
- [Hildebrand, F. B.](https://en.wikipedia.org/wiki/Francis_B._Hildebrand) (1974). *Introduction to Numerical Analysis* (2nd ed.). McGraw-Hill. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-07-028761-9](https://en.wikipedia.org/wiki/Special:BookSources/0-07-028761-9).
- David Kincaid and Ward Cheney: *Numerical Analysis : Mathematics of Scientific Computing*, 3rd Ed., AMS, ISBN 978-0-8218-4788-6 (2002).
- [Leader, Jeffery J.](https://en.wikipedia.org/wiki/Jeffery_J._Leader) (2004). *Numerical Analysis and Scientific Computation*. Addison Wesley. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-201-73499-0](https://en.wikipedia.org/wiki/Special:BookSources/0-201-73499-0).
- [Wilkinson, J.H.](https://en.wikipedia.org/wiki/James_H._Wilkinson) (1988) \[1965\]. [The Algebraic Eigenvalue Problem](https://archive.org/details/algebraiceigenva0000wilk). Clarendon Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-19-853418-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-19-853418-1).
- [Kahan, W.](https://en.wikipedia.org/wiki/William_Kahan) (1972). *A survey of error-analysis*. Proc. IFIP Congress 71 in Ljubljana. *Info. Processing 71*. Vol. 2. North-Holland. pp. 1214–39. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-7204-2063-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-7204-2063-0). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [25116949](https://search.worldcat.org/oclc/25116949). (examples of the importance of accurate arithmetic).
- [Trefethen, Lloyd N.](https://en.wikipedia.org/wiki/Lloyd_N._Trefethen) (2008). ["IV.21 Numerical analysis"](http://people.maths.ox.ac.uk/trefethen/NAessay.pdf) (PDF). In Leader, I.; Gowers, T.; Barrow-Green, J. (eds.). [Princeton Companion of Mathematics](https://books.google.com/books?id=GLumDwAAQBAJ&pg=PR5). Princeton University Press. pp. 604–614. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-691-11880-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-691-11880-2).

## External links

### Journals

- *[Numerische Mathematik](https://en.wikipedia.org/wiki/Numerische_Mathematik)*, volumes 1–..., [Springer](https://www.springer.com/mathematics/numerical+and+computational+mathematics/journal/211), 1959–
  - [volumes 1–66, 1959–1994](http://www-gdz.sub.uni-goettingen.de/cgi-bin/digbib.cgi?PPN362160546) (searchable; pages are images). (in English and German)

### Online texts

- ["Numerical analysis"](https://www.encyclopediaofmath.org/), *[Encyclopedia of Mathematics](https://en.wikipedia.org/wiki/Encyclopedia_of_Mathematics)*, [EMS Press](https://en.wikipedia.org/wiki/European_Mathematical_Society), 2001 \[1994\]
- [Numerical Recipes](https://web.archive.org/web/20150905141405/http://www.nr.com/oldverswitcher.html), William H. Press (free, downloadable previous editions)
- [First Steps in Numerical Analysis](https://web.archive.org/web/20120225082123/http://kr.cs.ait.ac.th/~radok/math/mat7/stepsa.htm) ([archived](https://en.wikipedia.org/wiki/Internet_Archive)), R.J.Hosking, S.Joe, D.C.Joyce, and J.C.Turner
- [CSEP (Computational Science Education Project)](https://web.archive.org/web/20170801213333/http://www.phy.ornl.gov/csep/CSEP/TEXTOC.html), [U.S. Department of Energy](https://en.wikipedia.org/wiki/U.S._Department_of_Energy) ([archived 2017-08-01](https://en.wikipedia.org/wiki/Internet_Archive))
- [Numerical Methods](https://dlmf.nist.gov/3), ch 3. in the *[Digital Library of Mathematical Functions](https://en.wikipedia.org/wiki/Digital_Library_of_Mathematical_Functions)*
- [Numerical Interpolation, Differentiation and Integration](https://personal.math.ubc.ca/~cbm/aands/page_875.htm), ch 25. in the *Handbook of Mathematical Functions* ([Abramowitz and Stegun](https://en.wikipedia.org/wiki/Abramowitz_and_Stegun))
- [Tobin A. Driscoll and Richard J. Braun: Fundamentals of Numerical Computation (free online version)](https://fncbook.com/)

### Online course material

- [Numerical Methods](http://www.damtp.cam.ac.uk/user/fdl/people/sd103/lectures/nummeth98/index.htm#L_1_Title_Page) ([Archived](https://web.archive.org/web/20090728181209/http://www.damtp.cam.ac.uk/user/fdl/people/sd103/lectures/nummeth98/index.htm#L_1_Title_Page) 28 July 2009 at the [Wayback Machine](https://en.wikipedia.org/wiki/Wayback_Machine)), Stuart Dalziel [University of Cambridge](https://en.wikipedia.org/wiki/University_of_Cambridge)
- [Lectures on Numerical Analysis](http://www.math.upenn.edu/~wilf/DeturckWilf.pdf), Dennis Deturck and Herbert S. Wilf [University of Pennsylvania](https://en.wikipedia.org/wiki/University_of_Pennsylvania)
- [Numerical methods](http://johndfenton.com/Lectures/Numerical-Methods/Numerical-Methods.pdf), John D. Fenton [University of Karlsruhe](https://en.wikipedia.org/wiki/University_of_Karlsruhe)
- [Numerical Methods for Physicists](http://www-teaching.physics.ox.ac.uk/computing/NumericalMethods/NMfP.pdf), Anthony O’Hare [Oxford University](https://en.wikipedia.org/wiki/Oxford_University)
- [Lectures in Numerical Analysis](https://web.archive.org/web/20120225082123/http://kr.cs.ait.ac.th/~radok/math/mat7/stepsa.htm) ([archived](https://en.wikipedia.org/wiki/Internet_Archive)), R. Radok [Mahidol University](https://en.wikipedia.org/wiki/Mahidol_University)
- [Introduction to Numerical Analysis for Engineering](http://ocw.mit.edu/courses/mechanical-engineering/2-993j-introduction-to-numerical-analysis-for-engineering-13-002j-spring-2005/), Henrik Schmidt [Massachusetts Institute of Technology](https://en.wikipedia.org/wiki/Massachusetts_Institute_of_Technology)
- [Numerical Analysis for Engineering](http://ece.uwaterloo.ca/~dwharder/NumericalAnalysis/), D. W. Harder [University of Waterloo](https://en.wikipedia.org/wiki/University_of_Waterloo)
- [Introduction to Numerical Analysis](https://www.math.umd.edu/~diom/courses/AMSC466/Levy-notes.pdf), Doron Levy [University of Maryland](https://en.wikipedia.org/wiki/University_of_Maryland)
- [Numerical Analysis - Numerical Methods](https://web.archive.org/web/20070310212643/http://math.fullerton.edu/mathews/n2003/NumericalUndergradMod.html) (archived), John H. Mathews [California State University Fullerton](https://en.wikipedia.org/wiki/California_State_University_Fullerton)
