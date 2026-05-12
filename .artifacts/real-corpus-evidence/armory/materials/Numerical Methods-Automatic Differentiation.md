[[numerical-methods.base]]

> Source: [[Automatic Differentiation]]
> License: Wikipedia content is available under CC BY-SA 4.0.

In [mathematics](https://en.wikipedia.org/wiki/Mathematics) and [computer algebra](https://en.wikipedia.org/wiki/Computer_algebra), **automatic differentiation** (**auto-differentiation**, **autodiff**, or **AD**), also called **algorithmic differentiation**, **computational differentiation**, and **differentiation arithmetic** is a set of techniques to evaluate the [partial derivative](https://en.wikipedia.org/wiki/Partial_derivative) of a function specified by a computer program. Automatic differentiation is a subtle and central tool to automatize the simultaneous computation of the numerical values of arbitrarily complex functions and their derivatives with no need for the symbolic representation of the derivative; only the function rule or an algorithm thereof is required. Auto-differentiation is thus neither numeric nor symbolic, nor is it a combination of both. It is also preferable to ordinary numerical methods: In contrast to the more traditional numerical methods based on finite differences, auto-differentiation is 'in theory' exact, and in comparison to symbolic algorithms, it is computationally inexpensive.

Automatic differentiation exploits the fact that every computer calculation, no matter how complicated, executes a sequence of elementary arithmetic operations (addition, subtraction, multiplication, division, etc.) and [elementary functions](https://en.wikipedia.org/wiki/Elementary_function) ([exp](https://en.wikipedia.org/wiki/Exponential_function), [log](https://en.wikipedia.org/wiki/Natural_logarithm), [sin](https://en.wikipedia.org/wiki/Sine), [cos](https://en.wikipedia.org/wiki/Cosine), etc.). By applying the [[Chain Rule]] repeatedly to these operations, partial derivatives of arbitrary order can be computed automatically, accurately to working precision, and using at most a small constant factor of more arithmetic operations than the original program.

## Difference from other differentiation methods

![[media/aa25b43df316a1109dce21f0efcca1caba0c6884.png]]
Figure 1: How automatic differentiation relates to symbolic differentiation

Automatic differentiation is distinct from [symbolic differentiation](https://en.wikipedia.org/wiki/Symbolic_differentiation) and [numerical differentiation](https://en.wikipedia.org/wiki/Numerical_differentiation). Symbolic differentiation faces the difficulty of converting a computer program into a single [mathematical expression](https://en.wikipedia.org/wiki/Mathematical_expression) and can lead to inefficient code. Numerical differentiation (the method of finite differences) can introduce [round-off errors](https://en.wikipedia.org/wiki/Round-off_error) in the [discretization](https://en.wikipedia.org/wiki/Discretization) process and cancellation. Both of these classical methods have problems with calculating higher derivatives, where complexity and errors increase. Finally, both of these classical methods are slow at computing partial derivatives of a function with respect to *many* inputs, as is needed for [[Gradient Descent|gradient]]-based [optimization](https://en.wikipedia.org/wiki/Optimization_(mathematics)) algorithms. Automatic differentiation solves all of these problems.

## Applications

Currently, for its efficiency and accuracy in computing first and higher order [derivatives](https://en.wikipedia.org/wiki/Derivative), auto-differentiation is a celebrated technique with diverse applications in [scientific computing](https://en.wikipedia.org/wiki/Scientific_computing) and [mathematics](https://en.wikipedia.org/wiki/Mathematics). It should therefore come as no surprise that there are numerous computational implementations of auto-differentiation. Among these, one mentions [INTLAB](https://en.wikipedia.org/wiki/INTLAB), Sollya, and InCLosure. In practice, there are two types (modes) of algorithmic differentiation: a forward-type and a reversed-type. Presently, the two types are highly correlated and complementary and both have a wide variety of applications in, e.g., non-linear [optimization](https://en.wikipedia.org/wiki/Optimization), [sensitivity analysis](https://en.wikipedia.org/wiki/Sensitivity_analysis), [robotics](https://en.wikipedia.org/wiki/Robotics), [machine learning](https://en.wikipedia.org/wiki/Machine_learning), [computer graphics](https://en.wikipedia.org/wiki/Computer_graphics), and [computer vision](https://en.wikipedia.org/wiki/Computer_vision). Automatic differentiation is particularly important in the field of [machine learning](https://en.wikipedia.org/wiki/Machine_learning). For example, it allows one to implement [backpropagation](https://en.wikipedia.org/wiki/Backpropagation) in a [neural network](https://en.wikipedia.org/wiki/Neural_network_(machine_learning) "Neural network (machine learning)") without a manually-computed derivative.

## Forward and reverse accumulation

### Chain rule of partial derivatives of composite functions

Fundamental to automatic differentiation is the decomposition of differentials provided by the [[Chain Rule]] of [partial derivatives](https://en.wikipedia.org/wiki/Partial_derivative) of [composite functions](https://en.wikipedia.org/wiki/Function_composition). For the simple composition 

$$
{\begin{aligned}y&=f(g(h(x)))=f(g(h(w_{0})))=f(g(w_{1}))=f(w_{2})=w_{3}\\w_{0}&=x\\w_{1}&=h(w_{0})\\w_{2}&=g(w_{1})\\w_{3}&=f(w_{2})=y\end{aligned}}
$$

 the chain rule gives 

$$
{\frac {\partial y}{\partial x}}={\frac {\partial y}{\partial w_{2}}}{\frac {\partial w_{2}}{\partial w_{1}}}{\frac {\partial w_{1}}{\partial x}}={\frac {\partial f(w_{2})}{\partial w_{2}}}{\frac {\partial g(w_{1})}{\partial w_{1}}}{\frac {\partial h(w_{0})}{\partial x}}
$$

### Two types of automatic differentiation

Usually, two distinct modes of automatic differentiation are presented.

- **forward accumulation** (also called **bottom-up**, **forward mode**, or **tangent mode**)
- **reverse accumulation** (also called **top-down**, **reverse mode**, or **adjoint mode**)

Forward accumulation specifies that one traverses the chain rule from inside to outside (that is, first compute ${\frac {\partial w_{1}}{\partial x}}$ and then ${\frac {\partial w_{2}}{\partial w_{1}}}$ and lastly ${\frac {\partial y}{\partial w_{2}}}$), while reverse accumulation traverses from outside to inside (first compute ${\frac {\partial y}{\partial w_{2}}}$ and then ${\frac {\partial w_{2}}{\partial w_{1}}}$ and lastly ${\frac {\partial w_{1}}{\partial x}}$). More succinctly,

- Forward accumulation computes the recursive relation: 

$$
{\frac {\partial w_{i}}{\partial x}}={\frac {\partial w_{i}}{\partial w_{i-1}}}{\frac {\partial w_{i-1}}{\partial x}}\quad {\text{with }}w_{3}=y,
$$

- Reverse accumulation computes the recursive relation: 

$$
{\frac {\partial y}{\partial w_{i}}}={\frac {\partial y}{\partial w_{i+1}}}{\frac {\partial w_{i+1}}{\partial w_{i}}}\quad {\text{with }}w_{0}=x.
$$

The value of the partial derivative, called the *seed*, is propagated forward or backward and is initially ${\frac {\partial x}{\partial x}}=1$ or ${\frac {\partial y}{\partial y}}=1$. Forward accumulation evaluates the function and calculates the derivative with respect to one independent variable in one pass. For each independent variable $x_{1},x_{2},\dots ,x_{n}$ a separate pass is therefore necessary in which the derivative with respect to that independent variable is set to one (${\frac {\partial x_{1}}{\partial x_{1}}}=1$) and of all others to zero (${\frac {\partial x_{2}}{\partial x_{1}}}=\dots ={\frac {\partial x_{n}}{\partial x_{1}}}=0$). In contrast, reverse accumulation requires the evaluated partial functions for the partial derivatives. Reverse accumulation therefore evaluates the function first and calculates the derivatives with respect to all independent variables in an additional pass.

Which of these two types should be used depends on the sweep count. The [computational complexity](https://en.wikipedia.org/wiki/Computational_complexity_theory) of one sweep is proportional to the complexity of the original code.

- Forward accumulation is more efficient than reverse accumulation for functions *f* : ℝ<sup>*n*</sup> → ℝ<sup>*m*</sup> with *n* ≪ *m* as only *n* sweeps are necessary, compared to *m* sweeps for reverse accumulation.
- Reverse accumulation is more efficient than forward accumulation for functions *f* : ℝ<sup>*n*</sup> → ℝ<sup>*m*</sup> with *n* ≫ *m* as only *m* sweeps are necessary, compared to *n* sweeps for forward accumulation.

[Backpropagation](https://en.wikipedia.org/wiki/Backpropagation) of errors in multilayer perceptrons, a technique used in [machine learning](https://en.wikipedia.org/wiki/Machine_learning), is a special case of reverse accumulation.

Forward accumulation was introduced by R. E. Wengert in 1964. According to Andreas Griewank, reverse accumulation has been suggested since the late 1960s, but the inventor is unknown. [Seppo Linnainmaa](https://en.wikipedia.org/wiki/Seppo_Linnainmaa) published reverse accumulation in 1976.

### Forward accumulation

![[media/5fb7f015483f2d7c19df8503bf947b9ef3a37e40.png]]
Forward accumulation

In forward accumulation AD, one first fixes the *independent variable* with respect to which differentiation is performed and computes the derivative of each sub-[expression](https://en.wikipedia.org/wiki/Expression_(mathematics) "Expression (mathematics)") recursively. In a pen-and-paper calculation, this involves repeatedly substituting the derivative of the *inner* functions in the chain rule: 

$$
{\begin{aligned}{\frac {\partial y}{\partial x}}&={\frac {\partial y}{\partial w_{n-1}}}{\frac {\partial w_{n-1}}{\partial x}}\\[6pt]&={\frac {\partial y}{\partial w_{n-1}}}\left({\frac {\partial w_{n-1}}{\partial w_{n-2}}}{\frac {\partial w_{n-2}}{\partial x}}\right)\\[6pt]&={\frac {\partial y}{\partial w_{n-1}}}\left({\frac {\partial w_{n-1}}{\partial w_{n-2}}}\left({\frac {\partial w_{n-2}}{\partial w_{n-3}}}{\frac {\partial w_{n-3}}{\partial x}}\right)\right)\\[6pt]&=\cdots \end{aligned}}
$$

 This can be generalized to multiple variables as a matrix product of [Jacobians](https://en.wikipedia.org/wiki/Jacobian_matrix_and_determinant).

Compared to reverse accumulation, forward accumulation is natural and easy to implement as the flow of derivative information coincides with the order of evaluation. Each variable $w_{i}$ is augmented with its derivative ${\dot {w}}_{i}$ (stored as a numerical value, not a symbolic expression), 

$$
{\dot {w}}_{i}={\frac {\partial w_{i}}{\partial x}}
$$

 as denoted by the dot. The derivatives are then computed in sync with the evaluation steps and combined with other derivatives via the chain rule.

Using the chain rule, if $w_{i}$ has predecessors in the computational graph: 

$$
{\dot {w}}_{i}=\sum _{j\in \{{\text{predecessors of }}i\}}{\frac {\partial w_{i}}{\partial w_{j}}}{\dot {w}}_{j}
$$

![[media/b72ee99fbaf6b2f35d4d2db5f283ffe39322e92c.png]]
Figure 2: Example of forward accumulation with computational graph

As an example, consider the function: 

$$
{\begin{aligned}y&=f(x_{1},x_{2})\\&=x_{1}x_{2}+\sin x_{1}\\&=w_{1}w_{2}+\sin w_{1}\\&=w_{3}+w_{4}\\&=w_{5}\end{aligned}}
$$

 For clarity, the individual sub-expressions have been labeled with the variables $w_{i}$.

The choice of the independent variable to which differentiation is performed affects the *seed* values *ẇ*<sub>1</sub> and *ẇ*<sub>2</sub>. Given interest in the derivative of this function with respect to *x*<sub>1</sub>, the seed values should be set to: 

$$
{\begin{aligned}{\dot {w}}_{1}={\frac {\partial w_{1}}{\partial x_{1}}}={\frac {\partial x_{1}}{\partial x_{1}}}=1\\{\dot {w}}_{2}={\frac {\partial w_{2}}{\partial x_{1}}}={\frac {\partial x_{2}}{\partial x_{1}}}=0\end{aligned}}
$$

With the seed values set, the values propagate using the chain rule as shown. Figure 2 shows a pictorial depiction of this process as a computational graph.

|  |  |
|----|----|
| Operations to compute value | Operations to compute derivative |
| $w_{1}=x_{1}$ | ${\dot {w}}_{1}=1$ (seed) |
| $w_{2}=x_{2}$ | ${\dot {w}}_{2}=0$ (seed) |
| $w_{3}=w_{1}\cdot w_{2}$ | ${\dot {w}}_{3}=w_{2}\cdot {\dot {w}}_{1}+w_{1}\cdot {\dot {w}}_{2}$ |
| $w_{4}=\sin w_{1}$ | ${\dot {w}}_{4}=\cos w_{1}\cdot {\dot {w}}_{1}$ |
| $w_{5}=w_{3}+w_{4}$ | ${\dot {w}}_{5}={\dot {w}}_{3}+{\dot {w}}_{4}$ |

To compute the [gradient](https://en.wikipedia.org/wiki/Gradient) of this example function, which requires not only ${\frac {\partial y}{\partial x_{1}}}$ but also ${\frac {\partial y}{\partial x_{2}}}$, an *additional* sweep is performed over the computational graph using the seed values ${\dot {w}}_{1}=0$; ${\dot {w}}_{2}=1$.

#### Implementation

##### Pseudocode

Forward accumulation calculates the function and the derivative (but only for one independent variable each) in one pass. The associated method call expects the expression Z to be derived with regard to a variable V. The method returns a pair of the evaluated function and its derivative. The method traverses the expression tree recursively until a variable is reached. If the derivative with respect to this variable is requested, its derivative is 1, 0 otherwise. Then the partial function as well as the partial derivative are evaluated.

    tuple<float,float> evaluateAndDerive(Expression Z, Variable V) {
       if isVariable(Z)
          if (Z = V) return {valueOf(Z), 1};
          else return {valueOf(Z), 0};
       else if (Z = A + B)
          {a, a'} = evaluateAndDerive(A, V);
          {b, b'} = evaluateAndDerive(B, V);
          return {a + b, a' + b'};
       else if (Z = A - B)
          {a, a'} = evaluateAndDerive(A, V);
          {b, b'} = evaluateAndDerive(B, V);
          return {a - b, a' - b'};
       else if (Z = A * B)
          {a, a'} = evaluateAndDerive(A, V);
          {b, b'} = evaluateAndDerive(B, V);
          return {a * b, b * a' + a * b'};
    }

##### C++

    #include <iostream>
    struct ValueAndPartial { float value, partial; };
    struct Variable;
    struct Expression {
       virtual ValueAndPartial evaluateAndDerive(Variable &variable) = 0;
    };
    struct Variable: public Expression {
       float value;
       Variable(float value): value(value) {}
       ValueAndPartial evaluateAndDerive(Variable &variable) {
          float partial = (this == &variable) ? 1.0f : 0.0f;
          return {value, partial};
       }
    };
    struct Plus: public Expression {
       Expression &a, &b;
       Plus(Expression &a, Expression &b): a(a), b(b) {}
       ValueAndPartial evaluateAndDerive(Variable &variable) {
          auto [valueA, partialA] = a.evaluateAndDerive(variable);
          auto [valueB, partialB] = b.evaluateAndDerive(variable);
          return {valueA + valueB, partialA + partialB};
       }
    };
    struct Multiply: public Expression {
       Expression &a, &b;
       Multiply(Expression &a, Expression &b): a(a), b(b) {}
       ValueAndPartial evaluateAndDerive(Variable &variable) {
          auto [valueA, partialA] = a.evaluateAndDerive(variable);
          auto [valueB, partialB] = b.evaluateAndDerive(variable);
          return {valueA * valueB, valueB * partialA + valueA * partialB};
       }
    };
    int main () {
       // Example: Finding the partials of z = x * (x + y) + y * y at (x, y) = (2, 3)
       Variable x(2), y(3);
       Plus p1(x, y); Multiply m1(x, p1); Multiply m2(y, y); Plus z(m1, m2);
       float xPartial = z.evaluateAndDerive(x).partial;
       float yPartial = z.evaluateAndDerive(y).partial;
       std::cout << "∂z/∂x = " << xPartial << ", "
                 << "∂z/∂y = " << yPartial << std::endl;
       // Output: ∂z/∂x = 7, ∂z/∂y = 8
       return 0;
    }

### Reverse accumulation

![[media/539201340bb3a679631a63d842aca70376570dab.png]]
Reverse accumulation

In reverse accumulation AD, the *dependent variable* to be differentiated is fixed and the derivative is computed *with respect to* each sub-[expression](https://en.wikipedia.org/wiki/Expression_(mathematics) "Expression (mathematics)") recursively. In a pen-and-paper calculation, the derivative of the *outer* functions is repeatedly substituted in the chain rule: 

$$
{\begin{aligned}{\frac {\partial y}{\partial x}}&={\frac {\partial y}{\partial w_{1}}}{\frac {\partial w_{1}}{\partial x}}\\[6px]&=\left({\frac {\partial y}{\partial w_{2}}}{\frac {\partial w_{2}}{\partial w_{1}}}\right){\frac {\partial w_{1}}{\partial x}}\\[6px]&=\left(\left({\frac {\partial y}{\partial w_{3}}}{\frac {\partial w_{3}}{\partial w_{2}}}\right){\frac {\partial w_{2}}{\partial w_{1}}}\right){\frac {\partial w_{1}}{\partial x}}\\[6px]&=\cdots \end{aligned}}
$$

In reverse accumulation, the quantity of interest is the *adjoint*, denoted with a bar ${\bar {w}}_{i}$; it is a derivative of a chosen dependent variable with respect to a subexpression $w_{i}$: 

$$
{\bar {w}}_{i}={\frac {\partial y}{\partial w_{i}}}
$$

Using the chain rule, if $w_{i}$ has successors in the computational graph: 

$$
{\bar {w}}_{i}=\sum _{j\in \{{\text{successors of }}i\}}{\bar {w}}_{j}{\frac {\partial w_{j}}{\partial w_{i}}}
$$

Reverse accumulation traverses the chain rule from outside to inside, or in the case of the computational graph in Figure 3, from top to bottom. The example function is scalar-valued, and thus there is only one seed for the derivative computation, and only one sweep of the computational graph is needed to calculate the (two-component) gradient. This is only [half the work](https://en.wikipedia.org/wiki/Space%E2%80%93time_tradeoff) when compared to forward accumulation, but reverse accumulation requires the storage of the intermediate variables *w*<sub>*i*</sub> as well as the instructions that produced them in a data structure known as a "tape" or a Wengert list (however, Wengert published forward accumulation, not reverse accumulation), which may consume significant memory if the computational graph is large. This can be mitigated to some extent by storing only a subset of the intermediate variables and then reconstructing the necessary work variables by repeating the evaluations, a technique known as [rematerialization](https://en.wikipedia.org/wiki/Rematerialization). [Checkpointing](https://en.wikipedia.org/wiki/Checkpointing_scheme) is also used to save intermediary states.

![[media/0c726bdc5a5850df7895a3fb062a2415c6a9b8ec.png]]
Figure 3: Example of reverse accumulation with computational graph

The operations to compute the derivative using reverse accumulation are shown in the table below (note the reversed order):

$$
{\begin{aligned}{\bar {w}}_{5}&=1\quad {\text{(seed)}}\\{\bar {w}}_{4}&={\bar {w}}_{5}\cdot 1\\{\bar {w}}_{3}&={\bar {w}}_{5}\cdot 1\\{\bar {w}}_{2}&={\bar {w}}_{3}\cdot w_{1}\\{\bar {w}}_{1}&={\bar {w}}_{3}\cdot w_{2}+{\bar {w}}_{4}\cdot \cos w_{1}\end{aligned}}
$$

The data flow graph of a computation can be manipulated to calculate the gradient of its original calculation. This is done by adding an adjoint node for each primal node, connected by adjoint edges which parallel the primal edges but flow in the opposite direction. The nodes in the adjoint graph represent multiplication by the derivatives of the functions calculated by the nodes in the primal. For instance, addition in the primal causes fanout in the adjoint; fanout in the primal causes addition in the adjoint; a [unary](https://en.wikipedia.org/wiki/Unary_operation) function *y* = *f*(*x*) in the primal causes *x̄* = *ȳ* *f*′(*x*) in the adjoint; etc.

#### Implementation

##### Pseudocode

Reverse accumulation requires two passes: In the forward pass, the function is evaluated first and the partial results are cached. In the reverse pass, the partial derivatives are calculated and the previously derived value is back-propagated. The corresponding method call expects the expression Z to be derived and *seeded* with the derived value of the parent expression. For the top expression, Z is differentiated with respect to Z, this is 1. The method traverses the expression tree recursively until a variable is reached and adds the current *seed* value to the derivative expression.

    void derive(Expression Z, float seed) {
       if isVariable(Z)
          partialDerivativeOf(Z) += seed;
       else if (Z = A + B)
          derive(A, seed);
          derive(B, seed);
       else if (Z = A - B)
          derive(A, seed);
          derive(B, -seed);
       else if (Z = A * B)
          derive(A, valueOf(B) * seed);
          derive(B, valueOf(A) * seed);
    }

##### C++

    #include <iostream>
    struct Expression {
       float value;
       virtual void evaluate() = 0;
       virtual void derive(float seed) = 0;
    };
    struct Variable: public Expression {
       float partial;
       Variable(float value) {
          this->value = value;
          partial = 0.0f;
       }
       void evaluate() {}
       void derive(float seed) {
          partial += seed;
       }
    };
    struct Plus: public Expression {
       Expression &a, &b;
       Plus(Expression &a, Expression &b): a(a), b(b) {}
       void evaluate() {
          a.evaluate();
          b.evaluate();
          value = a.value + b.value;
       }
       void derive(float seed) {
          a.derive(seed);
          b.derive(seed);
       }
    };
    struct Multiply: public Expression {
       Expression &a, &b;
       Multiply(Expression &a, Expression &b): a(a), b(b) {}
       void evaluate() {
          a.evaluate();
          b.evaluate();
          value = a.value * b.value;
       }
       void derive(float seed) {
          a.derive(b.value * seed);
          b.derive(a.value * seed);
       }
    };
    int main () {
       // Example: Finding the partials of z = x * (x + y) + y * y at (x, y) = (2, 3)
       Variable x(2), y(3);
       Plus p1(x, y); Multiply m1(x, p1); Multiply m2(y, y); Plus z(m1, m2);
       z.evaluate();
       std::cout << "z = " << z.value << std::endl;
       // Output: z = 19
       z.derive(1);
       std::cout << "∂z/∂x = " << x.partial << ", "
                 << "∂z/∂y = " << y.partial << std::endl;
       // Output: ∂z/∂x = 7, ∂z/∂y = 8
       return 0;
    }

### Beyond forward and reverse accumulation

Forward and reverse accumulation are just two (extreme) ways of traversing the chain rule. The problem of computing a full Jacobian of *f* : ℝ<sup>*n*</sup> → ℝ<sup>*m*</sup> with a minimum number of arithmetic operations is known as the *optimal Jacobian accumulation* (OJA) problem, which is [NP-complete](https://en.wikipedia.org/wiki/NP-complete). Central to this proof is the idea that algebraic dependencies may exist between the local partials that label the edges of the graph. In particular, two or more edge labels may be recognized as equal. The complexity of the problem is still open if it is assumed that all edge labels are unique and algebraically independent.

## Automatic differentiation using dual numbers

Forward mode automatic differentiation is accomplished by augmenting the [algebra](https://en.wikipedia.org/wiki/Algebra_over_a_field) of [real numbers](https://en.wikipedia.org/wiki/Real_numbers) and obtaining a new [arithmetic](https://en.wikipedia.org/wiki/Arithmetic). An additional component is added to every number to represent the derivative of a function at the number, and all arithmetic operators are extended for the augmented algebra. The augmented algebra is the algebra of [dual numbers](https://en.wikipedia.org/wiki/Dual_numbers).

Replace every number $\,x$ with the number $x+x'\varepsilon$, where $x'$ is a real number, but $\varepsilon$ is an [abstract number](https://en.wikipedia.org/wiki/Abstract_number) with the property $\varepsilon ^{2}=0$ (an [infinitesimal](https://en.wikipedia.org/wiki/Infinitesimal); see *[Smooth infinitesimal analysis](https://en.wikipedia.org/wiki/Smooth_infinitesimal_analysis)*). Using only this, regular arithmetic gives 

$$
{\begin{aligned}(x+x'\varepsilon )+(y+y'\varepsilon )&=x+y+(x'+y')\varepsilon \\[4px](x+x'\varepsilon )-(y+y'\varepsilon )&=x-y+(x'-y')\varepsilon \\[4px](x+x'\varepsilon )\cdot (y+y'\varepsilon )&=xy+xy'\varepsilon +yx'\varepsilon +x'y'\varepsilon ^{2}=xy+(xy'+yx')\varepsilon \\[8px]{\frac {x+x'\varepsilon }{y+y'\varepsilon }}&={\frac {{\frac {x}{y}}+{\frac {x'\varepsilon }{y}}}{1+{\frac {y'\varepsilon }{y}}}}=\left({\frac {x}{y}}+{\frac {x'\varepsilon }{y}}\right)\cdot \left(1-{\frac {y'\varepsilon }{y}}\right)={\frac {x}{y}}+\left({\frac {x'}{y}}-{\frac {xy'}{y^{2}}}\right)\varepsilon \end{aligned}}
$$

 using the fact that 

$$
\left(1+{\frac {y'\varepsilon }{y}}\right)\cdot \left(1-{\frac {y'\varepsilon }{y}}\right)=1.
$$

Now, [polynomials](https://en.wikipedia.org/wiki/Polynomials) can be calculated in this augmented arithmetic. If 

$$
P(x)=p_{0}+p_{1}x+p_{2}x^{2}+\cdots +p_{n}x^{n},
$$

 then 

$$
{\begin{aligned}P(x+x'\varepsilon )&=p_{0}+p_{1}(x+x'\varepsilon )+\cdots +p_{n}(x+x'\varepsilon )^{n}\\&=p_{0}+p_{1}x+\cdots +p_{n}x^{n}+p_{1}x'\varepsilon +2p_{2}xx'\varepsilon +\cdots +np_{n}x^{n-1}x'\varepsilon \\&=P(x)+P^{(1)}(x)x'\varepsilon \end{aligned}}
$$

 where $P^{(1)}$ denotes the derivative of $P$ with respect to its first argument, and $x'$, called a *seed*, can be chosen arbitrarily.

The new arithmetic consists of [ordered pairs](https://en.wikipedia.org/wiki/Ordered_pair), elements written $\langle x,x'\rangle$, with ordinary arithmetics on the first component, and first order differentiation arithmetic on the second component, as described above. Extending the above results on polynomials to [analytic functions](https://en.wikipedia.org/wiki/Analytic_functions) gives a list of the basic arithmetic and some standard functions for the new arithmetic: 

$$
{\begin{aligned}\left\langle u,u'\right\rangle +\left\langle v,v'\right\rangle &=\left\langle u+v,u'+v'\right\rangle \\[4px]\left\langle u,u'\right\rangle -\left\langle v,v'\right\rangle &=\left\langle u-v,u'-v'\right\rangle \\[4px]\left\langle u,u'\right\rangle \cdot \left\langle v,v'\right\rangle &=\left\langle uv,u'v+uv'\right\rangle \\[8px]{\frac {\left\langle u,u'\right\rangle }{\left\langle v,v'\right\rangle }}&=\left\langle {\frac {u}{v}},{\frac {u'v-uv'}{v^{2}}}\right\rangle &&(v\neq 0)\\[8px]\sin \left\langle u,u'\right\rangle &=\left\langle \sin(u),u'\cos(u)\right\rangle \\[4px]\cos \left\langle u,u'\right\rangle &=\left\langle \cos(u),-u'\sin(u)\right\rangle \\[4px]e^{\left\langle u,u'\right\rangle }&=\left\langle e^{u},u'e^{u}\right\rangle \\[8px]\log \left\langle u,u'\right\rangle &=\left\langle \log(u),{\frac {u'}{u}}\right\rangle &&(u>0)\\[8px]\left\langle u,u'\right\rangle ^{k}&=\left\langle u^{k},u'ku^{k-1}\right\rangle &&(u\neq 0)\\[8px]\left|\left\langle u,u'\right\rangle \right|&=\left\langle \left|u\right|,u'\operatorname {sgn} u\right\rangle &&(u\neq 0)\end{aligned}}
$$

 and in general for the primitive function $g$, 

$$
g(\langle u,u'\rangle ,\langle v,v'\rangle )=\langle g(u,v),g_{u}(u,v)u'+g_{v}(u,v)v'\rangle
$$

 where $g_{u}$ and $g_{v}$ are the derivatives of $g$ with respect to its first and second arguments, respectively.

When a binary basic arithmetic operation is applied to mixed arguments—the pair $\langle u,u'\rangle$ and the real number $c$—the real number is first lifted to $\langle c,0\rangle$. The derivative of a function $f:\mathbb {R} \to \mathbb {R}$ at the point $x_{0}$ is now found by calculating $f(\langle x_{0},1\rangle )$ using the above arithmetic, which gives $\langle f(x_{0}),f'(x_{0})\rangle$ as the result.

### Implementation

An example implementation based on the dual number approach follows.

#### Pseudocode

``` pre
Dual plus(Dual A, Dual B) {
  return {
    realPartOf(A) + realPartOf(B),
    infinitesimalPartOf(A) + infinitesimalPartOf(B)
  };
}
Dual minus(Dual A, Dual B) {
  return {
    realPartOf(A) - realPartOf(B),
    infinitesimalPartOf(A) - infinitesimalPartOf(B)
  };
}
Dual multiply(Dual A, Dual B) {
  return {
    realPartOf(A) * realPartOf(B),
    realPartOf(B) * infinitesimalPartOf(A) + realPartOf(A) * infinitesimalPartOf(B)
  };
}
X = {x, 0};
Y = {y, 0};
Epsilon = {0, 1};
xPartial = infinitesimalPartOf(f(X + Epsilon, Y));
yPartial = infinitesimalPartOf(f(X, Y + Epsilon));
```

#### C++

    #include <iostream>
    struct Dual {
       float realPart, infinitesimalPart;
       Dual(float realPart, float infinitesimalPart=0): realPart(realPart), infinitesimalPart(infinitesimalPart) {}
       Dual operator+(Dual other) {
          return Dual(
             realPart + other.realPart,
             infinitesimalPart + other.infinitesimalPart
          );
       }
       Dual operator*(Dual other) {
          return Dual(
             realPart * other.realPart,
             other.realPart * infinitesimalPart + realPart * other.infinitesimalPart
          );
       }
    };
    // Example: Finding the partials of z = x * (x + y) + y * y at (x, y) = (2, 3)
    Dual f(Dual x, Dual y) { return x * (x + y) + y * y; }
    int main () {
       Dual x = Dual(2);
       Dual y = Dual(3);
       Dual epsilon = Dual(0, 1);
       Dual a = f(x + epsilon, y);
       Dual b = f(x, y + epsilon);
       std::cout << "∂z/∂x = " << a.infinitesimalPart << ", "
                 << "∂z/∂y = " << b.infinitesimalPart << std::endl;
       // Output: ∂z/∂x = 7, ∂z/∂y = 8
       return 0;
    }

### Vector arguments and functions

Multivariate functions can be handled with the same efficiency and mechanisms as univariate functions by adopting a directional derivative operator. That is, if it is sufficient to compute $y'=\nabla f(x)\cdot x'$, the directional derivative $y'\in \mathbb {R} ^{m}$ of $f:\mathbb {R} ^{n}\to \mathbb {R} ^{m}$ at $x\in \mathbb {R} ^{n}$ in the direction $x'\in \mathbb {R} ^{n}$ may be calculated as 

$$
(\langle y_{1},y'_{1}\rangle ,\ldots ,\langle y_{m},y'_{m}\rangle )=f(\langle x_{1},x'_{1}\rangle ,\ldots ,\langle x_{n},x'_{n}\rangle )
$$

 using the same arithmetic as above. If all the elements of $\nabla f$ are desired, then $n$ function evaluations are required. Note that in many optimization applications, the directional derivative is indeed sufficient.

### High order and many variables

The above arithmetic can be generalized to calculate second order and higher derivatives of multivariate functions. However, the arithmetic rules quickly grow complicated: complexity is quadratic in the highest derivative degree. Instead, truncated [[Taylor Series|Taylor polynomial]] algebra can be used. The resulting arithmetic, defined on generalized dual numbers, allows efficient computation using functions as if they were a data type. Once the Taylor polynomial of a function is known, the derivatives are easily extracted.

## Implementation

### Source code transformation (SCT)

![[media/6c19a1e93c1f745033ba53a0c65b1797b2aeb8ee.png]]
Figure 4: Example of how source code transformation could work

The source code for a function is replaced by an automatically generated source code that includes statements for calculating the derivatives interleaved with the original instructions.

[Source code transformation](https://en.wikipedia.org/wiki/Source_code_transformation) can be implemented for all programming languages, and it is also easier for the compiler to do compile time optimizations. However, the implementation of the AD tool itself is more difficult and the build system is more complex.

### Operator overloading (OO)

![[media/b10ee62d2ac516c74108c0e43def21a129e98ff5.png]]
Figure 5: Example of how operator overloading could work

[Operator overloading](https://en.wikipedia.org/wiki/Operator_overloading) is a possibility for source code written in a language supporting it. Objects for real numbers and elementary mathematical operations must be overloaded to cater for the augmented arithmetic depicted above. This requires no change in the form or sequence of operations in the original source code for the function to be differentiated, but often requires changes in basic data types for numbers and vectors to support overloading and often also involves the insertion of special flagging operations. Due to the inherent operator overloading overhead on each loop, this approach usually demonstrates weaker speed performance.

### Operator overloading and source code transformation

Overloaded Operators can be used to extract the valuation graph, followed by automatic generation of the AD-version of the primal function at run-time. Unlike the classic OO AAD<sup>\[*[clarification needed](https://en.wikipedia.org/wiki/Wikipedia:Please_clarify)*\]</sup>, such AD-function does not change from one iteration to the next one. Hence there is any OO or tape interpretation run-time overhead per Xi sample.

With the AD-function being generated at runtime, it can be optimised to take into account the current state of the program and precompute certain values. In addition, it can be generated in a way to consistently utilize native CPU vectorization to process 4(8)-double chunks of user data (AVX2\AVX512 speed up x4-x8). With multithreading added into account, such approach can lead to a final acceleration of order 8 × \#Cores compared to the traditional AAD tools. A reference implementation is available on GitHub.

## See also

- [Differentiable programming](https://en.wikipedia.org/wiki/Differentiable_programming)

## Notes

1.  In terms of weight matrices, the adjoint is the [transpose](https://en.wikipedia.org/wiki/Transpose). Addition is the [covector](https://en.wikipedia.org/wiki/Covector) ${\begin{bmatrix}1&\cdots &1\end{bmatrix}}$, since ${\begin{bmatrix}1&\cdots &1\end{bmatrix}}{\begin{bmatrix}x_{1}\\\vdots \\x_{n}\end{bmatrix}}=x_{1}+\cdots +x_{n}$, and fanout is the vector ${\begin{bmatrix}1\\\vdots \\1\end{bmatrix}}$, since ${\begin{bmatrix}1\\\vdots \\1\end{bmatrix}}{\begin{bmatrix}x\end{bmatrix}}={\begin{bmatrix}x\\\vdots \\x\end{bmatrix}}$.

## References

1.  Neidinger, Richard D. (2010). ["Introduction to Automatic Differentiation and MATLAB Object-Oriented Programming"](http://academics.davidson.edu/math/neidinger/SIAMRev74362.pdf) (PDF). *SIAM Review*. **52** (3): 545–563. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.362.6580](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.362.6580). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/080743627](https://doi.org/10.1137%2F080743627). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [17134969](https://api.semanticscholar.org/CorpusID:17134969).
2.  ^   Baydin, Atilim Gunes; Pearlmutter, Barak; Radul, Alexey Andreyevich; Siskind, Jeffrey (2018). ["Automatic differentiation in machine learning: a survey"](http://jmlr.org/papers/v18/17-468.html). *Journal of Machine Learning Research*. **18**: 1–43.
5.  ^   *[![[media/090e20f6ba7aa50acfde11fabbf7a4aac4b65956.png]]](https://creativecommons.org/licenses/by-sa/4.0/ "creativecommons:by-sa/4.0/") This article incorporates [text](https://pmc.ncbi.nlm.nih.gov/articles/PMC10280627/) by Dawood and Megahed available under the [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) license.*
8.  S. Chevillard, M. Joldes, and C. Lauter. Sollya (2010). An Environment for the Development of Numerical Codes. In K. Fukuda, J. van der Hoeven, M. Joswig, and N. Takayama, editors, Mathematical Software - ICMS 2010, volume 6327 of Lecture Notes in Computer Science, pages 28–31, Heidelberg, Germany. Springer.
10. Christian P. Fries (2019). Stochastic Automatic Differentiation: Automatic Differentiation for Monte-Carlo Simulations. Quantitative Finance, 19(6):1043–1059. doi: 10.1080/14697688.2018.1556398. url: [https://doi.org/10.1080/14697688.2018.1556398](https://doi.org/10.1080/14697688.2018.1556398).
13. ^   R.E. Wengert (1964). ["A simple automatic derivative evaluation program"](https://doi.org/10.1145%2F355586.364791). *Comm. ACM*. **7** (8): 463–464. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1145/355586.364791](https://doi.org/10.1145%2F355586.364791). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [24039274](https://api.semanticscholar.org/CorpusID:24039274).
14. Griewank, Andreas (2012). ["Who invented the reverse mode of differentiation?"](https://ftp.gwdg.de/pub/misc/EMIS/journals/DMJDMV/vol-ismp/52_griewank-andreas-b.pdf) (PDF). *Optimization Stories*. Documenta Mathematica Series. Vol. 6. pp. 389–400. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.4171/dms/6/38](https://doi.org/10.4171%2Fdms%2F6%2F38). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-936609-58-5](https://en.wikipedia.org/wiki/Special:BookSources/978-3-936609-58-5).
15. Linnainmaa, Seppo (1976). "Taylor Expansion of the Accumulated Rounding Error". *BIT Numerical Mathematics*. **16** (2): 146–160. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/BF01931367](https://doi.org/10.1007%2FBF01931367). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [122357351](https://api.semanticscholar.org/CorpusID:122357351).
16. Maximilian E. Schüle, Maximilian Springer, [Alfons Kemper](https://en.wikipedia.org/wiki/Alfons_Kemper), [Thomas Neumann](https://en.wikipedia.org/wiki/Thomas_Neumann) (2022). "LLVM code optimisation for automatic differentiation". *Proceedings of the Sixth Workshop on Data Management for End-To-End Machine Learning*. pp. 1–4. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1145/3533028.3533302](https://doi.org/10.1145%2F3533028.3533302). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9781450393751](https://en.wikipedia.org/wiki/Special:BookSources/9781450393751). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [248853034](https://api.semanticscholar.org/CorpusID:248853034).`{{`[`cite book`](https://en.wikipedia.org/wiki/Template:Cite_book)`}}`: CS1 maint: multiple names: authors list ([link](https://en.wikipedia.org/wiki/Category:CS1_maint:_multiple_names:_authors_list))
17. Bartholomew-Biggs, Michael; Brown, Steven; Christianson, Bruce; Dixon, Laurence (2000). "Automatic differentiation of algorithms". *Journal of Computational and Applied Mathematics*. **124** (1–2): 171–190. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2000JCoAM.124..171B](https://ui.adsabs.harvard.edu/abs/2000JCoAM.124..171B). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/S0377-0427(00)00422-2](https://doi.org/10.1016%2FS0377-0427%2800%2900422-2). [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[2299/3010](https://hdl.handle.net/2299%2F3010).
18. Maximilian E. Schüle, Harald Lang, Maximilian Springer, [Alfons Kemper](https://en.wikipedia.org/wiki/Alfons_Kemper), [Thomas Neumann](https://en.wikipedia.org/wiki/Thomas_Neumann), Stephan Günnemann (2021). "In-Database Machine Learning with SQL on GPUs". *33rd International Conference on Scientific and Statistical Database Management*. pp. 25–36. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1145/3468791.3468840](https://doi.org/10.1145%2F3468791.3468840). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9781450384131](https://en.wikipedia.org/wiki/Special:BookSources/9781450384131). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [235386969](https://api.semanticscholar.org/CorpusID:235386969).`{{`[`cite book`](https://en.wikipedia.org/wiki/Template:Cite_book)`}}`: CS1 maint: multiple names: authors list ([link](https://en.wikipedia.org/wiki/Category:CS1_maint:_multiple_names:_authors_list))
19. Maximilian E. Schüle, Harald Lang, Maximilian Springer, [Alfons Kemper](https://en.wikipedia.org/wiki/Alfons_Kemper), [Thomas Neumann](https://en.wikipedia.org/wiki/Thomas_Neumann), Stephan Günnemann (2022). ["Recursive SQL and GPU-support for in-database machine learning"](https://doi.org/10.1007%2Fs10619-022-07417-7). *Distributed and Parallel Databases*. **40** (2–3): 205–259. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s10619-022-07417-7](https://doi.org/10.1007%2Fs10619-022-07417-7). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [250412395](https://api.semanticscholar.org/CorpusID:250412395).`{{`[`cite journal`](https://en.wikipedia.org/wiki/Template:Cite_journal)`}}`: CS1 maint: multiple names: authors list ([link](https://en.wikipedia.org/wiki/Category:CS1_maint:_multiple_names:_authors_list))
20. Naumann, Uwe (April 2008). "Optimal Jacobian accumulation is NP-complete". *Mathematical Programming*. **112** (2): 427–441. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.320.5665](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.320.5665). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s10107-006-0042-z](https://doi.org/10.1007%2Fs10107-006-0042-z). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [30219572](https://api.semanticscholar.org/CorpusID:30219572).
21. ["AADC Prototype Library"](https://github.com/matlogica/aadc-prototype). June 22, 2022 – via GitHub.

## Further reading

- Rall, Louis B. (1981). *Automatic Differentiation: Techniques and Applications*. Lecture Notes in Computer Science. Vol. 120. [Springer](https://en.wikipedia.org/wiki/Springer_Science%2BBusiness_Media). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-10861-0](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-10861-0).
- Griewank, Andreas; [Walther, Andrea](https://en.wikipedia.org/wiki/Andrea_Walther) (2008). [Evaluating Derivatives: Principles and Techniques of Algorithmic Differentiation](https://epubs.siam.org/doi/book/10.1137/1.9780898717761). Other Titles in Applied Mathematics. Vol. 105 (2nd ed.). [SIAM](https://en.wikipedia.org/wiki/Society_for_Industrial_and_Applied_Mathematics). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/1.9780898717761](https://doi.org/10.1137%2F1.9780898717761). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-89871-659-7](https://en.wikipedia.org/wiki/Special:BookSources/978-0-89871-659-7).
- Neidinger, Richard (2010). ["Introduction to Automatic Differentiation and MATLAB Object-Oriented Programming"](http://academics.davidson.edu/math/neidinger/SIAMRev74362.pdf) (PDF). *SIAM Review*. **52** (3): 545–563. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.362.6580](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.362.6580). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/080743627](https://doi.org/10.1137%2F080743627). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [17134969](https://api.semanticscholar.org/CorpusID:17134969). Retrieved 2013-03-15.
- Naumann, Uwe (2012). *The Art of Differentiating Computer Programs*. Software-Environments-tools. [SIAM](https://en.wikipedia.org/wiki/Society_for_Industrial_and_Applied_Mathematics). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-611972-06-1](https://en.wikipedia.org/wiki/Special:BookSources/978-1-611972-06-1).
- Henrard, Marc (2017). *Algorithmic Differentiation in Finance Explained*. Financial Engineering Explained. [Palgrave Macmillan](https://en.wikipedia.org/wiki/Palgrave_Macmillan). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-319-53978-2](https://en.wikipedia.org/wiki/Special:BookSources/978-3-319-53978-2).

## External links

- [www.autodiff.org](http://www.autodiff.org/), An "entry site to everything you want to know about automatic differentiation"
- [Automatic Differentiation of Parallel OpenMP Programs](http://www.autodiff.org/?module=Applications&application=HC1)
- [Automatic Differentiation, C++ Templates and Photogrammetry](https://www.researchgate.net/publication/241730000_Automatic_Differentiation_C_Templates_and_Photogrammetry)
- [Automatic Differentiation, Operator Overloading Approach](https://web.archive.org/web/20070927120356/http://www.vivlabs.com/subpage_ad.php)
- [Compute analytic derivatives of any Fortran77, Fortran95, or C program through a web-based interface](http://tapenade.inria.fr:8080/tapenade/index.jsp) Automatic Differentiation of Fortran programs
- [Description and example code for forward Automatic Differentiation in Scala](http://www.win-vector.com/dfiles/AutomaticDifferentiationWithScala.pdf) [Archived](https://web.archive.org/web/20160803214549/http://www.win-vector.com/dfiles/AutomaticDifferentiationWithScala.pdf) 2016-08-03 at the [Wayback Machine](https://en.wikipedia.org/wiki/Wayback_Machine)
- [finmath-lib stochastic automatic differentiation](https://www.finmath.net/finmath-lib/concepts/stochasticautomaticdifferentiation/), Automatic differentiation for random variables (Java implementation of the stochastic automatic differentiation).
- [Adjoint Algorithmic Differentiation: Calibration and Implicit Function Theorem](https://web.archive.org/web/20140423121504/http://developers.opengamma.com/quantitative-research/Adjoint-Algorithmic-Differentiation-OpenGamma.pdf)
- [C++ Template-based automatic differentiation article](http://www.quantandfinancial.com/2017/02/automatic-differentiation-templated.html) and [implementation](https://github.com/omartinsky/QuantAndFinancial/tree/master/autodiff_templated)
- [Tangent](https://github.com/google/tangent) [Source-to-Source Debuggable Derivatives](https://research.googleblog.com/2017/11/tangent-source-to-source-debuggable.html)
- [Exact First- and Second-Order Greeks by Algorithmic Differentiation](http://www.nag.co.uk/doc/techrep/pdf/tr5_10.pdf)
- [Adjoint Algorithmic Differentiation of a GPU Accelerated Application](http://www.nag.co.uk/Market/articles/adjoint-algorithmic-differentiation-of-gpu-accelerated-app.pdf)
- [Adjoint Methods in Computational Finance Software Tool Support for Algorithmic Differentiationop](http://www.nag.co.uk/Market/seminars/Uwe_AD_Slides_July13.pdf)
- [More than a Thousand Fold Speed Up for xVA Pricing Calculations with Intel Xeon Scalable Processors](https://www.intel.com/content/dam/www/public/us/en/documents/white-papers/xva-pricing-application-financial-services-white-papers.pdf)
- [Sparse truncated Taylor series implementation with VBIC95 example for higher order derivatives](https://github.com/ExcessPhase/ctaylor)
